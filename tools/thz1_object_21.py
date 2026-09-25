#!/usr/bin/env python3
"""Produce ROM-backed metadata and controlled traces for THZ1 object type $21."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OBJECT_RECORDS = ROOT / "data" / "rom-cache" / "thz1" / "object-records.json"

ANIM_PATH = ROOT / "tools" / "thz1_animation_reach.py"
spec = importlib.util.spec_from_file_location("thz1_animation_reach", ANIM_PATH)
anim = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(anim)


def s16(value: int) -> int:
    return (value + 0x8000) % 0x10000 - 0x8000


def parameter_left_bound(origin_x: int, parameter: int) -> int:
    """Translation of $B22F..$B24E: origin X minus parameter times 16."""
    return (origin_x - ((parameter & 0xFF) << 4)) & 0xFFFF


def first_left_reversal_tick(parameter: int) -> int:
    """Ticks from integer origin at -$0080 until integer X is below the bound."""
    x_8_8 = 0
    bound_8_8 = -(parameter & 0xFF) * 16 * 256
    ticks = 0
    while True:
        ticks += 1
        x_8_8 -= 0x80
        # $62D5 compares integer position, not the fractional byte.
        integer_x = x_8_8 // 256
        if integer_x < bound_8_8 // 256:
            return ticks


def load_placements() -> list[dict]:
    records = json.loads(OBJECT_RECORDS.read_text(encoding="utf-8"))
    return [
        {
            "record_index": row["index"],
            "rom_offset": row["rom_offset"],
            "world_x": row["world_x"],
            "world_y": row["world_y"],
            "flags": row["flags"],
            "parameter": row["parameter"],
            "aux0": row["aux0"],
            "aux1": row["aux1"],
        }
        for row in records["records"]
        if int(row["type_id"], 16) == 0x21
    ]


def _oracle_type():
    sys.path.insert(0, str(ROOT / "tools"))
    from oracle import Oracle
    return Oracle


def _new_object_oracle(rom: bytes):
    Oracle = _oracle_type()
    oracle = Oracle(rom)
    oracle.bank(2, 0x0C)
    oracle.mem[0xD12B] = 0x0C
    oracle.cpu.ix = 0xD700
    return oracle


def run_init_fixture(rom: bytes, x: int, parameter: int, flags: int = 0) -> dict:
    oracle = _new_object_oracle(rom)
    oracle.word(0xD711, x)
    oracle.mem[0xD73F] = parameter
    oracle.mem[0xD704] = flags
    oracle.call(0xB210)
    return {
        "origin_x": x,
        "parameter": parameter,
        "input_flags": f"0x{flags:02X}",
        "requested_state": oracle.mem[0xD702],
        "x_velocity_8_8": s16(oracle.word(0xD716)),
        "y_velocity_8_8": s16(oracle.word(0xD718)),
        "left_bound": oracle.word(0xD737),
        "parameter_after": oracle.mem[0xD73F],
        "object_flags_03": f"0x{oracle.mem[0xD703]:02X}",
        "variant_latch": oracle.mem[0xD73F],
    }


def run_patrol_fixture(rom: bytes, x: int, y: int, parameter: int) -> dict:
    oracle = _new_object_oracle(rom)
    oracle.mem[0xD700] = 0x21
    oracle.word(0xD711, x)
    oracle.word(0xD714, y)
    oracle.word(0xD73A, x)
    oracle.word(0xD73C, y)
    oracle.mem[0xD73F] = parameter
    oracle.call(0xB210)

    transitions = []
    for tick in range(1, 2049):
        before = oracle.mem[0xD702]
        if before in (4, 5):
            callback = 0xB264
        elif before == 1:
            callback = 0xB2F0
        else:
            callback = 0xB268
        oracle.call(callback)
        after = oracle.mem[0xD702]
        if after != before:
            transitions.append({
                "tick": tick,
                "from_state": before,
                "to_state": after,
                "x_integer": oracle.word(0xD711),
                "x_fraction": oracle.mem[0xD710],
                "y_integer": oracle.word(0xD714),
                "x_velocity_8_8": s16(oracle.word(0xD716)),
            })
            if len(transitions) == 2:
                break
    return {
        "placement": {"world_x": x, "world_y": y, "parameter": parameter},
        "left_bound": parameter_left_bound(x, parameter),
        "predicted_first_reversal_tick": first_left_reversal_tick(parameter),
        "transitions": transitions,
    }


def run_grounding_fixture(rom: bytes, placement: dict) -> dict:
    """Run initialization and the first patrol update through the original code."""
    x, y = placement["world_x"], placement["world_y"]
    oracle = _new_object_oracle(rom)
    oracle.mem[0xD700] = 0x21
    oracle.word(0xD711, x)
    oracle.word(0xD714, y)
    oracle.word(0xD73A, x)
    oracle.word(0xD73C, y)
    oracle.mem[0xD73F] = int(placement["parameter"], 16)
    oracle.mem[0xD704] = 0
    oracle.call(0xB210)
    # The placement loader's bit 6 is cleared when activation becomes live.
    oracle.mem[0xD704] &= ~0x40
    oracle.call(0xB268)
    anchor = oracle.word(0xD714)
    probe_y = oracle.word(0xD35A)
    surface = anchor + 18
    standing = surface - 18
    return {
        "placement": {"world_x": x, "world_y": y, "parameter": placement["parameter"]},
        "first_integrated_y": y + 2,
        "lookup_probe": {"x": oracle.word(0xD358), "y": probe_y,
                         "expression": "first_integrated_y + 18"},
        "terrain_tile": f"0x{oracle.mem[0xD353]:02X}",
        "terrain_map_address": f"0x{oracle.word(0xD354):04X}",
        "collision_flags": f"0x{oracle.mem[0xD364]:02X}",
        "vertical_profile_value": oracle.mem[0xD368],
        "collision_surface_y": surface,
        "final_object_anchor_y": anchor,
        "placement_to_anchor_delta": anchor - y,
        "mapping_piece_y_bounds": [anchor - 32, anchor - 1],
        "top_bounce_threshold_y": anchor - 4,
        "ordinary_standing_sonic_anchor_y": standing,
        "ordinary_level_side_contact": "DAMAGE" if standing > anchor - 4 else "TOP_BOUNCE",
    }


def _contact_oracle(rom: bytes, object_y: int, player_flags: int = 0,
                    power_up: int = 0):
    oracle = _new_object_oracle(rom)
    oracle.mem[0xD700] = 0x21
    oracle.word(0xD711, 500)
    oracle.word(0xD714, object_y)
    oracle.mem[0xD72C] = 0x0B
    oracle.mem[0xD72D] = 0x1A
    oracle.word(0xD511, 500)
    oracle.word(0xD514, 500)
    oracle.mem[0xD52C] = 9
    oracle.mem[0xD52D] = 18
    oracle.mem[0xD503] = player_flags
    oracle.mem[0xD532] = power_up
    oracle.word(0xD518, 0)
    return oracle


def run_contact_fixtures(rom: bytes) -> dict:
    top = _contact_oracle(rom, object_y=504)
    top.call(0xB2AF)

    side = _contact_oracle(rom, object_y=500)
    side.call(0xB2AF)

    attack = _contact_oracle(rom, object_y=500, player_flags=0x02)
    attack.call(0xB2AF)

    invincible = _contact_oracle(rom, object_y=500, power_up=0x06)
    invincible.call(0xB2AF)

    return {
        "top_contact": {
            "requested_player_state": top.mem[0xD502],
            "player_y_velocity_8_8": s16(top.word(0xD518)),
            "d448": f"0x{top.mem[0xD448]:02X}",
            "sound_request": f"0x{top.mem[0xDE04]:02X}",
            "object_type_after": f"0x{top.mem[0xD700]:02X}",
        },
        "ordinary_side_contact": {
            "damage_request_d3b0": f"0x{side.mem[0xD3B0]:02X}",
            "object_type_after": f"0x{side.mem[0xD700]:02X}",
        },
        "rolling_attack": {
            "object_type_after": f"0x{attack.mem[0xD700]:02X}",
            "placement_token_after": attack.mem[0xD73E],
            "score_bytes_after": " ".join(
                f"{value:02X}" for value in attack.mem[0xD29D:0xD2A0]
            ),
        },
        "power_up_06_contact": {
            "object_type_after": f"0x{invincible.mem[0xD700]:02X}",
            "damage_request_d3b0": f"0x{invincible.mem[0xD3B0]:02X}",
        },
    }


def animation_summary(rom: bytes) -> dict:
    trace = anim.trace_type(rom, 0x21)
    states = []
    for state in trace["states"]:
        states.append({
            "state_index": state["state_index"],
            "script_cpu": state["script_cpu"],
            "script_rom": state["script_rom"],
            "frame_indices": state["frame_indices"],
            "callbacks": sorted({row["callback_cpu"] for row in state["records"]}),
            "commands": [
                {key: value for key, value in command.items() if key != "rom"}
                for command in state["commands"]
                if command.get("command") != "loop_detected"
            ],
            "unresolved": state["unresolved"],
        })
    return {
        "type_table_entry_rom": f"0x{trace['type_table_entry_rom']:05X}",
        "bank": f"0x{trace['bank']:02X}",
        "state_table_cpu": f"0x{trace['state_table_cpu']:04X}",
        "state_table_rom": f"0x{trace['state_table_rom']:05X}",
        "state_count": trace["state_count"],
        "state_script_cpus": [f"0x{x:04X}" for x in trace["state_script_cpus"]],
        "reachable_mapping_frame_indices": [
            f"0x{x:02X}" for x in trace["reachable_frame_indices"]
        ],
        "unresolved_states": trace["unresolved_states"],
        "states": states,
    }


def build_report(rom: bytes) -> dict:
    digest = hashlib.sha256(rom).hexdigest()
    if digest != ROM_SHA256:
        raise ValueError(f"ROM SHA-256 mismatch: {digest}")
    placements = load_placements()
    return {
        "format": 1,
        "rom_sha256": digest,
        "object_type": "0x21",
        "identity": {
            "verified": None,
            "likely": "Boing-o-Bot / Bane Motora",
            "basis": "reconstructed spring-backed wheeled sprite, patrol, top bounce, attack response, and THZ1 placements",
        },
        "placements": placements,
        "animation": animation_summary(rom),
        "handlers": {
            "initialization": {"cpu": "0xB210", "rom": "0x33210"},
            "left_orientation_patrol": {"cpu": "0xB264", "rom": "0x33264"},
            "shared_patrol": {"cpu": "0xB268", "rom": "0x33268"},
            "contact": {"cpu": "0xB2AF", "rom": "0x332AF"},
            "falling": {"cpu": "0xB2F0", "rom": "0x332F0"},
        },
        "grounding_path": {
            "callback_cpu": "0xB268",
            "fixed_vector": "0x0320",
            "object_floor_wrapper_cpu": "0x77CB",
            "collision_lookup_cpu": "0x7666",
            "probe_adjustment_cpu": "0x7690",
            "probe_adjustment": 18,
            "floor_projection_cpu": "0x70E7",
            "handler_table_cpu": "0x77ED",
            "anchor_contract": "object +$14/+$15 remains the integer world anchor; +18 is a temporary collision probe and the floor correction is subtracted from the anchor",
        },
        "parameter": {
            "meaning": "leftward patrol span in units of 16 integer pixels",
            "left_bound_expression": "saved_origin_x - (parameter << 4)",
            "consumed_on_initialization": True,
        },
        "controlled_original_routine_fixtures": {
            "evidence": "controlled trace",
            "initialization": [
                run_init_fixture(rom, 1000, 2),
                run_init_fixture(rom, 1000, 8),
            ],
            "patrol": [
                run_patrol_fixture(rom, 2400, 254, 2),
                run_patrol_fixture(rom, 800, 606, 8),
            ],
            "grounding": [run_grounding_fixture(rom, row) for row in placements],
            "combined_grounding_contact": {
                "fixtures": [run_grounding_fixture(rom, row) for row in placements
                             if (row["world_x"], row["world_y"]) in ((800, 606), (2400, 254))],
                "contract": "ground the object with $B268, derive ordinary Sonic anchor as surface_y-18, retain horizontal overlap inside +/-20, then apply the $B2AF split",
                "expected": "ordinary lower-side contact -> DAMAGE",
            },
            "contact": run_contact_fixtures(rom),
        },
    }


def report_markdown(report: dict) -> str:
    patrol = report["controlled_original_routine_fixtures"]["patrol"]
    lines = [
        "# THZ1 object `$21` controlled report",
        "",
        f"ROM SHA-256: `{report['rom_sha256']}`",
        "",
        f"Animation table: `{report['animation']['state_table_cpu']}` "
        f"(ROM `{report['animation']['state_table_rom']}`), "
        f"{report['animation']['state_count']} states; frames "
        + ", ".join(report["animation"]["reachable_mapping_frame_indices"])
        + ".",
        "",
        "## Controlled patrol transitions",
        "",
        "| Parameter | Left bound | First reversal tick | First transition | Second transition |",
        "|---:|---:|---:|---|---|",
    ]
    for item in patrol:
        first, second = item["transitions"]
        lines.append(
            f"| `{item['placement']['parameter']:02X}` | {item['left_bound']} | "
            f"{first['tick']} | {first['from_state']}→{first['to_state']} | "
            f"{second['from_state']}→{second['to_state']} at {second['tick']} |"
        )
    lines += [
        "",
        "The JSON report contains the full initialization, movement, animation, "
        "and contact fixtures. These execute original ROM routines through the "
        "repository Oracle; they are not full-emulator gameplay observations.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "build" / "thz1-object-21"
    )
    parser.add_argument("--metadata", type=Path)
    args = parser.parse_args()

    report = build_report(args.rom.read_bytes())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    (args.output / "REPORT.md").write_text(
        report_markdown(report), encoding="utf-8"
    )
    if args.metadata:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps({
        "state_table": report["animation"]["state_table_cpu"],
        "states": report["animation"]["state_count"],
        "frames": report["animation"]["reachable_mapping_frame_indices"],
        "output": str(args.output),
    }))


if __name__ == "__main__":
    main()

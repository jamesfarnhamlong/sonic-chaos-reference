#!/usr/bin/env python3
"""Produce ROM-backed metadata and controlled traces for THZ1 object type $27."""

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


def horizontal_test(distance: int, threshold: int) -> bool:
    """Translation of fixed $61BB: absolute integer distance is strictly less."""
    return abs(distance) < threshold


def expected_oscillation() -> dict:
    """Translate state-2 script phases and callbacks through counter underflow."""
    velocity = 0
    displacement = 0
    counter = 0x80
    callbacks: list[str] = []

    # Script $895F: +3 for 8 frame-pairs, -3 for 16 frame-pairs, then
    # +3 for 16 frame-pairs. Each record lasts two updates. The independent
    # object counter underflows during the third phase, after 33 +3 updates.
    phases = (("0x89DF", 3, 32), ("0x89F3", -3, 64),
              ("0x89DF", 3, 64))
    for callback, delta, updates in phases:
        for _ in range(updates):
            velocity += delta
            displacement += velocity
            callbacks.append(callback)
            counter = (counter - 1) & 0xFF
            if counter == 0xFF:
                return {
                    "updates": len(callbacks),
                    "add_callbacks": callbacks.count("0x89DF"),
                    "subtract_callbacks": callbacks.count("0x89F3"),
                    "displacement_8_8": displacement,
                    "velocity_before_reset_8_8": velocity,
                    "counter_after": counter,
                }
    raise AssertionError("counter did not underflow")


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
        if int(row["type_id"], 16) == 0x27
    ]


def _oracle_type():
    sys.path.insert(0, str(ROOT / "tools"))
    from oracle import Oracle
    return Oracle


def _new_object_oracle(rom: bytes):
    Oracle = _oracle_type()
    oracle = Oracle(rom)
    oracle.bank(2, 0x1E)
    oracle.mem[0xD12B] = 0x1E
    oracle.cpu.ix = 0xD700
    oracle.mem[0xD700] = 0x27
    return oracle


def _position_16_8(oracle, integer_address: int) -> int:
    return oracle.word(integer_address) * 0x100 + oracle.mem[integer_address - 1]


def run_creation_fixture(rom: bytes) -> dict:
    oracle = _new_object_oracle(rom)
    oracle.bank(2, 0x1C)
    oracle.mem[0xD700:0xD740] = bytes(0x40)
    oracle.cpu.hl = 0x867D  # ROM $7067D in bank $1C.
    oracle.call(0x80EB, bc=0xD418)
    return {
        "record_cpu": "0x867D",
        "occupancy_address": "0xD418",
        "occupancy_value": f"0x{oracle.mem[0xD418]:02X}",
        "object_type": f"0x{oracle.mem[0xD700]:02X}",
        "current_x": oracle.word(0xD711),
        "current_y": oracle.word(0xD714),
        "saved_x": oracle.word(0xD73A),
        "saved_y": oracle.word(0xD73C),
        "object_flags_04": f"0x{oracle.mem[0xD704]:02X}",
        "parameter_3f": f"0x{oracle.mem[0xD73F]:02X}",
        "art_base_08": f"0x{oracle.mem[0xD708]:02X}",
        "art_base_09": f"0x{oracle.mem[0xD709]:02X}",
        "placement_token_3e": oracle.mem[0xD73E],
    }


def run_init_fixture(rom: bytes, parameter: int) -> dict:
    oracle = _new_object_oracle(rom)
    oracle.mem[0xD704] = 0x10
    oracle.mem[0xD73F] = parameter
    oracle.word(0xD716, 0x1234)
    oracle.word(0xD718, 0x5678)
    oracle.mem[0xD71E] = 0xA5
    oracle.mem[0xD71F] = 0x5A
    oracle.call(0x898E)
    return {
        "parameter": f"0x{parameter:02X}",
        "requested_state": oracle.mem[0xD702],
        "object_flags_04": f"0x{oracle.mem[0xD704]:02X}",
        "x_velocity_8_8": s16(oracle.word(0xD716)),
        "y_velocity_8_8": s16(oracle.word(0xD718)),
        "field_1e": f"0x{oracle.mem[0xD71E]:02X}",
        "field_1f": f"0x{oracle.mem[0xD71F]:02X}",
    }


def run_proximity_fixture(rom: bytes, distance_at_compare: int) -> dict:
    oracle = _new_object_oracle(rom)
    oracle.mem[0xD704] = 0x10
    oracle.mem[0xD701] = oracle.mem[0xD702] = 1
    oracle.word(0xD711, 1000)
    oracle.word(0xD714, 500)
    oracle.word(0xD716, 0xFD80)
    oracle.word(0xD718, 0)
    # $89AC integrates first: 1000 becomes 997.5 and the integer comparison
    # coordinate is 997. Keep Y far away so this fixture cannot overlap.
    oracle.word(0xD511, 997 - distance_at_compare)
    oracle.word(0xD514, 1000)
    oracle.call(0x89AC)
    return {
        "distance_at_compare": distance_at_compare,
        "object_x_16_8_after": _position_16_8(oracle, 0xD711),
        "player_integer_x": oracle.word(0xD511),
        "requested_state": oracle.mem[0xD702],
        "object_flags_04": f"0x{oracle.mem[0xD704]:02X}",
        "x_velocity_8_8": s16(oracle.word(0xD716)),
        "counter_1e": f"0x{oracle.mem[0xD71E]:02X}",
    }


def run_oscillation_fixture(rom: bytes) -> dict:
    oracle = _new_object_oracle(rom)
    oracle.mem[0xD704] = 0x12
    oracle.word(0xD711, 1000)
    oracle.word(0xD714, 500)
    oracle.word(0xD511, 1000)
    oracle.word(0xD514, 1000)
    oracle.word(0xD174, 872)
    oracle.word(0xD176, 372)
    oracle.mem[0xD701] = 1
    oracle.mem[0xD702] = 2
    oracle.mem[0xD707] = 1
    oracle.word(0xD70E, 0x8959)
    oracle.word(0xD716, 0)
    oracle.word(0xD718, 0)
    oracle.mem[0xD71E] = 0x80
    oracle.mem[0xD71F] = 1
    start_y = _position_16_8(oracle, 0xD714)
    rows = []
    for update in range(1, 130):
        oracle.call(0x5DF1)
        callback = oracle.word(0xD70C)
        rows.append({
            "update": update,
            "callback_cpu": f"0x{callback:04X}",
            "current_state": oracle.mem[0xD701],
            "requested_state": oracle.mem[0xD702],
            "counter_1e": f"0x{oracle.mem[0xD71E]:02X}",
            "loop_counter_33": f"0x{oracle.mem[0xD733]:02X}",
            "y_velocity_8_8": s16(oracle.word(0xD718)),
            "y_displacement_8_8": _position_16_8(oracle, 0xD714) - start_y,
        })

    transition = rows[-1]
    oracle.call(0x5DF1)
    resumed = {
        "update": 130,
        "callback_cpu": f"0x{oracle.word(0xD70C):04X}",
        "current_state": oracle.mem[0xD701],
        "requested_state": oracle.mem[0xD702],
        "x_velocity_8_8": s16(oracle.word(0xD716)),
        "y_velocity_8_8": s16(oracle.word(0xD718)),
        "x_16_8": _position_16_8(oracle, 0xD711),
        "y_displacement_8_8": _position_16_8(oracle, 0xD714) - start_y,
    }
    callbacks = [row["callback_cpu"] for row in rows]
    return {
        "updates_to_counter_underflow": len(rows),
        "add_callbacks": callbacks.count("0x89DF"),
        "subtract_callbacks": callbacks.count("0x89F3"),
        "underflow_update": transition,
        "horizontal_resume_update": resumed,
        "checkpoints": [rows[i - 1] for i in (1, 32, 33, 96, 97, 128, 129)],
    }


def run_removal_fixture(rom: bytes, distance: int) -> dict:
    oracle = _new_object_oracle(rom)
    oracle.mem[0xD704] = 0x12
    oracle.mem[0xD701] = oracle.mem[0xD702] = 3
    oracle.mem[0xD73E] = 25
    oracle.word(0xD711, 1000)
    oracle.word(0xD714, 500)
    oracle.word(0xD716, 0xFD80)
    oracle.word(0xD718, 0)
    oracle.word(0xD511, 1000 - distance)
    oracle.word(0xD514, 1000)
    oracle.call(0x8A29)
    return {
        "distance": distance,
        "object_type_after": f"0x{oracle.mem[0xD700]:02X}",
        "placement_token_after": oracle.mem[0xD73E],
        "x_16_8_after": _position_16_8(oracle, 0xD711),
    }


def _contact_oracle(rom: bytes, player_flags: int = 0, power_up: int = 0):
    oracle = _new_object_oracle(rom)
    oracle.mem[0xD704] = 0x10
    oracle.mem[0xD73E] = 25
    oracle.word(0xD711, 500)
    oracle.word(0xD714, 500)
    oracle.word(0xD716, 0xFD80)
    oracle.mem[0xD72C] = 9
    oracle.mem[0xD72D] = 14
    oracle.word(0xD511, 500)
    oracle.word(0xD514, 500)
    oracle.mem[0xD52C] = 9
    oracle.mem[0xD52D] = 18
    oracle.mem[0xD503] = player_flags
    oracle.mem[0xD532] = power_up
    return oracle


def run_contact_fixtures(rom: bytes) -> dict:
    results = {}
    for name, player_flags, power_up in (
        ("ordinary", 0, 0),
        ("rolling_attack", 2, 0),
        ("power_up_06", 0, 6),
    ):
        oracle = _contact_oracle(rom, player_flags, power_up)
        before_x = _position_16_8(oracle, 0xD711)
        oracle.call(0x89AC)
        results[name] = {
            "contact_bits_21": f"0x{oracle.mem[0xD721] & 0x0F:02X}",
            "damage_request_d3b0": f"0x{oracle.mem[0xD3B0]:02X}",
            "object_type_after": f"0x{oracle.mem[0xD700]:02X}",
            "placement_token_after": oracle.mem[0xD73E],
            "score_bytes_after": " ".join(
                f"{value:02X}" for value in oracle.mem[0xD29D:0xD2A0]
            ),
            "x_displacement_8_8": _position_16_8(oracle, 0xD711) - before_x,
        }
    return results


def run_lifetime_fixtures(rom: bytes) -> dict:
    results = {}
    for name, flags in (("before_trigger", 0x10), ("after_trigger", 0x12)):
        oracle = _new_object_oracle(rom)
        oracle.mem[0xD704] = flags
        oracle.mem[0xD701] = oracle.mem[0xD702] = 3
        oracle.mem[0xD73E] = 25
        oracle.word(0xD711, 1000)
        oracle.word(0xD714, 500)
        oracle.word(0xD174, 0)
        oracle.word(0xD176, 0)
        oracle.call(0x61E1)
        results[name] = {
            "object_type_after": f"0x{oracle.mem[0xD700]:02X}",
            "current_state_after": oracle.mem[0xD701],
            "object_flags_04": f"0x{oracle.mem[0xD704]:02X}",
            "placement_token_after": oracle.mem[0xD73E],
        }

    cleanup = _new_object_oracle(rom)
    cleanup.mem[0xD700] = 0xFE
    cleanup.mem[0xD73E] = 25
    cleanup.mem[0xD418] = 0x27
    cleanup.call(0x5EF8)
    results["type_fe_cleanup"] = {
        "occupancy_address": "0xD418",
        "occupancy_value_after": f"0x{cleanup.mem[0xD418]:02X}",
        "object_type_after": f"0x{cleanup.mem[0xD700]:02X}",
        "slot_is_zero": not any(cleanup.mem[0xD700:0xD740]),
    }
    return results


def animation_summary(rom: bytes) -> dict:
    trace = anim.trace_type(rom, 0x27)
    states = []
    for state in trace["states"]:
        records = []
        seen_records = set()
        for row in state["records"]:
            if row["cpu"] in seen_records:
                continue
            seen_records.add(row["cpu"])
            records.append({key: value for key, value in row.items() if key != "rom"})
        commands = []
        seen_commands = set()
        for command in state["commands"]:
            if command.get("command") == "loop_detected":
                continue
            key = command["cpu"]
            if key in seen_commands:
                continue
            seen_commands.add(key)
            commands.append({key: value for key, value in command.items() if key != "rom"})
        states.append({
            "state_index": state["state_index"],
            "script_cpu": state["script_cpu"],
            "script_rom": state["script_rom"],
            "frame_indices": state["frame_indices"],
            "records": records,
            "commands": commands,
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
    return {
        "format": 1,
        "rom_sha256": digest,
        "object_type": "0x27",
        "identity": {
            "verified": None,
            "status": "UNRESOLVED",
            "basis": "No semantic identity is established by the recovered ROM/source evidence.",
        },
        "placements": load_placements(),
        "animation": animation_summary(rom),
        "mapping": {
            "pointer_entry_rom": "0x3C04E",
            "table_cpu": "0x91F5",
            "table_rom": "0x3D1F5",
            "object_specific_frames": [
                {"index": "0x01", "cpu": "0x91FB", "rom": "0x3D1FB"},
                {"index": "0x02", "cpu": "0x9206", "rom": "0x3D206"},
            ],
            "collision_extents_from_frames": {"horizontal_2c": 9, "vertical_2d": 14},
        },
        "handlers": {
            "initialization": {"cpu": "0x898E", "rom": "0x7898E"},
            "horizontal_and_trigger": {"cpu": "0x89AC", "rom": "0x789AC"},
            "vertical_add": {"cpu": "0x89DF", "rom": "0x789DF"},
            "vertical_subtract": {"cpu": "0x89F3", "rom": "0x789F3"},
            "vertical_shared_tail": {"cpu": "0x8A06", "rom": "0x78A06"},
            "horizontal_resume_and_removal": {"cpu": "0x8A29", "rom": "0x78A29"},
        },
        "comparisons": {
            "horizontal_proximity": {
                "helper_cpu": "0x61A5",
                "vector_cpu": "0x0383",
                "player_coordinate": "integer X word $D511",
                "object_coordinate": "integer X word IX+$11/+$12 after movement",
                "expression": "abs(object_x - player_x) < 0x0040",
                "boundary": "63 triggers; 64 and greater do not",
            },
            "state_3_removal": {
                "helper_cpu": "0x61A5",
                "vector_cpu": "0x0383",
                "expression": "abs(object_x - player_x) >= 0x0180",
                "boundary": "383 survives; 384 and greater set type 0xFE",
            },
        },
        "orientation": {
            "placement_flag_bit_4": True,
            "object_field": "IX+0x04 bit 4",
            "renderer_cpu": "0x22B6",
            "effect": "mirrored coordinate stream, negated frame X origin, art base IX+0x09",
            "thz1_art_bases": "0xAA/0xAA",
        },
        "interaction": {
            "overlap_helper_cpu": "0x6328",
            "generic_attack_check_cpu": "0x5F3D",
            "ordinary_contact_damage_request": False,
            "ordinary_contact_stalls_callback": True,
            "rolling_or_attack_destroys": True,
            "power_up_06_destroys": True,
            "replacement_type": "0x0F",
            "score_bytes": "10 00 00",
        },
        "lifetime": {
            "pre_trigger": "generic off-range type 0xFE; cleanup releases occupancy",
            "trigger_change": "set IX+0x04 bit 1, suppressing generic off-range deletion",
            "post_trigger": "state 3 sets type 0xFE at horizontal separation >= 0x0180",
            "object_specific_removal_can_respawn": True,
            "defeated_replacement_can_respawn": False,
        },
        "controlled_original_routine_fixtures": {
            "evidence": "controlled trace",
            "placement_creation": run_creation_fixture(rom),
            "initialization": [run_init_fixture(rom, 0), run_init_fixture(rom, 1)],
            "proximity": [
                run_proximity_fixture(rom, distance) for distance in (65, 64, 63)
            ],
            "oscillation": run_oscillation_fixture(rom),
            "removal": [run_removal_fixture(rom, distance) for distance in (383, 384, 385)],
            "contact": run_contact_fixtures(rom),
            "lifetime": run_lifetime_fixtures(rom),
        },
        "independent_translation": expected_oscillation(),
        "unresolved": [
            "semantic identity and canonical name",
            "meaning of a nonzero placement parameter and object field IX+0x1F",
            "downstream gameplay significance of ordinary generic contact bookkeeping",
            "semantic names of placement-scan map-cell eligibility values",
            "complete lifetime and presentation of replacement type 0x0F",
            "hardware-frame timing and emulator-observed encounter",
        ],
    }


def report_markdown(report: dict) -> str:
    oscillation = report["controlled_original_routine_fixtures"]["oscillation"]
    lines = [
        "# THZ1 object `$27` controlled report",
        "",
        f"ROM SHA-256: `{report['rom_sha256']}`",
        "",
        "The strict original helper boundaries are 63/64 pixels for activation "
        "and 383/384 pixels for state-3 removal.",
        "",
        f"State 2 reaches counter underflow on update "
        f"{oscillation['updates_to_counter_underflow']}: "
        f"{oscillation['add_callbacks']} add callbacks and "
        f"{oscillation['subtract_callbacks']} subtract callbacks.",
        "",
        "The JSON report contains the complete source-level state records and "
        "commands plus initialization, proximity, oscillation, removal, and "
        "contact fixtures. These execute original ROM routines through the "
        "repository Oracle; they are not full-emulator gameplay observations.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "build" / "thz1-object-27"
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
        "oscillation_updates": report["controlled_original_routine_fixtures"]
        ["oscillation"]["updates_to_counter_underflow"],
        "output": str(args.output),
    }))


if __name__ == "__main__":
    main()

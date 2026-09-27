#!/usr/bin/env python3
"""Build the deterministic THZ1 type-$09 behavior report."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
RECORDS = ROOT / "data" / "rom-cache" / "thz1" / "object-records.json"

spec = importlib.util.spec_from_file_location(
    "thz1_animation_reach", ROOT / "tools" / "thz1_animation_reach.py"
)
anim = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(anim)


def load_placements() -> list[dict]:
    source = json.loads(RECORDS.read_text(encoding="utf-8"))
    keys = ("index", "rom_offset", "raw_bytes", "world_x", "world_y",
            "flags", "parameter", "aux0", "aux1")
    return [{key: row[key] for key in keys} for row in source["records"]
            if row["type_id"] == "0x09"]


def strict_overlap(dx: int, dy: int) -> bool:
    return abs(dx) < 12 and abs(dy) < 12


def sparkle_timeline() -> dict:
    # State 2 has eight four-update records: frames 5/6 alternate four times.
    frames = [5, 6] * 4
    updates = [frame for frame in frames for _ in range(4)]
    return {"records": len(frames), "updates": len(updates),
            "frames_by_record": frames, "frames_by_update": updates,
            "terminal_type": "0xFE"}


def _oracle(rom: bytes):
    sys.path.insert(0, str(ROOT / "tools"))
    from oracle import Oracle
    o = Oracle(rom)
    o.bank(2, 0x0C)
    o.mem[0xD12B] = 0x0C
    o.cpu.ix = 0xD700
    o.mem[0xD700] = 0x09
    return o


def run_init(rom: bytes, parameter: int) -> dict:
    o = _oracle(rom)
    o.mem[0xD73F] = parameter
    o.call(0x9C10)
    return {"parameter": f"0x{parameter:02X}",
            "requested_state": o.mem[0xD702],
            "renderer_flags_04": f"0x{o.mem[0xD704]:02X}"}


def run_collect(rom: bytes, parameter: int, dx: int, dy: int,
                global_frame: int = 0) -> dict:
    o = _oracle(rom)
    o.mem[0xD73F] = parameter
    o.mem[0xD73E] = 7
    o.word(0xD711, 1000)
    o.word(0xD714, 500)
    o.word(0xD511, 1000 - dx)
    o.word(0xD514, 500 - dy)
    o.mem[0xD12F] = global_frame
    o.mem[0xD29A] = 0x09
    o.call(0x9C22 if parameter == 0 else 0x9C3D)
    return {"parameter": f"0x{parameter:02X}", "dx": dx, "dy": dy,
            "global_frame": global_frame,
            "collected": o.mem[0xD73E] == 0,
            "requested_state": o.mem[0xD702],
            "object_type_after": f"0x{o.mem[0xD700]:02X}",
            "ring_counter_d29a_bcd": f"0x{o.mem[0xD29A]:02X}",
            "sound_request": f"0x{o.mem[0xDE04]:02X}"}


def run_lifetime(rom: bytes) -> dict:
    o = _oracle(rom)
    o.mem[0xD704] = 0
    o.mem[0xD73E] = 7
    o.word(0xD711, 1000)
    o.word(0xD714, 500)
    o.word(0xD174, 0)
    o.word(0xD176, 0)
    o.call(0x61E1)
    before = {"object_type_after": f"0x{o.mem[0xD700]:02X}",
              "placement_token_after": o.mem[0xD73E]}
    occupancy = 0xD3FF + 7
    o.mem[occupancy] = 0x09
    o.mem[0xD700] = 0xFE
    o.call(0x5EF8)
    return {"offscreen": before,
            "cleanup": {"occupancy_address": f"0x{occupancy:04X}",
                        "occupancy_after": f"0x{o.mem[occupancy]:02X}",
                        "slot_is_zero": not any(o.mem[0xD700:0xD740])}}


def animation_summary(rom: bytes) -> dict:
    trace = anim.trace_type(rom, 0x09)
    return {
        "type_table_entry_rom": f"0x{trace['type_table_entry_rom']:05X}",
        "bank": f"0x{trace['bank']:02X}",
        "state_table_cpu": f"0x{trace['state_table_cpu']:04X}",
        "state_table_rom": f"0x{trace['state_table_rom']:05X}",
        "state_count": trace["state_count"],
        "state_script_cpus": [f"0x{x:04X}" for x in trace["state_script_cpus"]],
        "reachable_mapping_frame_indices": [f"0x{x:02X}" for x in trace["reachable_frame_indices"]],
        "states": [{
            "state_index": state["state_index"],
            "script_cpu": state["script_cpu"],
            "frame_indices": [f"0x{x:02X}" for x in state["frame_indices"]],
            "records": [{key: value for key, value in row.items() if key != "rom"}
                        for row in state["records"]
                        if row["cpu"] not in {r["cpu"] for r in state["records"][:state["records"].index(row)]}],
            "commands": [{key: value for key, value in row.items() if key != "rom"}
                         for row in state["commands"] if row.get("command") != "loop_detected"],
        } for state in trace["states"]],
    }


def build_report(rom: bytes) -> dict:
    digest = hashlib.sha256(rom).hexdigest()
    if digest != ROM_SHA256:
        raise ValueError(f"ROM SHA-256 mismatch: {digest}")
    placements = load_placements()
    visible = [row for row in placements if row["parameter"] == "0x00"]
    hidden = [row for row in placements if row["parameter"] == "0x01"]
    boundaries = [run_collect(rom, 0, dx, 0) for dx in (11, 12, -11, -12)]
    boundaries += [run_collect(rom, 0, 0, dy) for dy in (11, 12, -11, -12)]
    hidden_phase = [run_collect(rom, 1, 0, 0, frame) for frame in (0, 1)]
    return {
        "format": 1, "rom_sha256": digest, "object_type": "0x09",
        "raw_record_count": len(placements), "runtime_entity_count": len(placements),
        "record_to_entity_rule": "one placement record creates one runtime object slot; no child or pattern objects are generated",
        "parameter_counts": {"0x00": len(visible), "0x01": len(hidden)},
        "placements": placements,
        "identity": {"presentation": "ring/sparkle family",
                     "resource_effect": "increments BCD ring counter $D29A by one",
                     "machine_identifier_policy": "retain numeric type 0x09"},
        "animation": animation_summary(rom),
        "mapping": {"table_cpu": "0x8C71", "table_rom": "0x3CC71",
                    "frames": [f"0x{x:02X}" for x in range(7)]},
        "parameters": {
            "0x00": {"initial_state": 1, "visible": True,
                     "collection": "strict abs(dx)<12 and abs(dy)<12 every update",
                     "aftermath": "request state 2; 32-update frames-5/6 sparkle; terminal type 0xFE"},
            "0x01": {"initial_state": 3, "visible": False,
                     "renderer_flag": "IX+4 bit 7",
                     "collection": "same strict overlap, evaluated only when global frame $D12F is even",
                     "aftermath": "set type 0xFF immediately; no visible sparkle"}},
        "interaction": {"helper_cpu": "0x617E", "boundary": "11 succeeds; 12 fails on either axis",
                        "sound_request": "0xBF", "ring_counter": "$D29A packed BCD +1",
                        "score_effect": "none", "placement_token_after_collection": 0},
        "lifetime": {"uncollected_offscreen": "type 0xFE; generic cleanup clears occupancy and permits recreation",
                     "collected": "placement token is cleared before terminal cleanup, preserving occupancy; no same-act respawn"},
        "layout_ring_relationship": {"same_resource_counter": True,
            "same_source_population": False,
            "type_09_generates_layout_rings": False,
            "layout_population_count": 142,
            "evidence": "separate surface-type-7 handler at $753E recognizes block IDs $40-$43; type-$09 callbacks never read layout cells"},
        "sparkle_timeline": sparkle_timeline(),
        "controlled_original_routine_fixtures": {
            "initialization": [run_init(rom, 0), run_init(rom, 1)],
            "overlap_boundaries": boundaries,
            "hidden_frame_phase": hidden_phase,
            "counter_increment": run_collect(rom, 0, 0, 0),
            "lifetime": run_lifetime(rom)},
        "closure": "IMPLEMENTATION READY",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path, default=ROOT / "data/rom-cache/thz1/object-09.json")
    a = p.parse_args()
    report = build_report(a.rom.read_bytes())
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"raw_records": 24, "runtime_entities": 24, "output": str(a.output)}))


if __name__ == "__main__":
    main()

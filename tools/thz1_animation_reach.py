#!/usr/bin/env python3
"""Trace THZ1 object animation scripts to the mapping frame indices they can use.

This is the layer above thz1_object_assets.py.

Evidence chain reproduced by this tool:

    object type
      -> animation state table at CPU $65BA
      -> state script pointer
      -> animation records writing IX+6 (frame index)
      -> bank-$0F object mapping table
      -> concrete frame record
      -> structural PNG preview

The engine maps bank $0C before calling the animation routine for object types
below $26, and bank $1E for types $26 and above. The THZ1 targets
($09/$10/$18/$1B/$21) are therefore decoded from bank $0C.

ROM-derived output stays under build/.

Python 3.10+.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]

V2_PATH = ROOT / "tools" / "thz1_object_assets.py"
spec = importlib.util.spec_from_file_location("thz1_object_assets", V2_PATH)
v2 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(v2)

GRAPHICS_MAP = ROOT / "data" / "rom-cache" / "thz1" / "graphics-map.json"
OBJECT_RECORDS = ROOT / "data" / "rom-cache" / "thz1" / "object-records.json"

ANIM_TYPE_TABLE_ROM = 0x65BA
TARGET_TYPES = (0x09, 0x10, 0x18, 0x1B, 0x21)

# Hard anchors from recovered ROM regions already in the reference repository.
SPIKE_STATE_TABLE_CPU = 0xAC4A
SPIKE_STATE_POINTERS = (0xAC54, 0xAC5A, 0xAC65, 0xAC6E, 0xAC74)
SPRING_STATE_TABLE_CPU = 0x8212
SPRING_STATE_POINTERS = (
    0x8226, 0x822C, 0x8232, 0x823C, 0x8242,
    0x8248, 0x824E, 0x8254, 0x83B3, 0x83B9,
)

# Animation control commands now verified by the THZ1 object work.
# Unsupported forms still stop the static trace rather than being guessed.
#
# FF 00            restart current state's script
# FF 01 <lo> <hi>  call absolute routine, then resume parser
# FF 02 <xlo> <xhi> <ylo> <yhi>
#                    set signed 8.8 velocity (runtime may negate X for bit 4)
# FF 03 <state>    request another animation/object state
# FF 06 <sound>    write sound request byte to PlaySound ($DE04)
# FF 07 <lo> <hi>  jump to absolute script CPU address
# FF 0B <offset> <mask>  object[offset] &= mask
# FF 0C <offset> <mask>  object[offset] |= mask
# FF 0E <count>    set loop counter at IX+$33
# FF 0F <lo> <hi>  decrement loop counter; jump while nonzero
SUPPORTED_COMMANDS = {
    0x00, 0x01, 0x02, 0x03, 0x06, 0x07, 0x0B, 0x0C, 0x0E, 0x0F
}


def u16(data: bytes, pos: int) -> int:
    if pos < 0 or pos + 2 > len(data):
        raise ValueError(f"u16 outside ROM at 0x{pos:X}")
    return data[pos] | (data[pos + 1] << 8)


def animation_bank(type_id: int) -> int:
    return 0x0C if type_id < 0x26 else 0x1E


def cpu_to_rom(bank: int, cpu: int) -> int:
    if not 0x8000 <= cpu <= 0xBFFF:
        raise ValueError(
            f"CPU pointer ${cpu:04X} outside slot-2 range for bank ${bank:02X}"
        )
    return bank * 0x4000 + (cpu - 0x8000)


def animation_state_table(rom: bytes, type_id: int) -> dict:
    entry_rom = ANIM_TYPE_TABLE_ROM + (type_id - 1) * 2
    cpu = u16(rom, entry_rom)
    bank = animation_bank(type_id)
    rom_off = cpu_to_rom(bank, cpu)

    first_script = u16(rom, rom_off)
    delta = first_script - cpu
    if delta <= 0 or delta % 2:
        raise ValueError(
            f"type ${type_id:02X}: cannot infer state-table length from "
            f"${cpu:04X} -> first script ${first_script:04X}"
        )
    count = delta // 2
    if not 1 <= count <= 64:
        raise ValueError(
            f"type ${type_id:02X}: implausible state count {count}"
        )

    pointers = [u16(rom, rom_off + i * 2) for i in range(count)]
    for p in pointers:
        cpu_to_rom(bank, p)

    return {
        "type_id": type_id,
        "type_table_entry_rom": entry_rom,
        "bank": bank,
        "state_table_cpu": cpu,
        "state_table_rom": rom_off,
        "state_count": count,
        "state_script_cpus": pointers,
    }


def parse_state_script(
    rom: bytes,
    bank: int,
    script_cpu: int,
    state_index: int,
    max_steps: int = 256,
) -> dict:
    """Statically follow one animation state script.

    Ordinary records are four bytes:
        duration, frame_index, callback_lo, callback_hi

    Control bytes start with FF. Unsupported commands stop with an explicit
    unresolved record rather than being guessed.
    """
    start_cpu = script_cpu
    pc = script_cpu
    loop_counter: Optional[int] = None
    seen = set()
    records: List[dict] = []
    frames: List[int] = []
    commands: List[dict] = []
    unresolved: Optional[dict] = None

    for _ in range(max_steps):
        # FF 0F can legitimately revisit the same PC with a changing counter.
        visit_key = (pc, loop_counter)
        if visit_key in seen:
            commands.append({
                "cpu": f"0x{pc:04X}",
                "command": "loop_detected",
            })
            break
        seen.add(visit_key)

        rom_pos = cpu_to_rom(bank, pc)
        opcode = rom[rom_pos]

        if opcode != 0xFF:
            if rom_pos + 4 > len(rom):
                raise ValueError(f"truncated animation record at ${pc:04X}")
            duration = opcode
            frame_index = rom[rom_pos + 1]
            callback = u16(rom, rom_pos + 2)
            records.append({
                "cpu": f"0x{pc:04X}",
                "rom": f"0x{rom_pos:05X}",
                "duration": f"0x{duration:02X}",
                "frame_index": frame_index,
                "callback_cpu": f"0x{callback:04X}",
                "raw": " ".join(f"{b:02X}" for b in rom[rom_pos:rom_pos + 4]),
            })
            frames.append(frame_index)
            pc += 4
            continue

        cmd = rom[rom_pos + 1]
        cmd_record = {
            "cpu": f"0x{pc:04X}",
            "rom": f"0x{rom_pos:05X}",
            "command": f"0x{cmd:02X}",
        }

        if cmd not in SUPPORTED_COMMANDS:
            cmd_record["status"] = "unsupported"
            commands.append(cmd_record)
            unresolved = cmd_record
            break

        if cmd == 0x00:
            cmd_record["meaning"] = "restart_state_script"
            cmd_record["target_cpu"] = f"0x{start_cpu:04X}"
            commands.append(cmd_record)
            pc = start_cpu
            continue

        if cmd == 0x01:
            target = u16(rom, rom_pos + 2)
            cmd_record["meaning"] = "call_routine"
            cmd_record["target_cpu"] = f"0x{target:04X}"
            commands.append(cmd_record)
            pc += 4
            continue

        if cmd == 0x02:
            x_velocity = u16(rom, rom_pos + 2)
            y_velocity = u16(rom, rom_pos + 4)
            cmd_record["meaning"] = "set_velocity_8_8"
            cmd_record["x_velocity_raw"] = f"0x{x_velocity:04X}"
            cmd_record["y_velocity_raw"] = f"0x{y_velocity:04X}"
            cmd_record["x_runtime_note"] = (
                "negated when object flags byte +0x04 bit 4 is set"
            )
            commands.append(cmd_record)
            pc += 6
            continue

        if cmd == 0x03:
            target_state = rom[rom_pos + 2]
            cmd_record["meaning"] = "request_state"
            cmd_record["target_state"] = target_state
            commands.append(cmd_record)
            break

        if cmd == 0x06:
            sound = rom[rom_pos + 2]
            cmd_record["meaning"] = "sound_request"
            cmd_record["sound_id"] = f"0x{sound:02X}"
            commands.append(cmd_record)
            pc += 3
            continue

        if cmd == 0x07:
            target = u16(rom, rom_pos + 2)
            cpu_to_rom(bank, target)
            cmd_record["meaning"] = "jump"
            cmd_record["target_cpu"] = f"0x{target:04X}"
            commands.append(cmd_record)
            pc = target
            continue

        if cmd in (0x0B, 0x0C):
            offset = rom[rom_pos + 2]
            mask = rom[rom_pos + 3]
            cmd_record["meaning"] = (
                "and_object_field" if cmd == 0x0B else "or_object_field"
            )
            cmd_record["offset"] = f"0x{offset:02X}"
            cmd_record["mask"] = f"0x{mask:02X}"
            commands.append(cmd_record)
            pc += 4
            continue

        if cmd == 0x0E:
            loop_counter = rom[rom_pos + 2]
            cmd_record["meaning"] = "set_loop_counter"
            cmd_record["count"] = loop_counter
            commands.append(cmd_record)
            pc += 3
            continue

        if cmd == 0x0F:
            target = u16(rom, rom_pos + 2)
            cpu_to_rom(bank, target)
            if loop_counter is None:
                cmd_record["status"] = "loop_counter_not_initialized"
                commands.append(cmd_record)
                unresolved = cmd_record
                break
            loop_counter = (loop_counter - 1) & 0xFF
            cmd_record["meaning"] = "decrement_loop_and_jump"
            cmd_record["counter_after"] = loop_counter
            cmd_record["target_cpu"] = f"0x{target:04X}"
            commands.append(cmd_record)
            pc = target if loop_counter else pc + 4
            continue

    else:
        unresolved = {
            "cpu": f"0x{pc:04X}",
            "command": "step_limit",
            "status": "unresolved",
        }

    return {
        "state_index": state_index,
        "script_cpu": f"0x{script_cpu:04X}",
        "script_rom": f"0x{cpu_to_rom(bank, script_cpu):05X}",
        "frame_indices": sorted(set(frames)),
        "records": records,
        "commands": commands,
        "unresolved": unresolved,
    }

def trace_type(rom: bytes, type_id: int) -> dict:
    table = animation_state_table(rom, type_id)
    states = [
        parse_state_script(
            rom,
            table["bank"],
            script_cpu,
            state_index=i,
        )
        for i, script_cpu in enumerate(table["state_script_cpus"])
    ]
    reachable = sorted({
        frame
        for state in states
        for frame in state["frame_indices"]
    })
    unresolved = [
        state["state_index"]
        for state in states
        if state["unresolved"] is not None
    ]
    return {
        **table,
        "type_id_text": f"0x{type_id:02X}",
        "states": states,
        "reachable_frame_indices": reachable,
        "unresolved_states": unresolved,
    }


def validate_animation_anchors(rom: bytes) -> dict:
    """Hard gate using recovered type-$1B and type-$26 script regions."""
    spike = animation_state_table(rom, 0x1B)
    if spike["state_table_cpu"] != SPIKE_STATE_TABLE_CPU:
        raise AssertionError(
            f"$1B state table ${spike['state_table_cpu']:04X}, "
            f"expected ${SPIKE_STATE_TABLE_CPU:04X}"
        )
    if tuple(spike["state_script_cpus"]) != SPIKE_STATE_POINTERS:
        raise AssertionError(
            f"$1B state pointers {spike['state_script_cpus']!r}, "
            f"expected {SPIKE_STATE_POINTERS!r}"
        )

    spike_trace = trace_type(rom, 0x1B)
    if spike_trace["reachable_frame_indices"] != [0x0E]:
        raise AssertionError(
            f"$1B reachable frames {spike_trace['reachable_frame_indices']}, "
            "expected only frame $0E"
        )
    if spike_trace["unresolved_states"]:
        raise AssertionError(
            f"$1B parser unresolved states: {spike_trace['unresolved_states']}"
        )

    spring = animation_state_table(rom, 0x26)
    if spring["state_table_cpu"] != SPRING_STATE_TABLE_CPU:
        raise AssertionError(
            f"$26 state table ${spring['state_table_cpu']:04X}, "
            f"expected ${SPRING_STATE_TABLE_CPU:04X}"
        )
    if tuple(spring["state_script_cpus"]) != SPRING_STATE_POINTERS:
        raise AssertionError(
            f"$26 state pointers {spring['state_script_cpus']!r}, "
            f"expected {SPRING_STATE_POINTERS!r}"
        )

    spring_trace = trace_type(rom, 0x26)
    if spring_trace["reachable_frame_indices"] != [0, 1, 2, 3]:
        raise AssertionError(
            f"$26 reachable frames {spring_trace['reachable_frame_indices']}, "
            "expected $00/$01/$02/$03"
        )
    if spring_trace["unresolved_states"]:
        raise AssertionError(
            f"$26 parser unresolved states: {spring_trace['unresolved_states']}"
        )

    return {
        "spikes_1B": "pass",
        "spring_26": "pass",
    }


def mapping_frame_cpu(rom: bytes, type_id: int, frame_index: int) -> int:
    mapping = v2.object_mapping(rom, type_id)
    pos = mapping["mapping_rom"] + frame_index * 2
    cpu = u16(rom, pos)
    # Concrete frame records used by the renderer live in bank $0F.
    v2.cpu15_to_rom(cpu)
    return cpu


def object_bases(object_records: dict, type_id: int) -> List[Tuple[int, int]]:
    return v2.placement_bases(object_records, type_id)


def render_reachable(
    rom: bytes,
    graphics_map: dict,
    object_records: dict,
    type_trace: dict,
    output_dir: Path,
    scale: int,
) -> List[dict]:
    vram, _ = v2.build_vram(rom, graphics_map)
    type_id = type_trace["type_id"]
    bases = object_bases(object_records, type_id)
    tile_base = bases[0][0] if bases else 0

    output_dir.mkdir(parents=True, exist_ok=True)
    rendered = []
    sheet = []

    for frame_index in type_trace["reachable_frame_indices"]:
        frame_cpu = mapping_frame_cpu(rom, type_id, frame_index)
        frame = v2.parse_frame_record(rom, frame_cpu)
        result = v2.render_frame(vram, frame, tile_base, scale=scale)

        item = {
            "frame_index": frame_index,
            "frame_cpu": f"0x{frame_cpu:04X}",
            "frame_rom": f"0x{v2.cpu15_to_rom(frame_cpu):05X}",
            "piece_count": frame["piece_count"],
            "tile_offsets": [f"0x{x:02X}" for x in frame["tile_offsets"]],
        }

        if result is not None:
            w, h, rgba, meta = result
            name = f"frame_index_{frame_index:02X}_{frame_cpu:04X}.png"
            v2.write_rgba_png(output_dir / name, w, h, rgba)
            item["png"] = name
            item["render"] = meta
            sheet.append((name, w, h, rgba))
        else:
            item["png"] = None
            item["render"] = None

        rendered.append(item)

    v2.make_contact_sheet(sheet, output_dir / "reachable_contact.png")
    return rendered


def json_ready_trace(trace: dict) -> dict:
    out = dict(trace)
    out["type_table_entry_rom"] = f"0x{out['type_table_entry_rom']:05X}"
    out["bank"] = f"0x{out['bank']:02X}"
    out["state_table_cpu"] = f"0x{out['state_table_cpu']:04X}"
    out["state_table_rom"] = f"0x{out['state_table_rom']:05X}"
    out["state_script_cpus"] = [f"0x{x:04X}" for x in out["state_script_cpus"]]
    out["reachable_frame_indices"] = [
        f"0x{x:02X}" for x in out["reachable_frame_indices"]
    ]
    return out


def report_text(summary: dict) -> str:
    lines = [
        "# THZ1 animation reachability",
        "",
        "## HARD VALIDATION",
        "",
        "- Type `$1B` recovered spike scripts resolve to mapping frame index `$0E` only.",
        "- Type `$26` recovered spring scripts resolve to mapping frame indices "
        "`$00/$01/$02/$03`.",
        "- Both anchor checks passed before `$09/$10/$18` results were accepted.",
        "",
        "## REACHABLE FRAME INDICES",
        "",
        "| Type | Anim bank | State table | States | Reachable mapping indices | Unresolved states |",
        "|---:|---:|---:|---:|---|---|",
    ]
    for obj in summary["objects"]:
        frames = ", ".join(obj["reachable_frame_indices"]) or "none"
        unresolved = ", ".join(str(x) for x in obj["unresolved_states"]) or "none"
        lines.append(
            f"| `{obj['type_id_text']}` | `{obj['bank']}` | "
            f"`{obj['state_table_cpu']}` | {obj['state_count']} | "
            f"{frames} | {unresolved} |"
        )

    lines += [
        "",
        "## INTERPRETATION LIMITS",
        "",
        "- This report establishes which mapping frame indices are reachable from "
        "the per-type animation state scripts under the supported control commands.",
        "- It does not assign semantic names to `$09`, `$10` or `$18`.",
        "- `FF 00`, `FF 01`, `FF 02`, `FF 03`, `FF 06`, `FF 07`, `FF 0B`, "
        "`FF 0C`, `FF 0E` and `FF 0F` are interpreted. If another command is "
        "encountered, that state is marked "
        "unresolved rather than guessed.",
        "- PNGs are structural grayscale previews using the same THZ1 VRAM load "
        "reconstruction as v2; they are not CRAM-accurate.",
        "",
        "## PER-TYPE STATES",
        "",
    ]

    for obj in summary["objects"]:
        lines += [
            f"### {obj['type_id_text']}",
            "",
        ]
        for state in obj["states"]:
            frames = ", ".join(f"`0x{x:02X}`" for x in state["frame_indices"]) or "none"
            status = "UNRESOLVED" if state["unresolved"] else "decoded"
            lines.append(
                f"- state {state['state_index']}: script `{state['script_cpu']}`, "
                f"frames {frames}, {status}"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build" / "thz1-animation-v3",
    )
    parser.add_argument("--scale", type=int, default=4)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    graphics_map = v2.load_json(GRAPHICS_MAP)
    object_records = v2.load_json(OBJECT_RECORDS)

    digest = hashlib.sha256(rom).hexdigest()
    if digest != graphics_map["rom_sha256"]:
        raise SystemExit(
            f"ROM SHA-256 mismatch: {digest}; expected {graphics_map['rom_sha256']}"
        )

    # Preserve the v2 renderer/mapping hard gate as well.
    v2.validate_known_anchors(rom, graphics_map)
    anim_validation = validate_animation_anchors(rom)
    print("Mapping anchors: PASS ($21 $26 $27 $28)")
    print("Animation anchors: PASS ($1B spikes, $26 spring)")

    args.output.mkdir(parents=True, exist_ok=True)

    traces = []
    for type_id in TARGET_TYPES:
        trace = trace_type(rom, type_id)
        rendered = render_reachable(
            rom, graphics_map, object_records, trace,
            args.output / f"{type_id:02X}",
            args.scale,
        )
        trace["rendered_reachable_frames"] = rendered
        traces.append(trace)

        frames = " ".join(f"${x:02X}" for x in trace["reachable_frame_indices"]) or "none"
        unresolved = (
            ",".join(str(x) for x in trace["unresolved_states"])
            if trace["unresolved_states"] else "none"
        )
        print(
            f"${type_id:02X}: anim table ${trace['state_table_cpu']:04X}, "
            f"{trace['state_count']} states, reachable frames [{frames}], "
            f"unresolved states [{unresolved}]"
        )

        checkpoint = json_ready_trace(trace)
        (args.output / f"{type_id:02X}" / "animation.json").write_text(
            json.dumps(checkpoint, indent=2) + "\n",
            encoding="utf-8",
        )

    persisted = [json_ready_trace(t) for t in traces]
    summary = {
        "format": 1,
        "rom_sha256": digest,
        "mapping_anchor_validation": "pass",
        "animation_anchor_validation": anim_validation,
        "supported_control_commands": [
            "0x00", "0x01", "0x02", "0x03", "0x06", "0x07",
            "0x0B", "0x0C", "0x0E", "0x0F",
        ],
        "objects": persisted,
    }

    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output / "REPORT.md").write_text(
        report_text(summary) + "\n",
        encoding="utf-8",
    )

    unresolved_total = sum(len(t["unresolved_states"]) for t in traces)
    print(f"Output: {args.output}")
    if unresolved_total:
        print(
            f"Completed with {unresolved_total} unresolved state script(s). "
            "Do not infer their frame reachability until those command forms are decoded."
        )
    else:
        print("All target state scripts decoded with the supported control commands.")


if __name__ == "__main__":
    main()

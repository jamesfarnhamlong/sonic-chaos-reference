#!/usr/bin/env python3
"""Finish THZ1 type $18 graphics reconstruction.

This tool applies the dynamic graphics load requested by type $18 before
rendering its reachable mapping frames.

Verified chain:
- type $18 state-2 callback writes $12 to RAM $D3B3;
- dynamic loader treats $12 as selector 2 in the table at $7BA6;
- selector 2 points to list $7BCB;
- that list loads 16 tiles to VRAM $0D40 (tile $6A) and then 48 tiles
  to VRAM $0F40 (tile $7A), filling tile IDs $6A..$A9;
- type-$18 mapping frames 1..5 use tile offsets entirely inside $6A..$A8.

The tool is read-only with respect to the ROM/repository. PNG/JSON output is
written under build/.

Python 3.10+.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]

V2_PATH = ROOT / "tools" / "thz1_object_assets.py"
spec = importlib.util.spec_from_file_location("thz1_object_assets", V2_PATH)
v2 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(v2)

GRAPHICS_MAP = ROOT / "data" / "rom-cache" / "thz1" / "graphics-map.json"

EXPECTED_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
TYPE_ID = 0x18

DYNAMIC_SELECTOR = 0x12
DYNAMIC_POINTER_TABLE = 0x7BA6
EXPECTED_LIST_CPU = 0x7BCB

# The now-complete animation analysis for type $18.
EXPECTED_STATE_TABLE = 0xA7BC
EXPECTED_REACHABLE_FRAMES = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)

# Raw control anchors proving the previously unresolved state tails.
EXPECTED_STATE5_PREFIX = bytes.fromhex("FF 01 47 AA FF 06 AB 40 01 2F 03 FF 07 26 A8")
EXPECTED_STATE6_PREFIX = bytes.fromhex("FF 0E 04 FF 06 AA 02 01 2F 03 02 02 2F 03")
EXPECTED_STATE6_TAIL = bytes.fromhex("FF 0F 31 A8 02 02 FA A8 FF 00")


def u16(data: bytes, pos: int) -> int:
    return data[pos] | (data[pos + 1] << 8)


def banked_cpu_to_rom(bank: int, cpu: int) -> int:
    if not 0x8000 <= cpu <= 0xBFFF:
        raise ValueError(f"CPU ${cpu:04X} outside slot 2")
    return bank * 0x4000 + (cpu - 0x8000)


def validate_animation_tail(rom: bytes) -> None:
    state5 = banked_cpu_to_rom(0x0C, 0xA81F)
    state6 = banked_cpu_to_rom(0x0C, 0xA82E)
    tail = banked_cpu_to_rom(0x0C, 0xA85D)

    if rom[state5:state5 + len(EXPECTED_STATE5_PREFIX)] != EXPECTED_STATE5_PREFIX:
        raise AssertionError("type $18 state-5 bytes differ from verified prefix")
    if rom[state6:state6 + len(EXPECTED_STATE6_PREFIX)] != EXPECTED_STATE6_PREFIX:
        raise AssertionError("type $18 state-6 bytes differ from verified prefix")
    if rom[tail:tail + len(EXPECTED_STATE6_TAIL)] != EXPECTED_STATE6_TAIL:
        raise AssertionError("type $18 state-6 tail differs from verified bytes")


def dynamic_list_for_selector(rom: bytes, selector: int) -> Tuple[int, List[dict]]:
    if selector < 0x10:
        raise ValueError("this helper covers the >= $10 dynamic-list path only")

    index = selector - 0x10
    ptr_pos = DYNAMIC_POINTER_TABLE + index * 2
    list_cpu = u16(rom, ptr_pos)

    if selector == DYNAMIC_SELECTOR and list_cpu != EXPECTED_LIST_CPU:
        raise AssertionError(
            f"selector $12 points to ${list_cpu:04X}, expected ${EXPECTED_LIST_CPU:04X}"
        )

    pos = list_cpu
    entries = []
    while True:
        bank_byte = rom[pos]
        if bank_byte == 0xFF:
            break

        count = rom[pos + 1]
        vram_dest = u16(rom, pos + 2)
        source_cpu = u16(rom, pos + 4)

        bank = bank_byte & 0x1F
        source_rom = banked_cpu_to_rom(bank, source_cpu)

        entries.append({
            "list_rom": pos,
            "bank_byte": bank_byte,
            "bank": bank,
            "tile_count": count,
            "vram_destination": vram_dest,
            "tile_base": vram_dest // 32,
            "source_cpu": source_cpu,
            "source_rom": source_rom,
            "remap": bool(bank_byte & 0x80),
        })
        pos += 6

    return list_cpu, entries


def apply_dynamic_entries(vram: bytearray, rom: bytes, entries: List[dict]) -> None:
    for entry in entries:
        count = entry["tile_count"]
        source = entry["source_rom"]
        dest = entry["vram_destination"]
        byte_count = count * 32
        raw = rom[source:source + byte_count]

        if len(raw) != byte_count:
            raise ValueError("truncated dynamic graphics source")

        if entry["remap"]:
            raw = v2.apply_rom_remap(raw, rom)

        end = dest + len(raw)
        if end > len(vram):
            raise ValueError("dynamic load exceeds 16 KiB VRAM image")
        vram[dest:end] = raw


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build" / "thz1-type18-final",
    )
    ap.add_argument("--scale", type=int, default=4)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(
            f"ROM SHA-256 mismatch: {digest}; expected {EXPECTED_SHA256}"
        )

    graphics_map = v2.load_json(GRAPHICS_MAP)
    if graphics_map["rom_sha256"] != digest:
        raise AssertionError("graphics-map ROM hash does not match ROM")

    # Preserve the known frame/mapping gate.
    v2.validate_known_anchors(rom, graphics_map)
    validate_animation_tail(rom)

    # Type-$18 animation-state table anchor from the v3 run.
    type_table_entry = 0x65BA + (TYPE_ID - 1) * 2
    state_table = u16(rom, type_table_entry)
    if state_table != EXPECTED_STATE_TABLE:
        raise AssertionError(
            f"type $18 state table ${state_table:04X}, expected ${EXPECTED_STATE_TABLE:04X}"
        )

    # Build normal THZ1 VRAM first, then reproduce the dynamic $12 load.
    vram, static_manifest = v2.build_vram(rom, graphics_map)
    list_cpu, dynamic_entries = dynamic_list_for_selector(rom, DYNAMIC_SELECTOR)
    apply_dynamic_entries(vram, rom, dynamic_entries)

    # Hard-check that selector $12 fills exactly tiles $6A..$A9.
    ranges = [
        (e["tile_base"], e["tile_base"] + e["tile_count"] - 1)
        for e in dynamic_entries
    ]
    if ranges != [(0x6A, 0x79), (0x7A, 0xA9)]:
        raise AssertionError(f"unexpected selector-$12 tile ranges: {ranges!r}")

    args.output.mkdir(parents=True, exist_ok=True)

    mapping = v2.object_mapping(rom, TYPE_ID)
    rendered_sheet = []
    frames = []

    for frame_index in EXPECTED_REACHABLE_FRAMES:
        # Frame zero is shared/empty; preserve it in metadata but no PNG.
        pos = mapping["mapping_rom"] + frame_index * 2
        frame_cpu = u16(rom, pos)
        frame = v2.parse_frame_record(rom, frame_cpu)

        item = {
            "frame_index": f"0x{frame_index:02X}",
            "frame_cpu": f"0x{frame_cpu:04X}",
            "frame_rom": f"0x{v2.cpu15_to_rom(frame_cpu):05X}",
            "piece_count": frame["piece_count"],
            "tile_offsets": [f"0x{x:02X}" for x in frame["tile_offsets"]],
        }

        result = v2.render_frame(vram, frame, 0, scale=args.scale)
        if result is not None:
            w, h, rgba, meta = result
            name = f"frame_{frame_index:02X}_{frame_cpu:04X}.png"
            v2.write_rgba_png(args.output / name, w, h, rgba)
            rendered_sheet.append((name, w, h, rgba))
            item["png"] = name
            item["render"] = meta
        else:
            item["png"] = None
            item["render"] = None

        frames.append(item)

    v2.make_contact_sheet(
        rendered_sheet,
        args.output / "reachable_contact_dynamic.png",
    )

    summary = {
        "rom_sha256": digest,
        "type_id": "0x18",
        "state_table_cpu": f"0x{state_table:04X}",
        "reachable_frame_indices": [
            f"0x{x:02X}" for x in EXPECTED_REACHABLE_FRAMES
        ],
        "animation_tail_validation": "pass",
        "dynamic_selector": "0x12",
        "dynamic_list_cpu": f"0x{list_cpu:04X}",
        "dynamic_entries": [
            {
                "list_rom": f"0x{e['list_rom']:05X}",
                "bank_byte": f"0x{e['bank_byte']:02X}",
                "bank": f"0x{e['bank']:02X}",
                "tile_count": e["tile_count"],
                "vram_destination": f"0x{e['vram_destination']:04X}",
                "tile_base": f"0x{e['tile_base']:02X}",
                "source_cpu": f"0x{e['source_cpu']:04X}",
                "source_rom": f"0x{e['source_rom']:05X}",
                "remap": e["remap"],
            }
            for e in dynamic_entries
        ],
        "frames": frames,
    }

    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Known mapping anchors: PASS")
    print("Type $18 animation tail: PASS")
    print(f"Dynamic selector $12 -> list ${list_cpu:04X}")
    for e in dynamic_entries:
        first = e["tile_base"]
        last = first + e["tile_count"] - 1
        print(
            f"  bank ${e['bank']:02X} CPU ${e['source_cpu']:04X} "
            f"ROM ${e['source_rom']:05X} -> VRAM ${e['vram_destination']:04X} "
            f"tiles ${first:02X}-${last:02X} ({e['tile_count']} tiles)"
        )
    print("Reachable frames: $00 $01 $02 $03 $04 $05")
    print(f"Output: {args.output}")
    print("Review reachable_contact_dynamic.png")


if __name__ == "__main__":
    main()

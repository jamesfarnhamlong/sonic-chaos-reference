"""Build a deterministic, metadata-only cache of Sonic Chaos THZ1 ROM data."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OBJECT_START = 0x705AE
OBJECT_END = 0x7078B
LAYOUT_START = 0x48000

DECODED_TYPES = {
    0x1B: "retracting_spikes",
    0x26: "concealed_spring",
    0x28: "moving_platform",
}

TERRAIN_KINDS = {
    48: "upright_spring",
    49: "upright_spring",
    51: "horizontal_spring",
    54: "diagonal_spring",
    56: "diagonal_spring",
    61: "static_spike_block",
    71: "ring_monitor_block",
}

RING_OFFSETS = {
    64: ((8, 8), (24, 8)),
    65: ((8, 24), (24, 24)),
    66: ((8, 8),),
    67: ((24, 8),),
}


def decode_layout(rom):
    out = []
    pos = LAYOUT_START
    while len(out) < 4095:
        value = rom[pos]
        pos += 1
        if value == 0xFF:
            value, count = rom[pos:pos + 2]
            pos += 2
            if count == 0:
                break
            out.extend([value] * min(count, 4095 - len(out)))
        else:
            out.append(value)
    if len(out) != 4095:
        raise AssertionError(f"THZ1 layout decoded to {len(out)} cells")
    return out, pos


def decode_objects(rom):
    records = []
    pos = OBJECT_START
    while rom[pos] != 0xFF:
        raw = rom[pos:pos + 9]
        stored_x = int.from_bytes(raw[1:3], "little")
        stored_y = int.from_bytes(raw[3:5], "little")
        type_id = raw[0]
        records.append({
            "index": len(records) + 1,
            "rom_offset": f"0x{pos:05X}",
            "raw_bytes": raw.hex(" ").upper(),
            "type_id": f"0x{type_id:02X}",
            "decoded_kind": DECODED_TYPES.get(type_id),
            "stored_x": stored_x,
            "stored_y": stored_y,
            "world_x": stored_x - 256,
            "world_y": stored_y - 256,
            "flags": f"0x{raw[5]:02X}",
            "parameter": f"0x{raw[6]:02X}",
            "aux0": f"0x{raw[7]:02X}",
            "aux1": f"0x{raw[8]:02X}",
        })
        pos += 9
    if len(records) != 53 or pos != OBJECT_END:
        raise AssertionError((len(records), hex(pos)))
    return records


def layout_interactions(layout):
    terrain = []
    rings = []
    for index, block_id in enumerate(layout):
        x = index % 128 * 32
        y = index // 128 * 32
        if block_id in TERRAIN_KINDS:
            terrain.append({
                "block_id": block_id,
                "kind": TERRAIN_KINDS[block_id],
                "x": x,
                "y": y,
                "source": "THZ1 bounded layout cell",
            })
        for dx, dy in RING_OFFSETS.get(block_id, ()):
            rings.append({
                "block_id": block_id,
                "kind": "ring",
                "x": x + dx,
                "y": y + dy,
                "source": "ring pixels within THZ1 layout block",
            })
    return {"terrain": terrain, "rings": rings}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/rom-cache/thz1"))
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("ROM hash differs; cache offsets are revision-specific")
    args.output.mkdir(parents=True, exist_ok=True)

    layout, layout_end = decode_layout(rom)
    records = decode_objects(rom)
    interactions = layout_interactions(layout)
    object_path = args.output / "object-records.json"
    interaction_path = args.output / "layout-interactions.json"
    write_json(object_path, {
        "rom_sha256": digest,
        "record_start": f"0x{OBJECT_START:05X}",
        "terminator": f"0x{OBJECT_END:05X}",
        "coordinate_bias": 256,
        "records": records,
    })
    write_json(interaction_path, {
        "rom_sha256": digest,
        "layout_start": f"0x{LAYOUT_START:05X}",
        "compressed_read_end": f"0x{layout_end:05X}",
        "runtime_cells": len(layout),
        "row_width_cells": 128,
        **interactions,
    })
    manifest = {
        "format": 1,
        "rom_sha256": digest,
        "policy": "metadata only; no ROM, graphics, or audio bytes",
        "files": {},
    }
    for path in (object_path, interaction_path):
        manifest["files"][path.name] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
    write_json(args.output / "manifest.json", manifest)
    print(json.dumps({
        "objects": len(records),
        "decoded_objects": sum(r["decoded_kind"] is not None for r in records),
        "terrain_interactions": len(interactions["terrain"]),
        "rings": len(interactions["rings"]),
    }))


if __name__ == "__main__":
    main()

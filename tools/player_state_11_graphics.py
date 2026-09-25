#!/usr/bin/env python3
"""Extract the exact normal-Sonic presentation for state-$11 frames $38-$3A."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import thz1_object_assets as assets

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
FRAME_IDS = (0x38, 0x39, 0x3A)
PLAYER_TILE_TABLE_ROM = 0x0104B
PLAYER_MAPPING_POINTER_ROM = 0x3C002


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dynamic_source(rom: bytes, frame_id: int) -> dict:
    entry = PLAYER_TILE_TABLE_ROM + frame_id * 4
    bank = rom[entry]
    cpu = assets.u16(rom, entry + 1)
    blocks = rom[entry + 3]
    if not 0x8000 <= cpu <= 0xBFFF:
        raise ValueError(f"frame ${frame_id:02X} source outside slot 2")
    source = bank * 0x4000 + cpu - 0x8000
    raw = rom[source:source + blocks * 64]
    if len(raw) != blocks * 64:
        raise ValueError("truncated player graphics source")
    return {
        "table_entry_rom": f"0x{entry:05X}",
        "raw_entry": " ".join(f"{x:02X}" for x in rom[entry:entry + 4]),
        "bank": f"0x{bank:02X}",
        "source_cpu": f"0x{cpu:04X}",
        "source_rom": f"0x{source:05X}",
        "transfer_blocks_64_bytes": blocks,
        "tile_count": len(raw) // 32,
        "vram_destination": "0x0000",
        "resulting_tile_indices": [f"0x{x:02X}" for x in range(len(raw) // 32)],
        "tile_bytes_sha256": sha(raw),
        "raw": raw,
    }


def render_unscaled(rom: bytes, frame: dict, raw: bytes) -> tuple[int, int, bytes, dict]:
    vram = bytearray(0x4000)
    vram[:len(raw)] = raw
    result = assets.render_frame(
        vram, frame, 0, scale=1, margin=0,
        palette=assets.thz1_sprite_palette(rom),
    )
    if result is None:
        raise AssertionError("state-$11 frame unexpectedly empty")
    return result


def build(rom: bytes, output: Path | None = None) -> dict:
    digest = sha(rom)
    if digest != ROM_SHA256:
        raise ValueError(f"ROM SHA-256 mismatch: {digest}")
    mapping = assets.object_mapping(rom, 1)
    pointers = assets.mapping_frame_pointers(rom, mapping["mapping_cpu"], 128)
    palette = assets.thz1_sprite_palette(rom)
    palette_raw_pos = assets.PALETTE_DATA_ROM + assets.THZ1_SPRITE_PALETTE * 16
    frames = []
    if output:
        output.mkdir(parents=True, exist_ok=True)
    for frame_id in FRAME_IDS:
        frame_cpu = pointers[frame_id]
        parsed = assets.parse_frame_record(rom, frame_cpu)
        source = dynamic_source(rom, frame_id)
        width, height, rgba, render = render_unscaled(rom, parsed, source["raw"])
        if output:
            assets.write_rgba_png(output / f"frame-{frame_id:02X}.png", width, height, rgba)
        frames.append({
            "animation_frame_index": f"0x{frame_id:02X}",
            "mapping_pointer_entry_rom": f"0x{mapping['mapping_rom'] + frame_id * 2:05X}",
            "mapping_frame_cpu": f"0x{frame_cpu:04X}",
            "mapping_frame_rom": f"0x{parsed['frame_rom']:05X}",
            "mapping_record": assets.serialise_frame(parsed),
            "graphics_transfer": {k: v for k, v in source.items() if k != "raw"},
            "render": {
                **render,
                "canvas_width": width,
                "canvas_height": height,
                "gamemaker_origin_x": -render["bounds"]["min_x"],
                "gamemaker_origin_y": -render["bounds"]["min_y"],
                "rgba_sha256": sha(rgba),
            },
        })
    return {
        "format": 1,
        "rom_sha256": digest,
        "evidence": "byte-verified mapping plus deterministic graphics reconstruction",
        "player_type": "0x01",
        "animation_script": {"cpu": "0x8334", "rom": "0x30334", "cadence": [
            {"updates": 8, "frame": "0x38"}, {"updates": 4, "frame": "0x39"},
            {"updates": 8, "frame": "0x3A"}, {"updates": 4, "frame": "0x39"},
        ]},
        "renderer": {
            "animation_mapping_resolver_cpu": "0x64FA",
            "sat_y_cpu": "0x226A",
            "sat_x_tile_cpu": "0x22B6",
            "dynamic_tile_loader_cpu": "0x0D15",
            "change_detector_cpu": "0x1027",
            "mapping_table_cpu": f"0x{mapping['mapping_cpu']:04X}",
            "mapping_table_rom": f"0x{mapping['mapping_rom']:05X}",
            "tile_base": "0x00",
            "horizontal_mirroring": "object +$04 bit 4 mirrors piece X coordinates; LoadPlayerTiles uses the ROM $0100 bit-reversal table to mirror tile bytes into the same VRAM destination",
        },
        "palette": {
            "level_palette_table_rom": f"0x{assets.LEVEL_PALETTE_INDEX_ROM:05X}",
            "selector": f"0x{assets.THZ1_SPRITE_PALETTE:02X}",
            "palette_rom": f"0x{palette_raw_pos:05X}",
            "raw": " ".join(f"{x:02X}" for x in rom[palette_raw_pos:palette_raw_pos + 16]),
            "raw_sha256": sha(rom[palette_raw_pos:palette_raw_pos + 16]),
            "rgba": [list(x) for x in palette],
            "index_zero": "transparent",
        },
        "frames": frames,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path, default=ROOT / "build" / "player-state-11")
    p.add_argument("--metadata", type=Path)
    args = p.parse_args()
    report = build(args.rom.read_bytes(), args.output)
    if args.metadata:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"frames": len(report["frames"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()

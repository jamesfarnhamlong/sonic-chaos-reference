#!/usr/bin/env python3
"""Reproduce the low-selector dynamic graphics used with THZ1 type $10.

ROM-derived PNGs and binary data are emitted only below build/.  The committed
JSON contains addresses, composition facts and hashes, never extracted pixels.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_TOOL = ROOT / "tools" / "thz1_object_assets.py"
spec = importlib.util.spec_from_file_location("thz1_object_assets", ASSET_TOOL)
assets = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(assets)

GRAPHICS_MAP = ROOT / "data" / "rom-cache" / "thz1" / "graphics-map.json"
EXPECTED_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
SELECTORS = (0x02, 0x04, 0x06)
PLAYER_TYPES = {"0x01": (0x7CBB, 0x7CD3), "alternate": (0x7CC7, 0x7CDF)}
DESTINATIONS = ((0x0980, 6), (0x0BC0, 4))
MAPPING_FRAMES = (0x0B, 0x0C)


def u16(data: bytes, pos: int) -> int:
    return data[pos] | (data[pos + 1] << 8)


def bank14_to_rom(cpu: int) -> int:
    if not 0x8000 <= cpu <= 0xBFFF:
        raise ValueError(f"bank-$0E pointer outside slot 2: ${cpu:04X}")
    return 0x0E * 0x4000 + (cpu - 0x8000)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pixel_bytes(raw_tiles: bytes) -> bytes:
    return bytes(
        pixel
        for pos in range(0, len(raw_tiles), 32)
        for row in assets.decode_mode4_tile(raw_tiles[pos:pos + 32])
        for pixel in row
    )


def pointer(rom: bytes, table: int, selector: int) -> dict:
    entry = table + selector * 2
    cpu = u16(rom, entry)
    rom_pos = bank14_to_rom(cpu)
    return {
        "pointer_table_cpu": f"0x{table:04X}",
        "pointer_entry_rom": f"0x{entry:05X}",
        "source_cpu": f"0x{cpu:04X}",
        "source_rom": f"0x{rom_pos:05X}",
    }


def render_compositions(rom: bytes, output: Path | None, selector: int, sources: list[dict],
                        base_vram: bytearray, palette: list[tuple]) -> dict:
    vram = bytearray(base_vram)
    streams = []
    for source, (dest, count) in zip(sources, DESTINATIONS):
        pos = int(source["source_rom"], 16)
        raw = rom[pos:pos + count * 32]
        if len(raw) != count * 32:
            raise ValueError("truncated dynamic tile source")
        vram[dest:dest + len(raw)] = raw
        streams.append({
            **source,
            "encoding": "raw_sms_mode4_planar_4bpp",
            "transform": "none; direct ROM-to-VRAM copy",
            "byte_count": len(raw),
            "tile_count": count,
            "vram_destination": f"0x{dest:04X}",
            "resulting_tile_indices": [f"0x{x:02X}" for x in range(dest // 32, dest // 32 + count)],
            "tile_bytes_sha256": sha(raw),
            "decoded_pixel_indices_sha256": sha(pixel_bytes(raw)),
        })

    mapping = assets.object_mapping(rom, 0x10)
    frames = []
    sheet = []
    for frame_index in MAPPING_FRAMES:
        frame_cpu = u16(rom, mapping["mapping_rom"] + frame_index * 2)
        frame = assets.parse_frame_record(rom, frame_cpu)
        result = assets.render_frame(vram, frame, 0, scale=4, palette=palette)
        assert result is not None
        width, height, rgba, render_meta = result
        name = f"selector-{selector:02X}-frame-{frame_index:02X}.png"
        if output is not None:
            assets.write_rgba_png(output / name, width, height, rgba)
        sheet.append((name, width, height, rgba))
        frames.append({
            "frame_index": f"0x{frame_index:02X}",
            "frame_cpu": f"0x{frame_cpu:04X}",
            "frame_rom": f"0x{assets.cpu15_to_rom(frame_cpu):05X}",
            "tile_offsets": [f"0x{x:02X}" for x in frame["tile_offsets"]],
            "used_tile_indices": [f"0x{x:02X}" for x in render_meta["used_tiles"]],
            "rgba_sha256": sha(rgba),
            "png": name,
        })
    sheet_name = f"selector-{selector:02X}.png"
    if output is not None:
        assets.make_contact_sheet(sheet, output / sheet_name)
    return {"streams": streams, "frames": frames, "preview": sheet_name}


def type05_bounded(rom: bytes, output: Path | None, base_vram: bytearray,
                   palette: list[tuple]) -> dict:
    mapping = assets.object_mapping(rom, 0x05)
    pointers = assets.mapping_frame_pointers(rom, mapping["mapping_cpu"], 64)
    rendered = []
    sheet = []
    for index, frame_cpu in enumerate(pointers[1:], 1):
        frame = assets.parse_frame_record(rom, frame_cpu)
        result = assets.render_frame(base_vram, frame, 0, scale=4, palette=palette)
        assert result is not None
        width, height, rgba, meta = result
        name = f"type-05-frame-{index:02X}.png"
        if output is not None:
            assets.write_rgba_png(output / name, width, height, rgba)
        sheet.append((name, width, height, rgba))
        rendered.append({
            "frame_index": f"0x{index:02X}",
            "frame_cpu": f"0x{frame_cpu:04X}",
            "frame_rom": f"0x{assets.cpu15_to_rom(frame_cpu):05X}",
            "tile_offsets": [f"0x{x:02X}" for x in frame["tile_offsets"]],
            "bounds": meta["bounds"],
            "rgba_sha256": sha(rgba),
        })
    if output is not None:
        assets.make_contact_sheet(sheet, output / "type-05-contact.png")
    return {
        "evidence": "STATIC DATA and BYTE-VERIFIED ASSEMBLY; no semantic identity assigned",
        "allocation": "type 0x10 selector 0x06 allocates a zeroed type-0x05 slot with parameter 0",
        "state_table_cpu": "0x993D",
        "state_scripts_cpu": ["0x9943", "0x9949", "0x9951"],
        "parameter_0_initialization_cpu": "0x9959",
        "initialization": "parameter 0 selects frame 0, sets object flags +0x04 bits 0/1, and requests state 1",
        "state_1": "FF 05 calls CPU 0x99EA and installs CPU 0x998A in object fields +0x0C/+0x0D; 0x99EA advances frame 1..32 and wraps",
        "lifetime": "CPU 0x998A retains the object while player selector 0xD532 equals 0x06 and changes type to 0xFF after it no longer equals 0x06",
        "mapping_cpu": f"0x{mapping['mapping_cpu']:04X}",
        "mapping_rom": f"0x{mapping['mapping_rom']:05X}",
        "visible_frame_count": 32,
        "tile_offsets": ["0x20", "0x22"],
        "graphics_source": "preloaded THZ1 common sprite tiles; not either low-selector dynamic transfer",
        "spawn_position": "the reward allocator and parameter-0 initializer do not copy type-0x10 world coordinates; the 32 frame records move one visible 8x16 piece around their rendering anchor, but the exact special-render anchor path remains outside this bounded trace",
        "relationship": "a bounded visible presentation associated with player selector 0x06; no traced write places it at the consumed type-0x10 world coordinates",
        "poc_significance": "POC 18.3 omits a ROM-backed 32-frame visible effect while selector 0x06 is active; numeric reward mechanics remain independently implemented",
        "preview": "type-05-contact.png",
        "frames": rendered,
    }


def build_metadata(rom: bytes, output: Path | None = None) -> dict:
    digest = sha(rom)
    if digest != EXPECTED_SHA256:
        raise ValueError(f"ROM SHA-256 {digest}; expected {EXPECTED_SHA256}")
    graphics_map = assets.load_json(GRAPHICS_MAP)
    base_vram, static_loads = assets.build_vram(rom, graphics_map)
    palette = assets.thz1_sprite_palette(rom)
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)

    variants = []
    for player_type, tables in PLAYER_TYPES.items():
        for selector in SELECTORS:
            sources = [pointer(rom, table, selector) for table in tables]
            if player_type == "0x01":
                rendered = render_compositions(rom, output, selector, sources, base_vram, palette)
            else:
                rendered = {"streams": []}
                for source, (dest, count) in zip(sources, DESTINATIONS):
                    pos = int(source["source_rom"], 16)
                    raw = rom[pos:pos + count * 32]
                    rendered["streams"].append({
                        **source,
                        "encoding": "raw_sms_mode4_planar_4bpp",
                        "transform": "none; direct ROM-to-VRAM copy",
                        "byte_count": len(raw),
                        "tile_count": count,
                        "vram_destination": f"0x{dest:04X}",
                        "resulting_tile_indices": [f"0x{x:02X}" for x in range(dest // 32, dest // 32 + count)],
                        "tile_bytes_sha256": sha(raw),
                        "decoded_pixel_indices_sha256": sha(pixel_bytes(raw)),
                    })
            variants.append({
                "selector": f"0x{selector:02X}",
                "player_type": player_type,
                **rendered,
            })

    palette_raw = rom[assets.PALETTE_DATA_ROM + 0x06 * 16:assets.PALETTE_DATA_ROM + 0x07 * 16]
    return {
        "format": 1,
        "rom_sha256": digest,
        "evidence": "BYTE-VERIFIED ASSEMBLY plus deterministic ROM decoding",
        "loader": {
            "entry_cpu": "0x7AC2",
            "low_selector_cpu": "0x7C71",
            "selector_ram": "0xD3B3",
            "player_type_ram": "0xD500",
            "source_bank": "0x0E",
            "index_rule": "pointer = word[table_cpu + selector * 2]",
            "transfer_rule": "raw bytes copied directly to VDP data port by CPU 0x1D9C",
            "timing": "once when type 0x10 crosses off-screen to visible and copies its parameter to 0xD3B3; loader clears selector after both transfers",
            "simultaneous_requirement": "both transfers execute synchronously for every low selector",
        },
        "palette": {
            "level_palette_table_rom": "0x07F3C",
            "thz1_selectors": ["0x15", "0x06"],
            "sprite_palette_selector": "0x06",
            "palette_rom": f"0x{assets.PALETTE_DATA_ROM + 0x06 * 16:05X}",
            "raw_sha256": sha(palette_raw),
            "index_zero": "transparent for sprite rendering",
            "relationship": "dynamic tiles and shell pieces are sprites and use the same THZ1 sprite palette",
        },
        "static_thz1_load_count": len(static_loads),
        "overwrites": {
            "0x0980": "overwrites preloaded common tiles 0x4C-0x51",
            "0x0BC0": "overwrites preloaded common tiles 0x5E-0x61",
        },
        "composition": {
            "mapping_table_cpu": "0x8C71",
            "frame_0B_cpu": "0x8D0F",
            "frame_0C_cpu": "0x8D1A",
            "frame_0B": "top three 8x16 pieces use dynamic tiles 0x4C-0x51; bottom pieces use unchanged tiles 0x52-0x57",
            "frame_0C": "uses unchanged tiles 0x58-0x5D and 0x52-0x57; it does not reference either dynamic range",
            "second_transfer": "tiles 0x5E-0x61 are referenced by shared mapping frame 0x0D, not type-0x10 frames 0x0B/0x0C; no placed THZ1 type reaches frame 0x0D",
            "type_05_relationship": "type 0x05 uses its own mapping 0x8A57 and tile offsets 0x20/0x22; the second transfer is not its presentation",
        },
        "type_05_bounded": type05_bounded(rom, output, base_vram, palette),
        "variants": variants,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--output", type=Path, default=ROOT / "build" / "thz1-type10-graphics")
    ap.add_argument("--metadata", type=Path)
    args = ap.parse_args()
    metadata = build_metadata(args.rom.read_bytes(), args.output)
    target = args.metadata or args.output / "metadata.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "metadata": str(target), "selectors": ["0x02", "0x04", "0x06"]}, indent=2))


if __name__ == "__main__":
    main()

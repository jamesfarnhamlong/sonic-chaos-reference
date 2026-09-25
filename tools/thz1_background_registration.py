#!/usr/bin/env python3
"""Reconstruct bounded THZ1 background patches and compare POC 18.5 pixels."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from cache_game_data import decode_layout
from tile_decompress import decompress_tile_stream
import thz1_object_assets as assets

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
PATCHES = (
    {"name": "type10-04-336-270", "object": [336, 270], "surface_y": 288, "box": [288, 64, 384, 336]},
    {"name": "type10-04-1472-110", "object": [1472, 110], "surface_y": 128, "box": [1424, 64, 1520, 176]},
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def render_indices(rom: bytes) -> tuple[bytearray, list[int], list[dict]]:
    raw_tiles = decompress_tile_stream(rom, 0x40F9E)
    tiles = [assets.decode_mode4_tile(raw_tiles[p:p + 32]) for p in range(0, len(raw_tiles), 32)]
    blocks: list[list[list[int]]] = []
    block_meta = []
    for block_id in range(256):
        ptr_entry = 0x44000 + block_id * 2
        mapping_cpu = assets.u16(rom, ptr_entry)
        mapping_rom = 0x44000 + mapping_cpu - 0x8000
        pixels = [[0] * 32 for _ in range(32)]
        attrs = []
        for piece in range(16):
            attr = assets.u16(rom, mapping_rom + piece * 2)
            tile_id = attr & 0x1FF
            source_index = tile_id - 0xC0
            attrs.append({
                "piece": piece, "attribute": f"0x{attr:04X}",
                "vram_tile": f"0x{tile_id:03X}", "source_tile_index": source_index,
                "x_flip": bool(attr & 0x0200), "y_flip": bool(attr & 0x0400),
                "palette_1": bool(attr & 0x0800), "priority": bool(attr & 0x1000),
            })
            if not 0 <= source_index < len(tiles):
                continue
            tile = tiles[source_index]
            for py in range(8):
                for px in range(8):
                    sx = 7 - px if attr & 0x0200 else px
                    sy = 7 - py if attr & 0x0400 else py
                    pixels[(piece // 4) * 8 + py][(piece % 4) * 8 + px] = tile[sy][sx]
        blocks.append(pixels)
        block_meta.append({
            "block_id": f"0x{block_id:02X}", "pointer_entry_rom": f"0x{ptr_entry:05X}",
            "mapping_cpu": f"0x{mapping_cpu:04X}", "mapping_rom": f"0x{mapping_rom:05X}",
            "pieces": attrs,
        })
    layout, _ = decode_layout(rom)
    world = bytearray(4096 * 1024)
    for i, block_id in enumerate(layout):
        ox, oy = (i % 128) * 32, (i // 128) * 32
        block = blocks[block_id]
        for y in range(32):
            world[(oy + y) * 4096 + ox:(oy + y) * 4096 + ox + 32] = bytes(block[y])
    return world, layout, block_meta


def crop_bytes(world: bytes, box: list[int]) -> bytes:
    x0, y0, x1, y1 = box
    return b"".join(world[y * 4096 + x0:y * 4096 + x1] for y in range(y0, y1))


def rgba_world(rom: bytes, world: bytes) -> bytes:
    palette = assets.palette_rgba(rom, assets.THZ1_BACKGROUND_PALETTE)
    out = bytearray(len(world) * 4)
    for i, value in enumerate(world):
        # Background colour zero is opaque on the background plane.
        r, g, b, _ = palette[value]
        out[i * 4:i * 4 + 4] = bytes((r, g, b, 255))
    return bytes(out)


def crop_rgba(world: bytes, box: list[int]) -> bytes:
    x0, y0, x1, y1 = box
    stride = 4096 * 4
    return b"".join(world[y * stride + x0 * 4:y * stride + x1 * 4] for y in range(y0, y1))


def poc_blob(repo: Path, path: str) -> bytes:
    repo = repo.resolve()
    return subprocess.check_output([
        "git", "-c", f"safe.directory={repo.as_posix()}", "-C", str(repo),
        "show", f"origin/main:{path}",
    ])


def decode_rgba_png(data: bytes) -> tuple[int, int, bytes]:
    """Decode the non-interlaced 8-bit RGBA PNGs generated for the POC."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    p = 8
    packed = bytearray()
    width = height = None
    while p < len(data):
        n = struct.unpack(">I", data[p:p + 4])[0]
        kind = data[p + 4:p + 8]
        payload = data[p + 8:p + 8 + n]
        p += 12 + n
        if kind == b"IHDR":
            width, height, depth, colour, comp, filt, interlace = struct.unpack(">IIBBBBB", payload)
            if (depth, colour, comp, filt, interlace) != (8, 6, 0, 0, 0):
                raise ValueError("unsupported PNG format")
        elif kind == b"IDAT":
            packed.extend(payload)
        elif kind == b"IEND":
            break
    if width is None or height is None:
        raise ValueError("PNG missing IHDR")
    source = zlib.decompress(bytes(packed))
    stride = width * 4
    out = bytearray(height * stride)
    prior = bytearray(stride)
    pos = 0
    for y in range(height):
        mode = source[pos]
        row = bytearray(source[pos + 1:pos + 1 + stride])
        pos += stride + 1
        for x in range(stride):
            left = row[x - 4] if x >= 4 else 0
            up = prior[x]
            upper_left = prior[x - 4] if x >= 4 else 0
            if mode == 1:
                row[x] = (row[x] + left) & 0xFF
            elif mode == 2:
                row[x] = (row[x] + up) & 0xFF
            elif mode == 3:
                row[x] = (row[x] + ((left + up) // 2)) & 0xFF
            elif mode == 4:
                estimate = left + up - upper_left
                distances = (abs(estimate - left), abs(estimate - up), abs(estimate - upper_left))
                row[x] = (row[x] + (left if distances[0] <= distances[1] and distances[0] <= distances[2]
                                      else up if distances[1] <= distances[2] else upper_left)) & 0xFF
            elif mode != 0:
                raise ValueError(f"unsupported PNG filter {mode}")
        out[y * stride:(y + 1) * stride] = row
        prior = row
    return width, height, bytes(out)


def build(rom: bytes, output: Path | None = None, poc_repo: Path | None = None) -> dict:
    if sha(rom) != ROM_SHA256:
        raise ValueError("ROM SHA-256 mismatch")
    world, layout, block_meta = render_indices(rom)
    rgba = rgba_world(rom, world)
    results = []
    for spec in PATCHES:
        box = spec["box"]
        x0, y0, x1, y1 = box
        cells = []
        for cy in range(y0 // 32, (y1 - 1) // 32 + 1):
            for cx in range(x0 // 32, (x1 - 1) // 32 + 1):
                block_id = layout[cy * 128 + cx]
                cells.append({
                    "cell": [cx, cy], "world_origin": [cx * 32, cy * 32],
                    "block_id": f"0x{block_id:02X}",
                    "block_mapping_cpu": block_meta[block_id]["mapping_cpu"],
                    "block_mapping_rom": block_meta[block_id]["mapping_rom"],
                })
        # At the object's X, record every palette-index transition around the floor.
        sample_x = spec["object"][0]
        column = [world[y * 4096 + sample_x] for y in range(y0, y1)]
        transitions = []
        previous = None
        for y, value in enumerate(column, y0):
            if value != previous:
                transitions.append({"y": y, "palette_index": value})
                previous = value
        raw_crop = crop_bytes(world, box)
        rgba_crop = crop_rgba(rgba, box)
        top_rows = []
        for y in range(spec["surface_y"], spec["surface_y"] + 32):
            values = world[y * 4096 + x0:y * 4096 + x1]
            top_rows.append({"y": y, "non_background_index_pixels": sum(v != 0 for v in values)})
        result = {
            **spec, "layout_cells": cells, "sample_x_palette_transitions": transitions,
            "canonical_indexed_crop_sha256": sha(raw_crop),
            "canonical_rgba_crop_sha256": sha(rgba_crop),
            "platform_visual_rows": {
                "background_palette_index": 0,
                "first_non_background_y_at_object_x": next(
                    y0 + i for i, value in enumerate(column) if value != 0 and y0 + i >= spec["surface_y"]
                ),
                "top_block_world_y_bounds": [spec["surface_y"], spec["surface_y"] + 31],
                "top_block_row_non_background_counts": top_rows,
                "empty_16_rows_below_collision_surface": False,
            },
        }
        if output:
            output.mkdir(parents=True, exist_ok=True)
            w, h = x1 - x0, y1 - y0
            assets.write_rgba_png(output / f"{spec['name']}.png", w, h, rgba_crop)
        if poc_repo:
            q = sample_x // 1024
            manifest = json.loads(poc_blob(poc_repo, "POC_notes/rom-cache/terrain-assets.json"))
            asset = next(x for x in manifest["assets"] if x["world_x"] == q * 1024)
            width, height, png = decode_rgba_png(poc_blob(poc_repo, asset["root_png"]))
            local_x0, local_x1 = x0 - q * 1024, x1 - q * 1024
            poc_crop = b"".join(png[y * width * 4 + local_x0 * 4:y * width * 4 + local_x1 * 4]
                                for y in range(y0, y1))
            row_width = (x1 - x0) * 4
            mismatch_rows = [y0 + row for row in range(y1 - y0)
                             if poc_crop[row * row_width:(row + 1) * row_width] !=
                             rgba_crop[row * row_width:(row + 1) * row_width]]
            platform_y0 = spec["surface_y"] - 32
            platform_y1 = min(y1, spec["surface_y"] + 48)
            platform_offset0 = (platform_y0 - y0) * row_width
            platform_offset1 = (platform_y1 - y0) * row_width
            canonical_platform = rgba_crop[platform_offset0:platform_offset1]
            poc_platform = poc_crop[platform_offset0:platform_offset1]
            result["poc_18_5"] = {
                "commit": "726b16eafbc92d4240fa182bb6ef699cfbcf923a",
                "asset": asset["root_png"], "asset_manifest_sha256": asset["sha256"],
                "rgba_crop_sha256": sha(poc_crop),
                "exact_rgba_match": poc_crop == rgba_crop,
                "first_mismatch": next((i // 4 for i in range(0, len(poc_crop), 4)
                    if poc_crop[i:i + 4] != rgba_crop[i:i + 4]), None),
                "mismatch_world_rows": mismatch_rows,
                "platform_registration_box": [x0, platform_y0, x1, platform_y1],
                "canonical_platform_rgba_sha256": sha(canonical_platform),
                "poc_platform_rgba_sha256": sha(poc_platform),
                "platform_exact_rgba_match": canonical_platform == poc_platform,
            }
        results.append(result)
    used_blocks = sorted({int(cell["block_id"], 16) for result in results
                          for cell in result["layout_cells"]})
    return {
        "format": 1, "rom_sha256": ROM_SHA256,
        "evidence": "deterministic ROM background reconstruction and POC read-only pixel comparison",
        "source": {
            "layout_stream_rom": "0x48000", "layout_dimensions_blocks": [128, 32],
            "block_pointer_table_rom": "0x44000", "primary_tile_stream_rom": "0x40F9E",
            "vram_base_tile": "0x0C0", "palette_selector": "0x15",
        },
        "blocks": [block_meta[x] for x in used_blocks],
        "patches": results,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path, default=ROOT / "build" / "thz1-background-registration")
    p.add_argument("--metadata", type=Path)
    p.add_argument("--poc-repo", type=Path)
    a = p.parse_args()
    report = build(a.rom.read_bytes(), a.output, a.poc_repo)
    if a.metadata:
        a.metadata.parent.mkdir(parents=True, exist_ok=True)
        a.metadata.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"patches": len(report["patches"]), "output": str(a.output)}))


if __name__ == "__main__":
    main()

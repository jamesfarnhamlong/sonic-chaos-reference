#!/usr/bin/env python3
"""Deterministic THZ1 object sprite-map extractor for Sonic Chaos (SMS).

This tool is deliberately narrow. It validates the already-known mappings for
object types $21/$26/$27/$28 before decoding the currently unknown THZ1 types.

It uses the renderer behavior preserved in:
  archive/continuation-01/overlay/SonicChaos.asm
    _LABEL_64FA_335  - object type -> mapping table -> frame record
    _LABEL_226A_108  - Y piece coordinates
    _LABEL_22B6_113  - X piece coordinates and tile-offset list

ROM-derived bytes and PNG previews are written only below build/.

Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from tile_decompress import apply_rom_remap, decompress_tile_stream

GRAPHICS_MAP = ROOT / "data" / "rom-cache" / "thz1" / "graphics-map.json"
OBJECT_RECORDS = ROOT / "data" / "rom-cache" / "thz1" / "object-records.json"

TARGET_TYPES = (0x09, 0x10, 0x18, 0x1B, 0x21, 0x26, 0x27, 0x28)
POINTER_TABLE_ROM_BASE = 0x3C000
BANK15_ROM_BASE = 0x3C000
CPU_SLOT_START = 0x8000
CPU_SLOT_END = 0xBFFF

# Frame index zero is shared by the known object mappings. We preserve it in
# metadata but exclude it from the known object-specific frame-anchor check.
KNOWN_SHARED_FRAME = 0xA0E4


def u16(data: bytes, pos: int) -> int:
    if pos < 0 or pos + 2 > len(data):
        raise ValueError(f"u16 outside input at 0x{pos:X}")
    return data[pos] | (data[pos + 1] << 8)


def s16_value(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def s16(data: bytes, pos: int) -> int:
    return s16_value(u16(data, pos))


def cpu15_to_rom(cpu: int) -> int:
    if not CPU_SLOT_START <= cpu <= CPU_SLOT_END:
        raise ValueError(f"bank-$0F CPU pointer outside $8000-$BFFF: ${cpu:04X}")
    return BANK15_ROM_BASE + (cpu - CPU_SLOT_START)


def fmt_cpu(value: int) -> str:
    return f"0x{value:04X}"


def fmt_rom(value: int) -> str:
    return f"0x{value:05X}"


def parse_hex(value: object) -> int:
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        raise TypeError(value)
    return int(value, 16)


def object_mapping(rom: bytes, type_id: int) -> dict:
    pointer_rom = POINTER_TABLE_ROM_BASE + type_id * 2
    mapping_cpu = u16(rom, pointer_rom)
    mapping_rom = cpu15_to_rom(mapping_cpu)
    return {
        "type_id": type_id,
        "pointer_table_rom": pointer_rom,
        "pointer_raw": rom[pointer_rom:pointer_rom + 2],
        "mapping_cpu": mapping_cpu,
        "mapping_rom": mapping_rom,
    }


def mapping_frame_pointers(rom: bytes, mapping_cpu: int, max_entries: int = 32) -> List[int]:
    """Read the contiguous bank-$0F frame-pointer list.

    _LABEL_64FA_335 indexes mapping_cpu with frame_index*2. There is no frame
    count byte. The known tables end where the following frame record begins;
    that next little-endian word is not a bank-$0F CPU pointer.

    The four known mappings are used as a hard validation of this stopping rule.
    """
    pos = cpu15_to_rom(mapping_cpu)
    frames: List[int] = []

    for _ in range(max_entries):
        value = u16(rom, pos)
        if not CPU_SLOT_START <= value <= CPU_SLOT_END:
            break
        frames.append(value)
        pos += 2

    if not frames:
        raise ValueError(f"no frame pointers at mapping ${mapping_cpu:04X}")
    if len(frames) == max_entries:
        raise ValueError(f"mapping ${mapping_cpu:04X} exceeded safety limit")
    return frames


def parse_frame_record(rom: bytes, frame_cpu: int) -> dict:
    """Decode the exact 11-byte structure consumed by the sprite renderer.

    From _LABEL_64FA_335:
      +0      piece count -> ix+5
      +1..2   raw word -> ix+44/45 (purpose intentionally unnamed)
      +3..4   piece-coordinate table pointer -> ix+40/41
      +5..    ix+42/43 points here

    From _LABEL_226A_108 / _LABEL_22B6_113:
      +5..6   signed Y origin added to object screen Y
      +7..8   signed X origin added to object screen X
      +9..10  pointer to one tile-offset byte per piece

    The coordinate table contains four bytes per piece:
      signed Y word, signed X word.
    """
    frame_rom = cpu15_to_rom(frame_cpu)
    if frame_rom + 11 > len(rom):
        raise ValueError(f"truncated frame record ${frame_cpu:04X}")

    piece_count = rom[frame_rom]
    if piece_count > 64:
        raise ValueError(
            f"implausible piece count {piece_count} at frame ${frame_cpu:04X}"
        )

    raw_word_1 = u16(rom, frame_rom + 1)
    coords_cpu = u16(rom, frame_rom + 3)
    y_origin = s16(rom, frame_rom + 5)
    x_origin = s16(rom, frame_rom + 7)
    tiles_cpu = u16(rom, frame_rom + 9)

    # Empty/shared frames can legitimately have no pieces. Preserve raw fields
    # without forcing their pointers through bank-$0F validation.
    pieces = []
    tile_offsets = []

    if piece_count:
        coords_rom = cpu15_to_rom(coords_cpu)
        tiles_rom = cpu15_to_rom(tiles_cpu)

        if coords_rom + piece_count * 4 > len(rom):
            raise ValueError(f"coordinate table truncated for frame ${frame_cpu:04X}")
        if tiles_rom + piece_count > len(rom):
            raise ValueError(f"tile list truncated for frame ${frame_cpu:04X}")

        for i in range(piece_count):
            p = coords_rom + i * 4
            y_offset = s16(rom, p)
            x_offset = s16(rom, p + 2)
            tile_offset = rom[tiles_rom + i]
            tile_offsets.append(tile_offset)
            pieces.append({
                "index": i,
                "y_offset": y_offset,
                "x_offset": x_offset,
                "relative_y": y_origin + y_offset,
                "relative_x": x_origin + x_offset,
                "tile_offset": tile_offset,
            })

    return {
        "frame_cpu": frame_cpu,
        "frame_rom": frame_rom,
        "piece_count": piece_count,
        "raw_word_1": raw_word_1,
        "coords_cpu": coords_cpu,
        "coords_rom": cpu15_to_rom(coords_cpu) if piece_count else None,
        "y_origin": y_origin,
        "x_origin": x_origin,
        "tile_list_cpu": tiles_cpu,
        "tile_list_rom": cpu15_to_rom(tiles_cpu) if piece_count else None,
        "tile_offsets": tile_offsets,
        "pieces": pieces,
        "raw_11": rom[frame_rom:frame_rom + 11],
    }


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_known_anchors(rom: bytes, graphics_map: dict) -> None:
    known = {
        parse_hex(item["type_id"]): item
        for item in graphics_map["object_sprite_mappings"]
    }

    failures = []
    for type_id in (0x21, 0x26, 0x27, 0x28):
        expected = known[type_id]
        actual = object_mapping(rom, type_id)

        expected_cpu = parse_hex(expected["mapping_cpu_address"])
        expected_rom = parse_hex(expected["mapping_rom_offset"])
        if actual["mapping_cpu"] != expected_cpu:
            failures.append(
                f"${type_id:02X} mapping CPU: got ${actual['mapping_cpu']:04X}, "
                f"expected ${expected_cpu:04X}"
            )
        if actual["mapping_rom"] != expected_rom:
            failures.append(
                f"${type_id:02X} mapping ROM: got ${actual['mapping_rom']:05X}, "
                f"expected ${expected_rom:05X}"
            )

        frames = mapping_frame_pointers(rom, actual["mapping_cpu"])
        specific = [f for f in frames if f != KNOWN_SHARED_FRAME]
        expected_frames = [parse_hex(v) for v in expected["frame_records"]]
        if specific != expected_frames:
            failures.append(
                f"${type_id:02X} frames: got "
                f"{[f'${v:04X}' for v in specific]}, expected "
                f"{[f'${v:04X}' for v in expected_frames]}"
            )

    if failures:
        raise AssertionError(
            "KNOWN-ANCHOR VALIDATION FAILED; unknown types were not decoded:\n  "
            + "\n  ".join(failures)
        )


def build_vram(rom: bytes, graphics_map: dict) -> Tuple[bytearray, List[dict]]:
    """Reproduce the THZ1 graphics-load order into a 16 KiB VRAM image."""
    vram = bytearray(0x4000)
    manifest = []

    streams = [graphics_map["level_art"]["primary_stream"]]
    streams.extend(graphics_map["supplemental_list"]["entries"])

    for stream in streams:
        stream_rom = parse_hex(stream["stream_rom_offset"])
        decoded = decompress_tile_stream(rom, stream_rom)
        if stream.get("transform_remap"):
            decoded = apply_rom_remap(decoded, rom)

        dest = parse_hex(stream["vram_destination"])
        end = dest + len(decoded)
        if end > len(vram):
            raise ValueError(
                f"{stream['id']} would write beyond VRAM: ${dest:04X}..${end:04X}"
            )
        vram[dest:end] = decoded

        expected = stream.get("expected_tile_count")
        actual_tiles = len(decoded) // 32
        if expected is not None and actual_tiles != expected:
            raise AssertionError(
                f"{stream['id']} decoded {actual_tiles} tiles, expected {expected}"
            )

        manifest.append({
            "id": stream["id"],
            "vram_destination": dest,
            "tile_base": dest // 32,
            "tile_count": actual_tiles,
            "transform_remap": bool(stream.get("transform_remap")),
        })

    return vram, manifest


def decode_mode4_tile(raw: bytes) -> List[List[int]]:
    if len(raw) != 32:
        raise ValueError("SMS Mode 4 tile must contain 32 bytes")
    pixels = [[0] * 8 for _ in range(8)]
    for y in range(8):
        p0, p1, p2, p3 = raw[y * 4:y * 4 + 4]
        for x in range(8):
            bit = 7 - x
            pixels[y][x] = (
                ((p0 >> bit) & 1)
                | (((p1 >> bit) & 1) << 1)
                | (((p2 >> bit) & 1) << 2)
                | (((p3 >> bit) & 1) << 3)
            )
    return pixels


def tile_pixels(vram: bytes, tile_id: int) -> List[List[int]]:
    tile_id &= 0xFF
    pos = tile_id * 32
    return decode_mode4_tile(vram[pos:pos + 32])


def rgba_for_index(index: int) -> Tuple[int, int, int, int]:
    if index == 0:
        return (0, 0, 0, 0)
    # Neutral preview only; this is not an attempt to reconstruct CRAM.
    level = 24 + round(index * (231 / 15))
    return (level, level, level, 255)


def blank_rgba(width: int, height: int) -> bytearray:
    return bytearray(width * height * 4)


def set_pixel(buf: bytearray, width: int, height: int, x: int, y: int,
              rgba: Tuple[int, int, int, int]) -> None:
    if not (0 <= x < width and 0 <= y < height):
        return
    p = (y * width + x) * 4
    # Palette zero is transparent. Do not overwrite an existing non-transparent
    # piece with transparent pixels.
    if rgba[3] == 0:
        return
    buf[p:p + 4] = bytes(rgba)


def render_frame(vram: bytes, frame: dict, tile_base: int,
                 scale: int = 4, margin: int = 4) -> Optional[Tuple[int, int, bytes, dict]]:
    pieces = frame["pieces"]
    if not pieces:
        return None

    min_x = min(p["relative_x"] for p in pieces)
    min_y = min(p["relative_y"] for p in pieces)
    max_x = max(p["relative_x"] + 8 for p in pieces)
    max_y = max(p["relative_y"] + 16 for p in pieces)

    logical_w = max_x - min_x
    logical_h = max_y - min_y
    width = (logical_w + margin * 2) * scale
    height = (logical_h + margin * 2) * scale
    buf = blank_rgba(width, height)

    nonzero = 0
    used_tiles = []

    for piece in pieces:
        tile_id = (tile_base + piece["tile_offset"]) & 0xFF
        # SMS 8x16 sprite mode uses a consecutive pair of 8x8 patterns.
        used_tiles.extend([tile_id, (tile_id + 1) & 0xFF])
        top = tile_pixels(vram, tile_id)
        bottom = tile_pixels(vram, tile_id + 1)
        pix16 = top + bottom

        ox = piece["relative_x"] - min_x + margin
        oy = piece["relative_y"] - min_y + margin

        for py, row in enumerate(pix16):
            for px, pal in enumerate(row):
                if pal:
                    nonzero += 1
                rgba = rgba_for_index(pal)
                for sy in range(scale):
                    for sx in range(scale):
                        set_pixel(
                            buf, width, height,
                            (ox + px) * scale + sx,
                            (oy + py) * scale + sy,
                            rgba,
                        )

    meta = {
        "bounds": {
            "min_x": min_x, "min_y": min_y,
            "max_x": max_x, "max_y": max_y,
            "width": logical_w, "height": logical_h,
        },
        "tile_base": tile_base,
        "used_tiles": used_tiles,
        "nonzero_source_pixels": nonzero,
    }
    return width, height, bytes(buf), meta


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_rgba_png(path: Path, width: int, height: int, rgba: bytes) -> None:
    if len(rgba) != width * height * 4:
        raise ValueError("RGBA buffer size mismatch")
    rows = []
    stride = width * 4
    for y in range(height):
        rows.append(b"\x00" + rgba[y * stride:(y + 1) * stride])
    raw = b"".join(rows)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def placement_bases(object_records: dict, type_id: int) -> List[Tuple[int, int]]:
    out = set()
    wanted = f"0x{type_id:02X}"
    for record in object_records["records"]:
        if record["type_id"].upper() == wanted.upper():
            out.add((parse_hex(record["aux0"]), parse_hex(record["aux1"])))
    return sorted(out)


def primary_normal_base(bases: List[Tuple[int, int]]) -> int:
    """Renderer's ordinary (not X-flipped) tile base is IX+8 == aux0."""
    return bases[0][0] if bases else 0


def serialise_frame(frame: dict) -> dict:
    out = {**frame, "pieces": [dict(p) for p in frame["pieces"]]}
    for key in ("frame_cpu", "coords_cpu", "tile_list_cpu"):
        if out[key] is not None:
            out[key] = fmt_cpu(out[key])
    for key in ("frame_rom", "coords_rom", "tile_list_rom"):
        if out[key] is not None:
            out[key] = fmt_rom(out[key])
    out["raw_word_1"] = f"0x{out['raw_word_1']:04X}"
    out["raw_11"] = " ".join(f"{b:02X}" for b in out["raw_11"])
    out["tile_offsets"] = [f"0x{v:02X}" for v in out["tile_offsets"]]
    for piece in out["pieces"]:
        piece["tile_offset"] = f"0x{piece['tile_offset']:02X}"
    return out


def make_contact_sheet(rendered: Sequence[Tuple[str, int, int, bytes]],
                       output: Path, gap: int = 8) -> None:
    if not rendered:
        return
    width = max(w for _, w, _, _ in rendered)
    height = sum(h for _, _, h, _ in rendered) + gap * (len(rendered) - 1)
    canvas = blank_rgba(width, height)
    y0 = 0
    for _, w, h, rgba in rendered:
        for y in range(h):
            src = rgba[y * w * 4:(y + 1) * w * 4]
            dst_start = ((y0 + y) * width) * 4
            canvas[dst_start:dst_start + w * 4] = src
        y0 += h + gap
    write_rgba_png(output, width, height, bytes(canvas))


def build_report(summary: dict) -> str:
    lines = [
        "# THZ1 object graphics extraction",
        "",
        "## VERIFIED FROM ROM",
        "",
        f"- ROM SHA-256: `{summary['rom_sha256']}`",
        "- Known `$21/$26/$27/$28` mapping addresses and object-specific frame "
        "pointers matched `data/rom-cache/thz1/graphics-map.json` before unknown "
        "types were decoded.",
        "- Object mapping pointer entry used: `0x3C000 + type * 2`.",
        "- Mapping tables were followed as 16-bit bank-$0F frame pointers, as "
        "used by `_LABEL_64FA_335`.",
        "- Frame records were interpreted with the coordinate/tile reads used by "
        "`_LABEL_226A_108` and `_LABEL_22B6_113`.",
        "",
        "| Type | Pointer ROM | Mapping CPU | Mapping ROM | Frames | aux0/aux1 |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for obj in summary["objects"]:
        bases = ", ".join(
            f"${a:02X}/${b:02X}" for a, b in obj["placement_bases_numeric"]
        ) or "none"
        lines.append(
            f"| `${obj['type_id']}` | `{obj['pointer_table_rom']}` | "
            f"`{obj['mapping_cpu']}` | `{obj['mapping_rom']}` | "
            f"{len(obj['frames'])} | {bases} |"
        )

    lines += [
        "",
        "## INFERRED STRUCTURE",
        "",
        "- The names `x_origin` and `y_origin` describe how the renderer uses the "
        "signed words at frame-record offsets +7 and +5. Unknown/raw fields are "
        "not assigned semantic names beyond what the code proves.",
        "- Preview PNGs use the normal tile base (`aux0`) and neutral grayscale "
        "palette indices. They are structural previews, not CRAM-accurate art.",
        "",
        "## VISUAL / OUTPUT CHECKS",
        "",
    ]

    for obj in summary["objects"]:
        nonblank = sum(
            1 for f in obj["frames"]
            if f.get("render") and f["render"]["nonzero_source_pixels"] > 0
        )
        lines.append(
            f"- `{obj['type_id']}`: {nonblank}/{len(obj['frames'])} frame entries "
            "produced non-blank normal-base previews."
        )

    lines += [
        "",
        "## UNRESOLVED",
        "",
        "- Semantic identities for object types remain unchanged; this extractor "
        "does not name unknown objects from appearance.",
        "- CRAM/palette selection is not decoded here.",
        "- X-flipped rendering is not emitted yet. The game switches to `aux1` "
        "and mirrors X coordinates when object flag bit 4 is set.",
        "- A shared frame pointer (commonly `$A0E4`) is preserved in metadata. "
        "It is not treated as an object-specific frame during anchor validation.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build" / "thz1-assets-v2",
    )
    parser.add_argument("--scale", type=int, default=4)
    args = parser.parse_args()

    if args.scale < 1 or args.scale > 16:
        raise SystemExit("--scale must be between 1 and 16")

    graphics_map = load_json(GRAPHICS_MAP)
    object_records = load_json(OBJECT_RECORDS)
    rom = args.rom.read_bytes()

    digest = hashlib.sha256(rom).hexdigest()
    if digest != graphics_map["rom_sha256"]:
        raise SystemExit(
            f"ROM SHA-256 mismatch: {digest}; expected {graphics_map['rom_sha256']}"
        )

    # Hard gate: if our method cannot reproduce the already-proven mappings,
    # it is not allowed to analyse the unknown object types.
    validate_known_anchors(rom, graphics_map)
    print("Known-anchor validation: PASS ($21 $26 $27 $28)")

    vram, vram_manifest = build_vram(rom, graphics_map)

    args.output.mkdir(parents=True, exist_ok=True)
    objects = []

    for type_id in TARGET_TYPES:
        mapping = object_mapping(rom, type_id)
        frame_ptrs = mapping_frame_pointers(rom, mapping["mapping_cpu"])
        bases = placement_bases(object_records, type_id)
        tile_base = primary_normal_base(bases)

        type_dir = args.output / f"{type_id:02X}"
        type_dir.mkdir(parents=True, exist_ok=True)
        rendered_for_contact = []
        frames_out = []

        for index, frame_cpu in enumerate(frame_ptrs):
            frame = parse_frame_record(rom, frame_cpu)
            serial = serialise_frame(frame)
            serial["frame_index"] = index
            serial["shared_frame"] = frame_cpu == KNOWN_SHARED_FRAME

            rendered = render_frame(vram, frame, tile_base, scale=args.scale)
            if rendered is not None:
                w, h, rgba, render_meta = rendered
                name = f"frame_{index:02d}_{frame_cpu:04X}.png"
                write_rgba_png(type_dir / name, w, h, rgba)
                serial["render"] = {
                    **render_meta,
                    "png": name,
                }
                rendered_for_contact.append((name, w, h, rgba))
            else:
                serial["render"] = None

            frames_out.append(serial)

        make_contact_sheet(rendered_for_contact, type_dir / "contact.png")

        obj = {
            "type_id": f"0x{type_id:02X}",
            "pointer_table_rom": fmt_rom(mapping["pointer_table_rom"]),
            "pointer_raw": " ".join(f"{b:02X}" for b in mapping["pointer_raw"]),
            "mapping_cpu": fmt_cpu(mapping["mapping_cpu"]),
            "mapping_rom": fmt_rom(mapping["mapping_rom"]),
            "placement_bases": [
                {"aux0": f"0x{a:02X}", "aux1": f"0x{b:02X}"}
                for a, b in bases
            ],
            # Kept only while creating the Markdown report; removed from JSON.
            "placement_bases_numeric": bases,
            "normal_preview_tile_base": f"0x{tile_base:02X}",
            "frames": frames_out,
        }
        objects.append(obj)

        # Per-type checkpoint survives interruption/context loss.
        checkpoint = dict(obj)
        checkpoint.pop("placement_bases_numeric", None)
        (type_dir / "metadata.json").write_text(
            json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8"
        )

        specific = [p for p in frame_ptrs if p != KNOWN_SHARED_FRAME]
        print(
            f"${type_id:02X}: mapping ${mapping['mapping_cpu']:04X}, "
            f"{len(frame_ptrs)} frame entries "
            f"({len(specific)} object-specific)"
        )

    summary = {
        "format": 1,
        "rom_sha256": digest,
        "known_anchor_validation": "pass",
        "renderer_sources": [
            "_LABEL_64FA_335",
            "_LABEL_226A_108",
            "_LABEL_22B6_113",
        ],
        "vram_loads": vram_manifest,
        "objects": objects,
    }

    report = build_report(summary)

    # Remove helper numeric values from persisted JSON.
    for obj in summary["objects"]:
        obj.pop("placement_bases_numeric", None)

    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    (args.output / "REPORT.md").write_text(report + "\n", encoding="utf-8")

    print(f"Output: {args.output}")
    print("Done. Review contact.png and REPORT.md before promoting any findings.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generic, ROM-derived level-package extractor for the Sonic Chaos SMS ROM.

Everything here is derived from the version-checked ROM. Nothing is copied from
historical offset lists; those are kept only as *comparison* values
(``HISTORICAL_REFERENCE``) and the extractor records whether the ROM agrees.

Act descriptors are built from the original engine's own tables:

    act header table        file $5082 (zone -> act -> 22-byte record),
                            consumed by the loader at $4FDC..$5081
    player start table      file $4E98 (zone -> act -> 8 bytes), loader $4E57
    object-list pointers    bank $1C / CPU $8546 (file $70546), placement
                            creator at file $70000
    level art entries       file $7CED + 7 * (zone*3 + act), loader $78E1
    palette selectors       file $7F3C + 2 * (zone*3 + act), loader $794F

Evidence classes used in the emitted JSON:
    DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED,
    CONTROLLED ROUTINE RESULT, HISTORICAL REFERENCE ONLY, UNRESOLVED
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import rom as rom_tables  # noqa: E402  (collision-header reader)
import thz1_object_assets as assets  # noqa: E402
from tile_decompress import apply_rom_remap, decompress_tile_stream  # noqa: E402

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
FORMAT = 1
DEFAULT_OUTPUT = ROOT / "data" / "rom-cache" / "levels"

# --- engine tables (all BYTE-VERIFIED against the loader disassembly) -------
ACT_HEADER_TABLE = 0x5082          # loader $4FDC: table[zone] -> table[act]
ACT_HEADER_SIZE = 22
START_TABLE = 0x4E98               # loader $4E57
OBJECT_ZONE_TABLE_ROM = 0x70546    # bank $1C, CPU $8546 (placement creator)
OBJECT_BANK = 0x1C
OBJECT_RECORD_SIZE = 9
ART_TABLE = 0x7CED                 # loader $78E1: (zone*3+act)*7
ART_ENTRY_SIZE = 7
PALETTE_SELECT_TABLE = 0x7F3C      # loader $794F: (zone*3+act)*2
PALETTE_DATA = 0x3B64D             # 16-byte records
LAYOUT_RAM_BASE = 0xC001           # loader $4DBE
LAYOUT_RAM_LIMIT_CELLS = 4095      # loader stops when DE leaves $C000-$CFFF
BLOCK_PIXELS = 32                  # 4x4 tile entries per block
QUADRANT_PIXELS = 16               # handler $753E tests bit 4 of X/Y

# Ring handler tables ($753E .. $75DB, file == CPU)
RING_PRESENCE_TABLE = 0x75DC
RING_REPLACEMENT_OFFSET = 0x18
RING_FIRST_BLOCK = 0x40
RING_BLOCK_COUNT = 6
RING_SURFACE_TYPE = 7
QUADRANTS = ("top_left", "top_right", "bottom_left", "bottom_right")
QUADRANT_ORIGIN = ((0, 0), (16, 0), (0, 16), (16, 16))

ACTS = OrderedDict([
    ("thz1", {"zone": 0, "act": 0, "name": "Turquoise Hill Zone Act 1"}),
    ("thz2", {"zone": 0, "act": 1, "name": "Turquoise Hill Zone Act 2"}),
    ("thz3", {"zone": 0, "act": 2, "name": "Turquoise Hill Zone Act 3"}),
])

# HISTORICAL REFERENCE ONLY (Sonic Retro community table, as quoted in the task
# brief). Never used to locate data; compared against the ROM-derived values.
HISTORICAL_REFERENCE = {
    "thz1": {"object_list": 0x705AE, "layout": 0x48000, "width": 128, "height": 32,
             "mapping": 0x44000, "tiles": 0x40F9E, "fg_palette": 0x3B6AD, "bg_palette": 0x3B79D},
    "thz2": {"object_list": 0x7078C, "layout": 0x48BA9, "width": 128, "height": 32,
             "mapping": 0x44000, "tiles": 0x40F9E, "fg_palette": 0x3B6AD, "bg_palette": 0x3B79D},
    "thz3": {"object_list": 0x708FE, "layout": 0x49815, "width": 80, "height": 16,
             "mapping": 0x44000, "tiles": 0x40F9E, "fg_palette": 0x3B6AD, "bg_palette": 0x3B79D},
}

EVIDENCE = (
    "DECODED DATA", "BYTE-VERIFIED ASSEMBLY", "SOURCE-TRACED",
    "CONTROLLED ROUTINE RESULT", "HISTORICAL REFERENCE ONLY", "UNRESOLVED",
)


# --- small helpers -----------------------------------------------------------
def hx(value: int, digits: int = 4) -> str:
    return f"0x{value:0{digits}X}"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u16(rom: bytes, pos: int) -> int:
    return rom[pos] | (rom[pos + 1] << 8)


def s16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def bank_cpu_to_rom(bank: int, cpu: int) -> int:
    if not 0x8000 <= cpu <= 0xBFFF:
        raise ValueError(f"CPU ${cpu:04X} outside the bank-switched slot")
    return bank * 0x4000 + (cpu - 0x8000)


def rom_to_bank_cpu(offset: int) -> tuple:
    if offset < 0x4000:
        return 0, offset
    bank = offset // 0x4000
    return bank, 0x8000 + offset % 0x4000


def load_rom(path) -> bytes:
    data = Path(path).read_bytes()
    if len(data) != 524288 or sha256(data) != ROM_SHA256:
        raise ValueError("Expected Sonic Chaos (Europe) v1.2, SHA-256 " + ROM_SHA256)
    return data


def coordinate_hash(rows) -> str:
    """Stable hash of an ordered coordinate list: 'class,x,y' lines."""
    text = "".join(f"{cls},{x},{y}\n" for cls, x, y in rows)
    return sha256(text.encode("ascii"))


# --- layout stream -----------------------------------------------------------
def decode_layout_stream(rom: bytes, start: int, cell_limit: int = None) -> tuple:
    """Decode the compressed layout stream.

    Non-$FF byte: literal cell. ``FF value count``: run of ``count`` copies;
    count 0 terminates (loader $4DC4..$4DFA). ``cell_limit`` reproduces the
    original loader's RAM bound (it checks the destination before *every* write,
    including inside runs). Returns (cells, end_offset, terminated).
    """
    cells = []
    pos = start
    terminated = False
    while cell_limit is None or len(cells) < cell_limit:
        value = rom[pos]
        pos += 1
        if value == 0xFF:
            value, count = rom[pos], rom[pos + 1]
            pos += 2
            if count == 0:
                terminated = True
                break
            room = count if cell_limit is None else min(count, cell_limit - len(cells))
            cells.extend([value] * room)
        else:
            cells.append(value)
    return cells, pos, terminated


def row_offset_table(rom: bytes, cpu: int) -> dict:
    """Read the per-row offset table referenced by header word +20.

    The table lives in the always-mapped engine region (file offset == CPU
    address, exactly as the collision lookup reads it through ($D168)). Rows are
    counted while entry k equals k * stride.
    """
    stride = u16(rom, cpu + 2)
    rows = []
    while True:
        entry = u16(rom, cpu + 2 * len(rows))
        if entry != len(rows) * stride:
            break
        rows.append(entry)
    return {"cpu": cpu, "stride": stride, "rows_matching_stride": len(rows), "entries": rows}


# --- act descriptor ----------------------------------------------------------
def act_header(rom: bytes, zone: int, act: int) -> dict:
    zone_ptr = u16(rom, ACT_HEADER_TABLE + zone * 2)
    header_rom = u16(rom, zone_ptr + act * 2)
    raw = rom[header_rom:header_rom + ACT_HEADER_SIZE]
    map_bank, map_cpu = raw[0], u16(raw, 1)
    layout_bank, layout_cpu = raw[3], u16(raw, 4)
    return {
        "zone_pointer_table_rom": ACT_HEADER_TABLE + zone * 2,
        "act_pointer_rom": zone_ptr + act * 2,
        "header_rom": header_rom,
        "raw": raw.hex().upper(),
        "block_mapping_bank": map_bank,
        "block_mapping_cpu": map_cpu,
        "block_mapping_rom": bank_cpu_to_rom(map_bank, map_cpu),
        "layout_bank": layout_bank,
        "layout_cpu": layout_cpu,
        "layout_rom": bank_cpu_to_rom(layout_bank, layout_cpu),
        "width_cells": u16(raw, 6),
        "negative_width": s16(u16(raw, 8)),
        "header_word_10": u16(raw, 10),
        "ram_d280": u16(raw, 12),
        "ram_d27c": u16(raw, 14),
        "ram_d282": u16(raw, 16),
        "ram_d27e": u16(raw, 18),
        "row_offset_table_cpu": u16(raw, 20),
    }


def object_list_pointer(rom: bytes, zone: int, act: int) -> dict:
    zone_ptr_rom = OBJECT_ZONE_TABLE_ROM + zone * 2
    zone_cpu = u16(rom, zone_ptr_rom)
    act_ptr_rom = bank_cpu_to_rom(OBJECT_BANK, zone_cpu) + act * 2
    list_cpu = u16(rom, act_ptr_rom)
    return {
        "zone_pointer_rom": zone_ptr_rom,
        "act_pointer_rom": act_ptr_rom,
        "list_bank": OBJECT_BANK,
        "list_cpu": list_cpu,
        "list_rom": bank_cpu_to_rom(OBJECT_BANK, list_cpu),
    }


def player_start(rom: bytes, zone: int, act: int) -> dict:
    zone_ptr = u16(rom, START_TABLE + zone * 2)
    act_ptr_rom = zone_ptr + act * 2
    record = u16(rom, act_ptr_rom)
    return {
        "record_rom": record,
        "raw": rom[record:record + 8].hex().upper(),
        "ram_d2d6": u16(rom, record),
        "ram_d2d8": u16(rom, record + 2),
        "ram_d511": u16(rom, record + 4),
        "ram_d514": u16(rom, record + 6),
    }


def art_entry(rom: bytes, zone: int, act: int) -> dict:
    index = zone * 3 + act
    entry_rom = ART_TABLE + index * ART_ENTRY_SIZE
    raw = rom[entry_rom:entry_rom + ART_ENTRY_SIZE]
    primary = {
        "id": "primary",
        "bank_byte": raw[0],
        "vram_destination": u16(raw, 1),
        "stream_cpu": u16(raw, 3),
        "stream_rom": bank_cpu_to_rom(raw[0] & 0x1F, u16(raw, 3)),
        "transform_remap": False,
    }
    list_rom = u16(raw, 5)
    supplemental = []
    pos = list_rom
    while rom[pos] != 0xFF:
        entry = rom[pos:pos + 5]
        supplemental.append({
            "id": f"supplemental_{len(supplemental)}",
            "raw": entry.hex().upper(),
            "bank_byte": entry[0],
            "vram_destination": u16(entry, 1),
            "stream_cpu": u16(entry, 3),
            "stream_rom": bank_cpu_to_rom(entry[0] & 0x1F, u16(entry, 3)),
            "transform_remap": bool(entry[0] & 0x80),
        })
        pos += 5
    return {
        "entry_rom": entry_rom, "raw": raw.hex().upper(),
        "supplemental_list_rom": list_rom, "supplemental_terminator_rom": pos,
        "primary": primary, "supplemental": supplemental,
    }


def palette_selection(rom: bytes, zone: int, act: int) -> dict:
    index = zone * 3 + act
    pos = PALETTE_SELECT_TABLE + index * 2
    bg, sprite = rom[pos], rom[pos + 1]
    return {
        "selector_rom": pos,
        "background_index": bg,
        "sprite_index": sprite,
        "background_rom": PALETTE_DATA + bg * 16,
        "sprite_rom": PALETTE_DATA + sprite * 16,
    }


def build_descriptor(rom: bytes, key: str, metadata: dict = None) -> dict:
    """ROM-derived act descriptor. Raises if internal consistency checks fail."""
    metadata = ACTS[key] if metadata is None else metadata
    zone, act = metadata["zone"], metadata["act"]
    header = act_header(rom, zone, act)
    objects = object_list_pointer(rom, zone, act)
    width = header["width_cells"]
    cells, end, terminated = decode_layout_stream(rom, header["layout_rom"])
    if not terminated:
        raise AssertionError(f"{key}: layout stream did not terminate")
    if len(cells) % width:
        raise AssertionError(f"{key}: {len(cells)} cells not divisible by width {width}")
    height = len(cells) // width
    rows = row_offset_table(rom, header["row_offset_table_cpu"])
    consistency = {
        "negative_width_matches": header["negative_width"] == -width,
        "row_table_stride_matches_width": rows["stride"] == width,
        "row_table_covers_all_rows": rows["rows_matching_stride"] >= height,
        # Derived consistency observation (not a proven field meaning):
        # header word +18 equals world pixel height minus 240 for all three acts,
        # and word +16 equals (width - 8) * 32.
        "d27e_plus_240_equals_pixel_height": header["ram_d27e"] + 240 == height * BLOCK_PIXELS,
        "d282_equals_width_minus_8_blocks": header["ram_d282"] == (width - 8) * BLOCK_PIXELS,
        "header_word_10_equals_7_widths": header["header_word_10"] == 7 * width,
    }
    return {
        "key": key, "name": metadata["name"], "zone": zone, "act": act,
        "header": header,
        "layout": {
            "rom": header["layout_rom"], "end_rom": end,
            "encoded_cells": len(cells),
            "width_cells": width, "height_cells": height,
            "runtime_written_cells": min(len(cells), LAYOUT_RAM_LIMIT_CELLS),
        },
        "row_table": {k: rows[k] for k in ("cpu", "stride", "rows_matching_stride")},
        "consistency": consistency,
        "objects": objects,
        "start": player_start(rom, zone, act),
        "art": art_entry(rom, zone, act),
        "palette": palette_selection(rom, zone, act),
    }


def compare_historical(desc: dict) -> dict:
    ref = HISTORICAL_REFERENCE[desc["key"]]
    rom_values = {
        "object_list": desc["objects"]["list_rom"],
        "layout": desc["layout"]["rom"],
        "width": desc["layout"]["width_cells"],
        "height": desc["layout"]["height_cells"],
        "mapping": desc["header"]["block_mapping_rom"],
        "tiles": desc["art"]["primary"]["stream_rom"],
        "fg_palette": desc["palette"]["sprite_rom"],
        "bg_palette": desc["palette"]["background_rom"],
    }
    return {name: {"historical": ref[name], "rom_derived": rom_values[name],
                   "agrees": ref[name] == rom_values[name]} for name in ref}


# --- objects -----------------------------------------------------------------
def decode_object_list(rom: bytes, start: int) -> tuple:
    """Records are 9 bytes; the list ends at a record whose type byte is $FF
    (placement creator at file $70031: LD A,(HL) / INC A / JR Z)."""
    records = []
    pos = start
    while rom[pos] != 0xFF:
        raw = rom[pos:pos + OBJECT_RECORD_SIZE]
        stored_x, stored_y = u16(raw, 1), u16(raw, 3)
        bank, cpu = rom_to_bank_cpu(pos)
        records.append({
            "index": len(records) + 1,
            "zero_based_index": len(records),
            "rom_offset": hx(pos, 5),
            "bank": hx(bank, 2),
            "cpu": hx(cpu),
            "raw_bytes": " ".join(f"{b:02X}" for b in raw),
            "type_id": f"0x{raw[0]:02X}",
            "stored_x": stored_x,
            "stored_y": stored_y,
            "world_x": stored_x - 256,
            "world_y": stored_y - 256,
            "flags": f"0x{raw[5]:02X}",
            "parameter": f"0x{raw[6]:02X}",
            "aux0": f"0x{raw[7]:02X}",
            "aux1": f"0x{raw[8]:02X}",
        })
        pos += OBJECT_RECORD_SIZE
    return records, pos


# --- terrain rings -----------------------------------------------------------
def ring_tables(rom: bytes) -> dict:
    """Decode the quadrant-presence / replacement tables of handler $753E."""
    blocks = OrderedDict()
    for n in range(RING_BLOCK_COUNT):
        block = RING_FIRST_BLOCK + n
        presence = [rom[RING_PRESENCE_TABLE + n * 4 + q] for q in range(4)]
        replacement = [rom[RING_PRESENCE_TABLE + RING_REPLACEMENT_OFFSET + n * 4 + q]
                       for q in range(4)]
        blocks[block] = {
            "presence_bytes": presence,
            "quadrants": [QUADRANTS[q] for q in range(4) if presence[q]],
            "replacement_blocks": replacement,
        }
    return blocks


def surface_type_7_blocks(rom: bytes) -> list:
    return [b for b in range(256)
            if rom_tables.header(rom, b)["flags"] & 0x1F == RING_SURFACE_TYPE]


def ring_block_semantics(rom: bytes) -> dict:
    """Blocks that the terrain-ring handler can collect from.

    A ring block needs BOTH (a) collision surface type 7 (handler $753E gate,
    `AND $1F / CP 7`) and (b) at least one presence-table quadrant. Derived from
    the shared ROM tables, not assumed per act.
    """
    tables = ring_tables(rom)
    surface7 = surface_type_7_blocks(rom)
    ring_blocks = [b for b in surface7 if b in tables and tables[b]["quadrants"]]
    return {"surface_type_7_blocks": surface7, "tables": tables, "ring_blocks": ring_blocks}


def terrain_rings(act_key: str, cells: list, width: int, semantics: dict,
                  runtime_cells: int) -> list:
    rings = []
    tables = semantics["tables"]
    ring_blocks = set(semantics["ring_blocks"])
    for index, block in enumerate(cells):
        if index >= runtime_cells or block not in ring_blocks:
            continue
        cx, cy = index % width, index // width
        for q, name in enumerate(QUADRANTS):
            if not tables[block]["presence_bytes"][q]:
                continue
            ox, oy = QUADRANT_ORIGIN[q]
            cx_off, cy_off = ox + QUADRANT_PIXELS // 2, oy + QUADRANT_PIXELS // 2
            rings.append({
                "act": act_key,
                "source_class": "terrain",
                "layout_cell_index": index,
                "cell_x": cx, "cell_y": cy,
                "block_id": f"0x{block:02X}",
                "quadrant": name,
                "quadrant_origin": [ox, oy],
                "block_offset": [cx_off, cy_off],
                "world_x": cx * BLOCK_PIXELS + cx_off,
                "world_y": cy * BLOCK_PIXELS + cy_off,
                "evidence": "DECODED DATA (cell) + BYTE-VERIFIED ASSEMBLY (presence table $75DC)",
            })
    return rings


def ring_art_check(rom: bytes, vram: bytes, semantics: dict) -> dict:
    """Cross-check quadrant presence against real block art.

    For every ring block and quadrant, count non-transparent pixels the block's
    mapping draws in that 16x16 quadrant and report the pixel bbox centre. This
    confirms that the presence table agrees with the art and that quadrant
    centre (8,8) is the ring's centre.
    """
    result = OrderedDict()
    blocks = block_pixel_maps(rom, vram, only=semantics["ring_blocks"])
    for block in semantics["ring_blocks"]:
        pix = blocks[block]
        info = {}
        for q, name in enumerate(QUADRANTS):
            ox, oy = QUADRANT_ORIGIN[q]
            pts = [(x, y) for y in range(oy, oy + 16) for x in range(ox, ox + 16)
                   if pix[y][x] & 0x0F]
            if pts:
                xs = [p[0] - ox for p in pts]
                ys = [p[1] - oy for p in pts]
                info[name] = {"opaque_pixels": len(pts),
                              "bbox": [min(xs), min(ys), max(xs), max(ys)]}
            else:
                info[name] = {"opaque_pixels": 0, "bbox": None}
        result[f"0x{block:02X}"] = info
    return result


# --- graphics ----------------------------------------------------------------
def build_vram(rom: bytes, art: dict) -> tuple:
    """Reproduce the level art load (primary stream then supplemental list)."""
    vram = bytearray(0x4000)
    loads = []
    for stream in [art["primary"]] + art["supplemental"]:
        data = decompress_tile_stream(rom, stream["stream_rom"])
        if stream["transform_remap"]:
            data = apply_rom_remap(data, rom)
        dest = stream["vram_destination"]
        if dest + len(data) > len(vram):
            raise ValueError(f"{stream['id']} overruns VRAM")
        vram[dest:dest + len(data)] = data
        loads.append({
            "id": stream["id"], "vram_destination": hx(dest),
            "tile_base": hx(dest // 32, 2), "tile_count": len(data) // 32,
            "stream_rom": hx(stream["stream_rom"], 5),
            "stream_bank_cpu": "%s:%s" % (hx(stream["bank_byte"] & 0x1F, 2), hx(stream["stream_cpu"])),
            "transform_remap": stream["transform_remap"],
            "decoded_sha256": sha256(data),
        })
    return bytes(vram), loads


def block_mapping(rom: bytes, mapping_rom: int, block: int) -> dict:
    entry = mapping_rom + block * 2
    cpu = u16(rom, entry)
    # The table is an index within the bank, not the base of its pointers.
    # Loader $4FDC stores bank in $D162 and table CPU in $D164; render
    # loops $5316/$53DA dereference the resulting absolute CPU pointer.
    bank = mapping_rom // 0x4000
    rom_off = bank_cpu_to_rom(bank, cpu)
    return {"pointer_entry_rom": entry, "cpu": cpu, "rom": rom_off,
            "attributes": [u16(rom, rom_off + p * 2) for p in range(16)]}


def block_pixel_maps(rom: bytes, vram: bytes, only=None, mapping_rom: int = 0x44000) -> dict:
    """32x32 palette-index images: bits 0-3 colour, bit 4 = attribute palette 1."""
    tiles = {}

    def tile(tid):
        if tid not in tiles:
            tiles[tid] = assets.decode_mode4_tile(vram[tid * 32:tid * 32 + 32])
        return tiles[tid]

    out = {}
    for block in (range(256) if only is None else only):
        attrs = block_mapping(rom, mapping_rom, block)["attributes"]
        pixels = [[0] * 32 for _ in range(32)]
        for piece, attr in enumerate(attrs):
            tid = attr & 0x1FF
            t = tile(tid)
            for py in range(8):
                for px in range(8):
                    sx = 7 - px if attr & 0x0200 else px
                    sy = 7 - py if attr & 0x0400 else py
                    colour = t[sy][sx]
                    pixels[(piece // 4) * 8 + py][(piece % 4) * 8 + px] = (
                        0 if colour == 0 else colour | (0x10 if attr & 0x0800 else 0))
        out[block] = pixels
    return out


def block_usage(rom: bytes, cells: list, mapping_rom: int, runtime_cells: int) -> list:
    counts = Counter(cells[:runtime_cells])
    usage = []
    for block in sorted(counts):
        mapping = block_mapping(rom, mapping_rom, block)
        tiles = sorted({a & 0x1FF for a in mapping["attributes"]})
        usage.append({
            "block_id": f"0x{block:02X}", "cell_count": counts[block],
            "mapping_pointer_entry_rom": hx(mapping["pointer_entry_rom"], 5),
            "mapping_cpu": hx(mapping["cpu"]), "mapping_rom": hx(mapping["rom"], 5),
            "tile_ids": [hx(t, 3) for t in tiles],
            "any_priority_bit": any(a & 0x1000 for a in mapping["attributes"]),
            "any_palette1_bit": any(a & 0x0800 for a in mapping["attributes"]),
        })
    return usage


# --- act package -------------------------------------------------------------
def build_act(rom: bytes, key: str, metadata: dict = None) -> dict:
    desc = build_descriptor(rom, key, metadata)
    layout = desc["layout"]
    width, height = layout["width_cells"], layout["height_cells"]
    cells, _, _ = decode_layout_stream(rom, layout["rom"])
    runtime_cells = layout["runtime_written_cells"]
    records, terminator = decode_object_list(rom, desc["objects"]["list_rom"])
    semantics = ring_block_semantics(rom)
    vram, vram_loads = build_vram(rom, desc["art"])
    return {
        "key": key, "descriptor": desc, "cells": cells, "runtime_cells": runtime_cells,
        "records": records, "object_terminator_rom": terminator,
        "semantics": semantics, "vram": vram, "vram_loads": vram_loads,
        "terrain_rings": terrain_rings(key, cells, width, semantics, runtime_cells),
        "width": width, "height": height,
    }


def object_rings(act: dict) -> list:
    out = []
    for rec in act["records"]:
        if rec["type_id"] != "0x09":
            continue
        param = int(rec["parameter"], 16)
        out.append({
            "act": act["key"],
            "source_class": "object_09_visible" if param == 0 else "object_09_hidden",
            "object_index": rec["index"],
            "rom_offset": rec["rom_offset"],
            "raw_bytes": rec["raw_bytes"],
            "parameter": rec["parameter"],
            "world_x": rec["world_x"], "world_y": rec["world_y"],
            "evidence": "DECODED DATA (record) + CONTROLLED ROUTINE RESULT (init $9C10, param semantics)",
        })
    return out


def ring_hash_rows(rings: list) -> list:
    return [(r["source_class"], r["world_x"], r["world_y"]) for r in rings]


def main() -> None:  # pragma: no cover - thin CLI; heavy lifting in level_export
    import level_export
    level_export.main()


if __name__ == "__main__":
    main()

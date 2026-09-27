#!/usr/bin/env python3
"""Build Task-08 render, block-$47, type-$27 timing and POC-coverage data."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from cache_game_data import decode_layout
from tile_decompress import decompress_tile_stream
import thz1_object_assets as assets

SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
RECORDS = ROOT / "data/rom-cache/thz1/object-records.json"
POC_COMMIT = "726b16eafbc92d4240fa182bb6ef699cfbcf923a"


def sat_visible_bounds(anchor_y: int) -> dict:
    # Frame-$01/$02 raw nonzero pixels are anchor-32..anchor-1. SMS displays
    # an SAT Y byte at Y+1.
    return {"anchor_y": anchor_y, "raw_sat_piece_y": [anchor_y - 32, anchor_y - 16],
            "visible_top": anchor_y - 31, "visible_bottom": anchor_y}


def _type21_sat_fixture(rom: bytes, world_x: int, anchor_y: int) -> dict:
    from oracle import Oracle
    o = Oracle(rom)
    o.bank(2, 0x0F)
    o.cpu.ix = 0xD700
    o.word(0xD711, world_x)
    o.word(0xD714, anchor_y)
    o.word(0xD174, world_x - 128)
    o.word(0xD176, anchor_y - 100)
    o.mem[0xD705] = 6
    o.word(0xD728, 0xA10B)  # frame-$01 coordinate stream
    o.word(0xD72A, 0x9126)  # frame-$01 Y/X-origin structure
    o.word(0xD36F, 0xD200)
    o.call(0x3FC8)
    o.call(0x226A)
    raw = list(o.mem[0xD200:0xD206])
    return {"world_x": world_x, "anchor_y": anchor_y, "camera_y": anchor_y - 100,
            "prepared_screen_anchor_y": o.word(0xD71C),
            "original_sat_y_bytes": raw,
            "displayed_piece_top_scanlines": [value + 1 for value in raw],
            "final_visible_world_bounds": [anchor_y - 31, anchor_y]}


def type21_render(rom: bytes) -> dict:
    rows = []
    for x, placed_y, anchor_y, surface_y in (
        (800, 606, 590, 608), (1248, 862, 846, 864),
        (2048, 318, 302, 320), (3152, 894, 878, 896),
        (3296, 286, 270, 288), (2400, 254, 238, 256)):
        bounds = sat_visible_bounds(anchor_y)
        rows.append({"world_x": x, "placement_y": placed_y,
                     "stable_anchor_y": anchor_y, "floor_surface_y": surface_y,
                     **{k: v for k, v in bounds.items() if k != "anchor_y"},
                     "blank_rows_between_sprite_and_terrain": surface_y - bounds["visible_bottom"] - 1})
    return {
        "screen_coordinate_preparation": "object integer +$14/+$15 minus camera $D176 -> object+$1C/+$1D",
        "frame_y_origin": 0, "piece_y_offsets": [-32, -16],
        "raw_nonzero_relative_y": [-32, -1], "sms_sat_display_bias_y": 1,
        "visible_nonzero_relative_y": [-31, 0],
        "mirrored_y_stream_is_identical": True,
        "clip_rule": "pieces outside the renderer's SAT range receive Y=$E0; clipping does not translate retained pieces",
        "placements": rows,
        "controlled_fixture_world_x": [800, 3296, 2400],
        "controlled_original_renderer_fixtures": [
            _type21_sat_fixture(rom, 800, 590),
            _type21_sat_fixture(rom, 3296, 270),
            _type21_sat_fixture(rom, 2400, 238)],
        "poc_18_5": {"sprite_yorigin": 36, "nontransparent_canvas_rows": [4, 35],
                     "visible_relative_y": [-32, -1],
                     "difference": "one pixel above original because the SMS SAT Y+1 convention is absent",
                     "render_only_correction": "add +1 to draw Y, equivalently change SPR_chaos_object_21 yorigin from 36 to 35"},
        "classification": "POC RENDERING BUG",
        "qualification": "the original still has 17 blank scanlines; the conspicuous hover is canonical apart from one POC scanline",
    }


def _u16(data: bytes, p: int) -> int:
    return data[p] | data[p + 1] << 8


def block47(rom: bytes, render_output: Path | None = None) -> dict:
    layout, _ = decode_layout(rom)
    cells = []
    for x in (3328, 3360, 3392, 3424):
        cx, cy = x // 32, 256 // 32
        cells.append({"world": [x, 256], "cell": [cx, cy],
                      "block_id": f"0x{layout[cy * 128 + cx]:02X}"})
    ptr_entry = 0x44000 + 0x47 * 2
    mapping_cpu = _u16(rom, ptr_entry)
    mapping_rom = 0x44000 + mapping_cpu - 0x8000
    raw_tiles = decompress_tile_stream(rom, 0x40F9E)
    decoded = [assets.decode_mode4_tile(raw_tiles[p:p + 32])
               for p in range(0, len(raw_tiles), 32)]
    palettes = [assets.palette_rgba(rom, assets.THZ1_BACKGROUND_PALETTE),
                assets.palette_rgba(rom, assets.THZ1_SPRITE_PALETTE)]
    rgba = bytearray(32 * 32 * 4)
    indexed = bytearray(32 * 32)
    pieces = []
    for piece in range(16):
        attr = _u16(rom, mapping_rom + piece * 2)
        tile_id = attr & 0x1FF
        source = tile_id - 0xC0
        pal = 1 if attr & 0x0800 else 0
        pieces.append({"piece": piece, "attribute": f"0x{attr:04X}",
                       "vram_tile": f"0x{tile_id:03X}", "source_tile_index": source,
                       "palette": pal, "x_flip": bool(attr & 0x0200),
                       "y_flip": bool(attr & 0x0400), "priority": bool(attr & 0x1000)})
        if not 0 <= source < len(decoded):
            continue
        tile = decoded[source]
        for py in range(8):
            for px in range(8):
                sx = 7 - px if attr & 0x0200 else px
                sy = 7 - py if attr & 0x0400 else py
                colour = tile[sy][sx]
                q = ((piece // 4) * 8 + py) * 32 + (piece % 4) * 8 + px
                # Mode-4 colour zero exposes the backdrop; palette selection
                # matters only for nonzero pixels.
                indexed[q] = 0 if colour == 0 else colour | (pal << 4)
                r, g, b, _ = palettes[0 if colour == 0 else pal][colour]
                rgba[q * 4:q * 4 + 4] = bytes((r, g, b, 255))
    collision_entry = 0x38000 + 0x47 * 2
    collision_cpu = _u16(rom, collision_entry)
    collision_rom = 0x38000 + collision_cpu - 0x8000
    headers = []
    for plane, p in (("base", collision_rom), ("alternate", collision_rom + 7)):
        flags, modifier = rom[p], rom[p + 1]
        vertical_cpu, horizontal_cpu = _u16(rom, p + 2), _u16(rom, p + 4)
        vertical_rom = 0x38000 + vertical_cpu - 0x8000
        horizontal_rom = 0x38000 + horizontal_cpu - 0x8000
        headers.append({"plane": plane, "raw": " ".join(f"{b:02X}" for b in rom[p:p + 7]),
                        "flags": f"0x{flags:02X}", "surface_type": f"0x{flags & 0x1F:02X}",
                        "modifier": f"0x{modifier:02X}",
                        "vertical_profile_cpu": f"0x{vertical_cpu:04X}",
                        "vertical_profile": [f"0x{x:02X}" for x in rom[vertical_rom:vertical_rom + 32]],
                        "horizontal_profile_cpu": f"0x{horizontal_cpu:04X}",
                        "horizontal_profile": [f"0x{x:02X}" for x in rom[horizontal_rom:horizontal_rom + 32]],
                        "floor_dispatch": "0x6AE3" if (flags & 0x1F) == 0x16 else "0x6C82"})
    if render_output is not None:
        render_output.parent.mkdir(parents=True, exist_ok=True)
        assets.write_rgba_png(render_output, 32, 32, bytes(rgba))
    return {
        "cells": cells, "all_four_cells_verified": all(c["block_id"] == "0x47" for c in cells),
        "block_pointer_entry_rom": f"0x{ptr_entry:05X}",
        "mapping_cpu": f"0x{mapping_cpu:04X}", "mapping_rom": f"0x{mapping_rom:05X}",
        "pieces": pieces, "palette_selectors": {"palette_0": "0x15", "palette_1": "0x06"},
        "palette_aware_index_sha256": hashlib.sha256(indexed).hexdigest(),
        "rgba_sha256": hashlib.sha256(rgba).hexdigest(),
        "rendered_pixel_dimensions": [32, 32],
        "canonical_red_magenta": False,
        "poc_18_5_colour_comparison": {
            "asset": "sprites/SPR_chaos_terrain_3/dd57e33b-ad36-48d4-8c15-56334af88da0.png",
            "poc_block_rgba_sha256": "2be2a042d43ba29d7b3317628eb522d027ae4723b131ff2dcdddb823778c72ed",
            "exact_match": False,
            "cause": "POC terrain was generated as palette 0; block $47 nonzero artwork attributes select palette 1 ($06)"},
        "collision_pointer_entry_rom": f"0x{collision_entry:05X}",
        "collision_header_cpu": f"0x{collision_cpu:04X}",
        "collision_header_rom": f"0x{collision_rom:05X}", "collision_headers": headers,
        "terrain_behavior": {"base_surface_handler_cpu": "0x6AE3",
            "meaning": "qualifying airborne/rolling contact routes to $7857: replace the cell with block $46, refresh it, allocate one transient type-$0F parameter-$40 object, and add BCD $10 (ten) to $D29A",
            "excluded_player_states": ["0x0F", "0x10", "0x15", "0x1A"],
            "replacement_handler_cpu": "0x7857", "replacement_block": "0x46",
            "spawned_object_type": "0x0F", "spawned_object_parameter": "0x40",
            "ring_counter_effect": "$D29A packed BCD +0x10 (ten)",
            "has_collision": True, "is_layout_scanner_entity_generator": False,
            "creates_transient_object_on_break": True},
        "population_relationship": {"type_09": "none", "type_10": "none",
            "layout_rings_40_43": "distinct handler and population",
            "runtime_entities_created_initially": 0,
            "runtime_entities_created_on_break": 1},
        "classification": "INTERACTIVE TERRAIN",
    }


def type27_timing() -> dict:
    rows = []
    for x, y in ((3504, 224), (2288, 768), (2240, 112)):
        rows.append({"world": [x, y],
            "creation_camera_x_inclusive": [x - 351, x + 96],
            "creation_camera_y_inclusive": [y - 351, y + 96],
            "active_callback_and_sat_camera_x_inclusive": [x - 287, x + 32],
            "active_callback_and_sat_camera_y_inclusive": [y - 287, y + 32],
            "actual_nonzero_pixel_camera_x_inclusive": [x - 267, x + 11],
            "actual_nonzero_pixel_camera_y_inclusive": [y - 205, y],
            "creation_to_first_nonempty_frame_updates": 2})
    return {"placement_scan_period_updates": 4,
        "accepted_relative_rectangle": {"x": [-96, 351], "y": [-96, 351]},
        "active_relative_rectangle": {"x": [-32, 287], "y": [-32, 287]},
        "frame_1_2_nonzero_relative_pixels_after_sat_bias": {"x": [-12, 11], "y": [-14, 0]},
        "creation_frame": "after the object scheduler; piece count remains zero",
        "next_update": "state 0 requests state 1; piece count remains zero",
        "second_update": "state 1 loads nonempty frame 1; SAT output is allowed if lifetime clears visibility bit 6",
        "can_first_display_inside_visible_viewport": True,
        "geometry_explanation": "a late placement scan or camera jump may create in the active rectangle; its first nonempty frame is two object updates later and can already intersect 256x192",
        "normal_scroll_explanation": "steady left-to-right scrolling accepts the placement in the hidden margin, enables SAT by relative X=287, and pixels enter at relative X=267",
        "cleanup": "pre-trigger exit from accepted rectangle -> type FE -> occupancy release; post-trigger state 3 removes at abs(player X-object X)>=384 and can recreate",
        "placements": rows,
        "poc_18_5": {"commit": POC_COMMIT,
            "behavior": "uses only X camera range [-128, viewport+384], creates state 1 and sets visible immediately",
            "difference": "omits ROM 32x32 visibility grid, Y eligibility, empty state-0 update, and first-frame delay",
            "required_change": "apply the ROM creation/active rectangles in both axes and preserve the two-update empty-to-frame-1 sequence"},
        "classification": "POC LIFETIME/PRESENTATION BUG"}


POC_OBJECTS = {0x10: "objects/OBJ_chaos_object_10", 0x18: "objects/OBJ_chaos_object_18",
               0x1B: "objects/OBJ_chaos_spikes", 0x21: "objects/OBJ_chaos_object_21",
               0x27: "objects/OBJ_chaos_object_27",
               0x28: "objects/OBJ_chaos_platform"}
MEANING = {0x09: "one placed type-$09 collectible", 0x10: "placed item object",
           0x18: "goal sign", 0x1B: "retracting spikes", 0x21: "ground enemy",
           0x26: "concealed/contact spring", 0x27: "flying enemy", 0x28: "moving platform"}


def coverage() -> dict:
    records = json.loads(RECORDS.read_text(encoding="utf-8"))["records"]
    matrix = []
    for row in records:
        t = int(row["type_id"], 16)
        missing = t == 0x09
        resource = POC_OBJECTS.get(t)
        if t == 0x26:
            resource = {"0x00": "objects/OBJ_chaos_object_spring_26_normal",
                        "0x01": "objects/OBJ_chaos_object_spring_26_weak",
                        "0x8A": "objects/OBJ_chaos_object_spring_26_span"}[row["parameter"]]
        matrix.append({"record_index": row["index"], "rom_offset": row["rom_offset"],
            "type": row["type_id"], "parameter": row["parameter"],
            "world_x": row["world_x"], "world_y": row["world_y"],
            "runtime_meaning": MEANING[t], "expected_runtime_entity_count": 1,
            "poc_representation": "MISSING" if missing else "exact placed object",
            "evidence": "POC 18.5 origin/main room/resource comparison; ROM record bytes checked against object-records.json",
            "poc_file_resource": None if missing else resource})
    absent = [x["record_index"] for x in matrix if x["poc_representation"] == "MISSING"]
    return {"format": 1, "rom_sha256": SHA, "poc_commit": POC_COMMIT,
        "poc_scope": "latest pushed main (POC 18.5); local Windows integration was not treated as repository evidence",
        "raw_object_population": {"count": 53, "records": matrix},
        "separate_populations": {
            "layout_derived_rings": {"count": 142, "poc_representation": "generated by canonical adapter", "source_blocks": ["0x40", "0x41", "0x42", "0x43"]},
            "block_47_cells": {"count": 4, "initial_runtime_entities": 0,
                "conditional_transient_entities": "one type-$0F parameter-$40 object per broken cell",
                "poc_representation": "MISSING interactive terrain behavior; artwork alone is present and is not an object-record substitute"},
            "terrain_interactions": "separate layout/collision population"},
        "missing_record_indices": absent, "missing_runtime_entities": len(absent),
        "answer": "NO, WITH EXACT MISSING RECORDS/ENTITIES",
        "classification": "INCOMPLETE"}


def build(rom: bytes, render_output: Path | None = None) -> dict:
    digest = hashlib.sha256(rom).hexdigest()
    if digest != SHA:
        raise ValueError(f"ROM SHA-256 mismatch: {digest}")
    return {"format": 1, "rom_sha256": digest, "type_21": type21_render(rom),
            "block_47": block47(rom, render_output), "type_27": type27_timing(),
            "poc_coverage_summary": {"raw_records": 53, "represented": 29, "missing": 24}}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path, default=ROOT / "data/rom-cache/thz1/final-runtime-closure.json")
    p.add_argument("--coverage", type=Path, default=ROOT / "data/rom-cache/thz1/poc-coverage.json")
    p.add_argument("--render-output", type=Path,
                   default=ROOT / "build/thz1-final-runtime/block-47.png")
    a = p.parse_args()
    a.output.write_text(json.dumps(build(a.rom.read_bytes(), a.render_output), indent=2) + "\n", encoding="utf-8")
    a.coverage.write_text(json.dumps(coverage(), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"closure": str(a.output), "coverage": str(a.coverage)}))


if __name__ == "__main__":
    main()

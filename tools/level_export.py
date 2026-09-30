#!/usr/bin/env python3
"""Export machine-readable THZ1/THZ2/THZ3 level packages from the ROM.

    python tools/level_export.py /path/to/SonicChaos.sms \
        [--output data/rom-cache/levels] [--maps build/level-maps] [--sheets build/level-object-sheets]

Per act it writes layout.json, rings.json, objects.json, assets.json and
manifest.json, plus levels/object-census.json across acts. THZ1 is the control
fixture and must reproduce the committed THZ1 cache before anything else is
written.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import level_package as L  # noqa: E402
import thz1_object_assets as assets  # noqa: E402


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


anim = _load("thz1_animation_reach")
dyn18 = _load("thz1_type18_dynamic_graphics")
object09 = _load("thz1_object_09")

THZ1_CACHE = ROOT / "data" / "rom-cache" / "thz1"
CONTROL_LOOP = ((2880, 384), (2832, 448), (2840, 408), (2928, 448), (2920, 408))
CONTROL_TWIST = ((3124, 548), (3160, 522), (3208, 512))
CONTROL_POST_TWIST = ((3367, 830), (3394, 798), (3422, 774))
THZ1_TERRAIN_KINDS = {  # THZ1-only research labels, NOT verified for other acts
    0x30: "upright_spring", 0x31: "upright_spring", 0x33: "horizontal_spring",
    0x36: "diagonal_spring", 0x38: "diagonal_spring", 0x3D: "static_spike_block",
    0x47: "ring_monitor_block",
}
REGEN = "python tools/level_export.py <SonicChaos.sms> --output data/rom-cache/levels --maps build/level-maps --sheets build/level-object-sheets"


# --- JSON --------------------------------------------------------------------
def dumps(value) -> str:
    """Indented JSON with arrays of scalars collapsed to one line."""
    text = json.dumps(value, indent=2)
    text = re.sub(r"\[\n\s+([^\[\]{}]*?)\n\s+\]",
                  lambda m: "[" + re.sub(r",\n\s+", ", ", m.group(1)) + "]", text)
    return text + "\n"


def write_json(path: Path, value) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = dumps(value)
    path.write_text(text, encoding="utf-8", newline="\n")
    return L.sha256(text.encode("utf-8"))


# --- control fixture -----------------------------------------------------------
def verify_thz1_control(rom: bytes, act: dict) -> dict:
    """THZ1 must reproduce the committed cache before THZ2/3 are trusted."""
    stored_objects = json.loads((THZ1_CACHE / "object-records.json").read_text(encoding="utf-8"))
    stored_layout = json.loads((THZ1_CACHE / "layout-interactions.json").read_text(encoding="utf-8"))
    bounded = act["cells"][:act["runtime_cells"]]
    legacy = _load("cache_game_data")
    legacy_cells, _ = legacy.decode_layout(rom)
    stored_rings = [(r["x"], r["y"]) for r in stored_layout["rings"]]
    mine = [(r["world_x"], r["world_y"]) for r in act["terrain_rings"]]
    checks = OrderedDict([
        ("layout_cells_match_legacy_decoder", bounded == legacy_cells),
        ("dimensions_128x32", (act["width"], act["height"]) == (128, 32)),
        ("object_records_match_committed_cache", [
            {k: r[k] for k in ("index", "rom_offset", "raw_bytes", "world_x", "world_y")}
            for r in act["records"]] == [
            {k: r[k] for k in ("index", "rom_offset", "raw_bytes", "world_x", "world_y")}
            for r in stored_objects["records"]]),
        ("terrain_ring_count_142", len(mine) == 142),
        ("terrain_rings_match_committed_cache", mine == stored_rings),
    ])
    nine = [r for r in act["records"] if r["type_id"] == "0x09"]
    visible = [r for r in nine if r["parameter"] == "0x00"]
    hidden = [r for r in nine if r["parameter"] == "0x01"]
    checks["type09_24_raw_11_visible_13_hidden"] = (len(nine), len(visible), len(hidden)) == (24, 11, 13)
    coords = {(r["world_x"], r["world_y"]) for r in visible}
    for name, group in (("loop", CONTROL_LOOP), ("twist", CONTROL_TWIST), ("post_twist", CONTROL_POST_TWIST)):
        checks[f"known_visible_type09_{name}"] = all(p in coords for p in group)
    checks["initial_visible_population_153"] = len(mine) + len(visible) == 153
    failed = [k for k, v in checks.items() if not v]
    if failed:
        raise AssertionError("THZ1 control fixture failed: " + ", ".join(failed))
    return dict(checks)


# --- pieces --------------------------------------------------------------------
def type09_runtime_checks(rom: bytes, parameters) -> list:
    out = []
    for p in sorted(parameters):
        run = object09.run_init(rom, p)
        out.append({"parameter": f"0x{p:02X}", "init_routine": "0x9C10 (bank 0x0C)",
                    "requested_state": run["requested_state"],
                    "renderer_flags_04": run["renderer_flags_04"],
                    "interpretation": ("visible rotating collectible (state 1, renderer not skipped)"
                                       if p == 0 else
                                       "invisible collectible trigger (state 3, renderer-skip bit 7)"),
                    "evidence": "CONTROLLED ROUTINE RESULT"})
    return out


def rings_json(act: dict, type09_checks: list) -> dict:
    terrain = list(act["terrain_rings"])
    for n, r in enumerate(terrain, 1):
        r["id"] = f"{act['key']}:terrain:{n:04d}"
    objs = L.object_rings(act)
    for r in objs:
        r["id"] = f"{act['key']}:type09:{r['object_index']:03d}"
    visible = [r for r in objs if r["source_class"] == "object_09_visible"]
    hidden = [r for r in objs if r["source_class"] == "object_09_hidden"]
    rings = terrain + objs
    sem = act["semantics"]
    art_check = L.ring_art_check(_ROM[0], act["vram"], sem)
    return {
        "format": L.FORMAT, "rom_sha256": L.ROM_SHA256, "act": act["key"],
        "counts": {
            "terrain": len(terrain),
            "object_09_raw_records": len(objs),
            "object_09_visible": len(visible),
            "object_09_hidden": len(hidden),
            "initial_visible_population": len(terrain) + len(visible),
        },
        "hashes": {
            "terrain_coordinates_sha256": L.coordinate_hash(L.ring_hash_rows(terrain)),
            "object_09_coordinates_sha256": L.coordinate_hash(L.ring_hash_rows(objs)),
            "all_rings_sha256": L.coordinate_hash(L.ring_hash_rows(rings)),
        },
        "terrain_ring_semantics": {
            "evidence": "BYTE-VERIFIED ASSEMBLY (handler $753E, tables $75DC..$760B) + DECODED DATA (collision headers $38000)",
            "rule": "A layout cell is a terrain-ring block iff its collision surface type is 7 "
                    "(handler gate AND $1F / CP 7) AND the presence table $75DC has a nonzero entry; "
                    "quadrant = (x bit 4) + 2*(y bit 4). Derived from shared ROM tables, not per act.",
            "surface_type_7_blocks": [f"0x{b:02X}" for b in sem["surface_type_7_blocks"]],
            "ring_blocks": [f"0x{b:02X}" for b in sem["ring_blocks"]],
            "quadrants_by_block": {f"0x{b:02X}": sem["tables"][b]["quadrants"] for b in sem["ring_blocks"]},
            "replacement_blocks_after_collect": {
                f"0x{b:02X}": [f"0x{v:02X}" for v in sem["tables"][b]["replacement_blocks"]]
                for b in sem["ring_blocks"]},
            "coordinate_convention": "world = cell * 32 + quadrant origin (0/16) + 8; quadrant centre. "
                                     "Art check below shows each ring occupies bbox [1,0,14,15] of its 16x16 quadrant.",
            "art_check_opaque_pixels_by_quadrant": art_check,
            "runtime_cell_bound": "cells at index >= 4095 are never written by the loader and are excluded",
            "ring_block_cells_in_this_act": {
                f"0x{b:02X}": sum(1 for c in act["cells"][:act["runtime_cells"]] if c == b)
                for b in sem["ring_blocks"]},
        },
        "object_09_semantics": {
            "parameters_present": sorted({r["parameter"] for r in objs}),
            "runtime_checks": type09_checks,
            "collection": "both parameters use $617E: abs(dx) < 12 and abs(dy) < 12 (SOURCE-TRACED, docs/object-09.md)",
            "note": "Only parameters $00 and $01 occur in THZ1/2/3. No unfamiliar parameter was assigned a meaning.",
        },
        "source_classes": ["terrain", "object_09_visible", "object_09_hidden"],
        "rings": rings,
    }


def objects_json(act: dict) -> dict:
    recs = []
    for r in act["records"]:
        r = dict(r)
        if r["type_id"] == "0x09":
            r["ring_view"] = ("object_09_visible" if r["parameter"] == "0x00" else "object_09_hidden")
        recs.append(r)
    start = act["descriptor"]["objects"]["list_rom"]
    term = act["object_terminator_rom"]
    bank, cpu = L.rom_to_bank_cpu(term)
    counts = Counter(r["type_id"] for r in recs)
    return {
        "format": L.FORMAT, "rom_sha256": L.ROM_SHA256, "act": act["key"],
        "list": {
            "pointer_chain": {
                "zone_pointer_rom": L.hx(act["descriptor"]["objects"]["zone_pointer_rom"], 5),
                "act_pointer_rom": L.hx(act["descriptor"]["objects"]["act_pointer_rom"], 5),
                "evidence": "BYTE-VERIFIED ASSEMBLY (placement creator, file $70000..$70048)"},
            "start_rom": L.hx(start, 5),
            "start_bank": L.hx(act["descriptor"]["objects"]["list_bank"], 2),
            "start_cpu": L.hx(act["descriptor"]["objects"]["list_cpu"]),
            "terminator_rom": L.hx(term, 5), "terminator_bank": L.hx(bank, 2), "terminator_cpu": L.hx(cpu),
            "terminator_byte": "0xFF",
            "record_size": L.OBJECT_RECORD_SIZE,
            "record_count": len(recs),
            "record_bytes": term - start,
            "raw_bytes_sha256": L.sha256(_ROM[0][start:term + 1]),
        },
        "coordinate_bias": 256,
        "field_layout": {
            "0": "type id", "1-2": "stored X (little endian); world X = stored - 256",
            "3-4": "stored Y (little endian); world Y = stored - 256",
            "5": "flags", "6": "parameter", "7": "aux0", "8": "aux1",
            "evidence": "type/X/Y: BYTE-VERIFIED ASSEMBLY (creator $700EB); bytes 5-8 are raw "
                        "type-specific fields (naming follows the THZ1 census; meanings are not universal)"},
        "type_counts": dict(sorted(counts.items())),
        "records": recs,
    }


def layout_json(act: dict) -> dict:
    d = act["descriptor"]
    cells, width, height = act["cells"], act["width"], act["height"]
    start, end = d["layout"]["rom"], d["layout"]["end_rom"]
    encoded = _ROM[0][start:end]
    tokens = literals = runs = run_cells = 0
    pos = start
    while pos < end:
        if _ROM[0][pos] == 0xFF:
            count = _ROM[0][pos + 2]
            pos += 3
            if count:
                runs += 1
                run_cells += count
            tokens += 1
        else:
            literals += 1
            tokens += 1
            pos += 1
    bank, cpu = L.rom_to_bank_cpu(start)
    unwritten = list(range(act["runtime_cells"], len(cells)))
    usage = L.block_usage(_ROM[0], cells, d["header"]["block_mapping_rom"], act["runtime_cells"])
    for u in usage:
        block = int(u["block_id"], 16)
        flags = L.rom_tables.header(_ROM[0], block)["flags"]
        u["collision_header_flags"] = f"0x{flags:02X}"
        u["collision_surface_type"] = flags & 0x1F
        if block in THZ1_TERRAIN_KINDS:
            u["thz1_research_label"] = THZ1_TERRAIN_KINDS[block]
    return {
        "format": L.FORMAT, "rom_sha256": L.ROM_SHA256, "act": act["key"], "name": d["name"],
        "dimensions": {
            "width_cells": width, "height_cells": height, "block_pixels": L.BLOCK_PIXELS,
            "width_pixels": width * L.BLOCK_PIXELS, "height_pixels": height * L.BLOCK_PIXELS,
            "evidence": "DECODED DATA: header width; height = terminated cell count / width",
            "consistency_checks": d["consistency"],
        },
        "layout_stream": {
            "rom_offset": L.hx(start, 5), "bank": L.hx(bank, 2), "cpu": L.hx(cpu),
            "end_offset_exclusive": L.hx(end, 5),
            "encoded_size_bytes": end - start,
            "encoded_sha256": L.sha256(encoded),
            "encoding": {
                "literal": "byte != $FF: one cell",
                "run": "$FF value count: `count` cells of `value`; count 0 terminates",
                "evidence": "BYTE-VERIFIED ASSEMBLY (loader $4DC4..$4DFA, asm/recovered/bounded_layout_decoder.asm)"},
            "tokens": tokens, "literal_tokens": literals, "run_tokens": runs, "cells_in_runs": run_cells,
            "encoded_cells": len(cells),
            "next_stream_offset_note": "stream end equals the next act's layout start "
                                       "(THZ1->THZ2->THZ3->GPZ1), confirming contiguity",
        },
        "runtime_bound": {
            "ram_base": "0xC001", "cell_limit": L.LAYOUT_RAM_LIMIT_CELLS,
            "written_cells": act["runtime_cells"],
            "unwritten_cell_indices": unwritten,
            "unwritten_cell_blocks": [cells[i] for i in unwritten],
            "note": "The loader stops when DE leaves $C000-$CFFF, so a 4096-cell stream loses its last cell.",
            "evidence": "BYTE-VERIFIED ASSEMBLY / CONTROLLED ROUTINE RESULT (docs/data-formats.md)"},
        "header": {k: (L.hx(v, 4) if isinstance(v, int) and k not in ("negative_width", "width_cells") else v)
                   for k, v in d["header"].items()},
        "block_mapping": {
            "rom": L.hx(d["header"]["block_mapping_rom"], 5),
            "bank": L.hx(d["header"]["block_mapping_bank"], 2), "cpu": L.hx(d["header"]["block_mapping_cpu"]),
            "format": "256 word pointers; each block = 16 tile-entry words (4x4 tiles); "
                      "entry bits: 0-8 tile, 9 x-flip, 10 y-flip, 11 palette 1, 12 priority",
            "evidence": "DECODED DATA (shared with THZ1 renderer tools)"},
        "cells_sha256": L.sha256(bytes(cells)),
        "runtime_cells_sha256": L.sha256(bytes(cells[:act["runtime_cells"]])),
        "block_ids_used": len(usage),
        "block_usage": usage,
        "rows": [cells[r * width:(r + 1) * width] for r in range(height)],
    }


# --- assets ----------------------------------------------------------------------
def _coverage(loads: list, tile: int):
    for s in loads:
        base = int(s["tile_base"], 16)
        if base <= tile < base + s["tile_count"]:
            return s["id"]
    return None


def act_assets(rom: bytes, act: dict, thz1: dict, sheets: Path = None) -> dict:
    d = act["descriptor"]
    vram = bytes(act["vram"])
    pal = d["palette"]
    sprite_palette = assets.palette_rgba(rom, pal["sprite_index"])
    loads = act["vram_loads"]
    by_type = OrderedDict()
    for r in act["records"]:
        by_type.setdefault(r["type_id"], []).append(r)
    types = []
    for type_id in sorted(by_type, key=lambda t: int(t, 16)):
        t = int(type_id, 16)
        recs = by_type[type_id]
        bases = Counter((r["aux0"], r["aux1"]) for r in recs)
        thz1_bases = {(r["aux0"], r["aux1"]) for r in thz1["records"] if r["type_id"] == type_id}
        entry = OrderedDict([("type_id", type_id), ("placed_count", len(recs))])
        entry["placement_bases"] = [{"aux0": a, "aux1": b, "count": n} for (a, b), n in sorted(bases.items())]
        entry["in_thz1_extraction_set"] = t in assets.TARGET_TYPES
        entry["placement_bases_all_seen_in_thz1"] = set(bases) <= thz1_bases if thz1_bases else None
        art_verified = t in assets.TARGET_TYPES and {a for a, _ in bases} <= {a for a, _ in thz1_bases}
        entry["art_status"] = (
            "VERIFIED IN THZ1 STUDY: same type, same aux0 tile base, art from the shared level art load"
            if art_verified else
            "UNRESOLVED: type not in the THZ1 extraction set; art source not traced. Frame geometry only; "
            "no pixels are rendered and no reference sheet is produced")
        try:
            m = assets.object_mapping(rom, t)
            frame_ptrs = assets.mapping_frame_pointers(rom, m["mapping_cpu"])
            entry["mapping"] = {
                "pointer_table_rom": L.hx(m["pointer_table_rom"], 5), "pointer_raw": m["pointer_raw"].hex().upper(),
                "mapping_bank": "0x0F", "mapping_cpu": L.hx(m["mapping_cpu"]), "mapping_rom": L.hx(m["mapping_rom"], 5),
                "frame_pointer_count": len(frame_ptrs), "frame_pointers": [L.hx(p) for p in frame_ptrs],
                "shared_mapping_types": [f"0x{o:02X}" for o in range(256)
                                         if o != t and assets.u16(rom, assets.POINTER_TABLE_ROM_BASE + o * 2) == m["mapping_cpu"]
                                         and o in (0x09, 0x10, 0x18, 0x1B, 0x21, 0x26, 0x27, 0x28, 0x50)],
                "evidence": "DECODED DATA (bank $0F table at $3C000, engine $64FA)"}
        except Exception as exc:  # noqa: BLE001
            entry["mapping"] = {"error": repr(exc), "evidence": "UNRESOLVED"}
            frame_ptrs = []
        try:
            trace = anim.json_ready_trace(anim.trace_type(rom, t))
            entry["animation"] = {
                "type_table_entry_rom": trace["type_table_entry_rom"], "bank": trace["bank"],
                "state_table_cpu": trace["state_table_cpu"], "state_table_rom": trace["state_table_rom"],
                "state_count": trace["state_count"], "state_script_cpus": trace["state_script_cpus"],
                "reachable_frame_indices": trace["reachable_frame_indices"],
                "unresolved_states": trace["unresolved_states"],
                "evidence": "SOURCE-TRACED (static trace, tools/thz1_animation_reach.py); "
                            "states with unsupported commands are listed as unresolved"}
            reach = [int(x, 16) for x in trace["reachable_frame_indices"]]
        except Exception as exc:  # noqa: BLE001
            entry["animation"] = {"error": repr(exc), "evidence": "UNRESOLVED"}
            reach = []
        overlay = None
        if t == 0x18:
            _, dyn = dyn18.dynamic_list_for_selector(rom, dyn18.DYNAMIC_SELECTOR)
            vram_dyn = bytearray(vram)
            dyn18.apply_dynamic_entries(vram_dyn, rom, dyn)
            overlay = bytes(vram_dyn)
            entry["dynamic_graphics"] = {
                "selector": "0x12", "list_cpu": L.hx(dyn18.EXPECTED_LIST_CPU),
                "entries": [{"tile_base": L.hx(e["tile_base"], 2), "tile_count": e["tile_count"],
                             "source_rom": L.hx(e["source_rom"], 5)} for e in dyn],
                "evidence": "SOURCE-TRACED (THZ1 type-$18 study; shared object code)"}
        render_vram = overlay or vram
        base = int(recs[0]["aux0"], 16)
        frames, sheet = [], []
        indices = reach if reach else list(range(len(frame_ptrs)))
        unloaded_all = set()
        for fi in indices:
            if fi >= len(frame_ptrs):
                continue
            frame = assets.parse_frame_record(rom, frame_ptrs[fi])
            used = sorted({(base + p["tile_offset"] + k) & 0xFF for p in frame["pieces"] for k in (0, 1)})
            missing = [u for u in used if _coverage(loads, u) is None
                       and not (overlay and any(int(e_["tile_base"], 16) <= u < int(e_["tile_base"], 16) + e_["tile_count"]
                                                for e_ in entry["dynamic_graphics"]["entries"]))]
            unloaded_all.update(missing)
            item = {
                "frame_index": fi, "frame_cpu": L.hx(frame_ptrs[fi]), "frame_rom": L.hx(frame["frame_rom"], 5),
                "piece_count": frame["piece_count"], "raw_11": " ".join(f"{b:02X}" for b in frame["raw_11"]),
                "y_origin": frame["y_origin"], "x_origin": frame["x_origin"],
                "coordinate_table_cpu": L.hx(frame["coords_cpu"]) if frame["piece_count"] else None,
                "tile_list_cpu": L.hx(frame["tile_list_cpu"]) if frame["piece_count"] else None,
                "pieces": [{"y": p["relative_y"], "x": p["relative_x"], "tile_offset": p["tile_offset"]}
                           for p in frame["pieces"]],
                "tile_ids_normal_base": [L.hx(u, 2) for u in used],
                "tile_ids_not_in_static_art_load": [L.hx(u, 2) for u in missing],
            }
            rendered = (assets.render_frame(render_vram, frame, base, scale=2, palette=sprite_palette)
                        if art_verified else None)
            if not art_verified and frame["pieces"]:
                xs = [p["relative_x"] for p in frame["pieces"]]
                ys = [p["relative_y"] for p in frame["pieces"]]
                item["bounds"] = {"min_x": min(xs), "min_y": min(ys), "max_x": max(xs) + 8,
                                  "max_y": max(ys) + 16, "width": max(xs) + 8 - min(xs),
                                  "height": max(ys) + 16 - min(ys),
                                  "note": "geometry only (8x16 pieces); pixels not established"}
            elif rendered:
                w, h, rgba, meta = rendered
                item["bounds"] = meta["bounds"]
                item["nonzero_source_pixels"] = meta["nonzero_source_pixels"]
                sheet.append((f"f{fi:02d}", w, h, rgba))
            else:
                item["bounds"] = None
            frames.append(item)
        entry["tile_base_normal"] = L.hx(base, 2)
        entry["frames"] = frames
        entry["tiles_missing_from_static_art_load"] = [L.hx(u, 2) for u in sorted(unloaded_all)]
        entry["graphics_status"] = (
            "UNRESOLVED: referenced tiles are absent from the static level art load"
            if unloaded_all and art_verified is False else
            ("verified" if art_verified else
             "UNRESOLVED: the object's own art load has not been traced; tile ids that fall inside "
             "the static VRAM image are not evidence of its art (observed: they hold other objects' tiles)"))
        if sheet:
            name = f"{act['key']}_type{t:02X}.png"
            if sheets:
                sheets.mkdir(parents=True, exist_ok=True)
                assets.make_contact_sheet([(n, w, h, b) for n, w, h, b in sheet], sheets / name)
            entry["reference_sheet"] = {"file": f"build/level-object-sheets/{name}",
                                        "note": "generated, git-ignored; tile base = aux0, sprite palette of the act"}
        types.append(entry)
    return {
        "format": L.FORMAT, "rom_sha256": L.ROM_SHA256, "act": act["key"],
        "level_art": {
            "entry_rom": L.hx(d["art"]["entry_rom"], 5), "entry_raw": d["art"]["raw"],
            "primary_stream": {k: (L.hx(v) if k in ("stream_cpu", "vram_destination") else L.hx(v, 5) if k == "stream_rom" else v)
                               for k, v in d["art"]["primary"].items()},
            "supplemental_list_rom": L.hx(d["art"]["supplemental_list_rom"], 5),
            "supplemental_streams": [{k: (L.hx(v) if k in ("stream_cpu", "vram_destination") else L.hx(v, 5) if k == "stream_rom" else v)
                                      for k, v in s.items()} for s in d["art"]["supplemental"]],
            "vram_loads": loads,
            "vram_image_sha256": L.sha256(vram),
            "evidence": "BYTE-VERIFIED ASSEMBLY (loader $78E1) + DECODED DATA (tile streams)"},
        "block_mapping": {"rom": L.hx(d["header"]["block_mapping_rom"], 5),
                          "bank": L.hx(d["header"]["block_mapping_bank"], 2),
                          "cpu": L.hx(d["header"]["block_mapping_cpu"])},
        "palettes": {
            "selector_rom": L.hx(pal["selector_rom"], 5),
            "background": {"index": L.hx(pal["background_index"], 2), "rom": L.hx(pal["background_rom"], 5),
                           "cram_bytes": _ROM[0][pal["background_rom"]:pal["background_rom"] + 16].hex().upper()},
            "sprite": {"index": L.hx(pal["sprite_index"], 2), "rom": L.hx(pal["sprite_rom"], 5),
                       "cram_bytes": _ROM[0][pal["sprite_rom"]:pal["sprite_rom"] + 16].hex().upper()},
            "evidence": "BYTE-VERIFIED ASSEMBLY (loader $794F, resolver $3B63E) + DECODED DATA",
            "note": "Background half is CRAM 0-15; tile-attribute palette-1 and sprites use the sprite half "
                    "(renderer assumption shared with the THZ1 tools). Runtime palette animation is not modelled."},
        "object_types": types,
    }


# --- census ------------------------------------------------------------------------
def build_census(acts: dict, assets_by_act: dict) -> dict:
    thz1_census = json.loads((THZ1_CACHE / "object-census.json").read_text(encoding="utf-8"))
    research = {o["type_id"]: o["research"] for o in thz1_census["objects"]}
    thz1_variants = {(r["type_id"], r["flags"], r["parameter"], r["aux0"], r["aux1"]) for r in acts["thz1"]["records"]}
    types = sorted({r["type_id"] for a in acts.values() for r in a["records"]}, key=lambda t: int(t, 16))
    out = []
    for t in types:
        per_act = {k: sum(1 for r in a["records"] if r["type_id"] == t) for k, a in acts.items()}
        variants = Counter()
        for k, a in acts.items():
            for r in a["records"]:
                if r["type_id"] == t:
                    variants[(k, r["flags"], r["parameter"], r["aux0"], r["aux1"])] += 1
        vlist = [{"act": k, "flags": f, "parameter": p, "aux0": a0, "aux1": a1, "count": n,
                  "seen_in_thz1": (t, f, p, a0, a1) in thz1_variants} for (k, f, p, a0, a1), n in sorted(variants.items())]
        res = research.get(t)
        if res is None:
            cls, notes = ["C", "D"], ["new to THZ2/3; not present in THZ1", "identity unresolved (numeric id only)"]
        else:
            status = res["semantic_identity"]["status"]
            complete = res["behavior_completeness"].startswith("VERIFIED") and res["lifetime_contact_completeness"].startswith("VERIFIED")
            cls = ["A" if complete else "B"]
            notes = [f"THZ1 behavior: {res['behavior_completeness']}", f"THZ1 identity: {status}"]
            if status == "UNRESOLVED":
                cls.append("D")
        new_variants = [v for v in vlist if v["act"] != "thz1" and not v["seen_in_thz1"]]
        entry = OrderedDict([("type_id", t), ("counts", per_act), ("total", sum(per_act.values())),
                             ("classes", cls), ("notes", notes),
                             ("new_variants_vs_thz1", new_variants), ("variants", vlist)])
        if res is None:
            entry["follow_up"] = "Recommended research task: state table, handler, contact/lifetime behaviour, " \
                                 "and art source for numeric type " + t + "."
        out.append(entry)
    return {
        "format": L.FORMAT, "rom_sha256": L.ROM_SHA256,
        "class_legend": {"A": "already covered by THZ1 research (behaviour verified for THZ1-reachable use)",
                         "B": "present in THZ1 but research incomplete",
                         "C": "new to THZ2/3", "D": "identity unresolved"},
        "policy": "Numeric type ids only; no names inferred from appearance.",
        "acts": {k: {"raw_objects": len(a["records"]), "unique_types": len({r["type_id"] for r in a["records"]}),
                     "new_types_vs_thz1": sorted({r["type_id"] for r in a["records"]} - {r["type_id"] for r in acts["thz1"]["records"]}, key=lambda x: int(x, 16))}
                 for k, a in acts.items()},
        "types": out,
    }


_ROM = [None]


def build_all(rom: bytes, output: Path, maps: Path = None, sheets: Path = None) -> dict:
    _ROM[0] = rom
    acts = OrderedDict((k, L.build_act(rom, k)) for k in L.ACTS)
    control = verify_thz1_control(rom, acts["thz1"])
    thz1_records = {"records": acts["thz1"]["records"]}
    params = {int(r["parameter"], 16) for a in acts.values() for r in a["records"] if r["type_id"] == "0x09"}
    t09 = type09_runtime_checks(rom, params)
    assets_by_act, summary = {}, OrderedDict()
    thz1_vram = acts["thz1"]["vram"]
    for key, act in acts.items():
        d = act["descriptor"]
        act_dir = output / key
        rings = rings_json(act, t09)
        lay = layout_json(act)
        obj = objects_json(act)
        ast = act_assets(rom, act, thz1_records, sheets)
        assets_by_act[key] = ast
        hashes = OrderedDict()
        hashes["layout.json"] = write_json(act_dir / "layout.json", lay)
        hashes["rings.json"] = write_json(act_dir / "rings.json", rings)
        hashes["objects.json"] = write_json(act_dir / "objects.json", obj)
        hashes["assets.json"] = write_json(act_dir / "assets.json", ast)
        if maps:
            import level_maps
            level_maps.write_maps(rom, act, rings["rings"], maps / key)
        manifest = OrderedDict([
            ("format", L.FORMAT), ("rom_sha256", L.ROM_SHA256), ("act", key), ("name", d["name"]),
            ("zone_index", d["zone"]), ("act_index", d["act"]),
            ("evidence_classes", list(L.EVIDENCE)),
            ("verified_offsets", OrderedDict([
                ("act_header", {"rom": L.hx(d["header"]["header_rom"], 5), "raw": d["header"]["raw"],
                                "evidence": "BYTE-VERIFIED ASSEMBLY (loader $4FDC)"}),
                ("layout", {"rom": L.hx(d["layout"]["rom"], 5), "end_exclusive": L.hx(d["layout"]["end_rom"], 5),
                            "bank": L.hx(d["header"]["layout_bank"], 2), "cpu": L.hx(d["header"]["layout_cpu"])}),
                ("object_list", {"rom": L.hx(d["objects"]["list_rom"], 5), "terminator": L.hx(act["object_terminator_rom"], 5),
                                 "bank": "0x1C", "cpu": L.hx(d["objects"]["list_cpu"])}),
                ("block_mapping", {"rom": L.hx(d["header"]["block_mapping_rom"], 5), "bank": L.hx(d["header"]["block_mapping_bank"], 2),
                                   "cpu": L.hx(d["header"]["block_mapping_cpu"])}),
                ("tiles_primary", {"rom": L.hx(d["art"]["primary"]["stream_rom"], 5), "vram": L.hx(d["art"]["primary"]["vram_destination"])}),
                ("palette_selector", {"rom": L.hx(d["palette"]["selector_rom"], 5)}),
                ("background_palette", {"rom": L.hx(d["palette"]["background_rom"], 5), "index": L.hx(d["palette"]["background_index"], 2)}),
                ("sprite_palette", {"rom": L.hx(d["palette"]["sprite_rom"], 5), "index": L.hx(d["palette"]["sprite_index"], 2)}),
            ])),
            ("historical_reference_comparison", {"status": "HISTORICAL REFERENCE ONLY; ROM-derived values are canonical",
                                                 "fields": L.compare_historical(d)}),
            ("player_start", dict(d["start"], note="Loader $4E57 copies these words to $D2D6/$D2D8/$D511/$D514; "
                                                   "field meanings are not named here (UNRESOLVED)")),
            ("dimensions", {"width_cells": act["width"], "height_cells": act["height"],
                            "width_pixels": act["width"] * 32, "height_pixels": act["height"] * 32}),
            ("counts", {"raw_objects": len(act["records"]), "unique_object_types": len({r["type_id"] for r in act["records"]}),
                        **rings["counts"]}),
            ("hashes", {"layout_cells_sha256": lay["cells_sha256"], "runtime_cells_sha256": lay["runtime_cells_sha256"],
                        "objects_raw_sha256": obj["list"]["raw_bytes_sha256"], **rings["hashes"],
                        "vram_image_sha256": ast["level_art"]["vram_image_sha256"]}),
            ("art_shared_with_thz1", act["vram"] == thz1_vram),
            ("presentation_model", {
                "status": "SOURCE-TRACED / BYTE-VERIFIED (see docs/mapped-object-screen-registration.md, "
                          "data/rom-cache/mapped-object-registration.json)",
                "R8_hscroll": "-(camera_x + 1) mod 256", "R9_vscroll": "(camera_y + 17) mod 224",
                "sms_sprite_y": "sprite drawn one line below its SAT Y",
                "object_terrain_relation": "terrain_row = anchor_y + y_origin + piece_y + 18 ; "
                                           "terrain_col = anchor_x + x_origin' + piece_x + 1",
                "applied_to_canonical_data": False,
                "note": "Canonical anchors (objects.json/rings.json world_x/world_y) and mapping geometry "
                        "(assets.json frames) are stored separately and unmodified; no GameMaker offset is baked in."}),
            ("reference_maps", {"directory": f"build/level-maps/{key}", "files": {n: f"{key}_{n}.png" for n in ("terrain", "rings", "objects", "combined")},
                                "image_size": [act["width"] * 32, act["height"] * 32 + 30],
                                "legend_band_px": 30,
                                "note": "generated research aids (git-ignored); JSON is authoritative"}),
            ("files", hashes),
            ("regenerate", REGEN),
        ])
        write_json(act_dir / "manifest.json", manifest)
        summary[key] = manifest
    census = build_census({k: v for k, v in acts.items()}, assets_by_act)
    write_json(output / "object-census.json", census)
    return {"acts": acts, "control": control, "census": census, "manifests": summary}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--output", type=Path, default=L.DEFAULT_OUTPUT)
    ap.add_argument("--maps", type=Path, default=None)
    ap.add_argument("--sheets", type=Path, default=None)
    args = ap.parse_args()
    rom = L.load_rom(args.rom)
    result = build_all(rom, args.output, args.maps, args.sheets)
    print("THZ1 control fixture: PASS", json.dumps(result["control"]))
    for key, m in result["manifests"].items():
        print(key, m["dimensions"], m["counts"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""ROM-backed audit of the Gigapolis isometric terrain decks.

The visual name is deliberately kept out of machine-facing identities.  The
tool inventories both sides of the ambiguity which motivated the audit:

* terrain surface $1C, blocks $8C..$97 (the Gigapolis deck collision);
* mapped object $28 parameter $83 (the falling/sag platform family).

This keeps an apparent platform from being silently treated as one object.
The output contains no ROM bytes beyond short routine prefixes/hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import level_package as L  # noqa: E402
import rom as rom_tables  # noqa: E402
import thz1_object_assets as assets  # noqa: E402
from oracle import Oracle  # noqa: E402

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OUTPUT = ROOT / "data" / "rom-cache" / "isometric-platform.json"
SURFACE = 0x1C
BLOCKS = tuple(range(0x8C, 0x98))

ACTS = OrderedDict(
    (f"{key}{act + 1}", {"zone": zone, "act": act, "name": f"{key.upper()}{act + 1}"})
    for zone, key in enumerate(("thz", "gpz", "sez", "mghz", "apz", "eez"))
    for act in range(3)
)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


psc = _load("platform_spike_collision")
si = _load("spring_interaction")


def hx(v: int, n: int = 2) -> str:
    return f"0x{v:0{n}X}"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def s16(v: int) -> int:
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def ranges(values) -> list:
    vals = sorted(set(values))
    if not vals:
        return []
    out, a, b = [], vals[0], vals[0]
    for v in vals[1:]:
        if v == b + 1:
            b = v
        else:
            out.append([a, b])
            a = b = v
    out.append([a, b])
    return out


def load_rom(path: Path) -> bytes:
    data = path.read_bytes()
    if len(data) != 524288 or sha(data) != ROM_SHA256:
        raise ValueError("Expected canonical Sonic Chaos (Europe) v1.2 ROM")
    return data


def act_data(rom: bytes, key: str) -> dict:
    d = ACTS[key]
    header = L.act_header(rom, d["zone"], d["act"])
    cells, end, terminated = L.decode_layout_stream(rom, header["layout_rom"])
    op = L.object_list_pointer(rom, d["zone"], d["act"])
    records, term = L.decode_object_list(rom, op["list_rom"])
    if not terminated or len(cells) % header["width_cells"]:
        raise AssertionError(key)
    return {"key": key, "header": header, "cells": cells,
            "width": header["width_cells"], "height": len(cells) // header["width_cells"],
            "layout_end": end, "objects": records, "object_list": op, "object_end": term}


def runs32(profile) -> list:
    out, start = [], 0
    for i in range(1, 33):
        if i == 32 or profile[i] != profile[start]:
            out.append([start, i - 1, hx(profile[start])])
            start = i
    return out


def block_definitions(rom: bytes) -> dict:
    gpz_art = L.art_entry(rom, 1, 0)
    gpz_vram, _ = L.build_vram(rom, gpz_art)
    pixels = L.block_pixel_maps(rom, gpz_vram, only=BLOCKS, mapping_rom=0x45640)
    out = OrderedDict()
    for b in BLOCKS:
        h = rom_tables.header(rom, b)
        # Read the bank-relative mapping pointers before interpreting deck art.
        mapping = L.block_mapping(rom, 0x45640, b)
        attrs = mapping["attributes"]
        palette_pixels = [p for row in pixels[b] for p in row]
        effective = [32 if (v & 0x40) else (v & 0x3F) for v in h["vertical"]]
        out[hx(b)] = {
            "header_rom": hx(h["address"], 5), "flags": hx(h["flags"]),
            "surface_type": h["flags"] & 0x1F, "solid_bit7": bool(h["flags"] & 0x80),
            "one_way_bit6": bool(h["flags"] & 0x40), "modifier": hx(h["modifier"]),
            "vertical_pointer_rom": hx(h["vertical_pointer"], 5),
            "horizontal_pointer_rom": hx(h["horizontal_pointer"], 5),
            "vertical_profile_runs": runs32(h["vertical"]),
            "effective_surface_1c_height_runs": runs32(effective),
            "horizontal_profile_runs": runs32(h["horizontal"]),
            "mapping_pointer_rom": hx(mapping["pointer_entry_rom"], 5),
            "mapping_cpu": hx(mapping["cpu"], 4), "mapping_rom": hx(mapping["rom"], 5),
            "mapping_attributes_all_zero": all(v == 0 for v in attrs),
            "mapping_attributes_sha256": sha(b"".join(v.to_bytes(2, "little") for v in attrs)),
            "decoded_nonzero_palette_pixels": sum(bool(v) for v in palette_pixels),
            "decoded_palette_indices": sorted(set(palette_pixels)),
            "presentation": "visible terrain deck/platform art",
        }
    if {v["surface_type"] for v in out.values()} != {SURFACE}:
        raise AssertionError("block set no longer surface $1C")
    return out


def terrain_census(rom: bytes) -> dict:
    acts, all_rows = OrderedDict(), []
    for key in ACTS:
        a = act_data(rom, key)
        rows = []
        for i, b in enumerate(a["cells"][:4095]):
            h = rom_tables.header(rom, b)
            if h["flags"] & 0x1F != SURFACE:
                continue
            cx, cy = i % a["width"], i // a["width"]
            row = {"cell_index": i, "cell_x": cx, "cell_y": cy,
                   "world_x": cx * 32, "world_y": cy * 32, "block": hx(b)}
            rows.append(row)
            all_rows.append((key, cx, cy, b))
        acts[key] = {
            "dimensions_cells": [a["width"], a["height"]], "count": len(rows),
            "block_counts": dict(sorted(Counter(r["block"] for r in rows).items())), "cells": rows,
        }
    return {
        "evidence": "DECODED DATA (all 18 normal-act headers/layout streams) + collision header table",
        "acts": acts, "total_cells": len(all_rows),
        "coordinate_hash_sha256": sha("".join(f"{k},{x},{y},{b:02X}\n" for k, x, y, b in all_rows).encode("ascii")),
        "acts_with_surface_1c": [k for k, v in acts.items() if v["count"]],
    }


def platform_state(parameter: int) -> int:
    state = (parameter & 0x3F) + 1
    if (parameter & 0x7F) in (5, 11):
        state = 13
    return state


def object_census(rom: bytes) -> dict:
    acts, all_rows = OrderedDict(), []
    for key in ACTS:
        a = act_data(rom, key)
        rows = []
        for r in a["objects"]:
            if r["type_id"] != "0x28":
                continue
            p, aux1 = int(r["parameter"], 16), int(r["aux1"], 16)
            row = {k: r[k] for k in ("index", "rom_offset", "raw_bytes", "world_x", "world_y",
                                      "flags", "parameter", "aux0", "aux1")}
            row.update({"initial_state": platform_state(p), "parameter_bit7": bool(p & 0x80),
                        "parameter_bit6": bool(p & 0x40),
                        "state4_touch_fall_variant": platform_state(p) == 4,
                        "state10_horizontal_reverser": platform_state(p) == 10,
                        "aux1_numeric": aux1})
            rows.append(row)
            all_rows.append((key, row))
        acts[key] = {"count": len(rows),
                     "parameter_counts": dict(sorted(Counter(r["parameter"] for r in rows).items())),
                     "initial_state_counts": {str(k): v for k, v in sorted(Counter(r["initial_state"] for r in rows).items())},
                     "placements": rows}
    return {"evidence": "DECODED DATA (all normal-act object lists)", "type_id": "0x28", "acts": acts,
            "total": len(all_rows), "acts_with_type_28": [k for k, v in acts.items() if v["count"]],
            "coordinate_hash_sha256": sha("".join(f'{k},{r["world_x"]},{r["world_y"]},{r["parameter"]},{r["aux1"]}\n'
                                                   for k, r in all_rows).encode("ascii"))}


def placement_contexts(rom: bytes, objects: dict) -> dict:
    out = OrderedDict()
    for key in ACTS:
        a = act_data(rom, key)
        rows = []
        for r in objects["acts"][key]["placements"]:
            x, y = r["world_x"], r["world_y"]
            samples = []
            for yy in (y - 32, y - 18, y, y + 16, y + 32):
                cx, cy = x // 32, yy // 32
                if 0 <= cx < a["width"] and 0 <= cy < a["height"]:
                    b = a["cells"][cy * a["width"] + cx]
                    h = rom_tables.header(rom, b)
                    samples.append({"sample_y": yy, "cell": [cx, cy], "block": hx(b),
                                    "flags": hx(h["flags"]), "surface": hx(h["flags"] & 0x1F),
                                    "vertical_at_anchor_x": hx(h["vertical"][x & 31])})
            rows.append({"world": [x, y], "parameter": r["parameter"], "initial_state": r["initial_state"],
                         "terrain_column_samples": samples,
                         "over_surface_1c": any(s["surface"] == "0x1C" for s in samples)})
        out[key] = rows
    return {"evidence": "DECODED DATA", "by_act": out,
            "state4_over_surface_1c": sum(r["initial_state"] == 4 and r["over_surface_1c"] for rows in out.values() for r in rows),
            "state4_total": sum(r["initial_state"] == 4 for rows in out.values() for r in rows)}


def graphics(rom: bytes) -> dict:
    mapping = assets.object_mapping(rom, 0x28)
    ptrs = assets.mapping_frame_pointers(rom, mapping["mapping_cpu"])
    frame = assets.parse_frame_record(rom, ptrs[1])
    zones = OrderedDict()
    for zone, key in ((1, "gpz"), (3, "mghz")):
        art = L.art_entry(rom, zone, 0)
        stream = next(s for s in art["supplemental"] if s["vram_destination"] == 0x0D40)
        vram, loads = L.build_vram(rom, art)
        load = next(x for x in loads if x["vram_destination"] == "0x0D40")
        opaque = []
        for piece in frame["pieces"]:
            for half in range(2):
                tile = assets.tile_pixels(vram, (0x6A + piece["tile_offset"] + half) & 0xFF)
                for py, row in enumerate(tile):
                    for px, colour in enumerate(row):
                        if colour:
                            opaque.append((piece["relative_x"] + px, piece["relative_y"] + half * 8 + py))
        bbox = ([min(x for x, _ in opaque), min(y for _, y in opaque),
                 max(x for x, _ in opaque), max(y for _, y in opaque)] if opaque else None)
        zones[key] = {"source_rom": hx(stream["stream_rom"], 5), "vram_destination": hx(stream["vram_destination"], 4),
                      "tile_base": "0x6A", "decoded_tile_count": load["tile_count"],
                      "palette_selector": L.palette_selection(rom, zone, 0),
                      "decoded_art_sha256": load["decoded_sha256"],
                      "opaque_source_pixels": len(opaque),
                      "opaque_relative_bounds_inclusive": bbox,
                      "renderer_relative_bounds_inclusive": ([bbox[0], bbox[1] + 18, bbox[2], bbox[3] + 18]
                                                                if bbox else None)}
    return {"evidence": "DECODED DATA (object mapping table, act art lists and compressed streams)",
            "type": "0x28", "mapping_pointer_entry_rom": hx(mapping["pointer_table_rom"], 5),
            "mapping_cpu": hx(mapping["mapping_cpu"], 4), "mapping_rom": hx(mapping["mapping_rom"], 5),
            "frame_1": {"frame_cpu": hx(ptrs[1], 4), "frame_rom": hx(frame["frame_rom"], 5),
                        "piece_count": frame["piece_count"],
                        "relative_pixel_bounds_inclusive": [-16, -16, 15, -1],
                        "piece_offsets": [[p["relative_x"], p["relative_y"], p["tile_offset"]] for p in frame["pieces"]]},
            "zone_art": zones,
            "reading": "mapping/anchor geometry is shared; the compressed tile stream and palette selectors are zone presentation data"}


def routines(rom: bytes) -> list:
    specs = [
        (1, 0x6F61, 0x70E7, "floor projection including the surface-$1C branch at $6F8E"),
        (1, 0x715E, 0x73C9, "side probes and projection"),
        (1, 0x73C9, 0x753E, "ceiling probe and projection"),
        (1, 0x690B, 0x6973, "terrain pass and low-five-bit surface dispatch"),
        (0x1E, 0x8439, 0x8585, "type-$28 state scripts"),
        (0x1E, 0x8585, 0x85FE, "type-$28 initializer"),
        (0x1E, 0x8719, 0x879A, "type-$28 state-4 touch-delay/fall callback"),
        (0x1E, 0x8813, 0x8814, "type-$28 state-9 callback: RET"),
    ]
    out = []
    for bank, start, end, purpose in specs:
        off = start if bank == 1 else bank * 0x4000 + start - 0x8000
        data = rom[off:off + end - start]
        out.append({"bank": hx(bank), "cpu": hx(start, 4), "end_cpu_exclusive": hx(end, 4),
                    "rom_offset": hx(off, 5), "length": len(data), "sha256": sha(data),
                    "first_16_bytes": data[:16].hex(), "purpose": purpose})
    return out


class TerrainLab:
    """Original terrain pass on a chosen decoded normal-act layout."""

    def __init__(self, rom: bytes, key: str):
        self.o = Oracle(rom)
        self.m = self.o.mem
        a = act_data(rom, key)
        cells = bytes(a["cells"][:4095])
        self.m[0xC001:0xD000] = bytes(4095)
        self.m[0xC001:0xC001 + len(cells)] = cells
        self.o.word(0xD168, 0xD800)
        for row in range(128):
            self.o.word(0xD800 + row * 2, row * a["width"])
        self.o.word(0xD16A, -a["width"])
        self.o.word(0xD2E0, 0x8000)
        self.base = bytes(self.m[0xC000:0xE000])

    def run(self, x: int, y: int, vx=0, vy=0, prev=0x9C, state=5, attack=False, floor=False) -> dict:
        self.m[0xC000:0xE000] = self.base
        o, m = self.o, self.m
        o.word(0xD511, x); o.word(0xD514, y)
        o.word(0xD516, vx); o.word(0xD518, vy)
        m[0xD501] = m[0xD502] = state
        m[0xD503] = (0 if floor else 1) | (2 if attack else 0)
        m[0xD522] = 2 if floor else 0
        m[0xD36C] = prev
        m[0xD52C], m[0xD52D] = (8, 24) if state != 0x0F else (9, 24)
        o.cpu.ix = 0xD500
        o.call(0x690B)
        return {"x": o.word(0xD511), "y": o.word(0xD514), "vx": s16(o.word(0xD516)),
                "vy": s16(o.word(0xD518)), "floor": bool(m[0xD522] & 2),
                "ceiling": bool(m[0xD522] & 1), "contacts": m[0xD523],
                "sampled_block": m[0xD353], "sampled_flags": m[0xD364], "new_previous": m[0xD36C]}


def terrain_boundary_sweeps(rom: bytes) -> dict:
    """Exhaustive local floor boundaries plus selected side/underside probes."""
    lab = TerrainLab(rom, "gpz1")
    a = act_data(rom, "gpz1")
    cells = [(i % a["width"], i // a["width"], b) for i, b in enumerate(a["cells"][:4095]) if b in BLOCKS]
    by_block = OrderedDict()
    cases = 0
    for b in BLOCKS:
        reps = [(cx, cy) for cx, cy, bb in cells if bb == b]
        if not reps:
            continue
        cx, cy = reps[0]
        h = rom_tables.header(rom, b)
        rows = []
        for lx in range(32):
            x = cx * 32 + lx
            projected = []
            for probe_local_y in range(-2, 35):
                y = cy * 32 + probe_local_y - 18
                got = lab.run(x, y, vy=0x100, prev=0x9C)
                cases += 1
                if got["floor"] and got["y"] != y:
                    projected.append(probe_local_y)
            raw = h["vertical"][lx]
            effective = 32 if raw & 0x40 else raw & 0x3F
            surface_local_y = 32 - effective
            rows.append({"local_x": lx, "raw_vertical": hx(raw), "effective_height": effective,
                         "surface_local_y": surface_local_y,
                         "probe_local_y_projected_ranges": ranges(projected)})
        by_block[hx(b)] = {"representative_cell": [cx, cy], "local_x_rows": rows}

    # State/velocity gates use a stable long-run cell (GPZ1 cell 68,1 block $8D).
    cx, cy = 68, 1
    x, surface = cx * 32 + 16, cy * 32 + 16
    gates = []
    for state in (1, 5, 6, 9, 0x0A, 0x0B, 0x0E, 0x0F, 0x11, 0x12, 0x1C, 0x20, 0x22):
        for vy in (-0x700, -1, 0, 1, 0x700):
            y = surface - 18 + (1 if vy >= 0 else 0)
            got = lab.run(x, y, vy=vy, prev=0x9C, state=state, attack=state in (9, 0x0A, 0x1C))
            gates.append({"state": hx(state), "vy_8_8": vy, "y_before": y, "y_after": got["y"],
                          "floor_after": got["floor"], "contacts": hx(got["contacts"])})
            cases += 1
    approaches = []
    for label, x, y, vx, vy in (
        ("from_left_at_surface", cx * 32 - 12, surface - 18, 0x700, 0),
        ("from_right_at_surface", (cx + 1) * 32 + 12, surface - 18, -0x700, 0),
        ("from_below_rising", cx * 32 + 16, surface + 20, 0, -0x700),
        ("from_above_falling", cx * 32 + 16, surface - 40, 0, 0x700),
    ):
        got = lab.run(x, y, vx=vx, vy=vy, prev=0x9C, state=0x0A, attack=True)
        approaches.append({"label": label, "before": [x, y, vx, vy], "after": got})
        cases += 1

    # Isolate each block from its neighbours and compare side/ceiling probes
    # against an all-empty layout.  This avoids attributing adjacent GPZ art
    # cells to the audited block.
    isolated = OrderedDict()
    empty_lab = TerrainLab(rom, "gpz1")
    iso_lab = TerrainLab(rom, "gpz1")
    width = a["width"]
    tcx, tcy = 10, 10
    left, top = tcx * 32, tcy * 32
    empty = bytearray(empty_lab.base)
    empty[1:1 + 4095] = bytes([0x9D]) * 4095
    empty_lab.base = bytes(empty)
    for b in BLOCKS:
        image = bytearray(empty)
        image[1 + tcy * width + tcx] = b
        iso_lab.base = bytes(image)
        row = {}
        for direction, px, vx in (("from_left", left - 8, 0x100),
                                  ("from_right", left + 39, -0x100)):
            changed = []
            for probe_y in range(32):
                py = top + probe_y - 6
                got = iso_lab.run(px, py, vx=vx, vy=-0x100, prev=0, state=0x0A, attack=True)
                baseline = empty_lab.run(px, py, vx=vx, vy=-0x100, prev=0, state=0x0A, attack=True)
                cases += 1
                if (got["x"], got["vx"], got["contacts"]) != (baseline["x"], baseline["vx"], baseline["contacts"]):
                    changed.append(probe_y)
            row[direction + "_side_probe_local_y_changed_ranges"] = ranges(changed)
        ceiling_changed = []
        ceiling_samples = []
        for probe_y in range(-4, 37):
            px, py = left + 16, top + probe_y + 6
            got = iso_lab.run(px, py, vy=-0x100, prev=0, state=0x0A, attack=True)
            baseline = empty_lab.run(px, py, vy=-0x100, prev=0, state=0x0A, attack=True)
            cases += 1
            if (got["y"], got["vy"], got["ceiling"]) != (
                    baseline["y"], baseline["vy"], baseline["ceiling"]):
                ceiling_changed.append(probe_y)
                ceiling_samples.append({"probe_local_y": probe_y, "player_y_before": py,
                                        "player_y_after": got["y"], "player_vy_after": got["vy"],
                                        "ceiling_flag": got["ceiling"], "contacts": hx(got["contacts"])})
        row["ceiling_probe_local_y_changed_ranges"] = ranges(ceiling_changed)
        row["ceiling_changed_samples"] = ceiling_samples
        isolated[hx(b)] = row
    return {"evidence": "CONTROLLED ROUTINE RESULT (original $690B/$6F61/$715E/$73C9 on decoded GPZ1 layout)",
            "cases": cases, "per_block_floor_boundaries": by_block, "state_velocity_matrix": gates,
            "selected_top_side_underside_approaches": approaches,
            "isolated_block_side_underside_sweeps": isolated,
            "projection_rule": "when previous surface low five bits are $1C and sampled vertical byte has bit 6, $6F8E forces effective height 32; otherwise height is raw & $3F"}


def state4_object_sweep(rom: bytes) -> dict:
    """Boundary and timing sweeps for the placed parameter-$83 variant."""
    lab = psc.platform_lab(rom, 0x83, 0x6A)
    ox, oy = lab.obj16(0x11), lab.obj16(0x14)
    contacts = claims = 0
    cases = 0
    region = {}
    for dy in range(-40, 41):
        supported = []
        for dx in range(-40, 41):
            lab.reset()
            lab.player(ox + dx, oy + dy, vy=0x700, f3=0, f22=0)
            cb = lab.callback()
            cases += 1
            contacts += bool(lab.m[psc.SLOT + 0x21])
            claims += bool(lab.m[0xD3C0])
            if lab.m[0xD3C0]:
                supported.append(dx)
        if supported:
            region[str(dy)] = [min(supported), max(supported)]

    # One supported fixture: observe trigger, 80-update delay, gravity, motion,
    # carry and sag/recovery using only the real engine/callback.
    lab.reset()
    lab.player(ox, oy - 8, vy=0x700, f3=0, f22=0)
    timeline = []
    for f in range(105):
        cb = lab.frame()
        timeline.append([f, lab.obj16(0x14), s16(lab.obj16(0x18)), lab.m[psc.SLOT + 0x27],
                         lab.m[psc.SLOT + 0x1E], lab.m[psc.SLOT + 0x35], lab.m[0xD3C0],
                         lab.o.word(0xD514), lab.o.word(0xD518)])
    first_trigger = next((r[0] for r in timeline if r[3]), None)
    first_fall = next((r[0] for r in timeline if r[3] == 0xFF), None)
    first_sag_move = next((r[0] for r in timeline if r[1] != oy), None)
    first_gravity = next((r[0] for r in timeline if r[2] != 0), None)
    first_fall_integer_move = next((r[0] for r in timeline if r[3] == 0xFF and r[1] != oy), None)

    # Side, underside and attack posture are tested independently at contacts
    # which the shared overlap classifies away from the top.
    probes = []
    for name, dx, dy, vy, attack in (
        ("top", 0, -8, 0x700, False), ("left_side", -24, 0, 0, False),
        ("right_side", 24, 0, 0, True), ("underside_rising", 0, 12, -0x700, True),
    ):
        lab.reset(); lab.player(ox + dx, oy + dy, vy=vy, f3=(1 if vy < 0 else 0) | (2 if attack else 0))
        before = [lab.o.word(0xD511), lab.o.word(0xD514), lab.o.word(0xD516), lab.o.word(0xD518)]
        lab.callback()
        probes.append({"name": name, "before": before,
                       "after": [lab.o.word(0xD511), lab.o.word(0xD514), lab.o.word(0xD516), lab.o.word(0xD518)],
                       "contact_bits": hx(lab.m[psc.SLOT + 0x21]), "support_owner": lab.m[0xD3C0],
                       "trigger_phase": hx(lab.m[psc.SLOT + 0x27])})
        cases += 1

    state_matrix = []
    for state in (1, 5, 6, 9, 0x0A, 0x0B, 0x0E, 0x11, 0x12, 0x1C, 0x20, 0x22):
        for vy in (-0x700, 0, 0x700):
            for attack in (False, True):
                lab.reset(); lab.player(ox, oy - 8, vy=vy, f3=(2 if attack else 0), cur=state, req=state,
                                        f22=(2 if state in (1, 5, 6, 9) else 0))
                lab.callback()
                state_matrix.append({"state": hx(state), "player_vy_8_8": vy, "attack": attack,
                                     "floor_before": state in (1, 5, 6, 9),
                                     "supported": bool(lab.m[0xD3C0]),
                                     "phase_after": hx(lab.m[psc.SLOT + 0x27])})
                cases += 1

    lifecycle = []
    for phase in (0, 0x80, 0xFF):
        lab.reset()
        lab.m[psc.SLOT + 4] |= 0x40
        lab.m[psc.SLOT + 0x27] = phase
        before_token = lab.m[psc.SLOT + 0x3E]
        lab.callback()
        lifecycle.append({"phase_before": hx(phase), "tracking_token_before": before_token,
                          "type_after": hx(lab.m[psc.SLOT]),
                          "tracking_token_after": lab.m[psc.SLOT + 0x3E],
                          "saved_parameter_after": hx(lab.m[psc.SLOT + 0x3F])})
        cases += 1
    return {"evidence": "CONTROLLED ROUTINE RESULT (type-$28 parameter $83 initialized by original engine; engine + callback executed)",
            "cases": cases, "initial_state": 4, "callback_cpu": hx(cb, 4),
            "contact_flag_cases": contacts, "support_owner_claim_cases": claims,
            "support_region_dx_range_by_dy": region,
            "timeline_columns": ["update", "platform_y", "platform_vy_8_8", "phase_+27", "delay_+1E", "sag_+35", "D3C0", "player_y", "player_vy"],
            "timeline": timeline, "first_trigger_update": first_trigger, "first_falling_phase_update": first_fall,
            "first_sag_move_update": first_sag_move, "first_gravity_update": first_gravity,
            "first_fall_integer_y_move_update": first_fall_integer_move,
            "selected_contacts": probes, "player_state_velocity_attack_matrix": state_matrix,
            "inactive_lifecycle": lifecycle,
            "reading": "state 4 uses ordinary top-only $8814 support. First top support sets +$27=$80; the script-loaded +$1E=$50 counts down, then +$27=$FF. Falling adds $0030 gravity before moving and tests/carries after moving. Parameter bit 7 enables the shared eight-pixel weight sag."}


def emulated_traces(rom: bytes) -> dict:
    """Selected whole-game traces on a surface-$1C span and a state-3 sprite."""
    # The shared boot accepts the global act index even though earlier tools
    # named only THZ indices.  Index 3/4 are GPZ1/2 in the verified level table.
    psc.ACT_INDEX["gpz1"] = 3
    psc.ACT_INDEX["gpz2"] = 4
    out = {"evidence": "EMULATED ORIGINAL FRAME (approximate SMS harness; update-aligned teleport into original GPZ acts)"}
    e = psc.Emu(rom, "gpz1")

    # Stable $8D span: cell row 1, columns 68..89, surface at world Y 48.
    def run(name, x, y, vx, vy, state, f3, floor=False, pad=0, frames=18, rocket=False):
        e.restore(); e.place(x, y, vx, vy, cur=state, f3=f3, floor=floor, prev=0x9C)
        if rocket:
            e.s.w16(0xD44C, 0x012C)
            e.s.mem[0xD532] = 1
        rows = []
        for f in range(frames):
            e.s.pad = pad
            e.s.run_frame()
            r = psc.player_rec(e)
            rows.append([f, r["x"], r["y"], r["vx"], r["vy"], r["cur"], r["f3"], r["f23"], r["d3c0"], e.s.mem[0xD36C]])
        out[name] = rows

    run("fall_to_surface_1c", 68 * 32 + 16, 8, 0, 0x300, 0x0E, 1)
    run("roll_across_surface_1c", 68 * 32 + 4, 30, 0x500, 0, 9, 2, True, psc.PAD["RIGHT"])
    run("rocket_shoes_across_surface_1c", 68 * 32 + 4, 30, 0x500, 0, 0x11, 1, True, rocket=True)

    # GPZ2 parameter-$83 record at (1584,384).  The trace records the exact
    # owning slot/state and the delayed-fall phase.
    e2 = psc.Emu(rom, "gpz2")
    e2.restore(); e2.place(1584, 350, 0, 0x300, cur=0x0E, f3=1)
    rows = []
    for f in range(110):
        e2.s.run_frame()
        r = psc.player_rec(e2)
        slots = [0xD540 + i * 0x40 for i in range(19) if e2.s.mem[0xD540 + i * 0x40] == 0x28]
        q = next((q for q in slots if e2.s.u16(q + 0x11) == 1584), None)
        rows.append([f, r["x"], r["y"], r["vy"], r["f23"], r["d3c0"],
                     e2.s.mem[q + 1] if q else None, e2.s.u16(q + 0x11) if q else None,
                     e2.s.u16(q + 0x14) if q else None, e2.s.mem[q + 0x27] if q else None])
    out["gpz2_near_parameter_83"] = rows
    out["columns"] = {
        "surface_rows": ["frame", "x", "y", "vx", "vy", "current_state", "d503", "d523", "d3c0", "previous_surface"],
        "parameter_83_rows": ["frame", "x", "y", "vy", "d523", "d3c0", "type28_state", "type28_x", "type28_y", "phase_+27"],
    }
    return out


def build(rom: bytes, static_only: bool = False) -> dict:
    blocks = block_definitions(rom)
    terrain = terrain_census(rom)
    objects = object_census(rom)
    out = OrderedDict([
        ("format", 1), ("rom_sha256", ROM_SHA256), ("research_only", True), ("poc_untouched", True),
        ("identity", {"terrain_surface": "0x1C", "terrain_blocks": [hx(b) for b in BLOCKS],
                      "mapped_object_examined_separately": "0x28",
                      "finding": "Gigapolis contains two distinct systems: visible surface-$1C terrain decks, and type-$28 platforms. Parameter $83 is the object-backed touch-delay/fall/sag variant introduced in GPZ2 and later reused; it is not the source of the surface-$1C deck collision."}),
        ("routines", routines(rom)), ("terrain_blocks", blocks), ("terrain_census", terrain),
        ("type_28_census", objects), ("type_28_terrain_contexts", placement_contexts(rom, objects)),
        ("graphics", graphics(rom)),
        ("surface_1c_boundary_sweeps", None if static_only else terrain_boundary_sweeps(rom)),
        ("type_28_parameter_83_sweep", None if static_only else state4_object_sweep(rom)),
        ("selected_emulator_traces", None if static_only else emulated_traces(rom)),
        ("reuse_manifest", {
            "gigapolis": {k: {"surface_1c_cells": terrain["acts"][k]["count"],
                                "type_28_parameters": objects["acts"][k]["parameter_counts"],
                                "type_28_placements": objects["acts"][k]["placements"]}
                           for k in ("gpz1", "gpz2", "gpz3")},
            "mecha_green_hill": {k: {"surface_1c_cells": terrain["acts"][k]["count"],
                                      "type_28_parameters": objects["acts"][k]["parameter_counts"],
                                      "type_28_placements": objects["acts"][k]["placements"]}
                                 for k in ("mghz1", "mghz2", "mghz3")},
            "other_acts": {k: {"surface_1c_cells": terrain["acts"][k]["count"],
                                "type_28_parameters": objects["acts"][k]["parameter_counts"]}
                           for k in ACTS if not k.startswith(("gpz", "mghz"))},
        }),
        ("unresolved", [
            "Dynamic background/palette/scroll presentation remains outside this static deck-art audit.",
            "Whole-frame traces use the project's approximate SMS harness; visible-playback confirmation remains desirable but no collision rule depends on it.",
        ]),
    ])
    return out


def dumps(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    ap.add_argument("--output", type=Path, default=OUTPUT)
    args = ap.parse_args()
    data = build(load_rom(args.rom), args.static_only)
    text = dumps(data)
    if args.check:
        if args.output.read_text(encoding="utf-8") != text:
            raise SystemExit(f"cache differs: {args.output}")
        print(f"OK {args.output}")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()

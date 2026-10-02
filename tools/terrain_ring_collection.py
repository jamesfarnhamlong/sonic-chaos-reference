#!/usr/bin/env python3
"""Ordinary terrain-ring collection (routine $753E) - research only, deterministic.

Answers: exact probe coordinates, the meaning of +$07 bit 0, tile/quadrant addressing, direction independence,
state gating, edge inclusivity, frame timing, THZ1/THZ2/THZ3 equivalence. Output:
data/rom-cache/terrain-ring-collection.json (numeric labels only).

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT
(original Z80 routines on tools/oracle.py), EMULATED ORIGINAL FRAME (tools/sms_frame_harness.py), UNRESOLVED.

Usage:
  python tools/terrain_ring_collection.py ROM.sms [--check] [--static-only]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "tests"))

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OUTPUT = ROOT / "data" / "rom-cache" / "terrain-ring-collection.json"
BLOCK = 32                      # layout cell = 32x32 px
PROBE_DY = {0: -26, 1: -16}     # DE loaded at $7541 / $754A (+$07 bit 0 clear / set)
ANCHOR_BIAS = 18                # added inside $7725 (same terrain anchor correction as the floor probe)
RING_TYPE = 7
ACTS = ("thz1", "thz2", "thz3")
PRESENCE_ROM = 0x75DC
REPLACEMENT_ROM = 0x75F4


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def u16(rom: bytes, pos: int) -> int:
    return rom[pos] | (rom[pos + 1] << 8)


def rom_of(bank: int, cpu: int) -> int:
    return cpu if cpu < 0x8000 else bank * 0x4000 + cpu - 0x8000


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


EVIDENCE = {
    "DECODED DATA": "ROM tables/records decoded by a parser",
    "BYTE-VERIFIED ASSEMBLY": "routine bytes compared literally and disassembled by hand",
    "SOURCE-TRACED BEHAVIOR": "behavior read from the disassembly, not executed",
    "CONTROLLED ROUTINE RESULT": "original routine executed on a Z80 core with explicit RAM",
    "EMULATED ORIGINAL FRAME": "whole original game run in the approximate SMS harness",
    "UNRESOLVED": "not established",
}

# (name, bank, first CPU, end CPU exclusive, purpose)
ROUTINES = [
    ("surface_probe_dispatch", 1, 0x753E, 0x75DC, "$753E: choose probe offset from +$07 bit 0, call $7725, dispatch on surface type (7 ring, $1D, $1A, $14)"),
    ("ring_quadrant_tables", 1, 0x75DC, 0x760C, "presence table (6 blocks x 4 quadrants) and replacement-block table"),
    ("surface_type_1d_handler", 1, 0x760C, 0x7646, "type $1D: block := $46, +$10 rings, sound $BF"),
    ("surface_type_1a_handler", 1, 0x7646, 0x7666, "type $1A: needs floor bit, X speed $0700, state $10, sound $BD"),
    ("surface_type_14_handler", 1, 0x749D, 0x7500, "type $14 blocks $3A/$3B: depth correction and bounce"),
    ("light_lookup_7725", 1, 0x7725, 0x77B0, "light surface lookup: probe point -> layout cell -> header byte 0"),
    ("lookup_out_of_range", 1, 0x77B0, 0x77CB, "cell pointer outside $C000..$CFFF: block $FF, type 0"),
    ("ring_counter_3138", 0, 0x3138, 0x314A, "$D29A += 1 (BCD) and carry handling"),
    ("probe_wrapper_690b", 1, 0x690B, 0x691A, "$691A, $715E, $73C9, then $753E, then $64CB"),
    ("player_step_3fef", 0, 0x3FEF, 0x4010, "shared player step: clamp $4141 ... $690B then movement $48BC"),
    ("state_probe_caller_4c12", 1, 0x4C12, 0x4C37, "state routine that calls $753E before movement"),
    ("animation_engine", 1, 0x64FA, 0x65AF, "per-update: DEC +$07, reload record at zero"),
    ("player_update_361d", 0, 0x361D, 0x3657, "player slot: engine $64FA, then callback $5E91, then $4A74"),
]

SOURCES_OF_PROBE = {
    "$3FEF (shared step, 22 CALL sites + JP at vector $0404)": "CALL $690B at $400B, before movement $48BC at $400E",
    "$396D / $39E6 handlers": "CALL $690B at $3976 / $39EF, before $48BC",
    "$3F17.. state routine": "CALL $690B at $3F58, before $48BC at $3F5B",
    "$4C12 (vector $044C)": "CALL $753E at $4C19, before $48BC at $4C1C",
    "bank $0C JP $038C (vector -> $690B) at $91DF": "object-side caller, not a player state routine",
}


# --------------------------------------------------------------------------- #
# 1. pure models
# --------------------------------------------------------------------------- #
def tables(rom: bytes) -> tuple[dict, dict]:
    pres = {0x40 + b: [rom[PRESENCE_ROM + b * 4 + q] for q in range(4)] for b in range(6)}
    repl = {0x40 + b: [rom[REPLACEMENT_ROM + b * 4 + q] for q in range(4)] for b in range(6)}
    return pres, repl


def probe_point(x: int, y: int, bit0: int) -> tuple[int, int]:
    """$7725: X is the anchor X; Y = anchorY + DE + $12, negative -> 0."""
    py = y + PROBE_DY[bit0] + ANCHOR_BIAS
    return x, 0 if py < 0 else py


def quadrant(px: int, py: int) -> int:
    return ((px >> 4) & 1) + 2 * ((py >> 4) & 1)


def cell_of(px: int, py: int) -> tuple[int, int]:
    return px >> 5, py >> 5


def collects(block: int, px: int, py: int, pres: dict) -> bool:
    return block in pres and bool(pres[block][quadrant(px, py)])


def anchor_region(left: int, top: int, bit0: int) -> dict:
    """Anchor (x, y) ranges (inclusive) that collect the quadrant with pixel origin (left, top)."""
    dy = PROBE_DY[bit0] + ANCHOR_BIAS
    return {"x": [left, left + 15], "y": [top - dy, top + 15 - dy]}


def ring_quadrants(rows: list, pres: dict) -> list:
    out = []
    for cy, row in enumerate(rows):
        for cx, b in enumerate(row):
            if b in pres:
                for q in range(4):
                    if pres[b][q]:
                        out.append({"cell": (cx, cy), "block": b, "quadrant": q, "left": cx * 32 + (q & 1) * 16, "top": cy * 32 + (q >> 1) * 16})
    return out


# --------------------------------------------------------------------------- #
# 2. static facts
# --------------------------------------------------------------------------- #
def routine_table(rom: bytes) -> list[dict]:
    out = []
    for name, bank, a, z, purpose in ROUTINES:
        o, e = rom_of(bank, a), rom_of(bank, z)
        out.append({"name": name, "bank": bank, "cpu_start": h(a), "cpu_end_exclusive": h(z), "rom_offset": h(o, 5), "length": e - o,
                    "sha256": sha(rom[o:e]), "first_16_bytes": rom[o:o + 16].hex(), "purpose": purpose})
    return out


def header_types(rom: bytes) -> dict:
    """Surface type (low 5 bits of header byte 0) per block through the shared header table (bank 14 $8000, all zones)."""
    by_type: dict[int, list[int]] = defaultdict(list)
    for b in range(256):
        a = 0x30000 + u16(rom, 0x38000 + b * 2)
        by_type[rom[a] & 0x1F].append(b)
    return {"evidence": "DECODED DATA", "table_rom": "0x38000 (bank 14 $8000, selected by $D2E0)",
            "all_zones_use_table_cpu": sorted({r["collision_table_cpu"] for r in csv.DictReader(open(ROOT / "data" / "zone-collision-pointers.csv"))}),
            "blocks_of_type_7": [h(b, 2) for b in by_type[7]], "blocks_of_type_1d": [h(b, 2) for b in by_type[0x1D]],
            "blocks_of_type_1a": [h(b, 2) for b in by_type[0x1A]], "blocks_of_type_14": [h(b, 2) for b in by_type[0x14]]}


def quadrant_tables(rom: bytes) -> dict:
    pres, repl = tables(rom)
    names = ["top_left", "top_right", "bottom_left", "bottom_right"]
    rows = []
    for b in sorted(pres):
        rows.append({"block": h(b, 2), "quadrants_with_ring": [names[q] for q in range(4) if pres[b][q]],
                     "replacement_after_collect": {names[q]: h(repl[b][q], 2) for q in range(4) if pres[b][q]}})
    return {"evidence": "DECODED DATA + BYTE-VERIFIED ASSEMBLY", "presence_rom": h(PRESENCE_ROM, 5), "replacement_rom": h(REPLACEMENT_ROM, 5),
            "index": "(block-$40)*4 + ((probeX>>4)&1) + 2*((probeY>>4)&1)", "rows": rows,
            "presence_values": sorted({v for r in pres.values() for v in r}), "replacement_values": sorted({h(v, 2) for r in repl.values() for v in r})}


def act_rings(rom: bytes) -> dict:
    pres, _ = tables(rom)
    out = {}
    for act in ACTS:
        d = json.loads((ROOT / "data" / "rom-cache" / "levels" / act / "layout.json").read_text(encoding="utf-8"))
        rq = ring_quadrants(d["rows"], pres)
        rings = json.loads((ROOT / "data" / "rom-cache" / "levels" / act / "rings.json").read_text(encoding="utf-8"))["counts"]["terrain"]
        out[act] = {"width_cells": len(d["rows"][0]), "ring_quadrants": len(rq), "cache_terrain_ring_count": rings, "equal": len(rq) == rings,
                    "blocks": sorted({h(r["block"], 2) for r in rq})}
    return out


# --------------------------------------------------------------------------- #
# 3. controlled fixtures
# --------------------------------------------------------------------------- #
class Lab:
    SLOT = 0xD500

    def __init__(self, rom: bytes):
        from oracle import Oracle
        self.rom = rom
        self.o = Oracle(rom)
        self.m = self.o.mem
        self.pres, self.repl = tables(rom)
        self.rows: list = []
        self.width = 128

    def set_layout(self, rows: list) -> None:
        self.rows = [list(r) for r in rows]
        self.width = len(rows[0])
        flat = bytes(b for r in self.rows for b in r)
        self.m[0xC001:0xC001 + len(flat)] = flat
        for row in range(128):
            self.o.word(0xD800 + row * 2, row * self.width)

    def cell_addr(self, cx, cy):
        return 0xC001 + cy * self.width + cx

    def reset(self):
        m = self.m
        m[0xD540:0xD700] = bytes(0x1C0)
        m[0xD29A] = 0
        m[0xD299] = 0
        m[0xDE04] = 0
        m[0xD500] = 1

    def trial(self, x, y, bit0, vx=0, vy=0, req=1, flags03=0, flags22=0):
        o, m = self.o, self.m
        self.reset()
        o.bank(2, 0x0C)
        m[0xD507] = bit0
        o.word(0xD511, x)
        o.word(0xD514, y)
        o.word(0xD516, vx)
        o.word(0xD518, vy)
        m[0xD501] = m[0xD502] = req
        m[0xD500 + 3] = flags03          # +$03 is $D503 (the player's movement flags)
        m[0xD500 + 0x22] = flags22
        o.cpu.ix = self.SLOT
        o.call(0x753E)
        return {"counter": m[0xD29A], "slot0_type": m[0xD540], "effect_xy": (o.word(0xD35C), o.word(0xD35E)),
                "sound": m[0xDE04], "probe": (o.word(0xD358), o.word(0xD35A))}


def probe_coordinate_fixture(lab: Lab) -> dict:
    o, m = lab.o, lab.m
    lab.set_layout(json.loads((ROOT / "data" / "rom-cache" / "levels" / "thz1" / "layout.json").read_text(encoding="utf-8"))["rows"])
    rng = random.Random(7)
    cases = bad = 0
    first_bad = None
    pts = [(rng.randrange(0, 4000), rng.randrange(-30, 1000)) for _ in range(400)] + [(0, 0), (31, 31), (32, 32), (4095, 1000), (1416, 96), (1431, 96), (1432, 96)]
    for x, y in pts:
        for bit0 in (0, 1):
            m[0xD507] = bit0
            lab.reset()
            o.word(0xD511, x & 0xFFFF)
            o.word(0xD514, y & 0xFFFF)
            o.cpu.ix = lab.SLOT
            o.call(0x7725, bc=0, de=PROBE_DY[bit0] & 0xFFFF)
            px, py = probe_point(x, y, bit0)
            row, col = py >> 5, px >> 5
            want_block = lab.rows[row][col] if row < len(lab.rows) and col < lab.width and (row * lab.width + col) < 4095 else None
            got_x, got_y, got_block = o.word(0xD358), o.word(0xD35A), m[0xD353]
            cases += 1
            ok = got_x == px and got_y == py and (want_block is None or got_block == want_block)
            if not ok:
                bad += 1
                first_bad = first_bad or [x, y, bit0, got_x, got_y, got_block, px, py, want_block]
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "$7725 as called by $753E (BC=0)", "cases": cases, "mismatches": bad, "first_mismatch": first_bad,
            "rule": "probeX = anchorX (BC=0); probeY = anchorY + (-26 | -16) + 18, negative -> 0; column = probeX >> 5, row = probeY >> 5 (32x32 layout cells)",
            "effective_probe_offsets_from_anchor_y": {"bit0_clear": -8, "bit0_set": 2}}


def collection_fixture(lab: Lab, act: str) -> dict:
    o, m = lab.o, lab.m
    d = json.loads((ROOT / "data" / "rom-cache" / "levels" / act / "layout.json").read_text(encoding="utf-8"))
    lab.set_layout(d["rows"])
    rq = ring_quadrants(lab.rows, lab.pres)
    cases = bad = collected = 0
    first_bad = None
    edge = {"x": set(), "y0": set(), "y1": set()}
    for r in rq:
        cx, cy = r["cell"]
        addr = lab.cell_addr(cx, cy)
        orig = lab.rows[cy][cx]
        for bit0 in (0, 1):
            reg = anchor_region(r["left"], r["top"], bit0)
            for x in range(r["left"] - 2, r["left"] + 18):
                for y in range(reg["y"][0] - 2, reg["y"][1] + 3):
                    px, py = probe_point(x, y, bit0)
                    in_map = (py >> 5) < len(lab.rows) and (px >> 5) < lab.width
                    paddr = lab.cell_addr(px >> 5, py >> 5) if in_map else None
                    cell_block = lab.rows[py >> 5][px >> 5] if in_map else 0
                    if paddr is not None:
                        m[paddr] = cell_block            # earlier trials may have consumed this cell
                    t = lab.trial(x, y, bit0)
                    want = collects(cell_block, px, py, lab.pres)
                    got = t["counter"] == 1
                    cases += 1
                    collected += got
                    if got != want:
                        bad += 1
                        first_bad = first_bad or [act, r, bit0, x, y, t, want]
                    if got and (px >> 4 << 4, py >> 4 << 4) == (r["left"], r["top"]):
                        edge["x"].add(x)
                        (edge["y0"] if bit0 == 0 else edge["y1"]).add(y)
                    if paddr is not None:
                        m[paddr] = cell_block
    return {"evidence": "CONTROLLED ROUTINE RESULT", "act": act, "ring_quadrants": len(rq), "cases": cases, "mismatches": bad, "first_mismatch": first_bad,
            "collected_cases": collected,
            "accepted_anchor_x_span_over_all_rings": [min(edge["x"]), max(edge["x"])] if edge["x"] else None,
            "model": "collect iff block(probe cell) in $40..$45, presence[block][quadrant(probe)] != 0; quadrant = ((probeX>>4)&1) + 2*((probeY>>4)&1)"}


def region_fixture(lab: Lab) -> dict:
    """Exact accepted anchor rectangle for one isolated quadrant (inclusive edges), both +$07 bit-0 values."""
    lab.set_layout(json.loads((ROOT / "data" / "rom-cache" / "levels" / "thz1" / "layout.json").read_text(encoding="utf-8"))["rows"])
    m = lab.m
    cx, cy = 44, 2                                  # the cell is set to block $42: one ring, top-left quadrant, nothing else nearby
    addr = lab.cell_addr(cx, cy)
    left, top = cx * 32, cy * 32
    for dx in (-1, 1):
        for dy in (-1, 0, 1):
            m[lab.cell_addr(cx + dx, cy + dy)] = 0
    m[lab.cell_addr(cx, cy - 1)] = 0
    m[lab.cell_addr(cx, cy + 1)] = 0
    rows = []
    for bit0 in (0, 1):
        xs, ys = set(), set()
        for x in range(left - 6, left + 24):
            for y in range(top - 40, top + 50):
                m[addr] = 0x42
                if lab.trial(x, y, bit0)["counter"] == 1:
                    xs.add(x)
                    ys.add(y)
                m[addr] = 0x42
        rows.append({"bit0": bit0, "anchor_x_accepted": [min(xs), max(xs)], "anchor_y_accepted": [min(ys), max(ys)],
                     "width": max(xs) - min(xs) + 1, "height": max(ys) - min(ys) + 1,
                     "expected": anchor_region(left, top, bit0)})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "quadrant_pixels": {"left": left, "top": top, "right_inclusive": left + 15, "bottom_inclusive": top + 15},
            "rows": rows, "union_anchor_y_either_parity": [rows[1]["anchor_y_accepted"][0], rows[0]["anchor_y_accepted"][1]],
            "overlap_anchor_y_both_parities": [rows[0]["anchor_y_accepted"][0], rows[1]["anchor_y_accepted"][1]],
            "edges": "all four edges inclusive at integer-pixel resolution; the fractional position bytes (+$10, +$13) are not used"}


def direction_fixture(lab: Lab) -> dict:
    """Same position, many velocities/flags/requested states: collection must not change."""
    lab.set_layout(json.loads((ROOT / "data" / "rom-cache" / "levels" / "thz1" / "layout.json").read_text(encoding="utf-8"))["rows"])
    m = lab.m
    addr = lab.cell_addr(44, 2)
    left, top = 44 * 32, 2 * 32 + 16
    cases = diff = 0
    for bit0, y in ((0, top + 8 + 4), (1, top + 4)):
        for vx in (0, 0x0600, 0xFA00, 0x0100, 0xFF00):
            for vy in (0, 0x0600, 0xFA00, 0x0800, 0xF800):
                for req in (1, 5, 9, 0x0B, 0x0F, 0x10, 0x15, 0x1C):
                    for f03, f22 in ((0, 0), (2, 2), (0x80, 0x40), (0xFF, 0xFF)):
                        m[addr] = 0x41
                        t = lab.trial(left + 8, y, bit0, vx, vy, req, f03, f22)
                        cases += 1
                        if t["counter"] != 1:
                            diff += 1
    return {"evidence": "CONTROLLED ROUTINE RESULT", "cases": cases, "not_collected": diff,
            "conclusion": "the routine reads only +$07 bit 0, X, Y (and +$22 for type $1A): velocity direction, requested state and contact flags do not matter; "
                          "'from below' or 'from the side' collects exactly when the single probe point lies in the quadrant"}


def effects_fixture(lab: Lab) -> dict:
    o, m = lab.o, lab.m
    lab.set_layout(json.loads((ROOT / "data" / "rom-cache" / "levels" / "thz1" / "layout.json").read_text(encoding="utf-8"))["rows"])
    addr = lab.cell_addr(44, 2)
    left, top = 44 * 32, 2 * 32 + 16
    rows = []
    for rings_before in (0x00, 0x09, 0x19, 0x98, 0x99):
        m[addr] = 0x41
        lab.reset()
        m[0xD29A] = rings_before
        m[0xD299] = 0
        lab.reset()
        m[0xD29A] = rings_before
        o.bank(2, 0x0C)
        m[0xD507] = 0
        o.word(0xD511, left + 8)
        o.word(0xD514, top + 8 + 8)
        o.cpu.ix = lab.SLOT
        o.call(0x753E)
        rows.append({"d29a_before": f"{rings_before:02X}", "d29a_after": f"{m[0xD29A]:02X}", "d299_after": m[0xD299], "cell_after": h(m[addr], 2),
                     "slot0_type": m[0xD540], "effect_xy": [o.word(0xD35C), o.word(0xD35E)], "sound": h(m[0xDE04], 2)})
    # replacement chain: every ring quadrant of every ring block
    chain = []
    pres, repl = lab.pres, lab.repl
    for blk in sorted(pres):
        for q in range(4):
            if pres[blk][q]:
                m[addr] = blk
                cxl, cyt = 44 * 32 + (q & 1) * 16, 2 * 32 + (q >> 1) * 16
                t = lab.trial(cxl + 8, cyt + 8 + 8, 0)
                chain.append({"block": h(blk, 2), "quadrant": q, "collected": t["counter"] == 1, "cell_after": h(m[addr], 2), "expected_cell_after": h(repl[blk][q], 2)})
                m[addr] = 0x41
    return {"evidence": "CONTROLLED ROUTINE RESULT", "samples": rows, "replacement_chain": chain,
            "side_effects": "BCD +1 on $D29A (carry past $99 runs $3104 + $178F), block write to the layout cell (D354), tile redraw $23F9, "
                            "type $03 effect via $5E9C at the probe point (D35C/D35E = probeX, probeY), sound $BF, $3138"}


def other_types_fixture(lab: Lab) -> dict:
    """The same probe also handles blocks of surface type $1D, $1A and $14 (not rings)."""
    o, m = lab.o, lab.m
    lab.set_layout(json.loads((ROOT / "data" / "rom-cache" / "levels" / "thz1" / "layout.json").read_text(encoding="utf-8"))["rows"])
    addr = lab.cell_addr(44, 2)
    out = []
    for blk, label in ((0xB8, "type_1d"), (0xA7, "type_1a"), (0x3A, "type_14")):
        for f22 in (0, 2):
            m[addr] = blk
            t = lab.trial(44 * 32 + 8, 2 * 32 + 8 + 8, 0, flags22=f22)
            out.append({"block": h(blk, 2), "label": label, "plus22": f22, "counter": t["counter"], "cell_after": h(m[addr], 2), "d29a": h(m[0xD29A], 2),
                        "x_speed": o.word(0xD516), "requested_state": m[0xD502], "sound": h(m[0xDE04], 2)})
            m[addr] = 0x41
    return {"evidence": "CONTROLLED ROUTINE RESULT", "rows": out,
            "note": "type $1D: block -> $46 and +10 rings; type $1A: needs +$22 bit 1, sets X speed $0700 and requests state $10; type $14: depth correction path. "
                    "Semantic names are UNRESOLVED; they are listed only because they share the probe."}


# --------------------------------------------------------------------------- #
# 4. +$07 bit 0 and state reach
# --------------------------------------------------------------------------- #
CMD_LEN = {0: 2, 1: 4, 2: 6, 3: 3, 4: 8, 5: 6, 6: 3, 7: 4, 8: 6, 9: 4, 0xA: 5, 0xB: 4, 0xC: 4, 0xD: 7, 0xE: 3, 0xF: 4}


def script_callbacks(rom: bytes, cpu: int, bank: int = 0x0C) -> set[int]:
    cbs: set[int] = set()
    seen = set()
    pc = cpu
    for _ in range(300):
        if pc in seen:
            break
        seen.add(pc)
        o = rom_of(bank, pc)
        if rom[o] != 0xFF:
            cbs.add(u16(rom, o + 2))
            pc += 4
            continue
        c = rom[o + 1]
        if c == 5:
            cbs.add(u16(rom, o + 4))
        if c == 0xD:
            cbs.add(u16(rom, o + 5))
        if c in (0, 3):
            break
        if c == 7:
            pc = u16(rom, o + 2)
            continue
        if c == 0xF:
            pc += 4
            continue
        pc += CMD_LEN.get(c, 2)
    return cbs


def reach(rom: bytes, bank: int, start: int, targets: set[int], vec: dict, limit: int = 6000):
    from z80dis import z80
    seen: set[int] = set()
    work = [vec.get(start, start)]
    hits: dict[int, int] = {}
    unknown = 0
    while work and len(seen) < limit:
        a = work.pop()
        while a not in seen and len(seen) < limit:
            seen.add(a)
            o = rom_of(bank, a)
            if o >= len(rom):
                break
            d = z80.decode(rom[o:o + 4], a)
            n = d.len or 1
            op = rom[o]
            tgt = None
            if op in (0xCD, 0xC3) or (op & 0xC7) in (0xC4, 0xC2):
                tgt = rom[o + 1] | rom[o + 2] << 8
            elif op in (0x18, 0x10) or (op & 0xE7) == 0x20:
                e = rom[o + 1]
                e -= 256 if e > 127 else 0
                tgt = (a + 2 + e) & 0xFFFF
            if tgt is not None:
                tgt = vec.get(tgt, tgt)
                if tgt in targets:
                    hits[tgt] = hits.get(tgt, 0) + 1
                elif tgt not in seen:
                    work.append(tgt)
            if op in (0xC9, 0xC3, 0x18) or (op == 0xED and rom[o + 1] in (0x4D, 0x45)):
                break
            if op == 0xE9 or (op == 0xDD and rom[o + 1] == 0xE9):
                unknown += 1
                break
            a += n
    return hits, unknown


# fixed-bank regions of recovered player-state code (ROM offsets from asm/recovered/regions.json) and bank-$0C twist code
CATEGORY_REGIONS = [("rolling_ramp", 0x38C5, 0x3901), ("spring", 0x393B, 0x396D), ("loop", 0x3C1B, 0x3EFD), ("twist", 0x94C1, 0x982A)]


def _category(target: int) -> str | None:
    for name, a, z in CATEGORY_REGIONS:
        if a <= target < z:
            return name
    return None


LAST_REAL_STATE = 0x36


def state_reach(rom: bytes) -> dict:
    vec = {v: u16(rom, v + 1) for v in range(0x0320, 0x0450, 3) if rom[v] == 0xC3}     # fixed-bank vector table (JP entries every 3 bytes from $0320)
    targets = {0x753E}
    rows = []
    with open(ROOT / "data" / "sonic-state-scripts.csv", newline="", encoding="utf-8") as source:
        script_rows = list(csv.DictReader(source))
    for r in script_rows:
        st = int(r["state_hex"], 16)
        if st > LAST_REAL_STATE:
            rows.append({"state": h(st, 2), "script_cpu": r["script_cpu"], "excluded": "pointer is not a plausible state script (points into fixed code, zero fill or a shared tail)"})
            continue
        cbs = sorted(script_callbacks(rom, int(r["script_cpu"], 16)))
        hits_total, unknown = 0, 0
        reached = []
        for cb in cbs:
            hh, u = reach(rom, 0x0C, cb, targets, vec)
            if hh:
                reached.append(h(cb))
            hits_total += sum(hh.values())
            unknown += u
        targets_resolved = sorted({vec.get(c, c) for c in cbs})
        cats = sorted({cat for t in targets_resolved for cat in [_category(t)] if cat})
        rows.append({"state": h(st, 2), "script_cpu": r["script_cpu"], "callbacks": [h(c) for c in cbs], "callback_targets": [h(t) for t in targets_resolved],
                     "region_categories": cats, "callbacks_reaching_753E": reached, "may_probe": bool(reached), "indirect_jumps_not_followed": unknown})
    return {"evidence": "SOURCE-TRACED BEHAVIOR (static reachability over CALL/JP/JR; indirect jumps are not followed)", "rows": rows,
            "states_that_may_probe": [r["state"] for r in rows if r.get("may_probe")],
            "states_that_do_not": [r["state"] for r in rows if "may_probe" in r and not r["may_probe"]],
            "excluded_states": [r["state"] for r in rows if "excluded" in r]}


def timer_fixture(rom: bytes) -> dict:
    """+$07 under the original animation engine for each player state (controlled)."""
    from oracle import Oracle
    o = Oracle(rom)
    m = o.mem
    snap = bytes(m[0xC000:0xE000])
    out = []
    with open(ROOT / "data" / "sonic-state-scripts.csv", newline="", encoding="utf-8") as source:
        script_rows = list(csv.DictReader(source))
    for r in script_rows:
        st = int(r["state_hex"], 16)
        m[0xC000:0xE000] = snap
        m[0xD500] = 1
        for a in range(0xD501, 0xD540):
            m[a] = 0
        m[0xD502], m[0xD501] = st, 0xFF
        seq = []
        for _ in range(26):
            o.bank(2, 0x0C)
            m[0xD12B] = 0x0C
            o.cpu.ix = 0xD500
            o.call(0x64FA)
            seq.append(m[0xD507])
        body = seq[1:]
        out.append({"state": h(st, 2), "plus07_after_each_engine_update_first_26": body,
                    "bit0_set_fraction": round(sum(v & 1 for v in body) / len(body), 3)})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "$64FA with the player slot, bank $0C re-paged before each call (as $361D does)",
            "rule": "records load +$07 = duration; every update without a reload does DEC (IX+7) at $6510; FF 05 / frame-selector routines may set +$07 themselves; "
                    "+$07 bit 0 is therefore the parity of the remaining animation ticks, not a posture flag",
            "states": out}


def emulated_forced_states(rom: bytes) -> dict:
    """Request one player state per trial (requested again every frame) and count probe calls made while the state is current."""
    o18 = _load("object_18")
    from sms_frame_harness import BTN_RIGHT
    rows = json.loads((ROOT / "data" / "rom-cache" / "levels" / "thz1" / "layout.json").read_text(encoding="utf-8"))["rows"]
    tw = [(cx, cy, b) for cy, r in enumerate(rows) for cx, b in enumerate(r) if 0x58 <= b <= 0x73]
    tcx, tcy, tb = tw[len(tw) // 2]
    s = o18._boot(rom, 0, lambda m: None)
    m = s.mem
    for _ in range(120):
        s.pad = 0
        s.run_frame()
    x0, y0 = s.u16(0xD511), s.u16(0xD514)
    calls: list = []
    s.add_pc_hook(0x753E, lambda mm: calls.append(m[0xD501]) if s.cpu.ix == 0xD500 else None)
    out = []
    names = {0x01: "standing", 0x05: "walking", 0x06: "running", 0x09: "rolling", 0x0A: "jump", 0x0B: "spring ascent", 0x0C: "loop (callback $03CB)",
             0x0D: "loop (callback $03D1)", 0x13: "loop (callback $03CE)", 0x0E: "falling", 0x1B: "ramp launch", 0x1C: "diagonal spring", 0x22: "twisting strip"}
    for st in (0x01, 0x05, 0x06, 0x09, 0x0A, 0x0B, 0x0E, 0x1B, 0x1C, 0x0C, 0x0D, 0x13, 0x22):
        x, y = (tcx * 32 + 16, tcy * 32 + 10) if st == 0x22 else (x0, y0)
        for a in (0xD174, 0xD284):
            s.w16(a, x - 104)
        for a in (0xD176, 0xD286):
            s.w16(a, y - 100)
        s.w16(0xD511, x)
        s.w16(0xD514, y)
        s.w16(0xD516, 0x0500)
        s.w16(0xD518, 0)
        for _ in range(4):
            s.pad = 0
            s.run_frame()
        calls.clear()
        cur = []
        for _ in range(30):
            if m[0xD501] != st:
                m[0xD502] = st
            s.pad = BTN_RIGHT
            s.run_frame()
            cur.append(m[0xD501])
        out.append({"state": h(st, 2), "label": names[st], "frames_in_state": cur.count(st), "probe_calls_in_state": calls.count(st)})
    return {"evidence": "EMULATED ORIGINAL FRAME", "method": "state requested every frame (twist on a THZ1 twist block, others near the start); counts only calls whose current state equals the forced one",
            "twist_block_cell": [tcx, tcy], "twist_block": h(tb, 2), "rows": out}


def emulated_all_states(rom: bytes) -> dict:
    """Request every real state in turn (30-frame holds are not needed: one frame in the state suffices) and record whether the probe ran."""
    o18 = _load("object_18")
    from sms_frame_harness import BTN_RIGHT
    s = o18._boot(rom, 0, lambda m: None)
    m = s.mem
    for _ in range(120):
        s.pad = 0
        s.run_frame()
    x0, y0 = s.u16(0xD511), s.u16(0xD514)
    calls: list = []
    s.add_pc_hook(0x753E, lambda mm: calls.append(m[0xD501]) if s.cpu.ix == 0xD500 else None)
    rows = []
    for st in range(0, LAST_REAL_STATE + 1):
        for a in (0xD174, 0xD284):
            s.w16(a, max(x0 - 104, 0))
        for a in (0xD176, 0xD286):
            s.w16(a, y0 - 100)
        s.w16(0xD511, x0)
        s.w16(0xD514, y0)
        s.w16(0xD516, 0x0500)
        s.w16(0xD518, 0)
        for _ in range(4):
            s.pad = 0
            s.run_frame()
        calls.clear()
        cur = []
        for _ in range(12):
            if m[0xD501] != st:
                m[0xD502] = st
            s.pad = BTN_RIGHT
            s.run_frame()
            cur.append(m[0xD501])
        rows.append({"state": h(st, 2), "frames_in_state": cur.count(st), "probe_calls_in_state": calls.count(st)})
    return {"evidence": "EMULATED ORIGINAL FRAME", "method": "each real state requested every frame for 12 frames near the THZ1 start; counts probe calls made while that state is current",
            "rows": rows, "observed_probing": [r["state"] for r in rows if r["probe_calls_in_state"]],
            "observed_not_probing": [r["state"] for r in rows if not r["probe_calls_in_state"] and r["frames_in_state"]],
            "never_held": [r["state"] for r in rows if not r["frames_in_state"]],
            "correction": "static reachability listed $21 and $34 as possible callers; neither probes when held, so the static list over-approximates"}


def emulated_play(rom: bytes) -> dict:
    o18 = _load("object_18")
    from sms_frame_harness import BTN_RIGHT, BTN_LEFT, BTN_DOWN, BTN_1
    s = o18._boot(rom, 0, lambda m: None)
    m = s.mem
    hist: dict = defaultdict(lambda: [0, 0])
    log = []
    order: list = []
    cur = {"f": 0}

    def hook(_):
        if s.cpu.ix != 0xD500:
            return
        st, b = m[0xD501], m[0xD507] & 1
        hist[st][b] += 1
        log.append((cur["f"], st, b, s.u16(0xD511), s.u16(0xD514), m[0xD29A]))
        order.append((cur["f"], "probe"))

    s.add_pc_hook(0x753E, hook)

    def mark(name):
        def fn(_):
            if s.cpu.ix == 0xD500:
                order.append((cur["f"], name))
        return fn

    for pc, name in ((0x3FEF, "step_3fef"), (0x4141, "clamp"), (0x402A, "x_integrate"), (0x4097, "y_integrate"), (0x48BC, "move_48bc")):
        s.add_pc_hook(pc, mark(name))
    rng = random.Random(1)
    pad = 0
    end_pos = {}
    streak = defaultdict(int)
    best = defaultdict(int)
    last_b = {}
    for f in range(6000):
        cur["f"] = f
        if f % 45 == 0:
            r = rng.random()
            pad = BTN_RIGHT if r < .5 else (BTN_RIGHT | BTN_DOWN if r < .65 else (BTN_LEFT if r < .75 else (BTN_RIGHT | BTN_1 if r < .9 else BTN_DOWN)))
        s.pad = pad | (BTN_1 if f % 70 < 8 and pad & BTN_RIGHT else 0)
        s.run_frame()
        end_pos[f] = (s.u16(0xD511), s.u16(0xD514))
    for _, st, b, *_ in log:
        if last_b.get(st) == b:
            streak[st] += 1
        else:
            streak[st] = 1
        best[st] = max(best[st], streak[st])
        last_b[st] = b
    per_frame: dict = defaultdict(list)
    for f, name in order:
        per_frame[f].append(name)
    seq_counts: dict = defaultdict(int)
    for f, names in per_frame.items():
        if "probe" in names:
            seq_counts[" > ".join(names)] += 1
    pos_after_integration = sum(1 for names in per_frame.values() if "probe" in names and "x_integrate" in names and "y_integrate" in names
                                and names.index("x_integrate") < names.index("probe") and names.index("y_integrate") < names.index("probe"))
    frames_with_probe = sum(1 for names in per_frame.values() if "probe" in names)
    return {"evidence": "EMULATED ORIGINAL FRAME",
            "method": "THZ1 booted in tools/sms_frame_harness.py, 6000 frames of seeded pseudo-random pad input (RIGHT, DOWN+RIGHT, LEFT, jump), "
                      "PC hook at $753E with IX=$D500",
            "probe_calls": len(log), "by_state_bit0_clear_set": {h(k, 2): v for k, v in sorted(hist.items())},
            "longest_same_bit0_run_by_state": {h(k, 2): v for k, v in sorted(best.items())},
            "probe_position_equals_same_frame_end_position": [sum(1 for f, st, b, x, y, c in log if end_pos.get(f) == (x, y)), len(log)],
            "frames_with_a_probe": frames_with_probe,
            "frames_where_x_and_y_integration_precede_the_probe": pos_after_integration,
            "frames_where_clamp_precedes_the_probe": sum(1 for names in per_frame.values() if "probe" in names and "clamp" in names and names.index("clamp") < names.index("probe")),
            "event_sequences_per_frame": dict(sorted(seq_counts.items(), key=lambda kv: -kv[1])[:6]),
            "states_probed": [h(k, 2) for k in sorted(hist)]}


# --------------------------------------------------------------------------- #
# 5. unresolved and build
# --------------------------------------------------------------------------- #
UNRESOLVED = [
    "Why the original alternates the probe height: the code only reads +$07 bit 0; whether this is intended dithering or an accident of reusing the animation counter is not established.",
    "Semantic names of surface types $1D, $1A and $14 (the same probe handles them).",
    "Exact per-frame +$07 values for states whose durations are set by frame-selector routines (e.g. run/jump speed-dependent animation) were only measured statistically in play.",
    "A complete census of which player states call the probe at runtime: static reachability is complete but may over-approximate (conditional paths); only states reached in play were observed dynamically.",
    "Rings are removed by writing the layout cell; no ROM evidence was gathered on respawn after re-entering the zone (outside this study).",
    "Pixel-exact visual position of the collected-ring effect (type $03) was not measured; only its logical position (probe point) is established.",
]


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    out = {
        "format": 1, "rom_sha256": ROM_SHA256, "research_only": True, "poc_untouched": True, "machine_facing_label": "terrain_ring_collection",
        "evidence_classes": EVIDENCE,
        "routines": routine_table(rom),
        "probe_callers": SOURCES_OF_PROBE,
        "header_types": header_types(rom),
        "quadrant_tables": quadrant_tables(rom),
        "act_rings": act_rings(rom),
        "model": {"probe_dy_by_bit0": {"0": -26, "1": -16}, "anchor_bias": ANCHOR_BIAS, "effective_probe_y_from_anchor": {"0": -8, "1": 2},
                  "probe_x": "anchor X", "cell": "32x32 layout block", "quadrant": "16x16, index ((x>>4)&1) + 2*((y>>4)&1)"},
        "unresolved": UNRESOLVED, "static_only": static_only,
    }
    out["state_reach"] = state_reach(rom)
    if not static_only:
        lab = Lab(rom)
        out["probe_coordinate_fixture"] = probe_coordinate_fixture(lab)
        out["collection_fixture"] = {act: collection_fixture(Lab(rom), act) for act in ACTS}
        out["region_fixture"] = region_fixture(Lab(rom))
        out["direction_fixture"] = direction_fixture(Lab(rom))
        out["effects_fixture"] = effects_fixture(Lab(rom))
        out["other_types_fixture"] = other_types_fixture(Lab(rom))
        out["timer_fixture"] = timer_fixture(rom)
        out["emulated_play"] = emulated_play(rom)
        out["emulated_forced_states"] = emulated_forced_states(rom)
        out["emulated_all_states"] = emulated_all_states(rom)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    a = ap.parse_args()
    rom = a.rom.read_bytes()
    data = build(rom, a.static_only)
    text = json.dumps(data, indent=1) + "\n"
    if a.check:
        cached = OUTPUT.read_text(encoding="utf-8")
        if a.static_only:
            cj, dj = json.loads(cached), json.loads(text)
            bad = [k for k in dj if k in cj and k != "static_only" and cj[k] != dj[k]]
        else:
            bad = [] if cached == text else ["file"]
        print("OK: cache matches the ROM" if not bad else f"MISMATCH in {bad}")
        sys.exit(1 if bad else 0)
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT} ({len(text)} bytes)")


if __name__ == "__main__":
    main()

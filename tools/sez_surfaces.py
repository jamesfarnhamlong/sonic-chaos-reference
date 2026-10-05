#!/usr/bin/env python3
"""SEZ terrain-mechanics audit: surface $0C / block $AF / dynamic object $13 (crumble ledge) and surface $1A / block $A7 (booster pad).
Research only, deterministic.

Scope (bounded): ONLY the two terrain mechanics and the dynamic type $13 they drive.  Out of scope: $28/$86, $20/$23, $54/$55, monitor repair, parked
presentation defects.
Outputs (numeric labels; region hashes only, no ROM bytes or pixels):
  data/rom-cache/sez/surfaces-0c-1a.json            full evidence (static facts, census, sweeps, whole-game scenarios)
  data/rom-cache/sez/surface-runtime-contracts.json machine-readable runtime contracts + original-routine oracle vectors for the POC

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY (z80dis of every routine involved), SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT (original Z80
routines on tools/oracle.py / the controlled terrain lab), EMULATED ORIGINAL FRAME (whole game in tools/sms_frame_harness.py booted into the act, one row per
player update, player placement applied at the start of a player update), MODEL (an independent translation checked against the above), UNRESOLVED.

Usage:
  python tools/sez_surfaces.py ROM.sms [--check] [--static-only]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import level_package as L                   # noqa: E402
import rom as R                             # noqa: E402

OUT_AUDIT = ROOT / "data" / "rom-cache" / "sez" / "surfaces-0c-1a.json"
OUT_CONTRACTS = ROOT / "data" / "rom-cache" / "sez" / "surface-runtime-contracts.json"
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
RESEARCH_BASE = "a200826"
ZONE = 2
ACTS = ("sez1", "sez2", "sez3")
ZONE_NAMES = ("thz", "gpz", "sez", "mghz", "aqz", "eez")

CRUMBLE_BLOCK = 0xAF
CRUMBLE_REPLACEMENT = 0xB0
CRUMBLE_SIBLINGS = (0xB9, 0xBA, 0xBB)
BOOSTER_BLOCK = 0xA7
CRUMBLE_HANDLER = 0x6B79
BOOSTER_HANDLER = 0x7646
RING_PROBE = 0x753E
SLOT_BASE = 0xD540
SLOT_SIZE = 0x40
CELL = 32


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def s16(v: int) -> int:
    return (v + 32768) % 65536 - 32768


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_json(o) -> str:
    return sha(json.dumps(o, sort_keys=True, separators=(",", ":")).encode())


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM")


def file_of(bank: int, cpu: int) -> int:
    return cpu if cpu < 0x8000 else bank * 0x4000 + (cpu - 0x8000)


def loc(i: int) -> dict:
    return {"file": h(i, 5), "bank": h(i // 0x4000, 2), "cpu": h(i if i < 0x8000 else 0x8000 + i % 0x4000)}


def disasm(rom: bytes, bank: int, start: int, end: int) -> list:
    from z80dis import z80
    out, pos = [], start
    while pos < end:
        o = file_of(bank, pos)
        d = z80.decode(rom[o:o + 4], pos)
        out.append({"cpu": h(pos), "bytes": rom[o:o + d.len].hex(), "text": z80.disasm(d)})
        pos += d.len
    return out


def ranges(values) -> list:
    out = []
    for v in sorted(set(values)):
        if out and v == out[-1][1] + 1:
            out[-1][1] = v
        else:
            out.append([v, v])
    return out


# --------------------------------------------------------------------------- #
# 1. static facts
# --------------------------------------------------------------------------- #
# name, bank, start, end (exclusive), purpose
REGIONS = [
    ("crumble_handler_6b79", 0, 0x6B79, 0x6BAA, "surface $0C floor handler: skip when player Y speed negative; Y speed := 0; spawn type $13 once per distinct probed cell pointer"),
    ("booster_handler_7646", 0, 0x7646, 0x7666, "surface $1A handler (ring probe only): needs +$22 bit 1; X max/speed := $0700; +$03 bit1 set, bit0 clear; request state $10; sound $BD"),
    ("ring_probe_753e", 0, 0x753E, 0x756F, "terrain ring probe entry: lookup at (X, Y-8 | Y+2 by +$07 bit 0); dispatch on the sampled surface type ($07 ring, $1D, $1A, $14)"),
    ("surface_1a_floor_handler_69b1", 0, 0x69B1, 0x69B2, "floor-dispatch entry of surface $1A is a bare RET: the floor pass never acts on $A7"),
    ("type13_callbacks", 0x0C, 0xA2DD, 0xA3AF, "crumble object: init $A2DD, shard fall $A31B, remove $A33F, rider hold $A344, break/replace $A36A"),
    ("spawn_positioned_5eb7", 0, 0x5EB7, 0x5EE1, "16-slot positioned spawn used by $6B79 (slots 0..15, silent no-op when full, leaves IY past the pool)"),
    ("spawn_16_slot_5e9c", 0, 0x5E9C, 0x5EB7, "16-slot allocator used by HUD/ring helpers (type in C, parameter in H)"),
    ("spawn_11_slot_5ee1", 0, 0x5EE1, 0x5EF8, "11-slot child allocator (slots 7..17) used by script command 4"),
    ("script_command4_671f", 0, 0x671F, 0x678C, "script command 4: allocate child via $5EE1, offset from the parent, copy +$04 bit4/+$08/+$09, parameter -> +$3F"),
    ("cell_replace_6c1f", 0, 0x6C1F, 0x6C45, "block replacement: store block id at (D354), redraw the cell through $2425; reached by vector $0428"),
    ("object_scheduler_5dd1", 0, 0x5DD1, 0x5DF1, "object scheduler: D521 := 0, slots 0..18 ascending (after the player callback)"),
    ("object_visibility_61e1", 0, 0x61E1, 0x6276, "generic lifecycle window class lookup (table $1C:$8146); class 2 sets +$04 bit 6, class 3 removes unless +$04 bit 1"),
    ("integrate_60fb", 0, 0x60FB, 0x613C, "24-bit X/Y += sign-extended 8.8 velocity (vector $0338)"),
    ("floor_pass_691a", 1, 0x691A, 0x6973, "foot sample, projection against previous flags, dispatch by surface type"),
    ("terrain_pass_690b", 1, 0x690B, 0x691A, "floor, sides, ceiling, terrain-ring probe, merge"),
    ("ring_probe_dispatch_tail_7556", 0, 0x7556, 0x756F, "CP chain after the lookup: $07, $1D, $1A, $14"),
    ("effect5_81bf", 0x1D, 0x81BF, 0x8259, "level effect 5: every 3rd call alternate 32 bytes to VRAM $2B00 (zone 2) unless boss flag D44E"),
    ("level_clear_297e", 0, 0x297E, 0x298B, "clears $D300..$DBBF (includes $D356, D400 occupancy, slots) at every level initialisation"),
    ("state_10_callback_3a23", 0, 0x3A23, 0x3A37, "player state $10 (spin-dash roll) callback: $3FEF updater, $4281, then $37F4 while the state is kept"),
    ("state_10_setter_4719", 0, 0x4719, 0x473C, "spin-dash roll setter (NOT used by the booster): X speed +/-7.0 by facing, +$03 bit 1, request $10, sound $BE"),
]
FLOOR_DISPATCH = 0x6973
VECTORS = {0x0338: 0x60FB, 0x0329: 0x5EE1, 0x0428: 0x6C1F, 0x032C: 0x5E9C}


def region_table(rom: bytes) -> list:
    return [{"name": n, "bank": h(b, 2), "cpu": h(a), "file": h(file_of(b, a), 5), "length": e - a, "sha256": sha(rom[file_of(b, a):file_of(b, e)]), "purpose": p}
            for n, b, a, e, p in REGIONS]


def header_facts(rom: bytes, blk: int) -> dict:
    hd = R.header(rom, blk)
    return {"block": h(blk, 2), "header_file": h(hd["address"], 5), "flags": h(hd["flags"], 2), "surface_type": h(hd["flags"] & 0x1F, 2), "solid_bit7": bool(hd["flags"] & 0x80),
            "one_way_bit6": bool(hd["flags"] & 0x40), "alt_plane_bit5": bool(hd["flags"] & 0x20), "modifier": hd["modifier"],
            "vertical_profile_by_x": list(hd["vertical"]), "horizontal_profile_distinct": sorted(set(hd["horizontal"])), "trailing_byte": hd["trailing_byte"]}


def byte_scan(rom: bytes, lo: int, hi: int) -> list:
    return [p for p in range(len(rom) - 1) if rom[p] == lo and rom[p + 1] == hi]


def operand_sites(rom: bytes) -> dict:
    """Whole-ROM scan of the little-endian absolute operands that carry the two mechanics' state."""
    roles = {
        "D354": {0x6B85: "$6B79: HL := probed cell pointer (compare)", 0x6B9E: "$6B79: HL := probed cell pointer (store as remembered cell)",
                 0x6BE0: "breakable-block handler $6B2C", 0x6C2B: "$6C1F cell replacement target", 0x7064: "sink branch / floor projection helper",
                 0x75AB: "terrain ring replacement ($753E chain)", 0x7615: "ring-probe helper", 0x76C8: "lookup $7666: store probed cell pointer",
                 0x778F: "object lookup $7725: store", 0x77B4: "object lookup $7725: store", 0x7865: "breakable helper", 0x78A1: "breakable helper",
                 0x323A2: "bank $0C: store (type $0D/$07 helper)"},
        "D356": {0x6B89: "$6B79: DE := remembered cell pointer (compare)", 0x6BA1: "$6B79: store remembered cell pointer after the spawn call"},
    }
    out = {}
    for name, lohi in (("D354", (0x54, 0xD3)), ("D356", (0x56, 0xD3)), ("D521", (0x21, 0xD5))):
        rows = []
        for p in byte_scan(rom, *lohi):
            rows.append({"operand": h(p, 5), **{k: v for k, v in loc(p).items() if k != "file"}, "context_bytes": rom[p - 1:p + 2].hex(), "role": roles.get(name, {}).get(p, "UNCLASSIFIED")})
        out[name] = rows
    out["reading"] = ("$D356 has exactly two operand sites, both inside $6B79 (one read, one write): it is written ONLY by the crumble handler and cleared only by the $297E level clear "
                      "($D300..$DBBF).  $D521 is cleared every frame by the scheduler ($5DD1) and set bit 1 by the rider callback $A344.")
    return out


def level_clear_facts(rom: bytes) -> dict:
    callers = [p for p in range(0x8000) if rom[p] == 0xCD and (rom[p + 1] | rom[p + 2] << 8) == 0x297E]
    lo, n = 0xD300, 0x08BF + 1
    return {"evidence": "BYTE-VERIFIED ASSEMBLY (LDIR at $2989 with HL=$D300, DE=$D301, BC=$08BF after a zero store)", "routine": "$297E",
            "clears_cpu_range": [h(lo), h(lo + n - 1)], "covers_d356": lo <= 0xD356 < lo + n, "covers_slots_d540": lo <= 0xD540 < lo + n,
            "covers_occupancy_d400": lo <= 0xD400 < lo + n, "covers_effect_state_d452": lo <= 0xD452 < lo + n, "covers_d12f_frame_counter": lo <= 0xD12F < lo + n,
            "caller_sites": [loc(p) | {"cpu": h(p)} for p in callers], "caller_count": len(callers)}


def type13_facts(rom: bytes) -> dict:
    import mghz_object_census as C
    sc = C.state_scripts(rom, 0x13)
    pub = C.public_script(sc)
    return {"type_table_entry_rom": h(sc["type_table_entry_rom"], 5), "bank": h(sc["bank"], 2), "state_table_cpu": pub["state_table_cpu"], "state_table_rom": pub["state_table_rom"],
            "state_count": sc["state_count"], "state_script_cpus": pub["state_script_cpus"], "callbacks": pub["callbacks"], "calls": pub["calls"], "frames_used": pub["frames_used"],
            "spawns": pub["spawns"], "sets_bit4": pub["sets_bit4"], "clears_bit4": pub["clears_bit4"], "states": pub["states"],
            "callback_roles": {"0xA2DD": "state 0 init: parameter != 0 -> request state 3 (shard) else snap to the cell (+14,+24), remember the cell origin, request state 1",
                               "0xA344": "state 1, record 1 (16 updates): player rider hold", "0xA36A": "state 1, record 2 (1 update): break = cell replacement unless asleep / left of camera X",
                               "0xA33F": "state 1 tail and state 2: remove self (type := $FF)", "0xA31B": "state 3 shard: sleep -> remove; parameter countdown; vy += $0200; integrate"},
            "state_2_reached_by_code": False,
            "state_2_note": "no routine writes requested state 2: $A2DD writes 1 or 3 only; the state-2 script (and its remove callback) is unreachable (static scan of the type's callbacks)"}


def static_facts(rom: bytes) -> dict:
    disp = {h(t, 2): h(rom[FLOOR_DISPATCH + 2 * t] | rom[FLOOR_DISPATCH + 2 * t + 1] << 8) for t in range(0x1D)}
    vec = {}
    for v, target in VECTORS.items():
        stub = rom[v:v + 3]
        assert stub[0] == 0xC3 and (stub[1] | stub[2] << 8) == target, v
        vec[h(v)] = h(target)
    routines = {}
    for n, b, a, e, p in REGIONS:
        if n in ("crumble_handler_6b79", "booster_handler_7646", "type13_callbacks", "spawn_positioned_5eb7", "spawn_11_slot_5ee1", "cell_replace_6c1f", "level_clear_297e",
                 "state_10_callback_3a23", "state_10_setter_4719", "ring_probe_753e", "effect5_81bf", "script_command4_671f", "spawn_16_slot_5e9c"):
            routines[n] = disasm(rom, b, a, e)
    heads = {h(b, 2): header_facts(rom, b) for b in (CRUMBLE_BLOCK, CRUMBLE_REPLACEMENT, BOOSTER_BLOCK) + CRUMBLE_SIBLINGS}
    surf0c = [h(b, 2) for b in range(256) if R.header(rom, b)["flags"] & 0x1F == 0x0C]
    surf1a = [h(b, 2) for b in range(256) if R.header(rom, b)["flags"] & 0x1F == 0x1A]
    identical = {h(b, 2): all(R.header(rom, b)[k] == R.header(rom, CRUMBLE_BLOCK)[k] for k in ("flags", "modifier", "vertical", "horizontal")) for b in CRUMBLE_SIBLINGS}
    return {"evidence": "DECODED DATA + BYTE-VERIFIED ASSEMBLY", "floor_dispatch_table_6973": {"surface_$0C": disp["0x0C"], "surface_$1A": disp["0x1A"], "surface_$00": disp["0x00"]},
            "vectors": vec, "routines_disassembly": routines, "regions": region_table(rom), "block_headers": heads,
            "surface_0c_blocks_all_zones": surf0c, "surface_1a_blocks_all_zones": surf1a, "siblings_header_identical_to_af": identical,
            "operand_sites": operand_sites(rom), "level_clear": level_clear_facts(rom), "type13": type13_facts(rom)}


# --------------------------------------------------------------------------- #
# 2. census of every act in every zone
# --------------------------------------------------------------------------- #
def act_layout(rom: bytes, zone: int, act: int) -> dict:
    d = L.build_descriptor(rom, "x", {"zone": zone, "act": act, "name": "x"})
    cells, _, _ = L.decode_layout_stream(rom, d["header"]["layout_rom"], L.LAYOUT_RAM_LIMIT_CELLS)
    w = d["header"]["width_cells"]
    return {"zone": zone, "act": act, "key": f"{ZONE_NAMES[zone]}{act + 1}", "width": w, "cells": cells, "height": len(cells) // w, "header": d["header"]}


def all_layouts(rom: bytes) -> dict:
    return {f"{ZONE_NAMES[z]}{a + 1}": act_layout(rom, z, a) for z in range(6) for a in range(3)}


def block_at(lay: dict, cx: int, cy: int):
    if 0 <= cx < lay["width"] and 0 <= cy < lay["height"]:
        i = cy * lay["width"] + cx
        return lay["cells"][i] if i < len(lay["cells"]) else None
    return None


def cell_geometry(cx: int, cy: int) -> dict:
    """Derived world coordinates for one $AF cell (all from the proven formulas in the sections below)."""
    x0, y0 = cx * CELL, cy * CELL
    return {"cell_origin": [x0, y0], "object_anchor": [x0 + 14, y0 + 24], "hold_anchor_y": y0 + 24 - 40, "standing_anchor_y_on_solid_cell_top": y0 - 18,
            "shard_anchors": [[x0 + o, y0] for o in (0, 8, 16, 24)], "cell_pointer_offset_from_c001": cy * 128 + cx}


def census(rom: bytes, lays: dict) -> dict:
    out = {"evidence": "DECODED DATA (layout streams of all 18 acts, loader ceiling 4095 cells)", "acts": {}, "totals": {}}
    tot = {"crumble_af": {}, "booster_a7": {}, "b0": {}}
    for key, lay in lays.items():
        row = {"width": lay["width"], "cells_loaded": len(lay["cells"])}
        for name, blk in (("af", CRUMBLE_BLOCK), ("a7", BOOSTER_BLOCK), ("b0", CRUMBLE_REPLACEMENT)) + tuple((f"sibling_{b:02X}", b) for b in CRUMBLE_SIBLINGS):
            pos = [(i % lay["width"], i // lay["width"]) for i, b in enumerate(lay["cells"]) if b == blk]
            if not pos:
                continue
            entries = []
            for cx, cy in pos:
                e = {"cell": [cx, cy], "world": [cx * CELL, cy * CELL]}
                if blk == CRUMBLE_BLOCK:
                    e.update(cell_geometry(cx, cy))
                e["neighbours"] = {k: (None if block_at(lay, cx + dx, cy + dy) is None else h(block_at(lay, cx + dx, cy + dy), 2))
                                   for k, (dx, dy) in {"above": (0, -1), "below": (0, 1), "left": (-1, 0), "right": (1, 0)}.items()}
                entries.append(e)
            row[name] = entries
            tot.setdefault({"af": "crumble_af", "a7": "booster_a7", "b0": "b0"}.get(name, name), {})[key] = len(pos)
        out["acts"][key] = row
    out["totals"] = tot
    out["sez_counts"] = {"crumble_af": [tot["crumble_af"].get(k, 0) for k in ACTS], "booster_a7": [tot["booster_a7"].get(k, 0) for k in ACTS]}
    out["other_zone_counts"] = {"crumble_af": {k: v for k, v in tot["crumble_af"].items() if not k.startswith("sez")}, "booster_a7": {k: v for k, v in tot["booster_a7"].items() if not k.startswith("sez")}}
    out["b0_in_initial_layouts"] = sum(tot["b0"].values())
    return out


def crumble_runs(lay: dict) -> list:
    """Maximal horizontal runs of $AF cells per row."""
    runs = []
    for cy in range(lay["height"]):
        row = [cx for cx in range(lay["width"]) if block_at(lay, cx, cy) == CRUMBLE_BLOCK]
        for a, b in ranges(row):
            runs.append({"row": cy, "cells": [a, b], "count": b - a + 1})
    return runs


# --------------------------------------------------------------------------- #
# 3. controlled-routine labs (original Z80 routines on tools/oracle.py, no VDP / scheduler / camera)
# --------------------------------------------------------------------------- #
PLAYER = 0xD500


class CrumbleLab:
    """The original $6B79 handler, the original type-$13 engine pass ($64FA) and callbacks and the cell replacement vector on a decoded act layout.

    Everything the real game would supply is explicit RAM: player block, probed cell registers ($D354/$D358/$D35A), remembered cell ($D356), camera X ($D174)."""

    def __init__(self, rom: bytes, zone: int = ZONE, act: int = 0):
        import thz1_animation_reach as A
        from oracle import Oracle
        self.rom = rom
        d = L.build_descriptor(rom, "x", {"zone": zone, "act": act, "name": "x"})
        cells, _, _ = L.decode_layout_stream(rom, d["header"]["layout_rom"], L.LAYOUT_RAM_LIMIT_CELLS)
        self.width = d["header"]["width_cells"]
        self.cells0 = bytes((cells + [0] * 4095)[:4095])
        self.o = Oracle(rom)
        self.m = self.o.mem
        self.bank = A.animation_bank(0x13)
        self.o.word(0xD168, d["header"]["row_offset_table_cpu"])
        self.o.word(0xD16A, -self.width)
        self.m[0xD800:0xD900] = bytes(256)
        self.reset()

    def reset(self) -> None:
        m, o = self.m, self.o
        m[0xC001:0xD000] = self.cells0
        for i in range(19):
            b = SLOT_BASE + i * SLOT_SIZE
            m[b:b + SLOT_SIZE] = bytes(SLOT_SIZE)
        m[0xD500] = 1
        m[0xD52C], m[0xD52D] = 8, 24
        o.word(0xD356, 0)
        o.word(0xD174, 0)
        o.word(0xD176, 0)
        m[0xD521] = 0
        m[0xD503] = 0
        o.cpu.ix = PLAYER

    # -- helpers
    def ptr(self, cx: int, cy: int) -> int:
        return 0xC001 + cy * self.width + cx

    def cell(self, cx: int, cy: int) -> int:
        return self.m[self.ptr(cx, cy)]

    def slot(self, i: int) -> int:
        return SLOT_BASE + i * SLOT_SIZE

    def row(self, i: int) -> dict:
        m, o, b = self.m, self.o, self.slot(i)
        return {"slot": i, "type": m[b], "state": m[b + 1], "req": m[b + 2], "frame": m[b + 6], "dur": m[b + 7], "f4": m[b + 4], "x": o.word(b + 0x11), "y": o.word(b + 0x14),
                "vx": s16(o.word(b + 0x16)), "vy": s16(o.word(b + 0x18)), "p3f": m[b + 0x3F], "cb": o.word(b + 0xC), "cell": o.word(b + 0x30), "cx": o.word(b + 0x34), "cy": o.word(b + 0x36)}

    def live(self) -> list:
        return [self.row(i) for i in range(19) if self.m[self.slot(i)]]

    def player(self, x: int, y: int, vy: int = 0, f3: int = 0, state: int = 5) -> None:
        o, m = self.o, self.m
        o.word(0xD511, x)
        o.word(0xD514, y)
        o.word(0xD518, vy & 0xFFFF)
        m[0xD503] = f3
        m[0xD501] = m[0xD502] = state

    def probe(self, cx: int, cy: int, px: int = None, py: int = None) -> None:
        """Registers the lookup $7666 would leave for a foot sample inside cell (cx, cy)."""
        o = self.o
        o.word(0xD354, self.ptr(cx, cy))
        o.word(0xD358, cx * CELL + 16 if px is None else px)
        o.word(0xD35A, cy * CELL + 2 if py is None else py)

    def handler(self) -> dict:
        self.o.cpu.ix = PLAYER
        self.o.call(CRUMBLE_HANDLER)
        return self.snapshot_player()

    def snapshot_player(self) -> dict:
        o, m = self.o, self.m
        return {"d518": o.word(0xD518), "d356": o.word(0xD356), "y": o.word(0xD514), "d521": m[0xD521]}

    def step_slot(self, i: int) -> None:
        o, m = self.o, self.m
        b = self.slot(i)
        o.bank(2, self.bank)
        m[0xD12B] = self.bank
        o.cpu.ix = b
        m[0xD44F] = 0xFF
        o.call(0x64FA)
        cb = m[b + 0xC] | m[b + 0xD] << 8
        if cb:
            o.bank(2, self.bank)
            m[0xD12B] = self.bank
            o.cpu.ix = b
            o.call(cb)
        m[0xD44F] = 0

    def object_pass(self) -> list:
        """One scheduler pass: D521 := 0, then every live type-$13 slot ascending (the scheduler order); returns the per-slot rows seen."""
        self.m[0xD521] = 0
        for i in range(19):
            if self.m[self.slot(i)] == 0x13:
                self.step_slot(i)
        return self.live()


def fill_slots(lab: CrumbleLab, slots, typ: int = 0x0F) -> None:
    for i in slots:
        lab.m[lab.slot(i)] = typ


def handler_model(d519: int, same_cell: bool, occupied: set, ptr: int, x: int, y: int, d518_before: int, d356_before: int) -> dict:
    """Independent translation of $6B79 (+ $5EB7 + the IY write): returns the post state."""
    if d519 & 0x80:
        return {"d518": d518_before, "d356": d356_before, "spawn": None, "slot16_30_31": None}
    out = {"d518": 0, "d356": d356_before, "spawn": None, "slot16_30_31": None}
    if same_cell:
        return out
    free = next((i for i in range(16) if i not in occupied), None)
    out["d356"] = ptr
    if free is None:
        out["slot16_30_31"] = [ptr & 0xFF, ptr >> 8]          # IY is left at $D940 (slot 16): +$30/+$31 := L/H of the cell pointer
    else:
        out["spawn"] = {"slot": free, "type": 0x13, "p3f": 0, "x": x, "y": y, "cell_pointer_30_31": [ptr & 0xFF, ptr >> 8]}
    return out


def handler_matrix(rom: bytes) -> dict:
    """$6B79 against its model: all 256 values of the Y-speed high byte (+$19) x same/different remembered cell x pool free / full / first-k occupied."""
    lab = CrumbleLab(rom)
    cx, cy = 67, 6
    ptr = lab.ptr(cx, cy)
    cases = mism = 0
    spawn_slots = {}
    examples = {}

    def run(d519, same, occupied, d518_low=0x34, d356_other=None):
        nonlocal cases, mism
        lab.reset()
        lab.player(2160, 176, vy=(d519 << 8) | d518_low)
        lab.probe(cx, cy, 2160, 194)
        lab.o.word(0xD356, ptr if same else (ptr - 1 if d356_other is None else d356_other))
        fill_slots(lab, occupied)
        for off in (0x30, 0x31):
            lab.m[0xD940 + off] = 0xEE                    # slot 16 sentinel bytes
        d356_before = lab.o.word(0xD356)
        post = lab.handler()
        d518_before = (d519 << 8) | d518_low
        mod = handler_model(d519, same, set(occupied), ptr, 2160, 194, d518_before, d356_before)
        types = [lab.m[lab.slot(i)] for i in range(19)]
        spawned = [i for i in range(19) if i not in occupied and types[i]]
        got = {"d518": post["d518"], "d356": post["d356"], "spawn": None, "slot16_30_31": None}
        if spawned:
            i = spawned[0]
            b = lab.slot(i)
            got["spawn"] = {"slot": i, "type": types[i], "p3f": lab.m[b + 0x3F], "x": lab.o.word(b + 0x11), "y": lab.o.word(b + 0x14), "cell_pointer_30_31": [lab.m[b + 0x30], lab.m[b + 0x31]]}
        if lab.m[0xD940 + 0x30] != 0xEE or lab.m[0xD940 + 0x31] != 0xEE:
            got["slot16_30_31"] = [lab.m[0xD940 + 0x30], lab.m[0xD940 + 0x31]]
        cases += 1
        if got != mod:
            mism += 1
        return got

    for d519 in range(256):
        for same in (False, True):
            run(d519, same, ())
    for d519 in (0x00, 0x7F, 0x80, 0xFF):
        for same in (False, True):
            run(d519, same, tuple(range(16)))
    for k in range(17):
        g = run(0x01, False, tuple(range(k)))
        spawn_slots[k] = None if g["spawn"] is None else g["spawn"]["slot"]
    for pat in (tuple(range(0, 16, 2)), tuple(range(1, 16, 2)), (0, 2, 3, 5, 7, 11, 12), (15,), tuple(range(1, 16)), tuple(range(0, 15))):
        g = run(0x01, False, pat)
        spawn_slots["pattern_" + "".join(f"{i:x}" for i in pat)] = None if g["spawn"] is None else g["spawn"]["slot"]
    full = run(0x01, False, tuple(range(16)))
    examples["full_pool"] = full
    examples["free_pool"] = run(0x01, False, ())
    # D518 is zeroed before the same-cell test (so every call with a non-negative Y speed zeroes it); D356 follows even when nothing was created
    return {"evidence": "CONTROLLED ROUTINE RESULT ($6B79 and $5EB7 executed) vs MODEL", "cases": cases, "mismatches": mism, "first_free_slot_by_first_k_occupied": spawn_slots,
            "examples": examples, "model": "if +$19 bit7: nothing; else D518 := 0; if D354 == D356: stop; else spawn type $13 at the first free slot of 0..15 (position $D358/$D358, parameter 0) "
            "or nothing when full; D356 := D354 (also when full); when full IY = $D940 so +$30/+$31 of slot 16 receive the cell pointer"}


# --- type $13 callbacks ---------------------------------------------------------
def new_crumble_object(lab: CrumbleLab, slot: int = 0, x: int = 2160, y: int = 194, p: int = 0) -> int:
    b = lab.slot(slot)
    lab.m[b:b + SLOT_SIZE] = bytes(SLOT_SIZE)
    lab.m[b] = 0x13
    lab.o.word(b + 0x11, x)
    lab.o.word(b + 0x14, y)
    lab.m[b + 0x3F] = p
    return b


def call_callback(lab: CrumbleLab, addr: int, b: int) -> None:
    o, m = lab.o, lab.m
    o.bank(2, lab.bank)
    m[0xD12B] = lab.bank
    o.cpu.ix = b
    o.call(addr)


def init_matrix(rom: bytes) -> dict:
    """$A2DD: parameter != 0 requests state 3 and nothing else; parameter 0 snaps to the cell (+14, +24), remembers the raw probe position, requests state 1."""
    lab = CrumbleLab(rom)
    cases = mism = 0
    for p in range(256):
        for (x, y) in ((2160, 194), (0x0834, 0x01C7), (0x1FFF, 0x0FFF), (5, 5), (0x00E0, 0x00E0), (0x01FF, 0x03E0)):
            b = new_crumble_object(lab, 0, x, y, p)
            call_callback(lab, 0xA2DD, b)
            ex = {"req": 3} if p else {"req": 1, "x": (x & 0xFFE0) + 14, "y": (y & 0xFFE0) + 24, "cell_x": x, "cell_y": y}
            got = {"req": lab.m[b + 2]}
            if not p:
                got.update({"x": lab.o.word(b + 0x11), "y": lab.o.word(b + 0x14), "cell_x": lab.o.word(b + 0x34), "cell_y": lab.o.word(b + 0x36)})
            else:
                if lab.o.word(b + 0x11) != x or lab.o.word(b + 0x14) != y:
                    mism += 1
            cases += 1
            mism += got != ex
    for xl in range(256):                                         # every X / Y low byte
        for (x0, y0, axis) in ((0x0800 + xl, 0x0100, "x"), (0x0800, 0x0100 + xl, "y")):
            b = new_crumble_object(lab, 0, x0, y0, 0)
            call_callback(lab, 0xA2DD, b)
            ok = lab.o.word(b + 0x11) == (x0 & 0xFFE0) + 14 and lab.o.word(b + 0x14) == (y0 & 0xFFE0) + 24
            cases += 1
            mism += not ok
    return {"evidence": "CONTROLLED ROUTINE RESULT ($A2DD executed) vs MODEL", "cases": cases, "mismatches": mism,
            "rule": {"parameter_nonzero": "requested state 3 (shard), position and everything else untouched", "parameter_zero": "X := (X & $FFE0) + 14, Y := (Y & $FFE0) + 24 (cell centre-ish anchor), "
                     "+$34/+$35 := raw X, +$36/+$37 := raw Y (the probed position, not snapped), requested state 1"}}


def rider_model(d501: int, d503: int) -> bool:
    return d501 == 0x0E or not (d503 & 1)


def rider_matrix(rom: bytes) -> dict:
    """$A344 (rider hold) for every player state 0..$36 and every +$03 value."""
    lab = CrumbleLab(rom)
    cases = mism = 0
    held = {}
    for st in range(0x37):
        for f3 in range(256):
            lab.reset()
            b = new_crumble_object(lab, 0, 2158, 216, 0)
            lab.o.word(0xD511, 2000)
            lab.o.word(0xD514, 1234)
            lab.o.word(0xD518, 0x0345)
            lab.m[0xD501] = st
            lab.m[0xD503] = f3
            lab.m[0xD521] = 0
            call_callback(lab, 0xA344, b)
            applied = lab.o.word(0xD514) == 216 - 40 and lab.o.word(0xD518) == 0 and lab.m[0xD521] == 2
            untouched = lab.o.word(0xD514) == 1234 and lab.o.word(0xD518) == 0x0345 and lab.m[0xD521] == 0
            cases += 1
            if applied != rider_model(st, f3) or applied == untouched or lab.o.word(0xD511) != 2000:
                mism += 1
            held.setdefault(st, 0)
            held[st] += applied
    return {"evidence": "CONTROLLED ROUTINE RESULT ($A344 executed) vs MODEL", "cases": cases, "mismatches": mism,
            "rule": "hold iff player state == $0E OR +$03 bit 0 clear; effect: player Y := objectY - 40, Y speed := 0, $D521 bit 1 set; player X, state and every other byte untouched; "
                    "the object's own position is NOT compared with the player's (no horizontal or vertical presence test)",
            "held_count_by_state_of_256_f3_values": {h(k, 2): v for k, v in held.items()}}


def break_model(f4: int, obj_x: int, cam_x: int) -> str:
    if f4 & 0x40:
        return "removed"
    if ((obj_x - cam_x) & 0x10000) or obj_x < cam_x:
        return "removed"
    return "replaced"


def break_matrix(rom: bytes) -> dict:
    """$A36A: replace the cell unless the object is asleep (+$04 bit 6) or its X is left of camera X ($D174, unsigned 16-bit compare)."""
    lab = CrumbleLab(rom)
    cx, cy = 67, 6
    ptr = lab.ptr(cx, cy)
    cases = mism = 0
    outcomes = {}
    for f4 in range(256):
        for dcam in (-40, -2, -1, 0, 1, 2, 40):
            lab.reset()
            ox = cx * CELL + 14
            b = new_crumble_object(lab, 0, ox, cy * CELL + 24, 0)
            lab.m[b + 1] = 1
            lab.m[b + 4] = f4
            lab.o.word(b + 0x34, cx * CELL + 16)
            lab.o.word(b + 0x36, cy * CELL + 2)
            lab.o.word(b + 0x30, ptr)
            lab.o.word(0xD174, (ox - dcam) & 0xFFFF)
            call_callback(lab, 0xA36A, b)
            res = "removed" if lab.m[b] == 0xFF else ("replaced" if lab.cell(cx, cy) == CRUMBLE_REPLACEMENT else "other")
            cases += 1
            exp = break_model(f4, ox, (ox - dcam) & 0xFFFF)
            mism += res != exp
            outcomes[res] = outcomes.get(res, 0) + 1
    for cam in (0, 1, 0x7FFF, 0x8000, 0xFFFF, 100, 2159, 2158, 2157):          # camera values including 16-bit wrap
        lab.reset()
        ox = 2158
        b = new_crumble_object(lab, 0, ox, 216, 0)
        lab.m[b + 1] = 1
        lab.o.word(b + 0x34, 2160)
        lab.o.word(b + 0x36, 194)
        lab.o.word(b + 0x30, ptr)
        lab.o.word(0xD174, cam)
        call_callback(lab, 0xA36A, b)
        res = "removed" if lab.m[b] == 0xFF else ("replaced" if lab.cell(cx, cy) == CRUMBLE_REPLACEMENT else "other")
        cases += 1
        mism += res != break_model(0, ox, cam)
    return {"evidence": "CONTROLLED ROUTINE RESULT ($A36A executed) vs MODEL", "cases": cases, "mismatches": mism, "outcome_counts": outcomes,
            "rule": "removed (type := $FF, cell NOT replaced) iff +$04 bit 6 set or objectX < cameraX ($D174, unsigned 16-bit compare, strict); otherwise the cell pointer in +$30/+$31 receives block $B0 "
                    "through $0428 -> $6C1F (redraw origin: X from +$34/+$35 & $FFE0, Y from +$36/+$37 & $FFE0 | $10)"}


# --- shards and the 11-slot child pool --------------------------------------------
SHARD_PARAMS = (3, 8, 5, 1)
SHARD_OFFSETS = (-14, -6, 2, 10)             # X offsets from the crumble object (anchor X = cell + 14 -> cell + 0, 8, 16, 24)
SHARD_DY = -24                                # Y offset (anchor Y = cell + 24 -> cell + 0)


def shard_model(p: int, n: int, y0: int) -> int:
    """Y of a shard after n object passes since it was created (n = 1 is the state-0 pass)."""
    y = y0
    delay, vy = p, 0x200                 # the state-3 script loads Y speed + once
    for k in range(2, n + 1):
        if delay:
            delay -= 1
            continue
        vy += 0x200
        y += vy >> 8
    return y


def shard_move_index(p: int) -> int:
    """Object pass (counting from creation, state-0 pass = 1) of the first movement."""
    return p + 2


def shard_matrix(rom: bytes) -> dict:
    lab = CrumbleLab(rom)
    cases = mism = 0
    first_move = {}
    for p in range(1, 256):                                      # parameter 0 is the crumble parent (state 1), not a shard
        lab.reset()
        b = new_crumble_object(lab, 7, 2160, 192, p)
        ys, first = [], None
        for n in range(1, p + 14):
            lab.m[0xD521] = 0
            lab.step_slot(7)
            y = lab.o.word(b + 0x14)
            ys.append(y)
            if first is None and n >= 2 and y != 192:
                first = n
            cases += 1
            mism += y != shard_model(p, n, 192)
        first_move[p] = first
        mism += first != shard_move_index(p)
    lab.reset()
    b = new_crumble_object(lab, 7, 2160, 192, 1)
    rows = []
    for n in range(1, 14):
        lab.step_slot(7)
        r = lab.row(7)
        rows.append([n, r["state"], r["req"], r["frame"], r["x"], r["y"], r["vy"], r["p3f"]])
    # sleeping shard is removed by the callback before it moves
    for p in (1, 5, 9):
        lab.reset()
        b = new_crumble_object(lab, 7, 2160, 192, p)
        lab.step_slot(7)
        lab.step_slot(7)
        lab.m[b + 4] |= 0x40
        y_before = lab.o.word(b + 0x14)
        lab.step_slot(7)
        cases += 1
        mism += not (lab.m[b] == 0xFF and lab.o.word(b + 0x14) == y_before)
    return {"evidence": "CONTROLLED ROUTINE RESULT ($A2DD, $A31B and the engine's state-3 script executed) vs MODEL", "cases": cases, "mismatches": mism,
            "first_move_pass_equals_parameter_plus_2_for_parameters_1_to_255": all(first_move[p] == p + 2 for p in range(1, 256)),
            "rows_parameter_1_columns": ["pass", "state", "requested", "frame", "x", "y", "vy_8_8", "parameter_countdown"], "rows_parameter_1": rows,
            "model": "state 3 script sets velocity (0, +$0200) once; every pass: asleep (+$04 bit 6) -> type := $FF; else if parameter > 0: parameter -= 1; else vy += $0200 and Y += vy (integer part, "
                     "fraction stays 0): y_k = y0 + k(k+3) for the k-th move; X never changes; no terrain probe, no contact helper, no cap"}


def lifecycle_table(rom: bytes) -> list:
    base = file_of(0x1C, 0x8146)
    return ["".join(str(rom[base + r * 32 + c]) for c in range(32)) for r in range(32)]


def lifecycle_class(table: list, obj_x: int, obj_y: int, cam_x: int, cam_y: int) -> int:
    """Generic object lifecycle class from $61E1: 0/1 awake, 2 asleep (+$04 bit 6), 3 removed (also any position outside the 512 x 512 window)."""
    xp, yp = obj_x + 128 - cam_x, obj_y + 128 - cam_y
    if xp < 0 or yp < 0 or (xp >> 1) > 255 or (yp >> 1) > 255:
        return 3
    return int(table[yp >> 4][xp >> 4])


def lifecycle_check(rom: bytes) -> dict:
    """$61E1 against the decoded table and the class model, over every 1-pixel offset of the window plus margins."""
    lab = CrumbleLab(rom)
    table = lifecycle_table(rom)
    cases = mism = 0
    counts = {}
    cam_x, cam_y = 1000, 600
    for dxp in range(-8, 521):
        for dyp in range(-8, 521, 1 if dxp % 16 == 0 else 7):
            lab.reset()
            b = new_crumble_object(lab, 3, cam_x + dxp - 128, cam_y + dyp - 128, 0)
            lab.o.word(0xD174, cam_x)
            lab.o.word(0xD176, cam_y)
            lab.m[b + 4] = 0
            lab.m[b + 3] = 0
            lab.o.cpu.ix = b
            lab.o.call(0x61E1)
            asleep = bool(lab.m[b + 4] & 0x40)
            removed = lab.m[b] in (0xFE, 0xFF)
            cls = lifecycle_class(table, cam_x + dxp - 128, cam_y + dyp - 128, cam_x, cam_y)
            exp_asleep, exp_removed = cls >= 2, cls == 3
            cases += 1
            mism += (asleep != exp_asleep) or (removed != exp_removed)
            counts[cls] = counts.get(cls, 0) + 1
    # +$04 bit 1 keeps a class-3 object alive (asleep only)
    for cls_pos in ((cam_x - 400, cam_y), (cam_x + 128, cam_y - 300)):
        lab.reset()
        b = new_crumble_object(lab, 3, cls_pos[0], cls_pos[1], 0)
        lab.o.word(0xD174, cam_x)
        lab.o.word(0xD176, cam_y)
        lab.m[b + 4] = 0x02
        lab.o.cpu.ix = b
        lab.o.call(0x61E1)
        cases += 1
        mism += not (lab.m[b] == 0x13 and lab.m[b + 4] & 0x40)
    return {"evidence": "CONTROLLED ROUTINE RESULT ($61E1 executed) vs the decoded 32x32 table", "cases": cases, "mismatches": mism, "class_counts": {str(k): v for k, v in sorted(counts.items())},
            "table_rows_16px_cells": table, "index": "x' = objX + 128 - cameraX, y' = objY + 128 - cameraY (16-bit); outside 0..511 on either axis = class 3; cell = table[y' >> 4][x' >> 4]",
            "classes": {"0": "visible/awake core", "1": "awake margin", "2": "asleep: +$04 bit 6 set (object callbacks may remove themselves)", "3": "removed: bit 6 set and type := $FF (or $FE with a placement token) unless +$04 bit 1"}}


def object_timeline(rom: bytes, parent_slot: int = 0, pool_blocked: tuple = (), free_after_spawn: tuple = (), passes: int = 80, cell=(67, 6), player_f3: int = 0, player_state: int = 5) -> dict:
    """Spawn a crumble parent through the REAL handler and run the object passes until everything is gone.

    parent_slot: the parent lands in this slot (slots below are occupied by dummies); pool_blocked: slots (7..17) occupied by dummies when the children are created;
    free_after_spawn: dummies removed after the spawn (slots that become free before the break)."""
    lab = CrumbleLab(rom)
    cx, cy = cell
    lab.player(cx * CELL + 16, cy * CELL - 16, vy=0, f3=player_f3, state=player_state)
    lab.o.word(0xD518, 0x0100)
    lab.probe(cx, cy, cx * CELL + 16, cy * CELL + 2)
    fill_slots(lab, range(parent_slot))
    fill_slots(lab, pool_blocked)
    lab.handler()
    out = {"parent_slot": next(i for i in range(19) if lab.m[lab.slot(i)] == 0x13)}
    for i in free_after_spawn:
        lab.m[lab.slot(i)] = 0
    rows, events = [], []
    parent = out["parent_slot"]
    for n in range(1, passes + 1):
        lab.m[0xD521] = 0
        lab.o.word(0xD514, cy * CELL - 18)           # the terrain pass puts the player on the cell top before the object pass
        before = {i: lab.m[lab.slot(i)] for i in range(19)}
        for i in range(19):
            if lab.m[lab.slot(i)] == 0x13:
                lab.step_slot(i)
        live = [lab.row(i) for i in range(19) if lab.m[lab.slot(i)] == 0x13 or (lab.m[lab.slot(i)] and i not in pool_blocked and before.get(i, 0) == 0)]
        created = [i for i in range(19) if before[i] == 0 and lab.m[lab.slot(i)] == 0x13]
        if created:
            events.append({"pass": n, "children_created_slots": created, "parameters": [lab.m[lab.slot(i) + 0x3F] for i in created],
                           "positions": [[lab.o.word(lab.slot(i) + 0x11), lab.o.word(lab.slot(i) + 0x14)] for i in created]})
        if lab.cell(cx, cy) == CRUMBLE_REPLACEMENT and not any(e.get("replaced_pass") for e in events):
            events.append({"pass": n, "replaced_pass": n})
        rows.append({"pass": n, "player_y": lab.o.word(0xD514), "d521": lab.m[0xD521], "d518": lab.o.word(0xD518),
                     "slots": [[r["slot"], r["type"], r["state"], r["req"], r["y"], r["p3f"]] for r in live]})
        if not any(lab.m[lab.slot(i)] == 0x13 for i in range(19)):
            break
    out["events"] = events
    out["rows"] = rows
    out["passes"] = len(rows)
    out["cell_after"] = lab.cell(cx, cy)
    return out


# --- the original terrain pass on a decoded act layout ------------------------------
WATCH = {CRUMBLE_HANDLER: "h0c", BOOSTER_HANDLER: "h1a", 0x5EB7: "spawn", 0x48F7: "hurt", 0x753E: "ring_probe", 0x691A: "floor_pass"}


class FloorLab:
    """The original terrain pass $690B (floor $691A, sides, ceiling, ring probe, merge) or one of its parts on a decoded act layout, with every input explicit."""

    def __init__(self, rom: bytes, key: str):
        import isometric_platform as I
        self.lab = I.TerrainLab(rom, key)
        self.o, self.m = self.lab.o, self.lab.m
        self.width = I.act_data(rom, key)["width"]
        for a in WATCH:
            self.o.cpu.set_breakpoint(a)

    def _step_over(self, pc: int) -> None:
        cpu = self.o.cpu
        cpu.clear_breakpoint(pc)
        cpu.ticks_to_stop = 1
        cpu.run()
        cpu.set_breakpoint(pc)

    def go(self, x, y, vx=0, vy=0, floor=False, prev=0, cur=5, f3=None, k=0, p24=0, anim7=0, d3b1=0, entry=0x690B, patch=None, face=0, d3c0=0, req=None, d356=0, extent=(8, 24),
           d522=None, pre373=0) -> dict:
        self.m[0xC000:0xE000] = self.lab.base
        o, m = self.o, self.m
        for (cx, cy), blk in (patch or {}).items():
            m[0xC001 + cy * self.width + cx] = blk
        o.word(0xD511, x)
        o.word(0xD514, y)
        o.word(0xD516, vx & 0xFFFF)
        o.word(0xD518, vy & 0xFFFF)
        m[0xD501] = cur
        m[0xD502] = cur if req is None else req
        m[0xD503] = f3 if f3 is not None else (0 if floor else 1)
        m[0xD504] = 0x10 if face else 0
        m[0xD507] = anim7
        m[0xD522] = d522 if d522 is not None else (2 if floor else 0)
        m[0xD523] = 0
        m[0xD524] = p24
        m[0xD525] = 0
        m[0xD36C] = prev
        m[0xD36B] = 0
        m[0xD3C0] = d3c0
        m[0xD3BC] = k
        m[0xD3B1] = d3b1
        m[0xD52C], m[0xD52D] = extent
        m[0xD521] = 0
        m[0xDE04] = 0
        o.word(0xD356, d356)
        o.word(0xD373, pre373)
        for i in range(19):
            m[SLOT_BASE + i * SLOT_SIZE:SLOT_BASE + i * SLOT_SIZE + 8] = bytes(8)
        o.cpu.ix = PLAYER
        hits = []
        o.cpu.pc = entry
        o.cpu.bc = o.cpu.de = 0
        o.cpu.sp = 0xDFE0
        o.word(o.cpu.sp, o.RETURN)
        for _ in range(400):
            o.cpu.ticks_to_stop = 100000
            o.cpu.run()
            pc = o.cpu.pc
            if pc == o.RETURN:
                break
            if pc in WATCH:
                hits.append(WATCH[pc])
                if pc == 0x48F7:
                    o.cpu.pc = o.RETURN
                    break
                self._step_over(pc)
        else:
            raise RuntimeError("controlled pass did not return")
        objs = [i for i in range(19) if m[SLOT_BASE + i * SLOT_SIZE]]
        return {"hits": hits, "x": o.word(0xD511), "y": o.word(0xD514), "vx": s16(o.word(0xD516)), "vy": s16(o.word(0xD518)), "d518": o.word(0xD518), "floor": bool(m[0xD522] & 2),
                "d522": m[0xD522], "d523": m[0xD523], "d36c": m[0xD36C], "f3": m[0xD503], "req": m[0xD502], "d373": o.word(0xD373), "d516": o.word(0xD516), "snd": m[0xDE04],
                "d356": o.word(0xD356), "d354": o.word(0xD354), "block": m[0xD353], "flags": m[0xD364], "profile": m[0xD368], "objs": objs,
                "obj0": ({"type": m[SLOT_BASE + objs[0] * SLOT_SIZE], "x": o.word(SLOT_BASE + objs[0] * SLOT_SIZE + 0x11), "y": o.word(SLOT_BASE + objs[0] * SLOT_SIZE + 0x14)} if objs else None)}


# --- surface $0C floor trigger sweep (terrain pass on a decoded SEZ layout) -----------
STATE_FOOT_EXTRA = {0x21: -14, 0x12: 8}            # per-state foot offset in $691A (shared floor pass)
SWEEP_ACT = "sez1"
SWEEP_CELL = (67, 6)


def isolated_cell_patch(cx: int, cy: int, blk: int, radius: int = 4) -> dict:
    p = {(x, y): 0xFE for x in range(cx - radius, cx + radius + 1) for y in range(cy - radius, cy + radius + 1)}
    p[(cx, cy)] = blk
    return p


def crumble_trigger_sweep(rom: bytes) -> dict:
    """Original terrain pass with one isolated $AF cell: when does $6B79 run, and what do spawn / Y speed / remembered cell do?"""
    fl = FloorLab(rom, SWEEP_ACT)
    cx, cy = SWEEP_CELL
    patch = isolated_cell_patch(cx, cy, CRUMBLE_BLOCK)
    x0, y0 = cx * CELL, cy * CELL
    ptr = 0xC001 + cy * fl.width + cx
    cases = mism = 0
    reach_counts = {"reached_and_in_cell": 0, "not_reached_and_outside": 0}
    effect_counts = {}
    for st in (5, 0x21, 0x12):
        extra = STATE_FOOT_EXTRA.get(st, 0)
        for prev in (0, 0x4C, 0x82):
            for vy in (-0x100, 0, 0x100, 0x700):
                for floor in (False, True):
                    for dx in range(-12, 44, 3):
                        for r in range(-3, 36):
                            for d356 in (0, ptr):
                                ay = y0 + r - 18 - extra
                                res = fl.go(x0 + dx, ay, 0, vy, floor=floor, prev=prev, cur=st, patch=patch, d356=d356)
                                foot = ay + 18 + extra
                                in_cell = (x0 <= x0 + dx < x0 + CELL) and (y0 <= foot < y0 + CELL)
                                reached = "h0c" in res["hits"]
                                cases += 1
                                bad = reached != in_cell
                                if reached:
                                    spawn = bool(res["objs"])
                                    exp_spawn = vy >= 0 and d356 != ptr
                                    exp_zero = vy >= 0
                                    bad |= spawn != exp_spawn
                                    bad |= (res["d518"] == 0) != exp_zero if vy != 0 else (res["d518"] != 0)
                                    bad |= res["d356"] != (ptr if exp_spawn else d356)
                                    key = f"vy{'<0' if vy < 0 else '>=0'}_same_cell={d356 == ptr}"
                                    effect_counts[key] = effect_counts.get(key, 0) + 1
                                    reach_counts["reached_and_in_cell"] += 1
                                else:
                                    reach_counts["not_reached_and_outside"] += 1
                                    bad |= bool(res["objs"])
                                mism += bad
    # support projection table (what the SHARED one-way projection does with this block; identical rows to any bit-6-only block)
    table = {}
    for prev in (0, 0x4C, 0x82):
        for vy in (-0x100, 0, 0x100, 0x700):
            for floor in (False, True):
                row = []
                for r in range(-4, 36):
                    res = fl.go(x0 + 16, y0 + r - 18, 0, vy, floor=floor, prev=prev, cur=5, patch=patch, d356=ptr)
                    row.append(f"{res['y'] - (y0 + r - 18)}/{int(res['floor'])}")
                table[f"prev={prev:#04x},vy_8_8={vy},floor0={int(floor)}"] = row
    return {"evidence": "CONTROLLED ROUTINE RESULT ($690B executed on the SEZ1 layout with one isolated $AF cell) vs MODEL", "cases": cases, "mismatches": mism, "reach_counts": reach_counts,
            "effect_counts": effect_counts, "support_projection_table": {"columns_foot_row_minus4_to_35": list(range(-4, 36)), "cell_value": "dy_of_final_anchor_y/floor_flag", "rows": table},
            "model": "$6B79 runs iff the foot sample (anchor X, anchor Y + 18 + state extra) lies in an $AF cell (extra: state $21 -14, state $12 +8, else 0); player state, floor flag, previous-update "
                     "flags and Y speed do not gate the CALL; inside it: Y speed high byte bit 7 set -> return; else Y speed := 0 and, if the probed cell pointer != $D356, spawn and remember"}


# --------------------------------------------------------------------------- #
# 4. whole-game rig (approximate SMS harness booted into an act; one row per player update)
# --------------------------------------------------------------------------- #
_RIGS: dict = {}


def rig(rom: bytes, key: str):
    """Boot the ORIGINAL game into the act once (cached)."""
    if key not in _RIGS:
        import sez_surfaces_rig as G
        zone = next(i for i, n in enumerate(ZONE_NAMES) if key.startswith(n))
        _RIGS[key] = G.ZoneGame(rom, zone, int(key[len(ZONE_NAMES[zone]):]) - 1)
    return _RIGS[key]


def act_width(lays: dict, key: str) -> int:
    return lays[key]["width"]


def air_patch(cx: int, cy: int, blk: int = 0xFE) -> dict:
    """Fixture patch: the cell above and its neighbours (rows cy-3..cy-1, columns cx-2..cx+2) become air so only the $AF cell acts."""
    return {(x, y): blk for x in range(cx - 2, cx + 3) for y in range(cy - 3, cy)}


QUIET = {"terrain", "floorpass", "ringprobe"}
WINDOW = 58                                   # updates after the spawn that a cell summary covers (all shards are gone by about +37)


def evs(r: dict, keep=None) -> list:
    return [e for e in r["ev"] if e not in QUIET and (keep is None or e in keep)]


def compact_rows(rows: list, lo: int = 0, hi=None, with_objs: bool = False) -> list:
    out = []
    for r in rows[lo:hi]:
        row = [r["u"], r["x"], r["y"], r["vx"], r["vy"], r["cur"], r["req"], r["f22"], r["f3"], r["d521"], evs(r)]
        if with_objs:
            row.append([list(o[:2]) + list(o[2:]) for o in r.get("o", [])])
        out.append(row)
    return out


COMPACT_COLUMNS = ["update", "x", "y", "vx_8_8", "vy_8_8", "state", "requested", "floor_flags_d522", "movement_d503", "d521", "events"]


def first_u(rows: list, name: str, start: int = 0):
    return next((r["u"] for r in rows if r["u"] >= start and name in r["ev"]), None)


def all_u(rows: list, name: str) -> list:
    return [r["u"] for r in rows if name in r["ev"]]


def shard_tracks(rows: list, cell_x0: int, cell_y0: int) -> list:
    """Follow every shard (type $13 state 3 / parameter != 0) from creation: slot, X, parameter at creation, first-move update, sleep and removal updates."""
    tracks = {}
    for r in rows:
        seen = set()
        for (slot, typ, st, req, x, y, vy, p3f, f4) in r.get("o", []):
            seen.add(slot)
            if typ == 0x13 and cell_x0 <= x < cell_x0 + CELL and y >= cell_y0 and (slot not in tracks or tracks[slot]["gone"]):
                if slot not in tracks or tracks[slot]["gone"]:
                    if st in (0, 3) and (req == 3 or st == 3) and y == cell_y0:
                        tracks[slot] = {"slot": slot, "x": x, "x_offset": x - cell_x0, "created_u": r["u"], "p_at_creation": p3f, "y0": y, "first_move_u": None, "sleep_u": None, "removed_u": None,
                                        "gone": False, "ys": []}
            t = tracks.get(slot)
            if t and not t["gone"]:
                if typ == 0x13 and st == 3:
                    t["ys"].append([r["u"], y])
                    if t["first_move_u"] is None and y != t["y0"]:
                        t["first_move_u"] = r["u"]
                if f4 & 0x40 and t["sleep_u"] is None:
                    t["sleep_u"] = r["u"]
                if typ != 0x13:
                    t["removed_u"] = r["u"]
                    t["gone"] = True
        for slot, t in tracks.items():
            if not t["gone"] and slot not in seen:
                t["removed_u"] = r["u"]
                t["gone"] = True
    out = []
    for t in sorted(tracks.values(), key=lambda t: (t["x_offset"], t["created_u"])):
        t = dict(t)
        t.pop("gone")
        t["ys"] = t["ys"][:6]
        out.append(t)
    return out


def drop_on_cell(g, cx: int, cy: int, width: int = 128, frames: int = 110, air: bool = True, state: int = 0x0E, f3: int = 1, start_above: int = 20, pad=None, dx: int = 16,
                 invulnerable: bool = True) -> list:
    """Fixture: the player is invulnerable (+$03 bit 7, $D3B1 = 255) so that mapped hazards placed next to some cells (SEZ1 (65,14), (66,14)) cannot interfere."""
    g.begin(cx * CELL + dx, cy * CELL - 18 - start_above, 0, 0, cur=state, f3=f3 | (0x80 if invulnerable else 0), floor=False, prev=0, patch=air_patch(cx, cy) if air else None, width=width,
            d3b1=255 if invulnerable else None, types=(0x13,))
    return g.run(frames, padf=pad)


def crumble_cell_summary(rows: list, cx: int, cy: int) -> dict:
    """First crumble object of a drop onto cell (cx, cy): spawn, hold, break, child allocation, shards."""
    x0, y0 = cx * CELL, cy * CELL
    T = first_u(rows, "spawn13")
    out = {"spawn_update": T}
    if T is None:
        return out
    B = first_u(rows, "13break", T)
    rep = first_u(rows, "replace", T)
    Crm = first_u(rows, "13rm", B or T)
    rows = [r for r in rows if r["u"] <= T + WINDOW]         # the player keeps falling after the break and may touch the next cell; stop at the shard lifetime
    byu = {r["u"]: r for r in rows}
    riders = [u for u in all_u(rows, "13rider") if T < u < (B or T + 99)]
    alloc = [e for e in byu[Crm]["ev"] if e == "alloc11"] if Crm in byu else []
    sh = [s for s in shard_tracks(rows, x0, y0) if Crm is not None and s["created_u"] == Crm]
    out.update({"hold_updates_offsets": [u - T for u in riders], "hold_count": len(riders), "hold_first_offset": riders[0] - T if riders else None, "break_update": B,
                "break_offset": None if B is None else B - T, "replace_offset": None if rep is None else rep - T, "child_alloc_offset": None if Crm is None else Crm - T,
                "child_alloc_calls_in_that_update": len(alloc), "remove_callback_offset": None if Crm is None else Crm - T,
                "player_y_at_spawn_end": byu[T]["y"], "player_y_held": sorted({byu[u]["y"] for u in riders if u in byu}), "player_y_at_break_update": None if B is None else byu[B]["y"],
                "player_y_after_break": None if B is None else [byu[u]["y"] for u in range(B + 1, B + 5) if u in byu],
                "shards": [{k: v for k, v in s.items() if k not in ("ys", "created_u", "first_move_u", "sleep_u", "removed_u")} | {
                    "created_offset": s["created_u"] - T, "first_move_offset": None if s["first_move_u"] is None else s["first_move_u"] - T,
                    "sleep_offset": None if s["sleep_u"] is None else s["sleep_u"] - T, "removed_offset": None if s["removed_u"] is None else s["removed_u"] - T,
                    "first_ys": s["ys"][:4]} for s in sh]})
    return out


def timeline_signature(rows: list, cx: int, cy: int) -> dict:
    """Coordinate-free signature of the first crumble object: event offsets relative to the spawn update, player Y relative to the cell top (equal for every cell and zone)."""
    x0, y0 = cx * CELL, cy * CELL
    T = first_u(rows, "spawn13")
    B = first_u(rows, "13break", T)
    Crm = first_u(rows, "13rm", B)
    byu = {r["u"]: r for r in rows if r["u"] <= T + WINDOW}
    ev = []
    for u in range(T, T + 20):
        r = byu.get(u)
        if r is None:
            continue
        for e in evs(r, ("spawn13", "13s0", "13rider", "13break", "replace", "13rm")):
            ev.append([u - T, e])
    ys = [byu[T + k]["y"] - y0 for k in range(0, 24) if T + k in byu]
    sh = [[s["x_offset"], s["p_at_creation"], s["created_u"] - T, None if s["first_move_u"] is None else s["first_move_u"] - T]
          for s in shard_tracks(list(byu.values()), x0, y0) if s["created_u"] == Crm]
    return {"events_relative": ev, "player_y_minus_cell_top_T_to_T23": ys, "shards_x_offset_p_created_firstmove_relative": sh}

def cell_sweep(rom: bytes, lays: dict, keys=None) -> dict:
    """Standard drop onto EVERY $AF cell of every act (fixture: the 5 x 3 block above is patched to air): one summary per cell + coordinate-free signature equality."""
    keys = keys or [k for k, lay in lays.items() if any(b == CRUMBLE_BLOCK for b in lay["cells"])]
    cells_out, sigs = [], {}
    for key in keys:
        lay = lays[key]
        w = lay["width"]
        g = rig(rom, key)
        for i, b in enumerate(lay["cells"]):
            if b != CRUMBLE_BLOCK:
                continue
            cx, cy = i % w, i // w
            rows = drop_on_cell(g, cx, cy, w)
            summ = crumble_cell_summary(rows, cx, cy)
            sig = timeline_signature(rows, cx, cy)
            sigs.setdefault(sha_json(sig), []).append(f"{key}:{cx},{cy}")
            geo = cell_geometry(cx, cy)
            ok = (summ.get("hold_count") == 16 and summ.get("hold_first_offset") == 1 and summ.get("break_offset") == 17 and summ.get("child_alloc_offset") == 18
                  and summ.get("player_y_held") == [geo["hold_anchor_y"]] and g.cell(cx, cy, w) == CRUMBLE_REPLACEMENT)
            cells_out.append({"act": key, "cell": [cx, cy], "ok": bool(ok), "above_block": h(block_at(lay, cx, cy - 1), 2) if block_at(lay, cx, cy - 1) is not None else None,
                              "hold_anchor_y": geo["hold_anchor_y"], "summary": summ})
    return {"evidence": "EMULATED ORIGINAL FRAME (whole game booted into each act, drop onto the cell, first player update clean)", "cells": cells_out, "cell_count": len(cells_out),
            "all_ok": all(c["ok"] for c in cells_out), "distinct_signatures": len(sigs), "signature_classes": {k[:12]: v for k, v in sigs.items()}, "signature_example": None,
            "acts": keys}


# --- named whole-game scenarios for the crumble ledge ------------------------------
PAD_LEFT, PAD_RIGHT, PAD_B1 = 4, 8, 16


def scenario_walk_off(g) -> dict:
    """SEZ1 (28,10),(29,10): walk LEFT off a two-cell ledge.  The rider hold has no presence test: Sonic keeps his Y while walking out into the air."""
    g.begin(990, 302, -0x200, 0, cur=5, f3=0, floor=True, prev=0x82, face=1, types=(0x13,), d3b1=255)
    rows = g.run(60, padf=lambda u, f: PAD_LEFT)
    cell_left_x = 28 * CELL
    spawn = all_u(rows, "spawn13")
    hover = [r["u"] for r in rows if r["x"] < cell_left_x and r["y"] == 304]
    first_fall = next((r["u"] for r in rows if r["u"] > (hover[-1] if hover else 0) and r["y"] > 304), None)
    return {"start": {"x": 990, "y": 302, "vx_8_8": -0x200, "state": "0x05", "input": "LEFT held"}, "spawn_updates": spawn, "break_updates": all_u(rows, "13break"),
            "hover_updates_left_of_both_cells_with_floor_flag": hover, "hover_count": len(hover), "first_free_fall_update": first_fall, "held_anchor_y": 304,
            "x_when_hover_ends": next((r["x"] for r in rows if hover and r["u"] == hover[-1]), None), "rows_columns": COMPACT_COLUMNS, "rows": compact_rows(rows, 8, 46)}


def scenario_strip_run(g) -> dict:
    """SEZ1 (62..67,14): run RIGHT across a six-cell bridge at 4 px/update."""
    g.begin(1940, 430, 0x200, 0, cur=5, f3=0, floor=True, prev=0x82, types=(0x13,), d3b1=255)
    rows = g.run(110, padf=lambda u, f: PAD_RIGHT)
    spawn = [(r["u"], r["x"]) for r in rows if "spawn13" in r["ev"]]
    brk = all_u(rows, "replace")
    cells = {cx: g.cell(cx, 14) for cx in range(60, 70)}
    return {"start": {"x": 1940, "y": 430, "vx_8_8": 0x200, "input": "RIGHT held"}, "spawns_u_x": spawn, "replace_updates": brk, "spawn_to_replace": [b - s for (s, _), b in zip(spawn, brk)],
            "cells_60_to_69_after": {str(k): h(v, 2) for k, v in cells.items()}, "player_y_values_before_update_100": sorted({r["y"] for r in rows if r["u"] < 100}),
            "rows_columns": COMPACT_COLUMNS, "rows": compact_rows(rows, 14, 50)}


def scenario_jump_up_through(g) -> dict:
    """SEZ1 (67,6) from below: a rising player passes through the one-way cell; the handler runs but does nothing while Y speed is negative."""
    g.begin(2160, 250, 0, -0x600, cur=0x0A, f3=1, floor=False, prev=0, types=(0x13,), d3b1=255)
    rows = g.run(70)
    byu = {r["u"]: r for r in rows}
    h0c = [r["u"] for r in rows if "h0c" in r["ev"]]
    rising = [u for u in h0c if byu[u]["vy"] < 0]
    first_spawn = first_u(rows, "spawn13")
    return {"start": {"x": 2160, "y": 250, "vy_8_8": -0x600, "state": "0x0A", "f3": 1}, "handler_calls_while_rising": len(rising), "handler_calls_while_rising_first_last": [rising[0], rising[-1]] if rising else None,
            "spawns_while_rising": [u for u in all_u(rows, "spawn13") if byu[u]["vy"] < 0], "first_spawn_update": first_spawn, "y_speed_before_spawn_update": byu[first_spawn - 1]["vy"] if first_spawn else None,
            "y_speed_at_spawn_update": byu[first_spawn]["vy"] if first_spawn else None, "rows_columns": COMPACT_COLUMNS, "rows": compact_rows(rows, 6, 50)}


def scenario_revisit_same_cell(g) -> dict:
    """Drop on (67,6), jump (B1) during the hold and land on the SAME cell again: the remembered cell ($D356) suppresses a second object."""
    g.begin(2160, 120, 0, 0, cur=0x0E, f3=0x81, floor=False, prev=0, types=(0x13,), d3b1=255)
    rows = g.run(70, padf=lambda u, f: PAD_B1 if 22 <= u <= 24 else 0)
    return {"spawn_updates": all_u(rows, "spawn13"), "replace_updates": all_u(rows, "replace"), "jump_press_updates": [22, 23, 24], "handler_calls": len(all_u(rows, "h0c")),
            "second_object_created": len(all_u(rows, "spawn13")) > 1, "state_trace_u_state_f3_y_vy": [[r["u"], r["cur"], r["f3"], r["y"], r["vy"]] for r in rows[20:50]],
            "rows_columns": COMPACT_COLUMNS, "rows": compact_rows(rows, 14, 60)}


def scenario_a_b_a(g) -> dict:
    """SEZ1 strip: touch A (62,14), step to B (63,14) before A breaks, return to A: D356 changed, so A spawns a SECOND object; both replace the same cell."""
    g.begin(62 * CELL + 16, 14 * CELL - 18 - 2, 0, 0, cur=0x0E, f3=0x81, floor=False, prev=0, types=(0x13,), d3b1=255)

    def hook(gm, f):
        n = len(gm.rows)
        if n == 6:
            gm.s.w16(0xD511, 63 * CELL + 16)
        elif n == 10:
            gm.s.w16(0xD511, 62 * CELL + 16)
    rows = g.run(48, hook=hook)
    return {"sequence": "A at update 1, X teleport to B after update 6, back to A after update 10 (writes on update boundaries)", "spawn_updates": all_u(rows, "spawn13"),
            "replace_updates": all_u(rows, "replace"), "d356_by_update": {str(u): rows[u - 1]["d356"] for u in (3, 8, 12)},
            "cell_pointers": {"A": 0xC001 + 14 * 128 + 62, "B": 0xC001 + 14 * 128 + 63}, "cells_after": {"62": h(g.cell(62, 14), 2), "63": h(g.cell(63, 14), 2)},
            "rows_columns": COMPACT_COLUMNS, "rows": compact_rows(rows, 0, 40)}


def scenario_strip_speed_sweep(g) -> dict:
    """SEZ1 bridge (62..67,14) run at 4.0 / 5.0 / 6.0 / 7.0 px/update (max X speed forced to $0700 so 7.0 is reachable): how close does the camera get to the objects' X at their break callbacks?"""
    out = {}
    for vx in (0x400, 0x500, 0x600, 0x700):
        g.begin(1900, 430, vx, 0, cur=6, f3=0, floor=True, prev=0x82, types=(0x13,), d3b1=255, apply=lambda gm: gm.s.w16(0xD373, 0x0700))
        rows = g.run(80, padf=lambda u, f: PAD_RIGHT)
        spawns = [(r["u"], r["x"]) for r in rows if "spawn13" in r["ev"]]
        breaks = [(r["u"], r["d174"]) for r in rows if "13break" in r["ev"]]
        margins = [62 * CELL + 14 + CELL * i - cam for i, (_, cam) in enumerate(breaks)]
        out[f"{vx / 256:.1f}_px_per_update"] = {"spawns_u_x": spawns, "break_updates": [u for u, _ in breaks], "camera_x_at_break": [c for _, c in breaks], "object_x_minus_camera_x_at_break": margins,
                                               "cells_replaced": sum(1 for cx in range(62, 68) if g.cell(cx, 14) == CRUMBLE_REPLACEMENT)}
    return {"evidence": "EMULATED ORIGINAL FRAME", "per_speed": out, "minimum_margin": min(min(v["object_x_minus_camera_x_at_break"]) for v in out.values()),
            "reading": "the removal branch needs objectX < cameraX; the smallest margin seen is positive for every cell at every speed up to 7.0 px/update"}

def scenario_removed_by_camera(g) -> dict:
    """The crumble object is removed instead of breaking when its X is left of camera X at the break callback: the cell stays $AF, $D356 still remembers it."""
    def pre(mm):
        mm.w16(0xD174, mm.u16(mm.cpu.ix + 0x11) + 1)
    g.pre[0xA36A] = pre
    g.begin(2160, 120, 0, 0, cur=0x0E, f3=0x81, floor=False, prev=0, types=(0x13,), d3b1=255)
    rows = g.run(50)
    del g.pre[0xA36A]
    stand = [r for r in rows if r["u"] > 36]
    return {"fixture": "camera X forced to objectX+1 inside the break callback ($A36A)", "spawn_updates": all_u(rows, "spawn13"), "replace_events": all_u(rows, "replace"),
            "remove_callbacks_a33f": all_u(rows, "13rm"), "live_crumble_objects_at_end": len([o for o in rows[-1]["o"] if o[1] == 0x13]), "cell_after_removal": h(g.cell(67, 6), 2), "d356_after": rows[-1]["d356"], "cell_pointer": 0xC001 + 6 * 128 + 67,
            "player_y_f22_while_standing_on_intact_cell": [stand[0]["y"], stand[-1]["y"], stand[-1]["f22"]], "handler_calls_after_removal": len([1 for r in stand if "h0c" in r["ev"]]),
            "new_objects_after_removal": len([1 for r in stand if "spawn13" in r["ev"]])}


def scenario_removed_asleep(g) -> dict:
    def pre(mm):
        mm.mem[mm.cpu.ix + 4] |= 0x40
    g.pre[0xA36A] = pre
    g.begin(2160, 120, 0, 0, cur=0x0E, f3=0x81, floor=False, prev=0, types=(0x13,), d3b1=255)
    rows = g.run(50)
    del g.pre[0xA36A]
    return {"fixture": "+$04 bit 6 forced inside the break callback ($A36A)", "spawn_updates": all_u(rows, "spawn13"), "replace_events": all_u(rows, "replace"),
            "cell_after": h(g.cell(67, 6), 2), "remove_callbacks_a33f": all_u(rows, "13rm"), "live_crumble_objects_at_end": len([o for o in rows[-1]["o"] if o[1] == 0x13])}


def scenario_full_pool(g) -> dict:
    """All 16 slots of the positioned-spawn pool occupied: no object, no hold, no break; Sonic stands on the intact one-way cell; $D356 follows."""
    saved = {}

    def fill(mm):
        saved.clear()
        for i in range(16):
            b = SLOT_BASE + i * SLOT_SIZE
            saved[i] = mm.mem[b]
            if mm.mem[b] == 0:
                mm.mem[b] = 0x0F

    def unfill(mm):
        for i in range(16):
            if saved.get(i) == 0:
                mm.mem[SLOT_BASE + i * SLOT_SIZE] = 0

    def at_ret(mm):
        saved["after"] = (mm.mem[0xD970], mm.mem[0xD971], mm.cpu.iy)
    g.hook(0x6B9A, fill)
    g.hook(0x6B9D, unfill)
    g.hook(0x6BA9, at_ret)
    try:
        g.begin(2160, 120, 0, 0, cur=0x0E, f3=0x81, floor=False, prev=0, types=(0x13,), d3b1=255)
        rows = g.run(60)
    finally:
        for a in (0x6B9A, 0x6B9D, 0x6BA9):
            g.s.pc_hooks.pop(a, None)
            g.s.cpu.clear_breakpoint(a)
    first = next(r for r in rows if "h0c" in r["ev"])
    return {"fixture": "dummy objects occupy the free slots 0..15 only for the duration of the $5EB7 call", "spawn_calls_logged_at_5eb7_entry": all_u(rows, "spawn13"), "replace_events": all_u(rows, "replace"),
            "first_handler_update": first["u"], "player_y_after": [r["y"] for r in rows[first["u"]:first["u"] + 8]], "y_speed_after": sorted({r["vy"] for r in rows[first["u"]:]}),
            "d356_after": rows[-1]["d356"], "cell_pointer": 0xC001 + 6 * 128 + 67, "cell_after": h(g.cell(67, 6), 2),
            "slot16_bytes_30_31_after_failed_spawn": list(saved.get("after", (0, 0, 0))[:2]), "iy_after_failed_spawn": saved.get("after", (0, 0, 0))[2],
            "rows_columns": COMPACT_COLUMNS, "rows": compact_rows(rows, 20, 32)}


def name_table_cell_words(g, cx: int, cy: int) -> list:
    """The 4 x 4 name-table words the VDP currently holds for a cell (tile column = 4*cx + i modulo 32, row = 4*cy + j modulo 28)."""
    base = (g.s.reg[2] & 0x0E) << 10
    out = []
    for j in range(4):
        for i in range(4):
            tx, ty = (cx * 4 + i) % 32, (cy * 4 + j) % 28
            a = base + (ty * 32 + tx) * 2
            out.append(g.s.vram[a] | g.s.vram[a + 1] << 8)
    return out


def scenario_hold_ordering(g) -> dict:
    """Y of the player at the START of the object pass (after that update's terrain pass) versus at the end of the update, during the hold."""
    seen = {}
    g.hook(0x5DD1, lambda mm: seen.__setitem__(len(g.rows) + 1, mm.u16(0xD514)))
    try:
        g.begin(2160, 120, 0, 0, cur=0x0E, f3=0x81, floor=False, prev=0, types=(0x13,), d3b1=255)
        rows = g.run(45)
    finally:
        g.s.pc_hooks.pop(0x5DD1, None)
        g.s.cpu.clear_breakpoint(0x5DD1)
    T = first_u(rows, "spawn13")
    pairs = [[r["u"] - T, seen.get(r["u"]), r["y"]] for r in rows if T - 1 <= r["u"] <= T + 19]
    return {"columns": ["update_minus_spawn", "y_after_terrain_pass_before_object_pass", "y_at_end_of_update"], "rows": pairs}

def scenario_persistence(g, rom: bytes) -> dict:
    """After the break the layout RAM cell stays $B0 (the VDP name table was redrawn blank at the break).  Teleporting the player + camera far away and back leaves it $B0 and
    creates no new crumble object."""
    g.begin(2160, 120, 0, 0, cur=0x0E, f3=0x81, floor=False, prev=0, types=(0x13,), d3b1=255)
    state = {"phase": 0}

    def hook(gm, f):
        n = len(gm.rows)
        if n == 46 and "words" not in state:
            state["words"] = ([w & 0x1FF for w in name_table_cell_words(gm, 67, 6)], [w & 0x1FF for w in name_table_cell_words(gm, 68, 6)])
        if n == 50 and state["phase"] == 0:
            gm.e._place(gm.s, 3000, 700, 0, 0)
            state["phase"] = 1
            state["away_cell"] = gm.cell(67, 6)
        elif n == 80 and state["phase"] == 1:
            gm.e._place(gm.s, 2160, 215, 0, 0)
            state["phase"] = 2
    rows = g.run(110, hook=hook)
    d = L.build_descriptor(rom, "x", {"zone": ZONE, "act": 0, "name": "x"})
    b0_tiles = [x & 0x1FF for x in L.block_mapping(rom, d["header"]["block_mapping_rom"], CRUMBLE_REPLACEMENT)["attributes"]]
    broken, intact = state["words"]
    return {"fixture": "player + camera teleported to (3000,700) after update 50 and back to (2160,215) after update 80 (writes on update boundaries); "
                       "the name table is read right after the break (update 46) because the harness teleport does not run the game's incremental scroll redraw",
            "spawns": all_u(rows, "spawn13"), "replace_updates": all_u(rows, "replace"), "cell_while_far_away": h(state.get("away_cell", 0), 2), "cell_after_return": h(g.cell(67, 6), 2),
            "new_crumble_objects_after_return": len([u for u in all_u(rows, "spawn13") if u > 80]), "name_table_tile_numbers_broken_cell_67_6_at_update_46": broken,
            "name_table_tile_numbers_intact_af_cell_68_6_at_update_46": intact, "block_b0_mapping_tile_numbers": b0_tiles, "broken_cell_matches_b0_mapping": broken == b0_tiles,
            "intact_af_neighbour_differs_from_b0": intact != b0_tiles}


def scenario_restart_restores(g) -> dict:
    """Death and act restart: $297E runs, the layout is reloaded ($AF cells return) and $D356 is zero."""
    log = []
    g.hook(0x297E, lambda mm: log.append(len(g.rows)))
    g.begin(2160, 120, 0, 0, cur=0x0E, f3=0x81, floor=False, prev=0, types=(0x13,), d3b1=255)

    def hook(gm, f):
        if len(gm.rows) == 60 and "killed" not in state:
            state["killed"] = len(gm.rows)
            state["cell_before_death"] = gm.cell(67, 6)
            state["d356_before_death"] = gm.s.u16(0xD356)
            gm.s.w16(0xD514, gm.s.u16(0xD176) + 0xE8)          # below the screen: ordinary vertical death rule
            gm.m[0xD503] &= 0x7F
    state = {}
    rows = g.run(260, hook=hook)
    g.s.pc_hooks.pop(0x297E, None)
    g.s.cpu.clear_breakpoint(0x297E)
    return {"fixture": "player written below the screen at update 60 (vertical death), then the game's own death / restart sequence", "cell_before_death": h(state["cell_before_death"], 2),
            "d356_before_death": state["d356_before_death"], "level_clear_297e_called_at_update": log, "cell_after_restart": h(g.cell(67, 6), 2), "d356_after_restart": g.s.u16(0xD356),
            "player_after_restart": [rows[-1]["x"], rows[-1]["y"]]}


def state_scan(g, mode: str) -> dict:
    """First player update with each state 0..$36 forced (script pointer cleared so the engine loads that state's own callback): which shared terrain routines run?"""
    out = {}
    for st in range(0x37):
        if mode == "crumble":
            g.begin(2160, 176, 0, 0, cur=st, f3=0, floor=False, prev=0)
        else:
            g.begin(1360, 558, 0, 0x700, cur=st, f3=0, floor=True, prev=0x82)
        rows = g.run(1)
        ev = set(rows[0]["ev"]) if rows else set()
        eff = ("spawn13" in ev) if mode == "crumble" else bool(rows and "h1a" in ev and rows[0]["d373"] == 0x700 and rows[0]["req"] == 0x10)
        out[h(st, 2)] = {"terrain_pass": "terrain" in ev, "floor_pass": "floorpass" in ev, "ring_probe": "ringprobe" in ev, "handler": ("h0c" if mode == "crumble" else "h1a") in ev,
                         "effect_applied": eff, "state_after": h(rows[0]["cur"], 2) if rows else None, "requested_after": h(rows[0]["req"], 2) if rows else None}
    key = "handler"
    return {"mode": mode, "evidence": "EMULATED ORIGINAL FRAME (first player update with the state forced)", "per_state": out,
            "effect_applied_states": [k for k, v in out.items() if v["effect_applied"]],
            "handler_reached_states": [k for k, v in out.items() if v[key]], "handler_not_reached_states": [k for k, v in out.items() if not v[key]],
            "terrain_pass_states": [k for k, v in out.items() if v["terrain_pass"]], "ring_probe_states": [k for k, v in out.items() if v["ring_probe"]],
            "floor_pass_states": [k for k, v in out.items() if v["floor_pass"]]}


def contact_scan(rom: bytes) -> dict:
    """Type $13 has no contact: no CALL/JP to a contact helper vector inside its callbacks, and a whole-game drop with the player under the falling shards logs zero contact calls."""
    from z80dis import z80
    contact_vectors = {0x033B, 0x0434, 0x0323, 0x0431 + 0, 0x6328, 0x630B, 0x5FA0, 0x5F3D, 0x5F54, 0x48F7, 0x48BC, 0x033E}
    hits, pos = [], 0xA2DD
    base = file_of(0x0C, 0xA2DD)
    while pos < 0xA3AF:
        d = z80.decode(rom[file_of(0x0C, pos):file_of(0x0C, pos) + 4], pos)
        txt = z80.disasm(d)
        if txt.upper().startswith(("CALL", "JP")):
            parts = txt.replace(",", " ").split()
            try:
                tgt = int(parts[-1], 0)
            except ValueError:
                tgt = None
            if tgt in contact_vectors:
                hits.append({"cpu": h(pos), "text": txt})
        pos += d.len
    calls = sorted({int(t["text"].split()[-1], 0) for r in (disasm(rom, 0x0C, 0xA2DD, 0xA3AF),) for t in r if t["text"].upper().startswith("CALL") and t["text"].split()[-1].startswith("0x")})
    return {"evidence": "BYTE-VERIFIED ASSEMBLY (every CALL/JP in $A2DD..$A3AE)", "contact_helper_calls_found": hits, "all_call_targets": [h(c) for c in calls],
            "reading": "the only calls are the integrator vector $0338, the cell replacement vector $0428 ; there is no overlap helper, no attack gate, no damage entry"}


# --------------------------------------------------------------------------- #
# 5. surface $1A / block $A7 (booster pad)
# --------------------------------------------------------------------------- #
BOOST_ACT = "sez2"
BOOST_CELL = (42, 17)                          # SEZ2: ground row 18 ($08) directly below


def booster_handler_matrix(rom: bytes) -> dict:
    """$7646 for every +$22 value and every +$03 value: effect iff +$22 bit 1 (the floor flag).  Pre-set X speed, max speed, requested state and sound request are all overwritten."""
    fl = FloorLab(rom, BOOST_ACT)
    cases = mism = 0
    effect = {}
    for d522 in range(256):
        for f3 in range(256):
            res = fl.go(1000, 500, 0x1234, 0x0555, floor=False, prev=0, cur=5, f3=f3, entry=BOOSTER_HANDLER, req=0x07, d522=d522, pre373=0x0222)
            applied = res["d516"] == 0x0700 and res["d373"] == 0x0700 and res["req"] == 0x10 and res["snd"] == 0xBD and res["f3"] == ((f3 | 2) & 0xFE)
            untouched = res["d516"] == 0x1234 and res["d373"] == 0x0222 and res["req"] == 0x07 and res["snd"] == 0 and res["f3"] == f3
            keeps = res["d522"] == d522 and res["d518"] == 0x0555 and res["x"] == 1000 and res["y"] == 500
            exp = bool(d522 & 2)
            cases += 1
            mism += (applied != exp) or (untouched == exp) or not keeps
            effect[exp] = effect.get(exp, 0) + 1
    return {"evidence": "CONTROLLED ROUTINE RESULT ($7646 executed) vs MODEL", "cases": cases, "mismatches": mism, "effect_counts": {str(k): v for k, v in effect.items()},
            "rule": "iff +$22 bit 1 (floor flag) is set: $D516 := $0700 (X speed +7.0, unconditional: sign and previous value are ignored), $D373 := $0700 (max X speed), +$03 := (+$03 | $02) & $FE "
                    "(attack posture ON, jump latch bit 0 cleared), requested state +$02 := $10, sound request $DE04 := $BD; otherwise nothing at all.  Y speed, facing (+$04 bit 4), "
                    "position and every other byte are untouched"}


def booster_probe_sweep(rom: bytes) -> dict:
    """The ring probe $753E on an isolated $A7 cell: it dispatches $1A iff the probe sample lies in the cell.  Probe = (anchor X, anchor Y - 8) for an even +$07 bit 0 and "
    (anchor X, anchor Y + 2) for an odd one (lookup adds 18 to the -26 / -16 offset); the effect additionally needs the floor flag."""
    fl = FloorLab(rom, BOOST_ACT)
    cx, cy = BOOST_CELL
    patch = isolated_cell_patch(cx, cy, BOOSTER_BLOCK)
    x0, y0 = cx * CELL, cy * CELL
    cases = mism = 0
    reached_in = reached_out = 0
    eff = 0
    for anim7 in (0, 1):
        for floor in (False, True):
            for ax in range(x0 - 14, x0 + CELL + 14):
                for ay in range(y0 - 24, y0 + CELL + 24):
                    res = fl.go(ax, ay, 0, 0, floor=floor, prev=0x82, cur=5, anim7=anim7, entry=RING_PROBE, patch=patch)
                    py = ay - 8 if not anim7 else ay + 2
                    inside = x0 <= ax < x0 + CELL and y0 <= py < y0 + CELL
                    reached = "h1a" in res["hits"]
                    effect = res["d516"] == 0x0700 and res["req"] == 0x10
                    cases += 1
                    mism += (reached != inside) or (effect != (inside and floor))
                    reached_in += reached and inside
                    reached_out += reached and not inside
                    eff += effect
    return {"evidence": "CONTROLLED ROUTINE RESULT ($753E executed on the SEZ2 layout with one isolated $A7 cell) vs MODEL", "cases": cases, "mismatches": mism,
            "reached_inside": reached_in, "reached_outside": reached_out, "effect_cases": eff, "grid": {"anchor_x": [x0 - 14, x0 + CELL + 13], "anchor_y": [y0 - 24, y0 + CELL + 23], "anim7_bit0": [0, 1], "floor_flag": [0, 1]},
            "model": "probe = (anchor X, anchor Y - 8) if (+$07 & 1) == 0 else (anchor X, anchor Y + 2); handler runs iff the probe's cell is $A7; effect iff additionally the floor flag is set"}


def block_a7_support(rom: bytes) -> dict:
    """The block is SOLID with a 0..2 px bump: the shared solid-floor projection against its vertical profile (surface $1A has a bare RET as floor handler)."""
    fl = FloorLab(rom, BOOST_ACT)
    cx, cy = BOOST_CELL
    patch = isolated_cell_patch(cx, cy, BOOSTER_BLOCK)
    x0, y0 = cx * CELL, cy * CELL
    prof = R.header(rom, BOOSTER_BLOCK)["vertical"]
    cases = mism = 0
    rows = {}
    for dx in range(CELL):
        row = []
        for r in range(0, CELL):
            res = fl.go(x0 + dx, y0 + r - 18, 0, 0x100, floor=False, prev=0x9A, cur=5, patch=patch)
            top = y0 + (CELL - prof[dx])
            foot = y0 + r
            exp_y = top - 18 if (prof[dx] > 0 and foot >= top) else y0 + r - 18
            cases += 1
            mism += res["y"] != exp_y
            row.append(res["y"] - (y0 + r - 18))
        rows[str(dx)] = row if dx in (0, 7, 8, 11, 12, 19, 20, 23, 24, 31) else None
    return {"evidence": "CONTROLLED ROUTINE RESULT ($690B floor projection vs the block's vertical profile) vs MODEL", "cases": cases, "mismatches": mism,
            "vertical_profile_runs": [[a, b, v] for a, b, v in runs_of(prof)], "sample_dy_by_foot_row_for_x": {k: v for k, v in rows.items() if v is not None},
            "reading": "support height = cell top + 32 - profile (0, 1 or 2 px above the cell bottom); the pad does not change the player's height in any meaningful way, and the floor handler for surface $1A does nothing"}


def runs_of(profile) -> list:
    out, start = [], 0
    for i in range(1, len(profile) + 1):
        if i == len(profile) or profile[i] != profile[start]:
            out.append((start, i - 1, profile[start]))
            start = i
    return out



# --- whole-game booster scenarios ------------------------------------------------------
def booster_rows_summary(rows: list, x0: int) -> dict:
    fires = [(r["u"], r["x"]) for r in rows if "h1a" in r["ev"]]
    first = fires[0][0] if fires else None
    byu = {r["u"]: r for r in rows}
    out = {"handler_updates": [u for u, _ in fires], "handler_x_at_end_of_update": [x for _, x in fires], "handler_count": len(fires)}
    if first:
        a = byu[first]
        out.update({"first_handler_update": first, "x_at_first_handler": a["x"] - x0, "state_after_first": h(a["cur"], 2), "requested_after_first": h(a["req"], 2), "vx_after_first": a["vx"],
                    "d373_after_first": a["d373"], "d503_after_first": a["f3"], "state_next_update": h(byu[first + 1]["cur"], 2) if first + 1 in byu else None,
                    "x_offsets_from_cell_left_at_each_handler_update": [x - x0 for _, x in fires], "vx_from_first_to_first_plus_8": [byu[u]["vx"] for u in range(first, first + 9) if u in byu]})
    return out


def booster_run(g, cx: int, cy: int, width: int, side: str = "left", vx: int = 0x200, frames: int = 40, state: int = 5, f3: int = 0, face=None, pad=None, dist: int = 24, ground_dy: int = 1,
                with_pad_input: bool = True, extra: dict = None) -> list:
    x0 = cx * CELL
    anchor_y = (cy + ground_dy) * CELL - 18
    if side == "left":
        x, vxx, pd = x0 - dist, vx, PAD_RIGHT
    elif side == "right":
        x, vxx, pd = x0 + CELL - 1 + dist, -vx, PAD_LEFT
    else:
        x, vxx, pd = x0 + CELL // 2, vx, 0
    kw = dict(extra or {})
    g.begin(x, anchor_y, vxx, 0, cur=state, f3=f3, floor=True, prev=0x82, face=(0 if side != "right" else 1) if face is None else face, types=(0x13,), d3b1=255, width=width, **kw)
    return g.run(frames, padf=pad if pad is not None else ((lambda u, f: pd) if with_pad_input else None))


def booster_cell_sweep(rom: bytes, lays: dict) -> dict:
    """Walk onto EVERY $A7 cell of every act from the left at 2 px/update (ground = the row below the cell) and from the right; coordinate-free signature equality."""
    out, sigs = [], {}
    for key, lay in lays.items():
        cells = [(i % lay["width"], i // lay["width"]) for i, b in enumerate(lay["cells"]) if b == BOOSTER_BLOCK]
        if not cells:
            continue
        g = rig(rom, key)
        w = lay["width"]
        for cx, cy in cells:
            res = {"act": key, "cell": [cx, cy], "world": [cx * CELL, cy * CELL], "below_block": h(block_at(lay, cx, cy + 1), 2)}
            for side in ("left", "right"):
                rows = booster_run(g, cx, cy, w, side=side, frames=26)
                summ = booster_rows_summary(rows, cx * CELL)
                res[side] = summ
            res["ok_left"] = bool(res["left"].get("handler_count")) and res["left"].get("state_after_first") is not None
            sig_l = {k: res["left"].get(k) for k in ("handler_count", "requested_after_first", "vx_after_first", "d373_after_first", "d503_after_first", "vx_from_first_to_first_plus_8")}
            xs = res["left"].get("x_offsets_from_cell_left_at_each_handler_update") or []
            sig_l["x_steps_between_handler_updates"] = [b - a for a, b in zip(xs, xs[1:])]
            sig_l["first_x_offset_in_0_or_1"] = bool(xs) and xs[0] in (0, 1)
            first_l = res["left"].get("first_handler_update")
            sig_l["relative_updates"] = [u - first_l for u in res["left"].get("handler_updates", [])] if first_l else None
            sigs.setdefault(sha_json(sig_l), []).append(f"{key}:{cx},{cy}")
            out.append(res)
    return {"evidence": "EMULATED ORIGINAL FRAME (whole game booted into each act, standing walk onto the cell)", "cells": out, "cell_count": len(out),
            "all_left_ok": all(c["ok_left"] for c in out), "distinct_left_signatures": len(sigs), "signature_classes": {k[:12]: v for k, v in sigs.items()}}


def scenario_booster_speed_table(g, cx=42, cy=17, width=128) -> dict:
    """Entry speed vs number of handler updates (the 32 px column is re-triggered every update the probe is inside it)."""
    table = {}
    for vx in (0, 0x80, 0x100, 0x200, 0x300, 0x400, 0x500, 0x600, 0x700, -0x100, -0x400, -0x700):
        side = "left" if vx >= 0 else "right"
        rows = booster_run(g, cx, cy, width, side=side, vx=abs(vx), frames=40, pad=lambda u, f: PAD_RIGHT if vx >= 0 else PAD_LEFT, dist=24)
        s = booster_rows_summary(rows, cx * CELL)
        table[str(vx)] = {"handler_count": s["handler_count"], "x_offsets": s.get("x_offsets_from_cell_left_at_each_handler_update"), "vx_after_first": s.get("vx_after_first")}
    standing = booster_run(g, cx, cy, width, side="center", frames=20)
    return {"entry_x_speed_8_8_to_result": table, "standing_start_center": booster_rows_summary(standing, cx * CELL)}


def scenario_booster_input_scripts(g, cx=84, cy=24, width=128) -> dict:
    """After the launch (standing start in the column of SEZ2 (84,24); flat ground continues right for 44 updates) with different inputs: state $10 persistence, skid, jump."""
    scripts = {"none": lambda u, f: 0, "right": lambda u, f: PAD_RIGHT, "left": lambda u, f: PAD_LEFT, "down": lambda u, f: 2, "up": lambda u, f: 1,
               "jump_press_u3_to_u5": lambda u, f: PAD_B1 if 3 <= u <= 5 else 0, "right_and_jump_u6": lambda u, f: PAD_RIGHT | (PAD_B1 if 6 <= u <= 8 else 0)}
    out = {}
    for name, pf in scripts.items():
        rows = booster_run(g, cx, cy, width, side="center", frames=44, pad=pf)
        trans, prev = [], None
        for r in rows:
            if r["cur"] != prev:
                trans.append([r["u"], h(r["cur"], 2), r["vx"], r["x"], r["y"], r["f3"], r["face"]])
                prev = r["cur"]
        out[name] = {"state_transitions_u_state_vx_x_y_f3_face": trans[:8], "vx_at_updates": {str(u): rows[u - 1]["vx"] for u in (1, 4, 10, 20, 40) if u <= len(rows)},
                     "d373_at_updates": {str(u): rows[u - 1]["d373"] for u in (1, 10, 20, 40) if u <= len(rows)}, "x_at_44": rows[-1]["x"], "handler_updates": all_u(rows, "h1a")}
    return out


def scenario_state10_exit(g, cx=84, cy=24) -> dict:
    """State $10 at low speed on flat ground (SEZ2 row 25): the exit rule of the shared callback ($37F4) with different inputs."""
    out = {}
    for name, pad in (("none", 0), ("down", 2), ("right", PAD_RIGHT), ("left", PAD_LEFT)):
        g.begin((cx + 2) * CELL, (cy + 1) * CELL - 18, 0x30, 0, cur=0x10, f3=2, floor=True, prev=0x82, types=(0x13,), d3b1=255)
        rows = g.run(14, padf=lambda u, f, pad=pad: pad)
        out[name] = [[r["u"], r["vx"], h(r["cur"], 2), h(r["req"], 2)] for r in rows[:10]]
    return {"start": "state $10, X speed +$0030, floor flag set, flat ground", "columns": ["update", "x_speed_8_8", "state", "requested"], "per_input": out,
            "rule": "$37F4: opposing direction held -> skid state $07 / $08; else if |X speed| >= $10 stay; else requested state $04 (DOWN held) or $01"}


def scenario_booster_bridge(g) -> dict:
    """SEZ2: the pad at (42,17) leads onto the four-cell crumble bridge (44..47,18): Sonic arrives at 7 px/update, every cell breaks 17 updates after its own first contact, nobody falls."""
    rows = booster_run(g, 42, 17, 128, side="left", frames=70, dist=64)
    spawn = [(r["u"], r["x"]) for r in rows if "spawn13" in r["ev"]]
    rep = all_u(rows, "replace")
    return {"approach": "from x = 1280 (64 px before the pad) at 2 px/update, RIGHT held", "handler_updates": all_u(rows, "h1a"), "crumble_spawns_u_x": spawn, "replace_updates": rep,
            "spawn_to_replace": [b - s for (s, _), b in zip(spawn, rep)], "cells_44_to_47_after": {str(cx): h(g.cell(cx, 18), 2) for cx in range(44, 48)},
            "player_y_range_during_bridge": sorted({r["y"] for r in rows if 44 * CELL - 8 <= r["x"] <= 48 * CELL + 8}), "min_state_during": sorted({h(r["cur"], 2) for r in rows}),
            "x_at_end": rows[-1]["x"], "never_fell_below_y": max(r["y"] for r in rows), "rows_columns": COMPACT_COLUMNS, "rows": compact_rows(rows, 28, 62)}



def scenario_booster_footwear(g, cx=42, cy=17, width=128) -> dict:
    """Rocket Shoes ($11) and Spring Shoes ($12) in the pad column, probe parity forced each update at the probe: the effect needs the floor flag AT THE PROBE."""
    out = {}
    for st in (0x11, 0x12, 0x14, 0x15):
        for parity in (0, 1):
            seen = []

            def pre(mm, parity=parity, seen=seen):
                mm.mem[0xD507] = (mm.mem[0xD507] & 0xFE) | parity
                seen.append(mm.mem[0xD522] & 2)
            g.pre[RING_PROBE] = pre
            kw = dict(d532=4, apply=lambda gm: gm.s.w16(0xD44C, 300)) if st == 0x11 else {}       # Rocket Shoes: selector 4 + 300-update timer
            try:
                g.begin(cx * CELL + 16, (cy + 1) * CELL - 18, 0, 0x700 if st != 0x11 else 0, cur=st, f3=0, floor=True, prev=0x82, types=(0x13,), d3b1=255, **kw)
                rows = g.run(10)
            finally:
                g.pre.pop(RING_PROBE, None)
            fires = [r["u"] for r in rows if "h1a" in r["ev"]]
            launched = [r["u"] for r in rows if r["req"] == 0x10 and r["d373"] == 0x700]
            out[f"state_{st:02X}_probe_parity_{parity}"] = {"probe_updates": len(seen), "floor_flag_at_probe_per_update": seen[:10], "handler_updates": fires, "launched_updates": launched,
                                                          "states_seen": sorted({h(r["cur"], 2) for r in rows}), "y_first_5": [r["y"] for r in rows[:5]],
                                                          "d532_after": rows[-1]["d532"], "state_sequence_first_6": [h(r["cur"], 2) for r in rows[:6]]}
    out["notes"] = ("$11 = real Rocket Shoes setup (selector $D532 = 4, timer $D44C = 300): the first handler update replaces the rocket state by $10 (the selector and timer are NOT cleared by the "
                    "handler); $12 = Spring Shoes state forced WITHOUT the $2F shoe object: it is rising after its own relaunch, so the floor flag is clear at the probe and the handler does nothing "
                    "(parity 1 shows a launch only because the first update still has the floor flag); end-to-end Spring Shoes with a real shoe object on a pad is UNRESOLVED (no pad is near a shoe)")
    return out


def effect5_timeline(rom: bytes) -> dict:
    """Level effect 5 ($1D:$81BF): every 3rd call alternate 32 bytes to VRAM $2B00 (tile $158); paused while $D44E != 0; gated by the effect dispatcher ($D492 == 0)."""
    import sez_surfaces_rig as G
    log = {"calls": [], "copies": [], "clear": [], "engine": 0}
    boot = {0x297E: lambda mm: log["clear"].append(mm.frame),
            0x81BF: lambda mm: log["calls"].append((mm.frame, mm.mem[0xD44E], mm.mem[0xD455], mm.mem[0xD454], mm.mem[0xD12F], mm.mem[0xD492])),
            0x820B: lambda mm: log["copies"].append(("0x8DDD", mm.frame, mm.mem[0xD12F])), 0x8218: lambda mm: log["copies"].append(("0x8DFD", mm.frame, mm.mem[0xD12F])),
            0x64FA: lambda mm: log.__setitem__("engine", log["engine"] + (1 if mm.cpu.ix == 0xD500 else 0))}
    g = G.ZoneGame(rom, ZONE, 1, boot_hooks=boot)
    first_call = log["calls"][0] if log["calls"] else None
    n0 = len(log["calls"])
    eng0 = log["engine"]
    for _ in range(60):
        g.s.pad = 0
        g.s.run_frame()
    calls60, eng60 = len(log["calls"]) - n0, log["engine"] - eng0
    img = {k: rom[file_of(0x1D, a):file_of(0x1D, a) + 32] for k, a in (("0x8DDD", 0x8DDD), ("0x8DFD", 0x8DFD))}
    vram = bytes(g.s.vram[0x2B00:0x2B20])
    which = next((k for k, v in img.items() if v == vram), None)
    seq = [c[0] for c in log["copies"]][:12]
    # pause: boss flag $D44E set -> no copies; cleared -> resumes
    c0 = len(log["copies"])
    g.m[0xD44E] = 1
    for _ in range(30):
        g.s.run_frame()
    paused_copies = len(log["copies"]) - c0
    g.m[0xD44E] = 0
    c1 = len(log["copies"])
    for _ in range(30):
        g.s.run_frame()
    resumed_copies = len(log["copies"]) - c1
    deltas = [b[1] - a[1] for a, b in zip(log["copies"], log["copies"][1:])]
    return {"evidence": "EMULATED ORIGINAL FRAME (SEZ2 boot with PC hooks on the effect-5 routine and its two copy routines) + BYTE-VERIFIED ASSEMBLY", "vram_destination": "0x2B00", "tile": "0x158",
            "sources": {"0x8DDD": {"bank": "0x1D", "file": h(file_of(0x1D, 0x8DDD), 5), "sha256": sha(img["0x8DDD"])}, "0x8DFD": {"bank": "0x1D", "file": h(file_of(0x1D, 0x8DFD), 5), "sha256": sha(img["0x8DFD"])}},
            "level_clear_frame": log["clear"][-1] if log["clear"] else None, "first_effect_call_frame": first_call[0] if first_call else None,
            "first_calls_counter_phase_d455_d454": [[c[2], c[3]] for c in log["calls"][:7]], "copy_sequence_first_12": seq, "copy_period_calls_between_copies": sorted(set(deltas)),
            "effect_calls_in_60_frames": calls60, "player_engine_passes_in_60_frames": eng60, "vram_image_after_run": which,
            "paused_while_d44e_nonzero_copies_in_30_frames": paused_copies, "resumed_after_clear_copies_in_30_frames": resumed_copies,
            "rule": "the dispatcher ($1D:$8000) calls the effect once per game-loop iteration while $D492 == 0; effect 5 returns at once if $D44E != 0, else increments the call counter (+3); at 3 it "
                    "resets to 0, toggles the phase (+2: 0 -> 1 -> 0) and copies 32 bytes: first copy (3rd call after the effect starts) = $8DFD, then $8DDD, alternating every 3 calls (period 6)"}


def booster_art_facts(rom: bytes) -> dict:
    """Which tiles of block $A7 are the animated tile $158; the block image for both effect frames is hashed (no pixels committed)."""
    import sez_art_approval as S
    import mghz_art_approval as AA
    import mghz_foundation as MF
    import sez_object_census as C
    a2 = C.vram_for_act(rom, 1)
    base, ring, strip = S.effect_variants(rom, a2, MF.ring_art_descriptor(rom, ZONE, 1))
    d = L.build_descriptor(rom, "x", {"zone": ZONE, "act": 1, "name": "x"})
    attrs = L.block_mapping(rom, d["header"]["block_mapping_rom"], BOOSTER_BLOCK)["attributes"]
    tiles = [a & 0x1FF for a in attrs]
    uses = [i for i, t in enumerate(tiles) if t == 0x158]
    images = []
    for v in strip:
        m = AA.block_maps(rom, a2, v, {BOOSTER_BLOCK})[BOOSTER_BLOCK]
        images.append(sha_json(m))
    af_attrs = [a & 0x1FF for a in L.block_mapping(rom, d["header"]["block_mapping_rom"], CRUMBLE_BLOCK)["attributes"]]
    blocks_using = []
    for b in range(256):
        t = [a & 0x1FF for a in L.block_mapping(rom, d["header"]["block_mapping_rom"], b)["attributes"]]
        if 0x158 in t:
            blocks_using.append(h(b, 2))
    return {"evidence": "DECODED DATA (block mapping $A7 in the SEZ2 mapping table) + EMULATED RENDER (hashes only)", "block": "0xA7", "mapping_tile_numbers_4x4_row_major": tiles,
            "positions_of_tile_0x158_row_major_index": uses, "tile_0x158_use_count": len(uses), "blocks_that_draw_tile_0x158_in_sez2": blocks_using,
            "block_image_sha256_by_effect_frame": {"0x8DDD": images[0], "0x8DFD": images[1]}, "images_differ": images[0] != images[1],
            "crumble_block_af_tile_numbers": af_attrs, "af_uses_tile_0x158": 0x158 in af_attrs,
            "reading": "block $A7 is a static pad drawing plus four copies of the animated tile $158 (the only art that changes); the two frames alternate every 3 effect calls.  The composed art has two "
                       "symmetric roller-like pieces and no arrow or other directional glyph: the art gives no evidence for a direction (the code is intrinsically rightward)"}



# --------------------------------------------------------------------------- #
# 6. cross-cutting facts
# --------------------------------------------------------------------------- #
def zone_gate_scan(rom: bytes) -> dict:
    """No routine of either mechanic reads the zone byte $D297 (nor the act byte $D298): the runtime is global, only data (block ids, art) differs by zone."""
    names = ("crumble_handler_6b79", "booster_handler_7646", "ring_probe_753e", "type13_callbacks", "spawn_positioned_5eb7", "spawn_11_slot_5ee1", "script_command4_671f", "cell_replace_6c1f",
             "object_visibility_61e1", "state_10_callback_3a23", "floor_pass_691a", "effect5_81bf")
    out = {}
    for n, b, a, e, p in REGIONS:
        if n not in names:
            continue
        o0, o1 = file_of(b, a), file_of(b, e)
        out[n] = {"reads_d297_zone": [h(a + i - 1) for i in range(1, o1 - o0 - 1) if rom[o0 + i] == 0x97 and rom[o0 + i + 1] == 0xD2 and rom[o0 + i - 1] in (0x3A, 0x32, 0x21, 0xED)],
                  "reads_d298_act": [h(a + i - 1) for i in range(1, o1 - o0 - 1) if rom[o0 + i] == 0x98 and rom[o0 + i + 1] == 0xD2 and rom[o0 + i - 1] in (0x3A, 0x32, 0x21, 0xED)]}
    return {"evidence": "BYTE-VERIFIED ASSEMBLY (operand scan of every routine region)", "regions": out,
            "zone_dependent_regions": [n for n, v in out.items() if v["reads_d297_zone"] or v["reads_d298_act"]],
            "known_zone_tables_touching_these_mechanics": {"effect5_81bf": "indexes its image table by the zone ($81E0: LD A,($D297)): SEZ uses entries 4/5 = $8DDD/$8DFD; other zones copy to $2E20/$3020 or return"}}


def update_order_trace(rom: bytes) -> dict:
    """The order in which the original game loop runs the pieces, observed with PC hooks over three loop iterations."""
    import sez_surfaces_rig as G
    g = G.ZoneGame(rom, ZONE, 1)
    log = []
    g.s.add_pc_hook(0x5DD1, lambda mm: log.append("object_scheduler_5dd1"))
    g.s.add_pc_hook(0x5E91, lambda mm: log.append("callback_player" if mm.cpu.ix == 0xD500 else "callback_object"))
    g.pre[0x690B] = lambda mm: log.append("terrain_pass_690b")
    g.pre[0x691A] = lambda mm: log.append("floor_pass_691a")
    g.pre[0x753E] = lambda mm: log.append("ring_probe_753e")
    g.hook(0x0606, lambda mm: log.append("frame_wait_0606"))
    orig = g._engine_hook

    def eng(mm):
        if mm.cpu.ix == 0xD500:
            log.append("player_engine_64fa")
        orig(mm)
    g.s.add_pc_hook(0x64FA, eng)
    g.begin(1360, 558, 0, 0x700, cur=5, f3=0, floor=True, prev=0x82)
    log.clear()
    for _ in range(4):
        g.s.run_frame()
    first = log.index("player_engine_64fa")
    seq = log[first:]
    # compress consecutive duplicates of object callbacks
    comp = []
    for x in seq:
        if comp and comp[-1] == x and x == "callback_object":
            continue
        comp.append(x)
    second = comp.index("player_engine_64fa", 1) if comp.count("player_engine_64fa") > 1 else len(comp)
    return {"evidence": "EMULATED ORIGINAL FRAME (PC hooks on the engine entry, callbacks, terrain pass, ring probe and scheduler)", "one_loop_iteration": comp[:second],
            "reading": "player engine -> player callback (movement, terrain pass: floor pass incl. $6B79, sides, ceiling, ring probe incl. $7646, merge; damage gate) -> object scheduler ($D521 := 0, "
                       "slots 0..18 ascending: crumble objects, shards, rider hold) -> wait for the frame.  The rider hold therefore overwrites the player's Y AFTER that update's terrain pass, "
                       "and its $D521 bit 1 is merged by the NEXT update's terrain pass"}


def pool_experiments(rom: bytes) -> dict:
    """The two spawn pools: the 16-slot positioned spawn (parent) and the 11-slot command-4 allocator (shards), and the one-update delay for children allocated below the parent."""
    out = {"children_with_k_free_slots_in_7_to_17": {}}
    for free in (11, 5, 4, 3, 2, 1, 0):
        blocked = tuple(range(7, 18))[:11 - free]
        r = object_timeline(rom, pool_blocked=blocked, passes=24)
        ev = [e for e in r["events"] if "children_created_slots" in e]
        out["children_with_k_free_slots_in_7_to_17"][str(free)] = {"children_slots": ev[0]["children_created_slots"] if ev else [], "parameters": ev[0]["parameters"] if ev else [],
                                                                   "creation_pass": ev[0]["pass"] if ev else None}
    low = object_timeline(rom, parent_slot=10, free_after_spawn=(7, 8, 9), passes=30)
    hi = object_timeline(rom, parent_slot=0, passes=30)

    def first_states(r, slot):
        res = []
        for row in r["rows"]:
            for s in row["slots"]:
                if s[0] == slot:
                    res.append([row["pass"], s[2], s[3], s[5]])
        return res[:5]
    out["child_below_parent_one_update_later"] = {"parent_slot": low["parent_slot"], "child_slot_7_rows_pass_state_requested_parameter": first_states(low, 7), "child_slot_11_above_parent_rows": first_states(low, 11),
                                                  "reference_parent_slot_0_child_slot_7_rows": first_states(hi, 7)}
    out["reading"] = ("slots 7..17 are shared with every other command-4 / badnik allocation: a busy screen creates fewer shards (the first k of the four in the order offsets 0, 8, 16, 24 with "
                      "parameters 3, 8, 5, 1).  A child created in a slot BELOW its parent's runs its state-0 callback one pass later (the scheduler already passed that slot), so its whole shard "
                      "timeline is one update later.  Shards are cosmetic: nothing reads them")
    return out



def crumble_posture_independence(rom: bytes) -> dict:
    """The handler never reads the player's movement byte +$03 (attack posture, jump latch, blink) or the state: identical effects for every +$03 value and many states."""
    fl = FloorLab(rom, SWEEP_ACT)
    cx, cy = SWEEP_CELL
    patch = isolated_cell_patch(cx, cy, CRUMBLE_BLOCK)
    x0, y0 = cx * CELL, cy * CELL
    ptr = 0xC001 + cy * fl.width + cx
    ref = None
    cases = mism = 0
    for st in (1, 5, 6, 9, 0x0A, 0x0E, 0x0F, 0x10, 0x11, 0x14, 0x15, 0x1A):
        for f3 in range(256):
            res = fl.go(x0 + 10, y0 + 2 - 18, 0, 0x100, floor=False, prev=0, cur=st, f3=f3, patch=patch)
            key = (bool(res["objs"]), res["d518"], res["d356"], "h0c" in res["hits"])
            ref = ref or key
            cases += 1
            mism += key != ref
    return {"evidence": "CONTROLLED ROUTINE RESULT ($690B executed)", "cases": cases, "mismatches": mism, "effect": {"spawned": ref[0], "d518_after": ref[1], "d356_is_cell_pointer": ref[2] == ptr, "handler_reached": ref[3]}}


def side_ceiling_sweeps(rom: bytes) -> dict:
    """Side pass ($715E) and ceiling pass ($73C9) of the original terrain code against an isolated cell: $AF and $A7 versus a one-way reference ($0D) and an ordinary solid block ($01)."""
    fl = FloorLab(rom, SWEEP_ACT)
    cx, cy = SWEEP_CELL
    x0, y0 = cx * CELL, cy * CELL
    out = {}
    for blk, name in ((CRUMBLE_BLOCK, "0xAF"), (BOOSTER_BLOCK, "0xA7"), (0x0D, "0x0D_one_way_reference"), (0x01, "0x01_solid_reference")):
        patch = isolated_cell_patch(cx, cy, blk)
        side_pushed = ceil_hit = ceil_moved = cases = 0
        for dy in range(-30, 40, 2):
            for dx in range(-24, 56):
                for vx in (0x100, -0x100):
                    r = fl.go(x0 + dx, y0 + dy, vx, 0, floor=False, prev=0, cur=0x0A, patch=patch, entry=0x715E)
                    cases += 1
                    side_pushed += (r["x"] != x0 + dx) or bool(r["d523"] & 0xC0)
        for dy in range(-30, 60, 2):
            for dx in range(-24, 56, 2):
                r = fl.go(x0 + dx, y0 + dy, 0, -0x100, floor=False, prev=0, cur=0x0A, patch=patch, entry=0x73C9)
                cases += 1
                ceil_hit += bool(r["d522"] & 1)
                ceil_moved += r["y"] != y0 + dy
        out[name] = {"cases": cases, "side_pass_pushes_or_flags": side_pushed, "ceiling_pass_sets_ceiling_flag": ceil_hit, "ceiling_pass_moves_player": ceil_moved}
    return {"evidence": "CONTROLLED ROUTINE RESULT ($715E and $73C9 executed)", "per_block": out,
            "reading": "$AF behaves like the one-way reference in the side and ceiling passes: no wall, no ceiling (a rising player passes through); the horizontal profile byte $60 is not a wall.  "
                       "$A7 (solid flag, surface $1A, horizontal profile $40): see the counts; the side pass never treats it as a wall and the ceiling pass has no handler for surface $1A"}


# --------------------------------------------------------------------------- #
# 7. assembly
# --------------------------------------------------------------------------- #
def booster_placements(rom: bytes, lays: dict, cells_report: dict) -> list:
    out = []
    ref = {(c["act"], tuple(c["cell"])): c for c in cells_report["cells"]}
    for key, lay in lays.items():
        for i, b in enumerate(lay["cells"]):
            if b != BOOSTER_BLOCK:
                continue
            cx, cy = i % lay["width"], i // lay["width"]
            c = ref.get((key, (cx, cy)), {})
            ground = (cy + 1) * CELL - 18
            out.append({"act": key, "cell": [cx, cy], "world_rect_xywh": [cx * CELL, cy * CELL, CELL, CELL], "trigger_anchor_x": [cx * CELL, cx * CELL + CELL - 1],
                        "trigger_anchor_y_even_parity": [cy * CELL + 8, cy * CELL + CELL + 7], "trigger_anchor_y_odd_parity": [cy * CELL - 2, cy * CELL + CELL - 3],
                        "ground_block_below": h(block_at(lay, cx, cy + 1), 2) if block_at(lay, cx, cy + 1) is not None else None, "standing_anchor_y_on_flat_ground_below": ground,
                        "neighbours": {k: (None if block_at(lay, cx + dx, cy + dy) is None else h(block_at(lay, cx + dx, cy + dy), 2)) for k, (dx, dy) in
                                       {"left": (-1, 0), "right": (1, 0), "above": (0, -1), "below": (0, 1), "left2": (-2, 0), "right2": (2, 0)}.items()},
                        "walk_from_left_handler_x_offsets": c.get("left", {}).get("x_offsets_from_cell_left_at_each_handler_update"),
                        "walk_from_right_handler_x_offsets": c.get("right", {}).get("x_offsets_from_cell_left_at_each_handler_update")})
    return out


def whole_game_crumble(rom: bytes, lays: dict) -> dict:
    g1, g2 = rig(rom, "sez1"), rig(rom, "sez2")
    first = drop_on_cell(g1, 67, 6, 128)
    return {"cell_sweep": cell_sweep(rom, lays), "drop_sez1_67_6": {"summary": crumble_cell_summary(first, 67, 6), "signature": timeline_signature(first, 67, 6),
                                                                      "rows_columns": COMPACT_COLUMNS, "rows": compact_rows(first, 8, 62, with_objs=True)},
            "walk_off_ledge": scenario_walk_off(g1), "strip_run": scenario_strip_run(g1), "jump_up_through": scenario_jump_up_through(g1), "revisit_same_cell": scenario_revisit_same_cell(g1),
            "a_b_a": scenario_a_b_a(g1), "strip_speed_sweep": scenario_strip_speed_sweep(g1), "removed_by_camera": scenario_removed_by_camera(g1), "removed_asleep": scenario_removed_asleep(g1), "full_pool": scenario_full_pool(g1),
            "persistence": scenario_persistence(g1, rom), "restart_restores": scenario_restart_restores(g1), "state_scan": state_scan(g1, "crumble"), "hold_ordering": scenario_hold_ordering(g1)}


def whole_game_booster(rom: bytes, lays: dict) -> dict:
    g = rig(rom, "sez2")
    cells = booster_cell_sweep(rom, lays)
    return {"cell_sweep": cells, "placements": booster_placements(rom, lays, cells), "speed_table": scenario_booster_speed_table(g), "input_scripts": scenario_booster_input_scripts(g),
            "state10_exit": scenario_state10_exit(g), "bridge": scenario_booster_bridge(g), "footwear": scenario_booster_footwear(g), "state_scan": state_scan(g, "booster"), "effect5": effect5_timeline(rom),
            "art": booster_art_facts(rom)}


def count_cases(d, acc=None) -> int:
    """Total of every integer 'cases' field in the tree (the controlled sweeps)."""
    total = 0
    if isinstance(d, dict):
        for k, v in d.items():
            if k == "cases" and isinstance(v, int):
                total += v
            else:
                total += count_cases(v)
    elif isinstance(d, list):
        for v in d:
            total += count_cases(v)
    return total


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    lays = all_layouts(rom)
    data = {"format": "sez-surfaces-0c-1a-v1", "rom_sha256": sha(rom), "research_base": RESEARCH_BASE, "research_only": True, "poc_untouched": True,
            "scope": {"in": ["surface $0C / block $AF / dynamic type $13 (crumble ledge)", "surface $1A / block $A7 (booster pad) and the effect-5 animation of its art"],
                      "out": ["$28/$86", "$20/$23", "$54/$55", "monitor repair", "parked presentation defects"]},
            "evidence_classes": ["DECODED DATA", "BYTE-VERIFIED ASSEMBLY", "SOURCE-TRACED BEHAVIOR", "CONTROLLED ROUTINE RESULT", "EMULATED ORIGINAL FRAME", "MODEL", "UNRESOLVED"],
            "static": static_facts(rom), "zone_gate_scan": zone_gate_scan(rom), "contact_scan": contact_scan(rom), "census": census(rom, lays),
            "crumble_runs": {k: crumble_runs(l) for k, l in lays.items() if any(b == CRUMBLE_BLOCK for b in l["cells"])}, "static_only": static_only}
    if static_only:
        return data
    crumble = {"trigger_sweep": crumble_trigger_sweep(rom), "posture_independence": crumble_posture_independence(rom), "side_ceiling": side_ceiling_sweeps(rom),
               "handler_matrix": handler_matrix(rom), "init_matrix": init_matrix(rom), "rider_matrix": rider_matrix(rom), "break_matrix": break_matrix(rom), "shard_matrix": shard_matrix(rom),
               "lifecycle": lifecycle_check(rom), "pools": pool_experiments(rom), "object_timeline_reference": {k: v for k, v in object_timeline(rom).items() if k != "rows"},
               "update_order": update_order_trace(rom), "whole_game": whole_game_crumble(rom, lays)}
    booster = {"handler_matrix": booster_handler_matrix(rom), "probe_sweep": booster_probe_sweep(rom), "a7_support": block_a7_support(rom), "whole_game": whole_game_booster(rom, lays)}
    sweeps = [crumble["trigger_sweep"], crumble["posture_independence"], crumble["side_ceiling"], crumble["handler_matrix"], crumble["init_matrix"], crumble["rider_matrix"], crumble["break_matrix"],
              crumble["shard_matrix"], crumble["lifecycle"], booster["handler_matrix"], booster["probe_sweep"], booster["a7_support"]]
    controlled_cases = sum(s["cases"] if "cases" in s else count_cases(s) for s in sweeps)
    mismatches = sum(s.get("mismatches", 0) for s in sweeps)
    wg_c, wg_b = crumble["whole_game"], booster["whole_game"]
    assert mismatches == 0, "a controlled sweep disagrees with its model"
    assert wg_c["cell_sweep"]["all_ok"] and wg_c["cell_sweep"]["distinct_signatures"] == 1, "crumble cells are not all identical"
    assert wg_b["cell_sweep"]["all_left_ok"] and wg_b["cell_sweep"]["distinct_left_signatures"] == 1, "booster cells are not all identical"
    data.update({"crumble": crumble, "booster": booster,
                 "counts": {"controlled_cases_total": controlled_cases, "controlled_mismatches": mismatches, "crumble_cells_driven_whole_game": wg_c["cell_sweep"]["cell_count"],
                            "booster_cells_driven_whole_game": wg_b["cell_sweep"]["cell_count"],
                            "whole_game_scenarios": len(wg_c) + len([k for k in wg_b if k not in ("placements", "art")]) + 1}})
    data["contracts_sha256"] = sha_json(make_contracts(rom, data, lays))
    return data



# --------------------------------------------------------------------------- #
# 8. oracle vectors (original-routine inputs -> outputs, directly usable as POC unit tests)
# --------------------------------------------------------------------------- #
def table_vectors(rom: bytes) -> dict:
    lab = CrumbleLab(rom)
    cx, cy = 67, 6
    ptr = lab.ptr(cx, cy)
    vec = {"crumble_handler_6b79": [], "crumble_rider_a344": [], "crumble_break_a36a": [], "crumble_init_a2dd": [], "crumble_shard_schedule": [], "booster_handler_7646": [], "booster_probe_753e": [],
           "crumble_trigger_floor_pass": []}
    for d519 in (0x00, 0x01, 0x7F, 0x80, 0xFF):
        for same in (False, True):
            for occ in ((), (0, 1, 2), tuple(range(16))):
                lab.reset()
                lab.player(2160, 176, vy=(d519 << 8) | 0x34)
                lab.probe(cx, cy, 2160, 194)
                lab.o.word(0xD356, ptr if same else ptr - 1)
                fill_slots(lab, occ)
                post = lab.handler()
                spawned = next((i for i in range(19) if i not in occ and lab.m[lab.slot(i)]), None)
                vec["crumble_handler_6b79"].append({"input": {"y_speed_high_byte_d519": d519, "remembered_cell_equals_probed_cell": same, "occupied_slots_0_15": list(occ), "probe_xy": [2160, 194], "cell_pointer": ptr},
                                                    "expect": {"y_speed_8_8": post["d518"], "remembered_cell_after": post["d356"], "spawned_slot": spawned,
                                                               "spawned_xy": None if spawned is None else [lab.o.word(lab.slot(spawned) + 0x11), lab.o.word(lab.slot(spawned) + 0x14)]}})
    for st in (0x05, 0x06, 0x09, 0x0A, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x14, 0x1A):
        for f3 in (0x00, 0x01, 0x02, 0x03, 0x80, 0x81):
            vec["crumble_rider_a344"].append({"input": {"player_state_d501": st, "movement_d503": f3}, "expect": {"hold_applied": rider_model(st, f3), "player_y": 216 - 40 if rider_model(st, f3) else "unchanged",
                                                                                                                  "y_speed": 0 if rider_model(st, f3) else "unchanged", "d521_bit1_set": rider_model(st, f3)}})
    for f4 in (0x00, 0x40, 0x02, 0x42):
        for dcam in (-2, -1, 0, 1, 2):
            vec["crumble_break_a36a"].append({"input": {"object_flags_04": f4, "camera_x_minus_object_x": -dcam, "object_x": 2158}, "expect": {"outcome": break_model(f4, 2158, 2158 - dcam)}})
    for (x, y) in ((2160, 194), (2144, 192), (2175, 223), (0x0834, 0x01C7), (5, 5)):
        vec["crumble_init_a2dd"].append({"input": {"parameter": 0, "probed_x": x, "probed_y": y}, "expect": {"requested_state": 1, "x": (x & 0xFFE0) + 14, "y": (y & 0xFFE0) + 24, "cell_x_raw": x, "cell_y_raw": y}})
    vec["crumble_init_a2dd"].append({"input": {"parameter": 3, "probed_x": 2144, "probed_y": 192}, "expect": {"requested_state": 3, "x": 2144, "y": 192}})
    for p in (1, 3, 5, 8, 20):
        vec["crumble_shard_schedule"].append({"input": {"parameter": p, "y0": 192}, "expect": {"first_move_pass": p + 2, "y_after_each_pass_1_to_16": [shard_model(p, n, 192) for n in range(1, 17)]}})
    fl = FloorLab(rom, BOOST_ACT)
    for d522 in (0x00, 0x01, 0x02, 0x03, 0x82, 0xFF):
        res = fl.go(1000, 500, 0x1234, 0x0555, floor=False, prev=0, cur=5, f3=0x01, entry=BOOSTER_HANDLER, req=0x07, d522=d522, pre373=0x0222)
        vec["booster_handler_7646"].append({"input": {"floor_flags_d522": d522, "movement_d503": 1, "x_speed_8_8": 0x1234, "max_x_speed_d373": 0x222, "requested_state": 7, "y_speed_8_8": 0x555},
                                            "expect": {"x_speed_8_8": res["d516"], "max_x_speed_d373": res["d373"], "requested_state": res["req"], "movement_d503": res["f3"], "sound_request_de04": res["snd"],
                                                       "y_speed_8_8": res["d518"], "position_unchanged": [res["x"], res["y"]] == [1000, 500]}})
    cx2, cy2 = BOOST_CELL
    patch = isolated_cell_patch(cx2, cy2, BOOSTER_BLOCK)
    x0, y0 = cx2 * CELL, cy2 * CELL
    for (dx, dy, anim7, floor) in ((-1, 14, 0, True), (0, 14, 0, True), (31, 14, 0, True), (32, 14, 0, True), (16, 14, 0, False), (16, 7, 0, True), (16, 8, 0, True), (16, 39, 0, True), (16, 40, 0, True),
                                   (16, -3, 1, True), (16, -2, 1, True), (16, 29, 1, True), (16, 30, 1, True), (16, 14, 1, True)):
        res = fl.go(x0 + dx, y0 + dy, 0, 0, floor=floor, prev=0x82, cur=5, anim7=anim7, entry=RING_PROBE, patch=patch)
        vec["booster_probe_753e"].append({"input": {"cell": [cx2, cy2], "anchor_x_minus_cell_left": dx, "anchor_y_minus_cell_top": dy, "anim_counter_bit0_plus07": anim7, "floor_flag": floor},
                                          "expect": {"handler_reached": "h1a" in res["hits"], "launched": res["d516"] == 0x700 and res["req"] == 0x10}})
    fc = FloorLab(rom, SWEEP_ACT)
    cx3, cy3 = SWEEP_CELL
    patch3 = isolated_cell_patch(cx3, cy3, CRUMBLE_BLOCK)
    for st in (5, 0x21, 0x12):
        extra = STATE_FOOT_EXTRA.get(st, 0)
        for foot in (-1, 0, 31, 32):
            for vy in (-0x100, 0x100):
                for same in (False, True):
                    ay = cy3 * CELL + foot - 18 - extra
                    res = fc.go(cx3 * CELL + 10, ay, 0, vy, floor=False, prev=0, cur=st, patch=patch3, d356=(0xC001 + cy3 * fc.width + cx3) if same else 0)
                    vec["crumble_trigger_floor_pass"].append({"input": {"state": st, "foot_row_in_cell": foot, "y_speed_8_8": vy, "remembered_cell_equals_cell": same, "anchor_x_offset_in_cell": 10},
                                                              "expect": {"handler_reached": "h0c" in res["hits"], "spawned": bool(res["objs"]), "y_speed_8_8": res["vy"]}})
    return vec


def trace_vector(vid: str, act: str, fixture: dict, columns, rows, checks: list, note: str = "") -> dict:
    return {"id": vid, "act": act, "fixture": fixture, "rows_columns": columns, "rows": rows, "checks": checks, "note": note}


def make_trace_vectors(data: dict) -> list:
    wgc, wgb = data["crumble"]["whole_game"], data["booster"]["whole_game"]
    cols = COMPACT_COLUMNS
    tv = []
    d = wgc["drop_sez1_67_6"]
    tv.append(trace_vector("crumble_drop_sez1_67_6", "sez1", {"start_anchor": [2160, 120], "state": "0x0E", "movement_d503": "0x81 (jump latch + invulnerable fixture)", "floor_flag": False, "previous_flags": 0,
                                                              "input": "none", "player_invulnerable_fixture": True}, cols, [r[:11] for r in d["rows"]],
                           ["spawn at the first update whose foot sample is in the cell", "16 rider updates directly after", "break update = spawn + 17", "children + remove callback = spawn + 18"],
                           "rows are updates 8..61; the 12th column of each row (objects) is in the audit JSON"))
    for key, title, note in (("walk_off_ledge", "crumble_walk_off_sez1_28_10", "Sonic walks left off the two-cell ledge and hovers at Y 304 until the second object breaks"),
                             ("strip_run", "crumble_strip_run_sez1_62_67_14", "six-cell bridge at 4 px/update: one object per cell, each breaks 17 updates after its spawn, Sonic never falls"),
                             ("jump_up_through", "crumble_rise_through_sez1_67_6", "handler runs while rising (no effect); first spawn on the first non-negative-Y-speed update with the foot in the cell"),
                             ("revisit_same_cell", "crumble_revisit_same_cell_sez1_67_6", "jump during the hold and land again on the same cell: no second object"),
                             ("a_b_a", "crumble_a_b_a_sez1_62_63_14", "teleport A -> B -> A: a second object for A is created because $D356 changed")):
        s = wgc[key]
        tv.append(trace_vector(title, "sez1", {k: v for k, v in s.items() if k not in ("rows", "rows_columns") and not isinstance(v, (list, dict))} | {"summary_keys": [k for k in s if k not in ("rows", "rows_columns")]},
                               cols, [r[:11] for r in s["rows"]], [], note))
    for key, title, note in (("full_pool", "crumble_full_pool_sez1_67_6", "pool full: no object, no hold, no break, Y speed zeroed every update"),):
        s = wgc[key]
        tv.append(trace_vector(title, "sez1", {k: v for k, v in s.items() if k not in ("rows", "rows_columns")}, cols, [r[:11] for r in s["rows"]], [], note))
    tv.append(trace_vector("booster_bridge_sez2_42_17", "sez2", {k: v for k, v in wgb["bridge"].items() if k not in ("rows", "rows_columns")}, cols, [r[:11] for r in wgb["bridge"]["rows"]], [],
                           "pad then four-cell crumble bridge"))
    return tv


def trim_for_contract(d: dict, drop=("rows", "rows_columns")) -> dict:
    return {k: v for k, v in d.items() if k not in drop}



# --------------------------------------------------------------------------- #
# 9. runtime contracts
# --------------------------------------------------------------------------- #
def make_contracts(rom: bytes, data: dict, lays: dict) -> dict:
    cr, bo = data["crumble"], data["booster"]
    wgc, wgb = cr["whole_game"], bo["whole_game"]
    cells = wgc["cell_sweep"]["cells"]
    ref = wgc["drop_sez1_67_6"]["summary"]
    hold_count = {c["summary"]["hold_count"] for c in cells}
    assert hold_count == {16} and {c["summary"]["break_offset"] for c in cells} == {17} and {c["summary"]["child_alloc_offset"] for c in cells} == {18}
    sh = {(s["x_offset"], s["p_at_creation"], s["first_move_offset"]) for c in cells for s in c["summary"]["shards"]}
    assert sh == {(0, 3, 22), (8, 8, 27), (16, 5, 24), (24, 1, 20)}, sh
    stc, stb = wgc["state_scan"], wgb["state_scan"]
    st13 = data["static"]["type13"]
    bo_cells = wgb["cell_sweep"]["cells"]
    crumble = {
        "status": "ROM-derived (Research); Windows acceptance pending; GameMaker implementation not started",
        "identity": {"surface_type": "0x0C", "block": "0xAF", "replacement_block": "0xB0", "dynamic_object_type": "0x13", "object_is_ever_placed": False,
                     "same_header_blocks_never_in_any_layout": ["0xB9", "0xBA", "0xBB"], "identity_name": "UNRESOLVED (numeric ids only)"},
        "terrain_block": {"flags": "0x4C", "one_way_bit6": True, "solid_bit7": False, "modifier": 0, "vertical_profile": "32 at every X (full cell height)", "horizontal_profile": "0x60 at every row",
                          "side_pass": "no wall (0 pushes in the sweep: same as one-way block $0D)", "ceiling_pass": "none: a rising player passes through",
                          "support": "ordinary one-way projection of the shared floor pass (table in the audit: support_projection_table); nothing else about the block is special"},
        "replacement_block_b0": {"flags": "0x00", "profiles": "vertical 0 / horizontal 0x40: empty air", "mapping": "all 16 tile numbers = 192 (blank)", "placed_in_initial_layouts": data["census"]["b0_in_initial_layouts"]},
        "update_order": data["crumble"]["update_order"]["one_loop_iteration"],
        "trigger": {
            "dispatch": "floor pass $691A -> floor dispatch table $6973[surface $0C] = $6B79 (run for the CURRENT foot sample, after the projection against the previous update's flags)",
            "probe": {"x": "player anchor X (no width)", "y": "player anchor Y + 18 + extra", "extra_by_state": {"0x21": -14, "0x12": 8}, "extra_default": 0, "cell": "32 x 32, block id from the layout RAM"},
            "handler_called_iff": "the probed block is $AF; independent of player state, floor flag, previous-update block flags, Y speed, +$03 (attack posture / jump latch / blink) and invincibility "
                                  "(106,704 + 3,072 controlled cases, 0 exceptions)",
            "states_that_run_the_floor_pass_and_so_the_handler": stc["handler_reached_states"], "states_that_do_not": stc["handler_not_reached_states"],
            "states_numeric_note": "numeric player-state ids only; $0C/$0D/$13 are the loop states, $16/$17/$18 and $1F/$20/$21/$23.. do not run the floor pass; $22 (twist) and $0F..$12 do",
            "handler_algorithm": ["if player +$19 bit 7 (Y speed negative): return (nothing changes: no Y speed write, no spawn, no remembered-cell update)",
                                  "Y speed := 0 (EVERY call, before the same-cell test: standing on the cell zeroes Y speed every update)",
                                  "if probed cell pointer ($D354) == remembered cell ($D356): return",
                                  "spawn type $13 at probe position ($D358,$D35A) via $5EB7: first free slot of slots 0..15, parameter 0; silent no-op when full",
                                  "$D356 := $D354 (also when the spawn failed); +$30/+$31 of the object at IY := cell pointer (IY = $D940 = slot 16 when the pool was full)"]},
        "remembered_cell": {"register": "$D356 (word)", "written_only_by": "$6B79 (byte scan: two operand sites in the whole ROM)", "reset": "$297E level clear ($D300..$DBBF) at every level initialisation: "
                            "death/restart gives 0 (EMULATED)", "behaviour": ["touching a different $AF cell always spawns (even while an earlier object still lives)", "re-touching the SAME cell while it is still remembered "
                                                                              "never spawns: jump + re-land (EMULATED), standing on a cell whose object was removed (EMULATED, cell stays $AF)",
                                                                              "A -> B -> A before A broke creates a SECOND object for A; both end with $B0 (EMULATED)"],
                            "cell_pointer": "layout RAM $C001 + cy * width + cx"},
        "allocator": {"parent": {"routine": "$5EB7", "slots": "0..15 (first free)", "full_behaviour": "no object, no hold, no break; cell never crumbles while the remembered cell equals it; Y speed still zeroed; "
                                 "slot 16 +$30/+$31 (bytes $D970/$D971) overwritten with the cell pointer (no consumer found)", "evidence": "handler matrix 545 cases + EMULATED full-pool drop"},
                      "children": {"routine": "$5EE1 via script command 4", "slots": "7..17 (11 slots, shared with every other command-4 / badnik allocation)", "when_k_free": "only the first k of the four shards are created, "
                                   "in the order offsets 0, 8, 16, 24 (parameters 3, 8, 5, 1); none when 0 free; silent", "child_below_parent_slot": "its state-0 callback (and so the whole shard timeline) is one update later"}},
        "object_13": {
            "created_by": "$6B79 only (and by its own command-4 children)", "state_table": st13["state_table_cpu"], "states": {"0": "init $A2DD (dur 224)", "1": "record 16 updates rider hold $A344; record 1 update break $A36A; "
                                                                                                                  "then sound $A3 + 4 child spawns; record 224 remove $A33F", "2": "remove (unreachable: nothing requests state 2)", "3": "shard fall $A31B"},
            "init_a2dd": {"parameter_nonzero": "request state 3", "parameter_zero": "X := (X & $FFE0) + 14, Y := (Y & $FFE0) + 24 from the probed position; +$34/35 := raw X, +$36/37 := raw Y; request state 1"},
            "timeline_updates_relative_to_spawn_update_T": {"spawn_and_state0_callback": 0, "rider_hold_first": 1, "rider_hold_count": 16, "rider_hold_last": 16, "break_callback": 17,
                                                            "cell_replaced": 17, "sound_a3_children_created_and_remove_callback": 18, "child_state0_callbacks": 18, "first_shard_state3_pass": 19,
                                                            "first_shard_move": {"offset_0_p3": 22, "offset_8_p8": 27, "offset_16_p5": 24, "offset_24_p1": 20}},
            "anchor": "object X = cell left + 14, object Y = cell top + 24 (the cell is the one containing the probed foot sample)", "visible_art": "the parent object is INVISIBLE (mapping frame 0 has no pieces); the ledge you see is the terrain block art; shards use mapping frame 15"},
        "rider_hold": {"callback": "$A344 (once per update during the 16-update record, in the object pass)", "applies_iff": "player state == $0E OR player +$03 bit 0 clear",
                       "effect": "player Y := objectY - 40 (= cell top - 16: feet 2 px INTO the cell), Y speed := 0, $D521 bit 1 set (no reader of that bit was found: it is cleared by the scheduler every frame and "
                                  "has no observable effect on the floor flags or the state, e.g. a hovering Sonic keeps floor flags 0 and state $0E)",
                       "no_presence_test": "no X or Y comparison with the object: any player in a qualifying state is held, so walking off a ledge hovers at the held Y until the last live object breaks "
                                           f"(SEZ1 walk-off: {wgc['walk_off_ledge']['hover_count']} hover updates beyond the ledge edge)",
                       "ordering": "inside every hold update the terrain pass leaves Sonic at cell top - 18 (EMULATED hook at the scheduler entry), the object pass then writes cell top - 16; the end-of-update Y is what is "
                                       "rendered; the first update (spawn) and the break update have no hold",
                       "matrix": "state 0..$36 x +$03 0..255 = 14,080 controlled cases, 0 exceptions"},
        "break": {"callback": "$A36A", "replaces_cell_unless": "object asleep (+$04 bit 6) or objectX < cameraX (strict, unsigned 16-bit; cameraX = $D174)", "replacement": "block $B0 written into the layout RAM through "
                  "vector $0428 -> $6C1F (also redraws the 4x4 name-table cells: blank)", "when_not_replaced": "object removed (type := $FF); the cell stays $AF and $D356 still remembers it",
                  "naturally_reachable": f"camera trails the player by about 118 px: SEZ1 bridge at 4.0..7.0 px/update keeps objectX - cameraX >= {wgc['strip_speed_sweep']['minimum_margin']} px at every break (EMULATED): the removal branches "
                                         "need fixtures in the shipped acts"},
        "shards": {"count": 4, "type": "0x13 parameter != 0 (state 3)", "spawn": "script command 4 at the break update + 1 (update 18): offsets from the parent (-14,-24),(-6,-24),(2,-24),(10,-24) -> world (cell+0, cell+8, cell+16, cell+24; "
                   "cell top)", "parameters_delay": [3, 8, 5, 1], "motion": "Y speed +$0200 loaded once, then per pass after the delay: Y speed += $0200, Y += Y speed (integer part); X never changes; "
                   "k-th move adds 2(k+1) px: y_k = y0 + k(k+3)", "first_move_pass_from_creation": "parameter + 2 (the state-0 pass is pass 1)", "lifetime": "until the generic lifecycle sleeps them (class 2: +$04 bit 6), "
                   "then their callback removes them one pass later (type $FF, slot cleared the pass after)", "no_terrain_no_contact_no_damage": True,
                   "art": "mapping frame 15 (8x16 piece, common object stream tiles $66/$67, art base 0) - presentation, see the SEZ art package"},
        "lifecycle": {"table": "bank $1C:$8146, 32 x 32 classes of 16 px, index (x - camX + 128, y - camY + 128)", "model": "lifecycle_class() in the audit; 55,155 cases, 0 mismatches"},
        "player_interactions": {"contact_with_player": "none (no overlap helper, no attack gate, no damage entry in any $13 callback)", "attack_posture": "not read by the handler, the hold or the object",
                                "rolling_jumping_spin_dash": "handled exactly like walking: only state == $0E or +$03 bit 0 clear matters for the hold; a jumping player (bit 0 set, state != $0E) is not held until "
                                                              "the landing clears bit 0", "rising": "no spawn, no zero", "footwear": "state $12 samples the foot 8 px lower ($6B79 reached 8 px earlier), state $21 14 px "
                                                                                                                                  "higher; Spring Shoes / Rocket Shoes end-to-end on a crumble cell is UNRESOLVED (no shoe is near a cell)",
                                "invincibility_d532": "not read", "hurt_blink_fixture": "no effect on the timeline"},
        "persistence": {"cell": "the layout RAM keeps $B0 for the rest of the act (scroll away/back: still $B0; no new object)", "restart": "act restart reloads the layout: $AF returns, $D356 := 0",
                        "object": "no placement token: never recreated, never persistent; a removed object leaves the cell $AF"},
        "global_runtime": {"proof": "same coordinate-free timeline signature for all 93 $AF cells in THZ1, THZ2, SEZ1-3, AQZ1-2, EEZ2; no routine involved reads the zone byte (byte scan)",
                           "signature_classes": wgc["cell_sweep"]["distinct_signatures"], "cells": wgc["cell_sweep"]["cell_count"]},
        "cells": [{"act": c["act"], "cell": c["cell"], **{k: v for k, v in cell_geometry(*c["cell"]).items() if k in ("object_anchor", "hold_anchor_y", "shard_anchors", "cell_pointer_offset_from_c001")},
                   "above_block": c["above_block"]} for c in cells if c["act"].startswith("sez")],
        "viewport_classification": [
            {"subject": "break removal 'left of camera'", "class": "EDGE(LEFT,0)", "rule": "objectX < cameraX (strict)", "adapter": "keep the relation to the visible left edge; do not convert to a world distance"},
            {"subject": "shard / object lifecycle (class 2 sleep, class 3 delete)", "class": "LIFECYCLE", "rule": "table lookup of (x - camX + 128, y - camY + 128)",
             "adapter": "candidate: the accepted generic lifecycle adapter (horizontal retention max(0, viewport_width - 256)); vertical bands not widened"},
            {"subject": "probe / handler / hold", "class": "WORLD", "rule": "player anchor and cell grid only: no camera input"},
            {"subject": "rider hold", "class": "WORLD", "rule": "no presence distance"}],
        "adapter_candidates_not_rom_facts": ["pre-aligning the hold to the terrain (e.g. holding at cell top - 18) is NOT canonical: the 2 px sink is observable", "dropping the unconditional hold "
                                             "(hover) is NOT canonical"],
    }
    bst = {
        "status": "ROM-derived (Research); Windows acceptance pending; GameMaker implementation not started",
        "identity": {"surface_type": "0x1A", "block": "0xA7", "identity_name": "UNRESOLVED (numeric ids only); art = a pad with animated tile $158, no directional glyph"},
        "terrain_block": {"flags": "0x9A", "solid_bit7": True, "one_way_bit6": False, "vertical_profile_runs": bo["a7_support"]["vertical_profile_runs"], "horizontal_profile": "0x40 at every row",
                          "floor_handler": "$69B1 = RET (the floor pass never acts on the block)", "side_pass": "no wall", "ceiling_pass": "no handler for surface $1A; solid profile pushes only in the 24 grazing cases "
                          "of the sweep", "support": "solid projection against the 0..2 px bump (support = cell top + 32 - profile)", "reading": "the pad is a decoration/trigger cell placed one cell ABOVE the ground row"},
        "trigger": {"dispatch": "terrain ring probe $753E ONLY (after floor, sides, ceiling in the terrain pass); the floor dispatch entry is a bare RET",
                    "probe": {"x": "player anchor X", "y": "anchor Y - 8 when (+$07 & 1) == 0 else anchor Y + 2", "note": "+$07 = the animation record counter (see the animation-counter audit)"},
                    "handler_reached_iff": "the probe's block is $A7", "effect_iff": "player +$22 bit 1 (floor flag) is set at the probe", "cell_condition_world": "anchor X in [cell left, cell left + 31]; "
                    "anchor Y in [cell top + 8, cell top + 39] (even parity) or [cell top - 2, cell top + 29] (odd parity)",
                    "standing_on_ground_row_below": "anchor Y = ground top - 18 = cell top + 14 lies inside both parity windows: a grounded walker is launched in every update the column contains it",
                    "controlled_sweeps": {"probe": bo["probe_sweep"]["cases"], "handler": bo["handler_matrix"]["cases"]}},
        "effect": {"x_speed_8_8": 0x0700, "max_x_speed_d373": 0x0700, "movement_d503": "(+$03 | $02) & $FE: attack posture ON, jump latch cleared", "requested_state": "0x10", "sound_request_de04": "0xBD",
                   "untouched": ["Y speed", "facing (+$04 bit 4)", "position", "floor flags", "everything else"], "sign": "always positive: an incoming X speed (including negative) is overwritten",
                   "not_the_spin_dash_setter": "$4719 would use facing and request sound $BE; the booster writes the speed itself and only REQUESTS state $10"},
        "after_launch": {"state_10": "spin-dash roll state: callback $3A23 -> shared updater $3FEF; X speed decays 5/256 per update with no input (4/256 with RIGHT held) and the player stays in $10 while "
                                    "|X speed| >= $10 and no opposing direction is held; LEFT held while moving right requests the skid state $07 and decelerates faster; DOWN/UP change nothing; B1 jumps (state $0A "
                                    "with attack posture kept, X speed kept)", "max_x_speed": "$D373 stays $0700 until a later setter rewrites it (a RIGHT-held airborne player re-accelerates to 7.0)",
                         "facing": "not written by the handler; the game turns Sonic to face right within the next update when he was facing left (EMULATED)", "attack": "+$03 bit 1 set = canonical attack posture"},
        "repeat_contact": {"rule": "the handler runs in EVERY update whose probe is inside the cell with the floor flag set; at 7.0 px/update a 32 px column re-triggers 5 times; the sound request is rewritten each time",
                           "standing_start": wgb["speed_table"]["standing_start_center"], "entry_speed_table": wgb["speed_table"]["entry_x_speed_8_8_to_result"]},
        "direction": {"fixed_rightward": True, "evidence": ["handler writes +$0700 unconditionally (65,536 controlled cases)", "entering from the right edge at any speed re-launches rightward after one update",
                                                            "the art has no directional glyph"], "from_right_handler_count": 1},
        "interactions": {"states_reaching_the_probe": stb["ring_probe_states"], "states_where_the_effect_applies_at_first_update": stb["effect_applied_states"], "state_scan_note": "forced-state first update",
                         "twist_22": "runs the floor pass but not the ring probe: no effect", "loop_states": "$0C/$0D/$13 do not run the terrain pass", "rocket_shoes_11": wgb["footwear"]["state_11_probe_parity_0"],
                         "spring_shoes_12_forced_without_shoe_object": {"parity_0": wgb["footwear"]["state_12_probe_parity_0"], "parity_1": wgb["footwear"]["state_12_probe_parity_1"]},
                         "footwear_notes": wgb["footwear"]["notes"], "crumble_bridge": "SEZ2: the pad at (42,17) leads onto the crumble bridge (44..47,18); arrival at 7 px/update crosses without falling (EMULATED)"},
        "effect5_animation": {"summary": "tile $158 (VRAM $2B00) alternates two 32-byte images every 3 effect calls, one call per game-loop iteration, paused while the boss flag $D44E != 0",
                              "sources": wgb["effect5"]["sources"], "first_copy_image": "0x8DFD", "period_calls": 6, "rule": wgb["effect5"]["rule"],
                              "art_relation": {k: wgb["art"][k] for k in ("block", "tile_0x158_use_count", "positions_of_tile_0x158_row_major_index", "blocks_that_draw_tile_0x158_in_sez2", "images_differ")},
                              "absolute_phase": "not tied to the player: it counts effect calls since the level started ($D452..: cleared by $297E); the pad's launch does not read it"},
        "global_runtime": {"proof": "same coordinate-free launch signature for all 9 $A7 cells (SEZ2 x2, SEZ3 x2, AQZ1, AQZ2 x2, EEZ1, EEZ2); the handler and probe read no zone byte (effect 5 does, by table)",
                           "signature_classes": wgb["cell_sweep"]["distinct_left_signatures"], "cells": wgb["cell_sweep"]["cell_count"]},
        "placements": [p for p in wgb["placements"] if p["act"].startswith("sez")],
        "viewport_classification": [{"subject": "probe / handler / launch", "class": "WORLD", "rule": "player anchor and cell grid only"},
                                    {"subject": "effect-5 animation", "class": "frame-count timer", "rule": "not viewport-relative; do not scale with the window"}],
        "adapter_candidates_not_rom_facts": ["a GameMaker mask or hitbox for the pad is NOT canonical: use the probe rule", "do not flip the direction for a left-facing player"],
    }
    contracts = {"format": "sez-surface-runtime-contracts-v1", "rom_sha256": data["rom_sha256"], "research_base": RESEARCH_BASE, "research_only": True,
                 "coordinate_policy": "world pixels; anchor = player Y register (feet = anchor + 18); cells 32 px; 'update' = one game-loop iteration (player engine, callback, object pass)",
                 "evidence_note": "every number is copied from the audit JSON (surfaces-0c-1a.json) or asserted against it when this file is generated",
                 "crumble_0C_13": crumble, "booster_1A": bst, "oracle_vectors": {"how_to_use": "table_vectors: call the named original routine (or its POC equivalent) with `input` and compare `expect`; "
                                                                                   "trace_vectors: apply `fixture` at an update boundary, feed `input`, compare rows column by column (the 12th row "
                                                                                   "column, objects, is in the audit JSON)", "table_vectors": table_vectors(rom),
                                                                                   "trace_vectors": make_trace_vectors(data)}}
    return contracts



def dumps(data: dict) -> str:
    return json.dumps(data, indent=1) + "\n"


def build_all(rom: bytes, static_only: bool = False) -> tuple:
    data = build(rom, static_only)
    if static_only:
        return data, None
    lays = all_layouts(rom)
    contracts = make_contracts(rom, data, lays)
    return data, contracts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    a = ap.parse_args()
    rom = L.load_rom(a.rom)
    data, contracts = build_all(rom, a.static_only)
    text = dumps(data)
    ctext = dumps(contracts) if contracts else None
    if a.check:
        bad = []
        cached = OUT_AUDIT.read_text(encoding="utf-8").replace("\r\n", "\n")
        if a.static_only:
            cj, dj = json.loads(cached), json.loads(text)
            bad += [k for k in dj if k in cj and k != "static_only" and cj[k] != dj[k]]
        else:
            bad += [] if cached == text else ["audit"]
            bad += [] if OUT_CONTRACTS.read_text(encoding="utf-8").replace("\r\n", "\n") == ctext else ["contracts"]
        print("OK: caches match the ROM" if not bad else f"MISMATCH in {bad}")
        sys.exit(1 if bad else 0)
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    OUT_AUDIT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT_AUDIT} ({len(text)} bytes)")
    if ctext:
        OUT_CONTRACTS.write_text(ctext, encoding="utf-8", newline="\n")
        print(f"wrote {OUT_CONTRACTS} ({len(ctext)} bytes)")


if __name__ == "__main__":
    main()

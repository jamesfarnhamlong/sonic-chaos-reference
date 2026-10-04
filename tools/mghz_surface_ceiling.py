#!/usr/bin/env python3
"""MGHZ terrain-mechanics audit: surface $1B (block $A0, sinking) and ceiling spikes (blocks $3E/$3F). Research only, deterministic.

Scope (bounded): ONLY the two mechanics the MGHZ foundation left open.  Not covered: type $24, type $2E, footwear, boss $56.
Output: data/rom-cache/mghz/surface-1b-ceiling-spikes.json (numeric labels; no ROM bytes beyond region hashes).

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT (original Z80 routines on
tools/oracle.py with the decoded MGHZ layouts), EMULATED ORIGINAL FRAME (whole game in tools/sms_frame_harness.py booted into MGHZ), UNRESOLVED.

Usage:
  python tools/mghz_surface_ceiling.py ROM.sms [--check] [--static-only]
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

import isometric_platform as I          # noqa: E402  (TerrainLab on decoded act layouts, act_data)
import level_package as L               # noqa: E402
import platform_spike_collision as P    # noqa: E402  (Emu helpers, region hashes, block_header)
import rom as R                         # noqa: E402

OUTPUT = ROOT / "data" / "rom-cache" / "mghz" / "surface-1b-ceiling-spikes.json"
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
RESEARCH_BASE = "ac04dfe"
ZONE = 3
ACTS = ("mghz1", "mghz2", "mghz3")
ACT_INDEX = {k: i for i, k in enumerate(ACTS)}

OIL_BLOCK = 0xA0
SPIKE_CEILING_BLOCKS = (0x3E, 0x3F)
FLOOR_SPIKE_BLOCKS = (0x3C, 0x3D)
HURT_ENTRY = 0x48F7
OIL_HANDLER = 0x6B14
SINK_BRANCH = 0x7010
FLOOR_PROJECTION = 0x6F61
CEILING_TYPE5 = 0x74E7
CEILING_BOUNCE = 0x7459
FLOOR_SPIKE_HANDLER = 0x6ACE


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def s16(v: int) -> int:
    return (v + 32768) % 65536 - 32768


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM")


def loc(i: int) -> dict:
    """File offset -> bank / CPU address."""
    return {"file": h(i, 5), "bank": h(i // 0x4000, 2), "cpu": h(i if i < 0x8000 else 0x8000 + i % 0x4000)}


def ranges(values) -> list:
    return P.ranges(values)


def rects(cells) -> list:
    """Set of (x, y) -> [x0, x1, y0, y1] rectangles (identical row runs merged)."""
    return P._rects(cells)


# --------------------------------------------------------------------------- #
# 1. static facts
# --------------------------------------------------------------------------- #
REGIONS = [
    ("surface_1b_handler_6b14", 0x6B14, 0x6B23, "player +$24 bit 1 := 1; $D3BC += 1 when ($D12F & 3) == 0"),
    ("surface_19_handler_6b23", 0x6B23, 0x6B2C, "sibling strip handler: +$24 bit 0, $D3BC += 1 every pass (for contrast)"),
    ("surface_0_handler_6c45", 0x6C45, 0x6C4D, "empty block: clears +$24 bits 0 and 1 ($6C4D tail is shared with surface 6/7)"),
    ("floor_pass_691a", 0x691A, 0x6973, "foot sample, previous-surface projection $6F61, dispatch by current surface type"),
    ("floor_projection_6f61", 0x6F61, 0x7056, "projection against the PREVIOUS flags $D36C: solid / one-way / strip gate / bit-1 sink branch $7010"),
    ("sink_branch_7010", 0x7010, 0x7056, "one-way projection with the sink counter: probe +4, penetration, Y := Y - pen + $D3BC"),
    ("jump_reset_45ed", 0x45ED, 0x463C, "jump setter: clears $D3BC and +$24 bit 0 (not bit 1)"),
    ("fall_reset_463c", 0x463C, 0x4663, "ordinary fall setter (state $0E): clears $D3BC and +$24 bit 0"),
    ("strip_fall_reset_4663", 0x4663, 0x4680, "strip fall setter (state $14): clears $D3BC, keeps +$24 bit 0"),
    ("y_integration_4097", 0x4097, 0x4141, "player Y integration: floor flag set => Y speed := $0700 ($0900 for modifier 10/12)"),
    ("ceiling_probe_73c9", 0x73C9, 0x7416, "ceiling pass entry gate, probe (0,-24), type dispatch chain"),
    ("ceiling_type5_74e7", 0x74E7, 0x7530, "type 5 ceiling tail: push down, hurt only for blocks $3E/$3F and not invulnerable, else ordinary bounce"),
    ("ceiling_bounce_7459", 0x7459, 0x7464, "ordinary ceiling response: Y speed := +1.0, clear ceiling flag"),
    ("floor_spike_handler_6ace", 0x6ACE, 0x6AE3, "type 5 foot handler: hurt when floor flag set and not invulnerable (tile != $F4/$F5)"),
    ("hurt_48f7", 0x48F7, 0x4984, "shared hurt entry (ring scatter or death); no invulnerability or power-up test inside"),
    ("damage_gate_48bc", 0x48BC, 0x48F7, "object/contact damage gate ($D532 == 6 invincibility lives HERE, not in terrain hazards)"),
    ("lookup_7666", 0x7666, 0x77B0, "block lookup: probe (X+BC, Y+DE+18), header flags -> $D364, vertical profile -> $D368"),
    ("terrain_pass_690b", 0x690B, 0x691A, "floor, sides, ceiling, terrain-ring probe, merge"),
]

FLOOR_DISPATCH = 0x6973
CEILING_CHAIN = (0x73F8, 0x7413)


def region_table(rom: bytes) -> list:
    return [{"name": n, "cpu": h(a), "file": h(a, 5), "length": b - a, "sha256": sha(rom[a:b]), "purpose": why} for n, a, b, why in REGIONS]


def dispatch_entries(rom: bytes) -> dict:
    out = {}
    for t in range(0x1D):
        out[h(t, 2)] = h(rom[FLOOR_DISPATCH + 2 * t] | rom[FLOOR_DISPATCH + 2 * t + 1] << 8)
    return out


def ceiling_chain(rom: bytes) -> list:
    import mghz_foundation as F
    return [[h(s, 2), h(t)] for s, t in F.dispatch_chain(rom, *CEILING_CHAIN)]


def header_facts(rom: bytes, blk: int) -> dict:
    hd = R.header(rom, blk)
    return {"block": h(blk, 2), "header_file": h(hd["address"], 5), "flags": h(hd["flags"], 2), "surface_type": h(hd["flags"] & 0x1F, 2),
            "solid_bit7": bool(hd["flags"] & 0x80), "one_way_bit6": bool(hd["flags"] & 0x40), "alt_plane_bit5": bool(hd["flags"] & 0x20),
            "modifier": hd["modifier"], "vertical_pointer": h(hd["vertical_pointer"] - 0x30000), "vertical_pointer_high_byte": (hd["vertical_pointer"] - 0x30000) >> 8,
            "horizontal_pointer": h(hd["horizontal_pointer"] - 0x30000), "vertical_profile_runs_by_x": P.runs32(hd["vertical"]),
            "horizontal_profile_runs_by_y": P.runs32(hd["horizontal"]), "trailing_byte": hd["trailing_byte"]}


def bit6_only_blocks(rom: bytes) -> list:
    return [b for b in range(256) if R.header(rom, b)["flags"] & 0x40 and not R.header(rom, b)["flags"] & 0x80]


def plus24_and_d3bc_sites(rom: bytes) -> dict:
    """Whole-ROM byte scan: every IX/IY bit instruction on +$24 and every little-endian $D3BC / absolute $D524 operand."""
    bitops = {"bit0": [], "bit1": [], "other_bits": []}
    names = {0x40: "BIT", 0x80: "RES", 0xC0: "SET"}
    for pre in (0xDD, 0xFD):
        for i in range(len(rom) - 3):
            if rom[i] == pre and rom[i + 1] == 0xCB and rom[i + 2] == 0x24:
                op = rom[i + 3]
                bit = (op >> 3) & 7
                kind = names.get(op & 0xC0)
                if kind is None or (op & 7) != 6:
                    continue
                row = {"op": f"{kind} {bit},(I{'X' if pre == 0xDD else 'Y'}+$24)", **loc(i)}
                bitops["bit0" if bit == 0 else "bit1" if bit == 1 else "other_bits"].append(row)
    d3bc = []
    roles = {0x4605: "jump setter $45ED: counter := 0", 0x465C: "fall setter $463C (state $0E): counter := 0", 0x467D: "strip-fall setter $4663 (state $14): counter := 0",
             0x6B1F: "surface $1B handler: INC (HL) when ($D12F & 3) == 0", 0x6B28: "surface $19 handler: INC (HL) every pass",
             0x703E: "sink branch $7010: the ONLY numeric read (Y := Y - penetration + counter)",
             0x30D1C: "other-character run selector: counter := 0 only when +$24 bit 0 is set and the previous surface != $19",
             0x30F01: "Sonic walk selector: counter := 0 only when +$24 bit 0 is set and the previous surface != $19",
             0x30F5C: "Sonic run selector: counter := 0 only when +$24 bit 0 is set and the previous surface != $19"}
    for p in range(len(rom) - 1):
        if rom[p] == 0xBC and rom[p + 1] == 0xD3:
            d3bc.append({"operand_file": h(p, 5), **loc(p), "role": roles.get(p, "UNCLASSIFIED")})
    return {"evidence": "BYTE-VERIFIED ASSEMBLY (whole-ROM scan of the instruction forms, then hand classification)",
            "plus24_bit_instructions": bitops, "d3bc_operands": d3bc,
            "reading": "bit 1 of the player's +$24 byte is SET only at $6B14 (surface $1B), CLEARED only at $6C49 (surface $00 handler) and READ only at $6FC7 (one-way projection). "
                       "Bit 0 is the surface-$19 strip bit (separate audit). The other +$24 word accesses in banks 0/2/$1E belong to unrelated object slots (VRAM-stream effect object at $2DDE..$2E56 etc.), not to the player."}


def block_art(rom: bytes) -> dict:
    """MGHZ block-mapping attribute words (16 per block; bit 9 H-flip, bit 10 V-flip) for the spike family: 3E/3F differ in ART only."""
    import mghz_foundation as F
    base = F.MAPPING_BANK * 0x4000
    return {h(b, 2): [h(v, 3) for v in L.block_mapping(rom, base, b)["attributes"]] for b in (0x3C, 0x3E, 0x3F, OIL_BLOCK, 0x9E)}


def foot_probe_facts(rom: bytes) -> dict:
    """$691A: the foot sample is (X, Y+18) plus a per-state extra Y offset; read from the code bytes."""
    ok = (rom[0x693C:0x6941] == bytes.fromhex("dd7e01fe21") and rom[0x6943:0x6946] == bytes.fromhex("11f2ff") and rom[0x6948:0x694B] == bytes.fromhex("fe1220") and rom[0x694C:0x694F] == bytes.fromhex("110800"))
    return {"evidence": "BYTE-VERIFIED ASSEMBLY ($691A..$694F)", "bytes_match_expected_pattern": ok, "foot_probe": "(anchor X, anchor Y + 18 + extra) with extra = 0 normally",
            "extra_y_by_current_state": {"0x21": -14, "0x12": 8}, "lookup_adds": 18,
            "note": "states $21 and $12 therefore sample the oil (and every other floor block) 14 px higher / 8 px lower than the default; the sink formula uses the sampled row, so their steady anchor differs by that offset. "
                    "State $12 is Spring Shoes (footwear audit) and is not examined further here."}


def static_facts(rom: bytes) -> dict:
    disp = dispatch_entries(rom)
    heads = {h(b, 2): header_facts(rom, b) for b in (OIL_BLOCK, 0x3E, 0x3F, 0x3C, 0x3D, 0x9E, 0x0D, 0x0F, 0xF9)}
    a, b = R.header(rom, 0x3E), R.header(rom, 0x3F)
    identical = {k: a[k] == b[k] for k in ("flags", "modifier", "vertical", "horizontal", "trailing_byte")}
    bit6 = bit6_only_blocks(rom)
    hhi = {h(x, 2): (R.header(rom, x)["horizontal_pointer"] - 0x30000) >> 8 for x in bit6}
    alt = {h(x, 2): (R.header(rom, x, plane=1)["horizontal_pointer"] - 0x30000) >> 8 for x in bit6}
    allhi = [(R.header(rom, x)["horizontal_pointer"] - 0x30000) >> 8 for x in range(256)]
    return {
        "evidence": "DECODED DATA + BYTE-VERIFIED ASSEMBLY",
        "floor_dispatch_table_6973": {"surface_$1B": disp["0x1B"], "surface_$05": disp["0x05"], "surface_$00": disp["0x00"], "surface_$19": disp["0x19"], "surface_$06": disp["0x06"], "surface_$07": disp["0x07"], "surface_$01": disp["0x01"], "surface_$02": disp["0x02"]},
        "ceiling_dispatch_chain": ceiling_chain(rom),
        "routines": region_table(rom),
        "block_headers": heads,
        "blocks_3e_3f_header_fields_identical": identical,
        "oil_block_is_the_only_surface_1b_block": [h(x, 2) for x in range(256) if R.header(rom, x)["flags"] & 0x1F == 0x1B] == ["0xA0"],
        "bit6_only_blocks_all_zones": [h(x, 2) for x in bit6],
        "sink_branch_B_register": {
            "finding": "the sink branch executes `CP B` with B left over from the block lookup $7666: the lookup ends by loading the HORIZONTAL-profile pointer of the block header into BC "
                       "($770A..$770C), so B is the high byte of that pointer. Every header pointer is a bank-$0E CPU address >= $8000, so B >= 128 and the `RET NC` "
                       "(penetration >= B) can never fire for a penetration <= 31; with a raw profile byte up to $FF it could only fire for penetration >= 137.",
            "horizontal_pointer_high_byte_by_bit6_only_block": hhi,
            "min_over_all_256_blocks": min(allhi), "max_over_all_256_blocks": max(allhi),
            "min_over_bit6_only_blocks": min(hhi.values()), "min_alternate_plane_bit6_only": min(alt.values()),
            "oil_block_B": hhi["0xA0"]},
        "foot_probe": foot_probe_facts(rom),
        "block_art_attribute_words": block_art(rom),
        "bit_and_counter_sites": plus24_and_d3bc_sites(rom),
    }


# --------------------------------------------------------------------------- #
# 2. controlled-routine lab (Z80 core, decoded MGHZ layouts)
# --------------------------------------------------------------------------- #
WATCH = {HURT_ENTRY: "hurt", OIL_HANDLER: "oil_handler", SINK_BRANCH: "sink_branch", CEILING_TYPE5: "ceiling_type5", CEILING_BOUNCE: "ceiling_bounce",
         FLOOR_SPIKE_HANDLER: "floor_spike_handler"}
TERMINAL = {HURT_ENTRY}


class Lab(I.TerrainLab):
    """The original terrain pass (or a sub-routine) on a decoded MGHZ act layout with every input state explicit."""

    def __init__(self, rom: bytes, key: str):
        super().__init__(rom, key)
        self.key = key
        self.width = I.act_data(rom, key)["width"]
        self.at_hurt = None
        for a in WATCH:
            self.o.cpu.set_breakpoint(a)

    def _step_over(self, pc: int) -> None:
        cpu = self.o.cpu
        cpu.clear_breakpoint(pc)
        cpu.ticks_to_stop = 1
        cpu.run()
        cpu.set_breakpoint(pc)

    def go(self, x, y, vx=0, vy=0, floor=False, prev=0, cur=0x0A, req=None, f3=None, d3c0=0, k=0, p24=0, d12f=1, inv=False, entry=0x690B,
           plane=0, patch=None, extent=(8, 24), hurt_flag=False, rings=0, d532=0, lookup_first=False) -> dict:
        self.m[0xC000:0xE000] = self.base
        o, m = self.o, self.m
        for (cx, cy), blk in (patch or {}).items():
            m[0xC001 + cy * self.width + cx] = blk
        o.word(0xD511, x)
        o.word(0xD514, y)
        o.word(0xD516, vx & 0xFFFF)
        o.word(0xD518, vy & 0xFFFF)
        m[0xD501] = cur
        m[0xD502] = cur if req is None else req
        m[0xD503] = (f3 if f3 is not None else (0 if floor else 1)) | (0x80 if inv else 0) | (0x40 if hurt_flag else 0)
        m[0xD522] = 2 if floor else 0
        m[0xD523] = 0
        m[0xD524] = p24
        m[0xD525] = plane
        m[0xD36C] = prev
        m[0xD36B] = 0
        m[0xD369] = 0
        m[0xD3C0] = d3c0
        m[0xD3BC] = k
        m[0xD12F] = d12f
        m[0xD29A] = rings
        m[0xD532] = d532
        m[0xD52C], m[0xD52D] = extent
        o.cpu.ix = 0xD500
        hits, at_hurt = [], None
        if lookup_first:
            self._run(0x7666, hits, bc=0, de=0)
            m[0xD36C] = prev
        self._run(entry, hits, bc=None if lookup_first else 0, de=None if lookup_first else 0)
        if hits and hits[-1] == "hurt":
            at_hurt = dict(self.at_hurt)
        return {"hits": hits, "x": o.word(0xD511), "y": o.word(0xD514), "vy": s16(o.word(0xD518)), "vx": s16(o.word(0xD516)), "floor": bool(m[0xD522] & 2),
                "ceiling": bool(m[0xD522] & 1), "d522": m[0xD522], "d523": m[0xD523], "d369": m[0xD369], "d36c": m[0xD36C], "d36b": m[0xD36B], "p24": m[0xD524],
                "k": m[0xD3BC], "block": m[0xD353], "flags": m[0xD364], "profile": m[0xD368], "d35a": o.word(0xD35A), "d358": o.word(0xD358), "f3": m[0xD503],
                "at_hurt": at_hurt}

    def _run(self, entry: int, hits: list, bc=0, de=0) -> None:
        """bc/de None keeps the registers left by the previous call (the sink branch compares against the B left by the lookup)."""
        o, m = self.o, self.m
        o.cpu.pc = entry
        if bc is not None:
            o.cpu.bc = bc
        if de is not None:
            o.cpu.de = de
        o.cpu.sp = 0xDFE0
        o.word(o.cpu.sp, o.RETURN)
        for _ in range(400):
            o.cpu.ticks_to_stop = 100000
            o.cpu.run()
            pc = o.cpu.pc
            if pc == o.RETURN:
                return
            if pc in WATCH:
                hits.append(WATCH[pc])
                if pc in TERMINAL:
                    self.at_hurt = {"y": o.word(0xD514), "x": o.word(0xD511), "d522": m[0xD522], "vy": s16(o.word(0xD518)), "state": m[0xD501], "d503": m[0xD503]}
                    o.cpu.pc = o.RETURN
                    return
                self._step_over(pc)
        raise RuntimeError("controlled pass did not return")



# --------------------------------------------------------------------------- #
# 3. whole-game lab (approximate SMS harness booted into an MGHZ act)
# --------------------------------------------------------------------------- #
class GameLab:
    """Boots the ORIGINAL game into zone 3 / act n, settles 90 frames, snapshots, and forks deterministic cases from the snapshot."""
    PAD = dict(UP=1, DOWN=2, LEFT=4, RIGHT=8, B1=16, B2=32)
    EVENTS = {OIL_HANDLER: "oil", SINK_BRANCH: "sink", HURT_ENTRY: "hurt", CEILING_TYPE5: "ceil5", CEILING_BOUNCE: "bounce", FLOOR_SPIKE_HANDLER: "floor5"}

    def __init__(self, rom: bytes, key: str):
        from sms_frame_harness import SMS, BTN_1, BTN_2
        self.rom, self.key = rom, key
        s = SMS(rom)
        done = [False]
        act = ACT_INDEX[key]

        def select(m):
            m._write(0xD297, ZONE)
            m._write(0xD298, act)

        def start(m):
            if m.frame > 300 and not done[0]:
                done[0] = True
        s.add_pc_hook(0x07D5, select)
        s.add_pc_hook(0x4E97, start)
        for f in range(4000):
            s.pad = 0 if f < 250 else BTN_1 if f < 700 and f % 40 < 3 else (BTN_1 | BTN_2) if not done[0] and f % 60 < 10 else 0
            s.run_frame()
            if done[0] and s.mem[0xD500] == 1:
                break
        else:
            raise RuntimeError("MGHZ boot failed")
        for _ in range(90):
            s.pad = 0
            s.run_frame()
        self.s, self.m = s, s.mem
        self.upd = 0
        self.pending = []
        self.pending_info = []
        s.add_pc_hook(0x5E91, self._on_callback)
        for a, name in self.EVENTS.items():
            s.add_pc_hook(a, self._event(name))
        self.e = P.Emu.__new__(P.Emu)
        self.e.s, self.e.rom, self.e.act = s, rom, key
        self.e._place = P._load("spring_interaction")._place
        self.e.base = self.e.snapshot()

    def _on_callback(self, mm):
        if mm.cpu.ix == 0xD500:
            self.upd += 1

    def _event(self, name):
        def fn(mm):
            self.pending.append(name)
            self.pending_info.append((name, mm.mem[0xD501], mm.mem[0xD12F]))
        return fn

    def place(self, x, y, vx=0, vy=0, cur=5, f3=0, floor=True, prev=0x82, p24=None, k=None, rings=0, d532=None, d3b1=None, inv=False, d3c0=None):
        self.e.restore()
        self.e.place(x, y, vx, vy, cur=cur, f3=f3, floor=floor, rings=rings, prev=prev)
        m = self.m
        m[0xD501] = cur
        if p24 is not None:
            m[0xD524] = p24
        if k is not None:
            m[0xD3BC] = k
        if d532 is not None:
            m[0xD532] = d532
        if d3b1 is not None:
            m[0xD3B1] = d3b1
        if inv:
            m[0xD503] |= 0x80
        if d3c0 is not None:
            m[0xD3C0] = d3c0
        self.upd = 0
        self.pending = []
        self.pending_info = []

    def row(self) -> dict:
        s, m = self.s, self.m
        r = {"u": self.upd, "fr": s.frame, "x": s.u16(0xD511), "y": s.u16(0xD514), "vx": s16(s.u16(0xD516)), "vy": s16(s.u16(0xD518)), "cur": m[0xD501], "req": m[0xD502], "f3": m[0xD503],
             "f22": m[0xD522], "f23": m[0xD523], "p24": m[0xD524], "k": m[0xD3BC], "d36c": m[0xD36C], "d36b": m[0xD36B], "d12f": m[0xD12F], "sy": s16(s.u16(0xD51C)),
             "cam": s.u16(0xD176), "rings": m[0xD29A], "d3b1": m[0xD3B1], "d3c0": m[0xD3C0], "ev": list(self.pending), "ev_info": list(self.pending_info)}
        self.pending.clear()
        self.pending_info.clear()
        return r

    def run(self, frames: int, padf=None, stop=None) -> list:
        """One row per player update (the frame loop may contain lag frames with no update)."""
        rows, last = [], self.upd
        for f in range(frames):
            self.s.pad = padf(self.upd, f) if padf else 0
            self.s.run_frame()
            if self.upd != last:
                last = self.upd
                rows.append(self.row())
                if stop and stop(rows[-1], rows):
                    break
        return rows


# --------------------------------------------------------------------------- #
# 4. surface $1B scenarios
# --------------------------------------------------------------------------- #
OIL_TOP = {"mghz1": 800, "mghz2": 928}          # world Y of the first oil row (rows 25 / 29)
RIM_TOP = {"mghz1": 768, "mghz2": 896}          # solid rim row above-left/right of the pit (one cell higher than the oil)
PIT_X = {"mghz1": (1344, 1663), "mghz2": (224, 671)}   # oil columns 42..51 / 7..20


def milestones(rows: list) -> dict:
    out = {"updates": len(rows)}
    oil = [r for r in rows if "oil" in r["ev"]]
    out["first_oil_handler_update"] = oil[0]["u"] if oil else None
    sink = [r for r in rows if "sink" in r["ev"]]
    out["first_sink_branch_update"] = sink[0]["u"] if sink else None
    inc = [r["u"] for i, r in enumerate(rows) if i and r["k"] > rows[i - 1]["k"] and r["k"] - rows[i - 1]["k"] == 1]
    out["counter_increment_updates_first8"] = inc[:8]
    out["counter_increment_gaps_first8"] = [b - a for a, b in zip(inc, inc[1:8])]
    d12f_at = []
    for i, r in enumerate(rows):
        if i and r["k"] - rows[i - 1]["k"] == 1:
            d12f_at.append(next((x[2] for x in r["ev_info"] if x[0] == "oil"), None))
    out["counter_increment_d12f_at_handler_first8"] = d12f_at[:8]
    out["counter_increment_d12f_low2_all_zero"] = all(v is not None and v & 3 == 0 for v in d12f_at)
    out["counter_increment_d12f_gaps_first8"] = [(b - a) & 255 for a, b in zip(d12f_at, d12f_at[1:9])]
    plunge = next((r for i, r in enumerate(rows) if i and "sink" in r["ev"] and r["y"] - rows[i - 1]["y"] >= 20), None)
    out["plunge_update"] = plunge["u"] if plunge else None
    out["plunge_counter"] = rows[rows.index(plunge) - 1]["k"] if plunge else None
    out["plunge_y_path"] = [r["y"] for r in rows[rows.index(plunge) - 1:rows.index(plunge) + 5]] if plunge else None
    dth = next((r for r in rows if r["req"] == 0x1F or r["cur"] == 0x1F), None)
    out["death_request_update"] = dth["u"] if dth else None
    out["death_screen_y_before"] = rows[rows.index(dth) - 1]["sy"] if dth and rows.index(dth) else None
    out["final"] = {k: rows[-1][k] for k in ("u", "x", "y", "k", "cur", "p24", "sy")}
    return out


def scenario_fall_in(lab: GameLab) -> dict:
    key = lab.key
    cx = (PIT_X[key][0] + PIT_X[key][1]) // 2
    lab.place(cx, OIL_TOP[key] - 18 - 60, 0, 0, cur=0x0E, f3=1, floor=False, prev=0)
    rows = lab.run(500, stop=lambda r, rs: r["cur"] == 0x1F)
    m = milestones(rows)
    first = next(r for r in rows if "oil" in r["ev"])
    i = rows.index(first)
    m["landing_rows"] = [{k: r[k] for k in ("u", "y", "vy", "cur", "f22", "p24", "k", "d36c", "ev")} for r in rows[i - 1:i + 4]]
    m["start"] = {"x": cx, "y": OIL_TOP[key] - 18 - 60, "state": "0x0E"}
    return m


def scenario_walk_in(lab: GameLab, vx: int, cur: int, label: str) -> dict:
    key = lab.key
    x0 = PIT_X[key][0] - 44
    lab.place(x0, RIM_TOP[key] - 18, vx, 0, cur=cur, f3=2 if cur == 9 else 0, floor=True, prev=0x82)
    rows = lab.run(500, padf=lambda u, f: GameLab.PAD["RIGHT"], stop=lambda r, rs: r["cur"] == 0x1F)
    m = milestones(rows)
    m["label"] = label
    m["start"] = {"x": x0, "y": RIM_TOP[key] - 18, "vx": vx, "state": h(cur, 2)}
    return m


def _stand_on_oil(lab: GameLab, x: int, k: int, cur: int = 1, f3: int = 0, vx: int = 0) -> None:
    """Sonic grounded on the oil with sink counter k: the steady-state projected anchor is oil top - 4 + k - 18 (verified by the parity sweep)."""
    key = lab.key
    lab.place(x, OIL_TOP[key] - 22 + k, vx, 0x700, cur=cur, f3=f3, floor=True, prev=0x5B, p24=2, k=k)


def scenario_jump_cycle(lab: GameLab, wait: int) -> dict:
    """Press jump (one update) `wait` updates after standing on the oil; then watch the landing and the counter."""
    key = lab.key
    x = (PIT_X[key][0] + PIT_X[key][1]) // 2
    _stand_on_oil(lab, x, 0)
    jumped = {"u": None}

    def pad(u, f):
        if u >= wait and jumped["u"] is None:
            jumped["u"] = u
        return GameLab.PAD["B1"] if jumped["u"] is not None and u == jumped["u"] else 0
    rows = lab.run(300, padf=pad, stop=lambda r, rs: r["cur"] == 0x1F or r["u"] > wait + 120)
    j = next((i for i, r in enumerate(rows) if r["cur"] == 0x0A), None)
    out = {"wait_updates": wait, "jump_taken": j is not None}
    if j is not None:
        kmax = max(r["k"] for r in rows[:j])
        air = rows[j:]
        apex = min(r["y"] for r in air)
        cleared = next((i for i, r in enumerate(air) if not r["p24"] & 2), None)
        land = next((i for i, r in enumerate(air) if i > 3 and "sink" in r["ev"] and r["vy"] >= 0 and r["f22"] & 2), None)
        out.update({"counter_just_before_jump": kmax, "counter_in_first_jump_row": rows[j]["k"], "counter_reset_by_jump_setter": kmax > 0 and rows[j]["k"] == 0,
                    "plus24_bit1_cleared_after_airborne_updates": cleared, "y_before_jump": rows[j - 1]["y"], "apex_y": apex, "rise_px": rows[j - 1]["y"] - apex, "jump_vy_first": rows[j]["vy"],
                    "f3_first": rows[j]["f3"], "relanded_update": air[land]["u"] if land is not None else None, "counter_at_reland": air[land]["k"] if land is not None else None,
                    "y_at_reland": air[land]["y"] if land is not None else None})
    out["final"] = {k: rows[-1][k] for k in ("u", "y", "k", "cur", "p24")}
    return out


def scenario_escape(lab: GameLab, k0: int) -> dict:
    """Standing on the oil beside the far rim wall with counter k0: hold RIGHT and jump.  Does Sonic end up on the far rim?"""
    key = lab.key
    xr = PIT_X[key][1] + 1                      # first solid column of the far rim
    x = xr - 40
    _stand_on_oil(lab, x, k0)
    state = {"j": None}

    def pad(u, f):
        if state["j"] is None and u >= 2:
            state["j"] = u
        return GameLab.PAD["RIGHT"] | (GameLab.PAD["B1"] if u == state["j"] else 0)
    rows = lab.run(240, padf=pad, stop=lambda r, rs: r["cur"] == 0x1F or r["u"] > 80)
    on_rim = [r for r in rows if r["x"] >= xr + 4 and r["f22"] & 2 and r["y"] <= RIM_TOP[key] - 18 + 1]
    return {"counter_at_jump": k0, "reached_far_rim": bool(on_rim), "max_x": max(r["x"] for r in rows), "min_y": min(r["y"] for r in rows), "died": rows[-1]["cur"] == 0x1F,
            "final": {k: rows[-1][k] for k in ("u", "x", "y", "k", "cur", "p24")}}


def patch_layout(lab: GameLab, cells: dict) -> None:
    """Overwrite runtime layout cells {(col,row): block} AFTER place() (the snapshot restore resets them)."""
    width = I.act_data(lab.rom, lab.key)["width"]
    for (cx, cy), blk in cells.items():
        lab.m[0xC001 + cy * width + cx] = blk


def oil_cells(rom: bytes, key: str) -> list:
    a = I.act_data(rom, key)
    return [(i % a["width"], i // a["width"]) for i, v in enumerate(a["cells"][:4095]) if v == OIL_BLOCK]


def scenario_speed_control(lab: GameLab) -> dict:
    """Does the oil change horizontal speed?  Same input, same place, same frame phase: the oil cells versus the same cells patched to ordinary solid block $01."""
    out = {}
    key = lab.key
    cells = oil_cells(lab.rom, key)
    solid = {c: 0x01 for c in cells}
    for name, direction, x0, vx0 in (("right", "RIGHT", 1400, 0), ("left", "LEFT", 1620, 0), ("right_from_run", "RIGHT", 1400, 0x600)):
        seqs = {}
        for where in ("oil", "solid_control"):
            _stand_on_oil(lab, x0, 0, cur=5, vx=vx0)
            if where == "solid_control":
                patch_layout(lab, solid)
                lab.m[0xD524] = 0
                lab.m[0xD36C] = 0x81
            rows = lab.run(80, padf=lambda u, f, d=direction: GameLab.PAD[d], stop=lambda r, rs: len(rs) >= 40)
            seqs[where] = {"vx": [r["vx"] for r in rows[:40]], "y": [r["y"] for r in rows[:40]], "x": [r["x"] for r in rows[:40]]}
        out[name] = {"vx_oil_first12": seqs["oil"]["vx"][:12], "vx_solid_first12": seqs["solid_control"]["vx"][:12],
                     "vx_identical_first40": seqs["oil"]["vx"] == seqs["solid_control"]["vx"], "x_identical_first40": seqs["oil"]["x"] == seqs["solid_control"]["x"],
                     "y_range_oil": [min(seqs["oil"]["y"]), max(seqs["oil"]["y"])], "y_range_solid": [min(seqs["solid_control"]["y"]), max(seqs["solid_control"]["y"])]}
    return out


def scenario_roll_on_oil(lab: GameLab) -> dict:
    key = lab.key
    x = PIT_X[key][0] + 60
    _stand_on_oil(lab, x, 0, cur=9, f3=2, vx=0x400)
    rows = lab.run(120, padf=lambda u, f: 0, stop=lambda r, rs: len(rs) >= 60)
    walk_lab = rows
    return {"states_seen": sorted({h(r["cur"], 2) for r in rows}), "f3_values_seen": sorted({h(r["f3"], 2) for r in rows}), "all_rows_supported_f22_bit1": all(r["f22"] & 2 for r in rows[2:]),
            "counter_after_60_updates": rows[-1]["k"], "y_after_60_updates": rows[-1]["y"], "y_first6": [r["y"] for r in rows[:6]], "vx_first8": [r["vx"] for r in rows[:8]]}


def scenario_direction_independence(lab: GameLab) -> dict:
    out = {}
    key = lab.key
    cx = (PIT_X[key][0] + PIT_X[key][1]) // 2
    for name, pad in (("neutral", 0), ("hold_left", GameLab.PAD["LEFT"]), ("hold_right", GameLab.PAD["RIGHT"]), ("hold_down", GameLab.PAD["DOWN"]), ("hold_up", GameLab.PAD["UP"])):
        lab.place(cx, OIL_TOP[key] - 18 - 20, 0, 0, cur=0x0E, f3=1, floor=False, prev=0)
        rows = lab.run(400, padf=lambda u, f, p=pad: p, stop=lambda r, rs: r["req"] == 0x1F or r["cur"] == 0x1F)
        ms = milestones(rows)
        out[name] = {k: ms[k] for k in ("first_oil_handler_update", "plunge_update", "plunge_counter", "death_request_update")}
        out[name]["frames_first_oil_to_plunge"] = next(r["fr"] for r in rows if r["u"] == ms["plunge_update"]) - next(r["fr"] for r in rows if r["u"] == ms["first_oil_handler_update"])
    return out


def scenario_after_death(lab: GameLab) -> dict:
    """Run to the oil death, then let the game restart the act: the player slot is re-initialised (counter and +$24 bit 1 return to 0)."""
    scenario_fall_in(lab)
    m = lab.m
    at_death = {"counter": m[0xD3BC], "plus24": m[0xD524], "state": m[0xD501]}
    for _ in range(900):
        lab.s.pad = 0
        lab.s.run_frame()
    return {"at_death": at_death, "after_restart": {"counter": m[0xD3BC], "plus24": m[0xD524], "state": m[0xD501], "x": lab.s.u16(0xD511), "y": lab.s.u16(0xD514), "zone": m[0xD297], "act": m[0xD298]}}


# --------------------------------------------------------------------------- #
# 5. surface $1B: controlled-routine models and sweeps
# --------------------------------------------------------------------------- #
def gate_model(prev: int, p24: int, req: int) -> str:
    """Which branch of $6F61 handles the PREVIOUS-flags case (byte-verified at $6F61..$6FC7)."""
    if prev & 0x80:
        return "solid"
    if prev & 0x40:
        if (p24 & 1) and req == 0x14:
            return "strip_fall_no_support"
        if p24 & 2:
            return "sink"
        return "one_way"
    return "none"


def sink_model(y: int, vy_negative: bool, floor: bool, d35a: int, profile: int, k: int, b: int) -> dict:
    """Python model of the sink branch $7010..$7055 (inputs are the lookup outputs D35A/D368 and the player state)."""
    if vy_negative:
        return {"y": y, "floor": floor, "applied": False, "d35a": d35a}
    d35a = (d35a + 4) & 0xFFFF
    c = d35a & 0x1F
    a = (profile + c) & 0xFF
    if a < 0x20:
        return {"y": y, "floor": False, "applied": False, "d35a": d35a}
    a = (a - 0x20) & 0xFF
    if a >= b:
        return {"y": y, "floor": False, "applied": False, "d35a": d35a}
    return {"y": (y - a + k) & 0xFFFF, "floor": True, "applied": True, "d35a": d35a, "penetration": a}


def hhi(rom: bytes, blk: int) -> int:
    return (R.header(rom, blk)["horizontal_pointer"] - 0x30000) >> 8


PREVS = (0x00, 0x01, 0x41, 0x5B, 0x81, 0x82, 0xC1)


def gate_matrix(rom: bytes) -> dict:
    lab = Lab(rom, "mghz1")
    rows, bad = [], 0
    for prev in PREVS:
        for p24 in (0, 1, 2, 3):
            for req in (5, 0x14):
                for vy in (-0x100, 0, 0x700):
                    for floor in (False, True):
                        r = lab.go(1360, 792, vy=vy, floor=floor, prev=prev, cur=5, req=req, p24=p24, k=7, entry=FLOOR_PROJECTION, lookup_first=True)
                        want = gate_model(prev, p24, req)
                        got_sink = "sink_branch" in r["hits"]
                        if got_sink != (want == "sink"):
                            bad += 1
                        rows.append((prev, p24, req, vy, floor, got_sink))
    summary = {}
    for prev in PREVS:
        for p24 in (0, 1, 2, 3):
            for req in (5, 0x14):
                sel = [r for r in rows if r[0] == prev and r[1] == p24 and r[2] == req]
                summary[f"prev={h(prev, 2)} p24={p24} req={h(req, 2)}"] = {"model": gate_model(prev, p24, req), "sink_branch_reached_in": sum(1 for r in sel if r[5]), "of": len(sel)}
    return {"evidence": "CONTROLLED ROUTINE RESULT ($7666 then $6F61 on the MGHZ1 oil block, watch point at $7010)", "cases": len(rows), "model_mismatches": bad, "summary": summary,
            "rule": "sink branch <=> previous flags have bit 6 and not bit 7, +$24 bit 1 set, and NOT (+$24 bit 0 and requested state $14); inside it a negative Y speed (+$19 bit 7) returns before touching anything"}


def sink_parity(rom: bytes) -> dict:
    lab = Lab(rom, "mghz1")
    blocks = bit6_only_blocks(rom)
    cases = applied = mismatches = 0
    per_block, examples = {}, []
    for blk in blocks:
        n = a = 0
        for col in (0, 8, 16, 24, 31):
            x = 42 * 32 + col
            for dy in range(-6, 35):
                y = 800 - 18 + dy
                for k in (0, 4, 12, 25, 32, 200):
                    for vy in (-1, 0, 0x700):
                        r = lab.go(x, y, vy=vy, floor=True, prev=R.header(rom, blk)["flags"], cur=5, req=5, p24=2, k=k, entry=FLOOR_PROJECTION, lookup_first=True,
                                   patch={(42, 25): blk})
                        want = sink_model(y, vy < 0, True, y + 18, r["profile"], k, hhi(rom, blk))
                        ok = r["y"] == want["y"] and r["floor"] == want["floor"] and (vy < 0 or r["d35a"] == want["d35a"]) and ("sink_branch" in r["hits"])
                        n += 1
                        a += want["applied"]
                        if not ok:
                            mismatches += 1
                            if len(examples) < 5:
                                examples.append({"block": h(blk, 2), "x": x, "y": y, "k": k, "vy": vy, "got": [r["y"], r["floor"], r["d35a"]], "want": [want["y"], want["floor"], want["d35a"]]})
        per_block[h(blk, 2)] = {"cases": n, "projected": a}
        cases += n
        applied += a
    return {"evidence": "CONTROLLED ROUTINE RESULT (every bit-6-only block patched into MGHZ1 cell (42,25); real routines $7666 + $6F61; Python model of $7010 compared)",
            "cases": cases, "projected_cases": applied, "mismatches": mismatches, "mismatch_examples": examples, "per_block": per_block,
            "model": {"gate": "bit6 && !bit7 && +$24.1 && !(+$24.0 && req==$14)", "negative_y_speed": "return before clearing anything",
                      "else": "floor flag cleared; D35A += 4; C := D35A & 31; A := D368 + C (8-bit); A < 32 -> return (floor flag stays cleared); A -= 32; A >= B -> return; Y := Y - A + $D3BC; floor flag set; $64CB; D369 := D100"}}


def steady_state(rom: bytes) -> dict:
    """The grounded update cycle on the oil: Y integration (+7, or +9 with modifier 10/12) then the sink projection; where does it run away?"""
    lab = Lab(rom, "mghz1")
    out = {}
    for integ in (7, 9):
        path, crit = [], None
        for k in range(0, 45):
            y = 800 - 22 + k                                    # projected steady anchor Y for counter k
            r = lab.go(1360, y + integ, vy=integ * 256, floor=True, prev=0x5B, cur=5, req=5, p24=2, k=k, entry=FLOOR_PROJECTION, lookup_first=True)
            step = r["y"] - y
            path.append((k, y, r["y"], step, r["floor"]))
            if crit is None and step >= 20:
                crit = k
        out[f"integration_{integ}"] = {"first_runaway_counter": crit, "anchor_y_after_projection_by_counter_0_to_24": [p[2] for p in path if p[0] <= 24],
                                       "rows_around_runaway_[counter,anchor_before,anchor_after,step,floor]": [list(p) for p in path if crit is not None and crit - 2 <= p[0] <= crit + 2]}
    return {"evidence": "CONTROLLED ROUTINE RESULT", "oil_top_world_y": 800, "steady_anchor_y_formula": "oil_top - 22 + counter (foot probe = anchor + 18 sits at oil_top - 4 + counter)",
            "runaway_rule": "grounded Y integration is +7, so the integrated probe row is (counter + 7) >= 32, i.e. counter >= 25: the projection then reads row 0..6 of the NEXT block and adds the full counter: ~+32 px per update",
            "cases": out}


def stale_bit_one_way(rom: bytes) -> dict:
    """+$24 bit 1 survives on ordinary ground and changes the projection of any other bit-6-only (one-way) block."""
    lab = Lab(rom, "mghz1")
    out = {}
    probes = (-3, 0, 2, 6, 10, 20)
    for blk in (0x0D, 0x0F, 0xF9):
        rows = {}
        for label, p24, k in (("bit1_clear", 0, 0), ("bit1_set_k0", 2, 0), ("bit1_set_k10", 2, 10), ("bit1_set_k25", 2, 25)):
            ys = []
            for dy in probes:
                r = lab.go(1360, 800 - 18 + dy, vy=0x700, floor=True, prev=0x41, cur=5, req=5, p24=p24, k=k, entry=FLOOR_PROJECTION, lookup_first=True, patch={(42, 25): blk})
                ys.append(r["y"] - (800 - 18))
            rows[label] = ys
        out[h(blk, 2)] = {"probe_rows_dy": list(probes), "final_anchor_y_minus_surface_anchor": rows}
    return {"evidence": "CONTROLLED ROUTINE RESULT", "results": out,
            "reading": "with +$24 bit 1 clear a one-way block puts the anchor at (surface - 18) for probes at or below the top; with the stale bit set it lands at surface - 18 - 4 + counter"}



# --------------------------------------------------------------------------- #
# 6. ceiling spikes: controlled sweeps
# --------------------------------------------------------------------------- #
# An isolated test cell inside the large all-air room of MGHZ2 (cells (27..43, 12..18) are block $2F): column 30, row 13, origin (960, 416).
TEST_CELL = (30, 13)
TEST_KEY = "mghz2"


def test_origin() -> tuple:
    return TEST_CELL[0] * 32, TEST_CELL[1] * 32


def ceiling_runs(rom: bytes) -> dict:
    """Contiguous horizontal runs of $3E/$3F cells per act with their vertical neighbours (census of the real placements)."""
    out = {}
    for key in ACTS:
        a = I.act_data(rom, key)
        w = a["width"]
        cells = a["cells"][:4095]
        found = sorted((i // w, i % w, v) for i, v in enumerate(cells) if v in SPIKE_CEILING_BLOCKS)
        runs, cur = [], None
        for row, col, v in found:
            if cur and cur["row"] == row and col == cur["col1"] + 1 and v == cur["block"]:
                cur["col1"] = col
            else:
                cur = {"row": row, "col0": col, "col1": col, "block": v}
                runs.append(cur)
        rows = []
        for r in runs:
            above = sorted({cells[(r["row"] - 1) * w + c] for c in range(r["col0"], r["col1"] + 1)})
            below = sorted({cells[(r["row"] + 1) * w + c] for c in range(r["col0"], r["col1"] + 1)}) if r["row"] + 1 < len(cells) // w else []
            rows.append({"block": h(r["block"], 2), "cells": [r["col0"], r["col1"], r["row"]], "world_x_range": [r["col0"] * 32, r["col1"] * 32 + 31], "cell_top_world_y": r["row"] * 32,
                         "count": r["col1"] - r["col0"] + 1, "blocks_above": [h(b, 2) for b in above], "above_is_solid": all(R.header(rom, b)["flags"] & 0x80 for b in above),
                         "blocks_below": [h(b, 2) for b in below], "below_is_air": all(R.header(rom, b)["flags"] & 0x1F == 0 and not R.header(rom, b)["flags"] & 0x80 for b in below),
                         "hazard_anchor_y_range": [r["row"] * 32 + 6, r["row"] * 32 + 30], "hazard_anchor_x_range": [r["col0"] * 32, r["col1"] * 32 + 31]})
        out[key] = rows
    return out


def ceiling_gate_sweep(rom: bytes) -> dict:
    """Ceiling pass $73C9 only on the isolated test cell, for BOTH blocks: Y-speed class x floor flag x support owner x invulnerability bit x current state."""
    out, total = {}, 0
    lab = Lab(rom, TEST_KEY)
    ox, oy = test_origin()
    for blk in SPIKE_CEILING_BLOCKS:
        combos = {}
        for vy_name, vy in (("rising_-1.0", -0x100), ("rising_-1/256", -1), ("zero", 0), ("falling_+1.0", 0x100)):
            for floor in (False, True):
                for d3c0 in (0, 9):
                    for inv in (False, True):
                        for cur in (0x0A, 0x1E):
                            hit, push, bounce, t5 = set(), set(), set(), set()
                            for x in range(ox - 12, ox + 44):
                                for y in range(oy - 12, oy + 45):
                                    r = lab.go(x, y, vy=vy, floor=floor, d3c0=d3c0, inv=inv, cur=cur, entry=0x73C9, f3=1, patch={TEST_CELL: blk})
                                    total += 1
                                    if "hurt" in r["hits"]:
                                        hit.add((x - ox, y - oy))
                                    if r["y"] != y:
                                        push.add((x - ox, y - oy))
                                    if "ceiling_bounce" in r["hits"]:
                                        bounce.add((x - ox, y - oy))
                                    if "ceiling_type5" in r["hits"]:
                                        t5.add((x - ox, y - oy))
                            name = f"vy={vy_name}|floor={int(floor)}|owner={d3c0}|invulnerable={int(inv)}|state={h(cur, 2)}"
                            combos[name] = {"hurt": rects(hit), "type5_tail_reached": rects(t5), "pushed_down": rects(push), "ordinary_bounce_path": rects(bounce)}
        out[h(blk, 2)] = combos
    return {"evidence": "CONTROLLED ROUTINE RESULT ($73C9 on the real MGHZ2 layout with the test cell patched; watch points $48F7, $74E7, $7459)", "cases": total,
            "test_cell": {"cell": list(TEST_CELL), "origin_world": [ox, oy], "neighbours": "all air ($2F)"},
            "coordinates": "[x0,x1,y0,y1] relative to the cell origin; x = anchor X (the ceiling probe is the anchor column, no width); y = anchor Y; probe row = y - 6", "results": out}


def want_ceiling_hit(parts: dict) -> bool:
    airborne_rising = parts["vy"].startswith("rising") and parts["floor"] == "0"
    return (airborne_rising or parts["owner"] != "0") and parts["invulnerable"] == "0" and parts["state"] != "0x1E"


def ceiling_gate_summary(sweep: dict) -> dict:
    """Condense the sweep to the implementation rule and check it holds in every combination for both blocks."""
    ok_all, identical_blocks = True, True
    for combo in sweep["results"]["0x3E"]:
        parts = dict(p.split("=") for p in combo.split("|"))
        for blk in ("0x3E", "0x3F"):
            got = sweep["results"][blk][combo]["hurt"]
            ok_all &= (got == [[0, 31, 6, 30]]) if want_ceiling_hit(parts) else (got == [])
        identical_blocks &= sweep["results"]["0x3E"][combo] == sweep["results"]["0x3F"][combo]
    return {"rule": "hurt <=> head probe (X, Y-6) in a $3E/$3F cell at row 0..24 (anchor Y = cell top + 6..30), any column of the cell (anchor X = cell left .. +31), "
                    "AND ((Y speed negative AND floor flag clear) OR support owner $D3C0 != 0), AND +$03 bit 7 clear, AND current state != $1E",
            "damage_rectangle_anchor_relative_to_cell_origin": {"x": [0, 31], "y": [6, 30]}, "rule_holds_for_every_combination_and_both_blocks": ok_all,
            "blocks_3e_and_3f_give_identical_results_in_every_combination": identical_blocks}


def ceiling_real_runs_check(rom: bytes) -> dict:
    """Every real $3E/$3F run (neighbours included): a rising jump-state anchor hurts exactly inside run x-range x [cell top + 6, +30]."""
    out = {}
    for key, runs in ceiling_runs(rom).items():
        lab = Lab(rom, key)
        for r in runs:
            x0, x1 = r["world_x_range"]
            top = r["cell_top_world_y"]
            hit = set()
            for x in range(x0 - 12, x1 + 13):
                for y in range(top - 8, top + 38):
                    res = lab.go(x, y, vy=-0x300, floor=False, cur=0x0A, f3=3, entry=0x73C9)
                    if "hurt" in res["hits"]:
                        hit.add((x, y))
            out[f"{key}:{r['block']}@cells{r['cells']}"] = {"hurt_[x0,x1,y0,y1]_world_anchor": rects(hit), "expected": [[x0, x1, top + 6, top + 30]], "matches": rects(hit) == [[x0, x1, top + 6, top + 30]]}
    return {"evidence": "CONTROLLED ROUTINE RESULT (real layouts, ceiling pass)", "results": out}


def ceiling_pass_vs_full(rom: bytes) -> dict:
    """The complete terrain pass versus the isolated ceiling pass on the test cell (rising jump state): only the side probes (which run first) may differ."""
    lab = Lab(rom, TEST_KEY)
    ox, oy = test_origin()
    full, iso = set(), set()
    for x in range(ox - 14, ox + 46):
        for y in range(oy - 14, oy + 48):
            a = lab.go(x, y, vy=-0x300, floor=False, cur=0x0A, entry=0x690B, f3=3, patch={TEST_CELL: 0x3F})
            b = lab.go(x, y, vy=-0x300, floor=False, cur=0x0A, entry=0x73C9, f3=3, patch={TEST_CELL: 0x3F})
            if "hurt" in a["hits"]:
                full.add((x - ox, y - oy))
            if "hurt" in b["hits"]:
                iso.add((x - ox, y - oy))
    return {"evidence": "CONTROLLED ROUTINE RESULT", "full_pass_hurt": rects(full), "isolated_ceiling_pass_hurt": rects(iso), "only_in_isolated_pass": rects(iso - full), "only_in_full_pass": rects(full - iso),
            "reading": "the side probes run before the ceiling probe in $690B and can push X (rows 0..15 of the cell) out of the column first, so a player grazing a cell edge from the side can avoid the hurt; the isolated rule is exact for the head column"}


def ceiling_foot_sweep(rom: bytes) -> dict:
    """Foot probe ($691A) on the isolated cell for BOTH blocks: where does a LANDING hurt?  Previous surface x floor flag x Y speed class."""
    out, n = {}, 0
    lab = Lab(rom, TEST_KEY)
    ox, oy = test_origin()
    for blk in SPIKE_CEILING_BLOCKS:
        res = {}
        for pname, prev in (("none_00", 0x00), ("solid_81", 0x81), ("spike_85", 0x85)):
            for floor in (False, True):
                for vname, vy in (("rising_-1.0", -0x100), ("zero", 0), ("descending_+1.0", 0x100), ("fast_+7.0", 0x700)):
                    cells, pushed = set(), set()
                    for x in range(ox - 4, ox + 36):
                        for foot in range(oy - 8, oy + 40):
                            r = lab.go(x, foot - 18, vy=vy, floor=floor, prev=prev, cur=0x0A, entry=0x691A, f3=1, patch={TEST_CELL: blk})
                            n += 1
                            if "hurt" in r["hits"]:
                                cells.add((x - ox, foot - oy))
                            if r["y"] != foot - 18:
                                pushed.add((x - ox, foot - oy))
                    res[f"prev={pname}|floor={int(floor)}|vy={vname}"] = {"hurt": rects(cells), "projected": rects(pushed)}
        out[h(blk, 2)] = res
    identical = out["0x3E"] == out["0x3F"]
    return {"evidence": "CONTROLLED ROUTINE RESULT", "cases": n, "coordinates": "[x0,x1,foot_row_y0,y1] relative to the cell origin; foot row = anchor Y + 18", "blocks_3e_3f_identical": identical, "results": out["0x3F"]}


def ceiling_side_sweep(rom: bytes) -> dict:
    """Side probes ($715E) at both edges of the isolated cell for BOTH blocks: walls, damage."""
    out, n = {}, 0
    lab = Lab(rom, TEST_KEY)
    ox, oy = test_origin()
    for blk in SPIKE_CEILING_BLOCKS:
        right, left, dmg = set(), set(), 0
        for y in range(oy - 12, oy + 44):
            for x in range(ox - 20, ox + 12):
                r = lab.go(x, y, vx=0x200, vy=0, floor=False, cur=0x0A, f3=3, entry=0x715E, patch={TEST_CELL: blk})
                n += 1
                dmg += "hurt" in r["hits"]
                if r["x"] != x:
                    right.add((x - ox, y + 6 - oy))
            for x in range(ox + 20, ox + 52):
                r = lab.go(x, y, vx=-0x200, vy=0, floor=False, cur=0x0A, f3=3, entry=0x715E, patch={TEST_CELL: blk})
                n += 1
                dmg += "hurt" in r["hits"]
                if r["x"] != x:
                    left.add((x - ox, y + 6 - oy))
        out[h(blk, 2)] = {"right_probe_pushes_[dx,dx,probe_row,probe_row]": rects(right), "left_probe_pushes": rects(left), "side_damage_cases": dmg}
    return {"evidence": "CONTROLLED ROUTINE RESULT", "cases": n, "coordinates": "[x0,x1,y0,y1]: x = anchor X relative to the cell origin, y = side probe row (anchor Y + 6) relative to the cell top", "results": out,
            "blocks_3e_3f_identical": out["0x3E"] == out["0x3F"],
            "reading": "side contact never hurts a $3E/$3F cell (damage is reserved for tiles $F4/$F5); the wall exists only for probe rows 0..15 of the cell (horizontal profile $60 there, $40 below)"}


# --------------------------------------------------------------------------- #
# 7. ceiling spikes: whole-game scenarios and state coverage
# --------------------------------------------------------------------------- #
CEIL_X = 1000                       # MGHZ2 corridor run (cells 27..43, row 11), cell top y = 352, tip row = anchor 382
CEIL_TOP = 352


def _ceiling_rows(lab: GameLab, y0: int, vy: int, cur: int, f3: int, rings: int, frames: int = 140, stop_after_hurt: int = 8, **kw) -> list:
    lab.place(CEIL_X, y0, 0, vy, cur=cur, f3=f3, floor=False, prev=0, rings=rings, **kw)
    seen = {"n": None}

    def stop(r, rs):
        if "hurt" in r["ev"] and seen["n"] is None:
            seen["n"] = len(rs)
        return (seen["n"] is not None and len(rs) >= seen["n"] + stop_after_hurt) or len(rs) > 90
    return lab.run(frames, stop=stop)


def _compact(r: dict) -> dict:
    return {k: r[k] for k in ("u", "y", "vx", "vy", "cur", "req", "f3", "f22", "f23", "rings", "d3b1", "ev")}


def scenario_ceiling_hit(lab: GameLab, rings: int, label: str, **kw) -> dict:
    rows = _ceiling_rows(lab, CEIL_TOP + 46, -0x300, 0x0A, 3, rings, **kw)
    i = next((j for j, r in enumerate(rows) if "hurt" in r["ev"]), None)
    b = next((j for j, r in enumerate(rows) if "bounce" in r["ev"]), None)
    out = {"label": label, "start": {"x": CEIL_X, "y": CEIL_TOP + 46, "vy": -0x300, "state": "0x0A", "rings_bcd": rings}, "hurt_reached": i is not None, "ordinary_bounce_reached": b is not None}
    if i is not None:
        out.update({"hurt_update": rows[i]["u"], "rows_around_hurt": [_compact(r) for r in rows[max(0, i - 3):i + 5]],
                    "anchor_y_at_hurt": rows[i]["y"], "pushed_to_tip_row": rows[i]["y"] == CEIL_TOP + 30})
    elif b is not None:
        out.update({"bounce_update": rows[b]["u"], "rows_around_bounce": [_compact(r) for r in rows[max(0, b - 2):b + 5]], "anchor_y_at_bounce": rows[b]["y"]})
    else:
        out["rows_last"] = [_compact(r) for r in rows[-3:]]
    return out


def scenario_ceiling_near_miss(lab: GameLab) -> dict:
    """A jump started 78 px under the tip peaks 1 px short: the type-5 tail is reached for 8 updates (probe rows 25..30) and nothing happens."""
    lab.place(CEIL_X, CEIL_TOP + 78, 0, -0x440, cur=0x0A, f3=3, floor=False, prev=0, rings=5)
    rows = lab.run(140, stop=lambda r, rs: len(rs) > 40 or "hurt" in r["ev"])
    t5 = [r for r in rows if "ceil5" in r["ev"]]
    return {"start": {"x": CEIL_X, "y": CEIL_TOP + 78, "vy": -0x440, "state": "0x0A"}, "type5_tail_updates": len(t5), "apex_y": min(r["y"] for r in rows), "head_probe_rows_at_apex": min(r["y"] for r in rows) - 6 - CEIL_TOP,
            "hurt": any("hurt" in r["ev"] for r in rows), "ceiling_bounce": any("bounce" in r["ev"] for r in rows), "rows_at_tail": [_compact(r) for r in t5[:3]]}


def scenario_ceiling_falling(lab: GameLab) -> dict:
    """Falling (Y speed >= 0) inside the damage rectangle: the ceiling pass returns at its entry gate."""
    lab.place(CEIL_X, CEIL_TOP + 20, 0, 0x100, cur=0x0E, f3=1, floor=False, prev=0, rings=5)
    rows = lab.run(60, stop=lambda r, rs: len(rs) > 6)
    return {"start": {"x": CEIL_X, "y": CEIL_TOP + 20, "vy": 0x100, "state": "0x0E"}, "hurt": any("hurt" in r["ev"] for r in rows), "type5_tail": any("ceil5" in r["ev"] for r in rows),
            "rows": [_compact(r) for r in rows[:5]]}


def scenario_ceiling_state_scan(lab: GameLab) -> dict:
    """Each player state forced (script pointer cleared so the engine loads it), Sonic rising inside the damage rectangle; events of the first three updates."""
    out = {}
    for st in range(0x37):
        lab.place(CEIL_X, CEIL_TOP + 31, 0, -0x300, cur=st, f3=1, floor=False, prev=0, rings=5)
        lab.m[0xD501] = st
        lab.m[0xD502] = st
        lab.m[0xD50E] = lab.m[0xD50F] = 0
        rows = lab.run(12, stop=lambda r, rs: len(rs) >= 3)
        info = [x for r in rows for x in r["ev_info"]]
        own = [x[0] for x in info if x[1] == st]
        ev = [x[0] for x in info]
        out[h(st, 2)] = {"ceiling_type5_reached_in_state": "ceil5" in own, "hurt_in_state": "hurt" in own, "ordinary_bounce_in_state": "bounce" in own,
                         "hurt_within_three_updates_any_state": "hurt" in ev, "bit7_set_by_state_scripts": any(r["f3"] & 0x80 for r in rows) and "hurt" not in ev,
                         "states_seen": sorted({h(r["cur"], 2) for r in rows})}
    return out


def scenario_oil_state_scan(lab: GameLab) -> dict:
    out = {}
    for st in range(0x37):
        lab.place(1360, 800 - 18 + 6, 0, 0x700, cur=st, f3=0, floor=True, prev=0x5B, p24=2, k=3)
        lab.m[0xD501] = st
        lab.m[0xD502] = st
        lab.m[0xD50E] = lab.m[0xD50F] = 0
        rows = lab.run(8, stop=lambda r, rs: len(rs) >= 1)
        info = rows[0]["ev_info"] if rows else []
        own = [x[0] for x in info if x[1] == st]
        out[h(st, 2)] = {"oil_handler": "oil" in own, "sink_branch": "sink" in own}
    return out


# --------------------------------------------------------------------------- #
# 8. MGHZ placements, examples and assembly
# --------------------------------------------------------------------------- #
def oil_pits(rom: bytes) -> dict:
    """Census of the real $A0 cells: rectangles, surroundings, world coordinates."""
    out = {}
    for key in ACTS:
        a = I.act_data(rom, key)
        w = a["width"]
        cells = a["cells"][:4095]
        coords = [(i % w, i // w) for i, v in enumerate(cells) if v == OIL_BLOCK]
        pits = []
        for x0, x1, y0, y1 in rects(coords):
            above = [cells[(y0 - 1) * w + c] for c in range(x0, x1 + 1)]
            left = [cells[r * w + x0 - 1] for r in range(y0, y1 + 1)]
            right = [cells[r * w + x1 + 1] for r in range(y0, y1 + 1)]
            rim_row = y0 - 1
            side_row = [cells[rim_row * w + x0 - 1], cells[rim_row * w + x1 + 1]]
            pits.append({"cells": [x0, x1, y0, y1], "count": (x1 - x0 + 1) * (y1 - y0 + 1), "world_rect": [x0 * 32, y0 * 32, x1 * 32 + 31, y1 * 32 + 31], "oil_top_world_y": y0 * 32,
                         "anchor_y_standing_at_counter_0": y0 * 32 - 22, "blocks_in_row_above_oil": sorted(h(b, 2) for b in set(above)),
                         "row_above_oil_collision": sorted({h(R.header(rom, b)["flags"] & 0x1F, 2) for b in above}),
                         "left_neighbour_blocks": sorted(h(b, 2) for b in set(left)), "right_neighbour_blocks": sorted(h(b, 2) for b in set(right)),
                         "rim_row_cells_just_outside_[left,right]": [h(b, 2) for b in side_row],
                         "roof_cells_in_row_above": [c for c in range(x0, x1 + 1) if R.header(rom, cells[(y0 - 1) * w + c])["flags"] & 0x80]})
        out[key] = {"oil_cells": len(coords), "pits": pits}
    return out


def bit6_cells(rom: bytes) -> dict:
    """Other bit-6-only (one-way) blocks in the MGHZ layouts: the only blocks a stale +$24 bit 1 can affect."""
    out = {}
    blocks = set(bit6_only_blocks(rom)) - {OIL_BLOCK}
    for key in ACTS:
        a = I.act_data(rom, key)
        w = a["width"]
        per = {}
        for i, v in enumerate(a["cells"][:4095]):
            if v in blocks:
                per.setdefault(h(v, 2), []).append([i % w, i // w])
        out[key] = {b: {"count": len(c), "first_cells": c[:4]} for b, c in sorted(per.items())}
    return out


def ceiling_probe_facts(rom: bytes) -> dict:
    """The probe offsets, read from the code bytes (not assumed)."""
    ld_de_ceiling = rom[0x73E0:0x73E3]
    ld_de_foot_add = rom[0x7690:0x7693]
    return {"evidence": "BYTE-VERIFIED ASSEMBLY",
            "ceiling_entry_gate": {"0x73C9": "RES 0,(IX+$22): ceiling flag cleared first", "0x73CD..0x73DC": "if $D3C0 == 0: return when floor flag (+$22.1) set; return when Y speed high byte (+$19) bit 7 is clear (not rising)", "owner_bypass": "$D3C0 != 0 skips both tests"},
            "ceiling_probe": {"bytes_at_0x73E0": ld_de_ceiling.hex(" "), "decoded_DE": s16(ld_de_ceiling[1] | ld_de_ceiling[2] << 8), "lookup_adds_to_Y": s16(ld_de_foot_add[1] | ld_de_foot_add[2] << 8),
                              "effective_probe": "(anchor X, anchor Y - 24 + 18) = (X, Y-6)", "block_row_hit_range_for_3e_3f": "probe row 0..24 inclusive (profile $58: bit 6 + 24; collision when 24 >= row)"},
            "type5_tail_74e7": ["C := D35A & 31 (probe row)", "B := D368 (vertical profile byte); A := B & $3F; return if A == 0", "if A != 32 and bit 6 of B clear: return", "return if A < C (row > height)",
                                "Y += A - C (pushes the anchor DOWN so the probe row becomes A = 24)", "+$22 bit 0 := 1; $64CB", "return if current state (+$01) == $1E",
                                "block (D353 & $FE) != $3E: JP $7459 (ordinary bounce)", "+$03 bit 7 set: JP $7459", "JP $48F7 (hurt)"],
            "ordinary_bounce_7459": "Y speed := +1.0 ($0100); ceiling flag (+$22 bit 0) := 0",
            "hurt_vertical_speed": "$48F7 sets Y speed $FC00 (-4.0) unless +$22 bit 0 is set, in which case $0100 (+1.0): ceiling-spike hurt therefore knocks the player DOWN at +1.0 (no ring rebound upwards)"}


def scenario_ceiling_spring_launch(lab: GameLab) -> dict:
    """MGHZ2 corridor: the type-$21 stomp bounce (-6.75, state $0B, reduced gravity) from the corridor floor reaches the ceiling spikes (placed badniks at (1040,590) and (1232,590))."""
    lab.place(CEIL_X, 566, 0, -0x6C0, cur=0x0B, f3=1, floor=False, prev=0, rings=5)
    rows = lab.run(200, stop=lambda r, rs: "hurt" in r["ev"] or len(rs) > 120)
    i = next((j for j, r in enumerate(rows) if "hurt" in r["ev"]), None)
    return {"start": {"x": CEIL_X, "y": 566, "vy": -0x6C0, "state": "0x0B (what a $21 top stomp leaves)", "rings_bcd": 5}, "hurt_reached": i is not None, "hurt_update": rows[i]["u"] if i is not None else None,
            "anchor_y_at_hurt": rows[i]["y"] if i is not None else None, "rise_px_before_hurt": 566 - rows[i]["y"] if i is not None else None,
            "rows_every_20": [_compact(r) for r in rows[::20]]}


def hazard_neighbours(rom: bytes, placements: dict) -> dict:
    """Mapped objects within 256 px (X) / 320 px (Y) of each real hazard rectangle: which other mechanics can deliver Sonic to it."""
    out = {}
    for key in ACTS:
        recs = I.act_data(rom, key)["objects"]
        rows = []
        for r in placements["ceiling_spike_runs"][key]:
            x0, x1 = r["world_x_range"]
            top = r["cell_top_world_y"]
            near = [{"type": o["type_id"], "parameter": o["parameter"], "world": [o["world_x"], o["world_y"]]} for o in recs
                    if x0 - 256 <= o["world_x"] <= x1 + 256 and top - 320 <= o["world_y"] <= top + 320 and o["type_id"] in ("0x28", "0x21", "0x1B", "0x10", "0x2F", "0x24", "0x2E", "0x26")]
            rows.append({"kind": "ceiling_spike_run", "cells": r["cells"], "nearby_objects": near})
        for p in placements["oil"][key]["pits"]:
            x0, y0, x1, y1 = p["world_rect"]
            near = [{"type": o["type_id"], "parameter": o["parameter"], "world": [o["world_x"], o["world_y"]]} for o in recs
                    if x0 - 256 <= o["world_x"] <= x1 + 256 and y0 - 320 <= o["world_y"] <= y1 + 320 and o["type_id"] in ("0x28", "0x21", "0x1B", "0x10", "0x2F", "0x24", "0x2E", "0x26", "0x09")]
            rows.append({"kind": "oil_pit", "cells": p["cells"], "nearby_objects": near})
        out[key] = rows
    return {"evidence": "DECODED DATA (placement geometry only; no gameplay observation)", "window": "|dx| <= 256 beyond the hazard x-range, |dy| <= 320", "results": out}


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    data = {"format": "mghz-surface-1b-ceiling-spikes-v1", "rom_sha256": sha(rom), "research_base": RESEARCH_BASE, "research_only": True, "poc_untouched": True,
            "scope": {"in": ["surface $1B / block $A0 sinking", "MGHZ2 (and MGHZ1) ceiling spikes, blocks $3E/$3F"], "out": ["$24", "$2E", "footwear", "boss $56"]},
            "evidence_classes": ["DECODED DATA", "BYTE-VERIFIED ASSEMBLY", "SOURCE-TRACED BEHAVIOR", "CONTROLLED ROUTINE RESULT", "EMULATED ORIGINAL FRAME", "UNRESOLVED"],
            "static": static_facts(rom), "ceiling_probe": ceiling_probe_facts(rom), "placements": {"oil": oil_pits(rom), "ceiling_spike_runs": ceiling_runs(rom), "other_bit6_blocks": bit6_cells(rom)},
            "static_only": static_only}
    if static_only:
        return data
    gm = gate_matrix(rom)
    sp = sink_parity(rom)
    ss = steady_state(rom)
    st = stale_bit_one_way(rom)
    gs = ceiling_gate_sweep(rom)
    gsum = ceiling_gate_summary(gs)
    rr = ceiling_real_runs_check(rom)
    pf = ceiling_pass_vs_full(rom)
    fs = ceiling_foot_sweep(rom)
    sd = ceiling_side_sweep(rom)
    assert gm["model_mismatches"] == 0 and sp["mismatches"] == 0, "sink model drifted from the ROM"
    assert gsum["rule_holds_for_every_combination_and_both_blocks"] and gsum["blocks_3e_and_3f_give_identical_results_in_every_combination"]
    assert all(v["matches"] for v in rr["results"].values())
    g1, g2 = GameLab(rom, "mghz1"), GameLab(rom, "mghz2")
    oil = {
        "fall_in": {"mghz1": scenario_fall_in(g1), "mghz2": scenario_fall_in(g2)},
        "walk_in": {"mghz1": [scenario_walk_in(g1, vx, cur, label) for vx, cur, label in ((0x100, 5, "walk_1.0"), (0x400, 5, "walk_4.0"), (0x600, 6, "run_6.0"), (0x400, 9, "roll_4.0"))],
                    "mghz2": [scenario_walk_in(g2, 0x400, 5, "walk_4.0")]},
        "jump_cycle": [scenario_jump_cycle(g1, w) for w in (6, 40, 90)],
        "escape_over_far_rim": [scenario_escape(g1, k) for k in (0, 8, 14, 18, 20, 22, 23, 24, 26)],
        "speed_control": scenario_speed_control(g1),
        "roll_on_oil": scenario_roll_on_oil(g1),
        "direction_independence": scenario_direction_independence(g1),
        "state_scan_first_update": scenario_oil_state_scan(g1),
        "after_death": scenario_after_death(g1),
    }
    ceil = {
        "hit_5_rings": scenario_ceiling_hit(g2, 5, "5 rings (BCD 05)"),
        "hit_0_rings": scenario_ceiling_hit(g2, 0, "0 rings"),
        "hit_while_invulnerable": scenario_ceiling_hit(g2, 5, "+$03 bit 7 and $D3B1 = 100", inv=True, d3b1=100),
        "hit_with_power_up_invincibility": scenario_ceiling_hit(g2, 5, "$D532 = 6", d532=6),
        "near_miss": scenario_ceiling_near_miss(g2),
        "falling_through": scenario_ceiling_falling(g2),
        "stomp_bounce_state_0b_launch": scenario_ceiling_spring_launch(g2),
        "state_scan_three_updates": scenario_ceiling_state_scan(g2),
    }
    data["placements"]["hazard_neighbour_objects"] = hazard_neighbours(rom, data["placements"])
    data["examples"] = build_examples(data["placements"], oil, ceil)
    data.update({"surface_1b": {"gate_matrix": gm, "sink_parity": sp, "steady_state": ss, "stale_bit_one_way": st, "whole_game": oil},
                 "ceiling_spikes": {"gate_sweep": gs, "gate_summary": gsum, "real_runs_check": rr, "full_pass_versus_isolated": pf, "foot_sweep": fs, "side_sweep": sd, "whole_game": ceil},
                 "counts": {"controlled_cases_total": gm["cases"] + sp["cases"] + gs["cases"] + fs["cases"] + sd["cases"]}})
    return data


def rim_text(p: dict) -> str:
    x0, x1, y0, _ = p["cells"]
    return (f"row {y0 - 1}: cells {x0 - 1} and {x1 + 1} are solid (blocks {p['rim_row_cells_just_outside_[left,right]'][0]} / {p['rim_row_cells_just_outside_[left,right]'][1]}, top y {(y0 - 1) * 32}); "
            f"cells {x0}..{x1} are block {', '.join(p['blocks_in_row_above_oil'])} (surface {', '.join(p['row_above_oil_collision'])}, no collision); the oil top is one cell lower (y {y0 * 32})")


def build_examples(placements: dict, oil: dict, ceil: dict) -> dict:
    """MGHZ-specific example coordinates with the expected results measured above (each is a copy of a measured scenario, so the test locks them)."""
    def pit(key):
        return placements["oil"][key]["pits"][0]
    fi1, fi2 = oil["fall_in"]["mghz1"], oil["fall_in"]["mghz2"]
    esc = {r["counter_at_jump"]: r["reached_far_rim"] for r in oil["escape_over_far_rim"]}
    runs = placements["ceiling_spike_runs"]
    return {
        "coordinates": "world pixels; anchor = player Y register (feet = anchor + 18); cells are 32 px",
        "oil": {
            "mghz1": {"pit_cells_[x0,x1,y0,y1]": pit("mghz1")["cells"], "world_rect_[x0,y0,x1,y1]": pit("mghz1")["world_rect"], "oil_top_y": 800, "rim_top_y": RIM_TOP["mghz1"],
                      "rim_description": rim_text(pit("mghz1")),
                      "fixtures": [
                          {"name": "drop_onto_oil_centre", "place": fi1["start"], "expect": {"first_oil_handler_update": fi1["first_oil_handler_update"], "plunge_at_counter": fi1["plunge_counter"], "plunge_anchor_y_path": fi1["plunge_y_path"],
                                                                                           "death_request_update": fi1["death_request_update"], "death_screen_y_before": fi1["death_screen_y_before"]}},
                          {"name": "walk_off_left_rim_holding_right", "place": oil["walk_in"]["mghz1"][1]["start"], "expect": {k: oil["walk_in"]["mghz1"][1][k] for k in ("first_oil_handler_update", "plunge_counter", "plunge_update", "death_request_update")}},
                          {"name": "steady_standing_anchor", "formula": "anchor_y = 778 + counter for counter 0..24 (feet = 796 + counter = oil_top - 4 + counter)"},
                          {"name": "jump_out_over_far_rim", "reaches_far_rim_by_counter_at_jump": esc, "setup": "standing on the oil 40 px left of the far rim wall (x 1624), hold RIGHT, press jump on the second update"}]},
            "mghz2": {"pit_cells_[x0,x1,y0,y1]": pit("mghz2")["cells"], "world_rect_[x0,y0,x1,y1]": pit("mghz2")["world_rect"], "oil_top_y": 928, "rim_top_y": RIM_TOP["mghz2"],
                      "rim_description": rim_text(pit("mghz2")),
                      "fixtures": [{"name": "drop_onto_oil_centre", "place": fi2["start"], "expect": {"first_oil_handler_update": fi2["first_oil_handler_update"], "plunge_at_counter": fi2["plunge_counter"], "plunge_anchor_y_path": fi2["plunge_y_path"],
                                                                                           "death_request_update": fi2["death_request_update"]}}]},
            "mghz3": "no $A0 cells"},
        "ceiling_spikes": {
            "mghz1": [{"block": r["block"], "cells": r["cells"], "hazard_anchor_x": r["hazard_anchor_x_range"], "hazard_anchor_y": r["hazard_anchor_y_range"], "above": r["blocks_above"], "below": r["blocks_below"]} for r in runs["mghz1"]],
            "mghz2": [{"block": r["block"], "cells": r["cells"], "hazard_anchor_x": r["hazard_anchor_x_range"], "hazard_anchor_y": r["hazard_anchor_y_range"], "above": r["blocks_above"], "below": r["blocks_below"]} for r in runs["mghz2"]],
            "mghz3": "no $3E/$3F cells (two $3C floor-spike cells at (101,13),(103,13) are covered by the platform/spike audit)",
            "fixtures": [
                {"name": "rising_hit_5_rings", "act": "mghz2", "place": ceil["hit_5_rings"]["start"], "expect": {"hurt_update": ceil["hit_5_rings"]["hurt_update"], "anchor_y": ceil["hit_5_rings"]["anchor_y_at_hurt"],
                                                                                                         "row": [r for r in ceil["hit_5_rings"]["rows_around_hurt"] if "hurt" in r["ev"]][0]}},
                {"name": "rising_hit_0_rings", "act": "mghz2", "place": ceil["hit_0_rings"]["start"], "expect": {"row": [r for r in ceil["hit_0_rings"]["rows_around_hurt"] if "hurt" in r["ev"]][0]}},
                {"name": "invulnerable_bounce", "act": "mghz2", "place": ceil["hit_while_invulnerable"]["start"], "expect": {"bounce_update": ceil["hit_while_invulnerable"]["bounce_update"], "anchor_y": ceil["hit_while_invulnerable"]["anchor_y_at_bounce"]}},
                {"name": "near_miss_apex_383", "act": "mghz2", "place": ceil["near_miss"]["start"], "expect": {"apex_y": ceil["near_miss"]["apex_y"], "hurt": ceil["near_miss"]["hurt"]}}]}}


def dumps(data: dict) -> str:
    return json.dumps(data, indent=1) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    a = ap.parse_args()
    rom = L.load_rom(a.rom)
    text = dumps(build(rom, a.static_only))
    if a.check:
        cached = OUTPUT.read_text(encoding="utf-8")
        if a.static_only:
            cj, dj = json.loads(cached), json.loads(text)
            bad = [k for k in dj if k in cj and k != "static_only" and cj[k] != dj[k]]
        else:
            bad = [] if cached.replace("\r\n", "\n") == text else ["file"]
        print("OK: cache matches the ROM" if not bad else f"MISMATCH in {bad}")
        sys.exit(1 if bad else 0)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT} ({len(text)} bytes)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Shared player fall / control audit (Research only, deterministic).

Bounded questions raised by the Windows MGHZ M1 test (which pre-date MGHZ):
  A. special fall state $14: complete runtime, entry, horizontal input, gravity, collision passes, exits, surface-$19 marker lifetime;
  B. ordinary fall $0E / ring monitor ($5FA0) + side wall: can the original enter the snag seen in the POC;
  C. which fall states can acquire one-way, type-$28 and GPZ solid-surface support.

Output: data/rom-cache/player-fall-control.json (numeric labels; hashes only, no ROM bytes, no pixels).

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT (original Z80 routines on tools/oracle.py),
EMULATED ORIGINAL FRAME (whole game in tools/sms_frame_harness.py booted into an act, PC hooks), SYNTHETIC CONTROL (state/layout patched in RAM, never a
canonical placement), POC SOURCE (READ-ONLY), UNRESOLVED.

Usage:
  python tools/player_fall_control.py ROM.sms [--check] [--static-only]
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

import isometric_platform as I          # noqa: E402  (act_data, TerrainLab)
import level_package as L               # noqa: E402
import mghz_surface_ceiling as M        # noqa: E402  (GameLab, header_facts)
import platform_spike_collision as P    # noqa: E402  (Emu: snapshot/restore/place)
import rom as R                         # noqa: E402

OUTPUT = ROOT / "data" / "rom-cache" / "player-fall-control.json"
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
RESEARCH_BASE = "a779fde"

ZONES = {"thz": 0, "gpz": 1, "sez": 2, "mghz": 3}
PAD = dict(UP=1, DOWN=2, LEFT=4, RIGHT=8, B1=16, B2=32)

# named routines (CPU addresses, fixed bank 1 unless noted)
SHARED_UPDATE = 0x3FEF
X_INTEGRATION, Y_INTEGRATION = 0x402A, 0x4097
INPUT_TABLES = 0x4141
TERRAIN_PASS, TERRAIN_FLOOR, TERRAIN_SIDES, TERRAIN_CEILING, TERRAIN_RINGS, MERGE = 0x690B, 0x691A, 0x715E, 0x73C9, 0x753E, 0x64CB
FLOOR_PROJECTION, ONE_WAY_GATE, SOLID_PROJECTION_GATE = 0x6F61, 0x6FBB, 0x6F6D
SURFACE19_HANDLER, SURFACE_ZERO_HANDLER = 0x6B23, 0x6C45
FALL_SETTER, STRIP_FALL_SETTER, LANDING, JUMP = 0x463C, 0x4663, 0x45CE, 0x45ED
WALK_SUFFIX = 0x3791
CB_FALL, CB_STRIP_FALL = 0x3A37, 0x3A48       # state $0E / $14 callbacks (trampolines $03AD / $03F8)
DAMAGE_GATE = 0x48BC
SOLID_OBJECT, OVERLAP = 0x5FA0, 0x6328
PLATFORM_SUPPORT, PLATFORM_CARRY = 0x8814, 0x88A0   # bank $1E
PLAYER_CALLBACK_DISPATCH = 0x5E91


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def s16(v: int) -> int:
    return (v + 32768) % 65536 - 32768


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos research ROM")


def squash(seq) -> list:
    out = []
    for n in seq:
        if not out or out[-1] != n:
            out.append(n)
    return out


# --------------------------------------------------------------------------- #
# whole-game lab (zone-parametrised copy of mghz_surface_ceiling.GameLab boot)
# --------------------------------------------------------------------------- #
HOOKS = {SHARED_UPDATE: "update_3FEF", X_INTEGRATION: "x_integration", Y_INTEGRATION: "y_integration", INPUT_TABLES: "input_tables",
         TERRAIN_PASS: "terrain_pass", TERRAIN_FLOOR: "terrain_floor", TERRAIN_SIDES: "terrain_sides", TERRAIN_CEILING: "terrain_ceiling",
         TERRAIN_RINGS: "terrain_rings", MERGE: "merge_64CB", FLOOR_PROJECTION: "floor_projection", ONE_WAY_GATE: "one_way_gate_6FBB",
         SOLID_PROJECTION_GATE: "solid_projection_6F6D", SURFACE19_HANDLER: "surface19_6B23", SURFACE_ZERO_HANDLER: "surface_zero_6C45",
         FALL_SETTER: "fall_setter_463C", STRIP_FALL_SETTER: "strip_fall_setter_4663", LANDING: "landing_45CE", JUMP: "jump_45ED",
         DAMAGE_GATE: "damage_gate_48BC", SOLID_OBJECT: "solid_object_5FA0", OVERLAP: "overlap_6328", PLATFORM_SUPPORT: "platform_support_8814",
         PLATFORM_CARRY: "platform_carry_88A0", CB_FALL: "callback_fall_0E", CB_STRIP_FALL: "callback_strip_fall_14", WALK_SUFFIX: "walk_suffix_3791"}


class Lab:
    """Boots the ORIGINAL game into (zone, act), settles, snapshots; every case restores the snapshot (deterministic).

    place() sets the REQUESTED state only and forces the animation engine to reload that state's script on the next update; without the reload the
    previously running (standing) script keeps supplying its own callback and the requested state's callback never runs.
    """

    def __init__(self, rom: bytes, zone: str, act: int):
        from sms_frame_harness import SMS, BTN_1, BTN_2
        self.rom, self.zone, self.act = rom, zone, act
        s = SMS(rom)
        done = [False]
        zone_index = ZONES[zone]

        def select(m):
            m._write(0xD297, zone_index)
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
            raise RuntimeError("boot failed")
        for _ in range(90):
            s.pad = 0
            s.run_frame()
        self.s, self.m = s, s.mem
        self.key = f"{zone}{act + 1}"
        self.width = I.act_data(rom, self.key)["width"]
        self.upd = 0
        self.ev: list = []
        self.cap: dict = {}
        self.record = False
        s.add_pc_hook(PLAYER_CALLBACK_DISPATCH, self._on_dispatch)
        for a, name in HOOKS.items():
            s.add_pc_hook(a, lambda mm, n=name, a=a: self._hit(n, a))
        self.e = P.Emu.__new__(P.Emu)
        self.e.s, self.e.rom, self.e.act = s, rom, self.key
        self.e._place = P._load("spring_interaction")._place
        self.e.base = self.e.snapshot()

    # ---- hooks
    def _on_dispatch(self, mm) -> None:
        if mm.cpu.ix == 0xD500:
            self.upd += 1
            self.ev.append("PLAYER")

    def _hit(self, name: str, addr: int) -> None:
        if not self.record:
            return
        self.ev.append(name)
        s, m = self.s, self.m
        if addr == SOLID_OBJECT:
            self.cap.setdefault("solid_calls", []).append({"x": s.u16(0xD511), "y": s.u16(0xD514), "d523": m[0xD523], "obj_x": s.u16(s.cpu.ix + 0x11),
                                                         "obj_y": s.u16(s.cpu.ix + 0x14)})
        elif addr == OVERLAP and s.cpu.ix != 0xD500:
            self.cap.setdefault("overlap_calls", []).append({"obj": s.cpu.ix, "x": s.u16(0xD511), "y": s.u16(0xD514)})

    # ---- cases
    def cell(self, cx: int, cy: int) -> int:
        return self.m[0xC001 + cy * self.width + cx]

    def place(self, x, y, vx=0, vy=0, cur=0x0E, f3=1, floor=False, prev=0, p24=None, k=None, rings=0, patch=None, d3c0=None, water=None) -> None:
        self.e.restore()
        self.e.place(x, y, vx, vy, cur=cur, f3=f3, floor=floor, rings=rings, prev=prev)
        m = self.m
        m[0xD501] = 0xFF if cur != 0xFF else 0          # force the engine to reload the requested state's script
        m[0xD523] = 0
        if p24 is not None:
            m[0xD524] = p24
        if k is not None:
            m[0xD3BC] = k
        if d3c0 is not None:
            m[0xD3C0] = d3c0
        if water is not None:
            m[0xD443] = water
        for (cx, cy), blk in (patch or {}).items():
            m[0xC001 + cy * self.width + cx] = blk
        self.upd = 0
        self.ev.clear()
        self.cap.clear()

    def row(self) -> dict:
        s, m = self.s, self.m
        return {"u": self.upd, "x": s.u16(0xD511), "y": s.u16(0xD514), "vx": s16(s.u16(0xD516)), "vy": s16(s.u16(0xD518)), "cur": m[0xD501], "req": m[0xD502],
                "f3": m[0xD503], "f22": m[0xD522], "f23": m[0xD523], "f21": m[0xD521], "p24": m[0xD524], "k": m[0xD3BC], "d36c": m[0xD36C], "d36b": m[0xD36B],
                "d3c0": m[0xD3C0], "d375": s16(s.u16(0xD375)), "rings": m[0xD29A], "sy": s16(s.u16(0xD51C)), "pad": m[0xD137]}

    def run(self, frames: int, padf=None, stop=None, events: bool = False) -> list:
        """One row per player update (the frame loop may hold lag frames with no update)."""
        rows = []
        self.record = events
        last = self.upd
        if padf:                                    # the pad has been held since before the first update (the game polls it once per frame)
            self.m[0xD137] = self.m[0xD138] = padf(0, 0)
        for f in range(frames):
            self.s.pad = padf(self.upd, f) if padf else 0
            self.ev.clear()
            self.cap.clear()
            self.s.run_frame()
            if self.upd != last:
                last = self.upd
                r = self.row()
                if events:
                    r["ev"] = squash(self.ev)
                    if self.cap:
                        r["cap"] = {k: list(v) for k, v in self.cap.items()}
                rows.append(r)
                if stop and stop(rows[-1], rows):
                    break
        self.record = False
        return rows


# --------------------------------------------------------------------------- #
# A. state $14 - static facts
# --------------------------------------------------------------------------- #
def w16(rom: bytes, a: int) -> int:
    return int.from_bytes(rom[a:a + 2], "little")


TABLES = {"dry_vx_nonneg": 0x429D, "dry_vx_neg": 0x431D, "friction": 0x439D, "water_vx_nonneg": 0x441D, "water_vx_neg": 0x449D, "unused_451D": 0x451D}
SURFACE_DELTA_TABLE = 0x459D


def input_tables(rom: bytes) -> dict:
    """The six state-indexed (2 x signed 16) tables read by $4141; index = state*4 (+2 for 'right only'); only states < $1E reach them."""
    rows = {}
    for st in range(0x1E):
        rows[h(st, 2)] = {name: [s16(w16(rom, base + st * 4)), s16(w16(rom, base + st * 4 + 2))] for name, base in TABLES.items()}
    zero_all = [h(st, 2) for st in range(0x1E) if all(v == [0, 0] for k, v in rows[h(st, 2)].items() if k != "unused_451D")]
    zero_input = [h(st, 2) for st in range(0x1E) if all(rows[h(st, 2)][k] == [0, 0] for k in ("dry_vx_nonneg", "dry_vx_neg", "water_vx_nonneg", "water_vx_neg"))]
    zero_friction = [h(st, 2) for st in range(0x1E) if rows[h(st, 2)]["friction"] == [0, 0]]
    return {"evidence": "DECODED DATA + BYTE-VERIFIED ASSEMBLY ($4141: table address = base + state*4 + (left ? 0 : 2), word signed)",
            "table_bases": {k: h(v) for k, v in TABLES.items()},
            "selection": "$4141: current state (IX+1) < $29 and >= $1E returns before the tables; otherwise dry/water by $D443, pad & 12 == 0 -> friction table $439D (indexed by vx sign: negative -> word0, else word1), "
                         "else vx<0 -> *_neg table else *_nonneg table, word0 when Left (bit 2) is held else word1; |vx|+$80 < $100 doubles the word; result -> $D375. Surface delta $D377 = word at $459D + $D369 "
                         "($459D[0] = 0).",
            "surface_delta_first_word": s16(w16(rom, SURFACE_DELTA_TABLE)),
            "states": rows, "states_with_all_tables_zero": zero_all, "states_with_zero_input_acceleration": zero_input, "states_with_zero_friction": zero_friction}


def fixed_bank_cp14_sites(rom: bytes) -> list:
    """Every `CP $14` (byte pair FE 14) in the fixed banks 0/1 and the player-selector bank $0C, with a role (the rest of the ROM belongs to other objects)."""
    roles = {0x3A4E: "state $0E/$14 callback: requested == $14 gates the landing test (callback $3A48)",
             0x6FC4: "one-way floor projection gate $6FBB: strip bit0 AND requested == $14 -> no projection",
             0x7402: "ceiling pass: SURFACE TYPE $14 (diagonal/ceiling spring), not a player state",
             0x7569: "terrain-ring probe: SURFACE TYPE $14, not a player state"}
    out = []
    for p in range(0, 0x8000):
        if rom[p:p + 2] == b"\xfe\x14":
            out.append({"cpu": h(p), "role": roles.get(p, "unclassified (not a player-state comparison in the audited routines)")})
    for p in range(12 * 0x4000, 13 * 0x4000):
        if rom[p:p + 2] == b"\xfe\x14":
            cpu = 0x8000 + p % 0x4000
            out.append({"bank": 12, "cpu": h(cpu), "role": {0x8F7B: "Sonic walk selector: compares a frame counter byte (not the player state)"}.get(cpu, "player-selector bank; not a state comparison (counter/data)")})
    return out


def state14_writers(rom: bytes) -> dict:
    """Static inventory of the code that requests state $14 for the PLAYER (IX = $D500)."""
    ld_ix2 = [p for p in range(len(rom) - 3) if rom[p:p + 4] == b"\xdd\x36\x02\x14"]
    callers = [p for p in range(len(rom) - 2) if rom[p + 1:p + 3] == b"\x63\x46" and rom[p] in (0xC3, 0xCD, 0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA)]
    return {"evidence": "BYTE-VERIFIED ASSEMBLY (opcode scan of the whole ROM)",
            "ld_ix_plus2_14_sites": [{"rom": h(p, 5), "bank": p // 0x4000, "cpu": h(p if p < 0x8000 else 0x8000 + p % 0x4000)} for p in ld_ix2],
            "ld_ix_plus2_14_player_site": "$4663 (the setter itself); the two bank-$1E sites ($9FCD, $AAF4) write the state of OTHER objects (type-specific state numbering)",
            "callers_of_4663": [{"cpu": h(p), "opcode": h(rom[p], 2)} for p in callers],
            "only_player_entry": "JP nz,$4663 at $37C3 inside the walk callback $3783 suffix: requested state still $05, no roll request ($47DC when |vx| >= 1.0 and Down held), "
                                 "dry (D443 == 0), |vx| high byte != $D374 (equality requests run $06 instead) and +$24 bit0 set"}


# --------------------------------------------------------------------------- #
# A. state $14 - controlled original routines (callbacks $3A37 / $3A48 on tools/oracle.py)
# --------------------------------------------------------------------------- #
AIR_X, AIR_Y = 3400, 500      # MGHZ1 shaft column 106, rows 15..24: every sampled cell is flags-0 air for >= 20 fall updates


class Air:
    """The ORIGINAL state callback ($3A37 = $0E, $3A48 = $14) on the decoded MGHZ1 layout, Sonic in empty air, every input explicit."""

    def __init__(self, rom: bytes, key: str = "mghz1"):
        self.t = I.TerrainLab(rom, key)
        self.o, self.m = self.t.o, self.t.o.mem
        self.rom = rom

    def setup(self, state, pad=0, vx=0, vy=0x100, water=0, x=AIR_X, y=AIR_Y, jump=0, p24=0, d523=0, req=None, f3=1, d369=0, cx_off=100, vmax=0x400):
        o, m = self.o, self.m
        m[0xC000:0xE000] = self.t.base
        o.word(0xD511, x)
        o.word(0xD514, y)
        m[0xD510] = 0
        m[0xD513] = 0
        o.word(0xD516, vx & 0xFFFF)
        o.word(0xD518, vy & 0xFFFF)
        m[0xD501] = state
        m[0xD502] = state if req is None else req
        m[0xD503] = f3
        m[0xD522] = 0
        m[0xD523] = d523
        m[0xD524] = p24
        m[0xD137] = pad
        m[0xD147] = jump
        o.word(0xD174, x - cx_off)
        o.word(0xD51C, 100)
        m[0xD443] = water
        o.word(0xD373, vmax)
        o.word(0xD375, 0)
        m[0xD36C] = 0
        m[0xD369] = d369
        m[0xD3BC] = 0
        m[0xD52C], m[0xD52D] = 8, 24
        m[0xD135] = 1                      # the death path waits for the frame-IRQ flag ($062D); the subroutine harness has no IRQ
        o.cpu.ix = 0xD500

    def snap(self) -> dict:
        o, m = self.o, self.m
        return {"x": o.word(0xD511), "xf": m[0xD510], "y": o.word(0xD514), "yf": m[0xD513], "vx": s16(o.word(0xD516)), "vy": s16(o.word(0xD518)), "d375": s16(o.word(0xD375)),
                "req": m[0xD502], "cur": m[0xD501], "f3": m[0xD503], "f22": m[0xD522], "f23": m[0xD523], "p24": m[0xD524], "k": m[0xD3BC]}

    def update(self, state: int, **kw) -> dict:
        self.setup(state, **kw)
        self.o.call(CB_STRIP_FALL if state == 0x14 else CB_FALL)
        return self.snap()

    def run(self, state: int, n: int, padf=None, **kw) -> list:
        self.setup(state, **kw)
        rows = [self.snap()]
        for i in range(n):
            self.m[0xD137] = padf(i) if padf else kw.get("pad", 0)
            self.m[0xD147] = 0
            self.o.word(0xD174, self.o.word(0xD511) - kw.get("cx_off", 100))
            self.o.call(CB_STRIP_FALL if state == 0x14 else CB_FALL)
            rows.append(self.snap())
        return rows


def model_x_delta(rom: bytes, state: int, pad: int, vx: int, water: int) -> int:
    """Python model of $4141's input delta ($D375) for states < $1E (surface delta zero)."""
    a = pad & 12
    if a == 0:
        if vx == 0:
            return 0
        word = w16(rom, TABLES["friction"] + state * 4 + (0 if vx < 0 else 2))
    else:
        base = TABLES[("water_" if water else "dry_") + ("vx_neg" if vx < 0 else "vx_nonneg")]
        word = w16(rom, base + state * 4 + (0 if a & 4 else 2))
    if ((abs(vx) + 0x80) & 0xFFFF) >> 8 == 0:
        word = (word * 2) & 0xFFFF
    return s16(word)


def model_x_update(rom: bytes, state: int, pad: int, vx: int, water: int, vmax: int = 0x400) -> int:
    hl = (vx + model_x_delta(rom, state, pad, vx, water)) & 0xFFFF
    if hl & 0x8000:
        if (hl >> 8) < ((-(vmax >> 8)) & 255):
            hl = (-vmax) & 0xFFFF
    elif (hl >> 8) >= (vmax >> 8):
        hl = vmax
    return s16(hl)


def model_y_update(vy: int, water: int) -> int:
    inc, cap = (0x18, 0x400) if water else (0x30, 0x700)
    hl = (vy + inc) & 0xFFFF
    if not hl & 0x8000 and (hl >> 8) >= (cap >> 8):
        hl = cap
    return s16(hl)


def horizontal_sweep(rom: bytes) -> dict:
    """Original callbacks vs the Python model over 2 states x 4 pad values x dry/water x ~370 signed X speeds; plus the $14 invariants."""
    air = Air(rom)
    speeds = sorted(set(list(range(-1100, 1101, 7)) + [0, 1, -1, 127, 128, 129, -127, -128, -129, 0x3FF, 0x400, 0x401, -0x3FF, -0x400, -0x401, 0x500, -0x500, 0x1000, -0x1000]))
    mism, n = [], 0
    changed14 = 0
    for state in (0x0E, 0x14):
        for pad in (0, 4, 8, 12):
            for water in (0, 1):
                for vx in speeds:
                    r = air.update(state, pad=pad, vx=vx, water=water)
                    n += 1
                    want = model_x_update(rom, state, pad, vx, water)
                    if r["vx"] != want:
                        mism.append({"state": h(state, 2), "pad": pad, "water": water, "vx": vx, "got": r["vx"], "want": want})
                    if state == 0x14 and r["d375"] != 0:
                        changed14 += 1
    return {"evidence": "CONTROLLED ROUTINE RESULT (callbacks $3A37/$3A48 on the decoded MGHZ1 layout, Sonic in empty air, camera 100 px left of Sonic)",
            "cases": n, "mismatches_vs_model": len(mism), "first_mismatches": mism[:3], "state14_nonzero_input_delta_cases": changed14,
            "speeds_swept": len(speeds), "maximum_speed": "$D373 = $0400 (high byte $D374 = 4)",
            "model": "delta = table word (dry/water, vx sign, Left?word0:word1, doubled while |vx|+$80 < $100; no input -> friction table; vx == 0 and no input -> 0); vx' = vx + delta; "
                     "then the $402A clamp: positive high byte >= max high byte -> +$0400, negative high byte < -max high byte (unsigned) -> -$0400",
            "state14_rule": "every dry, water and friction word of state $14 is 0: vx' = vx for |vx high byte| < 4; a speed beyond the maximum is clamped to +/-4.0 exactly like every other state"}


def vertical_sweep(rom: bytes) -> dict:
    air = Air(rom)
    mism, n = [], 0
    for state in (0x0E, 0x14):
        for water in (0, 1):
            for vy in list(range(-2200, 2201, 13)) + [0x6D0, 0x6FF, 0x700, 0x701, 0x3E8, 0x3FF, 0x400, -1, 1, 0x30, -0x30]:
                r = air.update(state, vy=vy, water=water, x=AIR_X, y=AIR_Y)
                n += 1
                want = model_y_update(vy, water)
                if r["vy"] != want:
                    mism.append({"state": h(state, 2), "water": water, "vy": vy, "got": r["vy"], "want": want})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "cases": n, "mismatches_vs_model": len(mism), "first_mismatches": mism[:3],
            "model": "vy' = vy + $0030 (dry) / $0018 (water); a non-negative result whose high byte is >= 7 (dry) / >= 4 (water) becomes $0700 / $0400; a negative result is kept; $4097 forces $0700 only "
                     "with +$22 bit1 (floor) set. States $0E and $14 are identical (the $18/$24 gravity variants belong to $0B/$1B only)."}


def air_fixtures(rom: bytes) -> dict:
    air = Air(rom)
    out = {}
    plans = {"hold_right": 8, "hold_left": 4, "neutral": 0, "alternate_8_updates": None}
    for state in (0x14, 0x0E):
        for vx0 in (256, 1024, -1024, 0):
            for name, pad in plans.items():
                padf = (lambda i: 8 if (i // 8) % 2 == 0 else 4) if pad is None else None
                rows = air.run(state, 16, padf=padf, pad=pad or 0, vx=vx0, vy=0x100)
                out[f"{h(state, 2)}_vx{vx0}_{name}"] = [{k: r[k] for k in ("x", "xf", "y", "vx", "vy", "d375")} for r in rows]
    return {"evidence": "CONTROLLED ROUTINE RESULT: 16 original updates per case (x/xf = pixel/fraction, vx/vy signed 8.8)", "cases": out}


# --------------------------------------------------------------------------- #
# A. state $14 - setters, entry/exit, marker lifetime
# --------------------------------------------------------------------------- #
def setter_diff(rom: bytes) -> dict:
    """Original setters $463C (ordinary fall $0E) and $4663 (special fall $14) run on identical pre-states; only the changed fields are kept."""
    air = Air(rom)
    o, m = air.o, air.m
    rows = []
    for setter in (FALL_SETTER, STRIP_FALL_SETTER):
        for cur in (0x01, 0x05, 0x06, 0x0A, 0x09):
            for p24 in (0, 1, 3):
                for f3 in (0x00, 0x03, 0x43, 0x83):
                    for f22 in (0x00, 0x02):
                        air.setup(cur, vx=0x0123, vy=0xFC00, p24=p24, f3=f3)
                        m[0xD522] = f22
                        m[0xD3BC] = 7
                        before = air.snap()
                        o.call(setter)
                        after = air.snap()
                        d = {k: [before[k], after[k]] for k in ("req", "vy", "f3", "f22", "p24", "k", "vx", "x", "y") if before[k] != after[k]}
                        rows.append({"setter": h(setter), "current_state": h(cur, 2), "p24_before": p24, "f3_before": h(f3, 2), "f22_before": h(f22, 2), "changed": d})
    by_setter = {}
    for r in rows:
        by_setter.setdefault(r["setter"], []).append(r)
    summary = {}
    for st, rs in by_setter.items():
        fields = sorted({k for r in rs for k in r["changed"]})
        summary[st] = {"cases": len(rs), "fields_ever_changed": fields}
    # the facts a POC must reproduce, derived from the executed cases (asserted in tests)
    facts = {
        "0x463C": "requested $0E, vy := +$0100, +$03 bit0 set, bit1 cleared, +$24 bit0 CLEARED, +$22 bit1 cleared, $D3BC := 0; a no-op when the CURRENT state is $0A (normal jump)",
        "0x4663": "requested $14, vy := +$0100, +$03 bit0 set, bit1 cleared, +$24 bit0 RETAINED, +$22 bit1 cleared, $D3BC := 0; no jump exemption; vx, x, y, plane, +$24 bit1 untouched",
    }
    return {"evidence": "CONTROLLED ROUTINE RESULT (5 current states x 3 marker values x 4 movement-flag values x 2 floor-flag values per setter)", "cases": len(rows),
            "summary": summary, "facts": facts, "first_cases": {st: rs[:2] for st, rs in by_setter.items()},
            "marker_difference_cases": [r for r in rows if r["current_state"] == "0x05" and r["f3_before"] == "0x00" and r["f22_before"] == "0x02" and r["p24_before"] == 1]}


def surface_marker_matrix(rom: bytes) -> dict:
    """+$24 bits 0/1 after the floor pass $691A for EVERY surface type 0..$1F (one representative block per type patched under Sonic's foot), marker before = 0 / 1 / 2 / 3."""
    t = I.TerrainLab(rom, "mghz1")
    o, m = t.o, t.o.mem
    a = I.act_data(rom, "mghz1")
    w = a["width"]
    blocks = {}
    for b in range(256):
        ty = R.header(rom, b)["flags"] & 0x1F
        blocks.setdefault(ty, b)
    out = []
    x, y = AIR_X, 520            # foot probe row y+18 = 538 -> layout row 16 (cells (106,16))
    cx, cy = x // 32, (y + 18) // 32
    for ty in sorted(blocks):
        for before in (0, 1, 2, 3):
            m[0xC000:0xE000] = t.base
            m[0xC001 + cy * w + cx] = blocks[ty]
            o.word(0xD511, x)
            o.word(0xD514, y)
            o.word(0xD516, 0x0200)
            o.word(0xD518, 0x0100)
            m[0xD501] = m[0xD502] = 0x14
            m[0xD503] = 1
            m[0xD522] = 0
            m[0xD523] = 0
            m[0xD524] = before
            m[0xD36C] = 0
            m[0xD3BC] = 5
            m[0xD52C], m[0xD52D] = 8, 24
            o.cpu.ix = 0xD500
            o.call(TERRAIN_FLOOR)
            out.append({"type": h(ty, 2), "block": h(blocks[ty], 2), "before": before, "after": m[0xD524], "k_after": m[0xD3BC], "req_after": m[0xD502]})
    after_by_type = {}
    for r in out:
        after_by_type.setdefault(r["type"], {})[str(r["before"])] = r["after"]
    sets = sorted(t for t, v in after_by_type.items() if any(v[b] & 1 for b in ("0", "2")))
    clears = sorted(t for t, v in after_by_type.items() if v["1"] & 1 == 0 or v["3"] & 1 == 0)
    return {"evidence": "CONTROLLED ROUTINE RESULT ($691A on the decoded MGHZ1 layout with one block per surface type patched into the foot cell)",
            "cases": len(out), "types_tested": len(after_by_type), "types_that_set_bit0": sets, "types_that_clear_bit0": clears,
            "after_by_type_and_before": after_by_type,
            "reading": "bit0 is SET only by surface $19 (handler $6B23) and CLEARED only by surface 0 (handler $6C45, together with bit1); every other surface type leaves it unchanged"}


# --------------------------------------------------------------------------- #
# A/C. whole-game fixtures on MGHZ1 / GPZ2 (EMULATED ORIGINAL FRAME)
# --------------------------------------------------------------------------- #
KEYS = ("u", "x", "y", "vx", "vy", "cur", "req", "f3", "f22", "f23", "p24", "k", "d36c", "d3c0")
MGHZ1_STRIP_UPPER = {"cells": "X102..111, Y12", "foot_y": 384}
MGHZ1_STRIP_LOWER = {"cells": "X95..109, Y27", "foot_y": 864}


def compact(r: dict, keys=KEYS) -> dict:
    return {k: r[k] for k in keys if k in r}


def transitions(rows: list, extra=None) -> list:
    """Rows where (current, requested, marker, floor bit, foot-surface-is-$19, support owner) changes, plus the first and last row."""
    out, last = [], None
    for i, r in enumerate(rows):
        key = (r["cur"], r["req"], r["p24"], r["f22"] & 2, r["d36c"] & 31 == 0x19, r["d3c0"] != 0) + (extra(r) if extra else ())
        if key != last or i == len(rows) - 1:
            out.append(compact(r))
        last = key
    return out


def fall_milestones(rows: list) -> dict:
    first_req = next((r for r in rows if r["req"] == 0x14), None)
    first_cur = next((r for r in rows if r["cur"] == 0x14), None)
    in14 = [r for r in rows if r["cur"] == 0x14 and first_cur and r["u"] > first_cur["u"]]
    foot19 = [r["u"] for r in rows if r["d36c"] & 31 == 0x19]
    runs, start = [], None
    for u in foot19:
        if start is None or u != prev + 1:
            if start is not None:
                runs.append([start, prev])
            start = u
        prev = u
    if start is not None:
        runs.append([start, prev])
    death = next((r for r in rows if r["req"] == 0x1F), None)
    marker = [[r["u"], r["p24"]] for i, r in enumerate(rows) if i == 0 or r["p24"] != rows[i - 1]["p24"]]
    landing = next((r for i, r in enumerate(rows) if i and rows[i - 1]["cur"] == 0x14 and r["cur"] != 0x14 and r["req"] == 5), None)
    return {"updates": len(rows), "first_request_14_update": first_req["u"] if first_req else None, "first_current_14_update": first_cur["u"] if first_cur else None,
            "vx_values_while_14_after_first": sorted({r["vx"] for r in in14}), "input_delta_values_while_14": sorted({r["d375"] for r in in14}),
            "foot_surface_19_update_runs": runs, "marker_changes_u_value": marker, "state_14_updates": sum(1 for r in rows if r["cur"] == 0x14),
            "death_request_update": death["u"] if death else None, "death_request_y": death["y"] if death else None,
            "death_screen_y_d51c": death["sy"] if death else None, "camera_y_at_death": (death["y"] - death["sy"]) if death else None,
            "landing_row": compact(landing) if landing else None}


def scenario(lab: Lab, name: str, x, y, pad, cur=5, vx=0x100, vy=0, f3=0, floor=True, prev=0x59, frames=260, stop_death=True, **kw) -> dict:
    lab.place(x, y, vx, vy, cur=cur, f3=f3, floor=floor, prev=prev, **kw)
    rows = lab.run(frames, padf=lambda u, f: pad, stop=(lambda r, rs: r["req"] == 0x1F) if stop_death else None)
    return {"name": name, "start": {"x": x, "y": y, "vx": vx, "vy": vy, "requested_state": h(cur, 2), "movement_flags": h(f3, 2), "floor": floor, "previous_surface": h(prev, 2), "pad": pad,
                                    **{k: v for k, v in kw.items()}},
            "milestones": fall_milestones(rows), "transitions": transitions(rows), "first_rows": [compact(r) for r in rows[:6]]}


def strip_scenarios(rom: bytes) -> dict:
    lab = Lab(rom, "mghz", 0)
    out = {"evidence": "EMULATED ORIGINAL FRAME (whole game booted into MGHZ1; Sonic and camera teleported; requested state set so the engine loads that state's own script)",
           "strips": {"upper": MGHZ1_STRIP_UPPER, "lower": MGHZ1_STRIP_LOWER, "block_flags": "$85/$87: header $59 = one-way bit6 + surface type $19, vertical profile 32"}}
    sc = {}
    for pad, nm in ((8, "right"), (4, "left"), (0, "neutral")):
        sc[f"upper_strip_walkoff_{nm}"] = scenario(lab, f"upper strip, walking +1.0, hold {nm}", 3408, 366, pad)
    for pad, nm in ((8, "right"), (4, "left"), (0, "neutral")):
        sc[f"ordinary_fall_onto_lower_strip_{nm}"] = scenario(lab, f"ordinary fall $0E from (3300,450), hold {nm}", 3300, 450, pad, cur=0x0E, vx=0, vy=0x100, f3=1, floor=False, prev=0, frames=200)
    sc["special_fall_injected_over_lower_strip"] = scenario(lab, "SYNTHETIC: state $14 injected above the lower strip, marker clear", 3300, 450, 8, cur=0x14, vx=0x100, vy=0x100, f3=1, floor=False,
                                                           prev=0, p24=0, frames=200)
    sc["ordinary_fall_over_lower_strip_with_marker_set"] = scenario(lab, "SYNTHETIC: ordinary fall $0E injected with the strip marker already set (+$24 bit0 = 1)", 3300, 450, 0, cur=0x0E, vx=0, vy=0x100,
                                                                  f3=1, floor=False, prev=0, p24=1, frames=200)
    out["scenarios"] = sc
    return out


def gpz2_strip_scenarios(rom: bytes) -> dict:
    lab = Lab(rom, "gpz", 1)
    sc = {}
    for pad, nm in ((8, "right"), (4, "left"), (0, "neutral")):
        sc[f"strip_walkoff_{nm}"] = scenario(lab, f"GPZ2 strip (528,686) walking +1.0, hold {nm}", 528, 686, pad, frames=160)
    sc["strip_fast_run_right"] = scenario(lab, "GPZ2 strip (528,686) running +4.0, hold right", 528, 686, 8, cur=6, vx=0x400, frames=60, stop_death=False)
    sc["strip_run_then_release"] = scenario(lab, "GPZ2 strip (528,686) running +4.0, pad released: run -> walk -> special fall", 528, 686, 0, cur=6, vx=0x400, frames=60, stop_death=False)
    return {"evidence": "EMULATED ORIGINAL FRAME (whole game booted into GPZ2)", "scenarios": sc}


# --------------------------------------------------------------------------- #
# B. ordinary fall / special fall + ring monitor ($5FA0) + side wall   (MGHZ1: monitor record 16 at (3568,814), wall column 112 from X3584)
# --------------------------------------------------------------------------- #
MONITOR = {"record": 16, "x": 3568, "y": 814, "type": "0x10", "parameter": 1}
WALL_X = 3584
MON_EXT = (10, 24)           # +$2C/+$2D of the state-2 monitor
SONIC_EXT = (8, 24)


def monitor_slot(lab: Lab):
    for i in range(19):
        b = 0xD540 + i * 0x40
        if lab.m[b] == 0x10:
            return b
    return None


def classify_contact(px: int, py: int, ox: int = MONITOR["x"], oy: int = MONITOR["y"]) -> int:
    """$6328 low-nibble classification for Sonic 8x24 against the monitor 10x24 (see docs/collision-geometry-audit.md section 3). 0 = no contact, 1 above, 2 below, 4 right, 8 left."""
    dx = px - ox
    span = SONIC_EXT[0] + MON_EXT[0]
    if dx >= 0:
        if dx > 255 or dx > span:
            return 0
        hp, hb = span - dx, 4
    else:
        if -dx > 255 or -dx > span:
            return 0
        hp, hb = span + dx, 8
    dy = py - oy
    if dy >= 0:
        if dy > 255 or dy > SONIC_EXT[1]:
            return 0
        vp, vb = SONIC_EXT[1] - dy, 2
    else:
        if -dy > 255 or -dy > MON_EXT[1]:
            return 0
        vp, vb = MON_EXT[1] + dy, 1
    return hb if hp < vp else vb


def wedge_row(r: dict) -> dict:
    d = compact(r, ("u", "x", "y", "vx", "vy", "cur", "req", "f22", "f23", "f21", "d375"))
    sc = r.get("cap", {}).get("solid_calls")
    if sc:
        d["monitor_5FA0"] = [{"player_before_push": [c["x"], c["y"]], "d523_at_call": c["d523"], "classification": classify_contact(c["x"], c["y"])} for c in sc]
    ev = r.get("ev", [])
    marks = [i for i, e in enumerate(ev) if e == "PLAYER"]
    if len(marks) > 1:                              # a frame boundary can fall right after the next update's dispatch; keep only this update's events
        ev = ev[:marks[1]]
    d["order"] = [e for e in ev if e in ("PLAYER", "x_integration", "terrain_sides", "solid_object_5FA0", "merge_64CB", "callback_fall_0E", "callback_strip_fall_14")]
    return d


def wedge_case(lab: Lab, x, y, cur, pad, vx=0, vy=0, frames=14, f3=1, name="") -> dict:
    lab.place(x, y, vx, vy, cur=cur, f3=f3, floor=False, prev=0)
    rows = lab.run(frames, padf=lambda u, f: pad, events=True)
    both = [r["u"] for r in rows if r["f23"] & 12 == 12]
    return {"name": name, "start": {"x": x, "y": y, "vx": vx, "vy": vy, "state": h(cur, 2), "pad": pad}, "rows": [wedge_row(r) for r in rows],
            "first_update_with_both_wall_flags": both[0] if both else None, "x_max": max(r["x"] for r in rows), "final": compact(rows[-1])}


def natural_monitor_falls(rom: bytes, lab: Lab | None = None) -> dict:
    lab = lab or Lab(rom, "mghz", 0)
    out = {}
    for pad, nm in ((8, "right"), (4, "left"), (0, "neutral")):
        lab.place(3504, 366, 0x100, 0, cur=5, f3=0, floor=True, prev=0x59)
        rows = lab.run(160, padf=lambda u, f: pad)
        mon_rows = [r for r in rows if r["f23"] & 0x0C and r["y"] > 700]
        stable = rows[-3:]
        out[f"poc_route_from_upper_strip_{nm}"] = {
            "start": {"x": 3504, "y": 366, "state": "0x05", "vx": 256, "pad": pad}, "transitions": transitions(rows),
            "final_rows": [compact(r) for r in stable], "standing_on_monitor_top": stable[-1]["y"] == MONITOR["y"] - MON_EXT[1] and stable[-1]["f23"] & 2 != 0,
            "rows_with_both_wall_flags": sum(1 for r in rows if r["f23"] & 12 == 12), "max_x": max(r["x"] for r in rows)}
    return out


def natural_fall_sweep(rom: bytes, lab: Lab | None = None) -> dict:
    """Natural arrivals: Sonic released in the shaft above the monitor chamber in state $0E or $14, every pad value, several X and incoming X speeds; 70 original updates each."""
    lab = lab or Lab(rom, "mghz", 0)
    outcomes: dict = {}
    n = both_cases = 0
    pop = 0
    for cur in (0x0E, 0x14):
        for pad, pn in ((0, "neutral"), (4, "left"), (8, "right")):
            for x in range(3540, 3580, 4):
                for vx in (0, 256):
                    lab.place(x, 700, vx, 0x100, cur=cur, f3=1, floor=False, prev=0)
                    rows = lab.run(70, padf=lambda u, f: pad)
                    n += 1
                    end = rows[-1]
                    xs = [r["x"] for r in rows]
                    jitter = sum(1 for a, b, c in zip(xs, xs[1:], xs[2:]) if (b - a) * (c - b) < 0)
                    both = any(r["f23"] & 12 == 12 for r in rows)
                    both_cases += both
                    if any(r["x"] >= WALL_X for r in rows):
                        pop += 1
                    key = ("standing_on_monitor_top" if end["y"] == 790 and end["f23"] & 2 else "left_chamber_or_other")
                    outcomes[key] = outcomes.get(key, 0) + 1
                    outcomes[f"{h(cur, 2)}_pad_{pn}_both_wall_flags"] = outcomes.get(f"{h(cur, 2)}_pad_{pn}_both_wall_flags", 0) + (1 if both else 0)
                    outcomes["x_oscillation_cases"] = outcomes.get("x_oscillation_cases", 0) + (1 if jitter > 2 else 0)
    return {"evidence": "EMULATED ORIGINAL FRAME (whole game, MGHZ1 monitor record 16 awake)", "cases": n, "cases_with_both_wall_flags_f23_bits_2_and_3": both_cases, "cases_with_player_x_ge_3584": pop, "outcome_counts": outcomes}


def wedge_fixtures(rom: bytes, lab: Lab | None = None) -> dict:
    lab = lab or Lab(rom, "mghz", 0)
    lab.place(3540, 700, 0, 0x100, cur=0x0E)
    lab.run(3, padf=lambda u, f: 0)                 # the awake monitor object is created by the first frames after the teleport
    slot = monitor_slot(lab)
    cases = {
        "synthetic_push_into_wall_then_terrain_return": wedge_case(lab, 3570, 808, 0x0E, 8, name="SYNTHETIC: Sonic placed inside the monitor box beside the wall, state $0E, hold Right"),
        "synthetic_same_in_special_fall": wedge_case(lab, 3570, 808, 0x14, 8, name="SYNTHETIC: same placement, state $14"),
        "synthetic_guard_skips_push": wedge_case(lab, 3575, 808, 0x0E, 8, name="SYNTHETIC: Sonic already against the wall (terrain right-wall bit set), state $0E, hold Right"),
        "synthetic_no_input": wedge_case(lab, 3575, 806, 0x0E, 0, name="SYNTHETIC: against the wall, no input"),
        "synthetic_floor_line_push_pops_to_monitor_top": wedge_case(lab, 3570, 806, 0x0E, 0, vy=0x100, name="SYNTHETIC: deep overlap, no input, Y speed +1.0: the one-frame push into the wall at the floor line "
                                                                                                          "makes the floor projection pop Sonic up 32 px, then he lands on the monitor top"),
        "natural_top_landing_from_above": wedge_case(lab, 3572, 700, 0x14, 8, vy=0x100, frames=40, name="NATURAL-LIKE: state $14 released above the chamber, hold Right"),
    }
    return {"evidence": "EMULATED ORIGINAL FRAME; start states are SYNTHETIC controls except where named natural", "monitor": dict(MONITOR, slot_present=slot is not None,
            extents="Sonic 8x24 / monitor 10x24 (+$2C/+$2D)"), "cases": cases}


def monitor_chamber_grid(rom: bytes, lab: Lab | None = None) -> dict:
    """SYNTHETIC controls: Sonic placed anywhere in the monitor/wall chamber (X 3552..3575, Y 786..830) in state $0E and $14, no input, 12 original updates each."""
    lab = lab or Lab(rom, "mghz", 0)
    cells = []
    summary = {"cases": 0, "first_contact_classes": {}, "pushed_into_wall_first_frame": 0, "ended_stable": 0, "ended_with_both_wall_flags": 0, "never_stable": 0}
    for cur in (0x0E, 0x14):
        for x in range(3552, 3576, 3):
            for y in range(786, 831, 4):
                lab.place(x, y, 0, 0x100, cur=cur, f3=1, floor=False, prev=0)
                rows = lab.run(12, padf=lambda u, f: 0, events=True)
                first = next((r for r in rows if r.get("cap", {}).get("solid_calls")), None)
                cls = classify_contact(first["cap"]["solid_calls"][0]["x"], first["cap"]["solid_calls"][0]["y"]) if first else 0
                final = rows[-1]
                stable = rows[-1]["x"] == rows[-2]["x"] == rows[-3]["x"] and rows[-1]["y"] == rows[-2]["y"] == rows[-3]["y"]
                pushed = any(r["x"] >= WALL_X for r in rows)
                both = final["f23"] & 12 == 12
                summary["cases"] += 1
                summary["first_contact_classes"][str(cls)] = summary["first_contact_classes"].get(str(cls), 0) + 1
                summary["pushed_into_wall_first_frame"] += pushed
                summary["ended_stable"] += stable
                summary["ended_with_both_wall_flags"] += both
                summary["never_stable"] += (not stable)
                cells.append([h(cur, 2), x, y, cls, int(pushed), int(stable), final["x"], final["y"], final["f23"], final["cur"]])
    return {"evidence": "EMULATED ORIGINAL FRAME with SYNTHETIC placements", "columns": ["state", "x", "y", "first_monitor_class", "x_reached_wall", "stable_last_3", "final_x", "final_y", "final_d523", "final_state"],
            "summary": summary, "cells": cells}


def solid_guard_matrix(rom: bytes) -> dict:
    """Original $5FA0 with the monitor's extents: classification x D523 guard bit x camera-edge guard, on controlled RAM (the existing 20,000-case grid proves the model in general).

    Guards (BYTE-VERIFIED $5FA0..$6064): above/below skip when D523 bit0/bit1 is already set; right skips when D523 bit2 is set OR playerX > cameraX + $E0; left skips when D523 bit3 is set OR
    playerX <= cameraX + $20.
    """
    import collision_geometry as G
    o = G._oracle_for(rom)
    m = o.mem
    rows = []
    px, py = 3000, 500
    screen = {"normal (player at screen X 100)": 100, "right of cam+$E0 (screen X 230)": 230, "at or left of cam+$20 (screen X 20)": 20}
    for name, dx, dy, bit in (("above", 2, -20, 1), ("below", 2, 20, 2), ("right", 15, -3, 4), ("left", -15, -3, 8)):
        for d523 in (0, bit):
            for label, sx in screen.items():
                ix = 0xD540
                ox, oy = px - dx, py - dy
                m[ix + 0x11], m[ix + 0x12] = ox & 255, ox >> 8
                m[ix + 0x14], m[ix + 0x15] = oy & 255, oy >> 8
                o.word(0xD511, px)
                o.word(0xD514, py)
                m[0xD52C], m[0xD52D] = 8, 24
                m[ix + 0x2C], m[ix + 0x2D] = 10, 24
                m[ix + 3] = 0x80
                m[ix + 0x21] = 0
                m[0xD503] = 0
                m[0xD523] = d523
                o.word(0xD174, px - sx)
                o.cpu.ix = ix
                o.call(SOLID_OBJECT)
                rows.append({"classification": name, "d523_bit_already_set": bool(d523), "camera_case": label, "x_moved": o.word(0xD511) != px, "y_moved": o.word(0xD514) != py,
                             "new_x": o.word(0xD511), "new_y": o.word(0xD514)})
    return {"evidence": "CONTROLLED ROUTINE RESULT ($5FA0, object slot $D540, Sonic 8x24 vs 10x24, +$03 bit7 set)", "rows": rows,
            "reference_model": "tools/collision_geometry.py model_5fa0 (20,000 random cases, 0 mismatches)"}


# --------------------------------------------------------------------------- #
# C. which player states acquire which support (EMULATED ORIGINAL FRAME, every state 0..$34 forced as the requested state, falling +1.0 from above the surface)
# --------------------------------------------------------------------------- #
SUPPORT_SURFACES = {
    # name: (lab key, x, top/anchor reference y, description)
    "one_way_41": ("mghz1", 2768, 224, "MGHZ1 cell (86,7) block $F9, header $41 (one-way bit6, type 1), four air cells above"),
    "strip_19": ("mghz1", 720, 352, "MGHZ1 cell (22,11) block $85, header $59 (one-way, surface $19)"),
    "solid_control": ("gpz2", 1744, 256, "GPZ2 cell (54,8) block $01, header $81 (ordinary solid)"),
    "deck_1C": ("gpz2", 144, 192, "GPZ2 cell (4,6) block $8D, header $9C (solid, surface $1C, the 'isometric deck')"),
    "platform_28": ("gpz2", 1584, 384, "GPZ2 type $28 parameter $83 (sag/fall platform), placement (1584,384)"),
}
STATES_ALL = list(range(0x35))
STATE_NOTES = {0x0A: "normal jump (descending)", 0x0B: "upright spring ascent/apex", 0x0E: "ordinary fall", 0x14: "special fall", 0x1B: "ramp launch", 0x1C: "diagonal spring", 0x11: "Rocket Shoes",
               0x12: "Spring Shoes", 0x1E: "hurt", 0x1F: "death"}


def support_run(lab: Lab, name: str, state: int, marker: int | None = None, frames: int = 80, near: bool = False) -> dict:
    key, x, ref, _ = SUPPORT_SURFACES[name]
    plat = name == "platform_28"
    y0 = ref - (80 if plat else 18 + 80)
    if near and not plat:
        y0 = ref - 18 + 2                    # foot probe (y+18) starts 2 rows inside the surface cell: the first sample IS the surface, so no air sample can clear the marker
    lab.place(x, y0, 0, 0x100, cur=state, f3=1, floor=False, prev=0, p24=marker)
    rows = lab.run(frames, padf=lambda u, f: 0)
    tail = rows[-8:]
    plateau = max(r["y"] for r in tail) - min(r["y"] for r in tail) <= 1
    owner = max(r["d3c0"] for r in rows)
    grounded = bool(tail[-1]["f22"] & 2 or tail[-1]["f23"] & 2 or tail[-1]["d3c0"])
    out = "supported" if plateau and grounded and tail[-1]["y"] < y0 + 160 else "not_supported"
    acq = next((r for r in rows if (r["f22"] & 2 or r["f23"] & 2 or r["d3c0"]) and r["y"] > y0 + 20), None)
    return {"state": h(state, 2), "outcome": out, "acquired_at_update": acq["u"] if acq else None, "acquired_y": acq["y"] if acq else None, "final_y": rows[-1]["y"],
            "final_state": h(rows[-1]["cur"], 2), "max_y": max(r["y"] for r in rows), "start_y": y0, "owner_seen": owner, "floor_flags_end": rows[-1]["f22"] & 3,
            "states_seen": sorted({h(r["cur"], 2) for r in rows}), "marker_end": rows[-1]["p24"]}


def support_matrix(rom: bytes) -> dict:
    labs = {"mghz1": Lab(rom, "mghz", 0), "gpz2": Lab(rom, "gpz", 1)}
    out = {}
    for name in SUPPORT_SURFACES:
        lab = labs[SUPPORT_SURFACES[name][0]]
        out[name] = {"surface": SUPPORT_SURFACES[name][3], "states": {h(s, 2): support_run(lab, name, s) for s in STATES_ALL}}
    marker_variants = {}
    for name in ("one_way_41", "deck_1C"):
        lab = labs[SUPPORT_SURFACES[name][0]]
        marker_variants[name] = {h(s, 2): support_run(lab, name, s, marker=1, near=True) for s in (0x0A, 0x0E, 0x14, 0x0B)}
    summary = {}
    for name, v in out.items():
        sup = [s for s, r in v["states"].items() if r["outcome"] == "supported"]
        acq = [s for s, r in v["states"].items() if r["acquired_at_update"] is not None]
        summary[name] = {"retained_support_states": sup, "acquired_support_at_any_update_states": acq, "acquired_but_not_retained_states": [s for s in acq if s not in sup],
                         "never_acquired_states": [s for s in v["states"] if s not in acq]}
    return {"evidence": "EMULATED ORIGINAL FRAME (whole game; each state forced as the REQUESTED state so the engine loads that state's own script/callback; Sonic released 80 px above the surface "
                        "at vy = +1.0, no input, 80 original updates); outcome 'supported' = Y plateau over the last 8 updates with a floor flag or support owner",
            "surfaces": {n: v["surface"] for n, v in out.items()}, "summary": summary, "per_state": {n: v["states"] for n, v in out.items()},
            "marker_set_variants_SYNTHETIC": {"note": "marker (+$24 bit0) = 1 at the start and the foot starts 2 rows inside the surface cell", "per_surface": marker_variants},
            "fall_state_notes": {h(k, 2): v for k, v in STATE_NOTES.items()}}


# --------------------------------------------------------------------------- #
# A. state $14 - collision passes, exits, edge clamp, marker lifetime, one-way gate
# --------------------------------------------------------------------------- #
def trace_row(r: dict, keys=("u", "x", "y", "vy", "cur", "req", "f22", "f23", "p24", "d36c")) -> dict:
    d = compact(r, keys)
    ev = r.get("ev", [])
    marks = [i for i, e in enumerate(ev) if e == "PLAYER"]
    if len(marks) > 1:
        ev = ev[:marks[1]]
    d["calls"] = ev
    return d


def pass_trace(rom: bytes) -> dict:
    """PC-hook order of the original routines for state $14 vs $0E: a mid-air update, the first and following updates over a one-way strip, and the landing update."""
    lab = Lab(rom, "mghz", 0)
    out = {}
    for cur in (0x14, 0x0E):
        lab.place(3300, 450, 0, 0x100, cur=cur, f3=1, floor=False, prev=0, p24=0)
        rows = lab.run(80, padf=lambda u, f: 0, events=True)
        sel = {"mid_air": next(r for r in rows if r["u"] == 3), "first_strip_sample": next(r for r in rows if r["d36c"] & 31 == 0x19),
               "update_after_first_strip_sample": rows[next(i for i, r in enumerate(rows) if r["d36c"] & 31 == 0x19) + 1]}
        out[h(cur, 2)] = {k: trace_row(v) for k, v in sel.items()}
    lab2 = Lab(rom, "gpz", 1)
    lab2.place(528, 686, 0x100, 0, cur=5, f3=0, floor=True, prev=0x59)
    rows = lab2.run(60, padf=lambda u, f: 0, events=True)
    land = next(r for i, r in enumerate(rows) if i and rows[i - 1]["cur"] == 0x14 and r["req"] == 5)
    out["landing_from_14_on_solid_floor_GPZ2"] = trace_row(land)
    return {"evidence": "EMULATED ORIGINAL FRAME (PC hooks: calls listed in execution order inside one player update; 'merge_64CB' directly after 'one_way_gate_6FBB' is the projection's own merge, "
                        "absent when the projection is bypassed)", "updates": out,
            "executed_in_both_states": ["update_3FEF", "input_tables ($4141)", "x_integration ($402A)", "y_integration ($4097)", "terrain_pass ($690B): floor $691A + $6F61, sides $715E, ceiling $73C9, "
                                        "terrain rings $753E, merges $64CB", "damage_gate_48BC"],
            "skipped_in_14_only": ["one-way floor projection after the strip handler has set +$24 bit0 (the gate $6FBB returns before the projection)"]}


def exit_fixtures(rom: bytes) -> dict:
    air = Air(rom)
    o, m = air.o, air.m
    out = {}

    def land(state):
        t = I.TerrainLab(rom, "mghz1")
        a = Air.__new__(Air)
        a.t, a.o, a.m, a.rom = t, t.o, t.o.mem, rom
        w = I.act_data(rom, "mghz1")["width"]
        a.setup(state, vy=0x200, x=AIR_X, y=520 + 3)          # foot y+18 = 541: 3 rows into cell (106,16)
        a.m[0xC001 + 16 * w + AIR_X // 32] = 0x01
        a.m[0xD36C] = 0x81
        a.o.call(CB_STRIP_FALL if state == 0x14 else CB_FALL)
        return a.snap()
    for state in (0x14, 0x0E):
        out[f"landing_on_solid_{h(state, 2)}"] = land(state)
    # hurt / death by the shared damage gate $48BC (state independent)
    for state in (0x14, 0x0E):
        for rings, label in ((0x10, "with_rings"), (0x00, "no_rings")):
            air.setup(state, vy=0x100)
            m[0xD3B0] = 1
            m[0xD29A] = rings
            o.call(CB_STRIP_FALL if state == 0x14 else CB_FALL)
            out[f"damage_request_{h(state, 2)}_{label}"] = air.snap()
            m[0xD3B0] = 0
            m[0xD29A] = 0
    # screen-Y death boundary $401A
    for state in (0x14, 0x0E):
        air.setup(state, vy=0x300)
        o.word(0xD51C, 0xD0)
        o.call(CB_STRIP_FALL if state == 0x14 else CB_FALL)
        out[f"screen_y_death_{h(state, 2)}"] = air.snap()
        air.setup(state, vy=0x300)
        o.word(0xD51C, 0xCF)
        o.call(CB_STRIP_FALL if state == 0x14 else CB_FALL)
        out[f"screen_y_just_above_death_{h(state, 2)}"] = air.snap()
    # a jump press while airborne does nothing ($45ED returns on +$03 bit0)
    for state in (0x14, 0x0E):
        out[f"jump_press_{h(state, 2)}"] = air.update(state, jump=0x10, pad=0x10, vy=0x100)
    return {"evidence": "CONTROLLED ROUTINE RESULT (callbacks $3A37/$3A48; one block patched into the foot cell where stated)",
            "cases": out,
            "reading": "Both states share: landing request $05 when the merged contact byte has bit1 (floor) set; hurt $1E (rings) / death $1F (no rings) via $48BC; screen-Y death at D51C >= $D0; "
                       "no air jump ($45ED returns while +$03 bit0 is set)."}


def edge_clamp_fixture(rom: bytes) -> dict:
    """$4141 screen-edge clamp (states < $29, applied before the table lookup): original behavior for $14 and $0E at camera+4..+8 and camera+$F8..$FB."""
    air = Air(rom)
    rows = []
    for state in (0x14, 0x0E):
        for sx, vx, pad in ((8, -0x200, 4), (12, -0x200, 4), (16, -0x200, 4), (0xF8, 0x200, 8), (0xF0, 0x200, 8), (0xE0, 0x200, 8)):
            air.setup(state, vx=vx, pad=pad, vy=0x100, cx_off=sx)
            o = air.o
            o.word(0xD174, 3400 - sx)
            before = air.snap()
            o.call(CB_STRIP_FALL if state == 0x14 else CB_FALL)
            a = air.snap()
            rows.append({"state": h(state, 2), "screen_x_before": sx, "vx_before": vx, "x_after": a["x"], "screen_x_after": a["x"] - (3400 - sx), "vx_after": a["vx"]})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "rows": rows,
            "reading": "The original keeps Sonic inside screen X 16..247 for EVERY state below $29 (including $14) by repositioning to the edge and zeroing vx; this is viewport-relative (EDGE) behavior and "
                       "is independent of state $14's zero air control"}


def marker_lifetime(rom: bytes) -> dict:
    lab = Lab(rom, "gpz", 1)
    runs = {}
    for label, cur, vx, pad, p24 in (("walk_on_ordinary_floor_marker_set", 5, 256, 8, 1), ("run_on_ordinary_floor_marker_set", 6, 1024, 8, 1), ("idle_on_ordinary_floor_marker_set", 1, 0, 0, 1),
                                     ("walk_on_ordinary_floor_marker_clear", 5, 256, 8, 0)):
        lab.place(1744, 238, vx, 0x700, cur=cur, f3=0, floor=True, prev=0x81, p24=p24)
        rows = lab.run(8, padf=lambda u, f, pad=pad: pad)
        runs[label] = {"start": {"state": h(cur, 2), "vx": vx, "marker": p24, "surface": "GPZ2 cell (54,8) solid block $01"}, "rows": [compact(r) for r in rows[:5]]}
    jumps = {}
    for label, cur, vx, pad in (("run_+4.0_on_strip_then_jump", 6, 0x400, 8), ("idle_on_strip_then_jump", 1, 0, 0)):
        lab.place(528, 686, vx, 0, cur=cur, f3=0, floor=True, prev=0x59)
        press = 5 if cur == 6 else 3
        rows = lab.run(70, padf=lambda u, f, pad=pad, press=press: (pad | 16) if press <= u < press + 2 else pad)
        jumps[label] = {"press_update": press, "transitions": transitions(rows)}
    return {"evidence": "EMULATED ORIGINAL FRAME (GPZ2)", "marker_cleared_by_walk_or_run_frame_selector_on_a_non_19_surface": runs, "jump_from_strip_clears_marker_and_landing_sets_it_again": jumps}


def one_way_gate_matrix(rom: bytes) -> dict:
    """$691A with the foot 3 rows inside one block, previous surface = that block's flags, for REQUESTED states 0..$34 x marker bit0 0/1: does the floor projection move Sonic?"""
    t = I.TerrainLab(rom, "mghz1")
    o, m = t.o, t.o.mem
    w = I.act_data(rom, "mghz1")["width"]
    blocks = {"one_way_0D": 0x0D, "strip_85": 0x85, "solid_01": 0x01, "deck_8C": 0x8C}
    depth = {"one_way_0D": 3, "strip_85": 3, "solid_01": 3, "deck_8C": 18}      # foot row inside the cell; the deck's floor contour is row 16
    cx, cy = AIR_X // 32, 16
    out = {}
    for name, blk in blocks.items():
        flags = R.header(rom, blk)["flags"]
        res = {}
        for req in range(0x35):
            for marker in (0, 1):
                m[0xC000:0xE000] = t.base
                m[0xC001 + cy * w + cx] = blk
                y = cy * 32 - 18 + depth[name]
                o.word(0xD511, AIR_X)
                o.word(0xD514, y)
                m[0xD510] = m[0xD513] = 0
                o.word(0xD516, 0)
                o.word(0xD518, 0x0200)
                m[0xD501] = 0x0E
                m[0xD502] = req
                m[0xD503] = 1
                m[0xD522] = 0
                m[0xD523] = 0
                m[0xD524] = marker
                m[0xD36C] = flags
                m[0xD52C], m[0xD52D] = 8, 24
                o.cpu.ix = 0xD500
                o.call(TERRAIN_FLOOR)
                res.setdefault(h(req, 2), {})[marker] = o.word(0xD514) - y
        bypass = sorted(r for r, v in res.items() if v[1] != v[0])
        out[name] = {"block": h(blk, 2), "header_flags": h(flags, 2), "states_whose_projection_differs_with_marker_set": bypass,
                     "y_delta_marker_clear": {r: v[0] for r, v in res.items() if r in ("0x05", "0x0E", "0x14")}, "y_delta_marker_set": {r: v[1] for r, v in res.items() if r in ("0x05", "0x0E", "0x14")}}
    return {"evidence": "CONTROLLED ROUTINE RESULT ($691A)", "blocks": out,
            "reading": "Only the pair (+$24 bit0 set, REQUESTED state $14) changes the projection, and only on one-way (header bit6, bit7 clear) blocks; solid/deck blocks project identically"}


def spring_exit_fixture(rom: bytes) -> dict:
    """Whole game: state $14 / $0E released above the MGHZ1 terrain upright spring (cell (110,25), block $30, type 9) - state independent upright launch."""
    lab = Lab(rom, "mghz", 0)
    out = {}
    for cur in (0x14, 0x0E):
        lab.place(3536, 700, 0, 0x100, cur=cur, f3=1, floor=False, prev=0, p24=0)
        rows = lab.run(120, padf=lambda u, f: 0, stop=lambda r, rs: r["req"] == 0x0B)
        hit = rows[-1]
        out[h(cur, 2)] = {"request_0B_update": hit["u"] if hit["req"] == 0x0B else None, "row": compact(hit), "previous_row": compact(rows[-2])}
    return {"evidence": "EMULATED ORIGINAL FRAME", "spring_cell": "MGHZ1 (110,25) block $30 (header $49, type 9)", "cases": out}


def strip_census(rom: bytes) -> dict:
    """Every run of surface-$19 cells in the 18 normal acts and what lies below it (first non-air cell per column)."""
    def cls(b):
        fl = R.header(rom, b)["flags"]
        if fl & 0x1F == 0x19:
            return "strip19"
        if fl == 0:
            return "air"
        if fl & 0x80:
            return "solid"
        if fl & 0x40:
            return "one_way"
        return f"other_{fl:02X}"
    acts = {}
    for key in I.ACTS:
        a = I.act_data(rom, key)
        w, c = a["width"], a["cells"][:4095]
        rows = len(c) // w
        runs = []
        for cy in range(rows):
            cx = 0
            while cx < w:
                if cls(c[cy * w + cx]) != "strip19":
                    cx += 1
                    continue
                x0 = cx
                while cx < w and cls(c[cy * w + cx]) == "strip19":
                    cx += 1
                below = {}
                gaps = []
                for x in range(x0, cx):
                    y = cy + 1
                    while y < rows and cls(c[y * w + x]) == "air":
                        y += 1
                    k = cls(c[y * w + x]) if y < rows else "level_bottom"
                    below[k] = below.get(k, 0) + 1
                    gaps.append(y - cy - 1)
                runs.append({"row": cy, "cells_x": [x0, cx - 1], "world_y_of_strip_top": cy * 32, "air_cells_below_min": min(gaps), "first_cell_below_by_class": dict(sorted(below.items()))})
        if runs:
            acts[key] = runs
    return {"evidence": "DECODED DATA (layout cells x header flags)", "acts_with_strips": sorted(acts), "run_count": sum(len(v) for v in acts.values()), "runs": acts,
            "other_acts": "no surface-$19 cell in THZ1-3, SEZ, APZ, EEZ or GPZ3"}


# --------------------------------------------------------------------------- #
# classification, build, CLI
# --------------------------------------------------------------------------- #
REGIONS = [(0x3783, 0x37CC, "walk callback $3783 + suffix $3791 (entry to $14)"), (0x384D, 0x386F, "run callback $384D"), (0x3A37, 0x3A59, "callbacks $3A37 ($0E) and $3A48 ($14)"),
           (0x3FEF, 0x401A, "shared update $3FEF"), (0x402A, 0x429D, "movement core: clamps, integration, $4141 input/friction tables lookup"),
           (0x45B3, 0x45ED, "stand/landing setters $45B3/$45CE"), (0x463C, 0x4680, "fall setters $463C/$4663"), (0x48A7, 0x4A33, "facing + damage gate $48BC + death"),
           (0x5FA0, 0x6065, "solid helper $5FA0"), (0x6328, 0x640B, "overlap $6328"), (0x690B, 0x6973, "terrain pass $690B/$691A"), (0x6B14, 0x6B2C, "surface $1B/$19 handlers"),
           (0x6C45, 0x6C82, "surface-zero handler $6C45"), (0x6F61, 0x7056, "floor projection + one-way gate $6FBB"), (0x715E, 0x7300, "side collision $715E")]
BANK_REGIONS = [(30, 0x8814, 0x8908, "type $28 support/carry $8814..$88FB"), (12, 0x8EE1, 0x8F76, "Sonic walk frame selector (marker clear on non-$19 surface)"),
                (12, 0x8CB4, 0x8D36, "other-character run selector (marker clear)")]


def region_hashes(rom: bytes) -> list:
    out = []
    for a, b, why in REGIONS:
        out.append({"cpu": h(a), "end_exclusive": h(b), "rom": h(a, 5), "length": b - a, "sha256": sha(rom[a:b]), "purpose": why})
    for bank, a, b, why in BANK_REGIONS:
        off = bank * 0x4000 + a - 0x8000
        out.append({"bank": bank, "cpu": h(a), "end_exclusive": h(b), "rom": h(off, 5), "length": b - a, "sha256": sha(rom[off:off + b - a]), "purpose": why})
    return out


def classification() -> list:
    C, P_, A_, U = "CANONICAL", "POC DIVERGENCE", "EXPLICIT ADAPTER CANDIDATE", "UNRESOLVED"
    return [
        {"id": "A1", "observation": "Left/Right are read in state $14 but give zero horizontal acceleration", "class": C,
         "evidence": "all dry/water/friction table words of state $14 are 0 ($4141); 5,296-case sweep of the original callback matches the model with 0 mismatches; whole-game MGHZ1/GPZ2 runs hold vx constant"},
        {"id": "A2", "observation": "X speed is preserved (no friction) while in $14; only a wall (D523 bit2/3), the $402A maximum clamp (+/-4.0) or the screen-edge clamp changes it", "class": C,
         "evidence": "friction word of $14 is 0; wall zeroing seen at the monitor wedge and the MGHZ1 wall; edge clamp fixture"},
        {"id": "A3", "observation": "Gravity in $14 equals ordinary fall $0E (+$0030/update, terminal +7.0; water +$0018/+4.0); entry sets Y speed to +1.0 and keeps X speed", "class": C,
         "evidence": "1,400-case vertical sweep, setter diff $4663 vs $463C"},
        {"id": "A4", "observation": "Walking onto/over a surface-$19 strip slower than the current maximum speed (or stopping on it, or landing on it from a fall/jump) requests $14 at once", "class": C,
         "evidence": "only entry: $37C3 -> $4663 in the walk callback; run -> walk -> $14 chain; landing always requests walk $05 ($45CE); whole-game MGHZ1/GPZ2 fixtures"},
        {"id": "A5", "observation": "All terrain passes run in $14 exactly as in $0E; the only skipped step is the one-way floor projection while +$24 bit0 is set and the REQUESTED state is $14", "class": C,
         "evidence": "PC-hook order trace; one-way gate matrix (4 block kinds x 53 requested states x marker 0/1)"},
        {"id": "A6", "observation": "A $14 fall passes through a second one-way surface-$19 strip below the first (the lower MGHZ1 strip) and continues to the pit", "class": C,
         "evidence": "the strip's foot sample sets the marker (surface handler $6B23 runs after the projection of the same update), so the next update's projection is bypassed; whole-game MGHZ1 trace"},
        {"id": "A7", "observation": "The marker (+$24 bit0) is set by every foot sample of surface $19, cleared only by a surface-0 foot sample, a normal jump, the ordinary fall setter $463C and the walk/run frame selectors on a non-$19 surface; "
                              "every other surface type leaves it unchanged", "class": C,
         "evidence": "26-type matrix, setter diff, GPZ2 fixtures, whole-game timelines"},
        {"id": "A8", "observation": "Landing from $14 requests walk $05 (clears airborne/attack/hurt bits, max speed $0400, camera byte $D289 = $60); it is NOT an idle request, so a landing on a strip hops straight back to $14", "class": C,
         "evidence": "landing fixtures + whole-game GPZ2/MGHZ1"},
        {"id": "A9", "observation": "Original MGHZ1 pit below the lower strip has no floor: the uncontrolled fall ends in the screen-relative death ($D51C >= $D0) at world Y 987..991 (camera Y 777..780 behind its bottom limit 784)", "class": C,
         "evidence": "whole-game traces (death requested at Y987 / Y991); act header camera bottom limit 784"},
        {"id": "A10", "observation": "POC death line for the same fall is Y1043 (its harness camera bottom 832); the canonical camera bottom limit is height-240 = 784 (+$D0 = 992)", "class": U,
         "evidence": "POC diagnosis camera clamp vs act header +18; the POC's camera-bottom choice may be an intentional widescreen adapter - needs an explicit decision"},
        {"id": "B1", "observation": "A monitor ($10) that Sonic falls onto is a SOLID FLOOR: $5FA0 projects the player onto its top edge (Y = monitorY - 24) and the mirrored contact makes D523 bit1 true", "class": C,
         "evidence": "whole-game MGHZ1 route (3504,366): Sonic stands on the monitor at (3575,790) with f23 = 6; 63/120 natural falls end there, 0 snag"},
        {"id": "B2", "observation": "POC monitor does not project the top contact and applies no D523/camera guard to its side/bottom pushes", "class": P_,
         "evidence": "POC SOURCE (READ-ONLY): OBJ_chaos_object_10/Step_0.gml 'Top-of-box standing is not projected here'; only the bottom push honors D523 bit1"},
        {"id": "B3", "observation": "Monitor side push toward a wall: the original pushes the player to monitorX+18 even into terrain ONCE, terrain pushes back on the next update, then the D523 guard (bit2 set) stops all further pushes", "class": C,
         "evidence": "SYNTHETIC placement fixtures: update 6 X = 3586, update 7 X = 3575 with D523 = 12, no re-push; 30 chamber-grid cases"},
        {"id": "B4", "observation": "The POC's repeating push/pull (opposing flags, little or no X movement) is not reproduced by the original", "class": P_,
         "evidence": "all 30 right-class chamber-grid placements end wedged (D523 = 14, Y814) or on the monitor top (D523 = 6, Y790) within 12 updates; 120 natural falls give 0 X oscillations and 0 double wall flags"},
        {"id": "B8", "observation": "After a one-frame push into the wall at the floor line the next floor projection pops Sonic up 32 px (Y814 -> 782), after which he falls back and stands on the monitor top; the POC's Y782 event is therefore not "
                              "itself a divergence", "class": C,
         "evidence": "SYNTHETIC fixture synthetic_floor_line_push_pops_to_monitor_top (D523 = 14 at the pop, top contact at update 9, final (3575,790) D523 = 6)"},
        {"id": "B5", "observation": "Being wedged between the monitor and the wall (D523 = 14, vx 0, Right or nothing held) is a stable original state if Sonic is placed inside the box; unreachable by natural falls; jump leaves it", "class": C,
         "evidence": "SYNTHETIC fixtures; reachability sweep"},
        {"id": "B6", "observation": "State $0E vs $14 does not change the monitor/wall outcome; it only changes the approach (no steering in $14)", "class": C,
         "evidence": "chamber grid and natural sweep give identical outcome counts for both states"},
        {"id": "B7", "observation": "$5FA0 right/left pushes are skipped when the player is beyond camera+$E0 / at or left of camera+$20 (viewport-relative guards); the guard must not be silently widened or dropped on a wide view", "class": A_,
         "evidence": "guard matrix; EDGE-relative semantics (docs/viewport-semantics-audit.md)"},
        {"id": "C1", "observation": "Ordinary one-way terrain ($41 blocks): every fall-capable state ($0A, $0B, $0E, $14, $1B, $1C, $11) acquires and keeps support; Spring Shoes $12 acquires then relaunches", "class": C,
         "evidence": "whole-game matrix, 53 forced states"},
        {"id": "C2", "observation": "Surface-$19 strips: $0E, $0A, $0B, $1C, $1D... acquire support on landing but lose it when the walk callback hops to $14; $14 itself never acquires it; only max-speed running crosses", "class": C,
         "evidence": "whole-game matrix + strip fixtures"},
        {"id": "C3", "observation": "Type $28 platforms: support is independent of the player state (acquired by every state whose update lets the object phase run, incl. $14) subject only to the Y-speed gate", "class": C,
         "evidence": "whole-game GPZ2 (1584,384) matrix; earlier controlled audit (all 52 states)"},
        {"id": "C4", "observation": "GPZ solid decks (surface $1C blocks $8C..$97): every fall-capable state acquires support, including $14 with the marker set (the solid path never reads the marker)", "class": C,
         "evidence": "whole-game matrix + marker-set variants + one-way gate matrix (deck row)"},
        {"id": "C5", "observation": "Windows 'uncontrollable fall through two isometric platforms': explained as the two MGHZ1 $19 strips (blocks $85/$87) - canonical. If the pass-through was over $1C decks or $28/$83 platforms it would be a POC divergence", "class": U,
         "evidence": "the POC diagnosis places both strips at X102..111/Y12 and X95..109/Y27; the original passes through both; decks/platforms are never passed through by $14 in the original"},
        {"id": "D1", "observation": "A QoL air-steering adapter for $14 (use the $0E tables) would be a deliberate non-canonical change", "class": A_,
         "evidence": "A1; do not apply before Windows acceptance of the canonical behavior"},
    ]


def agents_candidates() -> list:
    return [
        "State $14 (special fall) has all-zero dry/water/friction input tables: Left/Right are read but produce zero acceleration and no friction; X speed is preserved (only walls, the +/-4.0 clamp and the "
        "screen-edge clamp change it). This is canonical, not a POC omission. Gravity and terrain passes equal ordinary fall $0E.",
        "The only entry to $14 is the walk callback with +$24 bit0 (strip marker) set and |vx| high byte != the current maximum (dry). Landing always requests walk $05, so a landing on a $19 strip slower than max "
        "hops straight back into $14. Only max-speed running crosses a strip.",
        "The strip marker is set by every surface-$19 foot sample (after that update's projection) and cleared only by a surface-0 foot sample, jump, $463C or the walk/run selectors on non-$19 ground. "
        "Requested $14 + marker bypasses one-way projection only (not solid decks, not type $28).",
        "A monitor ($10) is a solid floor from above: $5FA0 snaps Y to monitorY-24 and the mirrored contact supplies D523 bit1. Side/bottom/top pushes are skipped when D523 already has the matching bit "
        "(and, for left/right, outside the camera+$20..+$E0 window). A one-update push into a wall is canonical; a persistent push/pull snag is not.",
        "Viewport guards in $5FA0 (camera+$E0 / camera+$20) and the $4141 screen-edge clamp (X within camera+16..247 for every state below $29) are EDGE-relative; use explicit adapters for wide views.",
    ]


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    out: dict = {"rom_sha256": ROM_SHA256, "research_base": RESEARCH_BASE, "scope": "shared player fall / control audit (state $14, state $0E + monitor/wall, fall-state support); Research only",
                 "evidence_classes": ["DECODED DATA", "BYTE-VERIFIED ASSEMBLY", "SOURCE-TRACED BEHAVIOR", "CONTROLLED ROUTINE RESULT", "EMULATED ORIGINAL FRAME", "SYNTHETIC CONTROL",
                                      "POC SOURCE (READ-ONLY)", "UNRESOLVED"],
                 "static_only": static_only, "regions": region_hashes(rom)}
    part_a = {"input_tables": input_tables(rom), "cp14_sites": fixed_bank_cp14_sites(rom), "writers": state14_writers(rom), "setter_diff": setter_diff(rom),
              "surface_marker_matrix": surface_marker_matrix(rom), "one_way_gate_matrix": one_way_gate_matrix(rom), "horizontal_sweep": horizontal_sweep(rom), "vertical_sweep": vertical_sweep(rom),
              "air_fixtures": air_fixtures(rom), "edge_clamp": edge_clamp_fixture(rom), "exit_fixtures": exit_fixtures(rom), "strip_census": strip_census(rom)}
    part_b = {"monitor": dict(MONITOR, extents="Sonic 8x24, monitor 10x24 (+$2C/+$2D)", wall="column 112 (block $04, solid) from world X3584; standing floor row 26 (block $01) -> anchor Y814"),
              "solid_guard_matrix": solid_guard_matrix(rom),
              "frame_order": "per frame: player update (animation engine $64FA, state callback: X integration $402A, Y integration $4097, terrain $690B {floor $691A, sides $715E, ceiling $73C9, "
                             "rings $753E, merges $64CB}, damage gate $48BC) THEN the object list in slot order; the monitor's $5FA0 therefore sees the terrain flags of the same frame's merge, "
                             "and the player's next X integration sees D523 as merged at the end of the previous player pass (the monitor's mirrored D521 nibble is merged one pass later)"}
    part_c = {}
    if not static_only:
        mg = Lab(rom, "mghz", 0)
        part_a["strip_scenarios"] = strip_scenarios(rom)
        part_a["gpz2_strip_scenarios"] = gpz2_strip_scenarios(rom)
        part_a["pass_trace"] = pass_trace(rom)
        part_a["marker_lifetime"] = marker_lifetime(rom)
        part_a["spring_exit"] = spring_exit_fixture(rom)
        part_b["natural_monitor_falls"] = natural_monitor_falls(rom, mg)
        part_b["natural_fall_sweep"] = natural_fall_sweep(rom, mg)
        part_b["wedge_fixtures"] = wedge_fixtures(rom, mg)
        part_b["chamber_grid"] = monitor_chamber_grid(rom, mg)
        part_c["support_matrix"] = support_matrix(rom)
    out.update({"part_a_state_14": part_a, "part_b_monitor_wall": part_b, "part_c_fall_support": part_c, "classification": classification(), "agents_candidates": agents_candidates(),
                "poc_source_read_only": {"files": ["objects/OBJ_chaos_object_10/Step_0.gml", "scripts/SCR_chaos_box_contact/SCR_chaos_box_contact.gml", "docs/mghz-fall-control-diagnosis.md"],
                                         "facts": ["monitor Step: 'Top-of-box standing is not projected here' - cp_bits == 1 is never projected",
                                                   "monitor Step: only the bottom push consults D523 (contacts & 2); side pushes have no D523 or camera guard",
                                                   "POC diagnosis: $14 has zero acceleration in every imported movement table (matches the ROM); strip pass-through and monitor snag identical at 82ebc89"]}})
    return out


def dumps(data: dict) -> str:
    return json.dumps(data, indent=1) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    a = ap.parse_args()
    rom = L.load_rom(a.rom)
    text = dumps(build(rom, a.static_only))
    if a.check:
        if OUTPUT.read_text(encoding="utf-8") != text:
            raise SystemExit("cache mismatch: " + str(OUTPUT))
        print("player-fall-control cache matches")
    else:
        OUTPUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUTPUT} ({len(text)} bytes)")


if __name__ == "__main__":
    main()

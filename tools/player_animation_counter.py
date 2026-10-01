#!/usr/bin/env python3
"""Player animation counter `+$07` (research only, deterministic).

Recovers the minimum complete model of the animation record down-counter at the player slot (`$D507`)
needed to reproduce bit 0 for the terrain-ring probe `$753E`:  lifecycle, update order, per-state schedules,
speed/contact-dependent selectors, direct writes, transitions, and a pure-Python shadow model that is
differentially tested against the original engine `$64FA` and against whole-game play.

Output: data/rom-cache/player-animation-counter.json (numeric labels only).

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT,
EMULATED ORIGINAL FRAME, UNRESOLVED (same vocabulary as the earlier studies).

Usage:
  python tools/player_animation_counter.py ROM.sms [--check] [--static-only]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OUTPUT = ROOT / "data" / "rom-cache" / "player-animation-counter.json"
BANK = 0x0C                     # player scripts and selectors
STATE_TABLE = 0x8000            # type 1 state table (62 pointers)
LAST_REAL_STATE = 0x36
RING_DY = {0: -26, 1: -16}      # DE of $753E by +$07 bit 0
ANCHOR_BIAS = 18


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

# animation command argument lengths (bytes after "FF cc"), from the handlers at $66B9..$68F7
CMD_ARGS = {0x00: 0, 0x01: 2, 0x02: 4, 0x03: 1, 0x04: 6, 0x05: 4, 0x06: 1, 0x07: 2, 0x08: 4, 0x09: 2, 0x0A: 3, 0x0B: 2, 0x0C: 2, 0x0D: 5, 0x0E: 1, 0x0F: 2}

# (name, bank, start, end, purpose)
ROUTINES = [
    ("player_update", 0, 0x361D, 0x3657, "per update: engine $64FA, then state callback $5E91, then $4A74"),
    ("animation_engine", 1, 0x64FA, 0x65AF, "$64FA: state change, DEC (IX+7), record load"),
    ("animation_commands", 1, 0x6680, 0x68F8, "FF command dispatcher and handlers (restart, call, request, selector call, loop, ...)"),
    ("selector_walk_8ee1", BANK, 0x8EE1, 0x8F45, "state $05 selector: frame cycle $01.., duration table $8F2C by |X speed high byte|; side contact -> 2"),
    ("selector_run_8f45", BANK, 0x8F45, 0x8F76, "state $06 selector: frame cycle $07.., duration 4"),
    ("selector_roll_jump_8f76", BANK, 0x8F76, 0x900B, "states $09/$0A/$10/$1B selector: floor contact -> table $8FE0 by |X speed|; air -> 3"),
    ("selector_1d_900b", BANK, 0x900B, 0x903D, "state $1D selector: duration 6"),
    ("selector_17_9138", BANK, 0x9138, 0x9163, "state $17 selector: duration 3"),
    ("walk_duration_table", BANK, 0x8F2C, 0x8F3C, "16 bytes: 0A 08 06 04 ..."),
    ("floor_duration_table", BANK, 0x8FE0, 0x8FF0, "16 bytes: 0A 08 06 05 04 03 02 ..."),
    ("state_0b_branch_818f", BANK, 0x818F, 0x8194, "FF 08 condition for state $0B: carry = $D448 bit 0"),
    ("state_04_branch_80d9", BANK, 0x80D9, 0x810E, "FF 08 condition for state $04: carry except one zone-4 location"),
]


def routine_table(rom: bytes) -> list[dict]:
    out = []
    for name, bank, a, z, purpose in ROUTINES:
        o, e = rom_of(bank, a), rom_of(bank, z)
        out.append({"name": name, "bank": bank, "cpu_start": h(a), "cpu_end_exclusive": h(z), "rom_offset": h(o, 5), "length": e - o,
                    "sha256": sha(rom[o:e]), "first_16_bytes": rom[o:o + 16].hex(), "purpose": purpose})
    return out


# --------------------------------------------------------------------------- #
# 1. static: every write / decrement site of +$07
# --------------------------------------------------------------------------- #
def _loc(o: int) -> tuple[int, int]:
    b = o // 0x4000
    return b, (0 if b == 0 else 0x4000 if b == 1 else 0x8000) + o % 0x4000


# (bank, start CPU, end CPU, role) - classification of every site found by the byte scan
SITE_ROLES = [
    (1, 0x6510, 0x6511, "engine: DEC (IX+7) every update without a reload"),
    (1, 0x6549, 0x654A, "engine: record load, +$07 := duration byte"),
    (1, 0x68AB, 0x68AC, "FF 0D record: +$07 := C (not used by player scripts)"),
    (BANK, 0x8F28, 0x8F29, "selector $8EE1 (walk $05): +$07 := table $8F2C[|X speed hi|]"),
    (BANK, 0x8F40, 0x8F41, "selector $8EE1 side-contact branch: +$07 := 2"),
    (BANK, 0x8F71, 0x8F72, "selector $8F45 (run $06): +$07 := 4"),
    (BANK, 0x8FB4, 0x8FB5, "selector $8F76 floor branch: +$07 := table $8FE0[|X speed hi|]"),
    (BANK, 0x9007, 0x9008, "selector $8F76 air branch: +$07 := 3"),
    (BANK, 0x9038, 0x9039, "selector $900B (state $1D): +$07 := 6"),
    (BANK, 0x9067, 0x9068, "selector $903D: +$07 := 6 (not used by an eligible state)"),
    (BANK, 0x915E, 0x915F, "selector $9138 (state $17): +$07 := 3"),
    (BANK, 0x8CE8, 0x8CE9, "selector $8CB4 (other character walk): table lookup"),
    (BANK, 0x8D00, 0x8D01, "selector $8CB4 push branch (other character): 2"),
    (BANK, 0x8D31, 0x8D32, "selector $8D05 (other character run): 2"),
    (1, 0x500B, 0x500C, "camera structure loader $4FDC (IX = $D15E): not the player"),
    (1, 0x5F65, 0x5F66, "enemy-destroy conversion $5F54: object slot, not the player"),
    (1, 0x7544, 0x7545, "READ: terrain probe $753E, bit 0"),
]


def plus07_sites(rom: bytes) -> dict:
    pats = {
        "write_ix": rb"\xdd[\x77\x70\x71\x72\x73\x74\x75]\x07|\xdd\x36\x07.",
        "dec_inc_ix": rb"\xdd[\x35\x34]\x07",
        "bit_ix": rb"\xdd\xcb\x07.",
        "read_ix": rb"\xdd[\x7e\x46\x4e\x56\x5e\x66\x6e]\x07",
        "write_iy": rb"\xfd[\x77\x70\x71\x72\x73\x74\x75]\x07|\xfd\x36\x07.",
        "absolute_d507": rb"[\x22\x32]\x07\xd5|\x3a\x07\xd5|\x21\x07\xd5|\x11\x07\xd5",
    }
    found = {}
    for kind, p in pats.items():
        rows = []
        for m in re.finditer(p, rom, re.S):
            b, c = _loc(m.start())
            role = next((r for (bk, a, z, r) in SITE_ROLES if bk == b and a <= c < z), None)
            rows.append({"rom_offset": h(m.start(), 5), "bank": b, "cpu": h(c), "bytes": rom[m.start():m.start() + 4].hex(),
                         "role": role or ("other object / other bank (not reachable with IX = player)" if kind != "absolute_d507" else "")})
        found[kind] = rows
    player_roles = [r for k, rows in found.items() for r in rows if r["role"] and not r["role"].startswith("other")]
    return {"evidence": "BYTE-VERIFIED ASSEMBLY (byte scan of the whole ROM + manual classification)", "sites": found,
            "player_relevant_sites": len(player_roles),
            "absolute_and_iy_writes_to_d507": len(found["absolute_d507"]) + len(found["write_iy"]),
            "conclusion": "the only writers of the player's +$07 are the engine load ($6549), the engine decrement ($6510) and the selector routines called by FF 05; "
                          "nothing else (no IY form, no absolute $D507 access, no block copy) writes it"}


# --------------------------------------------------------------------------- #
# 2. the pure shadow model
# --------------------------------------------------------------------------- #
class Model:
    """Shadow of the player animation engine for `+$07`, `+$01`, script pointer and loop counter.

    Per player update call `step(req, hi, floor, side, d448)` BEFORE the state callback and the ring probe; the result is the
    value of +$07 seen by the probe of that update.
    """

    def __init__(self, rom: bytes, zone: int = 0, act: int = 0):
        self.rom = rom
        self.zone, self.act = zone, act
        self.cur = 0
        self.ptr = 0
        self.t = 0
        self.loop = 0
        self.last = {}

    def script(self, state: int) -> int:
        return u16(self.rom, rom_of(BANK, STATE_TABLE + 2 * state))

    # -- selectors (FF 05 routines): value written to +$07
    def selector(self, addr: int, hi: int, floor: bool, side: bool) -> int:
        a = abs(hi if hi < 128 else hi - 256)            # LD A,($D517); AND A; JP P; NEG  (128 stays 128)
        if addr == 0x8EE1:
            return 2 if side else self.rom[rom_of(BANK, 0x8F2C + a)]      # reads past the 16-byte table for |hi| >= 16, as the original does
        if addr == 0x8F45:
            return 4
        if addr == 0x8F76:
            return self.rom[rom_of(BANK, 0x8FE0 + a)] if floor else 3
        if addr == 0x9138:
            return 3
        if addr == 0x900B:
            return 6
        raise KeyError(f"selector ${addr:04X} is not modelled")

    def branch_carry(self, addr: int, d448: int) -> bool:
        if addr == 0x818F:
            return bool(d448 & 1)
        if addr == 0x80D9:
            return True                 # carry unless zone 4 act 0 at one location (not a THZ case)
        raise KeyError(f"FF 08 routine ${addr:04X} is not modelled")

    def _next_record(self, req_box, hi, floor, side, d448):
        rom = self.rom
        for _ in range(4000):
            o = rom_of(BANK, self.ptr)
            b = rom[o]
            if b != 0xFF:
                self.t = b
                self.last = {"kind": "record", "cpu": self.ptr, "duration": b, "frame": rom[o + 1], "callback": u16(rom, o + 2)}
                self.ptr += 4
                return
            c = rom[o + 1]
            if c == 0x00:                                   # restart (or switch if a request is pending)
                self.cur = req_box[0] if self.cur != req_box[0] else self.cur
                self.ptr = self.script(self.cur)
                continue
            if c == 0x01:                                   # call routine (no effect on +$07 for the modelled states)
                if u16(rom, o + 2) == 0x038F:               # $3657 player init: INC (IX+2) (state 0 -> requests the next state)
                    req_box[0] = (req_box[0] + 1) & 0xFF
                self.ptr += 4
                continue
            if c == 0x03:                                   # request state
                req_box[0] = rom[o + 2]
                self.ptr += 3
                continue
            if c == 0x05:                                   # call selector, set callback; selector writes +$07
                addr = u16(rom, o + 2)
                self.t = self.selector(addr, hi, floor, side)
                self.last = {"kind": "selector", "cpu": self.ptr, "selector": addr, "duration": self.t, "callback": u16(rom, o + 4)}
                self.ptr += 6
                return
            if c == 0x07:
                self.ptr = u16(rom, o + 2)
                continue
            if c == 0x08:                                   # conditional jump on carry
                if self.branch_carry(u16(rom, o + 2), d448):
                    self.ptr = u16(rom, o + 4)
                else:
                    self.ptr += 6
                continue
            if c == 0x0E:
                self.loop = rom[o + 2]
                self.ptr += 3
                continue
            if c == 0x0F:
                self.loop = (self.loop - 1) & 0xFF
                self.ptr = self.ptr + 4 if self.loop == 0 else u16(rom, o + 2)
                continue
            if c in (0x02, 0x04, 0x06, 0x09, 0x0A, 0x0B, 0x0C):    # no effect on the counter or the pointer logic
                self.ptr += 2 + CMD_ARGS[c]
                continue
            raise KeyError(f"command FF {c:02X} at ${self.ptr:04X} is not modelled")
        raise RuntimeError("script did not reach a record")

    def step_state_run(self, state: int, hi, floor, side, d448, n):
        self.cur, self.ptr = state, 0
        return [self.step(state, hi, floor, side, d448) for _ in range(n)]

    def loaded_durations(self, state: int, hi, floor, side, d448, reloads: int) -> list:
        """Durations loaded by successive reloads after entering `state` (record durations / selector results)."""
        self.cur, self.ptr = state, 0
        out: list = []
        for _ in range(100000):
            prev = self.t
            before_ptr = self.ptr
            t = self.step(state, hi, floor, side, d448)
            if before_ptr == 0 or t != ((prev - 1) & 255) or self.last.get("duration") == t and prev == 1:
                out.append(t)
                if len(out) >= reloads:
                    break
        return out

    def step(self, req: int, hi: int = 0, floor: bool = False, side: bool = False, d448: int = 0, locked: bool = False) -> int:
        """One engine call. Returns +$07 afterwards. `req` is the requested state (+$02) at the start of the update."""
        req_box = [req]
        if self.ptr == 0:                    # script pointer zero: load the CURRENT state's script ($651D), ignoring +$02 this update
            self.ptr = self.script(self.cur)
            self._next_record(req_box, hi, floor, side, d448)
        elif not locked and req != self.cur:
            self.cur = req
            self.ptr = self.script(self.cur)
            self._next_record(req_box, hi, floor, side, d448)
        else:
            self.t = (self.t - 1) & 0xFF
            if self.t == 0:
                self._next_record(req_box, hi, floor, side, d448)
        self.req_after = req_box[0]         # +$02 as left by FF 03 commands
        return self.t


# --------------------------------------------------------------------------- #
# 3. controlled differential fixture against the original engine
# --------------------------------------------------------------------------- #
class Lab:
    def __init__(self, rom: bytes):
        from oracle import Oracle
        self.rom = rom
        self.o = Oracle(rom)
        self.m = self.o.mem
        self.snap = bytes(self.m[0xC000:0xE000])

    def reset(self, cur=1):
        m = self.m
        m[0xC000:0xE000] = self.snap
        m[0xD500] = 1
        for a in range(0xD501, 0xD540):
            m[a] = 0
        m[0xD501] = cur

    def prime(self, mod=None):
        """First engine call (script pointer zero): loads state 1's script; later calls then behave as in steady play."""
        self.engine(1, 0, True, False, 0)
        if mod is not None:
            mod.cur = 1
            mod.step(1, 0, True, False, 0)

    def engine(self, req, hi, floor, side, d448, surf=0, frame_counter=0):
        o, m = self.o, self.m
        m[0xD502] = req
        o.word(0xD516, (hi & 0xFF) << 8)
        m[0xD522] = 2 if floor else 0
        m[0xD523] = 0x0C if side else 0
        m[0xD448] = d448
        m[0xD36C] = surf
        m[0xD52F] = frame_counter
        o.bank(2, BANK)
        m[0xD12B] = BANK
        o.cpu.ix = 0xD500
        o.call(0x64FA)
        return m[0xD507]

    def probe_depth(self, x=1000, y=500):
        """Y offset from the anchor actually probed by the original $753E for the current +$07."""
        o, m = self.o, self.m
        o.bank(2, BANK)
        o.word(0xD511, x)
        o.word(0xD514, y)
        o.cpu.ix = 0xD500
        o.call(0x753E)
        return o.word(0xD35A) - y


# Player states observed (emulated, state forced) to run the terrain-ring probe: this study's dynamic_eligibility, which also corrects the
# static reachability list of terrain-ring-collection.json (it listed $21 and $34, which never probe when held).
ELIGIBLE_STATES = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x14, 0x15, 0x17, 0x19, 0x1A,
                   0x1B, 0x1C, 0x1D, 0x1E]


def eligible_states(rom: bytes) -> list[int]:
    return list(ELIGIBLE_STATES)


def differential_fixture(rom: bytes, episodes: int = 400, length: int = 160) -> dict:
    """Random state/input sequences: the shadow model must match the original engine on +$07, +$01, the script pointer and the loop counter."""
    lab = Lab(rom)
    m = lab.m
    states = [s for s in eligible_states(rom) if s in MODELLED_STATES]
    rng = random.Random(0x0705)
    cases = bad = 0
    first_bad = None
    parity_set = 0
    for ep in range(episodes):
        lab.reset()
        mod = Model(rom)
        mod.cur = 1
        req = rng.choice(states)
        for k in range(length):
            if rng.random() < 0.12:
                req = rng.choice(states)
            hi = rng.choice([0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 15, 249, 252, 255])
            floor = rng.random() < 0.6
            side = rng.random() < 0.15
            d448 = rng.randrange(2)
            surf = rng.choice([0, 0x19, 1])
            # the original FF 03 / callbacks may change +$02 inside the engine; mirror it
            got = lab.engine(req, hi, floor, side, d448, surf, rng.randrange(40))
            want = mod.step(req, hi, floor, side, d448)
            req = m[0xD502]
            cases += 1
            parity_set += got & 1
            ok = (got == want and m[0xD501] == mod.cur and (m[0xD50E] | m[0xD50F] << 8) == mod.ptr and m[0xD533] == mod.loop and m[0xD502] == mod.req_after)
            if not ok:
                bad += 1
                first_bad = first_bad or {"episode": ep, "update": k, "req": req, "hi": hi, "floor": floor, "side": side, "d448": d448,
                                          "original": [got, m[0xD501], h(m[0xD50E] | m[0xD50F] << 8), m[0xD533]], "model": [want, mod.cur, h(mod.ptr), mod.loop]}
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "$64FA on the player slot, bank $0C re-paged before every call", "episodes": episodes, "updates_per_episode": length,
            "cases": cases, "mismatches": bad, "first_mismatch": first_bad, "parity_set_fraction": round(parity_set / cases, 3),
            "states_used": [h(s, 2) for s in states]}


# the eligible states whose scripts use only commands the model implements (all of them, verified by the fixture)
MODELLED_STATES: set[int] = set()


def _init_modelled(rom: bytes) -> None:
    MODELLED_STATES.clear()
    for s in range(0, LAST_REAL_STATE + 1):
        mod = Model(rom)
        try:
            for hi in (0, 3, 9):
                mod.cur, mod.ptr = s, 0
                mod.step(s, hi, True, False, 0)
                for _ in range(300):
                    mod.step(s, hi, True, False, 0)
            MODELLED_STATES.add(s)
        except (KeyError, RuntimeError):
            pass


# --------------------------------------------------------------------------- #
# 4. schedules, selectors, transitions
# --------------------------------------------------------------------------- #
def _fragment(rom: bytes, ptr: int) -> list:
    """Records/commands at an FF 08 branch target (listed until the first FF command)."""
    ops = []
    for _ in range(12):
        o = rom_of(BANK, ptr)
        if rom[o] != 0xFF:
            ops.append({"at": h(ptr), "record": rom[o], "frame": rom[o + 1], "callback": h(u16(rom, o + 2))})
            ptr += 4
            continue
        c = rom[o + 1]
        ops.append({"at": h(ptr), "cmd": f"FF {c:02X}", "args": rom[o + 2:o + 2 + CMD_ARGS.get(c, 0)].hex()})
        break
    return ops


def script_program(rom: bytes, state: int) -> list:
    """Linear listing of a state script (records and commands) until the first terminating restart/request."""
    ptr = u16(rom, rom_of(BANK, STATE_TABLE + 2 * state))
    seen = set()
    ops = []
    while ptr not in seen and len(ops) < 80:
        seen.add(ptr)
        o = rom_of(BANK, ptr)
        if rom[o] != 0xFF:
            ops.append({"at": h(ptr), "record": rom[o], "frame": rom[o + 1], "callback": h(u16(rom, o + 2))})
            ptr += 4
            continue
        c = rom[o + 1]
        n = 2 + CMD_ARGS.get(c, 0)
        row = {"at": h(ptr), "cmd": f"FF {c:02X}", "args": rom[o + 2:o + n].hex()}
        if c == 0x05:
            row["selector"] = h(u16(rom, o + 2))
            row["callback"] = h(u16(rom, o + 4))
        if c in (0x07, 0x0F):
            row["target"] = h(u16(rom, o + 2))
        if c == 0x08:
            row["condition_routine"], row["target_if_carry"] = h(u16(rom, o + 2)), h(u16(rom, o + 4))
            row["fragment_at_target"] = _fragment(rom, u16(rom, o + 4))
        ops.append(row)
        if c == 0x00:
            break
        if c == 0x07:
            ptr = u16(rom, o + 2)
            continue
        ptr += n
    return ops


def _rle(seq: list) -> list:
    out: list = []
    for v in seq:
        if out and out[-1][0] == v:
            out[-1][1] += 1
        else:
            out.append([v, 1])
    return out


def state_schedules(rom: bytes, states: list[int]) -> dict:
    out = {}
    for s in states:
        if s not in MODELLED_STATES:
            out[h(s, 2)] = {"modelled": False}
            continue
        prog = script_program(rom, s)
        selectors = sorted({r["selector"] for r in prog if "selector" in r})
        variants = {}
        for label, hi, floor, side, d448 in (("hi0_floor", 0, True, False, 0), ("hi4_floor", 4, True, False, 0), ("hi4_air", 4, False, False, 0),
                                              ("hi4_floor_side", 4, True, True, 0), ("hi4_floor_d448", 4, True, False, 1)):
            mod = Model(rom)
            seq = [mod.step(s, hi, floor, side, d448) for _ in range(40)]
            variants[label] = seq
        constant = len({tuple(v) for v in variants.values()}) == 1
        dep, pdep = {}, {}
        alt_all = True
        for name, vals in (("x_speed_hi", [(hi, True, False, 0) for hi in range(0, 10)]), ("floor", [(4, f, False, 0) for f in (False, True)]),
                           ("side_contact", [(4, True, sd, 0) for sd in (False, True)]), ("d448_bit0", [(4, True, False, d) for d in (0, 1)])):
            seqs = set()
            pseqs = set()
            for hi, fl, sd, d4 in vals:
                mod = Model(rom)
                run = mod.step_state_run(s, hi, fl, sd, d4, 160)
                seqs.add(tuple(run))
                pseqs.add(tuple(v & 1 for v in run))
            dep[name] = len(seqs) > 1
            pdep[name] = len(pseqs) > 1
            alt_all = alt_all and all(all(v == i % 2 for i, v in enumerate(ps)) for ps in pseqs)
        loads = Model(rom).loaded_durations(s, 4, True, False, 0, 60)
        out[h(s, 2)] = {"modelled": True, "selectors": selectors, "program": prog, "depends_on_inputs": any(dep.values()), "input_dependence": dep,
                        "parity_depends_on_inputs": any(pdep.values()), "parity_input_dependence": pdep,
                        "parity_is_pure_alternation_from_entry_for_all_inputs": alt_all,
                        "loaded_durations_first_60_reloads_rle": _rle(loads),
                        "first_40_counter_values_by_input_set": variants if not constant else {"all": variants["hi0_floor"]}}
    return out


def selector_tables(rom: bytes) -> dict:
    walk = [rom[rom_of(BANK, 0x8F2C) + i] for i in range(16)]
    floor = [rom[rom_of(BANK, 0x8FE0) + i] for i in range(16)]
    return {"evidence": "DECODED DATA + CONTROLLED ROUTINE RESULT",
            "selector_8ee1_walk_state_05": {"rule": "if (+$23 & $0C): +$07 := 2 else +$07 := table[|X speed high byte|]", "table_cpu": "0x8F2C", "table": walk,
                                            "index": "|(X speed high byte $D517)| as an 8-bit absolute value (negative: NEG)",
                                            "thresholds": "duration 10 at |hi|=0, 8 at 1, 6 at 2, 4 at >=3"},
            "selector_8f45_run_state_06": {"rule": "+$07 := 4 always", "table": None},
            "selector_8f76_states_09_0A_10_1B": {"rule": "if (+$22 bit 1): +$07 := table[|X speed high byte|] else +$07 := 3", "table_cpu": "0x8FE0", "table": floor,
                                                  "thresholds": "10, 8, 6, 5, 4, 3, then 2 for |hi| >= 6 (floor); 3 in the air"},
            "selector_9138_state_17": {"rule": "+$07 := 3 always"},
            "selector_900b_state_1d": {"rule": "+$07 := 6 always"},
            "frame_only_inputs": "+$24 bit 0 with $D36C type $19 and $D52F choose the FRAME (not +$07)"}


def update_order() -> dict:
    return {"evidence": "BYTE-VERIFIED ASSEMBLY + EMULATED ORIGINAL FRAME",
            "per_player_update": [
                "$361D: IX = $D500 (type 0 -> return)",
                "$64FA animation engine: (a) script pointer zero -> load; (b) +$02 != +$01 and +$03 bit 3 clear -> +$01 := +$02, reload script; "
                "(c) otherwise DEC +$07; zero -> next record. Record: +$07 := duration. FF 05: selector writes +$07. FF 00 / FF 03 / FF 07 / FF 08 / FF 0F re-enter the loop in the SAME update.",
                "$5E91: state callback (JP (+$0C)): may request a state by writing +$02 (applies at the NEXT update's engine call)",
                "  callback -> $3FEF: clamp $4141 -> X integrate $402A -> Y integrate $4097 -> $690B (floor, sides, ceiling, terrain probe $753E, merge $64CB)",
                "$4A74"],
            "consequences": [
                "the probe of update n sees +$07 as set by the engine of update n (after any state switch of that same update)",
                "a state requested during update n is switched in at the start of update n+1: that update's probe already sees the new state's first record/selector value",
                "selector inputs (|X speed high byte| $D517, floor bit +$22.1, side bits +$23 & $0C) are read at the START of the update, i.e. the values left by the previous update's movement and merge"]}


# --------------------------------------------------------------------------- #
# 5. transitions with probe depth (controlled, original engine + original $753E)
# --------------------------------------------------------------------------- #
SCENARIOS = {
    "stand_idle_then_impatient": [(1, 0, True, False)] * 190,
    "stand_to_walk": [(1, 0, True, False)] * 4 + [(5, 1, True, False)] * 14,
    "walk_speed_ramp": [(5, hi, True, False) for hi in (0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5, 6) for _ in range(3)],
    "walk_to_run": [(5, 3, True, False)] * 6 + [(6, 4, True, False)] * 14,
    "run_to_jump_to_fall_to_land": [(6, 5, True, False)] * 6 + [(0x0A, 5, False, False)] * 12 + [(0x0E, 5, False, False)] * 12 + [(6, 5, True, False)] * 8,
    "run_to_roll_to_stand": [(6, 6, True, False)] * 5 + [(9, 6, True, False)] * 14 + [(9, 2, True, False)] * 10 + [(1, 0, True, False)] * 6,
    "roll_in_air_then_land": [(9, 4, False, False)] * 9 + [(9, 4, True, False)] * 14,
    "spring_ascent_to_fall": [(0x0B, 0, False, False)] * 30 + [(0x0E, 0, False, False)] * 12,
    "spring_ascent_d448": [(0x0B, 0, False, False, 1)] * 14,
    "walk_into_wall": [(5, 3, True, False)] * 5 + [(5, 3, True, True)] * 6 + [(5, 3, True, False)] * 4,
    "state_change_every_update": [(s, 2, True, False) for s in (1, 5, 6, 9, 5, 6, 1, 5)],
}


def transition_fixtures(rom: bytes) -> dict:
    lab = Lab(rom)
    rows_out = {}
    cases = bad = 0
    for name, seq in SCENARIOS.items():
        lab.reset()
        mod = Model(rom)
        lab.prime(mod)
        rows = []
        prev = None
        for k, item in enumerate(seq):
            req, hi, floor, side = item[:4]
            d448 = item[4] if len(item) > 4 else 0
            before = lab.m[0xD507]
            got = lab.engine(req, hi, floor, side, d448)
            want = mod.step(req, hi, floor, side, d448)
            depth = lab.probe_depth()
            cases += 1
            if got != want or depth != RING_DY[got & 1] + ANCHOR_BIAS:
                bad += 1
            rec = lab.m[0xD50E] | lab.m[0xD50F] << 8
            rows.append({"update": k, "requested": h(req, 2), "state_after": h(lab.m[0xD501], 2), "x_speed_hi": hi, "floor": floor, "side_contact": side,
                         "counter_before": before, "counter_after": got, "bit0": got & 1, "probe_y_from_anchor": depth,
                         "record_or_selector": mod.last.get("selector") and h(mod.last["selector"]) or (mod.last.get("cpu") and h(mod.last["cpu"])),
                         "script_ptr_after": h(rec), "reloaded": mod.last.get("kind") if got != ((before - 1) & 255) else None})
            prev = got
        rows_out[name] = rows
    return {"evidence": "CONTROLLED ROUTINE RESULT", "cases": cases, "mismatches": bad,
            "probe_depth_rule": "probe_y_from_anchor = -8 when bit0 = 0, +2 when bit0 = 1 (original $753E run after the engine in every row)", "scenarios": rows_out}


def selector_sweep(rom: bytes) -> dict:
    """Every |X speed| and contact combination for each selector: original engine versus the model."""
    lab = Lab(rom)
    cases = bad = 0
    rows = []
    for state, name in ((5, "walk"), (6, "run"), (9, "roll"), (0x0A, "jump"), (0x10, "state_10"), (0x1B, "ramp_launch"), (0x17, "state_17"), (0x1D, "state_1d")):
        for hi in list(range(0, 16)) + [248, 250, 255]:
            for floor in (False, True):
                for side in (False, True):
                    lab.reset()
                    mod = Model(rom)
                    lab.prime(mod)
                    got = lab.engine(state, hi, floor, side, 0)
                    want = mod.step(state, hi, floor, side, 0)
                    cases += 1
                    bad += got != want
                    if hi in (0, 1, 2, 3, 5, 6, 8, 15, 255) and not side:
                        rows.append({"state": h(state, 2), "label": name, "x_speed_hi": hi, "floor": floor, "first_counter": got, "bit0": got & 1})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "cases": cases, "mismatches": bad, "samples": rows}


def direct_write_fixtures(rom: bytes) -> dict:
    lab = Lab(rom)
    out = []
    # reload timing: selector re-run only when the counter expires (a speed change does NOT replace a running counter)
    lab.reset()
    lab.prime()
    seq = []
    for k in range(24):
        hi = 0 if k < 4 else 6
        seq.append({"update": k, "x_speed_hi": hi, "counter": lab.engine(5, hi, True, False, 0)})
    out.append({"case": "walk speed 0 -> 6 at update 4", "counter_sequence": [r["counter"] for r in seq],
                "note": "the 10 loaded at speed 0 keeps counting down; the new duration (4) is loaded only at the next reload"})
    lab.reset()
    lab.prime()
    seq = []
    for k in range(14):
        side = 3 <= k < 7
        seq.append(lab.engine(5, 3, True, side, 0))
    out.append({"case": "side contact for updates 3..6 while walking", "counter_sequence": seq,
                "note": "side contact only selects duration 2 when the selector runs (a reload); it never rewrites a running counter"})
    lab.reset()
    lab.prime()
    seq = [lab.engine(0x0A, 5, k < 5, False, 0) for k in range(14)]
    out.append({"case": "jump: floor bit set for the first 5 updates only", "counter_sequence": seq,
                "note": "floor bit selects table $8FE0 (speed 5 -> 3) versus the air constant 3 at each reload"})
    lab.reset()
    lab.prime()
    lab.m[0xD503] = 0x08                        # +$03 bit 3 set: state requests are ignored by the engine
    seq = [lab.engine(1 if k < 3 else 5, 0, True, False, 0) for k in range(8)]
    out.append({"case": "+$03 bit 3 set (never set by any recovered ROM code)", "counter_sequence": seq, "state_after": h(lab.m[0xD501], 2)})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "rows": out}


# --------------------------------------------------------------------------- #
# 6. emulated whole-game verification and dynamic eligibility
# --------------------------------------------------------------------------- #
def emulated_play(rom: bytes) -> dict:
    """Seeded play in the real game: capture the engine's inputs and the value the probe sees, replay them through the shadow model."""
    o18 = _load("object_18")
    from sms_frame_harness import BTN_RIGHT, BTN_LEFT, BTN_DOWN, BTN_1
    s = o18._boot(rom, 0, lambda m: None)
    m = s.mem
    pre: dict = {}
    updates = []
    probes = []

    def on_engine(_):
        if s.cpu.ix != 0xD500:
            return
        pre.update(req=m[0xD502], cur=m[0xD501], hi=m[0xD517], floor=bool(m[0xD522] & 2), side=bool(m[0xD523] & 0x0C), d448=m[0xD448], lock=bool(m[0xD503] & 8),
                   t=m[0xD507])

    def on_callback(_):
        if s.cpu.ix != 0xD500 or not pre:
            return
        updates.append(dict(pre, t_after=m[0xD507], cur_after=m[0xD501]))
        pre.clear()

    def on_probe(_):
        if s.cpu.ix == 0xD500:
            probes.append((len(updates), m[0xD507], m[0xD501]))

    s.add_pc_hook(0x64FA, on_engine)
    s.add_pc_hook(0x5E91, on_callback)
    s.add_pc_hook(0x753E, on_probe)
    rng = random.Random(5)
    pad = 0
    for f in range(7000):
        if f % 45 == 0:
            r = rng.random()
            pad = BTN_RIGHT if r < .5 else (BTN_RIGHT | BTN_DOWN if r < .65 else (BTN_LEFT if r < .75 else (BTN_RIGHT | BTN_1 if r < .9 else BTN_DOWN)))
        s.pad = pad | (BTN_1 if f % 70 < 8 and pad & BTN_RIGHT else 0)
        s.run_frame()
    # replay
    mod = Model(rom)
    mod.cur = updates[0]["cur"]
    cases = bad = 0
    first_bad = None
    by_state: dict = defaultdict(lambda: [0, 0])
    unmodelled = 0
    for i, u in enumerate(updates):
        if i == 0:
            mod.ptr = 0
            mod.cur = u["cur"]
            mod.t = u["t"]
        try:
            hi = u["hi"]
            want = mod.step(u["req"], hi, u["floor"], u["side"], u["d448"], u["lock"])
        except (KeyError, RuntimeError):
            unmodelled += 1
            break
        if i == 0:
            continue                    # the first update only seeds the model from the real pointer-less start
        cases += 1
        by_state[u["cur_after"]][0] += 1
        if want != u["t_after"] or mod.cur != u["cur_after"]:
            bad += 1
            by_state[u["cur_after"]][1] += 1
            first_bad = first_bad or {"update": i, "inputs": {k: u[k] for k in ("req", "cur", "hi", "floor", "side", "d448")}, "original": [u["t_after"], u["cur_after"]], "model": [want, mod.cur]}
            mod.t = u["t_after"]        # re-seed so one divergence does not hide others
            mod.cur = u["cur_after"]
    probe_cases = probe_bad = 0
    for idx, t_seen, st in probes:
        probe_cases += 1
        if idx - 1 < len(updates) and updates[idx - 1]["t_after"] != t_seen:
            probe_bad += 1
    return {"evidence": "EMULATED ORIGINAL FRAME",
            "method": "THZ1 booted in tools/sms_frame_harness.py, 7000 frames of seeded pseudo-random pad input; PC hooks at the engine entry $64FA (inputs) and at "
                      "the callback entry $5E91 (+$07 after the engine); the shadow model is driven with the captured inputs",
            "player_updates": len(updates), "model_cases": cases, "model_mismatches": bad, "first_mismatch": first_bad, "unmodelled_stop": unmodelled,
            "probe_calls": probe_cases, "probe_value_equals_engine_value": probe_cases - probe_bad,
            "updates_by_state_after_engine_total_mismatch": {h(k, 2): v for k, v in sorted(by_state.items())}}


def dynamic_eligibility(rom: bytes) -> dict:
    """Force every real state in turn and record whether the probe runs while that state is current."""
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
    return {"evidence": "EMULATED ORIGINAL FRAME", "rows": rows,
            "observed_probing": [r["state"] for r in rows if r["probe_calls_in_state"]],
            "observed_not_probing": [r["state"] for r in rows if not r["probe_calls_in_state"] and r["frames_in_state"]],
            "never_held": [r["state"] for r in rows if not r["frames_in_state"]]}


# --------------------------------------------------------------------------- #
# 6b. state $0B and $D448 (focused audit)
# --------------------------------------------------------------------------- #
# (rom offset of the store opcode, expected bytes ending with the store, meaning, value written)
D448_WRITERS = [
    (0x6A87, "3eff3248d4", "terrain upright spring (surface type 9, handler $6A75): Y speed $F880 -> $480C -> state $0B", 0xFF),
    (0x6AC8, "af3248d4", "terrain diagonal spring (surface type $14, handler $6A90): -> $482D -> state $1C (not $0B)", 0x00),
    (0x332CC, "3eff3248d4", "type $21 top contact (bank $0C $B2CC): Y speed $F940 -> $035F -> $480C -> state $0B", 0xFF),
    (0x782F8, "783248d4", "type $26 spring contact state 7 (bank $1E $82F8): parameter 0 -> $FF + $F8A0, nonzero -> 0 + $FB00 -> $035F -> $480C -> state $0B", None),
    (0x78420, "783248d4", "type $26 span-spring state 9 (bank $1E $8420): same parameter rule as $82F8", None),
    (0x799CA, "af3248d4", "type $50 attack contact (bank $1E $99CA): Y speed $FC00 -> $035F -> $480C -> state $0B", 0x00),
]


def d448_audit(rom: bytes) -> dict:
    occ = []
    for m in re.finditer(rb"\x48\xd4", rom):
        o = m.start() - 1
        b, c = _loc(o)
        occ.append({"rom_offset": h(o, 5), "bank": b, "cpu": h(c), "bytes": rom[o - 1:o + 5].hex()})
    writers = []
    for off, pre, meaning, val in D448_WRITERS:
        n = len(pre) // 2
        seen = rom[off + 3 - n:off + 3].hex()
        writers.append({"rom_offset": h(off, 5), "bank": _loc(off)[0], "cpu": h(_loc(off)[1]), "bytes": seen, "bytes_match": seen == pre,
                        "meaning": meaning, "value": None if val is None else h(val, 2)})
    callers_480c = [h(m.start(), 5) for m in re.finditer(rb"\xcd\x0c\x48|\xc3\x0c\x48", rom)]
    callers_035f = [h(m.start(), 5) for m in re.finditer(rb"\xcd\x5f\x03|\xc3\x5f\x03", rom)]
    prog = script_program(rom, 0x0B)
    durations = [r["record"] for r in prog if "record" in r]
    for r in prog:
        durations += [x["record"] for x in r.get("fragment_at_target", []) if "record" in x]
    requests_0b = [h(m.start(), 5) for m in re.finditer(rb"\xdd\x36\x02\x0b", rom) if _loc(m.start())[0] in (0, 1)]
    layout = {}
    for act in ("thz1", "thz2", "thz3"):
        d = json.loads((ROOT / "data" / "rom-cache" / "levels" / act / "objects.json").read_text(encoding="utf-8"))
        recs = [r for r in d["records"] if r["type_id"].lower() == "0x26"]
        layout[act] = [{"world": [r["world_x"], r["world_y"]], "parameter": r["parameter"],
                        "d448_after_launch": "0xFF (bit 0 set)" if int(r["parameter"], 16) == 0 else "0x00 (bit 0 clear)",
                        "launch": "strong $F8A0" if int(r["parameter"], 16) == 0 else "weak $FB00"} for r in recs]
    return {"evidence": "BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT",
            "reader": {"cpu": "0x818F (bank $0C)", "bytes": rom[rom_of(BANK, 0x818F):rom_of(BANK, 0x818F) + 5].hex(),
                       "meaning": "LD A,($D448); RRCA; RET: carry = bit 0",
                       "used_by": "FF 08 at $814A (first command of the state $0B script): carry -> script pointer := $8189"},
            "all_occurrences_of_the_address_bytes": occ, "writers": writers, "stores_total": len(writers),
            "other_accesses": "none: no IX/IY+$48 form, no HL/DE/BC load of $D448, no block copy; zeroed only by the boot/reset RAM clears ($0029, $0462)",
            "not_cleared_at_level_load": True,
            "callers_of_480c_upright_launch": callers_480c, "callers_of_035f_launch_vector": callers_035f,
            "player_requests_of_state_0b_in_fixed_banks": requests_0b,
            "every_upright_launch_writes_d448_first": True,
            "state_0b_durations_all_even": all(d % 2 == 0 for d in durations), "state_0b_durations": sorted(set(durations)),
            "thz_springs_by_parameter": layout,
            "meaning": "bit 0 of $D448 records the kind of the last upright launch: $FF for terrain upright springs, type $21 stomps and parameter-0 type $26 springs; "
                       "0 for weak (parameter != 0) type $26 springs and the boss bounce. It persists until the next launch writer, including across acts."}


def state_0b_fixture(rom: bytes) -> dict:
    """State $0B entered with $D448 bit 0 = 0 and = 1 against the original engine, long enough to cover the whole normal schedule."""
    lab = Lab(rom)
    n_updates = 200
    seqs = {}
    for d448 in (0, 1):
        lab.reset()
        mod = Model(rom)
        lab.prime(mod)
        orig, model = [], []
        for _ in range(n_updates):
            orig.append(lab.engine(0x0B, 0, False, False, d448))
            model.append(mod.step(0x0B, 0, False, False, d448))
        seqs[d448] = {"original": orig, "model": model}
    parity = {k: [v & 1 for v in q["original"]] for k, q in seqs.items()}
    first_value_diff = next((i for i in range(n_updates) if seqs[0]["original"][i] != seqs[1]["original"][i]), None)
    rng = random.Random(0x0B448)
    toggles = bad = 0
    for ep in range(300):
        lab.reset()
        lab.prime()
        got = []
        for k in range(n_updates):
            v = rng.choice([0x00, 0x01, 0xFF, 0xFE, 0x55])
            toggles += 1
            got.append(lab.engine(0x0B, 0, False, False, v) & 1)
        bad += got != parity[0]
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "$64FA, state $0B, bank $0C re-paged each call", "updates_per_run": n_updates,
            "counter_sequence_d448_clear_first_90": seqs[0]["original"][:90], "counter_sequence_d448_set_first_90": seqs[1]["original"][:90],
            "model_equals_original": seqs[0]["original"] == seqs[0]["model"] and seqs[1]["original"] == seqs[1]["model"],
            "first_update_where_counter_values_differ": first_value_diff,
            "parity_sequences_identical": parity[0] == parity[1], "parity_pattern_first_16": parity[0][:16],
            "random_toggle_episodes": 300, "random_toggle_updates": toggles, "random_toggle_parity_mismatches": bad,
            "d448_values_tried_in_toggle_test": ["0x00", "0x01", "0xFF", "0xFE", "0x55"],
            "reason": "every record of every path has an even duration (4, 6, 8), so the counter always runs d, d-1, ..., 1 with d even: bit 0 is 0,1,0,1,... "
                      "continuously across reloads; the D448 branch only changes WHICH even durations are loaded, never the parity sequence",
            "conclusion": "D448 bit 0 does not affect bit 0 of +$07 in state $0B (the only reader of $D448 is the state $0B script)"}


def emulated_springs(rom: bytes) -> dict:
    """Real launches in THZ1/THZ2: $D448 after the launch, length of state $0B and the engine's counter values versus the model for both $D448 values."""
    o18 = _load("object_18")
    rows = []
    cases = (("thz1", 0, 688, 864, 0x00), ("thz1", 0, 1912, 864, 0x01), ("thz1", 0, 1296, 608, 0x8A),
             ("thz2", 1, 864, 896, 0x00), ("thz2", 1, 1504, 896, 0x88), ("thz2", 1, 3472, 288, 0x01))
    for act, idx, sx, sy, param in cases:
        s = o18._boot(rom, idx, lambda m: None)
        m = s.mem
        for _ in range(60):
            s.pad = 0
            s.run_frame()
        trace = []

        def on_cb(_, trace=trace, m=m, s=s):
            if s.cpu.ix == 0xD500:
                trace.append((m[0xD501], m[0xD507], m[0xD448]))

        s.add_pc_hook(0x5E91, on_cb)
        x, y = sx, sy - 18
        for a in (0xD174, 0xD284):
            s.w16(a, max(x - 104, 0))
        for a in (0xD176, 0xD286):
            s.w16(a, y - 100)
        s.w16(0xD511, x)
        s.w16(0xD514, y)
        s.w16(0xD516, 0)
        s.w16(0xD518, 0)
        m[0xD448] = 0x55
        m[0xD440] = 0                  # initial-fill creation so the concealed spring exists
        trace.clear()
        for _ in range(260):
            s.pad = 0
            s.run_frame()
        idxs = [i for i, t in enumerate(trace) if t[0] == 0x0B]
        if not idxs:
            rows.append({"act": act, "spring": [sx, sy], "parameter": h(param, 2), "launched": False})
            continue
        run = []
        for t in trace[idxs[0]:]:
            if t[0] != 0x0B:
                break
            run.append(t)
        d448 = run[0][2]
        counters = [t[1] for t in run]
        exp = {dv: Model(rom).step_state_run(0x0B, 0, False, False, dv, len(run)) for dv in (0, 1)}
        rows.append({"act": act, "spring": [sx, sy], "parameter": h(param, 2), "launched": True, "d448_after_launch": h(d448, 2),
                     "updates_in_state_0b": len(run), "counters_first_20": counters[:20], "counters_last_8": counters[-8:],
                     "model_equal_for_observed_d448": counters == exp[d448 & 1],
                     "model_parity_equal_for_both_d448": [v & 1 for v in exp[0]] == [v & 1 for v in exp[1]],
                     "model_values_equal_for_both_d448": exp[0] == exp[1]})
    return {"evidence": "EMULATED ORIGINAL FRAME",
            "method": "THZ1/THZ2 booted in tools/sms_frame_harness.py; Sonic placed on each concealed spring with the placement scan forced to an initial fill ($D440 = 0); "
                      "$D448 preset to $55; PC hook at the callback entry $5E91 records +$01, +$07, $D448 per update",
            "rows": rows}


# --------------------------------------------------------------------------- #
# 7. build
# --------------------------------------------------------------------------- #
UNRESOLVED = [
    "+$03 bit 3 (engine ignores state requests while set) is never set by any recovered code; modelled behaviour is from the engine source only.",
    "FF 08 condition of state $04 depends on a zone-4 location (not a THZ case); the model assumes the carry path ($80C5 restart).",
    "$D448 beyond bit 0 (last-upright-launch marker, six stores of $FF/$00): only bit 0 is read, by the state $0B script; other bits were not investigated.",
    "FF 01 call targets ($038F, $8313, $82CC, $835E, ...) were verified only to leave +$07 unchanged in the differential runs.",
    "The probing set for states that cannot be held in the emulator (see dynamic_eligibility.never_held) rests on static reachability.",
    "Other-character selectors ($8CB4, $8D05) exist for a second player type; not part of THZ play and not modelled.",
]


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    _init_modelled(rom)
    elig = eligible_states(rom)
    out = {
        "format": 1, "rom_sha256": ROM_SHA256, "research_only": True, "poc_untouched": True, "machine_facing_label": "player_animation_counter",
        "evidence_classes": EVIDENCE, "routines": routine_table(rom), "plus07_sites": plus07_sites(rom), "update_order": update_order(),
        "selectors": selector_tables(rom), "eligible_states_static": [h(s, 2) for s in elig], "modelled_states": [h(s, 2) for s in sorted(MODELLED_STATES)],
        "schedules": state_schedules(rom, elig), "unresolved": UNRESOLVED, "static_only": static_only,
    }
    if not static_only:
        out["differential_fixture"] = differential_fixture(rom)
        out["selector_sweep"] = selector_sweep(rom)
        out["transition_fixtures"] = transition_fixtures(rom)
        out["direct_write_fixtures"] = direct_write_fixtures(rom)
        out["dynamic_eligibility"] = dynamic_eligibility(rom)
        out["emulated_play"] = emulated_play(rom)
        out["state_0b_fixture"] = state_0b_fixture(rom)
        out["emulated_springs"] = emulated_springs(rom)
    out["d448_audit"] = d448_audit(rom)
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

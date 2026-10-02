#!/usr/bin/env python3
"""THZ3 boss/support chain audit plus the `$1B` / `$28` closure items (research only, deterministic).

Part A closes the narrow platform/spike questions left by `docs/platform-spike-collision-audit.md`:
  A1 `$1B` cooldown versus contact / side wall / grounded push, A2 the exact grounded-attacker push,
  A3 `$28` / `$1B` lifecycle and phase, A4 the static-spike diagnostic rows (update-aligned replay).
Part B audits the THZ3 boss support chain (types `$50` `$12` `$34` `$0A` `$0F`), arena and camera rules,
boss contact grids, the phase model, the defeat -> act-clear chain, the required graphics and the manifest.

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT (original Z80 routines
on tools/oracle.py), EMULATED ORIGINAL FRAME (whole game in tools/sms_frame_harness.py, update-aligned), UNRESOLVED.

Usage:
  python tools/thz3_boss_support.py ROM.sms [--check] [--static-only] [--part a|b]
Output: data/rom-cache/thz3-boss-support.json and data/rom-cache/thz3/implementation-manifest.json (numeric labels only).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OUTPUT = ROOT / "data" / "rom-cache" / "thz3-boss-support.json"
MANIFEST = ROOT / "data" / "rom-cache" / "thz3" / "implementation-manifest.json"
UPDATE_BOUNDARY = 0x1336          # instruction after `CALL $062D` in the main loop `$1333`: start of every game update
SENTINEL = 0xAA


def _load(name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


psc = _load("platform_spike_collision")
o50 = _load("object_50")


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def s16(v: int) -> int:
    return (v + 32768) % 65536 - 32768


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rom_of(bank: int, cpu: int) -> int:
    return cpu if cpu < 0x8000 else bank * 0x4000 + cpu - 0x8000


def u16(rom: bytes, pos: int) -> int:
    return rom[pos] | (rom[pos + 1] << 8)


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM")


EVIDENCE = {
    "DECODED DATA": "ROM tables/records decoded by a parser",
    "BYTE-VERIFIED ASSEMBLY": "routine bytes compared literally and disassembled",
    "SOURCE-TRACED BEHAVIOR": "behavior read from the disassembly, not executed",
    "CONTROLLED ROUTINE RESULT": "original routine executed on a Z80 core with explicit RAM (tools/oracle.py)",
    "EMULATED ORIGINAL FRAME": "whole original game run in the approximate SMS harness, update-aligned (see harness_note)",
    "UNRESOLVED": "not established",
}

HARNESS_NOTE = (
    "The legacy `Emu.restore()` of tools/platform_spike_collision.py snapshots the machine at an arbitrary CPU position and does not restore "
    "`int_disabled`, `frame_tick` and `index_rp_kind`, so the FIRST update after a teleport can run a partially executed update and depends on IRQ "
    "phase (observed: vx -1004 versus -1024 for the same teleport). Every EMULATED fixture in this study therefore applies its writes from a PC hook at "
    "$1336 (the instruction after `CALL $062D` in the main loop $1333, i.e. exactly the start of a game update), so each update runs complete and "
    "repeated runs are bit-identical."
)


# --------------------------------------------------------------------------- #
# update-aligned emulation helper
# --------------------------------------------------------------------------- #
class Aligned:
    """Runs the whole game from `Emu` snapshots, applying every external write at an update boundary (PC hook at $1336)."""

    def __init__(self, emu):
        self.e, self.s, self.m = emu, emu.s, emu.s.mem
        self.driver = self.sample = None
        self.rows = None
        self.count = 0
        self.stop = None
        self.s.add_pc_hook(UPDATE_BOUNDARY, self._hook)

    def _hook(self, mach):
        if self.rows is None:
            return
        if self.driver:
            self.driver(self.count)
        self.rows.append(self.sample())
        self.count += 1

    def run(self, driver, sample, updates, pad=0, stop=None, restore=True):
        if restore:
            self.e.restore()
        self.rows, self.count, self.driver, self.sample = [], 0, driver, sample
        f = 0
        pending = None
        while self.count < updates + 1 and f < updates + 12:
            self.s.pad = pad(f) if callable(pad) else pad
            self.s.run_frame()
            f += 1
            if pending is not None:
                if self.count > pending:        # the boundary after the stop update has been sampled: its row is complete
                    break
            elif stop and self.rows and stop(self.rows):
                pending = self.count
        rows, self.rows = self.rows, None
        return rows


def player_row(e) -> dict:
    return psc.player_rec(e)


def ranges(values) -> list:
    return psc.ranges(values)


# =========================================================================== #
# PART A
# =========================================================================== #
def _spike_lab_state(rom: bytes, state: int, y: int):
    lab = psc.spike_lab(rom)
    psc.spike_set_state(lab, state, y)
    return lab


def _spike_probe(lab, dx, dy, *, f3=0, f22=2, vy=0x100, cooldown=0, ex=8, extra=None, merge=True) -> dict:
    """One callback of the real `$1B` state routine, then (optionally) the player's merge `$64CB`; all contact bytes preset to sentinels."""
    m, o = lab.m, lab.o
    ox, oy = lab.obj16(0x11), lab.obj16(0x14)
    lab.reset()
    m[psc.SLOT + 0x1F] = cooldown
    m[psc.SLOT + 0x20] = SENTINEL
    lab.player(ox + dx, oy + dy, vy=vy, f3=f3, f22=f22, ex=ex)
    m[0xD521] = 0
    m[psc.SLOT + 0x21] = 0
    if extra:
        extra(m, o)
    lab.callback()
    ran = m[psc.SLOT + 0x20] != SENTINEL
    row = {"helper_6328_ran": ran, "d521_high_nibble": m[0xD521] >> 4, "d520": m[0xD520], "damage_request_d3b0": m[0xD3B0] == 0xFF,
           "bounce_vy": s16(o.word(0xD518)) if o.word(0xD518) == 0xFC00 else None, "cooldown_after": m[psc.SLOT + 0x1F],
           "push_x": (o.word(0xD511) - ox) if (m[0xD502] == 1 and o.word(0xD511) != ox + dx) else None, "vx_after": s16(o.word(0xD516))}
    if merge:
        o.cpu.ix = 0xD500
        o.call(0x64CB)
        row["d523_after_merge"] = m[0xD523]
        row["wall_bits_d523_2_3"] = (m[0xD523] >> 2) & 3
    return row


def a1_cooldown_side_wall(rom: bytes) -> dict:
    out = {"evidence": "BYTE-VERIFIED ASSEMBLY (helper $32CFD, scheduler $5DD1, merge $64CB) + CONTROLLED ROUTINE RESULT (real $1B callbacks)"}
    lab = _spike_lab_state(rom, 2, 846)
    geoms = {"side_right": (18, 0), "side_left": (-18, 0), "below_vertical_dominated": (3, 10), "above_cone": (0, -12)}
    postures = {"walker_grounded": dict(f3=0, f22=2), "attacker_grounded": dict(f3=2, f22=2), "walker_airborne": dict(f3=1, f22=0),
                "attacker_airborne": dict(f3=3, f22=0)}
    table = []
    for cooldown in (0, 1, 2, 8, 15, 16):
        for gname, (dx, dy) in geoms.items():
            for pname, kw in postures.items():
                r = _spike_probe(lab, dx, dy, cooldown=cooldown, **kw)
                r.update(cooldown_before=cooldown, geometry=gname, posture=pname)
                table.append(r)
    out["probe_table"] = table
    out["probe_table_rows"] = len(table)
    active = [r for r in table if r["cooldown_before"] == 0]
    cool = [r for r in table if r["cooldown_before"] > 0]
    out["cooldown_zero_summary"] = {
        "helper_ran_all": all(r["helper_6328_ran"] for r in active),
        "contact_rows_with_wall": [[r["geometry"], r["posture"]] for r in active if r["wall_bits_d523_2_3"]],
        "contact_rows_with_push": [[r["geometry"], r["posture"], r["push_x"]] for r in active if r["push_x"] is not None],
        "damage_rows": [[r["geometry"], r["posture"]] for r in active if r["damage_request_d3b0"]],
    }
    out["cooldown_positive_summary"] = {
        "rows": len(cool),
        "helper_ran_any": any(r["helper_6328_ran"] for r in cool),
        "any_d521_contact": any(r["d521_high_nibble"] for r in cool),
        "any_wall": any(r["wall_bits_d523_2_3"] for r in cool),
        "any_push": any(r["push_x"] is not None for r in cool),
        "any_damage_or_bounce": any(r["damage_request_d3b0"] or r["bounce_vy"] is not None for r in cool),
        "cooldown_decrement_per_helper_call": sorted({(r["cooldown_before"], r["cooldown_after"]) for r in cool}),
    }

    # ---- update-by-update sequence after a damaging top contact ----------------
    seq = {}
    for pname, kw, geom in (("walker_grounded", dict(f3=0, f22=2), (18, 0)), ("attacker_grounded", dict(f3=2, f22=2), (18, 0))):
        lab.reset()
        m, o = lab.m, lab.o
        ox, oy = lab.obj16(0x11), lab.obj16(0x14)
        rows = []
        for upd in range(0, 21):
            dx, dy = (0, -12) if upd == 0 else geom
            lab.player(ox + dx, oy + dy, vy=0x100, **kw)
            m[psc.SLOT + 0x20] = SENTINEL
            m[0xD521] = 0
            lab.callback()
            o.cpu.ix = 0xD500
            o.call(0x64CB)
            rows.append({"update": upd, "role": "top contact (damage)" if upd == 0 else "side contact attempt",
                         "helper_ran": m[psc.SLOT + 0x20] != SENTINEL, "damage_request": m[0xD3B0] == 0xFF, "wall_bits": (m[0xD523] >> 2) & 3,
                         "pushed": m[0xD502] == 1 and o.word(0xD511) != ox + dx, "cooldown_after": m[psc.SLOT + 0x1F]})
            m[0xD3B0] = 0
        seq[pname] = rows
    out["sequence_after_damage"] = seq
    out["sequence_summary"] = {
        k: {"inactive_updates": [r["update"] for r in v[1:] if not r["helper_ran"]],
            "first_active_update_after_damage": next((r["update"] for r in v[1:] if r["helper_ran"]), None),
            "first_wall_or_push_update": next((r["update"] for r in v[1:] if r["wall_bits"] or r["pushed"]), None)} for k, v in seq.items()}

    # ---- what decrements / freezes the cooldown --------------------------------
    scope = {}
    for state, y0 in ((1, 864), (2, 846), (3, 852), (4, 864)):
        l2 = _spike_lab_state(rom, state, y0)
        l2.reset()
        l2.m[psc.SLOT + 0x1F] = 16
        l2.m[psc.SLOT + 0x20] = SENTINEL
        l2.player(l2.obj16(0x11) + 200, y0, vy=0x100)
        l2.callback()
        scope[str(state)] = {"cooldown_after_one_callback": l2.m[psc.SLOT + 0x1F], "helper_ran": l2.m[psc.SLOT + 0x20] != SENTINEL}
    l3 = _spike_lab_state(rom, 2, 846)
    l3.reset()
    l3.m[psc.SLOT + 4] = 0x40
    l3.m[psc.SLOT + 0x1F] = 16
    l3.player(l3.obj16(0x11) + 200, 846, vy=0x100)
    l3.callback()
    scope["state2_inactive_bit6"] = {"cooldown_after_one_callback": l3.m[psc.SLOT + 0x1F]}
    out["cooldown_decrement_scope"] = scope

    # ---- cooldown across the 102-update cycle ----------------------------------
    cyc = []
    for left in (30, 5):
        l4 = psc.spike_lab(rom)
        l4.m[psc.SLOT + 4] &= ~0x40
        l4.player(l4.obj16(0x11) + 300, 864, vy=0)
        log = []
        for _ in range(60):
            l4.frame()
            if l4.m[psc.SLOT + 1] == 2:
                break
        # state 2 runs 48 updates; wait until `left` remain
        while l4.m[psc.SLOT + 7] > left:
            l4.frame()
        l4.m[psc.SLOT + 0x1F] = 16
        for _ in range(130):
            l4.frame()
            log.append([l4.m[psc.SLOT + 1], l4.obj16(0x14), l4.m[psc.SLOT + 0x1F]])
        runs = []
        for st, y, cd in log:
            if runs and runs[-1][0] == st and runs[-1][3] == cd:
                runs[-1][1] += 1
            else:
                runs.append([st, 1, y, cd])
        cyc.append({"state2_updates_left_when_set": left, "runs_[state,updates,y,cooldown]": runs})
    out["cooldown_across_cycle"] = cyc

    out["answer"] = {
        "damage_cooldown": "object +$1F = 16 after a damaging top contact; decremented once per helper call (states 1 and 2 only, +$04 bit 6 clear); frozen in states 3/4 and while asleep; it is not cleared by the cycle, so a remainder carries into the next raised phase",
        "contact_detection": "the whole contact helper $32CFD returns before `CALL $033B` while the cooldown is non-zero: $6328 is not run, +$20/+$21 and the player's $D521 are not written for the 16 cooldown updates",
        "side_wall_response": "NOT active during the cooldown: the wall is only the merged copy of $D521 (scheduler $5DD1 zeroes $D521 at the start of every object phase, $6328 is the only writer, merge $64CB copies it into $D523 for the next player pass); no $6328 call means no wall bit. It also requires a non-attacking, non-invulnerable player (merge gate)",
        "grounded_attacker_push": "NOT active during the cooldown for the same reason (push code sits after the $033B call); it is an alternative to the wall because attackers are not merged",
        "does_the_cooldown_disable_the_whole_object": "No for the object itself (state script, movement, rise/hold/retract, rendering and +$04 handling continue); yes for everything the helper does (top damage, side wall and push)",
        "first_active_update_after_damage": 17,
    }
    return out


def model_push(dx: int, dy: int, ex=8, ey=24, oex=16, oey=24) -> int | None:
    """$32D2B..: None = no push; +23 only for a horizontal-dominated contact with dx >= 0; every other non-top contact (left, below) is -23."""
    c = psc.model_contact(dx, dy, ex, ey, oex, oey)
    if c in (0, 1):
        return None
    return 23 if c == 4 else -23


def a2_grounded_push(rom: bytes) -> dict:
    out = {"evidence": "BYTE-VERIFIED ASSEMBLY ($32D2B..$32D58) + CONTROLLED ROUTINE RESULT (real states 1 and 2 callbacks)"}
    total = mism = 0
    maps = {}
    for state, y0 in ((2, 846), (1, 864)):
        lab = _spike_lab_state(rom, state, y0)
        m, o = lab.m, lab.o
        ox, oy = lab.obj16(0x11), lab.obj16(0x14)
        grid = {}
        for ex, f3 in ((8, 2), (9, 2)):
            for dy in range(-30, 31):
                row = []
                for dx in range(-30, 31):
                    lab.reset()
                    lab.player(ox + dx, oy + dy, vy=0x100, f3=f3, f22=2, ex=ex)
                    m[0xD504] = 0
                    lab.callback()
                    px = o.word(0xD511) - ox
                    pushed = m[0xD502] == 1 and o.word(0xD511) != ox + dx
                    want = model_push(dx, dy, ex=ex)
                    if want is not None and ox + dx == ox + want:
                        want = None                # already at the push X: only the requested state changes
                        got = None if not pushed else px
                        if m[0xD502] == 1 and not pushed:
                            got = None
                    else:
                        got = px if pushed else None
                    total += 1
                    if m[0xD3B0] == 0xFF:
                        got = "damage"
                        want = "damage" if psc.model_contact(dx, dy, ex, 24, 16, 24) == 1 else want
                    if got != want:
                        mism += 1
                        if mism < 6:
                            out.setdefault("first_mismatches", []).append([state, ex, dx, dy, got, want])
                    row.append("D" if got == "damage" else ("R" if got == 23 else ("L" if got == -23 else ".")))
                grid.setdefault(str(ex), []).append("".join(row))
        maps[str(state)] = grid
    out["cases"] = total
    out["mismatches_vs_model"] = mism
    out["map_legend"] = "rows dy -30..+30, columns dx -30..+30; D damage (top cone), R pushed to objX+23, L pushed to objX-23, . nothing; grounded attacker, vy >= 0, Sonic extents 8x24 (key '8') and 9x24 (key '9')"
    out["maps_state2_extent8"] = maps["2"]["8"]
    out["maps_state1_equal_to_state2"] = maps["1"] == maps["2"]
    # independence of facing / orientation / speed sign / object mirror
    indep = {"cases": 0, "mismatches": 0}
    lab = _spike_lab_state(rom, 2, 846)
    m, o = lab.m, lab.o
    ox, oy = lab.obj16(0x11), lab.obj16(0x14)
    for dx, dy in ((18, 0), (-18, 0), (3, 10), (-3, 10), (10, 20), (0, 0), (1, 0), (23, 0), (-23, 0), (5, 24)):
        base = None
        for d504 in range(0, 256, 5):
            for vx in (0, 0x300, 0xFD00):
                for obj4 in (0x00, 0x10, 0x02, 0x80):
                    lab.reset()
                    lab.player(ox + dx, oy + dy, vx=vx, vy=0x100, f3=2, f22=2)
                    m[0xD504] = d504
                    m[psc.SLOT + 4] = obj4
                    lab.callback()
                    res = (o.word(0xD511) - ox, m[0xD502], o.word(0xD516), m[0xD3B0])
                    base = base or res
                    indep["cases"] += 1
                    if res != base:
                        indep["mismatches"] += 1
    out["independence"] = {**indep, "varied": "player byte $D504 (all residues of 5), X speed (0, +3.0, -3.0), object +$04 (0, mirror $10, $02, $80); ten positions",
                           "result": "push position, requested state, X speed and damage request never change: facing, speed sign and object orientation are not read"}
    # posture gates
    gates = {}
    for name, f3, f22 in (("grounded_attacker", 2, 2), ("grounded_walker", 0, 2), ("airborne_attacker", 3, 0), ("airborne_walker", 1, 0)):
        r = _spike_probe(lab, 18, 0, f3=f3, f22=f22, merge=False)
        gates[name] = {"push_x": r["push_x"], "damage": r["damage_request_d3b0"]}
    gates["grounded_attacker_below"] = {"push_x": _spike_probe(lab, 3, 10, f3=2, f22=2, merge=False)["push_x"]}
    out["posture_gates"] = gates
    out["rule"] = {
        "applies_when": "cooldown 0, +$04 bit 6 clear, state 1 or 2, player Y speed >= 0, $6328 contact bit is not 'player above' (bit 0), $D522 bit 1 AND $D503 bit 1 (grounded attacker)",
        "result": "requested state 1, X speed 0, X := objX + 23 when contact bit 2 (horizontal-dominated, dx >= 0) else objX - 23; Y untouched; no damage",
        "contact_from_below": "a vertical-dominated 'player below' contact (dy 0..24, depth 24-dy <= horizontal depth 24-|dx|) clears the horizontal bits, so +$21 bit 2 is clear and the push is ALWAYS -23 (left), even for dx > 0",
        "horizontal_right": "R iff contact bit 2: dx >= 0 and (24 - dx) < vertical depth (24 - |dy|, dy <= 24); ties go to the vertical axis (so dx == |dy| is vertical)",
        "horizontal_left": "dx < 0 and (24 - |dx|) < vertical depth: -23; the dx = 0 column is on the right-hand branch (dx >= 0)",
        "extent_9_state_0F": "extents 9 shift the horizontal depth by one (key '9' map); the rule is unchanged",
        "after_push": "the player callback of the next update applies requested state 1 ($45B3 clears $D503 bit 1): the roll ends; no other speed is touched",
        "poc_assumption_check": "POC '-23 from below' is correct for below-contact; the +23 case exists only for horizontal-dominated right-side contact",
    }
    return out


# ------------------------------------------------------------------- A3 ---- #
def _find(s, type_id: int, x: int | None = None):
    m = s.mem
    for i in range(19):
        b = 0xD540 + i * 0x40
        if m[b] == type_id and (x is None or s.u16(b + 0x11) == x):
            return b
    return None


def _lifecycle_driver(path):
    """path(c) -> (px, py). Written at update boundary c; speeds zeroed so the teleports are the only movement."""
    def drv_factory(e):
        s = e.s

        def drv(c):
            px, py = path(c)
            s.w16(0xD511, px); s.w16(0xD514, py); s.w16(0xD516, 0); s.w16(0xD518, 0)
        return drv
    return drv_factory


def a3_lifecycle(rom: bytes) -> dict:
    out = {"evidence": "EMULATED ORIGINAL FRAME (THZ1, update-aligned) + SOURCE-TRACED BEHAVIOR (scheduler $5DD1, $61E1, $5EF8, platform $8908, spike $32C8B)"}
    e = psc.Emu(rom, "thz1")
    al = Aligned(e)
    s, m = e.s, e.s.mem

    def lift_sample():
        b = _find(s, 0x28, 592)
        return None if b is None else (s.u16(b + 0x14), m[b + 1], m[b + 4])

    def spike_sample():
        b = _find(s, 0x1B, 1344)
        return None if b is None else (s.u16(b + 0x14), m[b + 1], m[b + 4] & 0x40, m[b + 7], m[b + 0x1F])

    def setup_at(x, y, floor=False):
        def f():
            e.place(x, y, 0, 0, cur=1, f3=0, floor=floor)
        return f

    def drive(path, first):
        d = _lifecycle_driver(path)(e)

        def drv(c):
            if c == 0:
                first()
            d(c)
        return drv

    # ---------------- lift `$28` state 11 (THZ1 #1 (592,464), 144-update period) -------------------
    lift = {"object": {"type": "0x28", "placement": [592, 464], "state": 11, "period_updates": 144}}
    arrivals = []
    for W in (0, 17, 60):
        path = lambda c, W=W: (300, 460) if c < W else (min(300 + 2 * (c - W), 700), 460)
        rows = al.run(drive(path, setup_at(300, 460)), lift_sample, 460)
        ys = [r[0] if r else None for r in rows]
        created = next(i for i, y in enumerate(ys) if y is not None)
        arrivals.append({"approach": "from_left_2px_per_update", "wait_updates_before_walking": W, "created_at_update": created,
                         "first_rows_[Y,state,+04]": [list(r) for r in rows[created:created + 5]],
                         "y_at_absolute_update_330": ys[330], "y_at_absolute_update_400": ys[400], "y_100_updates_after_creation": ys[created + 100]})
    for W in (0, 17):
        path = lambda c, W=W: (1300, 460) if c < W else (max(1300 - 2 * (c - W), 700), 460)
        rows = al.run(drive(path, setup_at(1300, 460)), lift_sample, 520)
        ys = [r[0] if r else None for r in rows]
        created = next((i for i, y in enumerate(ys) if y is not None), None)
        arrivals.append({"approach": "from_right_2px_per_update", "wait_updates_before_walking": W, "created_at_update": created,
                         "y_at_creation": ys[created] if created is not None else None, "y_at_absolute_update_330": ys[330], "y_at_absolute_update_500": ys[500]})
    lift["arrival_dependence"] = arrivals
    lift["phase_reading"] = ("the lift's Y at a fixed absolute update differs with the arrival time and direction: the phase origin is the creation update, "
                             "not the level clock (differences of tens of pixels in the table)")
    # creation / movement while asleep
    rows = al.run(drive(lambda c: (300 + 2 * min(c, 250), 460), setup_at(300, 460)), lift_sample, 80)
    first = next(i for i, r in enumerate(rows) if r)
    lift["asleep_motion"] = {"first_rows_[Y,state,+04]": [list(r) for r in rows[first:first + 8]],
                             "reading": "+$04 starts at $40 (asleep); state 0 -> 11 takes two updates; the lift moves 1 px/update from the third update while +$04 bit 6 is still set (callback $86DA and its keep-alive bit 1 do not depend on bit 6)"}
    # keep-alive radius and continuity: 30 updates beside the lift, 300 updates at distance d, 4 updates back; reference = never leaves
    def away_path(px_away):
        return lambda c: (480, 460) if (c < 30 or c >= 330) else (px_away, 460)
    ref_rows = al.run(drive(away_path(480), setup_at(480, 460)), lift_sample, 334)
    ref_y = [r[0] if r else None for r in ref_rows]
    radius = []
    for d in (400, 639, 640, 641):
        for side in (1, -1):
            rows = al.run(drive(away_path(592 + side * d), setup_at(480, 460)), lift_sample, 334)
            ys = [r[0] if r else None for r in rows]
            away = ys[31:330]
            radius.append({"player_dx_while_away": side * d, "updates_alive_while_away": sum(1 for y in away if y is not None), "away_updates": len(away),
                           "first_missing_update": next((i + 31 for i, y in enumerate(away) if y is None), None),
                           "y_after_return_[330..333]": ys[330:334], "free_running_reference_y_[330..333]": ref_y[330:334],
                           "continuous_with_free_run": ys[330:334] == ref_y[330:334]})
    lift["keep_alive_player_distance"] = radius
    lift["rule"] = {
        "creation": "steady scrolling: map cell 2 only (anchor 32..96 px outside the visible band, scan every 4th update); level start/teleport: cells 0/1 as well (initial fill)",
        "state_11_phase": "callback runs every update while the slot exists, asleep or awake: the Y path is a pure function of updates since creation (Y -1 px/update for 16 x aux1 updates, then reversing)",
        "keep_alive": "state 11 sets +$04 bit 1: $61E1 does not delete it; $8908 deletes it (type $FE, token cleared, so it is recreated) when |playerX - x| >= 640 or |playerY - y| >= 672 (PLAYER_DIST, camera independent); the X limit was verified at 639/640 on both sides",
        "recreation": "a deleted lift is recreated at the placement Y with a fresh counter (phase 0) when it re-enters cell 2 (or at the next level start)",
        "state_5_sag_platforms": "stationary; no keep-alive bit, so deleted by $61E1 outside the lifetime window and recreated at rest; support needs +$04 bit 6 clear (awake), the sag counter lives only while awake",
        "different_phase_on_arrival": "yes: phase depends on the update at which the placement was created (arrival time/direction) and is reset by deletion",
    }
    out["lift_28"] = lift

    # ---------------- moving spike `$1B` (THZ1 (1344,864)) ----------------------------------------
    sp = {"object": {"type": "0x1B", "placement": [1344, 864]}}
    created = []
    for speed in (2, 6):
        path = lambda c, sp_=speed: (1000 + sp_ * c, 860) if c < 400 // sp_ else (1400, 860)
        rows = al.run(drive(path, setup_at(1000, 860, True)), spike_sample, 220)
        first = next(i for i, r in enumerate(rows) if r)
        events, last = [], None
        for i in range(first, first + 130):
            r = rows[i]
            if r is None:
                events.append([i - first, "deleted"])
                break
            k = (r[1], r[2])
            if k != last:
                events.append([i - first, {"y": r[0], "state": r[1], "asleep_bit6": bool(r[2]), "timer": r[3]}])
                last = k
        created.append({"camera_speed_px_per_update": speed, "events_since_creation": events})
    sp["creation_and_wake"] = created
    sp["reading_creation"] = ("created asleep in cell 2 (state 0, +$04 = $40) and parked in state 1 (callback returns while asleep): the rise does not start until $61E1 clears bit 6 "
                              "(about 9..29 updates later depending on scroll speed); the 102-update cycle therefore starts at WAKE, not at creation")
    sleep_rows = []
    for K in (0, 10, 30, 60):
        for pre in (3, 40):
            e.restore()
            state = {"mode": "approach", "px": 1000, "k": 0, "pre": 0}

            def drv(c, state=state, K=K, pre=pre):
                if c == 0:
                    e.place(1000, 860, 0, 0, cur=1, f3=0, floor=True)
                r = spike_sample()
                if state["mode"] == "approach":
                    state["px"] += 3
                    if r and r[2] == 0:
                        state["mode"], state["k"] = "awake_hold", 0
                elif state["mode"] == "awake_hold":
                    state["k"] += 1
                    if state["k"] >= pre:
                        state["mode"] = "leave"
                elif state["mode"] == "leave":
                    state["px"] -= 2
                    if r and r[2]:
                        state["mode"], state["k"], state["entered"] = "asleep_hold", 0, r
                elif state["mode"] == "asleep_hold":
                    state["k"] += 1
                    if state["k"] >= K:
                        state["mode"], state["before"] = "return", r
                elif state["mode"] == "return":
                    state["px"] += 2
                    if r and r[2] == 0:
                        state["mode"], state["k"], state["woke"], state["wake_i"] = "after", 0, r, c
                s.w16(0xD511, state["px"]); s.w16(0xD514, 860); s.w16(0xD516, 0); s.w16(0xD518, 0)
            rows = al.run(drv, spike_sample, 700, restore=False)
            wake_i = state.get("wake_i")
            tail = []
            last = None
            if wake_i is not None:
                for i in range(wake_i, min(wake_i + 80, len(rows))):
                    r = rows[i]
                    if r and r[1] != last:
                        tail.append([i - wake_i, {"y": r[0], "state": r[1], "timer": r[3]}])
                        last = r[1]
            sleep_rows.append({"awake_hold_updates": pre, "asleep_hold_updates": K, "state_when_falling_asleep": list(state["entered"][:2]) if "entered" in state else None,
                               "state_after_sleep": list(state["before"][:2]) if "before" in state else None,
                               "state_changes_after_wake_[update_since_wake,{y,state,timer}]": tail})
    sp["sleep_wake_drift"] = sleep_rows
    sp["reading_sleep"] = ("while asleep (bit 6 set, awake margin left) the scripts' own timers keep running but the callbacks are skipped: a spike put to sleep in the raised phase "
                           "finishes its 48-update hold asleep, parks in state 3 raised at Y 846 and retracts only after waking; a long enough sleep desynchronises it from any fixed clock")
    # deletion and recreation (camera and player teleported together so the lifetime window is crossed at once)
    def del_driver(c):
        if c == 0:
            e.place(1000, 860, 0, 0, cur=1, f3=0, floor=True)
        elif c == 220:
            e.place(924, 860, 0, 0, cur=1, f3=0, floor=True)          # object 420 px right of the player: beyond the +96 ring
        elif c == 330:
            e.place(1144, 860, 0, 0, cur=1, f3=0, floor=True)         # camera 1040: object at screen 304 (+48), creation ring
        elif c > 330:
            s.w16(0xD511, 1144 + 2 * (c - 330)); s.w16(0xD514, 860)
        elif c < 150:
            s.w16(0xD511, 1000 + 3 * c); s.w16(0xD514, 860)
        elif c < 220:
            s.w16(0xD511, 1000 + 3 * 150); s.w16(0xD514, 860)
        if c not in (0, 220, 330):
            s.w16(0xD516, 0); s.w16(0xD518, 0)
    rows = al.run(del_driver, spike_sample, 470)
    runs, last = [], None
    for i, r in enumerate(rows):
        k = None if r is None else (r[1], r[2])
        if k != last:
            runs.append([i, None if r is None else {"y": r[0], "state": r[1], "asleep": bool(r[2])}])
            last = k
    sp["deletion_and_recreation_events_[update,row]"] = runs
    sp["rule"] = {
        "creation": "steady scrolling: cell 2 only (outer ring, asleep); initial fill/teleport: cells 0/1 as well",
        "initial_state": "state 0 callback $32C7D: +$03 bit 7, requested state 1, cooldown 0; the first rise happens after the first awake update",
        "script_vs_callback": "states 2 (raised hold) and 4 (hidden hold) are timed by the object script (48 updates, runs asleep); states 1 (rise, 3 x 6 px) and 3 (retract) are advanced by callbacks that return while +$04 bit 6 is set",
        "lifetime": "no keep-alive bit: deleted by $61E1 beyond the generic lifetime window (LEFT-96/RIGHT+96, token cleared -> recreated) and restarted from state 0/1 at the placement Y",
        "different_phase_on_arrival": "yes: phase origin is the wake update after (re)creation; sleep/wake episodes shift it; deletion restarts it",
        "widescreen": "the POC's post-wake retention adapter (max(0, view-256)) keeps a spike alive where the SMS would delete and restart it, so backtracking in the wide view can show a different phase than the original; at 256 px it is identical",
    }
    out["spike_1b"] = sp
    out["relation_to_viewport_audit"] = ("uses the generic lifetime of docs/viewport-semantics-audit.md unchanged (create cell 2 / initial fill, awake band [-32, 288), delete outside the "
                                         "[-96, 352) ring window, +$04 bit 1 keep-alive); the only $28/$1B-specific facts are the keep-alive radius 640x672 (PLAYER_DIST) and the callback gating above")
    return out


# ------------------------------------------------------------------- A4 ---- #
def _aligned_spike_run(al, e, hurt, x0, y0, vx, vy, cur, f3, floor=False, pad=0, frames=48):
    s, m = e.s, e.s.mem
    psc.TERRAIN_HURT.clear()
    hurt.clear()

    def setup(c):
        if c == 0:
            e.place(x0, y0, vx, vy, cur=cur, f3=f3, floor=floor)

    def sample():
        return (e.u16(0xD511), e.u16(0xD514), m[0xD503] & 1, m[0xD501], s16(e.u16(0xD518)))

    def stop(rows):
        path = rows[1:]
        if not path:
            return False
        if hurt or path[-1][0] < 1420 or path[-1][0] > 1650:
            return True
        n = len(path) - 1
        return bool(n >= 8 and path[-1][2] == 0 and m[0xD522] & 2 and abs(s16(e.u16(0xD516))) < 0x100) or len(path) >= frames

    return al.run(setup, sample, frames + 2, pad=pad, stop=stop)[1:]


def a4_static_spike_aligned(rom: bytes, legacy: dict | None = None) -> dict:
    out = {"evidence": "EMULATED ORIGINAL FRAME (THZ1, update-aligned replay of the diagnostic grid of docs/platform-spike-collision-audit.md section 2.3)",
           "harness_note": HARNESS_NOTE}
    e = psc.Emu(rom, "thz1")
    al = Aligned(e)
    s, m = e.s, e.s.mem
    hurt = []
    s.add_pc_hook(psc.HURT_ENTRY, lambda mach: hurt.append((s.frame, e.u16(0xD511), e.u16(0xD514))))
    s.add_pc_hook(0x6AE0, lambda mach: psc.TERRAIN_HURT.append(s.frame))
    counts, ex = {}, {"E1_foot_in_solid_rows_only_while_rising": [], "E2_foot_in_solid_rows_not_rising_undamaged": []}
    total = 0
    for label, xs in (("from_left", (1448, 1472, 1488)), ("from_right", (1584, 1600, 1624)), ("from_above", (1504, 1519, 1534, 1549, 1564))):
        for sn, cur, f3 in (("jump", 0x0A, 3), ("fall", 0x0E, 1)):
            for y0 in (790, 815, 835):
                for vxn in (-6, -4, -2, 0, 2, 4, 6):
                    for vyn in (-2, 0, 3):
                        for x0 in xs:
                            path = _aligned_spike_run(al, e, hurt, x0, y0, vxn * 256, vyn * 256, cur, f3)
                            cl = psc._spike_class(x0, path, hurt)
                            total += 1
                            counts[f"{label}|{sn}|{cl}"] = counts.get(f"{label}|{sn}|{cl}", 0) + 1
                            if cl in ex and sn == "jump":
                                ex[cl].append({"start": [x0, y0], "vx_px": vxn, "vy_px": vyn, "state": sn, "end": list(path[-1][:2]), "updates": len(path)})
    for label, x0s, pad, sgn in (("ground_from_left", (1440, 1470, 1490), psc.PAD["RIGHT"], 1), ("ground_from_right", (1590, 1620), psc.PAD["LEFT"], -1)):
        for sname, cur, f3 in (("walk", 5, 0), ("run", 6, 0), ("roll", 9, 2)):
            for vxn in (1, 3, 5, 7):
                for x0 in x0s:
                    path = _aligned_spike_run(al, e, hurt, x0, psc.PAIR_GROUND_Y, sgn * vxn * 256, 0x700, cur, f3, floor=True, pad=pad, frames=36)
                    cl = psc._spike_class(x0, path, hurt)
                    total += 1
                    counts[f"{label}|{sname}|{cl}"] = counts.get(f"{label}|{sname}|{cl}", 0) + 1
    out["runs"] = total
    out["counts_aligned"] = dict(sorted(counts.items()))
    old = (legacy or json.loads((ROOT / "data/rom-cache/platform-spike-collision.json").read_text(encoding="utf-8")))["static_spike_diagonal_sweep"]["counts"]
    out["counts_legacy_cache"] = old
    out["class_totals_aligned"] = _class_totals(counts)
    out["class_totals_legacy"] = _class_totals(old)
    out["differences"] = {k: [counts.get(k, 0), old.get(k, 0)] for k in sorted(set(counts) | set(old)) if counts.get(k, 0) != old.get(k, 0)}
    out["aligned_E_cases_jump"] = ex

    # --- the ten legacy diagnostic rows: initial state + per-update rows -----------------
    legacy_cases = []
    d = legacy or json.loads((ROOT / "data/rom-cache/platform-spike-collision.json").read_text(encoding="utf-8"))
    lex = d["static_spike_diagonal_sweep"]["examples_of_E_X"]
    for c in lex["E1_foot_in_solid_rows_only_while_rising"] + lex["E2_foot_in_solid_rows_not_rising_undamaged"]:
        legacy_cases.append(c)
    rows_out = []
    for c in legacy_cases:
        cur, f3 = (0x0A, 3) if c["state"] == "jump" else (0x0E, 1)
        x0, y0 = c["start"]
        initial = {}

        def sample():
            return {"x": e.u16(0xD511), "y": e.u16(0xD514), "vx": s16(e.u16(0xD516)), "vy": s16(e.u16(0xD518)), "state_d501": m[0xD501], "requested_d502": m[0xD502],
                    "d503": m[0xD503], "floor_d522": m[0xD522], "prev_flags_d36c": m[0xD36C], "lives": m[0xD299]}

        def setup(k):
            if k == 0:
                e.place(x0, y0, c["vx"] * 256, c["vy"] * 256, cur=cur, f3=f3, floor=False)
        hurt.clear(); psc.TERRAIN_HURT.clear()
        rows = al.run(setup, sample, 40, stop=lambda r: bool(hurt) or (len(r) > 1 and not (1420 <= r[-1]["x"] <= 1650)))
        path5 = [(r["x"], r["y"], r["d503"] & 1, r["state_d501"], r["vy"]) for r in rows[1:]]
        cls = psc._spike_class(x0, path5, hurt)
        rows_out.append({"case": c, "legacy_outcome_end": c["end"], "legacy_updates": c["frames"], "teleport_initial_state": rows[0],
                         "aligned_class": cls, "aligned_hurt_update": (len(rows) - 1) if hurt else None,
                         "aligned_rows_first_8_updates": rows[:9], "aligned_end": [rows[-1]["x"], rows[-1]["y"]], "aligned_updates": len(rows) - 1})
    out["legacy_ten_cases_replayed"] = rows_out
    out["first_update_rule"] = {
        "teleport_semantics": "Emu.place() writes the REQUESTED state ($D502) only; the current state $D501 stays 1 (stand) for the first update, the engine applies the request at the start of that update",
        "update_1": "airborne X speed |vx| > $0400 is clamped to +-$0400 (no drag that update); |vx| <= $0400 gets -16/256 drag toward 0 per update (observed -1024 -> -1008, +512 -> +496); gravity adds +48/256 to Y speed per update",
        "evidence": "rows in legacy_ten_cases_replayed (three case families: vx -6 and -4 px, +2 px) and the aligned class table",
    }
    out["interpretation"] = (
        "The six unresolved cases are the six E1 rows (rising teleports with vx -6/-4). Their difference from the older runs was the unaligned first update (vx -1004 instead of -1024 for the "
        "first -4 case, and x advancing 2 px instead of 1 px for the +2 px E2 rows), not different ROM behaviour. With update-aligned replay the rows are reproducible; the E2 "
        "set moves to the x >= 1564, vx +4 starts (leaving the 64 px block in one step); every other class is unchanged within 2% of runs."
    )
    return out


def _class_totals(counts: dict) -> dict:
    t = {}
    for k, v in counts.items():
        if k.startswith("ground"):
            continue
        cl = k.split("|")[2][:2]
        t[cl] = t.get(cl, 0) + v
    return dict(sorted(t.items()))


# =========================================================================== #
# PART B
# =========================================================================== #
def decode_script(rom: bytes, bank: int, start: int, limit: int = 120) -> list:
    """Object state-script decoder (same FF commands as docs/object-50.md; unknown commands raise)."""
    pc, seen, out = start, set(), []
    while len(out) < limit:
        if pc in seen:
            out.append({"cpu": h(pc), "op": "loops_back"})
            break
        seen.add(pc)
        o = rom_of(bank, pc)
        b = rom[o]
        if b != 0xFF:
            out.append({"cpu": h(pc), "op": "record", "duration": b, "frame": rom[o + 1], "callback": h(u16(rom, o + 2))})
            pc += 4
            continue
        c = rom[o + 1]
        a = rom[o + 2:o + 10]
        w = lambda i: a[i] | (a[i + 1] << 8)
        e = {"cpu": h(pc), "cmd": h(c, 2)}
        if c == 0:
            e.update(op="restart_state"); out.append(e); break
        if c == 3:
            e.update(op="request_state", state=a[0]); out.append(e); break
        if c == 1:
            e.update(op="call", target=h(w(0))); pc += 4
        elif c == 2:
            e.update(op="velocity_8_8", x=s16(w(0)), y=s16(w(2))); pc += 6
        elif c == 4:
            e.update(op="spawn", type=h(a[0], 2), dx=s16(w(1)), dy=s16(w(3)), parameter=h(a[5], 2)); pc += 8
        elif c == 5:
            e.update(op="call_and_set_callback", target=h(w(0)), callback=h(w(2))); pc += 6
        elif c == 6:
            e.update(op="sound", sound=h(a[0], 2)); pc += 3
        elif c == 7:
            e.update(op="jump", target=h(w(0))); pc = w(0)
        elif c == 9:
            e.update(op="set_field", offset=h(a[0], 2), value=h(a[1], 2)); pc += 4
        elif c == 0x0E:
            e.update(op="set_loop_counter", count=a[0]); pc += 3
        elif c == 0x0F:
            e.update(op="loop_jump", target=h(w(0))); pc += 4
        else:
            raise ValueError(f"unsupported command FF {c:02X} at ${pc:04X}")
        out.append(e)
    return out


def flow_ranges(rom: bytes, bank: int, entries: list, lo: int = 0x8000, hi: int = 0xC000) -> dict:
    """Reachable instruction ranges of paged-bank code (calls into other regions are noted but not followed)."""
    from z80dis import z80
    import re
    img = rom[0:0x8000] + rom[bank * 0x4000:(bank + 1) * 0x4000]
    seen, stack, external = {}, list(entries), set()
    while stack:
        pc = stack.pop()
        while lo <= pc < hi and pc not in seen:
            d = z80.decode(img[pc:pc + 4], pc)
            text = z80.disasm(d)
            ln = d.len or 1
            seen[pc] = ln
            mm = re.match(r"(CALL|JP|JR|DJNZ)\s+(?:[a-z]+,)?(0x[0-9a-f]+)$", text)
            if mm:
                t = int(mm.group(2), 16)
                if lo <= t < hi:
                    stack.append(t)
                else:
                    external.add(t)
            if text == "RET" or (text.startswith("JP ") and "," not in text) or (text.startswith("JR ") and "," not in text) or text.startswith("JP ("):
                break
            pc += ln
    rngs = []
    for pc in sorted(seen):
        if rngs and rngs[-1][1] == pc:
            rngs[-1][1] = pc + seen[pc]
        else:
            rngs.append([pc, pc + seen[pc]])
    return {"ranges": rngs, "external_targets": sorted(external)}


def region_record(rom: bytes, bank: int, entries: list, name: str) -> dict:
    fr = flow_ranges(rom, bank, entries)
    regs = []
    for a, b in fr["ranges"]:
        raw = rom[rom_of(bank, a):rom_of(bank, b)]
        regs.append({"cpu": f"{h(a)}-{h(b)}", "rom": f"{h(rom_of(bank, a), 5)}-{h(rom_of(bank, b), 5)}", "bytes": b - a, "first16": raw[:16].hex(), "sha256": sha(raw)})
    return {"name": name, "bank": h(bank, 2), "entries": [h(e) for e in entries], "regions": regs,
            "external_calls": [h(t) for t in fr["external_targets"]]}


VECTORS = {0x0329: 0x5EE1, 0x032C: 0x5E9C, 0x032F: 0x6065, 0x0332: 0x606B, 0x0335: 0x607A, 0x0338: 0x60FB, 0x033B: 0x6328, 0x033E: 0x5F54, 0x034A: 0x64F0,
           0x034D: 0x5FA0, 0x0353: 0x59E3, 0x0356: 0x59F3, 0x0359: 0x59C5, 0x035C: 0x59D8, 0x035F: 0x5F17, 0x0371: 0x5EB7, 0x0383: 0x61A5, 0x0386: 0x61B1,
           0x03EF: 0x61D6, 0x03F5: 0x4892}

SUPPORT = {
    0x12: {"bank": 12, "callbacks": [0xA265, 0xA26E]},
    0x34: {"bank": 30, "callbacks": [0x8C41, 0x8C9F, 0x8CA3, 0x8CFD]},
    0x0A: {"bank": 12, "callbacks": [0x9C86, 0x9C99]},
    0x0F: {"bank": 12, "callbacks": [0xA060, 0xA0C6, 0xA0E7, 0xA057, 0xA05B, 0xA089]},
}


def _frames_of(rom: bytes, type_id: int, wanted: list):
    m = o50.assets.object_mapping(rom, type_id)
    ptrs = o50.assets.mapping_frame_pointers(rom, m["mapping_cpu"])
    out = []
    for i in wanted:
        r = o50.assets.parse_frame_record(rom, ptrs[i])
        out.append({"frame": i, "record_cpu": h(ptrs[i]), "pieces": [{"y": p["relative_y"], "x": p["relative_x"], "tile_offset": p["tile_offset"]} for p in r["pieces"]],
                    "contact_extent_x": rom[r["frame_rom"] + 1], "contact_extent_y": rom[r["frame_rom"] + 2], "y_origin": r["y_origin"], "x_origin": r["x_origin"]})
    return out, {"mapping_cpu": h(m["mapping_cpu"]), "mapping_rom": h(m["mapping_rom"], 5), "pointer_entry_rom": h(m["pointer_table_rom"], 5), "frame_count": len(ptrs)}


def support_static(rom: bytes) -> dict:
    out = {"evidence": "DECODED DATA + BYTE-VERIFIED ASSEMBLY + SOURCE-TRACED BEHAVIOR"}
    frames_used = {0x12: [0], 0x34: [0, 1, 2, 3, 4], 0x0A: [0, 5, 6], 0x0F: [0, 7, 8, 9]}
    for t, info in SUPPORT.items():
        bank = info["bank"]
        tab = o50.anim.animation_state_table(rom, t)
        states = []
        for n, cpu in enumerate(tab["state_script_cpus"]):
            cmds = decode_script(rom, bank, cpu)
            states.append({"state": n, "script_cpu": h(cpu), "script_rom": h(rom_of(bank, cpu), 5), "script": cmds,
                           "frames": sorted({c["frame"] for c in cmds if c["op"] == "record"}),
                           "callbacks": sorted({c["callback"] for c in cmds if c["op"] == "record"})})
        frames, mapinfo = _frames_of(rom, t, frames_used[t])
        out[h(t, 2)] = {"type": h(t, 2), "bank": h(bank, 2), "type_table_entry_rom": h(tab["type_table_entry_rom"], 5), "state_table_cpu": h(tab["state_table_cpu"]),
                        "state_count": tab["state_count"], "states": states, "mapping": mapinfo, "frames_reachable": frames,
                        "code": region_record(rom, bank, info["callbacks"], f"type_{t:02x}_callbacks")}
    out["type_0a_and_0f_share_mapping"] = _frames_of(rom, 0x0A, [0])[1]["mapping_cpu"] == _frames_of(rom, 0x0F, [0])[1]["mapping_cpu"]
    out["type_34_art_base_table_cpu_0x8C98"] = list(rom[rom_of(30, 0x8C98):rom_of(30, 0x8C98) + 8])
    return out


def _support_record(type_id: int, x: int, y: int, param: int) -> bytes:
    sx, sy = x + 256, y + 256
    return bytes([type_id, sx & 0xFF, sx >> 8, sy & 0xFF, sy >> 8, 0x00, param, 0x00, 0x00])


def _kids(lab, skip_slot=psc.SLOT) -> list:
    m = lab.m
    return [(0xD540 + i * 0x40) for i in range(19) if m[0xD540 + i * 0x40] and 0xD540 + i * 0x40 != skip_slot]


def support_controlled(rom: bytes) -> dict:
    out = {"evidence": "CONTROLLED ROUTINE RESULT (real engine $64FA + callbacks on tools/oracle.py; one update = one lab.frame())"}

    # ---- type $12: HUD slide-away -------------------------------------------------------------
    lab = psc.ObjectLab(rom, 0x12, _support_record(0x12, 1936, 238, 0x97), 12, 0x00)
    m, o = lab.m, lab.o
    ys0 = [16, 16, 16, 16, 32, 32, 32, 32, 0, 0, 0, 0]
    m[0xDB34:0xDB40] = bytes(ys0)
    life, trace = 0, []
    for upd in range(1, 400):
        lab.frame()
        life = upd
        if upd in (1, 2, 3, 4, 5, 6, 50, 96, 97, 98, 99, 100):
            trace.append([upd, m[psc.SLOT], list(m[0xDB34:0xDB40])])
        if m[psc.SLOT] == 0xFF:
            break
    out["type_12"] = {"initial_sat_y_DB34_DB3F": ys0, "type_after_updates": trace, "updates_until_type_FF": life,
                      "final_sat_y_DB34_DB3F": list(m[0xDB34:0xDB40]),
                      "rule": "HUD slide-away: on every update where +$07 (the countdown of the 128-update record) is odd, i.e. every second update from the first, all 12 SAT Y bytes DB34..DB3F (three rows of four 8x16 HUD sprites at Y 16, 32, 0) are decremented by 1 (0.5 px/update upward); the object deletes itself (type $FF) in the update where SAT[$DB38] (the Y=32 row) reaches 0xE8..0xEF, i.e. after about 97 updates when the rows start at 16/32/0"}
    # emulated-independent sweep: lifetime as function of the second-row start Y
    lt = {}
    for y2 in (32, 20, 0, 200, 239, 240, 247, 248):
        l2 = psc.ObjectLab(rom, 0x12, _support_record(0x12, 1936, 238, 0x97), 12, 0x00)
        l2.m[0xDB34:0xDB40] = bytes([y2] * 12)
        n = 0
        for n in range(1, 600):
            l2.frame()
            if l2.m[psc.SLOT] == 0xFF:
                break
        lt[str(y2)] = n
    out["type_12"]["lifetime_by_second_row_start_y"] = lt

    # ---- type $34: explosion puff ------------------------------------------------------------------
    lab = psc.ObjectLab(rom, 0x34, _support_record(0x34, 1900, 230, 4), 30, 0x00)
    m, o = lab.m, lab.o
    m[0xD297] = 0
    m[0xD12F] = 0x03
    m[0xD2E2] = 0x00
    seq, last, life = [], None, 0
    for upd in range(1, 700):
        lab.frame()
        life = upd
        key = (m[psc.SLOT + 1], m[psc.SLOT + 6])
        if key != last:
            seq.append([upd, key[0], key[1], lab.obj16(0x11), lab.obj16(0x14)])
            last = key
        if m[psc.SLOT] == 0xFF:
            break
    out["type_34"] = {"parameter_3F": 4, "updates_until_type_FF": life, "state_frame_changes_[update,state,frame,x,y]": seq[:24],
                      "art_base_+$08/+$09": lab.m[psc.SLOT + 8], "contact_calls": "none: no $033B/$034D call in any callback (presentation only)",
                      "lifetime_rule": "+$1E = parameter; callback $8CFD (second to last record of each cycle) decrements +$1E and deletes the puff (type $FF) when it underflows"}
    lt = {}
    for parity in (0, 1):
        row = {}
        for p in (0, 1, 2, 4, 6):
            l2 = psc.ObjectLab(rom, 0x34, _support_record(0x34, 1900, 230, p), 30, 0x00)
            l2.m[0xD12F] = parity
            l2.reset()
            l2.m[0xD12F] = parity
            l2.m[psc.SLOT + 1] = 0; l2.m[psc.SLOT + 2] = 0; l2.m[psc.SLOT + 0xE] = 0; l2.m[psc.SLOT + 0xF] = 0
            n = 0
            for n in range(1, 900):
                l2.frame()
                if l2.m[psc.SLOT] == 0xFF:
                    break
            row[str(p)] = n
        lt[f"D12F_bit0_{parity}"] = row
    out["type_34"]["lifetime_by_parameter_and_D12F_bit0"] = lt
    out["type_34"]["lifetime_reading"] = "each script cycle ends in $8CA3, which re-selects the fast script (state 1, 26 updates) when $D12F bit 0 is set and the slow script (state 2, 50 updates) when it is clear; lifetime = (parameter + 1) cycles + 2 updates when $D12F is constant; with the free-running $D12F the five puffs of a boss (parameter 4) live about 150..250 updates"
    ba = {}
    for z in range(8):
        l3 = psc.ObjectLab(rom, 0x34, _support_record(0x34, 1900, 230, 4), 30, 0x00)
        l3.reset()
        l3.m[0xD297] = z
        l3.m[0xD12F] = 3
        l3.m[psc.SLOT + 8] = 0; l3.m[psc.SLOT + 9] = 0
        l3.m[psc.SLOT + 1] = 0; l3.m[psc.SLOT + 2] = 0; l3.m[psc.SLOT + 0xE] = 0; l3.m[psc.SLOT + 0xF] = 0
        l3.frame()
        ba[str(z)] = l3.m[psc.SLOT + 8]
    out["type_34"]["art_base_by_zone_D297"] = ba

    # ---- type $0A ------------------------------------------------------------------------------------
    # param 0: bonus calculator + sparkle emitter; param $FF: the sparkle
    lab = psc.ObjectLab(rom, 0x0A, _support_record(0x0A, 1700, 238, 0), 12, 0x00)
    m, o = lab.m, lab.o
    rows = []
    for time_bcd, rings in ((0x0010, 0x25), (0x0120, 0x25), (0x0500, 0x00), (0x0020, 0x99)):
        l2 = psc.ObjectLab(rom, 0x0A, _support_record(0x0A, 1700, 238, 0), 12, 0x00)
        l2.m[0xD2BF], l2.m[0xD2C0] = time_bcd & 0xFF, time_bcd >> 8
        l2.m[0xD29A] = rings
        l2.m[0xD2A6] = l2.m[0xD2A7] = 0
        l2.o.word(0xD511, 1750); l2.o.word(0xD514, 230)
        l2.reset()
        l2.m[0xD2BF], l2.m[0xD2C0] = time_bcd & 0xFF, time_bcd >> 8
        l2.m[0xD29A] = rings
        l2.m[psc.SLOT + 1] = 0; l2.m[psc.SLOT + 2] = 0; l2.m[psc.SLOT + 0xE] = 0; l2.m[psc.SLOT + 0xF] = 0
        l2.o.word(0xD511, 1750); l2.o.word(0xD514, 230)
        l2.frame(); l2.frame()
        l2.o.cpu.hl = 0
        l2.o.call(0x041F)
        rows.append({"time_D2BF_D2C0_bcd": h(time_bcd), "rings_D29A_bcd": h(rings, 2), "D2A6_after_init": l2.o.word(0xD2A6), "routine_041F_HL": l2.o.cpu.hl,
                     "state_after_init": l2.m[psc.SLOT + 1], "position_after_init": [l2.obj16(0x11), l2.obj16(0x14)]})
    # emitter timeline
    lab = psc.ObjectLab(rom, 0x0A, _support_record(0x0A, 1700, 238, 0), 12, 0x00)
    m, o = lab.m, lab.o
    o.word(0xD511, 1750); o.word(0xD514, 230)
    seen = {}
    spawn = []
    for upd in range(1, 80):
        o.word(0xD511, 1750 + upd); o.word(0xD514, 230)
        lab.frame()
        for a in _kids(lab):
            if a not in seen:
                seen[a] = upd
                spawn.append({"update": upd, "slot": h(a), "type": h(m[a], 2), "x": lab.o.word(a + 0x11), "y": lab.o.word(a + 0x14), "parameter_3F": m[a + 0x3F]})
    # child lifetime
    child = psc.ObjectLab(rom, 0x0A, _support_record(0x0A, 1700, 238, 0xFF), 12, 0x00)
    fr, last, n = [], None, 0
    for n in range(1, 120):
        child.frame()
        k = (child.m[psc.SLOT], child.m[psc.SLOT + 6])
        if k != last:
            fr.append([n, h(k[0], 2), k[1]])
            last = k
        if child.m[psc.SLOT] in (0xFE, 0xFF, 0):
            break
    out["type_0a"] = {"param_0_init": rows, "emitter_spawns_first_80_updates": spawn[:12],
                      "sparkle_param_FF": {"state_frame_type_changes_[update,type,frame]": fr, "updates_until_removed": n},
                      "rule": "parameter 0: init callback $9C86 requests state 2 and runs `CALL $041F; LD ($D2A6),HL` (the same time/ring bonus routine the $19 child uses), then snaps to the player anchor; state 2 loops forever: 8 updates, snap to player, spawn a $0A (parameter $FF) at (0,-12), 8 updates, snap, spawn at (0,-8). Parameter nonzero: init requests state 1 and returns; state 1 alternates frames 5/6 for 4 updates each (28 updates) and then deletes itself ($FE through $034A)"}

    # ---- type $0F as left behind by the boss ---------------------------------------------------------------
    lab = psc.ObjectLab(rom, 0x0F, _support_record(0x0F, 1936, 238, 0), 12, 0x00)
    m = lab.m
    seq, last, n = [], None, 0
    for n in range(1, 400):
        lab.frame()
        k = (m[psc.SLOT], m[psc.SLOT + 1], m[psc.SLOT + 6])
        if k != last:
            seq.append([n, h(k[0], 2), k[1], k[2]])
            last = k
        if m[psc.SLOT] in (0xFE, 0xFF, 0):
            break
    out["type_0f"] = {"parameter_3F": 0, "state_frame_changes_[update,type,state,frame]": seq, "updates_until_removed": n,
                      "removal": "callback $A0C6: +$3F bit 6 -> clear token and $FF; bit 7 -> $FE (respawn tracking); neither (the boss leaves parameter 0) -> $FF",
                      "sound": "$AB is requested only by state 3 (monitor path); the boss path (state 1) requests none"}
    return out


# --------------------------------------------------------------------------- #
# THZ3 whole-game helpers (update-aligned)
# --------------------------------------------------------------------------- #
class Thz3:
    """THZ3 booted through tools/object_50.py's patched new-game path; all driving is applied at update boundaries."""

    def __init__(self, rom: bytes, cam=(1500, 80), player=(1604, 238)):
        def hook(mach):
            mach.w16(0xD2D6, cam[0]); mach.w16(0xD2D8, cam[1]); mach.w16(0xD511, player[0]); mach.w16(0xD514, player[1])
        self.rom = rom
        self.s = o50._boot(rom, hook)
        self.m = self.s.mem
        self.u = self.s.u16
        self.emu = psc.Emu.__new__(psc.Emu)
        self.emu.s, self.emu.rom, self.emu.act = self.s, rom, "thz3"
        self.base_frame = self.s.frame
        self.al = Aligned(self.emu)

    def boss(self):
        return o50._boss_base(self.s)

    def sample_boss(self) -> dict:
        s, m, u = self.s, self.m, self.u
        b = self.boss()
        r = {"cam_x": u(0xD174), "cam_y": u(0xD176), "left_limit_D280": u(0xD280), "right_limit_D282": u(0xD282), "bottom_limit_D27E": u(0xD27E),
             "scroll_D15E": m[0xD15E], "scroll_D15F": m[0xD15F], "pan_target": [u(0xD2DA), u(0xD2DC)], "player": [u(0xD511), u(0xD514)], "rings": m[0xD29A],
             "player_state_D501": m[0xD501], "d293": m[0xD293], "zone_act": [m[0xD297], m[0xD298]]}
        if b:
            r.update(boss=[u(b + 0x11), u(b + 0x14)], boss_state=m[b + 1], boss_requested=m[b + 2], boss_health=m[b + 0x26], boss_phase_32=m[b + 0x32],
                     boss_vx=s16(u(b + 0x16)), boss_screen_x=u(b + 0x1A), boss_cooldown_1E=m[b + 0x1E], boss_reaction_1F=m[b + 0x1F], boss_flags_04=m[b + 4])
        else:
            r.update(boss=None, boss_state=None, boss_requested=None, boss_health=None, boss_phase_32=None, boss_vx=None, boss_screen_x=None, boss_cooldown_1E=None,
                     boss_reaction_1F=None, boss_flags_04=None)
        return r

    def run(self, driver, updates, pad=0, stop=None):
        return self.al.run(driver, self.sample_boss, updates, pad=pad, stop=stop, restore=False)


def _events(rows: list, keys: tuple) -> list:
    out, last = [], None
    for i, r in enumerate(rows):
        k = tuple(r.get(x) for x in keys)
        if k != last:
            out.append({"update": i, **{x: r.get(x) for x in keys}})
            last = k
    return out


def arena_camera(rom: bytes) -> dict:
    out = {"evidence": "EMULATED ORIGINAL FRAME (THZ3 booted with the new-game init patched to act index 2; update-aligned; player rings 99 so contact does not end the run) + CONTROLLED ROUTINE RESULT + SOURCE-TRACED BEHAVIOR",
           "harness_note": HARNESS_NOTE,
           "method": "player starts at (1604,238) with the camera at X 1500 and runs right (BTN_RIGHT held for 75 updates); the boss contact is switched off (+$03 bit 6) in the measurement runs so the camera/clamp facts are isolated from the fight"}
    t = Thz3(rom)
    s, m = t.s, t.m
    m[0xD29A] = 0x99

    def drv(c):
        b = t.boss()
        if b:
            m[b + 3] |= 0x40
    rows = t.run(drv, 1500, pad=lambda f: psc.PAD["RIGHT"] if f < 75 else (psc.PAD["RIGHT"] if 520 <= f < 800 else (psc.PAD["LEFT"] if f >= 800 else 0)))
    first = next(i for i, r in enumerate(rows) if r["boss"] is not None)
    ev = _events(rows, ("boss_state", "boss_phase_32"))
    ev = [e for e in ev if e["boss_state"] is not None]
    lim = _events(rows, ("left_limit_D280", "right_limit_D282", "bottom_limit_D27E"))
    out["timeline"] = {
        "created_at_update": first, "creation_row": {k: rows[first][k] for k in ("cam_x", "cam_y", "boss", "boss_state", "player")},
        "boss_screen_x_at_creation": rows[first]["boss"][0] - rows[first]["cam_x"],
        "boss_state_events_[update_since_creation,state,phase]": [[e["update"] - first, e["boss_state"], e["boss_phase_32"]] for e in ev[:14]],
        "limit_events_first_8": [[e["update"] - first, e["left_limit_D280"], e["right_limit_D282"], e["bottom_limit_D27E"]] for e in lim[:8]],
    }
    st1 = next(i for i, r in enumerate(rows) if r["boss_state"] == 1)
    st2 = next(i for i, r in enumerate(rows) if r["boss_state"] == 2)
    st3 = next(i for i, r in enumerate(rows) if r["boss_state"] == 3)
    out["timeline"]["state_1_at"] = st1 - first
    out["timeline"]["trigger_state_2_at"] = st2 - first
    out["timeline"]["trigger_row"] = {k: rows[st2][k] for k in ("cam_x", "left_limit_D280", "right_limit_D282", "player", "boss")}
    out["timeline"]["state_3_at"] = st3 - first
    out["timeline"]["state_3_row"] = {k: rows[st3][k] for k in ("cam_x", "cam_y", "left_limit_D280", "right_limit_D282", "bottom_limit_D27E", "scroll_D15E", "scroll_D15F", "pan_target")}
    # left limit follows the camera every update before the trigger
    follow = [(r["cam_x"], r["left_limit_D280"]) for r in rows[st1:st2]]
    out["timeline"]["left_limit_minus_camera_while_state_1"] = sorted({a - b for a, b in follow})
    # state 2: boss child $12 wait (the HUD slide-away)
    out["timeline"]["state_2_duration_updates"] = st3 - st2
    # pan
    pan = [(i, r["cam_x"], r["cam_y"]) for i, r in enumerate(rows[st3 - 2:st3 + 120], st3 - 2)]
    xs = [p[1] for p in pan]
    ys = [p[2] for p in pan]
    x_end, y_end = xs[-1], ys[-1]
    x_done = next(i for i, p in enumerate(pan) if p[1] == x_end) + pan[0][0]
    y_done = next(i for i, p in enumerate(pan) if p[2] == y_end) + pan[0][0]
    out["pan"] = {"target_D2DA_D2DC": rows[st3]["pan_target"], "x_start": xs[2], "y_start": ys[2], "x_end": x_end, "y_end": y_end,
                  "x_step_per_update": sorted({b - a for a, b in zip(xs[2:30], xs[3:31]) if b != a}), "y_step_per_update": sorted({b - a for a, b in zip(ys[2:30], ys[3:31]) if b != a}),
                  "updates_from_state_3_until_x_final": x_done - st3, "updates_from_state_3_until_y_final": y_done - st3,
                  "note": "both axes move 1 px per update toward the target; the X limit is exclusive so X ends 1 px short of the target (1679 for 1680)"}
    # boss entry
    s18 = next(i for i, r in enumerate(rows) if r["boss_state"] == 18)
    s6 = next(i for i, r in enumerate(rows) if r["boss_state"] == 6)
    out["boss_entry"] = {"state_18_at": s18 - first, "state_6_at": s6 - first, "boss_x_at_18": rows[s18]["boss"], "boss_x_at_6": rows[s6]["boss"], "screen_x_at_6": rows[s6]["boss_screen_x"],
                         "camera_at_6": [rows[s6]["cam_x"], rows[s6]["cam_y"]], "entry_vx": rows[s18]["boss_vx"]}
    # player clamp
    right_pos = [r["player"][0] for r in rows[540:800]]
    left_pos = [r["player"][0] for r in rows[1000:1400]] if len(rows) > 1400 else [r["player"][0] for r in rows[-300:]]
    cam = rows[700]["cam_x"]
    out["player_clamp"] = {"camera_x": cam, "max_player_x_running_right": max(right_pos), "min_player_x_running_left": min(left_pos),
                           "max_minus_camera": max(right_pos) - cam, "min_minus_camera": min(left_pos) - cam,
                           "rule": "the original player edge clamp EDGE(LEFT,+16)..EDGE(RIGHT,-9) (camera+16 .. camera+247, +-1 from the sub-pixel/low-byte quirks) confines Sonic to world X ~1695..1927 while the camera is locked at 1679; THZ3 has NO terrain wall there (floor row 8 is flat from X 1600 to 2560), so the camera and this clamp are the only arena boundary"}
    out["arena_terrain"] = {"floor_row": 8, "floor_world_y": 256, "ground_anchor_y": 238, "flat_floor_columns": [50, 79], "walls": "none",
                            "evidence": "DECODED DATA (levels/thz3/layout.json rows 8..15 are solid block rows 0x01/0x0A/0x0B from column 50 to 79; rows 0..7 empty)"}
    out["final_lock"] = {"camera": [rows[700]["cam_x"], rows[700]["cam_y"]], "left_limit_D280": rows[700]["left_limit_D280"], "right_limit_D282": rows[700]["right_limit_D282"],
                         "bottom_limit_D27E": rows[700]["bottom_limit_D27E"], "scroll_D15E_D15F": [rows[700]["scroll_D15E"], rows[700]["scroll_D15F"]],
                         "boss_patrol_x_range": [min(r["boss"][0] for r in rows[300:1300] if r["boss"] and r["boss_state"] in (6, 9, 12, 15)),
                                                 max(r["boss"][0] for r in rows[300:1300] if r["boss"] and r["boss_state"] in (6, 9, 12, 15))]}
    return out


def trigger_boundaries(rom: bytes) -> dict:
    """Controlled: state 1 trigger |dx| < 160 and |dy| < 256 (player anchor minus boss anchor), both signs, +-1 around each edge, plus the creation window."""
    out = {"evidence": "CONTROLLED ROUTINE RESULT (real state-1 callback $9771 and creation loop $8000)"}
    rows = []
    for dx in (-161, -160, -159, 159, 160, 161):
        for dy in (0, 255, 256, -255, -256, 257):
            g = o50.Fixture(rom); g.create(); g.step(); g.step()
            g.o.position(g.r(0x11, 2) + dx, g.r(0x14, 2) + dy)
            g.o.word(0xD174, 1600)
            g.o.word(0xD282, 2304)
            g.step()
            rows.append({"dx": dx, "dy": dy, "triggered": g.r(2) == 2, "right_limit_D282_after": g.o.word(0xD282)})
    out["state_1_trigger"] = {"rows": rows, "triggered_iff": "|dx| < 160 and |dy| < 256 (strict; dx, dy are player anchor minus boss anchor; zone 0 row of the table at $97A1 = (160, 256))",
                              "mismatches_vs_rule": sum(1 for r in rows if r["triggered"] != (abs(r["dx"]) < 160 and abs(r["dy"]) < 256))}
    win = []
    for cam in range(1560, 1680):
        g = o50.Fixture(rom)
        g.o.bank(2, 0x1C); g.m[0xD12B] = 0x1C
        g.m[0xD400:0xD440] = bytes(0x40)
        g.m[0xD700:0xD9C0] = bytes(0x2C0)
        g.o.word(0xD174, cam); g.o.word(0xD176, 80); g.m[0xD440] = 1
        g.o.call(0x8000)
        win.append([cam, g.m[0xD400] == 0x50])
    made = [c for c, ok in win if ok]
    out["creation_window_steady_scroll_camera_x"] = {"created_camera_x_every_pixel_1560_1679": made, "first": made[0], "last": made[-1],
                                                      "boss_screen_x_range": [1936 - made[-1], 1936 - made[0]],
                                                      "rule": "cell 2 only while scrolling: 288 <= bossX - cameraX < 352, i.e. EDGE(RIGHT, +32 .. +95) (every camera X 1560..1679 swept); the initial fill ($D440 = 0) would also create it in cells 0/1"}
    return out


# --------------------------------------------------------------------------- #
# B4 boss contact grid
# --------------------------------------------------------------------------- #
class BossLab(o50.Fixture):
    """The real boss slot after state 3 (health 8, +$03 bit 7) with a RAM snapshot so thousands of cases run quickly."""

    CRUISE = {6: -128, 9: -6, 12: 128, 15: 6, 18: -128}

    def __init__(self, rom: bytes):
        super().__init__(rom)
        self.create(); self.step(); self.force_state(3); self.step()
        self.snap = bytes(self.m[0xC000:0xE000])

    def case(self, state, dx, dy, d503, d522=0, d532=0, health=8, cooldown=0, vy=0x100, vx=0, ex=8, ey=24, reaction=0):
        self.m[0xC000:0xE000] = self.snap
        self.force_state(state)
        self.w(0x26, health); self.w(0x1E, cooldown); self.w(0x32, 0); self.w(0x1F, reaction)
        self.w(0x16, self.CRUISE.get(state, 0) & 0xFFFF, 2)
        if state == 18:
            self.w(0x10, 0x80)           # state 18 moves BEFORE its contact test: with sub-pixel $80 the -0.5 px step leaves the integer X unchanged
        bx, by = self.r(0x11, 2), self.r(0x14, 2)
        self.o.word(0xD174, bx - 250)
        self.o.position(bx + dx, by + dy)
        m = self.m
        m[0xD503], m[0xD522], m[0xD532] = d503, d522, d532
        m[0xD52C], m[0xD52D] = ex, ey
        self.o.word(0xD516, vx & 0xFFFF); self.o.word(0xD518, vy & 0xFFFF)
        m[0xD3B0] = 0; m[0xD502] = 0; m[0xDE04] = 0; m[0xD452] = 0; m[0xD448] = 0xEE
        self.call_bank(0x00, 0x3FC8)
        self.step()
        px, py = self.o.word(0xD511), self.o.word(0xD514)
        return {"requested": self.r(2), "health": self.r(0x26), "cooldown_1E": self.r(0x1E), "contact_bits": self.r(0x21) & 15, "damage_request": m[0xD3B0] == 0xFF,
                "player_requested_state": m[0xD502], "player_vx": s16(self.o.word(0xD516)), "player_vy": s16(self.o.word(0xD518)), "player_dx_after": px - (bx + dx),
                "player_dy_after": py - (by + dy), "sound": m[0xDE04], "flash": m[0xD452], "d448": m[0xD448]}


POSTURES = {
    "walker_grounded": dict(d503=0x00, d522=2, d532=0),
    "walker_airborne": dict(d503=0x01, d522=0, d532=0),
    "attacker_ball_grounded": dict(d503=0x02, d522=2, d532=0),
    "attacker_jump_airborne": dict(d503=0x03, d522=0, d532=0),
    "invincible_pickup_state": dict(d503=0x83, d522=0, d532=6),
    "invincible_after_landing_bit1_clear": dict(d503=0x80, d522=2, d532=6),
    "invulnerable_blink_non_attacking": dict(d503=0x80, d522=2, d532=0),
    "hurt_state_bit6_with_bit1": dict(d503=0x42, d522=0, d532=0),
    "hurt_state_bit6_without_bit1": dict(d503=0x40, d522=0, d532=0),
}


def boss_model(state, c, attack, cooldown, vy, health):
    """Expected outcome from the shared overlap helper's contact code (1 above, 2 below, 4 right, 8 left; 0 none) and $99AE's order."""
    if state == 18:
        if c == 0 or cooldown:
            return "none"
        return "knockback_no_health" if attack else "player_damage_request"
    if cooldown:
        return "none"
    if c == 0:
        return "none"
    if c == 1:
        return "top_bounce" if vy >= 0 else "top_contact_no_rebound"
    if attack:
        return "final_hit" if health == 1 else "hit"
    return "player_damage_request"


def boss_outcome(r: dict, state: int, health: int) -> str:
    if r["contact_bits"] == 0 and not r["damage_request"] and r["health"] == health and r["requested"] == state:
        return "none"
    if state == 18:
        return "player_damage_request" if r["damage_request"] else "knockback_no_health"
    if r["health"] < health:
        return "final_hit" if r["requested"] == 4 else "hit"
    if r["damage_request"]:
        return "player_damage_request"
    if r["requested"] == state + 1:
        return "top_bounce" if r["player_requested_state"] == 0x0B else "top_contact_no_rebound"
    return "none" if r["cooldown_1E"] == 0 and r["contact_bits"] == 0 else "contact_other"


def boss_contact_grid(rom: bytes) -> dict:
    out = {"evidence": "CONTROLLED ROUTINE RESULT (real boss callbacks; $6328 minimum-penetration contact, $5FA0 solid push, $99AE / $814D)"}
    lab = BossLab(rom)
    dxs, dys = range(-34, 35), range(-52, 29)
    summary, edges, total, mism = {}, {}, 0, 0
    first_bad = []
    for pname, pk in POSTURES.items():
        counts, per_row = {}, {}
        for dy in dys:
            for dx in dxs:
                r = lab.case(6, dx, dy, **pk)
                got = boss_outcome(r, 6, 8)
                c = psc.model_contact(dx, dy, 8, 24, 20, 48)
                want = boss_model(6, c, bool(pk["d503"] & 2), 0, 0x100, 8)
                total += 1
                if got != want:
                    mism += 1
                    if len(first_bad) < 6:
                        first_bad.append([pname, dx, dy, got, want])
                counts[got] = counts.get(got, 0) + 1
                per_row.setdefault(dy, {}).setdefault(got, []).append(dx)
        summary[pname] = dict(sorted(counts.items()))
        edges[pname] = {str(dy): {k: [min(v), max(v)] for k, v in rows.items() if k != "none"} for dy, rows in per_row.items() if dy in (-48, -47, -24, -1, 0, 1, 12, 24, 25)}
    out["cases"] = total
    out["mismatches_vs_model"] = mism
    out["first_mismatches"] = first_bad
    out["geometry"] = {"boss_extents_x_y": [20, 48], "player_extents_x_y": [8, 24], "dx_range": [-34, 34], "dy_range": [-52, 28],
                       "box": "contact iff |dx| <= 28 and -48 <= dy <= 24 (dy = playerY - bossY, both anchors, boss anchor after any movement of that update: states 6/9/12/15 test before $0338, state 18 moves first); the minimum-penetration axis decides top/below versus left/right",
                       "top_contact": "dy -48..-1 with vertical penetration (48-|dy|) <= horizontal (28-|dx|) -> bit 0 'player above' (a triangle-free diamond: |dx| <= 28 - ... see edges)",
                       "below_contact": "dy 0..24 with vertical penetration 24-dy <= 28-|dx|"}
    out["outcome_counts_by_posture_state_6"] = summary
    out["edges_by_posture_[min_dx,max_dx]_per_selected_dy"] = edges
    # +-1 around the first/last contact column and row for the attacker posture, each state
    edge_rows = []
    for state in (6, 9, 12, 15, 18):
        for dx, dy in ((28, 0), (29, 0), (-28, 0), (-29, 0), (0, 24), (0, 25), (0, -48), (0, -49), (0, -1), (0, 0), (27, -47), (28, -47), (1, 23), (27, 1)):
            for pname in ("attacker_ball_grounded", "walker_grounded"):
                r = lab.case(state, dx, dy, **POSTURES[pname])
                edge_rows.append({"state": state, "dx": dx, "dy": dy, "posture": pname, "outcome": boss_outcome(r, state, 8), "contact_bits": r["contact_bits"]})
    out["edge_rows"] = edge_rows
    # per-state equality of the contact matrix (6, 9, 12, 15 identical; 18 smaller helper)
    same = True
    for pname in ("attacker_ball_grounded", "walker_grounded", "invincible_after_landing_bit1_clear"):
        for dy in range(-52, 29, 4):
            for dx in range(-34, 35, 3):
                ref = boss_outcome(lab.case(6, dx, dy, **POSTURES[pname]), 6, 8)
                for st in (9, 12, 15):
                    if boss_outcome(lab.case(st, dx, dy, **POSTURES[pname]), st, 8) != ref:
                        same = False
    out["states_6_9_12_15_identical_outcomes"] = same
    s18 = {}
    for pname in ("attacker_ball_grounded", "walker_grounded"):
        cnt = {}
        for dy in range(-52, 29):
            for dx in range(-34, 35):
                r = lab.case(18, dx, dy, **POSTURES[pname])
                k = boss_outcome(r, 18, 8)
                want = boss_model(18, psc.model_contact(dx, dy, 8, 24, 20, 48), bool(POSTURES[pname]["d503"] & 2), 0, 0x100, 8)
                cnt[k] = cnt.get(k, 0) + 1
                if k != want:
                    mism += 1
                total += 1
        s18[pname] = dict(sorted(cnt.items()))
    out["state_18_outcome_counts"] = s18
    out["mismatches_vs_model"] = mism
    out["cases"] = total
    # results of each outcome class (fields written)
    eff = {}
    for name, (dx, dy, pk, st, hp, cd, vy) in {
        "hit_from_left_side": (-26, 0, "attacker_ball_grounded", 6, 8, 0, 0x100),
        "hit_from_right_side": (26, 0, "attacker_ball_grounded", 6, 8, 0, 0x100),
        "hit_from_below": (0, 10, "attacker_ball_grounded", 6, 8, 0, 0x100),
        "top_bounce": (0, -40, "attacker_jump_airborne", 6, 8, 0, 0x100),
        "top_bounce_player_rising": (0, -40, "attacker_jump_airborne", 6, 8, 0, 0xFE00),
        "top_contact_plain": (0, -40, "walker_airborne", 6, 8, 0, 0x100),
        "plain_side_contact": (-26, 0, "walker_grounded", 6, 8, 0, 0x100),
        "final_hit": (-26, 0, "attacker_ball_grounded", 6, 1, 0, 0x100),
        "contact_in_cooldown": (-26, 0, "walker_grounded", 6, 8, 2, 0x100),
        "invincible_walker_side": (-26, 0, "invincible_after_landing_bit1_clear", 6, 8, 0, 0x100),
        "invincible_pickup_state_side": (-26, 0, "invincible_pickup_state", 6, 8, 0, 0x100),
        "hurt_state_with_bit1_side": (-26, 0, "hurt_state_bit6_with_bit1", 6, 8, 0, 0x100),
    }.items():
        r = lab.case(st, dx, dy, health=hp, cooldown=cd, vy=vy, **POSTURES[pk])
        eff[name] = {"posture": pk, **r}
    out["effects"] = eff
    # invulnerability timeline of the boss: reaction state 20 updates + 2 update cooldown
    out["invulnerability_rule"] = ("after a hit the boss is in reaction state S+2 for +$1F = 20 updates (no overlap routine runs) and returns to the patrol state; the 2-update cooldown +$1E "
                                   "is set only by a harmful (non-attack, non-top) contact: so the earliest next hit is 22 updates after the first one (emulated frames 201, 223, ...)")
    return out


# --------------------------------------------------------------------------- #
# B5/B6/B7 full fight, defeat and act-clear chain (emulated)
# --------------------------------------------------------------------------- #
PC_MARKS = {
    0x83ED: "state_20_handler_sets_D293_bit4_or_5", 0x1543: "main_loop_zone_clear_1543", 0x1594: "zone_clear_results_branch_check", 0x159B: "call_32F9_results_screen",
    0x33E2: "results_call_2D55", 0x33E5: "results_call_2D08_ring_and_time_tally", 0x2D28: "tally_time_bonus_phase_2D28", 0x2D54: "tally_done_2D54",
    0x15CE: "zone_clear_advance_15CE", 0x15DE: "level_load_requested_15DE", 0x15E8: "game_complete_branch_15E8", 0x4892: "player_state_20_request_4892",
}


def _hud_rows(m) -> list:
    return [m[0xDB34], m[0xDB38], m[0xDB3C]]


def defeat_chain(rom: bytes, hostile_after_defeat: bool = False, rings_bcd: int = 0x47, png_dir: Path | None = None) -> dict:
    t = Thz3(rom)
    s, m, u = t.s, t.m, t.u
    m[0xD29A] = rings_bcd                  # BCD ring count: the tally has something to count and one stray hit does not end the run
    sound = o50._sound_logger(s)
    marks = {}
    hits_2d08 = []

    def mark(name):
        def f(mach):
            if name.startswith("state_20_handler") and mach.slot[2] != 0x0C:
                return                                  # $83ED exists in other banks too; the player state-$20 handler lives in bank $0C
            marks.setdefault(name, mach.frame)
            if name == "results_call_2D08_ring_and_time_tally":
                marks["rings_at_tally_start"] = m[0xD29A]
        return f
    for addr, name in PC_MARKS.items():
        s.add_pc_hook(addr, mark(name))
    state = {"conv": None, "seen5": False}

    def park(x, y):
        s.w16(0xD511, x); s.w16(0xD514, y); s.w16(0xD516, 0); s.w16(0xD518, 0)
        m[0xD503] &= 0xFC

    def driver(c):
        b = t.boss()
        if state["conv"] is not None:
            return
        if b is None:
            if state["seen5"]:
                state["conv"] = c
            return
        st = m[b + 1]
        bx, by = u(b + 0x11), u(b + 0x14)
        if st == 5:
            state["seen5"] = True
            park(1800, 238)
        elif st in (6, 9, 12, 15) and m[b + 0x1E] == 0 and m[b + 0x1F] == 0 and c > 260:
            s.w16(0xD511, bx - 20); s.w16(0xD514, by); s.w16(0xD516, 0); s.w16(0xD518, 0)
            m[0xD503] = (m[0xD503] | 2) & ~0x41
        elif st == 4:
            park(1760, 238)
        elif st in (3, 18, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17):
            park(1696, 238)

    def sample():
        b = t.boss()
        kids = []
        for i in range(19):
            a = 0xD540 + i * 0x40
            if m[a] and a != b:
                kids.append([h(a), m[a], u(a + 0x11), u(a + 0x14), m[a + 1], m[a + 6], m[a + 0x3F]])
        base = t.sample_boss()
        base.update(kids=kids, hud=_hud_rows(m), d2a6=u(0xD2A6), d299=m[0xD299], score=[m[0xD29D], m[0xD29E], m[0xD29F]], timer_run_D2BE=m[0xD2BE],
                    time_bcd=[m[0xD2BF], m[0xD2C0]], slot_d700_type=m[0xD700], player_req=m[0xD502], player_flags_D503=m[0xD503], player_d522=m[0xD522],
                    occupancy_D400=m[0xD400], zone=m[0xD297], act=m[0xD298], frame=s.frame)
        return base

    def pad(f):
        if state["conv"] is None:
            return psc.PAD["RIGHT"] if f < 75 else 0
        return (psc.PAD["LEFT"] | psc.PAD["B1"]) if hostile_after_defeat and f % 7 < 5 else 0

    rows = t.al.run(driver, sample, 4200, pad=pad, restore=False, stop=lambda r: len(r) > 100 and r[-1]["zone"] != 0)
    conv = next((i for i, r in enumerate(rows) if r["slot_d700_type"] == 0x0F), None)
    created = next(i for i, r in enumerate(rows) if r["boss_state"] is not None)
    chain = {"variant": {"hostile_input_after_defeat": hostile_after_defeat, "rings_bcd": h(rings_bcd, 2)},
             "evidence": "EMULATED ORIGINAL FRAME (THZ3, update-aligned; the attacker is teleported 20 px left of the boss with $D503 bit 1 whenever a patrol state is ready, +$1E = +$1F = 0; "
                         "between attacks Sonic is parked at X 1696; during state 5 he is parked on the floor at X 1800; after the slot converts nothing is written"}
    chain["updates_total"] = len(rows)
    chain["created_at_update"] = created
    # health timeline
    hp = _events(rows[created:], ("boss_health", "boss_state"))
    chain["hit_events_[update_since_creation,state,health]"] = [[e["update"], e["boss_state"], e["boss_health"]] for e in hp if e["boss_state"] is not None][:60]
    hits = [i for i in range(created + 1, len(rows)) if rows[i]["boss_health"] is not None and rows[i - 1]["boss_health"] is not None
            and rows[i]["boss_health"] < rows[i - 1]["boss_health"] and rows[i - 1]["boss_health"] <= 8]
    chain["hit_updates_since_creation"] = [i - created for i in hits]
    chain["hit_intervals"] = [b - a for a, b in zip(hits, hits[1:])]
    chain["rings_after_hits"] = [rows[i]["rings"] for i in hits]
    if conv is None:
        chain["error"] = "boss never converted"
        return chain
    st4 = next(i for i, r in enumerate(rows) if r["boss_state"] == 4)
    st5 = next((i for i, r in enumerate(rows) if r["boss_state"] == 5), None)
    chain["final_hit_update"] = hits[7] - created if len(hits) >= 8 else None
    chain["state_4_at"] = st4 - created
    chain["state_5_seen_in_an_update_sample"] = st5 is not None
    chain["conversion_at"] = conv - created
    chain["state_4_to_conversion_updates"] = conv - st4
    # state 4 children
    k4 = []
    seen = set()
    for i in range(st4, conv + 400):
        if i >= len(rows):
            break
        for k in rows[i]["kids"]:
            key = (k[0], k[1])
            if key not in seen:
                seen.add(key)
                k4.append({"update_since_state_4": i - st4, "slot": k[0], "type": h(k[1], 2), "x": k[2], "y": k[3], "parameter_3F": k[6]})
    chain["children_seen_from_state_4"] = k4
    boss_xy = rows[st4]["boss"]
    chain["boss_anchor_at_state_4"] = boss_xy
    chain["child_offsets_from_boss_anchor"] = [{"type": c["type"], "dx": c["x"] - boss_xy[0], "dy": c["y"] - boss_xy[1], "update": c["update_since_state_4"]} for c in k4 if c["type"] in ("0x34",)]
    # lifetimes of 34/0A/0F children (per slot: first update seen until its type changes or the slot empties)
    life = {}
    for typ in (0x34, 0x0A, 0x0F):
        spans = []
        cur = {}
        for i in range(st4, len(rows)):
            present = {}
            for k in rows[i]["kids"]:
                if k[1] == typ:
                    present[k[0]] = k
            for slot in list(cur):
                if slot not in present:
                    spans.append([slot, cur.pop(slot), i - st4])
            for slot in present:
                cur.setdefault(slot, i - st4)
        for slot, first in cur.items():
            spans.append([slot, first, None])
        life[h(typ, 2)] = [[sp[1], None if sp[2] is None else sp[2] - sp[1]] for sp in sorted(spans, key=lambda q: q[1])][:14]
    chain["child_spans_[first_update_since_state_4,updates_alive_or_null_if_alive_at_end_of_sampling]"] = life
    # slot conversion
    chain["conversion_row"] = {k: rows[conv][k] for k in ("slot_d700_type", "player_req", "left_limit_D280", "right_limit_D282", "scroll_D15E", "scroll_D15F", "cam_x", "cam_y", "occupancy_D400", "d2a6", "timer_run_D2BE", "time_bcd", "rings")}
    chain["row_before_conversion"] = {k: rows[conv - 1][k] for k in ("slot_d700_type", "player_req", "left_limit_D280", "right_limit_D282", "scroll_D15E", "scroll_D15F", "cam_x", "cam_y", "player", "player_d522", "boss_state")}
    # player state $20 and flag
    p20 = next((i for i, r in enumerate(rows) if r["player_state_D501"] == 0x20), None)
    chain["player_state_20_first_update_since_conversion"] = None if p20 is None else p20 - conv
    flag_frame = marks.get("state_20_handler_sets_D293_bit4_or_5")
    conv_frame = rows[conv]["frame"]
    chain["conversion_frame_since_creation"] = conv_frame - rows[created]["frame"]
    chain["act_clear_flag_set_frames_after_conversion"] = None if flag_frame is None else flag_frame - conv_frame
    chain["d293_changes_[frames_since_conversion,value]"] = [[e["frame"] - conv_frame, e["d293"]] for e in _events(rows[conv:], ("d293", "frame")) if True][:0] or [[r["frame"] - conv_frame, r["d293"]] for i, r in enumerate(rows[conv:], conv) if i == conv or r["d293"] != rows[i - 1]["d293"]]
    fl_row = next((r for r in rows if r["frame"] >= (flag_frame or 0) and r["frame"] > conv_frame), None)
    chain["player_at_last_gameplay_update_before_flag"] = None
    pre = [r for r in rows[conv:] if flag_frame is None or r["frame"] <= flag_frame]
    chain["player_and_camera_at_flag"] = {"player_x": pre[-1]["player"][0], "cam_x": pre[-1]["cam_x"], "difference": pre[-1]["player"][0] - pre[-1]["cam_x"], "threshold_playerX_minus_cameraX_gt": 0x120}
    p20 = next((r for r in rows if r["player_state_D501"] == 0x20), None)
    chain["player_state_20_frames_after_conversion"] = None if p20 is None else p20["frame"] - conv_frame
    chain["camera_after_release_[frames_since_conversion,cam_x,D280,D282]"] = [[r["frame"] - conv_frame, r["cam_x"], r["left_limit_D280"], r["right_limit_D282"]] for i, r in enumerate(rows[conv:], conv) if i == conv or (r["left_limit_D280"], r["right_limit_D282"]) != (rows[i - 1]["left_limit_D280"], rows[i - 1]["right_limit_D282"])][:8]
    chain["main_loop_marks_frames_after_flag"] = {k: (v - flag_frame if flag_frame is not None else None) for k, v in marks.items() if isinstance(v, int) and k != "rings_at_tally_start"}
    chain["main_loop_marks_frames_after_conversion"] = {k: v - conv_frame for k, v in marks.items() if isinstance(v, int) and k != "rings_at_tally_start"}
    nxt = next((r for i, r in enumerate(rows) if r["zone"] != 0 and i > conv), None)
    chain["next_zone_loaded_frames_after_conversion"] = None if nxt is None else nxt["frame"] - conv_frame
    chain["next_zone_act"] = None if nxt is None else [nxt["zone"], nxt["act"]]
    chain["d293_at_next_zone"] = None if nxt is None else nxt["d293"]
    # bonus / tally
    chain["d2a6_changes_[frames_since_conversion,value]"] = [[r["frame"] - conv_frame, r["d2a6"]] for i, r in enumerate(rows[conv:], conv) if i == conv or r["d2a6"] != rows[i - 1]["d2a6"]][:8]
    chain["d2a6_formula_check"] = {"rings_bcd": h(rings_bcd, 2), "expected_H_from_time_table_and_L_rings_minus_0x11": "see support_controlled.type_0a.param_0_init"}
    chain["score_before_and_after_the_sequence"] = [rows[conv]["score"], rows[-1]["score"]]
    chain["rings_at_conversion_and_at_next_zone"] = [rows[conv]["rings"], rows[-1]["rings"]]
    chain["rings_at_tally_start"] = marks.get("rings_at_tally_start")
    chain["timer_run_flag_D2BE_values_seen"] = sorted({r["timer_run_D2BE"] for r in rows[conv:]})
    chain["time_bcd_at_conversion"] = rows[conv]["time_bcd"]
    chain["time_bcd_at_next_zone"] = rows[-1]["time_bcd"]
    # HUD
    chain["hud_rows_DB34_DB38_DB3C_events_first_10_[update_since_creation,...]"] = [[e["update"] - created, *e["hud"]] for e in _events(rows[created:], ("hud",))][:6] + ["..."]
    chain["hud_rows_at"] = {"after_slide_away_(creation+105)": rows[created + 105]["hud"], "at_state_4": rows[st4]["hud"], "at_conversion": rows[conv]["hud"], "at_end": rows[-1]["hud"]}
    chain["sound_requests_[frame_since_creation,value]"] = [[fr - rows[created]["frame"], v] for fr, v in _dedupe(sound, 0, created)]
    chain["player_states_after_conversion_[frames_since_conversion,D501]"] = [[r["frame"] - conv_frame, r["player_state_D501"]] for i, r in enumerate(rows[conv:], conv) if i == conv or r["player_state_D501"] != rows[i - 1]["player_state_D501"]][:14]
    if png_dir is not None:
        png_dir.mkdir(parents=True, exist_ok=True)
    return chain


def _dedupe(log, base, created):
    out, prev = [], None
    for fr, v in log:
        if v != prev:
            out.append([fr - base, v])
        prev = v
    return out


def _bcd(v: int) -> int:
    return (v >> 4) * 10 + (v & 15)


def defeat_variants(rom: bytes) -> dict:
    out = {"evidence": "EMULATED ORIGINAL FRAME (same driver as defeat_chain, different ring counts / held buttons after the slot converts)"}
    rows = []
    for name, kw in (("rings_00", dict(rings_bcd=0x00)), ("rings_10", dict(rings_bcd=0x10)), ("rings_47", dict(rings_bcd=0x47)), ("rings_99", dict(rings_bcd=0x99)),
                     ("rings_47_buttons_held_after_defeat", dict(rings_bcd=0x47, hostile_after_defeat=True))):
        c = defeat_chain(rom, **kw)
        marks = c["main_loop_marks_frames_after_flag"]
        sc = c["score_before_and_after_the_sequence"][1]
        score = _bcd(sc[0]) + 100 * _bcd(sc[1]) + 10000 * _bcd(sc[2])
        d2a6 = c["d2a6_changes_[frames_since_conversion,value]"][1][1] if len(c["d2a6_changes_[frames_since_conversion,value]"]) > 1 else None
        rows.append({"variant": name, "rings_bcd": h(kw["rings_bcd"], 2), "rings_decimal": _bcd(kw["rings_bcd"]), "d2a6_after_conversion": d2a6,
                     "d2a6_steps": None if d2a6 is None else (d2a6 >> 8 & 0xFF) // 16 * 1000 + ((d2a6 >> 8) & 15) * 100 + _bcd(d2a6 & 0xFF),
                     "flag_after_conversion_frames": c["act_clear_flag_set_frames_after_conversion"], "marks_frames_after_flag": marks,
                     "next_zone_after_conversion_frames": c["next_zone_loaded_frames_after_conversion"], "score_after": score,
                     "player_and_camera_at_flag": c["player_and_camera_at_flag"], "player_states": c["player_states_after_conversion_[frames_since_conversion,D501]"]})
    out["rows"] = rows
    r0, r47, r99 = rows[0], rows[2], rows[3]
    out["analysis"] = {
        "score_per_ring_units": (r47["score_after"] - r0["score_after"]) / max(1, r47["rings_decimal"] - r0["rings_decimal"]) if r47["rings_decimal"] != r0["rings_decimal"] else None,
        "tally_frames_per_ring": None,
    }
    return out


# --------------------------------------------------------------------------- #
# B1 reconciliation, B5 phase model, B8 assets
# --------------------------------------------------------------------------- #
def reconciliation(rom: bytes) -> dict:
    cache = json.loads((ROOT / "data/rom-cache/thz3/object-50.json").read_text(encoding="utf-8"))
    return {
        "evidence": "DECODED DATA (docs/object-50.md and data/rom-cache/thz3/object-50.json re-read; nothing re-derived that was already proven)",
        "object_50_cache_sections_reused": sorted(cache.keys()),
        "already_proven_and_retained": [
            "identity: one object is arena controller and fighter; single placement THZ3 record 1 of 10 at world (1936,238), flags/param/aux 0",
            "creation, occupancy byte $D400 = $50, keep-alive bit 1, no respawn after the defeat path zeroes the token",
            "19 states, all callbacks/scripts, all transitions executed; patrol cycle 721 updates; speeds -128/+128 (-130 after a turn) per 256",
            "8 hit points, decrement only through $99AE attack contact, reaction states 20 updates, earliest next hit 22 updates later",
            "contact helper geometry 20 x 48 against Sonic 8 x 24; top contact bounces without damage; state 18 uses $814D and never touches health",
            "defeat: state 4 (148 updates, five $34 children) then state 5 (release camera, restore right limit 2304, player state $20 + jingle, $0A child, convert to $0F); no score",
            "art selector $13 loads, palette $0C, hit flash command 7, SAT-vs-mapping equality, music request $8C / $97",
        ],
        "corrected_or_closed_by_this_study": [
            "type $12 is the HUD slide-away (scrolls the three HUD sprite rows out through the SAT Y buffer); it only matters to the boss as a ~98-update delay before the pan",
            "type $0A parameter 0 is NOT 'released animals': it computes the act-clear bonus D2A6 (routine $041F) and emits a trail of sparkle $0A (parameter $FF) objects behind the player",
            "D2A6 in THZ3 is set by that $0A at the conversion update (object-18 doc listed it as unresolved); the level timer D2BE is never stopped in THZ3",
            "$1543 (zone clear) traced instruction by instruction: same skeleton as $14AE (act clear) with an act-3 tail ($2D55 boss bonus loop) and zone advance",
            "'act completes about 181 frames after the conversion' is player-position dependent (186 when Sonic stands at X 1760 at the conversion; 181 from X 1800); the invariant is playerX - cameraX > $120",
            "player state in hit tests: the boss $03 bit 7 bypasses the player's $D503 bit-6 gate, so a hurt (bit 6) Sonic that still has bit 1 set DOES hit the boss and is knocked back again",
            "invincibility: $D532 == 6 is not tested; the pickup also sets $D503 bits 1|7, so an invincible Sonic hits the boss through bit 1 until the next landing clears it, after which he neither hits nor is hurt",
            "player extents while rolling: 8 x 24 (docs/collision-geometry-audit.md), no longer an open item",
        ],
        "partly_proven_still": [
            "consumer of $D494/$D495 (sprite palette command): observed through CRAM only",
            "sound names beyond their class (numbers only): $8C boss music, $B6 hit, $A6 bounce, $C4 explosion, $97 clear jingle, $B4 tally tick",
            "zones 1..7 rows of $97A1 / $9808 (decoded data only, not needed for THZ3)",
        ],
        "missing_for_poc_implementation_before_this_study_now_supplied": [
            "support object roles (b2), arena/camera constants in the shared vocabulary (b3), explicit +-1 contact fixtures incl. invincible/hurt postures (b4), phase model split into gameplay/presentation (b5), "
            "defeat -> act clear timeline with the bonus and results waits (b6/b7), asset inventory (b8), machine-readable manifest (b9)",
        ],
    }


# (state, role, entry, duration, movement, spawns, vulnerable, exit, hit_effect, class)
PHASES = [
    (0, "init", "slot created (generic placement ring)", "1 update", "none", "type $12 (pool $D540, parameter $97); music request $8C; $D44E := zone+1; left limit follows camera", False, "next update -> 1", "-", "gameplay"),
    (1, "wait_for_player", "from 0", "until trigger", "none", "-", False, "|dx| < 160 and |dy| < 256 (PLAYER_DIST) -> right limit := camera X, request 2", "-", "gameplay"),
    (2, "wait_for_hud_slide", "from 1", "until the $12 child is gone (about 98 updates after creation)", "none", "-", False, "child gone -> bottom limit 78, pan target (bossX-256, bossY-160), request 3", "-", "gameplay (timing); the child itself is presentation"),
    (3, "arena_setup", "from 2", "1 update", "vx := -128/256", "art selector $13, palette $0C, health 8, +$03 bit 7", False, "request 18", "health := 8", "gameplay"),
    (18, "entry_sweep", "from 3", "about 68 updates", "-0.5 px/update from the right edge", "-", False, "screen X low byte in $80..$DF (EDGE(RIGHT,-33..-128)) -> 6; helper $814D: solid, hurts a non-attacker, knocks an attacker back, never changes health", "none", "gameplay"),
    (6, "left_cruise", "from 18 / 15", "until screen X low byte < $38 (EDGE(LEFT,+56))", "-128/256 (first) / -130/256", "-", True, "decelerate (phase $FF) then request 9", "-1 health -> reaction 8", "gameplay"),
    (9, "turn_to_right", "from 6", "about 19 updates", "decelerate then accelerate to +$20", "-", True, "vx >= $0020 -> 12", "-1 -> reaction 11", "gameplay"),
    (12, "right_cruise", "from 9", "until screen X low byte >= $C8 (EDGE(LEFT,+200))", "+128/256, mirrored", "-", True, "decelerate then request 15", "-1 -> reaction 14", "gameplay"),
    (15, "turn_to_left", "from 12", "about 14 updates", "decelerate then accelerate to -$20", "-", True, "vx < -$0020 -> 6", "-1 -> reaction 17", "gameplay"),
    (7, "top_bounce_reaction_of_6", "player landed on top", "20 updates", "continues", "-", False, "-> 6", "none", "gameplay"),
    (10, "top_bounce_reaction_of_9", "top contact", "20 updates", "continues", "-", False, "-> 9", "none", "gameplay"),
    (13, "top_bounce_reaction_of_12", "top contact", "20 updates", "continues", "-", False, "-> 12", "none", "gameplay"),
    (16, "top_bounce_reaction_of_15", "top contact", "20 updates", "continues", "-", False, "-> 15", "none", "gameplay"),
    (8, "hit_reaction_of_6", "attack hit", "20 updates", "frozen", "-", False, "-> 6, vx := 0, phase 1", "(health already -1)", "gameplay"),
    (11, "hit_reaction_of_9", "attack hit", "20 updates", "frozen", "-", False, "-> 9", "-", "gameplay"),
    (14, "hit_reaction_of_12", "attack hit", "20 updates", "frozen", "-", False, "-> 12", "-", "gameplay"),
    (17, "hit_reaction_of_15", "attack hit", "20 updates", "frozen", "-", False, "-> 15", "-", "gameplay"),
    (4, "defeat_explosions", "health reached 0 in 6/9/12/15", "148 updates", "none", "five $34 puffs at offsets (-8,0) (8,0) (0,-16) (-8,-24) (-8,-24) on updates 0..4; 24 flicker loops (4 updates saved frame, 2 blank)", False, "-> 5", "-", "presentation + timing"),
    (5, "finish", "from 4", "1 update when Sonic is on the floor (D522 bit 1), else waits", "none", "release camera (D280 := camX, D282 := 2304), player state $20 + $97, $0A parameter 0, convert to $0F", False, "slot becomes type $0F, token cleared", "-", "gameplay"),
]


def phase_model(rom: bytes) -> dict:
    cache = json.loads((ROOT / "data/rom-cache/thz3/object-50.json").read_text(encoding="utf-8"))
    tab = o50.anim.animation_state_table(rom, 0x50)
    states = []
    for row in PHASES:
        st, role, entry, dur, mov, spawn, vul, exit_, hit, cls = row
        states.append({"state": st, "role": role, "entry": entry, "duration": dur, "movement": mov, "spawns": spawn, "boss_can_be_damaged_in_this_state": vul, "exit": exit_,
                       "hit_count_effect": hit, "class": cls, "script_cpu": h(tab["state_script_cpus"][st])})
    return {"evidence": "SOURCE-TRACED + CONTROLLED + EMULATED (docs/object-50.md section 5, re-verified by the contact grid, trigger boundaries and full-fight emulation of this study)",
            "states": states,
            "vulnerable_states": [r["state"] for r in states if r["boss_can_be_damaged_in_this_state"]],
            "explicit_adapter_note": "everything marked presentation (explosion puffs, flicker, HUD slide, poof, sparkles) can be replaced by GameMaker effects as long as the timing facts (state 4 = 148 updates, state 2 wait about 98 updates after creation) are kept",
            "hit_cycle": {"reaction_updates": 20, "min_interval_between_hits_updates": 22, "hits_to_defeat": 8, "top_contact_damage": 0},
            "patrol_cycle_updates": 721, "patrol_world_x_range_at_locked_camera_1679": [1726, 1887]}


def assets(rom: bytes) -> dict:
    cache = json.loads((ROOT / "data/rom-cache/thz3/object-50.json").read_text(encoding="utf-8"))
    loads = cache["graphics"]["art_source"]["dynamic_load"]["loads"]
    st = support_static(rom)
    items = []
    items.append({"id": "boss_tiles_unmirrored", "kind": "tiles", "source": "bank 0x0A:$8940 (ROM 0x28940)", "tiles": 72, "vram": "0x05C0", "tile_ids": "0x2E..0x75", "source_sha256": loads[0]["source_sha256"],
                  "status": "extracted/decoded (tools/object_50.py --png)", "used_by": "boss frames 1-6 unmirrored (+$08 = 0)"})
    items.append({"id": "boss_tiles_mirrored_copy", "kind": "tiles", "source": "same source through the bit-reversal table at ROM 0x0100", "tiles": 44, "vram": "0x0EC0", "tile_ids": "0x76..0xA1",
                  "source_sha256": loads[1]["source_sha256"], "status": "extracted/decoded", "used_by": "boss frames 1-4 mirrored (+$09 = 0x48)"})
    items.append({"id": "explosion_tiles_a2", "kind": "tiles", "source": "bank 0x09:$ABA0 (ROM 0x26BA0)", "tiles": 12, "vram": "0x1440", "tile_ids": "0xA2..0xAD", "source_sha256": loads[2]["source_sha256"],
                  "status": "extracted/decoded", "used_by": "type $34 puffs, art base from table at bank 0x1E:$8C98 (zone 0 = $A2)"})
    items.append({"id": "boss_mapping_94C6", "kind": "mapping", "source": "bank 0x0F:$94C6 (ROM 0x3D4C6), pointer 0x3C0A0", "frames": 7, "status": "decoded (object-50.json graphics.frames)"})
    items.append({"id": "boss_sprite_palette_0C", "kind": "palette", "source": "ROM 0x3B70D", "status": "decoded; differs from sprite palette $06 only in colours 13-15 ($35,$20,$3F); hit flash writes $3F,$3F for 4 updates"})
    items.append({"id": "effect_mapping_8C71_frames", "kind": "mapping", "source": "bank 0x0F:$8C71 (ROM 0x3CC71) shared by $0A and $0F, frames 5,6 (sparkle) and 7,8,9 (smoke poof)",
                  "status": "decoded here (support_static); tiles already in the THZ level VRAM image (offsets 32..45, tile base 0)"})
    items.append({"id": "puff_mapping_92C5_frames", "kind": "mapping", "source": "bank 0x0F:$92C5 (ROM 0x3D2C5), frames 1-4", "status": "decoded here; tiles via explosion_tiles_a2"})
    items.append({"id": "hud_sprites", "kind": "existing", "source": "level HUD (SAT rows DB34..DB3F)", "status": "already in POC (HUD objects); type $12 only needs a slide-away effect"})
    items.append({"id": "results_screen_32F9", "kind": "screen", "source": "$32F9 and tables $3800..$3D10", "status": "same screen as acts 1/2 (deferred in POC for THZ1/2 as well); not extracted"})
    items.append({"id": "audio_requests", "kind": "numbers", "source": "sound ids 0x8C boss music, 0xB6 hit, 0xA6 bounce, 0xC4 explosion, 0x97 clear jingle, 0xB4 tally", "status": "numbers only (no audio is extracted)"})
    return {"evidence": "DECODED DATA", "items": items, "genuinely_missing": ["audio waveforms/music (never extracted by this project)", "results-screen graphics (shared with acts 1/2, deferred)"],
            "substitute_graphics": "none invented; every sprite above is ROM-derived", "support_frames_decoded": {k: st[k]["frames_reachable"] for k in ("0x34", "0x0A", "0x0F")},
            "export": "python tools/thz3_boss_support.py ROM --png build/thz3-boss-support writes boss, puff, poof and sparkle frames (git-ignored, ROM-derived)"}


def export_pngs(rom: bytes, out_dir: Path) -> None:
    from PIL import Image
    out_dir.mkdir(parents=True, exist_ok=True)
    vram, _ = o50.dynamic_vram(rom)
    pal = o50.sprite_palette(rom, 0x0C)
    todo = [("boss", 0x50, list(range(1, 7)), 0, False), ("boss_mirrored", 0x50, [1, 2, 3, 4], 0x48, True), ("puff34", 0x34, [1, 2, 3, 4], 0xA2, False),
            ("sparkle0a", 0x0A, [5, 6], 0, False), ("poof0f", 0x0F, [7, 8, 9], 0, False)]
    for name, t, frames, base, mir in todo:
        m = o50.assets.object_mapping(rom, t)
        ptrs = o50.assets.mapping_frame_pointers(rom, m["mapping_cpu"])
        for i in frames:
            r = o50.assets.parse_frame_record(rom, ptrs[i])
            fr = {"pieces": [{"y": p["relative_y"], "x": p["relative_x"], "tile_offset": (p["tile_offset"] + (0 if t == 0x50 else base)) & 0xFF} for p in r["pieces"]]}
            c = o50.compose_frame(vram, fr, mir if t == 0x50 else False, pal)
            if not c:
                continue
            w, hgt, x0, y0, canvas, _ = c
            im = Image.new("RGBA", (w, hgt), (0, 0, 0, 0))
            for y in range(hgt):
                for x in range(w):
                    if canvas[y][x]:
                        im.putpixel((x, y), o50.rgba_of(canvas[y][x], pal))
            im.save(out_dir / f"{name}_frame{i}.png")


# --------------------------------------------------------------------------- #
# vocabulary constants, manifest, build
# --------------------------------------------------------------------------- #
def arena_constants(arena: dict | None) -> dict:
    """Recovered THZ3 boss constants in the shared vocabulary. SMS view width 256; 'view' = the real view width in a port."""
    return {
        "evidence": "derived from the b3 emulation/controlled results (values copied, not assumed) + SOURCE-TRACED tables $97A1/$9808",
        "boss_anchor": {"rule": "WORLD(1936,238) canonical placement; equals LOCKED_CAMERA(1679)+257 = EDGE(RIGHT,+1) of the locked 256 px view"},
        "creation": {"rule": "generic ring: 288 <= bossX - camX <= 351 (EDGE(RIGHT,+32..+95)); camera X 1585..1648 at 256 px", "vocabulary": "EDGE(RIGHT,+32..+95)"},
        "camera_left_lock": {"rule": "from creation (state 0) the left scroll limit D280 is raised to the camera every update: the camera never scrolls left again", "vocabulary": "LOCKED_CAMERA follow, camera-relative"},
        "trigger": {"rule": "|playerX - bossX| < 160 and |playerY - bossY| < 256 (strict)", "vocabulary": "PLAYER_DIST(160) / PLAYER_DIST(256): never widened"},
        "right_lock": {"rule": "at the trigger the right scroll limit D282 := camera X; later D282 := pan target X (1680)", "vocabulary": "LOCKED_CAMERA(camera at trigger)"},
        "pan": {"target": "(bossX-256, bossY-160) = (1680,78): X = bossX - 256 (boss at EDGE(RIGHT,0) of the locked view), Y = bossY - 160; bottom limit D27E := 78",
                "speed": "1 px/update on both axes; X stops 1 px short (exclusive limit): 1679", "vocabulary": "LOCKED_CAMERA(1679, 78)", "starts": "when the $12 child is gone"},
        "entry": {"start": "boss at WORLD 1935/1936 moving -0.5 px/update", "to_patrol": "screen X low byte in $80..$DF -> state 6 (measured x 1901, screen 222)", "vocabulary": "EDGE(RIGHT,-33) of the locked view (screen X 223 max)"},
        "patrol": {"left_turn": "screen X low byte < $38: EDGE(LEFT,+56) of the locked view = WORLD 1735", "right_turn": "screen X low byte >= $C8: EDGE(LEFT,+200) = EDGE(RIGHT,-56) = WORLD 1879",
                   "measured_world_range_of_anchor": [1726, 1887], "vocabulary": "LOCKED_CAMERA(1679)+56 / +200"},
        "player_clamp": {"rule": "original EDGE(LEFT,+16)..EDGE(RIGHT,-9) of the locked view; measured anchor range 1694..1927 (camera 1679); THZ3 has no terrain wall (flat floor 1600..2560)",
                         "vocabulary": "LOCKED_CAMERA(1679)+16 .. +247 in WORLD terms; a live-view EDGE clamp would let a wide view leave the arena"},
        "release": {"rule": "state 5: D280 := camera X, scroll flags cleared, D282 := 2304 (saved at creation = level width 2560 - 256)", "vocabulary": "right limit = WORLD width - view width"},
        "act_clear_threshold": {"rule": "playerX - cameraX > $120 (EDGE(RIGHT,+33)); measured player X 2591..2593, camera 2299 (2304 limit); in world terms 2593 = worldWidth + 33 for any view width"},
        "arena_measured": arena and {k: arena[k] for k in ("final_lock", "player_clamp")},
        "widescreen_decisions_left_to_the_port": [
            "where the locked camera sits for a view wider than 256 (SMS: boss enters from the right edge, EDGE(RIGHT,+1))",
            "whether the arena clamp stays at world 1695..1926 (faithful arena) or follows the live view (bigger arena, floor continues to 2560)",
            "boss patrol stays in WORLD terms (1726..1887) so the fight geometry is unchanged",
        ],
    }


CONTACT_FIXTURE_POINTS = [(28, 0), (29, 0), (-28, 0), (-29, 0), (0, 24), (0, 25), (0, -48), (0, -49), (0, -1), (0, 0), (27, -47), (28, -47), (1, 23), (27, 1), (14, -34), (15, -34), (-14, -34), (-15, -34)]


def contact_fixtures(rom: bytes) -> list:
    lab = BossLab(rom)
    rows = []
    for pname in ("walker_grounded", "attacker_ball_grounded", "attacker_jump_airborne", "invincible_pickup_state", "invincible_after_landing_bit1_clear",
                  "invulnerable_blink_non_attacking", "hurt_state_bit6_with_bit1"):
        for dx, dy in CONTACT_FIXTURE_POINTS:
            r = lab.case(6, dx, dy, **POSTURES[pname])
            rows.append({"state": 6, "posture": pname, "dx": dx, "dy": dy, "expected": boss_outcome(r, 6, 8), "contact_bits": r["contact_bits"]})
    for dx, dy in ((0, -40), (0, -49)):
        r = lab.case(6, dx, dy, d503=0x03, vy=0xFE00)
        rows.append({"state": 6, "posture": "attacker_jump_airborne_rising", "dx": dx, "dy": dy, "expected": boss_outcome(r, 6, 8), "contact_bits": r["contact_bits"]})
    return rows


def manifest(rom: bytes, cache: dict) -> dict:
    obj = json.loads((ROOT / "data/rom-cache/levels/thz3/objects.json").read_text(encoding="utf-8"))
    lay = json.loads((ROOT / "data/rom-cache/levels/thz3/layout.json").read_text(encoding="utf-8"))
    b = cache["part_b"]
    placements = []
    for r in obj["records"]:
        t = int(r["raw_bytes"].split()[0], 16)
        placements.append({"index": r["index"], "type": h(t, 2), "world": [r["world_x"], r["world_y"]], "flags": r["flags"], "parameter": r["parameter"], "aux0": r["aux0"], "aux1": r["aux1"],
                           "rom_offset": r["rom_offset"], "class": "boss" if t == 0x50 else "reused_ordinary_object"})
    return {
        "format": 1, "rom_sha256": ROM_SHA256, "act": "thz3", "research_only": True, "poc_untouched": True,
        "purpose": "everything POC needs to make THZ3 playable through boss and act clear; numeric labels only; every value is copied from data/rom-cache/thz3-boss-support.json",
        "reused_ordinary_systems": {
            "terrain": {"blocks_used": lay["block_ids_used"], "new_blocks_vs_thz1_thz2": 0, "size_px": [2560, 512], "layout": "data/rom-cache/levels/thz3/layout.json"},
            "objects": {"0x09": "rings, strict proximity < 12 (object-09)", "0x26": "springs (spring-interaction)", "0x10": "monitor parameter 1 (object-10)",
                        "0x1B": "moving spike at (752,128): lifecycle facts in part_a.a3_lifecycle.spike_1b, push/cooldown in a1/a2", "terrain": "rings $753E, springs, no spike blocks"},
        },
        "placements": placements,
        "boss": {
            "object": "0x50", "placement": placements[0], "hit_points": 8, "states": b["b5_phase_model"]["states"], "vulnerable_states": b["b5_phase_model"]["vulnerable_states"],
            "damage_rule": "contact bit side/below + player $D503 bit 1 -> -1 health, knockback, reaction 20 updates; bit 0 (top) -> bounce vy -4.0 (state $0B, sound $A6), no damage; non-attacking -> damage request + 2-update cooldown; $D532 == 6 never tested",
            "knockback": "contact bit 3: vx -6.0; bit 2: vx +6.0; bit 1: vy +6.0; bit 0: vy -4.0; other axis keeps vx and negates vy; player state $1B; palette flash command 7; sound $B6",
            "contact_geometry": b["b4_boss_contact"]["geometry"], "contact_fixtures": b["b4_boss_contact"]["manifest_fixtures"],
            "children": {"0x12": "HUD slide-away (presentation, but gates state 2)", "0x34": "explosion puff x5 in state 4 (presentation)", "0x0A": "param 0: bonus D2A6 + sparkle emitter; param $FF sparkle (presentation + bonus)", "0x0F": "slot conversion poof (presentation, 38 updates)"},
        },
        "arena_and_camera": b["b3_arena_camera"]["constants"],
        "defeat_and_clear": b["b6_defeat_act_clear"]["summary"],
        "assets": b["b8_assets"]["items"],
        "fixtures": {"files": ["data/rom-cache/thz3-boss-support.json", "tests/test_thz3_boss_support.py"],
                     "counts": cache["counts"], "aligned_update_harness": "Aligned (tools/thz3_boss_support.py): writes at the $1336 update boundary"},
        "poc_readiness": b["b11_poc_readiness"],
    }


def poc_readiness() -> dict:
    return {
        "evidence": "POC SOURCE (READ-ONLY) at 7799c34 plus the uncommitted working tree; nothing was run or modified",
        "usable_unchanged": [
            "SCR_chaos_viewport: WORLD/EDGE/CENTER/PLAYER_DIST/LOCKED_CAMERA helpers cover every boss constant (b3.constants)",
            "SCR_chaos_box_contact: $6328 minimum-penetration contact for any extents (boss 20x48 vs Sonic 8x24) and SCR_chaos_box_projection for the solid push",
            "SCR_chaos_attack: chaos_attack_posture (bit 1 only) is exactly the boss predicate; staged $D3B0 request/promotion (chaos_request_stage) matches the ROM's one-update delay",
            "act-clear tail: player state $20 run, EDGE(RIGHT,+33) clear (chaos_goal_clear_dx), chaos_act_complete progression; type $0F transient (OBJ_chaos_object_0F_transient: 37 visible updates matches the ROM puff)",
            "SCR_chaos_spike1b already skips the whole contact helper (wall and push included) during the 16-update cooldown, pushes +23 only for bit 4 else -23: matches A1/A2",
            "THZ3 level data/objects/rings already generated (SCR_chaos_level_thz3_data); chaos_level_spawn_objects counts the unsupported $50 as skipped",
        ],
        "new_subsystems_required": [
            "boss object ($50): 19-state machine with the numbers in part_b.b5_phase_model, health, reaction timers, solid contact, hit/bounce/damage effects",
            "arena camera: scroll limits (left raise, right lower, bottom 78) and the explicit-target pan; chaos_goal_pan_step derives its target from a sign anchor and the view centre, so it needs a target provider (LOCKED_CAMERA(1679,78)) rather than a rewrite",
            "arena player clamp in WORLD terms (chaos_goal_clamp_player is hard-wired to the live view and only runs until state $20)",
            "boss-clear completion: conversion update computes D2A6 (needs time and rings), requests state $20, keeps the timer running, then the shared act-clear tail",
            "presentation effects: HUD slide-away, $34 puffs, $0A sparkle trail; boss/puff sprites and palette $0C (frames exported by --png)",
        ],
        "assumptions_likely_to_conflict": [
            "chaos_act_complete and chaos_finish_time assume the timer stopped at a $18 contact; in THZ3 the timer is never stopped and the bonus is taken at the conversion update",
            "chaos_goal_clamp_player and chaos_goal_pan_step use the live view width: in a wide view they would enlarge or re-centre the arena unless an explicit world rectangle is supplied",
            "OBJ_chaos_zone follows the player vertically with a fixed 1/1.5 rule and has no scroll-limit concept; the boss pan needs Y locked to 78",
            "the lifecycle retention adapter extends lifetimes for $1B; the ROM restarts a deleted spike at wake (A3) so wide-view backtracking can show a different spike phase (adapter, acceptable)",
            "chaos_acts() lists THZ3 as the last act with 'no act clear'; progression after THZ3 is zone 1 act 1 (not implemented)",
        ],
        "widescreen_helpers_sufficient": "yes for relationships (vocabulary), no for the clamp/pan/limit behaviour above, which must be written once as a small camera-limit layer",
        "thz3_fully_playable_in_next_batch": "reasonable: no new ROM research is blocking; the work is one boss object, a camera-limit/arena layer, three effect objects and sprite import. Results screen and boss-clear score loop can stay deferred like THZ1/2",
    }


def counts_of(cache: dict) -> dict:
    n = lambda v: psc._count_cases(v)
    a, b = cache.get("part_a", {}), cache.get("part_b", {})
    c = {
        "a1_probe_rows": a.get("a1_cooldown_side_wall", {}).get("probe_table_rows", 0),
        "a2_push_cases": a.get("a2_grounded_push", {}).get("cases", 0) + a.get("a2_grounded_push", {}).get("independence", {}).get("cases", 0),
        "a4_aligned_spike_runs": a.get("a4_static_spike_aligned", {}).get("runs", 0),
        "b3_trigger_cases": len(b.get("b3_arena_camera", {}).get("trigger_boundaries", {}).get("state_1_trigger", {}).get("rows", [])),
        "b3_creation_window_cases": 120,
        "b4_contact_cases": b.get("b4_boss_contact", {}).get("cases", 0),
    }
    c["controlled_cases_total"] = sum(c.values())
    c["emulated_whole_game_runs"] = 3 + 2 + 5 + 3 + 2 + 20 + 1446
    return c


def build(rom: bytes, part: str = "all", static_only: bool = False) -> dict:
    check_rom(rom)
    legacy = json.loads((ROOT / "data/rom-cache/platform-spike-collision.json").read_text(encoding="utf-8"))
    out = {"format": 1, "rom_sha256": ROM_SHA256, "subject": "THZ3 boss/support audit and $1B/$28 closure", "research_only": True, "poc_untouched": True,
           "evidence_classes": EVIDENCE, "harness_note": HARNESS_NOTE, "static_only": static_only}
    a, b = {}, {}
    if part in ("all", "a") and not static_only:
        a["a1_cooldown_side_wall"] = a1_cooldown_side_wall(rom)
        a["a2_grounded_push"] = a2_grounded_push(rom)
        a["a3_lifecycle"] = a3_lifecycle(rom)
        a["a4_static_spike_aligned"] = a4_static_spike_aligned(rom, legacy)
    if part in ("all", "b"):
        b["b1_reconciliation"] = reconciliation(rom)
        b["b2_support_objects"] = {"static": support_static(rom), "controlled": None if static_only else support_controlled(rom),
                                   "roles": {
                                       "0x12": {"role": "HUD slide-away: scrolls the three HUD sprite rows (SAT Y bytes DB34..DB3F) out of the top of the screen at 0.5 px/update", "creator": "boss state 0 callback (allocator $81A6, parameter $97)", "placements": 0, "boss_essential": "timing only (state 2 waits for it, about 98 updates after creation)", "contact": "none"},
                                       "0x34": {"role": "explosion puff", "creator": "boss state 4 script (FF 04, five per boss, parameter 4); the same state also exists for the other bosses ($51-$53 scripts)", "placements": 0, "boss_essential": False, "contact": "none"},
                                       "0x0A": {"role": "parameter 0: act-clear bonus calculator (D2A6 := $041F) + sparkle emitter; parameter $FF: sparkle (frames 5/6, 28 updates)", "creator": "boss state 5 via $032C (parameter 0); itself (parameter $FF)", "placements": 0, "boss_essential": "bonus value only (results screen); sparkles are presentation", "contact": "none"},
                                       "0x0F": {"role": "generic replacement object (poof); the boss slot becomes one with parameter 0", "creator": "$033E conversion at the end of state 5 (also monitors/badniks in THZ1/2)", "placements": 0, "boss_essential": False, "lifetime_updates": 38, "contact": "none"},
                                   },
                                   "not_in_chain": "none of the four is a canonical map placement in THZ1-3; no further object is needed by the canonical THZ3 boss sequence"}
        if not static_only:
            arena = arena_camera(rom)
            arena["trigger_boundaries"] = trigger_boundaries(rom)
            arena["constants"] = arena_constants(arena)
            b["b3_arena_camera"] = arena
            grid = boss_contact_grid(rom)
            grid["manifest_fixtures"] = contact_fixtures(rom)
            b["b4_boss_contact"] = grid
        b["b5_phase_model"] = phase_model(rom)
        if not static_only:
            chain = defeat_chain(rom)
            var = defeat_variants(rom)
            b["b6_defeat_act_clear"] = {"fight": chain, "variants": var, "summary": {
                "final_hit_to_state_4": "same update", "state_4_updates": 148, "conversion": "state 5 runs in the update after state 4 ends when Sonic is on the floor: camera released, D282 := 2304, player state $20 + $97, $0A parameter 0 (D2A6 bonus), slot -> $0F",
                "player_control": "none after the conversion update (state $20 ignores input); damage cannot occur: no boss contact in states 4/5",
                "flag": "playerX - cameraX > $120 sets D293 bit 4 (act index 2); about 181..186 frames after conversion depending on Sonic's X",
                "main_loop": "$1333 -> $1543: 60 waits, fades, 96, 30, results $32F9 at flag+199, ring/time tally from flag+299, act-3 boss bonus loop $2D55 (50 x 10 points in zone 0) at flag+275, advance $15CE at about flag+856..889, level load of zone 1 act 0",
                "timer": "never stopped in THZ3 (D2BE stays $FF); bonus computed once at conversion",
                "score": "rings x 10 + D2A6 steps + 500; no score for the boss itself ($5F77 gate)",
                "converges_with_18_19_20": "shares player state $20, handler $83A6, flag D293 and the results routines; differs in the creator ($50 state 5 instead of $19), the $0A bonus and the $1543 act-3 tail"}}
        b["b7_results_dependencies"] = {"evidence": "BYTE-VERIFIED (disassembly of $1333, $1543, $14AE, $32F9, $2D08, $2D55, $2F05) + EMULATED (b6)",
                                        "owner": "no separate object: the main loop ($1333) dispatches on D293 bit 4 to $1543",
                                        "input_lock": "state $20 handler ignores input; hostile button presses leave the flag frame and player X unchanged",
                                        "mandatory_waits_frames": "flag -> $1543 immediate; 60 + 96 + 30 + 12 + 48 + 96 + 48 around the results screen (about 199 frames to $32F9)",
                                        "tally": "$2D08: rings (BCD, 10 points each) then D2A6 (1 point per step); $2D55 (only when the act index is 2): table $2D84[zone] = 50,100,150,200,250,600 iterations of +10 points",
                                        "needed_to_finish_thz3": "progression only (zone 1 act 0 request after about 860..890 frames); the tally and screen are presentation/score and may be deferred like THZ1/2",
                                        "zone_advance": "$15CE: D298 := 0, D297 += 1; zone >= 6 -> game-complete flag instead"}
        b["b8_assets"] = assets(rom)
        b["b11_poc_readiness"] = poc_readiness()
    out["part_a"], out["part_b"] = a, b
    out["unresolved_or_deferred"] = [
        "results-screen graphics and boss-clear score loop presentation (deferred, shared with acts 1/2)",
        "button-skip of the tally pacing ($D137) did not shorten the harness run; real pad polling not verified",
        "sound/music numbers only",
        "no Windows/GameMaker run; POC was read only",
        "zones 1-7 boss tables decoded as data only",
        "$12 byte pattern at ROM 0x30DAC is not inside a decoded type script; the boss allocator call is the only proven creator",
    ]
    if not static_only and part == "all":
        out["counts"] = counts_of(out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    ap.add_argument("--part", choices=("all", "a", "b"), default="all")
    ap.add_argument("--png", type=Path)
    a = ap.parse_args()
    rom = a.rom.read_bytes()
    if a.png:
        check_rom(rom)
        export_pngs(rom, a.png)
        print(f"wrote PNGs to {a.png}")
        return
    data = build(rom, a.part, a.static_only)
    text = json.dumps(data, indent=1) + "\n"
    if a.check:
        cached = OUTPUT.read_text(encoding="utf-8").replace("\r\n", "\n")
        if a.static_only or a.part != "all":
            cj, dj = json.loads(cached), data
            bad = []
            for p in ("part_a", "part_b"):
                for k, v in dj[p].items():
                    if cj[p].get(k) != v:
                        bad.append(f"{p}.{k}")
        else:
            bad = [] if cached == text else ["file"]
            if not bad and MANIFEST.exists():
                m = json.dumps(manifest(rom, data), indent=1) + "\n"
                bad = [] if MANIFEST.read_text(encoding="utf-8").replace("\r\n", "\n") == m else ["manifest"]
        print("OK: thz3-boss-support cache matches the ROM" if not bad else f"MISMATCH in {bad}")
        sys.exit(1 if bad else 0)
    if a.static_only or a.part != "all":
        print(json.dumps({k: list(v) for k, v in (("part_a", data["part_a"]), ("part_b", data["part_b"]))})[:300])
        return
    OUTPUT.write_text(text, encoding="utf-8", newline="\n")
    MANIFEST.write_text(json.dumps(manifest(rom, data), indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT} ({len(text)} bytes) and {MANIFEST}; counts: {data.get('counts')}")


if __name__ == "__main__":
    main()

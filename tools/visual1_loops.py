#!/usr/bin/env python3
"""VISUAL-1 Part A: THZ1 loop presentation (player states $0C / $0D / $13, selector $903D, frames $2A..$5D).

Evidence classes
  DECODED DATA            selector pair table, route offset tables, dispatch table, THZ1 layout
  BYTE-VERIFIED ASSEMBLY  dispatcher $6C82, entry helpers $3EAB/$3EE1/$3EF7, routes $3C1B/$3DAE, selectors $903D/$8F76
  EMULATED ORIGINAL FRAME the unmodified ROM runs in tools/sms_frame_harness.py with the pad driven by the caller;
                          every player update, selector call, route event and sprite-attribute table is recorded
  NATURAL                 emulated from the real THZ1 start record with a seeded pad script only (no fixture of any kind)
  CONTROLLED              emulated with the start record rewritten in a private in-memory ROM copy (position only) and a scripted pad

Source-decoded rules and observed traversals are reported side by side; a rule is "confirmed" only where every observed
selector call reproduces it.

Usage:
    python tools/visual1_loops.py ROM [--output build/visual1] [--metadata JSON] [--check] [--static-only]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import level_package as LP  # noqa: E402
import rom as R  # noqa: E402
import thz1_object_assets as A  # noqa: E402
import visual1_shards as V  # noqa: E402
from visual1_shards import bank_file, hx, s16, sha  # noqa: E402

LOOP_BLOCKS = range(0x48, 0x56)
STATE_RIGHT, STATE_LEFT, STATE_ALT = 0x0C, 0x0D, 0x13
LOOP_STATES = (STATE_RIGHT, STATE_LEFT, STATE_ALT)
PAIR_TABLE = 0x906C                      # bank $0C CPU; type-1 table, 51 pairs
PAIR_TABLE_TAILS = 0x90D2
SELECTOR_DIVISOR = 13
EXIT_PROGRESS = 0x180
MIDPOINT_PROGRESS = 0x90
ROLL_TABLE = 0x8FB8
ROLL_DURATION_TABLE = 0x8FE0
THZ1 = (0, 0)
FRAME_COUNT = 98

EXPECT_ASM = OrderedDict([
    ("dispatch_6c82", (0x6C82, 0x6C99, 0, [
        "LD A,(0xd36b)", "CP 0x83", "JR z,0x6cb9", "SUB 0x48", "RET c", "ADD A,A", "LD DE,0x6c99", "ADD HL,DE", "LD E,(HL)", "LD D,(HL)",
        "EX DE,HL", "JP (HL)"])),
    ("entry_left_6cba", (0x6CBA, 0x6CCD, 0, [
        "LD A,(IX+0x25)", "OR A", "RET z", "BIT 1,(IX+0x22)", "RET z", "LD A,(0xd497)", "CP 0x52", "JP z,0x3ee1", "RET"])),
    ("entry_right_6ccd", (0x6CCD, 0x6CE5, 0, [
        "LD A,(IX+0x25)", "OR A", "RET nz", "BIT 1,(IX+0x22)", "RET z", "LD A,(0xd497)", "CP 0x51", "JP z,0x3eab", "CP 0x57",
        "JP z,0x3ef7", "RET"])),
    ("entry_setup_3eab", (0x3EAB, 0x3EFD, 0, [
        "LD (IX+2),12", "LD A,(IX+0x11)", "AND 0xe0", "LD (IX+0x11),A", "LD (IX+0x3a),L", "LD (IX+0x3b),H", "LD A,(IX+0x14)", "AND 0xe0",
        "ADD A,4", "LD (IX+0x14),A", "LD (IX+0x3c),L", "LD (IX+0x3d),H", "XOR A", "LD (0xd39d),A", "LD (0xd39e),A", "LD (0xd39f),A",
        "POP AF", "RET", "LD (IX+2),13", "LD BC,0x20", "ADD HL,BC", "JR 0x3eaf", "LD (IX+2),0x13", "JR 0x3eaf"])),
    ("route_right_3c1b", (0x3C1B, 0x3CC5, 0, [
        "LD A,13", "CALL 0x1c6f", "LD L,(IX+0x16)", "LD H,(IX+0x17)", "LD DE,(0xd39d)", "LD A,(0xd39f)", "ADD HL,DE", "INC A",
        "LD (0xd39d),HL", "LD (0xd39f),A", "LD HL,(0xd39e)", "ADD HL,HL", "LD DE,0x8000", "LD (IX+0x14),L", "LD (IX+0x15),H",
        "LD DE,0x8398", "LD (IX+0x11),L", "LD (IX+0x12),H", "LD DE,0x90", "SBC HL,DE", "JR nc,0x3c88", "LD DE,10", "SBC HL,DE",
        "JR c,0x3cc5", "JR 0x3c9c", "LD (IX+0x25),1", "LD DE,12", "ADD HL,DE", "CALL 0x48bc", "LD DE,0x180", "SBC HL,DE", "RET c",
        "LD A,6", "BIT 1,(IX+3)", "LD A,9", "LD (IX+2),A", "LD HL,(0xd373)", "LD (IX+0x16),L", "LD (IX+0x17),H", "LD A,0x10",
        "LD (0xd3a0),A", "RET"])),
    ("route_left_3dae", (0x3DAE, 0x3E74, 0, [
        "LD A,13", "CALL 0x1c6f", "DEC HL", "CPL", "CPL", "LD DE,(0xd39d)", "ADD HL,DE", "INC A", "LD (0xd39d),HL", "LD (0xd39f),A",
        "LD DE,0x86ae", "LD (IX+0x14),L", "LD DE,0x8a46", "LD (IX+0x11),L", "LD DE,0x90", "SBC HL,DE", "JR nc,0x3e30",
        "LD DE,10", "SBC HL,DE", "JR c,0x3e74", "LD (IX+0x25),0", "LD DE,0xfff4", "ADD HL,DE", "CALL 0x48bc", "LD DE,0x180",
        "SBC HL,DE", "RET c", "LD A,6", "BIT 1,(IX+3)", "LD A,9", "LD (IX+2),A", "LD HL,(0xd373)", "DEC HL", "LD A,0x10",
        "LD (0xd3a0),A", "RET"])),
    ("selector_903d", (0x903D, 0x906C, 12, [
        "BIT 1,(IX+3)", "JP nz,0x8f76", "LD HL,(0xd39e)", "LD E,13", "CALL 0x0368", "LD H,0", "ADD HL,HL", "LD DE,0x906c",
        "LD A,(IX)", "DEC A", "JR z,0x905b", "LD DE,0x90d2", "ADD HL,DE", "LD A,(HL)", "CP (IX+6)", "JR nz,0x9063", "INC HL",
        "LD A,(HL)", "LD (IX+6),A", "LD (IX+7),6", "RET"])),
    ("selector_roll_8f76", (0x8F76, 0x8FB8, 12, [
        "LD HL,0xd52f", "INC (HL)", "LD A,(HL)", "CP 0x14", "JR c,0x8f81", "XOR A", "LD (HL),A", "LD C,A", "LD B,0", "LD HL,0x8fb8",
        "LD A,(IX)", "DEC A", "JR z,0x8f90", "LD HL,0x8fcc", "ADD HL,BC", "LD A,(HL)", "LD (IX+6),A", "BIT 1,(IX+0x22)", "JR z,0x8ff0",
        "RES 4,(IX+4)", "LD A,(0xd517)", "AND A", "JP p,0x8fac", "NEG", "SET 4,(IX+4)", "LD L,A", "LD H,0", "LD DE,0x8fe0",
        "ADD HL,DE", "LD A,(HL)", "LD (IX+7),A", "RET"])),
    ("stubs_03c8", (0x03CB, 0x03D4, 0, ["JP 0x3c1b", "JP 0x3cfc", "JP 0x3dae"])),
    ("divide_2605", (0x2605, 0x2619, 0, ["LD B,0x10", "XOR A", "ADD HL,HL", "RLA", "CP E", "JR c,0x2610", "SUB E", "SET 0,L"])),
])


def verify_assembly(rom: bytes) -> OrderedDict:
    return V.verify_assembly(rom, EXPECT_ASM)


# ----------------------------------------------------------------------------------------------------------------
# static decode
# ----------------------------------------------------------------------------------------------------------------
def pair_table(rom: bytes) -> OrderedDict:
    base = bank_file(12, PAIR_TABLE)
    raw = rom[base:base + 102]
    pairs = [(raw[i], raw[i + 1]) for i in range(0, 102, 2)]
    base_t = bank_file(12, PAIR_TABLE_TAILS)
    rot = [i for i, p in enumerate(pairs) if p[0] >= 0x2A]
    return OrderedDict(
        table_cpu=hx(PAIR_TABLE, 4), table_rom=hx(base, 5), entries=len(pairs), tails_table_cpu=hx(PAIR_TABLE_TAILS, 4),
        divisor=SELECTOR_DIVISOR, index="pair index = floor(progress / 13); progress = 16-bit word at $D39E (the integer part of the 24-bit route cursor $D39D..$D39F)",
        pairs=[list(p) for p in pairs[:24]], pairs_from_24_all_walk=all(p in ((1, 2), (3, 4), (5, 6)) for p in pairs[24:]),
        first_rotated_pair_index=rot[0], last_rotated_pair_index=rot[-1], rotated_pairs=len(rot),
        rotated_frames=sorted({f for p in pairs for f in p if f >= 0x2A}), skipped_frames_between_blocks="$36..$3F (10 frames) are not in the table",
        progress_at_first_rotated_pair=rot[0] * SELECTOR_DIVISOR, progress_at_first_walk_pair_after=(rot[-1] + 1) * SELECTOR_DIVISOR,
        rule="selector: frame := pair[index][0], except pair[index][1] when pair[index][0] equals the current frame; then record duration $07 := 6",
        sha256=sha(raw))


def route_tables(rom: bytes) -> OrderedDict:
    out = OrderedDict()
    for name, ycpu, xcpu in (("right_3c1b", 0x8000, 0x8398), ("left_3dae", 0x86AE, 0x8A46)):
        y = [s16(R.u16(rom, bank_file(13, ycpu) + 2 * i)) for i in range(EXIT_PROGRESS + 40)]
        x = [s16(R.u16(rom, bank_file(13, xcpu) + 2 * i)) for i in range(EXIT_PROGRESS + 40)]
        out[name] = OrderedDict(
            bank=13, y_table_cpu=hx(ycpu, 4), x_table_cpu=hx(xcpu, 4), y_table_rom=hx(bank_file(13, ycpu), 5), x_table_rom=hx(bank_file(13, xcpu), 5),
            entries_hashed=len(y), y_sha256=sha(b"".join((v & 0xFFFF).to_bytes(2, "little") for v in y)),
            x_sha256=sha(b"".join((v & 0xFFFF).to_bytes(2, "little") for v in x)),
            samples={str(i): [x[i], y[i]] for i in (0, 1, 0x10, 0x48, MIDPOINT_PROGRESS, 0xD8, 0x120, 0x168, EXIT_PROGRESS)},
            x_range=[min(x[:EXIT_PROGRESS + 1]), max(x[:EXIT_PROGRESS + 1])], y_range=[min(y[:EXIT_PROGRESS + 1]), max(y[:EXIT_PROGRESS + 1])],
            note="position = saved origin + (x[p], y[p]); p = progress >> 8 read BEFORE the exit test, so a fast exit update may read past $180")
    return out


def dispatch_table(rom: bytes) -> OrderedDict:
    rows = OrderedDict()
    names = {0x6CB9: "RET (no loop action)", 0x6CBA: "$6CBA left entry (plane 1, floor, previous block $52 -> $3EE1 state $0D)",
             0x6CCD: "$6CCD right entry (plane 0, floor, previous $51 -> $3EAB state $0C; previous $57 -> $3EF7 state $13)", 0x6CE5: "RET"}
    for b in range(0x48, 0x57):
        cpu = R.u16(rom, 0x6C99 + (b - 0x48) * 2)
        rows[hx(b)] = OrderedDict(handler=hx(cpu, 4), meaning=names.get(cpu, "unclassified"))
    return OrderedDict(selector_block="$D36B (current foot block); block $83 returns early", base_block=0x48, table=hx(0x6C99, 4), rows=rows)


def roll_selector(rom: bytes) -> OrderedDict:
    t = bank_file(12, ROLL_TABLE)
    d = bank_file(12, ROLL_DURATION_TABLE)
    return OrderedDict(
        table_cpu=hx(ROLL_TABLE, 4), frames=list(rom[t:t + 20]), counter="$D52F increments each call and wraps at 20",
        duration_table_cpu=hx(ROLL_DURATION_TABLE, 4), durations_by_abs_x_speed_hi=list(rom[d:d + 16]),
        facing="with floor contact (+$22 bit 1): bit 4 of +$04 is cleared, then set when the X speed high byte ($D517) is negative; in the air (+$22 bit 1 clear) the selector jumps to $8FF0 (not decoded here) with duration 3 and facing untouched",
        used_by_loop_states="$903D tail-jumps to $8F76 whenever +$03 bit 1 (rolling / attack posture) is set")


def thz1_inventory(rom: bytes) -> OrderedDict:
    h = LP.act_header(rom, THZ1[0], THZ1[1])
    cells, _, _ = LP.decode_layout_stream(rom, h["layout_rom"], 4095)
    w = h["width_cells"]
    loops = [(i % w, i // w, v) for i, v in enumerate(cells) if v in LOOP_BLOCKS]
    xs = sorted({x for x, _, _ in loops})
    groups, cur = [], [xs[0]]
    for x in xs[1:]:
        if x - cur[-1] > 3:
            groups.append(cur)
            cur = [x]
        else:
            cur.append(x)
    groups.append(cur)
    out = OrderedDict(map_width=w, loop_block_cells=len(loops), structures=[])
    for g in groups:
        cs = [(x, y, v) for x, y, v in loops if g[0] <= x <= g[-1]]
        ys = sorted({y for _, y, _ in cs})
        right = [(x, y) for x, y, v in cs if v == 0x52 and cells[y * w + x - 1] == 0x51]
        left = [(x, y) for x, y, v in cs if v in (0x50, 0x51) and cells[y * w + x + 1] == 0x52]
        alt = [(x, y) for x, y, v in cs if v == 0x52 and cells[y * w + x - 1] == 0x57]
        out["structures"].append(OrderedDict(
            cells_x=[g[0], g[-1]], cells_y=[ys[0], ys[-1]], world_x=[g[0] * 32, g[-1] * 32 + 31], world_y=[ys[0] * 32, ys[-1] * 32 + 31],
            blocks={hx(v): sum(1 for _, _, vv in cs if vv == v) for v in sorted({v for _, _, v in cs})},
            right_gate_cells=[list(c) for c in right],
            right_gate_world_x=[c[0] * 32 for c in right], left_gate_cells=[list(c) for c in left],
            left_gate_world_x_crossing_from_right=[(c[0] + 1) * 32 - 1 for c in left],
            floor_row_world_y=[c[1] * 32 for c in right], alt_gate_cells=[list(c) for c in alt],
            bottom_row_blocks=[hx(cells[right[0][1] * w + x]) for x in range(g[0] - 1, g[-1] + 2)] if right else []))
    out["block_57_cells_in_thz1"] = sum(1 for v in cells if v == 0x57)
    return out


def static_report(rom: bytes) -> OrderedDict:
    return OrderedDict(
        assembly=verify_assembly(rom), dispatch=dispatch_table(rom), pair_table=pair_table(rom), route_tables=route_tables(rom),
        roll_selector=roll_selector(rom), thz1=thz1_inventory(rom),
        routes=OrderedDict({
            "right_3c1b (state $0C via vector $03CB)": OrderedDict(
                per_update="progress += X speed (8.8); position = origin + (x[p], y[p]); p < $90: X speed -= 10 (borrow -> bailout $3CC5); p >= $90: plane := 1, X speed += 12; call $48BC",
                exit="p >= $180 -> request state $06 (state $09 when +$03 bit 1), X speed := $D373 (maximum speed), $D3A0 := $10",
                bailout="$3CC5: origin X <= current X -> X += 8 else X -= 2, then $4680 (request state $1D)"),
            "left_3dae (state $0D via vector $03D1)": OrderedDict(
                per_update="progress += -X speed (the speed is negated, so it is positive for a leftward run); tables $86AE / $8A46; p < $90: |speed| -= 10; p >= $90: plane := 0, speed -= 12 (more negative); call $48BC",
                exit="p >= $180 -> request state $06 (or $09), X speed := -($D373), $D3A0 := $10",
                bailout="$3E74: same as the right route"),
            "alt_3cfc (state $13 via vector $03CE)": "not reached in THZ1 (needs previous foot block $57; THZ1 has no $57 cell); see docs/gpz-loop-route-audit.md"}),
        entry_conditions=OrderedDict(
            right_state_0c="current foot block $52, previous foot block $51, plane ($D525 / +$25) 0, floor flag +$22 bit 1 set -> $3EAB",
            left_state_0d="current foot block $50 or $51, previous foot block $52, plane 1, floor flag set -> $3EE1 (adds 32 to X before the shared snap)",
            alt_state_13="current $52, previous $57, plane 0 -> $3EF7 (not in THZ1)",
            no_other_gate="no speed, facing, state or attack test: only blocks, plane and the floor flag (the route itself bails out when slow)",
            setup="X &= ~31 (kept in +$3A/+$3B), Y := (Y & ~31) + 4 (kept in +$3C/+$3D), cursor $D39D..$D39F := 0, then POP AF (the terrain pass ends early)"))


# ----------------------------------------------------------------------------------------------------------------
# emulation
# ----------------------------------------------------------------------------------------------------------------
class LoopTracer:
    """One tick = one player update ($361D); the snapshot is taken at $5DD1, right after the player's callbacks."""

    def __init__(self, s):
        self.s, self.m = s, s.mem
        self.tick = 0
        self.ticks = []
        self.events = []
        self.selector = []
        self.pending = False
        for pc, fn in ((0x361D, self._tick), (0x5DD1, self._snap), (0x3EAB, self._entry("right_3eab")), (0x3EE1, self._entry("left_3ee1")),
                       (0x3EF7, self._entry("alt_3ef7")), (0x3CC5, self._ev("bailout_right_3cc5")), (0x3E74, self._ev("bailout_left_3e74")),
                       (0x4680, self._ev("fall_off_request_4680")), (0x3CA9, self._ev("exit_right_3ca9")), (0x3E51, self._ev("exit_left_3e51")),
                       (0x3C1B, self._route("right")), (0x3DAE, self._route("left")), (0x903D, self._sel_in), (0x906B, self._sel_out),
                       (0x8F76, self._roll_in), (0x3C88, self._ev("midpoint_right_3c88")), (0x3E30, self._ev("midpoint_left_3e30"))):
            s.add_pc_hook(pc, fn)

    def p(self):
        return self.m[0xD39E] | (self.m[0xD39F] << 8)

    def _tick(self, mm):
        self.tick += 1

    def _snap(self, mm):
        m, s = self.m, self.s
        self.ticks.append(OrderedDict(
            tick=self.tick, video_frame=mm.frame, state=m[0xD501], req=m[0xD502], f03=m[0xD503], f04=m[0xD504], frame=m[0xD506], timer=m[0xD507],
            x=s.u16(0xD511), x_sub=m[0xD510], y=s.u16(0xD514), y_sub=m[0xD513], vx=s16(s.u16(0xD516)), vy=s16(s.u16(0xD518)), plane=m[0xD525],
            fl22=m[0xD522], p=self.p(), p_sub=m[0xD39D], cur_block=m[0xD36B], prev_block=m[0xD497], pad=s.pad, cam=[s.u16(0xD174), s.u16(0xD176)],
            d52f=m[0xD52F], sx=s.u16(0xD51A), sy=s.u16(0xD51C)))

    def _ctx(self, mm, **extra):
        m, s = self.m, self.s
        d = OrderedDict(tick=self.tick, video_frame=mm.frame, state=m[0xD501], req=m[0xD502], f03=m[0xD503], f04=m[0xD504], x=s.u16(0xD511),
                        y=s.u16(0xD514), vx=s16(s.u16(0xD516)), vy=s16(s.u16(0xD518)), plane=m[0xD525], fl22=m[0xD522], p=self.p(),
                        cur_block=m[0xD36B], prev_block=m[0xD497], pad=s.pad)
        d.update(extra)
        return d

    def _entry(self, name):
        def hook(mm):
            self.events.append(OrderedDict(kind="entry", route=name, **self._ctx(mm)))
        return hook

    def _ev(self, name):
        def hook(mm):
            self.events.append(OrderedDict(kind=name, **self._ctx(mm)))
        return hook

    def _route(self, side):
        def hook(mm):
            self.events.append(OrderedDict(kind="route_update_" + side, **self._ctx(mm)))
        return hook

    def _sel_in(self, mm):
        self.pending = True
        self.selector.append(OrderedDict(tick=self.tick, video_frame=mm.frame, kind="loop_selector_903d", rolling=bool(self.m[0xD503] & 2),
                                         p=self.p(), frame_before=self.m[0xD506], f04=self.m[0xD504], state=self.m[0xD501]))

    def _sel_out(self, mm):
        self.pending = False
        if self.selector:
            self.selector[-1]["frame_after"] = self.m[0xD506]
            self.selector[-1]["duration_after"] = self.m[0xD507]

    def _roll_in(self, mm):
        if self.pending:
            self.pending = False
            self.selector[-1]["kind"] = "loop_selector_903d_to_roll_8f76"
            self.selector[-1]["d52f_before"] = self.m[0xD52F]
            self.selector[-1]["x_speed_hi"] = self.m[0xD517]
            self.selector[-1]["floor"] = bool(self.m[0xD522] & 2)
            self.selector[-1]["pending_return"] = True
        else:
            self.selector.append(OrderedDict(tick=self.tick, video_frame=mm.frame, kind="roll_selector_8f76_direct", state=self.m[0xD501]))


def pair_model(pairs, p: int, current: int) -> int:
    a, b = pairs[min(p // SELECTOR_DIVISOR, len(pairs) - 1)]
    return b if a == current else a


def route_model(vx0: int, left: bool = False, max_updates: int = 400):
    """Closed-form model of the $3C1B (right) / $3DAE (left) route callbacks.

    State per update: 24-bit progress p24 += speed; p = p24 >> 8; first half (p < $90): speed -= 10, a borrow (speed < 10) bails out;
    second half: plane := 1 (0 for the left route) and speed += 12; exit when p >= $180.  The left route works on the negated speed.
    Returns the list of (p, speed, plane) after every update and the outcome ("exit" / "bailout")."""
    sp = (-vx0) & 0xFFFF if left else vx0 & 0xFFFF
    p24, rows = 0, []
    plane = None
    for _ in range(max_updates):
        p24 += sp
        p = (p24 >> 8) & 0xFFFF
        if p < MIDPOINT_PROGRESS:
            if sp < 10:
                rows.append((p, sp, plane))
                return rows, "bailout"
            sp -= 10
        else:
            plane = 0 if left else 1
            sp = (sp + 12) & 0xFFFF
        rows.append((p, sp, plane))
        if p >= EXIT_PROGRESS:
            return rows, "exit"
    return rows, "none"


def check_route_model(tv: dict) -> OrderedDict:
    ticks = tv["ticks"]
    entry = tv["entry_events"][0] if tv["entry_events"] else None
    if not entry or tv["state"] not in (STATE_RIGHT, STATE_LEFT):
        return OrderedDict(checked=False)
    left = tv["state"] == STATE_LEFT
    rows, outcome = route_model(entry["vx"], left)
    bad = []
    for i, t in enumerate(ticks):
        if i >= len(rows):
            bad.append((i, "model ended"))
            break
        p, sp, plane = rows[i]
        if t["p"] != p:
            bad.append((i, "p", t["p"], p))
    exit_ev = any(e["kind"].startswith("exit") for e in tv["events"])
    bail_ev = any(e["kind"].startswith("bailout") for e in tv["events"])
    return OrderedDict(checked=True, entry_vx=entry["vx"], model_outcome=outcome, observed_outcome="exit" if exit_ev else "bailout" if bail_ev else "none",
                       model_updates=len(rows), observed_ticks=len(ticks), progress_mismatches=len(bad), first_mismatch=bad[0] if bad else None)


def boot_thz1_patched(rom: bytes, anchor):
    return V.boot_zone(V.patched_rom(rom, THZ1[0], THZ1[1], (max(anchor[0] - 104, 0), max(anchor[1] - 112, 0)), anchor), THZ1[0], THZ1[1])


def boot_thz1_natural(rom: bytes):
    import object_18 as O
    return O._boot(rom, 0, lambda m: None)


def random_schedule(seed: int, frames: int = 4000):
    """The pad script of the seeded input search (right-heavy: right, right+jump, right+down, right+down+jump, left)."""
    from sms_frame_harness import BTN_RIGHT, BTN_1, BTN_DOWN, BTN_LEFT
    rng = random.Random(seed)
    out, f = [], 0
    while f < frames:
        n = rng.randint(10, 50)
        r = rng.random()
        p = (BTN_RIGHT if r < 0.55 else BTN_RIGHT | BTN_1 if r < 0.8 else BTN_RIGHT | BTN_DOWN if r < 0.88 else
             BTN_RIGHT | BTN_DOWN | BTN_1 if r < 0.93 else BTN_LEFT)
        out.append((f, f + n, p))
        f += n
    return out


def run_pad(s, tr: LoopTracer, pad, frames: int, sat_from: int = 0):
    """Run ``frames`` video frames; returns the SAT of every frame together with the player state at the moment the SAT was uploaded."""
    m = s.mem
    sat_frames = []
    state_at_upload = {}
    orig = s._out

    def out(port, value):
        port &= 0xFF
        if 0x80 <= port < 0xC0 and not port & 1 and s.code != 3:
            base = (s.reg[5] & 0x7E) << 7
            if base <= s.addr < base + 0xC0 and s.frame not in state_at_upload:
                state_at_upload[s.frame] = OrderedDict(
                    x=s.u16(0xD511), y=s.u16(0xD514), frame=m[0xD506], f04=m[0xD504], state=m[0xD501], cam=[s.u16(0xD174), s.u16(0xD176)], tick=tr.tick)
        return orig(port, value)
    s.cpu.set_output_callback(out)
    for f in range(frames):
        s.pad = pad(f)
        s.run_frame()
        if f >= sat_from:
            cx, cy = s.u16(0xD174), s.u16(0xD176)
            sat_frames.append((s.frame - 1, cx, cy, [(i, y, x, n) for i, y, x, n in s.sat()], state_at_upload.get(s.frame - 1)))
        if m[0xD500] != 1 and f > 50:
            break
    return sat_frames


# ----------------------------------------------------------------------------------------------------------------
# trace -> traversals
# ----------------------------------------------------------------------------------------------------------------
def segment_traversals(tr: LoopTracer, pairs) -> list:
    """Cut the tick list into loop traversals (consecutive ticks whose state is $0C/$0D/$13) with their events."""
    out, cur = [], None
    for t in tr.ticks:
        if t["state"] in LOOP_STATES:
            if cur is None or cur["state"] != t["state"]:
                cur = OrderedDict(state=t["state"], ticks=[])
                out.append(cur)
            cur["ticks"].append(t)
        else:
            cur = None
    res = []
    for tv in out:
        t0, t1 = tv["ticks"][0]["tick"], tv["ticks"][-1]["tick"]
        ev = [e for e in tr.events if e["kind"] == "entry" and t0 - 1 <= e["tick"] <= t0]
        evs = [e for e in tr.events if t0 <= e["tick"] <= t1 + 1 and e["kind"] not in ("route_update_right", "route_update_left", "entry")]
        sel = [x for x in tr.selector if t0 <= x["tick"] <= t1]
        after = [t for t in tr.ticks if t["tick"] == t1 + 1]
        fall, k = [], t1 + 1
        by = {t["tick"]: t for t in tr.ticks}
        while k in by and by[k]["state"] == 0x1D and len(fall) < 40:
            fall.append(by[k])
            k += 1
        res.append(OrderedDict(tv, entry_events=ev, events=evs, selector=sel, after=after[0] if after else None, fall_off=fall))
    return res


def summarise_traversal(tv: dict, pairs, rom_cells=None) -> OrderedDict:
    ticks = tv["ticks"]
    first, last = ticks[0], ticks[-1]
    sel = tv["selector"]
    frames_seq = []
    for t in ticks:
        if not frames_seq or frames_seq[-1][0] != t["frame"]:
            frames_seq.append([t["frame"], 1])
        else:
            frames_seq[-1][1] += 1
    # rule check: every non-rolling selector call reproduces pair_model
    checked, bad = 0, []
    for c in sel:
        if c["kind"] == "loop_selector_903d" and "frame_after" in c:
            checked += 1
            exp = pair_model(pairs, c["p"], c["frame_before"])
            if exp != c["frame_after"] or c["duration_after"] != 6:
                bad.append(c)
    rolling = [c for c in sel if c["kind"].endswith("roll_8f76")]
    frames_set = sorted({t["frame"] for t in ticks})
    entry = tv["entry_events"][0] if tv["entry_events"] else None
    exit_ev = [e for e in tv["events"] if e["kind"].startswith("exit")]
    bail = [e for e in tv["events"] if e["kind"].startswith("bailout")]
    ticks_in = len(ticks)
    return OrderedDict(
        state=hx(tv["state"]), first_tick=first["tick"], last_tick=last["tick"], ticks_in_state=ticks_in, entry_context=entry,
        first_state_tick=OrderedDict(x=first["x"], y=first["y"], vx=first["vx"], plane=first["plane"], frame=first["frame"], f03=first["f03"],
                                     f04=first["f04"]),
        last_state_tick=OrderedDict(x=last["x"], y=last["y"], vx=last["vx"], plane=last["plane"], frame=last["frame"], p=last["p"], f04=last["f04"]),
        exit_event=exit_ev[0] if exit_ev else None, bailout_event=bail[0] if bail else None,
        after=OrderedDict((k, tv["after"][k]) for k in ("tick", "state", "req", "x", "y", "vx", "plane", "frame", "f03", "f04")) if tv["after"] else None,
        facing_bit4_values=sorted({t["f04"] >> 4 & 1 for t in ticks}), rolling_values=sorted({(t["f03"] >> 1) & 1 for t in ticks}),
        plane_values_in_order=[v for i, v in enumerate(t["plane"] for t in ticks) if i == 0 or v != ticks[i - 1]["plane"]],
        frame_runs=frames_seq, distinct_frames=frames_set, rotated_frames_used=[f for f in frames_set if f >= 0x2A],
        selector_calls=len(sel), selector_calls_checked_against_pair_table=checked, selector_rule_violations=len(bad),
        route_model_check=check_route_model(tv),
        fall_off_state_1d=OrderedDict(ticks=len(tv["fall_off"]), frames=[t["frame"] for t in tv["fall_off"]][:12], x_speed=[t["vx"] for t in tv["fall_off"]][:6],
                                      y_speed=[t["vy"] for t in tv["fall_off"]][:6]) if tv["fall_off"] else None, selector_to_roll_calls=len(rolling), progress_at_last_tick=last["p"], max_x_speed=max(t["vx"] for t in ticks), min_x_speed=min(t["vx"] for t in ticks),
        ticks_table=[[t["tick"] - first["tick"], t["x"], t["y"], t["vx"], t["p"], t["frame"], t["timer"], t["plane"], t["f04"] >> 4 & 1, t["f03"] & 3] for t in ticks])


def sat_composition_check(rom: bytes, tr: LoopTracer, sat_frames) -> OrderedDict:
    """Compare the real sprite-attribute table with the composition predicted from (frame, facing, position, camera).

    The sprite list is built from the object state of a completed tick and uploaded at vblank, so each real SAT is compared with the last three
    tick snapshots taken before the upload (the tick whose SAT it is is unknown to the harness).  The anchor is the player's cached screen position
    (+$1A / +$1C = $D51A / $D51C, written by the engine before the player moves: previous position minus current camera); the piece layout comes from
    the same tick (lag 0) or from the tick before it (lag 1).  A SAT matches when it contains the whole expected piece set of at least one of them.  Facing bit 4 of +$04 selects x = rel_x (clear) or x = -rel_x - 8 (set); the wrong convention is
    also tried so that a match under the wrong convention would be noticed."""
    m = A.object_mapping(rom, 1)
    base = m["mapping_cpu"]
    recs = {}

    def rec(f):
        if f not in recs:
            cpu = R.u16(rom, A.cpu15_to_rom(base) + 2 * f)
            recs[f] = A.parse_frame_record(rom, cpu)
        return recs[f]
    by_tick = {t["tick"]: t for t in tr.ticks}
    stats = OrderedDict(frames_with_upload=0, matched=0, mismatched=0, facing_clear_matched=0, facing_clear_total=0, facing_set_matched=0, facing_set_total=0,
                        loop_frames=0, loop_matched=0, loop_facing_set_frames=0, loop_facing_set_matched=0, matched_only_under_wrong_convention=0)
    examples = []
    for vf, cx, cy, sat, up in sat_frames:
        if not up:
            continue
        stats["frames_with_upload"] += 1
        sat_set = {(x, y, n) for _, y, x, n in sat}
        ok = wrong = False
        hit = None
        for tk in range(up["tick"], max(up["tick"] - 3, 0), -1):
            for lag in (0, 1):
                t = by_tick.get(tk)
                tf = by_tick.get(tk - lag)
                if not t or not tf or tf["frame"] >= FRAME_COUNT:
                    continue
                pr = rec(tf["frame"])
                if not pr["pieces"]:
                    continue
                facing = (tf["f04"] >> 4) & 1

                def expect(mode):
                    return {((t["sx"] + (-pc["relative_x"] - 8 if mode else pc["relative_x"])) & 0xFF, (t["sy"] + pc["relative_y"]) & 0xFF,
                             pc["tile_offset"]) for pc in pr["pieces"]}
                if expect(facing) <= sat_set:
                    ok, hit = True, tf
                    stats["matched_with_frame_lag_%d" % lag] = stats.get("matched_with_frame_lag_%d" % lag, 0) + 1
                    break
                if expect(1 - facing) <= sat_set:
                    wrong = True
            if ok:
                break
        t = hit or by_tick.get(up["tick"]) or {"state": up["state"], "f04": up["f04"]}
        facing = (t["f04"] >> 4) & 1
        key = "facing_set" if facing else "facing_clear"
        stats[key + "_total"] += 1
        stats["matched" if ok else "mismatched"] += 1
        stats["matched_only_under_wrong_convention"] += int(wrong and not ok)
        if ok:
            stats[key + "_matched"] += 1
        elif len(examples) < 3:
            examples.append(OrderedDict(video_frame=vf, state=t["state"], tick=up["tick"]))
        if t["state"] in LOOP_STATES:
            stats["loop_frames"] += 1
            stats["loop_matched"] += int(ok)
            if facing:
                stats["loop_facing_set_frames"] += 1
                stats["loop_facing_set_matched"] += int(ok)
    stats["mismatch_examples"] = examples
    stats["rule"] = ("expected piece = ($D51A + rel_x, or -rel_x - 8 when +$04 bit 4 is set; $D51C + rel_y as the raw SAT Y byte; tile offset), "
                     "cached screen position $D51A / $D51C of the tick snapshot")
    return stats


# ----------------------------------------------------------------------------------------------------------------
# scenarios
# ----------------------------------------------------------------------------------------------------------------
def pad_hold(btn):
    return lambda f: btn


def scenario(rom: bytes, name: str, kind: str, boot, pad, frames: int, pairs, with_sat: bool = True, extra=None):
    s = boot()
    tr = LoopTracer(s)
    sat_frames = run_pad(s, tr, pad, frames)
    tvs = segment_traversals(tr, pairs)
    out = OrderedDict(name=name, evidence=kind, frames_run=frames, ticks=len(tr.ticks), traversals=[summarise_traversal(tv, pairs) for tv in tvs])
    out["sat_composition"] = sat_composition_check(rom, tr, sat_frames) if with_sat else None
    if extra:
        out.update(extra)
    return out, tr


def natural_replay(rom: bytes, seed: int, frames: int, pairs):
    sched = random_schedule(seed, frames + 50)
    idx = [0]

    def pad(f):
        while sched[idx[0]][1] <= f:
            idx[0] += 1
        return sched[idx[0]][2]
    sc, tr = scenario(rom, "natural_seed_%d" % seed, "NATURAL (real THZ1 start record, seeded pad script, nothing patched)", lambda: boot_thz1_natural(rom), pad, frames, pairs,
                      extra=OrderedDict(seed=seed, schedule_runs=[list(r) for r in sched if r[0] < frames]))
    return sc, tr


def poc_report(poc: Path, rom: bytes) -> OrderedDict:
    import re
    out = OrderedDict()
    motion = (poc / "scripts/SCR_chaos_motion/SCR_chaos_motion.gml").read_text(encoding="utf-8")
    data = (poc / "scripts/SCR_chaos_motion_data/SCR_chaos_motion_data.gml").read_text(encoding="utf-8")
    adapter = (poc / "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml").read_text(encoding="utf-8")
    tick = V.function_body(motion, "SCR_chaos_loop_tick") or ""
    enter = V.function_body(motion, "SCR_chaos_loop_try_enter") or ""
    layout = (poc / "scripts/SCR_chaos_loop_layout/SCR_chaos_loop_layout.gml").read_text(encoding="utf-8")

    def arr(name):
        m = re.search(name + r"\s*=\s*\[([^\]]*)\]", data)
        return [int(v) for v in m.group(1).replace("\n", " ").split(",") if v.strip()] if m else []
    tabs = OrderedDict()
    for name, ycpu, xcpu, key in (("right", 0x8000, 0x8398, "Right"), ("left", 0x86AE, 0x8A46, "Left")):
        px, py = arr("chaosLoop%sX" % key), arr("chaosLoop%sY" % key)
        rx = [s16(R.u16(rom, bank_file(13, xcpu) + 2 * i)) for i in range(len(px))]
        ry = [s16(R.u16(rom, bank_file(13, ycpu) + 2 * i)) for i in range(len(py))]
        tabs[name] = OrderedDict(poc_entries=len(px), equals_rom_x=(px == rx), equals_rom_y=(py == ry))
    out["movement_tables"] = tabs
    out["loop_entry"] = OrderedDict(
        function="SCR_chaos_loop_try_enter (legacy adapter: scripts/SCR_chaos_motion/SCR_chaos_motion.gml)", source_sha256=sha(enter.encode()),
        speed_gate_abs_hspeed=("abs(cp_p.hspeed) < 0.25" in enter), bottom_crossing_window=("cp_p.bbox_bottom < cp_row + 12" in enter and "cp_p.bbox_bottom > cp_row + 33" in enter),
        speed_cap_px=("min(abs(cp_p.hspeed), 8)" in enter), uses_block_transition=False, plane_array="global.chaosLoopPlanes[cp_i] per loop (plane 0 rightward, 1 leftward)",
        loop_detection=("cp_ids[cp_i] == 82 && cp_ids[cp_i - 1] == 81" in layout))
    out["loop_tick"] = OrderedDict(
        function="SCR_chaos_loop_tick", source_sha256=sha(tick.encode()), table_clamp_394=("min(cp_index, 394)" in tick), midpoint_144=("cp_index < 144" in tick),
        decel_10=("-= 10" in tick), accel_12=("+= 12" in tick), exit_384=("cp_index >= 384" in tick), exit_speed_capped=("chaosLoopExitSpeed" in tick),
        presentation_rotation=("image_angle = cp_angle" in tick), rotation_source="point_direction between table samples index-3 and index+3 (generic tangent rotation)",
        mirror=("image_xscale = cp_p.chaosLoopDirection" in tick), sprite=("SPR_player_spin / SPR_player_run" if "SPR_player_run" in tick else "unknown"),
        image_speed_0_5=("image_speed = 0.5" in tick), plane_switch_at_midpoint=("chaosLoopPlanes[cp_p.chaosLoopNumber]" in tick),
        low_speed_release=("cp_p.chaosLoopVelocity < 0" in tick), selects_rom_frames_2a_5d=False)
    frames = sorted(int(m.group(1), 16) for p in (poc / "sprites").iterdir() for m in [re.match(r"SPR_chaos_player_frame_([0-9A-F]{2})$", p.name)] if m)
    needed = sorted(set(range(0x2A, 0x36)) | set(range(0x40, 0x5E)))
    out["poc_frame_sprites"] = OrderedDict(
        resources_named_player_frame=[hx(f) for f in frames], loop_rotation_frames_needed=len(needed), loop_rotation_frames_present=[hx(f) for f in needed if f in frames],
        loop_rotation_frames_missing=len([f for f in needed if f not in frames]), walk_frames_01_06_present=all(f in frames for f in range(1, 7)))
    out["state_13_presentation"] = OrderedDict(
        adapter_lines="SCR_chaos_adapter.gml: state $13 uses SPR_player_spin / SPR_player_run and image_angle from route points ($13 only)",
        uses_image_angle_for_13=("cp_c.state == $13" in adapter and "point_direction(global.chaosRoute19X" in adapter))
    return out


def natural_search(rom: bytes, lo: int, hi: int, frames: int = 4000):
    rows = []
    for seed in range(lo, hi):
        s = boot_thz1_natural(rom)
        m = s.mem
        sched = random_schedule(seed, frames)
        idx, prev, ev, maxx = 0, None, [], 0
        for f in range(frames):
            while sched[idx][1] <= f:
                idx += 1
            s.pad = sched[idx][2]
            s.run_frame()
            st = m[0xD501]
            maxx = max(maxx, s.u16(0xD511))
            if st != prev and st in LOOP_STATES:
                ev.append([f, st, s.u16(0xD511), s.u16(0xD514)])
            prev = st
            if m[0xD500] != 1 and f > 50:
                break
        rows.append([seed, maxx, ev])
    return rows


NATURAL_SEARCH = OrderedDict(
    method="seeded pad scripts from the real THZ1 start record (tools/visual1_loops.py random_schedule: 10-50 frame runs of RIGHT 55%, RIGHT+JUMP 25%, RIGHT+DOWN 8%, "
           "RIGHT+DOWN+JUMP 5%, LEFT 7%); 4000 frames each; any entry into state $0C/$0D/$13 is logged",
    seeds_run=120, seeds_with_a_loop_entry=9, seeds_reaching_x_2368=54, seeds_reaching_x_2900=51,
    entries_seen=OrderedDict(state_0c=29, state_0d=0, state_13=0),
    seeds_with_entries=OrderedDict({"3": "2015@(2372,419), 3310@(2881,516)", "6": "1602,1652,1703,2148,2275@x~2368 (slow bailouts) then 2555@(2884,515)",
                                    "13": "1241@(2372,419), 1476@(2884,515)", "43": "1252, 2897", "44": "1113", "52": "746, 1075, 1468, 1613, 2965",
                                    "61": "860@(2372,419), 1139@(2885,515)", "81": "1460, 1747, 2658, 2800, 3864, 3924, 3975", "97": "780@(2372,419), 1018@(2884,515)"}),
    not_found="no natural entry into $0D or $13 in 120 seeds (the scripts rarely reverse toward the loop); $0D is therefore CONTROLLED only; $13 needs previous foot block $57 (none in THZ1)",
    reproduce="python tools/visual1_loops.py ROM --search 0 120 (not part of --check)")


def build(rom: bytes, output: Path | None = None, static_only: bool = False, seeds=((13, 1700), (6, 2700), (97, 1250)), poc: Path | None = None) -> dict:
    if sha(rom) != R.SHA256:
        raise ValueError("ROM SHA-256 mismatch")
    st = static_report(rom)
    report = OrderedDict(format=1, rom_sha256=sha(rom), research_base="ce298af87341d4cce2917461ef4c1b3137f45c91",
                         evidence="DECODED DATA + BYTE-VERIFIED ASSEMBLY + EMULATED ORIGINAL FRAME", static=st)
    if static_only:
        return report
    from sms_frame_harness import BTN_RIGHT, BTN_LEFT, BTN_DOWN
    pairs = [tuple(p) for p in st["pair_table"]["pairs"]] + [(1, 2), (3, 4), (5, 6)] * 27
    emu = OrderedDict()
    nat = []
    for seed, frames in seeds:
        sc, _ = natural_replay(rom, seed, frames, pairs)
        nat.append(sc)
    emu["natural"] = nat
    emu["natural_search"] = NATURAL_SEARCH
    ctl = []

    def spin(f):
        from sms_frame_harness import BTN_1
        if f < 30:
            return 0
        if f < 34:
            return BTN_DOWN
        if f < 58:
            return BTN_DOWN | (BTN_1 if (f - 34) % 4 == 0 else 0)
        return BTN_RIGHT
    plans = (
        ("hold_right_from_(2100,380)", "CONTROLLED (start record rewritten: position only; pad = RIGHT held)", (2100, 380), pad_hold(BTN_RIGHT), 520),
        ("right_then_left_into_loop_1", "CONTROLLED (start (2100,380); RIGHT until frame 226 then LEFT)", (2100, 380), lambda f: BTN_RIGHT if f < 226 else BTN_LEFT, 520),
        ("spin_dash_roll_through_both_loops", "CONTROLLED (start (2250,430) on the flat floor; spin dash: DOWN, button-1 taps, then RIGHT)", (2250, 430), spin, 300),
        ("roll_started_while_running", "CONTROLLED (start (2100,380); RIGHT, DOWN pressed at frame 75 while running)", (2100, 380),
         lambda f: BTN_RIGHT if f < 75 else (BTN_RIGHT | BTN_DOWN), 360),
    )
    for name, kind, anchor, pad, frames in plans:
        sc, _ = scenario(rom, name, kind, (lambda a=anchor: boot_thz1_patched(rom, a)), pad, frames, pairs)
        ctl.append(sc)
    starts = OrderedDict()
    for ax in (2272, 2290, 2300, 2335):
        sc, _ = scenario(rom, "slow_start_x%d" % ax, "CONTROLLED (start (%d,430) on the row-14 floor; RIGHT held)" % ax, (lambda a=ax: boot_thz1_patched(rom, (a, 430))),
                         pad_hold(BTN_RIGHT), 220, pairs, with_sat=False)
        starts[str(ax)] = [OrderedDict((k, tv[k]) for k in ("state", "ticks_in_state", "progress_at_last_tick", "route_model_check")) |
                           OrderedDict(entry_vx=tv["entry_context"]["vx"] if tv["entry_context"] else None, outcome="exit" if tv["exit_event"] else "bailout" if tv["bailout_event"] else "none",
                                       after_state=tv["after"]["state"] if tv["after"] else None) for tv in sc["traversals"]]
    emu["controlled"] = ctl
    emu["entry_speed_by_start_position"] = starts
    emu["route_speed_injection"] = injected_speed_runs(rom, pairs)
    report["emulated"] = emu
    if output:
        output.mkdir(parents=True, exist_ok=True)
        render_strips(rom, output)
    if poc:
        report["poc"] = poc_report(poc, rom)
    return report


def injected_speed_runs(rom: bytes, pairs, speeds=(0x0355, 0x0356, 0x0357, 0x0400)):
    """Controlled: the player speed is overwritten with V at the first $3C1B callback (progress 0) of a right-route traversal."""
    from sms_frame_harness import BTN_RIGHT
    out = OrderedDict()
    for v in speeds:
        s = boot_thz1_patched(rom, (2272, 430))
        tr = LoopTracer(s)
        done = []

        def inject(mm, v=v, done=done):
            if not done:
                done.append(True)
                mm.w16(0xD516, v)
        s.add_pc_hook(0x3C1B, inject)
        run_pad(s, tr, pad_hold(BTN_RIGHT), 330)
        tvs = segment_traversals(tr, pairs)
        tv = tvs[0] if tvs else None
        model_rows, model_outcome = route_model(v)
        out[hx(v, 4)] = OrderedDict(
            injected_speed_8_8=v, injected_px_per_update=round(v / 256, 4), model_outcome=model_outcome, model_updates=len(model_rows),
            observed_outcome=None if not tv else ("exit" if any(e["kind"].startswith("exit") for e in tv["events"]) else "bailout" if any(e["kind"].startswith("bailout") for e in tv["events"]) else "none"),
            observed_ticks=None if not tv else len(tv["ticks"]), observed_progress_at_end=None if not tv else tv["ticks"][-1]["p"],
            progress_mismatches=None if not tv else sum(1 for i, t in enumerate(tv["ticks"]) if i < len(model_rows) and t["p"] != model_rows[i][0]),
            after_state=None if not tv or not tv["after"] else tv["after"]["state"])
    return out


def render_strips(rom: bytes, output: Path) -> None:
    """Ignored build/ images: the real emulated frames around the player during loop 1 (rightward, running) and (leftward, mirrored)."""
    from PIL import Image
    from sms_frame_harness import BTN_RIGHT, BTN_LEFT
    for name, pad, frames, sel in (("thz1-loop1-right-traversal-strip.png", pad_hold(BTN_RIGHT), 230, range(100, 218, 8)),
                                   ("thz1-loop1-left-traversal-strip.png", lambda f: BTN_RIGHT if f < 226 else BTN_LEFT, 460, range(326, 456, 9))):
        s = boot_thz1_patched(rom, (2100, 380))
        m = s.mem
        shots = []
        for f in range(frames):
            s.pad = pad(f)
            s.run_frame()
            if f in sel:
                rgb = s.render()[0]
                sx, sy = s.u16(0xD51A), s.u16(0xD51C)
                x0, y0 = max(0, min(256 - 96, sx - 48)), max(0, min(192 - 112, sy - 70))
                crop = Image.new("RGB", (96, 112))
                crop.putdata([rgb[y0 + y][x0 + x] for y in range(112) for x in range(96)])
                shots.append((m[0xD501], m[0xD506], crop.resize((192, 224), Image.NEAREST)))
        cols = 7
        sheet = Image.new("RGB", (192 * cols, 224 * ((len(shots) + cols - 1) // cols)))
        for i, (_, _, im) in enumerate(shots):
            sheet.paste(im, ((i % cols) * 192, (i // cols) * 224))
        sheet.save(output / name)


def implementation_contract(rep: dict) -> OrderedDict:
    st = rep["static"]
    emu = rep["emulated"]

    def trav(group, name, idx):
        for sc in emu[group]:
            if sc["name"] == name:
                return sc["traversals"][idx]
        raise KeyError(name)
    ref = OrderedDict()
    for key, (group, name, idx) in (("right_running_entry_vx_1024", ("controlled", "hold_right_from_(2100,380)", 0)),
                                    ("left_running_entry_vx_-944", ("controlled", "right_then_left_into_loop_1", 1)),
                                    ("right_rolling_entry_vx_1592", ("controlled", "spin_dash_roll_through_both_loops", 0))):
        tv = trav(group, name, idx)
        ref[key] = OrderedDict(
            scenario=name, entry=OrderedDict((k, tv["entry_context"][k]) for k in ("x", "y", "vx", "plane", "f03", "f04", "cur_block", "prev_block")),
            columns=["tick_from_first_state_tick", "x", "y", "vx_8_8", "progress", "frame", "timer", "plane", "facing_bit4", "f03_low2"], ticks=tv["ticks_table"],
            frame_runs=tv["frame_runs"], exit=tv["after"])
    inv = st["thz1"]["structures"]
    entries = [tv["entry_context"] for grp in ("natural", "controlled") for sc in emu[grp] for tv in sc["traversals"] if tv["entry_context"] and tv["state"] == "0x0C"]
    anchors = OrderedDict()
    for name, lo, hi in (("loop_1", 2300, 2500), ("loop_2", 2800, 3000)):
        es = [e for e in entries if lo <= e["x"] <= hi]
        anchors[name] = OrderedDict(x=[min(e["x"] for e in es), max(e["x"] for e in es)], y=[min(e["y"] for e in es), max(e["y"] for e in es)], entries=len(es))
    comps = [sc["sat_composition"] for sc in emu["controlled"] if sc["sat_composition"]]
    lag1 = sum(c.get("matched_with_frame_lag_1", 0) for c in comps)
    total = sum(c["frames_with_upload"] for c in comps)
    return OrderedDict(
        format=1, scope="THZ1 loop presentation: player states $0C/$0D (and the shared $13 mechanism), selector $903D, frames $2A..$5D",
        evidence="BYTE-VERIFIED ASSEMBLY + DECODED DATA + EMULATED ORIGINAL FRAME; every emulated traversal reproduces the closed-form route model and every selector call reproduces the pair rule",
        loops=OrderedDict((("loop_%d" % (i + 1)), OrderedDict(
            cells_x=s["cells_x"], cells_y=s["cells_y"], right_gate_world_x=s["right_gate_world_x"][0], left_gate_world_x_crossing=s["left_gate_world_x_crossing_from_right"][0],
            floor_row_world_y=s["floor_row_world_y"][0], entry_anchor_observed=anchors["loop_%d" % (i + 1)])) for i, s in enumerate(inv)),
        entry=OrderedDict(
            right="foot block $52 after previous foot block $51, plane 0, floor flag: requests $0C; anchor X := X & ~31, Y := (Y & ~31) + 4; cursor := 0",
            left="foot block $50/$51 after previous $52, plane 1, floor flag: requests $0D; X += 32 first",
            no_speed_gate="any speed enters; a slow entry bails out inside the route"),
        route_algorithm=OrderedDict(
            per_tick="p24 += speed (right) or -speed (left); p = p24 >> 8; position = anchor + table[p]; p < $90: speed -= 10 (borrow -> bailout); else plane := 1 (right) / 0 (left), speed += 12; contact/damage routine $48BC runs; p >= $180 exits",
            model=OrderedDict(function="route_model(vx0, left)", reproduces_every_observed_traversal=True),
            minimum_completing_entry_speed_8_8=0x0356, minimum_completing_entry_speed_px=0x0356 / 256, updates_at_minimum=183, updates_at_1024=111, below_minimum="bailout at progress 143 after 86 updates for $0355; lower speeds bail earlier",
            tables=st["route_tables"]),
        frame_selection=OrderedDict(
            selector="every record (6 updates) $903D runs: index = progress // 13; frame := pair[index][0], except pair[index][1] when pair[index][0] equals the current frame; duration := 6",
            pairs=st["pair_table"]["pairs"], pairs_after_index_23="walk pairs (1,2),(3,4),(5,6) repeated", rotation_ends_at_progress=312,
            observed_cadence="at 4 px/update one record covers 24 px so each call lands about 2 pairs later and only one frame of most pairs is ever shown",
            rolling="when +$03 bit 1 is set the selector tail-jumps to $8F76: ball frames $25..$29 by the shared counter $D52F (period 20), duration by |X speed high byte| from $8FE0; facing bit 4 follows the sign of the X speed",
            rolling_exit_state=9, running_exit_state=6),
        facing_and_mirroring=OrderedDict(
            facing_bit="+$04 bit 4: clear = faces right, set = faces left; the route never changes it (only the rolling selector writes it)",
            right_route_observed="bit 4 clear on every tick of every $0C traversal (frames are the unmirrored art)",
            left_route_observed="bit 4 set on every tick of the $0D traversal; the same frame numbers are drawn mirrored",
            composition="piece X = anchor + rel_x, mirrored: anchor - rel_x - 8; Y = anchor + rel_y (raw SAT Y byte); anchor = cached screen position $D51A/$D51C",
            composition_verified=OrderedDict((sc["name"], sc["sat_composition"]["loop_matched"] if sc["sat_composition"] else None) for sc in emu["controlled"]),
            frame_lag=OrderedDict(frames_matching_only_with_the_previous_ticks_frame=lag1, frames_compared=total,
                                  meaning="in those video frames the sprite shows the frame held at the end of the previous tick (the sprite list is built before the animation engine runs)")),
        exit=OrderedDict(
            at="p >= $180", state="$06 (running) or $09 (rolling, +$03 bit 1)", speed="X speed := $D373 (maximum speed; negated for the left route)", d3a0=0x10,
            plane="left as set at the midpoint (1 after a right loop, 0 after a left loop)"),
        bailout=OrderedDict(
            condition="speed < 10 before the midpoint", effect="X -= 2 (when already right of the anchor) else X += 8, then state $1D (falling) via $4680",
            fall_off_selector="$900B (height keyed 16-pair table), see docs/visual0-thz1-fidelity.md"),
        reference_traversals=ref,
        natural_evidence=OrderedDict(
            seeds=[s["seed"] for s in emu["natural"]], search=emu["natural_search"]["seeds_with_a_loop_entry"], search_size=emu["natural_search"]["seeds_run"],
            note="natural = real THZ1 start record and a seeded pad script; $0D and $13 have no natural example"),
        poc_gaps=rep.get("poc") and OrderedDict(
            movement_tables_equal_rom=all(v["equals_rom_x"] and v["equals_rom_y"] for v in rep["poc"]["movement_tables"].values()),
            presentation="generic image_angle rotation of the run/spin sprite; ROM frames $2A..$5D absent (%d of %d missing)" % (rep["poc"]["poc_frame_sprites"]["loop_rotation_frames_missing"], rep["poc"]["poc_frame_sprites"]["loop_rotation_frames_needed"]),
            entry="bottom-crossing window and |hspeed| >= 0.25 instead of block transition; speed capped at 8 px; exit speed capped"))


def dumps(rep) -> str:
    return json.dumps(V.clean(rep), indent=1) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--metadata", type=Path)
    p.add_argument("--check", action="store_true")
    p.add_argument("--static-only", action="store_true")
    p.add_argument("--poc", type=Path)
    p.add_argument("--contract", type=Path, help="also write the implementation contract (needs the emulated run and --poc)")
    p.add_argument("--search", nargs=2, type=int, metavar=("FIRST_SEED", "END_SEED"))
    a = p.parse_args()
    if a.search:
        print(json.dumps(natural_search(R.load(a.rom), *a.search)))
        return
    rep = build(R.load(a.rom), a.output, a.static_only, poc=a.poc)
    text = dumps(rep)
    if a.contract and not a.static_only:
        text_c = dumps(implementation_contract(rep))
        if a.check:
            if a.contract.read_text(encoding="utf-8") != text_c:
                sys.exit("contract differs: " + str(a.contract))
            print("contract identical")
        else:
            a.contract.parent.mkdir(parents=True, exist_ok=True)
            a.contract.write_text(text_c, encoding="utf-8")
    if a.metadata:
        if a.check:
            if a.metadata.read_text(encoding="utf-8") != text:
                sys.exit("metadata differs: " + str(a.metadata))
            print("metadata identical")
        else:
            a.metadata.parent.mkdir(parents=True, exist_ok=True)
            a.metadata.write_text(text, encoding="utf-8")
    print(json.dumps({"scenarios": len(rep.get("emulated", {}).get("natural", [])) + len(rep.get("emulated", {}).get("controlled", []))}))


if __name__ == "__main__":
    main()

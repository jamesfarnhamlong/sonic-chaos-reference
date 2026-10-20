#!/usr/bin/env python3
"""C1-R: targeted EMULATED traces of the original look-up / look-down camera, idle wait and Peel-Out (THZ1, Sonic, unmodified ROM code).

    python tools/c1r_camera_trace.py ROM --write        # regenerate data/c1r/camera-look-trace.json (about 30 s)
    python tools/c1r_camera_trace.py ROM --check        # regenerate in memory and compare with the committed file
    python tools/c1r_camera_trace.py --validate         # no ROM: internal consistency of the committed file

Rows are sampled at every entry of the camera update `$4C90` (one row = one game update, the state BEFORE that update's follow step; the player update of the
same game update has already run).  Harness frames are NOT game updates (lag frames run the engine twice or not at all), so frame-sampled traces are not used.

Evidence class: EMULATED ORIGINAL FRAME (tools/g0_rig.py Session on the approximate SMS harness).  The only inputs are scripted joypad states; no RAM, PC or
bank is written.  One continuous run: a real New Game, THZ1 act 1, Sonic.  Columns are per harness frame (60 Hz frame = one game update here).

RAM read:  D501 state, D502 request, D503 movement byte, D511/D514 player X/Y, D516/D518 X/Y speed (8.8), D174/D176 committed camera,
           D289 Y lead TARGET, D28D working Y lead, D28F/D28E zone bounds, D28A X lead, D137 direction snapshot, D3C0 water flag, D3B1 invulnerability timer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

OUT = ROOT / "data" / "c1r" / "camera-look-trace.json"
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
COLS = ["frame", "state", "req", "move", "px", "py", "vx", "vy", "cam_x", "cam_y", "work_x", "work_y", "lead_x", "lead_y", "lead_target", "face", "pan", "dir_in", "inv_timer"]


def _s16(v):
    return v - 65536 if v >= 32768 else v


def row_at_entry(S, mm):
    m = mm.mem
    u = lambda a: m[a] | (m[a + 1] << 8)
    return [S.s.frame, m[0xD501], m[0xD502], m[0xD503], u(0xD511), u(0xD514), _s16(u(0xD516)), _s16(u(0xD518)), u(0xD174), u(0xD176), u(0xD284), u(0xD286),
            m[0xD28A], m[0xD28D], m[0xD289], (m[0xD504] >> 4) & 1, m[0xD15F], m[0xD137], m[0xD3B1]]


def install_recorder(S):
    rows = []

    def fn(mm):
        if mm.mem[0xD15E] & 0x80:
            rows.append(row_at_entry(S, mm))
    S.hook(0x4C90, fn)
    return rows


def run_plan(S, rows, plan):
    """plan = [(frames, pad), ...] in harness frames; returns the rows recorded during it and the update index at each segment start."""
    first = len(rows)
    marks = []
    for frames, pad in plan:
        marks.append(len(rows) - first)
        for _ in range(frames):
            S.s.pad = pad
            S.s.run_frame()
    return rows[first:], marks


def scenario(name, desc, S, plan, rows):
    f0 = S.s.frame
    got, marks = run_plan(S, rows, plan)
    for r in got:
        r[0] -= f0
    return dict(name=name, description=desc, columns=COLS, segments=[[f, p] for f, p in plan], segment_first_row=marks, rows=got)


def first_change(rows, col, from_idx=0):
    c = COLS.index(col)
    base = rows[from_idx][c]
    for i in range(from_idx, len(rows)):
        if rows[i][c] != base:
            return i
    return None


def fresh(rom_path, settle=40):
    """New Game in its own Session; the recorder is installed after the scripted settle so index 0 = first camera update after it."""
    import rom as R
    from g0_rig import Session
    S = Session(R.load(rom_path))
    boot_frame = S.boot_new_game()
    S.run(settle)
    return S, boot_frame, install_recorder(S)


def census(S):
    """Object slot types (64-byte slots from $D500; slot 0 is the player)."""
    return sorted({S.m[0xD500 + 64 * n] for n in range(1, 24) if S.m[0xD500 + 64 * n]})


def census_by_frame(S, plan):
    """Object slot-type changes per harness frame during the plan (frame index relative to the start of the plan)."""
    seen, f = [], 0
    for frames, pad in plan:
        for _ in range(frames):
            S.s.pad = pad
            S.s.run_frame()
            c = census(S)
            if not seen or seen[-1][1] != c:
                seen.append([f, c])
            f += 1
    return seen


PLANS = None


def plans():
    from sms_frame_harness import BTN_UP, BTN_DOWN, BTN_1, BTN_RIGHT
    return [
        ("idle_wait", "No input from the first controllable update: state 1 -> 2 (script record 180 then FF 03 02)", [(420, 0)], 0),
        ("look_up_hold_release", "Hold Up 150 frames from standing, release for 150", [(150, BTN_UP), (150, 0)], 40),
        ("look_down_hold_release", "Hold Down 150 frames (crouch, state 4), release for 150", [(150, BTN_DOWN), (150, 0)], 40),
        ("look_up_then_walk", "Hold Up 70, then Right 40, then no input 120: lead reset by the walk callback", [(70, BTN_UP), (40, BTN_RIGHT), (120, 0)], 40),
        ("peel_out_ordinary", "Up 20; Up+Button1 3; Up 60; release everything for 90: states $15 charge -> $1A run, speed from $46E2",
         [(20, BTN_UP), (3, BTN_UP | BTN_1), (60, BTN_UP), (90, 0)], 40),
        ("peel_out_hold_right", "As above but Right is held after release (90 frames): speed retention and the run-state exits",
         [(20, BTN_UP), (3, BTN_UP | BTN_1), (60, BTN_UP), (90, BTN_RIGHT)], 40),
        ("peel_out_long_hold", "Up 10; Up+Button1 3; Up held 1900 frames; release; 60 frames (the state $15 script loops 210 x 8 updates before FF 01 $82CC); object slot types per frame",
         [(10, BTN_UP), (3, BTN_UP | BTN_1), (1900, BTN_UP), (60, 0)], 40),
    ]


def run(rom_path):
    out = dict(schema="c1r-camera-look-trace/2", rom_sha256=hashlib.sha256(Path(rom_path).read_bytes()).hexdigest(), zone_act="THZ1 act 1, Sonic",
               note="every scenario is a fresh New Game (own Session); one row per camera update ($4C90 entry with D15E bit 7 set)", scenarios=[])
    for name, desc, plan, settle in plans():
        S, boot_frame, rows = fresh(rom_path, settle)
        if name == "peel_out_long_hold":
            f0 = S.s.frame
            seen = census_by_frame(S, plan)
            got = [dict(zip(COLS, r)) for r in rows]
            sc = dict(name=name, description=desc, columns=COLS, segments=[[f, p] for f, p in plan], segment_first_row=[0],
                      rows=[[r[0] - f0] + r[1:] for r in rows], object_type_changes_by_frame=seen)
            del got
        else:
            sc = scenario(name, desc, S, plan, rows)
        if name == "idle_wait":
            sc["controllable_from_harness_frame"] = boot_frame
        out["scenarios"].append(sc)
    return out


def summarise(out):
    s = {}
    by = {x["name"]: x for x in out["scenarios"]}
    cs = COLS.index
    r = by["idle_wait"]["rows"]
    st = cs("state")
    first2 = next(k for k, row in enumerate(r) if row[st] == 2)
    s["idle_wait"] = dict(first_row_in_state_2=first2, rows_in_state_1=sum(1 for row in r[:first2] if row[st] == 1), rows_in_state_0=sum(1 for row in r[:first2] if row[st] == 0))
    for key in ("look_up_hold_release", "look_down_hold_release"):
        r = by[key]["rows"]
        seg = by[key]["segment_first_row"]
        c0 = r[0][cs("cam_y")]
        hold = r[:seg[1]]
        cam_move = next((k for k, row in enumerate(hold) if row[cs("cam_y")] != c0), None)
        lead_move = next((k for k, row in enumerate(hold) if row[cs("lead_y")] != r[0][cs("lead_y")]), None)
        s[key] = dict(hold_updates=seg[1], first_lead_change_row=lead_move, first_camera_change_row=cam_move,
                      camera_dy_at_end_of_hold=hold[-1][cs("cam_y")] - c0, lead_at_end_of_hold=hold[-1][cs("lead_y")],
                      lead_target_values=sorted({row[cs("lead_target")] for row in r}), player_screen_y_start=r[0][cs("py")] - c0,
                      player_screen_y_end_of_hold=hold[-1][cs("py")] - hold[-1][cs("cam_y")], player_screen_y_final=r[-1][cs("py")] - r[-1][cs("cam_y")])
    return s


def build(rom_path):
    out = run(rom_path)
    out["summary"] = summarise(out)
    return out


def validate():
    d = json.loads(OUT.read_text())
    assert d["schema"] == "c1r-camera-look-trace/2" and d["rom_sha256"] == ROM_SHA256
    for sc in d["scenarios"]:
        assert all(len(row) == len(COLS) for row in sc["rows"]), sc["name"]
        assert sc["columns"] == COLS
    print("validate ok:", len(d["scenarios"]), "scenarios")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", nargs="?")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.validate:
        validate()
        return
    rom_path = a.rom or os.environ.get("SONIC_CHAOS_ROM") or str(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")
    out = build(rom_path)
    text = json.dumps(out, separators=(",", ":"), sort_keys=True) + "\n"
    if a.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text)
        print("wrote", OUT, len(text), "bytes")
    elif a.check:
        same = OUT.read_text() == text
        print("check:", "identical" if same else "DIFFERENT")
        sys.exit(0 if same else 1)
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""C3-BX: ROM boss EXIT traces (defeat -> release at $81BD / $9D26 -> player state $20 run-off -> act clear / next scene), 256 px. Research only; needs the ROM.

    python tools/c3bx_rom_exit.py ROM --write | --check

Evidence: EMULATED (unmodified ROM in tools/sms_frame_harness.py via the T2 Rig) + SYNTHETIC injection stated per scenario:
  1. the shipped T3 arrival ('hold', RIGHT held) runs until the boss reaches its fight state and the arena camera is settled;
  2. Sonic is placed on the floor at the arena camera + 73 (the screen X of the ROM AQZ3 exit trace in data/rom-cache/aqz/boss-59-game-checks.json), speed 0;
  3. the boss slot state is forced to 5 (the shared clear state of types $50/$54/$59) and nothing else is written (the puff/blink script of state 5 runs first: t0 below is the first update of player state $20);
  4. RIGHT is released (state $20 runs by itself). GPZ3 and MGHZ3 are not traced here (writing the state does not reach $9D26 / $81BD there): their natural ROM rows are in data/rom-cache.
Rows are per update. Nothing here stores ROM bytes, tiles or pixels: only small numeric tuples.
"""
from __future__ import annotations
import argparse, json, sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import t3_boss_walkon_audit as A  # noqa: E402

OUT = ROOT / "data" / "c3bx" / "rom-exit.json"
SCREEN0 = 73
ARENA_CAM = {"THZ3": 1679, "GPZ3": 1663, "SEZ3": 2975, "MGHZ3": 3060, "AQZ3": 1727}   # pan ends of the ROM arena (T3 data/t3/rom-series.json)
MAXU = 1600


def exit_trace(rig, zkey):
    z = A.ZONES[zkey]
    fam, prim = z["family"], z["primary"]
    bx, by = rig.anchors(f"{z['rom']}3", prim)[0]
    lab = rig.lab(z["rom"], 2)
    s, m = lab.s, lab.m
    px = bx - z["back"]
    lab.place(px, by - 120, 0x300, 0, cur=0x0E, f3=1, floor=False, prev=0, p24=0)
    s.w16(0xD174, px - 104)
    s.w16(0xD284, px - 104)
    last, hist, ready, stopped, init_r = lab.upd, [], None, False, None
    import t2_camera_audit as T2

    def boss_slot():
        for a in range(0xD540, 0xDA00, 0x40):
            if m[a] == prim:
                return a
        return None

    for _ in range(80000):
        s.pad = 0 if stopped else 8                # the T3 'stop' convention: RIGHT is released at the arena lock (a player who waits), so the entrance never ends in a pit or a hit
        m[0xD29A] = 0x50
        s.run_frame()
        if lab.upd == last:
            continue
        last = lab.upd
        r = T2.snap(lab, z["rom"], ())
        hist.append(r["cx"])
        if init_r is None:
            init_r = r["limR"]
        if not stopped and ((r["limR"] != init_r and r["limR"] <= r["cx"] + 8) or r["d15f"] & 1):
            stopped = True
        a = boss_slot()
        if a is not None and (m[a + 1] == z["fight_state"] or (zkey == "MGHZ3" and m[a + 1] >= 6)) and len(hist) > 40 and r["cx"] == ARENA_CAM[zkey] and all(h == hist[-1] for h in hist[-30:]) and (m[0xD522] & 2 or zkey == "MGHZ3"):
            ready = lab.upd
            break
        if lab.upd > 4000:
            break
    if ready is None:
        return OrderedDict(error="arena never settled")
    a = boss_slot()
    cam = s.u16(0xD174)
    x = cam + SCREEN0
    s.w16(0xD511, x)
    s.w16(0xD516, 0)
    if zkey == "MGHZ3":                       # the hold player fell off the arena platform (py 612): put him back on the arena floor (Y 430, from the T2 MGHZ3 fight rows) and let him land
        s.w16(0xD514, 430)
        s.w16(0xD518, 0)
        for _ in range(90):
            s.pad = 0
            m[0xD29A] = 0x50
            s.run_frame()
            if m[0xD522] & 2:
                break
        last = lab.upd
    m[a + 1] = 5
    m[a + 2] = 5
    cols = OrderedDict((k, []) for k in ("u", "px", "py", "pst", "preq", "vx", "cx", "cy", "limL", "limR", "scr", "bossst", "clr", "zone", "act"))
    cleared = None
    for u in range(MAXU):
        walk = zkey == "MGHZ3" and m[0xD501] != 0x20 and m[0xD502] != 0x20
        s.pad = 8 if walk else 0
        m[0xD29A] = 0x50
        s.run_frame()
        if lab.upd == last:
            continue
        last = lab.upd
        r = T2.snap(lab, z["rom"], ())
        vals = dict(u=len(cols["u"]), px=r["px"], py=r["py"], pst=r["pst"], preq=m[0xD502], vx=A.s16(r["vx"]), cx=r["cx"], cy=r["cy"], limL=r["limL"], limR=r["limR"], scr=r["px"] - r["cx"],
                    bossst=(m[a + 1] if m[a] == prim else -1), clr=m[0xD293], zone=m[0xD297], act=m[0xD298])
        for k in cols:
            cols[k].append(vals[k])
        if cleared is None and (cols["clr"][-1] & 0x10 or (cols["zone"][-1], cols["act"][-1]) != (cols["zone"][0], cols["act"][0])):
            cleared = len(cols["u"]) - 1            # D293 bit 4: the act-clear flag (set at EDGE(RIGHT,+33)); the zone/act change is the next-scene handoff
        if cleared is not None and len(cols["u"]) > cleared + 6:
            break
    return OrderedDict(ready_u=ready, arena_camera=cam, cleared_u=cleared, cols=cols)


def build(rom):
    import t2_camera_audit as T2
    rig = T2.Rig(rom)
    zones = OrderedDict()
    for zk in ("THZ3", "SEZ3", "AQZ3"):         # GPZ3 (head release $9D26) and MGHZ3 ($81BD behind a player gate) cannot be reached by writing the boss state: their natural ROM rows are in data/rom-cache (see c3bx_exit_matrix.py)
        zones[zk] = exit_trace(rig, zk)
    return OrderedDict(description=__doc__.strip().splitlines()[0], evidence="EMULATED + SYNTHETIC injection (see module docstring)", rom_sha256=A.ROM_SHA256, screen0=SCREEN0, zones=zones)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rom = A.load_rom(a.rom)
    text = A.dumps(build(rom))
    if a.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text)
        print("wrote", OUT, len(text))
    elif a.check:
        same = OUT.exists() and OUT.read_text() == text
        print("CHECK rom-exit", "identical" if same else "DIFFERENT")
        return 0 if same else 1
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

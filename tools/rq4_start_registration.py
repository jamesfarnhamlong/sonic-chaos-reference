#!/usr/bin/env python3
"""RQ4: original campaign start-coordinate and camera registration.

    python tools/rq4_start_registration.py /path/to/SonicChaos.sms            # regenerate data/rq4/start-registration.json (about 2 minutes)
    python tools/rq4_start_registration.py /path/to/SonicChaos.sms --check    # regenerate in memory and compare with the committed file
    python tools/rq4_start_registration.py --validate                         # no ROM: internal consistency of the committed file
    python tools/rq4_start_registration.py ROM --probe-offsets                # THZ1 depenetration sweep (start Y +/- 8), printed only

The ROM is read from the argument or SONIC_CHAOS_ROM; no ROM bytes or pixels are written.  Needs Python >= 3.10 with the `z80` and `z80dis` packages
(the same environment as tools/g0_campaign.py).

Evidence classes
  STATIC          bytes of the ROM (loader `$4E57..$4E97`, record table `$4E98`, camera/scroll init `$4DAD..$4E56`)
  EMULATED        unmodified ROM code in the approximate harness (tools/g0_rig.py Session): a real New Game (title -> character select -> level
                  load) with only the START_INDEX fixture of G0-R (zone/act stores at `$07D5`) for acts other than THZ1.  No arrival fixture,
                  no RAM writes except the documented pit-death Y offset used for the reload observation.
  FIXTURE-SWEEP   --probe-offsets only: one ARRIVAL write of a start Y offset, to measure the terrain depenetration the first updates apply.

"Update" below means one entry of the player engine `$64FA` with IX = `$D500` (the harness cannot see lag frames inside it; frame offsets are
harness frames after the return of the start-position loader `$4E97`).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

OUT = ROOT / "data" / "rq4" / "start-registration.json"
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
BASE_COMMIT = "850a60303b91a0885052510554e2a07ad056999a"
AFTER = [0, 1, 2, 3, 4, 5, 10, 20, 40, 80, 200]      # player-engine passes completed since the loader returned
SETTLED = 200
ZONES = ["THZ", "GPZ", "SEZ", "MGHZ", "AQZ", "EEZ"]
LOADER_REGIONS = {"start_position_loader": (0x4E57, 0x4E98), "camera_and_scroll_init": (0x4DAD, 0x4E57), "act_record_pointer_reader": (0x2A4F, 0x2A9A)}


def load_rom(path=None):
    import rom as R
    p = Path(path or os.environ.get("SONIC_CHAOS_ROM", str(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")))
    return R.load(p)


# --------------------------------------------------------------------------------------------------------------------------------------------
def static_table(rom):
    u = lambda o: rom[o] | (rom[o + 1] << 8)  # noqa: E731
    rows = []
    for z in range(6):
        tbl = u(0x4E98 + 2 * z)
        for a in range(3):
            rec = u(tbl + 2 * a)
            rows.append(dict(zone=z, act=a, zone_name=ZONES[z], record="%04X" % rec, camera=[u(rec), u(rec + 2)], player=[u(rec + 4), u(rec + 6)]))
    return rows


def static_census(rom):
    return dict(
        rom_sha256=hashlib.sha256(rom).hexdigest(),
        table=static_table(rom),
        record_layout="4 little-endian words at the record: +0 -> $D2D6 (camera X target), +2 -> $D2D8 (camera Y target), +4 -> $D511 (player anchor X), +6 -> $D514 (player anchor Y)",
        routine_hashes=[dict(name=n, start="%04X" % a, end="%04X" % b, sha256=hashlib.sha256(rom[a:b]).hexdigest()) for n, (a, b) in LOADER_REGIONS.items()],
        source_chain=[
            "$1673 level (re)load -> $2934 loader: $297E clears $D300..$DBBF, $4DAD camera/scroll init, $2A4F act record, ...",
            "$4DAD ... CALL $4E57: (zone $D297, act $D298) -> table $4E98 -> record -> $D2D6/$D2D8 (camera) and $D511/$D514 (player); RET at $4E97",
            "$4DFF..$4E0E: $D174 := $D284 := $D2D6, $D176 := $D286 := $D2D8 (the camera is committed directly from the record, no clamp)",
            "$4E11..$4E30: 29 passes (B = $1D) with $D286 := $D176 + 8, $1C6F, $53BF (column/row fill), $062D (vblank flush) to draw the initial map",
            "$4E32..$4E52: camera re-committed from $D2D6/$D2D8 and $D173 := ((camY + 16) mod $E0) (the vertical-scroll row register)",
            "no ROM routine adds, subtracts or scales the record values for the player: $4E8B/$4E94 store the words unchanged",
        ],
    )


# --------------------------------------------------------------------------------------------------------------------------------------------
def player_cluster(S, ax, ay):
    """SAT entries that belong to the player: inside the anchor neighbourhood (the HUD entries sit at the top-left corner and are excluded).

    Reports the SAT rectangle and the OPAQUE pixel rectangle (palette index != 0 in the sprite tiles) relative to the anchor (ax, ay) = screen position
    of ($D511,$D514) after subtracting the camera; row r of a sprite is screen row SAT_Y + 1 + r (the SMS Y+1 rule)."""
    s = S.s
    tall = bool(s.reg[1] & 0x02)
    h = 16 if tall else 8
    shift = 8 if (s.reg[0] & 0x08) else 0
    pat_base = 256 if (s.reg[6] & 0x04) else 0
    ents, ox0, ox1, oy0, oy1 = [], [], [], [], []
    for i, sy, sx, n in s.sat():
        if sy >= 0xE0:
            continue
        top, left = sy + 1, sx - shift
        if not (abs(left - ax) <= 32 and ay - 48 <= top <= ay + 8):
            continue
        ents.append((i, top, left, n))
        nn = n & 0xFE if tall else n
        for r in range(h):
            row = s.tile_row(pat_base + nn + (r >> 3), r & 7)
            cols = [c for c, v in enumerate(row) if v]
            if cols:
                oy0.append(top + r)
                oy1.append(top + r)
                ox0.append(left + cols[0])
                ox1.append(left + cols[-1])
    if not ents:
        return None
    return dict(count=len(ents), tall=tall, entries=[[t, l] for _, t, l, _ in ents],
                left=min(l for _, _, l, _ in ents) - ax, right=max(l for _, _, l, _ in ents) + 8 - 1 - ax,
                top=min(t for _, t, _, _ in ents) - ay, bottom=max(t for _, t, _, _ in ents) + h - 1 - ay,
                opaque=None if not oy0 else dict(left=min(ox0) - ax, right=max(ox1) - ax, top=min(oy0) - ay, bottom=max(oy1) - ay))


class Collector:
    """Passive observer: begins at every in-game return of the start-position loader `$4E97`, then samples after each harness frame."""

    def __init__(self, S):
        self.S = S
        self.loads = []
        self.cur = None
        S.hook(0x4E97, self._begin)
        S.hook(0x64FA, self._engine)
        orig = S.s.run_frame

        def run_frame():
            orig()
            self._tick()
        S.s.run_frame = run_frame

    def _grab(self, f0):
        S, m, s = self.S, self.S.m, self.S.s
        p = [S.u16(0xD511), S.u16(0xD514)]
        c = [S.u16(0xD174), S.u16(0xD176)]
        return dict(player=p, camera=c, target=[S.u16(0xD2D6), S.u16(0xD2D8)], screen_anchor=[p[0] - c[0], p[1] - c[1]], state=m[0xD501],
                    player_object=m[0xD500], flow=m[0xD293], frame=s.frame - f0, display_enabled=bool(s.reg[1] & 0x40), vdp_r8=s.reg[8], vdp_vscroll_latched=s.vscroll_latched)

    def _begin(self, mm):
        S = self.S
        if S.m[0xD295] != 0xFF:
            return
        f0 = S.s.frame
        self.cur = dict(f0=f0, n=0, done=False, first={}, rows={}, entry=self._grab(f0))
        self.loads.append(self.cur)

    def _engine(self, mm):
        """Entry of engine pass n+1: the state seen here is the state AFTER n completed passes (n = 0 is the loader result)."""
        c = self.cur
        if c is None or c["done"] or mm.cpu.ix != 0xD500:
            return
        n = c["n"]
        if n in AFTER:
            c["rows"][n] = self._grab(c["f0"])
        c["n"] = n + 1
        if n >= SETTLED:
            c["settled_pending"] = True

    def _tick(self):
        c = self.cur
        if c is None or c["done"]:
            return
        S, s = self.S, self.S.s
        if "display_on_frame" not in c["first"] and (s.reg[1] & 0x40):
            c["first"]["display_on_frame"] = s.frame - c["f0"]
        if "player_sprite_update" not in c["first"] and c["n"] > 0:
            cl = player_cluster(S, S.u16(0xD511) - S.u16(0xD174), S.u16(0xD514) - S.u16(0xD176))
            if cl:
                c["first"]["player_sprite_after_passes"] = c["n"]
                c["first"]["player_sprite_frame"] = s.frame - c["f0"]
                c["first"]["player_sprite_update"] = c["n"]
        if c.pop("settled_pending", False):
            g = c["rows"][SETTLED]
            c["rows"][SETTLED]["sprite_cluster"] = player_cluster(S, g["screen_anchor"][0], g["screen_anchor"][1])
            c["done"] = True

    def result(self, i):
        c = self.loads[i]
        return dict(loader_return=c["entry"], first=c["first"], updates={str(k): c["rows"][k] for k in sorted(c["rows"])})


def observe_act(args):
    rom_path, zone, act = args
    from g0_rig import Session
    rom = load_rom(rom_path)
    S = Session(rom)
    if (zone, act) != (0, 0):
        S.set_start_index(zone, act)
    C = Collector(S)
    S.boot_new_game()
    S.run_until(lambda s: C.loads and C.loads[-1]["done"], limit=3000)
    fresh = C.result(0)
    # reload: a pit death (G0-R restart_matrix fixture: player Y + 600) -> level reload ($1673) at the same zone/act
    S.s.w16(0xD514, S.u16(0xD514) + 600)
    S.run_until(lambda s: len(C.loads) > 1 and C.loads[-1]["done"], limit=6000)
    reload_ = C.result(1)

    def core(d):
        return {k: v for k, v in d.items() if k != "frame"}

    same = all(core(fresh["updates"][k]) == core(reload_["updates"][k]) for k in fresh["updates"]) and core(fresh["loader_return"]) == core(reload_["loader_return"])
    return dict(zone=zone, act=act, fresh=fresh, reload=reload_, reload_equals_fresh_except_frame_offsets=same)


def observe_all(rom_path, jobs=4, only=None):
    work = [(str(rom_path), z, a) for z in range(6) for a in range(3) if only is None or (z, a) in only]
    if jobs <= 1:
        res = [observe_act(w) for w in work]
    else:
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            res = list(ex.map(observe_act, work))
    return res


# --------------------------------------------------------------------------------------------------------------------------------------------
def derive(acts, table):
    """Per-act summary: record vs entry vs settled, and the adapter-relevant screen offsets."""
    rec = {(t["zone"], t["act"]): t for t in table}
    rows = []
    for o in acts:
        z, a = o["zone"], o["act"]
        t = rec[(z, a)]
        f = o["fresh"]
        ent = f["loader_return"]
        u1, u3, us = f["updates"]["1"], f["updates"]["3"], f["updates"][str(SETTLED)]
        cl = us.get("sprite_cluster")
        rows.append(dict(
            zone=z, act=a, name="%s%d" % (ZONES[z], a + 1),
            record_player=t["player"], record_camera=t["camera"],
            loader_return_player=ent["player"], first_update_player=u1["player"], first_update_camera=u1["camera"],
            update3_player=u3["player"], settled_player=us["player"], settled_camera=us["camera"],
            player_matches_record_at_entry=ent["player"] == t["player"],
            camera_committed_at_first_update_equals_record=u1["camera"] == t["camera"],
            terrain_shift_y=us["player"][1] - t["player"][1], terrain_shift_x=us["player"][0] - t["player"][0],
            settle_update=next((int(k) for k in sorted(f["updates"], key=int) if f["updates"][k]["player"] == us["player"]), None),
            camera_y_drift=us["camera"][1] - t["camera"][1], camera_x_drift=us["camera"][0] - t["camera"][0],
            entry_screen_anchor=u1["screen_anchor"], settled_screen_anchor=us["screen_anchor"],
            sprite_sat_rect_rel_anchor=None if not cl else dict(left=cl["left"], right=cl["right"], top=cl["top"], bottom=cl["bottom"]),
            sprite_opaque_rect_rel_anchor=None if not cl else cl["opaque"],
            foot_world_row=us["player"][1] + 17, floor_probe_row=us["player"][1] + 18,
            vdp_r8_r9_settled=[us["vdp_r8"], us["vdp_vscroll_latched"]],
            display_on_frame=f["first"].get("display_on_frame"), player_sprite_update=f["first"].get("player_sprite_update"),
            reload_equals_fresh=o["reload_equals_fresh_except_frame_offsets"],
        ))
    return rows


def build(rom, rom_path, jobs=4):
    st = static_census(rom)
    acts = observe_all(rom_path, jobs)
    return dict(
        schema="rq4-start-registration/1", base_commit=BASE_COMMIT, rom_sha256=st["rom_sha256"],
        evidence="STATIC (table, loader bytes) + EMULATED ORIGINAL FRAME (real New Game via tools/g0_rig.Session; approximate VDP); see tools/rq4_start_registration.py",
        static=st, summary=derive(acts, st["table"]), observations=acts,
        fixture_sweeps=dict(evidence="FIXTURE-SWEEP: ARRIVAL write of (start Y + dy) at the loader return $4E97, otherwise a real New Game", notes={s["label"]: s["note"] for s in SWEEPS}, rows=probe_offsets(rom_path, jobs)),
        poc_source_read=POC_SOURCE_READ,
    )


POC_SOURCE_READ = dict(
    evidence="SOURCE-READ (not executed): SonicChaos_POC poc/g1-a-run-state 68615389a844b95e3bab58c6d2634be4e63a4488; Research cross-check tests/test_collision_geometry.py asserts chaosAnchorOffset == 5",
    chaosAnchorOffset=5, formula="18 - (SPR_player_mask bbox_bottom 33 - yorigin 20)",
    core_start="SCR_chaos_core_attach: core Y = instance y - 5, except zones SS/EEZ/AQZ/SEZ/MGHZ/GPZ where core yu := instance y (the record is taken as the canonical anchor)",
    publish="SCR_chaos_core_publish: instance y = core Y + 5; draw registration for ROM-art player: y = core Y + 18, x = core X + 1",
    thz_branch="OBJ_chaos_zone Create_0: THZ1 instance_create(142, 658); THZ2 (110, 398) / THZ3 (110, 224) as CHAOS_THZ*_DEV_SPAWN (instance y, not anchor)",
    thz1_camera="OBJ_chaos_zone Create_0: XView 0, YView 550 (legacy fixed); the per-zone chaos_*_camera() tables are used for GPZ/MGHZ/SEZ/AQZ/EEZ only")


def handoff_table(d):
    """Markdown G1-B handoff table, rendered from the committed JSON (docs/rq4-campaign-start-registration.md embeds it verbatim)."""
    head = [("| Act | ROM record: anchor (X,Y) / camera (X,Y) | Entry = after pass 0 | After 1 pass | After 2 passes | Rest (pass 200) | Anchor shift to rest "
             "| Camera at rest | Screen anchor entry -> rest |"), "|---|---|---|---|---|---|---|---|---|"]
    rows = []
    obs = {(o["zone"], o["act"]): o for o in d["observations"]}
    for r in d["summary"]:
        u = obs[(r["zone"], r["act"])]["fresh"]["updates"]
        f = lambda p: "(%d,%d)" % tuple(p)  # noqa: E731
        rows.append("| %s | %s / %s | %s | %s | %s | %s | %+d | %s | %s -> %s |" % (
            r["name"], f(r["record_player"]), f(r["record_camera"]), f(u["0"]["player"]), f(u["1"]["player"]), f(u["2"]["player"]), f(r["settled_player"]),
            r["terrain_shift_y"], f(r["settled_camera"]), f(r["entry_screen_anchor"]), f(r["settled_screen_anchor"])))
    return chr(10).join(head + rows)


def dumps(d):
    return json.dumps(d, indent=1, sort_keys=False) + "\n"


# --------------------------------------------------------------------------------------------------------------------------------------------
def validate(d):
    errs = []
    if d["rom_sha256"] != ROM_SHA256:
        errs.append("rom sha")
    tbl = {(t["zone"], t["act"]): t for t in d["static"]["table"]}
    if len(tbl) != 18:
        errs.append("table size")
    if len(d["summary"]) != 18 or len(d["observations"]) != 18:
        errs.append("summary/observation size")
    for r in d["summary"]:
        k = (r["zone"], r["act"])
        t = tbl.get(k)
        if t is None:
            errs.append("%s missing from table" % r["name"])
            continue
        if r["record_player"] != t["player"] or r["record_camera"] != t["camera"]:
            errs.append("%s record mismatch" % r["name"])
        if not r["player_matches_record_at_entry"]:
            errs.append("%s: loader did not store the record unchanged" % r["name"])
        if not r["camera_committed_at_first_update_equals_record"]:
            errs.append("%s: first-update camera differs from record" % r["name"])
        if not r["reload_equals_fresh"]:
            errs.append("%s: reload differs from fresh load" % r["name"])
        if r["terrain_shift_x"] != 0:
            errs.append("%s: unexpected X shift" % r["name"])
    return errs


# POC-equivalent starts (source-read, tools/rq4 doc section 6): POC core anchor = instance y - chaosAnchorOffset (5); the THZ branch of the POC passes the
# record numbers as INSTANCE y, so the core starts 5 above the record; THZ1 literal 658 -> core 653.
SWEEPS = [
    dict(zone=0, act=0, label="THZ1", dys=[-8, -5, -4, -1, 0, 1, 4, 5, 8], note="record 654; -1 = POC core anchor from instance 658; +4/+5 = embedded starts"),
    dict(zone=0, act=1, label="THZ2", dys=[-5, 0], note="record 398; -5 = POC core anchor from the DEV_SPAWN instance y 398"),
    dict(zone=0, act=2, label="THZ3", dys=[-5, 0], note="record 224; -5 = POC core anchor from the DEV_SPAWN instance y 224"),
]


def sweep_one(args):
    rom_path, zone, act, dy = args
    from g0_rig import Session
    rom = load_rom(rom_path)
    S = Session(rom)
    if (zone, act) != (0, 0):
        S.set_start_index(zone, act)
    st = dict(on=False, n=0, out={})

    def arr(mm):
        mm.w16(0xD514, mm.u16(0xD514) + dy)
    S.hook(0x4E97, lambda mm: st.update(on=S.m[0xD295] == 0xFF))

    def eng(mm):
        if st["on"] and mm.cpu.ix == 0xD500:
            n = st["n"]
            if n in AFTER:
                st["out"][str(n)] = [S.u16(0xD511), S.u16(0xD514), S.m[0xD501]]
            st["n"] = n + 1
    S.hook(0x64FA, eng)
    S.boot_new_game(arrival=arr)
    S.run(260)
    return dict(zone=zone, act=act, start_dy=dy, after_passes=st["out"], settled=st["out"].get(str(SETTLED), [None])[:2])


def probe_offsets(rom_path, jobs=4):
    work = [(str(rom_path), s["zone"], s["act"], dy) for s in SWEEPS for dy in s["dys"]]
    if jobs <= 1:
        return [sweep_one(w) for w in work]
    with ProcessPoolExecutor(max_workers=jobs) as ex:
        return list(ex.map(sweep_one, work))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--probe-offsets", action="store_true")
    ap.add_argument("--table", action="store_true", help="print the G1-B handoff table rendered from the committed JSON")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args(argv)
    if a.table:
        print(handoff_table(json.loads(OUT.read_text(encoding="utf-8"))))
        return 0
    if a.validate:
        errs = validate(json.loads(OUT.read_text(encoding="utf-8")))
        print("OK" if not errs else "\n".join(errs))
        return 1 if errs else 0
    path = a.rom or os.environ.get("SONIC_CHAOS_ROM") or str(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")
    if a.probe_offsets:
        for r in probe_offsets(path, a.jobs):
            print(r)
        return 0
    rom = load_rom(path)
    d = build(rom, path, a.jobs)
    errs = validate(d)
    if errs:
        print("\n".join(errs))
        return 1
    if a.check:
        same = OUT.read_text(encoding="utf-8") == dumps(d)
        print("RQ4 check:", "OK" if same else "DIFFERS")
        return 0 if same else 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(dumps(d), encoding="utf-8", newline="\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())

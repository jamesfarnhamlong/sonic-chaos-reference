#!/usr/bin/env python3
"""C3-BX: boss EXIT matrix (ROM vs POC P4 vs candidate patches) from the committed series. Deterministic, ROM-free and POC-free.

    python tools/c3bx_exit_matrix.py --write | --check | --table

Inputs (all committed): data/c3bx/rom-exit.json (EMULATED + SYNTHETIC, tools/c3bx_rom_exit.py), data/rom-cache/{aqz,gpz,mghz}/*game*.json (natural ROM fights of the earlier research
phases), data/c3bx/poc-exit-p4.json (POC-SOURCE MODEL), data/c3bx/poc-exit-A1.json and poc-exit-A1+A2.json (PROPOSAL MODEL: P4 source + in-memory text patches).
Output: data/c3bx/exit-matrix.json. Nothing here stores ROM bytes.

Definitions (all counted from t0 = the first update the player is IN state $20):
  scr0          Sonic screen X at t0 (the scenario places him at camera + 73, the screen X of the ROM AQZ3 exit)
  first_move    updates from t0 to the first camera X change
  last_move     updates from t0 to the last camera X change (the camera freeze)
  cam_final     camera X when the run ends;  cam_max the largest legal camera X at that width (world width - W; GPZ3: its restored right limit 1920 - 1)
  short         cam_max - cam_final: how much valid world was never scrolled into view (0..~6 = the camera reached the world edge)
  steady_scr    median Sonic screen X over the updates in which the camera moved (the follow lead)
  clear         updates from t0 to the act-clear flag; px_clear / scr_clear Sonic world / screen X on that update
  back_scroll   largest camera retreat after t0
"""
from __future__ import annotations
import argparse, json, statistics
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "c3bx"
OUT = D / "exit-matrix.json"
ROOM_W = {"THZ3": 2560, "GPZ3": 2560, "SEZ3": 4096, "MGHZ3": 3840, "AQZ3": 2560}


def dumps(d):
    return json.dumps(d, separators=(",", ":")) + "\n"


def metrics(zone, W, px, cx, st, t0, clear_i, frozen=None, cam_max=None):
    n = len(px)
    scr = [px[i] - cx[i] for i in range(n)]
    fm = next((i for i in range(t0, n) if cx[i] != cx[t0]), None)
    lm = max((i for i in range(t0 + 1, n) if cx[i] != cx[i - 1]), default=None)
    moving = [scr[i] for i in range(t0 + 1, n) if cx[i] != cx[i - 1]]
    cmax = cam_max if cam_max is not None else ROOM_W[zone] - W
    if zone == "GPZ3":
        cmax = min(cmax, 1919)
    back = 0
    top = cx[t0]
    for i in range(t0, n):
        top = max(top, cx[i])
        back = max(back, top - cx[i])
    m = OrderedDict(scr0=scr[t0], cam0=cx[t0], cam_final=cx[-1], cam_max=cmax, short=cmax - cx[-1],
                    first_move=(fm - t0) if fm is not None else None, last_move=(lm - t0) if lm is not None else None,
                    steady_scr=int(statistics.median(moving)) if moving else None, back_scroll=back)
    if clear_i is not None:
        m["clear"] = clear_i - t0
        m["px_clear"] = px[clear_i]
        m["scr_clear"] = scr[clear_i]
    else:
        m["clear"] = None
    if frozen is not None:
        fz = next((i for i in range(t0, n) if frozen[i]), None)
        m["freeze_flag"] = (fz - t0) if fz is not None else None
    return m


def rom_rig():
    d = json.loads((D / "rom-exit.json").read_text())
    out = OrderedDict()
    for z, r in d["zones"].items():
        c = r["cols"]
        t0 = next(i for i, v in enumerate(c["pst"]) if v == 32)
        out[z] = metrics(z, 256, c["px"], c["cx"], c["pst"], t0, r["cleared_u"])
    return out


def rom_caches():
    out = OrderedDict()
    d = json.loads((ROOT / "data/rom-cache/aqz/boss-59-game-checks.json").read_text())
    c = next(x for x in d["cases"] if x["name"] == "fight_9")
    cl = next(m for m in c["marks"] if m["event"] == "clear")["u"]
    rows = [r for r in c["rows"] if r["u"] >= cl]
    px, cx, st = [r["x"] for r in rows], [r["d174"] for r in rows], [r["cur"] for r in rows]
    t0 = next(i for i, v in enumerate(st) if v == 32)
    nxt = next(i for i, r in enumerate(rows) if r["zone"] == 5)
    out["AQZ3_natural"] = metrics("AQZ3", 256, px[:nxt], cx[:nxt], st[:nxt], t0, nxt - 1)
    out["AQZ3_natural"]["note"] = "natural ROM fight (data/rom-cache/aqz/boss-59-game-checks.json, case fight_9), player parked at world 1800 = screen 73; act-clear flag and the zone change are the same update"
    d = json.loads((ROOT / "data/rom-cache/gpz/boss-51-fullgame.json").read_text())
    rows = d["rows"]
    i0 = next(i for i, r in enumerate(rows) if r["state"] == 32)
    nxt = next(i for i, r in enumerate(rows) if i > i0 and r["zone"] != rows[i0]["zone"])
    seg = rows[i0:nxt]
    px, cx, st = [r["player"][0] for r in seg], [r["camera"][0] for r in seg], [r["state"] for r in seg]
    clr = next(i for i, r in enumerate(seg) if r["clear"] & 0x10)
    out["GPZ3_natural"] = metrics("GPZ3", 256, px, cx, st, 0, clr)
    out["GPZ3_natural"]["note"] = "natural ROM fight (data/rom-cache/gpz/boss-51-fullgame.json); Sonic stands at world 1760 = screen 97 at the head release; restored right limit 1920"
    d = json.loads((ROOT / "data/rom-cache/mghz/boss-56-fullgame.json").read_text())
    ph = [p for p in d["camera_release_replay"]["phases"] if p["phase"] == "before_camera"]
    seen, rel = set(), []
    for p in ph:
        if p["update"] not in seen:
            seen.add(p["update"])
            rel.append(p)
    first = rel[0]["update"]
    out["MGHZ3_release"] = OrderedDict(
        note="ROM MGHZ3 release replay (data/rom-cache/mghz/boss-56-fullgame.json camera_release_replay): the $81BD right-limit restore is not tied to the player gate; Sonic stands at world 3260 (screen 200) and the camera follows at 7 px/update from the first update after the restore; the state-$20 run-off itself is the shared code traced for THZ3/SEZ3/AQZ3",
        release_update=rel[1]["update"] - first, first_camera_step=[(p["update"] - first, p["camera"][0] - rel[0]["camera"][0]) for p in rel[2:6]],
        limit_right_before_after=[rel[0]["limits"][1], rel[1]["limits"][1]], retained_left=d["camera_release_replay"]["retained_left"])
    return out


def poc_runs(fname):
    d = json.loads((D / fname).read_text())
    out = OrderedDict()
    for z, zz in d["zones"].items():
        out[z] = OrderedDict()
        for wn, r in zz.items():
            c = r["cols"]
            W = int(wn[1:])
            t0 = next(i for i, v in enumerate(c["st"]) if v == 32)
            out[z][wn] = metrics(z, W, c["px"], c["cx"], c["st"], t0, r["cleared_u"], frozen=c["frozen"])
    return out


def build():
    return OrderedDict(
        description="C3-BX boss exit matrix: ROM vs POC P4 vs candidate patches (see module docstring for the metric definitions)",
        evidence=OrderedDict(rom_rig="EMULATED + SYNTHETIC (tools/c3bx_rom_exit.py)", rom_cache="EMULATED natural fights (earlier research phases)",
                             poc_p4="POC-SOURCE MODEL (node VM, shipped P4 GML)", candidates="PROPOSAL MODEL (P4 GML + in-memory text patches, tools/c3bx_candidates.js)"),
        rom=OrderedDict(list(rom_rig().items()) + list(rom_caches().items())),
        poc_p4=poc_runs("poc-exit-p4.json"),
        candidate_A1=poc_runs("poc-exit-A1.json"),
        candidate_A1_A2=poc_runs("poc-exit-A1+A2.json"))


def table(m):
    lines = ["| zone | width | source | camera final / max | short | first move | freeze (last move) | steady Sonic screen X | clear (updates) | Sonic world X at clear |", "|---|---|---|---|---|---|---|---|---|---|"]
    def row(z, w, src, r):
        lines.append(f"| {z} | {w} | {src} | {r['cam_final']} / {r['cam_max']} | {r['short']} | +{r['first_move']} | +{r['last_move']} | {r['steady_scr']} | +{r['clear']} | {r.get('px_clear')} |")
    for z in ("THZ3", "GPZ3", "SEZ3", "MGHZ3", "AQZ3"):
        for key, src in (("rom", "ROM"), ("poc_p4", "POC P4"), ("candidate_A1_A2", "A1+A2")):
            if key == "rom":
                for k in (z, z + "_natural"):
                    if k in m["rom"] and "cam_final" in m["rom"][k]:
                        row(z, 256, "ROM" + (" (natural)" if k.endswith("natural") else ""), m["rom"][k])
            else:
                for wn, r in m[key].get(z, {}).items():
                    row(z, wn[1:], src, r)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--table", action="store_true")
    a = ap.parse_args()
    m = build()
    if a.table:
        print(table(m))
    elif a.write:
        OUT.write_text(dumps(m))
        print("wrote", OUT)
    elif a.check:
        same = OUT.exists() and OUT.read_text() == dumps(m)
        print("CHECK exit-matrix", "identical" if same else "DIFFERENT")
        return 0 if same else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

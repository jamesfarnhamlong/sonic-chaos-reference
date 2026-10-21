#!/usr/bin/env python3
"""C3-BX: boss ENTRANCE matrix (ROM 256 vs POC P4 at 256/348/400, plus the THZ3 candidate B1). Deterministic, ROM-free, POC-free.

    python tools/c3bx_entrance_matrix.py --write | --check | --table

Inputs: data/t3/rom-series.json + data/t3/frame-extents.json (T3, EMULATED + BYTE-VERIFIED), data/c3bx/poc-series-p4.json (POC-SOURCE MODEL of 354532f),
data/c3bx/poc-entrance-B1.json (PROPOSAL MODEL: P4 source + the B1 text patch). Metrics come from t3_boss_walkon_audit.summarize; thz3 adds the walk-on trajectory.
"""
from __future__ import annotations
import argparse, json, sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import t3_boss_walkon_audit as A  # noqa: E402

D = ROOT / "data" / "c3bx"
OUT = D / "entrance-matrix.json"
VIEWS = {"w256": (256, 192), "w348": (348, 196), "w400": (400, 225)}


def dumps(d):
    return json.dumps(d, separators=(",", ":")) + "\n"


def slim(s):
    fv, cam, pl = s.get("first_visible"), s.get("camera"), s.get("player")
    pe, pa = s.get("pan_end"), s.get("pan_start")
    fa = s.get("fight_activation")
    return OrderedDict(
        first_visible=None if not fv else OrderedDict(u=fv["u"], columns=fv["visible_columns"], anchor_screen=fv["anchor_screen"], camera_x=fv["camera"][0]),
        creation_step=cam["creation_update_step"], x_retreat=cam["x_retreat"]["pixels"], pan_start_camera=None if not pa else pa["camera"], pan_end_camera=None if not pe else pe["camera"],
        fight_boss_world=None if not fa else fa["boss_world"], fight_boss_screen_x=None if not fa else fa["boss_screen_x"],
        player_screen_x_max=pl["screen_x_max"], updates_beyond_right_clamp_plus_4=pl["updates_beyond_right_clamp_plus_4"])


def thz3_walk(series, view):
    """Boss-state timeline of THZ3: update/camera/anchor at state 18 (walk-on) start and at state 6 (fight)."""
    W = view
    ext = json.loads((ROOT / "data/t3/frame-extents.json").read_text())["types"]["0x50"]
    out = OrderedDict()
    s18 = next(i for i, v in enumerate(series["bs"]) if v == 18)
    s6 = next(i for i, v in enumerate(series["bs"]) if v == 6)
    def cols(i):
        f = series["bfr"][i]
        if f >= len(ext) or not ext[f]["pieces"]:
            return 0
        l = series["bx"][i] + ext[f]["min_x"] - series["cx"][i]
        r = series["bx"][i] + ext[f]["max_x_excl"] - series["cx"][i]
        return max(0, min(W, r) - max(0, l))
    out["state18"] = OrderedDict(u=series["u"][s18], camera_x=series["cx"][s18], boss_x=series["bx"][s18], boss_screen_x=series["bx"][s18] - series["cx"][s18], columns_next=cols(s18 + 1))
    out["fight"] = OrderedDict(u=series["u"][s6], camera_x=series["cx"][s6], boss_x=series["bx"][s6], boss_screen_x=series["bx"][s6] - series["cx"][s6])
    out["walk_px"] = series["bx"][s18] - series["bx"][s6]
    out["walk_updates"] = series["u"][s6] - series["u"][s18]
    return out


def build():
    rom = json.loads((ROOT / "data/t3/rom-series.json").read_text())
    ext = json.loads((ROOT / "data/t3/frame-extents.json").read_text())
    p4 = json.loads((D / "poc-series-p4.json").read_text())
    b1 = json.loads((D / "poc-entrance-B1.json").read_text())
    out = OrderedDict(description="C3-BX boss entrance matrix (see module docstring)", zones=OrderedDict())
    for zk in A.ZONES:
        zr = OrderedDict()
        rs = rom["zones"][zk]["stop"]
        zr["rom_w256_stop"] = slim(A.summarize(A.rom_rows(rs, zk), (256, 192), ext, zk, "rom", "stop"))
        for wk, view in VIEWS.items():
            ps = p4["zones"][zk][wk]["stop"]
            rows = ({k: ps[k][i] for k in ps} for i in range(len(ps["u"])))
            zr[f"p4_{wk}_stop"] = slim(A.summarize(rows, view, ext, zk, "poc", "stop"))
        out["zones"][zk] = zr
    th = OrderedDict()
    r = rom["zones"]["THZ3"]["stop"]
    n = len(r["u"])
    bs = [(r["boss"][i][0] if r["boss"][i] else None) for i in range(n)]
    rows = [i for i in range(n) if r["boss"][i]]
    rs = OrderedDict((k, [r["boss"][i][0][{"bs": 1, "bfr": 2, "bx": 4}[k]] for i in rows]) for k in ("bs", "bfr", "bx"))
    rs["cx"] = [r["cx"][i] for i in rows]
    rs["u"] = [r["u"][i] for i in rows]
    th["rom_w256"] = thz3_walk(rs, 256)
    for wk, view in VIEWS.items():
        th[f"p4_{wk}"] = thz3_walk(p4["zones"]["THZ3"][wk]["stop"], view[0])
        th[f"B1_{wk}"] = thz3_walk(b1["zones"]["THZ3"][wk]["stop"], view[0])
        ps = b1["zones"]["THZ3"][wk]["stop"]
        rws = ({k: ps[k][i] for k in ps} for i in range(len(ps["u"])))
        th[f"B1_{wk}"]["summary"] = slim(A.summarize(rws, view, ext, "THZ3", "poc", "stop"))
    out["thz3_walk_on"] = th
    return out


def table(m):
    L = ["| zone | source | first visible (cols @ anchor screen X) | creation step | x retreat | pan end camera | fight boss screen X | Sonic screen X max |", "|---|---|---|---|---|---|---|---|"]
    for z, zr in m["zones"].items():
        for k, v in zr.items():
            fv = v["first_visible"]
            L.append(f"| {z} | {k} | {fv['columns']} @ {fv['anchor_screen'][0]} | {v['creation_step']} | {v['x_retreat']} | {v['pan_end_camera']} | {v['fight_boss_screen_x']} | {v['player_screen_x_max']} |" if fv else f"| {z} | {k} | - | | | | | |")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true"); ap.add_argument("--check", action="store_true"); ap.add_argument("--table", action="store_true")
    a = ap.parse_args()
    m = build()
    if a.table:
        print(table(m)); print(json.dumps(m["thz3_walk_on"], indent=1)[:3500])
    elif a.write:
        OUT.write_text(dumps(m)); print("wrote", OUT)
    elif a.check:
        same = OUT.exists() and OUT.read_text() == dumps(m)
        print("CHECK entrance-matrix", "identical" if same else "DIFFERENT"); return 0 if same else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""P4 preflight: T3 metrics for the final V1/T1 POC (03db5e1c) beside the historical C1-I series (Research only; no ROM, no POC needed).

    POC=<v1t1 checkout> T3_OUT=data/p4/poc-series-v1t1.json T3_WIDTHS=256x192,348x196,400x225 node tools/t3_poc_boss_run.js --write
    POC=<c1i checkout>  T3_OUT=data/p4/poc-series-c1i-w400.json T3_WIDTHS=256x192,348x196,400x225 node tools/t3_poc_boss_run.js --write
    python tools/p4_rebaseline.py --write | --check | --table

data/t3/* (C1-I, 256/348) stays untouched; data/p4/* are the new baselines. Metrics are the T3 summary metrics, per zone, width and scenario.
"""
from __future__ import annotations
import argparse, json, sys
from collections import OrderedDict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import t3_boss_walkon_audit as A

D = ROOT / "data" / "p4"
OUT = D / "baseline-summary.json"
WID = OrderedDict([("w256", (256, 192)), ("w348", (348, 196)), ("w400", (400, 225))])
SRC = OrderedDict([("c1i", D / "poc-series-c1i-w400.json"), ("v1t1", D / "poc-series-v1t1.json"), ("proposal", D / "poc-series-proposal.json")])
KEEP = ("created", "relocations", "right_limit", "pan_start", "pan_end", "first_visible", "fight_activation", "camera", "player")


def build():
    ext = json.loads(A.F_EXT.read_text())
    out = OrderedDict(description="T3 summary metrics for C1-I 69527335 and final V1/T1 03db5e1c, widths 256/348/400, scenarios hold/stop. Update numbers are scenario-relative.",
                      sources={k: str(v.relative_to(ROOT)) for k, v in SRC.items()}, zones=OrderedDict())
    series = {k: json.loads(p.read_text()) for k, p in SRC.items()}
    for k, s in series.items():
        out.setdefault("poc_checkout_head", {})[k] = s.get("poc_checkout_head")
    for z in A.ZONES:
        zr = OrderedDict()
        for k, s in series.items():
            for wk, (w, h) in WID.items():
                for sc in ("hold", "stop"):
                    ps = s["zones"][z][wk][sc]
                    rows = ({c: ps[c][i] for c in ps} for i in range(len(ps["u"])))
                    zr[f"{k}_{wk}_{sc}"] = A.summarize(rows, (w, h), ext, z, "poc", sc)
        out["zones"][z] = zr
    return out


def d(x):
    return json.dumps(x, separators=(",", ":"))


def table(S):
    L = ["| zone | cfg | metric | C1-I | V1/T1 |", "|---|---|---|---|---|"]
    for z in A.ZONES:
        for wk in WID:
            for sc in ("hold", "stop"):
                a, b = S["zones"][z][f"c1i_{wk}_{sc}"], S["zones"][z][f"v1t1_{wk}_{sc}"]
                rows = [("x_retreat", a["camera"]["x_retreat"]["pixels"], b["camera"]["x_retreat"]["pixels"]),
                        ("creation_step", a["camera"]["creation_update_step"], b["camera"]["creation_update_step"]),
                        ("pan_max_step", a["camera"]["pan_max_abs_step"], b["camera"]["pan_max_abs_step"]),
                        ("y_up/down", [a["camera"]["y_total_up"], a["camera"]["y_total_down"]], [b["camera"]["y_total_up"], b["camera"]["y_total_down"]]),
                        ("lowered_before_pan", a["right_limit"]["lowered_before_pan"], b["right_limit"]["lowered_before_pan"]),
                        ("pan_end_cam", a["pan_end"] and a["pan_end"]["camera"], b["pan_end"] and b["pan_end"]["camera"]),
                        ("sonic_beyond_clamp", a["player"]["updates_beyond_right_clamp_plus_4"], b["player"]["updates_beyond_right_clamp_plus_4"])]
                for m, x, y in rows:
                    if x != y or m in ("x_retreat", "creation_step"):
                        L.append(f"| {z} | {wk} {sc} | {m} | {d(x)} | {d(y)} |")
    return "\n".join(L)


# ---- numeric contract: V1/T1 before, proposal-model after, per package / zone / width ---------------------------------------------------
def contract(S):
    z = S["zones"]
    def g(zone, k, w, sc):
        r = z[zone][f"{k}_{w}_{sc}"]; c = r["camera"]
        return OrderedDict(x_retreat=c["x_retreat"]["pixels"], creation_step=c["creation_update_step"], pan_max_step=c["pan_max_abs_step"], y_up_down=[c["y_total_up"], c["y_total_down"]],
                           pan_end_camera=r["pan_end"]["camera"], pan_start_camera=r["pan_start"]["camera"], right_limit_lowered_before_pan=r["right_limit"]["lowered_before_pan"],
                           sonic_beyond_clamp_plus_4=r["player"]["updates_beyond_right_clamp_plus_4"], sonic_screen_x_max=r["player"]["screen_x_max"])
    pk = OrderedDict()
    spec = [("T3-A", ["GPZ3", "SEZ3", "MGHZ3", "AQZ3"], "creation_step", "dx in [0,7], |dy| <= 7 at the creation update; no backward X step"),
            ("T3-B", ["AQZ3"], "right_limit_lowered_before_pan", "true; x_retreat 0; Sonic never beyond EDGE(RIGHT,-9)+4"),
            ("T3-C", ["GPZ3"], "x_retreat", "0 at every width; pan_end_camera X = 1664-(W-256)-1"),
            ("T3-D", ["EEZ3"], "pan_max_step", "Y step <= 1 per update in the pan (X <= 1); pan_end_camera Y 334 (ROM 334)"),
            ("T3-E", ["SEZ3", "MGHZ3"], "x_retreat", "0 at 256, 348 and 400 (secondary)")]
    for pid, zones, key, rule in spec:
        pk[pid] = OrderedDict(rule=rule, zones=OrderedDict())
        for zone in zones:
            pk[pid]["zones"][zone] = OrderedDict((f"{w}_{sc}", OrderedDict(before_v1t1=g(zone, "v1t1", w, sc), after_model=g(zone, "proposal", w, sc))) for w in WID for sc in ("hold", "stop"))
    thz = OrderedDict((f"{w}_{sc}", g("THZ3", "v1t1", w, sc)) for w in WID for sc in ("hold", "stop"))
    return OrderedDict(description="Numeric before/after contract. before = final V1/T1 03db5e1c (POC-SOURCE MODEL); after = PROPOSAL MODEL (tools/p4_proposal_model.js: in-memory camera decisions on the same source), not POC code. THZ3 is unchanged (V1/T1 already satisfies the contract).",
                       packages=pk, thz3_final_v1t1=thz)


F_CONTRACT = D / "p4-contract.json"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--write", action="store_true"); ap.add_argument("--check", action="store_true"); ap.add_argument("--table", action="store_true")
    a = ap.parse_args()
    S = build()
    if a.write or a.check:
        t2 = json.dumps(contract(json.loads(json.dumps(S))), separators=(",", ":")) + "\n"
        if a.write: F_CONTRACT.write_text(t2); print("wrote", F_CONTRACT.relative_to(ROOT), len(t2))
        else: print("CHECK p4-contract", "identical" if F_CONTRACT.exists() and F_CONTRACT.read_text() == t2 else "DIFFERENT")
    if a.table:
        print(table(json.loads(json.dumps(S)))); return 0
    t = json.dumps(S, separators=(",", ":")) + "\n"
    if a.write:
        OUT.write_text(t); print("wrote", OUT.relative_to(ROOT), len(t)); return 0
    same = OUT.exists() and OUT.read_text() == t
    print("CHECK baseline-summary", "identical" if same else "DIFFERENT"); return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())

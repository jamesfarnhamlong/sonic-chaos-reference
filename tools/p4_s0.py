#!/usr/bin/env python3
"""P4 preflight, assignment B: S0 stage-entry transition findings (Research only; no ROM and no POC needed to write, a checkout to verify anchors).

    python tools/p4_s0.py --write | --check
    python tools/p4_s0.py --verify <checkout>      # every source anchor still present at the recorded line (read only)
"""
from __future__ import annotations
import argparse, json, sys
from collections import OrderedDict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "p4" / "s0-source-findings.json"
POC = "03db5e1c53497e76bf9e8f511b1c98ec0443be90"

A = lambda f, a, l, why: OrderedDict(file=f, anchor=a, line=l, why=why)
ANCHORS = [
    A("objects/OBJ_chaos_zone/Create_0.gml", "chaos_act_load_begin();", 1, "first statement of every ordinary-act room start"),
    A("scripts/SCR_chaos_level/SCR_chaos_level.gml", "chaos_results_room_begin();", 656, "called from chaos_act_load_begin (line 654)"),
    A("scripts/SCR_chaos_results/SCR_chaos_results.gml", "global.chaosResults={phase:\"level_in\",age:0}", 24, "armed only when global.chaosResultsIncoming was set before the room change"),
    A("objects/OBJ_chaos_zone/Create_0.gml", "instance_create(0,0,OBJ_effect_fade_in);", 43, "legacy black fade object, created unconditionally, after the level_in arming"),
    A("objects/OBJ_effect_fade_in/Create_0.gml", "alpha = 1;", 2, "starts fully black"),
    A("objects/OBJ_effect_fade_in/Step_0.gml", "alpha -= 0.050", 2, "20 steps to clear; it is a Step-driven object, not time based"),
    A("scripts/SCR_chaos_results/SCR_chaos_results.gml", "instance_deactivate_all(true)", 243, "first level_in Draw: captures application_surface, then freezes every instance except the controls (the fade object included)"),
    A("scripts/SCR_chaos_results/SCR_chaos_results.gml", "else if(cp_phase==\"level_in\")", 253, "draws the captured frame through the SMS-style in_black steps: 0 (black), 1/3, 2/3 at ages 1-9, 10-14, 15-19"),
    A("scripts/SCR_chaos_results/SCR_chaos_results.gml", "case \"level_in\":if(cp_s.age>=20)", 198, "age 20: instance_activate_all(): player, zone, ring manager AND the frozen fade object resume"),
    A("scripts/SCR_chaos_results/SCR_chaos_results.gml", "global.chaosResultsIncoming=true;return true", 190, "end of the zone-title / loader_black phase: sets the flag, then room_goto(next act)"),
    A("scripts/SCR_chaos_death/SCR_chaos_death.gml", "global.chaosResultsIncoming=true;room_goto", 43, "death / continue respawn uses the same handoff"),
    A("scripts/SCR_chaos_debug_select/SCR_chaos_debug_select.gml", "    room_goto(cp_entry.room);", 73, "Level Select: no flag, so no level_in and no freeze"),
    A("objects/OBJ_menu_data_select/Alarm_2.gml", "SCR_zone_goto", 3, "Data Select START: legacy fade_out then room_goto, no flag"),
    A("objects/OBJ_chaos_controls/Draw_0.gml", "chaos_results_scene_draw(global.chaosResults,false)", 2, "controls (depth -10000) draw the capture above the level and below the fade object (depth -999999)"),
]


def build():
    fall = json.loads((ROOT / "data" / "p4" / "s0-poc-start-fall.json").read_text())
    return OrderedDict(
        description="S0: why a stage entered through its zone-title screen flashes black and Level Select does not (source reading of final V1/T1 03db5e1c + POC-SOURCE MODEL of the start fall). Mechanism is established from source; the order the player perceives is not observed.",
        poc_commit=POC,
        routes=OrderedDict([
            ("zone_title", "results/title phases -> loader_black -> chaosResultsIncoming=true -> room_goto -> zone Create: level_in armed AND OBJ_effect_fade_in created -> first Draw captures the frame and deactivates all instances (fade object frozen at alpha 0.95) -> 19 updates of the captured frame through black, 1/3, 2/3 -> update 20: everything resumes, fade object continues from 0.95 over the live level"),
            ("death_respawn", "same handoff (SCR_chaos_death.gml:43): the same flash is predicted after a respawn"),
            ("level_select", "chaos_debug_launch -> room_goto: only OBJ_effect_fade_in, running from update 1 (alpha 1 -> 0 in 20 steps, gameplay live): monotone fade, no dip"),
            ("data_select_start", "legacy fade_out (alpha +0.07) then room_goto: same as Level Select on arrival"),
        ]),
        predicted_brightness=OrderedDict([("zone_title", "0 for updates 1-9; 1/3 (10-14); 2/3 (15-19); then ~0.05 at update 20-21 (dip); then linear to 1.0 by update ~40"),
                                          ("level_select", "alpha 0.95 at update 1 falling 0.05 per update: monotone to 1.0 by update 20")]),
        rom_reference=OrderedDict([("source", "data/t2/zone-start.json (EMULATED)"), ("black_frames", "0-33 (palette sums 0)"), ("dim_steps", "frames 34, 39, 44 (three 5-frame steps)"),
                                   ("GPZ1_MGHZ1", "player state 14 from frame 30, +14 px over frames 30-37, floor contact frame 39-40: the drop is mostly under black/the dimmest step"),
                                   ("THZ1", "no drop; 7 px anchor flicker 654/661 in frames 35-38 under the first dim step (T2-11)"), ("gameplay_runs_during_fade", True)]),
        poc_start_fall=fall,
        poc_only_exposure=["gameplay is frozen for the 19 level_in updates (deactivate_all) - the ROM runs the player during its fade", "the fall therefore happens after the freeze, under the resumed fade object (alpha 0.95..), instead of under black",
                           "the resumed fade object adds a second fade on top of the finished SMS-style fade (dip to ~0.05)"],
        capture=OrderedDict(file="<working_directory>/s0_entry_trace.csv", columns=CAPTURE_COLUMNS, rows="first 90 Draw events after Room Start, one file per entry", routes=["Level Select -> GPZ1", "Level Select -> MGHZ1", "death respawn in GPZ1", "zone title -> GPZ1 (after THZ3)"],
                            confirms="in the zone-title and respawn routes: fade_exists flips false at update 1-2 and true at results_age 20 with fade_alpha 0.90-0.95, lum drops by > 0.25 within 2 updates of that release; the Level Select routes show lum monotone"),
        anchors=ANCHORS)


def verify(poc):
    bad = 0
    for a in ANCHORS:
        p = Path(poc) / a["file"]
        ls = p.read_text(errors="replace").split("\n") if p.exists() else []
        hits = [i + 1 for i, l in enumerate(ls) if a["anchor"] in l]
        st = "ok" if a["line"] in hits else ("MOVED " + str(hits) if hits else "MISSING")
        bad += st != "ok"
        print(f"{st:10} {a['file']}:{a['line']}  {a['anchor'][:60]}")
    return 1 if bad else 0


CAPTURE_COLUMNS = ["u", "room", "route", "results_phase", "results_age", "fade_exists", "fade_alpha", "player_y", "core_state", "floor", "view_y", "lum"]


def analyze(rows):
    """rows: dicts with the CAPTURE_COLUMNS (numbers parsed). Verdict on the one question: does the brightness fall again after the fade-in has started?
    lum = mean luminance 0..1 of three sample pixels of application_surface at the end of the Draw event."""
    lum = [float(r["lum"]) for r in rows]
    first = next((i for i, v in enumerate(lum) if v > 0.02), None)
    if first is None:
        return OrderedDict(verdict="no light", dips=[])
    dips = [OrderedDict(u=rows[i]["u"], before=round(lum[i - 1], 3), after=round(lum[i], 3)) for i in range(first + 1, len(lum)) if lum[i] < lum[i - 1] - 0.25]
    phase_end = next((rows[i]["u"] for i in range(1, len(rows)) if rows[i - 1]["results_phase"] == "level_in" and rows[i]["results_phase"] != "level_in"), None)
    alpha_at_release = next((float(rows[i]["fade_alpha"]) for i in range(1, len(rows)) if rows[i - 1]["results_phase"] == "level_in" and rows[i]["results_phase"] != "level_in"), None)
    return OrderedDict(first_lit_update=rows[first]["u"], dips=dips, level_in_released_at=phase_end, fade_alpha_after_release=alpha_at_release,
                       verdict="DIP: the fade object resumes over a finished fade" if dips else "monotone fade-in")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--write", action="store_true"); ap.add_argument("--check", action="store_true"); ap.add_argument("--verify"); ap.add_argument("--analyze", metavar="CSV")
    a = ap.parse_args()
    if a.verify: return verify(a.verify)
    if a.analyze:
        import csv
        print(json.dumps(analyze(list(csv.DictReader(open(a.analyze)))), indent=1)); return 0
    t = json.dumps(build(), indent=1) + "\n"
    if a.write: OUT.write_text(t); print("wrote", OUT.relative_to(ROOT)); return 0
    same = OUT.exists() and OUT.read_text() == t; print("CHECK s0-source-findings", "identical" if same else "DIFFERENT"); return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())

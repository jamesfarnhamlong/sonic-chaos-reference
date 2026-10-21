#!/usr/bin/env python3
"""T3: boss walk-on / widescreen framing matrix, adapter register and discrepancy register (Research only; no ROM and no POC needed).

Everything numeric is read from the committed T3 series and summary (data/t3/*.json); the classification text is authored here.

    python tools/t3_register.py --write                 # data/t3/boss-framing-matrix.json, adapter-register.json, discrepancy-register.json
    python tools/t3_register.py --check                 # regenerate in memory, compare with the committed files
    python tools/t3_register.py --tables                # markdown tables used by docs/t3-boss-walkon-framing-audit.md
    python tools/t3_register.py --verify-anchors POC    # every adapter anchor still exists in the POC checkout (read only); prints drift
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "t3"
OUT = {"matrix": D / "boss-framing-matrix.json", "adapters": D / "adapter-register.json", "register": D / "discrepancy-register.json"}
STATUSES = ("proven-match", "adapter-difference", "proven-gap", "not-audited", "unresolved")
KINDS = ("ROM-recovered", "deliberate widescreen adapter", "legacy non-ROM rule", "omission of a ROM rule")
POC_COMMIT = "69527335011bacf22ff16bd25d3a94874a1fa563"
ZONES = ["THZ3", "GPZ3", "SEZ3", "MGHZ3", "AQZ3", "EEZ3"]
CFG = ("rom_hold", "poc_w256_hold", "poc_w348_hold")


def load(name):
    return json.loads((D / name).read_text())


SUM = load("boss-walkon-summary.json")["zones"]
SERIES = load("poc-series.json")["zones"]


def S(z, k):
    return SUM[z][k]


def pct(a, b):
    return f"{a}/{b}"


# ------------------------------------------------------------------------------------------------------------------ matrix
ENTRY = OrderedDict([
    ("THZ3", OrderedDict(mode="walks in from the right edge by its own motion", detail="no relocation. State 18 starts at the pan (X velocity -128 = -0.5 px/update) with the anchor 271 px from the camera (sliver of 5 columns); the camera pans +16 px at the same time; the walk ends when the anchor is 223 px right of the live camera (state 6).")),
    ("GPZ3", OrderedDict(mode="relocated at creation, invisible, then emerges in place", detail="the placement (1728,270) is moved to (1856,270) one update after creation (screen X 462, off-screen); mapping frame 0 (no sprite) until the camera-ready gate; the head then appears in one update at screen (193,173) and rises. Nothing walks in from the right.")),
    ("SEZ3", OrderedDict(mode="relocated at state 3, then drops from above the screen", detail="at state 3 the anchor jumps from the placement (3200,622) to (3136,430): screen X 209 but screen Y -83, above the top. The body falls into view; all 40 columns appear at once. Sonic can be right of the boss (T2-14).")),
    ("MGHZ3", OrderedDict(mode="revealed by the camera pan; descends", detail="no relocation; the anchor X stays at 3269. State 11 starts at the pan with the anchor at screen X 272 / Y -4; the +52 px pan brings the left edge from the right edge into view (4 columns at first) while the body falls.")),
    ("AQZ3", OrderedDict(mode="body relocated up and hidden; child $5A parts fly in from the right", detail="at state 3 the body anchor jumps (1856,238) -> (1856,14), above the screen; the visible parts ($5A, frame 29...) are created off-screen right (WORLD 2048 = EDGE(RIGHT,+65) at the settled camera) and move left; first visible 1 column at screen X 259.")),
    ("EEZ3", OrderedDict(mode="relocated at state 3, held invisible, appears at the right edge and walks in", detail="at state 3 the anchor jumps 2080 -> 2208 (screen 337, off-screen right); state 12 keeps mapping frame 0 (no sprite) while the 1 px/update pan brings the anchor to screen 257; state 6 then shows it there (15 columns) and walks it left.")),
])


def point(s):
    if s is None:
        return None
    return OrderedDict((k, s[k]) for k in s if k in ("u", "camera", "player_world_x", "player_screen_x", "boss_world", "boss_screen_x", "boss_screen_y", "anchor_screen", "visible_columns"))


def matrix():
    out = OrderedDict(
        description="Six-zone boss walk-on matrix: ROM (EMULATED, 256), POC C1-I at 256 and 348 (POC-SOURCE MODEL), scenario 'hold' (RIGHT held through the intro). All numbers are read from data/t3/boss-walkon-summary.json.",
        poc_commit=POC_COMMIT, scenario="hold", zones=OrderedDict())
    for z in ZONES:
        zr = OrderedDict(entry_mode=ENTRY[z], configs=OrderedDict())
        for k in CFG:
            s = S(z, k)
            zr["configs"][k] = OrderedDict(
                created=s["created"], relocations=s["relocations"], right_limit=s["right_limit"], pan_start=point(s["pan_start"]), pan_end=point(s["pan_end"]),
                first_visible=s["first_visible"], fight_activation=point(s["fight_activation"]), camera=s["camera"], player=s["player"],
                pan_updates=None if not (s["pan_start"] and s["pan_end"]) else s["pan_end"]["u"] - s["pan_start"]["u"])
        zr["rom_camera_in_348_window"] = S(z, "rom_hold_same_camera_in_348")["first_visible"]
        out["zones"][z] = zr
    return out


# ------------------------------------------------------------------------------------------------------------------ adapters
def A(i, z, kind, file, anchor, what, rom_basis, line=None):
    assert kind in KINDS
    return OrderedDict(id=i, zone=z, kind=kind, file=file, anchor=anchor, line_at_c1i=line, what=what, rom_basis=rom_basis)


ADAPTERS = [
    A("A-THZ-1", "THZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_boss/SCR_chaos_boss.gml", "function chaos_boss_creation_band", "creation band measured from the live right edge, not from a 256 px window", "ROM creates the object in the outer spawn ring of the 256 px window ($80EB, object-50.json placement_window)", 14),
    A("A-THZ-2", "THZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_boss/SCR_chaos_boss.gml", "function chaos_boss_clamp", "arena right edge and patrol right turn extended by W-256 (world rectangle)", "none: the ROM arena is the screen clamp at the locked camera; T2 shows the viewport clamp gives the same rectangle", 32),
    A("A-THZ-3", "THZ3", "legacy non-ROM rule", "scripts/SCR_chaos_boss/SCR_chaos_boss.gml", "cp_x=max(cp_b.camera_min,min(room_width-cp_vp.w,round(instance_find(OBJ_player,0).x-cp_vp.w/2)))", "mode 1 follows Sonic by centring him (never back-scrolling); Y is frozen at the creation value for modes 1-2", "ROM keeps the ordinary $5832 follow (lead 104/136, zone +-8/+-16, cap 7) and only raises the left limit (state 1 $9771 -> $8199)", 246),
    A("A-THZ-4", "THZ3", "ROM-recovered", "scripts/SCR_chaos_boss/SCR_chaos_boss.gml", "cp_x=cp_vp.left+sign(CHAOS_BOSS_CAMERA_X-cp_vp.left)", "mode 3 pan 1 px/update/axis to (1679,78) at every width", "table $9808 row 0: anchor + (-256,-160), exclusive right limit", 250),
    A("A-THZ-5", "THZ3", "ROM-recovered", "scripts/SCR_chaos_boss/SCR_chaos_boss.gml", "if (chaos_boss_x(cp_b)-cp_b.camera_x <= 223)", "state 18 ends when the anchor is 223 px right of the LIVE camera (world 1902 after the pan), at every width", "state 18 exit (object-50.json state_18_exit)", 119),
    A("A-THZ-6", "THZ3", "legacy non-ROM rule", "scripts/SCR_chaos_boss/SCR_chaos_boss.gml", "cp_x=clamp(round(instance_find(OBJ_player,0).x-cp_vp.w/2),cp_vp.left,room_width-cp_vp.w)", "mode 4 (release) centres on Sonic in one update", "ROM resumes the ordinary follow, <= 7 px/update (T1-02)", 255),
    A("A-GPZ-1", "GPZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_gpz_boss/SCR_chaos_gpz_boss.gml", "function chaos_51_fight_camera_target", "fight camera X target 1664-(W-256) (1572 at 348): keeps the canonical RIGHT edge 1919 and exposes the extra width to the LEFT", "ROM target is LOCKED_CAMERA(1664,96), settles (1663,97)", 24),
    A("A-GPZ-2", "GPZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_gpz_boss/SCR_chaos_gpz_boss.gml", "function chaos_51_fight_camera_y", "fight camera Y 96 -> 112 for wide, tall views (presentation only)", "ROM target Y 96", 28),
    A("A-GPZ-3", "GPZ3", "omission of a ROM rule", "scripts/SCR_chaos_gpz_boss/SCR_chaos_gpz_boss.gml", "cp_b.camera_right=1664; cp_s.xu=1856*256;", "the creation callback writes the CANONICAL right limit 1664 (exclusive camera limit, right edge 1920) at every width; the adapter in A-GPZ-1 is not applied to the limit", "ROM $9A99 writes D282 = 1664 and relocates the head 1728 -> 1856 (one update after creation); the limit is WORLD-fixed 270 px ahead of the camera", 114),
    A("A-GPZ-4", "GPZ3", "legacy non-ROM rule", "scripts/SCR_chaos_gpz_boss/SCR_chaos_gpz_boss.gml", "var cp_follow_x=clamp(round(instance_find(OBJ_player,0).x-cp_vp.w/2),cp_b.camera_left,cp_b.camera_right-1);", "modes 1 and 4: centre on Sonic horizontally; vertical target player.y - h/1.5; one-update snap at 256, 4 px/update at wide", "ROM keeps the ordinary follow throughout the approach (no mode-1 owner)", 298),
    A("A-GPZ-5", "GPZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_gpz_boss/SCR_chaos_gpz_boss.gml", "if (cp_vp.w>256 && !cp_b.camera_owned && cp_b.last_view_valid)", "first takeover starts from the last normal view, not from GameMaker's object-follow value", "none (continuity of the adapter)", 283),
    A("A-GPZ-6", "GPZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_gpz_boss/SCR_chaos_gpz_boss.gml", "if (cp_vp.w>256) cp_x+=sign(cp_target-1-cp_x);", "mode 2/3 approach to the width-adjusted target from EITHER side at 1 px/update (no snap)", "ROM pan is 1 px/update/axis toward (1664,96)", 293),
    A("A-SEZ-1", "SEZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_sez_boss/SCR_chaos_sez_boss.gml", "function chaos_54_target_x", "pan target X = 3232 - W (canonical RIGHT edge kept; extra width to the left); Y stays 462", "ROM target (2976,462), settles (2975,462)", 81),
    A("A-SEZ-2", "SEZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_sez_boss/SCR_chaos_sez_boss.gml", "cp_x+=clamp(cp_tx-1-cp_x,-4,4); cp_y+=clamp(cp_ty-cp_y,-4,4);", "wide pan bounded to 4 px/update per axis", "ROM pan is 1 px/axis/update", 550),
    A("A-SEZ-3", "SEZ3", "legacy non-ROM rule", "scripts/SCR_chaos_sez_boss/SCR_chaos_sez_boss.gml", "var cp_fx2=chaos_54_follow_x(cp_b,cp_vp,cp_px),cp_fy2=chaos_54_follow_y(cp_vp,cp_py);", "modes 1-2: X centres on Sonic (left limit raised, so the camera stalls until Sonic passes the centre); Y = player.y - h/1.5 (snap at 256, 4 px/update wide)", "ROM keeps the ordinary follow (lead 104, Y lead 96/120, zone +-8/+-16, cap 7)", 592),
    A("A-SEZ-4", "SEZ3", "ROM-recovered", "scripts/SCR_chaos_sez_boss/SCR_chaos_sez_boss.gml", "if (cp_b.camera_right >= cp_vp.left) cp_b.camera_right=cp_vp.left;", "trigger lowers the right limit to the camera ($0356)", "shared boss state 1/2 ($9771/$9799)", 247),
    A("A-MGH-1", "MGHZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_mghz_boss/SCR_chaos_mghz_boss.gml", "function chaos_56_target_x", "pan target X = 3269 - (W-48): boss stays at RIGHT-48 (209 at 256, 301 at 348); canonical right edge kept", "ROM target (3061,256), settles (3060,256)", 69),
    A("A-MGH-2", "MGHZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_mghz_boss/SCR_chaos_mghz_boss.gml", "cp_x+=clamp(cp_tx-1-cp_x,-4,4); cp_y+=clamp(cp_ty-cp_y,-4,4);", "wide pan bounded to 4 px/update per axis", "ROM pan is 1 px/axis/update", 477),
    A("A-MGH-3", "MGHZ3", "legacy non-ROM rule", "scripts/SCR_chaos_mghz_boss/SCR_chaos_mghz_boss.gml", "var cp_fx2=chaos_56_follow_x(cp_b,cp_vp,cp_px),cp_fy2=chaos_56_follow_y(cp_vp,cp_py,cp_y);", "modes 1-2: Y target player.y - h/1.5 capped 7 (256) / 4 (wide) per update; X centres on Sonic with the left limit raised", "ROM keeps the ordinary follow; the pan Y target is 256 only from state 3", 519),
    A("A-MGH-4", "MGHZ3", "ROM-recovered", "scripts/SCR_chaos_mghz_boss/SCR_chaos_mghz_boss.gml", "if (cp_b.camera_right >= cp_vp.left) cp_b.camera_right=cp_vp.left;", "trigger lowers the right limit to the camera ($0356)", "shared boss state 1/2", 192),
    A("A-AQZ-1", "AQZ3", "omission of a ROM rule", "scripts/SCR_chaos_aqz_boss/SCR_chaos_aqz_boss.gml", "case $9771:", "state 1 copies the right limit but never raises the left limit to the camera ($8199 -> $0353) and never lowers the right limit to the camera at the trigger ($0356)", "ROM: right limit := camera at the trigger (u99: limit 1642 with the camera at 1646), left raised every update (data/t2/boss-arrival.json AQZ)", 285),
    A("A-AQZ-2", "AQZ3", "legacy non-ROM rule", "scripts/SCR_chaos_aqz_boss/SCR_chaos_aqz_boss.gml", "var cp_fx2=chaos_59_follow_x(cp_b,cp_vp,cp_px),cp_fy2=chaos_59_follow_y(cp_vp,cp_py);", "modes 1-2 centre on Sonic horizontally (limit = camera_right, which is never lowered, see A-AQZ-1) and use player.y - h/1.5 vertically", "ROM keeps the ordinary follow", 627),
    A("A-AQZ-3", "AQZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_aqz_boss/SCR_chaos_aqz_boss.gml", "cp_s.view_dx=cp_b.intro_dx;", "the $5A parts get a fixed VIEW-space translation intro_dx = W-256+ceil(wait/2) when the intro callback $AC38 runs; draw AND contact use the translated X; canonical xu is never changed", "ROM spawns the parts at WORLD 2048 = EDGE(RIGHT,+65) of the settled 256 px camera", 55),
    A("A-AQZ-4", "AQZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_aqz_boss/SCR_chaos_aqz_boss.gml", "if (cp_b.intro_stable >= 16) cp_b.intro_ready=true;", "at wide the $5A parts are hidden and skipped until the pan has been settled for 16 updates", "none", 610),
    A("A-EEZ-1", "EEZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_eez_boss/SCR_chaos_eez_boss.gml", "chaos_eez_boss_setx(cp_s,cp_x+128+max(0,cp_v.w-256))", "state 3 relocation adds W-256 to the canonical +128 (2208 at 256, 2300 at 348): a WORLD coordinate change that keeps the boss off-screen right at the settled camera", "ROM relocates 2080 -> 2208 (screen 337 before the pan, 257 after)", 150),
    A("A-EEZ-2", "EEZ3", "deliberate widescreen adapter", "scripts/SCR_chaos_eez_boss/SCR_chaos_eez_boss.gml", "(cp_v.w>256 && floor(cp_c.xu/256)>=cp_x", "wide trigger also fires when Sonic is right of the boss inside the view", "ROM trigger: strict |dx| < 96, |dy| < 304", 143),
    A("A-EEZ-3", "EEZ3", "ROM-recovered", "scripts/SCR_chaos_eez_boss/SCR_chaos_eez_boss.gml", "cp_target=floor(cp_v.w/2)+((cp_core.player_flags&16) != 0 ? 8 : -24);", "follow with the ROM zone/lead/cap form (CENTER-relative leads at wide), left/right/bottom limits written by the boss", "$5832/$58E1 with the boss limits", 325),
    A("A-EEZ-4", "EEZ3", "omission of a ROM rule", "scripts/SCR_chaos_eez_boss/SCR_chaos_eez_boss.gml", "cp_y+=sign(cp_b.pan_y-cp_y);cp_y=min(cp_y,cp_b.bottom-1);", "the pan clamps the camera Y to the new bottom limit in the first pan update", "ROM pans 1 px/update from the current Y (387 -> 334 in 53 updates, no clamp)", 323),
    A("A-SH-1", "ALL", "legacy non-ROM rule", "scripts/SCR_chaos_camera/SCR_chaos_camera.gml", "function chaos_camera_follow_allowed", "the C1-I ordinary follow is switched off as soon as ANY boss owner is active (THZ3 mode != 0, GPZ3 active, MGHZ3/SEZ3/AQZ3 active); the ROM has no such owner switch before the pan", "ROM O4/O5: the ordinary follow keeps running with the left limit raised and, after the trigger, the right limit at the camera (data/t2/owner-map.json)", 98),
    A("A-SH-2", "ALL", "deliberate widescreen adapter", "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml", "chaos_56_owns_camera() || chaos_54_owns_camera() || chaos_59_owns_camera()", "player edge clamp EDGE(LEFT,+16)..EDGE(RIGHT,-9) of the live view as full-width integers, applied from boss creation for GPZ3/MGHZ3/SEZ3/AQZ3 (T2-04: THZ3 is not in the list)", "$4141: unconditional below state $29", 199),
]


def adapters():
    return OrderedDict(description="Camera/arrival adapters and rules of the accepted POC C1-I, classified. 'kind' separates recovered ROM behaviour, deliberate widescreen adapters (documented in the code header), legacy non-ROM rules (inherited from the pre-C1-I zone cameras, not documented as an adapter and not matched to the ROM) and omissions of a ROM rule. line_at_c1i is the line in the C1-I checkout; anchor is the text to search after a re-baseline.",
                       poc_commit=POC_COMMIT, rows=ADAPTERS)


def verify_anchors(poc):
    bad = 0
    for a in ADAPTERS:
        p = Path(poc) / a["file"]
        lines = p.read_text(errors="replace").split("\n") if p.exists() else []
        hits = [i + 1 for i, l in enumerate(lines) if a["anchor"] in l]
        state = "ok" if hits and (a["line_at_c1i"] is None or a["line_at_c1i"] in hits) else ("MOVED " + str(hits) if hits else "MISSING")
        if state != "ok":
            bad += 1
        print(f"{a['id']:9} {a['file'].split('/')[-1]:28} {state}")
    return 1 if bad else 0


# ------------------------------------------------------------------------------------------------------------------ register
def R(i, scope, finding, rom, poc, method, status, impact, group, proof, evidence):
    assert status in STATUSES
    return OrderedDict(id=i, scope=scope, finding=finding, rom_datum=rom, poc_code_path=poc, comparison_method=method, status=status, gameplay_impact=impact, proposed_work_group=group, acceptance_proof=proof, evidence=evidence)


def register():
    g3, g3w = S("GPZ3", "poc_w256_hold"), S("GPZ3", "poc_w348_hold")
    gr = S("GPZ3", "rom_hold")
    ps, pe = g3w["pan_start"], g3w["pan_end"]
    mz, mw, mr = S("MGHZ3", "poc_w256_stop"), S("MGHZ3", "poc_w348_stop"), S("MGHZ3", "rom_stop")
    sz, sw = S("SEZ3", "poc_w256_hold"), S("SEZ3", "poc_w348_hold")
    az, aw, ar = S("AQZ3", "poc_w256_hold"), S("AQZ3", "poc_w348_hold"), S("AQZ3", "rom_hold")
    azs, aws = S("AQZ3", "poc_w256_stop"), S("AQZ3", "poc_w348_stop")
    ez, ew, er = S("EEZ3", "poc_w256_hold"), S("EEZ3", "poc_w348_hold"), S("EEZ3", "rom_hold")
    tz, tw = S("THZ3", "poc_w256_hold"), S("THZ3", "poc_w348_hold")
    exp = {z: S(z, "rom_hold_same_camera_in_348")["first_visible"] for z in ZONES}
    rv = {z: S(z, "rom_hold")["first_visible"] for z in ZONES}
    rows = [
        R("T3-01", "GPZ3 boss intro, 348 px (reported observation 1: camera rolls backwards)",
          f"The camera runs forward to the canonical right limit (X 1663; {ps['camera'][0]} at the first pan update), then the pan retreats {g3w['camera']['x_retreat']['pixels']} px to the width-adjusted fight target 1571, at 1 px/update for {g3w['pan_end']['u'] - ps['u']} updates (u{ps['u']}..u{pe['u']}). The clamp carries Sonic with it: world X {ps['player_world_x']} -> {pe['player_world_x']}. The head, invisible until the end of the pan, then appears at screen X {g3w['first_visible']['anchor_screen'][0]} (193 at 256). At 256 the camera never moves left after the approach (retreat {g3['camera']['x_retreat']['pixels']} = the takeover snap only); the ROM never moves left (retreat {gr['camera']['x_retreat']['pixels']}).",
          "GPZ3 $9A99: D282 := 1664 (exclusive; right edge 1920) at creation, head 1728 -> 1856; pan target LOCKED_CAMERA(1664,96) settles (1663,97); the camera runs INTO the limit and stops; no leftward camera motion (rom_hold x_retreat 0)",
          "SCR_chaos_gpz_boss.gml:114 camera_right=1664 (not width-adjusted) vs :24 chaos_51_fight_camera_target = 1664-(W-256); :293 approach from either side at 1 px/update",
          "POC-SOURCE MODEL data/t3/poc-series.json GPZ3 w348 hold vs w256 vs rom-series.json (EMULATED)", "proven-gap",
          "The camera scrolls back 92 px with Sonic dragged left by the viewport clamp, while the boss head is still invisible; visible on every approach that carries the camera to the limit (Sonic beyond boss X 1745)",
          "T3-A (GPZ3 limit)", "camera X non-decreasing from creation to fight; final camera (1571,112) at 348 and (1663,96) at 256; right screen edge 1919 at the fight in both",
          ["A-GPZ-3", "A-GPZ-1"]),
        R("T3-02", "GPZ3, SEZ3, AQZ3, MGHZ3 creation-time camera takeover (256 and 348)",
          f"At boss creation the ordinary C1-I follow is replaced by a rigid centre follow. At 256 the camera steps backwards in ONE update: GPZ3 {g3['camera']['creation_update_step']}, SEZ3 {sz['camera']['creation_update_step']}, AQZ3 {az['camera']['creation_update_step']} (X,Y); MGHZ3 Y -7 per update for 4 updates ({mz['camera']['creation_update_step']} at the creation update). At 348 the same takeover is bounded to 4 px/update (GPZ3 {g3w['camera']['creation_update_step']}, SEZ3 {sw['camera']['creation_update_step']}, AQZ3 {aw['camera']['creation_update_step']}). THZ3 and EEZ3 have none. The ROM has no takeover: the ordinary follow keeps running (rom steps at creation {gr['camera']['creation_update_step']}, SEZ3 {S('SEZ3','rom_hold')['camera']['creation_update_step']}).",
          "ROM boss states 0/1 never change the follow; only the left limit is raised each update ($9771 -> $8199 -> $0353)",
          "SCR_chaos_camera.gml:98 chaos_camera_follow_allowed returns false once the boss is active; per-zone modes 1-2: SCR_chaos_{gpz:298,sez:592,mghz:519,aqz:627}",
          "POC-SOURCE MODEL (creation_update_step in data/t3/boss-walkon-summary.json)", "proven-gap",
          "A one-frame backward camera snap of 12 px and a Sonic position jump of 12-16 px on screen the moment the boss appears (256); a small bounded slide at 348",
          "T3-A (shared follow continuity)", "|camera step| at the creation update <= 7 (the ROM cap) at 256 and <= 7 at 348; no negative X step at creation; Sonic screen X changes by <= his own movement + the ROM follow step", ["A-SH-1", "A-GPZ-4", "A-SEZ-3", "A-AQZ-2", "A-MGH-3"]),
        R("T3-03", "MGHZ3 boss intro (reported observation 2: camera pans upwards)",
          f"Two vertical movements, only the second is in the ROM. (1) At creation the POC camera Y goes UP {mz['camera']['y_total_up']} px at 256 ({mw['camera']['y_total_up']} px at 348) in 4 (8) updates to player.y - h/1.5 (Y 238/235) because modes 1-2 keep the pre-C1-I vertical rule; the ordinary follow had Sonic at screen Y 99. (2) The pan then moves Y back DOWN {mz['camera']['y_total_down']} px ({mw['camera']['y_total_down']} px at 348) to 256 while X pans. In the ROM (Sonic standing, 'stop') the camera Y changes {mr['camera']['y_total_up'] + mr['camera']['y_total_down']} px in total ({mr['camera']['y_range']}) because the ordinary follow already holds Y within the pan target's zone.",
          "pan table $9808 row 3: anchor + (-208,-32) = (3061,256); bottom limit 256 written first; the camera Y at the trigger comes from the ordinary follow (Y 258 in the ROM run)",
          "SCR_chaos_mghz_boss.gml:437 chaos_56_follow_y = clamp(round(player.y-h/1.5)), capped 7 (256) / 4 (wide) per update; :519 mode-1/2 branch",
          "POC-SOURCE MODEL data/t3/poc-series.json MGHZ3 w256/w348 stop vs rom-series.json MGHZ3 stop", "proven-gap",
          "An extra upward scroll of about 30 px as the boss appears (floor drops to Sonic screen Y 128), then a partial scroll back down during the pan",
          "T3-A", "camera Y changes at most the ROM follow step (<= 7) per update from creation; |total Y travel| from creation to pan end <= |Y(trigger) - 256| + 2; pan end Y = 256 at both widths", ["A-MGH-3"]),
        R("T3-04", "MGHZ3 timing at 348 vs 256",
          f"Creation is measured from the live right edge (u{S('MGHZ3','poc_w348_stop')['created']['u']} vs u{mz['created']['u']}); the HUD wait that gates the pan is the same 100 updates after creation, so the pan starts at u{mw['pan_start']['u']} vs u{mz['pan_start']['u']}. The wide pan is bounded to 4 px/update: {mw['pan_end']['u'] - mw['pan_start']['u']} updates (X {mw['pan_start']['camera'][0]} -> {mw['pan_end']['camera'][0]}, Y {mw['pan_start']['camera'][1]} -> {mw['pan_end']['camera'][1]}) against {mz['pan_end']['u'] - mz['pan_start']['u']} at 256 (1 px/update, X {mz['pan_start']['camera'][0]} -> {mz['pan_end']['camera'][0]}). The boss starts descending (state 11) at the pan start in both: at 256 the camera is still panning for {mz['pan_end']['u'] - mz['fight_activation']['u']} updates of the fight, at 348 for {mw['pan_end']['u'] - mw['fight_activation']['u']}. The boss ends at screen X {mw['pan_end']['boss_screen_x']} (209 at 256).",
          "pan 1 px/axis/update; state 11 starts at the pan (ROM rom_hold: u170, pan u168..u220)", "SCR_chaos_mghz_boss.gml:477 (4 px wide pan), :69 (target 3269-(W-48))",
          "POC-SOURCE MODEL", "adapter-difference", "Different pan duration and a different boss position on screen; combat is not gated by the pan in the ROM or the POC",
          "decision D-T3-3", "if the ROM rate is kept: pan updates at 348 = max(|dX|,|dY|) = 29 (still <= the 256 value)", ["A-MGH-1", "A-MGH-2"]),
        R("T3-05", "AQZ3 arena lock missing (not reported; found by this audit)",
          f"The POC trigger sets mode 2 but never lowers the right limit to the camera and never raises the left limit; the right limit stays {az['right_limit']['at_creation']} until the pan, so the camera keeps following Sonic. With RIGHT held it reaches X {az['pan_start']['camera'][0]} at the pan start (ROM: {ar['pan_start']['camera'][0]}), then the pan retreats {az['camera']['x_retreat']['pixels']} px at 1 px/update over {az['pan_end']['u'] - az['pan_start']['u']} updates (348: {aw['camera']['x_retreat']['pixels']} px). A player who stops at the trigger still sees {azs['camera']['x_retreat']['pixels']} px (348: {aws['camera']['x_retreat']['pixels']}). In the model Sonic then stays at world X 2043 (core next state $1F) while the camera retreats past him (screen X {az['player']['screen_x_max']} of 256); the cause was not examined and may be harness-specific, so it is not used as evidence.",
          "AQZ3 $9771 -> $8199/$0353 each update, trigger -> $0356 (ROM: limit 1642 with the camera at 1646 on u99; data/t2/boss-arrival.json AQZ)",
          "SCR_chaos_aqz_boss.gml:285 case $9771 copies limit_right only; compare SCR_chaos_sez_boss.gml:247 and SCR_chaos_mghz_boss.gml:192", "POC-SOURCE MODEL (AQZ3 w256/w348 hold and stop) vs EMULATED rom hold", "proven-gap",
          "AQZ3 boss intro: the camera scrolls ahead of the arena and then rolls back, and the arena is not bounded to the trigger view",
          "T3-B (AQZ3 lock)", "right limit <= camera + 8 from the trigger update; camera X constant from trigger to pan start; Sonic screen X <= W-6 for every update; no negative camera X step before the fight", ["A-AQZ-1", "A-AQZ-2"]),
        R("T3-06", "EEZ3 boss pan start (not reported; model-derived)",
          f"The first pan update clamps the camera Y to the new bottom limit: largest Y step in the pan {ez['camera']['pan_max_abs_step'][1]} px at 256 and {ew['camera']['pan_max_abs_step'][1]} px at 348, in ONE update at the pan start (Y {ez['camera']['y_range'][1]} -> {ez['pan_start']['camera'][1]}). The ROM writes the bottom limit first and then pans 1 px/update (Y {er['pan_start']['camera'][1]} -> {er['pan_end']['camera'][1]}; largest Y step in the pan {er['camera']['pan_max_abs_step'][1]}).",
          "EEZ3 state 2 -> 3: D27E := target Y, then the shared pan; no clamp of the current Y",
          "SCR_chaos_eez_boss.gml:323 cp_y=min(cp_y,cp_b.bottom-1)", "POC-SOURCE MODEL EEZ3 vs EMULATED", "unresolved",
          "A 25-49 px vertical camera jump at the start of the EEZ3 boss pan if the model is faithful; needs a Windows capture",
          "T3-C (EEZ3 pan)", "camera Y step <= 1 per update (256) during the pan; <= 4 at 348 if the wide adapter is kept", ["A-EEZ-4"]),
        R("T3-07", "Boss-arrival classification (relocated / walks in / revealed by the camera)",
          "ROM: THZ3 walks in from the right by its own motion; GPZ3 relocates at creation then emerges in place; SEZ3 relocates at state 3 and drops from above; MGHZ3 is revealed by the pan while it descends; AQZ3 hides the body above the screen and flies the $5A parts in from the right; EEZ3 relocates at state 3, stays invisible through state 12 and appears at the right edge when state 6 starts, then walks in. No universal screen-edge rule exists.",
          "rom-series.json relocations and first_visible per zone (EMULATED + frame extents BYTE-VERIFIED)", "data/t3/boss-framing-matrix.json entry_mode", "EMULATED", "proven-match",
          "Defines what 'canonical' means per zone for the presentation decisions", "decision D-T3-2", "n/a (descriptive)", []),
        R("T3-08", "Boss exposed earlier / more completely by the wider view (item 6)",
          f"With the ROM camera unchanged a 348 px window shows the first visible frame with more of the sprite: THZ3 {exp['THZ3']['visible_columns']} of 40 columns (256: {rv['THZ3']['visible_columns']}), MGHZ3 {exp['MGHZ3']['visible_columns']} of 32 ({rv['MGHZ3']['visible_columns']}), EEZ3 {exp['EEZ3']['visible_columns']} columns ({rv['EEZ3']['visible_columns']}); AQZ3 parts appear {rv['AQZ3']['u'] - exp['AQZ3']['u']} updates earlier. GPZ3 and SEZ3 are unchanged (the sprite appears fully in place at 256 too). The POC at 348 shows THZ3 with {tw['first_visible']['visible_columns']} columns at screen X {tw['first_visible']['anchor_screen'][0]}, MGHZ3 {S('MGHZ3','poc_w348_hold')['first_visible']['visible_columns']} columns at {S('MGHZ3','poc_w348_hold')['first_visible']['anchor_screen'][0]}, GPZ3 at screen X {g3w['first_visible']['anchor_screen'][0]}; EEZ3 shows {ew['first_visible']['visible_columns']} columns (the relocation keeps the ROM sliver) and AQZ3 hides the parts until the pan has settled 16 updates.",
          "ROM sliver entries: THZ3 5 columns, MGHZ3 4, EEZ3 15, AQZ3 1 (data/t3/rom-series.json, frame-extents.json)", "A-THZ-2, A-EEZ-1, A-AQZ-3/4", "EMULATED + POC-SOURCE MODEL", "adapter-difference",
          "THZ3 and MGHZ3 bosses pop into the right edge region instead of sliding in; no boss is visible before it exists or before its state allows it", "decision D-T3-2", "first-visible anchor screen X and columns recorded per width", ["A-THZ-2", "A-EEZ-1", "A-AQZ-3"]),
        R("T3-09", "Horizontal framing of Sonic during modes 1-2",
          f"Because the left limit is raised to the camera and the target is the view centre, the camera stalls until Sonic passes the centre. Sonic's screen X when the arena right limit is lowered (the lock): MGHZ3 ROM {S('MGHZ3','rom_hold')['right_limit']['player_screen_x_at_first_lowered']}, POC 256 {S('MGHZ3','poc_w256_hold')['right_limit']['player_screen_x_at_first_lowered']}, POC 348 {S('MGHZ3','poc_w348_hold')['right_limit']['player_screen_x_at_first_lowered']}; SEZ3 ROM {S('SEZ3','rom_hold')['right_limit']['player_screen_x_at_first_lowered']}, POC 256 {S('SEZ3','poc_w256_hold')['right_limit']['player_screen_x_at_first_lowered']}, POC 348 {S('SEZ3','poc_w348_hold')['right_limit']['player_screen_x_at_first_lowered']}. In the ROM Sonic stays on the follow lead (116) until the lock.",
          "ROM follow zone lead +- 8 around 104/136 (CENTER-24/+8 at wide by decision D1-A)", "SCR_chaos_*_boss.gml mode 1-2 branches", "POC-SOURCE MODEL", "proven-gap", "Cosmetic: Sonic drifts 16 px (256) / 28 px (348) right of his usual screen position before the lock", "T3-A", "Sonic screen X at the lock within the follow zone", ["A-SEZ-3", "A-MGH-3", "A-AQZ-2"]),
        R("T3-10", "THZ3 (T2/T1 cross-reference; not re-derived)",
          f"T2-01/T2-02/T1-01: no screen clamp in modes 1-2 (Sonic max screen X {tz['player']['screen_x_max']} at 256 and {tw['player']['screen_x_max']} at 348; {tz['player']['updates_beyond_right_clamp_plus_4']} / {tw['player']['updates_beyond_right_clamp_plus_4']} updates beyond the clamp), centre follow, Y frozen at {tz['camera']['y_range'][1]} until the pan (ROM follows Y to {S('THZ3','rom_hold')['camera']['y_range'][1]}). The pan, the walk-on world positions and the state 18 -> 6 position (world 1902) are ROM-faithful at both widths.",
          "T2 section 1", "A-THZ-3, A-THZ-4, A-THZ-5, A-SH-2", "T2 + POC-SOURCE MODEL", "proven-gap", "see T2-01..T2-05", "T2/T1 camera-module package (D-T2-3)", "see T2 test plan", ["A-THZ-3"]),
        R("T3-11", "Camera release for all six bosses",
          "Not re-traced in T3. T1 traced THZ3, SEZ3 and MGHZ3 (defeat forced); GPZ3/AQZ3/EEZ3 remain contracts from their own audits. Code-level classification is in docs/t3-boss-walkon-framing-audit.md section 8.", "T1 section T1.3; T2 matrix", "SCR_chaos_boss.gml:255; gpz $9D26; sez/mghz/aqz $81BD handlers; eez release", "not re-traced", "not-audited", "unknown for GPZ3/AQZ3/EEZ3", "separate T3-R probe", "n/a", []),
        R("T3-12", "V1/T1 Package B (final SHA not supplied)",
          "All POC statements are about C1-I 69527335. The final V1/T1 SHA was not supplied; if V1/T1 touched the boss camera (PKG-T1A: THZ3 mode 1/4) the THZ3 rows may be stale. Re-baseline with: POC=<final checkout> node tools/t3_poc_boss_run.js --check, then python tools/t3_register.py --verify-anchors <final checkout>.",
          "n/a", "n/a", "limitation", "unresolved", "Possible stale THZ3 numbers", "Manager: supply SHA", "tools re-run is a no-op diff when nothing relevant changed", []),
    ]
    return OrderedDict(description="T3 discrepancy register. Fields follow the AGENTS.md Fidelity Register vocabulary (status: proven-match, adapter-difference, proven-gap, not-audited, unresolved).", poc_commit=POC_COMMIT, rows=rows)


# ------------------------------------------------------------------------------------------------------------------ tables
def _p(v):
    return "-" if v is None else str(v)


def tables():
    """Markdown tables for the report. Update numbers are scenario-relative; the 'rel' columns are updates after creation."""
    L = []
    L.append("### Table 1 - canonical ROM walk-on timeline (EMULATED, 256 px, RIGHT held)\n")
    L.append("| zone | created (boss screen X) | relocation | right limit lowered | pan start..end | first visible (anchor screen, columns) | fight opens | Sonic left of boss at first visible |")
    L.append("|---|---|---|---|---|---|---|---|")
    for z in ZONES:
        s = S(z, "rom_hold")
        c, rl = s["created"], s["right_limit"]
        rel = "; ".join(f"u+{x['u'] - c['u']} {tuple(x['from_'])}->{tuple(x['to'])} (screen {tuple(x['to_screen'])})" for x in s["relocations"]) or "none"
        fv, fa = s["first_visible"], s["fight_activation"]
        L.append(f"| {z} | u{c['u']} ({c['boss_screen_x']}) | {rel} | u+{rl['first_lowered_update'] - c['u']} ({rl['first_lowered_value']}) | u+{s['pan_start']['u'] - c['u']}..u+{s['pan_end']['u'] - c['u']} | u+{fv['u'] - c['u']} ({fv['anchor_screen'][0]},{fv['anchor_screen'][1]}; {fv['visible_columns']}) | u+{fa['u'] - c['u']} | {'yes' if fv['player_left_of_boss'] else 'no'} |")
    for scn, title in (("hold", "RIGHT held through the intro"), ("stop", "RIGHT released at the arena lock: Sonic waits")):
        cfgs = tuple(k.replace("_hold", "_" + scn) for k in CFG)
        L.append(f"\n### Table 2-{scn} - coordinates at the key events ({title}): camera X,Y / boss screen X,Y / Sonic screen X\n")
        L.append("| zone | event | ROM 256 | POC 256 | POC 348 |")
        L.append("|---|---|---|---|---|")
        for z in ZONES:
            for ev, key in (("creation", "created"), ("pan start", "pan_start"), ("pan end", "pan_end"), ("fight opens", "fight_activation")):
                cells = []
                for k in cfgs:
                    s = S(z, k)[key]
                    if s is None:
                        cells.append("-")
                    elif key == "created":
                        cells.append(f"u{s['u']} cam {tuple(s['camera'])} boss {s['boss_screen_x']} Sonic {s['player_screen_x']}")
                    else:
                        cells.append(f"u{s['u']} cam {tuple(s['camera'])} boss ({_p(s['boss_screen_x'])},{_p(s['boss_screen_y'])}) Sonic {s['player_screen_x']}")
                L.append(f"| {z} | {ev} | " + " | ".join(cells) + " |")
        L.append(f"\n### Table 3-{scn} - camera continuity from creation to the end of the pan ({title})\n")
        L.append("| zone | config | step at creation (dx,dy) | largest step in window (dx,dy) | X retreat (px) | Y range | Y up/down total | pan max step | Sonic screen X max / beyond clamp+4 |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for z in ZONES:
            for k, name in zip(cfgs, ("ROM 256", "POC 256", "POC 348")):
                s = S(z, k)
                c, pl = s["camera"], s["player"]
                L.append(f"| {z} | {name} | {_p(c['creation_update_step'])} | {tuple(c['max_abs_step'])} | {c['x_retreat']['pixels']} | {tuple(c['y_range'])} | {c['y_total_up']}/{c['y_total_down']} | {tuple(c['pan_max_abs_step'])} | {pl['screen_x_max']} / {pl['updates_beyond_right_clamp_plus_4']} |")
    L.append("\n### Table 4 - first visible frame: ROM, ROM scene in a 348 window, POC\n")
    L.append("| zone | ROM 256 (anchor screen; columns) | ROM camera, 348 window | POC 256 | POC 348 |")
    L.append("|---|---|---|---|---|")
    for z in ZONES:
        def f(v):
            return "-" if v is None else f"u{v['u']} ({v['anchor_screen'][0]},{v['anchor_screen'][1]}; {v['visible_columns']} of {{}} )"
        cells = []
        for v in (S(z, "rom_hold")["first_visible"], S(z, "rom_hold_same_camera_in_348")["first_visible"], S(z, "poc_w256_hold")["first_visible"], S(z, "poc_w348_hold")["first_visible"]):
            cells.append("-" if v is None else f"u{v['u']} ({v['anchor_screen'][0]},{v['anchor_screen'][1]}; {v['visible_columns']} col)")
        L.append(f"| {z} | " + " | ".join(cells) + " |")
    return "\n".join(L)


def build():
    return {"matrix": matrix(), "adapters": adapters(), "register": register()}


def dumps(d):
    return json.dumps(d, indent=1) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tables", action="store_true")
    ap.add_argument("--verify-anchors", metavar="POC")
    a = ap.parse_args()
    if a.verify_anchors:
        return verify_anchors(a.verify_anchors)
    if a.tables:
        print(tables())
        return 0
    built = build()
    rc = 0
    for k, p in OUT.items():
        t = dumps(built[k])
        if a.write:
            p.write_text(t)
            print("wrote", p.relative_to(ROOT), len(t))
        elif a.check:
            same = p.exists() and p.read_text() == t
            print("CHECK", p.name, "identical" if same else "DIFFERENT")
            rc |= 0 if same else 1
    return rc


if __name__ == "__main__":
    sys.exit(main())

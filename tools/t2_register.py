#!/usr/bin/env python3
"""T2: ownership contracts, six-zone boss-camera matrix and discrepancy register (Research only; no ROM needed).

Everything numeric is read from the committed trace files (data/t2/*.json, data/t1/*.json); the classification text is authored here.

    python tools/t2_register.py --write      # data/t2/ownership-contracts.json, boss-camera-matrix.json, discrepancy-register.json
    python tools/t2_register.py --check      # regenerate in memory, compare with the committed files
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "t2"
OUT = {"contracts": D / "ownership-contracts.json", "matrix": D / "boss-camera-matrix.json", "register": D / "discrepancy-register.json"}
CLASSES = ("canonical ROM behaviour", "intentional widescreen adapter", "confirmed mismatch", "unverified")


def load(name):
    return json.loads((D / name).read_text())


def contracts():
    return OrderedDict([
        ("rom", "Sonic Chaos (Europe) v1.2, SHA-256 eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"),
        ("vocabulary", "WORLD, EDGE(side,n), CENTER(n), PLAYER_DIST(n), LOCKED_CAMERA(c) as in docs/viewport-semantics-audit.md section 9; EDGE(RIGHT,0) = camera + view width"),
        ("owners", [
            OrderedDict(id="O0_ORDINARY_FOLLOW", rom="$4C90 -> $5832/$58E1, limits $4CB0/$4CF7", active="D15E bit7 set and D15F bit0 clear",
                        writes="D284/D286 (committed to D174/D176 at vblank $0570)", limits="D27C/D280 inclusive, D27E/D282 exclusive; a crossing step is dropped",
                        player_bounds="O-P1 (ROM clamp)", ends="any later owner", evidence="BYTE-VERIFIED (c1r) + EMULATED"),
            OrderedDict(id="O1_SIGN_WAIT", rom="goal sign $18 state-3 callback $A8C4 -> vector $0353 (bank $0C)", active="every update the awake sign object runs state 3 (sign anchor inside the lifetime window: screen X < 288 on 256 px)",
                        writes="D280 := max(D280, camera); follow stays on", limits="left raised every update; right untouched",
                        player_bounds="O-P1: Sonic cannot walk back off the screen; measured minimum screen X 13 in THZ1/MGHZ2/GPZ2/SEZ2", ends="contact (state 4) -> O2",
                        evidence="data/t2/sign-wait.json (4 acts, EMULATED) + BYTE-VERIFIED call site"),
            OrderedDict(id="O2_SIGN_PAN", rom="$AA43 vector $0359 / $5956", active="D15F bit0 set after sign contact until the act ends", writes="camera 1 px/update per axis to (signX-128, signY-153); right limit := target when moving right",
                        limits="exclusive right limit: X settles at target-1", player_bounds="O-P1 until player state $20 (about +280 updates)", ends="state $20 freeze ($83CB vector $0407) -> O3", evidence="viewport-semantics-audit section 2 (EMULATED), unchanged"),
            OrderedDict(id="O3_ACT_CLEAR_RUN", rom="player state $20 handler $83A6", active="player state $20", writes="at d > $F8 vector $0407: D15E bit7 cleared, D280 := camera (frozen)", limits="frozen camera",
                        player_bounds="NONE (state $20 does not call $4141/$4281): Sonic legitimately leaves the screen; flag at d > $120 = EDGE(RIGHT,+33)", ends="next-level load", evidence="BYTE-VERIFIED + EMULATED (T1)"),
            OrderedDict(id="O4_BOSS_PRETRIGGER", rom="shared boss state 1 $9771 (bank $1E) -> $8199 -> vector $0353", active="boss object exists, states 0/1", writes="D280 := max(D280, camera) every update; the old right limit is saved in boss +$25/+$27",
                        limits="left raised each update; follow still scrolls right", player_bounds="O-P1", ends="trigger -> O5", evidence="BYTE-VERIFIED + EMULATED (data/t2/boss-arrival.json, six zones)"),
            OrderedDict(id="O5_BOSS_LOCK", rom="$9799 vector $0356, state 2", active="trigger: strict |dx|<table, |dy|<table ($97A1 rows)", writes="D282 := camera (right limit at the camera: the right screen edge becomes the arena wall)",
                        limits="left = camera (raised), right = camera: the camera cannot move", player_bounds="O-P1: the clamp is the arena. No world rectangle exists in the ROM", ends="HUD slot wait -> O6", evidence="BYTE-VERIFIED + EMULATED"),
            OrderedDict(id="O6_BOSS_PAN", rom="state 2 -> 3 table $9808 + vector $0359 / $5956", active="D15F bit0", writes="camera to boss anchor + (dx,dy), 1 px/update/axis; D27E (bottom) written first; right limit := target while moving right",
                        limits="exclusive right limit: X settles at target-1", player_bounds="O-P1", ends="boss state 5 release -> O7", evidence="data/t2/owner-map.json boss_tables + data/t2/boss-arrival.json"),
            OrderedDict(id="O7_BOSS_RELEASE", rom="shared $81BD (THZ3, SEZ3, AQZ3; MGHZ3 branch $81F4); GPZ3 $9D2F; EEZ3 $B232/$B92D", active="defeat conversion", writes="D280 := camera (not MGHZ3), vector $035C (pan off, enable), D282 := saved right limit (+$25/+$27)",
                        limits="follow resumes, <= 7 px/update", player_bounds="O-P1 until player state $20", ends="O3", evidence="BYTE-VERIFIED + data/t1/transition-audit.json"),
            OrderedDict(id="O8_ZONE_SPECIAL", rom="GPZ3 world-fixed lock $9AA1; EEZ3 two encounters; EEZ tube D15F; AQZ/EEZ scroll", active="zone-specific", writes="see matrix", limits="see matrix", player_bounds="O-P1", ends="zone-specific", evidence="data/t2/boss-camera-matrix.json"),
        ]),
        ("player_bounds", OrderedDict(
            id="O-P1", rom="$4141 (called from the shared player step $3FEF, vector $0404) and $4281", gate="player state < $29 (CP $29 / JR NC); state $20 is excluded because its handler never calls it",
            rule="e = (playerX - D174) AND $FF; e < $10 -> X := cam+$10 (minus this update's X speed), X speed := 0; e >= $F8 -> X := cam+$F7 (same compensation)",
            scope="UNCONDITIONAL: not owned by the sign, a boss or any object. Proven with a bare limit lock (D280 = D282 = camera) and no object: data/t2/clamp-scope.json",
            observed_range_screen_x="[13..16, 247..249] (the compensation order leaves 1-2 px of slack)", reads="the COMMITTED camera D174, so it uses the previous update's camera exactly as a Z80-ordered POC step would",
            widescreen_form="EDGE(LEFT,+16) .. EDGE(RIGHT,-9) of the live view, full-width integers (the 8-bit low-byte form teleports a player at d >= 256: do not port it)")),
        ("legitimate_off_screen_phases", [
            "player state $20 (act-clear run-off): flag at EDGE(RIGHT,+33)",
            "player states >= $29 (the clamp is skipped by the ROM gate)",
            "death / pit falls (camera bottom limit)",
            "EEZ tube states $16/$17 and other scripted transports (own handlers)"]),
        ("update_order", "ROM $16B8: camera ($16CA) -> player ($16CD) -> objects ($16D0). The player clamp therefore reads the camera committed by the PREVIOUS update; POC order (adapter step, objects phase, then zone End Step camera) has the same relation."),
    ])


def matrix():
    b = load("boss-arrival.json")["zones"]
    tab = load("boss-arrival.json")["tables"]
    trig = {r["zone_or_encounter"]: r for r in tab["trigger_table_97A1"]["rows"]}
    pan = {r["zone_or_encounter"]: r for r in tab["pan_table_9808"]["rows"]}

    def tr(k):
        return f"strict |dx|<{trig[k]['dx']}, |dy|<{trig[k]['dy']}"

    def pn(k):
        return f"anchor + ({pan[k]['dx']}, {pan[k]['dy']})"
    z = OrderedDict()
    spec = [
        ("THZ3", "THZ", "$50", "shared states 0-5 ($9765..), bank $1E", tr("THZ"), "right limit := camera at the trigger (limit trails the camera by one scroll step)", pn("THZ"),
         "settles (1679,78) per T1; HUD slot ($12) must disappear first (97 updates)", "$81BD: floor bit 1 gate; D280 := camera; pan off; D282 := saved 2304; player state $20 follows; $0A bonus object",
         "follow resumes, <= 7 px/update (T1)", "none: generic O-P1 clamp = arena (the POC's 1695..1926 rectangle is that clamp expressed in world terms at 256)"),
        ("GPZ3", "GPZ", "$51", "own intro $9A64..; head object; segments", "creation: world-fixed lock (below); table row 1 is not used for the lock", "right limit := 1664 (WORLD) AT CREATION, 270 px ahead of the camera; the camera runs into the limit by itself",
         "LOCKED_CAMERA (1664,96) via $9AED vector $0359 (equals the row-1 offset from the head's 1856)", "settles (1663,96/97); camera-ready gate: |diff| < 4 per axis",
         "head-gone release: D280 := camera, D282 := $0780 (1920), D27E := 96; pan off + enable ($035C, $042B)", "follow", "none: generic O-P1 clamp"),
        ("SEZ3", "SEZ", "$54", "shared states 0-5", tr("SEZ"), "right limit := camera at the trigger", pn("SEZ"), "settles (2975,462); combat starts at once, no camera-arrival gate",
         "$81BD: D280 := camera; D282 := saved 3840", "follow resumes <= 7 px/update", "none: generic O-P1 clamp (sez3-boss-54-audit: no SEZ-specific world arena)"),
        ("MGHZ3", "MGHZ", "$56", "shared states 0-5, release branch $81F4", tr("MGHZ"), "right limit := camera at the trigger", pn("MGHZ"), "settles (3060,256) per T1/audit",
         "$81F4 branch: NO left-limit write; D282 := saved 3584; gated on WORLD X >= 3356 and floor bit 1", "follow resumes, then waits for Sonic X >= 3356 (T1)",
         "none: generic O-P1 clamp. The arena floor ends: holding RIGHT walks Sonic into the pit (data/t2/boss-arrival.json run ended in a fall)"),
        ("AQZ3", "AQZ", "$59", "shared states 0-5", tr("AQZ"), "right limit := camera at the trigger", pn("AQZ"), "settles (1727,78); combat init runs while the camera still moves; no arrival gate",
         "$81BD: D280 := camera; D282 := saved natural right limit 2304; player state $20", "follow", "none: generic O-P1 clamp; no boss-owned world rectangle"),
        ("EEZ3", "EEZ", "$5E then $60", "two consecutive encounters; boss anchor shifted +128 at setup", f"{tr('EEZ first ($5E)')} (second encounter row: {tr('EEZ second ($60)')})",
         "right limit := min(old right, camera); old right saved", "anchor + (-128,-160) nominal (1952,334)/(2336,334)", "settles (1951,333)/(2335,333); bottom limit 334",
         "handoffs release pan and restore the saved right limits; no player $20 / act clear; the chain continues to the ending", "not a normal follow release: scripted chain", "none: viewport-relative O-P1; the audit forbids a THZ-style fixed world arena"),
    ]
    for key, zk, typ, activation, trigger, lock, pan_rule, settle, release, after, bounds in spec:
        t = b[zk]
        row = OrderedDict(boss_type=typ, activation_code=activation, trigger=trigger, lock=lock, pan_target=pan_rule, pan_settle=settle, release=release, camera_after_release=after, player_boundary=bounds)
        cr = t["created"]
        row["emulated_arrival"] = OrderedDict(
            arrival_distance_left_of_anchor=t["arrival_distance_left_of_anchor"],
            created=OrderedDict(update=cr["update"], boss_world_x=cr["boss_world_x"], boss_screen_x=cr["boss_screen_x"], player_world_x=cr["player_world_x"], player_screen_x=cr["player_screen_x"], camera_x=cr["camera"][0]),
            first_anchor_on_screen=None if not t["first_anchor_on_screen"] else OrderedDict((k, t["first_anchor_on_screen"][k]) for k in ("update", "boss_world_x", "boss_screen_x", "player_world_x", "player_screen_x", "camera", "boss_right_of_player")),
            right_limit_first_changed=t.get("right_limit_first_changed"),
            arena_lock=None if "arena_lock_right_limit" not in t else OrderedDict((k, t["arena_lock_right_limit"][k]) for k in ("update", "camera", "boss_world_x", "boss_screen_x", "player_world_x", "player_screen_x")),
            pan=t.get("pan"), max_player_screen_x_any_update=t["max_player_screen_x_any_update"], max_player_screen_x_before_lock=t["max_player_screen_x_before_lock"])
        z[key] = row
    return OrderedDict([("sources", ["data/t2/boss-arrival.json", "data/t2/owner-map.json", "data/t1/transition-audit.json", "docs/*-boss-*-audit.md"]),
                        ("note", "pan/trigger rows are BYTE-VERIFIED tables ($97A1/$9808). Emulated numbers come from one arrival script per zone (RIGHT held, boss state never forced) and are SYNTHETIC at the start only."),
                        ("zones", z)])


def register():
    R = []

    def add(i, scope, finding, cls, impact, evidence, poc, rec):
        assert cls in CLASSES, cls
        R.append(OrderedDict(id=i, scope=scope, finding=finding, classification=cls, gameplay_impact=impact, evidence=evidence, poc_path=poc, recommendation=rec))
    add("T2-01", "THZ3 boss, camera modes 1-2 (creation to HUD wait)", "No player screen clamp is applied between boss creation and the pan (mode 3 has only a world-rectangle clamp). Sonic runs past the locked screen edge.",
        "confirmed mismatch", "Report 1: Sonic leaves the visible screen while the camera is locked", "POC-SOURCE MODEL data/t2/poc-model.json (256: 52 updates beyond the view, max screen X 443; 348: 94 updates, 441); ROM: max screen X 249 in all six zones (data/t2/boss-arrival.json)",
        "SCR_chaos_adapter.gml:199 clamp predicate lists goal contact, GPZ3, MGHZ3, SEZ3, AQZ3 only; EEZ3 is a separate block at :212; THZ3 appears nowhere except the mode-3 world rectangle at :203", "route every locked owner through one bounds predicate (section 5 of the report)")
    add("T2-02", "THZ3 boss entry", "The boss appears to Sonic's left: with T2-01 Sonic passes the spawn x (1936) at update 123 in both widths; at 348 the extended arena (to 2018) keeps him right of the boss for the whole fight.",
        "confirmed mismatch", "Report 2", "POC-SOURCE MODEL: first_update_player_right_of_boss_spawn_x 123 (256 and 348); 348: 208 updates right of the boss anchor. ROM: boss created at screen X 342 and enters through screen X 255 with Sonic clamped at <= 249",
        "chaos_boss_clamp / CHAOS_BOSS_ARENA_RIGHT + chaos_boss_arena_extra", "fix T2-01 first; after it, at 256 the case cannot occur. At 348 it can only occur within the last 2 px of the viewport clamp (RIGHT-9 = 1938 vs spawn 1936); decide D-T2-2 before touching the boss position")
    add("T2-03", "Goal sign wait (all 12 ordinary acts; reported at MGHZ2)", "C1-I added the ROM 'raise left limit' while the awake sign is in state 3, but the player clamp is still enabled only from sign contact (chaosGoalContact). Before contact the camera cannot scroll back and Sonic can walk off its left edge.",
        "confirmed mismatch", "Report 3: backtracking near the end of MGHZ2 leaves Sonic offscreen with the camera locked",
        "POC-SOURCE MODEL (THZ1 sign): player screen X reaches -494 (256) / -448 (348) with the left limit tracking the camera; ROM (4 acts): minimum screen X 13, camera stays",
        "OBJ_chaos_object_18/Step_0.gml:9 (raise) vs SCR_chaos_adapter.gml:199 (clamp gate)", "bounds predicate must include O1_SIGN_WAIT")
    add("T2-04", "Architecture", "The ROM clamp is a property of the player step (state < $29), not of any owner. The POC keeps a hand-maintained disjunction of owners; any new camera lock that forgets to join it is unprotected.",
        "confirmed mismatch", "Root cause class behind T2-01 and T2-03", "BYTE-VERIFIED $4141 + EMULATED bare limit lock (data/t2/clamp-scope.json: screen X 14..249 with no sign and no boss)", "SCR_chaos_adapter.gml:199, :203, :212", "single owner-independent predicate; see report section 5")
    add("T2-05", "THZ3 boss, camera mode 1 and mode 4", "Creation and release re-centre the camera on Sonic (T1-01/T1-02). Not re-measured here as a snap: in the T2 arrival script Sonic is left of centre so the left limit absorbs it (step 0).",
        "confirmed mismatch", "Camera pop at creation (Sonic ahead of centre) and at release (33 px example in T1)", "T1 register + POC-SOURCE MODEL (conditional on Sonic position)", "SCR_chaos_boss.gml chaos_boss_camera_step modes 1 and 4",
        "keep T1 PKG-T1A: left-limit raise only, bounded takeover/release")
    add("T2-06", "Boss entry geometry, THZ3 / GPZ3 / MGHZ3 / AQZ3 / EEZ3", "In the ROM the boss is created off-screen right (screen X 338-342, Sonic at 115-116) and its anchor first reaches the screen at X 254-255, with Sonic (clamped to <= 249) to its left. AQZ3 and EEZ3 bosses are already inside the window at X 254 before the arena locks; THZ3 and MGHZ3 first show at the pan.",
        "canonical ROM behaviour", "Defines 'approaches from the right'", "data/t2/boss-arrival.json (EMULATED + SYNTHETIC start)", "chaos_boss_creation_band uses EDGE(RIGHT,+32..+95): equivalent", "none")
    add("T2-14", "SEZ3 boss entry", "The SEZ3 boss is not slid in: at state 3 its anchor jumps from the placement (3200,622) to (3136,430), screen X 209. With Sonic hugging the right clamp (X 246-247) the boss therefore appears to Sonic's LEFT.",
        "canonical ROM behaviour", "A report of 'boss on the left' is original behaviour in SEZ3 when Sonic stands at the right edge; it is not a THZ3-style error", "data/t2/boss-arrival.json SEZ first_anchor_on_screen (update 169, boss_right_of_player false); trace rows 168-169", "-", "do not generalise T2-02 to SEZ3")
    add("T2-07", "THZ3 at widths > 256", "The locked/pan camera is a world camera (1679). At 348 the boss spawn (1936) is already inside the view at the lock (screen X 337), and at pan end it sits at screen 257, so it is visible before it 'enters'. The ROM puts it at 256 = the right edge.",
        "intentional widescreen adapter", "Boss cannot arrive from beyond the right edge at wide widths without a moved boss or a moved camera, neither ROM-backed", "POC-SOURCE MODEL (348: boss screen X 337 at lock); ROM table row 0 offset -256", "chaos_boss_camera_step mode 3 (CHAOS_BOSS_CAMERA_X 1679)",
        "do not move the boss or the camera target; decision D-T2-2")
    add("T2-08", "Clamp edges in the POC", "POC clamp is EDGE(LEFT,+16)..EDGE(RIGHT,-9) full-width with no speed compensation (ROM slack: screen X 13..16 and 247..249).", "intentional widescreen adapter", "<= 2 px", "data/t2/clamp-scope.json vs SCR_chaos_goal.gml chaos_goal_clamp_player", "SCR_chaos_goal.gml", "keep")
    add("T2-09", "SEZ3, MGHZ3, AQZ3, GPZ3 and EEZ3 player bounds", "The existing owner predicates (chaos_54/56/59_owns_camera, GPZ3 active, EEZ separate block) do apply the viewport clamp, matching the ROM relation.", "canonical ROM behaviour",
        "none expected", "SCR_chaos_adapter.gml:199, :212; ROM max screen X 249 in all six zones", "same", "keep behaviour; fold into the single predicate")
    add("T2-10", "Zone start: black period and fade", "ROM: about 34 harness frames of black while the loader scrolls the camera, then a 3-step palette fade (5-frame cadence). POC: OBJ_effect_fade_in, a 20-step linear alpha fade created in OBJ_chaos_zone Create (inherited template).",
        "unverified", "Possible source of the brief black flash; cause not isolated", "data/t2/zone-start.json (EMULATED, harness frames); POC read only", "OBJ_effect_fade_in, OBJ_chaos_zone/Create_0.gml:43", "Windows probe R-T2-3 before any palette work")
    add("T2-11", "Zone start: apparent fall", "ROM: GPZ1, MGHZ1, EEZ1 start airborne and drop 14-15 px to the floor at harness frames 30-40 (state 14 -> 5 -> 1); THZ1/SEZ1/AQZ1 start grounded with a 7 px anchor flicker during the first fade step. These are canonical and mostly hidden under the fade.",
        "canonical ROM behaviour", "A short drop at the start of three zones is original", "data/t2/zone-start.json", "-", "do not 'fix'; compare POC only after the R-T2-3 capture")
    add("T2-12", "Zone start: POC view/camera at first frames", "C1-I seeds the follow camera in Create (chaos_camera_ordinary_begin) and a wide start X; whether the first rendered frames use the final camera Y/X and whether the fade covers them was not executed.", "unverified",
        "Flash / drop candidates", "POC read only", "SCR_chaos_camera.gml chaos_camera_ordinary_begin", "R-T2-3 capture of view X/Y/alpha for 60 updates in THZ1, GPZ1, MGHZ1")
    add("T2-13", "State $20 run-off", "Sonic is exempt from the clamp and leaves the screen to EDGE(RIGHT,+33); POC exempts state 32 / next 32.", "canonical ROM behaviour", "none", "viewport-semantics-audit section 4 + T1", "SCR_chaos_adapter.gml:199 (cp_c.state != 32 && cp_c.next != 32)", "keep")
    return OrderedDict([("classes", list(CLASSES)), ("rows", R)])


def build():
    return {"contracts": contracts(), "matrix": matrix(), "register": register()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    for k, v in build().items():
        text = json.dumps(v, indent=1) + "\n"
        if a.write:
            OUT[k].write_text(text)
            print("wrote", OUT[k].relative_to(ROOT), len(text))
        elif a.check:
            same = OUT[k].exists() and OUT[k].read_text() == text
            print("CHECK", k, "identical" if same else "DIFFERENT")
            if not same:
                sys.exit(1)


if __name__ == "__main__":
    main()

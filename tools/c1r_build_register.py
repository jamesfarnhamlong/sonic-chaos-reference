#!/usr/bin/env python3
"""C1-R: builds data/c1r/gameplay-fidelity-register.json and data/c1r/implementation-contracts.json from the audited rows below.

    python tools/c1r_build_register.py --write     # regenerate both files
    python tools/c1r_build_register.py --check     # compare with the committed files

The rows are authored here (not generated from the ROM); every row cites the evidence it rests on.  tests/test_c1r_audit.py validates the schema,
the cross references and the numbers that are also asserted by the traces.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_REG = ROOT / "data" / "c1r" / "gameplay-fidelity-register.json"
OUT_CON = ROOT / "data" / "c1r" / "implementation-contracts.json"

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
POC_COMMIT = "ac021e1ef2665c8668de13959f5ccc4653f312d1"
RESEARCH_BASE = "b6467ba0ad79fad0937f750083a5261e7ea64e8f"

CLASSES = ("MATCH", "ADAPTER", "MISMATCH", "MISSING", "UNVERIFIED")
EVIDENCE = ("ROM_SOURCE", "EMULATED", "CONTROLLED", "PRIOR_RESEARCH", "POC_SOURCE", "WINDOWS_ACCEPTANCE")
TRACKS = ("C1-I", "C1-I-optional", "research-first", "separate-research", "resolved", "deferred", "decision")

TRACE = "data/c1r/camera-look-trace.json"
SIGN = "data/c1r/sign-registration.json"


def ev(cls, ref):
    assert cls in EVIDENCE, cls
    return {"class": cls, "ref": ref}


def row(id_, subsystem, rom_ref, evidence, confidence, rom, poc, classification, coverage, impact, risk, action, track, deps=(), poc_refs=(), basis=None, related=()):
    assert classification in CLASSES and track in TRACKS
    d = dict(id=id_, subsystem=subsystem, rom_ref=rom_ref, evidence=evidence, confidence=confidence, canonical_rom_behaviour=rom, current_poc_behaviour=poc,
             classification=classification, existing_coverage=coverage, user_visible_impact=impact, implementation_risk=risk, recommended_action=action, track=track,
             dependencies=list(deps), poc_refs=list(poc_refs), related=list(related))
    if basis:
        d["match_basis"] = basis
    return d


SRC_COMPARED = "SOURCE_COMPARED: ROM disassembly read against the POC GML; no differential run in C1-R"
PRIOR_DIFF = "PRIOR_DIFFERENTIAL: earlier accepted Research/POC differential evidence, not re-run in C1-R"

CORE = "scripts/SCR_chaos_core/SCR_chaos_core.gml"
STEP2 = "objects/OBJ_chaos_zone/Step_2.gml"


def rows():
    r = []
    # ------------------------------------------------------------------ A: controls and states
    r.append(row("A-01", "player/look-up", "states 1,2,5.. -> 3: `$36C6/$36F0/$3783` -> `$46B0`; state 3 callback `$3713`; exit `$3753`->`$45B3`",
                 [ev("ROM_SOURCE", "tools/c1r audit disassembly 36C6-3759 (docs/c1r section 2.1)"), ev("POC_SOURCE", CORE + ":802-815"), ev("EMULATED", TRACE + " look_up_hold_release")], "high",
                 "Up held while standing (state 0/1/2/19) and no Left/Right and zero X speed requests state 3 (`$46B0`, X speed zeroed, attack bit untouched). Up has priority over Down. State 3 returns to walk if Left/Right, to crouch (4) if Down, to stand (`$45B3`) when Up is released.",
                 "SCR_cc_tick states 1-4 block implements the same order: walk on Left/Right, Up -> 3 (vx = 0), Down -> 4 (roll/attack bits cleared), release -> SCR_cc_stand. VISUAL-P1 presents state 3 with ROM frame `$13`.",
                 "MATCH", "VISUAL-P1 presentation accepted on Windows; trace row look_up_hold_release shows ROM states 1->3->1", "none expected", "low",
                 "Keep; add the camera lead hook (B-01) in the same block.", "resolved", poc_refs=[CORE + ":802-815"], basis=SRC_COMPARED))
    r.append(row("A-02", "player/crouch", "`$46BB`, state 4 callback `$3759`",
                 [ev("ROM_SOURCE", "46BB-46CD, 3759-3782"), ev("POC_SOURCE", CORE + ":802-815"), ev("EMULATED", TRACE + " look_down_hold_release")], "high",
                 "Down held while standing requests state 4 (X speed zero, rolling/hurt bits cleared). In state 4 a fresh button press starts spin-dash charge (`$4701`); Up while crouching returns to look-up (`$46B0`); Down released -> stand. Left/Right are not read.",
                 "Same transitions (state 4 excluded from the walk test; Up -> 3; Down released -> stand; button press -> state 15 spin-dash charge at SCR_cc_tick:779).",
                 "MATCH", "VISUAL-P1 presentation (frame `$14`) accepted", "none expected", "low", "Keep; add the camera lead hook (B-02).", "resolved", poc_refs=[CORE + ":778-782", CORE + ":802-815"], basis=SRC_COMPARED))
    r.append(row("A-03", "player/look-up+button", "state 3 callback `$3713`: `LD A,(IX)` / DEC / `D147 & $30` -> `JP $46CE` (Sonic, type 1)",
                 [ev("ROM_SOURCE", "3713-3739"), ev("POC_SOURCE", CORE + ":554 (SCR_cc_shared)"), ev("EMULATED", TRACE + " peel_out_ordinary: state 3 -> request $15 on the update the button is pressed")], "high",
                 "In state 3 a NEW button press (`D147 & $30`) is intercepted BEFORE the shared movement `$3FEF`: Sonic starts Peel-Out (state `$15`), no jump. (Tails takes `$473C` instead; not audited.) The ordinary jump request `$45ED` is only reached from `$3FEF`.",
                 "SCR_cc_shared performs SCR_cc_jump for ANY state when a button is pressed (SCR_chaos_core.gml:554), so Up + jump from look-up is an ordinary jump. Peel-Out does not exist in the core.",
                 "MISMATCH", "none (never exercised: no POC test presses a button in state 3)", "High: Up+jump is a natural input and gives a different move than the original", "low",
                 "Intercept state 3 + pressed button before SCR_cc_shared (C1-I item I3).", "C1-I", deps=["A-04"], poc_refs=[CORE + ":554"]))
    r.append(row("A-04", "player/peel-out charge", "`$46CE` setter, state `$15` callback `$396D`, script `$8256`",
                 [ev("ROM_SOURCE", "46CE-46E1, 396D-39B5"), ev("EMULATED", TRACE + " peel_out_ordinary / peel_out_hold_right"), ev("PRIOR_RESEARCH", "docs/player-attack-badnik-audit.md section 2.1; docs/visual0-sonic-state-frame-catalogue.md state 15")], "high",
                 "`$46CE`: X speed := 0, hurt bit cleared, request `$15`, sound request `$AC`. Callback `$396D` every update: `+$04` bit 7 cleared, camera Y lead target := `$60`, terrain pass `$690B`, wall push-out (`D523` bit 3: X += 4, bit 2: X -= 4), `$48BC`, screen clamp `$4281`, a fresh button press re-requests sound `$AC`, and **the dash is released when Up (D137 bit 0) is no longer held** - the button need not stay held, there is no charge timer. Attack bit `$D503` bit 1 is neither set nor cleared.",
                 "No core state 21/26: SCR_cc_tick has no branch; grep finds no peel-out entry outside VISUAL-P1 presentation (`chaos_visual_p1_state` owns 21/26 but the core never enters them).",
                 "MISSING", "VISUAL-P1 ships the 07-0A frames and the animation program for state 21; no behaviour test", "Medium: original move absent", "medium",
                 "Implement states 21/26 in the core (C1-I item I3).", "C1-I", deps=["A-03", "B-01"], poc_refs=[CORE + ":761-815", "scripts/SCR_chaos_visual_p1/SCR_chaos_visual_p1.gml:4-17"]))
    r.append(row("A-05", "player/peel-out run", "`$46E2` release, state `$1A` callback `$39B6`, entry call `$8313`",
                 [ev("ROM_SOURCE", "46E2-4700, 39B6-39E5, 37F4-3830"), ev("EMULATED", TRACE + " peel_out_ordinary (speed 1792 -> friction), peel_out_hold_right (speed held 1792), D503 bit 7 for 12 updates")], "high",
                 "`$46E2`: max X speed `D373` := `$0700`, X speed := +/-`$0700` by facing (`+$04` bit 4 set -> `$F900`), request `$1A`, sound `$BE`. Entry call `$8313` sets invulnerability (`D503` bit 7) with timer `D3B1` = `$0C` (observed: 12 updates, then cleared). Callback `$39B6`: lead := `$60`, shared movement `$3FEF`, `$4281`; a side contact (`D523 & $0C`) clears bits 1 and 7 and requests walk (`$45CE`); floor block `$19` -> run (`$47A9`); otherwise the walk/run exit logic `$37F4`. With no direction held the ordinary friction slows Sonic (observed 1792 -> 0 over about 60 updates); with Right held the speed stays 1792.",
                 "Absent (see A-04).", "MISSING", "trace fixtures only", "Medium", "medium", "Implement with A-04 (C1-I item I3). Sound requests are `$AC`/`$BE` request ids only (audio is not an authorised runtime task).", "C1-I", deps=["A-04"]))
    r.append(row("A-06", "player/peel-out long hold", "state `$15` script `$8256`: `FF 0E D2` loop then `FF 01 $82CC`",
                 [ev("ROM_SOURCE", "script bytes 0x30256.. and routine bytes at 0x82CC"), ev("EMULATED", TRACE + " peel_out_long_hold: aura object type 5 appears 1,764 updates after state 15 starts; D503 becomes 0x82; sound id $BF")], "medium",
                 "After the script's 60 + 24 updates of ramp plus 210 loops of 8 updates (60 + 24 + 1,680 = 1,764 updates; observed object appearance exactly 1,764 harness frames after entry) a callback requests sound `$BF` and creates object type 5 (the star aura); `D503` shows bits 7 and 1 (invulnerable, attack posture) for the rest of the charge and the early run. Resolves the UNRESOLVED 'aura after a very long charge' of docs/player-attack-badnik-audit.md section 13.",
                 "Absent.", "MISSING", "trace only", "Negligible (needs a 30 s charge)", "low", "Defer; optional with I3 if trivial. Documented so nobody mistakes it for a bug.", "deferred", deps=["A-04"]))
    r.append(row("A-07", "player/spin dash", "`$4701` / `$4719`, callbacks `$39E6` (charge) `$3A23` (roll)",
                 [ev("ROM_SOURCE", "4701-473B, 39E6-3A36"), ev("POC_SOURCE", CORE + ":778-795"), ev("PRIOR_RESEARCH", "docs/player-attack-badnik-audit.md")], "medium",
                 "Charge: X speed 0, attack bit set, state `$0F`; release (Down no longer held) sets speed +/-`$0700`, max `$0700`, state `$10`. Callbacks set the camera lead `$60`.",
                 "Implemented with the same constants (maximum 1792, vx +/-1792).", "MATCH", "accepted since early packages", "none", "low", "Keep.", "resolved", basis=PRIOR_DIFF))
    r.append(row("A-08", "player/idle wait", "state 1 script `$8081`: record `0B x180` then `FF 03 02` + `FF 00`",
                 [ev("ROM_SOURCE", "script bytes 0x30081"), ev("EMULATED", TRACE + " idle_wait: exactly 180 camera updates in state 1, then state 2"), ev("PRIOR_RESEARCH", "docs/player-animation-counter.md section 5; docs/visual-p1-presentation.md section 6")], "high",
                 "Standing sprite (frame `$0B`) for 180 updates; the script then requests state `$02` (look-around cycle). State 2 returns to 1 only through input (jump, walk, look, crouch).",
                 "The core never requests state 2; VISUAL-P1 deliberately holds frame `$0B` (documented limitation).", "MISSING", "trace idle_wait; no POC test", "Medium: a 3 s idle shows the original look-around", "low",
                 "Add the 180-update counter and state-2 presentation program (C1-I item I4).", "C1-I", deps=["A-09"], poc_refs=["scripts/SCR_chaos_visual_p1/SCR_chaos_visual_p1.gml:23-24"]))
    r.append(row("A-09", "player/idle frames", "frames `$0C-$10` (state 2), `$11,$12` (state 2 tail)",
                 [ev("PRIOR_RESEARCH", "docs/visual0-sonic-state-frame-catalogue.md (on claude/eager-hopper-xo4388 41318f5)"), ev("POC_SOURCE", "sprites/ listing at ac021e1")], "high",
                 "State 2 script: `0C x64`, loop 20 x (`0D x16`, `0E x16`), `0F x64`, `10 x16`, `11 x16`, `12 x16`, jump to `$80B3`.",
                 "No SPR_chaos_player_frame_0C..12; `$11/$12` exist only as SPR_chaos_continue_sonic_11/12 (different palette).", "MISSING", "none", "required by A-08", "low", "Import 7 frames from the ROM tile tables with the catalogue canvas/origin data.", "C1-I", deps=[]))
    r.append(row("A-10", "player/idle callback", "`$36F0`",
                 [ev("ROM_SOURCE", "36F0-3712")], "high",
                 "State 2: shared movement `$3FEF`; a fresh button -> jump `$45ED`; Left/Right -> walk `$45CE`; Up -> look-up; Down -> crouch. It does not write the camera lead.",
                 "Generic code handles all four exits; the jump branch at SCR_chaos_core.gml:803 exists but is unreachable because state 2 is never requested.", "MATCH", "n/a", "none", "low", "Becomes live with A-08.", "resolved", basis=SRC_COMPARED, related=["A-08"]))
    r.append(row("A-11", "player/ledge-edge pose", "stand tail `$4A33` (called from `$45B3`), state `$19` callback `$3BC6`, script `$808A` (frames `$19-$1B`)",
                 [ev("ROM_SOURCE", "4A33-4A73, 3BC6-3BEF"), ev("PRIOR_RESEARCH", "docs/visual0-sonic-state-frame-catalogue.md: state 19 'not seen in THZ1 play'"), ev("EMULATED", "12 seeded random THZ1 runs never entered state 19 (negative evidence only)")], "medium",
                 "Every stand request `$45B3` ends in `$4A33`: it probes the terrain 18 px below the foot at X-4 and X+4 (`$7666`, result byte `D368`); if the two results differ by 16 or more it requests state `$19` and sets/clears `+$04` bit 4 toward the lower/higher side; equal results request stand. State 19 (callback `$3BC6`) returns to walk on any speed or Left/Right, otherwise look-up/crouch/stay. NEWLY FOUND: not listed in AGENTS or any earlier register.",
                 "No state 25 in the core or presentation; frames `$19-$1B` have no POC sprite.", "MISSING", "none", "Medium: the edge-balance pose when braking at a ledge", "medium",
                 "Research first (R-C1-1): establish the meaning of `D368`, the exact side rule and a natural THZ reproduction before implementation.", "research-first"))
    r.append(row("A-12", "player/walk-run-brake-roll", "states 5-9, `$37F4`, `$386F`, `$389A`, `$38C5`",
                 [ev("PRIOR_RESEARCH", "docs/movement.md, reports/differential-verification.json, docs/audit-2026-09-21.md"), ev("POC_SOURCE", CORE + ":816-835")], "medium",
                 "Walk/run/skid/roll transition tables as recovered (equality test for run, brake on opposite direction, roll on Down above a speed threshold, strip fall).",
                 "SCR_cc_tick mirrors the recovered branches (comments cite the ROM tests).", "MATCH", "earlier CPU differential (physics) and accepted Windows sessions", "none expected", "low", "No action.", "resolved", basis=PRIOR_DIFF))
    r.append(row("A-13", "player/push frame", "walk selector `$8EE1` side flag -> frame `$5E`",
                 [ev("PRIOR_RESEARCH", "docs/player-animation-counter.md section 4"), ev("POC_SOURCE", "SPR_chaos_player_frame_5E present")], "medium",
                 "There is no dedicated pushing STATE: walk uses a fixed 2-update record and frame `$5E` while a side contact is set.", "VISUAL-P1 reproduces the walk selector and has the `$5E` sprite.", "MATCH", "VISUAL-P1 Windows 8/8", "none", "low", "No action.", "resolved", basis="WINDOWS_ACCEPTANCE (VISUAL-P1) + source"))
    r.append(row("A-14", "player/control suppression - hurt", "`$4942`, `$494F`, `$48F7`",
                 [ev("PRIOR_RESEARCH", "docs/player-hurt-ring-scatter-audit.md, docs/platform-spike-collision-audit.md section 4")], "medium",
                 "Hurt movement locks control until landing; invulnerable window `$78`; contact flags per `$48BC`.", "SCR_cc_hurt_enter/tick implement the recovered entry; `hurt_rom` keeps the lock until landing.", "MATCH", "accepted hurt/ring packages", "none", "low", "No action.", "resolved", basis=PRIOR_DIFF))
    r.append(row("A-15", "player/control suppression - act clear and sign", "`$83A6`, `$A88E`",
                 [ev("PRIOR_RESEARCH", "docs/object-18-act-clear.md"), ev("POC_SOURCE", CORE + ":745-760")], "high",
                 "State `$20` ignores input; the sign pan, edge clamp and freeze follow docs/object-18-act-clear.md.", "SCR_cc_state32_tick and SCR_chaos_goal implement them; widescreen clear threshold is an explicit adapter.", "ADAPTER", "G0-R/G1 packages Windows accepted", "none", "low", "No action.", "resolved", basis=PRIOR_DIFF))
    r.append(row("A-16", "player/special fall and strip", "state `$14`, `$4663`",
                 [ev("PRIOR_RESEARCH", "docs/player-fall-control-audit.md A1-A10 (A10 death line UNRESOLVED)")], "medium",
                 "Left/Right read but no acceleration or friction in `$14`; landing requests walk; death line is screen-relative (`+$D0`).", "Not re-inspected in C1-R; MGHZ packages implemented `$14`.", "UNVERIFIED", "MGHZ M1 Windows follow-up", "unknown", "low", "Re-check only together with the camera bottom-limit decision (B-09 / D-10).", "separate-research", deps=["B-09"]))
    r.append(row("A-17", "player/monitor top contact and wall push", "`$5FA0`, `D523` guard",
                 [ev("PRIOR_RESEARCH", "docs/player-fall-control-audit.md B1-B8 (POC DIVERGENCE at 82ebc89)")], "low",
                 "A monitor is a solid floor from above; one-update wall push then `D523` guard stops pushes.", "Status at ac021e1 not re-inspected (a monitor-contact package exists in the workspace).", "UNVERIFIED", "unknown", "possible 'sticking' near monitors", "medium", "Fold into the C2 terrain/interactable audit.", "separate-research"))
    r.append(row("A-18", "player/attack posture predicate", "`D503` bit 1, `D532 == 6`",
                 [ev("PRIOR_RESEARCH", "docs/player-attack-badnik-audit.md"), ev("POC_SOURCE", "docs/attack-posture.md in POC")], "medium",
                 "Attack = `D503` bit 1 or invincibility; not airborne.", "Migrated to chaosAttackPosture in an earlier package.", "MATCH", "accepted package", "none", "low", "No action. Peel-out (A-04/A-05) must leave bit 1 untouched.", "resolved", basis=PRIOR_DIFF))
    # ------------------------------------------------------------------ B: camera
    r.append(row("B-01", "camera/look-up", "`$3713` writes `D289` := `$B8`; lead slew `$58E1`; follow `$5894`",
                 [ev("ROM_SOURCE", "3713-3721, 58E1-5934, 5894-58E0"), ev("EMULATED", TRACE + " look_up_hold_release (model replay 0 mismatches over 3,557 updates)")], "high",
                 "While state 3 runs (and the platform-owner byte `D3C0` is 0) the Y lead TARGET is `$B8` (184). The working lead `D28D` moves toward it 1 px per update. The vertical follow keeps Sonic's screen Y (`playerY - camY`) inside [lead-16, lead+16): the camera starts to move only when the zone edge passes Sonic, then follows at <=7 px/update (in practice 1 px/update, the lead slew). From a standing rest at screen Y 112: first camera move after 33 lead steps (update 35 in the trace, which includes the 2-update state-entry lag), final screen Y 168, camera 56 px up after 150 updates (88 px from rest 80). There is NO explicit timer or hard limit besides the lead and the stage limits.",
                 "No look-up camera. Vertical camera is rigid: view Y := clamp(round(player.y - viewH/1.5)).", "MISSING", "model + trace fixture", "High: signature original feature", "medium",
                 "Implement the Y-lead machinery (C1-I item I1/I2).", "C1-I", deps=["B-06", "A-01"], poc_refs=[STEP2 + ":13-20"]))
    r.append(row("B-02", "camera/look-down", "`$3759` writes `D289` := `$30`",
                 [ev("ROM_SOURCE", "3759-3763"), ev("EMULATED", TRACE + " look_down_hold_release")], "high",
                 "In state 4 (crouch) with `D3C0` = 0 the Y lead target is `$30` (48). Camera moves immediately if Sonic is already at the lower zone edge (screen Y 112): 48 px down after 150 updates, final screen Y 64.",
                 "No crouch camera.", "MISSING", "model + trace", "High", "medium", "As B-01.", "C1-I", deps=["B-06", "A-02"]))
    r.append(row("B-03", "camera/platform exception", "`LD A,(D3C0) / OR A / JR NZ` at `$3713` and `$3759`",
                 [ev("ROM_SOURCE", "3713-371E, 3759-3764"), ev("PRIOR_RESEARCH", "docs/mghz-m1-windows-followup.md: D3C0 = support owner slot (non-zero while riding a `$28` platform)")], "high",
                 "Riding a type `$28` platform (or any support owner) disables the look-up and look-down lead changes; the lead target is left at its previous value.",
                 "n/a.", "MISSING", "bytes only (not traced: needs a platform scene)", "Low", "low", "Implement with B-01/B-02: skip the writes when the core's support owner is set. Trace in MGHZ/SEZ before acceptance.", "C1-I", deps=["B-01"]))
    r.append(row("B-04", "camera/release and lag", "stand callback `$36C6` writes `D289` := `$60` every update",
                 [ev("ROM_SOURCE", "36C6-36C8"), ev("EMULATED", TRACE + " (release: camera begins to return 35 updates after the button is released, ends 90 updates later; look-down release rests at screen Y 80, not 112)")], "high",
                 "On release the target jumps to `$60` at once but the lead slews 1 px/update; the camera follows only after the zone edge passes Sonic, so the return is delayed (about 32-35 updates after look-up) and ends at the zone edge: after look-up Sonic rests at screen Y 112, after look-down at 80 (hysteresis).",
                 "n/a", "MISSING", "model + trace", "Medium: determines the feel", "low", "Falls out of the model; do not add a separate reset timer.", "C1-I", deps=["B-01"]))
    r.append(row("B-05", "camera/reset on state change", "`D289` writers (13 sites)",
                 [ev("ROM_SOURCE", "byte scan of `32 89 D2`: 36C8 (states 0/1), 371B(`$B8`), 3761(`$30`), 3785(walk), 3973(`$15`), 39B8(`$1A`), 39EC(`$0F`), 3A25(`$10`), 3BC8(`$19`), 3EFF(loop helper), 45E9(`$45CE` walk request), 462F(jump `$45ED`), 507B(init `$78`)")], "high",
                 "The lead target is a persistent register: rewritten to `$60` by states 0,1,5,`$0F`,`$10`,`$15`,`$19`,`$1A`, by every walk request (landing, hurt recovery) and by the jump launch; NOT written by 2, 6-9, `$0A`, `$0B`, `$0E`, `$1B`, `$1C`, hurt, death. So rolling, running and airborne states keep the previous target, look-up/down end when any writing state runs, and hurt does not reset it until the next landing.",
                 "n/a", "MISSING", "bytes + trace (walk, jump from stand)", "Medium", "low", "Implement as a per-state table (contract I2).", "C1-I", deps=["B-01"]))
    r.append(row("B-06", "camera/vertical follow", "`$5894-$58E0`, `$58E1`, `$4CF7`",
                 [ev("ROM_SOURCE", "5894-58E0, 4CF7-4D3D"), ev("EMULATED", TRACE + " 3,557 consecutive camera updates reproduced exactly by tools/c1r_camera_model.py"), ev("POC_SOURCE", STEP2 + ":13-20, scripts/SCR_player_view/SCR_player_view.gml")], "high",
                 "Lead target `D289` (rest `$60` = 96), working lead `D28D` slews 1 px/update, zone [lead-16, lead+16) on the low byte of playerY-camY, step = distance outside the zone capped at 7 (-8 survives), top limit inclusive, bottom exclusive, a crossing step is DROPPED. Rest screen Y: 112 after a fall, 80 after a rise (anywhere in 80..112).",
                 "Rigid lock: view Y := clamp(round(player.y - viewH/1.5), 0, room_h - viewH) every End Step (anchor about 130.7 px below the view top at 196 px height); no dead zone, no 7 px cap (except MGHZ/AQZ/EEZ where VSpeed is zeroed and, for MGHZ only, a +/-7 cap).",
                 "MISMATCH", "G1-B marked 'inherited camera follow'; verification/verify_viewport_adapter.js covers lifecycle, not follow", "High: Sonic sits 36-68 px lower on screen than in the original; fast falls/rises behave differently", "high",
                 "Replace with the model (C1-I item I1).", "C1-I", deps=["D2"], poc_refs=[STEP2 + ":13-20"]))
    r.append(row("B-07", "camera/horizontal follow", "`$5832`, `$58E1`, `$4CB0`",
                 [ev("ROM_SOURCE", "5832-5893, 58E1-5916"), ev("EMULATED", TRACE + " (X leads 104 right-facing, 136 left-facing, slew 1 px/update, replayed by the model)"), ev("PRIOR_RESEARCH", "docs/viewport-semantics-audit.md section 3")], "high",
                 "X lead target `$68` (104) when `+$04` bit 4 is clear, `$88` (136) when set, `$78` in pan mode (follow itself is skipped in pan mode); working lead slews 1 px/update; zone lead +/-8; step cap 7; low-byte compare.",
                 "GameMaker native object follow: HBorder = round(viewW/2.3) (151 at 348), VSpeed/HSpeed -1 (instant), no facing lead (SCR_player_view.gml). Widescreen behaviour of the lead is therefore not a ROM-derived adapter - it is GameMaker's.",
                 "MISMATCH", "G1-B inherited; sign pan (B-11) separate", "High: camera framing ahead of Sonic differs when turning", "high",
                 "Replace with the model plus an explicit widescreen lead mapping (decision D1) (C1-I item I1).", "C1-I", deps=["D1"], poc_refs=["scripts/SCR_player_view/SCR_player_view.gml"]))
    r.append(row("B-08", "camera/vertical window bias", "`$4D3E`: `R9 = (camY + 17) mod 224`; `R8 = -(camX+1)`",
                 [ev("ROM_SOURCE", "4D3E-4D5C"), ev("PRIOR_RESEARCH", "docs/mapped-object-screen-registration.md section 1; docs/rq4-campaign-start-registration.md section 3"), ev("POC_SOURCE", "objects/OBJ_chaos_zone/Create_0.gml:96-101")], "high",
                 "The visible terrain window starts at world row camY+17 (columns from camX+1); sprites are placed at anchor-camera+1. Sonic's feet are therefore at screen line anchor-camY (112 at rest), world row anchor+17.",
                 "The GM view top equals the canonical camera record (no +17). Objects carry their own +18 draw offsets so terrain/object relations are right, but the whole picture is 17 px lower relative to the screen than the original (foot at line 129 + follow differences).",
                 "ADAPTER", "RQ4 handed this to G1-B as an open adapter decision", "Medium: vertical framing 17 px lower", "high",
                 "Decision D2: keep canonical camera = view top (recommended; 79 view-Y consumers in 64 files, 55 chaos_vp_current calls) and record the offset as a documented adapter.", "decision", deps=["D2"]))
    r.append(row("B-09", "camera/limits and boundary handling", "`$4CB0`, `$4CF7`; limits `D27C/D27E/D280/D282`",
                 [ev("ROM_SOURCE", "4CB0-4D3D"), ev("PRIOR_RESEARCH", "docs/viewport-semantics-audit.md section 2.2/3 (114 CONTROLLED cases)")], "high",
                 "Left/top inclusive, right/bottom exclusive; a step that would cross is dropped (the camera can stop up to 6 px short of the limit when the step is large). THZ top 8, bottom worldH-240.",
                 "GameMaker room clamp (view cannot leave the room) plus per-zone adapters (EEZ/AQZ/boss owners); the death line differs (docs/player-fall-control-audit.md A10: POC 1043 vs canonical 992 for MGHZ1).",
                 "ADAPTER", "viewport adapter verifiers", "Low-medium (edge of map, pits)", "medium", "Implement the dropped-step rule inside the model; settle A10 with the same package or leave deferred.", "C1-I", deps=["B-06"], related=["D-10", "A-16"]))
    r.append(row("B-10", "camera/level start", "loader `$4E57`, init `$4DAD`, lead init `$5074-$507B`",
                 [ev("PRIOR_RESEARCH", "docs/rq4-campaign-start-registration.md"), ev("EMULATED", TRACE + " idle_wait row 0: THZ1 cam (38,530), Y lead starts 120 and slews to 96 over 24 updates (camera Y +12)"), ev("POC_SOURCE", "objects/OBJ_chaos_zone/Create_0.gml:96-101")], "high",
                 "Camera at entry = the record; Y lead starts at `$78` and slews to the standing target `$60`, so THZ1 settles from screen Y 124 to 112.",
                 "G1-B seeds the camera record; the follow afterwards is the GM rule (B-06).", "MATCH", "G1-B Windows accepted (record only)", "none", "low", "Model initial lead `$78` (D2 independent).", "resolved", basis="WINDOWS_ACCEPTANCE (G1-B, record only) + ROM"))
    r.append(row("B-11", "camera/sign pan", "`$0359`, `$5956`, `$83A6`",
                 [ev("PRIOR_RESEARCH", "docs/viewport-semantics-audit.md 2.2; docs/object-18-act-clear.md"), ev("POC_SOURCE", "scripts/SCR_chaos_goal/SCR_chaos_goal.gml:176-255")], "high",
                 "Pan mode: follow disabled on both axes, 1 px/update per axis to (signX-$80, signY-$99), right limit exclusive (camera stops at 3831 in THZ1).", "chaos_goal_pan_step reproduces the ROM rules; widescreen target is CENTER(0) with a world-right clamp (explicit adapter).", "ADAPTER", "G0-R/G1 accepted", "none", "low", "Keep. The follow model must hand over exactly at pan start (pan_mode skips the lead slew).", "resolved", basis=PRIOR_DIFF))
    r.append(row("B-12", "camera/scripted and boss", "boss framework vectors `$0353/$0356/$035C/$042B`",
                 [ev("PRIOR_RESEARCH", "docs/object-50.md, docs/mghz3-boss-56-audit.md, docs/sez3-boss-54-audit.md, docs/aqz3-boss-59-audit.md")], "medium",
                 "Boss arenas lock/raise the limits and pan the camera.", "Per-boss camera owners (`*_owns_camera`) gate the End Step follow in Step_2.gml:13.", "ADAPTER", "per-boss accepted packages", "none", "medium",
                 "Keep every owner guard; the new follow must be inert whenever an owner is active (acceptance test).", "resolved", deps=["B-06"], basis=PRIOR_DIFF))
    r.append(row("B-13", "camera/special stages", "`$5894..$58E0` 'same scheme' for SS4/SS5",
                 [ev("POC_SOURCE", "scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml:97 (measured constants)")], "low",
                 "Special-stage follow uses the same routine with its own limits.", "Own measured follow; not touched by Step_2 (chaos_is_ss exits first).", "UNVERIFIED", "SS packages", "unknown", "low", "Out of scope for C1-I; do not change SS cameras.", "deferred"))
    r.append(row("B-14", "camera/viewport distinction", "256x192 window",
                 [ev("PRIOR_RESEARCH", "docs/viewport-semantics-audit.md; POC SCR_chaos_viewport"), ev("POC_SOURCE", "348x196 view")], "high",
                 "All follow constants are authored for a 256x192 window. Nothing in the ROM defines a wide-screen offset.",
                 "348x196 adapter: lifecycle bands, right edge and clamps follow the real view width; the player lead is GM's.", "ADAPTER", "viewport verifiers", "n/a", "n/a",
                 "Any widescreen mapping of the leads (D1) is a documented adapter, never ROM behaviour.", "decision", deps=["D1"]))
    r.append(row("B-15", "camera/documentation correction", "viewport-semantics-audit.md section 3 'Follow (Y) ... lead `$78`, dead zone `$68..$98`'",
                 [ev("EMULATED", TRACE + " lead_y rests at 96"), ev("ROM_SOURCE", "D289 writer scan")], "high",
                 "`$78` is only the INITIAL working lead; ordinary play settles at `$60` (zone `$50..$70`), `$B8` while looking up, `$30` while crouching. The earlier statement omitted the `D289` writers.",
                 "n/a", "MISMATCH", "this audit", "Documentation only", "low", "Corrected here; the old document is left untouched (historical).", "resolved", related=["B-06"]))
    # ------------------------------------------------------------------ C: sign
    r.append(row("C-01", "sign/placement and anchor", "type `$18` records, state 3 `$A88E`",
                 [ev("PRIOR_RESEARCH", "docs/object-18-act-clear.md sections 2-4"), ev("POC_SOURCE", "objects/OBJ_chaos_object_18/Create_0.gml")], "high",
                 "World anchor = placement record; contact box dx +/-20, dy -42..+playerExtY.", "Canonical anchor and contact preserved; render adapter is draw-only.", "MATCH", "G0-R/U3/G2 accepted", "none", "low", "No action.", "resolved", basis=PRIOR_DIFF))
    r.append(row("C-02", "sign/resource crop", "mapping `$8EBA` frame 1: 10 pieces, canvas x -16..15, y -48..-1 (48 opaque rows)",
                 [ev("CONTROLLED", SIGN + " (tools/c1r_sign_registration.py): POC alpha mask == ROM composite minus its top 4 rows, shifted up 4, xor = 0 for all 5 frames"),
                  ev("POC_SOURCE", "POC_notes/import_sign_prizes.py:51-55 (`out.crop((0,4,32,52))`), POC_notes/import_type18_assets.py:31-32 ('margin4 then bottom-align')"),
                  ev("PRIOR_RESEARCH", "docs/u3-sign-prize-presentation.md section 'Compositing' - 'parked GOAL-FOLLOWUP-1'")], "high",
                 "The sign is 32x48 pixels; the face occupies the top 32 rows (pieces 0-7), the post the lower 16.",
                 "All 12 sign sprites (6 base sprites of 5 frames + 6 per-zone prize sets of 48 frames) have opaque rows 0..43 only: the inherited resource conversion (margin 4, bottom-align, crop 4) removed the TOP 4 ROM rows (48 px in frames 1/5) and moved the art 4 px up inside the 32x48 canvas.",
                 "MISMATCH", "proven by SIGN fixture; Windows report 'cropping'", "Medium: sign face top is flattened", "low",
                 "Re-export the 12 resources without the crop (C1-I item I6).", "C1-I", deps=["C-03"], poc_refs=["sprites/SPR_chaos_object_18", "POC_notes/import_sign_prizes.py:51-55"]))
    r.append(row("C-03", "sign/draw offset", "terrain row = anchor + mapping_y + 18 (`docs/mapped-object-screen-registration.md`)",
                 [ev("PRIOR_RESEARCH", "docs/mapped-object-screen-registration.md"), ev("POC_SOURCE", "scripts/SCR_chaos_render_adapter/SCR_chaos_render_adapter.gml:11"), ev("CONTROLLED", SIGN)], "high",
                 "For a bottom-origin 32x48 canvas whose last row is the post's last row the derived draw offset is +18.",
                 "TYPE18_RENDER_Y_ADAPTER = 22 = 18 + 4: it exactly compensates the 4-row canvas shift of C-02, so the VISIBLE pixels already land at the ROM-derived position (visible top at anchor-26 in both).",
                 "ADAPTER", "SIGN fixture", "none beyond C-02", "low", "Change to 18 together with C-02 (never alone: it would sink the crop).", "C1-I", deps=["C-02"]))
    r.append(row("C-04", "sign/x registration", "terrain col = anchor + mapping_x + 1 (`R8 = -(camX+1)`)",
                 [ev("PRIOR_RESEARCH", "docs/mapped-object-screen-registration.md; docs/u3-sign-prize-presentation.md 'face origin (113,106)' at camera (3831,405)"), ev("POC_SOURCE", "TYPE18_RENDER_X = 0 (type `$09` uses +1; types `$10/$21/$27` use 0)")], "medium",
                 "All sprites sit 1 px right of anchor+mapping in terrain space.", "X offset 0 for type `$18` (as for the accepted `$10/$21/$27`); only type `$09` carries +1.", "UNVERIFIED", "no Windows measurement of the sign X", "possible 1 px", "low",
                 "Manager decision D4: class-wide X policy for mapped objects; do not change the sign alone.", "decision", related=["C-02"]))
    r.append(row("C-05", "sign/animation frame offsets and hop", "frames 1-5; hop (state 4)",
                 [ev("PRIOR_RESEARCH", "docs/object-18-act-clear.md section 5 (hop apex 126 px)"), ev("POC_SOURCE", "objects/OBJ_chaos_object_18/Draw_0.gml:1-11")], "medium",
                 "Hop and spin frames are anchor-relative; the pieces share the same canvas for all frames.", "Frames and hop implemented from the research; draw-only hop offset.", "MATCH", "G1/G2 accepted", "none", "low", "No action.", "resolved", basis=PRIOR_DIFF))
    r.append(row("C-06", "sign/prize selection and reward", "`$A9..` prize tables",
                 [ev("PRIOR_RESEARCH", "docs/u3-sign-prize-presentation.md; docs/g0-campaign-contract.md")], "high",
                 "Selection and reward per U3.", "Implemented and accepted.", "MATCH", "G2 accepted", "none", "low", "Must not change (I6 touches resources only).", "resolved", basis=PRIOR_DIFF))
    r.append(row("C-07", "sign/foreground priority", "6 of 942 face pixels hidden in SEZ1",
                 [ev("PRIOR_RESEARCH", "docs/u3-sign-prize-presentation.md section 'Compositing and foreground priority'")], "medium",
                 "Foreground-priority background tiles hide face pixels in SEZ act 1 only.", "Not re-inspected.", "UNVERIFIED", "none", "negligible", "low", "Deferred.", "deferred"))
    # ------------------------------------------------------------------ D: related discrepancies
    r.append(row("D-01", "loop/entry Y anchor", "`$3EAB`: `Y := (Y & ~31) + 4`",
                 [ev("PRIOR_RESEARCH", "docs/visual1-loop-shards.md A2/A8 (41318f5)"), ev("POC_SOURCE", "docs/visual-p3-loop-presentation.md section 7 (anchor 1 px above ROM)")], "high",
                 "Entry snaps X to a multiple of 32 and Y to (Y&~31)+4.", "Legacy loop-entry origin leaves the anchor 1 px above the ROM on every tick (X exact).", "MISMATCH", "VISUAL-P3 differential (110 ticks)", "1 px offset against terrain", "medium",
                 "Do not include in C1-I: it is a loop-entry change. Bundle with D-02/D-03/D-04 as a separate loop-entry package.", "deferred", deps=["D-02"]))
    r.append(row("D-02", "loop/entry rule", "`$6CBA/$6CCD` foot-block transition `$51 -> $52`",
                 [ev("PRIOR_RESEARCH", "docs/visual1-loop-shards.md A2, A8"), ev("PRIOR_RESEARCH", "data/visual1/loop-contract.json")], "high",
                 "Entry on the previous/current foot-block transition, plane 0/1, floor flag; no speed or facing gate; raw entry speed.", "Bottom-crossing X window with |hspeed| >= 0.25, possible airborne entry, per-loop plane array.", "MISMATCH", "VISUAL-1 contract; POC differential", "Entry from jump or at odd speeds", "high",
                 "Separate loop-entry package (needs the VISUAL-1 contract merged to Research main first).", "deferred", deps=["D-01"]))
    r.append(row("D-03", "loop/low-speed route", "`$0356` borrow bailout, state `$1D`",
                 [ev("PRIOR_RESEARCH", "docs/visual1-loop-shards.md A3, A9")], "high",
                 "Bailout when the cursor borrows below `$90`; X nudge; state `$1D`.", "Release when speed goes negative; jump latch.", "MISMATCH", "VISUAL-P3 'slow entry' check passes the POC behaviour, not the ROM's", "Slow-walk loop entry differs", "medium", "Same loop-entry package.", "deferred", deps=["D-02"]))
    r.append(row("D-04", "loop/speed caps", "route exit `speed := D373`",
                 [ev("PRIOR_RESEARCH", "docs/visual1-loop-shards.md A8")], "high",
                 "Raw speed; exit at progress >= `$180`.", "Speed capped at 8 px, exit speed capped, sample clamp 394, traversal one update shorter (110 vs 111).", "MISMATCH", "VISUAL-P3", "minor", "medium", "Same loop-entry package.", "deferred", deps=["D-02"]))
    r.append(row("D-05", "terrain/sticking and vibration", "terrain pass `$690B`, side sensors",
                 [ev("PRIOR_RESEARCH", "docs/visual-p1-closure.md: unchanged gameplay state on 22,983 compared updates, no collision fix claimed"), ev("PRIOR_RESEARCH", "AGENTS.md track C2")], "low",
                 "Not characterised in C1-R.", "Observed historically; possible mixture of presentation facing jitter and collision.", "UNVERIFIED", "none specific", "annoying when it occurs", "high", "Belongs to track C2; C1-R found no camera- or control-state cause (the rigid POC camera cannot jitter by itself).", "separate-research"))
    r.append(row("D-06", "spring rebound facing oscillation", "`+$04` bit 4 rules",
                 [ev("PRIOR_RESEARCH", "docs/player-spring-airborne-state-closure.md section 11 item 4 (candidate cause: sign(vx) facing)"), ev("POC_SOURCE", "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml:60-100 (legacy sprite selection outside VISUAL-P1-owned states)")], "medium",
                 "Facing is the `+$04` bit 4 flag: `$0B` follows held Left/Right, `$0E/$1C/$14` never update it.", "VISUAL-P1 fixed the owned states (0,1,3-8,15,21,26,30-32); airborne `$09/$0A/$0B/$0E/$1C/$14` still use the legacy selection and `sign(vx)`.", "UNVERIFIED", "P1 differential covers owned states only", "left/right flip after a rebound", "medium",
                 "Candidate C1-I-optional only if C2 does not take it first; the contract already exists in the spring closure document.", "separate-research", deps=["D-08"]))
    r.append(row("D-07", "slope/low-speed contact", "`$69B2`, `$6A02`",
                 [ev("PRIOR_RESEARCH", "docs/movement.md; docs/collision-geometry-audit.md")], "low", "Recovered; collision geometry audited.", "Not re-opened in C1-R.", "UNVERIFIED", "none new", "unknown", "high", "Track C2.", "separate-research"))
    r.append(row("D-08", "airborne/spring presentation set", "frames `$02-$06,$01` (fall), `$1C-$21` (tumble), `$61`",
                 [ev("PRIOR_RESEARCH", "docs/player-spring-airborne-state-closure.md section 11")], "medium",
                 "State-derived sprite/timing for `$0B/$0E/$1C/$14` (82-update `$0B` program, 232-update fall).", "Legacy flag-derived sprite choice outside P1-owned states.", "MISMATCH", "contract exists", "visual", "medium",
                 "Presentation track (VISUAL-P4 style); not part of C1-I.", "deferred", related=["D-06"]))
    r.append(row("D-09", "ceiling-spring dispatch correction C1", "blocks `$3A/$3B` from the ring-probe point",
                 [ev("PRIOR_RESEARCH", "docs/player-spring-airborne-state-closure.md section 11 item 6")], "medium", "Dispatch also from the terrain-ring probe point.", "Not re-inspected.", "UNVERIFIED", "AQZ3 natural run fixture", "AQZ3 corridor", "medium", "Track C2.", "separate-research"))
    r.append(row("D-10", "death line vs camera bottom", "screen-relative death `playerY - camY >= $D0`",
                 [ev("PRIOR_RESEARCH", "docs/player-fall-control-audit.md A9/A10")], "medium",
                 "Death when the screen Y reaches `$D0` (208) with the canonical camera bottom (784 for MGHZ1 => 992).", "POC camera bottom 832 => death line 1043 (UNRESOLVED decision).", "ADAPTER", "none", "pit death height", "low",
                 "Settle together with the boundary rule B-09 if the Manager wants it in C1-I.", "decision", deps=["B-09"]))
    return r


def decisions():
    return [
        {"id": "D1", "question": "How should the original X leads (104 facing right / 136 facing left, authored for a 256 px window) be mapped onto the 348 px view?",
         "options": [
             {"id": "D1-A", "name": "CENTER-relative", "rule": "target screen X = viewW/2 - 24 (right-facing) or viewW/2 + 8 (left-facing); zone +/-8", "effect": "keeps the original offset from the view centre: 150/182 at 348 px; visible space ahead grows by 46 px in both directions"},
             {"id": "D1-B", "name": "EDGE-relative", "rule": "target screen X = 104 / 136 from the left edge", "effect": "all extra width appears to the right: look-ahead right-facing 244 px, left-facing 212 px behind"},
             {"id": "D1-C", "name": "keep GameMaker native horizontal follow", "rule": "no change", "effect": "retains the current lack of facing lead; only vertical changes"}],
         "recommendation": "D1-A: it reuses the existing CENTER(n) category of the accepted viewport adapter and treats the change as a documented adapter. ROM does not say which was intended (docs/viewport-semantics-audit.md: unresolved)."},
        {"id": "D2", "question": "Should the GM view top be the canonical camera (status quo) or canonical camera + 17 (the ROM's R9 bias)?",
         "options": [
             {"id": "D2-A", "name": "status quo", "rule": "view top = canonical camera; follow model runs in canonical camera space", "effect": "Sonic's foot sits at screen line 80+17..112+17 = 97..129 instead of 80..112 (17 px low); minimal blast radius"},
             {"id": "D2-B", "name": "view = canonical + 17", "rule": "all canonical consumers read camera = view - 17", "effect": "exact framing; touches 79 view-Y reads in 64 files and 55 chaos_vp_current() calls"}],
         "recommendation": "D2-A for C1-I; revisit B only as a separate, fully regression-tested package."},
        {"id": "D3", "question": "View height 196 vs 192", "options": [{"id": "D3-A", "name": "extra 4 rows at the bottom", "rule": "zone is measured from the view top; 'vertical is not widened'", "effect": "ROM zone numbers unchanged"}],
         "recommendation": "D3-A (only one option compatible with the existing viewport policy)."},
        {"id": "D4", "question": "Mapped-object X policy (+1 px terrain-space bias): sign only, class-wide, or none?", "options": [
            {"id": "D4-A", "name": "leave 0 (accepted)", "rule": "no change", "effect": "sign X stays as accepted"},
            {"id": "D4-B", "name": "class-wide +1 with a Windows comparison round", "rule": "TYPE*_RENDER_X = 1 for types 10/18/21/27", "effect": "possible 1 px right shift of all mapped objects"}],
         "recommendation": "D4-A for C1-I; raise B as a separate cross-class question."}]


def contracts():
    items = [
        {"id": "I1", "title": "ROM follow camera (X and Y) replacing GameMaker's native follow in ordinary acts", "size": "moderate (one new script, one Step_2 branch; no collision or movement change)",
         "rom_requirement": ["tools/c1r_camera_model.py is the executable contract: leads (X `$68/$88`, Y `$60`) slew 1 px/update, zones +/-8 (X) and +/-16 (Y), step cap 7, low-byte compare, dropped crossing steps at limits (left/top inclusive, right/bottom exclusive), pan mode skips everything.",
                             "Initial Y lead `$78` at level load, X lead initial `$78`."],
         "rom_evidence": ["B-06", "B-07", "B-09", "B-10", TRACE],
         "poc_integration_points": [STEP2 + ":13-20 (replace the rigid End Step lock and the GM object follow)", "scripts/SCR_player_view/SCR_player_view.gml (switch the view object off for ordinary acts)", "OBJ_chaos_zone/Create_0.gml:84-101 (seed leads at level start)", "existing *_owns_camera guards in Step_2.gml:13 stay"],
         "modification_scope": "1 new script (chaos_camera_follow), edits to 3 existing files; MGHZ/AQZ/EEZ special cases (VSpeed=0, +/-7 cap) become redundant for THZ/GPZ/SEZ/MGHZ and are replaced by the same model; special stages untouched.",
         "fixtures": ["data/c1r/camera-look-trace.json: replay each scenario's player X/Y/facing/lead-target series through the GML port; per-update camera X/Y and both leads must equal the recorded work_x/work_y/lead_x/lead_y exactly (3,557 updates).", "tools/c1r_camera_model.py is the reference implementation (Python)."],
         "acceptance": ["Fixture replay: 0 mismatches", "Windows: standing on flat ground then falling/rising: Sonic rests at the original screen offsets; turning shows the 32-update lead slew; boss arenas, sign pan and special stages unchanged"],
         "risks": ["Camera-dependent systems (lifecycle bands, instance_activate_region, death line `playerY-camY >= $D0`, MGHZ oil plunge, AQZ/EEZ scroll) all read the view; the model must keep view top = canonical camera (decision D2-A)", "fast falls: step cap 7 lets Sonic outrun the camera (original behaviour; MGHZ already does this)"],
         "dependencies": ["D1", "D2", "D3"], "blockers": [], "regression_identities": ["sign pan (B-11)", "boss owners (B-12)", "viewport lifecycle verifiers", "EEZ/AQZ scroll"]},
        {"id": "I2", "title": "Look-up / look-down camera lead hooks", "size": "routine",
         "rom_requirement": ["Y lead target `D289` is a persistent value: `$B8` in state 3 and `$30` in state 4 only when the support owner is 0; `$60` in states 0,1,5,`$0F`,`$10`,`$15`,`$19`,`$1A`, in the walk request (landing/hurt recovery) and at the jump launch; unchanged in every other state (table B-05)."],
         "rom_evidence": ["B-01", "B-02", "B-03", "B-04", "B-05"],
         "poc_integration_points": [CORE + ":802-815 (states 1-4 block)", CORE + ":169-190 (SCR_cc_stand/walk/jump)", "core struct: add camera_lead_target (default `$60`, init per level)"],
         "modification_scope": "about 25 lines in SCR_chaos_core.gml plus the I1 consumer; no movement change.",
         "fixtures": ["look_up_hold_release, look_down_hold_release, look_up_then_walk scenarios: lead_target series per update must match (value and update index, after the one-update callback lag)", "release hysteresis: final screen Y 112 after look-up, 80 after look-down"],
         "acceptance": ["Fixture lead_target and camera series equal", "Windows: hold Up/Down on flat ground, release, jump from stand, ride a platform (no look)"],
         "risks": ["support owner (D3C0) must come from the existing platform carry code; verify on MGHZ `$28` platform"], "dependencies": ["I1", "A-01", "A-02"], "blockers": ["platform trace before acceptance (B-03 is BYTE-VERIFIED only)"]},
        {"id": "I3", "title": "Peel-Out (states $15/$1A) and removal of the look-up jump", "size": "moderate (new core states, no collision change)",
         "rom_requirement": ["State 3 + fresh button (Sonic only) -> `$46CE`: vx 0, request 21 (`$15`), sound request `$AC`, no jump.",
                             "State 21: lead `$60`, terrain pass, side push-out +/-4, `$48BC`, screen clamp, `$AC` re-request on fresh button, release when Up is not held -> `$46E2`.",
                             "`$46E2`: max X speed `$0700`, vx = +/-`$0700` (facing bit), request 26 (`$1A`), sound request `$BE`, invulnerable (`D503` bit 7) for 12 updates.",
                             "State 26: lead `$60`, shared movement, `$4281`, side contact clears bits 1 and 7 and walks, floor block `$19` -> run, else walk/run exits (`$37F4`)."],
         "rom_evidence": ["A-03", "A-04", "A-05", TRACE + " peel_out_ordinary / peel_out_hold_right"],
         "poc_integration_points": [CORE + ":554 (SCR_cc_shared jump)", CORE + ":761-835 (SCR_cc_tick)", "scripts/SCR_chaos_visual_p1/SCR_chaos_visual_p1.gml (presentation of 21/26 already owned)", "attack-posture code must leave bit 1 untouched"],
         "modification_scope": "about 60 lines in SCR_chaos_core.gml (two states, one interception); presentation already exists; sound ids as requests only.",
         "fixtures": ["peel_out_ordinary: states 21 from update 22, 26 from update 85, vx 1792 at the release update, friction series, D503 bit 7 for 12 updates", "peel_out_hold_right: vx constant 1792 until the ramp at x about 393 (state 27 launch)"],
         "acceptance": ["Fixture series equal (state, vx, move byte) on the same terrain", "Windows: Up + jump never jumps; charge, release with Up, run, wall hit, loop entry from 26 (observe only)"],
         "risks": ["state 26 can reach loops/ramps/springs: only the shared handlers are used, but a Windows pass must try them", "invulnerability must not enable contact kills (bit 7 only; attack bit untouched)"],
         "dependencies": ["I2 (lead rewrite in 21/26)"], "blockers": [], "excluded": ["long-hold aura (A-06)", "Tails state 24 flight"]},
        {"id": "I4", "title": "Idle wait (state 2) timer and presentation", "size": "routine",
         "rom_requirement": ["180 updates in state 0/1 (record `0B x180`) then request state 2; state 2 script `0C x64; 20 x (0D x16, 0E x16); 0F x64; 10 x16; 11 x16; 12 x16; jump $80B3`; exits per `$36F0` (A-10)."],
         "rom_evidence": ["A-08", "A-09", "A-10", TRACE + " idle_wait (180 rows in state 1)"],
         "poc_integration_points": ["scripts/SCR_chaos_visual_p1 (add state 2 program, own-state list)", CORE + ":761 (request on timeout; the core state may stay 1 if the Designer keeps ring-probe parity from the presentation counter)", "new sprites SPR_chaos_player_frame_0C..12"],
         "modification_scope": "7 sprite resources + about 30 lines; ring-probe parity unaffected (all state-2 record durations are even).",
         "fixtures": ["idle_wait trace: first state-2 update after exactly 180 state-1 updates"],
         "acceptance": ["Windows: 3 s idle -> look-around cycle; any input exits; jump works from state 2"],
         "risks": ["the shadow animation counter used by the terrain-ring probe (docs/player-animation-counter.md) must keep following the executing state's record durations"], "dependencies": [], "blockers": ["frames $0C-$12 must be imported from the ROM tile tables (A-09)"]},
        {"id": "I6", "title": "Goal-sign resource crop and draw offset", "size": "routine (resource regeneration + one constant)",
         "rom_requirement": ["Sign frames are 32x48 with 48 opaque rows (face rows 0-31, post 32-47); origin (16,48); derived draw offset +18 for a bottom-origin canvas."],
         "rom_evidence": ["C-02", "C-03", SIGN],
         "poc_integration_points": ["POC_notes/import_sign_prizes.py:51-55 (remove `out.crop((0,4,32,52))` and the margin note)", "POC_notes/import_type18_assets.py (base sprites)", "scripts/SCR_chaos_render_adapter/SCR_chaos_render_adapter.gml:11 (22 -> 18)"],
         "modification_scope": "regenerate 12 sprites (6 base x 5 frames + 6 prize sets x 48 frames; two importers); constant 22 -> 18.",
         "fixtures": ["tools/c1r_sign_registration.py ROM --poc POC: after the change xor_same_position must be 0 for all 5 base frames (and the prize frames against the same composite)"],
         "acceptance": ["Alpha mask == ROM composite, rows 0..47", "Windows: sign face top no longer flat; sign sits exactly where it did before on the ground (visible rows 4..47 unchanged)"],
         "risks": ["must change the constant and the resources in the same release (either alone shifts the sign 4 px)"], "dependencies": [], "blockers": [], "decision": "D4 (X policy) is NOT part of I6"},
    ]
    optional = [
        {"id": "I5", "title": "Ledge-edge pose (state $19)", "status": "BLOCKED on Research R-C1-1", "why": "`D368` semantics and a natural reproduction are not established (A-11)."},
        {"id": "I7", "title": "Facing bit for airborne states", "status": "OPTIONAL - only if C2 does not take it", "why": "contract exists in docs/player-spring-airborne-state-closure.md section 11 item 4 (D-06)."},
        {"id": "I8", "title": "Peel-out long-hold aura", "status": "DEFERRED", "why": "A-06; needs a 30 s charge."}]
    return {
        "format": "c1r-implementation-contracts/1", "package": "C1-I", "status": "PROPOSED - not authorised", "poc_parent": POC_COMMIT, "research_base": RESEARCH_BASE, "rom_sha256": ROM_SHA256,
        "decisions_required_before_dispatch": decisions(), "items": items, "optional_or_blocked": optional,
        "excluded_deliberately": [
            {"id": "X1", "what": "loop-entry rule, Y anchor, low-speed bailout, speed caps (D-01..D-04)", "why": "changes accepted loop mechanics; needs the VISUAL-1 contract merged and a separate differential package"},
            {"id": "X2", "what": "terrain sticking, slope, spring oscillation (D-05, D-07, D-09)", "why": "track C2; no C1-R evidence of a camera/control cause"},
            {"id": "X3", "what": "17 px vertical window bias (decision D2-B)", "why": "79 view-Y reads; separate regression package"},
            {"id": "X4", "what": "mapped-object X +1 px (decision D4)", "why": "cross-class question, not a sign-only fix"},
            {"id": "X5", "what": "special-stage and boss camera owners", "why": "accepted; inert-guard test only"}],
        "release_shape": {"recommended_order": ["I6 (independent, smallest)", "I1 + I2 together (one camera change)", "I3", "I4"], "single_windows_session": True,
                          "windows_f5_checklist": ["Stand on flat ground 10 s: foot at screen line 112 (follow rest), look-around after 3 s", "Hold Up 3 s then release; hold Down 3 s then release; compare with trace (first move about 33 updates, return delay about 35)", "Walk left/right: lead slews over about 32 updates", "Up+jump -> peel-out charge; release Up -> dash 7 px/update; Right held keeps speed; wall hit stops", "Jump from stand: camera target resets", "MGHZ platform ride: look-up does not move the camera", "Sign pan and results unchanged; sign face top complete; sign still on the ground", "Boss arenas THZ3/GPZ3/SEZ3/MGHZ3/AQZ3/EEZ3 camera unchanged; special stages unchanged"]},
        "verification_plan": {"python": "python tools/c1r_camera_model.py is the reference; tests/test_c1r_audit.py (no ROM needed) replays 3,557 updates; Designer ports the replay to a GameMaker/Node verifier like verify_viewport_adapter.js", "cost": "trace regeneration about 30 s, model replay under 1 s, sign tool about 2 s; no full-ROM replay required"},
    }


def build():
    reg_rows = rows()
    ids = [x["id"] for x in reg_rows]
    assert len(ids) == len(set(ids))
    counts = {c: sum(1 for x in reg_rows if x["classification"] == c) for c in CLASSES}
    tracks = {t: sum(1 for x in reg_rows if x["track"] == t) for t in TRACKS}
    reg = {"format": "c1r-gameplay-fidelity-register/1", "rom_sha256": ROM_SHA256, "poc_commit": POC_COMMIT, "research_base": RESEARCH_BASE,
           "legend": {"classification": list(CLASSES), "evidence_classes": list(EVIDENCE), "tracks": list(TRACKS),
                      "note": "MATCH never means 'no bug observed': match_basis states what supports it. SOURCE_COMPARED rows were not differentially executed in C1-R."},
           "counts": {"rows": len(reg_rows), "by_classification": counts, "by_track": tracks}, "rows": reg_rows}
    return reg, contracts()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    reg, con = build()
    t1 = json.dumps(reg, indent=1) + "\n"
    t2 = json.dumps(con, indent=1) + "\n"
    if a.write:
        OUT_REG.parent.mkdir(parents=True, exist_ok=True)
        OUT_REG.write_text(t1)
        OUT_CON.write_text(t2)
        print("wrote", OUT_REG, OUT_CON)
    elif a.check:
        ok = OUT_REG.read_text() == t1 and OUT_CON.read_text() == t2
        print("check:", "identical" if ok else "DIFFERENT")
        sys.exit(0 if ok else 1)
    print(json.dumps(reg["counts"], indent=1))


if __name__ == "__main__":
    main()

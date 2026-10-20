#!/usr/bin/env python3
"""Builds data/v1/twist-animation-contract.json and data/t1/discrepancy-register.json (no ROM needed).

    python tools/v1_t1_register.py --write | --check

The twist contract is data-driven: `frame_at(updates_since_entry)` below is the oracle that a GameMaker implementation (or its JS harness) must
reproduce; tests/test_v1_t1_audit.py replays it against every emulated traversal in data/v1/twist-audit.json.
"""
from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
POC_BASELINE = "ac021e1ef2665c8668de13959f5ccc4653f312d1"
RESEARCH_BASE = "c2692337649fcbd8b75c4ceff4645d9d61e2a59e"
CONTRACT = ROOT / "data" / "v1" / "twist-animation-contract.json"
REGISTER = ROOT / "data" / "t1" / "discrepancy-register.json"

FRAMES = [0x25, 0x26, 0x27, 0x28, 0x29]
DURATION = 3


def frame_at(updates_since_entry: int) -> int:
    """ROM animation frame (+$06) of state $22: update 0 is the first update the state executes (the update after the request)."""
    return FRAMES[(updates_since_entry // DURATION) % len(FRAMES)]


def contract() -> dict:
    return OrderedDict(
        format=1, rom_sha256=ROM_SHA256, research_base=RESEARCH_BASE, accepted_poc_parent=POC_BASELINE,
        scope="Presentation of player state $22 (twist strip, surface type $17) in THZ1-3 and MGHZ2. Mechanics (entry, dispatch tables, vector math, exit) are accepted and MUST NOT change.",
        rom=OrderedDict(
            script_cpu="0x8425 (bank $0C, file 0x30425)", callback_each_record="0x94C1",
            records=[{"duration": DURATION, "frame": hex(f)} for f in FRAMES], loop="FF 00 restart; cycle = 15 updates",
            frame_formula="frame = 0x25 + ((updates_since_entry // 3) mod 5)", first_update_of_state_shows="0x25 for updates 0,1,2",
            restart_on_tile_change=False, restart_on_reentry=True, reverse_on_left=False,
            facing="object +$04 bit 4 is INHERITED from the entering state and never written by the strip code (0 writes to IX+4 in $94C1..$9829); draw mirrored iff the bit is set",
            rotation="none: the ROM never rotates a sprite; the 'twisting' look is five authored frames + foreground-priority background tiles",
            variants="MGHZ (zone 3) selects variants 2/3 for right/left, other zones 0/1; the script, frames, durations and facing rule are identical in every variant"),
        poc_target=OrderedDict(
            state="core state 34 ($22)", sprites=["SPR_chaos_player_frame_25", "SPR_chaos_player_frame_26", "SPR_chaos_player_frame_27", "SPR_chaos_player_frame_28", "SPR_chaos_player_frame_29"],
            sprite_canvas="24x32 origin (12,32), RGBA equal to the ROM composites (VISUAL-0 catalogue)",
            animation_program_row_format="[type, count, frame, script_cpu_decimal]; type 0 = record, type 1 = restart",
            animation_program=[[0, 3, 37, 33829], [0, 3, 38, 33833], [0, 3, 39, 33837], [0, 3, 40, 33841], [0, 3, 41, 33845], [1, 0, 0, 33849]],
            hooks=["add 34 to chaos_player_animation_supported (SCR_chaos_player_animation.gml:5)", "add `case 34` to chaos_player_animation_program",
                   "chaos_player_animation_present already draws supported states from chaos_player_frame_sprite() with image_angle 0 and xscale from player_flags bit 4",
                   "the legacy chooser (SCR_chaos_adapter.gml:57-58 facing from sign(vx) that WRITES player_flags bit 4; :78 SPR_player_spin; :88 image_angle; :101 image_speed) must no longer run for state 34"],
            must_not_change=["SCR_cc_twist_* (SCR_chaos_core.gml:238-345)", "global.chaosTwistHandlers", "state transitions, speeds, positions", "terrain-ring shadow counter (presentation layer must not feed it)"]),
        verification=[
            "oracle: frame_at(n) for n in 0..300 equals the executing frame in every entry of data/v1/twist-audit.json emulated_scenarios (frame_rule_holds_every_update)",
            "JS harness: run SCR_cc_twist_tick for 95 updates (THZ1 right) and compare the published sprite name sequence with frame_at; assert image_angle == 0 and image_xscale follows the entering facing bit for all updates",
            "MGHZ2 chute: vx changes sign inside the strip; assert image_xscale and player_flags bit 4 are unchanged for every update of state 34",
            "negative control: legacy path must fail the same assertions (SPR_sonic_spin, image_angle != 0)",
            "state-differential: all core fields identical to the accepted parent for the same input script (presentation-only change)"],
        windows_f5=[
            "THZ1 right run (Act 1 strip): five curled-ball frames cycle at a steady rhythm independent of speed; the sprite never rotates; no quill/sphere frame is held longer than the others",
            "THZ1/THZ2 left run through the strip: same cycle, mirrored the way Sonic faced when entering",
            "descending half of the THZ arch (blocks $62-$6C,$73): Sonic is hidden behind the ribbon exactly while the foreground priority tiles overlap him (about 54 of 95 updates have hidden pixels; 6 are fully hidden)",
            "MGHZ2 chute: no mirror flip mid-ride; sprite disappears behind the partial priority cells at the two bends",
            "exit: ball frames hand over to the ordinary roll cycle with no pop in position"])


def reg_rows() -> list:
    R = []

    def add(id_, area, title, cls, kind, impact, rom, poc, action, deps="", status="open"):
        R.append(OrderedDict(id=id_, area=area, title=title, classification=cls, change_kind=kind, impact=impact, rom_evidence=rom, poc_evidence=poc, action=action, depends_on=deps, status=status))

    add("V1-01", "twist", "Twist drawn with the legacy 40x40 SPR_sonic_spin instead of ROM frames $25-$29", "confirmed mismatch (source-read; Windows not run)", "purely visual", "high",
        "state $22 script 0x8425: records 3x frame $25,$26,$27,$28,$29, FF 00 loop (DECODED)", "SCR_chaos_adapter.gml:78 SPR_player_spin; chaos_player_animation_supported omits 34", "PKG-V1")
    add("V1-02", "twist", "Sprite is rotated by the path angle", "confirmed mismatch", "purely visual", "high",
        "ROM never rotates sprites; 0 writes of frame or flags in $94C1..$9829 (BYTE-VERIFIED)", "SCR_chaos_adapter.gml:88 image_angle=(angle-64)*360/256", "PKG-V1")
    add("V1-03", "twist", "GameMaker image_speed 0.075-0.325 replaces the fixed 3-update/5-frame cycle", "confirmed mismatch", "purely visual", "medium",
        "frame_at(n)=0x25+((n//3) mod 5) held for 100% of updates in 10 traversals (EMULATED)", "SCR_chaos_adapter.gml:101", "PKG-V1")
    add("V1-04", "twist", "Facing derived from sign(vx) and written back to player_flags bit 4", "confirmed mismatch (also a non-ROM write to a shared flag)", "visual + removes a non-ROM flag write", "medium (MGHZ2 chute flips)",
        "facing bit inherited; strip never writes it; MGHZ2 vx range -1050..+1270 with bit constant (EMULATED)", "SCR_chaos_adapter.gml:57-58", "PKG-V1")
    add("V1-05", "twist", "Strip depth ordering = per-cell priority tiles (THZ blocks $62-$6C,$73 fully; MGHZ 16 blocks partially)", "accepted adapter (CROSSZONE-FG1 foreground pass); not Windows-verified for the strip", "none expected", "medium",
        "block mapping bit 12: THZ 192 cells, MGHZ2 75 cells (DECODED); Sonic hidden pixels 54/95 and 39/93 updates (EMULATED)", "OBJ_chaos_terrain_foreground depth -60 over player -50; SPR_chaos_thz_foreground / mghz_foreground from verify_thz_foreground.py", "check only in F5; no change", status="verify")
    add("V1-06", "twist", "MGHZ and THZ share one animation; entry rule and variant tables differ", "proven match (static)", "none", "info",
        "same script and frames in THZ1/2/3 and MGHZ2; MGHZ right entry clamps speed up to 0x0500; variants 2/3 (EMULATED + BYTE-VERIFIED)", "SCR_cc_twist_enter reproduces the clamp; 112/112 dispatch handlers equal data/twist-dispatch.csv", "none")
    add("V1-07", "twist", "Existing twist verifiers assert mechanics only", "test gap", "tests", "medium", "n/a",
        "verification/verify_v16_twist.js, twist-results.json: no sprite/frame/facing field", "add the oracle test of PKG-V1", "PKG-V1")
    add("V1-08", "twist", "Entry tile touch requests sound $A5 before the speed test", "adapter-free numeric fact; no audio authorised", "none", "low",
        "0x6E74 and 0x6EF7 write $DE04=$A5 before the speed gate (BYTE-VERIFIED)", "not modelled (audio out of scope)", "record only")
    add("T1-01", "boss camera", "THZ3 boss creation switches the camera to 'centre on Sonic' (snap up to viewW/2-HBorder = 23 px at 348 px)", "confirmed mismatch (source-read)", "camera ownership", "high",
        "ROM: no camera write at creation; left limit follows the camera (D280=cam each update); follow continues until trigger (EMULATED THZ3: 4 px/update, no step >7)", "SCR_chaos_boss.gml:244-247 camera_mode 1", "PKG-T1A", "C1-I I1 camera final SHA")
    add("T1-02", "boss camera", "THZ3 release (mode 4) re-centres: Sonic at 1886 => camera 1679 -> 1712 in one update (33 px)", "confirmed mismatch (source-read, example computed)", "camera ownership", "high",
        "ROM: first 14 updates after release 1679,1686,1693,...: 7 px/update cap (EMULATED)", "SCR_chaos_boss.gml:253-257", "PKG-T1A", "C1-I I1")
    add("T1-03", "boss camera", "GPZ3 follow modes 1/4 centre on Sonic at width 256 (wide uses bounded 4 px/update)", "intentional widescreen adapter at wide; mismatch only at 256", "camera ownership (256 only)", "low",
        "ROM follow is lead 104/136 +-8, <=7 px/update (docs/viewport-semantics-audit.md)", "SCR_chaos_gpz_boss.gml:298-302", "decide D-T1-2")
    add("T1-04", "boss camera", "SEZ3, MGHZ3, AQZ3: ROM-form follow at 256 and bounded 4 px/update adapter at wide, takeover from last normal camera", "intentional widescreen adapter", "none", "info",
        "release: 7 px/update (SEZ, MGHZ EMULATED); MGHZ clear gate WORLD X>=3356 + floor", "SCR_chaos_sez_boss.gml:557-600, mghz_boss, aqz_boss", "none")
    add("T1-05", "tests", "verify_thz3_boss_clear.js:84 expects legacy SPR_player_walk; accepted POC draws SPR_chaos_player_frame_02", "stale test expectation (fails on the accepted parent); committed thz3-boss-clear-trace.json stale for the same reason", "tests only", "medium",
        "state $20 uses the walk selector $8EE1 (frames $01-$06; first update frame $02 in the POC fixture)", "node verification/verify_thz3_boss_clear.js -> AssertionError actual 'SPR_chaos_player_frame_02' expected 'SPR_player_walk'", "PKG-T1B: update expectation to the ROM frame, regenerate trace; do not loosen the attack-bit assertion", "")
    add("T1-06", "boss palette", "Boss sprite-palette swap is instant and shared (colours 13-15 of the sprite palette) 2-5 updates after state 3 in THZ/SEZ/MGHZ", "unverified in POC (art is pre-baked per sprite)", "visual", "medium",
        "THZ3 u173, SEZ3 u171, MGHZ3 u173; BG palette untouched; no fade (EMULATED)", "SPR_chaos_boss_50*, flash variants; effect on other sprites using colours 13-15 not inspected", "R-T1-2 inspect Sonic/ring/HUD use of colours 13-15; then decide")
    add("T1-07", "boss palette", "Hit flash = colours 13/14 white for command calls 4-7 (4 updates), four command slots", "claimed match by earlier boss work; not re-traced", "visual", "low",
        "docs/object-50.md section palette; command 7 fixture", "SCR_chaos_boss.gml:77 flash=4; mghz/sez/aqz flash arrays", "none unless F5 disagrees", status="verify")
    add("T1-08", "transition", "Clear transition: hold 64 (66 boss) frames, 3-step white fade (5 frames/step), 1-frame display blank at +188, fade-in, tally, second white fade then 3-step black, next level", "recovered earlier (U4); timing alignment with the POC clock unverified", "visual timing", "low",
        "ordinary: 64/69/74, 188-189, 220/225/230, 535-545 white, 635-645 black, next act +677; THZ3 boss: 66,...,722,817,next +860 (EMULATED, harness frames)", "SCR_chaos_results.gml:60-66, 177-181, 252", "F5 stopwatch only", status="verify")
    add("T1-09", "goal", "Act-clear timeline identical in all 12 ordinary acts (contact +280 state $20, +308/309 flag, camera settles sign-129 / sign-153, flag at player-camera 289)", "proven match as ROM contract; POC accepted (G1-D, U3)", "none", "info",
        "12/12 acts (EMULATED)", "chaos_goal_* functions; widescreen EDGE(RIGHT,+33)", "none")
    add("T1-10", "goal", "No sparkle objects exist in the ordinary act-clear in any zone", "ROM fact", "none", "info",
        "object pool during the sequence holds only $18 and $19 in all 12 acts (EMULATED)", "no goal sparkle code in the POC", "keep ring sparkles and boss-defeat sparkles separate")
    add("T1-11", "boss defeat", "Defeat sparkle trail: $0A param 0 controller; sparkle $FF every 8 updates from controller+10, at Sonic's world position (0,-12/-8), world-fixed, 29 rows", "proven match in code reading (OBJ_chaos_boss_effect); art registration not Windows-verified", "none", "low",
        "THZ3: 20 sparkles, interval 8, offsets alternate (0,-12),(0,-8), displacement (0,0) (EMULATED)", "OBJ_chaos_boss_effect/Step_0.gml: mod 8, dy -12/-8, life 28", "none")
    add("T1-12", "boss exit", "Sonic disappears then reappears already running after boss defeat", "unverified observation; not reproducible from source or the JS harness", "undetermined (camera ownership / player visibility / next-act start state)", "high",
        "ROM: Sonic runs off the right edge (screen X 200 at state $20 start, off-screen by flag) then the frozen scene fades; no hide", "committed THZ3 trace shows Sonic visible every update; hypotheses H1 camera snap, H2 invulnerability blink, H3 canonical off-screen run + next-act carry-over of vx, H4 a view/depth change", "R-T1-3: Windows capture + per-update dump of OBJ_player visible/alpha/x/vx/view_x for 600 updates after the boss converts")
    add("T1-13", "boss defeat", "GPZ3/AQZ3/EEZ3 defeat->release->run-off were not re-traced in this study", "not audited here; contracts exist in earlier audits", "none", "info",
        "docs/gpz3-boss-runtime-audit.md, aqz3-boss-59-audit.md, eez-boss-endgame-audit.md", "see audit docs", "reuse earlier contracts; add traces only if F5 disagrees", status="not-audited")
    add("T1-14", "baseline", "Final C1-I SHA not obtainable; POC remote exposes no C1-I branch", "baseline gap", "process", "info",
        "git ls-remote shows ac021e1 as newest accepted POC branch", "accepted gameplay baseline ac021e1", "Manager to supply the final C1-I SHA before PKG-T1A starts", status="blocked")
    return R


def register() -> dict:
    return OrderedDict(format=1, rom_sha256=ROM_SHA256, research_base=RESEARCH_BASE, accepted_poc_parent=POC_BASELINE, rows=reg_rows())


def build() -> dict:
    return {CONTRACT: contract(), REGISTER: register()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    for path, data in build().items():
        text = json.dumps(data, indent=1) + "\n"
        if a.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            print("wrote", path.relative_to(ROOT))
        elif a.check:
            print(path.name, "identical" if path.exists() and path.read_text() == text else "DIFFERS")


if __name__ == "__main__":
    main()

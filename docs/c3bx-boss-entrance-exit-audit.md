# C3-BX: cross-zone boss entrance and post-clear audit

Research only. No POC edits, no root AGENTS.md edits, no release package. Nothing is implemented; the "candidates" are in-memory text patches run in the research harness.
Base: research P4 preflight `981145f961ac71ea3f373899b027a9e3cec1f5e0`. POC reference: `354532f1819ae37bebb639ef47f538bf7876d0e6` (P4 closure; branch `poc/p4-integrated-zone-presentation`).

Evidence labels: **EMULATED** = unmodified ROM v1.2 in the T2 rig (+ **SYNTHETIC** where the scenario is injected, stated). **ROM CACHE** = natural ROM fights recorded by earlier research phases (`data/rom-cache`). **POC-SOURCE MODEL** = shipped P4 GML in the node VM harness (not GameMaker, not Windows). **PROPOSAL MODEL** = P4 GML plus the exact text patches of `tools/c3bx_candidates.js`, applied in memory only (the POC checkout is never written). Everything marked *unverified* has not been seen on Windows.

---

## 1. Answers first

1. **AQZ3 walk-off is a camera defect, confirmed.** In the ROM the camera follows Sonic for 150 updates (screen X ~118) until the world edge (camera 2303 = 2560 - 256), and the act clears 180 updates after state `$20` starts with Sonic at world X 2595. In P4 at 348/400 the camera never moves (first move: none), the run ends at world X 2112 / 2160, 480 / 435 px short of the ROM, and 485 / 433 px of valid world are never scrolled into view. Cause: two wide-only locks in `SCR_chaos_aqz_boss.gml`: the mode-4 branch at **:612-614** (`cp_x=fight_x; cp_y=fight_y; frozen=true`) *and* the `$81BD` viewport callback at **:57-59** (`camera_left = camera_right = fight_x`). Removing only the first is not enough (the second pins the limits); removing both is not enough either (section 3, A2).
2. **It was added on purpose, as a precaution, not out of necessity** (`docs/aqz-package-p4-c.md` "Locked wide clear camera", `-d`): the worry was "no black world beyond terrain". The world is 2560 wide and the camera is already capped at worldWidth - W in `chaos_59_camera_step` (:630) and by the zone End Step clamp (`Step_2.gml:29-31`), so no void can appear. The docs' claim "not a shortened run" is false for the locked camera: the clear threshold EDGE(RIGHT,+33) of a fixed camera is world X 1727+W+33 = 2108 / 2160, not 2592.
3. **Same class of defect elsewhere, smaller:** SEZ3 and MGHZ3 freeze the camera early at wide widths (402 / 172 px short at 348, 376 / 118 at 400) because the wide post-clear follow is capped at 4 px/update while state `$20` moves Sonic 6 px/update, so Sonic reaches the shared freeze edge EDGE(RIGHT,-7) first. THZ3 reaches the world edge (6 px short). GPZ3 is limited by its restored right limit (1920) and reaches it.
4. **THZ3 walk-on is not a trajectory problem.** Boss walk (34 px, 67 updates, 1935 -> 1902) matches the ROM exactly. The problem is exposure: at 348/400 the whole 40-column sprite appears at screen X 314 / 340 (first frame of state 18), where the ROM shows 5 columns at the right edge (271). A small camera-only candidate (B1) restores the ROM geometry, and it also fixes a world-coordinate leak in P4 at 400 (fight starts at boss X 1896 instead of 1902).
5. Everything else in entrances is clean in P4 (section 5): no camera retreat, no creation step beyond 4 px, boss world coordinates and sequences unchanged. Remaining "early exposure" items are MGHZ3 (revealed whole at the pan start) and nothing else new.

## 2. Exit matrix (`data/c3bx/exit-matrix.json`, `python tools/c3bx_exit_matrix.py --table`)

Scenario: the shipped entrance runs to the settled arena; fresh standing Sonic at camera + 73 (the screen X of the ROM AQZ3 exit; GPZ3 uses 97 to match its natural ROM fight); the zone's own clear routine runs; RIGHT is not held afterwards (MGHZ3: a scripted 6 px/update walk to the `$81BD` gate). t0 = first update in player state `$20`. "short" = valid camera range never scrolled into view.

| Zone | Width | Source | Camera final / legal max | Short | First camera move | Last move (freeze) | Sonic screen X while following | Act clear | Sonic world X at clear |
|---|---|---|---|---|---|---|---|---|---|
| AQZ3 | 256 | ROM (rig; natural cache agrees: 36 / 150 / 179 / 2595) | 2303 / 2304 | 1 | +36 | +150 | 118 | +180 | 2595 |
| AQZ3 | 256 | P4 | 2300 / 2304 | 4 | +42 | +156 | 112 | +187 | 2592 |
| AQZ3 | 348 | P4 | **1727** / 2212 | **485** | **none** | **none** | - | +107 | **2112** |
| AQZ3 | 400 | P4 | **1727** / 2160 | **433** | **none** | **none** | - | +115 | **2160** |
| AQZ3 | 348 / 400 | A1 only | 2190 / 2156 (max 2212 / 2160) | 22 / 4 | +59 / +66 | - | 220 / 250 (hugs the right edge) | +184 / +187 | 2574 / 2592 |
| AQZ3 | 348 / 400 | **A1+A2** | **2206 / 2156** (max 2212 / 2160) | 6 / 4 | +59 / +66 | +148 / +144 | 158 / 184 | **+187 / +187** | **2592 / 2592** |
| THZ3 | 256 | ROM (rig) | 2303 / 2304 | 1 | +36 | +158 | 118 | +188 | 2595 |
| THZ3 | 256 / 348 / 400 | P4 | 2300 / 2206 / 2155 | 4 / 6 / 5 | +42 / +59 / +66 | - | 112 / 236 / 264 | +195 | 2592 |
| SEZ3 | 256 | ROM (rig) | 3839 / 3840 | 1 | +36 | +198 | 118 | +228 | 4131 |
| SEZ3 | 256 / 348 / 400 | P4 | 3836 / **3346 / 3320** | 4 / **402 / 376** | +42 / +59 / +66 | +204 / +175 / +188 | 112 / 220 / 266 | +235 / +184 / +197 | 4128 / 3730 / 3756 |
| SEZ3 | 348 / 400 | A1+A2 | 3746 / 3692 | 2 / 4 | +59 / +66 | +212 / +216 | 158 / 184 | +251 / +259 | 4132 / 4128 |
| MGHZ3 | 256 / 348 / 400 | P4 | 3579 / **3320 / 3322** | 5 / **172 / 118** | +1 | +36 / +30 / +39 | 115 / 320 / 359 | +67 / +39 / +48 | 3871 / 3703 / 3757 |
| MGHZ3 | 348 / 400 | A1+A2 | 3487 / 3436 | 5 / 4 | +1 | +28 / +23 | 169 / 202 | +67 | 3871 |
| GPZ3 | 256 | ROM (natural cache) | 1915 / 1919 | 4 | +23 | +92 | 116 | +122 | 2207 |
| GPZ3 | 256 / 348 / 400 | P4 | 1919 | 0 | +38 / +56 / +64 | +102 / +145 / +164 | 128 / 203 / 256 | +130 / +161 / +178 | 2210 / 2304 / 2354 |

How to read it:

* **Freeze mechanism.** ROM: the camera follows (Sonic parked at screen ~118) until the world limit; the shared freeze at EDGE(RIGHT,-7) (`$F8`) is never reached first. POC wide: the camera is slower than Sonic, Sonic drifts to the right edge (steady screen X 220-359), and the freeze fires at +175..+190 well before the world edge (SEZ3, MGHZ3) or never starts (AQZ3).
* **Act-clear threshold** is already width-correct in the shared code (`chaos_goal_clear_dx`: screen X W + 33 of the frozen camera). Sonic's world X at clear is therefore ~2592 at every width *if and only if* the camera reaches the world edge. That is the check that separates a faithful exit from a shortened one.
* **Next-scene handoff:** ROM changes zone/act in the same update as the act-clear flag (AQZ3 +179/+180, GPZ3 +122/+123). The POC hands off through its results scene after the flag; no wide-specific difference was found (not traced past the flag).
* **MGHZ3 differs structurally:** `$81BD` restores the right limit on every call, but state `$20` only starts when Sonic walks past world X 3356 on the floor. ROM replay (`camera_release_replay`): the camera follows at +7 px/update from the first update after the restore (Sonic standing at screen 200). The ROM state-`$20` run-off itself for MGHZ3 and GPZ3 could not be forced (writing the boss state is overwritten by the script engine); GPZ3 has a natural trace, MGHZ3's run-off is shared code traced in THZ3/SEZ3/AQZ3. *Unverified for MGHZ3 as a single ROM trace.*
* **Systemic +7-update lag (all zones, 256 too):** the POC player's `x` integrates ~7 updates later than the ROM in state `$20` although `vx` is identical update for update (AQZ3: px +20 = 1806 vs ROM 1814; first camera move +42 vs +36; clear +187 vs +180). It is in the shared state-`$20` code or its harness hosting; it is not exit-camera related, not widescreen related, and has no visible consequence beyond ~0.1 s. *Unexplained; flagged, no candidate.*
* **GPZ3** uses a rigid centre follow in mode 4 (`round(player.x - w/2)`, :317-320) instead of the ROM lead/dead-zone: Sonic at screen 128 vs ROM 116, camera final 1919 vs 1915. Cosmetic, 256-wide, pre-existing; listed so it is not mistaken for a wide bug.

## 3. Correction candidates (camera only)

No boss mechanic, world coordinate, sprite mapping, clear gate, timer, `$0A`/`$0F` conversion or the shared player-boundary rule is touched. The P4 approach lock (`:287`, `$0356`) and left raise (`:76-77`, `$8199`) are untouched.

**A1 - AQZ3: delete the explicit wide clear adapter** (`SCR_chaos_aqz_boss.gml`)

```
-    if (cp_pc == $81BD && cp_b.clear && cp_vp.w > 256) {            // :57-59
-        cp_b.camera_left=cp_b.fight_x; cp_b.camera_right=cp_b.fight_x;
-    }
...
-    } else if (cp_b.camera_mode == 4 && cp_wide) {                   // :612-614
-        // Explicit wide clear adapter: state $20 runs off the fixed fight view.
-        cp_x=cp_b.fight_x; cp_y=cp_b.fight_y; cp_b.frozen=true;
     } else if (cp_b.camera_mode == 4) {
```

Wide mode 4 then runs the branch that already exists for it: restored right limit, `chaos_59_post_clear_x`, final cap `chaos_59_camera_bound` / End Step clamp, EDGE(RIGHT,-7) freeze.

**A2 - post-clear follow speed in wide views, 4 -> 7 px/update (the recovered follow maximum `CHAOS_54_FOLLOW_RIGHT`)**, X only, Y stays 4:
`SCR_chaos_aqz_boss.gml:573`, `SCR_chaos_sez_boss.gml:541`, `SCR_chaos_mghz_boss.gml:470` (`clamp(...,-4,4)` -> `-7,7`); `SCR_chaos_boss.gml:248` (THZ3 `chaos_boss_follow_step`, cap 7 only when `cp_mode == 4`); `SCR_chaos_gpz_boss.gml:320` (mode 4 only). The 4 px cap exists for *takeover smoothness* (V1/T1); at release the camera is already at rest and the lead slews 1 px/update, so no snap results. The pan and approach caps (`:550`, `:477`, `:285`, `:323`) stay 4.

A1 alone is insufficient (table: Sonic outruns the camera, 22 px short at 348, steady screen X 220); A2 alone does nothing for AQZ3. **A1+A2 is the smallest set that reproduces the ROM exit at 348 and 400** in AQZ3, and repairs SEZ3/MGHZ3 (402 -> 2, 172 -> 5 px short) with the same one-token edit. THZ3 and GPZ3 get the lead-correct Sonic position (158-200) with identical clear timing and world X.

*Rejected alternatives* (the Manager asked not to assume): extending Sonic's run or delaying act completion is not needed - with A1+A2 the clear lands at +187 updates and world X 2592 at every width, the same as P4 at 256; shifting the world/boss is not needed; a wide-only scripted scroll is not needed. No invented level content: the camera ends exactly on the last world column (2560).

**B1 - THZ3 walk-on, keep-right framing** (`SCR_chaos_boss.gml`, same family as the accepted GPZ3/SEZ3/MGHZ3 width-adjusted targets; three lines)

```
 :243  if (cp_mode == 1) { cp_lim.left=max(cp_lim.left,cp_b.camera_min); if (cp_vp.w > 256) cp_lim.right=min(cp_lim.right,1664-(cp_vp.w-256)); }
 :265  cp_x=cp_vp.left+sign((CHAOS_BOSS_CAMERA_X-(cp_vp.w-256))-cp_vp.left);
 :112  if (chaos_boss_x(cp_b)-cp_b.camera_x <= 223+(cp_vp.w-256)) chaos_boss_set_state(cp_b,6);
```

Boss world X, trajectory and mechanics are untouched; the camera, not the boss, moves, and the walk-on gate keeps the stop at world 1902.

| THZ3 entrance | ROM 256 | P4 256 | P4 348 | P4 400 | B1 348 | B1 400 |
|---|---|---|---|---|---|---|
| state 18 starts: camera X / boss screen X | 1664 / 271 | 1666 / 270 | 1620 / 316 | 1594 / 342 | 1572 / 364 | 1518 / 418 |
| first visible columns (screen X of anchor) | 5 (271) | 8 (268) | **40 (314)** | **40 (340)** | 6 (362) | 4 (416) |
| walk-on | 34 px / 68 upd | 34 / 67 | 34 / 67 | **40 / 80** | 34 / 67 | 34 / 67 |
| fight start: boss world X / screen X | 1901 / 223 | 1902 / 223 | 1902 / 223 | **1896** / 222 | 1902 / 315 | 1902 / 367 |
| pan end camera X | 1679 | 1679 | 1679 | 1674 | 1587 | 1535 |
| camera retreat | 0 | 0 | 0 | 0 | 0 | 0 |

Trade-off (decision for the Manager, D-T3-2 provisionally accepted the current exposure): B1 shows 92 / 144 px more *left* terrain (valid: camera >= 1535, THZ3's arena floor starts at world X 1480 per T2; the left edge reaches it at W = 456, so widths above ~455 px are *unverified*). It places the fight on the right of the wide view (boss screen 315 / 367), as GPZ3/SEZ3/MGHZ3 already do. The alternative with no camera change is to keep the pop-in and accept it.

## 4. Other zones: entrances (P4, `data/c3bx/entrance-matrix.json`) and EEZ3

P4 entrances (first-visible columns @ anchor screen X; ROM 256 -> P4 348): GPZ3 24 @ 193 -> 285; SEZ3 40 @ 161 -> 253 (both appear whole in place; position follows the width-adjusted fight camera, canonical); MGHZ3 1 @ 271 -> **32 @ 306** (revealed whole at the pan start - accepted D-T3-2); AQZ3 1 @ 259 -> 1 @ 351 (view-space adapter restores the sliver; at 400 no sprite became visible within the 450-update window - the `intro_ready` gate; *unchecked beyond the window*); EEZ3 15 @ 257 -> 15 @ 349 (relocation adapter keeps the sliver). x-retreat 0 in every zone and width; creation steps [4,0] (AQZ3 ROM [4,5]); the P4 package worked as designed.

**EEZ3** (three encounters in one act; ROM CACHE `data/rom-cache/eez/boss-game-checks.json`, controlled chain): encounter 1 `$5E` camera (1946,323) -> pan to (1951,333) over ~225 updates; on defeat the ordinary follow resumes with the boss-written limits; encounter 2 `$60`: camera 1951 -> 2214 in one update at its init, then 2228, 2235, 2335 (ROM-native jump, not a follow); encounter 3 `$61/$62`: camera 2335 -> **1830 in one update** at init; the final defeat sets clear flags `$50` and there is **no state `$20` run-off**: the camera stays at 1830 and zone 6 / ending is entered after the `$1543` wait (POC: `chaos_eez_boss_terminal_step`, 198 updates, then the P5 handoff, camera frozen on `clear&16`). The POC already shows the P4 EEZ pan Y <= 1 px/update (`:323`). *Not run numerically in the POC*: encounters 2 and 3 camera snaps and the exit at 348 (the EEZ chain needs the full carrier harness); source reading shows `chaos_eez_boss_route` enters boss 60 at the actual viewport edges (`cp_v.left + (odd ? 0 : cp_v.w)`), i.e. a view-relative edge entry, and the final-handoff camera is frozen, so no AQZ3-type camera shortcut is expected. One Windows capture closes it (section 7).

## 5. Classification of every difference

| Difference | Class |
|---|---|
| AQZ3 camera locked and frozen at wide (A1) | **POC defect** (mis-judged precaution; shortened run, static scenery) |
| 4 px post-clear cap makes SEZ3/MGHZ3/AQZ3 freeze early (A2) | **POC defect** (adapter side effect) |
| THZ3 whole sprite pops in at 314/340 (B1); fight start 1896 at 400 | **Adapter exposure / POC defect** (camera framing only) |
| MGHZ3 revealed whole at pan start (32 columns @ 306) | **Intentional adapter, accepted** (D-T3-2) |
| AQZ3 sliver restored by view-space translation; EEZ3 relocation | **Intentional adapters** (documented) |
| Camera Y/lead details at 256 (steady 112 vs 118), GPZ3 rigid centre follow in mode 4 | **Pre-existing small POC difference**, not widescreen |
| +7 update lag of state `$20` movement | **Unexplained shared difference**, no visible effect |
| EEZ3 encounter-2/3 camera jumps and no `$20` run-off; MGHZ3 post-defeat player walk to 3356 | **Canonical ROM** |
| THZ3 walk 34 px at 0.5 px/update, first frame at the edge | **Canonical ROM** |

## 6. Numeric acceptance tests (`tests/test_c3bx.py`, 12 tests, pass)

Exit (A1+A2), AQZ3 at 348 and 400, plus the same for SEZ3, MGHZ3, THZ3: camera first moves by +66 updates (ROM +36, POC 256 +42); no back-scroll (0); camera final within 6 px of worldWidth - W (2212 / 2160 AQZ3; 3748 / 3696 SEZ3; 3492 / 3440 MGHZ3); act clear exactly as many updates after t0 as at 256 (AQZ3 187); Sonic world X at clear 2590-2596 (AQZ3), within 4 px of the 256 value elsewhere; steady Sonic screen X 150-190 (not the screen edge); the 256 series is byte-identical to P4 (A1 and A2 do not alter any 256 row).
Entrance (B1): fight boss X 1902 at 256 / 348 / 400; walk 34 px; first visible <= 8 columns; x retreat 0; 256 rows identical to P4.
Frozen unchanged: all boss state sequences, creation positions, `camera_right` locks of P4.

## 7. Windows checklist (F5, 256 and 348; 400 optional)

1. **AQZ3** (use developer navigation to the boss, defeat it): after the last hit Sonic runs right and the background/terrain scrolls with him (he stays near the middle-left, ~screen 150-190 at 348), the view stops on the last column of the level, Sonic exits the right edge, the act ends about 3 s after the run begins (same duration as at 256). No stationary background, no black column.
2. **SEZ3, MGHZ3, THZ3, GPZ3**: same run-off at 348 - scenery keeps scrolling until the level edge; no early stop with Sonic running across a frozen screen.
3. **THZ3 entrance (only if B1 is taken):** the boss enters from the right edge of the 348 view and slides in ~34 px, no sprite pops into the middle of the screen; arena left edge shows floor, no void.
4. **256 regression:** all exits and the THZ3 entrance look as before P4.
5. **Capture for the open items** (single, developer-gated, like `boss_exit_trace.csv`): enable F3 before the fight and send `boss_exit_trace.csv` from (a) AQZ3 at 348, (b) EEZ3 final encounter at 348 (one run through all three encounters); the existing columns already contain view X, Sonic screen X, core state and act clear.

## 8. Explicitly unverified

* All camera/exit numbers are node-VM or emulator results; none seen in GameMaker or on Windows.
* ROM exit traces are SYNTHETIC injections of the defeat (state forced to `$05`, Sonic placed at screen 73); GPZ3 and AQZ3 natural cache runs agree with them where comparable. MGHZ3's post-gate run-off and GPZ3 at screen 73 have no direct ROM trace.
* EEZ3 encounters 2-3 in the POC; AQZ3 intro at 400 px beyond 450 updates; THZ3 widths above ~455 px; behaviour of the results scene after the clear flag at wide.
* The +7 update state-`$20` lag: measured, cause not identified.

## 9. Reproduction

```
POC=<354532f checkout>  node tools/c3bx_poc_exit_run.js --check                      # P4 exit series
POC=<354532f checkout>  C3BX_PATCH=A1,A2 node tools/c3bx_poc_exit_run.js --check     # candidate (also A1)
POC=<354532f checkout>  node tools/c3bx_poc_entrance_run.js --check ; C3BX_PATCH=B1 ... --check
POC=<354532f checkout>  T3_OUT=data/c3bx/poc-series-p4.json T3_WIDTHS=256x192,348x196,400x225 node tools/t3_poc_boss_run.js --check
python3 tools/c3bx_rom_exit.py <ROM> --check      # needs the ROM; sha256 eabc8db5...e607
python3 tools/c3bx_exit_matrix.py --check ; python3 tools/c3bx_entrance_matrix.py --check ; python3 -m unittest tests.test_c3bx
```

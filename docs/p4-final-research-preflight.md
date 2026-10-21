# P4 final research preflight

Research only. No POC edits, no root AGENTS.md edits, no ROM bytes or derived art committed.
Accepted T3 commit `7a39b3fb65e29c635e0bdaba2b7c5e496bfcccc2` is unchanged; this addendum lives on `research/p4-final-preflight`.

Baseline: POC `03db5e1c53497e76bf9e8f511b1c98ec0443be90` (`poc/v1-t1-consolidated`).
Evidence labels: **POC-SOURCE MODEL** = the shipped GML run in the node VM harness (`verification/chaos_world_harness.js`, Step_2 order). **PROPOSAL MODEL** = the same source with one camera decision replaced in memory in the research process (`tools/p4_proposal_model.js`); it is not POC code. **EMULATED** = ROM v1.2 in the T2 rig. S0 findings are **SOURCE READING** plus a POC-SOURCE MODEL of the start fall; nothing in them was observed on Windows.

C1-I evidence (`data/t3/*`) is preserved. New baselines are stored separately in `data/p4/`.

---

## 1. Assignment A: what V1/T1 changed, and what persists

V1/T1 changed only THZ3's boss camera (`chaos_boss_follow_step`, `SCR_chaos_boss.gml:235`) and the shared player clamp (`chaos_player_bounds_apply`, `SCR_chaos_goal.gml:246`). The other five boss zones produce the same created, pan, first-visible, camera, player and right-limit series as C1-I at 256, 348 and 400 (`tests/test_p4_preflight.py::TestRebaseline`).

| Zone | T3 problem | Status on 03db5e1c |
|---|---|---|
| THZ3 | continuity at the creation update; Sonic beyond the boss clamp | **FIXED**. Creation step [4,0] at 256 and [3,0] at 348/400 (was [0,0]); Sonic beyond clamp 0 (was 54/96/107). No retreat. |
| GPZ3 | camera rolls backwards; width-adjusted limit | **PERSISTS**. X retreat 12 / 92 / 144 at 256 / 348 / 400. Creation step [-12,-11] at 256, [-4,-4] wide. The right limit is only set to 1664 at the trigger, not 1664−(W−256). |
| MGHZ3 | vertical takeover | **PERSISTS**. Creation step [0,-7] at 256, [0,-4] wide. Camera rises 29 / 76 / 59 px before the stop. |
| SEZ3 | creation step; early right limit | **PERSISTS**. Retreat 12 / 4 / 9. Creation step [-12,-16] at 256, [-4,-4] wide. |
| AQZ3 | missing lock and rollback | **PERSISTS**. Retreat 166 (hold) / 76 / 22 at 256 / 348 / 400. The `$8199` left raise and `$0356` right lock are not applied. At 256 Sonic ends 158 px beyond the clamp. |
| EEZ3 | pan-start snap | **PERSISTS, reachable**. Y step 49 / 25 / 25 in one update at pan start (ROM pans 1 px per update). |

Anchor drift versus T3 is recorded in `data/p4/baseline-summary.json` (THZ3 anchors moved; the other zones' anchors are unchanged).

## 2. Implementation contract (one P4 package, per D-T3-1)

Five small edits in four files. Each is a generalisation of something V1/T1 already ships for THZ3, so none is new camera design.

| Pkg | Function / line (final) | Change |
|---|---|---|
| T3-A | `chaos_51_camera_step` (`SCR_chaos_gpz_boss.gml:273`), `chaos_54_camera_step` (`SCR_chaos_sez_boss.gml:557`), `chaos_56_camera_step` (`SCR_chaos_mghz_boss.gml:485`), `chaos_59_camera_step` (`SCR_chaos_aqz_boss.gml:583`) | In `camera_mode` 0–2 (0 is the creation update itself) replace the legacy rigid follow (`player.y − h/1.5`, centre X) with the `chaos_boss_follow_step` pattern: `chaos_cam_follow` with the ordinary limits intersected with the boss limits, ±4 px per axis when W > 256. |
| T3-B | `chaos_59_*`, `case $9771` (`SCR_chaos_aqz_boss.gml:285`) and the mode-1/2 update | `camera_left := camera` every update in modes 1–2; at the trigger `camera_right := min(camera_right, camera)` once ($0356 equivalent). |
| T3-C | `chaos_51_*` creation (`SCR_chaos_gpz_boss.gml:114`) | `camera_right = 1664 − max(0, W − 256)` instead of 1664. Pan target already uses the width-adjusted value, so pan end X becomes 1664−(W−256)−1. |
| T3-D | `chaos_eez_boss_camera_step` mode 3 (`SCR_chaos_eez_boss.gml:323`) | Remove `cp_y=min(cp_y,cp_b.bottom-1)` so the pan moves 1 px per update from the live camera Y toward `pan_y`. |
| T3-E (secondary) | `chaos_54_*`, `chaos_56_*` at creation | Wide only: `camera_right := min(camera_right, chaos_54_target_x(W) / chaos_56_target_x(W))`, same pattern as T3-C. Needed only so the 400 px retreat is 0; drop if D-T3-3's 4 px cap is accepted as sufficient at 400. |

Decisions applied: **D-T3-1** one package. **D-T3-2** no change to THZ3/MGHZ3 world coordinates; current wide exposure left as is. **D-T3-3** the 4 px wide pan cap is retained (it is what `chaos_boss_follow_step` already does).

### Numeric before / after (hold scenario; `data/p4/p4-contract.json`)

"Before" = POC-SOURCE MODEL on 03db5e1c. "After" = PROPOSAL MODEL. 256 / 348 / 400 px.

| Metric | Zone | Before | After |
|---|---|---|---|
| X retreat (px) | GPZ3 | 12 / 92 / 144 | 0 / 0 / 0 |
| | SEZ3 | 12 / 4 / 9 | 0 / 0 / 0 |
| | AQZ3 | 166 / 76 / 22 | 0 / 0 / 0 |
| | MGHZ3, EEZ3, THZ3 | 0 | 0 |
| Creation step [dx,dy] | GPZ3 | [-12,-11] / [-4,-4] / [-4,-4] | [4,0] |
| | SEZ3 | [-12,-16] / [-4,-4] / [-4,-4] | [4,0] |
| | MGHZ3 | [0,-7] / [0,-4] / [0,-4] | [4,0] |
| | AQZ3 | [-12,-19] / [-4,-4] / [-4,-4] | [4,0] |
| GPZ3 pan start camera | | [1663,146] / [1662,143] / [1662,124] | [1661,157] / [1571,157] / [1517,157] |
| GPZ3 pan end camera X | | 1663 / 1571 / 1519 | 1663 / 1571 / 1519 (unchanged; now reached without retreat) |
| AQZ3 right limit lowered before pan | | false | true |
| AQZ3 Sonic beyond clamp+4 at 256 | | 158 | 0 |
| EEZ3 max Y step in pan | | 49 / 25 / 25 | 1 / 1 / 1 |
| EEZ3 pan end camera Y | | 333 | 334 (ROM 334) |
| MGHZ3 camera rise before stop (y_up) | | 29 / 76 / 59 | 46 / 63 / 46 |

MGHZ3's rise gets longer at 256 and shorter wide because the follow is now continuous from the trigger instead of snapping at creation. The pan end and stop points are unchanged (`TestContract`). MGHZ3's remaining vertical travel is the ROM's own pan (D-T3-2), not a defect.

### EEZ3 corroboration (required by the Manager before changing the camera)

- The snap persists in the final baseline at all three widths (Y step 49 / 25 / 25).
- Camera Y before the pan (382 / 358 / 358) is always above the freshly written bottom limit 334 for a standing trigger, so the unconditional `min(cp_y, bottom−1)` is what snaps it.
- ROM pans 1 px per axis per update with no such clamp (T2 EMULATED).
- Still **Windows-unverified**; treat T3-D as the last package to land and gate it on the F5 check below.

## 3. Assignment B: S0 zone-title transition

Data: `data/p4/s0-source-findings.json`, `data/p4/s0-poc-start-fall.json`, `tools/p4_s0.py` (14 line-anchored findings, all verified at the recorded lines on 03db5e1c).

**Cause (SOURCE READING).** On the zone-title route `chaos_results_room_begin` arms `level_in` (`SCR_chaos_results.gml:24`), and then `OBJ_chaos_zone/Create_0.gml:43` still creates the legacy black `OBJ_effect_fade_in` (alpha 1, −0.05 per step, 20 steps). At the first Draw the controls capture `application_surface` and call `instance_deactivate_all(true)` (`SCR_chaos_results.gml:243`), which freezes the fade object at about alpha 0.95. The captured frame is shown through the SMS-style black / ⅓ / ⅔ steps for 19 updates, and at age 20 `instance_activate_all()` (`:198`) resumes the frozen fade object over the now-finished fade. Result: black, ⅓, ⅔, a dip to roughly 0.05 brightness, then a second fade from 0.95 to clear. That is the "level appears, flash black, reappears".

- Level Select (`SCR_chaos_debug_select.gml:73`) and Data Select (`OBJ_menu_data_select/Alarm_2.gml:3`) set no `chaosResultsIncoming`, so there is no `level_in` and no freeze: a single monotone fade-in. This matches the observation that Level Select is clean.
- Death respawn (`SCR_chaos_death.gml:43`) uses the same handoff, so the same flash is predicted after a respawn.
- **ROM vs POC-only.** ROM zone start: palette black frames 0–33, then three dim steps at 34 / 39 / 44, with gameplay running during the fade. GPZ1 and MGHZ1 start airborne (state 14, +14 px fall, floor contact at frame 39–40); THZ1 does not fall (it shows a 7 px anchor flicker under the first dim step, T2-11). The POC-SOURCE MODEL reproduces +14 px for GPZ1 and MGHZ1 and 0 for THZ1 (`s0-poc-start-fall.json`). The fall itself is ROM behaviour. What is POC-only is that gameplay is frozen for the 19 `level_in` updates, so the fall happens after the freeze under the resumed fade object rather than under black. The user's "drops a few pixels" is therefore visible; in the ROM it is hidden.

**Recommended correction (conditional on the capture below).** Guard the legacy fade at `OBJ_chaos_zone/Create_0.gml:43` with `if (!chaos_results_active())` (or the equivalent `chaosResults` check) so only one fade runs on the zone-title and respawn routes. Do not change fade timings, camera positions or spawn coordinates. A later, separate option is to let gameplay run during `level_in` (matches ROM, hides the fall); it is bigger and not needed to remove the flash.

**Single Windows capture (diagnostic, not a fix).** Build with a per-Draw logger writing `s0_entry_trace.csv` to the working directory with columns `u,room,route,results_phase,results_age,fade_exists,fade_alpha,player_y,core_state,floor,view_y,lum` for the first 90 Draw events after Room Start. Run four entries: Level Select → GPZ1, Level Select → MGHZ1, death respawn in GPZ1, zone title → GPZ1 (after THZ3). Analyse with `python tools/p4_s0.py --analyze s0_entry_trace.csv`. Confirmation: in the zone-title and respawn routes `fade_exists` goes false at update 1–2 and true at `results_age` 20 with `fade_alpha` 0.90–0.95, and `lum` drops by more than 0.25 within 2 updates of that release. Level Select routes show monotone `lum`. The analyzer has been self-tested on synthetic series for both verdicts.

## 4. Tests and Windows acceptance

Focused tests (`tests/test_p4_preflight.py`, 13 tests): THZ3 corrected and the other five identical to C1-I; persisting numbers pinned; the proposal model meets each package's rule; S0 start fall, 14 anchors, 4 routes. Re-baseline: `python tools/p4_rebaseline.py --check`.

Windows F5 acceptance, 256 and 348 required, 400 secondary:

1. GPZ3: camera never moves left from the trigger to the pan end; pan ends at X 1663 (256) / 1571 (348) / 1519 (400); boss enters from the right edge.
2. SEZ3 / MGHZ3 / AQZ3: no visible backward step or snap at the trigger; AQZ3 camera locks (Sonic cannot walk back past the trigger-time right edge).
3. EEZ3: pan start has no vertical jump; pan ends at camera Y 334.
4. THZ3: unchanged from the passed V1/T1 acceptance.
5. S0 (after the fade guard, or the capture only): zone title → GPZ1 / MGHZ1 / THZ1 shows one fade, no dip, no flash; Level Select unchanged.

## 5. Explicitly unverified

- All camera results are POC-SOURCE MODEL or PROPOSAL MODEL; none are observed in the Windows build. The proposal model is a stand-in for the code changes, not the code.
- EEZ3 snap on Windows is reasoned from source and the model only (see corroboration above).
- S0: the mechanism is established from source; the perceived order and duration of the flash are not observed. The capture is what confirms it. The respawn flash is predicted, not seen.
- AQZ3 "Sonic stuck at 2043" in the harness is unexplained (possibly a harness artefact) and was not used as evidence.
- 400 px is a secondary check only.

## Reproduction

```
POC=<03db5e1c checkout> T3_OUT=data/p4/poc-series-v1t1.json T3_WIDTHS=256x192,348x196,400x225 node tools/t3_poc_boss_run.js --check
POC=<03db5e1c checkout> T3_WIDTHS=256x192,348x196,400x225 node tools/p4_proposal_model.js --check
python tools/p4_rebaseline.py --check     python tools/p4_s0.py --check     python -m unittest tests.test_p4_preflight tests.test_t3_boss_walkon_audit
```

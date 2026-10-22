# Q2-R1 — campaign defect triage

Research-only checkpoint. POC source: `4eb684911c5785667181b9d3f940b1dc820e66d1`; Research parent: `d1253cac423a2b632874874b293fa40565eee73e`. No POC edits, compilation, diagnostics installation, new ROM execution or Windows testing. The source host executes shipped GML through the existing JavaScript adapter; it is not GameMaker.

## Decision

**One implementation-worthy discrepancy is demonstrated: Q2R1-AQZ-FACING.** Gameplay facing can remain opposite to input while the displayed sprite faces correctly. Charge preserves that stale bit and release consequently launches in the wrong world-X direction. Recommend one future bounded facing-ownership package, subject to Manager authorisation. Do not change underwater acceleration, dash speed or collision physics.

This is a reproducible low-speed braking-to-charge slice in both Aqua Planet acts, not a complete replay of Chief's fast same-direction sequence. Indefinite travel is not established. **Q2R1-SS3-MONITOR remains unresolved:** no persistent trap was reproduced. No monitor correction is proposed.

Manager reports Q1 accepted: Chief completed one continuous widescreen Sonic campaign through all 18 acts, all Emeralds, full good ending, credits and title; nine targeted smoke checks also passed. This supersedes the older absence-of-campaign-evidence statement for that scope. It does not turn the historical blank Q1 checklists into individually measured results or close these new findings. See the machine-readable receipt and issue register in [data/q2r1](../data/q2r1/).

## Evidence and reproduction

Run from this Research worktree, passing the clean accepted POC path if it differs from the default sibling `SonicChaos_POC_c2e1`:

```text
node tools/q2r1_dash.js <POC>
node tools/q2r1_ss3.js <POC>
node tools/q2r1_gate.js <POC>
node tools/q2r1_manifest.js <POC>
node tools/q2r1_validate.js <POC>
```

The dash and SS3 tools assert the exact POC HEAD and clean status before/after execution. The gate redirects verifier outputs into Research. The validation independently replays all 24 dash cases without the presentation wrapper and compares state, requested state, fixed-point position, velocity and facing each update. No runtime fix is injected. Evidence provenance hashes are recorded in `data/q2r1/register.json` by `tools/q2r1_manifest.js`.

| Evidence | Result | Limit |
|---|---|---|
| 24 dash sequences | 8 wet discrepancies, 16 controls; 48 release checks | Seeded local player state, reduced canonical facing/release oracle |
| Independent uninstrumented dash replay | All 24 identical | Same source host, not independent engine |
| SS3 cached original input route | Emerald collected after 2,090 updates at 256×192 and 348×196 | Cached input replay, not a new paired ROM execution |
| SS3 mapped upper-left approaches | 28 cases; 12 attacking cases break monitors | Player/camera seeds, not natural routes from entry |
| Existing monitor support gate | PASS: 75,805 checks, including 35,920 cached projection rows and 1,440 callback cases | Shared collision contract, not proof against every live trap |

No 256-pixel Windows test is requested. All new Windows cards target F5 at **348×196**. Source comparison widths are controls only. No full historical suite was rerun.

## Q2R1-AQZ-FACING — high confidence proven gap

### Applicable canonical contract

Recovered [dispatch_target_03783.asm](../asm/recovered/dispatch_target_03783.asm), `$3788..$3791`: shared movement runs first; if requested state remains `$05`, `$48A7` updates facing from held Left/Right. Left has priority when both are held. [standing_walk_setters.asm](../asm/recovered/standing_walk_setters.asm), `$45CE..$45E4`, also calls `$48A7` when requesting walk. These are gameplay flag writes, separate from sprite drawing.

[player_state_setters.asm](../asm/recovered/player_state_setters.asm), `$4701`, zeros horizontal velocity and requests charge `$0F` without changing facing. `$4719..$4732` reads `(IX+4)` bit 4, writes signed VX `+$0700` or `$F900` (±7 px/update), then requests `$10`. There is no underwater release alternative. Existing [water audit](aqz-water-environment-audit.md), movement table and `data/rom-cache/aqz/water-runtime.json` establish underwater walk acceleration 2 versus dry 16, doubled near zero. This explains why the stale-sign window is easier to retain underwater; it does not justify changing those canonical values.

### Current writers and first divergence

All POC references below are relative to the pinned POC commit.

Pinned source: [core](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_core/SCR_chaos_core.gml#L174), [presentation](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_visual_p1/SCR_chaos_visual_p1.gml#L81), [monitor contact](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/objects/OBJ_chaos_object_10/Step_0.gml#L46).

| Stage | POC callsite | Consequence |
|---|---|---|
| Walk request | `scripts/SCR_chaos_core/SCR_chaos_core.gml:174` (`SCR_cc_walk`) | Omits canonical walk-setter facing call |
| Walking callback tail | same file `:853` | Omits applicable `$3791` input-facing write |
| Facing helper | same file `:708` | Correct input-facing helper already exists; not applied to these walk paths |
| Presentation publication | `scripts/SCR_chaos_visual_p1/SCR_chaos_visual_p1.gml:81`, especially `:90–91` | Copies velocity sign to instance scale and back into gameplay flag; independent `visual_anim.pface` drives drawn orientation |
| Charge/release | core `:815–823` | Preserves flag during charge; release reads it to choose ±1792 |
| Adjacent ownership risks | `scripts/SCR_chaos_player_animation/SCR_chaos_player_animation.gml:80–95`, legacy core sprite path in adapter | Other velocity/scale-to-gameplay flag writers require bounded review before implementation |

The **first divergent retained result** is update 0's facing bit after the walk callback: canonical input Right requires bit 4 clear, POC retains bit 4 set. The source omission precedes the traced presentation write; the wrapper shows presentation continues publishing the velocity-derived bit. A correct-looking sprite therefore does not prove correct launch direction. The first consequential velocity divergence is release at update 5.

### Minimal failing sequence

Actual unchanged AQZ1 terrain at player anchor `(1680,654)` or AQZ2 `(1136,814)`. Seed executing/requested walk `$05`, grounded, VX = −16 fixed-point units (−1/16 px/update), facing left, no support owner. This is a **player-state seed**, not a claimed natural starting route or object placement. No map/object edits. Mirror signs/inputs for the opposite direction.

| Update | Input | Executing → requested (decimal) | Actual VX | Expected retained face / release |
|---|---|---|---:|---|
| 0 | Right | 5 → 5 | −12 | Right; actual gameplay bit remains left while draw faces right |
| 1 | Down | 5 → 1 | 0 | Right preserved |
| 2 | Down | 1 → 4 | 0 | Right preserved |
| 3 | Down + fresh Space | 4 → 15 | 0 | Right preserved |
| 4 | Down | 15 → 15 | 0 | Right preserved |
| 5 | Release Down, hold Right | 15 → 16 | **−1792** | **+1792** |

`dash-traces.json.gz` records full fractional X/Y, current/requested state, VX/VY, input, gameplay/instance/draw facing, terrain contact/modifier/surface delta, water and support, plus before/after presentation writes. Wrong direction persists into later world-X integration; this is not only alternating animation. No claim that it persists forever.

Controls: both initial signs × both intended directions, both acts, widths 256/348; a genuine dry THZ1 flat-map control at `(160,654)` rather than an overwritten AQZ water flag. Same-sign wet releases match. Opposite-sign dry releases match because dry acceleration crosses zero sooner. Dry control is a different level, not a paired wet/dry edit of one map. All decisive terrain modifiers and retained surface deltas are zero; no carrier, slope or water crossing is needed. Skimming's established `$4BC0` VY rule is not the first divergent write. These controls do not exclude additional defects elsewhere.

### One proposed Designer package

Restore canonical input-facing ownership at the proven walk callback and walk setter; prevent presentation/legacy scale publication from undoing gameplay facing. Preserve state-specific canonical facing rules rather than applying input facing globally. Audit only directly related strip/fallback publication paths. Keep charge/release speeds, water acceleration, braking tables, skimming, maps and terrain handling unchanged.

Regression risks: Peel-Out/Spin Dash/airborne and strip facing, neutral input, simultaneous directions, fallback frames, shoe/camera readers and animation orientation. Required gates: wet/dry both directions and widths in source tests, current/pending charge states, neutral/both-direction controls, then Chief's exact fast underwater sequences in both acts at 348×196. This report proposes no patch and does not authorise implementation. Confidence is high for the narrower discrepancy, partial for attribution of Chief's full observation.

## Q2R1-SS3-MONITOR — unresolved

Chief clarified **upper-left impact, standing about 10% below the monitor's top**, not “top 10% of the stage.” Which monitor, incoming state, buttons and escape attempts remain unknown.

### Placement and ownership

Canonical census `data/rom-cache/special-stages/object-census.json`, SS3 type `$10`, parameter `$06`: seven invincibility monitors at `(240,622)`, `(912,622)`, `(1584,622)`, `(2256,622)`, `(2928,622)`, `(2800,366)` and `(3696,622)`. Individual decoded record indices/CPU addresses are retained in the trace. No enemy shares the SS3 census. No monitor was relocated.

Shared `objects/OBJ_chaos_object_10/Step_0.gml:46–68` owns collision: integer player extents 8×24 (charge width9), object 10×24; minimum penetration, vertical tie; terrain/camera guards can suppress projection. Projection retains fractions. Mirrored object contact is staged for the next player's terrain merge. It does not immediately zero velocity or force standing. Attack posture bit1 is required to break a monitor; invincibility alone is insufficient. Top contact excludes requested charge/dash/spring/Peel-Out states; downward speed and roll state alter the bounce callback (`:72` onward).

Applicable original rules: recovered `$6328` overlap (`asm/recovered/object_player_overlap.asm`), `$5FA0` projection, `$D521/$D523` staging and callback cache in POC `verification/monitor-support-fixtures.json`; see [player-fall-control-audit.md §2](player-fall-control-audit.md). Its old “POC divergence” summary describes an earlier POC; current source and the cached verifier already include those corrections. Do not reopen that historical defect as a new Q2 finding.

### Focused results and visual distinction

The cached original input route naturally breaks the five lower tube-mouth monitors and completes at both widths. It does not exercise every upper-left approach. Local fixtures approach **all seven real monitors** from `(monitorX−21,monitorY−29)`, VX+1/VY+2, ordinary fall or attacking jump; Right20, Left20, Right+jump20 updates. These player/camera seeds are explicitly not natural routes. Six monitors receive contact in each attack mode/width; the final monitor's approach is intercepted by existing geometry. Twelve attacking fixtures break their monitors. The nonattack contacted fixtures slide down the side and can escape with the chosen inputs; no persistent standing-in-side trap is demonstrated.

Example first monitor at348: update2 integer projection leaves player `(222.375,600.125)`, side contact8; next update stops horizontal motion through merged contact, then slides to the floor, later jumps away. A fractional residue after integer projection is canonical-supported and is not itself a 10% embedding defect.

Presentation metadata provides a hypothesis, **not a finding**: `SCR_chaos_render_adapter.gml:9` uses accepted Y offset18; monitor frame `$06` bbox top4/bottom35, originY28. Its registered top is monitorY−6, matching the player's feet (anchor+18) at logical top support monitorY−24. Art extends 2 pixels beyond the logical side. No rendered ROM/Windows paired image was captured; neither layer priority nor this art margin explains Chief's persistent standing report on current evidence. The front-terrain draw object also exists, but no layering discrepancy is proven. Viewport side guards are intentional adapters; width-paired completion does not prove all contact locations equivalent.

No first divergent collision event has been established. Keep OPEN; collect exact monitor and approach before expanding the matrix or proposing correction.

## Adjacent triage and deferrals

| ID | Evidence and disposition |
|---|---|
| Q2R1-SS3-JUNCTION | Established original SS3 `$7A` branch at world cell `(3296,352)`, decision near `(3306,364)`: **held Up** selects the Emerald route. `SCR_chaos_eez.gml:38–77` reads `held`, alignment and first-decision latch, not a fresh press. See special-stages-followup-audit §3 and traversal audit. Particular human failure untraced; OPEN, no shared facing cause shown. |
| Q2R1-SS5-DOWN | Same shared router uses held Down for `$7B`; latch prevents late rerouting in the same cell. Existing `verification/verify_ss5_play.js` documents cached original 1,424 player updates, 16 lag frames and 1,426 harness frames; original-route input timing is not interchangeable with display timing. No new SS5 run; reported timing discrepancy OPEN. |
| Q2R1-REBOUND | Monitor callback state/attack/vertical speed exclusions above are established, not proof of a cross-zone bug. Badniks have separate callbacks. No identical first divergent event or common cause with AQZ facing established. OPEN separate bounded impact-position/state comparison. |
| Q2R1-BOSS1-RIGHT | Zone/encounter unresolved. Obtain identification before comparing boss/camera contract. OPEN. |
| Q2R1-GOAL-CENTER | Human off-centre sign report; world placement versus camera/art not paired. OPEN presentation investigation. |
| Q2R1-BREAKABLE-ANIM | Outside-THZ animations reported incomplete; accepted THZ2 shard scope is narrower. Identify zone/block before classification. OPEN. |
| Q2R1-SLZ1-PRIORITY | User label SLZ1 is not resolved to a canonical zone; do not silently substitute Sleeping Egg. OPEN. |
| Q2R1-CARD-COMPOSITION | Zone title/results widescreen composition reported; defer paired presentation review. OPEN. |
| Q2R1-CONTINUES | Unusually many continues reported. Adapter `chaos_continue_add_binary`, score threshold and Special Stage award paths exist; no actual award ledger/score totals supplied, so no excess-award claim. OPEN. |
| PRES-ENTRY-MGHZ3 | Carry existing spike-pit/tree camera reveal presentation discrepancy unchanged; no correction here. OPEN. |

Historical oscillation/slope sticking, diagonal spikes, state-$20 lag and C2R3 activation-phase uncertainty remain OPEN under their earlier evidence. None automatically invalidates accepted campaign progression. No broad cross-zone rebound or collision investigation was added.

## Remaining limits and next milestone

Only cached ROM-derived assembly/data/traces were used. No fresh original ROM access/execution is claimed. Models do not capture GameMaker rendering, key sampling, frame timing or live Windows camera output. The dash oracle covers applicable facing/release writes, not the entire ROM state machine. SS3 natural replay is an input-only success control, not an original-vs-POC per-update equivalence proof. Local approach fixtures do not establish natural reachability from stage entry.

Manager may authorise the single bounded facing package above, followed by Chief's underwater checks. Keep SS3 open pending the observation card. Remaining adjacent findings should receive separately bounded triage only after precise encounter evidence. No further implementation or investigation is self-authorised by this checkpoint. Stop for Manager review.

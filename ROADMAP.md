# Sonic Chaos — ROADMAP
**Live plan · 2 November 2026 · Owner: Chief / coordination: Manager-san #8**

This is the **current plan**, deliberately rewritten after seven prior Manager handovers. **No earlier “NEXT/GO/HOLD” instruction is active merely because it appears in an archived report.** Operating rules: [AGENTS.md](AGENTS.md). Short state: [MEMORY.md](MEMORY.md). Owner-led issues: [base completion register](docs/CURRENT_BASE_GAME_REMAINING_20261101.md). [Full pre-rewrite roadmap preserved at immutable revision](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md).

## Project target

A personally playable, original-faithful **Master System Sonic Chaos GameMaker remake** with authentic Sonic/Tails campaigns, five Special Stages, native soundtrack and PC widescreen (348×196) that does not introduce unfair behaviour. Source-ROM comparison remains 256×192. Chief decides when the base is finished; public release/port/graphics upgrade is **not** implied.

## Milestone ledger — accepted work

| Milestone | Chief status | Outcome |
| --- | --- | --- |
| M0–M2 / Special Stages and gameplay | **Accepted in prior scoped tests** | Both Sonic/Tails campaigns, zones, Special Stages 1–5, boss/level progression and endings. The historical M2 exceptions remain documented. |
| M3 frontend / M4 original audio pilot | **Accepted** | Title, original opening/choice, menus, stage entries, native audio foundation; original idle attract/demo deferred. |
| **M5-G2 full known-use soundtrack** | **Chief accepted** | 25/25 original known-use music routes, default native audio, original F2 catalogue and transitions; five truly empty songs, unused $8E and unvisited natural SFX cases documented. |
| **M6-C2 opening border** | **Chief accepted** `3cf37924…` | Robotnik enters/leaves **behind** the foreground black bars. |
| **M6-D original km/h / no dev shortcuts** | **Chief accepted** `7acdd39f…` | Rolling original $19 panel, time1:50/rings28→617 km/h, all developer keyboard shortcuts removed; Pause Level Select and menu Sound Test retained. |
| **M6-E character select widescreen** | **Chief accepted** `a4c26e13bc323a9f736c613c279b447dd6aedef5` | Original checker fills 348×196 without stretching; 256x192 art, animation and music unchanged. |
| M6-A / M6-B / M6-C audits | **Reviewed, no further code justified for their respective historical scopes** | MGHZ3 wide visual roughness retained as parked owner concern; old contact/SEZ/SS3 and palette reports have no current reproducible blocker. |
| **M6-F-R1 offscreen persistence** | **CHIEF ACCEPTED** `636ed72be111bc3de4c297e5768c40c8f38a54e6` | GPZ3 scattered-ring recovery and THZ2 triggered bee identity/patrol continuity both passed Chief F5; preserve current PC-widescreen bounded policy. |

**Accepted POC production parent:** `636ed72be111bc3de4c297e5768c40c8f38a54e6` (M6-F-R1, Chief F5 accepted). All new production work branches from R1. No POC main merge permitted without Chief instruction.

## NOW — M6-G: Manager GO; one Chief F5 pending

**One consolidated private source candidate is ready**: `SonicChaos_POC:poc/m6g-all-enemy-persistence@6e2ffcc1f333c5cdaa0048ac696b55c4f6308905`, exact one commit beyond Chief-accepted **R1 `636ed72be111bc3de4c297e5768c40c8f38a54e6`**. Four production scripts changed, 1,314 resources and 38 IncludedFiles preserved per integrity evidence. **NOT yet Chief accepted**, no main merge. [Manager review](docs/m6g-manager-review-chief-f5-gate-20261102.md) and [original directive](docs/m6g-regular-enemy-persistence-chief-directive-20261102.md).

The machine-readable census covers **95 placements across seven regular numeric types**; excludes slot-coupled hazards, emitters, bosses/projectiles and other non-regular actors. **Five types** have targeted source changes: THZ/MGHZ `$21`, GPZ `$25`, SEZ `$20/$23`, AQZ `$3D`; flying `$27/$2C` R1 behaviour remains unchanged. Wide `348×196` awakened patrols **sleep rather than reset** across camera-Y departure within a finite **±512px horizontal** envelope. GPZ `$25` separately restores original **no sleep gate** on callbacks at both widths, with an original blank initializer pass and bounded below-map retirement. Do not mislabel GPZ native256 fidelity correction as byte-identical to R1 or the new 348-only vertical policy as original SMS.

**Verification:** 19 PASS / **2 raw FAIL preserved**: the inherited all-width384 viewport assertion and the M6-G-superseded wide-Y SEZ deletion expectation; separate policy-aware checks PASS. 760 policy cases, 20 grounded terrain routes and original-Z80 comparisons were executed. Existing `$21` falling/asleep discrepancy and GPZ1 below-map token18 remain explicit historic limits, not silently resolved.

**ONE Chief F5 of private `SonicChaos_M6G_20261102_A_PRIVATE.zip`:**
1. **THZ patroller**: watch reversal, depart vertically, return; same encounter and direction/phase; asleep motion may genuinely pause.
2. **GPZ `$25` patroller**: moderate backtrack then return, optionally vertical departure; movement should progress offscreen per original, without restarting.
3. **SEZ `$20` hopper**: watch a hop, depart/return; same hop/patrol state, not origin reset; sleep may pause callbacks.

No new build or per-enemy human test. Do **not** repeat previously Chief-accepted GPZ3 rings, THZ2 bee, audio/menus/km/h or full campaign. If all three PASS, promote M6-G SHA and proceed to Chief's full base playthrough **before enhancements**. If any FAIL, fix exact symptom in one focused integrated revision. No automatic POC main merge.

## NEXT — base-finish phase, before enhancements

1. **Owner's remaining observations:** Chief may identify one or two more concrete base-game issues. Record them as current observations; no automatic 93-issue sweep.
2. **One full normal playthrough by Chief** **BEFORE** enhancements. Exercise ordinary progression as preferred, watch for gameplay fairness, resource stability, music transitions and visible widescreen problems; collect a short consolidated punch list rather than stopping after every act. Do not require another six-stage technical test package solely to watch already-accepted systems.
3. **Single finish decision:** fix only reproduced substantial issues that emerge; decide which explicitly parked polish (MGHZ3 entrance wide roughness, one-time startup onset) matters to Chief. Old frontend attract demos and save/resume are **POST-BASE** by Chief's current decision. AQZ Tails palette provisionally satisfactory.
4. **Base checkpoint:** Chief explicitly approves baseline; verify source+private assets, one reproducible GameMaker `.yyp`, clean branch/source SHA, manifest+SHA256, known original fidelity/QoL deviations, open technical exceptions, restoration/launch proof. Freeze without automatically merging main or publishing third-party material.

The **current human gate** is a SINGLE Chief F5 on the Manager-approved M6-G candidate: THZ/GPZ ground patrol persistence and SEZ walker/hopper. M6-G is **not yet Chief accepted**; last fully accepted source remains R1. The planned full base-game playthrough follows Chief acceptance. New issues from the full playthrough can change the list.

## AFTER BASE — optional enhancement research, not yet implementation approval

**AM-san** prepared a useful sequence; decide priorities after Chief's complete playthrough, and protect a reversible “Classic” baseline:

| Optional programme | Initial investigation | Constraints / gate |
| --- | --- | --- |
| **E1 — Higher frame-rate presentation** | Confirm actual GameMaker `option_game_speed:30`, real Step/animation/update ownership, fixed audio60Hz clock, renderer cadence. Pilot **60-FPS rendered/interpolated presentation with canonical30Hz gameplay simulation** first, compare 30-FPS Classic. | Simply setting game speed to60 will accelerate time-based physics, object AI, timing, attacks and animations. True60-Hz gameplay requires explicit normalization and separate engineering; don't promise it as a toggle. |
| **E2 — Graphics and presentation** | Keep native pixel sprites. Compare nearest pixel-perfect versus optional sharp-bilinear, and only later bounded xBRZ/ScaleFX experiments, original/enhanced palette presets, optional high-resolution particles/lighting. | Preserve exact source pixel positions and 348-wide camera/occlusion; upscalers must not smudge/replace original art or alter collisions. No compulsory AI-restyled sprites. |
| **E3 — Windows options and comfort** | Optional performance, controls/display settings, archival source packaging. | No obligatory save system just because modern Sonic games have one. |
| **E4 — Optional full original attract demos** | Three original demo sequences (THZ1 Sonic, GPZ1 Tails, SEZ1 Sonic), proper input-replay evidence. | Explicitly **parked until after base**; original replay is not a trivial input-pair copy. |
| **E5 — Optional save/emerald progression** | Chief's Sonic 3-like persistent emerald progress and Level Select unlock idea. | **Parked post-base**, since Sonic Chaos is short. No change to currently open Pause Level Select without approval. |

Enhancement order is a **proposal** (60-FPS proof → scaler → palette/effects), not an authorization to implement all items. Each pilot should have independent original-frame/feel criteria and one meaningful Chief comparison, with few expensive native builds.

## LATER — Vita port and separate preservation projects

- **Vita**: begin feasibility after the base is frozen, preferably after performance choices are understood. AM-san's earlier compatibility audit called modern GMS-to-Vita **amber-green**: first investigate latest YoYo Loader compatibility and constraints; if unsuitable, consider native VitaSDK/vitaGL adaptation. **GMS1.4/GayMaker backport is a high-maintenance fallback**, not default. Preserve native-resolution art and widescreen camera; benchmark performance honestly and never claim 60 FPS on Vita without measurements.
- **Separate side projects**: complete accessible ROM disassembly/decomp, SMS/GG slowdown-reduction patch. These are not POC completion gates; request new owner authorization before work.

## Workspace closure / archiving — new solution needed

**Detailed dry-run/backup/restore protocol:** [WORKSPACE_ARCHIVE_STRATEGY](docs/WORKSPACE_ARCHIVE_STRATEGY.md). No local files are touched by documentation maintenance.



Chief reports ~**170 folders** across worktrees/archives. **No Janitor-san**. Use a combined Codex audit and Manager review when the base freeze is ready:
1. Read-only inventory of full local paths, sizes, `git worktree list --porcelain`, branch/commit/dirty/untracked status, resource/private-asset manifests, final ZIP receipts.
2. Classify **canonical current**, **historical reproducible**, **research evidence**, **generated and safely recreatable**, **unknown/keep**. Prefer a **small approved archive set** rather than 170 indistinguishable folders, but assume unknown local data is important.
3. Verify separate reliable backup **and** restoration of accepted final source/required assets. Produce dry-run actions; Chief signs off each disposal class.
4. Only then remove registered worktrees safely with Git commands or archive old revisions; **never mass-delete, run blanket `git clean -fdx`, move registered worktrees in Explorer, or destroy private data**.

Public research repository keeps safe documentation. Private build payloads and copyrighted content remain outside public distribution; no automatic GitHub visibility or main-merge changes.

## Authority and change management

**Team now:** Chief; Manager-san #8; AM-san; **one combined Research/Designer Codex agent**. Cloud-kun and Janitor-san departed; the separate Claude Research/Designer works elsewhere.

**Docs policy:** Edit this roadmap **in place**; record accepted SHA and Chief approval once. Keep a concise [current issue ledger](docs/CURRENT_BASE_GAME_REMAINING_20261101.md), [agent operating contract](AGENTS.md), and [short memory](MEMORY.md). Historical full-roadmap version at [immutable Git snapshot](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md). Do not append old “CURRENT” reports forever.

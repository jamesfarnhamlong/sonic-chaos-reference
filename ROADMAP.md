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
| **M6-F-R1 offscreen persistence correction** | **MANAGER GO; Chief THZ2 F5 PENDING** `636ed72be111bc3de4c297e5768c40c8f38a54e6` | M6-F GPZ3 rings Chief PASS preserved. Corrected triggered THZ2 bee vertical identity/phase, source-host compared to original; actual THZ2 drop/spring and below-right follow still need one Chief F5. |

**Accepted POC production parent:** `a4c26e13bc323a9f736c613c279b447dd6aedef5` until Chief accepts M6-F. No POC main merge permitted without Chief instruction.

## NOW — M6-F-R1: Manager GO for one Chief THZ2 acceptance

**Why this corrective candidate exists:** M6-F **GPZ3 off-top ring recovery CHIEF PASS**; ordinary-enemy continuity **CHIEF FAIL** in THZ2. R1 `SonicChaos_POC:poc/m6f-r1-bee-vertical-retention@636ed72be111bc3de4c297e5768c40c8f38a54e6` is one direct commit after partial M6-F, exact pushed SHA verified, with **one production file changed**. The GPZ3 ring code is byte-identical.

**Source proof:** earlier bee placement31 THZ2 (X1152/Y640) was retired at controlled update185 and recreated197 when camera Y departed. Original type$27 keeps triggered bit1 identity across vertical offscreen sleep; state2/3 oscillator continues, state3 has X-only player384 native deletion. R1 returns sleep/hidden cell2 instead of deletion3 outside vertical band and preserves existing finite PC-widescreen **horizontal ±512** departure. Native256, pretrigger, other enemy types, boss/hazard/projectile/graphics unchanged. **197 focused /40,332 original-Z80** assertions, 9 PASS and one inherited all-width384 raw FAIL honestly retained; 15,750 M6-F and879,757 lost-ring internal regressions passed. Source-host, **not** native GameMaker proof. [Full Manager review](docs/m6fr1-manager-review-chief-gate-20261102.md).

**Single Chief F5 in full private `SonicChaos_M6FR1_20261102_A_PRIVATE.zip`:** (A) THZ2 earlier bee above twin columns: activate, descend between columns, spring back, bee retains evolved identity/patrol rather than resetting; (B) follow bee right from below, depart/return, encounter remains progressed. **No repeat GPZ3 rings, soundtrack, frontend or full campaign**. If both PASS, mark R1 Chief accepted, promote SHA as production checkpoint and proceed with Chief's planned full playthrough. If FAIL, precise natural symptom only; repair narrowly in one integrated candidate. No main merge.

## NEXT — base-finish phase, before enhancements

1. **Owner's remaining observations:** Chief may identify one or two more concrete base-game issues. Record them as current observations; no automatic 93-issue sweep.
2. **One full normal playthrough by Chief** **BEFORE** enhancements. Exercise ordinary progression as preferred, watch for gameplay fairness, resource stability, music transitions and visible widescreen problems; collect a short consolidated punch list rather than stopping after every act. Do not require another six-stage technical test package solely to watch already-accepted systems.
3. **Single finish decision:** fix only reproduced substantial issues that emerge; decide which explicitly parked polish (MGHZ3 entrance wide roughness, one-time startup onset) matters to Chief. Old frontend attract demos and save/resume are **POST-BASE** by Chief's current decision. AQZ Tails palette provisionally satisfactory.
4. **Base checkpoint:** Chief explicitly approves baseline; verify source+private assets, one reproducible GameMaker `.yyp`, clean branch/source SHA, manifest+SHA256, known original fidelity/QoL deviations, open technical exceptions, restoration/launch proof. Freeze without automatically merging main or publishing third-party material.

The **only mandatory currently pending gate** is **M6-F-R1's two THZ2 bee scenarios in one Chief F5**. Source candidate Manager GO; rings already Chief PASS and protected. Full playthrough only after the integrated correction passes. New issues from the full playthrough can change the list.

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

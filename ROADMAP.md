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
| **M6-F offscreen persistence** | **SPLIT Chief F5: rings PASS / enemies FAIL** `70cac5dea79e5e81fb88513effec367cb1af4d0c` | GPZ3 high-Y recoverable rings now work; THZ2 bee resets upon vertical drop/spring-up or following its rightward path from below. M6-F overall HOLD. |

**Accepted POC production parent:** `a4c26e13bc323a9f736c613c279b447dd6aedef5` until Chief accepts M6-F. No POC main merge permitted without Chief instruction.

## NOW — M6-F-R1: finish enemy persistence without disturbing passing rings

**Chief's 2 Nov F5:** high-Y GPZ3 lost-ring return **PASS**; enemy continuity **FAIL**, with two reproducible **THZ2 bee** cases: (a) triggered bee above twin columns resets after player falls between columns then springs back up; (b) following bee right while below then departing/returning also recreates it at origin. No repeat GPZ3 ring human test.

**Probable source cause:** M6-F introduced a 128px camera-Y retention cutoff for already-awake wide flying enemies. Original type$27 sets keep-alive bit1 after player proximity trigger; post-trigger generic offscreen check does not delete it, and later state3 removal uses **player-relative horizontal X separation >=384**, not vertical camera distance. Current wide type$27 post-update cell3 may retire even state2/3 after vertical camera departure. Prove first failing THZ2 update/identity against ROM before changing policy; preserve original sleep semantics and finite memory policy.

**Corrective assignment:** branch `poc/m6f-r1-bee-vertical-retention` from **M6-F candidate** `70cac5dea79e5e81fb88513effec367cb1af4d0c` (not M6-E; keep Chief-passed ring code). One combined agent researches original THZ2 generated$27 route, corrects triggered bee identity/oscillator/state across Y movement, tests THZ1/THZ2 and GPZ/EEZ aliases, preserves native256 and all approved M6-E/M6-D/M6-C2/audio code. Cheap tests during development, one integrated final regression, **one private source ZIP/one short Chief THZ2 F5**. No Runner error623 loop or per-bee microbuilds.

**Detailed source and owner verdict:** [M6-F Chief split result + R1 mandate](docs/m6f-chief-thz2-bee-failure-20261102.md).

## NEXT — base-finish phase, before enhancements

1. **Owner's remaining observations:** Chief may identify one or two more concrete base-game issues. Record them as current observations; no automatic 93-issue sweep.
2. **One full normal playthrough by Chief** **BEFORE** enhancements. Exercise ordinary progression as preferred, watch for gameplay fairness, resource stability, music transitions and visible widescreen problems; collect a short consolidated punch list rather than stopping after every act. Do not require another six-stage technical test package solely to watch already-accepted systems.
3. **Single finish decision:** fix only reproduced substantial issues that emerge; decide which explicitly parked polish (MGHZ3 entrance wide roughness, one-time startup onset) matters to Chief. Old frontend attract demos and save/resume are **POST-BASE** by Chief's current decision. AQZ Tails palette provisionally satisfactory.
4. **Base checkpoint:** Chief explicitly approves baseline; verify source+private assets, one reproducible GameMaker `.yyp`, clean branch/source SHA, manifest+SHA256, known original fidelity/QoL deviations, open technical exceptions, restoration/launch proof. Freeze without automatically merging main or publishing third-party material.

The **only mandatory currently pending gate** is corrected M6-F-R1 **THZ2 bee persistence** Chief-native acceptance; M6-F rings already passed and must remain protected. New issues from the full playthrough can change the list.

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

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
| M6-A / M6-B / M6-C audits | **Historical reviews** | M6-A's MGHZ3 no-code close is now superseded by a **new exact Chief spike/tree reveal defect**, assigned to M6-H; old contact/SEZ/SS3/palette reports still inactive without new evidence. |
| **M6-F-R1 offscreen persistence** | **CHIEF ACCEPTED** `636ed72be111bc3de4c297e5768c40c8f38a54e6` | GPZ3 scattered-ring recovery and THZ2 triggered bee identity/patrol continuity both passed Chief F5; preserve current PC-widescreen bounded policy. |
| **M6-G regular-enemy retention** | **CHIEF ACCEPTED** `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905` | THZ patrol vertical return, GPZ patrol backtracking and SEZ `$20` hopper return passed owner F5; five types received source changes, two flying aliases remain unchanged. |

**Accepted POC production parent:** `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905` (M6-G, Chief F5 accepted all three planned checks). All future production work branches from accepted M6-G. No POC main merge permitted without Chief instruction.

## NOW — M6-H MGHZ3 spike-gated boss reveal correction

**New Chief evidence (2 Nov): `MGHZ-007` is REOPENED as a concrete visual-sequencing defect.** Accepted M6-G pre-reveal camera locks too far right: its 348px view includes first four spikes **and the central striped tree**, so boss `$56` visibly pops beside a previously exposed tree. Chief's stretched original reference has the first right lock **between spikes #3/#4**, before the tree, then authentic HUD/camera pan reveals spikes4–8, tree and boss and sets the full arena. The **left** camera limit prevents backtracking; it is not the initial right framing mechanism. Original Y and boss vertical pose derive from ROM, not resized screenshot pixels.

**Source cause to verify:** accepted GML `chaos_56_camera_step()` in modes0/1 prematurely limits `camera_right` to `chaos_56_target_x(W)=3269-(W-48)`, i.e. camera X2969 at W348 / visible world RIGHT3317, already beyond static central tree near world3264. This is **final arena framing** reused for the **pre-reveal** lock. The proper earlier right edge must be found from actual eight spike WORLD tiles and original camera D174/D280/D282 state. ROM type `$56` stays at WORLD(3269,288), source pan 256→(3060,256) and 348 combat target2968, preserving original collision/music/trigger, camera Y and 11-hit combat. No guessed world-pixel constant from video.

**Authorized M6-H production branch:** `poc/m6h-mghz3-spike-gated-reveal` **from Chief-accepted M6-G** `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905`. Combined Codex Research/Designer researches the canonical spike strip and original state0/1/2 camera trace, proves current GML pre-reveal discrepancy, then implements **a separate early right-edge camera cap** with authentic source-supported handoff to pan. Crucially, **boss must still be created and triggered offscreen** in its canonical outer spawn band before reveal. Preserve left-backtrack limit and pixel/tick source-256 control; do not move tree/spikes/boss or invent visibility masks/timers. Internal original-ROM and shipped-GML 256/348 scenario traces plus selected MGHZ boss/clear/AQZ1 and inherited regression/integrity once; **ONE private source ZIP and ONE Chief F5 only when coherent**. No Runner error623 investigation.

**Chief's final visual acceptance:** stand at first spike trap with tree fully hidden at lock between spikes3/4; as camera advances, remaining spikes and tree appear with boss already attached/moving on pole; full combat arena reveals through spike8, right/left constraints work, Sonic can fight and exit to AQZ1. A human can judge this in one normal Sonic MGHZ3 visit. No repeat M6-G enemies, GPZ3 rings, 63 sounds or other accepted features.

[Full binding M6-H directive](docs/m6h-mghz3-spike-gated-boss-reveal-20261102.md). **Previous M6-A no-code closure is historical/superseded by this precise Chief reproduction**; do not treat it as STOP.

## NEXT — base-finish phase, before enhancements

1. **Owner's remaining observations:** Chief may identify one or two more concrete base-game issues. Record them as current observations; no automatic 93-issue sweep.
2. **One full normal playthrough by Chief** **BEFORE** enhancements. Exercise ordinary progression as preferred, watch for gameplay fairness, resource stability, music transitions and visible widescreen problems; collect a short consolidated punch list rather than stopping after every act. Do not require another six-stage technical test package solely to watch already-accepted systems.
3. **Single finish decision:** after the focused M6-H MGHZ3 correction and Chief's resumed full playthrough, fix only newly reproduced substantial issues; the one-time startup audio delay remains optional parked polish. Original attract demos and save/resume are **POST-BASE** by Chief's choice. AQZ Tails palette provisionally satisfactory.
4. **Base checkpoint:** Chief explicitly approves baseline; verify source+private assets, one reproducible GameMaker `.yyp`, clean branch/source SHA, manifest+SHA256, known original fidelity/QoL deviations, open technical exceptions, restoration/launch proof. Freeze without automatically merging main or publishing third-party material.

**Current gate:** M6-H is an **authorized in-development** MGHZ3 widescreen camera-reveal correction, not yet packaged or Chief accepted. Last playable accepted source M6-G. When M6-H passes one normal MGHZ3 owner test, resume full playthrough, then private base freeze before enhancements. No automatic POC main merge.

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

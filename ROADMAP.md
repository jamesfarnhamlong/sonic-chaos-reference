# Sonic Chaos — ROADMAP
**Live plan · 2 November 2026 · Owner: Chief / coordination: Manager-san #9**

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
| **M6-H MGHZ3 boss spike-gated reveal** | **CHIEF F5 ACCEPTED 2 NOV** · private source commit pending | Initial camera boundary now between spike3/4, tree hidden; subsequent pan reveals tree, Robotnik and complete eight-spike trap; boss/AQZ1 accepted with no notes. [Owner receipt](docs/m6h-chief-acceptance-and-base-status-20261102.md). |

**Verified Git update (2 Nov):** The exact M6-H production implementation is now committed on `poc/m6h-mghz3-spike-gated-reveal` at `c3e40a7a3d6c17be3e17d7c1eb729b2a705a3089` (parent M6-G `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905`); two subsequent documentation/verification commits put the branch at `64a5a53ceebed43ed79e36a681a27b0d6a0c16aa`. Git comparison confirms three commits ahead of M6-G and none behind. This corrects the earlier uncommitted-source statement. Packaging Candidate B reportedly smoke-PASS, but its file inventory, clean project naming and local folder cleanup have not been demonstrated. Source `options_windows_executable_name` remains `SonicChaos_A4B_EXPERIMENTAL.exe`; project `name` remains experimental. Do not create further candidate worktrees until existing ones are accounted for.

## NOW — M6-H ACCEPTED; finish the base game

**M6-H / MGHZ-007: CHIEF F5 PASS, CLOSED (2 November 2026).** Chief's exact response: **"Yes, perfect! No notes, thats now working as intended."** The initial 348-wide camera stops between the body of spikes3/4 (right world edge3256, central tree not yet visible); the original boss at (3269,288) and full eight-spike arena are exposed through the original HUD/pan handoff. Final 348 cameraX2980 shows the authored second bank through world3328. The original256 camera and wide pan speed remain preserved. One production script changed; 1,314 resources retained. Source gate: 12 PASS / four documented raw FAIL due to historical framing, inherited M4 harness, obsolete G2 asset index. [M6-H acceptance, technical and publication notes](docs/m6h-chief-acceptance-and-base-status-20261102.md). **Do not reopen M6-H or commission another MGHZ3 correction.**

**M6-H source publication DONE:** Production commit `c3e40a7a3d6c17be3e17d7c1eb729b2a705a3089`, branch HEAD `64a5a53ceebed43ed79e36a681a27b0d6a0c16aa`. Chief-accepted M6-H private ZIP remains the playable control. Packaging/cleanup work must not alter the accepted gameplay or create more untracked candidate folders without necessity. Source naming and Windows metadata are not yet cleaned in this branch.

**New Chief-reported gameplay issue: `$A7` distant spike sound repeating; root cause unverified.** The agreed base-game feature set is in place within accepted scoped evidence. That does **not** claim an uninterrupted normal 18-act run has already been completed since the latest changes or prove every rare audio/ROM state.

### Next owner gate — one normal full playthrough

1. **Chief resumes/completes the base game** under normal progression, watching generally for unfairness, progression issues, music breaks, camera presentation and stability. Capture only newly reproduced substantial issues in one short punch list, not a 93-row audit and not per-feature repeat checks.
2. **If a new blocker emerges**, batch only concrete regressions; protect accepted audio, rings, enemies, opening/results and MGHZ3. If none, no further production work is needed before freeze.
3. **Chief decides private base freeze.** Establish one exact, reproducible `.yyp` + required private assets, committed source SHA, ZIP/manifest/SHA-256, clean source branch, independent backup and one restore/open proof. Document native256 parity controls versus bounded 348-wide QoL, raw test exceptions, natural SFX limits and deferred optional features. No automatic main merge or public distribution.

**Current gate:** **Owner full playthrough and controlled final packaging/deletion inventory**, not another development milestone. Only after Chief base-freeze approval can optional enhancement pilots be authorized. The one-time startup audio onset delay, AQZ Tails palette, original attract demos and save/emerald upgrades remain explicitly parked.

**Cleanup Batch 1 (Manager-reviewed, Chief exact-path approval pending):** Designer's read-only inventory identifies **seven exact E: paths totaling 2,179,106,838 logical bytes (~2.18 GB)**: three generated/extracted package directories and four clean, backed-up historical Git worktrees. The `build\export-b` nested directory is already inside its parent count; the additional H: `source-restore-check-b` is not in this batch. Active `SonicChaos_Production` packaging worktree and the E:/H: packaging receipts are KEEP. Larger 14.425 GB proposal remains unapproved. [Exact path manifest and guards](docs/sonic-chaos-final-packaging-and-deletion-plan-20261102.md). **No deletions performed or authorized for execution until Chief approves these seven exact targets.**

**Gameplay regression now open — `PROD-AUDIO-A7-REPEAT`:** Chief reports repeated spike SFX `$A7` on crossing spike X despite very large Y separation. Suspected persistence-policy link is unproven. Keep gameplay/audio investigation separate from Candidate B's accepted packaging smoke. **Do not declare private base freeze until assessed.**

## New owner instruction — production naming, distribution and permanent cleanup

Chief confirms the final workspace size **133 GB, 2,929,194 files, 1,268,255 folders**, and requests **permanent deletion of proven redundancy**, not indiscriminate archiving. The accepted candidate EXE has `SonicChaos_A4B_EXPERIMENTAL.exe`; source options already display `Sonic Chaos` but configure that old EXE filename and placeholder Windows company/description metadata. Some sidecars (`data.win`, native audio DLL/driver, SCSP and OGG) are runtime requirements; others (`g1d/g1e_cases.json`, old `m4/` and G1B banks) merit actual dependency classification before trimming.

**Authorized next packaging planning scope:** Exact M6-H source closeout first, one isolated `SonicChaos.yyp`/`SonicChaos.exe` naming + dependency-minimized Windows VM ZIP candidate, no gameplay changes and no automatic main merge. Then read-only workspace inventory, preservation of canonical private essentials + verified Git history, **specific DELETE/KEEP/UNKNOWN manifest**, and staged irreversible deletion only once Chief approves each path class. This is not optional new gameplay feature work; it is final presentation and source/backup hygiene. [Binding plan](docs/sonic-chaos-final-packaging-and-deletion-plan-20261102.md).

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

**Chief's bulk-cleanup correction (2 Nov):** 2.18 GB is only ~1.6% of the 133 GB workspace; do not spend dozens of jobs on incremental deletions. Reuse existing 14.425 GB manifest and verified H: essential backup, prioritize full inventory of \`releases\` (Chief estimates ~13 GB), the biggest clean Git worktree clones and generated build/cache trees. Present ONE ranked, exact-path, checksum/restore-supported **bulk deletion proposal**, potentially tens of GB if safe, then one Chief approval and coordinated deletion job. **No further standalone candidates or new worktrees for inventory.** Preserve unique private content and current source; never wholesale-delete the releases root. [Binding updated cleanup plan](docs/sonic-chaos-final-packaging-and-deletion-plan-20261102.md).\n\n## Workspace closure / permanent deletion

**Detailed permanent-delete / backup / restore protocol:** [WORKSPACE_ARCHIVE_STRATEGY](docs/WORKSPACE_ARCHIVE_STRATEGY.md). No local files are touched by documentation maintenance.



The old ~**170-folder** estimate covers development worktree/package groups, **not** recursive folder totals: Chief's later 2 Nov Explorer screenshot shows at least **133 GB, 2,929,194 files and 1,268,255 folders** (previous 1.41 GB figure was partial). **No Janitor-san**. Protect the accepted M6-H ZIP/source immediately and perform read-only top-level storage inventory before choosing a whole-workspace backup method; avoid an unplanned million-file Robocopy. Use combined Codex audit and Manager review when base freeze is ready:
1. Read-only inventory of full local paths, sizes, `git worktree list --porcelain`, branch/commit/dirty/untracked status, resource/private-asset manifests, final ZIP receipts.
2. Classify **canonical current**, **historical reproducible**, **research evidence**, **generated and safely recreatable**, **unknown/keep**. **Permanently delete only proven duplicate/generative outputs under an approved exact manifest**, retaining unique research in source history/essential independent backup; do not archive all 133 GB.
3. Verify separate reliable backup **and** restoration of accepted final source/required assets. Produce dry-run actions; Chief signs off each disposal class.
4. Only then remove registered worktrees safely with Git commands or permanently delete proven redundant old revisions; **never mass-delete, run blanket `git clean -fdx`, move registered worktrees in Explorer, or destroy private data**.

Public research repository keeps safe documentation. Private build payloads and copyrighted content remain outside public distribution; no automatic GitHub visibility or main-merge changes.

## Authority and change management

**Team now:** Chief; Manager-san #9; AM-san; **one combined Research/Designer Codex agent**. Cloud-kun and Janitor-san departed; the separate Claude Research/Designer works elsewhere.

**Docs policy:** Edit this roadmap **in place**; record accepted SHA and Chief approval once. Keep a concise [current issue ledger](docs/CURRENT_BASE_GAME_REMAINING_20261101.md), [agent operating contract](AGENTS.md), and [short memory](MEMORY.md). Historical full-roadmap version at [immutable Git snapshot](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md). Do not append old “CURRENT” reports forever.

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
| **M6-H MGHZ3 boss spike-gated reveal** | **CHIEF F5 ACCEPTED 2 NOV** · committed | Initial camera boundary now between spike3/4, tree hidden; subsequent pan reveals tree, Robotnik and complete eight-spike trap; boss/AQZ1 accepted with no notes. [Owner receipt](docs/m6h-chief-acceptance-and-base-status-20261102.md). |

**Verified Git update (2 Nov):** The exact M6-H production implementation is now committed on `poc/m6h-mghz3-spike-gated-reveal` at `c3e40a7a3d6c17be3e17d7c1eb729b2a705a3089` (parent M6-G `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905`); two subsequent documentation/verification commits put the branch at `64a5a53ceebed43ed79e36a681a27b0d6a0c16aa`. Git comparison confirms three commits ahead of M6-G and none behind. This corrects the earlier uncommitted-source statement. Packaging Candidate B reportedly smoke-PASS, but its file inventory, clean project naming and local folder cleanup have not been demonstrated. Source `options_windows_executable_name` remains `SonicChaos_A4B_EXPERIMENTAL.exe`; project `name` remains experimental. Do not create further candidate worktrees until existing ones are accounted for.

## NOW — FINAL PRIVATE WINDOWS CANDIDATE; CHIEF FULL CAMPAIGN GATE

**3 Nov production commit:** `8b3b435` **committed locally, worktree clean**; private source ZIP `SonicChaos_Production_20261103_FINAL_CANDIDATE_SOURCE_PRIVATE.zip` **12.10 MB**, Windows ZIP `SonicChaos_Windows_20261103_FINAL_CANDIDATE_PRIVATE.zip` **5.93 MB**, receipt `SonicChaos_Production_20261103_FINAL_CANDIDATE_RECEIPT.json` under `E:\AI\Codex\Sonic Chaos\releases`. Ordinary GameMaker Windows export is **unmodified**. **Technical candidate PASS (Designer-reported)**: one original gameplay Z80 backend for gameplay/F2 Sound Test, all 68 IDs present (63 playable + five empty), 26 redundant GMSound/OGG and obsolete Notes removed, historical B1/C10/G1B/M4 production implementations retired; tested native catalogue/UI/queue/startup/cross-zone audio, clean source project loading, compilation and Windows ZIP extraction. **Five inherited raw verifier failures remain documented.** Human listening and complete natural campaign not yet claimed. **Manager GO for one Chief test of exact ZIP, NOT final freeze.**

**Protected ancestors:** M6-H / MGHZ-007 boss reveal original spike3/4 Chief F5 accepted, source `c3e40a7a3d6c17be3e17d7c1eb729b2a705a3089`; Chief $A7 spike lifecycle accepted `8e9d22499dc910922bd788346bb35678b4a28494` ancestor. Preserve enemy/ring offscreen retention, original km/h panel, widescreen choice, original intro/pan, 25 known-use tracks, native256 parity and 348-wide modes.

**Chief test:** Extract and run **that single Windows ZIP**, play a complete Sonic campaign and complete Tails campaign through endings; normal gameplay audio and Sound Test audition are included in the same acceptance run, not separate repeat microtests. Report only reproducible blockers in one consolidated list. If no problems, Chief approves **private base freeze**, exact ZIP hashes/receipts, clean commit SHA, independent source restore and optional tag. **No changes to runtime assets/executable after Chief testing without declaring a new candidate.** New commit `8b3b435` is local only so independently back up its Git objects/branch and source ZIP on H: (and hash/restore-check) before freeze; do not assume previous `8e9d224` bundle is sufficient. First-launch ~2–3s audio latency parked pending later investigation, not reason to insert untested cards now.

**Workspace closeout:** Chief-approved initial cleanup removed **112.53 GB**, **856 targets** and **89 worktrees**. Root housekeeping then removed **19.69 GB**, **49 further worktrees** and 11 snapshot/build directories, reducing root **74 folders/11 loose files → 12 folders/only `AGENTS.md`**. Fifty-two obsolete management files independently hash-backed into one H: archive, Git stores/accepted packages verified; A1L golden PSG DLL and M4 tooling-reference support paths are documented exceptions, not the shipped game's redundant audio systems. No follow-on housekeeping work ordered.

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

**Historical storage note:** The old 133/145GB bulk-cleanup planning process is now completed and evidenced in Git history and the final execution receipt. The active direction is final product quality plus minimal root housekeeping; do not restart the retired staged deletion plans.

Public research repository keeps safe documentation. Private build payloads and copyrighted content remain outside public distribution; no automatic GitHub visibility or main-merge changes.

## Authority and change management

**Team now:** Chief; Manager-san #9; AM-san; **one combined Research/Designer Codex agent**. Cloud-kun and Janitor-san departed; the separate Claude Research/Designer works elsewhere.

**Docs policy:** Edit this roadmap **in place**; record accepted SHA and Chief approval once. Keep a concise [current issue ledger](docs/CURRENT_BASE_GAME_REMAINING_20261101.md), [agent operating contract](AGENTS.md), and [short memory](MEMORY.md). Historical full-roadmap version at [immutable Git snapshot](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md). Do not append old “CURRENT” reports forever.

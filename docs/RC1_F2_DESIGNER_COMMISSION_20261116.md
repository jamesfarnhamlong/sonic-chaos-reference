# Sonic Chaos — F2 Presentation and Classic Frontend: Designer-San Commission
**16 November 2026 · Manager-san #13 · Chief-authorized CONDITIONAL ENGINEERING GO**

## Decision and constraints
Chief chooses to **backload physical testing** until one combined F1+F2 private trial, rather than separately accept the F1 candidate immediately. **F1 engineering PASS is not Chief acceptance.** F2 may proceed **now**, but a combined candidate cannot be declared RC2 or production/released until the Chief later checks the remaining F1 and F2 scenarios.

Read public reference:
- docs/RC1_F1_MANAGER_REVIEW_AND_F2_CONDITIONAL_GO_20261116.md
- docs/RC1_CHIEF_FULL_RUN_DEFECT_REGISTER_20261115.md
- docs/RC1_CORRECTIVE_SPRINTS_AND_NGPLUS_GATE_20261115.md
- docs/CURRENT_MANAGER_HANDOVER.md, ROADMAP.md, AGENTS.md, MEMORY.md

Read PRIVATE repo issue #2: https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/2 ; review private F1 issue #1 / monitor issue #4 and F1_RESULT_MATRIX.md / F1_DELIVERY_REPORT.md.

## Baseline and branch
Private SonicChaos_POC F1 **frozen compiled game commit: e82af5554a755f2708b9120809ca3bb17ddc1eb7** (tree 4d8be45d40d8236a3d3277a056012964b5b70908), ancestor RC1 ad499c9b483776714cf18683ed9a23aa0ed1e668. Create a fresh PRIVATE F2 branch from **that exact game SHA**, not the original RC1 or an unverified local worktree. F1 branch/package immutable. Later F1 packaging-only verification files may be read/reused for test harness but must not introduce unreviewed runtime changes. Push incremental commits and exact diff/SHA receipts; keep original main/R22/RC1/F1 branches and Classic freeze untouched, 22 dependencies private and authenticated.

## F2 tickets — seven scoped issues
**SC-RC1-02 — AQZ speed-up/pusher palette:** identify exact mechanism/object first (not automatically ROM $A7 terrain booster); compare authenticated original SMS palette, palette bank and runtime draw/underwater cases. Only fix confirmed wrong coloration. Compare Sonic/Tails and Classic/Enhanced.

**SC-RC1-04 — GPZ inversion hang before results:** Chief observes a 1–2 second inverted black/white hold in GPZ only. Measure real native frames, compare against original ROM and other zones; if original canonical, record no-change disposition. If erroneous, correct minimum fade/goal ordering without altering score/rewards/timers/SS transitions.

**SC-RC1-11 — Enhanced Save TV default focus:** incomplete file defaults to current unfinished frontier; completed with fewer than six emeralds defaults THZ. The six-emerald completed/Super NG+ entry is **reserved and not activated** until separate approved Super integration. Do not fake transformation icon or auto-modify a completed save. Preserve five-slot character lock, dual-generation JSON checksum/seq, erase/wipe, restart and existing Chief RC1 saves.

**SC-RC1-12 — Pause pictures and zone icons:** use original-faithful/pixel-authentic art for six zones; remove inappropriate EEZ Super Sonic placeholder when not transformed. A Super portrait is reserved for actual future NG+ state only. Keep expected pause controls, aspect and pixel art integrity. No unlicensed uploads to public reference repo.

**SC-RC1-13 — EEZ last-emerald pre-credits white flash:** brief white rectangle is 4:3 inside Enhanced widescreen; locate actual camera/surface/pass responsible and render the intended flash across active Enhanced viewport while preserving Classic 256x192 duration/frames. Inspect window/fullscreen, integer/noninteger and CRT/Sharp Pixels choices as needed.

**SC-RC1-14 — ORIGINAL ROM LEVEL SELECT in Classic:** Chief is emphatic: **the official original ROM's OWN cheat-triggered level select**, with authentic original visual screen, navigation, sound, character/act selection and cheat entry. This is **NOT** the custom GameMaker developer selector SCR_chaos_debug_select, NOT a wrapper around it, and NOT a newly invented substitute. Trace original ROM code/graphics/menu/cheat behavior from Z80 disassembly and captured original emulator behavior; port the original into native GameMaker faithfully (not necessarily executing Z80). Verify actual cheat order rather than presuming “Konami code.” If original behavior/assets cannot be authenticated, HOLD this single ticket with evidence and complete the others; do not fake it. Preserve Classic title idle attract and controls.

**SC-RC1-15 — Classic title unwanted white text:** identify draw origin and remove only extraneous white overlay while preserving original ROM title text, Classic cheat, sound, frontend, idle demo and Enhanced independent menu. Native pixel compare Classic title.

## Test conditions
1. Trace each F2 issue to a reproducible actual compiled GameMaker scene, original ROM when parity requested, and minimal source diff; separate ROM evidence, source fixtures, native compiled results and Chief acceptance. No blanket green results from unexecuted cases.
2. **Mandatory full F1 carryforward**: rerun all TEN F1 tickets in native compiled scenes (Sonic AQZ loops, THZ/EEZ crumble, GPZ1 music, boss/invincibility priority/results, SEZ3 pogo crush/Tails clear, AQZ3 final pip and Boss Rush music, all Classic boss camera view, TV standing and SS1 TV start), plus aggregate native F1 preservation. No regressions to RC1 normal gameplay or Enhanced OFF/Classic. Include two characters, 256x192 Classic / 348x196 Enhanced, default/feature-on, important full-screen/Save TV scenarios.
3. **Real user-save safety**: F2 normal release uses canonical SonicChaos save namespace exactly as RC1/F1; no trial prefix invisibility, data reset, migration or overwrite; back up and smoke-test resume/erase in SCTest scratch profile. Do not alter Chief's completed RC1 saves/settings. Any incompatible schema is a delivery HOLD.
4. **Test-data hygiene**: use existing separate SCTest standard account only for dirty native tests with watcher proof of zero Chief AppData writes. Limit diagnostic files and bytes; keep compact failure captures, hashes and small deterministic logs. No thousands of screenshots or 150GB scratch archive. Keep verifiable Git/H: recovery.
5. **Isolation of enhancements**: do NOT cherry-pick Super Sonic R3d (separate verified private SHA 21176dd03138b155412bef9256306437275414ca), implement A5 sound research without new approval, “fix” closed false-positive MGHZ2 freeze, retime attract or perform broad physics/refactor/60fps work.
6. Review every unexpected difference. If an F1 regression is discovered, trace and correct it with separate recorded follow-up source SHA, preserve prior immutable F1, propagate into F2 and re-run cross-coverage. Do not hide unresolved F1 failures.

## Delivery
One **PRIVATE combined F1+F2 engineering candidate** (tentative identity v0.99.2-f2, **not automatic RC2**); one Windows ZIP with clean eight-file runtime, one complete recoverable private source ZIP including 22 authenticated dependencies, SHA256 per-archive and manifests, exact remote Git head/tree, independent H: backup proof, no instrumented/diagnostic artifacts in shipping runtime.

Supply a per-ticket matrix (17 F1/F2: all ten inherited F1 + seven F2) reporting reproduced cause, native PASS/HOLD, changed files, source/ROM evidence and regression limitations. Supply short **combined Chief test guide** focused on all reported scenes. Source suite inherited failing cases remain declared (F1 record 75/178 PASS, no RC1-passing suite newly fails), not artificially reclassified as all PASS. Engineering status is not Chief acceptance.

**After delivery:** Manager reviews engineering evidence, Chief performs one consolidated acceptance band. Only then consider an accepted RC2 promotion. No automatic Super integration, production main merge/tag, public release or v1.0 claim. Please send milestone private SHA updates at meaningful steps without interrupting Chief for minor details.

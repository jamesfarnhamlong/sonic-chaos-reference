# Sonic Chaos — F1 Manager Review and Conditional F2 GO
**16 November 2026 · Manager-san #13 · Chief chooses deferred human testing**

## Decision
**GO for F2 engineering, conditionally.** Chief prefers another substantial development sprint before a combined human test band. F1 is **engineering PASS / Chief acceptance PENDING**. This explicitly supersedes the earlier sequencing rule that F2 must await owner physical F1 approval. No v1.0 signoff, production promotion, release tag or public release is implied.

Current [live register](RC1_CHIEF_FULL_RUN_DEFECT_REGISTER_20261115.md); [sprint plan](RC1_CORRECTIVE_SPRINTS_AND_NGPLUS_GATE_20261115.md); private POC [F1 issue #1](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/1) and [F2 issue #2](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/2).

## Technical F1 delivery review
Read Chief-uploaded F1_DELIVERY_REPORT.md, F1_RESULT_MATRIX.md, F1_CHANGE_INVENTORY.md and F1_CHIEF_ACCEPTANCE_GUIDE.md. Remotely checked the private GitHub F1 branch and frozen source ancestry. Findings:
- Private branch fix/f1-rc1-corrective-20261115; exact native-tested F1 **game code SHA e82af5554a755f2708b9120809ca3bb17ddc1eb7**, tree 4d8be45d40d8236a3d3277a056012964b5b70908, child of frozen RC1 ad499c9b483776714cf18683ed9a23aa0ed1e668. Later F1 commits are verification-only by remote compare.
- Private v0.99.1-f1 Windows trial ZIP reported SHA256 fc31f1050605fe7d1e3601818f86ff423d71ff6bd302051b8a5f29545c3f9df9; recoverable source ZIP reported SHA256 0bdf5de09e805bea0373608efefe33cf05260a2e4f3548fc8952e08c441b7a4a. Manager has **not** accessed Chief-local ZIP bytes to verify these hashes.
- All **10 F1** issues are reported **native engineering PASS** in a compiled GameMaker RC1-vs-F1 SCTest matrix; 7/7 aggregate preservation scenarios exact; 115 SCTest runs observed zero Chief AppData writes. F1 package preserves canonical SonicChaos save namespace; Chief RC1 saves should continue unchanged.
- **Source aggregate is NOT 178/178 PASS**: the record says 75/178 passed and no suite passing on RC1 failed on F1. Inherited failures remain; 7 suites newly passing versus an incomplete RC1 comparison export are not proven new game fixes.
- Native tests caught and corrected three problematic first cuts before final delivery: SC-RC1-20 monitor change broke SS1 start, SC-RC1-16 first GPZ3 camera correction blocked the boss, and SC-RC1-10 first HUD pip changed Boss Rush desperation music. These corrections are traceable and the final aggregate compares clean.
- Natural Sonic AQZ loop run-in at high speed, natural SEZ3 boss big-drop contact and Tails pogo victory, complete Classic boss cameras and Chief's visual/feel remain human checks. Automated tests do not constitute Chief PASS.
- Exact original RC1 and R22 code and packages, Classic freeze, 22 private dependencies, private Git/H: recovery preserved; no main merge or public release. F1 remains an immutable private candidate for rollback.

## Conditional F2 commission constraints
1. Branch F2 **from exact F1 game code e82af5554a755f2708b9120809ca3bb17ddc1eb7**, not from RC1 or a changing worktree. A separate private branch, individually committed fixes and pushed receipts. F1 ZIP/branch stays immutable. If tools depend on later verification-only F1 commits, disclose/copy those without altering the frozen game source.
2. Scope is exactly **seven F2 tickets**: SC-RC1-02 AQZ booster/pusher palette; 04 GPZ inverted black/white goal/result delay (prove actual ROM behavior first, accept no-change if authentic); 11 Save TV default incomplete-frontier or completed-under-six emeralds THZ (reserve six-emerald NG+ flow for separate feature); 12 Pause zone icons and EEZ/Super art mix-up; 13 widescreen EEZ final-emerald white flash; 14 Classic title original ROM cheat Level Select; 15 unwanted Classic title text.
3. **SC-RC1-14 must faithfully port the ROM's own cheat-triggered Level Select menu/presentation/navigation/behavior**. Do NOT connect the GameMaker custom developer selector SCR_chaos_debug_select or invent another UI. Prove ROM cheat sequence, graphics/menu, sound, input and character/act effects. If authentication is blocked, HOLD only that ticket and continue independent F2 work.
4. No Super Sonic NG+ code integration (separate remotely verified R3d feature HEAD 21176dd03138b155412bef9256306437275414ca, core accepted for its reported tests only). No speculative MGHZ2 twist physics (SC-RC1-21 closed false positive); SC-RC1-22 sound A5 is research-only and must not be changed without explicit approval.
5. **F2 native preservation MUST retest all TEN F1 fixes**, plus Classic 256x192, Enhanced 348x196 Features OFF/ON, Sonic/Tails, save resume, SS1 TV start, GPZ3 boss floor, SEZ3 pogo clear/crush, AQZ final HUD/music and all relevant F2 scenes. Use SCTest for dirty probes; prove no Chief AppData writes and cap evidence output. Do not repeat the thousands-of-PNG/150GB clutter.
6. Deliver ONE combined private **F1+F2 engineering candidate**, separate Windows and recoverable source ZIP with 22 deps, SHA256, Git/H: recovery, exact per-ticket matrix and short combined Chief test guide. Use stable **SonicChaos** save namespace; do NOT wipe or import Chief's live profile. Suggested private identity v0.99.2-f2 (not yet RC2). Don't label any outstanding Chief acceptance as PASS.
7. If later Chief play reveals an F1 failure, make the smallest independently versioned F1 follow-up and propagate it into the F2 candidate with full affected regression; preserve old F1 code SHA. **No RC2 nomination until combined Chief F1+F2 test band succeeds**. Do not automatically proceed to NG+ or v1.0 after packaging.

## Deferred human test: combined band
F1 checks: AQZ Sonic loop visuals; all restored THZ/EEZ crumble and prior SEZ/AQZ; GPZ1 invincibility + Sneakers audio in Enhanced ON with ROM-canonical OFF/Classic difference; boss/invincibility/result audio; SEZ3 grounded pogo crush and Tails victory; AQZ3 last HUD pip and Boss Rush music; Classic GPZ3 complete fight and other boss views; monitors no sinking/jitter; SS1 initial TV; saved-game resume.

F2 checks: AQZ palette, GPZ goal delay with ROM reference, Save TV default focus, six-zone Pause thumbnails/EEZ image, EEZ widescreen flash, authentic ROM cheat Level Select, Classic title text. Run Chief's own Classic and Enhanced play routes, not just fixtures. F1/F2 verdict is PENDING until owner reports results.

**Current:** F2 engineering CONDITIONAL GO; F1 Chief acceptance PENDING; no combined package yet; v1.0 HOLD.

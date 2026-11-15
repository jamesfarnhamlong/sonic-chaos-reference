# Sonic Chaos — RC1 Corrective Sprints and Super Sonic NG+ Gate

**Private implementation issues:** [F1 core fixes](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/1) · [F2 presentation/frontend](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/2) · [Super Sonic NG+ HOLD](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/3). Exact issue content is in PRIVATE source repo; public management contains no source binaries/screenshots.
**15 Nov 2026 · Manager-san #13 · ACTIVE plan for Chief-approved full-run fixes**

**Source of truth for all owner findings:** [RC1 Full-Run Defect Register](RC1_CHIEF_FULL_RUN_DEFECT_REGISTER_20261115.md), IDs SC-RC1-01…20. Do not reopen the obsolete 5-Nov issue tracker as active. Keep historical tracker/ROM research for source references only.

## What changed
Chief finished two whole Enhanced playthroughs (Sonic all Chaos Emeralds, Tails), all Boss Rush, and first two Classic Sonic zones on PRIVATE RC1, then reported many meaningful bugs. This is strong exploratory coverage but **v1.0 acceptance HOLD**, not a failed packaging/recoverability certificate. RC1 `ad499c9b483776714cf18683ed9a23aa0ed1e668` remains immutable comparison oracle; no silent in-place overwrite or main merge.

## Approach — long engineering sprints, short owner verification
- Do **two substantial corrective sprints**, each handling a coherent set of tickets in one Codex working session/branch and using independently reviewed commits/targeted tests per issue, plus one aggregate compiled native preservation test. No dozens of tiny user-delivery ZIPs.
- Test in isolated `SCTest` profile with bounded diagnostic logs/screenshots (quota and post-run cleanup), no ordinary Chief AppData writes, no repeated 6,000-file incidents. Never delete live Chief RC1 saves; no repeat fresh-profile wipe for fixes.
- Track every ticket through OPEN → REPRODUCED (or original ROM confirms) → PATCHED → NATIVE-VERIFIED → CHIEF-VERIFIED/CLOSED. If not reproduced, mark HOLD with evidence, not invented green. Include exact code SHA and unresolved source/raw harness limits.
- Prefer fix the actual primary cause rather than symptom hacks. ROM/source proof where possible, original Classic 256×192 invariant; Enhanced wide 348×196 fair-play deltas explicit.
- If gameplay/physics/audio improvements alter the normal game, require cross-product validation: Sonic/Tails, Classic/Enhanced OFF/Enhanced ON, screen modes, normal save compatibility, five SS, all six bosses and Boss Rush, early/mid/late act music ownership.
- Work on **separate private branches from accepted RC1 source**, preserving code freeze, H: and all release ZIPs. Push incremental commits with exact refs and dependency receipts. No release naming claim before delivery hashes and Chief check.

> **SC-RC1-14 scope clarification (Chief, 15 Nov):** Classic's cheat must expose the authentic original ROM Level Select, not the internal GameMaker developer selector and not a redesigned menu. This is **F2 only**, not F1. See [living tracker](RC1_CHIEF_FULL_RUN_DEFECT_REGISTER_20261115.md).

## Sprint F1 — source/ROM mechanics + boss/camera + audio (priority)
**Tickets:** SC-RC1-01,03,05,06,07,08,09,10,16,**20**.

1. Establish a reproducer/scene matrix in the actual compiled RC1 for all ten; probe original ROM where behaviors are intended to be canonical. Root-cause reports not required for already ROM-proven crumble gate before source edit, but confirm port gate precisely.
2. Correct ROM ledge `$AF` across **93 cells**: THZ1(1), THZ2(1), SEZ1–3(36), AQZ1(32), AQZ2(2), EEZ2(21). Restore 23 missing behavior; timing spawn T, hold16, `$B0` at T+17, A3/splinters at T+18; remembered-cell/pool/camera/restart.
3. Sonic AQZ loop **sprite mapping** audit across every type of loop (Sonic and Tails controls, left/right, roll/slow/exit, Classic/Enhanced) without conflating this with speculative loop-motion speed research. Boss/level camera all six Classic arenas; fix GPZ floor cropping at authentic 4:3 boundary without sacrificing Enhanced wide fairness.
4. Boss health final AQZ desperation hit, boss falling-pogo collision, Tails equipped victory state cleanup. Stage label typed “SLz3” must be resolved from actual room/repro (don't casually rewrite to SEZ3).
5. Consolidate music state arbiter: GPZ1 invincibility→zone restore, invincibility > boss until effect expires, then boss/zone based on active state, and results > boss. Test both ordinary and Boost/SS transitions with native driver.
6. **Classic TV/monitor standing SC-RC1-20:** Chief has screenshot-confirmed Sonic now embeds into intact monitor top; previously it vibrated violently. Inspect ROM-authentic standing floor/contact projection and port sprite origin. Correct both displacement and prior oscillation, test continuous stationary frames, Sonic/Tails, monitor variants, collision/landing/break/jump-off, Classic/Enhanced OFF/ON, preserve R18 monitor repair and ordinary solid floors. No unexplained global offset hack. Dedicated private issue [#4](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/4); owner screenshot remains private.
7. One comprehensive **private F1 Windows trial**, exact version/manifest/22-dep source and native preservation report, focused Chief acceptance route (AQZ Sonic loop, THZ/EEZ crumble, GPZ music, 2 boss pogo cases, Classic GPZ camera, and monitor standing without sink or jitter). **No production RC1 replacement** and no automatic F2 work until F1 evidence reviewed. Do not promise perfect original equality if not measured.

## Sprint F2 — presentation + Classic title/frontend + save UI
**Tickets:** SC-RC1-02,04,11,12,13,14,15. Base on accepted F1 verified code, but preserve independent F1 and F2 SHA refs.

1. AQZ speed item palette: object identification first, then original SMS palette compare. GPZ inverted black/white linger: compare with ROM and other goal transitions; if original or harmless, record no-change disposition.
2. Make widescreen final-emerald EEZ white flash respect actual rendering viewport while leaving Classic 4:3 intact.
3. Pause pictures: canonical art for each of six zones, no EEZ/Super Sonic substitution except actual transformed NG+ display. Pixel presentation only; art provenance/right checks. Complete/incomplete Save TV default focus rule, with 6-emerald NG+ entry **deferred until Super feature explicitly accepted**.
4. Classic title: remove stray white text. **Restore the original ROM's own cheat-triggered Level Select, NOT the custom GameMaker developer selector and NOT an invented replacement.** Use ROM-disassembly/runtime evidence for exact cheat sequence, original level-select graphics/layout/input/audio, routes, cancel/return and character behavior. Find/port authentic ROM menu logic and assets as needed for native GameMaker; direct Z80 execution is not assumed. The developer `SCR_chaos_debug_select` can be inspected as a separate internal tool but must **not** be surfaced as the Classic ROM menu. If source assets/behavior cannot be authenticated, HOLD and report; no substitute. Preserve title idle demos and Classic inputs.
5. One private F2 compiled trial and full combined regression; compare against fixed F1 and immutable RC1. Exact package identities, no appdata spill; Chief targeted acceptance across title, menu, GPZ ending, EEZ flash, AQZ, pause/screenshots and save resume. After owner PASS, nominate stable **RC2** for a new focused checking band. No default feature additions.

## Super Sonic — **NGP pilot**, not hidden inside F1/F2
Feature branch `feature/super-sonic-r3-20261114` exists on private GitHub, but local R3d IDs `6b4486e`, `21176dd` from Chief's handover were not resolvable via private remote fetch on 15 Nov. Agent must report local full hashes and push exact reviewed source if authorized. Do not merge branch wholesale: compare it against the **F2 accepted corrective source**, list all changed files/hunks, identify possible conflict in loop, AQZ, result, Save UI, camera and music owners.

**Go/no-go:** Only after F1/F2 clean normal game testing and Chief says GO, integrate on a separate opt-in NG+ trial branch (future RC3/NGP). Super ON exclusively in Enhanced NG+ Sonic with documented eligibility; Classic and ordinary Enhanced Sonic/Tails maintain their exact behavior and profiles. Verify authentic five Special Stage Emeralds + sixth from Eggman ending, save completed-state/6-emerald semantics, 100-ring + 1UP cap, transformation art, camera waterline, loops, signposts, music arbitration, boss phases, death/detach, restart, Save TV/Pause. Require diff-matrix/compiled source tests, then owner transformation trial. If time or risk threatens v1.0, **park Super until after 1.0**; its presence on a branch is not a mandate for inclusion.

## Next owner checking band, once F2 candidate is ready
- **Sonic:** six-zone full run, SS1–5, sixth emerald/ending, repeated saved-game resume, GPZ1 invincibility, AQZ loop art/item, AQZ final health hit, EEZ flash.
- **Tails:** six-zone full run with boss finishes **wearing pogo** and save/slot isolation.
- **Classic Sonic/Tails sampling:** verify stable correct-height Sonic/Tails stand on multiple intact monitors (not embedded or vibrating), land/jump-off/break; actual 256×192 title/level-select, THZ/EEZ crumble, GPZ boss visible floor, six boss-camera arenas, no unwanted text, unchanged original music/graphics.
- **Boss Rush:** six bosses, boss HP final phases, end screens, tracks through results, no pogo levitation.
- **Visual/audio:** GPZ inverted flash comparative, pause zone icons and complete file selection, fullscreen + 4:3/wide, Enhanced Features ON/OFF, timing/track ownership, no new AppData contamination.
Use an explicit checkbox result per ticket. Any unresolved P1 is a new documented release hold.

## Housekeeping and ownership
Continue using the disposable `SCTest` account and explicit quota-limited diagnostics for F1/F2/NGP. When Chief accepts final result and no follow-up is needed, apply [post-RC1 housekeeping plan](V099_RC1_POST_TEST_HOUSEKEEPING_PLAN_20261114.md) to remove SCTest + its user profile and superseded captures, while protecting RC1/final source/H: archives and fresh Chief saves. **Do not do cleanup during active corrective testing.**

**Chief alone authorizes F1/F2 owner acceptance, any Super integration and eventual v1.0.** Manager records status in this doc, the live defect register, ROADMAP.md and MEMORY.md; design agent implements in PRIVATE `SonicChaos_POC`; PUBLIC reference repo remains documentation/research only.

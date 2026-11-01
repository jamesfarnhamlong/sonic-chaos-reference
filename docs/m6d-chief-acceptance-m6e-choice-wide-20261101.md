# Sonic Chaos — Chief accepts M6-D; M6-E Character Select widescreen polish
**Manager-san #8 · 1 November 2026**

## Decision: M6-D CHIEF ACCEPTED

Chief reported **“Success! All good”** after running the private M6-D source candidate in normal GameMaker F5 and supplied an image of the original-style rolling **km/h** display, visibly rendered over a Sonic goal-sign scene. Chief's statement is treated as acceptance of the previously requested consolidated M6-D test scope (both-character speed display, ordinary controls and removed developer keyboard routes, Pause→Level Select, menu Sound Test). The supplied image independently shows one goal-panel view, **not** independent visual proof of every separate tested route. Do not ask Chief to rerun accepted checks.

Accepted POC source is `jamesfarnhamlong/SonicChaos_POC:poc/m6d-speed-display-cleanup@7acdd39f469a74d41362f2998c6783d815b719bf`, direct child of Chief-accepted M6-C2 `3cf379240c6e1e06b52a4b57fcfd087fcd1fffa2`. All existing 1,313 resource registrations preserved; one original glyph atlas added (1,314 total). The original-ROM $19 goal child rolls/settles the source bonus rating (controlled example 1:50 +28 rings → 617 km/h), with unchanged tally, lives/continues, native audio and intro border. Production shortcut scan removed dev-only F2/F3/R/F4/F6–F12/Shift-number/etc. while preserving normal controls, Pause→Level Select, menu Sound Test. Designer source/ROM checks passed; Chief now accepts F5 candidate. No merge to POC main automatically; source branch remains accepted checkpoint.

**Private package** `SonicChaos_M6D_20261101_A_PRIVATE.zip` and its receipt are user-local; Manager GitHub review did not independently validate private bytes. [Previous gate review](m6d-manager8-review-chief-gate-20261101.md). Remaining known exceptions from historical research unchanged; do not reopen source audio/physics.

## New Chief observation — Character Select still displays as centered 4:3

Chief says **“at some point the character select needs expanding to 16:9 too, think its the last element.”** Treat this as a **newly confirmed user-desired widescreen presentation adaptation** and candidate next milestone, not a canonical SMS defect (the original was 256×192).

Source verification against accepted M6-D:
- `scripts/SCR_chaos_choice/SCR_chaos_choice.gml:chaos_choice_draw()` computes `cp_x=vp.left+floor((vp.w-256)/2)`, `cp_y=vp.top+floor((vp.h-192)/2)`, draws a full black viewport rectangle, then one original `SPR_chaos_choice_bg_{0,1}` at that 256×192 anchor and the original 6-frame actor sprite centered at `cp_x+128,cp_y+137`.
- Both original choice BG sprites are exactly **256×192**; source GameMaker viewport is accepted **348×196**, so centered art leaves **46 px per side and 2 px vertically**; those black outer strips do not match the intended filled-widescreen presentation.
- `OBJ_chaos_choice/Create_0.gml` starts original $82 choice theme; the state machine owns original cursor/movement $B4, confirmation $A0, six-update actor frames, palette fade/cycle and 30/90 wait transitions. `OBJ_chaos_choice/Step_0.gml` invokes accepted `chaos_run_new_game` on completion. These **must remain byte-for-byte or behaviorally unchanged** as far as practical.
- Other accepted title/results/zone cards already have previous widescreen adaptation and Chief acceptance. This does not prove all presentation bugs fixed; MGHZ3 visual roughness and one-time startup delay remain user-parked, attract/demo playback remains optionally deferred.

## M6-E — Character Select 348×196 widescreen polish (next scoped task)

**Authorized as a future, single focused frontend polish milestone**, no immediate code modifications made by Manager. If assigned, branch `poc/m6e-choice-widescreen` directly from accepted M6-D SHA `7acdd39f469a74d41362f2998c6783d815b719bf` (not older M6-C2/G2 or historical audit branches).

Scope:
1. Preserve exact original 256×192 composition at 1:1, both Sonic/Tails animation/portrait/cursor and palette-effect timing; **do not scale/stretch source pixels or change sound/input/state machine**.
2. Replace **only the unintended black SIDE MARGINS** in the 348×196 choice scene with a deliberate, source-compatible full-width background extension. Investigate the original two BG sprites and current color banks so extension follows natural edges / repeatable background features; make a tasteful widescreen composition without invented foreground figures or arbitrary mirror seams. User intent is full 16:9 character select, not a 4:3 island over black. At native256 retain the exact original pixels and expected black/VDP boundary semantics.
3. If the existing art is not plausibly extendable from its edge tiles, develop **minimal bounded background extension** with clear side-by-side conceptual preview and source/backdrop explanation rather than hiding the problem behind solid black or stretching all imagery. This is an explicitly allowed **PC widescreen adaptation**; don't stop because the original 8-bit ROM has no widescreen graphics.
4. Source-host verification: 256 frame/animation/palette pixel parity and 348 fill/margin coverage for both selection states, multiple choice animations and fades; current 60Hz timing, choice music $82/change B4/confirm A0, actor launch to THZ1, both characters and accepted G2 native music and M6-D original speed panel/shortcut cleanup. Resource & private art preservation. Avoid agent Runner error623 loop; one Chief F5 preview/candidate, no micro-test cascade.
5. Deliver one clean pushed branch SHA, all passed/retained test exceptions, private GameMaker ZIP/manifest/CRC if new private art required, and **one Chief acceptance viewing of Sonic/Tails choice screen**. No automatic main merge. Do not modify MGHZ3 pan, startup timing, results cards or retired developer shortcuts as part of M6-E.

**After M6-E** review optional attract/demo feature and release/readiness vs separately parked MGHZ3/startup polish; do not declare project release-ready solely on source-only gate.

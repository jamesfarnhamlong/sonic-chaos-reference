# Sonic Chaos — C1-R3 Original Special Stage Loader and Camera Phase
**12 November 2026 · Manager-san #11 · ONE ISOLATED DESIGNER CLASSIC RESEARCH/BOUNDED-CORRECTION SPRINT GO · NO CLASSIC REPLACEMENT**

## Chief’s priority and present source

## FINAL R3 STATUS — ISOLATED TECHNICAL PASS, CLASSIC REPLACEMENT HOLD (12 NOV 2026)

Chief delivered isolated C1-R3 at **`b667cc5cebcd3c3e047d9f527cc78b76e1e027f0`**. Original ROM camera work is now **prepared before player, committed after objects**, rather than computed in post-player End Step. Five SS stage streams×100 = **500/500 source camera phases exact**, settled SS5 equivalent-state clock **145/145 positions/camera exact**, S6 Enhanced **10,542 states and 102 images exact** in inherited bounded matrix. The raw historical SS4/SS5 harnesses retain FAIL due their different mode/phase/settlement setup; separate explicit-mode SS4 22,742 assertions PASS, but a new valid comparison does not erase the old FAIL log. Only two Classic-only scripts changed; R2 SS Y starting coordinates preserved. [Full Manager R3 review](C1_R3_CAMERA_PHASE_MANAGER_REVIEW_20261112.md). **This R3 commissioning brief is historical/complete; do not relaunch R3.** [NEXT C1-R4 VDP render-policy original ROM audit](C1_R4_ORIGINAL_VDP_RENDER_POLICY_SPRINT_20261112.md) from exact R3 local commit. Classic production replacement/integration/Chief test still HOLD.


Chief’s strict instructions: **future Classic = as close to the original SMS Europe v1.2 ROM as evidence permits**, including original quirks, warts and source defects; **NO QoL or discretionary fixes**. Current production Classic and frozen original Classic tag remain untouched. **Enhanced Wide348×196**, in existing protected S6 `47c501ecb994a4fcb1eeac1c29793f3f1142a304`, is the reference for Enhanced with all *new optional gameplay QoL* OFF. The separate S5–S7 frontend/CRT owner acceptance remains deferred, with unchanged S6 Windows ZIP.

**C1-R2 isolated research source is the sole allowed R3 parent:** `316125f6f280f24a7a8af507155d9dfe86954cea`; branch `classic/c1-r2-rom-wide-gap-closure-20261112`, parent C1-R1 `bc32e706691666b420c4daeff87338ec865190e5`. Preserve R1 and R2 sources, Git refs, Windows research trials, receipts, original Classic tag, S4–S6 and S7 no-change source. Independent C1 project resides at `management-audits/c1-20261112/project/SonicChaos.yyp`; reuse exact isolated worktree/project with a new R3 branch, and **never write in S6 production checkout**. Full private source ZIP `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Production_20261112_C1_R2_CLASSIC_FIDELITY_SOURCE_PRIVATE.zip`, receipt `SonicChaos_20261112_C1_R2_CLASSIC_FIDELITY_RECEIPT.json`. Restore/check four ignored runtime and eighteen original sprite PNGs from complete E:/H: package. Verify full SHA/parent/clean tree before change, no auto publish/merge/tag/main release.

**Read the full private R2 report before executing:** `E:\AI\Codex\Sonic Chaos\releases\C1_R2_ROM_WIDE_FIDELITY_20261112.md`, plus R2 `c1-r2/coverage-matrix.json`, `c1-r2/reconciled-findings.json`, original/native phase traces and prior R1 report; [Manager R2 source review](C1_R2_ROM_WIDE_MANAGER_REVIEW_20261112.md), [C1 ROM-wide binding mandate](C1_ROM_WIDE_CANONICAL_FIDELITY_MANDATE_20261112.md) and current AGENTS/ROADMAP/MEMORY/HANDOVER. These private files are on the Chief's actual local system, not the public management repo; C1 agent has local custody, Manager read uploaded R2 Markdown only.

## R2 established and MUST NOT regress
- Original-ROM hundredth-ring natural-entry trace identifies first coordinate divergence at `registration_import` (update1, before core move/collision), **−1280 in16.8 units = −5px**, due to missing registration of Special Stage core from stage constructor. Classic-only `objects/OBJ_chaos_zone/Create_0.gml` fix exactly corrects SS2 Y1838, SS3 Y622, SS4 Y366, SS5 Y878; SS1 Y118 remains unchanged negative control. **Do not replace with arbitrary spawn Y offset, map edit or floor snap.**
- R2 original SS native entry tests PASS (8 stage-character corrections plus 2 SS1 controls); C1 contract1095 + new SS entry60 PASS. Native Classic width256x192, 23 rooms×2 characters×3 scales =138 captures; no stretching. Ordinary Classic R1 3564 sampled rows unchanged.
- Enhanced control exact versus S6: 4554 stage-room+5988 boss/ring state=10542 samples, 46+12+44 native/Options images=102; original S5/S6 windows/UI/gameplay/camera/save/audio intact. All S7 no-change source untouched.
- **SS5 inherited clock camera test remains a true FAIL**. Do not waive, rewrite assertions without proof, or convert to PASS by hiding affected states.

## R3 bound scope: actual original loader→player→camera update ordering
**Phase A — ROM/GM matched first updates**
1. Capture **natural original ROM entries** into each of SS1–SS5 (Sonic hundredth-ring route), preserving genuine state0/update order, camera work/pending/committed camera registers and player/controller input at precise RAM/frame boundary. Tails SS stress optional, NEVER claim Tails naturally enters the original stages.
2. Instrument at corresponding **compiled Windows GameMaker** boundaries: room/zone creation, stage start seeded core and registration, adapter import, pre-core state, player physics/collision, camera target/current write, End Step, presenter draw, update/VBlank commit. Verify which phases differ because the ROM starts in state0 while GM uses state1 wrapper. Isolate first divergent tick/field, not merely observed screen pixel.
3. Align **host frame/tick offsets** and original ROM interrupt/loader scheduling before deciding a camera mismatch is a gameplay defect. Record source routine, RAM pointer/state, GameMaker path, both traces, causal explanation and evidence grade.

**Phase B — strictly proof-backed corrections (one source coherent subcase only)**
4. Investigate recorded SS camera evidence:
   - **SS1** sampled camera Y=15 vs original14.
   - **SS3** R1 settled cameraY516, R2 settled cameraY519, originalY518.
   - **SS4** look-down/lead path remains open.
   - **SS5** clock update11 current camera X30 vs original31 (inherited SS5 raw test FAIL).
   - **SS2** verify its first-update camera/lead phase even though registration Y correction passes.
   - Original pending camera computation before player pass vs GM SS End Step using post-player lead may explain some drift but is **hypothesis requiring paired proof**.
5. Apply minimal **Classic-only** correction if traced original-camera update order actually differs. Prefer a precise phase/order and state-ownership fix over per-stage ±1 pixels or arbitrary delay; preserve special-stage map/collectibles, original 16.8 anchors and canonical collision/physics. If internal GameMaker phase cannot be made ROM-identical without broader unproved pipeline changes, **stop at research/hold** and leave R2 original candidate intact instead of shipping apparent pixel-matched deception.
6. Record first-update through at least any SS5 clock failure window, look-down SS4, launch, stationary, turn, jump/rise/rocket/hurt as relevant to original stage scripts; exact source slices, update cadence, state/PSG and camera trace diff. Avoid overstating entire SS route from fixed initial snapshots. Keep each of 16 prior findings intact and update 382 record register with exact new evidence/UNVERIFIED entries.

**Phase C — regressions and full scope boundaries**
7. Re-run **actual Windows GameMaker** full matrices: all five SS first-update corrected anchors, SS camera traces including raw existing SS5 FAIL, Classic 256x192 at1x/2x/3x, ordinary original 18 acts where regression risk, both characters stress/real route distinctions, and native sound owner comparisons when touched. Keep original camera/world/source art/PSG/physics unchanged except proven Classic-only needs.
8. Confirm **Enhanced S6 EXACT** on comparable prior 10,542 native states and 102 image cells, rather than merely running optional test suites; source save/INI file hashes and Boss Rush/CRT/post-S5 presentation unchanged. Avoid changing Enhanced shared scripts unless guarded Classic-only with proof.
9. **Explicit exclusions from new R3 implementation** (may retain research notes): do **NOT** broadly refactor the shared16 object-slot pool/lost-ring lists; R2's GPZ controlled original scheduler peaked6 and all sampled7-ring hurts succeeded, so natural shortage unproven. Do NOT port recorded THZ/GPZ/SEZ attract demos without original loader/dispatch alignment; do NOT implement constant black left8 VDP stripe (backdrop is palette-dependent); do NOT claim physical PAL timing/cycle-accurate VDP. These are separate next gates after SS phase.
10. Keep all 382+ records and original 16 classifications, mark resolved subcases only, publish exact exceptions/unvisited code paths honestly; never claim “100% canon” or a full retail campaign on the basis of bounded traces.

## Deliverables and no-integration guard
One **isolated C1-R3 research/proven correction** (or evidence-led no-change hold if camera cause remains unresolved): updated ROM-wide matrix & findings register, original-RAM vs GameMaker phase tables/screenshots, preserved SS1–SS5 corrected first Y, SS5 original failing-to-pass or honest remaining FAIL, a minimal Classic-only source patch if justified, native Window trial + full source/evidence/receipt/H: if code changed. Do not manufacture new executable or commit for no-change study if previous valid C1-R2 source stands.

**No automatic C1→S6 merge, production Classic replacement, private/public Git push, release, tag or Chief physical campaign test.** After R3 report, Manager will decide next separate C1 gates for pool ownership, attract demos, VDP mask & PAL/NTSC timing, and wider 18-act coverage; Chief will eventually accept Classic only after original evidence and controlled integration.

**C1-R3 IMPLEMENTATION/RESEARCH GO. Production Classic replacement remains HOLD.**

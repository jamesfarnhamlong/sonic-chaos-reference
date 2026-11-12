# Sonic Chaos — C1-R8 Original Sign/Boss Camera Owner Transfer: Manager Closeout

**12 November 2026 · Manager-san #11 · ORIGINAL OWNER RULE CONFIRMED IN CONTROLLED ROM WINDOWS · RESEARCH PASS / NO-CODE HOLD · CLASSIC REPLACEMENT HOLD**

## Review provenance / custody
Chief delivered and Manager read the full private Markdown report `C1_R8_CAMERA_OWNER_TRANSFER_20261112.md`. Manager has **not** independently executed original ROM/GameMaker traces, inspected the complete private `camera-ownership-decision-matrix.json`, evidence ZIP, receipt or H: recovery. The findings are grounded in source/report descriptions and agent-reported tests, **not independent Manager execution**.

- Private report: `E:\AI\Codex\Sonic Chaos\management-audits\c1-20261112\r8\delivery\C1_R8_CAMERA_OWNER_TRANSFER_20261112.md`.
- Private matrix: `E:\AI\Codex\Sonic Chaos\management-audits\c1-20261112\r8\camera-ownership-decision-matrix.json`. Adjacent private evidence ZIP and receipt retained locally by Designer.
- Isolated C1-R8 branch `classic/c1-r8-camera-owner-boundary-20261112`; **no runtime edits/source commit**, exact unchanged R3 HEAD `b667cc5cebcd3c3e047d9f527cc78b76e1e027f0`, tree `ffdfc37e23d1b18e866b8beae051234c443b9665`. R4/R5/R6/R7/R8 are evidence-only branches.
- Protected original Classic historical tag, immutable Enhanced S6 local source `47c501ecb994a4fcb1eeac1c29793f3f1142a304`, all R1–R7 reports/packages, E:/H: independent source Git and 22 ignored original deps preserved per Designer. No shipping Windows/source trial, merge, push, release, tag or new Chief C1 playtest.

## Core ROM result — exactly what happens at owner takeover
Original `$16B8` driver prepares camera via `$4C90` BEFORE player `$361D` and objects `$5DD1`. Original sign/THZ boss callbacks in the object phase write **new pan owner/target, D15F flag and bounds** without writing camera pending registers **D284/D286**; VBlank `$0570/$057C` copies the ALREADY prepared pending X/Y into committed camera **D174/D176**. The new owner/bounds influence **the NEXT update's camera preparation**, not the current commit. This includes a ROM-authentic quirky right lock where the previously prepared camera X can momentarily be beyond the newly tightened bound: must preserve in Classic, no post-object reclamp/fairness correction.

R8's bounded original ROM update/activation records (controlled approaches with disclosed player-position/velocity guide only *before* evidence windows; original ROM instructions/registers/owner targets not injected; not complete natural campaigns):

| Original activation | Original update | Prior committed camera | Prepared camera | Object-phase new owner/target | VBlank commit |
| --- | ---: | --- | --- | --- | --- |
| Sign contact/pan | 586 | 3821,449 | **3825,449** | sign bit0, target3832/405, left3821 | **3825,449** |
| THZ boss creation/left lock | 279 | 1603,126 | **1607,126** | left1603, boss next1 | **1607,126** |
| THZ boss trigger/right lock | 293 | 1659,126 | **1663,126** | right1659, boss next2 | **1663,126** |
| THZ child-gated pan | 379 | 1663,126 | **1663,126** | bottom78, target1680/78, sign bit0 | **1663,126** |

All **20 original window updates** show no object-phase pending-camera writes (including same-value writes), and prepared values match final committed view. Sign next update587 commits3826/448; THZ pan next update380 commits1664/125. Thus the previously open **commit-vs-replace-vs-discard original rule is SOLVED for these sampled owner transitions**. Do not overgeneralize to all six bosses, death/respawn, results, late screens, PAL/NTSC or cycle accuracy.

## Why GameMaker implementation still cannot safely proceed
Designer obtained compiled native **semantic** owner transitions, not original-aligned absolute simulation:

| Native controlled activation | First relevant result | Difference from original |
| --- | --- | --- |
| Sign state3→4/pan | sign Step activates pre-player; End Step immediately pans | Original sign contact activates AFTER player in object phase, so prior pending view should commit first |
| THZ boss mode0→1 | boss activates; new boss follow applies after player this End Step | Original before-player pending persists and commits despite changed bounds |
| THZ mode1→2 | post-object right lock selects helper | Prior original prepared camera may outlive newly tightened bound for one update |
| THZ mode2→3/pan | new pan immediately steps this End Step | Original pan first steps on NEXT preparation |

Native controlled **boss setup gains +7px Y in its first player/terrain update**, and sign's native Step can execute before the player's adapter despite ROM sign contact later in `$5DD1`. Initial state/owner/collision/placement cadence differ in these controlled setups. **Exact numeric original/native activation alignment remains incomplete**. It's unsafe to port the original phase in a blind adapter hook, shift the entire zone End Step or add a compensating one-pixel camera offset. The next work is **native event ownership architecture**, not more original register research.

**R9 was a DESIGN-ONLY PROPOSAL in the agent's report, not a production source patch, not yet commissioned by Chief/Manager.** Its proposed shape is Classic-only:
1. Prepare pending camera candidate at a defined **entry-owner** phase before player/objects, using prior committed view/lead/limits and any already-active owner.
2. Allow object/sign/boss activation to write owner/target/bounds for **the NEXT update**; do not cancel, overwrite or re-clamp the already prepared candidate.
3. Commit that candidate after objects; preserve separate sign/boss/result/SS/Enhanced owners and block guessed behavior in unverified transitions.
4. Need specific **native player/object phase and sign Step placement plan**, particularly boss seed's +7 Y and sign before-player activation, to make implementation safe. Full absolute equivalence still absent.

The report explicitly recommends **NO implementation GO** on current native alignment. Manager endorses no-change. Do not commission a series of essentially identical camera instrumentation tasks; **stop this particular R7/R8 research line here**. Before revisiting code, require an independently reviewable minimal ownership/scheduling design, with guarded original-effect boundaries and regression handling for sign, THZ boss, other bosses and death/level transitions; alternatively pause this integration stream and pursue a different concrete Classic divergence.

## Preservation, unresolved defects and project status
R8 reports fresh exact tests: **Enhanced S6 10,542 native state samples/102 images**, C1 Classic native256×192 **138 captures** +30 UI scale, R2 Special Stage initial registration controls, R3 five-stage500 camera and SS5 settled clock145 comparisons, explicit-mode SS4 22,742. Sign-prize 7,845 and boss result/rollover19,674 source-host assertions repeated as **regression controls only**, not original/native owner equivalence. H: source/evidence independently recovered; all test observers/restoration cleaned up.
- Raw death harness missing `chaos_m2d_vy_value` ERROR, raw GPZ camera cap FAIL and THZ clear camera step FAIL remain; historical raw SS4/SS5 similarly not reclassified.
- **Tails early animation counter** ROM `8,8` vs native `8,7` at update2 (same source frame/positions) remains separate possible canonical mismatch, not a demonstrated visible error.
- **Shared original first16 object slots/pending FE/FF owner reuse**, **palette-aware left8 VDP mask with unresolved visible-frame/fade phase**, three original **attract demos absent** (input/driver/rotation research completed), original IRQ/physical PAL timing and full original 18-act/5-SS route/ending/rare audio coverage remain OPEN.
- Strict user mode contract: **true 256×192 Classic reproduces ROM quirks exactly, NO QoL**. Protected S6 348×196 Wide Enhanced with future optional gameplay QoL OFF must remain exactly unchanged. Chief's S5–S7 owner test 33 PASS/4 inaccessible UNOBSERVED; Chief will supply six144×128 Save TV art PNGs, generic GameMaker Pause redesign wholly parked.

## Manager disposition / suggested strategic next move
**C1-R8 ROM rule established and research PASS; no-code hold ACCEPTED. C1 production Classic replacement / C1→S6 merge HOLD.**

Answer to Chief's question “any closer to resolution?”: **Yes—original pending-camera owner precedence is no longer unknown**, closing the key original-ROM uncertainty from R7. But **the actual GameMaker-native event-order/first update mismatch has not been safely resolved**, so no claim of practical release proximity or 100% original parity follows. At least one guarded architecture/design decision remains for ordinary camera; several independent Classic gaps remain. Recommended **PAUSE camera instrumentation**, not automatically approve R9 code. Reassess source-level integration design as a discrete decision or switch to a more local actionable ROM-correct difference (e.g. Tails early animation counter) before returning to broader Classic completion. Do not ask Chief for original-vs-GameMaker **attract demo** comparison until native authentic replay actually exists.

# Sonic Chaos — C1-R7 Authentic Retail Entry and Camera Handoff: Manager Closeout

**12 November 2026 · Manager-san #11 · RESEARCH TECHNICAL PASS / NO-CODE HOLD ACCEPTED · CLASSIC REPLACEMENT HOLD**

## Actual source of review, identities and limits
Manager received/read Chief-uploaded complete Markdown **`C1_R7_NATIVE_RETAIL_ENTRY_HANDOFF_20261112.md`**. This assessment is grounded in that report; **Manager has not independently executed Windows GameMaker, the original ROM, raw alignment JSONs, the evidence ZIP, or receipt/H: recovery**.

- Isolated C1 project `management-audits/c1-20261112/project/SonicChaos.yyp`; branch `classic/c1-r7-native-retail-entry-20261112`.
- **Exact unchanged source HEAD `b667cc5cebcd3c3e047d9f527cc78b76e1e027f0`**, tree `ffdfc37e23d1b18e866b8beae051234c443b9665`. R4/R5/R6/R7 are evidence-only/no-code branches; do not invent a C1-R7 source commit or Windows shipping ZIP.
- Private local R7 report: `E:\AI\Codex\Sonic Chaos\management-audits\c1-20261112\r7\delivery\C1_R7_NATIVE_RETAIL_ENTRY_HANDOFF_20261112.md`. Private receipt: `SonicChaos_20261112_C1_R7_RETAIL_RESEARCH_RECEIPT.json` in same delivery directory. Original EU v1.2 ROM SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
- Original protected S6 Enhanced source remains `47c501ecb994a4fcb1eeac1c29793f3f1142a304`; frozen historical Classic tag `classic-core-20261105` untouched. C1 H: evidence, Git/source and all four ignored runtime dependencies +18 PNGs independently restored/checked **per Designer**, not Manager reexecuted; no merge, push, tag, release, production change or Chief physical C1 playtest.

## Genuine compiled Classic retail path observed (not a debug stage hop)
The R7 `build_probe.py` injects **trace-only** observers into a temporary native Windows compile, byte-restoring test resources/source afterwards. Its primary run goes: PC outer Classic selector → opening → original title → original character-select → legitimate `chaos_run_new_game(choice.cursor+1,ROM_chaos_thz1)` → THZ1 Create/player/object/camera/draw. It does **not** use direct room jump, debug loader, state injection or Level Select for these primary two runs. Probe event timeline is outer selector1, committed Classic53, opening54, title832, character choice1013, new-game1208, THZ1 room1209 (probe ticks **not** original ROM frame counts). Menu edges were supplied at frontend/input boundary and focus-only hidden-window gate bypassed; test speed **240 updates/s**. This is **real compiled retail-route execution** but **not literal unmodified physical controller/no-input timing or PAL/NTSC 50/60Hz testing**.

Sonic and Tails each have **180 player updates**, 180 adapter imports/registrations, native pre/post-core, objects, ordinary camera and presented draw observations. R6 original ROM controls were paired to GameMaker by named source phase and corresponding held/action inputs, yielding **360 paired rows**, with original D373, D498..D49F state0 initializer/animation details also traced.

## What is now properly equivalent
- Player raw position **pre/post callback matches in all 180 entries for both Sonic and Tails**; no recurring first-update five-pixel registration mismatch here.
- Effective initial max speed matches ROM `$0400` = **1024**, and initial facing flags match after mapping GameMaker's initializer to original state0 effects. Original `state0/next0` vs native wrapper `state1/next1` is *not itself* proof of a missing initializer. Do not rename native state1 to0.
- Sonic source-shade animation counter matches all 180. Native Tails differs from original at **update2**: original first two counters **8,8**, native **8,7**, with same pointer8A3E. Likely different state0→state1 reload vs direct native state1 decrement; this is a **specific counter difference needing separate causal probe** and possible terrain/ring probe timing implications, **not demonstrated visible frame/player position error** in the current 180 rows.
- Original input held/action matches all 360; original direction pressed edges at updates36/81/121 not copied to native action-only pressed field. Record as byte-semantic difference, not automatically player-physics FAIL or complete original pressed-byte equality.
- Original character probe extents FFF7/FFF4/0009/FFF4 are mapped to different native sensor/mask ownership; complete cross-path shape parity remains **UNVERIFIED**, despite bounded matched positions.

## Genuine camera divergence and blocking owner boundary
Original camera primitive previously modeled **2,160/2,160 pre-player leads/pending** correctly in R6, but actual GameMaker ordinary follow runs post-objects within zone End Step. R7 proves actual original/native paired THZ1 first divergent lead **update1 Y120 ROM / Y119 native**; first committed displayed camera differs **update13 ROM (38,530) / native (38,531)**; pre-core update14 consumes differing previous committed view. This is an actual compiled ordinary camera output mismatch even after equivalent initializer mapping, but the first displayed 1px difference is **not sufficient to justify moving the entire End Step**.

`camera-owner-map.json` and report classify separate End Step sign, THZ, GPZ, MGHZ, SEZ, EEZ, AQZ owners, dynamic bounds, boss locks and sign pan. Post-object sign/boss predicates can change during the **same update**. Precise missing proof: **when object code activates sign/boss ownership, does original pre-player pending camera work (a) commit, (b) get replaced by new owner, or (c) get discarded?** Need original ROM original pending/committed registers and native owner activation at **same update**, with before-player eligibility and after-object eligibility. Without that, a source relocation could regress original boss/goal behaviour. Do not implement a one-pixel camera shim or unconditional early camera-commit.

Cached original source-host sign prizes **7,845 assertions PASS** and five-boss result/rollover **19,674 PASS** are valuable regression controls, **NOT proof of compiled original-equivalent same-update owner handoff**. Other raw test statuses must remain visible:
- Raw death harness **FAIL/ERROR** at missing `chaos_m2d_vy_value`.
- Raw GPZ camera cap assertion **FAIL**; explicit-mode in-memory control did not cure.
- Raw THZ zone-clear camera step X6 vs cap4 **FAIL**; explicit-mode control did not cure.
- Raw old SS4 and SS5 verifiers remain **FAIL** under prior mode/timeline differences even though exact R2/R3 isolated tests pass.

Natural compiled goal-sign release, THZ boss takeover, death/respawn, Continue, act transition and new GPZ/MGHZ/EEZ starts are **UNVERIFIED**, not presumed accepted from 180 initial THZ samples.

## Preservation and honest overall status
On unchanged exact R3 source, Designer reports **Enhanced S6 10,542 state samples +102 images exact**, Classic **23 rooms×2 characters×1/2/3×=138 native256×192 captures** plus30 frontend scale outputs, R2 SS first anchors ten checks, R3 original SS camera500/SS5 settled clock145, explicit-mode SS4 22,742 assertions PASS. Full existing ROM-wide **382 coverage records and16 findings** annotated; original mask from R4, attract replay from R5, first16 shared object slot ownership and other original ROM paths remain open. Preservation and exact H: recovery reported verified; no code/push/release/Chief check.

**Manager verdict: R7 isolated original/native first-180-update retail phase proof ACCEPTED. No-change production hold ACCEPTED. C1 Classic replacement and C1→S6 integration HOLD.** Classic continues to follow **exact original ROM, including quirks, no QoL**. Chief's 33-passed/4-unobserved S5–S7 Enhanced owner acceptance is separate; Pause redesign parked; Chief generating six 144×128 Save TV source PNGs.

## Next bounded action: R8 sign/boss takeover decision boundary only
Authorize **one instrument-only**, tightly scoped ROM/original-vs-compiled-native comparison for **goal-sign activation and THZ boss camera takeover at the exact object→camera-owner transition**, to determine pending-camera commit/replace/discard. Reuse R7 existing compiled retail observer and R6 stabilized original hook reference; no broad fresh 18-act camera/timing census. Need at least original before-player/pending, after-objects owner/guard and VBlank-committed camera for the **first activation update and adjacent control updates**, with native same owner flags/mode/bounds and source line map. Do not apply an ordinary camera code fix in R8; return a decision table and phase-equivalence evidence. If natural route cannot be observed, state exactly why and one bounded alternative, **not indefinite re-runs**. If owner semantics are proven then Manager may authorize a separate minimal original-correct Classic-only camera correction sprint. [R8 binding evidence sprint](C1_R8_SIGN_BOSS_CAMERA_OWNER_BOUNDARY_SPRINT_20261112.md).

Tails animation counter update2 is a **separate known subcase**, not in R8 implementation. Authentic original attract playback remains downstream of ordinary native camera/entry/driver equivalence; Chief offered eventual side-by-side **attract demos**, not unrelated gameplay testing, so no human comparison requested now.

**R7 RESEARCH PASS / NO-CHANGE HOLD; R8 INSTRUMENT-ONLY OWNER TRANSFER GO; CLASSIC REPLACEMENT HOLD.**

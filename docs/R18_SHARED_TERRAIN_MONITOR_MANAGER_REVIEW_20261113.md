# Sonic Chaos — R18 Shared Terrain-Monitor Collision Repair: Manager #12 Delivery Review

> **NEXT STEP REVISED BY CHIEF (13 NOV 2026):** Manager has [commissioned R19 P1 source implementation](R19_CLASSIC_FULLSCREEN_BOTH_TITLE_QUIT_ENHANCED_LIVE_SETTINGS_20261113.md) in an isolated branch from this R18 source **while Chief physically tests R18**. This is permission for source work, **not a declaration that Chief physically passed R18** or authorisation to merge/release production. R19 must retain R18's shared THZ TV-chain correction.

**13 November 2026 · P0 SOURCE CORRECTION DELIVERED · PRIVATE CHIEF PHYSICAL F5 GO · PRODUCTION HOLD UNTIL CHIEF PASS**

## Exact source, custody and evidence provenance
Chief uploaded and Manager read the full private R18 delivery report and the THZ override audit. Manager did **not** independently launch the local Windows ZIP, review the private GML/source diff/raw original emulator traces or reproduce H: package recovery; all counts below are Designer-reported. The report and audit are valid sources of a bounded technical review, not proof of an already passed Chief F5.

- Local R18 branch `core/r18-monitor-dash-collision-20261113`, full source SHA **`050ee0d6e2d947ae068e443703eb7b40d2d052f1`**, tree **`f7c3bac483829063479084164e35631affcbc9ad`**; R17 base SHA `86d5414a7eedf47108149f742c8080d6271499e3`, tree `499fd983eb4e6817f7e589a20a7483ba712c6c7f`. Two runtime files changed:3 insertions/52 deletions; one source note added. Private package names: `SonicChaos_Windows_20261113_R18_MONITOR_COLLISION_PRIVATE.zip`, `SonicChaos_Source_20261113_R18_MONITOR_COLLISION_PRIVATE.zip`, `R18_DELIVERY_REPORT.md`, `THZ_OVERRIDE_AUDIT.md` and `SonicChaos_20261113_R18_SHA256.txt`; Chief supplied private local E:/paths, not a GitHub production release.
- Original ROM EU v1.2 SHA256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. R18 ROM comparator boots actual original game through New Game/character choice but **controls** initial player/camera position and logical charge inputs; these are controlled original-game scenarios, not the Chief's full physical ROM playback.
- Separate `R18TRIAL_` save/INI/diagnostic names at packaging; canonical source restored after transform; no observer in shipped executable. Independent H: Git/source/22 dependencies archive check and protected real save hashes reported PASS. Accepted production S6, R17 previous candidate, R12/R15/R16, private sources and packages unchanged. No merge/push/tag/release.

## Root cause: THZ had a special-case bypass, not missing general dash physics
Real THZ1 ring-TV terrain row = **surface `$16`, tile `$47`**, distinct from mapped type-`$10` monitor entities. Three pieces of obsolete local code disrupted ordinary attack resolution:
1. Legacy `SCR_chaos_block47_step` was a four-cell swept THZ monitor collision override called before normal terrain probes and **excluded released spin-dash state `$10`**.
2. Two `zone != 0` predicates prevented the existing generic surface-`$16` floor/side monitor handlers from processing THZ.
3. Result: native Sonic charged motion at X3321.671875/VX1768 was side-projected to X3319.671875, then next tick VX zero and roll attack cleared.

R18 **removes the obsolete override/call and the two THZ dispatch exclusions**; existing common terrain-monitor break handling now performs shared floor/side processing in THZ. First changed build exposed previously uninitialised THZ break ledger; R18 initialises it on first use. No speed restoration shim, artificially nonsolid monitors, new stage-offset patch, guessed attack state, altered input stream or two-monitor special exception.

## Focused original and actual compiled gameplay verification
- Controlled original and compiled near/far charged dash first **30 updates after release exact for position, velocity, current/requested state and move/attack flags**. Four THZ terrain TVs break at updates **6,11,15,20** from near release. Horizontal speeds at breaks: **1768,1748,1732,1712** in original/GameMaker and ordinary **4/256px per update** deceleration continues, instead of zeroing at first/second impact.
- **44 successful focused compiled cases** for both Classic256×192 and Enhanced348×196: near/far single, two/three/four terrain TVs, mapped type-`$10` TVs, normal support and running, solid wall, Tails charged roll and Sonic Peel-Out; **14 supplemental compiled** roll/jump/short-charge tests not miscounted as separate original oracle checks.
- Distinction confirmed: original Sonic **Peel-Out is NOT a roll attack** and stops at intact monitors; original Tails charged roll breaks TV chains. Mapped TVs' projection/top support byte-identical to R17. Shared source-host support verification75,805 asserts (35,920 projected,1440 monitor callbacks) is supplemental to actual compiled charged-dash proof.
- Post-change preservation reported Enhanced10,542 state samples exact and102 images (94 unchanged vs S6,6 intended Chief TV pictures,2 intended R15 Pause), Classic138 gameplay+30 frontend exact, R2/R3, R10, R13/R14, demo12,948 observed actions same as R17, Pause614 assertions. Historical raw host errors/fails remain documented, not made into PASS. New expected changes in previously broken THZ contacts are genuine **corrections**, not baseline-regression failures.
- No entire GameMaker source audit/full Sonic/Tails campaign or Chief physical-controller R18 acceptance is claimed.

## THZ override audit outcome: bounded and honest
`THZ_OVERRIDE_AUDIT.md` surveyed runtime zone-zero special cases and found **no other THZ-only monitor break/attack bypass in the inspected source execution paths**, not universal absence of legacy code. Remaining:
- `OBJ_CHAOS_mask_07/Step_2.gml`: legacy GameMaker one-way mask solidity; normal player uses ROM decoded terrain profile. Some other consumers may use mask. Don't remove without a real observable issue.
- `OBJ_chaos_terrain_3/Draw_0.gml`: four-cell overlay reads mutable map to draw broken TV terrain; it is presentation, not attack enforcement.
- `SCR_cc_spring`: **intentional original ROM** THZ diagonal spring impulse -7.0 vs elsewhere -5.5; MUST NOT simplify as dead code.
- THZ source-original layouts, loops, rendering/filter/fragment decisions remain meaningful.
- Sample-engine `OBJ_monitors` contact bridge in adapter is still present but nonattacking/airborne gated; may be vestigial, **not proven safe to delete**. [Separate risk-ranked audit note](POST_R18_LEGACY_GAME_MAKER_ADAPTER_RISK_REGISTER_20261113.md) parks cleanup until after Chief verifies core fix and P1 interface blockers.

Do not assert prior developers or AI agents necessarily wrote deliberate shortcuts without source-history proof; code was obsolete relative to today’s shared handler, but its original purpose may have been a temporary adapter. A blanket cleanup could reintroduce significant bugs.

## Manager decision and only immediate Chief action
**R18 SOURCE IMPLEMENTATION REVIEW: TECHNICALLY ACCEPTED FOR PRIVATE CHIEF PHYSICAL TEST.** Production integration and new feature work remain HOLD pending Chief result. One short F5:
1. In private R18 ZIP choose Classic Sonic THZ1 upper-route ring-TV row. From close and long release hit one TV, confirm break and continued charged-roll motion.
2. Fresh test: charged spin dash through at least two consecutive TVs without stopping; optionally 3–4 if easy.
3. Repeat those actions in Enhanced 16:9; stand on an intact TV and ordinary-jump contact/solid wall briefly.
4. Compare with the original ROM if new arrangement still stops, reporting precise screen/approach for targeted review. No full 18-act test required.
On owner PASS, close P0, authorize one P1 interface batch (Classic fullscreen, both title Quit to Desktop, Enhanced Pause live settings); then a bounded attract-tail check and small Chief-chosen Enhanced extras shortlist. On FAIL, one narrowly scoped R18 corrective source iteration. **No production merge or release just from these automated results.**

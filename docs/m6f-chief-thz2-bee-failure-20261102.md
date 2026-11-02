# M6-F — Chief split verdict and THZ2 bee correction (2 November 2026)

## Owner F5 decision

Chief tested M6-F at POC a70? Exact candidate: 70cac5dea79e5e81fb88513effec367cb1af4d0c, direct child of Chief-accepted M6-E a4c26e13bc323a9f736c613c279b447dd6aedef5.

**RINGS — CHIEF PASS.** High-Y GPZ3 scattered rings persist off the top and return for recovery. Chief considers it now perfect. Freeze the M6-F ring change; do not require another GPZ3 human check.

**ENEMIES — CHIEF FAIL.** Many temporarily departed enemies still respawn at their starting coordinates/phase. Critical precise test: **THZ2 flying bee above two columns**. After engaging bee, Sonic/Tails drops between columns and springs back up: G2/M6-F bee resets, original ROM retains it. Following it right while remaining below, moving off-screen and returning: again POC resets, original continues same bee/patrol. This is the only REQUIRED Chief retest after correction. M6-F as a whole is **NOT CHIEF ACCEPTED**. The last fully accepted production SHA remains M6-E.

## Strong code-level hypothesis; needs exact route proof

At M6-F:
- scripts/SCR_chaos_placement/SCR_chaos_placement.gml: chaos_enemy_retention_cell enforces a camera-relative 512px horizontal and 128px vertical envelope for previously-awoken wide enemies. Outside Y envelope -> cell3.
- objects/OBJ_chaos_object_27/Step_0.gml: after the update, cell3 removes an **already-triggered** state2/3 bee in wide mode if chaosWoken. The subsequent placement scan can recreate it at chaosOriginX/Y, resetting state, velocities, age and oscillator phase.
- Original [object $27 audit](object-27.md) and [viewport semantics](viewport-semantics-audit.md): after the proximity trigger sets flag bit1, original generic $61E1 off-range processing protects the object from ordinary deletion. Later state3 $8A29 removal is tied to abs(playerX-beeX) >=384, **X-only**, not camera Y. Original out-of-range can still pause callbacks (bit6). Distinguish preserving identity/phase from optional continued offscreen simulation; use a labelled PC widescreen QoL rule if continuity requires it.
- The broad M6-F alias tests did not specifically recreate Chief's THZ2 drop-between-columns and follow-from-below sequences. Earlier source pass does not override this natural F5 FAIL.

## M6-F-R1 authorized correction, one consolidated outcome

Branch poc/m6f-r1-bee-vertical-retention directly from M6-F candidate 70cac5dea79e5e81fb88513effec367cb1af4d0c, **not** from M6-E, to retain the Chief-passed ring improvements. No main merge.

1. Derive exact THZ2 generated type$27 instance and two-column route from map + original ROM; paired original and shipped-GML traces. Trace SAME bee identity and placement occupancy, cameraX/Y, playerX/Y, world position, velocity, state1/2/3, triggered bit1, chaosWoken, chaosAsleep, active/deleted, oscillator/counter, exact cell and cause of recreation through drop, spring ascent, right chase and below-screen return.
2. Demonstrate the first divergent update and confirm/refute the Y-bound hypothesis. Correct **triggered-bee identity and state retention** across ordinary vertical camera departure without arbitrarily immortal entities. Preserve original pretrigger spawn/deletion, state3 X separation semantics at native256, original behavior of sleep vs callback motion, sprite visibility/contact, defeat and placement slot ownership. If implementing a PC wide continuation mode, specify bounded finite lifetime or appropriate player/world anchors without recreating the original vertical bug. The requirement is the **same encounter/patrol**, not simply a visually identical respawn.
3. Extend focused tests to THZ1 and THZ2 $27, GPZ/EEZ $2C shared flying guises, state2 oscillator, state3 travel, horizontal departure and backtrack, vertical camera follow, native256 parity and full damage/defeat and room reset. Do not alter bosses/hazards/general viewport bands.
4. Lock the working scattered-ring source and rerun its focused GPZ3 regression **internally once at final integration**; no extra Chief ring retest or tiny candidate ZIP. Preserve M6-E character select, M6-D km/h/removed shortcuts, M6-C2 opening and native audio; all assets/resources.
5. Chief's budget: cheap targeted original ROM/GML tests during development, one integrated risk-focused final suite, **one private source ZIP and one short Chief F5** of the exact THZ2 bee two-column and follow-from-below scenarios. No repeated GameMaker compilation, Runner623 debugging, per-bee previews or broad human check.
6. Return source-backed before/after per-update evidence, remaining hard-retire policy, test outcomes (including raw inherited FAILs), unchanged ring behavior, exact clean remote commit and private artifact/integrity receipt. A source-only PASS is not native acceptance.

**Current project priority:** M6-F ring PASS, enemy FAIL, overall HOLD pending R1. Full playthrough follows acceptance. Attract demos/save/AQZ Tails palette/MGHZ3 visual/startup onset remain owner-parked.

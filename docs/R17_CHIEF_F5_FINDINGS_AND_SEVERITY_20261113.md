# Sonic Chaos — R17 Chief F5 Actual Gameplay Findings and Priority
**13 November 2026 · CHIEF PRACTICAL FEEDBACK · PRODUCT ACCEPTANCE PARTIAL / CORE COLLISION P0 FAIL · PRODUCTION HOLD**

## Provenance
Chief actually ran the combined private R17 Windows package and supplied the results. This is **human observation**, distinct from Designer's compiled 10,542-state baseline/138-image preservation and 614 Pause assertions. Manager verified the historical project conversation context of the earlier October monitor report; Manager has not personally executed Chief's local R17 executable.

Exact R17 source `86d5414a7eedf47108149f742c8080d6271499e3`, tree `499fd983eb4e6817f7e589a20a7483ba712c6c7f`; parent R15 `c7af4937358097063e19732773ef5bfdd3e4bc5b`, original R16 donor `11e41afb8c02f7372ed0872421a2b5f29d420749`. Private trial namespace; protected production unchanged.

## Chief's explicit result and severity
| Area | Chief outcome | Next action |
| --- | --- | --- |
| Classic three-demo mechanism / cancel / New Game HUD+controls | **PASS**, THZ/GPZ/SEZ and repeat; visual route **roughly 90%** against Fusion on recheck, later differences and occasionally awkward stops | Low priority bounded later tune only after core fixes |
| Classic 256×192 gameplay / simple Pause / minimal Quit | **PASS** for game/pause; **FAIL** when maximizing Classic window: window is repositioned, not true scaled fullscreen | **P1** Classic display/window-mode fix after P0 core |
| Enhanced Pause six entries/icons, gameplay options/quit | **PASS** basic, BUT displayed option states sometimes differ from choices applied at boot: current live state not reflected | **P1** use actual applied host/presenter live-state in UI instead of stale stored preference |
| Physical controls/audio/relaunch/settings | **PASS** per Chief's checked checklist | Preserve |
| Six 144×128 Enhanced Save TV previews, five-TV save/load/erase flows | **UNOBSERVED by Chief**: no complete save to examine all zones; Chief saw Designer's captures and thinks fine | Defer Chief visual check to natural full run, do not treat as FAIL or fully owner-certified |
| Enhanced title Quit | **MISSING USER-FACING FEATURE** explicitly requested after Chief's first feedback | **P1**, add actual Quit-to-Desktop entry in Enhanced title, with safe cancel/confirm if appropriate, preserve Classic title |
| **Spin dash / charged rolling attacks versus TV monitors** | **P0 FAIL, blocks production and additional QoL**. Sonic's dash breaks at most one TV then stops against second; even a single TV can halt Sonic when launched farther away. Chief compared directly with original ROM; not canon for this scenario. Both Classic & Enhanced affected. Super Peel-Out and Tails variants need original rule checked, not assumed. | **IMMEDIATE R18 CORE COLLISION REPAIR** |

Chief requested **NO other changes before fixing P0**. A passing Enhance 10,542-state/Classic138 preservation suite does not establish correctness of **charged-dash monitor impacts and multi-monitor chains** if those specific interactions were absent from its coverage. It may have faithfully preserved an older bug.

## Critical earlier history and accountability
Chief had already reported **2 October 2026**: `spin dash doesnt break boxes from the side (stop dead)` in a THZ1 monitor row. A narrow follow-up source report classified some contact geometries as original arrangement-dependent based on projection/contact ordering (e.g. original `$5FA0` before attack): **that did not reproduce the real same-position full-charge multi-monitor case Chief now ROM-tested**. Other October work repaired SS1 monitor support/top projection; later November AQZ black-smoke monitor-Draw registration fixed presentation. These targeted improvements did **NOT** prove charged high-speed movement through consecutive TVs. Earlier general source-host/pixel conservation checks passed but never certified this specific natural interaction. We should not repeat 'canonical' reassurance based on narrow adjacent tests.

**Corrective policy:** Real hardware/ROM comparison for actual same charge, position, approach, TV arrangement before asserting canonical; actual compiled native collision-state/velocity/attack flags/collision resolution across first AND second TV; verify both modes and relevant player attacks. Investigate shared contact/break/solid-resolution order and potential stale collision from removed object. No blanket monitors non-solid (would break original top standing support); no arbitrary instant speed restore or test-specific offset. Match original practical gameplay.

## Next jobs and acceptance gates
1. **Immediate [R18 P0 charged-dash monitor collision correction](R18_P0_SPINDASH_MONITOR_CHAIN_CORE_COLLISION_REPAIR_20261113.md)**, isolated from protected R17 source, both modes. Agent must deliver a changed compiled playable candidate, focused original/native case tests for near/far and two+ successive TVs, preserved normal monitor/support/Special Stage behavior, small Chief physical reproduction guide. Chief test must specifically pass before further feature/presentation implementation.
2. **Only after P0 Chief PASS:** one **P1 display/user-interface correction batch**: Classic maximize/fullscreen genuine scaling with 4:3 letterbox/pillarbox and nearest integer presentation, Enhanced Pause toggles reading *applied live* host state, Enhanced title screen Quit to Desktop (controller/key usable). Chief's Saver artwork validation can wait for natural full campaign; do not force a full save merely for screenshot parity.
3. Demo earlier cutoff/accelerated third stage playback and occasionally stopping remain **P2, practical polish**, not priority ahead of TV collision or P1. Unknown cause not assumed identical to original IRQ; no new exhaustive IR​Q census. R17 review of implementation still technically valid, but **Chief production acceptance is HOLD** until P0 corrected and owner verified.

**No production merge, release, tag or unattended source push.** Chief personal GameMaker translation practical fidelity contract remains the target.

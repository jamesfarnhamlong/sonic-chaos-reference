# Sonic Chaos — S3 Boss Rush Integrated Candidate: Manager #11 Delivery Review
**6 November 2026 · Manager-san #11 · TECHNICAL DELIVERY GO FOR CHIEF PLAYTEST, NOT CHIEF ACCEPTANCE**

## Provenance and protected baselines
- Source report supplied privately by Designer: `S3_BOSS_RUSH_20261105.md`, dated 5 November 2026. The report cites S3 authority blob `b7b3e3a54c68ff8cc567b11a0110a25df1a3716d`.
- Candidate commit **reported only in abbreviated form**: `7a6a4b7`; request the full commit and branch at archival/acceptance, and independently check remote/local availability when accessible. This review did **not** fetch Chief's private E:/H: ZIPs or native screenshots and did not independently rehash them.
- Local accepted Enhanced S2 source parent reported `0809ef9cbc9ea9c1fda3bc0ead45aa9aa749a5a7`; original frozen Classic tag `classic-core-20261105` points to `3a58912659b48573ac7f2c5c96a02a2211d5e4da`. No merge, retag, publication or Chief acceptance is authorized.
- Chief-facing Windows ZIP: `SonicChaos_Windows_20261105_S3_BOSS_RUSH_CANDIDATE_PRIVATE.zip`; source ZIP: `SonicChaos_Production_20261105_S3_BOSS_RUSH_SOURCE_PRIVATE.zip`; Designer's private report and SHA-256/H: recovery receipt accompany them.

## Delivered design versus binding S3 brief
- Enhanced title `START` followed immediately by `BOSS RUSH`; START retains five-slot Data Select, Boss Rush goes directly to Sonic/Tails select and one LEVEL 7 introduction. Classic original title remains unchanged.
- One 9,632-pixel predominantly horizontal course in THZ→GPZ→SEZ→MGHZ→AQZ→EEZ order; five 192-pixel original-floor-column connector segments; original GPZ loop/steps and substantial approach geography retained. First two connectors step upward, later ones level.
- One EEZ tile-205 background throughout; eight challenge-only recoloured terrain atlases for THZ/GPZ/SEZ/MGHZ; AQZ/EEZ tiles rendered under EEZ CRAM through existing palette shader; original bosses, water and hazards remain functionally legible per Designer's claim. Actual referenced screenshot assets were not included with the uploaded Markdown.
- Original Act 3 boss room identity/local coordinates retained behind hidden connector-midpoint handoffs, preserving player fractional motion, animation, camera, rings, time, blink, powers and effect phase. No repeated intro/fade/results at joins.
- Challenge: both characters start with three lives/no continues, no checkpoints; full-course death restart; fifteen single rings (3 at entry and 3 in each of first four connectors), source THZ ring monitor/GPZ invincibility monitor retained; no added rings in AQZ→EEZ connector. Full Sonic final EEZ eligibility is temporary session/boss-local, never a campaign Emerald grant. End displays BOSS RUSH CLEAR and title/restart choices.
- MGHZ optional lower terrain pruned at local Y >= 512, challenge-only pit boundary; required special platform, tree, spikes and original combat-camera fatal anchor Y464 preserved. Human fairness judgement outstanding.

## Engineering evidence supplied, not independently rerun
- 11,307,008 collision-profile samples; all five joins checked in local/course coordinate contexts.
- 12 boss/player controlled scenarios (both characters × six) with 228 captured states at each 348/290/256 width = **684 matched states** against accepted S2.
- 15 compiled-native join tests (Sonic jump, Tails jump, Tails flight × five joins).
- Original GPZ special loop state 19 exercised for 117 updates and led to boss trigger.
- Native tests of lives/pits/restart/game over and complete controlled original EEZ 16-hit chain for both characters.
- All four on-disk empty/tombstone save generations unchanged; absence of slot creation verified. Populated-progress isolation demonstrated in mocked-IO cases, **not** in a human full-course run with populated on-disk saves.
- S2 source verifier 2,918 passes; original boss, M6H and SS source suites reported pass; combined S1 graphics smoke pass; standard uninstrumented Windows compile and short six-second launch smoke pass. The natural full-course owner/controller/audio test is still unrun.
- Historical verifier first-failure matches remain recorded; inherited S1 allowlist no longer fits intentional S3 resources/hooks. Do not relabel historical fails as passes.
- Designer reports 5,709 protected source files unchanged relative to S2; challenge/menu hooks separately inventoried; independent H: package/Git recovery verified by Designer, not this Manager.

## Manager decision
**GO for one consolidated Chief acceptance test.** This is technical readiness to test, **not** final S3 approval. No additional Designer fixes or builds are commissioned based solely on documented test coverage gaps.

## Chief acceptance checklist — one combined session
1. On the exact S3 Windows ZIP, verify Enhanced title START→existing Data Select, and BOSS RUSH immediately beneath START→original Sonic/Tails select→one LEVEL 7 opening. Check Classic title/start briefly on a separate launch.
2. Prefer a full Sonic course first. Judge the actual EEZ background/terrain palette consistency across all six sections; readable water/spikes/hazards and attractive reused scenery; no abrupt visual seam or surprise re-entry card/fade at joins.
3. Traverse the GPZ loop normally, check MGHZ spike-gated tree/boss reveal, AQZ water/fight and EEZ full final fight. Note boss triggers, camera lock/unlock, movement, ring supply, native music/SFX and both-character-relevant hazards.
4. Judge difficulty/fairness: challenge-only pits, approach/exit/knockback, no unintended unavoidable deaths, three lives/no continues and whole-course restart after death. Full Sonic clear should display BOSS RUSH CLEAR; START restart and B/ESC title should work.
5. Brief Tails entry/flight and at least one connector + selected relevant boss spot check; no second full run required unless Chief wishes.
6. Verify ordinary Enhanced START can still open a save without unexpected changes; do not deliberately wipe owner progress. Save safety may also be retested separately by Designer against populated files or disposable copies if a real concern emerges.

## Status and follow-up
- S3 technical candidate: **MANAGER GO FOR CHIEF TEST**.
- S3 subjective visual/audio/gameplay acceptance: **PENDING**.
- Any new defect: log exact zone/boss/approximate X or screen, character, input, scene, symptom and reproducibility; consolidate into one S3 corrective batch instead of microbuilds.
- Full hash, full SHA, native screenshot bundle and private receipt remain with Designer; archive and source publication decisions occur only following Chief acceptance.

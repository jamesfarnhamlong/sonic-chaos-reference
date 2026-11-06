# Sonic Chaos — S3-R1 Manager #11 Technical Review
**6 November 2026 · MANAGER GO FOR CHIEF F5 — FINAL S3 ACCEPTANCE PENDING**

## Source and review limits
Designer supplied private `S3_R1_BOSS_RUSH_20261106.md` for one integrated S3-R1 Windows candidate: `SonicChaos_Windows_20261106_S3_R1_BOSS_RUSH_CANDIDATE_PRIVATE.zip`, private source ZIP and SHA-256/H: receipt on Chief's E:/H: drives. R1 source is abbreviated `8b5086c` (full SHA and tree stated in local receipt, not supplied to Manager); branch `enhancement/s3-r1-map-polish-20261106`. R1 parent exact `7a6a4b714171cadcfd9f9efb77763f31f8ac5885`; accepted S2 source `0809ef9cbc9ea9c1fda3bc0ead45aa9aa749a5a7`. Immutable Classic tag `classic-core-20261105` still targets `3a58912659b48573ac7f2c5c96a02a2211d5e4da`.

This Manager reviewed the uploaded Markdown report, **not** private ZIP binaries, external hashes, independent H: backup, or the linked PNGs in the report (`s3-r1-native/*.png` were not uploaded). All reported native source/game tests are **Designer-reported**, not personally rerun. Chief's successful first S3 natural full run remains established evidence for the unmodified core; R1 has **not** received a human full-course PASS.

## Scope completed, per report
- Complete horizontally traversable Level 7 now **13,024 pixels** (S3 original: 9,632), preserving THZ→GPZ→SEZ→MGHZ→AQZ→EEZ and longer original source geography, EEZ lower entry/lift and **320-pixel final ascent**. Five connector lengths: 64, 128, 64, 128, 64.
- Original boss room identities/local coordinates and camera owner remain behind seamless internal handoffs; no repeated title, fade, results or opening. Existing GPZ loop special state preserved. Boss attacks and state/camera functions unchanged.
- Exactly two designated pit changes: SEZ's six static `$F8` cells replaced with authentic `$AF` crumble cells (source X2336–2528, Y512), original `$13` pool/break animation/audio, lower source rectangle Y>=544 removed; MGHZ safety rectangle X1824–2752 Y>=480 removed while preserving special strip/tree/spikes/boss combat platforms.
- **Important confirmed mechanic:** original kill rule is signed `player anchor Y - camera Y >= 208`, not one fixed global world Y. Constant course ordinary-camera band used while original fight camera owners still authoritative; previous challenge-only forced MGHZ Y>=512 death removed. Pit fatalities hit screen Y210 on actual original rule, avoiding mid-course kill-Y mutation.
- MGHZ special strip preserves original surface25 tread/run/fail states: standing idle inert; too-slow movement fails; running/jumping proper route; Tails flight landing works. GPZ original loop and EEZ type28 parameter05 lift remain authentic.
- EEZ industrial palette/background and challenge-only terrain adaptations retained; stray organic trees removed but **original MGHZ boss-supporting tree retained**; floating noncolliding AQZ water patch omitted; AQZ twelve spring tiles restored to pixel-exact original functional palette, along with spring rendering for Sonic/Tails.
- Challenge-only suppression of unwanted defeat sparkle `$0A`, GPZ smoke puffs and victory-jingle request `$97`. Ordinary campaign effects/sound retained. HUD rings/time instantiated immediately at joins, including fractional timer phase and minute rollover, and challenge clock continues through EEZ.
- Enhanced main menu START→five-card Data Select, BOSS RUSH directly below→Sonic/Tails→LEVEL 7; Classic unchanged; three lives/no continues/checkpoints and sparse rings remain.
- **Save isolation improvement:** actual native disposable populated saves (five slots, ten generation files, Sonic Emeralds, Tails progress, partial/full completion) revalidated and byte-compared unchanged, plus Chief's real campaign file hashes checked before/after all probe runs. No test-only code or filename prefix ships.

## Delivered verification evidence
- 684 native compiled boss/player/camera sample rows match accepted S3 (12 scenes × 3 widths, 228 rows/width); this is controlled testing, not six natural victories.
- 25 native joins: Sonic/Tails walking+jumping and Tails flight across five handoffs; HUD clock continuous through 1:59→2:00; seven rings retained at final join.
- Ten native full original-input approaches including SEZ crumble, MGHZ strip, AQZ springs, EEZ lift/roof, both characters.
- 24 native pit/knockback cases over three widths: failures die by original camera-relative rule, boss recoveries survive.
- Ten first-five-boss clear effects tests; jingle request absent and undesired effect drawings suppressed.
- Both Sonic/Tails original EEZ sixteen-hit boss chain and challenge finish/restart/title controlled probes.
- 16,189,440 protected collision samples; existing S2/regression source suites and original strip/lift replay 46/46; 5,693 protected original resource/save/spring-runtime files unchanged.
- Standard GameMaker LTS 2026.0.0.23 Windows VM PackageZip compilation/six-second uninstrumented launch smoke, no verifier symbols, settings/saves unchanged.
- Old U5-A whole-core test failure is inherited on both S3 and R1, specifically `shoes@256 u1`, not secretly marked passing; focused original strip/type28 trace replay passes.

## Chief F5 acceptance — ONE focused session, no repetitive microchecks
1. Launch exact R1 Windows ZIP. Enhanced START still routes into existing Data Select; BOSS RUSH below START → Sonic/Tails → single LEVEL 7 opening. Short Classic confirmation only.
2. Play **one preferred-character full course** to the BOSS RUSH CLEAR. Judge 13,024px route, consistent industrial EEZ/MGHZ-style scenery and intended 320px final ascent; confirm no discordant trees, AQZ floating water or invisible 2→3 obstruction.
3. Confirm SEZ purple section actually crumbles, corresponding pit is lethal and fair; MGHZ run/jump strip and pit also fair, with original boss-supporting tree/spike gate visible. GPZ loop should remain authentic.
4. Check AQZ spring colours, graphic visibility and launch; late 4→5 transition no missing spring/other sprite. All six bosses, original final EEZ sequence, music continuity; no unwanted sparkle, Boss2 puffs or victory jingle.
5. Ring/time HUD remains visible and continuous across joins, and restart/life depletion/title paths make sense. Short Tails entry/flight spot check where practical rather than second full route.
6. Ordinary Enhanced save and Classic unaffected. No need to overwrite/wipe any personal save or repeat automated exhaustive tests.

## Decision
**MANAGER TECHNICAL GO FOR CHIEF WINDOWS PLAYTEST. S3-R1 NOT YET CHIEF ACCEPTED.** Preserve private builds, S2/frozen Classic, no automatic merge/tag/public release. If Chief identifies remaining defects, consolidate any related fixes in one scoped corrective batch, not separate microbuilds.

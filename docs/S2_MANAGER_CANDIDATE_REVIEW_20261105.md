# Sonic Chaos S2 Data Select — Manager Candidate Review
**5 November 2026 · Manager-san #10 · TECHNICAL REPORT PASS, GO FOR ONE CHIEF WINDOWS ACCEPTANCE SESSION · NOT YET CHIEF ACCEPTED**

## Delivered private candidate
- Designer local branch: `enhancement/s2-data-select-20261105`.
- Designer reported local commit: `0809ef9cbc9ea9c1fda3bc0ead45aa9aa749a5a7`, parent Chief-accepted S1 `56c767e8b4f0f73c41f2d8ec41ca471d7a90e746`.
- Private Windows ZIP `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Windows_20261105_S2_DATA_SELECT_PRIVATE.zip`.
- Complete source `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Production_20261105_S2_DATA_SELECT_SOURCE_PRIVATE.zip`.
- Private SHA-256 file `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_20261105_S2_DATA_SELECT_SHA256.txt`.
- Designer report uploaded for Manager review as `S2_DATA_SELECT_20261105.md`, 142 lines; private source `SonicChaos_Production/docs/production/S2_DATA_SELECT_20261105.md`.
- Designer reports independent E:/H: archive, hash, complete source and Git recovery PASS. **Manager cannot inspect/recalculate these private local package/H: SHA values from paths alone**. As of Manager's 5 Nov remote check, **S2 commit and branch were NOT resolvable through the connected game GitHub remote** (S1 likewise local), whereas original Classic annotated tag `87f13ef24877519c820d4d2612b58279a43578e6` and accepted E0-R1 branch `deccefc0acd822f74b6b26895ec278cdf67a7cee` remain. This is compatible with no push; it does not disprove the Designer's local commit.

## Chief's binding design matched by report
- After selecting Enhanced, **original opening/title -> five horizontal Data Select cards**, replacing original Sonic/Tails choice, with no extra save-mode flag/text/Options entry. Classic continues original title -> original character choice -> original unsaved game. Enhanced S1 display toggles/defaults unchanged (all OFF in accepted S1; final display defaults deferred to endgame).
- Empty slot: Left/Right select one of five; Up/Down choose Sonic or Tails; A/Enter/pad A/Start creates and verifies `character + THZ frontier + five-bit Emerald mask=0 + incomplete` then starts THZ1. Created character is locked; delete is only reset.
- Occupied unfinished slot: Up/Down chooses **unlocked zones**, not acts; launches **Act 1** of selected zone, reinitializing canonical lives/continues/rings/score/player/camera. Recorded frontier advances **after committed Act 3 zone clear**, never Act 1/2. Replay and previous zone cannot decrease it. Upon completed game, the chosen slot shows special complete TV image and offers all **18 act** entries.
- Sonic Special Stages: five earned mask bits recorded only on authentic confirmed collection; original Sonic eligibility and lowest-unearned-stage route retained. Authenticated EEZ final boss sixth bit appears only after full five-emerald completion; Sonic partial clear displays its actually earned five bits, not false sixth. Tails cannot earn/display Emeralds, but can have a completed slot. Confirmed WIPE supports NO default and cancellation, protects other slots.
- Native-rendered six zone thumbnails added privately from compiled scenes; original character palette portraits and card assets reused; old original `ROM_menu_data_select` and `saveGameN.ini` logic still disconnected. Reported Draw failure `c_magenta` corrected to defined `c_fuchsia`; numeric readback validation and global `chaosS2` name collision also corrected before packaging.

## Storage and safety
- One dedicated `global.chaosEnhancedCampaign` owner and namespaced `chaos_campaign_*` functions; not legacy `global.chaoEmerald`, `saveGameN.ini` or `settings.ini`.
- Five independent slot records, each two generations `enhanced_campaign_v1_slotN_0.json` and `_1.json`, schema/version/slot id/monotonic generation/MD5 integrity; persistent fields `occupied`, locked character, frontier zone, completed, five Sonic Emerald bits and authentic full-ending receipt; no mid-act/lives/Continues/score snapshots. GameMaker's app sandbox typically `%LOCALAPPDATA%\SonicChaos`. MD5 is corruption detection, **not** hostile tamper protection.
- Pending staging readback verification, committed generation fallback on damaged file, visible recovery, future schema version write protection, wipe tombstone confirmation, no cross-slot writes; failed save is surfaced and cannot silently launch with unsaved new slot. Manager has not independently inspected actual save directory/files; claims are in Designer report.
- Exactly six original runtime GML files reportedly modified with guarded Enhanced-only hooks and slot detachment; Classic observers must return without accessing storage. Removing them reportedly reconstructs S1 byte source. No core gameplay/camera/audio/physics rewrite; accepted Classic tag and S1 packages preserved.

## Verification evidence — Designer-reported
- **2,908** source-host assertions using shipped new owner GML and mocked IO/menu inputs: five slots, character locks, all frontiers, 32 masks, full/partial/Tails completion, 18-act replay, invalid/future/corrupt records and failed writes, controller inputs and wipe.
- **339** compiled native Windows file checks with real GameMaker IO, staging failures/backup rollback, version protection, actual SS goal-bit events and duplicate guards; **all five** canonical Special Stage goal-bit paths tested using controlled states.
- **36** native actual rendered/player endpoints for both Sonic/Tails across 18 acts; real results loader and ending callbacks test no Act1/2 promotion, Act3 frontier promotion and Sonic full/partial/Tails closure. **Not** natural full campaigns.
- Compared with accepted S1: **108 gameplay state snapshots, 36 rendered endpoints and 180 audio driver ticks all exact**; no reported state/visual/audio divergence from the canonical game.
- **18** native UI display states across five cards, six zone TVs, empty Sonic/Tails, Emeralds, completion and delete/recovery; 256/290/348 logical widths and S1 graphical toggle ON/OFF checks. Separate process reload restores Tails slot; real title routing and Enhanced/Classic selection checked.
- Existing S1 source-host **3,472 PASS** and original SS return/Level Select checks PASS. Six inherited raw verifier failures were reproduced identically against accepted S1 and S2; no false 'all historical tests PASS' assertion.
- Production-style Windows candidate compiled, Designer fixed reported GML Draw crash (invalid `c_magenta` -> `c_fuchsia`) and two data/namespace issues before final package. Physical controller, ordinary owner aesthetic review and real short fresh-install launch remain Chief acceptance pending.

## Manager decision
**S2 delivery and scope review: TECHNICAL PASS ON DESIGNER EVIDENCE — GO FOR CHIEF'S SINGLE COMBINED WINDOWS F5.** No independent package/hash or code audit is claimed; no reason to commission another micro-build solely for managerial inspection. Preserve current S2 commit/package while Chief tests.

**Chief acceptance card (single short session; no campaigns):**
1. Run S2 private ZIP, choose Enhanced, verify opening/title then **Data Select instead of original character selector**. Select an empty slot, toggle Sonic/Tails portrait and confirm Sonic THZ1 starts. Return to title, reenter, confirm the slot remains Sonic and TV THZ.
2. Create a Tails slot, verify **no Emeralds**; exit/relaunch candidate and confirm that slot persists. Try WIPE: cancel once (NO default), confirm deletion next, verify Sonic save remains.
3. Test left/right slot selection and up/down zones. If convenient, naturally finish THZ3 to confirm GPZ television/start unlock, or rely on already documented native Act3 tests rather than demanding three full acts from Chief. The saved-zone/Act1, 5 Special Stage, partial/full ending, all 18 acts after completion, and corruption/fallback cases have controlled native proof; no need to personally run campaigns.
4. Run Classic from opening/title: authentic original Sonic/Tails choice, no Data Select; confirm ordinary music/gameplay and no new crash. Check physical controller and controls. Report visual layout/flow plus one consolidated issue list, or 'PASS'.

**If Chief PASS:** mark S2 as accepted Enhanced successor, preserve SHA, defer all final display defaults. If issues: one S2-R1 corrective batch then one combined recheck. No automatic game main merge or public release.

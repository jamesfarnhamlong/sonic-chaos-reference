# Sonic Chaos — Chief's Focused S5 + S6 + S7 Combined Acceptance Checklist
**12 November 2026 · Manager-san #11 · OWNER'S TEST GUIDE · CHECKS NOT YET EXECUTED**

Based on Designer's private source guide `E:\AI\Codex\Sonic Chaos\releases\S5_S6_S7_COMBINED_ACCEPTANCE_20261112.md`, uploaded by Chief on 12 Nov. Preserve user originals. Scope is **presentation/input/window parity**, not two complete playthroughs. Chief chooses test time.

## CHIEF RESULTS — 12 NOVEMBER 2026

Chief returned completed combined checklist with **33 PASS / 4 UNOBSERVED / 0 reported functional failures** on the existing S6 Windows candidate, actual physical gamepad. All S6 Options and window/display/settings persistence checks PASS, S5 authentic title and regular stage clear PASS, Boss Rush intro/representative play PASS, existing Classic preservation smoke PASS. Four unobserved because no appropriate saves/reached results: all five TV states, GPZ dedicated preview save state, earned Emerald/progress displays, final Boss Rush CLEAR TIME/RINGS/LIVES. These were **NOT marked FAIL** and no fictional PASS was recorded. Chief likes original 41-frame title source presentation (can't detect redesign beyond native-style menu). Two **art-only feedback items**: Boss Rush PAUSE card erroneously displays THZ palm-tree thumbnail (verified older source zone icon `SPR_data_zones` **36×36** inside `SPR_data_form_2` **40×40**) and the six Save TV zone pictures (S5 **144×128** native displayed **288×256** exact2×) need stronger curated art. [Full owner acceptance and proposed visual-only scope](S5_S7_CHIEF_ACCEPTANCE_AND_ART_POLISH_20261112.md). No extra Classic/canon, save, camera or gameplay change commissioned. Current S6 exact package remains unchanged; S7 no-change closed.

## Exact baseline
- Extract **`E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Windows_20261112_S6_FRONTEND_UI_CANDIDATE_PRIVATE.zip`** into a fresh folder; reported SHA256 `8d41e2eac1761b376ecdaf9bb1f982f3c7e4077ef4be299cbcaf0fdaaa11b166`.
- Source exact `47c501ecb994a4fcb1eeac1c29793f3f1142a304`; S5 source ancestor `11cefcece3c43e33db8a2f5967347c444b5a8fb4`. S7 prototype rejected; **no S7 executable or PHOSPHOR setting**. `CRT FILTER ON` means existing S1 light scanlines.
- Use disposable/empty Enhanced save slot; do not erase valued progress. Record physical controller, host resolution, borderless/window, Sharp/Integer/CRT state for defects.
- Timing flexible; representative flows only. Unsupported/unreached states recorded UNOBSERVED, not PASS.

## Checklist
### S6: options and physical gamepad
- [ ] Enhanced Options native pixel alphabet, visible selection pointer, no overlapping old text
- [ ] Physical controller Up/Down, A confirm, B back: each press one action, held confirm doesn't double-enter
- [ ] Change all current settings and return, values retained when expected
- [ ] Window mode WINDOWED/BORDERLESS label matches actual state; Start and Back accessible

### S4/S6: display and settings persistence
- [ ] At 1920x1080 compare window/borderless; no crop, black-screen or stretch
- [ ] Integer Fit ON and OFF both acceptable; Sharp Pixels ON/OFF works
- [ ] CRT OFF and current LEGACY ON light scanlines; **no S7 new CRT to find**
- [ ] Commit settings, close, relaunch, values persist; resize, Alt+Enter, focus/minimise/restore recover
- [ ] If practical, test 1280x720 output UI readability with CRT OFF/legacy ON

### S5: title
- [ ] Original authentic title/logo/palette animation and START GAME art
- [ ] Matching original-pixel-font BOSS RUSH, clean pointer and no doubled/hidden title text
- [ ] Press START early: first valid visible menu routing remains correct
- [ ] Start Game and Boss Rush each navigate correctly; return to title works

### S5: five-TV Data Select
- [ ] Five TV slots, clear focus/current character, authentic Sonic/Tails running animation
- [ ] Tails head clean; TV static/emerald icons correct
- [ ] Zone previews centre with even black letterbox; GPZ crop includes pipes/bridge/platform
- [ ] Existing saved progression/character/Emeralds display and load correctly
- [ ] Erase prompt defaults NO, B/Cancel leaves real slot untouched; avoid destructive test of valued slot

### S5: zone intro and end
- [ ] Normal stage title card zone/act typography and movement transition unchanged
- [ ] Brief Sonic/Tails ordinary movement/music/HUD sample (not entire campaign)
- [ ] One zone end original rolling km/h, ring and speed tally, sound and forward progression

### S5: Boss Rush intro/end
- [ ] BOSS RUSH character choice and Level7 card match regular source zone cards
- [ ] Representative boss section: LIVES HUD, camera and canonical challenge audio/behavior
- [ ] If readily reachable, CLEAR displays frozen TIME/RINGS/LIVES and correct restart/title routing; if not, **UNOBSERVED** rather than implied PASS

### Current Classic smoke, distinct from future C1
- [ ] Existing Classic launches and original menu/gameplay/audio preserved with expected old baseline
- [ ] Returning to Enhanced retains its features/preferences and doesn't contaminate Classic data
- [ ] Don't confuse existing Classic smoke with acceptance of the **future true 256×192 ROM-wide C1 rewrite**. C1 is separate, in progress, and must be source/ROM verified before integration.

## Finding record
For each failure record milestone, screen/zone, character and slot, size/mode, settings (Integer/Sharp/CRT), controller, action sequence, expected vs actual, optional screenshot. One consolidated correction after Manager review; no automatic microbuild. Mark S5, S6 and S7 separately Accept / Hold / Unobserved. The S7 outcome is a **no-change design decision** not a new shader A/B test.

## Mode philosophy and future C1 gate
Chief additionally mandated [ROM-wide C1 audit, original Master System rules only](C1_ROM_WIDE_CANONICAL_FIDELITY_MANDATE_20261112.md), rejecting QoL and discretionary fixes for future Classic. Preserve exact **S6 Enhanced wide gameplay with all newly optional gameplay QoL toggles OFF** as the control (S4 existing display-default policy stays until separately changed); new QoL requires explicit later Chief decisions and defaults OFF. C1 requires its **own original-vs-GameMaker ROM evidence**, not merely the S5–S7 UI smoke checklist.

# Sonic Chaos — S1 Integrated Display Candidate: Manager Review
**5 November 2026 · Manager-san #10 · S1 TECHNICAL PASS (Designer evidence) / GO FOR ONE CHIEF ACCEPTANCE SESSION · NOT YET CHIEF ACCEPTED**

## Delivery
Designer has completed the substantial, coherent S1 display sprint, with all three enhancements together and all features **OFF** by default.

- Private branch: `enhancement/s1-display-foundation-20261105`.
- Designer-reported local commit: `56c767e8b4f0f73c41f2d8ec41ca471d7a90e746`.
- Windows candidate: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Windows_20261105_S1_DISPLAY_FOUNDATION_PRIVATE.zip`.
- Complete source: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Production_20261105_S1_DISPLAY_FOUNDATION_SOURCE_PRIVATE.zip`.
- Full-resolution screenshots: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_20261105_S1_DISPLAY_FOUNDATION_VISUAL_COMPARISONS_PRIVATE.zip`.
- Receipt: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_20261105_S1_DISPLAY_FOUNDATION_RECEIPT.json`.
- Report provided directly to Manager as `S1_DISPLAY_FOUNDATION_20261105.md` (49 lines); private original at `SonicChaos_Production/docs/production/S1_DISPLAY_FOUNDATION_20261105.md`.

GitHub verification by Manager 5 Nov: original Classic annotated tag object `87f13ef24877519c820d4d2612b58279a43578e6` still exists; frozen production commit `3a58912659b48573ac7f2c5c96a02a2211d5e4da` and accepted E0-R1 branch `deccefc0acd822f74b6b26895ec278cdf67a7cee` remain. **S1 SHA and branch are NOT available through currently connected game GitHub remote**, likely because Designer intentionally made no public/private remote push. No inference of invalid local source is warranted. Manager has not opened/re-hashed the E:/H: ZIPs, private receipt, full-resolution screenshot ZIP, or the S1 local code diff: Designer's technical/hash claims are accurately attributed, not represented as independently reproduced.

## Functional scope delivered (reported)
- `SHARP PIXELS OFF/ON`: same E2-P1 captured actual GPU texture state, with restoration; no hardcoded baseline. Default OFF.
- `INTEGER FIT OFF/ON`: true logical native-sized application surface, nearest whole-number scaling with opaque centred borders; inherited Wide348×196, actual Retro290×218 and Auto logical view retained; camera, world visibility, collision, and fractional visual positions not modified. Default OFF. 1000×700 Wide => 696×392 output + 152/154 borders; 1920×1080 Wide => 1740×980 + 90/50 borders **only in controlled client-size probes**, not an added fullscreen mode.
- `CRT FILTER OFF/ON`: self-contained one-pass scanline modulation ≤10% plus weak RGB mask ≤2%, no blur, warp, remapping, crop, feedback or external shader. Present only when shader compiles. Default OFF.
- One existing Enhanced Options page with visible ON/OFF, Up/Down/Confirm and ESC/pad B; **START GAME bottommost**; no saved preferences, F-key developer toggles or second executable.
- Windows normal 1×/2×/3× multiplier unchanged; fullscreen switching/arbitrary resize unavailable. The previously parked **shared Classic+Enhanced display settings** and **release developer Level Select removal** remain endgame polish, NOT S1.

## Original-source protection
Exactly four formerly frozen GML files were changed on the isolated successor branch under the [explicit S1 Manager authorization](S1_PROTECTED_RENDER_HOOK_AUTHORIZATION_20261105.md): `SCR_screen`, `OBJ_pause/Alarm_0`, `SCR_chaos_results`, and `SCR_chaos_death`. Report says deleting the four guarded insertions restores the accepted-E0 file texts. The E0-owned frontend script also differs, as expected. All other frozen gameplay, collision, camera, audio, sprites and Windows project options reportedly unchanged. Original **frozen tag and accepted archives remain immutable**, notwithstanding the guarded successor-branch file changes.

## Verification evidence grades (per Designer report)
- Source-host 3,472 assertions passed, including nine display states (Classic + all eight Enhanced three-toggle combinations), default OFF, focus/input, feature and shader eligibility, filter state, native scale geometry, both character model snapshots. These tests have mocked input/engine.
- Compiled native integration: 60 controlled cells, 11 accepted E0 control cells; 5,460 compared player/core/camera/animation/audio-request snapshots equal. THZ/AQZ both Sonic/Tails in all nine states, plus Wide1×/2×, actual Retro, controlled native256, Auto, Continue, character-choice, SS1, early ending.
- Pixel evidence: 164 controlled Classic/all-OFF pairs **exactly zero RGB differences in both application/full-client**. 104 Integer Fit output pairs match exact nearest-neighbour expansion; 124 Integer+CRT pairs within declared channel-bound effect. AQZ water references used controlled raster sweep, **not natural traversal**. 791 screenshot records plus raw actual-res image/crop evidence are private.
- Audio: 180 separately clocked native programme ticks per each nine states: E0 CPU state, ordered PSG and 132,300 PCM frames each match. This is controlled native audio, **not natural listening or measured wall-clock IRQ**.
- Lifecycle: compiled Pause/results/death presenter events and manual fallback verified after originally instrumenting with automatic presentation still active. Focus minimize/restore, surface loss/recreation, too-small clients, presenter destruction, room changes, pause/death/results replay reported PASS. No independent full campaign, consumer DPI/multimonitor matrix or live scanout measurement.
- Final uninstrumented Windows VM candidate compiles/boots, no test-only verifier resources and one EXE. Designer reports hashes and independent H: copies/bundle pass; Manager did not independently access receipt.
- Historical raw `verify_viewport_adapter.js` still FAIL at same type $27 on accepted E0 and S1; referenced `verify_c1i_camera.js` missing, so no fabricated pass. Four keyboard-injection extra-scene traces were replaced after matched deterministic-input reruns against E0. These are transparent verification limitations, not grounds to relabel all original raw FAILs green.

## Management verdict
**S1 integrated candidate: DESIGNER-REPORTED TECHNICAL PASS and MANAGER REPORT/SCOPE REVIEW PASS — GO FOR CHIEF F5.** No requirement for another development cycle before normal Chief visual/controller acceptance. No declaration of independent code/hash audit or in-motion visual quality, and no automatic promotion of any default to ON.

**Single Chief acceptance session** using the new **S1 Windows ZIP**, not E2-P1:
1. Brief Classic and Enhanced-all-OFF starts: original SEGA/menu/cinematic/music/gameplay acceptable. All OFF first preserves baseline.
2. One Enhanced gameplay run with **INTEGER FIT ON** (Sharp/CRT OFF): inspect intentional borders, actual original pixels, readability, THZ scrolling, Sonic/Tails if convenient.
3. One Enhanced run with **SHARP + INTEGER FIT + CRT ON**: judge scanlines/mask strength, scroll shimmer/diagonals, original HUD and AQZ water if convenient. Additional toggles/combos only if a defect is observed; the agent's 9-state matrix already exists.
4. Verify keyboard/pad navigation/Back/confirm and last Start Game. Brief Pause/resume, results or death, minimize/restore. The reviewer should note if black frames or audio freezes occur.
5. Chief chooses **KEEP OFF defaults**, **PROMOTE specific effects to ON by default later**, or **RETURN one concise defects list**. No full Sonic/Tails campaigns or repeated builds per option.

**Do not merge into game main, retag Classic, change user window/fullscreen settings or begin E1 frame-pacing work on this receipt.** GPZ3 map texture seam and richer scatter are tracked separately. CRT and Integer Fit can remain opt-in regardless of default selection. Follow-on endgame display settings and hide release-facing Pause Level Select are parked in [release polish tracker](tracking/ENDGAME_RELEASE_POLISH.md).

### Follow-up record
If Chief approves, record explicit preferred defaults, exact acceptance SHA and package receipt location, then consider next substantial *separate* sprint. If Chief finds a defect, group corrections into one S1-R1 batch and one final combined candidate, not micro-build/retest per issue.

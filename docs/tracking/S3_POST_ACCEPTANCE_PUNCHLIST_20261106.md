# Sonic Chaos — S3 Boss Rush Post-Acceptance Punchlist
**6 November 2026 · Manager-san #11 · CHIEF NEW OBSERVATIONS · OPEN, NOT FIXED · NO DESIGNER SPRINT YET**

## Scope and status
Chief explicitly accepted S3-R2 Boss Rush on 6 Nov after natural gameplay and the original Game Gear $9B music / clear statistics / visuals. **AFTER that acceptance**, Chief reported three further issues, reproduced at least once by Chief's own play (precise reproduction frequency not yet known). Preserve the accepted immutable source/package and historical acceptance receipt; track these as **new post-acceptance defects**, not as failures known during R2 acceptance. These are not cleared by earlier 684 controlled boss comparisons or 25 tested handoffs. The next S4 1080p Enhanced presentation architecture is **Chief-approved direction / not yet implementation-commissioned**.

Accepted production branch: private `jamesfarnhamlong/SonicChaos_POC` `enhancement/s3-r2-visual-audio-results-20261106`, full commit `29044caac612a0d2a23399e9fb7a58abda387740`, tree `69ef6d22e3fdd19c1351c612c752e81fc0c61362`. Four ignored runtime files are only in accepted E:/H: full-source archives, outside Git tree. Restore all before running new GameMaker builds.

## Owner-reported open items

| ID | Priority | Chief observation | Scope / next evidence |
|---|---|---|---|
| **S3-POST-01** | **P1 / noticeable visual-camera defect** | **MGHZ → AQZ transition:** a momentary, striking camera jump, appearing to warp **backwards for a split second**. Chief speculates a Y reset but did not prove X versus Y, timing, or root cause. | Examine exactly the section **3→4** handoff, final MGHZ section camera unlock, `chaos_s3_end` / `chaos_s3_handoff` / `chaos_s3_room_ready`, global/local coordinate transform, viewport and camera-owner timing. Trace for every Draw/rendered frame before and after `room_goto`: player world course X/Y, local X/Y, `global.chaosCam`, camera view X/Y, screen-relative player position, camera bounds/owner, texture offset and preceding follow step. Diagnose whether one wrong frame is actually presented; correct exact source of discontinuity with challenge-only changes. **Do not guess root cause or change core world camera/physics, nor 'smooth' by masking the jump without evidence.** Test Sonic/Tails, Wide348 and retro/native widths, normal runs and representative speed/flight through same join. Keep original bosses/EEZ and gameplay geometry intact. |
| **S3-POST-02** | **P2 / HUD consistency** | **LIVES HUD appears inconsistently hidden in Boss Rush**, notably during **SEZ (sometimes called SLZ in Chief's report)** and **MGHZ** boss encounters; should **remain visible throughout Boss Rush**. | Trace original Act 3 per-zone draw/visibility/room object ownership and any draw-guard flags / UI scene. Determine whether lives HUD is suppressed by original room design or lost at internal handoffs. Ensure challenge-only consistent lives count display with **RINGS/TIME/LIVES** throughout all six encounters and joins, along with correct live decrement at death and final BOSS RUSH CLEAR. Avoid duplicate counts or changing Classic/ordinary Enhanced original boss HUD. |
| **UI-POST-03** | **P2 / Enhanced title input timing** | **Pressing START too early on title** skips to actual game before revealing the intended selectable **START / BOSS RUSH** options. Chief calls this a minor UI issue. | Trace title intro/timing and earliest START confirm handler, input buffer/repeat and first visual reveal. Enhanced title must not silently bypass visible mode selection: early START should reveal/prepare menu or be ignored until menu visible, requiring an explicit subsequent confirmation when options are on screen. Avoid double-accept from one held key, gamepad START/A, or buffered confirm. **Preserve Classic's original title/START behaviour unchanged**, the accepted Enhanced START→Data Select and BOSS RUSH→character select routes, and the cinematic/audio pacing. |

## Preliminary source review (not a proven diagnosis)
Manager inspected accepted private S3-R2 `scripts/SCR_chaos_s3/SCR_chaos_s3.gml` on GitHub:
- `chaos_s3_section` uses explicit local-to-course Y offsets; **MGHZ has `oy=-128`, AQZ has `oy=0`**.
- `chaos_s3_end` follows camera during post-clear, then invokes `chaos_s3_handoff` at the connector midpoint.
- `chaos_s3_handoff` adjusts core local/player/camera coordinates and `cam.x/y` before `room_goto`; `chaos_s3_room_ready` restores `global.chaosCam` and view X/Y in the incoming room.
- These are **possible points to instrument**, not evidence of a faulty Y transform or incorrect camera equation. Previous controlled handoff state checks passed but the owner's visual-frame report demonstrates an untested presentation path/timing or new condition.

No reliable source diagnosis is available yet for the two HUD/title symptoms. No source changes have been made.

## Manager proposed handling and restrictions

## Assignment status — S4 COMMISSIONED 6 NOV (NOT FIXED YET)

All **three OPEN** owner issues are now in the **same integrated S4 sprint** authorized by Manager #11 following Chief's "Excellent! So, next job?" question. P1 camera handoff diagnosis first, P2 lives HUD and early Enhanced title START with 1080p UI display work. [S4 authoritative implementation scope](../S4_ENHANCED_1080P_FOUNDATION_SPRINT_20261106.md). Do not mark any issue solved by assignment, source instrumentation, or scaling alone: require real compiled evidence and Chief's final Windows test. Accepted S3-R2 exact SHA/archive remains unchanged.


- **Do not reclassify accepted S3-R2 as rejected or delete the acceptance receipt.** Mark accepted-with-post-acceptance-open-punchlist until a scoped follow-up candidate is Chief-tested. Do not claim the new issues fixed.
- Prioritize **S3-POST-01** ahead of UI cosmetic tasks. Capture actual rendered frames; test whether it is challenge-only handoff/presenter versus original camera.
- Because Chief prefers substantial consolidated sprints, **do not commission three microbuilds.** Discuss with Chief whether to commission one bounded Boss Rush/UI correction package now or include HUD/title with the proposed Enhanced 1080p S4 foundation; ensure camera issue is not lost. Avoid combining an unsafe camera behavioural fix with an unproven 1080p compositor by default.
- Only branch from recovered exact S3-R2 full source, including four ignored E:/H: runtime files; retain accepted build/hash as restoration anchor. Keep Classic/S1/S2, two death pits, boss cameras, native GG $9B, S2 save isolation, S3 HUD, results and gameplay sounds protected. One final integrated private candidate and one owner test if/when Chief approves.
- If Chief can supply approximate screenshot or short clip at seam, useful but **not required before Designer can instrument/reproduce** using existing accepted source and scripted inputs; do not make user repeat entire game or send multiple manual tests.

**Status: three OPEN post-acceptance observations, now assigned to S4 integrated sprint (6 Nov 2026). No fix/build/Chief PASS yet.**

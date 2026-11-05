# Sonic Chaos — Post-Classic Enhancement Backlog
**Working planning inventory · 5 November 2026 · Chief/Manager-san #10 · E0 accepted; E1 pacing parked; S1 Chief accepted; final display defaults undecided**

## 0. Immutable starting point
- Private Classic core tag: `classic-core-20261105` (annotated tag object `87f13ef24877519c820d4d2612b58279a43578e6`, peeled source `3a58912659b48573ac7f2c5c96a02a2211d5e4da`). Remote tag and freeze record verified 5 November 2026.
- Private project: `jamesfarnhamlong/SonicChaos_POC`. Main remains unchanged. Gameplay core, existing 60-target ordinary simulation (sprite poses change at state-specific intervals), 256×192 original reference, 348×196 PC widescreen, Z80 audio timing, Sonic/Tails, stages, results, existing QoL are protected. Source ZIP's stale B-only archive manifest is an accepted provenance caveat, not a reason to rebuild.
- All enhancements need a named opt-in mode or isolated presentation/adaptor layer, baseline-off comparison, separate implementation branch and Chief approval. Never mutate or force-move Classic tag. Future mandatory core deviations require separate evidenced successor checkpoint.
- Chief's two anticipated future **maintenance**, not enhancements: remove/hide developer Pause Level Select from release-facing access; disallow Pause during specific results/transition intervals. Current Classic freeze retains both; neither implementation commissioned.

## E0 — Unified Classic / Enhanced frontend — CHIEF ACCEPTED (5 Nov 2026)

Chief **accepted E0-R1** on the standard private Windows candidate. **Exact Enhanced baseline:** `enhancement/e0-r1-ui-20261105` commit `deccefc0acd822f74b6b26895ec278cdf67a7cee`; first E0 commit `69450848b1e06fcef7de63f19ae238ff346e479a` remains historical. Original frozen Classic `classic-core-20261105` at `3a58912659b48573ac7f2c5c96a02a2211d5e4da` remains unchanged.

One executable, shared original Sonic Chaos core, PC-only silent SEGA still ~2 seconds, 2-mode picker, Classic straight to cinematic, Enhanced directly to empty Options with **START GAME** last. `ESC`/pad B returns from Options, and no feature toggles are shown until actual implementation. New Enhanced features must be registered once and effectively off in Classic; no overlapping FX/dev switches. [Chief E0 acceptance](E0_R1_CHIEF_ACCEPTANCE_20261105.md) and [technical review](E0_R1_MANAGER_TECHNICAL_REVIEW_20261105.md).

**E1 research PASS:** active ordinary GameMaker gameplay targets 60 updates/s and no universal 30 Hz gating was found; actual Windows displayed-frame cadence is still unmeasured. Next is **E1-P0 measurement of existing E0-R1 ZIP only** (no code/build), not an automatic 30-to-60 conversion or interpolator. [E1 Manager decision](E1_MANAGER_REVIEW_20261105.md). A `tm_countvsyncs_winalt` pilot remains HOLD unless baseline is uneven and Chief authorizes. GPZ3 bug and ring QoL remain separate.

## 1. Graphics and performance — front of queue

**S1 CLOSED / CHIEF ACCEPTED (5 Nov):** Chief completed one combined Windows check of Sharp Pixels, native-grid Integer Fit and lightweight CRT, reporting all working as expected; local source `56c767e8b4f0f73c41f2d8ec41ca471d7a90e746`. Existing candidate defaults remain **OFF/OFF/OFF**. **Chief specifically deferred ALL final product default decisions until the end**, noting integer-fit may belong ON under fullscreen and Sharp Pixels may not pair well with a more realistic CRT shader. Do not switch Sharp ON by default automatically or repackage S1. A future accurate `SCANLINES` label for the existing lightweight effect is optional; stronger authentic CRT research remains separate and uncommissioned. [Chief S1 acceptance and correction](S1_CHIEF_ACCEPTANCE_AND_DISPLAY_DEFAULTS_20261105.md).

**S1 protected-source exception approved (5 Nov):** Designer reported checkpoint `5786dacc1ebc73006a79a255d071000e93d6c479` without implementing W2 because native-grid presenter would deactivate in Pause/results/death. Manager independently inspected four original source sites and authorized **guarded Enhanced-only lifecycle hooks** in `SCR_screen.gml`, `OBJ_pause/Alarm_0.gml`, `SCR_chaos_results.gml` and `SCR_chaos_death.gml`, on the S1 successor branch only. These do not mutate the immutable Classic tag/source/archive. **S1 later completed and Chief accepted all three options, with final product defaults intentionally deferred.** Small same-purpose presentation lifecycle guards are delegated, not another stop-per-file rule; unsafe fallback or gameplay/audio/camera changes still STOP. [Exact Manager authorization](S1_PROTECTED_RENDER_HOOK_AUTHORIZATION_20261105.md).


**CHIEF PROCESS CHANGE — SPRINT BATCHING (5 Nov):** Stop one-toggle/one-build/one-Ch​ief-test cycles. S1 is a coherent Enhanced display sprint incorporating E2-P1 Sharp Pixels (already delivered/visual-reviewed, default OFF), a safe native-grid integer-fit presentation pipeline, and—conditional on robust lifecycle—a restrained one-pass CRT option. One isolated branch and consolidated private Windows candidate/visual A/B at the end, with focused internal checks. All new toggles OFF by default until combined Chief acceptance; E2-P1b and E2-P2 earlier per-feature HOLDs are superseded **only within the narrow S1 scope**; unsafe presenter/native-grid or need to edit frozen GML still requires STOP. Lola full multipass CRT remains parked. [Sprint S1 authority](ENHANCED_SPRINT_S1_DISPLAY_FOUNDATION_20261105.md).


**E1-P0 final status (5 Nov): C — MEASUREMENT INCONCLUSIVE.** Accepted E0-R1 ZIP matched private SHA-256 `a087b6b1900a4160bfa3febc3abdf67fd54ce54d1f00f6c0ac13e0b124adaf6b`. Host desktop nominally 1920×1080 at 100 Hz, but no Sonic/Tails samples were collected: existing PresentMon returned 1/no CSV while target was not running, and non-elevated WPR failed profiling with `0xc5585011`. Actual displayed cadence remains unknown. **No E1-P1 implementation permission or '60 FPS solved' claim.** [Manager disposition](E1_P0_MEASUREMENT_DISPOSITION_20261105.md).

**E2 research PASS; E2-P1 GO (5 Nov):** existing Windows texture interpolation is true, and selected Draw paths locally override filtering. **Approved private pilot only:** Enhanced `SHARP PIXELS OFF/ON` texture nearest sampling via one shared E0 registry + display-policy module; default OFF; no stored user settings yet; START GAME bottom, no original GML edits, one private comparative Windows candidate with 1:1 captures and Chief visual decision. Not native-grid integer-fit, not CRT, not a fullscreen/resizing feature and not proven 60 FPS delivery. [E2 Manager authorization](E2_MANAGER_REVIEW_AND_P1_AUTHORIZATION_20261105.md).

**E1 status:** P0's attempt produced no timestamps. P1 HOLD until credible measurement can justify it; no timing code/feature. E2/S1 display pipeline is now Chief accepted; future CRT/fullscreen decisions remain uncommissioned. See [Manager's E1 review](E1_MANAGER_REVIEW_20261105.md).
| ID | Idea | Status / source | Preliminary gate |
|---|---|---|---|
| E-G1 | 60 FPS presentation | Prior ROADMAP E1; Chief renewed 5 Nov; Sonic 1/2 SMS Remakes support user-selectable 30/60 (outside precedent) | Research complete: normal simulation already targets 60 and pose holds are state-specific. E1-P0 capture attempt closed INCONCLUSIVE; Windows pacing P1 HOLD until measured evidence and separately approved. No default interpolation or clock changes. |
| E-G2 | Pixel-preserving scaling | **S1 Chief accepted** | Sharp Pixels and native-grid Integer Fit available and individually selectable, currently default OFF in accepted S1. Final defaults to be chosen with fullscreen and CRT presentation, not set now. |
| E-G3 | CRT post-process | **S1 lightweight CRT accepted; realistic CRT research future** | Existing S1 effect looks primarily like scanlines to Chief and remains optional/default OFF in accepted ZIP. Consider future label `SCANLINES`. More impressive Lola-style CRT is separate possible sprint; assess scaling/Sharp compatibility and final default at the end. |
| E-G4 | Optional palette and effects presets | Prior ROADMAP E2, AM-san | Original palettes default; reversible enhanced colours/subtle ambient lighting/particles; no change to source pixels, waterline shader, hitboxes or timers. |
| E-G5 | Higher-detail background/parallax tiles | Chief new explicit 5 Nov | Selective original-style background-only trial, preserve 8-bit foreground/character art, tile collision and occlusion; measure artistic consistency, no AI-restyled sprites. |

## 2. Gameplay modes

**S2 INTEGRATED DATA SELECT CANDIDATE DELIVERED (5 Nov; Chief check pending):** local reported S2 source `0809ef9cbc9ea9c1fda3bc0ead45aa9aa749a5a7` implements five-slot Enhanced-only Data Select replacing original character choice, selected-zone Act1, Act3 high-water unlock, Sonic's five earned Special Stage bits, authentic full-ending sixth, Tails no Emeralds, all-act completed slots, wipe and validated two-generation versioned storage. Reported 2,908 host checks, 339 compiled Windows checks, 36 native scene endpoints, exact state/render/audio parity with S1; corrected Draw `c_magenta` crash. **Ready for one Chief combined Windows/pad smoke; not yet Chief accepted**, and no Boss Rush/Super Sonic or graphics default changes. [S2 Manager review](S2_MANAGER_CANDIDATE_REVIEW_20261105.md).

**S2 REVISED BY CHIEF — SONIC 3-STYLE FIVE-CARD DATA SELECT (5 Nov):** Enhanced START GAME leads through the original opening/title **directly to Data Select replacing the character selector**. **No opt-in Save Mode flag, indicator or extra options row.** Empty 5 slots: left/right slots, up/down Sonic/Tails locked portrait on creation. Occupied: up/down unlocked **zones**, launch Act1 of selected zone, **save highest zone unlocked only after Act3 clear**, never lives/continues/score/mid-act. Slot data = character + zone frontier + Sonic-only five Special Stage Emerald bits + completion. Sonic can derive sixth icon from authentic five-plus-final boss route; Tails earns no Emeralds; completing game changes TV image and unlocks **any of 18 acts**. Include wipe confirmation and new robust isolated save storage. Existing original five-card OpenSonic objects and artwork may help but old saveGameN.ini logic is unsafe/off. One comprehensive S2 sprint and one Chief final candidate; no Boss Rush/Super Sonic yet. [Binding revised S2 charter](S2_ENHANCED_SAVE_EMERALD_SPRINT_20261105.md).

| ID | Idea | Status / source | Preliminary gate |
|---|---|---|---|
| E-P1 | Sonic 3-style Save / Emerald Progression | **S2 revised five-card Data Select sprint NEXT (Chief contract)** | **Always-on for Enhanced**, replacing original character choice after title; five locked-character cards, zone-only Act1 start on load, save next zone only after Act3, Sonic-only five SS earned bits, authentic sixth full-clear display, completed all-18-act replay, no saved lives/continues/midact; separate versioned file, confirmed deletion. Classic remains unchanged. |
| E-P2 | Boss Rush | Chief explicit 5 Nov | Either contiguous boss challenge or specially designed scrolling arena/zone; reuse existing boss scripts and original attack balance first; separate scoring and progression/Continue/emerald logic; avoid changes to Classic bosses. |
| E-P3 | Super Sonic | Chief explicit 5 Nov, feasibility only | Post-full-completion unlock because final Emerald belongs to Robotnik clear; dedicated original-style custom sprite and animation, energy economy, interactions and ending/continuity; do not retroactively insert transformation into canonical campaign. |
| E-P4 | Optional Enhanced QoL | Chief and earlier tracker | Candidate only with side-by-side original/Enhanced comparison and precise trigger: Spring Shoes restriction at boss (Chief wrote `SLZ`; verify zone/act), MGHZ falling-coconut damage/activation, AQZ boss music interrupted after invincibility, THZ3 spike/jump SFX priority, limited collision/scene polish. Original/Classic remains unchanged. Ring/enemy offscreen persistence already accepted and MUST NOT be misclassified as unfinished. |
| E-P5 | Original attract demos | Older ROADMAP E4 / FRONTEND-002, now post-freeze eligible | Original THZ1 Sonic → GPZ1 Tails → SEZ1 Sonic demo playback only after verifying ROM replay/input timeline. No artificial demos or gameplay deviation; not urgent. |
| E-P6 | Time Attack / score challenge | **New option to consider**, inspired by other SMS Remakes; not previously approved | Separate optional timer/leaderboard local mode reusing original acts; no entitlement to the original campaign state or secret-stage rules. |

## 3. Presentation, compatibility and comfort
| ID | Idea | Status / source | Preliminary gate |
|---|---|---|---|
| E-C1 | Preserved strict original 4:3 gameplay mode | Chief explicitly 5 Nov | Distinguish existing 256×192 viewport from true restored 256-wide *ROM lifetime/camera/culling/AI* policy; current widescreen adapters were deliberate PC QoL; do not assume 4:3 rendering automatically restores all mechanics. Optional historical control, low personal use priority, preservation value. |
| E-C2 | Windows display/input comforts | Earlier ROADMAP E3/old master roadmap | Window/fullscreen scaling, display presets, controller remapping, optional latency/input-buffer comfort, sensible in-game options; keep Classic defaults and clean startup. |
| E-C3 | First cold-launch sound delay | Chief reported ~2–3 sec on first EXE launch; parked in previous docs | Measure cause before inserting new cards/forced delay; may be tooling/cache dependent; don't reopen original driver architecture casually. |
| E-C4 | Production-facing debug/Pause restrictions | Chief current intended core-adjacent maintenance | Hide/remove developer Level Select when explicitly ordered; restrict Pause in results/noninteractive scenes once exact allowed intervals identified; preserve archival Classic and Sound Test policy separately. |

## 4. Parked platform and separate preservation projects
- **PS Vita feasibility**: Chief has Vita ports of SMS1/2; first investigate current YoYo Loader route for modern GameMaker, resource/audio/runtime performance. Only if unsuitable assess VitaSDK/vitaGL or high-maintenance GMS1.4/GayMaker backport. No Vita FPS promise without profiling. Kept separate from Windows enhancements.
- **Reproducible accessible ROM disassembly/decomp**: build on `sonic-chaos-reference` with machine-readable data and human documentation. Separate research project, not required to implement enhanced Windows gameplay.
- **SMS hardware slowdown-reduction patch**: preserve original ROM for comparative testing; distinct cartridge patch and hardware/emulation feasibility.

## 5. Rejected / not now
- **Knuckles**: lacking consistent authentic art/moveset; available OpenSonic assets would clash; not in this roadmap.
- **Cut-content restoration**: no meaningful authenticated Sonic Chaos cut content currently identified; do not invent it or borrow unsupported builds as fact.
- **Changing all bosses fundamentally**: not preferred; boss rush reuses original mechanics as separate mode first.
- **Compulsory sprite redraw/AI upscale**, permanent original-physics changes and universal '60Hz simulation' promises: prohibited without new Chief decision.

## 6. Proposed sequencing and decision gates
1. **DONE:** E0 unified mode picker / Enhanced Options shell, Chief accepted at `deccefc0...`; preserve exact SHA and Classic frozen tag.
2. **E1 RESEARCH/P0 DONE (C INCONCLUSIVE):** park Windows pacing changes pending new capture evidence; do not reinterpret as a 60 FPS proof.
3. **E2 RESEARCH DONE; E2-P1 GO:** isolate nearest-only `SHARP PIXELS` OFF/ON visual pilot, Classic identical, one private candidate and Chief A/B. P1b integer-fit and P2 CRT hold until separately approved. (highest technical upside) and E-G2/E-G3 display pipeline including Lola Retro feasibility; no build required unless a demonstrable pilot warranted. Low-cost two-mode visual/performance comparison after research.
4. Short graphics pilot: nearest/pixel-perfect vs native default, CRT off/on; evaluate Lola Retro adaptation feasibility separately. Then optional enhanced palette and selected background art.
5. **S2 REVISED NEXT:** implement Chief's five-card Enhanced Data Select replacing the character selector; zone frontier (Act3 clears) and Sonic five Special Stage Emerald flags only, no lives/continues, all-stage completed replay. Not a separate opt-in save mode. [Chief-revised S2 charter](S2_ENHANCED_SAVE_EMERALD_SPRINT_20261105.md). Boss Rush can be designed independently and may be lower-risk than Super Sonic.
6. Later authentic attract demos, enhanced QoL preferences and strict 4:3 original-mechanics mode. Keep maintenance Pause/debug separate from enhancements.
7. Vita research after rendering/performance decisions; source decomp and SMS slowdown patch separate.

## Decisions needing explicit Chief selection
- S1 already delivered and Chief accepted; **S2 save/progression is now the next commission**. Later features still need separate substantive sprint selection.
- Clarify the 'SLZ' boss/Spring Shoes reference before assigning exact original-vs-QoL tests.
- Confirm graphics aesthetic by screenshots before commissioning any high-resolution artwork.
- Decide whether desired 60 FPS means only visual smoothness or truly 60 Hz gameplay responsiveness; recommend the safer rendering-first research.

## References
- Canonical `ROADMAP.md`, `AGENTS.md`, `MEMORY.md`; current issue/triage docs, M2/M6 tracking, Chief post-freeze proposals 5 Nov.
- Original other-remake evidence: `https://sonic-sms-remake.blogspot.com/2022/12/sonic-1-v19-rev2.html`; Sonic 2 SMS Remake 30/60 metadata `https://kotaku.com/games/sonic-2-sms-remake`.
- CRT shader: `https://github.com/zoran123456/lola-retro`; secondary earlier RetroPie context only: `https://github.com/Sakitoshi/retropie-crt-tvout`.
- This document is a private noncommercial project *planning inventory* only, not authorization for public release, copyrighted code/art extraction, or cross-project reuse of copyrighted assets.

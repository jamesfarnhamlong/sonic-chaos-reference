# V1 / T1: twist-strip presentation and cross-zone goal/boss transition fidelity

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified, never committed).
Research base `c2692337649fcbd8b75c4ceff4645d9d61e2a59e` (C1-R). Accepted POC read-only at `ac021e1ef2665c8668de13959f5ccc4653f312d1` (VISUAL-P3).
Nothing in the POC, accepted releases, private assets or the root `AGENTS.md` was modified.

**Baseline gap (T1-14).** The final C1-I SHA could not be obtained: the POC remote exposes no C1-I branch (newest accepted branch is `poc/visual-p3-loop-presentation` at `ac021e1`).
All "POC" statements below are about `ac021e1` source; C1-I's camera work (I1/I2) is therefore not reflected. Manager must supply the C1-I SHA before PKG-T1A starts.

Machine-readable results: `data/v1/twist-audit.json`, `data/v1/twist-animation-contract.json`, `data/t1/transition-audit.json`, `data/t1/discrepancy-register.json` (14 + 8 rows).
Tools: `tools/v1_t1_trace.py` (needs ROM, ~5 min), `tools/v1_t1_register.py`. Tests: `tests/test_v1_t1_audit.py` (13, ROM-free, 0.01 s).
Evidence classes as in earlier studies. **EMULATED** = unmodified ROM in the approximate SMS harness. **SYNTHETIC CONTROL** = injected start position/camera, or a boss's requested state forced to its defeat state (stated per scenario). The POC was read, and its own JS harness was run once (below); GameMaker and Windows were not run.

## 0. Answers in brief

1. **The twist visual is a presentation bug only.** The ROM animates state `$22` with the five ball frames `$25..$29`, 3 updates each, looping, with no rotation, no facing change and no per-tile reset. The POC draws the legacy 40x40 `SPR_sonic_spin`, rotated by the path angle, at a speed-dependent rate, with facing taken from `sign(vx)` (and written back into the shared facing bit). The correction does not touch accepted twist mechanics.
2. **THZ and MGHZ use the same animation.** Same script, frames, durations and facing rule. They differ in entry rule (MGHZ raises any rightward entry speed to `$0500`), variant tables (2/3 vs 0/1), geometry (THZ arch vs MGHZ vertical chute) and which tiles carry foreground priority.
3. **The "Mobius" depth illusion comes from level artwork, not the sprite.** Foreground-priority background tiles hide the ball on the descending half. The POC already ships a priority overlay for THZ and MGHZ (CROSSZONE-FG1); only a Windows look confirms it for the strip.
4. **All 12 ordinary act clears share one ROM timeline** (contact, +280 state `$20`, +308/309 flag), have no sparkle objects at all, and end with a white fade chain. The POC's recovered structure matches.
5. **THZ3 is the one boss with a confirmed camera defect**: it re-centres on Sonic at creation and again at release (snap). SEZ3, MGHZ3, AQZ3 and GPZ3 (wide) use bounded 4 px/update adapters instead.
6. **The stale boss-clear sprite test is real**: `verify_thz3_boss_clear.js:84` fails on the accepted parent (expects `SPR_player_walk`, gets `SPR_chaos_player_frame_02`). The game is right; the expectation is stale.
7. **Not determined:** why Sonic seems to vanish and reappear running after a boss. No source path or harness trace reproduces it (T1-12); a Windows probe is specified.

## Part V1: Mobius/twist

### V1.1 Where the strip exists (DECODED DATA)

Blocks with surface type `$17` (`flags & $3F`), all 18 acts: **THZ1 22 cells (1 strip), THZ2 66 (3 strips), THZ3 22 (1), MGHZ2 28 (1).** Nothing in GPZ, SEZ, AQZ, EEZ, THZ-other or MGHZ1/3.
THZ strip = horizontal arch (blocks `$58..$6C`, `$73`; entry `$59/$5C` rightward, `$73/$72/$6B` leftward). MGHZ2 strip = 28 distinct blocks `$58..$73` forming a downward chute at cells x73-76, y12-22.

### V1.2 Player sprite (BYTE-VERIFIED + EMULATED, 10 traversals)

State `$22` script (bank `$0C` `$8425`, file `$30425`): five records `duration 3`, frames `$25 $26 $27 $28 $29`, callback `$94C1` each, then `FF 00` restart. Cycle 15 updates.
`frame = $25 + ((n div 3) mod 5)`, `n` = updates since entry, `n = 0` the first executing update. The rule held on **every update of every traversal**: THZ1 right/left, THZ2 right/left, THZ3, MGHZ2 right (two speeds) and the bottom-entry swing.
Frames `$25..$29` are Sonic's curled-ball set (frame `$29` is the plain sphere); the roll states reuse the same five frames in a scrambled 20-entry order, so the strip is a plain 5-frame loop in order.

| Question | ROM answer |
|---|---|
| Duration / repeat / exit | 3 updates per frame; loops until the surface test fails; exit writes angle and magnitude 0 and requests state 9 (roll) |
| Restart on tile change or reversal | No. Restarts only when the state is re-entered |
| Facing | Object `+$04` bit 4 is inherited from the entering state; the strip code contains **0 writes** to `IX+4` and `IX+6` (scan of `$94C1..$9829`). Left-entry traversals with the bit set or clear keep their value throughout |
| Orientation / rotation | None. No sprite rotation exists in the ROM |
| Draw position | Ordinary mapped-object registration (`D51A/D51C` cached position equals `anchor - camera` within camera motion: 71 of 94 updates exact, rest +-1..3 px). The strip handlers place the **anchor** on tile-relative positions; the sprite follows it |
| Level art vs sprite | Strip tile art is static (no BG tile or palette change during the ride in THZ1; MGHZ2's BG palette cycles on colours 4 and 11 every 10 frames, but equally when standing still, so it is a level ambience). Depth is per-cell foreground priority (below) |

### V1.3 Foreground priority (DECODED + EMULATED)

Name-table priority bit `$1000` per 8x8 cell of each block mapping: **THZ: 12 blocks (`$62..$6C`, `$73`), all 16 cells, 192 cells**, identical in THZ1/2/3. **MGHZ2: 16 blocks, 75 cells** (partial masks, e.g. `$63` 12/16, `$66` 14/16).
Effect on Sonic (pixel-level): THZ1 right run: hidden pixels in **54 of 95** updates, up to 381 of about 410, fully hidden in 6; MGHZ2: 39 of 93, fully hidden in 3.
So Sonic rides in front on the rising half and behind the ribbon on the descending half; that is the depth cue. The POC draws a mapping-priority overlay above the player (`OBJ_chaos_terrain_foreground`, depth -60 over -50) from `SPR_chaos_thz_foreground` / `SPR_chaos_mghz_foreground`, built from the same attribute bit and independently pixel-verified (`verify_thz_foreground.py`). Classification: accepted adapter; **verify in F5**, no change planned.

### V1.4 The POC today (POC SOURCE)

| POC code | Behaviour | ROM |
|---|---|---|
| `SCR_chaos_adapter.gml:78` | `SPR_player_spin` (legacy `SPR_sonic_spin`, 40x40, 5 GM frames) | frames `$25..$29`, 24x32 |
| `:88` | `image_angle = (angle-64)*360/256` | no rotation |
| `:101` | `image_speed = clamp(abs(vx)/4096, 0.075, 0.325)` | fixed 3 updates/frame |
| `:57-58` | `image_xscale = sign(vx)` then **writes `player_flags` bit 4** | bit never written; inherited |
| `SCR_chaos_player_animation.gml:5` | state 34 not in `chaos_player_animation_supported`, so the legacy chooser runs | |

The exact-ROM sprites `SPR_chaos_player_frame_25..29` already exist (RGBA equal to the ROM composites). The accepted twist verifiers (`verify_v16_twist.js`, `twist-results.json`) assert mechanics only (1,078 entry cases, 83/75 traversal updates, rolling exit); **none checks a sprite, frame or facing**, so they cannot detect any of this. All 112 dispatch handlers equal `data/twist-dispatch.csv`.

### V1.5 Implementation contract

`data/v1/twist-animation-contract.json` (data-driven; oracle `frame_at()` in `tools/v1_t1_register.py`).
Animation program (existing row format `[type,count,frame,script]`): `[[0,3,37,33829],[0,3,38,33833],[0,3,39,33837],[0,3,40,33841],[0,3,41,33845],[1,0,0,33849]]`.
Hooks: add 34 to the supported list and `chaos_player_animation_program`; the existing `chaos_player_animation_present` already uses `image_angle = 0` and `xscale` from `player_flags` bit 4; stop the legacy chooser for state 34.
**Can it be done without changing accepted mechanics? Yes.** It changes no core field except removing a non-ROM write to `player_flags` bit 4 during state 34 (a flag the ROM leaves alone; after exit the facing is the entering one, as in the ROM).
Risks: the presentation layer must not feed the terrain-ring shadow counter (`chaos_player_animation_update` header says it does not); exit hand-over to state 9 frames (already owned by P1).

## Part T1: goal and boss transitions

### T1.1 Ordinary act clear, six zones x two acts (EMULATED, sign sequence entered by a placement 60 px before the sign)

| Zone/act | Sign anchor | Camera at flag | Notes |
|---|---|---|---|
| THZ1 / THZ2 | (3960,558) / (3960,654) | (3831,405) / (3831,501) | |
| GPZ1 / GPZ2 | (4992,430) / (3968,686) | (4863,277) / (3839,533) | |
| SEZ1 / SEZ2 | (3960,558) / (3960,398) | (3831,405) / (3831,245) | SEZ2 contact late in my run only |
| MGHZ1 / MGHZ2 | (3968,366) / (3968,270) | (3839,213) / (3839,117) | |
| AQZ1 / AQZ2 | (5248,494) / (3968,622) | (5119,341) / (3839,469) | |
| EEZ1 / EEZ2 | (3968,430) / (3968,366) | (3839,277) / (3839,213) | |

Identical in all 12: state `$20` at contact **+280**; flag at **+308/309** (position-dependent by one update); camera settles at `signX-129`, `signY-153` (sign at screen centre, exclusive right limit); flag when `playerX - cameraX = 289` (RIGHT+33); Sonic held in `[cam+16, cam+247]` until state `$20` and enters it at **screen X 248**, i.e. at the right clamp, so he is already almost off the 256 px view and leaves it within about 40 px.
**Object pool during the whole sequence holds only `$18` and `$19`** (plus each zone's own enemies/water): **no goal or clear sparkle object exists in the ROM.** Keep it that way; the sparkles people see belong to ring pickup or the boss-defeat emitter.
First run-off pose varies with whether Sonic arrives pressed against the clamp: in several zones the selector shows side-contact frame `$5E` for the first 29 updates, elsewhere frames `$01..$06`. Both are the ordinary `$8EE1` selector; the POC's VISUAL-P1 port handles `$5E` and the walk set.
Sign sprite crop (C1-R I6) is unchanged: resource defect, not placement.

### T1.2 Transition after the flag (EMULATED, harness frames after the flag)

| Event | Ordinary act (THZ1, GPZ2) | Boss route (THZ3, SEZ3; defeat forced) |
|---|---|---|
| Freeze, Sonic already off-screen | 0..63 | 0..65 |
| White fade, 3 steps x 5 frames | +64, 69, 74 | +66/62, +71/67, +76/72 |
| Display blank (VDP R1) one frame | +188..189 | +188..189 |
| Fade back to results palette | +220, 225, 230 | +222/218.. |
| Results/tally | about 300 frames | about 490 (boss tally) |
| Second white fade | +535, 540, 545 | +722/748.. |
| Black fade, 3 steps | +635, 640, 645 | +817/843.. |
| Next act loaded | +677 | +860 / +887 |

The POC's recovered results chain (`SCR_chaos_results.gml`: `pre_card` white step 5 from age 60; tail white 96, black 48) is the same structure. Phase alignment between the POC clock and these harness frames is **unverified (T1-08)**; F5 stopwatch only.

### T1.3 Boss approach, camera and handoffs (EMULATED, SYNTHETIC CONTROL arrival; THZ3/SEZ3/MGHZ3 defeat forced to state 4)

Approach: Sonic injected 480 px left of the boss anchor, RIGHT held until the boss exists. All times in player updates.

| | THZ3 `$50` | GPZ3 `$51` | SEZ3 `$54` | MGHZ3 `$56` | AQZ3 `$59` | EEZ3 `$5E` |
|---|---|---|---|---|---|---|
| Anchor | (1936,238) | (1728,270) | (3200,622) | (3269,288) | (1856,238) | (2080,494) |
| Created (camera) | u66 (1594) | u67 | u67 | u67 | u67 | not reached in this run |
| Music `$8C` | u67 | u68 | u68 | u68 | u68 | |
| Trigger (right limit := camera) | u83, cam 1662 | arena limit 1664 set at creation | u83, cam 2926 | u83, cam 2995 | u99, cam 1646 | |
| Camera before trigger | ordinary follow, left limit raised each update, **no jump** | same | same | same | same | |
| Pan start / owner | u168 (`$D15F` bit 0) | u197 | u169 | u168 | u169 | |
| Pan target / settle | (1680,78) / **(1679,78)** | (1664,96) / (1663,97) | (2976,462) / (2975,462) | (3061,256) / (3060,256) | (1728,78) / (1727,78) | (1952,334)/(1951,333) per audit |
| Pan rate | 1 px/axis/update (max 2 sampled) | 1 | 1 | 1 | 1-2 | |
| Sprite palette swap | u173 (5 after state 3), colours 13-15 only | u197 | u171 | u173 | n/a (not driven) | |
| BG palette | unchanged | unchanged | unchanged | ambient cycle only | unchanged | |
| Display blank | one frame at u179 (art load) | none | none | none | none | |
| Defeat state | 4 (about 148 updates) | head `$0E` | 4 | 4 | 5-puff + blink | 4, then second encounter `$60` |
| Release (pan off, limits) | u321: left=cam 1679, right 2304 | `D280=cam, D282=1920, D27E=96` (audit) | u322: 2975, 3840 | u378: right 3584, left kept | right 2304, left=cam (audit) | per audit |
| Camera after release | **follow resumes, +7/update**, no jump | follow | +7/update to 3040 then limit | +7/update then limit 3107 (waits for Sonic X >= 3356) | follow | |
| State `$20` / flag | u322 (screen X 200) / u487, player-cam 292 | audit: u1218 / u1341 | u323 / u534 | gated on WORLD X >= 3356 + floor | floor only | |
| Next level | zone1 act0 | zone2... | zone3 act0 (MGHZ1) | zone4 | zone5 | ending chain |

GPZ3, AQZ3, EEZ3 defeat to release were **not re-traced**: forcing state 4 does not defeat them (GPZ head is `$0E` and needs its segment cascade; AQZ's state 4 is not the defeat entry; EEZ's boss was not created from my arrival). The existing audits (`gpz3-boss-runtime-audit.md`, `aqz3-boss-59-audit.md`, `eez-boss-endgame-audit.md`) remain the contracts for those handoffs. Each boss keeps its own contract: the camera pan targets, the gating rules (THZ none, MGHZ WORLD X >= 3356, GPZ floor only, EEZ two encounters) and the release limits all differ.

**Widescreen adapter differences (POC SOURCE).**
* **THZ3 (confirmed defect):** `chaos_boss_camera_step` mode 1 sets `x = max(camera_min, player.x - viewW/2)` the moment the boss is created and mode 4 sets `x = clamp(player.x - viewW/2, ...)` at release. The ROM does neither: it keeps following and only raises the left limit; at release it resumes the normal follow at <= 7 px/update. At 348 px the GameMaker follow leaves Sonic anywhere in a 46 px zone centred on screen, so creation snaps by up to **23 px** in one update; the release example (Sonic 1886, locked camera 1679) jumps **33 px** (1679 to 1712). Pan mode 3 (settles at the ROM's 1679) and the pre-trigger hold are fine.
* **GPZ3:** modes 1/4 centre on Sonic at width 256, but wide uses a bounded 4 px/update takeover/release. SEZ3, MGHZ3, AQZ3: ROM-form follow (lead 104/136, deadzone +-8, 7 px cap) at 256 and a 4 px/update bounded adapter at wide, resuming from the last normal camera. These are intentional adapters.
* Camera at state `$20` in the POC: Sonic held at screen centre (canonical case); the ROM's lead puts him at about screen X 104-120. Owned by C1-I I1, not repeated here.
* Run-off: POC clear threshold `viewW+33` is the ROM relationship; in the 640 px harness case Sonic stays on screen until the flag (screen X 675 at flag), as expected for the adapter.

### T1.4 Boss-defeat sparkles (EMULATED, THZ3)

`$0A` parameter 0 controller lives from the release (u321) to the flag; first sparkle 10 updates later, then **one every 8 updates**; each sparkle `$0A/$FF` is created at **Sonic's current world position** with offset **(0,-12) and (0,-8) alternating**, never moves in world space (displacement (0,0)), shows frames 5,5,5,5,6,6,6,6 repeating, and lasts 29 rows (28 after creation). 20 sparkles to the zone change. The POC emitter (`OBJ_chaos_boss_effect`: mod 8, dy -12/-8, life 28, frames alternate each 4) matches by reading. Ring-pickup sparkles are a different mechanism (terrain/ring probe, frames 5/6 of the type `$09` mapping) and must stay separate.

### T1.5 Palette flashes and "inherited" flashes

ROM facts: boss palette swap = **instant**, sprite colours 13-15 only, a few updates after state 3, with no BG change and no fade. Hit flash = sprite colours 13/14 white on command calls 4-7. Act-clear and zone-clear fades are all **white then black**, three 5-frame steps (T1.2). Nothing flashes at boss creation or defeat. Because the sprite palette is shared, every sprite that uses colours 13-15 changes at the swap; the POC pre-bakes boss sprites and has not been checked for Sonic/ring/HUD pixels on those colours (T1-06, research follow-up R-T1-2). An "inherited" POC flash that does not match the list above should be treated as non-canonical; none was found in source, so this needs the F5 look.

### T1.6 Stale boss-clear sprite test

`node verification/verify_thz3_boss_clear.js` on `ac021e1` fails at line 84: `actual 'SPR_chaos_player_frame_02'`, `expected 'SPR_player_walk'`. VISUAL-P1 changed state `$20` to the ROM selector frames; the test and the committed `thz3-boss-clear-trace.json` still describe the legacy sprite. Per AGENTS section 6 this is an inherited expectation, not parity proof. Fix = update the expectation to the ROM frame sequence and regenerate the trace; keep the attack-bit assertion.

### T1.7 Sonic disappearing after a boss (UNVERIFIED)

Not reproduced. The committed per-update THZ3 trace (canonical and 640 px) shows Sonic visible every update with no camera step above 7. In the ROM Sonic leaves the screen on the right in the last 40 px of the run and the frozen scene fades (canonical). Hypotheses, none proven: H1 camera snap (T1-01/02) mistaken for loss; H2 invulnerability blink after the final hit; H3 canonical off-screen run followed by a next-act start carrying velocity (the harness has no next room); H4 a view/depth change. Decisive probe (R-T1-3): Windows capture plus a per-update dump of player `visible`, `image_alpha`, `x`, `vx`, view X for 600 updates after the boss converts.

## Prioritised discrepancy register (`data/t1/discrepancy-register.json`)

| Pri | ID | Item | Class | Kind |
|---|---|---|---|---|
| 1 | V1-01..04 | Twist sprite, rotation, cadence, facing | confirmed mismatch | purely visual |
| 2 | T1-01, T1-02 | THZ3 boss-entry and release camera snaps | confirmed mismatch | camera ownership |
| 3 | T1-12 | Sonic vanishes after boss | unverified | undetermined |
| 4 | T1-05, V1-07 | Stale clear-sprite test; twist tests assert no visuals | test gap | tests |
| 5 | T1-06 | Shared sprite-palette swap effect on other sprites | unverified | visual |
| 6 | V1-05, T1-07, T1-08 | Priority overlay, hit flash, fade timing | verify in F5 | none expected |
| 7 | T1-03 | GPZ3 centring at 256 | adapter | camera (256 only) |
| info | T1-04, T1-09..11, V1-06, V1-08, T1-13, T1-14 | matches, ROM facts, gaps | | |

## Recommended implementation packages

| Package | Content | Changes | Depends on |
|---|---|---|---|
| **PKG-V1** | Twist presentation per the contract; add the oracle test and a negative control | purely visual (plus removal of a non-ROM facing-flag write) | nothing; assets exist |
| **PKG-T1B** | Fix `verify_thz3_boss_clear.js` expectation and trace; add boss-camera continuity assertions (no step above 7 at 256, above 4 at wide) for all six bosses | tests | none |
| **PKG-T1A** | THZ3 boss camera: keep the ordinary follow owner, raise the left limit only, bounded takeover/release like SEZ/MGHZ; optionally GPZ3 at 256 | camera ownership | final C1-I SHA (I1 owns the follow rule) and decision D-T1-1 |
| **R-T1-2 / R-T1-3** | Palette-colour use check; Windows disappearance probe | research | Windows session |
| (hold) | Any player-state or object-lifecycle change | none authorised | R-T1-3 result |

Classification summary: **purely visual** V1-01..04, T1-06; **camera ownership** T1-01..03; **player-state / lifecycle** none confirmed (T1-12 undetermined).
Suggested build order: PKG-V1 and PKG-T1B together (no dependencies), then PKG-T1A after C1-I.
Decisions for Manager: D-T1-1 THZ3 camera at wide: reuse the SEZ/MGHZ bounded 4 px/update adapter (recommended) or the 7 px ROM cap; D-T1-2 whether GPZ3's 256 branch is worth touching (recommended: no).

## Lean verification and Windows F5 acceptance

Focused checks only; previously accepted systems were not rerun. PKG-V1: oracle replay in the JS harness, MGHZ2 facing constancy, negative control, state differential against `ac021e1` for the same input script. PKG-T1B: the corrected test passes on the parent's mechanics and fails if `SPR_player_walk` returns. PKG-T1A: camera-step series equals the ROM series at 256 (7 px cap) and has no step above 4 at wide, at creation, pan, release and state `$20`.
F5 (new behaviour only): THZ1 and THZ2 right and left strip runs; MGHZ2 chute; THZ3 approach (no jump when the boss appears), fight, defeat and run-off (no jump at release; sparkle trail every 8 updates behind Sonic); one SEZ3 or MGHZ3 defeat for comparison; one ordinary act clear checking the fade chain; and the R-T1-3 capture. Smoke: none beyond that.

## Limits

Approximate VDP/IRQ model; harness frames are not updates for timing across the fade chain (counted separately); three bosses were driven by forcing their defeat state, three were intro-only; EEZ3 boss not created from the chosen arrival; AQZ3 and GPZ3 defeat/run-off not re-traced; no GameMaker/Windows run; C1-I SHA unavailable; POC private PNG payloads (including the foreground atlas) not inspected, so the overlay is verified from its generator and verifier, not pixels.
Reproduce: `python tools/v1_t1_trace.py ROM --check`, `python tools/v1_t1_register.py --check`, `python -m unittest tests.test_v1_t1_audit`.

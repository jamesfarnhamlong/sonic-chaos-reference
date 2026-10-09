# Player spring / airborne state closure (states `$09 $0A $0B $0E $1B $1C`)

Research only; `SonicChaos_POC` and GameMaker were not modified. ROM: Sonic Chaos (Europe) v1.2, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified; never committed).
Branch `research/player-spring-airborne-closure` (cut from Research `main` `eb4bf95`), **uncommitted, awaiting Manager review - not merged**.

Machine-readable result: `data/rom-cache/player-spring-airborne.json` (about 0.7 MB: hashes and per-update rows only, no ROM bytes, no pixels).
Tool: `tools/player_spring_airborne.py`. Tests: `tests/test_player_spring_airborne.py` (54 tests, 92 s with the ROM). Approval board (git-ignored):
`build/player-spring-airborne/approval-board.png`.

Evidence labels: **DECODED**, **BYTE-VERIFIED** (disassembled bytes), **CONTROLLED** (original Z80 routine called on `tools/oracle.py`),
**EMULATED** (whole original game in `tools/sms_frame_harness.py`, PC hooks, rows recorded once per player update), **SYNTHETIC** (state/cells patched in
RAM for a control, never a canonical placement), **OBSERVATION** (supplied original-game video), **POC SOURCE** (read-only), **UNRESOLVED**.

Conventions: speeds are signed 8.8 fixed point (`$FB00` = -5.0 px/update). `+$01` current ("executing") state `$D501`, `+$02` requested state `$D502`,
`+$03` movement flags `$D503` (bit 0 airborne, bit 1 attack/rolling posture), `+$04` bit 4 facing/mirror, `+$06` animation frame, `+$07` record counter.
**A row `u` of an emulated trace is the state after player update `u`**: `+$01`/frame/counter are what the engine executed and drew during update `u`,
position/speed/flags are the end of that update, `+$02` is what the callback requested for update `u+1`. Names such as "fall" or "jump" are not used as evidence;
states are written "state `$XX` - callback, frames, flags".

## 1. Result in brief

**Answer to the key question - what does Sonic visibly use after / between spring launches, and which ROM state owns it?**

| Moment in a spring corridor | Executing state | Visible animation | Update cadence |
|---|---|---|---|
| after a diagonal terrain spring (`$1C`), a weak type-`$26`/`$50` bounce (`$0B`, `$D448` bit 0 clear), or a strip fall (`$14`) | `$1C` / `$0B` / `$14` | the **tumble set**, frames `$1C..$21` | `$1C` 8 updates per frame, `$0B` 4, `$14` 4 |
| after a strong upright launch (type `$26` parameter 0, terrain upright `$30/$31`, type `$21` stomp, AQZ type `$30`) | `$0B` with `$D448` bit 0 set | frame `$61` held | one 4-update record repeated |
| after the apex, a ledge run-off, a ceiling bump | `$0E` | the **fall set**: frames `$02,$03,$04,$05,$06,$01` (upright limbed poses) | 8 updates per frame |
| after a ceiling-spring block (`$3A/$3B`), the breakable-block bounce, a horizontal spring, a jump | `$1B` / `$09` / `$0A` | the **spin set** `$25..$29` (selector `$8F76`, pseudo-random order) | 3 updates per frame in the air |

1. `$0E` is **not** a bare movement state: it has its own animation program (callback `$03AD`, 29 records of 8 updates, frames `$02..$06,$01`) and a
   distinct wrapper `$3A37`. The inherited Sonic-2 generic fall presentation corresponds to none of the original rows above; four distinct ROM presentations
   (fall set, tumble set, tall pose `$61`, spin set) are being collapsed into two Sonic-2 sprites by the POC.
2. The weak type-`$26` spring and the THZ3 boss (`$50`) bounce are **one canonical contract**: same request (`$0B`), same `$D448 = 0`, same `$D503 = 1`, same
   82-update script of frames `$1C..$21`; they differ only in launch Y speed (-5.0 vs -4.0).
3. A spring can replace the pending request before the apex only in the cases listed in section 6.4 (ceiling-spring blocks and horizontal springs). Upright and
   diagonal terrain springs and type `$26` cannot fire while the player is rising. **New and decisive for the AQZ chain:** a ceiling-spring block `$3A/$3B` also fires on a
   player who is *falling* onto it (correction C1, section 8); the POC only dispatches it from the ceiling pass.
4. All frames the POC lacks were recovered from ROM data (section 7). None of `$01-$06, $1C-$21, $25-$29, $61` exists in the POC project (silhouette scan of 1,146
   sprite PNGs, positive control = frames `$38-$3A`).
5. The supplied walkthrough clip corroborates the tumble set (frame `$1D` held 4-5 video frames) and the plain ball `$29` (section 9).

## 2. Method

* `tools/player_spring_airborne.py` decodes the state scripts through the accepted `player_animation_counter.script_program` and an interpreter of `FF 08 / 0E / 0F / 07`,
  decodes mapping frames and the interrupt-side tile-transfer table, calls the original wrappers / setters / handlers on the Oracle, and runs the whole game in
  the frame harness (THZ1, THZ3, AQZ2, AQZ3).
* PC hooks on the engine addresses count **only while bank 1 is mapped in slot 1** (`mm.slot[1] == 1`). During collision work the game maps bank 2 there, and the same
  CPU addresses then execute different code; unguarded hooks produced false launch events during development.
* Open-air fixtures patch cells (`SYNTHETIC`). Natural traces (AQZ3 from the start with Right held) patch nothing.

## 3. The six states, aspect by aspect

Common to all six: the callback is the per-state wrapper reached through the vector in the fixed low ROM; every wrapper begins `CALL $3FEF` (shared movement:
input `$4141`, X `$402A`, Y `$4097`, terrain pass `$690B` = floor `$691A`, sides `$715E`, ceiling pass `$73C9`, terrain-ring/special probe `$753E`, merge `$64CB`).
Collision extents are 8x24 in every state (`docs/collision-geometry-audit.md`). The engine order is `$64FA` animation engine, then the callback (`$5E91`), then `$4A74`:
a request written by the callback of update `N` becomes the executing state at the start of update `N+1`, and the script restarts only when the executing state changes.

### 3.1 State `$0B` - callback `$039E -> $393B`; frames `$1C..$21` (`$D448` bit 0 clear) / `$61` (set); `$D503 = 1`

| # | Aspect | Result |
|---|---|---|
| 1-3 | script, frames, timing | script `$814A` (ROM `$3014A`): `FF 08 [$818F -> $8189]`, `FF 0E 02`, six records (4 updates, frames `$1C..$21`) looped twice by `FF 0F`, then (4,`$1C`)(4,`$1D`)(6,`$1E`)(6,`$1F`)(6,`$20`)(8,`$21`), `FF 00`: **82-update cycle**. Branch fragment `$8189`: one record (4, `$61`), `FF 00`. `$D448` is read **only when the script (re)starts** |
| 4 | mapping / mirroring | type-1 table `$80C8` (ROM `$3C0C8`); `$1C..$21` at `$82B5,$82C0,$82CB,$82D6,$82E1,$82EC` (24x32, origin (12,32)); `$61` at `$85AC` (16x48, origin (9,44)); facing = `+$04` bit 4 |
| 5 | animation callback | every record `$039E` |
| 6 | movement callback | `$393B`: `CALL $3FEF`; requested still `$0B`? then floor flag `+$23` bit 1 -> `JP $45CE`; Y-speed high byte non-negative -> `JP $463C`; else `JP $48A7` |
| 7 | gravity | +24/256 dry, +12 water (EMULATED, open air); down-cap +7.0 / +4.0 |
| 8 | horizontal control | `dry_nonnegative (-64,16)`, `dry_negative (-16,64)`: braking against the motion is 64/256 per update; `no_direction (16,-16)` drag; cap `$D373 = $0400`; facing follows held Left/Right every update (`$48A7`) |
| 9 | terrain / probes | shared pass; ring-probe eligible (parity-dependent `$753E` probe) |
| 10, 15 | transitions to `$0E` | **apex**: after gravity the Y-speed high byte is non-negative (start vy >= -24; CONTROLLED sweeps in the cache and -300..+300 in the tests, 0 exceptions) -> `$463C`: request `$0E`, vy +1.0, airborne set, attack clear. A ceiling bump sets vy +1.0, so the same test fires at once (weak arc 54 updates in open air, 29 in situ under a THZ1 platform) |
| 11 | ordering | the setter writes `+$02`; the old state still draws for that update, the new script starts one update later (first record's full duration) |
| 12 | `$D503` | airborne 1, attack 0 |
| 13 | damages? | **no** (attack bit clear): breakable `$0D/$16` blocks are not broken, badnik callbacks read bit 1 |
| 14 | springs retrigger | terrain upright/diagonal and type `$26` need floor flag **and** Y speed >= 0, impossible while rising; possible at/after the apex (section 6.4) |
| 16 | next spring before the apex | only ceiling-spring blocks and horizontal springs (section 6.4) |

### 3.2 State `$1C` - callback `$03B6 -> $3955`; frames `$1C..$21`; `$D503 = 3`

| # | Aspect | Result |
|---|---|---|
| 1-3 | script / timing | `$8194` (ROM `$30194`): six records of 8 updates (frames `$1C..$21`), `FF 00`: 48-update cycle; **no `$D448` condition** (the diagonal spring stores `$D448 = 0` but `$1C` never reads it) |
| 4-5 | mapping / callback | same frames as `$0B` weak; every record `$03B6` |
| 6 | movement callback | `$3955`: shared movement; requested still `$1C`? floor -> `$45CE`; Y speed non-negative -> `$463C`; otherwise `RET` (**no facing update**) |
| 7 | gravity | +48/256 dry (+24 water) |
| 8 | horizontal | `(-16,16)` both signs; `no_direction (0,0)`: **no drag at all** (vx constant in open air); cap `$0400` |
| 10, 15 | transition | apex or ceiling bump -> `$0E` (attack bit cleared); landing -> state 5 |
| 12-13 | `$D503`, damage | 3 until the apex request, then 1: **attacks** while 3 (breaks `$0D/$16` blocks, CONTROLLED); not after the apex |
| 14, 16 | springs | as `$0B`; plus a diagonal re-launch in the apex update wins over the apex (section 6.4) |

### 3.3 State `$0E` - callback `$03AD -> $3A37`; frames `$02,$03,$04,$05,$06,$01`; `$D503 = 1`

| # | Aspect | Result |
|---|---|---|
| 1-3 | script / timing | `$81E0` (ROM `$301E0`): **29 records of 8 updates** = frames `$02..$06,$01` four times then `$02..$06`, `FF 00` (232-update program; the last `$01` is dropped once per cycle) |
| 4-5 | mapping / callback | `$02 $8197`, `$03 $81A2`, `$04 $81AD`, `$05 $81B8`, `$06 $81C3`, `$01 $818C`; callback `$03AD` |
| 6 | movement callback | `$3A37`: shared movement; requested still `$0E`? floor -> `$45CE`; **no apex test, no facing update** |
| 7 | gravity | +48/256 dry (+24 water), terminal +7.0 (reached at update 38 from rest) |
| 8 | horizontal | `(-16,16)`; drag `(16,-16)` without input; facing **never** changed by input |
| 10, 15 | how `$0E` is entered | `$463C` callers (BYTE-VERIFIED scan): `$393B`/`$3955` apex wrappers, ceiling bump, empty-floor pass `$6C7C` (any non-airborne state except `$09`, which goes to `$0A` through `$4699`), `$3F09/$3F83` (scripted movement, not examined), state `$11` expiry, vector `$039B` (bank `$0F:$9ABE`) |
| 12-14 | flags, damage, springs | `$D503 = 1`; no attack; **every** spring family can replace it: terrain upright/diagonal and type `$26` (floor flag + Y speed >= 0 holds while falling onto them), ceiling blocks (also from above), horizontal |

### 3.4 State `$0A` - callback `$03B3 -> $3901`; selector `$8F76`; `$D503 = 3`

Script `$8142`: `FF 05 [$8F76, vector $03B3]`, `FF 00`. The selector advances `$D52F` (wraps at 20), takes the frame from table `$8FB8` (Sonic: 20 entries over `$25..$29`),
duration 3 in the air / `$8FE0[|vx hi|]` on the floor (10,8,6,5,4,3,2,...), and sets facing from input at each reload (air) or from the X speed sign (floor).
Wrapper `$3901`: held-jump counter `$D3B2` (below), shared movement, then landing `$45CE` when the floor flag is set unless `$D36C = $0D`.
**There is no apex transition**: `$463C` returns immediately when the executing state is `$0A`, so a jump stays `$0A` through ascent, apex and descent.
Held jump (CONTROLLED sweep): counter += 1 and, while the new counter < 14, vy := `$FBC0` (-4.25) / `$FCC0` (-3.25 water) before gravity (+48, water +24); without a
button the counter is set to `$20`. Control `(-64,16)/(-16,64)`, drag `(16,-16)` like `$0B`. Attacks.

### 3.5 State `$09` - callback `$03C5 -> $38C5 -> $37F4`; selector `$8F76`; `$D503 = 2`

Rolling state. Entered by a horizontal terrain spring (vx +/-6.0, cap `$0600`, **airborne bit cleared**, attack set) or a roll. With the airborne bit clear the integrator `$4097`
takes the ground branch: **no gravity**; a negative Y speed is replaced by its magnitude (EMULATED AQZ3 update 15-16: vy -736 -> +736) and the floor flag forces `+7.0`.
In the air (no floor) the empty-floor pass `$6C7C` sees state 9 and calls `$4699`: request `$0A`, vy 0, airborne + attack set - so a horizontal spring hit mid-flight gives
`$09` for two updates and then `$0A`. Control tables `(-16,-4)/(4,16)`, drag `(5,-5)`. Attacks.

**Same-state horizontal contact (Manager amendment; CANONICAL - preserve it).** With `$09` already executing, the horizontal setter requests `$09` again; wrapper `$38C5` only tests `requested == 9`,
so it continues into `$37F4`, which looks at the sign of the X speed the setter just wrote and the held direction: positive vx + Left held -> `$47B6`, negative vx + Right held -> `$47C9`
(airborne bit clear: sound `$A1`, attack cleared, request `7` / `8`). CONTROLLED (`$4849` then `$37F4`, vx +6.0): no input -> request 9, `$D503` 2; Left held -> request **7**, `$D503` 0. EMULATED (THZ1 `$33`
at (3200,832), grounded roll running left, update 20): setter exit executing 9 / request 9 / `$D503` 2 / vx +1536; end of update, Left held: request `$07`, `$D503` 0, vx +1536, vy +1792, frame `$26` counter 1
(state 9's frame/counter untouched); update 21 executes `$07` (frame `$15`). No input: request stays 9, `$D503` 2, frames `$26,$27...`. The POC behavior is the original's.

### 3.6 State `$1B` - callback `$03C8 -> $38D1`; selector `$8F76`; `$D503 = 3`

Entered by ceiling-spring blocks (vx +4.0, vy +5.5), type `$15` (vy +7.5), the ramp launch, the THZ3 boss hit response (direct `LD A,$1B / LD ($D502),A` at bank `$1E:$8147`) and a bank-`$0C` object through vector `$03BF` (`$9204`, not identified). Gravity +36/256 (+18 water). Wrapper `$38D1`:
shared movement; while airborne **nothing else** (no apex, no `$0E`); with the floor flag it clears the airborne bit (`$D503` becomes 2), then jump -> `$45ED`, near-zero speed -> `$45B3`
(state 1), otherwise `$1B` continues on the ground as an attack. Running off a ledge from grounded `$1B` is `$463C` -> `$0E` (AQZ3 update 344). Control `(-16,16)`, drag `(2,-2)`.
Breaks `$0D/$16` blocks (AQZ3 update 294: vy -1088).

### 3.7 State `$14` (comparator)

Third consumer of the tumble set: script `$81C6`, six records of 4 updates, frames `$1C..$21`, callback `$03F8 -> $3A48`, entered only by the strip-fall setter `$4663`, all-zero air control
(`docs/player-fall-control-audit.md`).

## 4. State `$0B` closure: both `$D448` branches and every caller

* **Strong** (`$D448` bit 0 = 1): frame `$61`, mapping `$85AC` (bank `$05` tiles `$A7C0`, ROM `$167C0`), one record of 4 updates repeated; each restart re-reads `$D448`.
  Written by: terrain upright `$6A87` (`$FF`, vy `$F880`), type `$21` top stomp `$B2CC` (`$FF`, `$F940`), type `$26`/`$30` fixed/span `$82F8`/`$8420` (`$FF` for parameter 0, vy `$F8A0`).
* **Weak** (bit 0 = 0): frames `$1C..$21`. Written by: type `$26` nonzero parameter / span with aux1 != 0 (`$00`, vy `$FB00`), type `$50` bounce `$99CA` (`$00`, vy `$FC00`).
  The diagonal spring also stores 0 but enters `$1C`.
* **All natural callers** (BYTE-VERIFIED absolute-address scan, `setter_callers` in the cache): the upright setter `$480C` is reached only from `$5F21` (vector `$035F`) and `$6A8D`
  (terrain); the vector `$035F` is called only from bank `$0C:$B2D2` (type `$21`), bank `$1E:$82FB` and `$8423` (type `$26`/`$30` fixed and span) and bank `$1E:$99D0` (type `$50`). No other caller exists.
* EMULATED entry rows (`d448_on_entry_to_0B`): every strong entry shows `$FF` and first frame `$61`; every weak entry `$00` and first frame `$1C`; the THZ3 boss fixture presets `$FF` and the bounce stores `0`.
* Callers differ in **velocity only**, never in state/animation: -7.5 (terrain), -7.375 (`$26`/`$30` strong), -6.75 (`$21`), -5.0 (`$26` weak), -4.0 (`$50`).
* Flight lengths in open air (EMULATED): terrain upright 80 updates, strong `$26` 79, `$21` stomp 72, weak `$26` 54, boss bounce 43; the `$1C` diagonal arc is 38 updates in THZ (vy -7.0) and 29-30 in AQZ (vy -5.5, shortened by ceilings).
* **A stronger launch during a weak script does not change the frames:** with the weak script running, an upright launch (vy -1920, `$D448 = $FF`) leaves state `$0B` requested
  again (same state, no restart) and the frames keep following the weak program until the 82-update script restarts (`apex_ordering`, row 1-5: frames `$1C,$1C,$1C,$1C,$1D`).

## 5. THZ3 boss bounce vs weak type `$26`

End to end (EMULATED, `type50_boss_top_bounce`): contact = top-classified, non-rising contact (`docs/thz3-boss-contact-followup.md`: `abs(dx) <= 28`, top bounce at `dy <= -35`, works for non-attacking, hurt and blinking Sonic)
-> helper -> vector `$035F` -> `$480C` with HL `$FC00` -> `+$02 = $0B`, vy -1024, `$D448 := 0` (preset `$FF`, row 2 shows `0`), `$D503 = 1`, floor flag cleared. Executing `$0B` from update 3:
frames `$1C x4, $1D x4, ...` identical to the weak type-`$26` rows (`t26_weak_fixed`), 43 updates of ascent, apex `$463C` -> `$0E`, landing -> state 5.
**Explicit canonical shared contract:** type `$26` weak and type `$50` top bounce share one player-animation program; the POC must not give the boss bounce its own presentation.

## 6. AQZ spring-chain study

### 6.1 Where the clip is

AQZ2 and AQZ3 contain the terrain springs (`$30/$31` upright, `$36..$39` diagonal, `$32..$35` horizontal, `$3A/$3B` ceiling) and the breakable blocks `$9B/$9C` (`$0D`) / `$47` (`$16`).
AQZ3 (80x16 cells) is the corridor: ceiling blocks at (800,160) (1216,160) (1344,160) (1472,160) (544,288) (672,288) (928,288), diagonals `$37` at x 480..1408, `$39` at (800,288) (1056,288),
horizontal `$33` (992,224), type `$30` strong spring at (944,256). AQZ2 has a zig-zag shaft: left-diagonal `$39` at x 3104 (y 704..896) against right-diagonal `$37` at x 2976 (y 736, 800).
The ramp at the start of the clip and the corridor match AQZ3 (section 9); AQZ2's shaft is covered as the second chain.

### 6.2 AQZ3 natural run (EMULATED, Right held from the start, no jump; `aqz3_natural_run`)

| Update | Executing -> requested | Event | Position / speed after the update | `$D503` | Animation |
|---:|---|---|---|:-:|---|
| 125 | `$06 -> $1C` | diagonal setter `$482D`, HL `$FA80` (-5.5) | (487,350) vx +4.0 vy -5.5 | 3 | `$1C` frames from 126: `$1C` x8, `$1D` x6 |
| 139 | `$1C -> $0E` | apex `$463C` (ceiling above shortens the arc to 14 updates) | (543,294) vy +1.0 | 1 | `$0E` frame `$02` from 140 |
| 142 | `$0E -> $1B` | ceiling block `$3B` (set `$1B`), **vy was +400: falling onto it** | (555,312) vx +4.0 vy +5.5 | 3 | spin frames from 143 (3 updates each) |
| 152 | `$1B` | floor flag: airborne bit cleared | (595,366) | 2 | still `$1B` on the ground |
| 157 | `$1B -> $1C` | diagonal setter while grounded `$1B` | (615,350) | 3 | `$1C` from 158 |
| 171 / 174 | `$1C -> $0E -> $1B` | apex, then ceiling block while falling | (671,294) / (683,312) | 1 / 3 | as above |
| 189 | `$1B -> $1C` | diagonal | (743,350) | 3 | `$1C` x8, `$1D` x8, `$1E` x8, `$1F` x6 |
| 219 / 227 | `$1C -> $0E -> $1C` | apex then **left** diagonal while falling (vx -4.0) | (823,272) / (823,286) | 1 / 3 | `$0E` frame `$02` x8, then `$1C` |
| 257 / 265 | `$1C -> $0E -> $1C` | apex then right diagonal while falling | (745,208) / (751,222) | 1 / 3 | |
| 278 | `$1C -> $1B` | ceiling block `$3B` replaces the pending `$1C` request **while rising** (no apex ever issued) | (803,184) vx +4.0 vy +5.5 | 3 | `$1C` frames `$1C,$1D` seen, then spin |
| 294 | `$1B -> $1B` | breakable `$0D` block (`$6B2C`): vy -1088, bounce | (867,238) | 3 | spin frames |
| 344 | `$1B -> $0E` | empty floor under a grounded `$1B` (`$6C7C -> $463C`) | (928,181) | 1 | `$0E` from 345 |
| 365 | `$0E -> $0B` | type-`$30` spring, HL `$F8A0` (-7.375), `$D448 = $FF` | (951,238) vy -7.375 | 1 | **frame `$61`** for 79 updates |
| 444 | `$0B -> $0E` | apex (world Y -48: above the top, not fatal, `docs/spring-interaction-audit.md` section 8) | (1080,-48) | 1 | `$0E` |

Per-update rows, segments and events: `aqz_chains.scenarios[aqz3_natural_run]`. The two other AQZ3 chains (`aqz3_diag_ceiling_chain`, `aqz3_left_diag_horizontal_ceiling`) and the AQZ2 shaft
(`aqz2_diagonal_shaft`: five diagonal launches at x 3120 / 2984 / 3127 / 2984 / 3127, the last four from `$0E`; each ascent lasts 30-42 updates before its apex) are in the same section of the cache.

### 6.3 Mid-flight horizontal spring (`aqz3_left_diag_horizontal_ceiling`)

Update 15: executing `$1C` (rising, vy -736) touches a horizontal block: request `$09`, vx +6.0 (cap `$0600`), `$D503 = 2` (airborne **clear**), Y speed untouched. Update 16: state `$09`, vy flipped to +736
(ground branch), update 17: empty-floor pass `$6C7C` sees state 9 -> `$4699`: request `$0A`, vy 0, `$D503 = 3`; update 18: `$0A` (spin frames, gravity +48); landing update 29.

### 6.4 Can the next spring replace the request before the apex?

| Next contact while ... | Result | Evidence |
|---|---|---|
| terrain upright / diagonal / type `$26` while the executing state is rising (`$0B`, `$1C`) | **cannot fire**: floor flag clear and vy negative (both gates); the rising player never has the floor flag | CONTROLLED `spring_gate_matrix` (7 states x 6 gate cases); no accepted upright/diagonal launch with executing state `$0B`/`$1C` in 23 handoff rows |
| ... in the **same update as the apex**, foot probe in the spring's 16-px top | **the launch wins**: request stays `$0B`/`$1C`, vy := launch value, no `$0E`; the animation does not restart (same state) | EMULATED `apex_ordering` (`$0B` over `$30`: vy -1920, `$D448 = $FF`; `$1C` over `$36`: vy -1408, vx +4.0) vs control (`$0E`, vy +1.0) |
| ... after the apex, executing `$0E`/`$1B`/`$1C` grounded | fires (floor flag + vy >= 0): `$0E -> $1C` / `$0B`, `$1B -> $1C` | AQZ3 updates 157, 227, 265, 365 |
| ceiling-spring block `$3A/$3B` | fires **rising** (ceiling pass) **and falling** (ring-probe tail): replaces the pending request with `$1B` | AQZ3 updates 142 (falling), 278 (rising); `ceiling_spring_windows` |
| horizontal spring | no gate at all: replaces any pending request with `$09` | AQZ3 update 15 |
| type `$26`/`$30` object spring | needs the floor flag (cannot fire in flight); contact lock-out 42 / 20 updates per object | `docs/spring-interaction-audit.md` section 3 |

**Why the POC may intermittently fall out of the chain (candidate, not executed):** the POC dispatches the ceiling-spring block only from `SCR_cc_ceiling`, which returns for a falling player
(`support == 0 && (bg & 2 || vy >= 0)`), and its terrain-probe hook handles surface `$1A` only. In the original the chain `$1C -> apex -> $0E -> ceiling block` relies on exactly the falling
launch (AQZ3 updates 142 and 174). Compare the POC against `aqz3_natural_run` rows 125-345.

## 7. Graphics recovery

Frames are rendered from bank `$0F` mapping table `$80C8` with the interrupt-side tile table at ROM `$104B` (4 bytes per frame: bank, source CPU, 64-byte block count) exactly as in
`docs/player-state-11-graphics.md`. Palette: THZ1 sprite palette `$06` (ROM `$3B6AD`) for the board; AQZ1-3 use `$0A` (`$3B6ED`). Index 0 is transparent. Mirroring is the `+$04` bit 4 rule
(piece X mirrored, tile bytes bit-reversed through the table at `$0100`); a horizontal flip of the right-facing image is equivalent.

| Frame | Mapping CPU / ROM | Tile source bank:CPU / ROM | Blocks | Canvas (origin) | Tile SHA-256 |
|---|---|---|---:|---|---|
| `$02` | `$8197` / `$3C197` | `$04:$81C0` / `$101C0` | 6 | 24x32 (15,31) | `f073c93ff306` |
| `$03` | `$81A2` / `$3C1A2` | `$04:$8340` / `$10340` | 6 | 24x32 (14,31) | `0fecaf05e2d9` |
| `$04` | `$81AD` / `$3C1AD` | `$04:$84C0` / `$104C0` | 7 | 32x32 (14,31) | `33ff31397084` |
| `$05` | `$81B8` / `$3C1B8` | `$04:$8680` / `$10680` | 6 | 24x32 (15,31) | `3599bfdf2b11` |
| `$06` | `$81C3` / `$3C1C3` | `$04:$8800` / `$10800` | 6 | 24x32 (16,31) | `d2d455a6e7d1` |
| `$01` | `$818C` / `$3C18C` | `$04:$8000` / `$10000` | 7 | 32x32 (16,31) | `758012b0b7b2` |
| `$1C` | `$82B5` / `$3C2B5` | `$04:$A800` / `$12800` | 6 | 24x32 (12,32) | `eb2c7297e067` |
| `$1D` | `$82C0` / `$3C2C0` | `$04:$A980` / `$12980` | 6 | 24x32 (12,32) | `14fb8c96ddbf` |
| `$1E` | `$82CB` / `$3C2CB` | `$04:$AB00` / `$12B00` | 6 | 24x32 (12,32) | `7bc6fa8a1c9a` |
| `$1F` | `$82D6` / `$3C2D6` | `$04:$AC80` / `$12C80` | 6 | 24x32 (12,32) | `7a5b56d9b5c1` |
| `$20` | `$82E1` / `$3C2E1` | `$04:$AE00` / `$12E00` | 6 | 24x32 (12,32) | `93f904f5eebb` |
| `$21` | `$82EC` / `$3C2EC` | `$04:$AF80` / `$12F80` | 6 | 24x32 (12,32) | `ed76140709bd` |
| `$61` | `$85AC` / `$3C5AC` | `$05:$A7C0` / `$167C0` | 6 | 16x48 (9,44) | `b8a566a4f786` |
| `$25` | `$8318` / `$3C318` | `$04:$B580` / `$13580` | 6 | 24x32 (12,32) | `b1a092488a5c` |
| `$26` | `$8323` / `$3C323` | `$04:$B700` / `$13700` | 6 | 24x32 (12,32) | `0af752a1e984` |
| `$27` | `$832E` / `$3C32E` | `$04:$B880` / `$13880` | 6 | 24x32 (12,32) | `05a94d56c9eb` |
| `$28` | `$8339` / `$3C339` | `$04:$BA00` / `$13A00` | 6 | 24x32 (12,32) | `666bd2d341d7` |
| `$29` | `$8344` / `$3C344` | `$04:$BB80` / `$13B80` | 6 | 24x32 (12,32) | `cfe37ae826d3` |

Usage: `$02..$06,$01` state `$0E`; `$1C..$21` states `$0B` (weak), `$1C`, `$14`; `$61` state `$0B` (strong); `$25..$29` selector `$8F76` (`$09 $0A $10 $1B`). Frame `$61` also appears in other scripts
(`$18 $23 $24 $26 $27 $2A..$2F`, with `$5F/$60`); those uses were not analysed. Board (`build/player-spring-airborne/approval-board.png`, 860x706, PNG SHA-256
recorded in the cache) shows each frame with number, mapping CPU and tile source; the frames are unmodified ROM renders - no interpolation, no redraw.

**Already in the POC?** No. Silhouette comparison (either facing) of all frames against every PNG under `SonicChaos_POC_thz1_cleanup/sprites/*/` at commit `5d99a38` (1,146 files): zero matches for
`$01-$06, $1C-$21, $25-$29, $61`; positive control: frames `$38/$39/$3A` match `SPR_chaos_player_state_11` and its AQZ variant. `python tools/player_spring_airborne.py ROM --poc-scan <sprites dir>` reproduces it
(read-only). The spin set `$25..$29` is outside the requested scope but is in the same class (the POC uses inherited art for `$09/$0A/$10/$1B`).

## 8. Corrections to earlier Research

**C1 - ceiling-spring blocks are also dispatched by the terrain-ring probe.** `docs/spring-interaction-audit.md` section 2.5 / 3 states that `$749D` needs a negative Y speed and a clear floor flag.
That is the gate of the ceiling pass `$73C9` (`$73D3 BIT 1,(IX+$22); RET nz`, `$73D8 BIT 7,(IX+$19); RET z`). `$753E` (called at `$6914`) ends `$7569 CP $14` / `$756B JP $749D`
(unconditional; the `CP` is dead), and `$749D` contains no Y-speed or floor test. The probe point is the parity-dependent ring-probe point. EMULATED (`ceiling_spring_windows`, block `$3B` in open air):
a falling player (`$0E` or `$1C`, vy +1.0) is launched from cell column 9 on (first contact at anchor Y 238), a rising player over the whole width (anchor Y 246-248); the launch is vx +4.0, vy +5.5, `$D503` 3, request `$1B`.
Natural trace: AQZ3 update 142. Classification: **CANONICAL; POC DIVERGENCE candidate** (the earlier audit was not wrong about the ceiling pass; it did not model the second dispatcher).
Note: `$749D` tests the vertical profile left in `D368` by the last `$7666` sample while the tile identity comes from the probe sample (`D353`); in practice both fall in the same cell.

**C2 - `$463C` is not "the apex routine".** Seven absolute call sites (apex wrappers, `$3F09/$3F83`, the empty-floor pass `$6C7C`, state `$11` expiry, vector `$039B`); `$0E` is therefore the
generic airborne-without-spring state. Not a correction of a recorded fact, but the older labels ("falling") should not be read as "entered only at the apex".

## 9. Video corroboration (OBSERVATION)

Supplied files found in `Downloads`: `Aqua Planet Zone - Sonic Chaos - Master System - Walkthrough 05.mp4` (full, 9,774 frames, 30 fps, 640x360, 325.8 s) and `... Walkthrough 05 (1).mp4`
(10 s, 300 frames; timer 0:01 to 0:11, a spring corridor). Only the 10-second clip was analysed (frames extracted to a scratch directory, not into the repo).

* **Plain ball `$29`:** automatic silhouette matching (blue-body mask, scale calibrated on the ball: 1.7 x 1.55 video px per SMS px, either facing) identifies the ball at IoU >= 0.70 on 30 video frames
  (20, 30-31, 37-38, 51, 67-68, 128-132, 142, 153, 159-161, 176, 188-191, 223, 232, 240-241, 248-249, 270).
* **Tumble frame `$1D`:** video frames 42, 58, 75, 96, 116 and 286, rendered at the same scale beside ROM frame `$1D`, show the same curled pose (orange spike up-right, white glove top and lower right) -
  `build/player-spring-airborne/video-corroboration.png`. Runs of that pose last 4-5 video frames (40-43, 57-60, 73-77, 93-97, 114-118) or 8 (281-288) = 8-10 / 16 game updates at 60 Hz,
  which is the 8-update `$1C` record.
* **Cadence elsewhere:** outside those runs the sprite changes every 1-2 video frames (2-4 updates), consistent with the selector's 3-update spin frames; between detected sprite changes (video frames 20-80) the runs are 1 frame x24, 2 frames x14, 3 frames x1, 5 frames x1.
* **Route:** the clip begins on a ramp; the AQZ3 natural run (section 6.2) has the matching ramp (x 259-391, y 239-366) before its first diagonal launch. This is an identification by shape, not by frame-exact replay
  (the video's input stream is unknown, and its run is not the Right-held run).
* **Is the visible original sequence accounted for?** Every pose class seen in the clip is a member of the recovered sets (tumble `$1C..$21`, spin `$25..$29`, upright limbed fall/run frames, plain ball). No pose in the clip
  corresponds to the inherited Sonic-2 jump or fall sprites. Per-frame identification of the limbed tumble poses by the blue-mask matcher is weak (scores 0.3-0.55), so only `$29` and `$1D` are claimed.
  A frame-exact comparison needs the player's input recording; none was supplied.

## 10. State-transition table (`transition_table` in the cache)

| Source mechanism | State | `$D448` | `$D503` on entry | Animation | Next canonical transition |
|---|---|---|---|---|---|
| type `$26` parameter 0 / span aux1 0 (-7.375), terrain upright `$30/$31` (-7.5), type `$21` stomp (-6.75), AQZ type `$30` | `$0B` | `$FF` | 1 | frame `$61` repeated | apex (vy >= 0 after gravity, 79/80/72 updates) -> `$0E`, vy +1.0, `$D503` 1; floor -> state 5 |
| type `$26` parameter != 0 / span aux1 != 0 (-5.0), type `$50` non-rising top bounce (-4.0) | `$0B` | `$00` | 1 | `$1C..$21` x4 updates, 82-update cycle | apex (54 / 43 updates) -> `$0E`; ceiling bump -> immediate; floor -> state 5 |
| terrain diagonal `$36/$37/$38/$39` (vx +/-4.0, vy -7.0 THZ / -5.5 elsewhere) | `$1C` | `$00` (unused) | 3 | `$1C..$21` x8 updates | apex -> `$0E` with attack **cleared**; floor -> state 5 |
| terrain horizontal `$32..$35` (vx +/-6.0, cap `$0600`) | `$09` | untouched | 2 | spin selector | grounded roll; in the air: 2 updates then `$0A` (vy 0) |
| ceiling blocks `$3A/$3B` (vx +4.0, vy +5.5), type `$15` (vy +7.5), ramp, THZ3 boss hit | `$1B` | untouched | 3 | spin selector | no apex; floor -> bit 0 clear, persists as ground attack; ledge -> `$0E`; speed ~0 -> state 1; jump -> `$0A` |
| `$463C` callers (apex, ceiling bump, empty floor, state `$11` expiry) | `$0E` | untouched | 1 | `$02..$06,$01` x8 updates, 232-update program | floor -> state 5; any spring replaces the request |
| jump button, `$4699` | `$0A` | untouched | 3 | spin selector | stays `$0A`; floor -> state 5 (not if `$D36C = $0D`) |
| strip-fall setter `$4663` | `$14` | untouched | 1 | `$1C..$21` x4 updates | floor -> state 5 |

Observed handoffs (`handoff_matrix`, derived from every emulated row): `$06/$05/$01 -> $1C` (diagonal), `$0E -> $1C`, `$1B -> $1C`, `$0E -> $1B` (ceiling block), `$1C -> $1B` (ceiling block, rising),
`$1C -> $09` (horizontal), `$0E/$0A/$01/$05 -> $0B` (upright), `$1C/$0B/$1B -> $0E` (apex / ledge), landings -> 5.

## 11. POC implementation contract

Replace, in `SCR_chaos_core_sprites` (`SCR_chaos_adapter.gml` lines 74-76) and `chaos_spring26_launch_presentation` (`SCR_chaos_spring.gml` line 38), the flag-derived Sonic-2 selection by a **state-derived** selection:

1. Choose the sprite from the executing state `cp_c.state` (not `next`, not `move & 1/2`, not the sign of vy): `$0B` -> weak or strong sprite by the stored `$D448` bit 0 **as read at script (re)start**;
   `$1C` and `$14` -> tumble set; `$0E` -> fall set; `$09 $0A $10 $1B` -> spin set (separate follow-up for the art, same rule).
2. New sprite resources, exact ROM frames, imported without redraw: fall set `$02,$03,$04,$05,$06,$01`; tumble set `$1C..$21`; tall pose `$61`; (spin set `$25..$29`). Origins from the table in section 7.
3. Timing is the player-update counter, not `image_speed`: `$0B` weak 82-update program (4x12, 4, 4, 6, 6, 6, 8), strong 4-update record; `$1C` 6 x 8; `$14` 6 x 4; `$0E` 29 x 8 (232 updates).
   A script restarts only when the executing state changes; re-requesting the executing state (`$1C -> $1C`, `$0B -> $0B`) does not restart it and does not re-read `$D448`.
4. Facing is the `+$04` bit 4 flag, not `sign(vx)`: `$0B` follows held Left/Right every update; `$0E`, `$1C`, `$14` never update it; spin states update it at selector reloads (every 3 updates airborne);
   the diagonal setter sets it from the block. (`SCR_chaos_core_sprites` currently uses `sign(vx)` outside the footwear states: candidate cause of the parked "rapid left/right oscillation after a rebound".)
5. Movement values (already accepted in the POC core; unchanged): gravity `$0B` 24, `$1B` 36, others 48 (water 12 / 18 / 24); controls and drag per section 3; cap `$D373`.
6a. Same-state horizontal contact: keep the order setter (request 9) -> rolling suffix `$37F4` in the same update; opposing held direction replaces the request with `$07`/`$08` and clears attack (do not guard the repeat).
6. Dispatch ceiling-spring blocks `$3A/$3B` from the terrain-ring probe point as well as from the ceiling pass (correction C1), and keep the horizontal-spring-in-air behavior (`$09` two updates, then `$0A` with vy 0).
7. Acceptance fixtures: replay `aqz_chains.scenarios[aqz3_natural_run]` (Right held from (110,238)); expected rows: state, `$D503`, x, y, vx, vy, frame, counter per update. Fixture rows for each flight kind are in
   `emulated_flights_thz`, `stomp_and_boss`, `apex_ordering` and `free_flight`.
8. Windows checks: weak upright spring and THZ3 boss bounce show the tumble frames; strong springs show the tall pose; falling after an apex/ledge shows the limbed fall frames; the AQZ3 corridor never drops out
   (including the falling-into-ceiling-block launches).

## 12. Unresolved, candidates, AGENTS updates

* UNRESOLVED: `$3F09/$3F83` (the scripted movement routine that also calls `$463C`) was not examined; the other uses of frame `$61` in scripts `$18 $23 $24 $26 $27 $2A..$2F`; the `$1D` branch (`$760C`) of the ring-probe
  tail; water variants of horizontal control are decoded from the tables only (water gravity is emulated); the video input recording.
* POC DIVERGENCE candidates (read-only, not executed): the ceiling-spring dispatch (C1), `sign(vx)` facing, `SPR_player_jump` forced on every type-`$26` launch, `SPR_player_jump` for state `$12`
  (script frame `$0B` is the upright standing pose).
* AGENTS candidate updates: (a) "State `$0E` has its own 232-update fall animation (frames `$02..$06,$01`); `$0B` weak/`$1C`/`$14` use frames `$1C..$21`; `$0B` strong uses `$61`; the weak type-`$26` and THZ3 boss bounce share one program."
  (b) "Ceiling-spring blocks `$3A/$3B` are dispatched by both the ceiling pass (rising) and the terrain-ring probe (any Y speed)." (c) "Sprite selection follows the executing state and restarts only on a state change."
  (d) "Hook PC events only while bank 1 is mapped in slot 1."

## 13. Reproduce

```sh
python tools/player_spring_airborne.py path/to/SonicChaos.sms            # writes the cache and build/player-spring-airborne/*.png (about 3 minutes)
python tools/player_spring_airborne.py path/to/SonicChaos.sms --check    # byte-compares the cache with a fresh build
python tools/player_spring_airborne.py path/to/SonicChaos.sms --poc-scan path/to/POC/sprites   # read-only POC asset comparison
python -m unittest tests.test_player_spring_airborne                      # cache locks + ROM-backed re-execution (ROM tests skip without the ROM)
```

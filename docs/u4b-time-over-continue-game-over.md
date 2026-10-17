# U4-B - Original TIME OVER, Continue and Game Over presentation

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified, never committed).
Base: accepted Research main `fdfe8effcf1c03d5ffd621d47c81f56038c5aeb7`, branch `research/u4b-time-over-continue-game-over`. No POC branch, GameMaker project, Igor, executable package or ROM bytes were touched or added.
Requested by Manager-san #4 as the evidence for the combined G2-C/G2-D milestone. U4-A (`docs/u4-ordinary-results.md`) already covers the ordinary results card and is not repeated.

| | |
|---|---|
| Tool | `tools/u4b_screens.py` (`ROM`, `ROM --check`, `--only static`, `--validate`, `--doc`, `--poc PATH`) |
| Committed data | `data/u4b/death-screens-static.json` (decoded facts), `data/u4b/death-screens-observed.json` (emulated original-code runs and their verdicts), `data/u4b/audio-requests.json`, `data/u4b/audit.json` (existing Research evidence and POC inventory), `data/u4b/export-manifest.json` (hashes of the exported graphics) |
| Ignored exports | `build/u4b/` - 34 indexed PNGs listed in the manifest, `palettes.json` with fade ramps, 4 emulated comparison PNGs. Regenerated bit-exactly; their index-data hashes are committed |
| Tests | `tests/test_u4b_screens.py` (no-ROM part and ROM part) |
| Builds on | `docs/g0-campaign-contract.md` (T07/T08/T09 flow and timings), `docs/audio-request-audit.md`, `docs/u4-ordinary-results.md` (fade engine model, tile decoder), `tools/g0_rig.py` |

Evidence classes (every claim below carries one): **DECODED DATA** (read from ROM bytes), **BYTE-VERIFIED ASSEMBLY** (routine regions with offset/length/SHA-256; draw, loader, fade-request, wait-loop and sound operands parsed from the code bytes),
**SOURCE-TRACED BEHAVIOUR** (hand disassembly), **MODEL VERIFIED AGAINST THE ORIGINAL CODE** (a Python composition compared with the emulated VRAM/CRAM/SAT and rendered pixels, 0 mismatches), **EMULATED ORIGINAL FRAME**
(`tools/g0_rig.py`, approximate VDP, NTSC frame timing, +/-1 frame), **CONTROLLED VARIANT** (RAM presets and scripted one-frame button edges, listed per scenario) and **UNRESOLVED** (section 11).
Numbers `$xx` are hexadecimal; "update" is one `$062D` frame wait; "frame" is a harness frame.

## 1. Answer in one page

1. **Three screens, two tile streams, no sprite art of their own.** TIME OVER, Continue and Game Over are drawn by `$3495`, `$345B` (+`$3478`) and `$3436`. Game Over and Continue **share one 87-tile stream** (`13:$B5AF`, file `0x4F5AF`, loaded by `$7A50` to VRAM `$1800` = tile 192);
   TIME OVER has its own **44-tile stream** (`10:$8A70`, file `0x40A70`, `$7A28`, also VRAM `$1800`). Both go through the same `$24C2` decoder as U4-A (`A = 0`, no remap). Name-table blocks use `$2349` (2-byte cells).
2. **Layouts (cells, row/col from the name-table address):** GAME OVER 17x3 at (8,8) `$3A10` from `13:$BEC5`; CONTINUE banner 15x3 at (3,9) `$38D2` from `13:$BF2B`; countdown frame 6x2 at (11,13) `$3ADA` from `13:$BF85` (star, blank, `0`, `9`, blank, star);
   digit redraw 1x2 at (11,16) `$3AE0` from the glyph table `13:$BF9D + 4*digit`; TIME OVER 17x4 at (10,8) `$3A90` from `10:$8F16`. Every other cell holds the **`$21DA` fill word `$00C0`** (tile 192 = stream tile 0, cleared by `$21DA` then overwritten by the stream).
3. **Palettes (fade requests, all "bit 7 only" = fade in from black):** Game Over BG record `$22` + sprite record 7; Continue BG record `$24` + sprite record 7; TIME OVER BG record `$23` and **no** sprite request (sprite CRAM stays black from the preceding fade).
   Records live at bank 14 `$B64D + 16*n`; `$22` and `$24` are byte-identical (white `$3F`, blues `$20/$39`, `$0A`). TIME OVER is the odd one: BG colour 0 = `$30` (blue), colour 1 = `$0F` (yellow), the rest black; the whole screen is blue behind a black text box.
4. **The Continue character** is the normal player object (type from `D2C8`: 1 Sonic, 2 Tails) in **state `$35`** at screen position (128,160) (IX+`$11` := `$80`, IX+`$14` := `$A0`; camera zero): idle frames `$11,$12` (Sonic) / `$0F,$10` (Tails), **8 updates each, looping**.
   Accepting sets `D526 := $FF`; the idle callback (`$8933` / `$8ECE`) then switches the script to run frames `$07..$0A` (Sonic) / `$07..$09` (Tails), **4 updates each**, with callback `$8946` adding `$0010` to the X speed word every update (`$0338` moves the object): Sonic/Tails run off to the right during the 180-update hold.
5. **Countdown:** digit 9 is drawn by the block, then **10 digits x 116 updates** (`CP $74`): at each rollover `D2CB` is decremented, `$3478` redraws the ones digit 8..0, sound `$B4` follows (nine ticks); after digit 0 the underflow to `$FF` expires the countdown with no redraw and no sound.
6. **Input:** the loop tests `D147 & $30` once per update, after the frame wait. `D147` is the **newly-pressed** byte (`$2451`: current & ~previous, bit 6 masked), so only a fresh edge of button 1 or 2 counts. Measured: an edge in the interrupt of the frame the loop is entered or earlier is ignored, the next one is accepted;
   an edge in the very frame that expires the countdown is still accepted, one frame later is not. A held button, or one pressed during the 16-update set-up loop, never accepts.
7. **Accepted branch:** sound `$A0`, `D2C3` := `(D2C3 - 1) | $80`, run animation, 180-update hold, exit fade, 60-update wait, `$13C9`: lives 3 (Sonic) / 5 (Tails), score 0, same act reloaded (through the act title card). **Expired branch:** exit fade, 60-update wait, Game Over; **`D2C3` is not consumed.**
8. **TIME OVER at 10:00 is a screen of its own, shown before any lives test.** Clock minutes hit BCD `$10` -> `D44B := $C0`, the player routine calls the death routine (sound `$96`), `$15F2` takes the life at once, and after the death animation and fades `$1653` shows TIME OVER (180-update hold, fade, 90-update wait) **even when lives remain**. It then reloads the act, or goes on to Continue / Game Over.
9. **Game Over:** card up about 8 updates after the branch, sound `$87` (**written after the card draw and fade request**), two 240-update holds (not skippable), fade to black, 60-update wait, `JP $04B4` (title). **Buttons do nothing** on TIME OVER or Game Over (a pulse every 20 frames was ignored).
10. **Audio:** `$87`, `$94`, `$A0` are **unsupported in the POC** (no resource) and stay numeric; trigger points in section 8 and `data/u4b/audio-requests.json`. Nothing is substituted. They do not block the screen extraction.

## 2. Routine regions (byte-verified)

<!-- BEGIN u4b:routines -->
| routine | CPU range (end exclusive) | file | bytes | SHA-256 | role |
|---|---|---|---|---|---|
| timer_update | res $27EE-$2885 | 0x027EE | 151 | `6e9bb53b07eb` | clock tick: seconds/minutes BCD, 10:00 sets D44B := $C0 and stops the clock (D2BE := 0), special-stage countdown branch at $2826 |
| player_update | res $361D-$3657 | 0x0361D | 58 | `394729c8763a` | per-update player entry; D44B bit 6 calls the death routine $4984 (TIME OVER) before the engine update |
| death_routine | res $4984-$49C3 | 0x04984 | 63 | `4bcdb9fd1be9` | player death: state $1F, D293 bit 2, keeps D44B bit 7, requests sound $96 (zone < 8) |
| life_lost_branch | res $15F2-$1673 | 0x015F2 | 129 | `4bbd54fc356e` | main-loop D293 bit 2: lives -1 at once, death animation loop, fade slots, TIME OVER gate, lives test, reload or last-life branch |
| game_over_branch | res $138A-$13C9 | 0x0138A | 63 | `74ffa46e69f3` | main-loop D293 bit 6 clear: clears, $13ED continue test, Game Over screen + sound $87, waits, fade, title |
| continue_restore | res $13C9-$13ED | 0x013C9 | 36 | `cb461aa67f2f` | continue accepted: lives 3 (type 1) / 5, score := 0, D293 reload flags, back to the main loop |
| continue_screen | res $13ED-$1464 | 0x013ED | 119 | `cc200555dd3a` | continue test (D2C3 bit 7 cleared), object init, screen draw, sound $94, 16+30 frame set-up, fade-in requests, countdown call, exit fade |
| continue_countdown | res $1464-$148C | 0x01464 | 40 | `c4b9eca58a3e` | frame wait, player update, button test D147 & $30, 116-update digit, digit redraw, sound $B4, expiry |
| continue_accept | res $148C-$14AB | 0x0148C | 31 | `c72ca1fe3da5` | accept: sound $A0, D2C3 -1 with bit 7 set, D526 := $FF (player run script), 180-update wait |
| game_over_screen | res $3436-$345B | 0x03436 | 37 | `fb78271502bb` | tile load (bank 19 stream $B5AF), 3x17 GAME OVER block, fade-in requests (BG record $22, sprite record 7) |
| continue_draw | res $345B-$3478 | 0x0345B | 29 | `e350f531b208` | tile load (same stream), 3x15 CONTINUE block and 2x6 digit/star frame |
| continue_digit_draw | res $3478-$3495 | 0x03478 | 29 | `dfe598c60dc5` | bank 19 page, 1x2 digit glyph from the table at $BF9D + 4*digit |
| time_over_screen | res $3495-$34D3 | 0x03495 | 62 | `998343a60f6b` | clears, tile load (bank 16 stream $8A70), 4x17 TIME OVER block, fade-in (BG record $23), 180-wait, fade out, 90-wait, D44B := 0 |
| time_over_loader | res $7A28-$7A3C | 0x07A28 | 20 | `3a11937378ac` | bank $10, VRAM $1800, tile stream $8A70 through the $24C2 decoder |
| game_over_loader | res $7A50-$7A64 | 0x07A50 | 20 | `c753ffe7b51d` | bank $13, VRAM $1800, tile stream $B5AF through the $24C2 decoder |
| blit_2byte | res $2349-$2383 | 0x02349 | 58 | `ed1527fb32e0` | B rows x C columns of 2-byte name-table cells from DE to the name table at HL (wraps at $3F00 -> $3800) |
| blit_address_adjust | res $23C7-$23F7 | 0x023C7 | 48 | `d8dd0a22e0a7` | adds the camera scroll (D174/D176) to the name-table address; zero after $4FCE |
| input_edge_detect | res $2451-$2496 | 0x02451 | 69 | `3a4e3686da71` | per interrupt: D137 current (pressed = 1), D147/D157 = newly pressed this interrupt (bit 6 masked), history shift |
| frame_wait | res $062D-$063C | 0x0062D | 15 | `c66c1b360269` | EI; waits for the interrupt to set D135, clears it |
| sound_regs | res $18E1-$18ED | 0x018E1 | 12 | `c741d938a54f` | DE09..DE0B := 12,1,2 (music fade parameters) |
| fade_slot_reset | res $1CAF-$1CBD | 0x01CAF | 14 | `f1ae4c770bb0` | D492/D494 := bit 6 only (fade to black) |
| name_table_clear | res $21DA-$220E | 0x021DA | 52 | `4284e62602d1` | frame wait, name table $3800 x $380 words := $00C0 (LD DE,$00C0), VRAM $1800 x 32 bytes := 0, SAT buffer Y := $F0 |
| try_again_screen_out_of_scope | res $34D3-$3522 | 0x034D3 | 79 | `0d583f1a6aea` | ending TRY AGAIN card (sound $98, 1-byte cells D2D3 := 0); outside this task, listed so it is not mistaken for Game Over |
| player_state35_callback_sonic | bank $0C $8933-$8946 | 0x30933 | 19 | `650d6c60f057` | continue-screen idle callback (type 1): D526 == $FF switches the script to the run records |
| player_state35_run_callback | bank $0C $8946-$895A | 0x30946 | 20 | `de5eb5b10447` | run callback: $0338 movement, X speed (+$16/$17) += $0010 per update |
| player_state35_callback_tails | bank $0C $8ECE-$8EE1 | 0x30ECE | 19 | `c4fabf31cc29` | continue-screen idle callback (type 2) |
<!-- END u4b:routines -->

All offsets are resident (`$0000-$7FFF`, file offset = CPU address) except the bank-12 player callbacks. `$34D3-$3522` is the **ending TRY AGAIN card** (sound `$98`, 1-byte cells, `D2D3 := 0`), listed only so it is not mistaken for Game Over.

## 3. Flow from the death to the title (source-traced, emulated)

```
clock 10:00   $27EE..$281E  D44B := $C0, D2BE := 0 (clock stops)
              $361D..$362F  player update: D44B & $40 -> $4984 (death)
death         $4984         state $1F, D293 bit 2, D44B keeps bit 7 only, sound $96 (zone < 8)
life lost     $15F2         lives := lives - 1 (BCD, at once), $3116 HUD, update loop until D51D == 2,
                            60 updates, $1CAF fade to black, 90 updates
              $1653         D44B bit 7 set?  -> $3495 TIME OVER (clears D44B)
              $165B         lives != 0 -> reload the act ($1673: act title card, loader, fade-in)
              $166B         lives == 0 -> D293 bit 6 cleared -> main loop $138A
$138A         $297E $4FCE $21DA, CALL $13ED
$13ED         D2C3 bit 7 cleared; D2C3 == 0 -> RET (no Continue)
              else Continue screen: D2CA := 0, D2CB := 9, object $D500 type D2C8 state $35 at (128,160),
              $345B draw, sound $94, 16 updates (frame wait + player update), fade-in requests, 30 updates, $1464 countdown
$1464         per update: frame wait, $361D, D147 & $30 -> accept; D2CA++ ; D2CA == 116 -> D2CA := 0, D2CB--, $FF -> expired,
              else $3478 redraw + sound $B4
accept $148C  sound $A0, D2C3 := (D2C3 - 1) | $80, D526 := $FF, 180 updates (run animation), RET
$1450         D293 bit 6 cleared, $1CAF fade to black, $18E1, 60 updates, RET
$1396         D2C3 bit 7 set -> $13C9 restore: lives 3/5, score := 0, D293 reload flags -> $1333
              else Game Over: $21DA, $3436 card, sound $87, 240 + 240 updates, $1CAF, $18E1, 60 updates, JP $04B4
```

The decrement happens **before** every screen, so "3 lives" means three attempts and the Game Over test is "lives after the decrement == 0" (G0 T07/T08). TIME OVER at 10:00 uses minutes BCD `$10`, not 9:59.

## 4. TIME OVER screen

* **Graphics (DECODED):** 44-tile stream, 17x4 block at (10,8), BG record `$23`. 29 of its tiles are byte-identical to tiles of the U4-A results stream and 32 to the act-title stream (letters; see section 9). Colour 0 is the screen colour, so the whole 32x24 field is blue; text and its box use colours 1 and 2.
* **Sequence (EMULATED, +/-1):** screen entry at the death fixture +264, CRAM black, the tile load takes about 17 frames, then three visible fade-in passes 5 frames apart (CRAM `1005..`, `200a..`, `300f..`), steady until the 180-update hold ends, three fade-out passes, 90-update wait, exit 275 frames after entry.
  The sprite half of CRAM is black throughout; **no sound is requested** by the screen (the death sound `$96` was requested at the death).
* **Branches:** lives remain -> act reload (act title card, sound `$88`, level music) ; no lives -> `$138A` (Continue or Game Over). `D44B` is cleared at the end so the next life is not affected.
* **Not skippable:** a button pulse every 20 frames changes nothing.

## 5. Continue screen

* **Graphics (DECODED):** banner and star frame from the shared 87-tile stream; digits are 1x2 glyphs of that stream (ten distinct 8x16 glyph pairs; see the manifest strip). The tens column is the block's fixed `0`.
* **Composition (VERIFIED):** the Python composition (name table + sprite SAT + CRAM) equals the emulated VRAM name table, rendered BG pixels, CRAM, SAT, sprite pixels and the dynamically transferred player tiles in **every** capture (117 captures in 18 scenario runs, `captures` in the observed JSON; the player object itself is also compared: type, state `$35`, X 128, Y 160).
* **Character art (DECODED + VERIFIED):** frames are normal player frames: mapping tables `$80C8` (Sonic) / `$85BF` (Tails), six 8x16 pieces (five for Tails frames `$09/$0F/$10`), tile transfers from the `$104B` (Sonic) / `$11CF` (Tails) tables to VRAM `$0000` (12 tiles; 10 for the five-piece frames), sprite palette record 7, SAT Y = screen Y + relative Y, X = screen X + relative X, tile base 0.
  The exported sprite strips are in `build/u4b/sprites/`.
* **Timing (EMULATED):** screen setup 7 frames after the branch (`$345B`), sound `$94` at the setup, fade-in request 21 frames later (after the 16-update loop), three visible fade passes, countdown loop entered 30 updates after the request.
  Digit rollovers every 115-117 harness frames (116 updates), nine `$B4` requests, expiry 1,160 updates after the loop starts.
* **Input and branches:** section 7.

## 6. Game Over screen

* **Graphics (DECODED):** 17x3 block at (8,8) from the shared stream, BG record `$22`, sprite record 7 (no sprites drawn). Blue letters on black.
* **Sequence (EMULATED):** direct (no continues): card entered 156 frames after the pit-death fixture (60 + 90 waits plus the death animation), sound `$87` 8-9 frames after the branch, title entered 538-540 frames after the sound (240 + 240 holds, fade passes, 60-update wait).
  After an **expired countdown** the Game Over branch starts 60 updates after the expiry (the exit fade happens first), then the same 538-frame screen. Not skippable by buttons.
* **Transitions:** `$13C6: JP $04B4` -> title. `D299` stays 0 and score/emeralds/`D2C3` stay stale until the next New Game (G0 T09). Music-fade registers `DE09..DE0B := 12,1,2` (`$18E1`) are written before the title.

## 7. Fades, input timing, accepted and expired branches

All fades use the U4-A engine (`$B45A`): every 5th interrupt one pass. Fade-in from black takes four passes (the first still black, so three visible states 5 frames apart); fade to black takes three. The U4-A model reproduces **every** CRAM series of all 18 scenario runs (`fade_checks`).

<!-- BEGIN u4b:scenarios -->
| scenario | death | character | button edge (frame) | `$A0` | Game Over | act reloaded | end lives / D2C3 / score |
|---|---|---|---|---|---|---|---|
| time_over_lives3 | TIME OVER | Sonic | - | - | no | yes | 02 / 00 / 001230 |
| time_over_no_continue_sonic | TIME OVER | Sonic | - | - | yes | no | 00 / 00 / 001230 |
| time_over_continue_expire_sonic | TIME OVER | Sonic | - | - | yes | no | 00 / 02 / 001230 |
| time_over_continue_expire_tails | TIME OVER | Tails | - | - | yes | no | 00 / 02 / 001230 |
| time_over_continue_accept_sonic | TIME OVER | Sonic | 836 | A0 | no | yes | 03 / 81 / 000000 |
| pit_continue_accept_tails | pit | Tails | 692 | A0 | no | yes | 05 / 82 / 000000 |
| pit_continue_accept_first_poll | pit | Sonic | 208 | A0 | no | yes | 03 / 81 / 000000 |
| pit_continue_press_before_countdown | pit | Sonic | 160 | - | yes | no | 00 / 02 / 001230 |
| pit_continue_button_held | pit | Sonic | - | - | yes | no | 00 / 02 / 001230 |
| pit_game_over_no_continue_sonic | pit | Sonic | - | - | yes | no | 00 / 00 / 001230 |
| pit_game_over_no_continue_tails | pit | Tails | - | - | yes | no | 00 / 00 / 001230 |
<!-- END u4b:scenarios -->

Reference timeline (TIME OVER, unanswered Continue, Game Over; harness frames after the death fixture, +/-1):

<!-- BEGIN u4b:timeline -->
| event | harness frame after the death fixture | ROM |
|---|---|---|
| death fixture frame | 2 | clock reaches 10:00 (`$281C` sets D44B := $C0); `$4984` runs, sound `$96`, life -1 |
| TIME OVER screen | 264 | `$3495`: clears, tile load, 4x17 block, fade-in request |
| TIME OVER exit | 539 | `$34CE`: after 180-update hold, fade-out, 90-update wait; D44B := 0 |
| last-life branch | 540 | `$138A` (D293 bit 6 clear) |
| Continue screen | 542 | `$13F5`: object init, `$345B` draw, sound `$94` |
| Continue fade-in request | 563 | `$1431`: BG record $24, sprite record 7 (after the 16-update set-up loop) |
| countdown loop entered | 593 | `$1464` (after the 30-update wait) |
| digit 8 .. digit 0 redrawn | 710, 825, 942, 1057, 1173, 1289, 1405, 1521, 1637 | `$1482`; sound `$B4` one frame later each |
| countdown expired | 1753 | digit underflow to $FF, return, `$1450` exit fade |
| Game Over branch | 1813 | `$139D` after the 60-update exit wait |
| Game Over card / sound `$87` | 1822 | `$13A3` |
| title | 2360 | `$04B4` after 240 + 240 holds, fade, 60-update wait |
<!-- END u4b:timeline -->

Input edge sweeps (CONTROLLED: one-frame button edge, last-life pit death):

<!-- BEGIN u4b:boundary -->
| delta vs countdown-loop entry | pad frame | outcome |
|---|---|---|
| -6 | 201 | ignored |
| -5 | 202 | ignored |
| -4 | 203 | ignored |
| -3 | 204 | ignored |
| -2 | 205 | ignored |
| -1 | 206 | ignored |
| 0 | 207 | ignored |
| 1 | 208 | accepted |
| 2 | 209 | accepted |
| 3 | 210 | accepted |

| delta vs the frame that expires the countdown | pad frame | outcome |
|---|---|---|
| -9 | 1358 | accepted |
| -8 | 1359 | accepted |
| -7 | 1360 | accepted |
| -6 | 1361 | accepted |
| -5 | 1362 | accepted |
| -4 | 1363 | accepted |
| -3 | 1364 | accepted |
| -2 | 1365 | accepted |
| -1 | 1366 | accepted |
| 0 | 1367 | accepted |
| 1 | 1368 | expired |
| 2 | 1369 | expired |
| 3 | 1370 | expired |
<!-- END u4b:boundary -->

Reading the sweep: the **first accepted edge is the interrupt after the loop is entered**; an edge on the last update of digit 0 (the update that would expire the screen) **is still accepted**; the first edge after that is ignored and Game Over follows.
The accepted press is recorded by the code at `$146A` before `D2CA` is incremented, so the order is test, then count. A PC adapter should poll a fresh press once per update at the same point.

## 8. Audio requests (numbers and trigger points only)

<!-- BEGIN u4b:audio -->
| request | store | trigger | driver | ledger name | POC status |
|---|---|---|---|---|---|
| $96 | $49B6 | player death routine $4984, zone < 8; fires on every death (time over, pit, hurt without rings): the same request that precedes the life-lost loop | music | Player death music | NOT IMPLEMENTED as a request; inherited SND_sonic_death is not asserted to be $96 |
| $94 | $141D | Continue screen entry: sound written after the screen is drawn and before the 16-update set-up loop | music | Continue-screen music | UNSUPPORTED: no verified audio resource in the POC (G2-A) for this request |
| $B4 | $1487 | each countdown digit change 8..0 ($1482 redraw then the request); nine times per unanswered countdown, none for digit 9 or the expiry | sfx | Results tally / continue countdown feedback | NOT VERIFIED: no ROM-verified countdown tick asset wired |
| $A0 | $148E | button edge accepted by the countdown loop ($146A..$148C): once, before D2C3 is decremented | sfx | unresolved | UNSUPPORTED: no verified audio resource in the POC (G2-A) for this request |
| $87 | $13A5 | Game Over screen, written after the card draw and fade request, before the two 240-update holds ($139D branch: no continue, or an expired countdown) | music | Game over music | UNSUPPORTED: no verified audio resource in the POC (G2-A) for this request |
<!-- END u4b:audio -->

* `$96` is requested **once at the death** (`$49B6`), not by any screen. `$B4` is also the tally tick of U4-A and the character-select cursor sound; here it is the digit-change tick.
* `$87`, `$94`, `$A0` appear in `data/rom-cache/audio/request-ledger.json` with driver pointers, but no audio has been rendered or named beyond that ledger. **The POC has no resource for them** (audit below); they must stay silent or be mapped to verified assets later. Do not substitute `SND_sonic_death` or any other music.
* Order and timing observed in the unanswered path: `$96` (death), `$94` (about 8 frames after the Continue branch), nine `$B4` one frame after each digit redraw, `$87` 8-9 frames after the Game Over branch. Accepted path: `$A0` one frame after the press, then the act title `$88` and level music after the reload.

## 9. Shared graphics and the existing Research / POC inventory

* **Within this package:** Game Over and Continue share the 87-tile stream (0 non-blank tiles shared with the TIME OVER stream, 0 with the U4-A results stream, 0 with the act-title stream). TIME OVER shares 29 non-blank tiles with the results stream and 32 with the act-title stream (indices in `shared_tiles_with_results_stream`).
* **Research already holding data:** `data/g0/campaign-oracle.json` and `docs/g0-campaign-contract.md` (flow and frame checkpoints), `data/rom-cache/audio/request-ledger.json`, U4-A tile decoder and fade model, `tools/player_scripts.py` / `thz1_object_assets.py` (the state-`$35` scripts and mappings were already statically parsed; only the frames needed here were exported). Hashes in `data/u4b/audit.json`.
* **POC (accepted G2-A `b91b833aff15e9668f9c7404c2b70dbc003f9f19`, read-only):** has `SPR_chaos_results_tiles`, `SPR_chaos_ss_continue` (the 2x2 results-card icon, not the Continue screen) and `SPR_chaos_title_tiles` (ROM-derived, U4-A). Its Game Over is the **inherited** 141x16 `SPR_menu_game_over` in `ROM_menu_game_over`
  (`OBJ_player_death` alarm 150: `global.life > 0` -> restart, else that room). It has **no TIME OVER screen, no Continue screen, no ROM Game Over card, no fade/title transition for them, and no audio for `$87 $94 $A0`**. The G2-B branch (`ad3f403`) exists but is not accepted and was not audited.

## 10. Asset inventory (exact)

Hashes are of the row-major palette-index bytes (never of PNG bytes) in `data/u4b/export-manifest.json`; all PNGs are ignored output in `build/u4b/`.

| group | files | content |
|---|---|---|
| tile sheets | `tiles/gameover_continue_vram1800.png` (87 tiles), `tiles/time_over_vram1800.png` (44 tiles) | full decoded streams, 16 tiles per row, tile index = 192 + position |
| blocks | `blocks/game_over_block0`, `continue_block0/1`, `time_over_block0`, `continue_digit_glyphs` | the exact tilemap blocks as drawn; glyph strip 0..9 |
| composed frames | `frames/game_over`, `time_over`, `continue_digit0..9`, `continue_sonic_idle0/1`, `continue_tails_idle0/1` | 256x192 palette-index frames (verified equal to the emulator) |
| player frames | `sprites/sonic_frame07..0A,11,12`, `sprites/tails_frame07..09,0F,10` | exact character frames, sprite palette record 7, index 0 transparent |
| palettes | `palettes.json` | the three screens' CRAM and the fade-in / fade-out ramps (RGB = channel x 85, the accepted harness expansion) |
| emulated | `emulated/*.png` | four emulator frames for visual comparison (not hashed in the manifest; checked pixel-for-pixel by the observed layer) |

Committed (small numeric decode only): name-table cell words, palette colour bytes, glyph tile ids, animation script records, mapping offsets, tile-source offsets with SHA-256, tile SHA-256 lists. No pixel data and no ROM bytes.

## 11. Decoded, traced, emulated and unresolved

| item | class |
|---|---|
| streams, blocks, glyph table, fill word, palette records and requests, wait loops, sound operands, player scripts/mappings/tile sources | DECODED DATA / BYTE-VERIFIED ASSEMBLY |
| flow in section 3, TIME OVER gate order, `D2C3`/lives/score effects, input edge definition (`D147`) | SOURCE-TRACED BEHAVIOUR (disassembly) |
| composition equals VRAM/CRAM/SAT/pixels, fade series equal the U4-A model | MODEL VERIFIED AGAINST THE ORIGINAL CODE |
| frame offsets, 116-update digit cadence in harness frames, press boundaries, sound order, run trace, six-zone identity | EMULATED ORIGINAL FRAME (+/-1) |
| presets (lives, continues, clock, player Y) and button edges | CONTROLLED VARIANT, stated per scenario |

Unresolved (ids in the static JSON `unresolved`):

<!-- BEGIN u4b:unresolved -->
| id | item | state |
|---|---|---|
| U4B-1 | meaning/timbre of requests $87, $94, $A0 (and $B4, $96): numbers and trigger points only; no audio is extracted or substituted | OPEN - AUDIO-0/U5, does not block the screens |
| U4B-2 | cycle-exact cadence on real hardware: the Continue digit, hold and fade waits are `$062D` frame waits, but the harness shows each as n or n-1 frames and the player-update body is CPU-bound; the +/-1 figures are harness measurements | EMULATED, not cycle-proven |
| U4B-3 | a 7-pixel sprite row at screen line 0 (x 1..7) appears in the emulated Game Over and Continue frames: unused SAT entries are parked at Y=$E0 or Y=$F0 ($21DA writes $F0; the player engine rewrites the first entries to $E0), and an 8x16 sprite at Y=$F0 wraps its last row onto line 0 showing leftover player tile data (X 1..7). Whether real hardware / the TV overscan shows it is unverified; TIME OVER shows none | EMULATOR OBSERVATION, hardware unverified; recommend the POC does not draw it |
| U4B-4 | the frozen level frame faded to black before TIME OVER / Continue / Game Over is level specific (death animation, camera, palettes); only the post-fade black screens are reproducible from tables | ADAPTER must keep the last gameplay frame |
| U4B-5 | real-time duration of the death sequence before the screens ($15F2..$164B: animation loop until D51D == 2, 60 + 90 waits, fade passes) depends on the death type (pit fall distance, hurt arc); only the fixed waits are decoded | PARTIAL: waits decoded, animation length per death type measured only for the pit/time-over fixtures |
| U4B-6 | POC input mapping: the original accepts a NEW press edge of either fire button (D147 & $30, one edge per interrupt); a PC adapter must not accept a held button or a key-repeat | DECODED, adapter decision |
| U4B-7 | Continue availability when D2C3 bit 7 is set at the death (a continue was just used): `$13ED` clears bit 7 first, so a just-used flag never blocks a new Continue screen; verified only through the code and the scenarios above, not through an accepted-continue-then-die run | SOURCE-TRACED |
| U4B-8 | the two-digit field always shows tens digit 0 (cell pair fixed in the 2x6 block); a counter above 9 digits does not exist, so no larger layout is decoded | DECODED |
| U4B-9 | the ending TRY AGAIN card ($34D3, sound $98) is a different screen (stream bank $16 $B1E4, 1-byte cells) and is not part of this package | OUT OF SCOPE |
| U4B-10 | `docs/u4-ordinary-results.md` lists `$21DA` as clearing the name table `:= 0`; the operand is `LD DE,$00C0`, so the fill word is $00C0 (tile 192, which `$21DA` also zeroes). Harmless to U4-A (its card refills VRAM tile 256+), but corrected here | NOTE on an accepted document; U4-A text left unchanged |
| U4B-11 | TIME OVER is reached by presetting the clock to 09:59.59 (RAM) and letting the original `$27EE` roll it to 10:00; no real ten-minute act was played. The trigger operands (BCD `$10` minutes, D44B := $C0) are decoded from the code | CONTROLLED VARIANT + BYTE-VERIFIED trigger |
<!-- END u4b:unresolved -->

## 12. Reproduce

```sh
python tools/u4b_screens.py PATH/TO/SonicChaos.sms            # regenerate data/u4b and build/u4b (about five minutes)
python tools/u4b_screens.py PATH/TO/SonicChaos.sms --check    # recompute everything and compare with the committed JSON
python tools/u4b_screens.py PATH/TO/SonicChaos.sms --only static --check   # decoded layer only (seconds)
python tools/u4b_screens.py --validate                        # no ROM
python -m unittest tests.test_u4b_screens                     # part 1 needs no ROM; part 2 uses SONIC_CHAOS_ROM
```

## 13. Promotion recommendation

See the report that accompanies the commit: PROMOTE as research main; the decoded layer, composition and fade/timing data are ready for a POC import (G2-C TIME OVER, G2-D Continue/Game Over) with the unresolved items above carried as adapter notes. No Research blocker remains for the screens; audio stays a separate project.

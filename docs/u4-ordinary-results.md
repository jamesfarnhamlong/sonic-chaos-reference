# U4-A - Original ordinary act-clear results graphics and presentation

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified, never committed).
Base: accepted Research main `db23e5400db923025d2179aba5a01535c6f64b89`, branch `research/u4-ordinary-results`. No POC branch, GameMaker project or Igor was touched.

| | |
|---|---|
| Tool | `tools/u4_results.py` (`ROM`, `ROM --check`, `--only static`, `--validate`, `--doc`) |
| Committed data | `data/u4/ordinary-results-static.json` (decoded ROM facts, draw plan, tilemaps, palettes, fade/title model inputs), `data/u4/ordinary-results-observed.json` (emulated original-code runs and the verification flags), `data/u4/export-manifest.json` (hashes of the exported graphics) |
| Ignored exports | `build/u4/` - indexed PNGs, palettes and ramps (see section 9). Regenerated bit-exactly from the ROM by the tool; their hashes are committed |
| Tests | `tests/test_u4_results.py` (no-ROM part and ROM part) |
| Builds on | `docs/g0-campaign-contract.md` (tail timings, post-tally fade), `docs/object-18-act-clear.md` (sign chain, `$D299`/`$D2C3` correction), `docs/special-stages-progression-audit.md` (stage card selection) |

Evidence classes: **DECODED DATA** and **BYTE-VERIFIED ASSEMBLY** (operands and routine regions read from ROM bytes; every routine has offset, length and SHA-256 in the JSON),
**SOURCE-TRACED BEHAVIOR** (hand disassembly of `$14AE..$1540`, `$1543..$15F1`, `$32F9..$3435`, `$2D08..$2F48`, `$26D6..$27DE`, `$B45A..$B64C` bank 14, `$3175..$32F8`, `$2D90..$2EE5`),
**MODEL VERIFIED AGAINST THE ORIGINAL CODE** (Python re-implementations of the card draw, the fade engine and the act-title animator compared with the emulated VRAM/CRAM of the unmodified ROM in
12 scenarios and 17 act clears), **EMULATED ORIGINAL FRAME** (`tools/g0_rig.py` / `tools/sms_frame_harness.py`: original Z80 code, approximate VDP, NTSC frame timing), **CONTROLLED VARIANT**
(`D2CD` forced at `$32F9`, RAM presets), **UNRESOLVED** (section 11). Numbers `$xx` are hexadecimal. "Frame" = one harness frame; all offsets are relative to the act-clear entry
(`$14AE`, or `$1543` for act index 2) and may move by +/-1 when hooks are attached or when the flag is raised by a RAM fixture instead of the real sign chain.

## 1. Answer in one page

1. **There is no separate "results graphics" asset beyond one compressed tile stream and a handful of tilemaps.** `$32F9` pages ROM bank `$13` into slot 2 and decompresses the **160-tile** stream at
   `13:$949C` (file `0x4D49C`) to VRAM `$2000` (tile indices 256..415), fills the whole 32x24 name table with entry `$0121` (a solid-colour tile, index 13 of the card palette), and draws 1-byte-per-cell
   blocks (tile id, attribute byte = `D2D3` = 1, i.e. tile indices >= 256) and 2-byte-per-cell icons from bank `$13`. Digits are 1x2 glyph cells from a 22-byte table (`13:$A516`).
2. **Palette**: BG slot request `D492/D493` = fade-in from white to palette record 3, sprite slot `D494/D495` = record 4 (`14:$B64D + 16*n`). The card draws **no sprites** (verified: 0 sprite pixels at the tally call and return in every scenario).
   The backdrop colour is sprite-palette entry 0 (`R7 = 0`), which is `$3F` (white) on the card and black on the act title card.
3. **Layout** (cells): banner 32x4 at (0,2); labels 8x11 at (3,8); multiplier panel 5x5 at (21,8); ring field 2 digits at (18,8); bonus field 4 digits at (16,11); score field 6 digits at (13,14) plus a constant `0` at (19,14);
   continue icons 2x2, pitch 2 cells from (14,17), at most 8 (a ninth award icon lands in slot 8); emerald icons 2x2, pitch 4 cells from (8,20), five slots from `D2CC` bits 0..4.
4. **Ordinary vs Special Stage card**: same routine, same positions, same panel, same number/icon/emerald code; only the banner (SONIC/other `HAS PASSED` vs `SPECIAL STAGE`), the second label row (10 cells) and the
   `D2CD = $FF` sound `$86` + 240-frame hold differ (section 5).
5. **Sequence** (section 3): 60 frames of frozen gameplay, fade to white, 96 + 30 + 12 frames of clean-up, card at +198, fade-in, 60 frames, tally, 95 frames of lit card, fade to white, 96 white,
   fade to black, 48 black, `act += 1`, then the **act title card** (new finding, section 8: zone name and act number slide in, 180-frame hold, skippable with button 1/2), loader, fade in from black.
6. **Fades** are produced by one engine in bank 14 (`$B45A`): every 5th interrupt it moves the palette buffer one level per channel; to-white/to-black take 3 passes, from-black/from-white take 4. The model reproduces all
   21 observed CRAM states of an act clear in every one of the 17 acts that have a card (section 4).
7. **Boss act (act index 2)** reuses the same tail through `$1543`; the only presentation differences are the boss-bonus loop in front of the ring loop and the zone (instead of act) increment (section 6).
8. **Not extracted / not claimed**: the sign prize art `$1B..$20`, TIME OVER, Continue, Game Over, ending screens (follow-up questions), and the sound meaning of any request number.

## 2. Routine regions (byte-verified)

<!-- BEGIN u4:routines -->
| routine | CPU range (end exclusive) | file | bytes | SHA-256 | role |
|---|---|---|---|---|---|
| `act_clear_tail` | res $14AE-$1543 | 0x014AE | 149 | `30ad4626a11d` | main-loop branch for D293 bit 5: fades, results, tally, act += 1, reload request |
| `zone_clear_tail` | res $1543-$15F2 | 0x01543 | 175 | `46b9f946a53c` | main-loop branch for D293 bit 4 (act index 2): same tail, zone gate, zone += 1 |
| `results_card` | res $32F9-$33F1 | 0x032F9 | 248 | `c218b2489fc3` | card draw: tile load, fill, banner, labels, panel, continue icons, numbers, fade-in, 60-wait, tally |
| `emerald_icons` | res $33F1-$342A | 0x033F1 | 57 | `d87170ded962` | up to five 2x2 emerald icons from D2CC bits 0..4 |
| `palette_white_fill` | res $342A-$3436 | 0x0342A | 12 | `710976c37089` | fills the palette buffer D472..D491 with $3F |
| `results_tile_loader` | res $79CB-$79DF | 0x079CB | 20 | `789d50786fc1` | bank 19, VRAM $2000, tile stream $949C through the $24C2 decoder |
| `tally_loops` | res $2D08-$2D55 | 0x02D08 | 77 | `98a654fd67b6` | ring loop (10 raw per ring) then bonus-word loop (1 raw per step) |
| `tally_boss_bonus` | res $2D55-$2D84 | 0x02D55 | 47 | `b179e863ac7e` | act index 2 only: N steps of 10 raw (N from the table at $2D84) |
| `tally_boss_table` | res $2D84-$2D90 | 0x02D84 | 12 | `043f523a1b4e` | six 16-bit step counts, one per zone |
| `tally_pacing` | res $2EE6-$2EFB | 0x02EE6 | 21 | `fefd3cf1becc` | step counter D110 and the 255-iteration delay (skipped when a button is held) |
| `tally_award` | res $2EFB-$2F49 | 0x02EFB | 78 | `8259f2307dfd` | score add via $262F, continue icon redraw, sound $B4 every 16th step |
| `score_add` | res $262F-$26D6 | 0x0262F | 167 | `2b27ea7996e7` | BCD score add, continue award rule (D2C8 dependent) |
| `number_draw` | res $26D6-$27DF | 0x026D6 | 265 | `ab69d67f502a` | ring, bonus and score fields: BCD to digits, zero suppression, 1x2 glyph cells |
| `fade_slot_reset` | res $1CAF-$1CBD | 0x01CAF | 14 | `f1ae4c770bb0` | D492/D494 := bit 6 only (fade to black) |
| `palette_upload` | res $1CBD-$1CD3 | 0x01CBD | 22 | `f6dcae7b923d` | D496 != 0: D472 -> CRAM (32 bytes) |
| `animation_freeze` | res $1CEB-$1D06 | 0x01CEB | 27 | `bab91b8f675e` | clears four sprite animation slots, D39B (terrain animation pointer), D131/D132 |
| `sound_regs` | res $18E1-$18ED | 0x018E1 | 12 | `c741d938a54f` | DE09..DE0B := 12,1,2 |
| `object_clear` | res $297E-$2993 | 0x0297E | 21 | `221571d85dc1` | zeroes D300..DBBF, D131/D132 |
| `camera_clear` | res $4FCE-$4FDC | 0x04FCE | 14 | `5df3d51a2927` | zeroes D15E..D28F |
| `name_table_clear` | res $21DA-$220E | 0x021DA | 52 | `4284e62602d1` | frame wait, name table $3800 x $380 words := 0, VRAM $1800 x 32, SAT buffer Y := $F0 |
| `fade_engine` | 0E:$B45A-$B63E | 0x3B45A | 484 | `731304e4d403` | every 5th frame: per-slot palette step (to white, to black, in from black, in from white, copy) |
| `fade_palette_select` | 0E:$B63E-$B64D | 0x3B63E | 15 | `415eecd6642b` | slot +1 -> table address $B64D + 16*index |
| `fade_isr_hook` | res $058A-$0590 | 0x0058A | 6 | `4fdbafd2f810` | frame interrupt: palette upload, input scan |
| `level_reload_branch` | res $1673-$1696 | 0x01673 | 35 | `0c339c5c2b04` | D293 bit 1: $4FCE, $3175 (title card), $2934 loader, $794F fade-in request |
| `act_title_card` | res $3175-$31E2 | 0x03175 | 109 | `ec6baa3f6501` | name-table fills, fade-in request, sound $88, arrows, text, 180-frame hold, fade-out |
| `act_title_arrows` | res $31E2-$3225 | 0x031E2 | 67 | `5cb7c83f7070` | 29 iterations of two 2x3 arrow blocks sliding along rows 1 and 21 |
| `act_title_text` | res $3225-$32CA | 0x03225 | 165 | `6e14a3c37e08` | zone-name object (32x4) then act-number object (12x4) built by the $2D90 name-table animator |
| `act_title_zone_table` | res $32CA-$32D6 | 0x032CA | 12 | `76ef1377e14a` | six pointers (bank 19) to the 32x4 zone-name maps |
| `act_title_delay` | res $32EE-$32F4 | 0x032EE | 6 | `f465bfe2b709` | DEC BC / JR NZ busy delay (CPU time, not frames) |
| `name_table_animator` | res $2D90-$2EE6 | 0x02D90 | 342 | `aeb740392742` | per-update scroller for objects D700.. (modes 0..3) |
| `title_tile_loader` | res $7A12-$7A26 | 0x07A12 | 20 | `95616ace318c` | bank 19, VRAM $2000, tile stream $A7E5 |
<!-- END u4:routines -->

## 3. Timeline of an ordinary act clear

<!-- BEGIN u4:timeline -->
| harness frame | event | what the ROM does |
|---|---|---|
| 0 | clear_entry | `$14AE` entered (D293 bit 5 seen by the main loop) |
| 60 | anim_freeze | `$1CEB`: sprite animation slots, terrain animation pointer, D131/D132 cleared |
| 60 | fade_white_request | D492/D494 := bit6\|bit4 (to white), D2D4 := 4 |
| 156 | sound_regs | `$18E1`: DE09..0B := 12,1,2 |
| 186 | sound_stop | sound request 0 |
| 186 | object_clear | `$297E`/`$4FCE`/`$21DA` clears, `$342A` white buffer |
| 198 | card_start | `$32F9` |
| 215 | card_numbers | last draw call of the card |
| 216 | card_fade_in_request | D492/D494 := bit7\|bit4, records 3 and 4 |
| 274 | tally_call | `$2D55`/`$2D08` |
| 579 | tally_return | tally finished |
| 626 | post_card_wait | back in `$14AE` after the 48-frame wait inside `$32F9` |
| 674 | tail_white_request | D492/D494 := bit6\|bit4 |
| 770 | white_fill | `$342A` white buffer (screen is already white) |
| 770 | black_request | `$1CAF`: D492/D494 := bit6 (to black) |
| 818 | progress | act := act + 1, D293 bit 1 |
| 819 | title_start | `$3175` act title card |
| 831 | title_fills_done | fills, fade-in request (BG record $21), sound $88 |
| 860 | title_arrows_start | `$31E2` arrows |
| 875 | title_text_start | `$3225` zone and act objects |
| 896 | title_hold_start | hold up to 180 frames |
| 1074 | title_hold_end | hold over or button |
| 1104 | title_return | `$31E1` return |
| 1104 | level_loader | `$2934` |
| 1180 | level_fade_in_request | `$794F`: D492/D494 := bit7 (in from black) |
<!-- END u4:timeline -->

Source of the loop lengths (all `LD B,n` immediates in `static.wait_loops`, one `$062D` frame wait per iteration): `$14AE` 60, `$14D0` 96, `$14DB` 30, `$14F4` 12, card `$33DA` 60, `$33E8` 48,
`$14FF` 48, `$1519` 96, `$1527` 48; the act title card 30 + 180 + 30; `$1543..$15CC` repeat the same counts. The harness shows each as n or n-1 frames because `$062D` returns at once when the interrupt tick is
already non-zero. The table above is the **baseline** (real THZ1 goal-sign chain, Sonic, 25 rings, 2 emeralds); the other 11 scenarios and the 17-clear zone matrix reproduce it to +/-1 frame.

What is on screen:

* **+0..+60 - frozen gameplay.** Name table, VDP registers, camera and player position are unchanged (verified, `frozen_frame`); the HUD ring-icon sprite (SAT entries 12 and 13) keeps animating until `$1CEB` clears the
  four sprite-animation slots at +60 (cause inferred, U4-5). Palette-cycling acts keep cycling CRAM entries until the first fade pass. `$1CEB` also clears the terrain-animation pointer `D39B`.
* **+60..+156 - fade to white** of the frozen frame (3 passes, 5 frames apart), then 96-frame wait. `$18E1` at +156 sets `DE09..DE0B := 12,1,2` (music fade parameters), sound request 0 at +186.
* **+186..+198 - blank**: `$297E` (objects), `$4FCE` (camera block), `$21DA` (name table, SAT buffer), `$342A` (palette buffer := `$3F`); screen is white.
* **+198 `$32F9` - card**: `$79CB` loads the tile stream (about 17 frames of DI decompression), fill, banner, labels, panel, continue icons, emerald icons, numbers (all while white), then the fade-in request.
* **+216..+229 - card fade-in** from white (3 visible passes), 60-frame wait, tally at +274.
* **Tally** (section 7). **+579 -> +674**: 95 frames of the finished card.
* **+674..+689 - fade to white**, 96 white, `$342A`, `$1CAF` fade to black (3 passes, black by +784), 48 frames black, `progress` (`D298 += 1`, `D293` bit 1) at +818.
* **+819..+1104 - act title card** (section 8), then the loader (`$2934`, black, 76 frames in the baseline) and the level palette fade-in from black (`$794F`, 4 passes; in the baseline the first colours appear 8 frames after the request).

CRAM changes of the baseline (the 21 states; BG half shown):

<!-- BEGIN u4:cram -->
| harness frame | CRAM bytes 0..3 |
|---|---|
| 63 | 3d2d1d19... |
| 68 | 3e3e2e2e... |
| 73 | 3f3f3f3f... |
| 219 | 3a2f2a2b... |
| 224 | 351f291b... |
| 229 | 300f281b... |
| 679 | 351f3d2f... |
| 684 | 3a2f3e3f... |
| 689 | 3f3f3f3f... |
| 774 | 2a2a2a2a... |
| 779 | 15151515... |
| 784 | 00000000... |
| 839 | 10000000... |
| 844 | 24000000... |
| 849 | 38100000... |
| 1079 | 24000000... |
| 1084 | 10000000... |
| 1089 | 00000000... |
| 1188 | 10040000... |
| 1193 | 24080400... |
| 1198 | 381c0804... |
<!-- END u4:cram -->

## 4. Fade engine (`14:$B45A..$B63D`, called from the frame interrupt at `$059F`)

Slots: `D492` (BG, buffer `D472..D481`) and `D494` (sprite, buffer `D482..D491`); slot byte +0 = mode/step, +1 = palette record index. Gate: `D2D4` = 4 (written at boot `$04BB/$04C6` and by both clear tails `$14B9/$154E`),
`D2D5` is incremented per call and the engine runs when it reaches 5, so **one pass per 5 interrupts** (the phase can shift by one frame after a long DI section, e.g. the tile decompression).
The pass writes the buffer and sets `D496`; `$1CBD` (interrupt) copies `D472` to CRAM on the next frame. The engine works on the **buffer**; palette-cycling code writes CRAM directly, so cycled entries are not part of the ramp
(`checks.palette_cycled_entries_masked` lists them per scenario: zone 3 entries 4, 11; zone 5 entries 14, 15).

| slot byte | name | per pass (per 2-bit channel) | passes |
|---|---|---|---|
| bit6 + bit4 | to white | +1 up to 3 | 3 |
| bit6 | to black | -1 down to 0 | 3 |
| bit7 | in from black | `max(0, p - (3 - target))`, `p` = pass counter 0..3 (pass 0 = black) | 4 |
| bit7 + bit4 | in from white | -1 towards target while different | 4 |
| bit5 | copy | buffer := record, slot cleared | 1 |

The slot clears itself after the last pass. Requests in this path: `$14BE`/`$1553` (to white), `$33AB` (in from white, records 3 and 4), `$1507`/`$15A6` (to white), `$1521 $342A` then `$1524`/`$15C3 -> $1CAF` (to black),
`$31A9` (act title card BG, in from black, record `$21`), `$31D3 -> $1CAF` (to black), `$794F` (level, in from black, records from the table at `$7F3C`, index `3*zone+act`).
Exported ramps (RGB, both palettes): `build/u4/palettes.json`.

Palette records used by the card and the title card (16 SMS colours each, `%00BBGGRR`):

<!-- BEGIN u4:palettes -->
| record | file | 16 SMS colours %00BBGGRR |
|---|---|---|
| 3 ($03) | 0x3B67D | 30 0F 28 1B 06 3A 00 00 33 22 00 2A 00 3F 35 20 |
| 4 ($04) | 0x3B68D | 3F 20 35 1B 06 3A 00 3F 07 01 15 2A 1F 0C 08 04 |
| 5 ($05) | 0x3B69D | 3F 3F 3F 3F 3F 3F 3F 3F 3F 3F 3F 3F 3F 3F 3F 3F |
| 33 ($21) | 0x3B85D | 38 10 00 00 00 00 00 00 00 00 30 03 3F 0F 03 00 |
<!-- END u4:palettes -->

## 5. The results card

Draw plan of `$32F9` (every operand read from the code bytes; sources in bank `$13`, destination = name-table cell):

<!-- BEGIN u4:blocks -->
| element | condition | routine | ROM source | cell (col,row) | size | content |
|---|---|---|---|---|---|---|
| `screen_fill` | always | `$1D8A` | - | (0,0) | 32x24 | entry `$0121` |
| `banner_sonic` | D2CD == 0 and D2C8 == 1 | $2383 | 13:$A58C (0x4E58C) | (0,2) | 32x4 | tile ids 289..375 |
| `banner_other` | D2CD == 0 and D2C8 != 1 | $2383 | 13:$A60C (0x4E60C) | (0,2) | 32x4 | tile ids 289..411 |
| `labels_ordinary` | D2CD == 0 | $2383 | 13:$A68C (0x4E68C) | (3,8) | 8x11 | tile ids 289..398 |
| `panel_ordinary` | D2CD == 0 | $2383 | 13:$A6EC (0x4E6EC) | (21,8) | 5x5 | tile ids 257..385 |
| `banner_stage` | D2CD != 0 | $2383 | 13:$A705 (0x4E705) | (0,2) | 32x4 | tile ids 289..413 |
| `labels_stage` | D2CD != 0 | $2383 | 13:$A785 (0x4E785) | (3,8) | 8x11 | tile ids 289..415 |
| `panel_stage` | D2CD != 0 | $2383 | 13:$A6EC (0x4E6EC) | (21,8) | 5x5 | tile ids 257..385 |
| `continue_icon_other` | D2C8 != 1 | `$2383` | 19:$A530 | (14,17)+2n | 2x2 each, n < 8 | tile ids 280,281,282,283 |
| `continue_icon_sonic` | D2C8 == 1 | `$2383` | 19:$A52C | (14,17)+2n | 2x2 each, n < 8 | tile ids 276,277,278,279 |
| `emerald_0` | D2CC bit 0 | `$2349` | 19:$A55C | (8,20) | 2x2 | entries 933,934,93D,93E |
| `emerald_1` | D2CC bit 1 | `$2349` | 19:$A564 | (12,20) | 2x2 | entries 935,936,93F,940 |
| `emerald_2` | D2CC bit 2 | `$2349` | 19:$A56C | (16,20) | 2x2 | entries 937,938,941,942 |
| `emerald_3` | D2CC bit 3 | `$2349` | 19:$A574 | (20,20) | 2x2 | entries 939,93A,943,944 |
| `emerald_4` | D2CC bit 4 | `$2349` | 19:$A57C | (24,20) | 2x2 | entries 18F,190,191,192 |
<!-- END u4:blocks -->

Number fields (BCD to digits in `$2726`/`$27AD`; each digit is a 1x2 glyph cell: top tile at (col,row), bottom tile at (col,row+1), next digit one column right):

<!-- BEGIN u4:numbers -->
| field | source | BCD bytes | digit cells | blank leading zeros | first cell (col,row) | routine |
|---|---|---|---|---|---|---|
| `rings` | `$D29A` | 1 | 2 | 1 | (18,8) | $26D6 |
| `bonus` | `$D2A6` | 2 | 4 | 3 | (16,11) | $26E7 |
| `score` | `$D29D` | 3 | 6 | 5 | (13,14) | $26F8 |
| score trailing `0` | constant | - | 1 | - | (19,14) | `$2383` |
<!-- END u4:numbers -->

Rules recovered from `$2726..$27DE`:

* digits are drawn most significant first from the BCD bytes (`D29A` 1 byte, `D2A6` 2 bytes, `D29D..D29F` 3 bytes, low byte first); a nibble above 9 aborts the draw (nothing is written);
* the first `leading_zero_blank` zero digits are drawn with the blank glyph (index 10); a non-zero digit ends the suppression, so `0 rings` reads ` 0`, bonus `7` reads `   7`;
* the score field is skipped entirely while `D29D | D29E | D29F == 0`; the constant `0` cell at (19,14) is always drawn, so the card reads **six BCD digits and a fixed 0** (display factor x10, resolving the HUD-card half of G0 U1);
* the static text is graphics only: `RING`, `SPEED` (ordinary) or `TIME` (stage card), `SCORE`, `CONTINUE`, `x 100`, `x 10` are tiles of the same stream. Bonus word `$0914` shows `914 x 10`, rings `25` show `25 x 100`.

Digit glyph table (`13:$A516`, two bytes per glyph; the ids are the low bytes of name-table entries `$01xx` because `D2D3 = 1`, i.e. tile index 256 + id):

<!-- BEGIN u4:glyphs -->
| digit | top tile id (low byte) | bottom tile id (low byte) |
|---|---|---|
| 0 | 1 | 2 |
| 1 | 3 | 4 |
| 2 | 5 | 6 |
| 3 | 7 | 8 |
| 4 | 9 | 10 |
| 5 | 11 | 12 |
| 6 | 13 | 14 |
| 7 | 15 | 16 |
| 8 | 17 | 18 |
| 9 | 17 | 19 |
| blank | 33 | 33 |
<!-- END u4:glyphs -->

**Ordinary vs Special Stage card** (`D2CD == 0` vs `!= 0` at `$330B`): geometry of banner, labels and panel is identical; the panel block is the same ROM bytes (`$A6EC`); the labels differ in 10 cells (rows 3-4, columns 3-7:
`SPEED` -> `TIME`); the banner differs in 93 cells (Sonic) / 100 cells (other character) of 128. `D2CD = $FF` (success) additionally writes sound request `$86` and holds 240 frames before the common 60-frame wait; `$33D7`
clears `D2CD`. The stage card keeps the identical continue-icon, emerald-icon and number code, so the accepted Special Stage results card can be rebuilt from the same exports (`blocks/banner_stage.png`, `blocks/labels_stage.png`).

Character dependence: `D2C8 == 1` (Sonic) selects `banner_sonic` and `continue_icon_sonic`; any other value (Tails = 2) selects `banner_other` / `continue_icon_other`. The Sonic award rule (every 5,000 raw score units) and the other
character's rule run inside the tally (`$262F`); each award that changes `D2C3` redraws one icon at slot `min(old count & $7F, 8)` (`$2F17..$2F39`), so a ninth continue draws into slot 8 (columns 30-31) - verified in
`sonic_continue_overflow`.

## 6. Boss act (act index 2) versus ordinary act

| | ordinary (`$14AE`) | act index 2 (`$1543`) |
|---|---|---|
| entry | main loop, `D293` bit 5 | main loop, `D293` bit 4 |
| frames, fades, clear calls | as section 3 | identical (`$1CEB` is run a second time at `$157D`, no visible effect) |
| gate | none | `$1594`: zone >= 5 skips the card (ending selector) |
| card | `$32F9` | `$159B CALL $32F9` - **same routine, same banner and labels** (no act or zone number is printed) |
| tally | ring loop, then bonus loop | `$2D55` first: N steps of BCD 10 raw (`$27EB`), N = 50, 100, 150, 200, 250, 600 by zone (`$2D84`; the 600 entry is unreachable), only the SCORE field is redrawn, then a 12-frame wait; then the same ring and bonus loops |
| progress | `$1534`: `act += 1` | `$15CE..$15D6`: `act := 0`, `zone += 1` |
| after | act title card of (zone, act+1) | act title card of (zone+1, 0) |

Boss-bonus cadence (`boss_zone0_act2`, `boss_zone3_act2`, step hooks): 3.57 and 3.64 steps per harness frame (50 and 200 steps). How the boss object sets `D2A6` per zone is G0 U2 and was not traced here.

Zone matrix (flag raised 60 frames after the act is in play for 16 of the 17 clears; THZ1 uses the real sign chain). Zone 5 act 2 never draws a card.

<!-- BEGIN u4:zone_matrix -->
| zone | act | tail | card start | tally call | tally return | progress | title hold |
|---|---|---|---|---|---|---|---|
| 0 | 0 | act | 198 | 274 | 579 | 818 | 896 |
| 0 | 1 | act | 198 | 274 | 282 | 520 | 598 |
| 0 | 2 | zone | 198 | 274 | 306 | 544 | 622 |
| 1 | 0 | act | 198 | 274 | 282 | 520 | 598 |
| 1 | 1 | act | 199 | 275 | 283 | 521 | 599 |
| 1 | 2 | zone | 198 | 274 | 319 | 557 | 635 |
| 2 | 0 | act | 199 | 275 | 283 | 521 | 599 |
| 2 | 1 | act | 199 | 275 | 283 | 521 | 599 |
| 2 | 2 | zone | 198 | 274 | 333 | 571 | 649 |
| 3 | 0 | act | 199 | 275 | 283 | 521 | 599 |
| 3 | 1 | act | 199 | 275 | 283 | 521 | 599 |
| 3 | 2 | zone | 199 | 275 | 347 | 585 | 663 |
| 4 | 0 | act | 199 | 275 | 283 | 521 | 599 |
| 4 | 1 | act | 199 | 275 | 283 | 521 | 599 |
| 4 | 2 | zone | 198 | 274 | 359 | 597 | 675 |
| 5 | 0 | act | 198 | 274 | 282 | 520 | 598 |
| 5 | 1 | act | 198 | 274 | 282 | 520 | 598 |
| 5 | 2 | none | - | - | - | - | - |
<!-- END u4:zone_matrix -->

All 17 clears reproduce the same card layout (same compose, same palette records, same fade model, same title-card model); only THZ1 differs in the card hash because the real `$19` child set a bonus word.

## 7. Tally and award behaviour

`$2D08`: while `D29A != 0`: `D29A -= 1` (BCD), score += `$27E5` (BCD `10 00 00` raw), `$26D6` redraws rings, `$26F8` redraws the score, `$2EE6` pacing. Then while `D2A6 != 0`: the word counts down by 1 (BCD, borrow
into the high byte), score += `$27E2` (BCD `01 00 00`), `$26E7`, `$26F8`, pacing. Because the card shows score x10, one ring is worth 100 on the card and one bonus step 10.
`$2EE6`: `D110 += 1`; if `D137 == 0` (no button held) a 255-iteration `PUSH AF / POP AF / DJNZ` delay (about 8.7k T-states) follows. `$2F08` plays sound request `$B4` whenever `D110 & 15 == 0` before the step.

Harness cadence (NTSC timing, CPU bound): 3.07 bonus steps per frame (914 steps in 298 frames), ring loop 25 steps in 9 frames; with button 1 held 6.01 steps per frame (914 steps in 152 frames). That is about 19.5k and 9.9k T-states per
step; the adapter should derive its own rate from the target frame rate (`adapter.tally_rate`). Sound `$B4` is requested every 16th step (about every 5 frames at 3 steps per frame).

## 8. Act title card (newly found; shown at every act load)

G0 listed act title cards as not found (PRES-04). They exist: between the post-tally black and gameplay `$1673 -> $3175` shows the zone name and act number on a red/yellow/blue background. It is part of the visible
return to gameplay, so it is recovered here at the same standard as the results card (tile stream, tilemaps, palette, exact name-table state after every animator update, timing); its sound and fade facts are in the tables.

<!-- BEGIN u4:title -->
| element | position | size | behaviour |
|---|---|---|---|
| fill | `$3800` | 128 words | entry `$0101` |
| fill | `$3900` | 512 words | entry `$0108` |
| fill | `$3D00` | 128 words | entry `$0141` |
| arrow_left | (29,1) | 3x2 | 29 iterations, -1 col each; 19:$B193 |
| arrow_right | (1,21) | 3x2 | 29 iterations, +1 col each; 19:$B199 |
| zone name | (0,7) | 32x4 | mode 0, 32 updates; maps $B19F $B21F $B29F $B31F $B39F $B41F |
| act number | (31,12) start | 12x4 | mode 1, 21 updates; maps $B49F $B4CF $B4FF |
<!-- END u4:title -->

Sequence (`$3175..$32C9`): clear name table and sprite buffer (`$21DA`), load the 95-tile stream `13:$A7E5` to VRAM `$2000` (`$7A12`), fill rows 0-3 with `$0101`, rows 4-19 with `$0108`, rows 20-23 with `$0141`, request BG
fade-in from black to record `$21` (the sprite palette stays black), sound `$88`, 30 frames, `D2D3 := 1`, 29 arrow iterations (a busy delay of `BC=$0400` each; the left block moves one column left from column 29, the right block one
column right from column 1, redrawn each iteration), zone-name object (type `$10`, mode 0, 32 updates: update n draws columns `2*((32-n)>>1) .. +n-1` of the 32x4 map at columns 0..n-1 of rows 7-10), act-number
object (type `$11`, mode 1, 21 updates: a 12x4 block whose destination starts at column 31 of row 12 and moves one column left per update, width `min(n,12)`), 180-frame hold ended early when button 1 or 2 is held (`D137 & $B0`, checked
once per frame), fade to black (`$1CAF`), `$18E1`, 30 frames.
The `$2383` row-wrap bookkeeping (HL advances one byte per cell while the VDP advances two) puts the second cell of the act-number block at column 0 of the **next** row during the first updates; column 0 is hidden by the VDP left-column
mask (`R0` bit 5), and the model reproduces it bit for bit (all 83 name-table states of every title card are compared with the emulated VRAM).

Zone names are the six 32x4 maps (`title/zone_name_0..5.png`), act numbers the three 12x4 maps (`title/act_number_0..2.png`); final frames for all 18 (zone, act) pairs are `title/frame_zoneZ_actA.png`.
The title card of zone 5 act 2 is shown after zone 5 act 1; the clear of zone 5 act 2 itself goes to the ending selector (U4-10).

## 9. Exports (`build/u4/`, ignored; hashes in `data/u4/export-manifest.json`)

All PNGs are 8-bit indexed with the 32-entry CRAM of the card (palette index 0..15 = BG record, 16..31 = sprite record; the act title card uses record `$21` for 0..15). The manifest hash is the SHA-256 of the row-major
index bytes, not of the PNG file, so it does not depend on the PNG encoder.

| file | content |
|---|---|
| `card_tiles_vram2000.png` | the 160 decompressed tiles, 16 per row (tile index = 256 + position) |
| `blocks/banner_sonic.png`, `banner_other.png`, `banner_stage.png` | 256x32 banners |
| `blocks/labels_ordinary.png`, `labels_stage.png`, `panel_ordinary.png`, `panel_stage.png` | 64x88 labels, 40x40 panel |
| `blocks/continue_icon_sonic.png`, `continue_icon_other.png`, `emerald_icon_0..4.png` | 16x16 icons (emerald icons use sprite-palette indices) |
| `blocks/digit_glyphs.png` | 11 glyphs 8x16 (0..9, blank) |
| `blocks/screen_fill_tile.png` | the `$0121` fill tile |
| `frames/*.png` | composed 256x192 reference frames (static layers and an example with numbers) |
| `title/*.png` | title tile sheet, 6 zone-name maps, 3 act-number maps, 2 arrows, 18 final frames |
| `palettes.json` | card palettes (SMS and RGB) and the exact fade ramps for the card and from white / to black |

Regenerate: `python tools/u4_results.py "<ROM>"` (static + exports in seconds with `--only static`; observations about 2.5 minutes). Python >= 3.10, `Pillow`, and for the observations the `z80` package (kosarev/z80).
Policy note for the Manager: tile pixels and composed frames are ROM-derived graphics, so they stay in the ignored `build/` and only hashes, name-table entries, palettes (16 colour values per record, the same
kind of numeric table as earlier caches) and decoded layout are committed.

## 10. ROM-native values, original palette/index information, GameMaker adapter

**ROM-native coordinates and timing** - everything in sections 2-8: 256x192 pixels, 32x24 cells of 8x8, frame counts above, the 5-frame fade grid, `R0 = $26` (left 8-pixel column shows the backdrop), `R8 = R9 = 0`
(no scroll on either card). **Original palette/index information** - indexed exports use the original 4-bit pixel indices and palette-select bit 11 of the entry exactly as stored; colours are the 2-bit SMS values (RGB expansion
`x85` is the accepted harness convention, not a ROM value).

**GameMaker presentation adapters for 348x196** (proposal, `static.adapter`, not ROM data):

* place the 256x192 image at offset (46, 2) of the 348x196 logical frame; fill the side/top/bottom bars with the ROM backdrop colour of the same frame (white on the card, black on the title card) and run them through the
  same palette ramp, because the backdrop is a CRAM entry and fades with the card;
* keep the left 8-pixel mask column (it is the backdrop colour; invisible on the white card, a black strip on the title card);
* fade-to-white of the last gameplay frame needs a copy of that frame (U4-4); the ROM has no table for it;
* tally rate and busy-delay lengths are CPU-bound: choose them from the target frame rate (about 3 steps per 60 Hz frame, 6 with a button held, as measured);
* sound requests are numbers only (`$B4`, `$86`, `$88`, 0, music table `$18BA`), meanings stay with AUDIO-0 / U5.

## 11. Unresolved and out of scope (no replacements invented)

<!-- BEGIN u4:unresolved -->
| id | item | state |
|---|---|---|
| U4-1 | meaning of the sound request numbers in this path ($B4 tally tick, $86 stage card, $88 title card, 0 stop, level-music table at $18BA) | numbers only (see U5 / AUDIO-0) |
| U4-2 | cycle-exact rates of CPU-bound waits (tally steps, title busy loops $32EE) on a real console; harness gives NTSC-frame figures only | EMULATED, not cycle-proven |
| U4-3 | sub-frame placement of each act-title animator update and arrow iteration (the name-table states and their order are exact; the frame each state is first visible is harness-measured) | MEASURED |
| U4-4 | the frozen gameplay frame that is faded to white before the card is level/act specific (VRAM, SAT, CRAM at the clear entry); it cannot be reproduced from ROM tables alone | ADAPTER must capture the last gameplay frame |
| U4-5 | what drives the sprite change in [0,60) after the clear entry (HUD ring icon, SAT entries 12 and 13); inferred ISR animation slot D452..D46A, cleared by $1CEB | INFERRED |
| U4-6 | D2CC bit 5 (sixth emerald bit) is never drawn on this card; only bits 0..4 have icons | DECODED (by design of $33F1); semantics belong to the ending research |
| U4-7 | label wording is graphics only (read from tiles: RING, SPEED, SCORE, CONTINUE, 'x 100', 'x 10'); there is no text string in the ROM for it | DECODED GRAPHICS |
| U4-8 | D2D3 (attribute byte of every 1-byte-per-cell draw) is 1 in every observed card and title; its only zero writer is $34EA (ending TRY AGAIN screen); the ending -> title -> new game -> clear path was not run here | OBSERVED, one path unexercised |
| U4-9 | act-title animator modes 2 and 3 and the $2E80 type-$11 variant are not reached by the title card (not decoded beyond their bytes) | NOT NEEDED |
| U4-10 | zone 5 act index 2 skips the card (ending selector); the ending screens are outside this task | G0 / EEZ-ending research |
| U4-11 | how the level palette cycling entries interact with the fade passes beyond the entries listed per act (animated entries are masked in the fade comparison) | MASKED, listed per scenario |
<!-- END u4:unresolved -->

Out of scope by instruction: TIME OVER, Continue, Game Over, ending screens, sign-prize art selectors `$1B..$20`.

## 12. G1-C dependencies after U4-A

1. Card: import `blocks/*`, the glyph strip and the draw plan; compose exactly as `compose_name_table` (the tool verifies it against emulated VRAM).
2. Fades: implement the engine of section 4 (or import `palettes.json` ramps) on a 5-frame grid; fades act on the whole frame including the backdrop.
3. Capture the last gameplay frame at the clear entry for the pre-card fade (U4-4); freeze HUD ring animation at +60.
4. Tally: rate (adapter), award rule with icon redraw, button skip, boss-bonus loop for act index 2, sound requests as numbers.
5. Act title card: import `title/*`, run the verified animator (`title_states`), 180-frame hold with the button skip, then the level fade-in from black; the 76-frame loader gap is black.
6. Zone 5 act 2 (ending) and the post-ending `D2D3` question (U4-8) stay with the ending work.
7. Sign-prize art selectors and TIME OVER / Continue / Game Over remain separate follow-up questions.

## 13. Tests

`tests/test_u4_results.py`: part 1 (no ROM) re-runs the compose, fade and title models on the committed plan with negative controls, checks the committed timelines and the generated tables of this document; part 2 (ROM)
recomputes the static census and the export hashes and replays four clears (baseline with per-step hooks, Tails, ninth-continue overflow, boss act) against the committed observations.
`python tools/u4_results.py ROM --check` recomputes everything (12 scenarios and the 17-clear zone matrix). Reference run: see the Research report.

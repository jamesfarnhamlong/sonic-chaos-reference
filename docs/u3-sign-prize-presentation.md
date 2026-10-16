# U3-A: goal-sign prize graphics, reward-table parity and retry behaviour

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified by the tool, never committed).
Base: Research `main` `87ae62b76de35e41c9bb837c1125a54210f2f85c`. POC G1-C `535d5768131b6d943048e316912c65ece4be32b1` was read, not touched.
Tool: `tools/u3_sign_prizes.py` (`ROM`, `--check`, `--validate`, `--doc`). Tests: `tests/test_u3_sign_prizes.py`.
Data: `data/u3/sign-prize-static.json`, `sign-prize-controlled.json`, `sign-prize-observed.json`, `export-manifest.json`. Pixel exports: ignored `build/u3/` only.
Builds on `docs/object-18-act-clear.md` (G0-R corrected preface), `docs/g0-campaign-contract.md`, `docs/u4-ordinary-results.md`, `docs/mapped-object-screen-registration.md`.

Evidence classes, strongest first: **DECODED DATA** (numbers read from ROM bytes) / **BYTE-VERIFIED ASSEMBLY** (instruction fragments compared with constants in the tool, region hashes) /
**SOURCE-TRACED** (disassembly read by hand) / **CONTROLLED** (the original Z80 routines executed on `z80` with explicit RAM, compared cell by cell with a pure model) /
**EMULATED** (the unmodified ROM in the approximate SMS harness; harness frames are not ROM updates, so all timing below is counted in **sign-object updates**) /
**ADAPTER** (GameMaker proposal) / **UNRESOLVED**. Numbers written `$xx` are hexadecimal; ring counts, lives and continues are BCD in the ROM.

## 1. Answer

| Question | Result | Evidence |
|---|---|---|
| Where is the face art? | Six 16-tile blocks (512 bytes each) in bank `$0D` file `0x354BC + n*0x200`; selectors `$1B,$1C,$1D,$1E,$1F,$20` each load one block into VRAM tiles `$6A..$79`. `$12` (the sign's wake selector) loads the `$1C` block plus 48 fixed tiles `$7A..$A9` from bank `$09`. **`$1C` is byte-identical to the default face and is never selected.** | DECODED + BYTE-VERIFIED + EMULATED (VRAM equals the expected block in all 98 captures) |
| What do they show? | `$12`/`$1C` Dr. Robotnik (default), `$1B` Sonic, `$1D` Tails, `$1E` gold ring, `$1F` blue bird, `$20` blank grey panel with the post running through it. Exact palette indices are in the ignored exports; hashes in the manifest. | DECODED + EMULATED |
| Which face for which reward? | class 1 **life**: Sonic `$1B`, Tails `$1D` (own face). class 3 **continue**: Sonic `$1D`, Tails `$1B` (**the other character's face**). class 2 **+10 rings**: `$1E` for both. no prize (class `$FF`, re-roll classes 4..8): `$1F`. class 0 **retry**: `$20`. | BYTE-VERIFIED + CONTROLLED (100 counts x both tables x both players) + EMULATED (Sonic and Tails) |
| Is the face animated? | No. One 16-tile block is swapped in four consecutive updates (a 4-quadrant wipe, section 3). The face is visible only in sign frame 1; spin frames 2..5 never show it. | SOURCE-TRACED + EMULATED |
| Two prize tables | `($D297 + 1)` odd -> `$A919` (zones 0, 2, 4 = THZ, SEZ, AQZ); even -> `$A962` (zones 1, 3, 5 = GPZ, MGHZ, EEZ). Act and character are irrelevant. Both are fully decoded; the 100-count class vectors are in the JSON. 45 of 100 counts are a reward or retry in at least one table and 44 of them get a different class in the other. | DECODED + CONTROLLED + EMULATED (all six zones, both acts) |
| Reward arithmetic | life: `D299 + 1` (BCD), unchanged at `$99`, sound `$A9` **even at the cap**. continue: `D2C3 := ((D2C3 + 1) DAA) & $7F` - wraps 79 -> 00, clears bit 7, no sound. rings: `D29A + $10` (DAA, carry dropped: 90 -> 00), no sound. | CONTROLLED + EMULATED |
| Retry | class 0 (THZ-parity counts 16 28 32 44 58; GPZ-parity 18 36 45 81 89): blank panel, state 3, `+$35 := $FF`, no reward, no child, no timeout, player free, timer stays stopped. The next contact is a 64-update spin and a **re-roll `(D12F & 7) + 1`** = classes 1..8: 3/8 reward (life, rings, continue), 5/8 nothing. **A re-roll can never be class 0, so a retry cannot repeat; the second landing is final.** | CONTROLLED (all 256 `D12F` bytes) + EMULATED (all eight classes seen) |
| Equal-digit life | child state 3 (+278 updates after contact): `D2A6` zero -> `$0777`; if all three digits are equal -> `CALL $03F2` (the same life routine). It is independent of the class reward: a class-1 sign **plus** an equal-digit word gives **+2 lives**. | CONTROLLED + EMULATED |
| Ring prize and bonus | the class-2 ring prize is applied at landing, **before** the child reads `D29A`: the bonus word and the tally both use the new count. | CONTROLLED + EMULATED (`$0708`, not `$0798`) |

## 2. Dynamic graphics loader and selectors

**BYTE-VERIFIED ASSEMBLY (`$7AC2..$7BA6`) + DECODED DATA.** RAM: `D3B3` selector (0 = idle), `D3B4` current entry bank byte, `D3B5` tiles left, `D3B6` source pointer, `D3B8` VRAM destination,
`D3BA` next list entry. A selector `>= $10` indexes the pointer table at `$7BA6` (`selector - $10`, two bytes); each list entry is six bytes `[bank | remap<<7, tiles, vram_lo, vram_hi, src_lo, src_hi]`
and `$FF` ends the list, whereupon `$7B92` clears `D3B3..D3B8`. The loader copies **at most four 32-byte tiles per call** and is called once per level frame update, **right after the object pass** (`$16B8`: `CALL $5DD1`, then `CALL $7AC2` at `$16D3`; the paused-object branch calls it at `$1723`), so a selector written by the sign is already being loaded in the same update; the first call also fetches
the entry, so a 16-tile entry costs **four consecutive updates starting in the update that wrote `D3B3`** (observed: face hash changes at landing, +1, +2, +3 in every one of 43 clears).
None of the sign selectors uses the remap bit.

<!-- BEGIN u3:selectors -->
| selector | list | entries (bank:source, tiles) | face block file | tile-byte SHA-256 | 32x32 index SHA-256 | face |
|---|---|---|---|---|---|---|
| $12 | `$7BCB` | 0D:$96BC x16 to tile $6A + 09:$8640 x48 to tile $7A | 0x356BC | `b168f0ebdfe2` | `554246d1505a` | Dr. Robotnik |
| $1B | `$7C47` | 0D:$94BC x16 to tile $6A | 0x354BC | `d5c3c3b6a2c9` | `6a1deb11b103` | Sonic |
| $1C | `$7C4E` | 0D:$96BC x16 to tile $6A | 0x356BC | `b168f0ebdfe2` | `554246d1505a` | Dr. Robotnik |
| $1D | `$7C55` | 0D:$98BC x16 to tile $6A | 0x358BC | `3f1c9ae61037` | `4f3a5cbeecac` | Tails |
| $1E | `$7C5C` | 0D:$9ABC x16 to tile $6A | 0x35ABC | `04bbe24e2e08` | `4effc5a92a98` | gold ring |
| $1F | `$7C63` | 0D:$9CBC x16 to tile $6A | 0x35CBC | `192aa683f01a` | `2258c1b9a695` | blue bird |
| $20 | `$7C6A` | 0D:$9EBC x16 to tile $6A | 0x35EBC | `5742789b5166` | `eea2ef0d619f` | blank panel (index 10 fill) |
<!-- END u3:selectors -->

* Source blocks `$94BC, $96BC, $98BC, $9ABC, $9CBC, $9EBC` (bank `$0D`) are exactly `$200` bytes apart; file `0x354BC..0x35EBC`. The first block of `$12` is `$96BC` = `$1C`.
* No routine in `$A867..$ABA0` or `$AA87..` writes `$1C`; the controlled scans (400 first-pass rows, 512 re-roll rows) never produce it.
* Persistence: nothing but the next `D3B3` write replaces the face. `$A87D` (state 2, once per sign object) writes `$12`; every landing writes one of `$1B,$1D,$1E,$1F,$20`.

### Sign mapping (bank `$0F`, type `$18`, pointer `$3C030 -> $8EAE`)

<!-- BEGIN u3:mapping -->
| frame | record | pieces | tile ids (8x16 each) | selector-dependent |
|---|---|---|---|---|
| 0 | `$A0E4` | 0 | - | no |
| 1 | `$8EBA` | 10 | $6A $6C $6E $70 $72 $74 $76 $78 $7A $7C | yes |
| 2 | `$8EC5` | 6 | $7E $80 $82 $84 $86 $88 | no |
| 3 | `$8ED0` | 6 | $8A $8C $8E $90 $7A $7C | no |
| 4 | `$8EDB` | 6 | $92 $94 $96 $98 $86 $88 | no |
| 5 | `$8EE6` | 10 | $9A $9C $9E $A0 $A2 $A4 $A6 $A8 $7A $7C | no |
<!-- END u3:mapping -->

Frame 1 pieces 0..7 (tiles `$6A,$6C,...,$78`) are the **32 x 32 face** at x -16..+15, y -48..-17 relative to the sign anchor; pieces 8, 9 are the post. The face is exactly what the selectors replace;
frames 2..4 (side views) and 5 (back, tiles `$9A..$A9`) use fixed tiles. Sprites are 8x16 (VDP R1 = `$E2`); a piece draws tile `n` (top half) over tile `n+1` (bottom half).
Upload order (loader tile order): batch 1 = tiles `$6A..$6D` (pieces 0, 1: top row, left half); batch 2 = `$6E..$71` (pieces 2, 3: top row, right half); batch 3 = `$72..$75` (pieces 4, 5: bottom row, left); batch 4 = `$76..$79` (pieces 6, 7: bottom row, right).

### Palettes (DECODED DATA)

The sign is a sprite and uses the level's **sprite palette** (CRAM 16..31). `$794F` reads `$7F3C + (zone*3 + act)*2`; byte 1 = sprite record at `$3B64D + 16*index`. Act independent. Colour 0 is the transparent index.
The observed CRAM sprite half equals the ROM record in every capture of every zone.

<!-- BEGIN u3:palettes -->
| zone | sprite record | 16 SMS colours %00BBGGRR |
|---|---|---|
| 0 | $06 | 38 20 35 1B 06 3A 00 3F 07 01 15 2A 1F 0C 08 04 |
| 1 | $07 | 00 20 35 1B 06 3A 00 3F 07 01 15 2A 1F 0C 08 04 |
| 2 | $08 | 30 20 35 1B 06 3A 00 3F 07 01 15 2A 1F 37 22 00 |
| 3 | $09 | 19 20 35 1B 06 3A 00 3F 07 01 15 2A 1F 0C 08 04 |
| 4 | $0A | 10 20 35 1B 06 3A 00 3F 07 01 15 2A 1F 2A 15 1D |
| 5 | $0B | 00 20 35 1B 06 3A 00 3F 07 01 15 2A 1F 0C 08 04 |
<!-- END u3:palettes -->

Zones 1 and 5 use different records with identical colours; the six faces differ per zone only through colour 0 and, in SEZ/AQZ, colours 13..15. Pixel indices are zone independent.

### Compositing and foreground priority (EMULATED)

* SAT registration of the face is the ordinary mapped-object rule (`docs/mapped-object-screen-registration.md`): `SAT_X = anchor_x - camera_x - 16`, drawn one line below `SAT_Y`. In every stationary capture
  the face origin is exactly `(anchor - camera) + (-16, -47)` (mapping `-48` plus the VDP's one-line offset). THZ1 at the pan stop: camera `(3831, 405)`, anchor `(3960, 558)`, face origin on screen `(113, 106)`.
* A sprite pixel is hidden wherever a **foreground-priority background tile** overlaps it. In 98 captures over 43 clears this happens only in **SEZ Act 1** (zone 2, act index 0): 6 of 942 face pixels at the bottom-right corner (face-relative x 28..31, y 27..31)
  after landing, 2 before. Everything else shows all 942 non-transparent face pixels, with no other sprite on top. A GameMaker foreground pass above the sign therefore reproduces this without a special case.
* Nothing in the sign code changes sprite priority or SAT order.

## 3. Prize tables, parity and the 100-count scan

**DECODED DATA + BYTE-VERIFIED ASSEMBLY.** `$A909`: `A := ($D297 + 1)`, `RRCA`, carry -> `HL := $A919`, else `$A962`; then `$A9FA` runs `CPIR` with `BC = $40`, `A = D29A` over 64 bytes and stores
`class = (C >> 4) & 15 = 3 - index/16` (first match; `$FF` when the count is absent; it also stores the matched count at `$DC00`, a write-only scratch byte - UNRESOLVED, no effect observed).
Each table is four 16-byte rows (class 3, 2, 1, 0) padded with `$FF`; no count appears twice in a table.

<!-- BEGIN u3:prize_classes -->
| table | class | counts | BCD ring counts |
|---|---|---|---|
| $A919 | 3 continue (D2C3 +1) | 4 | 15 30 40 60 |
| $A919 | 2 rings +10 | 9 | 09 19 29 39 49 59 69 79 89 |
| $A919 | 1 life (D299 +1) | 7 | 55 65 77 88 95 97 99 |
| $A919 | 0 retry | 5 | 16 28 32 44 58 |
| $A919 | $FF none | 75 | (all other counts) |
| $A962 | 3 continue (D2C3 +1) | 4 | 00 24 48 72 |
| $A962 | 2 rings +10 | 9 | 10 20 30 40 50 60 70 80 90 |
| $A962 | 1 life (D299 +1) | 7 | 11 33 77 87 94 96 98 |
| $A962 | 0 retry | 5 | 18 36 45 81 89 |
| $A962 | $FF none | 75 | (all other counts) |
<!-- END u3:prize_classes -->

* 25 of 100 counts are rewards or retries in each table; **75** give nothing (an earlier note in `docs/object-18-act-clear.md` says 71 - superseded).
* Counts that are a reward or retry in **both** tables: `$30`, `$40`, `$60` (class 3 in THZ-parity, class 2 in GPZ-parity), `$77` (class 1 in both), `$89` (class 2 / class 0). Ring count `$00` is a **continue** in GPZ/MGHZ/EEZ and nothing in THZ/SEZ/AQZ.
* Observed: all six zones, act 0 and act 1, with ring counts `$15` (class 3 in THZ-parity only) and `$24` (class 3 in GPZ-parity only): the parity matrix is exactly as the tables say (act index 1: SEZ `$15` -> continue, GPZ `$15` -> bird).

## 4. First-pass dispatch and rewards

**BYTE-VERIFIED ASSEMBLY (`$A9A2..$A9F9`), CONTROLLED, EMULATED.** `+$34` is the class. `D500` = player type (Sonic 1, Tails 2 = character + 1).

| class | effect at the landing update | `D3B3` Sonic / Tails | sound | sign state |
|---|---|---|---|---|
| 1 | `CALL $03F2 -> $3104`: `D299 := D299 + 1` (DAA) unless `D299 = $99`; HUD digits refreshed when `D292 = 0` | `$1B` / `$1D` | `$A9` (also at the cap) | 5 |
| 2 | `D29A := (D29A + $10) DAA`, carry dropped | `$1E` / `$1E` | none | 5 |
| 3 | `D2C3 := ((D2C3 + 1) DAA) & $7F` | `$1D` / `$1B` | none | 5 |
| 0 | `+$35 := $FF` (retry) | `$20` | none | 3 |
| `$FF`, 4..8 | none | `$1F` | none | 5 |

* Lives: `$98 -> $99`, `$99 -> $99`; the life sound is requested in all cases (controlled and emulated: `A9` once with lives 99).
* Continues: controlled over `$00..$79` plus `$80, $81, $89, $99, $FF`: `$79 -> $00` (the 80th continue wraps), bit 7 ("a continue was just used", `docs/g0-campaign-contract.md`) is always cleared by the prize,
  and with bit 7 set the DAA runs on the full byte (`$99 -> $00`, `$80 -> $01`). Reaching the sign with bit 7 set is not established (the flag is cleared at `$13ED`).
* Rings: `$90 -> $00` on the GPZ-parity table (class 2 counts are `$10..$90`); `$89 -> $99` on the THZ-parity table.
* The reward is applied **once per landing**; a retry landing applies none.

### Sonic and Tails

Only two things depend on the character: the face selectors for classes 1 and 3 (the life face is the player's own, the continue face the other one's) and the starting counters (3 lives / 0 continues versus 5 / 3).
Everything else - tables, rolls, timings, bonus, art blocks - is shared. Tails was emulated (rings `$09`, `$15`, `$55`, retry `$16` with two roll phases): `D500 = 2`, lives 5 -> 6 for `$55` (face `$1D`), continues 3 -> 4 for `$15` (face `$1B`).
This is ROM data for G6; it does **not** make Tails playable in the POC.

## 5. Retry and retouch

**SOURCE-TRACED + CONTROLLED + EMULATED.**

```
state 3 (wait, frame 1, face $12) --contact--> +$02 = 4, D2BE := 0 (timer stops), camera pan starts
state 4: hop 130 updates (sound $F8 once, $AA every 4 updates) -> $A8FA at the saved Y
$A8FA: +$02 := 5; +$35 == 0 ?  yes -> table lookup ($A9FA) -> class -> dispatch ($A9A2)
                               no  -> class := (D12F & 7) + 1                          -> dispatch ($A9A2)
dispatch: class 0 -> +$35 := $FF, D3B3 := $20, +$02 := 3                               (retry)
          class 1..3 -> reward + selector, sign stays in state 5 (frame 1 held), child $19 is spawned by the state-5 script
          else       -> selector $1F, state 5
state 3 again (blank panel): contact -> +$02 = 6 (+$35 != 0)
state 6: 4 loops x 16 updates = 64 updates of spin (sound $AA every 4), then $A8FA again
```

* **First touch versus retouch:** the retouch has no hop (the sign Y stays), no `$F8`, no second camera pan, and runs 64 updates from the state change (**65 updates from the requesting contact update to the landing**), against 130 for the hop.
  Both set `D2BE := 0` and `D445 := 0`.
* **Re-roll table** (class = `(D12F & 7) + 1`; the ring count is irrelevant - controlled, all 100 counts x both parities):

<!-- BEGIN u3:reroll -->
| D12F & 7 | +$34 | effect | selector Sonic | selector Tails |
|---|---|---|---|---|
| 0 | 1 | life | $1B | $1D |
| 1 | 2 | rings | $1E | $1E |
| 2 | 3 | continue | $1D | $1B |
| 3 | 4 | none | $1F | $1F |
| 4 | 5 | none | $1F | $1F |
| 5 | 6 | none | $1F | $1F |
| 6 | 7 | none | $1F | $1F |
| 7 | 8 | none | $1F | $1F |
<!-- END u3:reroll -->

* The ROM never produces class 0 on a re-roll and `+$35` stays `$FF`, so **there is no second retry**: a retouch always ends in state 5 and the child. The roll byte is `D12F`, the displayed-frame counter incremented by the interrupt
  (`docs/mghz-surface-1b-ceiling-spikes-audit.md`); it is not a PRNG and the outcome depends only on the frame phase of the landing update.
  Emulated pad-only timing (idle 0..8 frames before walking back) produced classes `3, 3, 4, 5, 6, 7, 8, 1, 2` with `D12F` = 226, 226, 227..233 read at `$AA19` - all eight classes were observed for Sonic, and Tails with two phases (226 -> 3, 228 -> 5).
* While the blank panel shows, the sign has **no timeout** and nothing else happens (EMULATED, 900 frames with RIGHT held against the view clamp (player at camera +247) and 900 frames idle): sign state 3, `+$35 = $FF`, timer stopped, no child, no act flag,
  lives/continues/rings untouched. The player keeps control and must touch the sign again (moving, or requesting state `$18`) to continue; the act cannot end without it.
* A **fresh sign object** (state 0 clears `+$34/+$35` and `$A87D` writes `$12` again) would reset a retry and re-roll from the ring table. The shared cleanup `$61E1` removes the sign only after it leaves the window and re-creates it from its placement
  (`docs/object-18-act-clear.md` section 6). During a retry the sign pan locks the camera (left limit raised every state-3 update, right limit = the pan target) and the player is clamped to `cam+$10..cam+$F7` until state `$20`, so this should not be reachable
  in normal play. It was **not forced in emulation** (UNVERIFIED).

## 6. Equal-digit bonus word and interaction

**DECODED DATA + BYTE-VERIFIED ASSEMBLY + CONTROLLED + EMULATED.** Child `$19` state 3 (`$AB48`, **child update 147 = +278 sign updates after contact, 148 after the final landing**):

1. `CALL $041F -> $6276`: `H` = third column of the first table entry whose limit exceeds `D2C0:D2BF` (BCD mm:ss, strict): `L := ((D29A - $11) DAA) + entry.L` (entry.L is 0 in all ten entries; the subtraction has **no borrow into H**, so 0 rings gives `$0989`, 10 rings `$0999`).
2. `H|L = 0 -> HL := $0777`.
3. `D2A6 := HL`. If `H = L & 15 = L >> 4` (all three digits equal) -> `CALL $03F2` **(one life, sound `$A9`, cap `$99`)**.
4. The child then waits for the floor (no timeout) and requests player state `$20` (+280 after contact).

<!-- BEGIN u3:time_table -->
| index | time (D2C0:D2BF) | H |
|---|---|---|
| 0 | < 0:29 | $09 |
| 1 | < 0:59 | $08 |
| 2 | < 1:29 | $07 |
| 3 | < 1:59 | $06 |
| 4 | < 2:29 | $05 |
| 5 | < 2:59 | $04 |
| 6 | < 3:29 | $03 |
| 7 | < 3:59 | $02 |
| 8 | < 4:59 | $01 |
| 9 | any | $00 |
<!-- END u3:time_table -->

Equal-digit combinations (controlled over 21 time samples x 100 counts; all are exactly these): `rings = 11 * (H + 1)` for `H = 1..8` (22 33 44 55 66 77 88 99) -> `$0111..$0888`; `rings = 10` with `H = 9` -> `$0999`; `rings = 11` with `H = 0` (time `>= 4:59`) -> zero -> `$0777`.
In ring order: 22 -> time 3:59-4:58, 33 -> 3:29-3:58, 44 -> 2:59-3:28, 55 -> 2:29-2:58, 66 -> 1:59-2:28, 77 -> 1:29-1:58, 88 -> 0:59-1:28, 99 -> 0:29-0:58, 10 -> under 0:29, 11 -> 4:59 or more.

**Interaction with the class prize (CONTROLLED, 3,200-cell chain matrix, 0 mismatches; EMULATED):**

* The class prize happens at the landing; the equal-digit test happens 148 updates later. They are separate `$03F2` calls: **class 1 plus equal digits = +2 lives** (THZ-parity: 99 in 0:29-0:58 -> `$0888`, 88 in 0:59-1:28, 77 in 1:29-1:58, 55 in 2:29-2:58; GPZ-parity: 77, 33 in 3:29-3:58, and 11 with a time of 4:59 or more -> `$0777`). Emulated: THZ1 rings `$99` with timer 0:40 -> lives 3 -> 5 and `A9` twice;
  GPZ rings `$11` with timer 5:00 -> `$0777`, lives 3 -> 5.
* A non-prize count can still give the equal-digit life alone (GPZ-parity `$99` at 0:40: `$0888`, class `$FF`, +1; controlled chain).
* At lives `$98` the first award reaches `$99` and the second is a no-op that still plays `$A9`; at `$99` both are no-ops.
* The ring prize changes the bonus: rings `$09` become `$19` at the landing, so at 1:00 the child computes `L = $19 - $11 = $08` and writes **`$0708`** (emulated) instead of `$0798` (what `$09` would give); the tally counts the new total.
* Retry does not change this: the child runs once, after the final landing, with the rings and time of that moment (the timer stopped at the first contact).

## 7. Complete timeline (sign-object updates; contact = update 0 = the update that writes `D2BE := 0`)

| update | event | evidence |
|---:|---|---|
| 0 | contact: timer stops, camera pan, sign request 4 | EMULATED |
| +130 | hop lands: `$A8FA`; reward applied; `D3B3` written; first four face tiles uploaded | EMULATED (43 clears, exact) |
| +131..+133 | remaining 12 face tiles (three more batches); sign state 5; child `$19` spawned (+131) | EMULATED |
| +278 | `D2A6` written; equal-digit life + `$A9` | EMULATED |
| +280 | player state `$20` | EMULATED (floor required, no timeout) |
| +309 | act-clear flag `D293` bit 5 (position dependent) | EMULATED |
| retry: +130 | class 0: blank panel (`$20`), state 3 (+131); player free | EMULATED |
| retry: touch at t | request 6 (state 6 at t+1); **landing at t+65**; then the same +1 / +148 / +150 steps relative to that landing | EMULATED |

## 8. GameMaker adapter contract (ADAPTER; rom_native numbers are reproduced by the observations)

Keep ROM and adapter separate. Existing POC names (read-only): `global.life`, `global.chaosContinues`, `global.ring`, `global.chaosFinishTime`, `global.chaosResultsBonus` (`chaos_results_bonus`, written at child age 146 by `OBJ_chaos_object_19/Step_0.gml`),
`chaos_goal_sign_*` in `SCR_chaos_goal`, prize rows `chaos_thz_prize_rows`/`chaos_gpz_prize_rows` in `SCR_chaos_gpz_data` (decimal renderings of the raw BCD **bytes**, `$15 -> 21`; compared read-only with the ROM tables: **byte-identical**). Convert a decimal ring count `n` to the BCD byte `(n/10)*16 + n%10` before the lookup.

**Data to import (canonical, from `data/u3/sign-prize-static.json`):** two 64-byte tables, `zone_table(zone)`, the effect/selector table of section 4, the re-roll table, six face images (32 x 32, palette-index data from the ignored exports or a ROM-time import step - do not commit pixels), the six zone sprite palettes.

**Sign fields (proposal):** `prizeClass` (`+$34`), `retryUsed` (`+$35 != 0`), `faceSelector` (`$12` until the first landing), `faceUploadAge` (updates since the landing, 0..3), `awarded`.

**Behaviour to implement exactly once per sign:**

1. Wake: `faceSelector = $12` (Robotnik), draw frame 1 with it. No face change at contact, during the hop or the spin: they show the old face in frame 1 only.
2. Landing update (+130 after a first touch, +65 after a retouch request): `class = retryUsed ? (frameCounter & 7) + 1 : lookup(table(zone), ringsBCD)`. Apply the reward of section 4 **at that update**. A class-0 result sets `retryUsed`, face `$20`, state 3, no child.
   `frameCounter` is the displayed-frame counter `D12F` (any monotonically increasing frame count reproduces the distribution; the exact phase is not reproducible across ports).
3. Face wipe: change the face one quadrant per update in the order top-left, top-right, bottom-left, bottom-right starting at the landing update (an instant swap is an acceptable adapter simplification; the ROM never shows a mixed face for more than three updates).
4. Convert the POC's decimal `global.ring/life/continues`: ring prize `+10` with a 100 wrap (`90 -> 0`, `89 -> 99`), life `+1` capped at 99, continue `+1` wrapping 79 -> 0 (the ROM BCD wrap). The POC's existing SS-award code uses `(c + 1) & $7F` (wrap at 128); that is a separate, pre-existing difference and was not audited here.
5. **No double award / no duplicate bonus (hard rules):**
   * G1-D must **not** compute the bonus word. G1-C already does at child age 146 (`chaos_results_bonus`); G1-D reads that value.
   * The class reward is applied at the landing only; it must not be applied again at the child, at the act flag, at the results card or at the tally.
   * The equal-digit life belongs to the child update that writes `D2A6` (age 146 in the POC): test the **already computed** word for three equal digits (`777` after the zero replacement counts) and grant one life with sound `$A9`, guarded by a per-sign flag. It is independent of the class reward (+2 is correct).
   * A retry landing grants nothing; the retouch re-roll grants at most one class reward.
   * Apply the class-2 ring prize **before** child age 146 (it is: landing is at least 148 updates earlier) so `global.ring`, `result_rings` and the tally see the new count.
6. Timer: stopped at first contact (G1-C already does this); it stays stopped through the retry.
7. Optional 348 x 196 presentation: the face is anchor relative; nothing in this specification depends on the view width. **Do not** change the sign pan or the sign x here: the end-sign misalignment is the parked **GOAL-FOLLOWUP-1**.
   Observed ROM registration for comparison only: camera `(3831, 405)` at the pan stop, anchor `(3960, 558)` -> face origin on screen `(113, 106)`.

**Finding for Manager (G1-C, not changed here):** `chaos_results_bonus` in `SCR_chaos_results.gml` uses `seconds < 29 + 30*i` for `i < 9`, which ends the `H = 1` bucket at **4:29** (269 s). The ROM's ninth table entry has limit `$0459`, so the bucket ends at **4:59** (299 s)
(`$0359` is the eighth). Times 4:29..4:58 give `H = 1` in the ROM and `H = 0` in the POC (`D2A6` `$01xx` versus `$00xx`/`$0777`). The first eight buckets agree. Recommend fixing this inside G1-D together with the equal-digit award because that test consumes the same word.

## 9. Emulated clears (EMULATED; unmodified ROM; fixtures per scenario)

Fixtures are limited to: ARRIVAL (player and camera 160 px before the sign), RAM presets at the start of play (ring count; for four named scenarios the level timer, lives or continues), and joypad input (RIGHT, plus a timed LEFT for retouches).
Injected presets are marked in the data (`fixtures`). Nothing writes a program counter, a bank, an object or the VDP. 43 clears + two 900-frame retry holds.

<!-- BEGIN u3:observed -->
| scenario | zone/act | player | rings in | class | face | lives | continues | rings | D2A6 |
|---|---|---|---|---|---|---|---|---|---|
| thz1_sonic_r01 | 0/0 | Sonic | $01 | 255 | $1F | 03 -> 03 | 00 -> 00 | $01 -> $01 | $0990 |
| thz1_sonic_r09 | 0/0 | Sonic | $09 | 2 | $1E | 03 -> 03 | 00 -> 00 | $09 -> $19 | $0908 |
| thz1_sonic_r09_ring_prize_bonus | 0/0 | Sonic | $09 | 2 | $1E | 03 -> 03 | 00 -> 00 | $09 -> $19 | $0708 |
| thz1_sonic_r15 | 0/0 | Sonic | $15 | 3 | $1D | 03 -> 03 | 00 -> 01 | $15 -> $15 | $0904 |
| thz1_sonic_r15_continues79_wrap | 0/0 | Sonic | $15 | 3 | $1D | 03 -> 03 | 79 -> 00 | $15 -> $15 | $0904 |
| thz1_sonic_r16_retouch_wait0 | 0/0 | Sonic | $16 | 3 | $1D | 03 -> 03 | 00 -> 01 | $16 -> $16 | $0905 |
| thz1_sonic_r16_retouch_wait1 | 0/0 | Sonic | $16 | 3 | $1D | 03 -> 03 | 00 -> 01 | $16 -> $16 | $0905 |
| thz1_sonic_r16_retouch_wait2 | 0/0 | Sonic | $16 | 4 | $1F | 03 -> 03 | 00 -> 00 | $16 -> $16 | $0905 |
| thz1_sonic_r16_retouch_wait3 | 0/0 | Sonic | $16 | 5 | $1F | 03 -> 03 | 00 -> 00 | $16 -> $16 | $0905 |
| thz1_sonic_r16_retouch_wait4 | 0/0 | Sonic | $16 | 6 | $1F | 03 -> 03 | 00 -> 00 | $16 -> $16 | $0905 |
| thz1_sonic_r16_retouch_wait5 | 0/0 | Sonic | $16 | 7 | $1F | 03 -> 03 | 00 -> 00 | $16 -> $16 | $0905 |
| thz1_sonic_r16_retouch_wait6 | 0/0 | Sonic | $16 | 8 | $1F | 03 -> 03 | 00 -> 00 | $16 -> $16 | $0905 |
| thz1_sonic_r16_retouch_wait7 | 0/0 | Sonic | $16 | 1 | $1B | 03 -> 04 | 00 -> 00 | $16 -> $16 | $0905 |
| thz1_sonic_r16_retouch_wait8 | 0/0 | Sonic | $16 | 2 | $1E | 03 -> 03 | 00 -> 00 | $16 -> $26 | $0915 |
| thz1_sonic_r55 | 0/0 | Sonic | $55 | 1 | $1B | 03 -> 04 | 00 -> 00 | $55 -> $55 | $0944 |
| thz1_sonic_r55_lives99_cap | 0/0 | Sonic | $55 | 1 | $1B | 99 -> 99 | 00 -> 00 | $55 -> $55 | $0944 |
| thz1_sonic_r99_t0040_two_lives | 0/0 | Sonic | $99 | 1 | $1B | 03 -> 05 | 00 -> 00 | $99 -> $99 | $0888 |
| thz1_tails_r09 | 0/0 | Tails | $09 | 2 | $1E | 05 -> 05 | 03 -> 03 | $09 -> $19 | $0908 |
| thz1_tails_r15 | 0/0 | Tails | $15 | 3 | $1B | 05 -> 05 | 03 -> 04 | $15 -> $15 | $0904 |
| thz1_tails_r16_retouch_wait0 | 0/0 | Tails | $16 | 3 | $1B | 05 -> 05 | 03 -> 04 | $16 -> $16 | $0905 |
| thz1_tails_r16_retouch_wait3 | 0/0 | Tails | $16 | 5 | $1F | 05 -> 05 | 03 -> 03 | $16 -> $16 | $0905 |
| thz1_tails_r55 | 0/0 | Tails | $55 | 1 | $1D | 05 -> 06 | 03 -> 03 | $55 -> $55 | $0944 |
| zone0_act0_sonic_r15 | 0/0 | Sonic | $15 | 3 | $1D | 03 -> 03 | 00 -> 01 | $15 -> $15 | $0904 |
| zone0_act0_sonic_r24 | 0/0 | Sonic | $24 | 255 | $1F | 03 -> 03 | 00 -> 00 | $24 -> $24 | $0913 |
| zone0_act1_sonic_r15 | 0/1 | Sonic | $15 | 3 | $1D | 03 -> 03 | 00 -> 01 | $15 -> $15 | $0904 |
| zone1_act0_sonic_r15 | 1/0 | Sonic | $15 | 255 | $1F | 03 -> 03 | 00 -> 00 | $15 -> $15 | $0904 |
| zone1_act0_sonic_r24 | 1/0 | Sonic | $24 | 3 | $1D | 03 -> 03 | 00 -> 01 | $24 -> $24 | $0913 |
| zone1_act1_sonic_r15 | 1/1 | Sonic | $15 | 255 | $1F | 03 -> 03 | 00 -> 00 | $15 -> $15 | $0904 |
| zone1_sonic_r00_even_continue | 1/0 | Sonic | $00 | 3 | $1D | 03 -> 03 | 00 -> 01 | $00 -> $00 | $0989 |
| zone1_sonic_r11_t0500_zero_word_two_lives | 1/0 | Sonic | $11 | 1 | $1B | 03 -> 05 | 00 -> 00 | $11 -> $11 | $0777 |
| zone1_sonic_r18_even_retry | 1/0 | Sonic | $18 | 6 | $1F | 03 -> 03 | 00 -> 00 | $18 -> $18 | $0907 |
| zone2_act0_sonic_r15 | 2/0 | Sonic | $15 | 3 | $1D | 03 -> 03 | 00 -> 01 | $15 -> $15 | $0904 |
| zone2_act0_sonic_r24 | 2/0 | Sonic | $24 | 255 | $1F | 03 -> 03 | 00 -> 00 | $24 -> $24 | $0913 |
| zone2_act1_sonic_r15 | 2/1 | Sonic | $15 | 3 | $1D | 03 -> 03 | 00 -> 01 | $15 -> $15 | $0904 |
| zone3_act0_sonic_r15 | 3/0 | Sonic | $15 | 255 | $1F | 03 -> 03 | 00 -> 00 | $15 -> $15 | $0904 |
| zone3_act0_sonic_r24 | 3/0 | Sonic | $24 | 3 | $1D | 03 -> 03 | 00 -> 01 | $24 -> $24 | $0913 |
| zone3_act1_sonic_r15 | 3/1 | Sonic | $15 | 255 | $1F | 03 -> 03 | 00 -> 00 | $15 -> $15 | $0904 |
| zone4_act0_sonic_r15 | 4/0 | Sonic | $15 | 3 | $1D | 03 -> 03 | 00 -> 01 | $15 -> $15 | $0904 |
| zone4_act0_sonic_r24 | 4/0 | Sonic | $24 | 255 | $1F | 03 -> 03 | 00 -> 00 | $24 -> $24 | $0913 |
| zone4_act1_sonic_r15 | 4/1 | Sonic | $15 | 3 | $1D | 03 -> 03 | 00 -> 01 | $15 -> $15 | $0904 |
| zone5_act0_sonic_r15 | 5/0 | Sonic | $15 | 255 | $1F | 03 -> 03 | 00 -> 00 | $15 -> $15 | $0904 |
| zone5_act0_sonic_r24 | 5/0 | Sonic | $24 | 3 | $1D | 03 -> 03 | 00 -> 01 | $24 -> $24 | $0913 |
| zone5_act1_sonic_r15 | 5/1 | Sonic | $15 | 255 | $1F | 03 -> 03 | 00 -> 00 | $15 -> $15 | $0904 |
<!-- END u3:observed -->

## 10. Unresolved and limitations

* `$A8C8` writes `D4A3 := $FF` at the first-touch state 4; purpose still unknown (`docs/object-18-act-clear.md`). `$DC00` receives the matched ring count; no reader found by an operand scan, no observable effect.
* The state of the sign after it leaves the window and is recreated (fresh state 0) is source-traced only; see section 5.
* Whether bit 7 of `D2C3` can still be set when the sign pays a continue is not established.
* Sound requests are observed through the sound register of the harness (approximate); only `$A9` (life) is asserted. Audio wiring is out of scope.
* Tails is research data only. The child panel graphics/digits (`D3F2..D3F4`), HUD, Continue/Game Over/TIME OVER, boss zones and Special Stage gameplay are out of scope.
* Harness frames differ from ROM updates by lag frames (observed up to +3 over 130 updates); all counts above are sign updates, which agree exactly in every scenario.
* No end-to-end natural clear of all 18 acts was run; each zone and act-0/act-1 was cleared once through the real sign chain (zones 0..5, both acts), counted at the sign, with controlled triggers (ring presets, timer presets) where stated.

## 11. Reproduction

```
python tools/u3_sign_prizes.py --validate              # no ROM
python tools/u3_sign_prizes.py "<ROM>" --check          # complete regeneration compare (static, Z80, 43 clears, hashes; ~3 minutes, Python >= 3.10)
python tools/u3_sign_prizes.py "<ROM>"                  # rewrite data/u3/*.json and build/u3/ (ignored): faces, frames, tile blocks, per-zone sheets
python tools/u3_sign_prizes.py --doc                    # refresh the generated tables of this document
python -m unittest tests.test_u3_sign_prizes
```

### Routines and regions

<!-- BEGIN u3:routines -->
| routine | CPU range (end exclusive) | file | bytes | SHA-256 | role |
|---|---|---|---|---|---|
| `dyn_loader` | res $7AC2-$7BA6 | 0x07AC2 | 228 | `4e38aedf882d` | dynamic graphics loader: D3B3 selector -> list -> 4 tiles per call to VRAM (bank byte bit 7 = remap through the $0100 table) |
| `dyn_selector_table` | res $7BA6-$7BCA | 0x07BA6 | 36 | `cddad45fedf2` | 18 little-endian list pointers for selectors $10..$21 |
| `dyn_lists` | res $7BCA-$7C71 | 0x07BCA | 167 | `d088a4654220` | selector lists, six bytes per entry [bank, tiles, vram_lo, vram_hi, src_lo, src_hi], $FF ends a list |
| `sign_wake_states` | 0C:$A867-$A88E | 0x32867 | 39 | `d83aa65b7c78` | states 0..2: clear class/retry bytes, wait for on-screen, D3B3 := $12 |
| `sign_contact_state3` | 0C:$A88E-$A8C8 | 0x3288E | 58 | `b32f8dde6d48` | state 3 contact test, timer stop, state 4 (first touch) or 6 (retouch) |
| `sign_state4_marker` | 0C:$A8C8-$A8CE | 0x328C8 | 6 | `10f33b3d9cfe` | D4A3 := $FF (purpose unresolved) |
| `sign_hop_landing` | 0C:$A8CE-$A8FA | 0x328CE | 44 | `21856dbf8e25` | state-4 hop physics; at the saved Y calls $A8FA |
| `sign_landing_prize` | 0C:$A8FA-$A919 | 0x328FA | 31 | `66122494219b` | landing: state 5, retouch test (+$35), zone parity table select |
| `sign_prize_table_odd` | 0C:$A919-$A959 | 0x32919 | 64 | `a400c282f3f7` | 64-byte BCD ring-count table used when (zone + 1) is odd |
| `sign_prize_select_even` | 0C:$A959-$A962 | 0x32959 | 9 | `a0d6fc8d7052` | even-parity branch: HL := $A962, CALL $A9FA, JP $A9A2 |
| `sign_prize_table_even` | 0C:$A962-$A9A2 | 0x32962 | 64 | `3a0d4b966d01` | 64-byte BCD ring-count table used when (zone + 1) is even |
| `sign_prize_dispatch` | 0C:$A9A2-$A9EC | 0x329A2 | 74 | `f311bd63deee` | class -> reward ($03F2 life, rings +$10, continue +1) and D3B3 face selector |
| `sign_retry_setup` | 0C:$A9EC-$A9FA | 0x329EC | 14 | `6c2eb86b411b` | class 0: +$35 := $FF, D3B3 := $20, state 3 |
| `sign_prize_lookup` | 0C:$A9FA-$AA16 | 0x329FA | 28 | `21146a16e701` | CPIR over a 64-byte table, class = C >> 4 (also stores the ring count at $DC00) |
| `sign_retouch_reroll` | 0C:$AA16-$AA22 | 0x32A16 | 12 | `4fced8442bc5` | +$34 := ($D12F & 7) + 1, then the common dispatch |
| `sign_camera_pan` | 0C:$AA22-$AA47 | 0x32A22 | 37 | `ac4de7e5f5a6` | sign pan target (signX - $80, signY - $99), vector $0359 |
| `child19_spawn_vector` | 0C:$AA47-$AA4F | 0x32A47 | 8 | `17babded4f08` | state 5 script call: spawn type $19 |
| `child19_states` | 0C:$AA4F-$AB9F | 0x32A4F | 336 | `6dd036dd15a5` | type $19 table, scripts, state callbacks and constants (digit cycling, slide-in) |
| `child19_bonus_state3` | 0C:$AB48-$AB8C | 0x32B48 | 68 | `210d5092ec87` | state 3: $041F bonus word, zero -> $0777, equal digits -> $03F2, panel digits |
| `bonus_word_6276` | res $6276-$62AD | 0x06276 | 55 | `4acadba93d4d` | $041F target: time bucket index, H/L word |
| `bonus_time_table` | res $62AD-$62D5 | 0x062AD | 40 | `0095da7fd315` | ten 4-byte entries: limit word (BCD mmss), L byte, H byte |
| `life_award_3104` | res $3104-$3138 | 0x03104 | 52 | `a1eea829e8c4` | sound $A9, D299 + 1 capped at $99, HUD digits when D292 = 0 |
| `vectors_03F2_041F` | res $03F2-$03F5 | 0x003F2 | 3 | `39eb0b74ce68` | JP $3104 |
| `vectors_041F` | res $041F-$0422 | 0x0041F | 3 | `475e4cd3d459` | JP $6276 |
| `level_sprite_palette_index` | res $7F3C-$7F60 | 0x07F3C | 36 | `cd522bd78d05` | (zone * 3 + act) * 2 -> [background palette, sprite palette] |
| `sprite_loader_vector_check` | res $794F-$7979 | 0x0794F | 42 | `c21afec2d5ae` | palette index loader $794F |
<!-- END u3:routines -->

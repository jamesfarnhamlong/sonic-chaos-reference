# U2-A: Act 3 boss completion and bonus-object tracing

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified by the tool, never committed). Base: Research `main` `1fb25857470f7c867d763c435a324befea751c12`.
POC `SonicChaos_POC_g1d` @ `d9275feeca1a799928b6eb1a866d32275c4024b5` was **read, not run, not edited**.
Tool: `tools/u2_act3_boss_bonus.py` (`ROM`, `--check`, `--validate`, `--doc`; Python >= 3.10, `py -3.13`). Tests: `tests/test_u2_act3_boss_bonus.py` (43). Data: `data/u2/act3-boss-bonus-{static,controlled,observed}.json`.
Builds on `docs/g0-campaign-contract.md` (T05/T06), `docs/u3-sign-prize-presentation.md`, `docs/u4-ordinary-results.md`, `docs/object-50.md`, `docs/thz3-boss-support-audit.md`, the per-zone boss audits and `docs/eez-boss-endgame-audit.md`.

Evidence tiers (used in every table and every test class): **SOURCE** decoded ROM bytes / hashes / anchors / script decode · **CONTROLLED** original routines on the Z80 core with hand-built slots · **EMULATED** whole fights of the unmodified ROM in the
approximate SMS harness, **driven by FIXTURE writes** (arena placement and synthetic player/attack placement at update boundaries; every boss, bonus, results and zone routine is the original) · **FIXTURE** injected RAM (the G0-style flag; *not* a natural clear) ·
**POC SOURCE-READ** GameMaker code transcribed, never executed. No fight here is a controller-only playthrough. Frames are harness frames; hook events carry the frame being run, polled events the frame just completed (+1).

## 1. Answer

1. **Two different bonuses, paid in different places, both exactly once.**
   * The **fixed boss bonus** comes from the results code `$2D55` / table `$2D84`: `50, 100, 150, 200, 250, 600` steps of 10 raw = **500 / 1000 / 1500 / 2000 / 2500** (zones THZ..AQZ; the 6000 entry is unreachable). It is added to the score by the results tally, not at defeat.
   * The **time/ring bonus word** `D2A6` comes from the boss-created **type `$0A` parameter 0** object (`0C:$9C86`): `CALL $041F` -> `D2A6`. The tally later pays `rings * 10` and then the word at 1 raw per step. It has **no** zero replacement (`$0777`) and **no** equal-digit life: those belong only to the sign child `$19` (U3).
   * Observed, every ordinary zone: score is unchanged until `$2D55`; then `fixed + rings*10 + word` is added exactly once (e.g. THZ3 `500 + 470 + 936 = 1906`, rings `$47`, word `$0936`).
2. **Who creates `$0A`.** Exactly two immediate allocation sites exist: `1E:$81E2` (the **shared release** `$81BD`/`$81DF`, used by THZ3 `$50`, SEZ3 `$54`, MGHZ3 `$56` via its `$81F4` branch and AQZ3 `$59`) and `1E:$9D4E` (GPZ3's head release `$9D26`). Both also call `$03F5` (player state `$20`).
   **EEZ3 never creates a bonus-word object**: its `$61` writes `D293 := $50` directly; its state-5 script spawns two `$0A` **parameter 1** sparkles that never write `D2A6`; the results card and the fixed bonus are skipped.
3. **Natural versus injected.** The G0 spine's six act-index-2 rows are 1 forced player state `$20` (THZ3) and 5 injected `D293` flags: **none contains a boss defeat, a `$0A` object or a `D2A6` write**. Re-running the injection here gives `fixed + rings*10` and *no word*: a natural clear pays exactly the word more (936 / 836 raw).
4. **G1-E must not reuse the POC's `chaos_boss_bonus` / `+500` formulas** (section 8): both disagree with the ROM.

## 2. Six-zone table (verified / observed / unknown)

| zone | controller | SOURCE producer | CONTROLLED | EMULATED (fixture-driven fight) | still unknown |
|---|---|---|---|---|---|
| THZ3 | `$50` | `$81BD` in state-5 script `$961E` -> tail `$81DF` | release needs floor bit 1; `$0A`/0 + `$0F` + state `$20` (sound `$97`) | defeat -> `$0A` -> D2A6 `$0936` -> flag -> results -> GPZ1 | natural controller-only fight |
| GPZ3 | `$51` head | `$9D26` (head state 14, grounded) -> `$9D55 JP $03F5` | same, boss slot becomes `$FF`, right limit `$0780` | same chain -> SEZ1 | caller recorded as the scheduler (`JP`) |
| SEZ3 | `$54` | `$81BD`, script `$961E` | same as THZ3 | same chain -> MGHZ1 | SEZ3 early lift (parked) |
| MGHZ3 | `$56` | `$81BD` -> `$81F4` branch (X >= `$0D1C` **and** floor) -> `$81DF` | X 3355 blocks, 3356 releases; **no left-limit write** | flag **1 frame** after the request (X gate already met) -> AQZ1 | - |
| AQZ3 | `$59` | `$81BD`, script `$A7F0` (record `$A857`) | same as THZ3 | same chain -> EEZ1 | harness runs 11 cases; first chain analysed |
| EEZ3 | `$61` | **no release**: `$BB1A` early clear or `$BB61` final write `D293 := $50` | `$0A` parameter 1 writes no D2A6 | no results, no fixed bonus, no `$0A`/0; ending branch by `D2CC` | sparkles' spawn (24 updates into state 5) not reached by the fixtures; `$60` state 5 shares script `$961E` (reachability unverified) |

<!-- BEGIN u2:producers -->
| zone | controller | defeat/clear producer | state | release gate |
|---|---|---|---|---|
| THZ3 | $50 | $81BD via state-5 script $961E | 5 | floor bit 1 ($D522 bit 1) |
| GPZ3 | $51 | $9D26 head state 14 (grounded) | 14 | floor bit 1 ($D522 bit 1) |
| SEZ3 | $54 | $81BD via state-5 script $961E | 5 | floor bit 1 |
| MGHZ3 | $56 | $81BD -> $81F4 branch -> $81DF | 5 | player X >= $0D1C (3356) AND floor bit 1; no left-limit write |
| AQZ3 | $59 | $81BD via state-5 script $A7F0 (record $A857) | 5 | floor bit 1 |
| EEZ3 | $61 | NONE: $61 writes D293 := $50 directly (state 5 early clear BB28, or state 7 final BB6C) | 5 or 7 | state 5: any case except Sonic with D2CC == $1F; state 7: after contact |
<!-- END u2:producers -->

## 3. The natural chain per zone (THZ, GPZ, SEZ, MGHZ, AQZ)

SOURCE + EMULATED (every step observed in all five fights):

1. Boss HP reaches 0 -> boss states run explosions/`$34` puffs and arrive at the release state (`$50/$54/$56/$59`: state 5 callback `$81BD`; GPZ: head state 14 `$9D26`).
2. **Release update** (floor bit 1 required; MGHZ also player X >= 3356): left limit := camera X (`$D280`, not for MGHZ), `CALL $035C` releases the sign-style camera pan, right limit := the saved value (`+$25/+$27`; GPZ `$0780`), then `CALL $03F5` (**player state `$20`**, sound `$97` because `D298 = 2`),
   allocate **`$0A` parameter 0** (first free slot from `$D540`), `+$3F := $80`, `+$3E := 0` (token cleared: never re-created), `JP $033E` (the boss slot becomes `$0F`).
3. **Next update**: the `$0A` object's state-0 callback `$9C86` runs: `CALL $041F` with the timer `D2BF/D2C0` and rings `D29A` of that update, `D2A6 := HL`, state 2 sparkle emitter (every 8 updates, forever).
4. State `$20` handler `$83A6` runs the player right; beyond `cameraX + $120` it sets **`D293` bit 4** (`$83ED`, act index 2). The delay is position dependent (observed 1 to 237 frames).
5. `$1543`: fades, `$1594` (zone < 5) -> **results card `$32F9`** 198..199 frames after the flag -> **`$2D55` fixed bonus** -> **`$2D08` tally** (rings x 10, then the word) -> `$15CE` zone increment -> next act-1 loader.

<!-- BEGIN u2:timeline -->
| fight | $03F5 request | D2A6 set | flag bit 4 ($83ED) | $1543 | results card | $2D55 fixed bonus | $2D08 tally | zone increment $15CE | ending selector | title |
|---|---|---|---|---|---|---|---|---|---|---|
| THZ3 | 0 | 2 | 187 | 188 | 386 | 462 | 486 | 1043 | - | - |
| GPZ3 | 0 | 2 | 123 | 124 | 322 | 398 | 435 | 992 | - | - |
| SEZ3 | 0 | 2 | 237 | 238 | 436 | 512 | 563 | 1120 | - | - |
| MGHZ3 | 0 | 2 | 1 | 2 | 200 | 276 | 340 | 897 | - | - |
| AQZ3 | 0 | 2 | 199 | 200 | 398 | 474 | 551 | 1076 | - | - |
| EEZ3_sonic_flags1F | - | - | - | 0 | - | - | - | 198 | 200 | 9907 |
| EEZ3_sonic_flags00 | - | - | - | -1 | - | - | - | 198 | 200 | 2015 |
| EEZ3_sonic_flags3F | - | - | - | -1 | - | - | - | 198 | 200 | 9907 |
<!-- END u2:timeline -->

Frames after the `$03F5` request (hook frame). The `$0A` object exists one frame later (polled), computes the word in that same update, and the poll sees `D2A6` one frame after that.

<!-- BEGIN u2:observed -->
| fight | $0A param 0 frame | D2A6 | state-$20 request | flag bit 4 | results card | fixed bonus | ring units | word units | tally total | zone/act |
|---|---|---|---|---|---|---|---|---|---|---|
| THZ3 | 1628 | $0936 | 1627 | 1814 | 2013 | 500 | 470 | 936 | 1406 | 0/2 -> 1/0 |
| GPZ3 | 2160 | $0936 | 2159 | 2282 | 2481 | 1000 | 470 | 936 | 1406 | 1/2 -> 2/0 |
| SEZ3 | 1799 | $0936 | 1798 | 2035 | 2234 | 1500 | 470 | 936 | 1406 | 2/2 -> 3/0 |
| MGHZ3 | 1487 | $0936 | 1486 | 1487 | 1686 | 2000 | 470 | 936 | 1406 | 3/2 -> 4/0 |
| AQZ3 | 3383 | $0836 | 3382 | 3581 | 3780 | 2500 | 470 | 836 | 1306 | 4/2 -> 5/0 |
| EEZ3_sonic_flags1F | - | - | - | - | - | 0 | 0 | 0 | 0 | 5/2 -> 6/0 |
| EEZ3_sonic_flags00 | - | - | - | - | - | 0 | 0 | 0 | 0 | 5/2 -> 6/0 |
| EEZ3_sonic_flags3F | - | - | - | - | - | 0 | 0 | 0 | 0 | 5/2 -> 6/0 |
<!-- END u2:observed -->

* Rings are the fixture `$47` (the fight harnesses write it), so `ring units = 470` everywhere; the time bytes are natural: 0:09 THZ and MGHZ, 0:14 SEZ, 0:20 GPZ and 0:40 AQZ -> `H = 9, 9, 9, 9, 8`.
* `D2A6` always equals the pure model of `$041F` at the compute update (`$0936` THZ/GPZ/SEZ/MGHZ, `$0836` AQZ); the grid of 21 times x 100 ring counts was executed on the original `$9C86` (`CONTROLLED`).
* **No double count:** the score is `0` at `$2D55` entry in every fight; the total increase equals `fixed + tally` (rings + word) exactly; there is one `$2D55`, one `$2D08`, one results card, one zone increment, one `$0A` parameter 0 and one `D2A6` write per clear.
* Lives, continues and emeralds are unchanged across the rollover; the next act starts at the RQ4 record (GPZ1 `(110,384)`, SEZ1 `(110,718)`, MGHZ1 `(78,192)`, AQZ1 `(110,206)`, EEZ1 `(238,864)`, all with the ROM camera target) - **observed**, not assumed.

### The fixed table

<!-- BEGIN u2:fixed_bonus -->
| zone | steps of 10 raw | raw units | status |
|---|---|---|---|
| THZ | 50 | 500 | used |
| GPZ | 100 | 1000 | used |
| SEZ | 150 | 1500 | used |
| MGHZ | 200 | 2000 | used |
| AQZ | 250 | 2500 | used |
| EEZ | 600 | 6000 | never reached (results skipped) |
<!-- END u2:fixed_bonus -->

## 4. The `$0A` object (SOURCE + CONTROLLED)

`type $0A`: state table `0C:$9C58`, states `$9C5E`, `$9BE8`, `$9C64`. State 0 is one 224-update record with callback **`$9C86`** (`dd 36 02 01` request state 1; `A := +$3F`; `RET NZ`; request state 2; `CALL $041F`; `LD ($D2A6),HL`; copy the player X/Y).

| parameter | who | effect (CONTROLLED) |
|---|---|---|
| `0` | boss release (`LD C,$0A` at `$81E2` / `$9D4E`) | `D2A6 := $041F` word (e.g. `$0936`), state 2 sparkle emitter, position := player |
| `$FF` | the object itself (state 2, every 8 updates, dy -12) | sparkle, 28 updates, no `D2A6` |
| `1` | EEZ `$61` state-5 script (dx +4 / -4) | stays state 1: **no `D2A6`**, no life |

* `D2A6` is stored exactly as returned: **`H|L = 0` stays 0** (only rings `$11` at time >= 4:59 or 9:00: two cells of the grid) - the sign child's `$0777` and equal-digit life do not apply.
* The 21 x 100 grid equals the U3 model of `$041F`; 19 cells are equal-digit words and **none** changes `D299` (CONTROLLED).
* `D2A6` writers (G0 census, unchanged): sign child `$19` (`0C:$AB52`), boss object `$0A` parameter 0 (`0C:$9C96`), Special Stage success (`1E:$94BD`), and the tally's own decrements.
* **Absent object:** if all 16 slots are occupied the creator `$5E9C` returns without creating anything; the boss still converts to `$0F`, player state `$20` is still requested and `D2A6` stays 0. No fallback bonus exists in the ROM (CONTROLLED, `allocation_failure`).

### Shared release routine (SOURCE anchors, CONTROLLED)

`$81BD`: `type == $56` -> `$81F4`; else `CALL $037D`, floor bit 1 required. `$81CD`: `D280 := cameraX; CALL $035C; D282 := (+$25/+$27)`. `$81DF`: `CALL $03F5`, `LD C,$0A / LD H,0 / CALL $032C`, `+$3F := $80`, `+$3E := 0`, `JP $033E`.
The same script `$961E` is the state-5 script of `$50`, `$54`, `$56` **and `$60`** (EEZ); `$59` has its own record at `$A857`. `$5E`, `$5F`, `$61`, `$62` do not call `$81BD`.

## 5. EEZ3 (T06): terminal route

SOURCE + EMULATED (three emerald-flag variants, Sonic):

* `$61` state 5 (`$BB1A`): **Sonic (`D500 = 1`) with `D2CC == $1F` waits for contact**; every other case writes **`D293 := $50` immediately** (early clear). State 7 (`$BB61`): `D2CC |= $20`, `D293 := $50`, type := `$FF`.
* There is **no `$03F5` request, no `$83ED`, no results card, no fixed bonus, no `$0A` parameter 0 and no `D2A6` write**; the score is unchanged. `$1594` skips `$32F9` and falls into `$15CE` (zone 6, act 0) -> `$1365` -> `$18ED`.
* Ending branch by `D2CC & $3F == $3F`: full Sonic `$18FE`, partial `$1A41`, other character `$1ACD` (Tails is G6 research data; not run here). Full ending returns to the title through the credits (about 9,700 frames after the selector), the partial ending after `TRY AGAIN` (about 1,800).

<!-- BEGIN u2:eez -->
| variant | D2CC in | last clear write D293 | results card | ending branch | D2CC out |
|---|---|---|---|---|---|
| EEZ3_sonic_flags1F | $1F | $50 | no | ending_full_sonic | $3F |
| EEZ3_sonic_flags00 | $00 | $50 | no | ending_partial_sonic | $00 |
| EEZ3_sonic_flags3F | $3F | $50 | no | ending_full_sonic | $3F |
<!-- END u2:eez -->

## 6. Injected clears versus natural clears (FIXTURE)

`tools/g0_scenarios.py campaign_spine` forced player state `$20` at THZ3 and raised `D293` for 15 other acts. Re-running that style of injection at each zone's natural start (`RAM D293 |= $10`, rings `$47`) reproduces the tail and the fixed bonus but **never a word**:

<!-- BEGIN u2:injected -->
| injected clear | $0A objects | D2A6 writes | fixed bonus | ring units | word units | tally total |
|---|---|---|---|---|---|---|
| THZ3_injected_flag | 0 | 0 | 500 | 470 | 0 | 470 |
| GPZ3_injected_flag | 0 | 0 | 1000 | 470 | 0 | 470 |
| SEZ3_injected_flag | 0 | 0 | 1500 | 470 | 0 | 470 |
| MGHZ3_injected_flag | 0 | 0 | 2000 | 470 | 0 | 470 |
| AQZ3_injected_flag | 0 | 0 | 2500 | 470 | 0 | 470 |
<!-- END u2:injected -->

So the G0 oracle is correct for the **tail, fixed bonus and rollover** and says nothing about the type-`$0A` bonus word. A premature flag (boss not yet created) is exactly this case: no `$0A`, no `D2A6`, no state-`$20` request.

## 7. Routines and regions (SOURCE)

<!-- BEGIN u2:routines -->
| routine | CPU range (end exclusive) | file | bytes | SHA-256 | role |
|---|---|---|---|---|---|
| `creator_5E9C` | res $5E9C-$5EB7 | 0x05E9C | 27 | `75ab05f0ff52` | vector $032C: C = type, H = parameter, first free slot from $D540 (16 slots); no free slot -> RET with nothing created |
| `player_state20_4892` | res $4892-$48A7 | 0x04892 | 21 | `ad096870119c` | vector $03F5: D502 := $20, request $89 (act index != 2) or $97 (act index 2) |
| `act_clear_tail_14AE` | res $14AE-$1543 | 0x014AE | 149 | `30ad4626a11d` | main-loop tail for D293 bit 5 (act index 0/1) |
| `zone_clear_tail_1543` | res $1543-$15F2 | 0x01543 | 175 | `46b9f946a53c` | main-loop tail for D293 bit 4 (act index 2): fades, results gate $1594, zone increment $15CE |
| `tally_loops_2D08` | res $2D08-$2D55 | 0x02D08 | 77 | `98a654fd67b6` | ring loop (10 raw per ring) then the D2A6 bonus-word loop (1 raw per step) |
| `boss_bonus_loop_2D55` | res $2D55-$2D84 | 0x02D55 | 47 | `b179e863ac7e` | act index 2 only: N steps of 10 raw before the tally loops |
| `boss_bonus_table_2D84` | res $2D84-$2D90 | 0x02D84 | 12 | `043f523a1b4e` | six 16-bit step counts, one per zone |
| `bonus_word_6276` | res $6276-$62AD | 0x06276 | 55 | `4acadba93d4d` | $041F: time bucket + (D29A - $11) -> HL |
| `bonus_time_table_62AD` | res $62AD-$62D5 | 0x062AD | 40 | `0095da7fd315` | ten 4-byte entries: limit mm:ss BCD, L, H |
| `state20_handler_83A6` | 0C:$83A6-$8400 | 0x303A6 | 90 | `b1d9c1a6cfb6` | player state $20 handler: run right, sets D293 bit 5 (act index < 2) or bit 4 (act index 2) beyond cameraX + $120 |
| `bonus_object_0A` | 0C:$9C58-$9CAC | 0x31C58 | 84 | `3f43cacb2a10` | type $0A: 3-entry state table, state-0 and sparkle-emitter scripts, state-0 callback (D2A6 for parameter 0), player-position copy |
| `boss_release_81BD` | 1E:$81BD-$8212 | 0x781BD | 85 | `3414b6424c06` | shared state-5 release: floor gate, camera/limits, $03F5, allocate $0A parameter 0, convert to $0F; $81F4 = MGHZ3 branch |
| `boss_state5_script_961E` | 1E:$961E-$9632 | 0x7961E | 20 | `40a5f65fd357` | script of state 5 of $50/$54/$56/$60: record whose callback is $81BD |
| `aqz_state5_script_A7F0` | 1E:$A7F0-$A85B | 0x7A7F0 | 107 | `391ed9bcdf3c` | script of state 5 of $59 (callback record at $A857 -> $81BD) |
| `gpz_head_release_9D26` | 1E:$9D26-$9D58 | 0x79D26 | 50 | `c15a5df9d48d` | GPZ3 head state 14 grounded release: limits, $0A parameter 0, $03F5 |
| `eez_61_state5_script_B9FF` | 1E:$B9FF-$BA37 | 0x7B9FF | 56 | `47179180dcc6` | $61 state 5 script: two spawns of type $0A parameter 1 (dx +4/-4) after 24 updates |
| `eez_61_state5_callback_BB1A` | 1E:$BB1A-$BB51 | 0x7BB1A | 55 | `c355dbd184a1` | $61 state 5 callback: early clear D293 := $50 unless Sonic with D2CC = $1F |
| `eez_61_final_BB61` | 1E:$BB61-$BB76 | 0x7BB61 | 21 | `48f76b413761` | $61 state 7: D2CC \|= $20, D293 := $50, type := $FF |
| `zone_results_gate_1594` | res $1594-$15F2 | 0x01594 | 94 | `ceff253f12a7` | zone >= 5 skips the results card |
<!-- END u2:routines -->

## 8. G1-E implementation contract (POC SOURCE-READ comparison + ROM rules)

POC facts read at `d9275fe` (not run): `chaos_boss_bonus(seconds, rings)` in `SCR_chaos_boss.gml` (H = `max(0, 9 - floor(seconds/30))`, L = `(rings - 11) mod 100`, `steps = H*100 + L`) and `global.chaosBossClearScore = ring*10 + steps + 500`
(same line in the GPZ/MGHZ/SEZ boss scripts); `chaos_act_complete` sends only act < 3 to the results card, act 3 keeps the developer return or `zoneGoto` + `SCR_save_game`; `chaos_results_bonus` is the G1-D corrected sign-child word (with the `777` replacement).

| POC today | ROM fact | action |
|---|---|---|
| H = `9 - floor(s/30)` | strict BCD limits `0:29, 0:59, 1:29, ... 3:59, 4:59` (`$62AD`): wrong at seconds 29, 59, 89, 119, 149, 179, 209, 239 and 270..298 (**37 of 600 seconds**, tested) | use the ROM bucket table (the corrected `chaos_results_bonus` core), not `chaos_boss_bonus` |
| `+500` for every zone | 500 / 1000 / 1500 / 2000 / 2500 by zone (`$2D84`) | take the fixed bonus from the table at `$2D55` time |
| pre-computed `chaosBossClearScore` | score is untouched until the results tally | add nothing at defeat; the tally owns every score change |
| word via `chaos_results_bonus` (zero -> 777) | `$0A` leaves zero as zero, no life | boss path: `H*100 + L` without replacement or equal-digit award |
| time sampled at defeat / clear | sampled at the `$0A` **first update** (the update after the release), timer still running | sample once, one update after the release |

Rules:

1. **Release update:** request player state `$20` (sound `$97`), clear the sign pan, restore limits, convert the boss slot, create one `$0A` parameter 0. Do not compute the word here.
2. **Next update:** compute `D2A6` once from the current seconds/minutes and rings with `$041F` semantics (rings subtraction without borrow into H; rings 0 -> `$0989`). Store it as the existing `global.chaosResultsBonus`.
3. **Flag:** `D293` bit 4 only from the state-`$20` handler (position `> cameraX + $120` of the live view; the 348-wide adapter decision stays with the existing viewport code). Not from `chaos_act_complete` shortcuts.
4. **Results (zone < 5 only):** reuse the accepted G1-C/U4 card; run the fixed bonus **first** (`steps * 10` raw by zone), then rings x 10, then the word at 1 raw per step; one pass, one zone increment; retain lives, continues, emeralds and score; reset rings/timer/power-ups as the existing loader does.
5. **EEZ3:** no results, no fixed bonus, no word; the controller writes the flag itself (early clear unless Sonic with `D2CC == $1F`; final bit `$20`) and the accepted ending selector runs. Do not add a `$0A` word or score for the Laser Walker/EEZ boss.
6. **Idempotency guards:** one `$0A` parameter 0 per defeat (the boss token is cleared), one flag, one `$2D55`; a second flag write must not repeat the tally.
7. Out of scope here and unchanged: boss art, sparkle visuals, audio assets (requests logged numerically `$97`), Tails, G1-F natural Special Stage, G1-G endings, parked PRES/GOAL/SEZ3-lift items.

### F5 acceptance plan for G1-E (Windows, human)

1. THZ3 boss defeat -> state `$20` run -> results with a **fixed 500**, rings x 10 and the word; GPZ1 starts at the RQ4 record; score/lives/continues/emeralds retained.
2. GPZ3 (1000), SEZ3 (1500), MGHZ3 (2000; clears almost immediately because the X gate is already met), AQZ3 (2500): each lands on the next zone's act 1.
3. The word equals the model for the on-screen time (< 0:29 -> `H = 9` ... see section 4); rings 0 gives `...89` units; 11 rings at >= 4:59 gives 0.
4. EEZ3: no results card; Sonic with `$1F` collects the final bit and sees the full ending; with `$00` the partial ending; `$3F` early-clears into the full ending; return to the title. (Tails stays G6.)
5. No second tally, no double bonus when the player mashes the button; the developer return path still works.

## 9. Limits and unresolved

* Fights are fixture driven (synthetic placement/attack writes; boss, bonus and results code unmodified). They are not controller-only playthroughs.
* AQZ3 uses the 11-case harness; only the first complete chain is analysed. GPZ's `$03F5` caller is the scheduler because the release ends in `JP $03F5`.
* The two EEZ `$0A` parameter-1 sparkles are SOURCE (script decode) only: the fixtures end state 5 before the 24-update delay. They cannot change `D2A6`.
* `$60` (EEZ mid-boss) lists the shared state-5 script; no fight entered that state (reachability **unverified**).
* The timer tick between the compute update and the poll can differ by one second in rare frames; the word is verified against the inputs captured **at** `$9C93`.
* Sound requests are logged numerically only (`$97`); nothing audible is claimed.

## 10. Reproduction

```
python tools/u2_act3_boss_bonus.py --validate                 # no ROM
python tools/u2_act3_boss_bonus.py "<ROM>" --check             # complete regeneration compare (about 5 minutes, Python >= 3.10)
python tools/u2_act3_boss_bonus.py "<ROM>"                     # rewrite data/u2/*.json
python tools/u2_act3_boss_bonus.py --doc                       # refresh the generated tables of this document
python -m unittest tests.test_u2_act3_boss_bonus
```

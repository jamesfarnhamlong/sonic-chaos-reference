# G0-R - Ordinary campaign ROM contract (Act 1 -> Act 2 -> Act 3 -> next zone, Special Stages, lives, continues, Game Over, end of EEZ)

Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. Base: Research `main`
`0bb7390813a8fa4320ef35253a2c39598eee8e08`. Branch `research/g0-campaign-contract`. Research only: the POC was read, never modified, and no ROM
byte is committed.

Machine-readable outputs (all deterministic, regenerated and compared by `--check`):

| File | Content |
|---|---|
| `data/g0/campaign-contract.json` | RAM map, 18 transitions with per-field effects, rules, outcome table, routine byte hashes, writer census, start-position table, sign-prize tables, boss-bonus table, palette-fade answer, evaluated expectations (each with its source reason), unresolved list |
| `data/g0/campaign-oracle.json` | 35 whole-game observations of the original ROM (fixtures named, state captured at named routine entries) |
| `data/g0/g1-g2-ledger.json` | ordered G1/G2 dependency ledger, FULLGAME-0 reconciliation, static POC observations |
| `tools/g0_rig.py`, `tools/g0_scenarios.py`, `tools/g0_contract.py`, `tools/g0_ledger.py`, `tools/g0_campaign.py`, `tools/g0_doc.py` | oracle session, scenarios, hand-authored contract, ledger, runner/checker, doc renderer |
| `tests/test_g0_campaign.py` | structure/consistency tests (no ROM) + live ROM tests |

## 1. Headline results

1. **There is exactly one place where an act changes**: `$1538` (`D298 += 1`) after `$14AE`, and one place where a zone changes: `$15D6`
   (`D297 += 1`) after `$1543`. A Special Stage return (`$1869`) re-enters the *same* act-clear tail, so it increments the act too - always the
   **next** ordinary act. Nothing else in the ROM stores progress.
2. **Run state** is `zone, act, lives (D299), continues (D2C3), score (D29D-F), emeralds (D2CC), character (D2C8)`. **`D299` is lives and `D2C3`
   is the CONTINUE counter** (bit 7 = "a continue was just used"). `docs/object-18-act-clear.md` labels `D2C3` "lives": that label is wrong
   (G0-R correction; the prize class that adds to `D2C3` is a continue, the class that calls `$03F2 -> $3104` is the life).
3. **New Game** (`$2C17`, `$07CE`, `$3065..$3564`, `$04D4`) is the *only* place (besides power-on) that clears emeralds, rings and score:
   lives 3 / continues 0 for Sonic, lives 5 / continues 3 for Tails. Game Over and the ending leave the old values in RAM until the next New Game.
4. **Score never awards a life.** It awards a **continue**: Sonic every 5,000 raw units, Tails every 3,000 (CONTROLLED sweep of `$262F`).
   Lives come from the 100th ring, the ten-ring monitor wrap, the 1-UP monitor, sign prize class 1 and an equal-digit bonus word; cap 99.
5. **Death** costs one life at the *start* of the sequence (3 lives = 3 attempts), restarts the same act at its ROM start position (no
   checkpoints, 18/18 acts), resets rings/timer/power-ups, keeps score/continues/emeralds. **TIME OVER is 10:00**, not 9:59.
6. **Continue** (last life, continues available): button within the 10-digit, 116-frame-per-digit countdown -> lives 3 (5), **score 0**, continues
   - 1, emeralds kept, *same act*. No button -> Game Over, nothing consumed.
7. **Special Stage return** goes to `(origin zone, origin act + 1)`; failure costs no life and no continue; success adds an emerald bit and a continue.
8. **Act-3 Special Stage alias** (act index 2 -> act index 3) needs the 100th ring *inside an act-index-2 act*; every such act holds at most 83 rings
   (REUSED census), so it is **FORCED-ONLY** (section 6). Not normal behaviour; not to be implemented.
9. **End of EEZ**: act-index-2 clear in zone 5 skips the results screen, sets zone 6 and runs the ending selector: Sonic with `D2CC & $3F == $3F` ->
   full ending, any other Sonic flags (including `$20` alone) -> partial ("TRY AGAIN"), Tails -> its own ending; all return to the title.
10. **Palette fade after the Special Stage tally: YES, proven** (section 9).

## 2. Method and evidence

* Disassembly of the resident routines (`z80dis`), CPU addresses below `$8000` equal file offsets. Each routine region used is hashed in
  `routines` of the contract (SOURCE-TRACED); a writer census of every campaign byte lists the candidate store sites and marks which were read.
* **EMULATED**: `tools/g0_rig.py` is one continuous run of the original ROM in the approximate SMS harness (`tools/sms_frame_harness.py`):
  power-on, title, character select, New Game, ordinary acts, deaths, continue/Game Over, Special Stage detours, ending, back to the title.
  Fixtures are limited to (a) **ARRIVAL** placement before the THZ sign (the `tools/object_18.py` fixture), (b) **RAM** writes of named bytes
  (lives, rings, flags - each scenario lists them) and (c) **PAD** input. Nothing writes code, banks, objects or VDP state.
  The Special Stage success uses the accepted **input-only** replay (`natural-inputs.json`, 2,288 frames); no teleport.
* **CONTROLLED**: `tools/oracle.py` runs the original score adder `$262F` over 100 thousands-crossings for both characters.
* Where the head of a chain was already proven (goal sign, `$19` child, player state `$20`, boss tail) it is REUSED and the scenario fixture starts
  at that proven point; the **tail** (`$14AE` onward) is always unmodified ROM. The 18-act spine uses the real sign chain for THZ1/THZ2, forced player
  state `$20` for THZ3 and the act-clear flag (what the state-`$20` handler sets) for the other 15 acts.
* The harness VDP is approximate: waits counted in frame-wait iterations (`$062D`) are source-exact; CRAM visibility offsets are EMULATED.

Reproduce (Python >= 3.10 with `requirements.txt`; the ROM path or `SONIC_CHAOS_ROM`):

```
python tools/g0_campaign.py "../source/Sonic Chaos (Europe).sms"            # regenerate data/g0/*.json (about 2 min with --jobs 4)
python tools/g0_campaign.py "../source/Sonic Chaos (Europe).sms" --check    # regenerate and compare with the committed files
python tools/g0_campaign.py "../source/Sonic Chaos (Europe).sms" --only new_game_sonic,death_pit_lives3 --print
python tools/g0_campaign.py --validate                                      # no ROM: evaluate every expectation on the committed oracle
python tools/g0_campaign.py "../source/Sonic Chaos (Europe).sms" --from-oracle   # rebuild contract/ledger from the committed oracle (no emulation)
python tools/g0_campaign.py --doc                                           # re-render the generated tables of this document
python -m unittest tests.test_g0_campaign
```

## 3. The natural campaign in one paragraph

Title -> button -> character select -> **New Game** (zone 0, act 0) -> each act: play -> goal sign (acts 1/2) or boss (act 3) -> player state `$20`
-> `D293` bit 5 / bit 4 -> `$14AE`/`$1543`: **198 frames** (60+96+30+12) of fade/clean-up -> results card (`$32F9`) -> tally (rings x10 raw, bonus
word +1 raw per step; act 3 first pays the boss bonus) -> **48 + 96 + 48 frames** with the fade-out -> `act += 1` (or `zone += 1, act = 0`) ->
level reload (rings 0, timer 0, power-ups cleared, ROM start position). The 100th ring in an act index 0/1 inserts a Special Stage whose return
joins the same tail. The final EEZ act replaces the results with the ending selector.

The 18-act spine run (`campaign_spine`) records the (zone, act) sequence, the results screens (17 of 18 clears), the boss bonuses
(500, 1000, 1500, 2000, 2500 raw for zones 0-4), and the first Sonic continue award when the score crosses 5,000 raw.

## 4. Special Stage detours: normal entry and return to the NEXT act

* Gate (`$178F`): `D2C8 == 1` (Sonic), `zone < 6`, `(D2CC & $1F) != $1F`; the **act index is not read**. Otherwise only the life is awarded.
* Selection (`$187B`): stage = 8 + number of consecutive set low bits of `D2CC` (max 4): oracle `ss_select_mask00/01/03/07/0F` -> zones 8,9,10,11,12.
  A failed stage is offered again at the next hundredth ring. After five emeralds (`$1F`) entry is refused for good but the life is still awarded.
* Entry (`$17A2`, `$17B0`): timer stopped, `D294 = $88`, `D2CD = 1`, `D296 = origin zone`; stage timer 59 s counts down.
* Exit: success (`D294` bit 6, emerald bit + continue + `D2CD = $FF`) or failure/timeout/death (bit 5): `$1869` restores the zone, sets `D293` bit 5 ->
  the ordinary act-clear tail: results card (stage card chosen by `D2CD`), tally, the post-tally fade, **`act += 1`**, reload. Rings, timer and
  power-ups do not carry; score gains the tally. In the accepted input-only SS1 route the stage itself earned two ring-wrap lives (04 -> 06) which
  persist after the return.
* "Return to the next ordinary act" therefore means *the next act of the same zone*: act 1 -> act 2, act 2 -> act 3 (index 2). There is no "return to
  the same act".

## 5. Preserved: sixth Emerald and EEZ full vs partial ending

Unchanged from the accepted EEZ research and re-proved by `ending_*`: Sonic with `D2CC & $3F == $3F` -> full ending; `$1F` (five stage emeralds, no
sixth) -> partial; `$20` alone -> partial; Tails -> `$1ACD`. The sixth bit is set by the final-zone `$61` object only when the flags are exactly `$1F`
(REUSED `docs/eez-boss-endgame-audit.md`). The ending does not clear the emerald byte; only the next New Game does (`next_new_game.emeralds == 00`).

## 6. The deferred act-3 Special Stage alias - exact circumstances

All of the following must hold; the first is why ordinary play cannot do it.

1. The ring counter wraps 99 -> 00 (or the ten-ring monitor result is < `$10`) **while `D298 == 2`** (Act 3 of any zone). `D29A` is zeroed at every act
   load and the maximum number of rings obtainable in each act-index-2 act is THZ3 19, GPZ3 19, SEZ3 42, **MGHZ3 83**, AQZ3 14, EEZ3 0 (REUSED
   `docs/special-stages-followup-audit.md` section 5, an upper bound over every ring source). 83 < 100.
2. Sonic, zone < 6, `D2CC & $1F != $1F` (identical to a normal entry; the gate does not look at the act).
3. Result when forced (`ring100_act3_forced`, `special_stage_death_act3_forced`): the stage runs normally; the return performs `D298 := 3`, the loader indexes
   the *next zone's* act-1 record under the old zone number (zone 0 act 3 starts at player (110,384), the GPZ1 start), and the act-3 boss bonus
   (500 raw for zone 0) is paid by the results screen because `$2D55` still sees `D298 == 2`.

So: **no ordinary route; fixtures only** (START_INDEX act 2 + injected 100th ring). This note does not normalise the alias and adds no new claim
about a natural route; the census remains an upper bound that was not re-derived.

## 7. Death, restart, Game Over and continues

Oracle timings (harness frames after the death fixture): a pit death decrements the life at once and the same act reloads about 150 frames later (death
animation, then waits of 60 and 90). On the last life with **no** continue the Game Over screen is up after about 10 frames and the title about 700
frames after the death. With continues available the continue screen runs a 10-digit countdown of 116 frames per digit (1,160 frames after roughly 120
of set-up); a button at +200 consumes the continue (`$1491`, wait 180), then `$1450..$1461` (fade slots, wait 60) and the reload follow 240 frames after the
press. An unanswered countdown ends in the same Game Over path about 1,970 frames after the death, consuming nothing. The player object on the continue
screen is redrawn at fixed coordinates; the zone and act are untouched until the reload.

## 8. What changes on each transition

The per-transition field effects (stage index, rings, timer, score, lives, continues, Emerald flags, result card, power-ups, player identity,
restart position) are in the generated section below. **Checkpoints do not exist** (restart position is a ROM table keyed by zone/act, section
"ROM start positions"). **Save/continue-from-save does not exist in the ROM**: no cartridge RAM (the only `$FFFC` writes are the start-up
mapper writes at `$0008`/`$0466`), no password; "Continue" is only the in-run continue screen.

## 9. Separate question: a fade after the Special Stage tally?

**Yes - proven (source-traced + emulated), and it is the same sequence as an ordinary act clear.** After the stage `$1869` sets `D293` bit 5, the
tail `$14AE`: `$14FC CALL $32F9` (results card **and** the `$2D08` tally) returns; `$14FF` waits 48 frames; `$1507..$1517` request the fade slots `D492/D494`
(`0|bit6|bit4`); `$1519` waits 96 frames; `$1521 CALL $342A` fills the palette buffer `D472..D491` with `$3F`; `$1524 CALL $1CAF` resets the slots; `$1527`
waits 48 frames; only then `$152F` clears bit 5, increments the act and sets the reload flag. The emulated CRAM (`post_tally_fade`) shows, 98-102 frames after
the tally returns, three 5-frame steps up to **full white** (summed brightness 201 -> 252 -> 288), 95-100 frames of white, then three steps down to **black**
(192 -> 96 -> 0) 31-35 frames *before* the act index changes, after which the loader fades the new act in. The results-card fades *before* the card (white flash
and fade-in) are separate and were already known; the POC's "abrupt return" is therefore a POC omission, not ROM behaviour.
Caveats: CRAM is written by the ROM's palette routine but the harness VDP is approximate, and brightness is a sum over the 32 entries (it proves white-then-black,
not each step's exact colours). Status in `campaign-contract.json`: `palette_fade_answer.status = "resolved"`.

## 10. Reconciliation with FULLGAME-0, SS5 and FG1

FULLGAME-0 (`e86b4de`, audited POC SS1) is reclassified item by item in the table below. Highlights: SS2-SS5 are **not** missing (AGENTS: accepted individually);
FG1 `c0c4c97` touches only THZ foreground priority (one wiring line in `SCR_chaos_level`) and no campaign flow; the SS5 tip still has a three-entry
`chaos_acts()` (STATIC-POC SP1), the 1-UP monitor shadow variable (SP2), a continue counter that is only drawn (SP3) and the inherited game-over room (SP5).
FULLGAME-0 questions Q1 (D299/D2C3), Q2 (score life), Q4 (time-over) are **resolved**; Q3 (score display) and Q12 (attract / act cards) are partial.
Classification words follow the Manager legend; STATIC-POC rows are source observations, not Windows acceptance.

## 11. Manager review points before integration into Research main

* **Correction of an accepted document**: `docs/object-18-act-clear.md` calls `D2C3` "lives". This package proves it is the continue counter; the old document is
  left unchanged (annotate or supersede at integration).
* **Limitation (explicit):** the 18-act spine injects the act-clear flag for 15 acts (THZ1/THZ2 use the real sign chain, THZ3 forced player state `$20`). It proves the common progression path and the shared `$14AE`/`$1543` tail, **not** natural play through every sign and boss.
* The oracle uses the accepted input-only SS1 route and the accepted THZ sign fixture; the 15 non-THZ acts raise the act-clear flag directly (flagged in the
  scenario, not a natural boss/sign playthrough).
* `docs/special-stages-progression-audit.md` section 5 says the next act "always"; confirmed - and note the stage can also pay lives in-stage (ring wraps).
* The harness is approximate; frame numbers of CRAM changes are EMULATED. Waits (198/48/96/48/116) are source-exact.

<!-- g0-generated:begin -->

### Run state and flow bytes

| Name | Address | Scope | Role |
|---|---|---|---|
| `menu` | `$D292` | FLOW | title/menu state flags (bit7 start requested, bit6 title active, bit5/4/3 attract and option sub-states); non-zero suppresses the HUD and the level timer |
| `flow` | `$D293` | FLOW | main-loop dispatch flags: bit7 end path $1365, bit6 level frame enabled (0x40 = playing), bit5 act complete $14AE, bit4 zone complete $1543, bit2 life lost $15F2, bit1 level (re)load $1673, bit0 pause $1696 |
| `mode` | `$D294` | FLOW | stage mode: bit7 special stage active, bit6 success $183F, bit5 failure $1815, bit3 entering |
| `started` | `$D295` | FLOW | $FF once a game has been started from the title/character select (or hidden level select); cleared by $2C17 when START is pressed on the title; gates the zone/act reset inside $2A00 |
| `saved_zone` | `$D296` | ACT | zone to restore after a special stage |
| `zone` | `$D297` | RUN | zone: 0 THZ, 1 GPZ, 2 SEZ, 3 MGHZ, 4 AQZ, 5 EEZ, 6 end-of-game, 7 title, 8..12 Special Stages 1..5 |
| `act` | `$D298` | RUN | act index 0..2 (Act 1..3); unguarded +1 at $1538 on every act complete and every special-stage return |
| `lives` | `$D299` | RUN | lives, packed BCD; game over when the post-death value is 0 (the life being played is part of the count) |
| `rings` | `$D29A` | ACT | rings, packed BCD (wraps 99->00 at $3138) |
| `score` | `$D29D` | RUN | score, 3 bytes packed BCD little-endian (D29D units/tens, D29E hundreds/thousands, D29F ten-thousands/hundred-thousands); HUD draws these six digits then a fixed block at name-table $3BA6 (display = raw x 10 is probable, glyph not decoded) |
| `bonus` | `$D2A6` | ACT | end-of-act time/ring bonus word consumed by the tally (+1 raw per step); set by the sign child $19 (0C:$AB52), the boss bonus object type $0A (0C:$9C96) and by the stage success callback ($94BD: seconds left << 8) |
| `continues` | `$D2C3` | RUN | continues in bits 0..6 (mixed binary/BCD increments), bit7 = 'a continue was just used' (cleared by $13ED, set by $1491) |
| `character` | `$D2C8` | RUN | 1 = Sonic, 2 = Tails (the select cursor 0/1 is held here until $30C5 increments it) |
| `emeralds` | `$D2CC` | RUN | Chaos Emerald bits: $01/$02/$04/$08/$10 = Special Stages 1..5, $20 = sixth (EEZ) |
| `result_card` | `$D2CD` | ACT | results card selector: 0 ordinary, 1 stage failure card (also marks 'stage entered'), $FF stage success card; cleared by $33D7 when the card is drawn |
| `timer` | `$D2BE` | ACT | D2BE run flag ($FF running, 0 stopped); D2C2 frame ticks 0..59; D2BF seconds BCD; D2C0 minutes BCD; counts UP in acts (10:00 sets D44B=$C0 and stops), counts DOWN from 59 in a special stage |
| `timeover` | `$D44B` | ACT | $C0 set at 10:00; bit6 makes the player update call the death routine, bit7 makes the life-lost path show the TIME OVER screen |
| `powerup` | `$D532` | ACT | power-up id (player object field +$32) and D44C timer; inside the object RAM block $D300..$DBBF that $297E clears on every level load |
| `continue_screen` | `$D2CA` | FLOW | continue countdown: D2CA frame ticks (0..$73), D2CB digit 9..0 (underflow to $FF ends the screen) |
| `hidden_menus` | `$D2CE` | FLOW | bit0 level select unlocked, bit1 sound test unlocked (title input codes at $0D02 / $0D0B); not a normal-play path |

### Transitions

#### T01 - Power-on / reset to title

Trigger: reset vector. Evidence: REUSED docs/decomp-1d-r2-zone-act-invariants.md. Oracle: `new_game_sonic`.

- **stage index**: zone 7 (title), act 0
- **rings**: 0
- **timer**: 0
- **score**: 0
- **lives**: 0
- **continues**: 0
- **emeralds**: 0
- **result card**: 0
- **powerups**: none
- **player identity**: D2C8 = 0 until character select
- **restart position**: n/a

_All run-scoped bytes are zero after power-on; there is no battery RAM (the only $FFFC stores are the start-up mapper writes at $0008/$0466)._

#### T02 - Title START -> character select -> New Game

Trigger: button 1/2 on the title (START is not read; the harness has no console key). Evidence: SOURCE-TRACED; EMULATED new_game_sonic / new_game_tails with dirty pre-state. Oracle: `new_game_sonic`, `new_game_tails`.

- **stage index**: zone 0, act 0 (from $07CE)
- **rings**: 0 ($2A00)
- **timer**: 0:00, running ($2965..$2973)
- **score**: 0 ($2A04..$2A0A)
- **lives**: 3 Sonic / 5 Tails
- **continues**: 0 Sonic / 3 Tails
- **emeralds**: 0 ($2A1F)
- **result card**: not written (stale $D2CD is consumed by the first results card)
- **powerups**: none
- **player identity**: D2C8 = 1 Sonic / 2 Tails
- **restart position**: start position of THZ1 (T03)

_Emerald flags are cleared here and ONLY here (and by power-on); Game Over, the ending and the title do not clear them._

#### T03 - Level (re)load - first load, next act, next zone, death restart, continue restart

Trigger: D293 bit1 -> $1673. Evidence: SOURCE-TRACED; EMULATED restart_matrix (18 acts). Oracle: `restart_matrix`, `death_pit_lives3`.

- **stage index**: unchanged by the load itself
- **rings**: 0
- **timer**: 00:00 and running; D2C2 ticks are NOT cleared
- **score**: unchanged
- **lives**: unchanged
- **continues**: unchanged
- **emeralds**: unchanged
- **result card**: unchanged
- **powerups**: cleared (object RAM block, includes D532/D44C/D44B)
- **player identity**: player object type rewritten from D2C8
- **restart position**: ROM table (zone, act) only; no checkpoint storage exists

_The start position is read from a ROM table indexed by (D297, D298) at $4E65..$4E94; no store of a mid-level position exists, and all 18 acts restart at the fresh-load position after a death._

#### T04 - Act complete, act index 0 or 1 (sign chain -> next act)

Trigger: goal sign `$18` contact -> $19 child -> player state $20 -> $83A6 sets D293 bit5 (REUSED docs/object-18-act-clear.md); then $14AE. Evidence: REUSED head; SOURCE-TRACED tail; EMULATED clear_thz1_rings00/15/55/09 and campaign_spine. Oracle: `clear_thz1_rings00`, `clear_thz1_rings15`, `clear_thz1_rings55`, `clear_thz1_rings09`, `campaign_spine`.

- **stage index**: act + 1 (zone unchanged)
- **rings**: tally drains to 0; loader zeroes
- **timer**: stopped at contact, reset by the next load
- **score**: +10 raw per ring after the prize, + bonus word (time entry x100 + (rings-$11)) raw
- **lives**: +1 for prize class 1 (rings 55/65/77/88/95/97/99 in THZ-parity zones)
- **continues**: +1 for prize class 3 (rings 15/30/40/60) - a CONTINUE, not a life
- **emeralds**: unchanged
- **result card**: 0 -> ordinary card
- **powerups**: cleared by the reload
- **player identity**: unchanged
- **restart position**: next act's ROM start

_Act and zone are NOT stored in two places: $1538 is the only increment, there is no guard on the act byte._

#### T05 - Zone complete, act index 2, zones 0..4 (boss -> next zone)

Trigger: player state $20 tail (boss defeat chain, REUSED) sets D293 bit4 -> $1543. Evidence: SOURCE-TRACED; EMULATED campaign_spine (flag injected, everything after is ROM). Oracle: `campaign_spine`.

- **stage index**: (zone+1, act 0)
- **rings**: tally drains, loader zeroes
- **timer**: reset by load
- **score**: +boss bonus 500/1000/1500/2000/2500 raw for zones 0..4 + ring/time tally
- **lives**: unchanged
- **continues**: unchanged unless a score threshold is crossed
- **emeralds**: unchanged
- **result card**: 0
- **powerups**: cleared
- **player identity**: unchanged
- **restart position**: next zone act 1 start

_The 6000-raw table entry (index 5) belongs to zone 5 and is never used: zone >= 5 skips the results screen._

#### T06 - Final zone complete (EEZ act index 2) -> ending -> title

Trigger: D293 bit4 at zone 5 -> $1543 -> $1594 skips $32F9 -> $15CE. Evidence: REUSED docs/eez-boss-endgame-audit.md, docs/eez-ending-credits-audit.md; EMULATED ending_sonic_full / ending_sonic_partial / ending_sonic_20_only / ending_tails. Oracle: `ending_sonic_full`, `ending_sonic_partial`, `ending_sonic_20_only`, `ending_tails`.

- **stage index**: zone 6, act 0, then the title (zone 7)
- **rings**: n/a
- **timer**: n/a
- **score**: no results card, no tally
- **lives**: unchanged
- **continues**: unchanged
- **emeralds**: unchanged until the NEXT New Game (T02)
- **result card**: n/a
- **powerups**: n/a
- **player identity**: unchanged
- **restart position**: n/a

_Full vs partial depends only on D2CC & $3F == $3F. The sixth bit ($20) is set by the final-zone $61 object only when flags are exactly $1F (REUSED); a $20-only mask is therefore a partial ending._

#### T07 - Death with lives remaining (hurt-with-no-rings, pit, crush, drown, TIME OVER at 10:00)

Trigger: death routine $4984 (zone < 8) sets D293 bit2 (and $3C0D for the pit rule); time over: $27EE sets D44B := $C0 at 10:00, $362A calls $4984. Evidence: SOURCE-TRACED; EMULATED death_pit_lives3, death_time_over_lives3. Oracle: `death_pit_lives3`, `death_time_over_lives3`.

- **stage index**: unchanged (same act restarts)
- **rings**: 0
- **timer**: reset to 00:00
- **score**: kept
- **lives**: -1
- **continues**: kept
- **emeralds**: kept
- **result card**: unchanged
- **powerups**: cleared
- **player identity**: unchanged
- **restart position**: ROM start of the act

_The life that was being played counts: 3 lives = 3 attempts. Time over is 10:00, not 9:59. A Special Stage death or timeout does NOT use this path (T14)._

#### T08 - Death on the last life, continues available

Trigger: lives reach 0 -> $166B clears D293 bit6 -> main loop $138A. Evidence: SOURCE-TRACED; EMULATED death_continue_accept_sonic / _tails. Oracle: `death_continue_accept_sonic`, `death_continue_accept_tails`.

- **stage index**: unchanged (act restarts)
- **rings**: 0
- **timer**: reset
- **score**: 0
- **lives**: 3 Sonic / 5 Tails
- **continues**: -1, bit7 left set
- **emeralds**: KEPT
- **result card**: unchanged
- **powerups**: cleared
- **player identity**: unchanged
- **restart position**: ROM start of the act

_Continue never returns to Act 1/zone start; it restarts the act in which the last life was lost._

#### T09 - Game Over (no continue, or the continue countdown expires)

Trigger: $13ED returns with no continue taken -> $139D. Evidence: SOURCE-TRACED; EMULATED death_continue_timeout, death_game_over_no_continue. Oracle: `death_continue_timeout`, `death_game_over_no_continue`.

- **stage index**: title (zone 7 after the title init)
- **rings**: stale until New Game
- **timer**: stale
- **score**: stale until New Game
- **lives**: 0 (stale)
- **continues**: stale (an unused continue is NOT consumed by a timed-out screen)
- **emeralds**: stale until New Game
- **result card**: n/a
- **powerups**: n/a
- **player identity**: re-chosen at the next character select
- **restart position**: n/a

_A new game after Game Over starts from T02 with every run-scoped field reset._

#### T10 - Return to title then New Game (dirty state)

Trigger: T06/T09 end in JP $04B4; START again. Evidence: EMULATED new_game_sonic dirty pre-state, death_continue_timeout.then_new_game. Oracle: `new_game_sonic`, `death_continue_timeout`, `death_game_over_no_continue`.

- **stage index**: zone 0 act 0
- **rings**: 0
- **timer**: 0
- **score**: 0
- **lives**: 3/5
- **continues**: 0/3
- **emeralds**: 0
- **result card**: stale
- **powerups**: none
- **player identity**: re-chosen
- **restart position**: THZ1 start

_Run state is reset at New Game, never at the title entry._

#### T11 - Ring 100 (life award) and the Special Stage entry gate

Trigger: $3138 wraps D29A 99 -> 00 (also the ten-ring monitor $4AC0 when the result is < $10). Evidence: SOURCE-TRACED; EMULATED ring100_sonic / ring100_tails / ring100_all_emeralds / ring100_ten_monitor / ring100_lives_cap / oneup_monitor. Oracle: `ring100_sonic`, `ring100_tails`, `ring100_all_emeralds`, `ring100_ten_monitor`, `ring100_lives_cap`, `oneup_monitor`.

- **stage index**: unchanged until T12
- **rings**: wraps to 00 ($3138) or keeps the post-wrap value 05 (monitor)
- **timer**: stopped when a stage is entered
- **score**: unchanged
- **lives**: +1 (cap 99)
- **continues**: unchanged
- **emeralds**: unchanged
- **result card**: 1 when a stage is entered
- **powerups**: unchanged
- **player identity**: Sonic only may enter
- **restart position**: n/a

_The act index is NOT read by the gate (T16)._

#### T12 - Special Stage entry

Trigger: D294 = $88 -> main loop $1762 -> $17B0. Evidence: SOURCE-TRACED; EMULATED ss_select_mask00..0F, special_stage_success. Oracle: `ss_select_mask00`, `ss_select_mask01`, `ss_select_mask03`, `ss_select_mask07`, `ss_select_mask0F`, `special_stage_success`.

- **stage index**: zone 8..12 (stage), saved zone kept in D296; act index unchanged
- **rings**: 0 in the stage
- **timer**: 0:59 countdown
- **score**: unchanged
- **lives**: unchanged (+1 per ring wrap inside the stage)
- **continues**: unchanged
- **emeralds**: unchanged
- **result card**: 1
- **powerups**: cleared by the load
- **player identity**: Sonic
- **restart position**: stage start

_Selection is strictly sequential and uses the CONSECUTIVE low bits of D2CC; a failed stage is offered again._

#### T13 - Special Stage success

Trigger: stage Emerald object (type $31) collected. Evidence: REUSED docs/special-stages-progression-audit.md; EMULATED special_stage_success (input-only route). Oracle: `special_stage_success`.

- **stage index**: -> T15
- **rings**: stage rings are tallied (x10 raw), then zero
- **timer**: seconds left x100 raw bonus
- **score**: +rings x10 + seconds x100 raw
- **lives**: kept (+ any ring-wrap lives earned inside the stage)
- **continues**: +1
- **emeralds**: \| stage bit
- **result card**: $FF -> emerald results card
- **powerups**: cleared
- **player identity**: Sonic
- **restart position**: n/a

_A same-update timeout or death does not undo success (REUSED SS1 contract)._

#### T14 - Special Stage failure (timer underflow or death)

Trigger: $2846 (timer 0 - 1) or the shared death setup $49A0 (zone >= 8) sets D294 bit5 -> $1815. Evidence: REUSED; EMULATED special_stage_timeout / special_stage_death_act2. Oracle: `special_stage_timeout`, `special_stage_death_act2`.

- **stage index**: -> T15
- **rings**: 0
- **timer**: n/a
- **score**: unchanged (stage rings may still be tallied)
- **lives**: NOT decremented
- **continues**: unchanged
- **emeralds**: unchanged (stage offered again at the next 100 rings)
- **result card**: 1 -> failure card
- **powerups**: cleared
- **player identity**: Sonic
- **restart position**: n/a

_No retry, no life cost._

#### T15 - Return from a Special Stage to the NEXT ordinary act

Trigger: $1869. Evidence: SOURCE-TRACED; EMULATED special_stage_success / timeout / death. Oracle: `special_stage_success`, `special_stage_timeout`, `special_stage_death_act2`.

- **stage index**: (origin zone, origin act + 1)
- **rings**: 0
- **timer**: reset
- **score**: + tally
- **lives**: as T13/T14
- **continues**: as T13/T14
- **emeralds**: as T13/T14
- **result card**: 0 after the card
- **powerups**: cleared
- **player identity**: unchanged
- **restart position**: next act ROM start

_Identical code path to T04: the same fades and the same $14AE sequence run (the post-tally fade question, section 'Palette fade' of the narrative)._

#### T16 - FORCED-ONLY: Special Stage entered at act index 2 returns to act index 3 **(FORCED-ONLY)**

Trigger: 100th ring while D298 = 2 (not reachable by ordinary play). Evidence: REUSED docs/special-stages-followup-audit.md section 5 (census: maximum rings in act-index-2 acts THZ3 19, GPZ3 19, SEZ3 42, MGHZ3 83, AQZ3 14, EEZ3 0); EMULATED ring100_act3_forced, special_stage_death_act3_forced. Oracle: `ring100_act3_forced`, `special_stage_death_act3_forced`.

- **stage index**: (zone, act 3): the loader selects the adjacent record, i.e. the NEXT zone's act-1 data under the old zone number
- **rings**: 0
- **timer**: reset
- **score**: + boss bonus of the zone (500 raw for THZ)
- **lives**: as T14
- **continues**: as T14
- **emeralds**: as T14
- **result card**: 0
- **powerups**: cleared
- **player identity**: unchanged
- **restart position**: (110,384) for zone 0 act 3

_Entry needs the ring counter to wrap inside act index 2 (Act 3 of a zone); every act-index-2 act holds at most 83 rings (MGHZ3), so ordinary play cannot enter. A fixture (START_INDEX act 2 + injected 100th ring) can. NOT normal behaviour; do not implement as a campaign path._

#### T17 - Score and continue awards

Trigger: every score addition goes through $262F. Evidence: SOURCE-TRACED; CONTROLLED score_continue_rule. Oracle: `score_continue_rule`, `campaign_spine`.

- **stage index**: n/a
- **rings**: n/a
- **timer**: n/a
- **score**: n/a
- **lives**: NO life is awarded by score
- **continues**: +1 per threshold (binary +1 of a byte whose bit7 is preserved)
- **emeralds**: n/a
- **result card**: n/a
- **powerups**: n/a
- **player identity**: Sonic vs Tails rule
- **restart position**: n/a

_The earlier hypothesis of a score-driven extra LIFE is disproved: the award increments D2C3 (continues)._

#### T18 - Hidden level select / sound test and attract demos (non-campaign)

Trigger: title input codes (D2CE) / idle title (D292 attract sub-states). Evidence: SOURCE-TRACED. Oracle: none (source-traced).

- **stage index**: level select: any of the 18 (zone, act) pairs; attract: demo acts
- **rings**: level select starts with the New Game values
- **timer**: n/a
- **score**: n/a
- **lives**: n/a
- **continues**: n/a
- **emeralds**: n/a
- **result card**: n/a
- **powerups**: n/a
- **player identity**: n/a
- **restart position**: n/a

_These are developer/test fixtures of the ORIGINAL ROM, not part of the natural campaign; START_INDEX in the oracle reproduces the level select's two stores._

### Expected outcomes

| Event | Where | Result | Transition |
|---|---|---|---|
| act clear | act index 0 or 1, any zone | act := act + 1, same zone; results + tally + fades; rings 0, timer reset, powerups cleared; score += tally; lives/continues by sign prize class | T04 |
| act clear | act index 2, zone 0..4 | (zone + 1, act 0); results + boss bonus + tally; score += boss bonus | T05 |
| act clear | act index 2, zone 5 | zone 6 -> ending selector -> title; no results | T06 |
| death | lives after decrement > 0 | same (zone, act) reloads at its ROM start; lives -1, rings 0, timer reset, powerups cleared, score/continues/emeralds kept | T07 |
| death or TIME OVER | lives after decrement == 0 and continues > 0 | continue screen; button -> lives 3 (5), score 0, continues -1, same (zone, act); no button -> Game Over | T08/T09 |
| death or TIME OVER | lives after decrement == 0 and continues == 0 | Game Over screen -> title | T09 |
| 100th ring | Sonic, zone < 6, emeralds != $1F, act index 0 or 1 | life +1, Special Stage n (n = 1 + consecutive set bits), then return to (zone, act + 1) | T11/T12/T15 |
| 100th ring | Tails, or emeralds == $1F | life +1 only | T11 |
| 100th ring | act index 2 | FORCED-ONLY: not reachable (<= 83 rings per such act); a fixture returns to act index 3 and pays the boss bonus | T16 |
| Special Stage success | any | emerald bit, continue +1, tally, return to (zone, act + 1) | T13/T15 |
| Special Stage failure / timeout | any | no emerald, no life cost, tally of stage rings, return to (zone, act + 1) | T14/T15 |
| New Game | from the title | zone 0 act 0, lives 3 (5), continues 0 (3), rings/score/emeralds 0 | T02/T10 |

### ROM start positions (camera and player, from the table at `$4E65`)

| Zone | Act 1 (index 0) | Act 2 (index 1) | Act 3 (index 2) |
|---|---|---|---|
| 0 THZ | player (142,654), camera (38,530) | player (110,398), camera (6,274) | player (110,224), camera (0,112) |
| 1 GPZ | player (110,384), camera (0,272) | player (110,448), camera (0,336) | player (187,352), camera (75,240) |
| 2 SEZ | player (110,718), camera (0,608) | player (110,846), camera (0,742) | player (110,821), camera (0,702) |
| 3 MGHZ | player (78,192), camera (0,80) | player (112,558), camera (0,447) | player (110,160), camera (0,48) |
| 4 AQZ | player (110,206), camera (0,99) | player (110,558), camera (0,447) | player (110,238), camera (0,132) |
| 5 EEZ | player (238,864), camera (126,752) | player (170,430), camera (58,318) | player (110,288), camera (0,176) |

### Palette steps after the tally (harness frames relative to the `$14AE` entry)

| Run | tally returned | first CRAM change | full white | black | act incremented |
|---|---|---|---|---|---|
| `clear_thz1_rings00` | 596 | 694 | 704 | 804 | 835 |
| `special_stage_success` | 1179 | 1277 | 1287 | 1382 | 1417 |
| `special_stage_timeout` | 275 | 377 | 387 | 482 | 515 |

### Ordered G1/G2 dependency ledger

| # | Package | Milestone | Depends on | Status | Contract | Gaps needing new proof |
|---|---|---|---|---|---|---|
| 1 | G1-A Run-state owner and New Game reset | G1 | - | CONFIRMED | T02, T10, RULES.lives, RULES.continues, RULES.emeralds, RAM map | - |
| 2 | G1-B 18-act table, loader parameters and restart rule | G1 | G1-A | CONFIRMED | T03, start_positions, RULES.checkpoints | - |
| 3 | G1-C Act-clear tail: 198-frame wait, results card, tally, fades, next act | G1 | G1-B | CONFIRMED (control flow); GAP (presentation) | T04, T15, palette_fade_answer | U4 (ordinary results card graphics/palettes/text); U5 (sound requests) |
| 4 | G1-D Sign prize and time/ring bonus | G1 | G1-C | CONFIRMED (tables, classes); GAP (art selectors) | T04, sign_prize_tables, RULES.lives, RULES.continues | U3 (odd-zone table exercised only by decode, art selectors $1B..$20) |
| 5 | G1-E Zone rollover, act-3 boss bonus and end-of-game branch | G1 | G1-C | CONFIRMED (flow); GAP (U2 boss bonus object per zone) | T05, T06, act3_boss_bonus_table | U2 |
| 6 | G1-F Special Stage detour integration (entry, selection, return to the NEXT act) | G1 | G1-A, G1-C | CONFIRMED | T11, T12, T13, T14, T15, T16 | - |
| 7 | G1-G Ending selection and return to title | G1 | G1-E, G1-A | CONFIRMED | T06, T10 | - |
| 8 | G2-A Lives owner, awards and cap | G2 | G1-A | CONFIRMED | T07, T11, RULES.lives | - |
| 9 | G2-B Continues owner (awards, display, consumption) | G2 | G2-A | CONFIRMED | T08, T13, T17, RULES.continues | - |
| 10 | G2-C Death, restart and TIME OVER | G2 | G1-B, G2-A | CONFIRMED | T07 | U4 (TIME OVER screen graphics) |
| 11 | G2-D Continue screen and Game Over | G2 | G2-B, G2-C | CONFIRMED (flow, timings); GAP (presentation) | T08, T09 | U4 (screens), U5 (sounds $94, $A0, $87) |
| 12 | G2-E Score owner and HUD | G2 | G1-C | CONFIRMED (units); GAP (display, per-object awards) | T17, RULES.score | U1 (display factor); U7 (per-object awards) |
| 13 | G2-F Save / password | G2 | - | CONFIRMED ABSENT | RULES.saving | - |
| 14 | G6-pre Tails differences needed before Tails can enter the campaign | G6 (not G1/G2) | G1-A | GAP | RULES.player_identity | U6 |

### Unresolved items

| Id | Item | State | Blocks |
|---|---|---|---|
| U1 | Display factor of the HUD score and the card text ('RING n x 100') | partial: the HUD draws six BCD digits plus a fixed block at name-table $3BA6; whether it is a literal '0' glyph (x10 display) is not decoded | G2 score display only |
| U2 | Which boss objects allocate the bonus object type $0A (0C:$9C58..$9C96, which calls $041F) in each zone's act 3 | evidenced for AQZ3 $59 and EEZ $61 in earlier audits; THZ3/GPZ3/SEZ3/MGHZ3 not traced here; the spine injects the flag so it contains no boss time bonus | exact act-3 score for natural boss play |
| U3 | Sign prize table for zones with odd parity (table $A962) semantics beyond the class mapping, and the $A8FA retouch re-roll for every zone | decoded in docs/object-18-act-clear.md for the THZ table; the oracle exercises only zone 0 | G2 sign prize completeness |
| U4 | Presentation of the ordinary results card, continue screen, Game Over screen, TIME OVER screen and the act-clear fades (tile data, palettes, text) | control flow and timings traced; graphics not extracted (card tilemaps at $A58C/$A60C, $3436/$345B/$3478/$3495 draw routines) | G1/G2 presentation |
| U5 | Sound request meanings ($87 Game Over, $94 continue, $A0 accept, $89/$97 clear, $A9 life, $B4 tally step, $8A stage) | request numbers observed; names/assets unresolved (AUDIO-0) | audio only |
| U6 | Tails-specific campaign differences beyond lives/continues start, the score-continue rule and the ending branch | unresearched (movement, signs, bosses, art) | G6 |
| U7 | Whether any enemy/monitor/boss score table awards use a path other than $262F | all adds found go through $262F (JP at 1:$5F81 and CALL $2F0C); award values per object type not enumerated | G2 score parity |
| U8 | Timing equality between the harness frame counter and the real console for the 198/96/48-frame waits | waits are counted loop iterations of the frame wait $062D; the harness is approximate for VDP timing only | none |

### FULLGAME-0 reconciliation

| Feature | FULLGAME-0 (POC SS1) | G0 | Basis | Note |
|---|---|---|---|---|
| CAMP-01 | PARTIAL | PARTIAL | ROM contract T02 defines New Game; POC title/slots still inherited (STATIC-POC) | New Game vs Continue: the ROM has no save, so 'Continue' means the in-run continue screen (T08) |
| CAMP-02 | MISSING | MISSING | STATIC-POC SP1 at a13c4c9 | contract supplies the 18-act order and start-position table (G1-B) |
| CAMP-03 | ACCEPTED | ACCEPTED | REUSED object-18 head; AGENTS | sign chain unchanged |
| CAMP-04 | MISSING | MISSING | STATIC-POC SP1/SP5; ROM tail T04 fully timed | post-clear sequence is specified to the frame (198/…/96/48) incl. the post-tally fade |
| CAMP-05 | PARTIAL | PARTIAL | ROM T04/T05/T06 | zone rollover rule and boss bonus table now stated |
| CAMP-06 | PARTIAL | PARTIAL | ROM: type $0A + $2D55 table; STATIC-POC formula ring*10+steps+500 not ROM-derived | ROM boss bonus = bonus word ($041F) tally + 500/1000/1500/2000/2500 raw; per-zone allocator of $0A is gap U2 |
| CAMP-07 | ACCEPTED | ACCEPTED | AGENTS (SS1 accepted) | unchanged |
| CAMP-08 | UNRESOLVED | SUPERSEDED | AGENTS: SS2-SS5 Windows-accepted individually | do NOT classify SS2-SS5 as missing; natural end-to-end SS routing is not yet campaign-accepted; selection table verified in the oracle (ss_select_mask*) |
| CAMP-09 | PARTIAL | PARTIAL | ROM RAM map | D2CC = emeralds, D2C3 = continues (bit7 used flag); both run-scoped; clarifies Q1 |
| CAMP-10 | ACCEPTED | ACCEPTED | oracle ending_* | selector is exactly D2CC & $3F == $3F for Sonic; $20 alone is partial |
| CAMP-11 | MISSING | MISSING | STATIC-POC SP3; ROM T02/T10 | ROM clears emeralds/rings/score only at New Game; POC lazily-created globals are never cleared |
| CAMP-12 | PARTIAL | PARTIAL | oracle fixtures | developer START_INDEX == the hidden level select's two stores; the act-3 alias is FORCED-ONLY |
| LIFE-01 | PARTIAL | PARTIAL | ROM rules.lives | RESOLVED in ROM: start 3 (Sonic)/5 (Tails), BCD, cap 99; POC owner unchanged |
| LIFE-02 | ACCEPTED | ACCEPTED | oracle ring100_* | ROM also awards +1 per ring wrap inside a Special Stage |
| LIFE-03 | PARTIAL | PARTIAL | STATIC-POC SP2 unchanged at SS5; ROM T11 | ROM: monitor parameter bit1 -> $3104 (+1 life, sound $A9) |
| LIFE-04 | MISSING | MISSING | ROM T04 prize tables | CORRECTION: class 3 is a CONTINUE (D2C3), class 1 a LIFE; docs/object-18-act-clear.md mislabels D2C3 as lives |
| LIFE-05 | IMPLEMENTED_UNVERIFIED | IMPLEMENTED_UNVERIFIED | ROM RULES.score | units defined; per-object awards (U7) and display factor (U1) open |
| LIFE-06 | UNRESOLVED | RESOLVED | CONTROLLED score_continue_rule | score thresholds award CONTINUES, never lives |
| LIFE-07 | IMPLEMENTED_UNVERIFIED | IMPLEMENTED_UNVERIFIED | ROM T07 | reset set defined (lives-1, rings 0, timer 0, power-ups cleared; score/emeralds/continues kept); 3 lives = 3 attempts |
| LIFE-08 | PARTIAL | PARTIAL | ROM T09 | flow and waits traced; graphics and $87 unresolved (U4/U5) |
| LIFE-09 | MISSING | MISSING | ROM T08; STATIC-POC SP3 | semantics fully specified (consume on accept, 116 frames/digit, lives 3/5, score 0, emeralds kept, same act) |
| LIFE-10 | UNRESOLVED | RESOLVED | oracle death_time_over_lives3 | ROM time over is 10:00 (not 9:59) and shows a TIME OVER screen; the inherited 9:59 kill is wrong |
| TAIL-03 | PARTIAL | PARTIAL | ROM RULES.player_identity | adds Tails lives 5 / continues 3, digit-sum continue rule, no Special Stages, own ending |
| SAVE-01 | PARTIAL | PARTIAL | ROM RULES.saving | ROM has no save; any slot save is a PC feature (G7) |
| PRES-03 | MISSING | MISSING | ROM T02 | character select screen exists in ROM ($3065..$30E0, $3522..$356A); graphics not extracted (RES-R5) |
| PRES-04 | MISSING | MISSING | not examined | act title cards: not found in the G0 traces (the loader goes straight to play after a fade-in); still UNRESOLVED for RES-R5 |

| Question | FULLGAME-0 | G0 | Answer |
|---|---|---|---|
| Q1 | ROM starting lives / which of D299 and D2C3 is lives | RESOLVED | D299 = lives (3 Sonic / 5 Tails), D2C3 = continues (0 / 3); object-18-act-clear.md's 'lives' label for D2C3 is wrong |
| Q2 | score-threshold extra life | RESOLVED | no life; a continue: Sonic every 5,000 raw (thousands digit becomes 0/5), Tails by a digit rule |
| Q3 | score display scale | PARTIAL | HUD draws six BCD digits plus one fixed block at $3BA6 (probable x10); glyph not decoded (U1) |
| Q4 | ROM time-over rule | RESOLVED | 10:00 (D44B := $C0), death + TIME OVER screen |
| Q12 | attract/demo mode or act title cards | PARTIAL | attract demos exist ($2BC3/$2C34 rotate three demos); no act title card was observed in the load path (U4/RES-R5) |

### Static POC observations (read-only, accepted SS5 `a13c4c9`)

| Id | File | Lines | Finding |
|---|---|---|---|
| SP1 | `scripts/SCR_chaos_level/SCR_chaos_level.gml` | 414-420 | chaos_acts() still lists exactly THZ1, THZ2, THZ3 at SS5 (the SS milestones did not add the campaign table) |
| SP2 | `scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml` | 478-479 | type $10 parameter 2 (1-UP monitor) still only increments the shadow global.chaosType10D299 (never read); no life is awarded |
| SP3 | `scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml` | 34-35,126,176,280 | chaosContinues and chaosCollectedFlags are created lazily if absent, incremented by stage success and only DRAWN on the results card; nothing consumes a continue and New Game does not clear them |
| SP4 | `scripts/SCR_chaos_level/SCR_chaos_level.gml` | 121 | the EEZ boss reads chaosCollectedFlags lazily; the sixth bit is OR-ed at scripts/SCR_chaos_eez_boss line 258 |
| SP5 | `objects/OBJ_player_death/Alarm_1.gml` | 9 | death with no lives goes to the inherited ROM_menu_game_over room (legacy sprite), not the ROM Game Over/continue flow |
| SP6 | `scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml` | 342-355 | chaos_ss_return_valid() fallback is a POC guard for invalid developer origins (records chaosSSReturnFault, saves nothing); it is not ROM behaviour |
| SP7 | `FG1 c0c4c97` | - | FG1 changes THZ foreground priority only (one wiring line in SCR_chaos_level); it does not touch campaign flow, lives, continues or progression |

<!-- g0-generated:end -->

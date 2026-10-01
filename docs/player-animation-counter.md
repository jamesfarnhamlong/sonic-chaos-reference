# Player animation counter `+$07` (shadow model for the terrain-ring probe)

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`
(verified; never committed). `SonicChaos_POC` was not touched.
Machine-readable facts: `data/rom-cache/player-animation-counter.json`. Tool: `tools/player_animation_counter.py`.
Tests: `tests/test_player_animation_counter.py`. Builds on `docs/terrain-ring-collection.md` (the probe reads bit 0 of this counter).

Evidence classes: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY**, **SOURCE-TRACED BEHAVIOR**, **CONTROLLED ROUTINE RESULT** (original Z80 routines
on `tools/oracle.py`), **EMULATED ORIGINAL FRAME** (whole game in `tools/sms_frame_harness.py`), **UNRESOLVED**.

## 1. Answer

**Yes.** The POC can reproduce the terrain-ring parity faithfully **without** reproducing GameMaker-visible animation frame scheduling. It needs a shadow of the
engine's *timing* only: the counter, the current state, a position inside the state's record program (for multi-record states) and one loop counter. The animation
**frames** are irrelevant: frame indices (`+$06`, `$D52F`, `+$24`, `$D36C`) never influence `+$07` (verified by the differential fixtures, which do not model them).

Result of the differential tests of the shadow model against the original engine `$64FA` and `$753E`: **64,000 random-walk updates, 608 selector combinations, 451
scripted transition updates, 5,634 updates of real play (5,480 terrain probes) - 0 mismatches**; the ROM-backed tests add 25,000+ updates with new seeds and
8,192 selector cases covering every speed byte `0..255`.

## 2. Every site that touches the player's `+$07`

BYTE-VERIFIED (byte scan of the whole ROM for IX/IY/absolute forms, then classification):

| Site | Role |
|---|---|
| `$6510` `DEC (IX+7)` | the only decrement: every engine update that does not reload |
| `$6549` | record load: `+$07 := duration byte` of the record |
| `$68AB` | `FF 0D` record: `+$07 := C` (not used by any player script) |
| `$8F28` | selector `$8EE1` (walk): `+$07 := table $8F2C[|X speed hi|]` |
| `$8F40` | selector `$8EE1` side-contact branch: `+$07 := 2` |
| `$8F71` | selector `$8F45` (run): `+$07 := 4` |
| `$8FB4` | selector `$8F76` floor branch: `+$07 := table $8FE0[|X speed hi|]` |
| `$9007` | selector `$8F76` air branch: `+$07 := 3` |
| `$915E` | selector `$9138` (state `$17`): `+$07 := 3` |
| `$9038` (`$9067` for `$903D`) | selector `$900B` (state `$1D`): `+$07 := 6` |
| `$7544` | **read**: terrain probe `$753E` (one more reader: bank-`$0C` `$A26E`, an object) |

Nothing else writes it: **no IY form, no absolute `$D507` access, no block copy**. Other `(IX+7)` writes in the ROM (camera loader, enemy conversion, other
objects, a second-character selector set `$8CB4/$8D05`) are not reachable with IX = the player in THZ play. The slot is zero at start with the script pointer zero.

## 3. Exact update order (BYTE-VERIFIED + EMULATED)

```text
$361D  IX = $D500
$64FA  animation engine  (a) script pointer (+$0E/$0F) zero          -> load the CURRENT state's script (+$01), ignoring +$02 this update
                         (b) +$02 != +$01 and +$03 bit 3 clear       -> +$01 := +$02, reload the script
                         (c) otherwise DEC +$07; at zero             -> next record
       record: +$07 := duration.  FF 05: a selector routine writes +$07.  FF 00 / FF 03 / FF 07 / FF 08 / FF 0F re-enter the record loop in the SAME update.
$5E91  state callback (may write +$02: a request)
       $3FEF: clamp $4141, X integrate $402A, Y integrate $4097, $690B (floor, sides, ceiling, TERRAIN PROBE $753E, merge $64CB)
$4A74
```

Consequences: (1) the probe of update *n* sees the `+$07` produced by the engine of update *n*, **after** any state switch of that update; (2) a state requested by the
callback of update *n* is switched in at the **start of update n+1**, and that update's probe already sees the new state's first value; (3) selector inputs are read
at the **start** of the update, i.e. what the previous update's movement and contact merge left in `$D517`, `+$22`, `+$23`.

## 4. The shadow model (minimal faithful model)

State: `cur` (+$01), `t` (+$07), `ptr` (script position, +$0E/$0F), `loop` (+$33). Inputs at the start of each update: `req` (+$02), `hi` = the signed high byte of the X
speed (`$D517`), `floor` = `+$22` bit 1, `side` = `+$23 & $0C` non-zero, `d448` = `$D448` bit 0 (state `$0B` only; **irrelevant to the parity**, section 10).

```text
update(req, hi, floor, side, d448):
    if ptr == 0:               ptr = script[cur];            next_record()      # first update only
    elif req != cur:           cur = req; ptr = script[cur]; next_record()      # replaces the counter immediately
    else:                      t = (t - 1) & 255; if t == 0: next_record()
    return t                   # +$07 seen by this update's probe;  bit 0 -> probe Y = anchorY - 8 (even) / anchorY + 2 (odd)

next_record():   loop over the script from ptr:
    plain record  (duration, frame, callback):      t = duration; ptr += 4; return
    FF 00 restart:    if cur != req: cur = req;  ptr = script[cur]
    FF 03 s:          req = s                       # then continue (FF 00 follows and switches in the same update)
    FF 05 sel cb:     t = selector(sel); ptr += 6; return
    FF 07 a:          ptr = a
    FF 08 cond alt:   ptr = alt if carry(cond) else ptr + 6        # state $0B: carry = $D448 bit 0;  state $04: carry (THZ)
    FF 0E n:          loop = n
    FF 0F a:          loop -= 1; ptr = ptr + 4 if loop == 0 else a
    FF 01 / 02 / 04 / 06 / 09 / 0A / 0B / 0C:  no effect on the counter (FF 01 $038F also does req += 1, state-0 init)
```

Selectors (`DECODED` tables `$8F2C`, `$8FE0`; `a = |hi|`, 128 stays 128; indices >= 16 read past the table, as the original does):

| Selector | States | `+$07` |
|---|---|---|
| `$8EE1` | `$05` walk | `side ? 2 : $8F2C[a]` = **10, 8, 6, 4, 4, ...** for `a` = 0, 1, 2, >= 3 |
| `$8F45` | `$06` run | **4** |
| `$8F76` | `$09` roll, `$0A` jump, `$10`, `$1B` ramp launch | `floor ? $8FE0[a] : 3` = floor **10, 8, 6, 5, 4, 3, 2, 2, ...** for `a` = 0..5, >= 6; air **3** |
| `$9138` | `$17` | **3** |
| `$900B` | `$1D` | **6** |

The two selector results are loaded **only when the counter reloads**. A changed speed or contact flag does not replace a running counter: the old counter finishes
first (fixtures: walk speed 0 -> 6 at update 4 gives `10,9,...,1` then `4,3,2,1`; side contact for updates 3..6 gives `4,3,2,1,2,1,2,1,4,...`: the 2 appears only at the reloads).
A **state change** does replace it immediately, even between two states that share a selector (e.g. `$09` -> `$0A`).

## 5. Ring-eligible states: schedules

Eligible = observed to run `$753E` when held (`dynamic_eligibility`, 26 states). The static list in `terrain-ring-collection.json` also named `$21` and `$34`; they do **not**
probe (over-approximation) and are excluded here and corrected in `docs/terrain-ring-collection.md`.

Durations loaded by successive reloads (the counter then counts `d, d-1, ..., 1` for each load; run-length encoded as `d x n`):

| State | Loaded durations | Depends on inputs |
|---|---|---|
| `$00`, `$01` standing | 180, then `FF 03 02` + `FF 00` switch to state `$02` in the same update | no |
| `$02` | 64, 16 x 40 (loop `FF 0E 14`, two 16-records per pass), 64, 16 x 18 ... | no |
| `$03` | 6 forever | no |
| `$04` | 224 forever (the `FF 08` carries in THZ) | no |
| `$05` walk | selector `$8EE1` | **`hi`, `side`** |
| `$06` run | 4 forever | no |
| `$07`, `$08` | 8, 224, 8, 224, ... | no |
| `$09` roll, `$0A` jump, `$10`, `$1B` | selector `$8F76` | **`hi`, `floor`** |
| `$0B` spring ascent | 4 x 14 (two passes of six records + two more), 6 x 3, 8, repeat; if `$D448` bit 0: 4 forever (the `$8189` fragment) | values only (`d448`); **parity: no** |
| `$0E` fall | 8 forever | no |
| `$0F` | 2 | no |
| `$11` | 8, 4, 8, 4, ... | no |
| `$12`, `$14`, `$19` | 4 | no |
| `$15` | 6 x 4, 5 x 4, 4 x 4, 3 x 8, 2 x ... (loop `FF 0E D2`, then forever) | no |
| `$17` | selector `$9138` = 3 | no |
| `$1A` | 2 | no |
| `$1C` | 8 | no |
| `$1D` | selector `$900B` = 6 | no |
| `$1E` hurt | 1, 2, 4, 1, 2, 4, ... | no |

(complete op listings and the first 40 values per input set: `schedules` in the JSON). Only **six** states have input-dependent counter *values*: `$05`, `$09`, `$0A`, `$10`, `$1B`, `$0B`. Only **four** have input-dependent *parity* (bit 0): `$09`, `$0A`, `$10`, `$1B`, because the floor table `$8FE0` and the air constant contain odd durations (5, 3); in `$05` and `$0B` every duration is even (10/8/6/4/2 and 4/6/8), so their bit 0 is the plain alternation 0,1,0,1,... from state entry whatever the speed, side contact or `$D448` (`parity_is_pure_alternation_from_entry_for_all_inputs` in the JSON also holds for 17 more states).
Every other eligible state is a fixed schedule; its parity at update *k* after entry is a constant sequence.

Typical parities: standing/idle (180 ... ) alternates; walk `10..1`/`8..1`/`6..1`/`4..1`; run `4..1`; jump (air) `3,2,1` (bit set 2/3 of updates); roll on the floor at
speed 6 `2,1`; fall `8..1`. The earlier 68 % figure for rolling/jumping in `docs/terrain-ring-collection.md` came from the airborne constant 3; on the floor the selector
table is used.

## 6. Transitions in ordinary play (CONTROLLED, original engine + original `$753E`)

| Transition | Counter behaviour |
|---|---|
| stand -> walk | reload at once: `176 -> 8` (speed hi 1) |
| walk -> run | reload at once: run selector 4 |
| run -> jump (air) | reload at once: 3,2,1,3,2,1 |
| jump -> fall | reload at once: 8,7,...,1 |
| fall -> land (-> run/stand) | reload at once: run 4,3,2,1 / stand 180 |
| run -> roll (floor, hi 6) | reload at once: 2,1,2,1 (floor table) |
| roll in air -> floor | stays on 3,2,1 until the next reload, then the floor table (4,3,2,1 at hi 4) |
| roll -> stand | reload at once: 180 |
| spring ascent -> fall | reload at once: 8 |
| any state change every update | the counter is reloaded every update |
| same state re-requested | no effect (counter keeps decrementing) |

One persistent counter plus the reload rules of section 4 is **sufficient** for every ordinary transition: the only extra state is the position inside the multi-record
programs (`$00/$01/$02/$07/$08/$0B/$11/$15/$1E`) and the loop counter used by `$02`, `$0B`, `$15`. Single-record and selector states need no position.

## 7. Direct writes

The only commands that set `+$07` directly in eligible states are `FF 05` (selector calls) and ordinary records; no other command, callback, collision or state setter writes it.
`+$03` bit 3 would make the engine ignore state requests (it keeps decrementing); no recovered code sets it (UNRESOLVED, modelled from the engine source).

## 8. Fixtures (the POC oracle)

`transition_fixtures.scenarios` in the JSON: 11 scripted scenarios (451 updates) with, per update, state, requested state, X speed hi, floor/side inputs, counter before and after,
bit 0, the selected record/selector address, the script pointer, and the **probe Y offset actually produced by the original `$753E`** (`-8` for even, `+2` for odd, all rows).
`selector_sweep` (608 cases), `differential_fixture` (64,000 random updates), `direct_write_fixtures` and `emulated_play` complete the oracle.

## 9. Unresolved

* `+$03` bit 3 behaviour in real play (never set); the `FF 08` condition of state `$04` away from THZ (zone 4); `$D448` beyond bit 0 (section 10).
* `FF 01` call targets were checked only for their effect on the counter, not decoded.
* The alternate path `$16EF` and scripted sequences that call the player update (`$14xx` act-clear/results) were not examined for counter side effects.
* Other-character selectors (`$8CB4`, `$8D05`) are not part of THZ play and are not modelled.

## 10. State `$0B` and `$D448` bit 0 (focused audit)

**Answer to the practical question: no. `$D448` bit 0 can never affect terrain-ring collection in THZ1, THZ2 or anywhere else.** A fixed `$D448 = 0` in the POC is sufficient for the
parity (bit 0 of `+$07`); it only changes the counter *values* after update 56 of a state `$0B` run.

**Code path (BYTE-VERIFIED).** The state `$0B` script starts at `$814A` with `FF 08 [$818F, $8189]`, then `FF 0E 02`, six records of duration 4 (`$8153..$816B`, `FF 0F` loops once),
then records 4, 4, 6, 6, 6, 8 (`$816F..$8183`) and `FF 00` at `$8187`. The op listing of the script ends at `$8187`; the branch target `$8189` is a separate fragment, now listed under
`fragment_at_target` of the `FF 08` op: **record (duration 4, frame `$61`, callback `$039E`), then `FF 00`**. Routine `$818F` is `LD A,($D448); RRCA; RET`.

* **When read:** only when the script executes `FF 08`, i.e. at state entry and each time the script restarts (`FF 00`): after the normal path's last record (82 updates) or after the
  `$8189` record (4 updates). It is **not** re-read in between; changing `$D448` mid-flight does nothing until the next restart.
* **Bit 0 set:** every restart jumps to `$8189`: one record of 4, then `FF 00`, `FF 08` again: **4 on every reload** ("4 forever"). The normal sequence is bypassed entirely
  (there is no selector in state `$0B`; it is a plain record script).
* **Bit 0 clear:** normal sequence 4 x 14, 6 x 3, 8 (82 updates), then `FF 08` again.
* **Parity:** every duration on every path is even (4, 6, 8; verified from the ROM), so the counter always runs `d..1` with `d` even and bit 0 is 0,1,0,1,... continuously across
  reloads. The two paths load different even durations but produce the **same bit-0 sequence from the first update to the last**; the counter *values* first differ at update 56 (0-based)
  of a run (6 instead of 4). Controlled fixture (`state_0b_fixture`): 200 updates for `$D448` clear and set against the original engine, identical parity; 300 episodes x 200 updates with
  `$D448` randomly set to `$00/$01/$FF/$FE/$55` before every update: **0 parity mismatches** (60,000 updates).

**Writers (BYTE-VERIFIED, all six stores of `$D448`).** The address bytes occur exactly seven times in the ROM: the reader and six stores; no IX/IY+`$48` form, no register load, no block copy.
It is zeroed only by the boot/reset RAM clears (`$0029`, `$0462`), **not** at level load, and persists across acts.

| Store | Source | Value | Launch |
|---|---|---|---|
| `$6A87` | terrain upright spring (surface type 9, handler `$6A75`) | `$FF` | Y `$F880`, `$480C` -> state `$0B` |
| `$6AC8` | terrain diagonal spring (type `$14`, `$6A90`) | `0` | `$482D` -> state `$1C` (never `$0B`) |
| `$B2CC` | type `$21` top contact (bank `$0C`) | `$FF` | Y `$F940`, `$035F` -> `$480C` -> `$0B` |
| `$82F8` / `$8420` | type `$26` spring contact / span spring (bank `$1E`) | parameter 0: `$FF` (Y `$F8A0`); nonzero: `0` (Y `$FB00`) | `$035F` -> `$480C` -> `$0B` |
| `$99CA` | type `$50` attack contact | `0` | Y `$FC00`, `$035F` -> `$480C` -> `$0B` |

`$480C` is the only code that requests player state `$0B` (`$4811`), and its only callers are `$5F21` (inside vector `$035F`) and `$6A8D` (terrain): **every** upright launch writes `$D448`
immediately before launching. So bit 0 marks the kind of the last upright launch: strong (parameter-0 springs, terrain upright springs, `$21` stomps) = set; weak springs (parameter != 0)
and the boss bounce = clear.

**THZ cases (CONTROLLED + EMULATED).** THZ1 springs: `(688,864)` and `(3568,768)` parameter 0 -> `$D448 = $FF`; `(1296,608)` `$8A` and `(1912,864)` `$01` -> 0. THZ2: eight parameter-0 springs
-> `$FF`; `(1504,896)` `$88` and `(3472,288)` `$01` -> 0. Emulated launches (six springs, `emulated_springs`): strong springs keep Sonic in state `$0B` for **79 updates** (`$D448 = $FF`: counters
4,3,2,1 repeating), weak springs for 29-54 updates (`$D448 = 0`; shorter than 56, so the two paths coincide even in value). In every row the model equals the engine's counter for the observed
`$D448`, and the model's parity is identical for both `$D448` values.

Consequences for the POC: bit 0 of `+$07` in state `$0B` is `update_index % 2` counting from the update in which the state is entered (first value 4, even). `$D448` need not be modelled for
ring collection. Only the counter *values* of a strong spring ascent differ (6-records appear after update 56 if `$D448` is kept 0); nothing else reads the player's `+$07`.

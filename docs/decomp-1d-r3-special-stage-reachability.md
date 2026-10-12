# DECOMP-1D-R3 - Special-Stage Completion and Invalid-Record Reachability

Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Base commit `fcdfb58861787e242cf3732e301ddd3a25cb79f8` (DECOMP-1D-R2 on `main`; `origin/main` had not advanced).

Evidence: `data/decomp1d/r3-special-stage-reachability.json` (generated, deterministic).
Generator: `tools/decomp1d_r3_special_stage.py`. Tests: `tests/test_decomp1d_r3.py`.

This milestone answers two bounded questions DECOMP-1D-R2 left open, **U1** (can the zone-complete flag be raised while a special stage runs?)
and **U3** (what happens when the stage start selects data outside the verified set, and can the stage be left?). It promotes no banked
assembly, leaves the ledger and recovery manifest untouched and edits no earlier evidence. Everything below is derived from the canonical ROM;
the POC is not used as evidence.

## 1. Executive summary

<!-- r3-generated:begin -->

| Question | Verdict |
|---|---|
| U1 - zone completion inside a special stage | **PARTIAL** |
| U3 - out-of-domain record: overall | **PARTIAL** |

U3 verdicts for the 1192 out-of-domain special-stage rows (zones 8-12 x acts 0-255; 88 in-domain rows are not verdict rows):

| Zone | PROVEN RETURNABLE | PROVEN BLOCKED | PARTIAL | UNPROVEN |
|---|---:|---:|---:|---:|
| 8 | 3 | 0 | 218 | 15 |
| 9 | 0 | 0 | 220 | 16 |
| 10 | 1 | 0 | 222 | 19 |
| 11 | 2 | 0 | 216 | 18 |
| 12 | 2 | 0 | 221 | 19 |

Static record class by what the controlled run did (accelerated timer; all 1,280 rows, in-domain included):

| Record class | returned | stalled, interrupts disabled | executed RAM | restarted at the title | other |
|---|---:|---:|---:|---:|---:|
| verified record | 39 | 49 | 0 | 0 | 0 |
| slot 2 | 16 | 241 | 13 | 2 | 2 |
| bank 0 | 15 | 483 | 50 | 15 | 1 |
| RAM | 41 | 228 | 18 | 7 | 0 |
| slot 1 | 1 | 53 | 5 | 0 | 1 |

Natural 59-second timer versus the accelerated one: 114 rows run both ways, 15 differ (a PROVEN RETURNABLE verdict needs both runs to return): (8, 232), (9, 9), (9, 232), (9, 239), (10, 229), (10, 236), (10, 254), (11, 8), (11, 233), (11, 234), (11, 248), (12, 5), (12, 230), (12, 231), (12, 245).

| Setter | Physical offset | Bank / CPU | Reached by (type, state) |
|---|---|---|---|
| `SET 4,(HL)` | `$303ED` | $0C / `$83ED` | $01 st 32; $02 st 32 |
| `LD (0xd293),A` | `$7BB2A` | $1E / `$BB2A` | $61 st 5 |
| `LD (0xd293),A` | `$7BB6E` | $1E / `$BB6E` | $61 st 7 |

First out-of-domain act per special-stage zone, by table:

| Table | zone 8 | zone 9 | zone 10 | zone 11 | zone 12 |
|---|---:|---:|---:|---:|---:|
| loader record ($2A4F) | 9 | 9 | 6 | 9 | 6 |
| object list ($8000, bank $1C) | 15 | 12 | 9 | 6 | 3 |
| level header ($4FDC) | 15 | 12 | 9 | 6 | 3 |
| zone music ($18A0) | 15 | 12 | 9 | 6 | 3 |
| graphics rows ($78E1) | 18 | 15 | 12 | 9 | 6 |

* U1 route - player state $20 -> $303ED, natural special-stage objects (acts inside the verified list set): **excluded_so_far** (no trigger type in the resolved closure; 0 unresolved creation edge(s) and 4 open computed jump(s) ($314F4, $6972, $6C98, $77EC) are not excluded)
* U1 route - type $61 -> $7BB2A / $7BB6E, natural special-stage objects: **excluded_so_far** (no trigger type in the resolved closure; 0 unresolved creation edge(s) and 4 open computed jump(s) ($314F4, $6972, $6C98, $77EC) are not excluded)
* U1 route - out-of-domain placement lists (acts beyond the verified list set): **present** (986 of 1190 out-of-domain list rows name at least one trigger type; creation (camera window, spawn-map cell) and the boss fight were not evaluated)

<!-- r3-generated:end -->

* **U1 is PARTIAL.** The three writers of `$D293` bit 4 are re-derived and placed (section 2.1). `$303ED` is the act >= 2 branch of the player's state-`$20` callback (bank 12);
  that state is entered only through the level-clear routine `$4892`, whose three callers are boss and goal object types. `$7BB2A` and `$7BB6E` are callbacks of object type `$61` (bank `$1E`).
  The object types a special stage places (`$10 $26 $2F $31`), the two player types and the per-frame code cannot create any of those types **except through four computed jumps the model leaves open**
  (`$314F4 $6972 $6C98 $77EC`). The stage-mode dispatcher *does* honour bit 4 and nothing removes the bit before it looks, so a flag raised inside a stage runs `$1543`: the stage then keeps running at
  `(zone + 1, 0)`, and the game takes its end path once the stage exits. A forced run confirms the whole chain, including the callback's own side effect, but a forced state is not provenance. Beyond the verified
  placement lists (acts 15 / 12 / 9 / 6 / 3 for zones 8-12) the pointer is not a list at all; most such rows name boss and level-clear types. Those routes are open, not excluded.
* **U3 is PARTIAL, and the answer differs sharply per (zone, act).** The loader thresholds are re-derived (9, 9, 6, 9, 6). The mapper state at the record's dereference is derived, not assumed: slot 2 holds the layout bank named by the
  level-header table, bank `$1B` for every in-domain stage. The first out-of-domain pointer is `$8000`, i.e. the first ten bytes of bank `$1B`. **New: the loader is not the first thing to go wrong.** The graphics loader `$78E1`, which
  `$2934` runs *before* the loader, indexes a 42-row table by `(3*zone + act) mod 256`. Of the 1,070 rows (in- and out-of-domain) whose row index is 42 or more, 1,054 never become active in the harness: they decompress a garbage row with interrupts
  disabled and never reach the loader, starting at exactly the act where the table ends (zones 8-12: 18, 15, 12, 9, 6). Only 186 of the 1,192 out-of-domain rows reach the loader at all. Eight rows are PROVEN RETURNABLE (pointer chain resolved from the ROM,
  every slot type a supported handler or a resident jump stub, and both a natural-timer and an accelerated-timer run returned). 87 are UNPROVEN (the record pointer is in RAM or a bank is unresolved); **no row qualifies as PROVEN BLOCKED**.
* **The two mechanisms interact only conditionally.** A zone-complete inside a stage does not call the loader; the ordinary return keeps the act, so a large act can select another out-of-domain record when the level reloads.
* **R2's propositions keep their status.** A stays PARTIAL, B stays DISPROVEN (its weaker proven statement stands), C stays PARTIAL and gains one conditional route; R1 stays PARTIALLY CLOSED. New open items are listed in section 10.

## 2. U1 - zone completion while a special stage runs

### 2.1 The three writers (physical offset, bank, CPU address)

Re-derived by the R2 flag scan *and* by a byte census of every immediate materialisation of `$D293` (23 `LD HL,$D293`, no DE/BC/IX/IY/mirror forms): `setter_census`. The bank is the one the object scheduler pages into slot 2
(`$5DF1`: types below `$26` use bank 12, `$26..$EF` bank `$1E`).

| Physical | Bank : CPU | Instruction | Effect from an empty flag byte | Containing routine | Reached by (type, state) |
|---|---|---|---|---|---|
| `$303ED` | 12 : `$83ED` | `SET 4,(HL)` | `$10` | callback `$83A6` (player state `$20`) | types 1 and 2, state 32 |
| `$7BB2A` | `$1E` : `$BB2A` | `LD ($D293),A` after `LD A,$50` | `$50` | callback `$BB1A` | type `$61`, state 5 |
| `$7BB6E` | `$1E` : `$BB6E` | `LD ($D293),A` after `LD A,$50` | `$50` | callback `$BB61` | type `$61`, state 7 |

`$303ED` is reached only when the act is 2 or more (`$303DD..$303EF`: below 2 the callback sets bit 5, the act-complete flag, instead); executed over all 256 acts it sets bit 4 for exactly the acts 2..255. The two `$50` stores belong to the
final-zone object: state 5 skips its store when `D500 == 1` and `D2CC == $1F`; state 7 first ORs `$20` into the emerald byte.

### 2.2 Callback provenance

* **Player state `$20`.** `$83A6` is the vector of state 32 for both player types (`FF 05` in the script). State `$20` is written by one instruction pair, `LD A,$20 / LD ($D502),A` at `$4892`, reached through the stub `$03F5`.
  No `LD (IX+2),$20` exists in the image; no player-script command `FF 03` names `$20`; the only absolute stores of `$D502` are 17 sites with constant values, one of them `$20`; the 3,181 instructions the player types can run
  (callbacks, resident callees, and the destinations of the resolved jump tables) contain sixteen writes of `(IX+2)`, all constants other than `$20`. The three byte-search hits for a call or jump to `$03F5` are bank 12 `$AB9B` (type `$19`, state 4),
  bank `$1E` `$81DF` (types `$33`, `$40`-`$50`, `$54`, `$56`, `$59`, `$60`, state 5) and bank `$1E` `$9D55` (types `$51`-`$53`, state 14): the boss and goal objects. No script vector equals `$03F5` or `$4892`.
* **Type `$61`.** Created by its parent type `$60` through an `FF 04` child command, or by placement. It creates types `$62` and `$0A`.
* **A callback syntactically reachable is not a callback scheduled.** `reach_map` shows *which* callbacks contain a site; whether the engine runs one in a stage depends on the object existing (section 2.3) and on its script reaching the state.
  The generator keeps the two apart and the tests exercise the separation with a synthetic callback that exists but has no creation edge.

### 2.3 What a special stage can contain

The placement routine (`$8000` in bank `$1C`, called every fourth frame from `$16B8`) picks its list from `word[word[$8546 + 2*zone] + 2*act]` (8-bit indices). For zones 8-12 and acts inside the verified list set the lists place only types
`$10`, `$26`, `$2F`, `$31`. The creation relation was derived from every type's callback code: `FF 04` child commands (parsed from the scripts), pool allocations with the type in `C` or `B` (resolved from the immediate that dominates the call; one counted
loop is resolved from its own instructions), in-place conversions (`LD (IX),n`; the destroy markers `$FE/$FF` are not types) and one register conversion (the player's type follows the character byte `$D2C8`, whose executed domain is `{0, 1, 2}`).
The closure from the placed types, the two player types and the resident per-frame code is `{1, 2, 3, 5, 6, 7, $0C, $0F, $10, $11, $13, $31, $37, $3A, $3D}` plus `$2F` or `$26` where placed. It contains none of the trigger types
(`$19 $33 $40-$54 $56 $59 $60` for the level-clear route, `$61` for the `$50` route): the level-clear object `$19` is created by type `$18` through the pool allocator, and neither is in a stage's list.

That statement is **excluded so far**, not excluded. Four table-indexed jumps inside the closure's code are not closed: `$314F4` has no instruction bounding its index; `$6C98` has no upper bound; `$6972` and `$77EC` are bounded by `AND $1F` but their 31-word tables leave
the 32nd index reading the code bytes `$C9 $DD` = `$DDC9`, a RAM address. Five table jumps are specified, checked against the instructions that build and bound their index, and followed through every destination: `$5FB8` and `$311BB` are closed, `$6972` and `$77EC` have that one
non-code word, `$314F4` is unbounded (its four 28-word sub-tables are followed); `$6C98` is not specified.

For acts beyond the verified list set the pointer is *not* a list. The generator resolves each pointer under slot 1 = bank 1 and slot 2 = bank `$1C` (the placement code's own bank) and parses the bytes as list entries: 986 of the 1,190 out-of-domain list rows
name trigger types, 1,084 name type bytes above the type table (`$64-$EF`, which index the type table out of range) and 30 never terminate within the resolved bytes. Whether the camera window and spawn-map cell ever create such an entry, and whether such a
boss could be defeated inside a stage, was not evaluated (`U1-open`).

### 2.4 State dispatch during a stage

`$1333` waits for a frame (`$062D`) and then dispatches on `$D294` and `$D293`. Executed for every `$D293` and every combination of `$D294` bits 6, 5, 3 with bit 7 set (`dispatcher_table`):

| Priority | Condition (stage mode, `D294` bit 7 set) | Target |
|---|---|---|
| 1 | `D294` bit 6 | `$183F` stage success |
| 2 | `D294` bit 5 | `$1815` stage failure |
| 3 | `D294` bit 3 | `$17B0` stage start |
| 4 | `D293` bit 5 | `$14AE` act complete |
| 5 | `D293` bit 4 | `$1543` zone complete |
| 6 | `D293` bit 2 | `$15F2` life lost |
| 7 | `D293` bit 0 | `$1696` pause |
| - | `D293` bits 7, 6, 3, 1 | ignored (frame update `$1786`) |

Bit 4 is honoured in stage mode at the *next* loop iteration after the callback raised it (callbacks run inside the frame update; the dispatch follows the next frame wait). Nothing removes the bit first: of the writers that can clear it (three `RES 4,(HL)`
in the handlers themselves and stores whose value lacks bit 4) none is in the per-frame code, in the callbacks of the placed types and the players, or in the IM 1 closure (3,584 instructions; its only state-flag writer is the timer's `SET 5,(HL)` on `D294`, `$2849`).
An interrupt can therefore raise `D294` bit 5, which then pre-empts a pending bit 4, but never clear it. The sibling flag follows the same route: `D293` bit 5 (act complete) is raised by `$303E7`, the act < 2 branch of the same callback, and honoured at `$14AE`, which
runs the results screen, adds one to the act and raises the reload bit that stage mode ignores. It has the same provenance and was not analysed further.

### 2.5 The zone-complete path with `$D297` in 8..12

`$1543` (executed lemma per zone): waits 60 frames, clears the slot types (`$1CEB`) and the object RAM (`$297E`), reaches `$1594 CP 5`, taken for every special-stage zone, so the **results screen is skipped**; then `$15CF` stores act 0, `$15D6` stores zone + 1 (9..13) and,
because the new zone is >= 6, the code takes `$15E8`: `RES 4,(HL) / SET 7,(HL)`. Nothing in the path writes `D294`. The stage-mode dispatcher ignores `D293` bits 7 and 1 (the reload request), so **the stage keeps running at `(zone + 1, 0)` with no loader call, no player and no objects**
until its own exit. The exit (`$1869`) restores the saved zone and raises bit 5; with bit 7 still set the normal dispatch sees `D293 = $E0` and takes the **end path `$1365`**, not the act increment. Interrupts are enabled between the two stores (`EI` at `$15C8`, no `DI` before `$15D6`),
so `(zone, 0)` is observable between them; of the observable pairs only `(13, 0)` leaves the 39-entry music table (index 39 reads `$21`, the first byte of the code at `$18E1`). In the injection runs no sound request other than the stage's own was written after the injection.

### 2.6 Controlled executions (forced, labelled)

The campaign injects `D293 |= $10` once the stage is active. In every special-stage zone the zone sequence is `0 -> s -> s+1 -> 0`, `D293` is `$C0` while the stage keeps its flag, the stage's timeout exits it (`D293 = $E0` at the exit) and the game runs the end sequence.
Two further experiments force the player's state byte to `$20` in a stage at act 2. With the player where it is, the callback's position test (`player x - camera x > $120`) is not met and bit 4 is not raised in the observed window. With the player placed `$130` right of the camera
the original callback `$83A6` raises `D293 = $50` on its next update and the stage continues at zone 9, act 0 - confirming the callback's side effect and the reaction chain *given* state `$20`. These runs establish what the code does once the state exists, not that the state can occur.

### 2.7 U1 verdict

**PARTIAL.** Resolved: the writers, their callbacks, the level-clear entry, the dispatcher priority, the flag's survival to the dispatcher, the effect of `$1543` with `D297` in 8..12, and the natural placement universe (excluded so far). Open: four computed jumps; creation from out-of-domain placement lists
and the boss fight inside a stage; the inherited U2, U4-U6 and R2-R5/S1.

## 3. U3 - record selection beyond the verified set

### 3.1 The loader and its thresholds

`$2A4F` (resident, bank 0) reads `p1 = word[$2A9A + 2*zone]` and `record = word[p1 + 2*act]`, both indices in 8 bits (`ADD A,A` drops the carry), then loads `D2E0`, `D399`, `D39B` from record bytes 0-5 and the four slot types `D452/D45A/D462/D46A` from bytes 6-9.
Both pointer tables are in bank 0, so the two lookups are resolved from the image alone (`first_pointer`, `second_read_at` in the rows); only the *dereference* of the record pointer needs a mapper state. The first act whose record is not one of the nine verified records, re-derived by executing the loader
for every act 0..255, is 9, 9, 6, 9, 6 for zones 8-12 (table in the generated block, together with the thresholds of the four other tables the stage start reads). Because the arithmetic is 8-bit, acts 128..137 select the records of acts 0..9 again and the sets are not monotone;
the evidence keeps every act.

### 3.2 Mapper state at the dereference

The loader is called from `$2934` (from the level-reload path `$1679` and the special-stage start `$17E5`) immediately after `CALL $4DAD`. The mapper writes reachable from `$4DAD` (whose closure stays in bank 0/1 code) are exactly two calls of the helper `$1C6F` (`LD ($D12B),A / LD ($FFFF),A`):
`$4DB5` (`A = ($D163)`) and `$4E22` (`A = ($D162)`, inside the 29-iteration `$4E13` loop). So **slot 2 at `$2A4F` is `$D162`**, which `$4FDC` stores from byte 0 of the level header chosen by `word[word[$5082 + 2*zone] + 2*act]` (16-bit index here): bank `$1B` for every in-domain stage.
The derivation rests on P1-P3 (`PREMISES`); the harness observed the same bank at the call in every one of the 189 rows where the loader was reached and a static value exists (`static_slot2_vs_observed`: 0 mismatches), and the same slot types (0 mismatches). A header pointer outside the verified set can name another bank (bank-0 data, a number above 31 taken modulo 32,
or a slot-2 address that needs the bank *before* `$4FDC`, reported as unresolved, never guessed).

### 3.3 What the pointers resolve to

The first out-of-domain pointer of every special-stage zone is `$8000` read under bank `$1B` (physical `$6C000`): the first ten bytes of the stage-layout bank, `00 82 20 82 40 82 60 82 80 82`. As a record they give `D2E0 = $8200`, `D399 = $8220`, `D39B = $8240` and slot types
`$60 $82 $80 $82`. Other rows read the record from bank 0 (`$2260` is the middle of a routine: the "record" is code), from slot 1, from other banks, or from RAM (`$C000+`, not ROM-derivable: unresolved). Across the 1,192 out-of-domain rows the pointer classes are bank 0: 564, RAM: 294, slot 2: 274, slot 1: 60.
`loader.rows` lists every (zone, act) with its two table reads, the record pointer and physical offset, the bank, the bytes consumed and the class of each slot-type destination.

### 3.4 Downstream: the slot-type dispatcher

The four slot types are executed every frame by the bank-`$1D` dispatcher `$8018` (R1 site C), called from the IM 1 handler at `$05C6` after it maps bank `$1D` into slot 2, whenever `D293` bit 6 is set and bit 1 clear (`slot_dispatch_caller`): `JP (HL)` with `HL = word[$8028 + ((2*type) mod 256)]`.
The type is doubled in 8 bits, so `v` and `v + 128` select the same word; 21 words are table data (types `$00-$14`, `$80-$94`) and everything else is code. Executed for the first threshold record: `$60 -> $0401` (a resident jump stub), `$82 -> $832E` (a supported handler), `$80 -> $8052` (supported, a `RET`).
Of the 256 slot-type bytes (`slot_type_classes`): 42 select a supported handler, 12 a resident jump stub, 54 other resident code, 8 the stub area at a non-stub address, 42 an address below `$0320` (restart and boot code), 20 bank-1 code, 36 further bank-`$1D` bytes and 42 a **RAM address**
(type `$C0` reads `$80A8 = $CD00`). A record whose types are not all in the first two classes leaves the supported set; the controlled runs show what that does.

### 3.5 Can the stage be left?

Each arrow of *loader entry -> initialisation -> active stage -> completion -> restored state* needs its own evidence.

* **A pointer being computed** - static, all 1,280 rows.
* **A pointer being dereferenced successfully** - static where the bank and address resolve; checked against the observed mapper (0 mismatches).
* **A stage becoming active** - controlled: `D294 = $80` with the timer running. This is where most rows fail (section 3.6).
* **A completion condition being achievable** - the failure exit `$1815` (timer or death) needs no object; the success exit needs the goal ring and was not required.
* **The return being executable** - controlled: `D294` cleared and the saved zone restored.

What the 1,280 controlled runs show (table in the generated block): the in-domain rows at acts 0-8 (zones 8, 9, 11) and 0-5 (zones 10, 12) return; the stall of section 3.6 decides most others; 86 rows execute RAM (the program counter leaves ROM: in 23 of them after the stage became active, in 29 followed by a restart at the title);
`$DD26`, `$E0E1` and `$CB82` are the commonest first RAM addresses (type `$C0`'s `$CD00` is first in three rows). Garbage handlers that run every frame change what happens over time: of the 114 rows run with the natural 59-second timer as well, 15 differ from the accelerated run (for example `(9, 9)`: its natural run clears the stage flag at
frame 4140 without restoring the zone). The accelerated timer (P5) is therefore used only to bound the sweep; a PROVEN RETURNABLE verdict requires both runs to return.

Verdict rules (`u3_row_verdict`): **PROVEN RETURNABLE** needs every pointer resolved from the ROM, every slot type to select a supported handler or a resident jump stub, and both controlled runs to activate the stage, raise no RAM execution and return with the zone restored;
**PARTIAL** when the record was read but a later step is unresolved or a run did not return, or when the stage load stalls with interrupts disabled before the loader is reached; **UNPROVEN** when the pointer chain cannot be resolved from the ROM (record pointer in RAM, unresolved bank);
**PROVEN BLOCKED** is reserved for a ROM-supported guard or terminal path. **No row meets it:** every non-returning row ends in RAM-determined execution or in a decompression loop whose non-termination was observed (bounded) but not proved.

The five rows the task names: `(8, 9)` PROVEN RETURNABLE (record `$8000` in bank `$1B`; types `$60 $82 $80 $82` select `$0401`/`$832E`/`$8052`; both runs return); `(9, 9)` PARTIAL (same record, but the natural run does not restore the zone); `(10, 6)` PROVEN RETURNABLE; `(11, 9)` and `(12, 6)`
PARTIAL: the graphics row index is `3*11 + 9 = 3*12 + 6 = 42`, the first row past the table, so the stage load stalls in `$78E1` and the loader (whose record would be `$8000` read under a garbage bank) is never reached.

### 3.6 The graphics-load stall (new)

`$2934` runs `$297E`, then `$78E1`, `$2993`, `$4FCE`, `$4FDC`, `$4DAD` and only then the loader. `$78E1` executes with interrupts disabled and reads `IY = $7CED + 7*L`, `L = (3*zone + act) mod 256` (8-bit), a row `bank, ..., source pointer` that it hands to the tile decompressor `$24C2`.
The table has 42 rows (`graphics_table`; its extent follows the rule R1/R2 use: the first row's second-level pointer is the address of the data after the table). For `L >= 42` the row is other data: in the harness 1,054 rows never leave the decompressor at `$2400-$25FF` with interrupts disabled for the whole 1,200-frame bound,
and a spot run of `(12, 6)` stayed there for 40,000 frames (about eleven minutes of game time; the program counter was inside those two pages at every sampled frame from about frame 5,000 on). With interrupts disabled neither the frame interrupt nor the timer can run, so the stage can neither start nor be left by its timer. This is a bounded observation, not a termination proof, which is why those rows are PARTIAL and not PROVEN BLOCKED.
It is not universal: the five rows with `L = 142` (acts 118, 115, 112, 109, 106) decompress to an end and the stage runs and returns (their record pointer is in RAM, so they are UNPROVEN). In-domain rows are not immune either: `(8, 51)` and the acts 128 and above select verified records through the loader's 8-bit wrap (period 128 acts) while the graphics index `(3*zone + act) mod 256` has not wrapped back into the table, and 49 of the 88 in-domain rows stall.
This also bears on R2's definition of *grounded*: a verified record does not by itself make a stage work.

### 3.7 How a stage can be entered at such an act (conditional)

`entry_routes` searches the R2 events. The entry at act 9 needs at least seven earlier stage entries (zones 8, 9 and 11), the entry of zone 10 at act 6 four, and the entry of zone 12 at act 6 four successes in a row (all five stages run at acts 2..6 of one zone).
Every entry assumes 100 rings (U6); every success assumes its emerald bit (U2). The routes are *conditional*, never grounded.

## 4. Physical offsets, CPU addresses and bank contexts

Sections 2.1 and 3.2 give the writers and the loader. Further sites (physical offset: bank / CPU in its window):

| Site | Physical | Context |
|---|---|---|
| level-clear routine `$4892` (stub `$03F5`) | `$04892` (`$003F5`) | bank 1 slot 1 (bank 0 slot 0) |
| callers of `$03F5` | `$32B9B`, `$781DF`, `$79D55` | bank 12 `$AB9B`; bank `$1E` `$81DF`, `$9D55` |
| placement routine | `$70000` | bank `$1C` slot 2 (`$8000`) |
| placement list table | `$70546` | bank `$1C` (`$8546`) |
| graphics loader `$78E1`, row table `$7CED` | `$078E1`, `$07CED` | bank 1 slot 1 |
| loader | `$02A4F` | bank 0 |
| level-header reader `$4FDC` and table `$5082` | `$04FDC`, `$05082` | bank 1 slot 1 |
| slot-type dispatcher (called from `$05C6`) | `$74018` | bank `$1D` slot 2 (`$8018`) |
| dispatch `$1336`, `$1762`, `$176F` | `$01336`, `$01762`, `$0176F` | bank 0 |
| zone-complete path | `$01543`-`$015E8` | bank 0 |
| stage return | `$01869` | bank 0 |
| first out-of-domain record (zones 8-12) | `$6C000` | bank `$1B` slot 2 (`$8000`) |

## 5. Control flow and state transitions

```
main loop $1333:  wait $062D -> D294 bit7 ? stage mode : normal mode
stage mode:  D294 b6 -> $183F -> $1869 (zone := saved, D293 |= $20)
             D294 b5 -> $1815 -> $1869
             D294 b3 -> $17B0 (stage start: $187B zone := 8+n, $2934: $297E $78E1 [graphics] $2993 $4FCE $4FDC $4DAD $2A4F [loader] ...)
             D293 b5 -> $14AE (act complete; the stage is NOT left: D294 stays)
             D293 b4 -> $1543: act := 0, zone := zone+1, (zone>=6) D293 := D293 &~$10 | $80
                                   -> $1333, D294 unchanged, loader not called
             else    -> frame update $16B8 (object scheduler, placement, player)
normal mode after the stage exit: D293 bit7 set -> $1365 end path
                                  D293 = $60 (bit 5) -> $14AE -> act := act+1 -> bit 1 -> level reload $1673 -> $2934 -> graphics + loader
```

| Event | (zone, act) before | after | Flags | Loader called |
|---|---|---|---|---|
| stage entry (`$187B`) | (z, a), z < 6 | (8+n, a) | `D294 := $88` then `$80` | yes (`$2934`, after the graphics loader) |
| zone complete in a stage (forced) | (s, a), s in 8..12 | (s+1, 0) | `D293 := D293 &~$10 \| $80`, `D294` unchanged | no |
| stage exit | (s', a') | (saved, a') | `D294 := 0`, `D293 \|= $20` | no |
| act complete after the exit | (saved, a') | (saved, a'+1) | bit 5 cleared, bit 1 set | yes (reload) |

## 6. Mapper and RAM side effects

* `$187B` stores the saved zone in `D296` and writes the stage zone to `D297`; the act byte is not touched. The stage start clears `D15E..D28F` and `D300..DBBF`.
* `$78E1` and `$4DAD` change slot 2 several times; after `$4DAD` returns slot 2 is the layout bank (P3: an interrupt restores it). `$78E1` runs with interrupts disabled.
* `$1543` clears the four slot types (`$1CEB`) and the object RAM (`$297E`) twice, sets `D2D4 := 4` and writes act, zone and `D293`; it does not write `D294`.
* The slot-type dispatch writes nothing itself; a destination in RAM makes the program counter leave ROM.

## 7. Proven, conditional and unresolved paths

| Status | Item |
|---|---|
| proven (static, executed lemmas) | the three bit-4 writers, their callbacks, the level-clear entry; stage-mode dispatch priority, masking and the survival of the flag; the effect of `$1543`/`$1869` with `D297` in 8..12; the loader chain for every special-stage zone and 8-bit act; the mapper derivation (under P1-P3); the graphics-table extent |
| proven, scoped | no trigger type is in the natural placement universe's resolved closure |
| conditional | every route that needs 100 rings (U6) or an emerald bit (U2); every controlled result (it holds for the supplied state: forced entry, zero-filled RAM, the harness VDP); the claim "excluded" for the natural universe (four open computed jumps) |
| unresolved | out-of-domain placement lists (creation, boss fight); records whose pointer is in RAM or whose bank is unresolved; RAM-determined execution; termination of the `$24C2` decompression on garbage rows; the start-position and palette tables |

## 8. Interaction between U1 and U3

* **Could an out-of-domain stage instantiate a completion callback that cannot exist in a stage?** Conditionally: most out-of-domain placement-list rows name trigger types, but only 186 of 1,192 out-of-domain rows even reach the loader, and creation and the fight were not evaluated.
* **Could a stage zone-complete select a new combination with an unverified record?** No loader call follows (the stage-mode dispatcher ignores the reload request) and the new pairs `(9..13, 0)` select verified records.
* **Could the ordinary return keep an act high enough to select another out-of-domain record?** Yes, as a conditional chain: the level reloads for `(saved zone, act + 1)`; for saved zone 0 the reload leaves the verified records from entry act 29, for zone 5 from entry act 14.
* **Could a partial zone/act update be observed during an interrupt?** Yes, `(zone, 0)` between the two stores; harmless for the consumers analysed; the only pair outside the music table is the final `(13, 0)`.

## 9. Consequences for the R2 propositions and model

* **A (zone-music):** unchanged, PARTIAL. New fact: the first byte past the table (`$21`) is what `(13, 0)` would request; `(13, 0)` is reachable only through U1's open routes and no injection run requested it.
* **B (loader record):** unchanged, DISPROVEN as proposed. The proven weaker statement (nine records for zone <= 15, act <= 2; the per-zone safe act bounds) stands. R3 adds that leaving the bound is not an immediate fault for every row, and that other tables (graphics rows) fail earlier than the loader.
* **C (nested dispatcher):** unchanged, PARTIAL. One conditional route is added: the out-of-domain record of zone 12 at act 127 carries a type-5 slot, which would run the zone-indexed jump with zone 12 outside the 12-entry table (destinations `$0401`/`$21C9`); the stage entry at act 127 is conditional and was not run to that point.
* **R1:** PARTIALLY CLOSED, unchanged. Two jump tables read one word past their end (`$6972`, `$77EC`). The lemmas R1 left open, and what R3 adds:

  | R1 lemma | Status after R3 |
  |---|---|
  | zone/act (`$08137`, zone-music read) | open; A is still PARTIAL; one new forced pair `(13, 0)` reads `$21` |
  | sound test (`$D2BF`) | untouched |
  | record fetch (`$74027`: slot types come from nine records) | still not closed as stated (R2); R3 shows what the out-of-range rows select: supported handlers, resident stubs, resident or bank-1/`$1D` code, or RAM |
  | allocator / kernel vector (`$1CD3`) | untouched (U4) |
  | type-5 zone type (`$741F1`) | open; one conditional route to a type-5 slot beside zone 12 |
  | R2-R5, S1 | unchanged |

* **R2's model:** the ungrounded edge `zone_complete_in_special_stage` is *retained as unresolved*. If it were taken, its executed target is not `END` at once: the stage continues at `(zone + 1, 0)` and the game ends after the stage exits. R2's unknown-record paths are resolved for every special-stage (zone, act) in the
  sense that the pointer, bank and bytes are known where the ROM determines them; R2's definition of *grounded* (record in the nine) is unchanged, so no state becomes grounded and no R2 output changes.

## 10. Remaining dependencies and the next bounded task

Inherited: U2 (emerald masks), U4 (allocator / kernel vector), U5 (register-addressed block moves), U6 (character and 100 rings), R2-R5 and S1. New: **U1-open** (out-of-domain placement lists; creation and the boss fight), **N1** (the other zone/act consumers: start-position table `$4E98`, palette `$794F`, 42 zone and 21 act readers),
**N2** (slot and object type bytes outside their tables), **N3** (zero-filled power-on RAM in the harness, forced entry, accelerated timer) and the open jump tables. A further new item: termination of the `$24C2` decompression on out-of-table graphics rows.
Recommended next task: *DECOMP-1D-R4, the open computed jumps and the garbage-row decompression* - resolve `$314F4`, `$6C98`, `$6972` and `$77EC` (the terrain-type tables and their index domain), the object-type table bound for types `$64-$EF`, and decide whether `$24C2` terminates on the out-of-table rows
(an exact state-repeat check or a decoder model). That would let U1's natural-universe statement become PROVEN EXCLUDED (or produce its counterexample) and turn the 1,054 stalled rows into PROVEN BLOCKED or into returnable ones.

## 11. Tests and reproducibility

```
python tools/decomp1d_r3_special_stage.py /path/to/SonicChaos.sms --controlled --doc docs/decomp-1d-r3-special-stage-reachability.md   # regenerates the evidence (about half an hour)
python tools/decomp1d_r3_special_stage.py /path/to/SonicChaos.sms --check                                                             # static evidence vs a fresh run
python tools/decomp1d_r3_special_stage.py /path/to/SonicChaos.sms --check --controlled                                                # everything, including the campaign
python -m unittest tests.test_decomp1d_r3
```

The ROM is read from the path argument or `SONIC_CHAOS_ROM`; no ROM bytes are committed. The controlled campaign needs the `z80` package (`requirements.txt`); without it the controlled tests skip and `--controlled` is unavailable.
Controlled execution used the DECOMP harness (`tools/sms_frame_harness.py`): original Z80 code, Sega mapper, an approximate VDP, zero-filled RAM. It is **not** hardware validation and not a console emulator. Each case starts from one booted state (forked workers), so results do not depend on the schedule;
three complete campaigns during development gave identical outcome counts.

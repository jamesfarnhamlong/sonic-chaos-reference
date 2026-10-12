# DECOMP-1D-R2 - Zone/Act Invariant Proof

Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Base commit `2dcaa09beabe90329deed83af27f2912d19a232f` (DECOMP-1D-R1 on `main`).

Evidence: `data/decomp1d/r2-zone-act-invariants.json` (generated, deterministic).
Generator: `tools/decomp1d_r2_zone_act.py`. Tests: `tests/test_decomp1d_r2.py`.

This is **not** the DECOMP-1D assumption R2 (register-addressed writes); the name is the milestone's. It decides the valid
values and relationships of the zone byte `$D297` and act byte `$D298` at the three consumers DECOMP-1D-R1 left conditional.
Everything is derived from the ROM; nothing is taken from the POC or from external lists.

## Result

<!-- r2-generated:begin -->

| Proposition | Status |
|---|---|
| A - zone-music table read at $18A0 | **PARTIAL** |
| B - level loader record selection at $2A4F | **DISPROVEN** |
| C - nested dispatcher $741F1 in bank $1D | **PARTIAL** |

Writer census: 9 zone, 8 act and 1 saved-zone absolute stores; wide / index-register hits: 0; mirror hits: 0.

Modelled states (act cap 40): 1483 on any path, 115 grounded, 115 grounded in normal play.

Counterexample to B (normal play): initial(0, 0) -> act_complete(0, 1) -> act_complete(0, 2) -> special_stage_enter(8, 2) -> special_stage_return(0, 3)

Music index is inside the table iff `(3*zone + act) mod 256 <= 38`; nested-dispatcher zones inside the table: [0, 1, 2, 3, 4, 5, 64, 65, 66, 67, 68, 69, 128, 129, 130, 131, 132, 133, 192, 193, 194, 195, 196, 197].

<!-- r2-generated:end -->

* **A** - the zone-music read at `$18A0` is **PARTIAL**. The index is `(3*zone + act) mod 256` into a 39-entry table. It is
  inside the table for every modelled grounded path, and for every zone 0..12 with act 0..2. It is *not* an invariant: the act
  is unbounded (see B), so a special stage entered after enough act increments over-reads the table. Every such path rests on
  an undischarged dependency (U2, U3), so no grounded counterexample exists, but the route is **not** closed.
* **B** - the loader record selection at `$2A4F` is **DISPROVEN** as proposed. `zone <= 15` is not contradicted (see below) but
  `act <= 2` is false in normal play: new game, finish acts 0 and 1, collect 100 rings in act 2, finish the special stage, and the
  return path increments the act to 3. The implication the proposal wanted is still **proven**: for zone <= 15 and act <= 2 the
  four slot types come from nine records. The record-fetch dependency of `$74027` is therefore *not* closed as stated.
* **C** - the nested dispatcher `$741F1` is **PARTIAL**. The table has 12 entries; exactly zones 0..5 (and their 8-bit aliases
  64..69, 128..133, 192..197) index inside it. No grounded path puts a type-5 slot beside a zone outside the table; the
  allocator route, zone-complete inside a special stage and special stages loaded from a garbage record are not excluded.
* **R1 stays PARTIALLY CLOSED.** No dispatcher is promoted. The bank-`$1C` entry at `$70000` stays conditional, the deferred
  regions `banked_entry_70000` and `banked_dispatch_7013E` stay unregistered, and the ledger is untouched.

## Method

1. **Census** of every way the ROM can write the three bytes: absolute stores in all encodings (`LD (nn),A`, `LD (nn),rr`,
   `LD (nn),IX/IY`; a byte search, so alignment does not hide a hit), their `$E000` mirror, immediate pointer
   materialisations in `$D290..$D298` followed through the stores made with them, and every `LDIR/LDDR/LDI/LDD` with its
   destination where both `DE` and `BC` are immediates. Unresolved items are *listed*, never assumed benign.
2. **Classification** of each store's value source from the instructions that feed `A` (constant, copy, increment, computed).
3. **Execution**, not pattern matching: a small fail-closed Z80 interpreter (`Interp`) runs the index expressions, the writers'
   value computations and the guards for every input. RAM that was not supplied, a ROM or mapper write, an instruction outside
   the whitelist, or a slot whose bank is unverified all raise; a result never rests on an invented value.
4. **Transition model**: the zone/act state machine whose events are the writer sites. Each edge carries the ROM facts that
   justify it and a *grounded* flag. An edge is grounded when every record it loads is one of the nine records of the
   proposed domain and a special stage is the one entered with no emerald bit set. Three explorations are made: every edge,
   grounded edges, and grounded edges of normal play (no hidden menu, no attract demo).
5. **Verdict rule** (`derive_status`): PROVEN needs a closed argument; DISPROVEN needs a counterexample whose every step is
   grounded; PARTIAL when some sub-claim is proven; UNPROVEN otherwise. Absence of an observed failure never upgrades a status.

## The writers

Nine zone writers, eight act writers and one saved-zone writer, all absolute `LD (nn),A` in the resident bank, all inside the
discovered code. No wide store, no index-register store, no `$E000`-mirror store exists. The reset and restart clears
(`LDIR` at `$0029` and `$0462`, `HL=$C001`, `DE=$C002`, `BC=$1FEE`, fill value 0) zero all three bytes.

| Byte | Site | Value | Provenance |
|---|---|---|---|
| zone | `$06CD` | 7 | title initialisation `$06C7` (zone, then act) |
| zone | `$07CF` | 0 | new game / continue `$07CE` (zone, then act) |
| zone | `$0821` | table | level-select pair, `$082A + 2*index`, index 0..17 |
| zone | `$15D6` | zone + 1 | zone complete; act is cleared first (`$15CF`); `CP 6` then picks the end path |
| zone | `$1870` | saved zone | special-stage return |
| zone | `$1897` | 8..12 | special-stage entry, `8 +` the count of consecutive set low bits of `$D2CC` |
| zone | `$2A27`, `$2BE8` | 0 | restart paths (`$2A27` after `OR A / RET NZ`) |
| zone | `$2C55` | 2, 0, 1 | attract rotation `$2C34`, row 0..2, `AND 15` of the row |
| act | `$06D1`, `$07D2`, `$15CF`, `$2A2A`, `$2BEB`, `$2C6E` | 0 | as above |
| act | `$0826` | 0..2 | level-select pair |
| act | `$1538` | act + 1 | act complete, **no guard** on the straight line `$14AE..$1538` |
| saved | `$187E` | zone | special-stage entry, reached only after the `$178F` guard |

The level-select index (`$D2C9`) is held to 0..17 by its two writers in the select loop (`$08A8` decrement if non-zero,
`$08B3` increment if below `$11`; both executed); the unguarded increment at `$0B7D` belongs to the sound-test loop and is not
reachable from `$085A`, and no `$D2C9` writer is inside the interrupt closure. The level-select screen itself is behind the
`$D2CE` bit 0 option, so those pairs are classified as a hidden menu, not normal play.

## Lifecycle

* **Boot / restart**: zone = act = 0, then the title sets zone 7, act 0.
* **New game** (`$07CE`): zone := 0, act := 0 (zone first). With the option set, the level-select screen then overwrites
  the pair (zone first) from the 18-entry table, zones 0..5 x acts 0..2.
* **Act complete** (`$303DD`, object-callback code): the trigger reads *only the act*. Act < 2 raises `D293` bit 5; act >= 2 raises
  bit 4. Bit 5 runs `$14AE`: wipe slot types and object RAM, then `INC act` (`$1538`), then bit 1 reloads and starts the music.
  The final zone is not special-cased by act number; the zone appears only at `$15D9` (`CP 6`) and `$1597` (`CP 5`).
* **Zone complete** (bit 4, `$1543`): act := 0 (`$15CF`), zone := zone + 1 (`$15D6`). Zone 5 + 1 = 6 takes the end path.
* **Special stage**: a 100-ring pickup (`$3138` single ring, `$4AC0` ten-ring monitor) calls
  `$178F`. It reads the character (must be 1), the zone (must be < 6) and the emerald byte (not all five bits); it does **not read
  the act**. It arms `$D294 := $88`; `$17B0` saves the zone and writes 8..12. The return (`$1869`) restores the zone and **raises
  bit 5**, so the act-complete path runs and increments the act. This is the unguarded growth: each special stage adds one act.
* Zone 6 (after the final zone), 7 (title) and 8..12 (special stages) are legitimate zone values; 13 is reachable only through U1.

## Intermediate states

Seven adjacent zone/act store pairs exist (`$06CD/$06D1`, `$07CF/$07D2`, `$0821/$0826`, `$15CF/$15D6` act first,
`$2A27/$2A2A`, `$2BE8/$2BEB`, `$2C55/$2C6E`). None has a `CALL` or `EI` between its stores, but an interrupt can run
between them whenever interrupts are enabled, and the music routine `$189B` and the nested dispatcher `$741E0` are **inside the
IM 1 closure** (the loader is not; its two callers `$06E8` and `$294B` are main-thread code). The transient pair `(new zone, old act)` is therefore an input to A; it is checked in the
evidence (`intermediate_pairs_checked`, none violating on a grounded path). The nested dispatcher reads only the zone, which is
written by one store at a time, so C sees no inconsistent value. The `(zone, 0)` transient of `$15CF` is always valid.
No zone/act writer is inside the interrupt closure, so an interrupt cannot interleave a *second* writer with a main-thread one.

## Evidence record per proposition

### A - zone-music table read, `$18A0`

* Entry `$18A0` (file `$018A0`, bank 0, slot 0), read at `$18B2`. Ten `CALL/JP` encodings name `$189B` (title `$06EF`, level
  start `$1685`, special stage `$17F7`, attract `$2CB0`, an object path `$4A9C`, others); the conditional `JP Z,$189B` at `$2853`
  (the `$D3C4` timer routine) is inside the interrupt closure.
* Inputs: zone `$D297`, act `$D298`. Index: `L = (3*zone + act) mod 256`, `H = 0`, address `$18BA + L` (executed for all pairs).
* Table: base `$18BA`, 39 entries; it ends at `$18E1`, the first `CALL/JP` target above the base (code).
* Valid iff `(3*zone + act) mod 256 <= 38`: zone 12 -> act 0..2, zone 5 -> act 0..23, zone 0 -> act 0..38 (plus wrapped runs).
* Writers: all 18 absolute stores classified. Domain: zone {0..5, 6, 7, 8..12}; act {0} plus the unguarded increment.
* Violations: none on a grounded path. On ungrounded paths the first over-read is act 15 at special-stage zone 8, 12 at zone 9, 9 at zone 10,
  6 at zone 11, 3 at zone 12. Zone 13 act 0 (index 39) needs U1. 203 violating states read a byte in `$C5-$D3`;
  the smallest forbidden act per special-stage zone is 26 / 23 / 20 / 17 / 14.
* Unresolved predecessors: U1, U2, U3. **Status PARTIAL.** `$08137` is not promoted; the sound-test lemma `$D2BF` is untouched.

### B - level loader record selection, `$2A4F`

* Entry `$2A4F` (file `$02A4F`, bank 0). Callers: `$06E8` (title) and `$294C`.
* Expression: `record = word[word[$2A9A + 2*zone (8-bit)] + 2*act (8-bit)]`; record bytes +6..+9 become the four initial slot
  types `$D452/$D45A/$D462/$D46A`. There is no validation: an out-of-range act aliases the next zone's table; past the last
  pointer (act 30 for zone 0, 15 for zone 5, 9 for special-stage zone 8) the word is record data used as a pointer.
* Sufficiency (PROVEN, executed): all 48 combinations zone <= 15, act <= 2 select the nine records `$2AF6, $2B00, $2B0A, $2B14,
  $2B1E, $2B28, $2B32, $2B3C, $2B46`; the slot types come from them (types 0,1,2,3,4,5,6,8,11,12,13,14). Zones 14 and 15 select only `$2AF6`
  for acts 0..2.
* Necessity of the bound: genuine levels are zone 0..5 x act 0..2 (the level-select table); a special stage reuses the act of
  the level that triggered it and its return adds one, which is how the act leaves that range.
* Per-zone safe act bound (acts 0..A all select a record): 29, 26, 23, 20, 17, 14 for zones 0..5; 8 for special-stage zones 8, 9, 11; 5 for 10, 12.
* Invalid combinations are not rejected; the intermediate states of the transitions are valid pairs on grounded paths.
* **DISPROVEN** for `act <= 2`; zone <= 15 is PARTIAL (U1 would reach 13, still < 16). The weaker, proven statement is the safe bound table.

### C - nested dispatcher, `$741F1` (bank `$1D`, CPU `$81F1`)

* Index `word at $81F2 + 2*(((2*zone) mod 256 + B) mod 128)`, with `B` the slot's phase bit; the zone is the only RAM read (executed).
* Table: 12 entries, end `$820A` (words below the lowest destination, R1's region rule). Zones inside: 0..5 and the aliases above.
* Type 5 occurs only in records `$2B0A`, `$2B1E`, `$2B28`, i.e. the acts of zones 2, 4, 5 (and the aliases of those tables).
* Construction: through the loader, none for zone > 5 on a grounded path. Special stages at act >= 9 (zones 8, 9, 11) or >= 6 (zones 10, 12)
  read a garbage pointer, so their record is unresolved (U3). Through the allocator: not excluded (U4).
* Survival: slot types are cleared by `$1CEB` and object RAM by `$297E` before the reload on the act-complete, zone-complete and
  special-stage-start paths (seven `$1CEB` call sites); title, restart and continue entries were not traced.
* **Status PARTIAL.**

## Relationship to the R1 dispatchers

| Dispatcher | Closed by R2 | Still open | Other dependencies |
|---|---|---|---|
| `$08137` | nothing | ZONE/ACT lemma (A is PARTIAL) and the SOUND TEST `$D2BF` lemma | U1-U3; sound-test closure has unresolved jumps |
| `$74027` | not the stated record-fetch lemma (act <= 2 is false); the safe-bound statement is proven | ALLOCATOR / kernel-vector lemma | U3, U4 |
| `$741F1` | table extent and the zone set; no grounded type-5 slot outside the table | allocator creation, zone-complete in a special stage, garbage special-stage records | U1, U3, U4 |

R1's overall status does not change.

## Premises and dependencies

* P1 standard mapper semantics (DECOMP-1D R4); slot 0 is bank 0 (the only `$FFFD` stores in discovered code write 0; one byte
  pattern in tile data at `$4FE4C` is outside the discovered code and is listed); slot 2 = bank `$1D` for `$8000` (R1).
* P2 player inputs are adversarial. P3 computed-pointer writers and unresolved block moves are listed, not excluded (DECOMP-1D R2
  stays open). P4 the discovered-code universe is the DECOMP-1D walk; object-callback code is classified by the same analysis.
* Inherited: DECOMP-1D R3 (slot 1 = bank 1 at handler entry), R5 (instruction universe), S1 (stack discipline), and R1's open lemmas.

## Unresolved

* **U1** zone-complete trigger inside a special stage: `D293` bit 4 is raised by `$303ED` (act >= 2) and the `$50` stores at `$7BB2A/$7BB6E`,
  object-callback code outside the discovered universe; the special-stage dispatcher honours it.
* **U2** emerald masks come from objects (`$794A7`, `$7BB69`); special-stage zones above 8 are not grounded.
* **U3** special stages loaded from a garbage record pointer; whether they can be left is unknown.
* **U4** allocator / kernel-vector route to a type-5 slot (R1 lemma).
* **U5** register-addressed block moves with an unresolved destination: 19 in discovered code, 18 outside it.
* **U6** the character byte and reaching 100 rings are player-supplied.

## Reproduce

```
python tools/decomp1d_r2_zone_act.py /path/to/SonicChaos.sms --doc docs/decomp-1d-r2-zone-act-invariants.md
python tools/decomp1d_r2_zone_act.py /path/to/SonicChaos.sms --check
python -m unittest tests.test_decomp1d_r2
```

The ROM is read from the path argument or `SONIC_CHAOS_ROM`; no ROM bytes are committed. Controlled execution (the interpreter)
corroborates arithmetic only; no emulator was available and no hardware trace was taken.

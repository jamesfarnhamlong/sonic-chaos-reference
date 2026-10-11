# DECOMP-1C: player script and callback dispatch recovery

Branch `research/decomp-1c-player-callbacks`, started from Research `main` `f58bf16` (DECOMP-1B merged).
Scope: reconstruct how the animation engine consumes the player state scripts, prove which JP stubs in the
`$0320-$044F` stub run are entered, recover those stubs and the handlers only they or the scripts reach, and let the
ledger recognise the mechanism. Not a general player-physics or whole-engine disassembly; no POC, root `AGENTS.md`
or other worktree changes.

Everything below is regenerated from the original ROM (SHA-256 `eabc8db5...fee607`) by
`python tools/decomp1c_callbacks.py <ROM>` into `data/decomp1c/callbacks.json` and
`data/decomp1c/derived-regions.json`, and checked by `tests/test_decomp1c.py`.

## Result

| | DECOMP-1B final | DECOMP-1C | Change |
|---|---:|---:|---:|
| Recovered assembly (regions / bytes) | 78 / 13,360 | 113 / 13,988 | +35 / +628 |
| Reviewed flow-verified CODE (reviews / bytes) | 26 / 1,568 | 29 / 1,910 | +3 / +342 |
| CODE | 17,086 | 18,056 | +970 |
| UNKNOWN | 368,371 | 367,401 | -970 |
| Structurally classified | 155,917 | 156,887 | +970 |
| Independently evidenced | 145,004 | 145,346 | +342 |
| Classified only by the recovery manifest | 10,913 | 11,541 | +628 |
| Unresolved audit clusters / UNKNOWN bytes in them | 36 / 2,361 | 23 / 1,553 | -13 / -808 |
| Audit ranges fully classified / partial / unresolved | 168 / 6 / 37 | 185 / 8 / 18 | |

The three metrics stay separate. **+970 classified (UNKNOWN to CODE)** = 162 bytes of JP stubs + 406 bytes of
handlers + 402 bytes of callees reached through the script-dispatch seeds and the recovered stubs that stay reviewed
flow claims. **+628 recovered assembly** = 165 stub bytes + 463 handler bytes; 3 stub bytes and 57 handler bytes were
already classified by earlier claims. Recovered bytes count as "classified only by the recovery manifest" in this
ledger, so converting a reviewed claim to assembly moves bytes from the independent line to that one; it is not a
loss of evidence. **Execution traces: none.** Every statement here is static (ROM structure plus control
flow); nothing shows the game enters a given state during play.

`build_verify.py`: byte-identical, 113 regions, 13,988 bytes, 5,370 decoded instructions.

## Phase 1: the script format, as the engine reads it

`tools/player_scripts.py` takes nothing from audit caches, region names or expected addresses. It first decodes the
engine's own instructions and refuses to parse a ROM that differs from the sequences it relies on
(`engine_facts`, tamper-tested):

* `$651D-$6537`: state lookup. Object type `IX+0` indexes the word table at `$65BA`; that word is the type's state
  table; the requested state indexes it; the result becomes the script cursor `IX+14/15`. The player is type 1
  (Sonic) or 2 (the second character); both are parsed (tables at `$8000` and `$89BB`, 55 and 54 states; a table ends
  where the lowest script it points at begins).
* `$6543`: a record is **4 bytes: duration, frame, callback-lo, callback-hi** unless the first byte is `$FF`. The
  callback word is stored into `IX+12/13`.
* `$FF xx` (`$6680-$6695`): command `xx` is dispatched through the 16 pointers at `$6696`; the handler reads its
  operands from the cursor.
* Player update `$361D` maps bank 12 around `CALL $64FA` (`$3637-$363C`), and around `CALL $5E91` (`$3648-$364D`) for
  the callback; `$5E91-$5E9A` loads `IX+12/13` into HL and executes `JP (HL)`. So scripts are read from bank 12
  and every non-zero callback vector is executed with bank 12 mapped.

Command semantics are **derived**, not listed: a small symbolic walk of each handler (`derive_commands`) follows its
paths, tracks which operand byte each register holds and records what is stored to the cursor (consume *n* bytes,
or jump to an operand word), which operand word is executed through `JP (HL)`, and which operand bytes are stored
to `IX+12/13`. Result (operand offsets are from the byte after the command number):

| Cmd | Handler | Operands consumed / flow | Executes operand word | Callback stored from |
|---|---|---|---|---|
| 0 | `$66B9` | none; restarts the script (terminal) | | |
| 1 | `$66C5` | 2; continue | word at +0 | |
| 2 | `$66DB` | 4; continue | | |
| 3 | `$670B` | 1 | | |
| 4 | `$671F` | 6 (both branches) | | |
| 5 | `$67A1` | 4; frame set | word at +0 (selector) | word at +2 |
| 6 | `$67D5` | 1 | | |
| 7 | `$67EC` | jump to operand word at +0 | | |
| 8 | `$67FF` | 4, or jump to the word at +2 | word at +0 | |
| 9-12 | `$6827 $6841 $6857 $6873` | 2 / 3 / 2 / 2 | | |
| 13 | `$688F` | 5; frame set | | word at +3 |
| 14 | `$68BB` | 1 | | |
| 15 | `$68CF` | 2, or jump to the word at +0 | | |

`parse_scripts` then walks each state's script exactly this way: records advance 4, commands advance by the derived
operand length, both successors of a conditional command are explored, and anything the engine could not read is
recorded in `notes` instead of repaired (unknown command, a jump leaving the slot-2 window). **All 109 player
state scripts parse with no notes.** A word that merely equals a stub address inside a duration, frame, selector or
unrelated operand is never reported as a callback; `tests/test_decomp1c.py` builds a record whose duration/frame
bytes spell a stub address to prove it.

Parsed callbacks: 567 rows: 492 record callback fields, 30 `FF 05` callback operands and 75 executed operands
(`FF 01` x42, `FF 05` selectors x30, `FF 08` x3, across both characters).

## Phase 2: the established chains, re-derived from the ROM

Each row is a parsed script location, not a word match. All three are static (statically reachable; not observed in
execution) and executed with bank 12 mapped.

| State | Char | Script (CPU / file) | Where the vector is | Vector -> stub -> destination |
|---|---|---|---|---|
| `$0A` | 1 | `$8142` / `$30142` | `FF 05` at `$8142`, callback operand `$8146` (`$30146`), selector `$8F76` | `$03B3` -> `JP $3901` |
| `$0A` | 2 | `$8ACE` / `$30ACE` | `FF 05` at `$8ACE`, callback operand `$8AD2` (`$30AD2`), selector `$8F76` | `$03B3` -> `$3901` |
| `$0E` | 1 / 2 | `$81E0` / `$8B67` | 29 record callback fields, first at `$81E2` / `$8B69` | `$03AD` -> `JP $3A37` |
| `$14` | 1 / 2 | `$81C6` / `$8B4D` | 6 record callback fields, first at `$81C8` / `$8B4F` | `$03F8` -> `JP $3A48` |

Supporting instructions: the record read `$653D`, command dispatcher `$6680`, handler `$67A1` (stores `IX+12/13`
at `$67AC/$67B1`, then `JP (HL)` into the selector), callback executor `$5E91-$5E9A`, and player update
`$3637-$364D`. The full per-callback table (type, state, bank, script CPU and file offset, operand CPU and file
offset, vector, selector and its operand) is `callbacks[]` in `data/decomp1c/callbacks.json`.

## Phase 3: which stubs are recovered

The stub run is **`$0320-$044F`: 101 consecutive three-byte `JP` instructions**, not the 69 at `$0380-$044E` the
brief names; 32 more precede `$0380`. That geometry is recorded as a structural fact only. A stub is recovered only
when it is entered by one of:

1. a parsed script stores its address as a callback vector, or has the engine execute it as a command operand;
2. a CALL/JP in byte-verified recovered assembly (excluding the regions this tool derives) targets it;
3. a CALL/JP in code reachable from a hardware vector (DECOMP-1B root) targets it.

Result: **55 of 101 stubs supported** (34 by scripts only, 20 by recovered banked object code only, 1 by both),
**46 left UNKNOWN**: `$326 $32C $335 $341 $344 $34A $350 $353 $356 $359 $35C $362 $365 $368 $36B $374 $377 $37D
$389 $38C $398 $39B $3A1 $3BF $3D7 $3EF $3F2 $3F5 $3FB $3FE $401 $404 $407 $40A $40D $413 $419 $41C $41F $422 $425
$428 $42B $434 $43A $446`. Their bytes look like `JP`, but neither a script nor any proven caller enters them; absence
of evidence is not evidence of absence, and they may be used by code or scripts this milestone does not cover
(other object types' scripts, unrecovered code). The three priority stubs are all supported.

The 55 stubs form 22 runs (`callback_stubs_<addr>`, 165 bytes) registered in `asm/recovered/`.

**Handlers.** A reviewed CODE run becomes a recovered `dispatch_target_<offset>` region only if every seed of its
review is a supported stub destination or a script-executed word, an entry lies inside the run, confined descent
from those entries fetches every byte, the last instruction is terminal and every `JR`/`DJNZ` stays inside the run
(the assembly needs labels). 13 of the 47 reviewed claims (derived with the handler regions removed) qualify (463 bytes): `$03783 $0384D $03901 $03A37 $05EB7
$0606B $0614E $062F7` reached through stubs and `$300D9 $3018F $30313 $3100B $31138` (bank 12) through script
operands. They include the three priority wrappers `$3901` and `$3A37` (both `$3A37` and `$3A48` entries). Some,
such as `$05EB7`/`$0606B`/`$0614E`, belong to the shared object-helper stubs below `$0380`, not to the player;
the common property is the proven entry, not the owner. The other claims stay reviewed flow claims: `$03138`, `$03BFB` do not end in a terminal instruction; `$30CB4`, `$30EE1`,
`$30F76` have relative branches that leave the run across embedded tables; `$30CFC`, `$30F3C` are not fully reached
from their entries and `$30FF0` has no entry of its own.

## Phase 4: ledger integration

* `player_scripts.dispatch_seeds(rom)` turns every parsed callback vector and executed operand into a
  review seed: `{"player_script": {type, state, command, field, operand_offset}}`. A resident target is its own file
  offset; a slot-2 target is bank 12.
* `decomp1a_review.py` uses these seeds beside the recovered dispatch tables, so every cluster entered by a script
  gains a supported entry; `rom_ledger.import_reviewed` re-derives the same seed from the ROM and rejects a stale
  or altered one (tested). Nothing is a hand-maintained address list.
* `tools/recover.py` registers `data/decomp1c/derived-regions.json`, which the tool computes; a test asserts the
  tool reproduces it.
* Simulation overrides (`script_seeds=False`, `drop_regions`) exist only for evidence reports; the default builder
  produces the committed `reviewed-ranges.json`. The DECOMP-1B report still describes the evidence as of 1B
  (it drops the 1C regions and seeds), and its test expectations were updated accordingly.

Newly classified through the seeds and stubs include the wrappers and callbacks in `$03783-$037CC`, `$0384D-$0386F`,
`$03901-$0393B`, `$03A37-$03A59`, `$03BFB-$03C15`, `$062F7-$0630B`, and the bank-12 script routines
`$300D9-$3010E`, `$3018F-$30194`, `$30313-$3031D`, `$30CB4-$30D36`, `$30EE1-$30F76`, `$30F76-$3100B` (partly),
`$3100B-$3103D` and `$31138-$31163`. Embedded tables inside those clusters (duration and selector tables) stay UNKNOWN.

## Unproven and uncertain

* All evidence is static. No claim that the game enters any of these states, executes any of these callbacks, or
  that a given selector is exercised; `callbacks.json` states the tier.
* The state-table length is inferred (it ends at the lowest script it points to). States beyond it are not parsed.
* Only player types 1 and 2 and the 16 commands were parsed. Scripts of other object types, which also reach the
  `$0320` stubs and the stub run via `$5E91`-style callbacks, are out of scope; that is why 46 stubs remain unproven.
* The bank assumption (bank 12 mapped while scripts and callbacks run) is read from `$3637-$364D` and `$1C6F`;
  a script command that remaps a bank before a later callback is not modelled.
* Executed operand words and callback vectors in slot 2 (35 distinct) are classified only where they fall in an
  existing unresolved audit cluster; elsewhere in bank 12 they are recorded, not claimed.
* The remaining unresolved clusters (23, 1,553 bytes) are listed in `reviewed-ranges.json`; DECOMP-1C did not touch
  the camera-adjacent, banked-manifest or type-`$28` script ranges. The `CALL $8000` into bank 28 at `$70000` is
  still ambiguous by rule.
* Naming: `dispatch_target_` marks the proof (proven entry through the dispatch mechanism), not a semantic role.

## Verification

* `python tools/decomp1c_callbacks.py <ROM>` regenerates `callbacks.json` and `derived-regions.json`; run twice with
  `python tools/recover.py <ROM>` between until stable (the committed state is a fixed point and re-running is
  idempotent), then `python tools/decomp1a_review.py <ROM>` and `python tools/rom_ledger.py <ROM>`.
* `python tools/rom_ledger.py <ROM> --check`, `python tools/decomp1b_callers.py <ROM>` (reproduces the committed 1B file)
  and `python tools/build_verify.py <ROM> --output build/d1c --wla-z80 ... --wlalink ...`
  (`byte_identical: true`, 113 regions, 13,988 bytes).
* `python -m unittest tests.test_decomp1c tests.test_decomp1b tests.test_decomp1a tests.test_rom_ledger` (80 tests).

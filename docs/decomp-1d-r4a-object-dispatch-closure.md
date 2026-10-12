# DECOMP-1D-R4A - Residual Object Dispatch Closure

Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Base commit `8af1f0366a3620d20b0a1341017d272968c5cfbb` (Research `main` after the DECOMP-1D-R3 integration; R3 was verified to be on `main` before branching).

Evidence: `data/decomp1d/r4a-object-dispatch-closure.json` (generated, deterministic). Generator: `tools/decomp1d_r4a_object_dispatch.py`.
Tests: `tests/test_decomp1d_r4a.py`. Reconciliation with the accepted Special Stage work: `docs/decomp-1d-r4a-reconciliation.md`.

This milestone resolves the four computed jumps DECOMP-1D-R3 left open (`$314F4`, `$6972`, `$77EC`, `$6C98`). It is static, ROM-derived work: no
controlled run was needed and none is claimed. It promotes no banked assembly, edits neither the ledger nor the recovery manifest, touches no
Special Stage art, cache or manifest, and does not look at the graphics decompressor (R4B).

## 1. Executive summary

<!-- r4a-generated:begin -->

| Dispatcher | Bound | Verdict |
|---|---|---|
| `$6972` floor dispatcher | D364 & $1F; surfaces present 0,1,2,3,4,5,7,9,10,11,12,13,14,16,18,19,20,22,23,24,25,26,27,28,29,30; $1F absent | **CLOSED (premise-conditional: P1-P6)** |
| `$77EC` second dispatcher | same index, same domain | **CLOSED (premise-conditional: P1-P6)** |
| `$6C98` surface-16 sub-dispatcher | block ids 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 131 | **CLOSED (premise-conditional: P1-P6)** |
| `$314F4` bank-12 callback dispatch | gate surface $17, block ids 88-115, 28 of 28 entries | **CLOSED (premise-conditional: P1-P6)** |

| Question | Answer |
|---|---|
| Completely bounded and resolved | yes, all four (premise-conditional) |
| Adds object types beyond R3's closure (itself a superset of the accepted placed census) | no |
| Reaches the level-clear callback or type $61 | no |
| Object-creation closure | **PARTIAL** |
| U1 | **PARTIAL** (route A excluded_so_far, route B excluded_so_far) |

Closure types (all five stages, with the new edges): $01, $02, $03, $05, $06, $07, $0C, $0F, $10, $11, $13, $26, $2F, $31, $37, $3A, $3D.

<!-- r4a-generated:end -->

All four sites are **terrain-surface dispatchers of the shared collision engine**, not object-creation code. Their index is the surface byte (or
the block id) that the block-lookup routines `$7666`/`$7725` read from the block header table; R3 saw them only as `JP (HL)` inside the callback
closure of the two player types and a handful of objects. Because the index domain is the header table - 256 block ids, two planes, ROM constant -
it can be enumerated completely, whatever the layout contains.

| Site | Instruction pattern (re-derived) | Index domain | Out-of-table word reachable? |
|---|---|---|---|
| `$6972` | `LD A,(D364)`, `AND $1F`, `ADD A,A`, table `$6973` | surfaces of all 256 ids: 26 values, `$1F` absent | no |
| `$77EC` | same index, table `$77ED` | same | no |
| `$6C98` | `D36B - $48`, `ADD A,A` (8-bit), table `$6C99` | ids `$48-$57` and `$83` (the surface-16 blocks) | no |
| `$314F4` | gate `D364 & $3F == $17`, then `(D353 - $58) * 2` | ids `$58-$73` (the surface-23 blocks) | no |

## 2. Method

1. **Re-derive the instructions.** Each jump is decoded in place and compared with its specification; the generator raises if a byte differs.
2. **Find the feeders.** A byte search of the whole image lists every absolute access to `D364` (surface byte), `D353` (block id), `D36B` (its copy)
   and `D2E0` (header-table pointer). Writers: `D364` at `$76DC $76EE $77A2 $77BD`; `D353` at `$76CB $7792 $77B8`; `D36B` at `$6955` only; `D2E0` at
   `$2A71` only. None of the four has an address-constant (`LD HL,nn`) materialisation, so no pointer to them is built in code.
3. **Enumerate the domain.** Every block id 0-255, both header planes (`rom.header(id, plane)`: byte 0, and the `+7` alternate read when bit 5 is set).
   The surfaces present are 0-5, 7, 9-14, 16, 18-20, 22-30; absent 6, 8, 15, 17, 21 and **31**.
4. **Check the pairing.** The bound on `$6C98` and `$314F4` uses the block id (`D36B`/`D353`) together with the surface (`D364`); that is only valid if
   both come from one lookup. Between the lookup and the jump the code is: `$6F61`-reach (212 instructions, no writer, no lookup call) for `$6972`/`$6C98`;
   `$70E7`-reach (139) for `$77EC`; eleven straight instructions for `$314F4` (the only transfer is the gate's `JP nz`). The IM 1 closure of
   DECOMP-1D R2 (3,584 instructions) contains no writer, no lookup entry and not the `D2E0` store.
5. **Follow the destinations.** Every table word used is checked to decode in the window its jump runs in (resident, or bank 12 slot 2). The code
   behind them is followed by recursive descent, with the table jumps it meets resolved (the four here, `$5FB8` and `$311BB` from R3). Creation sites and
   routes to the level clear are read from that closure.

## 3. Per-dispatcher results

### 3.1 `$6972` and `$77EC` (masked dispatchers)

Both read `D364 & $1F` and index a 31-word table (`$6973`-`$69B0`, `$77ED`-`$782A`). The 32nd word is `$DDC9`, a RAM address formed from code bytes. It is
reached only by index 31. `D364` takes the surface byte of the block header, so index 31 needs a header with low five bits `$1F`: **none of the 256
ids has one**, in either plane. `D364` is also set to 0 when the lookup leaves the layout (`$77BD`). `D2E0` is stored once, at `$2A71`, from the first word of
the loader record; that word is `$8000` in all nine verified records, so the table is the ROM table at `$38000` for every act of zones 0-15 with act <= 2,
the five stages included. Index 31 is therefore unreachable under the premises of section 5. The destinations are the 26 handlers of the surfaces present;
the entries of the absent surfaces (6, 8, 15, 17, 21) are never indexed.

### 3.2 `$6C98` (the surface-16 sub-dispatcher)

`$6C82` is the surface-16 floor handler (entry 16 of the `$6973` table). It reads `D36B`, branches to `$6CB9` for `$83`, returns for ids below `$48` and
otherwise dispatches on `(id - $48) * 2` (8-bit) into `$6C99`. The table is **16 words** (`$6C99`-`$6CB8`; the first destination `$6CB9` follows it),
covering ids `$48-$57`. The ids whose header has surface 16 are exactly `$48-$57` and `$83`. The word after the table is `$DDC9` again, but index 16 would need
id `$58`, whose surface is 23. The instruction semantics were cross-checked with the fail-closed interpreter for all 256 ids (no mismatch). Destinations:
`$6CB9` (ids `$48-$4F`, `$83`), `$6CBA` (`$50-$51`), `$6CCD` (`$52`), `$6CE5` (`$53-$57`). R3 had no specification for this jump.

### 3.3 `$314F4` (the bank-12 callback dispatch)

Reached only after `D364 & $3F == $17` (surface 23). `(IX+$38) & 3` picks one of four 28-word sub-tables (spacing checked), then `(D353 - $58) * 2` indexes it. The
ids whose header byte has `& $3F == $17` are `$58-$73` - 28 ids, 28 entries: index 0-27, the whole sub-table and nothing beyond. No destination is outside
`$8000-$BFFF`; all 112 words decode (45 distinct). R3 called this jump unbounded because no instruction bounds the index; the **gate** does.

## 4. Object-creation closure and U1

* The destinations of `$6C98` and `$5E6F` (see 4.1) contain **no creation site** (one destroy marker). The destinations of `$314F4` contain none. The surface handlers behind
  `$6972` contain nine allocator calls, all with immediate types in R3's closure (`$06 $07 $0F $13 $37 $3A`); `$77EC` handlers create nothing.
* Per stage, the natural closure recomputed with every new edge is **identical** to R3's (15-16 types, none a trigger type). The four sites introduce no object
  type outside the R3 closure, and the types the closure adds beyond the accepted placed census (`$10 $26 $2F $31`) were already R3's; they come from the player
  and the shared engine, not from these jumps.
* No destination reaches a level-clear caller (`$32B9B $781DF $79D55`), a bit-4 setter (`$303ED $7BB2A $7BB6E`) or a `CALL/JP $03F5/$4892`. Type `$61` is not created.
* **Object-creation closure: PARTIAL.** **U1: PARTIAL, unchanged in verdict.** The four jumps no longer keep it open, but R3's evidence lists two more resident computed
  jumps that R3's prose does not name (4.1), and the out-of-domain placement lists remain R3's open items. Nothing here promotes U1 to proven or excluded.

### 4.1 Two further resident jumps, not named by R3

R3's JSON (`creation.frame_loop.computed_jumps_not_followed`) lists `$5E6F`, `$5E9A`, `$6695` for the per-frame code; its prose names only the four. `$5E6F`
is bounded by `AND 15` into a 16-word table (`$5E70`-`$5E8F`; destinations `$5E90 $5EF8 $626D`) and was followed here as part of the new closure.
`$5E9A` (`JP (HL)` with HL = the per-object callback pointer `(IX+12)`) and `$6695` (the script-command dispatcher, index = the byte after `$FF`) are **open**: their
domains are script data and the object state, which this task did not enumerate. They are the reason the route status stays `excluded_so_far`.

## 5. Premises and what remains open

* **P1** every block id 0-255 is possible; the bounds hold for all of them.
* **P2** `D2E0 = $8000` (nine verified records). Records outside them (R3 U3) can change it; the bounds do not cover those.
* **P3** the listed writers are the only writers of `D364/D353/D36B/D2E0`. Register-addressed stores and the unresolved block moves of DECOMP-1D R2 (inherited U5) are not excluded.
* **P4** the IM 1 closure does not run the lookups; its transfers into slot-2 code (`partial_dispatch` edges at `$8137 $74027 $741F1`) are recorded, not followed (R3 P3).
* **P5** byte-search hits that are not instructions of known code: for `$77EC`, two in data banks 7 and 8 (`CALL PE,$77EC`) are not shown to be data; for `$6C98`, two
  in banks 5 and 6; for `$6972`, three `CALL $690B` encodings in bank 0. They are reported, not dismissed, and the conclusions assume they are not executed. All hits that are
  instructions of known code target the expected entry points (`$690B/$691A`, `$77CB`).
* **P6** standard Sega mapper semantics and R3's slot premises.

Verdict wording: **CLOSED (premise-conditional)** means the index domain is fully bounded and every destination resolved *under P1-P6*. It is not hardware validation and not a
claim about code reached through an unexplored predecessor.

## 6. Special Stage implementation interface (short handover)

The canonical implementation manifest (`data/rom-cache/special-stages/implementation-manifest.json`) stays the only source of truth; nothing here duplicates it.

* **Usable now, unchanged:** stage indexing, entry gate and exit contract, the five layouts and block tables, ring and object placements, the surface handlers, and the object contracts `$10`, `$26`, `$2F`, `$31`.
* **Residual dispatchers that affect ordinary implementation: none.** `$6C98` and `$314F4` are not reached by any stage layout (stage surfaces are 0, 1, 2, 3, 7, 9, 10, 12, 13, 19, 20, 22, 29; surfaces 16 and 23 are absent), and
  `$6972`/`$77EC` are the shared floor/second dispatchers the manifest already records (`floor_handler` per surface matches the table here).
* **Newly established creation behaviour (static, not a gameplay claim):** the surface handlers create objects. In stage surfaces: surface 1 creates type `$3A` (the accepted audit has surface 1 inert outside zone 5),
  surface 12 type `$13`, surface 13 type `$07`, surface 22 type `$0F` (SS4's 11, 41 and 12 cells). These are creation sites reachable in the handler code; whether a given site executes depends on the handler's own conditions, which this
  task did not trace. Existing accepted contracts (springs, crumble, breakable in SS4) already cover the visible behaviour; the POC should keep using them.
* **Act 3:** dormant. See the reconciliation document.

## 7. Verification

* `python3 -m unittest tests.test_decomp1d_r4a` (synthetic tests plus canonical-ROM tests).
* Earlier Special Stage tests (`tests.test_ss_*`), the R1-R3 tests and `tests.test_rom_ledger` re-run; `python3 tools/rom_ledger.py --check`; `git diff --check`.
* `python3 tools/decomp1d_r4a_object_dispatch.py --check` compares a fresh run with the committed JSON byte for byte.
* Baseline unchanged: 156,887 classified bytes, 13,988 recovered bytes, 113 recovered regions, 367,401 UNKNOWN bytes, zero contradictory claims.

## 8. Unresolved items

* R4A-1: `$5E9A` and `$6695` (section 4.1).
* R4A-2: indirect writers of the feeder variables (inherited U5).
* R4A-3: records outside the verified nine (inherited U3).
* R4A-4: the IM 1 slot-2 transfers.
* R4A-5: act-3 reachability through original gameplay rests on the accepted ring census.
* R4B: termination of the graphics decompressor on out-of-table rows, not investigated here.

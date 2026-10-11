# ROM address ledger (DECOMP-0)

Long-term objective: a complete, documented, reproducible disassembly of
Sonic Chaos (Europe) v1.2. This document describes the **measurement
infrastructure** for that objective, not a disassembly. The ledger answers
three questions for every one of the 524,288 ROM bytes: *what kind of byte is
it, how do we know, and has it been recovered into reproducible source?*

Files:

| File | Role |
|---|---|
| `tools/rom_ledger.py` | generator (Python 3.8+; 3.13 is the tested choice) |
| `data/rom-ledger/ledger.json` | machine-readable ledger (metadata only, deterministic) |
| `data/rom-ledger/summary.md` | generated human-readable summary (totals, 32 banks, largest gaps) |
| `tests/test_rom_ledger.py` | accounting, bounds, bank-split, manifest, overlap and determinism tests |

Nothing in the output contains ROM bytes, graphics or audio. Offsets, lengths,
names, counts and source paths only.

## Data model

* **File offsets are authoritative.** Intervals are zero-based and half-open
  `[start, end)`. The ROM is 32 banks of 16 KiB (`0x4000`); no segment crosses
  a bank boundary.
* Bank/CPU addresses are derived, never primary: `cpu_paged = 0x8000 + offset % 0x4000`
  (the address when the bank sits in slot 2) and, for banks 0 and 1 only,
  `cpu_resident = offset` (the always-mapped engine region; see
  `tools/level_package.py` `row_offset_table`). The ledger does not assert
  which CPU view a given routine uses.
* A **claim** is one source's statement about one exact range: `start`, `end`,
  `primary` class, optional `subtype`, `subsystem` and `logical_content`,
  `recovered` flag, `evidence` quality, `basis`, `sources`, `names`, `importers`.
  Exact duplicates from different sources are merged and keep all their sources.
* A **segment** is a maximal run of bytes covered by the same set of claims
  (`claims` lists claim ids). The segments tile `[0, 524288)` with no gap and no
  overlap. Bytes covered by no claim are `UNKNOWN`.
* **Primary class** (exactly one per byte): `CODE`, `DATA`, `GRAPHICS`, `MUSIC`,
  `COMPRESSED`, `PADDING`, `UNKNOWN`.
* **Separate semantic fields:** `subtype` (e.g. `object-placement-list`),
  `subsystem` (e.g. `level-zone-3`, `object-type-$18`, `sound`),
  `logical_content` (for `COMPRESSED`: what the stream decodes to),
  `recovery` (`recovered` / `not_recovered`), `evidence`, `classification_basis`
  (`independent`, `recovery_manifest_only`, `contested`, `none`) and
  `regions` (recovered-region names).

### Class definitions used so far

| Class | Used for |
|---|---|
| `CODE` | Z80 instructions: recovered regions with `kind: code`, and audit-manifest ranges that state `kind: code` and whose SHA-256 matches the ROM |
| `DATA` | tables and records: pointer tables, headers, object lists, block-mapping tables, collision headers and profiles, movement tables |
| `GRAPHICS` | uncompressed pixel/colour content. Today: 12 CRAM palettes only. Tile-index maps (block mappings) are `DATA`, not graphics |
| `MUSIC` | none proven. The sound pointer table is `DATA` (subsystem `sound`); no track extent is established |
| `COMPRESSED` | any compressed stream, with `logical_content` naming the payload (level layout cells, tile graphics) |
| `PADDING` | none. A zero- or `$FF`-filled interval is **not** padding on its own (see below) |
| `UNKNOWN` | everything not yet proven, including contested bytes |

## Evidence standards

A claim is imported only when **both boundaries and the class** are supported:

| `evidence` | Meaning | Examples |
|---|---|---|
| `byte_verified_assembly` | registered in `asm/recovered/regions.json`; `tools/build_verify.py` reassembles the ROM byte for byte | the 74 recovered regions |
| `decoder_verified` | an existing decoder/loader consumes exactly these bytes and the extent is recomputed from the ROM on every run | level layout RLE streams (end at the `count 0` terminator), tile streams (header + payload + command bytes; the payload end must equal the command start or the stream is rejected), object lists (to the `$FF` terminator) |
| `structure_verified` | fixed-size record/table read by a loader, or a committed export the ROM bytes must reproduce | act headers (22 B), art-load entries (7 B), palette records (16 B), collision profile arrays (32 B), sound/state/twist pointer tables |
| `manifest_hash_verified` | audit manifest range whose SHA-256 matches the ROM **and** which states `kind` | `data/rom-cache/object-18-act-clear.json`, `thz3/object-50.json` |
| `manifest_copy` | cache copy of a recovered region; must match a registered region's exact range and kind (else rejected), and counts as recovery-manifest evidence, never independent | `thz1/object-census.json` |

Deliberately **not** done:

* A pointer target is not an extent. Sound track starts, state-script targets,
  mapping-frame pointers and so on are not imported; only the pointer words and
  fixed-size records are.
* Fill patterns are not padding. Inside UNKNOWN there are 629 runs of at least
  32 `$00` bytes (33,616 bytes) and 26 runs of at least 32 `$FF` bytes (47,393
  bytes); none is classified, because blank-looking bytes can be data, unused
  space or code operands.
* Content is not inferred from neighbours.
* Audit ranges that hash correctly but state no `kind` are **not** guessed
  from their name or purpose text. They are listed under
  `unclassified_range_claims` (211 ranges, 14,310 bytes in union, 3,961 of those
  bytes still UNKNOWN) as the cheapest future wins.
* Zone index 6 is not imported: the act-header table aliases it onto zone 0
  (six real zones x three acts = 18 acts).

### Overlaps

Claims are compared pairwise.

* **Identical** claims merge.
* **Nested, same class** is compatible. The narrowest claim supplies
  `subtype`/`subsystem`/`logical_content`; all claims remain listed.
  Example: `data/movement-tables.csv` entries inside the recovered
  `movement_tables` region (375 nested pairs in the initial ledger).
* **Partial overlap, same class** is compatible but listed in `overlaps.partial`
  (none initially).
* **Different classes** are *contradictory*. The overlapped bytes become
  `UNKNOWN`, are marked `contested`, and the pair is listed in
  `overlaps.contradictory`. Nothing is chosen silently.

### Structurally identified versus recovered

These are two independent measurements.

* **Structurally identified** = the byte has a primary class other than UNKNOWN,
  i.e. we know what *kind* of byte it is and where its structure ends. Most of
  this ledger's coverage is structural: a 4,096-cell layout stream is
  identified (`COMPRESSED`, exact extent) although nothing in it is assembly
  source.
* **Recovered into reproducible source** = the byte lies inside a region of
  `asm/recovered/regions.json`, which `tools/build_verify.py` reassembles and
  compares with the ROM. The `recovery` field and `recovered_*` totals track
  this only.

Consequences:

* Recovering bytes that were already structurally identified (for example a
  table with an independent decoder) raises source coverage and leaves
  structural coverage unchanged.
* Bytes recovered but never independently identified are reported separately
  as `classified_by_recovery_only_bytes` (10,799 initially). Their class comes
  from the recovery manifest's own `kind`, so the headline structural figure
  includes them, and `independent_structural_bytes` (142,681) shows the part
  with outside evidence. Recovering a previously UNKNOWN region will therefore
  add to the classified total through the manifest's `kind` and is visible as
  `recovery_manifest_only`, never as independent evidence.
* A recovered region that a manifest contradicts stays `recovered` while its
  class is contested.

## Regeneration

Current carrier-contract correction accounting (2026-10-11): **154,108**
structurally classified bytes, **13,046** assembly-recovered bytes, and
**370,180** UNKNOWN bytes. Independently evidenced classification is 143,404
bytes. The seven exact, hash-verified carrier/helper CODE claims in
`data/rom-cache/eez/carrier-17.json` add 628 previously UNKNOWN bytes; they do
not recover assembly or resolve the 32 contested bytes at `$06696..$066B6`.
Earlier baseline figures in this document describe the initial DECOMP-0 ledger.

```bash
python tools/rom_ledger.py "path/to/Sonic Chaos (Europe).sms"      # writes data/rom-ledger/
python tools/rom_ledger.py "path/to/Sonic Chaos (Europe).sms" --check   # exit 1 if committed files are stale
python -m unittest tests.test_rom_ledger
```

The ROM path may also come from `SONIC_CHAOS_ROM`. The tool refuses any file
that is not 524,288 bytes with SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Output is deterministic (stable ordering, no timestamps or commit ids, LF
newlines). Tests that need the ROM skip when it is absent; the remaining tests
check the committed ledger alone. Re-run the generator whenever
`regions.json`, a committed export, or an audit cache changes; the
`--check`/test pair fails when the ledger is stale.

Importers (all in `tools/rom_ledger.py`):

1. `import_recovered`: every region of `asm/recovered/regions.json`, bounds and
   bank checked, never hard-coded.
2. `import_level_structures`: for the 18 acts, uses `tools/level_package.py` to
   locate act headers, layout streams, object lists, player-start records,
   art-load entries, supplemental lists, tile streams, palette selectors and
   palettes, plus the block-mapping pointer tables and the 32-byte blocks the
   layouts use.
3. `import_collision`: pointer table `$38000`, 272 seven-byte surface headers
   and the 129 distinct 32-byte profile arrays (`tools/rom.py`).
4. `import_pointer_tables`: sound, player-state-script, twist-dispatch,
   movement-table and surface-modifier exports (each entry re-checked against the
   ROM).
5. `import_layout_manifests`: layout descriptors in the zone and special-stage
   implementation manifests, re-decoded; this adds the five special-stage layouts.
6. `import_manifest_ranges`: hash-verified audit ranges (class only when `kind`
   is stated) and cache copies of recovered regions.

## Initial result

| Category | Bytes | % of ROM |
|---|---:|---:|
| CODE | 14,681 | 2.800 |
| DATA | 38,631 | 7.368 |
| GRAPHICS | 192 | 0.037 |
| MUSIC | 0 | 0.000 |
| COMPRESSED | 99,976 | 19.069 |
| PADDING | 0 | 0.000 |
| UNKNOWN | 370,808 | 70.726 |
| **Total** | **524,288** | 100 |

| Coverage metric | Bytes | % of ROM |
|---|---:|---:|
| Recovered into reproducible assembly | 13,046 | 2.488 |
| Structurally classified (primary class known) | 153,480 | 29.274 |
| &nbsp;&nbsp;independently evidenced | 142,681 | 27.214 |
| &nbsp;&nbsp;classified only by the recovery manifest | 10,799 | 2.060 |
| Recovered and independently evidenced | 2,215 | 0.422 |
| UNKNOWN | 370,808 | 70.726 |
| of which contested | 32 | 0.006 |

Recovered manifest, recalculated by the generator: 74 regions, 13,046 bytes (11,060 code, 1,986 data). 32 of the data bytes are the contested pair described below, so the ledger counts 11,060 recovered CODE and 1,954 recovered DATA bytes.

The generator tallies 1,622 claims, 1,808 segments, 375 compatible nested overlaps, 0 partial overlaps and 1 contradictory pair; 0 claims were rejected.

## 32-bank summary

| Bank | File range | Code | Data | Graphics | Compressed | Unknown | Recovered | Classified |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | `00000-03FFF` | 2,419 | 0 | 0 | 0 | 13,965 | 1,531 | 14.8% |
| 1 | `04000-07FFF` | 6,900 | 2,085 | 0 | 0 | 7,399 | 7,137 | 54.8% |
| 2 | `08000-0BFFF` | 0 | 136 | 0 | 0 | 16,248 | 0 | 0.8% |
| 3 | `0C000-0FFFF` | 0 | 0 | 0 | 0 | 16,384 | 0 | 0.0% |
| 4 | `10000-13FFF` | 0 | 0 | 0 | 0 | 16,384 | 0 | 0.0% |
| 5 | `14000-17FFF` | 0 | 0 | 0 | 0 | 16,384 | 0 | 0.0% |
| 6 | `18000-1BFFF` | 0 | 0 | 0 | 0 | 16,384 | 0 | 0.0% |
| 7 | `1C000-1FFFF` | 0 | 0 | 0 | 0 | 16,384 | 0 | 0.0% |
| 8 | `20000-23FFF` | 0 | 0 | 0 | 2,130 | 14,254 | 0 | 13.0% |
| 9 | `24000-27FFF` | 0 | 0 | 0 | 7,949 | 8,435 | 0 | 48.5% |
| 10 | `28000-2BFFF` | 0 | 0 | 0 | 0 | 16,384 | 0 | 0.0% |
| 11 | `2C000-2FFFF` | 0 | 0 | 0 | 0 | 16,384 | 0 | 0.0% |
| 12 | `30000-33FFF` | 2,234 | 1,066 | 0 | 0 | 13,084 | 2,241 | 20.1% |
| 13 | `34000-37FFF` | 0 | 0 | 0 | 0 | 16,384 | 0 | 0.0% |
| 14 | `38000-3BFFF` | 0 | 6,544 | 192 | 0 | 9,648 | 0 | 41.1% |
| 15 | `3C000-3FFFF` | 0 | 54 | 0 | 0 | 16,330 | 54 | 0.3% |
| 16 | `40000-43FFF` | 0 | 0 | 0 | 11,907 | 4,477 | 0 | 72.7% |
| 17 | `44000-47FFF` | 0 | 11,648 | 0 | 0 | 4,736 | 0 | 71.1% |
| 18 | `48000-4BFFF` | 0 | 0 | 0 | 15,693 | 691 | 0 | 95.8% |
| 19 | `4C000-4FFFF` | 0 | 0 | 0 | 0 | 16,384 | 0 | 0.0% |
| 20 | `50000-53FFF` | 0 | 10,496 | 0 | 2,418 | 3,470 | 0 | 78.8% |
| 21 | `54000-57FFF` | 0 | 0 | 0 | 15,885 | 499 | 0 | 97.0% |
| 22 | `58000-5BFFF` | 0 | 0 | 0 | 12,770 | 3,614 | 0 | 77.9% |
| 23 | `5C000-5FFFF` | 0 | 0 | 0 | 13,319 | 3,065 | 0 | 81.3% |
| 24 | `60000-63FFF` | 0 | 0 | 0 | 12,309 | 4,075 | 0 | 75.1% |
| 25 | `64000-67FFF` | 0 | 0 | 0 | 0 | 16,384 | 0 | 0.0% |
| 26 | `68000-6BFFF` | 0 | 0 | 0 | 5,596 | 10,788 | 0 | 34.2% |
| 27 | `6C000-6FFFF` | 0 | 0 | 0 | 0 | 16,384 | 0 | 0.0% |
| 28 | `70000-73FFF` | 318 | 5,869 | 0 | 0 | 10,197 | 83 | 37.8% |
| 29 | `74000-77FFF` | 124 | 0 | 0 | 0 | 16,260 | 0 | 0.8% |
| 30 | `78000-7BFFF` | 2,686 | 733 | 0 | 0 | 12,965 | 2,000 | 20.9% |
| 31 | `7C000-7FFFF` | 0 | 0 | 0 | 0 | 16,384 | 0 | 0.0% |

`MUSIC` and `PADDING` are 0 in every bank. `summary.md` carries the same table with those columns.

## Significant proven regions

* **Recovered assembly:** 74 regions, 13,046 bytes (11,060 code, 1,986 data),
  banks 0, 1, 12, 15, 28, 30. Dense in bank 1 (engine: terrain, collision, object
  dispatch) and bank 0 (player movement, state setters).
* **Level layouts:** 23 RLE streams, 52,911 bytes: 18 acts (banks 18, 20, 21,
  23) and the five special stages (`0x68000-0x695DC`, bank 26). Each re-decodes
  to its terminator.
* **Tile graphics streams:** 35 distinct level-art streams, 47,065 bytes, in
  banks 8, 9, 16, 22, 24.
* **Block mappings:** six 512-byte pointer tables (`0x44000`, `0x45640`,
  `0x46A40`, `0x50000`, `0x51320`, `0x524E0`) and the 596 distinct 32-byte
  blocks the layouts reference.
* **Object placement lists:** 18 lists, 4,797 bytes, `0x705AE-0x7186B`.
* **Collision:** pointer table, 272 headers, 129 profile arrays
  (`0x38000-0x39990`).
* **Pointer tables:** 68 sound pointers (`0x090E1-0x09169`), 61 player-state
  script pointers (`0x30000-0x3007A`), 112 twist dispatch pointers.
* **Palettes:** 12 distinct 16-byte records.

## Contradictory claims

One pair, 32 bytes (`0x06696-0x066B6`):

* `data/rom-cache/thz3/object-50.json` routine `anim_cmd_dispatch` claims
  `0x6680-0x66B6` as one `CODE` routine (hash matches those bytes);
* `asm/recovered/regions.json` registers `animation_command_dispatch`
  `0x6680-0x6696` as code and `animation_command_table` `0x6696-0x66B6` as data.

The ledger keeps the 32 table bytes UNKNOWN/contested (still `recovered`).
The likely explanation is a loose routine boundary in the audit, but that is a
conclusion for a reviewer, not something the ledger assumes. Resolving it
means correcting the audit boundary or the recovered split with evidence.

## Unresolved areas

* 370,180 bytes (70.6 %) remain UNKNOWN. Twelve banks have no claim at all:
  3, 4, 5, 6, 7, 10, 11, 13, 19, 25, 27, 31.
* `MUSIC`, `PADDING` and uncompressed `GRAPHICS` (beyond palettes) are 0 bytes
  by evidence standard, not by absence in the ROM.
* Sound data (bank 2 after `0x09169`, and the targets of the 68 pointers) has
  no established extents.
* Sprite/object art streams, object mapping frames, animation scripts and the
  targets of the player-state script pointers are referenced by tools but lack
  proven extents.

## Recommended next regions

Ordered by evidence per effort.

1. **Classify the 211 hash-verified, kindless audit ranges** (14,310 bytes,
   3,961 still UNKNOWN). Their unknown bytes lie in banks 0, 1, 12, 28, 29 and 30. A kind decision per range converts them without new reverse
   engineering.
2. **Resolve the object-50 / animation-table contradiction** (32 bytes) above.
3. **Bank 2 `0x08000-0x0BFFF` (16,248 bytes unknown):** the sound pointer table sits at
   `0x090E1`; derive track extents from the sound header format before
   attempting `MUSIC`.
4. **Special-stage neighbourhood, bank 26 `0x695DC-0x6BFFF` (10,788 bytes):**
   directly follows the five proven special-stage layouts.
5. **Bank 12 gaps around the recovered object scripts** (`0x3040F-0x314C0`,
   4,274 bytes) and the state-script targets after `0x3007A`.
6. **Bank 14 `0x39990-0x3B6AC` (7,453 bytes)** between the proven collision
   profiles and the palette records.
7. **Bank 28 `0x7186B-0x73FFF` (10,133 bytes)** after the last object list.
8. **Bank 1 and bank 0 engine gaps** (7,191 and 13,965 bytes) around recovered
   code, and the startup/interrupt area `0x0000-0x1332`.
9. **Banks 3-7** (82 KB, no claims): start from the loaders that select them
   (art-load entries and mapping-pointer tables already reference banks 8, 9, 16,
   22, 24) rather than from content guesses.

## AGENTS.md candidate update (for Manager-san; not applied)

Under *Research Workflow*:

> Whole-ROM accounting lives in `data/rom-ledger/` (`tools/rom_ledger.py`,
> `docs/rom-address-ledger.md`). When a task proves or recovers ROM ranges, rerun
> the generator and commit the refreshed ledger. Structural identification and
> recovery into `asm/recovered` are separate metrics; a new range claim needs
> exact boundaries plus a stated class, and a hash-verified range without a
> stated `kind` is reported, not guessed.

## Infrastructure notes

* The default `python` on this workstation is 3.7.4. The tool and tests were run
  with `py -3.13`; the repository requires 3.8+.
* `python tools/build_verify.py` needs WLA-DX (`wla-z80`, `wlalink`); see the
  verification record in the handover report.
* The ledger imports `tools/level_package.py`, `tools/rom.py` and
  `tools/tile_decompress.py`; changes to those decoders can change the ledger
  and are caught by `--check`.

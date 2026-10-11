# DECOMP-1A: classification from existing evidence

Branch `research/decomp-1a-existing-evidence`, from Research `main` `c42c86a`. Scope: resolve the
211 hash-verified ROM ranges that DECOMP-0 left without a content kind, and the one 32-byte
CODE/DATA contradiction, using evidence Research already holds. No new engine analysis, no
assembly recovery, no POC or root `AGENTS.md` changes.

## Method and evidence standard

A SHA-256 match proves a range, not its type. A kind is accepted only from the ROM itself:

* **CODE** by control flow (`tools/rom_flow.py`, built on the existing `z80dis` decoder). An entry point
  is control-flow-supported when a CALL/JP/JR/DJNZ at an instruction of byte-verified recovered code (or of a claim
  already supported this way) targets it, or it is a word of a recovered dispatch table whose address
  recovered code loads and whose consumer jumps through `JP (HL)`. A slot-2 target is attributed to the
  caller's own bank only when the caller itself executes in slot 2; a resident caller reaching a slot-2
  address is ambiguous and never used. Recursive descent confined to the audit range(s) must then fetch
  every claimed byte as an instruction and may not touch a recovered DATA region.
* Names, purposes and neighbouring regions were not used as evidence. Audit text is kept only as
  provenance (`names`, `sources`).
* Only bytes that were UNKNOWN are claimed. Re-describing already classified bytes would add no
  coverage and, for recovered code, would be circular.

`data/rom-ledger/reviewed-ranges.json` is produced by `tools/decomp1a_review.py` and consumed by
`rom_ledger.import_reviewed`, which does not trust it: every review is re-proven from the ROM and
`regions.json` on each build (to a fixed point, so file order is irrelevant) and a stale or inconsistent
entry raises instead of being skipped. Each review records exact bounds, bank, audit provenance, the
proven entries and their proofs, the claimed runs, the verification method and the remaining
uncertainty (statically reachable CODE only; no execution trace; the routine's purpose is audit text).

## Evidence tiers

The ledger keeps three kinds of evidence apart, and this task adds only the middle one:

1. **Byte-verified recovered assembly**: reassembled byte for byte by `tools/build_verify.py`.
2. **Static control-flow evidence ("statically reachable CODE")**: instructions that recursive descent reaches
   from supported entry points. It shows the bytes decode and are reachable by branches from known code. It
   does not show that the game ever executes them, and says nothing about purpose. Recorded as
   `reviewed_flow_verified`.
3. **Original-ROM execution traces**: actual Z80 PC and mapper observations from the unmodified game. None
   are used yet; they are the recommended way to confirm tier 2 and to resolve banked routines.

Decoding uses each instruction's real CPU address (`rom_flow.cpu_address`: resident banks 0/1 at their file
offset, other banks at `$8000 + offset % $4000`), so relative `JR`/`DJNZ` targets are true CPU addresses.
Every recorded seed of a review must be supported; a review with any unsupported seed is rejected.

## 1. Baseline and final totals

| | DECOMP-0 | After task C | DECOMP-1A final |
|---|---:|---:|---:|
| CODE | 14,681 | 14,681 | 15,541 |
| DATA | 38,631 | 38,663 | 38,663 |
| GRAPHICS | 192 | 192 | 192 |
| MUSIC / PADDING | 0 | 0 | 0 |
| COMPRESSED | 99,976 | 99,976 | 99,976 |
| UNKNOWN | 370,808 | 370,776 | 369,916 |
| Contested | 32 | 0 | 0 |
| Structurally classified | 153,480 | 153,512 | 154,372 |
| Independently evidenced | 142,681 | 142,713 | 143,573 |
| Recovered assembly | 13,046 | 13,046 | 13,046 |

"After task C" is the contradiction fix alone. Recovered assembly is unchanged: structural
classification is not source recovery, and `regions.json` and `asm/recovered` were not touched.

## 2-3. Candidate ranges reviewed

211 ranges reviewed. Status is measured on the final ledger (`bytes_by_class` and `status` per range
in `unclassified_range_claims`):

| Status | Before | After |
|---|---:|---:|
| Fully classified (no UNKNOWN byte) | 130 | 156 |
| Partially classified | 6 | 7 |
| Unresolved (all bytes UNKNOWN) | 75 | 48 |

Of the 211, 26 moved from unresolved to fully classified and 1 from unresolved to partial. The
ranges' bytes overlap one another, so the union is the meaningful byte figure: 14,310 bytes, of which
UNKNOWN fell 4,064 -> 4,032 (task C) -> 3,172.

## 4. Net newly classified UNKNOWN bytes

**892 bytes**: 860 CODE (16 reviews, 16 claims) plus 32 DATA (the animation pointer table, task C).

The 16 reviewed CODE claims:

| Review | Bytes (file offset) | Entry proofs | Audit provenance |
|---:|---|---:|---|
| 0 | `0033B-0033E` | 1 | overlap_object_wrapper_033b |
| 1 | `01C6F-01C76` | 1 | (unnamed in cache) |
| 2 | `03138-0314A` | 1 | ring_counter_3138 |
| 3 | `03FEF-0401A` | 2 | player_step_3fef, player_update_3fef |
| 4 | `048A7-04A33` | 23 | facing_48A7, facing + damage gate $48BC + death, damage_dispatch_48bc, |
| 5 | `05E9C-05EB7` | 3 | (unnamed in cache) |
| 6 | `05EB7-05EE1` | 3 | (unnamed in cache) |
| 7 | `05F27-05F3D` | 1 | owner positioning helper $5F27 |
| 8 | `0606B-0607A` | 1 | slot_index_606b, object_id_606b |
| 9 | `06ACE-06AE3` | 1 | floor_spike_handler_6ace |
| 10 | `06B14-06B2C` | 2 | (unnamed in cache) |
| 11 | `06B2C-06B56` | 1 | breakable_6B2C |
| 12 | `06B79-06BAA` | 1 | (unnamed in cache) |
| 13 | `06C45-06C82` | 3 | floor_loss_6c72 |
| 14 | `0760C-07646` | 1 | surface_type_1d_handler |
| 15 | `07646-07666` | 1 | (unnamed in cache) |

## 5. Classification changes that do not increase coverage

130 of the 211 ranges were already fully classified before this task by recovered assembly or other
claims (121 CODE-only, 2 DATA-only, 7 mixed CODE/DATA). Their kind is now documented per range
(`bytes_by_class`), with no coverage change. Observations from that comparison, none acted on:

* Seven ranges mix CODE and DATA (for example the type `$2F` tables/scripts/callbacks range and
  `terrain_handler_table`); they are subdivided by the existing claims and were not forced into one class.
* `isometric-platform.json` range `0x78439-0x78585` ("type-$28 state scripts", 332 bytes) overlaps
  byte-verified recovered code (`platform_code`, starting `0x78577`) by 14 bytes. The audit extent is
  therefore too long at its end; the 318 bytes before `0x78577` stay UNKNOWN because no consumer of the
  range is proven. The cache was not edited.

## 6. Independently evidenced coverage

Independent structural coverage rose from 142,681 to 143,573 bytes (+892). Recovered-and-independent
rose by 32 (2,215 -> 2,247): the corrected `object-50` data entry repeats the recovered pointer-table
range with its own SHA-256, as that audit's other explicit-kind entries already did; the recovered
manifest copies (`thz1/object-census.json`, 22 entries) remain recovery-manifest evidence only. The 860
reviewed bytes were all UNKNOWN before, none is recovered, and `classified_by_recovery_only_bytes` is
unchanged at 10,799.

## 7. The 32-byte contradiction (`0x06696-0x066B6`)

**Resolved in favour of the recovered split.** From the original ROM and byte-verified assembly:

* `animation_command_dispatch` (`0x6680-0x6696`) ends in `JP (HL)` at `$6695`; it is preceded by
  `LD DE,$6696`, `ADD A,A` and `ADD HL,DE`, so `$6696` is the base of a word table indexed by `xx*2`.
* The 16 words at `0x6696` all point at instruction starts inside the recovered
  `animation_command_handlers` (`0x66B6-0x68F8`); the table ends exactly where the handlers begin.
* The object-50 audit's own purpose text said "command dispatcher and pointer table": it had merged the two.

`tools/object_50.py` now records `anim_cmd_dispatch` as `0x6680-0x6696` CODE and a new
`anim_cmd_pointer_table` as `0x6696-0x66B6` DATA; `data/rom-cache/thz3/object-50.json` was regenerated
(only those two entries changed; `anim_cmd_dispatch` length 54 -> 22 and its SHA-256 follow). The ledger's
contradiction detector is unchanged and still tested with a synthetic pair.

## 8. Remaining unresolved ranges and the evidence needed

47 clusters (overlapping audit ranges merged), 3,172 UNKNOWN bytes: 26 resident-engine clusters (1,277 bytes)
and 21 banked clusters (1,895 bytes).

Common reason: no CALL/JP/JR from byte-verified (or already proven) code, and no recovered dispatch
table, reaches the entry. Those routines are called from still-unrecovered code. Evidence that would
settle them:

* **Resident engine (banks 0/1):** a proven caller, a decoded jump-table consumer, or a Z80 PC trace of the
  unmodified game. Recovering a caller is the natural route: each recovered caller converts its callee
  automatically on the next `decomp1a_review.py` run.
* **Banked (2+):** a bank-resolved entry (a CALL/JP from verified code in the same bank, a decoded
  callback/script-pointer table entry, or a PC trace with the mapper state). For ranges that may be tables
  (duration tables, state scripts) an instruction that loads the address and indexes it.

| Bounds | UNKNOWN bytes | Audit entries | Cache |
|---|---:|---|---|
| `00570-0057C` | 12 | vblank_camera_commit | viewport-semantics.json |
| `01D2D-01D33` | 6 | vdp_register_init | viewport-semantics.json |
| `0361D-03657` | 58 | player_update | player-animation-counter.json |
| `03783-037CC` | 73 | (unnamed in cache) | gpz-surface19.json |
| `0384D-0386F` | 34 | (unnamed in cache) | gpz-surface19.json |
| `03901-0393B` | 58 | wrapper_0A_3901 | player-spring-airborne.json |
| `03A37-03A59` | 34 | wrapper_0E_3A37, callbacks $3A37 ($0E) and $3A48 ($14) | gpz-surface19.json, player-fall-control.json, player-spring- |
| `03BFB-03C15` | 26 | player_pit_screen_y | viewport-semantics.json |
| `045B3-04892` | 51 | stand/landing setters $45B3/$45CE, state_setters_45b3, landing_45CE, n | gpz-surface19.json, player-attack-badnik.json, player-fall-c |
| `04A74-04AA3` | 47 | power_up_timer_4a74 | player-attack-badnik.json |
| `04C12-04C37` | 37 | state_probe_caller_4c12 | terrain-ring-collection.json |
| `04C90-04CB0` | 32 | camera_update | viewport-semantics.json |
| `04CB0-04CF7` | 71 | camera_limit_x | viewport-semantics.json |
| `04CF7-04D3E` | 71 | camera_limit_y | viewport-semantics.json |
| `04D3E-04D5D` | 31 | camera_to_vdp | viewport-semantics.json |
| `04E57-04E98` | 65 | (unnamed in cache) | gpz/implementation-manifest.json |
| `04FDC-05082` | 166 | level_header_loader | gpz/block-mapping-audit.json, viewport-semantics.json |
| `05316-05323` | 13 | (unnamed in cache) | gpz/block-mapping-audit.json |
| `053DF-053E9` | 10 | (unnamed in cache) | gpz/block-mapping-audit.json |
| `05832-05935` | 259 | camera_follow | viewport-semantics.json |
| `05935-05956` | 33 | camera_follow_init | viewport-semantics.json |
| `059B3-05A03` | 6 | camera_vectors | viewport-semantics.json |
| `05F3D-05F84` | 23 | badnik_attack_check_5f3d, attack_convert_5f3d | player-attack-badnik.json, spring-interaction.json |
| `0606B-06089` | 15 | slot_index_606b, object_id_606b | platform-spike-collision.json, player-attack-badnik.json |
| `0614E-06168` | 26 | (unnamed in cache) | sez/enemies-20-23-runtime.json |
| `062F7-0630B` | 20 | x_velocity_negate | sez/platform-28-runtime.json |
| `300D9-3010E` | 53 | state_04_branch_80d9 | player-animation-counter.json |
| `3018F-30194` | 5 | state_0b_branch_818f | player-animation-counter.json |
| `30313-3031D` | 10 | peel_out_state_1a_init_8313 | player-attack-badnik.json |
| `30CB4-30D36` | 130 | (unnamed in cache) | gpz-surface19.json |
| `30EE1-30F76` | 149 | selector_walk_8ee1, walk_duration_table, selector_run_8f45 | gpz-surface19.json, player-animation-counter.json |
| `30F76-3100B` | 149 | selector_roll_jump_8f76, floor_duration_table | player-animation-counter.json |
| `3100B-3103D` | 50 | selector_1d_900b | player-animation-counter.json |
| `31138-31163` | 43 | selector_17_9138 | player-animation-counter.json |
| `31959-319FB` | 162 | type05_aura_998a | player-attack-badnik.json |
| `322DD-323B0` | 211 | (unnamed in cache) | sez/implementation-manifest.json |
| `70000-70146` | 8 | placement_scan, object_creator_80eb, placement_creator | sez/platform-28-runtime.json, spring-interaction.json, viewp |
| `74000-74052` | 82 | (unnamed in cache) | mghz/implementation-manifest.json |
| `741BF-74259` | 154 | (unnamed in cache) | sez/implementation-manifest.json |
| `742F7-7432E` | 55 | (unnamed in cache) | mghz/implementation-manifest.json |
| `7432E-74392` | 100 | (unnamed in cache) | mghz/implementation-manifest.json |
| `7450A-74555` | 75 | (unnamed in cache) | mghz/implementation-manifest.json |
| `78439-78585` | 318 | type-$28 state scripts, platform_clear_deltas_8577 | isometric-platform.json, platform-spike-collision.json |
| `79B91-79B9D` | 12 | (unnamed in cache) | gpz/boss-51-composition.json |
| `79C0F-79C19` | 10 | (unnamed in cache) | gpz/boss-51-composition.json |
| `79E4B-79EAF` | 100 | (unnamed in cache) | gpz/boss-51-composition.json |
| `7A141-7A154` | 19 | (unnamed in cache) | gpz/boss-51-composition.json |

Two resident clusters have proven entries but unreached bytes: `0x045B3-0x04892` (51 bytes) and
`0x05F3D-0x05F84` (23 bytes) lie between reached routines, so flow cannot say whether they are code
or data. `0x0606B-0x06089` (15 bytes) is partly reached.

## 9. Recommended next classification targets

1. **Recover callers, not callees.** The camera block (`0x04C90-0x05956`, about 500 UNKNOWN bytes), the level
   header loader (`0x04FDC-0x05082`), the player-update/state wrappers (`0x0361D-0x03A59`)
   need only a supported entry; recovering the few call sites in unrecovered engine
   code (the main loop in bank 0) would convert most of the resident backlog.
2. **A bounded PC trace** of the unmodified game through `tools/sms_frame_harness.py` (title -> THZ1 -> boss
   frame) would give actual-execution and mapper evidence (a stronger tier than the static evidence used here) for the banked routines (bank 12 selectors,
   bank 28/30 object code) and distinguish their tables. It needs a hook faster than per-address Python hooks.
3. **Bank 12 selector/duration tables** (`0x30EE1-0x3103D`): decide code vs data by finding the instruction
   that loads the table address and indexes it, after the selector routines are reached.
4. **Bank 30 type-`$28` scripts** (`0x78439-0x78577`, 318 bytes): needs the consumer of the script pointer
   in the object table; also correct the audit end.
5. **Bank 28 `0x74000-0x74555`** (MGHZ/SEZ manifest ranges, 466 UNKNOWN bytes): no proven entry yet;
   needs a bank-resolved caller or callback-table entry as above.

## Verification

* `python -m unittest tests.test_rom_ledger tests.test_decomp1a` (ROM-backed tests skip without the ROM).
* `python tools/rom_ledger.py <ROM> --check` and `python tools/decomp1a_review.py <ROM>` reproduce the
  committed `ledger.json`, `summary.md` and `reviewed-ranges.json` byte for byte.
* Existing Research checks affected by the `object_50.py` change are listed in the handover report.
* The recovered assembly and `regions.json` are untouched, so byte-identical reconstruction is unchanged;
  it was re-run for the record.

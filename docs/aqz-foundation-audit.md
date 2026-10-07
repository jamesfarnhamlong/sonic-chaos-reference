# Aqua Planet A1 foundation

Research branch `research/aqz-foundation`, based on canonical
`53e9095ae2d807be8cd67f8ed572caead09094d9`. No POC files or accepted SEZ
contracts were changed. Manager review and James's visual approval are pending.

ROM: Sonic Chaos (Europe) v1.2, 524288 bytes, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Every extraction reads the verified local ROM anew. No historical AQZ export
is an input. Numeric IDs below are identities, not names inferred from art.

## Machine package and evidence limits

- `data/rom-cache/aqz/implementation-manifest.json`: complete layouts, used
  blocks plus ring replacements, both collision planes/profiles, attribute
  words, art loads, palettes, ring placements, effect traces, water/environment
  reconnaissance, original mapping/loader checks, source-region/tool hashes.
- `data/rom-cache/aqz/object-census.json`: every nine-byte mapped record,
  locations/raw bytes/flags/parameter/auxiliaries, anchor cell/block, one-based
  placement token, per-placement accepted parameter matches and contracts,
  state scripts/callback scans, dependencies and shared-system source hashes.
- `data/rom-cache/aqz/art-approval.json`: source/SAT/composition hashes and
  **PENDING_JAMES_APPROVAL**. No PNG pixels are committed.
- `data/rom-cache/aqz/original-checks.json`: original-game boot/layout and
  complete-state, history-independent replay fixtures.

Decoded data and controlled original-routine results are usable for review.
Static state-table entry counts are not claims that every state is reachable
in every placement. Callback scans include shared callees; a RAM reference is
reconnaissance, not a complete movement/contact contract. Missing mechanics
remain explicitly blocked rather than assigned guessed behavior.

## Exact metadata

The ROM zone index is **4**. Cells are 32x32 pixels. Initial coordinates are
direct `$4E57` word copies; camera bounds are the `$4FDC` header words. Right
bounds retain the original exclusive semantics.

| Act | Cells | Pixels | Player start | Initial camera | Camera min | Camera max | Encoded / loaded cells | Terrain rings | Type09 rings | Objects |
|---|---|---|---|---|---|---|---|---:|---:|---:|
| AQZ1 | 168x24 | 5376x768 | (110,206) | (0,99) | (0,8) | (5120,528) | 4032 / 4032 | 123 | 5 | 35 |
| AQZ2 | 128x32 | 4096x1024 | (110,558) | (0,447) | (0,8) | (3840,784) | 4096 / 4095 | 50 | 10 | 30 |
| AQZ3 | 80x16 | 2560x512 | (110,238) | (0,132) | (0,8) | (2304,272) | 1280 / 1280 | 4 | 0 | 4 |

| Act | Header file | Layout bank:CPU / file | Row-offset table CPU | Object list bank:CPU / file |
|---|---|---|---|---|
| AQZ1 | $051F2 | $17:$8000 / $5C000 | $5A33 | $1C:$93E5 / $713E5 |
| AQZ2 | $05208 | $17:$87C1 / $5C7C1 | $5A97 | $1C:$9521 / $71521 |
| AQZ3 | $0521E | $15:$BAF3 / $57AF3 | $5B67 | $1C:$9630 / $71630 |

The header-pointer table is `$5082`; the zone4 act pointers are `$50BA/$50BC/$50BE`.
Object pointers are `$1C:$857E/$8580/$8582`. Lists terminate at
`$71520/$7162F/$71654` respectively, and contain exactly 35/30/4 records.
AQZ1/2 contain one sign `$18` each. AQZ3 has no sign; its mapped boss `$59`
is at WORLD(1856,238), record `$71630`.

Only AQZ2 has an absent last cell: encoded index4095 is not written to RAM.
The cache preserves it separately; it is never counted as loaded terrain or rings.
Controlled `$4DBE` execution stops at `$4DFB`, before rendering, and proves all
9407 written cells plus the two-byte sentinel beyond each act's loaded end.
Original-game boot independently agrees on all 9407 cells.

## Mapping-pointer correction

All three acts use `$14:$9320`, file `$51320`. Each mapping word is an absolute
CPU pointer, so the conversion is exactly:

```
mappingFile = bank * $4000 + pointer - $8000
```

The historical table-relative formula adds an erroneous **$1320**. It reads
different bytes for **all 256 block entries**, not just the currently visible
ones. Both original horizontal/vertical consumers agree with the corrected
decoder for every block in every act: **1536 checks, zero mismatches**.
Both-plane collision headers retain their original bank-$0E profile sources.
Terrain flips, palette selection and priority bits remain attribute data.

## Terrain and shared-system matrix

The shared collision-header table is file `$38000`. Every exported block
contains flags, modifier, trailing byte, both horizontal/vertical 32-byte
profiles and file pointers for each plane. `solid`/`one_way` are decoded
header bits7/6, not inferred image geometry. Hazards are surface-handler
semantics, not a generic new hitbox.

| Surface | Loaded cells AQZ1/2/3 | Evidence/contract | Classification |
|---|---|---|---|
| $00 | 2510/2611/754 | shared empty/background probe | shared recovered |
| $01 | 840/860/111 | shared solid; `$6A5D` special gate is zone5 only | shared recovered |
| $02 | 415/384/383 | shared solid/profile | shared recovered |
| $03 | 28/35/8 | shared slope/profile modifier | shared recovered |
| $04 | 16/48/0 | `$6CE6 RET`; shared collision still applies | shared with AQZ data |
| $05 | 13/9/0 | blocks$3C/$3D, accepted terrain floor-spike probe | shared recovered |
| $07 | 72/38/4 | accepted `$753E` terrain-ring probe | shared recovered |
| $09 | 1/2/0 | upright springs$30/$31 | shared recovered |
| $0A | 1/7/1 | horizontal springs$33/$35, shared side-path checks | shared recovered |
| $0C | 32/2/0 | block$AF crumble; accepted SEZ `$13` runtime | shared recovered |
| $0D | 18/13/1 | breakable$9B/$9C and shared shards | shared recovered, AQZ art |
| $10 | 14/42/0 | blocks$48..$55, shared `$6C82` loop/plane dispatch | shared with AQZ layout |
| $12 | 0/2/0 | ramp blocks$1F/$23 | shared recovered |
| $14 | 2/13/18 | diagonal/ceiling spring blocks$36/$37/$39/$3B | shared recovered |
| $16 | 10/14/0 | block$47 floor break/bounce/reward | shared recovered |
| $1A | 1/2/0 | block$A7 booster, accepted SEZ contract | shared recovered |
| $1E | 59/13/0 | `$6D42 RET`; shared collision still applies | shared with AQZ data |

Surface `$10` is not a new water mechanic. Its block dispatch and plane
headers use the accepted THZ/GPZ loop contracts, including the previous-foot
block `$D497` and alternate `$13` route. Layout integration must preserve those
gates and skip the ordinary ring/terrain probe in loop states.

Terrain rings: 123/50/4. Type09 rings: 5/10/0, all parameter0. Collection
remains the accepted parity probe and strict type09 anchor proximity. Ring
frames come from bank$1D CPU$855D, file$7455D, four 128-byte frames -> VRAM$28C0
(tiles$146..$149), eight updates per frame. The animation source is common;
AQZ mapping/palette data is freshly decoded. No probe widening is introduced.

Shared support `$06/$03/$07/$13/$0F/$34/$0A/$12` is inventoried separately
from mapped records. Hurt/lost rings is a shared global mechanic, not a new
water effect. Recorded source-region hashes from eight accepted audits all
match: **195 source regions**. This is evidence of the same ROM routines;
water and zone gates still need their explicit contracts, not blanket reuse.

## Complete mapped-object census

| Type | AQZ1 | AQZ2 | AQZ3 | Parameters | Classification / exact scope |
|---|---:|---:|---:|---|---|
| $09 | 5 | 10 | 0 | $00 | SHARED_WITH_AQZ_DATA: accepted type09, AQZ palette |
| $0C | 1 | 1 | 0 | $00 | AQZ_SPECIFIC_NEEDS_AUDIT: mapped emitter and dynamic bubble paths |
| $10 | 8 | 4 | 2 | $01/$02/$03/$04/$06 | SHARED_WITH_AQZ_DATA: known monitor/reward paths |
| $18 | 1 | 1 | 0 | $00 | SHARED_WITH_AQZ_DATA: accepted sign; zone+1 odd selects `$A919` as THZ/SEZ |
| $30 | 1 | 0 | 1 | $00 | SHARED_WITH_AQZ_DATA: same strong fixed-spring scripts/callbacks as$26 |
| $3C | 8 | 3 | 0 | $00/$01 | AQZ_SPECIFIC_NEEDS_AUDIT: numeric enemy family |
| $3D | 9 | 10 | 0 | $00/$04/$08 | AQZ_SPECIFIC_NEEDS_AUDIT: numeric enemy family |
| $3F | 2 | 1 | 0 | $86/$83/$8B | AQZ_SPECIFIC_NEEDS_AUDIT: shared platform scripts with AQZ2 override |
| $59 | 0 | 0 | 1 | $00 | BOSS_SUPPORT: dedicated A5 |
| **Total** | **35** | **30** | **4** | **69 records** | all nine bytes and tokens in cache |

Mapped `$26/$28/$1B/$2F` are absent. Two Rocket Shoes monitors occur in AQZ1
at (1664,430) and (3344,174), with the accepted parameter$04 runtime including
its recovered water constants. Spring Shoes are absent: no invented AQZ variant.

`$30` and `$26` both point at `$1E:$8212`; scripts and callback pointers are
identical. Both AQZ `$30` records use parameter0, strong path states
0->7->1->2->5->7, art$86/$86 and mapping$941A. The original initializer adds12
to runtime object Y; the stored canonical anchor is not rewritten. Frame3
belongs to the unplaced weak path and is absent from this type's mapping.
No weak type30 implementation contract is claimed.

`$3F` and `$28` both point at `$1E:$8439`. That alone is insufficient:
`$8617` tests zone4/act1 and requests state14. The AQZ2 $8B path therefore
needs A3. Placement $86 has aux1$32 (50), not a guessed pixel distance; the
canonical byte is preserved. Matching known parameters is recorded as evidence,
not a replacement for the AQZ-specific gate audit.

## Graphics, palette, background and effects

All acts use primary stream file$58000 ($16:$8000), **232 tiles** -> VRAM$1800,
base$C0. The eight supplemental streams/load bases are:

| Source file | Tile base | Tiles |
|---|---:|---:|
| $23340 | $10 | 90 |
| $27090 | $6A | 6 |
| $27150 | $70 | 16 |
| $26570 | $80 | 6 |
| $273E0 | $86 | 8 |
| $272C0 | $8E | 18 |
| $26B60 | $A0 | 4 |
| $274A0 | $A4 | 16 |

Each load includes exact VRAM destination, bank/CPU source, remap flag and
decompressed hash. All three acts select background palette25 (file$3B7DD)
and sprite palette10 (file$3B6ED). Exact CRAM bytes are cached.

The shared descriptor requests **[5,0,0,11]** in every act:

- Effect5 (`$1D:$81BF`): two 32-byte frames `$8E7D/$8EBD` -> VRAM$2E20,
  tile$171, every **3 updates**, paused when `$D44E != 0` (boss active).
- Effect11 (`$1D:$8166`): **16** 448-byte frames at `$9997 + frame*$1E0`
  -> VRAM$3000, tiles$180..$18D, every **8 updates**. The source stride is
  480 bytes; the transferred length is 448, not 480. **Continues while boss
  active.** 192-update running/paused traces are stored separately.
- No palette writes occur in either recorded effect trace. Waterline palette
  switching is a different mechanism, not a palette cycle inferred from art.

**Water physics is proven in AQZ1/2, absent from AQZ3's gated water updater.**
`$4B46` requires zone4 and act<2; `$4BC0` compares unsigned player WORLD(Y)
against WORLD($D450). All 18 zone/act gates and five boundary values are executed.
The common gravity path halves dry increments underwater (state$0B +12/256,
state$1B +18/256, ordinary +24/256, downward cap4); normal jump setter chooses
-3.25 rather than dry -4.25. Those bytes prove physics changes, but do not
close every state, entry/exit, damage, drowning and input path for A2.

`$2A2E` creates two dynamic `$0D` waterline controllers, parameters0/1 and an
initial waterline768. `$0C:$9DAD` selects actual WORLD(Y)=**568 in AQZ1**,
**788 in AQZ2**. Both original-game boots confirm these values and two live
controllers. No controllers occur in AQZ3.

The controller callback `$9DDD` publishes object Y to `$D450`. `$9DED` enables
the scanline when cameraY < waterline <= cameraY+192 and publishes
waterline-cameraY to `$D132`. Outside this interval it disables line IRQ and
queues above-water palettes25/10 or below-water48/49. IRQ `$0652` copies 32
fixed CRAM bytes from `$0688`. The two strip instances use tile base$A0;
`$9EFE` advances modulo16 and picks cameraX-relative positions from tables
$9F2B/$9F4B. This is camera-relative strip placement, distinct from terrain
tile effects and player water physics. Exact raster timing and any additional
parallax remain A2; the review maps intentionally do not simulate IRQ timing.

Underwater `$D444` increments each water-updater call; at120 it resets and
increments `$D445`. At11 it creates countdown type$32; at17 it requests player
state$1F. Leaving water resets `$D445`. Dynamic types$0C/$0E/$32 remain in
the A2 dependency inventory. No oxygen/air-collection behavior is guessed.

## Reconnaissance / package order

All listed counts below are decoded state-table entries. Source-reachable
states and runtime-tested subsets must remain distinct in later audits.
Callback lists, static frame durations, script velocities, IX field/RAM references,
external calls and hashed code regions are in `object-census.json`.

| Type | Bank:table CPU | Entries | Script frames | Driver / next audit |
|---|---|---:|---|---|
| $0C | $0C:$9CAC | 4 | 0..3 | mapped timer/emitter + dynamic player air path; A2 |
| $0D | $0C:$9D9B | 3 | 0..1 | camera/waterline IRQ controller; A2 |
| $0E | $0C:$9F8B | 2 | 0..3 | water-entry player effect; A2 |
| $30 | $1E:$8212 | 10 | 0..3 (placed strong path0..2) | shared strong fixed spring; AQZ presentation only |
| $32 | $1E:$94C6 | 2 | 0,1,16..21 | water timer/countdown; A2 |
| $3F | $1E:$8439 | 15 | 0..1 | player/support, movement timer, AQZ2 state14; A3 |
| $3C | $1E:$91F1 | 9 | 0..2 | signed Y steps ±4 in four-call legs,32-update dwell; parameter-selected path; A4 |
| $3D | $1E:$9291 | 4 | 0..4 | script X±0.75/Y-2; callback compares waterline, reads clock; A4 |
| $59 | $1E:$A7BA | 21 | 0..10 | boss timers, player contact and world/screen limits; A5 |
| $5A | $1E:$AC08 | 5 | 0,26..29 | world initialization (2048,238), velocities -0.5/-2; A5 |
| $5B | $1E:$AD2B | 2 | 0,11 | Y-1 initialization; A5 |
| $5C | $1E:$AD60 | 6 | 0,14..15; callback16..23 | parameters0..6, boss/child state coordination; A5 |
| $5D | $1E:$AED5 | 2 | 0,24..25 | projectile child; A5 |

These movement observations are BYTE-VERIFIED/DECODED reconnaissance, not
implementation contracts. Runtime reachability, collision, sleep/removal and
boundary sweeps still belong to their dedicated packages.

Proposed order:

1. **A2 environment:** waterline/IRQ palette behavior, water player states,
   drowning/countdown/bubbles and AQZ loop-layout integration with shared contracts.
2. **A3 platform:** `$3F` parameters$83/$86/$8B, with AQZ2 state14 override.
3. **A4 enemies:** `$3C/$3D` all placed parameter/flag paths, contact, art
   orientation, terrain/waterline response and lifecycle.
4. **A5 boss:** `$59/$5A/$5B/$5C/$5D`, dynamic allocation dependencies,
   arena, combat and original clear/results/next-zone chain.

A3/A4 research can consume this foundation; POC's first playable AQZ checkpoint
needs A2 and visual approval. No widescreen behavior is designed here.

## AQZ3 boss and viewport reconnaissance

Mapped `$59` WORLD(1856,238), parameter0, no sign. The 21-entry table begins
`$1E:$A7BA`. Intro uses the shared boss framework; row4 has strict
PLAYER_DIST X<96 / Y<304 and camera offsets(-128,-160). Follow-up must prove
the selected row, settled camera and any alternate intro path in whole-game tests.

`$A9A5` requests dynamic graphics selector$17 (decimal23), sprite palette16,
subtracts224 from object Y and initializes byte+$26 to10. This is not a claim
of an audited ten-hit fight: underflow and phase gates must be checked in A5.
Dynamic list file$7C12 uploads 132 tiles from `$0A:$A840` (file$2A840) to
base$2E, and12 tiles from `$09:$ABA0` (file$26BA0) to base$B2.

Script spawns prove children$5A (state6), $5D (state10), $5B (state13), and
seven $5C parameters0..6 (state14). Explosion state5 creates five$34 parameter8;
state11 creates five$34 parameter2. Shared clear callback$81BD is in state4,
with $0F/$0A/$12 support. Exact clear gates, allocator ownership, child cleanup
and results/transition remain A5, not assumed from SEZ.

Viewport vocabulary retained:

- **WORLD:** canonical placements, waterline568/788, `$ABF2` boss Y>238.
- **PLAYER_DIST:** boss framework strict96/304 trigger; mapped spring proximity
  remains the accepted shared contract.
- **EDGE:** `$AA6C` uses cached screen X thresholds48/208 to stop boss horizontal
  velocity; waterline visibility uses cameraY+192.
- **CENTER:** controller X positions are camera-relative table data, not a
  player-distance trigger; table values are decoded rather than rescaled.
- **LOCKED_CAMERA:** boss framework target-relative offsets(-128,-160); exact
  settled lock/arena behavior awaits A5.

Other scan references remain unresolved classifications until source branches
are followed. Do not widen WORLD/PLAYER_DIST values or silently replace SMS
constants while importing this package.

## Visual review

Local PNG boards are under **`build/aqz-approval/`** (ignored, local only).
`art-approval.json` preserves extraction provenance and composition hashes.
`boards-sha256.json` in the review directory hashes all PNGs. Reproduction:

```
.venv/Scripts/python.exe tools/aqz_foundation.py ROM
.venv/Scripts/python.exe tools/aqz_art_approval.py ROM
<Pillow Python> tools/aqz_art_previews.py
```

Boards: three complete maps, three used/replacement block sheets, three start
crops, two underwater palette-variant block sheets, three animated scenery/ring
boards, and eighteen new/palette-variant object boards including the waterline,
entry/countdown effects, Rocket Shoes palette variant, boss and four children.
**32 boards total.**
SAT compositions are checked through the original renderer, including flips.
The child$5C callback `$AE5B` overrides its script frame. A1024-case original
selector sweep proves frames16..23; all are included, rather than limiting
the visual package to the script's frames14/15.
Forced bit4=1 images are explicitly diagnostic, not permission to flip the
runtime bitmap. Terrain priority/palette/flip semantics remain in the mapping
cache; flat terrain sheets do not establish sprite occlusion or raster timing.
No synthetic art, manual pixel correction or invented background has been added.

James must approve the new compositions before POC consumes them. Approval
state stays pending even though extraction and renderer tests pass.

## Verification and unresolveds

`tests/test_aqz_foundation.py` checks ROM identity, fresh cache regeneration,
metadata/start/bounds, original layout loaders/sentinels, corrected mapping
conversion/original consumers, collision profiles, every object record,
parameter-guarded reuse, art loads/palettes/effects, water gates/boundaries,
original renderer compositions and guarded whole-game replay.

Original-game fixtures preserve the **complete exported CPU state** as well as
RAM/VDP/harness state. This includes prefix/EI shadow/frame_tick. Restoring
registers only, or injecting a NOP, is not used. Two48-update runs per act
agree after prior history. This approximate SMS harness provides original-code
confirmation; it is not a final human gameplay acceptance result.

Focused validation: **9 tests, 13062 enumerated evidence checks**, including
1536 mapping-consumer checks,9407 original-loader cells,69 original placement
creators,1024 child-frame selector cases and154 renderer compositions. Counts
are named coverage tallies, not a claim that every check is a separate test
method. Source tool hashes normalize text to LF for reproducibility across
Git CRLF checkouts.

Full `tests/verify_cache.py` completed successfully, regenerating both existing
Research audits and all four AQZ caches from the verified ROM. `git diff --check`
and the staged diff check pass. Review PNGs, ROM files and build debris are
excluded from the commit. Visual approval and Manager merge review remain pending.

Unresolved: James visual approval; complete water/player/controller/raster
contract; additional parallax if present; `$3F` AQZ2 state14; both enemy families'
contact/lifecycle/reachability; boss/children combat/clear dependency chain;
results graphics/audio. New object counts and obvious constants do not close
these mechanics. POC must not treat them as implemented or invent substitutes.

## AGENTS candidate updates

- AQZ A1 foundation is available for Manager review on `research/aqz-foundation`;
  do not merge or treat new art as approved before review/James sign-off.
- AQZ is zone4; only AQZ1/2 use the water updater, with waterlines568/788.
- AQZ mapping table$14:$9320 requires bank-relative pointer conversion;
  historical exports are wrong by$1320. AQZ2 leaves encoded cell4095 unloaded.
- Next AQZ research packages: A2 water/environment, A3$3F platform, A4$3C/$3D
  enemies, A5$59 boss/support. No POC rollout is assigned by this report.

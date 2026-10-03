# GPZ1–3 foundation census and implementation report

Research branch: `research/gpz-foundation`, based on current Research `main`
`3141c9a`. Canonical ROM: Sonic Chaos (Europe) v1.2, verified SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
No POC file was modified. This report was prepared before the requested checkpoint.

The authoritative census package is
`data/rom-cache/gpz/implementation-manifest.json`. Regenerate it with
`tools/gpz_foundation.py`. All coordinates, rows, parameters, flags, auxiliary
bytes, ring quadrants, collision profiles, mapping attributes, mutation blocks,
source offsets and asset hashes are machine-readable. This document is the
pre-commit milestone report; coordinates here are examples, not an importer input.

## 1. Dimensions, starts, bounds and lookup

| Act | Cells | Pixels | Player anchor | Initial camera | Header camera maxima |
|---|---|---|---|---|---|
| GPZ1 | 160 × 24 | 5120 × 768 | (110,384) | (0,272) | (4864,528) |
| GPZ2 | 128 × 32 | 4096 × 1024 | (110,448) | (0,336) | (3840,784) |
| GPZ3 | 80 × 16 | 2560 × 512 | (187,352) | (75,240) | (2304,272) |

Camera minimum words are (0,8) in each act. These are SMS header values; the
horizontal right limit is exclusive. Widescreen camera bounds remain an explicit
adapter. Room extent and camera extent are different concepts.

**Decoded data + controlled original routine:** `$4E57` directly copies the
four start words to `$D2D6/$D2D8/$D511/$D514`; tests execute that loader for all
three acts. No THZ-derived presentation offset was applied. Headers originate
in `$5082`; starts in `$4E98`; object pointers in bank `$1C:$8546`.

GPZ1's 160-cell stride is new data, not a new addressing algorithm. GPZ2 uses
128 and GPZ3 80. All use the existing row-offset-table lookup and collision table
`$8000` in bank `$0E` (file `$38000`). The original 4095-cell loader ceiling
applies: GPZ1 loads 3840 cells, GPZ2 encodes 4096 but loads 4095, GPZ3 loads 1280.
Never treat GPZ2 index 4095 as a loaded terrain cell.

The common GPZ block mapping table is bank `$11:$9640`, ROM `$45640`, rather
than THZ `$44000`. The primary art is bank `$10:$A478`, ROM `$42478`.

## 2. Terrain and surfaces

GPZ1/2/3 use **99 / 113 / 67 distinct layout blocks**, 125 in their union.
Every used block is classified and includes both collision planes, raw vertical
and horizontal profiles, modifier, trailing byte, mapping pointer and 16 tile
attributes. Ring replacement blocks and `$46/$9D` mutation targets are included
even when absent from the initial layout.

| Act | Surface IDs used (hex) |
|---|---|
| GPZ1 | 00,01,02,03,04,05,07,09,0A,0D,10,12,14,16,19,1C |
| GPZ2 | 00,01,02,03,04,05,07,0A,0D,10,14,16,19,1C |
| GPZ3 | 00,01,02,03,04,07,0A,10,12,1C |

The manifest separates `THZ_SUPPORTED`, `SURFACE_1C` and
`NEW_OR_UNRESOLVED`. `THZ_SUPPORTED` describes the shared surface family;
explicit ceiling/spring requirements still apply. It does not certify every
POC branch for every block.

Surface `$1C` contains **212 / 116 / 90 cells**. Consume Research `ce2ef9b`:
blocks `$8C..$8F` height16; `$90/$93` mirrored 1..8 profiles; `$91/$92`
height8; `$94..$97` raw `$54` becomes height32 when **previous** surface is
`$1C` and sampled bit6 is set. All twelve GPZ mappings decode to zero opaque
pixels. Preserve them as collision cells; do not invent platform sprites.
Accepted side and underside results remain in the isometric audit/cache.

**POC read-only correction:** its floor bit6 special case and side-profile path
already exist, but `SCR_cc_ceiling` explicitly rejects surface28. Thus the
prior statement that surface `$1C` is entirely data-only is too broad for
underside fidelity. Reconcile that branch against the accepted underside oracle.

Other gaps are explicit, not hidden in ordinary solid masks:

- `$16`, block `$47`: **13 / 8 / 0 cells**. `$6AE3` is the researched
  attack-gated break/bounce path; `$7857` replaces the block with `$46`, queues
  dynamic graphics and calls the ring reward branch. POC lacks its floor path.
- `$19`, blocks `$85/$87`: **21 / 24 / 0 cells**. `$6B23` sets player `+$24`
  bit0 and increments `$D3BC`; the original routine result is tested. The
  downstream state/terrain-animation consumers are unresolved. This needs a
  bounded follow-up before claiming faithful GPZ1/2 traversal.
- Surface `$10` loop-contact families are shared. Canonical loop cells and
  alternate-plane profiles are in the package; generate centres/rows from the
  current layout rather than transcribing THZ locations.

## 3. Rings

| Act | Terrain rings | Type $09 visible ($00) | Type $09 hidden ($01) | Total placements/quadrants |
|---|---:|---:|---:|---:|
| GPZ1 | 84 | 8 | 32 | 124 |
| GPZ2 | 239 | 10 | 20 | 269 |
| GPZ3 | 4 | 5 | 0 | 9 |

Both accepted collection pipelines apply unchanged: terrain `$753E` uses the
final anchor and animation-counter parity; object `$09` uses strict anchor
proximity. Terrain ring centres, quadrant origins, source cells and replacement
tables are supplied. Do not widen pickup or merge the two populations.

## 4. Springs

| Act | Mapped $26 | Terrain upright | Diagonal right/left | Horizontal | Ceiling |
|---|---:|---:|---|---:|---:|
| GPZ1 | 5 | 1 | 1 / 0 | 5 | 0 |
| GPZ2 | 7 | 0 | 19 / 6 | 2 | 15 |
| GPZ3 | 0 | 0 | 0 / 0 | 2 | 0 |

Mapped springs reuse the accepted mechanism. GPZ1 has three fixed strong
springs and two hidden weak spans: `$87` at (4112,192), width112; `$86` at
(2288,608), width96. GPZ2 has six fixed strong springs and one fixed weak
`$01` at (2672,704). Their raw records and runtime rest Y = placementY+12 are
retained; the manifest never replaces the placement anchor with the rest Y.

Terrain spring cell origins and block IDs are exhaustive in the JSON. These
are cells, not inferred counts of independently animated spring entities.
GPZ2's 15 ceiling cells are block `$3A`. The accepted spring audit already
establishes their downward launch; no footwear/spring archaeology was reopened.

**New POC integration:** diagonal `$6A90` uses zone byte `$D297 != 0` to
select Y speed **−5.5**, while X remains ±4. POC hardcodes THZ −7. Ceiling
surface `$14` also needs the existing researched ceiling path, currently rejected.

## 5. Spikes and hazards

Static spikes are block `$3C`, surface5: **16 / 5 / 0 cells**. They use the
accepted foot-probe/side projection rules. There is one type `$1B/$00`, GPZ2
(208,672), using the researched moving-spike behavior.

No other object is asserted to be a non-enemy hazard. Types `$25/$2C` are
next-pass contact/enemy candidates and are deliberately skipped. Their damage,
children and human names are unresolved here; a census is not an enemy audit.

## 6. Monitors

| Act | $01 rings | $02 life counter | $03 speed selector | $04 Rocket Shoes | $06 invincibility |
|---|---:|---:|---:|---:|---:|
| GPZ1 | 0 | 1 | 1 | 0 | 2 |
| GPZ2 | 2 | 1 | 4 | 1 | 2 |
| GPZ3 | 1 | 0 | 0 | 0 | 1 |

All 16 records have proven existing numeric reward branches and exact anchors.
The Rocket monitor is GPZ2 (2288,430). Consume the accepted footwear audit;
no substitute reward or new shoe model is proposed. Existing POC selectors
1/2/3/4/6 are present. GPZ palette/art installation remains required.

## 7. Platforms

| Act | Parameter @ canonical anchor; aux1; initial state |
|---|---|
| GPZ1 | `$89 @ (1648,320); $0E; 10`, `$89 @ (2896,448); $0C; 10` |
| GPZ2 | `$05 @ (1632,800); $18; 13`, `$83 @ (1584,384); $0B; 4`, `$0A @ (2512,640); $0B; 11` |
| GPZ3 | `$89 @ (912,80); $0B; 10` |

All have aux0 `$6A`. Tests run all six original initializers. `$05` initializes
state13 and stores 6 in `+$36`; contact requests state6, not state5 or state14
(the state14 override is zone4/act1). All fifteen shared platform scripts are
included so POC can consume the reachable state6 behavior without prose tables.

Only `$0A` is currently supported by POC. Shared triangular support, signed
speed gate, owner and carry helpers are reusable. Add state10 horizontal reversal
and sag/X carry for `$89`, state13→6 touch-start for `$05`, and the accepted
state4 `$83` contract: +8 sag/recovery, 80 countdown, `$0030` gravity,
post-move support, permanent consumption after triggered lifecycle removal.
Do not send any of these parameters through THZ state5 fallback behavior.

## 8. Complete object classification

| Type | GPZ1 | GPZ2 | GPZ3 | Status / identification |
|---|---:|---:|---:|---|
| $09 | 40 | 30 | 5 | REUSED_SUPPORTED — object ring |
| $10 | 4 | 10 | 2 | REUSED_SUPPORTED — monitor |
| $18 | 1 | 1 | 0 | REUSED_SUPPORTED — goal sign |
| $1B | 0 | 1 | 0 | REUSED_SUPPORTED — moving spike |
| $25 | 5 | 7 | 0 | NEW_NEEDS_RESEARCH — numeric identity, next-pass candidate |
| $26 | 5 | 7 | 0 | REUSED_SUPPORTED — mapped upright spring |
| $28 | 2 | 3 | 1 | $0A REUSED_SUPPORTED; $89/$05/$83 REUSED_NEEDS_DATA |
| $2C | 4 | 3 | 0 | NEW_NEEDS_RESEARCH — numeric identity, next-pass candidate |
| $51 | 0 | 0 | 1 | BOSS — GPZ boss/controller |
| total | 61 | 62 | 9 | 132 exact raw records |

Here `REUSED_NEEDS_DATA` means canonical prior research exists but importer or
runtime integration is missing; it is not a promise that importing data alone
is sufficient. No mapped record qualifies as PRESENTATION_ONLY or UNRESOLVED;
those statuses remain valid schema values. Numeric objects with incomplete
behavior are explicitly NEW_NEEDS_RESEARCH rather than assigned invented names.
Every record has exactly one status and one foundation partition. The current
runtime partition is **50 / 50 / 7**, integrate-first **2 / 2 / 1**, skip
**9 / 10 / 1**. Zone art and the terrain runtime requirements still gate a build.

## 9. Act clear and GPZ3 boss census

GPZ1 sign `$18/$00` is (4992,430); GPZ2 is (3968,686). Their ordinary
`$18 → $19 → player $20` structure and shared viewport relationships remain
unchanged. The zone-parity sign prize table is **different**: GPZ selects
bank `$0C:$A962` instead of THZ `$A919`. Both decoded tables are supplied.
POC already defers the prize/retry presentation; preserve that bounded scope
or consume the correct GPZ table when expanding it.

GPZ3 has one mapped `$51/$00`, (1728,270), ROM `$70DF6`, bank `$1C:$8DF6`.
Its state table is bank `$1E:$9A3A` (ROM `$79A3A`), 21 states. Census-level
script decoding establishes additional `$51` children with parameters1..4,
`$34` explosion children with parameters8/4, and state0's shared `$81A6` HUD
allocator call (type `$12`). This is not a complete reachable dependency graph.
The `$0A/$0F` completion dependencies must not be copied from THZ without audit.
Skipping mapped `$51` prevents the entire dynamic chain, arena lock/HUD removal
and completion from starting. GPZ3 foundation has no invented act-clear trigger.

## 10. Graphics and asset readiness

All three acts share eight static loads, hashed after decoding/remap:

| ROM source | VRAM tile base | Tiles | Foundation use |
|---|---|---:|---|
| $42478 | $C0 | 254 | GPZ terrain/background tile mappings |
| $23340 | $10 | 90 | shared rings/monitors/spikes/sign base art |
| $262C0 | $6A | 6 | GPZ platform art |
| $26030 | $72 | 20 | mapped spring art |
| $26720 | $86 | 6 | registration retained; precise unused role not asserted |
| $25690 | $8C | 10 | next-pass $2C auxiliary art base |
| $25780 | $96 | 18 | next-pass $25 auxiliary art base |
| $25780, remapped | $A8 | 18 | next-pass $25 alternate art base |

Palette selectors are background `$16` (ROM `$3B7AD`) and sprite `$07`
(ROM `$3B6BD`), with exact CRAM values supplied. Mapping flips/palette/priority
bits are retained; transparent terrain must stay transparent in a sprite export.
GPZ type `$28` uses shared mapping `$9217`, frame1, four 8×16 pieces;
only X−16..+7 is opaque, Y anchor+2..+17 under the original renderer registration.
Use the accepted isometric art contract and shared anchor; do not widen collision.

Existing `level_package` VRAM/block renderer and `level_maps` work from explicit
GPZ descriptors. `level_package` now accepts optional act metadata without
changing the THZ default catalog. Build-local PNGs can be generated with existing
renderers. The manifest is metadata only, not a committed binary tile/ROM dump.
POC still needs generated zone terrain sheets, ring-stripped terrain, object
sprite/palette variants, layout/placement tables, and GPZ room/act registration.
Existing dynamic monitor-selector and sign extraction tools remain useful.
Static tilemap registration is established. Dynamic GPZ palette/tile animation,
scroll behavior and presentation over the transparent deck need bounded follow-up
and Windows comparison; no fabricated parallax is supplied.

## 11. Read-only POC readiness and genuinely new integration

Inspected clean active checkout `42aaa5032cef385284a00d0c1b7a0e7714747b4b`.
This is newer than the root's accepted THZ3-foundation summary. Reusable:
variable-width core/ring/loop lookup, raw terrain profiles, both ring probes,
mapped spring variants, static/moving spikes, monitor selectors, platform
support/carry, ordinary sign clear, and viewport/lifecycle vocabulary.

The complete identified runtime list is in `runtime_requirements`: platform
states4/10/13→6; non-THZ diagonal speed; ceiling spring path; surface16
break/reward; surface19 consumer closure; surface1C underside reconciliation.
This list contains recovered behavior missing from POC, not speculative enemies.
Room predicates, act registry, start/camera setup and graphics installation must
be generalized beyond THZ; these are integration/data-generation work.

## 12. Migration and build plan

1. Review this census; close surface19 consumers and bounded background/dynamic
   registration questions before claiming a faithful complete foundation.
2. Generate GPZ1–3 data and assets from this manifest and the verified local ROM;
   keep GPZ1 width160 and GPZ2's unwritten final cell intact.
3. Implement the listed shared runtime paths with focused original-routine
   boundary/timing fixtures. Consume the accepted $83/$1C oracles directly.
4. Instantiate supported rows and integrate-first platforms after their runtime
   exists. Assert exact per-act counts; explicitly skip $25/$2C/$51.
5. Run traversal/act-clear regressions with THZ1 as control; package all three
   GPZ acts at one meaningful checkpoint and compile source/extracted package.
6. James compares starts, perspective deck/undersides, horizontal/touch/falling
   platforms, ceiling/diagonal springs, breakables and GPZ1/2 completion in Windows.
   GPZ3 remains deliberately non-boss. No POC build was attempted in this research task.

## 13. Focused verification

Run from the Research worktree:

```text
.venv/Scripts/python.exe tools/gpz_foundation.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe -m unittest tests.test_gpz_foundation -v
```

The new module has **20 focused tests**: 14 cache/schema/census locks and 6
ROM-backed tests. These cover exact layouts/dimensions/starts, raw object hashes,
rings, springs, hazards, rewards, platform placements/init, $1C, mutation mappings,
safe partitions, boss script census, dependencies, deterministic regeneration,
original start loader, original surface19 writes and source/art hashes.
The shared metadata API also receives the existing focused level-package
regression checks: **37 passed, zero skips** (20 GPZ + 17 existing level-package).
Fresh GPZ cache regeneration and `git diff --check` pass. No full research suite or expensive accepted oracle cache
regeneration is required.

## 14. Unresolved and limits

- Surface19 downstream player/terrain animation consumer closure.
- Dynamic GPZ palette/background tile/scroll presentation registration.
- Human names and full behavior/contact/dependencies of $25/$2C; next enemy pass.
- Full GPZ3 boss/dependency/completion audit; deliberately excluded.
- New platform subtype runtime work should use focused timing/lifecycle oracles
  during POC integration; this census tests initializers, not complete trajectories.
- Static art hashes prove deterministic extraction, not Windows visual acceptance.

All known gaps are recorded. This package is authoritative for decoded canonical
data and census decisions; it does not certify a finished traversal runtime.

## 15. AGENTS.md candidate updates

Do not edit root AGENTS during this work. Proposed accepted-checkpoint additions:

- GPZ1/2/3 foundation manifest: dimensions160×24 / 128×32 / 80×16; starts and
  camera words tested by original loader; 132 mapped records; skip $25/$2C/$51.
- GPZ foundation requires more than $28/$83: also $89 state10, $05 state13→6,
  non-THZ diagonal −5.5, ceiling springs, surface16, surface19 follow-up and
  surface1C underside reconciliation against accepted Research.
- GPZ1/2 share the ordinary sign chain but use zone-parity prize table $A962.
- Preserve GPZ2's 4095 loaded-cell bound; install GPZ mapping/art/palettes from
  the generated package, with no manual canonical placements or synthetic art.

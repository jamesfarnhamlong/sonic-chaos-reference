# Turquoise Hill Zone Act 1 object census

This is the authoritative census of the 53 raw nine-byte object records at ROM
`$705AE..$7078A` for the 524,288-byte Sonic Chaos SMS ROM with SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
The machine-readable detail is in
[`data/rom-cache/thz1/object-census.json`](../data/rom-cache/thz1/object-census.json)
and regenerates with `tools/thz1_object_census.py`.

| Type | Records | Coordinates / distribution | Parameter variants | Graphics | Animation | Verified role/status | Behavior status | Next research need |
|---:|---:|---|---|---|---|---|---|---|
| `$09` | 24 | records 14-21, 37-52; routes across X 816-3422 | `$00` ×11, `$01` ×13 | static shared catalogue | 4 states; frames `$00-$06`; decoded | ring/sparkle family supported, not canonical | unresolved | parameter/entity expansion and collection/lifetime study |
| `$10` | 5 | `(336,270)` to `(2688,686)` | `$02` ×1, `$04` ×2, `$06` ×2 | static plus parameter-selected icon load | 4 states; `$00/$0B/$0C`; decoded | monitor/item-box presentation supported, not canonical | complete for THZ1 reachability | canonical identity and type-`$05` child semantics |
| `$18` | 1 | `(3960,558)` | `$00` | dynamic tiles `$6A-$A9` | 7 states; `$00-$05`; decoded | goal-sign presentation supported, not canonical | partial | completion/lifetime study |
| `$1B` | 4 | lower route, Y 864 | `$00` | static shared frame `$0E` | 5 states; decoded | retracting/moving spikes verified | substantial | camera lifetime and complete gameplay damage |
| `$21` | 6 | X 800-3296; Y 254-894 | `$02/$03/$04/$06/$08` | bases `$86/$98` | 7 states; `$00-$02`; decoded | patrol/spring-contact role verified; canonical identity open | complete for THZ1 reachability | semantic identity only; full-emulator observation |
| `$26` | 4 | `(688,864)`, `(3568,768)`, `(1296,608)`, `(1912,864)` | `$00` ×2, `$01`, `$8A` | base `$72` | 10 states; `$00-$03`; decoded | concealed/contact spring verified | substantial | camera lifetime and scheduler integration |
| `$27` | 3 | `(3504,224)`, `(2288,768)`, `(2240,112)` | `$00` | remapped base `$AA` | 4 states; `$00-$02`; decoded | semantic identity unresolved | complete for THZ1 reachability | semantic identity and downstream ordinary-contact meaning |
| `$28` | 6 | two lifts; four diagonal-positioned platforms | `$0A` ×2, `$84` ×4 | base `$6A` | 15 states; `$00/$01`; command `$09` resolved | moving-platform role verified | partial | formal subtype/rider/lifetime study |

## Scope and evidence rules

The counts above are derived from `object-records.json`, then every cached raw
record is checked byte-for-byte against the matching ROM. The census also runs
the existing mapping anchors for `$21/$26/$27/$28`, animation anchors for
`$1B/$26`, and exact placement comparisons against the dedicated `$10`, `$21`
and `$27` caches.

The evidence labels mean:

- **decoded data**: fields or tables extracted from the matching ROM;
- **byte-verified assembly**: a registered recovered region reconstructs the
  original bytes;
- **source-traced behavior**: control flow was followed in original code;
- **controlled original-Z80 trace**: original instructions ran with recorded
  RAM fixtures;
- **gameplay observation**: explicitly identified emulator/video observation;
- **inference / unresolved**: not promoted to verified behavior.

Static state-table length and script reachability do not by themselves prove
object behavior. The complete per-frame mapping records, state-script pointers,
graphics load records, field variants, artifact links, and research-status
facets are retained in the JSON rather than repeated here.

The separately cached **142 ring positions** are decoded from ring pixels in
THZ1 layout blocks `$40..$43`. They are a different source population from the
24 raw type-`$09` object records. Current evidence does **not** establish that
one is an expansion of the other, so neither count is substituted for the
other.

## `$09`

### What is verified

There are 24 raw records. All have flags `$00`, aux0 `$00`, and aux1 `$00`.
The animation type-table entry is ROM `$065CA`; bank `$0C` state table
`$9BC8` (ROM `$31BC8`) has four statically determined states. All scripts
decode with the currently verified command set and reach mapping frames
`$00-$06`. Mapping `$8C71` (ROM `$3CC71`) resolves the shared empty frame and
object-specific frame records `$8CE3/$8CEE/$8CF9/$8D04/$8CAC/$8CB7` in bank
`$0F`. The static THZ1 common graphics stream supplies the reachable tile
range `$10-$22`.

| Record | ROM | World `(X,Y)` | Flags | Param | aux0 | aux1 |
|---:|---:|---:|---:|---:|---:|---:|
| 14 | `$70623` | `(3124,548)` | `$00` | `$00` | `$00` | `$00` |
| 15 | `$7062C` | `(3160,522)` | `$00` | `$00` | `$00` | `$00` |
| 16 | `$70635` | `(3208,512)` | `$00` | `$00` | `$00` | `$00` |
| 17 | `$7063E` | `(2880,384)` | `$00` | `$00` | `$00` | `$00` |
| 18 | `$70647` | `(2832,448)` | `$00` | `$00` | `$00` | `$00` |
| 19 | `$70650` | `(2840,408)` | `$00` | `$00` | `$00` | `$00` |
| 20 | `$70659` | `(2928,448)` | `$00` | `$00` | `$00` | `$00` |
| 21 | `$70662` | `(2920,408)` | `$00` | `$00` | `$00` | `$00` |
| 37 | `$706F2` | `(3367,830)` | `$00` | `$00` | `$00` | `$00` |
| 38 | `$706FB` | `(3394,798)` | `$00` | `$00` | `$00` | `$00` |
| 39 | `$70704` | `(3422,774)` | `$00` | `$00` | `$00` | `$00` |
| 40 | `$7070D` | `(816,844)` | `$00` | `$01` | `$00` | `$00` |
| 41 | `$70716` | `(864,844)` | `$00` | `$01` | `$00` | `$00` |
| 42 | `$7071F` | `(944,844)` | `$00` | `$01` | `$00` | `$00` |
| 43 | `$70728` | `(1040,844)` | `$00` | `$01` | `$00` | `$00` |
| 44 | `$70731` | `(1728,588)` | `$00` | `$01` | `$00` | `$00` |
| 45 | `$7073A` | `(1760,588)` | `$00` | `$01` | `$00` | `$00` |
| 46 | `$70743` | `(1856,588)` | `$00` | `$01` | `$00` | `$00` |
| 47 | `$7074C` | `(1968,588)` | `$00` | `$01` | `$00` | `$00` |
| 48 | `$70755` | `(2048,588)` | `$00` | `$01` | `$00` | `$00` |
| 49 | `$7075E` | `(2080,588)` | `$00` | `$01` | `$00` | `$00` |
| 50 | `$70767` | `(2400,684)` | `$00` | `$01` | `$00` | `$00` |
| 51 | `$70770` | `(2512,684)` | `$00` | `$01` | `$00` | `$00` |
| 52 | `$70779` | `(2640,684)` | `$00` | `$01` | `$00` | `$00` |

### What is partially established

Reconstructed reachable graphics support a ring/sparkle-family description,
but that visual result is not evidence that every frame or state has the same
semantic role. Placement completeness and animation reachability are complete;
object behavior is not.

### What remains unresolved

Parameter `$00` versus `$01`, runtime entity generation, collection, sparkle
selection, persistence, and respawn need a dedicated source/trace study. The
relationship—if any—to the 142 layout-derived ring positions is unresolved.

## `$10`

### What is verified

Five records use flags/aux fields `$00`. Animation entry ROM `$065D8` selects
bank `$0C` table `$A101` (ROM `$32101`), four states, with fully decoded static
reachability to frames `$00/$0B/$0C`. Shared mapping `$8C71` (ROM `$3CC71`)
resolves object-specific frame records `$8D0F/$8D1A`; the common static stream
supplies tile offsets `$4C-$5C`.

| Record | ROM | World `(X,Y)` | Flags | Param | aux0 | aux1 |
|---:|---:|---:|---:|---:|---:|---:|
| 9 | `$705F6` | `(656,846)` | `$00` | `$06` | `$00` | `$00` |
| 10 | `$705FF` | `(1712,494)` | `$00` | `$06` | `$00` | `$00` |
| 11 | `$70608` | `(336,270)` | `$00` | `$04` | `$00` | `$00` |
| 12 | `$70611` | `(1472,110)` | `$00` | `$04` | `$00` | `$00` |
| 13 | `$7061A` | `(2688,686)` | `$00` | `$02` | `$00` | `$00` |

### What behavior is verified

Recovered scripts and controlled original-routine traces establish all four
states, 10×24 runtime extents, strict overlap boundaries, required player flag
`$D503.1`, top/side downward-motion checks, bottom-hit launch, parameter-to-
`$D3A3` masks, numeric reward dispatch, type-`$0F` replacement, score addition,
and placement occupancy behavior. Frames `$0B/$0C` alternate in both active
state 2 and airborne state 3; destruction presentation is type `$0F` frames
`$07/$08/$09`, not `$0B/$0C`.

Parameter `$02` queues bit 1 and increments BCD `$D299` with sound `$A9`.
Parameter `$04` queues bit 3 and, for player type `$01`, sets `$D532=$04`, a
300-count timer, sound `$85`, and player state `$11`. Parameter `$06` queues
bit 5, sets `$D532=$06`, a 600-count timer, flags `$D503.1/.7`, sound `$84`,
and allocates type `$05` parameter zero when newly selected. These numeric
effects are not assigned conventional item names.

Untouched or bottom-hit-only instances retain their placement token; tracked
off-range cleanup releases occupancy and permits respawn. Successful conversion
clears the token while leaving occupancy nonzero, so a consumed placement does
not respawn during the same loaded act.

### What remains unresolved

The canonical name, user-facing names for `$02/$04/$06`, semantic names for the
numeric sound/RAM effects, complete type-`$05` child behavior, and full-emulator
gameplay timing remain unresolved. See `docs/object-10.md`.

## `$18`

### What is verified

Record 53 is ROM `$70782`, world `(3960,558)`, flags/parameter/aux fields all
`$00`. Animation entry ROM `$065E8` selects bank `$0C` table `$A7BC` (ROM
`$327BC`), seven states, with fully decoded reachability to frames `$00-$05`.
Mapping `$8EAE` (ROM `$3CEAE`) resolves specific records `$8EBA/$8EC5/$8ED0/
$8EDB/$8EE6`.

The dynamic path is verified: state logic writes selector `$12` to `$D3B3`;
the `$7BA6` pointer table selects list `$7BCB`, which loads 16 tiles from bank
`$0D:$96BC` (ROM `$356BC`) to VRAM `$0D40` and 48 tiles from bank `$09:$8640`
(ROM `$24640`) to VRAM `$0F40`. Together these replace tiles `$6A-$A9` and
produce the coherent rotating goal-sign presentation.

### What is partially established

Graphics, mapping, and static animation reachability are complete. The visual
result supports an end-of-act goal-sign/signpost role, but there is no dedicated
behavior study comparable to `$21` or `$27`.

### What remains unresolved

Trigger/contact rules, completion logic, exact state timing, lifetime, and the
stage-results transition remain to be formally source-traced and controlled-
traced. Frame meanings must not be assigned from appearance alone.

## `$1B`

### What is verified

Animation entry ROM `$065EE` selects bank `$0C` table `$AC4A` (ROM `$32C4A`),
five decoded states, all reaching shared mapping frame `$0E` at record `$8D30`
under mapping `$8C71` (ROM `$3CC71`). The common static graphics use tile
offsets `$62/$64`. Recovered `spike_object_handlers.asm` and
`spike_object_scripts.asm` establish an 18-pixel rise, raised hold, retraction,
hidden hold, and damage checks only in rising/raised states.

| Record | ROM | World `(X,Y)` | Flags | Param | aux0 | aux1 |
|---:|---:|---:|---:|---:|---:|---:|
| 33 | `$706CE` | `(1344,864)` | `$00` | `$00` | `$00` | `$00` |
| 34 | `$706D7` | `(1936,864)` | `$00` | `$00` | `$00` | `$00` |
| 35 | `$706E0` | `(2464,864)` | `$00` | `$00` | `$00` | `$00` |
| 36 | `$706E9` | `(2912,864)` | `$00` | `$00` | `$00` | `$00` |

### What is partially established

Selected original handlers were compared in `windows-poc-15-objects.json`.
This verifies core rise/retract arithmetic, not full scheduler or gameplay
damage aftermath.

### What remains unresolved

Camera activation/despawn, occupancy release/respawn, complete damage aftermath,
and full gameplay scheduling remain unverified.

## `$21`

### What is verified

The dedicated [type `$21` study](object-21.md) is complete for THZ1-reachable
behavior. Animation entry ROM `$065FA` selects bank `$0C` table `$B1B6` (ROM
`$331B6`), seven decoded states, frames `$00-$02`. Mapping `$911B` (ROM
`$3D11B`) resolves specific records `$9121/$912C`. Collision extents are 11
horizontal and 26 vertical. Bit 4 selects mirrored X coordinates and aux1
`$98`; patrol scripts set it for negative-X orientation and clear it for
positive-X orientation. Parameter is a leftward span in units of 16 pixels.

| Record | ROM | World `(X,Y)` | Flags | Param | aux0 | aux1 |
|---:|---:|---:|---:|---:|---:|---:|
| 27 | `$70698` | `(800,606)` | `$00` | `$08` | `$86` | `$98` |
| 28 | `$706A1` | `(1248,862)` | `$00` | `$06` | `$86` | `$98` |
| 29 | `$706AA` | `(2048,318)` | `$00` | `$06` | `$86` | `$98` |
| 30 | `$706B3` | `(3152,894)` | `$00` | `$03` | `$86` | `$98` |
| 31 | `$706BC` | `(3296,286)` | `$00` | `$04` | `$86` | `$98` |
| 32 | `$706C5` | `(2400,254)` | `$00` | `$02` | `$86` | `$98` |

### What is partially established

The possible canonical identity remains supported but non-canonical. The formal
result is source-traced and controlled original-Z80 work, not a full-emulator
gameplay observation.

### What remains unresolved

Only canonical semantic identity and full-emulator/gameplay confirmation prevent
a stronger classification. Placement, behavior, animation, contact, orientation,
and lifetime paths are verified.

## `$26`

### What is verified

Animation entry ROM `$06604` selects bank `$1E` table `$8212` (ROM `$78212`),
ten decoded states, frames `$00-$03`. Mapping `$91C0` (ROM `$3D1C0`) resolves
specific records `$91C8/$91D3/$91DE`; all records use supplemental base `$72`.
Recovered fixed and span handlers establish strong/weak impulses, extension,
hold, and retraction. Parameter `$8A` is a 160-pixel concealed span form, not a
weak fixed spring.

| Record | ROM | World `(X,Y)` | Flags | Param | aux0 | aux1 | Verified form |
|---:|---:|---:|---:|---:|---:|---:|---|
| 7 | `$705E4` | `(688,864)` | `$00` | `$00` | `$72` | `$72` | fixed strong |
| 8 | `$705ED` | `(3568,768)` | `$00` | `$00` | `$72` | `$72` | fixed strong |
| 22 | `$7066B` | `(1296,608)` | `$00` | `$8A` | `$72` | `$72` | concealed 160-pixel span, weak |
| 23 | `$70674` | `(1912,864)` | `$00` | `$01` | `$72` | `$72` | fixed weak |

### What is partially established

Core behavior has recovered assembly and selected original-Z80 comparisons.
The contact window is measured against object Y minus 28; this is not presented
as a complete generic collision-extent study.

### What remains unresolved

Camera activation/removal, occupancy/respawn, complete scheduler/animation
timing, and gameplay contacts at every placement remain to be formally tested.

## `$27`

### What is verified

The dedicated [type `$27` study](object-27.md) is complete for THZ1-reachable
behavior. Animation entry ROM `$06606` selects bank `$1E` table `$8947` (ROM
`$78947`), four decoded states, frames `$00-$02`. Mapping `$91F5` (ROM
`$3D1F5`) resolves records `$91FB/$9206`. All records set orientation bit 4
and use remapped base `$AA`; collision extents are 9 horizontal and 14 vertical.
The strict `<64` activation, 129-update sequence, `>=384` removal, attack defeat,
ordinary overlap, orientation, cleanup, and respawn chain are controlled-traced.

| Record | ROM | World `(X,Y)` | Flags | Param | aux0 | aux1 |
|---:|---:|---:|---:|---:|---:|---:|
| 24 | `$7067D` | `(3504,224)` | `$10` | `$00` | `$AA` | `$AA` |
| 25 | `$70686` | `(2288,768)` | `$10` | `$00` | `$AA` | `$AA` |
| 26 | `$7068F` | `(2240,112)` | `$10` | `$00` | `$AA` | `$AA` |

### What is partially established

Coherent graphics and fully traced behavior still do not establish a canonical
semantic identity. Ordinary overlap performs generic contact bookkeeping but
the tested callback does not request damage.

### What remains unresolved

Semantic identity, the broader downstream interpretation of ordinary-contact
bookkeeping, and full-emulator gameplay observation remain open.

## `$28`

### What is verified

Six decoded moving-platform records use mapping `$9217` (ROM `$3D217`) and
specific frame `$921B`, with supplemental base `$6A`. Animation entry ROM
`$06608` selects bank `$1E` table `$8439` (ROM `$78439`); its first script
statically implies 15 states. Reachable decoded frames are `$00/$01`.
Recovered `platform_code.asm` and `platform_reverse.asm` plus earlier research
establish two parameter-`$0A` lifts and four parameter-`$84` sag/bob platforms.

| Record | ROM | World `(X,Y)` | Flags | Param | aux0 | aux1 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | `$705AE` | `(592,464)` | `$00` | `$0A` | `$6A` | `$09` |
| 2 | `$705B7` | `(3664,512)` | `$00` | `$0A` | `$6A` | `$0D` |
| 3 | `$705C0` | `(1040,384)` | `$00` | `$84` | `$6A` | `$00` |
| 4 | `$705C9` | `(1136,320)` | `$00` | `$84` | `$6A` | `$00` |
| 5 | `$705D2` | `(1232,256)` | `$00` | `$84` | `$6A` | `$00` |
| 6 | `$705DB` | `(1328,208)` | `$00` | `$84` | `$6A` | `$00` |

### What is partially established

The two lifts initially move upward one pixel per update and reverse after 144
and 208 updates respectively; the four `$84` platforms have an eight-pixel
sag/bob limit. Recovered rider paths exist, but the census does not promote
adapter/video observations to complete original behavior. The aux1 values are
consumed as object-specific initialization data and are not uniformly a second
graphics art base.

### What remains unresolved

Animation states 4, 12, and 14 use command `$09`, now byte-verified as a
four-byte `object[offset] = immediate` operation. A formal
study must cover subtype initialization, rider/contact edges, activation,
despawn, occupancy/respawn, and distinguish source-traced behavior from the
earlier adapter.

## Prioritized research backlog

### Object behavior still needing formal trace

1. **Type `$18` completion/lifetime study.** Dynamic graphics are already
   complete, isolating the remaining end-of-act behavior question.
2. **Type `$09` parameter/entity-generation/collection study.** This must
   explain the 24 raw records without assuming a relationship to the separate
   142 layout-derived positions.
3. **Type `$28` formal platform study.** Its larger rider/lifetime dependencies
   make it less isolated than `$10`.

### Graphics, palette, and mapping gaps

All eight placed types now have no unresolved states under the currently
verified animation-command set. This does not imply their
behaviors are complete.

### Placement/entity expansion gaps

Determine the runtime meaning of type-`$09` parameter `$00/$01` and whether its
records generate multiple entities. Preserve the independent 142-position
layout-ring cache until source evidence proves a relationship.

### Generic engine dependencies

Camera eligibility, removal, occupancy release, and respawn need formal studies
for `$1B`, `$26`, and `$28`. Full scheduler/gameplay validation remains absent
for all results currently based on subroutine fixtures.

### POC integration-ready research

Types `$10`, `$21` and `$27` have complete formal THZ1 behavior studies. The `$26`
and `$1B` core state machines are substantially recovered, but their generic
lifetime and integration checks remain explicit prerequisites. No conclusion
in this census uses the current POC as evidence for original-ROM behavior.

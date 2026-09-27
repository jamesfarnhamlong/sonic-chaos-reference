# THZ1 final runtime / entity closure

Task 08 uses the canonical ROM SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
POC comparison is read-only against the latest pushed POC 18.5 commit
`726b16eafbc92d4240fa182bb6ef699cfbcf923a`; the newer local Windows integration
is not repository evidence.

## Five closure conclusions

1. **TYPE `$21` VISUAL HOVER — POC RENDERING BUG.** The conspicuous gap is
   overwhelmingly canonical: the ROM leaves 17 blank scanlines. POC 18.5 is
   additionally one pixel too high because it omits the SMS SAT Y+1 convention.
2. **TYPE `$09` — IMPLEMENTATION READY.** There are 24 raw records and exactly
   24 runtime entities: 11 visible rotating collectibles and 13 invisible,
   even-frame collectible triggers.
3. **BLOCK `$47` — INTERACTIVE TERRAIN.** It is breakable terrain, not static
   decoration and not a placement generator. Its red/magenta POC colour is not
   canonical; breaking it awards ten rings, changes it to `$46`, and creates a
   transient type `$0F`.
4. **TYPE `$27` APPEARANCE — POC LIFETIME/PRESENTATION BUG.** The original can
   legitimately first display it inside the viewport, but only through its
   two-axis visibility grid and two-update empty-frame sequence. POC 18.5 makes
   it visible immediately in a much wider X-only range.
5. **THZ1 POC ENTITY COVERAGE — INCOMPLETE.** POC 18.5 represents 29 of the 53
   raw records. All 24 type-`$09` records—indices 14–21 and 37–52—are missing.
   It also renders block `$47` artwork without its separate terrain behavior.

## Type `$21`: anchor to SAT

The fixed physics result remains unchanged: floor lookup samples anchor Y+18
and projects the unshifted anchor to surface-18. Generic `$3FC8` writes
`screen_y = object +$14/+$15 - camera $D176` to `+$1C/+$1D`. Frames `$01/$02`
have Y origin 0 and six piece coordinates at -32/-16; mirroring changes the X
stream and art base, not Y. `$226A` adds screen anchor, origin and piece Y,
writes the raw SAT byte, and writes `$E0` only for clipped pieces. The SMS
displays SAT Y on scanline Y+1.

Nonzero source pixels occupy raw relative Y -32..-1, so displayed pixels occupy
world `anchor-31..anchor`. All placements therefore have the same 17-row gap:

| Placement | Stable anchor | Surface | Visible top..bottom | Blank rows |
|---|---:|---:|---:|---:|
| `(800,606)` | 590 | 608 | 559..590 | 17 |
| `(1248,862)` | 846 | 864 | 815..846 | 17 |
| `(2048,318)` | 302 | 320 | 271..302 | 17 |
| `(3152,894)` | 878 | 896 | 847..878 | 17 |
| `(3296,286)` | 270 | 288 | 239..270 | 17 |
| `(2400,254)` | 238 | 256 | 207..238 | 17 |

Controlled `$3FC8/$226A` fixtures for X=800, 3296 and 2400 place screen anchor
at 100 and produce SAT bytes `68,68,68,84,84,84`; displayed piece tops are
69/85. POC's 32×40 image has nontransparent rows 4..35 and yorigin 36, yielding
relative -32..-1 without SAT bias. The exact render-only correction is draw Y+1
or yorigin 35. Do not change anchor, +18 probe, contacts or room placements.

## Type `$09`

The full state, parameter, collection and lifetime study is in
`object-09.md`. Parameter `$00` rotates and then sparkles for 32 updates;
parameter `$01` is invisible, checks strict 12×12-axis proximity on even global
frames, and disappears immediately. Both add one to packed-BCD ring counter
`$D29A`, request sound `$BF`, clear the placement token and persist as collected.
Uncollected off-screen instances release occupancy and can recreate.

## Block `$47`

Layout decompression independently gives `$47` at cells `(104..107,8)`, world
origins `(3328,256)` through `(3424,256)`. Pointer entry ROM `$4408E` selects
mapping `$8A20` / ROM `$44A20`. Its artwork attributes use priority and palette
1 (`$06`) for tiles `$117-$11D`, including X flips at the right edges; the
palette-aware RGBA block hash is
`ec9e7afdafe3b1494082e1900e271643a651b19755cf23904211a3ecb42b4e3d`.
POC 18.5's same-cell hash is
`2be2a042d43ba29d7b3317628eb522d027ae4723b131ff2dcdddb823778c72ed`.
It used background palette `$15` for every nonzero pixel and therefore appears
red/magenta. The attributes select palette 1 (`$06`), producing the canonical
orange/yellow/grey monitor-like art. The red/magenta colour is **not canonical**.

Collision pointer entry `$3808E` selects `$83F1`. Base header
`96 00 D0 8C 10 95 FF` has surface `$16`, a vertical profile of
`17,17,18×28,17,17`, and horizontal profile `00×8,1C×24`. Its `$6AE3` callback
accepts qualifying airborne/rolling contact (excluding states `$0F/$10/$15/$1A`)
and routes to `$7857`. That handler changes the cell to `$46`, refreshes its
mapping, sets graphics selector 1, allocates type `$0F` parameter `$40`, and
adds packed-BCD `$10`—ten—to `$D29A`. Alternate header
`B0 00 F0 8C 30 95 FF` is empty-profile plane behavior through `$6C82`.

No scanner recognizes block ID `$47`; behavior arises from its collision header.
There is no relationship to type `$09`, type `$10`, or blocks `$40-$43`, beyond
the fact that `$47` and collectibles can update the same ring counter.

## Type `$27` creation and display

The placement scan runs every four object updates. Its grid accepts relative X
and Y -96..351, keeps -32..287 active/SAT-eligible, and treats the outer band as
created but sleeping. Creation happens after the object scheduler with zero
pieces. The next update runs empty state 0 and requests state 1. The second
update loads nonempty frame 1; lifetime can then clear bit 6 for SAT output.
Frame `$01/$02` nonzero pixels occupy relative X -12..11 and displayed Y -14..0.

| Object | Creation camera X | Active/SAT camera X | First pixel camera X | First pixel camera Y |
|---|---|---|---|---|
| `(3504,224)` | 3153..3600 | 3217..3536 | 3237..3515 | 19..224 |
| `(2288,768)` | 1937..2384 | 2001..2320 | 2021..2299 | 563..768 |
| `(2240,112)` | 1889..2336 | 1953..2272 | 1973..2251 | -93..112 |

Camera-Y creation and active ranges are respectively object Y-351..Y+96 and
object Y-287..Y+32; exact values are cached. A late scan/camera jump can create
inside the active rectangle, so first display two updates later can already be
inside 256×192. With steady left-to-right scrolling it is created in the hidden
margin, becomes SAT-eligible at relative X 287, and pixels enter at 267.

POC 18.5 instead uses an X-only range from camera-128 through viewport+384,
starts directly in state 1 and sets `visible=true` immediately. That is not the
original lifetime/presentation sequence. Pre-trigger ROM cleanup outside the
accepted rectangle releases occupancy; after the strict <64 trigger, state 3's
>=384 separation removal eventually releases it for recreation.

## Complete coverage audit

`poc-coverage.json` contains all 53 record indices and offsets exactly once.
Types `$10/$18/$1B/$21/$26/$27/$28` account for 29 exact placed POC resources.
The missing records are:

`14,15,16,17,18,19,20,21,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52`.

Each missing record requires one type-`$09` entity at its cached coordinate and
parameter. The 142 terrain-ring positions remain separately represented by the
POC adapter. The four `$47` cells and other terrain interactions are also a
separate population; static pixels do not implement `$47`'s break callback.

**Does the current POC instantiate or otherwise faithfully represent every
gameplay-relevant THZ1 entity implied by the ROM? NO, WITH EXACT MISSING
RECORDS/ENTITIES.**

## POC 19 implementation contract

1. Add exactly 24 one-to-one numeric type-`$09` instances with the parameter,
   overlap, counter, presentation, occupancy and respawn behavior above.
2. Move only type-`$21` rendering down one scanline (draw Y+1 or yorigin 35).
   Preserve its physics anchor, +18 probe, contacts and room coordinates.
3. Regenerate `$47` pixels with per-piece palette bit 11 (`$06` for its nonzero
   art), then implement it as collision-driven breakable terrain: eligibility
   from `$6AE3`, replacement `$46`, type-`$0F`/parameter-`$40` transient, and
   ten-ring `$D29A` effect. Do not replace the cells with type `$10` objects.
4. Replace type-`$27`'s immediate X-only visibility with the original two-axis
   accepted/active grid and two-update empty-to-frame-1 timing.
5. Keep the 142 block-`$40..$43` ring positions separate from all 24 type-`$09`
   records and from block `$47`.

## Recovery and verification

Task 08 adds six genuine regions: generic object screen preparation, the type
`$09` scripts/handlers, the layout-ring handler/tables and block `$47`'s surface
handler. Totals move from 64/12,240/4,731 to **70 recovered regions, 12,678
bytes and 4,878 decoded instructions**. Nineteen new controlled original calls
(15 type `$09`, three SAT-render fixtures, one `$47` reward) move comparisons
from 37,630 to **37,649**. Full reconstruction remains 524,288-byte identical.

## THZ2/THZ3 rollout readiness

The placement decoder, state-script tooling, generic visibility/lifetime model,
collision-header dispatcher, palette-aware block renderer and population audit
are reusable. Acts 2/3 still require their own layout, object records, graphics
loads, block headers and act-specific callbacks; none are decoded here. Our
layout decoder and deterministic background renderer are canonical ROM checks.
Aspect Edit Plus can independently cross-check resource format and dimensions,
while the user's full-level PNGs can cross-check appearance only; neither is
behavior evidence.

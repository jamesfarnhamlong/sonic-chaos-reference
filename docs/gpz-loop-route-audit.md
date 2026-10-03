# GPZ alternate loop route closure

Evidence: decoded canonical ROM data, source-traced behavior and controlled
execution of original Z80 instructions. ROM SHA-256:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
No POC code was changed. No route was inferred from its visible shape.

## Exact gates

Coordinates are canonical 32-pixel layout-cell origins. The transition is from
the previous foot block `$57` into the adjacent `$52` cell.

| Act | `$57` cell / world origin | `$52` gate cell / world origin |
|---|---|---|
| GPZ1 | (64,8) / (2048,256) | (65,8) / (2080,256) |
| GPZ1 | (79,10) / (2528,320) | (80,10) / (2560,320) |
| GPZ2 | (58,7) / (1856,224) | (59,7) / (1888,224) |
| GPZ3 | (23,6) / (736,192) | (24,6) / (768,192) |

These are all four `$57` placements in the decoded GPZ1/2/3 loaded layouts;
every one has `$52` immediately to its right. See `gates` in the generated cache
for map widths and loaded-cell indices.

## Entry chain and collision profiles

`$691A` saves the previous **foot** block `$D36B` into `$D497`, performs the
current foot lookup `$7666`, stores the new block in `$D36B`, projects the floor
through `$6F61`, then dispatches on the newly sampled surface low five bits.
`$D497` is not the last side/ceiling sample.

Surface `$10` dispatches to `$6C82`. Its block dispatch table `$6C99` selects
`$6CCD` for current block `$52`. `$6CCD` requires:

- player `+$25` equals zero (plane 0);
- player `+$22` bit 1 is set (floor contact after the projection);
- previous foot block `$D497` equals `$57`.

It jumps to `$3EF7`, which requests **hex `$13` (decimal 19)**. This is distinct
from `$3EE1`, which requests **decimal 13 / hex `$0D`**. There is no player-state,
attack-bit, facing or horizontal-speed check in this entry helper. The 576-case
original block-dispatch matrix includes speed -4/0/+4 and states `$01/$05/$09/$0A`.
Actual floor projection has its ordinary previous-surface, height and Y-speed
conditions; the helper's absence of a speed test does not imply successful
traversal at zero speed.

The ROM profiles are shared, independent of act:

| Block / plane | Header file offset / bank CPU | Flags | Modifier | Vertical profile file |
|---|---|---|---|---|
| `$57`, either plane | `$384C3` / `$0E:$84C3` | `$90` | `$00` | `$38F30` |
| `$52`, plane 0 | `$38484` / `$0E:$8484` | `$B0` | `$0E` | `$38F70` |
| `$52`, plane 1 | `$3848B` / `$0E:$848B` | `$90` | `$14` | `$38F90` |

`$52` flags bit 5 selects its second header on plane 1. Both headers have surface
low bits `$10`. Complete profile bytes and pointers are decoded in the cache.

`$3EF7` shares setup `$3EAF..$3EDF` with the other loops:

- `X := X & ~31`; save X into `+$3A/+$3B`;
- `Y := (Y & ~31) + 4`; save Y into `+$3C/+$3D`;
- clear all three bytes `$D39D/$D39E/$D39F` (route progress);
- preserve X/Y velocity, plane, attack/airborne flags, and subpixel position bytes.

Only the requested state `+$02` changes at contact; current state `+$01` changes
on the next animation-engine update. The setup discards one stacked return with
`POP AF`: it leaves the terrain pass early, skipping that pass's remaining side,
ceiling and terrain-ring checks. This is a control-flow effect, not just a state
assignment.

## State `$13` traversal

Player bank `$0C` state-table entry `$8026` points to script `$81BE` (file
`$301BE`). The script uses the shared loop frame selector `$903D` and callback
vector `$03CE -> $3CFC`. The selector selects presentation from progress or the
inherited attack posture; it does not change movement/contact geometry.

`$3CFC` pages bank `$0D` and implements:

1. Add unsigned 8.8 X velocity to the 24-bit 16.8 progress `$D39D..$D39F`.
2. Set integer Y from origin Y plus the signed word at `$0D:$8DDC + 2*p`
   (file `$34DDC`), and X from origin X plus the word at `$0D:$9140 + 2*p`
   (file `$35140`), where `p = progress >> 8`.
3. For `p < $90` (144), subtract `$000A` (10/256 pixel/update) from X velocity.
   On unsigned borrow, take the slow-route bailout below.
4. At `p >= 144`, set plane to 1 and add `$000C` (12/256 pixel/update) to X
   velocity. The plane switch occurs on this same update, after the table position.
5. Call the ordinary damage/contact routine `$48BC`. It remains active.
6. At `p >= $1A0` (416), request `$0A`, set Y velocity to `$D373` (4.0 in the
   fixture), zero X velocity, set airborne and attack bits `+$03` bits 0/1,
   and clear floor bit `+$22` bit 1.

While the route is active, `$690B` and ordinary terrain profile lookup `$7666`
are not called. It follows the ROM coordinate tables rather than projecting onto
the visible blocks. Terrain rings consequently do not run during this state.
The plane is preserved as 1 on successful exit. On the next actual ordinary
player callback, current state becomes `$0A`, gravity/movement and `$690B/$7666`
resume on plane 1. The fixture traces this update; no implicit plane reset exists.
Table lookup precedes the 416 exit comparison; index 416 is read by the standard
fixture. Do not truncate the imported tables to indices 0..415 or clamp progress
before lookup. An exit update can overshoot 416 according to incoming velocity;
this audit does not claim arbitrary oversized/negative speeds are safe table indices.

Held Right, held Left, held action and continuously written pressed-action bits
produce the same route as released input. State `$13` does not consult those
input bytes. An attacking entry preserves attack throughout; the successful exit
sets attack even for a non-attacking entry.

## Slow-route bailout

If the pre-midpoint velocity subtraction borrows, `$3D5F` jumps into the common
`$3CC5` bailout. If current X is at/before origin X, it adds 8 to X; otherwise it
subtracts 2. `$4680` requests `$1D`, sets Y velocity to +0.5, sets airborne,
clears attack and floor, and leaves X velocity and plane unchanged.

For a fresh route with progress zero and positive 8.8 X speed, the exact minimum
for reaching the midpoint is `$0356` (854/256 = 3.3359375). `$0355` fails on update
86; `$0356` completes on update 190. This follows the discrete progress-before-
deceleration ordering. It is not an entry speed gate. The zero-speed fixture
enters `$13` and bails out on its first route update. Signed negative-speed entry
is possible in the helper, but successful negative traversal of this unsigned
right-entry route is not claimed.

## Relationship to THZ loops

This is the same shared surface/block dispatch and entry setup used by the other
loops, with a distinct state callback, coordinate tables and exit branch. There
is no GPZ zone-ID check in this path:

- plane 0, current `$52`, previous `$51` requests `$0C` via `$3EAB`;
- plane 1, current `$51`, previous `$52` requests `$0D` via `$3EE1`, which first
  adds 32 to X before the shared snap;
- plane 0, current `$52`, previous `$57` requests `$13` via `$3EF7`.

The metadata/block transition selects the alternate route. Reusing a full-loop
table or requiring a registered THZ loop origin would lose this behavior.

## Reproduction and limits

Run with the verified, local-only ROM:

```text
.venv/Scripts/python.exe tools/gpz_loop_route.py "../source/Sonic Chaos (Europe).sms"
.venv/Scripts/python.exe tools/gpz_loop_route.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe -m unittest discover -s tests -p test_gpz_loop_route.py -v
```

The cache contains four complete entry/traversal/exit fixtures, 576 block-dispatch
controls, nine complete route controls and 24 fractional progress/velocity
boundary cases. Each four-gate fixture enters at gate X+2/Y+1 with X speed +4.0,
Y speed +7.0 and previous foot block `$57`. Projection plus setup snaps to
gate X/Y+4. Plane changes on route update 47; update 117 requests `$0A` at
origin X-50/Y+103, X speed 0, Y speed +4.0. The next update executes ordinary
terrain collision on plane 1. The relative route is identical at all four gates.

The original animation engine and callbacks run without replacement instructions.
Only RAM, the mapper, breakpoints and return addresses are supplied by the oracle.
The next ordinary update uses a supplied camera X = player X-104 so the canonical
SMS edge clamp does not interfere with the isolated test. These are controlled
original-routine fixtures, not rendered original-game observation or a full
interrupt/object/camera schedule. Windows presentation comparison remains for POC.

## AGENTS candidate update

GPZ alternate loop entry is plane-0 floor contact with current foot block `$52`
and previous foot block `$57`, requesting hex `$13` (decimal 19). The four gates
are GPZ1 `(2080,256)` and `(2560,320)`, GPZ2 `(1888,224)`, GPZ3 `(768,192)`.
The shared loop setup snaps/saves origin X to a 32-pixel boundary and Y to the
boundary+4, preserves velocities/attack flags, and clears route progress.
State `$13` uses bank `$0D` tables `$8DDC/$9140`, changes plane to 1 at progress
144, and at progress 416 requests `$0A`, X speed 0, Y speed `$D373`, airborne/
attack set and floor clear. Ordinary terrain resumes on the next player update
with plane 1 retained. Slow pre-midpoint traversal bails through `$4680` to `$1D`.

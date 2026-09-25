# THZ1 object type `$21`

This document applies only to the 524,288-byte Master System ROM with SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
CPU addresses in `$8000..$BFFF` name the stated slot-2 bank; `ROM` always means a
file offset. The principal object code is bank `$0C`, CPU `$B1B6..$B2F8`, ROM
`$331B6..$332F8`.

## Result

Type `$21` is a ground patrol object with a spring-like top contact. A THZ1
record creates it at the decoded placement position. Initialization consumes
the parameter as a leftward patrol span of `parameter * 16` integer pixels,
starts X velocity at `-$0080` and Y velocity at `+$0200` in signed 8.8 units,
and requests patrol state 3. It moves between the computed left bound and its
saved placement X, reverses X velocity after strictly crossing either bound,
and alternates orientation states 3/4.

While the shared overlap routine reports contact, a player at or above
`object_y - 4` is launched with Y velocity `$F940` and player state `$0B`.
Other contact requests damage unless the player's rolling/attack flag is set or
power-up `$06` is active; those two cases apply the generic defeated-enemy
conversion to type `$0F`. Loss of floor contact requests falling state 1.

This is source-traced and controlled-trace behavior, not a full-emulator frame
observation.

## THZ1 placements

The placement loader removes the `$0100` coordinate bias. These are the six
decoded records already cached in `data/rom-cache/thz1/object-records.json`.

| Record ROM | World X | World Y | Flags | Parameter | `aux0` | `aux1` |
|---:|---:|---:|---:|---:|---:|---:|
| `$70698` | 800 | 606 | `$00` | `$08` | `$86` | `$98` |
| `$706A1` | 1248 | 862 | `$00` | `$06` | `$86` | `$98` |
| `$706AA` | 2048 | 318 | `$00` | `$06` | `$86` | `$98` |
| `$706B3` | 3152 | 894 | `$00` | `$03` | `$86` | `$98` |
| `$706BC` | 3296 | 286 | `$00` | `$04` | `$86` | `$98` |
| `$706C5` | 2400 | 254 | `$00` | `$02` | `$86` | `$98` |

## Creation and initialized fields

The placement scan begins at bank `$1C`, CPU `$8000` (ROM `$70000`). It walks
the act's nine-byte records alongside occupancy bytes at `$D400`. A zero
occupancy byte and the scan's camera/map eligibility checks allow creation.
The common placement creator is bank `$1C:$80EB` (ROM `$700EB`). It calls the
badnik-slot allocator through fixed vector `$0329` (`$5EE1`), which searches 11
slots beginning at `$D700` in `$40`-byte steps.

The creator copies these record fields before type `$21` runs:

| Object field | Value/source | Evidence |
|---:|---|---|
| `+$00` | type `$21` | `$80F2..$80F6` |
| `+$11/+$12` | current integer X | `$80F7..$8105` |
| `+$3A/+$3B` | saved placement X | `$80F7..$8105` |
| `+$14/+$15` | current integer Y | `$8108..$8116` |
| `+$3C/+$3D` | saved placement Y | `$8108..$8116` |
| `+$04` | record flags OR `$40` | `$8119..$811D` |
| `+$3F` | placement parameter | `$8120..$8122` |
| `+$08` | `aux0`, `$86` in THZ1 | `$8125..$8127` |
| `+$09` | `aux1`, `$98` in THZ1 | `$812A..$812C` |
| `+$3E` | one-based `$D400` occupancy token | `$812F..$8138` |

Object state 0's callback is bank `$0C:$B210` (ROM `$33210`). It writes:

- requested state `+$02 = 3`;
- signed 8.8 X velocity `+$16/+$17 = $FF80`;
- signed 8.8 Y velocity `+$18/+$19 = $0200`;
- `+$03` bit 7 set;
- left bound `+$37/+$38 = current_integer_x - (parameter << 4)`;
- `+$3F = 0` after consuming the parameter.

It does not change current X or Y. If incoming `+$04` bit 4 is set, it instead
stores `1` at `+$3F`, clears `+$04`, and requests state 5. Every THZ1 record has
flags `$00`, so the loader supplies only bit 6 and this alternate initialization
path is not THZ1-reachable.

The generic scheduler at fixed CPU `$5DD1` updates 19 slots. Types below `$26`
map bank `$0C`, run the animation/state engine at `$64FA`, call the callback
stored at object `+$0C/+$0D`, and then run the visibility/lifetime routine when
current state `+$01` is nonzero.

## Parameter and patrol arithmetic

The parameter is a byte multiplied by 16 through four `SLA E` / `RL D` pairs at
`$B238..$B246`. No clamp or table lookup is present. The resulting word is
subtracted from the placement X and saved as the left bound.

The patrol callback is `$B268` (ROM `$33268`):

1. Return immediately while `+$04` bit 6 is set.
2. Integrate signed 8.8 X/Y velocity through fixed vector `$0338` (`$60FB`).
3. Run generic object floor projection through `$0320` (`$77CB`).
4. If floor-contact bit 1 at `+$22` is clear, request state 1 and return.
5. Unless `$D12F` bit 0 is set, call `$62D5` to test the active X bound.
6. On strict overshoot, call `$62F7` to negate X velocity and toggle 3↔4 or
   5↔6 according to the latch at `+$3F`.
7. Run contact handling at `$B2AF`.

For negative velocity, `$62D5` tests `current_integer_x - left_bound` and
reverses only on borrow. For positive velocity it tests
`saved_origin_x - current_integer_x` and again reverses only on borrow. Equality
does not reverse. At speed `$0080` this produces a half-pixel overshoot before
the integer coordinate crosses the bound.

Controlled execution of the original callbacks against the decoded THZ1 map
produced:

| Placement | Parameter | Computed left bound | First reversal | Return reversal |
|---|---:|---:|---|---|
| `(2400,254)` | `$02` | 2368 | update 65, X=`2367.5`, state 3→4 | update 132, X=`2401.0`, state 4→3 |
| `(800,606)` | `$08` | 672 | update 257, X=`671.5`, state 3→4 | update 516, X=`801.0`, state 4→3 |

Thus the nominal endpoint separation is exactly 32 versus 128 pixels; the
strict integer comparison explains the observed endpoint overshoot.

Y is not a fixed placement coordinate after activation. The initial `+$0200`
velocity is integrated and the generic object-floor routine projects the object
onto terrain each patrol update. In the two fixtures above, the stored Y settled
from 254 to 238 and from 606 to 590 respectively. This is original integer/fixed-
point behavior, not a request to pre-adjust the placement by 16 pixels.

Task 07 closes the anchor ambiguity: `$7666` adds 18 only to the lookup probe.
The stored/rendered object anchor remains `+$14/+$15`; `$70E7` applies its
profile correction back to that unshifted field. All six THZ1 placements settle
on their first active patrol update to Y `590, 846, 302, 878, 270, 238` in
placement order. See [the visual/anchor closure](thz1-visual-anchor-closure.md)
for the full probe, surface, visible-piece and combined contact table.

## State machine and animation

The type entry at ROM `$065FA` is CPU pointer `$B1B6`. Because `$21 < $26`, the
table and scripts run in bank `$0C`; table ROM is `$331B6`. The first script
pointer `$B1C4` makes this a seven-entry table.

| State | Script | Frames / callback | Entry and transitions | THZ1 reachability |
|---:|---:|---|---|---|
| 0 | `$B1C4` | frame 0, `$B210` | placement starts here; initialization requests 3 | yes, initial |
| 1 | `$B1CA` | frame 1, `$B2F0` | requested when patrol loses floor contact | yes |
| 2 | `$B1D6` | no ordinary record; `FF 00` only | no type `$21` code requests it | not found |
| 3 | `$B1D8` | frames 1/2, `$B268` | bit 4 set; negative-X patrol; bound toggles to 4 | yes |
| 4 | `$B1E6` | frames 1/2, `$B264` | bit 4 clear; positive-X patrol; bound toggles to 3 | yes |
| 5 | `$B1F4` | frames 1/2, `$B264` | alternate bit-4 initialization; toggles to 6 | no THZ1 record |
| 6 | `$B202` | frames 1/2, `$B268` | alternate variant; toggles to 5 | no THZ1 record |

State 1 begins with `FF 02 00 00 00 02`, setting X velocity to zero and Y
velocity to `+$0200`. Callback `$B2F0` integrates position and adds `$0040` to
Y velocity each update. Its `$E0`-duration record restarts afterward, which
reapplies the initial velocity if the object remains active that long. It does
not call terrain or player-contact helpers.

States 3/6 use `FF 0C 04 10` to OR bit 4 into `+$04`. States 4/5 use
`FF 0B 04 EF` and callback `$B264` to clear it. Each uses duration `$08` records
for mapping frames 1 and 2. No type `$21` script requests a sound or another
state; all state transitions are callback writes to `+$02`.

The extended animation parser now decodes `FF 02`, `FF 0B`, and `FF 0C` from
their handlers at fixed CPU `$66DB`, `$6857`, and `$6873`. No unknown command
remains in the seven type `$21` scripts.

## Mapping, collision dimensions, and orientation

The mapping pointer-table entry is ROM `$3C042`; it selects mapping CPU `$911B`
in bank `$0F` (ROM `$3D11B`). Mapping indices resolve as follows:

| Index | Frame CPU | Frame ROM | Role |
|---:|---:|---:|---|
| 0 | `$A0E4` | `$3E0E4` | shared empty frame used during initialization |
| 1 | `$9121` | `$3D121` | first object-specific patrol frame |
| 2 | `$912C` | `$3D12C` | second object-specific patrol frame |

Both object-specific records contain six pieces and supply collision fields
`+$2C = $0B` and `+$2D = $1A` through the generic mapping loader at
`$657F..$65A4`. The contact helper therefore uses an object horizontal extent
of 11 and vertical extent of 26, combined with the player's dimensions.

The THZ1 graphics stream is bank `$09`, CPU source `$9AB0`, ROM `$25AB0`, and
decompresses to 18 tiles. Base `$86` uses the ordinary result; `$98` uses the
existing remap path. The renderer at fixed CPU `$22B6` proves their selection:

- with object `+$04` bit 4 clear, tile offsets are added to `+$08` (`$86`);
- with bit 4 set, they are added to `+$09` (`$98`);
- the same bit selects the alternate coordinate stream by adding `$0D08` at
  `$22EB..$22F5`, and it negates the frame X origin at `$22C5..$22D1`.

For frame 1, ordinary X coordinates begin `-12,-4,+4`; the alternate stream
begins `+4,-4,-12`. Together with the remapped art bytes this is a proven
horizontal presentation change, not merely two unrelated palettes or art
loads. THZ1 state 3 (moving left) selects `$98`; state 4 (moving right) selects
`$86`. States 6 and 5 make the same respective selections.

## Sonic interaction

Patrol states call fixed overlap helper `$6328` through vector `$033B`. Contact
is ignored if that helper leaves object `+$21` zero. There is no local hit
cooldown.

After overlap, `$B2B7..$B2C8` compares `object_y - 4` with player integer Y:

- If `object_y - 4 >= player_y`, it writes `$FF` to `$D448`, loads HL=`$F940`,
  and jumps through `$035F` to the shared vertical-spring setter `$480C`.
  With a non-upward player fixture this requests player state `$0B`, writes
  Y velocity `$F940` (-6.75 in signed 8.8), sets airborne, clears rolling and
  floor contact, and requests sound `$A6`. Type `$21` survives. This branch is
  evaluated before the attack tests, so top contact bounces rather than defeats
  the object.
- Otherwise, player movement flag `$D503` bit 1 or power-up `$D532 == 6`
  jumps through `$033E` to generic conversion `$5F54`. That routine adds the
  three-byte score-table value at `$27EB` (`10 00 00` in ROM), replaces the
  same object slot with type `$0F`, clears current/requested state, flags,
  animation cursor, parameter, and placement token. Type `$21` itself does not
  allocate a separate object.
- If neither attack condition holds, it writes `$FF` to damage-request byte
  `$D3B0`. Downstream player damage, ring loss, and invulnerability timing are
  shared systems and are not redefined by type `$21`.

Controlled original-routine fixtures verified all three paths: top bounce,
ordinary damaging side contact, and conversion under both rolling/attack and
power-up `$06`.

## Activation, despawn, and persistence

The bank-$1C placement scan uses the biased record coordinates to accept a
window equivalent to `camera - 128 <= world_position < camera + 384` on each
axis, then applies a bank-$1C map-cell eligibility test at CPU `$8146`. The
meaning of every map-cell value is not assigned here. Creation sets `+$04` bit
6; patrol callbacks sleep while it remains set. The post-update routine at
fixed `$61E1` clears bit 6, repeats the range/map test, and either keeps the
object active or marks it off-range.

THZ1 flags are zero, so object `+$04` bit 1 is clear. When a placement-backed
object (`+$3E != 0`) leaves the accepted region, `$625B` changes its type to
`$FE` and clears current state. On the following scheduler pass, the `$FE`
handler at `$5EF8` clears the corresponding `$D400` occupancy byte and zeroes
the `$40`-byte slot. When the camera returns, the placement record is eligible
again and creation restores the original X/Y, saved origin, parameter, flags,
and art bases. Normal off-screen despawn therefore resets the patrol rather than
preserving its phase.

Defeat is different. `$5F54` clears `+$3E` while converting the occupied slot
to type `$0F`, but does not clear the record's `$D400` occupancy byte. The
placement scan skips nonzero occupancy bytes, so a defeated type `$21` does not
respawn merely because the camera leaves and returns during the same loaded act.

State 1 retains its placement token. A falling instance will eventually be
removed by the same visibility path and can be recreated from its original
record if the camera returns.

## Semantic identity

- **Verified identity:** unresolved. The ROM has no semantic name for type
  `$21`, and no official name source was established in this work.
- **Likely identity:** **Boing-o-Bot**, also reported as **Bane Motora**. The
  reconstructed 24×32 sprite has a spring assembly over a wheeled shell; the
  code patrols a bounded ground span, springs top contact, and requires a side
  rolling attack or power-up `$06` for defeat. Those independent graphics and
  behavior findings match the commonly documented enemy rather than relying on
  visual resemblance alone.
- **Unresolved identity:** whether one of those names is the authoritative name
  for this exact Master System revision.

The repository may use the likely name in explanatory prose, but machine data
retains object type `$21` as the primary identifier.

## Verification and artifacts

Evidence levels used here:

- **Byte verified:** generated regions in `asm/recovered/`, including
  `object_21_scripts.asm`, `object_21_handlers.asm`, the animation command
  engine, placement creation, scheduler, orientation renderer, visibility,
  cleanup, and defeated-enemy conversion. `tools/build_verify.py` reconstructs
  the matching ROM.
- **Source traced:** field initialization, state transitions, movement order,
  orientation/base selection, overlap branches, occupancy and despawn rules.
- **Controlled trace:** original `$B210`, `$B264/$B268`, `$B2AF`, shared floor,
  spring, collision, destruction and score routines executed through
  `tools/oracle.py` with explicit RAM/map fixtures.
- **Differentially tested:** parameter-bound arithmetic has a small independent
  translation test; the ROM verification suite asserts original-routine results.
- **Visually reconstructed:** structural grayscale frames from the existing
  graphics tool; no CRAM-accurate identity claim.
- **Gameplay observed:** not claimed.

Run:

```text
python tools/thz1_object_21.py path/to/SonicChaos.sms
python tools/thz1_animation_reach.py path/to/SonicChaos.sms
python tests/verify_rom.py path/to/SonicChaos.sms --output reports
python tools/build_verify.py path/to/SonicChaos.sms --output build/verify
```

Committed decoded metadata is in `data/rom-cache/thz1/object-21.json`. Generated
ROM-derived reports and previews stay under ignored `build/`.

## Remaining questions

- The global meaning of `$D12F` bit 0 is not named here; type `$21` uses it only
  to bypass bound reversal while still proceeding to contact handling.
- State 2 is not requested by any recovered type `$21` path. Its `FF 00`-only
  script has no ordinary record or callback, and its intended purpose is unknown.
- States 5/6 are proven for an incoming placement flag bit 4, but no THZ1 record
  uses that flag. Other acts were not audited for type `$21` placements here.
- The complete lifetime and presentation of replacement type `$0F` is outside
  this object's recovered region.
- Exact scheduler/VDP timing and an emulator-recorded THZ1 encounter remain
  unobserved; the controlled traces do not claim full-hardware timing.

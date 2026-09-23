# Turquoise Hill object type `$27`

This document applies only to the 524,288-byte Master System ROM with SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
CPU addresses in `$8000..$BFFF` name the stated slot-2 bank; `ROM` always means a
file offset. The principal object code is bank `$1E`, CPU `$8947..$8A44`, ROM
`$78947..$78A44`.

## Result

Type `$27` is retained as a numeric identity. No semantic name is established
by the ROM or source evidence used here.

The THZ1 placement creates it with orientation bit 4 set. It initializes at
signed 8.8 X velocity `$FD80` (-2.5 pixels/update), moves left, and enters state
2 only when the absolute difference between its post-movement integer X and
Sonic's integer X is strictly less than 64 pixels. State 2 stops horizontal
motion and performs a scripted vertical oscillation. Its independent `$80`
counter underflows on callback update 129, at which point state 3 is requested
and both velocities are reset. State 3 resumes leftward travel on the following
update and sets type `$FE` at an absolute Sonic-X separation of 384 pixels or
greater.

Ordinary overlap records generic contact but does not request damage. A rolling
or attack contact (`$D503` bit 1) or power-up `$06` applies the generic defeated-
enemy conversion: add score bytes `10 00 00`, replace the slot with type `$0F`,
and detach it from the placement.

These findings are source-traced and controlled original-routine results, not
a full-emulator gameplay observation.

## THZ1 placements and creation

The three decoded records in `data/rom-cache/thz1/object-records.json` are:

| Record ROM | World X | World Y | Flags | Parameter | `aux0` | `aux1` |
|---:|---:|---:|---:|---:|---:|---:|
| `$7067D` | 3504 | 224 | `$10` | `$00` | `$AA` | `$AA` |
| `$70686` | 2288 | 768 | `$10` | `$00` | `$AA` | `$AA` |
| `$7068F` | 2240 | 112 | `$10` | `$00` | `$AA` | `$AA` |

The placement scan begins at bank `$1C`, CPU `$8000` (ROM `$70000`). It walks
the act's nine-byte records alongside occupancy bytes at `$D400`. A zero
occupancy byte and the scan's camera/map eligibility checks allow creation. The
common creator is bank `$1C:$80EB` (ROM `$700EB`). It calls the badnik-slot
allocator through fixed vector `$0329` (`$5EE1`), which searches 11 slots from
`$D700` in `$40`-byte steps.

A controlled call using the first record and occupancy byte `$D418` produced:

| Object field | Created value/source | Evidence |
|---:|---|---|
| `+$00` | type `$27` | `$80F2..$80F6` |
| `+$11/+$12` | current X = 3504 | `$80F7..$8105` |
| `+$3A/+$3B` | saved X = 3504 | `$80F7..$8105` |
| `+$14/+$15` | current Y = 224 | `$8108..$8116` |
| `+$3C/+$3D` | saved Y = 224 | `$8108..$8116` |
| `+$04` | flags `$10` OR `$40` = `$50` | `$8119..$811D` |
| `+$3F` | parameter `$00` | `$8120..$8122` |
| `+$08/+$09` | art bases `$AA/$AA` | `$8125..$812C` |
| `+$3E` | one-based occupancy token 25 | `$812F..$8138` |

The corresponding `$D418` occupancy byte becomes `$27`.

## Initialization and changed fields

State 0 callback `$898E` (ROM `$7898E`) always first writes requested state
`+$02 = 1`, then reads parameter `+$3F`.

For the THZ1 parameter `$00` path it changes only:

- `+$16/+$17 = $FD80`, signed 8.8 X velocity -2.5;
- `+$18/+$19 = $0000`, signed 8.8 Y velocity zero.

The record-created `+$04 = $50`, parameter, positions, origins, art bases, and
occupancy token are not changed by this callback.

The nonzero-parameter branch exists but is not reachable from any THZ1 `$27`
record. It immediately requests state 2, zeroes X velocity, writes `+$1F = 1`,
and initializes `+$1E = $80`. It does **not** write Y velocity. The meaning of
the nonzero placement parameter and field `+$1F` is **UNRESOLVED**.

## State table and every script command

The object-type pointer entry is ROM `$06606`. Since `$27 >= $26`, the generic
scheduler selects bank `$1E`. The four-entry state table is CPU `$8947`, ROM
`$78947`; its pointers are `$894F/$8955/$895F/$8984`.

| State | Script | Ordinary records | Entry / transition |
|---:|---:|---|---|
| 0 | `$894F` / ROM `$7894F` | duration `$E0`, frame 0, callback `$898E` | placement entry; callback requests 1 |
| 1 | `$8955` / ROM `$78955` | duration 2, frames 1/2, callback `$89AC` | left travel; proximity requests 2 |
| 2 | `$895F` / ROM `$7895F` | duration 2, frames 1/2; callbacks `$89DF/$89F3` | vertical oscillation; counter underflow requests 3 |
| 3 | `$8984` / ROM `$78984` | duration 2, frames 1/2, callback `$8A29` | left travel; separation removes |

All control commands are decoded; no state has an unsupported command:

| CPU / ROM | Bytes | Exact action |
|---:|---:|---|
| `$8953` / `$78953` | `FF 00` | restart state-0 script at `$894F` |
| `$895D` / `$7895D` | `FF 00` | restart state-1 script at `$8955` |
| `$895F` / `$7895F` | `FF 0E 08` | set animation loop counter `+$33` to 8 |
| `$896A` / `$7896A` | `FF 0F 62 89` | decrement `+$33`; jump to `$8962` while nonzero |
| `$896E` / `$7896E` | `FF 0E 10` | set `+$33` to 16 |
| `$8979` / `$78979` | `FF 0F 71 89` | decrement `+$33`; jump to `$8971` while nonzero |
| `$897D` / `$7897D` | `FF 0E 10` | set `+$33` to 16 |
| `$8980` / `$78980` | `FF 07 62 89` | jump to `$8962` |
| `$898C` / `$7898C` | `FF 00` | restart state-3 script at `$8984` |

The generic animation engine is fixed CPU `$64FA..$65AE`. It installs each
ordinary record's duration at `+$07`, frame at `+$06`, and callback at
`+$0C/+$0D`. The scheduler calls that stored callback every object update,
including duration-hold updates; duration 2 therefore means two callback
updates per record, not one.

## Exact 64-pixel proximity calculation

State-1 callback `$89AC` runs in this order:

1. Return immediately if `+$04` bit 6 is set.
2. Call overlap helper `$6328` through vector `$033B`.
3. If overlap exists, tail-jump to attack check `$5F3D` through `$0323` and do
   no movement or proximity test on that update.
4. Otherwise integrate signed 8.8 X/Y position through `$0338` (`$60FB`).
5. Load `BC=$0040` and call horizontal helper `$61A5` through `$0383`.

`$61A5` reads object integer X from `IX+$11/+$12` and Sonic integer X from
`$D511`. `$61BB` subtracts the two 16-bit words, uses bit 7 of the high byte to
detect a negative two's-complement delta and negate it, then performs an
unsigned subtraction of threshold `$0040`. It returns `$FF` only on borrow.
For the THZ1 coordinate range this is exactly:

```text
abs(object_integer_x_after_movement - sonic_integer_x) < 64
```

The comparison ignores both objects' fractional X bytes. Controlled fixtures
with the object at post-movement X `997.5` prove that separations 65 and 64 do
not trigger, while 63 does. At 63, `$89C7..$89DA` sets `+$04` bit 1, requests
state 2, zeroes X velocity, writes `+$1F = 1`, and initializes `+$1E = $80`.

## Horizontal movement and orientation

Initialization stores `$FD80`, so generic integration moves left by exactly
2.5 pixels per active callback. State 1 performs movement before proximity.
State 3 performs its 384-pixel test before overlap and movement; a surviving
state-3 callback then moves left by 2.5 pixels.

All three THZ1 records set placement flag bit 4. Creation preserves it in
object `+$04` while also setting bit 6, producing `$50`. No `$27` state script
or handler clears bit 4; proximity only sets bit 1, producing `$12` after the
visibility bit has cleared.

The fixed renderer at `$22B6..$2334` proves that `+$04` bit 4:

- selects the horizontally mirrored coordinate stream;
- negates the frame X origin;
- selects art base `+$09` rather than `+$08`.

For THZ1 both bases are `$AA`, so the base value is unchanged, but coordinate
mirroring still applies. Bit 4 also makes animation command `FF 02` negate X
velocity globally, but no `$27` script contains `FF 02`; `$27` writes its own
negative X velocity directly.

## Vertical oscillation and transition back to travel

State 2 uses two callbacks:

- `$89DF` (ROM `$789DF`) adds `$0003` to signed 8.8 Y velocity;
- `$89F3` (ROM `$789F3`) subtracts `$0003` from signed 8.8 Y velocity.

Both join `$8A06`, which calls overlap helper `$6328`, applies the same generic
attack check on overlap, integrates position through `$60FB`, then decrements
object counter `+$1E`. The transition occurs on subtraction underflow: `$00 -
1 = $FF` sets carry, so `$8A22` requests state 3 and jumps to `$8999`. That
shared initialization tail restores X velocity `$FD80` and zeros Y velocity.
Thus values `$80` through `$00` produce 129 callback updates.

With no contact, the script and handler sequence is exact:

| End of update | Callback phase | Y velocity (8.8 raw) | Y displacement (8.8 raw) |
|---:|---|---:|---:|
| 32 | 32 × `$89DF` | +96 | +1584 (6.1875 px) |
| 96 | then 64 × `$89F3` | -96 | +1488 (5.8125 px) |
| 128 | then 32 × `$89DF` | 0 | 0 |
| 129 | 33rd `$89DF`; underflow | +3 before reset, 0 after | +3 (0.01171875 px) |

The state-2 controlled run therefore contains 65 add callbacks and 64 subtract
callbacks. Current state remains 2 while requested state becomes 3 on update
129. On update 130 the animation engine installs state 3, callback `$8A29`
runs, and X moves left by 2.5 pixels with Y velocity zero.

Ordinary overlap tail-returns before integration and before decrementing
`+$1E`. Consequently 129 is the exact no-contact callback count, but sustained
ordinary contact can delay the transition in scheduler updates.

## Exact 384-pixel removal and respawn

State-3 callback `$8A29` loads `BC=$0180` and calls the same `$61A5/$61BB`
integer-X helper before any contact or movement. Its branch is inverted:

```text
abs(object_integer_x - sonic_integer_x) >= 384  -> type $FE
abs(object_integer_x - sonic_integer_x) < 384   -> contact, then movement
```

Controlled comparisons prove that separation 383 survives and moves, while
384 and 385 set `+$00 = $FE` without moving. The placement token remains in
`+$3E`; this is object-specific deletion, not the generic visibility decision.

On the following scheduler pass, lifecycle dispatch selects fixed `$5EF8`.
That routine uses the one-based token to clear the corresponding `$D400`
occupancy byte, then zeros the `$40`-byte slot. The placement scan can therefore
create type `$27` again when its window becomes eligible. A controlled `$FE`
cleanup cleared first-record occupancy `$D418` and the whole slot.

## Sonic interaction

Frames 1 and 2 are selected from mapping table CPU `$91F5`, ROM `$3D1F5` in
bank `$0F`. Their records are CPU `$91FB/$9206`, ROM `$3D1FB/$3D206`; each
supplies collision extents `+$2C = 9` and `+$2D = 14`. Frame 0 uses the shared
empty record `$A0E4`. The reachable indices are `$00/$01/$02`, with `$01/$02`
object-specific.

Active callbacks call fixed overlap helper `$6328`. When it reports no overlap,
normal movement continues. When it reports overlap, each `$27` callback tail-
jumps through `$0323` to `$5F3D`:

- ordinary contact leaves type `$27`, writes no damage request to `$D3B0`, and
  returns before movement, proximity testing, or counter decrement;
- player flag `$D503` bit 1 (rolling/attack) converts the slot to type `$0F`;
- power-up byte `$D532 == $06` performs the same conversion.

The conversion at `$5F54..$5F76` adds the type's score-table value through
`$5F77`/`$262F`; the controlled result is `10 00 00`. It clears current and
requested state, flags, animation duration/cursor, placement token `+$3E`, and
parameter `+$3F`. Because it detaches the token without clearing the placement's
nonzero `$D400` byte, a defeated type `$27` does not respawn merely because the
camera leaves and returns during the same loaded act.

The overlap helper also updates generic contact flags/bookkeeping. Whether any
downstream system gives ordinary `$27` contact an additional gameplay meaning
beyond the verified no-damage, no-movement callback result is **UNRESOLVED**.

## Activation and generic visibility/lifetime behavior

The bank-$1C placement scan accepts a window equivalent to `camera - 128 <=
world_position < camera + 384` on each axis, then applies its map-cell
eligibility test at CPU `$8146`. Creation sets `+$04` bit 6. State-1 callback
`$89AC` sleeps while that bit remains set. The post-update lifetime routine at
fixed `$61E1` clears bit 6, repeats the range/map test, and either keeps the
object active or marks it off-range.

On the first scheduler update, state 0 installs callback `$898E`, which requests
state 1; current state is still zero, so the scheduler does not yet call the
lifetime routine. On the next update the animation engine installs state 1,
`$89AC` returns because creation bit 6 remains set, and the post-update lifetime
check clears/re-evaluates that bit. Normal state-1 movement begins on the next
eligible update.

Before proximity, bit 1 is clear. Off-range generic handling sets type `$FE`
for this placement-backed object; `$FE` cleanup releases occupancy, so returning
to the placement can recreate it from the original record.

The 64-pixel trigger sets bit 1. At fixed `$6250`, generic off-range handling
returns when bit 1 is set instead of deleting the object. A controlled off-range
call left post-trigger type `$27` and state 3 alive with flags `$52`, whereas the
same pre-trigger object became `$FE`. The state-3 384-pixel test is therefore
the post-trigger lifetime mechanism. It eventually sets `$FE`, whose cleanup
releases occupancy and permits respawn.

The semantic meaning of every bank-$1C map-cell eligibility value is not needed
for this chain and remains **UNRESOLVED**.

## Verification and artifacts

Evidence levels used here:

- **Byte verified:** existing `object_27_scripts.asm` and
  `object_27_handlers.asm`, plus the generic scheduler, animation engine,
  renderer, placement creator, visibility, cleanup, and defeated-enemy regions.
- **Source traced:** every state record/command, all changed fields, strict
  comparisons, orientation, overlap branches, occupancy, and respawn paths.
- **Controlled trace:** original placement creator, callbacks, scheduler,
  overlap/destruction, visibility, and cleanup routines executed through
  `tools/oracle.py` with explicit RAM fixtures.
- **Differentially tested:** an independent arithmetic translation checks the
  strict boundaries and complete no-contact oscillation trajectory.
- **Gameplay observed:** not claimed.

Run:

```text
python tools/thz1_object_27.py path/to/SonicChaos.sms
python -m unittest tests.test_thz1_object_27 -v
python tests/verify_rom.py path/to/SonicChaos.sms --output reports
python tools/build_verify.py path/to/SonicChaos.sms --output build/verify
```

Committed decoded metadata is in `data/rom-cache/thz1/object-27.json`.
Generated detailed reports stay under ignored `build/`.

## Remaining unresolved questions

- The semantic identity and canonical name of type `$27` are **UNRESOLVED**.
- The intended meaning of a nonzero placement parameter and object field
  `+$1F` is **UNRESOLVED**; all three THZ1 records use parameter `$00`.
- The downstream gameplay significance, if any, of generic contact bookkeeping
  on ordinary overlap is **UNRESOLVED**. The tested callback itself issues no
  damage request and performs no movement on that update.
- The semantic names of all placement scan map-cell eligibility values are
  **UNRESOLVED**.
- The complete lifetime/presentation of replacement type `$0F` is outside this
  object study.
- Exact hardware-frame timing and an emulator-recorded THZ1 encounter remain
  unobserved; controlled original-routine updates are not a full SMS replay.

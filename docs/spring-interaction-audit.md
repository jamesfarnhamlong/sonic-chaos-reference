# Spring interaction audit (mapped type `$26` and terrain springs)

Research only; the POC was not touched. Evidence labels: **BYTE-VERIFIED** (disassembled routine bytes), **CONTROLLED**
(original Z80 routine run on `tools/oracle.py` with explicit RAM), **EMULATED** (whole original game in
`tools/sms_frame_harness.py`), **DECODED** (parsed ROM data), **UNRESOLVED**.

Machine-readable result: `data/rom-cache/spring-interaction.json`. Regenerate/verify:

```sh
python tools/spring_interaction.py path/to/SonicChaos.sms            # writes the cache (about two minutes)
python tools/spring_interaction.py path/to/SonicChaos.sms --check    # byte-compares the cache with a fresh build
python -m unittest tests.test_spring_interaction                     # ROM-backed tests need SONIC_CHAOS_ROM
```

Conventions: speeds are signed 8.8 fixed point (`$F8A0` = -7.375 px/update); `+n` = player/object field offset; the player
is the slot at `$D500`, so `$D501` current state, `$D502` requested state, `$D503` movement flags (bit 0 airborne,
bit 1 rolling/attack posture), `$D511/$D514` X/Y anchor, `$D516/$D518` X/Y speed, `$D522` background contact flags
(bit 1 = floor), `$D519` high byte of Y speed. `$D36B` is the sampled block id and `$D36C` the **previous update's** terrain flags.
Object coordinates in this document are runtime/world coordinates (`stored - 256`, creator `$80EB`).

## 1. Mechanisms found

There are **six spring mechanisms (A-F)** that launch the player through the setters of `$480C..$4891` or the ceiling pass, plus two bounces (G)
that reuse `$480C` and two terrain "bounce on break" blocks (H) that are not springs.

| # | Mechanism | Data source | ROM routine | Orientation | Request | Launch speed | `$D448` | `vx` | `vy` | Position change |
|---|---|---|---|---|---|---|---|---|---|---|
| A | mapped type `$26`, fixed (parameter bit 7 clear) | placement record byte 6 (`+$3F`), byte 8 (`+$09`) | state 7 `$82AF` (bank `$1E`, ROM `$782AF`) | upright | `$0B` | vy `$F8A0` (-7.375) if parameter 0, else `$FB00` (-5.0) | `$FF` / `$00` | untouched | set | none |
| B | mapped type `$26`, span (parameter bit 7 set) | same | state 8 `$83BF`, state 9 `$8401` | upright | `$0B` | as A, chosen by `+$3F` (aux1-derived) | `$FF` / `$00` | untouched | set | **object** X := player X & `$FFF0`; player untouched |
| C | terrain upright: type 9, blocks `$30/$31` | layout cell + collision header | `$6A75` -> `$480C` | upright | `$0B` | vy `$F880` (-7.5) | `$FF` | untouched | set | none |
| D | terrain diagonal: type `$14`, blocks `$36/$37` (right), `$38/$39` (left) | same | `$6A90` -> `$482D` | up and sideways | `$1C` | vx +4.0 (`$0400`) for block < `$38`, -4.0 (`$FC00`) for >= `$38`; vy `$F900` (-7.0) when `$D297` = 0 (THZ), `$FA80` (-5.5) otherwise | `$00` | set | set | none |
| E | terrain horizontal: type 10, blocks `$32/$33` (solid left half), `$34/$35` (solid right half) | same | side cores `$71B2/$7257` tails `$71FC..$720D`, `$72A2..$72B3` -> `$4868` / `$4849` | sideways | `9` (rolling) | vx -6.0 (`$FA00`) from the right probe, +6.0 (`$0600`) from the left probe; speed cap `$D373` := `$0600` | untouched | set | **untouched** | the ordinary side projection only |
| F | terrain ceiling spring: type `$14` blocks `$3A/$3B` (and type `$15`, `$748F`) | same | ceiling pass `$749D` (`$748F`) | downward | `$1B` | vx +4.0, vy +5.5 (`$0580`) down; type `$15`: vy +7.5 (`$0780`) only | untouched | set | set | player pushed down out of the block |
| G | `$21` top stomp, `$50` top bounce (same `$480C`) | object handlers `$B2D2`, `$99D0` | via vector `$035F` | upright | `$0B` | vy `$F940` (-6.75) / `$FC00` (-4.0) | `$FF` / `$00` | untouched | set | none |
| H | breakable blocks type `$16` (`$6AE3`) / `$0D` (`$6B2C`) | layout cell | `$6AE3`, `$6B2C` | upward | unchanged state | vy `$FBC0` (-4.25); needs `$D503` bit 1 (rolling/attack) | untouched | untouched | set | the block becomes `$46` / `$9D` |

Blocks `$3A/$3B`, type `$15` and the breakable blocks `$47/$9B/$9C` are in no spring role in THZ: layout scan (DECODED) finds blocks
`$3A/$3B` in **no** THZ1/THZ2/THZ3 cell. The terrain-handler table at `$6973` is decoded in the cache (`terrain_handler_table`): type 9 -> `$6A75`,
type `$14` -> `$6A90`; type 10 is not dispatched through that table but tested inside the side cores.

Terrain spring cells (DECODED from the layouts; world coordinates of the 32x32 cell):

| Act | Upright (`$30/$31`) | Diagonal right (`$36`) | Diagonal left (`$38`) | Horizontal |
|---|---|---|---|---|
| THZ1 | (928,640) `$30`, (2112,832) `$31` | (2464,256), (2976,352), (1536,416), (1056,768) | (1664,512), (1152,704) | (3200,832) `$33` left half |
| THZ2 | (2368,672), (3040,704) `$30` | (1184,224), (2656,512) | - | (3264,256), (1856,512) `$34`; (3040,864) `$35` (right halves) |
| THZ3 | (544,352), (1152,352) `$31` | (1344,160) | - | - |

Type `$26` placements and their derived behavior:

| Act | Position | Parameter / aux1 | Form | Launch | `$D448` | Notes |
|---|---|---|---|---|---|---|
| THZ1 | (688,864), (3568,768) | `$00` / `$72` | fixed strong | -7.375 | `$FF` | |
| THZ1 | (1912,864) | `$01` / `$72` | fixed weak | -5.0 | `$00` | |
| THZ1 | (1296,608) | `$8A` / `$72` | span 160 px, weak | -5.0 | `$00` | trigger X in [1296,1456) |
| THZ2 | (864/960/1056,896), (2064,544), (3200/3296/3392/3568,896) | `$00` / `$72` | fixed strong | -7.375 | `$FF` | |
| THZ2 | (3472,288) | `$01` / `$72` | fixed weak | -5.0 | `$00` | |
| THZ2 | (1504,896) | `$88` / `$72` | span 128 px, weak | -5.0 | `$00` | trigger X in [1504,1632) |
| THZ3 | (656/720/784,384), (1456,384) | `$00` / `$72` | fixed strong | -7.375 | `$FF` | |

All 33 canonical type-`$26` and terrain upright/diagonal spring cells launch in the emulated original with exactly these values
(`emulated_placements`; EMULATED), and all four horizontal cells launch when run into from their open side (`emulated_horizontal`).

## 2. Exact activation geometry

### 2.1 Type `$26` fixed contact (state 7, `$82AF`) - CONTROLLED, 1,630 + 154 cases, model mismatches 0

Coordinates: the **player anchor** `($D511,$D514)` against the object's **current** `+$11` / `+$14`. No extents, mask, sprite edge
or `$6328` overlap is involved. Rest Y is the placement Y + 12 (initializer `$825A`).

* Horizontal: `abs(playerX - objectX) < 12`, strict: `dx` -11..+11 pass; ±12 and ±13 fail (`$0383` -> `$61A5` compares `|dx| < BC`, BC = 12).
* Vertical: `0 <= (objectY - 28) - playerY < 6`, i.e. **`playerY` in `[objectY-33, objectY-28]`**, six rows, both ends inclusive
  (unsigned 16-bit compares at `$82DD`/`$82E4`). In placement terms with `restY = placementY + 12`: `playerY` in `[placementY-21, placementY-16]`.
  Edges: -35 and -34 fail, -33 passes, -28 passes, -27 and -26 fail (relative to objectY).
* A player standing on a floor whose surface is at the placement Y has anchor Y = surface - 18 = placementY - 18, inside the window
  (verified on all canonical placements in the emulator).

### 2.2 Type `$26` span trigger (state 8, `$83BF`) - CONTROLLED, 35,415 cases

* Horizontal: `x0 <= playerX < x0 + span`, `x0` = placement X (restored from `+$3A/+$3B` every update), `span = (parameter & $7F) * 16`.
  There is **no** `|dx| < 12` rule here.
* Vertical: `abs(objectY - playerY) < $30` strict (`$0386` -> `$61B1` with BC = `$30`): `playerY - objectY` in -47..+47, objectY = placement Y + 12.
  This is a different, much taller window than the fixed contact.
* State 9 (the next update, `$8401`) then moves the object X to `playerX & $FFF0`, applies the launch and enters the extension state. It does
  **not** re-test any gate: the launch values and `$D448` are written even if `$480C` then rejects a negative Y speed.

### 2.3 Terrain upright / diagonal (types 9 and `$14`) - CONTROLLED, 3 x 46,656 grid cases + random cells of all acts, model mismatches 0

The activation is a **cell-membership test of the foot probe**, not a sprite or mask overlap:

* Probe point: `(playerX, playerY + 18)` (`$7666` adds 18 to Y; `$691A` passes dy = 0, except dy = -14 while the *current* state `$D501` is `$21` and +8 while it is `$12`).
  The cell is the 32x32 layout cell containing that point: cell-relative x `0..31` and probe-y `0..31`.
* The handler is chosen from the terrain flags of the *new* cell (`flags & $1F`); but whether the **floor flag** is set when the handler runs depends on
  the *previous update's* surface `$D36C`, because the projection `$6F61` runs first and uses the old flags (`docs/collision.md`):

| Previous-update surface | Floor flag at dispatch | Region that triggers (upright cell; vy high byte `v`) |
|---|---|---|
| none (flags without bit 7/6) | unchanged from the previous update | whole cell if the flag was already set; nothing if clear |
| solid (bit 7) | unchanged **or** set by landing on the new cell's profile (profile height + probe Y&31 >= 32) | flag set: whole cell. Flag clear: probe Y rows 16..31 (spring top is 16 px high) |
| one-way (bit 6 only, includes spring-on-spring `$49/$54`) | **cleared**, then set only inside `[surface, surface + v + 8]` | probe Y rows `16 .. 24+v` (v = high byte of Y speed) regardless of the old flag |
| solid and one-way (`$C1`) | solid rule | as solid |

  Typical cases: running onto a spring from ordinary ground (previous surface solid, floor flag set) triggers as soon as the probe X enters the cell, anywhere in
  the cell vertically; landing from the air triggers when the foot sinks 0..8+v pixels into the 16-pixel top; spring-to-spring (one-way to one-way) needs that
  same landing window. For the diagonal blocks the 16-pixel top exists only on the spring half (`$36/$37`: cell x 0..15, `$38/$39`: x 16..31), so the landing
  and the solid/one-way cases are restricted to that half; the "flag already set, previous surface solid/none" case still fires over the whole cell.
* Probe coordinates and previous-surface flags are the only geometry inputs; the diagonal blocks' horizontal profile (the visual slope) is not used.

### 2.4 Terrain horizontal (type 10) - CONTROLLED, 40,967 cases, mismatches 0

Activation is the ordinary side projection of a solid (bit 7) cell: the **side probe point** `(X + 9, Y + 6)` (right probe, `$716B`) or `(X - 9, Y + 6)` (left probe,
`$7210`) must be inside the block's solid horizontal profile and the projection must be non-zero. In block terms:

| Blocks | Solid sub-rectangle (cell-relative) |
|---|---|
| `$32/$33` | columns 0..15, rows 8..27 |
| `$34/$35` | columns 16..31, rows 8..27 (horizontal-profile bit 6 flips the side) |

(THZ1 block `$33` at (3200,832): right probe launches for player X 3191..3206, left probe for 3209..3224, player Y 834..853 - i.e. 20 rows, inclusive.)
After the projection the launch is applied from the projected position.

### 2.5 Ceiling spring blocks - CONTROLLED, 6,406 cases

Probe `(X, Y - 6)` in a `$3A/$3B` cell, probe rows 0..16, all columns; needs Y speed negative, floor flag clear. Not present in THZ.

> **Correction (`docs/player-spring-airborne-state-closure.md` section 8, C1):** the Y-speed / floor-flag gate stated above is the gate of the ceiling pass `$73C9` only. `$749D` is also reached by the unconditional tail of the terrain-ring probe `$753E` (`$7569 JP $749D`), which has no such gate: a `$3A/$3B` block also launches a player who is falling onto it (AQZ3, state `$0E`, vy +400).

## 3. Activation gates (all swept)

| Gate | Type `$26` (state 7 / 8) | Terrain upright `$6A75` / diagonal `$6A90` | Terrain horizontal | Ceiling `$749D` |
|---|---|---|---|---|
| must be on the floor | **yes**: `$D522` bit 1 | **yes**: flag at dispatch (section 2.3); airborne Sonic can still trigger on the update he lands | **no** | needs the flag **clear** |
| Y speed | high byte negative rejects; **zero passes**; low byte irrelevant; so an already-rising player cannot trigger | same sign test, twice (handler `$6A80`, setter `$480C`); zero passes | **none** | must be negative |
| current state `$D501` | not read | `$11` rejects; every other state (including `$0B`, `$1C`) passes | `$11` rejects | none |
| requested state `$D502` | `$21` rejects (only that value of 64) | not read | not read | none |
| object/inactivity | `+$04` bit 6 set (inactive/off the awake band) rejects | - | - | - |
| other flags | `$D503` irrelevant (all 6 variants pass) | `$D503` irrelevant | `$D503` irrelevant | - |
| re-trigger protection | the object is in extension/hold/retract states 1..6 for **42 updates (strong) / 20 updates (weak)** and evaluates nothing; on top of the Y-speed sign (a launch makes vy negative) | the Y-speed sign (the launch makes vy negative until the apex) | none (but the launch moves Sonic out of the wall) | Y-speed sign |
| multi-frame contact | a hit is a single-update event: the launch changes the object state at once | same | same | same |

Special behavior of the diagonal spring: **`vx`, the facing bit (`+$04` bit 4, set for left launches) and `$D448 = 0` and sound `$A6` are written before
the Y-speed gate of `$482D`**. A diagonal spring touched with negative Y speed (and the floor flag set) therefore changes X speed and facing but leaves state and Y
speed alone (CONTROLLED, `terrain_gates`).

Speed gates swept (type `$26` state 7, same shape for terrain): `$0000, $0001, $00FF, $0100, $7FFF` pass; `$8000, $FF00, $FFFF` reject.

## 4. Type `$26` parameter semantics (CONTROLLED: `$825A` initializer plus the contact handlers, 54 cases)

Placement record: byte 6 -> `+$3F` ("parameter"), byte 8 -> `+$09` ("aux1"); every canonical record has aux1 = `$72`.

* **Bit 7 clear (fixed):** `+$3F` is used as is. `0` -> strong (`$F8A0`, `$D448 = $FF`, extension state 1); **any nonzero value** -> weak (`$FB00`, `$D448 = 0`).
  The extension animation state is 3 only when the value is exactly 1, otherwise 1 (animation only; `2..$7F` are not placed). The low seven bits otherwise do nothing.
* **Bit 7 set (concealed span):** span = `(parameter & $7F) * 16` px starting at the placement X (`$8A` -> 160, `$88` -> 128, `$81` -> 16, `$FF` -> 2,032);
  `+$3F` is **overwritten** with 1 (weak) when aux1 is non-zero and 0 (strong) when aux1 is zero; the rest state is 8 (not 7). With the canonical aux1 = `$72`
  every span spring is weak. This reconciles `docs/thz2-thz3-object-deltas.md` ("aux1 != 0 -> weak") and `docs/act1-objects.md` ("$8A = 160-pixel span").
* No parameter selects orientation: type `$26` is always an upright spring. No parameter changes the launch beyond strong/weak.
* After a launch the object plays the extension sequence `+28` px in four updates, holds, and retracts (CONTROLLED + EMULATED: strong 42 updates
  from the launch to the contact state again (4 extension, hold, 4 retract); weak 20); contact is not evaluated meanwhile.

## 5. Launch velocities and state requests (CONTROLLED, `launch_table`)

| Mechanism | `vx` | `vy` | Requested state | `$D503` bits (0 air, 1 roll) | `$D522` floor | Other |
|---|---|---|---|---|---|---|
| `$480C` (A, B, C, G) | untouched | `HL` unconditionally (not additive, not clamped, independent of incoming speed) | `$0B` | bit 0 **set**, bit 1 **clear** | cleared | speed cap `$D373` untouched; rejected if Y speed negative; sound `$A6` set by the caller |
| `$482D` (D) | set by `$6A90` | `HL` | `$1C` | bits 0 and 1 **set** | cleared | rejected if Y speed negative |
| `$4849/$4868` (E) | +6.0 / -6.0 | untouched | `9` | bit 0 **clear**, bit 1 set | cleared | `$D373` := `$0600`; sound `$A6` |
| ceiling (F) | +4.0 | +5.5 / +7.5 | `$1B` | bits 0 and 1 set | cleared | player moved out of the block |

The spring-flight state wrappers: `$0B` is updated by `$393B` (shared movement `$3FEF`, landing -> `$45CE`, apex -> `$463C`), `$1C` by `$3955`. The apex request
`$463C` sets `$0E` (falling), vy +1.0, **bit 0 set, bit 1 cleared**; landing `$45CE` clears bits 0/1/6, requests state 5 and resets the speed cap to `$0400`.
Emulated flights (EMULATED): strong type `$26` launch from y 846 rises 287 px over 79 updates in `$0B`; weak 104 px over 29; terrain upright (-7.5) 296 px over 80;
diagonal `$1C` lasts 38 updates and rises 127 px (apex y 127 from y 254); horizontal state 9 runs at `$0600` and later states restore `$0400` on landing.

## 6. `$D448`

* Address bytes occur exactly seven times in the ROM (BYTE-VERIFIED): one reader (`$3018F`, CPU `$818F` bank `$0C`: `LD A,($D448); RRCA; RET`) and six stores
  (`$06A87` upright `$FF`, `$06AC8` diagonal `$00`, `$332CC` type `$21` stomp `$FF`, `$782F8` type `$26` fixed, `$78420` type `$26` span, `$799CA` type `$50` bounce `$00`).
* The single reader is the `FF 08` condition at the start of the state `$0B` animation script: **bit 0 set -> hold frame `$61`; clear -> frames `$1C..$21` cycle**.
  Strong (`$FF`): terrain upright, type `$26` parameter 0 (or span with aux1 = 0), `$21` stomp. Weak (`$00`): type `$26` nonzero parameter / aux1-derived, `$50` bounce.
  The diagonal writes `$00` but enters `$1C`, whose script has no `$D448` condition.
* It is therefore **presentation/animation-counter only**: not movement, gravity, apex/landing, controls, collision, attack posture (`$D503`), damage, nor terrain-ring parity
  (`docs/player-animation-counter.md` section 10).
* Lifetime: it is not cleared on landing (the strong value was still `$FF` after landing in the emulator) nor on act start (only the boot/reset RAM clears zero it). Because `$480C` is the only
  code that requests `$0B` and every caller writes `$D448` first, a stale value is never observed; **persistence across acts is irrelevant**.
* The horizontal spring, the ceiling spring and the breakable bounces do not touch it.

## 7. Is spring-launched Sonic "attacking"?

**No - except for the diagonal and horizontal springs, and the answer is decided by `$D503` bit 1, not by being airborne.**

* The badnik callbacks test the player's movement flag `$D503` bit 1 (the rolling/attack posture) - and, for `$27/$21/$50`, power-up `$D532 == 6` - never the player state
  number and never the airborne bit (CONTROLLED: `$5F3D` converts exactly when `D503 & 2` or `D532 == 6` for all swept values; the type `$21` tail `$B2B2` resolves a top contact
  (`objectY - 4 >= playerY`) as a **stomp bounce first** whatever the flags, otherwise converts iff bit 1, otherwise writes the damage request `$D3B0 = $FF`).
* Original flag values during real play (EMULATED, per update, `emulated_flights`):

| Situation | State | `$D503` (bits 0/1) | Attacks? |
|---|---|---|---|
| upright spring (type `$26`, terrain upright) | `$0B` then falling `$0E` | `1` (airborne, bit 1 clear) | **no** |
| diagonal terrain spring | `$1C` (38 updates) | `3` (airborne + rolling) | **yes**, until the apex request `$463C` clears bit 1 and requests `$0E` (then no) |
| horizontal terrain spring | `9` | `2` (grounded roll) | yes (ordinary roll) |
| normal jump | `$0A` | `3` | yes |
| jump that lands on the upright spring | `$0A` -> `$0B` | `3` -> `1` | yes before, **no** after: the launch clears the attack posture |
| roll | `9` | `2` | yes |
| `$21` stomp / `$50` bounce | `$0B` | `1` | no |

* Spring-launched Sonic must therefore **not** damage a badnik merely because he is airborne or in the spring state. This is a property of each enemy routine reading `$D503` bit 1,
  not a global flag (type `$27` reads it through `$5F3D`, type `$21` in its own callback, type `$10` at `$A16C`, type `$50` in its contact helper; breakable blocks `$6AE3/$6B2C` also require it).
* State `$1C` plays animation frames `$1C..$21`, the same frame set that the weak (`$D448 = 0`) `$0B` script cycles, while the attack posture differs (bit 1 set in `$1C`, clear in weak `$0B`).
  This is a candidate explanation for "attacks while apparently unrolled" after a **diagonal** spring; I did not trace the parked type `$27` observation end to end and make no change to the `$27` study.

## 8. THZ1 top-of-screen death

Facts established from the original (nothing changed in the POC):

* **The original never kills Sonic for going above the top.** The only fatal screen condition in the shared movement update is `$401A`: death (`$4984`: state `$1F`, vy -5.0, `$D293` bit 2)
  iff the **signed screen Y** `$D51C = playerY - cameraY` (computed by `$3FC8`) is **non-negative and >= `$D0` (208)**. Negative screen Y (above the camera) is never fatal
  (CONTROLLED: 11 sample points, plus 400 random values in the tests). The dying-state fall check at `$3C09` uses `$D8`. The rule is **camera-relative and signed**, it is vertical-only and is not affected by
  horizontal widening.
* **Sonic can travel far above the visible top.** Forcing Y speed -8.0 for 200 updates in THZ1 (EMULATED): the camera stops at its top limit (8), world Y wraps below zero as an unsigned 16-bit value
  (65483 = -53 at update 24 ... 64170 = -1,366 at update 192; minimum -1,420), screen Y reaches -1,374 and Sonic is neither killed nor clamped (state `$0E`, `$D293` bit 2 never set). The top/bottom clamps `$3B25` (called only from state `$11`'s `$3A7C` path) and `$3FA7` (called only from a separate scripted
  movement routine at `$3F00..$3F83`, not identified) are not part of ordinary spring flight.
* **Canonical launches cannot do it in THZ1.** Every canonical THZ1 spring (4 type `$26`, 2 upright, 6 diagonal) launched in the emulator: the highest first-launch apex is **world Y 127**
  (diagonal (2464,256); rise 127 px), minimum screen Y 73-74; no flight dies. Launch speeds are overwritten, not added, so chains cannot climb higher. The camera follow (lead `$78`,
  dead zone `$68..$98`, step <= 7) keeps Sonic on screen. The highest canonical flight in any act is THZ3 diagonal (1344,160): apex y 31, screen Y 22 (still on screen, camera top limit 8).

Classification: **D (the original also kills Sonic) is excluded.** **E (unresolved)** for the observed POC death: no canonical THZ1 launch reaches the top, so a POC death above the top
needs something the canonical routines do not do. Candidates the POC can check from its own logs (no fix proposed): (1) a launch velocity/gravity/gate difference (**B**) such that the apex
is far higher than 127 (from a read-only look at POC `04be903`, its gravity table `24/36/48` matches the ROM values for `$0B/$1B/$1C`); (2) a rigid camera/view clamp at 0 (**C**) combined with a negative `y`; (3) a death test that is
world-space/unsigned instead of signed screen-relative: a read-only look at POC `04be903` shows `SCR_chaos_core` keeping Y as a 24-bit unsigned value (`& 16777215`) and `SCR_chaos_sample_damage` killing on `y > room_height`, so any excursion
above world Y 0 would read as a huge Y (the ROM wraps the same way but its test is signed). This was not executed. The discriminating log is: world Y, view Y, Y speed, requested state and the death source on the death frame.

## 9. Loop / twist / special states

* **Type `$26`**: player state is not read; only the requested state `$21` blocks (all 64 values of each of `$D501/$D502` swept). Loop states `$0C/$0D/$13`, twist `$22`, act-clear `$20`, rolling,
  jumping, falling and spring flight all pass the gate if the floor flag, Y-speed sign and geometry pass. When it fires it requests `$0B` **from any state**, overwriting loop/twist/act-clear
  requests, setting vy only (vx kept).
* **Terrain springs** (types 9, `$14`, 10, ceiling): dispatched from `$690B`, which the shared update `$3FEF` calls; states that never call it never evaluate them. From
  `docs/terrain-ring-collection.md` section 6 (EMULATED, 26 states observed to call it): `$00-$0B, $0E, $0F, $10, $11 (gated off), $12, $14, $15, $17, $19, $1A, $1B, $1C, $1D, $1E`; **not** called in loop
  states `$0C/$0D/$13`, twist `$22`, act-clear `$20`, `$16`, `$18`, `$1F`, `$21`, `$23+`. So a terrain spring is **inert** in loops, the twist and act-clear. Inside the evaluated states only
  `$11` blocks the upright/diagonal/horizontal handlers.
* A launch forces a state transition (`$0B/$1C/9/$1B`) and overwrites velocity as in section 5.

## 10. Presentation versus gameplay anchors

* **Type `$26`**: gameplay anchor = object `+$11/+$14` = placement X and placement Y + 12 (`$825A`). Mapping `$91C0` records are drawn from the same coordinates
  (`docs/mapped-object-screen-registration.md`: rows -6..+17 for frame 2), so at rest the art sits 12 px below the placement Y; the extension raises the **object** by 7 px per update for 4 updates
  (28 px; rest -> placement Y - 16) while contact is not evaluated. Never derive the contact window from the visible top of a frame, the extension height or the GameMaker mask.
* **Terrain springs** are ordinary background tiles: the gameplay shape is the layout cell plus its collision header; no object, no separate collision anchor. Probes: upright/diagonal `(X, Y+18)`,
  horizontal `(X ± 9, Y+6)`, ceiling `(X, Y-6)`.
* The animation counters of `$0B` depend on `$D448` (section 6) but are presentation/timing only.

## 11. Tests and evidence counts

| Fixture (`tools/spring_interaction.py`) | Cases | Result |
|---|---:|---|
| type `$26` state 7 grid + edges | 1,630 | 0 mismatches against the model |
| type `$26` gate sweeps (vy, floor, requested/current 64 states, flags) | 154 | as section 3 |
| type `$26` span (state 8 grid, gates, state 9) | 35,415 | 0 mismatches |
| type `$26` parameters (real `$825A` initializer) | 54 | as section 4 |
| terrain upright / diagonal right / diagonal left (6 previous classes x 2 floor x 3 vy x 36x36 probes) | 3 x 46,656 | 0 mismatches |
| terrain gates, `$D297`, launches | 68 | as sections 3, 5 |
| terrain horizontal (4 cells, both probes) | 40,967 | 0 mismatches |
| ceiling blocks | 6,406 | 0 mismatches |
| bounce-on-break blocks | 8 | as section 1 |
| attack gate (`$5F3D`, `$B2B2`) | 17 | as section 7 |
| **controlled total** | **224,687** | |
| emulated: all 33 canonical spring cells, 10 flight classes, 4 horizontal cells, 2 object cycles, 1 top-of-screen thrust | - | as sections 1, 5, 7, 8 |
| `tests/test_spring_interaction.py` | 33 tests | cache-driven checks plus ROM-backed random sweeps with different seeds (4,000 + 3,000 type `$26`, 7,500 terrain cells over all acts, 2,000 horizontal, 400 death, 500 attack) |

## 12. Unresolved

* Names of terrain flag types `$09/$14/$0A/$16/$0D` and of player state `$21` (numeric only).
* Which POC mechanism produces the reported top-of-screen death (section 8); the ROM side is closed.
* Whether the camera Y follow can ever lag a launch enough to leave the view (no emulated flight did; no formal bound).
* The parked type `$27` observation was not traced end to end.
* Type `$26` frame-by-frame pixel timing of states 1..6; behavior outside THZ (the `$FA80` diagonal speed was verified as an immediate, not on a zone layout).

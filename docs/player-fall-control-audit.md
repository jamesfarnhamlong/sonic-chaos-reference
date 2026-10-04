# Shared player fall / control audit (special fall `$14`, ordinary fall `$0E` + monitor/wall, fall-state support)

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified; never committed). Branch `research/player-fall-control-audit` from Research `main` @ `a779fde`. The POC and the root `AGENTS.md` were **not** modified; POC files were only read.
Machine-readable facts: `data/rom-cache/player-fall-control.json`. Tool: `tools/player_fall_control.py` (`python tools/player_fall_control.py ROM [--check] [--static-only]`, ~85 s). Tests: `tests/test_player_fall_control.py` (46 tests, ~25 s; cache locks plus ROM re-execution). `tests/verify_cache.py` regenerates the cache.
Prompted by the Windows MGHZ M1 observations (which pre-date MGHZ): Left/Right "read but no acceleration" in the special fall, an uncontrollable fall through two platforms, and a ring-monitor/wall snag. The POC diagnosis (`docs/mghz-fall-control-diagnosis.md` in the POC workspace, read only) already showed the same behavior at the accepted checkpoint `82ebc89`; this audit answers it from the ROM.

Evidence labels: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY**, **CONTROLLED ROUTINE RESULT** (original Z80 routines on `tools/oracle.py`), **EMULATED ORIGINAL FRAME** (whole game in `tools/sms_frame_harness.py`, Sonic/camera teleported, requested state set so the engine loads that state's own script, pad held from before the first update), **SYNTHETIC CONTROL** (state or placement injected, never a canonical placement), **POC SOURCE (READ-ONLY)**, **UNRESOLVED**.

## 0. Verdicts

| # | Observation | Class |
|---|---|---|
| A1 | `$14`: Left/Right read, **zero acceleration** | **CANONICAL** (not a POC omission) |
| A2 | `$14`: X speed preserved, **no friction** (only walls, the +/-4.0 clamp, the screen-edge clamp change it) | CANONICAL |
| A3 | `$14` gravity/terminal speed equal ordinary fall `$0E`; entry sets Y speed +1.0, keeps X speed | CANONICAL |
| A4 | Entering a `$19` strip slower than max / stopping on it / landing on it requests `$14` at once | CANONICAL |
| A5 | All terrain passes run in `$14`; only the one-way projection is skipped (marker + requested `$14`) | CANONICAL |
| A6 | `$14` passes through a **second** `$19` strip below the first and on to the pit | CANONICAL |
| A7 | Marker (`+$24` bit0) lifetime: set by `$19` foot samples, cleared by air sample / jump / `$463C` / walk-run selectors | CANONICAL |
| A8 | Landing from `$14` requests **walk** `$05`, so a strip landing hops straight back into `$14` | CANONICAL |
| A9 | MGHZ1 pit below the lower strip has no floor; the fall ends in screen-relative death at world Y 987..991 | CANONICAL |
| A10 | POC death line for that fall is Y1043 (camera bottom 832) vs canonical camera bottom 784 (+`$D0` = 992) | UNRESOLVED (needs a decision: adapter or fix) |
| B1 | A monitor is a **solid floor from above** (`$5FA0` snaps Y to `monitorY-24`, mirrored contact gives D523 bit1) | CANONICAL |
| B2 | POC monitor projects **no top contact** and has **no D523/camera guard** on side pushes | **POC DIVERGENCE** (source-traced) |
| B3 | One-update push of Sonic into the wall, terrain pushes back, D523 guard then stops all pushes | CANONICAL |
| B4 | The POC's repeating push/pull with opposing flags is **not** reproduced by the original | **POC DIVERGENCE** |
| B8 | After a one-frame push into the wall at the floor line the floor projection pops Sonic up 32 px (Y814 -> 782); he then lands on the monitor top (the POC's Y782 event itself is canonical) | CANONICAL (synthetic placement) |
| B5 | Wedged between monitor and wall (D523 = 14, vx 0) is stable in the original, reachable only by placement | CANONICAL (synthetic only) |
| B6 | `$0E` vs `$14` does not change the monitor/wall outcome, only the approach | CANONICAL |
| B7 | `$5FA0` right/left pushes use viewport windows (camera+`$20`..camera+`$E0`) | EXPLICIT ADAPTER CANDIDATE (wide views) |
| C1-C4 | One-way, `$28` and GPZ `$1C` support by fall state (section 4) | CANONICAL |
| C5 | "Fall through two isometric platforms" = the two MGHZ1 `$85/$87` strips | UNRESOLVED only if James meant `$1C` decks / `$28` platforms (those are never passed through by a fall state) |
| D1 | A QoL air-steering adapter for `$14` would be a deliberate non-canonical change | EXPLICIT ADAPTER CANDIDATE |

## 1. State `$14` runtime (part A)

### 1.1 Entry (BYTE-VERIFIED, opcode scan of the whole ROM)

* Only one instruction requests `$14` for the player: `LD (IX+2),$14` at **`$4663`** (the two other hits, bank `$1E` `$9FCD/$AAF4`, are other objects). Its **only caller** is `JP nz,$4663` at **`$37C3`**, inside the walk callback `$3783` (script trampoline `$03E9`).
* Walk callback `$3783`, after the shared update `$3FEF`, with requested state still `$05`: facing update `$48A7`; if the signed X high byte is not `$00/$FF` and Down is held -> `$47DC` (roll); **water (`$D443 != 0`) skips the rest**; `|vx|` high byte **equal** to `$D374` (current maximum, normally 4) -> `$47A9` (run `$06`); otherwise **`+$24` bit0 set -> `$4663`**. Equality, not `>=`.
* Run callback `$384D` requests walk `$05` when the **signed** high byte's absolute value is below 4 (`vx >= 1024` or `vx <= -769` keep running). So decelerating running Sonic reaches `$14` through `$06 -> $05 -> $14` (GPZ2 fixture: `+1004` requests `$05`, `+984` requests `$14` on the next update).
* Landing (`$45CE`, see 1.7) always requests **walk**, never idle. A fall or jump that lands on a `$19` strip below max speed therefore hops straight back into `$14` (`ordinary_fall_onto_lower_strip_neutral`: landing request `$05` on update 71, `$14` requested on update 72).
* `$4663` (CONTROLLED, 240 setter cases): requested `$14`; **Y speed := +1.0**; `+$03` bit0 (airborne) set, bit1 (attack posture) cleared; `+$22` bit1 (floor) cleared; `$D3BC := 0`; **`+$24` bit0 retained**; X/Y position, X speed, plane untouched. Ordinary fall setter `$463C` is identical except it **clears `+$24` bit0** and does nothing when the current state is `$0A`.
* Only two fixed-bank comparisons treat `$14` as a *player state*: the callback's own landing gate (`$3A4E`) and the one-way floor gate (`$6FC4`). (`$7402/$7569` compare *surface type* `$14`.)

### 1.2 Callback and shared update

`$14` callback `$3A48` and ordinary fall `$0E` callback `$3A37` are the same code: `CALL $3FEF; if requested state == own state and merged contact (+$23) bit1: JP $45CE`. All differences are therefore in the **tables** and the **setter**.
Shared update `$3FEF`: `$4B46` (zone 4 acts 0-1 only: water-timer counters `$D444/$D445`, requests `$1F` at 17; unrelated to GPZ/MGHZ), `$401A` (screen-Y death), `$4141` (input/friction tables), `$402A` (X clamp + integration), `$4097` (gravity + Y integration), `$690B` (terrain), `$48BC` (damage gate), then a jump check that does nothing while `+$03` bit0 is set.

### 1.3 Horizontal input, acceleration, velocity preservation (CONTROLLED, 5,296 cases, 0 mismatches vs the model below)

`$4141` indexes six 2 x signed-16 tables by `state*4` (+2 for "not Left"), only for states below `$1E` (`$1E..$28` return before the tables): dry right-moving, dry left-moving, water right/left (`$D443`), a friction table (`$439D`, used when Left and Right are both up; water uses the same friction) and an unused one. **State `$14`'s words are 0 in every table**; state `$0E` has +/-16 (dry), +/-4 (water) and friction 16. Both states share the `$402A` clamp.

```text
delta = (no direction) ? (vx == 0 ? 0 : friction[state][vx<0 ? 0 : 1])
                       : table[dry/water][vx<0 ? neg : nonneg][state][Left ? 0 : 1]
if |vx| + $80 < $100: delta *= 2                       # near-zero doubling
vx' = vx + delta
if vx' >= 0: if high(vx') >= high(max) then vx' = +max
else:        if high(vx') <  -high(max) (unsigned byte) then vx' = -max         # max = $0400
```

For `$14`: `vx' = vx` (so a speed beyond +/-4.0 is clamped, as everywhere). `$402A` also zeroes `vx` and the input delta when the merged contact byte blocks the direction (D523 bit2 = right, bit3 = left). `$4141` additionally keeps Sonic within screen X 16..247 for **every** state below `$29` (reposition to camera+16 / the right limit, offset by the update's own speed, and zero vx; `edge_clamp` fixture with vx -/+2.0: screen X 8 and 12 -> 18, 248 -> 245, vx 0, identical for both states); that is EDGE-relative, not a state-`$14` rule. Water: the strip-fall branch of the walk callback is skipped, and water tables/gravity (`$18`, terminal 4.0) apply.
Fixtures: `air_fixtures` (16 updates, both states, vx 0/+1.0/+4.0/-4.0, four pad plans) and whole-game `strip_scenarios`: after the first update `$14` holds vx at 272 (Right), 240 (Left) or 236 (neutral) until a wall or the pit.
(`272/240/236` = the entry update's last state-`$05` step, +16 / -16 / -20 friction, then constant.)

### 1.4 Gravity (CONTROLLED, 1,400 cases, 0 mismatches)

`vy' = vy + $30` dry (`$18` water); a non-negative result with high byte >= 7 (dry) / >= 4 (water) becomes `$0700` / `$0400`. `$0B` (`$18`) and `$1B` (`$24`) have their own increments; `$0E` and `$14` do not. Floor flag set forces +7.0 in `$4097`. Fixture: Y 500, 501, 502, 504, 505, 507 for vx 256 (identical for `$14` and `$0E`).

### 1.5 Flags: attack / floor / airborne

Entry: airborne set, attack posture clear, floor clear (1.1). During `$14` Sonic is **non-attacking** (a badnik contact damages; `$D503` bit1 stays clear). Landing `$45CE` clears `+$03` bits 0, 1 and 6, requests walk `$05`, sets max speed `$0400`, runs `$48A7` and sets `$D289 = $60`.

### 1.6 Terrain passes and support eligibility (EMULATED, PC-hook order)

Identical in both states for a mid-air update: `$4141 -> $402A -> $4097 -> $690B { $691A floor + $6F61, $715E sides, $73C9 ceiling, $753E rings, $64CB merges } -> $48BC`. **Executed in `$14`: all of them.** The one skipped step is the one-way floor projection **after** the strip handler `$6B23` has set `+$24` bit0: `$6FBB` returns while the bit is set and the requested state is `$14` (trace: `one_way_gate_6FBB` is followed directly by `surface19_6B23` in `$14`, by the projection's own `merge_64CB` in `$0E`). Gate matrix (4 block kinds x 53 requested states x marker 0/1, `$691A`): only the pair (marker set, requested `$14`) changes the projection, and only on one-way blocks (`$0D` and `$85`); the solid block `$01` and the GPZ deck `$8C` are unaffected. Solid surfaces use `$6F6D`, which never reads the marker.
Support by state is in section 4. Short form: `$14` **acquires** ordinary solid floors, GPZ `$1C` decks, type-`$28` platforms (owner id set, rider Y = platform Y - 14), monitor tops and terrain springs exactly like `$0E`; it **never acquires** one-way blocks while the marker is set and a `$19` strip's one-way surface at all.

### 1.7 Exit conditions and requested successors (CONTROLLED + EMULATED)

| Condition | Result (both `$14` and `$0E`) |
|---|---|
| merged contact bit1 (solid floor, one-way, `$28` rider, monitor top) and requested state still own | `$45CE`: request `$05` |
| hurt (damage request `$D3B0`, or a non-attacking contact) | rings: request `$1E`, Y -4.0, X -1.0 (+1.0 when D523 bit3, a left wall, is set), flags `$C1`; no rings: request `$1F`, Y -5.0 |
| screen Y (`$D51C`) >= `$D0` | `$4984`: request `$1F` |
| terrain upright spring (MGHZ1 cell (110,25)) | request `$0B` (update 27 in both; Y -7.5) |
| jump press | nothing (`$45ED` returns while airborne) |

### 1.8 The surface-`$19` marker (`+$24` bit0) lifetime

* **Set** by the surface handler `$6B23` on **every** foot sample (anchor Y + 18) of surface type `$19` (blocks `$85/$87`), *after* that update's projection, and increments `$D3BC`. The projection of the first update uses the previous (air) surface, so the bypass applies from the **second** strip update on - which is why a fall onto a strip is never supported while in `$14`.
* **Cleared** only by: a foot sample of **surface 0** (`$6C45`, which also clears bit1), a normal jump `$45ED`, the ordinary fall setter `$463C`, and the Sonic walk/run frame selectors (bank `$0C`) on a non-`$19` surface (fixture: marker set on ordinary floor is cleared in the first walk/run update, retained in idle).
* **Persists** across every other surface type (matrix over 26 types: `$19` sets, `$00` clears, all others leave it; `$1B` only sets bit1). It is retained by the `$14` setter, by landing, and by the strip's own landing/hop cycle until an air sample.
* Consumers: the one-way gate `$6FBB` (with requested `$14`) and the walk callback `$37BF`. `$D3BC` is shared with surface `$1B` and is **not** a strip timer.
* Timeline, MGHZ1 `upper_strip_walkoff_right`: marker `[1,1] [15,0] [83,1] [88,0]` (set on the upper strip, cleared at the first air sample, set again by the lower strip's foot samples on updates 83-87, cleared again below it).

### 1.9 Whole-game fixtures (EMULATED ORIGINAL FRAME)

MGHZ1 upper strip (cells X102..111 / Y12, top Y384; lower strip X95..109 / Y27, top Y864, **nothing below it**), start (3408,366), state `$05`, vx +1.0:

| Case | Result |
|---|---|
| hold Right / Left / neutral | `$14` requested on update 1 and current on update 1; vx 272 / 240 / 236 constant; foot `$19` on updates 1-14, again 83-87; marker bypass; death requested on update 104 at Y987 (screen Y 210, camera 777) |
| `$0E` released at (3300,450), any pad | lands on the lower strip (update 71, Y846, floor), requests `$05`, then `$14` on update 72 (neutral) - falls through; holding Right at full speed 4.0 crosses until the wall (update 83) |
| `$14` injected (SYNTHETIC) at the same place | passes through the lower strip, marker 70-74, death update 91 |

GPZ2 strip (528,686): walk-off lands on the solid floor Y878 on update 43/44 for all three pads; running +4.0 holding Right crosses the strip supported for 60 updates; releasing at +4.0: update 1 `+1004` (walk), update 2 `+984` and `$14`.
Strip census (DECODED): 13 `$19` runs in GPZ1 (2), GPZ2 (2), MGHZ1 (5), MGHZ2 (2), MGHZ3 (2); the MGHZ1 lower run and MGHZ3 `(7, 15..26)` have the level bottom below them, so for them a failed run is a bridge fall (inference about intent; the behavior is the measured one).

## 2. Monitor + wall (part B; MGHZ1 monitor record 16 at (3568,814), wall column 112 from X3584, floor row 26)

### 2.1 Ordering inside one frame (EMULATED, PC hooks)

Player update first: animation engine, state callback (`$402A`, `$4097`, terrain `$690B`: floor, **sides `$715E`**, ceiling, rings, merges `$64CB`), damage gate; **then** the object list. The monitor's `$5FA0` therefore sees the terrain flags of the same frame's merge; the player's next X integration sees `D523` as merged at the end of the previous player pass, and the monitor's mirrored `D521` nibble (`$80` = left, `$20` = floor, `$40` = right, `$10` = ceiling) is merged one pass later.

### 2.2 `$5FA0` (BYTE-VERIFIED, 20,000-case model in `tools/collision_geometry.py` + guard matrix here)

`$6328` keeps one axis (ties vertical; Sonic 8x24 vs monitor 10x24: dx +/-18, dy -24..+24). Then:

| class | push | skipped when |
|---|---|---|
| above | `Y = monitorY - 24` | D523 bit0 already set |
| below | `Y = monitorY + 24` | D523 bit1 already set |
| right | `X = monitorX + 18` | D523 bit2 set **or** `playerX > cameraX + $E0` |
| left | `X = monitorX - 18` | D523 bit3 set **or** `playerX <= cameraX + $20` |

It never touches velocity, state or floor flags (`$10` then does its attack branch; non-attacking Sonic just stays solid). Top standing exists because the mirrored contact is merged into D523 bit1.

### 2.3 What the original does (EMULATED)

* **Natural arrival** (the POC route: from the upper strip at (3504,366), +1.0, Right or neutral): `$14` falls and **lands on the monitor top** at (3575,790) with `f22 = 4` (terrain right wall) and `f23 = 6` (floor via the monitor). 63 of 120 natural arrivals (shaft X 3540..3576 x vx 0/256 x three pads x both states) end there; 0 cases with D523 bits 2 and 3 together, 0 cases with X >= 3584, 0 X oscillations. (Hold-Left runs steer into other terrain.)
* **Deep overlap** (SYNTHETIC placement inside the monitor box beside the wall, `synthetic_push_into_wall_then_terrain_return`): update 6 the monitor sees D523 = 0, classifies **right** and pushes X to **3586** (into the wall); update 7 the terrain pushes back to **3575** (f22 = 4, merged D523 = 12 with the mirrored left bit), the monitor sees D523 = 12 and **skips** the push; update 8 `$402A` takes the blocked branch and zeroes vx and the input delta; Sonic lands on the floor (Y814) with D523 = 14 and stays: stable, **no repeating push**, vx 0 with Right held, standing between monitor and wall. `$14` gives the identical final state. A jump leaves it.
* Chamber grid (SYNTHETIC, 192 placements X 3552..3575 x Y 786..830, no input, both states): 30 right-class pushes, every one ends at X 3575 (wedged on the floor at Y814 with D523 = 14, or standing on the monitor top at Y790 with D523 = 6); 182 end stable within 12 updates, the other 10 are left-class placements pushed out to X 3550 that are still moving at update 12 (state `$19`, not wedged).
* **Floor-line pop** (SYNTHETIC, `synthetic_floor_line_push_pops_to_monitor_top`: (3570,806), Y speed +1.0, no input): the one-frame push to X 3586 happens at the floor line; the next update's floor projection samples the wall column and **pops Sonic up 32 px (Y814 -> 782)** with D523 = 14; he then falls back, the monitor classifies **top**, projects Y790 and he stands there (final (3575,790), D523 = 6). This is the original's own "Y782" event - the POC trace shows the same pop, so the pop itself is not the divergence; what differs is that the original then settles on the monitor top and the POC does not.
* Why the POC differs: the POC's monitor never projects the top contact, so a falling Sonic sinks to |dy| <= 13 where `$6328` classifies **right** (dx +7), pushes him toward the wall each update, and has no D523 guard to stop it (POC SOURCE: `objects/OBJ_chaos_object_10/Step_0.gml`, "Top-of-box standing is not projected here"; only the bottom push honors D523 bit1).

### 2.4 `$0E` versus `$14`

No difference at the monitor or the wall: the same classification, projection, flags and settling (chamber-grid rows are identical for both states). `$14` only removes steering, so a player who would have held Left in `$0E` to leave the area cannot.

## 3. Reproduce / consume

`player-fall-control.json`: `part_a_state_14` (`input_tables`, `horizontal_sweep`, `vertical_sweep`, `air_fixtures`, `setter_diff`, `surface_marker_matrix`, `one_way_gate_matrix`, `exit_fixtures`, `edge_clamp`, `strip_scenarios`, `gpz2_strip_scenarios`, `pass_trace`, `marker_lifetime`, `spring_exit`, `strip_census`), `part_b_monitor_wall` (`solid_guard_matrix`, `natural_monitor_falls`, `natural_fall_sweep`, `wedge_fixtures`, `chamber_grid`), `part_c_fall_support` (`support_matrix`), `classification`, `agents_candidates`. `tools/player_fall_control.py` also carries the Python shadow models (`model_x_update`, `model_y_update`) used by the sweeps.

## 4. Support while falling (part C; whole game, every state `$00..$34` forced as the requested state, released 80 px above the surface at +1.0, no input)

"Retained" = Y plateau with a floor flag or support owner at the end; "acquired" = a floor flag/owner at any update.

| Surface | Retained | Acquired but not retained | Never acquired |
|---|---|---|---|
| one-way `$41` (MGHZ1 (86,7)) | `$00-$0B $0E $10 $11 $14 $19-$1E $21 $22 $25` | `$0C $0D $0F $12 $13 $15 $1F` | `$16-$18 $20 $23 $24 $26-$34` |
| `$19` strip (MGHZ1 (22,11)) | `$00 $01 $02 $0C $0D $0F $13 $19 $1B $21` | `$03-$0B $0E $10 $11 $12 $15 $1A $1C $1D $1E $22 $25` | `$14 $16-$18 $1F $20 $23 $24 $26-$34` |
| solid (GPZ2 (54,8)) | `$00-$0B $0E $10 $11 $14 $19-$1E $21 $22 $25` | `$0F $12 $15` | `$0C $0D $13 $16-$18 $1F $20 $23 $24 $26-$34` |
| GPZ `$1C` deck (GPZ2 (4,6)) | `$00-$0B $0E $0F $10 $11 $14 $15 $19-$1E $21 $22 $25` | `$12` | `$0C $0D $13 $16-$18 $1F $20 $23 $24 $26-$34` |
| `$28` platform (GPZ2 (1584,384), param `$83`) | `$00-$0B $0E $10 $11 $14 $19-$1F $21 $22 $25` | `$12` | `$0C $0D $0F $13 $15-$18 $20 $23 $24 $26-$34` |

Fall-relevant reading: `$0A` (jump), `$0B` (upright spring), `$0E`, `$14`, `$1B` (ramp launch), `$1C` (diagonal spring) and `$11` (Rocket Shoes) acquire and keep ordinary one-way, solid, deck and `$28` support. `$12` (Spring Shoes) acquires and relaunches. Loop/route states `$0C/$0D/$13`, `$16-$18`, act-clear `$20`, death `$1F` (except on a `$28` rider) do not retain terrain support (they follow their own tables or end the fall); the full per-state rows are in the JSON. The `$19` strip is the exception: a landing state hops straight to walk and then `$14`, so only states that do not request walk on landing (idle `$01`, `$00/$02`, `$0F`, `$19`, `$1B`, `$21`) stay on it, and `$14` never acquires it.
Marker-set variants (SYNTHETIC, foot starts 2 rows inside the surface, marker 1): `$0A/$0E/$0B` are still supported by a one-way `$41` block, `$14` is **not** (the bypass applies to **any** one-way block while the marker persists); the GPZ deck supports all four (the solid path ignores the marker).
`$28` support is independent of the player state (earlier controlled audit: all 52 states); here every state whose update lets the object phase run acquires it, subject to the platform's Y-speed gate (`platformVy <= playerVy`).

**The Windows pass-through.** MGHZ1's two strips are terrain `$85/$87`. A `$14` Sonic passes through both (section 1.9) and the fall ends in the pit; Sonic cannot steer. The same fall in `$0E` lands on the lower strip but the landing request (walk) hops into `$14` again unless Sonic arrives at full speed. A GPZ `$1C` deck or a `$28/$83` platform is **never** passed through by a falling body in the original, so if the Windows run passed through those it is a POC divergence (C5).

## 5. Classification detail, adapter candidates, unresolved

* **POC divergence (implement from this audit):** (B2/B4) monitor top projection `Y = monitorY - oEy` unless D523 bit0, and D523 guards on all four pushes.
* **Explicit adapter candidates (do not apply silently):** wide-view windows for the `$5FA0` side pushes (EDGE-relative, canonical window camera+`$20`..camera+`$E0`) and for the `$4141` edge clamp (X within camera+16..247); an optional QoL steering change for `$14` (D1) - would be non-canonical, keep the canonical zero-control behavior as the default until Windows acceptance.
* **Unresolved:** (A10) whether the POC camera-bottom choice (832 vs the header's 784 = height-240) is an intentional widescreen adapter; (C5) which platforms James meant; the internal branch conditions of the bank-`$0C` walk/run selectors that clear the marker were validated behaviorally (and by `docs/gpz-surface19-audit.md`) but not re-derived here; the source of the camera lag that makes the death request arrive at camera 777..780 instead of 784 was not traced.

## 6. AGENTS candidate updates (not applied)

1. State `$14` (special fall) has all-zero dry/water/friction input tables: Left/Right are read but produce zero acceleration and no friction; X speed is preserved (only walls, the +/-4.0 clamp and the screen-edge clamp change it). This is canonical, not a POC omission. Gravity and terrain passes equal ordinary fall `$0E`.
2. The only entry to `$14` is the walk callback with the strip marker (`+$24` bit0) set and |vx| high byte != the current maximum (dry). Landing always requests walk `$05`, so a landing on a `$19` strip slower than max hops straight back into `$14`. Only max-speed running crosses a strip.
3. The strip marker is set by every surface-`$19` foot sample (after that update's projection) and cleared only by a surface-0 foot sample, jump, `$463C` or the walk/run selectors on non-`$19` ground. Requested `$14` + marker bypasses one-way projection only (not solid decks, not type `$28`).
4. A monitor (`$10`) is a solid floor from above: `$5FA0` snaps Y to `monitorY-24` and the mirrored contact supplies D523 bit1. Side/bottom/top pushes are skipped when D523 already has the matching bit (and, for left/right, outside the camera+`$20`..+`$E0` window). A one-update push into a wall is canonical; a persistent push/pull snag is not.
5. Viewport guards in `$5FA0` (camera+`$E0` / camera+`$20`) and the `$4141` screen-edge clamp (X within camera+16..247 for every state below `$29`) are EDGE-relative; use explicit adapters for wide views.

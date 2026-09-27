# Task 09 — THZ1 engine / POC reconciliation

Date: 27 September 2026

Canonical input is the 524,288-byte SMS ROM with SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
The GameMaker comparison is the read-only `SonicChaos_POC_poc19` tree. This
report does not treat POC output as ROM evidence. It does, however, supersede
the implementation advice in Tasks 07/08 where that advice confused a ROM
anchor with a GameMaker instance origin.

## Executive result

There is no evidence for one universal numeric Y offset for every THZ1 entity.
There is a universal *conversion procedure*: preserve a canonical ROM anchor,
render every mapping piece from that anchor, include the SMS SAT `Y+1` rule,
and choose the GameMaker origin from the reconstructed mapping canvas rather
than from collision geometry. Terrain-quadrant objects are a different source
class and must be registered to the quadrant's pixel rectangle.

POC 19 violates that procedure in three ways. It uses room-instance `y` as
both canonical anchor and GameMaker draw origin; it keeps legacy sprite origins
for terrain-derived rings; and it compensates type `$21` with a `+18` Draw
event. The last change looks good because it places the sprite bottom at the
collision surface, but it is not the ROM renderer. The ROM really renders the
type `$21` pixels above its `+18` floor probe. Therefore the Task 08 statement
that the ROM has a 17-row visible gap is source-correct; its POC recommendation
(`+1` only) is not sufficient to match the user's desired visually grounded
POC presentation. Those are two different targets and must not be conflated.

The serious terrain failure has a separate, concrete cause. On damage POC 19
changes the player into `OBJ_player_lost_a`. That object no longer executes the
Chaos core and instead calls the sample project's `SCR_physics()`/mask
collision. Invincibility itself does not bypass the Chaos terrain core;
damage-state object substitution does.

## 1. ROM to GameMaker vertical-coordinate contract

### 1.1 ROM mapping objects

For an ordinary mapped object define:

```
A = integer object anchor (+$14/+$15)
C = camera Y ($D176)
O = signed frame Y origin
P = signed mapping-piece Y
T = first nonzero tile-row within the 8x16 piece
```

The first displayed SMS pixel is `A - C + O + P + T + 1`; `+1` is the SMS SAT
convention. The corresponding world pixel is `A + O + P + T + 1`.
The last pixel uses the last nonzero tile row. Collision probes and contact
extents are not terms in this render equation.

For a GameMaker canvas whose source pixel row is `R`, draw at:

```
GM_draw_y = A + 1
GM_yorigin = R - (O + P + T)
```

Equivalently, omit the draw `+1` and subtract one from the Y origin. This is
the only generic ROM-mapping transform justified by `$3FC8/$226A`.

ROM object Y is therefore a canonical physics/render anchor, but it is **not
automatically equivalent to GameMaker instance Y**. Equality is valid only
when the selected GameMaker origin makes every canvas row reproduce its signed
mapping coordinate. Transparent canvas padding is harmless only when included
in that origin calculation.

### 1.2 Terrain and layout-quadrant entities

The 142 ring positions do not pass through the generic object renderer in the
original. Blocks `$40..$43` contain ring pixels in one or more 16x16 quadrants;
`$753E` selects the quadrant from adjusted X/Y bits 4, replaces the terrain
block, awards a ring, and creates only the collection effect. The POC's moving
`OBJ_ring` is an adapter.

For a quadrant at block origin `(bx,by)` and quadrant `(qx,qy)`, the canonical
pixel rectangle is:

```
left = bx + 16*qx
top  = by + 16*qy
right/bottom = left/top + 15
```

If an instance is stored at the quadrant centre, it must be `(left+8,top+8)`
with sprite origin `(8,8)` on an exact 16x16 crop. POC 19 instead uses the
legacy `SPR_ring` (16x18, origin `(7,9)`, nontransparent rows `1..16`) at centre
coordinates. Its visible bounds are displaced relative to the source quadrant
and its art is not a proof of the terrain-ring pixels. This is a generic
terrain-entity adapter bug, not bad source coordinates.

### 1.3 Answers to the coordinate questions

- ROM object Y equals the canonical GameMaker data anchor, not necessarily the
  GameMaker instance/draw Y.
- Mapping Y=0 is correct only when the reconstructed canvas origin is derived
  from that mapping row. It must not be chosen from the collision bbox.
- The current canvases do contain transparent padding. Types `$10/$21` account
  for it in their declared origins; `SPR_ring` does not represent the original
  terrain-quadrant source class.
- A collision surface is not a visual-ground reference. The `$21` `+18` probe
  is the clearest counterexample.
- SAT `Y+1` is the only proved generic sprite-render correction. There is no
  proved additional universal ROM renderer offset.
- The apparent shared error is an adapter-policy error (mixed anchors), not a
  proved common constant.
- Raw object-list entities and layout rings do use different conventions:
  object anchor/mapping versus terrain-quadrant rectangle.

## 2. Type `$10` presentation

The five raw placements remain unchanged. Initialisation does not alter Y.
Frames `$0B/$0C` have visible ROM bounds `A-24..A+7` after SAT `Y+1`.

| Placement / parameter | Visible pixels | collision surface | gap below sprite |
|---|---:|---:|---:|
| `(656,846)` / `$06` | `822..853` | 864 | 10 rows |
| `(1712,494)` / `$06` | `470..501` | 512 | 10 rows |
| `(336,270)` / `$04` | `246..277` | 288 | 10 rows |
| `(1472,110)` / `$04` | `86..117` | 128 | 10 rows |
| `(2688,686)` / `$02` | `662..693` | 864 | 170 rows |

The current 32x40 canvases have visible rows `4..35` and origin `(16,28)`, so
drawing at instance Y produces `A-24..A+7`: it already includes the canvas
padding correctly. An exact SMS presentation uses draw Y `A+1` (or origin Y
27), producing the hardware `+1` scanline. It does **not** move the placement,
settle the box, or apply the `$21` `+18` probe.

Windows' impression that all five are high is real feedback about the desired
POC composition, but it does not establish a ROM transform: four have a proved
10-row ROM gap and the `$02` record is intentionally suspended. If POC 20 is
intended to mimic the original, implement SAT `+1` only. A separate
"visually grounded" mode would be a noncanonical presentation policy and must
be labelled as such; do not encode it as per-placement data.

## 3. Type `$21` reconciliation

The first active patrol update integrates Y by `+2`, probes at the resulting
anchor `+18`, and `$70E7` subtracts the profile correction from the unshifted
anchor. Stable anchors are `590,846,302,878,270,238`; surfaces are each anchor
`+18`. Contact uses the unshifted anchor and fixed extents. Frames `$01/$02`
have nonzero mapping pixels at relative `-32..-1`; SAT therefore displays
`A-31..A`.

POC 19's sprite has visible rows `4..35`, origin 36, hence relative
`-32..-1`. Its Draw event then adds 18 and changes the visible bounds to
`A-14..A+17`, placing the last pixel immediately above the collision surface.
That explains why it looks grounded. It is not a missing canvas-origin or SAT
rule: it deliberately renders the physics probe, not the ROM anchor.

Implementation contracts:

- **Exact ROM:** retain the canonical instance/data anchor; draw at `A+1` or
  use origin 35; visible bottom is `A`; preserve probe `A+18` and all contact
  thresholds.
- **POC grounded-presentation adapter:** keep physics/contact at `A`, expose a
  named shared `render_anchor_y = A+18`, draw the mapping canvas from that
  render anchor, and declare it noncanonical. Never hide this in the object
  placement or floor projector.

Task 08's “17 blank rows” remains the exact ROM result. What is corrected here
is the earlier implication that this result must also be accepted as the POC's
visual-ground contract. The present `+18` is a POC policy, not newly discovered
ROM behavior.

## 4. Layout-derived ring registration

All 142 decoded source positions are retained. The audit contract is:

1. retain `(block_x,block_y,quadrant_x,quadrant_y)` as source data;
2. compute the exact 16x16 source rectangle;
3. create the POC collectible at `(left+8,top+8)`;
4. use a ROM-derived 16x16 quadrant canvas at origin `(8,8)`;
5. make collection use the same 16x16 rectangle, not an animated sprite bbox;
6. compare the pre-collection POC pixels with the removed terrain quadrant.

The current centre coordinates (for example `(328,216)`, `(328,232)`) are not
to be adjusted by eye. The current origin `(7,9)` is the suspect conversion.
This is especially visible in the twisting section because the ring quadrants
are read against strong curved terrain edges. It is not the same numeric error
as type `$21`, though both arise from treating an instance origin as a source
anchor.

## 5. Block `$47` contact contract

Block `$47`'s base header is solid type `$16`, vertical profile
`17,17,18x28,17,17`, horizontal profile `00x8,1Cx24`. Normal terrain collision
runs floor, both sides, ceiling, the special top probe, then merges contact.
`$6AE3` is eligible only when:

- player movement flag `+$03.1` (rolling/attack posture) is set;
- current player state is not `$0F,$10,$15,$1A`;
- and either combined side/ceiling contact bits `$D522 & $0C` are nonzero, or
  signed vertical velocity `$D518` is nonnegative.

Thus a qualifying side hit does not require downward velocity and does not
require a particular horizontal velocity sign. A pure floor/top entry requires
nonnegative Y velocity. Ceiling/side contact bypasses that Y-direction test.
The profile itself supplies the exact boundary: the lower 24 rows are side
solid (horizontal extent `$1C`), with no side profile in the first eight rows.

On success the handler writes vertical velocity `$FBC0` (-4.25), clears floor
contact, marks airborne, preserves horizontal velocity and numeric player
state, changes the collided cell to `$46`, refreshes its terrain mapping, sets
graphics selector 1, allocates type `$0F` parameter `$40` at block-centre X
and Y+8, and adds packed-BCD `$10` (ten rings).

POC 19 dispatches `$47` only inside `SCR_cc_floor()` and its condition requires
`move&2` plus a POC approximation of contacts. A side sensor can therefore
resolve the wall without ever invoking the break handler. The fix is a shared
post-floor/sides/ceiling surface-response dispatch using the merged contacts,
called once per tick. `$46` must update both the collision tile and the visible
terrain layer atomically; it must have the `$46` collision header immediately.

## 6. Type `$27` deterministic presentation

The placement scan occurs every fourth object update, after that update's
object scheduler. Accepted creation range is two-dimensional relative
`-96..351`; active/SAT range is `-32..287`. Creation sets an occupied slot with
zero pieces. The next object update executes empty state 0 and requests state
1. The following update loads nonempty frame 1; visibility/lifetime then
allows SAT output. Visible frame pixels are relative X `-12..11`, Y `-14..0`.

Normal left-to-right fixture for `(3504,224)`:

| Event | Condition/result |
|---|---|
| scan | camera X reaches the first cadence point in `3153..3600`; create after scheduler, no pixels |
| object update 1 | state 0 runs; request state 1; no pixels |
| object update 2 | state 1 loads frame 1; SAT only if camera X `3217..3536` and camera Y `-63..256` |
| first possible visible pixel | object left pixel enters at camera X 3237; displayed Y is `211..225` at camera Y 0 after SAT convention |
| state 1 | move -2.5 before strict `abs(objectX-playerX)<64` activation test |
| state 2 | 129 callbacks: 32 add, 64 subtract, 33 add; counter underflows on 129 |
| next update | state 3 resumes -2.5 X movement |
| removal | before movement/contact when strict separation `>=384`; placement occupancy is released and a later scan may recreate it |

During a fast camera jump an object may be created directly inside the active
rectangle, but the two empty updates still apply. If it remains in the outer
accepted band it sleeps with no SAT output. Pre-trigger departure releases
occupancy. POC 19 approximates cadence with a room-resident dormant instance
and stops the whole state callback whenever outside the SAT rectangle; the ROM
distinguishes created/sleeping, active update, and SAT eligibility. The POC
must keep those three booleans separate and sample camera coordinates once at
the scanner/scheduler phase boundary.

## 7. Damage, invulnerability, and terrain collision

Power selector `$06` and post-hit invulnerability suppress damage/object harm;
they do not suppress `$690B` terrain update. State `$11` also calls the shared
movement/collision path. A valid damage request reaches `$48BC`, cancels state
`$11`/selector `$04` where applicable, and requests hurt state `$1E`; it does
not switch to a different collision engine.

The shared player path continues floor, side and ceiling sensing in ordinary
grounded, ordinary airborne, hurt, post-hit invulnerable, power-invincible and
rolling/attack states. State-specific probe offsets exist (notably state `$21`
uses -14 and `$12` uses +8 for the floor lookup), but immunity flags are not a
terrain-collision gate. Genuine skips are bounded special controllers: loop/
twist handlers while they own position, death/removal transitions, and states
whose own script replaces the ordinary movement callback. They are selected
by numeric player state, never merely by `D532`, blink, or damage immunity.

Controlled POC regression matrix:

| Fixture | Required result |
|---|---|
| grounded, ordinary | floor probe each tick; remains projected |
| airborne descending | floor/side/ceiling run; land on crossing |
| hurt `$1E` | knockback/gravity plus the same terrain probes; no engine swap |
| post-hit blink | identical terrain result to non-blink at same state/position |
| selector `$06` | identical terrain result; object damage is suppressed/converted separately |
| rolling/attack | rolling extents/state flags, but terrain remains active |
| damage transition tick | resolve damage state and terrain in deterministic ROM order; preserve core position/velocity |
| blink expiry / power expiry | no discontinuity in anchor, plane, previous header or contacts |

POC 19 fails the hurt rows because `SCR_chaos_apply_hazard_damage()` calls
`instance_change(OBJ_player_lost_a,true)`. The replacement executes legacy
`SCR_physics()`, animated-mask collision and built-in gravity and loses the
Chaos core's anchor, plane, previous-header and contact state. `global.powerInv`
and `global.playerBlink` are correctly checked only around damage, but the
resulting object-class split makes the symptom appear immunity-related.

## 8. POC discrepancy classification

| Finding | Classification |
|---|---|
| no explicit canonical/render-anchor API | generic POC adapter bug |
| type `$21` Draw `+18` presented as ROM correction | object-specific POC policy/hack |
| type `$10` canvas origin 28 | correct for mapping rows; missing SAT +1 |
| `SPR_ring` origin `(7,9)` used for terrain quadrants | generic terrain-entity adapter bug |
| ring coordinates themselves | correct source data |
| `$47` response dispatched only from floor approximation | generic collision-dispatch bug |
| `$47` horizontal velocity preserved, vertical `$FBC0` | correct ROM behavior in POC 19.1 |
| `$27` cadence/empty frames | broadly correct intent; scheduler/SAT conflation remains a POC bug |
| hurt implemented by `instance_change` to legacy physics | generic player-state adapter bug, high severity |
| invincibility/blink checks around damage | correct concept; must remain object-damage-only |
| terrain disabled solely by invincibility | no such ROM behavior found |

## 9. Minimal shared fixes

1. Introduce separate `canonical_anchor`, `render_anchor`, and collision-probe
   helpers. Mapping sprites receive SAT `+1`; collision code never edits draw
   origins.
2. Introduce a terrain-quadrant collectible renderer with exact 16x16 source
   crops/origin `(8,8)` and fixed collection rectangles.
3. Move terrain surface callbacks to one post-sensor dispatcher fed by merged
   floor/side/ceiling contacts. `$47` becomes data handled by that dispatcher.
4. Keep one player instance and one Chaos collision core through hurt and
   immunity states. State changes mutate core state; they do not change to a
   legacy-physics object.
5. Split placement-created, update-awake and SAT-visible state in the object
   lifetime adapter; run scan cadence after the scheduler.

## 10. Cleanup implementation order

## POC 20 CLEANUP CONTRACT

1. Add anchor/render conversion helpers and pixel-bound assertions. Implement
   the SMS SAT `+1` once in the mapped-object draw path.
2. Add a canonical terrain-quadrant representation and regenerate/verify all
   142 rings without changing their source block/quadrant coordinates.
3. Remove type `$21`'s private Draw event. Select explicitly between exact-ROM
   rendering (`A+1`) and the labelled grounded POC adapter (`A+18`); tests must
   state which target they assert.
4. Keep type `$10` room placements and physics untouched; route frames `$0B/$0C`
   through the shared mapped-object draw helper.
5. Replace the floor-only `$47` branch with post-sensor response dispatch;
   atomically install `$46` art/collision and spawn the parameter-`$40` transient.
6. Replace hurt `instance_change` with a Chaos-core hurt state. Keep terrain
   collision live during blink, selector `$06`, selector `$04`, and transition
   frames; restrict immunity to damage/contact resolution.
7. Refactor type `$27` to explicit `allocated/sleeping/awake/SAT` phases and
   add the cadence table above as a frame-by-frame fixture.
8. Regression-test visible pixel bounds against reconstructed ROM bounds,
   `$47` top/side/ceiling entries, all player-state matrix rows, type `$27`
   steady scroll and camera jumps, occupancy release/recreation, and all 142
   ring quadrant rectangles.


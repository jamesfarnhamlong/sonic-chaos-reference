# Windows Act 1 POC roadmap after 14.5

Status date: 21 September 2026

## Current baseline: POC 14.5

Windows play-testing confirms a major improvement in general movement. The first
curved ramp now triggers rolling, carries Sonic up the curve, and returns cleanly
to standing. Moving platforms and both loops work. Red terrain springs feel close
to the original. The twisting strip still uses no original special-state behavior.

An emulator comparison on 21 September 2026 adds three refinements to this
baseline:

- the opening red upright spring reaches the expected height; remaining visible
  differences are player/spring animation-state issues, not evidence for changing
  its recovered impulse;
- the far-right object `$26` spring is dormant as a flush/hidden pressure device
  and extends only when Sonic steps on it; the POC's permanently visible orange
  spring is therefore not the original object presentation or activation cycle;
- the lower route contains timed retracting spikes which alternate between a
  nearly hidden tip and a fully raised damaging state. POC 14.5 does not implement
  this cycle.

POC 14.5 should now be treated as the comparison baseline. Future work should
preserve its single fixed-point movement authority and ROM-derived rules. A fix
must not introduce coordinate checks, invisible route helpers, painted collision,
or per-placement exceptions.

## POC 15 — spring and Act 1 interaction pass

Implementation status: source complete on 21 September 2026; original-handler,
movement-fixture and project-structure checks pass. GameMaker compilation and the
Windows acceptance runs below remain pending.

### Goal

Make every spring and required route interaction in Turquoise Hill Act 1 follow
its original object or terrain contract. This pass should make the level reliably
playable up to the twisting strip without changing the shared movement model.

### Research and implementation

1. Recover the complete bank-30 object `$26` update/contact routine.
2. Identify its requested player state, contact tests, re-trigger policy, animation
   timing, dormant/flush presentation, extension/retraction cycle, gravity path,
   and landing/apex transition. Do not draw a full spring before its activation
   state makes it visible.
3. Preserve the four Act 1 records and parameters:

   | World position | Parameter | Verified raw Y impulse |
   | ---: | ---: | ---: |
   | `(688, 864)` | `$00` | `-7.375` |
   | `(3568, 768)` | `$00` | `-7.375` |
   | `(1296, 608)` | `$8A` | `-5.0` |
   | `(1912, 864)` | `$01` | `-5.0` |

   The nonzero middle variants are deliberately weaker in the recovered handler.
   Their apparent under-power must be compared with the original trajectory before
   changing a constant.
4. Differential-test the object routine against the Z80 instructions, then replace
   the provisional object-spring adapter in the POC.
5. Exercise all terrain spring contracts already recovered:
   upright `-7.5`, THZ diagonal `X=±4, Y=-7`, and horizontal `X=±6` with its speed cap.
6. Add spring identity, source kind, parameter, current/requested state and native
   velocity to the F3 overlay while testing. Remove or hide the extra diagnostic
   once each placement is classified.
7. Verify plane transitions and walkthrough monitor passages encountered before
   the strip. Implement only the decoded tile/header rule that owns each transition.
8. Recheck damage, badnik rebound, monitors, checkpoints and moving-platform carry
   at the 60 Hz test clock. These are POC adapters and must not write terrain state.
9. Trace object type `$1B`. Four parameter-zero Act 1 records occur on the lower
   route at `(1344,864)`, `(1936,864)`, `(2464,864)` and `(2912,864)`. Their
   placement pattern makes them the leading retracting-spike candidates, but this
   identity remains provisional until the object dispatch/handler is decoded.
   If confirmed, port the original global/local timer, hidden-tip frame, raised
   frame, damaging interval and collision bounds without inventing per-placement
   phases.
10. Trace animation selection during terrain-spring flight. Keep the now-validated
    opening red-spring trajectory unchanged while correcting only ROM-supported
    animation/state scheduling.

### Acceptance checks

- Each of the four `$26` placements is present, identifies the correct parameter,
  and matches the original launch/landing route in an emulator comparison.
- The far-right `$26` placement is flush/hidden while dormant, triggers only on
  valid top contact, extends for the launch, and follows the original reset policy.
- The weaker middle spring is either demonstrated to be correct or changed because
  a traced object-state rule proves why the current flight is wrong.
- Upright, diagonal and horizontal terrain springs work in both applicable directions
  and retain momentum/state at their apex and landing.
- The opening red upright spring retains its 14.5 trajectory while Sonic's takeoff,
  ascent, apex, fall and landing animations follow the original state sequence.
- If type `$1B` is confirmed as the retracting spike object, all four records share
  the decoded timing rule, visibly pass through hidden-tip and raised frames, and
  damage Sonic only during the original active collision interval.
- The Act 1 route up to the twisting strip can be repeated three times without a
  stuck state, embedded player, missing interaction or location-specific workaround.
- Numerical fixtures execute the shipped GML source and cover every newly translated
  object branch. GameMaker compilation and Windows play-testing both pass.

### Explicitly outside POC 15

The twisting strip itself, generic enemy grounding, later breakables, other stages,
sound conversion and unrelated presentation polish remain separate work. Retracting
spikes are included because emulator evidence places them on the Act 1 lower route.

## POC 16 — original twisting-strip state

### Goal

Replace the current glide over the Möbius/twisting strip with the original state
`$22` behavior, including entry requirements, per-tile angle/magnitude changes,
alignment and exit back to rolling.

### Research and implementation

1. Add the state `$22` fields to the shared core: angle, magnitude and variant.
2. Port the verified THZ entry rules:
   - rightward entry tiles `$59/$5C`, at least `+3.0` X velocity;
   - leftward entry tiles `$73/$72/$6B`, strictly below `-3.0` X velocity;
   - only the original eligible current states may enter.
3. Export the four 28-entry dispatch tables as source data. THZ uses variants 0/1;
   variants 2/3 stay in the core data for later levels and tests.
4. Translate each handler literally, including tile-relative X/Y alignment, angle
   changes, magnitude changes, immediate-return helpers and ignored ROM writes.
5. Use the verified angle-table vector conversion and 16.8 integration. Keep this
   special-state movement inside the core so ordinary floor physics cannot also move
   Sonic during the same update.
6. On leaving surface type `$17`, clear twist fields and request rolling state `$09`
   exactly as the original routine does.
7. Drive sprite rotation and layer/plane presentation from the core's angle and
   state. Presentation must not alter the trajectory.

### Acceptance checks

- CPU comparisons pass for all four dispatch variants, 28 tile indices, representative
  magnitudes and both travel directions.
- At low speed Sonic fails to enter according to the original threshold; no hidden
  boost is applied.
- At valid speed Sonic traverses the complete strip in both directions, retains the
  correct collision plane/layer, exits into rolling and returns to ordinary movement.
- Overshoot, stopping and approach from the wrong side do not trap or teleport Sonic.
- Three consecutive Windows runs in each direction complete without divergence.

### Explicitly outside POC 16

Enemy AI, complete breakable/hazard behavior, music playback, other acts and final
camera/presentation tuning are not acceptance requirements for the twist pass.

## POC 17 — Act 1 systems and completion pass

After springs and the twist are stable, complete the remaining shared interactions:

1. Port generic object-floor projection for badniks, then trace each THZ enemy anchor
   and state rather than positioning enemies by their artwork bounds.
2. Translate special side/floor/ceiling dispatch needed by Act 1: breakables, hazards,
   push behavior and the remaining `$24` projection branches.
3. Audit object activation/despawn, platform phase, checkpoints, damage and respawn.
4. Confirm the original update cadence and PAL/NTSC scheduler before declaring real-time
   speeds final. Keep per-update physics fixed while this is measured.
5. Replace temporary completion/debug presentation with the Act 1 goal behavior and
   create a clean Windows build.

The acceptance target for POC 17 is one complete, repeatable Turquoise Hill Act 1
playthrough with no debug teleport, route exception or required guessed object.

## Evidence requested from Windows/emulator testing

For the `$26` spring investigation, the most useful capture is the middle weak spring
in both POC 14.5 and the SMS ROM: begin at rest, keep the same input throughout, and
show the landing or highest reachable platform. A normal video establishes the visible
route. An emulator memory trace of X/Y, velocity, current/requested state and contact
flags would establish the exact update contract.

For the twist pass, capture a successful and a deliberately slow approach in each
direction. Keep F3 visible in the POC. Record the emulator's region/timing mode and the
ROM SHA-256 with any original-game trace.

The emulator clips supplied on 21 September 2026 are observational evidence only:
they establish the visible spike cycle, the far-right spring's contact-triggered
extension, and the opening red spring's matching height. They do not by themselves
establish exact update counts because recording start, emulator pause state and
regional scheduler timing were not controlled.

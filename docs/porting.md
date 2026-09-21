# Porting plan and open questions

## Next Windows prototype

The immediate goal remains a reliable first act on Windows. The reference work supports a systematic replacement of the overlapping sample-engine and Chaos collision rules.

1. **Use one movement state.** Preserve current/requested state, movement flags, combined contact flags, fractional position and signed 8.8 velocities. Choose a single update unit before adding presentation scaling.
2. **Port the full lookup and ordinary collision sequence.** Preserve both profiles, modifier, collision plane, previous floor type and above-tile projection. Replace the v13 whole-mask wall stop when this path is tested.
3. **Match the supplied numerical fixtures.** Compare each update's position, velocity, type, modifier and state against the reference trace before relying on how the animation looks. The fixture is a bounded reference, not a complete replay.
4. **Apply ramp state `$1B`.** Preserve the eligibility branches and requested-state timing. Test both directions and low-speed approaches in an emulator to complete the current evidence.
5. **Integrate spring states and the apex transition.** Use the original terrain impulses and state gravity. Confirm object type `$26` variants separately.
6. **Implement the twist's tile handlers and angle integration.** Keep alignment rules and the actual immediate-RET behavior. Verify variants 0/1 in THZ and 2/3 in their original level.
7. **Ground enemies with their own object routine.** `$77CB/$70E7` is a useful starting point; their anchor sizes and state updates still need tracing.
8. **Drive animation from state and actual motion.** Standing, rolling, ramp launch and spring flight should have a single source of truth. Avoid a separate animation patch masking an incorrect physics state.

## Investigation still required

| Topic | What we have | What remains |
|---|---|---|
| First curve | Exact profiles, dispatch, positive launch arithmetic, core trace | Full animation/state scheduler replay; leftward/low-speed cases |
| Basic collision | CPU-tested lookup, ordinary projection, side cores | Special `+$24` paths and all tile-type interactions |
| Update timing | Active-update arithmetic | Confirm the game's scheduler and PAL/NTSC timing before converting to seconds |
| Springs | Terrain launch, gravity, apex transition | Object `$26` variants, downward/diagonal contacts in gameplay |
| Twist | Full tables/handlers and tested vector math | Complete per-variant traversal and animation/camera integration |
| Loops | Original path code and sample exports | Overshoot backing ranges, falloff and all exits in full gameplay |
| Platforms | Six placements and recovered code | Activation/despawn phase, all rider edge cases |
| Enemies | Generic floor routine recovered | Per-enemy anchors, motion/state code and corrected placements |
| Hidden passages | Alternate header selector and plane switches | Document each actual THZ1 passage transition |
| Breakables | Type handlers and map replacements | Actual later placements and attack conditions |
| Sound | 68 verified SMS pointers | Driver format, song naming, playback/rendering and Game Gear differences |
| Other stages | Shared table pointer checked for normal zones | Export and validate remaining layouts/objects |

## Useful emulator captures

A debugger trace with original player X/Y, fractional bytes, velocity, state, `$D36C`, `$D369`, `$D522/$D523`, and collision plane would let us compare the entire frame path. The most valuable captures are:

- Walk and run right into the first curve; approach it from the leftward direction too.
- Ride an upright spring through apex and landing.
- Traverse the twist in both directions.

Record the ROM hash and emulator timing mode with any capture. Ordinary video remains useful for visible behavior, but it cannot establish subpixel arithmetic or which branch executed.

## Repository direction

This package is structured for an initial GitHub repository. It includes source, evidence and reproducible commands. No remote repository has been created. Good next research issues are the first three open items above, each with a small address range, a documented hypothesis, and a reproducible comparison.

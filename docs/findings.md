# Findings and corrections — 20 September 2026

## The first curve is more than a shape

The approach uses tile `$22` at world `(352,640)` and tile `$23` at `(384,640)`. Its upper section includes `$1F` at `(384,608)`.

| Tile | Surface flags | Modifier byte offset | Role established here |
|---|---:|---:|---|
| `$22` | `$83` | `$0E` | Approach contour and negative horizontal speed modifier |
| `$23` | `$92` | `$0A` | Curved surface dispatching to ramp behavior `$69B2` |
| `$1F` | `$92` | `$02` | Upper curve with the same ramp behavior dispatch |

The vertical contour is only one part of the definition. Each tile also has a horizontal profile, a surface type, and a speed modifier. Type `$12` (low five bits of `$92`) can request a special rolling or ramp-launch state.

The shared movement fixture starts at `(320,654)` with X speed +4, holds right, applies requested states on the following tick, and follows the camera. It enters state `$1B` at X=386 with X velocity `952/256` and Y velocity `-1428/256`. That is the original `Y = -(X + floor(X/2))` calculation on the fixed-point velocity. See [the trace](../reports/first-ramp-trace.csv).

This fixture does not run the animation/state-script scheduler or the whole game. In particular, it briefly reports a side contact later in the ascent; it is not evidence of a flawless full-game traversal. What it establishes is the exact ramp branch, its inputs and its result.

## Why the prototype stopped

The v13 GameMaker wall resolver asks whether Sonic's whole collision mask intersects a solid mask at any position along the intended horizontal move. It then zeroes horizontal speed. A slope can satisfy that test before the floor resolver moves Sonic up.

The ROM instead uses a centre foot probe and dedicated side probes, reads their separate profiles, projects the player, and dispatches tile behavior in a defined order. Its movement update also moves a grounded player downward by 7 pixels (9 for certain modifiers) before floor projection. This keeps contact with descending contours and permits projection through adjacent tiles.

Our previous floor logic neither implements that order nor the ramp state transition. Adding a larger mask step-up, or simply permitting more overlap, cannot establish equivalent behavior.

## Corrections to earlier assumptions

| Earlier assumption | What the Chaos instructions establish |
|---|---|
| Heights above 32 are invalid | Projection masks with `$3F`; magnitudes up to 63 are meaningful. Bit 6 also carries behavior. |
| A height mask determines wall solidity | Side collision uses the second profile, indexed by Y, plus surface flag bit 7. |
| Ground contact should always zero Y speed | The shared updater forces +7 or +9 before projection while grounded. |
| Only the newly sampled tile matters | `$6F61` branches using **previous** surface byte `$D36C`; `$691A` replaces it afterward. |
| One pixel tile top is enough to handle penetration | `$7056` also consults the tile one row above, using the row-stride field. |
| A spring can use one gravity value for its entire flight | State `$0B` uses +`$18`; at the apex its wrapper requests falling `$0E` and sets Y speed to +1. |
| Upright spring gravity is +`$20` | The recovered dry increment is +`$18/256` per update. Earlier POC notes claiming `$20` were wrong. |
| The twist can share ordinary floor movement | State `$22` chooses per-tile handlers, sets angle/magnitude, converts them to X/Y velocity, and integrates position. |
| Similar Sonic 2 RAM names can be copied directly | Several Chaos fields moved; for example adjusted X is `$D358`, vertical sample `$D368`, and horizontal sample `$D367`. |

## Other useful results

- The exact assembly for 32 recovered regions rebuilds correctly. Source-byte identity does not prove every annotation.
- The collision table has 16 alternate headers selected through object field `+$25`. Side contacts with tiles `$A1/$A2` can switch this field.
- The twist contains two helper entry points that immediately `RET`. Translating the unreachable arithmetic following those entry points would introduce behavior absent from this ROM.
- The supplied 68 sound offsets are verified against the pointer table at file `$090E1`. We have an index, not converted audio.
- The original 53 object records, six platforms, and three loop-path exports remain included and reproducible.

The Windows prototype should next use the recovered rules in original units, checked against these fixtures. [The porting plan](porting.md) gives the order.

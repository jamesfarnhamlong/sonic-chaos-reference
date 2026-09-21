# Player movement and springs

Evidence: recovered `movement_core.asm`, `movement_tables.asm`, `player_state_setters.asm`, `spring_state_updates.asm`, and the differential/flight reports.

## Units and state

X/Y velocity uses signed 8.8 fixed point: `$0100` is +1 pixel per active update. Position keeps eight fractional bits plus a 16-bit integer coordinate. Integration retains subpixels; it does not round the speed to whole pixels each update.

`+$01` is the current state and `+$02` the requested state. The animation/state interpreter applies state changes separately. A faithful port must preserve that distinction. The test movement fixture applies a requested state on the following tick but does not emulate the full interpreter.

| State | Meaning supported by these routines |
|---|---|
| `$01` | Standing |
| `$05` | Walking |
| `$06` | Running |
| `$09` | Rolling |
| `$0A` | Ordinary jump |
| `$0B` | Upright spring ascent |
| `$0E` | Falling |
| `$1B` | Ramp launch |
| `$1C` | Diagonal spring |
| `$22` | Twisting strip |

The [61 state-script pointers](../data/sonic-state-scripts.csv) are decoded, but this table does not claim semantic names for all of them.

## Horizontal motion

`$4141` selects state-indexed input or friction parameters. The tables contain pairs of signed 16-bit increments; current direction and input decide which value is used. Near zero speed the selected increment is doubled. The second header byte supplies a **byte offset**, not an ordinal index, into the surface-modifier table `$459D`.

`$402A` adds velocity + input delta (`$D375`) + surface delta (`$D377`), checks the direction's combined wall-contact bit, applies the original maximum-speed comparisons, and integrates X. The comparisons use high bytes; replacing them with an arbitrary floating-point clamp is not automatically equivalent.

| Example, state `$05` | Original increment |
|---|---:|
| Dry directional input | ±`$10/256` = ±0.0625 |
| No-direction friction pair | +`$14/256`, -`$14/256` |
| Water directional input | ±`$02/256` |
| First approach modifier `$0E` | -`$18/256` = -0.09375 |
| Curve modifier `$0A` | -`$1F/256` = -0.12109375 |

These are table values, not universal rules for all states. The actual no-direction branch selects `$439D` even on the water path. Another table at `$451D` is exported as data, but `$4141` does not select it in the recovered branch. Do not “correct” the original by assuming symmetry.

The standing setter `$45B3` clears airborne/rolling bits, requests state 1, zeros X velocity, and sets maximum X speed to 4. This is the appropriate state relationship to study for idle behavior. An animation-only repair cannot correct stale movement state.

## Vertical motion

`$4097` chooses behavior using state, airborne flag, water flag, and ground contact.

| Airborne state | Dry increment per update | Water increment |
|---|---:|---:|
| Upright spring `$0B` | `$18/256` = 0.09375 | `$0C/256` |
| Ramp launch `$1B` | `$24/256` = 0.140625 | `$12/256` |
| Other ordinary airborne states | `$30/256` = 0.1875 | `$18/256` |

The ordinary downward terminal speed is +7 dry, +4 in water. Ground contact forces +7 before integration, or +9 when modifier `$0A/$0C` is present. Floor projection then corrects Y. Other support/state branches exist and are retained in assembly.

Ordinary jumping at `$45ED` launches at -4.25 dry or -3.25 in water, moves Y up one pixel, sets airborne/rolling, and requests `$0A`.

## Spring launch and the apex transition

The terrain upright spring supplies -7.5 to `$480C`, which requests `$0B`. Its update wrapper `$393B` uses shared movement, checks landing, then checks the sign of vertical speed. At the apex it calls `$463C`: request falling `$0E`, set Y velocity to **+1.0**, and adjust movement flags. Falling subsequently uses the ordinary airborne increment.

An empty-map fixture, starting at Y=800 with -7.5 and no water, executes these original routines:

| Active update | Y | Vertical speed | Requested state |
|---:|---:|---:|---|
| 1 | 792.59375 | -7.40625 | `$0B` |
| 79 | 503.75 | -0.09375 | `$0B` |
| 80 | 503.75 | +1.0 | `$0E` |
| 81 | 504.9375 | +1.1875 | `$0E` |

The rise is **296.25 original pixels** in this controlled fixture. See [the complete trace](../reports/vertical-spring-trace.csv). This measures active routine updates, not verified real-world frame timing. Collision, water, changing states, and object-spring variants can alter gameplay results.

The diagonal terrain spring requests `$1C` and uses the ordinary gravity branch while in that state. Its THZ launch is X=±4, Y=-7; other levels use Y=-5.5 in the recovered contact handler. Its wrapper `$3955` also requests falling at the apex. Horizontal springs request rolling `$09` and update the speed-cap field as well as velocity.

Object type `$26` spring variants are a separate research target; the terrain spring's launch values must not be assigned to them merely because the artwork looks similar.

## The first curve's state transition

At `$69B2`, upward motion returns. With a nonzero previous surface modifier, an eligible rightward moving player with bottom contact requests `$1B` and receives:

```text
new_vy_8_8 = -(vx_8_8 + floor(vx_8_8 / 2))
```

The negative-velocity branch takes the magnitude before forming the launch. Its contact-bit gate differs from the positive branch in the actual instructions; preserve the branch conditions rather than assuming mirror symmetry. The current Python tests explicitly check the eligible positive branch.

With zero previous modifier, a different path merges contact flags and can first apply a ±4 X impulse and request rolling. Tile `$1F` or IDs ≥`$22` select -4; other IDs select +4. The ramp state itself is excluded from one relaunch branch.

This combination of previous modifier, current tile, flags and current state is why treating the curve as an ordinary polygon produced inconsistent results.

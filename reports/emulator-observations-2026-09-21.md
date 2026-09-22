# Turquoise Hill Act 1 emulator observations — 21 September 2026

These observations came from the supplied SMS emulator recordings `spike1.mov`
and `spring 1.mov`, plus the tester's direct comparison of the opening red spring
with Windows POC 14.5. They guide handler recovery; they are not substitutes for
instruction traces.

## Retracting spikes

The lower route contains a spike set that cycles between a nearly hidden state
(only a small tip is visible) and a fully raised state. This is a timed object,
not static spike artwork or an always-active terrain collision.

The 2.87-second, 60 fps recording visibly includes both states and repeated
transitions. It is sufficient to establish the state cycle but not a precise ROM
period because the capture's start phase and emulator scheduler are uncontrolled.

Four parameter-zero type `$1B` object records occur along the lower route:

| ROM record | World position |
| --- | ---: |
| `$706CE` | `(1344,864)` |
| `$706D7` | `(1936,864)` |
| `$706E0` | `(2464,864)` |
| `$706E9` | `(2912,864)` |

Their type, parameters, Y coordinate and distribution make them the leading
candidate placements. This is a testable identification, not yet a confirmed
handler label. Confirm it by recovering the object dispatcher and type `$1B`
update, animation and damage routines.

## Far-right contact spring

The device previously described as a missing orange spring is not displayed as
a permanently extended spring in the original game. In its dormant state it is
flush with or almost hidden in the floor. Stepping on it makes the body extend and
launch Sonic.

This explains why the static level map appeared to omit the spring and why simply
placing always-visible spring artwork in the POC was misleading. It also provides
a stronger interpretation of object `$26`: the non-terrain object owns activation
and animation states as well as an impulse. The weak/nonzero parameter variants
must still be traced separately; this observation does not prove that their `-5.0`
impulse is wrong.

## Opening red terrain spring

Direct ROM comparison indicates that POC 14.5's opening red upright spring reaches
the correct height. Preserve the recovered `-7.5` impulse and spring-flight physics
unless a later numerical trace disproves them.

Visible oddities remain in Sonic's animation during the spring sequence. Treat
those as current/requested-state and animation-script scheduling work: takeoff,
ascent, apex, falling and landing should be compared without retuning trajectory.

## Next trace targets

1. Recover the bank-30 type `$26` object lifecycle, not only its impulse setter.
2. Recover the object dispatcher entry and full handler for type `$1B`.
3. Record the dormant-to-extension frames and re-arm/reset condition of `$26`.
4. Trace Sonic's animation script/state values across a red terrain-spring flight.
5. Only after the handlers are identified, add differential fixtures and port them
   to POC 15.

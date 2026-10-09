# Zone5 ordinary objects — source contracts and controlled results

Unmerged research. `objects-36-39.json` preserves complete state scripts,
source hashes and numeric contracts. 10,718 controlled assertions cover all
256 initializer parameters, both approach directions, sleep combinations,
endpoint/player equality and all countdown bytes. Numeric types remain the
identities; no appearance-based enemy naming is claimed.

`$36` has ten placements: parameters `$0A/$0C/$0E/$12`. Its WORLD range is
canonical origin X through origin X+parameter×16. State1 waits awake and
chooses direction toward Sonic at speed1; state2 accelerates magnitude by
1/16 after moving, stopping at its range edge or player crossing/equality.
State2 has no sleep gate. It flashes frames6/7 with durations8,8,4,4,2,2,1,1,
allocates `$37` at (0,+8), then waits32 and requests1. It never calls the
badnik contact or defeat helper. Preserve canonical origin separately from
runtime position; the range is not viewport-relative.

`$37` has two distinct producers. Command4 parameter0 from `$36` starts
state1,Vy+2.5; surface `$0B` parameter1 starts state3,Vy+4.25, overrides base
to `$7C`, aligns X to cell+15 and Y to cell+24−88 in act2 or −120 otherwise.
State1 applies forced hurt before movement and tests the anchor for solid or
one-way terrain; sleeping requests its dissipating state2 without contact.
State3 moves first and only damages while at/before the saved cellY−24
threshold. State2 uses frames2..5 for six updates each then deletes. No attack
defeat, pickup or reward path is present.

`$38` has seven natural records: six parameter0 and one parameter1. Parameter0
patrols at +0.25 and reverses when the 32 counter underflows (33 calls), with
forced hurt tested before movement. Strict proximity on both axes <32 starts
state2. Its 32 movement calls reverse every three calls, then the 33rd callback
requests3 without moving. State3 allocates `$39` parameters0/1 and converts
itself through `$5F54`; this happens autonomously, independent of attack.
The shared conversion requests the numeric reward at `$27EB` for types<$50
and converts to type `$0F`; do not skip it as an ordinary no-score deletion.

Parameter1 instead repeatedly runs state4, which command4-spawns `$38`
parameter2. The child falls with gravity1/16, then travels left at−0.75,
using anchor blocks `$44/$45/$46` to continue. Other blocks restart the
proximity/countdown branch at +0.25. This is a real allocator dependency;
pool pressure can alter emitted children and cannot be replaced with a
decorative timer. Command4 uses the shared eleven-slot pool and ascending
scheduler behavior, with failure advancing the script.

`$39` starts at velocity(-2,-5.5) for parameter0 or(-1.5,-4) otherwise,
retains originX and alternates state1/state2, reflecting X after the first
pass and adding gravity+0.25 during state1. It uses forced hurt, not attack
defeat. `$9178` compares WORLD Y with cameraY+192, but its state3 request is
overwritten by both callers' unconditional tail requests. `$9173` is a delete
routine that the decoded state scripts do not reference. Do not infer a
functional 192-pixel deletion gate solely from this nearby routine; generic
lifecycle remains relevant.

Reuse candidates are `$09/$10/$18/$26/$28/$2C`. `$28/$05/$8B` enter the shared
state13 contact gate, whose AQZ2 override does not apply to zone5; `$8B` must
not select AQZ state14 here. Existing spring span and enemy parameter contracts
still need explicit zone5 integration checks. No new placements are authored.

Remaining closure: complete natural producer/projectile scheduler traces,
pool exhaustion, scored conversion observation, shared-family zone5 traces,
and surface `$0B` cell mutation/restoration. This checkpoint does not claim
complete A3 acceptance. Art boards for numeric `$36/$38` are provisional;
children and reachable animation frames still need registration checks.

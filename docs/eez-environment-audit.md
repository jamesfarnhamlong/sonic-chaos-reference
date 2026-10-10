# Zone5 environment — controlled contracts and remaining closure

Unmerged research, verified Europe v1.2. `environment-gates.json` records
5,200 assertions; `transport-state21.json` records 44,800 independent model
comparisons against original route handlers. These are supplied-RAM routine
tests, not natural gameplay acceptance.

Surface `$01` is new here: `$6A5D` requires zone5, probed floor block `$0B`,
and zero `$D3F7`, then allocates type `$3A` parameter0 from the 16-slot pool.
It has no separate floor flag test. Exhaustion leaves the pool unchanged.
The latch is set by the allocated object's initializer, not by allocation;
do not silently move it earlier or expand the pool.

`$3A` initializer `$1E:$91A8` sets `$D3F7=$FF`, art bases `$92/$92` and
state1. `$91BA` aligns its WORLD anchor to `(playerX&~7)+3` and
`((playerY+32)&~31)+6`. It alternates frame1/frame0 for two updates each.
`$91DB` clears the latch and deletes when requested player state is `$17`
or the floor-probed block ceases to be `$0B`. This is independent of generic
screen lifetime. The original code is hashed in the machine contract.

Surface `$0E` `$6B56` is a grounded conveyor: floor bit1 gates a one-pixel
negative WORLD X displacement using the full 24-bit coordinate, preserving
the fraction and X velocity. This occurs in the player's terrain pass.
No camera, viewport or player-distance scaling applies.

Surface `$13` `$6D43` has transport entry behavior. `$80` immediately returns.
All other blocks copy the floor marker to `$D36D`, clear floor bit1 and set
player flag3 bit0, even when they do not launch. Current state `$21` inhibits
launch. `$7F` requires nonnegative Vy and launches down at +6.0; `$81` requires
nonnegative Vx and WORLD Y modulo32 <16 and launches right at +6.0; `$82`
requires the same Y band and either current state `$18` or Vx<=0 and launches
left at -6.0. Launch requests `$21`, zeros the other speed, and requests `$A5`.
The apparent `$80` rising branch below the early return is unreachable from
the normal handler entry. Do not implement it as an active fourth launcher.

State `$21` callback `$0C:$916B` runs hurt handling, clears hide, marks camera
control `$D15F` bit1, and tracks current floor block `$D36B` against `$D3C5`.
A changed block clears route latch `$D3C6`. Current `$74..$83` dispatches
through `$91BC` while unlatch­ed; otherwise it uses previous marker `$D36D`.
Leaving both ranges sets `$D373=$0600`, converts rising Vy to -6.5, requests
sound `$BA`, clears hurt/contact request and invokes ordinary state setter
`$47FB`. Current-block latch skips routing but still runs move/terrain tail.

The machine table and `eez_transport.model` define every route. Sweeps cover
all 16 block IDs, all directional button combinations, center boundary values,
both horizontal/vertical directions and positive fractional Vx. Routing checks
the velocity high byte; positive subpixel Vx can follow the nominal zero-X
branch. WORLD X snaps to `(X&~31)+14`; WORLD Y snaps to
`((Y-16)&~31)+44`. Turns set one axis to ±6.0 and zero the other. `$7E` keeps
the existing motion. There is no viewport scaling in these selectors.

Route selectors are isolated before common tail `$91DC`: `$0338` moves,
then `$038C` invokes terrain. Do not replace this with unrestricted airborne
movement or infer tile identities from the drawn pipes. Entry occurs through
ordinary terrain dispatch before the following state update.

Whole-game boot matches all 11,774 layout cells and repeats 48 updates per
act identically using all 65,580 exported CPU-state bytes plus the platform
snapshot. Static terrain VRAM matches all used nonanimated tiles in act1;
animated/ring tiles were explicitly excluded. This bounds the provisional
terrain-board speckles to initial/animated VRAM presentation rather than a
static tile decoder discrepancy. Boards still need proper animation-state
presentation before James approval.

`terrain-effects.json` adds 202 assertions for `$0B`, including all first-free
slots and exhaustion. Floor bit1 gates replacement `$B1->$B2` before allocation.
On exhaustion the replacement still happens and the routine writes the probed
cell coordinates through out-of-pool IY `$D940`. Type `$37` has no restoration
callback; the mutated cell persists until map reload. Do not add restoration.

Effects 5/6/13 pause while boss-active; effect8 does not. The 384-call traces
record every copy/palette write. Effect5 is zone-dependent (64 bytes to `$3020`
every3 calls); effect6 swaps paired96-byte strips every30; effect13 cycles four
96-byte strips to `$3760` every8; effect8 cycles12 palette pairs at indices14/15
every8. Ring animation remains separate. Exact source/destination records are
machine-readable in `terrain-effects.json`.

Remaining A2 closure: transport
full player update/order traces; effect 6/8/13 interpretation and animation
approval. Carrier `$17` is a distinct A4 subsystem, not this tube state `$21`.
No whole-stage closure or POC-ready status is claimed yet.

# Zone5 mapped $17 and player $16/$17

Unmerged research; `carrier-17.json` is the source contract, script tables,
block lists, source hashes and 32,470 controlled assertions.
All five mapped placements use parameter `$02`; canonical records remain
unchanged. This mechanism is separate from terrain transport state `$21`.

`$A741` captures top/side overlap (shared contact bits0/2/3), excluding bottom.
Attack posture is not a capture requirement. Shared hurt suppression applies;
already executing player state `$17` bypasses the helper. Successful capture
stores the actor slot in `$D3A6`, clears player flag3 bits0/1 and requests
player `$16`. Actor state1, initially Vy+1, clears its placement token and
requests its parameter state2 at Vy+4. Awake no-contact motion samples terrain
and saves block `$D36E`; sleeping state1 does nothing.

State2 accelerates positive X by1/16 to the high-byte4 gate and probes
(+16,−16) against the six original obstacle IDs. State3 is the negative-X
counterpart; natural parameter02 does not itself select3. Falling enters
state4 at Vy+1, uses gravity+1/8 with the original rejection ceiling6, and
zeros X on a forward obstacle. Landing on one of the 15 continuation blocks
returns to the parameter state at Vy+4; other floor contact bounces at−4,
zeros X, requests5 and plays `$BB`. If this actor owns `$D3A6`, that bounce
clears ownership and invokes the shared hurt helper. State5 falls with
gravity+1/4 until floor then requests6. State6 frame1 lasts16 updates and
calls `$A72B` to clear token/parameter; subsequent frame0 calls `$0362->$64F5`
to set typeFF and delete. `$64F5` is deletion, not flag clearing.
Scripts and block bytes are cached rather than renamed from appearance.

Player `$16` copies actor WORLD position and velocities through `$4C56`,
sets attack posture and hides the carrier. It uses frame `$5F` for one update,
then requests player `$17`. Facing comes from carrier parameter==2, not Vx.
Player `$17` copies actor state, runs terrain rings, hurt and movement input;
hurt/death requests or action-button bits4/5 detach. Detach unhides the actor,
sets its cooldown16/hurt flag, requests its parameter state, clears owner and
uses the ordinary player setter. The normal terrain pass is not substituted
for this carrier callback. Player-before-objects order means the copied
position precedes the actor's current movement update.

All movement/probe/alignment coordinates are WORLD. Before capture, generic
mapped lifecycle applies; clearing the token on capture matters for later
placement occupancy. No dynamic child allocation or reward path is present.

The original scheduler trace in `system-game-checks.json` observes player16/17,
owner assignment, carrier2/4 continuation, and action-button detach. Bounce
sweeps vary owner, player floor flags and contact side, verifying both carrier
motion and the owning player's shared hurt reaction. Cleanup callbacks are
directly tested separately. Generic mapped lifecycle is reused; captured token
release is explicit. These controlled checks do not claim an input-only route
playthrough or Windows approval.

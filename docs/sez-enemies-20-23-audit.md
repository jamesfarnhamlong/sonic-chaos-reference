# SEZ S4 — enemies `$20` and `$23`

Research baseline: S3 `ed9122b3d5ac11442714ecaef4cc4316c4706342`.
This closes the ROM runtime contract for all 15 mapped enemies. POC implementation
and Windows acceptance remain separate. No POC files or new art boards were made.

Canonical input: Sonic Chaos (Europe) v1.2, 524288 bytes, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
The ROM remains local-only. Evidence is decoded data, source-traced behavior,
controlled execution of original Z80 routines and guarded whole-game fixtures.
The SMS harness is approximate; the fixtures establish update behavior, not
hardware/audio fidelity or human gameplay acceptance.

The importable contract is
[`enemies-20-23-runtime.json`](../data/rom-cache/sez/enemies-20-23-runtime.json).
It contains every raw placement, all creator fields, decoded state/animation
records, helper hashes, callback ordering, contact/defeat rules, lifecycle bands,
boundary vectors, all-block floor vectors and every natural placement's traces.
The generator is `tools/sez_enemies_20_23.py`; its counted checks are stored in
`assertions` and `assertion_total`.

## Placements and initialization

All records are bank `$1C`; all flags are `$00`. World coordinates are stored
coordinates minus `$100` on each axis. Indices and placement tokens are one based;
the natural allocator marks `D400[index-1]` with the type. The controlled creator
uses synthetic occupancy address `$D418` (token 25); whole-game fixtures verify
the actual natural token. Do not import token 25 from the controlled fixture.

| Act | Index | Type | File offset | CPU | World X | World Y | Parameter | Aux0/Aux1 |
|---|---:|---|---|---|---:|---:|---|---|
| SEZ1 |31|$20|$70F0E|$8F0E|1232|142|$01|$A4/$A4|
| SEZ1 |32|$20|$70F17|$8F17|2160|750|$00|$A4/$A4|
| SEZ1 |33|$20|$70F20|$8F20|2864|814|$00|$A4/$A4|
| SEZ1 |34|$20|$70F29|$8F29|3088|110|$00|$A4/$A4|
| SEZ1 |35|$23|$70F32|$8F32|1760|430|$00|$86/$86|
| SEZ1 |36|$23|$70F3B|$8F3B|2112|430|$00|$86/$86|
| SEZ1 |37|$23|$70F44|$8F44|2576|142|$00|$86/$86|
| SEZ1 |38|$23|$70F4D|$8F4D|2800|430|$00|$86/$86|
| SEZ2 |26|$20|$71041|$9041|1616|78|$01|$A4/$A4|
| SEZ2 |27|$20|$7104A|$904A|2608|910|$00|$A4/$A4|
| SEZ2 |28|$20|$71053|$9053|3120|78|$00|$A4/$A4|
| SEZ2 |29|$23|$7105C|$905C|2192|750|$00|$86/$86|
| SEZ2 |30|$23|$71065|$9065|2256|494|$00|$86/$86|
| SEZ2 |31|$23|$7106E|$906E|2704|206|$00|$86/$86|
| SEZ2 |32|$23|$71077|$9077|2704|430|$00|$86/$86|

The original creator starts current/requested state 0, blank frame 0, velocities
and fractions zero and flag `$04` bit 6 set. Aux bytes become art bases `+$08/09`;
parameter goes to `+$3F`. Visible animation records load the collision extents.
No callback reads either enemy's parameter. For `$20`, all 256 parameter values
are replayed for 180 updates at the same natural coordinates, through repeated
terrain-triggered hops; every observed field except the parameter is identical.
Thus natural `$00/$01` differences are terrain/placement differences.

## Type `$20`

State table `$0C:$B0D0`, file `$330D0`; callbacks `$B100/$B119/$B14C`.
The cache decodes all five table entries. State 0's frame-0 record lasts `$E0`,
but its first callback immediately requests state 3. States 1 and 2 are unused
restart-only scripts: no reachable callback requests them; do not enter them.
State 3 alternates frames 1/2 for 10 callbacks each; state 4 uses 4 each.
Both visible scripts set `$04` bit 4; neither clears or changes facing.

Initialization sets X speed `-$0080` (-0.5), Y speed `+$0200` (+2), counter
`+$1E=$80`, and requests state 3. It performs no contact or movement.

Walking callback `$B119`:

1. Return if the prior update's sleep bit 6 is set.
2. Shared overlap `$6328`; any low-nibble contact takes `$5F3D` and returns,
   including a non-attacking overlap that does not defeat the enemy.
3. Decrement counter modulo 256. A result of zero requests state 4 and sets
   Y speed `-$0300` (-3), with no movement or terrain probe that callback.
4. Otherwise probe before moving: anchor `(X-4,Y+10)` for negative X speed,
   `(X+4,Y+10)` for nonnegative X speed. `$7725` supplies the block ID.
   Exact equality with `$47`, `$F6` or `$F7` takes the identical hop branch.
   The three IDs have no distinct enemy effect. An early hop preserves the
   decremented counter until landing resets it.
5. Otherwise integrate both axes through `$60FB`, then object floor `$77CB`.

There is no ledge test or turnaround. Walking continues left with constant +2
Y speed if unsupported. Ordinary ledges never reverse X speed. Counter input 0
wraps to 255; it does not hop immediately. Contact and sleep pause the counter.

Hopping callback `$B14C`: sleep gate, movement, contact, then gravity `+$0020`
(+0.125). Eligible overlap returns before gravity and landing. Only when the
**updated signed** Y speed is nonnegative does `$614E` sample `(X,Y+18)`.
Either block-header bit 6 or 7 requests state 3, resets counter 128 and sets Y
speed +2. This is a flag-only gate, not a collision-profile test. There is no
same-callback floor projection on hop landing; the next walking callback moves
and projects. Integration retains fractional anchor bytes. There is no cap or
special player-distance rule in these callbacks.

## Type `$23`

State table `$0C:$B3D9`, file `$333D9`; callbacks `$B3FD/$B412/$B439`.
State 0 is frame0/224 and immediately requests state 1. `$B3FD` initializes or
relaunches with X speed `-$0100` (-1), Y speed `-$0200` (-2), with no contact or
movement. Natural bit4 stays zero; no callback reverses X or changes orientation.

State 1 is frame1/224, restarting the record without restarting velocities.
`$B412` tests contact **before** movement and returns on eligible overlap even
without defeat. Otherwise it integrates, adds `$0010` (+0.0625) gravity, and tests
the same flag-only `(X,Y+18)` landing gate if updated Y speed is nonnegative.
Landing requests state 2, writes `+$1E=$40` (never subsequently read), and calls
`$77CB` for projection **in that same callback**. No separate landing timer exists.

State 2 has these records, in order:

| Duration | Frame | Callback |
|---:|---:|---|
|12|2|`$B439`: contact only|
|4|1|`$B439`: contact only|
|6|2|`$B439`: contact only|
|224|1|`$B3FD`: requests state1 and sets leap velocities|

There are exactly 22 rest/contact callbacks, then one relaunch callback, then
state 1 on the following engine update. The final 224 duration never becomes
a 224-update rest. Rest does not retest support or move. Neither leap nor rest
checks the sleep bit: `$23` keeps running asleep until generic deletion.

On a flat floor at the natural height, original integration gives 65 moving
callbacks (64 leaves Y two pixels above its starting anchor; 65 returns to it).
The resulting 65+22+1 =88 callback period is an observation derived from the
terrain path, not a hardcoded leap duration. Lower ground can extend the leap.

## Terrain and natural signatures

`$77CB` clears object floor bit1, samples the current block/profile, projects
through `$70E7`, then dispatches the header's low five surface bits. Solid bit7
uses the profile penetration; one-way bit6 requires nonnegative Y speed and
penetration below the high-speed-byte-plus-7 threshold. It preserves velocities.
The exact all-block/all-32-foot-row oracle results are included in the cache.
Surface `$0E` is exceptional: after a successful projection `$7836` adds -256
world X for block `$F0`, +256 otherwise. That is a teleport, not enemy facing or
a one-pixel walking correction. The all-block sweep locks its signed magnitude.
Ordinary surface handlers do not reverse X speed. Flag-only leap/hop landing can
request a state change where the projection profile itself rejects support.

All 15 placements receive 420 original-routine updates on their own act maps,
plus 425 whole-game updates using natural creation and the original scheduler.
Whole-game fixtures clear the initial object pool/occupancy at an update boundary,
then park only player/camera near the moving enemy and out of contact. They do not
edit the enemy or terrain. The cache states these controls alongside each trace.

Neither type collapses to one coordinate-independent 420-update signature:

- `$20`: seven distinct traces. SEZ1 #31 / SEZ2 #26 hop early on trigger blocks;
  other records initially hop at the counter boundary. SEZ1 #34 and SEZ2 #28
  descend from their placement heights; later landing heights/timings vary.
- `$23`: six placements share one relative trace. SEZ2 #31 is different from its
  second leap: controlled landing at update168/Y240, later Y270. SEZ2 #32 shares
  the first four flat cycles but starts descending near the end of the 420-update
  horizon (final Y434 instead of Y430). It forms the third signature.

## Contact, defeat and drawing

There is no special contact helper. Both use `$6328 -> $5F3D`, and the player's
existing `$48BC` on the following player update. **Extents are frame dependent.**

| Type/frame | Object extents X/Y | Normal Sonic closed box, relative to enemy | State `$0F` closed box |
|---|---|---|---|
|$20 frame1 or2|7/20|X -15..15, Y -20..24|X -16..16, Y -20..24|
|$23 frame1|9/26|X -17..17, Y -26..24|X -18..18, Y -26..24|
|$23 frame2|7/20|X -15..15, Y -20..24|X -16..16, Y -20..24|

Frame0 extents are 0/0, but initialization/relaunch callbacks do not test contact.
Minimum penetration chooses the classification; vertical wins a tie. Object
contact masks are `$01` above, `$02` below, `$04` right, `$08` left. `$6328` writes the
placement slot ID to `D520` and corresponding upper-nibble direction to `D521`.

Player `$D503` bit6 suppresses ordinary-enemy overlap entirely. Bit7 blinking
preserves overlap and eligible attack defeat, but suppresses the object touch
marker and player damage/rebound. Bit1 attack posture, or `$D532==6`, defeats on
eligible overlap. Airborne bit0 alone never defeats. The original shared handler's
6144-case priority matrix is regenerated alongside the per-enemy grids.

Next player update: an ordinary attack from above sets Y speed -3, clears floor
and sets airborne; from below sets +0.5 except current state9; side classification
does not rebound. Invincibility selector6 and blink bit7 suppress rebound.
Non-attack contact requests ordinary ring-loss hurt with rings, death without;
the canonical Rocket Shoes exception remains shared. Ring-loss sound is `$A4`,
ordinary death `$96`. Hurt/blink gates precede this choice.

Defeat immediately converts the existing slot to `$0F`, adds the `$27EB` BCD
entry `10 00 00` (+10; score addition is disabled when `D292!=0`), and clears
current/requested state, flags4, duration, script pointer, token and parameter.
All other slot bytes are preserved. `D400[index-1]` remains occupied, so the enemy
cannot recreate on backtracking until the act's occupancy reset.

The same conversion pass preserves the saved mapping/piece pointers and frame:
the renderer briefly draws the last enemy frame with bit4 cleared. For `$20`
this is the unmirrored form already present in the supplied art package. Ordinary
animation remains approved bit4=1; `$23` stays unmirrored. No new graphics or board
was generated. The next object update initializes blank smoke frame0 and art
bases0; the following update's `$03EF->$61D6` queues `$C4` only if `DE04==0`.
Smoke uses frames7/8/9 and reaches `$FF` on the 40th object update after conversion.
Its token remains zero; final cleanup does not release the enemy's occupancy.

## Lifecycle and scheduling

Both use the generic mapped lifecycle; neither sets keepalive bit1 or checks a
player-distance removal threshold. For **both axes**, canonical bands are:
visible `[0,256)`, awake `[-32,288)`, lifetime `[-96,352)` relative to camera.
The vertical lifetime uses 256 despite the shorter drawn screen height.
Steady mapped creation scans once per four updates in the outer creation ring
`[-96,-32)` / `[288,352)`; initial fill includes inner bands.
Outside lifetime, a tracked enemy becomes `$FE`; the next scheduler pass marks
`$FF`, and a later pass clears the slot and releases its occupancy token.
Ordinary recreation repeats the creator/state0 sequence at the canonical anchor.
Whole-game away/return fixtures verify recreation and defeated non-recreation
for both types. Canonical anchors remain world coordinates; bands are **EDGE**
relationships. The accepted POC post-wake horizontal retention adapter may be
used later, but it is not part of this ROM contract. Vertical bands are not widened.

Player engine/callback/terrain/contact precede object scheduling. Each enemy's
engine advances records before its callback; visibility runs after that callback.
Animation progresses asleep for both. `$20` walking/hopping callback timers and
motion pause; `$23`'s cycle progresses. Wake does not reinitialize an existing
object. With natural creation after object pass N: N+1 runs state0 initializer;
N+2 loads the active script. `$20` still sees the creator's sleep bit on N+2 and
first moves/tests contact on N+3 after visibility clears it. `$23` ignores sleep
and first moves/tests contact on N+2. Whole-game vectors lock this difference.

Only `$20` hopping moves before contact. Every other contact callback tests first.
Eligible overlap ends the enemy callback, even if no defeat occurs; gravity,
timer and terrain operations after contact are skipped. Smoke initialization is
deferred to the next object update. Two A/B/A reruns verify snapshot-history
independence using `ZoneGame.restore_snapshot()`'s hidden CPU-state guard.

## Verification and remaining scope

Run `tools/sez_enemies_20_23.py ROM --check`, focused SEZ/shared-enemy tests,
`tests/verify_cache.py ROM` and `git diff --check`. Counts and source hashes in the
cache are authoritative; the report records the executed test totals.

No unresolved runtime dependency remains for these two types. Human-facing
enemy names remain intentionally numeric. POC implementation, transient-conversion
presentation acceptance and Windows gameplay acceptance are downstream work.
Boss `$54/$55`, previously closed platforms/surfaces, monitor repair, slope/facing
presentation and results remain outside S4.

AGENTS candidate update: add this audit/cache to canonical enemy guidance after
Manager review; record `$20` timer/probe hop, `$23` terrain-dependent leap/rest and
frame-dependent extents, shared attack-bit defeat, differing sleep callbacks and
defeat occupancy retention. Do not rewrite the root coordination file here.

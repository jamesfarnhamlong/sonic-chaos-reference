# AQZ A5 — boss $59, children $5A–$5D, arena and clear

Review package on `research/aqz3-boss-59`, based on canonical A4
`c4ec2ee1e1bbf86b38939352691da09859f75c33`. POC files are untouched.

## Provenance and reproduction

Europe v1.2 ROM: 524288 bytes, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
No ROM is committed. `boss-59-runtime.json` contains source file/bank/CPU ranges,
source hashes and normalized tool hashes. State scripts are decoded fresh from
bank $1E; movement/contact vectors execute original routines. The whole-game
cache uses the original loader, scheduler, renderer, player, camera, results and
transition code in the existing approximate SMS harness. This is not a claim of
cycle-perfect hardware or a controller-only human playthrough.

Reproduce from the Research checkout:

```powershell
.venv\Scripts\python.exe tools\aqz59_runtime.py '..\source\Sonic Chaos (Europe).sms' --check
.venv\Scripts\python.exe tools\aqz59_game.py '..\source\Sonic Chaos (Europe).sms' --check
.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_aqz*.py'
.venv\Scripts\python.exe tests\verify_cache.py '..\source\Sonic Chaos (Europe).sms'
git diff --check
```

## Placement, intro, camera

AQZ3 record1, file `$71630`, bank `$1C:$9630`, WORLD `(1856,238)`,
parameter0, token1. Stored/raw coordinates remain in the census. Original mapped
creator preserves the anchor, occupancy and aux/art fields. The original scanner
is swept over 1030 camera-X/fill cases: initial fill includes the visible window;
periodic creation uses the canonical 32..95-pixel outside-edge bands. The boss is
allocated to `$D700` in the natural fixtures.

`$974C` sets keepalive bit4.1 and boss-active `$D44E=5`, allocates `$12`, saves the
camera right limit, requests1 and converts a pending Spring Shoes request to fall.
This occurs before the trigger. State1 requires strict `abs(dx)<96` and
`abs(dy)<304`. State2 waits for its stored HUD slot to become zero. It then installs
camera target `(1728,78)`, upper Y78 and requests3. Pan rate is one pixel per axis
per update; the exclusive X limit settles at `(1727,78)`. Combat initialization
runs while the camera is still moving. There is no camera-arrival gate.

State3 requests graphics selector23/palette16, allocates HUD again, subtracts224
from integer Y (238->14), sets +26=10, counter30=6 and field34=6, clears23/24,
and requests6. The ordinary camera/player edge system remains in use; no new
boss-owned world rectangle is imposed. The saved natural right limit is2304.
Synthetic approach camera writes are explicitly recorded in the whole-game
method; their intermediate left limit is not a new canonical world clamp.

## Complete state graph

Exact record durations, frames, script commands, velocities, callback addresses
and spawns are in `state_graphs`; `contracts.callbacks` specifies callback order,
comparison inclusivity and side effects. All state IDs below are decimal.

| State | Canonical path |
|---|---|
| 0 | Shared intro/music `$8C`; request1 |
| 1 | Strict player-distance trigger ->2 |
| 2 | HUD disappearance -> camera setup ->3 |
| 3 | AQZ combat initialization ->6 |
| 4 | Frame1, RET only; no natural incoming request; **does not clear** |
| 5 | Five `$34/8` puffs, timed blink loops, then floor-gated `$81BD` clear |
| 6 | Spawn `$5A` at `(0,+224)` every64-record restart; six allocations; ->7 |
| 7 | Wait field34==0, then65 eligible decrements ->8 |
| 8 | Solid contact, integrate then gravity+16/256; Y>238 ->9, vx−160/256, vy−6 |
| 9 | Frames2/4 every8; cached-edge stop, integrate then gravity+48/256; contact tail |
| 10 | Set counter30=FF each callback; frames1/3 every4; spawn `$5D(-8,-32)` after8; ->9 |
| 11 | Five `$34/2` puffs; gravity+32/256 before integration; Y>238 ->12 |
| 12 | Contact,47 stationary countdown calls; then97 moves at vy−1; ->13 |
| 13 | Spawn `$5B(0,-32)`, wait fixed `$D724!=0` ->14 |
| 14 | First16 blank/frame6 updates, seven same-pass `$5C` spawns; 17 callback decrements ->18 |
| 15 | Contact, wait child counter30==0 ->19, set counter30=64 |
| 16 | Up to64 contact callbacks; overlap ->5; next zero-counter call ->14 repeat |
| 17 | Frame2/16 calls with contact tail, then face player, vx±160/256, vy−6 ->9 |
| 18 | vx0/vy−1.5,32 updates, set fixed parent field23=FF ->15 |
| 19 | vx0/vy+1.5,32 updates ->16 |
| 20 | Four frame7 callbacks using the state9 movement/contact core ->9 |

States0..3 and5..20 are observed in each complete fight. State4 is an external-only
table entry. A landing return precedes the HP/contact tail: positive integer
WORLD Y>238 and nonnegative updated VY requests17, zeroes velocities and returns.
That can postpone processing a pending defeat marker. The Y helper rejects the
signed-negative half of the word; it is not an unsigned waterline comparison.

## Contact, health and feedback

Boss frames1..5/7 have extents20×64, frames6/8/9 20×48, frame10 20×32;
frame0 is0×0. Engine mapping extents and exact geometry are in the cache.
For the ordinary combat frames, closed overlap is normal Sonic X±28,
Y−64..+24; state `$0F` X±29. Solid projection `$5FA0` runs before response.
The shared helper respects hurt flag `$D503.6`; blinking does not suppress HP.

`$AAB5` first decrements nonzero cooldown31, then projects. `$8105` rebound uses
attack bit `$D503.1` independently of HP cooldown: top VY−4, bottom VY+6,
side VX±6 and negate incoming VY, request `$1B`, preserving floor/flags.
HP additionally requires contact, attack and decremented cooldown0. Selector6
is not a substitute for attack. This distinguishes HP and rebound predicates.

A damaging contact sets cooldown16, requests20, command7 palette flash and sound
`$B6`, and performs **SUB1** on +26. Ten->...->0 survives; **0->255 borrow** sets
angle/marker+10=FF. There are eleven damaging contacts. The final marker is
processed by the next eligible tail into11. A non-final hit request20 can be
overwritten by the tail's strict `PLAYER_DIST(Y)<32` when counter30==0.
Entry/defeat callbacks call `$814D`: attackers rebound; nonattack overlap queues
`$D3B0=FF`. Combat's `$AAB5` has its separate HP/projection path.
Shared hurt/blink/invincibility consumption occurs in the following player phase.
The shared command7 uses the accepted delayed four-call palette flash with AQZ
sprite palette16. No ordinary badnik score conversion is added to the boss.

## Child contracts

All child tables/records/extents and controlled contact/sleep outputs are cached.
They use the same bank-$0F mapping family as `$59`, with approved A1 compositions.

- `$5A` has five states. Init forces WORLD `(2048,238)`, vx−0.5, vy−2,
  keepalive, health1, counter30=2 and clears object03.7. Frames28/29 or26/27
  alternate every7. Gravity+20/256 occurs before integration. Falling Y>238
  resets vy−2; three landings underflow counter2 and reselect direction toward
  the player at vx±0.5. Overlap `$6328` is checked before gravity/movement;
  any qualifying contact saves the requested state and requests3. **Attack is
  not required.** State3 integrates once, returns to the saved state, sets a
  four-call overlap lockout, VY+2 for top or−2 otherwise, flashes/soundsB6 and
  decrements health. The second contact underflows1->0->255, decrements fixed
  `$D734` and requests4. State4 converts to `$0F/0` with no score. There is no
  parent liveness/type lookup and no sleep pause. Multiple children coexist.
- `$5B` has two states, frame11, keepalive and VY−1. It integrates without contact.
  When asleep it marks itselfFF and writes fixed `$D724=FF`; the boss waits for
  this support signal. It is presentation/support, not a contact hazard.
- `$5C` has six states. Init sets keepalive, angle0, magnitude128 and lookup
  velocity. State1 frames14/15 alternate every2; move then forced-hurt `$630B`,
  asleep ->2. State2 waits for fixed `$D723!=0`, then relocates relative to camera,
  loads angle/turn step, recomputes velocity and enters5. Delay counter N is
  decremented N times; the following call requests3. State3 selects frames16..23
  every3 callbacks using angle thresholds88/168 and counter30 parity, moves,
  turns/recomputes every4 callbacks, then forced hurt and Y>238 ->4. Negative
  turn applies while angle>=80, positive while angle<176. State4 decrements
  fixed `$D71E` and converts to `$0F/0`; no parent type/ownership check.
- `$5D` has two states. Init vx−2.25, vy0; strict player-Y distance<32 leaves
  steering0; otherwise player above setsFF, below1. Frames24/25 every2. Awake:
  integrate, forced hurt, then accelerate Y by−8/256 or+8/256 according to the
  retained direction. It does not retarget, use gravity, or consult a parent.
  Asleep marksFF; it has no keepalive initialization.

Child overlap: `$5A` extents4×32, normal X±12/Y−32..+24; `$5C` initial4×32,
curved12×16 (X±20/Y−16..+24); `$5D`4×16 (X±12/Y−16..+24).
State `$0F` adds one to horizontal reach. `$5C/$5D` forced hurt is not attack defeat;
hurt suppression is shared overlap behavior, while invincibility/blink are handled
by the following player phase. `$5A` health decrements in its response state without
retesting attack/selector/hurt. Asleep `$5C` callbacks continue; waiting states have
no contact callback. There is no enemy-water drag or buoyancy.

| $5C parameter | Camera-relative reset | Angle | Step | Delay |
|---|---|---|---|---|
| 0 | (−16,+80) |112|−2|16|
| 1 | (−16,−16) |112|−2|48|
| 2 | (+64,−16) |112|−2|80|
| 3 | (+192,−16) |144|+2|112|
| 4 | (+272,−16) |144|+2|144|
| 5 | (+272,+80) |144|+2|176|
| 6 | (−400,−400) |217|−82|208|

Parameter6 reads adjoining data beyond the six-entry tables: coordinate data
comes from angle pairs and angle/step from the `$5D` state pointer. No correction
or cosmetic simplification is justified. It remains an independently allocated
keepalive child; in all complete fights it survives the parent conversion and
never contributes the seventh completion. The boss counter starts6: completions
0..5 reach zero and release state15. Its historical design intent is unresolved. All seven parameters use the same
contact callbacks; parameter6 is not declared presentation-only because its
normal trace is offscreen.
Velocity is exactly signed sine-table byte ×128 arithmetic-shifted4, VY using
angle+192. All256 angles are original-routine checked; no idealized floating sine.

## Allocation, scheduling, support and clear

Command4 uses `$5EE1`: first zero slot `$D700..D980` (11). Failure sets carry,
skips spawn operands and continues the script, with no retry or guaranteed child.
The command inherits original art fields and creates at integer parent+offset;
child fractional fields start zero. The ascending19-slot scheduler initializes
new later slots in the same update; an earlier slot waits for the next pass.
The shared lifetime map has active bands `[-32,288)`, asleep outer bands
`[-96,-32)`/`[288,352)` and removal outside `[-96,352)`, on both axes.
The Y map is canonically256 tall even though the displayed domain is192 lines;
keepalive exempts removal but does not suppress the asleep bit. See the accepted
`docs/viewport-semantics-audit.md` map decode.
There is no universal ownership cleanup. Fixed parent reads/writes assume `$D700`.
HUD/bonus use `$5E9C`, first zero `$D540..D900` (16); exhaustion leaves IY `$D940`
and `$81A6` still stores it. That failure is preserved, not repaired.

Partial `$5C` allocation is checked with0..10 free slots. Complete-game exhaustion
blocks all6 `$5A` spawns, leaves field34=6 and stalls state7. Missing `$5B` can
leave state13 waiting; fewer than six completing `$5C` children can leave state15
waiting. These are consequences of the actual counter/signal consumers, not a
new fallback. Parent state changes/defeat do not sweep children. Keepalive children
remain allocated even when asleep until their own callbacks convert/delete them.

Both five-puff sequences use offsets `(−8,0),(+8,0),(0,−16),(−8,−24),(−8,−24)`;
the repeated last offset is literal. They spawn one per script record update.
Parameter2/8 is the accepted shared puff cycle counter:3/9 cycles until borrow,
with clock-bit-selected26/50-update scripts and shared jitter. Controlled fixtures
record78/150 and234/450 callbacks from the preinitialized slot fixture; those
counts do not redefine mapped-creator latency. `$12/$34/$0F/$0A` reuse accepted
support routines; source hashes and parameter-specific checks are recorded.

State5's script gives the final five puffs/blink sequence, then `$81BD` runs.
Only floor bit1 gates release; there is no world-X gate. Release restores right
limit2304, sets left to current cameraX, requests player `$20`, allocates `$0A/0`
and converts boss to `$0F/0`, clearing token (no backtrack recreation). Timer
continues. Boss-active `$D44E` remains5 through parent conversion and bonus/results;
shared next-act initialization clears it to0. Existing children and puffs persist until their own lifetime/transition
cleanup. The bonus/sparkle controller and ordinary `$20` beyond-right threshold
converge into results. Three complete fights prove progression to **zone5 act0**.
Original `$4E57` independently proves initial player `(238,864)` and camera
`(126,752)`; first ordinary terrain projection yields Y878.

## Water, viewport and presentation

The source closure and controlled paired vectors find no direct `$D443/$D450` or
raster `$D131/$D132` dependency in the boss/child callbacks. AQZ3 has no A2 water
controller/updater. Shared player hurt/physics may respond indirectly to player
state; do not invent AQZ3 water. Normal restart/transition initialization remains
A2's accepted contract.

WORLD: placement, transformed Y14, positive Y>238 and velocities. PLAYER_DIST:
strict96/304 trigger, strict32 Y tests. LOCKED_CAMERA: settled `(1727,78)`;
target `(1728,78)` retains exclusive-X behavior. CENTER: bossX−128 camera target.
EDGE: previous-render screen-X48/208 at canonical256 pixels, canonical child
screen offsets and generic create/wake/sleep bands. No widescreen design here.
Cached screen bytes remain prior-render values; fresh world-camera subtraction
is not a substitute. Camera updates precede player; player movement/terrain/hurt
precedes the object scheduler; script engine precedes callback; lifecycle follows
callback; renderer then refreshes cached screen bytes. Thus contact results are
consumed by the next player phase and child sleep decisions use prior lifecycle.

A1 already approves every reachable composition: boss0..10, `$5A`0/26..29,
`$5B`0/11, `$5C`0/14..23 and `$5D`0/24/25. Original renderer composition/flips,
priority and palette semantics are reused. No new board, bitmap flip or synthetic
art is needed. Palette16/selector23 dynamic loads are the A1 extraction. Boss-active
pauses effect5; independent effect11 continues per A1/A2, without new water logic.

## Fixtures, limits and AGENTS candidates

Whole-game fixtures include a passive combat cycle, passive-child movement,
four full eleven-contact fights (final hit in states9/10/17, including an extra
floor-wait case), nonattack,
invincibility, hurt and blink controls, and allocator exhaustion. Synthetic player
positions/flags/floor and initial camera writes are labelled; no boss/child code,
placement, HP or script is replaced. Exhaustion temporarily occupies empty slots
at allocator entry and restores them only after the original failure branch.
Replay after all fights/exhaustion restores full exported CPU bytes plus existing
RAM/VDP/harness state, including prefix/EI shadow/frame_tick; no NOP repair.

Natural runtime is closed for implementation review. Remaining limitations:
historical intent of parameter6 adjacent-table reads; real SMS hardware/audio
comparison and human presentation acceptance are not claimed by this harness;
results replacement graphics/audio remain outside scope. No allocator redesign
or POC adapter is included.

AGENTS candidates (do not edit root here): record A1–A4 accepted main and A5 only
after review; `$59` health10 needs eleven contacts because defeat is borrow;
`$5A` any-overlap response needs two contacts; fixed `$D700` child dependencies;
seven `$5C` allocations but six completion gate and parameter6 adjoining-data
behavior; state4 does not clear; floor-only final clear progresses zone5/act0.

Validation: 42 AQZ regression tests and 43 shared boss/support tests passed.
A5 enumerates 124,638 original-routine assertions plus22 whole-game assertions,
19,400 recorded updates and a further3,000-update complete-state replay.
Full `verify_cache` and working/staged `git diff --check` passed.

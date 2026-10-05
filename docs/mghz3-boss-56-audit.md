# MGHZ3 boss `$56`, projectiles `$57/$58`

Original Research base `7ba4d8a7bfb7f8164462fbf50db05c4b63cec0fe`; focused
reconciliation base `badba9d085906054e4f15fa1d1a960ca2ae0abdd`. This package closes
the ROM runtime/data dependency chain for POC implementation after review and
merge. No POC files are changed. The shared monitor fix and parked slope,
spring and facing presentation issues remain separate.

Evidence: **decoded data**, **byte-verified assembly**, **source-traced behavior**,
**controlled routine result**, and **emulated original frame**. Numeric types
are authoritative; “pole-climbing body” and “projectile” describe their visible
composition/runtime, not a newly proven character name. JSON numbers are decimal.

Canonical outputs:

- `data/rom-cache/mghz/boss-56-runtime.json`: all 19 state scripts, exact
  command operands/callbacks, frame/SAT metadata, source hashes, geometry and
  immunity sweeps, creation/camera tests, eight controlled scheduler scenarios,
  projectile tests, defeat gate and palette/sound sources.
- `data/rom-cache/mghz/boss-56-fullgame.json`: eleven actual damaging-hit
  entries, intro, camera, timer, support objects, results and AQZ1 loader marks.
- `data/rom-cache/mghz/boss-56-implementation-manifest.json`: implementation
  contract and explicit coordinate/adaptation classifications.

```powershell
.venv/Scripts/python.exe tools/mghz56_runtime.py '../source/Sonic Chaos (Europe).sms' --check
.venv/Scripts/python.exe tools/mghz56_fullgame.py '../source/Sonic Chaos (Europe).sms' --check --png
.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_mghz56*.py' -v
```

Both tools reject any ROM other than the 524,288-byte Europe v1.2 ROM with
SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
No ROM or graphics/audio dump is committed. PNGs stay under ignored `build/`.

## Placement, creation and intro

MGHZ3 is `3840 × 768`, map stride 120. Record 12 is `$56/$00` at **(3269,288)**,
bank `$1C:$93DB`, file `$713DB`. Stored coordinates are world+256; flags and
both art bases are zero. There is no `$18` goal sign. Neither `$57` nor `$58`
is mapped: they exist only through the scripts below.

The original mapped scanner `$1C:$8000` allocates from `$D700..$D980`, eleven
slots. It checks a two-axis lifecycle band, occupancy and initial-fill mode.
For ordinary rightward approach with screen Y32, steady creation occurs at
screen X **288..351**: `EDGE(RIGHT,+32..+95)`. The corresponding left band is
`-96..-33`. Initial fill also creates inside the awake band. The exhaustive
scanner test executes the real MGHZ3 object list, including its eleven earlier
platform placements; it does not substitute a handmade boss record.

State0 plays boss music `$8C`. Callback `$1E:$974C` (file `$7974C`) sets keep-alive
`+$04` bit1, `$D44E=zone+1=4`, `$D4A5=0`, allocates `$12` HUD slide-away, raises
the left camera limit and saves the old right limit in `+$25/+$27`. It requests
state1. Requested Spring Shoes `$12` becomes fall `$0E` at this initialization;
this is the already recovered footwear dependency, not a new monitor change.

State1 `$9771` keeps the left limit up to the camera and triggers only if
**abs(playerX-bodyX)<160 and abs(playerY-bodyY)<304**. These are strict
`PLAYER_DIST` tests, independent of facing/viewport width. Success lowers the
right camera limit to the current camera and requests state2.

State2 `$97C1` waits for the pointed HUD slot's type byte to clear. Zone row3
at `$1E:$9808` supplies offsets **(-208,-32)**. It sets Y max256, starts the pan
toward **(3061,256)** and requests state3 immediately; it does not wait for
camera arrival. The original pan advances X/Y by 1 px simultaneously. Its
right limit is exclusive, so the settled camera is **(3060,256)**. This is
confirmed in the full-game trace, not inferred solely from the THZ fixture.

State3 `$A576` sets dynamic graphics selector `$16`, sprite palette index15,
allocates another `$12`, sets controller `+$03` bit7, initializes HP byte
`+$26=10` and cooldown `+$38=0`, then requests state `$0B`. Keep the saved
right-limit bytes intact; `$8199` is not called during ordinary combat.

## Exact state tables

All three animation banks are `$1E`. `$56` table is CPU `$A4C4`, file `$7A4C4`;
`$57` table `$A6D7/$7A6D7`; `$58` table `$A78A/$7A78A`. Durations below are
record callback calls, including the first call when the record is installed.

| `$56` state | Script CPU | Behavior / next state |
|---|---|---|
| 00 | 95B1 | Music8C, blank repeating224 record; shared init ->01. |
| 01 | 95BA | Blank224 loop; strict player-distance trigger ->02. |
| 02 | 95C0 | Blank224 loop; HUD gone -> pan setup ->03. |
| 03 | A4DE | Blank224 loop; art/palette/HP init ->0B. |
| 04 | 95CC | Shared five-puff explosion sequence and frame restoration ->05. |
| 05 | 961E | Blank224 loop; MGHZ-specific clear callback81BD. |
| 06 | A4E4 | vx0/vy−1; frames1/2, 8 calls each, three repetitions then one frame2 call; boundary/contact/movement597; next callback5B7 selects08/09. |
| 07 | A4F1 | vx0/vy+1; same frames, two repetitions then one frame2 call; same boundary/contact/movement; selects08/09. |
| 08 | A510 | Spawn57/0 at (−20,−8); vx−2/vy0; frames3/4 two calls each, eight repetitions; one restore-X call, then selector613 ->06/07. |
| 09 | A51C | Spawn57/1 at (−16,−8); otherwise same as08. |
| 0A | A543 | Frames6/5 two calls each, ten repetitions; nonvulnerable contact; selector613 ->06/07. Table state exists, but no request to it was reached/proven in the audited init/combat code. |
| 0B | A558 | Entry vx/vy0, soundAD; frames6/5 two calls each; integrate, nonvulnerable contact, gravity+24/256, floor gate ->0C with soundB9. |
| 0C | A56D | Frame6 for16 calls, nonvulnerable contact ->06. Velocity is not integrated here. |

Callback `$A597` tests the rise/fall bounds **before** contact/movement. Rising
vy<0 with worldY<288 requests0B immediately, bypassing contact that call.
Non-rising vy>=0 with worldY>=430 requests06 immediately, also bypassing
contact. Otherwise it integrates the 24-bit position then calls vulnerable
contact `$A62D` with A=FF. It does not clamp Y to 288/430: canonical overshoot
is visible in the trajectories. Gravity in0B has no terminal cap and is not
underwater-scaled. The post-gravity world430 test selects0C.

`$A5FD` selects 08/09 from `(D12F + ROM[$0200+D12F]) & 1`; all 256 counter
values are in the cache. This is deterministic engine-counter/ROM-table input,
not a fresh random choice. `$A613` selects06 if unsigned playerY<bodyY, or
if body vy>=0 AND body worldY==430; otherwise07. It tests the helper's **Z
flag**, not its A-return value. Thus rising bodies and non-rising bodies at429
or431 select07 when playerY>=bodyY. In08/09, contact precedes
movement and X velocity is negated every call, giving the small −2/+2 wobble.
The one-call `$A5C9` tail restores **saved canonical X3269**, then contact runs.

| `$57` state | Script CPU | Behavior |
|---|---|---|
| 00 | A6DF | Blank224 record, A724 requests01 and sets +04 bit0. |
| 01 | A6E5 | Frames14/13, four calls each, three repetitions (24 calls); A77F CALL0434 contact on every call, RET at A782. Then A72D selects02 for parameter0 or03 otherwise. |
| 02 | A6FA | SoundBE; frames11/12 alternate four calls each; integrate/contact/removal A761. vx−2, vy0. |
| 03 | A709 | Spawn58 params0 and1 at own anchor; soundBE; frame15 repeated224, A761. vx−2.125, vy0; launch first subtracts8 from Y. |

| `$58` state | Script CPU | Behavior |
|---|---|---|
| 00 | A78E | Blank224 record; A79A sets vx−2.125, vy−0.4375 (param0) or +0.4375 (nonzero), requests01. |
| 01 | A794 | Frame15 repeated224; same A761 movement/contact/removal. |

Projectiles have no gravity or terrain bounce. The 24-call `$57` warning phase
is stationary but damaging on overlap throughout. The downward/upward `$58` pair and the parent `$57`
continue independently; the central projectile remains after the split.

## Scheduling, ownership and removal

The real scheduler `$5DD1` traverses **19 slots in ascending address order**,
`$D540..$D9C0`. Each visit runs animation commands, callback, then lifecycle.
Player/terrain movement precedes the object scheduler in the whole-game trace.
Requested states normally promote on the next visit; script transitions can
install a successor immediately while commands are consumed in that visit.

Script command4 uses `$5EE1`, the eleven-slot `$D700..$D980` pool. It copies
parent anchor+signed offsets, saved X/Y, art bases and only mirror bit4 into
the child. There is **no boss ownership pointer** on `$57/$58`. A later-address
child is visited in the creation update; an earlier reused slot waits until
the next update. Command4 skips all six operands when the pool is full; it
does not block/retry the parent script. Controlled traces lock both same-update
init and split timing; an exhausted-pool fixture locks the skip behavior.

HUD/bonus calls instead use the sixteen-slot allocator `$5E9C`. Controller
`+$34/+$35` owns the HUD pointer, not a projectile link. Do not collapse these
two allocator pools into a parent-first recursive update.

`$A761` checks **previous lifecycle sleep bit6 before moving**. If asleep it
converts to `$0F`. Otherwise it moves, then on even `D12F` converts when
**screen-X low byte<176 AND screen-Y low byte>=120**. Odd calls bypass that
early screen test. Remaining calls use `$0434->$630B->$6328` and queue damage
on any overlap. Generic `$61E1` updates sleep/deletion after the callback.
Outside the outer lifetime band an untracked projectile can be markedFF before
it gets a following conversion call. It does not inherit mapped-enemy retention.

Conversion `$033E->$5F54` clears type/state tracking into smoke `$0F`; `$5F77`
skips ordinary enemy score for every type>=50, so **no +10 score is awarded**
for these projectile conversions or the boss conversion. Parent defeat does
not directly kill extant projectiles. Do not invent cleanup ownership.

## Body and projectile contact

Body frames1..6 have object extents **16 × 48**. Normal Sonic8 ×24 therefore
contacts on closed intervals **dx−24..+24, dy−48..+24**. State0F Sonic has X
extent9, giving dx±25. `$6328` chooses minimum penetration, vertical winning
ties; above bit0, below bit1, right bit2, left bit3. The body's contact routine
always uses **solid projection `$034D->$5FA0` before the attack branch**.

This directly depends on complete `$5FA0`: terrain side bits `$D523` guard
each projection; horizontal pushes also respect camera+32/camera+224. Top
projection writes playerY=bodyY−48 unless blocked by terrain top-contact bit;
below writes bodyY+24 unless blocked. Collision uses the canonical anchor,
never SAT registration. The package executes 192 guarded projection cases.
POC must use these rules for the boss; no shared monitor implementation is
changed in this Research package.

After projection:

1. **Below-classified contact with player floor bit1 set calls `$0425->$4984`**,
   the player death setup, before attack handling. It sets D293 bit2 and writes
   sound96 in ordinary levels. Attack handling can subsequently overwrite the
   requested player state/velocity; the death flag remains. This is not normal
   recoverable ring-loss damage and is not suppressed by invincibility here.
2. In vulnerable calls A=FF, player **D503 bit1** is the only attack predicate.
   Non-attacker queues D3B0=FF. Attacker receives `$8105` response and soundB6.
   Only **above/top bit0** can then decrement HP, and only when cooldown is0
   after its decrement. A hit sets cooldown8 and queues palette command7.
3. In nonvulnerable calls A=0, attacker still receives `$8105`, but no HP
   decrement/flash/B6; non-attacker still queues hurt. States0..5 have no body
   contact callback. State0B/0C/0A are nonvulnerable.

The body sets object +03 bit7; overlap deliberately bypasses the ordinary
player hurt-bit6 early exit. Neither D532 selector6 nor D3B1 blinking is an
alternate boss attack predicate. Boss contact/HP decrement can still execute
for attacking hurt/blinking Sonic. Shared pending-hurt consumption is separate
and retains its own immunity/ring-loss rules.

`$8105` requests player1B and normally preserves movement/floor flags: above
vy−4; below vy+6; left vx−6 and negate incoming vy; right vx+6 and negate vy.
Top/below preserve incoming vx. It does **not** request the THZ top-bounce0B
or clear attack/floor itself. The preliminary grounded-below death setup is
the exception to flag preservation. Rising attacks are not filtered out here.

HP starts10. Subtraction tests **carry/underflow**, not zero: **11 damaging
hits**, bytes10→9→…→0→FF. HP0 remains alive. The eleventh requests boss04;
other hits leave the current combat state/script intact. Cooldown decrements
on every `$A62D` call, including no overlap/nonvulnerable calls; it does not
disable projection, hurt, rebound or sound. Repeated top contact hits on calls
0,8,16,24. Boundary branches that skip `$A62D` also skip this decrement.

Projectiles use the same closed overlap but **no solid projection** and no
attack/defeat branch. Frame11 extents12×16 gives normal Sonic dx±20; frame12
8×16 gives dx±16; frames13/14/15 4×16 give dx±12. All use dy−16..+24.
Frames13/14 are active warning-phase hazard boxes on all24 callback calls.
Their ordinary +03 bit7 is clear: hurt-bit6 skips contact, while attack posture
cannot defeat them. Selector6 immunity belongs to the subsequent player hurt
consumer. Exhaustive child geometry/attack/hurt/bit7 sweeps lock this distinction.

## Defeat, effects, clear and progression

State04 is shared script `$95CC`, five `$34/$04` puffs at body-relative
(-8,0), (+8,0), (0,-16), (-8,-24), (-8,-24). The `$9A1E/$9A29/$9A2F`
calls preserve/restore the body's previous frame while explosions animate.
The repeated frame restoration tail is **24 × 6 calls** (2-call record with
timer overridden to4); controlled sequence reaches05 on zero-based tick148
(the 149th scheduler visit). Do not
replace it with a fixed generic smoke lifetime or a THZ hit-reaction state.

`$34` uses art base `$6E` for zone3 (table `$1E:$8C98`), exactly the shared
12 explosion tiles loaded by selector16. It selects states1/2 from D12F parity
and requests soundC4. Shared support scripts/mappings and code hashes are in
the runtime cache and the earlier THZ support audit.

MGHZ branch `$1E:$81F4..$8210` of the state05 callback:

- disables camera pan, restores the saved right limit (3584 for MGHZ3);
- waits for **WORLD(playerX)>=3356 ($0D1C) AND floor bit1**;
- calls4892 to request player20;
- allocates `$0A/$00` bonus/sparkle controller;
- writes boss parameter80/token0 and converts the controller to `$0F`.

Unlike the other shared boss branch it does not first re-lock camera-left to
the current camera and does not hand off on floor alone. At256, world3356 is
already beyond settled-camera3060 +289, so player20 can reach the clear flag
on its first handler visit. The emulated trace does precisely that; do not
require a long auto-run as a fidelity criterion. At wider widths the existing
explicit RIGHT+33 adapter can produce a longer shared auto-run.

### Original post-defeat camera baseline

`$81F4 CALL $035C` reaches `$59D8`: set D15E bit7, clear D15F bit0.
`$81FD` restores D282 from the split saved-right bytes +25/+27 (3584).
It leaves **D280 unchanged**, retaining the intro's left-lock result, rather
than assigning a new fixed arena-left coordinate. Main replay retains2954;
the separate delayed-clear fixture retains2947. These are trace inputs/results,
not two competing immutable arena constants. The saved right limit is WORLD
3584 (act width3840 minus canonical viewport256), exclusive.

The shared camera entry `$4C90` resumes `$5832` with pan disabled. `$16B8`
runs camera first (`$16CA`), then player (`$16CD`), then objects (`$16D0`).
Consequently release in the state05 object callback affects the **next camera
update**. Release precedes the WORLD3356+floor clear test; follow resumes while
the gate is false. Same-visit script promotion can enter05 and release/clear
before an external driver has ever observed state05 at an update boundary.

The working horizontal lead D28A slews1/update toward104 facing right or136
facing left. These are viewport offsets (at256, CENTER−24 / CENTER+8);
their intended wider-view relationship is not proven. Pan mode uses120, but
after release the working lead is retained and slews toward the facing target.
Define `k=(playerX-D284)&255`, using the pre-follow candidate camera. An exact
16-bit zero difference bypasses the horizontal branch. Otherwise:

- `k < lead-8`: delta = k−(lead−8); retain −1..−8, cap −9 or lower to−7.
- `lead-8 <= k <= lead+8`: delta0 (the upper comparison computes0).
- `k > lead+8`: delta = min(7,k−(lead+8)).

The new candidate is **actual camera D174 + delta**. There is no player-speed
read or speed cap. Left movement is possible: even with stationary Sonic,
position error can cause ±7; exactly−8 is preserved by the `$F8` comparison.
The 8px dead-zone, step caps and1px lead slew are motion constants, independent
of viewport width. `$4CB0` accepts left candidate >=D280 and right candidate
<D282; an overshoot rejects the entire move rather than snapping to a limit.
The VBlank handler commits D284/D286 to D174/D176.

SMS low-byte wrapping also matters: the main synthetic clear replay reaches
player3368 with camera3060, difference308, low byte52. The next follow candidate
is3053 (−7), before the shared state20 clear path completes. This is original
controlled behavior, not a reason to reproduce wrapping in widescreen. The
additional full-game delayed-clear fixture proves right and left7px movements
before the clear gate, with the retained left and restored right limits.
An explicit smooth, right-only, 4px/player-speed-limited widescreen adapter
remains a valid downstream design choice; it does not match this256px baseline.

### Reconciliation oracles and replay reconstruction

`tools/mghz56_reconciliation.py` byte-verifies bank1E CPU A77F/file7A77F as
`CD 34 04 C9`: CALL0434 then RET atA782. Vector0434 reaches630B, which calls
6328 and sets D3B0=FF for any low-nibble overlap. Both warning frames are4×16;
normal Sonic8×24 gives closed dx−12..12 and dy−16..24 (state0F extent9 gives
dx−13..13). No projection, movement, attack defeat, rebound or HP branch runs.
Attack posture does not protect Sonic. With the child bit7 clear, player hurt
bit6 skips overlap; bit7 invulnerability still permits the queued request,
but player48BC handles immunity, as it also does for D532==6. Ordinary47 BCD
rings become0; invulnerable/hurt/power6 fixtures retain47. These fixtures run
the actual scheduler for all24 warning calls for both parameters and all
attack/hurt/invulnerability/power combinations, plus exhaustive frame13/14
geometry. Player damage is consumed on the next player phase in the real game;
the isolated fixture invokes that same consumer explicitly after sampling.

AtA61D, SBC playerY−bodyY produces carry. LD B,6 preserves it; JR C bypasses
the helper. Otherwise A69F's BIT7(vy high) produces Z=0 for rising velocity and
RET NZ preserves that flag. Non-rising velocity reaches SBC bodyY−430, producing
Z=1 **only at equality**. LD A,0/FF and RET C preserve Z. A626's JR Z keeps06;
otherwise INC B produces07. The old A-return threshold remains valid for the
other callbacks that explicitly test A, but was wrong for this selector.
The oracle exhausts all65536 player Y values for each body429/430/431 and
vy−1/0/+1:589824 selector executions, including both sides and equality.

The full-game format2 cache records D12F at each boundary and phase, pre-driver
player state, after-camera, **after-player-before-objects**, after-objects,
warning-contact and post-helper flags, and release events. Boundary `player`
still deliberately describes synthetic driver input. It is not physics-settled
Y. For the main fixture's written430, measured settled Y includes398,430,437;
the usual platform-resting value is398. The delayed release's X3260 rests414.
Do not replace exact terrain results by a generic384..412 parked-Y assumption.

`D12F=(frame+96)&255` can be an explicitly fitted driver reconstruction only
when validated against counter values at the same execution phase. It is not
a ROM formula: IRQ0606 increments D12F;075A resets it during setup; harness
frame counts continue through setup/results. The current main trace has
boundary offsets188/237/252/253, not a single96. Extra breakpoint sampling in
the approximate IRQ harness can alter interrupt alignment (old cache543 rows,
new main546). A reported14/256 successful offsets establishes only that those
synthetic fixtures reach the fight, not that they reproduce canonical timing.
Likewise a384..412 parked-Y choice may avoid hazards for a synthetic fixture,
but is not reconstruction of the logged input430 or a universal ROM position.
Use phase-recorded values to remove both guesses. Exact controller-only timing
and original-game visual acceptance remain outside this synthetic replay.

Type0A initializes the shared time/ring bonus at D2A6, follows the player and
emits parameterFF sparkles at Y−12/Y−8 every8 calls. The parent80 smoke uses
shared0F behavior; parent/expired-projectile smoke and sparkles have existing
canonical mappings. Boss defeat **never stops D2BE**, and the timer advances
through the fight/explosions. Results code performs its normal timer reset.

The full-game trace executes 11 original A681 hit entries, actual explosions,
world/floor clear gate, D293 bit4, `$32F9` results, `$2D55/$2D08` tally, `$15CE`
zone advance and `$15DE` load request for **zone4 / act0 (AQZ1)**. Rings are
BCD, and the shared results/tally sound requests remain the existing path.

## Art, palette, sound and 256-pixel presentation

All three types share mapping **bank0F:$9861, file$3D861**. Exact per-frame
pointer/file, ten body SAT pieces, child pieces, tile offsets, extents and
composition hashes are committed as decoded metadata. Runtime frames are
**0..6 and11..15**; frames7..10 exist in the mapping but are not consumed by
these reachable scripts. Body frames1..6: ten 8×16 pieces, top pair atY−48,
four atY−32, four atY−16. `$57` frame11 has three pieces,12 two; warning13/14
and central/diagonal15 one each. No whole-bitmap mirror is applied.

Selector16 list `$7C05` loads 64 tiles to base46/VRAM `$05C0` from bank05:$B680,
file$17680, and12 shared explosion tiles to base110/VRAM `$0DC0` from
bank09:$ABA0, file$26BA0. Both source hashes are regenerated. Both placement
art bases are0. Sprite palette15 CRAM data and its provenance are in the cache.
Command7 writes palette sprite entries13/14 (CRAM29/30) white3F on its fourth
command call, restores **2A/15** on call8, then clears itself. This is the MGHZ
palette restoration, not the THZ colors35/20.

Numeric requests: boss music8C; fall entryAD; landingB9; projectile launchBE;
attack contactB6; grounded-below death96; puffC4; shared clear97; tallyB4.
Their sound pointer/file/header metadata is in `feedback.sound_sources`.
No unsupported sound names or substitute recordings are introduced.

Every reachable nonblank frame is bit-for-bit composition-hash identical to
the **James-approved 2026-10-04 foundation** board, including child frames11..15.
No new visual composition requires approval. Regenerated original 256×192
frames are local diagnostics in `build/mghz56-review/`; the existing approved
board is `build/mghz-approval/type-56-approval.png`. SAT metadata remains
separate from the existing +(1,18) terrain-relative presentation adapter.

`tools/mghz56_review.py` renders a compact recap board from the existing ignored
foundation preview input and these original-game PNGs (use a Pillow-enabled
Python). Every input frame hash is checked against its recorded approval;
output is `build/mghz56-review/boss-56-review-board.png`.

## Widescreen classification and candidates

The manifest records each source and adapter candidate. Preserve all WORLD
anchors, rise/fall Y288/430, clearX3356 and PLAYER_DIST160/304. Keep the
**LOCKED_CAMERA3060/256** baseline. The pan table places the nominal boss at
screen208 (settled209 due to exclusivity); expressing208 as RIGHT−48 or
CENTER+80 is arithmetic, not proof of authorial screen-edge/centre intent.
Optional arena reframing requires explicit design/Windows comparison and must
not move the canonical pole/placement/collision.

Player edge clamp LEFT+16/RIGHT−9 and side-projection guards LEFT+32/RIGHT−32
are actual viewport relationships. Adapt them without SMS low-byte wrapping.
Generic creation/lifetime bands remain edge-relative. The transient child
early-removal gate is raw screen-X<176, paired with raw screen-Y>=120 on even
calls; RIGHT−80 is an explicit horizontal widening candidate. Preserve its
vertical top+120 relationship and do not casually reuse mapped-enemy retention.
There is no proven separate centre-relative mechanic in this package.

The shared player20 RIGHT+33 completion and RIGHT−7 camera freeze use the
existing explicit widescreen adapter. A later POC implementation must report
its chosen arena/projectile behavior and first validate width256 equivalence.

## Verification limits and remaining work

Runtime generator: **894,975 counted oracle/model assertions**, plus static
art/source assertions. Whole-game fixtures: eight counted assertions, 546 main
update-boundary rows and11 original hit entries, deterministic regeneration.
The separate delayed-clear replay verifies bidirectional camera follow before
the gate. The37 boss regression tests and159-test MGHZ suite pass; see
`reports/mghz3-boss-56-reconciliation.md` for the focused change report.
Independent attacks are synthetic, applied at1336 before full updates; no
combat/camera/results routine is patched. The routine-only Oracle supplies
D135=1 when a real death routine waits for IRQ synchronization. Whole-game
VDP/IRQ emulation is approximate; its images/traces do not replace James's
Windows acceptance or a controller-only original-game comparison.

No active ROM runtime dependency is left open. State0A's unused table entry is
retained without inventing an external trigger. Optional widescreen framing,
Windows gameplay acceptance and the already deferred shared POC results
graphics/audio remain downstream work. No global monitor/contact or parked
presentation fixes are included.

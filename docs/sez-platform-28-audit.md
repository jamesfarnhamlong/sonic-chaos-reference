# SEZ S3 — type $28 parameters $86 and $04

Research branch: `research/sez-platform-28`, based on canonical
`6e169d78f0918c74db4f12d89e410dc50423e3e8`. Research only; no POC files modified.
ROM: Sonic Chaos (Europe) v1.2, 524,288 bytes, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.

The runtime is closed for implementation. `$86` makes a contact-started rightward
excursion and returns, then waits for another contact. `$04` is a stationary
state-5 platform with weight sag disabled. The previously named “axis flag”
`+$25` enables sag; it does **not** swap the movement axis in either audited state.
The new cache supersedes platform reconnaissance in the SEZ foundation.

Machine contract and executable oracle vectors:
[`data/rom-cache/sez/platform-28-runtime.json`](../data/rom-cache/sez/platform-28-runtime.json).
Generator: [`tools/sez_platform_28.py`](../tools/sez_platform_28.py).
Tests: [`tests/test_sez_platform_28.py`](../tests/test_sez_platform_28.py).

## Placements and initialization

All coordinates below are canonical world anchors, decoded from the original
records as stored coordinate minus 256. All records have flags `$00`, aux0 `$6A`.
No coordinates or approved art were changed.

| Act / record (1-based) | File / bank:CPU | Parameter | Anchor | Aux1 | Role |
|---|---|---|---|---|---|
| SEZ1 #1 | `$70E00` / `$1C:$8E00` | `$83` | (784,384) | `$6A` | accepted control |
| SEZ1 #2 | `$70E09` / `$1C:$8E09` | `$04` | (1264,320) | `$6A` | fixed state5 |
| SEZ1 #3 | `$70E12` / `$1C:$8E12` | `$83` | (1904,896) | `$6A` | accepted control |
| SEZ1 #4 | `$70E1B` / `$1C:$8E1B` | `$86` | (1584,96) | `$18` | 384 px excursion |
| SEZ1 #5 | `$70E24` / `$1C:$8E24` | `$86` | (2128,576) | `$30` | 768 px excursion |
| SEZ2 #1 | `$70F60` / `$1C:$8F60` | `$84` | (1488,320) | `$6A` | accepted sag control |
| SEZ2 #2 | `$70F69` / `$1C:$8F69` | `$86` | (1776,960) | `$1C` | 448 px excursion |

DECODED DATA + CONTROLLED ROUTINE RESULT: creator `$1C:$80EB` / file `$700EB`
copies position into live X/Y and origin words `+$3A/3B`, `+$3C/3D`, parameter
into `+$3F`, aux bases into `+$08/09`, and an occupancy token into `+$3E`.
The cache records the full 64-byte **RAM fields**, immediately after creator,
after initializer, and after state-script entry; these are not ROM dumps.

Initializer `$1E:$8585` / file `$78585`:

- Sets object `+$03` bit7, allowing shared overlap despite the player's contact
  bit6 gate. Extents are 16×16.
- Requests `(p & $3F)+1`, except `(p & $7F)` 5/11 requests state13; stores the
  unmodified `(p & $3F)+1` in `+$36`.
- `+$25=$FF` iff parameter bit7; `+$26=$FF` iff bit6 (clear for all four SEZ values).
- Copies aux1 to `+$34` (reload) and `+$37` (remaining 16-call blocks), sets
  `+$30=16`, records the shared object owner ID in `+$32`.
- Zeros latch `+$31`, sag count `+$35`, sag-return flag `+$33`, carry deltas
  `+$23/24` and `+$38/39`, scratch `+$1E/1F/27`.

| Parameter | Requested state / callback | Initial X/Y speeds | Additional script initialization |
|---|---|---|---|
| `$83` | 4 / `$8719` | 0,0 | `+$1E=80`; accepted delay/fall control |
| `$84` | 5 / `$879A` | 0,0 | weight sag enabled |
| `$04` | 5 / `$879A` | 0,0 | weight sag disabled |
| `$86` | 7 / `$87E2` | +1,0 | sets `+$04` bit1 keepalive, frame1 |

The pre-existing exhaustive creator sweep still passes for all 56 parameters
whose selected state is inside the 15-state table; 200 are outside the table.
The dedicated traces park the player inside keepalive range before state entry.
The old generic controlled ObjectLab initially parked Sonic outside that range,
so it could mark a freshly initialized `$86` slot `$FE`; the new controlled lab
explicitly normalizes type/active flags, and the separate creator traces retain
the original field values. Whole-game fixtures use natural creation without that
normalization.

## State 7: trigger, motion, bounds and restart

BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT:

```text
$31=0: $8908 -> $033B/$6328 -> if (+$21 & 15)==0 return -> latch1
latch1/2: $8908 -> $8662 {move -> delta -> support/sag/carry -> counter/reverse}
after $8662: negative X speed -> latch2
            nonnegative speed: latch1 stays1; latch2 becomes0
```

`$87E2` is bank `$1E`, file `$787E2`. `$8662` is the existing horizontal mover
with reversal counter; `$0437` dispatches to fixed-ROM `$62F7`, which negates X
velocity. No acceleration, deceleration, terrain sampling, platform projection
against terrain, sound call, facing change or new frame is present. Frame1 stays
in use across state-script record reloads. The approved SEZ board already covers it.

Trigger is **any classified overlap**, not just top support: against ordinary
Sonic it is the closed rectangle `abs(dx)<=24`, `-16<=dy<=24`, measured before
movement. Side and underside contact start it too. State `$0F`'s player extent9
makes horizontal reach25 through the same shared overlap helper. Rising speed,
attack posture, floor flag, player state and a different support owner do not
block this initial trigger. A rising Sonic can start motion without being carried.

On the trigger callback the platform moves right **immediately**, then tests
support against the new X coordinate. This distinguishes the pre-move trigger
from the post-move support triangle, including the one-pixel boundary strip.
The sweeps cover both inclusivity and classification ties.

Each moving callback decrements `+$30`; zero reloads16 and decrements `+$37`.
Zero `+$37` reloads aux1 and negates X velocity **after that update's movement
and carry**. For `N=16*aux1` and first-motion update `T`:

- `T .. T+N-1`: move right1; final anchor `originX+N`, speed becomes−1, latch2.
- `T+N .. T+2N-1`: move left1; final anchor `originX`, speed becomes+1, latch0.
- Next callback with no overlap: stationary, counters unchanged.
- Next callback with overlap: starts another excursion immediately. A continuous
  rider can therefore restart without jumping off or waiting for a cooldown.

The three natural ranges are inclusive `(1584..1968)`, `(2128..2896)` and
`(1776..2224)`. This is **counter-derived travel**, not a coordinate clamp:
the callback never reads saved origin X to enforce a boundary. Moving the live
X synthetically shifts the timed path. Aux1=0 wraps to 256 blocks/4096 updates
per leg (unused by SEZ); reversal-boundary sweeps cover all 256 aux bytes.

Leaving the platform, jumping off, or losing top support after trigger does not
pause, reverse or cancel the excursion. Recontact during motion applies normal
support; it does not reset the counters. Y velocity remains zero. The sag
mechanism alone can move Y by 0..8 pixels relative to the original Y.

## State 5: $04 versus $84

At identical coordinates and aux values 0/$18/$1C/$30/$6A/$FF, both variants
run `$879A` and the same speed gate/owner/top-support/carry code. `$04` does
not move. `$84` enables `$88FB` weight sag:

```text
supported offsets: 1 2 3 4 5 6 7 8 8 7 6 5 4 3 2 1 0, then holds at0
```

Releasing support resets the return selector and rises one pixel per callback
until sag count0. Aux1 is copied into reversal fields during initialization but
the state-5 callback never calls the reversal counter. There is no orthogonal
velocity, travel bound, oscillator or axis-dependent collision box. Bit6 sleep
returns before all contact, sag and release work; wake resumes retained sag
fields, and true recreation resets them. The natural SEZ1 `$04` placement and
SEZ2 `$84` control were both checked in the whole original game.

## Support, carry and player scheduling

Both use the established `$28` top-only support contract. The effective ordinary
triangle is `dy=-16..-1`, inclusive, `abs(dx)<=8+abs(dy)`. Vertical ties win.
Owner `$D3C0` must be zero or this object's ID. Shared `$8866` is signed
`platformVy<=playerVy`; the horizontal state-7 path directly checks playerVy's
sign because its platformVy is zero. Fractional and both-negative cases are
included in the 6,417-case accepted helper sweep.

State7 moves, computes integer X delta, tests geometry, sags, then carries.
State5 tests before sag. Carry sets player Y to post-sag `platformY-14`, adds
the integer X delta (including −1 on the final return callback), and preserves
both player velocities. Sag is the same bit7-enabled cycle in `$86` as `$84`.
No Y-delta addition is needed: carry snaps to platform Y every callback.

The original loop updates camera, then player/terrain, then objects in slot
order, then the periodic placement scan. The cache has event sequences from
all five natural state5/7 placements. Contact writes `$D521`, which becomes
merged `$D523` support on the next player pass; support itself does not set the
terrain floor flag `$D522` or replace player state/movement flags. Jumping in
the player pass causes negative Y speed, so the same update's platform phase
releases support through `$8843`, while excursion motion continues.

Side contact can start state7 but never gives support; shared release clears
mirrored side bits. Underside contact does not create a solid ceiling projection.
The state/attack/floor/owner matrix covers all 52 player states, including roll,
jump, fall, Spring Shoes `$12`, Rocket Shoes `$11`. The platform helper has no
footwear state or `$D532` selector: its geometry/speed gate is unchanged, and
it does not detach or replace shoes. The footwear/player routines can supply
different velocity/flags; this audit does not redefine those global mechanics.

## Lifecycle and viewport classification

State7's script enables keepalive **before any trigger**. Generic lifetime
deletion is consequently disabled from state entry, while generic visibility
still updates sleep bit6 and SAT eligibility **after the callback**. State7 and
`$8662` have no bit6 early return: asleep platforms keep moving/counting and
can still trigger/support through the same geometry. Whole-game camera-displaced
fixtures prove sleeping movement, and controlled fixtures prove sleeping contact.
There is no wake-time counter/position reset. State5 instead returns while asleep.

`$8908` independently marks type `$FE` at `abs(platformX-playerX)>=640` **or**
`abs(platformY-playerY)>=672`; both boundaries are inclusive. It runs even when
waiting. Marking `$FE` does not abort the rest of the current callback. A later
scheduler pass cleans the slot with `$5EF8`, releasing `$D400[token-1]`. Returning
to the creation band recreates from the exact placement, with latch0, speed+1,
tick16 and period=aux1. A natural moving SEZ1 #4 was deleted and recreated this way.

| Constant / relationship | Classification | Widescreen treatment |
|---|---|---|
| Mapped anchors and origin words | WORLD | preserve |
| 16-call period blocks; aux-derived displacement | object-origin-relative / temporal | preserve |
| Sag8, triangular contact, carry−14 | object/player-relative geometry | preserve |
| Keepalive distances640/672 | PLAYER_DIST | preserve; do not widen |
| Shared visible/awake/sleep/create/SAT bands | lifecycle / EDGE | existing viewport adapter only |
| Post-wake horizontal retention | GameMaker adapter only | explicit existing policy; never replaces640/672 |

The complete reachable bank-$1E state7 code scan has **no camera RAM references**.
Its fixed helper dependencies use player distance/anchors. There are no new
screen-edge constants or proposed widescreen platform rules.

## Reproduction and evidence limits

```powershell
.\.venv\Scripts\python.exe tools/sez_platform_28.py '../source/Sonic Chaos (Europe).sms' --check
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_sez*.py'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_platform_spike_collision.py'
.\.venv\Scripts\python.exe tests/verify_cache.py '../source/Sonic Chaos (Europe).sms'
git diff --check
```

Validation on 2026-10-06: 34 SEZ foundation tests (15,938 counted checks),
60 existing SEZ mechanics tests, 10 new S3 tests, 45 platform/spike tests and
30 isometric-platform tests passed: **179 distinct tests**. The foundation's
old unresolved-platform classification fixtures were corrected and all 34
foundation tests rerun successfully. Full `tests/verify_cache.py` passed.
The final source-hash boundary adjustment is additionally covered by focused
platform-cache regeneration/check; staged `git diff --check` is clean.

The generator checks **203,622 assertions/comparisons**, including the nested
6,417-case signed-speed sweep. Counts by group are in the cache. The three natural
`$86` objects each run a whole outbound/return cycle (768/1536/896 moving updates).
Those full-cycle fixtures park the player/camera nearby **after natural trigger**
at player-update boundaries to prevent unrelated terrain/death/lifecycle from
interrupting the contract check; platform anchors, counters and layout are never
patched. Separate unforced 45-update rider runs exercise real terrain, carry and
landing. The cache also stores actual jump-off, camera-induced sleep, deletion/
recreation and A/B/A history-independence vectors.

Whole-game runs use `ZoneGame.restore_snapshot()`'s established real-NOP then
re-restore guard. All three long cycles followed by the original rider case
reproduce the same first12 updates. This is an approximate SMS-harness observation,
not a claim of complete hardware emulation or human Windows acceptance.

No ROM runtime dependency remains unresolved for `$86/$04`. POC implementation
and final Windows gameplay acceptance remain pending. No new composition was
found; the approved platform art remains sufficient. Enemies, boss, surfaces,
monitor repair, player presentation and results were outside this audit.

## AGENTS candidate updates

- SEZ S3 Research is closed: use `data/rom-cache/sez/platform-28-runtime.json`.
- `$28/$86` starts on any closed shared overlap, makes a +1/−1 right-and-return
  trip of `16*aux1` px per leg, and resets its trigger latch after returning.
  Persistent overlap can immediately start another trip; leaving does not stop it.
- `$28/$04` is state5 with weight sag disabled, not an axis-swapped mover.
  `$86/$84` both use the shared 8 px sag while supported.
- State7 runs asleep and has keepalive from script entry; preserve strict
  player-distance retention640/672, even in wider views. Recreation starts at
  canonical placement. POC S3 still needs implementation and Windows acceptance.

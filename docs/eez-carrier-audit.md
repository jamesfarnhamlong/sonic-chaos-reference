# Zone5 mapped $17 and player $16/$17

Canonical Europe v1.2 research, corrected 2026-10-11. `carrier-17.json`
contains the source contract, scripts, block lists, source hashes and 124,524
controlled assertions (32,470 original + 92,054 expanded).
`carrier-game-checks.json` adds 265 assertions over ten original scheduler cases.
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
clears ownership and invokes the distinct `$494F` hurt tail described below. State5 falls with
gravity+1/4 until floor then requests6. State6 frame1 lasts16 updates and
calls `$A72B` to clear token/parameter; subsequent frame0 calls `$0362->$64F5`
to set typeFF and delete. `$64F5` is deletion, not flag clearing.
Scripts and block bytes are cached rather than renamed from appearance.

Player `$16` uses frame `$5F` for one update. `$4C02` clears Sonic's hide bit7,
loads owner `$D3A6`, calls `$4C56`, then hides the owner. Script `$835E` requests
player `$17` on the following script advance. `$17` uses the original three-update
directional selector `$9138` (Sonic `$5F/$60`).

`$4C56` copies **integer WORLD** X words `+$11/$12` and Y `+$14/$15`, plus
the exact signed 8.8 VX/VY words `+$16..$19`. Sonic's fractional bytes
`$D510/$D513` remain unchanged; owner fractions `+$10/+$13` are not copied.
The helper **sets** Sonic's attack bit1; facing flag4 bit4 is cleared when
owner parameter==2 and set otherwise, independently of VX. Owner state,
floor/flags, attack bit, animation counter and fractions are not copied.
The old phrase “copies actor state” was too broad. A full fixed-point position
copy is incorrect. Player-before-objects order sees the actor's pre-movement
integer position combined with Sonic's retained fractions.

`$4C12` executes in order: load owner, `$4C56` copy, `$753E` terrain-ring/special
probe, `$48BC` ordinary hurt gate, and **`$401A` signed cached screen-Y death**.
`$401A` reads signed `$D51C`, returns for negative Y, compares nonnegative Y
with `$00D0`, and invokes `$4984` at Y>=208. This screen-Y word was already
prepared; owner WORLD-position copying does not recalculate it. No movement
or input processing occurs in `$401A`. Direction bits do not steer: the
callback does not call `$4141/$402A/$4097/$690B` input/movement/normal terrain.
The real ring probe collects a natural EEZ1 quadrant on both parity paths.

After those calls, requested `$1E/$1F` detaches immediately. Otherwise clear
player airborne bit0, then test action byte `$D137` bits4/5; either detaches.
Detach unhides the owner, writes cooldown `+$1F=16`, sets owner flag3 bit6,
requests its parameter state, clears `$D3A6`, then jumps to **ordinary jump
setter `$45ED`**, not a generic state setter.

`$45ED` returns when airborne bit0 is set, current player state is `$11`, or
`$D36B & $FC == $90`. Otherwise it clears `$D3B2/$D3BC`, sets airborne/attack
bits0/1, clears special bit0, requests jump `$0A`, sets VY-4.25 dry/-3.25 water,
decrements integer Y by1 (fraction retained), writes `$D289=$60`, clears floor,
and requests sound `$A2`. Copied VX is retained. Real hurt/death flags retain
airborne, so the jump setter returns. A synthetic request-only `$1E/$1F`
without airborne can instead be overwritten by jump; do not add a state-based
fallback. The executing player remains `$17` on an action-detach update, so
the subsequent actor `$A741` returns before decrementing cooldown.

### Owning-carrier bounce is a distinct hurt path

`$A6D7` clears owner only when this actor equals `$D3A6`, then calls
**`$A710 -> $0419 -> $494F`**. This enters after ordinary `$48F7` ring-loss /
no-ring-death selection and `$4942..$494E` immunity setup. `$494F` clears player
contact byte `+$20`, requests `$1E`, sets airborne bit0, clears floor bit1,
sets VY-4 (ceiling bit0 ->+1), VX-1 (side bit3 ->+1), and clears `$D375`.
It preserves rings, attack and existing immunity bits, and `$D3B1`. Zero rings
still request hurt `$1E`; this call does not grant 120-update immunity. It
does not invoke the detach/jump setter. Non-owning bounce changes actor motion
and clears player hide bit7, but does not enter `$494F` or clear another owner.
Ordinary `$48BC` while attached can lose rings/select no-ring death; that is
separate from this bounce tail.

All movement/probe/alignment coordinates are WORLD. Generic `$61E1` lifecycle
applies **after capture too**; no carrier-specific widescreen rule is proven.
Only state1 gates asleep; states2..6 continue callbacks asleep.

Clearing actor token `+$3E` does **not** clear its original `$D400` occupancy
byte. Outside lifetime, token-backed actors become FE, `$626D` makes FF, and
later `$5EF8` releases the occupancy named by the token and clears the slot.
Tokenless actors become FF directly; their later slot clearing cannot release
the old occupancy byte. State6 also clears token/parameter before deletion.
Do not infer guaranteed placement respawn after captured-carrier disappearance.

Neither generic removal/cleanup nor `$4C56/$4C12` validates/repairs `$D3A6`.
FE/FF/reused RAM slots are copied as-is; a fully cleared RAM owner supplies zero
integer positions/speeds while Sonic retains his fractions and the stale owner.
No automatic detach is justified. Arbitrary null/non-RAM owner-pointer
consequences, and natural reachability of every synthetic stale-owner fixture,
remain outside the proven contract. No safe recovery is claimed.

### Natural records

| Act / record | File offset / bank:CPU | WORLD anchor |
|---|---|---|
| 1 / 17 | `$716E5` / `$1C:$96E5` | `(1040,478)` |
| 1 / 18 | `$716EE` / `$1C:$96EE` | `(2832,222)` |
| 2 / 9 | `$71749` / `$1C:$9749` | `(752,318)` |
| 2 / 10 | `$71752` / `$1C:$9752` | `(2672,670)` |
| 3 / 3 | `$7184F` / `$1C:$984F` | `(272,318)` |

### Validation correction

The old 32,470 assertions executed actual ROM routines; their overlap model
was not found incorrect. All their checked words/knockback results remain
unchanged. The defects were coverage/interpretation: no `$4C12/$401A` execution,
no varied fractions, and no bounce assertions on rings, immunity flags/timer
or zero-ring survival. “Shared hurt helper” and “ordinary player setter”
omitted distinctions needed for faithful implementation.

`tools/eez_carrier_contract.py` adds 92,054 checked predicates: all 65,536
screen-Y words, varied fractions/speeds/flags, every six-bit input combination,
actual callback-entry order, ordinary hurt/death versus synthetic requests,
bounce preservation, all 256 block/marker branches, sleep/gravity, slot cleanup /
stale owner and real ring probe. Instructions are original and unpatched;
routine death tests supply the normal IRQ semaphore in RAM.
`tools/eez_carrier_game.py` seeds all five natural records once per action-bit
case and observes original copy boundaries, state transitions, capture token
semantics, sustained attachment and detach. Its 265 assertions cover ten cases.
Existing `system-game-checks.json` still covers the first carrier's longer route.
No input-only whole-act traversal, natural state3 entry, new visual approval,
POC implementation or Windows acceptance is claimed.

Reproduce: `python tools/eez_carrier.py <ROM> --check`,
`python tools/eez_carrier_game.py <ROM> --check`, and
`python -m unittest discover -s tests -p test_eez_carrier_contract.py -v`.
ROM SHA-256: `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.

# Rocket Shoes and Spring Shoes audit

This is the canonical Master System contract for the two footwear systems in
Sonic Chaos (Europe) v1.2. It distinguishes ROM identity, player gameplay
state, animation and the GameMaker adapter. Reproduce the machine results with:

```text
python tools/powerup_shoes.py ".../Sonic Chaos (Europe).sms" --check
python -m unittest tests.test_powerup_shoes
```

The cache is `data/rom-cache/powerup-shoes.json`. Evidence labels are decoded
data, byte-verified assembly, source-traced behavior and controlled original-
routine result. Human names do not replace the numeric identities.

## 1. Identities

| System | Canonical object/reward | Player state | Persistent storage |
|---|---|---:|---|
| Rocket Shoes | monitor type `$10`, parameter `$04`; reward mask `$08` | `$11` | selector `$D532=$04`; active timer `$D44C`; entry copy `$D3A1` |
| Spring Shoes | mapped object type `$2F`, parameter `$00` | `$12` | attached-object pointer `$D3A4`; **no** selector or timer |

State `$11` is Rocket Shoes, not Spring Shoes and not a shared footwear state.
Spring Shoes are a physical object which attaches to Sonic; they are not a
monitor reward. Type `$2F` graphics and its attached positioning support the
conventional Spring Shoes name, while `$2F` remains the machine identity.

Rocket's `$10/$04` icon is the parameter-4 monitor frame from the normal type-
`$10` graphics set. Spring object mappings are at bank `$0F`, CPU `$9287`
(ROM `$3D287`). Sleeping Egg loads the common 512-byte stream at ROM `$26840`
to VRAM `$1280` (tiles `$94..$A3`); Mecha Green Hill loads that same stream to
VRAM `$1580` (tiles `$AC..$BB`). The auxiliary placement byte follows that art
base. This is a presentation variant, not a second behavior.

## 2. Placement and global reuse

Rocket Shoes occur 11 times, always type `$10` parameter `$04`, flags/auxiliary
bytes zero:

| Act | World `(X,Y)` |
|---|---|
| Turquoise Hill 1 | `(336,270)`, `(1472,110)` |
| Turquoise Hill 2 | `(2544,494)` |
| Gigalopolis 2 | `(2288,430)` |
| Sleeping Egg 1 | `(2192,878)` |
| Sleeping Egg 2 | `(1584,942)` |
| Mecha Green Hill 1 | `(1312,110)` |
| Mecha Green Hill 2 | `(48,878)` |
| Aqua Planet 1 | `(1664,430)`, `(3344,174)` |
| Electric Egg 2 | `(560,878)` |

Spring Shoes occur 16 times, always type `$2F` parameter `$00`, flags zero:

| Act | World `(X,Y)` | aux0/aux1 |
|---|---|---|
| Sleeping Egg 1 | `(224,398)`, `(784,782)`, `(1264,302)`, `(1936,686)`, `(2384,750)`, `(2528,718)`, `(2944,558)`, `(3152,878)` | `$94/$94` |
| Sleeping Egg 2 | `(432,846)`, `(608,718)`, `(848,878)`, `(3248,846)` | `$94/$94` |
| Sleeping Egg 3 | `(176,814)` | `$94/$94` |
| Mecha Green Hill 1 | `(1552,238)` | `$AC/$AC` |
| Mecha Green Hill 2 | `(3760,494)`, `(2592,174)` | `$AC/$AC` |

All omitted regular acts contain neither relevant object. The full 18-act
manifest, record ROM offsets and auxiliary bytes are cached. Thus one Rocket
movement model and one Spring attachment model close all regular-game reuse.

## 3. Rocket pickup and update order

Breaking `$10/$04` queues `$D3A3` bit 3. On the next player update the old
player state runs first; reward dispatcher `$4AA3/$4ADF` then writes selector
4 and the timer and calls `$4775`. That entry routine:

- zeroes X/Y velocity;
- sets horizontal maximum `$0700` (7.0 px/update);
- requests sound `$85` and writes ordinary duration `$012C` (300);
- copies the duration to `$D3A1`;
- clears `$D503` attack bit 1 and bit 6;
- requests state `$11`.

The animation/state engine applies current state `$11` on the following
update. Consequently the monitor break is object phase N, the reward/next-
state write is player update N+1, and the first full `$11` callback is N+2.
Special level `$08` uses `$1770` and skips sound `$85`; that fork is not a
regular-act duration.

The state script at CPU `$8334` / ROM `$30334` is frames `$38,$39,$3A,$39`
for 8,4,8,4 updates and repeats. These frames are presentation; the gameplay
callback is `$3A7C` throughout.

## 4. Rocket movement, terrain and camera

The input model is powered flight, not ordinary movement with a higher cap:

- Left/Right first updates facing through `$48A7`.
- State `$11` then ORs a held horizontal direction into `$D137` from facing:
  mirrored means Left; unmirrored means Right. There is no neutral horizontal
  cruise while this callback runs.
- Shared acceleration is `1/16` px/update² dry (`$0010`) and `1/128` in water
  (`$0002`), capped by 7.0. Reversal changes facing then thrusts that way.
- Up subtracts `$0040` from Y velocity, clamped to `-$0400`; Down adds `$0040`,
  clamped to `+$0400`.
- With neither vertical direction, the signed **high byte** selects `-$0020`
  for nonnegative speed and `+$0020` for negative speed. Fractional values can
  cross zero and oscillate; there is no clamp-to-zero.
- Ordinary gravity is bypassed in state `$11`. Jump/spin-dash input has no
  state-local action path.

State `$11` still invokes shared X/Y integration and the ordinary terrain
passes. Floors, walls, ceilings, slopes and one-way terrain project normally.
On ground contact its local tail clears the object floor-contact bit, moves the
anchor up two pixels and zeros Y speed. Type `$28` platform and ordinary object
passes remain available. Loops/twists may replace the player state through
their terrain handlers rather than becoming a special Rocket movement mode.

Terrain upright, diagonal and horizontal spring handlers explicitly reject
current state `$11`; the ceiling-spring path does not carry that exclusion.
Mapped type `$26` does not test state `$11`: if its normal geometry/floor/Y-
speed gates succeed, its canonical launch overwrites velocity and state.

Rocket adds one vertical viewport constraint using the player anchor:

- screen Y `<24` becomes `EDGE(TOP,+25)` and Y speed 0;
- screen Y `>=192` becomes `EDGE(TOP,+191)` and Y speed 0.

Horizontal follow/lead and the ordinary player edge clamp are otherwise
unchanged. These 192-line relations are canonical; do not reproduce low-byte
SMS wrapping artifacts or silently widen them.

## 5. Rocket rings, attack and termination

Rocket Shoes collect both ring forms in the original:

- type `$09` uses its normal state-independent strict test
  `abs(dx)<12 && abs(dy)<12` on canonical anchors;
- state `$11` is explicitly one of the 26 player states which run terrain-ring
  probe `$753E`; it executes after movement/projection using anchor X and
  `Y-8` on an even animation-record counter or `Y+2` on an odd counter.

There is no dedicated Rocket ring path and no power-up-state object skip. The
direct explanation for a no-ring implementation is therefore a missing/bypassed
ordinary ring pipeline, not canonical behavior. The accepted POC source now
contains state 17 in `SCR_chaos_anim_probe_states()` and its type `$09` path is
unconditional, so the reported Windows failure is not reproduced by current
static source. It may describe an older executable; obtain its exact package
before changing either canonical probe.

Entry clears attack posture `$D503.1`; state `$11` does not restore it. Normal
Rocket Sonic therefore cannot break a monitor or defeat a side-contact enemy.
Type `$21` retains its top-stomp-before-attack behavior, while side/low contact
damages; type `$27` and ordinary hazards damage through their canonical paths.
Moving/static spikes remain hazardous. Damage's special state-$11 branch
clears selector 4 and queued bit 3, restores level music, requests sound `$C3`
and enters hurt without ordinary ring loss. State is never shorthand for the
attack bit: picking invincibility later can set bit 1 while `$11` still runs.

Ordinary duration is exactly 300 end-of-player-update decrements. There are
300 full callbacks which enter with timer 300..1. The following callback enters
with zero, still performs its movement/collision work, restores music through
`$189B`, then `$463C` requests fall `$0E`, sets Y speed `+1.0` and marks
airborne. Landing and ordinary terrain collision do not expire it. Damage does.
Death/act setup eventually replaces state/RAM, but the complete global RAM-
clear chain across every transition remains unresolved.

## 6. Spring Shoes pickup, bounce and springs

Type `$2F` initialization requests object state 1 and suppresses generic
contact damage. While Sonic is non-rising and not already in player state
`$12`, its `$5FA0` projection may classify a top contact. That contact stores
the object slot in `$D3A4`, requests player `$12`, and requests object state 3.
There is no power-up selector, timer, pickup music, palette change or immediate
velocity write. A grounded attacking side contact instead pushes Sonic to the
object side, zeros X velocity and requests standing; it is not pickup.

State `$12` uses the shared movement/terrain pipeline and ordinary gravity:
`+$0030` dry / `+$0018` water with downward terminals `+7/+4`. Horizontal
control uses `+/-$0010` dry (`+/-$0002` water), maximum from ordinary player
state, and neutral `+/-$0020` friction. Up/Down have no special meaning.
The shared foot probe receives the state-$12 `+8` offset.

Every floor-contact update automatically:

- clears the object-contact floor bit;
- marks airborne;
- writes Y velocity `-$0780` = `-7.5`;
- moves the player anchor up one pixel;
- keeps/requests player state `$12` and owner state 3;
- requests sound `$C2`.

This is a fixed independent bounce, not a multiplier for springs and not
conditional on incoming downward speed after the contact has been formed.
Pressing either action button detaches the owner and invokes normal jump
`$45ED`: `-4.25` dry / `-3.25` water, state `$0A`. Thus manual jump is allowed
but explicitly cancels the shoes.

Canonical springs win over the footwear:

| Spring | Result |
|---|---|
| strong mapped `$26` | `vy=-7.375`, `$0B`, attack clear |
| weak mapped `$26` | `vy=-5.0`, `$0B`, attack clear |
| span `$26` | its strong/weak parameter result, `$0B`, attack clear |
| terrain upright | `vy=-7.5`, `$0B`, attack clear |
| terrain diagonal | `vx=+/-4`, `vy=-7`, `$1C`, attack set |
| terrain horizontal | `vx=+/-6`, preserve vy, state 9, attack set |

No value is multiplied or added. Once current player state is no longer `$12`,
the owner sees that on its next update, requests detach state 5, initializes
fall speed `+1.5` and falls with `+0.5` gravity.

## 7. Spring rings, hazards and lifetime

Type `$09` collection remains state-independent. State `$12` is explicitly in
the same terrain-ring 26-state family and uses the same animation-counter
parity. Its player script is one duration-4 frame `$0B` record, so gameplay
probe timing must follow the player animation-record counter, not the visible
GameMaker sprite clock.

Neither type `$2F` attachment nor the state-$12 callback changes attack bit 1.
The bit is inherited at pickup and preserved at automatic rebounds. Rising,
apex and falling Spring Shoes Sonic therefore have whichever attack posture
was carried into the attachment; airborne status alone proves nothing. Type
`$21/$27`, monitors and hazards read their normal predicates. Type `$21` top
stomp, side hurt, ordinary damage, spikes, canonical springs or any other
state replacement ends state `$12`, then the owner detaches. The special
state-$12 side-wall branch detaches and invokes hurt movement directly.

There is no duration, warning or expiry-on-landing. The object lasts exactly
while player current state remains `$12` and the owner is attached. Normal
act/death/state replacement removes that relationship; global transition RAM
initialization was not exhaustively traced.

## 8. Coexistence and storage

Rocket `$04`, speed-up `$03` and invincibility `$06` share `$D532/$D44C`; the
latest reward overwrites selector and timer. Spring Shoes own neither field.
This permits state and selector to diverge temporarily:

- invincibility picked during `$11` writes selector 6/timer 600 and attack bit
  1; state `$11` can continue and now attacks;
- speed-up picked during `$11` overwrites selector/timer while the player state
  can remain `$11`; when timer 3 reaches zero `$4A74` deliberately does not
  clear selector 3, and the next decrement wraps zero to `$FFFF`, so this ROM
  effect persists until another reset/reward;
- a new Rocket pickup requests `$11`, overwrites selector/timer and clears
  attack, so an attached `$2F` subsequently detaches;
- a `$2F` pickup requests `$12`, ending Rocket movement, while an old shared
  selector/timer can continue its independent cleanup.

Implement player state, attack flags, animation, selector/timer and type `$2F`
ownership as separate concepts. A single `footwear` enum cannot express these
canonical overlaps.

## 9. Spin-dash versus monitor

Type `$10` calls solid projection `$5FA0` **before** its attack branch. It then
requires `$D503.1`. Bottom contact has its own bounce. Top contact rejects
requested states `$0F/$10/$15/$1A`. Every remaining top or side break also
requires nonzero, nonnegative/downward Y velocity. State 9 breaks without the
usual `vy=-4` rebound.

The focused `top/side/bottom`, edge `-1/0/+1`, requested-state and Y-speed
matrix proves:

- an unambiguous side contact in attacking posture with positive Y speed does
  break;
- a contact projected/classified as top while requested state is `$0F/$10`
  canonically does not break;
- solid contact is already staged before either outcome and can affect the next
  player update.

Classification is **D: arrangement-specific/canonical edge case** for the
reported observation as stated. The row arrangement can expose top/side
classification and staged-solid ordering. If a captured Windows case shows an
unambiguous side classification, attack bit set and positive Y speed yet the
box survives, that narrower case is POC B/C rather than canonical. The exact
pose/build was not supplied, so no geometry change is justified.

## 10. Read-only POC migration

| Area | Accepted POC | Required migration |
|---|---|---|
| Rocket identity/entry | substantially present | retain `$10/$04`, selector 4, state `$11` and delayed state application |
| Rocket X control | shared movement sees only user input | after facing update, force held Left/Right from facing before shared movement |
| Rocket neutral Y | clamps fractional speed to zero | use signed-high-byte `+/-$20`, including zero-crossing oscillation |
| Rocket attack | adapter forces `!state11` | publish stored canonical attack bit; invincibility can set it during `$11` |
| Rocket damage cleanup | generic POC hurt can scatter rings or select death before cancelling `$11` | add the canonical state-$11 special branch: retain rings (including zero), cancel selector/queue, enter `$1E`, sound `$C3` |
| Rocket rings | current source has state 17 and unconditional type `$09` | keep it; reproduce the reported executable before changing probes |
| Rocket collision | shared terrain broadly present | preserve terrain-spring state-11 rejection versus mapped `$26` override |
| Rocket camera | vertical clamp present | retain canonical anchor thresholds |
| Spring Shoes | absent; type `$26` springs are a different system | add mapped `$2F`, owner pointer/lifecycle and player state `$12` |
| Spring attack/rings | absent | preserve inherited attack; add `$12` terrain-ring eligibility/counter timing |
| Monitor order | broadly mirrors `$5FA0` then attack | retain ordering; diagnose captured contact classification before adjustment |

The concrete Rocket mismatches are in `SCR_cc_state11_tick` and the adapter's
blanket state-$11 attack suppression. The current animation-probe table already
contains decimal 17 and 18. No POC files were changed for this audit.

## 11. Remaining uncertainty

- The exact failing Rocket no-ring Windows executable/save state was not
  available; current accepted source and ROM behavior both allow collection.
- The exact monitor-stop pose was not available; the conditional canonical
  classification above is closed, while a replay-specific POC defect is not.
- Global death/act transition RAM clearing was not followed through every game
  mode. Local damage, expiry, state-replacement and detach behavior is closed.

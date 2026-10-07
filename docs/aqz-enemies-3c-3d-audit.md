# AQZ A4 — numeric types $3C/$3D

Base: Manager-approved A3 `932e091be7a80f3353abac9143b7cef151ce74a6`, fast-forwarded to Research main without a new/merge commit. Europe v1.2 ROM, 524288 bytes, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. No POC changes. ROM remains local-only.

Machine contracts and original-routine vectors: `data/rom-cache/aqz/enemies-3c-3d-runtime.json`. Natural loader/scheduler cases: `enemies-3c-3d-game-checks.json`. Manifest and census point every placement at these contracts. Source-region hashes include scripts/callbacks, creator, scheduler, lifecycle, contact, defeat, player response and VBlank clock increment; tool hashes normalize source text through UTF-8/LF.

Evidence labels: decoded data, source-traced behavior, controlled original Z80 routine result, original-game software-harness observation. These fixtures do not claim Windows/human acceptance or hardware raster verification.

## Census and corrections to reconnaissance

The authoritative `object-census.json` supplies all30 records; each record's nine bytes is compared to the verified ROM. No placement coordinates or summary counts are manually reconstructed. Both output caches retain act/index, file/bank/CPU, raw/stored/world coordinates, flags, parameter and aux bytes.

| Type | AQZ1 | AQZ2 | Parameters |
|---|---:|---:|---|
| $3C | 8 | 3 | act1: $00×7,$01×1; act2: $00×2,$01×1 |
| $3D | 9 | 10 | act1: $00/$04/$08 each3; act2: $00×5,$04×3,$08×2 |

Two reconnaissance claims need correction. $3C's four-call legs move **4 pixels per callback**, hence16 pixels per leg. $3D does **not** read the waterline or global clock: $936A reads saved object-origin Y at +$3C/+3D, while +$35 is its own dwell counter. The A1 stored code scan already reports no RAM references for $3D; the later wording about waterline/time was not an implementation contract.

Also, $3C has no attack defeat path. Its $0434 vector points to forced-hurt helper $630B. Treating it as an ordinary defeatable badnik would contradict original execution.

## Creator and $3C complete graph

Both types use original mapped creator $1C:$80EB: stored coordinates minus256 become runtime anchors and saved origins; flags|$40, parameter+$3F, aux+$08/09 and one-based token+$3E are retained. Occupancy is set by the outer loader. Table $1E:$91F1 (file$791F1) has nine scripts; initializer $9251 requests1 for parameter0. Any nonzero parameter requests5 and adds12 to integer anchorY once. Natural parameter1 is the only nonzero placement; stored origin/placement is not rewritten.

| States | Frame | Motion/callbacks | Transition |
|---|---:|---|---|
| 1→2→3→4 | 1 | 1: four calls Y−=4 ($926F); 2:32 dwell; 3:four calls Y+=4 ($9274); 4:32 dwell ($9284) | 4→1 |
| 5→6→7→8 | 2 | 5:four calls Y+=4; 6:32 dwell; 7:four calls Y−=4; 8:32 dwell | 8→5 |

Each cycle is72 object callbacks after initialization. Parameter0 spans originY−16..originY; parameter1 spans originY+12..originY+28. Integer writes preserve fraction and velocity bytes; no origin clamp or direction-threshold comparison occurs. The script selects the direction and duration. No terrain, player-distance or water trigger. No initializer writes a natural mirror bit; orientation is in frame1 versus frame2's original mapping.

Movement precedes the contact tail. $9284 skips contact if asleep flag4 bit6 is set or VBlank-owned $D12F bit0 is1. IRQ code $0603/$0606 increments $D12F, so the predicate is **even global VBlank counter**, not an invented private enemy timer or an unconditional every-other object-update counter. The returning-routine trace increments that counter synthetically per step; whole-game fixtures use the original IRQ. Script counters/transitions and integer motion continue while asleep.

Awake/even-frame contact calls $0434→$630B→$6328. Any overlap sets $D3B0=$FF, regardless of attack or selector6. No $5F3D call, score or type conversion. Player-side invincibility selector6 clears the damage request; attack posture alone does not protect against forced hurt. Hurt/blink suppression is handled by the shared overlap/player response described below. Ordinary deletion/recreation is supported; there is no defeated/non-recreation variant for $3C.

## $3D complete natural graph and parameters

Table $1E:$9291 (file$79291) has four scripts. State0 callback $9304 reads and decrements the parameter. Natural `$00/$04/$08` mean **zero/four/eight initializer decrement callbacks**, followed by a callback requesting state1; launch begins on the next engine phase. They do not select direction, formation index or water phase. Initialization ignores asleep: countdown and request continue while the mapped object is sleeping.

State1 installs 8.8 velocities X=$00C0 (+0.75), Y=$FE00 (−2); frames1/2 alternate every8 script updates. State2 installs X=$FF40 (−0.75), Y=$FE00; frames3/4 alternate every8. Fraction bytes survive state changes. Natural initializer requests1; the active callback toggles requests1↔2.

Active callback $932B order:

1. Return if asleep.
2. $6328 contact; on nonzero contact nibble jump to $5F3D and return, even when defeat is rejected. Thus any unsuppressed overlap pauses the callback's motion/dwell decrement on that call.
3. If +$35>0, decrement it, and at zero request the opposite state. Return without movement/gravity throughout this32-call dwell.
4. Otherwise add +24/256 to Y speed via $0431→$631A, then integrate X/Y via $0338→$60FB.
5. If updated Y speed is nonnegative and **unsigned integer anchorY>=saved WORLD originY**, inclusively, set +$35=32.

There is no terminal cap, terrain probe, coordinate projection or clamp. The next engine phase after the dwell reinitializes launch velocities but keeps fractions/position. The first ordinary leg from zero fraction takes42 moving calls, travels31.5 pixels horizontally and returns to originY with Y fraction168 and Vy496/256; later legs may differ because overshoot/fractions are preserved. Do not hard-code42 as a callback timer. Full240-step vectors expose the actual integration and drift.

Grouped placements are independent. There is no other-slot read, neighbour/controller link, global clock read or shared phase variable. Their spacing and parameter delays come from the census; no “school/swarm” communication contract is inferred.

State3 is **not reached by natural parameters or $3D's own defeat**. Parameter$FF selects it, forces art base+$08=$70 and clears mirror bit4. The small local path is also controlled:40 calls at Y−0.5; seven stationary8-call frame records2/3/4/1/2/3/4;40 calls at Y+0.5; nominal16-call frame1 record whose $92FF callback deletes on its **first** call. With the initializer included, deletion occurs on controlled step138. Movement ignores sleep through shared $0338. External creation of this nonnatural path is outside the natural A4 contract; no A5 creator is audited.

## Frame extents, contact and player outcomes

Original engine $64FA installs these frame extents:

| Type/frame | Extent X,Y | Ordinary Sonic closed overlap | State$0F closed overlap |
|---|---|---|---|
| $3C 1/2 | 3,13 | X−11..+11,Y−13..+24 | X−12..+12,Y−13..+24 |
| $3D 1/2/3/4 | 3,21 | X−11..+11,Y−21..+24 | X−12..+12,Y−21..+24 |
| Both frame0 | 0,0 | Initialization/invisible frame; initializer has no contact call | Same |

$6328 owns closed-interval overlap, minimum penetration and vertical tie classification. $D503 bit6 suppresses overlap for these ordinary objects (object flag3 bit7 is clear). Bit7 suppresses the object contact-status byte but does **not** suppress the contact nibble or $D520, nor prevent an attacking/invincible $3D defeat. The player $48BC handler separately skips damage/rebound while blinking; its timer remains canonical.

$3D calls shared $5F3D: contact plus `$D532==6` or `$D503 bit1` converts to$0F, awards100 points (score accumulator low byteBCD$10), and resets state/request/script pointer/duration/flags4/token/parameter. The enemy does not write a direct rebound. Ordinary nonattack contact leaves $D520 for the next player callback's shared hurt/ring-loss path. Do not substitute airborne state for bit1.

On the next player update, attacking $3D contact rebounds −3.0 from above or +0.5 from below; side contact preserves velocity. State9 suppresses **only the below** rebound, not the top rebound. Selector6 suppresses both, while still defeating $3D. Hurt/blink player flags suppress player-side damage/rebound as above. $3C's $D3B0 forced-hurt request takes precedence over the attacking $D520 rebound route; invincibility selector6 protects the player but does not defeat $3C.

Both contact families are swept across all256 movement-flag bytes, selector0/6, top/bottom/side positions, both player X extents and every visible frame. Separate original player-handler vectors cover8192 flag/state/selector/classification combinations, including state9 and retained blink/hurt semantics. Whole-game contact fixtures stop synthetic player writes after first qualifying overlap so the following real player phase can respond.

## Water, lifecycle and scheduling

Neither family nor its called contact/move/gravity helpers reads $D443, $D450, water controllers or camera raster state. $3C reads only the VBlank clock for contact parity; $3D uses its own saved WORLD origin and counter. Changing water flag/line/raster inputs leaves their original callback outputs identical. Player water physics can change actual approach/contact, independently of enemy physics. Their rendered colours still consume the shared A2 raster/palette presentation; this changes colour interpretation without an enemy state/movement branch or new composition. No buoyancy, drag, palette-driven state or underwater speed multiplier.

Natural $3D origins are above their act waterlines; even the AQZ2 originY782 placement returns close to782 rather than treating WORLD788 as its boundary. Whole-game controlled waterline probes place a synthetic line at originY−10 before the target $932B callback. Each trajectory passes both sides of that line and matches its passive enemy snapshots exactly, covering allthree parameters in both acts. This is an explicitly synthetic waterline test, not a claim of canonical controller movement. Raster/controller behavior remains the accepted A2 contract.

Both are ordinary mapped lifecycle objects with **no keepalive**. Canonical256px create/wake/sleep/delete bands are EDGE relationships from `docs/viewport-semantics-audit.md`; origins, motion and comparison are WORLD. No family-specific PLAYER_DIST, CENTER or LOCKED_CAMERA constant appears. Research does not design the later post-awake retention adapter.

Callback executes before generic $61E1, so observes the previous asleep flag. $3C continues movement asleep; active $3D freezes motion/counter/contact while engine frame timing continues. Both initializers run asleep. First visible activity depends on this scheduling and original creation band, rather than an invented immediate create-and-move step.

Ordinary outer-window deletion marks$FE when token is present, then$FF/cleanup releases occupancy. Returning through a creation band reinitializes raw parameter, origin, fractions and phase. $3D defeat clears its token before$0F cleanup, leaving occupancy spent until act restart; backtracking cannot recreate it. $3C has no defeat conversion. Deletion/recreation and defeat/backtrack fixtures cover every distinct act/type/parameter path.

Original order: player update (A2 water/motion/terrain/contact), object engine/callback, generic lifecycle, periodic bank$1C mapped creation, renderer/effects. $3C moves before contact; $3D contacts before counter/gravity/movement. Enemy $D520/$D3B0 requests are consumed in the following player phase. Independent $3D slot delays are local; IRQ clock phase only gates $3C contact.

## Art, fixtures and verification

A1 boards are approved. All reached frames/orientations are already present: $3C0..2 and $3D0..4, mapping compositions rather than an added whole-bitmap flip. No new board or synthetic asset is required. See `data/rom-cache/aqz/art-approval.json` and ignored `build/aqz-approval` for reproduction and hashes.

Controlled fixtures execute original creators/scripts/callbacks for all30 placements over240 steps each. Coordinate-independent parameter equivalents compare exactly after anchor normalization. Natural whole-game coverage runs all30 through original loader/scheduler for180 recorded updates each; further fixtures cover attack, ordinary damage, invincibility, hurt/blink flags, sleep/wake, deletion/recreation, defeat/backtrack and waterline probes. Distinct cases are grouped only after source/relative-vector equivalence; each act/type/parameter is represented.

The software harness restores full exported CPU bytes plus RAM/VDP/harness snapshot, including prefix, EI shadow and frame_tick. Replay after the intervening contact/lifecycle history compares180-step traces exactly in both acts. No register-only restore or NOP repair. Synthetic player/camera controls, blink timer protection and waterline probe are labelled in cache metadata; enemy, occupancy, layout and ROM code are not injected or rewritten.

Validation targets: nine focused A4 unittest methods;177802 enumerated original-routine assertions;15032 whole-game rows (not an assertion count); existing A1–A3 regression tests; full `verify_cache`; working/staged `git diff --check`.

```text
.venv\Scripts\python.exe tools\aqz_enemies.py ROM.sms --check
.venv\Scripts\python.exe tools\aqz_enemies_game.py ROM.sms --check
.venv\Scripts\python.exe -m unittest discover -s tests -p test_aqz_enemies.py
.venv\Scripts\python.exe tests\verify_cache.py ROM.sms
git diff --check
```

## Unresolveds and AGENTS candidates

No unresolved natural A4 runtime dependency remains. External creators of nonnatural $3D/$FF are not inferred from its local script. A5 boss/children, POC/widescreen adaptation and results assets remain excluded. Human POC playtesting remains a later acceptance step.

Candidates for Manager consolidation: Research main now includes accepted A1–A3 at932e091; $3C is a forced-hurt contact family with no attack defeat; its movement continues asleep and contact is even-VBlank gated; $3D parameters0/4/8 are initializer delays and its compare is saved WORLD originY, not water; ordinary mapped lifecycle release differs from $3D defeated/spent occupancy; state9 suppresses only the shared below rebound; preserve full CPU snapshots. Root AGENTS is not edited here.

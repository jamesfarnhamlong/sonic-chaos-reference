# GPZ3 `$51` gameplay/runtime audit

Pre-commit review, branch `research/gpz3-boss-runtime`, based on Research main
`d214c60`. Canonical Europe v1.2 ROM SHA-256:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
No POC edits. The approved `$51/$34/$0A` art package is unchanged. Runtime
reachability confirms its frame roles; no art/composition review was reopened.

Evidence: decoded state scripts; source-traced callbacks; controlled original
Z80 routines, allocator and `$5DD1` scheduler; one update-aligned original-game
fight/results/next-zone trace. The SMS harness models approximate VDP/IRQ timing;
the fight uses synthetic attacking placements, not a controller-only recording.
Controlled fixture ticks are scheduler calls, not video timestamps. All JSON
states/IDs/addresses are numeric decimal; this document uses hexadecimal `$` IDs.

## Reproducible package

- `tools/gpz51_runtime.py` generates `data/rom-cache/gpz/boss-51-runtime.json`.
- `tools/gpz51_fullgame.py` generates `data/rom-cache/gpz/boss-51-fullgame.json`.
- `tests/test_gpz51_runtime.py` locks geometry, classification, mux, health,
  reactions, throws, regrowth, removal, floor gate and the complete transition.
- Existing `tests/test_gpz51_composition.py` supplies the all-256-low-byte mode
  sweep and approved composition regression locks.

The runtime cache contains every scheduler row of a normal mode1 cycle (1,000
updates, including initial emergence and first restored stack), state-change
events for modes0/1/2 and both throw directions, the complete 21-state scripts,
32 signed sway offsets, contact cases, health entry/recontact timelines,
defeat/support rows and boundary sweeps. Every script record retains duration,
frame and callback; command operands retain exact spawn/velocity/repeat values.
No ROM or pixel dump is added. Source region `$1E:$9A3A..$A1D3`, file
`$79A3A..$7A1D3`, has a regeneration-checked hash.

```powershell
$env:SONIC_CHAOS_ROM='E:\AI\Codex\Sonic Chaos\source\Sonic Chaos (Europe).sms'
.venv/Scripts/python.exe tools/gpz51_runtime.py $env:SONIC_CHAOS_ROM --check
.venv/Scripts/python.exe tools/gpz51_fullgame.py $env:SONIC_CHAOS_ROM --check
.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_gpz51*.py' -v
```

## Mode selection and setup

Canonical mapped record: `$51/$00` at `(1728,270)`, bank `$1C:$8DF6`, file
`$70DF6`. Initialization `$1E:$9A99` / file `$79A99` runs only for parameter0:

- right camera limit `$D282 = $0680` (1664), runtime head X `$0740` (1856);
- `$D44E = zoneIndex+1`; boss music `$8C` to `$DE04/$D4A4`;
- mode `+$32`, health `+$26` selected by `(playerY_low-16) mod256`.

| Player Y low byte | Mode | Initial HP | Attached segments |
|---|---:|---:|---:|
| 16..143 | 0 | 5 | 3 |
| 144..239 | 1 | 8 | 3 |
| 240..255 or 0..15 | 2 | 10 | 4 |

These are low-byte ranges, not world-height bands. The all-byte initializer
sweep executes original code. Parameter children bypass controller setup;
`$9AE0` requests `parameter+1`. `$9B91` reads the fixed head at `$D732`, skipping
the parameter4 spawn in modes0/1. Keep the controller identity stable: several
routines explicitly read `$D700` fields rather than searching by type.

There is no THZ-style `<160/<256` player trigger in this `$51` init chain. Mapped
creation still belongs to the existing generic placement loader. Once created,
state0 starts the intro. Script `$9A64` sets keep-alive, initializes, runs a
one-update blank record, creates `$12` HUD slide-away, waits112 updates, installs
dynamic selector `$14` and palette13, waits16 updates, then starts the camera
pan. Its 224-update camera-ready record repeats until both camera axes are
strictly within4 pixels of `(1664,96)`; callback `$9AF7` then sets timer1 and
script cursor `$9A90`, entering the spawn chain. Repeated 224 is not an intro
duration to implement as a fixed wait. The controlled already-positioned camera
run creates parameter1 at tick130.

## All states and transitions

State script table `$1E:$9A3A` / file `$79A3A`, 21 entries. Requested state
changes become active on the object's next scheduler visit; instant script
commands can consume intermediate states on that visit.

| Hex state | Script CPU | Behavior / outgoing transition |
|---|---|---|
| `$00` | `$9A64` | Parent intro; children request parameter+1. Parent camera-ready tail -> `$01`. |
| `$01` | `$9B45` | Spawn/link parameter1 at dy+32; parent -> `$07`. |
| `$02` | `$9B56` | Spawn/link parameter2 at dy+32; parameter1 -> `$06`. |
| `$03` | `$9B67` | Spawn/link parameter3 at dy+32; parameter2 -> `$06`. |
| `$04` | `$9B78` | Modes0/1 -> `$06` immediately; mode2 waits4 blank updates, spawns parameter4, -> `$06`. |
| `$05` | `$9B9C` | Parameter4 init alias -> `$06`. |
| `$06` | `$9BA1` | Attached segment: defeat check, follow lower support, mux contact; missing support -> `$08/$09`. Frames3..9, 4 updates each. |
| `$07` | `$9BBF` | Head: follow, mux contact, attacking overlap -> `$0D`; lost/detached support -> `$08/$0C`. Frame2. |
| `$08` | `$9BC5` | Rise Y speed−1 until Y<270, clamp270 and request `$0A`; frames3..9, 4 updates. No contact callback. |
| `$09` | `$9BE9` | Segment drop: defeat check, mux contact, gravity+1/8, movement; Y>=270 clamps and installs landing tail `$9C0F`. |
| `$0A` | `$9C20` | Floor-supported bottom: defeat check, mux contact, movement, horizontal acceleration and throw-counter overflow -> `$0B/$0F/$13/$14`. |
| `$0B` | `$9C4E` | Detached left slide: defeat check, forced-hurt contact, acceleration left, movement, split-byte deletion predicate. |
| `$0C` | `$9C74` | Head fall: gravity+1/8, movement; Y>=270 clamps and requests `$01` (regrow). No head-hit/contact callback. |
| `$0D` | `$9C86` | Head reaction: sound `$B3`, decrement HP once; HP0 requests `$0E`, else 54 reaction updates then `$07`. Follow/mux contact continues. |
| `$0E` | `$9CB5` | Head explosion sequence, wait, repeated floor-gated `$9D26`; grounded -> delete head, `$0A/$00`, request player `$20`. |
| `$0F` | `$9D58` | Detached right slide, counterpart of `$0B`. |
| `$10` | `$9D7E` | Segment defeat delay16 updates -> `$11`. |
| `$11` | `$9D87` | Four `$34/$04` puffs at one-update intervals; segment deletes on fourth record callback `$9DB9`. |
| `$12` | `$9DBE` | `$51/$11` landing dust: frames10/11 at3 updates, two repeats plus final3-update frame11, then delete. |
| `$13` | `$9DD3` | Detached left arc, configured X−1.5/Y−4.5, forced-hurt, gravity+1/8, floor rebound−4, split-byte deletion. |
| `$14` | `$9DF9` | Detached right arc, configured X+1.5/Y−4.5; otherwise counterpart of `$13`. |

Do not confuse hex state `$11` (segment explosion) with parameter `$11`
(landing dust, state `$12`), or player state `$20` with boss state `$14`.

## Linked scheduler, timing and regrowth

`$5DD1` walks 19 slots from `$D540` to `$D9C0`, ascending, stride64. Per slot it
processes requested-state scripts (`$64FA`), callback (`$5E91`), then lifecycle.
Original allocation and this ordering are part of the oracle. A child allocated
in a later slot can initialize that same update; one allocated into a slot that
was already visited waits until the next update. Snapshot both active/requested
states; do not run all children simultaneously from an imagined stack snapshot.

`$A141` links upper `+$34` to lower support and lower `+$36` to upper predecessor.
`$9E4B` follows the lower object's current X/Y using signed `$A154` offsets at
`(headPhase+parameter)&31`. The head increments `+$1E` every follow; phase `+$1F`
advances every8 follow calls normally, every call in reaction state `$0D`.
Lower-support state `$0B/$0F/$13/$14` means detached: upper segment requests
`$09`, head requests `$0C`. Invalid/deleted support or dust state `$12` checks
own Y: below270 -> rise `$08`; above270 -> fall; exactly270 stays. A rigid
32-pixel stack would lose sway and sequential-update behavior.

Bottom state `$0A` moves first. At X>1810 it selects acceleration−2/256; at
X<=1802 selects+2/256. There is no clamp or velocity cap here. After movement:
`phase += 1 + ((playerX_low + parameter + bottomX_low) & 3)`, byte arithmetic.
Overflow triggers detachment; phase is not reset on `$0A` entry. Delays depend
on coordinates, player movement and inherited phase, not a universal timer.
Player X<bottom X throws left; equality throws right. Odd parameter selects
arc `$13/$14`; even parameter selects slide `$0B/$0F`.

Slide starts at zero velocity, accelerates by1/8 in mode0 and1/4 in modes1/2.
Arc X stays±1.5, configured Y−4.5; **on a floor launch at Y270, the first arc
callback's pre-move floor check immediately replaces this with−4.0**. The fixture
launch snapshot therefore has Y speed−4, not−4.5. Subsequent gravity is+1/8 and
floor rebounds are−4. This clarifies runtime motion without changing an art role.

The detached removal code compares bytes separately after movement:

- left: `X_low < $40 AND X_high < $07`;
- right: `X_low >= $80 AND X_high >= $07`.

Around the intended arena these remove left below1600 and right from1920, but
they are not monotonic full-word comparisons (e.g. right X2048 survives). Both
slide/arc callbacks are swept over all low bytes for X1280..2303. Keep this exact
rule in the fidelity baseline; any cleanup outside the reachable arena must be
an explicit adapter, never described as a widened viewport rule.

Normal mode1 fixture (static player1500/160, camera1664/96):

| Tick | Event |
|---:|---|
| 130..134 | Allocate parameters1,2,3; skip4; bottom requests rise. |
| 135..231 | Bottom rises from366 to270; strict `<270` completion. |
| 232 | Full head+3 stack, bottom in `$0A`. |
| 332/333 | Parameter3 requests/enters left arc `$13`. |
| 334/335 | Parameter2 requests/enters drop `$09`. |
| 356/357 | Parameter2 lands; dust child starts `$12`; new bottom `$0A`. |
| 446/447 | Parameter2 requests/enters left slide `$0B`. |
| 470/471 | Parameter1 lands, emits dust, becomes bottom. |
| 578/579 | Parameter1 requests/enters left arc `$13`. |
| 580/581 | Head requests/enters fall `$0C`. |
| 601 | Head reaches270 and requests `$01`. |
| 602..606 | Spawn new parameters1,2,3 below floor; skip4. |
| 607..704 | New bottom rises; linked stack returns. |

Right fixture has the same first detachment tick333, but enters `$14`; parameter2
then uses `$0F`. Mode2 throws4->3->2->1. Old thrown parameter1 and newly grown
parameter1 coexist at tick602: identify attachment by live links, never counts
or parameter identity. HP/mode/mux/phase survive regrowth; controller init state0
is not rerun. Dust spawns at X+10,Y unchanged through `$9C0F`.

## Geometry, vulnerability and player response

Approved visible head frames1/2 and segment frames3..9 all load object extents
X12/Y32. With ordinary Sonic8x24, closed overlap is `abs(dx)<=20`,
`-32<=dy<=24`. Player state `$0F` has X9, therefore reach21. Shared `$6328`
selects minimum penetration; vertical wins ties. All top/below/left/right,
boundary and outside cases are retained. Presentation registration (+1,+18)
does not enter this geometry.

Attached contact `$A0F5` clears own contact bits. The head advances its global
`+$27` selector modulo5; a head/segment only calls `$6328` when that selector
equals its parameter. Modes0/1 leave selector4 with no attached target; mode2
can cover all five. Segment contact is not tested every update, and the selector
also continues during head reaction. Detached `$A0E6` bypasses this mux.

All selected attached overlaps request sound `$AB` and X speed±4 away from the
object (equal X chooses+4), independent of posture. Only head state `$07` then
tests `$D503` attack bit1; any overlap class can request reaction `$0D`, request
sound `$B6`, and set player Y speed−4. No top-only bounce exemption or THZ phase
vulnerability exists. Segments do not lose HP or detach when attacked.
Health decrements only on `$0D` entry. Reaction remains contact-active for
push/hurt, but `$A063` has no head-hit branch. `$08/$0C` callbacks do not test
contact. Ordinary attached `$06/$09/$0A` are solid contact/hurt/rebound targets;
detached `$0B/$0F/$13/$14` are forced-hurt hazards.

Shared overlap disables contact for player hurt bit6 (unless object bit7
explicitly bypasses it; canonical `$51` flags do not), and object disabled bit6.
Player blinking bit7 alone does not suppress geometric head hits; the player
damage consumer handles invulnerability separately. Selector6 invincibility
is not an attack substitute for head HP damage. Attacking plus invincibility
can still damage the head.

Preserve the player/object update order. `$6328` writes `$D520` contact owner and
`$D521` classification high nibble. On the next player `$48BC` call:

- Attached nonattack, vulnerable Sonic: ordinary ring-loss/hurt; no rings -> death.
- Attached attack: shared classification rebound, above−3, below+0.5 (current
  player state9 suppresses below rebound), side leaves Y unchanged. Thus a head
  hit writes−4 immediately but can become−3/+0.5 on the next consumer call;
  side stays−4. The boss callback does not request a player spring state.
- Invincibility selector6 or active i-frames prevents shared damage/rebound;
  selected attached ±4 X still occurs. Head's immediate−4 remains on a valid hit.
- Detached overlap sets `$D3B0=$FF` regardless of attack posture. This bypasses
  the ordinary attacking-contact branch: attacking Sonic can be hurt. I-frames,
  hurt and selector6 still protect through the shared gates/consumer.

Ordinary ring-loss response: rings0, requested player `$1E`, flags add hurt/
i-frame/airborne, clear floor, invulnerability120; Y−4 (ceiling bit0 chooses+1),
X±1 from retained `$D523` side flag. The earlier callback's ±4 can therefore be
overwritten by hurt. No-ring response requests `$1F`, Y−5, clears floor, selects
death path/sound `$96`. Controlled no-ring rows stop at its IRQ wait `$062D`
after those writes; they do not claim to simulate the wait. Rocket-specific
shared hurt behavior remains documented in the existing footwear audit; this
boss adds no footwear exception.

Reaction holds54 updates (3+3 initial records, then eight 3+3 pairs). Head sway
runs faster throughout. The five-mux recontact sweep observes the next HP
decrement55..59 updates after reaction entry, depending on selector phase. This
is not THZ's reaction/cooldown rule; there is no separate two-update contact
cooldown in `$51`. The full-game attack driver happens to produce60-update hits.

## Arena, explosion and floor-gated defeat handoff

Camera target is `LOCKED_CAMERA(1664,96)`, `$9AED -> $0359/$59C5`:
pan1 pixel/update/axis using the shared camera adapter. Right limit1664 is
exclusive; original-game trace settles X1663,Y96, left limit1662. Camera-ready
gate accepts absolute per-axis difference<4. General player screen-edge clamp
still applies during fight; `$51` contains no THZ arena world-rectangle constants.
Preserve existing viewport semantics explicitly when adapting to widescreen.
Controller1856, floor270, acceleration thresholds1802/1810 and projectile byte
thresholds are world/runtime values, not arbitrary screen-width scalings.

Final HP decrement requests `$0E`. On its next visit the head spawns five
`$34/$08` puffs: offsets(-8,0),(+8,0),(0,-16),(-8,-24),(-8,-24), at relative
updates0..4 of state `$0E`. The duplicate last offset is canonical. Head alternates
frame1/blank; then16 repeats of2+2, four repeats2+4, four repeats2+8, then waits128.
The grounded clear callback is first eligible260 updates after `$0E` entry
(259 boundaries after the first post-entry boundary sample).
If floor is unset, the final224-update blank record repeats its `$9D26` callback
every update; there is no forced airborne clear or timeout.

Segment `$A0D1` reads upper predecessor's active state; `$0E/$11` requests own
`$10` and unwinds its caller, skipping remaining motion/contact for that call.
State `$10` waits16 updates then enters `$11`; four `$34/$04` puffs at
(-8,0),(+8,0),(0,-16),(-8,-24), then deletes. Lower segments see predecessor
`$11` during the same ascending scheduler pass. Controlled three-ball final-hit
timeline, relative to reaction entry: `$10` active for parameters1/2/3 at2/19/36;
`$11` at18/35/52; deletion at21/38/55. Detached balls retain live upper links and
may also respond to this cascade; the callback reads the pointed slot's state
without a type check. Never indiscriminately delete every object with parameter1.

`$1E:$9D26` / file `$79D26` requires `$D522` floor bit1. When set:

1. `$D280=currentCameraX`, `$D282=$0780` (1920), `$D27E=$0060` (96).
2. `$035C` clears pan mode/enables scroll; `$042B` enables camera movement.
3. Head type becomes `$FF`, placement token `+$3E=0`.
4. Allocate `$0A/$00` via `$032C`, then jump `$03F5 -> $4892`, requesting player `$20`.

All256 floor-flag combinations are swept. Only bit1 gates it. The timer is not
stopped by this chain. Original allocator may reuse the just-deleted head slot
for `$0A` in a controlled fixture; in the full-game trace it chooses another free
slot. Neither result implies conversion to THZ smoke `$0F`.

## Results and transition trace

The original-game trace naturally selects mode2/10HP after player terrain
projection; this is distinct from the controlled normal mode1 cycle. Attack
driver placements occur at `$1336` before player movement; pending contact and
rings are reset between synthetic contacts to isolate progression. All writes
stop when the head disappears. The original code then runs unmodified physics,
camera, `$0A` bonus/sparkles, clear flag, results tally and MGHZ1 loader.

| Trace milestone | Update / frame |
|---|---|
| Ten health-entry calls, HP10..1 | updates417,477,537,597,657,717,777,837,897,957 |
| HP0 reaction requests defeat | update957, sampled next boundary958 |
| Head active `$0E` | boundary959 |
| Grounded `$9D26`, request player `$20` | update1218 / frame2159 |
| Head gone, release limits `(1663,1920,8,96)` | boundary1219 |
| Player `$20`, bonus2358 | boundary1220 |
| `$83ED` sets `$D293` bit4 | update1341 / frame2282 |
| Main loop zone-clear `$1543` | frame2283 |
| Results call `$32F9` | frame2481 |
| Ring/time tally `$2D08` | frame2594 |
| Tally done `$2D54` | frame2913 |
| Advance `$15CE`, load request `$15DE` | frame3151; zone2/act0 |
| MGHZ1 loaded | final frame3508, player110/718, camera0/608 |

The clear flag retains canonical `playerX-cameraX >= $121` (right edge+33).
Observed flag call is player2207/camera1915, difference292 due to6-pixel movement
steps. Camera freeze occurs through the existing `$20` edge rule; do not replace
it with THZ boss-specific completion timing. During results there are no gameplay
`$1336` boundaries, so **frame numbers**, not update counters, give tally timing.
Fixed/page-bank filters protect hooks against same-address bank aliases.

## Support dependencies and implementation checklist

Required runtime support: `$12` existing HUD SAT slide; `$34` GPZ base `$96`,
parameters8/4 with original update-parity-selected scripts/delay; `$0A/$00` bonus
controller plus `$0A/$FF` sparkle children; `$51/$11` dust; original slot allocator,
state script engine, fixed-point motion, overlap/next-update hurt consumer, camera
pan/edge adapters, player `$20`, `$D293` zone-clear and existing results/zone load.
Numeric sounds: music `$8C`, contact `$AB`, head hit `$B6`, reaction `$B3`, ordinary
hurt `$A4`, no-ring death `$96`. Reuse approved graphics and current CRAM. `$0F`
is not a recovered `$51` defeat child. No replacement results assets are invented.

- Import canonical placement, approved art/dynamic selector14/palette13 and all
 21 numeric scripts/callback relationships; preserve the runtime X reassignment.
- Store controller, lower/upper live links, phase/counter, health, mode, mux and
 fixed-point fractional positions. Preserve requested vs active state ordering.
- Run children in the recovered scheduler/allocator order, including delayed
 activation after allocation into an already-visited slot and slot reuse.
- Implement source table sway, emergence/drop/regrowth and independent detached
 lifetimes; permit old/new equal parameters to coexist.
- Implement coordinate-dependent throw overflow, parity direction/state choice,
 mode-dependent slide acceleration and pre-move arc floor bounce.
- Use current gameplay anchors and extents, mux attached checks, forced detached
 damage and next-player-update shared response. Do not use sprite masks or air
 state as an attack predicate.
- Decrement health on reaction entry, allow all head contact classes, preserve
 54-update reaction and mux-dependent recontact. Keep faster reaction sway.
- Implement upper-state-driven defeat propagation, exact puff spawns, dust,
 grounded-only handoff, camera release, bonus/sparkles and player `$20` convergence.
- Document each widescreen camera/clamp/lifetime adapter separately. Keep the
 256-pixel original-game fixture as the fidelity control.
- Compare POC against the numeric cycle/contact/defeat fixtures, then request
 James's Windows gameplay acceptance at a coherent implementation checkpoint.

## Validation and remaining limits

18 focused tests pass with the verified ROM, including complete regeneration of
both new caches and the approved composition fixtures. Sweeps include all256
mode low bytes, 5,922 closed geometry/classification samples (player widths8/9),
all25 mux combinations, 960 head posture/power/mux/class/speed cases, 560 attached
contact cases, 84 detached cases, 64 ordinary hurt variants, 360 throw-overflow
cases, 4,096 split-byte removal samples, 121 camera-ready samples, all256 floor
flags, all health decrements1..10 and five earliest-recontact phases.

No art conflict or unresolved core state/contact/health/clear gate was found.
Evidence limits remain explicit: the full-game fight is synthetic/update-aligned,
not human observation; widescreen acceptance and stress under slot exhaustion,
cross-slot reuse outside captured sequences, long gameplay histories and exact
hardware IRQ/VDP timings are not certified. No POC rollout or Windows acceptance
is implied. Existing results-screen asset deferrals remain separate from the
proven runtime completion path.

## AGENTS candidate updates (do not edit root during this audit)

- Dedicated `$51` runtime audit closes modes0/1/2 (HP5/8/10), linked phases,
 bottom-up throws/regrowth, contact mux, detached hazards, defeat propagation and
 `$9D26` grounded handoff through original results/MGHZ1 transition.
- `$51` head/segment geometry is X12/Y32 (ordinary Sonic reach±20, Y−32..+24).
 Only head state `$07` attack-bit contact damages; all four classes can hit.
 Head reaction54 updates, earliest re-decrement55..59 by five-slot mux phase.
- Keep immediate head Y−4 distinct from next-update shared attack rebound
 (above−3/below+0.5/side unchanged); detached attacks still request forced hurt.
- GPZ camera target1664/96, exclusive right limit settles1663; grounded clear
 releases right limit1920/bottom96. Timer continues. No THZ arena/health/cooldown
 assumptions and no `$0F` boss conversion.
- Reuse approved art package unchanged; consume the runtime fixtures after review
 and Research main integration. GPZ3 boss implementation/Windows acceptance remains
 a separately assigned milestone.

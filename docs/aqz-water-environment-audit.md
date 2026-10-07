# Aqua Planet A2 — water, environment and player runtime

Research base: `d1661de8b44b7904dd1c250c6fa53b8f4c24b735`. Europe v1.2,
524288 bytes, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Research only; no POC changes. A1 Manager technical review passed and James
explicitly approved **all AQZ A1 boards** on 2026-10-07. Approval is recorded in
the reproducible art manifest. Original PNGs remain under `build/aqz-approval`.

The machine contracts and input/output oracle vectors are
`data/rom-cache/aqz/water-runtime.json`; complete original-game traces are
`water-game-checks.json`. The foundation manifest links and embeds the contracts.
Source regions record bank, CPU, file, length and SHA-256; tool hashes use UTF-8
normalized newlines. No external ROM exports, modified terrain-ring probe, ROM
dump, synthetic artwork or POC implementation was used.

## Water ownership and crossing

Only zone 4 acts 0/1 call the water updater. The WORLD lines are 568 and 788.
AQZ3 has no updater/controller. `$2934` clears act RAM at `$297E`, loads act data,
then calls `$2A2E`: allocate `$0D` parameter 0, then 1, then set `$D450=768`.
Normal restart clears `$D300..$DBBF`, including all objects, water flags and both
air counters. A full allocator silently drops a controller; there is no retry.

Type `$0D`, bank `$0C`, table `$9D9B`, has three entries. Reachable states are 0
and 1; state 2 aliases 1 but has no AQZ requesting path. State 0 sets Y to the
act line, art base `$A0`, keepalive bit 1 and requests state 1. It does **not**
publish `$D450`. On the next object pass both `$9DDD` callbacks first move their
strip X, prepare raster using current `$D450`, then publish their identical Y.
Parameter 0 therefore first prepares from 768 and publishes the act line;
parameter 1 sees that updated line. Both own the same redundant gameplay write.
Their parameter difference is strip presentation, not exclusive water authority.
The original lifecycle may mark them asleep, but keepalive prevents deletion
and their callback never gates on asleep. Death/transition follows shared RAM
clear; no persistent controller survives into AQZ3.

`$4BC0` compares unsigned player **anchor Y** to `$D450`. Equality is submerged.
Below/equal sets `$D443=$FF`; strictly above clears it. Only a zero-to-submerged
flag transition attempts `$0E` parameter 0. There is no exit splash, velocity
scaling, floor/airborne, latch/input, animation, requested-state or sound write
in this crossing routine. Allocation failure still sets the water flag.

Every submerged call additionally checks nonnegative Y speed, attack bit 1 and
absolute **signed X-speed high byte** at least 4; if all qualify it sets Y speed
to `−3.0`. This is a repeated gate, not an entry-only bounce. Negative fractional
X uses its high byte and is not equivalent to testing `abs(full speed)>=4`.
The sweep covers line −5..+5, both previous flags, five Y speeds, seven signed
X speeds and both attack values (1540 original calls). Player bytes other than
Y speed remain unchanged. Crossing precedes movement/terrain, so the flag can
lag the completed-update Y position by one update.

## Player physics and accepted contract reuse

Numbers in this table are fixed-point units `/256` per update. Positive gravity
is applied only when `$4097` takes the airborne branch. Grounded motion bypasses
gravity. The floor-support override **after** gravity sets Y speed to 7, or 9 on
surface `$0A/$0C`; it overrides the underwater cap. X maximum `$D373` is **not**
halved. Full signed direction tables and every relevant state are machine-readable.

| Runtime path | Dry | Underwater | Source / exception |
|---|---:|---:|---|
| Ordinary airborne jump/fall/roll walk integration | gravity 48, cap 1792 | gravity 24, cap 1024 | `$40BE..$4124` |
| Strong spring `$0B` | gravity 24, cap 1792 | gravity 12, cap 1024 | same source, state branch |
| Attack launch `$1B` | gravity 36, cap 1792 | gravity 18, cap 1024 | same source, state branch |
| Normal jump / held-jump launch | −1088 | −832 | `$45ED/$3901`; hold window unchanged |
| Walk/run `$05/$06`, same-direction acceleration | 16 | 2 | doubles near zero `abs(vx)<128` |
| Brake `$07/$08`, same table direction | 32 | 4 | signed opposite entry retained |
| Jump/fall/spring `$0A/$0B/$0E`, same-direction acceleration | 16 | 4 | neutral drag remains 16 |
| Roll `$09`, charge/release `$0F/$10` | accepted signed entries | identical entries | neutral roll drag 5; release ±7 unchanged |
| Rocket `$11` horizontal thrust | 16 | 2 | doubles near zero; max X 7 |
| Rocket `$11` vertical | Up/Down ±64, neutral ±32 | same | bypasses gravity; exact signed-high-byte caps in shared vectors |
| Hurt `$1E` | gravity 48, cap 7 | gravity 24, cap 4 | initial shared hurt launch unchanged; shared water updater continues |
| Loops `$0C/$0D/$13` | route integration | same | no gravity/water-updater call; flag and air timer latched |
| Act-clear `$20` | vx +16 to high-byte 6; vy zero | same | `$0C:$83A6`; no terrain/water timer/ring probe |
| Air recovery `$25` | frozen for 16 calls | same | resets coarse timer, then requests fall `$0E` |
| Death `$1F` | airborne gravity 48/cap7 | latched water gravity24/cap4 | no crossing, terrain, damage or air updater |
| Drowning `$28` | fixed vy128 then death path | latched water flag | screenY≥216 sets death flag; subsequent `$4097` still applies cap |

`$4141` selects water tables `$441D/$449D` versus dry `$429D/$431D`; neutral
`$439D` and slope `$459D` are shared unchanged. Direction entries are signed;
use the cache rather than a blanket multiplier. The oracle covers all 55
state indices, both flags and five X speeds/input directions. For state≥30
the ordinary control function returns without changing acceleration: retained
fixture sentinels are **not** physics constants. Such states use their own callbacks.

Underwater walking skips `$47A9` run selection and the special strip-fall branch
at `$37A4`. Sonic crouch `$3713` bypasses the jump-fly selector while submerged.
Spin dash release and mapped/terrain spring launch setters have no water branch.
Accepted hurt/lost-ring scatter, boosters, crumble, breakables and terrain
rings remain unchanged; their handlers do not read `$D443`. Loop route callbacks
also do not read it or call the updater. Old helpers `$4B94` (halve maximum) and
`$4BA5` (quarter motion) have **no pointer references anywhere in this ROM**;
they are not implementation contracts. No loop slowing or loop drowning updates
may be inferred from their existence.

AQZ1's actual mapped Rocket monitor at `(1664,430)` is activated through the
original object/reward scheduler; selector `$04`, state `$11` and duration 300
result. The same live reward is carried through controlled water entry and exit.
Separate fixtures cover both acts' Rocket motion. Shared retained-ring damage
uses `$48F7`'s state `$11` branch regardless of water; it bypasses ordinary
ring-loss/no-ring-death selection and then uses the existing hurt response.
The updater still runs during Rocket, so it does not grant drowning immunity.

## Air timer and drowning

`$4B46` runs on the shared movement path. While submerged it increments `$D444`;
if the resulting byte is at least 120, it clears the byte, attempts a small
player breath bubble (`$0C` parameter 3) when refresh register R bit 2 is clear,
then increments `$D445`. Exactly 11 allocates `$32`; exactly 17 requests `$1F`.
No other warning threshold exists. Entry resets neither counter. Exit and air
recovery clear **only** `$D445`; the partial `$D444` survives. A byte 255 wraps
to 0 and does not increment coarse time. The cache sweeps fine 0/118/119/120/
254/255, coarse 0/10/11/15/16/17, both sides and full/free pools (216 cases).

Zeroed counters yield `$32` at updater call 1320 and `$1F` at 2040. These are
updater calls, not unconditional wall-clock frames. Loops, stationary spin dash
charge, air recovery, clear and death callbacks pause the updater. A failed
countdown allocation is not retried; request `$1F` still occurs but the missing
countdown cannot execute its tail. Do not invent an allocation-failure fallback.

Type `$32`, bank `$1E`, table `$94C6`, has states 0/1. Initialization uses player
X/Y−34 and keepalive; steady follow uses X/Y−40. Frames 21..16 each last 120
object callbacks, sound `$B5` at each new numeral; animation counter bit 2 controls
the hide flag. `$D445==0` deletes it; merely clearing water flag does not delete
it until the updater resets coarse time. Terminal frame 1 calls `$9555` immediately:
request `$28`, set player airborne flag, clear flags4 and floor, zero Y speed
and X acceleration, sound `$96`, set camera bottom bound to current cameraY,
delete the countdown. This tail is one object pass after `$1F` in the whole-game
zero-counter control. `$28` callback `$3BFB` sets Y speed 0.5 until screenY≥216,
then sets `$D293` bit2 and follows the shared death/restart path. It bypasses
ordinary hurt/lost-ring scatter. The held ring count is not cleared by the
timer or terminal callback. The fixture continues through a real act restart,
where water flags, fine/coarse timers and objects are cleared.

## Bubbles and splash

Mapped `$0C` parameter 0 emitters: AQZ1 `(768,686)`, AQZ2 `(2496,942)`.
Bank `$0C`, table `$9CAC`, all four states are accounted for. Initializer `$9CF6`
sets art `$8E/$8E`, flags3 bit7, Y speed −0.75 and requests parameter+1.
Parameter 3 instead requests state 2 and overrides spawn to player X/Y−16.
State 1 is an inert emitter: durations 128/120/112, commands spawn parameters
1/1/2, repeat every 360 callbacks. A zero-object scheduler trace emits at calls
130/250/362 then 490/610/722. Command4 uses the eleven-slot allocator `$5EE1`
(`$D700..$D980`); failure advances without a retry. Player breaths use the
separate sixteen-slot allocator `$5E9C`.

State 2 is a small bubble, frame1; it never checks player contact. State 3 uses
frame1 and 2 for 16 callbacks each, then frame3 repeating 224. Only frame3's
`$9D39` callback tests contact, on frame-counter phases 1/2/3 (not 0). It uses
shared closed overlap `$6328`: Sonic8×24 and bubble8×16 give `abs(dx)<=16`,
playerY−bubbleY in −16..24. Flags3 bit7 permits contact even with hurt Sonic
and prevents damage. It requests `$25` and marks the bubble FE. The callback
itself has no parameter/frame predicate; **script reachability** restricts this
path to the large bubble. State `$25` plays `$AE`, displays player frame54 for
16 callbacks, clears coarse time via `$836F`, then requests fall `$0E`. There is no player-state restriction on large-bubble
contact: it can interrupt Rocket state `$11`; the air script requests ordinary
fall, without a special Rocket-resume path. Terrain-ring probing is skipped
during the air script because it does not call shared movement.

Rising bubbles use constant vy −192/256 and horizontal acceleration ±4/256
selected by frame-counter bit4, then shared 24-bit integration `$0338`.
Asleep bubbles remove immediately. On 3/4 `$D2E2` phases they also remove when
`objectY − extentY < WORLD waterline`; equality survives. Mapped inert emitters
do not run this check. FE becomes FF next object pass and is cleared on the
following pass; mapped placement tokens use the accepted recreation system.
The oracle covers 5376 contact/phase/sleep/hurt controls; only the large callback
restores air. The first drowning control at the natural AQZ1 emitter repeatedly
received air; the final drowning fixture deliberately uses another open column.

Type `$0E`, table `$0C:$9F8B`, is presentation only. State 0 samples player X
and **WORLD waterline Y**, sets art `$A4` and flags4 bit0, requests 1. State 1
plays `$AF`, frames1/2/3 four callbacks each, then frame0 immediately deletes
through `$0362`. Original scheduler: frames begin at2/6/10, FF at14, zero at15.
No movement/contact/player mutation; only entry creates it. Pool failure drops
the effect while crossing succeeds.

## Raster, palettes and independent effects

`$0C:$9DED` enables split presentation exactly when
`cameraY < WORLD waterline <= cameraY+192`. `$D132` receives line−cameraY;
`$D131=$FF`. Equal cameraY is the fully-submerged branch, not raster line0.
Line192 is enabled; line193 is disabled. Offscreen branches only request a
palette when `$D131` was nonzero: water above/equal camera requests `$30/$31`
(decimal48/49); water below192 requests `$19/$0A` (25/10). Once disabled these
branches do not repeat palette requests. Preserve this stateful behavior.

Vectors `$040A/$040D` target `$1C9B/$1CA8` and write VDP **register0**, `$36/$26`
to enable/disable line IRQ; enabling is guarded by `(D492 & CF)==0`. Vblank
`$04EF..$0513` additionally writes `$D132` to R10 and sets R0 bit4 when D131
is set and palette state permits. The SMS line-counter reload/underflow relation
is retained; a POC must not treat the register value as an invented pixel cut.
IRQ `$0652` copies 32 bytes at fixed `$0688` directly to CRAM when D132 !=FF
or the water flag is set, clears R0 bit4 and sets D496. A guarded vblank restores
the saved above/current palette `$D472[32]` through `$0627->$1CBD`, clearing D496.
Original-game checks compare live CRAM at IRQ return and palette restore.

**The fixed split-IRQ palette is not the indexed `$30/$31` palette.** Their
CRAM color lists, hashes and differing entry indices are cached separately. Most entries exchange
red/blue components, with an additional sprite-entry0 difference; no intent is
inferred. A1 underwater-palette boards do not simulate the split IRQ. Keep both
ROM sources in the POC-facing package, not one generic underwater palette.
This is a source finding; no new art composition is introduced.

Strip movement `$9EFE` increments its index before lookup, wraps at16, adds
offset to cameraX. Table `$9F2B` is 8..248 by16; `$9F4B` rotates it by eight
entries. Both strips stay at WORLD waterline. There is no refraction or horizontal
scroll write in this IRQ; this routine provides palette switching and sprite
strip movement. Existing scrolling/background machinery remains separate.
Controllers have no boss-active pause. Effect5 (every3, pauses on D44E) and
effect11 (16 frames/every8, continues on D44E) retain A1 VRAM destinations and
mapping attributes. Neither changes priority or palettes. Raster CRAM changes
can alter their visible colors along with other graphics; they do not merge
into one effect or acquire gameplay water semantics.

## Order, fixtures, viewport and reproduction

Canonical order is camera/background `$4C90`, player animation, player callback
(water test and air timer first on shared path), screen-death check, control,
X/Y integration, terrain floor/sides/ceiling/rings, damage, reward; then 19
sequential object slots (animation, callback, lifecycle); mapped creation every
fourth D2E2 pass. Split rendering `$220E/$1027` moves into main path `$16EF`,
while normal rendering occurs in vblank. Vblank effects and raster IRQ can
interrupt the main path; they are not additional physics updates.

Whole-game fixtures cover both acts: entry, rising exit, repeated crossings,
2040-update drowning, terminal `$28`/death/restart, large-bubble air recovery,
Rocket entry/exit, camera delta0/1/192/193 and independent replay. AQZ1 also
covers its real mapped monitor reward followed by crossings without restoring
the reward state. Player/camera placements, held drowning anchor, bubble slot
and queued-reward controls are explicitly labelled synthetic; canonical layout
and original code/scheduler remain intact. Exact exported CPU state, including
prefix, EI shadow and frame_tick, is restored with RAM/VDP/harness state.
No register-only restore or NOP repair is used.

Viewport classes: waterline `WORLD(568/788)`; raster `EDGE(TOP,waterline−cameraY)`
within original192-line domain; strip X `EDGE(LEFT,8..248)` across canonical256;
bubble contact and countdown offsets `PLAYER_DIST`; drowning camera lower bound
`LOCKED_CAMERA(currentY)` and death screen test `EDGE(TOP,+216)`. No widescreen
or view-height substitution is designed here.

Reproduce with local verified ROM:

```powershell
.venv\Scripts\python.exe tools/aqz_water.py "..\source\Sonic Chaos (Europe).sms"
.venv\Scripts\python.exe tools/aqz_water_game.py "..\source\Sonic Chaos (Europe).sms"
.venv\Scripts\python.exe tools/aqz_foundation.py "..\source\Sonic Chaos (Europe).sms"
.venv\Scripts\python.exe tools/aqz_art_approval.py "..\source\Sonic Chaos (Europe).sms"
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_aqz*.py" -v
.venv\Scripts\python.exe tests/verify_cache.py "..\source\Sonic Chaos (Europe).sms"
git diff --check
```

Remaining scope: A3 `$3F` platform paths, A4 `$3C/$3D` enemies, A5 `$59..$5D`
boss/arena/clear. No water contract is inferred for those excluded systems.
Hardware raster timing and human visible comparison are not supplied by the
software harness; the register sequence and CRAM sources are byte-verified,
while actual display timing remains hardware/Windows presentation acceptance.
This limitation is not a replacement of the published canonical register rules.

AGENTS candidates: record A1 approval and A2 water closure after Manager review;
warn that air time counts updater calls, partial time survives exit/recovery,
loop/death callbacks latch water; keep split-IRQ and offscreen water palettes
separate; retain complete CPU-state snapshots. Do not edit root AGENTS here.

Validation: 17 focused AQZ tests passed, with 31,443 enumerated evidence checks/vectors (A1 13,062; A2 18,381), plus 10,351 live CRAM copy/restore assertions. The 5,596 A2 original-game trace rows include real restart and mapped Rocket reward controls. All 32 approved PNG hashes were unchanged after regenerating the boards. Full verify_cache and git diff --check passed before commit.

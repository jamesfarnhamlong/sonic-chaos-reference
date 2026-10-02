# Player attack posture and badnik interaction audit (`$D503` bit 1, `$D532`, types `$21` / `$27`)

Research only; the POC was not touched. Evidence labels: **BYTE-VERIFIED** (disassembled routine bytes / whole-ROM byte scan), **CONTROLLED**
(original Z80 routine run on `tools/oracle.py` with explicit RAM), **EMULATED** (whole original game in `tools/sms_frame_harness.py`),
**DECODED**, **UNRESOLVED**.

Machine-readable result: `data/rom-cache/player-attack-badnik.json`. Regenerate/verify:

```sh
python tools/player_attack_badnik.py path/to/SonicChaos.sms            # writes the cache (about two minutes)
python tools/player_attack_badnik.py path/to/SonicChaos.sms --check    # byte-compares the cache with a fresh build
python -m unittest tests.test_player_attack_badnik                     # cache tests + ROM-backed random sweeps (SONIC_CHAOS_ROM)
```

## 1. Answer in one paragraph

Sonic "attacks" when **`$D503` bit 1 is set, or the power-up `$D532` equals 6 (invincibility)**. Nothing else: not airborne (`$D503` bit 0), not the
state number, not the sprite. Bit 1 is written by about twenty setters, so airborne is neither necessary (grounded roll, spin dash) nor sufficient
(upright spring flight, post-apex fall, ledge fall are airborne and **not** attacking). The attack decision is split in two: the **player's own
handler `$48BC`** decides damage versus rebound for every object whose overlap routine raised the contact flag `$D520`; each **object** decides
independently whether *it* dies (`$27` through `$5F3D`, `$21` in its own tail, the monitor and the boss through bit 1 only).

## 2. `$D503` (player movement byte) - BYTE-VERIFIED + CONTROLLED

| Bit | Meaning proved | Evidence |
|---|---|---|
| 0 | airborne | every launch/fall setter sets it; landing clears it |
| **1** | **attack posture** | read by `$48BC`, `$5F3D`, type `$21` tail, monitor `$A17A`, spike side bump `$AD34`, breakable blocks `$6AE3/$6B2C`, boss; set/cleared as in 2.1 |
| 3 | state-switch lock read by the animation engine (`$6502`); no player code sets it | scan |
| 6 | hurt/dying: `$6328` returns before any contact, `$48BC` takes `$4A2E` | `$4942`, `$3BF4/$3BFF` set it; landing `$45CE` clears it |
| 7 | invulnerable (post-hit blink, timer `$D3B1` = `$78`, or `$0C` for state `$1A`): contact is computed but `$48BC` takes `$49F7` | `$4942`, invincibility pickup `$4B24`, state `$1A` entry `$8313`, type `$05` child |
| 2, 4, 5 | not referenced by player code | scan |

### 2.1 Who sets/clears bit 1 (every site; `setter_effects` runs each setter against all 256 input values)

| Effect on bit 1 | Setter (entry) | Requested state |
|---|---|---|
| **set** | `$45ED` jump (needs bit 0 clear, state not `$11`), `$4699` (rolling off a ledge / jump without impulse), `$4701` spin-dash charge, `$4719` spin-dash roll, `$47DC` roll (when X speed != 0), `$47FB` ramp launch, `$482D` diagonal spring, `$4849/$4868` horizontal spring, `$3DA5` loop-exit launch, `$7654` terrain launch, `$4B22` invincibility pickup (HL write), `$4C7D` carried state (HL write) | `$0A`, `$0A`, `$0F`, `$10`, `9`, `$1B`, `$1C`, `9`, `$0A`, `$10`, - |
| **clear** | `$45B3` stand, `$45CE` landing (also bits 0 and 6), `$463C` fall `$0E` (**not** when the current state is `$0A`), `$4663` state `$14`, `$4680` state `$1D`, `$46BB` state 4, `$473C` state `$18`, `$4775` state `$11`, `$47A9/$47B6/$47C9` states 6/7/8, `$480C` upright spring, `$39CE` peel-out wall hit | `1`, `5`, `$0E`, `$14`, `$1D`, `4`, `$18`, `$11`, `6/7/8`, `$0B` |
| **untouched** | hurt `$4942`, death `$4984`, act clear `$4892`, state 3 `$46B0`, peel-out `$46CE/$46E2`, loop entry `$3EAB/$3EE1/$3EF7`, twist entry/exit `$95EC/$978F` | `$1E`, `$1F`, `$20`, 3, `$15/$1A`, `$0C/$0D/$13`, `$22`, 9/`$0A` |

### 2.2 Timeline rules (EMULATED + BYTE-VERIFIED)

* **Persistence.** Bit 1 only changes in the setters above. Loops and the twist inherit it; the **twist exit requests state 9 / `$0A` without setting bit 1**, so a ball state can be non-attacking if Sonic entered running.
* **Landing.** `$45CE` clears bits 0, 1, 6 in the callback of the landing update; `$D501` still reads `$0A` for that one update.
* **Apex / fall.** The ordinary jump never reaches `$463C` (it returns when the current state is `$0A`): bit 1 stays set through ascent, apex and descent until landing (emulated 53 updates, vy -1040 .. +880, all `$D503 = 3`). The spring apex `$393B/$3955` and every other fall (ledge `$6C7C`, state `$11` end, scripted movement) calls `$463C`, which sets bit 0 and **clears bit 1**.
* **Rolling off a ledge** (`$6C7F`) goes to `$0A` with bits 0 and 1 (still attacking); **walking off** goes to `$0E` with bit 1 clear.
* **Damage / death** do not clear bit 1 (they set bit 6, which suppresses all contact); the next landing clears it.
* **Two-phase state change.** A request written by the callback of update *n* changes `$D501` (the animation script/frame) at the start of update *n+1* (`$64FA`), but its `$D503` effect is immediate. Natural play therefore contains one-update windows where the frame contradicts the bit: jump start (`$D501 = 5/6`, requested `$0A`, `$D503 = 3`: **unrolled frame, attacking**; 3 occurrences in 2,144 recorded updates) and landing (`$D501 = $0A`, requested 5, `$D503 = 0`: ball frame, not attacking).

## 3. `$D532` - BYTE-VERIFIED + CONTROLLED

`$D532` is the **player power-up selector**, written in exactly five places (`$48FF`, `$4AA0`, `$4AE8`, `$4B13`, `$4B3C`), read in five (`$48CA`, `$4A74/$4A8F`, `$5F43`, `$B2DD`, `$998A`, `$98EC`).

| Value | Source | Effect | Timer `$D44C` |
|---|---|---|---|
| 3 | monitor reward bit 2 (parameter 3) `$4B13` | X speed cap forced to `$0600` every update | 900; **not** cleared at expiry by `$4A74` (UNRESOLVED where it ends) |
| 4 | reward bit 3 (parameter 4), only when `$D500 == 1` `$4AE8` | requests state `$11` | 300 (`$1770` in zone 8); cleared at expiry or when damaged in state `$11` |
| **6** | reward bit 5 (parameter 6) `$4B3C` | **invincibility**: `$48BC` ignores every contact, `$5F3D` and type `$21` convert regardless of bit 1; pickup also sets `$D503` bits 1|7 and spawns the type `$05` star aura | 600; cleared at expiry |

So the "magic `== 6`" in `$5F3D` / `$B2D5` / `$48CA` is not enemy-specific: it is the invincibility power-up substituting for bit 1. The **monitor and the boss do not test it** (bit 1 only).

## 4. Update order (EMULATED, PC hooks; BYTE-VERIFIED)

```text
update n:
  $361D player:  $64FA animation engine (applies request from update n-1 to $D501)
                 $5E91 state callback -> $3FEF: input, X/Y movement, terrain $690B, $48BC (consume D520/D3B0 from update n-1), jump request $45ED
                 $4A74 power-up timer
  $5DD1 objects: each callback: $6328 overlap (sets D520 = slot id for objects with +3 bit 7 clear, D521 high nibble), $5F3D/$B2B2 gate, $5F54 conversion, D3B0
```

* A badnik always sees the bit left by the player callback of the **same** update (movement already applied).
* The player's rebound/damage for an overlap in update *n* is applied in update *n+1*, **after** that update's movement (observed: bee converted in update 4, player `vy` -768 in update 5).
* `$D520`/`$D3B0` persist until `$48BC` consumes them.

## 5. The shared player-side contact rule `$48BC` - CONTROLLED (6,144 cases, model mismatches 0)

Priority order: `$D503` bit 7 -> no processing; bit 6 -> `D520` cleared only; `$D532 == 6` -> `D3B0`, `D520` cleared; **`D3B0 != 0` -> damage whatever bit 1 is**;
`D520 == 0` -> nothing; `D520 != 0` with bit 1 -> rebound by the high nibble of `$D521` (bit 4: `vy = +0.5` unless the current state is 9; bit 5: `vy = -3.0`; neither: none), else damage.
Damage is rings -> scatter + state `$1E` (bit 6|7, `$D3B1 = $78`), no rings -> death `$1F`; state `$11` is hurt without a ring test.

`$D521` high nibble comes from `$6328`'s minimum-penetration axis. For a type `$27` box (CONTROLLED, 21,756 cases): player in `dy -14..-1` -> bit 5 (above, **-3.0**); `dy +7..+24` -> bit 4 (below, **+0.5**); the left/right bands -> bits 6/7 (no rebound).

## 6. Per-object rules

`$6328` (shared) clears `+$20`, keeps `+$21` high nibble, returns for object bit 6 / player bit 6, skips `+$20` when player bit 7 is set, and **sets player `D520` only when the object's `+3` bit 7 is clear**. Objects that set bit 7 at init (`$10`, `$18`, `$19`, `$1B`, `$21`, `$28`, `$50`) therefore never feed `$48BC`; `$27` (and the unbanked rest) do.

| Type | Contact routine | Attack test | Non-attacking contact | Defeat | Rebound |
|---|---|---|---|---|---|
| `$27` flying bee (THZ1 x3, THZ2 x4) | `$033B` at the start of every state callback; contact -> `$0323` (`$5F3D`) and the callback **returns before moving** | `$D532 == 6 || bit 1` | callback requests nothing, **but `$48BC` hurts via `D520`** | `$5F54` to `$0F` | -3.0 above / +0.5 below / none side, via `$48BC` |
| `$21` ground patrol (THZ1 x6, THZ2 x5) | `$B2AF` -> `$033B`, tail `$B2B2` | `$D532 == 6 || bit 1` | `D3B0 := $FF` | `$5F54` (side/low only) | top contact (`playerY <= objY-4`) is a stomp bounce **before** the attack test: `vy $F940`, state `$0B`, bit 1 cleared, badnik survives; side defeat: none |
| `$10` monitor | `$034D` (`$5FA0`) | **bit 1 only** | solid, no damage | reward + `$0F` | -4.0 from above (none in state 9), +2.0 and monitor up from below |
| `$1B` moving spike | `$ACFD` | side bump reads bit 1 + floor flag | top: `D3B0 := $FF` regardless of bit 1 | - | - |
| `$50` boss (THZ3) | `$6328` | bit 1 only | `D3B0 := $FF` + 2-update cooldown | 8 hits | docs/object-50.md |

CONTROLLED sweeps: type `$27` 21,756 cases (box `dx -17..17`, `dy -14..24`; conversion exactly `overlap && (bit1 || D532==6)`; the callback **never** writes `D3B0`), type `$21` 24,168 cases (box `|dx| <= 19`, `dy -26..24`; stomp `dy <= -4` for **any** posture; convert `dy -3..24` with bit 1/`D532 == 6`; else `D3B0`), monitor 12,834 cases (bit 1 mandatory; `D532 == 6` alone breaks nothing; airborne-only breaks nothing), `$5F3D` 4,608 cases (all 256 `$D503` values x `$D532` 0..8; only bit 1 and the value 6 matter).

## 7. The parked type `$27` observation - classification **B** (with D as a side finding)

*Can the ROM make Sonic destroy a bee from above while visually unrolled?*

| Situation | ROM result (EMULATED forced-pose trials) |
|---|---|
| normal jump falling onto it (`$D503 = 3`) | bee converted at update 4, Sonic rebounds `vy -768` at update 5, **attack bit persists** |
| upright-spring fall `$0B` / falling `$0E` after apex or ledge (`$D503 = 1`) | **not converted; Sonic is hurt** (rings 16 -> 0, state `$1E`) |
| diagonal spring flight `$1C` (`$D503 = 3`) | converted + -3.0 rebound (attacking by design) |
| invincible `$0E` or on foot (`$D532 = 6`) | converted, no damage |
| jump start frame | `$D501` still 5/6 (unrolled frame) with bit 1 set for one update: the only canonical "unrolled but attacking" case (plus invincibility) |

The POC predicate `global.playerJump = (move & 3) != 0` is true in `$0B` and `$0E`, which the ROM does not treat as attacking: of 2,144 emulated updates the legacy predicate is true on 1,188 and the canonical one on 724; **464 updates (all in `$0B`, `$0E`, plus boundary updates) are false positives**. Classification **B: POC `global.playerJump` false positive**; the one-update jump-start window is canonical (C-class timing, 1/60 s). **D (enemy-specific POC mismatch):** the POC says "ordinary `$27` overlap requests no damage"; the ROM callback indeed requests none, but the shared `$D520` path hurts a non-attacking Sonic (emulated: rings 16 -> 0). The Windows run itself was not replayed (needs the POC build).

## 8. Canonical attack matrix (CONTROLLED setter column; EMULATED timelines)

| Situation | State | Set/cleared by | Bit 1 | Badnik sees attacking |
|---|---|---|---|---|
| standing / walking / running | 1 / 5 / 6 | `$45B3`, `$45CE`, `$47A9` | cleared | no |
| crouch / look-up | 4 / 3 | `$46BB` / `$46B0` | cleared / kept | no |
| jump ascending / apex / falling | `$0A` | `$45ED` | set (no apex change) | **yes** |
| landing request (callback of landing update) | `$0A -> 5` | `$45CE` | cleared at once | no (ball frame, one update) |
| rolling | 9 | `$47DC`, horizontal spring, slope `$6A02` | set | yes |
| spin-dash charge / roll | `$0F` / `$10` | `$4701` / `$4719` | set | yes |
| peel-out charge / run | `$15` / `$1A` | `$46CE` / `$46E2` | kept (clear in an ordinary charge; aura object only after a very long charge) | no (UNRESOLVED long hold) |
| ramp launch | `$1B` | `$47FB` | set | yes |
| upright spring (`$26`, terrain) | `$0B` | `$480C` | **cleared** | **no** |
| spring apex, ledge fall | `$0E` | `$463C` | cleared | **no** |
| diagonal spring | `$1C` | `$482D` | set until apex | yes |
| horizontal spring | 9 | `$4849/$4868` | set | yes |
| loop `$0C/$0D/$13`, twist `$22` | - | no D503 write (exit launch `$3DA5` sets) | inherited | inherited |
| hurt / death | `$1E` / `$1F` | `$4942`, `$4984` | kept (bit 6 disables contact) | contacts ignored |
| act clear | `$20` | `$4892` | kept | n/a |
| invincible | any | `$4B1D` (+ `$D532 = 6`) | set | yes |

## 9. Non-attacking contact (CONTROLLED + EMULATED)

`$27` **damages** (via `D520`) - correcting the older reading "no damage"; its callback stalls movement on every overlap update. `$21` side/low contact damages via `D3B0`; top contact never damages. Invulnerability (bit 7, `$D3B1`) suppresses both. `$26`, `$28`, `$09` do not damage.

## 10. POC consumer migration table (read-only, POC `7799c345`)

See `poc_consumers` in the cache (17 rows). Summary: **retire** `global.playerJump` as an attack predicate (`SCR_chaos_adapter.gml:30`); consumers to move to the canonical bit (`chaosAttackPosture`, plus `powerInv` = `D532 == 6` where the ROM does): type `$27` (`Step_0.gml:58`), type `$21` (`:73`), sample-damage (`SCR_chaos_adapter.gml:425`), block `$47` step (`:242`); type `$10` uses bit 1 only (`:69`); the stomp (`:310`) and legacy spring (`SCR_physics_spring.gml:23-36`) must stop setting an attack predicate; type `$21` defeat should not call `SCR_physics_jump_objects()`; type `$27` needs ROM-faithful contact damage and the -3.0/+0.5 rebound; physics gates (`SCR_physics_speed`, ramp, `OBJ_player_char/Step_0`) are **airborne/state** consumers and stay; `playerSuper` has no ROM counterpart; `SCR_badnik_death`/`SCR_monitor_collisions` are legacy sample objects.

## 11. THZ3 dependency census (read-only)

All 77 THZ3 terrain blocks already appear in THZ1/THZ2 (new blocks: none); springs present: upright `$31`, diagonal `$36`; ring block `$40`; no spike blocks; surface types `0,1,2,3,7,9,13,20,23,24`. Objects: `$09` x3, `$26` x4 strong, `$10` parameter 1, `$1B` x1 at (752,128), `$50` boss x1 - all except the boss are covered by accepted research (the `$1B` placement is outside the measured platform/spike set but uses the same routine). Boss (`$50`) already has a full study; its children `$12/$34/$0A/$0F` and the act-clear screen are unresolved and **deferrable**. Recommended scope: THZ3 foundation (layout, rings, springs, monitors, `$1B`) right after the attack-posture migration; hold the boss.

## 12. Tests and counts

| Fixture | Cases | Result |
|---|---:|---|
| setter effects (26 setters x 256 `$D503` values) | 6,912 | exact bit maps |
| power-up branches, expiry, immunity | 12 | as section 3 (not in the total) |
| `$5F3D` gate | 4,608 | 0 mismatches |
| `$48BC` contact handler | 6,144 | 0 mismatches |
| type `$27` sweep | 21,756 | 0 mismatches |
| type `$21` sweep | 24,168 | 0 mismatches |
| monitor sweep | 12,834 | bit-1 rule |
| **controlled total** | **76,422** | |
| emulated natural timelines | 17 scenarios, 2,144 updates | section 2.2 / 7 |
| emulated contact trials | 14 + 1 frame-order trace | section 6 / 7 |
| `tests/test_player_attack_badnik.py` | 32 tests | 5 ROM-backed random sweeps with new seeds (1,500 + 600 + 800 + 800 + determinism) |

## 13. Unresolved

Super Peel-Out beyond an ordinary charge (aura only after a long hold); loop `$0C/$0D/$13` and twist `$22` not reachable in THZ1/THZ2 natural runs (byte-verified only); act-clear `$20` not emulated end to end; **animation-frame identity** (which frames are balls) not established - the visual discussion uses state numbers and the update lag; `$D532` persistence across acts and the end of power-up 3; the actual Windows trigger of the bee observation; THZ3 `$1B` (752,128) not measured.

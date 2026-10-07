# AQZ A3 — mapped type $3F platform

Research base: `172724dc34fe8750a4c36d82c4f5cd0e83a89e0d` (Manager-approved A1+A2). Europe v1.2 ROM, 524288 bytes, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. ROM remains local-only. No POC or ROM code changes.

Evidence: decoded scripts and placements, source-traced callbacks, controlled execution of original Z80 routines, and original-game software-harness traces. Automated harness results are not a new human gameplay/art approval. Machine contracts and reproducible source-region/tool hashes are in `data/rom-cache/aqz/platform-3f-runtime.json`; natural loader/scheduler vectors are in `platform-3f-game-checks.json`.

## Placement-to-path mapping

| Placement | File / bank:CPU | Stored X,Y | WORLD X,Y | Raw record | Runtime |
|---|---|---|---|---|---|
| AQZ1 #1, token1 | $713E5 / $1C:$93E5 | 2384,736 | 2128,480 | `3F 50 09 E0 02 00 86 80 32` | state7; aux1 $32 = 50 groups of16; 800-call outward leg |
| AQZ1 #2, token2 | $713EE / $1C:$93EE | 3664,528 | 3408,272 | `3F 50 0E 10 02 00 83 80 00` | state4; sag and contact-triggered delayed fall |
| AQZ2 #2, token2 | $7152A / $1C:$952A | 2352,925 | 2096,669 | `3F 30 09 9D 03 00 8B 80 00` | state13 gate → state14 script → falling tail |

Creator $1C:$80EB subtracts256 from stored coordinates, retains origins at +$3A/+$3C, stores canonical placement token +$3E, parameter +$3F and aux/art bytes +$08/+$09. Original outer loader handles occupancy; calling $80EB alone is not an occupancy-allocation proof. Generic loader/scheduler traces include the actual outer loader.

Both type $28 and $3F dispatch to bank $1E and table $8439 (15 states). Initializer $8585 sets movement flag3 bit7, sag byte +$25 from parameter bit7, byte +$26 from parameter bit6, requested state `(parameter & $3F)+1` and saved state +$36. Parameters masked with $7F equal5/11 override request to13. Aux1 initializes +$34 reload and +$37 remaining groups; +$30 starts16. Sag, return phase, movement deltas, latch and fall/delay scratch are zeroed. Render bytes +$10/+$11 become $C0/$02. $0332 → $606B supplies support owner ID from the slot.

The type-specific mapping pointer at +$2A/+2B differs. The equivalence fixture normalizes that pointer and the three type bytes (slot, creator scratch and source record), then compares all 8192 RAM bytes for 1649 callback updates per $83/$86 pair. Motion, contact, timers, sag and fall match. Numeric type alone never selects a platform callback path.

## $83 and $86 reuse verdict

**$83: shared $28/$83 runtime, AQZ mapping/art.** State4 shows frame1, zero initial velocity and delay80. A top contact after sag/carry sets +$27=$80. The next80 awake callbacks decrement +$1E; the following callback sets +$27=$FF without gravity; the next begins gravity +48/256, uncapped. Movement precedes support while falling. A rising player skips support. No terrain sampling. Sag/recovery adds/removes one pixel, up to8, independently of fall velocity.

Sleeping idle state4 returns. Sleeping state4 with nonzero +$27 overwrites runtime parameter+$3F with$80, clears +$3E and marks type$FE. The stored placement record remains unchanged. Cleanup cannot release the erased placement token: occupancy remains spent until act restart. This differs from ordinary generic deletion of an untriggered placement, which releases its token and permits fresh creation.

**$86: accepted SEZ $28/$86 state7 callback, AQZ aux/art.** Script sets keepalive flag4 bit1, frame1 and X velocity +1. Any shared rectangle overlap (`|dx|<=24`, dy−16..24 for ordinary Sonic) triggers latch1; trigger does not require downward speed, top contact, floor, attack or a particular player state. Movement happens on that same callback. Top support is a separate post-move test. A rising player can trigger motion without being carried.

Counter +$30 counts16 moving callbacks; +$37 counts aux1 groups, then reloads +$34 and negates X velocity after movement/carry. Aux1=$32 means800 updates/pixels each leg, 1600 round trip. It is not50 pixels. A zero group byte wraps through256 groups, giving4096 calls per leg (not a natural A3 value). Negative velocity changes latch to2; reversal after the return changes latch to0. A continuing overlap retriggers on the next callback. Position is not clamped to saved origin.

Asleep flag6 does not pause state7 counters/contact/motion. Its own $8908 retention uses strict `PLAYER_DIST(X,640)` and `PLAYER_DIST(Y,672)`; equality removes. The callback continues after marking$FE. Generic keepalive prevents ordinary outer-window deletion, not this player-distance removal. Cleanup releases occupancy; fresh creation restores origin, counters, velocity and latch.

## AQZ2 $8B: full state13/14 path

$85FE returns while asleep or when player Y velocity is negative. Shared $6328 overlap must classify top bit0. It requests saved +$36; **zone4 / act1 then overrides the request to14**. Thus $8B does not directly mean14, and the zone/act gate also overrides other parameter5/11 state13 paths. State13 does not acquire the support owner or carry the player.

State14 script $851D, exact records:

| Calls | Velocity X,Y | Callback | No-rider endpoint |
|---:|---|---|---|
| 160 | +1,0 | $8628 | 2256,669 |
| 64 | 0,+1 | $86A1 | 2256,733 |
| 96 | +1,0 | $8628 | 2352,733 |
| 128 | 0,−1 | $86A1 | 2352,605 |
| 128 | 0,−1 | $86A1 | 2352,477 |

$8577 clears carry deltas before each direction change (not between the two consecutive upward records). Frame1 throughout. No acceleration, collision probe, water sampling or coordinate endpoint clamp. Active no-rider travel is576 calls and displacement(+256,−192). Weight sag can add0..8 pixels to Y.

The tail writes delay80 and fall flag$80, zeros speeds, and jumps to script record $8489 / callback $8719. **Current and requested numeric state remain14; it does not request state4.** Eighty tail calls decrement delay, the next arms$FF, the next adds gravity48/256, uncapped. There is no script transition back to13, no rider-operated stop, and no terrain landing. It exits through deletion/cleanup.

$8628/$86A1 have a non-obvious asleep branch: they integrate once, then continue and integrate again. One asleep callback therefore moves twice but consumes one script duration. Horizontal carry delta includes only the second movement. Generic lifecycle can delete afterward because state14 does not set keepalive. The falling tail uses the state4 spent-token rule. Controlled awake/asleep vectors cover the full route and tail.

## Support/carry, water and scheduling

Shared $8814 requires no owner or the platform's own owner. Shared top triangle for ordinary Sonic is dy−16..−1 inclusive and `abs(dx)<=8+abs(dy)` inclusive. An unrelated owner blocks support. Horizontal $8628/$8662 callbacks require playerVy>=0; route vertical $86A1 requires signed platformVy<=playerVy ($8866), including fractional/both-negative cases. **Falling $8719 (state4 and state14 tail) uses only playerVy>=0, not the relative-speed gate:** a faster falling platform can still support a slower player if the post-move triangle overlaps. Controlled vectors prove platformVy560 with playerVy0 acquires support. Support is tested after movement except stationary contact/fall-trigger paths. Sag runs before projection. $88A0 writes rider Y=platformY−14 and adds integer platform X delta; it preserves both velocities, state and floor/movement flags. Object contact flags are consumed in the next player phase. State13's gate is contact only, not carry. State $0F's accepted extent9 expands shared geometry; do not substitute8 for all player states.

No reachable platform callback reads $D443, $D450, controller state or the player's underwater bit. Calls through fixed helpers are object ID ($606B), move ($60FB), overlap ($6328), distances and velocity negation; none introduces a water physics branch. Paired original callback controls change water flag/line and produce identical platform/player outputs. Water can change player velocity in the preceding player update, indirectly changing the support gate. Do not add buoyancy, drag or an underwater movement pause. The route's maximum no-rider Y733 is above WORLD788; later uncapped fall crosses the line. Natural scheduler rider vectors include that submerged falling path.

Order: camera/player update (including A2 water test, motion and terrain), object script engine $64FA, callback $5E91, generic lifecycle $61E1, periodic bank$1C mapped creation, renderer/effects. Callback sees the prior asleep flag because lifecycle updates it afterward. Natural traces show loader-created state0, initializer request, then active script on the next object phase; AQZ2 contact requests14 and script14 enters on its next phase.

Generic canonical 256px lifecycle uses EDGE visible/wake/sleep/delete bands from `docs/viewport-semantics-audit.md`; it is not a world-distance rule. Untriggered $83/$8B generic deletion releases occupancy. Slot cleanup is $FE→$FF→zero. Returning through the outer creation band creates a fresh original placement. Triggered $83 and state14 tail sleeping deletion retain spent occupancy, reset on act restart. State7 has its separate keepalive/distance rule described above.

Viewport labels: natural coordinates and origin-relative scripted travel are WORLD; 640/672 are PLAYER_DIST; create/wake/sleep/delete bands are EDGE. There is no CENTER or LOCKED_CAMERA constant specific to these platform callbacks. No widescreen behavior is designed.

## Presentation, oracle coverage and reproduction

Approved A1 frame0/1 compositions cover every reachable frame. Aux0=$80 supplies the tile base; aux1=$32/$00 supplies counter data and must not be treated as a second tile base. Type mapping pointers retain their original composition semantics. No new frame or board is needed; approval remains James's “all AQZ A1 boards approved”. Existing boards: ignored `build/aqz-approval`; reproducible hashes in `data/rom-cache/aqz/art-approval.json`.

Routine fixtures include full creator snapshots; $28/$3F normalized-RAM equivalence; 1620 state13 predicate cases; 41976 geometry cases; 2646 callback support/motion/owner cases; signed speed pairs; full awake/asleep script14 route; exact $83/$86 timing; strict distance boundaries; spent/released token cleanup and water-input controls. Cache records the exact executed assertion total, separate from unittest method count and whole-game rows.

Natural whole-game traces cover all three original placements: passive, synthetic continuous rider, deletion and fresh recreation. No platform is injected. Synthetic player anchor/velocity/request14 writes occur at original water-test and object-phase boundaries; rider Vy=7 ensures the moving support gate can be exercised. Rider movement flag3=$81 protects against unrelated terrain damage interrupting the route (the unprotected control reaches terrain damage before the underwater tail). The deletion/recreation case additionally moves the camera away and back through screenX320 then100. These are controlled fixtures, not claims of normal input-only gameplay. Original layout, loader, scheduler and callbacks remain enabled. Complete CPU-state bytes, RAM, VDP and harness state are restored, including prefix, EI shadow and frame_tick; repeated passive runs compare exactly. No NOP repair or register-only restoration.

Validation: eight focused A3 unittest methods, 70,468 enumerated original-routine assertions, and 2,982 whole-game trace rows, including three complete-snapshot replay comparisons. Row count is not an assertion count. A1/A2 regression suites and full `verify_cache` are also required before the branch checkpoint.

Reproduce with Python/z80 environment:

```text
.venv\Scripts\python.exe tools\aqz_platform_3f.py ROM.sms --check
.venv\Scripts\python.exe tools\aqz_platform_game.py ROM.sms --check
.venv\Scripts\python.exe -m unittest discover -s tests -p test_aqz_platform_3f.py
.venv\Scripts\python.exe tests\verify_cache.py ROM.sms
git diff --check
```

## Unresolveds and AGENTS candidates

No unresolved A3 runtime dependency remains. A4 types$3C/$3D, A5 boss$59–$5D and results art/audio remain outside this package. Human POC implementation/playtesting is a later acceptance step; this package does not assert Windows acceptance.

Candidate updates: Research main now includes accepted A1+A2 at172724dc; type$3F shares the $28 table but AQZ2 state13 contact overrides to14; aux1 state7 counts16-update groups; scripted state14 keeps numeric14 through its fall tail; triggered fall sleep clears token and leaves spent occupancy; preserve complete CPU snapshot restores for original-game fixtures. Manager should consolidate accepted candidates rather than copying this audit into root AGENTS.

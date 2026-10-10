# Special Stages SS-A4 — large goal ring, completion and failure paths

Unmerged research on `research/special-stages-canonical`. Machine packages `data/rom-cache/special-stages/goal-ring.json`, `natural-completions.json` (+ `natural-inputs.json`); tools `ss_goal_ring.py`, `ss_natural.py`, `ss_search.py`; tests `tests/test_ss_goal_ring.py`, `tests/test_ss_natural.py`.
Evidence: CONTROLLED (original callback `$1E:$9489` over a boundary sweep), EMULATED (whole-game, approximate SMS harness, complete CPU-state restore), SOURCE-TRACED.

## 1. Identity, placement, art

The large ring is **mapped object type `$31`** (type-table entry `$661A`, bank `$1E`, state table `$1E:$9468`, two states). One placement per stage; **the placement parameter is the stage's completion bit** (`01/02/04/08/10`). It is *not* the ordinary `$18` goal sign: no timer stop, no sign hop, no `$19` child, no player state `$20`, no results flag `$D293`.

| Stage | World (x,y) | Token | Parameter |
|---|---|---|---|
| SS1 | (15248,118) | 2 | `$01` |
| SS2 | (432,142) | 9 | `$02` |
| SS3 | (3712,494) | 8 | `$04` |
| SS4 | (8112,174) | 12 | `$08` |
| SS5 | (656,462) | 4 | `$10` |

Art: state 1 shows mapping frames 1, 2, 3 for 6 updates each (frame 0 is the empty frame used by state 0), art bases `$6A/$6A`. The tile data come from each stage's **own** supplemental stream (`$D40` bytes), so there are five colourways of one composition (blue, yellow-orange, green, grey, magenta). Exact mapping records over the stage VRAM are in the SS-A5 boards.

## 2. Callback `$1E:$9489` (CONTROLLED)

```
if (+4 bit6) return                       ; hidden/asleep
shared overlap $6328 (closed intervals)   ; dx: |dx| <= playerHalfW($D52C)+8
                                          ; dy = playerY-ringY in [-16, +playerHalfH($D52D)]
if (+0x21 & $F) == 0 return
D2A6 := D2BF<<8 ; D2CC |= +0x3F ; D2CD := $FF ; +0x3E := 0 ; type := $FF
D294 |= $40 ; D2C3 := (D2C3+1) & $7F
```

Sweep of the original callback over 49 x 74 offsets, normal 8x24 Sonic: contact rectangle **dx -16..+16, dy -16..+24** (a full rectangle, 1,353 cells); state `$0F` (9x24) widens to ±17; a player-blink/hurt flag (`$D503 = $40/$80`) does **not** suppress contact because object flag `+3` bit 7 is set at state 0 (`$9480`); `+4` bit 6 or `+3` bit 6 set blocks collection. The placement creator gives `flags $40`, extents `+$2C = 8`, `+$2D = 16`. Player-state independence: the ring never tests Rocket/Spring Shoes, invincibility, or airborne state.

## 3. Ordering and consequences

Order within an update: player engine and terrain -> object scheduler (the ring tests contact after the player has moved) -> frame. The callback only writes flags; the main loop `$1333` sees `D294` bit 6 on its next iteration and runs `$183F`: sound `$8A`, 30 frames, palette-fade flags, 120 frames, `$1869` (`D294 := 0`, `D297 := D296`, `D293 |= $20`) -> results `$32F9` (success card, sound `$86` for 240 frames when `D2CD == $FF`), tally, `D298 += 1`, level load (EMULATED timeline in `flow-traces.json`). Gameplay does not stop at contact (the player may still act for the remainder of that iteration); the timer is stopped by `$1753`. If bit 5 (failure) is set simultaneously, the dispatcher tests bit 6 first, so **success wins** (EMULATED: emerald set, card `$FF`).

Effects (CONTROLLED, five parameter/pre-state combinations): completion bit OR-ed (idempotent if already set), continues incremented modulo 128 with bit 7 cleared (`$7F -> 0`, `$80 -> 1`), `D2A6 = BCD(seconds left) << 8`, placement token cleared, object deleted. The ring cannot be collected twice, and its occupancy byte stays set so it does not respawn.

## 4. What is *not* a failure of the ring

Allocation: the ring is created by the ordinary placement creator inside the 32x32 window like any mapped object; stage object counts (<= 12) cannot exhaust the 19-slot pool, and no allocation-failure behavior was observed or invented. If the ring is far from the camera it simply does not exist yet (no collection possible).

## 5. Failure paths (all stages, EMULATED)

| Path | Mechanism | Result |
|---|---|---|
| Death | shared death setup `$4984 -> $49A0`: zone >= 8 -> `D294 |= $20` (no `D293` bit2) | `$1815`: death state shown ~30 frames, then the common return; **no life lost, no retry** |
| Timeout | `$2826..$2846`: `D2BF` underflow after display 00; timer is 59 s, i.e. ~60 s from stage start (frame 3510 in every stage when idle) | same as death |
| Falling out of bounds | death line from `$401A` (screen Y >= $D8 rule); SS1 pit death at update 30; controlled placement below each stage's camera limit ends all five stages with `$A0` | same as death |
| Out above the top | not fatal (shared rule) | - |
| Hurt | rings lost normally; zero rings -> shared death -> failure | no hazards exist in the stages |

Restart/retry: none. After any failure the game proceeds to the next act; the stage is offered again at the next 100-ring entry (SS-A5).

## 6. Natural completions (input only)

`natural-inputs.json` stores only controller input (run-length), searched with `ss_search.py` (best-first over short held-input macros, forking complete harness snapshots including the z80 core's full state view; success requires the *original game* to set `D294` bit 6 and the stage's `D2CC` bit) and then **replayed continuously from the stage-entry snapshot** by `ss_natural.py` (regeneration is a test). The stage entry itself is the original `$3138` ring routine run with `D29A = $99` (a hundred-ring entry); `D2CC` is preset to the stage's predecessor bits.

| Stage | Result | Frames | Notes |
|---|---|---|---|
| SS1 | **completed** | 2288 | tap Jump onto the Rocket monitor, hold Right, steer Up/Down to Y ~118 |
| SS3 | **completed** | 2090 | pipe network + rooms |
| SS5 | **completed** | 1426 | pipe maze |
| SS2 | **unresolved** | | Spring Shoes climb: the shoes are reached by input in 234 frames (jump-run steps), the relaunch is verified, but no complete climb was found: best-first search (5,726 nodes) reached Y 1277 of 142, and a platform-aware steering controller loses the shoes when Sonic moves away from the owner `$2F` object (attachment is tied to that object's lifetime, so the seven placements are re-pickup stations). A station-to-station route needs a purpose-built controller. |
| SS4 | **completed** | 2057 | platform course; found by a time-weighted best-first search (4,527 nodes), replay-verified |

Each completed run continues to the return to zone 0 act 1 with the emerald bit and +1 continue set (`natural-completions.json`). Every stage also has an idle-timeout route (3510 frames) and a controlled-placement pit-death route.

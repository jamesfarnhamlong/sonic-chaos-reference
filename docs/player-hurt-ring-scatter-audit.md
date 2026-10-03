# Player hurt / lost-ring scatter audit (shared global mechanic)

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`
(verified; never committed). `SonicChaos_POC` and the root `AGENTS.md` were **not** modified (the POC was only read).
Machine-readable facts: `data/rom-cache/player-hurt-ring-scatter.json`. Tool: `tools/player_hurt_ring_scatter.py`.
Tests: `tests/test_player_hurt_ring_scatter.py`. Builds on `docs/platform-spike-collision-audit.md` (`$48BC/$48F7`),
`docs/terrain-ring-collection.md` (layout rings) and `docs/viewport-semantics-audit.md` (`$61E1`).

Evidence classes: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY**, **SOURCE-TRACED BEHAVIOR**, **CONTROLLED ROUTINE RESULT** (original Z80
routines on `tools/oracle.py` with explicit RAM), **EMULATED ORIGINAL FRAME** (whole game, `tools/sms_frame_harness.py`),
**MODEL** (pure-Python re-implementation checked against the ROM), **POC SOURCE (READ-ONLY)**, **UNRESOLVED**.

## 0. Verdict

The ROM does **not** emit decoration. A hurt with rings creates `min(7, tens + 1)` real **type `$06` collectable objects** that fly
out with fixed per-index velocities, bounce on terrain, can be picked up again after a 16-update lockout (no player-state
condition) and live until their 8th floor contact or until they leave the camera band. The POC emits exactly one non-collectable
decorative object (section 11), which is why Windows shows rings that vanish quickly and cannot be recollected.

## 1. Answers to the audit questions

| Question | Result | Evidence |
|---|---|---|
| How many rings are emitted? | `N = min(7, tensDigit(BCD $D29A) + 1)` for 1..99 rings: 1-9 -> **1**, 10-19 -> 2, 20-29 -> 3, 30-39 -> 4, 40-49 -> **5**, 50-59 -> 6, 60-99 -> **7**. 0 rings -> death, no scatter. State `$11` keeps its rings (no scatter). The held count is set to 0; at most N (<= 7) rings can be recovered | BYTE-VERIFIED (`$4915..$4937`) + CONTROLLED (all 100 BCD values, 0 mismatches vs the model) |
| Object / type / state | type **`$06`** (type table `$065BA + 5*2` -> bank `$0C:$99FB`), 3 states: 0 init, 1 flight, 2 sparkle | DECODED |
| Spawn order | loop `H = 0..N-1`; each call of the allocator `$5E9C` takes the **first free slot of the first 16** (`$D540 + 64k`, k < 16), writes type `$06` and token `+$3F = H`. The scheduler runs slots 0..18 ascending, so the tokens spawned this update run their init in the same update | BYTE-VERIFIED + CONTROLLED |
| Initial X velocity (px/update, by token) | `0, -1.25, +1.25, -2.5, +2.5, -3.25, +3.25` (8.8: `$0000 $FEC0 $0140 $FD80 $0280 $FCC0 $0340`, table `$9A7C`) | DECODED |
| Initial Y velocity (px/update, by token) | `-5.0, -4.625, -4.625, -3.5, -3.5, -2.0, -2.0` (8.8: `$FB00 $FB60 $FB60 $FC80 $FC80 $FE00 $FE00`, table `$9A8A`) | DECODED |
| Scatter pattern | tokens fan out symmetrically (odd token left, even token right), faster tokens flatter; token 0 goes straight up. Origin = player anchor **X, Y-16** read in the object phase of the hurt update | DECODED + CONTROLLED + EMULATED |
| Gravity | `+0x0020` (0.125 px/update^2) added to `+$18/$19` once per update **before** the move; **no terminal speed** | BYTE-VERIFIED (`$9A9E`: `LD DE,$20 ; CALL $0431`) |
| Floor / wall / ceiling | **Floor** (vy >= 0 after gravity+move): header flag byte of the 32x32 block at `(x, y+18)`, bit 7 (solid) **or** bit 6 (one-way). **Ceiling** (vy < 0): header bit 7 only at `(x, y+2)`, which sets `vy := -vy`. **No wall test** (rings pass through walls). Block-level only: profiles/slopes are ignored; a position outside the map reads as air | BYTE-VERIFIED (`$614E`, `$6168`, `$7725`) + MODEL (84,420 ring-updates, 0 mismatches) |
| Bounce | `+$3C` starts at `$FC00` (-4.0). Every floor contact adds `$0080`; if there is no 16-bit carry it becomes both `+$3C` and the new Y speed: **-3.5, -3.0, -2.5, -2.0, -1.5, -1.0, -0.5**. The 8th contact carries (`$FF80 + $80`) and the ring is deleted (`$FF`, no sparkle). Position is **not** corrected on contact | BYTE-VERIFIED + CONTROLLED |
| Lifetime | no timer. Ends by: (a) pickup, (b) 8th floor contact, (c) off-screen removal (section 6). Example: token 0 on a flat floor under it lives 298 updates | CONTROLLED + EMULATED |
| Flashing | **none in the object logic**: the only periodic change is the flight animation (frames 1,2,4,3, 4 updates each, 16-update cycle) and the pickup sparkle (frames 5,6). No alpha, no blink, no visibility toggle. The *player* blinks (section 7). Sprite-per-scanline flicker, if any, would be a renderer property (UNRESOLVED, not object logic) | BYTE-VERIFIED (scripts and callbacks contain no visibility write) |
| Recollection lockout | scheduler pass `U0` = the hurt update; **no pickup test in U1..U16** (state 1 records 1-4, callback `$9A9E`); the pickup variant (callback `$9A98` = overlap test, then the same motion) starts at **U17** | CONTROLLED (7 tokens, first pickup always U17) |
| Pickup rule | `|ringX - playerX| <= 11 and |ringY - playerY| <= 11` against the player **anchor** (`$D511/$D514`); extents/sprite not read; the test uses the ring position **before** this update's movement and the player position **after** this update's player phase | CONTROLLED (29x29 offset sweep, 0 mismatches) |
| Player condition | **none**: collected in states `$01/$05/$0A/$1E/$1F/$20`, with `$D503` in `{$00,$02,$40,$80,$C1}`, `$D532` in `{0,3,6}` and any invulnerability timer (90 cases, all collect) | CONTROLLED |
| Pickup effect | sound `$BF`, `$0347 = JP $3138` (BCD +1 of `$D29A`; at 99 -> 00: sound `$A9` replaces `$BF`, lives +1 capped, `$178F`), ring freezes, state 2 sparkle | CONTROLLED |
| Off-screen removal | `$61E1` after every callback of a state != 0 (not in the init update): anchor outside the cell map -> delete at once; cell value 2 -> bit 6 -> the ring's own callback deletes it **on the next update**. Net SMS band: anchor in `[cam-32, cam+288)` on both axes stays; X/Y at `-96..-33` or `288..351` is deleted one update later; beyond `-97` / `352` immediately | CONTROLLED (3,640 offsets, 0 mismatches vs model) |
| Cap on emitted objects | yes: 7 (count rule) and only the first 16 object slots are allocatable; allocation failure is silent and does not shift tokens; slots 16..18 are never used | CONTROLLED |
| Underwater | **no difference**: none of the 22 routines references `$D443`; hurt + 300 passes are byte-identical with `$D443 = 0/1` | BYTE-VERIFIED + CONTROLLED |
| Hurt / invulnerability | scatter objects ignore the player's flags; a request while `+$03` bit 7 is set is held back (`$49F7`) and discarded at the end of the 120-update countdown; a later hurt spawns new rings into the next free slots and the old ones keep running | CONTROLLED |
| Same pickup path as terrain rings? | **Same counter routine `$3138`, separate detection and presentation.** Layout rings: block probe `$753E`, layout rewrite, effect object type `$03`, persist for the act. Dropped rings: object overlap `$617E`, own sparkle states, gone afterwards | BYTE-VERIFIED |

## 2. Update order and pass numbering

All of this happens inside one game update; `U0` is the update whose player phase runs `$48F7`.

```text
player phase   : ... terrain / spikes (may call $48F7)  ->  $48BC gate (may call $48F7)
                 $48F7: N = f(rings); H = 0..N-1: $5E9C(C=6,H) ; $D29A := 0 ; HUD $314A ; sound $A4 ; $D3B1 := $78 ; state $1E
object phase   : slots 0..18 ascending; each type $06 slot: engine $64FA -> callback ($5E91) -> $61E1 if state != 0
```

| Pass | Ring state (`+$01`) | Callback | What happens |
|---|---|---|---|
| `U0` | 0 | `$9A2B` init | `X := $D511`, `Y := $D514 - 16`, `vx/vy` from the tables by token, `+$3C := $FC00`, `+$03 := $C0`, `+$04 bit 0`, request state 1. No `$61E1`. |
| `U1..U16` | 1 | `$9A9E` | gravity, move, ceiling/floor probe, bit-6 delete test; `$61E1` |
| `U17..` | 1 | `$9A98` -> `$9A9E` | pickup test first; otherwise the same motion |
| pickup `Up` | 1 -> req 2 | `$9AF1` | sound `$BF`, `$3138`, request state 2, **no movement this update** |
| `Up+1..Up+28` | 2 | `$032F` (RET) | frames 5 (+1..+4), 6 (+5..+8), 5, 6, ... frozen at the pickup position |
| `Up+29` | 2 | `$034A` | type := `$FE` (record 8 fetched) |
| `Up+30 / Up+31` | - | `$626D / $5EF8` | `$FE` -> `$FF` -> slot zeroed (reusable by the allocator only now) |

A deleted ring (`$9AEC`, `$61E1`) carries type `$FF` until the scheduler reaches the slot again, so it cannot be re-allocated in the update in which it died.

## 3. Emission

```text
$48F7: if state == $11: rings kept, sound $C3, goto $4942 (no scatter)
       if $D29A == 0: death $1F (vy -5.0), no scatter
       A = ($D29A >> 4) + 1 ; if A >= 8: A = 7        ; the high nibble of a BCD byte is the decimal TENS digit
       for H in 0..A-1: $5E9C(C = 6, H)
       $D29A := 0 ; $314A ; sound $A4 ; +$03 |= $C1 ; $D3B1 := $78 ; state $1E ; vy -4.0 (+1.0 if +$22 bit 0) ; vx -1.0 (+1.0 if $D523 bit 3)
```

| Decimal rings | 1-9 | 10-19 | 20-29 | 30-39 | 40-49 | 50-59 | 60-99 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Objects | 1 | 2 | 3 | 4 | 5 | 6 | 7 |

### Correction of the earlier table

`docs/platform-spike-collision-audit.md` (section on `$48F7`) and `data/rom-cache/platform-spike-collision.json` (`hurt_consequences`)
list "(rings >> 4) + 1 ... 1, 1, 2, 3, 5, 7 for 1, 15, 16, 32, 64, 100 rings". Those rows fed **raw byte values** to `$D29A`; the byte is **BCD**
(`ADD A,1 ; DAA`). Decimal 15 / 16 / 32 / 64 rings are stored as `$15 / $16 / $32 / $64` and emit **2 / 2 / 4 / 7** objects; "100" cannot occur (it wraps to 00
with an extra life). The earlier rows remain valid byte-level controlled results but must not be read as ring counts. The POC rule
`min(7, (rings >> 4) + 1)` on a decimal counter (`SCR_chaos_core.gml`) inherits the mislabel.

## 4. The scatter object (type `$06`)

State 1 per update (**BYTE-VERIFIED**, verified by **MODEL**; 8.8 velocities, 24-bit positions `[+$10 fraction | +$11/$12 pixel]`, `[+$13 | +$14/$15]`):

```text
if pass >= 17 and |x - $D511| < 12 and |y - $D514| < 12:  sound $BF ; $3138 ; request state 2 ; return     ; (still runs $61E1)
vy += $0020
x24 += sext(vx) ; y24 += sext(vy)                                                       ; $60FB
if vy < 0 (bit 15):   if header($7725(x, y + 2)) bit 7:  vy := -vy                      ; $6168, DE = -16, +18 bias inside $7725
else:                 if header($7725(x, y + 18)) bit 6 or 7:
                          b = bounce + $80 ; if b > $FFFF: delete ($FF) ; return
                          bounce = vy = b                                                ; -3.5 ... -0.5
if (+$04 bit 6, written by the previous $61E1): delete ($FF)
```

`$7725` adds the fixed `+$12` terrain bias, so the **floor probe is the ring anchor + 18** and the **ceiling probe the anchor + 2**; X is the anchor X
(no side probes). The probed value is header byte 0 of the layout block (`block = layout[(y >> 5) * stride + (x >> 5)]`, outside `$C000..$CFFF` -> flags 0):

| Block header flags | Falling ring | Rising ring |
|---|---|---|
| bit 7 (solid, e.g. `$01` = `$81`) | bounces | turns around (`vy := -vy`) |
| bit 6 only (one-way, e.g. `$0D` = `$41`) | **bounces (lands)** | passes up through |
| neither (air `$00`, ring blocks `$40..$45` = `$07`) | passes | passes |

Consequences measured on a flat floor (floor row top 640, player anchor 622 = floor - 18, camera X 872, `lab`, no player motion):

| Token | Bounce updates (relative to U0) | End |
|---:|---|---|
| 0 | 83, 137, 184, 223, 254, 276, 291 | 8th contact at 298 (`bounce_exhausted`) |
| 1 / 2 | 77 | leaves the band, deleted by bit 6 at 130 / 129 |
| 3 / 4 | 60 | band exit at 66 / 65 |
| 5 / 6 | 38 | band exit at 51 |

If the player stands still at the spawn point, token 0 falls back through the player box and is **recollected at update 81** (two updates before its first bounce).

## 5. Pickup

* The test is one point-in-box: `|dx| <= 11` and `|dy| <= 11` (`SBC` against 12, strict) on integer pixels; both axes use the **anchors**; nothing about the player (state, `$D503` hurt bit 6 / blink bit 7, `$D3B1`, `$D532`) is read. Collected examples include states `$1E` (hurt) and `$1F`.
* The ring tests with its position at the **start** of the pass (before gravity/move) and the player position after the player phase of the same update.
* Several rings can be collected in the same update (one `$3138` each).
* No double collection: the ring leaves state 1 immediately.
* `+$03 = $C0`: bit 6 disables the shared contact helper `$6328`, so a lost ring never hurts, never pushes and never interacts with `$D520`.

## 6. Removal summary

| Cause | When | Visible effect |
|---|---|---|
| Pickup | any pass >= 17 | sparkle 28 updates |
| 8th floor contact | after bounces -3.5 .. -0.5 | silent delete |
| `$61E1` outside the 512-px window or cell 3 | same update | silent delete |
| `$61E1` cell 2 (`bit 6`) | next update, end of the ring's callback (after its movement) | silent delete |

The active cells are `[-32, 288)` camera-relative on both axes (`$D174/$D176`); the horizontal band is a lifecycle constant of a 256-px view (see the widescreen note in section 11).
A ring thrown at +3.25 px/update from the middle of the screen is removed after about 50 updates; token 0 (vx = 0) stays.

## 7. Hurt, invulnerability and the player blink

* `$48BC` (gate): `+$03` bit 7 -> countdown `$49F7`; bit 6 -> clear `+$20`, return; `$D532 == 6` -> request cleared; otherwise request `$D3B0` or contact `$D520` -> `$48F7`.
* After a ring-loss hurt: `+$03 |= $C1`, `$D3B1 := $78`; the countdown is `119 .. 0` and the invulnerable bits are cleared at the **121st gate update** (`$4A19`, which also zeroes `$D3B0`).
* **Player blink** (not the rings): `+$04` bit 7 (hidden) follows bit 1 of the decremented `$D3B1` unless the current state is `$1E`: 2 updates hidden, 2 visible; no blink while in state `$1E`.
* A second damage request during the countdown is held back and discarded when the countdown ends; a fresh hurt afterwards emits new rings into the next free slots while the earlier rings keep their own bounce/lifetime (controlled run: invulnerability ended at gate update 121, new ring in slot 3).
* Terrain spikes call `$48F7` directly after testing `+$03` bit 7 themselves (`docs/platform-spike-collision-audit.md`): the scatter is identical for every damage source (enemy request, boss forced hurt, spikes).
* State `$11` (rocket) is hurt without ring loss: no scatter.

## 8. Terrain rings versus dropped rings

| | Layout ring (type 7 quadrant) | Dropped ring (type `$06`) |
|---|---|---|
| Detection | one point at `(anchorX, anchorY - 8/+2)` in a 16x16 quadrant of blocks `$40..$45` (`$753E`) | object overlap box, `|dx|,|dy| <= 11` (`$617E`) |
| Counter | `JP $3138` | `$0347 = JP $3138` |
| Sound | `$BF` (`$A9` on the 100th ring) | `$BF` (`$A9` on the 100th ring) |
| Effect | layout cell rewritten, effect object type `$03` at the probe point | the ring becomes its own sparkle (states 2) |
| Persistence | gone for the loaded act | gone |
| Lockout / player gate | none / none | 16 updates / none |

## 9. Underwater

No scatter-related routine (22 regions, operand scan for `$D443`) reads the water condition. Gravity `$20`, velocity tables, bounce and pickup are the same underwater (identical hurt + 300 passes). Any water-specific POC rule would be invented.

## 10. Exact example: losing 47 rings during the GPZ3 boss (**EMULATED ORIGINAL FRAME**)

Whole GPZ3 game booted through the original loader and driven with the same scheduler-aligned harness as `docs/gpz3-boss-runtime-audit.md`. Until update 630 the usual
synthetic parking keeps Sonic out of harm; at update 630 (boss state 7, detached ball state `$0B` at (1805, 270), camera (1663, 96)) Sonic is placed at (1795, 270) with `$D29A = $47`,
standing, not attacking. Then the original game runs freely (`natural_no_recollect`). A second run (`player_teleports_onto_ring_0_at_k40`) is identical until update 40
after the hurt, when Sonic is placed on ring token 0. Row `k` is the RAM at the **start** of update `k`; the hurt (and `U0`) is update `k = 1`.

Result: 5 rings (`0x47` -> tens 4 + 1), tokens 0..4 in slots 0..4, Sonic: requested state `$1E`, vy -4.0, vx -1.0, `$D3B1 = 120`, `$D503 = $C1`, counter `00` (the sound request `$A4` is consumed by the sound engine before the next sample; the lab shows it).

| k | Sonic (x,y) vx,vy; state/req; `$D503`; inv; rings | token 0 | token 1 | token 2 | token 3 | token 4 |
|---:|---|---|---|---|---|---|
| 2 | (1795,270) -1.00,-4.00; 01/1E; C1; 120; 00 | 1795,254 v(0,-5.000) | 1795,254 v(-1.25,-4.625) | 1795,254 v(+1.25,-4.625) | 1795,254 v(-2.5,-3.500) | 1795,254 v(+2.5,-3.500) |
| 3 | (1794,266); 1E/1E; C1; 119 | 1795,249 v(0,-4.875) | 1793,249 | 1796,249 | 1792,250 | 1797,250 |
| 18 | (1779,232) -1.00,-1.00; 1E/1E; C1; 104 | 1795,191 v(0,-3.000) | 1775,197 | 1815,197 | 1755,215 | 1835,215 |
| 19 | (1778,231); 1E/1E; C1; 103 | 1795,188 (first pickup-eligible pass is update 18) | 1773,194 | 1816,194 | 1752,213 | 1837,213 |
| 40 | (1757,257) -1.00,+3.12; 1E/1E; C1; 82 | 1795,156 v(0,-0.250) | 1747,170 | 1842,170 | 1700,213 | 1890,213 |
| 63 | (1746,270) 0,+7.00; 01/01; 80; 59 | 1795,185 | 1718,208 | 1871,208 | 1642,269 (bounced at k=62) | 1947,269 (bounced) |
| 66 | (1746,270); inv 56 | 1795,194 | 1715,218 | 1875,218 | 1635,260 | removed (x 1952 > cam+288) |
| 69 | | 1795,203 | 1711,228 | 1878,228 | removed (x 1630) | |
| 80 | (1746,270); inv 42 | 1795,249 | 1697,269 (bounced at k=79) | 1892,269 | | |
| 86 | | 1795,271 v(0,-3.375) (first bounce at k=85, y 274) | 1690,252 | 1900,252 | | |
| 128 | inv 0 | 1795,242 | 1637,254 | removed (last row k=127, x 1951) | | |
| 135 | | 1795,259 | removed (last row k=134, x 1630) | | | |
| 140 | | 1795,268 v(0,-2.875) (second bounce at k=139, -3.0 speed) | | | | |

Facts shown by the real run:

* Rings 1..4 leave the camera band (camera X 1663: anchor `d = x - 1663` outside `[-32, 288)`, i.e. x `< 1631` or `>= 1951`) and their last rows are k = 65 (token 4), 68 (token 3), 127 (token 2) and 134 (token 1). Tokens 3/4 bounce once at k = 62 and tokens 1/2 at k = 79 on the arena floor (y 272-273 = floor probe at y+18 inside the floor block row).
* Ring 0 (vx = 0) stays inside the band: it bounces at k = 85 (speed -3.5) and k = 139 (-3.0) and would continue to the 8th contact; only ring 0 can realistically be recollected in this arena (the other four are thrown out of the 256-px band within 65-134 updates).
* Sonic is knocked from (1795,270) to (1746,270) and lands by k = 60; `$D503 = $C1` until landing, `$80` afterwards, cleared at k = 123 (gate update 121 after the hurt). Sonic then stands in the ball's lane with 0 rings, so the trace stops at k = 150 (a further hit with 0 rings is death `$1F`).
* In the second run Sonic is placed on ring 0 at (1795,156) at the start of update 40 (hurt state `$1E`, `$D3B1 = 82`, `$D503 = $C1`): the ring counter goes **0 -> 1** in that update (row 41), ring 0 is in state 2 and plays its sparkle (frames 5/6, last row k = 69) and is gone; tokens 1..4 are unaffected.
* Boss contact, ring loss and the ordinary `$48F7` are the same as the `$06` objects above; the GPZ3 `$51` boss adds nothing ring-specific (`docs/gpz3-boss-runtime-audit.md`: attached non-attack, vulnerable Sonic -> ordinary ring loss; no rings -> death `$1F`).

(The full per-update arrays, 150 rows per run, are in the cache under `gpz3_boss_example`.)

## 11. POC diagnosis (read-only) and adapter notes

**POC SOURCE (READ-ONLY, `SonicChaos_POC_thz1_cleanup` working tree on `84c3e10`).**

* `SCR_chaos_hurt_apply` (`scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml`): `if (cp_c.hurt_scatter > 0) instance_create(cp_p.x,cp_p.y,OBJ_player_lost_b);` creates **one** object whatever `hurt_scatter` is.
* `OBJ_player_lost_b`: alpha 0.6, `alarm[0] = 80` destroys it after 80 steps, `vspeed = -8`, `gravity = 0.4` (cap 12), alpha blink alarms of 4 steps, `Alarm_3` sets `global.ring = 0`; no terrain probe, no bounce, no pickup, no velocity table.
* `SCR_chaos_core.gml`: `hurt_scatter = min(7, (rings >> 4) + 1)` on a decimal counter (see the correction in section 3); the count is computed but only used as a boolean.
* This explains the observed Windows behaviour exactly (quick fade, no recollection).

Adapter notes (not ROM facts): updates are per-frame object phases (no seconds claim); keep the ring anchor/pickup canonical and decide presentation separately (frames 1-4 flight animation, 5/6 pickup sparkle; draw extents (8,16)/(4,16) are not collision); derive the lifecycle band from the displayed width (do not let a widescreen view keep SMS edges); if a non-block collision is used the same two probe points and the one-way rule must be kept; never add alpha/blink/timer to the lost rings; recollection must be independent of player state and evaluated before the ring's own movement.

## 12. Unresolved

* Whether the sprite renderer draws an object whose type is `$FE` (the final update of the sparkle). One frame at most, presentation only.
* SMS sprite-per-scanline flicker with 7 rings plus other sprites (renderer property; no ring blink exists in the object code).
* The exact on-screen anchor offset of the ring sprite frames (the accepted type-`$09` ring presentation can be reused only after a check against frames 1-6).

## 13. Reproduce

```text
python tools/player_hurt_ring_scatter.py "Sonic Chaos (Europe).sms"          # regenerate the cache (~10 s)
python tools/player_hurt_ring_scatter.py "Sonic Chaos (Europe).sms" --check  # byte-compare
python -m unittest tests.test_player_hurt_ring_scatter -v                    # cache tests; ROM-backed tests need SONIC_CHAOS_ROM or the ROM beside the repo
```

## 14. AGENTS candidate updates (root `AGENTS.md` not edited)

* **Player hurt/ring loss is shared by every damage source** (`$48F7`): `N = min(7, tens digit of BCD $D29A + 1)` real type-`$06` objects (decimal 15/32/64 rings emit 2/4/7, not 1/3/5), ring counter := 0, sound `$A4`, invulnerability 120 updates, state `$1E`.
* **Lost rings are collectable canonical objects**: spawn (playerX, playerY-16); velocities X `{0,-1.25,+1.25,-2.5,+2.5,-3.25,+3.25}`, Y `{-5.0,-4.625,-4.625,-3.5,-3.5,-2.0,-2.0}` px/update; gravity +0.125/update, no cap; pickup test from the 17th pass (16-update lockout) with box `|dx|,|dy| <= 11` against the player anchor and **no player-state condition**; +1 ring through the shared `$3138`; sparkle frames 5/6 for 28 updates.
* **Lost ring physics**: block-flag probes only (falling: header bit 6/7 at y+18, rising: bit 7 at y+2); bounce speeds -3.5 .. -0.5, the 8th floor contact deletes; no wall test, no timer, no flashing; removal at the camera band (`$61E1`, one update later through the ring's own bit-6 check); allocation limited to the first 16 object slots.
* **Never** use the legacy decorative `OBJ_player_lost_b` for lost rings, and never apply `rings >> 4` to a decimal counter.

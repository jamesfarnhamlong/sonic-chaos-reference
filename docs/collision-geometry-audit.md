# Collision geometry audit: player extents, shared helpers and current THZ objects

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified; never committed).
`SonicChaos_POC` was read (files only, never run or modified; commit `a3b0382`).
Machine-readable facts: `data/rom-cache/collision-geometry.json` (numeric labels only).
Tool: `tools/collision_geometry.py`. Tests: `tests/test_collision_geometry.py` (43 tests; `tests/verify_cache.py` regenerates the cache).
Builds on `docs/object-18-act-clear.md` (where the wrong `9 x 18` assumption was found).

Evidence classes: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY**, **SOURCE-TRACED BEHAVIOR**, **CONTROLLED ROUTINE RESULT** (original Z80 routines on
`z80` with explicit RAM), **EMULATED ORIGINAL FRAME** (whole game in `tools/sms_frame_harness.py`), **POC SOURCE (READ-ONLY)**, **UNRESOLVED**.
`dx = playerX - objectX`, `dy = playerY - objectY`, integer anchors (`$D511/$D514` and object `+$11/+$14`); `Ex/Ey` = player extents `$D52C/$D52D`;
`oEx/oEy` = object extents `+$2C/+$2D`.

## 1. Summary

| Question | Result |
|---|---|
| Sonic's extents | **8 × 24 in every state**, except state `$0F` = **9 × 24**. They do not change for rolling, jumping, spring, loop/twist, reward (`$18`) or act-clear run (`$20`) states. |
| Where they come from | Only the animation engine (`$6595/$659A`) writes `$D52C/$D52D`, copying bytes 1/2 of the current mapping frame record. Nothing else writes them; only the overlap/solid helpers read them. Terrain never reads them. |
| `$6328` | Exact model recovered and matched on **62,400** controlled cases (0 mismatches): closed-interval overlap, unsigned 16-bit, player box `x ±Ex, y [-Ey, 0]`, object box `x ±oEx, y [-oEy, 0]`, minimum-penetration bit (ties go vertical). |
| `$5FA0` | `$6328` plus a one-bit dispatch that moves **only the player's position** (no velocity, no state, no floor flag). Matched on **20,000** controlled cases (0 mismatches). |
| Objects | `$18 $1B $21 $27 $28` use `$6328`; `$10` and `$50` use `$5FA0`; `$26` springs and `$09` rings use proximity boxes (no extents); `$19 $0A $0F $12 $34` have no physical collision. |
| Discrepancies | 21 audited assumptions: **3 CRITICAL** (POC rings, POC monitors, POC goal-sign adapter), **5 EDGE**, **9 TEST-ONLY** (all in research fixtures), **4 NOT A BUG** (terrain constants, spring window width, constant mask, unimplemented `$21`). No POC file contains the wrong `9 x 18` constants; the POC uses GameMaker sprite-mask overlap instead of the ROM boxes. |

## 2. Player collision extents

**CONTROLLED ROUTINE RESULT + BYTE-VERIFIED + EMULATED.**

### 2.1 How the extents are produced

* RAM: `$D52C` (X extent) and `$D52D` (Y extent) are `+$2C/+$2D` of the player slot `$D500`.
* The animation engine `$64FA`, on every record load (`$6595/$659A`), copies **frame-record bytes 1 and 2** of the mapping table (`$3C000 + type*2`, bank `$0F`) into them.
  Extents therefore change exactly when the current animation frame changes: at a state change (`+$02` → `+$01`) and at each script record. There is no separate
  "hitbox" table and no state-specific override (byte scan: no `LD ($D52C),A`/`LD ($D52D),A` anywhere; the only IX writes are the engine and three unrelated objects).
* Reads: `$5FE0` (solid, player-below push), `$6023`/`$6052` (solid side pushes), `$6358/$6376/$6397` (`$6328`), and the unused variant `$643B/$6458/$6478`.
  No terrain, movement or state-setter routine reads the extents.
* Extents are not derived from sprite size. They are record bytes (Sonic type-1 table `$80C8`).

### 2.2 Method

For every player state `$00..$33` the state script was run through the **real** engine on the player slot (Sonic type 1 and type 2) at speeds 0, `$0100`, `$0300`,
`$0600` and `-$0300` (so the run-frame selector `$8EE1` visits its frames). Every record's `$D52C/$D52D` were recorded. Independently, 8,000 frames of pseudo-random
play in the full emulated game (seed 1) sampled `($D501, $D52C, $D52D)` each frame: every Sonic state reached (19 of them) agrees with the table; the only other value seen
is a transient `(0,0)` in state 0 before the first record loads.

### 2.3 Table (all 52 scripted states)

"Requested/current state": the engine loads the script of the requested state `+$02` into current `+$01` at the next engine run; the extents are those of the record
currently loaded. A script request (`FF 03`) column shows where the script itself changes state. Numeric labels only (names are not proven).

| State | Sonic X,Y | Type-2 X,Y | Mapping frames (Sonic) | Script callback(s) | Script requests state |
|---:|---|---|---|---|---|
| `$00` | 8,24 | 8,24 | 11 | `$0395` | `$01` |
| `$01` | 8,24 | 8,24 | 11,12,13,14 | `$0395`, `$03E0` | - |
| `$02` | 8,24 | 8,24 | 12,13,14 | `$03E0` | - |
| `$03` | 8,24 | 8,24 | 19 | `$03BC` | - |
| `$04` | 8,24 | 8,24 | 20 | `$03B9` | - |
| `$05` | 8,24 | 8,24 | 1,2,3,4,5,6 | `$03E9` | - |
| `$06` | 8,24 | 8,24 | 7,8,9,10 | `$03D4` | - |
| `$07` | 8,24 | 8,24 | 21,22 | `$03E3` | - |
| `$08` | 8,24 | 8,24 | 21,22 | `$03E6` | - |
| `$09` | 8,24 | 8,24 | 38,39,40,41 | `$03C5` | - |
| `$0A` | 8,24 | 8,24 | 38,39,40,41 | `$03B3` | - |
| `$0B` | 8,24 | 8,24 | 28,29,30,31,32,33 | `$039E` | - |
| `$0C` | 8,24 | 8,24 | 1,2 | `$03CB` | - |
| `$0D` | 8,24 | 8,24 | 1,2 | `$03D1` | - |
| `$0E` | 8,24 | 8,24 | 1,2,3,4,5,6 | `$03AD` | - |
| `$0F` | 9,24 | 8,24 | 34,35,36 | `$03DD` | - |
| `$10` | 8,24 | 8,24 | 38,39,40,41 | `$03A4` | - |
| `$11` | 8,24 | 8,24 | 56,57,58 | `$03C2` | - |
| `$12` | 8,24 | 8,24 | 11 | `$03B0` | - |
| `$13` | 8,24 | 8,24 | 1,2 | `$03CE` | - |
| `$14` | 8,24 | 8,24 | 28,29,30,31,32,33 | `$03F8` | - |
| `$15` | 8,24 | 8,24 | 7,8,9,10 | `$043D` | - |
| `$16` | 8,24 | 12,32 | 95,96 | `$0449`, `$044C` | - |
| `$17` | 8,24 | 12,32 | 95,96 | `$044C` | - |
| `$18` | 8,24 | 8,24 | 95,96,97 | `$807C` | - |
| `$19` | 8,24 | 8,24 | 25,26,27 | `$0392` | - |
| `$1A` | 8,24 | 8,24 | 7,8,9,10 | `$0440` | - |
| `$1B` | 8,24 | 8,24 | 38,39,40,41 | `$03C8` | - |
| `$1C` | 8,24 | 8,24 | 28,29,30,31,32,33 | `$03B6` | - |
| `$1D` | 8,24 | 8,24 | 1,2 | `$03DA` | - |
| `$1E` | 8,24 | 8,24 | 23 | `$03AA` | - |
| `$1F` | 8,24 | 8,24 | 24 | `$03A7` | - |
| `$20` | 8,24 | 8,24 | 1,2,3,4,5,6 | `$83A6` | - |
| `$21` | 8,24 | 8,24 | 37,38,39,40,41 | `$916B` | - |
| `$22` | 8,24 | 8,24 | 37,38,39,40,41 | `$94C1` | - |
| `$23` | 8,24 | 8,24 | 95,96,97 | `$807C` | - |
| `$24` | 8,24 | 8,24 | 95,96,97 | `$807C` | - |
| `$25` | 8,24 | 8,24 | 1,2,3,4,5,6,54 | `$836F`, `$03AD` | - |
| `$26` | 8,24 | 8,24 | 95,96,97 | `$807C` | - |
| `$27` | 8,24 | 8,24 | 95,96,97 | `$807C` | - |
| `$28` | 8,24 | 8,24 | 55 | `$0443` | - |
| `$29` | 8,24 | 8,24 | 7,8,9,10 | `$0338` | - |
| `$2A` | 8,24 | 8,24 / 12,32 | 95,96,97 | `$807C` | - |
| `$2B` | 8,24 | 8,24 | 95,96,97 | `$807C` | - |
| `$2C` | 8,24 | 8,24 | 95,96,97 | `$807C` | - |
| `$2D` | 8,24 | 8,24 | 95,96,97 | `$807C` | - |
| `$2E` | 8,24 | 8,24 | 95,96,97 | `$807C` | - |
| `$2F` | 8,24 | 8,24 | 95,96,97 | `$807C` | - |
| `$30` | 8,24 | 8,24 | 1,2,3,4,5,6 | `$032F` | - |
| `$31` | 8,24 | 8,24 | 1,2,3,4,5,6 | `$032F` | - |
| `$32` | 8,24 | 8,24 | 95,96,97 | `$807C` | - |
| `$33` | 8,24 | 8,24 | 37,38,39,40,41 | `$0338` | - |

Key rows (labels only where earlier research proved them; no state is named from appearance):

| Situation | State | Sonic X,Y | Evidence |
|---|---|---|---|
| ordinary states (stand/walk/run/jump/roll/crouch/spin-dash/hurt/death-like and every other scripted state) | every state except `$0F` | **8,24** | CONTROLLED + EMULATED; no state makes the box smaller for rolling or larger for jumping |
| upright spring flight (`docs/movement.md`) | `$0B` (frames 28-33) | 8,24 | CONTROLLED + EMULATED |
| numeric reward pose (`docs/player-state-11.md`) | `$11` | 8,24 | CONTROLLED |
| the only different value | `$0F` (frames 34-36) | **9,24** | CONTROLLED + EMULATED (the type-`$10` top-hit block list also names `$0F`; its meaning is not proven here) |
| reward/requested state tested by the goal sign | `$18` (frames 95-97) | 8,24 | CONTROLLED |
| act-clear run | `$20` (frames 1-6) | 8,24 | CONTROLLED |
| loop / twist strips | position-table states | 8,24 | CONTROLLED; the geometry is a position lookup, not the extents |

The only non-`8,24` Sonic value is `$0F`. Type 2 (the second player type) has `12,32` in states `$16`, `$17` and `$2A`; THZ research is Sonic-only.

## 3. Shared overlap helper `$6328`

**BYTE-VERIFIED + CONTROLLED (62,400 random, edge and structured cases, 4 outputs each, 0 mismatches).** Vector `$033B` (26 call sites in banks `$0C/$1E`), also called by
`$5FA0` and by the damage wrapper `$630B` (vector `$0434`, 16 call sites). An unused variant at `$640B` (sets all four contact bits, no direction choice) has no direct caller.

Inputs: object `IX`: `+$11/+$12` X, `+$14/+$15` Y, `+$2C` X extent, `+$2D` Y extent, `+$03` flags. Player: `$D511` X, `$D514` Y, `$D52C`, `$D52D`, `$D503`.

```text
clear +$20 ; +$21 &= $F0
if +$03 bit 6: return
if not +$03 bit 7 and $D503 bit 6: return            ; the player's bit-6 gate
span = (Ex + oEx) & $FF
dx = (playerX - objectX) as UNSIGNED 16-bit
  no borrow (playerX >= objectX):  need dx <= 255 and dx <= span ; bit2 (player right)   hPen = span - dx
  borrow:                          need 1 <= objectX-playerX <= 255 (256 fails) and <= span ; bit3 (player left)
dy = (playerY - objectY) as UNSIGNED 16-bit
  no borrow (player at/below anchor): need dy <= 255 and dy <= Ey  (PLAYER extent only) ; bit1   vPen = Ey - dy
  borrow (player above):              need 1 <= objectY-playerY <= 255 and <= oEy (OBJECT extent only) ; bit0   vPen = oEy - |dy|
keep only one axis:  mask = 12 if hPen < vPen else 3  ; +$21 = (bits & mask)       ; ties choose the vertical axis; the high nibble is cleared
+$20 = 1 if $D503 bit 7 is clear
if not +$03 bit 7: $D520 = ((IX-$D500) >> 6) + 1
$D521 = ($D521 & $0F) | ((+$21 ^ (12 if vertical bits absent else 3)) << 4)       ; mirrored contact seen from the object
```

* **Anchors**: player `($D511,$D514)`, object `(+$11,+$14)`; both boxes hang **above** their anchors. Equivalent closed-interval form:
  player `x [px-Ex, px+Ex] × y [py-Ey, py]`, object `x [ox-oEx, ox+oEx] × y [oy-oEy, oy]`; contact iff the closed boxes share a point. (Verified on a 3-extent-set grid.)
* **Inclusive**: every comparison is `<=`; touching edges count. `dx = 0` or `dy = 0` takes the no-borrow side.
* **Asymmetry**: below the anchor only the player's `Ey` counts; above only the object's `oEy`. Left/right use the sum `Ex + oEx`.
* **Overflow/wrap**: the sum is 8-bit (no real extent overflows); any distance of 256 or more fails (256 exactly fails through `NEG 0`); a coordinate near `$FFFF`/0 behaves as a
  very large distance because the subtraction is unsigned.
* **Return convention**: none. Callers test `(IX+$21) & $0F`. `+$20` is the player's "not in attack posture" bit; `$D520/$D521` are the reverse-link bookkeeping.
* **Resulting Sonic boxes** (measured on the real callbacks): `$10` dx ±18, dy -24..+24; `$1B` ±24, -24..+24; `$27` ±17, -14..+24; `$21` ±19, -26..+24;
  `$28` ±24, -16..+24 (±1 px shift from its pre-move); `$18` ±20, -42..+24.

## 4. Shared solid helper `$5FA0`

**BYTE-VERIFIED + CONTROLLED (20,000 cases, 0 mismatches; also checked per case that player velocity, current/requested state and floor flags are untouched).**
Vector `$034D`; used by type `$10` (`$A177`) and the boss `$50` (two sites).

```text
call $6328
n = +$21 & $0F ; if n == 0 return
jump table $5FB9[n]:   n=1 (player above)  -> $5FF1 ; n=2 (player below) -> $5FDA ; n=4 (right) -> $6038 ; n=8 (left) -> $6009 ; others RET
$5FF1 above : unless $D523 bit 0: playerY = objectY - oEy                ; anchor placed on the object's top edge
$5FDA below : unless $D523 bit 1: playerY = objectY + Ey ($D52D)
$6038 right : unless $D523 bit 2 and only if playerX <= cameraX + $E0: playerX = objectX + oEx + Ex
$6009 left  : unless $D523 bit 3 and only if playerX >  cameraX + $20: playerX = objectX - (oEx + Ex)
```

* **Consumes**: `Ex` (both side pushes), `Ey` (below push and the dy ≥ 0 test), `oEx` (side pushes), `oEy` (above push and the dy < 0 test), camera X `$D174`, combined contact flags `$D523`.
* **Classification**: exactly the `$6328` bit (one of four); ties go vertical (`hPen < vPen` decides horizontal).
* **Velocity/state**: none. Callers do everything else (type `$10` adds attack, bounce and reward logic after the push).
* **Consequences for type `$10` fixtures**: the existing fixtures used `Ex,Ey = 9,18`; with Sonic's real `8,24` the contact box is `dx ±18` (not ±19) and the player-below reach is `dy ≤ 24`
  (not 18). The push positions also change: below push `objectY + 24` (fixtures implied `+18`), side push `objectX ± 18` (implied ±19). The top edge (`dy = -24`) is unaffected.

## 5. Per-object collision table (current THZ objects)

**SOURCE-TRACED (recursive descent over the real state callbacks) + CONTROLLED (box sweeps of the real callbacks with Sonic 8,24).**
Class: A = `$6328`, B = `$5FA0`, C = other shared helper, D = bespoke logic, E = no physical collision.

| Type | Class | Contact routine | Player extents used | Object extents used | Boxes for Sonic (8,24) |
|---|---|---|---|---|---|
| `$09` placed ring | C | `$617E` (vector `$0380`), collection via `$3138` | none | none | anchor box: `|dx| < 12` and `|dy| < 12` (strict) |
| `$10` monitor | B + D | state-2 callback `$A16C`; `CALL $034D` at `$A177` | `Ex` both sides, `Ey` | (10,24) states 2/3 | dx ±18, dy -24..+24 |
| `$18` goal sign | A | state-3 callback `$A88E` (`CALL $033B`) | `Ex`, `Ey` | (12,42) frame 1 | dx ±20, dy -42..+24 |
| `$1B` spike | A + D | `$AC8B/$ACC3` → `$ACFD` (`CALL $033B` at `$AD0D`) | `Ex`, `Ey` | (16,24) every state | dx ±24, dy -24..+24 (box moves with Y) |
| `$21` enemy | A + D | `$B2AF` (contact) | `Ex`, `Ey` | (11,26) | dx ±19, dy -26..+24 |
| `$26` spring | C + D | state-7 callback `$82AF` (`CALL $0383`/`$0386` proximity) | none | none | `|dx| < 12` (strict), `0 <= objectY-28-playerY < 6` |
| `$27` | A + D | `$89AC`, `$89DF`, `$8A06` (`CALL $033B` x3) then `$5F3D` | `Ex`, `Ey` | (9,14) | dx ±17, dy -14..+24 |
| `$28` platform | A + D | four `CALL $033B` sites (states 1-14) + carry code | `Ex`, `Ey` | (16,16) | dx ±24, dy -16..+24 (±1 px pre-move) |
| `$50` boss | B + D | two `CALL $034D` sites; proximity `$61A5/$61B1` | `Ex`, `Ey` | (20,48) | dx ±28, dy -48..+24 |
| `$19` sign child | E | none (reads `$D522`, requests state `$20`) | - | - | - |
| `$0A`, `$0F`, `$12`, `$34` effects/children | E | none | - | - | - |

Gates and comparisons per type (all `$6328` comparisons inclusive, see section 3):

| Type | State gates | Attack gates | Direction / velocity gates | Notes |
|---|---|---|---|---|
| `$09` | callbacks run while on screen | - | none | two strict proximity tests at `$617E` (`|d| < 12`) |
| `$10` | `+$04` bit 6 set (off-screen) skips the whole callback; solid push happens for **any** overlap | `$D503` bit 1 must be set or `$A17D` returns | bit 1 (player below): pop the monitor (player vy `$0200`, monitor vy `$FE00`, state 3); bit 0 (above): blocked when requested state is `$0F/$10/$15/$1A`; above and side need `$D518` non-zero and non-negative; afterwards vy `$FC00` (except state 9) and `$5F54` | solid push first, then the rest; tie rule from `$6328` |
| `$18` | sign state 3; gate on player X speed `!= 0` or requested state `$18` | none | none | `+$03` bit 7 ignores the player's bit-6 gate |
| `$1B` | only rising and raised states (`$AC8B`, `$ACC3`); cooldown `+$1F` | side/below case needs `$D503` bit 1 and floor contact `$D522` bit 1 | skipped while the player moves up (`$D519` bit 7); above contact: damage request `$D3B0`, bounce vy `$FC00`, cooldown 16 | retract/hidden states do not test |
| `$21` | patrol states, `+$04` bit 6 clear | `$D503` bit 1 or `$D532 == 6` converts the enemy (`$5F54`) | top contact decided by `objectY - 4 >= playerY` before the attack test (bounce `$F940` via `$5F17`); else damage request `$D3B0` | no hit cooldown |
| `$26` | `+$04` bit 6 clear; requested state != `$21`; floor contact `$D522` bit 1 | none | `$D519` bit 7 clear (not moving up); launch vy `$F8A0` or `$FB00` by parameter | uses proximity, not `$6328`; `|dx| <= 11` |
| `$27` | active states 1-3 | `$5F3D`: nibble non-zero, then `$D532 == 6` or `$D503` bit 1 converts; otherwise nothing is written | none | no damage request from the object itself |
| `$28` | states 1-14, per-state callbacks | none | reads `$D518/$D519`; writes `$D511/$D514/$D521` (carry) | geometry only audited |
| `$50` | states 6..18 | `$D503` attack bits; cooldown `+$1E` | see `docs/object-50.md` | solid push then reaction logic |

Only `$6328`/`$5FA0` read the extents; `$26` and `$09` never do, so the `9 x 18 → 8 x 24` correction cannot affect them.

## 6. Terrain, spikes and related geometry

**BYTE-VERIFIED (`$3686`) + opcode scan.** Terrain does not use the overlap extents at all:

| Mechanic | Geometry | Depends on `Ex/Ey`? | State-dependent? |
|---|---|---|---|
| floor contact | lookup at player X, Y + 18 (anchor correction `$D35A`, `docs/ram.md`) | no | no |
| side walls | probes at X -9 and X +9, Y -12 (+18 added by the lookup): `$D498/$D49A = $FFF7/$FFF4`, `$D49C/$D49E = $0009/$FFF4` | no | no: the only writes of `$D498..$D49E` are the `$3686` initializer and the Y reset `$3F50/$3F54` |
| ceilings | position lookups (`asm/recovered/ceiling_collision.asm`); not audited further, but the byte scan proves they never read `$D52C/$D52D` | no | not audited |
| layout (terrain) rings | one terrain cell at player X + 0, Y - 26 (Y - 16 when animation timer `+$07` bit 0 is set) via `$7725` | no | via a timer bit |
| placed rings `$09` | anchor box `|dx|,|dy| < 12` | no | no |
| moving spikes `$1B` | `$6328` with (16,24), states 1-2 only | yes | states 1-2 |
| loops / twist strips | position-table lookups (`docs/twist.md`, `docs/continuation-01.md`) | no | cursor-driven |
| static spike terrain tiles | located later: type 5, blocks `$3C/$3D`, foot probe only (`docs/platform-spike-collision-audit.md`) | no | no (only `+$03` bit 7) |

Flags for POC fixtures: anything that models the side probes with a different half-width than 9, or the foot with a different offset than +18, is wrong; the POC adapter uses `+18` and
`chaosAnchorOffset` consistently (see section 8).

## 7. Automated oracle tests

`tests/test_collision_geometry.py` (43 tests). Cases executed against the original ROM when it is available:

| Test | Original routine | Cases |
|---|---|---|
| overlap model vs `$6328` (random, edge and structured grids, 4 outputs compared) | `$6328` | 62,400 (cache) + 3,000 (live) |
| solid model vs `$5FA0` (position, velocity, state, flags) | `$5FA0` | 20,000 |
| player extents per state (engine, 5 speeds, 2 player types) | `$64FA` | 52 states × 5 speeds × 2 types |
| emulated random play extents | full game | 8,000 frames |
| object box sweeps (real callbacks) | `$A16C $ACC3 $89AC $89DF $879A $86A1 $B2AF` | 7 × 10,101 cells = 70,707 |
| spring `$82AF` sweep and gates | `$82AF` | 3,280 cells + 5 gate cases |
| proximity `$61A5` and ring box `$617E` | `$61A5`, `$617E` | 16 |
| goal sign live sweep | `$A88E` | 4,941 cells |

Cache-driven tests check the recorded results, the pure models (edges, ties, gates, wrap) and the audit lists (`--check` and `verify_cache.py` regenerate everything).

## 8. Audit of existing research and POC assumptions

Searched: research tools, docs and caches for `D52C/D52D`, `(9,18)` and related constants; POC scripts, objects, sprite metadata and `verification/` files (read-only).
The POC contains **no** `9 x 18` player-extent constants. Its `18` is the terrain foot offset (correct). Its object contact uses GameMaker sprite masks
(`SPR_player_mask`, bbox x 16..26, y 3..33, origin (20,20)) or hand-written thresholds, so the question is whether those reproduce the ROM boxes.

POC mask in ROM anchor coordinates (`chaosAnchorOffset = 18 - (33 - 20) = 5`): x `-4..+6`, y `-12..+18`. The ROM treats the player as x `-8..+8`, y `-24..0`
around the anchor (section 3). The two regions differ in width (11 vs 17 px) and in vertical placement, so a mask overlap is not the ROM test even when an object's numbers match.

| # | Where | Assumption | ROM | Class |
|---|---|---|---|---|
| 1 | `tools/thz1_object_10.py` `_contact_oracle` and `overlap_contact()` defaults | player `9,18` | `8,24` | TEST-ONLY |
| 2 | `data/rom-cache/thz1/object-10.json` `overlap_boundaries` | horizontal 19 contacts, bottom 19 does not | right edge is 18; bottom reach is 24 (recomputed: cells 19 right and 19 bottom flip) | TEST-ONLY |
| 3 | `docs/object-10.md` overlap/solid numbers | values of the `9,18` fixtures | see section 4 | TEST-ONLY |
| 4 | `tools/thz1_object_21.py:189-190` | `9,18` | `8,24` (fixtures at dx 0, dy 0..4: results unchanged) | TEST-ONLY |
| 5 | `tools/thz1_object_27.py:255-256` | `9,18` | `8,24` (fixtures at 0,0: unchanged) | TEST-ONLY |
| 6 | `tools/object_50.py:652`, contact matrix text "player extents X 9, Y 18" | `9,18` | `8,24` (all matrix cells are inside both boxes: unchanged) | TEST-ONLY |
| 7 | `tools/player_state_11.py:23,49` | `9,18` | `8,24` | TEST-ONLY |
| 8 | `tools/thz2_thz3_object_deltas.py:94-95` | `9,18` | `8,24` | TEST-ONLY |
| 9 | `docs/object-50.md` section 8 geometry sentence | `9,18` | `8,24` | TEST-ONLY |
| 10 | POC spring contact `abs(dx) <= 12` | inclusive 12 | strict `< 12` (`<= 11`) | EDGE |
| 11 | POC spring contact has no floor test | triggers airborne in the window | needs `$D522` bit 1, not moving up, requested state `!= $21` | EDGE |
| 12 | POC spring window `foot in [layoutY-3, layoutY+2]` | 6-pixel window | `playerY in [objectY-33, objectY-28]` (6 px, `+18` foot conversion consistent) | NOT A BUG (offset from `layoutY` not re-derived) |
| 13 | POC spike damage: mask bbox vs `x ±16` and visible height | mask box | `$6328` (16,24): dx ±24, dy -24..+24 on the moving anchor, downward-velocity and cooldown gates | EDGE |
| 14 | POC platform `bbox_right >= x-16 and bbox_left < x+16` | mask ±16 | `$28` overlap (16,16): dx ±24 | EDGE |
| 15 | POC `OBJ_chaos_object_27` (badnik parent, generic collision) | mask overlap | `$6328` (9,14): dx ±17, dy -14..+24; attack gate `$5F3D` | EDGE |
| 16 | POC rings `place_meeting` | mask overlap | placed rings: 23 x 23 anchor box (`$617E`); layout rings: terrain probe at (0,-26/-16) | **CRITICAL** |
| 17 | POC monitors (`SCR_monitor_collisions`, solid) | solid mask collision, break on any jump/spin overlap | `$5FA0` box ±18 / ±24 with pop, velocity and requested-state gates (section 5) | **CRITICAL** |
| 18 | POC goal sign adapter `x >= signX + 10`, `y > signY - 108` | adapter | see `docs/object-18-act-clear.md` | **CRITICAL** |
| 19 | POC player mask, one constant for every state | constant mask | constant ROM extents (`8,24`, `9,24` in `$0F`) | NOT A BUG (intentional adapter) |
| 20 | POC terrain probes `+18`, side sensors | constants | `+18`, ±9 / -12, state-independent | NOT A BUG |
| 21 | POC type `$21` | not implemented | - | NOT A BUG (nothing to compare) |

Classification notes:

* **CRITICAL** (#16-#18): the rule itself differs, so gameplay results change: which positions collect a ring, how far from a monitor Sonic can hit it and from which side,
  and where the goal sign triggers.
* **EDGE** (#10, #11, #13-#15): same general behaviour, different boundaries or rarely-hit gates.
* **TEST-ONLY** (#1-#9): the recorded fixture results are valid for the extents they used, but their numbers do not describe Sonic. Only the type-`$10` boundary table (#2) actually
  contains now-wrong expectations (right edge 19 and bottom edge 19); type `$21/$27/$50` fixtures happen to sit inside both boxes.
* No entry is marked wrong merely because it looked right in Windows testing: the classes come from the ROM rules above.

## 9. What appears correct despite the old assumptions

* Terrain: `+18` floor anchor and ±9/-12 side probes are the original constants and never use the extents.
* The POC spring window width (6 px) and its `+18` foot conversion; only its X tolerance and airborne gate differ.
* All research results for types `$21`, `$27`, `$50` and the `$10` top-edge/reward logic: their fixtures never depended on `Ex/Ey`.
* The goal-sign research (`docs/object-18-act-clear.md`) already uses `8,24`.

## 10. Unresolved

* Static spike terrain tiles were located and audited in `docs/platform-spike-collision-audit.md`.
* Player states above `$33` and player types other than 1/2.
* Frames selected by callbacks rather than scripts are covered only by the 8,000-frame emulated sample.
* The unused overlap variant `$640B`: no direct caller found; a computed jump was not excluded.
* Type `$28` and `$26` side behaviour (carry, launch) beyond contact geometry; how `$D523` is produced.
* POC masks were not executed (GameMaker bbox rounding, per-subimage masks); the POC mask numbers are read from project metadata.
* Why the layout-ring probe depth alternates with `+$07` bit 0.

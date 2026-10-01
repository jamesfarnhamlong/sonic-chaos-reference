# THZ platform and spike collision audit (type `$28` platforms, type-5 terrain spikes, type `$1B` moving spikes)

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified; never committed).
`SonicChaos_POC_thz1_cleanup` @ `7799c34` was **read only** (never run, never modified).
Machine-readable facts: `data/rom-cache/platform-spike-collision.json` (numeric labels only). Tool: `tools/platform_spike_collision.py`.
Tests: `tests/test_platform_spike_collision.py` (cache-driven plus ROM-backed regeneration); `tests/verify_cache.py` regenerates the cache (~2.5 min).
Builds on `docs/collision-geometry-audit.md` (`$6328`, `$5FA0`, extents 8x24) and `docs/spring-interaction-audit.md` (terrain pipeline, floor flag).

Evidence labels: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY**, **SOURCE-TRACED BEHAVIOR**, **CONTROLLED ROUTINE RESULT** (original Z80 routines on `tools/oracle.py`),
**EMULATED ORIGINAL FRAME** (whole game in `tools/sms_frame_harness.py`, snapshot-forked, Sonic and camera teleported), **POC SOURCE (READ-ONLY)**, **UNRESOLVED**.
Notation: `dx = playerX - objectX`, `dy = playerY - objectY` (anchors `$D511/$D514`, object `+$11/+$14`); extents of Sonic `8 x 24` (`$D52C/$D52D`).

## 0. Identity correction: `$28` is the platform, `$1B` is the moving spike

The task text suggested `$28` might be the moving-spike object. It is not. **CONTROLLED + BYTE-VERIFIED**:

| Type | Role | THZ1 / THZ2 / THZ3 placements |
|---|---|---|
| `$28` | moving/sagging **platform** (support, carry; no damage anywhere in its code) | 6 / 3 / 0 |
| `$1B` | **moving (retracting) spike** (damage helper `$ACFD`) | 4 / 0 / 1 (THZ3 `(752,128)` is outside this audit) |
| terrain type 5 | **static spikes** (no object): blocks `$3D` (THZ1 x4, THZ2 x3) and `$3C` (THZ2 x2) | cells, see 4 |

The earlier "type `$28` contact around +-24 X, -16..+24 Y with a +-1 move" is the **platform's** `$6328` box (extents 16x16 vs Sonic 8x24). The moving-spike box is
extents 16x24 and its *damage* region is a cone (section 7), not that box.

## 1. Platform mechanisms (THZ1/THZ2)

### 1.1 Inventory (BYTE-VERIFIED + DECODED)

Object code: bank `$1E` (file `$78000`), state scripts `$8439` (15 states), placement creator `$700EB` (bank `$1C`). The ROM supports 15 states; **only two are placed** in THZ1/THZ2/THZ3:

| Placement (act, record, world X,Y) | param | aux1 | state | callback | behavior |
|---|---|---|---|---|---|
| THZ1 #1 (592,464) | `$0A` | `$09` | 11 | `$86DA` | vertical lift: Y speed -1.0 initially, reverses every 144 updates |
| THZ1 #2 (3664,512) | `$0A` | `$0D` | 11 | `$86DA` | reverses every 208 updates |
| THZ2 #1 (552,720) | `$0A` | `$19` | 11 | `$86DA` | reverses every 400 updates |
| THZ2 #2 (3672,608) | `$0A` | `$13` | 11 | `$86DA` | reverses every 304 updates |
| THZ1 #3..#6 (1040,384) (1136,320) (1232,256) (1328,208), THZ2 #3 (1552,304) | `$84` | `$00` | 5 | `$879A` | stationary platform with weight sag (`+$25 = $FF`) |

Parameter rule (`$8585`): `state = (param & $3F) + 1`, forced to 13 when `(param & $7F)` is 5 or 11; bit 7 -> `+$25 = $FF` (sag), bit 6 -> `+$26 = $FF`; `aux1 -> +$34 / +$37`.
Reversal period `= 16 x aux1` updates (counter `$8925`, `B = $10`). Lift speed is exactly 1 px/update (script command `FF 02`: Y speed `$FF00`), up first, then down, then up (confirmed over 2 periods).
Lift extremes: record (592,464): Y 464 -> 320; (3664,512): 512 -> 304; THZ2 (552,720): 720 -> 320; (3672,608): 608 -> 304.

All 15 states (callbacks `$8585 $8628 $86A1 $8718 $8719 $879A $87B2 $87E2 $8812 $8813 $8662 $86DA $86A1 $85FE $8628`) are in the cache; states 1/2/10/12/14 are other movers (horizontal / vertical), 4/6/7 touch-triggered,
13 a stationary contact platform. **They are supported by the ROM but unplaced in THZ**, so they are recorded numerically and only the horizontal-mover carry (state 1, `+$23` X delta) was executed as a proof of the carry path.

All platform states share `$8814` (support) / `$8843` (clear) / `$8866` (gate) / `$88A0` (carry). No state has side or underside collision; all use `$6328` with the object's `+$03` bit 7 set (init), which bypasses the player's `$D503` bit-6 gate.

Other platform-like THZ mechanisms (**DECODED + CONTROLLED**): terrain-backed **one-way** surfaces. THZ1 has 9 cells of block `$0D` (flags `$41`: bit 6 one-way, type 1, vertical profile 32), 1 cell of `$AF` (`$4C`);
THZ2 13 + 1 cells. They are not objects. Their support rows are measured in 1.5. No THZ platform carries spikes or another hazard (the only hazard mounted on a moving object is the `$1B` itself, which does not carry a platform).

### 1.2 Support geometry (CONTROLLED, 89,304 cells, 0 mismatches vs the model)

Support is claimed (`$D3C0 := object id`, id = `((IX-$D500)>>6)+1`, 9 for slot `$D700`) when **all** hold, in this order inside the platform callback:

1. state 11 only: `$8908` keep-alive (removal when `+$04` bit 1 and the player is >= 640 px in X or >= 672 px in Y away); state 5 only: `+$04` bit 6 clear (the object is on-screen/active; lifts keep running when inactive-flagged).
2. gate `$8866` passes: **platform Y speed `<=` player Y speed** (signed 8.8). The returned `$FF` is exactly `platformVy > playerVy`; 6,417 cases, 0 mismatches; thresholds: platform -1.0 -> player vy >= -1.0, platform 0 -> >= 0, platform +1.0 -> >= +1.0.
3. owner: `$D3C0` is 0 or this object's id (another owner -> this platform releases nothing and claims nothing).
4. `$6328` contact between Sonic (x +-8, y [-24,0]) and the platform box (x +-16, y [-16,0]); the platform's own `+$03` bit 7 ignores the player's bit-6 gate. The helper keeps one axis: **the contact bit must be "player above" (bit 0)**, i.e.
   `-16 <= dy <= -1` and `|dx| <= 8 + |dy|` (and `<= 24`): a **triangular** region (vertical beats horizontal when `24-|dx| >= 16-|dy|`).

| dy (pre-test anchor) | -16 | -15 | -14 | -12 | -8 | -4 | -2 | -1 |
|---|---|---|---|---|---|---|---|---|
| support dx range | +-24 | +-23 | +-22 | +-20 | +-16 | +-12 | +-10 | +-9 |

All comparisons are inclusive (`<=`), `dx = 0` takes the right-hand branch, strict/inclusive edges are those of `$6328`. Player anchor (not foot) and platform anchor (`+$11/+$14`) are used; **the tested platform Y is the post-move Y for movers
(`$0338` runs first: relative to the pre-move anchor the lift's region is dy -17..-2 while rising, -15..0 while descending) and the pre-sag Y for state 5** (`$8814` runs before `$88FB`).

Inputs that do NOT matter (CONTROLLED, all 52 player states and both floor-flag values): the player's current/requested state, floor flag `$D522`, attack posture `$D503` bit 1, airborne bit `$D503` bit 0, `$D503` bit 6, player extents `9,24` (state `$0F`).
Inputs that matter: Y-speed gate, owner, platform `+$04` bit 6 (state 5), platform `+$03` bits 7/6, anchors.
Incoming Y speed matters only through the gate (a player must be moving at least as fast downward as the platform); being descending is **not** required (vy = 0 passes a stationary or ascending platform).
Boundary sweep: every `dx, dy` in [-30,30] x [-30,30] against 12 player speeds, +-1 around every edge: 44,652 cells per mechanism.

### 1.3 Carry and update order (CONTROLLED + EMULATED)

Per frame the **player is updated first**, then the object list in slot order. Recorded order (PC hooks) for a rider on the first lift:

```text
player callback -> $3FEF { X integration $402A, Y integration $4097 (returns at once: grounded and $D3C0 != 0),
                           terrain $690B {floor, merge $64CB, sides, ceiling, ring probe, merge}, damage gate $48BC }
lift callback $86DA -> move $60FB -> support $8814 -> overlap $6328 -> carry $88A0
```

`$88A0` (carry): **player Y := platform Y - (+$2D - 2) = platform Y - 14** (post-move, post-sag platform Y) and **player X += platform X delta of that update** (`+$23/+$24`, = new X - old X computed after the move).
No speed is touched (player X/Y speed stay exactly what they were; after landing on the rising lift the stored vy stays `$0190`/`$01F0` etc.). The lifts and sag platforms have X delta 0, so **they carry only in Y**; the horizontal carry (state 1) was verified: platform dx = player dx for every update, dy constant -14, vx unchanged.

Support lifecycle (EMULATED, whole game):

| Event | Result |
|---|---|
| landing from above | claim in the platform phase of update N (player Y snapped to platform Y - 14); the player pass of update N+1 still integrates as airborne; the landing (`$45CE`, requested state 5, `$D503` bit 0 cleared) is registered from merged flag `$D523` bit 1 at the end of that pass. `$D522` (terrain floor flag) stays 0 on a platform. |
| standing | `$4097` skips Y integration (grounded with `$D3C0 != 0`); the platform re-snaps Y every update: player Y - platform Y = -14 constant (rising and falling lifts) |
| reversal (rider vy >= +1.0, e.g. landed with vy `$0190`) | support continuous through the reversal |
| reversal with retained vy < +1.0 | support lost on the reversal update, Sonic falls 1-2 updates (2 px), re-claims at the next update (vy `$0130 >= $0100`) |
| landing on a **descending** lift | claim only once the player's own downward speed >= +1.0 (e.g. start vy 0 claims at update 13 with vy `$0340`); never carried slower than that |
| step off the edge | support ends when contact turns horizontal-dominated: with the rider at dy -14 the last supported `|dx|` is 22 (right: dx 22 supported, 24 released; left: -21 supported, -23 released at 2 px/update); the same update the player pass has already moved him |
| jump | jump sets vy -4.25 in the player pass; the platform phase of the **same** update sees vy < platform vy, clears `$D3C0` (the carry is skipped) |
| leaving support | `$8843`: sag counter released, mirrored side bits cleared, `$D3C0 := 0` only if this object owns it; the state setters (`$476D`) also clear it |

Weight sag (state 5, `+$25 = $FF`): while supported the platform sinks 1 px/update for 8 updates (`+$35` 0..8), holds one update at 8 (`+$33 := $FF`), then rises 1 px/update back to 0 **while still supported**, then rests. Offsets by update: `1 2 3 4 5 6 7 8 8 7 6 5 4 3 2 1 0`;
the rider's Y follows (platform Y - 14). Released: rises 1 px/update until the counter is 0.

Other `D3C0` readers: `$3714/$375A` (state handlers skip writing camera byte `$D289` while supported), `$40A9` (Y integration), `$64CF` (merge of object contact flags is done while supported even in attack posture), `$73CE` (the ceiling pass runs even with floor flag set).

### 1.4 Side and underside behavior (CONTROLLED + EMULATED)

THZ platforms are **top-only, no projection**. `$8843` clears the mirrored side bits (`$D521 &= $33`) whenever the contact is not "above". Verified: side contact leaves no `$D523` wall bit (walker or attacker); a non-attacking
player's underside contact sets `$D523` bit 0 (ceiling) but **no code reads it** (no `BIT 0,(IX+$23)` in the ROM; `$5FA0` is not used by `$28`), so jump-through is real: rising from below (attacking `$0A`, 12 updates, or non-attacking spring `$0B`) never claims support and changes no speed;
running through the platform at its height (4 px/update, 24 updates) is also unaffected. One-way-ness is therefore **intentional**: it comes from the `bit 0` ("player above") filter and the contact box, not from a speed gate. The box is 32 wide against steps of at most 7 px, so there is no tunnelling case inside the box;
the only way to miss a platform that Sonic overlaps is the Y-speed gate: landing on a **descending** lift while moving down more slowly than 1.0 px/update (above), or an overlap that starts with the player already below the anchor (`dy >= 0`).

### 1.5 Terrain-backed one-way platform (block `$0D`) (CONTROLLED, 16,144 cases)

Flags `$41`, vertical profile 32, horizontal `$60`; no side/ceiling core runs (bit 7 clear): 0 side pushes, 0 ceiling pushes. Floor projection (`$6F61`, previous surface bit 6): **skipped while rising**, accepted for foot rows 1 .. 8 + (vy high byte) of the cell
(vy 0 -> rows 1..8; +1 -> 1..9; +2 -> 1..10; +4 -> 1..12; +7 -> 1..15), independent of the floor flag; requires the previous sample's flags to be one-way/solid (previous = air -> no projection that update). A solid previous surface (`$81`) accepts rows 1..31.

## 2. Static terrain spikes

### 2.1 Which blocks and cells (DECODED)

| Block | flags | type | profiles | THZ1 cells | THZ2 cells |
|---|---|---|---|---|---|
| `$3D` | `$85` | 5, solid | vertical 16 for all 32 columns; horizontal rows 0..15 = `$40`, rows 16..31 = `$60` | (47,26) (48,26) (69,26) (70,26) = world (1504,832) (1536,832) (2208,832) (2240,832) | (64,26) (41,27) (51,27) = (2048,832) (1312,864) (1632,864) |
| `$3C` | `$85` | 5, solid | identical to `$3D` | - | (106,8) (13,22) = (3392,256) (416,704) |

`$85` = bit 7 solid + terrain type 5; no alternate plane, modifier 0. The vertical profile 16 puts the spike **surface at block row 16**; rows 0..15 are empty for the foot probe. No THZ layout contains tiles `$3E/$3F/$F4/$F5` (the only other type-5 damage tiles).
The historical `$3D / $85` question is answered: `$3D` (and `$3C`) are the **only** type-5 cells, and the type-5 floor handler `$6ACE` is the **only** damage entry for them.

### 2.2 Probes and damage (BYTE-VERIFIED + CONTROLLED)

Probe geometry: foot `(X, Y+18)`, right side `(X+9, Y+6)`, left side `(X-9, Y+6)`, ceiling `(X, Y-6)` (anchor Y; `$7666` adds 18). Terrain never uses the extents.

- **Foot (`$6ACE`, dispatched on the NEW sample's low 5 flag bits after the projection of the PREVIOUS surface)**: `tile & $FE != $F4`, floor flag `$D522` bit 1 set, `+$03` bit 7 (invulnerable) clear, then `JP $48F7` (hurt/death). Nothing else (no state, no speed).
- **Sides (`$7306` right / `$7329` left)**: type 5 is an ordinary wall (`$71B8`/`$725D` projection, rows 16..31 only; profile rows 0..15 = no extent). Damage only for tiles `$F4`/`$F5`; requested state `$17` takes the breakable branch, requested state `$1E` (hurt) returns without pushing.
  0 side damage cases in 11,864; the wall pushes the player to the block edge for probe rows 848..863 (cells) and the ground block rows beneath.
- **Ceiling (`$74E7`)**: no push (vertical profile 16, bit 6 clear: the ceiling core returns), damage only for tiles `$3E/$3F`. 0 damage cases, 0 pushes.
- Solid? Yes for the foot and the sides; **not** solid from below.

Foot-probe table (101,376 cases, whole pair x 1504..1567, foot rows 824..871 relative to the cell at 832..863; previous surface x floor flag x Y-speed class):

| floor flag `$D522.1` | previous surface | player Y speed | damaging foot rows of the cell |
|---|---|---|---|
| set (grounded) | any (air, `$81`, `$85`) | any (even rising) | **832..863** (the whole cell) |
| clear (airborne) | solid `$81` or spike `$85` | `>= 0` | **848..863** (rows 16..31) |
| clear | solid/spike | negative | none (projection and hazard skipped while rising) |
| clear | air `$00` (first sample into the cell) | any | none that update |

All edges are `<=` on the integer rows/columns above; the floor flag persists until a state setter or the empty-floor handler clears it (it is NOT recomputed each update), which is why a grounded Sonic is hurt in any row of the cell.

### 2.3 Diagonal static-spike phasing (priority question) - result: **D (depends on collision order and vertical direction), deterministic, not glitchy**

Evidence: 1,446 emulated runs (jump/fall, vx -6..+6 px, vy -2/0/+3 px, starts left/right/above, plus walk/run/roll on the ground), 160 natural jump runs, 4 controlled rows.

- **A damaged**: every approach in which the foot probe ends up in rows 848..863 while level or descending (previous surface solid), and every grounded foot in the cell.
- **B stopped/projected**: ground-level approaches (walk, run, roll, any speed 1..7 px) and low jump arcs hit the **side wall** (probe `Y+6` in rows 848..863, anchor Y >= 842) and are pushed back to X = 1495 (right-moving) / 1576 (left-moving); never damaged.
- **C passed**: arcs that clear the pair in the air (rising jumps over the pair).
- **The only undamaged contact is while rising**: for anchor Y 830..841 the foot probe is inside the solid rows (848..859) but the side probe (`Y+6` = 836..847) is above the wall rows. A **rising** player (Y speed < 0) there is **neither projected, nor damaged, nor pushed** (CONTROLLED: damaged anchor Y for vy -1.0 = none; for vy 0 and +1.0 = 830..845).
  So a rising diagonal jump can pass through the upper-left/upper-right corner of the spike band. In the 1,446-run grid 516 runs contained at least one such rising update; 482 of them were damaged later (they came down onto the spikes) and 34 ended undamaged. 0 of the 160 natural jump runs (standing start beside the pair, direction held, jump length 1/4/8/16 updates) reached the solid rows undamaged (classes A/B/C/D only),
  The only level/descending undamaged foot samples ("E2", 2 teleport starts per state) begin with the foot already inside the last 3 columns of the block with previous surface = air and leave the block on the next update; no approach from outside produces them (a natural entry always has more than 50 columns left, so a second sample inside the block is guaranteed).
- **One-update lag**: a first foot sample in the solid rows with previous surface = air (horizontal entry through the 12-pixel band) does nothing; the next update (previous = `$85`) projects to anchor Y 830 and hurts. Damage after entry is therefore delayed by one update but not avoided.

**Source-model mismatch candidates for the POC (not proven POC bugs)**: any model that (a) damages or blocks a rising player in the 12-pixel band, (b) skips the "previous surface" gate, (c) makes the side wall extend over rows 0..15 of the cell, or (d) clears the floor flag in a way the ROM does not, will differ in exactly these places. The POC's `SCR_cc_floor` type-5 branch has the same three conditions as `$6ACE`; the phasing is therefore POC-side or related to its floor-flag bookkeeping and needs a POC replay (not done).

### 2.4 Aftermath and repeated contact (EMULATED)

Landing on the pair with 5 rings: hurt at the update the foot reaches row 16 (anchor Y 830), state `$1E`, rings 0, `$D3B1 = $78`, vy -4.0, vx -1.0, `+$03` bits 7|6 set 120 updates; the player lands again on the spikes and, **when the invulnerability ends, is hurt again immediately (second hit = death with 0 rings)** (hurt entry count 2 in 200 updates).
With no rings the first hit is death (`$1F`, vy -5.0). While invulnerable, spike terrain is simply solid ground (the handler returns at `+$03` bit 7).

## 3. Moving spike `$1B`

### 3.1 Placement, order, timing (CONTROLLED)

THZ1 x4 at Y 864 (X 1344, 1936, 2464, 2912), flags 0, param 0, no THZ2 record. Extents 16x24 (every state). Scripts (bank 12): cycle **102 updates**: hidden (state 4) 48, rising (state 1) 3 (Y 858, 852, 846), raised (state 2) 48 at 846, retract (state 3) 3 (852, 858, 864).
Movement is 6 px/update up to 18 px (`+$3C - Y == 18`), down to `+$3C`. **The contact helper `$ACFD` runs in states 1 and 2 only and BEFORE the Y move in state 1** (damage rows -24..-1 are relative to the pre-move anchor 864; verified: the damage rows do not move to the post-move 858).
`+$04` bit 6 (inactive) skips the whole callback; state 3/4 never test.

### 3.2 Contact and damage (CONTROLLED, 89,304 cells, 0 mismatches)

`$6328` box: x +-24 (8 + 16), y [-24, 0] (player below-anchor reach 24). The helper reads the contact bit:

- **"player above"** (`dy` in -24..-1 and `|dx| <= |dy|`, `|dx| <= 24`) and player Y speed `>= 0` and cooldown 0 -> damage request `$D3B0 := $FF`, **bounce `$D518 := $FC00` (-4.0)**, cooldown `+$1F := 16`. The damage region is a **45-degree cone** (dy -24: dx +-24 ... dy -1: dx +-1), not the box.
- side/below contact: never damages. A **grounded player in attack posture** (`$D522` bit 1 and `$D503` bit 1) is pushed to X = objectX +23 (right contact) or -23, requested state 1, X speed 0. A **non-attacking** player is not pushed, but the side contact becomes `$D523` bit 2/3 (a **wall**: his X integration stops;
  emulated: walking at 3.7 px/update stops at objectX - 18, two updates after the contact because the merged flag is read by the next X integration).
- gates: cooldown (16 updates, decremented only in states 1/2), `+$04` bit 6, player rising (`$D519` bit 7): no request. The player's invulnerability and `$D503` bit 6 are **not** checked by the helper (the request is written and the bounce applied; `$48BC` then ignores the request while `+$03` bit 7 is set: an invulnerable player just bounces).
- The helper does not project the player vertically; attack posture changes nothing for damage.

Emulated chain (0 rings 5): contact in the object phase of update N (request + bounce), the player's update N+1 integrates once with vy -4.0 and `$48BC` consumes the request at the end of that pass -> hurt entry at N+1.

## 4. Damage and invulnerability (limited to what spikes need)

- **Terrain hazards** call `$48F7` directly after testing `+$03` bit 7; **object requests** go through `$48BC` (60 combinations in the cache): `+$03` bit 7 -> countdown `$49F7` (any request ignored and kept), bit 6 -> `$4A2E` (clears `+$20`), `$D532 == 6` -> request cleared, request `$D3B0` or contact `$D520 != 0` (not attacking) -> `$48F7`.
- **`$48F7`**: rings 0 -> state `$1F`, vy `$FB00` (-5.0), `+$04 := 0`. Rings > 0 -> state `$1E`, rings := 0, `(rings >> 4) + 1` type-`$06` scatter objects capped at 7 (1, 1, 2, 3, 5, 7 for 1, 15, 16, 32, 64, 100 rings), `$D3B1 := $78`, `+$03 |= $C1`, floor flag cleared, vy `$FC00` (+`$0100` when `+$22` bit 0), vx `$FF00` (+`$0100` when `$D523` bit 3). **Knockback direction depends only on the left-wall bit, not on the hazard side.**
- **Invulnerability**: `$D3B1` counts 119 .. 0 once per `$48BC`; the bits are cleared on the 121st gate update after the hit and a pending request is discarded then. Hurt state `$1E` control lock lasts until landing (observed 42 updates in the static-spike aftermath before requested state 5).
- Repeated contact: with rings, a second hazard contact inside the 120 updates only bounces (`$1B`) or is ignored (terrain); a contact in the update the invulnerability ends hurts again.

## 5. Player-state exclusions (EMULATED, `+$01 = +$02 = state` plus the script pointer cleared so the engine reloads that state's callback; Sonic then teleported into the hazard)

| State | static spike (floor probe) | platform support | `$1B` request |
|---|---|---|---|
| `$01 $05 $06 $09 $0A $0E` stand/walk/run/roll/jump/fall | hurt on the first update | claimed | written, hurt next update |
| `$0B` spring, `$1C` diagonal spring | hurt | claimed | written |
| `$22` twist | hurt | claimed | written |
| `$1E` hurt, `$1F` death, `$20` act-clear | the terrain pass runs and the handler has **no state gate** (only `+$03` bit 7, which the forced states did not carry) | claimed | written (`$1F`: no hurt consequence observed) |
| `$0C $0D $13` loop | terrain pass runs (hurt) | **not exercised**: the loop handler leaves/repositions within 1-13 updates; no conclusion | not exercised |

The platform and spike code reads no player state; every difference above comes from the state handlers (which call `$3FEF` or not, and who reposition). The oracle shows `player_current_state_irrelevant` for all 52 states for the platform.

## 6. Interaction order (EMULATED)

Inside one update: player callback -> X integration -> Y integration -> terrain (floor probe + projection, **type-5 handler and `$48F7` here**, sides, ceiling, ring probe, merge) -> `$48BC` -> objects (`$06` scatter, `$1B`/`$28`/`$26`/`$21` in slot order).
Consequences:

- terrain projection and the static-spike hurt happen **before** the platform contact test of the same update; the platform never reads the hurt state;
- a synthetic platform (cloned type-`$28` slot over the spike pair; no THZ placement overlaps a spike cell) at Y <= 835 holds Sonic clear of the spike surface (support only); within about one fall step of the surface, or with a sinking sag platform, the next player pass moves the foot onto the surface and the terrain hurts him; at Y >= 845 the terrain hurts him before any contact;
- `$1B` request/bounce are written **after** the player's pass, so the hurt is one update later than the contact and the bounce velocity is integrated once first;
- THZ platforms never move horizontally, so the "platform carrying Sonic horizontally across spike terrain" case does not occur in THZ1/THZ2/THZ3 placements (the unused state-1 horizontal mover exists in the ROM).

## 7. Presentation versus gameplay anchors (EMULATED + DECODED)

| Object | canonical placement | runtime anchor | collision anchor / probe | sprite opaque rows (rel. anchor) |
|---|---|---|---|---|
| `$28` platform | record X,Y | `+$11/+$14` (lift Y moves, sag adds 0..8) | box x +-16, y [-16,0]; rider anchor = platform Y - 14 (equivalent foot row Y + 4) | +2 .. +17 (measured lines 103..118 at anchor 384) |
| Sonic on it | - | - | anchor | -13 .. +17 (measured 357..387) |
| `$1B` | record X,Y = 864 | +$14 864 -> 846 | box x +-16, y [-24,0], cone for damage, player anchor | -6 .. +17 |
| static spikes | layout cell | - | foot (X,Y+18), sides (X+-9,Y+6), ceiling (X,Y-6) | block art |

Visible overlap: Sonic's last opaque row (platform Y + 3) is two rows into the platform's first opaque row (Y + 2); the collision top (Y - 16) is 18 rows above the visible top. **That gap is canonical; a GameMaker presentation offset must not be folded into support geometry.**
World row of a sprite line = line + camera Y + 17.

## 8. Read-only comparison with POC `7799c34` (nothing is called a bug unless ROM-backed)

| Area | POC (source read) | ROM | Verdict |
|---|---|---|---|
| static spike probing | `SCR_cc_floor` kind 5: not `$F4/$F5`, `(bg & 2)`, `(player_flags & 128) == 0` after projection | `$6ACE` same three | structurally matches; outcome depends on floor-flag bookkeeping; **not proven** |
| diagonal phasing | no divergent probe found | rising band only (2.3) | POC-side cause unresolved, needs replay |
| `$1B` geometry/damage | mask bbox overlap with x +-16 and visible height in states 1/2 | cone, rising gate, cooldown, side wall, push | **CRITICAL (ROM-backed)** |
| `$1B` timing | +6 / 48 / -6 / 48, check after the move | check before the move in state 1 | EDGE |
| platform support | mask overlap x +-16, foot in [y-1, y+20], snap platform y - 19 | triangle, relative-speed gate, snap platform Y - 14 | likely mismatch; needs replay |
| speed gate / vy on landing | `vy >= 0` / vy := 0 | `p >= P` / vy retained | ROM-backed EDGE |
| carry order | platforms advanced before the player step | player first, platform after | EDGE (one-update phase) |
| THZ2 lifts | travel only for x 592 / 3664 | THZ2 (552,720) 400 and (3672,608) 304 | mismatch if the object is reused |
| sag cycle | 1..8, hold, 7..0 | identical | matches |
| damage gating | blink/invincible globals | `+$03` bit 7 / `$48BC` | not compared in depth |

## 9. Test and sweep counts

See the cache `counts` and the per-section `cases`/`runs`: platform support 89,304; gate 6,417; foot sweep 101,376; side/ceiling 11,864; one-way terrain 16,144; `$1B` contact 89,304; diagonal 1,446 emulated runs; natural jumps 160;
`$48BC` matrix 60; plus the emulated platform/spike/state scenarios. `tests/test_platform_spike_collision.py`: cache assertions and ROM-backed regeneration of every controlled section.

## 10. Unresolved

See `unresolved` in the cache: loop/twist contact not exercisable by teleport; object lifecycle (activation/recreation phase) not audited; `$D4A5` write purpose; requested-state `$17` breakable branch only located;
no recorded-input play; no POC execution; side-wall of the raised `$1B` for a non-attacking player is routine/emulation evidence, not yet visually confirmed against original-game video.

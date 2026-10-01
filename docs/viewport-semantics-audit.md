# Viewport-relative semantics audit (Sonic Chaos SMS, Europe v1.2)

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`
(verified; never committed). `SonicChaos_POC` was not touched.
Machine-readable facts: `data/rom-cache/viewport-semantics.json`. Tool: `tools/viewport_semantics.py`.
Tests: `tests/test_viewport_semantics.py` (36 tests; `tests/verify_cache.py` also regenerates the cache).

Purpose: separate what the ROM expresses in **world space** from what it expresses **relative to the camera, the screen edges, the
spawn window or the player**, so a widescreen adapter can be written once instead of per object. This document records ROM facts and
their classification. It does not prescribe GameMaker offsets.

Evidence classes: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY**, **SOURCE-TRACED BEHAVIOR**, **CONTROLLED ROUTINE RESULT** (the original
Z80 routines run on `tools/oracle.py` with explicit RAM, swept over synthetic camera positions), **EMULATED ORIGINAL FRAME** (the whole
game in `tools/sms_frame_harness.py`), **UNRESOLVED**.

## 0. Frame of reference and classes

* `cam` = camera X (`$D174`), the world X of **screen column 0** of the original 256-px scroll window. `camY` = `$D176`.
* `RIGHT` = `cam + 256` (the exclusive right edge; the last visible column is `cam + 255`). `d = x - cam`.
* `$D174/$D176` are copied from the working target `$D284/$D286` by interrupt-time code at `$0570` (inside the `$0538` output path); the follow/pan/limit routines
  write the target, the vblank copy commits it (BYTE-VERIFIED). `$4D3E` derives `R8 = -(cam+1)`, `R9 = (camY+17) mod 224`.
* Per-frame order (`$16B8`): camera `$4C90` -> player `$361D` -> objects `$5DD1` -> `$7AC2` -> **placement scan `$8000` once per 4th pass**
  (`$D2E2`, `CP 4` at `$16D9`). (BYTE-VERIFIED)

Classes used in the tables (A-F are the requested ones; **G was added** because several constants are none of A-F):

| Class | Meaning |
|---|---|
| A | WORLD-SPACE |
| B | CAMERA-RELATIVE (a function of camera position or motion, not of the screen width) |
| C | SCREEN-EDGE-RELATIVE (an offset from the left/right/centre of the 256-px window) |
| D | VIEWPORT / SPAWN-WINDOW-RELATIVE (create, sleep, delete bands around the window) |
| E | PRESENTATION-ONLY |
| F | UNRESOLVED |
| G | PLAYER-RELATIVE WORLD DISTANCE (neither camera nor screen) |

## 1. Answer in ten lines

1. **`$20` / `$121`**: class C, **exactly `RIGHT + 33`** (`playerX - cam >= 289`, 16-bit unsigned, `cam` = the committed camera `$D174`). The
   camera is **not moving** at that moment: it stopped about 280 updates earlier (pan finished) and is explicitly frozen at `d > $F8`.
2. The sign contact starts a **camera pan, 1 px/update per axis, X and Y together**, to `(signX-$80, signY-$99)` = sign at screen centre X 128.
   The right limit is exclusive, so X settles at `signX-129` (THZ1/2: 3831). The player stays inside `[cam+16, cam+247]` until state `$20`.
3. Everything the generic object lifecycle does is a function of **`max(band(x-cam), band(y-camY))`** with bands at exactly the original window
   `[0,256)` and margins of 32 / 64 / 32 px (class D, 91,000+ controlled cases, 0 mismatches). It is edge/centre symmetric; it is not a world grid.
4. Steady-state creation happens only in the outer ring `RIGHT+32 .. RIGHT+96` (and `LEFT-96 .. LEFT-32`); objects wake at `RIGHT+32`,
   are deleted at `RIGHT+96` / `LEFT-96`; at the initial fill everything out to the ring is created.
5. **Type `$27`**: no bee-specific viewport constant. Its entry is the generic ring (created at `d = 348..351`, awake at `d <= 287`, first
   pixel about `d = 267`); its `<64` trigger and `>=384` removal are **player-relative** (class G).
6. **384** is two unrelated things: the camera-relative outer bound of the 512-px lifetime window (`cam+384`, structural, class D) and, for
   `$27`, a **player-distance radius** (`BC=$0180`, class G). The type `$27` value is not derived from the screen.
7. The player edge clamp (`cam+16` / `cam+247`) is class C, uses the **low byte** of `playerX - cam`, and **teleports** the player when `d >= 256`
   (8-bit wrap). This is the most dangerous literal-port hazard.
8. The camera right limit is world data = `worldWidth - 256` (exclusive) in every THZ act; level-limit constants encode the 256-px window.
9. Boss/projectile code in later zones is full of 8-bit compares on `anchor - camera` and spawns at `cam + {-$20, 0, $20, $B0, $E0, $100}`;
   none of it is traced beyond instruction semantics (section 8).
10. Proposed vocabulary (section 9): `WORLD`, `EDGE(side,n)`, `CENTER(n)`, `PLAYER_DIST(n)`, `LOCKED_CAMERA(c)`.

## 2. Player state `$20` and act-clear (audit target 1)

### 2.1 What `$121` is

BYTE-VERIFIED + CONTROLLED. Handler `$83A6` (bank `$0C`), per update, with `d = (playerX - $D174)` as 16-bit unsigned:

```text
$83C2  d <= $F8   -> keep running (no camera action)
$83CB  d >  $F8   -> CALL $0407  (=$59B9): RES 7,$D15E  and  $D280 := $D174   [camera frozen]
$83CF  d <= $120  -> keep running
       d >  $120  -> X speed := 0, $D293 |= $20 (act index < 2) / $10   [act complete request]
```

| Question | Result |
|---|---|
| Frame | `playerX` = player anchor `$D511`; `cam` = `$D174`. Not the player's box, not the sprite. |
| Original visible width | 256 px scroll window (VDP R8/R9; R0 = `$26`, whose bit 5 masks the left 8 columns by SMS VDP documentation). |
| Threshold vs right edge | `d >= $121 = 289 = 256 + 33`: **`RIGHT + 33` exactly** (34 px past the last visible column `cam+255`). The box (`anchor +- 8`) is then entirely off-screen with >= 25 px to spare. |
| Is `+33` exact? | Yes. Swept at 22 + 11 cameras x 3 act indices: flag set iff `d >= 289`; `d = 288` never sets it (CONTROLLED, 528 + 2,496 cases). |
| Camera moving or fixed? | **Fixed.** In the emulated THZ1/THZ2 runs the pan finishes at `+6/+41` updates after contact (X/Y), `$D15E` bit 7 is cleared at `+283`, state `$20` begins at `+280`, the flag is set at `+310`. |
| Other camera limit/release | Yes, three: (a) pan target also becomes `$D282` (right limit), (b) `$D282` is **exclusive** so X stops at target-1, (c) the freeze at `d > $F8` (= `RIGHT - 7`). The effective relationship at the flag is `playerX = signX + 160` in both acts (camera 3831, `d = 289`). |
| Negative d | 16-bit compare: a player left of the camera compares as a huge `d` and sets the flag at once (not reachable). |

Relationship to world space: with the camera frozen the threshold is a fixed world X, but that X is **not** canonical data: it is
`finalCamera + 289` and `finalCamera = signX - 129` comes from the pan below. An adapter must therefore express it as
`RIGHT + 33` of *its* frozen camera, not as `signX + 160`.

### 2.2 Recovered camera behavior around `$18` -> `$19` -> `$20`

EMULATED ORIGINAL FRAME (THZ1 and THZ2, three start conditions; `cam` start X 3700/3760, RIGHT held until the flag; frame 0 = sign contact).
Controlled routine fixtures reproduce each rule.

| Update | Event | Evidence |
|---:|---|---|
| 0 | `$18` state 3 -> 4 at contact; vector `$0359`: `$D15E` bit 7 set, `$D15F` bit 0 set (pan mode), target `($D2DA,$D2DC) = (signX-$80, signY-$99)` = (3832, 405) THZ1 / (3832, 501) THZ2 | CONTROLLED (object-18) + EMULATED |
| 0 | pan mode disables the follow routine (`$5832`: `BIT 0,$D15F` -> `$5956`) for the rest of the act (reset only by `$4FCE`) | BYTE-VERIFIED |
| 0.. | every update: `X += sign(targetX-camX)`, `Y += sign(targetY-camY)` (**1 px/update/axis**); moving right sets `$D282 := targetX`, moving left sets `$D280 := targetX` (not when zone index = 6) | CONTROLLED, 900 cases |
| +6 | camera X stops at **3831**: the next step (3832) is dropped because `$4CB0` treats the right limit as exclusive and the step would reach `$D282`. The camera does not slide to the limit. | CONTROLLED (114 cases) + EMULATED |
| +41 | camera Y reaches 405 (THZ1) / 501 (THZ2): sign at screen Y 153 | EMULATED |
| +0..+279 | state 3 callback keeps raising `$D280` to the camera (`$0353`); the player keeps full control but is held in `[cam+16, cam+247]` by the edge clamp (section 4); with RIGHT held it sits at screen X 235..251 | EMULATED |
| +280 | player state `$20`; input ignored; clamp no longer applied (handler `$83A6` does not call it) | EMULATED + CONTROLLED |
| +283 | `d` passes `$F8` (249): `$D15E` bit 7 cleared, `$D280 := cam` (camera frozen; it had not moved for 270+ updates) | EMULATED |
| +310 | `d = 289`: `$D293 |= $20`, X speed 0, player X 4120 = `signX + 160` | EMULATED |

Facts versus the POC's provisional adapter (facts only; the ROM also puts the sign at screen **centre** X 128, with the settled camera one pixel left at `signX - 129`):

| POC adapter | ROM |
|---|---|
| X pan 4 px/update | **1 px/update** |
| no Y pan | Y pans to `signY - $99` at 1 px/update (41 updates in both acts) |
| camera frozen when state `$20` begins | pan has long finished; freeze at `d > $F8`, three updates after state `$20` starts |
| clear threshold `viewWidth + 33` | matches the ROM relationship (`RIGHT + 33`) |

## 3. Camera engine (audit target 4)

Only what gameplay constants depend on. Evidence: BYTE-VERIFIED + CONTROLLED sweeps (`$5832`: 2,048 cases; `$5956`: 900; `$4CB0`: 114).

| Piece | Routine | ROM facts |
|---|---|---|
| Origin | `$4D3E`, `$0570` | `cam` is the left edge of the window; `R8 = -(cam+1)`; `R9 = (camY+17) mod 224`. All object screen coordinates are `anchor - cam` (`$3FC8`, 16-bit). |
| Follow (X) | `$5832`, `$58E1` | Player screen-X target (lead): `$68` (104) facing right, `$88` (136) facing left, `$78` (120) in pan mode; the working lead moves **1 px/update** toward the new lead. Dead zone `lead +- 8`. Step `+min(7, k-(lead+8))` / `max(-7, k-(lead-8))` (a step of exactly -8 survives the clamp). `k` is the **low byte** of `playerX - target`. |
| Follow (Y) | `$5894..$58E0` | Same scheme, lead `$78`, dead zone `$68..$98`. Vertical, not affected by horizontal widening. |
| Limits | `$4CB0/$4CF7`, header +12/+14/+16/+18 | Left/top **inclusive**, right/bottom **exclusive**; a step that would cross is **dropped**, not truncated. THZ: left 0, right = `worldWidth - 256`, top 8, bottom = `worldHeight - 240`. |
| Locks | vectors `$0353/$0356/$0359/$035C/$0407/$042B` | `$0353`: `$D280 := max($D280, cam)`; `$0356`: `$D282 := min($D282, cam)`; `$0359`: pan on; `$035C`: pan off (enable); `$0407`: freeze + `$D280 := cam`; `$042B`: enable. A right lock at the camera turns the **right screen edge into the arena wall**. |
| 256-px constants | | `right limit = width - 256` (data); the player clamp literals (`$10`, `$F7`); the 8-bit compares in follow/clamp; the `(d+128)/2` byte of the lifetime window; `R9 mod 224` (vertical). |

Unresolved: whether the leads 104/136 were tuned for 256 px or are independent; the code gives only the numbers.

## 4. Player edge clamp (new, relevant to every arena and to the sign wait)

CONTROLLED, 11,264 cases (22 cameras x 256 offsets x 2 entry points) + 5,632 more in the tests with different cameras; 0 mismatches.

```text
e = (playerX - cam) AND $FF                                   ; LOW BYTE ONLY
if e <  $10: playerX := cam + $10   ; minus this update's X speed (8.8), then X speed := 0
if e >= $F8: playerX := cam + $F7   ; same compensation
```

* Entry `$4141` (from the shared player step `$3FEF`, vector `$0404`) applies it for states `< $29`; entry `$4281` is the same test for the
  `$39xx` state handlers. Player extents (`$D52C`) are **not** read: `$10` and `$F7` are literals. Numerically `$10 = 8 (masked column) + 8 (extent)`
  and `$F7 = 255 - 8`, which suggests "the 16-px box stays inside the visible columns 8..255"; the code does not say so (**interpretation, UNRESOLVED**).
* `playerX - cam = 261` (a player further right than a 256 window can hold) has low byte 5, so the **left** clamp fires: X := `cam + 16 - speed`
  (CONTROLLED sample: 261 -> 16). Any widescreen build that lets the player stand at `d >= 256` must not run the original 8-bit test.
* State `$20` is not clamped; that is why act-clear can run to `d = 289`.
* Class C: `LEFT + 16` and `RIGHT - 9` (anchor). In the sign wait the player is confined to `[cam+16, cam+247]` for about 280 updates.

## 5. Spawn / sleep / despawn windows (audit target 3)

### 5.1 Geometry (DECODED + CONTROLLED, 72,072 + 2,048 cases, 0 mismatches)

Both the placement scan (`$8000`, bank `$1C`) and the lifetime routine (`$61E1`) test the object's **anchor** (not its sprite) against one
32x32 byte map at ROM `0x70146` (bank `$1C:$8146`). Each map cell is 16 x 16 px; the index uses `(x - cam + 128)` and `(y - camY + 128)`, which
must lie in `0..511` (8-bit after halving). Every one of the 1,024 map bytes equals

```text
cell(dx, dy) = max(band(dx), band(dy)),   band(d) by u = (d + 128) >> 4:
   u 8..23           -> 0   d in [0, 256)            exactly the original window
   u 6,7 | 24,25     -> 1   d in [-32,0) | [256,288) 32-px margin
   u 2..5 | 26..29   -> 2   d in [-96,-32) | [288,352) 64-px outer ring
   u 0,1 | 30,31 / outside [-128,384) -> 3   deletion zone
```

The map is symmetric about `cam + 128`, so the data cannot tell "edge +- N" from "centre +- N"; both give the same bands for the window
`[cam, cam+256)`. **Vertically the central band is `[0,256)`**, i.e. taller than the 192-line screen.

| Cell | `$61E1` result | `$8000` creation |
|---|---|---|
| 0, 1 | bit 6 (`+$04`) cleared: **active**, SAT-eligible, state callbacks run | only during the initial fill (`$D440 == 0`) |
| 2 | bit 6 set: **asleep** (alive, callbacks return early) | **always** (this is the steady-state creation ring) |
| 3 or outside the 512 window | bit 6 set and removal: `+$00 := $FE` if the placement token `+$3E` is non-zero (cleanup `$5EF8` releases the `$D400` occupancy byte, so it can respawn) else `$FF`; **unless `+$04` bit 1 is set** (keep-alive), then it stays asleep | never |

Scan details: the record X/Y are stored `world + 256`, so the scan evaluates `(storedX - 256 - cam, storedY - 256 - camY)`; pool capacity 11 slots;
the scan runs once per 4 object updates. With a maximum camera speed of 7 px/update (section 3), the camera moves at most 28 px between
scans, less than the 64-px ring, so a record cannot jump across the creation ring in normal play.

### 5.2 What the 32 / 64 px margins are

All 32 px of cell 1 and all 64 px of cell 2 are **deliberate off-screen margin** (the window is `[0,256)`); nothing in the ROM relates them to a
sprite size. Objects wake 32 px before they can be seen and are created 64 px further out. Sprites up to ~24 px wide therefore never pop in.

### 5.3 The number 384 (audit target 3, "do not infer from arithmetic coincidence")

| Where | Frame | Value | Verdict |
|---|---|---|---|
| `$61E1` / `$8000` window bound (`LD BC,$80` + `SRL`) | camera-relative | accepted `d` is `[-128, 384)`; the deletion zone is `[352,384)` plus everything beyond | `384 = 256 (RIGHT) + 128`: structural limit of an 8-bit `(d+128)/2` byte, **not an arbitrary radius** |
| `$27` state 3 (`$8A29`, `LD BC,$0180`, helper `$61A5`) | **player-relative** `|objX - playerX| >= 384` | removal (`$FE`) | **fixed world radius from the player**; `$61A5` reads `$D511`, never the camera (swept over 33 cameras) |

They share a number but not a frame. For `$27` the radius is always reached after the bee left the screen on the **left** (the player's
screen X is at most 247, so the bee is at `<= -137`, beyond the -96 deletion edge): the 384 is "far enough past the player", not "screen width + margin".
Other player-distance values (class G): `$27` trigger 64; `$28` persistence 640 x 672 (`$8908`, keep-alive bit only); `$50` trigger `(160,256)`; `$26` 12.

## 6. Type `$27` (flying bee) from a viewport view (audit target 2)

| Question | Answer |
|---|---|
| What makes it wake? | Generic `$61E1`: anchor leaves the asleep ring and enters cell 0/1: `d < 288` (`RIGHT + 32`) and the Y band <= 1. Bit 6 clears and state-1 movement starts. No `$27`-specific bound. (EMULATED: awake at `d = 287/286/286` for camera steps 1/2/3 px per frame.) |
| What creates it? | Scan `$8000` once per 4 updates: steady scrolling right creates it when `d` is in `[288,352)` (EMULATED: first created at `d = 351/350/349`); first creation at initial fill covers the whole `d < 352`. Camera ranges for the three THZ1 records: creation `x-351 .. x+96`, active `x-287 .. x+32` (CONTROLLED, ROM-checked at every camera). |
| What is margin? | The 64-px creation ring `[288,352)` and the 32-px margin `[256,288)`: nothing of the bee is drawn until its first pixel (`d = 267`, frame art spans `d-12 .. d+11`). It stays asleep for about 62 camera pixels after creation (`d` 350 -> 287), then walks 2.5 px/update: about 8 updates between waking and the first pixel. |
| Where does it "enter"? | Result of **all three**: canonical anchor (it sits still at its placement until woken), the wake edge `RIGHT + 32` (decides when it starts moving, in camera terms), and the camera's scroll history. A bee that is woken stands `32` px beyond the right edge; it then travels left and its position relative to the player depends on the player's speed. |
| What leaves it? | Before the 64-px trigger: generic deletion at `RIGHT + 96` / `LEFT - 96` (`$FE`, respawns later). After the trigger `+$04` bit 1 is set: generic deletion is disabled and state 3 removes it at `|dx| >= 384` from the player (`$FE`); a defeated bee is detached from the occupancy byte and never respawns. |
| Widescreen implication | The placement is canonical and stays. The activation/lifetime boundaries are `EDGE(right, +32/+96)` / `EDGE(left, -32/-96)` rules (class D) that currently assume `RIGHT = cam + 256`. The trigger (64) and the 384 removal are `PLAYER_DIST` rules and need no adaptation. No bee-specific offset is supported by the ROM. A wider view with unadapted generic bands would leave `x in [cam+256, cam+W)` either un-created or asleep inside the visible region (pop-in); adapting the generic bands makes the bee wake `32` px beyond the *displayed* edge but starts its walk `(W-256)` px earlier in world terms. That is a consequence of the generic relationship, not something the ROM prescribes. |

## 7. Understood object types (audit target 5)

`WORLD` / `CAMERA` / `EDGE` / `LIFECYCLE` / `PLAYER` per test. "Generic" = covered by the shared lifecycle adapter, nothing object-specific.

| Type | Viewport-relevant tests found | Classes | Widescreen adaptation |
|---|---|---|---|
| `$09` rings | generic lifecycle; bespoke player proximity | D, G | generic only |
| `$10` monitors | generic lifecycle; shared overlap `$6328` | D, G | generic only |
| `$18` goal sign | state 1 waits for bit 6 clear; left lock `$0353` each gated update; pan target `(signX-$80, signY-$99)`; contact box is world | D, B, C, A | **yes**: pan target = CENTRE of the displayed width (then -1) |
| `$19` child | `X = cam+$104 -> cam+$85`, `Y = camY+$50` | C, E | **yes**: `RIGHT + 4` / `CENTER + 5` (screen-anchored banner) |
| player state `$20` | freeze `d > $F8`; flag `d > $120` | C, B | **yes**: `RIGHT - 7`, `RIGHT + 33` (flag part adopted by the POC) |
| `$21` | generic lifecycle; world patrol | D, A | generic only |
| `$26` springs | generic lifecycle; `|dx| < 12` proximity | D, G | generic only |
| `$27` | generic ring/wake; `<64` trigger, `>=384` removal | D, G | generic only (section 6) |
| `$28` platforms | generic lifecycle; persistence radius 640 x 672 | D, G | generic only |
| `$50` THZ boss | trigger `(160,256)` from player; pan puts the boss on the **RIGHT edge**; patrol/entry on screen X `$38 / $C8 / $80..$DF` with the camera locked (1679); locks `$0353/$0356` | G, C, B | **yes, later**: arena camera lock and "enters at RIGHT" must be expressed once |

Types `$09 $10 $21 $26 $28` contain **no** camera, screen-X or edge compare of their own (byte scan of `$D174/$D176/+$1A/+$1C`/vector calls).

## 8. Boss / future-zone scan (audit target 6)

Not researched; instruction-level inventory only (`future_risk_scan` in the JSON; 21 literal sites byte-checked). Owner types are the nearest
preceding state-table pointer in the bank, a navigation aid only. Zone/act placement of bosses (DECODED): zone 0 act 3 `$50`, zone 1 `$51`,
zone 2 `$54`, zone 3 `$56`, zone 4 `$59`, zone 5 `$5E` (+ `$60`).

| Category | Seen | Likely meaning (**not** established) |
|---|---|---|
| Boss patrol / stop on screen X | `$9878 CP $38`, `$9884 CP $C8`, `$9A0F` `$80..$DF` (`$50`, documented); `$A385 CP $D0`, `$A447 CP $D4` (`$54`); `$AA70 CP $D0 / $30` (`$59`); `$B07A CP $30`, `$B0F7 CP $C0` (`$5E`); `$B4AC CP $F9 / 7` (`$5F`) | arena turn/stop points on a 256-px screen; 8-bit compares |
| Projectile/child despawn | `$A771 CP $B0`, `$A778 screen Y CP $78` (`$57`) | removal by screen position |
| Spawn relative to camera | `cam - $20` (`$B696`), `cam` or `cam + $100` (`$B6E1`), `cam + $20/$E0`, Y = camY, Y speed `+$600` (`$B845`), `cam + $B0 + ..` (`$BAB8`), table offsets from `cam` / `camY` (`$ADD6`) | objects created at the screen edges / top |
| Arena camera pan | `$9808` table: boss anchor screen X **256 / 192 / 224 / 208 / 128 / 128** (zones 0..5), Y 160/160/160/32/160/160; zone 0 exercised | boss enters at a fixed screen position |
| Camera vector calls | `$0353` x2, `$0356` x1, `$0359` x3, `$035C` x5, `$0407` x1, `$042B` x1 across banks `$0C/$1E` | arena locks and releases |
| Vertical | `$3C09` player screen Y >= `$D8`; `$9178` object Y vs `camY + $C0`; `$9583` `$D27E := camY` | bottom-edge death / arena bottom lock |
| Unknown | type `$1C` (bank `$0C`, `$AD95`): screen X `< $30` rewrites world X `$C0..$DF`, Y `$20..$9F` | frame of the writes UNRESOLVED |

Risk categories for widescreen: (1) 8-bit screen-X compares assume `0..255`; (2) "spawn at RIGHT/LEFT" and the pan table's
"boss at RIGHT" need `RIGHT = displayed width`; (3) arena locks make the displayed window the arena; (4) thresholds compared while the camera
is locked are world-fixed; (5) player-relative constants are unaffected.

## 9. Proposed small vocabulary (audit target 8)

Only relationships with recovered evidence; each is written in the original units.

| Primitive | Meaning | Recovered users |
|---|---|---|
| `WORLD(x)` | canonical placement, terrain, level limits (`right = width - view`) | all placements, sign contact box, hop |
| `EDGE(LEFT, n)` / `EDGE(RIGHT, n)` | `cam + n` / `cam + view + n` (original `view = 256`) | act-clear `RIGHT + 33`; camera freeze `RIGHT - 7`; player clamp `LEFT + 16`, `RIGHT - 9`; child `$19` `RIGHT + 4`; lifecycle ring edges `+-32 / +-96`; boss anchor `RIGHT + 0` (zone 0) |
| `CENTER(n)` | `cam + view/2 + n` | sign pan (`CENTER + 0`; effective -1 from the exclusive limit); child `$19` stop `CENTER + 5`; boss pan rows 4,5 (`CENTER + 0`) |
| `PLAYER_DIST(n)` | `|x - playerX|` (or Y) compared with `n` | `$27` 64 / 384; `$28` 640 / 672; `$50` 160 / 256; `$26` 12 |
| `LOCKED_CAMERA(c)` | while the camera is frozen/locked at `c`, a screen-X compare is the world X `c + k` | boss patrol `$38 / $C8 / $80..$DF`, THZ3 arena at 1679 |

`WINDOW_BANDS` (create/sleep/delete) is not a separate primitive: it is the set of `EDGE` offsets `{0, 32, 96}` on both sides plus the
vertical equivalents. Camera-motion constants (lead 104/136, dead zone 8, step 7, pan 1 px/update) are camera tuning (class B), not viewport
relations, and carry no width dependency. Two structural facts are not relationships but limits: the 8-bit `(d+128)/2` window (cannot exceed 512 px total)
and the 8-bit low-byte compares in follow/clamp/boss code.

## 10. Master constants table (audit deliverable)

Generated from `data/rom-cache/viewport-semantics.json` (`python tools/viewport_semantics.py --markdown`). Class letters as in section 0;
"evidence" and ROM addresses are in the JSON.

| system | constant | ROM address | raw meaning | coordinate frame | 256px relationship | widescreen implication | class | confidence |
|---|---|---|---|---|---|---|---|---|
| view | scroll window width 256 | VDP init $1D2D (R0..R6) | name table 32 columns; the camera is the world X of screen column 0 | screen | defines RIGHT = cam + 256 | every RIGHT-relative rule below is relative to the displayed width, not to 256 | E | high |
| view | R0 = $26 (bit 5) | ROM $1D2D | left 8 px column masked by the VDP | screen | visible x = 8..255 | presentation only; no gameplay constant reads it | E | medium |
| camera | camera X $D174 / Y $D176 | $4D3E, commit $0570 | R8 = -(cam+1), R9 = (camY+17) mod 224; $D174 := $D284 at vblank | world | left edge = cam | the left edge is the origin of every screen-relative value; a wide view extends RIGHT only | B | high |
| camera | follow lead 104 / 136 (pan mode 120) | $58E1..$58F3, init $5074 | player screen X target: $68 facing right, $88 facing left, $78 while panning; slews 1 px/update | screen (left origin) | 104 = centre-24, 136 = centre+8 | tuning of where the player sits; relation to the width is not proven (not forced by any other constant) | B | high |
| camera | dead zone +-8, max step 7 | $590D/$5912, $5861..$5867, $587F..$5885 | no scroll while player screen X in [lead-8, lead+8]; step capped at +7/-7 px per update | screen offset / speed | none | motion constants, independent of width | B | high |
| camera | pan speed 1 px/update per axis | $5964 INC DE, $597C DEC DE, $599F, $59A9 | pan toward ($D2DA,$D2DC); X and Y simultaneous | world | none | POC provisional 4 px/update and absent Y pan are adapters, not ROM | B | high |
| camera | pan sets limits | $596D..$597A, $5985..$598F | moving right: $D282 := target; moving left: $D280 := target (not zone index 6) | world | none | pan target also becomes the lock | B | high |
| camera | limits left/top/right/bottom | act header +12/+14/+16/+18; table $5082 | THZ: left 0, right = width-256 (exclusive), top 8, bottom = height-240 | world | right = world width - 256 | right limit encodes the original window; a wider view needs worldWidth - viewWidth | A | high |
| camera | right limit exclusive, left inclusive | $4CC5 (JR c), $4CE2 (JR nc) | camera in [left, right-1]; overshooting steps are dropped | world | none | camera settles at limit-1 (signX-129 in the sign pan) | B | high |
| camera | left lock / right lock | vectors $0353/$0356 -> $59E3/$59F3 | $D280 := max($D280,cam); $D282 := min($D282,cam) | world | arena width = visible width | a right lock at the camera makes the right screen edge the arena wall | B | high |
| player | left clamp 16 | $4153 (LD BC,$10), $4156 (CP $10); copy at $428C/$428F | playerX < cam+16 -> X = cam+16 (minus this update's speed), X speed := 0 | camera-relative | LEFT + 16 (= 8 masked + extent 8, interpretation) | stays LEFT + 16 | C | high |
| player | right clamp 247 | $415B (LD BC,$F7), $415E (CP $F8); copy at $4294/$4297 | low byte of (playerX-cam) >= $F8 -> X = cam+$F7 | camera-relative (8-bit) | RIGHT - 9 (= 255 - extent 8, interpretation) | must follow the displayed right edge or it is an invisible wall; low-byte compare breaks for d >= 256 | C | high |
| player | state gate $29 | $4144 (CP $29) | $4141 clamps only states < $29; state $20 (act-clear run) uses its own handler and is not clamped | state | none | — | F | high |
| player | pit death screen Y >= $D8 | $3C09 (CP $D8) at $3C06 | player screen Y >= 216 sets $D293 bit 2 | screen Y | vertical, not width | unaffected by horizontal widening | C | medium |
| act-clear | camera freeze d > $F8 | $83C2 (LD DE,$00F8) .. $83CB (CALL $0407), bank $0C | playerX - cam >= 249: $D15E bit 7 cleared, $D280 := cam | camera-relative 16-bit | RIGHT - 7 | freeze the camera when the player passes RIGHT - 7 | C | high |
| act-clear | clear threshold d >= $121 | $83CF (LD HL,$0120) .. $83E7 (SET 5), bank $0C | (playerX - cam) as unsigned 16-bit > $120 sets $D293 bit 5 (act idx < 2) or bit 4 | camera-relative 16-bit | RIGHT + 33 (exact; = 289) | player anchor 33 px past the right edge; camera is frozen so it is also a fixed world X once the pan ended | C | high |
| act-clear | sign pan target (signX-$80, signY-$99) | $AA22..$AA47 (bank $0C), vector $0359 | camera pans until the sign sits at screen X 128 / Y 153 | screen centre X, screen Y 153 | CENTRE (128); effective camera = target-1 because the right limit is exclusive | centre the sign in the displayed width: cam = signX - view/2 (-1) | C | high |
| act-clear | child $19 X = cam+$104 -> cam+$85, Y = camY+$50 | $AA87.., $AAE4.. (bank $0C) | spawns at RIGHT + 4, slides left 8 px/update to CENTRE + 5 | screen | RIGHT + 4 / CENTRE + 5 | screen-anchored HUD-like banner: express as RIGHT and CENTRE offsets | E | high |
| lifecycle | active band [-32, 288) | $61E1, map ROM $70146 (bank 1C $8146) | cells 0/1: bit 6 clear (updates run, SAT eligible) | camera-relative | LEFT - 32 .. RIGHT + 32 (map cell 0 = exactly [0,256)) | wake boundary is RIGHT + 32 of the displayed width | D | high |
| lifecycle | asleep ring [-96,-32) and [288,352) | $61E1 | cell 2: alive, bit 6 set, no updates | camera-relative | RIGHT + 32 .. RIGHT + 96 | create/sleep ring follows the displayed edges | D | high |
| lifecycle | deletion beyond -96 / +352 (window [-128,384)) | $61E1: $61EB/$6209 (LD BC,$0080), $61F9 SRL, $624C | cell 3 or outside the 512-px window: type $FE (tracked) / $FF unless +$04 bit 1 | camera-relative | LEFT - 96 / RIGHT + 96 | window is 2 x 256 wide because an 8-bit byte holds (d+128)/2: structural limit | D | high |
| lifecycle | vertical bands | $61E1 | same bands on camera Y: cell 0 = [0,256) although the screen is 192 lines | camera-relative Y | vertical window 256 tall | vertical unchanged by horizontal widening | D | high |
| lifecycle | creation: cell 2 only (cells 0/1 only at initial fill) | $8021/$802A (offset $FF80), $8099 (CP 2), $809D (CP 3), $80A2 (LD A,($D440)) | steady scrolling creates objects in the outer ring RIGHT+32..+96 / LEFT-96..-32 | camera-relative | RIGHT + 32 .. RIGHT + 96 | creation ring must sit outside the displayed width or objects pop in | D | high |
| lifecycle | scan period 4 updates | $16D9 (CP 4) | placement scan every 4th object update | time | 28 px max camera travel per scan < 64 px ring | ring width must exceed 4 x max camera speed | B | high |
| lifecycle | spawn/despawn tested on the anchor only | $61EE..$6217 | single point (anchor X,Y), not sprite extents | world anchor | none | sprite size is not part of the window | D | high |
| type $27 | proximity \|dx\| < 64 | $89BF (LD BC,$0040), call $89C2 -> $0383 | state 1 -> 2 when the post-move anchor is within 63 px of the player | player-relative world distance | none | unchanged by the view | G | high |
| type $27 | removal \|dx\| >= 384 (state 3) | $8A29 (LD BC,$0180), call $8A2C -> $0383 | type $FE when 384 px or more from the player | player-relative world distance | 384 is NOT derived from the view: it is player-relative; it equals the window's right extent only numerically | keep as player distance; it exceeds any visible offset from the player (<= 255 left of the camera origin) | G | high |
| type $28 | persistence radius 640 x 672 | $8908 (BC=$0280/$02A0) | with keep-alive bit 1: removed when \|dx\| >= 640 or \|dy\| >= 672 from the player | player-relative world distance | 2.5 x 256 numerically only | player distance, unaffected | G | high |
| type $26 / $09 / $10 / $21 | contact / proximity | per object docs | bespoke player proximity or shared overlap $6328 | player-relative | none | none | G | high |
| type $50 | trigger \|dx\|<160, \|dy\|<256 | $9771..$9799, table $97A1 (bank $1E) | boss starts when the player is within 160 px horizontally | player-relative world distance | 160 = 128 + 32 numerically | player distance | G | high |
| type $50 | pan target boss + (-256, -160) | $9808 table row 0 | boss anchor sits at screen X 256 (= RIGHT edge) when the arena camera arrives | anchor-relative | RIGHT (zone 0). Rows 1..5: 192, 224, 208, 128, 128 (users untraced) | a boss that 'enters at the right edge' needs RIGHT = displayed width, but its patrol below is fixed on the locked camera | C | high |
| type $50 | patrol turn at screen X $38 / $C8; patrol entry $80..$DF | $9878, $9884, $9A0F | low byte of (anchor - camera) with the camera locked at 1679 | camera-relative, camera locked | left-origin; equals a fixed world interval while the camera is locked | arena positions are world-fixed; keep the locked camera's left edge or convert via the lock value | B | high |
| type $50 | arena locks | $8199 call $0353, $81D3 call $035C, $D282 saved/restored | left limit raised to the camera, right limit lowered to the camera | camera lock | arena = displayed window | locked arena width follows the displayed width | B | high |
| generic | screen X low-byte compares | see future sites | 8-bit compares on (anchor - camera) | camera-relative 8-bit | assume 0..255 | 8-bit wrap hazard; use full-width integer screen X | C | medium |

## 11. Tests (audit target: "controlled tests")

`python -m unittest tests.test_viewport_semantics -v` (36 tests, ROM-backed sweeps need `SONIC_CHAOS_ROM` or the ROM next to the repo).

| Fixture (original routine) | Cases in the cache | What is swept |
|---|---:|---|
| lifetime `$61E1` | 72,072 | 11 cameras x 2 camera Y x dx -140..400 x 14 dy x flags/token; edge samples at three cameras |
| placement scan `$8000` | 2,048 | 4 acts x 64 cameras x 4 camera Y x initial/steady fill; capacity 11; plus the three THZ1 `$27` records over 560 cameras each |
| follow `$5832` | 2,048 | 4 cameras x 2 facings x 256 offsets; lead slew; pan-mode lead |
| pan `$5956` | 900 | 12 cameras x 3 camera Y x 25 target deltas; limits; zone 6 |
| limits `$4CB0` | 114 | six limit pairs x 19 steps (inclusive/exclusive edges) |
| player clamp `$4281`, `$4141` | 11,264 | 22 cameras x 256 offsets x 2 entries; velocity compensation; wrap; state gate |
| state `$20` `$83A6` | 528 | 22 cameras x 3 act indices x 8 offsets around `$F8` / `$120` |
| type `$19` child | 12 | 4 cameras x 3 camera Y |
| player-relative helpers `$61A5/$61B1`, type `$28` `$8908` | 1,980 + 36 | 5 radii x 22 cameras x 9 deltas x 2 axes; platform radii |
| emulated original frames | 3 act-clear runs (THZ1 x2, THZ2), 3 bee scrolls, VDP registers | camera/pan/freeze/flag timeline; creation/wake `d`; R0/R8/R9 |

The 36 tests re-run the original routines over **11 camera positions that are not in the cache sweep** (3, 99, 129, 300, 777, 1500, 2600,
3333, 4000, 6001, 12345), so a rule that fits only the generated cameras fails. Pure-model tests need no ROM and lock the closed forms.

## 12. Unresolved

* Whether the follow leads 104/136 and the clamp literals `$10/$F7` were derived from the window width / sprite extents (numbers only).
* Users of the boss tables rows 1..5 (`$97A1`, `$9808`) and the mechanics of every site in section 8; no later boss was traced.
* Type `$1C` coordinate frame; zones 7/8 (special stages, right limits 7936/16128) camera behavior.
* Vertical constants (`bottom = height - 240`, 256-px vertical bands, pit death screen Y `$D8`) versus 192/224/240-line modes.
* The hardware effect of R0 bit 5 (left 8-px mask) is by VDP documentation, not measured on pixels.
* The second camera-release step in the sign chain: engine state is cleared by `$4FCE` in the results sequence; not traced further.
* A full emulated bee approach (trigger, hover, removal) with a real moving player was not run; the lifecycle and trigger relationships are proven separately.

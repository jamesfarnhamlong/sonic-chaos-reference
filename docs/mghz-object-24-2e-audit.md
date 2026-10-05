# MGHZ objects `$24` and `$2E` audit (M3 Research)

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`
(verified; never committed). `SonicChaos_POC` was not touched. Base: Research `main` `4149f84`, branch `research/mghz-24-2e`.
Machine-readable facts: `data/rom-cache/mghz/object-24-2e.json`. Tool: `tools/mghz_object_24_2e.py`.
Tests: `tests/test_mghz_object_24_2e.py`. Numeric type IDs are authoritative; **no descriptive name is adopted** (community labels remain leads).

Evidence classes: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY** (z80dis of every callback and every shared helper they reach),
**CONTROLLED ROUTINE RESULT** (the original Z80 creator `$80EB`, animation engine `$64FA`, callbacks and shared helpers executed on
`tools/oracle.py` with the decoded MGHZ layouts), **EMULATED ORIGINAL FRAME** (whole game in `tools/sms_frame_harness.py`, booted into
MGHZ1/MGHZ2, real placement scan, real player), **MODEL** (independent translations checked against those), **UNRESOLVED**.

## 1. Answer in brief

| | `$24` | `$2E` |
|---|---|---|
| Behaviour (not a name) | placement-backed hazard: idles, **shakes** when Sonic is within 48 px horizontally and slower than `$100`, then **drifts ±0.5 px/update outward while accelerating downwards** until the 32×32 map cell under it is solid/one-way, where it **converts to the shared defeat effect `$0F` (+10 score)** and is detached from its placement | **keep-alive strip emitter** (parent, parameter 0) + three short-lived **particle children** (parameters 1–3): while Sonic's anchor is within ±2 px of the emitter's Y and X is in `(originX, originX + aux1·16]`, it spawns a 3-particle burst at Sonic's X every 5 updates |
| Placements | 12 (MGHZ1 8, MGHZ2 4), six pairs 16 px apart, parameter 1 (falls left) then 0 (falls right); Y 48 or 112; none in any other zone | 2 (one per act: MGHZ1 (1352,780) `aux1 $13`; MGHZ2 (232,908) `aux1 $1B`); children are dynamic (parameters 1/2/3); none in any other zone |
| States | 4 (`$B44D` table `$0C:$B445`) | 4 (table `$1E:$8A45`, **shared by unused alias type `$2D`**) |
| Contact | shared wrapper `$0434`→`$6328`, extents 4×11, **hurts on any overlap, any posture**; no rebound, no cooldown, cannot be defeated by Sonic | **none** (frame extents exist but nothing reads them) |
| Terrain | defeat probe: header bit 6/7 of the 32×32 cell at `(X, Y+18)` | none |
| Lifecycle | generic placement lifecycle (removable in every state; asleep ⇒ frozen); a converted piece never respawns this act load | parent: **keep-alive** after its init callback; children: self-removing after 14 passes |
| New art approval needed? | **No** – every drawn frame hash-equals the approved board | **No** |

New findings that matter for the POC (details below): the shake is a **17-update** fixed script; all 12 mapped pieces fall **exactly 96 px**
and convert after **56 falling updates**; the `$2E` emitter **does not exist** if Sonic enters the oil strip from the right on a fresh load; the
`$2E` children go **opposite to the player's object-flag bit 4** and a child in a slot below its parent runs one update late; the dynamic-object pool is
only **11 slots (7..17)**.

## 2. Placements, parameters, flags

All 18 mapped object lists (6 zones × 3 acts, `L.object_list_pointer`) were scanned: **14 records, all MGHZ** (`$24` ×12, `$2E` ×2). No other zone places either
type; no code creates them except the placement creator `$1C:$80EB` and the `$2E` state-2 spawn script. Type `$2D` shares `$2E`'s state table
(type-table entries `$6612` and `$6614` both point to `$1E:$8A45`) but is never placed, spawned or loaded by an immediate-type pattern: an unused alias, not a dependency.

Creator rule (`asm/recovered/object_placement_create.asm`, BYTE-VERIFIED + controlled): record `type, Xlo, Xhi, Ylo, Yhi, flags, parameter, aux0, aux1`; stored X/Y carry a +256 bias;
the slot gets `+$11/+$14` = position, `+$3A/+$3C` = origin copy, `+$04` = **flags | `$40`** (created asleep), `+$3F` = parameter, `+$08/+$09` = aux0/aux1, `+$3E` = **occupancy token = list index (1-based)** and
`D400[index-1] := type`.

| Type | act | idx | world X,Y | flags | param | aux0 / aux1 | family |
|---|---|---:|---|---|---|---|---|
| `$24` | MGHZ1 | 26,27 | (456,112) (472,112) | `$00` | 1, 0 | `$A0`/`$A0` | left-falling, right-falling pair |
| `$24` | MGHZ1 | 28,29 | (2120,112) (2136,112) | `$00` | 1, 0 | `$A0`/`$A0` | pair |
| `$24` | MGHZ1 | 30,31 | (2664,112) (2680,112) | `$00` | 1, 0 | `$A0`/`$A0` | pair |
| `$24` | MGHZ1 | 32,33 | (3080,48) (3096,48) | `$00` | 1, 0 | `$A0`/`$A0` | pair |
| `$24` | MGHZ2 | 38,39 | (808,48) (824,48) | `$00` | 1, 0 | `$A0`/`$A0` | pair |
| `$24` | MGHZ2 | 40,41 | (2888,112) (2904,112) | `$00` | 1, 0 | `$A0`/`$A0` | pair |
| `$2E` | MGHZ1 | 34 | (1352,780) | `$00` | 0 | `$72` / `$13` | strip 304 px: X ∈ (1352, 1656] |
| `$2E` | MGHZ2 | 42 | (232,908) | `$00` | 0 | `$72` / `$1B` | strip 432 px: X ∈ (232, 664] |

Parameter/flag families: `$24` flags are `$00` in all 12 (no mirror bit, no keep-alive bit); parameter 0 ⇒ fall vx `+$80`, **any other value** ⇒ `−$80` (only 0/1 mapped). `$2E` flags `$00`;
`aux1` is **not an art base here**: it is the strip length in 16-px units (`$8A8A` computes `originX + aux1·16`), although the creator copies it to `+$09` like every type.
Placement tracking: both types are placement-backed (`+$3E ≠ 0`).

## 3. Object `$24`

### 3.1 State table (BYTE-VERIFIED: type-table entry file `$06600` → state table `$0C:$B445`)

| State | Script | Frames × duration | Callback | Successor |
|---|---|---|---|---|
| 0 `$B44D` | one record | frame 0, 224 | `$B490`: `+$02 := 1`, `+$1F := 0` (**runs even while asleep**) | state 1 (next update) |
| 1 `$B453` | 3 records | frames 1,2,3 × 8 (24-update loop) | `$B49A`: `+$04` bit 6 ⇒ return; contact `$0434`; `|objX−playerX| < $30` (strict, `$0383`) and `|player vx| < $100` (strict) ⇒ `+$02 := 2` | state 2 |
| 2 `$B461` | loop ×4 of {vx `+$0200`, frame 1 × 2; vx `−$0200`, frame 2 × 2}; then frame 3 × 4 | `$B4C5` (bit 6 ⇒ return; contact; move `$0338`) / last record `$B4D1` | `$B4D1`: vx := `+$80` if `+$3F == 0` else `−$80`, vy := 0, `+$02 := 3` | state 3 |
| 3 `$B482` | frames 1,2,3 × 4 (12-update loop) | `$B4F0`: bit 6 ⇒ return; contact; move; gravity `+$10` (`$0431`); terrain probe `$037A`; if solid ⇒ `+$3F := $80`, **`JP $033E`** | `$0F` (converted) |

Every callback (except `$B490` and `$B4D1`) returns immediately while `+$04` bit 6 (asleep) is set: **no trigger, no contact and no motion while asleep**, but the animation engine still cycles frames.
No script spawns anything, plays a sound or sets a mirror bit.

### 3.2 Timeline (CONTROLLED; whole game agrees)

`T` = the update whose state-1 callback sets request 2. Contact is evaluated at `T` (before the trigger test), `T+1..T+16` (shake), and every update from `T+18` (before the move); **not** at `T+17` and not in the state-0 update.

| Update | State / frame | Position (parameter 1 at X=456, Y=112) |
|---|---|---|
| `T` | 1 → requests 2 | (456,112) |
| `T+1,T+2` | 2, frame 1 | x 458, 460 (vx `+$200` ⇒ +2 px/update) |
| `T+3,T+4` | 2, frame 2 | x 458, 456 (vx `−$200`) |
| `T+5..T+16` | the same 4-update pattern ×3 | shake offsets `+2,+4,+2,0` repeating; ends back on the origin |
| `T+17` | 2, frame 3, `$B4D1` | no move; vx `−$80` (param ≠ 0) or `+$80` (param 0); vy 0; requests 3 |
| `T+18…` | 3, frames 1,2,3 × 4 | move first (`x ± 0.5`, `y += vy`), then vy += `$10`; e.g. x 455.5, 455, 454.5…; y 112, 112.06, 112.19, 112.38… |
| `T+73` | converted | after the **56th falling update** (the conversion happens in the same update, after move + gravity) |

Whole game (pair at 456/472 with Sonic parked at x=412): created frame 2, awake frame 4, trigger frame 5, state 2 loaded frame 6, state 3 loaded frame 23, converted frame 78 (= trigger + 73), slot cleared frame 119.
Positions are 24-bit (`16-bit integer + fraction byte`), integrated by `$60FB` with sign-extension; the cache stores the full row table and an independent translation (`model_fall`) reproduces all 12 landings.

### 3.3 Trigger (CONTROLLED sweep, 1,432 cases)

Fires iff `+$04` bit 6 clear, **`|dx| ≤ 47`** and **`|player vx| ≤ 255`** (16-bit absolute value, so `−$8000` does not fire). Player Y, state and posture are not read (swept dy −120…+240). Boundary cases are in the cache (`dx = ±47` fires, `±48` does not; `vx = ±255` fires, `±256` does not).
Because walking speed exceeds `$100` after a few frames, a run-through does not trigger (whole game: running right from x=300 never triggers; starting inside the window and holding RIGHT triggers at frame 5; standing still triggers).
The two pieces of a pair test their own `|dx| < 48` independently (Sonic at 412 triggers only the left piece (456); at 515 only the right piece (472); at 464 both).

### 3.4 Terrain, landing and defeat

`$037A` (`$614E`) calls the object sampler `$7725` at `(X + 0, Y + 18)`: the 32×32 map cell's **header flag byte** (not the height profile); bit 6 (one-way) or bit 7 (solid) ⇒ "hit"; outside the map reads as air. There is **no wall, ceiling, oil `$1B`, `$19` strip or platform interaction**. All 12 mapped pieces land on block `$01` (flags `$81`):

| Records | Start Y | Landing probe cell row | Conversion position | Falling updates |
|---|---|---|---|---|
| Y=112 pieces (8) | 112 | row 7 (Y 224) | param 1: X−28, Y 208; param 0: X+28, Y 208 | 56 |
| Y=48 pieces (4) | 48 | row 5 (Y 160) | X∓28, Y 144 | 56 |

Defeat path (`$033E`→`$5F54`, BYTE-VERIFIED + whole game): adds the score entry at `$27EB` (`10 00 00` BCD, **+10**, skipped when `$D292 ≠ 0`), sets the slot type to **`$0F`** and clears `+1,+2,+4,+7,+14,+15,+$3E,+$3F`; it keeps the position, `+$08/+$09` and the renderer's saved frame pointer, so the conversion update still draws the last `$24` frame.
`$0F`'s own init then sets art base 0 / `+$04 = 1`; its frames 7–9 use tiles `$24..$2C`, identical in the MGHZ1 and THZ1 act VRAM (hash-equal) – shared explosion art. Its request-sound vector `$03EF` writes `$C4` to `$DE04`. Whole-game lifetime from conversion to slot clear: **41 frames** (runs: frame 2 ×1 (stale), frame 0 ×2, then 7/8/9 cycles).
Sonic cannot defeat a `$24`: none of its callbacks calls an attack helper (`$033B`/`$0323`/`$5F3D`).

### 3.5 Player contact (CONTROLLED, 24,990 cases + whole game)

Shared wrapper `$0434` (`$630B`) = `$6328` overlap then `D3B0 := $FF` if any of `+$21 & $0F`. Extents come from the current frame header (frames 1–3: **4×11**; frame 0: 0×0 – never reached in a contact state).

| Variant (player extents, `$D503`, `$D532`) | `D3B0` set when | Result in the real game |
|---|---|---|
| ordinary 8×24 | `|dx| ≤ 12` and `−11 ≤ dy ≤ 24` (closed; dx = playerX−objX, dy = playerY−objY, anchors bottom-centre) | `$48BC` hurt (`$48F7`): rings ⇒ scatter + state `$1E`; 0 rings ⇒ death `$1F` |
| state `$0F` 9×24 | `|dx| ≤ 13` | same |
| attacking (`$D503` bit 1: rolling state 9, jump `$0A`) | same box | **still hurt** (the request outranks bit 1) |
| `$D532 == 6` (invincibility) | same box | request cleared every frame, no hurt, no defeat |
| blinking (`$D503` bit 7) | same box | request held back (`D3B0` stays `$FF`), no hurt, rings kept |
| hurt state (`$D503` bit 6) | **never** (`$6328` returns early) | no contact |

`D520` is also written (`slot id`, object `+3` bit 7 is clear) with the minimum-penetration bits in `D521`, but `$48BC` takes the `D3B0` path first, so **there is no rebound for any side** (top/side/below are all damage). There is no cooldown or recontact rule beyond the player's own blink; the object re-asserts the request every update it overlaps.
Whole-game outcomes (fork at fall update ~20; exact observed `(dx,dy)` per frame in the cache): ordinary 10 rings ⇒ hurt at the next frame, rings 0, state `$1E`; 0 rings ⇒ state `$1F`; rolling and jumping attack ⇒ hurt; invincible ⇒ no hurt; blinking ⇒ none; hurt state ⇒ no contact. Footwear states route through the same shared helpers and `$48BC`; **no footwear-specific handling exists in `$24`**.

### 3.6 Lifecycle (EMULATED ORIGINAL FRAME)

Generic only (`$61E1`, current state ≠ 0): initial fill creates the piece when the anchor column `objX − cameraX` lies in **[−96, 348]**; it is awake in **[−32, 284]**; scrolling right (frame granularity, camera moves several pixels per frame) it was created at +347, woke at +283, slept at −33 and was removed at −101. Removal marks `$FE` (token ≠ 0) → `$626D` makes `$FF` → `$5EF8` releases `D400[token−1]` and zeroes the slot.
Consequences (all observed): leaving before the trigger removes and later **recreates the piece at its origin in state 1**; leaving mid-fall does the same (no score); a piece left behind in the sleep band **hangs frozen in mid-air** (flags `$40`, animation still cycling) until it is removed or Sonic returns; after a **landing** the piece is detached (`D400` keeps `$24`), so backtracking never recreates it while its partner is recreated. Nothing becomes keep-alive.

## 4. Object `$2E`

### 4.1 State table (BYTE-VERIFIED `$1E:$8A45`)

| State | Script | Callback | Successor |
|---|---|---|---|
| 0 `$8A4D` | frame 0 × 224 | `$8A8A`: `+$3F == 0` (parent): `+$34/35 := aux1·16 + word(+$3A)`, **`SET 1,(IX+4)` (keep-alive)**, `INC +$02` ⇒ state 1. `+$3F ≠ 0` (child): vx := `$FF60 − 16n` (n = parameter) if **player object `$D504` bit 4 clear**, else `$00A0 + 16n`; vy := `−$0100`; `+$02 := 3` | 1 / 3 |
| 1 `$8A53` | frame 0 × 224 | `$8AE5`: `|objY − playerY| < 3` (strict, `$0386`) and `originX < playerX` and `playerX ≤ originX + aux1·16` (unsigned 16-bit) ⇒ `+$02 := 2`, **objX := playerX** | 2 |
| 2 `$8A59` | frame 4 × 4 (callback `$032F` = RET) then 3 spawn commands (type `$2E`, offsets (4,0),(0,−2),(−4,−4), parameters 1,2,3) and `request_state 1` | – | 1 (re-evaluated in the same update) |
| 3 `$8A7A` | frames 1,2,3 × 4, then frame 3 × 224 with `$034A` | `$8B10`: move `$0338`, gravity `$10` | type `$FE` |

The parent never tests `+$04` bit 6 (it runs asleep or awake). No sound, no terrain probe, no contact helper (static scan: the callbacks call only `$0386`, `$0338`, `$0431`).

### 4.2 Strip trigger (CONTROLLED, 834 cases over both acts)

Fires for playerX ∈ **(originX, originX + aux1·16]** (MGHZ1 1353…1656 = 304 values; MGHZ2 233…664 = 432) and dy ∈ **−2…+2**. It reads nothing else (vx, airborne, attacking, blinking, hurt bit, `$D532`, facing all fire at mid-strip). On firing the parent's **X becomes the player's X** (Y unchanged); its own origin (`+$3A`) is unchanged.

### 4.3 Burst and children (CONTROLLED + model, whole game)

Timeline relative to the trigger update `t`: states `t+1..t+4` = state 2, frame 4 (4 updates); on the fifth the engine runs the spawn commands, requests state 1 and the callback re-evaluates immediately, so with Sonic parked in the band a burst repeats **every 5 updates** (cadence proven 11 bursts / 60 passes).
Each child: `rel 0` init update (frame 0, **no move**), `rel 1..12` moving updates (frames 1,2,3 × 4), `rel 13` frame 3 with `$034A` (type `$FE`), `rel 14` `$FF`, `rel 15` slot zero. Position at spawn = parent X + dx, parent Y + dy; then `x += vx`, `y += vy`, `vy += $10` per moving update (24-bit):

| Child | spawn offset | vx (facing bit 4 clear) | vx (bit 4 set) | vy |
|---|---|---|---|---|
| 1 | (+4, 0) | −176 (`$FF50`) | +176 | −256 |
| 2 | (0, −2) | −192 | +192 | −256 |
| 3 | (−4, −4) | −208 | +208 | −256 |

Example (MGHZ1, Sonic at X=1392, facing bit clear): child 1: (1396,780), then 1395/779, 1394/778, 1393/777 … 1387/772 at the end (vy −64). Whole game confirms both signs: Sonic walking right (object `$D504` bit 4 clear) ⇒ children go left; dropped into the strip holding LEFT (bit 4 set) ⇒ vx +176/+192/+208. Mirror: `+$04` bit 4 of the children is never set, so art is never flipped; only the velocity sign follows the player.
The spawn command copies the parent's `+$04` bit 4, `+$08`, `+$09` and sets origin copies; it allocates from **slots 7..17 only** (`$5EE1`, 11 slots) and silently skips when none is free (partial bursts: 0/1/2/3 free slots ⇒ children {}, {1}, {1,2}, {1,2,3}).
**Update order:** children placed in a slot below the parent's index are processed before the parent in the next scheduler pass, so their first update (init) lags one frame (observed: slot 7 with parent slot 10, and slot 8 with parent 9 in MGHZ2). Whole-game bursts also showed pool saturation: later bursts of the same walk-in create only 2 or 1 children.

### 4.4 Contact, terrain

**No contact.** Frame headers carry extents 4×16 (frames 1–3) and 8×16 (frame 4) and the engine writes them to `+$2C/+$2D`, but a ROM-wide byte scan finds 18 readers of `(IX|IY+$2C/$2D)`: 13 inside the `$6328` family, four in the fixed bank on different structures, and others in other types' code – **none inside `$8A8A..$8B1A`** – and 655 frames of Sonic overlapping `$2E` boxes at the trigger Y produced no hit of `$6328/$630B/$5FA0/$5F3D/$5F54` with a `$2E` slot and no `D3B0/D520`. The old census "0×0 extents" referred to frame 0 only. There is no terrain, wall, oil, platform or gravity-global dependence (gravity is the constant `$10`).

### 4.5 Lifecycle

Creation needs the origin to lie in `[cam−128, cam+384)` at some creation pass. After the init callback the parent has `+$04` bit 1: it is **never removed** (observed present and running 1,400 px away, flags `$42`, `D400` token kept). Entering the strip on a **fresh load from the right** therefore creates nothing (MGHZ1: Sonic at X=1646 ⇒ origin is 190 px left of the camera ⇒ no parent ⇒ no splash), while the same walk after a visit from the left splashes.
Children are untracked (`+$3E = 0`): any exit window removal would use `$FF`; normally their own `$034A` removes them.
Whole game: walking in from the left rim of MGHZ1, the first burst is at X≈1387 (Sonic falling onto the oil, anchor Y = 780 for one update); further bursts follow as the sinking anchor passes Y 778…782 (retriggers at X 1407, 1427, 1447, …); MGHZ2 shows the same chain (5 bursts before the pit bottom).

## 5. Shared engine facts learned (candidate AGENTS lines in section 9)

* Dynamic object slots 7..17 (11) only; `$5EE1` returns the first free; spawn skips silently when full.
* Removal is two passes: `$FE`→`$626D`→`$FF`→`$5EF8`.
* `$5F54` leaves the saved sprite pointer; the `$0F` replacement initialises its own art base.
* The creator copies aux1 to `+$09` for every type (not always an art base).
* SAT reaches VRAM 0–3 harness frames late in busy scenes; the renderer used either the committed or the working camera (`$D174`/`$D284`).

## 6. Lifecycle and screen-relative classification

| Constant | Class | Widescreen adapter |
|---|---|---|
| `$24` trigger `|dx| < 48`, `|vx| < $100` | `PLAYER_DIST(48)` (X only) | none |
| `$24` shake/fall/gravity/landing probe | `WORLD` | none |
| `$24` create −96…348, awake −32…284, removal ≤ −97 / ≥ 352 | `EDGE` (generic spawn window) | generic lifecycle adapter only |
| `$2E` strip X range, Y band ±2 | `WORLD` (from placement) | none |
| `$2E` parent creation window `[cam−128, cam+384)` | `EDGE` | **decision required**: a wider view makes the parent appear earlier (e.g. entering from the right); faithful SMS behaviour is "no splash if never created" |
| `$2E` parent keep-alive | `WORLD` | none |
| Child physics (vx 176/192/208, vy −256, gravity 16) | `WORLD` | none |
| 11-slot pool | engine capacity | decide whether to emulate |

No constant inside `$24`/`$2E` logic is `CENTER` or `LOCKED_CAMERA`.

### POC adapter decisions (Manager, recorded after review; **not ROM facts**)

The ROM facts above are unchanged; exact 256-px behaviour remains the baseline.

* `$24`: retain the canonical initial create/wake behaviour; use the already-accepted generic post-awake horizontal retention adapter in the POC; do **not** widen the player `|dx| < 48` trigger, the terrain probe or the contact box.
* `$2E`: do **not** widen the initial parent-creation window; preserve the canonical case where a fresh load/approach can reach the strip before the invisible parent exists (no splash); once created, preserve the canonical permanent keep-alive.

## 7. Art and presentation

Mapping: `$24` entry `$3C048`→`$3D169` (4 frames), `$2E` entry `$3C05C`→`$3D24C` (5 frames); bases `$A0` (12 tiles from `$25EE0`) / `$72` (10 tiles from `$26780`); sprite palette index 9. The previously approved Research board (`data/rom-cache/mghz/art-approval.json`) already contains frames 0–3 (`$24`) and 0–4 (`$2E`).
Runtime check (whole game): 110 frames with `$24` and 150 frames with `$2E`: the composition hash of every drawn frame **equals the approved hash** (`$24` 1/2/3: 70/61/49 of 70/61/49; `$2E` 1/2/3/4: 50/48/49/20 of the same), the live sprite palette equals the approved CRAM row in every frame, and all model SAT pieces reach the VRAM SAT (delays 0–3 frames). Orientation: `+$04` bit 4 is never set (placement flags 0; scripts never write it; spawn copies it) – runtime uses the unmirrored board image for both fall directions and both splash directions. **No new visual approval is required.** The converted `$0F` uses the shared explosion tiles `$24–$2C`, byte-identical to THZ1.

## 8. Corrections to the foundation census

1. `$24` state 3 does not "delete itself": it converts to `$0F` (+10) on a solid/one-way cell. 2. `$0431` is the gravity add, not a contact helper. 3. `$2E` "0×0 extents" was frame 0 only; frames 1–4 carry 4×16/8×16 that nothing consumes. 4. `$2E` `aux1` is the strip length. 5. The `$2E` parent is not deleted through `$034A` (only its children are); it is keep-alive.

## 9. POC implementation checklist and AGENTS candidates

See `poc_checklist` and `agents_candidate_updates` in the cache JSON (also echoed here):

**POC checklist**

1. `$24`: created asleep; update 1 requests state 1; idle frames 1,2,3 × 8; contact each update from state 1 (before movement) except `T+17`.
2. Trigger (awake, state 1): `|dx| < 48` and `|vx| < $100`.
3. Shake 16 updates (offsets `+2,+4,+2,0` ×4 via vx ±`$200`, 2-update frames 1/2), init update `T+17` sets vx `±$80`, vy 0.
4. Fall: move, `vy += $10`, probe cell `(x, y+18)` header bit 6|7 ⇒ convert (56 falling updates for all mapped pieces).
5. Convert: +10 score, `$0F` at the same x,y (+ sound `$C4` from `$0F`), detached from the placement.
6. Contact: closed boxes 4×11 vs 8×24 (9×24 in `$0F`); hurt in all postures; invincible clears; blink holds; hurt-state disables; no rebound; no cooldown.
7. Lifecycle: placement-backed generic lifecycle, frozen while asleep, recreated fresh if removed before landing, never after landing.
8. `$2E`: keep-alive emitter with strip `(originX, originX + aux1·16]`, `|dy| < 3`, copy playerX, 4 updates frame 4, burst of 3 children, immediate re-evaluation (period 5).
9. Children: init update then 12 moving updates (frames 1,2,3 × 4), vx `−(160+16n)` / `+(160+16n)` by the player's object-flag bit 4, vy −`$100`, gravity `$10`, then removal marking; never mirrored.
10. `$2E` has no contact; no terrain; 11-slot pool; parent absent if never created.
11. No new art import approval; no widescreen constant inside the objects; two adapter decisions (generic lifecycle, `$2E` parent creation window).

**AGENTS candidate updates** (root `AGENTS.md` untouched)

* MGHZ `$24` (12 records) = proximity-triggered shake-then-fall hazard, converts to `$0F` (+10) on a solid/one-way 32×32 cell at `(x, y+18)`; shared contact `$0434`, any posture hurt; audit `docs/mghz-object-24-2e-audit.md`.
* MGHZ `$2E` (1 per act) = keep-alive strip emitter, `aux1` = strip length in 16-px units, no contact; children go opposite to the player's object-flag bit 4.
* The placement creator copies `aux1` to `+$09` for every type; do not assume it is an art base.
* Dynamic objects and spawn commands use slots 7..17 only; removal is `$FE`→`$FF`→cleanup (two passes).
* Enemy conversion `$5F54` keeps the saved frame pointer for the conversion pass; `$0F` re-initialises art base 0.
* Type `$2D` is an unused alias of `$2E`'s state table.

## 10. Unresolved and limits

* No human gameplay recording: evidence is ROM code or original code in the approximate harness (PSG, exact VDP/lag pattern not modelled; frame counts can differ by one in lag frames, so durations are given in object engine passes).
* Which free slots a real scene leaves to `$2E` bursts depends on other dynamic objects; the pool rule is proven, individual scenes are sampled.
* `$0F` audio/command details beyond `$C4` and its exact later states are shared with other enemies and were not re-audited.
* Names for `$24`/`$2E` are not established.

## 11. Reproduction

```text
python tools/mghz_object_24_2e.py path/to/SonicChaos.sms            # regenerate data/rom-cache/mghz/object-24-2e.json (~20 s)
python tools/mghz_object_24_2e.py path/to/SonicChaos.sms --check    # byte-compare the cache
python -m unittest tests.test_mghz_object_24_2e                     # cache locks + ROM-backed re-execution
```

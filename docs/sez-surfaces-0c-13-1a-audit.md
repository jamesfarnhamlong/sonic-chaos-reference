# SEZ terrain mechanics: surface `$0C` / block `$AF` / dynamic `$13` (crumble ledge) and surface `$1A` / block `$A7` (booster pad)

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`
(verified, never committed). `SonicChaos_POC` and the root `AGENTS.md` were not touched. Base: Research `main` at `a200826`
(SEZ foundation + visual approval). Branch: `research/sez-surfaces`.

Machine-readable facts: `data/rom-cache/sez/surfaces-0c-1a.json` (full evidence, `tools/sez_surfaces.py`) and
`data/rom-cache/sez/surface-runtime-contracts.json` (runtime contracts + oracle vectors for the POC).
Tests: `tests/test_sez_surfaces.py`. Builds on `docs/sez-foundation-audit.md` §5 and `docs/sez-object-census.md` (which left both mechanics
"decoded, not audited"), `docs/platform-spike-collision-audit.md`, `docs/mghz-surface-1b-ceiling-spikes-audit.md` and `docs/player-animation-counter.md`.

Scope is exactly the two terrain mechanics and the dynamic type `$13` they drive. **Not** covered: `$28/$86`, `$20/$23`, `$54/$55`, monitor repair,
parked presentation defects.

Evidence classes: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY** (z80dis of every routine), **SOURCE-TRACED BEHAVIOR**, **CONTROLLED ROUTINE RESULT**
(original Z80 routines on `tools/oracle.py` / the terrain pass on a decoded act layout), **EMULATED ORIGINAL FRAME** (the whole game in
`tools/sms_frame_harness.py`, one row per player update), **MODEL** (an independent translation checked against the above), **UNRESOLVED**.
Coordinates are world pixels; the *anchor* is the player Y register (feet = anchor + 18); cells are 32 px. "Update" = one game-loop iteration.

## 1. Answers in one page

**Crumble ledge (`$AF` -> type `$13` -> `$B0`).**

* Block `$AF` (flags `$4C`: one-way, surface `$0C`) is an ordinary one-way platform (no wall, no ceiling) whose floor handler `$6B79` runs for **any**
  foot sample inside the cell (anchor X, anchor Y + 18; state `$12` +8, `$21` -14), whatever the state, floor flag, previous flags, attack posture or
  invincibility (106,704 + 3,072 controlled cases).
* The handler does nothing while Y speed is negative. Otherwise it **zeroes Y speed on every call** (also while standing) and, if the probed cell differs
  from the remembered cell `$D356`, spawns one type `$13` at the first free slot of 0..15 (silently nothing when full) and remembers the cell.
* The object's timeline is exact and identical for all 93 `$AF` cells of THZ1/2, SEZ1-3, AQZ1-2, EEZ2: with `T` = the spawn update: `T+1..T+16` rider hold
  (16 updates), **`T+17` the cell becomes `$B0`** (layout RAM + 4 x 4 name-table redraw), `T+18` sound `$A3`, four shards and the object's removal; shard `p`
  first moves at `T+19+p` (p = 3, 8, 5, 1 at cell +0, +8, +16, +24 -> `T+22, T+27, T+24, T+20`), Y speed `+2.0`, then `+2.0` per update, no cap.
* **The rider hold has no presence test.** While a live object is in its 16-update record, any player whose state is `$0E` or whose `+$03` bit 0 is clear
  gets Y := object Y - 40 (= **cell top - 16**: feet 2 px into the cell) and Y speed := 0 *every update, wherever he is*: running off the end of a ledge
  hovers for up to the rest of the hold (SEZ1 (28..29,10): 9 hover updates beyond the edge). The terrain pass leaves him at cell top - 18; the object pass
  then pushes him to cell top - 16 (the rendered Y).
* The cell is replaced unless the object is asleep or `objectX < cameraX` (strict) at the break update; then the object just disappears and the cell stays `$AF`
  **and is still remembered**, so it never crumbles again until another crumble cell is touched. Not naturally reachable at <= 7.0 px/update (camera trails about 118 px).
* Everything else follows: jumping off and re-landing on the same cell creates no second object; A -> B -> A before A breaks creates a second object for A;
  a full 16-slot pool means no object, no hold, no break; the layout RAM keeps `$B0` for the act and an act restart reloads the layout and clears `$D356`.

**Booster pad (`$A7`, surface `$1A`).**

* Block `$A7` (flags `$9A`: solid, surface `$1A`, 0..2 px bump) is dispatched **only by the terrain-ring probe `$753E`**; its floor handler is a bare `RET`.
  The probe is (anchor X, anchor Y - 8) for an even `+$07` bit 0, (anchor X, anchor Y + 2) for an odd one. If that cell is `$A7` **and the floor flag is set**:
  X speed := **+7.0**, max X speed `$D373` := **`$0700`**, `+$03` := (`+$03` | 2) & `$FE` (attack posture on, jump latch cleared), requested state **`$10`**,
  sound request `$BD`. Nothing else is written (Y speed, facing, position untouched). 65,536 controlled cases.
* The pad cell sits one cell **above** the ground row; a grounded walker (anchor = cell top + 14) is inside both parity windows, so the pad launches in **every update**
  its 32-px column contains him (5 launches at 7 px/update; sound rewritten each time).
* **Direction is intrinsically rightward**: the speed is written unconditionally; entering from the right fires once at the right edge and sends Sonic back right. The art has
  no directional glyph.
* State `$10` is the spin-dash roll state: shared callback/physics (decay 5/256 per update with no input, 4 with RIGHT, skid `$07` with LEFT, B1 jumps keeping speed and
  attack posture, `|vx| < $10` -> stand `$01` / crouch `$04`). The pad also **cancels Rocket Shoes** (state `$11` -> `$10`, selector and timer left) and, when Spring Shoes land
  in the column with an odd probe parity, converts `$12` to `$10` with the shoe's -7.5 Y speed kept.
* The art is a static pad plus tile `$158` in 8 of the 16 cells; effect 5 alternates two 32-byte images into VRAM `$2B00` every 3 effect calls (first `$8DFD`, then `$8DDD`; period 6),
  paused while the boss flag `$D44E` is set. All 9 `$A7` cells (SEZ2 x2, SEZ3 x2, AQZ x3, EEZ x2) behave identically; no routine of either mechanic reads the zone byte.

## 2. Verification summary

| Check | Result |
|---|---|
| `$6B79` + `$5EB7` vs model: Y-speed high byte 0..255 x same/different remembered cell x pool free/full/first-k occupied/patterns | 545 cases, 0 mismatches |
| Terrain pass `$690B` with one isolated `$AF` cell: state (3) x previous flags (3) x Y speed (4) x floor flag (2) x X (19) x foot row (39) x remembered cell (2) | 106,704 cases, 0 mismatches |
| Same, every `+$03` value x 12 states | 3,072 cases, 0 mismatches |
| `$715E` side pass and `$73C9` ceiling pass vs one-way / solid references | 29,600 cases (informational counts, AF == one-way reference) |
| `$A2DD` init (all parameters, positions, every X/Y low byte) | 2,048 cases, 0 mismatches |
| `$A344` rider hold: state 0..`$36` x `+$03` 0..255 | 14,080 cases, 0 mismatches |
| `$A36A` break: `+$04` 0..255 x camera offsets + 16-bit wrap | 1,801 cases, 0 mismatches |
| Shard state-3 schedule: parameters 1..255, 13+ passes each, sleep removal | 35,958 cases, 0 mismatches |
| `$61E1` lifecycle vs the decoded 32 x 32 class table | 55,155 cases, 0 mismatches |
| `$7646` booster handler: `+$22` 0..255 x `+$03` 0..255 | 65,536 cases, 0 mismatches |
| `$753E` ring probe on an isolated `$A7` cell: X (60) x Y (80) x parity x floor flag | 19,200 cases, 0 mismatches |
| `$A7` solid projection vs its profile: 32 X x 32 foot rows | 1,024 cases, 0 mismatches |
| Whole game: a drop onto **every** `$AF` cell of 8 acts | 93 cells, one coordinate-free timeline signature |
| Whole game: a walk onto **every** `$A7` cell (left and right) | 9 cells, one launch signature |
| Whole-game scenarios (walk-off, bridge, rise-through, revisit, A-B-A, removal x2, full pool, persistence, restart, hold ordering, state scans x2, speed table, input scripts, state-`$10` exit, bridge, footwear, effect 5) | see sections 3-4 |
| Controlled total | 334,723 cases, 0 mismatches |
| ROM writes / stored ROM bytes | none (region hashes only) |

Reproduce: `python tools/sez_surfaces.py ROM.sms [--check] [--static-only]` (about 60 s), `python -m unittest tests.test_sez_surfaces` (60 tests, 2,287 assertions, about 30 s).

### Harness notes (affect how the whole-game rows were produced)

* Rows are recorded **once per game-loop iteration** at every player-engine entry (`$64FA`, IX = `$D500`), not once per displayed frame: the harness can run two iterations in one frame
  (observed with the invulnerability blink), which would merge two updates into one row. Placement fixtures are written at an engine entry, so row `u = 1` is the first clean update.
* The harness snapshot restores registers, memory and the VDP but not the z80 core's **hidden decode state** (`index_rp_kind` = pending DD/FD prefix, `int_disabled`). A previous run can end
  between a prefix and its opcode; resuming the snapshot PC with a stale `IX` prefix executed the first instruction wrongly (the player appeared 3,300 px away; later rows were
  history-dependent). `tools/sez_surfaces_rig.py` executes one real NOP and restores again; `tests` lock that a run after an unrelated run equals a fresh run. Other whole-game research tools use
  `Emu.restore()` without this guard (see unresolved).
* Game-loop order (observed with PC hooks): player engine -> player callback (movement, terrain pass: floor pass incl. `$6B79`, sides, ceiling, ring probe incl. `$7646`, merge; damage gate)
  -> object scheduler `$5DD1` (`$D521 := 0`, slots 0..18 ascending) -> frame wait.

## 3. Surface `$0C` / block `$AF` / object `$13`

### 3.1 What the blocks are (DECODED DATA + BYTE-VERIFIED ASSEMBLY)

| Block | Flags | Vertical profile | Horizontal profile | Notes |
|---|---|---|---|---|
| `$AF` | `$4C` (bit 6 one-way, surface `$0C`) | 32 at every X | `$60` at every row | the only surface-`$0C` block placed in any layout |
| `$B9`, `$BA`, `$BB` | `$4C` | identical | identical | same header as `$AF`, **never placed** in any act (UNRESOLVED purpose) |
| `$B0` | `$00` | 0 | `$40` | empty air; mapping = 16 x tile 192 (blank); placed in no initial layout |

Floor dispatch table `$6973`: surface `$0C` -> `$6B79`. Side pass and ceiling pass do nothing for `$AF` (7,400 sweep cases per block: 0 pushes, 0 ceiling hits, identical to the one-way
reference `$0D`; an ordinary solid block pushes in 1,536 side cases). The horizontal profile byte `$60` is not a wall. Support is the shared one-way projection (table `support_projection_table`
in the audit): nothing about the block's collision is special.

### 3.2 Handler `$6B79` (BYTE-VERIFIED + CONTROLLED)

```text
BIT 7,(IX+$19)    ; player Y speed negative -> RET (no write at all)
Y speed := 0      ; ($D518), EVERY call, before the same-cell test
if $D354 == $D356: RET           ; remembered cell
$5EB7(B=$13, C=0, DE=$D358, HL=$D35A)   ; spawn at the probed position, first free slot of 0..15
$D356 := $D354
(IY+$31),(IY+$30) := $D354       ; IY = the new slot, or $D940 = slot 16 when the pool was full
```

`$D354` = pointer into the layout RAM (`$C001 + cy * width + cx`) of the probed cell; `$D358/$D35A` = the probed world position (anchor X, foot Y), **not** snapped.
Operand scan of the whole ROM: `$D356` has exactly two sites, both in `$6B79`; it is cleared only by the level clear `$297E` (clears `$D300..$DBBF`, 16 call sites; EMULATED: death/restart gives 0).

Trigger (controlled terrain pass): the handler is **called iff the probe lies in an `$AF` cell** - 50,688 of 106,704 grid cases reach it, all of them inside the cell, none outside - independent of state, floor flag,
previous-update block flags, Y speed, `+$03` and invincibility. States running the floor pass (EMULATED first update, forced state): `$00-$0B, $0E-$12, $14, $15, $19-$1E, $22`;
not: loop `$0C/$0D/$13`, `$16-$18`, `$1F`, `$20`, `$21`, `$23+` (numeric ids only). Contact is **not** support: the first update with the foot in the cell only runs the handler (previous flags are the air's);
the one-way support is applied from the next update.

### 3.3 Remembered cell `$D356`

* A different cell always spawns, even while an earlier object lives (strip run: one object per cell, 6 cells). The same cell never spawns while remembered:
  jump + re-land (EMULATED: one spawn, 18 handler calls), stand on a cell whose object was removed (cell intact, 14 handler calls, 0 objects).
* A -> B -> A before A breaks: three objects (A, B, A again), three `$B0` writes (the second A write is harmless).
* `$D356` follows even when the spawn failed (full pool) - the cell then never crumbles while the player stays on it or returns to it without touching another crumble cell.

### 3.4 Allocator pools

* Parent: `$5EB7`, slots 0..15, first free; **silent no-op when full**; IY then points at `$D940` (slot 16) and the handler writes the cell pointer into that slot's `+$30/+$31`
  (EMULATED: bytes `$D970/$D971` = `44 C3` for cell (67,6); no consumer of those bytes was found - UNRESOLVED/inert).
  Full pool: no object, no hold, no break; Y speed still zeroed; Sonic stands on the intact one-way cell (anchor 174 for (67,6)).
* Children: script command 4 via `$5EE1` (slots 7..17, **shared with every badnik/command-4 allocation**). With k free slots only the first k shards exist, in the order offsets 0, 8, 16, 24
  (parameters 3, 8, 5, 1); none when 0. A child allocated in a slot **below** its parent's runs its state-0 callback one pass later, so its whole timeline is one update later.

### 3.5 Type `$13` state table (bank `$0C`, table `$A28A`, 4 states)

| State | Script | Callback | Meaning |
|---|---|---|---|
| 0 | record dur 224, frame 0 | `$A2DD` | init: parameter != 0 -> request state 3; else X := (X & `$FFE0`) + 14, Y := (Y & `$FFE0`) + 24, `+$34/35` := raw X, `+$36/37` := raw Y, request state 1 |
| 1 | record 16 (frame 0) / record 1 / sound `$A3` / 4 x spawn `$13` (dx -14, -6, 2, 10; dy -24; parameters 3, 8, 5, 1) / record 224 | `$A344` / `$A36A` / `$A33F` | rider hold x16, break, remove |
| 2 | record 224 | `$A33F` | remove - **unreachable** (nothing requests state 2) |
| 3 | velocity (0, +`$0200`), record 224 frame 15 | `$A31B` | shard: asleep -> remove; parameter countdown; vy += `$0200`; integrate (`$0338`) |

Mapping frame 0 has **no pieces** (the parent is invisible; the ledge you see is the terrain block art); frame 15 is one 4 x 16 piece (common-stream tiles `$66/$67`, art base 0).
The type has no placement token (`+$3E = 0`), so it is never recreated and never persistent.

### 3.6 Timeline (all cells; `T` = spawn update)

| Update | Event (EMULATED + controlled lab) |
|---|---|
| `T` | foot enters the cell; handler spawns; object state-0 callback runs in the same update's object pass (parent in slots 0..15, scheduler runs after the player) |
| `T+1 .. T+16` | rider hold (16 callbacks of record 1) |
| `T+17` | `$A36A`: layout RAM cell := `$B0` via `$0428 -> $6C1F` (+ name-table redraw); no hold this update; terrain leaves Sonic at cell top - 18 |
| `T+18` | sound `$A3`; 4 children created (state-0 callbacks the same pass when the slot is above the parent's); `$A33F` removes the parent |
| `T+19` | children load state 3 (velocity +2.0) and start counting down |
| shard `p` | first move at **`T+19+p`** -> cell+0 (p 3): `T+22`; +8 (p 8): `T+27`; +16 (p 5): `T+24`; +24 (p 1): `T+20` |
| shard motion | `y_k = y0 + k(k+3)` after the k-th move (y0 = cell top): +4, +6, +8, ... px; X constant; no terrain, no contact |
| shard end | sleeps when the generic lifecycle class is >= 2 (cell Y offset >= 288 below the camera at central X): measured sleep `T+31..T+40`, slot freed `T+32..T+41` (camera dependent) |

Whole-game fixtures: SEZ1 (67,6) drop: spawn 15, riders 16..31, break 32, children 33; Y: 176 (spawn update), 176 x16 (held), 174 (break update), then 181, 182, 184, 185 ...

### 3.7 Rider hold (CONTROLLED + EMULATED)

`$A344`: `LD A,($D501); CP $0E; JR Z,hold; LD A,($D503); BIT 0,A; RET NZ; hold: $D521 |= 2; $D518 := 0; $D514 := objectY - 40`.

* Applies iff **player state == `$0E` OR `+$03` bit 0 clear** (14,080 cases). No X/Y comparison with the object, no check that the player is on the cell.
* `$D521` bit 1: no reader was found (the player merge uses the *high* nibble of `$D521`); it is cleared every frame by `$5DD1`; a hovering Sonic keeps floor flags 0 and state `$0E`. Treat as inert.
* A jumping player (state `$0A`, bit 0 set) is not held until his landing clears bit 0 (jump-through fixture: spawn update 45, landing request and first hold on update 46); rolling, spin-dash and walking are held like standing.
* Ordering (hook at the scheduler entry): hold updates show anchor 174 after the terrain pass and 176 at the end of the update; the spawn update ends at 176 (first contact, no projection yet), the break update at 174.
* Walk-off fixture (SEZ1 (28,10),(29,10), LEFT held): spawns `u11/u19`, breaks `u28/u36`; hover (Y 304 beyond the ledge edge x < 896) `u28..u36` (9 updates), free fall from `u37`.

### 3.8 Break and replacement

`$A36A`: asleep (`+$04` bit 6) or `objectX < $D174` (strict, unsigned 16-bit; 1,801 cases incl. wrap) -> object removed, **cell not replaced**. Otherwise `$D354 := (IX+$31/30)`, `C := $B0`, `CALL $0428 -> $6C1F`:
layout RAM byte := `$B0`, then `$2425` redraws the 4 x 4 name-table cells (EMULATED: broken cell = 16 x tile 192, the intact neighbour keeps its art). Collision changes immediately (next lookup reads flags 0).
Natural reachability of the removal branch: the camera trails the player by about 118 px. SEZ1 bridge run at 4.0 / 5.0 / 6.0 / 7.0 px/update (EMULATED, max speed forced to `$0700`): all six cells replace and the
smallest `objectX - cameraX` at a break callback is **+8 px** (59 / 10-22 / 8-14 / 8-14 px per speed), so the removal branches are only reachable with fixtures (camera forced, `+$04` forced) in the shipped acts.

### 3.9 Lifecycle (generic `$61E1`, decoded table)

`x' = objX + 128 - camX`, `y' = objY + 128 - camY`; class = table[y' >> 4][x' >> 4] (32 x 32, bank `$1C:$8146`); outside 0..511 = class 3. Class 2 sets `+$04` bit 6 (the object's callback may remove itself),
class 3 removes (type `$FE/$FF`) unless `+$04` bit 1. The table rows are in the audit (`lifecycle.table_rows_16px_cells`); model and routine agree on 55,155 positions.

### 3.10 Contact, attack, states

* No contact: the `$13` callbacks call only `$0338` and `$0428` (byte-verified); no overlap helper, no attack gate, no damage entry. Shards cannot hurt or be hurt.
* The handler never reads `+$03`, the state, the floor flag or `$D532`; attack posture, rolling, jumping, spin-dash and invincibility change nothing about spawn/hold/break.
* Invulnerability blink (fixture used to keep the SEZ1 `$23` enemy beside (65,14)/(66,14) from interfering): timeline unchanged.
* Spring Shoes (`$12`): the shared floor pass samples 8 px lower, so the handler is reached 8 px earlier; Rocket Shoes `$11` reaches it like any airborne state. A natural shoe-on-ledge route does not exist in SEZ (UNRESOLVED end to end).

### 3.11 Persistence

* The layout RAM keeps `$B0` for the act: player + camera teleported far away and back (EMULATED): still `$B0`, no new object. A removed (asleep/left-of-camera) object leaves the cell `$AF`.
* Death/restart (the game's own sequence, `$297E` runs): `$B0` cells are `$AF` again and `$D356 = 0`.

### 3.12 Placements (SEZ; coordinates from the formulas, all locked by the cell sweep)

Object anchor (cell+14, cell+24), hold anchor Y = cell top - 16, shard anchors (cell+0/8/16/24, cell top). SEZ1: (67..69,6) | (114,8) | (28..29,10) | (114,11) | (21,13) | (97..98,13) |
**(62..67,14) six-cell bridge** | (93..94,14) | (104,28). SEZ2: (100,7) | (25..26,8) | (42,8) | (102,8) | (104,9) | (106,10) | (16..17,11) | (42..43,13) | **(44..47,18)** (four-cell bridge after the pad `(42,17)`) | (54,27).
SEZ3: (27,10). The cell above is air (`$FE`) for 24 cells; ring cells `$40` above SEZ1 (67..69,6) and SEZ2 (44..47,18); nothing solid sits above any cell. The SEZ1 bridge has a `$23` enemy placement at (2112,430) beside cells (65,14)/(66,14) (out of scope; it hurt the drop fixture until the invulnerability fixture was added).

### 3.13 Global runtime proof

The coordinate-free timeline signature (event offsets, Y relative to the cell top, shard offsets/parameters/first moves) is **identical for all 93 `$AF` cells**: THZ1 (52,11), THZ2 (20,9), SEZ x36, AQZ1 x32, AQZ2 x2, EEZ2 x21.
A byte scan of the handler, `$5EB7`, `$5EE1`, command 4, `$6C1F`, `$61E1`, the type callbacks and the floor pass finds no read of the zone byte `$D297` or act byte `$D298`. The runtime is global; only the layouts and art differ.

## 4. Surface `$1A` / block `$A7`

### 4.1 Data and placements

Block `$A7`: flags `$9A` (solid, surface `$1A`), vertical profile `0 x8, 1 x4, 2 x8, 1 x4, 0 x8`, horizontal profile `$40`, modifier 0. Floor dispatch entry `$69B1` = `RET`. The block is a solid cell with a 0..2 px bump; support = cell top + 32 - profile (1,024 cases).
Side pass: no wall; ceiling pass: no handler for surface `$1A` (24 grazing cases move the player, as for any solid profile).

| Act | Cell | World rect | Ground below | Trigger window (anchor) |
|---|---|---|---|---|
| SEZ2 | (42,17) | 1344,544 32x32 | `$08` row 18, then the `$AF` bridge (44..47,18) | X 1344..1375; Y 552..583 even / 542..573 odd; standing 558 |
| SEZ2 | (84,24) | 2688,768 | `$08` row 25 | X 2688..2719; standing 782 |
| SEZ3 | (34,7) | 1088,224 | `$08` row 8 | X 1088..1119; standing 238 |
| SEZ3 | (72,22) | 2304,704 | `$08` row 23 | X 2304..2335; standing 718 |

(also AQZ1 (80,5), AQZ2 (82,10) and (92,19), EEZ1 (41,4), EEZ2 (15,5)). SEZ2 (42,17) has `$47` (surface `$16` floor-break) cells at (39..40,17) on the way in.

### 4.2 Trigger (BYTE-VERIFIED + CONTROLLED)

`$753E`: `BC = 0`, `DE = -26` (or -16 if `(IX+7) & 1`), `$7725` lookup adds 18 -> probe Y = anchor - 8 / anchor + 2; `AND $1F` of the header flags = surface; `CP $1A -> $7646`. The probe runs in the terrain pass **after** floor, sides and ceiling, so it
sees the update's final position and flags. Handler reached iff the probe's cell is `$A7` (4,096 / 4,096 inside cases, 0 outside); effect iff the floor flag (`+$22` bit 1) is also set (2,048 effect cases).
`+$07` = the animation record counter (see `docs/player-animation-counter.md`): the parity alternates with the animation durations; both parities cover the cell for a standing walker.

### 4.3 Effect (CONTROLLED, 65,536 cases)

`$7646`: `BIT 1,(IX+$22); RET Z; HL := $0700; ($D373) := HL; ($D516) := HL; SET 1,(IX+3); RES 0,(IX+3); (IX+2) := $10; ($DE04) := $BD`. Nothing else is written; Y speed, facing, floor flags, position, `$D532` are untouched.
It is **not** the spin-dash setter `$4719` (which uses facing for +/-7.0 and requests sound `$BE`).

### 4.4 After the launch (state `$10`, shared physics)

* Callback `$3A23` -> `$3FEF` (updater: `$4B46`, `$401A`, `$4141` input/friction, `$402A`, `$4097`, `$690B`, `$48BC`) -> `$37F4` (EMULATED + byte-read).
* Measured X speed: no input 1792 -> 1787 -> 1782 (-5 per update); RIGHT held -4; low speed `$30` -> 28 -> 18 -> 0 (the shared friction; not pad-specific). `$D373` stays `$0700`
  (a RIGHT-held airborne player re-accelerates to 7.0).
* Exit rule (`$37F4`): opposing direction held while moving -> skid state `$07` (right) / `$08` (left); else `|vx| >= $10` -> stay in `$10`; else requested `$04` (DOWN) or `$01`. LEFT after a launch: `$10 <-> $07` alternation while decelerating.
* B1 during `$10`: jump state `$0A` with `+$03 = 3` (jump latch + attack posture), X speed kept (1761 at the first jump update).
* Attack posture (`+$03` bit 1) is set by the handler: the launched Sonic is an attacker (canonical attack bit, not equivalent to airborne).

### 4.5 Repeated contact, entry direction

At 2..7 px/update the column (32 px) re-triggers the handler 5 times (offsets 0/7/14/21/28 or 1/8/15/22/29 or 3/10/17/24/31 ...); a standing start in the centre triggers 3 times (17, 24, 31).
From the right (moving left, measured at 1, 4 and 7 px/update) it fires **once** at the right edge (offset 30/31) and the speed becomes +7.0: the pad can never push Sonic left. The facing flag is not written; the game turns a left-facing Sonic around on the next update (EMULATED).

### 4.6 Footwear and unusual states (EMULATED)

* First-update scan (forced state): the ring probe is reached in `$00-$0B, $0E-$12, $14, $15, $17, $19-$1E`; the launch takes effect at the first update in `$00-$0B, $0E, $0F, $10, $14, $19-$1C` (not in `$11` forced without its Rocket timer, `$12`, `$17`, `$1D`, `$1E` there: floor flag or probe parity; `$15` peel-out charge launches from the second update).
  `$12` (Spring Shoes) and `$22` (twist) do not reach the handler at the first update; loop states, `$16`, `$18`, `$1F`, `$20`, `$21` never run the probe.
* Rocket Shoes (`$D532 = 4`, timer 300): the first handler update replaces `$11` by `$10`; the selector and timer stay set (the Rocket's own audit owns what happens next).
* Spring Shoes state `$12` landing in the column (shoe object absent, forced state): probe parity 1 -> handler at the landing update, X speed 7.0, requested `$10`, Y speed -7.5 kept (a high launch); parity 0 -> no effect.
  End to end with a real `$2F` shoe is UNRESOLVED (no pad is near a shoe).
* SEZ2 (42,17) -> (44..47,18): arriving at 7 px/update, the four crumble cells spawn at x 1409/1443/1477/1504, each breaks 17 updates later, Sonic never drops below Y 560.

### 4.7 Effect 5 and the art

Effect 5 (`$1D:$81BF`, descriptor effect id 5): once per game-loop iteration while `$D492 == 0`; returns at once if `$D44E != 0`; else counter `+3` += 1; at 3: counter := 0, phase `+2` toggles 0 -> 1 -> 0, and 32 bytes are copied to VRAM `$2B00`
(tile `$158`): the first copy is `$8DFD` (3rd call), then `$8DDD`, alternating every 3 calls (period 6). SEZ uses table entries 4/5 (zone byte read at `$81E0`; other zones copy to `$2E20/$3020` or return). Measured: 60 effect calls in 60 frames,
no copies while `$D44E = 1`, 10 copies in the next 30 frames. The effect counters are cleared by `$297E` at level initialisation: the phase counts effect calls since the act began, not player time.
Block `$A7` draws tile `$158` in **8 of its 16 cells** (rows 1-2); no other SEZ2 block draws it (`$AF` does not). The two effect frames give two different block images (hashes in the audit). The composed art is a static pad with two symmetric roller-like pieces;
there is no arrow or other directional glyph.

## 5. Porting guidance (POC-san; GameMaker adapter is separate)

1. **Crumble.** Implement the handler as a floor-pass dispatch for block `$AF` on the foot sample (anchor X, anchor Y + 18 + state extra) *after* the one-way projection, exactly as in 3.2; keep the three numbers (Y-speed zero, remembered cell, pool) separate.
2. Create a dynamic object with the 16-update rider record, a 1-update break record, then the 4 children and removal: use the update offsets of 3.6 (do not re-derive timings from video).
3. Reproduce the **unconditional rider hold** (including the hover). It is observable and faithful; do not gate it on the object being under Sonic and do not hold at cell top - 18.
4. Replace the cell by `$B0` in the layout the terrain probes read, redraw it blank, keep it for the act, restore it with the act, clear the remembered cell at act start. Removal branches (asleep / left of camera X) leave the cell `$AF`.
5. Shards are cosmetic: `y_k = y0 + k(k+3)`, delays 3/8/5/1, no contact; give them the generic lifecycle (adapter in section 6), and honour the shared 7..17 child pool only if the POC models that pool.
6. **Booster.** Trigger from the same probe the POC already uses for terrain rings (parity-dependent probe Y), not from a mask; effect exactly as 4.3; state `$10` is the existing spin-dash roll state with its shared physics. Do not special-case direction.
7. Tile `$158`: alternate the two images every 3 effect calls (first `$8DFD`); do not tie it to the player.

## 6. Viewport classification (explicit; nothing 256-wide widened silently)

| Subject | Class | Rule / adapter (candidate, not a ROM fact) |
|---|---|---|
| probe, handler, rider hold, booster probe/effect | `WORLD` | player anchor + 32 px cell grid only |
| break "left of camera" | `EDGE(LEFT,0)` | `objectX < cameraX` strict; keep the relation to the visible left edge |
| shard / crumble object lifecycle | `LIFECYCLE` | table of section 3.9; candidate: the accepted generic retention adapter `max(0, viewport_width - 256)` horizontally, vertical bands not widened |
| effect 5 | frame-count timer | not viewport-relative; do not scale with the window |

## 7. Unresolved / limits

* Names/identities of surfaces `$0C`/`$1A`, blocks `$AF/$A7` and object `$13` (numeric only); purpose of the never-placed `$B9/$BA/$BB`.
* `$D521` bit 1 consumer (none found; inert in every observation); `+$30/+$31` of slot 16 clobbered by a failed spawn (no consumer found).
* Sound ids `$A3` (shatter) and `$BD` (pad) are requests only; their audio mapping is not researched.
* Spring Shoes / Rocket Shoes end to end with real shoe objects on a crumble cell or a pad (no natural route in SEZ; forced-state evidence above); natural probe parity at a Spring Shoes landing.
* The harness has approximate frame/IRQ timing (rows are per loop iteration, so lag does not change them); the removal-by-camera/asleep branches are fixture-driven; shard sleep offsets depend on the camera.
* Other whole-game research tools that restore a snapshot through `Emu.restore()` (MGHZ/GPZ/THZ fixtures) do not reset the hidden z80 prefix state; their committed results reproduce, and one MGHZ cross-run check was clean, but they were not re-audited here.
* Windows acceptance of everything above; GameMaker implementation not started.

## 8. Windows acceptance suggestions for James

1. SEZ1 (62..67,14) bridge: run right at normal speed; each cell should drop away about 17 frames after you first touch it, shards fall in a staggered 1-3-5-8 order; Sonic should not fall while running. Walk **left** off the end of (28..29,10) and watch Sonic hover for about 9 frames past the edge before falling.
2. SEZ2 (42,17): walk into the pad: Sonic should shoot right at 7 px/frame; hold LEFT right after and watch him skid (`$10`/`$07`); approach from the right and verify you are bounced back right. Press B1 during the launch to jump.
3. SEZ2 (42,17) -> (44..47,18): the launch carries Sonic across the four-cell bridge without falling; the cells crumble behind him.
4. Watch the pad art: two roller-like pieces alternate every 3 frames.

## 9. AGENTS candidate updates

Candidate lines for Manager-san (root `AGENTS.md` untouched):

* Crumble ledge: floor handler `$6B79` runs for any foot sample (anchor X, Y + 18 [+8 state `$12`, -14 state `$21`]) inside block `$AF` (surface `$0C`); it does nothing while Y speed is negative, else zeroes Y speed every call and, when the probed cell != `$D356`,
  spawns type `$13` (slots 0..15, silent when full) and remembers the cell (`$D356` is cleared only by the level clear `$297E`). Timeline from the spawn update `T`: rider hold `T+1..T+16`, cell := `$B0` at `T+17`, 4 shards + removal at `T+18`, shard `p` first moves at `T+19+p`
  (p = 3, 8, 5, 1 at cell+0/8/16/24; Y speed +2.0, +2.0 per update, no cap).
* The rider hold (`$A344`) has no presence test: any player in state `$0E` or with `+$03` bit 0 clear gets Y := cell top - 16 and Y speed 0 every update for 16 updates (walking off hovers). The break (`$A36A`) does nothing (cell stays `$AF`, still remembered) if the object is asleep or `objectX < cameraX`.
* Type `$13` has no contact, no placement token, mapping frame 0 invisible; state 2 unreachable. The runtime is global (93 cells in THZ/SEZ/AQZ/EEZ identical).
* Booster pad: block `$A7` (surface `$1A`, solid) is dispatched only by the terrain-ring probe `$753E` (Y - 8 / Y + 2 by `+$07` bit 0): with the floor flag set it writes X speed +7.0 and `$D373 = $0700`, `+$03 = (+$03 | 2) & $FE`, requests state `$10` and sound `$BD`;
  it is called every update the column contains Sonic; direction is always rightward; it cancels Rocket Shoes. Tile `$158` alternates every 3 effect calls (first `$8DFD`).
* Harness: the z80 snapshot restore must also reset the hidden prefix/interrupt-shadow state (`tools/sez_surfaces_rig.py`: one NOP, then restore) or whole-game fixtures can become history dependent.

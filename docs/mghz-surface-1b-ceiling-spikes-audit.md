# MGHZ terrain mechanics: surface `$1B` (oil, block `$A0`) and ceiling spikes (blocks `$3E/$3F`)

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`
(verified, never committed). `SonicChaos_POC` and the root `AGENTS.md` were not touched. Base: Research `main` at `ac04dfe`.

Machine-readable facts: `data/rom-cache/mghz/surface-1b-ceiling-spikes.json` (`tools/mghz_surface_ceiling.py`).
Tests: `tests/test_mghz_surface_ceiling.py`. Builds on `docs/mghz-foundation-audit.md` (which left both mechanics open),
`docs/gpz-surface19-audit.md` (shared `$D3BC` / `+$24`), `docs/platform-spike-collision-audit.md` (static `$3C/$3D` spikes, damage chain),
`docs/player-hurt-ring-scatter-audit.md` (what `$48F7` does) and `docs/spring-interaction-audit.md` (the screen-Y death rule).

Scope is exactly the two mechanics. **Not** covered: type `$24`, type `$2E`, footwear, boss `$56`. Where one of those shares a coordinate
with a hazard (type `$2E` sits on both oil pits, Spring Shoes use a different foot offset) it is flagged and left alone.

Evidence classes: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY**, **SOURCE-TRACED BEHAVIOR**, **CONTROLLED ROUTINE RESULT** (original Z80 routines on
`tools/oracle.py` with the decoded MGHZ layouts), **EMULATED ORIGINAL FRAME** (whole game in `tools/sms_frame_harness.py`, booted into zone 3), **UNRESOLVED**.
Coordinates are world pixels; the *anchor* is the player Y register (feet = anchor + 18); cells are 32 px.

## 1. Answers in one page

**Surface `$1B` / block `$A0` is a slow-sink-then-plunge hazard, and it kills.**

* Block `$A0` (header flags `$5B`: one-way bit 6, **not** solid bit 7, surface `$1B`, modifier 0, vertical profile 32 at every X, horizontal profile `$40` = no wall) is
  the only block of surface type `$1B`. MGHZ1 has one 10 x 7 pit (70 cells), MGHZ2 one 14 x 3 pit (42 cells), MGHZ3 none.
* Standing on it, the player is *held up* by a one-way projection that is moved **one pixel lower every 4th frame**. The projection is
  `Y := Y - penetration + counter` (`$D3BC`); the counter rises by one on each update whose frame counter `$D12F & 3 == 0`.
  Steady state: anchor Y = oil top - 22 + counter (feet = oil top - 4 + counter).
* When `counter + 7 >= 32` (counter **25**; **23** for blocks with modifier 10/12) the integrated foot probe crosses into the next oil block and the
  projection adds the whole counter again: Sonic drops **32 px per update** (`803, 835, 867, 899, 932` in MGHZ1). The camera follows at most 7 px/update, so
  the shared vertical-death rule (signed screen Y >= `$D0`) fires four updates later. From the first oil-handler update to the plunge is 94..104 updates (100..108 frames) and to the death request 98..108 updates in the
  harness, depending on the `$D12F` phase and lag.
* Nothing else changes: **no speed, direction, state, attack-posture or input change**. Walking, running, rolling, jumping, holding any direction all sink identically.
* Reset: the jump setter (`$45ED`), the ordinary fall setter (`$463C`) and the strip-fall setter (`$4663`) zero the counter; nothing else does. `+$24` bit 1 (the "oil" flag)
  is set only by the oil handler and cleared **only** by a foot sample of a surface-0 block (the decorative band block `$9E` counts) or by slot re-initialisation (death/restart).
  Jumping out is possible while the counter is <= 23 (fixture: 32 px rim, jump from beside the wall); a jump rise of 46 px.
* Block-header requirement: the sink branch is a property of **previous-flags bit 6 && !bit 7 plus `+$24` bit 1**, not of block `$A0`. A stale bit 1 changes the projection of
  every other one-way block (`$0D/$0F/$F9/...`) to `surface - 18 - 4 + counter`, with no depth limit. No MGHZ route was found that carries the stale bit onto them
  (the pits are one cell lower than their rims, so every exit passes through surface-0 cells that clear the bit).

**Ceiling spikes `$3E/$3F` hurt only a *rising* head, in a 32 x 25 px rectangle, and `$3E` and `$3F` are identical.**

* Collision data of `$3E` and `$3F` is byte-identical (flags `$85`, vertical profile `$58` = bit 6 + 24 at every X, horizontal profile `$60` rows 0..15 / `$40` rows 16..31). They differ
  only in art (`$3E` = the floor-spike tiles `$102..$104` vertically flipped; `$3F` = dedicated tiles `$108..$10A`). Every result below was measured for both blocks and is identical.
* The only hazard test is the **ceiling pass** `$73C9` -> `$74E7`. Probe = `(anchor X, anchor Y - 6)` (`DE = -24`, lookup adds 18): one column, no player width.
  Hurt rectangle, anchor coordinates relative to the cell origin: **X 0..31, Y 6..30** (probe row 0..24 of the cell).
* The pass runs only if the floor flag is clear **and** the Y speed is negative, or if a platform owner (`$D3C0`) is set. A falling or level player inside the rectangle is untouched
  (the "near miss" fixture peaks at anchor 383 = probe row 25 and is never hurt).
* Not hurt when `+$03` bit 7 is set (acts as an ordinary ceiling: pushed to row 24, Y speed := +1.0, ceiling flag cleared) or when the current state is `$1E`. **Power-up invincibility (`$D532 == 6`) does not protect**:
  `$48F7` contains no invincibility test (only the object-contact gate `$48BC` has one).
* Hurt consequences (shared `$48F7`): rings > 0 -> state `$1E`, rings := 0, scatter, `$D3B1 := $78`; **Y speed +1.0** (not -4.0) because the ceiling flag is set at that moment; X speed -1.0.
  Rings = 0 -> state `$1F`, Y speed -5.0.
* They are **not** ordinary solid blocks: as floor they hurt a landing (foot row >= 8 with a solid/spike previous block and not rising; any foot sample at all when the floor flag is already set),
  as walls they exist only for probe rows 0..15 and never hurt, as ceiling they are solid for probe rows 0..24 and hurt as above.
* MGHZ placements: MGHZ1 3 cells (row 15, cols 4..6); MGHZ2 25 cells in three runs (row 11 cols 27..43; (87,16); row 21 cols 107..113); MGHZ3 none.
  In MGHZ2 a `$21` top stomp under the row-11 run (floor corridor, badniks at (1040,590) and (1232,590)) leaves Sonic in state `$0B`, which has enough height to reach the spikes (fixture: hurt after a 184 px rise).

## 2. Verification summary

| Check | Result |
|---|---|
| Sink-branch parity: Python model of `$7010..$7055` vs the real routine, all 24 bit-6-only blocks, 5 columns, 41 probe rows, 6 counters, 3 Y speeds | **88,560 cases (42,456 projections), 0 mismatches** |
| `$6F61` gate matrix (7 previous-flag values x 4 `+$24` values x 2 requested states x 3 Y speeds x 2 floor flags) | 336 cases, 0 mismatches against the gate model |
| Ceiling pass sweep, both blocks, 4 Y-speed classes x floor x owner x invulnerability bit x state (`$0A`/`$1E`), 56 x 57 positions | 408,576 cases; rule holds in all 128 combinations; `$3E` == `$3F` |
| Real runs: every placed `$3E/$3F` run, rising jump state | hurt rectangle == `[run x0..x1] x [top+6 .. top+30]` for all 4 runs |
| Foot / side sweeps, both blocks | 92,160 + 7,168 cases; `$3E` == `$3F` |
| Whole-game (MGHZ1, MGHZ2 booted into the harness) | about 60 deterministic scenario runs plus two forced-state scans of 55 states; listed in sections 3, 4 and 5 |
| Oracle/harness RAM, ROM write | no ROM writes; no ROM bytes stored (region hashes only) |

Reproduce: `python tools/mghz_surface_ceiling.py ROM.sms [--check]` (about 20 s), `python -m unittest tests.test_mghz_surface_ceiling`.

## 3. Surface `$1B`

### 3.1 What the block is (DECODED DATA + BYTE-VERIFIED ASSEMBLY)

* Floor dispatch table `$6973`: surface `$1B` -> handler `$6B14`; surface `$00` -> `$6C45`; surfaces `$06/$07` -> `$6C4D`.
* `$6B14`: `SET 1,(IX+$24)`; `A = $D12F & 3`; return unless zero; `INC ($D3BC)`. That is the **whole** handler: no speed, state, flag, position or sound.
* Block `$A0`: header `$386C2`, flags `$5B`, art = one flat tile (attribute `$1173`; palette index 9 per the foundation audit). The band above the pit is block `$9E`
  (flags 0, surface 0) whose bottom tile row (attributes `$116F/$1170/$1370/$1171`) carries the surface art (inference from the mapping, not observed).
* Layout (DECODED): oil top is **one cell lower** than the solid rims on both sides.

| Act | Pit (cells x0..x1, y0..y1) | World rect (x0,y0,x1,y1) | Oil top y | Rim top y | Notes |
|---|---|---|---|---|---|
| MGHZ1 | 42..51, 25..31 | 1344,800 .. 1663,1023 | 800 | 768 (row 24, cells 41 and 52 solid, cells 42..51 are `$9E`) | pit reaches the map bottom; a `$28/$89` platform at (1360,750) and a `$2E` at (1352,780) are co-located |
| MGHZ2 | 7..20, 29..31 | 224,928 .. 671,1023 | 928 | 896 (row 28, cells 6 and 21 solid, cells 7..20 are `$9E`) | pit reaches the map bottom; a `$2E` at (232,908) is co-located |
| MGHZ3 | none | | | | |

### 3.2 Entry conditions

1. The foot sample `(X, Y + 18 + extra)` must land in an `$A0` cell. `extra` is 0 except current state `$21` (-14) and `$12` (+8) (`$6930..$694F`). X is the anchor X exactly.
2. The player must be in a state whose update performs the floor sampling `$691A`. EMULATED first-update scan of all states: **`$00-$0B, $0E, $0F, $10, $11, $12, $14, $15, $19, $1A, $1B, $1C, $1D, $1E`** run the full terrain pass and the oil
   handler; **`$22` (twist) runs the floor sampling and the oil handler but not the ceiling pass**; loop states `$0C/$0D/$13`, `$16-$18`, death `$1F`, act-clear `$20`, `$21` and `$23+` did not (numeric IDs only).
3. Contact is *not* support. The first update with the foot in oil only runs the handler: the previous flags are those of the air (no bit 6/7), so `$6F61` projects nothing; the player is held from the **next**
   update (fixture: update 25 handler only, y 783, floor flag clear; update 26 projected to 778, floor flag set).
4. If the previous update's block was ordinary solid (bit 7) the first oil update is projected like solid ground against the oil block geometry (controlled: gate matrix). No MGHZ geometry produces that entry (the pit is one cell lower than its rims).

### 3.3 The per-update algorithm (exact; verified by the 88,560-case parity sweep)

```text
# inside the floor pass, once per player update, after X/Y integration
foot  = Y + 18 + extra(state)                      # lookup clamps a negative sum to 0
blk   = layout[X >> 5][foot >> 5]                  # outside the map: block $FF, flags 0
prof  = vertical_profile(blk)[X & 31]              # block $A0: 32 for every X
# 1. projection against the PREVIOUS update's flags (prevFlags = $D36C) with THIS lookup's geometry
if   prevFlags & 0x80:  solid projection                                  # ordinary solid ground
elif prevFlags & 0x40:
     if (plus24 & 1) and requested_state == 0x14:  no support            # strip-fall request (surface $19 audit)
     elif plus24 & 2:                                                     # SINK BRANCH $7010
          if Yspeed_high_byte_bit7:  nothing at all (floor flag unchanged)   # rising
          else:
               floor_flag = 0
               probe = foot + 4 ;  row = probe & 31
               a = (prof + row) & 255
               if a >= 32:                       # always true for prof == 32
                    pen = a - 32                 # == row for the oil
                    # `CP B ; RET NC`: B = HIGH BYTE OF THE HORIZONTAL-PROFILE POINTER (>= 146 for every block): never rejects
                    Y = (Y - pen + counter) & 0xFFFF ;  floor_flag = 1 ;  modifier = block modifier
     else:                   ordinary one-way projection
# 2. remember and run the handler of the CURRENT block
prevFlags = flags(blk)
if   surface(blk) == 0x1B:  plus24 |= 2 ;  if (D12F & 3) == 0: counter = (counter + 1) & 255
elif surface(blk) == 0x00:  plus24 &= ~3
(surfaces 6 and 7 enter the surface-0 handler at $6C4D, i.e. AFTER the two RES instructions: they do NOT clear the bits)
```

Y integration for a grounded player (`$4097` -> `$410B`) forces the Y speed to `$0700`, so Y rises by 7 before the pass (9 when the previous modifier is 10/12).
Because the projection is applied against the integrated position, the steady-state fixed point is `anchor = oil_top - 22 + counter`
(`778 + counter` in MGHZ1, `906 + counter` in MGHZ2), exactly reproduced by the real routine for counters 0..24.

### 3.4 Timing, plunge and death (CONTROLLED + EMULATED)

* **Counter cadence.** Increments happen on updates whose `$D12F & 3 == 0`; `$D12F` counts displayed frames (`$0606`), not player updates. At the handler, `$D12F` took the values 32, 36, 40, ... in
  every fixture; consecutive increments are 4 apart, 8/12 apart when an update did not coincide with the right frame (harness lag). In lag-free play this is one pixel per 4 updates.
* **Plunge.** Controlled: counter 24 is stable (`802 -> 802`); counter **25** gives `803 -> 835` (+32); counter 26 `804 -> 836`. With integration 9 (modifier 10/12 floor) the threshold is 23. General step after the threshold:
  `Y' = Y + 7 + counter - ((Y + 7 + 22) & 31)`, i.e. +32 for block-aligned Y (+33 once at counter 26 in the fixture).
* **Death.** The plunge outruns the camera (follow step <= 7): MGHZ1 `sy 144, 169, 194, 220`; the ordinary vertical-death rule (`docs/spring-interaction-audit.md`: signed screen Y >= `$D0`) requests state `$1F` with Y speed -5.0
  on the following update. Fixtures (MGHZ1 centre drop, `first_oil_handler_update = 25`): plunge update 129 at counter 25, death request update 133; MGHZ2 drop: 26 / 126 / 128.
* The pit bottoms are the map bottom: MGHZ2's plunge ends at anchor 995 (foot 1013) where the lookup runs off the 32-row map (block `$FF`, no support) before the death rule fires.
* Death/restart re-initialises the player slot: counter and `+$24` return to 0 (fixture).

### 3.5 Floor / support interaction

* While sinking the player is *supported*: floor flag set, `D523` bit 1, state remains walk/stand/roll. Every sink-branch update clears the floor flag at its start and sets it again on projection, so the flag is set again inside the same pass;
  the only way to lose support is for `row + prof < 32`, which cannot happen on `$A0` (prof 32).
* A rising player (Y speed negative) is never held: the branch returns before touching the floor flag. Falling back onto the oil restarts at the current counter (zeroed by the jump setter).
* There is no depth cap: any penetration (rows 0..31 of the sampled block) is projected, so a stale bit-1 one-way block captures a player up to 31 px deep (controlled stale-bit rows).
* Side probes: block `$A0` has horizontal profile `$40` (no extent), so the oil itself is never a wall; the pit walls are the neighbouring solid cells.

### 3.6 Exit / reset (SOURCE-TRACED + EMULATED)

| Event | Counter `$D3BC` | `+$24` bit 1 |
|---|---|---|
| jump setter `$45ED` (needs: not airborne, state != `$11`, `$D36B & $FC` != `$90`) | := 0 (`$4604`) | unchanged (cleared by the next surface-0 foot sample; 0 / 1 / 4 airborne updates in the fixtures) |
| ordinary fall setter `$463C` (state `$0E`, no-op in jump state) | := 0 (`$465B`) | unchanged |
| strip-fall setter `$4663` (state `$14`) | := 0 (`$467C`) | unchanged |
| walking off the oil sideways onto solid ground | **kept** | **kept** (types 1/2 handlers do not clear it) |
| foot sample of a surface-0 block (`$9E`, `$FE`, `$2F`, ...) | kept | cleared (`$6C49`) |
| walk/run frame selectors (bank `$0C`) | cleared only when `+$24` bit 0 is set and the previous surface is not `$19` | n/a |
| death and level restart | 0 (slot re-initialised; fixture) | 0 |

No other writer of `+$24` bit 1 or `$D3BC` exists (whole-ROM byte scan: bit-1 instructions at `$6B14`, `$6C49`, `$6FC7` only; nine `$D3BC` operand sites).

### 3.7 Speed, direction, jumping, rolling, attack posture

* **Speed/direction:** the horizontal sequences on the oil and on the same cells patched to ordinary solid block `$01` are identical for 40 updates in all three tests (right from rest, left from rest, right from a run); only Y differs.
  Plunge counter and timing are the same for neutral / left / right / up / down input (counter 25 in all).
* **Jumping:** possible; first jump-state row has Y speed -4.0625, 46 px rise, counter zeroed. Re-landing restarts at the counter (2 at re-contact in the 90-update case).
* **Rolling / attack posture:** rolling (`$09`, `$D503 = $02`) keeps its state and posture for 60 updates on the oil and sinks identically (counter 15, anchor 793). Neither the handler nor the sink branch reads `$D503`.
* **Escape fixture (MGHZ1, jump from 40 px left of the far wall holding RIGHT):** reaches the far rim for counters 0, 8, 14, 18, 20, 22, 23; fails for 24 and 26. Setup-specific, not a universal threshold.

### 3.8 Stale bit-1 and other one-way blocks (CONTROLLED)

With `+$24` bit 1 set, a one-way block (`$0D`, `$0F`, `$F9` tested) places the anchor at `surface_anchor - 4 + counter` for every probe row 0..31, instead of `surface_anchor` for rows 0..15 and no capture below
(`bit1_clear: [-3,0,0,0,0,20]`, `bit1 set, counter 0/10/25: [-3,-4,...]`, `[-3,6,...]`, `[-3,21,...]`). MGHZ contains such blocks outside the oil
(`placements.other_bit6_blocks`: `$0D/$0F/$F9/$30/$31/$36/$38/$59/$73`, and strip blocks `$85/$87`). The bit survives only on ground whose foot sample is never surface 0; the oil is entered and left through surface-0 cells, so this is a latent original quirk, not an MGHZ route.

## 4. Ceiling spikes

### 4.1 Data and placements

| Block | Flags | Vertical profile | Horizontal profile | Art (attribute words) |
|---|---|---|---|---|
| `$3E` | `$85` (solid, surface 5) | `$58` at all 32 X (bit 6 + 24) | `$60` rows 0..15, `$40` rows 16..31 | `$504,$503,$502` rows 0..2 (V-flipped `$104..$102`), blank `$0C0` |
| `$3F` | `$85` | `$58` | same | `$108,$109,$10A`, `$0E3` |

| Act | Run (block, cells, world X, cell top Y) | Hazard rectangle (anchor X, anchor Y) | Above / below |
|---|---|---|---|
| MGHZ1 | `$3E`, (4..6, 15), 128..223, 480 | 128..223 x 486..510 | solid `$05/$06/$07` / air `$FE` |
| MGHZ2 | `$3F`, (27..43, 11), 864..1407, 352 | 864..1407 x 358..382 | solid `$06/$07/$08/$0B` / air `$2F` (a 7-row room, floor at y 608 with `$28/$83` platforms and two `$21`) |
| MGHZ2 | `$3F`, (87, 16), 2784..2815, 512 | 2784..2815 x 518..542 | solid `$F4` / air |
| MGHZ2 | `$3F`, (107..113, 21), 3424..3647, 672 | 3424..3647 x 678..702 | solid `$05..$0B` / air |
| MGHZ3 | none (two `$3C` floor spikes at (101,13),(103,13): platform/spike audit) | | |

### 4.2 Probe path and gate (BYTE-VERIFIED)

`$690B` runs floor, sides, **ceiling**, ring probe, merge. `$73C9`:

```text
ceiling_flag(+$22.0) := 0
if $D3C0 == 0:                         # no platform owner
     if floor_flag(+$22.1):  return    # grounded: no ceiling test at all
     if Yspeed_high_byte bit7 == 0: return     # not rising (zero counts as not rising)
probe = lookup(X, Y - 24 + 18) = (X, Y - 6)         # BC = 0, DE = $FFE8
dispatch on surface type:  5 -> $74E7
$74E7:  row = (Y-6) & 31 ;  B = vertical profile byte (here $58) ;  h = B & $3F (= 24)
        if h == 0: return ;  if h != 32 and not (B & 0x40): return
        if h < row: return                                   # rows 25..31: no collision (7 px skirt)
        Y += h - row ;  ceiling_flag := 1 ;  $64CB           # pushed DOWN so the probe row becomes 24
        if state(+$01) == $1E: return
        if (block & $FE) != $3E: JP $7459                    # other type-5 blocks ($3C/$3D): bounce, no damage
        if +$03 bit 7:          JP $7459
        JP $48F7                                             # hurt
$7459:  Yspeed := +1.0 ; ceiling_flag := 0
```

Only the head column is tested: Sonic's 8 px half-width is irrelevant, the rectangle is exactly the cell's 32 columns.
The full pass differs from the isolated rule only where the side probes (run first) push X out of the column: for rows 6..9 of the cell the wall (probe rows 0..15) can displace a grazing player before the ceiling probe (controlled `full_pass_versus_isolated`).

### 4.3 Rising / falling and the gate matrix (CONTROLLED, both blocks identical)

Hurt iff **(Y speed negative and floor flag clear) or owner `$D3C0 != 0`**, and `+$03` bit 7 clear, and state != `$1E`, and anchor in the rectangle:

| Y speed | floor flag | owner | invulnerable bit | state | result |
|---|---|---|---|---|---|
| -1.0, -1/256 | 0 | 0 | 0 | `$0A` | **hurt** (rows 6..30) |
| any | 1 | 0 | any | any | no ceiling pass |
| 0, +1.0 | 0 | 0 | any | any | no ceiling pass |
| any | any | 9 | 0 | `$0A` | **hurt** |
| -1.0 | 0 | 0 | 1 | `$0A` | pushed to row 24, Y speed +1.0 (bounce), no hurt |
| -1.0 | 0 | 0 | 0 | `$1E` | pushed to row 24, nothing else |

Attack posture (`$D503` bit 1) is not read by the ceiling pass: the rule held with `$D503 = 1` (controlled sweep) and `$D503 = 3`, a spin jump (whole-game fixtures).

EMULATED state scan (three updates, state forced, Sonic rising in the rectangle of the MGHZ2 run): the ceiling tail is reached in `$00-$0B, $0E, $0F, $10, $11, $12, $14, $15, $19, $1A, $1B, $1C, $1D, $1E` (the same set as the oil handler, except `$22`);
hurt follows in all of them except `$1E`; states `$15`/`$1A` set `+$03` bit 7 through their scripts (observed `$81`/`$80`) and therefore take the ordinary bounce; `$11` (Rocket Shoes) reaches the hurt entry too (the shoes-specific branch of `$48F7` is the footwear audit's).
No MGHZ placement delivers a platform owner to a spike (the nearest `$28` objects are the corridor floor platforms 226+ px below, or far away).

### 4.4 Consequences of a hit (EMULATED, shared `$48F7`)

Fixture: anchor X 1000, start (1000, 398) in state `$0A`, Y speed -3.0, rings (BCD) 5. Hurt at update 7 with the anchor pushed to **382**:

| | rings 5 | rings 0 |
|---|---|---|
| requested state | `$1E` | `$1F` |
| Y speed after the update | **+1.0** (`$0100`: the ceiling flag is set) | -5.0 (`$FB00`) |
| X speed | -1.0 (`D523` bit 3 clear) | 0 |
| `D523` / `D522` | 1 / 1 | 1 / 1 |
| rings, blink | 0, `$D3B1 = 119` after the update (`$78` set), `+$03 = $C1 | previous` | n/a |

The ring scatter objects and everything after the entry are the hurt audit's. The player is *pushed down* by +1.0, there is no upward rebound. The power-up invincibility case (`$D532 = 6`) produces the identical row (hurt).
Invulnerable (`+$03` bit 7, `$D3B1 = 100`): bounce at update 7, anchor 382, Y speed +1.0, state unchanged, no hurt.

### 4.5 Outside the hazard test: not ordinary solid blocks (CONTROLLED)

* **Floor (foot probe `$691A`, type-5 handler `$6ACE`):** with a previous block of solid or spike flags and a non-rising player, a foot row >= 8 of the cell is projected up to row 8 and then hurts (foot rows 8..31 hurt; rows 9..31 are projected).
  With the floor flag already set (grounded), any foot sample inside the cell hurts. Rising players and first contact from air (previous flags 0, floor flag clear) do not.
* **Sides (`$715E`):** a wall only for probe rows 0..15 of the cell (right probe pushes for anchor X 8 px before to 11 px into the cell, left probe 20..39 px); rows 16..31 (the spike tips) are not a wall. **No side damage in 7,168 cases.**
* **Ceiling:** solid for probe rows 0..24 (25 rows, inclusive), hurting as in 4.2.
* Net effect: a rising player cannot pass the cell (his head is stopped, and hurt, at probe row 24); probe rows 25..31 are a safe 7 px skirt; a falling player is ignored by the ceiling pass but lands on the cell through the foot probe; a horizontal pass through the tips (rows 16..31) meets no wall.

### 4.6 Near miss and the MGHZ2 corridor

* A jump from anchor 430 (Y speed -4.25, 46 px beneath the tip row) peaks at **383** (probe row 25): the type-5 tail is reached for 8 updates, nothing is pushed and nothing hurts. Level ground in the corridor is 208 px lower, so ordinary jumps cannot reach the spikes.
* Reaching them needs the `$0B` launch: state `$0B` from (1000, 566) with Y speed -6.75 (what a `$21` top stomp leaves) rises 184 px and is hurt at anchor 382 on update 37. The corridor floor holds two `$21` at (1040,590) and (1232,590) directly under the run.

### 4.7 Implementation checklist: the four independent `$3E/$3F` collision paths

"Rising only" describes **path A alone**. The blocks are hazardous in other paths too; implement every path separately and do not infer one from another.

| Path | Probe | Hurts? | Condition (all proven above, both blocks identical) |
|---|---|---|---|
| **A. Ceiling / head** | (X, Y-6), probe row 0..24 | **yes, only while rising** | Y speed negative and floor flag clear (or `$D3C0` owner), `+$03` bit 7 clear, state != `$1E`; otherwise solid push-down only (bounce if exempt) or no test at all |
| **B. Floor / foot (landing)** | (X, Y+18), foot row 8..31 | **yes, not rising-dependent**: a non-rising player landing on the cell | previous block solid/spike flags (or floor flag already set), not rising, `+$03` bit 7 clear; a rising player and first contact from air do not trigger it; a grounded player (floor flag set) is hurt by any foot sample in the cell |
| **C. Side walls** | (X±9, Y+6), probe rows 0..15 | **no** | wall only (rows 16..31 are not a wall); damage on sides is reserved for tiles `$F4/$F5` |
| **D. Ceiling, hazard exempt** | as A | no | `+$03` bit 7 set: solid to probe row 24, Y speed := +1.0 (bounce); state `$1E`: pushed down only |

So: "harmless unless rising" is **wrong** (path B hurts a falling or walking player who reaches the cell by the foot probe), and "hurts from every direction" is **wrong** (path A never fires for a level/falling head, path C never hurts).

## 5. MGHZ example coordinates (all measured, locked by tests)

Oil:

* MGHZ1 drop onto the pit centre: place (1503, 722), state `$0E`, 0 rings. Handler update 25, support from update 26 at anchor 778, counter 25 -> plunge `803, 835, 867, 899, 932`, death request update 133 (screen Y before: 220).
* MGHZ1 walk off the left rim: place (1300, 750), state `$05`, vx 4.0, hold RIGHT. Handler update 24, plunge update 124, death request 128, ends at the far wall x 1655.
* MGHZ2 drop: place (447, 850): handler update 26, plunge `931, 963, 995, 995, 981`, death request 128.
* Steady anchors: MGHZ1 `778 + counter`; MGHZ2 `906 + counter` (counter 0..24).

Ceiling spikes:

* MGHZ2 corridor: x 864..1407, hazard anchor Y 358..382; rising from (1000, 398) at -3.0: hurt at 382 on update 7.
* MGHZ1: x 128..223, hazard anchor Y 486..510, air below (`$FE`).

## 6. Porting guidance (POC-san; GameMaker adapter is separate)

1. Keep the three numbers separate: the **counter** (frame-gated, byte), the **projection** (`Y -= row; Y += counter`) and the **death rule** (existing screen-Y adapter). Do not tune them empirically.
2. Gate the counter on the displayed-frame tick, not on the player-update counter, exactly as `$D12F & 3`. In lag-free play this is one pixel per 4 ticks.
3. Do not widen anything for the widescreen view: the oil test is the anchor column and the 192-line `$D0` death constant is screen-relative; make the screen-Y adapter an explicit relationship to the viewport bottom edge, not a world constant.
4. Implement the sink as a branch of the one-way projection selected by the *previous* block's flags and a per-player `oil` bit, so the stale-bit quirk is reproducible; clear the bit only on surface-0 foot samples.
5. The ceiling hazard is a head-column test only; do not use Sonic's 8x24 box.
6. Treat `$3E` and `$3F` as one collision type; art differs.

## 7. Unresolved / limits

* Type `$2E` and the `$28/$89` platform co-located with the MGHZ1 pit were not examined; whether `$2E` is a visual splash is not established.
* The harness has approximate frame/IRQ timing; counter cadence in updates carries lag-dependent jitter (reported as `$D12F` values). The ROM rule itself is exact.
* The jump-escape table is one setup (jump from beside the wall), not a general reachability analysis of the pits.
* Spring Shoes (state `$12`) and state `$21` sample the floor 8 px lower / 14 px higher; their oil and spike interaction is not examined beyond the byte-verified offsets.
* The state scans use forced states and the first update(s) only; states that never appear in the listed set were not found to run the pass, not proven never to.

## 8. Windows acceptance suggestions for James

1. MGHZ1: drop into the pit from the left rim (x ~1344): Sonic's feet should start 4 px above the logical oil top (y 800), sink one pixel every ~4 frames and fall through the oil roughly 100 frames after landing, dying about 4 frames later. A jump within the first ~90 frames clears the pit (rim is 32 px up).
2. Same for MGHZ2 (14 x 3 pit, bottom at the map bottom).
3. MGHZ2 corridor: stomp the `$21` at (1040,590) and watch the `$0B` flight into the ceiling spikes: hurt, pushed *down* slowly (+1.0).

## 9. AGENTS candidate updates

Candidate lines for Manager-san (root `AGENTS.md` untouched):

* Surface `$1B` (MGHZ block `$A0`, flags `$5B`): handler `$6B14` sets player `+$24` bit 1 and does `$D3BC += 1` when `$D12F & 3 == 0`. It changes no speed/state/flag. The bit selects the **sink branch** `$7010` of the one-way projection (previous flags bit 6 and not bit 7): probe +4, `Y := Y - penetration + $D3BC`, no depth cap, rising players ignored.
* Oil timing: steady anchor = oil top - 22 + counter; at counter 25 (23 on modifier 10/12 blocks) the projection runs away at +32 px/update and the ordinary screen-Y death (`>= $D0`) follows 4 updates later. Speed, direction, rolling, jumping and attack posture do not matter. The counter is zeroed only by the jump/fall/strip-fall setters and slot re-init; `+$24` bit 1 is cleared only by a surface-0 foot sample.
* The oil pits are one cell lower than their rims (MGHZ1 (42..51, 25..31); MGHZ2 (7..20, 29..31)); the `$9E` band above is surface 0.
* Ceiling spikes `$3E/$3F` are collision-identical (art differs). The only hazard test is the ceiling pass: probe `(X, Y-6)`, hurt rectangle anchor X cell+0..31, Y cell top+6..30, only while rising with the floor flag clear (or a platform owner), not with `+$03` bit 7, not in state `$1E`; pushes the player down to probe row 24; hurt Y speed is +1.0. Power-up invincibility does not protect. They also hurt a landing (foot row >= 8) and have walls only for rows 0..15.
* MGHZ2 placements: row-11 run reaches `$21` stomp launches from the corridor floor; MGHZ1 has three cells at (4..6,15).

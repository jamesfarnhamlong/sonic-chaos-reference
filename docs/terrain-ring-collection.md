# Ordinary terrain-ring collection (`$753E`)

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`
(verified; never committed). `SonicChaos_POC` was not touched.
Machine-readable facts: `data/rom-cache/terrain-ring-collection.json`. Tool: `tools/terrain_ring_collection.py`.
Tests: `tests/test_terrain_ring_collection.py` (`tests/verify_cache.py` also regenerates the cache).
Builds on `docs/collision.md`, `docs/thz2-thz3-level-package.md` (ring populations) and `docs/object-09.md`.

Evidence classes: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY**, **SOURCE-TRACED BEHAVIOR**, **CONTROLLED ROUTINE RESULT** (the original Z80
routines run on `tools/oracle.py` with explicit RAM), **EMULATED ORIGINAL FRAME** (whole game in `tools/sms_frame_harness.py`), **UNRESOLVED**.

## 1. Answer

| Question | Result |
|---|---|
| Coordinates | **X = player anchor X** (`$D511`, BC = 0). **Y = anchor Y + DE + 18**, with DE = **-26** (`+$07` bit 0 clear, `$7541`) or **-16** (set, `$754A`) and +18 (`$12`) added inside `$7725` (the same terrain-anchor bias as the floor probe). A negative result is clamped to 0. Effective probe: **anchorY - 8** (bit clear) or **anchorY + 2** (bit set), i.e. 26 / 16 px above the terrain foot reference `anchorY + 18`. They are adjusted anchor coordinates; no state/animation Y offset and no player-extent value enters. (BYTE-VERIFIED + CONTROLLED, 814 cases, 0 mismatches) |
| `+$07` bit 0 | `+$07` is the **animation record down-counter**: records load `+$07 = duration`, the engine (`$64FA`, called at `$361D` before the state callback) does `DEC (IX+7)` each update (`$6510`) and reloads at zero; `FF 05` frame-selector routines may set it. Bit 0 is therefore the **parity of the remaining animation ticks**, not a posture flag. Only `$753E` (and one bank-`$0C` routine at `$A26E`) read it. (BYTE-VERIFIED + CONTROLLED + EMULATED) |
| Why alternate? | Mechanically because the counter decrements every update. Durations 10..1 (walk `$05`) or 4..1 alternate evenly (bit set 48 % of updates); 3,2,1 cycles (rolling `$09`, jump `$0A`, `$10`, `$16`, `$17`, `$1B`) set the bit **68 %** of updates (played jumps: 1,399 odd vs 701 even probes). Whether this dithering is intended is **UNRESOLVED**. |
| Cell/tile addressing | `column = probeX >> 5`, `row = probeY >> 5` (32x32 layout blocks); layout RAM address = `rowOffset[row]` (table `$D168`) `+ column + $C001`; a pointer outside `$C000..$CFFF` returns block `$FF`, type 0. Block id = the layout byte; surface type = low 5 bits of byte 0 of the block's header (shared table, bank 14 `$8000`, all zones). |
| Ring identification | type 7 -> blocks **`$40..$45` only** (checked against all 256 block ids). `quadrant = ((probeX>>4)&1) + 2*((probeY>>4)&1)`; presence byte `$75DC + (block-$40)*4 + quadrant` must be non-zero; the replacement block is the byte `$18` further (`$75F4..`). |
| Direction | **Any.** One probe point; no velocity, contact flag or requested state is read (1,600 combinations: 0 differences). Collection "from below" or "from the side" happens exactly when the point lies inside the quadrant; there is no separate top-only path. |
| States | Probed in standing, walking, running, rolling `$09`, jump `$0A`, spring ascent `$0B`, falling `$0E`, ramp launch `$1B`, diagonal spring `$1C` and others; **not probed** in loop states `$0C/$0D/$13`, twisting strip `$22`, act-clear `$20` and more (section 6). |
| Edge inclusivity | Integer-pixel, **all four edges inclusive**: quadrant pixels `left..left+15`, `top..top+15` must contain `(probeX, probeY)`. In anchor terms: X in `[left, left+15]`; Y in `[top+8, top+23]` (bit clear) or `[top-2, top+13]` (bit set). The fraction bytes (`+$10`, `+$13`) are not used. |
| Frame timing | Inside the player update: engine (`+$07` refreshed) -> state callback -> `$3FEF`: clamp `$4141`, X integration `$402A`, Y integration `$4097`, then `$690B`: floor `$691A`, sides `$715E`, ceiling `$73C9`, **ring probe `$753E`**, contact merge `$64CB`; damage handler `$48BC` afterwards. The probe sees the update's **final** position (equal to the frame-end position in 4,876 of 4,916 probes; 4,897 of 4,916 frames show exactly this event order). |
| THZ1 / THZ2 | Same routine, same tables (one shared header table), same ring blocks (`$40..$43`). THZ3 uses only `$40`. 142 / 133 / 6 ring quadrants; every one was swept: 224,800 cases, 0 mismatches. |

## 2. The routine

BYTE-VERIFIED. `$753E` (fixed bank 1):

```text
BC = 0 ; DE = -26 ; if (IX+7).0: DE = -16
$D442 := $D441
A := $7725(BC, DE)    ; returns header byte 0; also $D358 = X, $D35A = Y, $D353 = block, $D354 = cell pointer
$D441 := A
switch A & $1F:  7 -> ring    $1D -> block $46, +10 rings    $1A -> launcher    $14 -> blocks $3A/$3B depth correction
ring:  idx = (block-$40)*4 + ((X>>4)&1) + 2*((Y>>4)&1)
       if presence[idx] == 0: return
       cell := replacement[idx]; redraw ($23F9); effect type $03 at ($D358,$D35A) via $5E9C; sound $BF; $3138 (+1 BCD ring)
```

`$7725` with `BC = 0`: `$D358 = playerX + BC`; `Y = playerY + DE + $12`, `Y < 0 -> 0`, `$D35A = Y`; column `X >> 5`; row `Y >> 5`; cell through the
row-offset table at `$D168` and the base `$C001` (range check `CP $C0`, else block `$FF`); returns the first header byte and stores it in `$D364`.

Presence and replacement (DECODED, `$75DC` / `$75F4`):

| Block | Ring quadrants | After collecting |
|---|---|---|
| `$40` | top-left, top-right | TL taken -> `$43` (TR remains); TR taken -> `$42` (TL remains) |
| `$41` | bottom-left, bottom-right | BL taken -> `$45`; BR taken -> `$44` |
| `$42` / `$43` | top-left / top-right | `$46` |
| `$44` / `$45` | bottom-left / bottom-right | `$46` |

Effects (CONTROLLED): `$D29A` BCD +1; a carry past `$99` wraps to `00`, adds one to `$D299` and plays `$A9`; the layout cell is rewritten; the type-`$03` effect is
created at the **probe point** `(anchorX, probeY)`, not at the quadrant centre; sound `$BF`. The ring is gone for the rest of the loaded act (layout write).

The same probe also dispatches other surface types (CONTROLLED, names UNRESOLVED): type `$1D` (block `$B8`: cell `$46`, +`$10` BCD, `$BF`), type `$1A` (block `$A7`:
needs `+$22` bit 1, X speed `$0700`, requests state `$10`, `$BD`), type `$14` (blocks `$36..$3B`; `$3A/$3B` depth-correction path).

## 3. Exact collection rectangle

CONTROLLED, one isolated quadrant swept in 1 px steps (block `$42` at cell (44,2): pixels X 1408..1423, Y 64..79), both parities:

| `+$07` bit 0 | probe Y | accepted anchor X | accepted anchor Y | size |
|---|---|---|---|---|
| 0 | anchorY - 8 | 1408..1423 | 72..87 | 16 x 16 |
| 1 | anchorY + 2 | 1408..1423 | 62..77 | 16 x 16 |

In general anchor Y is in `[top+8, top+23]` / `[top-2, top+13]`. The two windows overlap on **6 rows** and their union is **26 rows** (`top-2 .. top+23`).
The probe is a **point**: it ignores the player's 8x24 extents and sprite. A negative probe row clamps to row 0 (anchor Y < 9 collects row-0 ring quadrants).

## 4. `+$07` parity (the alternation)

Controlled engine runs for every state (`timer_fixture`) and 6,000 emulated frames of seeded input (4,916 probes):

| State | `+$07` after each engine update | bit 0 set |
|---|---|---|
| `$05` walking | 10,9,...,1,10,... | 48 % |
| `$06` running | 4,3,2,1,... | 48 % |
| `$09` rolling (airborne, no floor bit) | 3,2,1,... | **68 %** |
| `$0A` jump (airborne) | 3,2,1,... | **68 %** |
| `$0B` spring | 4,3,2,1,... | 48 % |
| `$01` standing | 180,179,... | alternates every update |

On the floor `$09/$10/$1B` use a speed-dependent table instead (`docs/player-animation-counter.md`). Played: state `$0A` 701 even vs 1,399 odd probes; `$05` 564 / 523. The longest same-parity runs are 1-8 updates. Frame-selector routines (`FF 05`) write `+$07`
themselves (speed-dependent run/jump animation), so these fractions are typical values, not constants.

## 5. Frame timing (EMULATED + SOURCE-TRACED)

Per update: `$361D` -> engine `$64FA` -> callback `$5E91` -> `$3FEF` (clamp -> X integrate -> Y integrate -> `$690B`: floor, sides, ceiling, **probe**, merge) -> `$48BC`.
4,897 of 4,916 probing frames show exactly `step > clamp > x_integrate > y_integrate > probe > move_48bc`; the remaining frames use other callers (`$4C12` via vector
`$044C`, `$3F58`, `$396D/$39E6`) that also probe before `$48BC`. The probe therefore reads the **post-clamp, post-integration, post-projection** position and the
**current** `+$07`. The counter, sound and cell change take effect in the same update; the tile redraw is queued through `$23F9`.

## 6. State reach

Static reachability over CALL/JP/JR from every state-script callback (indirect jumps not followed), plus emulated forcing:

* **Static reachability (over-approximation)**: `$00-$0B, $0E, $0F, $10, $11, $12, $14, $15, $17, $19, $1A, $1B, $1C, $1D, $1E, $21, $34`.
* **Observed to probe (emulated, every real state forced, `emulated_all_states`)**: `$00-$0B, $0E, $0F, $10, $11, $12, $14, $15, $17, $19, $1A, $1B, $1C, $1D, $1E` (26 states). `$21` and `$34` do **not** probe when held: the static list over-approximates them (corrected 2026-10; see `docs/player-animation-counter.md`).
* **Not called** (static; confirmed dynamically for all of these except where noted): loop states `$0C`, `$0D`, `$13` (callbacks `$03CB/$03D1/$03CE` -> `$3C1B..$3EFD`), twist `$22`, act-clear `$20`, `$16`, `$18`, `$1F`, `$21`, `$23-$36` (all observed not to probe).
* Emulated (state requested every frame, 30 frames): standing, walking, running, rolling, jump, spring ascent, falling, ramp launch and diagonal spring probed on every
  frame in the state; `$0C`, `$0D`, `$13` and `$22` on **no** frame (the twist was tested on a real THZ1 twist block).
* States `$37-$3C` point at non-script data and are excluded.

Consequence: rings are not collected while the player is in a loop state or the twisting strip. Rolling, jumping and spring flight use the **same** mechanism with no
state-specific offset.

## 7. Tests and evidence counts

| Fixture | Cases | Result |
|---|---:|---|
| probe coordinates (`$7725`) | 814 | 0 mismatches |
| collection sweeps, THZ1 / THZ2 / THZ3 (every ring quadrant, both parities, X -2..+17, Y window +-2) | 113,600 / 106,400 / 4,800 | 0 mismatches |
| exact region (isolated quadrant) | 2 x 2,700 | rectangles as in section 3 |
| direction / state / flag independence | 1,600 | 0 differences |
| effects and replacement chain | 5 + 8 | as in section 2 |
| tests: seeded random points over whole levels + exact edges of random rings | 18,000+ | model equals the original routine |
| emulated play | 6,000 frames, 4,916 probes | event order and parity statistics |

## 8. Unresolved

* Whether the parity dithering of the probe height is intentional.
* Names of surface types `$1D`, `$1A`, `$14`.
* Runtime census of states: static reach is complete but may over-approximate; only the listed states were exercised dynamically.
* Respawn of consumed rings when an act reloads was not studied here; the pixel position of the type-`$03` effect sprite was not measured (logical position = probe point).

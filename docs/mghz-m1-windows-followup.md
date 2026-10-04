# MGHZ M1 Windows follow-up: rising platform into terrain, strip `$1A8/$1A9`, breakable `$0D`

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`
(verified, never committed). `SonicChaos_POC` and the root `AGENTS.md` were not modified (POC files were read only, see section 6).
Base: Research `main` at `7315df2`. **Left uncommitted** for review.

Machine-readable facts: `data/rom-cache/mghz/m1-windows-followup.json` (`tools/mghz_m1_followup.py`, ~30 s to regenerate, `--check` verifies it).
Tests: `tests/test_mghz_m1_followup.py`. Review renders (git-ignored, standard-library PNG writer): `python tools/mghz_m1_followup.py ROM --png build/mghz-m1-followup`.
Builds on `docs/platform-spike-collision-audit.md` (platform carry, one-way capture), `docs/mghz-surface-1b-ceiling-spikes-audit.md` (ceiling probe) and
`docs/mghz-foundation-audit.md` (effects, blocks).

Evidence classes: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY**, **SOURCE-TRACED BEHAVIOR**, **CONTROLLED ROUTINE RESULT**, **EMULATED ORIGINAL FRAME**
(whole game in `tools/sms_frame_harness.py` booted into MGHZ, PC hooks), **SYNTHETIC CONTROL** (a layout cell patched in RAM; never a canonical placement), **UNRESOLVED**.
Coordinates are world pixels; the *anchor* is the player Y register (feet = anchor + 18); cells are 32 px. "Update" = one player update (one frame in every run here).

## 1. Answers in one page

**A. The overhead terrain a rising `$28` platform reaches is breakable `$0D` (`$9C`) in two places and a one-way ledge (`$F9`) in two others. The original never embeds-and-jitters and never pushes out.**

* All 8 vertical `$28` movers in MGHZ were scanned along the carried rider's head path (`platform Y - 14`, ceiling probe `Y - 6`). Only four meet overhead terrain:
  **MGHZ2 #12** (2768,624) and **MGHZ2 #13** (3024,560), both parameter `$05` (state 13, becomes state 6 on touch), reach a column of **`$9C` blocks (surface `$0D`)**;
  **MGHZ1 #10** (2768,414) and **MGHZ1 #11** (2960,830) reach one **`$F9` block (flags `$41`, one-way)**. No MGHZ platform path meets an ordinary solid block.
* **Riding into a `$0D` ceiling kills Sonic.** Ceiling pass `$73C9` runs for a supported rider; for surface `$0D` the handler `$7464` breaks the block only when the support owner `$D3C0 == 0`;
  with an owner it jumps to **`$4984`**: requested state `$1F`, Y speed `$FB00` (-5.0), `+$04 := 0`, death-jingle request `$96`; **no ring test, no invulnerability test, no push-out, no jitter**.
  MGHZ2 #12: the platform is claimed at update 11 and Sonic dies at update **104** (platform Y 531 at the start of that update; Sonic Y 517 in the pass, head probe row 511 = bottom row of cell (86,15)).
  The same with 5 rings (rings are not scattered). MGHZ2 #13: death at update 136 (platform Y 435, Sonic Y 421).
* **The way out is to leave the platform.** A jump pressed at any update 52..102 clears `$D3C0`; the rising head then takes the *break* branch instead (block becomes `$9D`, four fragments, Sonic keeps rising).
  Presses at updates 20..51 never reach the block (he lands back on the platform and later dies); presses at 103..109 are too late (death). The platform keeps rising while he is airborne.
* **Snap to the upper surface:** yes, but only on the one-way ledges (MGHZ1 #10/#11). The platform carries Sonic *through* the 32-px `$F9` block (feet inside it, constant offset -14, no jitter) until a pass whose
  feet depth is within the one-way capture band `8 + (Y speed >> 8)` rows; that pass projects him onto the block's top (**-11 px in one update** with the natural retained speed `$0340`, support released,
  floor flag set, anchor = block top - 18). With retained Y speed 0 the depth is 8, with `$0700` it is 15 (sweep in the cache). Never for `$0D` (death comes first).
* **SMS quirk or POC divergence?** The behaviors above are canonical SMS routines (original code, not a harness artifact). A POC that lets a supported rider overlap `$9C` without dying, or that
  keeps him embedded/unsupported, **diverges** (section 6 records where the POC's ceiling code differs, read only).

**B. `$1A8/$1A9` are the two animated tiles of small ground flowers; the ROM art contains no horizontal line.**

* Only blocks **`$D2/$D3`** (surface 0, no collision, no priority) reference the tiles: 12 empty tiles (`$0C0`, all index 0) above a bottom row of `$1A8`, `$1A8` h-flipped, `$1A9`, `$1A9` h-flipped (`$D3`: pair order swapped).
  The 32x8 strip at the bottom of the cell shows a symmetric twin-bulb on a stem and a single bulb, which swap places every 4 updates (first upload at update 3, sources `$8E3D`/`$8E1D`, initial = `$8E1D`).
* 103 layout cells: MGHZ1 37, MGHZ2 44, MGHZ3 22. 98 of the 103 sit **directly above the ground-surface block `$01`** (4 above `$F5`, 1 above `$9B`); they are scattered along the ground line, not a connected strip. The MGHZ3 boss area contains five
  (cells (105,11) (109,11) (113,11) (114,11) (118,11)); MGHZ2 has 28 twist cells and four strip cells 8-10 cells away. No sprite uses VRAM tiles `$1A8/$1A9` (sprite patterns are VRAM tiles 0..255; `r6` bit 2 clear).
* The two tiles contain **no row that spans the tile** (longest nonzero run 14 px in the whole cell, 0 horizontal-line rows in all three VRAM states); rows 0..23 of the cell are index 0. A thin horizontal line is therefore
  **not ROM art**; it must come from presentation. The POC strip sprite is pixel-identical to the ROM in all three states and its schedule matches (section 6), but it paints the **index-0 pixels opaque** in the 8-row band
  (162 per block) while the static terrain keeps them transparent. I could not run Windows, so the exact artifact (atlas/filter seam at the band's top/bottom edge) is **not proven**.

**C. Breakable `$0D` has no animation or frame change before or during destruction.**

* The intact blocks `$9B/$9C` use no animated tile and no cycled palette entry (indices 1,2,8,9,12,15 / 8,9,12). All 16 tiles carry the priority bit. Destruction is one routine, `$7898`: layout cell := `$9D`,
  name-table refresh of the 4x4 tiles (same update), then four type-`$07` fragment objects (quadrant in `+$3F`, anchor = cell top-left, offsets 4/20) and sound `$A3` from the fragment's state 0. **Expected presentation = shared break
  behavior only.** The replacement `$9D` is the one that uses palette indices 4/11 (so the hole shares the scenery palette cycles).
* Triggers: floor `$6B2C` (attack posture; Sonic Y speed := `$FBC0`, -4.25), sides `$72B6/$72DD` (attack posture, |X speed| >= 3), ceiling `$7464` (support owner clear; owner set = crush death, see A).

## 2. Part A: details

### 2.1 Placements (static scan, cache `part_a.placements`)

| Act / record | World | Param / aux1 | State | Travel up (updates = px) | Overhead terrain on the carried head path |
|---|---|---|---|---|---|
| MGHZ1 #9 | (1136,240) | `$05` / `$07` | 13 -> 6 | 112 | none |
| MGHZ1 #10 | (2768,414) | `$05` / `$0C` | 13 -> 6 | 192 | cell (86,7) `$F9` (one-way) from platform Y 275 |
| MGHZ1 #11 | (2960,830) | `$05` / `$1C` | 13 -> 6 | 448 | cell (92,12) `$F9` from platform Y 435 |
| MGHZ2 #3, #4 | (304,496), (648,464) | `$0A` / `$0A`, `$12` | 11 lifts | 160, 288 | none |
| **MGHZ2 #12** | **(2768,624)** | `$05` / `$19` | 13 -> 6 | 400 | **cells (86,15)..(86,8) `$9C`** (first fatal platform Y 531), then (86,7) `$F9` |
| **MGHZ2 #13** | **(3024,560)** | `$05` / `$14` | 13 -> 6 | 320 | **cells (94,12)..(94,8) `$9C`** (first fatal Y 435), then (94,7) `$F9` |
| MGHZ2 #14 | (3856,768) | `$05` / `$10` | 13 -> 6 | 256 | none |

State 13 (`$85FE`, stationary) waits for a contact flag and enters state `+$36 = (param & $3F) + 1 = 6` (`$87B2`): latch `+$31` 0 -> 1 on any contact bit, then the lift callback `$86DA`
(Y speed -1.0 per update, reversal period `16 x aux1` updates). Once started the platform keeps moving without a rider (jump fixture). The scan rule: carried anchor = `platform Y - 14`, ceiling probe = anchor - 6.

### 2.2 Update ordering (cache `part_a.update_order`, EMULATED + BYTE-VERIFIED)

Per update, in execution order: player callback (`$3FEF`: X integration, Y integration, terrain pass `$690B` = floor, sides, **ceiling `$73C9`**) -> platform callback (`$60FB` move, support `$8814`, overlap `$6328`,
**carry `$88A0`: player Y := platform Y - 14**). So the terrain pass sees the position produced by the *previous* update's carry; the carry never sees the terrain result of the same update. A pass that kills (`$4984`)
leaves Sonic at the pre-carry Y and the platform moves once more (support is then dropped, `$D3C0 = 0`) and freezes (death freezes the object list).

### 2.3 Fixtures for direct POC comparison (all from the original game, determinism checked by `--check`)

Start: Sonic placed 39 px above the platform anchor, X speed 0, Y speed +1.0, state `$0E` (falling), airborne bit set, no input (`start` fields in the cache). `u` = update index from the placement.

| Fixture (cache key) | Expected |
|---|---|
| `mghz2_12_ride_into_breakable_0d.rings_0` | support claimed at u=11 (`$D3C0 = 9`); death at **u=104**; platform Y at the start of u=104 is 531; Sonic Y in the pass 517; events: ceiling `$7464` then `$4984`; after: requested state `$1F`, Y speed -1280, platform moves once to 530 and freezes |
| `...rings_5` | identical (rings stay 5; no scatter) |
| `mghz2_13_ride_into_breakable_0d.rings_0` | claim u=11 (`$D3C0 = 10`: slot id differs); death at **u=136**; platform Y 435; Sonic Y 421 |
| `mghz2_12_jump_window` | jump press (B1 held 3 updates) at u 20..51 -> death at 104; **52..102 -> break**; 103..109 -> death |
| `mghz2_12_break_by_jump` | press at u=60: break at **u=75**, pass Y 517, Y speed -464, `$D3C0 = 0`, cell -> `$9D`, four fragments, Sonic keeps rising |
| `mghz1_10_one_way_snap_natural` | snap at **u=194**: pass Y 217 -> 206 (-11), depth 11, platform Y 231, `$D3C0` 9 -> 0, floor flag 2, Y speed 832 retained |
| `mghz1_11_one_way_snap_natural` | snap at u=450: pass Y 377 -> 366 (-11), depth 11 |
| `mghz1_10_one_way_depth_sweep` | retained Y speed `$000,$100,$200,$300,$370,$400,$500,$700` -> depth 8,9,10,11,11,12,13,15 (= 8 + (v >> 8)), snap at u=197,196,195,194,194,193,192,190; final anchor always 206 |
| `synthetic_solid_control` (**not canonical**) | cells (86,13..15) patched to `$01`: ordinary ceiling bounce (Y speed := +1.0) in u=104..109 while he stays carried at platform Y - 14; at u=129 the *foot* probe finds solid blocks and the floor projection lifts him by one block per update (-62, -32, -32); the remaining `$9C` cells then crush him |

Rules for the POC to reproduce (SOURCE-TRACED + CONTROLLED): ceiling pass for a supported rider; `$0D` + owner -> `$4984`; `$0D` + no owner and not on floor and rising -> break; one-way capture band as above;
carry after the player pass; no X/Y speed change by the carry.

### 2.4 Not covered

An ordinary solid block above a `$28` platform does not occur in MGHZ; the synthetic control is a sketch of that generic rule, not a placement. Horizontal movers (`$89`) were not part of the question.

## 3. Part B: details

* **Block mapping (DECODED, cache `part_b.consumers.block_mapping`):** `$D2` = 12 x tile `$0C0` + `[$1A8, $1A8h, $1A9, $1A9h]`; `$D3` = `[$1A9, $1A9h, $1A8, $1A8h]`. Header flags `$00` (empty background, surface 0), no priority, palette 0.
  Only `$D2/$D3` use the tiles in any of the 116 blocks of any act.
* **Frames (BYTE-VERIFIED + CONTROLLED):** effect 14 (bank `$1D:$82F7`) uploads 64 bytes to VRAM `$3500` at update 3 from `$8E3D`, update 7 from `$8E1D`, and so on every 4th update; the two sources overlap by one tile (`X0 X1 X2`, `X0 == X2`).
  Level load leaves the `$8E1D` state in VRAM. Paused while `$D44E != 0`. Hashes of the three tile states and of the block bottoms are in the cache.
* **Emulated confirmation:** in the booted game the name table holds exactly the pattern above (13 entries in the visible window, all in the fourth row of a 4-row group, tile above `$0C0`, h-flip pairs as mapped).
* **Cells:** `part_b.consumers.layout_cells` (coordinates, the block below/above each cell, twist proximity). Review renders: `strip-blocks-D2-D3-{A,B}.png` (8x), `strip-context-*` (ground garden, start area, MGHZ2 near the twist, MGHZ3 boss area; frames A and B).
  These PNGs are for James' review; the identification as "flowers/buds" is visual and pending that review.
* **Line audit:** `part_b.thin_line_audit` computes, per VRAM state and block, the longest nonzero horizontal run (14) and rows with a run >= 16 (none).

## 4. Part C: details

* Blocks (cache `part_c.blocks`): `$9B` (14/8 cells MGHZ1/2), `$9C` (41/44), `$9D` (not placed in the layout), all header flags `$8D` for `$9B/$9C` (solid, surface `$0D`).
* Triggers (BYTE-VERIFIED, `part_c.triggers`): floor `$6B2C` requires current state not in `{$0F,$10,$15,$1A}` and player `+$03` bit 1; it sets `$D3B2 := $10`, Y speed `$FBC0`, clears the floor flag and sets the airborne bit, then `$7898`.
  Side handlers `$72B6/$72DD` need the same attack bit and |X speed high byte| >= 3. Ceiling: see A. (`$D3B2` is only written, by the jump setter `$4601` and by `$6B42`; treated as a jump-hold counter, unresolved.)
* Break (`$7898`, `part_c.break_routine_7898`): see section 1. **No intermediate block, no hit frame, no timer on the block.** Emulated floor break (MGHZ1 cell (76,23), spin jump from above): break at u=12, the same update writes `$9D`,
  refreshes the name table and spawns four fragments; player Y speed -1088 (= `$FBC0`, set by `$6B2C`).
* Fragments (`part_c.fragment_object_07`): state 0 = sound `$A3`, frame 0 (no pieces) for 1 update, init callback `$9B11`; state 1 = frame 15 (one piece), callback `$9BB5`, gravity +192 per update (measured), deleted when off-screen.
  Initial offsets (from the cell top-left) and speeds come from two tables chosen by the sign of Sonic's X speed:

  | Quadrant | x/y offset | Sonic X speed >= 0 (vx, vy) | Sonic X speed < 0 (vx, vy) |
  |---|---|---|---|
  | 0 | 4, 0 | -2.0, -4.0 | -0.5, -3.0 |
  | 1 | 20, 0 | +0.5, -3.0 | +2.0, -4.0 |
  | 2 | 4, 20 | -2.0, -1.0 | -0.5, -2.0 |
  | 3 | 20, 20 | +0.5, -2.0 | +2.0, -1.0 |

  Lifetimes in the emulation: 21..30 updates (deleted once off-screen at the bottom). Fragment *art* (which VRAM patterns the MGHZ stream supplies for frame 15) remains an open art task (`docs/mghz-foundation-audit.md`).

## 5. Verification

* `python tools/mghz_m1_followup.py ROM --check` regenerates everything (A: a few hundred short runs of the original game; B/C: decoded data and emulated checks) and byte-compares the cache (verified).
* `tests/test_mghz_m1_followup.py`: cache locks (no ROM) plus ROM-backed re-execution of fixtures (ride death x2, jump boundary, one-way depth model, break trigger, name-table scan, strip hashes). Skips ROM classes without the verified ROM.
* Cross-checks that agree with earlier audits: carry order and the `platform Y - 14` offset (`docs/platform-spike-collision-audit.md` 1.3), one-way capture band (1.5), ceiling probe `Y - 6` (`docs/mghz-surface-1b-ceiling-spikes-audit.md`).

## 6. POC comparison (read only; nothing in POC was changed)

* **A:** `SCR_chaos_core.gml` `SCR_cc_ceiling` (working tree, lines ~444-460) handles kind 13 only when `support == 0` (break); a supported rider falls through to `cp_c.unsupported = cp_kind; return;`: no `$4984` crush death.
  So the POC does not kill, which matches the Windows symptom (rider stays inside/unsupported). The one-way capture is shared code and was not re-verified against the fixtures above.
* **B:** `SPR_chaos_mghz_strip` frames 0/1/2 equal the ROM initial/`$8E3D`/`$8E1D` states for the bottom 8 rows of `$D2/$D3` (checked pixel by pixel). `chaos_mghz_terrain_dynamic` steps frame 1 at tick 4 (= ROM update 3), then every 4: schedule matches.
  Differences: the strip frames are **opaque** in rows 24..31 (162 of 256 pixels are the backdrop green), the base block sheet and static terrain are transparent there; they are drawn per cell with `draw_sprite_part` from a 512x512 atlas.
  The working tree already switches `gpu_set_texfilter(false)` around this pass (uncommitted, not mine). Recommendation (not applied): keep index-0 pixels transparent in the strip sheet and keep nearest sampling; then compare the same screen on Windows.
* **C:** the POC keeps intact art as a mutable overlay above `$9D` (per its M1 notes) and has no fragment art yet; the audit above is consistent with "no pre-break frame".

## 7. Unresolved / limits

* The exact cause of the Windows horizontal line is not reproduced (no Windows run); only "not ROM art" and the POC differences above are established.
* Platform slot ids differ between placements (`$D3C0` 9 or 10); fixtures use "non-zero".
* Frame-level phase of effect 14 against the global clock is still unverified (slot-init relative only), as in the foundation audit.
* `$D3B2` purpose, and the fragment art, are unresolved.
* Sound `$A3` is identified as the request in the fragment script, not heard.

## 8. Windows acceptance suggestions for James

1. MGHZ2 (2768,624): ride the touch-start platform up without jumping: expect the death at platform Y ~531, with or without rings. Jump at the right moment: expect the block to break and Sonic to continue.
2. MGHZ1 (2768,414): ride up through the single ledge: Sonic passes through it and pops onto its top (about 11 px) without jitter.
3. Compare a `$D2/$D3` cell (MGHZ1 (49,7)) with strip filtering off and on.

## 9. AGENTS candidate updates

* A supported `$28` rider (support owner `$D3C0 != 0`) entering a `$0D` ceiling cell dies (`$4984`); without an owner the same cell breaks. MGHZ2 #12/#13 are the real cases; fixtures in `m1-windows-followup.json`.
* The `$28` carry runs after the player pass; one-way capture depth for a carried rider is `8 + (retained Y speed >> 8)` rows, producing a one-update snap to the ledge top (MGHZ1 #10/#11).
* MGHZ tiles `$1A8/$1A9` are only the `$D2/$D3` ground-flower strip (103 cells); the ROM art contains no horizontal line; keep index-0 pixels transparent when overlaying the animated strip.
* Breakable `$0D` has no intermediate frame: layout write to `$9D` + four type-`$07` fragments (offset/speed tables in the cache) + sound `$A3`.

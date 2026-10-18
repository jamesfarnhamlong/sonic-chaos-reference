# VISUAL-0: THZ1 canonical graphics and animation audit

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified, never committed).
Base: Research `main` `b6467ba0ad79fad0937f750083a5261e7ea64e8f`; branch `research/visual0-thz1-fidelity`. The POC (accepted `poc/opening-1-cinematic@1175afa`) was **read only** and not modified.
Machine-readable facts: `data/rom-cache/visual0/sonic-animation-catalogue.json`, `data/rom-cache/visual0/block47-break.json`.
Tools: `tools/visual0_sonic_catalogue.py`, `tools/visual0_block47.py`. Tests: `tests/test_visual0_sonic_catalogue.py`, `tests/test_visual0_block47.py`.
Generated appendix (every frame, every state, POC status): [visual0-sonic-state-frame-catalogue.md](visual0-sonic-state-frame-catalogue.md).

Evidence classes: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY**, **SOURCE-TRACED**, **EMULATED ORIGINAL FRAME** (the real ROM booted in `tools/sms_frame_harness.py`; objects, SAT, VRAM, name table read back each update),
**POC SOURCE (READ-ONLY)**, **UNRESOLVED**. No screenshot of the POC and no inherited sprite name is used as evidence; ROM frames are named by number only.

## 0. Verdicts

| # | Finding | Class |
|---|---|---|
| A1 | The POC's mixed look is largely a **selection** problem: 23 ROM Sonic frames (plus 3 state-`$11` and 2 EEZ frames) already exist as pixel-identical sprites, but the accepted presentation path draws only 10 of the 55 Sonic states from ROM frames (plus the strip, EEZ-carrier and state-`$11` routes); every other state is drawn from the inherited `SPR_sonic_*` family (stand, walk, run, skid, look, spin-dash charge, hurt, death, act-clear, peel-out ...) | **CONFIRMED** (POC SOURCE + ROM catalogue) |
| A2 | In seeded emulated THZ1 play (3 runs, 14,594 player updates, 21 states, 33 distinct frames) **42.7 % of player updates are in states the POC draws with inherited art**; every observed (state, frame) pair is inside the static catalogue (0 outside) | EMULATED, 0 mismatches |
| A3 | ROM Sonic has **98 mapping frames `$00..$61`** (97 non-empty), 96 referenced by some state script or selector, only `$3B` unreferenced. 28 are wired into POC gameplay; **69 non-empty frames have no gameplay-wired POC sprite** (some exist only as opening/continue sprites) | DECODED + POC SOURCE |
| A4 | 14 frames that THZ1 play actually composes have no POC sprite case: `$07-$0A $13-$18 $22-$24 $5E` (run frames exist in the POC only as opening/continue sprites) | EMULATED + POC SOURCE |
| A5 | Loop-route states `$0C/$0D/$13` choose among **pre-rotated frames `$2A..$5D`** (selector `$903D`, 51-pair table); the POC rotates a generic sprite instead. THZ1 contains two such loops. Traversal was **not** reproduced in emulation | DECODED; traversal UNRESOLVED |
| B1 | Breaking a THZ1 `$47` ring-box is **not** a bare tile swap and **not** a multi-fragment explosion. The original shows: cell -> empty block `$46`; one smoke puff (type `$0F` parameter `$40`, frames `$07/$08/$09`, 37 updates, sound request `$AB`); **and a rising ring icon (type `$11`, frame `$0D`, 33 updates)**; ring counter +10; dynamic tile selector `$D3B3 := 1` | **CONFIRMED** (EMULATED, byte-verified chain) |
| B2 | The POC reproduces the cell swap, +10 and the puff (pixel-identical frames `$07-$09`, identical timing) but **has no type `$11` object**: the rising icon is the missing presentation element | **CONFIRMED** (POC SOURCE) |
| B3 | Break eligibility has **two** original paths. The side-sensor path (`$718F -> $736B -> $7857`, left mirror `$7234 -> $7389 -> $7857`) excludes only states `$0F/$15` and needs attack bit + non-negative Y speed; the POC adapter excludes `$10` as well. A natural **spin-dash roll (state `$10`) broke cell 1 in the real ROM** | EMULATED; POC divergence (gameplay, outside the graphics brief, recorded for the Manager) |
| B4 | Other breakables (`$0D` blocks `$9B/$9C` -> `$9D`) use a different presentation (four type `$07` shards, sound `$A3`). Static decode only here | DECODED; not emulated |

## 1. Part A: Sonic animation

### 1.1 Chain (all addresses verified)

```text
state request (+$02) -> engine $64FA: type 1 table $65BA -> state script (bank $0C, CPU $8000.., 55 states)
  record = duration, frame, callback;  FF commands (restart, request, selector FF 05, FF 0D facing frame, loops, child, sound)
  frame index (+$06 = $D506) -> bank-$0F mapping table CPU $80C8 (ROM $3C0C8, 98 words) -> frame record (pieces, tile offsets)
  frame change -> $1027 marks a transfer -> LoadPlayerTiles $0D15: table ROM $104B + frame*4 = bank, source CPU, 64-byte blocks
      -> VRAM tile 0..N (dynamic: the same 8x16 slots are reused by every frame)
  facing = +$04 bit 4: mirror piece X about the anchor and bit-reverse tile bytes through table $0100
  palette = level sprite palette (THZ1: selector $06, ROM $3B6AD); index 0 transparent
```

The catalogue tool renders every frame with this chain (`build/visual0-sonic/frame-XX.png`, ignored; contact sheet `contact-sheet.png`).
The three state-`$11` frames hash identically to the earlier independent extraction (`player-state-11-graphics.json`), and 23 THZ1 POC sprites are RGBA-identical to the
catalogue render (alpha-mask identical, palette-different for the AQZ variants; negative control: a wrong palette changes the hash).

### 1.2 What the catalogue contains

* **Frames** (appendix section 1): mapping record, pieces, tile source `bank:CPU -> ROM` and tile count, GameMaker canvas and origin (`origin = -bounds.min`, the convention of the 23 accepted sprites), THZ1 RGBA hash, the states that use it, the POC sprites that match it.
* **States** (appendix section 2): all 55, decoded the way the engine walks them (records, loops, conditional branch, selectors with their frame tables read from the ROM).
* **Frame writers**: engine record read `$654E`, `FF 0D` `$68B5`, selectors `$8EE1 $8F45 $8F76 $900B/$903D $9138`; the only other player-frame write is `$3661` (callback `$3657` via stub `$038F`, `FF 01` in state 0): it writes frame `$10` and the **same engine pass** then loads state 0's record frame `$0B`, so frame `$10` is never composed for the player.
* **Request census** (appendix section 3): byte-pattern census of immediate state requests in the resident engine and the player part of bank `$0C`, plus script `FF 03` chains. Code versus data is not classified, so a hit is evidence of reach, not proof.

### 1.3 Special transitions and selector rules (BYTE-VERIFIED)

| Mechanism | Rule | Frames |
|---|---|---|
| State 0 / 1 | `FF 01 $038F` (state 0 only), record `$0B` x180, `FF 03 02`, restart. State 2 (idle-wait, not seen in 18k emulated updates) then plays `$0C` x64, 20 loops of `$0D`/`$0E` x16, `$0F` x64, `$10/$11/$12` x16, jump | `$0B`; `$0C-$12` |
| Walk `$05` / act-clear `$20` | selector `$8EE1`: side contact `$D523&$0C` -> frame **`$5E`**, duration 2 (before any strip test); surface-`$19` strip set `$3C-$3F`; else shared index `$D52F` over `$01..$06`. Duration loaded only on record reload (`docs/player-animation-counter.md`) | `$01-$06`, `$3C-$3F`, `$5E` |
| Run `$06` | selector `$8F45`: `$07..$0A` (duration 4) or strip `$3C-$3F`; walk and run **share** the index | `$07-$0A`, `$3C-$3F` |
| Roll `$09`, jump `$0A`, spin-dash roll `$10`, ramp `$1B` | selector `$8F76`: 20-entry table `$25 $26 $27 $28 $29 $26 $27 $28 $25 $29 $27 $28 $25 $26 $29 $28 $25 $26 $27 $29`, duration from the floor table (10,8,6,5,4,3,2,2...) or 3 in the air | `$25-$29` |
| Spin-dash charge `$0F` | three-record loop `$22 $23 $24` x2 (the ball with the dust cloud, distinct from `$25-$29`) | `$22-$24` |
| Spring ascent `$0B` | `FF 08` reads `$D448` bit 0 at each restart: **set** (strong upright spring) -> frame `$61` x4, repeated; **clear** -> 12 records of 4 (`$1C-$21` twice), then 4,4,6,6,6,8 (82 updates) and the test repeats | `$1C-$21`, `$61` |
| Diagonal spring `$1C`, strip fall `$14` | `$1C..$21` x8 / x4 | `$1C-$21` |
| Fall `$0E` | `$02 $03 $04 $05 $06 $01` x8, repeated | `$01-$06` |
| Hurt `$1E`, death `$1F` | `$17` (1,2,4 updates), `$18` x128 | `$17`, `$18` |
| Numeric reward `$11` / Spring Shoes `$12` | `$38 $39 $3A $39` (8,4,8,4) / `$0B` x4 | `$38-$3A`, `$0B` |
| Peel-out `$15` / `$1A` | run frames `$07-$0A` with durations 6,5,4,3,2 (state `$15`, with a counted loop and a call at `$82CC`) / 2 (state `$1A`, call `$8313`) | `$07-$0A` |
| Loop route `$0C` `$0D` `$13` | selector `$903D`: route progress `D39E` / 13 indexes a 51-pair table (`$906C`) -> `$01-$06` then the rotated set `$2A-$5D`; when `+$03` bit 1 (rolling) the selector tail-jumps to `$8F76`. `$1D` uses the same table with a 16-pair, height-keyed index (`$900B`) | `$01-$06`, `$2A-$5D` |
| EEZ carrier `$16` / `$17` | `$5F` x1 / selector `$9138` (4-step cycle `$5F $60 $5F $60`, duration 3) | `$5F`, `$60` |
| Shared script `$806E` (states `$18 $23 $24 $26 $27 $2A-$2F $32`) | `$5F x32; $60 x32; $61 x32` (role unknown; none of these states is requested by an immediate-form site) | `$5F-$61` |

### 1.4 What the POC does, state by state (POC SOURCE, read-only, accepted `1175afa`)

Presentation from ROM frames (`chaos_player_animation_supported`): states `$09 $0A $0B $0E $10 $12 $14 $1B $1C $21`, plus the surface-`$19` strip (`$3C-$3F`), the EEZ carrier (`$5F/$60`)
and state `$11` through a separate path (`$38-$3A`). **Everything else** goes through the legacy chooser in `SCR_chaos_core_sprites`
(`SPR_player_stop/walk/run/up/down/break/spin_dash/falling/jump/spin` -> `SPR_sonic_*`), using the POC's own thresholds (e.g. `abs(vx) >= 1024` for run, `cp_c.next == 3` for "up", `== 4` for "down", `7/8` for "break").

| THZ1 state (ROM) | Share of 14,594 observed updates | ROM frames | POC draws |
|---|---:|---|---|
| `$0A` jump, `$09` roll, `$10` spin-dash roll, `$1B` ramp | 46.9 % | `$25-$29` | ROM frames |
| `$05` walk (incl. side-contact `$5E`) | 22.9 % | `$01-$06`, `$5E` | **inherited** `SPR_sonic_walk`; `$5E` has no sprite |
| `$0B` spring ascent, `$1C` diagonal spring | 6.0 % | `$1C-$21`, `$61` | ROM frames |
| `$04` | 6.1 % | `$14` | inherited |
| `$0E` fall | 4.4 % | `$01-$06` | ROM frames |
| `$1F` death | 3.1 % | `$18` | inherited (`SPR_sonic_death`) |
| `$06` run | 2.0 % | `$07-$0A` | inherited |
| `$0F` spin-dash charge | 1.9 % | `$22-$24` | inherited `SPR_sonic_spin_dash` |
| `$03`, `$07`, `$08`, `$00/$01`, `$15/$1A` | 4.5 % | `$13`, `$15/$16`, `$0B`, `$07-$0A` | inherited |
| `$1E` hurt | 1.5 % | `$17` | inherited (`SPR_player_falling`) |
| `$20` act-clear | 0.7 % | `$01-$06` | inherited |

(Percentages from `emulated_play.observed_state_frame_counts`; random pad input, so they describe *what occurs*, not how a person plays. Idle-wait state `$02` and the loops were not reached.)

So the inconsistency the reviewer sees is real and structural: ROM art while airborne or curled (`$25-$29` etc.) versus a different artist's walk/run/stand/skid. The ROM walk set (`$01-$06`),
stand (`$0B`), skid/turn (`$13/$14`), look (`$15/$16`) and charge (`$22-$24`) frames are all extractable today; the POC already ships `$01-$06`, `$0B` (and run `$07-$0A` for the opening/continue cinematics) as correct sprites.

### 1.5 Import contract for the POC (not performed here)

1. **Registration**: the tool prints canvas and origin for every frame (appendix); the accepted resources use `origin = (-bounds.min_x, -bounds.min_y)`. Mirror (`image_xscale = -1`) **about the anchor**, which is what the ROM's piece-X mirroring does; do not mirror about the canvas centre.
2. **Missing frames in THZ1 play** (export with `python tools/visual0_sonic_catalogue.py ROM --output build/visual0-sonic`): `$07 $08 $09 $0A` (run; opening/continue copies exist), `$13`, `$14`, `$15 $16`, `$17`, `$18`, `$22 $23 $24`, `$5E`; for idle-wait `$0C-$12`; for the loops `$2A-$5D`.
3. **Selection**: drive the sprite from the canonical state and frame (the shadow engine already tracks state/selector/phase in `chaos_player_animation_update`); do not choose by speed thresholds.
4. **Palette**: one sprite variant per zone palette (the POC already has THZ and AQZ variants; `data/u5a/player-static.json` lists the per-act selectors).

### 1.6 Unresolved (stated, not guessed)

* **Loop traversal in THZ1** (two surface-`$10` structures, blocks `$48-$55` at cells (72..75, 9..13) and (88..91, 12..16)): the dispatcher `$6C82/$6C99` routes to `$3EAB/$3EE1/$3EF7` only for plane-1 or `$51/$57` previous-foot-block cases; several scripted starts were blocked by the walls before the entry. Which exact route enters `$0C/$0D` in THZ1 and the facing/mirroring of `$2A-$5D` are **UNRESOLVED** (proposed VISUAL-1 task).
* Idle-wait `$02` frame order is decoded from the script but was not observed in play.
* Palette effects during power-ups and invincibility (CRAM operations) were not analysed; the render uses the static level sprite palette.
* Tails (type 2, 54 states) and the other-character selectors `$8CB4/$8D05` are out of scope. States `$25`-`$36` (ending, continue and cutscene scripts) are catalogued statically only.
* Names: only roles already established in this repository are attached to states (appendix); every other state stays numeric.

## 2. Part B: THZ1 terrain block `$47`

### 2.1 Chain

```text
cells: layout (104..107, 8) = world (3328|3360|3392|3424, 256), block $47 in all four (DECODED)
$47 collision header $383F1: surface $16
  foot/top path:  $6AE3  attack bit +$03.1; state not $0F $10 $15 $1A; (D522&$0C != 0 or Y speed >= 0) -> vy := $FBC0, airborne, JP $7857
  side path:      side sample type $16: $718F -> $736B (right), $7234 -> $7389 (left): state not $0F $15; +$03.1; Y speed >= 0 -> JP $7857 (no velocity change)
$7857:  D3B3 := 1; cell := $46; name-table refresh $23F9; allocate type $0F param $40 at (cell X + 16, cell Y + 8) via $5EB7; JP $4AC2 (+10 rings, BCD $10)
type $0F init $A060: param bit 6 -> state 3; spawns type $11 at the same X,Y through $0371 -> $5EB7
type $0F state 3 (script $A00B): FF 06 $AB; 7 x4, 8 x4, 9 x4, 7 x4, 8 x4, 9 x8, 8 x4, 7 x4, 7 x1; then record 0 x128 whose callback $A0C6 removes it
type $11 state 1: FF 02 vy = $FB00 (-5.0 px/update); record $0D x32 (callback $A244: vy += $0040 per update, capped at +$0080 once positive via $0350 -> $5F84, then position += speed via $0338 -> $60FB); record 0 x128 whose callback $A250 removes it
```

Types `$0F` and `$11` (and the type-`$07` shards) share mapping table `$8C71`. Frames: `$07` one piece (-4,-16) tile `$24`; `$08` two pieces tiles `$26/$28`; `$09` tiles `$2A/$2C`; `$0D` two pieces tiles `$5E/$60` (8x16 each, 16x16 together).

### 2.2 Emulated timeline (EMULATED ORIGINAL FRAME; two independent entries)

Both a controlled top landing (cell 0, state `$0A`, entry `$6B11`) and a **natural spin dash** (cell 1, state `$10`, entry `$7386`, pad-driven DOWN + button 1 taps, then RIGHT) produced the identical response:

| Update (0 = creation) | Puff, type `$0F` at (cell X+16, 264) | Icon, type `$11` |
|---|---|---|
| 0 | creation: empty record, requests state 3 | frame `$0D` already loaded, Y 264 |
| 1 | `FF 06 $AB` executes (sound request `$AB`) | Y 259 |
| 1-4 / 5-8 / 9-12 | frames `$07` / `$08` / `$09` | Y by update 1..: 259, 254, 250, 245, 241, 238, 234, 231, 228, 225, 223, 220, 218, 217, 215, 214, 213, 212, 212, 211, 211, 212, 212, 212, 212, 213, 213, 213, 213, 214, 214, 214, 214 |
| 13-16 / 17-20 / 21-28 | `$07` / `$08` / `$09` | (continues) |
| 29-32 / 33-37 | `$08` / `$07` (5 updates) | update 33 carries the empty record and the removal callback |
| 38 | empty record, removed | - |

* Puff = 37 visible object updates; icon = 33 updates of frame `$0D` (anchor Y 264 down to a minimum of 211 and back to 214, i.e. it rises about 53 pixels and settles). Pieces reach the SAT one video frame after the update that loaded the frame in this harness.
* Only the struck cell changes: the name-table 4x4 words become all `$00C0` (block `$46`: sixteen empty tiles); the other three cells stay `$47`. The pre-break 4x4 words equal the static `$47` mapping; the post-break words equal the static `$46` mapping.
* Ring BCD `$D29A` 0x00 -> 0x10. `D3B3` is stored 1 at `$7859` and consumed within the update: tiles `$4C-$51` change (stream `$399A0`, hash `63250c66...`); tiles `$5E-$61` are written with identical bytes (stream `$39EE0`), so the icon art is the content that was already resident. Source-traced, **not** emulated: a type-`$10` monitor on screen at that instant would show the replaced `$4C-$51` face (frame `$0B` uses those tiles).
* Tile art: puff tiles `$24-$2D` equal the static THZ1 VRAM image (`vram_24_2D_equals_static_thz1_vram: true`, supplemental stream bank `$08` `$B340`). Frames are rendered in the THZ1 sprite palette `$06`.
* Sound: request `$AB` (numeric only; no PC asset is claimed).

### 2.3 POC comparison (POC SOURCE, read-only)

`SCR_chaos_block47_step` + `OBJ_chaos_object_0F_transient`: cell 71 -> 70, +10 rings, puff created at (cell X + 16, 264) with `SPR_chaos_object_0F` images 0/1/2 that are **pixel-identical** to ROM frames `$07/$08/$09`; the frame schedule (4,4,4,4,4,8,4,4,+1; visible < 37) matches the ROM script. **Missing**: type `$11` (no object exists), hence no rising icon; the break adapter also applies its own swept box and excludes state `$10` on every contact (the ROM side path does not).

### 2.4 Implementation contract

1. Create the puff exactly as now; add one more transient at the same (X, Y) that uses frame `$0D` (export `build/visual0-block47/type0F-frame-0D.png`, 16x16, tiles `$5E-$61` in the THZ1 sprite palette) and the 33-update Y table above, removed after the last update.
2. Eligibility: foot/top path as `$6AE3` (with the `-4.25` rebound); side path as `$736B/$7389` (state not `$0F/$15`, attack bit, Y speed >= 0, **spin-dash roll `$10` allowed**, no velocity change).
3. Do not replace the cells with type `$10` objects, do not invent debris.

### 2.5 Adjacent finding: `$0D` breakables (static only)

`$6B2C -> $7898` (blocks `$9B/$9C` -> `$9D`, dominant in SEZ 145/100/8, MGHZ 55/52/0, SS4 41) allocates **four type `$07` objects** (parameters 0..3 at the cell's X/Y) that play sound `$A3` then show frame `$0F` (one 8x16 piece, tile `$66`, 128-update record) with their own callbacks (`$9B11`, `$9BB5`). This is the genuine "fragments" presentation; its trajectories were **not** emulated here (UNRESOLVED, proposed VISUAL-1).

### 2.6 Unresolved

* Contact from below (the ceiling branch of `$6AE3`) and the left-hand side path were not driven.
* Other zones' type-`$0F` art (the POC substitutes zone poof sprites) was not audited; this report is THZ1 only.
* The icon is named only by appearance in prose; no semantic name is assigned to type `$11`.

## 3. Reproduce and verify

```sh
python tools/visual0_sonic_catalogue.py ROM --output build/visual0-sonic --poc PATH_TO_POC --emulate \
    --metadata data/rom-cache/visual0/sonic-animation-catalogue.json --doc docs/visual0-sonic-state-frame-catalogue.md
python tools/visual0_block47.py ROM --output build/visual0-block47 --poc PATH_TO_POC \
    --metadata data/rom-cache/visual0/block47-break.json            # add --check to compare instead of write
python -m unittest tests.test_visual0_sonic_catalogue tests.test_visual0_block47
```

`--poc` is optional (without it the POC sections are omitted); `SONIC_CHAOS_ROM` overrides the ROM search. Both caches regenerate **byte-identically** (`--check`), generated PNGs stay in ignored `build/`.

# SEZ1–3 foundation audit (Sleeping Egg Zone)

Research branch `research/sez-foundation`, based on canonical Research `main`
`e0f42f89a6ecabd6ed504ef318ea8170ce1a3f1f`. Canonical ROM: Sonic Chaos (Europe) v1.2,
SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified by every
tool). POC and root `AGENTS.md` untouched. Foundation/census pass only — no boss implementation.

Machine-readable package (regenerate/check with the tools below):

| File | Tool |
|---|---|
| `data/rom-cache/sez/implementation-manifest.json` (**the three-act implementation manifest**) | `tools/sez_foundation.py` |
| `data/rom-cache/sez/object-census.json` | `tools/sez_object_census.py` |
| `data/rom-cache/sez/art-approval.json` + ignored `build/sez-approval/*.png` | `tools/sez_art_approval.py`, `tools/sez_art_previews.py` |
| `tests/test_sez_foundation.py` | 34 tests, 15,938 counted sweep checks |

Object census, reuse proofs, new enemies and the boss boundary: [`sez-object-census.md`](sez-object-census.md).

**Zone index.** SEZ is ROM zone index **2** (THZ 0, GPZ 1, SEZ 2, MGHZ 3, AQZ 4, EEZ 5). Evidence: object lists
`$70E00/$70F60/$7108A` (bank `$1C`), layouts `$54000` / `$54CC8` / `$53460` (SEZ1/2/3), mapping table `$46A40`
(bank `$11`) and art `$60000` equal the community offsets table.

## 1. Block-mapping pointer: SEZ does **not** inherit the GPZ decoder mistake

SEZ's mapping table is `$11:$AA40` (file `$46A40`), **`$2A40` bytes into its bank** — unlike THZ and MGHZ it is *not* bank
aligned, so the historical table-relative decoder would be wrong here (every block would read `$2A40` bytes too far).
Corrected shared rule (`tools/level_package.py::block_mapping`, unchanged):

```text
mappingFile = bank*$4000 + pointer - $8000        ; $11*$4000 = $44000
```

*Evidence (CONTROLLED ROUTINE RESULT).* For each SEZ act the original loader `$4FDC` was executed (registers `$D162/$D164` =
`$11/$AA40`), then both original pointer consumers (`$5316` horizontal, `$53DF` vertical) for **all 256 block IDs**; the bytes the
original reads equal the decoder's for every block: 3 acts × 256 × 2 = **1,536 checks, 0 mismatches** (the manifest records the 512 checks per act; the test re-runs all 1,536). For all three acts the historical formula reads *different* bytes for all 256 blocks, and its
resolved-offset hash differs from the correct one. All 170 exported block records (union of used and replacement blocks) carry the
bank-correct mapping, attribute hash and pixel hash. No old/local SEZ export was consulted.

## 2. Level foundation

| Act | Cells | Pixels | Player | Camera | Camera max (x,y) | Loaded cells | Distinct blocks | Terrain-ring quadrants |
|---|---|---|---|---|---|---|---|---|
| SEZ1 | 128×32 | 4096×1024 | (110,718) | (0,608) | (3840,784) | 4095 of 4096 | 57 | 54 |
| SEZ2 | 128×32 | 4096×1024 | (110,846) | (0,742) | (3840,784) | 4095 of 4096 | 56 | 180 |
| SEZ3 | 128×32 | 4096×1024 | (110,821) | (0,702) | (3840,784) | 4095 of 4096 | 53 | 42 |

Camera minimum `(0,8)` in all acts. All three acts are **128×32** (no 160- or 80-wide act; terrain lookups must still use the act
width). Starts come from loader `$4E57` (executed by a test). **Loader ceiling preserved:** the original layout loader `$4DC4`
writes 4095 bytes and stops at `$D000`; cell index 4095 of **every** SEZ act is *not* terrain (`unloaded_cells`), proven by running the
original loader against the three streams (12,285 cell comparisons, sentinel byte untouched). Header consistency checks (stride =
width, `D282 = (w−8)·32`, `D27E+240 = pixel height`, row table `$5A97`) hold for all three. Collision headers are one global table
(`$0E:$8000`, file `$38000`) for every zone and act, so a block ID has the same surface/profile everywhere — surface reuse is a
block-ID question.

**Graphics.** Seven static loads, identical for all three acts: terrain `$60000` → tile `$C0` (**239 tiles**), `$23340` → `$10` (90,
shared object stream), platform `$26370` → `$6A` (8), `$26030` → `$72` (20), `$25950` → `$86` (14), Spring Shoes `$26840` → `$94` (16),
`$253C0` → `$A4` (18, `transform_remap`). Palettes: background `$17` (ROM `$3B7BD`), sprite `$08` (ROM `$3B6CD`); the boss uses sprite
palette `$0E` (14). No parallax plane exists; the background is part of the single block layer.

## 3. Animated terrain and level effects

| Mechanism | Source | SEZ result |
|---|---|---|
| Terrain-ring animation | `LoadRingArtPointers` row zone 2 (`$2A9A`), routine `$1D:$850A` | 4 frames × 128 B from `$1D:$855D` to VRAM `$29A0` (tiles `$14D..$150`), 8 updates/frame (same frame data as every zone; zone-specific destination) |
| Level effect slots | descriptor bytes 6..9 = `[5,0,0,0]` | single effect **5**, dispatcher `$1D:$8000` |
| Effect 5 | `$1D:$81BF` | zone-indexed VRAM animation. Zone 2 copies 32 B alternately from `$1D:$8DFD` / `$1D:$8DDD` to VRAM `$2B00` (**tile `$158`**) every **3** updates; paused while `$D44E != 0` (boss active). Zones 0/1/3 are RET stubs; zones 4/5 use `$2E20`/`$3020` |

Effect 5 was executed for 300 updates (exact period 3, strict alternation), for all 255 non-zero `$D44E` values (always paused) and for
all six zone rows (only zones 2, 4, 5 write). The only block that draws tile `$158` is **`$A7`** (the surface-`$1A` block; SEZ2/3):
it is its animated art. Absolute phase against `$D12F` is not claimed.

## 4. Zone-dependent code: nothing special-cases zone 2

A linear sweep of the fixed ROM and banks `$0C/$1C/$1D/$1E` found **51** `LD A,($D297)` sites (`zone_dependent_code`). Each was
classified by its first following compare: every gate tests 0, 3, 4, 5, 6, 7 or 8 — **none tests zone 2**. SEZ therefore differs
from the shared engine only through zone-indexed *tables*: art/palette/object-list/header tables, the ring+effect descriptor
(`$2A9A`), effect-5 frames, boss framework rows (`zone+$D4A5`), the sign prize-table parity and the zone-`!= 0` diagonal-spring launch
(`$6AB9`, −5.5). The sign prize selector `$0C:$A909` was **executed for zones 0..5**: SEZ gets table `$A919` (THZ parity), MGHZ/GPZ `$A962`.
Water is absent (`$4B46`/`$D443` gate on zone 4 acts 0–1). No camera triggers/locks exist in the act headers; only the shared boss
framework locks the camera (SEZ3).

## 5. Collision and special-surface census

All used surfaces, cells per act (SEZ1/2/3) and status. "Accepted shared" = researched and Windows-accepted in THZ/GPZ/MGHZ.

| Surface | Blocks | Cells | Consumer | Status |
|---|---|---|---|---|
| `$00` `$01` `$02` `$03` | ordinary, slopes | many | `$6C45/$6A5D/$6A5B/$6A5C` | accepted shared |
| `$05` | `$3D` | 0/0/4 | floor spike probe `$6ACE` (also THZ1/2, AQZ2) | accepted shared (`$3C/$3D` audit) |
| `$07` rings | `$40..$45` | 36/121/28 | probe `$753E` | accepted shared |
| `$09` upright spring | `$30,$31` | 0/9/1 | `$6A75` | accepted shared |
| `$0A` horizontal spring | `$32,$33` | 0/2/0 | side path `$71FC/$7283` | accepted shared |
| `$0D` breakable | `$9B,$9C` → `$9D` | 145/100/8 | `$6B2C → $7898` | researched; **dominant SEZ terrain**; shard art = common-stream tile `$66/$67` (zone independent) |
| `$12` ramp | `$1F,$23` | 2/6/2 | `$69B2` | accepted shared (THZ first curve, same block IDs) |
| `$14` diagonal spring | `$36` | 0/0/1 | `$6A90` (zone ≠ 0 → −5.5) | accepted shared |
| `$16` floor break/bounce | `$47` | 5/18/4 | `$6AE3` | accepted shared (GPZ closure / THZ block `$47`: a terrain monitor picture) |
| **`$0C`** | `$AF` | 19/16/1 | `$6B79` | **new — needs audit** |
| **`$1A`** | `$A7` | 0/2/2 | probe `$753E → $7646` | **new — needs audit** |

Absent from SEZ: twist `$17`, strip `$19`, oil `$1B`, isometric `$1C`, ceiling spikes `$3E/$3F`, and any plane-switching block (no block has a
different alternate-plane header, so no loop route data exist; `$0C` is **not** a loop surface).

Controlled results (all swept exhaustively on the original routines, 769 cases):

* **`$0C` / block `$AF` (flags `$4C`, one-way).** Handler `$6B79` returns if player `+$19` bit 7 is set; otherwise, when the probed cell
  pointer `$D354` differs from the remembered `$D356`, it spawns a **type `$13`** at the probed position and stores the pointer
  (`$D356` follows even if the 16-slot allocator is full and nothing was created). Swept over all 256 `+$19` values × same/different
  cell (512 cases) plus the full-allocator case. Type `$13` (bank `$0C`, 4 states) snaps to the cell (+14, +24), holds a grounded
  player at `objY−40` for 16 updates (`$A344`), then replaces the cell by block **`$B0`** (empty) through vector `$0428 → $6C1F`
  and emits four shard children (`$13` parameters 3/8/5/1, frame 15). It removes itself when asleep or left of camera X
  (`EDGE(LEFT,0)`). Behaviour is **decoded and byte-read, not audited** (rider timing, shard timing, interaction with attack states,
  respawn after leaving the map). 36 SEZ cells; also THZ1/2 ×1, AQZ ×34, EEZ ×21.
* **`$1A` / block `$A7`.** Dispatched only by the terrain probe `$753E` (the ring probe). If player `+$22` bit 1 (floor) is set it writes
  `$D373 = $D516 = $0700` (max X speed and X velocity +7.0), sets `+$03` bit 1 / clears bit 0, requests state `$10` and sound `$BD`;
  otherwise nothing (swept over all 256 `+$22` values). Direction is fixed positive in the handler; whether the block art/placement
  implies only rightward entry is open. 4 SEZ cells; AQZ ×3, EEZ ×2.

## 6. Canonical data → original runtime → possible GameMaker adapter

`implementation-manifest.json › special_mechanics` (6 rows) records, for each SEZ-specific mechanic, the three layers separately and
never fills a gap with invented behaviour: crumble `$0C`, booster `$1A`, breakable `$0D`, ramp `$12`, block `$47`, effect-5 tile `$158`.
Adapters named there are **candidates** (cell replacement, terrain-probe interaction, two-frame tile strip), not ROM facts.

## 7. Rings

Terrain rings 54 / 180 / 42 quadrants (`coordinate_sha256` per act); **no type `$09` rings and no hidden `$01` rings** in SEZ. Both
accepted pipelines apply unchanged: probe `$753E` (all 13 recorded routine regions byte-identical to the accepted audit; no zone-2 gate
inside). The probe also dispatches `$1A` — the POC's ring probe slot is where the booster belongs.

## 8. Viewport classification (see census §7 for objects)

`WORLD`: start/camera words, camera limits (right/bottom exclusive; a right limit `worldWidth−viewportWidth` is an explicit adapter, not ROM
intent), terrain, effect-5 pause. `EDGE`: generic mapped lifecycle, sign clear `RIGHT+33`, wake conversion `RIGHT+32`, crumble-object left removal.
`PLAYER_DIST`: boss trigger (160, 304). `LOCKED_CAMERA`: boss camera target `(2976,462)` nominal. Nothing 256-wide was widened silently; candidate
adapters are listed only where needed.

## 9. Verification

```text
.venv/Scripts/python.exe tools/sez_foundation.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe tools/sez_object_census.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe tools/sez_art_approval.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe -m unittest tests.test_sez_foundation tests.test_block_mapping_audit tests.test_level_package tests.test_mghz_foundation
git diff --check
```

PNG boards: `python tools/sez_art_approval.py <rom>` (project venv) then `tools/sez_art_previews.py` with a Pillow-enabled Python (16 PNGs in
`build/sez-approval/`, git-ignored). **Approved by James on 2026-10-05 (all 16 boards) for POC use.**

## 10. Unresolved

* Surface `$0C`/`$13` crumble and surface `$1A` booster semantics (§5); package S2.
* Effect-5 absolute phase vs the global clock; whether `$A7`'s tile `$158` is the only animated art of the pad.
* Results/act-3 tables `$2D84`, `$32CA`, `$A3A0` (zone-indexed presentation) — deferred with the results screen.
* No Windows/gameplay acceptance is claimed; the visual package was approved by James on 2026-10-05.

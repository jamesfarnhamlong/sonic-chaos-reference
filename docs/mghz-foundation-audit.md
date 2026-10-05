# MGHZ1–3 foundation audit (Mecha Green Hill)

Research branch `research/mghz-foundation`, based on Research `main` `399f95b`
(recoverable-ring checkpoint). Canonical ROM: Sonic Chaos (Europe) v1.2, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified).
POC and root `AGENTS.md` untouched; work left uncommitted for review.

Later dedicated runtime closure: [MGHZ3 `$56/$57/$58`](mghz3-boss-56-audit.md).
Its boss implementation manifest supersedes this foundation's unresolved boss
reconnaissance; the original foundation cache remains a dated data/census checkpoint.

Machine-readable packages (regenerate/check with the tools below):

| File | Tool |
|---|---|
| `data/rom-cache/mghz/implementation-manifest.json` | `tools/mghz_foundation.py` |
| `data/rom-cache/mghz/object-census.json` | `tools/mghz_object_census.py` |
| `data/rom-cache/mghz/art-approval.json` + ignored `build/mghz-approval/*.png` | `tools/mghz_art_approval.py`, `tools/mghz_art_previews.py` |

Object census, enemies, boss and footwear: `docs/mghz-object-census.md`.

**Zone index.** MGHZ is ROM zone index **3** (THZ 0, GPZ 1, SEZ 2, MGHZ 3, APZ 4, EEZ 5).
Evidence: object list `$710B8`, layout `$559D4`, mapping `$50000`, art `$619F0` equal the
community table. Note: `tools/gpz_enemy_approval.py::placements` labels index 2 as `mghz`;
it only filters numeric types, but do not reuse its labels.

## 1. Level foundation

| Act | Cells | Pixels | Player | Camera | Camera max (x,y) | Loaded cells |
|---|---|---|---|---|---|---|
| MGHZ1 | 128×32 | 4096×1024 | (78,192) | (0,80) | (3840,784) | 4095 of 4096 |
| MGHZ2 | 128×32 | 4096×1024 | (112,558) | (0,447) | (3840,784) | 4095 of 4096 |
| MGHZ3 | 120×24 | 3840×768 | (110,160) | (0,48) | (3584,528) | 2880 of 2880 |

Camera minimum (0,8) in all acts. Starts come from loader `$4E57` (executed by a test). The
original 4095-cell loader ceiling applies: index 4095 of MGHZ1/2 is not terrain (manifest
`unloaded_cells`). All three header consistency checks hold (stride = width, `D282 = (w−8)·32`,
`D27E+240 = pixel height`). Row table `$5A97`/`$5AD7` (MGHZ3), shared collision table bank `$0E:$8000`.

**Mapping pointer.** Header bank `$14`, table `$14:$8000` = file `$50000`; pointers are absolute
CPU words in bank `$14`: `file = $50000 + word − $8000`. The table sits on a bank boundary, so the
old table-relative formula is *numerically identical here* — this is the masking the GPZ
correction warned about. Verified instead against the original consumers `$5316` and `$53DF`
(512 checks, 0 mismatches; test also executes six blocks on MGHZ2 and a non-aligned Aqua table in the
same bank to show the old formula would be wrong there). Do not assume the GPZ export rules; all
MGHZ blocks (116 distinct incl. replacements) carry bank-correct mappings, hashes and pixel counts.

**Blocks.** 77 / 111 / 52 distinct layout blocks per act. No block has a different alternate-plane
header (no plane-switching routes in MGHZ). Priority-bit tiles occur in 29 blocks (MGHZ2 list in the
manifest `census.priority_blocks_in_layout`; foreground pass already exists for GPZ). The background
is part of the single block layer (non-solid blocks `$28..$2F`, `$C6..$E3`, `$FE`); there is no
parallax plane in the ROM tables.

**Graphics.** Eight static loads, identical for all three acts: terrain `$619F0` → tile `$C0` (250 tiles),
`$23340` → `$10` (90), platform `$26470` → `$6A` (8), `$26780` → `$72` (10), `$25CD0` → `$7C` and remapped
`$8E` (18 each), `$25EE0` → `$A0` (12), `$26840` → `$AC` (16). Palettes: background `$18`
(ROM `$3B7CD`), sprite `$09` (ROM `$3B6DD`); exact CRAM in the manifest. Boss uses sprite palette `$0F`.

## 2. Animated terrain and dynamic art

| Mechanism | Source | MGHZ result |
|---|---|---|
| Terrain-ring animation | `LoadRingArtPointers` descriptor (`$2A9A` → `$2B14`), routine `$1D:$850A` | 4 frames × 128 B from `$1D:$855D` to VRAM `$2160` (tiles `$10B..$10E`, blocks `$40..$45`), 8 updates/frame. Same frame source as other zones, zone-specific destination |
| Level effect slots | descriptor bytes 6..9 → `$D452` slots, dispatcher `$1D:$8000` (gate `$D492 == 0`) | effect IDs **2, 3, 14**, slot 4 unused |
| Effect 2 | `$1D:$832E` | CRAM bg entry 4 (`$D476`), every 10 updates; observed bytes 0→`$30`→0→`$14`→`$28`→0 (60-update period) |
| Effect 3 | `$1D:$8360` | CRAM bg entry 11 (`$D47D`), every 10 updates, ten values (100-update period) |
| Effect 14 | `$1D:$82F7` | 64 bytes to VRAM `$3500` (tiles `$1A8/$1A9`) alternating `$8E3D`/`$8E1D` every 4 updates; paused while `$D44E != 0` (boss active). Blocks `$D2/$D3` use these tiles |

Event series were produced by executing the original routines (`level_effects` in the manifest).
Absolute phase against `$D12F` is not claimed. The dependency `$D44E` is set by the boss framework,
so effect 14 must freeze during the MGHZ3 fight. Other zone-dependent code sites (51 listed with
annotations) were swept: none besides the above, the twist/diagonal gates, the sign prize table
(odd zone → `$A962`, so MGHZ uses the GPZ table) and the shared boss framework affects MGHZ.
Sign art selector `$12` overwrites tiles `$6A..$A9` at act clear (original behaviour).

## 3. Collision and special-surface census

All used surfaces, cell counts (MGHZ1/2/3), consumers and status:

| Surface | Blocks | Cells | Consumer | Status |
|---|---|---|---|---|
| `$00` `$01` `$02` `$03` | ordinary, slopes (`$10..$1D`) | many | floor `$6C45/$6A5D/$6A5B/$6A5C` (no special; `$6A5D` acts only in zone 5) | accepted shared |
| `$07` rings | `$40..$45` | 89/83/54 | `$753E` | accepted shared |
| `$09` upright spring | `$30,$31` | 12/2/3 | `$6A75` | accepted shared |
| `$0A` horizontal spring | `$32,$34,$35` | 2/6/1 | side post-test `$71FC/$7283` | accepted shared |
| `$14` diagonal spring | `$36,$38` | 4/11/0 | `$6A90` (zone≠0 → −5.5 Y) | accepted shared |
| `$19` strip | `$85,$87` | 56/26/41 | `$6B23` | accepted shared (GPZ closure) |
| `$17` twist | `$58..$73` | 0/28/0 | `$6E56`; zone 3 selects variants 2/3 | researched; data only |
| `$0D` breakable | `$9B,$9C` → `$9D` | 55/52/0 | `$6B2C → $7898`, side `$72B6/$72DD`, ceiling `$7464` | researched; art/fragment data |
| `$05` spikes | `$3C` up; `$3E,$3F` **ceiling** | 3/30/2 | floor `$6ACE`, side wall `$7306/$7329`, ceiling hurt `$74E7` for `$3E/$3F` | **new: ceiling audit** |
| `$1B` oil | `$A0` | 70/42/0 | `$6B14` + one-way sinking branch `$7010` | **new: dedicated audit** |
| `$18` | `$8A,$8B` | 1/7/1 | floor `$69B1` (RET); no other consumer found; also in THZ | accepted shared (visual check) |
| bit-6 one-way blocks | `$0D,$0F,$F9` (surface 1) | 5/13/0 | accepted one-way projection | accepted shared |

There are **no** type-`$26` mapped springs, no surface `$16/$10/$12/$13/$1C`, no ceiling springs
(`$3A/$3B`) and no loop routes in MGHZ.

**Surface `$1B` (new).** Handler `$6B14` sets player `+$24` bit 1 and increments `$D3BC` on every
fourth `$D12F` update (executed by test). Only the *one-way* branch (previous flags bit 6, set for
block `$A0` = flags `$5B`) reads bit 1 (`$6FC7 → $7010`): it probes 4 px lower and adds `$D3BC`
to the corrected Y at `$703D`, i.e. Sonic sinks. Only surface `$00` (`$6C45`) clears the bit, so
stale bit 1 can persist over ordinary ground; effects on state, escape, death and the `$D3BC`
reset sites (`$4604/$465B/$467C`) need a dedicated audit. Block `$A0` is a flat single-colour
fill (palette index 9) — oil/liquid is a candidate reading, not a proven name.

**Ceiling spikes (new).** `$74E7` applies projection like a solid ceiling and hurts via `$48F7`
only when the sampled block `& $FE == $3E` (blocks `$3E/$3F`; 3 cells MGHZ1, 25 MGHZ2). Existing spike
audit covers `$3C/$3D` floor behaviour only. Side contact with any surface-5 block is a plain wall.

**Twist.** MGHZ2's single 28-cell strip (blocks `$58..$73`, entry tiles `$59/$73`) uses the accepted
twist handlers; zone 3 sets `+$38` to 2/3 (`$6E7F/$6EE8/$6F52`). The POC core already maps
`level == 3` to variants 2/3 (read-only observation); data integration only.

## 4. Rings

Terrain rings 169 / 136 / 83 quadrants; type `$09` 0 / 6 / 0 (all visible, parameter `$00`). Both
accepted pipelines apply unchanged. No hidden `$01` rings.

## 5. What is new versus reused

- **New terrain mechanics:** surface `$1B` sinking; ceiling spikes; level effects 2/3/14 (presentation).
- **Reused with new data:** twist variants 2/3, breakable `$0D` (fragment art for MGHZ), `$19` strip,
  diagonal springs (−5.5), ring pipelines (new VRAM destination), platforms `$28/$83/$89/$05/$0A`.
- **Absent from MGHZ:** loops, plane switches, isometric surface `$1C`, mapped `$26` springs, surface `$16`.

## 6. Verification

```text
.venv/Scripts/python.exe tools/mghz_foundation.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe tools/mghz_object_census.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe tools/mghz_art_approval.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe -m unittest tests.test_mghz_foundation tests.test_block_mapping_audit tests.test_level_package tests.test_gpz_foundation
git diff --check
```

63 tests pass, no skips (with `SONIC_CHAOS_ROM` pointing at the verified ROM); regenerated caches
match. PNG boards: `python tools/mghz_art_approval.py <rom>` then a Pillow-enabled Python
`tools/mghz_art_previews.py` (16 PNGs in `build/mghz-approval/`, git-ignored).

## 7. Unresolved

- ~~Surface `$1B` semantics; ceiling-spike hurt behaviour~~ — resolved in `docs/mghz-surface-1b-ceiling-spikes-audit.md`. Still open: fragment art for type `$07`.
- Effect phase vs. global clock; which scenery the `$1A8/$1A9` pair draws (needs PNG review). The scenery is identified in `docs/mghz-m1-windows-followup.md` (blocks `$D2/$D3`, ground flowers); effect phase vs. the global clock is still open.
- Surface `$18` visual role; no mghz-specific background scroll was found.
- No Windows/gameplay acceptance is claimed; the PNG boards were approved by James on 2026-10-04 for this foundation checkpoint.

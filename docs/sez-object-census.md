# SEZ1–3 object census, reuse proofs, enemies, boss boundary and rollout plan

Companion to [`sez-foundation-audit.md`](sez-foundation-audit.md). Data: `data/rom-cache/sez/object-census.json`
(`tools/sez_object_census.py`). This is a **census plus bounded reconnaissance**, not a behaviour audit. Numeric type IDs are
authoritative; community names are leads only. POC state is a read-only observation of `472c7b9` (MGHZ3 boss).

## 1. Placement census (39 / 33 / 5 records, none off-map)

| Type | Param(s) | aux | SEZ1 | SEZ2 | SEZ3 | Category | Classification |
|---|---|---|---:|---:|---:|---|---|
| `$10` | `$01` / `$02` / `$06` | – | 2/1/2 | 1/1/2 | 0/1/1 | monitor | shared, recovered |
| `$10` | `$04` Rocket Shoes | – | 1 | 1 | 0 | footwear | shared, recovered |
| `$18` | `$00` sign | – | 1 | 1 | 0 | support | shared, recovered |
| `$1B` | `$00` | – | 2 | 2 | 0 | hazard | shared, recovered |
| `$20` | `$00` / `$01` | `$A4/$A4` | 3+1 | 2+1 | 0 | enemy | **SEZ-specific, needs audit** |
| `$23` | `$00` | `$86/$86` | 4 | 4 | 0 | enemy | **SEZ-specific, needs audit** |
| `$26` | `$00` / `$01` | `$72/$72` | 3/4 | 7/5 | 1/0 | mapped spring | shared, recovered |
| `$26` | `$88`, `$8C` (span) | `$72/$00` | 1+1 | 0 | 0 | mapped spring | shared (`$8C` is a new value of the accepted span rule) |
| `$28` | `$83` | `$6A/$6A` | 2 | 0 | 0 | platform | shared, SEZ art |
| `$28` | `$84` / `$04` | `$6A/$6A` | 0/1 | 1/0 | 0 | platform | shared state 5 (`$04`: axis flag clear, partial) |
| `$28` | **`$86`** | `$6A/$18,$30,$1C` | 2 | 1 | 0 | platform | **state 7, needs audit** |
| `$2F` | `$00` | `$94/$94` | 8 | 4 | 1 | Spring Shoes | shared, SEZ art base |
| `$54` | `$00` | `$00/$00` | 0 | 0 | 1 | boss | boss/support |

Full per-record data (index, ROM offset `$70E00/$70F60/$7108A`, raw bytes, flags, aux, X/Y, anchor cell/block, classification) is in the JSON.
Coordinates are preserved exactly (`world = stored − 256`). **SEZ places no type `$09` ring**: every ring is a terrain ring.
SEZ3 contains only two monitors, one spring, one Spring Shoes and the boss — **no sign**.

**Six-zone reuse.** `$20`, `$23`, `$54` (and the dynamic children `$55` and `$13`) appear in no other zone: researching them buys SEZ only.
`$2F` is shared with MGHZ, `$26` with THZ/GPZ/EEZ, `$28` with all but AQZ, `$10`/`$18` with all six.

**Dynamically created (never placed):** `$13` (surface `$0C` and its own shards), `$07` (breakable shards), `$55` (boss child), and the shared
`$0F` smoke, `$34` puff, `$0A` bonus/sparkle, `$12` HUD slide-away, `$06` lost ring, `$03` ring sparkle.

## 2. Proven reuse (exact vs partial)

Each shared system was checked by **bytes**, not appearance: the routine regions recorded by its accepted audit (`shared_system_proofs`) are
re-hashed in the ROM (0 mismatches) and tested for zone-indexed code sites inside them (none tests zone 2).

| System | Result | Evidence |
|---|---|---|
| Terrain rings (`$753E`, quadrant tables, replacement chain) | **exact** (13 regions) | probe bytes unchanged; only the VRAM destination `$29A0` is SEZ data; no `$09` rings exist |
| Shared hurt / lost-ring scatter (type `$06`) | **exact** (22 regions) | no zone gate inside; `$06` frames 1–6 compose identically in all 18 acts |
| Mapped `$26` springs | **exact** (30 spring regions); art identical to THZ | frames 0–3 identical for bases `$72/$72` and `$72/$00`; new parameter `$8C` follows the accepted span rule `(p & $7F)·16` = 192 px |
| Terrain springs `$09`/`$0A`/`$14` | **exact**; diagonal launch −5.5 because zone ≠ 0 | `$6AB9` is the only zone gate in the region; blocks `$30..$33`, `$36` |
| `$10` monitors (params 1/2/4/6) | **exact**; frames 0/11/12 identical to THZ | all four SEZ parameters are accepted rewards |
| `$28` platforms | **behaviour exact for `$83/$84`; art NEW** | state table/callbacks unchanged; frame 1 differs from THZ, GPZ **and** MGHZ → SEZ-specific composition (approved 2026-10-05); `$86` (state 7) and `$04` are **not** accepted |
| Ordinary sign clear (`$18`, SEZ1/2) | **exact** (45 regions) | prize selector executed: zone 2 → table `$A919` (THZ parity); pan targets (3832,405) / (3832,245) inside limits |
| Rocket Shoes (`$10` param 4) | **exact**; 1 + 1 placements | counts match `powerup-shoes.json` |
| Spring Shoes (`$2F`) | **exact behaviour, SEZ art base `$94`** | `$26840` is the *same ROM stream* as MGHZ (`→ $AC`); decoded hash and all five frame compositions identical; only the VRAM base (`$94` vs `$AC`) and the sprite palette (`$08` vs `$09`) differ |
| Shared `$0F` smoke, `$34` puff, `$0A`, `$03`, `$07`/`$13` shard | **exact art** | 19 frames compose identically in all 18 acts (static common stream, base 0) |
| `$1B` moving spike | **exact**; frame 14 identical | accepted THZ audit; art base `$00` |
| Sprite palettes | **new colour data** | the zone sprite palette CRAM (`$08`) differs from THZ/GPZ/MGHZ for every shared object: compositions are identical, colours need the shared-objects board |

Spring Shoes presentation (cadence 12 + 69, +16/+11 follow, unmirrored, `$12→$0E` sign conversion) therefore carries over unchanged; do **not**
copy MGHZ's base `$AC` — SEZ uses `$94`.

## 3. SEZ-specific enemies `$20` and `$23` (reconnaissance)

Both live in bank `$0C`, use the shared helper vectors (`$033B` contact/attack, `$0323` attack check, `$0338` move, `$0320` floor projection,
`$037A` terrain probe) and read **no placement parameter** and **no camera RAM** (static code scan). Identity is numeric only.

* **`$20`** — 5 states (callbacks `$B100`, `$B119`, `$B14C`), frames 0..2, both visible states **set `+$04` bit 4** so the runtime composition is the
  bit4=1 image (never a whole-bitmap flip). Art `$A4/$A4` (18 tiles from `$253C0`, `transform_remap`), extents 7×20. Controlled trace
  (player parked, object forced awake, act layout loaded): walks left at −0.5 px/update, hops with Y speed −3.0 after a 128-update counter or when the
  block sampled at (±4, −8) ahead is `$47/$F6/$F7`, returns to ordinary gravity-fall; it does not turn at ledges (e.g. SEZ1 #34 falls 110 → 434).
  Param `$01` vs `$00` is not read by any callback.
* **`$23`** — 3 states (`$B3FD`, `$B412`, `$B439`), frames 0..2, bit4 never set (unmirrored only), art `$86/$86` (14 tiles from `$25950`), extents 9×26.
  Controlled trace: repeated leaps — Y speed −2.0, X speed −1.0, gravity +`$10` per update, lands after 64 updates, rests 22 updates, repeats every 88
  (≈ 65 px per leap to the left); the first period (state changes at updates 66 and 89) is identical in all 8 traces, later periods depend on the terrain.

Contact/defeat outcomes (attack vs hurt), lifecycle with the wide-view adapter, hop timing against `$D12F`, and facing/animation are **not audited**.

## 4. Platform parameters (exhaustive creator sweep)

The original creator `$80EB` + two updates was run for **every parameter value 0..255 whose state lies in the 15-state table (56 values)**:
`state = 13 if (p & $7F) ∈ {5,11} else (p & $3F)+1`, axis flag `+$25 = $FF` iff bit 7 (0 mismatches). SEZ uses `$83` (state 4, accepted GPZ/MGHZ),
`$84` (state 5, accepted THZ), **`$04`** (state 5 with the axis flag clear — one placement, partial) and **`$86`** (state **7**, initial X speed +1.0,
three placements with aux1 `$18/$30/$1C`). State 7 (`$87E2`, "touch-started horizontal mover") is the only platform state with no accepted placement;
its code region is scanned (no camera references). Package S3.

## 5. SEZ3 boss `$54` and the boundary

| Item | Value (evidence) |
|---|---|
| Placement | `54 80 0D 6E 03 00 00 00 00` at ROM `$7108A`, world **(3200, 622)**, inside the map (DECODED) |
| State table | bank `$1E`, `$A1DC`, **13 states**; own states **3, 6, 7, 8, 9, 10, 11, 12**; states 0, 1, 2, 4, 5 are the *shared* boss-framework scripts (`$95B1/$95BA/$95C0/$95CC/$961E`, identical to `$50`/`$56`) |
| Init (`$A291`, BYTE-VERIFIED) | dynamic art selector **`$15`**, sprite palette index **14**, health byte **8**, requests state 6, moves (−64, −192), Y speed +0.75 |
| Children / support IDs | **`$55`** (4 states, frames 0, 17–19; spawned by state 7 at (−16,−36)); `$34` puffs (parameter 4, five spawns in state 4); `$12` HUD; `$0F` smoke; `$0A` bonus/sparkle — the last four are **shared** and already researched |
| Mapping | `$962D`, 20 frames, shared by `$54` and `$55` |
| Framework row | zone+`$D4A5` = 2: trigger `abs(dx)<160`, `abs(dy)<304`; camera target = anchor + (−224, −160) = **(2976, 462)** nominal (`PLAYER_DIST` / `LOCKED_CAMERA`) |
| Clear | no sign; boss chain converges on the shared defeat script (`$95CC`, `$9A1E/$9A29/$9A2F`), shared `$0A/$0F` and player state `$20` — SEZ3 gate/camera release **UNRESOLVED** |
| Not derived | hits to defeat (health byte 8 decrements through zero in earlier bosses), per-state behaviour, arena clamp, contact boxes, camera RAM uses (the scan shows `cameraLimit*`, `cameraX`, `bossActive` references) |

Boundary: the SEZ3 act without the boss is a playable foundation (rings, monitors, spring, shoes, terrain); the boss needs its own package (S5).
Dependencies are **mostly shared**: only `$54`'s own states, `$55` and art selector `$15`/palette 14 are new.

## 6. Footwear

Placements (13 Spring Shoes + 2 Rocket monitors, verified against `powerup-shoes.json`): Rocket monitors SEZ1 (2192,878) and SEZ2 (1584,942);
Spring Shoes SEZ1 ×8, SEZ2 ×4, SEZ3 ×1 (all aux `$94/$94`; terrain windows and neighbours are in the JSON).

## 7. Viewport classification

All SEZ constants are classified explicitly (`viewport_classification`, 13 rows) — `WORLD`: start/camera/limits, effect-5 pause, platform state 7;
`EDGE`: generic lifecycle (visible `[LEFT,RIGHT)`, awake margin 32, create/sleep bands 96..32 outside each edge), sign clear `RIGHT+33`, sign wake `RIGHT+32`,
crumble-object removal `LEFT+0`, player edge clamp; `PLAYER_DIST`: boss trigger (160,304), `$20/$23` (no screen references); `LOCKED_CAMERA`: boss camera
target; `UNRESOLVED`: the boss object's own camera-limit manipulations. **Candidate adapters** (explicit, not ROM intent): reuse the accepted post-wake
horizontal retention `max(0, viewport_width−256)` for `$20/$23/$26/$28/$10/$1B/$2F`; right camera limit `worldWidth − viewportWidth`; a boss composition
adapter belongs to the boss package. Nothing 256-wide was widened.

## 8. Visual approval package (APPROVED 2026-10-05)

`tools/sez_art_approval.py` + `tools/sez_art_previews.py` recompose from ROM mappings/SAT data through the original render oracle (no hand-edited
sprites); 16 PNGs in git-ignored `build/sez-approval/`; the committed `data/rom-cache/sez/art-approval.json` records subjects, bases, palettes and
composition hashes with state **APPROVED BY USER 2026-10-05**: James reviewed all 16 boards and approved the complete visual package for POC use.

* **New compositions (approved):** SEZ terrain tiles/blocks (`terrain-tiles`, `terrain-blocks`, `terrain-special-surfaces`, `terrain-context-sez1..3`,
  `map-sez1..3`), `animated-terrain` (ring frames at `$29A0`, effect-5 tile `$158`, block `$A7`), `type-20`, `type-23`, `type-28` (SEZ platform art), `type-54`
  (boss + `$55` child frames incl. dynamic selector `$15`, arena/approach contexts).
* **Unchanged shared compositions** (`$10`, `$1B`, `$26`, `$2F` frames, `$07` shard): proven identical in §2 and shown once on
  `shared-objects-sez-palette.png` **only for the SEZ sprite-palette colours**.
* Forced mirrors (`bit4=1`) of `$23/$28/$2F/$54` are diagnostics and not candidates; for `$20` the script-set bit4=1 image is the canonical one.

## 9. Rollout plan (bounded)

| Pkg | Scope | Blocked by |
|---|---|---|
| **S1** SEZ three-act foundation | terrain/art/palettes, 4095 ceiling, terrain rings, springs, monitors, sign clear (SEZ1/2), shoes, `$28` `$83/$84`, breakable `$0D`, ramp `$12`, block `$47`, `$3D`, effect-5, shared support | – (visual package approved 2026-10-05) |
| S2 terrain mechanics | surface `$0C/$13` crumble and `$1A` booster audits | – |
| S3 platform state 7 | `$28` parameter `$86` (+ `$04` axis variant) | – |
| S4 enemies | `$20`, `$23` audits (15 placements, SEZ only) | – |
| S5 SEZ3 boss | `$54/$55` dedicated audit + implementation | S1 |

## 10. Unresolved

* Identity/name of `$20`, `$23`, `$54`, `$55`, `$13`; their gameplay (§3, §5).
* Platform state 7 and parameter `$04` behaviour (§4); surfaces `$0C/$13` and `$1A` (foundation §5).
* SEZ3 clear gate, hit count and arena; boss camera-limit RAM uses.
* Effect-5 absolute phase; results-screen zone tables; Windows acceptance of any of the above.

## 11. AGENTS candidate updates

* SEZ is ROM zone 2: three acts, all **128×32**, 4095-cell loader ceiling in all three; mapping table `$11:$AA40` is **not** bank aligned (`$2A40` into the
  bank) so the bank-relative rule is mandatory and now verified for 1,536 block/consumer pairs.
* SEZ shares the engine: no code gate tests zone 2; differences are tables (art, palettes `$17`/`$08`, boss row 2, effect 5, prize table `$A919`).
* SEZ has no type `$09` rings and no loops/plane switches; `$0C` is a crumble candidate, `$1A` a booster candidate — both need a small audit before import.
* Spring Shoes art base is `$94` in SEZ (`$AC` in MGHZ); same ROM stream and compositions. Platform `$28` art is SEZ-specific; parameter `$86` is state 7.
* New SEZ-only types: `$20`, `$23` (enemies), `$54` (SEZ3 boss, shared framework states 0/1/2/4/5, own 3/6..12, child `$55`, selector `$15`, palette 14, health byte 8).
* SEZ3 has no sign; its clear path is the boss chain (UNRESOLVED).

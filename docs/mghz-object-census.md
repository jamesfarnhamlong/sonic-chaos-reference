# MGHZ1–3 object census, enemies, boss and rollout plan

Companion to `docs/mghz-foundation-audit.md`. Data: `data/rom-cache/mghz/object-census.json`
(`tools/mghz_object_census.py`). This is a **census**, not a behaviour audit. Numeric type IDs
are authoritative; community names are leads only. POC state is a read-only observation of
`84c3e10` (uncommitted POC batch not inspected).

## 1. Placement census (35 / 43 / 12 records, none off-map)

| Type | Param(s) | MGHZ1 | MGHZ2 | MGHZ3 | Category | Status | Canonical research | POC |
|---|---|---:|---:|---:|---|---|---|---|
| `$09` | `$00` | 0 | 6 | 0 | ring | reused | thz1 object-09 | yes |
| `$10` | `$01/$02/$06` | 3 | 3 | 0 | monitor | reused | object-10 | yes |
| `$10` | `$04` Rocket Shoes | 1 | 1 | 0 | footwear | reused, needs data | powerup-shoes | reward missing |
| `$18` | `$00` sign | 1 | 1 | 0 | support | reused | object-18 | yes |
| `$1B` | `$00` | 3 | 4 | 0 | hazard | reused | platform-spike | yes |
| `$21` | `$01..$16`, flags `$10`, aux `$7C/$8E` | 6 | 9 | 0 | enemy | **new art, reused runtime** | object-21 | states 3/4 only |
| `$24` | `$00/$01`, aux `$A0/$A0` | 8 | 4 | 0 | enemy candidate | **new, audit** | none | absent |
| `$28` | `$83` | 7 | 7 | 11 | platform | reused | isometric-platform (MGHZ art noted) | yes (GPZ) |
| `$28` | `$89` / `$05` / `$0A` | 1/3/0 | 0/3/2 | 0 | platform | reused | platform-spike, isometric | yes |
| `$2E` | `$00`, aux `$72/$13|$1B` | 1 | 1 | 0 | hazard/effect candidate | **new, audit** | none | absent |
| `$2F` | `$00`, aux `$AC/$AC` | 1 | 2 | 0 | footwear (Spring Shoes) | reused, needs data | powerup-shoes | absent |
| `$56` | `$00` | 0 | 0 | 1 | boss | **new** | none | absent |

Full per-record table (index, ROM offset, raw bytes, flags, aux, X/Y, anchor cell/block, status) is
in the JSON. Notable: MGHZ3 contains no ring, monitor or sign (11 platforms + boss only, a diagonal
staircase of `$83` platforms at 64 px steps plus a horizontal row); MGHZ1 has no `$09`.
All `$21` records have flags `$10` (see §3). Coordinates are preserved exactly.

**Six-zone reuse.** `$24`, `$2E`, `$56` (and dynamic children `$57`, `$58`, and breakable fragments
`$07`) appear in no other zone: researching them buys MGHZ only. `$21` is shared with THZ (26
placements) and `$2F` with SEZ (16), so their research pays beyond MGHZ.

## 2. Footwear

Placements (verified against the accepted `powerup-shoes.json`):

| Act | Item | World | Ground | Neighbours (within 256×160) |
|---|---|---|---|---|
| MGHZ1 | Rocket monitor `$10/$04` | (1312,110) | surface-1 block 18 px below anchor cell | `$28` (−176,+130), `$2F` (+240,+128) |
| MGHZ1 | Spring Shoes `$2F` | (1552,238) | surface 1 | monitor `$10` (−240,−128), `$21` (+192,0) |
| MGHZ2 | Rocket monitor `$10/$04` | (48,878) | bottom-left corner, start is (112,558) | `$2E` (+184,+30) |
| MGHZ2 | Spring Shoes | (2592,174) | surface 1 | monitor `$10/$02` (+80,+160) |
| MGHZ2 | Spring Shoes | (3760,494) | surface 1 | `$21` (−192,+32) |

**Route assessment (inference from decoded placement geometry, no gameplay observation):**
MGHZ1 x≈1300–1560 is the best canonical test route: both footwear types sit within 240 px of each
other on one stretch (monitor above, shoes below), so one short segment exercises Rocket pickup,
Rocket flight over `$28/$83` platforms and the Spring Shoes. MGHZ2's Rocket monitor is a quick
first-minute pickup (320 px below the start) but has no Spring Shoes near it. Nothing in the
placements shows geometry built specifically around the footwear; Rocket flight additionally has
ceiling-spike (`$3E/$3F`, 25 cells) and oil (`$1B`) terrain in MGHZ2, which must be audited first.

## 3. Ordinary enemies and hazards

| Type | Class | Mapping (entry → table → frames) | Art / palette | Visible frames | Extents |
|---|---|---|---|---|---|
| `$21` | **2 — new art, reused runtime** | `$3C042` → `$911B` (`$3D11B`), 3 frames | bases `$7C` (normal) / `$8E` (remapped, bit4); VRAM loads `$25CD0` ×2; sprite palette `$09` | 1, 2 (+ empty 0); both orientations canonical | 11×26 |
| `$24` | **3 — new runtime** | `$3C048` → `$9169` (`$3D169`), 4 frames | base `$A0`, 12 tiles from `$25EE0`; palette `$09` | 1, 2, 3 (unmirrored only) | 4×11 |
| `$2E` | **3 — new runtime** | `$3C05C` → `$924C` (`$3D24C`), 5 frames | base `$72`, 10 tiles from `$26780`; palette `$09` | 1..4 | 0×0 (no contact box) |

* **`$21`:** identical ROM state table (`$0C:$B1C4`, 7 states) and callbacks as THZ. MGHZ differs in
  art and in placement flags `$10`, which makes the original initialiser clear `+$04` bit 4, set latch
  `+$3F = 1` and request **state 5** (frames use the normal base while walking left, `vx = −$0080`;
  states 5/6 were "not THZ1-reachable" in the old audit). The original callbacks were executed on the
  MGHZ layout for all 15 records (`controlled_patrol_traces`): the patrol reverses at `parameter·16` px
  (first reversal at update 35…707 depending on span), alternating states 5↔6. Remaining work:
  confirm states 5/6 art facing, vertical settling on MGHZ ledges, spring-top contact is unchanged.
* **`$24`:** 4 states. Callbacks `$B49A` (sleep/trigger: player |dx|<`$30` and |player vx|<`$100` →
  state 2), `$B4D1` (vx `+$80` for parameter 0, `−$80` otherwise), `$B4F0` (move, contact, delete).
  Placed in opposite-direction pairs at Y 48/112. Behaviour source-read only.
* **`$2E`:** one per act; spawns three `$2E` children (parameters 1/2/3) and deletes through the
  generic `$034A`. Zero extents: not a contact enemy. Aux1 `$13/$1B` is not a mirror base.
  Community label "oil splash" is an unverified lead.
* Forced mirrors (`bit4=1`) of `$24`/`$2E` exist only as diagnostics and are marked **not approved**.

## 4. MGHZ3 boss reconnaissance (type `$56`)

* Placement record `$713DB`, `56 C5 0D 20 02 00 00 00 00` → **(3269,288)**, inside the 3840×768 map.
* State table `$1E:$A4C4` (file `$7A4C4`), **13 states**: shared boss-framework scripts for 0,1,2,4,5
  (same ROM scripts as the THZ boss table, e.g. defeat script `$95CC` → `$9A1E/$9A29`), own states
  3, 6–12 (frames 1–6). Mapping `$9861` (16 frames, shared with children), no mirrors.
* Init (state 3, `$A576`): dynamic-art selector `$16` → 64 tiles to VRAM `$05C0` (ROM `$17680`) + 12 tiles
  to `$0DC0` (ROM `$26BA0`), sprite palette `$0F` (`$D494` bit 5, `$D495 = 15`), HUD allocator `$81A6`
  (type `$12`), health field `+$26 = 10`.
* Children: `$57` (params 0/1, spawned by states 8/9) → `$58` (params 0/1); shared `$34` explosions,
  `$0A` sparkle chain, `$0F` smoke, `$12` HUD.
* Arena/camera: shared tables by `zone + $D4A5`. State 1 trigger (strict) |dx|<160, |dy|<**304**;
  state 2 camera-target offsets (−208, −32) → nominal target (3061,256) (the THZ rule would stop at
  3060); header limits x max 3584, bottom 528. Effect 14 must pause (`$D44E`).
* Completion: no sign; shared defeat chain expected to converge on `$0A/$0F` and player state `$20`,
  but **unverified for MGHZ3** — do not copy THZ/GPZ constants.
* Estimated size: smaller than GPZ3 (13 states, one child chain of two types), larger than THZ3's
  support work; a bounded task of its own.

## 5. PNG approval package (James review required)

`build/mghz-approval/` (git-ignored; regenerate as in the foundation audit): `terrain-tiles`,
`terrain-blocks`, `terrain-special-surfaces`, `terrain-context-mghz{1,2,3}`, `map-mghz{1,2,3}`,
`animated-terrain`, `type-21`, `type-24`, `type-2e`, `type-2f` (Spring Shoes), `type-28` (MGHZ
platform art), `type-56` (boss + children). Boards show raw tiles, palette-correct frames, SAT
pieces, orientation(s), anchor and a canonical terrain composite. **Approved by James 2026-10-04 (foundation checkpoint), including the flat `$A0` oil presentation and the animated scenery:** all of them
(manifest `art-approval.json`). Mirrors are runtime-
canonical only for `$21`; all other bit4=1 images are forced diagnostics and not candidates.

## 6. Proposed POC decomposition

| Package | Content | Research prerequisite | Complexity |
|---|---|---|---|
| **1. Terrain + shared mechanics** | MGHZ1–3 registration (generic act table, 4095-cell ceiling), terrain/art/palettes, rings (new VRAM dest), springs, `$19`, twist variants 2/3, breakable `$0D`, `$1B`/`$26`-less objects, `$28` platforms, monitors, sign | none blocking; breakable fragment art (small) | medium |
| **1a. Level effects** | CRAM cycles (2, 3), tile strip (14), ring animation | none | small |
| **R1. Research: surface `$1B` oil + ceiling spikes** | bounded audits — **done**, `docs/mghz-surface-1b-ceiling-spikes-audit.md` | before package 1 claims fidelity for those cells | medium |
| **2. `$21` MGHZ variant** | art + states 5/6 | small controlled audit of facing/settling | small |
| **3. New runtimes** | `$24`, `$2E` | audit each (≈4 states) | medium |
| **4. Footwear** | Rocket (`$11`) + Spring Shoes (`$2F`) on MGHZ1 x≈1300–1560 | none (researched) | medium |
| **5. MGHZ3 boss** | `$56/$57/$58`, arena, completion | dedicated boss audit incl. completion | large |

Recommended order: R1 → 1 (+1a) → 2 → 4 → 3 → 5. MGHZ3 can ship as a non-boss act after package 1
(skip `$56`, as GPZ3 did). Blockers: none for data extraction; fidelity claims for oil and ceiling
spikes wait on R1; art waits on PNG approval.

## 7. AGENTS candidate updates (do not apply here)

- MGHZ is zone index 3: 128×32 / 128×32 / 120×24; starts (78,192) / (112,558) / (110,160); cameras
  (0,80) / (0,447) / (0,48); MGHZ1/2 have the unloaded 4096th cell. Manifest
  `data/rom-cache/mghz/implementation-manifest.json`, census `object-census.json`.
- MGHZ mapping table `$14:$8000` is aligned, so table-relative and bank-relative formulas agree by
  accident; always use the bank-relative rule (Aqua/EEZ tables in bank `$14` are not aligned).
- MGHZ new terrain mechanics: surface `$1B` sinking (block `$A0`, `+$24` bit 1, `$D3BC`) and ceiling
  spikes (`$3E/$3F`, hurt at `$74E7`); level effects 2/3/14 from the ring-art descriptor.
- `$21` in MGHZ uses placement flags `$10` (states 5/6, aux `$7C/$8E`); `$24`, `$2E`, `$56/$57/$58` are
  MGHZ-only; boss framework tables are zone-indexed (MGHZ trigger 160×304, camera offset (−208,−32)).
- Zone-3 sign prize table is `$A962` (odd zones); diagonal springs use −5.5; twist variants 2/3.

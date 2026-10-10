# Five Special Stages — canonical audit report (for Manager review)

Branch `research/special-stages-canonical` from Research `main` `c4c389c28fe686713d9371fb925f60eb4014191c`. Europe v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. Research `main` is **not** merged. The POC was not touched.

## Commit chain

`SS-A1 foundation` -> `SS-A2 traversal` -> `SS-A3 powerups` -> `SS-A4 goal ring` -> `SS-A5 progression/closure` (see `git log`).

## What the ROM says (headline facts)

1. **Five stages = ROM zones 8..12**, one act each. Order is fixed 1..5 (`$187B`: zone = 8 + consecutive set bits of `$D2CC` from bit 0). Zone 7 is the Game Over screen, not a stage.
2. **Entry** is the hundredth ring (`$3138` BCD wrap or the +10-ring monitor `$4AC0`), always granting +1 life, then `$178F` gates on Sonic only, zone < 6 and `$D2CC & $1F != $1F`. Timer becomes a 59-second countdown; power-ups, rings and the act timer are lost.
3. **Exit** (success or failure) always returns to the *next act*; failure costs no life and has no retry; the stage is re-offered at the next entry. Canonical quirk: from act index 2 the return loads act index 3 = next zone's act 0 data under the old zone (the next zone's first act is then played twice).
4. **Goal ring** = mapped type `$31`; its placement parameter is the stage's completion bit. Collection: contact box dx +-16, dy -16..+24; sets `D2CC` bit, +1 continue, time-bonus value, `D294` bit 6. No player state change; success beats a simultaneous failure flag.
5. **No Special-Stage-specific terrain code**: every surface uses an existing handler. **Tubes are the final-zone transport (surface `$13`, blocks `$74..$82`, player state `$21`) unchanged**; router proven zone-independent (76,800 original-handler checks over zones 8..12).
6. **Only two stage-specific behavior differences exist**: Rocket Shoes last 6000 updates with no pickup sound in zone 8 (300 elsewhere), and the death path in zones >= 8 sets stage failure instead of life loss. The clock monitor (parameter 5) only matters inside a stage (`$D3C4 = 11`: timer frozen for 11 one-second ticks).
7. No enemies, signs, `$09` rings or hazard objects exist in any stage.

## Stage metadata

| Stage | Zone | Cells / pixels | Start / camera | Limits (L/R/T/B) | Terrain rings | Objects |
|---|---|---|---|---|---|---|
| SS1 | 8 | 512x8 / 16384x256 | (111,118) / (0,15) | 0/16128/8/16 | 144 | `$10/4`, `$31/1` |
| SS2 | 9 | 24x64 / 768x2048 | (111,1838) / (0,1727) | 0/512/8/1808 | 26 | `$10/5`, `$2F` x7, `$31/2` |
| SS3 | 10 | 128x24 / 4096x768 | (143,622) / (31,526) | 0/3840/8/528 | 0 | `$10/6` x7, `$31/4` |
| SS4 | 11 | 256x16 / 8192x512 | (142,366) / (30,254) | 0/7936/8/272 | 0 | `$10/4` x5, `$10/5`, `$26` x5, `$31/8` |
| SS5 | 12 | 48x32 / 1536x1024 | (143,878) / (31,768) | 0/1280/8/784 | 15 | `$10/5` x3, `$31/16` |

Palettes: SS1/2/4 bg 38 / sp 18; SS3 bg 39 / sp 19; SS5 bg 39 / sp 20. Music `$8F`.

## Shared-versus-new dependency table

| Subsystem | Status | Basis |
|---|---|---|
| Loaders, scheduler, player engine, camera | shared | zone-table driven; no zone branch beyond the list in SS-A1 |
| Terrain surfaces `$00/$02/$03/$07/$09/$0A/$0C/$0D/$14/$16/$1D` | shared | same handlers; collision headers global |
| Surface `$01` | shared, **inert outside zone 5** | `$6A5D` |
| Tubes / state `$21` / router | shared (final zone) | 76,800 zone-byte checks + natural traces |
| Rocket Shoes `$10/4` | shared + **zone-8 override** | `$4AEE/$4787` |
| Clock monitor `$10/5` | **new here** (code global, only SS timer reads it) | `$4B02`, `$2826` |
| Invincibility monitor `$10/6` | shared | object-10 contract |
| Spring Shoes `$2F`, springs `$26`, terrain springs | shared | zone-sweep + traces |
| Death/failure in stages | **stage-specific rule** (`$49A0`, `$2846`) | source-traced |
| Goal ring `$31`, results card, tally, continue/emerald reward | **new** | SS-A4/A5 |
| Terrain art (`$64000`, `$65590`), per-stage ring/object art `$D40` streams, results cards | **new art** | boards PENDING |

## Tests (all pass on this branch)

`tests/test_ss_foundation.py` (5), `test_ss_flow_traces.py` (4), `test_ss_traversal.py` (4), `test_ss_powerups.py` (4), `test_ss_goal_ring.py` (4), `test_ss_natural.py` (3), `test_ss_progression.py` (3). Each regenerates its cache and compares byte-for-byte.

## Natural completion / failure coverage

See `docs/special-stages-goal-ring-audit.md` section 6 and `data/rom-cache/special-stages/natural-completions.json`. Every stage has a verified idle-timeout failure and a pit-death failure route returning to the next act. Natural input-only completions that were found and replay-verified are recorded per stage; stages without one are explicitly marked unresolved, not simulated.

## Visual boards needing James's approval (PENDING)

`build/ss-approval/` (ignored), index `data/rom-cache/special-stages/art-approval.json`: five maps (`map-ss1-part1..4`, `map-ss2`, `map-ss3`, `map-ss4-part1..2`, `map-ss5`), `terrain-outdoor`, `terrain-interior`, `objects-new` (goal ring, five colourways), `monitors-emulated` (parameters 4/5/6), `goal-ring-in-situ`, `results`. Pixel-identical `$2F/$26` art is deduplicated.

## Unresolved

- Whether the act-index-3 aliasing should be reproduced in the POC (canonical) or adapted.
- Names for sounds `$8A/$86/$B5/$F8/$8F`; purpose of seven invincibility monitors in SS3.
- Input-only natural completions for any stage not marked completed.
- Sound/PSG and exact mid-line timing are not modelled by the harness; all traces are approximate-harness evidence.
- Visual approval.

## Proposed POC rollout

1. **SS-P1 foundation:** stage rooms, importer for the five caches, entry gate/selector, timer countdown, results/return to act+1, completion bits, `$31` ring with the contact box and success/failure ordering (reuse accepted shared player/terrain systems).
2. **SS-P2 SS1 + SS2:** Rocket Shoes 6000-update override; Spring Shoes climb; clock monitor.
3. **SS-P3 SS3 + SS5:** reuse the accepted final-zone tube/transport implementation under the stage zone bytes (no new tube code).
4. **SS-P4 SS4:** springs, crumble, breakable, Rocket Shoes x5.
5. **SS-P5 presentation:** boards-approved art, results card, widescreen adapters (viewport constants: camera lead `$78` is CENTER-relative; everything else WORLD).

AGENTS candidate updates: add the Special Stage zone 8..12 indexing and entry/exit contract, the act-index-3 quirk, the two stage-specific overrides, the `D2CC`/`D2C3` reward semantics, and that tubes reuse EEZ transport unchanged.

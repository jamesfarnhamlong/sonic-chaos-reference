# Special Stages SS-A1 — indexing, entry/exit contract and foundation

Unmerged research on `research/special-stages-canonical`, base Research `main` `c4c389c`. Europe v1.2, SHA-256 `eabc8db5…ee607`.
Evidence labels: **BYTE-VERIFIED** (assembly read and executed), **DECODED**, **EMULATED** (whole-game, approximate SMS harness, `tools/ss_rig.py`).
Machine package: `data/rom-cache/special-stages/{implementation-manifest,object-census,flow-traces}.json`; tools `ss_foundation.py`, `ss_flow_traces.py`, `ss_rig.py`, `ss_maps.py`.

## 1. Number, indexing, order

There are **five** Special Stages: ROM zones **8..12**, one act each (all three act slots point at the same 22-byte header record). Zone 7 (one type `$1F` object, 256x8 map) is *not* a Special Stage: `$187B` can never select it.

Selection (`$187B`, BYTE-VERIFIED + executed in tests): `$D296 := $D297` (saved zone), then `$D297 := 8 + (count of consecutive set bits of $D2CC from bit 0, max 4)`. `$D2CC` bits 0..4 are the per-stage completion bits (SS1=1, SS2=2, SS3=4, SS4=8, SS5=16). Order is therefore fixed: the lowest *uncleared-in-sequence* stage is always next. Bit 5 (`$20`) is set by a different object (bank `$1E:$BB61`, final-zone chain, A5).

## 2. Entry conditions

The only code that enters a stage is `$178F` (BYTE-VERIFIED, executed against all combinations in `tests/test_ss_foundation.py`). It returns without effect unless **all** hold: player character `$D2C8 == 1` (Sonic), current zone `$D297 < 6`, `$D2CC & $1F != $1F`. It then sets `$D294 := $88`, `$D2CD := 1`, timer-run flag `$D2BE := 0`.

Callers: ring counter `$3138` (BCD `$D29A+1`; **wrap to `$00` = 100 rings**) and the +10-ring monitor reward `$4AC0` (`$D29A += $10`; entering if the BCD sum wrapped). Both first run `$3104`: **+1 life** (BCD cap 99) with sound `$A9`, *even if the gate then refuses*. The ring counter is left at 00. There is no act-number check: entry is possible in act index 2 and in zone 5.

Transition (main loop `$1333`, `$D294` bit7 -> `$1762`, bit3 -> `$17B0`): sound `$8A`, 30 frames, clear `$1CEB`, palette-fade flags, 150 frames, then `$187B`, loader `$4FCE/$2934` (zero `$D15E..$D28F` and `$D300..$DBBF`), HUD, timer `$D2BF:$D2C0 := $0059` counting down, music (`$189B`), palette (`$794F`), camera init, timer-run `$D2BE := $FF`. EMULATED: the zone byte changes at frame 180, the stage is playable at frame 242.

## 3. State preserved / reset on entry

| Preserved | Reset / replaced |
|---|---|
| lives (+1), score `$D29D..F`, completion bits `$D2CC`, continues `$D2C3`, saved zone `$D296`, act `$D298`, character | rings -> 0; all object slots, player slot, power-up selector `$D532`, power timers, boss flags (zeroed `$D300..$DBBF`); camera/limits/layout; elapsed-time timer replaced by the 0:59 countdown |

Hence an active Rocket/Spring Shoes, invincibility, or the act timer is **lost** on entry and is not restored on return.

## 4. Return destination (success and failure share it)

Every exit (success `$D294` bit6 -> `$183F`; failure bit5 -> `$1815`) ends at `$1869`: `$D294 := 0`, `$D297 := $D296`, `$D293 |= $20`. That flag is the ordinary **act-clear** flag, so `$14AE` runs: results `$32F9` (special-stage card because `$D2CD != 0`), tally, then **`$D298 += 1`** and a normal level load. EMULATED whole-game traces (`flow-traces.json`): success, death and timeout all land on zone 0 act 1 (from zone 0 act 0), with lives unchanged (4); only success sets the emerald bit and +1 continue. **Failure costs nothing and has no retry.** The interrupted act's remaining content is skipped.

**Canonical quirk:** entered from act index 2 (including boss acts and zone 5), the return makes `$D298 = 3`. Header/start/palette/art/object tables are adjacent, so act index 3 *is* the next zone's act 0 data under the old zone number. EMULATED: zone 0 act 3 loads at player (110,384) (the GPZ1 start), zone 1 act 3 at (110,718) (SEZ1 start), zone 5 act 3 at (96,142) (zone-7 start). Clearing that act uses the `D298 >= 2` bit4 path, i.e. the next zone's first act is played twice. Decision for POC: reproduce, or adapt as a labelled QoL deviation — not decided here.

## 5. Stage metadata (DECODED, loaders executed)

| Stage | Zone | Cells | Pixels | Player start | Camera start | Limits (camera) | Terrain rings | Mapped objects | Palettes |
|---|---|---|---|---|---|---|---|---|---|
| SS1 | 8 | 512x8 | 16384x256 | (111,118) | (0,15) | L 0 / R 16128 / T 8 / B 16 | 144 | 2 | bg 38 / sp 18 |
| SS2 | 9 | 24x64 | 768x2048 | (111,1838) | (0,1727) | L 0 / R 512 / T 8 / B 1808 | 26 | 9 | bg 38 / sp 18 |
| SS3 | 10 | 128x24 | 4096x768 | (143,622) | (31,526) | L 0 / R 3840 / T 8 / B 528 | 0 | 8 | bg 39 / sp 19 |
| SS4 | 11 | 256x16 | 8192x512 | (142,366) | (30,254) | L 0 / R 7936 / T 8 / B 272 | 0 | 12 | bg 38 / sp 18 |
| SS5 | 12 | 48x32 | 1536x1024 | (143,878) | (31,768) | L 0 / R 1280 / T 8 / B 784 | 15 | 4 | bg 39 / sp 20 |

All maps load with the shared decoder; SS1 and SS4 encode a 4096th cell the 4095-cell loader never writes (preserved). No `$09` rings exist in any stage. Block mapping tables: bank `$1B` at `$8000` (SS1/2/4) and `$8F60` (SS3/5); the bank-relative pointer rule holds (0 mismatches in the original-consumer check).

## 6. Objects (DECODED + original placement creator)

| Stage | Census (type/param) |
|---|---|
| SS1 | `$10/4` Rocket Shoes monitor x1 (under the start), `$31/1` goal ring |
| SS2 | `$10/5` x1, `$2F/0` Spring Shoes x7, `$31/2` |
| SS3 | `$10/6` x7, `$31/4` |
| SS4 | `$10/4` x5, `$10/5` x1, `$26` springs x5 (params 0/1), `$31/8` |
| SS5 | `$10/5` x3, `$31/16` |

The large ring is type `$31` whose placement **parameter is the stage's completion bit** (source of the `$D2CC` write). Monitor parameter meanings are closed in SS-A3.

## 7. One loader, thin dispatch

All five stages use the same loaders (`$4E57`, `$4FDC`, `$4DAD`, placement creator, scheduler, player engine). Static scan of every read of `$D297` in the ROM finds only these stage-aware sites: `$187B` (select), `$178F`/`$4A..` (entry), death `$49A0` (zone >= 8 -> stage failure), Rocket Shoes duration (`$4AEE`, `$4787`: zone **8** only), plus zone-indexed *tables* (start, header, object list, art, palette, music). Music is `$8F` for all five. No per-stage code branch exists beyond SS1's Rocket Shoes override.

## 8. Graphics: shared vs new (`graphics_sharing` in the manifest)

Primary terrain stream: **new** `$64000` (SS1/2/4, outdoor) and **new** `$65590` (SS3/5, pipe interior). A 0x200-byte supplemental stream (`$23340`) is shared with 21 ordinary acts; SS2/SS4 also load shared streams `$26840`/`$26030` (grass/ordinary ground); every stage has its own `$D40`-byte supplemental stream (`$3A51A…`). Boards for the new compositions are produced in SS-A5 for James.

## 9. Not covered here

Terrain/tube mechanics (SS-A2), power-up overrides (SS-A3), ring/failure details (SS-A4), score/continue/emerald progression (SS-A5), visual approval.

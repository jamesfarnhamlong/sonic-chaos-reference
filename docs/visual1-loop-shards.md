# VISUAL-1: THZ1 loop frames and THZ2 breakable-terrain shards

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified, never committed).
Base: VISUAL-0 `ce298af87341d4cce2917461ef4c1b3137f45c91`. The POC (accepted `poc/opening-1-cinematic@1175afa52a4ac2044e9c61b03ba0b7c1656ed817`) was **parsed read-only**; no gameplay, asset or runtime file was changed. No ROM bytes, no original pixels and no audio are committed (generated images stay in the ignored `build/visual1/`).

Machine-readable results

| File | Content |
|---|---|
| `data/rom-cache/visual1/shards-thz2.json` | Part B: static decode, THZ2 corridor trace (6 breaks, 21 shards), controls, per-zone floor-path fixtures, POC comparison |
| `data/rom-cache/visual1/loops-thz1.json` | Part A: static decode, 3 natural + 4 controlled scenarios, speed sweeps, POC comparison |
| `data/rom-cache/visual1/loops-natural-search.json` | the 120-seed natural-entry search (every loop entry seen) |
| `data/visual1/shard-contract.json`, `data/visual1/loop-contract.json` | implementation contracts (derived from the two caches; no POC change implied) |

Tools: `tools/visual1_shards.py`, `tools/visual1_loops.py`. Tests: `tests/test_visual1_shards.py` (22 ROM-free + 5 ROM-backed), `tests/test_visual1_loops.py` (20 ROM-free + 5 ROM-backed).

Scope notes carried from the Manager: the THZ2 bottom-left corridor (six block `$9C` cells, extra-life monitor at (64,718)) is the **primary** breakable fixture. The THZ1 `$47` ten-ring-box puff and rising icon (VISUAL-0 B1/B2) is a **separate, lower-priority backlog item** and is used here only as a contrast (section B6). VISUAL-0's `$47` data are not an implementation contract for destructible terrain.

## 0. Evidence classes

* **DECODED DATA**: tables read from the ROM. **BYTE-VERIFIED ASSEMBLY**: routines disassembled and compared with the exact expected instruction text (the tools raise if the ROM differs).
* **EMULATED ORIGINAL FRAME**: the unmodified ROM running in `tools/sms_frame_harness.py` (Z80 core, approximate VDP and timing); objects, SAT, name table, mailbox and RAM are read back. **NATURAL** = the real THZ1 start record and a seeded pad script only. **CONTROLLED** = the start record (position only) rewritten in a private in-memory ROM copy; and/or RAM injection, stated per case.
* **CLOSED-FORM MODEL**: a Python re-implementation of the ROM arithmetic that must reproduce every emulated per-tick value bit for bit.
* **POC SOURCE (READ-ONLY)**. **UNRESOLVED** is stated, never guessed.

"Tick" = one player update (`$361D`) followed by one object pass (`$5DD1`). It is the logic time unit. Harness video frames are recorded beside it but are approximate: in the corridor run 32 of 183 main-loop iterations returned early (`$D15E` bit 6 set, no player and no object pass), so a tick is not one video frame (ROM slow-down behaviour as emulated; hardware-unverified).

## 1. Verdicts

| # | Finding | Class |
|---|---|---|
| A1 | **THZ1's two loops are entered naturally**: loop 1 gate (74,13) = world X 2368 and loop 2 gate (90,16) = X 2880, by the rule *current foot block `$52`, previous `$51`, plane 0, floor flag* -> `$3EAB` -> state `$0C`. From the real start record, 9 of 120 seeded pad scripts entered a loop (29 entries); seeds 13, 6, 97 are replayed here. No speed gate exists | NATURAL + ASM |
| A2 | State `$0D` (leftward, plane 1, blocks `$50/$51` after `$52`) was entered only in the CONTROLLED run (RIGHT through loop 1, then LEFT). No natural `$0D` or `$13` entry exists in the 120 seeds; `$13` needs previous block `$57`, and THZ1 has no `$57` cell | CONTROLLED; `$13` N/A in THZ1 |
| A3 | Route movement is `p24 += speed; p = p24>>8; position = anchor + table[p]; p<$90: speed -= 10 (borrow = bailout); else plane flips and speed += 12; exit at p >= $180`. The closed-form model reproduces **every observed tick of all 16 traversals** (progress mismatches 0). Minimum completing entry speed is `$0356` (3.336 px/update): `$0355` bails out at update 86, `$0356` completes in 183 updates; 4.0 px/update takes 111 | ASM + EMULATED + MODEL |
| A4 | **Frame selection**: every 6-update record `$903D` sets `frame := pair[p // 13][0]` (or `[1]` when `[0]` is already shown). 24 pairs: three walk pairs, then 21 rotation pairs `$2A..$35` and `$40..$5D` (42 frames), then walk pairs again from progress 312. All 262 selector calls (19-27 per full traversal) reproduce the rule (0 violations) | ASM + EMULATED |
| A5 | **Rolling alternative**: whenever `+$03` bit 1 is set at selector time `$903D` tail-jumps to `$8F76` (ball frames `$25..$29`, 20-step counter `$D52F`, duration from `|X speed hi|`: 10/8/6/5/4/3/2...). Observed in a natural run (entry 3.44 px, rolling, exit state `$09`) and in a spin-dash roll (entry 6.2 px) | NATURAL + CONTROLLED |
| A6 | **Facing/mirroring**: the route never writes `+$04` bit 4; `$0C` runs unmirrored, `$0D` runs with bit 4 set and the same frame numbers drawn mirrored (`x = anchor - rel_x - 8`). The composition rule reproduces the real SAT in **1,368/1,368 loop video frames** (128 of them mirrored), 0 matches only under the wrong convention | EMULATED |
| A7 | The accepted POC uses its **legacy loop adapter**: movement tables equal the ROM (395 entries each), but presentation is a generic rotation of the run/spin sprite; none of the 42 ROM rotation frames exists in the POC, entry uses a bottom-crossing window and `|hspeed| >= 0.25`, and speeds are capped at 8 px | POC SOURCE |
| B1 | The six THZ2 `$9C` cells are reachable only by **side contact** (every cell has solid terrain above; floor path N/A). A natural spin dash from the corridor shaft foot (404,718) broke all six in 34 ticks, passed the type-`$10` monitor at (64,718) and raised the life counter 3 -> 4 | EMULATED (CONTROLLED start) |
| B2 | A break is **one tick**: layout cell -> `$9D`, 4x4 name-table refresh, and **four type-`$07` objects** (parameters 0..3) spawned at the cell's top-left with offsets 4/20; no intermediate frame, no timer. The hole is in the name table in the break's own frame | ASM + EMULATED |
| B3 | Each shard's motion is exactly `vy += $00C0` (saturating at `$0FC0`) **then** `pos += velocity`, starting from tables `$9B75` (Sonic X speed >= 0) or `$9B95` (< 0). 21 shards, 544 per-tick values: 0 model mismatches. Lifetimes are **cull-driven** (23-29 ticks in the corridor run) | ASM + EMULATED + MODEL |
| B4 | **Shards compete for the 16 shared object slots**: the 4th and 5th breaks of the corridor run created only 2 and 3 shards (3 requests silently dropped; no sound for a dropped request) | EMULATED |
| B5 | Each created shard requests `$A3` in the break tick; the mailbox keeps one pending byte, so a break gave **1-2 driver-visible requests** (2 when the tick straddled a vblank); the driver accepted them (priority `0x58`) | EMULATED |
| B6 | The shard **art is not the earlier "common-stream" pair**: the level loader's last step (`$2934` -> `$79F2`) writes a zone-indexed 2-tile stream into VRAM `$0CC0`. The visible 8x8 is the **top** half in SEZ/AQZ/SS and the **bottom** half in THZ/GPZ/MGHZ/EEZ. The POC's SEZ/SS4 shard sprites are RGBA-identical to the overwritten pair (AQZ's by alpha mask: its colours are index-encoded), not the ROM's final art | ASM + EMULATED + POC SOURCE |
| B7 | The accepted POC creates **no shard, no sound and no `$D3B2` effect** for `$0D` in any zone; its only `$A3` and shards belong to the separate type-`$13` crumble path | POC SOURCE |
| B8 | The `$0D` effect shares **no object, sprite, sound or timing** with THZ1 `$47` (type `$0F` puff + type `$11` icon, `$AB`, +10 rings) | ASM |

Explicitly **UNRESOLVED**: section A9 and B9.

---

# Part A: THZ1 loop presentation

## A1. What was run

`tools/visual1_loops.py` records, for every tick, the player's state (`+$01`), requested state (`+$02`), flags `+$03/+$04`, mapping frame `+$06`, record timer `+$07`, position, speed, plane `+$25`, floor flag, route progress `$D39D..$D39F`, current/previous foot block `$D36B/$D497` and cached screen position `$D51A/$D51C`; it hooks the dispatcher `$6C82`, the three entry helpers, both route callbacks, their exit/bailout points and both selectors.

| Class | Scenario | What it shows |
|---|---|---|
| NATURAL | `natural_seed_13` (1,700 frames) | RIGHT-heavy pad script from the real start; both loops, entry 4.0 px/update, 111 ticks each |
| NATURAL | `natural_seed_6` (2,700 frames) | three slow entries (0.50, 0.50, 0.95 px) that **bail out**, a rolling entry (3.44 px) that completes in 153 ticks, a rolling entry at loop 2 (2.31 px) that bails out |
| NATURAL | `natural_seed_97` (1,250 frames) | both loops again |
| CONTROLLED | `hold_right_from_(2100,380)` | RIGHT held from a start 270 px before loop 1: loop 1 then loop 2 |
| CONTROLLED | `right_then_left_into_loop_1` | RIGHT until frame 226, then LEFT: loop 1 (`$0C`) then the leftward `$0D` |
| CONTROLLED | `spin_dash_roll_through_both_loops` | start (2250,430), spin dash, release RIGHT: rolling traversal (6.2 px) |
| CONTROLLED | `roll_started_while_running` | DOWN while running at 4 px: slow rolling entry (2.6 px) that bails out |
| CONTROLLED | four slow starts, and speed injection at the first route callback | entry speed dependence; the exact `$0356` threshold |

The natural search (`--search 0 120`): 120 pad scripts of 10-50 frame runs (RIGHT 55 %, RIGHT+jump 25 %, RIGHT+DOWN 8 %, RIGHT+DOWN+jump 5 %, LEFT 7 %); 54 reached X 2368, 51 reached X 2900, **9 entered a loop** (29 entries, all state `$0C`).

## A2. Entry (source-decoded, then observed)

Source (`$6C82` dispatches on the current foot block `D36B`, table `$6C99`):

| Current block | Handler | Condition | Request |
|---|---|---|---|
| `$52` | `$6CCD` | plane `+$25` = 0, floor flag `+$22` bit 1, previous foot block `D497` = `$51` | `$3EAB` -> **state `$0C`** |
| `$52` | `$6CCD` | same, previous = `$57` | `$3EF7` -> state `$13` (not in THZ1) |
| `$50`, `$51` | `$6CBA` | plane 1, floor flag, previous = `$52` | `$3EE1` -> **state `$0D`** (X += 32 first) |
| `$48..$4F`, `$53..$56` | RET | - | - |

`$3EAB..` also snap `X &= ~31`, `Y := (Y & ~31) + 4` (kept in `+$3A..$3D`), zero the cursor and `POP AF` (the terrain pass ends early). There is **no speed, facing, state or attack test**.

THZ1 layout (decoded): loop 1 spans cells (72..75, 9..13), gate cell (74,13), floor row Y 416, right gate X 2368, left-gate crossing X 2367 (cell 73 -> 74 boundary from the right); loop 2 spans (88..91, 12..16), gate (90,16), X 2880/2879, floor row Y 512. No `$57` cell exists.

Observed entries (all 10 loop-1 entries: X 2368-2370, Y 419-420; 5 loop-2 entries: X 2880-2882, Y 515-516; `prev $51 -> cur $52`, plane 0):

| Scenario | State | Ticks | Entry X,Y | Entry speed | Plane | Outcome | After |
|---|---|---:|---|---|---|---|---|
| natural 13 | `$0C` | 111 | 2369,420 | 1024 (4.00) | 0->1 | exit | `$06` vx 1016 |
| natural 13 | `$0C` | 111 | 2881,516 | 1024 (4.00) | 0->1 | exit | `$06` vx 1016 |
| natural 6 | `$0C` | 13 | 2368,420 | 128 (0.50) | 0 | bailout | `$1D` |
| natural 6 | `$0C` | 13 | 2368,420 | 128 (0.50) | 0 | bailout | `$1D` |
| natural 6 | `$0C` | 25 | 2368,420 | 242 (0.95) | 0 | bailout | `$1D` |
| natural 6 | `$0C` | 153 | 2370,419 | 880 (3.44) | 0->1 | exit (rolling) | `$09` vx 996 |
| natural 6 | `$0C` | 60 | 2880,516 | 592 (2.31) | 0 | bailout (rolling) | `$1D` |
| natural 97 | `$0C` | 111, 111 | 2369,420 / 2881,516 | 1024 | 0->1 | exit | `$06` |
| controlled hold-right | `$0C` | 111, 111 | 2370,419 / 2881,516 | 1024 | 0->1 | exit | `$06` |
| controlled right-then-left | `$0C` | 111 | 2370,419 | 1024 | 0->1 | exit | `$06` |
| controlled right-then-left | **`$0D`** | 128 | 2366,420 | -944 (-3.69) | 1->0 | exit | `$06` vx -1016 |
| controlled spin dash | `$0C` | 65, 65 | 2369,420 / 2882,515 | 1592 / 1576 (6.2) | 0->1 | exit (rolling) | `$09` vx 1764 |
| controlled roll while running | `$0C` | 67 | 2370,419 | 666 (2.60) | 0 | bailout (rolling) | `$1D` |

Between the loops the plane returns to 0 (observed at tick 299 as the foot crosses blocks `$18/$19` at (2777,522)); the mechanism is not decoded here (A9).

## A3. State transitions and the route per tick

```text
terrain pass (foot-block transition) -> requests $0C/$0D   [tick T, +$02]
tick T+1: state $0C/$0D, record = FF 05 selector $903D + vector $03CB/$03D1 (-> $3C1B / $3DAE), loop
route callback every tick (right):  p24 += X speed;  p = p24 >> 8;  Y = anchorY + Ytab[p];  X = anchorX + Xtab[p]
                                    p <  $90: X speed -= 10   (borrow -> bailout)
                                    p >= $90: plane := 1;  X speed += 12
                                    call $48BC (damage/contact stays live)
                                    p >= $180: request $06 (or $09 if +$03 bit 1); X speed := $D373; $D3A0 := $10
left route ($3DAE): the same on the negated speed; tables $86AE/$8A46 (Y identical, X mirrored); plane := 0 at the midpoint; speed := -$D373
```

Bailout (`$3CC5/$3E74`): current X > anchor X -> X -= 2, else X += 8; then `$4680` requests state `$1D` (falling). Observed in all 5 bailouts: `$1D` lasts 1-23 ticks, the X speed becomes -280 then -256 (Sonic is pushed back about 1 px/update), the Y speed starts at +176 and grows by 48 per tick. Tables are read **before** the exit test, so a fast exit tick can read past index `$180` (the tool hashes 424 entries per axis).

Closed-form model `route_model(vx0, left)` (24-bit cursor, 16-bit speed): reproduces progress at every observed tick of every traversal, the outcome (exit/bailout) and the tick count. Reference traversals (entry speed -> ticks): 1024 -> 111; 880 -> 153; `$0357` -> 180; `$0356` -> 183; `$0355` -> bailout at 86 (progress 143); 1592 -> 65; -944 (left) -> 128. Entry-speed bailouts from rest starts: 512 -> 52 ticks (progress 52); 352 -> 36 (24); 208 -> 21 (8); 128 -> 13 (3).

## A4. Rotation-frame indexing

Table `$906C` (bank `$0C`, type 1; Tails uses `$90D2`): 51 pairs.

| Pair index (p // 13) | Frames | Progress range |
|---|---|---|
| 0, 1, 2 | `$01/$02`, `$03/$04`, `$05/$06` (upright walk) | 0..38 |
| 3..8 | `$2A/$2B`, `$2C/$2D`, `$2E/$2F`, `$30/$31`, `$32/$33`, `$34/$35` | 39..116 |
| 9..23 | `$40/$41` ... `$5C/$5D` | 117..311 |
| 24.. | `$01..$06` again | 312.. |

`$36..$3F` are not in the table (ten frames skipped). The rule at each selector call (once per record, duration set to 6): `frame := pair[index][0]`, except `pair[index][1]` when `pair[index][0]` is the frame already shown.

Observed at 4 px/update (111 ticks, identical in 7 traversals): one record covers 24 px, so each call lands about two pairs later; the shown sequence is `$01 $03 $2A... ` as `1, 3, 42, 46, 48, 50, 64, 66, 68, 70, 72, 76, 78, 82, 86, 88, 92, 5, 3` (records of 6 ticks, last cut by the exit). At lower speed the toggle inside a pair is visible (e.g. the leftward traversal shows `$44`, `$46`, `$50`, `$52` but also `68, 69, 70` in successive records). All 262 selector calls (19 per running traversal, 22 leftward, 26-27 rolling) were each checked against the rule: **0 violations in 16 traversals**.

## A5. Rolling alternative selector

Condition: `+$03` bit 1 (the attack posture bit set by rolling, spin dash, jump) **at the moment `$903D` runs**. Then `$8F76`: counter `$D52F` (+1 per call, wraps at 20) indexes `37 38 39 40 41 38 39 40 37 41 39 40 37 38 41 40 37 38 39 41`; with floor contact the duration is table `$8FE0[|X speed hi|]` (10, 8, 6, 5, 4, 3, 2, 2...) and bit 4 of `+$04` is cleared then set when the X speed high byte is negative; in the air the duration is 3.

Observed: spin-dash roll (entry 1592) -> frames `$25..$29` only, 27 of 27 selector calls took the alternative; natural seed 6 (entry 880) -> 26 of 26; the slow rolling entry shows durations 6,6,6 then 8,8,8 then 10,10 as the speed high byte falls 2 -> 1 -> 0. A rolling exit requests `$09`, a running exit `$06`. Leftward rolling through `$0D` was not observed (A9).

## A6. Facing and sprite mirroring

* `+$04` bit 4 clear = facing right. The route does not touch it; only the rolling selector writes it.
* Observed: bit 4 is clear for all ticks of all `$0C` traversals and set for all 128 ticks of the `$0D` traversal; the frame numbers are the same `$2A..$5D` set in both cases.
* The compositor (verified against the real SAT): piece X = `D51A + rel_x` (clear) or `D51A - rel_x - 8` (set), raw SAT Y = `D51C + rel_y`, tile = the piece's tile offset. `D51A/D51C` are the cached screen position written **before** the player moves (previous position minus current camera). 1,368 of 1,368 loop video frames match (128 with bit 4 set); no frame matched only under the wrong convention. In 144 of 1,655 video frames of the controlled runs the sprite shows the frame held at the end of the previous tick (the sprite list is built before the animation engine runs): a one-tick presentation lag, not a logic difference.
* So the `$0D` loop is the same pre-rotated art drawn mirrored (anchor-centred mirror), not a second set of frames.

## A7. Timing

| Phase | Ticks | Source |
|---|---|---|
| gate -> first route update | 1 (requested state in tick T, state `$0C` from T+1) | EMULATED |
| traversal at 4 px/update | 111 (47 ticks to p = $90 while decelerating, then accelerating to the exit) | EMULATED + MODEL |
| traversal at 3.34 px (minimum) | 183 | EMULATED + MODEL |
| leftward at 3.69 px | 128 | EMULATED |
| rolling at 6.2 px | 65 | EMULATED |
| exit | speed := `$D373` the same tick; the next tick is state `$06`/`$09` | EMULATED |
| bailout | state `$1D` the tick after; 1-23 ticks of `$1D` observed | EMULATED |

Each frame lasts 6 ticks (running) or 6-10 ticks (rolling by speed). The tick-to-video-frame relation is approximate (A0/section 0).

## A8. POC comparison (read-only, accepted `1175afa`)

| Aspect | Original (evidence above) | POC |
|---|---|---|
| Movement tables | `$8000/$8398`, `$86AE/$8A46` | **identical** (395 entries per axis, equal x and y) |
| Cursor/decel/accel | -10 below 144, +12 from 144, exit 384 | same constants, `min(index, 394)` clamp, exit speed capped to 8 px |
| Entry | foot-block transition `$51->$52` / `$52->$50,$51`, plane, floor flag; no speed gate; raw speed | bottom-crossing X window and `bbox_bottom` band, `abs(hspeed) >= 0.25`, `loop = block pair $51,$52` found in the layout, speed capped at 8 px |
| Plane | `+$25` flips at the midpoint | per-loop `chaosLoopPlanes` array |
| Low-speed | bailout rule at borrow, X nudge, state `$1D` | release when the speed goes negative, jump latch set |
| Presentation | `$2A..$5D` frames by `p // 13`, rolling alternative | `image_angle = point_direction(table[i-3], table[i+3])` on the generic run or spin sprite, `image_speed 0.5`, `image_xscale` = direction |
| Frames | 42 rotation frames | none of the 42 exists as a POC resource (walk frames `$01..$06` do) |

The POC's generic rotation is therefore **not original-game evidence** and must not be used as the contract. The state-`$13` route (GPZ) is owned by the core, not the legacy adapter, and is outside THZ1.

## A9. Unresolved (Part A)

* Natural entry into `$0D` was not produced by any of the 120 scripts; `$13` cannot occur in THZ1 (no `$57`).
* Leftward **rolling** traversal (the `$8F76` facing write for a negative speed) is source-decoded only.
* The plane reset to 0 between the loops (blocks `$18/$19` at (2777,522)) and the purpose of `$D3A0 := $10` at exit are not decoded.
* Real-hardware (50 Hz) timing and the harness's early-returning iterations are emulator behaviour; the contact routine `$48BC`, enemies inside loops, camera behaviour and palette effects were not studied.
* Tails (`$90D2`) was not run. Seeds searched: 0..119 only.

---

# Part B: THZ2 breakable terrain (`$0D`, blocks `$9B/$9C` -> `$9D`)

## B1. Fixture

THZ2 layout row 22: `$9C` at cells (4,5,6) and (9,10,11), empty cells (7,8) between, the corridor floor `$01/..` below, solid terrain above (surface 2) and the type-`$10` extra-life monitor (parameter 2) at (64,718). Block `$9C` header flags `$8D` (solid, surface `$0D`), `$9D` flags `$00`. The census of the layouts shows THZ2 has exactly these six `$0D` cells (THZ1 none, THZ3 five).

Primary run (`corridor_report`): the start record is rewritten in memory so the act starts at (404,718), the foot of the shaft; pad: LEFT (face), DOWN, button-1 taps (spin-dash charge), then LEFT. This is CONTROLLED (start position), but everything after is original code and original input. Result: spin-dash roll (state `$10`, X speed -1784..-1652), six side-left breaks, monitor reached (lives 3 -> 4). Four spin-dash variants (1..4 button taps) give the same six breaks and 3 dropped shards.

## B2. The break chain (BYTE-VERIFIED)

```text
terrain handlers (all end in $7898):
  floor   $6B2C: state not in {$0F,$10,$15,$1A}, +$03 bit 1 -> $D3B2 := $10 (written, never read), Y speed := $FBC0 (-4.25), floor flag cleared, +$03 bit 0 set
  right   $72B6: +$03 bit 1, |X speed hi| >= 3; hi < 7 -> X speed += $0040
  left    $72DD: same on the negated high byte; X speed += $FFC0 (faster leftward)
  ceiling $7464: support owner $D3C0 == 0 -> break; owner set -> crush death $4984
$7898: layout cell (D354) := $9D; block mapping of $9D -> name table via $23F9 (4x4, same tick);
       anchor D35C/D35E := sample (D358/D35A) & $FFE0; spawn type 7 with H = 0,1,2,3 via $5E9C
$5E9C: first free of the 16 slots $D540..$D93F (stride $40); none free -> RET, nothing created
```

The side path never touches `$D3B2`. In the corridor the handler was `$72DD` for all six breaks (state `$10` is allowed; only the floor path excludes it).

## B3. Observed corridor timeline (tick = player update; B = break tick)

| Break | Tick B | Cell | Sonic X, speed | Free slots | Shards created / dropped (params) |
|---|---:|---|---|---:|---|
| 1 | 31 | (11,22) | 388, -1784 | 15 | 4 / 0 (0-3) |
| 2 | 35 | (10,22) | 360, -1768 | 11 | 4 / 0 |
| 3 | 40 | (9,22) | 325, -1748 | 7 | 4 / 0 |
| 4 | 54 | (6,22) | 232, -1692 | 2 | **2 / 2** (params 0,1) |
| 5 | 59 | (5,22) | 199, -1672 | 3 | **3 / 1** (params 0,1,2) |
| 6 | 64 | (4,22) | 166, -1652 | 7 | 4 / 0 |

Tick B: the cell and name table change (the new hole is in the name table of the break's own video frame); the 4 requests become objects in slots; each runs state 0 (`FF 06 A3`, record frame 0 for 1 tick, init callback `$9B11`). Tick B+1 onward: record frame 15, callback `$9BB5`. The first shard sprite pixels reached the harness SAT 4 video frames after the break (2 ticks; ticks were 1-2 frames apart here, hardware-unverified).

Exact placement in the THZ2 corridor (cell origin = layout cell x 32; parameters 0..3 = quadrants; all six used the leftward table `$9B95` because Sonic was moving left):

| Cell | Origin | Shard start positions (param 0, 1, 2, 3) |
|---|---|---|
| (11,22) | (352,704) | (356,704) (372,704) (356,724) (372,724) |
| (10,22) | (320,704) | (324,704) (340,704) (324,724) (340,724) |
| (9,22) | (288,704) | (292,704) (308,704) (292,724) (308,724) |
| (6,22) | (192,704) | (196,704) (212,704) (196,724) (212,724) - params 2,3 dropped |
| (5,22) | (160,704) | (164,704) (180,704) (164,724) (180,724) - param 3 dropped |
| (4,22) | (128,704) | (132,704) (148,704) (132,724) (148,724) |

Shard parameter `+$3F` is the quadrant. `$9B11` picks the table by the sign of the player's X speed high byte (`$D517`) when it runs:

| q | offset (x,y) | `$9B75` (X speed >= 0): vx, vy | `$9B95` (X speed < 0): vx, vy |
|---|---|---|---|
| 0 | 4, 0 | -2.0, -4.0 | -0.5, -3.0 |
| 1 | 20, 0 | +0.5, -3.0 | +2.0, -4.0 |
| 2 | 4, 20 | -2.0, -1.0 | -0.5, -2.0 |
| 3 | 20, 20 | +0.5, -2.0 | +2.0, -1.0 |

(8.8 values /256 px per tick.) Position relative to the cell origin after k ticks for the leftward table (integer pixels, k = 0..13): q0 x `4 3 3 2 2 1 1 0 0 -1 -1 -2 -2 -3`, y `0 -3 -4 -5 -5 -4 -3 0 3 6 11 16 22 29`; q1 x `20 22 24 ... 46`, y `0 -4 -6 -8 -9 -9 -9 -7 -5 -3 1 5 10 16`; q2 y `20 18 18 18 19 21 23 27 31 35 41 47 54 62`; q3 y `20 19 20 21 23 26 29 34 39 44 51 58 66 75` (`contract.trajectory_relative_to_cell_origin` has both tables to k = 48 in 8.8). The integrator is **gravity then move**; the Y speed saturates at `$0FC0` (15.75 px/tick) because `$5F84` discards sums >= `$1000` (the first reproducing mismatch of the model was exactly this cap).

Lifetime: `$61E1` (after each update) tests the anchor against the cull map at bank `$1C:$8146` (32 x 32 cells of 16 px, offset -128): values 0/1 on-screen, 2 = flag `+$04` bit 6 (the shard's callback then removes it in the next tick), 3 = removed by the engine. The flagged window is **screen offset outside -32..287 on both axes** (the 256 x 256 box plus 32). In the corridor run: 21 shards, 16 deleted below the view (screen Y >= 288 at the 606 camera), 6 right of it (X >= 288 as the camera ran left), none left; ticks alive 23..29; the floor-path fixtures (static camera) 19..30. A tick count therefore depends on the camera.

## B4. Art (the correction to the earlier "common stream" statement)

Frame 15 is one 8x16 piece at (-4,-16) using tiles `$66/$67`. What those tiles contain is decided by the **last** stream the level loader writes: `$2934` calls `$79F2` at `$295B`; it pages bank `$0E`, selects the stream pointer at `$A3A0 + 2*zone` (zone byte `D297`) and decompresses it with `$24C2` into VRAM `$0CC0`. Each stream holds 2 tiles with **one 8x8 graphic in one half**:

| Zone(s) | Stream CPU | Visible 8x8 | Sprite palette index |
|---|---|---|---|
| THZ (0), zone 6 (zone 7 shares the stream; its palette index is 41) | `$A3C0` | bottom (rows Y-8..Y-1) | 6 |
| GPZ (1) | `$A3F0` | bottom | 7 |
| SEZ (2) | `$A420` | **top** (rows Y-16..Y-9) | 8 |
| MGHZ (3) | `$A448` | bottom | 9 |
| AQZ (4) | `$A478` | top | 10 |
| EEZ (5) | `$A4A0` | bottom | 11 |
| SS1, SS2, SS4 (8, 9, 11) | `$A4D0` | top | 18 |
| SS3, SS5 (10, 12) | `$A4F4` | top | 19 / 20 |

THZ2 shard colours (sprite palette `$06`, palette indices used 3, 4, 7, 10, 11, 12): (255,170,85), (170,85,0), (255,255,255), (85,85,85), (170,170,170), (255,255,85); the sprite palette is the ordinary level sprite palette (CRAM 16..31), index 0 transparent. The static decode equals the live VRAM of every fixture (RGBA hash equal in 10 of 10 emulated zone fixtures). The earlier "static common stream" (a 16-row 8x16 brick, written by the primary level stream at frames 898/899 of the boot, `$66/$67`) is **overwritten at the end of loading** and is never on screen: in SEZ the live pair is the 8x8 piece (top half), `$67` blank. The type-`$13` crumble shards display the same tile pair (SEZ1 emulation: 6 frames, live hash equals the final stream).

## B5. Sound

`FF 06 A3` heads state 0 of every created shard; command `$67D5` writes the byte to `$DE04` twice in a row. A dropped request creates no object and therefore no sound. The driver mailbox holds one pending byte: writes between two vblank interrupts collapse into one request, so each corridor break gave 1-2 driver-visible requests ([2,1,2,1,1,2]); the first break's four writes straddled the vblank (one before line 193, three after). The driver's priority byte for `$A3` is `0x58` (ROM `$09091`); every request was accepted (current priority `0x50`, then `0x58`; equal priority is accepted) and a reissue restarts the effect. This is a numeric request only; no PC waveform is claimed.

## B6. How this differs from THZ1 block `$47`

| | THZ1 `$47` (surface `$16`) | `$9B/$9C` (surface `$0D`) |
|---|---|---|
| Cell | -> `$46` | -> `$9D` |
| Entry | `$6AE3` foot path, `$736B/$7389` side cores -> `$7857` | `$6B2C`, `$72B6`, `$72DD`, `$7464` -> `$7898` |
| Objects | 1 type-`$0F` puff (param `$40`, frames `$07/$08/$09`, 37 updates) + 1 type-`$11` rising icon (frame `$0D`, 33 updates) | 4 type-`$07` shards (frame 15, ballistic, cull-limited lifetime) |
| Sound | `$AB` | `$A3` per shard (collapses to 1-2) |
| Side effects | +10 rings, dynamic tile selector `D3B3 := 1` | none (floor path only: `D3B2 := $10`, Y speed `$FBC0`) |

They share no object, sprite, sound or timing. `$47`'s rising icon must not be used as the contract for destructible terrain.

## B7. Explicit comparison with the accepted POC source

Read-only parse of `1175afa` (`tools/visual1_shards.py --poc`).

| Original behaviour | POC | Status |
|---|---|---|
| Layout cell -> `$9D` | `SCR_chaos_break_block`: `chaosTileIds[i] = 157`, `chaosBrokenCells` push; THZ2/THZ3 terrain objects draw `SPR_chaos_thz2_block_9d` | present |
| Floor/side/ceiling eligibility (`$6B2C/$72B6/$72DD/$7464`) | `SCR_cc_break13_floor/_side`, ceiling branch with crush death: conditions, `vy = -1088`, +/-`$40` nudge match | present |
| **Four type-`$07` shard objects** at cell + (4|20, 0|20) with parameters 0..3 | none: `SCR_chaos_break_block` contains no `instance_create`; there is no type-`$07` object; its own comment says the fragments "are UNRESOLVED and deliberately not presented" | **missing** |
| **Per-shard velocities, gravity `$C0` (cap `$0FC0`), table choice by Sonic's X speed** | absent | **missing** |
| **16-slot pool and silent drops** | absent | **missing** (a faithful port would drop shards when the pool is full; the corridor run lost 3 of 24) |
| **Cull-driven lifetime (-32..287 box)** | absent (nothing to remove) | **missing**; widescreen needs the right bound extended by the extra width |
| **Shard sprite, per zone (top or bottom 8x8 of the zone stream, palette)** | `SPR_chaos_sez_shard`, `SPR_chaos_aqz_shard`, `SPR_chaos_ss4_shard` only; THZ, GPZ, MGHZ and EEZ have none. The three sprites are the **16-row pre-override pair** (SEZ and SS4 RGBA-identical to it; AQZ alpha-mask identical): **not** the ROM's final art, which is an 8x8 in the top half | **wrong art / missing** |
| Sound `$A3` at the break | the only `$A3` is `SCR_chaos_sez_s2.gml:118`, the type-`$13` crumble path; the `$0D` break plays nothing | **missing** |
| `$D3B2 := $10` (floor path) | not modelled (written but never read in the ROM: no visible effect) | immaterial |

Zone by zone (`$0D` cells from the layout census: THZ2 6, THZ3 5, GPZ1 16, GPZ2 13, SEZ1-3 145/100/8, MGHZ1-2 55/52, AQZ1-3 18/13/1, EEZ1-2 1/1, SS4 41; SS1, SS2, SS3, SS5 none; zone 6 acts 1-2 mirror THZ2/THZ3):

* **SEZ**: cell swap only; no shards; shard sprite present but wrong art; type-`$13` shards exist (a different object).
* **MGHZ**: cell swap only; no shard sprite at all (stream `$A448`, bottom 8x8).
* **SS4 (zone 11)**: cell swap only; shard sprite present but is the SEZ pre-override pair under the SS palette (stream `$A4D0`, top 8x8, palette 18). The other four special stages have no `$0D` cell.
* **THZ2/THZ3/GPZ/EEZ/AQZ**: the same; GPZ, EEZ and THZ have no shard sprite, AQZ's is wrong art.

Visible consequences in the accepted POC: the THZ2 corridor shows an empty hole with no debris and no sound, and the pool, trajectory and sound behaviour above are absent.

## B8. Other zones and unsupported cases (emulated vs not)

Floor-path fixtures (controlled start, Sonic dropped in the jump posture onto a `$0D` cell with free air above, `$6B2C` -> `$7898`): SEZ1 (105,7), SEZ2 (95,3), SEZ3 (59,19), MGHZ1 (2,7), MGHZ2 (9,18), AQZ1 (11,7), AQZ2 (71,21), AQZ3 (27,8), EEZ2 (12,14), SS4 (65,7) all create 4 shards with table `$9B75`, 0 model mismatches, art as in the table above. **Not reproduced**: THZ2, THZ3, GPZ1, GPZ2, EEZ1, zone 6 (every `$0D` cell has a non-empty cell above, so the floor path cannot occur there); breaking them is by side contact only (generic controls: walking never breaks; rolling with high byte 3 and 4 breaks with the +/-`$40` nudge; high byte 2 does not; a rightward roll uses table `$9B75`). The ceiling path and a break with the support owner set (crush death) belong to `docs/mghz-m1-windows-followup.md`; SS4 was entered through the level loader, not the special-stage entry flow.

## B9. Unresolved (Part B)

* Object field `+$08`: `$9B11` sets it to `$9C` only for zone 6, act 2 (byte-verified at `$9B64..$9B70`); its effect on the shard was not exercised.
* Side/ceiling-path fixtures in the other zones were not run (the code is shared; the shard behaviour is a pure function of cell, speed sign, pool and camera).
* Hardware timing: shard sprites appear in the harness SAT two ticks after the break; this video-frame number is not hardware-exact. Sound audibility was not rendered.
* Pool occupancy in other acts depends on their objects; the 3 dropped shards are specific to the corridor's 14 occupied slots.

---

## Reproduce and verify

```sh
python tools/visual1_shards.py ROM --output build/visual1 --poc PATH_TO_POC \
    --metadata data/rom-cache/visual1/shards-thz2.json --contract data/visual1/shard-contract.json   # add --check to compare
python tools/visual1_loops.py  ROM --output build/visual1 --poc PATH_TO_POC \
    --metadata data/rom-cache/visual1/loops-thz1.json --contract data/visual1/loop-contract.json     # add --check to compare
python tools/visual1_loops.py ROM --search 0 120                                                       # natural-entry search (not part of --check)
SONIC_CHAOS_ROM=ROM python -m unittest tests.test_visual1_shards tests.test_visual1_loops
```

`SONIC_CHAOS_ROM` overrides the ROM search; `--poc` is optional (without it the POC sections are omitted). Both caches regenerate byte-identically (`--check`); images (strips of the first corridor break and of the loop traversals, shard tile art) are written only to the ignored `build/visual1/`. Without a ROM the ROM-free test classes still lock every number quoted here.

## Implementation contracts (for VISUAL-P2; nothing is implemented)

* Shards: `data/visual1/shard-contract.json` - the break tick, spawn rule and pool, both speed tables, per-tick integration, 48-tick trajectories, cull window, sound, per-zone art streams, the `$47` contrast.
* Loops: `data/visual1/loop-contract.json` - entry gates, route algorithm and tables (hashes, samples), selector pairs and cadence, rolling rule, facing rule, exit/bailout, minimum speed, three 100+-tick reference traversals as test vectors.

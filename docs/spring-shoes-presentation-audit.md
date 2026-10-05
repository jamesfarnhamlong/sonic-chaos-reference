# Spring Shoes presentation, act-clear and detach audit (type `$2F` / player state `$12`)

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified; never committed). Branch `research/spring-shoes-presentation` from Research `main` @ `a779fde`. The POC and the root `AGENTS.md` were **not** modified; POC files were only read.
Machine-readable facts: `data/rom-cache/spring-shoes-presentation.json`. Tool: `tools/spring_shoes_presentation.py` (`python tools/spring_shoes_presentation.py ROM [--check] [--static-only]`, ~35 s). Tests: `tests/test_spring_shoes_presentation.py` (27 tests, ~35 s). `tests/verify_cache.py` regenerates the cache.
Builds on `docs/powerup-shoes-audit.md` (identity, bounce, placements); this audit adds the presentation fixtures, the act-clear interaction and re-tests the detach cases dynamically.
Not covered (as instructed): `$24/$2E/$56`.

Evidence labels: **DECODED DATA**, **BYTE-VERIFIED ASSEMBLY**, **CONTROLLED ROUTINE RESULT** (original Z80 routines on `tools/oracle.py`), **EMULATED ORIGINAL FRAME** (whole game in `tools/sms_frame_harness.py`; requested state set so the engine loads that state's own script; pad held from before the first update; PC hooks and write watches), **SYNTHETIC CONTROL** (state/RAM injected), **POC SOURCE (READ-ONLY)**, **UNRESOLVED**.

## 0. Verdicts

| # | Finding | Class |
|---|---|---|
| P1-P3 | Shoe frames, cadence and Sonic's single frame `$0B` (section 1) | **CANONICAL** |
| P4 | Registration: shoe = Sonic X, Sonic Y + 16 (frame 3) / +11, one-update lag, never mirrored | CANONICAL |
| P6 | Why the POC looks "too active": not explainable from source | UNRESOLVED (needs a capture) |
| B1 | The sign's contact does not request `$20` and does not touch the shoes | CANONICAL |
| B2 | Only footwear clear path: the sign (and the `$50` boss) convert a *requested* `$12` to `$0E` when they wake | CANONICAL |
| B3 | That wake is `EDGE(RIGHT,+32)` (screen X < 288) | EXPLICIT ADAPTER CANDIDATE (wide view) |
| B4-B5 | Replacement timeline; `$D3A4` never cleared; type `$2F` removed only by the generic lifetime routine and re-created from its placement | CANONICAL |
| B6 | **Spring Shoes can stall act completion** (already-awake sign + vertical contact): the child waits for D522 bit1, which state `$12` always clears | CANONICAL (conditional) |
| B7 | Whether that stall is reachable in a canonical placement | UNRESOLVED |
| C1 | `$21` top stomp: successor `$0B`, shoes detach | CANONICAL |
| C2 | `$21` side/low contact: ordinary damage `$1E`, shoes detach | CANONICAL |
| C3 | Mapped `$26` springs **never** launch or detach a `$12` Sonic | CANONICAL (corrects `powerup-shoes-audit.md` section 6) |
| C4 | The POC lets a mapped spring launch state `$12` | **POC DIVERGENCE** (source-traced) |
| C5 | Side-wall branch: hurt `$1E` **without** ring loss or invulnerability; also fired by object contacts mirrored into D523 | CANONICAL |
| C6-C7 | Terrain upright spring (`$0B`) and manual jump (`$0A`) detach | CANONICAL |

## 1. Presentation (part A)

### 1.1 Type `$2F` scripts (DECODED + BYTE-VERIFIED, bank `$1E` table `$8B1A`)

Records are `(duration, frame, callback)`; `FF 00` restarts the state, `FF 03 n` requests state `n`, `FF 07 a` jumps.

| State | Script | Meaning |
|---|---|---|
| 0 | `E0 00 $8B5B`, `FF 00` | creation: requests state 1; `+$03` bit7 (solid, no generic damage) |
| 1 | frame 1 x8, frame 2 x8, callback `$8B64`, loop | free on the ground; offers attachment |
| 3 | frame 3 x**12** (`$8BC3`), `FF 03 04` | attached, just bounced |
| 4 | frame 4 x4 (`$8BC3`), loop | attached, held |
| 5 | frame 4 x1 (`$8BCE` fall speed +1.5), frame 4 x8 (`$8BD7` gravity +0.5 + move), jump | detached |

`$8BC3`: if the player's **current** state `$D501 != $12` the shoe requests state 5. The player's own callback requests state **3** at every floor contact (`$3B84`) and state 5 on jump/side-wall detach.
Mapping frames (type table `$9287`, frames 0..4; frame 0 empty): frames 1/2 = two 8x16 pieces at y -16, x -8/0, tile offsets 0,2 / 4,6; frames 3/4 = pieces at y -16, x -12/-4 with x origin +4 (= -8/0), tile offsets 8,10 / 12,14. Art base `$94` (SEZ) or `$AC` (MGHZ). Frame 4's art is shorter: opaque rows anchor+7..+17 (frames 1-3: +2..+17), cols -7..+8.
Sonic: state `$12` script = **one** record, frame `$0B`, duration 4, `FF 00` (`$8346`); frame `$0B` = five pieces (rows -32..-1, cols -10..+13).

### 1.2 Cadence (EMULATED; MGHZ1 shoes (1552,238), Sonic released 38 px above, no input)

| Update | Event |
|---|---|
| 3-4 | object created (state 0) |
| 5-11 | state 1, frame 1 (the first 8-update frame-1 record was already running) |
| 11 | player requests `$12` (top contact); shoe requested state 3 |
| **12** | first `$12` update: Y speed -7.5, **shoe state 3, frame 3, timer 12**, player current `$12` |
| 24 | shoe state 4, **frame 4** (12 updates of frame 3: updates 12..23) |
| 93, 174, 255 | next floor contacts (**period 81**), shoe state 3 / frame 3 again |
| per cycle | frame 3 x12, frame 4 x69; shoe frame changes exactly twice per bounce |

Sonic during `$12`: record frame `$0B` constantly (`pframe` = 11), timer cycling 4,3,2,1 (re-firing the restart every 4 updates; no visible change). Sonic's only presentation change is facing (`+$04` bit4: values {0,16} with Left/Right alternation). The shoe's flags `+$04` stay 0 in every run: the shoe is **never mirrored**. SEZ1 (art base `$94`) gives the identical cadence (contacts 14/95/176/257, period 81). The SAT buffer equals the renderer model on every checked frame except the pickup update (13) in the static-camera run.
So the shoe sprite is not continuously animated; it changes only at the pickup/bounce event and 12 updates later. Anything that changes the shoe or Sonic sprite more often is not original.

### 1.3 Registration (SOURCE-TRACED + DECODED, verified on the SAT)

`$3BA8` (called from the player's callback every update) sets the owner: `owner X := player X`, `owner Y := player Y + HL` with `HL = $10` when the owner's frame (`+6`) is 3, else 11. The frame tested is the one left by the **previous** object phase. Offsets by update relative to a contact at update C: C: 11 (frame 4 still), **C+1..C+12: 16**, C+13 on: 11. So the compressed frame 3 (rows 0..15 below Sonic's anchor) is shown for the 12 updates after the contact; the held frame 4 (rows -5..+10) overlaps Sonic's lowest piece row (ending at -1) by 5 rows. dx is always 0 (shoe columns -8..+7).
Terrain-space opaque rows (`+18` presentation constant included, `docs/mapped-object-screen-registration.md`): frames 1-3 anchor+2..+17, frame 4 anchor+7..+17.

### 1.4 POC (READ-ONLY)

`OBJ_chaos_object_2F/Step_0.gml` mirrors these states (frames 1/2 every 8 ticks, frame 3 for 12 ticks then 4); the player's sprite in `$12` is `SPR_player_jump`, image 0, speed 0. The reported "too active" look cannot be derived from source; compare a capture against `traces.mghz1_plain.rows_*` (exact update indices) before changing anything (P6).

## 2. Act clear while `$12` (part B)

### 2.1 What the sign does

Type `$18` contact (`$A88E`) writes nothing to the player (stops the timer, starts the hop, `docs/object-18-act-clear.md`). The `$20` request comes from the child `$19` (state 4, `$AB8C`): `if D522 bit1 (floor): CALL $03F5 -> $4892`, **no timeout**. `$18` has an earlier, separate effect:

* **State-2 callback `$A87D`** (runs once when the sign wakes, `$61E1`): `$D3B3 := $12` (sign art selector) and, **if the requested player state is `$12`, requested := `$0E`**. The identical sequence exists at bank `$1E` `$9765` (type `$50` state 0). These are the only two instructions in the ROM that compare the requested state with `$12` (opcode scan). There is no other footwear clear path and no instruction ever clears `$D3A4`.
* Wake threshold (EMULATED sweep, sign screen X 300..271): converts for 287 and below, not for 288+ = `RIGHT+32` (the generic awake band `d < 288`). It is an EDGE-relative relation (B3).

### 2.2 Timeline when the sign wakes with shoes attached (activation fixture)

| Update (relative to the teleport) | Event |
|---|---|
| 3 | the sign's object phase writes requested `$0E` (PC `$A88D`) |
| 4 | the player's update makes `$0E` current |
| 4-5 | the shoes see `$D501 != $12` in their callback and request state 5; state 5 in update 5 |
| 5.. | the shoes fall (+1.5 then +0.5 gravity) |
| 36 | the generic lifetime routine `$61E1` deletes the slot (type `$FE` at `$625F`, tracked placement) |
| later | the placement creator `$80F6` writes type `$2F` again: **the shoes re-appear from their placement** |

`$D3A4` still holds `$D700` afterwards (no write at all). In the canonical flow of MGHZ2 the player reaches the sign with `$0E`, walks into it and the chain runs normally: conversion at frame 2, contact 38, child 168, request `$20` at 316, act-clear flag 346.

### 2.3 Can Spring Shoes stall act completion? (answer: yes, in one narrow case)

State `$12` clears D522 bit1 in **every** branch (rebound `$3B6B`, jump `$45ED` at `$4632`, hurt tail `$494F` at `$495B`; controlled matrix `callback_12_matrix`), so the child's floor test (`$AB8C`) never succeeds while the shoes are attached, and the level timer is already stopped. If the sign is already awake (its conversion already spent) when Sonic owns the shoes and the contact is **vertical** (no D523 side bit), act completion stalls:

* SYNTHETIC pre-woken sign, vertical contact: contact at frame 24, child spawned 154, child state 4 at 302, **no `$20` request in 1,500 updates** (player still `$12`, shoes attached).
* Pressing B1 200 updates after the contact: shoes detach at 225, request `$20` at 315, act-clear flag at 385.
* A **horizontal** contact is not a stall: it triggers the side-wall hurt (section 3.4) at the contact update, the chain completes (request `$20` at 282, flag 320).

So "Spring Shoes have no timer" does not by itself guarantee completion; what guarantees it in the canonical placements is the sign's wake conversion. Reachability: the only shoes within 288 px of a sign are MGHZ2 `(3760,494)` vs the sign `(3968,270)`, and a sign that woke earlier must still be alive when Sonic picks the shoes up; that sequence was **not** reproduced naturally (B7). An implementation must nevertheless reproduce the conversion at the wake and must not add a timer or clear path of its own.

## 3. Detach cases (part C; MGHZ1 shoes attached naturally, Sonic teleported next to the trigger)

| Trigger | Successor requested | Update of request / current / shoe state 5 | Side effects |
|---|---|---|---|
| manual jump (B1/B2; rising, falling or at floor contact) | `$0A`, Y -4.25 | N / N+1 / **N** (the callback sets the owner in the same update) | `+$03` = 3 |
| `$21` top stomp (`$5F17 -> $480C`) | `$0B`, Y -6.75 | N / N+1 / **N+2** | attack clear |
| `$21` side/low contact | `$1E` ordinary damage | N / N+1 / N+2 | rings lost (5 -> 0), `+$03` = `$C1`, invulnerability 119 |
| terrain wall or object-mirrored side contact | `$1E` via `$3B9D -> $494F` | N / N+1 / **N** | **rings kept (5 -> 5), invulnerability 0, `+$03` = 1** |
| terrain upright spring | `$0B`, Y -7.5 | N / N+1 / N+2 | |
| mapped `$26` spring | **none** | - | inert |

* **3.1 Manual jump** (`$3B8E`): clears the airborne bit and calls `$45ED`; allowed even in the air. Owner state 5 is written by the player in the same update.
* **3.2 `$21` top stomp / side:** the shared `$5F17` stomp path requests `$0B`; the shoes then follow the generic rule (`$D501 != $12` -> state 5). A side/low contact is ordinary damage through `$48BC`; when it coincides with a floor contact the shoes' rebound still runs in that update (Y -7.5) and the owner is requested to state 3 once more before it turns to 5.
* **3.3 Mapped `$26` springs are inert (CORRECTION).** `$782AF` needs D522 bit1 **and** a non-negative Y speed; the shoes' rebound (and every other `$12` branch) clears D522 bit1 and sets -7.5 in the same update, and the `$12` floor contact is 8 px higher than a standing contact (foot-probe offset `+8`), outside the spring's 6-px Y window. Whole game: three SEZ1 fixed springs that launch a `$0E` control (request `$0B`) never launch the shoe wearer over 21 x 260 updates (0 spring requests, rebounds 1-3 per run). The isolated-handler result in `powerup-shoes-audit.md` section 6 ("strong mapped `$26` -> `$0B`") is not reachable in play. (POC divergence C4: `SCR_chaos_spring.gml` re-evaluates the contact on the pre-bounce Y speed/floor, i.e. a mapped spring can launch state `$12`.)
* **3.4 Side-wall branch** (`$3B63 AND 12 -> $3B9D`): fires when the merged contact byte `D523` has bit2 or bit3 set after the shared update - terrain walls **and** object contacts mirrored into D523 (a `$10` monitor beside the shoes at SEZ1 (368,238); the `$18` sign). It sets the owner to state 5 and jumps into the hurt tail `$494F`: requested `$1E`, Y -4.0 (+1.0 on a ceiling), X -1.0 (+1.0 when bit3), but skips the damage-gate preamble: **no ring loss, no invulnerability (`+$03` bits 6/7, `$D3B1`)**, no sound. A following hazard can therefore hurt again at once.
* **3.5 Owner pointer:** in every case `$D3A4` stays `$D700` (no write); only the player state decides whether the pointer is used.

## 4. Fixtures to consume

`spring-shoes-presentation.json`: `part_a_presentation` (`object_scripts`, `mapping_frames`, `player_state_12_script`, `static_facts`, `registration`, `traces.{mghz1_plain, mghz1_left_right, sez1_plain, art_bounds_*}` with per-update rows and follow offsets), `part_b_act_clear` (`activation`, `chains`, `callback_12_matrix`), `part_c_detach` (`cases`, `mapped_spring`, `object_mirrored_side_contact_monitor`), `classification`, `agents_candidates`.

## 5. Adapter candidates and unresolved

* **Explicit adapter candidate:** the sign/boss wake that converts the shoes is `EDGE(RIGHT,+32)`; on a wide view the generic wake band must be adapted explicitly (the conversion must still happen before the sign becomes visible/contactable).
* **Unresolved:** (P6) the cause of the "too active" Windows presentation; (B7) natural reachability of the act-clear stall; the first `$12` update's SAT mismatch (the SAT lags one update at the pickup) is recorded, not explained.

## 6. AGENTS candidate updates (not applied)

1. Spring Shoes presentation: attached shoe = frame 3 for 12 updates after every floor contact, frame 4 otherwise (unattached: frames 1/2 every 8); Sonic's record is the single frame `$0B`; shoe anchor = Sonic X, Sonic Y + 16 (frame 3) / +11, one-update lag, never mirrored.
2. A type-`$18` sign (and the type-`$50` boss) converts a *requested* state `$12` to `$0E` when it wakes (screen X < 288 = `EDGE(RIGHT,+32)`); no other code clears Spring Shoes except the state change itself. `$D3A4` is never cleared.
3. Spring Shoes can stall act completion only in the narrow case of an already-awake sign plus a vertical contact (the child waits for D522 bit1, which state `$12` always clears); a side contact hurts instead.
4. Mapped `$26` springs never act on state `$12`; terrain springs, `$21` stomps, damage and manual jump do. The state-`$12` side-wall branch hurts without ring loss or invulnerability and is also triggered by object contacts mirrored into D523.

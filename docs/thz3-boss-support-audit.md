# THZ3 boss/support audit and `$1B` / `$28` closure

**Contact/presentation supplement:** [thz3-boss-contact-followup.md](thz3-boss-contact-followup.md)
has exact velocity/flag responses, hurt versus power immunity, palette timing
and the entry-frame oracle. It corrects the old 22-update minimum interpretation
to **21** (22 was the earlier driver schedule), and verifies that state 18 has
no fighting-contact cooldown gate. The focused cache is separate to preserve
this broad audit's reproducibility. Supplement checkpoint is on
`research/thz3-contact-feedback`, pending review before integration into main.

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified; never committed).
`SonicChaos_POC_thz1_cleanup` was **read only**. Builds on `docs/object-50.md`, `docs/platform-spike-collision-audit.md`, `docs/player-attack-badnik-audit.md`,
`docs/object-18-act-clear.md`, `docs/viewport-semantics-audit.md`.
Machine-readable: `data/rom-cache/thz3-boss-support.json` (all evidence) and `data/rom-cache/thz3/implementation-manifest.json` (POC manifest).
Tool: `tools/thz3_boss_support.py` (`--check`, `--png DIR`). Tests: `tests/test_thz3_boss_support.py` (43 tests; 9 re-run the ROM-backed sections).

Evidence labels: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED, CONTROLLED (original Z80 routines, `tools/oracle.py`), EMULATED (whole game,
`tools/sms_frame_harness.py`), UNRESOLVED.

**Harness correction (affects older EMULATED rows).** `Emu.restore()` snapshots at an arbitrary CPU position and does not restore `int_disabled`,
`frame_tick`, `index_rp_kind`; the first update after a teleport could be a partial update that depends on IRQ phase (vx -1004 vs -1024 for one identical
teleport). All EMULATED fixtures here write from a PC hook at `$1336` (the instruction after `CALL $062D` in the main loop `$1333`, the start of an update)
and are bit-identical on repeat. Replaying the whole static-spike diagnostic grid that way moves 1446 run classes by < 2% (A 482→480, B 132→128,
D 718→722, E1 34→36, E2 4→4); no class appears or disappears. Older caches are unchanged.

## Part A — `$1B` / `$28` closure

### A1 `$1B` cooldown versus side wall (BYTE-VERIFIED + CONTROLLED, 96 probes + sequences)
The helper `$32CFD` tests the cooldown **first** and returns before `CALL $033B` (`$6328`). So during the 16 cooldown updates the contact helper does
nothing at all:

| Part | During cooldown |
|---|---|
| damage cooldown | `+$1F = 16` after a damaging top contact; decremented once per helper call, **only in states 1 and 2** (frozen in 3/4 and while `+$04` bit 6 is set); a remainder carries into the next cycle (example: set with 5 updates of the raised hold left → 12 stays through hidden, then 11, 10, 9 in the next rise) |
| contact detection | `$6328` not run: `+$20/+$21` and the player's `$D521` are not written |
| side wall | **inactive**: `$5DD1` zeroes `$D521` at the start of every object phase, `$6328` is the only writer, merge `$64CB` copies it to `$D523` for the next player pass; no call = no wall bit (the wall also needs a non-attacking, non-invulnerable player) |
| grounded-attacker push | **inactive** (it sits after the `$033B` call) |
| the object itself | keeps running (script, rise/hold/retract, drawing) |

Sequence (walker and attacker): damage at update 0, updates 1..16 inactive, update 17 is the first with wall/push. Nothing else (`+$04`, invulnerability,
`$D503` bit 6) is tested by the helper.

### A2 grounded-attacker push (BYTE-VERIFIED + CONTROLLED, 14,884 grid cases + 6,240 independence cases, 0 mismatches vs model)
Condition: cooldown 0, bit 6 clear, state 1/2, Y speed >= 0, contact bit is not "above", `$D522` bit 1 **and** `$D503` bit 1. Result: requested state 1, X speed 0,
`X := objX + 23` only when the contact is horizontal-dominated with `dx >= 0` (+`$21` bit 2), otherwise `objX - 23`.
* **Contact from below** (vertical depth `24-dy` <= horizontal depth `24-|dx|`, dy 0..24; ties go to the vertical axis) clears the horizontal bits, so the push is
  **always -23 (left), even for dx > 0**. The POC assumption "-23 from below" is exact; +23 exists only for right-side horizontal contact.
* `dx = 0` is on the right-hand branch (`dx >= 0`) but vertical depth wins there, so dx = 0 pushes -23; dx 1 at dy 0 pushes +23.
* Independent of facing (`$D504` swept), X-speed sign, object `+$04` (mirror) and state 1/2. Sonic extents 9 (state `$0F`) shift the map by one pixel, rule unchanged.
* After the push the next update runs requested state 1 (`$45B3` clears bit 1): the roll ends.

### A3 lifecycle and phase (EMULATED, update-aligned; `docs/viewport-semantics-audit.md` generic rules unchanged)
**`$28` lift (state 11, parameter `$0A`)**: created asleep in cell 2 (or by the initial fill); the callback `$86DA` runs every update **while asleep** (two idle updates
464,464 then -1 px/update with `+$04 = $42`); keep-alive bit 1 stops generic deletion; `$8908` deletes it (type `$FE`, recreated) when `|playerX-x| >= 640` (checked at 639/640
both sides) or `|playerY-y| >= 672`. PLAYER_DIST, camera independent. Away-and-back inside the radius is continuous with a free run; beyond it the lift restarts at the placement Y.
Y at a fixed absolute update differs with arrival time and direction (table in the cache); Y 100 updates after creation is identical (365). **Phase = updates since creation.**
**`$28` sag platforms (state 5)**: stationary, no keep-alive, support needs awake.
**`$1B`**: created asleep (state 0, `+$04 = $40`), parked in state 1 because its callback returns while asleep; the rise starts after the wake update (9..29 updates later
depending on scroll speed). States 2 (raised hold) and 4 (hidden hold) are timed by the object script, which **keeps running asleep**; states 1 and 3 are advanced by callbacks
and freeze. So a spike put to sleep while raised finishes its hold asleep, parks in state 3 raised, and retracts only after waking; deletion (beyond the generic window) and
recreation restart it from state 0/1 at the placement Y. Different arrival times/directions therefore legitimately show different spike phases. The POC's wide-view retention
adapter keeps spikes where the SMS would delete and restart them (adapter, not ROM).

### A4 static-spike diagnostic rows (closed)
The ten legacy rows (6 E1: vx -6/-4, vy -2; 4 E2: start (1564,835) vx +2) are replayed update-aligned with initial state and first eight updates (`part_a.a4_static_spike_aligned.legacy_ten_cases_replayed`).
The "first-update speed" gap was the unaligned teleport: teleports write only the **requested** state; update 1 applies it (`D501` 1→`$0A`/`$0E`), clamps |vx| > `$0400` to `$0400` with no drag, otherwise
drag -16/256 toward 0, gravity +48/256. Aligned results: the six E1 rows stay E1 (ends differ by 0..6 px from the old rows); the four E2 rows are **hurt at update 2** (second foot sample, previous surface `$85`);
the real E2 (undamaged level/descending foot) exists only for x >= 1564 with vx +4 (leaves the 64 px block in one step; 4 runs). No further movement audit is needed.

## Part B — THZ3 boss/support chain

### B1 `$50` reconciliation
Retained: everything in `docs/object-50.md` sections 1-11 (identity, placement, 19 states, 8 hit points, geometry 20x48, defeat sequence, art, palette). Corrected/closed here: `$12`,
`$0A`, `$D2A6`, `$1543`, the `181 frames` figure (position dependent), hurt-with-bit-1 hits, invincibility details (see below). Still partial: `$D494/$D495` consumer, sound names.

### B2 support objects (DECODED + BYTE-VERIFIED + CONTROLLED; no canonical placements for any of them)
| Type | Role | Creator | Boss-essential? | Facts |
|---|---|---|---|---|
| `$12` | **HUD slide-away**: three rows of four HUD sprites (SAT Y bytes `DB34..DB3F`, Y 16/32/0) scroll up 0.5 px/update | boss state 0 (`$81A6`, parameter `$97`) | timing only: boss state 2 waits for it (**97 updates**, ≈98 after creation) | frame 0 only (blank); deletes itself when the Y=32 row reaches `$E8..$EF`; HUD stays hidden through the fight and returns at the next level; screenshots confirm |
| `$34` | explosion puff (frames 1-4, art base from table `$8C98`: `A2 96 74 6E B2 B2 88 DD`, zone 0 = `$A2`) | boss state 4 script `FF 04` x5, parameter 4 | no (presentation) | no contact call; position jitters from `$D2E2/$D12F`; lifetime (parameter+1) cycles of 26 (fast) or 50 (slow) updates, speed chosen by `$D12F` bit 0 each cycle; observed 129/249/129/248/129 |
| `$0A` | parameter 0: **act-clear bonus + sparkle emitter** (`$D2A6 := $041F`: H time class 9..0, L rings-`$11`; then every 8 updates a `$0A` parameter `$FF` at the player's X, Y-12 / Y-8); parameter `$FF`: sparkle (frames 5/6, 28 updates) | boss state 5 via `$032C` | bonus yes (results), sparkles no | emitter never ends; the same type exists for the other bosses |
| `$0F` | generic replacement poof (frames 7/8/9); the boss slot becomes one with parameter 0 | `$033E` | no | **38 updates** then `$FF` (callback `$A0C6` runs at once; the `128` record is never waited); no sound in this path |

### B3 arena and camera (EMULATED natural run + CONTROLLED boundaries; vocabulary of `AGENTS.md`)
Natural run from (1604,238), camera 1500 (all numbers in the cache):
| Event | Result |
|---|---|
| creation | boss screen X 288..351 (camera 1585..1648): `EDGE(RIGHT,+32..+95)` (every camera X swept) |
| from creation | left scroll limit `D280` raised to the camera every update: the camera never scrolls left again (limit trails the camera by that update's scroll) |
| trigger (state 1→2) | `|dx| < 160` and `|dy| < 256` strict (PLAYER_DIST, 36 boundary cases); right limit `D282 :=` camera X (1657 in the run) |
| state 2 | waits for `$12` (84 updates after the trigger in the run) |
| state 3 | bottom limit `D27E := 78`, pan target `(bossX-256, bossY-160) = (1680,78)`, `D282 := 1680`; `D15F` bit 0 set; pan 1 px/update on X and Y; X ends 1679 (exclusive limit), Y ends 78 (17 and 47 updates) |
| boss entry | state 18 starts the update after state 3 while the pan is still running; boss at 1935, -0.5 px/update; state 6 when screen X low byte `$80..$DF` (measured x 1901, screen 222) |
| patrol | turns at `EDGE(LEFT,+56)` / `EDGE(LEFT,+200)` of the locked view (world 1735 / 1879); anchor range 1726..1887 |
| player clamp | `EDGE(LEFT,+16)..EDGE(RIGHT,-9)`: measured running into it 1694..1927 with camera 1679 |
| terrain | **no wall**: flat solid floor row 8 from X 1600 to 2560; camera and clamp are the only boundary |
| release (state 5) | `D280 := camera X`, `D15E/D15F` cleared, `D282 := 2304` (saved at creation, = 2560-256) |
Widescreen: keep patrol/boss in WORLD terms; the clamp must be a WORLD rectangle `LOCKED_CAMERA(1679)+16..+247` or the arena grows with the view; the act-clear world X is
`worldWidth + 33 = 2593` for any view width (camera limit `worldWidth - view`). Where the locked wide camera sits is a port decision (listed in the cache).

### B4 contact and damage (CONTROLLED, 61,479 grid cases, 0 mismatches)
Grid dx -34..34, dy -52..28 for nine postures against the real callbacks; states 6/9/12/15 identical, state 18 tested separately (it moves **before** its test).
* Box: `|dx| <= 28`, `-48 <= dy <= 24`; side/below with `$D503` bit 1 -> hit (-1 health, knockback `vx -6.0/+6.0`, `vy +6.0` from below, player state `$1B`, flash 7, sound `$B6`); top -> bounce `vy -4.0`, state `$0B`, sound `$A6`, no damage (ignored when already rising); otherwise `D3B0 := $FF` + 2-update cooldown.
* Only bit 1 counts. **Invincibility pickup** leaves `$D503 = $83` so it hits; after the next landing (bit 1 cleared) an invincible Sonic neither hits (request is cleared by `$48BC` for `$D532 == 6`) nor is hurt.
* **Hurt (bit 6) with bit 1 still set still hits** (boss `+$03` bit 7 bypasses the player's bit-6 gate); hurt without bit 1 produces a request that `$48BC` discards. Blink (bit 7) non-attacking: request ignored, boss still solid.
* Cooldown/reaction: reaction states 20 updates, earliest next hit 22 updates later (8 hits at 22-update intervals in the fight run).

### B5 phase model — see `part_b.b5_phase_model` (19 rows, classes gameplay/presentation). Vulnerable states 6, 9, 12, 15 only.

### B6/B7 defeat and act clear (EMULATED, update-aligned; frames counted on the harness frame counter because the clear sequence leaves the `$1333` loop)
Final hit at creation+361 → state 4 the same update (five `$34` at offsets (-8,0)(8,0)(0,-16)(-8,-24)(-8,-24), updates 0..4) → 148 updates → conversion (state 5 completes in one update when Sonic is on the floor).
Conversion update: camera released, `D282 := 2304`, player state `$20` + jingle `$97`, `$0A` parameter 0 sets `D2A6` (0x0936 for 47 rings and a fast clear), slot becomes `$0F`; no score for the boss.
No input control from then on (hostile buttons: identical flag frame and player X). Flag: `playerX - cameraX > $120` (player 2591, camera 2299) = conversion+186 frames (181 when starting from X 1800).
Main loop `$1333` → **`$1543`** (not `$14AE`): 60 waits, fades, results `$32F9` at flag+199, `$2D55` act-3 boss bonus loop (zone table 50,100,150,200,250,600 iterations of +10) at flag+275, ring tally (10/ring) then `D2A6` steps (1 each) from flag+299, advance `$15CE` at flag+856..889 (rings 0..99): `D298 := 0`, `D297 += 1` → zone 1 act 0. Score = rings×10 + `D2A6` steps + 500 (checked for 0, 10, 47, 99 rings). Timer `D2BE` stays `$FF`.
Convergence with `$18/$19/$20`: shared from player state `$20` (`$4892`, `$83A6`, flag `D293`) and the results routines; different creator (`$50` state 5 instead of `$19`), bonus source (`$0A`), no timer stop, `$1543` instead of `$14AE`.
Needed to finish THZ3 for POC: the flag → progression request only; screen/tally/score are deferrable (same deferral as THZ1/2).

### B8 assets
Extracted/decoded: boss tiles (72 + 44 mirrored via bit-reversal + 12 explosion tiles, hashes in cache), boss mapping, palette `$0C`, frames of `$34`, `$0A`, `$0F` (tiles already in the THZ VRAM image), HUD (existing).
`python tools/thz3_boss_support.py ROM --png build/thz3-boss-support` writes boss (6 + 4 mirrored), puff (4), sparkle (2), poof (3) frames (git-ignored). Genuinely missing: audio, results-screen graphics. No substitute art.

### B9 manifest — `data/rom-cache/thz3/implementation-manifest.json`: reused systems, 10 placements, 19-state table, contact rules and 128 fixtures, arena constants in the vocabulary, defeat/clear summary, assets, POC readiness.

### B11 POC readiness (read-only)
Usable unchanged: `SCR_chaos_viewport` vocabulary, `SCR_chaos_box_contact` (+projection), `chaos_attack_posture` and the staged `D3B0`, `chaos_goal_clear_dx`/state `$20` tail/`chaos_act_complete`, `OBJ_chaos_object_0F_transient` (37 visible updates = ROM),
and `SCR_chaos_spike1b` already matches A1/A2 (whole helper skipped in cooldown, +23 only for bit 4). New: the boss object, a scroll-limit/arena-camera layer with an explicit-target pan, a world-rectangle arena clamp, boss-clear completion (bonus at conversion, timer not stopped),
`$12/$34/$0A` effects, sprite import. Likely conflicts: `chaos_goal_clamp_player` and `chaos_goal_pan_step` are live-view/sign based; `chaos_finish_time` assumes a `$18` stop; no scroll limits in `OBJ_chaos_zone`; THZ3 listed as "no act clear". THZ3 is reasonably completable in one POC batch.

## Unresolved / deferred
Results-screen graphics and score-loop presentation; tally button-skip not observed in the harness; sound numbers only; zones 1-7 boss tables; one `FF 04 12` byte pattern at ROM `0x30DAC` outside any decoded script; no Windows run.

## Reproduce
```sh
python tools/thz3_boss_support.py ROM.sms            # writes both JSON files (~2.5 min)
python tools/thz3_boss_support.py ROM.sms --check    # byte comparison
python tools/thz3_boss_support.py ROM.sms --png build/thz3-boss-support
python -m unittest tests.test_thz3_boss_support      # ~2 min with SONIC_CHAOS_ROM
```
Note: the repository's default `python` is 3.7 here; the tools need Python >= 3.8 (bytes.hex(sep)), e.g. 3.13.

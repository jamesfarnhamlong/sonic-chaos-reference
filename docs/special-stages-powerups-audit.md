# Special Stages SS-A3 — power-ups, rewards and player-state reuse

Unmerged research on `research/special-stages-canonical`. Machine package `data/rom-cache/special-stages/powerups.json`; tool `tools/ss_powerups.py`; test `tests/test_ss_powerups.py`.
Evidence: CONTROLLED (original reward dispatcher `$4AA3` executed for every queue bit under all 13 zone bytes), EMULATED (whole-game traces), BYTE-VERIFIED (zone-read scan).

## 1. Census

| Object | Parameter | Placements | Meaning |
|---|---|---|---|
| `$10` monitor | 4 | SS1 x1, SS4 x5 | **Rocket Shoes** (queue bit 3 -> `$D532=4`, player state `$11`) |
| `$10` monitor | 5 | SS2 x1, SS4 x1, SS5 x3 | **new here: clock monitor** (queue bit 4): `$D3C4 := 11`, sound `$F8` |
| `$10` monitor | 6 | SS3 x7 | invincibility selector (`$D532=6`, timer `$0258`, d503 bits1/7, child `$05`) |
| `$2F` | 0 | SS2 x7 | Spring Shoes pickup |
| `$26` | 0 / 1 | SS4 x2 / x3 | spring: parameter 0 strong, 1 weak |
| `$31` | 1/2/4/8/16 | one per stage | goal ring (SS-A4) |

There are no enemies, no `$09` rings, no `$18` signs, no hazards objects in any stage. Reward queue bit for monitor parameter *p* is `p-1` (`D3A3`); parameters 1..6 map to bits 0..5.

## 2. Shared contracts that are reused unchanged (identity proven, not inferred from art)

Object code is global (type table `$65BA`, bank states); a static scan of every read of `$D297` in the ROM (SS-A1 section 7) finds no zone read inside the `$10`, `$26`, `$2F` object code or the player spring/shoes states. The controlled sweep confirms it for the rewards: running `$4AA3` for each bit under zones 0..12 gives **identical** results except the two below.

- `$10` param 2 (life), 3 (state `$0B`-free speed selector `$D532=3`, 900), 5, 6: identical in all zones. (Param 5 sets `$D3C4` everywhere; the variable is read only by the Special-Stage timer branch `$2826`.)
- Rocket Shoes otherwise follow `docs/powerup-shoes-audit.md` (state `$11`, thrust, 300 updates elsewhere).
- Spring Shoes: EMULATED SS2 first pickup enters state `$12` at update 11 of the trace, launch Y -7.5 (`$F880`), relaunch -7.5 on each floor contact (4/4 observed), owner pointer `$D3A4 = $D700` — identical to `docs/powerup-shoes-audit.md`.
- `$26` springs: parameter 0 -> state `$0B`, `$D448 = $FF`, Y -7.375 (seen -1864 after the update's gravity); parameter 1 -> `$D448 = 0`, Y -5.0 (-1256 after gravity). Identical to `docs/spring-interaction-audit.md`; terrain springs in the maps use the shared handlers with the zone != 0 diagonal Y -5.5.
- Pickup score, monitor break order and contact geometry: shared (`$5FA0`/`$6328` family).

## 3. Special-Stage-specific overrides (complete list)

1. **Rocket Shoes in zone 8 (SS1)** — `$4AEE` loads `$D44C = $1770` (6000) instead of `$012C`, and `$4787` skips both the pickup sound `$85` and its frame wait, with `$D3A1 = $1770`. CONTROLLED: only deviation for any bit/zone. EMULATED: after pickup the selector stays active until the stage timeout (the 59 s countdown, 3510 frames, ends before 6000 updates); in SS4 (zone 11) the shoes last 300 updates (301 frames observed) and Sonic leaves into the **fall state `$0E`**, with the level music restored by `$189B`.
2. **Clock monitor (param 5) is only meaningful in a Special Stage.** On pickup `$D3C4 = 11`. The countdown branch (`$2826`) then does not decrement `$D2BF` on the next 11 one-second ticks, each tick decrements `$D3C4` (sound `$B5`), and the 11th tick (`D3C4 -> 0`) restarts the stage music (`$8F`). EMULATED SS2: frozen at `$58` from pickup until ~611 frames later (first tick after 12 frames because the 60-frame counter was mid-cycle), timer decrements again from ~700 frames. Re-collecting while paused simply reloads 11 (not additive).
3. **Death/failure.** The shared death setup (`$4984 -> $49A0`) for zones >= 8 sets `$D294` bit5 (stage failure) instead of `$D293` bit2 (life loss). Rocket Shoes' special damage (rings kept) and Spring Shoes' wall-hurt branch are unchanged shared logic; no source of damage exists in the stage objects.
4. **Active shoes/selector state is lost at entry and not restored** (entry zeroes `$D300..$DBBF`), and the stage timeout/death does not touch it explicitly.
5. **Collection never ends a stage.** No power-up writes `$D294`; completion is solely the `$31` ring (SS-A4). Monitor +10 rings and the 100-ring life/entry behavior (SS-A1) are unreachable inside a stage (no `$10/1` placements; entry gate refuses for zone >= 6; EMULATED/CONTROLLED).

Terrain interaction with Rocket Shoes: the shared state-`$11` terrain/screen clamps apply: EMULATED SS1 flight is clamped to screen-anchored Y 34..206 whether Down or Up is held, with no death; neutral Y drifts up slowly (signed-high-byte correction).

## 4. Unresolved

- SS3 places seven invincibility monitors but no hurt source was found; the design purpose is unknown (kept as placements, no invented hazard).
- The `$26` placement at (3856,448) (SS4) was not reached by the controlled walk-on test; its contract is the shared parameter-0 spring by object-code identity.
- Names of sounds `$F8/$B5/$8F/$85` are unresolved (numeric only).

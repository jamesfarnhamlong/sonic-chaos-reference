# T2: camera ownership and screen-boundary audit

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified, never committed).
Research base `c95668822a6451c645e035da5bedce57d5fb9632` (V1/T1). POC read only at C1-I `69527335011bacf22ff16bd25d3a94874a1fa563` (clean checkout, nothing modified).
**The uncommitted V1/T1 Package A was not supplied; nothing below compares it.** Where a statement is about the POC it is about C1-I source and the node VM model of that source, not GameMaker and not Windows.

Machine-readable: `data/t2/` (`owner-map.json`, `clamp-scope.json`, `boss-arrival.json`, `sign-wait.json`, `zone-start.json`, `poc-model.json`, `ownership-contracts.json`, `boss-camera-matrix.json`, `discrepancy-register.json`).
Tools: `tools/t2_camera_audit.py` (needs ROM), `tools/t2_poc_model.js` (needs the POC checkout, read only), `tools/t2_register.py`. Tests: `tests/test_t2_camera_audit.py` (19, ROM-free, 0.02 s).
Evidence classes: **BYTE-VERIFIED** (decoded ROM), **EMULATED** (unmodified ROM in the approximate harness), **SYNTHETIC** (arrival position injected; stated), **POC-SOURCE** (read or executed in the node VM).

## 0. Answers in brief

The four Windows observations do **not** share one cause.

| # | Observation | Cause | Class |
|---|---|---|---|
| 1 | THZ3: camera locks, Sonic runs beyond the screen | The ROM clamps Sonic to the screen in **every** state below `$29`; the POC applies its clamp only for a hand-listed set of owners, and THZ3's boss camera modes 1-2 are not in it | confirmed mismatch (T2-01) |
| 2 | THZ3: the boss is to Sonic's left | Consequence of #1: Sonic passes the boss spawn X 1936 (update 123, both 256 and 348 px). At 348 px the extended arena (to 2018) then keeps him right of the boss for the whole fight. Not an error of the boss position | confirmed mismatch (T2-02) |
| 3 | MGHZ2 end: backtracking leaves Sonic offscreen with the camera locked | Different mechanism: C1-I correctly raises the **left limit** while the awake goal sign waits (ROM vector `$0353`), but the clamp is enabled only after sign contact. Affects all 12 acts, not just MGHZ2 | confirmed mismatch (T2-03) |
| 4 | Zone-start black flashes / momentary falls | Not isolated. ROM: black period, then a 3-step palette fade; GPZ1/MGHZ1/EEZ1 genuinely start airborne and drop 14-15 px (canonical). POC uses an inherited 20-step alpha fade. Needs a Windows probe | unverified (T2-10..12) |

#1-#3 are one **architecture** problem (T2-04): in the ROM the boundary belongs to the player step, in the POC it is an owner list. Section 5 proposes one owner-independent predicate.

## 1. ROM facts (BYTE-VERIFIED + EMULATED)

### 1.1 The player screen boundary is unconditional

`$4141` (bank 1, called from the shared player step `$3FEF` via vector `$0404`; `$4281` is the same test for the `$39xx` handlers):

```text
4141  LD A,(IX+1) ; CP $29 ; JR NC,$4169          state >= $29 : no clamp
4148  HL = playerX - (D174)  ; A = L               D174 = COMMITTED camera, low byte only
4156  CP $10 ; JP C,$4244                           X := cam+$10 (minus this update's X speed), X speed := 0
415E  CP $F8 ; JP NC,$4251                          X := cam+$F7 (same)
```

No object, camera mode or sign state is consulted. Proof (`data/t2/clamp-scope.json`, EMULATED + SYNTHETIC): THZ3, camera frozen by a **bare** limit lock (`D280 = D282 = camera`, no sign, no boss), Sonic held LEFT/RIGHT/jumping: screen X stays 14..249 (compensation order leaves 1-2 px of slack).
State `$20` (act-clear run) never calls it, which is why Sonic legitimately leaves the screen there (flag at `EDGE(RIGHT,+33)`).
Only two call sites use the raise-left-to-camera vector `$0353`: the goal sign's state-3 callback (`$A8C4`) and the shared boss helper (`$8199`) (test `test_no_object_other_than_goal_sign_and_bosses_raises_the_left_limit`); the other left-limit writes are pan, release and the freeze.

Legitimate off-screen phases: state `$20`; states `>= $29`; death/pit falls; EEZ tube and other scripted transports. Everything else is bounded.

### 1.2 Ownership contracts (`data/t2/ownership-contracts.json`)

| Owner | ROM | Camera | Limits | Player bounds |
|---|---|---|---|---|
| O0 ordinary follow | `$4C90 -> $5832`, `$4CB0/$4CF7` | lead 104/136, zone ±8, step ≤ 7 | L/T inclusive, R/B exclusive, crossing step dropped | O-P1 |
| O1 sign wait | sign state-3 callback `$A8C4` -> `$0353` | follow continues | `D280 := max(D280, camera)` each update the sign runs (awake: screen X < 288) | **O-P1** |
| O2 sign pan | `$AA43` -> `$0359` | 1 px/update/axis to (signX-128, signY-153) | `D282 := target` moving right; settles target-1 | O-P1 |
| O3 state `$20` | `$83A6` | at `d > $F8` vector `$0407` freeze | frozen | **none** |
| O4 boss pre-trigger | `$9771 -> $8199 -> $0353` | follow continues | left raised each update; old right saved in boss `+$25/+$27` | O-P1 |
| O5 boss lock | `$9799 -> $0356` | cannot move | `D282 := camera` | O-P1 (the clamp **is** the arena) |
| O6 boss pan | table `$9808`, vector `$0359` | 1 px/update/axis | bottom limit written first; settles target-1 | O-P1 |
| O7 release | `$81BD` (`$81F4` for MGHZ3), GPZ3 `$9D2F`, EEZ3 `$B232/$B92D` | follow resumes ≤ 7 px/update | `D280 := camera` (not MGHZ3); `$035C`; `D282 :=` saved | O-P1 |
| O8 zone specials | GPZ3 world-fixed lock, EEZ3 two encounters, EEZ tube | see matrix | | O-P1 |

The ROM has **no world-space arena rectangle** for any boss. The "arena" is: right limit at the camera (`$0356`) + the clamp.
A camera-committed relation also matters: ROM order is camera -> player -> objects (`$16B8`), and the clamp reads the committed camera, i.e. the previous update's. The POC order (player adapter, objects phase, zone End Step camera) has the same relation.

## 2. Six-zone boss-camera matrix (`data/t2/boss-camera-matrix.json`)

| | THZ3 `$50` | GPZ3 `$51` | SEZ3 `$54` | MGHZ3 `$56` | AQZ3 `$59` | EEZ3 `$5E`,`$60` |
|---|---|---|---|---|---|---|
| Trigger (`$97A1`, strict) | \|dx\|<160, \|dy\|<256 | own code; creation locks | <160, <304 | <160, <304 | <96, <304 | <96, <304 (both) |
| Lock | right := camera at trigger | **right := 1664 (WORLD) at creation**, 270 px ahead; camera runs into it | right := camera | right := camera | right := camera | right := min(old, camera); saved |
| Pan target (`$9808`) | boss + (-256,-160) | LOCKED (1664,96) | boss + (-224,-160) | boss + (-208,-32) | boss + (-128,-160) | boss + (-128,-160) |
| Settles | (1679,78) | (1663,96/97) | (2975,462) | (3060,256) | (1727,78) | (1951,333)/(2335,333) |
| Combat waits for pan? | HUD slot only | camera-ready \|diff\|<4 | no | no | no | per chain |
| Release | `$81BD`: floor gate, `D280:=cam`, `D282:=2304` | head gone: `D280:=cam`, `D282:=1920`, `D27E:=96` | `$81BD`, `D282:=3840` | `$81F4`: no left write, `D282:=3584`, gate X ≥ 3356 + floor | `$81BD`, `D282:=2304` | restores saved right limits; no `$20` |
| Player boundary | O-P1 | O-P1 | O-P1 | O-P1 (floor ends: right edge is a pit) | O-P1 | O-P1 |

Rows marked "per T1" are re-used from `data/t1/transition-audit.json` / the boss audits and were not re-traced; GPZ3, MGHZ3 and EEZ3 release were not driven to completion here (same limit as T1).

### 2.1 Arrival comparison (EMULATED, RIGHT held from 480 px (EEZ3: 260 px) before the anchor; boss state never forced)

| | boss world / screen X at creation | Sonic world / screen X at creation | boss screen X at first visible frame | Sonic then | at arena lock: boss / Sonic screen X | max Sonic screen X, any update |
|---|---|---|---|---|---|---|
| THZ3 | 1936 / 342 (u66) | 1710 / 116 | 255 (u181, Sonic 221) | left of boss | 274 / 116 | 248 |
| GPZ3 | 1728 / 338 (u67) | 1506 / 116 | 254 (u120) | left | 198 / 116 | 249 |
| SEZ3 | 3200 / 338 (u67) | 2978 / 116 | **209 (u169, relocated to 3136,430)** | **right of boss** (246) | 274 / 116 | 248 |
| MGHZ3 | 3269 / 338 (u67) | 3047 / 116 | 255 (u187) | left | 274 / 116 | 248 |
| AQZ3 | 1856 / 338 (u67) | 1634 / 116 | 254 (u88, before lock) | left | 210 / 116 | 249 |
| EEZ3 | 2080 / 340 (u11) | 1855 / 115 | 254 (u33, before lock) | left | 210 / 116 | 248 |

Reading: every boss is created off-screen right and Sonic never exceeds screen X 249 in any zone. THZ3 does approach from the right edge. **SEZ3 is the exception by design**: at state 3 the boss anchor jumps from the placement to (3136,430) at screen X 209, so a Sonic hugging the right clamp (246) has the boss on his left in the original too (T2-14); do not generalise the THZ3 report to SEZ3.
Probe limits: the MGHZ3 run ended when Sonic walked off the arena floor (act reloaded at update 325), so its left/right probes are incomplete; the GPZ3 left probe barely moved (cause not examined), so GPZ3 bounds rest on the approach and the clamp proof.

## 3. POC comparison (POC-SOURCE; `data/t2/poc-model.json`)

### 3.1 THZ3 (observations 1 and 2)

Shipped GML in the POC's node harness, Sonic from x 1560, RIGHT held, no state forced:

| | 256 px | 348 px |
|---|---|---|
| boss created | u64, boss screen X 351, Sonic 116 | u52, boss 443, Sonic 162 |
| arena lock (mode 2) | u83, camera 1645, boss screen X 291 | u83, camera 1599, boss screen X 337 (already inside the view) |
| Sonic max screen X after lock | **443** (view 256) | **441** (view 348) |
| updates with Sonic beyond the view | 52 | 94 |
| Sonic passes boss spawn X 1936 | u123 | u123 |
| final (fight) | Sonic 1825, boss 1852 | Sonic held at 2018 (arena right), boss 1846: boss left of Sonic for 208 updates |

Code path: `SCR_chaos_adapter.gml:199` clamps only for `chaosGoalContact`, GPZ3 active, `chaos_56/54/59_owns_camera`; EEZ3 has its own block at `:212`; THZ3 has only the world rectangle `chaos_boss_clamp` at `:203`, and only when `camera_mode == 3` (`SCR_chaos_boss.gml` `chaos_boss_tick`: modes 1 and 2 run from creation to the HUD wait, about 100 updates).
At 256 px the mode-3 rectangle (1695..1926) equals the ROM clamp at the locked camera (1679 + 16 .. + 247), so only the gap between creation and pan is wrong. At 348 px the rectangle `ARENA_RIGHT + 92 = 2018` equals the viewport clamp `1679 + 339`; **a viewport clamp reproduces the same arena, so the "arena extension" adapter needs no separate rule.**
Boss entry at wide widths (T2-07): the world-locked camera puts the boss spawn inside the view (screen X 337 at the lock, 257 at pan end) instead of at the right edge; that is an adapter consequence, not a defect, and no ROM-backed boss or camera move fixes it. Remaining cosmetic case after the clamp fix: Sonic at the extreme right (`RIGHT-9 = 1938`) is 2 px right of the spawn.

Camera snaps at creation/release (T1-01/02) are carried over unchanged: in this scenario the left limit absorbs the creation snap (step 0), so they depend on Sonic being ahead of centre.

### 3.2 Goal-sign wait (observation 3)

| | ROM (4 acts, EMULATED) | POC model, THZ1 sign, 256 px | 348 px |
|---|---|---|---|
| left limit starts tracking the camera | sign at screen X 268-285 | sign at 285 (u21) | 340 (u1) |
| Sonic min screen X walking back 320 updates | **13** (THZ1, MGHZ2, GPZ2, SEZ2) | **-494** (249 updates left of the view) | **-448** (237 updates) |
| camera while walking back | static (no back-scroll) | static (limit = camera) | static |

The camera behaviour is correct (C1-I I1); the missing piece is the clamp, gated by `global.chaosGoalContact` (`SCR_chaos_level.gml:499`, set at contact). In MGHZ2 the ledge carrying the sign starts between 270 and 420 px before it (a start at 420 px falls off it), so backtracking there is easy to meet, but the defect is act-independent.

## 4. Discrepancy matrix (`data/t2/discrepancy-register.json`, 14 rows)

| ID | Item | Class |
|---|---|---|
| T2-01 | THZ3 modes 1-2 have no screen clamp | confirmed mismatch |
| T2-02 | Boss appears left of Sonic (THZ3) | confirmed mismatch (consequence of T2-01) |
| T2-03 | Sign wait raises the left limit without the clamp (all acts) | confirmed mismatch |
| T2-04 | Clamp is an owner list in the POC, a player-step property in the ROM | confirmed mismatch (architecture) |
| T2-05 | THZ3 creation/release camera re-centre (T1-01/02) | confirmed mismatch, position-dependent |
| T2-06 | Bosses created off-screen right, first visible at X 254-255, Sonic ≤ 249 | canonical |
| T2-14 | SEZ3 boss relocates to screen X 209; may be left of Sonic | canonical |
| T2-07 | THZ3 boss already inside the wide view at the lock | intentional widescreen adapter |
| T2-08 | POC full-width clamp, no speed compensation (±2 px) | intentional widescreen adapter |
| T2-09 | SEZ3/MGHZ3/AQZ3/GPZ3/EEZ3 owners do clamp, equivalent relation | canonical |
| T2-13 | State `$20` exempt from the clamp | canonical |
| T2-10 | Zone-start black/fade timing vs inherited 20-step alpha fade | unverified |
| T2-11 | GPZ1/MGHZ1/EEZ1 start airborne (14-15 px drop); THZ1/SEZ1/AQZ1 7 px anchor flicker under the fade | canonical |
| T2-12 | POC first-frame view X/Y and fade coverage | unverified |

### Zone start (observation 4; `data/t2/zone-start.json`, EMULATED harness frames, palettes as CRAM sums)

All eight traced acts: VDP display stays on; BG and sprite palettes are black until frame 34-39, then three steps at 5-frame cadence; the camera Y advances 8 px per frame during the black period (the loader's scroll), so the camera set-up is hidden. GPZ1, MGHZ1 and EEZ1 start in the air (state 14), drop 14-15 px, land at frame 39-41. THZ1/SEZ1/AQZ1 flicker the anchor 654/661 (7 px) during the first fade step. The POC creates `OBJ_effect_fade_in` (alpha 1, minus 0.05 per step, 20 steps) in `OBJ_chaos_zone/Create_0.gml:43`, before `chaos_camera_ordinary_begin` (line 102), so a different black duration and cadence is certain; whether it produces the flash is **not** shown. Do not start a palette rewrite; run probe R-T2-3.

## 5. Recommended architecture

**One owner-independent bounds predicate; owners declare camera behaviour only.**

1. `chaos_player_bounds_active(core)` := `core.state < $29` and not the `$20` run (state or request) and the player is alive. It returns the viewport rectangle `EDGE(LEFT,+16)..EDGE(RIGHT,-9)` of the live view (full-width integers, current `chaos_goal_clamp_player`). It is called once per player update in `SCR_chaos_adapter_step/_end`, replacing the disjunction at `:199`, the THZ3 world rectangle at `:203` and the EEZ block at `:212`.
2. Camera ownership as a priority table (highest first): `STATE20_FREEZE`, `SIGN_PAN`, `BOSS_<zone>` (one record per zone: `follows`, `step(vp)`, `release(vp)`), `SIGN_WAIT` (left-lock only; follow stays on), `ORDINARY`. `chaos_camera_follow_allowed()` and the seven step calls in `OBJ_chaos_zone/Step_2.gml` become one dispatch. Zone specifics (GPZ3 world-fixed right limit, MGHZ3 release gate and no left write, EEZ3 two encounters, SEZ3/AQZ3 no arrival gate) live in the zone record, as in the matrix.
3. Shared pieces stay shared: left-lock raise (`$0353` = `chaos_camera_raise_left_limit`), right lock (`$0356`), pan (`$5956` = `chaos_goal_pan_step` generalised to a target), release (`$035C`). Boss tables `$97A1/$9808` are data (`owner-map.json`).
4. Do **not** keep a THZ-style world arena for THZ3: at 256 px it is the clamp at the locked camera, at wide widths the viewport clamp gives the same rectangle.

Minimal first step (fixes #1-#3 without the refactor): extend the predicate to `SIGN_WAIT` and THZ3 camera modes 1-3. Decision **D-T2-1**: universal ROM gate (recommended; byte-verified) versus "only while a lock is active". They differ only if Sonic outruns the follow camera in ordinary play; add a counter of would-be clamp hits and run one ordinary playthrough before enabling the universal form (ROM would also zero his speed there).

### Test and acceptance plan (focused)

* Extend the POC node harness: for each owner (sign wait on THZ1/MGHZ2/GPZ2/SEZ2 signs, THZ3 modes 1-3, SEZ3/MGHZ3/AQZ3/GPZ3/EEZ3 owners) hold RIGHT then LEFT for 300 updates at 256, 348 and 400 px: assert screen X within `[16, W-9]`; state `$20` exempt. `TargetContract.satisfied()` in the test file is the predicate shape; the current baseline fails it by design.
* Boss arrival: creation screen X ≥ view width; first visible with Sonic left of it (SEZ3 excepted); camera step ≤ 4 at wide; ROM series ≤ 7 at 256 (T1 PKG-T1B).
* Windows F5 (new behaviour only): THZ3 approach (cannot run past the screen edge; boss comes from the right), a sign wait with backtracking in MGHZ2 and one other act, SEZ3 boss entry for comparison (boss may appear left: original), one ordinary act clear (still runs off-screen).

## 6. Decisions and probes for Manager

* **D-T2-1** universal ROM gate vs lock-conditioned clamp (recommend universal, with telemetry first).
* **D-T2-2** THZ3 at wide widths: accept the adapter (boss visible inside the view at the lock; no boss/camera move). Recommended; nothing ROM-backed supports moving the boss.
* **D-T2-3** bundle with T1 PKG-T1A (THZ3 creation/release camera) in one camera-module package: recommended, same file and same predicate.
* **R-T2-3** Windows capture for observation 4: per update for 60 updates in THZ1, GPZ1, MGHZ1 dump view X/Y, fade alpha, player y, and a screen recording.
* Not authorised/not done: any POC change, global clamp, boss-position adjustment, palette rewrite.

## 7. Reproduction and limits

```text
python tools/t2_camera_audit.py ROM --write|--check     # ~2 min; --only static|clamp|boss|sign|start
POC=<C1-I checkout> node tools/t2_poc_model.js --write|--check
python tools/t2_register.py --write|--check
python -m unittest tests.test_t2_camera_audit
```

Limits: approximate VDP/IRQ harness (zone-start frames are harness frames, not updates, and palette sums are not colours); arrival scripts inject the start position (stated); THZ3 floor starts at X 1480 so creation at widths ≥ 590 px cannot be reached from the floor in the model; MGHZ3 and GPZ3 boundary probes incomplete (section 2.1); GPZ3/MGHZ3/EEZ3 release not re-traced; V1/T1 Package A not available; no GameMaker or Windows run; POC statements rest on source reading and the node VM model.

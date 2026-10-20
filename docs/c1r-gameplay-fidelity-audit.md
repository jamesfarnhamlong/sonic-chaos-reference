# C1-R: Player, camera and interaction fidelity audit

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified, never committed).
Research base `b6467ba0ad79fad0937f750083a5261e7ea64e8f` (branch `research/c1r-gameplay-fidelity`). Accepted POC read-only at `ac021e1ef2665c8668de13959f5ccc4653f312d1`
(`poc/visual-p3-loop-presentation`, clean worktree). VISUAL-1 (`41318f5`, `claude/eager-hopper-xo4388`) was read, not merged. Nothing in the POC, the root `AGENTS.md` or any release was modified.

Machine-readable results: `data/c1r/gameplay-fidelity-register.json` (50 rows), `data/c1r/implementation-contracts.json` (proposed C1-I),
`data/c1r/camera-look-trace.json` (7 emulated scenarios, 3,557 camera updates), `data/c1r/sign-registration.json`.
Tools: `tools/c1r_camera_trace.py`, `tools/c1r_camera_model.py`, `tools/c1r_sign_registration.py`, `tools/c1r_build_register.py`. Tests: `tests/test_c1r_audit.py` (18 tests, 0.03 s).

## 0. Executive summary

**Systems audited.** Player control states 0-4, 5-9, `$0F/$10`, `$15/$1A`, `$19`; idle wait; the ordinary follow camera (X and Y), look-up/look-down, camera limits, level start, sign pan and
boss/special-stage camera ownership; goal-sign (type `$18`) registration; the loop-entry, sticking and oscillation issues carried over from earlier audits.

**Confirmed matches (source-compared or earlier-differential, 12 rows).** Look-up (state 3) and crouch (state 4) entry/exit logic, spin dash, walk/run/brake/roll transitions, hurt lock, the sign pan and
act-clear rules, sign placement/contact/prize selection, level-start camera record. A MATCH row always states its basis (`match_basis`); none is claimed from the absence of a reported bug.

**Discrepancies (10 MISMATCH, 11 MISSING, 8 ADAPTER, 9 UNVERIFIED).** The ones that matter:

| # | Finding | Row |
|---|---|---|
| 1 | The POC camera is **not** the ROM follow rule. X is GameMaker's native object follow (border = width/2.3, no facing lead); Y is a rigid lock `player.y - viewH/1.5`. In the ROM the player rests at screen Y 80-112 (foot line), in the POC at about 148 - 36 to 68 px lower - and the ROM caps the camera at 7 px/update. | B-06, B-07 |
| 2 | **Look-up and look-down are not timers or offsets.** Each callback writes a persistent *lead target* (`$D289`): `$B8` while looking up, `$30` while crouching, `$60` otherwise. The working lead slews 1 px/update and the follow zone (lead +/-16) does the rest. The "delay" is an emergent 0-35 updates, the displacement 56 px up / 48 px down from a standing rest, and the return is hysteretic. Fully reproduced by a 40-line model (0 mismatches over 3,557 updates). | B-01 .. B-05 |
| 3 | **Look-up + jump button is Peel-Out in the ROM, a jump in the POC** (`SCR_cc_shared` jumps in every state). Peel-Out (`$15/$1A`) does not exist in the core. | A-03 .. A-05 |
| 4 | Peel-Out is released by **releasing Up**, not the button; launch speed 7.0 px/update; 12 updates of invulnerability; the star aura after 1,764 updates of charge resolves the earlier UNRESOLVED note. | A-04 .. A-06 |
| 5 | **Not in any earlier register:** state `$19` is a ledge-edge pose requested by every stand request when terrain probes at X-4/X+4 differ by 16 or more. The POC has neither the state nor frames `$19-$1B`. | A-11 |
| 6 | **Goal-sign cropping is a resource-conversion defect, not a placement defect.** All 12 sign sprites lost the top 4 rows of the ROM art (the face top) because the importer crops `(0,4,32,52)`; the draw offset 22 (= 18 + 4) hides the shift. Visible rows 4-47 are already at the ROM-derived position (xor = 0). | C-02, C-03 |
| 7 | The ROM shows the terrain window from world row `camY + 17` (VScroll bias); the POC view top is the record itself. 79 view-Y reads in 64 files make this an adapter decision, not a free fix. | B-08 |
| 8 | A documentation error is corrected: `docs/viewport-semantics-audit.md` gives the Y lead as `$78`; `$78` is only the *initial* lead. Ordinary play uses `$60`. | B-15 |

**Unresolved evidence gaps.** Platform-owner exception for look-up (`D3C0`) is byte-verified but not traced; `D368` meaning and a natural reproduction of state `$19`; sign X +1 px; Tails; non-THZ camera
limits; the harness is an approximate VDP/IRQ model; GameMaker and Windows were not run.

**Recommended C1-I scope (one release, four independent pieces; contracts in `implementation-contracts.json`).**
I1+I2 ROM follow camera with look-up/look-down (moderate; the only high-risk piece), I3 Peel-Out + the look-up jump fix (moderate), I4 idle wait (routine), I6 sign resource/offset fix (routine).
Four Manager decisions are needed before dispatch (section 7): D1 widescreen lead mapping, D2 the 17 px window bias, D3 view height, D4 sign X policy.

**Deliberately deferred.** Loop-entry rule, Y anchor, low-speed bailout and speed caps (needs the VISUAL-1 contract merged); terrain sticking/slope/spring oscillation (track C2); the 17 px bias; long-hold
aura; ledge pose until Research R-C1-1; special-stage and boss cameras (inert-guard tests only).

**Costs.** Trace regeneration 23-29 s, model replay and all 18 tests 0.03 s, sign tool about 2 s. No full-ROM replay and no historical regression sweep were needed.

## 1. Method and evidence classes

Sequence (Lean Verification 2.0): (1) inventory existing evidence; (2) compare ROM source against the POC source; (3) targeted emulated traces only where the existing research was silent;
(4) validate them with small tests; (5) build the register and contracts.

Evidence labels used in the register: `ROM_SOURCE` (disassembly read from the ROM, `z80dis`), `EMULATED` (unmodified ROM driven by scripted pad input in `tools/g0_rig.py`, approximate VDP),
`CONTROLLED` (computation compared exactly, here the sign mask comparison), `PRIOR_RESEARCH` (a cited Research document), `POC_SOURCE` (GML read), `WINDOWS_ACCEPTANCE`.
No Windows session was available to this audit; "accepted" always refers to earlier Manager-recorded acceptance.

**Method note (new).** Frame-sampled traces are wrong for update-level claims: the harness frame is not one game update (lag frames run the engine twice or not at all). The first attempt sampled
per harness frame and produced hundreds of spurious model mismatches. The final tool installs a PC hook on the camera entry `$4C90` and records one row per game update.

Existing evidence reused instead of re-derived: `docs/viewport-semantics-audit.md` (follow constants, limits, sign pan), `docs/rq4-campaign-start-registration.md` (start camera), `docs/mapped-object-screen-registration.md`
(+1/+18 sprite bias), `docs/object-18-act-clear.md`, `docs/u3-sign-prize-presentation.md`, `docs/player-attack-badnik-audit.md` (attack bit, `$46CE/$46E2`), `docs/player-animation-counter.md` (record durations),
`docs/visual-p1-presentation.md` (idle limitation), VISUAL-0 state/frame catalogue and VISUAL-1 loop contract (read only).

## 2. Player controls and states (coverage A)

### 2.1 Recovered control logic (BYTE-VERIFIED; EMULATED where stated)

```text
state 0/1 callback $36C6:   D289 := $60 ; $3FEF (input, movement, terrain, $48BC, jump) ;
                            if requested still 1: moving or Left/Right -> walk $45CE ; Up -> $46B0 (3) ; Down -> $46BB (4)
state 2   callback $36F0:   $3FEF ; if requested still 2: fresh button -> jump $45ED ; Left/Right -> walk ; Up -> 3 ; Down -> 4          (no D289 write)
state 3   callback $3713:   if D3C0 == 0: D289 := $B8 ;
                            Sonic: fresh button (D147 & $30) -> $46CE Peel-Out, BEFORE movement ; else $3FEF ; Left/Right -> walk ; Down -> 4 ; Up released -> stand $45B3
state 4   callback $3759:   if D3C0 == 0: D289 := $30 ; fresh button -> $4701 spin-dash charge ; $3FEF ; Up -> 3 ; Down released -> stand
state $15 callback $396D:   +4 bit 7 cleared ; D289 := $60 ; $690B ; side push-out +/-4 ; $48BC ; $4281 ; fresh button -> sound $AC ; Up not held -> $46E2
$46E2:                      D373 := $0700 ; speed := +/-$0700 (+4 bit 4) ; request $1A ; sound $BE        (state-1A entry call $8313: invulnerable, D3B1 = $0C)
state $1A callback $39B6:   D289 := $60 ; $3FEF ; $4281 ; side contact -> clear bits 1,7 + walk ; floor block $19 -> run ; else $37F4 exits
stand tail $4A33:           probe (X-4, foot+18) and (X+4, foot+18) with $7666 ; |D368_a - D368_b| >= 16 -> state $19 (facing by side) ; equal -> state 1
state $19 callback $3BC6:   D289 := $60 ; $3FEF ; speed or Left/Right -> walk ; Up -> 3 ; Down -> 4
```

`D3C0` is the platform/support-owner byte (`docs/mghz-m1-windows-followup.md`), not a water flag (`D443` is water). The lead writers are a closed set: 13 `LD (D289),A` sites in the ROM (`$B8`, `$30`, `$78` at level load,
ten times `$60`); the test `test_lead_writers` pins them. Table B-05 in the register lists which states rewrite the target and which leave it untouched.

### 2.2 Emulated observations (`data/c1r/camera-look-trace.json`, THZ1, Sonic, fresh New Game per scenario)

| Scenario | Observation |
|---|---|
| `idle_wait` | 2 updates in state 0, **exactly 180 updates in state 1**, then state 2 (script record `0B x180`, `FF 03 02`). |
| `look_up_hold_release` | State 3 one update after Up. Target `$B8` from the second update of state 3. Lead 96 -> 184 at 1 px/update; first camera move at update 35 (Sonic at screen Y 112); 56 px up after 150 updates; screen Y 168. Release: target `$60`, camera starts back about 35 updates later, returns to screen Y 112. |
| `look_down_hold_release` | State 4, target `$30`; camera moves at once (Sonic already at the lower zone edge): 48 px down, screen Y 64. Release returns to screen Y **80** (hysteresis). |
| `look_up_then_walk` | Right pressed in state 3 (lead 162 at that point): walk request rewrites the target to `$60` on the same update; the lead slews back at 1 px/update (66 steps). |
| `peel_out_ordinary` | Up 20, Up+button 3: state 3 -> request 21 on the button update; charge lasts while Up is held (63 updates here); on Up release state 26 with vx 1792; `D503` bit 7 for exactly 12 updates; with no direction held friction takes vx to 0 in about 60 updates. |
| `peel_out_hold_right` | vx stays 1792 until the first ramp (x about 393, state 27 launch). |
| `peel_out_long_hold` | Up held 1,900 frames: object type 5 appears exactly 1,764 frames after state 21 begins (script: 60 + 24 + 210 x 8); `D503` = `$82`; the previous note "aura only after a very long charge" is resolved. |

### 2.3 State inventory against the accepted POC

| ROM state | Role (numeric names kept) | POC status | Notes |
|---|---|---|---|
| `$00/$01` | stand | implemented | idle counter not modelled (A-08) |
| `$02` | idle wait | **unreachable**: branch exists (`SCR_chaos_core.gml:803`) but nothing requests it | A-08..A-10 |
| `$03`, `$04` | look-up, crouch | implemented (MATCH, source-compared) | camera hooks missing; state 3 + button wrong (A-03) |
| `$05-$08` | walk, run, skid L/R | implemented | VISUAL-P1 presentation |
| `$09`, `$0A` | roll, jump | implemented | |
| `$0B`, `$0E`, `$1B`, `$1C`, `$14` | spring/fall/ramp/diagonal/strip | implemented | legacy sprite selection and `sign(vx)` facing remain (D-06, D-08) |
| `$0C/$0D` | loop routes | **inherited GameMaker loop adapter**, not ROM states | D-01..D-04 |
| `$0F/$10` | spin dash | implemented | |
| `$11/$12` | rocket/spring shoes | implemented | |
| `$13` | GPZ route | implemented | |
| `$15/$1A` | peel-out charge/run | **missing** | A-04, A-05; presentation (frames `$07-$0A`) already owned by VISUAL-P1 |
| `$19` | ledge-edge pose | **missing** | A-11 (new) |
| `$1E/$1F/$20/$21/$22` | hurt, death, act clear, tube, twist | implemented | |

### 2.4 Control suppression and recovery

No new defect found. Hurt (lock until landing), act clear (input ignored), special fall `$14` (no air control - canonical), footwear states and the sign edge clamp were audited by earlier research and
are implemented; the two open items are the `$14` death line (A-16/D-10, camera-bottom dependent) and monitor top contact / wall push (A-17, track C2).

## 3. Camera (coverage B)

### 3.1 The original rule (viewport 256x192)

```text
per game update, after the player update ($4C90 -> $5832):
  X lead target = $68 (right-facing) | $88 (left-facing, +04 bit 4) | $78 (pan mode, follow skipped)      ; working lead slews 1 px/update
  Y lead target = D289                                                                                    ; working lead D28D slews 1 px/update
  X: k = low byte(playerX - camX) ; k < lead-8 : step max(-7, k-(lead-8)) (a step of -8 survives) ; k >= lead+8 : step min(7, k-(lead+8))
  Y: k = low byte(playerY - camY) ; k < lead-16 : step max(-7, k-(lead-16))                                 ; k >= lead+16 : step min(7, k-(lead+16))
  limits ($4CB0/$4CF7): left/top inclusive, right/bottom exclusive ; a step that would cross is DROPPED
  level load ($5074): both leads start at $78
```

`tools/c1r_camera_model.py` implements exactly this; `tests/test_c1r_audit.py::test_model_replays_every_update` compares it with every consecutive pair of the 3,557 recorded updates (working camera X/Y and both
leads): **0 mismatches**. The model is the executable contract for the Designer.

### 3.2 Look-up, look-down: answers to the required questions

| Question | ROM answer | Evidence |
|---|---|---|
| Prerequisites | Sonic in state 3 (Up) or 4 (Down) **and** the support-owner byte `D3C0` = 0. Tails shares the callbacks. | `$3713`, `$3759` |
| Delay before movement | No timer. The lead moves 1 px/update; the camera moves when the zone edge (lead -/+ 16) passes Sonic. From screen Y 112: first move after 33 lead steps up, 1 down; from 80: 1 up, 33 down (trace rows add the 2-update state-entry lag). Closed form: `look_displacement()`. | trace + model |
| Displacement, speed, limits | Final Sonic screen Y = lead -/+ 16: **168 looking up, 64 looking down** (56 / 48 px from a rest at 112; 88 / 16 px from 80). Camera speed = lead slew = 1 px/update (cap 7). Bounded by the stage limits with dropped-step semantics. | trace |
| Release | Target `$60` immediately; lead slews back 1 px/update; the camera returns 32-35 updates later, ends at the zone edge (112 after look-up, 80 after look-down). | trace |
| Reset on jump / roll / hurt / state change | Jump launch (`$45ED`), every walk request (landing, hurt recovery), stand, `$0F`, `$10`, `$15`, `$19`, `$1A` rewrite the target to `$60`. Roll (9), run/skid (6-8), `$0A`, `$0B`, `$0E`, `$1B`, `$1C`, hurt and death leave it unchanged. | B-05 |
| Stage boundary | `$4CB0/$4CF7`: crossing step dropped, so the camera may stop up to 6 px short of a limit. | B-09 |
| Level start / scripted movement / special routes | Start: record, lead `$78` -> 96 over 24 updates (THZ1 camera Y +12). Pan mode (sign, bosses) bypasses the follow and its lead slew entirely. Special stages use their own routine. | B-10..B-13 |

### 3.3 The accepted POC

* Vertical (`objects/OBJ_chaos_zone/Step_2.gml:13-20`): `view.y := clamp(round(player.y - viewH/1.5), 0, room_h - viewH)` every End Step (MGHZ adds a +/-7 cap; EEZ/MGHZ/AQZ zero VSpeed).
* Horizontal (`scripts/SCR_player_view`): `View object = OBJ_player`, `HBorder = round(viewW/2.3)`, `VBorder = 0`, speeds -1. At 348 px that is a free zone 46 px wide centred on the view, no facing lead.
* Start: `Create_0.gml:96-101` seeds the ROM record (G1-B); after the first update the GameMaker rules above apply.
* Sign pan, boss, EEZ/AQZ camera owners are separate and disable the follow (`Step_2.gml:13`).

### 3.4 Viewport distinction

All constants above are authored for a 256x192 window. **Nothing in the ROM defines a widescreen offset**; mapping the 104/136 leads onto 348 px (decision D1) and the 196-row view (D3) are PC adapters and must
be labelled as such. Options and a recommendation are in `implementation-contracts.json` (`decisions_required_before_dispatch`). The recommended D1-A keeps the existing CENTER(n) adapter category.
The 17 px VScroll bias (B-08, decision D2) is a real ROM fact that the POC does not reproduce; reproducing it exactly is not recommended inside C1-I.

## 4. Goal-sign registration (coverage C)

Question: sprite origin, world coordinate, animation offset, draw transform, or resource conversion?

| Candidate cause | Finding |
|---|---|
| World-coordinate registration | **Not the cause.** Anchor = placement record; contact and pan are the accepted ROM rules (C-01). |
| Sprite origin | **Not the cause.** Canvas 32x48, origin (16,48) = ROM piece extent x -16..15, y -48..-1 (C-02). |
| Animation-frame offset | **Not the cause.** All five frames share the same shift. |
| Draw/camera transformation | **Compensation, not cause.** The derived offset for this canvas is +18 (SAT +1, VScroll +17); the POC uses 22 = 18 + 4 (C-03). |
| **Existing resource conversion** | **The cause.** `POC_notes/import_type18_assets.py` (margin 4, bottom-align) and `import_sign_prizes.py:51-55` (`crop((0,4,32,52))`) shift the art up 4 px inside the canvas and cut the top 4 rows (face top). |

Proof (`tools/c1r_sign_registration.py`, mask comparison only, no artwork stored): composing frames 1-5 from the ROM tiles gives 48 opaque rows (frame 1: 1,038 px). Every one of the 12 POC sign
resources has opaque rows 0..43 and, shifted down 4 px, equals the ROM composite minus its first 4 rows with **xor = 0** in all 5 base frames of each tested sprite and in the 8 THZ prize frames compared (990 px versus 1,038 px;
48 px = the missing face top). Because the offset compensates, the visible pixels sit where the ROM-derived registration puts them; the defect is the missing rows. Fix (I6): regenerate without the crop
**and** change the offset to 18 in the same release. Sign prize selection, reward, hop and pan are untouched.

Open (decision D4, row C-04): derived terrain-space X is anchor +1 (HScroll `-(cam+1)`); the POC uses 0 for sign, monitors, `$21` and `$27` (accepted) and +1 only for `$09`. No evidence in hand shows the
reported "alignment" is that 1 px; changing it for the sign alone would be a cosmetic nudge without a class-wide ROM decision.

## 5. Related gameplay discrepancies (coverage D)

| Issue | Classification | Where it goes |
|---|---|---|
| Loop-entry Y 1 px above ROM (`(Y&~31)+4`) | MISMATCH, VISUAL-P3 differential | separate loop-entry package (D-01) |
| Loop entry rule (`$51->$52`), speed gate, airborne entry, plane array | MISMATCH | same package, needs the VISUAL-1 `loop-contract.json` merged first (D-02) |
| Low-speed route bailout | MISMATCH | same package (D-03) |
| Speed caps (8 px, exit cap, sample clamp 394, one-update-short traversal) | MISMATCH | same package (D-04) |
| Sonic sticking/vibration near terrain | UNVERIFIED; **no camera or control-state cause found** (the rigid camera cannot jitter by itself; VISUAL-P1 changed no gameplay state) | track C2 (D-05) |
| Spring/rebound left-right oscillation | UNVERIFIED; documented candidate: legacy `sign(vx)` facing outside P1-owned states | optional I7 or C2 (D-06) |
| Slope/spring contact | UNVERIFIED | C2 (D-07, D-09) |
| Airborne presentation set | MISMATCH, contract exists | presentation track (D-08) |
| Death line vs camera bottom (POC 1043 vs 992) | ADAPTER decision | with B-09 if wanted (D-10) |

## 6. Fidelity register

50 rows (`gameplay-fidelity-register.json`): MATCH 12, ADAPTER 8, MISMATCH 10, MISSING 11, UNVERIFIED 9. Tracks: C1-I 15, research-first 1, separate-research 6, resolved 16, deferred 8, decision 4.
Each row carries stable id, subsystem, ROM reference, evidence list with class, confidence, canonical behaviour, current POC behaviour, classification (+ `match_basis` for every MATCH), existing coverage,
visible impact, risk, action, track and dependencies. Earlier Research documents are cited, never overwritten.

## 7. Proposed consolidated package C1-I (not authorised)

Full contracts (ROM requirement, integration points, scope, fixtures, acceptance, risks, dependencies) are in `implementation-contracts.json`.

| Item | Content | Size | Risk to accepted mechanics | Depends on |
|---|---|---|---|---|
| I1 | ROM follow camera, X and Y, replacing the GM follow in ordinary acts (model + limits + pan hand-over) | moderate | **high**: everything reads the view (lifecycle, death line, MGHZ plunge, EEZ/AQZ scroll) | D1, D2, D3 |
| I2 | Look-up/look-down lead hooks (13-writer table, platform exception) | routine | low | I1 |
| I3 | Peel-Out states 21/26; state 3 + button no longer jumps | moderate | medium: state 26 can enter loops, ramps, springs | I2 (lead rewrite) |
| I4 | Idle wait: 180-update timer, state-2 program, 7 frames | routine | low | art import |
| I6 | Sign: regenerate 12 sprite resources without the crop, offset 22 -> 18 | routine | low if both change together | none |

No item needs a collision or movement rewrite. Blocked or optional: I5 ledge pose (Research R-C1-1), I7 airborne facing bit, I8 long-hold aura. Recommended build order I6, I1+I2, I3, I4; one Windows F5 session
(checklist in the contracts file). I1 is the only piece that can disturb other accepted systems: it must keep view top = canonical camera (D2-A), leave every `*_owns_camera` guard in place and be accepted
with the existing viewport/lifecycle verifiers plus the recorded trace replay.

**Decisions for Manager and James before dispatch:** D1 (recommended CENTER-relative leads), D2 (recommended keep canonical camera = view top; accept a documented 17 px framing offset), D3 (extra 4 rows at the bottom),
D4 (leave sign X at 0). Each is a documented adapter, not ROM behaviour.

## 8. Unresolved evidence and recommended next investigations

1. **R-C1-1 ledge pose `$19`:** meaning of `D368`, side rule, a natural THZ/GPZ reproduction (controlled `$4A33` sweep with `tools/oracle.py`). 12 seeded random THZ1 runs never entered it (negative evidence only).
2. Trace the support-owner exception (`D3C0`) on an MGHZ `$28` platform before I2 acceptance.
3. Camera limit handling outside THZ1 (the dropped-step rule is byte-verified and was sampled only inside the stage).
4. Tails (`$473C` branch of state 3, different leads/states) was not audited.
5. Mapped-object X policy (D4) needs one Windows comparison round, not research.
6. Real-hardware 50 Hz timing is not modelled; all counts are game updates.

## 9. Reproduction, results and limitations

```text
python tools/c1r_camera_trace.py ROM --write        # 23-29 s ; --check re-generated byte-identical
python tools/c1r_sign_registration.py ROM --poc <SonicChaos_POC @ ac021e1> --write   # about 2 s
python tools/c1r_build_register.py --write          # --check identical
python -m unittest tests.test_c1r_audit             # 18 tests OK, 0.03 s  (Python 3.13)
```

Results: trace regenerated identically; register/contract files regenerated identically; model replay 0 mismatches in 3,557 updates; sign comparison xor 0 in 5/5 base frames.
Limitations: approximate SMS harness (VDP, IRQ timing); THZ1/Sonic only for emulated claims; the POC was read, not executed (GameMaker not available here); Windows human acceptance was not run;
register `MATCH` rows marked `SOURCE_COMPARED` were not differentially executed in C1-R; no ROM bytes, tiles or artwork are stored anywhere in the new files (only counts, masks' summary numbers and hashes).

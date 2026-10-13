# FULLGAME-0 — Complete Game Gap Audit

Research repository: `sonic-chaos-reference` @ `0bb7390813a8fa4320ef35253a2c39598eee8e08` (accepted `main`)
POC repository: `SonicChaos_POC` @ `3381cfd7341b8c9bedf70eeb623c1357d5969875` (accepted `poc/special-stage-1`)
Machine-readable companion: [`data/fullgame-0/completeness-matrix.json`](../data/fullgame-0/completeness-matrix.json) (61 features, IDs used below).

Method: static source/documentation audit only. Nothing was executed, built or decoded; no POC, ROM-derived or `AGENTS.md` file was changed. Evidence labels: **POC-SRC** (read in accepted POC source), **RES** (accepted Research), **WIN-ACC** (AGENTS.md says Windows accepted), **GAP** (confirmed missing by static search), **UNAVAIL**.
Note: POC `main` is `03a6e7d` and is *not* the accepted baseline; every POC citation is to commit `3381cfd`.

---

## 1. Executive summary

1. **The accepted POC is a collection of fully accepted levels, not a campaign.** Every zone, boss, both endings and SS1 are Windows accepted, but almost all of that acceptance was reached through the *developer selector*. The natural path (title → slot select → act → clear → next act) only exists for THZ1–3.
2. **The single biggest gap is the post-clear spine (CAMP-02/04/05).** `chaos_acts()` lists only THZ1–3. After the act-clear flag, a normal session draws a developer overlay ("ACT n COMPLETE!") and stops; there is no results screen, no tally and no room change. The only tally object (`OBJ_menu_point_counter`) is an inherited openSonic screen reachable only from the legacy goal plate, with non-ROM bonus tables.
3. **Lives are partly wired, with a confirmed defect (LIFE-03).** Ring-100 extra lives are accepted (SS1). The type-`$10` parameter-`$02` monitor increments an unread shadow variable and never touches `global.life`. Research shows ring-100 (`$3104`) and that monitor run the same `$D299` +1 / `$A9` routine, so this is a real 1-UP bug. The goal-sign prize (LIFE-04), Continue (LIFE-09) and a faithful Game Over (LIFE-08) are absent. Whether the ROM awards lives for score is unknown (LIFE-06).
4. **State leaks on title return (CAMP-11).** Emerald bits and continues are plain RAM globals created if absent and never cleared, so a second run in one session inherits them. They are also not saved.
5. **Player mechanics are closer than AGENTS says.** Look up / crouch (states 3/4) and spin-dash exist; the real gaps are the look camera shift (unresearched) and **Super Peel-Out** (no entry path; only structural Research). A state-coverage diff is cheap and should precede G3 work.
6. **Audio is the largest unknown.** The AUDIO-0 ledger is accepted, but the POC has no music assets at all, routes only 3 request IDs, and still plays inherited openSonic effects by asset name. There is no ROM music playback path anywhere in Research.
7. **Presentation outside gameplay is inherited openSonic**: Sega logo, title, data select, Game Over. No ROM intro, title, character select or act cards exist, and none are researched yet.
8. **Tails is a full series, not a task.** The Chaos core and adapter are Sonic-only; retained Tails sprites/flight are legacy. Research has script-level structure but no Tails movement/flight/art study.
9. **Saves are mostly reusable** (5-slot INI + settings.ini) but store the wrong variables for Chaos and cap progression at 3 acts.

**Smallest practical path to a complete, naturally playable Sonic campaign** (silent audio and legacy title are acceptable at this stage):
`WP-01 natural spine` → `WP-03 lives API` → `WP-02 results/lives research (parallel)` → `WP-04 results+tally+prize` → `WP-05 Game Over/Continue` → `WP-06 SS2–SS5 (existing track)` → `WP-07 save v1`. Only WP-01 and WP-03 need no new Research; WP-04/05 need one bounded Research (RES-R0/R1). Everything else (G3–G6, G8, G9) improves faithfulness but does not block playability.

---

## 2. Feature-completeness matrix

Status legend: ACCEPTED · IMPLEMENTED—UNVERIFIED · PARTIAL · MISSING · UNRESOLVED · PC ENHANCEMENT. Kind: **C** canonical SMS, **A** GameMaker adapter/inherited engine, **E** PC enhancement.

| ID | Feature | K | Status | Cx | MS |
|---|---|---|---|---|---|
| CAMP-01 | Title → slot select → first act | A | PARTIAL | M | G1 |
| CAMP-02 | Natural act table, all 18 acts | A | **MISSING** | S | G1 |
| CAMP-03 | Act-clear chain ($18→$19→$20→flag) | C | ACCEPTED | S | G1 |
| CAMP-04 | Post-clear wait, results screen, tally | C | **MISSING** | L | G1 |
| CAMP-05 | Next-act progression / zone rollover | C | PARTIAL | M | G1 |
| CAMP-06 | Boss clear bonus tally | C | PARTIAL | M | G1 |
| CAMP-07 | Special Stage 1 entry/play/results/return | C | ACCEPTED | S | G1 |
| CAMP-08 | Special Stages 2–5 | C | UNRESOLVED | M×4 | G1 |
| CAMP-09 | Emerald bits / continues carried | C | PARTIAL | S | G1 |
| CAMP-10 | Ending routes + title return | C | ACCEPTED | S | G1 |
| CAMP-11 | Title return → New Game reset | C | **MISSING** | S | G1 |
| CAMP-12 | Developer path vs campaign path | A | PARTIAL | S | G1 |
| LIFE-01 | Life counter ownership / start value | C | PARTIAL | S | G2 |
| LIFE-02 | 100-ring extra life, cap 99 | C | ACCEPTED | S | G2 |
| LIFE-03 | 1-UP monitor ($10 param $02) | C | PARTIAL (defect) | S | G2 |
| LIFE-04 | Goal-sign prize + retry | C | **MISSING** | M | G2 |
| LIFE-05 | Score accumulation | C | IMPL—UNVERIFIED | S | G2 |
| LIFE-06 | Score-threshold extra life | C | UNRESOLVED | ? | G2 |
| LIFE-07 | Death → life loss → restart | C | IMPL—UNVERIFIED | S | G2 |
| LIFE-08 | Game Over screen | A | PARTIAL | M | G2 |
| LIFE-09 | Continue | C | **MISSING** | M | G2 |
| LIFE-10 | 9:59 time-over rule | C | UNRESOLVED | S | G2 |
| PLAY-01 | Look up (+camera) | C | PARTIAL | S | G3 |
| PLAY-02 | Crouch / spin-dash entry | C | IMPL—UNVERIFIED | S | G3 |
| PLAY-03 | Super Peel-Out | C | **MISSING** | L | G3 |
| PLAY-04 | State-script coverage vs core | C | UNRESOLVED | S | G3 |
| PLAY-05 | Animation completeness | C | UNRESOLVED | S | G3 |
| PLAY-06 | Isometric-platform fall presentation | C | UNRESOLVED | S | G8 |
| PLAY-07 | Hurt-landing extra vy=0 write | C | IMPL—UNVERIFIED | S | G8 |
| AUD-01 | Request ledger (70 IDs) | C | ACCEPTED | S | G4 |
| AUD-02 | Request→playback router | A | PARTIAL | M | G4 |
| AUD-03 | Music (31 IDs) | C | **MISSING** | ? | G4 |
| AUD-04 | SFX fidelity | C | PARTIAL | M | G4 |
| AUD-05 | Fades/loops/transitions | C | PARTIAL | M | G4 |
| PRES-01 | ROM intro animation | C | **MISSING** | L | G5 |
| PRES-02 | Title screen | C | **MISSING** | M | G5 |
| PRES-03 | Character selection | C | **MISSING** | M | G5 |
| PRES-04 | Act title cards | C | **MISSING** | M | G5 |
| PRES-05 | SS results cards | C | ACCEPTED | S | G5 |
| PRES-06 | Ending integration | C | ACCEPTED | S | G5 |
| PRES-07 | In-level HUD fidelity | C | UNRESOLVED | S | G8 |
| TAIL-01 | Playable Tails in Chaos core | C | **MISSING** | L | G6 |
| TAIL-02 | Tails ROM research | C | PARTIAL | L | G6 |
| TAIL-03 | Tails progression differences | C | PARTIAL | M | G6 |
| SAVE-01 | Slot save/load | A | PARTIAL | M | G7 |
| SAVE-02 | Options persistence | E | PARTIAL | S | G7 |
| SAVE-03 | Input remapping | E | **MISSING** | M | G7 |
| SAVE-04 | Display configuration | E | PARTIAL | S | G7 |
| SAVE-05 | Mid-level savestate | E | PC ENHANCEMENT (out of scope) | – | G7 |
| BUG-01…11 | Deferred issues (see §3.4) | mixed | see §3.4 | S–M | G8 |
| RC-01 | Release-candidate gate | A | MISSING | M | G9 |

Counts (61 JSON rows): ACCEPTED 8 · IMPLEMENTED—UNVERIFIED 6 · PARTIAL 17 · MISSING 17 · UNRESOLVED 12 · PC ENHANCEMENT 1.

---

## 3. Findings

### 3.1 Confirmed missing / incomplete functionality (static-evidence)

**A. Campaign and scoring**

- **CAMP-02** `chaos_acts()` has three entries (THZ1–3). `chaos_act_clamp()` clamps saved progression to 3; `chaos_act_index_for_room()` returns 0 for every other zone, so `chaos_act_complete()` never saves progress there. The 18-act order exists only in `chaos_debug_entries()`.
- **CAMP-04/05** Non-debug clear: `chaos_act_complete()` sets `chaosComplete`, saves THZ progress, and the HUD shows a developer overlay. Developer sessions return to the selector after 90 updates. No `room_goto` to the next act exists outside `OBJ_menu_point_counter.Alarm_11`, which is only reached from the inherited goal plate.
- **Ordinary results/tally is not ROM-based.** Inherited `OBJ_menu_point_counter` pays 100 points per ring and a lookup-table time bonus; the ROM runs `$14AE` (198-frame wait) → `$32F9` → `$2D08` with BCD `$27E5`/`$27E2` steps (RES `docs/object-18-act-clear.md`). SS1 already has an accepted tally/cards implementation that can seed the shared version.
- **Boss bonus (CAMP-06):** `chaos_boss_bonus()` fills `global.chaosBossBonus`, and each boss clear computes `global.chaosBossClearScore = ring*10 + steps + 500` (a POC-side formula not shown to be ROM-derived). Neither is added to `score` or displayed; nothing reads them.
- **SS gating (CAMP-08):** `chaos_ss_ring_counter_tick()` calls `continue` whenever the selected stage is not SS1, so after SS1 success natural play never offers SS2+. The ending requires all five bits for the full route, so SS2–SS5 are on the critical path to the good ending (the partial ending is reachable now).
- **State handling (CAMP-09/11):** `chaosCollectedFlags` and `chaosContinues` are created only if absent (SS1 install) and never reset; `SCR_save_game` persists the legacy `chaoEmerald` variable, not these.
- **Extra lives — ownership map (LIFE-\*).** Today a life can be added by: (1) `chaos_ss_ring_counter_tick()` (ring ≥ 100, cap 99, accepted); (2) legacy `OBJ_monitor_life` / `OBJ_plate` (not used by the Chaos path); (3) the inherited `OBJ_count_rings` "hundred" path (bypassed inside Chaos levels). A life is *not* added by the type-`$10` parameter-`$02` monitor (writes `chaosType10D299`, which is never read), nor by the goal-sign prize (deferred), nor by score. Lives are consumed by `OBJ_player_death` (`life-1`; restart if `life>0`). There is no central award function. Recommendation: one `chaos_award_life()` / `chaos_award_score()` owner before any further wiring.
- **Research inconsistency to fix (docs only):** `docs/object-18-act-clear.md` labels `$D2C3` "lives" and leaves `$D299` unnamed; `docs/special-stages-progression-audit.md` (later, EMULATED) names `$D2C3` "continues". The ring-counter audit (`$3104` = +1 life) plus the parameter-`$02` monitor makes `$D299` the lives counter. Reconcile in RES-R0.
- **Continue (LIFE-09)** is documented (EMULATED: consume `$D2C3`, lives → 3, score cleared, `$D2CC` kept) and the SS results card already draws continue icons, but nothing consumes the value. Game Over is the inherited screen (90 updates → title).
- **Death/time (LIFE-07/10):** inherited rules; not compared with ROM resets or the "3 lives = 3 attempts" count.

**B. Mechanics**

- **Look up / down.** AGENTS.md says "not implemented", but the Chaos core has states 3/4 with the Up/Down-held transitions and the adapter selects `SPR_player_up`/`SPR_player_down`. What was *not* found is any camera look-shift. Treat as PARTIAL and verify in Windows before commissioning anything. (Suggest correcting AGENTS.)
- **Super Peel-Out.** MISSING: states `$15`/`$1A` (decimal 21/26) are only excluded in two core guards. Research has structure only (setters `$46CE`/`$46E2`, attack bit kept, aura object after a very long hold, "UNRESOLVED long hold"). Narrow question for RES-R3: input combination, charge duration, release speed table, frame/animation scripts, sound, aura.
- **State-coverage diff (PLAY-04).** `data/sonic-state-scripts.csv` has 61 Sonic states; a literal-reference scan finds 27 never named in `SCR_chaos_core.gml` (`$00,$18,$19,$23,$24,$26,$27,$29–$3C`). Many are plausibly ending/boss/unused states handled elsewhere. This is a cheap, bounded static task and the right first step of G3.
- **Isometric-platform fall (PLAY-06):** an unverified observation, not a confirmed missing mechanic.

**C. Audio and presentation**

- Canonical request IDs: ledger accepted (70). POC playback is wired for `$A4`, `$A6`, `$BF` plus `$F8`; 17 distinct IDs are *recorded* at 39 call sites (`chaosLastSoundRequest`) with no sound. Intentionally silent: SS `$8F/$8A/$86`, ending `$8D/$9A/$98`, all level/boss music.
- Sound effects *are* inherited from openSonicSMS: 21 resources in `sounds/` (`SFX_ring`, `SFX_sonic_jump`, `SFX_sonic_spin_dash`, `SND_super_sonic_trans`, …), triggered by legacy code in `OBJ_player_char`, `SCR_physics_*`, `OBJ_monitor_*`. They are not keyed to ROM IDs and their fidelity versus the SMS sounds is unverified. There are **zero music assets**.
- Intro, title, data select, Game Over: inherited art/flow. Act title cards: no resource. In-level HUD: inherited objects.
- Available support: title entry `$04B4→$3065`, request IDs for title/select/continue (RES `audio-request-audit.md`), DECOMP-1B `level_intro_setup $06C7`. No extracted screens, graphics or timing.

**D. Tails.** Chaos core/adapter gate on `global.player == 1`; developer selector forces player 1; `SCR_player_sprites_tails` and Tails flight in `SCR_physics_speed` are legacy. Research available: DECOMP-1C parsed 109 Sonic/Tails scripts (Tails is object type 2), Tails EEZ ending scripts, `$D2C8` character byte, SS entry Sonic-only, ending `$8D` shared. Not available: movement tables, flight/carry rules, art extraction, boss/object deltas, progression/prize differences. Sonic mechanics cannot be reused unchanged (flight, SS ineligibility, different ending path, different animation/art).

**E. Saves and PC.** Reusable as-is: `saveGameN.ini` (`classicMode`: life, score, zoneGoto, …), `settings.ini` (screenSize, windowSize, buttons, music, saveGame), Delete button, data-select UI, `SCR_screen` window/aspect modes. Missing: Chaos emerald bits and continues, character, 18-act progression, versioning, input remap (hard-coded in `SCR_buttons`), separate volumes, fullscreen toggle (none found).

**Recommended initial save model (act boundary only):** write once, at `chaos_act_complete()`/after results, in non-debug sessions only: `{version, slot, character, next_act_index(1..18, 19=ending), lives, score, collected_bits (D2CC), continues (D2C3), settings_hash?}`; load = start at `next_act_index` with rings 0, timer 0, no powers, no checkpoint (the ROM drops rings, timer and active power-ups on Special Stage return; confirm for ordinary act boundaries in RES-R0). Reuse the INI with a new `[chaos]` section, keep the legacy section untouched, and write `version=1`. Continue = load slot; New Game = reset the slot (ROM `$2A00`). Nothing mid-level.

### 3.2 Implemented functionality requiring end-to-end testing

- Natural THZ1 → THZ2 → THZ3 via data-select START (the only fully natural chain).
- SS1 natural entry (100 rings) → return to the next act, across all six zones' return mappings (the POC covers THZ1 and developer fixtures).
- Death → restart → Game Over → title; life bookkeeping across 3 lives.
- Score accumulation across acts and persistence into the save slot (INI float/real handling, `score` is a bare global).
- Ring-100 behaviour combined with monitors (+10) and Large Rings in zones other than SS1.
- Both ending routes entered from a *natural* EEZ3 arrival (currently reached via selector).
- Look-up/crouch visuals and camera on Windows.
- Whether inherited SFX fire at plausible moments (monitor, spring, spin-dash, death).

### 3.3 Research gaps (each a bounded assignment; none is a reverse-engineering project)

| ID | Question | Size |
|---|---|---|
| RES-R0 | Ordinary results card + tables (`$2D84/$32CA/$A3A0`), score-byte display scale, tally pacing/skip, sign-prize classes, `$D299`/`$D2C3` naming, new-game init (`$2A00`) incl. starting lives, whether `$262F` grants score lives, time-over rule | M |
| RES-R1 | Game Over (zone 7 type `$1F`) and Continue prompt (`$141D/$1487/$148E/$1491`) presentation and input | M |
| RES-R2 | Look up/down camera behaviour | S |
| RES-R3 | Super Peel-Out state machine | M |
| RES-R5 | Intro / title / character select / act title cards (+ attract mode existence) | L |
| RES-R6 | Tails series (movement/flight, art, deltas, progression) | L |
| RES-R4 | Music playback path — *only after* a product decision (Q6) | ? |

### 3.4 Deferred bugs and compliance (AGENTS.md cross-reference)

| Issue | Status | Class | Next step |
|---|---|---|---|
| AQZ monitor-break explosion renders black | Confirmed open | cosmetic | audit effect palette source (no Research) |
| Goal/sign off-centre in several zones | Confirmed open (visual); pan code already viewport-centred | cosmetic | fold into viewport compliance pass |
| Cross-boss widescreen review | Planned, not started | fidelity | after all SS accepted |
| Final viewport/presentation compliance | Planned | compliance | after boss review |
| SEZ Spring Shoes terrain lock | Unverified/unreproduced | not a blocker | deterministic capture first |
| Spring Shoes/monitor contact | Unresolved canonical status | not a blocker | group with shared contact study |
| Dynamic-object slot model | Confirmed, cosmetic | low | shared allocator if pursued |
| Downhill/fall presentation | Unreproduced; M2 traces identical to M1 | possible visual blocker if reproduced | record Windows route + trace |
| Isometric fall animation | Unverified observation | – | verify, then maybe Research |
| `$21` rebound oscillation | Unverified after AQZ P1 | – | Windows recheck |
| Enemy spawn/despawn visibility | Unverified | low | examples first |
| Hurt-landing extra `vy=0` | Confirmed (Research) | shared-player, small | narrow fix in G8 |
| Loop/curve diagonal entry | Canonical baseline | optional QoL | adapter only if desired |
| Terrain-ring feel; AQZ water feel | Canonical / matches ROM | none | do not tune |
| `$14` zero air accel, strip pass-through, monitor pop | Canonical | none | do not "fix" |

None of these blocks playability; BUG-05 is the only one that could become a gameplay blocker if reproduced.

---

## 4. Recommended work packages and order

Dependencies are in the JSON (`work_packages`). `R` = needs a Research assignment first.

| Order | Package | MS | Cx | Depends | Research |
|---|---|---|---|---|---|
| 1 | **WP-01 CAMPAIGN-1 natural spine** — 18-act natural table, non-debug clear → next act, boss/EEZ3 handoffs, New Game & title reset of bits/continues/score, interim results using existing SS-style card, verifier | G1 | M | – | no |
| 1‖ | **WP-02 RESULTS-LIVES research** (RES-R0 + RES-R1) | G1/G2 | M | – | yes |
| 2 | **WP-03 LIVES-1** — single award API, wire monitor `$02`, parity checks for death/restart | G2 | S | WP-01 | no |
| 3 | **WP-04 RESULTS-1** — faithful ordinary results, tally, sign prize | G1/G2 | L | WP-01, WP-02 | R0 |
| 4 | **WP-05 GAMEOVER-CONTINUE-1** | G2 | M | WP-02, WP-03 | R1 |
| ‖ | **WP-06 SS2–SS5** (existing track; generalise the SS gate) | G1 | M×4 | WP-01 | no |
| 5 | **WP-07 SAVE-1** act-boundary save | G7 | S | WP-01, WP-03 | no |
| 6 | **WP-08** state-coverage diff + look up/down verification (RES-R2) | G3 | S | – | small |
| 7 | **WP-09** Super Peel-Out (RES-R3 first) | G3 | L | WP-08 | R3 |
| 8 | **WP-10** audio router + SFX map | G4 | M | – | no |
| 9 | **WP-14** options (remap, fullscreen, volumes) | G7 | M | – | no |
| 10 | **WP-12** presentation series (RES-R5 first) | G5 | L | WP-01 | R5 |
| 11 | **WP-11** music strategy/execution | G4 | ? | WP-10 | decision first |
| 12 | **WP-15** deferred bugs, cross-boss review, viewport pass | G8 | M | WP-06 | no |
| 13 | **WP-16** Original Mode RC | G9 | M | most | no |
| later | **WP-13** Tails series (RES-R6 first) | G6 | L | WP-12 | R6 |

Refined milestone grouping follows the proposed G0–G9 unchanged; the one adjustment is that **results/tally spans G1 and G2** (it is both a progression and a score feature), and SS2–SS5 are tracked under G1 because the full ending depends on them.

Complexity key: S ≈ days, M ≈ one milestone with one Windows gate, L ≈ multiple gates and/or a Research series, ? = needs a decision before sizing.

---

## 5. Complexity estimates (summary)

Small: CAMP-02/11, LIFE-01/03/05, PLAY-02/04, SAVE-02/04, most closure items.
Medium: CAMP-01/05/06, LIFE-04/08/09, AUD-02/04/05, PRES-02/03/04, SAVE-01/03, SS2–5 each, WP-15.
Large: CAMP-04 (with RES-R0), PLAY-03, PRES-01, TAIL-01/02.
Unknown: AUD-03 music, LIFE-06 score lives, BUG-05/07.

---

## 6. Explicit unresolved questions

1. ROM starting lives / new-game initialisation; confirm `$D299` = lives, `$D2C3` = continues.
2. Does the ROM award extra lives from score? (Not asserted either way.)
3. Score display scale and whether the SMS HUD shows score.
4. ROM time-over rule versus the inherited 9:59 kill.
5. What exactly is the user-reported extra-life problem? Confirmed candidate: 1-UP monitor never reaches `global.life` (LIFE-03). A repro or description would let us rule others in or out.
6. Music strategy: silence, converted tracks, or a ROM-driver playback path — a product/legal decision before any Research.
7. Does the ROM shift the camera on look up/down?
8. Super Peel-Out inputs and parameters.
9. Is Tails in scope for Original Mode v1, or a later release?
10. Asset provenance/distribution policy for ROM-derived data in a PC release (the POC embeds generated ROM-derived tables as GML data).
11. Do inherited SFX trigger at ROM-correct moments?
12. Does the ROM have an attract/demo mode or act title cards?
13. SS2 state (unaccepted branch not examined).

---

## 7. Handover

### Suggested first three assignments

1. **CAMPAIGN-1 (POC, WP-01)** — natural 18-act spine and New Game/title reset. No new Research needed; all next-zone destinations are in accepted boss audits. Windows gate: play THZ1 → THZ3 → GPZ1 from data-select START and verify a second run starts clean.
2. **RESULTS-LIVES-R0/R1 (Research, WP-02)** — one bounded research package covering the items in §3.3. Runs in parallel with #1.
3. **LIVES-1 (POC, WP-03)** — central life/score owner, fix the 1-UP monitor, parity-check death/restart. Small; unlocks Game Over/Continue and save v1. (SS2–SS5 continue as their own track.)

### AGENTS.md candidate updates

- Replace "Look up/down is not currently implemented" with: states 3/4 and sprites exist; camera shift unresearched/unverified.
- Add: "Natural campaign path currently covers THZ1–3 only (`chaos_acts()`); developer selector is the only route to other zones. Non-debug clear has no results/transition."
- Add: "`$D299` = lives (BCD, `$3104`), `$D2C3` = continues; reconcile older Research wording."
- Add: "Life/score changes must go through one owner; type-`$10` param `$02` currently does not."
- Note: POC `main` (`03a6e7d`) is not the accepted tip; accepted is `poc/special-stage-1`.
- Add pointer to this audit and the matrix.

### Evidence unavailable to this audit

SS2 branch/worktree; local ROM and ignored caches (approval boards); GameMaker/Windows play; the user's extra-life repro; no tests were run. The `E:\…` paths in AGENTS.md were treated as documentation references only.

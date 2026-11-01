# Sonic Chaos — Current base-game finish register

> **OWNER PRIORITY REVISION — LATER 1 NOV 2026 (SUPERSEDES PARTS OF INITIAL REGISTER):** M6-E candidate `SonicChaos_POC:poc/m6e-choice-widescreen@a4c26e13bc323a9f736c613c279b447dd6aedef5` has **MANAGER GO; one brief Chief F5 pending**, not yet accepted. Chief's repeated natural play identifies **NEW HIGH-PRIORITY BASE BLOCKER: premature offscreen despawn/paused or reset enemy patrols and thrown rings lost above viewport**, with **GPZ3 high boss hit/ring recovery** as the main fairness case. Prior ROM-exact harnesses did not validate the Chief's current gameplay expectation; ROM-faithful culling that harms wide gameplay is eligible for **labelled bounded PC QoL**. Next substantive milestone **M6-F** follows M6-E F5 PASS; research can start read-only now. **AQZ Tails underwater palette concern PROVISIONALLY INACTIVE** by owner after reviewing original footage and prior automated tests; do not re-audit. **Attract demos and Sonic-3-style save/emerald unlock** explicitly **PARKED POST-BASE** at owner's direction. MGHZ3 widescreen roughness/first-start audio delay still parked. Full current [M6-E review + M6-F directive](m6e-review-m6f-offscreen-persistence-20261101.md). The earlier table below listing attract as the next base feature is superseded by this Chief decision; do not assign it ahead of culling.

**Authoritative planning snapshot: 1 November 2026 · Manager-san #8 · after Chief M6-D acceptance**

**This file is the CURRENT queue.** Older `AGENTS.md`, `ROADMAP.md`, `CURRENT_M5.md`, `MEMORY.md`, AUDIT-0 (93 rows) and AUDIT-1 reports preserve *historical* claims and milestone states, many superseded by later Chief acceptance; **they do not automatically authorize rework**. This register reconciles those archives, **Chief's own 21-item/12-believed-fixed shortlist**, current accepted POC, and still incomplete frontend work. Additional one or two owner observations are anticipated but **NOT YET PROVIDED**; do not guess them. Chief alone selects which optional polish items must precede a private “base complete” declaration.

## Baseline and what is already done

**Last Chief-accepted PRIVATE GameMaker source:** `jamesfarnhamlong/SonicChaos_POC:poc/m6d-speed-display-cleanup@7acdd39f469a74d41362f2998c6783d815b719bf`. Source branch SHA confirmed by Manager on 1-Nov; acceptance: Chief **“Success! All good”**, with native screenshot showing km/h panel in goal sign sequence. Parent M6-C2 `3cf379240c6e1e06b52a4b57fcfd087fcd1fffa2` foreground Robotnik black-bar occlusion separately Chief-F5 accepted. **M6-D becomes the ONLY production parent for next work**; G2/M6-C2 are historical accepted ancestors. No automatic POC main merge.

- Original known-use Master System soundtrack **25/25 Chief accepted**, native by default; original F2 catalog **63 playable programmes / 5 intentionally empty**. Never claim 37/37 original SFX natural-path exhaustion, or invent unused $8E usage.
- Sonic and Tails playable, six-zone campaign, five Special Stages, boss transitions, endings; previous M2/Q3 acceptance means **no fresh all-acts replay** without a concrete regression. Source/data and human acceptance scopes kept distinct.
- Original opening/title layers/animation and native music accepted; M6-C2 machine **passes behind black bars** in owner's F5.
- Goal sign child $19 original rolling **km/h** display restored and Chief accepted in M6-D, existing scoring/tally untouched (reference ROM 1:50 + 28 rings => 617); **RESULTS-001 now closed** after earlier manager erroneously claimed feature nonexistent.
- ALL developer-only keyboard shortcuts retired in M6-D while retaining normal input, Pause→Level Select and menu Sound Test. **FRONTEND-003 now closed**, even prior F3-gated exceptions. **AUDIO-001** full *known-use music* and **AUDIO-004** ring SFX no-current-complaint inactive; no further blanket audio rework.
- Chief's previously accepted widescreen **title, zone/results cards**, boss, normal playable presentation remain frozen; do not reopen `PRES-002` without new current screenshot. All previous 1,313 registered resources preserved and one original glyph atlas added (1,314).

## A. Known remaining or user-requested base/frontend work

| Queue | ID / milestone | Current disposition | Source/decision | Gate |
|---|---|---|---|---|
| **NOW — already assigned** | **M6-E character select 348×196 widescreen** | Current screen draws two **256×192 original backgrounds** centered in 348×196, black ±46px side margins, 2px vertical. Chief specifically requests extending it as the **last known 4:3 frontend screen**. Must preserve original center native-size art and Sonic/Tails actor positions, animations, palette, $82/$B4/$A0 audio and campaign handoff. | `docs/m6d-chief-acceptance-m6e-choice-wide-20261101.md`; `SCR_chaos_choice.gml`, original BG resources. | One coherent private candidate and brief Chief F5 Sonic/Tails visual+launch acceptance. Branch `poc/m6e-choice-widescreen` directly from M6-D. |
| **NEXT DECISION** | **FRONTEND-002 — original idle attract/demo sequences** | Genuine incomplete original frontend: title idle currently returns to opening, rather than replay authentic demonstrations. Research identified three original scenes (THZ1 Sonic / GPZ1 Tails / SEZ1 Sonic), but original held/fresh input consumption does **not** replay as a trivial one-pair-per-update stream. Deliberately deferred M3-B, not a current gameplay crash. If **complete source-original frontend** is Chief's base criterion, this is a meaningful remaining feature; if “playable base” only, may stay explicit documented exception. | `SonicChaos_POC:docs/m3-frontend-report.md`, `OBJ_menu_title/Step_0.gml` (no-input demo boundary goes to opening). | **Chief priority choice** after M6-E and owner's remaining 1–2 items. No fake recordings or broad physics changes. |
| **OWNER INPUT PENDING** | Chief's “one or two things left” | Not yet specified. | Today's owner statement. | Capture exact symptoms/features before any new assignment; do not presume. |

## B. Six IDs still retained from Chief's originally titled nine after later accepted M6-C2/D

| ID | Current state | Action |
|---|---|---|
| **MGHZ-007** | Original boss approach **works**, but Chief dislikes messy/abrupt **348-pixel widescreen** composition. Original/G2 clips explain pit/pole, $56 boss vertical descent and a source-original1px vs widescreen4px pan adapter. No exact actionable drawing defect proved. | **Parked, explicitly NOT “fixed/perfect.”** Revisit as owner-guided aesthetic polish, not as mandatory speculative ROM parity correction. |
| **SEZ-002** | Historical Spring Shoes + monitor break/wide contact complaint; M6-B fresh **1,452 original Z80 callback cases** match **2,904 GameMaker width checks**, but exact historic play route not recovered. | Retain as historical/monitor **only if a new current route occurs**. No generic hitbox tweak or retest. |
| **SS-001** | Historical Special Stage 3 invincibility-monitor embedding; 28 bounded seeded routes did **not** reproduce reported persistent symptom. | Retain historical only; no active fix without exact occurrence. |
| **PLAYER-001** | Rebound/kill/pass-through feels inconsistent in historic reports; source supports contact posture/timing variation, exact symptom not paired against ROM. | Retain historical only; not an active proved bug. |
| **FRONTEND-002** | Actual original attract/demo feature absent. | Active **optional-vs-base requirement decision**, above. |
| **AUDIO-006** | Split two independent issues: **first-launch perceptible audio/onset delay** confirmed by Chief (does not recur during later music); and F8 raw CPU AF/carry discrepancy in exact audio comparison, no demonstrated PCM mismatch. | First-launch delay **parked final presentation polish**; if addressed, instrument startup before choosing silent cards/blank waits. F8 low-level driver exception retained as **technical-only**, not a missing audible track. |

**Three additional entries from the nine are now CLOSED after Chief evidence / source correction:** **OPENING-001** foreground border M6-C2 F5 PASS, **RESULTS-001** original $19 km/h display M6-D F5 PASS, **FRONTEND-003** all dev-only keyboard shortcuts removed M6-D F5 PASS. Do not keep them in the active-issues count.

## C. Chief's 12 bold/blank “believed fixed” entries — inactive by owner preference

`EARLY-011` red spring green/opaque rectangle; `MGHZ-006` slope/spring/facing oscillation; `SEZ-001` Spring Shoes fall-state lock; `SEZ-003` extra crumble shards; `AQZ-002` terrain-ring animation; `PRES-002` widescreen title/cards; `PLAYER-002` slope vibration; `PLAYER-003` static diagonal spike contact; `PLAYER-004` moving-spike width/activation; `TAILS-006` original Spring Shoes monitor uncertainty; `AUDIO-001` broad original audio coverage; `AUDIO-004` historical ring-SFX latency.

**Owner wording = “I believe we've fixed”**, not proof every specific old natural route has been exhaustively disproved. Many have bounded source verification and/or later corrected art. **Inactive, no further batch audit or human testing** absent a new current problem.

## D. Older AGENTS/ROADMAP and audit exceptions: archival, NOT additional active backlog

- Historical pre-M5 docs still say original title/front choice, all audio, Rocket Shoes Tails conversion, Special Stages, results graphic and developer keyboard options were **planned**. These are now delivered/accepted in later source generations. Their old STOP/HOLD clauses and “only five Sound Test samples” text are **obsolete**. Read latest document links above before treating a dated milestone as current.
- Earlier M2/R evidence lists AQZ palette/underwater reversal, GPZ3 line artifacts, AQZ1 crumble side-stick, spring/Badnik oscillation, unidentified “SLZ1” priority, fragment ownership in some zones, goal-sign centering and three-second frame-$5E diagnostics. These are **historical hypotheses, canonical oddities, accepted bounded exceptions or not specifically reverified in current M6-D**. Chief's own issue triage, later test evidence and absence of fresh observations **do not justify activating any as new defects today**. E.g. sign world-right framing and $5E no-draw safety adaptation are knowingly accepted. Retain exact source provenance in prior documentation; if Chief reports a specific current issue, check that original route, not a blanket audit.
- Modern scoped technical exceptions: SS5 raw256 camera-X verifier up to2px; obsolete THZ3 raw camera-cap test; F8 AF carry with audio exact; opening first-audible onset observation; G2 original SFX natural trigger gaps ($B8 player state34, unidentified $A8/$B2/$C1 and unvisited natural cases). These **are not 100% green**, but neither evidence of a new currently audible/gameplay failure. Don't claim all original SFX naturally verified; do not demand massive new ROM replay in absence of a user-visible symptom.
- Historical source-distribution/provenance/legal questions around private GameMaker/ROM-derived assets and native PSG bridge are unresolved for **public redistribution**. Chief's original purpose is **personal, noncommercial learning and preservation**, public `sonic-chaos-reference` contains safe research only; **a public release is not assumed or authorized**. This is a *separate distribution decision*, not an obstacle to a privately complete playable base. Local private final archive/restoration proof and optionally approved branch/merge/tagging may be worthwhile at base freeze; **no auto main merge**.

## E. Later optional programme — not base blockers

- **M7 Windows quality-of-life / final private archive:** optional clean-build restoration smoke, input/display/audio preferences, save/resume and packaging; do not invent a commercial release obligation or promise public distribution.
- **M8 / Assistant Manager side initiatives:** Vita port (investigate modern YoYo Loader route), full accessible ROM decomp/disassembly, Master System/Game Gear slowdown-reduction patch. These are separate/parked and **not prerequisites** to the playable GameMaker base.
- Optional MGHZ widescreen aesthetic pass and startup onset masking are above, **owner-parked**. Do not automatically introduce silent cards or alter timing.

## F. Practical finish order and explicit decision rule

1. Complete **M6-E widescreen character choice** and Chief's one visual/launch acceptance, preserving M6-D.
2. Hear **Chief's still-unspecified one or two remaining base requests**; record exact desired outcome and prioritize deliberately.
3. Decide whether **authentic attract/demo playback** is a must for *Chief's personal base complete* or a documented original-fidelity exception for another day.
4. If Chief wishes, address parked **MGHZ3 presentation** and/or measured one-time **startup delay** as polish, not involuntary blockers. No blanket resurrecting 93 AUDIT-0 issues.
5. Once Chief confirms base definition satisfied, consider **one private canonical final checkpoint/manifest** (clean source, verify private assets restored, all accepted features available, known exceptions, branch/tag/merge choice); do not automatically publish private assets or merge main.

**Owner decisions always outrank historical assistant assumptions.** If a newly reported defect contradicts a source-only pass, give the reported visual symptom priority and investigate the specific gap (the original km/h miss is the cautionary example). Do not treat absence of current complaint as a mathematical proof of perfect source parity.

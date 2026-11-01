# Sonic Chaos — AUDIT-0 historical issue index

**Historical snapshot: 30 October 2026.** Supplied by Assistant Manager-san. This is an evidence-reconciliation register, not a fresh code audit or permission to fix everything.

**Full fidelity:** see `SonicChaos_AUDIT0_Full_Issue_Ledger.csv` (all 93 issue records and all 17 source columns).

Original source basis: seven available Manager threads, reference management documents and archived fidelity register. Manager #4 thread was not supplied.

Status counts: CLOSED: 55, CANONICAL / QoL: 14, RETEST: 7, OPEN: 7, DEFERRED: 3, ACTIVE M5: 2, SOURCE GAP: 2, TEST EXCEPTION: 2, INFRASTRUCTURE: 1.

| ID | Title | Area | Status group | Current status | Severity | Next action | First/key source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EARLY-001 | THZ terrain palette incorrect | THZ / Graphics | CLOSED | CLOSED | Low | No action unless regression appears. | Thread 1 - Sonic Chaos Remake Idea.md L275-282 |
| EARLY-002 | Spring proximity crash (SPR_player_jump scope) | Player / Springs | CLOSED | CLOSED | Critical | No action. | Thread 1 - Sonic Chaos Remake Idea.md L353-367 |
| EARLY-003 | Loops/curved ground embed Sonic | Player / Terrain | CLOSED | CLOSED / SUPERSEDED | High | Retain only the separate diagonal-entry canonical/QoL issue. | Thread 1 - Sonic Chaos Remake Idea.md L378-389 |
| EARLY-004 | Spring directions/power wrong | Player / Springs | CLOSED | CLOSED | High | No action unless a specific spring contradicts ROM. | Thread 1 - Sonic Chaos Remake Idea.md L378-389 |
| EARLY-005 | Apparently missing end spring | THZ / Objects | CANONICAL / QoL | CLOSED — CANONICAL | Low | Keep canonical hidden presentation. | Thread 1 - Sonic Chaos Remake Idea.md L1116-1133 |
| EARLY-006 | Moving spikes absent / wrong presentation | THZ / Hazards | CLOSED | CLOSED | Medium | No action unless exact placement fails. | Thread 1 - Sonic Chaos Remake Idea.md L1116-1133 |
| EARLY-007 | Spring and roll animations differ from ROM | Player / Animation | CLOSED | CLOSED / MOSTLY | Medium | Spot-check in final fidelity pass; no known blocker. | Thread 1 - Sonic Chaos Remake Idea.md L1201-1210 |
| EARLY-008 | Noncanonical spring/spike placement | THZ / Data | CLOSED | CLOSED | High | No hand-authored placement changes. | Thread 1 - Sonic Chaos Remake Idea.md L1235-1240 |
| EARLY-009 | Missing sprite files + Level Select data-card crash | Frontend / Assets | CLOSED | CLOSED | Critical | No action. | Thread 1 - Sonic Chaos Remake Idea.md L1410-1431 |
| EARLY-010 | Spike vertical offset corrupts collision | THZ / Hazards | CLOSED | CLOSED | High | No action unless reproduced. | Thread 1 - Sonic Chaos Remake Idea.md L1481-1488 |
| EARLY-011 | Spring green box / opaque background artifact | THZ / Graphics | RETEST | NEEDS RETEST | Low | One final visual spot-check; close if absent. | Thread 1 - Sonic Chaos Remake Idea.md L1512-1522 |
| THZ-001 | Monitor side-contact wobble/phasing | Shared monitors | CLOSED | CLOSED | High | No action. | Thread 2 - Manager-San - Plan Extraction Tasks.md L1-53 |
| THZ-002 | Flying bee renders too high | THZ / Type $27 | CLOSED | CLOSED | Medium | No action. | Thread 2 / early THZ object milestone |
| THZ-003 | Flying bee endlessly respawns nearby | THZ / Type $27 | CLOSED | CLOSED | High | No action. | Thread 2 / early THZ object milestone |
| THZ-004 | Spring can kill Sonic above top of screen | Player / Death boundary | CLOSED | CLOSED | High | No action. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L4366-4376 |
| THZ-005 | Look up/down missing | Player / Camera | CLOSED | CLOSED | Medium | No action. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L4366-4376 |
| THZ-006 | Super Peel-Out missing | Player / Controls | CLOSED | CLOSED | Medium | No action. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L4366-4376 |
| THZ-007 | Diagonal loop/curved-slope entry can stop or glitch | Player / Terrain | CANONICAL / QoL | CANONICAL — QoL CANDIDATE | Low | Do not 'fix' in fidelity pass; optionally design labelled QoL later. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L4366-4376 |
| THZ-008 | Terrain ring pickup feels narrow/floaty | Rings | CANONICAL / QoL | CANONICAL / ACCEPTED | Low | No change without exact paired counterexample. | https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/52b68536d656a98eb74b280e8c297eabe6d122ef/archive/management/planning-20261022-v0.1/FIDELITY_REGISTER.md |
| THZ-009 | Bee hit from above while apparently unrolled | Enemy contact | CLOSED | CLOSED / SUPERSEDED | Medium | No action unless identical contact case fails. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L4997-5008 |
| THZ-010 | Monitor/terrain push-pull snag | Shared monitors | CLOSED | CLOSED — SHARED FIX | High | Re-test the old SS3 embedding route if easy; otherwise closed causally. | https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/52b68536d656a98eb74b280e8c297eabe6d122ef/archive/management/planning-20261022-v0.1/FIDELITY_REGISTER.md |
| THZ-011 | Goal sign appears off-centre/right-biased in widescreen | Act clear / Camera | CANONICAL / QoL | KNOWN-ADAPTER / QoL | Low | Keep as QoL/presentation candidate; capture exact act before changing. | Manager-San #5 - Fixes & Sound.md L12736-12766 |
| THZ-012 | Sonic falls/runs into black void on zone exit | Act clear / Camera | CLOSED | CLOSED | High | No action unless reproduced. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L4997-5008 |
| THZ-013 | THZ3 boss patrol wrong at widescreen | THZ3 boss | CLOSED | CLOSED-348 | High | No action. | Manager-San #5 - Fixes & Sound.md L13321-13329 |
| THZ-014 | THZ3 boss walk-on/entrance visually wrong | THZ3 boss | CLOSED | CLOSED | Medium | No action. | Manager #5 C3-BX sequence |
| THZ-015 | Goal sign artwork incomplete | Act clear / Graphics | CLOSED | CLOSED | Low | No action. | Manager #5 C1-I |
| GPZ-001 | GPZ graphics/map corruption from pointer conversion | GPZ / Data pipeline | CLOSED | CLOSED | Critical | Keep regression test. | Thread 3 GPZ mapping-pointer correction |
| GPZ-002 | Alternate vertical loop route missing | GPZ / Traversal | CLOSED | CLOSED | High | No action. | Thread 3 GPZ traversal pass |
| GPZ-003 | Surface $19 speed-strip/fall behaviour missing | GPZ / Traversal | CLOSED | CLOSED | High | No action; remember zero air acceleration is canonical. | Thread 3 GPZ traversal pass |
| GPZ-004 | Foreground pipe/deck layering flattened | GPZ / Presentation | CLOSED | CLOSED | Medium | No action. | Thread 3 GPZ traversal pass |
| GPZ-005 | GPZ terrain-ring animation timing/presentation wrong | GPZ / Rings | CLOSED | CLOSED | Low | No action. | Thread 3 GPZ traversal work |
| GPZ-006 | GPZ3 boss too central; right-thrown balls culled at 4:3 edge | GPZ3 boss | CLOSED | CLOSED-348 | High | No action. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L19878-19895 |
| GPZ-007 | Lost rings disappear immediately after damage | Shared hurt/rings | CLOSED | CLOSED | High | No action. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L19878-19895 |
| MGHZ-001 | Rising-platform contact into terrain behaves like glitch | MGHZ / Platforms | CANONICAL / QoL | CLOSED — CANONICAL | Medium | Preserve canonical behaviour. | Thread 3 MGHZ M1 follow-up |
| MGHZ-002 | Animated strip / horizontal seam / tiling artifact | MGHZ / Presentation | CLOSED | CLOSED | Low | No action. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L21971-21988 |
| MGHZ-003 | MGHZ sign clear not wired | MGHZ / Progression | CLOSED | CLOSED | High | No action. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L21971-21988 |
| MGHZ-004 | Spring Shoes animation wrong | Power-up / Presentation | CLOSED | CLOSED | Medium | No action. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L23999-24029 |
| MGHZ-005 | Finishing act with Spring Shoes can stall progression | Power-up / Act clear | CLOSED | CLOSED | High | No action; retain documented narrow already-awake canonical stall. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L23999-24029 |
| MGHZ-006 | Slope glitch + spring/jump/facing oscillation | Player / Presentation | OPEN | OPEN / DEFERRED | Medium | Reproduce deterministically during M6 before changing physics/presentation. | Thread 3 - Manager-San #2 - Folder Cleanup Plan.md L26059-26069 |
| MGHZ-007 | MGHZ3 tree/pit boss reveal is too early/abrupt | MGHZ3 boss / Camera | OPEN | OPEN / DEFERRED M6 | Medium | M6: recover/implement staged reveal without fake scenery. | Manager-San #5 - Fixes & Sound.md L10972-10978 |
| SEZ-001 | Spring Shoes fall-state terrain lock/no steering | SEZ / Player | RETEST | OPEN / RETEST | Medium | Reproduce exact route before any fix. | Thread 4 - Manager-san #3 & Knuckles - Project Handover Update.md L2503-2509 |
| SEZ-002 | Spring Shoes inconsistently break reward/monitor boxes / wide hit | SEZ / Contact | RETEST | OPEN / RETEST | Medium | Targeted retest after current baseline; classify contact vs presentation. | Thread 4 SEZ S3 discussion |
| SEZ-003 | Dynamic slot model yields extra crumble shards | SEZ / Scheduler | OPEN | OPEN / LOW | Low | Only fix with shared canonical allocator, not per-enemy hacks. | https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/52b68536d656a98eb74b280e8c297eabe6d122ef/archive/management/planning-20261022-v0.1/FIDELITY_REGISTER.md |
| AQZ-001 | Underwater palette double-change / missing water palette | AQZ / Presentation | CLOSED | CLOSED / MOSTLY | Medium | One final Sonic/Tails deep-water spot-check. | Thread 4 - Manager-san #3 & Knuckles - Project Handover Update.md L8782-8801 |
| AQZ-002 | AQZ terrain-ring animation appears too fast | AQZ / Rings | RETEST | NEEDS RETEST | Low | Compare with ROM once in M6; avoid tuning pickup geometry. | Thread 4 - Manager-san #3 & Knuckles - Project Handover Update.md L8782-8801 |
| AQZ-003 | AQZ lower routes/Act 3 initially impassable or missing mechanics | AQZ / Foundation | CLOSED | CLOSED | Critical | No action. | Thread 4 - Manager-san #3 & Knuckles - Project Handover Update.md L8782-8801 |
| AQZ-004 | Underwater Spin Dash reverses/rockets Sonic backward | AQZ / Controls | CLOSED | CLOSED-348 | High | No action. | Manager-San #5 - Fixes & Sound.md L12736-12766 |
| AQZ-005 | Underwater skim/turning feels overly twitchy or fast | AQZ / Physics | CANONICAL / QoL | CANONICAL/UNPROVEN | Low | Do not tune without paired route. | Thread 4 AQZ P1 F2/F3 |
| AQZ-006 | Wrong fall/spring animation and missing falling ceiling-spring dispatch | AQZ / Player | CLOSED | CLOSED | High | No action. | Thread 4 AQZ P1 audit/package |
| AQZ-007 | AQZ3 post-boss walk-off/camera freeze | AQZ3 / Camera | CLOSED | CLOSED | High | No action. | Manager #5 C3-BX work |
| EEZ-001 | EEZ3 boss warps in near centre / can fail to spawn at far right | EEZ3 boss | CLOSED | CLOSED | High | No action. | Thread 4 - Manager-san #3 & Knuckles - Project Handover Update.md L20070-20093 |
| EEZ-002 | EEZ3 phase-1 patrol/projectiles use 4:3 safe zone | EEZ3 boss | CLOSED | CLOSED | High | No action. | Thread 4 - Manager-san #3 & Knuckles - Project Handover Update.md L20070-20093 |
| EEZ-003 | EEZ3 phase-2 flight targeting appears reversed | EEZ3 boss | CLOSED | CLOSED | High | No action. | Thread 4 - Manager-san #3 & Knuckles - Project Handover Update.md L20070-20093 |
| EEZ-004 | Final Robotnik chase/lift alignment and emerald drop fail | Ending | CLOSED | CLOSED | Critical | No action. | Thread 4 - Manager-san #3 & Knuckles - Project Handover Update.md L20070-20093 |
| EEZ-005 | Emerald collection loses race to death processing | Ending | CLOSED | CLOSED | Critical | No action. | Thread 4 P4F |
| SS-001 | SS3 invincibility-monitor embedding | Special Stages / Contact | RETEST | LIKELY RESOLVED / RETEST | Medium | Replay exact SS3 monitor if convenient; close if absent. | Manager-San #5 - Fixes & Sound.md L12736-12766 |
| SS-002 | SS3/SS5 tube junction inputs feel too strict | Special Stages / Input | CANONICAL / QoL | CANONICAL / NO CHANGE | Low | No fidelity change unless paired mismatch. | Manager-San #5 - Fixes & Sound.md L12736-12766 |
| SS-003 | SS4 clock monitor vertical seam | Special Stages / Presentation | CLOSED | CLOSED-348 | Low | No action. | Manager-San #5 - Fixes & Sound.md L13798-13811 |
| SS-004 | Special Stage Entry Fail | Special Stages | CANONICAL / QoL | CANONICAL — PRESERVE | Low | Classify as canonical quirk; only QoL-change if explicitly desired. | Thread 4 - Manager-san #3 & Knuckles - Project Handover Update.md L17531-17565 |
| SS-005 | Bead Worm can spawn with extra segment by route | Boss / Special route | CANONICAL / QoL | CANONICAL — PRESERVE | Low | Do not 'fix' unless current POC fails to reproduce and fidelity requires it. | Thread 4 - Manager-san #3 & Knuckles - Project Handover Update.md L17531-17565 |
| SS-006 | Silent Sneakers monitor glitch | Power-up / Audio | CANONICAL / QoL | CANONICAL / AUDIO REVIEW | Low | Tag in M5 audio acceptance as canonical-behaviour choice. | Thread 4 - Manager-san #3 & Knuckles - Project Handover Update.md L17531-17565 |
| PRES-001 | Title/results cards not filling 16:9 | Frontend / Results | CLOSED | CLOSED-348 | Medium | No action. | Manager-San #5 - Fixes & Sound.md L12736-12766 |
| PRES-002 | Zone title cards need 16:9 adjustment | Stage intro | RETEST | NEEDS RETEST / UNCLEAR | Low | Check one normal stage card at final polish. | Manager-San #5 - Fixes & Sound.md L12736-12766 |
| PLAYER-001 | Rebound / kill / pass-through outcomes seem inconsistent | Player / Enemy contact | OPEN | OPEN-OBS | Medium | Reproduce same enemy, position, state, velocity before any change. | Manager-San #5 - Fixes & Sound.md L12736-12766 |
| PLAYER-002 | Historical slope sticking/vibrating | Player / Terrain | OPEN | OPEN / PARTIAL | Medium | M6 paired ROM/POC route. | https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/52b68536d656a98eb74b280e8c297eabe6d122ef/archive/management/planning-20261022-v0.1/FIDELITY_REGISTER.md |
| PLAYER-003 | Diagonal static-spike contact oddity | Hazards | OPEN | OPEN-OBS | Medium | Only investigate if reproducible. | https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/52b68536d656a98eb74b280e8c297eabe6d122ef/archive/management/planning-20261022-v0.1/FIDELITY_REGISTER.md |
| PLAYER-004 | Moving-spike width/activation-phase mismatch | Hazards / Lifecycle | OPEN | OPEN-SOURCE | Low | Low priority M6 source review if visible. | https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/52b68536d656a98eb74b280e8c297eabe6d122ef/archive/management/planning-20261022-v0.1/FIDELITY_REGISTER.md |
| PLAYER-005 | State $14 has no air steering | Player | CANONICAL / QoL | CANONICAL — NO FIX | Low | QoL only if explicitly labelled. | Thread 3 player-fall-control audit |
| PLAYER-006 | State $14 can fall through certain strips | Player / Surface $19 | CANONICAL / QoL | CANONICAL — NO FIX | Low | Do not fix as defect. | Thread 3 player-fall-control audit |
| PLAYER-007 | Monitor/floor line can produce one-frame push or ~32px pop | Shared collision | CANONICAL / QoL | CANONICAL — NO FIX | Low | Only act on captured noncanonical repeated snag. | https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/52b68536d656a98eb74b280e8c297eabe6d122ef/AGENTS.md |
| TAILS-001 | Shift+T developer act selection unreliable | Developer UI | CLOSED | CLOSED | Medium | No action. | Manager-San #5 - Fixes & Sound.md L15238-15247 |
| TAILS-002 | Tails Rocket Shoes monitor should become Ring monitor | Tails / Monitors | CLOSED | CLOSED | High | No action. | Manager #5 M2 Package B clarification |
| TAILS-003 | Tails jumps/rebounds feel floaty/high | Tails / Physics | CLOSED | CLOSED / ACCEPTED | Medium | Reopen only with measured paired route. | Manager-San #5 - Fixes & Sound.md L15238-15247 |
| TAILS-004 | Tails ordinary-loop animation wrong | Tails / Animation | CLOSED | CLOSED | Medium | No action. | Manager #6 pre-Package F |
| TAILS-005 | Tails 1-UP monitor shows Sonic portrait | Tails / Presentation | CLOSED | CLOSED | Low | No action. | Manager #6 pre-Package F |
| TAILS-006 | Spring Shoes / monitors interaction uncertain for Tails | Tails / Equipment | DEFERRED | DEFERRED / UNCLEAR | Low | Locate Designer audit details before M6; test only if still relevant. | Manager #6 Designer audit scope |
| TAILS-007 | Tails act-clear frame $5E malformed original mapping | Tails / Act clear | CANONICAL / QoL | CANONICAL EXCEPTION / CLOSED M2 | Medium | Keep documented; do not 'repair' animation/collision unless new evidence. | Manager #6 R5/Package F |
| TAILS-008 | Intrusive M2 trace success popup | Diagnostics | CLOSED | CLOSED | Low | No action. | Manager #6 Package G |
| FRONTEND-001 | Character select confirms with B instead of Xbox A | Frontend | CLOSED | CLOSED | Low | No action. | Manager-san #6 - Final Polishes.md L1674-1688 |
| FRONTEND-002 | Attract/demo playback not implemented | Frontend | DEFERRED | DEFERRED (M3-B) | Low | Do after M5/M6 only if desired. | Manager-san #6 - Final Polishes.md L2665-2681 |
| FRONTEND-003 | F10 debug selector obsolete | Developer UI | RETEST | LIKELY CLOSED | Low | AUDIT-1 source check for F10 binding. | Thread 4 - Manager-san #3 & Knuckles - Project Handover Update.md L21336-21376 |
| AUDIO-001 | Authentic full in-game soundtrack/SFX incomplete | Audio | ACTIVE M5 | OPEN — ACTIVE M5 | High | Finish M5 final rollout; do not mix with M6 defect fixes. | https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/52b68536d656a98eb74b280e8c297eabe6d122ef/ROADMAP.md |
| AUDIO-002 | Sound Test can falsely report PLAYING/unavailable entries | Audio / F2 | CLOSED | CLOSED / SUPERSEDED | Medium | Preserve truthful labels during final M5 rollout. | Manager #7 B0 audit |
| AUDIO-003 | Death → stage card gap: missing $88 jingle | Audio / Transitions | CLOSED | CLOSED in A4B experiment | High | Ensure final M5 rollout retains this route. | Manager-san #6 - Final Polishes.md L9569-9576 |
| AUDIO-004 | Ring SFX feels slightly delayed | Audio / Latency | DEFERRED | PARKED — INCONCLUSIVE | Low | Only reopen for reproducible user-priority playback fault. | Manager-san #6 - Final Polishes.md L10067-10074 |
| AUDIO-005 | M4 pause doubles music speed; Motobug spring silent; exit crash | Audio runtime | CLOSED | CLOSED | Critical | Regression lock during final M5. | Manager-san #6 - Final Polishes.md L2124-2151 |
| AUDIO-006 | Opening onset / F8 carry edge cases | Audio driver | ACTIVE M5 | OPEN within M5 | Medium | Resolve or explicitly document in final M5 acceptance. | https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/52b68536d656a98eb74b280e8c297eabe6d122ef/ROADMAP.md |
| RESULTS-001 | Original end-of-zone KPH/speed display/mechanic absent | Results | SOURCE GAP | SOURCE GAP / VERIFY | Medium | Recover source/provenance, verify original ROM behaviour, then inspect current results implementation before authorising work. | Current audit request; no KPH/km/h/speed-display wording located in the seven supplied Manager-thread Markdown files |
| OPENING-001 | Robotnik layers above black widescreen bar | Opening cinematic | SOURCE GAP | SOURCE GAP / VERIFY | Low | Recover the omitted source (likely Manager #4 / project docs) or inspect opening draw order and run a targeted 348×196 retest. | Current audit request; exact wording not located in the seven supplied Manager-thread Markdown files |
| RESULTS-002 | Goal sign right-justified / Sonic can fall off-screen on exit | Act clear / Results | CLOSED | PARTLY CLOSED / QoL remains | Medium | Keep exit gameplay CLOSED unless reproduced. Treat sign centring as an explicit QoL/presentation decision, not a hidden fidelity bug. | Current user request + historical THZ exit reports |
| TEST-001 | SS5 256px camera differs by up to 2px | Verification | TEST EXCEPTION | TEST-EXCEPTION — RETAIN | Low | Retain failure until verifier-maintenance or source evidence. | https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/52b68536d656a98eb74b280e8c297eabe6d122ef/archive/management/planning-20261022-v0.1/FIDELITY_REGISTER.md |
| TEST-002 | THZ3 boss-clear 4px camera cap verifier obsolete | Verification | TEST EXCEPTION | TEST-EXCEPTION — RETAIN | Low | Fix test only in dedicated verifier-maintenance work. | https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/52b68536d656a98eb74b280e8c297eabe6d122ef/archive/management/planning-20261022-v0.1/FIDELITY_REGISTER.md |
| INFRA-001 | Standalone Igor GMAssetCompiler permission failure | Build environment | INFRASTRUCTURE | KNOWN ENVIRONMENT LIMITATION | Low | Do not weaken permissions; keep IDE compile gate. | Multiple Manager #2/#3 threads |

## Provenance and limitations

# Sonic Chaos AUDIT-0 — Historical Issue Reconciliation
**Date:** 2026-10-30  
**Purpose:** recover, deduplicate and classify historical defects/observations before any cleanup implementation.

## Evidence basis
- Seven supplied Manager-thread Markdown files.
- **88,359 lines / 1,386 messages / 3,782,434 characters.**
- Current `sonic-chaos-reference` management documents (`AGENTS.md`, `MEMORY.md`, `ROADMAP.md`) at Research `main` **52b68536d656a98eb74b280e8c297eabe6d122ef**.
- Archived `archive/management/planning-20261022-v0.1/FIDELITY_REGISTER.md`.

A dedicated **Manager #4 thread was not supplied**. Exact historical provenance for the user-recalled **KPH end-of-zone mechanic** and **Robotnik-over-black-widescreen-bar** issue was not found in the seven-file corpus. They are therefore marked **SOURCE GAP**, not guessed open/closed.

## Result
After obvious duplicate aliases were removed, AUDIT-0 contains **93 distinct issue records**:

- **CLOSED: 55**
- **CANONICAL / QoL: 14**
- **OPEN: 7**
- **RETEST: 7**
- **DEFERRED: 3**
- **ACTIVE M5: 2**
- **SOURCE GAP: 2**
- **TEST EXCEPTION: 2**
- **INFRASTRUCTURE: 1**

## Important reconciliations
- **Goal exit:** the historical Sonic-running/falling-off-screen behaviour is treated as closed by later state-$20/camera/victory-run work. **Goal-sign centring is not the same issue**: the archived fidelity register keeps it as a known widescreen adapter/QoL question.
- **Canonical oddities:** do not move them into the defect queue just because they look broken. Examples include state `$14` no-air-steering/strip pass-through, strict Special Stage junction behaviour, some loop-entry instability and the Tails frame `$5E` hazard.
- **MGHZ3 staged reveal:** still a real presentation item and intentionally deferred to M6.
- **Slope / rebound / oscillation family:** several observations remain open or require a modern targeted reproduction; they should be treated as a causal family rather than patched individually.
- **M5 audio:** remains the active current milestone. Do not mix audio completion with the later M6 fidelity cleanup.
- **Raw test exceptions:** stay visible and must not be described as green gameplay tests.

## AUDIT-1 recommendation
Do **not** give one agent “fix all bugs.” Use the ledger as a no-code verification queue:

1. **Frontend/results/opening:** KPH, Robotnik/bar draw order, goal framing, title-card widescreen.
2. **Player/contact:** rebound variation, slope sticking/oscillation, SS3 monitor, static/moving spikes.
3. **Zone presentation:** MGHZ3 reveal, AQZ ring animation, priority/layering, remaining breakable presentation.
4. **Canonical/QoL review:** decide explicitly which authentic quirks should remain and which deserve labelled QoL adapters.
5. **Audio:** finish separately under the current M5 authority.

Every AUDIT-1 row should end with one of:
`Verified resolved`, `Still present`, `Partial`, `No code change needed`, `Needs Windows retest`, `Source gap`, or `Superseded`.

Only after AUDIT-1 should we authorize a **batched spot-fix milestone**.

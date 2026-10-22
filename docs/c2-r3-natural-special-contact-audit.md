# C2-R3 — Natural contact routes and special surfaces

Research-only checkpoint, 22 October 2026. Stop for Manager review.

Research parent: `02a586ffa133f40d93566a4a5bec7241d8236dcf`; isolated branch `research/c2-r3-natural-special-contact`. POC: `4eb684911c5785667181b9d3f940b1dc820e66d1` (`poc/c2-e1-contact-extent`). Both were checked locally at the assigned SHAs, with clean status. C2-R1/R2 reports and their evidence/registers were read as scoped historical evidence. C2-E1's accepted extent changes remain closed; older C2-R1 gap rows are not new findings against C2-E1.

## Decision

**No implementation-worthy discrepancy is proven. Recommend moving to bounded cross-zone/campaign QA, keeping Chief's visible oscillation and slope-sticking observations OPEN.** No Designer physics package is recommended, and no diagnostic is implemented.

A continuous, input-only source-host route from THZ1's act start reaches a real mapped patrol stomp at (1248,862). Separate routes exercise slope release, ordinary jump/fall and a terrain spring. There were no consecutive reversals with at least one pixel of movement in each direction, and no sustained consecutive facing flip sequence, in these attempts. This limited negative result does not reject the historical observation or explain it with C2-R2's canonical-supported 1/16-pixel cycle.

Natural **mapped $26 spring** reachability remains unresolved: their actual placements were loaded unchanged, but none of the bounded routes launched one. The terrain spring reached at X≈934 is a different system. C2-R2's seeded mapped-spring launches must not be relabelled as natural routes.

Four selected special-contact samples agree with existing original-ROM contracts: SEZ crumble timing/hold, AQZ entry/equality and signed-speed gate, MGHZ ceiling-spike gate, and EEZ attached carrier/action detach. These are limited controlled replays, not all-route parity.

## Evidence, reproduction and limits

From this Research worktree:

```powershell
node tools/c2r3_natural_routes.js ../SonicChaos_POC_c2e1
node tools/c2r3_special_cases.js ../SonicChaos_POC_c2e1
node tools/c2r3_replay_check.js ../SonicChaos_POC_c2e1
node tools/c2r3_register.js ../SonicChaos_POC_c2e1
python -m unittest discover -s tests -p test_c2r3_contact.py
```

Outputs: [natural summary](../data/c2r3/natural-summary.json), [compressed complete routes](../data/c2r3/natural-attempts.json.gz), [first writers and width difference](../data/c2r3/analysis.json), [special cases](../data/c2r3/special-cases.json), [uninstrumented replay](../data/c2r3/replay-check.json), [scoped register and source hashes](../data/c2r3/fidelity-register.json). Decompress the gzip as JSON; it contains numbers and source identifiers, no ROM/image/audio payload. Tools write only Research outputs; route and special-case tools enforce exact POC HEAD and clean status before/after.

All execution is shipped GML in the accepted Node source host, with GameMaker APIs mocked. Both source widths use height **196**; 256×196 is a width control, not a recreation of original SMS 256×192. Chief's future Windows target is **348×196 only**. No original ROM was located, opened, hashed or executed; no new emulator, Windows F5, compiled executable, POC edit or root AGENTS change. Canonical evidence is committed recovered assembly, decoded data and cached original routine/frame observations.

The natural attempts start at the accepted act-table anchor (142,654), state 1, zero speeds, zero rings, and install previous terrain flags from the real map. They instantiate the room's 28 relevant gameplay objects at their exact room coordinates: 6 patrols, 3 bees, 4 mapped springs, 6 platforms, 4 spikes, 5 monitors. The goal sign is outside this bounded sample. Room creation-order metadata orders construction; the source host still schedules its supported lists by its documented event order. No enemy or spring is moved by the Research setup or during replay except by its shipped handler. Actual per-update inputs are recorded, so threshold policies can be replayed without guessing timing.

**Host limitations matter:** ring-manager pickup/power/pool occupancy is not the full room runtime; zero rings are not subsequently replenished by terrain pickups. Camera follows the host rule before player motion, not the Windows camera controller. Generic collision APIs are mocked; room scenery/legacy collision shells are not all instantiated. Loop centers are empty in this host; the bounded region ends before the later THZ1 loop, but this is not global room parity. A source-host path through existing geometry establishes narrower reachability than a real GameMaker/ROM input replay. No claim of a natural combined spring/Badnik encounter is made.

## A. Input-only THZ1 routes

Eight attempts: four policies at each width. Maximum 600 updates; stop on death request or X>1456. Full traces include raw fractional X/Y, VX/VY, current/requested state, input, flags/facing, terrain contact/modifier and retained deltas, support owner, spring/patrol/spike states, camera, and before/after values of selected consequential writers. Updates below are zero-based source-host updates.

| Policy | Result at 348 | First consequential transitions / limitation |
|---|---|---|
| Hold Right | exits bounded region after 387 updates | Ramp at 89: request $1B, VX960, VY−1440. Fall at238; terrain upright spring at255 (X933.957, Y638.172): request $0B, VY−1920. Fall at335. No mapped $26 launch or patrol stomp |
| Hold Right; tap jump once when pre-update X≥760 | real lower patrol stomp, then exits after387 | Jump at213, then fall at286. $21 top bounce at325..328 near X1214..1226, requests $0B, VY−1728, attack clear, X unchanged. Fall at336. This is an enemy bounce without a co-located literal spring |
| Release directions on first nonzero modifier | 600-update budget, returns to left boundary | First ramp at91; at135 the zero-previous-modifier ramp branch writes VX−1024 and requests roll. This is a single consequential reversal, not a sustained oscillation. Retained/input/surface deltas are in the trace; no exact original input replay proves the full route canonical |
| Move right to X≥870, release; if Y≥800 turn left toward688 | 600-update budget, stops near (986,655) | The attempted lower return lands before the Y800 turn condition. It does **not** reach the fixed spring. Failed route planning is retained as negative reachability evidence, not a PASS |

No attempt has consecutive full-pixel direction reversals; the maximum consecutive draw-facing change count is one. The metric deliberately ignores subpixel cycles and is not a perceptual test. It does not license a statement that every route or display frame is free of visible oscillation.

### Width-dependent moving spike: first source difference, not a proven canonical gap

For the jump policy, player core fields match through update353. The spike at (1344,864) first has a different phase at update288 under the width-dependent activation band. At354:

* **256:** raised at Y846, state2. `chaos_spike1b_contact` writes VY−1024 and damage_request255. At355 the player consumes that request and requests death (the host has no collected rings).
* **348:** hidden at Y864, state4. No contact write; VY remains1120. The route continues.

The initial player difference is therefore an identified spike contact, not an unexplained horizontal writer. Patrol activation also differs earlier, but it does not produce a player-field difference before354 on this input route. This does not prove what would happen with the real camera, ring history or canonical object sleep/creation schedule.

Current callsites: `SCR_chaos_objects.gml` live-view activation band; `SCR_chaos_spike1b.gml:37` contact and `:60` step. The existing code explicitly calls this type's ROM sleep/delete lifecycle **unaudited**, and uses the POC camera band. Cached `$ACFD` contact supports the raised-spike bounce/request, but does not prove a canonical creation/phase schedule. Register `C2R3-SPIKE-WIDTH-PHASE` is an **adapter difference with unresolved lifecycle fidelity**, not an implementation assignment. No unsupported claim that the phase difference is necessary for widescreen is made.

## B. Small special-contact matrix

168 assertions. Cases were chosen from genuine existing contracts; maps and POC source were not altered. Width labels for pure callbacks indicate repetition under different host view settings; callbacks that do not read a view are not two independent runtime proofs.

| Finding | Original rule / source and confidence | Current exact callsite | Reproduction, controls and result |
|---|---|---|---|
| `C2R3-SEZ-CRUMBLE` | `$6B79`, `$A344`, `$A36A`; `sez/surface-runtime-contracts.json`, cached original drop rows. High within this fixture | `SCR_chaos_sez_s2.gml:37`, `:63`, `:71`, `:102` | SEZ1 unchanged cell(67,6), local seeded drop; compare cached rows9..45, first9 columns. Spawn15, hold16..31, replacement $AF→$B0 at32. Grounded/falling hold controls and airborne nonfall control agree. No presence gate added |
| `C2R3-AQZ-CROSSING` | `$4BC0`, `aqz/water-runtime.json` crossing_vectors. High for crossing callback | `SCR_chaos_aqz_environment.gml:33` | 12 original vectors per width: Y567/568, VX−1023/+1023/+1024, attack off/on, VY0 and prior dry. Equality submerges/splashes; attack with signed high-byte magnitude≥4 sets VY−768. Thus −1023 qualifies, +1023 does not. No blanket speed scaling |
| `C2R3-MGHZ-CEILING` | `$73C9→$74E7`, `mghz/surface-1b-ceiling-spikes.json` gate_summary and real_runs_check. High for sampled gate | `SCR_chaos_core.gml:512`, entered from ceiling pass `:483` | Real MGHZ2 row11 run at X864; Y357/358/382/383 boundary samples. Rising/falling, nonzero support, bit7 and hurt-state controls. Raised owner can enter the pass even when falling; static ceiling hurt ignores power invincibility. Canonical hurt yields next$1E, VX−256, VY+256 |
| `C2R3-EEZ-CARRIER` | `$4C56/$4C12/$45ED`, `eez/carrier-17.json`; original controlled export `verification/eez-p2/routine-oracle.json` attached. High for fixture outputs | `SCR_chaos_eez.gml:292`, `:297`, `:304` | 8 inherited controlled vectors per width: pad0/16, fractional seed0/77, dry/wet. Exact player and actor outputs match. Integer owner position copied with player fractions retained; action releases owner, sets cooldown16 and ordinary jump, keeping copied X speed |

These are **proven-match within listed controls**, not new whole-scene equivalence. SEZ uses an inherited invulnerable fixture and seeds the player locally; EEZ uses inherited routine fixtures, not a natural capture route. No objects in the actual POC or natural THZ1 route are relocated. The special cases do not claim a continuous route from act start.

SEZ drop metadata already says startY120 while cached row9 and the inherited verifier resolve startY154; this checkpoint reuses154 explicitly and leaves the original evidence intact. It is a known fixture metadata limitation, not a newly discovered runtime defect or silently corrected cache.

Unselected cases remain open: full SEZ pool competition, AQZ underwater platform/air/splash lifecycle, MGHZ oil sink/stale-bit routes, and natural EEZ capture/long ride/death flow. Oil is documented under MGHZ surface$1B; no SEZ oil mechanic was inferred from the assignment wording. The smaller matrix does not supersede those gaps.

## C. Implementation decision and next milestone

No finding meets the standard for a new POC correction: there is no first divergent write **against a matching canonical scenario**. The identified width difference has a precise POC writer but lacks canonical lifecycle proof. Therefore there is no minimal failing canonical fixture, unaffected control set and bounded correction bundle to hand to Designer. Generic clamps or physics changes would contradict the evidence.

Recommend **cross-zone/campaign Windows QA at348×196** next, retaining the historical oscillation and sticking findings as OPEN. Include natural gameplay through special surfaces and owner detach/landing, with act/input/visible displacement recorded if the symptom returns. Existing `EEZ3-FULLCHAIN-F5` remains separately open; nothing here closes it. If a specific spike-phase concern is observed, commission canonical lifecycle/camera research before editing activation.

Practical observation candidates, not newly Windows-verified routes:

1. THZ1 from act start: hold Right over the first slope; compare releasing on the slope with continuing. The source host reaches a terrain spring aroundX928. Keep this separate from mapped springs at(688,864)/(1912,864).
2. THZ1 from act start: follow Right, tap jump nearX760 on the upper route, then continue Right toward the lower patrol originally placed(1248,862). The source-host sequence reaches a stomp, then falling. Observe world displacement versus facing and camera; if Windows timing misses it, do not teleport an enemy or claim the route is verified there.
3. SEZ1 crumble(67,6), AQZ1 water line568, MGHZ2 row11 spike run X864..1407, EEZ1 carrier placement(1040,478) are canonical landmarks for broad QA. This checkpoint does **not** establish act-start input routes to them, so they are landmarks rather than guaranteed observation routes.

## Verification and stop

* Eight continuous source-host route attempts, zero host execution errors; bounded stops retained, including the256 death and failed fixed-spring return.
* 168 focused original-contract assertions PASS.
* Two348 routes replayed without tracing wrappers: **16,254 core-field/draw-facing comparisons PASS**.
* Seven evidence-consistency tests PASS.

No C2-R2 synthetic grid rerun, full historic regression sweep, imported-asset build, ZIP, executable, main promotion or POC candidate. No broad legacy-suite PASS claim. GML is unchanged; verification is evidence-focused rather than a parent/candidate implementation gate. Scope fingerprints, controls and raw per-update results are retained. Push Research checkpoint and stop for Manager review.

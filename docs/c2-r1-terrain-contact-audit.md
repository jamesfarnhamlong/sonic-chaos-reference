# C2-R1 terrain, collision and interactables audit

Research-only delivery, 22 October 2026. **Manager review required.** POC read/executed as source in a Node VM at `d1ef8fc42571fb01829d370671a96287d9ae6d93`; Research parent `637180aa3d658916b86af84b48b428ab2753f04a`. No GameMaker changes, builds, Windows acceptance, new ROM emulation, root coordination changes, merge or PR.

## Decision

Three related **source-level contact gaps** are demonstrated: state `$0F`'s 9-pixel X extent is lost in patrol `$21`, moving spike `$1B`, and the older `$28` platform support path. The shared overlap helper and newer consumers already accept the correct extent. These are bounded edge cases, **not an explanation of the reported slope/spring oscillation**. Recommend one extent-consistency bundle only if Manager considers its gameplay value sufficient; otherwise obtain a natural symptom replay before assigning Designer. There is no evidence for a generic velocity clamp, collision-map replacement or slope rewrite.

The historical slope sticking, rapid left/right oscillation after spring/Badnik contact, and unusual diagonal static-spike contact remain **unresolved as current POC defects**. A 48-sequence POC discovery grid produced zero velocity sign flips. It contained no live Badnik or mapped spring: it seeded walk/roll/spring/fall states on THZ1 terrain. It cannot reject the reported combined interaction. Do not convert this negative result into a regression PASS.

## Evidence and reproduction

Run from this Research checkout:

```powershell
node tools/c2r1_audit.js ../SonicChaos_POC_c3bx1
node tools/c2r1_gate.js ../SonicChaos_POC_c3bx1
python -m unittest discover -s tests -p test_c2r1_audit.py
```

The first tool checks the exact accepted HEAD, hashes controlling GML and fixtures, reads the canonical extent directly from the committed geometry cache, executes shipped source, records integer per-update traces, and verifies unchanged POC Git status. It records 121 assertions, 84 boundary/launch comparison rows, 48 discovery sequences of up to 96 updates, and 48 cross-zone terrain coverage entries (46 complete 24-update sequences; two absent SEZ1 type-5 samples). All new numeric evidence is in [source-audit.json](../data/c2r1/source-audit.json). The second tool redirects verifier writes into Research, caps each test at 45 seconds, and retains raw output. No verification overlay changes runtime or assertions. Five additional evidence-consistency tests pass using Python 3.12; the Python 3.13 launcher is unavailable here, and no PNG encoding/reconciliation was performed.

The ROM identity is the project-authoritative private SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. **No ROM file was opened, located, hashed or executed in this audit.** Canonical evidence below is inherited, committed decoded data / recovered assembly / cached controlled traces, not new Z80 execution. Confidence is high for the documented ordinary routines and extent exception; natural reachability, global scheduler equivalence and all-act terrain coverage are weaker or absent. Historical reports' old POC mismatch tables are not current verdicts.

## Systems and ownership

Addresses below are CPU addresses unless a source document specifies a bank. Exact current POC paths are relative to the accepted POC SHA; function names are stable callsites. See the machine-readable [register](../data/c2r1/fidelity-register.json).

| System | Canonical authority | Accepted POC callsites | Finding / confidence |
|---|---|---|---|
| Terrain lookup/map interpretation | `$7666`, [collision.md](collision.md), recovered `collision_lookup.asm` | `scripts/SCR_chaos_core/SCR_chaos_core.gml:83`, `SCR_cc_lookup` | Row stride, alternate plane headers and 32-entry profiles preserved in ordinary path; **unresolved** whole-map parity. Out-of-map fallback clears modifier in POC whereas canonical lookup retains `$D100`; no reachable impact established. |
| Floor/height maps | `$691A`, `$6F61/$7056`, `terrain_update.asm` | same file `SCR_cc_floor:377`, `SCR_cc_project_floor:107` | Old surface gates projection before new flags replace it; upward speed skips projection; upper-tile continuation retained. **Proven-match** only cached tested ordinary cases. Special object `+$24` paths explicitly excluded. |
| Slopes and ramp transitions | `$69B2`, `$459D`, [movement.md](movement.md) | `SCR_cc_input:34`, `SCR_cc_ramp:197`, `SCR_cc_y:64` | Signed 8.8 values, retained surface delta at zero speed, asymmetric ramp gate and ±4 impulse must be preserved. Sticking symptom **unresolved**. |
| Sides / ceiling / one-way | `$715E/$71B2/$7257`, `$73C9`, `$3686` | `SCR_cc_sides:448`, `SCR_cc_ceiling:483`, `SCR_cc_project_floor` | Floor `(X,Y+18)`, sides `(X±9,Y+6)`, ceiling `(X,Y−6)`; one-way strict penetration threshold. Focused cached controls pass; **proven-match** within those cases, not all ceiling specials. |
| Air / roll / spring / fall | `$3FEF/$402A/$4097`, `$480C/$482D`, [spring audit](spring-interaction-audit.md) | `SCR_cc_tick:775`, `SCR_cc_jump:189`, `SCR_cc_spring:222`; `SCR_chaos_spring.gml` launch/gate/phase | Upright spring clears attack, keeps X; diagonal spring differs; apex requests fall. Existing source replay passes. No generic airborne=attack rule. |
| Static spike | `$6ACE`, `$7306/$7329/$74E7`, [spike audit](platform-spike-collision-audit.md) §§2,6 | `SCR_cc_floor:396`, `SCR_cc_sides`, `SCR_cc_ceiling_spike:512` | Rising corner passage and first-sample delay can be canonical. Cached rising/descending/grounded/side controls pass. Historical diagonal symptom **unresolved**, not automatically a gap. |
| Moving spike `$1B` | bank `$0C` `$ACFD`, shared `$6328` | `SCR_chaos_spike1b.gml:21,37,58` | Cone, cooldown, pre-move contact, deferred damage already implemented. **Proven-gap** only state-$0F extent slice; activation lifecycle remains adapter/unresolved. |
| Mapped and hidden-span spring `$26` | bank `$1E` `$82AF`, `$0383/$0386`, `$480C`; spring audit | `SCR_chaos_spring.gml:13–40`, fixed/span helpers, pending state 9 | Strict X window / six Y rows; span has separate next-update launch without re-test. Focused source grids **proven-match**. Loop bypass **adapter-difference**. |
| Monitors / rewards | bank `$0C` `$A16C/$A177`, shared `$5FA0/$6328`; collision geometry audit | `objects/OBJ_chaos_object_10/Step_0.gml:46`, shared box helper, `SCR_chaos_type10_reward` | Current explicit extent and solid push precede break/reward logic; 75,805 support checks pass. All reward presentation/timers and nonordinary cases **not-audited** anew. |
| Badnik / damage | `$B2AF` type `$21`; `$89AC/$89DF/$8A06` type `$27`; `$48BC` | `SCR_chaos_attack.gml:36,47`, core damage gate:637; object Step events | Attack bit and next-pass contact already migrated. `$21` uses constant ±19 instead of ±20 at state `$0F`: **proven-gap**. Ordinary resolver already selects extent by state. |
| Platforms / owner | bank `$1E` `$8814/$8843/$8866/$88A0` | `SCR_chaos_platform.gml:55,67,83`, objects phase:58; adapter:144 | Owner-only release, relative Y-speed and carry retained. Older support helper hardcodes extent 8: **proven-gap** at state `$0F`; newer explicit-extent paths provide control. EEZ and MGHZ focused regressions pass. |
| THZ2 destructible/shards | `$7857/$7898`, numeric `data/rom-cache/visual1/` contracts | `SCR_cc_break13_*`, `SCR_chaos_shards`, `SCR_chaos_objects:25` | Shards share occupancy, not inferred solid terrain. New full shard verification **incomplete (timeout)**. Do not revise placement, pool or collision from this audit. |
| Contact order / activation | [attack audit](player-attack-badnik-audit.md) §4 and spike audit §6: player, terrain, damage gate, objects in slot order | adapter:156,189,210; `SCR_chaos_objects:1–116`; attack stage/promote:25–30 | POC preserves staged next-pass damage and two-pass side-wall pipeline. Grouped type phases/legacy Step events are not a universal ROM slot scheduler. Natural simultaneous contacts **unresolved**. Earlier/longer wide activation is an adapter property, not a velocity change. |

## Representative zone/act matrix

Each new terrain entry chooses the first eligible existing cell of surface types 1/2/3/5, seeds a falling player once and captures 24 updates with no input at 256 and 348. Coordinates, map index, flags, velocities, state and contacts are in `coverage` in the JSON. These are POC-only discovery traces: they **do not** establish ROM map or dynamic parity. The host installs zone environment structs for MGHZ/SEZ and advances their counters, but does not populate a natural scene's objects. The camera follows through the verification host, not the Windows camera controller.

| Zone | New ordinary-act terrain sequences at each width | Other evidence replayed / limitation |
|---|---|---|
| THZ1 | types 1,2,3,5; plus slope/spring/fall discovery grid | Cached first ramp 48 updates, spring flight 160, one-way/static/moving-spike/support controls. Natural spring+Badnik route still missing. |
| THZ2 | No new seeded grid | Existing spring grids and monitor tests cover examples; shard verification timed out. No fresh full corridor parity claim. |
| THZ3 | No new seeded grid | Shares audited object routines; encounters/loops outside C2 proof. |
| GPZ1 | types 1,2,3,5 | No natural loop, conveyor/route or full enemy replay added; GPZ2/3 not dynamically audited anew. |
| MGHZ1 | types 1,2,3,5 | MGHZ platform correction verifier passes 768 assertions, 90 jump windows, 256/348/640; no all-hazard claim. MGHZ2/3 ordinary contact sampling absent. |
| SEZ1 | types 1,2,3; no eligible type-5 sample | SEZ-specific surface/crumble/enemy contracts remain inherited source references; no newly paired natural scene; SEZ2/3 not dynamically audited anew. |
| AQZ1 | types 1,2,3,5 | Water/special terrain lacks paired natural replay. Frozen AQZ-P2 source-preservation test fails against accepted later code. AQZ2/3 not newly covered. |
| EEZ1 | types 1,2,3,5 | EEZ platform verifier passes 275,455 assertions across its recorded cases; this does not close EEZ3 full-chain Windows requirement. |

Terrain-map fidelity is separate: reading accepted installed tile IDs is not an independent layout extraction. No new 18-act collision-header or placement census was regenerated. Special Stages, Tails, loop-owned movement and transport-owned probe exceptions are outside new dynamic coverage.

## Minimal proven differences and controls

Coordinates here are relative anchors; objects may be translated to (100,100). The boundary tool runs actual consumers with current=requested state, zero hurt flags and Y speed 0. The patrol case sets attack posture for state `$0F` (charge); the geometry-only platform/spike cases do not depend on that posture. Each side and width is tested. `oracle` in the JSON is the **expected canonical result**, not a patched runtime. No after-implementation trace exists because implementation is prohibited.

| ID | Minimal input | Accepted result | Canonical expected result | Negative controls |
|---|---|---|---|---|
| C2-EXT-21 | state `$0F`, attack posture, `$21` dx=±20, dy=0, no invincibility | no contact (0) | contact → enemy defeated (2), since 9+11=20 | states `$01/$09/$0A/$0B/$0E` at same boundary correctly miss; ordinary attack matrix passes |
| C2-EXT-28 | state `$0F`, unowned platform, dy=−16, dx=±25, platform vy=player vy=0 | no support | above bit → support, since 9+16=25 | same five ordinary states miss; owner/speed/cone controls in existing battery pass |
| C2-EXT-1B | state `$0F`, moving spike, dy=−24, dx=±25 | no overlap | above bit 1 (zero-penetration tie goes vertical); damage/bounce if active, non-rising and cooldown zero | ordinary states miss; rising/cooldown/attack/damage controls in existing battery pass |

12 gap rows = three distinct findings × two sides × two widths. Width in pure-helper rows is a coverage label; those functions do not read the camera. This does not prove viewport activation parity. The cached animation engine evidence establishes 9×24 in state `$0F`; no new ROM callback was run. Charge animation transition frames and natural reachability at those exact boundaries remain Windows/ROM follow-up work.

## Verification ledger (raw, no adjusted results)

8 pass / 1 frozen-source failure / 1 timeout; [raw results](../data/c2r1/gate/results.json), adjacent `.log` files and redirected result JSONs. This is a single accepted-source gate, not a parent/candidate comparison.

| Verifier | Result |
|---|---|
| `verify_core.js` | PASS: 15,660 cases, 48 ramp / 160 spring updates |
| `verify_spring_interaction.js` | PASS: 170,497 assertions |
| `verify_attack_posture.js` | PASS: 95,991 assertions |
| `verify_platform_spike.js` | PASS: 19,990 direct assertions + 65 battery checks |
| `verify_monitor_support.js` | PASS: 75,805 checks |
| `verify_terrain_ring_probe.js` | PASS (see raw log) |
| `verify_eez_platforms.js` | PASS: 275,455 assertions |
| `verify_mghz_platform_crush.js` | PASS: 768 assertions |
| `verify_aqz_p2_terrain_preservation.js` | FAIL at line 7: exact source equality with frozen `7ca3336...`; accepted C3-BX1 core differs. Not a new candidate runtime failure; no assertion relaxed. Later behavioral cases never reached. |
| `verify_visual_p2_shards.js` | TIMEOUT at 45 s, no final result. Not PASS; not retried. |

Old GPZ sprite-ID and boss-test timeouts were not exercised; they retain their existing open identities. No full historic sweep, imported-asset rebuild, PNG re-encode, new original-ROM run or GameMaker test was required for these research-only changes. Replays consume previously published numeric fixtures; some legacy scripts also compare mirrors in `sonic-chaos-reference-work`, explicitly reported in their logs. That mirror comparison is not independent ROM verification.

## Ranked bounded proposals

1. **Contact extent consistency (three causal edits, modest gameplay impact).** Pass the executing animation/player extent into `$21`, `$1B`, and old `$28` support; reuse existing helper conventions. Do not change terrain probes, placements, attack gates, damage direction, velocities or ownership. Preserve 8-pixel controls and newer `_support_ex` consumers. Risks: one-pixel side contact can change support/damage timing; executing versus pending state can misclassify transition frames. Stop if cached mapping extent disagrees, a normal-state trace changes, or natural simultaneous contact exposes a broader scheduler dependency. Acceptance: exact gap rows become canonical, negative controls unchanged, then one Windows package with nearby monitor/spring/platform cases. **Not yet authorised.**
2. **Historical symptom isolation / contact-order research (highest unresolved gameplay value).** Obtain the exact act, route, input and starting condition for oscillation. Capture per-update current/pending state, input, facing, X/Y/subpixels, move/bg/combined contacts, previous/new tile/profile/modifier, support owner and object slot/order at 256 then 348 in ROM and POC. Candidate corrections only after first divergent write is identified; likely investigation boundaries are retained surface delta, terrain ramp dispatch, Badnik bounce/damage staging and spring/support release. None is established as the cause. Stop if only a teleport or harness-specific order reproduces it; do not alter global movement.
3. **Terrain special-path / lifecycle coverage research.** Pair SEZ oil/crumble, AQZ water/platform, MGHZ ceiling/spike and EEZ carriers using existing contracts. Audit whether fallback modifier retention or grouped object phases affects reachable contacts. Resolve shard verifier cost separately before using its frozen-parent differential as a gate. No collision-map replacement or importer change in this bundle.

## Practical Windows observation cards (unexecuted)

Use the already accepted private C3-BX1 project and its existing Level Select; F5 only. Repeat at the available 256 and 348 settings. These are observation routes, not guaranteed exact reproductions; do not enter fabricated placement coordinates or build external tools.

* **Slope/sticking:** THZ1, travel over the first curve rightward, then backtrack; repeat walking, rolling and after an ordinary jump. Release directions briefly on the slope. Note first loss of ground, unexpected stop, direction reversal and whether input was still held. Record the route and a short video if it recurs.
* **Spring/Badnik:** on the Chief's previously observed route, repeat spring ascent without attacking, with direction released and held, then with the nearby Badnik present and defeated. Record act, spring appearance, approach side, input and whether flicker is sprite-facing only or actual X reversal. Without that location this card remains a request for a reproducible route, not a known regression fixture.
* **Static spike:** THZ1's first static pair (world X1504–1567, inherited decoded cell evidence), approach on foot, jump over while rising, then descend onto it with rings. Canonical rising corner passage must not be judged solely by sprite overlap. Repeat from the other side; compare static terrain to a retracting spike separately.
* **Platform/monitor:** THZ1 first lift (placement 592,464), land near center then edge; charge beside a monitor and compare walking versus rolling contact. A one-pixel extent gap is unlikely to be conclusively diagnosed by eye; the source boundary fixtures are the primary proof. No claim that this route closes all three exact edge cases.
* **THZ2 shards:** play through the existing destructible corridor in both directions and confirm break progression and landing remain usable; capture any unexpected collision after fragments appear. This is a future human check, not a replacement for the timed-out source verifier.

## Limitations / stop

Before/after **Windows** or newly paired full-frame ROM traces are absent. Existing fixture replays and synthetic source boundaries are explicitly narrower evidence. No natural oscillation reproduction, exhaustive floor/wall/ceiling or all-reward audit, full object-slot scheduler proof, 18-act campaign, new asset verification, or final implementation acceptance is claimed. POC and root `AGENTS.md` remain untouched. Deliver Research commit/branch only, then stop for Manager review.

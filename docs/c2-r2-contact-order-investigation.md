# C2-R2: historical oscillation and contact-order investigation

Research-only checkpoint, 22 October 2026. Await Manager review.

POC read/executed: `poc/c2-e1-contact-extent@4eb684911c5785667181b9d3f940b1dc820e66d1`. Research parent: `research/c2-r1-terrain-contact-audit@1e34a2a666a83e107942678fe0c0497fffb3ff05`. Both local checkouts were clean and matched the assigned commits. Topic branch: `research/c2-r2-contact-order`. No POC modifications, GameMaker build, Windows run, root AGENTS edit or new ROM execution.

## Finding and recommendation

**A repeatable world-X oscillation exists in the accepted source, but the isolated numerical mechanism matches recovered canonical movement. No POC gameplay defect or minimal physics correction is proven.** This does not close Chief's historical observation of visible left/right oscillation, sometimes followed by falling, or the separate slope-sticking report.

With no directional input, upright spring flight and ordinary falling can settle into X velocities +16/-16 in signed 8.8 units. X alternates by **1/16 pixel**, every active update. A mapped spring launch and a mapped patrol stomp each reach this cycle; an empty-scene falling control reaches it too. Thus competing spring/Badnik writes are unnecessary for this small cycle. It is not evidence of a large visible displacement or alternating facing: in the selected +256/no-input examples, both instance and draw facing stay +1 through the cycle. A clamp would alter established canonical semantics.

The source-host grid contains 96 seeded sequences, up to 160 updates each, at widths 256/348: 30 sequences execute a real mapped-spring launch and 30 execute a live patrol stomp. Zero execution errors. Maximum unforced velocity/world-X sign changes: 148, in the empty control. Counts measure sign changes, not amplitude or severity. The historical symptom's amplitude, act and input are unknown; it cannot be identified with this cycle merely because both alternate.

## Evidence and method

Run from this Research checkout:

```powershell
node tools/c2r2_contact_order.js ../SonicChaos_POC_c2e1
node tools/c2r2_canonical_controls.js ../SonicChaos_POC_c2e1
node tools/c2r2_replay_check.js ../SonicChaos_POC_c2e1
node tools/c2r2_gate.js ../SonicChaos_POC_c2e1
```

[Summary](../data/c2r2/summary.json), [complete compressed traces](../data/c2r2/traces.json.gz), [canonical controls](../data/c2r2/canonical-controls.json), [gate ledger](../data/c2r2/gate/results.json), and [register](../data/c2r2/fidelity-register.json). The gzip decompresses to JSON; it contains only numeric/source-hash evidence, no assets or ROM bytes. Reproduction overwrites these Research outputs only. The tracing tool checks exact POC HEAD and clean status before/after and fingerprints the loaded scripts/events/harness. The control/replay tools consume that same checkout and should be run immediately after the guarded tracing tool.

Execution uses the accepted `verification/chaos_world_harness.js`: shipped GML translated mechanically into a Node VM; mocked GameMaker instance, camera, drawing and input boundary. A Research-only Proxy logs changed core fields; wrappers label selected real function writers without replacing their bodies. Unwrapped writes retain `host.frame` attribution, so this is not an exhaustive instruction-level call stack. A separate replay without Proxy or wrappers matches **430,080 field/draw-facing comparisons across 96 sequences**. No diagnostic was installed in the game.

Each update records current/requested state, raw 16.8 X/Y (fraction = low eight bits), signed 8.8 velocities, held/pressed input, flags/facing, terrain tile/previous flags/modifier/deltas, support token/reference, box pipeline, staged/promoted contact/request, spring and Badnik state, camera and published position, and chronological changed-field writes. Terrain classification uses installed headers plus `previous & 63`; this is a source map, not a newly extracted independent terrain oracle. The frame counter is an active host update, not a measured Windows display frame.

No private ROM was searched for, opened, hashed or executed. Canonical comparison uses committed recovered assembly, decoded tables and cached earlier ROM observations. Project ROM identity remains `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`; it was not independently reverified here.

## State-writer and order map

Paths below are relative to the exact POC commit; function names are the review anchors.

| Pass / writer | Writes and potential interaction | Canonical authority / limitation |
|---|---|---|
| `SCR_chaos_adapter_step`, adapter script | Reimports published position; clears core support if GameMaker owner reference is absent; merges support/object flags and two-stage side flags; animation precedes state tick | Adapter reference ownership and loop bypass differ from ROM RAM scheduling; side flags reach X integration two updates after object contact |
| `SCR_cc_tick`, core script | Applies requested state at update start; dispatches current-state callback | Current/requested distinction retained; special owners have early returns |
| `SCR_cc_input` -> `SCR_cc_x` | Chooses input/friction pair, doubles near zero, retains surface delta on no-input zero velocity; X integrates velocity + both deltas | Recovered `movement_core.asm` `$4141/$4223/$4196/$41A9/$402A`; `data/movement-tables.csv` |
| `SCR_cc_y`, floor/sides/ceiling, ramp | Y/gravity then probes/projection; old modifier gates ramp; ramp can set X impulse +/-1024 and roll or request $1B with negative Y velocity | `$4097`, `terrain_update.asm` `$691A/$69B2`; no new natural slope route or paired replay |
| `SCR_cc_spring` (terrain) | Upright preserves X; diagonal writes X/facing before Y gate; horizontal writes X/cap and roll request | `$480C/$482D/$4849`, `spring_contacts.asm`; distinct from mapped $26 |
| State tail / fall/walk setters | Spring apex requests $0E and sets Y velocity +256; landing requests walk; idle can zero X | `spring_state_updates.asm`, `player_state_setters.asm`; next request can suppress remaining tail |
| Adapter end of player pass: `SCR_cc_damage_gate` | Consumes prior promoted request/contact; hurt can write X +/-256, Y, $1E, clear support/deltas; attack rebound changes Y only | `$48BC/$48F7`; cache `player-attack-badnik.json` |
| Live $21 Step (after player) | Moves enemy and floor-projects it, then contact; top branch immediately calls `SCR_chaos_type21_top_bounce`: Y=-1728, request $0B, attack clear, release mirror owner; side nonattack stages hurt | `$B2AF`, existing attack audit; no X reversal in stomp setter. Repeated early top contacts in seeded patrol trace reset Y bounce; no canonical full-scene verdict |
| Ordinary enemy resolver / staging | Shared overlap chooses above/below/side; writes staged contact/nibble; last staged nibble can replace earlier one before promotion | Shared `$6328/$5F3D`; type $27 handler cache. Pure callback controls, not new live flying-enemy scene |
| `SCR_chaos_objects_phase` | Lost rings/shards, zone effects/bosses, grouped ordinary enemies, promotion, mapped springs, platforms, moving spikes, final promotion, support mirror and conditional publish | Actual source order overrides stale top comment claiming platforms first. Legacy $21 Step already ran. Group/type order is not proof of universal ROM slot order |
| `chaos_spring26_phase` / launch | Fixed spring tests final floor/Y-speed/request; span state 9 launches next update without retest. Upright launch preserves X, requests $0B, clears attack/floor; negative Y prevents launch | bank $1E `$82AF`, setters `$480C`, cached `spring-interaction.json` |
| Platform support/release | `chaos_platform28_support_ex`: only unowned/same owner can claim; failed test releases only itself. Rising rider released by relevant platform callbacks; next adapter clears missing mirror reference | `$8814/$8843/$8866`; source audit only for simultaneous launch/platform combinations in this checkpoint |
| Sprite / camera | Animation uses facing/input bits, presentation publishes draw facing; camera changes screen-X independently of world-X | Accepted animation path owns $0B/$0E facing, not simply velocity sign. Host follows camera before player; Windows camera is not emulated |

A spring launch and stomp both make Y negative and clear floor, preventing an ordinary later fixed-spring gate that update. A pending span launch can still write D448 before refusing negative Y. A staged hurt is consumed on the next player pass, after movement/terrain; it can supersede an earlier request. These are order-sensitive transitions, not proof of an endless contradictory-write loop. Simultaneous multiple-contact winners need a canonical slot-order replay before correction.

## Scenarios and negative controls

All players are **seeded**, not reached through a recorded level input route. Initial current=requested $0E, airborne, Y speed +256, X speed -256/0/+256; no input, held Left, held Right, or alternating Left/Right. Each at 256 and 348.

| Scenario | Actual objects / terrain | Result and limitation |
|---|---|---|
| `mapped-spring` | THZ1 fixed strong $26 at (688,864); player (688,846), real THZ1 terrain | Launch exercised; canonical placement from cache record 7. Seeded approach, not natural route proof |
| `mapped-patrol` | THZ1 $21 at (1248,862), parameter from shipped Create; player (1248,836) | Live movement, floor projection and stomp executed; canonical record. Adjacent spring not included |
| `combined-overlay` | Same mapped spring at (688,864), **translated synthetic $21 at (688,862)**; player (688,846) | Both systems active, but enemy floor-projects before side contact; stages hurt, next player pass hurts and inhibits spring. No successful launch/stomp in this overlay. Not a canonical placement or a natural spring+Badnik encounter |
| `empty-control` | Cleared host map, no objects; player (688,400) | Repeated tiny cycle without contact. Explicit synthetic isolation; not level geometry |

For the +256/no-input mapped spring, update 1 requests $0B with Y=-1888; update 2 executes $0B. First X sign reversal is update 12. Updates 12/13/14 alternate XU 177840/177856/177840, velocity -16/+16/-16, draw facing +1 throughout. Update 80 requests fall, update 81 executes it, still alternating. Landing update 94 requests walk; update 95 stops it. This is the requested spring-to-fall sequence at source-host level.

The +256/no-input mapped patrol first stomps at update 0, requests fall at 10, and first X reversal occurs at 12. The synthetic combined example stages damage at 0, hurts at 1, and runs $1E at 2; no sustained alternating X. Zero-speed no-input controls have zero world-X flips; held direction generally prevents the near-zero cycle (single reversals from changing direction are expected). Alternating input is an intentionally forced control, not a defect metric. Width labels in pure controls do not imply independent hardware tests; the matched width grid exercises the host activation adapter only.

## Canonical comparison and classification

**Confirmed canonical match, bounded:** the no-direction table at `$439D` has pairs [+16,-16] for $0B and $0E. `$4223` chooses by velocity sign; `$41A9..$41B3` doubles the increment when abs(velocity)+128 has zero high byte. Thus +16 + (-32) = -16 and -16 +32 = +16. `$402A` integrates the result without a zero-crossing clamp. Reduced semantic replay of these recovered branches against shipped input/X functions passes 704 comparisons (22 initial state/velocity cases, 32 updates each). This is not execution of original Z80 bytes and not whole-scene canonical parity.

**Confirmed cached contract/source consistency:** eight ordinary-contact callback controls exercise staging, promotion and next gate: upright airborne hurts; attack posture rebounds above (-768) or below (+128), side leaves Y unchanged. Three retained-surface controls verify no-input zero-speed retention. These bring canonical/control assertions to 758. No cached trace has the exact combined overlay initial state; no first divergent canonical write is established there.

**Proven POC discrepancy:** none established by C2-R2. The reproduced small X cycle is a confirmed source behavior with canonical arithmetic support, not a discrepancy. Large-amplitude oscillation and slope sticking remain **unresolved**.

**Adapter differences:** grouped object phases, loop-owned contact bypass, viewport activation/retention and mocked camera. These can change simultaneous-contact availability/order; no causal historical defect proven.

**Untested:** live $27 flight lifecycle, full global pool arbitration, simultaneous moving support/spring/Badnik on a canonical route, zero-speed retained nonzero surface slope dynamics, all zones/acts, Windows draw timing and natural reachability. No new full-ROM or per-update Windows comparison. Source controls cannot close those findings.

## Verification and next action

The focused accepted-source gate runs core, spring interaction, attack posture and platform/spike verifiers with all file outputs redirected into Research. Raw logs/results retained, no assertion overlays. No parent/candidate gameplay differential is applicable because POC is unchanged. No full historic suite, importer rebuild, archive, asset restoration or production test was run; their coverage is not claimed.

Recommended Windows observation (unexecuted): THZ1 strong spring at world (688,864), approach with modest horizontal speed and release directions during ascent; observe through apex/fall at 256 and 348. Separately use patrol near (1248,862), stomp and release direction. These are canonical landmarks, **not a certified route to Chief's symptom or a claim the two interact naturally**. Record whether Sonic's world position, facing, or screen position alternates, the size of displacement and held keys. A 1/16-pixel cycle may not be visibly distinguishable. Obtain Chief's original act/location if these do not resemble the symptom.

If visible oscillation persists, propose (do not implement) a developer-gated ring-buffer capture of the same core fields plus actual GameMaker instance execution order, platform owner IDs and camera after follow, triggered only on repeated world-X/draw-facing reversals. Pair a reachable replay with canonical source/ROM evidence before assigning Designer. Stop before any physics edit; no velocity clamp, terrain replacement, inferred placement or diagnostic implementation is authorised here. Preserve historical slope finding and unresolved contact-order risks for Manager selection.

Final verification ledger: **4/4 focused existing verifiers PASS**, 758 new canonical/control assertions PASS, 430,080 uninstrumented replay comparisons PASS, and **5/5 evidence-consistency tests PASS** (`python -m unittest discover -s tests -p test_c2r2_contact_order.py`). Core reports 15,660 cases, 48 ramp and 160 spring updates; spring 170,497 assertions; attack 95,991; platform/spike 19,990 direct + 65 battery checks. The spring/platform logs cross-check an older local Research mirror: that is consistency, not independent new ROM evidence. The spring log retains an inherited forced-thrust diagnostic (`pocFatal=true`, `romFatal=false`); it is not a newly established current-runtime defect or the oscillation reproducer. Raw logs are preserved. No historic boss/asset/frozen-source gates were rerun or declared green. The source host is clean after verification.

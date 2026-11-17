# Sonic Chaos — F3 Chief Physical Acceptance & RC2 Readiness Gate
**17 November 2026 · Manager-San #13 · F3 owner tests 6/6 PASS**

## Chief decision and exact tested context
Chief's physical feedback on the private **Sonic Chaos v0.99.3-f3** trial was:
- **MGHZ3: PASS**
- **GPZ3: PASS**
- **THZ3 / SEZ3 / AQZ3: PASS**
- **EEZ3: PASS**
- **Classic Pause: PASS**
- **Enhanced regression: PASS**

Chief added: "All seems fine to me". Therefore **F3 is CHIEF-ACCEPTED for the six tested gameplay/presentation categories**. The P1 Classic MGHZ3 boss camera symptom is no longer an observed release blocker. Close F3 camera/Classic Pause corrective sprint issues [#5](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/5), [#6](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/6), [#9](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/9). SC-RC1-26 SEZ/AQZ corner crumble previously closed authentic-no-change on ROM evidence. **Earlier F1/F2 owner 17/17 PASS remains accepted**, including one full Classic Sonic and one Enhanced Sonic (one emerald) campaign at F2; no new complete campaign claimed for F3.

## Frozen software / preservation identities
- PRIVATE repo `jamesfarnhamlong/SonicChaos_POC`, F3 branch `fix/f3-classic-rom-camera-fidelity-20261117`.
- F3 frozen code **`407377d5d9eeb0748b6b1698f6e377108eb3bf5a`**; extra verification-only commit **`a7f92774227ee6e8034d3b01e60e34b94bec3dd1`**.
- Exact F2 code parent `5d045ae0bba8dcbfa3f220c8e96d78baaa4fc22e`; earlier accepted F1 `e82af5554a755f2708b9120809ca3bb17ddc1eb7`; RC1 `ad499c9b483776714cf18683ed9a23aa0ed1e668`. No new game commit in Chief acceptance.
- F3 agent reported 10/10 native preservation/feature cases exact versus F2, 68 isolated SCTest runs with 0 Chief AppData writes; source aggregate 75/178 PASS identical to F2. Windows/source (22 private deps) ZIPs and independent H: recovery agent-reported verified. **Manager has not read Chief-local ZIP bytes/full SHA256**, and no release promotion executed.
- Retain normal `SonicChaos` save namespace, owner current saves, original RC1/F1/F2/frozen F3 packages and H: backup, Classic freeze, production main and previous tags.

## Distinguish user-accepted gameplay from remaining engineering evidence
- **SC-RC1-23 is closed as Chief-accepted correction**: six tested arenas show correct visual and playtest framing; MGHZ3 post-defeat no longer rises incorrectly; prior F1 GPZ3 floor fixed; Enhanced remains sound.
- **Remaining no-code, research-only [#10](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/10):** EEZ3 **moving chase stages 1–2** passed Chief's on-screen check, but numeric frame-by-frame original-ROM vs compiled-F3 moving camera timeline was **not executed** in F3. GPZ3 internal logical camera Y differs by 1px (ROM97 vs F3 98), while the measured fight screenshot alignment is correct; no known mechanic uses this value. These are **not currently observed P1 defects**. For an unconditional strict ROM-parity certification, obtain small bounded read-only ROM/native trace or record an explicit release-risk disposition. Do not reopen accepted code or claim identical numerical trajectories without proof.
- **SFX research [#7](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/7):** spike-with-Spring Shoes silence proved ROM-authentic; MGHZ spring-top robot high-priority suppression is supported by original driver but native concurrent interaction wasn't executed. Latent port direct/deferred queue class difference is documented; **do not change shared audio without a reproduced ROM differential/Chief decision**. SC-RC1-22 `$A5` sound also parked separately.
- Ordinary Classic levels retain previously documented D2-A presentation offset; F3 changed only boss arena draw framing. This is an existing design exception, not yet a newly observed gameplay problem.
- Historical SC-RC1-17 loop exit/slow fall-off research, GPZ3 seam historical watch and Classic attract original timing measured HOLD remain separate; no unapproved physics, camera, demo or audio rework.

## Recommendation: RC2 release nomination now becomes viable, but not yet executed
1. **Chief accepted gameplay baseline:** frozen F3 code `407377d5…`. Authorize **planning/preflight** for a single private **RC2 nomination candidate**, not automatically declaring RC2/v1.0. The RC2 integrator should select exact F3 gameplay tree, retain canonical saves, compare dependencies and build reproducible Windows/runtime and complete-source packages, freeze hashes, run full final native preservation and standard-user/Chief-profile isolation checks.
2. **Before claiming strict full Classic camera ROM numeric parity:** resolve or explicitly classify #10 with a bounded EEZ3 chase trace and GPZ3 1px impact check. No speculative source edits. This should be lightweight research, not another long gameplay correction sprint unless a material mismatch appears.
3. **Before Chief approval of RC2 nomination:** show exact code SHA, tree, 22 private dependency recovery, per-file ZIP manifest, SHA256, H: independent restore, clean runtime and installation/save continuity, existing 17 F1/F2 + six F3 owner PASS references, and honest residual research/HOLD list. No new full campaigns mandated if unchanged gameplay is truly byte-identical to accepted F3.
4. **Super Sonic NG+ integration remains SEPARATE** (R3d private HEAD `21176dd03138b155412bef9256306437275414ca` already core-gameplay accepted in reported testing). No automatic cherry-pick while RC2 readiness/nomination is being validated. After stable RC2 is Chief-approved, compare F3/RC2 vs R3d in its own opt-in integration branch and validate normal Classic/Enhanced parity and save/emerald rules.
5. Preserve SCTest account for any residual native checks; no clean-up until release and NG+ test requirements concluded, and never wipe Chief's live saves automatically.

**Formal status:** F3 Chief PASS 6/6; F1+F2 Chief PASS 17/17 from prior band; **RC2 readiness GO to plan**, **RC2 build/nomination, v1.0 and NG+ merge NOT EXECUTED**. Full strict EEZ3 ROM numeric parity research remains open without a current player-visible failure.

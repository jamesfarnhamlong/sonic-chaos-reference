# Sonic Chaos — RC2 Chief Private Baseline Acceptance
**21 November 2026 · Manager-San #13 · CHIEF APPROVED · private normal-game baseline frozen by decision**

## Authoritative decision
**Chief explicitly APPROVES `Sonic Chaos v0.99.5-rc2-c1` as the accepted PRIVATE RC2 normal-game baseline**, following the Manager's [final readiness recommendation](RC2_MANAGER_FINAL_CLOSEOUT_RECOMMENDATION_20261121.md). This **supersedes** `v0.99.4-rc2` for normal-game work and future integration baselines, with the older immutable branch/package and H: recovery retained as a **protected fallback**.

This is the **RC2 engineering + owner acceptance milestone**, not a v1.0 release. Approval authorises closing the finished private RC2 #11 and corrective C1 #13 engineering issues as completed with full history retained. It **does not authorise** a `main` merge, release/tag, publication, version relabel, an in-place ZIP modification, Super Sonic NG+ integration, the proposed `$A5` sound patch, broad camera/audio refactor, cleanup of SCTest, or deletion of archives. Any such action has a separate explicit Chief gate.

## Accepted source and artifact identities
| Item | Exact identity |
|---|---|
| Private production repository | `jamesfarnhamlong/SonicChaos_POC` |
| Accepted private source branch | `fix/rc2-c1-tails-boss-camera-20261117` |
| **Accepted GAME source commit** | **`115f166c41dd7236bce29345277872a39a5c0d2d`** |
| Accepted GAME tree | `c9032efc7b0328dbf3e2674329e5f54c80e4a5a0` |
| **Verification/package-only HEAD** | **`ca2650e38addffe6d61c1f16e2d3de84cb68f65e`** |
| Candidate label and Windows version | `v0.99.5-rc2-c1` / `0.99.5.3` |
| **Windows private 8-file ZIP SHA-256** | **`2b8b964c44e76c65fc65aa9cff709d413e1e55212c99251cb727c91d32d7b71e`** |
| **Full source ZIP +22 authenticated private deps SHA-256** | **`91057f1486354e81b87751c1a3d2558c4fcb14ea25a0163015d6f262bbd5b44b`** |
| Private Git bundle SHA-256 | `04973a3a2e5c264c65059134794f31ff2fd7cdb4a294e5d2c60c5d1dc95a83ef` |
| H: independent recovery copy | `H:\codex_backup\SonicChaos_20261102_essential\v0995-rc2-c1-20261117` |
| Protected older fallback game SHA | `342050ee1b237d37e7e17a6f6ea83b16655d0e6b` (`v0.99.4-rc2`) |
| Protected older fallback package SHA | `d064549cda914895c31ffbe62ff211c2d7eeb2b1` |
| Separate **not integrated** Super Sonic R3d | `21176dd03138b155412bef9256306437275414ca` |

Note that branch/package tip differs from the compiled game commit because the later commits affect **verification/** only. Do not identify the packaged game by the verification tip. This approval does not mean Git `main` has advanced to that commit or that any tag was created.

## Evidence and precise acceptance meaning
- Earlier **F1/F2 owner acceptance**: 17/17 issues/checks tested and accepted by Chief, plus a prior Classic Sonic full campaign and Enhanced Sonic one-emerald campaign. **F3 owner acceptance**: 6/6 tested Classic boss framing, Pause and Enhanced regression.
- The RC2-C1 corrective contained narrowly scoped **Classic 256px GPZ3 and EEZ3 boss-camera** changes plus release identity, no global physics or Enhanced overhaul. **Codex** verified a real compiled GPZ Tails flight-ceiling mismatch before correction; **Claude** corrected ROM canonical camera Y97 while preserving fight rendered top115, release114 and Tails flight ceiling worldY120/121. EEZ3 stage2 Tails high-flight camera min247/landing333 and 298/299 one-phase-offset ROM matches; other camera regression checks retained.
- Claude reported **60/60 compiled SCTest C1 runs PASS**, **0 observed Chief AppData writes**, R22 10/10 preservation+feature exact, Enhanced zero changed native rows in compared scenes, save suite 6/6. Inherited source suite **75/178 PASS**, one previously passing EEZ assertion intentionally corrected to ROM-exclusive 333 from a non-ROM 334; never represent the source suite as 178/178.
- **Chief smoke**, as actually reported: no visible new gameplay problem reported; existing saved games still exist and load **PASS**; GPZ3 visual check was tentative and EEZ3 high-flight precise ROM witness not confirmed, but numeric comparison is an **engineering responsibility**, not a user naked-eye test. No redundant boss campaigns demanded. **Chief now expressly approves the resulting private baseline**.
- 21 Nov Claude read-only integrity receipts: E: and H: manifests **12/12** matching, both ZIPs identical E:↔H:, prior `v0.99.4-rc2` backup **14/14**, clean GitHub tip, no new bundle/rebuild/tag. Manager independently verified GitHub identity, ancestry and documentation, **not physical bytes on Chief's drives**.

## Recorded non-blocking limitations
**No known RC2 baseline-blocking defect.** Do not silently declare total ROM-perfect behavior:
- SC-RC1-22: **confirmed missing `$A5` twist-gate sound** (real audible Classic fidelity difference); proposed minimal correction **not applied**, requires separate Chief approval and versioned new build if adopted.
- SC-RC1-25: spring `$A6` audio mailbox class differs; potential unproven audible deviation. Spring Shoes `$A4` suppression was ROM-authentic.
- SC-RC1-17 loop watch, 18 GPZ3 pipe seams not reproduced, 19 attract demos end early (measured parity HOLD), GPZ3 post-flight 1px rounding, one-update camera commit pipeline, GEN8-only `data.win` metadata rebuild variation, inherited source harness75/178 remain documented.
- R-FS1 fullscreen issue confirmed by Chief as **SCTest-account-only**, not a release blocker. Crumble SC-RC1-26 authentic and SC-RC1-21 twist freeze false positive.
- There was no new full human campaign on C1; inherited Chief-tested full campaigns and native preservation make that a non-blocking process limitation for the **private baseline**.

## Engineering closeout and next-gate ownership
- Private [RC2 engineering #11](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/11) and [RC2-C1 corrective #13](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/13) should be **CLOSED as completed** on this Chief acceptance, with their previous findings/comments retained.
- Original v0.99.4 RC2, accepted F3, Classic freeze, private Super R3d branch, complete C1 package, H: copies and all live saves remain protected; **no cleanup** performed by this documentation step.
- Suggested **later, separately commissioned** choice: Super Sonic R3d opt-in integration atop the exact accepted RC2-C1 GAME source (not its package tip), versus a small Classic `$A5` sound fidelity correction. Treat each as a new branched candidate with separate provenance and preservation, never mutate RC2 baseline in place.
- Public v1.0 release preparation, code promotion to `main`, signing/tagging and actual distribution remain **NOT AUTHORISED** and not implied by this baseline acceptance.

**Formal status: RC2 PRIVATE NORMAL-GAME BASELINE — CHIEF ACCEPTED on 21 November 2026.**

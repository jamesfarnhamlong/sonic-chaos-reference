# Sonic Chaos — Current base-game finish register
**Owner-led planning list · updated 2 November 2026**

For active coordination consult [AGENTS.md](../AGENTS.md) and [ROADMAP.md](../ROADMAP.md). This is a **small live/parked issue register**, not the entire original 93-ID AUDIT-0 archive. [Previous verbose version is preserved in Git history](archive/management/MANAGER_PRE_REWRITE_20261102.md). Historical source classifications are kept in [AUDIT-0](audit0/README.md), the [AUDIT-1 evidence branch](https://github.com/jamesfarnhamlong/SonicChaos_POC/tree/ad01199ad131f66e5f4e54a5308b611e638703f5/docs/audit1) and [Chief's 21-item triage](chief-current-issue-triage-20261101.md).

## CURRENT — CORRECTIVE A READY; NO FURTHER CONFIRMED CODE FIX, CHIEF ACCEPTANCE PENDING

**3 Nov `fc19b3f`:** source/Windows corrective package created by Designer, H: preservation verified, no new source edits after report. ROM-backed fixes for Tails flight cancellation, AQZ $1E wall projection for both characters, AQZ monitor poof indexed palette / +18 anchor / 40-update animation. Automated focused PASS: 6,880 paired AQZ updates, 37 SFX programmes, 68 F2 catalogue, native startup/Windows ordinary export; five inherited raw verifier failures unchanged. **Chief check outstanding only for three areas**: AQZ exploding monitors, Tails flight cancellation, AQZ wall movement. Boss-theme overwrite and THZ3 jump-overlap spike silence proven canonical, Chief explicitly preserves. MGHZ falling $24 hazard footwear/range provisionally accepted. Both Sonic/Tails complete campaigns were on `8b3b435`, which remains frozen as previous checkpoint.

**Updated issues:** [104-row current spreadsheet-compatible CSV](tracking/SonicChaos_CURRENT_Issue_Tracker_20261103.csv) and [watchlist](tracking/README.md); AM-san's 93-entry AUDIT0 unchanged and historical counts are NOT active release bugs. Remaining non-blockers are optional attract demos and results Pause gating, first-start audio delay, unverified end-boss Tails vertical pursuit, unreproduced extreme Tails roll, SFX $B8/three requester evidence gaps, inherited raw verifier exceptions. No new mass audit or new gameplay fix instructed.

## PREVIOUS — Current production truth

**M6-H/MGHZ-007: CHIEF F5 ACCEPTED 2 NOV — RESOLVED.** Chief tested the single private `SonicChaos_M6H_20261102_A_PRIVATE.zip` and confirmed: **"Yes, perfect! No notes, thats now working as intended."** Initial 348-wide camera right edge between spike3/4 without tree; proper boss/pole reveal; all eight spikes, fight and transition accepted. [Chief acceptance receipt](m6h-chief-acceptance-and-base-status-20261102.md). **No mandatory MGHZ3 fix remains.**

**M6-H published:** accepted production implementation `c3e40a7a3d6c17be3e17d7c1eb729b2a705a3089` with follow-up verification/docs branch HEAD `64a5a53ceebed43ed79e36a681a27b0d6a0c16aa`. Candidate B packaging smoke PASS is separately reported; renamed `SonicChaos.yyp` / `SonicChaos.exe` and startup guard remain uncommitted on `production/final-packaging-20261102`. No automatic main merge.

Other accepted functionality: Sonic/Tails, five Special Stages, all known-use music via native default, Sound Test, goal km/h, Robotnik opening border, widescreen cards/choice, removed dev shortcuts, recoverable rings, bees and regular enemies in their scoped accepted tests. Avoid another global audit of previously accepted work.

## 3 Nov — ROM movement findings and AQZ music CANONICAL, no production edits

Designer reports **bounded original-ROM parity PASS** for Tails acceleration, friction, speed caps and spin-dash release. Chief's abnormal roll-speed burst was **not reproduced**; do not adjust speeds from feel. **Two genuine GameMaker movement mismatches identified**: (1) missing terrain-probe flags, **Tails flight cancellation differs from tick 2**, and (2) missing surface `$1E` wall projection in AQZ, **differs at tick 61 with velocity divergence the next tick**, affecting **both characters**. Correct only verified divergences and protect authentic dry/water table values.

**Boss music verdict: ROM CONFIRMED / CHIEF ACCEPTED CANON.** The AQZ invincibility timer can replace boss music with zone music in the original game; Chief requests preservation, **no boss-music override, FT-08 CLOSED**. Prior text calling it unresolved is historical. Full private ROM reports at local `management-audits/tails-movement-20261103/REPORT.md` and `AQZ-MUSIC.md`. `8b3b435` source and ZIPs unchanged; no new build. Remaining required investigation: FT-01 THZ3 SFX + all-SFX automated matrix; FT-05 AQZ monitor explosion palette/position; targeted corrections to two confirmed movement divergences. [Current grouped issue register](tails-final-campaign-defect-triage-20261103.md).

## PREVIOUS — Sonic full-campaign result, shared AQZ observations

**Chief has completed both Tails AND Sonic complete natural campaigns** on the *same unchanged* 3 Nov ZIP / local `8b3b435`. Sonic additionally exercised **part of** the emerald route (not a new complete Special Stage sweep) and reported **NO additional defects**. Shared repeat observations: AQZ1/2 television explosion palette + vertical offset, and AQZ boss `$8C` music replaced by zone `$93` when incoming invincibility wears off. Tails movement (dry and underwater), THZ3 missing spike SFX and other earlier Tails findings remain open; the dedicated Tails physics parity audit is **ongoing**. [Consolidated Chief-run issue ledger](tails-final-campaign-defect-triage-20261103.md).

**Boss music canonical question UNRESOLVED:** Original timer restore `$189B` respects `$D4A3` music guard; `$D44E` marks AQZ boss activity separately. Need true ROM boss-invincibility overlapping timeline before claiming it is an original bug. If canon, ask Chief whether intentional PC improvement to keep boss track; if noncanon, fidelity correction. Do not infer original behavior from two GameMaker repeats. No extra full Sonic run requested; one grouped correction after final Tails/SFX/audio/TV verification.

## PREVIOUS — Tails full campaign result (3 Nov 2026) — RELEASE HOLD

Chief completed the Tails campaign in the exact final candidate `8b3b435`, identified **nine observations**. Sonic complete campaign of that same unchanged ZIP is now underway; **don't rebuild or alter it mid-test**. [Full final-campaign defect register](tails-final-campaign-defect-triage-20261103.md).

**P0: THZ3 moving spike missing $A7** (Chief requests all-SFX automated ROM-to-production audit, no manual 37-SFX checking); **P0: Tails ordinary ground roll/spin dash very excessive/slippery/abrupt speed**; **P0: boss AQZ invincibility expiry restores zone music over boss $8C**. **P1: AQZ1/2 destroyed monitor explosion wrong palette and raised position**; **P1: Tails underwater braking/momentum feels too strong**. These are potential release blockers to adjudicate with exact original-ROM traces and current GameMaker source. **P2 deferred:** pause during results (Chief retaining temporary debug), post-final-boss vertical Tails pursuit (ROM camera/input study).

**Chief follow-up:** MGHZ falling hazard Spring Shoes ring loss and slow-to-trigger coconut proximity are **provisionally CLOSED as canonical $24 behaviour** based on ROM research; they are NOT active fix requests. Confirm exact object identity opportunistically. Tails **full dry+underwater movement audit** is top priority, including fixed-point/Step translation and same-input comparison with Sonic control; if ROM is genuinely this slippery, explain and don't blindly retune. Allow source/ROM investigation while Sonic playthrough continues, but one grouped correction candidate after full findings. 

## PREVIOUS BASE GATE — historical state before Chief complete campaign

| Priority | Work | Required result |
| --- | --- | --- |
| **1 — M6-H source preservation** | Accepted production commit `c3e40a7...` published. | COMPLETE; keep baseline unchanged. |
| **2 — $A7 spike environmental audio** | Original sleep/callback lifecycle restored locally; Chief accepted corrected F5 on 3 Nov. | **CHIEF ACCEPTED; exact tested local commit `8e9d224...` recorded, not pushed.** |
| **2 — Chief full base playthrough** | Complete one normal run of the current accepted game and note only genuinely new reproducible defects, if any. | Short consolidated punch list, not dozens of repeated feature acceptance tests. |
| **3 — base freeze** | If no substantial new issue is observed, Chief approves a reproducible private baseline. | Exact source SHA + complete GameMaker project, private dependencies, manifest/SHA-256, independent backup and restore/open proof, source/native policy exceptions documented. |

**Current gameplay position:** The known $A7 distant spike repetition is **Chief F5 ACCEPTED in observed scope**, and its exact corrected source is now committed locally as `8e9d22499dc910922bd788346bb35678b4a28494` (not yet pushed). No other mandatory defect is currently open; Chief's ongoing full Sonic/Tails playthrough may surface new issues.

## PROD-AUDIO-A7-REPEAT — CHIEF F5 ACCEPTED (3 Nov 2026)

Chief tested the **corrected live project** `E:\AI\Codex\Sonic Chaos\SonicChaos_Production\SonicChaos.yyp` and reported **"That one works fine as far as i can see."** This supersedes the 3 Nov distant-$A7 reproduction in older `SonicChaos_Production_20261102_SOURCE_PRIVATE_B`, which predated the fix. **Spike repetition issue closed in observed Windows F5 scope**, no further human test or wider speculative environmental-sound audit requested. No claim of exhaustive all-route proof.

ROM/oracle and GameMaker source evidence is in Designer's private `docs/production/environmental-audio-audit.md` / `verification/environment-audio/`: $1B moving-spike inactive/sleep and one-shot script-entry timing; 4,962 new focused checks PASS and adjacent environmental contract regressions. Three runtime scripts were changed locally: `SCR_chaos_spike1b`, `SCR_chaos_objects`, `SCR_chaos_adapter`; enemy/flying/ring retention code unchanged. Other environmental requester sites were reviewed; no other repeating-distance defect demonstrated, but not every rare natural audio route exhaustively tested.

**Source committed locally; independent recovery/push pending:** Designer reported exact Chief-tested runtime at `8e9d22499dc910922bd788346bb35678b4a28494`, with all 558 protected GML hashes unchanged and packaging/cleanup edits excluded. No push/build/package/new worktree. Before major workspace deletion, verify this exact commit is in a freshly validated H: Git bundle/scratch restore; preserve `SonicChaos_Production` and its earlier pending packaging changes. Do not imply it has been pushed. No new builds/worktrees and no main merge. Keep the current clean `SonicChaos.yyp` source project and avoid unnecessary files in future source ZIP/EXE packages. Source ZIP must include **all registered GameMaker resources** (or remove unwanted note resources properly from the project before packaging); executable ZIP contains only demonstrated necessary runtime assets. Chief has additional major-cleanup results to review separately.

## PARKED (owner instruction; not to be auto-assigned)

| ID/topic | What remains documented | Disposition |
| --- | --- | --- |
| `AUDIO-006` startup | First launch/onset delay, seemingly not recurring after initialization; low-level F8 AF carry mismatch with exact audio output is distinct. | **Parked**; measure before adding splash/silent cards; F8 is technical exception. |
| `SEZ-002`, `SS-001`, `PLAYER-001` | Historical monitor/Spring Shoes, SS3 embed and rebound/contact reports; original-source narrow runs did not reproduce precise old symptoms. | Preserve original issue IDs, activate only on new current reproduction. |
| `AQZ` Tails palette | Underwater visual difference subtler than Sonic in original footage; previous tests passed. | Owner **provisionally satisfied**; no automatic palette changes. |
| `FRONTEND-002` attract demos | Original idle demonstrations missing, previous replay-input reconstruction complex. | **Explicitly post-base**. |
| Optional save / emerald progression | Sonic 3-like persistent emerald progress and Level Select unlock. | **Explicitly post-base**; game short, not required now. |
| Frame rate / graphics / Vita | AM-san proposals described in roadmap. | **Enhancements only after full base playthrough and owner approval**. |
| Local workspace hygiene | Roughly **170 worktrees/packages/folders**. | Archive-plan-only until base freeze; no Janitor, no deletion without owner-approved dry-run+verified backups. |

## Believed fixed, inactive — Chief's 12-item shortlist

`EARLY-011` spring opaque/green edge; `MGHZ-006` slope/spring oscillation; `SEZ-001` Spring Shoes temporary lock; `SEZ-003` crumble fragments; `AQZ-002` ring animation; `PRES-002` title/cards widescreen; `PLAYER-002` vibration; `PLAYER-003` diagonal spikes; `PLAYER-004` moving-spike phase; `TAILS-006` shoes/monitor uncertainty; `AUDIO-001` known-use audio coverage; `AUDIO-004` ring-SFX latency. “Believed fixed” is an owner-priority status, **not** a mathematically exhaustive route proof; do not ask Chief to check them again unless new actual symptoms arise.

## Subsequently resolved from Chief's originally retained nine

- `MGHZ-007`: Correct original spike3/4 gate, hidden pre-reveal tree and complete boss arena; M6-H private candidate accepted by Chief F5 on 2 November 2026, exact source commit publication pending. [Receipt](m6h-chief-acceptance-and-base-status-20261102.md).
- `OPENING-001`: Robotnik passes **behind** foreground bars; M6-C2 Chief F5 accepted.
- `RESULTS-001`: Authentic type$19 km/h panel, scoring formula + glyphs/timing; M6-D Chief F5 accepted. Earlier Manager's categorical assertion “no SMS km/h” was **wrong**.
- `FRONTEND-003`: **All** developer-only keyboard shortcuts retired in M6-D, not merely F10; Pause→Level Select remains usable.

## Technical holds / honest source boundaries

- M6-F integrated source tests: **15 PASS / one raw FAIL** from an obsolete assertion that the $27 flying family must retire at strict player384 in *all widths*. New widening is deliberately a PC QoL exception; native256 still tests original. Earlier SS5 256px camera, THZ3 old cap, and F8 carry exceptions remain separately documented.
- Original M5 driver: 25/25 known-use music Chief accepted; 63/63 actual playable Sound Test programmes; 5 empty; unused$8E with no proven retail requester. Some SFX natural site coverage and Continue presentation remain historically unobserved, not a general missing-soundtrack failure.
- Controlled original-ROM tests did not establish the missing THZ2 twin-column vertical bee route; Chief's natural M6-F F5 **FAIL** overrides prior alias PASS. GPZ3 high-hit ring recovery has now been **Chief-native accepted in scope**; source tests should guard it during R1 but no further human ring trial required.
- Private ROM/audio/art binaries and user videos do not belong in public reference repository; no automatic main merge, public distribution or executable package release.

## Next update rule

**M6-H/MGHZ-007 is Chief-accepted, source committed and closed.** Chief's corrected-source $A7 F5 has passed; full Sonic/Tails playthrough continues with no repeat isolated SFX tests. If no new significant defect, prepare the private freeze checkpoint and get owner approval. Do not reopen accepted music, camera, enemy, ring or original scoring milestones without a fresh reproduction.

After the full playthrough, add only **new owner-confirmed** issues. Do not transplant the old 93-row issue ledger into the current backlog.

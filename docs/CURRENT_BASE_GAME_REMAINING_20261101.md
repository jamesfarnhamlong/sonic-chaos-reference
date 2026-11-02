# Sonic Chaos — Current base-game finish register
**Owner-led planning list · updated 2 November 2026**

For active coordination consult [AGENTS.md](../AGENTS.md) and [ROADMAP.md](../ROADMAP.md). This is a **small live/parked issue register**, not the entire original 93-ID AUDIT-0 archive. [Previous verbose version is preserved in Git history](archive/management/MANAGER_PRE_REWRITE_20261102.md). Historical source classifications are kept in [AUDIT-0](audit0/README.md), the [AUDIT-1 evidence branch](https://github.com/jamesfarnhamlong/SonicChaos_POC/tree/ad01199ad131f66e5f4e54a5308b611e638703f5/docs/audit1) and [Chief's 21-item triage](chief-current-issue-triage-20261101.md).

## Current production truth

**M6-H/MGHZ-007: CHIEF F5 ACCEPTED 2 NOV — RESOLVED.** Chief tested the single private `SonicChaos_M6H_20261102_A_PRIVATE.zip` and confirmed: **"Yes, perfect! No notes, thats now working as intended."** Initial 348-wide camera right edge between spike3/4 without tree; proper boss/pole reveal; all eight spikes, fight and transition accepted. [Chief acceptance receipt](m6h-chief-acceptance-and-base-status-20261102.md). **No mandatory MGHZ3 fix remains.**

**Published source caveat:** At acceptance the M6-H branch `poc/m6h-mghz3-spike-gated-reveal` was **uncommitted/unpushed**. The last immutable, publicly committed *source* checkpoint remains **M6-G** `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905`, while the **accepted playable candidate** is M6-H private ZIP. Designer must publish the exact accepted diff (no code changes) and provide SHA/manifest concordance. No automatic merge or new microtest.

Other accepted functionality: Sonic/Tails, five Special Stages, all known-use music via native default, Sound Test, goal km/h, Robotnik opening border, widescreen cards/choice, removed dev shortcuts, recoverable rings, bees and regular enemies in their scoped accepted tests. Avoid another global audit of previously accepted work.

## ACTIVE — final base gate (no mandatory production bug currently confirmed)

| Priority | Work | Required result |
| --- | --- | --- |
| **1 — closure administration** | Publish exact Chief-approved M6-H candidate on its source branch from M6-G; no gameplay modifications or extra F5. | Full commit SHA, clean local/remote, source-vs-private-ZIP/diff hash, no copyrighted/private asset publication, no main merge. |
| **2 — Chief full base playthrough** | Complete one normal run of the current accepted game and note only genuinely new reproducible defects, if any. | Short consolidated punch list, not dozens of repeated feature acceptance tests. |
| **3 — base freeze** | If no substantial new issue is observed, Chief approves a reproducible private baseline. | Exact source SHA + complete GameMaker project, private dependencies, manifest/SHA-256, independent backup and restore/open proof, source/native policy exceptions documented. |

**Currently confirmed mandatory implementation defects: NONE.** This does not mean every rare route was exhaustively exercised by a complete natural campaign; it means the agreed current bug queue is closed pending the final normal run.

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

**M6-H/MGHZ-007 is Chief-accepted and closed.** Publish the exact accepted M6-H source commit (without altering gameplay), record the new full SHA and manifest parity, then Chief completes the full base-game playthrough. If no new significant defect, prepare the private freeze checkpoint and get owner approval. Do not reopen accepted music, camera, enemy, ring or original scoring milestones without a fresh reproduction.

After the full playthrough, add only **new owner-confirmed** issues. Do not transplant the old 93-row issue ledger into the current backlog.

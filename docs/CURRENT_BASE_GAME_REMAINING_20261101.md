# Sonic Chaos — Current base-game finish register
**Owner-led planning list · updated 2 November 2026**

For active coordination consult [AGENTS.md](../AGENTS.md) and [ROADMAP.md](../ROADMAP.md). This is a **small live/parked issue register**, not the entire original 93-ID AUDIT-0 archive. [Previous verbose version is preserved in Git history](archive/management/MANAGER_PRE_REWRITE_20261102.md). Historical source classifications are kept in [AUDIT-0](audit0/README.md), the [AUDIT-1 evidence branch](https://github.com/jamesfarnhamlong/SonicChaos_POC/tree/ad01199ad131f66e5f4e54a5308b611e638703f5/docs/audit1) and [Chief's 21-item triage](chief-current-issue-triage-20261101.md).

## Current production truth

**Chief-accepted base source:** `SonicChaos_POC@a4c26e13bc323a9f736c613c279b447dd6aedef5` (M6-E widescreen character selection, F5 PASS).

**M6-F Chief split verdict + M6-F-R1 review (2 Nov):** GPZ3 high-Y off-top rings **CHIEF PASS**; triggered THZ2 bee persistence **FAIL in original M6-F**. Corrective M6-F-R1 `poc/m6f-r1-bee-vertical-retention@636ed72be111bc3de4c297e5768c40c8f38a54e6` is now **MANAGER GO, one Chief THZ2 F5 PENDING**. Original THZ2 controlled removal185/recreation197 replaced with triggered state/identity continuity; only placement helper modified, rings byte-identical. [Current R1 Manager gate](m6fr1-manager-review-chief-gate-20261102.md). M6-E remains last fully Chief-accepted source until R1 passes.

Previously Chief accepted: M5 native known-use music and Sound Test; Robotnik foreground opening; original rolling km/h results-panel graphics/scoring; removal of ALL developer keyboard shortcuts while preserving Pause→Level Select; widescreen title/results cards and character select; both characters, campaign, bosses, five Special Stages and endings in prior scoped tests. Do not reopen without a fresh specific regression.

## ACTIVE — only the real near-term gate

| Priority | Feature/issue | Acceptance or decision |
| --- | --- | --- |
| **1 — M6-F-R1** | **THZ2 bee triggered offscreen identity/patrol correction**; GPZ3 rings already accepted. | Source/ROM proof PASS, commit `636ed72be…` Manager GO. Chief only needs (A) twin-column fall/spring and (B) follow from below/right in one F5. Protect passing ring fix; no broader builds/retests. |
| **2 — full playthrough** | Chief will complete **one full game run before any FPS/graphics enhancements**. | Collect current substantial gameplay/presentation concerns, without another broad mandatory re-audit of 93 historical IDs. |
| **3 — base decision** | Chief might report one or two further tweaks. | Fix any demonstrated base blocker in a meaningful batch; then Chief explicitly approves a private base checkpoint/source manifest. |

**No other production bug is currently Chief-confirmed as a mandatory blocker.** Historical contact quirks remain as observations, not guaranteed permanent absence.

## PARKED (owner instruction; not to be auto-assigned)

| ID/topic | What remains documented | Disposition |
| --- | --- | --- |
| `MGHZ-007` | Boss approach works, but Chief considers the 348-wide pit/pole/boss framing aesthetically messy; widescreen camera pan differs from original 256 rhythm. | **Parked visual polish**, not declared fixed; owner decides if needed before base freeze. |
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

- `OPENING-001`: Robotnik passes **behind** foreground bars; M6-C2 Chief F5 accepted.
- `RESULTS-001`: Authentic type$19 km/h panel, scoring formula + glyphs/timing; M6-D Chief F5 accepted. Earlier Manager's categorical assertion “no SMS km/h” was **wrong**.
- `FRONTEND-003`: **All** developer-only keyboard shortcuts retired in M6-D, not merely F10; Pause→Level Select remains usable.

## Technical holds / honest source boundaries

- M6-F integrated source tests: **15 PASS / one raw FAIL** from an obsolete assertion that the $27 flying family must retire at strict player384 in *all widths*. New widening is deliberately a PC QoL exception; native256 still tests original. Earlier SS5 256px camera, THZ3 old cap, and F8 carry exceptions remain separately documented.
- Original M5 driver: 25/25 known-use music Chief accepted; 63/63 actual playable Sound Test programmes; 5 empty; unused$8E with no proven retail requester. Some SFX natural site coverage and Continue presentation remain historically unobserved, not a general missing-soundtrack failure.
- Controlled original-ROM tests did not establish the missing THZ2 twin-column vertical bee route; Chief's natural M6-F F5 **FAIL** overrides prior alias PASS. GPZ3 high-hit ring recovery has now been **Chief-native accepted in scope**; source tests should guard it during R1 but no further human ring trial required.
- Private ROM/audio/art binaries and user videos do not belong in public reference repository; no automatic main merge, public distribution or executable package release.

## Next update rule

M6-F original received ring PASS/enemy FAIL. **Corrective R1 is now packaged and Manager GO**; awaiting only one THZ2 two-scenario Chief F5. On PASS, promote `636ed72be111bc3de4c297e5768c40c8f38a54e6` as fully accepted production baseline and start Chief full playthrough. On FAIL, record the specific scenario and avoid reopening accepted rings.

After the planned **full playthrough**, add only the new owner-confirmed findings. Do not transplant the old 93-row issue ledger into the current backlog.

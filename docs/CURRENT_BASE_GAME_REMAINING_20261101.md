# Sonic Chaos — Current base-game finish register
**Owner-led planning list · updated 2 November 2026**

For active coordination consult [AGENTS.md](../AGENTS.md) and [ROADMAP.md](../ROADMAP.md). This is a **small live/parked issue register**, not the entire original 93-ID AUDIT-0 archive. [Previous verbose version is preserved in Git history](archive/management/MANAGER_PRE_REWRITE_20261102.md). Historical source classifications are kept in [AUDIT-0](audit0/README.md), the [AUDIT-1 evidence branch](https://github.com/jamesfarnhamlong/SonicChaos_POC/tree/ad01199ad131f66e5f4e54a5308b611e638703f5/docs/audit1) and [Chief's 21-item triage](chief-current-issue-triage-20261101.md).

## Current production truth

**Chief-accepted base source:** `SonicChaos_POC:poc/m6g-all-enemy-persistence@6e2ffcc1f333c5cdaa0048ac696b55c4f6308905` (**M6-G Chief F5 PASS** on THZ ground patroller, GPZ ground patroller and SEZ `$20` hopper). R1 ring/bee acceptance preserved. [M6-G Chief receipt](m6g-chief-acceptance-20261102.md).

**Current phase (2 Nov):** M6-G is **CHIEF ACCEPTED**, not pending. Seven regular enemy numeric types / 95 placements inventoried; five types received source changes, original flying aliases retained. Chief found all 3 natural F5 encounters behaved as expected, enemies feel more natural and reset less. Seeing two SEZ left-moving enemies simultaneously is not proof of duplicate occupancy: `$20` and `$23` travel left rather than patrol bidirectionally; original independent placements and finite long-distance recreation are legitimate possibilities. No new SEZ bug opened. 19 source checks PASS / **2 raw FAIL**, one inherited viewport384 and one newly superseded SEZ wide-Y delete; inherited `$21` falling-asleep adapter and GPZ below-map record remain documented technical exceptions. **Next: Chief complete base playthrough before enhancements.**

Previously Chief accepted: M5 native known-use music and Sound Test; Robotnik foreground opening; original rolling km/h results-panel graphics/scoring; removal of ALL developer keyboard shortcuts while preserving Pause→Level Select; widescreen title/results cards and character select; both characters, campaign, bosses, five Special Stages and endings in prior scoped tests. Do not reopen without a fresh specific regression.

## ACTIVE — only the real near-term gate

| Priority | Feature/issue | Acceptance or decision |
| --- | --- | --- |
| **1 — base-game playthrough** | **Chief tests normal end-to-end game on accepted M6-G source** | M6-G **CHIEF PASS**. Collect only newly observed concrete gameplay/progression problems in one punch list, then decide any final meaningful fixes and explicit private base freeze. No repeat ring/bee/patrol microtests. |
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

M6-F-R1 and M6-G are **fully Chief accepted**. The next owner action is a normal full base-game playthrough on `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905`, after which any concrete issues can be triaged and Chief can explicitly approve base freeze. No active code/ZIP candidate awaits F5; enhancements remain deferred.

After the planned **full playthrough**, add only the new owner-confirmed findings. Do not transplant the old 93-row issue ledger into the current backlog.

# Sonic Chaos — Current base-game finish register
**Owner-led planning list · updated 2 November 2026**

For active coordination consult [AGENTS.md](../AGENTS.md) and [ROADMAP.md](../ROADMAP.md). This is a **small live/parked issue register**, not the entire original 93-ID AUDIT-0 archive. [Previous verbose version is preserved in Git history](archive/management/MANAGER_PRE_REWRITE_20261102.md). Historical source classifications are kept in [AUDIT-0](audit0/README.md), the [AUDIT-1 evidence branch](https://github.com/jamesfarnhamlong/SonicChaos_POC/tree/ad01199ad131f66e5f4e54a5308b611e638703f5/docs/audit1) and [Chief's 21-item triage](chief-current-issue-triage-20261101.md).

## Current production truth

**Chief-accepted base source:** `SonicChaos_POC@636ed72be111bc3de4c297e5768c40c8f38a54e6` (**M6-F-R1 Chief PASS**: GPZ3 high-Y ring recovery + THZ2 bee encounter retention).

**Current milestone (2 Nov): M6-G has completed source implementation and is MANAGER GO / Chief F5 PENDING** at `SonicChaos_POC:poc/m6g-all-enemy-persistence@6e2ffcc1f333c5cdaa0048ac696b55c4f6308905`, one commit after fully Chief-accepted R1. Five regular enemy types changed, two flying types unchanged; 95 placements mapped. Source gate **19 PASS / two raw FAIL** (one inherited viewport384 assertion, one newly superseded SEZ wide-Y removal rule); known THZ `$21` falling-asleep mismatch and GPZ1 below-world record retained. Single Chief check: THZ patroller vertical departure, GPZ patroller backtrack, SEZ hopper. No ring/bee human retests. [M6-G Manager review](m6g-manager-review-chief-f5-gate-20261102.md); [original directive](m6g-regular-enemy-persistence-chief-directive-20261102.md).

Previously Chief accepted: M5 native known-use music and Sound Test; Robotnik foreground opening; original rolling km/h results-panel graphics/scoring; removal of ALL developer keyboard shortcuts while preserving Pause→Level Select; widescreen title/results cards and character select; both characters, campaign, bosses, five Special Stages and endings in prior scoped tests. Do not reopen without a fresh specific regression.

## ACTIVE — only the real near-term gate

| Priority | Feature/issue | Acceptance or decision |
| --- | --- | --- |
| **1 — M6-G** | **Five-family enemy persistence correction; existing `$27/$2C` flying acceptance preserved** | Integrated candidate `6e2ffcc1…` **Manager GO / Chief native F5 pending**. THZ patrol vertical return, GPZ patrol moderate backtrack, SEZ hopper depart/return in one session. Explicit native `$25` callback correction; two raw policy tests remain FAIL; no other Chief retests. |
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

M6-F-R1 remains **fully Chief accepted**. M6-G implementation is complete and **Manager GO, but NOT yet Chief accepted**. Await its one THZ/GPZ/SEZ F5 session; promote `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905` only if Chief passes. Then Chief's full normal playthrough precedes any enhancements.

After the planned **full playthrough**, add only the new owner-confirmed findings. Do not transplant the old 93-row issue ledger into the current backlog.

# Sonic Chaos — Current base-game finish register
**Owner-led planning list · updated 2 November 2026**

For active coordination consult [AGENTS.md](../AGENTS.md) and [ROADMAP.md](../ROADMAP.md). This is a **small live/parked issue register**, not the entire original 93-ID AUDIT-0 archive. [Previous verbose version is preserved in Git history](archive/management/MANAGER_PRE_REWRITE_20261102.md). Historical source classifications are kept in [AUDIT-0](audit0/README.md), the [AUDIT-1 evidence branch](https://github.com/jamesfarnhamlong/SonicChaos_POC/tree/ad01199ad131f66e5f4e54a5308b611e638703f5/docs/audit1) and [Chief's 21-item triage](chief-current-issue-triage-20261101.md).

## Current production truth

**Chief-accepted base source:** `SonicChaos_POC:poc/m6g-all-enemy-persistence@6e2ffcc1f333c5cdaa0048ac696b55c4f6308905` (**M6-G Chief F5 PASS** on THZ ground patroller, GPZ ground patroller and SEZ `$20` hopper). R1 ring/bee acceptance preserved. [M6-G Chief receipt](m6g-chief-acceptance-20261102.md).

**Current phase (2 Nov):** M6-G remains **CHIEF ACCEPTED**, with THZ/GPZ patrol/SEZ hopper F5 PASS. Chief has now reported and illustrated a **precise new MGHZ3 WIDE CAMERA BUG: MGHZ-007 REOPENED**. Existing approach limit shows central tree before boss reveals; original first camera right locks **between spike3/4** (tree unseen) before the camera unveils spike4–8/tree/boss. Accepted wide mode uses final boss target X2969 to constrain pre-reveal camera, displaying world through X3317, already past the original central tree near world3264. This is source-supported leading hypothesis, not yet tested as final patch. Branch M6-H from accepted M6-G, derive exact source camera/spike coordinates, produce one consolidated candidate and one owner MGHZ3 acceptance; then resume full playthrough. [Binding M6-H specification](m6h-mghz3-spike-gated-boss-reveal-20261102.md).

Previously Chief accepted: M5 native known-use music and Sound Test; Robotnik foreground opening; original rolling km/h results-panel graphics/scoring; removal of ALL developer keyboard shortcuts while preserving Pause→Level Select; widescreen title/results cards and character select; both characters, campaign, bosses, five Special Stages and endings in prior scoped tests. Do not reopen without a fresh specific regression.

## ACTIVE — only the real near-term gate

| Priority | Feature/issue | Acceptance or decision |
| --- | --- | --- |
| **1 — M6-H, MGHZ-007 ACTIVE** | **MGHZ3 boss pre-reveal right lock is too far forward in 348-wide**. Chief's canonical comparison: initial right edge **between spikes3/4**, no central tree shown; subsequent camera unlock/reveal exposes spikes4–8, tree and boss at original world anchor. | Authorized source-backed camera/staging fix on a new branch from M6-G. Original ROM/map must yield exact spike-world boundary, native256 pan and cameraY. Preserve boss spawn/trigger/HUD/combat/clear, authored assets/terrain and left backtrack constraint. ONE integrated candidate and ONE Chief MGHZ3 F5. [M6-H directive](m6h-mghz3-spike-gated-boss-reveal-20261102.md). |
| **2 — full base playthrough** | **Chief resumes complete normal end-to-end game** after M6-H's one visual acceptance | Collect new issues into one punch list, then Chief decides private base freeze; no broad re-audit of accepted sound/rings/bees/patrols. |
| **2 — full playthrough** | Chief will complete **one full game run before any FPS/graphics enhancements**. | Collect current substantial gameplay/presentation concerns, without another broad mandatory re-audit of 93 historical IDs. |
| **3 — base decision** | Chief might report one or two further tweaks. | Fix any demonstrated base blocker in a meaningful batch; then Chief explicitly approves a private base checkpoint/source manifest. |

**No other production bug is currently Chief-confirmed as a mandatory blocker.** Historical contact quirks remain as observations, not guaranteed permanent absence.

## PARKED (owner instruction; not to be auto-assigned)

| ID/topic | What remains documented | Disposition |
| --- | --- | --- |
| `MGHZ-007` | **PROMOTED TO ACTIVE M6-H** (see first row). Historical M6-A no-code-close was based on insufficiently precise scene framing comparison; Chief now specifies exact spike3/4 pre-lock and tree/boss reveal ordering. | **NOT PARKED**, never classified fixed; do not reintroduce here as an optional aesthetic concern. |
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

M6-F-R1 and M6-G are **fully Chief accepted**. **Current development task is M6-H MGHZ3 camera reveal correction**, requested with precise screenshot and eight-spike timing by Chief; no accepted M6-H build exists yet. Keep accepted M6-G as production parent. Chief's full playthrough can resume after the single MGHZ3 F5 gate; then private base freeze and optional enhancements. Don't resurrect any of the already settled original audio/rings/enemy issues.

After the planned **full playthrough**, add only the new owner-confirmed findings. Do not transplant the old 93-row issue ledger into the current backlog.

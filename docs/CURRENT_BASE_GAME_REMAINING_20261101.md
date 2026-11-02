# Sonic Chaos — Current base-game finish register
**Owner-led planning list · updated 2 November 2026**

For active coordination consult [AGENTS.md](../AGENTS.md) and [ROADMAP.md](../ROADMAP.md). This is a **small live/parked issue register**, not the entire original 93-ID AUDIT-0 archive. [Previous verbose version is preserved in Git history](archive/management/MANAGER_PRE_REWRITE_20261102.md). Historical source classifications are kept in [AUDIT-0](audit0/README.md), the [AUDIT-1 evidence branch](https://github.com/jamesfarnhamlong/SonicChaos_POC/tree/ad01199ad131f66e5f4e54a5308b611e638703f5/docs/audit1) and [Chief's 21-item triage](chief-current-issue-triage-20261101.md).

## Current production truth

**M6-H/MGHZ-007: CHIEF F5 ACCEPTED 2 NOV — RESOLVED.** Chief tested the single private `SonicChaos_M6H_20261102_A_PRIVATE.zip` and confirmed: **"Yes, perfect! No notes, thats now working as intended."** Initial 348-wide camera right edge between spike3/4 without tree; proper boss/pole reveal; all eight spikes, fight and transition accepted. [Chief acceptance receipt](m6h-chief-acceptance-and-base-status-20261102.md). **No mandatory MGHZ3 fix remains.**

**M6-H published:** accepted production implementation `c3e40a7a3d6c17be3e17d7c1eb729b2a705a3089` with follow-up verification/docs branch HEAD `64a5a53ceebed43ed79e36a681a27b0d6a0c16aa`. Candidate B packaging smoke PASS is separately reported; renamed `SonicChaos.yyp` / `SonicChaos.exe` and startup guard remain uncommitted on `production/final-packaging-20261102`. No automatic main merge.

Other accepted functionality: Sonic/Tails, five Special Stages, all known-use music via native default, Sound Test, goal km/h, Robotnik opening border, widescreen cards/choice, removed dev shortcuts, recoverable rings, bees and regular enemies in their scoped accepted tests. Avoid another global audit of previously accepted work.

## ACTIVE — final base gate and newly reported spike-sound defect

| Priority | Work | Required result |
| --- | --- | --- |
| **1 — M6-H source preservation** | Accepted production commit `c3e40a7...` published. | COMPLETE; keep baseline unchanged. |
| **2 — `PROD-AUDIO-A7-REPEAT`** | Chief hears spike sound `$A7` repeated when crossing spike X at extreme Y separation. Possible culling-policy relationship unverified. | OPEN; compare authentic sound requester, 2D proximity/trigger and M6-F/G retention without changing packaging. Fix only if evidence supports it, before base freeze. |
| **2 — Chief full base playthrough** | Complete one normal run of the current accepted game and note only genuinely new reproducible defects, if any. | Short consolidated punch list, not dozens of repeated feature acceptance tests. |
| **3 — base freeze** | If no substantial new issue is observed, Chief approves a reproducible private baseline. | Exact source SHA + complete GameMaker project, private dependencies, manifest/SHA-256, independent backup and restore/open proof, source/native policy exceptions documented. |

**Current reported gameplay defect:** `PROD-AUDIO-A7-REPEAT` is OPEN and reproducible by Chief's description, but the exact requester and root cause are **unverified**. Candidate B packaging smoke PASS does not demonstrate a fix. No other previous mandatory defect has been reopened.

## PROD-AUDIO-A7-REPEAT — source cause located, fix NOT implemented (2 Nov)

**Chief symptom:** repeated spike SFX `$A7` on crossing spike world-X even with enormous player/spike Y separation. No playback capture was required; Chief's repeat observation is the acceptance reference. Source examination against the accepted gameplay commit `c3e40a7a3d6c17be3e17d7c1eb729b2a705a3089` identifies a concrete defect:

- `scripts/SCR_chaos_objects/SCR_chaos_objects.gml` lines 69–85 computes **X-only** camera band `[cameraX-64, cameraX+viewWidth+64]` and passes `cp_awake` to `chaos_spike1b_step`. It does not check camera Y for THZ/non-SEZ spike type `$1B`. The SEZ path uses a separate `chaos_sez_mapped_awake` gate; do not accidentally overwrite its special recreation policy.
- `scripts/SCR_chaos_spike1b/SCR_chaos_spike1b.gml` checks `cp_awake` **only before initial activation**. Once `chaosActive` is true, the 102-update animation/state cycle proceeds regardless of later `cp_awake`, and rising state1 at base Y issues `chaos_audio_request($A7,...)` **without any presence, Y, or awake check**. `cp_present` only gates collision and means the player core is usable, **not** spatial proximity.
- Source **both caller and spike script have identical Git blobs** in accepted M6-E, M6-F/R1, M6-G and M6-H: `288d505b7bbeb3db2cc763d589ae418c138c9a9e` and `acc1d3542ffb3b50e9c699bcdb90e82accdd73f6` respectively. **Thus no M6-F/G culling change touched this code**, although the symptom has surfaced now.
- Original-ROM Research `docs/platform-spike-collision-audit.md` section3.1 says ROM type `$1B` skips the *entire callback* with its inactive `+$04` bit6; moving-spike timing is 102 updates. **Exact spawn/sleep/recreation lifetime was explicitly left unresolved** in section7. Therefore Y-aware inactive gating is strongly indicated, but whether callback phase should pause/reinitialize on exit must be proven from original object scheduler before writing a fix. Do not substitute a guessed global `abs(playerY-spikeY)` cutoff or adjust enemy retention.
- Early targeted triage of other environment SFX paths finds potential candidates worth checking (not yet confirmed defects): SEZ crumble `$A3`, spring `$A6`, SEZ booster `$BD`, EEZ type37 `$B1`, MGHZ `$C4`, plus AQZ bubble/water audio. Request-site presence alone is not proof of wrong offscreen playback; review controlling lifecycle and ROM sound requests.

**Required focused task:** inventory **all live environmental (non-mobile-enemy) sound-producing request sites** and their caller wake/sleep rules, distinguishing pure contact-generated sounds from periodic automation; compare original ROM 256 and game 256/348 X/Y boundaries, recently accepted M6-F/G culling untouched. For spike `$1B`, construct controlled natural/camera-Y far, near, re-entry and X-far matrix with start/re-entry phase and audible writes; verify native state 1/2 contact/timing and other environment SFX site guards. Produce root-cause report and ONE narrowly scoped fix candidate only after original callback/lifecycle evidence. No game-wide SFX distance mute, no M6-G enemy policy changes, no broad campaign tests, no generated worktree proliferations. Chief acceptance: one meaningful normal play spot check after source evidence and exact regression checks. **Status: proven source-path omission; complete ROM-equivalent correction still pending.**

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

**M6-H/MGHZ-007 is Chief-accepted, source committed and closed.** Chief's remaining full playthrough continues with a focused `$A7` spike sound investigation as a new issue, not an automatic conclusion that enemy culling is faulty. If no new significant defect, prepare the private freeze checkpoint and get owner approval. Do not reopen accepted music, camera, enemy, ring or original scoring milestones without a fresh reproduction.

After the full playthrough, add only **new owner-confirmed** issues. Do not transplant the old 93-row issue ledger into the current backlog.

# Sonic Chaos — current issue tracker (3 November 2026)

**Live data:** [SonicChaos_CURRENT_Issue_Tracker_20261103.csv](SonicChaos_CURRENT_Issue_Tracker_20261103.csv) — **104 records, 25 columns**: all **93** original AUDIT-0 issues with their **17 source fields retained unchanged**, plus **8 current-review fields**, and **11 new FT-01…FT-11 entries** from Chief's final Sonic/Tails campaigns and the ROM-backed Corrective A work.

**Historical source, frozen and unchanged:** [AUDIT-0 93-row ledger](../audit0/SonicChaos_AUDIT0_Full_Issue_Ledger.csv) and [historical index](../audit0/SonicChaos_AUDIT0_Issue_Index.md). The original **30 October** counts (55 closed, 14 canon/QoL, 7 open, 7 retest, 3 deferred, 2 active audio, 2 source gaps, 2 test exceptions, one infrastructure) **are historical categories, not an assertion of today's open bugs**. Original Excel workbook `SonicChaos_Issue_Ledger_AUDIT0_2026-10-30.xlsx` was preserved in Chief's project Library; a new owner-facing Excel `SonicChaos_Current_Issue_Tracker_20261103.xlsx` was placed alongside it. The new workbook contains Overview, Corrective A, AUDIT0 Reconciled and Watchlist views; the Github CSV provides the full original 17+8 column records.

## Executive verdict

**Both normal full campaigns DONE:** Sonic no additional defects; Tails led to nine owner observations, two original physics-code mismatches and monitor art mismatches. Original GameMaker source candidate `8b3b435` preserved with both 3 Nov ZIPs. **Corrective A** `fc19b3f` is **locally committed, ordinary GameMaker Windows export, private source/receipt and independent H: backup reported PASS**. Four runtime files changed. Automated movement (6,880 AQZ updates both characters/widths), monitor sprite/timing, 37-SFX CPU/PSG/PCM, native startup, 68 Sound Test entries and relevant regressions PASS per Designer report. **Five inherited raw verifier failures still documented.**

**Chief's focused retest PENDING on Corrective A**, three topics: **(1)** AQZ1/2 monitor poof indexed palette, +18 registration, authentic 40-update animation; **(2)** Tails flight terrain-probe cancellation; **(3)** shared AQZ surface `$1E` wall projection both characters. FT-06 underwater feel is tied to the same wall-projection correction; original underwater acceleration/friction/caps were preserved, not tuned. **No full campaign repeat required** until and unless targeted verification reveals a regression. Do not call base frozen yet.

**Closed original behaviour:** (a) AQZ invincibility expiry may replace boss music — ROM verified, Chief says **preserve**; (b) THZ3 spike `$A7` priority48 is often rejected while jump SFX priority56 is active — 19 original-compatible requests / 9 admitted / 10 rejected, Chief recognizes the pattern and explicitly accepts; (c) MGHZ falling hazard `$24` ring-loss despite Spring Shoes and slow horizontal trigger `abs(dx)<=47, abs(vx)<=255` (provisionally closed subject only to actual object ID). No speculative audio priority, boss-music guard, coconut trigger or Tails roll-speed tuning.

## What is still hanging?

| Category | Item | Current disposition |
| --- | --- | --- |
| **Focus acceptance** | FT-05, FT-10, FT-11 / overlapping FT-06 | Three Chief checks on corrected build `fc19b3f`; implementation/source-host tests reported PASS. |
| **Unreproduced owner observation** | FT-07 extreme Tails rolling speed | Tested original ground acceleration, friction, caps, spin dash match. Reopen only on exact failing route. |
| **Optional/deferred** | FT-02 Pause allowed in results | Deliberately retained as debug. Later original-correct scene gating optional. |
| **Optional/original unresolved** | FT-09 Tails vertical flight alongside final Robotnik | No original final camera/input proof. Owner may authorize separate source review. |
| **Optional missing original feature** | FRONTEND-002 attract demos | Parked until after accepted base freeze. |
| **Startup nonblocking** | AUDIO-006 first-start delay and F8 carry detail | One-time 2–3s onset anecdote; F8 raw mismatch with exact audio separately recorded. |
| **Audio evidence limitations** | `$B8` unimplemented/unreached state; **three** original SFX requester triggers unresolved | All 37 SFX **programmes** have parity checks, but don't mistake this for all 109 sites naturally visited. No new sample or decoder justified. |
| **Technical inherited** | TEST-001/002 and five raw verifier failures | Preserved as inherited, reproduced baseline vs Corrective A; don't reclassify as new regressions. |
| **Legacy inactive** | SEZ-002, SS-001, PLAYER-001 and other "believed fixed" entries | Keep historical evidence but not current release blockers without new recreation. |
| **Known widescreen QoL** | THZ-011 goal sign bias | Original adapter accepted; optional later polish. |
| **Historical build environment** | INFRA-001 | Not a broken Windows release. |

**No additional confirmed mandatory gameplay implementation defect is supported by the 3 November results beyond awaiting Chief's targeted Corrective A acceptance.** This is a scoped statement about reported evidence, not a proof that every original script route or future input cannot reveal a bug.

## Clarification — what 37/109/193 SFX coverage actually establishes

**Programme proof ≠ trigger-site proof.** All 37 driver-indexed SFX programmes (`$A0..$C4`) were reported to match original CPU state, ordered PSG and rendered PCM when explicitly requested. This proves no known broken/incomplete *programme* in the native Z80 backend. It does **not** by itself demonstrate that every GameMaker gameplay event invokes the right ID, or that an ID omitted during a playthrough is a bug: the original driver arbitrates and may suppress requests. Example THZ3 `$A7`: 9 admitted and 10 legitimately priority-rejected while jumping, ROM-matched and Chief-approved.

**Verified original retail sites:** the original [AUDIO-0 ROM request ledger](../audio-request-audit.md) has **193 site/context rows** (including static alias/state/condition alternatives), and lists **34 of the 37 SFX IDs with at least one verified ROM call site**. The three without any verified original request site are **`$A8`, `$B2`, `$C1`**. They are *indexed original sound programmes*, not proven missing natural effects or proved unused; do not invent triggers. The newer Designer report refers to **109 original requester contexts**, apparently a filtered/deduplicated implementation inventory. **Do not subtract these counts or claim 109 of 193 failures** without an explicit row-to-row scope/mapping; source documents count different things.

**`$B8` is a different and more consequential hold:** it **has an original mapped request site**, but earlier GML coverage found its state34 requester **inaccessible/unimplemented**. Determine from original retail state transitions/placements whether state34 is naturally reachable. If natural, document the missing GameMaker route and treat as a real correction; if proven unreachable in the actual version, classify as dormant/unused. If reachability cannot be proved either way, keep it a precise research HOLD, not a fabricated PASS.

**Remaining source-level audio closure task (no Chief manual listening):** ask Designer for an *exhaustive 109-context current implementation matrix* (include ID, original object/type/state or scene and ROM address, POC writer+gate, original reachable/unreachable/unknown, test type, accepted vs priority-suppressed, PSG/PCM evidence, gaps and exact commit). Reconcile that matrix's denominator to the original 193-row ledger by documenting alias/dedup and which rows remain unaccounted for. Independently adjudicate `$B8` and `$A8/$B2/$C1`. Only fix a demonstrated **naturally reachable** missing implementation route; **do not create another driver, invent effects, ask Chief to test 37 SFX, or modify frozen Corrective A ZIP while Chief verifies AQZ**. If no missing reachable writer exists, close the SFX milestone as *all proven retail pathways implemented, with explicitly listed unreachable/unknown contexts*, not as an unqualified 100%-natural-play claim.

## Clarification — AQZ monitor correction scope

Corrective A's reported failure is specifically AQZ monitor destruction: old code used a shared RGB poof instead of the **already existing indexed AQZ poof**, lost the converted monitor's `+18` draw registration, and removed effect at 24 updates instead of the ROM **40-update** sequence with early blank frames. Agent reports **only four runtime files modified** and previous package independently hash-preserved; source-host AQZ sprite/draw/lifetime tests PASS. **However the exact four-file private diff was not supplied to this chat.** The evidence is strong for the AQZ symptom and targeted regression but **does not by itself prove that the draw path is unreachable outside AQZ**, since shared monitors/effects exist. Before marking zone isolation independently verified, request Designer's exact changed-function/zone guard and run an automated original monitor destruction smoke in THZ, GPZ, SEZ, MGHZ and EEZ plus AQZ1/2. No need for Chief to test other monitors without an actual failure. Avoid global palette rewrite.

## Source boundaries and update discipline

- **Owner fact:** both whole campaigns completed on 3 Nov baseline; Chief personally adjudicated original audio quirks.
- **Agent evidence:** ROM differential and automated package claims, reported by Designer. Raw private source archives and E: `REPORT.md` / `AQZ-MUSIC.md` / receipt are **not published here**; validate them locally if independent review is required.
- **Not proven:** every natural audio requester; specific Tails extreme-roll incident; Robotnik post-boss flight gating; a complete second emerald run (Sonic's later run was partial).
- **Don't rewrite AUDIT-0:** that file remains AM-san's immutable historical reconciliation. Update the current tracker and a future brief status note when Chief completes focused checks.

Last edited: 2026-11-03. Manager-san #9.

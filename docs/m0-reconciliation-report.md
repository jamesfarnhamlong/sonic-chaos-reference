# M0 — history reconciliation

22 October 2026. Research-only checkpoint, starting at `0ef9f5ea6f7f1a42f7b55557572529f4715dcb7e` on `research/m0-m1-roadmap-tails-frontend`. The Manager's present assignment authorises this research and its commit/push; older standby instructions do not cancel it. No implementation authority follows.

## Access and evidence boundary

This session actually has the Windows workspace mounted. Read: live root `AGENTS.md`, local `docs/AGENTS_ARCHIVE_20261020.md`, relevant sections of local ROADMAP/FULLGAME_0/CROSSZONE_0/SHARED_MECHANICS/ZONE_IMPLEMENTATION/DEFERRED_ISSUES references, accepted POC worktree at exact `7476affc6ed7626dabf69b446cdab0c9c3d7492e`, its Q1–Q3 predecessor closures, Research reports/caches and planning trio. Both Q3 root-amendment candidates were read without installing them. No repo-specific AGENTS exists in this Research checkout. Root AGENTS was read with SHA-256 `e124ad0709a8d54315b961da1ffeeaa11dc99c1899492673f7352fcf248d8fff9`; this differs from the two older recorded hashes. Its heading itself says candidate/not installed. Record the actual file read, without asserting a successful management installation or reconciling its authorship. Root remains untouched.

Read the Q3 FINAL private inventory JSON locally: it names the expected commit/parent, 7,101 files, one project, 1,100 resources, 5,889 runtime files, 4,924 sprite files, archive hash `b409be469f27e8b6270c510281dc601f04b471c8d3432f47ebe639e10e43c859`, and restoration 181 then 0. These are receipt assertions, **not a new ZIP CRC/hash/payload verification**. No ZIP was extracted. Historical private inventories were not exhaustively opened; their gaps remain external reconciliation dependencies if an omitted release affects a future decision. Do not ask Chief to resupply files already accessible here. No confidential local file contents or inventory payload are copied into Git.

New original-ROM work is static decoding only, hash-gated against `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. No new emulation, human listening, Windows F5, compilation or full-campaign execution occurred. Existing emulator measurements below remain attributed to their original reports.

## G0–G10 reconciliation

Historical category meanings come from the archived AGENTS §“G0 closed” and its reference map. They are not replaced by M0–M8.

| Historical group | Current disposition / authoritative evidence | Next prerequisite and proposed gate |
|---|---|---|
| G0 campaign contract / static reconciliation | Accepted Research `docs/g0-campaign-contract.md`, `data/g0/`; historical G0-D static 76-row audit is planning, not gameplay acceptance. | Reuse contracts; no new runtime package. |
| G1 campaign plumbing | G1-A reset, B 18-act metadata/anchors, C results/title flow, D sign rewards, E boss rollover, F SS progression, G endings have scoped accepted closures in POC `docs/g1*-closure.md` (A/B acceptance also in archive). Q1 adds natural campaign PASS. | Preserve; unobserved per-act normal results routes are coverage gaps. |
| G2 lives/death/Continue/score | G2-A lives; G2-B Continue owner; G2-C/D TIME OVER/Continue/Game Over four Windows PASS; G2-E scoring/results and Continue three Windows PASS. Tails numerical paths remain automated-only. | Reuse owners, add Tails route coverage in M2. Original save/password absent: G2-F no work. |
| G3 movement/camera | C1-I and V1/T1 accepted look, idle, Peel-Out, twist and shared bounds. P4/C3-BX1/Q3 add scoped boss policies. | Remaining symptoms need a new reproduction; no blanket camera rewrite. M6 if selected. |
| G4 sound | AUDIO-0 catalogue, AUDIO-1 feasibility, AUDIO-1B renders and AUDIO-A0 accepted five-preview Sound Test. **Live canonical soundtrack remains incomplete.** | Renderer/clock/loop/arbitration decisions → M4 pilot → M5 library. Audible Windows acceptance required. |
| G5 presentation | Authentic ordinary/SS results, title cards, six-zone art work, U5-A poses, OPENING-1 cinematic, Q2 wide cards, Q3 fragments/seam accepted in respective scopes. | Public title/character choice and demos remain gaps: M3; named remaining visual defects M6. |
| G6 Tails | Campaign/reward/ending source contracts, 11 authenticated opening/Continue resources exist. Public playable route not accepted. | M1 evidence → one substantial M2 candidate, character-specific source checks and natural Tails ending gate. |
| G7 PC saves/options | Optional future enhancement; inherited slot UI is not original saving. | M7 after original features, separate requirements/Windows persistence checks. |
| G8–G9 cross-zone/boss/Original Mode RC | Many scoped boss/zone milestones and Q1 18-act Sonic PASS; **not universal parity or production RC**. | Tails/audio/frontend plus remaining impact-ranked fidelity, then release gate. |
| G10 enhanced modes | Parked; ports/decomp/slowdown are separate. | Explicit later assignment. |

## Feature and supersession map

All POC document references in this section mean the file at accepted POC `7476affc`, unless a distinct SHA is given.

| Feature / older statement | Reconciled current status | Authority / prerequisite / group / Windows gate |
|---|---|---|
| All 18 Sonic acts and ending return | Chief-reported continuous New Game, all Emeralds, good ending/credits/title PASS at 348×196. Partial Sonic ending separately accepted. | Live root Q1 report; POC G1-G and Q3 closure preserve scope. No repeat campaign commissioned here. |
| SS1–SS5 | Historically implemented/accepted; natural full-Emerald campaign adds integration evidence. Dedicated timeout/return and alternate paths are not all independently covered. | Root Q1 coverage distinction; Research Q1 flow map; preserve in M2/M4 regressions. |
| Q1 per-act coverage | 18 visits PASS; ten separately observed normal transitions, eight distinct normal sign/results sequences NOT TESTED. | Root Q1 coverage summary. Do not convert a Special Stage detour into a normal-results observation. |
| Opening missing in U5-A | Superseded: OPENING-1 A four passes plus B machine-departure correction. Silent authentic cinematic preserved. | `docs/opening1-closure.md`; no remake. Audio belongs M4. |
| Continue/Game Over missing in old U4-B POC comparison | Superseded by G2-C/D accepted four scenarios. | `docs/g2cd-closure.md`; TIME OVER at 10:00, fresh-edge Continue, same-act reload, expiry/no-continue title. Tails native gate remains M2. |
| Tails reward rules missing | Partly superseded: G0 research and G2-E implementation already cover numerical character differences. | Research G0 + POC `docs/g2e-closure.md`; don't duplicate score/lives owners. |
| Character select absent / assumed title toggle | **ROM has a separate character-choice screen.** Current public POC New Game forces Sonic. | `$3065/$3522/$356A`, M1 census; M3 after M2, no public dead Tails option. |
| Current title | Inherited `SPR_title`, `objects/OBJ_menu_title/Draw_0.gml`; menu action `OBJ_menu_title_options/Alarm_1.gml` calls Sonic-only `chaos_run_new_game`. | Current POC source, not authentic SMS title acceptance. M3 new startup/selection/return Windows gate. |
| Level Select / Sound Test | Existing developer fixtures; not missing frontend features or public SMS selection. | `SCR_chaos_debug_select`, `docs/g2cd-debug-controls.md`, AUDIO-A0 closure. Preserve until separately approved production gate. |
| AQZ reverse dash / wide title-results cards | CLOSED-348 by Q2-P1 4/4, not a general water-physics rewrite. | `docs/q2p1-closure.md`; Q2 Research `8eacc666`. Preserve in M2. |
| THZ wide patrol / SS4 clock seam | CLOSED-348 by Q3-B 2/2; rejected A left coverage remains historical. | `docs/q3p1-closure.md`, boss policy. Do not reopen as unfixed. |
| SEZ/AQZ/SS4 fragments | CLOSED-348 Q3-A retained four-category acceptance. THZ2 fragments had earlier VISUAL-P2 scope. | Q3 and VISUAL-P2 closures; other owners still unresolved, M6 only after scheduler/art evidence. |
| Imported artwork | Existing authentic Sonic frames, loop/twist, scenery/boss/SS, results/death cards, opening and fragments are retained. Census names the 11 authentic Tails opening/Continue sprites. | Respective importers/closures; resource existence alone proves neither universal reachability nor authenticity. |
| Inherited placeholders | 29 other Tails-named resources including super/swim variants remain unverified inheritance; `SPR_title` is inherited. Registered Sega splash is unreachable and not an original-ROM feature. | Census + current sprite-owner source, OPENING closure. Replace only documented owners; do not reopen inherited-asset publication audit. |
| Audio previews | Five private accepted evaluation WAVs; 21 inherited sounds preserved, not certified original replacements. | AUDIO-A0 closure/provenance. M4 needs full pilot assets/loops; M5 full coverage. |

## Bugs retained without speculative closure

The planning Fidelity Register retains SS3 monitor embed, impact/rebound, historical visible oscillation, slope sticking, diagonal spike observations, natural mapped `$26` spring coverage, width-phase lifecycle uncertainty, MGHZ3 reveal, sign centering, unidentified “SLZ1” priority and “Boss1”, state20 timing lag, loop anchor, other fragment owners and continues observations. C2-R1/R2/R3 and Q2-R1 reports distinguish source findings from unresolved human symptoms. The canonical 1/16-pixel no-input cycle does not explain the larger oscillation.

Reading the older deferred reference additionally preserves the AQZ puff/palette report, SEZ Spring Shoes contact/lock observations, downhill/fall/isometric presentation, enemy lifecycle visibility, hurt-landing extra VY write, narrow terrain-ring feel and partial dynamic-pool coverage. These now have explicit register rows rather than silently disappearing. Current source still has the hurt landing write; no new causal/runtime proof is claimed. Canonical state14 no steering, monitor one-tick push/vertical pop, stationary lost-ring recollection, bee keepalive and water movement tables are constraints, not automatic bugs.

Historic ROADMAP FG-01/02/03/04/05 are superseded in parts:1-UP owner by G2-A; campaign by G1/Q1; look/Peel-Out by C1-I; intro/cards by OPENING/G1-C, while actual public title remains missing. AUD-01 is expanded by A0 but not closed as gameplay audio. FG-06 Tails remains a feature gap, FG-07 PC save/options optional. CROSSZONE XZ-022A foreground was closed by FG1/INTEGRATION-1 (six combined Windows categories, including one SS5 timeout/scoring return to GPZ2 from GPZ1); XZ-022B withdrawn. That exact SS5 fixture acceptance does not imply every dedicated timeout/origin path. Older XZ family-selector suspicions must be checked at current source before implementation, not blanket-reclassified as current bugs.

Q3 raw gates remain 16 PASS / 2 FAIL per side: SS5 256 camera-X ≤2 px and obsolete THZ3 cap assertion. Historical GPZ sprite mismatch, MGHZ timeout and AQZ source equality exceptions are not rerun or relabelled PASS. Tails/frontend work must compare affected contracts against Q3, not retroactively repair every frozen snapshot test.

## Decision

M0 reconciliation is complete for the accessible scope, with historical archive completeness unresolved. M1 provides static contracts and explicit pre-implementation evidence gates. Recommended order: **M2 authentic Tails**, then **M3 frontend**, then **M4 dispatcher pilot / M5 full library**. Asset extraction/character callbacks must meet the M1 dependency matrix before Designer's substantial package. Manager review is the next action; no implementation, merge, main promotion, root installation or release compilation is authorised.

## Focused verification

Nine cached contract/planning checks PASS: transfer/geometry/state-frame closure, wrong-origin and missing-frame negative controls, flight/Continue records, original choice-button/title-cue instructions, resource/palette census, attract table order/region, wrong-ROM hash rejection before file access, and deliverable/payload boundary. Deterministic `m1_census --check` compares the complete census against the private-ROM static decode and exact Q3 source. These checks validate consistency and pinned source evidence, not full behavioural emulation or Windows play. No broad historical gate was rerun.

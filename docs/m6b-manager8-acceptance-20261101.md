# M6-B — Manager-san #8 review and acceptance (1 November 2026)

## Verdict

**ACCEPTED — NO PRODUCTION CORRECTION JUSTIFIED** for the bounded player/contact fidelity audit. This does **not** declare all historical human observations disproven or closed. No Chief F5 candidate or retests required from this no-code exercise.

Accepted playable GameMaker baseline remains `jamesfarnhamlong/SonicChaos_POC@91fd74b56296bb9182768c3a9db78a186fa78f9e` (M5-G2). Evidence branch `poc/m6b-contact-fidelity@05bdbffa7c966b15a5e67fabf65031042a6d4b7d` independently GitHub-verified as **one commit ahead/zero behind G2**, remote tip same SHA. **37 changed files**, all documentation/verification artifacts, with a small set of pre-existing `verification/verify_*.js` fixtures repaired for later accepted APIs; **no production GameMaker `.gml`, `.yy`, `.yyp`, music or resource source changed**. Designer reports clean local worktree; Manager did not verify local filesystem. Do not merge main or reset G2 baseline.

Source: [complete M6-B report in POC](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/05bdbffa7c966b15a5e67fabf65031042a6d4b7d/docs/m6b-contact-fidelity.md), [commit](https://github.com/jamesfarnhamlong/SonicChaos_POC/commit/05bdbffa7c966b15a5e67fabf65031042a6d4b7d).

## Focused evidence

- **1,452 fresh controlled executions of the original SMS Z80 monitor callback $A16C**, matching G2 for **2,904 paired comparisons** at widths256 and348. Original routine execution is distinct from naturally reaching those cases during gameplay or running native GameMaker. Original ROM SHA256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`; no private ROM published.
- Spring Shoes/SEZ monitor geometry: attack posture, downward `vy` and side/top vs bottom interactions govern break/bump; anchor separation18 inclusive and19 rejects. No general hitbox widening or forced attack state justified.
- SEZ-001 terrain lock and SEZ-002 same-box historical event remain **not reproduced in bounded seeded routes**, not universally disproved; exact original user route missing.
- Historical MGHZ spring/slope/Badnik facing and collision issues: accepted C2-R2 replay has **430,080 comparisons/96 sequences**, position/velocity/state/contact match; **2,106 raw player_flags +540 raw drawFacing differences** retained because historical oracle predates accepted Q2-P1 facing ownership, not silently green. Visible oscillation route not reconstructed.
- Diagonal static spikes and moving-spike activation: focused original contracts and G2 checks acceptable, but `PLAYER-003` exact diagonal entry pose and `PLAYER-004` native hardware-vs-wide lifecycle route remain unproven.
- SS3 top-left invincibility monitor: 28 bounded seeded approaches, six monitors reached per posture/width, old persistent embed not reproduced; the exact historical player input/monitor route remains unknown.
- Tails Spring Shoes: existing scoped 670 assertions PASS but original Tails-specific observed case/provenance gap still OPEN.

**Verification**: reported **15 PASS / 2 inherited raw FAIL**, zero newly introduced production failures. Inherited `verify_ss5_play.js` width256 camera max2px discrepancy and obsolete `verify_thz3_boss_clear.js` camera cap4 vs accepted7 retained as failures. Initial broader tests with stale fixtures/legacy audio assertions were not misrepresented; four narrow fixture updates are documented and tests pass in scoped runs. All **1,313 GameMaker resources** and their tracked source identities preserved; **no native GameMaker run and no private asset ZIP integrity claim**.

## Binding status and roadmap

M6-B **closed as source-backed no-code review**. The source-only evidence does not change the historical original AUDIT-0 or AUDIT-1 verdict matrix retroactively. Retain `SEZ-001`, `SEZ-002`, `MGHZ-006`, `PLAYER-001..004`, `SS-001`, `TAILS-006` as route-limited/historical observation until new precisely reproducible evidence exists. **Do not repeat another broad physics investigation** absent that evidence; no player control, monitor reach, slope/contact, spike wake-band or SS-specific pushes are approved. All accepted M5-G2 music and native driver unchanged.

MGHZ3 `MGHZ-007` remains **playable but visually imperfect / owner-parked for final widescreen polish**, not declared perfect. One-time startup delay likewise parked as unmeasured first-boot presentation issue.

**Next authorized work: M6-C bounded presentation sweep (OPENING-001, PRES-002, EARLY-011)**, source/previous evidence first; avoid agent-native Runner error623 loop, make only source-backed and actually visible fixes. See [M6-C directive](m6c-presentation-sweep-manager8-20261101.md).

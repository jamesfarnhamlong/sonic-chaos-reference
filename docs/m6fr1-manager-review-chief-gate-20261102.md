# M6-F-R1 Manager review — Chief THZ2 acceptance gate
**2 November 2026 · Manager-san #8**

## Verdict: MANAGER GO; Chief native F5 PENDING

GitHub-reviewed branch `jamesfarnhamlong/SonicChaos_POC:poc/m6f-r1-bee-vertical-retention@636ed72be111bc3de4c297e5768c40c8f38a54e6` is **exactly one commit ahead / zero behind** M6-F candidate `70cac5dea79e5e81fb88513effec367cb1af4d0c`; pushed remote branch SHA matched exactly. **Only production changed file** is `scripts/SCR_chaos_placement/SCR_chaos_placement.gml` (19 changed lines). Other files are reports, controlled verification and private-package instructions. All1,314 existing resources /38 IncludedFiles and every other runtime asset/source are Designer-reported unchanged; private ZIP/checksum receipt on Chief's E: drive cannot be independently byte-inspected here. No POC main merge.

**Chief F5 prior status:** M6-F **GPZ3 ring recovery PASS** including high-Y offscreen descent; **THZ2 flying enemy persistence FAIL**. This R1 patch retains the Chief-passed M6-F ring code and is not a new fully accepted game until Chief checks bee. Fully accepted prior baseline remains M6-E `a4c26e13bc323a9f736c613c279b447dd6aedef5`.

### Precise diagnosis and correction

- Earlier THZ2 column group is bee **placement31**, original ROM record `$7089A`, X1152/Y640, nearby spring row Y896. Controlled local play-style replay found that M6-F deletes the active bee at **update185** (cameraY772, beeY640, state3), releases occupancy and recreates it at origin by **update197**. At update299 the restarted M6-F bee is X1119.5/state2/oscillator80/age102; R1 preserves the original encounter at X732/state3/oscillator129/age299. An independent follow-from-below fixture found a state2 deletion at update48. **These are controlled-source ticks, not Chief's native play timings.**
- Original type`$27` post-proximity state2/3 has a bit1 keep-alive for generic offscreen handling; bit6 may hide it while state2/3 continues oscillator/motion. Canonical state3 retire condition is **playerX-to-beeX >=384**, not vertical camera distance. M6-F incorrectly reintroduced **Y-based destruction** at ±128px camera envelope.
- R1 on 348-wide only gives **already-awake, triggered type`$27/$2C`** a typed lifetime override: cameraY beyond previous active envelope returns **sleep cell2** (keep existing identity/phase/occupancy), not deletion cell3. The state2/3 callbacks still execute; visibility hides it. Horizontal departure is finite and uses inherited `cameraX-512 .. cameraX+viewW+512` boundary. Other regular types (including ground`$25`), untriggered type`$27`, bosses/projectiles and all native256 logic remain with previous rules. Original post-trigger vertical keep-alive is canonical; wider horizontal 512 continuation is labelled **PC widescreen adaptation**, not original ROM parity.
- **Source diff inspected.** New helper `chaos_flying_wide_x_departed`, type guard `chaosEnemyType==$27||$2C`, explicit state>=2 and width>256; no modification to `SCR_chaos_lost_ring.gml`, collision, graphics, audio, camera, level or UI. The reported bundled private archive preserved every other runtime byte.

### Verification reviewed; honest limits

- `verification/m6fr1/gate.json` explicitly reports **9 PASS / 1 raw FAIL**, with no native GameMaker run.
- Focused **197 assertions, 16 paired THZ2 cases** (two characters, 256/348 widths, two column groups, two scenarios); **40,332 original-Z80 assertions**. The 256 controls show no divergence from inherited native behaviour, and 348 scenarios show precisely the corrected divergence from the M6-F parent. Also tests THZ1, GPZ1/2, EEZ1/2 flying aliases and original sleep/visibility, finite X retirement, defeat/occupancy, numeric type isolation.
- M6-F 15,750 focused checks plus lost-ring verifier **879,757 assertions** reran internally once and PASS. Adjacent placement/GPZ/M6-D/M6-E/M4 regressions PASS. `verify_m6d` first passed 1560 assertions but failed writing logs to absent build/m6d; directory created, targeted rerun PASS; original failure retained as environmental harness artifact, not game defect.
- **One inherited FAIL**: unmodified raw `verify_viewport_adapter` asserts type$27 always removes at PLAYER_DIST384 in all widths. This conflicts with approved 348-widescreen horizontal QoL and was already FAIL in M6-F. R1 separately verifies native256 384 and intentional 348 horizontal policy. Do not silently relabel raw FAIL PASS.
- Evidence is controlled source-host+Z80 emulated ROM replay, not full natural ROM player input and not GameMaker native F5. The manually supplied local Markdown matches the GitHub source report; no local ZIP bytes available for Manager authentication.

### ONE Chief GameMaker F5 check

Use **private full source ZIP** `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_M6FR1_20261102_A_PRIVATE.zip` extracted to a fresh folder; open `SonicChaos_A4B_EXPERIMENTAL.yyp`, standard 348×196 F5.

1. THZ2 **EARLIER** bee group above two columns: trigger the bee, fall between the columns, spring back up. It should **continue from its evolved position/state**, not recreate at the origin. Repeat normal movement if needed to cross the original reset point.
2. Follow the same bee to the right while below, let it depart from view, then return; verify **same bee/patrol progression**, not resetting. A **very long horizontal exit** may legitimately retire it at the documented finite boundary.

Report **A PASS/FAIL, B PASS/FAIL**, and only if failure provide exact visible symptom. **Do not repeat GPZ3 rings**, soundtrack, frontend, boss/acts or full game. No interim new build, no Runner error623 investigation. **If both PASS**, record complete M6-F-R1 Chief acceptance and promote integrated commit `636ed72be111bc3de4c297e5768c40c8f38a54e6` as the accepted production baseline. Then Chief's planned **full base-game playthrough before enhancements** can begin. If either fails, retain ring acceptance, investigate the single THZ2 occurrence and correct in one further limited package. No automatic main merge or private asset publication.

# Q1 — Source-backed campaign flow and limits

Planning review only, 22 October 2026. POC `4eb684911c5785667181b9d3f940b1dc820e66d1`, Research parent `715ab1b1aa22f723690d042fae2c2117e9a16b6f`. Isolated branch `research/q1-widescreen-campaign-qa-plan`. No gameplay, ROM, emulator, GameMaker or Windows execution. No new POC implementation discrepancy requiring a stop was established; the constraints below are source/documented limitations, not newly proven runtime failures.

## Campaign graph

The single `chaos_acts()` table contains 18 rooms in this order:

Turquoise Hill 1 →2 →3 → Gigalopolis 1 →2 →3 → Sleeping Egg 1 →2 →3 → Mecha Green Hill 1 →2 →3 → Aqua Planet 1 →2 →3 → Electric Egg 1 →2 →3.

Act 1/2 have goal-sign exits. Contact stops the clock and begins sign camera pan; it does **not** immediately advance. The sign child eventually requests player run-off state $20. The player raises `act_clear`; controls call `chaos_act_complete()`. Ordinary results capture rings and the time/ring bonus, display/tally, run fades and the next-act title, then load `next_index=index+1` and restore gameplay. Space accelerates tally and advances a title hold; it is not an encounter skip. Actual Windows completion of each edge is Q1 NOT TESTED.

For Act 3 in the first five zones, each boss requests the same run-off state through `chaos_goal_request_state20`. Completion enters shared results with the zone's fixed boss bonus, then loads the next zone's Act 1. The order is THZ→GPZ→SEZ→MGHZ→AQZ→EEZ. A boss defeat alone is insufficient test evidence: observe camera release, walk-off, results/title, next room and regained control. Do not require precise score measurements or per-frame timing in this human smoke.

Electric Egg 3 is terminal. Its three encounters and camera ownership changes stay in one act. The terminal scheduler waits, builds `chaosEezFinalHandoff`, and the zone End Step consumes it through `chaos_ending_handoff()`. It skips ordinary results and state $20 run-off. Sonic with all six low completion bits gets the full ending; otherwise the partial ending. Partial shows TRY AGAIN; full includes credits and END.; both return to title. The five-bit selector preset is not enough by itself: the final EEZ Emerald contact adds bit $20 before handoff.

The source graph establishes implemented destinations, not that every path is playable in one uninterrupted Windows run. Required `EEZ3-FULLCHAIN-F5` remains OPEN regardless of historical ending tests or source fixtures.

## Entry, shortcuts and resumability

Title's New Game alarm calls `chaos_run_new_game()`: Sonic, three lives, zero continues/Emeralds/score/rings, progression1, cleared Special Stage/ending contexts, natural-run true and developer-session false, then Turquoise Hill 1. No character-select step or legacy save-card step is needed. Title options and pause menus are the current navigation; old handovers' F10/disabled-SS instructions are historical.

Level Select exposes all 18 ordinary acts and five Special Stages. A launch resets local run/score/lives and applies the selected developer Emerald mask. Normal results still advance to the next ordinary act, while the developer flag suppresses normal saved progression. Therefore a Level Select Act 3→next-zone test is valid **transition** evidence, but never evidence of title/New Game continuity.

Natural progression is RAM-only. `SCR_save_game()` returns early for natural or developer sessions; title loading does not provide a natural campaign restore command. A paused live process can be resumed. Closing F5/reloading, title/New Game and shortcuts cannot be spliced into one uninterrupted run. Death/continue handling can reload the current act; record those events without claiming deathless completion. Game over→title ends that attempt. Player inability to complete a difficult route is a testing limitation, not proof of a code defect.

WIDE explicitly chooses 348×196. AUTO derives a size from the monitor, so do not infer the target from a widescreen-looking window. Window scaling does not change the logical view dimensions. No 256×192 Windows gate belongs to Q1.

## Special Stage access and return

The ordinary ring counter handles 100-ring wraps, including eligible monitor additions, awards a life and can schedule the entry fade. Entry is Sonic-only, ordinary-zone-only and refused once all five Special Stage completion bits are set. The first missing sequential bit selects SS1–5. Five stages are implemented; this is not an invented sixth stage.

For an ordinary Act 1/2 origin, the recorded return context names the **next act's room**. Success awards the relevant Emerald bit/continue and runs the stage result path; failure has its own result path; both use that context. It is not a return to the ring pickup position. A natural detour can bypass the ordinary sign/results edge, so record exit kind separately in the 18-act matrix.

Act 3 origins have no valid `next_room`. Existing source explicitly falls back from an invalid context to the THZ1→THZ2 developer fixture and records a return fault. Natural reachability of such an Act 3 entry is unverified; do not force one as normal-campaign acceptance. If it occurs during the live run, record the origin/return and stop the dependent continuation for review. This inherited constraint is not newly diagnosed as a reachable bug here.

Direct developer SS launches use a valid retained ordinary origin if present, otherwise the explicit THZ1→THZ2 fixture. Title reload alone does not establish that an earlier origin was cleared. The checklist therefore establishes an explicit Turquoise Hill 1 origin before each optional SS test. Preset stage-number-minus-one completion bits permit independent reward tests; those remain fixtures, not five naturally earned Emeralds.

## Historical acceptance versus Q1

Read accepted POC `docs/c2e1-closure.md`, `docs/c3bx1-closure.md`, and the G1-C/E/F/G closures. G1-C accepted sampled sign/results flow; G1-E sampled zone rollovers; G1-F sampled natural detours; G1-G accepted two developer-launched ending routes. None proves uninterrupted 18-act coverage, and their historical width/fixture qualifications remain intact. C2-E1 Windows scope is 348×196 only. Later P4/C3-BX1 accepted camera/exit work supersedes relevant old 'current' findings; do not reopen every historical transition observation as a fresh blocker.

Q1 starts with **zero Windows PASS rows**. Open issue priority and status live in `data/q1/coverage-register.json`. Existing MGHZ entrance presentation, historical visible oscillation/sticking/diagonal spike reports, state $20 lag and C2-R3 spike activation uncertainty are carried without implementation authority or automatic failure of unrelated checks. Required EEZ full-chain evidence has priority 0.

## Limits and practical blockers

No proven source-level blocker to the ordinary next-room graph was found. Runtime ability to finish the entire campaign is unverified. Missing accepted project/private assets or a failure to enter the target view blocks setup; this task neither builds nor restores a package. A runtime failure blocks only dependent later tests; keep earlier observations and independent smoke results. Optional Special Stage/ending work is separate from ordinary campaign acceptance. Audio completeness, Tails, diagnostic removal and production release readiness are outside this plan.

The machine-readable register, editable CSV and Markdown matrix keep individual act, normal transition and continuous-visit results separate. Every result includes a run/evidence field. A continuous visit is not a full-route parity claim. There is no new full regression sweep: this assignment validates the plan against source metadata and status consistency only.

## Exact accepted-source references

The links below pin the POC SHA above. Their lines were resolved mechanically from the accepted files; file hashes are retained in the coverage register.

| Reference | Accepted source |
|---|---|
| act_table | [scripts/SCR_chaos_level/SCR_chaos_level.gml:415](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_level/SCR_chaos_level.gml#L415) |
| new_game | [scripts/SCR_chaos_level/SCR_chaos_level.gml:568](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_level/SCR_chaos_level.gml#L568) |
| goal | [scripts/SCR_chaos_level/SCR_chaos_level.gml:498](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_level/SCR_chaos_level.gml#L498) |
| act_complete | [scripts/SCR_chaos_level/SCR_chaos_level.gml:476](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_level/SCR_chaos_level.gml#L476) |
| title_new | [objects/OBJ_menu_title_options/Alarm_1.gml:2](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/objects/OBJ_menu_title_options/Alarm_1.gml#L2) |
| title_select | [objects/OBJ_menu_title_options/Alarm_2.gml:2](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/objects/OBJ_menu_title_options/Alarm_2.gml#L2) |
| wide | [scripts/SCR_screen/SCR_screen.gml:61](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_screen/SCR_screen.gml#L61) |
| options | [objects/OBJ_menu_options/Step_0.gml:64](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/objects/OBJ_menu_options/Step_0.gml#L64) |
| pause | [objects/OBJ_virtual_controller/Step_0.gml:74](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/objects/OBJ_virtual_controller/Step_0.gml#L74) |
| pause_menu | [objects/OBJ_pause/Step_0.gml:52](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/objects/OBJ_pause/Step_0.gml#L52) |
| select | [scripts/SCR_chaos_debug_select/SCR_chaos_debug_select.gml:61](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_debug_select/SCR_chaos_debug_select.gml#L61) |
| select_entries | [scripts/SCR_chaos_debug_select/SCR_chaos_debug_select.gml:2](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_debug_select/SCR_chaos_debug_select.gml#L2) |
| emerald_preset | [scripts/SCR_chaos_debug_select/SCR_chaos_debug_select.gml:89](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_debug_select/SCR_chaos_debug_select.gml#L89) |
| results_begin | [scripts/SCR_chaos_results/SCR_chaos_results.gml:43](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_results/SCR_chaos_results.gml#L43) |
| results_next | [scripts/SCR_chaos_results/SCR_chaos_results.gml:207](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_results/SCR_chaos_results.gml#L207) |
| goal_child | [objects/OBJ_chaos_object_19/Step_0.gml:10](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/objects/OBJ_chaos_object_19/Step_0.gml#L10) |
| thz_boss | [scripts/SCR_chaos_boss/SCR_chaos_boss.gml:125](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_boss/SCR_chaos_boss.gml#L125) |
| gpz_boss | [scripts/SCR_chaos_gpz_boss/SCR_chaos_gpz_boss.gml:188](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_gpz_boss/SCR_chaos_gpz_boss.gml#L188) |
| sez_boss | [scripts/SCR_chaos_sez_boss/SCR_chaos_sez_boss.gml:221](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_sez_boss/SCR_chaos_sez_boss.gml#L221) |
| mghz_boss | [scripts/SCR_chaos_mghz_boss/SCR_chaos_mghz_boss.gml:250](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_mghz_boss/SCR_chaos_mghz_boss.gml#L250) |
| aqz_boss | [scripts/SCR_chaos_aqz_boss/SCR_chaos_aqz_boss.gml:173](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_aqz_boss/SCR_chaos_aqz_boss.gml#L173) |
| eez_terminal | [scripts/SCR_chaos_eez_boss/SCR_chaos_eez_boss.gml:403](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_eez_boss/SCR_chaos_eez_boss.gml#L403) |
| eez_final_emerald | [scripts/SCR_chaos_eez_boss/SCR_chaos_eez_boss.gml:258](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_eez_boss/SCR_chaos_eez_boss.gml#L258) |
| ending | [scripts/SCR_chaos_ending/SCR_chaos_ending.gml:3](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_ending/SCR_chaos_ending.gml#L3) |
| ending_return | [scripts/SCR_chaos_ending/SCR_chaos_ending.gml:58](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_ending/SCR_chaos_ending.gml#L58) |
| ending_consumer | [objects/OBJ_chaos_zone/Step_2.gml:7](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/objects/OBJ_chaos_zone/Step_2.gml#L7) |
| ss_entry | [scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml:305](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml#L305) |
| ss_context | [scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml:272](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml#L272) |
| ss_return | [scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml:341](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml#L341) |
| ss_reward | [scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml:125](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml#L125) |
| save_guard | [scripts/SCR_save_game/SCR_save_game.gml:3](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_save_game/SCR_save_game.gml#L3) |
| death | [scripts/SCR_chaos_death/SCR_chaos_death.gml:36](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_death/SCR_chaos_death.gml#L36) |

Historical acceptance sources (same POC commit): [c2e1-closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/docs/c2e1-closure.md), [c3bx1-closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/docs/c3bx1-closure.md), [g1c-closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/docs/g1c-closure.md), [g1e-closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/docs/g1e-closure.md), [g1f-closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/docs/g1f-closure.md), [g1g-closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/docs/g1g-closure.md).


Plan reproduction (metadata only): `node tools/q1_plan_register.js ../SonicChaos_POC_c2e1`; checks: `python -m unittest discover -s tests -p test_q1_plan.py` (seven plan-consistency tests). The generator initialises blank results: do not run it over completed QA records. Preserve filled CSV/register copies and evidence with their run IDs. These checks validate planning metadata, not gameplay. No historical suite was rerun.

EEZ encounter camera ownership/follow reference: [SCR_chaos_eez_boss.gml:317](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/4eb684911c5785667181b9d3f940b1dc820e66d1/scripts/SCR_chaos_eez_boss/SCR_chaos_eez_boss.gml#L317). The priority chain check follows the accepted canonical-jump contract carried in C3-BX1 closure, not a requirement to smooth every abrupt handoff. The register includes this additional source hash/anchor.

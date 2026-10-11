# Special Stages follow-up — terminology, SS3 route input, Act 3 quirk and Entry Fail

Branch `research/special-stages-followup`, starting from Research `main` `ce431507bd0a49437e9559326dbac3ca9c0b0206`. This is a reconciliation, not a new audit: canonical Special Stage behavior (type `$31`, parameters, collision, success/failure logic) is **unchanged**. Machine package: `data/rom-cache/special-stages/followup.json`, tool `tools/ss_followup.py`, test `tests/test_ss_followup.py`.

## Evidence ledger (kept separate)

| Claim | Class | Source |
|---|---|---|
| Type `$31` sets `D2CC \|= parameter`, +1 continue, time bonus, `D294` bit 6; five per-stage colourways; results card draws five collected-stage icons from `$D2CC` | **ROM / source-traced** | SS-A4/A5 |
| Type `$31` is the Chaos Emerald / Special Stage success object (not a ring) | **James + manual terminology**, consistent with the ROM above; the ROM itself only proves the flag/icon/colour linkage, not the name | this follow-up |
| Surface `$1D` block `$B8` = Large Ring, +10 rings, collected once per cell | **ROM-traced** (CONTROLLED `$753E`); the name "Large Ring" comes from James/the manual | section 2 |
| SS3 has exactly one branching junction; Up selects the branch that reaches the Emerald room | **ROM-traced** (original router + whole-game counterfactual) | section 3 |
| SS3 monitors are *intended* to block progress and cost time | **James's original-game observation** + **Sonic Retro** ("A series of tubes blocked by Invincibility Monitors"); not proven by ROM that they cannot be bypassed | section 3 |
| Special Stages are normally reached in Acts 1/2 | **manual / community**; supported by a ROM census (below) | section 5 |
| Entry Fail glitch exists | **community-documented**; mechanism reproduced from the ROM (below) | section 6 |

## 1. Terminology

Human-facing text now calls type `$31` the **Chaos Emerald (Special Stage success object)**; it is distinct from the **Large Rings**. Identifiers (`goal-ring.json`, `ss_goal_ring.py`, board id `goal-ring-in-situ`, doc file name) are kept to avoid churn; the audit doc carries a correction note. No behavior, placement, parameter or collision value changed.

## 2. Large Rings (ROM-traced)

Terrain surface type `$1D`, block `$B8`, is handled by the terrain-ring probe `$753E` (not by the no-op floor handler `$69B1`, which earlier text over-simplified). CONTROLLED: from any probe position inside the 32x32 cell (four positions tested) the result is identical: cell becomes `$46`, `D29A += $10` (BCD), one collection per cell, **10 rings each**; a wrap past 99 adds a life (the wrap path of the shared add). Counts: **SS1 128 cells, SS2 8 cells** (maximum 1,280 / 80 rings), none in SS3-5 and none in any ordinary act. They are separate from the 144 / 26 / 15 ordinary terrain-ring quadrants of SS1 / SS2 / SS5 and from the `$31` object. Inside a stage the ring count only feeds the results tally (`RING n x 100`); entry is refused in zones >= 6, so reaching 100 there only grants a life.

## 3. SS3 tube stage

- **One junction.** Block `$7A` occurs once in SS3 (cell at (3296,352)). The natural route (2,090 frames) makes exactly **one** router decision: at WORLD (3306,364), moving left at 6.0 px/update, with the pad held = `$01` = **Up**. The original router (and the final-zone model) gives two outcomes at that block: any pad without bit 0 keeps the tube going left; any pad with bit 0 (**Up**) turns the player up (Vy -6.0).
- **Proved by counterfactual.** Forking the whole game 14 frames before the decision and holding one direction only while Sonic is on the junction cell (then neutral): **Up** ends in the Emerald room (x 3790, y 494); neutral, Down, Left and Right all stay in the upper tube loop until the clock runs out (all four end at the same loop position). So the held direction James remembered is **Up**; it is needed only for the duration Sonic is on that single `$7A` block, approached travelling left.
- **Repeated sections.** The five lower room+tube sections are near-identical (layout comparison against the first: 292 / 294 cells identical for the second section; 229-266 / 294 for the others on a fixed 21-cell grid, indicating minor edits), consistent with the deliberate repetition James and Retro describe.
- **Monitors.** The natural route breaks **5** of the 7 invincibility monitors: exactly the five at each room's tube mouth ((240,622), (912,622), (1584,622), (2256,622), (2928,622)); each stands at the cap column (the room's last cell, x 224..255) immediately before the mouth block at x 256, in the jump arc the natural route uses to reach the pipe (walking is blocked by the cap column). The other two are in the pool room (2800,366) and final room (3696,622). The invincibility reward (`D532 = 6`, 600 updates) is real and fires 5 times on the route. That the monitors *must* be broken (cannot be avoided) is James's observation plus Sonic Retro; the ROM proves only their placement, reward and that the natural route breaks them. The earlier "purpose unresolved" note is **replaced**: they are route obstacles / time-cost gates, with a genuine reward, in a stage that deliberately repeats tube sections before the single branch to the Emerald.

## 4. SS2 natural route

SS2's gameplay contract remains closed. I made one time-boxed closure attempt with the existing full-state harness, using the intended structure (reach the first Spring Shoes by input, then chain bounces with horizontal steering only, never pressing jump, which would detach the shoes): the focused search from the shoes-acquired state exhausted after 452 nodes, and a larger generic search (jump-run and steering actions, 4,034 nodes) exhausted again without a route (best Y ~1277 of 142). I did **not** consult the external walkthrough (no web access was used), so no route hint beyond the known station layout was applied. **SS2 remains an unresolved route-automation item, explicitly non-blocking**: the Spring Shoes pickup/relaunch (-7.5), platform layout, Chaos Emerald object and failure routes are unchanged and already proven; only a replay-verified input script is missing. A future attempt should use a purpose-built station-to-station controller (the shoes stay attached only while their owner `$2F` object lives).

## 5. Act 3 quirk: dormant, not reachable through normal entry

- **Normal access (community/manual):** Special Stages are entered during Act 1 or Act 2 and return to the next act of the same zone.
- **ROM-traced mechanism (unchanged):** if entry happens while the act index is 2, the return makes it 3 and aliases the adjacent act-table data (zone 0 act 3 loads the zone-1 act-0 start/art/objects, etc.).
- **Reachability (DECODED census, upper bound):** entry needs the ring counter to wrap past 99 *within one act* (`$2A4F` zeroes `D29A` at every act load). The maximum rings obtainable in each act-index-2 act (every terrain ring quadrant, `$09` ring and +10 source, none lost) is THZ3 19, GPZ3 19, SEZ3 42, MGHZ3 **83**, AQZ3 14, EEZ3 0. Acts 1 and 2 reach 74..289. **No act-index-2 act can reach 100 rings**, so the quirk is **dormant: unreachable through normal entry** (reachable only by forcing entry, e.g. by a harness or cheat). No evidence of natural access was found. A claim that "Sonic Chaos has no known Act 3 bug" is not adopted: the cited source does not make it, and this finding rests on the ROM census, not on absence of reports.

## 6. Special Stage Entry Fail glitch

Community documentation reports the stage ejecting Sonic almost immediately after 100 rings. A **plausible ROM mechanism was found and reproduced** (status: *mechanism reproduced in the harness; not claimed to be the only cause*):

1. Entry (`$178F -> $1753`) stops the timer (`$D2BE := 0`) but leaves the 60-frame tick counter `$D2C2` at whatever the act's timer had.
2. The loader (`$2934`) zeroes `$D2BF/$D2C0`, sets the timer-run flag `$D2BE := $FF` and waits a frame. The stage's own timer (`$59`) is written much later (`$17F1`) and `$D2C2` is reset by `$1758` after that.
3. In stage mode (`D294` bit 7) each tick decrements `$D2BF`; `0 - 1 = $FF` takes the timeout branch `$2846` and sets `D294` bit 5 (stage failure).

CONTROLLED/EMULATED test of all 60 values of `$D2C2` at the moment of the 100th ring: **only `$D2C2 = 59` fails** (1 in 60), at frame 242, the moment the stage becomes playable; the timer display shows `0:59` and the normal failure return follows (next act, no emerald). This explains an "almost immediate ejection" at a roughly 1/60 rate, which depends on the frame phase of the ring pickup. Canonical entry/exit behavior is not changed by this note.

## 7. Open, non-blocking

Sound names (`$8A/$86/$B5/$F8/$8F`) remain unresolved and non-blocking.

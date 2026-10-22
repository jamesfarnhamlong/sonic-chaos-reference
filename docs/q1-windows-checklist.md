# Q1 — Chief's Windows checklist

**Target: 348×196 WIDE, GameMaker F5. All Q1 results are NOT TESTED.** Use the existing accepted C2-E1 project (`4eb684911c5785667181b9d3f940b1dc820e66d1`). This document prepares testing; no Windows run is claimed. No 256×192 GameMaker testing is required.

## Set up once

Open the accepted project's `SonicChaos_POC.yyp` and press F5. At the title choose **Options → screen size → wide**, using arrows and Space; return with **back**. WIDE fixes the logical view to 348×196; window size only magnifies it. AUTO can use another size. If the accepted project/assets cannot run, record setup **BLOCKED** and the reason; this assignment supplies no new package.

Use arrows to move and **Space** to jump/confirm. **Enter** opens pause; choose **resume game**, **level select** or **back to title** with arrows/Space. At title, **new game** starts Sonic in Turquoise Hill 1 with fresh progress; **level select** opens the developer grid. In the grid, arrows choose a zone/ACT and Space confirms; Esc returns to title. Use these menus, not historical F10 instructions.

For smoke tests, choose **CHAOS EMERALDS 5** before an ordinary act launch to avoid 100-ring Special Stage detours. For the first Electric Egg 3 check use 0 for the simpler partial ending. Presets are shortcut fixtures, never natural campaign progress. A fresh **new game** clears them.

## Short acceptance list

| Priority | Required evidence | Result |
|---|---|---|
| 1 | Electric Egg 3: all three encounters, camera jumps, final defeat, ending and usable title | NOT TESTED |
| 2 | Sessions B–D below: six-zone smoke, goal/results, boss release and next-act control | NOT TESTED |
| 3 | One separate title/New Game campaign, with an 18-act run log | NOT TESTED |
| Optional | Five Special Stages and both Sonic ending variants | NOT TESTED |

Choose **PASS / FAIL / NOT TESTED / BLOCKED** for each row. PASS means the stated sequence was observed; FAIL records expected versus actual; BLOCKED names what prevented testing. Keep untouched work NOT TESTED. Prior milestone passes are historical, not Q1 results. A known visual difference does not automatically fail an otherwise successful handoff.

## Targeted smoke — sensible sessions

After a clear, allow the run-off, results tally and next-act title to finish; confirm control in the destination before marking its transition PASS. Space may speed the tally/title hold; use it after first seeing the card. Developer-launched ordinary acts also advance to the next act, but remain shortcut-origin tests.

| Session / ID | Start with Level Select; observe this once | Result |
|---|---|---|
| A / EEZ3-FULLCHAIN-F5 | **Electric Egg ACT-3**, Emeralds 0. Play from its start through **first encounter → travel/camera jump → second encounter → travel/camera jump → final encounter → defeat → partial Sonic ending/TRY AGAIN → title**. No encounter skips or forced kills. Camera jumps can be canonical; no ordinary run-off/results card is expected here. | NOT TESTED |
| B / S02 | **Turquoise Hill ACT-1**: slope/movement and an available spring or Badnik contact; goal sign → results/title → **Turquoise Hill 2**. | NOT TESTED |
| B / S03 | **Turquoise Hill ACT-3**: partial-edge boss entrance, fight, defeat and camera release → results → **Gigalopolis 1**; check arrival control. | NOT TESTED |
| B / S04 | **Gigalopolis ACT-3**: approach/backtrack briefly before the arena locks; defeat/release/results → **Sleeping Egg 1**. | NOT TESTED |
| C / S05 | **Sleeping Egg ACT-1**: cross an encountered crumble ledge and release/reland on support; sign/results → **Sleeping Egg 2**. | NOT TESTED |
| C / S06 | **Sleeping Egg ACT-3**: entry/fight/defeat, camera follow and exit → **Mecha Green Hill 1**. Sample an accessible platform or ceiling/spike interaction on arrival. | NOT TESTED |
| C / S07 | **Mecha Green Hill ACT-3**: vertical camera takeover/fight/defeat/release/results → **Aqua Planet 1**. Record the known pit/tree reveal separately. | NOT TESTED |
| D / S08 | **Aqua Planet ACT-1**: water crossing, jump/swim and a reachable platform landing; sign/results → **Aqua Planet 2**. | NOT TESTED |
| D / S09 | **Aqua Planet ACT-3**: approach/arena lock, fight/defeat and victory scrolling → **Electric Egg 1**. Try carrier/platform attachment and jump release if reached; sign/results → **Electric Egg 2**. | NOT TESTED |

If a representative interaction is not reached, leave that observation NOT TESTED while recording the transition separately. Do not repeat an entire completed card just to inspect an unreached interaction; finish it on the campaign route or a later targeted visit. If a campaign visit already records the same smoke observation, reuse that evidence rather than replaying it. The short smoke does not cover every act; the matrix makes omissions visible.

## Continuous campaign — a separate run

Return to title and choose **new game**, never Level Select. Follow:

**Turquoise Hill 1–3 → Gigalopolis 1–3 → Sleeping Egg 1–3 → Mecha Green Hill 1–3 → Aqua Planet 1–3 → Electric Egg 1–3 → Sonic ending → title.**

Use one run ID. Fill the [18-act matrix](q1-18-act-coverage.md) as each act is entered and exited. Record deaths, normal continues, Special Stage detours and the observed ending. Ordinary deaths/continues may stay in the same campaign attempt; this is not a deathless challenge. Pause/resume is allowed. For breaks, leave the running game paused: campaign resumption after closing F5 is not supported by the natural save path.

Level Select, debug/restart shortcuts, a new title/New Game, or closing/relaunching ends qualification as an uninterrupted run. Preserve completed segment results; do not join segments into an uninterrupted claim. A return to title through game over ends the attempt; record an incomplete run, not automatically a game defect. Do not deliberately fail to test game over during the main campaign.

Natural 100-ring Special Stage detours can occur. In Act 1/2 they return to the **next ordinary act**, not the pickup point; record that exit kind and leave any bypassed normal sign/results transition NOT TESTED. If a detour unexpectedly returns to Turquoise Hill 2 from elsewhere, record the source act and block the dependent campaign continuation for review. Do not force an Act 3 Special Stage entry.

## Optional follow-ups

**Special Stages 1–5:** the grid's SS-1…SS-5 entries are enabled. For each stage, set CHAOS EMERALDS to the stage number minus one, launch Turquoise Hill ACT-1, then pause → level select → the desired SS. This establishes Turquoise Hill 1 as the origin, so expect Turquoise Hill 2 on return. Do not assume a title round trip clears an older selector origin. Observe success/emerald/results/return for each stage; add one failure/timeout return. These shortcut runs do not prove natural access. Separately, one natural 100-ring Act 1/2 detour checks entry and return; five completed Emerald bits refuse further natural entry.

**Endings:** partial uses fewer than six completed bits. For the full Sonic route, use five naturally earned Special Stage Emeralds, or the optional developer **CHAOS EMERALDS 5** preset, then **collect the final Electric Egg Emerald** after the final encounter; expect full ending, credits, END. and title. A preset alone is not six Emeralds. Test title/New Game reset after the ending. The two variants need not both be repeated merely to close the first-priority chain; a fully observed optional full route can supply that chain evidence instead of a second partial run.

Keep these OPEN: visible spring/Badnik oscillation, slope sticking, diagonal static-spike contact, state-$20 timing lag, C2-R3 spike-phase uncertainty, and **PRES-ENTRY-MGHZ3** pit/tree reveal. Note act, input, visible world movement versus facing/camera, and reproduction if encountered. They do not automatically fail unrelated successful checks. No new diagnostics or precise frame measurement is requested.

Record: **run ID / date / entry route / act / observation or transition / result / expected vs actual / short notes or video reference**. See [source-backed flow and limitations](q1-campaign-flow-source-map.md) and the [machine-readable register](../data/q1/coverage-register.json).

# Sonic Chaos — Chief's Product Direction: Classic vs Enhanced (13 November 2026)

> **CURRENT IMPLEMENTATION UPDATE (13 NOV 2026).** R15 integrated 4:3 Classic/16:9 Enhanced + distinct Pauses and R16 corrected original ROM Family B attract demos are delivered separately and Manager-reviewed. [R17 combined private implementation](R17_R15_R16_DUAL_MODE_ATTRACT_INTEGRATION_20261113.md) is NOW ACTIVE, superseding the earlier 'NEXT R15' sentence below; no production merge or Chief final approval yet.
**HIGHEST PRIORITY LIVE OWNER INSTRUCTION · supersedes the prior strict 100%-ROM-equivalence interpretation and contradictory older C1 holds**

## Why this exists

Chief explicitly corrected the scope on 13 November 2026 after reviewing the cost/progress of C1 R1–R14. This is a **personal, noncommercial translation/recreation into GameMaker**, not static ROM compilation, emulator-cycle reproduction, commercial QA or a research paper. Target **as close to original as reasonably possible** in Classic, NOT a numeric 100% proof or exhaustive worst-case equivalence. Achieving excellent practical accuracy is important, but speculative edge cases, one-pixel differences, rare hardware cadence and exhaustive ROM-wide test obligations are **not automatic production blockers**. Where necessary to make an enjoyable, stable PC game, a narrow documented compatibility compromise or omitted marginal detail is acceptable. **No excuse for avoidable major gameplay/rendering regressions.**

Previous management authored repeated ROM-wide 'strict exact' gates; these were Manager overinterpretation. The historical technical reports and their observed facts remain valid, but older claims that *all* obscure differences must be closed before shipping are **superseded** by Chief's product decision. Technical exceptions and approximations must be clearly recorded, not concealed.

## Two user-facing modes — binding contract

### CLASSIC
- True **256×192**, original **4:3** gameplay/viewport/nearest integer output. Remove **widescreen-specific corrections/adaptations** introduced to make 16:9 fair or convenient; use original-like 4:3 camera/movement/objects and preserve normal Sonic/Tails levels, bonuses, SS, bosses, original quirk where feasible. Do NOT proactively add enhancements, cosmetic fixes, discretionary QoL or redesigns.
- Authentic **original attract-mode demos** THZ Sonic, GPZ Tails, SEZ Sonic: R12 experimental playable proof exists; pending Chief visual/functional smoke. Its native input-pair-per-player schedule isn't cycle-equivalent to original IRQ; it can be used as a **documented practical adapter once Chief has approved its feel**, rather than withheld indefinitely for perfect IRQ timing.
- Classic original-style **Pause = freeze**, no normal option/level-select/pause menu. If a frozen PC game traps users, the **smallest separate unobtrusive quit/title affordance** is permitted as a platform usability adapter, clearly distinguished from original ROM behavior. Pause only in appropriate gameplay phases; prevent input leakage and save corruption.
- Original behavior **as close as practical**; PC compatibility patches are permitted only for demonstrable necessity, not discretionary 'improvements' in Classic. No 16:9 camera fairness bleed-through.

### ENHANCED
- Preserve Chief-approved **348×196 16:9 gameplay** as the default old 'Classic' widescreen presentation, with accepted S6 frontend/options/saving/audio/Boss Rush and adjustments **unchanged unless specifically chosen for improvement**.
- A modern useful Pause menu: **remove developer Level Select**, include accessible existing/initial relevant Options/toggles to see the effect in play, prohibit pause in inappropriate transitions/screens/results, add stage/level icons. Use existing original-derived art where possible; avoid requiring newly invented assets for first code pass. Never weaken existing save/Options/Boss Rush state.
- Offer optional **enhancement/QoL gameplay features** through a coherent toggle system, default OFF for newly added discretionary gameplay changes unless Chief specifies otherwise. Plan one or two substantial later QoL implementation sprints after integration/pause foundation.
- **Chief has now supplied six completed 144×128 Save TV preview pictures in a directory named `save_pictures_144x128`.** Integrate their verified zone mappings into Enhanced Save/Data Select under the [R17 addendum](R17_ADDENDUM_CHIEF_SAVE_TV_144X128_PREVIEWS_20261113.md), replacing only the older interim preview artwork. Do not recreate/guess the art or change the save-slot system; Classic remains unchanged. The earlier generic/shared Pause redesign is superseded by **two mode-specific pause behaviours**.

## Development/credit discipline

1. **Make tangible playable progress first.** Prefer cohesive implementation batches to repeated microresearch and source-host traces with no runtime change. Good enough and working beats a theoretically perfect unplayable/unfinished translation.
2. Preserve separate evidence levels: original-ROM observation, compiled-native reproduction, host-only tests, Chief actual play, and unverified. No '100% ROM accurate' claim from bounded captures.
3. Preserve old safety regression controls intelligently: targeted compile/play and changed-owner tests while implementing; one final comprehensive S6/Classic R2/R3/R10/R13/R14 suite **only after a meaningful changed integrated candidate**. No marathon 10,542-state/138-image/massive ROM census every work iteration.
4. Fix **visible, frequent, or game-breaking** discrepancies with priority. Keep rare unproven source-equivalence, original VDP mask/cadence, original first16 pool, obscure host verifier mismatches and current **one-pixel early ordinary camera phase** in a documented audit backlog unless they cause actual practical defects. A moderate effort for noticeable fidelity gains is welcome; multi-week research into a virtually invisible edge case is not.
5. Production, immutable accepted S6, experimental R12 Chief-test build, private ROM/art/source and saves remain protected. **Authorize a new private dual-mode integrated trial** on an isolated branch; do not merge/release accepted production until Chief personally tests. 'Old production Classic' and new isolated C1 source must be reconciled rather than assuming R14 was installed.
6. Avoid programmer/debug UI in release modes. Preserve original ROM peculiarities in Classic when practical, while acknowledging this is a translated PC application. Enhanced includes deliberate improvements behind user controls.

## Active order and roadmap
**NEXT:** [C1-R15 dual-mode product integration and separate Pause behaviours, implementation-first](C1_R15_DUAL_MODE_INTEGRATION_AND_PAUSE_IMPLEMENTATION_20261113.md). Once Chief reports R12 practical demo checks, integrate the reviewed authentic-input demo approach into Classic only if it meets the practical standard, with documented noncanonical IRQ. Then one/two substantial Enhanced QoL batches and Chief Save TV art integration. Audit after practical completion, using research to feed future improvements, rather than treating it as a prerequisite to seeing a usable game.

All historical C1 charters that assert absolute ROM-wide equivalence is a mandatory pre-production gate are **superseded** by this Chief-approved product brief; their facts, raw test results and valuable source corrections remain.

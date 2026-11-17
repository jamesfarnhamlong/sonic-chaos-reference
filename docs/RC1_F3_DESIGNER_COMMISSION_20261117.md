# Sonic Chaos — F3 Classic ROM Fidelity Audit and Corrective Sprint
**17 November 2026 · Manager-San #13 · CHIEF ENGINEERING GO**

## Mission
Chief authorizes ONE substantial **F3 audit-first sprint** to close the newly observed Classic fidelity issues on the already Chief-accepted private **v0.99.2-f2** baseline. **Highest priority: SC-RC1-23 MGHZ3 boss camera too high compared with the original ROM; make a demonstrable all-six-Classic-boss ROM parity audit, not just another local offset.** Also remove the Classic Pause non-ROM white hint (SC-RC1-24). Investigate intermittent missing spikes/Motobug SFX (SC-RC1-25) and crumble top-corner sticking in SEZ/AQZ (SC-RC1-26) against real original-ROM execution. **Audio and crumble are research-first; do not fabricate a fix when the ROM behaves the same.**

Chief has checked **17/17 F1+F2 tickets PASS** on v0.99.2-f2, completed a full **Classic Sonic** campaign and a **one-emerald Enhanced Sonic** campaign. These accepted fixes are protected: do not restart F1/F2, silently change a reported gameplay feature or call an ordinary preservation pass proof of ROM accuracy.

## Authoritative references
PUBLIC management/research (documentation only):
- `ROADMAP.md`, `AGENTS.md`, `MEMORY.md`, `docs/CURRENT_MANAGER_HANDOVER.md`
- `docs/RC1_CHIEF_FULL_RUN_DEFECT_REGISTER_20261115.md` (SC-RC1-23…26; 17 earlier Chief-pass tickets)
- `docs/RC1_F3_CLASSIC_FIDELITY_AUDIT_AND_CORRECTIVE_GATE_20261117.md` (governing F3 charter)
- `docs/sez-surfaces-0c-13-1a-audit.md` (authenticated ROM crumble `$AF/$0C/$13` contract)
- `docs/RC1_F2_MANAGER_REVIEW_AND_COMBINED_CHIEF_TEST_GO_20261116.md` (F2 compiled candidate identity)

PRIVATE GameMaker repository `jamesfarnhamlong/SonicChaos_POC`:
- [F3 parent #9](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/9), [camera #5](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/5), [Pause #6](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/6), [SFX #7](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/7), [crumble #8](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/8).

## Exact branch/preflight
- **Frozen F2 game source to branch from:** `5d045ae0bba8dcbfa3f220c8e96d78baaa4fc22e`, tree `d5d35c546c26f201f35257353ba4ea2dcd28974e`. Private F2 branch `fix/f2-rc1-presentation-20261116` has additional `verification/`-only commits, **not gameplay changes**. If needing their harnesses, carry them forward independently and document that choice; start gameplay from exact frozen F2 code, not arbitrary branch tip.
- Create and immediately push a **separate private F3 worktree and branch** (for example `fix/f3-classic-rom-camera-fidelity-20261117`); report remote branch and verified starting SHA. Protect frozen RC1, F1, F2 branches, tags and ZIPs, accepted Classic freeze, production `main`, all 22 authenticated private dependencies, H: independent backups and Chief's current Sonic/Tails saves.
- Read current implementation before changing it, including F1 GPZ3 **draw-only +17** camera correction (Pre-Draw/Post-Draw) and shared camera/render owners. Remember a 256x192 Classic screen is not a cropped 348x196 Enhanced window. Explicitly trace logical camera owner, renderer scroll/viewport, mode dispatch, stage/boss transitions and fullscreen handling.

## Workstream A — SC-RC1-23 P1: all six Classic boss cameras
**Chief observation:** MGHZ3 boss view is **too high** in Classic compared with the original ROM. Do **not** assume the GPZ3 +17 correction applies; do **not** assert the source is necessarily Enhanced leakage until proven.

1. **Audit matrix for THZ3, GPZ3, SEZ3, MGHZ3, AQZ3, EEZ3**. Each arena must have ORIGINAL ROM vs F2 native evidence for approach, camera lock/pan/boss reveal, settled arena, significant mid-fight vertical phases, boss defeat and transition/clear. Include **EEZ3's moving-camera case** and any special camera override, not just fixed-position probes. Include Sonic and Tails where camera paths differ.
2. Align frames meaningfully using original-ROM **VScroll, player world X/Y and world-to-screen coordinates**, boss anchor, floor row, camera X/Y, horizontal/vertical limits, viewport dimensions and camera ownership/ordering. Distinguish original game camera values from a screen-only presentation offset. Capture selected ROM screen frames at true 256x192 and **compiled native GameMaker** 256x192 images; record pixel/image differences with authenticated reference (do not treat picture-ratio or display scaling as gameplay error).
3. Identify the **first divergence** for MGHZ3 and any other actual mismatch; prove if an Enhanced widescreen owner/viewport/presentation layer leaks into Classic, or disprove. Check normal-zone-to-boss ownership transfer, bounds preparation/commit, scrolling/clipping, logic vs drawing, F1 GPZ3 draw-only framing and quit/restart. Preserve boss attack patterns, collision, player positions, camera trigger timing and lock/unlock progression. **No global +17 fudge, generalized camera rewrite or accidental physics/viewport changes.**
4. Apply **minimal, individually committed corrections only for ROM-proven divergences**. Repeat original-aligned camera captures after change; run full fights in actual compiled GameMaker including player approaches, not purely synthetic forced states. Record explicit PASS, HOLD or INCOMPLETE per boss and any remaining mismatch. If the all-six ROM numeric matrix cannot be completed, report the exact missing evidence and keep P1 HOLD; do not claim all bosses checked simply because the GPZ test passes.
5. Audit adjacent Classic runtime view/camera ownership as relevant (normal acts, title, Pause, end/results, fullscreen/resize), and **Enhanced 348x196** camera and Boss Rush independent behavior. No changes to Enhanced widening unless there is a demonstrated bug that requires a separate approved scope.

## Workstream B — SC-RC1-24 P2: Classic Pause white text
Remove only the **non-original white instructional overlay** from Classic Pause. Chief prefers these instructions in the README or existing confirmation prompt; it need not be replaced in the rendered screen. Compare authentic Classic Pause image and actual game states. Maintain pause freeze, resume, Quit to Title, quit-to-desktop confirmation, keyboard/controller mappings, fullscreen and **Enhanced Pause menus** unchanged. Independent small source commit and compiled Classic/Enhanced regression.

## Workstream C — SC-RC1-25 read-only first: intermittent missing SFX
Two specific Chief observations:
- Contact with spikes while **Spring Shoes** are worn sometimes produces **no spike sound**.
- **MGHZ Motobug** spring/contact sound intermittently goes missing, although the normal sound is sometimes heard.

Investigate exact **original ROM** request-site IDs, tick/IRQ order, sound mailbox overwrite/priority/intentional omission, native PCM sound request vs actual audible playback; run deterministic single-contact, concurrent-contact and repeated-contact cases with Sonic/Tails in Classic and Enhanced OFF/ON as relevant. Inspect GameMaker `SCR_chaos_audio` and event callsites, but do not assume a queue bug from symptoms. Cross-reference SC-RC1-22 ROM `$A5` twist-gate sound research as separate context, not an automatic third bug to implement.

**Decision:** if original ROM also omits the SFX in the same circumstances, record **ROM-authentic NO CHANGE**. If a proven mismatch exists, document source-first divergence, specific minimal patch and preservation tests; **seek Manager/Chief review before changing shared audio mailbox/priority/driver behavior**. Do not add global “always play” SFX or restructure music arbitration as a side effect. This research result can be delivered as HOLD/patch proposal while independent F3 camera and Pause work finishes.

## Workstream D — SC-RC1-26 read-only first: crumble corner sticking
Chief notices SEZ/AQZ upper-side/top-corner entry onto crumble blocks can cause the player to appear partly **inside the ledge** until it breaks, Classic and Enhanced.

Authentic ROM research already proves surface `$0C` / block `$AF` / object `$13`: **T+1..T+16** hold; player Y = cell top −16 (feet **2 pixels into block**), Y velocity 0 and **no player-presence check**. This can make odd corner hold / hovering original behavior. But compare **the exact top-corner collision approach**, not just ordinary standing:
- ROM vs F2 frame-aligned X/Y, velocity, animation/feet, flags/state, collision foot sample, cell state/object T, camera and screen position through break T+17 and sound/shards T+18.
- SEZ and AQZ (plus controls in THZ/EEZ), Sonic/Tails, side vs top/corner entries, relevant speeds and Spring Shoes and mode state.
- If matched to original, close as **ROM-authentic NO CHANGE**, explain the two-pixel overlap and original absent presence test in the owner guide. If mismatched, document root cause and a **minimal proposed correction** with preservation tests; do not alter the F1 93-cell crumble solution or broad player collision without evidence and a management scope decision.

## Working cadence, isolation and testing
- Do this as **one long autonomous agent sprint**, not many tiny owner trials. Evidence before source edits. Commit/push independently traced camera/UI changes and research reports at substantive checkpoints. Root-cause ambiguity means evidence-backed HOLD, not green test inflation; continue unrelated tasks. You may ask for a decision if a **large shared audio or collision system change** would be required; otherwise finish independent authorized work.
- Execute potentially dirty native tests only under the existing standard `SCTest` account, ensure watcher receipts show **zero writes to Chief's normal `%LOCALAPPDATA%\SonicChaos`**; normal Chief save namespace stays unchanged and completed Sonic/Tails files protected. Set explicit per-run screenshot/log **file-count and byte budget**, retain a compact hashed evidence sample, remove only known disposable scratch output; no thousands of PNGs, 150GB audits or extra full-project copies.
- Repeat compiled native **all 17 Chief-accepted F1/F2 ticket scenarios as far as feasible**, including ten F1 carry-forward, F2 original ROM Zone Select, Save TV default (owner check already passed), Pause previews, GPZ results, EEZ flash, SEZ3 pogo and music, AQZ loops and boss HUD, Classic GPZ3 floor and Special Stage 1 TV start. Run standard R22/RC1/F1/F2 preservation against frozen F2 and relevant ROM images. Enumerate which scenes were actually run vs inferred from shared code. Source suite inherited 75/178 passes: **no newly failing F2-passing tests**, do not misstate 178/178.
- Assert Classic **true 256x192**, Enhanced **348x196** and options/window/fullscreen/per-character path separation; include Boss Rush and save resume. Shipping runtime contains no probe/diagnostic hooks, no hardcoded path to Chief, no trial-prefix save disappearance.

## Deliverables and authority
Deliver in ONE private F3 bundle (if any source fix required):
- One clean Windows private trial (distinct F3 identity, e.g. `v0.99.3-f3`) plus one complete source archive (22 authenticated dependencies), SHA256 and per-file manifests, exact game-build/source package SHA and changed files, PRIVATE Git branch/commit/tree receipt.
- **Six-boss Classic ROM camera parity table**, numeric timeline/captured original-vs-compiled frames, exact MGHZ correction and GPZ +17 preservation; Classic Pause before/after; sound and crumble research verdicts (**authentic NO CHANGE vs proven mismatch/HOLD/proposal**) and any residual limitations.
- Combined native regression/preservation and isolation report; independent H: recoverability and no write pollution.
- **Short Chief acceptance guide** prioritizing MGHZ3 real fight, GPZ3 previous correction, the other four boss arenas, Classic Pause, then a quick Enhanced check. Do not require another full Sonic/Tails campaign unless evidence shows it is necessary.

**Do NOT** merge or cherry-pick Super Sonic R3d, rewrite loop physics, alter known original MGHZ2 slow twist, implement speculative sound effects, retime attract, erase AppData, change canonical saves, merge production, tag, publish, nominate RC2 or declare v1.0. **Engineering PASS does not equal Chief acceptance.** RC2/v1.0 remains HOLD until Chief verifies any F3 camera fix; NG+ integration is a separate post-normal-baseline gate.

**Chief has commissioned F3. Proceed and deliver one evidence-backed private candidate and report.**

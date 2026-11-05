# Sonic Chaos Enhanced — Sprint S1: Display Foundation
**5 November 2026 · Manager-san #10 · Chief-approved sprint-style working model · Authorize integrated Enhanced display development within scope**

## Why this sprint
Chief requests **fewer one-feature/micro-change tasks**, more substantial agent work, fewer repetitive standalone Windows builds and human F5 checks, and **one larger integration/testing/adjustment round per coherent sprint**. We retain source/ROM fidelity evidence and frozen-original protection, but move ordinary investigation, iteration and focused tests inside the sprint.

**One integrated development branch, many scoped internal checkpoints, one final Chief-facing private Windows candidate.** Research and implementation may proceed within the pre-approved scope without a new Manager review at every routine finding. A blocking need to edit frozen-source code or change the accepted design, a gameplay/audio regression, new renderer lifecycle hazard, or unbounded build/tool costs is an exception requiring a stop and scope review.

## Source provenance and guards
- **Permanent frozen Classic tag** `classic-core-20261105`, private source `3a58912659b48573ac7f2c5c96a02a2211d5e4da` and original Windows/source ZIPs are immutable.
- **Chief-accepted E0 frontend:** `deccefc0acd822f74b6b26895ec278cdf67a7cee`, private branch `enhancement/e0-r1-ui-20261105`.
- **Delivered E2-P1 Sharp Pixels local pilot:** Designer reported `ebcc8fc46dad5a9763fcfd24cdfb3ead98b0f823`. This SHA was not available in the connected game GitHub remote; Designer **must verify actual local commit, parent, clean worktree, receipt and branch before inheriting it**. If local parent/verification cannot be established, safely branch from accepted E0-R1 and recreate the bounded Sharp feature with evidence. Do not push/merge automatically or treat absence from remote as failure.
- Manager inspected **134 private visual comparison PNGs** for E2-P1. Classic and Enhanced Sharp OFF were pixel-identical in all eight controlled main groups. Sharp ON produces crisper outlines/HUD/THZ terrain; subjective in-motion Chief acceptance is deferred into sprint's combined check. Keep Sharp **OFF by default**, not pre-accepted as a permanent Enhanced default.
- No release/public ROM/asset transfer. Keep snapshots/comparison PNGs and detailed private receipts outside public reference Git.

## S1 coherent work package: one Enhanced display pipeline

### W1. Consolidate the accepted Sharp Pixels option
- Incorporate E2-P1 as a reversible option on the existing direct Enhanced Options screen: `SHARP PIXELS OFF/ON`, default OFF. Keep Classic display byte/pixel-equivalent to accepted E0 under matching state.
- Preserve GameMaker existing project Windows interpolation settings for Classic. Explicitly capture and restore the actual GPU filter state; do not assume a hardcoded baseline.
- No separate manager for every visual option, no FX/dev keys, no parallel game executable. `START GAME` remains the final selectable entry; ESC/pad B returns to mode choice before launch.

### W2. Build a robust native-grid and integer-fit Enhanced presentation foundation
- Current `SCR_screen` renders at view × multiplier (e.g., Wide348×196 → 1044×588 at 3×, actual Retro290×218 → 870×654); **nearest sampling alone is not native-grid integer-fit**. Build the smallest sensible Enhanced-only output path that rasterizes native logical pixels before scaled display and supports letterboxed integer fit of the chosen logical view.
- Preserve **existing camera/viewport semantics** of Wide, Retro and Auto; don't replace Auto with 348×196, stretch/crop HUD, or change world visibility/culling. Native256 is a controlled parity view only.
- Example desired 1080p Wide target: 348×196 at 5× = 1740×980 with centred borders (90px sides/50px top-bottom). These are mathematical visual targets, not claims of available fullscreen/resizing APIs. Do not silently change host resolution/window mode; where normal Windows project options prevent arbitrary fullscreen/resizes, first implement a viable explicit window/presentation policy and record constraints before expanding compatibility.
- Design robust resource ownership and fallback: application_surface, palette decoding, camera transforms, GUI/virtual controls, aspect fit, mouse/pad positioning if relevant, surface loss/recreation, window size/DPI, and suitable alpha/blend shader state restoration. Avoid new allocations each frame.
- **Critical lifecycle gate:** existing Pause and death/results paths deactivate instances. Do **not** disable automatic app-surface presentation until the single Enhanced presenter is proven alive, or the fallback is guaranteed to restore automatic rendering in every such path. Verify through native transitions; no blank screens. If the only solution requires altering protected preexisting Classic runtime GML/events, **STOP and provide an exact delta/alternative rather than slipping a core edit into S1**.
- Keep one reversible compatibility path and explicit failure behaviour. If true integer fit cannot meet correctness and source isolation, mark W2 BLOCKED and retain W1; do not substitute a post-filtered 3× surface while claiming native-grid fidelity.

### W3. One optional restrained CRT effect, conditional on W2 safety
- If and only if the common Enhanced output presenter is stable, implement **one simple, attributed single-pass CRT proof of concept** on its output. Do not port Lola Retro's eight-pass Master System shader under S1.
- `CRT FILTER OFF/ON` on the same Enhanced Options page, default OFF. Minimal scanlines/weak mask, neutral colour, no temporal feedback, no overscan/crop, no blur that destroys HUD readability. Explicitly honour licence/notice for any external source; prefer new self-contained shader when licence/technical fit permits.
- If the CRT shader cannot compile/operate in the installed GameMaker runner or would require protected core edits, skip W3 with documented cause; no incomplete/broken menu switch. Restore sharp/compatibility presentation when unavailable.
- Do not claim consumer-TV electrical authenticity, measured better 60 FPS delivery, or GPU performance without data. Existing E1 pacing proposal remains HOLD.

### W4. Integrated Enhanced Options and compatibility
- Use one stable, namespaced registry and display policy for `SHARP PIXELS`, `INTEGER FIT` (or an unambiguous integer-scaling presentation choice), `CRT FILTER` **only when features really work**. All features initially OFF in Classic; avoid implementing hypothetical options.
- Product defaults pending Chief approval: **all new effects OFF** for the sprint candidate. The menu should make chosen ON/OFF states prominent, preserve up/down/confirm, include easy return to Classic/Enhanced choice, and always keep `START GAME` last.
- A later product decision may make Sharp or Integer Fit default ON, but that is a **Chief decision after real A/B**. Do not write settings persistence or modify `settings.ini` unless the agreed effect cannot function without it; request review before broad persistent changes.

## Verification strategy: economy without compromising fidelity
- During development: agent runs quick source checks, unit/state tests and scene-focused probes as needed; local incremental compiler/smoke tests **only when a risky engine API needs validation**. **No repetitive fully packaged Chief-facing Windows ZIP after each switch or bug fix.**
- At integration: compile **one private standard Windows candidate** and run a **combined bounded matrix** with all installed toggles: (a) Classic; (b) Enhanced all OFF; (c) Sharp ON; (d) Integer Fit ON; (e) CRT ON where available; (f) representative combinations and OFF restoration. Compare canonical simulation/input/camera/animation/audio requests and appropriate pixels against accepted E0-R1 for Classic/Enhanced all OFF. Record intentional Enhanced pixel differences rather than treating them as parity defects.
- Sample first THZ1 Sonic/Tails with camera scroll; AQZ dry/water palette/transparency; foreground/atlas, ring/life/time HUD; title, E0 splash/menu, character choice, pause/resume, results/death/Continue and a representative SS/ending transition as bounded tests, not campaigns. Include Wide348, actual Retro290, 256 controlled reference and Auto behaviour in feasible display sizes. Test focus/minimize/restore and surface recreation if using a manual presenter.
- Externally measured frame pacing remains unknown after E1-P0; **do not conflate** any visual enhancement with stable 60 Hz display delivery.
- Deliver private unscaled matched captures at actual display pixels and labelled 1:1 crops, with camera/state trace and Native/Source-host labels. Separate engine-produced screenshots from art references.
- H: recovery, source-file/commit diff inventory, package hashes, test coverage, explicit limitations and a **single concise Chief acceptance card** for installed toggles and quality in motion.
- If substantial blockers make one integrated build unsafe, deliver an internal progress/blocked report rather than fabricating all-pass or letting the scope expand indefinitely.

## Explicit exclusions
- **No Frozen Classic corrections or GPZ3 tile-art rewrite in this sprint.** FC-PF-001 stays in [post-freeze defects](tracking/POST_FREEZE_CLASSIC_DEFECTS.md); original pixel-perfect maps in local `sources/` will drive a separately authorized visual-parity maintenance sprint.
- **No Enhanced ring-loss rework, save progression, boss rush, Super Sonic, attract-demo implementation, audio driver change or input/physics alterations.** These merit their own coherent later gameplay sprint, with one combined Chief check.
- **No automatic 60 FPS pacing toggles**, clock changes, native audio modifications, public releases, automatic main merge, forced new branch tags or bulk cleanup.

## Operating principle and next decision
Within the above bounds Designer-san may complete, iterate, investigate and self-correct without asking Chief/Manager after each micro-step. Send progress at meaningful internal milestones, not every test command. Stop only at explicit protected boundaries or genuinely unresolved architecture. Chief will review **one integrated S1 candidate** and choose permanent Enhanced defaults. W3 is conditional and may be excluded if the presenter is unsafe; document why.

**Current status: S1 authorized as a substantial development package, subject to exact source and lifecycle safeguards; Chief has requested sprint-style batching instead of per-feature testing.**
# Sonic Chaos E0 — Chief design acceptance and implementation authorization
**5 November 2026 · Chief approval conveyed to Manager-san #10**

## Decision
Chief accepted Manager-san #10's two refinements to Designer's research-only E0 report: **(1) use the existing blue-and-white striped SEGA logo's static final frame, sourced from inherited OpenSonicSMS `SPR_opening_sega`; (2) Enhanced Options must be directly reachable with Up/Down navigation rather than only a Right-key shortcut.** Chief accepted the rest of the E0 design as presented. This approval **authorizes E0 shell implementation and focused verification**, but **does not pre-accept the resulting Windows candidate**.

### Frozen original
- Private `SonicChaos_POC` annotated tag `classic-core-20261105`, peeled commit `3a58912659b48573ac7f2c5c96a02a2211d5e4da` remains permanent and unchanged.
- Start a single isolated E0 successor branch from frozen D, leaving accepted production branch and game `main` unchanged; no retag, merge or separate game core.

### Approved E0 design
- Existing system boot → one new nonpersistent frontend room/controller. It presents a **silent, centred, static SEGA PC-only splash of up to roughly one second**, safe to skip. The original Europe v1.2 ROM does not have a standalone SEGA splash; the inherited OpenSonicSMS sprite's provenance must be recorded. Do not claim ROM-sourced splash artwork, invent logo sound or reattach the legacy splash room.
- Splash → **CHOOSE MODE**. Two actual modes: Classic and Enhanced. Classic highlighted on fresh application boot; mode fixed for session until application relaunch. Use a visible *indented* `OPTIONS` action below Enhanced, reachable by Up/Down like other visible rows. Options is **not** a third mode; selecting it enters a separate Enhanced Options page without committing mode or launching a game. Back returns focus to Enhanced row. No hidden Right-only dependency. Make controls discoverable with keyboard and existing controller mappings.
- Either mode confirms and enters the **same existing original Sonic/Robotnik/Tails cinematic**, then unchanged title, character choice, Sonic/Tails gameplay, Sound Test, results, continue and ending. **Classic and Enhanced must be equivalent in E0** after shell exit; Enhanced is an empty framework only. No 60 FPS rendering, scaling, CRT or QoL implementation now.
- Enhanced Options initially says **'No additional features installed'** with Back. Use one namespaced session mode/feature registry module; registry empty and all effective features false. No fake toggles, developer shortcuts or new config write. Keep existing `settings.ini` intact; future `enhancements.ini` deferred until real features exist. Never borrow legacy save/campaign globals for mode state.
- Preserve original scene clock assignments and audio routing. This includes GameMaker zone `game_set_speed(60,gamespeed_fps)` already present in frozen code, which does **not** authorize a 60 FPS change during E0. Protect input-release boundaries so shell confirmation cannot skip the following cinematic.

### Narrow implementation and acceptance gate
- Prefer only new room `ROM_chaos_frontend`, object `OBJ_chaos_frontend` Create/Step/Draw and script `SCR_chaos_frontend`, with `SonicChaos.yyp` registration and room order insertion after `ROM_system_start` and before `ROM_menu_opening_cinematic`. Existing GML, audio, sprite bytes and original rooms should remain byte-identical. Conditional new text font only if documented glyph audit demonstrates need; no speculative new assets.
- Verify new event/resource registration, exact room ordering and explicit shell → cinematic exit, both modes × Sonic/Tails × native256 controlled reference/wide348; test actual Retro290×218 preference, held keyboard/controller action, shell skip, Options Back, title timeout, Continue, Game Over, existing return routes, game clocks/audio startup and scoped normal gameplay. Compare gameplay after original cinematic relative to frozen D; the new boot sequence itself obviously differs. No third campaigns, audio-catalogue sweep, 60 FPS work or global release audit.
- Produce **one private Windows candidate** plus source and verification receipts, exact branch/commit SHA, SHA-256 and H: backup. Chief conducts one small visual/functional F5 acceptance test. Do not merge to game `main`, alter frozen tag, publish binary, or declare E0 accepted without Chief report.

## Inputs
- Designer E0 research report supplied 5 November 2026: `E0_UNIFIED_FRONTEND_DESIGN_REPORT_20261105.md` in private `management-audits/e0-unified-frontend-20261105`.
- Canonical [E0 research brief](E0_UNIFIED_FRONTEND_RESEARCH_BRIEF_20261105.md), [Manager's design review](E0_MANAGER_DESIGN_REVIEW_20261105.md), [post-Classic enhancement roadmap](ENHANCEMENTS_ROADMAP_20261105.md).

**Management status: E0 DESIGN CHIEF APPROVED; E0 IMPLEMENTATION COMMISSIONED; CLASSIC IMMUTABLE; NATIVE CANDIDATE NOT YET DELIVERED.**

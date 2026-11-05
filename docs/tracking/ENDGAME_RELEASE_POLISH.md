# Sonic Chaos — Endgame Release Polish (Parked)
**5 November 2026 · Chief and Manager-san #10 · RECORD ONLY, NOT COMMISSIONED**

## Scope and sequencing
Chief explicitly deferred this work to the **final release-polish pass**, alongside removal of the developer Level Select. **Do not insert into the ongoing S1 Enhanced Display Foundation sprint, create a new build, request another micro-approval or change any game source now.** These are **shared PC/release UI** concerns for both Classic and Enhanced, not Enhanced-only graphical effects. Preserve the permanent original Classic tag/source/archive `classic-core-20261105` → `3a58912659b48573ac7f2c5c96a02a2211d5e4da`. Later release changes require a new successor checkpoint and Chief acceptance, not silent changes to the frozen artifact.

## RF-001 — Shared PC display preferences, accessible in UI
**Status: PARKED — Chief endgame request.**

**Requested outcome:** a discoverable in-game or pre-boot PC configuration interface to switch **windowed/fullscreen** and the currently inaccessible **window size/view behaviour**, applying equally to **Classic** and **Enhanced**, with persistence across launches. Chief mentioned possible Pause menu, pre-boot optional launcher, or both as options, **without approving one specific placement**. Avoid nesting essential controls invisibly under Enhanced Options.

**Source findings from accepted E0-R1 private commit `deccefc0acd822f74b6b26895ec278cdf67a7cee`:**
- Existing inherited `ROM_menu_options` and `OBJ_menu_options` remain registered in `SonicChaos.yyp`, but the authentic original title bypasses the inherited title/options controller; the old menu is not a currently accessible user flow.
- `OBJ_menu_options/Step_0.gml` implements **window multiplier** `global.windowSize` 1×/2×/3× and **logical camera/view policy** `global.screenSize` Auto (0), Wide (1), Retro (2), plus old Music/Buttons fields. These are **not a fullscreen toggle**.
- `OBJ_menu_options/Destroy_0.gml` saves `windowSize`, `screenSize`, `buttons`, `music` in existing `settings.ini`. `OBJ_system/Create_0.gml` reads the same settings at startup; `SCR_screen/SCR_screen.gml` sets window, application surface and viewport sizes using logical view and multiplier.
- Accepted Windows `options/windows/options_windows.yy` currently has `option_windows_start_fullscreen=false`, `option_windows_allow_fullscreen_switching=false` and `option_windows_resize_window=false`. Therefore **fullscreen/windowed operation is not implemented simply by restoring the inherited options room**.
- The later S1 display sprint is separately building optional Enhanced native-grid/letterbox rendering. A final shared PC window/fullscreen preference must coexist with that output policy without changing actual Wide/Retro/Auto camera visibility or introducing Classic/Enhanced leakage.

**Future design questions and gate:** Decide placement (shared preboot `PC DISPLAY` option before Classic/Enhanced mode is committed, optional Pause shortcut only if safe, or both), clear available labels and actual window/fullscreen support in GameMaker Windows runner, resolution limits/DPI/monitor constraints, how `settings.ini` persists without touching gameplay saves, behavior when rendering presenter is inactive during Pause/results/death, and safe fallback/restoration after unsupported modes. **Do not assume GameMaker fullscreen/resize API behavior from legacy menus alone.** Keep existing audio/buttons settings unchanged unless Chief separately requests UI for them.

**Acceptance:** one accessible shared settings entry, coherent Windowed/Fullscreen and Auto/Wide/Retro/size choices, preserved settings across restart, no incorrect aspect/camera stretch, gamepad/keyboard navigation, safe display restoration on Pause/title/Continue and Classic/Enhanced parity. One combined endgame candidate/test, not separate builds per option.

## RF-002 — Hide developer Pause → Level Select in release
**Status: PARKED — Chief endgame release cleanup.**

Current inherited `OBJ_pause/Step_0.gml` has three entries (Resume / Level Select / Back to Title), and `OBJ_pause/Draw_0.gml` visibly renders Level Select. The developer route calls `chaos_debug_open()` and can become release-facing. **Chief wants this removed or hidden in a release build**; retain a developer-only testing path only if explicitly authorized and impossible to access by ordinary end users. Do not silently remove the original tag's behaviour. Rework menu positions/navigation/focus carefully, preserve Pause/resume, title return, existing audio/instance reactivation and both modes. Consider the S1 Enhanced presenter keepalive before altering Pause menus. Test keyboard/controller input and no phantom third row after hiding.

## RF-003 — Pause restriction at results/transition boundaries
**Status: PARKED — previously recorded Chief final polish, not a current assignment.**

Once the release display menus are being polished, forbid Pause in the specific results/transition intervals Chief previously identified, but only after precise state/ROM vs PC-policy proof and bounded regression. No global Pause overhaul or timing changes. Preserve results/death/Continue/native audio and S1 display presenter lifecycle.

## Operating rules
- Not part of S1, E1, GPU/VSync pacing, native renderer integration, GPZ3 map seam repair or Enhanced ring scatter.
- During sprint development record relevant interactions if discovered, **but don't expand work or add new UI**.
- At the final polish planning gate, Manager may group RF-001/002/003 into **one bounded release-comfort sprint**, single native integration candidate and Chief check.
- Current state: **PARKED / DOCUMENTED — NO IMPLEMENTATION AUTHORIZED**.

# Sonic Chaos — E0 Unified Classic / Enhanced Frontend: Research Brief
**5 November 2026 · Chief first post-freeze job · research/design only, no code or build authorized**

## Goal and authoritative baseline
Chief: create **one Windows build** with startup SEGA splash, a **binary Classic / Enhanced mode picker**, the same original Sonic Chaos game in both modes initially, and a real user-facing Enhanced **Options** page below the Enhanced choice; future features appear there as On/Off controls. Technical options like 60 FPS presentation and appropriate scaling may eventually become Enhanced defaults when proved safe, not necessarily user-visible switches. No resurrected developer shortcut toggles, extra parallel EXEs or variant-specific gameplay copies.

Classic core is immutable, annotated private tag `classic-core-20261105`, peeled commit `3a58912659b48573ac7f2c5c96a02a2211d5e4da`. Frozen Windows/source ZIP identities remain as recorded in Classic freeze ledger; E0 is a *successor shell*, not a mutation of the frozen baseline. Classic remains behaviourally equivalent **after the shared launcher**, although a new boot splash/picker necessarily changes its startup compared with the byte-identical frozen binary. Do not claim that the newer executable is hash-identical to the Classic ZIP.

## Verified frontend source research (read-only, accepted D branch)
1. Existing room order begins `ROM_system_start` → `ROM_menu_opening_cinematic` → `ROM_menu_opening` (registered legacy, currently skipped) → `ROM_menu_title`. `OBJ_system_start/Create_0.gml` creates `OBJ_system`, applies `SCR_screen()`, sets `alarm[1]=15`; `Alarm_1.gml` calls `room_goto_next()`. Reorder a future isolated shell room *after* system start and *before* original cinematic; preserve the original startup owner and canonical cinematic.
2. `docs/opening1-package-a.md` and `docs/opening1-preflight.md` establish via original-ROM research that **Sonic Chaos SMS Europe v1.2 has NO standalone SEGA logo splash**. Actual startup is black → Sonic/Robotnik/Tails original cinematic → title. The inherited OpenSonicSMS `ROM_menu_opening` / `OBJ_menu_opening` / `SPR_opening_sega` (51-frame sprite) remain in project, intentionally disconnected. Do **not** label them 'from ROM' or treat a new splash as authentic retail behavior.
3. Logo art research options: (A) inspect whether ROM-derived original *title* artwork has an appropriate SEGA mark that can be reproduced standalone using authenticated palette/tile sources; (B) if not, reuse the registered inherited `SPR_opening_sega` explicitly as a PC-only splash, with correct asset provenance. Record source and visual sample; Chief to choose after research. No invented ROM splash timing. Keep private copyrighted art/ROM out of public management repo.
4. `OBJ_menu_opening_cinematic/Create_0.gml` calls `SCR_screen`, sets 60-Hz scene clock, and `chaos_audio_scene("opening",$90)`. Its Step owner uses existing original animation/skip and explicitly goes to `ROM_menu_title`. `OBJ_menu_title` likewise owns original title scene, start transition to `ROM_chaos_choice`, and opening return for idle no-attract. These scenes and 60-Hz clocks must stay untouched by E0; no doubled driver or new autoplay audio.
5. Existing `OBJ_system/Create_0.gml` loads `settings.ini`, guarded by `chaosRunInitialized`; globals include `screenSize`, `windowSize`, `buttons`, `music`, and *legacy* `saveGame`, which is not the future Sonic 3 progression system. Never overload player, emerald or campaign globals with mode/feature flags. The title recreates `OBJ_system` and uses its startup initialization guard.
6. Reuse existing `SCR_buttons()` mappings and GameMaker view/Draw conventions. Original title/character select/Level Select, Sound Test, pause, Sonic/Tails campaigns, audio clock, and game-over/Continue/title return must remain unchanged. Audit pending audio startup delay by observation only; don't add arbitrary splash hold time to mask it.

## Preferred mode flow (proposal for owner sign-off)
```text
Power on → existing system initialization
        → NEW SEGA-branded PC-only splash (short/skip-safe)
        → NEW CHOOSE MODE (two modes: Classic | Enhanced; Classic selected by default)
                  ├─ Classic → original cinematic → original title → existing character choice / game
                  └─ Enhanced → original cinematic → original title → existing character choice / game
                       (Enhanced's separate OPTIONS subaction accessible beneath mode choice
                        before launch; return to mode choice without initializing a campaign)
```
**Options is a subaction for Enhanced, not a third mode.** This keeps the original game/title unmodified in both modes. Chief may refine exact screen layout after Designer presents source-backed mock/states. The launcher appears on application startup, **not** after ordinary death/Continue, title return, or original cinematic timeout. Define explicit switch-mode flow only from a safe frontend, not during active gameplay.

## Feature contract / empty Options
- Runtime mode value is one explicit enum/string (`classic`, `enhanced`) initialized once at launcher acceptance, separated from existing gameplay/player selection. No per-feature F-key globals.
- Both branches launch the same existing ROM-authentic runtime. **No Enhanced gameplay changes in E0.** `classic` fixes effective feature flags to off; future Enhanced feature registry holds stable IDs, defaults, availability, user-setting persistence, app-version migration and a single explicit point of application outside protected core whenever feasible.
- At E0 there are **zero implemented enhancements**: Enhanced Options should show an honest placeholder such as 'No additional features installed' rather than fake toggles. Avoid claiming 60 FPS, scaling or CRT are already present.
- When G1 60 FPS and G2 pixel scaling become proven safe, Chief may elect to make them Enhanced default/on without dedicated toggles; retain a controlled compatibility/fallback route where needed for performance. Optional features (CRT, alternate palettes, QoL, saving, boss rush etc.) get true On/Off when they exist. Some *modes* such as Save Game and Boss Rush may warrant separate menu entries rather than simple binary toggles; don't force inappropriate UI semantics.
- A shared durable settings schema should distinguish **per-session mode**, **Enhanced feature preferences**, and existing `settings.ini` display/input preferences; decide whether mode selection itself persists only after deliberate approval. Proposed default is Classic on each fresh boot for safety and clarity.
- Keep a clean user-facing visual style matching original game resolution/pixel rules. Support both 256×192 and 348×196, window/fullscreen, keyboard+gamepad, navigation/cancel/confirm and mode-specific Options without edits to the ROM title art.

## Research-first gate — required before implementation approval
Designer-san must inspect source and produce (1) exact entry/exit state & room transition diagram for cold boot / skip / mode pick / Options cancel / game over / title timeout / reset; (2) visual/logo art provenance and recommended static/animated timing with example screens, making no false 'ROM splash' claim; (3) minimal proposed isolated GML/room/resource change list and `SCR_buttons`/`OBJ_system` persistence plan; (4) mode flag/single registry schema with Classic fallback and Enhanced empty option behavior; (5) startup audio/lifecycle risks and test plan for 256/348, Sonic/Tails, both modes and unchanged frozen code; (6) branch/freeze preservation and source-only risk audit.

**Stop after documentation; no branch implementation, build, GameMaker export, new ROM art extraction or release package now.** Submit a decision-ready specification to Manager and Chief. After Chief approves art and flow, a single isolated E0 implementation branch/candidate can be commissioned with small, focused compiled Windows checks. Do not rerun whole campaigns or expand into 60 FPS/CRT implementation under E0.

## Known questions the brief should resolve without assuming
- Whether a suitable authentic SEGA mark exists within the actual retail title art; if not, present the existing inherited splash honestly as the PC adaptation.
- Whether Classic/Enhanced selection should always appear at cold boot vs remember last mode; current proposal selects Classic each startup.
- Where Enhanced Options sits (recommended subaction below mode picker), and whether mode selection can be changed from the title only with a safe non-gameplay transition.
- Visual effects/audio for the short new splash and mode UI must not delay, double-play or steal the original cinematic `$90` audio and title `$99` / choice `$82`.
- Confirm game speed distinctions: project base 30, cinematic/title/choice set 60; this **does not** mean the future 60 FPS gameplay-enhancement is already solved.

## Next sequence
1. Research E0 with the accepted frozen source untouched.
2. Chief/Manager approve precise splash provenance and mock/frontend flow.
3. Separate E0 shell-only implementation and small mode-equivalence verification, preserving frozen tag and archive.
4. Only then begin 60 FPS rendering, scaling/CRT and other enhancements, using this single unified options framework.

# Sonic Chaos — S4 Enhanced 1080p Presentation: Chief Design Direction
**6 November 2026 · Manager-san #11 · DISPLAY DIRECTION CHIEF CONFIRMED / IMPLEMENTATION NOT YET COMMISSIONED**

## 1. Chief's decision — THIS IS BINDING FOR FUTURE DESIGN

## IMPLEMENTATION DECISION — S4 GO 6 NOVEMBER 2026

Chief requested "next job" after confirming the architecture and the three new bugs. Manager #11 authorized **one integrated S4 1080p Enhanced display foundation plus camera/HUD/title corrections**, keeping full Data Select visual-art polish for later S5. **[Binding S4 sprint / current instructions](S4_ENHANCED_1080P_FOUNDATION_SPRINT_20261106.md).** Former "discussion only" language below is historical and superseded. No Designer implementation results or Chief S4 acceptance yet.



## New related Chief issues — OPEN, NOT AN S4 IMPLEMENTATION ORDER

Chief reported three residual post-S3 bugs after final Boss Rush acceptance: MGHZ→AQZ camera snap (P1, potentially but not proven linked to handoff/camera restoration), lives HUD inconsistently hidden in SEZ/SLZ and MGHZ Boss Rush (P2), and early START skipping the visible Enhanced title START/BOSS RUSH choices (P2). [Binding issue register](tracking/S3_POST_ACCEPTANCE_PUNCHLIST_20261106.md). The title issue may naturally fit future high-res frontend work, and the HUD issue may fit Enhanced composition, **but the camera warp is a separate functional/presentation seam requiring its own evidence-led trace**, not a generic scaling change. **Do not assert any of these fixed by higher output resolution; no S4 implementation or new S3 fix has yet been authorized.**



Chief wants Enhanced mode built around a **1920×1080 (Full HD) presentation canvas** rather than squeezing 16-bit-inspired Data Select/title/results composition into GameMaker's tiny low-resolution view and multiplying it to a 3x window. The main reason is to give Enhanced-only *presentation elements* more room and more detail, while **never altering Sonic Chaos game-world assets**.

Chief explicitly confirms:
- **Preserve original gameplay artwork** (Sonic/Tails, enemies, stages, tiles, projectiles, animation, sprite dimensions, authentic collisions and scrolling) and retain original native-game logic/view.
- **Integer Fit is ON by default in Enhanced**, to maximise actual displayed game area while keeping even pixels and undistorted proportions. Other sampling/scaling may remain selectable as options, but do not silently turn on interpolation by default.
- **Enhanced title, Data Select, Boss Rush results, options and suitable UI/CRT effects** may be authored/layouted independently at true high-res output, with a tastefully pixel-art/8-bit-compatible style, not an HD-remake gameplay aesthetic. A 1920×1080 output surface does NOT magically add details to sprites rasterised at 348×196; the new UI must be drawn in the higher-res pass, not inside that low-res application_surface.
- **Classic must remain as it is, using its original GameMaker logical screen/window 1x/2x/3x behaviour**, including its existing interpolation policy and visual/gameplay/audio timing. Do not allow Enhanced display defaults/settings to leak into Classic.
- Fullscreen, borderless and bordered window controls are desirable with persistent preferences. Correct configuration suffix is **`.ini` (GameMaker application configuration), not Windows `.inf` (driver setup information)**. Let users choose in game; never require manually editing text or placing a load-bearing TXT in the package. Window-size defaults must handle non-1080 monitors and taskbar work areas safely.
- **S3 is Chief accepted / closed**; the private feature branch `enhancement/s3-r2-visual-audio-results-20261106` exists at full SHA `29044caac612a0d2a23399e9fb7a58abda387740`, tracked tree `69ef6d22e3fdd19c1351c612c752e81fc0c61362`. Four ignored runtime files are in independently verified private E:/H: full-source archives but outside Git: preserve these and ensure correct runtime reconstruction before editing. No further S3 builds or refactors without separate authorization.

**This conversation is architecture and acceptance-criteria agreement; Chief has NOT yet commissioned the Codex S4 implementation sprint.** We must discuss final options/scope first.

## 2. Actual accepted private source architecture inspected by Manager

Source: private `jamesfarnhamlong/SonicChaos_POC` at above R2 branch.
- `scripts/SCR_screen/SCR_screen.gml`: logical Wide **348×196**, Retro **290×218**, Auto; legacy `window_set_size(screenWidth*global.windowSize,screenHeight*global.windowSize)`, `surface_resize(application_surface,...)`, view and viewport size assignments; guarded early call `chaos_display_configure(...)`.
- `scripts/SCR_chaos_display/SCR_chaos_display.gml`: S1 Enhanced-only manual Post Draw presenter already implemented. **Integer Fit** resizes the application surface to **native logical** Width×Height, applies nearest-neighbour copy using integer factor `floor(min(outputW/nativeW,outputH/nativeH))`, and preserves original **1x–3x window**. Fallback and presenter's keepalive protect Pause/death/results and surface-loss cases. **Extend this accepted owner rather than introducing a second competing application-surface renderer.**
- `options/windows/options_windows.yy`: `option_windows_allow_fullscreen_switching:false`, `option_windows_resize_window:false`, `option_windows_borderless:false`, `option_windows_start_fullscreen:false`, `option_windows_interpolate_pixels:true`, VSYNC true. Window/fullscreen modes are currently not switched by S1; implementation requires explicit Windows GameMaker app/host policy and tests, not merely a menu toggle.
- S1 Sharp Pixels / Integer Fit / lightweight CRT are already Chief accepted but originally default OFF. **New Chief preference supersedes the old Enhanced Integer Fit OFF default once the new S4 output is implemented and verified**; it does not automatically force Sharp Pixels or CRT ON. Classic defaults unchanged.
- Original 348/196=1.7755102 is *nearly*, not precisely, 16:9=1.7777778; maintain exact original game image, with centred fit/letterbox rather than stretching to the screen's aspect.

## 3. Required mathematical contract

At a 1920×1080 output, authentic Enhanced Wide gameplay remains **348×196 logical pixels**. Nearest-neighbour **5x** native integer fit gives **1740×980**, centered at **(90,50)**. The remaining margins: **90 physical px each side and 50 top/bottom**. Native-game image fills **(1740*980)/(1920*1080)=82.25% of physical display area**, or ~90.6% of each dimension. Do not claim 100% fill or take more world into view to fake it.

High-res output/UI can use all available **1920×1080** independently. Decorate otherwise empty margins with subtle, compatible Enhanced-only backdrop/letterboxing, if desired, rather than stretch game/world art or violate integer fit. Native game camera/HUD/collision remain unchanged; avoid drawing gameplay HUD into a double-scaled low-resolution+GUI path.

For 256×192 canonical native gameplay / 290×218 Retro / Auto use the same principled integer-fit math with correct aspect and fallback; never force all old modes to the Wide348 camera or crop gameplay. Higher host resolutions (e.g. 2560×1440 and 3840×2160) should use `floor(min(W/w,H/h))` and centre; arbitrary windowed sizes should fit and show clear fallback rather than clip. Maintain 60-update simulation and native audio.

## 4. Proposed compositor architecture — not yet a Codex work order

**Game-world layer:** render at existing logical pixel grid with unmodified player/terrain/boss/world art, physics, camera and culling. Pass through the accepted S1 integer-fit/native-surface presenter, extended to dynamic large output targets; keep noninteger sampling/CRT as reversible options after correctness.

**Enhanced presentation/GUI layer:** use a separate high-res output-space composition/GUI pass (or an equivalent isolated GameMaker high-res UI surface) for Enhanced-only intro/title, Data Select, pause/options and Boss Rush CLEAR. UI can use higher-res fonts, TV frames, jewels, curated thumbnail layout, animated running previews and restrained CRT effects without altering original sprite data. Align overlays to output spaces at 1080p and render at appropriate scales for other displays. Prevent Enhanced UI from being rasterised first at the native 348px app-surface and then simply multiplied: that would NOT solve the 'crunchy' UI complaint.

**Host/window policy:** selectable windowed/bordered, borderless desktop fullscreen and/or supported ordinary fullscreen, with proper Windows DPI work area, focus/resume, Alt+Enter only if deliberately approved; persist validated settings in isolated GameMaker user `.ini`, separate from S2 campaign saves. No manual configuration-file editing required. Desktop 1920×1080 is a **target**, not mandatory default window size if the display/work area cannot accommodate it. Provide safe start/fallback and one-click recovery.

**Pixel/CRT:** Integer Fit ON by default for Enhanced in the new configuration; preserve separate Sharp Pixels/CRT choices and defer major new CRT design until the higher-resolution output is verified. Decide CRT ordering deliberately: native game-only CRT vs whole GUI overlay, with readable text and no smearing of high-res Enhanced UI; no unapproved upscale/art replacement.

**Asset quality:** High-res UI gives more **space** for layout, but tiny zone thumbnails will remain low-detail unless reframed/redrawn or displayed bigger. Preserve native-looking original characters; enhanced-only UI assets may be newly authored to suitable pixel-art resolutions/texture sizes without replacing game-world source sprites. Design retro-compatible, not indiscriminate vector/HD remake.

## 5. Architecturally sensitive verification and go/no-go gates
- Actual native GameMaker Windowed, borderless/fullscreen, resizing/focus/minimize and high-DPI behavior; verify what runtime and installed GM version allow before promising settings. Test 1080p + other smaller/larger monitors and no display capture black-frame failure.
- **Strict Classic parity** at 1x/2x/3x: same original screen size, application_surface/render path, camera, resource draw ordering, menu/campaign state/audio and settings isolation, with actual Windows screenshots and relevant state snapshots.
- **Enhanced gameplay parity** at 348 Wide and 290 Retro plus 256 canonical: preserve game-world visible extents, collision, camera triggers, original S3 six-boss and normal campaign state, native music/PCM request ordering, intact S2 save state. Compare screenshots for intentional *screen scaling* changes vs unchanged native source pixels.
- Presenter scene lifecycle at title/options, S2 Data Select, special stage, Pause, death/Continue/results, Boss Rush CLEAR, screen mode switching, S1 Sharp/Integer/CRT toggles, surface loss, minimize/restore. Tested fallback to safe old low-res original presentation if any high-res layer fails.
- High-res UI should be measured by **actual visible 1920×1080 screenshot** and 1:1 crop: demonstrate text, cards, artwork clarity and true hi-res draw rather than simply multiplying the old low-res canvas.
- After Chief authorizes scope, one cohesive substantial Designer sprint, one private Windows/source/test/receipt package and one integrated Chief visual/controls/playcheck; no repeated tiny builds.

## 6. Decisions still for Chief/Manager discussion BEFORE implementation
- Whether to put the 1080p high-res UI framework **and** the complete six-item Data Select visual redesign in the *same* S4 sprint, or first finish the display/window architecture and follow with one distinct S5 UI/art sprint. Manager recommends **foundation first** if UI integration becomes high-risk, because Data Select art should target a stable 1080p space.
- Which window presentation choices to expose first: bordered window + borderless desktop are core; exclusive fullscreen may be unnecessary/unsupported. Specify normal startup windowed size and enhanced/fullscreen default (fullscreen itself not automatically authorised).
- UI CRT policy: game-only by default vs full UI, plus whether lightweight scanlines need stronger upgrade after 1080p. No automatic new multi-pass CRT or Sharp default.
- Responsive layout targets for smaller windows/16:10/21:9, without losing authentic 16:9 gameplay or fitting low-resolution art as a stretched background.

**Current management decision: S4 DESIGN CONFIRMED / DESIGNER IMPLEMENTATION GO via binding [S4 charter](S4_ENHANCED_1080P_FOUNDATION_SPRINT_20261106.md); no candidate or Chief S4 acceptance yet.**

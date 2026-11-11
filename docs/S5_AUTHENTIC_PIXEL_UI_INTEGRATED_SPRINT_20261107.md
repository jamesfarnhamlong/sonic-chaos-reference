# SONIC CHAOS — S5 Authentic Pixel-UI Presentation
**7 November 2026 · Manager-san #11 · NEXT INTEGRATED DESIGNER JOB AUTHORIZED · CHIEF ACCEPTANCE PENDING**

## INTEGRATED IMPLEMENTATION COMPLETE — 11 NOV 2026 (CHIEF ACCEPTANCE PENDING)

**Designer reports all six S5 screens implemented in one private candidate**, local `enhancement/s5-authentic-pixel-ui-20261111` source commit `11cefcece3c43e33db8a2f5967347c444b5a8fb4`; original S4 parent `977a41824f227f3bdfe6f45596e6845902459842`. Chosen UI design 480×270@4× FullHD, native game Wide348×196 independent 5×, intentionally detailed original 144×128 TV stage previews output at 2×. Chief watched progress, refinements centred previews and correct GPZ pipe crop / Level7 card incorporated. Designer reports 35 native checks, 14 Windows host configurations, 8 exact Classic+8 exact Enhanced app-raster matches, private full source and E:/H: recovery. S5 is **TECHNICAL DELIVERY / MANAGER GO FOR ONE CHIEF Windows/physical pad acceptance**, not final Chief PASS. [Manager technical review and focused Chief check](S5_INTEGRATED_DELIVERY_MANAGER_REVIEW_20261111.md). Prior implementation orders below are historical. Do not issue another Designer build before owner results or push/merge/tag/release automatically.


Chief asked "OK! Sorry, we've been doing back and forth a bit — what's the next stage/job then?" after agreeing that source-image smoothing was not solving the UI mismatch. **S5 is now the next commissioned integrated design/implementation sprint.** No more broad conceptual reconsideration or multi-build owner calibration before delivering a meaningful candidate. Treat this document as the single latest binding S5 instruction; previous S5 "discussion only" statuses and upscale-algorithm-first directions are superseded.

**Deliverable:** Authentic Sonic Chaos-style original-art presentation for **six Enhanced-only screens**:
1. Title screen.
2. Save/Data Select screens (existing S2 five-slot functionality).
3. Zone introduction/title card.
4. Zone end/results/bonus presentation.
5. Boss Rush introduction (including Level 7 entry).
6. Boss Rush end/clear (TIME, RINGS, LIVES).

All should be recognizably one game, with original pixel typography, authentic ROM/GameMaker-source sprites and palette, **not** S4 high-res white sans-serif/navy dashboard/opaque overlays. Save source artwork/gameplay; rethink *composition, placement, alignment, size and efficient communication*.

## Source identity, baseline and safety
- Accepted S4 Enhanced display/window/render foundation local private branch `enhancement/s4-1080p-foundation-20261106`, exact Designer-reported source commit `977a41824f227f3bdfe6f45596e6845902459842`. Designer's complete S4 source/evidence/Windows/receipt and independent H: recovery under E:/H:; **do not assume S4 branch has been pushed to GitHub**, last Manager remote lookup found it absent.
- Frozen Classic core tag `classic-core-20261105` → `3a58912659b48573ac7f2c5c96a02a2211d5e4da` and accepted private S3-R2 (GG `$9B`, S3 cameras/music/clear) `29044caac612a0d2a23399e9fb7a58abda387740` unchanged.
- **22 ignored source dependencies**: four runtime files plus eighteen original sprite PNGs included in validated S4 E:/H: complete source but not guaranteed to be in tracked Git tree. Reconstruct actual source from full protected archive before building; inventory/check hash and don't silently commit private ROM art or invent a Git-complete claim.
- Create isolated S5 local feature branch from exact Chief-accepted S4; do not modify S4 accepted ZIP/source/branch, S3, Classic, `main`, labels/tags or private/public repo visibility. Keep no new copyrighted/fan art in public reference. One final private candidate and one Chief F5 test; no per-screen owner microbuild.

## Composition experiment (Designer internal, not 2 competing shipped UIs)
**Compare these two FULL-HD 16:9 logical UI grids using the same original assets on actual title and five-card Data Select screens:**
- **384×216 → integer 5× → 1920×1080**. Matches established clean five-pixel output but slightly less flexible for five cards.
- **480×270 → integer 4× → 1920×1080**. Manager's starting preference for five-card readability/spacing, finer-yet-pixel-perfect interface.
Choose **one** by objective pixel alignment, consistent fonts/character sprite sizing, effective composition, legibility and original-game aesthetic; document reasons and actual 1:1 screenshots. Output canvas is exactly 16:9 either way. **S4 gameplay remains its separate logical 348×196 Wide view**, normally 5× (1740×980 centered 90px sides / 50px top/bottom); do **not** change world visibility, original player sprites or HUD math. The title source art is authentic **256×192**, not secretly 16:9; preserve its geometry without stretch or invented pixel detail.

**Do not enforce 5× on the logical UI if it leaves the five cards cramped**. Chief's priority is clean, consistent integer pixel geometry and extra composition space, not a numerical ritual. Separate gameplay fit vs presentation logical grid correctly; preserve Integer Fit ON/OFF toggling.

Aseprite **Bilinear and Rotpixels were explicitly rejected** by Chief. Nearest integer scaling is the baseline. HQx/xBRZ can be compared on a few static source art crops only if cheap and likely useful; neither is a dependency, and never apply smoothing to *all* game-world art. Never do a fractional 2.5× rescale as a hidden second processing pass. Sharp Pixels/CRT S1 options remain independently functional.

## Six screens — requirements
**Title**
- Preserve authentic Sonic/Tails and logo artwork, original authentic background/palette/timing/sound and original **START GAME** lettering; put **BOSS RUSH** naturally near/below with same native pixel-font character, appropriate selection pointer. Avoid masking/hiding original title text using any large dark or generic modern panel. Handle any embedded original START text carefully (source frames/palette), no double labels. Keep S4 early-START protection: the menu must be visibly selectable before confirmation; preserve normal Enhanced START→Data Select and BOSS RUSH→character selection/Level7.
- Authentic original `SPR_chaos_m3_title` contains 41 indexed **256×192** ROM-authentic frames; final frame40 `26b1402f-e13e-58c8-ae7f-a0cbc55cd54a.png` with palette index3 `SCR_chaos_title_data.gml` through `SHD_chaos_title.fsh`. `SPR_chaos_title_tiles` is 128×48; `SPR_title` 114×65 is old/legacy, **not** full title. Never upscale raw packed indexed title PNG as though RGB; apply original palette before experiments.

**Save/Data Select**
- Chief prefers the **original S2 Sonic3-inspired TV card composition** to the modern S4 dashboard, but wanted more logical layout space. Preserve all five save slot data (character locked after first write, resumes, zone flag, seven? emerald count according to original save semantics—**do not change schema or assume unverified cardinality**), selection, wipe confirmation, slot navigation and empty-slot behaviour. Clear highlight, TV preview/static, recognisable original running Sonic/Tails, correct Tails cropped/yellow-head palette, source zone thumbnails, attractive existing Emerald gems, zone/character/emerald cues. Reduce repeated SLOT/NEW GAME/SELECT CHARACTER/CONTINUE copy and multi-line bottom instructions; show concise contextual prompt only where necessary. Do not hide destructive wipe confirmation.

**Zone Introduction**
- Recompose existing authentic act/zone splash on new UI pixel canvas, respecting sound, exact sequence/duration and original letters/number graphics. No physics/camera draw changes, no filler modern art or unapproved new transitions.

**Zone End**
- Keep original Zone Clear, Ring Bonus (100×rings max 9900) and Speed Bonus (speed×10 max 9990) order, rolling km/h native $19, timer/result logic, sounds/animation. Improve framing only. **No score calculation or gameplay redesign**.

**Boss Rush Introduction**
- Reuse existing challenge Sonic/Tails selection and single LEVEL 7 card, keep progression/camera and native audio $9B behaviour; style/present consistently with Title and other zone cards. No new game mode or different mechanics.

**Boss Rush End**
- Preserve exact frozen end **TIME / RINGS / LIVES**, restart/title controls and original completion state; create compact original-game-style result art and font, without large S4 dark rectangle and plain white sans-serif. No new score/leaderboard/save writes.

## Fidelity and implementation constraints
- **Classic never touches S5**: original 1×–3× window, 256×192 ROM look, scripts/menus/flow and audio timing continue bit/pixel-identical where applicable.
- **No new character/zone art**: original art assets and source sprites, original-styled pixel font/glyphs, original palette only or clearly existing approved game colours. No AI-generated/vector/HD assets, stock UI, unrelated Sonic fanart, modern overlays, retouched gameplay graphics, or fan project copying. UI frames may be composed from original tiles/linework for needed labels and borders; avoid gratuitous invented new graphic designs.
- Preserve accepted S4 fullscreen, borderless/windowed, resizing/persisted .ini, 1080p presenter, app-surface lifecycle, DPI/focus/minimize recovery and Integer Fit ON/OFF; no second competing display engine and no re-render native gameplay at UI grid.
- S1 Sharp/CRT toggles, S2 native saves/emerald persistence and S3 Boss Rush all six battles/GG $9B/clear statistics remain in scope for minimal regression. Preserve audio driver and original art.
- Any GameMaker runtime or asset-processing utility used for offline derivation must be reproducible, output correctly alpha-composited & palette-clean source, and licensed appropriately. No derivative file size explosion or loading external TXT/PNG as extra runtime prerequisites unless existing GameMaker conventions require it.

## Developer verification
- Determine chosen 16:9 UI grid by actual **1920×1080 1:1 native screen captures** on both candidate Title/Data Select compositions; record source dimensions and final factor. No need Chief to vote on half-implemented options unless genuinely blocked.
- One integrated Windows smoke for all six presentation surfaces with capture, UI text/focus/help legibility at windowed and borderless and Integer ON/OFF. Include controller selection, early START, new/load/erase save flows, 100 ring and progression/emerald display check, Zone Intro and final clear timing/bonus numbers, Boss Rush Level7 entry/final stats, short ordinary gameplay and representative Boss Rush join (not unnecessary full dual-character campaigns).
- Original world source sprite, camera/physics, Classic parity, sound/PSG and save JSON bytes must be unchanged as demonstrated by targeted comparisons with accepted S4. Respect inherited test FAIL records; don't report unrun natural routes as PASS.
- One private Windows candidate ZIP and full source ZIP, before/after screenshots, selected grid decision, assets/changed-file list and resource provenance, exact branch/commit/tree, hashes/receipt and H: independent restore. Manager GO for Chief acceptance only after tests. Never auto-push private branch or merge/tag/release.

## Handover
- S4 CHIEF FUNCTIONALLY ACCEPTED, but temporary hi-res menu art NOT final.
- S5 now **DESIGNER IMPLEMENTATION GO** for six authentic-pixel presentation screens as single integrated sprint. User controls final aesthetic/functional acceptance.
- Later optional screen shader/filter research is **separate**, not a prerequisite for shipping a cohesive original-art S5 UI.

# Sonic Chaos — S5 UI composition pivot and external fan-project references
**7 November 2026 · Manager-san #11 · CHIEF ART-DIRECTION REVISION · NO S5 PRODUCTION GO**

## Executive decision

## IMPLEMENTATION STATUS UPDATE — 7 NOV: ONE S5 SPRINT AUTHORISED

## 11 NOV — SOURCE IMPLEMENTED, CHIEF FINAL ACCEPTANCE STILL PENDING

Designer delivered single integrated S5 candidate `SonicChaos_Windows_20261111_S5_PIXEL_UI_CANDIDATE_PRIVATE.zip` from local commit `11cefcece3c43e33db8a2f5967347c444b5a8fb4`; **480×270@4×** chosen after actual 384×216@5× comparison. Original zone-TV maps cropped and detailed, GPZ pipe/blue bridge selected, pictures centred with equal black spacing, Boss Rush Level7 uses native zone-card family. No automatic HQx/xBRZ/HD assets. [Manager review and Chief next test](S5_INTEGRATED_DELIVERY_MANAGER_REVIEW_20261111.md). The historical no-implementation-GO direction below has been superseded; Chief physical Windows acceptance is still required.



Chief subsequently asked for the **next job** and Manager #11 authorised one **six-screen authentic native-pixel UI implementation sprint**. [Binding S5 charter](S5_AUTHENTIC_PIXEL_UI_INTEGRATED_SPRINT_20261107.md) supersedes 'no production GO' statements below. Designer will compare 384×216 5× vs 480×270 4× internally on original Title/Data Select, choose one coherent layout, then ship all six coordinated screens in one private Windows candidate. No S5 implementation or Chief acceptance yet.


Chief has exported the authentic ROM title artwork from `SPR_chaos_m3_title` and experimented in Aseprite. **Bilinear and Rotpixels looked terrible**. HQx/xBRZ remain possible exploratory comparisons, but **pixel resampling is NOT the success criterion**. The real problem is that the new S4 1080p high-res UI looks unrelated to Sonic Chaos, whereas the earlier S2 Sonic 3-inspired save screen felt coherent but was cramped by its original low-res layout.

**Design priority for S5:** Preserve authentic art and pixel font, arrange existing title/save/results content in a larger **logical pixel-art UI design canvas**, and upscale the completed composed presentation by a clean integer factor into accepted S4 1920x1080 output. Preserve original full-HD host compositor and native game-world camera/sprites, avoiding new character/HD artwork, modern sans-serif panels, screen-covering overlays, generic vector style or excessive instructions.

## Candidate UI grids — design proposal only
- **480 x 270** logical, **4x** exact nearest to **1920 x 1080**, aspect **16:9**: Manager's first recommended composition trial, provides more UI space and fine-but-still-obvious pixel geometry.
- **384 x 216** logical, **5x** exact nearest to **1920 x 1080**, aspect **16:9**: consistent with preferred 5x integer pixel grid but less design area.
- **320 x 180** logical, **6x** exact: chunky, less content space. Chief gave **320 x 240** as an example of how a larger logical UI could work, not a mandated 16:9 resolution; 320x240 is **4:3**.
- **Gameplay stays 348 x 196 Wide**, integer 5x gives **1740 x 980** in 1080p with 90px side/50px top-bottom gaps, as already Chief accepted. The title source itself is **256 x 192** original 4:3 art. UI may be a different logical grid than world; do not stretch gameplay or change camera visibility to force grid equivalence.
- Integer Fit ON and OFF are both Chief-accepted choices. Default ON remains S4 policy; do not disable OFF.

## Concrete Chief presentation preference
- Original title **START GAME** must remain part of coherent title artwork; integrate **BOSS RUSH** directly underneath it in the **original source pixel font / matching source-style lettering**, not an unrelated clean sans-serif block. Avoid both duplicate original START GAME and a new overlay covering it.
- Retain **S2's original style/concept for five Data Select cards** as stronger than the new S4 clean dashboard; implement at a larger logical UI canvas so original animated character poses, TV thumbnails, Emerald progression and selection are spacious but compact and visually legible. Minimize repeated text and unnecessary instructions; retain navigation/saves/erase exactly.
- Zone Introduction, Zone End, Boss Rush Introduction and Boss Rush End also get source-style typographic/pixel-art layout reflow to the same general visual language. Preserve timing, score calculations, sound and original artwork.
- Default to **nearest-neighbour integer upscaling of composed source-graphic/UI frame**, appropriate optional scanlines or existing CRT and Sharp Pixels choices. If HQx/xBRZ improves a particular isolated graphic without damaging original pixel identity, make it opt-in or chosen per-asset only, never mandatory global art transformation. **No invented/reconstructed original detail**.
- High-res UI architecture S4 acceptance is intact; do not replace it with a new competing compositor.

## External fan-project inspiration (private visual reference ONLY, no asset copying)
1. **Sonic Chaos — Turquoise Hill Demo**: https://sonicfangameshq.com/forums/showcase/sonic-chaos-turquoise-hill-demo.228/ . SFGHQ lists **August 19, 2018** creation and **August 29, 2018** update. It is a separate Crimson Engine Sonic Mania-inspired 16-bit reinterpretation, useful for compositional ideas, NOT a model for preserving original ROM visuals.
2. **Sonic and Tails PC/Android**: https://gamejolt.com/games/sonicandtailsportpcandandroid/843684 . Chief has tried it and observed a Windows port with persistent on-screen Android controls/crashes and interesting apparent widescreen UI/save/extras layouts. **Not independently verified** beyond Chief's observations because Game Jolt page was not readable with available fetch; do not overclaim release state or assets.
3. **Game Gear/Master System Chaos**: https://gamebanana.com/wips/49244 . Work-in-progress *mod* by Im_Percynator. Search-visible GameBanana summary has version0.1–0.3 updates approximately **8 years ago** (2018), v0.4–0.5 approximately **6 years ago** (2020), an author statement placing the project **on hold**, and **45% completion**. Not demonstrated permanently abandoned. Mod edit scope includes **title screen, menu, HUD, logo, life/ring icons, signpost, boss/character sprites**; art/layout is potential *inspiration* for our small UI retrofits, never a source to import protected art. A contemporary comment suggested **nearest-neighbour** instead of bad resized graphics—reinforces Chef's Bilinear/Rotpixels critique. No copied third-party resources.
   
## Follow-up status
**No production S5 implementation, source change or new Designer build authorized by discovering references.** If Chief greenlights S5, first prove one conservative **source-art 480x270 vs 384x216 composition** of title and Data Select at actual 1920x1080, not dozens of algorithm microbuilds; select grid and style, then apply consistent design across the six presentation scenes as a single meaningful sprint. Preserve accepted S4 local SHA `977a41824f227f3bdfe6f45596e6845902459842`, source/E:/H: archives and ignored assets. Original Classic, S2 saves, S3 Boss Rush, game-world drawing/sound/camera all protected.

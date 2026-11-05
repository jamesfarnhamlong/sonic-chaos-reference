# Sonic Chaos — E2-P1 Sharp Pixels: Manager Visual Evidence Review
**5 November 2026 · Manager-san #10 · STATIC VISUAL PASS (scoped), Chief's real Windows A/B acceptance PENDING**

## Evidence accessed
- Chief provided a `visual-comparisons.rar` archive containing **134 PNG files** (RAR5). Manager extracted and inspected the actual full-resolution screenshots/crops, not merely the previously supplied `VISUAL_COMPARISONS.md` index. The archive includes all eight groups and frontend/pause/results/death/AQZ palette comparisons. The screenshots are **PRIVATE**; do not commit copyrighted sprites, maps or screen captures to this public reference repository.
- Designer reports private E2-P1 commit `ebcc8fc46dad5a9763fcfd24cdfb3ead98b0f823`, Windows ZIP `SonicChaos_Windows_20261105_E2_P1_PRIVATE.zip`, source ZIP `SonicChaos_Production_20261105_E2_P1_SOURCE_PRIVATE.zip`, and private receipt and `REPORT.md` under `management-audits/e2-p1-sharp-pixels-20261105`. Designer reports native/source checks PASS, H: recovery, preserved original Classic and E0-R1 archives. **Manager has not directly accessed the local report, receipt, Windows/source archives or code; private E2 commit was not resolvable via connected GitHub at time of review**. The last confirmed remote accepted E0-R1 head remains `deccefc0acd822f74b6b26895ec278cdf67a7cee`. Local-only E2 commit is plausible; absence on remote is not evidence of a bad package.

## Independent static pixel comparison
All eight scene groups include matched `classic`, `enhanced-off`, and `enhanced-on` full-size PNGs. Manager used unscaled RGBA pixel arrays to count differences. In **all eight groups**, **Classic vs Enhanced OFF mismatched exactly ZERO pixels**. This is evidence of visual baseline preservation in these controlled captures only, not a proof of every route or of unchanged executable runtime files.

| Group | Target | Classic vs OFF changed pixels | Classic vs Sharp ON changed pixels (%) |
|---|---|---:|---:|
| 0 | THZ1 Sonic Wide3× 1044×588 | 0 | 106,216 (17.30%) |
| 1 | THZ1 Tails Wide3× 1044×588 | 0 | 106,640 (17.37%) |
| 2 | AQZ1 Sonic Wide3× 1044×588 | 0 | 12,131 (1.98%) |
| 3 | AQZ1 Tails Wide3× 1044×588 | 0 | 12,100 (1.97%) |
| 4 | THZ1 Wide1× 348×196 | 0 | 0 (0.00%) |
| 5 | THZ1 Wide2× 696×392 | 0 | 67,252 (24.65%) |
| 6 | THZ1 actual Retro3× 870×654 | 0 | 99,069 (17.41%) |
| 7 | THZ1 controlled native256 3× 768×576 | 0 | 75,668 (17.11%) |

**Interpretation:** Sharp ON materially changes THZ1 pixel edges at multiplied dimensions; the 1× static case is unchanged as expected for sampled integer geometry, while AQZ1 differs less because several original render/shader paths already use nearest locally. A change-count is **not** a quality rating, proof of pure 1:1 native scaling or proof of smoother motion.

## Visual observations
- THZ1 Sonic/Tails faces/outlines and HUD counter edges are visibly crisper; less blended intermediate colours, with more obvious pixel stairs at diagonals and character outlines (subjective trade-off). THZ foliage/flower/grass and checkerboard terrain are sharper; no obvious new static clipping/occlusion defect in reviewed 1:1 crops.
- AQZ1 player/terrain and controlled underwater palette splits remain visually legible, with much smaller ON differences. For both characters and each of split samples 30,60,90 the Classic/OFF full images are pixel-identical. Sharp ON changes ~1.95–2.00% of image pixels; no gross palette inversion/blackout seen in the reviewed examples.
- The Enhanced Options ON and OFF captures visibly show `SHARP PIXELS` state and `START GAME` below as final selectable entry; ESC/pad B Back help visible. The pause, results and death captures contain expected visible content in all sample states, not black frames. This does not substitute for transitions/resume in a natural play route.
- Title comparison happens to show zero pixel differences between Classic and ON in the sampled image; this can result from explicit local nearest handling. It is not evidence that the Sharp feature was not applied to gameplay.

## Material limits
- The archive supplies **controlled native GameMaker screenshots** and synthetic state routes, not a full natural gameplay passage, controller hardware acceptance or externally measured display/present cadence. No claim about camera-motion shimmer, latency, subjective scrolling quality, crash-free full campaigns or 60 FPS display cadence.
- Manager's independent evidence is limited to picture inspection and pixel comparison. Exact E2 code diff/H: recovery and SHA-256 cannot be independently verified without the private source/report/receipt; Designer's technical PASS is reported as such, not upgraded to direct Manager source verification.
- The GPZ3 tube texture issue remains tracked separately as Classic defect FC-PF-001; Sharp Pixels is not a substitute for the source-map texture correction. Enhanced ring-scatter and E1 pacing changes remain parked.

## Manager disposition / next action
**E2-P1 static VISUAL REVIEW: PASS (scoped).** The Sharp option produces a clear and plausible 8-bit visual alternative with Classic/OFF pixel-identical in all eight controlled capture groups. **Recommendation:** keep Sharp ON/OFF, default OFF pending Chief's preference. Do **not** mark E2-P1 Chief-accepted yet, promote Sharp to default ON, start native-grid integer-fit or begin CRT implementation.

**Chief's small acceptance:** run the single private E2-P1 Windows ZIP; look at default OFF vs toggled ON in a brief THZ1 scrolling sequence, compare Sonic/Tails/foreground and HUD, then view AQZ water if convenient; test physical pad and Back/START GAME, and briefly pause/resume. Ask specifically whether Sharp looks better *in motion* and whether any visual shimmer or harsh jaggies are objectionable. No full campaign or broad retest.

**Repository note:** no commit on private SonicChaos_POC was requested or performed by Manager; do not interpret a missing public remote ref as source failure. Later Designer can supply the SHA/link or the source/receipt for an exact diff audit if needed before final provenance closeout.

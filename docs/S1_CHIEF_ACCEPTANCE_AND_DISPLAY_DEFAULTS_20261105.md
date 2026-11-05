# Sonic Chaos — S1 Integrated Enhanced Display: Chief Acceptance
**5 November 2026 · Manager-san #10 · S1 CHIEF ACCEPTED · Permanent feature preference recorded (not yet applied to shipped binary)**

## Chief's actual acceptance and feedback
Chief completed the requested **one combined Windows acceptance session** for the S1 private candidate, then reported **"All checked! Working as expected."** This closes S1 as **CHIEF ACCEPTED**, without requiring further individual feature builds or another whole-game playthrough.

Chief's explicit observations:
- **Sharp Pixels:** difference subtle/not apparent in ordinary live play, but strikingly visible in the supplied screenshots. **Chief elects Sharp Pixels ON by default for future Enhanced builds.**
- **Integer Fit:** no obvious difference at Chief's existing window size, believed to have remained at **3× for roughly two months**. Function accepted as working, but its comparative benefit in larger/free-form/fullscreen clients is **not visually assessed by Chief**. Keep **OFF by default** pending shared PC fullscreen/resizing/window-size release polish.
- **Current `CRT FILTER`:** Chief likes the effect, but judges it essentially **scanlines**, not a convincing complete CRT simulation. **OFF by default**, preserve optional feature; propose renaming the existing lightweight entry to **SCANLINES** in a future integrated build so the label is accurate. This is a planned label change, **not already implemented in S1**. A substantially more realistic/visually impressive CRT (e.g. feasibility work using Lola Retro's multi-pass approach) is a **separate later research/design sprint**, not a retroactive flaw or extra work added to S1.

## Accepted precise source/package
- **Chief-accepted S1 private source branch:** `enhancement/s1-display-foundation-20261105`.
- **Chief-accepted local S1 commit (Designer-reported):** `56c767e8b4f0f73c41f2d8ec41ca471d7a90e746`.
- **Windows ZIP actually accepted:** `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Windows_20261105_S1_DISPLAY_FOUNDATION_PRIVATE.zip`.
- Private source ZIP: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Production_20261105_S1_DISPLAY_FOUNDATION_SOURCE_PRIVATE.zip`.
- Private full-resolution comparison ZIP: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_20261105_S1_DISPLAY_FOUNDATION_VISUAL_COMPARISONS_PRIVATE.zip`.
- Receipt and H: recoverability evidence: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_20261105_S1_DISPLAY_FOUNDATION_RECEIPT.json`, reportedly independently backed up by Designer; Manager did **not** directly hash the local archives, inspect receipt or resolve S1 on connected game GitHub remote at last check. This visibility limitation does not undo Chief's owner acceptance.
- **Immutable Classic source/tag** `classic-core-20261105` → `3a58912659b48573ac7f2c5c96a02a2211d5e4da` still protected; E0-R1 baseline `deccefc0acd822f74b6b26895ec278cdf67a7cee` and historical packages unchanged. **S1 is the new accepted Enhanced successor baseline**, not an automatic merge, retag, release upload or alteration of frozen Classic.

## Delivered S1 feature defaults versus intended next defaults

| Feature | What the **accepted S1 ZIP actually boots with** | Chief preference for the **next integrated Enhanced release** |
|---|---|---|
| `SHARP PIXELS` | **OFF** | **ON** (next integrated build; preserve Classic original) |
| `INTEGER FIT` | **OFF** | **OFF**; useful later with flexible window/fullscreen presentation |
| Existing `CRT FILTER` (light scanlines/mask) | **OFF** | **OFF**; propose rename `SCANLINES` later |

**No immediate micro-build commissioned.** The accepted Windows ZIP stays byte-identical and OFF/OFF/OFF by default; a small future change to the session default cannot be described as already implemented. All three toggles remain independently selectable in S1.

## Evidence and bounded conclusions
- Previous Designer S1 integrated report: 3,472 source-host assertions, 60 native scenario cells, 5,460 unchanged core gameplay snapshots, 164 classic/all-OFF pixel-identical pairs, 104 exact integer outputs and 124 bounded integer+CRT samples, 180 native Z80 programme ticks per state, compiled Pause/results/death ownership and fallback, private package/H: verification. Manager already documented evidence limits separately in [S1 integrated technical review](S1_INTEGRATED_CANDIDATE_MANAGER_REVIEW_20261105.md).
- Chief's normal real Windows visual/controller/play/listen check now reported **PASS**. This is practical acceptance, not new numeric frame-present telemetry, an independently audited source manifest or a full Sonic/Tails campaign.
- At 3× normal window sizes, integer-fit output can appear identical in dimensions to the original window; S1 explicitly did not introduce fullscreen or resize UI. Do not infer Integer Fit failed because its added value was not visible in Chief's current window configuration.
- Current CRT is a restrained single-pass filter (reported weak scanline modulation and RGB mask). Describing it as lightweight scanlines is a fair product-label clarification; stronger authentic CRT processing involves multipass surfaces, phosphor/beam handling and greater cost. Do not promise successful Lola port or automatically assume an authentic PAL/NTSC signal mode.

## Next development direction and scope protection
- **S1 CLOSED — CHIEF ACCEPTED.** Use accepted local SHA `56c767e8...` as base for subsequent **substantial, separately scoped** Enhanced sprints. First verify local branch/clean checkpoint/receipt; do not automatically push or merge.
- **Small future bundled polish changes:** set default `SHARP PIXELS=ON` only for committed Enhanced; leave `INTEGER FIT=OFF`; rename current effect `CRT FILTER` → `SCANLINES` if the label remains accurate; retain OFF. These changes may accompany the next coherent feature sprint or later release-polish batch, not get a standalone Chief package.
- **Future improved CRT:** research visually dramatic yet faithful CRT models separately (Lola Retro high-level reference: eight-pass Master System preset, major GameMaker conversion/resources/black-output/fallback risks). A future study can first compare reference imagery/technique versus current SCANLINES and agree a target/look before implementing. Default OFF unless Chief explicitly requests otherwise.
- **Already parked endgame release UI:** Classic+Enhanced common window size/layout/fullscreen menu and hide release-facing developer Pause Level Select together, with Pause interval restrictions later if justified. Existing `settings.ini` retains window multiplier and Auto/Wide/Retro. Avoid interrupting a sprint for these. [Endgame tracker](tracking/ENDGAME_RELEASE_POLISH.md).
- **Separate existing backlogs:** GPZ3 blue tube source-art seams (Classic post-freeze defect), richer optional Enhanced ring scatter; E1 true display-pacing proof remains inconclusive. Do not bundle unrelated gameplay/ROM issues into display polish without Chief authorization.

**Manager conclusion:** S1 achieved the requested large-sprint workflow, with Chief acceptance from one combined test. Historical E0, S1 visual evidence and frozen Classic all remain recoverable.

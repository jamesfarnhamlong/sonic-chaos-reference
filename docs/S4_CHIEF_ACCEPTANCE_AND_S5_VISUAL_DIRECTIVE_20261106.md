# Sonic Chaos — S4 CHIEF ACCEPTANCE and S5 original-art presentation directive
**6 November 2026 · Manager-san #11 · S4 FUNCTIONAL/RENDERING CHIEF PASS · S5 VISUAL ART DIRECTION ACCEPTED, NOT IMPLEMENTED**

## Chief's actual Windows acceptance

Chief reviewed and tested the integrated private **S4 Enhanced 1080p** Windows build and reports:

> “OK! All tested and pass. Boss rush completed with tails, those fixes are great and all good now.”

Chief confirms:
- **1080p Enhanced display / borderless** working.
- **Integer Fit ON and OFF** both work; Chief also likes the larger display area with OFF and wants users to retain the choice; Integer Fit is technically accepted but the new **Enhanced ON default is NOT a mandate that users keep it ON**.
- **S3-POST-01 MGHZ→AQZ camera jump**, **S3-POST-02 Boss Rush LIVES HUD visibility**, **UI-POST-03 early START** all **Chief PASS / CLOSED** on S4.
- **Full natural Boss Rush completion with Tails PASS**, including prior mechanics and original music continuity.
- S4 functional display architecture, in-motion play and window presentation are **CHIEF ACCEPTED**; only user-observed tests are claimed, not an invented second full Sonic or every display/monitor profile.

**Critical split verdict:** The **new Enhanced UI appearance is NOT ACCEPTED AS FINAL**. It was sufficient as a **foundation/provisional UI**, but Chief finds its white sans-serif text, dark rectangular panels, boxed five-card data screen, excessive instructional text and visual mismatch with the original title/ROM artwork **very unattractive/incongruous**. There is a visible extra/original START GAME underneath the new title overlay; the opaque panel obscures instead of integrating the authentic title presentation. This is an **S5 visual issue, not a reason to roll back functional S4**. The yellow-hat/flat Tails preview and small crunchy thumbnails remain. The results screen's large modern font/plain rectangle also needs original-style visual integration.

## S4 exact private delivery and source custody

- Private local S4 branch: `enhancement/s4-1080p-foundation-20261106`; Designer-reported complete commit `977a41824f227f3bdfe6f45596e6845902459842`. **At Manager's previous remote check, S4 branch/SHA were not present on private GitHub; do not assume a push occurred.**
- Standard Windows ZIP: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Windows_20261106_S4_1080P_CANDIDATE_PRIVATE.zip`.
- Complete private source ZIP: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Production_20261106_S4_1080P_SOURCE_PRIVATE.zip`.
- Native S4 evidence ZIP: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_20261106_S4_1080P_EVIDENCE_PRIVATE.zip`.
- Manifest/receipt: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_20261106_S4_1080P_RECEIPT.json`; SHA-256: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_20261106_S4_1080P_SHA256.txt`.
- Designer reported **75 native S3 handoffs**, **184 exactly matching Classic image comparisons**, high-resolution UI, native Wide348x196 5× rendering, window/lifecycle recovery and H: restoration. Chief's final Windows play makes S4 *owner-accepted*, not independently reverified every raw numerical claim.
- Complete source ZIP/H: preserves **4 ignored runtime dependencies and 18 ignored original sprite PNGs** that are **not guaranteed recoverable from Git tracked tree**. Never reconstruct S5 from Git alone, omit these files or change the accepted S4 ZIP. Accepted S3-R2 private remote source remains at `29044caac612a0d2a23399e9fb7a58abda387740`; frozen Classic tag `classic-core-20261105` remains `3a58912659b48573ac7f2c5c96a02a2211d5e4da`.
- No S5 build, source modification, public asset upload, automatic private Git push, main merge, release or tag change authorized by this receipt.

## S5 Chief art-direction pivot — ORIGINAL ART, COMPUTATIONAL 8→16-BIT-LIKE PRESENTATION

Chief explicitly says **“No creating new high res art! We should try to improve the original art using science!”** and wants the existing 8-bit source visuals **presented like a restrained 16-bit Sonic interface**, not redesigned from scratch in modern corporate/higher-resolution graphics. Sonic 3 and Sonic Mania images supplied privately **as layout/composition references only**, not licensed game assets to copy, upload, redistribute or trace.

**What to preserve:** S4 1080p output and safe High-DPI/window/mode layer, original game-world art/logic/camera/audio, Classic strict presentation, all S1/S2/S3 functionality, S2 save semantics, S3 GG `$9B` music, BOSS RUSH CLEAR TIME/RINGS/LIVES and Tails/Sonic animation source. Distinguish source *content/texture size* from full 1080p *composition space*.

**Design requirements to discuss before S5 implementation:**
1. **Title:** keep original Sonic/Tails and Sonic Chaos art, and its original pixel-language typography. Fix legacy START GAME appearing under independent menu. Compose only **START / BOSS RUSH** where they belong visually in the authentic title, not a giant navy rectangle or modern sans-serif cover. Small unobtrusive instruction only if required; require visible menu before early START acceptance (S4 fix must remain).
2. **Data Select:** five usable slot cards, but strip redundant `SLOT N / NEW GAME / SELECT CHARACTER / CONTINUE` repetition and sprawling bottom instructions. Let preview art, animated original running Sonic/Tails, a concise zone label, progression/gem icons, clear empty/occupied/highlight state, and a small contextual hint communicate state. Keep all intuitive navigation, selection, wipe confirmation, player-locked/zone selection and Classic separation.
3. **Authentic source**: do not introduce generated/purchased HD Sonic sprites, vector/poster art or unrelated font families. Preserve original source artwork pixel identity and only derive enhanced presentation assets from exact original or Chief-approved source art. The current Tails yellow hat/ears, character feet baseline, thumbnails too crunchy and Emeralds dull all still form the **six-item original S2-VIS-01..06 queue**; adjust layout and source pixel/frame selection first, not invent entirely new high-res illustrations. Current TV static (if any) must stay subtle, palette-suitable and safe.
4. **Boss Rush CLEAR:** source-styled panel/lettering, visually integrated with game scene and full-screen high-res compositor. Keep actual TIME/RINGS/LIVES and original music/audio, controller flow unchanged; no score yet.
5. **Original-art computational enlargement A/B:** compare ORIGINAL NEAREST 2× (reference), **Scale2x/EPX** conservative, **HQ2x**, and **xBRZ 2×** on a bounded set of actual private source assets: title character emblem, title font, one populated/empty TV card, Tails/Sonic 6-frame running sequences, Emerald icon and a preview tile. Compare at **actual 1080p 1:1** and in motion (palette/alpha halo, consistent frame edges, readability), first as **offline asset-generation/benchmarked nonshipping variants**, not a global filter injection. No algorithm is canonically superior: xBRZ/HQx infer shapes/new colors and can over-round outlines; glyphs, UI borders and tiny text may be better nearest/Scale2x; avoid unreviewed blanket smoothing of original game world or pixel text. Assess runtime licensing/attribution and asset-processing reproducibility before shipping external code. Once appropriate art-specific 2× is chosen, compose it at 1080p output at integer/aligned scale, without repeatedly resampling. Do not accidentally apply native 5× integer fit to the high-res UI twice.
6. **Text hierarchy:** original/game-inspired pixel font from existing assets where possible; minimal labels, smaller restrained instruction line only when interaction is otherwise not discoverable. No generic oversized sans serif or “debug dashboard” look.
7. **CRT/scale:** user specifically liked **both Integer Fit ON and OFF**; keep both working and selectable. S5 styling must be legible in either and under S1 CRT/Sharp on/off, not force a single smoothness preference. Keep gameplay unaffected in all conditions.

**Manager's suggested S5 prep:** a single authentic source-art comparison board (nearest vs Scale2x vs HQ2x vs xBRZ) and two compact layout composition studies (title and Data Select) inside ONE eventual substantive Designer sprint, but get Chief agreement on scope before implementation. Do NOT ask Chief to inspect numerous microbuilds. If an algorithm makes the source characters look too smooth or alters their distinctive pixel shape, discard it in favor of nearest/Scale2x and better composition.

## Status and next steps
- **S4 CLOSED / CHIEF ACCEPTED for display architecture, gameplay, windowing, S3 corrections and controller flow.**
- **Three post-S3 issues CLOSED BY CHIEF TEST on S4** (not merely Designer reported fixed).
- **S5 interface appearance** now the primary active design topic, not yet implementation GO. Existing new UI assets are **temporary foundations**, not approved final design.
- Optionally commission a separate small no-source-change **S4 private Git custody push** after verified complete ignored-file recovery; only when Chief authorizes. Never change accepted SHA/archives.

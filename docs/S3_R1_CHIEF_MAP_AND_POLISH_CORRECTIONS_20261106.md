# Sonic Chaos — S3-R1 Chief Map & Presentation Corrections
**6 November 2026 · Manager-san #11 · ONE FOCUSED INTEGRATED DESIGNER CORRECTION · NOT YET CHIEF ACCEPTED**

## Chief evidence and precedence
Chief personally completed the initial S3 Boss Rush course: all six fights and the EEZ final/ending run progressed correctly; no observed boss-mechanics defects; normal Classic and Enhanced modes also worked. Treat this as a **functional/core gameplay PASS**, not S3 final acceptance. The next task is a **single R1 corrective-polish sprint** based on Chief's new complete map compositions and annotated pit diagram, supplied **directly and privately to Designer**. Do not publish the PNGs to public reference GitHub.

Files Chief will attach to Designer:
- `bossrush_map1.png` — first four-stage horizontal composition.
- `bossrush_map2.png` — extended late-zone layout/end ascent.
- `image(20261106-045158).png` — **binding marked-up pit/platform diagram** (red outlines = proposed death pits; purple outline = SEZ/SLZ collapsing-platform strip).

Use these *actual images* as the authority for structural geography: avoid guessing coordinates from chat descriptions alone. Establish exact source-map/world-space boundaries before editing. The map screenshots represent **layout geometry**; the finished course still uses the unified EEZ/compatible MGHZ-inspired mechanical art direction, not the mixed source-zone skies and grass.

## 1. Spatial and pit constraints — Chief's latest explicit decision
- Keep the first four encounters on a largely continuous horizontal traversal band, then allow a deliberate, thematically appropriate **upward climb near the final encounter**. The attached complete maps supersede the shorter connector composition if they differ.
- In the first four zones, **only TWO areas are proposed for new death pits**, as annotated in **red**; do not add extra pits simply to constrain movement.
- **SEZ/SLZ platform area:** the strip marked **purple** is collapsing platforms, which Chief reports currently **do not collapse** in S3. Investigate original-state ownership and challenge assembly; restore the intended dynamic collapse mechanics and visible behavior in the challenge only, preserving original timing/collision/audio. The **first red pit beneath that bridge/platform area** is the lethal void after collapse; no safe hidden lower floor underneath.
- **MGHZ special-platform area:** the **second red pit is under the long special platform**; remove the unnecessary lower escape/safety terrain only in Boss Rush. Its intent is **run/jump correctly or die**, not a new unfair boss-attack death. Preserve the boss/tree/spike-gated reveal and essential combat platforms/camera.
- Chief specifically wants to avoid altering the **existing level-wide terminal/death Y threshold part-way through the zone**. Determine the actual current kill-Y contract in local and composed coordinates; place the two pits **below the effective existing terminal Y** (or use the already-authorized static challenge boundary if that is how S3 works), without new mid-zone dynamically varying kill-Y values. Do not assume the engine's numeric Y relationship without checking; report any genuine geometric impossibility rather than hiding a changed global death-plane/collision semantic.
- Pits serve to limit forbidden lower exploration/backtracking and constrain the playable vertical extent. Keep boundaries readable; Sonic and Tails should never walk on invisible floors, fall forever or be forced into invisible barriers; Tails flight and ordinary valid knockback must not cause a cheap or unavoidable combat death.

## 2. Existing Chief corrective findings to include IN SAME R1
- Visually homogenize the entire route: remove discordant source-zone **trees, grass and sky**. Prefer coherent Electric Egg industrial scenery, with appropriate MGHZ mechanical motifs where they harmonize. Preserve functional water/spikes/springs, boss sprites and original collision. No art replacement in ordinary Classic or Enhanced stages.
- Remove **boss-defeat sparkle and victory jingle** in challenge transitions only, keeping appropriate original fight sound effects and music continuity; remove **stray smoke puffs near Boss 2 (GPZ)**. Confirm these are challenge-only side effects and do not disable original feedback in regular stages.
- Fix the **Boss 2→3 invisible obstacle/mandatory jump** by identifying its collision owner and supplying visible compatible geometry or correcting an incorrect collision mapping. Avoid deleting necessary authentic hazards without evidence.
- Fix the **Boss 4→5 spring graphics failing to load** across the handoff; verify spring effect, sprite/resource ownership and collision for both characters.
- Recompose/lengthen late **4→5→6 connectors** using Chief's extended map as authority; allow modest, readable verticality especially the final ascent; keep short playable route rather than six disconnected rooms. Verify camera locks, hazards, transitions and player positions across altered joins.
- Retain the ordinary **rings/time HUD** visibly during the challenge and across all five joins, deaths, restart and finish; keep correct ring/time continuity and existing native display/raster at Wide/Retro. Future best-time/ring-score features are *not* commissioned now.
- Difficulty was considered **a little easy but acceptable** by Chief; do not arbitrarily buff bosses, restrict lives further or add pit hazards outside the annotated areas.

## 3. Source safety and verification
- Start from exact S3 delivered candidate, reported abbreviated `7a6a4b7` (obtain full SHA, branch and receipt locally), with accepted Enhanced S2 parent `0809ef9cbc9ea9c1fda3bc0ead45aa9aa749a5a7`. Protect immutable Classic tag `classic-core-20261105`. No automatic merge, main update or public asset/release publication.
- Preserve the six boss state machines, health, triggers, original local room/camera ownership, EEZ full final chain, GPZ loop, native audio driver and normal campaign saves. Isolate fixes to challenge-only maps/presentation/handoff behavior. Changes to common routines require an explicit guard, a change inventory and evidence that Classic/ordinary Enhanced stay equivalent.
- Agent owns routine research/correction and can make internal checkpoints and compile as needed, but only **ONE full Chief-facing R1 candidate** should be delivered.
- Within one consolidated verification suite: naturally traverse revised SEZ collapsing bridge into pit (including deterministic waits/occupancy), fall/die/restart correctly, MGHZ platform/pit and boss spike-gate; jump/fly across all revised joins, including 2→3 and 4→5; confirm springs render and function; verify camera/pit Y bound in both local/world frames, ring/time HUD continuity, the EEZ finish and clear/title, no boss post-defeat sparkle/jingle/smoke, EEZ-theme captures for every section. Test both characters at 348×196 Wide and representative 256×192/290×218 checks.
- Preserve save isolation with real pre/post file hashes, ideally using **disposable populated saves** (the first S3 native on-disk cases were empty/tombstone; populated isolation was source-mocked); do not touch Chief's real progress. Check normal Classic and ordinary Enhanced startup/Data Select. Report raw inherited failures separately.
- Package standard uninstrumented Windows ZIP, full private source, exact full commit/tree and changed files, annotated before/after stage maps or screenshots, focused native/log verification, SHA-256 and independent H: recovery. Do not claim Chief final PASS until actual R1 human gameplay.

**Manager decision: S3 functional PASS, S3-R1 focused corrective design/build GO; Boss Rush final acceptance pending.**

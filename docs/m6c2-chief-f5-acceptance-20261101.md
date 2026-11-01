# M6-C2 — Chief Windows F5 acceptance, production source baseline (1 November 2026)

**Status: CHIEF ACCEPTED — M6-C2 OPENING FOREGROUND LAYER FIX PASS.**

Chief explicitly reports after testing the private M6-C2 GameMaker candidate: **“I checked the opening animation, its good!”** This follows the targeted Manager approval request to observe Robotnik's machine entering/leaving **behind the black foreground bars** in normal unskipped opening; interpret the Chief response as approval of that targeted opening animation correction. **Do not invent additional specific claims** about a frame-by-frame native trace, return-to-title timings, every possible skip, 256-pixel native play or audio retest. No further Chief retest of opening is required.

**Exact accepted production source:** `jamesfarnhamlong/SonicChaos_POC` branch `poc/m6c2-opening-border-occlusion`, commit **`3cf379240c6e1e06b52a4b57fcfd087fcd1fffa2`**, a single direct child (1 ahead, 0 behind) of accepted M5-G2 `91fd74b56296bb9182768c3a9db78a186fa78f9e`. Remote tip verified previously. Only production diff is `scripts/SCR_chaos_opening/SCR_chaos_opening.gml`: ROM-backed zone7 block$2F opaque black priority layers restored by repainting existing strip bands after machine/actors. Flight coordinates, wide exit, 738 source updates, fades, startup native audio, and registered 1,313 resources not modified by this production patch.

**Designer source evidence**, distinct from Chief's F5: 7/7 focused gates PASS, 32,475 painter checks, 1,476 paired software pixel-mask frames, original opening sprite hashes81/81 and resource count1,313; no automated agent native GameMaker Runner trace because Codex Windows Runner failed with OS loader error623 in earlier attempts. Private ZIP `SonicChaos_M6C2_20261101_A_PRIVATE.zip` and external checksum receipt are user-local/private, **not independently byte-validated by Manager**; Designer reported clean worktree and SHA.

## Gate released: M6-D AUTHORIZED TO BEGIN PRODUCTION

Chief's F5 acceptance satisfies the explicit M6-D dependency in [binding Manager review and assignment](m6c2-manager-review-m6d-speed-and-shortcuts-20261101.md). **Replace “F5 approval pending” with “F5 PASS; M6-D may proceed.”** This is the acceptance fact requested in Codex's gate prompt, so respond **“Yes — Chief passed M6-C2.”**

Next branch `poc/m6d-speed-display-cleanup` must start directly from **accepted M6-C2 `3cf379240c6e1e06b52a4b57fcfd087fcd1fffa2`**, **not** original G2 or audit branches. Two authorized tasks:

1. **RESULTS-001 original Master System km/h goal child type$19 presentation**: source/ROM-backed correct visual/timing and both characters; current `chaos_bonus_word` already returns 617 for 1:50/28 rings but original `OBJ_chaos_object_19` speed panel is explicitly invisible/deferred; implement visual without changing validated scoring or tally. Original screenshot and SMS ROM Chief confirmation support feature.
2. **Remove ALL developer-only keyboard shortcuts from normal gameplay** (F2 legacy switch, F3 debug, R test restart, Shift+F7..F10 death fixture, T/Shift+T, number-key sign counter injection and additional hidden GML input traps discovered by complete audit). Preserve ordinary gameplay keyboard/controller, pause/resume, **Pause -> Level Select**, visible menu and **original F2 Sound Test catalogue** as a menu function (the F2 KEY shortcut can be removed while menu remains). Preserve all accepted M5 audio and M6-C2 opening.

Deliver ONE coherent private candidate with machine-readable verification and a focused Chief F5 check; no repetitive 63-audio/zone tests, no agent Runner error623 troubleshooting, no automatic main merge. Separate staged original child graphic sourcing from invented modern overlay. Retain MGHZ3 widescreen roughness and startup delay as parked.

**M6-C2 F5 gate closed; M6-D production work GO.**

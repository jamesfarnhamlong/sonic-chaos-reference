# Sonic Chaos — C1-R9 Classic Ordinary Camera Integration Design: Manager #12 Closeout

**12 November 2026 · Manager-san #12 · REVIEWED UPLOADED R9 REPORT · DESIGN HOLD · NO SOURCE CHANGE · CLASSIC REPLACEMENT HOLD**

## Source and decision provenance

Chief supplied `C1_R9_CAMERA_INTEGRATION_DESIGN_20261112.md` and the previous Manager #11 thread. Manager #12 read the R9 report and checked the current GitHub operating documents and [R9 charter](C1_R9_ORDINARY_CAMERA_INTEGRATION_DESIGN_SPRINT_20261112.md). This closeout is a management review of the **reported evidence and the proposed design**, not an independent rerun of ROM, GameMaker, Windows or H: recovery. The source-level paths and counts below are as reported by Designer.

**Verdict: DESIGN HOLD.** The proposed ordinary-camera pending-value transaction has a plausible custody mechanism, but **no established native post-player sign/child dispatch owner** exists, and goal-pan state-$20 freeze/control scheduling remains fused to camera preparation. Do **not** commission R10 camera coding or mark original/native camera parity established. Pause the camera line rather than run an additional near-identical tracer sprint.

## What R9 established

- **Original ROM rule (inherited from R8):** ordinary camera is prepared pre-player; sign/THZ object activation changes new owner/target/bounds without altering the already prepared candidate; VBlank commits that candidate unchanged. Examples are sign update586: commit(3825,449); THZ right lock update293: commit(1663,126) despite newly tightened right bound1659; THZ pan only begins update380. ROM inference is bounded to R8's controlled transitions, not every boss/lifecycle.
- **Actual GameMaker structure:** normal Step scheduling is not guaranteed across instances; existing sign `$18` and child `$19` callbacks are independent normal Steps, player adapter also runs a normal Step, and zone End Step executes its explicit objects phase followed by camera owner selection. Player End Step tail and zone End Step are not guaranteed ordered relative to one another. Ordinary camera has no pending buffer; a sign may update before player.
- **Feasible but incomplete design:** one idempotent Classic-only pre-mutation transaction entry, snapshot of entry owner/committed view/leads/bounds, a pure camera evaluator into pending XY, explicit once-only commit after objects with lifecycle/room/actor guards. New same-update owner changes affect only the next entry; reject retroactive reclamping. Keep Special Stage R3's distinct pending camera and all Enhanced S6 paths intact.
- **Critical missing interface:** explicit once-per-tick post-player dispatch for sign `$18` and child `$19` including child birth/first tick, contact, footwear conversion, retouch, prize and state20. The sign-pan helper also combines XY update with the state20 freeze decision; that logic must not be moved speculatively.
- **THZ specific original behaviour:** camera mode2 may retain X1663 despite right bound1659 for subsequent updates. Mode4/release and other zone bosses are unproven. Native controlled boss seed also gains +7px Y before semantic alignment, so no absolute original/native equivalence follows.
- **R9 evidence limits:** 36 relevant source files mapped; inherited 360 native retail alignment rows parsed (180 Sonic +180 Tails), 20 original transition decisions and 120 **external shadow permutations**. Shadow custody is not compiled scheduling proof; R9 ran no fresh native game, made no source/resource modification and produced no executable.

## Source / preservation custody

- Isolated Classic working source exact R3 commit `b667cc5cebcd3c3e047d9f527cc78b76e1e027f0`, tree `ffdfc37e23d1b18e866b8beae051234c443b9665`; R4–R9 are research/no-code work; do not invent an R9 gameplay commit.
- Production Enhanced S6 `47c501ecb994a4fcb1eeac1c29793f3f1142a304` unchanged by R9 per Designer. Frozen Classic historical tag `3a58912659b48573ac7f2c5c96a02a2211d5e4da` protected.
- Designer reports local H: recovery of 9,605 source files/22 ignored dependencies and clean source; Manager did not independently perform that recovery. No C1→S6 merge, branch push, tag, release or new Chief physical test.
- Prior known raw death helper ERROR, GPZ cap FAIL, THZ clear-camera FAIL, historical SS4/SS5 raw failures remain **open/honestly classified**.

## Manager #12 decision and proposed next track

**The original camera rule is solved for the R8 windows; GameMaker-native integration is not.** Park the ordinary-camera implementation until a separately evidenced sign/child/gameplay-phase owner and freeze split are available. Do not approve another generic camera probe and do not “correct” ROM quirks by smoothing, offsets or clamps.

**Recommended next Classic task, NOT YET COMMISSIONED:** a small independent **Tails update2 animation-counter discrepancy** investigation. The R7 genuine retail THZ1 trace recorded original counters `8,8` vs native `8,7` at update2; positions, animation pointer and displayed frames matched. Establish whether this is a real first-counter ownership/update-order defect, whether the mismatch propagates into terrain/rings or animation, and whether any *minimal Classic-only* fix is supported. Preserve the possibility of an evidence-backed NO-CHANGE conclusion. Do not touch the ordinary camera, introduce speculative gameplay offsets, or extend QoL into Classic. Any future coding requires normal ROM/native parity and Enhanced S6 regression evidence.

**Still open, separate C1 gates:** authentic original THZ/Sonic, GPZ/Tails and SEZ/Sonic attract-demo playback, first16 shared object slots, palette-aware left8 VDP mask with fade-phase alignment, natural whole-game routes, PAL timing and honest raw-failure reconciliation. Chief's offered side-by-side demo test is useful **after native GameMaker playback exists**, not now.

**Enhanced:** S5/S6 owner combined round 33 PASS, four late-save/result tests UNOBSERVED (not failures); Chief personally preparing six 144×128 Save TV assets for a later Enhanced-only integration. Generic shared Pause redesign entirely PARKED. No Enhanced QoL job commissioned.

**Final management status: C1-R9 DESIGN HOLD; CAMERA CODE HOLD; CLASSIC REPLACEMENT HOLD; Enhanced S6 PROTECTED; next Tails scope for Chief approval.**

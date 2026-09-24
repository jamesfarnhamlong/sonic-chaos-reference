# Sonic Chaos — project status

Updated: 24 September 2026

This is the coordination status for the Sonic Chaos SMS research/reference work and the Windows GameMaker proof of concept. Read this before starting a new research or POC pass. The ROM and the reference repository remain authoritative for original-game behavior; the POC is an implementation target, not evidence for the ROM.

## Canonical repositories and ROM

- Reference/disassembly: `jamesfarnhamlong/sonic-chaos-reference`
- Windows/GameMaker POC: `jamesfarnhamlong/SonicChaos_POC`
- Verified ROM size: 524,288 bytes
- Verified ROM SHA-256: `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`

Rules:

- Do not invent object identities, placements, graphics, collision helpers, animation meanings, or replacement artwork.
- Unknown object types remain numerically named until source evidence establishes a semantic identity.
- Preserve original integer/fixed-point movement units.
- Keep ROM-backed facts separate from POC adapters and gameplay observations.
- Record ROM file offsets and bank/CPU addresses where relevant.
- The user manually tests Windows/GameMaker archives and updates the POC repository from accepted builds.

## Current verified research baseline

Current `main` baseline:

- 53 recovered ROM regions
- 10,830 recovered bytes
- 4,206 decoded instructions
- 37,386 controlled original-Z80 comparisons
- 524,288-byte byte-identical reconstruction
- SHA-256 matches the canonical ROM above

The current THZ1 census contains exactly 53 raw nine-byte object records across eight placed types.

| Type | Records | Current research status |
|---|---:|---|
| `$09` | 24 | graphics/animation decoded; behavior and relationship to layout-derived rings unresolved |
| `$10` | 5 | graphics/animation decoded; parameter/reward/contact/lifetime study is Task 04 and is currently in progress, not merged |
| `$18` | 1 | dynamic goal-sign graphics verified; completion/lifetime behavior partial |
| `$1B` | 4 | retracting spikes; core state machine substantially verified |
| `$21` | 6 | THZ1-reachable behavior formally complete; canonical identity remains non-verified |
| `$26` | 4 | concealed/contact spring state machines substantially verified |
| `$27` | 3 | THZ1-reachable behavior formally complete; semantic identity unresolved |
| `$28` | 6 | moving-platform role verified; behavior partial; animation states 4/12/14 currently stop at unsupported command `$09` |

Important census correction: the 24 raw type-`$09` placement records and the 142 separately decoded ring positions from THZ1 layout blocks are different source populations. No current evidence proves that one expands into the other.

## Research task tracker

### Task 01 — type `$21`: COMPLETE

Formal placement, initialization, patrol, contact, animation, orientation and lifetime study.

Six THZ1 records:

- `(800,606,$08)`
- `(1248,862,$06)`
- `(2048,318,$06)`
- `(3152,894,$03)`
- `(3296,286,$04)`
- `(2400,254,$02)`

Key verified behavior:

- parameter is a leftward patrol span in units of 16 pixels;
- initialization sets X velocity to -0.5 and Y velocity to +2.0;
- floor projection and patrol reversal are source-traced and controlled-traced;
- contact distinguishes top bounce, ordinary side damage, and defeated-enemy conversion;
- defeat converts to type `$0F`, awards score bytes `10 00 00`, and detaches the placement token;
- generic off-range cleanup releases occupancy and allows recreation.

Primary study: `docs/object-21.md`.

### Task 02 — type `$27`: COMPLETE

Formal placement, state-script, proximity, oscillation, contact, orientation and lifetime study.

Three THZ1 records:

- `(3504,224)`
- `(2288,768)`
- `(2240,112)`

Key verified behavior:

- Sonic integer X is read at `$D511`;
- state-1 activation is strictly `abs(object_x - sonic_x) < 64`: 63 triggers, 64 does not;
- horizontal velocity is signed 8.8 `$FD80` (-2.5 pixels/update);
- state 2 performs 65 add-velocity and 64 subtract-velocity callbacks;
- the `$80` counter underflows on callback 129;
- net no-contact vertical displacement before reset is `$0003` in 8.8 units;
- state 3 resumes horizontal travel on update 130;
- state-3 removal is strictly `abs(object_x - sonic_x) >= 384`: 383 survives, 384 removes;
- object-specific `$FE` cleanup releases occupancy and permits respawn;
- trigger bit 1 suppresses generic off-range deletion until state 3 removes the object;
- ordinary contact requests no damage and stalls that callback;
- rolling/attack or power-up `$06` converts to `$0F`, awards `10 00 00`, and prevents ordinary placement respawn;
- placement bit 4 selects mirrored rendering; both THZ1 art bases are `$AA`.

Primary study: `docs/object-27.md`.

### Task 03 — THZ1 object census: COMPLETE

Authoritative inventory: `docs/thz1-object-census.md` and `data/rom-cache/thz1/object-census.json`.

The census records every THZ1 placement, field combination, animation/mapping entry point, graphics path, evidence level and remaining research gap. It is intended to drive subsequent independent research tasks rather than to infer behavior from presentation.

Additional correction: type `$28` placement aux1 values `$09/$0D/$00` are consumed as object-specific initialization data; they are not uniformly a second graphics art base.

### Task 04 — type `$10`: IN PROGRESS / NOT YET CANONICAL

Assigned as a formal parameter/reward/contact/lifetime study. Until its branch is reviewed and merged, do not use unmerged Task 04 findings in the POC.

Current canonical `main` knows only that THZ1 has five type-`$10` placements with parameters `$02/$04/$06`, fully decoded four-state animation reachability to frames `$00/$0B/$0C`, and monitor/item-box-like presentation supported by graphics.

## Shared engine research status

Substantially recovered/verified:

- collision header lookup and floor/side/ceiling projection cores;
- first THZ curve and ramp launch behavior;
- spring player states and tested upright spring trajectory;
- loops and twisting-strip state `$22`;
- THZ1 object placement creation;
- object update scheduler;
- object visibility/lifetime handling;
- placement occupancy cleanup;
- defeated-enemy conversion;
- object sprite orientation renderer;
- object animation engine and command dispatcher;
- animation commands `00,01,02,03,06,07,0B,0C,0E,0F`;
- type `$21`, `$26`, `$27`, `$1B` relevant regions;
- moving-platform code is recovered but not yet a complete formal object study.

Animation command semantics still not formally complete for commands `04,05,08,09,0A,0D`. Under the current THZ1 static reachability pass, only type `$28` has unresolved states: 4, 12 and 14, each stopping at unsupported command `$09`.

## Current POC baseline

POC repository `main` currently points to commit:

`a3b03825e600bc71279a0386b8c1d5f9bce81441`

Commit title:

`SonicChaos_Act1_POC_17_4`

This is the source baseline for POC 18. Do not start POC 18 from an older local archive or older branch if the GitHub `main` above is available.

Playable milestones represented by the current POC lineage:

### POC 14.5

- Integer/fixed-point movement and collision path substantially replaced inherited sample-engine physics for THZ1.
- First curved ramp rolls, launches and returns to ordinary movement.
- Both loops and six canonical moving platforms function through bounded adapters.
- Opening upright red spring reaches the tested ROM height.

### POC 15 / 15.1

- Type `$26` concealed springs added from recovered behavior.
- Type `$1B` confirmed and ported as four retracting spike sets.
- Object, terrain-spring, platform, ring and monitor placement data regenerated from ROM-derived caches.
- Fabricated badniks and fabricated finish marker removed.

### POC 16

- Player state `$22` twisting/Mobius traversal implemented.
- Four 28-entry dispatch tables (112 entries), entry rules, angle/magnitude motion, tile alignment and rolling exit ported.
- Windows test confirmed traversal; rolling presentation remains overused relative to the ROM.

### POC 17 / 17.4

- Three canonical type-`$27` placements added with ROM-derived frames and initial behavior.
- Static spike block type-5 floor-contact hazard condition ported.
- Moving spikes use ROM mapping frame `$0E` and floor-aligned presentation.
- Terrain-spring standalone PNG transparency was corrected, but the lower-route `$31` spring rectangle remained visible.
- POC 17.4 is the current regression baseline.

## Current POC limitations and handover corrections

### Lower-route `$31` spring rectangle

The unresolved visible rectangle is at world `(2112,832)`, object `OBJ_chaos_spring_49`.

The standalone `$31` spring PNG is already transparent. The stronger diagnosis is that the same layout cell is baked into the fully opaque terrain quadrant:

- terrain sprite: `SPR_chaos_terrain_2`
- world location: `(2112,832)`
- corresponding local terrain coordinate: `(64,832)`

The next fix must trace/regenerate the terrain/map composition so the block background follows the original background/transparent-plane rule. Do not manually paint over the rectangle, delete the canonical spring cell, or add a placement-specific cover object.

The thin lime rectangle visible with F3 is a separate debug overlay and should remain only when F3 is enabled.

### Animation/presentation limitations

- Spring and player roll animations remain visibly different from the ROM.
- Loop/twist traversal works, but the inherited presentation keeps Sonic rolling too often.
- The full original animation/state scheduler is not yet ported.
- Per-update physics must not be retuned to compensate for unverified PAL/NTSC or real-time cadence.

### Object/lifetime limitations

- Type `$21` was absent from POC 17.4 because its formal research was unfinished at the time. That blocker is now removed.
- POC 17.4's type-`$27` implementation predates the completed formal Task 02 audit. POC 18 should reconcile its implementation with the verified strict 64/384 boundaries, 129-update sequence, contact, orientation, and respawn behavior.
- Types `$1B` and `$26` have strong core state-machine evidence but incomplete formal generic lifetime/scheduler audits.
- Type `$18` goal-sign graphics are verified, but original completion/lifetime behavior is still partial. Do not replace completion logic with guessed signpost behavior.
- Type `$10` Task 04 is in progress; do not implement unmerged parameter/reward conclusions yet.

## POC 18 recommended scope

POC 18 should start from the current POC GitHub `main` and current reference GitHub `main`, then make a bounded integration pass.

Recommended order:

1. Synchronize both repositories and record both starting commit SHAs.
2. Treat POC 17.4 as the implementation baseline.
3. Fix the `$31` spring rectangle at the terrain-generation/compositing source, not in the standalone spring sprite.
4. Re-test moving and static spikes after the terrain regeneration.
5. Integrate type `$21` from the completed formal study using all six exact placements, parameters, graphics, animation reachability, contact, orientation and lifetime behavior.
6. Reconcile the existing type-`$27` POC code against the completed formal Task 02 study. Do not preserve earlier approximations where the research now gives exact behavior.
7. Preserve existing verified movement, loops, twist, springs and placements unless a change is directly required by the new research or Windows feedback.
8. Do not integrate Task 04 type-`$10` findings until that research has been reviewed and merged.
9. Do not guess type-`$18` completion behavior.

Prefer one coherent POC 18 archive over unrelated feature expansion.

## POC 18 acceptance checks

At minimum, Windows testing should verify:

- POC builds and reaches THZ1 from a fresh extraction.
- No cyan/green filled rectangle around the `$31` spring at `(2112,832)` with F3 off.
- With F3 on, only the expected thin sampled-tile debug outline appears.
- `$31` spring artwork, placement, launch direction and verified launch height remain unchanged.
- Adjacent canonical static spike cells still damage on floor contact.
- Moving spikes remain floor-aligned through their rise/retract cycle.
- All six type-`$21` placements appear at their exact ROM coordinates and use their exact parameters.
- Type `$21` patrol bounds, reversal, top-bounce/side-contact and defeat behavior agree with the reference fixtures.
- All three type-`$27` placements remain exact.
- Type `$27` uses strict <64 activation and >=384 removal behavior and does not acquire invented damage behavior.
- Existing first-ramp, loops, twist, springs, platforms, rings and monitors show no obvious regression.
- No fabricated objects, placements, graphics or completion marker are introduced.

If the pass is too large to diagnose cleanly, split the implementation into test archives while keeping POC 18 as the eventual accepted source milestone.

## Research queue after Task 04

Current census ordering, subject to Task 04 results:

1. type `$18` completion/lifetime study;
2. type `$09` parameter/entity-generation/collection study;
3. type `$28` formal platform subtype/rider/lifetime study, including command `$09`;
4. formal generic lifetime/scheduler completion for `$1B/$26/$28`;
5. broader animation-command interpreter completion;
6. later all-stage placement/layout/graphics expansion.

Update this file after reviewed research is merged or after an accepted POC milestone materially changes the integration state.

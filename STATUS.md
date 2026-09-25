# Sonic Chaos — project status

Updated: 25 September 2026

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

- 64 recovered ROM regions
- 12,240 recovered bytes
- 4,731 decoded instructions
- 37,622 controlled original-Z80 comparisons
- 524,288-byte byte-identical reconstruction
- SHA-256 matches the canonical ROM above

The current THZ1 census contains exactly 53 raw nine-byte object records across eight placed types.

| Type | Records | Current research status |
|---|---:|---|
| `$09` | 24 | graphics/animation decoded; behavior and relationship to layout-derived rings unresolved |
| `$10` | 5 | THZ1-reachable behavior formally complete; numeric parameter/reward effects verified; canonical identity remains non-verified |
| `$18` | 1 | dynamic goal-sign graphics verified; completion/lifetime behavior partial |
| `$1B` | 4 | retracting spikes; core state machine substantially verified |
| `$21` | 6 | THZ1-reachable behavior formally complete; canonical identity remains non-verified |
| `$26` | 4 | concealed/contact spring state machines substantially verified |
| `$27` | 3 | THZ1-reachable behavior formally complete; semantic identity unresolved |
| `$28` | 6 | moving-platform role verified; behavior partial; command `$09` decoded and all 15 animation states statically reachable |

Important census correction: the 24 raw type-`$09` placement records and the 142 separately decoded ring positions from THZ1 layout blocks are different source populations. No current evidence proves that one expands into the other.

## Research task tracker

### Task 06 — THZ1 Windows discrepancies: COMPLETE (POC 18.5 changes required)

The bounded audit is `docs/thz1-windows-discrepancies.md`; player state `$11`
is specified in `docs/player-state-11.md` and deterministic fixtures are in
`data/rom-cache/thz1/windows-discrepancies.json`.

- type `$10` uses placement Y directly and the reported gaps are canonical;
- parameter `$04` state `$11` is now implementation-ready;
- static block `$3D` is side-solid only in its lower 16 pixels and damages
  through its floor-contact handler, so POC's full-cell mask is incorrect;
- type `$21` is non-solid and uses fixed anchor extents, not animated bboxes;
  its shallow-top bounce ordering is canonical.

Task 06 adds three bounded regions (generic Y/X renderer, state `$11`, and
shared overlap), for 64 regions, 12,240 bytes, 4,731 instructions, and 37,622
controlled comparisons. POC 18.4 was inspected read-only at `acf154b7`.

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

### Task 04 — type `$10`: COMPLETE

Formal placement, state, contact, numeric reward, replacement and lifetime study.

Five THZ1 records:

- `(656,846,$06)`
- `(1712,494,$06)`
- `(336,270,$04)`
- `(1472,110,$04)`
- `(2688,686,$02)`

All records use flags/aux fields `$00`. Creation produces flags `$40` and one-based placement occupancy tokens 10–14.

Key verified behavior:

- four states are fully decoded; active and bottom-hit-airborne states alternate mapping frames `$0B/$0C`;
- runtime contact extents are horizontal 10 and vertical 24;
- player flag `$D503` bit 1 is mandatory for interaction; `$D532=$06` alone does not substitute;
- successful top/side interaction requires nonzero downward player Y velocity;
- top contact rejects requested player states `$0F/$10/$15/$1A`;
- bottom contact is independent of player Y direction: player Y becomes `+$0200`, object Y becomes `-$0200`, and object state 3 is requested without reward or consumption;
- successful top/side interaction queues the parameter-selected effect, adds score bytes `10 00 00`, converts the same slot to type `$0F`, and clears the placement token;
- no type-`$10` contact branch requests player damage;
- parameter `$02` queues `$D3A3` bit 1; dispatch increments BCD `$D299` up to `$99` and requests sound `$A9`;
- parameter `$04` queues bit 3; for player type `$01`, dispatch sets `$D532=$04`, timer `$012C` (or `$1770` at level `$08`), zeroes velocity, sets `$D373=$0700`, requests sound `$85`, and requests player state `$11`;
- for non-`$01` player type, initialization rewrites parameter `$04` to `$01`; that path queues bit 0 and adds BCD `$10` to `$D29A` before shared display/update calls;
- parameter `$06` queues bit 5; dispatch sets `$D532=$06`, timer `$0258`, `$D503` bits 1/7, requests sound `$84`, and allocates type `$05` parameter zero when newly selected;
- the parameter is also copied to dynamic graphics selector `$D3B3` on an off-screen-to-visible transition;
- type `$0F` supplies the direct replacement presentation using frames `$07/$08/$09`;
- untouched or bottom-hit-only objects retain their token; tracked off-range cleanup releases occupancy and allows respawn;
- successfully consumed objects clear the token while leaving the placement occupancy byte nonzero, so they do not respawn during the same loaded act.

Strict controlled overlap boundaries are verified at horizontal 18/19/20, top -23/-24/-25, and bottom 17/18/19.

Semantic status remains **SUPPORTED BUT NOT CANONICAL**. Do not assign user-facing names to parameters `$02/$04/$06`, sounds `$84/$85/$A9`, `$D299`, or `$D29A` without stronger evidence. Complete type-`$05` child behavior remains unresolved.

Task 04 added eight bounded recovered regions plus an extension of the existing player-state region. Current recovery totals are 61 regions, 11,709 bytes and 4,487 decoded instructions.

Primary study: `docs/object-10.md`.

### Task 05 — final THZ1 closure audit: COMPLETE (POC integration blockers remain)

The bounded audit is in `docs/thz1-closure-audit.md` with deterministic caches
`object-10-graphics.json` and `closure-audit.json`.

Key results:

- low selectors `$02/$04/$06` copy raw bank-`$0E` SMS tiles to `$0980`
  (six tiles, `$4C-$51`) and `$0BC0` (four tiles, `$5E-$61`);
- type `$10` frame `$0B` uses the first dynamic range in its top three pieces;
  frame `$0C` is fixed and neither active frame uses the second range;
- THZ1 sprite palette `$06` at ROM `$3B6AD` applies to both dynamic content
  and shell pieces, with index zero transparent;
- type `$05` parameter zero has 32 visible frames and persists while player
  selector `$D532` equals `$06`; POC 18.3 omits this visible effect;
- animation command `$09` is the four-byte form
  `FF 09 <offset> <value>` and performs `object[offset] = value`; type `$28`
  now has zero unresolved static animation states;
- census and recovery totals remain 53 records, eight placed types, 61 regions,
  11,709 bytes, 4,487 instructions and 37,451 controlled comparisons.

The audit conclusion is **THZ1 POC BLOCKED** for POC 18.3 as-is: the POC still
needs the now-reconstructed type-`$10` selected content and the bounded visible
type-`$05` selector-`$06` effect. No other established THZ1 discrepancy is a
blocker; remaining type `$18/$28` behavior and shared traversal scheduling are
documented adapters or future-fidelity work.

POC commit `231aeaf` also contains a non-ROM-backed custom ring Draw event while
its own verifier asserts that event file is absent. The rest of that verifier
passes when the contradictory absence assertion is isolated. Treat the custom
draw path as a documented POC presentation adapter and correct the POC verifier
during the next integration pass.

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
- type `$10`, `$21`, `$26`, `$27`, `$1B` relevant regions;
- direct type `$0F` replacement scripts/handlers and the type-`$10` numeric reward dispatcher;
- moving-platform code is recovered but not yet a complete formal object study.

Animation command semantics still not formally complete for commands `04,05,08,0A,0D`. Command `$09` is now verified as `object[offset] = immediate`; all eight placed THZ1 types have zero unresolved states under the supported static reachability pass.

## Current POC baseline

POC repository `main` currently points to commit:

`acf154b76b2145099c7c9155c280b660b96299ca`

Commit title:

`Sonic Chaos Act 1 POC 18.3`

The commit message was accidentally left as POC 18.3, but this commit contains
**Sonic Chaos Act 1 POC 18.4** and is the current Windows regression baseline.

Reference baseline recorded by the POC 18.4 handover:

- Task 05 reference `main`: `918b39b5f996ff9bfd553415e1319e5cb8c88d59`.

### POC 18.4 integrated state

Verified/research-backed integrations now present:

- type `$10`: five exact placements, ROM-derived active frames `$0B/$0C`, type-`$0F` replacement frames `$07/$08/$09`, numeric parameter effects, verified contact rules, and bounded occupancy/respawn behavior;
- type `$21`: all six exact placements, ROM-derived frames, signed 8.8 patrol movement, floor following, reversal, orientation, bounce/damage/defeat and bounded placement recreation;
- type `$27`: all three exact mirrored placements, strict <64 activation, exact 129-callback oscillation, strict >=384 removal, ordinary-contact stall and verified defeat/recreation behavior;
- type `$18`: five verified ROM-derived dynamic presentation frames at canonical room placement `(3960,558)`; the POC still uses a bounded pre-existing completion adapter rather than claiming original completion logic.
- Task 05 selector-dependent type-`$10` frame `$0B` graphics are integrated
  for parameters `$02/$04/$06`; frame `$0C` remains the shared fixed frame;
- the bounded 32-frame type-`$05` selector-`$06` presentation is integrated
  using the documented player-relative POC adapter;
- the contradictory ring-verifier assertion is corrected while retaining the
  accepted ring Draw adapter.

Terrain/presentation fixes now confirmed in the accepted POC:

- spring blocks `$30/$31/$33/$36/$38` are composed with contextual background rather than opaque cyan/black cells;
- the `$31` spring at world `(2112,832)` no longer shows the filled rectangle;
- ring-bearing layout blocks `$40/$41/$42/$43` no longer leave permanent flat ring artwork baked into terrain;
- all 142 separately decoded collectible ring objects remain present with their existing animation;
- type `$18` presentation is floor-aligned with a 22-pixel draw offset while preserving canonical room coordinates;
- F4-F7 debug warp shortcuts were removed; R restart and F3 diagnostics remain.

POC 18.4 automated verification reports:

- 15,660 movement-core fixture cases;
- all 112 twist dispatch entries;
- 1,078 twist entry/boundary cases;
- selected original-Z80 type `$26/$1B` checks;
- type `$27` initialization, acceleration, underflow and strict 383/384 removal checks;
- 21 canonical reference unit tests for `$10/$21/$27` plus animation reachability;
- canonical layout counts: 5 type-`$10`, 6 type-`$21`, 3 type-`$27`, 4 moving spikes, 4 static spikes, 6 platforms, 9 terrain springs and 142 separate layout rings;
- no legacy layout-monitor instances and no ROM file packaged;
- exact selector-dependent type-`$10` hashes, all 32 type-`$05` frames,
  selector-`$06`-only activation, and the corrected ring verifier all pass.

Windows testing confirms that the selector-dependent type-`$10` graphics and
selector-`$06` type-`$05` reward presentation function. Subsequent testing
exposed the Task 06 discrepancies: player state `$11` is missing, static
spikes retain a noncanonical full-cell collision approximation, and type `$21`
uses a GameMaker bbox/anchor approximation. The reported type-`$10` floating
placement is now verified canonical and must not be adjusted.

### Current THZ1 POC limitations

Immediate POC 18.5 blockers are:

- implement recovered player state `$11` for type-`$10` parameter `$04`;
- remove or bypass the full-cell THZ1 static-spike mask and use the decoded
  floor/side profiles and floor-hazard contract;
- replace type-`$21` animated GameMaker bbox contact with the recovered fixed
  player/object anchor and extent contract.

Accepted adapters or future-fidelity work remain:

- the type-`$05` player-relative presentation anchor is a documented POC adapter;
- original type `$18` completion/contact/lifetime logic remains partial; the POC completion trigger is explicitly an adapter;
- type `$09` raw records remain intentionally separate from the 142 layout-derived collectible positions until source evidence establishes a relationship;
- type `$28` retains a bounded platform adapter, although its former command-`$09` animation gaps are closed;
- full original animation/state scheduling remains absent, including some spring-flight and post-loop/twist presentation differences;
- generic lifetime/scheduler auditing for `$1B/$26/$28` is not as complete as the dedicated `$10/$21/$27` studies.

Task 06 is independently audited and accepted. Its totals remain 64 recovered
regions, 12,240 recovered bytes, 4,731 decoded instructions, 37,622 controlled
comparisons, and a 524,288-byte byte-identical reconstruction.

## Current research queue

With Task 06 accepted:

1. POC 18.5: implement recovered player state `$11`, remove or bypass the
   noncanonical full-cell THZ1 static-spike mask in favour of decoded collision
   profiles, and replace type-`$21` GameMaker bbox contact with the recovered
   fixed-anchor overlap contract.
2. Windows regression-test THZ1 and rerun the closure gate.
3. Resume non-blocking future-fidelity research: type `$18` completion,
   type `$09`, type `$28`, generic lifetime/scheduler work, remaining animation
   commands, and later stage expansion.

Update this file after reviewed research is merged or after an accepted POC milestone materially changes the integration state.

# Natural one-ring hurt: separation and the left-boundary exception

## Finding

The vertical first ring is correct. Ordinary natural hurt separates Sonic from it
through the player's **-1 px/update horizontal knockback**, not through ring randomness.
The current shipped POC preserves that separation on unobstructed flat ground.

Stationary repeated recollection **is reproducible in the original ROM** near the
left viewport clamp. The POC reproduces the same exception. Consequently this
audit does not establish a causal ROM/POC divergence that would justify changing
scatter, pickup lockout, pickup geometry or adding randomness.

James's observation that this does not *normally* happen is consistent with the
ROM. If his POC reproduction was in the arena interior rather than against its
left clamp, that particular reproduction remains unresolved; these controls do
not reproduce it there.

## Provenance and method

ROM verified by `rom.load`: Sonic Chaos (Europe) v1.2, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Research main inspected at `89641f8093e62401cd81f94e6ac889422f600472`;
working branch started from `4380b6c` (subsequent final-zone research documentation).

POC documentation's active cleanup workspace is P2 at `d4705ce` and contains no
AQZ3 boss. The actual P4 workspace is `../SonicChaos_POC_aqz_p3`, branch
`poc/aqz-p4-boss-59-5d`, base `1b089a5`, with existing uncommitted P4 changes.
Both were inspected; the P4 shipped GML was executed read-only via its existing
`verification/chaos_world_harness.js`. No POC files were edited.

Evidence:

- **Emulated original game:** `tools/natural_lost_ring_hurt.py` boots AQZ3,
  parks Sonic while the original boss reaches a contact opportunity, then releases
  him permanently with one ring. The boss is never rewritten. Its actual body
  contact, projection and damage request execute. No player writes follow release.
  Detailed callback/phase trace: `data/rom-cache/natural-lost-ring-hurt.json`.
- **Emulated original game with controlled placement:**
  `tools/natural_lost_ring_controls.py` places an actual state-0 `$5D` projectile
  once, then lets its original initializer/contact and the entire original player
  and object scheduler run. This is an explicit shot-placement fixture, **not a
  claim of natural projectile birth**. Camera reference is held fixed. Flat control
  uses AQZ3's ordinary block `$01` across a flat row at WORLD Y256 and removes
  unrelated mapped objects before player passes; arena controls retain the actual
  AQZ3 layout. No player pinning occurs. Boundary cases receive a second projectile
  fixture after immunity expires; neither rings nor player positions are reset.
  Trace: `data/rom-cache/natural-lost-ring-controls.json`.
- **POC shipped code:** `tools/natural_lost_ring_poc.js` executes the actual `$5D`
  forced-contact helper, contact promotion, damage gate, hurt movement, adapter,
  ring phase and terrain. This isolates the hit rather than claiming a whole boss
  fight replay. It tests flat terrain and AQZ3 at X1743,1750,1800,1856, no input or
  player pinning. Trace: `data/rom-cache/natural-lost-ring-poc.json`.

## Complete sequence

U0 means the update executing `$48F7`; object-phase contact happened in the prior
update. The controlled original shot starts at scheduler update 1, requests damage
at update 2, and `$48BC -> $48F7` executes at update 3 (U0).

1. Actual object contact publishes `$D520/$D521` and forced damage `$D3B0`.
   The player damage gate consumes the request on the following player pass.
2. `$48F7` sees one BCD ring. `$4915..$4937` allocates one type `$06`, token 0,
   through the first-free-slot allocator `$5E9C`. It then resets `$D29A` to zero,
   refreshes the HUD and requests hurt sound `$A4`.
3. `$4942/$494F` set immunity 120, request player `$1E`, set airborne/hurt bits,
   clear floor, write Y speed -4, and X speed -1 (left-wall bit can select +1).
   This depends on wall contact, not the hazard side or facing.
4. The same update's object scheduler runs the new ring's initializer `$9A2B`.
   It reads the final player anchor: X=playerX, Y=playerY-16, vx=0, vy=-5.
   There is no ring movement in U0. Natural boss hit observed at (1855,238):
   ring initializes at (1855,222), player vx=-256, vy=-1024 in 8.8 units.
5. Player `$1E` callback `$03AA -> $3A71 -> $3FEF` runs on subsequent updates.
   Its horizontal input routine returns for states >=$1E, preserving knockback.
   Dry gravity is +48/256. With free space, Sonic moves left each update.
6. Ring U1..U16 callbacks are `$9A9E`: +32/256 gravity, motion and terrain tests;
   no pickup test. At U16 the player is 16 pixels left of ring 0.
7. U17 first runs `$9A98`: pickup sees the ring's pre-motion position and the
   player's post-player-phase position. Free-space Sonic is now 17 pixels left,
   already outside the inclusive 11-pixel horizontal pickup reach. Natural trace:
   Sonic (1838,198), ring (1855,159) before its U17 movement.
8. Flat/arena hurt lands at U43. Ground motion then brakes the remaining -1
   speed. The original interior control settles 49 pixels left of its spawn.
9. With no pickup, token 0's first floor rebound is U83, vy=-3.5. At U81 its
   pre-motion Y is playerY-11; an aligned player would collect it **before** that
   rebound. Interior Sonic's horizontal separation prevents this.

## Results

| One-ring case, no input after hit | Original | Current POC |
|---|---|---|
| Flat, interior X1000 | Separates; no recollection | Separates; no recollection |
| AQZ3 interior X1856 | Settles X1807; no recollection | Separates; no recollection |
| AQZ3 X1800 | Not separately controlled | Separates; no recollection |
| AQZ3 X1743 (camera1727, left edge+16) | Clamp settles X1744; collects U81 | Clamp holds X1743; collects U81 |
| AQZ3 X1750 | Clamp settles X1744; collects U81 | Clamp holds X1743; collects U81 |
| Second boundary hit after immunity | One ring lost again, recollected U81 after second hurt | Same |

Original repeated-boundary ring transitions are scheduler updates
`3:1->0, 84:0->1, 133:1->0, 214:0->1` with no intervening player movement
instructions. Each pickup consumes that `$06` and starts its sparkle; the next
damage emits a **new** `$06`. It is not collecting one object multiple times.

## First divergences and minimal correction

At the boundary, the first position/velocity divergence is U1: the original
pre-movement viewport clipping allows Sonic X1742 with vx=-1, then its compensated
left clamp settles X1744. The POC's documented post-movement full-width clamp
immediately holds X1743 and zeroes vx. This is an existing GameMaker viewport
adapter; both outcomes remain within 11 pixels of the ring. Making that clamp
byte-exact would **not prevent recollection**.

In the unobstructed shared hurt path, entry velocities, scatter origin, lockout
and horizontal movement agree. A concrete state-response difference is U43:
`SCR_cc_hurt_tick` explicitly writes vy=0 on landing, whereas original `$3A71`
requests walking through `$45CE` and retains the terrain pass's +1040/256 Y speed.
The next grounded player update forces +7 in either case. A minimal canonical
state correction is to remove that extra landing `vy=0` write while retaining
the recovered floor/walking transition. This is **not a fix for stationary ring
recollection**, and no POC correction was applied during this research audit.

For the reported ring issue, the canonical recommendation is **no scatter change**.
There is no evidence for randomness, a new hurt-state pickup prohibition or an
extended lockout. An interior Windows reproduction would require its actual
player/camera/contact trace to identify a different first divergence; do not
present either incidental difference above as its proven cause.

## Reproduction and validation

From the research workspace, using Python 3.13 with the existing Z80 packages:

```text
python tools/natural_lost_ring_hurt.py "../source/Sonic Chaos (Europe).sms"
python tools/natural_lost_ring_controls.py "../source/Sonic Chaos (Europe).sms"
node tools/natural_lost_ring_poc.js
python -m unittest discover -s tests -p test_natural_lost_ring_hurt.py
python -m unittest discover -s tests -p test_player_hurt_ring_scatter.py
```

Three focused regression tests and all 38 accepted scatter tests pass with the
verified local ROM. Tests lock the natural first eligible callback, free-space
separation, first floor bounce and repeated boundary recollection in both engines.
No Windows/IDE execution was performed; POC results are shipped-code harness
results, not Windows acceptance.

AGENTS candidate update: Ordinary one-ring hurt separates Sonic via player
knockback. Stationary recollection at U81, including a second hit after immunity,
is canonical near the left clamp; do not randomize token 0 or change pickup gates.

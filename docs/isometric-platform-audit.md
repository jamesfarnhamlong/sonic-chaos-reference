# Gigapolis isometric platform / surface audit

Scope: canonical **Sonic Chaos (Europe) v1.2**, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
This is a Research result. No POC file was changed.

The exhaustive machine-readable result is
`data/rom-cache/isometric-platform.json`; `tools/isometric_platform.py`
rebuilds it from the verified ROM. Evidence labels below distinguish decoded
data, byte-verified code, controlled original-routine execution and selected
whole-game emulator traces.

## 1. Exact identity: two mechanisms, not one

The apparent Gigapolis isometric/platform presentation combines two independent
mechanisms:

1. **Terrain surface `$1C`, blocks `$8C..$97`**. These 32x32 layout cells are
   collision-only: their decoded GPZ mappings contain zero non-background
   pixels. They form the broad perspective/isometric decks in all three GPZ
   acts. They are always-present terrain, not mapped objects. **[DECODED DATA +
   CONTROLLED ROUTINE RESULT]**
2. **Mapped object type `$28`, parameter `$83`**. The parameter initializes
   type `$28` state 4, a top-supported platform which sags once, waits, then
   falls. Its first normal-act appearance is the single GPZ2 placement at
   `(1584,384)`. This is the mechanism later reused extensively in Mecha Green
   Hill. **[DECODED DATA + BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT]**

The systems are not a hybrid. Across all 18 normal acts there are 32 state-4
`$83` placements and none has surface `$1C` in its sampled terrain context.
Surface `$1C` appears only in GPZ; `$83` also appears in SEZ, MGHZ and EEZ.

## 2. Terrain surface `$1C`

### Placement census

Every cell is recorded as layout index, cell coordinate, world coordinate and
block ID in the JSON. The complete census is:

| Act | `$1C` cells | Block range |
| --- | ---: | --- |
| GPZ1 | 212 | `$8C..$97` as listed in the cache |
| GPZ2 | 116 | `$8C..$97` as listed in the cache |
| GPZ3 | 90 | `$8C..$97` as listed in the cache |
| all other normal acts, including MGHZ1/2/3 | 0 | — |

Total: **418 cells**. The ordered `(act, cellX, cellY, block)` census hashes to
`e057b15a3c699ce51aa9105fc2133d3911d5d57740e82b42d1a23588df572bc7`.
This makes the JSON the exact placement manifest without duplicating 418 rows
in prose. **[DECODED DATA: all 18 normal-act layout streams]**

### Block definitions and graphics relationship

All twelve blocks have header flags `$9C` (solid bit 7 plus low-five-bit
surface ID `$1C`) and modifier 0. Their mapping table is the GPZ block table at
ROM `$45640`. Mapping attributes are nonzero, but after the GPZ art streams are
decoded every one of the 1,024 pixels in every block is palette index 0. The
collision is therefore registered over background/perspective presentation;
there is no foreground collision sprite and no object anchor. **[DECODED DATA]**

The vertical floor contours are:

| Blocks | Effective height by local X | Floor row in the 32px cell |
| --- | --- | --- |
| `$8C..$8F` | 16 throughout | 16 |
| `$90` | 1,1,2,2,…,8,8 then 8 through X=31 | 31 down to 24 |
| `$91,$92` | 8 throughout | 24 |
| `$93` | mirror of `$90`: 8 down to 1 | 24 down to 31 |
| `$94..$97` | raw `$54`; effective 32 under the `$1C` rule | 0 |

The key special case is CPU `$6F8E`: when the **previous** surface low five
bits are `$1C` and the sampled vertical byte has bit 6, the effective height is
forced to 32 rather than using raw `$54 & $3F == 20`. This is ordinary terrain
projection with a surface-specific continuation rule; surface dispatch `$6A5B`
itself is only `RET`. **[BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT]**

Horizontal profiles and side behavior are not uniform:

| Blocks | Horizontal profile | Isolated original-routine result |
| --- | --- | --- |
| `$8C..$93` | `$40` throughout (extent 0) | no side projection |
| `$94..$96` | `$60` throughout (extent 32, right-oriented) | side projection while the side probe is at local Y 0..15 |
| `$97` | `$20` at Y 0..23, then 0 | side projection at local Y 0..23 |

The side ranges reflect the whole original `$690B` terrain pass and its
`(playerX±9, playerY+6)` probes, not a box synthesized from the floor line.
The isolated rising/underside sweep also records the original ceiling response:
`$8C..$93` alter rising motion for ceiling-probe rows 27..31; `$94..$97` do so
for rows 15..20. The response projects Sonic and changes rising `-$0100` to
falling `+$0100`; these cases do not leave the persistent ceiling flag set.
There is no hazard callback. **[15,537 CONTROLLED ROUTINE CASES]**

### Projection, traversal and player states

Surface `$1C` uses the standard terrain probes and standard projection order:

`state callback / movement -> floor projection -> side probes -> ceiling probe -> surface dispatch -> terrain-ring probe -> merged contacts`

The terrain pass happens inside the player's update. Mapped objects, including
type `$28`, update afterwards. A surface `$1C` deck therefore never claims the
object support owner `$D3C0`, never carries the player and has no independent
movement or lifecycle. **[SOURCE-TRACED + EMULATED ORIGINAL FRAME]**

The `$90/$93` contours are ordinary height-profile slopes. They do not use a
separate isometric coordinate transform: player projection is vertical to the
decoded height at the foot-probe X, with ordinary side/ceiling probes where the
horizontal/vertical profiles allow them. Modifier 0 means the surface contributes
no conveyor/surface-speed delta.

The controlled matrix covered standing, walking, running, rolling, jumping,
upright spring, falling, state `$0F`, rocket shoes `$11`, spring shoes `$12`,
diagonal spring `$1C`, act-clear `$20` and twist `$22`, with rising/zero/falling
Y speeds. Surface interaction is governed by the normal state's decision to run
the terrain pass and by the usual rising/falling gates; surface `$1C` contains
no state-specific attack, shoe, spring or damage branch. Selected whole-frame
traces show ordinary fall, rolling, and a correctly provisioned state `$11`
crossing the long GPZ1 `$8D` deck with no object owner. States which skip the
ordinary terrain pass elsewhere remain governed by that existing state rule;
`$1C` does not override it. **[CONTROLLED ROUTINE RESULT + EMULATED ORIGINAL
FRAME]**

## 3. Type `$28`, parameter `$83` (state 4)

### Identity, anchor and mapping

The initializer at `$8585` computes `(parameter & $3F)+1`, except low-seven-bit
values 5 and 11 are forced to state 13. Thus `$83` is state 4, not state 3.
Parameter bit 7 sets the shared weight/sag flag; bit 6 is clear. `aux0=$6A`
selects the platform tile base. State 4 does not consume `aux1`; its differing
GPZ/MGH/EEZ values are not behavior parameters. **[BYTE-VERIFIED ASSEMBLY]**

The canonical gameplay anchor is the mapped object's `(worldX,worldY)`. Type
`$28` uses shared mapping `$9217` (ROM `$3D217`), frame 1, four 8x16 pieces at
relative X `-16,-8,0,8`, relative Y `-16`, tile offsets `0,2,4,6`. The mapping
box is X `-16..15`, Y `-16..-1`.

GPZ loads six tiles at VRAM `$0D40` from ROM `$262C0`; only relative X
`-16..7` is opaque. MGHZ loads eight tiles at the same destination from ROM
`$26470`; X `-16..15` is opaque. With the original sprite renderer's +18 Y
placement, both have opaque Y `anchor+2..anchor+17`. Their decoded art hashes
and palette selectors differ, but the mapping, anchor, state, callback and
collision do not. **[DECODED DATA]**

### Support geometry and carry

Let `dx = playerX-platformX` and `dy = playerY-platformY`. State 4 calls the
same `$8814/$6328` support path as other type `$28` platforms:

```
-16 <= dy <= -1
abs(dx) <= 8 + abs(dy)
signed platformYSpeed <= signed playerYSpeed
support owner is zero or already this platform
```

All boundaries are inclusive. This is a triangle, widening from X `-9..9` at
`dy=-1` to `-24..24` at `dy=-16`. The exhaustive state-4 sweep covered 6,565
geometry points plus timing/state/lifecycle probes. **[CONTROLLED ROUTINE RESULT]**

Only the “player above” overlap class supports. Side and underside overlap can
set the temporary contact classification but does not project, stop, damage or
trigger the platform. Attack posture, current/requested player state, floor flag
and player airborne bit do not affect support. The player-speed gate is the only
state-like gate: a stationary platform rejects a player with negative Y speed
and accepts zero or positive Y speed. This was checked for standing, walking,
running, rolling, jump, `$0B`, fall, rocket shoes, spring shoes, diagonal spring,
act-clear and twist, with attack clear/set. **[CONTROLLED ROUTINE RESULT]**

Carry sets player Y to `platformY-14`, preserving the player's fractional Y,
and adds this update's platform X delta. State 4 has no X motion, so its X carry
is zero. Neither player X/Y velocity nor player state is cleared or replaced.

### Trigger, sag, delay and fall timing

On the first accepted top support:

- phase `+$27` becomes `$80`;
- script timer `+$1E` loads `$50` (80);
- because `$83` has bit 7, the shared sag begins immediately.

The trigger update does not decrement the timer. The next 80 callbacks count it
down. Phase becomes `$FF` on update 81. Gravity begins on update 82, adding
`$0030` (48/256 px/update) to platform Y velocity before position integration;
the first integer falling-Y change is update 84. **[CONTROLLED ROUTINE RESULT]**

Sag is independent of the later fall: updates 0..7 move one pixel per update to
home+8; update 8 holds; updates 9..16 recover one pixel per update to home, even
while Sonic remains supported. It then stays at home through the rest of the
delay. During delayed/sag operation, contact is tested at the pre-sag Y and carry
uses the post-sag Y. During falling operation, gravity and movement occur first,
then support/carry use the post-move Y. The selected GPZ2 whole-frame trace shows
creation, state-4 initialization, support-owner claim, the eight-pixel sag,
recovery, `$80->$FF`, accelerating fall and carry. **[CONTROLLED ROUTINE RESULT
AND EMULATED ORIGINAL FRAME]**

### Lifecycle

State 4 uses the generic camera-relative mapped-object lifecycle; it does not
call the type `$28` moving-platform keep-alive helper. Canonical bands are the
normal visible/awake/sleep/delete bands documented in
`docs/viewport-semantics-audit.md`.

While untriggered (phase 0), the inactive callback returns and ordinary removal
can release/recreate the placement. If a triggered platform (phase `$80` or
`$FF`) becomes inactive, `$8719` sets `+$3F=$80`, clears its placement tracking
token `+$3E`, and changes type to `$FE`. Because cleanup no longer has the token,
the placement occupancy remains consumed: the fallen platform cannot respawn
during that act. **[BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT]**

There is no attack or hazard behavior. The object has no spring/shoe special
case; those states matter only through their current anchor and signed Y speed.

## 4. Reuse manifest

### Gigapolis: all type `$28` variants

| Act | Placements `(parameter @ X,Y; aux1; state)` |
| --- | --- |
| GPZ1 | `$89 @ 1648,320;0E;s10`; `$89 @ 2896,448;0C;s10` |
| GPZ2 | `$05 @ 1632,800;18;s13`; `$83 @ 1584,384;0B;s4`; `$0A @ 2512,640;0B;s11` |
| GPZ3 | `$89 @ 912,80;0B;s10` |

The one `$83` row is at ROM `$70B88`. `aux0` is `$6A` for every row above.

### Mecha Green Hill: all type `$28` variants

| Act | `$83` placements | Other type `$28` variants |
| --- | --- | --- |
| MGHZ1 | `(752,736) (912,768) (1072,800) (1232,800) (1968,768) (2064,736) (2160,736)` | `$89@(1360,750),aux1=12`; `$05@(1136,240),07`; `$05@(2768,414),0C`; `$05@(2960,830),1C` |
| MGHZ2 | `(848,608) (1072,608) (1264,608) (1392,608) (3056,736) (3312,800) (3792,800)` | `$0A@(304,496),0A`; `$0A@(648,464),12`; `$05@(2768,624),19`; `$05@(3024,560),14`; `$05@(3856,768),10` |
| MGHZ3 | `(528,352) (592,384) (656,416) (720,448) (784,480) (848,512) (2160,640) (2288,640) (2416,640) (2544,640) (2672,640)` | none |

All 25 MGHZ `$83` rows have `aux0=$6A`, `aux1=$6A`. Their behavior is exactly
the GPZ2 state-4 behavior. The change is **presentation-only**: MGHZ supplies a
different eight-tile art stream and palette in place of GPZ's six-tile stream.
MGHZ has no terrain surface `$1C` cell. **[DECODED DATA + SHARED CODE IDENTITY]**

### Other appearances

Parameter `$83` also occurs at:

- SEZ1: `(784,384)`, `(1904,896)`;
- EEZ1: `(400,416)`, `(400,192)`, `(2160,800)`;
- EEZ3: `(784,752)`.

No other act uses terrain surface `$1C`. The JSON reuse manifest also includes
every non-`$83` type `$28` placement in all 18 normal acts, rather than silently
equating the whole object type with the audited state-4 variant.

## 5. POC readiness (read-only)

The active POC checkout was inspected only; it already contained unrelated,
uncommitted THZ3 boss work and was not modified.

Reusable as-is:

- `SCR_chaos_core.gml` already contains the exact `$1C` bit-6 floor special
  case (`raw bit 6 && previous surface == 28 -> height 32`) and the generic ROM
  vertical/horizontal profile pipeline. Surface `$1C` therefore needs decoded
  GPZ layout/header/profile data and transparent collision cells, **not a new
  collision algorithm**.
- `SCR_chaos_platform.gml` already has the canonical type `$28` triangular
  contact, signed relative-speed gate, support ownership and carry helpers.
- the canonical type `$28` placement importer/spawner and the shared
  player-before-object phase ordering can be reused.
- the existing viewport vocabulary/lifecycle adapter is the right integration
  point; canonical placement and collision anchors must remain unchanged.

Genuinely new POC runtime/presentation support:

- add an explicit type `$28` **mode/state 4** for parameter `$83`: one-time
  8-pixel sag/recovery, 80-count delay, `$0030` gravity, post-move support and
  permanent placement consumption after triggered offscreen removal;
- import GPZ/MGH type `$28` variants without routing unknown parameters through
  the current state-5 fallback;
- install zone-specific type `$28` platform art/palettes. GPZ's 24-pixel opaque
  width and MGHZ's 32-pixel width are presentation facts; collision remains on
  the common anchor/triangle;
- add GPZ/MGH canonical data packages (layout width, block mappings, collision
  headers/profiles, placements). No hand-authored visual offset may alter the
  collision anchor.

## 6. Reproduction and unresolved items

Run the focused audit and tests with the repository environment:

```text
.venv/Scripts/python.exe tools/isometric_platform.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe -m unittest tests.test_isometric_platform -v
```

Unresolved, deliberately bounded:

- The ROM does not name the design-level semantic reason for registering these
  transparent collision cells over the GPZ perspective background. The numeric
  identity, placement and runtime behavior are established.
- The selected whole-frame traces use the project's approximate SMS harness.
  Visible-playback confirmation remains useful for presentation acceptance, but
  no collision, timing or reuse conclusion depends on an inferred screenshot.

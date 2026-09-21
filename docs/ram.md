# RAM reference checked in Chaos

Little-endian words unless stated otherwise. Addresses are absolute RAM addresses for the player at IX=`$D500`. Other objects use the corresponding relative offsets where the original routine permits it.

| Address | Size | Meaning | Evidence |
|---|---:|---|---|
| `$D100` | 1 | Current sampled header's modifier byte | `$76F1`, `$7090` |
| `$D12B` | 1 | Saved slot-2 bank number | `$7666` |
| `$D137` | 1 | Direction input snapshot; physics masks bits 2/3 | `$4178` |
| `$D168` | 2 | Pointer to level row-offset table | `$76AF` |
| `$D16A` | 2 | Negative map row width | `$7066` |
| `$D174` | 2 | Horizontal camera offset used by movement bounds | `$4148` |
| `$D297/$D298` | 1 each | Level/act index | `LoadRingArtPointers`, `$4B46` |
| `$D2E0` | 2 | Collision-header pointer table address | `$76D2` |
| `$D353` | 1 | Most recently queried tile ID | `$76CA` |
| `$D354` | 2 | Address of queried tile in decoded layout | `$76C7` |
| `$D358` | 2 | Adjusted query X | `$7679` |
| `$D35A` | 2 | Adjusted query Y, including +18 anchor correction | `$769B` |
| `$D364` | 1 | Newly sampled surface flags/type | `$76DB` |
| `$D367` | 1 | Horizontal projection sample, indexed by Y | `$7718` |
| `$D368` | 1 | Vertical projection sample, indexed by X | `$7705` |
| `$D369` | 1 | Current floor speed-modifier byte offset | `$691A`, `$6FB7` |
| `$D36A` | 1 | Previous floor modifier | `$691D` |
| `$D36B` | 1 | Current floor tile, preserved across later side queries | `$6955` |
| `$D36C` | 1 | Previous surface for projection; replaced afterward | `$6F61`, `$6961` |
| `$D373` | 2 | Maximum horizontal speed field | `$366C`, `$404D` |
| `$D375` | 2 | Input/friction velocity increment | `$41B4`, `$402D` |
| `$D377` | 2 | Surface velocity increment | `$41C5`, `$4032` |
| `$D39D..$D39F` | 3 | Loop path cursor, eight fractional bits | previous `loop_states.asm` |
| `$D443` | 1 | Water condition used by movement | `$40C1`, `$4BC0` |
| `$D498/$D49A` | 2 each | Left side probe X/Y offsets | `$3686`, `$7210` |
| `$D49C/$D49E` | 2 each | Right side probe X/Y offsets | `$3686`, `$716B` |
| `$D500` | 1 | Object type; Sonic=1 | `$3686` |
| `$D501` | 1 | Current player state | `$6508` |
| `$D502` | 1 | Requested player state | `$6517`, state setters |
| `$D503` | 1 | Movement flags; bit 0 airborne, bit 1 rolling/attack posture | `$45ED`, `$47FB` |
| `$D50A` | 1 | Direction/angle in relevant movement states | `$6089` |
| `$D50B` | 1 | Magnitude in angle-driven movement | `$6096` |
| `$D510` | 1 | X fractional byte | `$407B`, `$60FB` |
| `$D511` | 2 | Integer X | `$7672` |
| `$D513` | 1 | Y fractional byte | `$412F`, `$611B` |
| `$D514` | 2 | Integer Y anchor | `$7689` |
| `$D516` | 2 | Signed 8.8 X velocity | `$402A` |
| `$D518` | 2 | Signed 8.8 Y velocity | `$4097` |
| `$D521` | 1 | Object-contact flags merged conditionally | `$64E1` |
| `$D522` | 1 | Background contact: bits 0 ceiling, 1 floor, 2 right, 3 left | `$715E`, `$6FAD`, `$7452` |
| `$D523` | 1 | Combined contact flags | `$64EC` |
| `$D524` | 1 | Special terrain flags; interpretation incomplete | `$6FBB` |
| `$D525` | 1 | Collision plane / alternate-header selection | `$76E3`, `$73A7/$73B8` |
| `$D538` | 1 | Twist dispatch variant | bank 12 `$94D1` |

`$D3C0`, several `+$24` paths, animation counters, and object-contact field details need further tracing. Numeric addresses are not evidence of equivalent meanings in Sonic 2 or Game Gear Chaos.

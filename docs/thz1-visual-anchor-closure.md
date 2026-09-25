# THZ1 final visual / anchor closure

This Task 07 report is bounded to type `$21` grounding, normal-Sonic state
`$11` frames `$38/$39/$3A`, and the background around the two type-`$10`
parameter-`$04` placements. POC commit `726b16eafbc92d4240fa182bb6ef699cfbcf923a`
was inspected read-only. Windows gameplay observations identify symptoms only.

## Final answers

- **TYPE `$21` SIDE-BOUNCE WINDOWS BUG — ROOT CAUSE PROVEN.** The POC omits the
  original generic lookup's `+18` Y probe, so its object anchor settles 18
  pixels too low and ordinary standing contact crosses the bounce split.
- **STATE `$11` GRAPHICS — IMPLEMENTATION READY.** Frames `$38/$39/$3A` have
  exact mappings, distinct dynamic art, palette, origin and hashes.
- **TYPE `$10` VISIBLE FLOATING — CANONICAL VISUAL APPEARANCE.** Both POC
  platform regions exactly match ROM-rendered pixels at the same coordinates;
  no 16-pixel terrain registration or composition error exists there.

## A. Type `$21` object-floor anchor

The source-traced path is `$B268 → $0320 → $77CB → $7666 → $70E7 →` the
`$77ED` object-floor dispatch. `$77CB` supplies zero BC/DE offsets. At `$7690`,
`$7666` adds `$0012` to object `+$14/+$15` only for lookup. `$70E7` subtracts
the profile correction from the original field. Thus `+$14/+$15` remains the
integer world/render/contact anchor; the probe is `anchor + 18`.

Controlled original-routine results after the first `+$0200` integration:

| Placement | Integrated Y | Probe Y | Tile | Surface Y | Stable object Y | Piece Y bounds | Bounce split | Standing Sonic Y | Result |
|---|---:|---:|---:|---:|---:|---|---:|---:|---|
| `(800,606)` | 608 | 626 | `$0B` | 608 | **590** | 558..589 | 586 | 590 | DAMAGE |
| `(1248,862)` | 864 | 882 | `$0B` | 864 | **846** | 814..845 | 842 | 846 | DAMAGE |
| `(2048,318)` | 320 | 338 | `$01` | 320 | **302** | 270..301 | 298 | 302 | DAMAGE |
| `(3152,894)` | 896 | 914 | `$01` | 896 | **878** | 846..877 | 874 | 878 | DAMAGE |
| `(3296,286)` | 288 | 306 | `$01` | 288 | **270** | 238..269 | 266 | 270 | DAMAGE |
| `(2400,254)` | 256 | 274 | `$A3` | 256 | **238** | 206..237 | 234 | 238 | DAMAGE |

The 16-pixel change is exact: integrate down two, probe another 18 down, then
project the anchor to `surface - 18`, netting `placement - 16`. The old 590 and
238 examples are re-verified, not pre-adjusted placements.

POC `SCR_chaos_object_floor_project(x,y)` instead looks up `(x,y)`. The minimal
correction is `SCR_cc_lookup(floor(x),floor(y)+18,0)`, while applying its
correction to the unshifted anchor Y. Do not alter the type-`$21` inequalities.
The helper is used only by types `$10` and `$21`, and both original callbacks
use `$77CB/$7666`, so the fix is valid generically for this helper.

The cache includes six grounding traces and combined fixtures for `(800,606)`
and `(2400,254)` that ground both anchors, retain horizontal overlap within
±20, and require lower-side **DAMAGE**.

## B. State `$11` graphics

See [player-state-11-graphics.md](player-state-11-graphics.md). The frame IDs
use mapping records `$83E9/$83F4/$83FF`, shared six-piece geometry, three
distinct 384-byte runtime loads, palette `$06`, and a 24×32 canvas with origin
`(16,32)`. Facing left is an ordinary mirror; physics need not change.

## C. Type `$10` background registration

The deterministic chain is layout stream ROM `$48000` → 128×32 block layout →
block-pointer table ROM `$44000` → 16 VDP attributes per 32×32 block → primary
tile stream ROM `$40F9E` at VRAM tile `$0C0` → background palette `$15`.
Flip bits, tile IDs and palette attributes are cached.

At X=336, world cell `(320,288)` is block `$01`; the first platform pixels at
the object X begin at collision surface Y=288. Stronger body colours develop
within the following decorative rows, explaining the lower perceived top. POC
and canonical pixels for X `288..383`, Y `256..335` share RGBA SHA-256
`bec00c782efa5af7dfab5e866cf05e3a85b846d916ea670473e3db89341916c0`.

At X=1472, world cell `(1472,128)` is block `$01`; platform pixels begin at
surface Y=128. POC and canonical pixels for X `1424..1519`, Y `96..175` share
RGBA SHA-256
`9c4c42947e5bd6d57849617f8bbf7f81b130d1025dc815dd9101a99199db236e`.

Wider requested patches differ only where POC deliberately removes layout-
embedded ring blocks `$40/$41` and creates collectible objects. Those rows are
above the tested platforms and do not translate them. There is no layout,
metatile, tile-crop, quadrant-canvas, layer-origin or room-origin offset to fix.
Moving either type `$10` would be incorrect.

## Evidence and POC 18.6 recommendations

Evidence labels are explicit in the JSON: byte-verified/source-traced code,
controlled original-routine traces, deterministic graphics reconstruction,
and POC read-only implementation/pixel comparison. Windows behavior remains a
gameplay observation, not ROM evidence.

1. Add `+18` only to lookup Y in `SCR_chaos_object_floor_project`; preserve the
   unshifted anchor and all type-`$21` contact comparisons.
2. Import the three 24×32 state-`$11` images at origin `(16,32)`, retain the
   numeric cadence, and use normal horizontal mirroring.
3. Make no type-`$10` coordinate or THZ1 background registration change.

## Verification totals

Task 07 adds eight formally counted controlled comparisons (six grounding and
two combined grounding/contact calls). It does not declare new recovered
regions. Final totals are 64 recovered regions, 12,240 recovered bytes, 4,731
decoded instructions, and 37,630 controlled comparisons. Full assembly
reconstruction remains byte-identical across all 524,288 bytes with canonical
SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.

# THZ1 object graphics and animation reachability

This note records the Turquoise Hill Act 1 object-graphics work performed after
the initial graphics-stream map. ROM-derived PNGs and tile bytes remain local
under `build/` and are not committed.

## Validation anchors

The sprite-mapping extractor must reproduce the existing mappings for object
types `$21`, `$26`, `$27` and `$28` before analysing other types.

The animation parser is separately anchored by two recovered objects:

- `$1B` retracting spikes: state table `$AC4A`; every state reaches mapping
  frame `$0E`.
- `$26` spring: state table `$8212`; reachable mapping frames are
  `$00/$01/$02/$03`.

These checks prevent a shared mapping catalogue from being mistaken for one
object's complete animation.

## Shared mapping catalogue

Types `$09`, `$10` and `$1B` all use mapping table `$8C71` (ROM `$3CC71`), but
their animation scripts select different entries:

| Type | Animation table | Reachable mapping frames | Identity |
|---:|---:|---|---|
| `$09` | `$9BC8` | `$00-$06` | ring / sparkle family |
| `$10` | `$A101` | `$00`, `$0B`, `$0C` | monitor / item box |
| `$1B` | `$AC4A` | `$0E` | retracting spikes |
| `$27` | `$8947` (bank `$1E`) | `$00-$02` | semantic name open; flying-object behavior recovered |

The identities for `$09` and `$10` come from the reconstructed reachable
graphics; `$1B` is additionally supported by recovered spike state handlers.

## Type `$18`: dynamic goal-sign graphics

Type `$18` uses mapping `$8EAE` (ROM `$3CEAE`) and animation table `$A7BC`.
Its reachable mapping frames are `$00-$05`.

Rendering those frames against the ordinary THZ1 VRAM image produces unrelated
object fragments because type `$18` dynamically replaces the tile range before
display.

Its state logic writes selector `$12` to RAM `$D3B3`. The dynamic graphics
loader resolves selector `$12` through the pointer table at `$7BA6` to list
`$7BCB`, which performs two loads:

| Bank | Source CPU | Source ROM | VRAM | Tile range | Tiles |
|---:|---:|---:|---:|---|---:|
| `$0D` | `$96BC` | `$356BC` | `$0D40` | `$6A-$79` | 16 |
| `$09` | `$8640` | `$24640` | `$0F40` | `$7A-$A9` | 48 |

Together these overwrite exactly `$6A-$A9`, covering the tile values used by
the `$18` mapping frames. Reconstructing the dynamic load produces a coherent
rotating end-of-act goal sign/signpost.

## Animation control commands decoded

The animation dispatcher at `$6696` currently has these control forms verified
by the THZ1 work:

| Command | Effect |
|---:|---|
| `FF 00` | restart current state's animation script |
| `FF 01 <lo> <hi>` | call absolute routine, then resume parsing |
| `FF 03 <state>` | request another object/animation state |
| `FF 06 <sound>` | write sound request to `PlaySound ($DE04)` |
| `FF 07 <lo> <hi>` | jump to absolute animation-script address |
| `FF 0E <count>` | set loop counter at `IX+$33` |
| `FF 0F <lo> <hi>` | decrement loop counter and jump while nonzero |
| `FF 02 <xlo> <xhi> <ylo> <yhi>` | set signed 8.8 X/Y velocity; X may be negated by orientation bit 4 |
| `FF 0B <offset> <mask>` | AND an object field with a mask |
| `FF 0C <offset> <mask>` | OR an object field with a mask |

Unknown command forms should remain unresolved rather than being inferred.
Preview colours use the THZ1 sprite palette `$06`, selected by the level table
at ROM `$07F3C` and stored at ROM `$3B6AD`. This replaces the earlier neutral
structural preview without changing any decoded tile or mapping data.

## Type `$27` behavior

Type `$27` has four animation states at bank-30 CPU `$8947`. State zero's
callback `$898E` selects state 1 and signed 8.8 X velocity `-$2.5` for the THZ1
parameter-zero records. State 1 alternates mapping frames `$01/$02` and moves
left until Sonic is within 64 pixels horizontally. State 2 stops horizontal
motion, initializes counter `$80`, and uses callbacks `$89DF/$89F3` to add or
subtract `$0003` from signed 8.8 Y velocity in the animation-script pattern.
The counter-underflow update requests state 3 and restores `-$2.5` X velocity.
State 3 removes the object once horizontal distance from Sonic reaches `$0180`.

THZ1 places three instances at world coordinates `(3504,224)`, `(2288,768)`
and `(2240,112)`. All have placement flag bit 4 set, parameter zero, and art
bases `$AA/$AA`. The sprite frames are visually coherent, but this document
deliberately retains the numeric type name rather than promoting a visual guess
to a canonical enemy name.

## Reproduce locally

```sh
python tests/test_thz1_object_assets.py
python tests/test_thz1_animation_reach.py
python tools/thz1_object_assets.py path/to/SonicChaos.sms
python tools/thz1_animation_reach.py path/to/SonicChaos.sms
python tools/thz1_type18_dynamic_graphics.py path/to/SonicChaos.sms
```

All ROM-derived previews and summaries are written below `build/`, which is
ignored by Git.

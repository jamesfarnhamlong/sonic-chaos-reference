# THZ1 graphics streams and object sprite mappings

This document records the currently verified Turquoise Hill Act 1 graphics
addresses for the supplied Master System ROM revision. It is intentionally
metadata-only: the repository does not contain ROM graphics, decompressed tile
bytes or exported PNGs.

## Level-art loader

`LoadLevelTiles` selects a seven-byte entry at CPU/file `$7CED` for THZ Act 1.

The verified entry bytes are:

```text
10 00 18 9E 8F 13 7E
```

They resolve to:

| Field | Value |
|---|---:|
| graphics bank | `$10` |
| VRAM destination | `$1800` (tile `$C0`) |
| primary compressed stream CPU | `$8F9E` |
| primary compressed stream ROM | `$40F9E` |
| supplemental-list CPU/file | `$7E13` |

The primary stream header reports 251 decompressed tiles.

## THZ1 palette selection

The level/act palette-selector table at ROM `$07F3C` starts with bytes
`15 06` for THZ1. `_LABEL_794F_293` stores those as the background and sprite
palette numbers. The palette resolver `_LABEL_3B63E_81` indexes 16-byte records
at ROM `$3B64D`, so THZ1 object sprites use palette `$06` at ROM `$3B6AD`.
Each Master System CRAM byte is decoded as two bits each of red, green and blue;
sprite colour index zero is transparent.

## Supplemental THZ1 graphics list

The list at `$7E13` contains six five-byte entries followed by `$FF`.
Bit 7 of the first byte requests the byte-remap path; low five bits select the
ROM bank.

| Bank byte | VRAM | Base tile | CPU stream | ROM stream | Remap |
|---:|---:|---:|---:|---:|:---:|
| `$08` | `$0200` | `$10` | `$B340` | `$23340` | no |
| `$09` | `$0D40` | `$6A` | `$A1C0` | `$261C0` | no |
| `$09` | `$0E40` | `$72` | `$A030` | `$26030` | no |
| `$09` | `$10C0` | `$86` | `$9AB0` | `$25AB0` | no |
| `$89` | `$1300` | `$98` | `$9AB0` | `$25AB0` | yes |
| `$89` | `$1540` | `$AA` | `$95A0` | `$255A0` | yes |

For remapped entries, each decompressed byte `b` is replaced with
`ROM[$0100 + b]` before presentation.

The streams tied to base tiles `$6A`, `$72`, `$86`, `$98` and `$AA` decode to
8, 20, 18, 18 and 10 tiles respectively on the checked ROM.

## Object sprite mappings

Bank `$0F` contains the object mapping-pointer table. The following mappings
have been source-traced and used to reconstruct coherent sprite frames:

| Type | Existing role status | Art base(s) | Mapping CPU | Mapping ROM | Frame records |
|---:|---|---:|---:|---:|---|
| `$21` | likely Boing-o-Bot; verified name still open ([behavior trace](object-21.md)) | `$86`, `$98` | `$911B` | `$3D11B` | `$9121`, `$912C` |
| `$26` | concealed spring | `$72` | `$91C0` | `$3D1C0` | `$91C8`, `$91D3`, `$91DE` |
| `$27` | semantic identity still open | `$AA` | `$91F5` | `$3D1F5` | `$91FB`, `$9206` |
| `$28` | moving platform | `$6A` | `$9217` | `$3D217` | `$921B` |

The frame records contain the piece count, pointers to per-piece coordinates and
tile-offset lists, plus fields whose exact semantics are not yet named here.
The reconstructed presentation uses 8x16 SMS hardware-sprite pieces. Visual
recognition alone is not used to promote an unknown object type to a semantic
name in the repository.

## Reproduce locally

The decompressor itself is standard-library only:

```sh
python tests/test_tile_decompress.py
```

To export the verified streams from your own matching ROM into the ignored
`build/` directory:

```sh
python tools/export_thz1_graphics.py path/to/SonicChaos.sms
```

The exporter first verifies the seven-byte THZ1 level-art entry, every
supplemental-list entry and the ROM SHA-256. It then writes local
`raw_tiles.bin` files and JSON manifests under `build/thz1-graphics/`.

These local binaries are intentionally excluded from version control.

#!/usr/bin/env python3
"""Render the SEZ visual-approval boards from build/sez-approval/preview-input.json (needs Pillow).

Run sez_art_approval.py first (project venv), then this script with a Python that has Pillow.
Every board is a review diagnostic; nothing here is an approved runtime asset.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

import mghz_art_previews as P

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/sez-approval'
P.OUT = OUT                                # shared board helpers write through the module global
SURFACE_COLOURS = {**P.SURFACE_COLOURS, 12: (255, 160, 0), 18: (230, 230, 90), 22: (0, 220, 220), 26: (255, 60, 200), 13: (255, 150, 40)}
KEYS = ('sez1', 'sez2', 'sez3')
caption, scaled, block_image, tile_image, BG, SMALL = P.caption, P.scaled, P.block_image, P.tile_image, P.BG, P.SMALL


def terrain_tiles(data):
    t = data['terrain']
    bg, sp = t['palettes']['background'], t['palettes']['sprite']
    tiles = sorted(int(k) for k in t['tiles'])
    cols = 16
    im = Image.new('RGBA', (cols * 44 + 8, ((len(tiles) + cols - 1) // cols) * 48 + 44), BG)
    caption(im, 'SEZ terrain tiles $C0..$1AE (primary stream, 239 tiles) | background palette $17 | raw 8x8, 4x scale | PENDING REVIEW')
    for n, tid in enumerate(tiles):
        x, y = 8 + (n % cols) * 44, 36 + (n // cols) * 48
        im.alpha_composite(scaled(tile_image(t['tiles'][str(tid)], bg, sp), 4), (x, y))
        caption(im, f'{tid:03X}', (x + 4, y + 33), SMALL)
    im.save(OUT / 'terrain-tiles.png')


def block_sheet(data, ids, title, name, cols=12, scale=2):
    t = data['terrain']
    bg, sp = t['palettes']['background'], t['palettes']['sprite']
    cell_w, cell_h = 32 * scale + 12, 32 * scale + 28
    im = Image.new('RGBA', (cols * cell_w + 8, ((len(ids) + cols - 1) // cols) * cell_h + 44), BG)
    caption(im, title)
    for n, b in enumerate(ids):
        meta = t['blocks'][str(b)]
        x, y = 8 + (n % cols) * cell_w, 36 + (n // cols) * cell_h
        ImageDraw.Draw(im).rectangle((x - 2, y - 2, x + 32 * scale + 1, y + 32 * scale + 1), outline=SURFACE_COLOURS.get(meta['surface'], (255, 255, 255)))
        im.alpha_composite(scaled(block_image(meta['pixels'], bg, sp), scale), (x, y))
        caption(im, f'${b:02X} s{meta["surface"]:02X}' + (' P' if meta['priority_tiles'] else ''), (x, y + 32 * scale + 3), SMALL)
        caption(im, '/'.join(str(meta['cells'].get(k, 0)) for k in KEYS), (x, y + 32 * scale + 14), SMALL, (170, 180, 195))
    im.save(OUT / name)


def special_surfaces(data):
    groups = [('crumble candidate $0C (block $AF)', [0xAF]), ('booster candidate $1A (block $A7, effect-5 animated tile $158)', [0xA7]),
              ('breakable $0D ($9B,$9C) -> replacement $9D', [0x9B, 0x9C, 0x9D]), ('ramp $12 ($1F,$23)', [0x1F, 0x23]), ('floor break/bounce $16 ($47)', [0x47]),
              ('springs: upright $30,$31 | horizontal $32,$33 | diagonal $36', [0x30, 0x31, 0x32, 0x33, 0x36]), ('static floor spikes $3D (SEZ3)', [0x3D]),
              ('ring blocks $40..$45', list(range(0x40, 0x46)))]
    t = data['terrain']
    bg, sp = t['palettes']['background'], t['palettes']['sprite']
    cols = 14
    rows_needed = sum((len(g) + cols - 1) // cols + 1 for _, g in groups)
    im = Image.new('RGBA', (cols * 76 + 8, rows_needed * 92 + 44), BG)
    caption(im, 'SEZ special-surface blocks | border colour = surface | cells = sez1/sez2/sez3 | P = priority tiles | PENDING REVIEW')
    y = 36
    for title, g in groups:
        caption(im, title, (8, y))
        y += 18
        for n, b in enumerate(g):
            if str(b) not in t['blocks']:
                continue
            meta = t['blocks'][str(b)]
            x, yy = 8 + (n % cols) * 76, y + (n // cols) * 92
            ImageDraw.Draw(im).rectangle((x - 2, yy - 2, x + 65, yy + 65), outline=SURFACE_COLOURS.get(meta['surface'], (255, 255, 255)))
            im.alpha_composite(scaled(block_image(meta['pixels'], bg, sp), 2), (x, yy))
            caption(im, f'${b:02X} s{meta["surface"]:02X}' + (' P' if meta['priority_tiles'] else ''), (x, yy + 68), SMALL)
            caption(im, '/'.join(str(meta['cells'].get(k, 0)) for k in KEYS), (x, yy + 79), SMALL, (170, 180, 195))
        y += ((len(g) + cols - 1) // cols) * 92 + 6
    im.save(OUT / 'terrain-special-surfaces.png')


def animated(data):
    an = data['animated']
    t = data['terrain']
    bg, sp = t['palettes']['background'], t['palettes']['sprite']
    im = Image.new('RGBA', (900, 560), BG)
    caption(im, 'SEZ animated terrain | ring tiles $14D..$150 (8 updates/frame) | effect 5 tile $158 (VRAM $2B00, 3 updates/frame) | PENDING REVIEW')
    caption(im, 'terrain-ring block $40, upper-left ring quadrant per frame (VRAM $29A0 loads)', (8, 36))
    for i, px in enumerate(an['ring_frames']):
        im.alpha_composite(scaled(block_image(px, bg, sp), 3), (8 + i * 112, 56))
        caption(im, f'ring frame {i}', (8 + i * 112, 154), SMALL)
    caption(im, 'ring tiles raw (4 frames x 4 tiles, 6x)', (8, 176))
    for f, tiles in enumerate(an['ring_tiles']):
        for j, rows in enumerate(tiles):
            im.alpha_composite(scaled(tile_image(rows, bg, sp), 6), (8 + j * 56 + f * 232, 196))
    caption(im, 'effect 5: two 32-byte frames ($1D:$8DDD, $1D:$8DFD) alternate at VRAM $2B00 (tile $158); only block $A7 draws it', (8, 262))
    for f, rows in enumerate(an['effect5_tiles']):
        im.alpha_composite(scaled(tile_image(rows, bg, sp), 8), (8 + f * 90, 282))
        caption(im, f'frame {"A ($8DDD)" if f == 0 else "B ($8DFD)"}', (8 + f * 90, 350), SMALL)
    x0 = 220
    for bid, frames in an['effect5_blocks'].items():
        for f, px in enumerate(frames):
            im.alpha_composite(scaled(block_image(px, bg, sp), 4), (x0 + f * 150, 282))
            caption(im, f'block ${int(bid):02X} frame {"A" if f == 0 else "B"}', (x0 + f * 150, 414), SMALL)
    caption(im, 'ring blocks $40..$45 at frame 0', (8, 440))
    for n, (bid, px) in enumerate(an['ring_blocks_frame0'].items()):
        im.alpha_composite(scaled(block_image(px, bg, sp), 2), (8 + n * 76, 460))
        caption(im, f'${int(bid):02X}', (8 + n * 76, 526), SMALL)
    im.save(OUT / 'animated-terrain.png')


def shared_board(data):
    shared = data['shared']
    reg = (data['registration']['x'], data['registration']['y'])
    entries = []
    for key, s in shared.items():
        for f in s['frames']:
            entries.append((s, f))
    cols = 5
    im = Image.new('RGBA', (cols * 150 + 8, ((len(entries) + cols - 1) // cols) * 170 + 44), BG)
    caption(im, 'Shared objects under the SEZ sprite palette $08 | compositions proven identical to the accepted zones | x2 | PENDING REVIEW (colours only)')
    for n, (s, f) in enumerate(entries):
        x, y = 8 + (n % cols) * 150, 36 + (n // cols) * 170
        stage = Image.new('RGBA', (64, 64), P.STAGE)
        stage.alpha_composite(P.composed(f['images'][0], s['palette'], True, size=(64, 64), anchor=(32, 24), reg=reg))
        im.alpha_composite(scaled(stage, 2), (x, y))
        caption(im, f'${s["type"]:02X} {s["label"]}', (x, y + 130), SMALL)
        caption(im, f'frame {f["frame"]} bases ${s["bases"][0]:02X}/${s["bases"][1]:02X}', (x, y + 142), SMALL, (170, 180, 195))
    im.save(OUT / 'shared-objects-sez-palette.png')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=OUT / 'preview-input.json')
    a = p.parse_args()
    data = json.loads(a.input.read_text(encoding='utf-8'))
    OUT.mkdir(parents=True, exist_ok=True)
    terrain_tiles(data)
    ids = sorted(int(k) for k in data['terrain']['blocks'])
    block_sheet(data, ids, 'SEZ terrain blocks (union of three acts incl. replacement targets) | border colour = surface | label = $id sSURFACE [P] / cells sez1/sez2/sez3 | PENDING REVIEW',
                'terrain-blocks.png')
    special_surfaces(data)
    for key in data['acts']:
        P.terrain_context(data, key)
        P.full_map(data, key)
    animated(data)
    for key, name in (('32', '20'), ('35', '23'), ('47', '2f'), ('40', '28'), ('84', '54')):
        P.object_board(data, key, name)
    shared_board(data)
    pngs = sorted(OUT.glob('*.png'))
    manifest = {'approval': 'PENDING', 'generator': 'sez_art_approval.py + sez_art_previews.py',
                'images': [{'file': v.name, 'sha256': hashlib.sha256(v.read_bytes()).hexdigest(), 'size': list(Image.open(v).size)} for v in pngs],
                'note': 'Review diagnostics only. Forced mirrors (bit4=1) of types $23/$28/$2F/$54 are NOT approval candidates; none of these assets is approved for POC use.'}
    (OUT / 'png-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'{len(pngs)} PNGs rendered in {OUT}')


if __name__ == '__main__':
    main()

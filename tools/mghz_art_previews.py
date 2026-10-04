#!/usr/bin/env python3
"""Render the MGHZ visual-approval boards from build/mghz-approval/preview-input.json (needs Pillow).

Run mghz_art_approval.py first (project venv), then this script with a Python that has Pillow.
Every board is a review diagnostic; nothing here is an approved runtime asset.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/mghz-approval'
FONT = ImageFont.load_default(size=13)
SMALL = ImageFont.load_default(size=10)
BG = (38, 45, 56, 255)
STAGE = (65, 72, 84, 255)
SURFACE_COLOURS = {0: (90, 90, 90), 1: (80, 200, 80), 2: (80, 200, 80), 3: (80, 200, 80), 5: (255, 60, 60), 7: (255, 215, 0), 9: (80, 160, 255), 10: (80, 160, 255),
                   13: (255, 150, 40), 20: (80, 160, 255), 23: (200, 90, 255), 24: (190, 190, 190), 25: (0, 220, 220), 27: (255, 120, 200)}


def caption(im, text, xy=(8, 8), font=FONT, fill=(240, 240, 244)):
    ImageDraw.Draw(im).text(xy, text, font=font, fill=fill)


def rgba_image(rows):
    im = Image.new('RGBA', (len(rows[0]), len(rows)))
    im.putdata([tuple(c) for row in rows for c in row])
    return im


def piece_image(piece, palette):
    im = Image.new('RGBA', (8, len(piece['pixels'])))
    im.putdata([tuple(palette[c]) for row in piece['pixels'] for c in row])
    return im


def tile_image(rows, bg, sp=None, transparent=False):
    im = Image.new('RGBA', (8, 8))
    data = []
    for row in rows:
        for c in row:
            idx = c & 15
            pal = sp if (c & 16 and sp) else bg
            data.append(tuple(pal[idx]) if not (idx == 0 and not transparent) else tuple(bg[0][:3]) + (255,))
    im.putdata(data)
    return im


def block_image(pixels, bg, sp):
    im = Image.new('RGBA', (32, 32))
    data = []
    for row in pixels:
        for c in row:
            idx = c & 15
            data.append(tuple(bg[0][:3]) + (255,) if idx == 0 else tuple((sp if c & 16 else bg)[idx][:3]) + (255,))
    im.putdata(data)
    return im


def composed(image, palette, registration=False, size=(128, 112), anchor=(64, 56), reg=(1, 18)):
    im = Image.new('RGBA', size)
    ax, ay = anchor
    for p in reversed(image['pieces']):
        im.alpha_composite(piece_image(p, palette), (ax + p['x'] + (reg[0] if registration else 0), ay + p['y'] + (reg[1] if registration else 0)))
    return im


def cross(im, x, y):
    d = ImageDraw.Draw(im)
    d.line((x - 3, y, x + 3, y), fill=(255, 80, 220))
    d.line((x, y - 3, x, y + 3), fill=(255, 80, 220))


def scaled(im, k):
    return im.resize((im.width * k, im.height * k), Image.Resampling.NEAREST)


# --- terrain boards ---------------------------------------------------------------
def terrain_tiles(data):
    t = data['terrain']
    bg, sp = t['palettes']['background'], t['palettes']['sprite']
    tiles = sorted(int(k) for k in t['tiles'])
    cols = 16
    im = Image.new('RGBA', (cols * 44 + 8, ((len(tiles) + cols - 1) // cols) * 48 + 44), BG)
    caption(im, 'MGHZ terrain tiles $C0..$1B9 (primary stream, 250 tiles) | background palette $18 | raw 8x8, 4x scale | PENDING REVIEW')
    for n, tid in enumerate(tiles):
        x, y = 8 + (n % cols) * 44, 36 + (n // cols) * 48
        im.alpha_composite(scaled(tile_image(t['tiles'][str(tid)], bg, sp), 4), (x, y))
        caption(im, f'{tid:03X}', (x + 4, y + 33), SMALL)
    im.save(OUT / 'terrain-tiles.png')


def block_sheet(data, ids, title, name, cols=12, scale=2, flag=None):
    t = data['terrain']
    bg, sp = t['palettes']['background'], t['palettes']['sprite']
    cell_w, cell_h = 32 * scale + 12, 32 * scale + 28
    im = Image.new('RGBA', (cols * cell_w + 8, ((len(ids) + cols - 1) // cols) * cell_h + 44), BG)
    caption(im, title)
    for n, b in enumerate(ids):
        meta = t['blocks'][str(b)]
        x, y = 8 + (n % cols) * cell_w, 36 + (n // cols) * cell_h
        d = ImageDraw.Draw(im)
        colour = SURFACE_COLOURS.get(meta['surface'], (255, 255, 255))
        d.rectangle((x - 2, y - 2, x + 32 * scale + 1, y + 32 * scale + 1), outline=colour)
        im.alpha_composite(scaled(block_image(meta['pixels'], bg, sp), scale), (x, y))
        label = f'${b:02X} s{meta["surface"]:02X}' + (' P' if meta['priority_tiles'] else '')
        caption(im, label, (x, y + 32 * scale + 3), SMALL)
        cells = '/'.join(str(meta['cells'].get(k, 0)) for k in ('mghz1', 'mghz2', 'mghz3'))
        caption(im, cells, (x, y + 32 * scale + 14), SMALL, (170, 180, 195))
    im.save(OUT / name)


def special_surfaces(data):
    groups = [('surface $1B oil (block $A0)', [0xA0]), ('twist $17 blocks $58..$73', list(range(0x58, 0x74))), ('strip $19 ($85,$87)', [0x85, 0x87]),
              ('breakable $0D ($9B,$9C) -> replacement $9D', [0x9B, 0x9C, 0x9D]), ('spikes: floor $3C / ceiling $3E,$3F', [0x3C, 0x3E, 0x3F]),
              ('springs: upright $30,$31 | horizontal $32,$34,$35 | diagonal $36,$38', [0x30, 0x31, 0x32, 0x34, 0x35, 0x36, 0x38]),
              ('one-way bit6 $0D,$0F,$F9 | surface $18 $8A,$8B', [0x0D, 0x0F, 0xF9, 0x8A, 0x8B]), ('ring blocks $40..$45', list(range(0x40, 0x46)))]
    t = data['terrain']
    bg, sp = t['palettes']['background'], t['palettes']['sprite']
    ids = [b for _, g in groups for b in g]
    cols = 14
    rows_needed = sum((len(g) + cols - 1) // cols + 1 for _, g in groups)
    im = Image.new('RGBA', (cols * 76 + 8, rows_needed * 92 + 44), BG)
    caption(im, 'MGHZ special-surface blocks | border colour = surface | cells = mghz1/mghz2/mghz3 | P = priority tiles | PENDING REVIEW')
    y = 36
    for title, g in groups:
        caption(im, title, (8, y))
        y += 18
        for n, b in enumerate(g):
            if str(b) not in t['blocks']:
                continue
            meta = t['blocks'][str(b)]
            x = 8 + (n % cols) * 76
            yy = y + (n // cols) * 92
            d = ImageDraw.Draw(im)
            d.rectangle((x - 2, yy - 2, x + 65, yy + 65), outline=SURFACE_COLOURS.get(meta['surface'], (255, 255, 255)))
            im.alpha_composite(scaled(block_image(meta['pixels'], bg, sp), 2), (x, yy))
            caption(im, f'${b:02X} s{meta["surface"]:02X}' + (' P' if meta['priority_tiles'] else ''), (x, yy + 68), SMALL)
            caption(im, '/'.join(str(meta['cells'].get(k, 0)) for k in ('mghz1', 'mghz2', 'mghz3')), (x, yy + 79), SMALL, (170, 180, 195))
        y += ((len(g) + cols - 1) // cols) * 92 + 6
    im.save(OUT / 'terrain-special-surfaces.png')


def terrain_context(data, key):
    a = data['acts'][key]
    sc = data['start_crops'][key]
    im = Image.new('RGBA', (768, 36 + 672), BG)
    caption(im, f'{key.upper()} start camera {a["start_camera"]} | player start {a["start_player"]} (magenta) | canonical terrain, SMS 256x224 crop x3')
    crop = rgba_image(sc['crop'])
    px, py = sc['player'][0] - sc['camera'], sc['player'][1] - a['start_camera'][1]
    cross(crop, px, py)
    im.alpha_composite(scaled(crop, 3), (0, 36))
    specials = [(k, v) for k, v in data['special_crops'].items() if k.startswith(key + ':')]
    if specials:
        cols = 2
        sheet = Image.new('RGBA', (768, 36 + ((len(specials) + cols - 1) // cols) * 372), BG)
        caption(sheet, f'{key.upper()} special-terrain crops (centre = chosen cell; x1.5)')
        for n, (k, v) in enumerate(specials):
            c = scaled(rgba_image(v['crop']), 1).resize((384, 336), Image.Resampling.NEAREST)
            x, y = (n % cols) * 384, 36 + (n // cols) * 372
            sheet.alpha_composite(c, (x, y + 16))
            caption(sheet, f'{k.split(":")[1]} cell ({v["cell"]["cell_x"]},{v["cell"]["cell_y"]}) block ${v["cell"]["block_id"]:02X}', (x + 4, y), SMALL)
        board = Image.new('RGBA', (768, im.height + sheet.height), BG)
        board.alpha_composite(im, (0, 0))
        board.alpha_composite(sheet, (0, im.height))
        im = board
    im.save(OUT / f'terrain-context-{key}.png')


def full_map(data, key):
    a = data['acts'][key]
    t = data['terrain']
    bg, sp = t['palettes']['background'], t['palettes']['sprite']
    blocks = {int(k): block_image(v['pixels'], bg, sp) for k, v in t['blocks'].items()}
    w, h = a['width'] * 32, a['height'] * 32
    im = Image.new('RGBA', (w, h), tuple(bg[0][:3]) + (255,))
    for i, b in enumerate(a['cells'][:a['runtime_cells']]):
        im.paste(blocks[b], ((i % a['width']) * 32, (i // a['width']) * 32))
    d = ImageDraw.Draw(im)
    colours = data['object_colours']
    for o in a['objects']:
        c = tuple(colours.get(o['type'], (255, 255, 255)))
        r = 7
        d.ellipse((o['x'] - r, o['y'] - r, o['x'] + r, o['y'] + r), outline=c, width=3)
        d.text((o['x'] + 9, o['y'] - 8), f'{o["index"]}:{o["type"][2:]}/{o["parameter"][2:]}', font=FONT, fill=c)
    for x, y in a['terrain_rings']:
        d.point((x, y), fill=(255, 215, 0))
    sx, sy = a['start_player']
    d.rectangle((sx - 4, sy - 12, sx + 4, sy + 12), outline=(255, 80, 220), width=2)
    half = im.resize((w // 2, h // 2), Image.Resampling.LANCZOS)
    board = Image.new('RGBA', (half.width, half.height + 44), BG)
    caption(board, f'{key.upper()} full terrain map {w}x{h} at 50% | circles = mapped objects "index:type/param" | gold dots = terrain rings | magenta = player start | PENDING REVIEW')
    board.alpha_composite(half, (0, 44))
    board.save(OUT / f'map-{key}.png')


def animated(data):
    an = data['animated']
    t = data['terrain']
    bg, sp = t['palettes']['background'], t['palettes']['sprite']
    im = Image.new('RGBA', (900, 820), BG)
    caption(im, 'MGHZ animated terrain | ring tiles $10B..$10E (8 updates/frame) | tiles $1A8/$1A9 strip (4 updates/frame) | palette cycles | PENDING REVIEW')
    caption(im, 'terrain-ring block $40, upper-left ring quadrant per frame (VRAM $2160 loads)', (8, 36))
    for i, px in enumerate(an['ring_frames']):
        b = scaled(block_image(px, bg, sp), 3)
        im.alpha_composite(b, (8 + i * 112, 56))
        caption(im, f'ring frame {i}', (8 + i * 112, 154), SMALL)
    caption(im, 'ring tiles raw (4 frames x 4 tiles, 6x)', (8, 176))
    for f, tiles in enumerate(an['ring_tiles']):
        for j, rows in enumerate(tiles):
            im.alpha_composite(scaled(tile_image(rows, bg, sp), 6), (8 + j * 56 + f * 232, 196))
    caption(im, 'effect 14: VRAM $3500 strip (tiles $1A8,$1A9) alternates between the two 64-byte sources; blocks $D2/$D3 reference them', (8, 262))
    for f, tiles in enumerate(an['strip_tiles']):
        for j, rows in enumerate(tiles):
            im.alpha_composite(scaled(tile_image(rows, bg, sp), 6), (8 + j * 56 + f * 140, 282))
        caption(im, f'source {"A ($8E3D)" if f == 0 else "B ($8E1D)"}', (8 + f * 140, 332), SMALL)
    for n, (bid, frames) in enumerate(an['strip_blocks'].items()):
        for f, px in enumerate(frames):
            im.alpha_composite(scaled(block_image(px, bg, sp), 3), (330 + n * 220 + f * 100 - 0, 276 - 0))
            caption(im, f'${int(bid):02X} src {"A" if f == 0 else "B"}', (330 + n * 220 + f * 100, 374), SMALL)
    caption(im, 'palette cycles on background CRAM entries (original routine, update step = 10); swatches in sequence order', (8, 410))
    y = 432
    for eid, cyc in an['palette_cycles'].items():
        caption(im, f'effect {eid}: CRAM entry {cyc["cram_index"]} | initial ${cyc["initial"]:02X} | sequence bytes ' + ' '.join(f'{v:02X}' for v in cyc['sequence_cram_bytes'][:12]), (8, y), SMALL)
        for i, c in enumerate(cyc['sequence_rgba'][:12]):
            ImageDraw.Draw(im).rectangle((8 + i * 40, y + 14, 8 + i * 40 + 34, y + 44), fill=tuple(c))
        y += 54
    caption(im, 'blocks that contain these palette indices (background palette, not palette-1)', (8, y + 4))
    y += 24
    for ci, ids in an['palette_cycle_demo_blocks'].items():
        caption(im, f'index {ci}: ' + ', '.join(f'${b:02X}' for b in ids), (8, y), SMALL)
        for i, b in enumerate(ids):
            im.alpha_composite(scaled(block_image(t['blocks'][str(b)]['pixels'], bg, sp), 2), (8 + i * 72, y + 14))
        y += 92
    im.save(OUT / 'animated-terrain.png')


# --- object boards ----------------------------------------------------------------------
def object_board(data, key, hex_name):
    s = data['subjects'][key]
    palette = s['palette']
    reg = (data['registration']['x'], data['registration']['y'])
    tiles = s['raw_tiles']
    cols = 16
    raw_h = 52 + ((len(tiles) + cols - 1) // cols) * 40
    raw = Image.new('RGBA', (768, raw_h), BG)
    caption(raw, f'Type ${int(key):02X} {s["label"]} | palette ${s["palette_index"]:02X} | bases ${s["bases"][0]:02X}/${s["bases"][1]:02X} | raw 8x8 tiles (3x) | PENDING REVIEW')
    for n, tile in enumerate(tiles):
        x, y = 8 + (n % cols) * 46, 36 + (n // cols) * 40
        tp = Image.new('RGBA', (8, 8))
        tp.putdata([tuple(palette[c]) for row in tile['pixels'] for c in row])
        stage = Image.new('RGBA', (24, 24), STAGE)
        stage.alpha_composite(scaled(tp, 3))
        raw.alpha_composite(stage, (x, y))
        caption(raw, f'{tile["tile"]:02X}', (x + 2, y + 25), SMALL)
    frames = s['frames']
    cell_w, cell_h = 256, 224
    per_row = 3
    sheet_h = 40 + len(frames) * (cell_h + 10)
    sheet = Image.new('RGBA', (768, sheet_h), BG)
    caption(sheet, 'composed frames (2x): left = canonical orientation (bit4=0), middle = mirrored image, right = SAT pieces (uncomposed) | magenta = anchor | stage includes +(1,18) registration')
    for n, f in enumerate(frames):
        y = 40 + n * (cell_h + 10)
        for im_idx, image in enumerate(f['images'][:2]):
            stage = Image.new('RGBA', (128, 112), STAGE)
            stage.alpha_composite(composed(image, palette, True, reg=reg))
            cross(stage, 64, 56)
            sheet.alpha_composite(scaled(stage, 2), (im_idx * 256, y))
            canonical = (not image['mirror']) or image.get('canonical_orientation')
            label = f'frame {f["frame"]} | bit4={int(image["mirror"])}'
            if image['mirror']:
                label += ' | RUNTIME-CANONICAL' if s['mirror_rule'].startswith('runtime uses bit4') else ' | FORCED DIAGNOSTIC (not approved)'
            caption(sheet, label, (im_idx * 256 + 6, y + 4), SMALL, (255, 235, 120) if image['mirror'] and not s['mirror_rule'].startswith('runtime uses bit4') else (240, 240, 244))
        caption(sheet, f'SAT pieces ({f["piece_count"]}), ext {f["extent_x_y"]}', (520, y + 4), SMALL)
        base_image = f['images'][0]
        for j, piece in enumerate(base_image['pieces']):
            x, yy = 520 + (j % 8) * 28, y + 22 + (j // 8) * 40
            sheet.alpha_composite(scaled(piece_image(piece, palette), 2), (x, yy))
    ctx = s.get('context')
    contexts = [('canonical terrain context', ctx)] if ctx else list(s.get('contexts', {}).items())
    if 'contexts' in s:
        contexts = list(s['contexts'].items())
    ctx_imgs = []
    for label, c in contexts:
        crop = rgba_image(c['crop'])
        ax, ay = c['anchor']
        frame_pick = next((f for f in frames if f['frame'] == (1 if s['type'] != 0x2F else 0)), frames[-1])
        image = frame_pick['images'][0]
        for piece in reversed(image['pieces']):
            crop.alpha_composite(piece_image(piece, palette), (ax + piece['x'] + reg[0], ay + piece['y'] + reg[1]))
        cross(crop, ax, ay)
        big = scaled(crop, 3)
        wrap = Image.new('RGBA', (768, 700), BG)
        caption(wrap, f'Type ${s["type"]:02X} | {s["act"].upper()} {label} | camera {c["camera"]} anchor {c["anchor"]} (frame {frame_pick["frame"]}, bit4=0)')
        wrap.alpha_composite(big, (0, 28))
        ctx_imgs.append(wrap)
    total_h = raw.height + sheet.height + sum(c.height for c in ctx_imgs) + 16
    board = Image.new('RGBA', (768, total_h), BG)
    y = 0
    for part in [raw, sheet] + ctx_imgs:
        board.alpha_composite(part, (0, y))
        y += part.height + 8
    board.save(OUT / f'type-{hex_name}-approval.png')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=OUT / 'preview-input.json')
    a = p.parse_args()
    data = json.loads(a.input.read_text(encoding='utf-8'))
    OUT.mkdir(parents=True, exist_ok=True)
    terrain_tiles(data)
    ids = sorted(int(k) for k in data['terrain']['blocks'])
    block_sheet(data, ids, 'MGHZ terrain blocks (union of three acts incl. ring replacement/mutation targets) | border colour = surface | label = $id sSURFACE [P] / cells mghz1/mghz2/mghz3 | PENDING REVIEW',
                'terrain-blocks.png')
    special_surfaces(data)
    for key in data['acts']:
        terrain_context(data, key)
        full_map(data, key)
    animated(data)
    for key, name in (('33', '21'), ('36', '24'), ('46', '2e'), ('47', '2f'), ('40', '28'), ('86', '56')):
        object_board(data, key, name)
    pngs = sorted(OUT.glob('*.png'))
    manifest = {'approval': 'PENDING', 'generator': 'mghz_art_approval.py + mghz_art_previews.py',
                'images': [{'file': v.name, 'sha256': hashlib.sha256(v.read_bytes()).hexdigest(), 'size': list(Image.open(v).size)} for v in pngs],
                'note': 'Review diagnostics only. Forced mirrors (bit4=1) of types $24/$2E/$2F/$28/$56 are NOT approval candidates; none of these assets is approved for POC use.'}
    (OUT / 'png-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'{len(pngs)} PNGs rendered in {OUT}')


if __name__ == '__main__':
    main()

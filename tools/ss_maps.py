"""Static map renderer for the Special Stage packages (decoded layout + block mappings + level VRAM; needs Pillow).

Terrain animation (effects) is not applied here; the stage VRAM is the post-load static art stream.  Pixels are written only to ignored `build/`.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

from PIL import Image, ImageDraw  # noqa: E402

import level_package as L  # noqa: E402
import thz1_object_assets as G  # noqa: E402


def palettes(r, act):
    pal = act['descriptor']['palette']
    bg = [tuple(c[:3]) for c in G.palette_rgba(r, pal['background_index'])]
    sp = [tuple(c[:3]) for c in G.palette_rgba(r, pal['sprite_index'])]
    return bg, sp


def render_map(r, act, scale=1, x0=0, y0=0, w=None, h=None, markers=None, ring_markers=True):
    """Return an RGB PIL image of the decoded terrain.  Index 0 of either palette half is drawn with background colour 0 (the backdrop)."""
    d = act['descriptor']['header']
    cells, width = act['cells'], act['width']
    vram = act['vram']
    maps = L.block_pixel_maps(r, vram, only=sorted(set(cells[:act['runtime_cells']])), mapping_rom=d['block_mapping_rom'])
    bg, sp = palettes(r, act)
    full_w, full_h = width * 32, act['height'] * 32
    w = full_w - x0 if w is None else w
    h = full_h - y0 if h is None else h
    im = Image.new('RGB', (w, h), bg[0])
    px = im.load()
    for cy in range(act['height']):
        for cx in range(width):
            i = cy * width + cx
            if i >= act['runtime_cells']:
                continue
            bx, by = cx * 32 - x0, cy * 32 - y0
            if bx + 32 <= 0 or by + 32 <= 0 or bx >= w or by >= h:
                continue
            m = maps[cells[i]]
            for yy in range(32):
                if not 0 <= by + yy < h:
                    continue
                row = m[yy]
                for xx in range(32):
                    if not 0 <= bx + xx < w:
                        continue
                    c = row[xx]
                    idx = c & 15
                    px[bx + xx, by + yy] = bg[0] if idx == 0 else (sp if c & 16 else bg)[idx]
    if scale != 1:
        im = im.resize((max(1, w // scale), max(1, h // scale)), Image.Resampling.NEAREST if scale < 1 else Image.Resampling.BOX)
    dr = ImageDraw.Draw(im)
    s = 1 / scale
    for m in (markers or []):
        x, y = (m['x'] - x0) * s, (m['y'] - y0) * s
        dr.rectangle((x - 3, y - 3, x + 3, y + 3), outline=m.get('colour', (255, 255, 0)))
        if m.get('label'):
            dr.text((x + 5, y - 5), m['label'], fill=m.get('colour', (255, 255, 0)))
    return im

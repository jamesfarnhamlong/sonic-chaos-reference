#!/usr/bin/env python3
"""Render lossless native-scale research maps from a ROM-derived level package.

Renderer assumptions (documented, not proven ROM facts):

* Every map pixel comes from decoded ROM tiles referenced by decoded ROM block
  mappings placed by the decoded layout. Nothing is redrawn by hand.
* A block is 4x4 tile entries (32x32 px). Tile bit 11 (attribute "palette 1")
  selects CRAM entries 16-31, which the engine fills with the act's *sprite*
  palette selector; the other half uses the *background* selector (same
  assumption as tools/thz1_background_registration.py, which matched POC pixels).
* Colour index 0 is drawn as background-palette colour 0 (backdrop) in both
  halves. Tile priority bits are ignored (a static map has no sprites).
* Per-frame palette animation, parallax and dynamic VRAM changes are not modelled.
* The layout cell the original loader never writes (index 4095 of a 4096-cell
  stream) is left as backdrop colour.

Overlay marks are diagnostic only. The JSON package stays authoritative.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import level_package as L  # noqa: E402
import thz1_object_assets as assets  # noqa: E402

LEGEND_HEIGHT = 30

# 3x5 bitmap font: digits, A-Z and a little punctuation.
_FONT_ROWS = {
    "0": "111 101 101 101 111", "1": "010 110 010 010 111", "2": "111 001 111 100 111",
    "3": "111 001 111 001 111", "4": "101 101 111 001 001", "5": "111 100 111 001 111",
    "6": "111 100 111 101 111", "7": "111 001 001 001 001", "8": "111 101 111 101 111",
    "9": "111 101 111 001 111", "A": "010 101 111 101 101", "B": "110 101 110 101 110",
    "C": "011 100 100 100 011", "D": "110 101 101 101 110", "E": "111 100 110 100 111",
    "F": "111 100 110 100 100", "G": "011 100 101 101 011", "H": "101 101 111 101 101",
    "I": "111 010 010 010 111", "J": "001 001 001 101 010", "K": "101 101 110 101 101",
    "L": "100 100 100 100 111", "M": "101 111 111 101 101", "N": "110 101 101 101 101",
    "O": "010 101 101 101 010", "P": "110 101 110 100 100", "Q": "010 101 101 111 011",
    "R": "110 101 110 101 101", "S": "011 100 010 001 110", "T": "111 010 010 010 010",
    "U": "101 101 101 101 111", "V": "101 101 101 101 010", "W": "101 101 111 111 101",
    "X": "101 101 010 101 101", "Y": "101 101 010 010 010", "Z": "111 001 010 100 111",
    "$": "011 110 010 011 110", " ": "000 000 000 000 000", "-": "000 000 111 000 000",
    ":": "000 010 000 010 000", "+": "000 010 111 010 000", "(": "010 100 100 100 010",
    ")": "010 001 001 001 010", ".": "000 000 000 000 010", "=": "000 111 000 111 000",
    "/": "001 001 010 100 100",
}
FONT = {ch: [row for row in spec.split()] for ch, spec in _FONT_ROWS.items()}

TERRAIN_RING_COLOUR = (255, 214, 0)
OBJ09_VISIBLE_COLOUR = (0, 230, 255)
OBJ09_HIDDEN_COLOUR = (255, 64, 255)
ANCHOR_COLOUR = (255, 255, 255)
OUTLINE = (0, 0, 0)
LEGEND_BG = (24, 24, 32)


class Canvas:
    def __init__(self, width: int, height: int, rgba=None):
        self.w, self.h = width, height
        self.buf = bytearray(rgba) if rgba is not None else bytearray(width * height * 4)

    def set(self, x: int, y: int, colour) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 4
            self.buf[i:i + 4] = bytes((colour[0], colour[1], colour[2], 255))

    def rect(self, x0, y0, x1, y1, colour) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, colour)

    def text(self, x: int, y: int, message: str, colour, scale: int = 2, shadow=True) -> int:
        cursor = x
        for ch in message.upper():
            glyph = FONT.get(ch, FONT[" "])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        self.rect(cursor + gx * scale, y + gy * scale,
                                  cursor + gx * scale + scale - 1, y + gy * scale + scale - 1, colour)
            cursor += 4 * scale
        return cursor

    @staticmethod
    def text_width(message: str, scale: int = 2) -> int:
        return len(message) * 4 * scale


def block_rgba_rows(rom: bytes, act: dict) -> tuple:
    """(per-block list of 32 RGBA rows, opaque backdrop RGBA)."""
    desc = act["descriptor"]
    palettes = (assets.palette_rgba(rom, desc["palette"]["background_index"]),
                assets.palette_rgba(rom, desc["palette"]["sprite_index"]))
    pixels = L.block_pixel_maps(rom, act["vram"], mapping_rom=desc["header"]["block_mapping_rom"])
    out = {}
    for block, rows in pixels.items():
        rgba_rows = []
        for row in rows:
            data = bytearray()
            for value in row:
                r, g, b, _ = palettes[1 if value & 0x10 else 0][value & 0x0F]
                data += bytes((r, g, b, 255))
            rgba_rows.append(bytes(data))
        out[block] = rgba_rows
    backdrop = palettes[0][0]
    return out, (backdrop[0], backdrop[1], backdrop[2], 255)


def terrain_canvas(rom: bytes, act: dict) -> Canvas:
    """Full-level terrain map at native scale (1 level pixel = 1 image pixel)."""
    blocks, backdrop = block_rgba_rows(rom, act)
    width, height = act["width"], act["height"]
    blank_row = bytes(backdrop) * L.BLOCK_PIXELS
    rows = []
    for cy in range(height):
        for py in range(L.BLOCK_PIXELS):
            parts = []
            for cx in range(width):
                index = cy * width + cx
                if index >= act["runtime_cells"]:
                    parts.append(blank_row)
                else:
                    parts.append(blocks[act["cells"][index]][py])
            rows.append(b"".join(parts))
    return Canvas(width * L.BLOCK_PIXELS, height * L.BLOCK_PIXELS, b"".join(rows))


def _outlined(canvas: Canvas, points, colour) -> None:
    for x, y in points:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                canvas.set(x + dx, y + dy, OUTLINE)
    for x, y in points:
        canvas.set(x, y, colour)


def draw_circle(canvas: Canvas, cx: int, cy: int, radius: int, colour) -> None:
    pts = []
    for y in range(-radius, radius + 1):
        for x in range(-radius, radius + 1):
            d = x * x + y * y
            if radius * radius - radius <= d <= radius * radius + radius:
                pts.append((cx + x, cy + y))
    _outlined(canvas, pts, colour)


def draw_diamond(canvas: Canvas, cx: int, cy: int, radius: int, colour) -> None:
    pts = [(cx + x, cy + y) for y in range(-radius, radius + 1) for x in range(-radius, radius + 1)
           if abs(x) + abs(y) == radius]
    _outlined(canvas, pts, colour)
    canvas.set(cx, cy, colour)


def draw_x_box(canvas: Canvas, cx: int, cy: int, radius: int, colour) -> None:
    pts = []
    for i in range(-radius, radius + 1):
        pts += [(cx + i, cy + i), (cx + i, cy - i)]
        pts += [(cx + i, cy - radius), (cx + i, cy + radius), (cx - radius, cy + i), (cx + radius, cy + i)]
    _outlined(canvas, pts, colour)


def draw_crosshair(canvas: Canvas, cx: int, cy: int, arm: int, colour) -> None:
    pts = [(cx + i, cy) for i in range(-arm, arm + 1)] + [(cx, cy + i) for i in range(-arm, arm + 1)]
    _outlined(canvas, pts, colour)


def _with_legend(canvas: Canvas, items, title: str) -> Canvas:
    out = Canvas(canvas.w, canvas.h + LEGEND_HEIGHT)
    out.rect(0, 0, out.w - 1, LEGEND_HEIGHT - 1, LEGEND_BG)
    out.buf[LEGEND_HEIGHT * out.w * 4:] = canvas.buf
    x = 8
    out.text(x, 10, title, (255, 255, 255))
    x += Canvas.text_width(title) + 24
    for kind, colour, label in items:
        cy = 15
        if kind == "circle":
            draw_circle(out, x + 8, cy, 6, colour)
        elif kind == "diamond":
            draw_diamond(out, x + 8, cy, 6, colour)
        elif kind == "xbox":
            draw_x_box(out, x + 8, cy, 5, colour)
        elif kind == "cross":
            draw_crosshair(out, x + 8, cy, 6, colour)
        x += 22
        x = out.text(x, 10, label, (230, 230, 230)) + 24
    return out


def draw_rings(canvas: Canvas, rings, small: bool = False) -> None:
    for ring in rings:
        x, y = ring["world_x"], ring["world_y"]
        cls = ring["source_class"]
        if cls == "terrain":
            draw_circle(canvas, x, y, 4 if small else 7, TERRAIN_RING_COLOUR)
        elif cls == "object_09_visible":
            draw_diamond(canvas, x, y, 4 if small else 8, OBJ09_VISIBLE_COLOUR)
        else:
            draw_x_box(canvas, x, y, 3 if small else 6, OBJ09_HIDDEN_COLOUR)


def draw_objects(canvas: Canvas, records) -> None:
    for n, rec in enumerate(records):
        x, y = rec["world_x"], rec["world_y"]
        draw_crosshair(canvas, x, y, 6, ANCHOR_COLOUR)
    for n, rec in enumerate(records):
        x, y = rec["world_x"], rec["world_y"]
        label = "$" + rec["type_id"][2:]
        wpx = Canvas.text_width(label) - 2
        lx = min(max(x + 5, 0), canvas.w - wpx - 3)
        ly = y - 15 if n % 2 == 0 else y + 6
        ly = min(max(ly, 0), canvas.h - 12)
        canvas.rect(lx - 1, ly - 1, lx + wpx, ly + 10, (0, 0, 0))
        canvas.text(lx, ly, label, (255, 255, 255))


LEGEND_RINGS = (
    ("circle", TERRAIN_RING_COLOUR, "TERRAIN RING"),
    ("diamond", OBJ09_VISIBLE_COLOUR, "$09 VISIBLE (PARAM $00)"),
    ("xbox", OBJ09_HIDDEN_COLOUR, "$09 HIDDEN TRIGGER (PARAM NONZERO)"),
)
LEGEND_OBJECTS = (("cross", ANCHOR_COLOUR, "OBJECT ANCHOR - LABEL IS NUMERIC TYPE ID"),)


def build_maps(rom: bytes, act: dict, rings: list) -> dict:
    """Return {name: Canvas} for the four research maps of one act."""
    key = act["key"].upper()
    base = terrain_canvas(rom, act)
    maps = {"terrain": _with_legend(base, (), f"{key} TERRAIN - DECODED ROM LAYOUT")}

    ring_canvas = Canvas(base.w, base.h, base.buf)
    draw_rings(ring_canvas, rings)
    maps["rings"] = _with_legend(ring_canvas, LEGEND_RINGS, f"{key} RINGS")

    obj_canvas = Canvas(base.w, base.h, base.buf)
    draw_objects(obj_canvas, act["records"])
    maps["objects"] = _with_legend(obj_canvas, LEGEND_OBJECTS, f"{key} OBJECTS")

    combined = Canvas(base.w, base.h, base.buf)
    draw_rings(combined, rings, small=True)
    draw_objects(combined, act["records"])
    maps["combined"] = _with_legend(combined, LEGEND_RINGS + LEGEND_OBJECTS, f"{key} COMBINED")
    return maps


def write_maps(rom: bytes, act: dict, rings: list, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for name, canvas in build_maps(rom, act, rings).items():
        path = out_dir / f"{act['key']}_{name}.png"
        assets.write_rgba_png(path, canvas.w, canvas.h, bytes(canvas.buf))
        written[name] = {"file": path.name, "width": canvas.w, "height": canvas.h,
                         "legend_height": LEGEND_HEIGHT}
    return written

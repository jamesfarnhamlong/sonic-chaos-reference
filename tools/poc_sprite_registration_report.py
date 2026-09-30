#!/usr/bin/env python3
"""Compare a GameMaker POC checkout's sprite registration with the original renderer.

Read-only.  Uses data/rom-cache/mapped-object-registration.json (original, emulated) and the POC's
sprite PNG/.yy files plus the adapter macros in scripts/SCR_chaos_render_adapter.  No ROM needed.

    python tools/poc_sprite_registration_report.py path/to/SonicChaos_POC

For every type whose POC draw is "sprite drawn at anchor + adapter" the report prints the predicted
vertical difference (POC minus original, in pixels; negative = POC draws higher).  Types with bespoke
draw code ($1B crop, $26 composite) are reported by the research JSON instead.

The numbers are GAMEMAKER ADAPTER ONLY inputs; they say nothing about ROM data.
"""
from __future__ import annotations

import json
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "rom-cache" / "mapped-object-registration.json"

SPRITES = {  # type -> (sprite resource, original observation source, macro name or None)
    "0x09": ("SPR_chaos_object_09", ("loop_type09", "0x09", 1), "TYPE09_RENDER_Y"),
    "0x10": ("SPR_chaos_object_10_04", ("type10_param04_336_270", "0x10", 11), "TYPE10_RENDER_Y_ADAPTER"),
    "0x18": ("SPR_chaos_object_18", ("type18_3960_558", "0x18", 1), "TYPE18_RENDER_Y_ADAPTER"),
    "0x21": ("SPR_chaos_object_21", ("type21_param08_800_606", "0x21", 1), "TYPE21_RENDER_Y_ADAPTER"),
    "0x27": ("SPR_chaos_object_27", ("type27_2240_112", "0x27", 1), None),
    "0x28": ("SPR_chaos_platform", ("type28_592_464", "0x28", 1), None),
}


def read_png_alpha(path: Path):
    data = path.read_bytes()
    pos, idat, w = 8, b"", 0
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", body[:10])
            assert depth == 8 and ctype == 6, "expected 8-bit RGBA PNG"
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = w * 4
    rows, prev = [], bytearray(stride)
    p = 0
    for _ in range(h):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for i in range(stride):
            a = line[i - 4] if i >= 4 else 0
            b = prev[i]
            c = prev[i - 4] if i >= 4 else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        rows.append(line)
        prev = line
    return w, h, [[row[x * 4 + 3] for x in range(w)] for row in rows]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    poc = Path(sys.argv[1])
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    emu = cache["source_facts"]["emulated_original_frames"]
    adapter_src = next(poc.glob("scripts/SCR_chaos_render_adapter/*.gml")).read_text(encoding="utf-8")
    macros = {m.group(1): int(m.group(2)) for m in re.finditer(r"#macro\s+(\w+)\s+(-?\d+)", adapter_src)}
    print(f"{'type':5} {'sprite':24} {'adapter':>7} {'POC rows':>12} {'original':>12} {'POC-orig':>9}")
    for t, (spr, (case, typ, frame), macro) in SPRITES.items():
        yy = (poc / "sprites" / spr / f"{spr}.yy").read_text(encoding="utf-8")
        yorigin = int(re.search(r'"yorigin":\s*(-?\d+)', yy).group(1))
        first_frame = re.search(r'"%Name":\s*"([0-9a-fA-F-]+)"', yy[yy.index('"frames"'):]).group(1)
        _w, _h, alpha = read_png_alpha(poc / "sprites" / spr / f"{first_frame}.png")
        rows = [y for y, r in enumerate(alpha) if any(r)]
        adapter = macros.get(macro, 0) if macro else 0
        poc_rows = (rows[0] - yorigin + adapter, rows[-1] - yorigin + adapter)
        obs = next(o["object"] for o in (b for b in emu[case]["observations"])
                   if o["object"]["type"] == typ and o["object"]["frame_index"] == frame)
        orig = obs["opaque_world_rows_rel_anchor"]
        print(f"{t:5} {spr:24} {adapter:>+7} {str(poc_rows):>12} {str(orig):>12} {poc_rows[0] - orig[0]:>+4}/{poc_rows[1] - orig[1]:+d}")


if __name__ == "__main__":
    main()

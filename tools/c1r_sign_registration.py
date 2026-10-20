"""C1-R part C: goal-sign (object type $18) registration, ROM mapping versus the accepted POC sprite resources.

Compares only *opaque-pixel masks* (no artwork is stored or printed).  Inputs: the verified ROM and, optionally, the accepted POC checkout
(`poc/visual-p3-loop-presentation`, ac021e1).  Output: data/c1r/sign-registration.json (numbers and hashes only).

    python tools/c1r_sign_registration.py ROM [--poc PATH_TO_POC] [--write] [--check]
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import u3_sign_prizes as U  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "c1r" / "sign-registration.json"
CANVAS_W, CANVAS_H, ORIGIN_X, ORIGIN_Y = 32, 48, 16, 48     # POC sprite canvas, origin bottom-centre
POC_ADAPTER_Y = 22                                           # TYPE18_RENDER_Y_ADAPTER at ac021e1
ROM_TERRAIN_BIAS_Y = 18                                      # SAT +1, VScroll R9 = camY + 17  (docs/mapped-object-screen-registration.md)


def rom_mask(frame, tiles):
    x0, y0, _w, _h, rows = U.compose_frame(frame, tiles)
    return {(x0 + rx + ORIGIN_X, y0 + ry + ORIGIN_Y) for ry, r in enumerate(rows) for rx, v in enumerate(r) if v}


def poc_mask(sprite_dir, frame_name):
    from PIL import Image
    a = Image.open(sprite_dir / (frame_name + ".png")).convert("RGBA").getchannel("A")
    return {(x, y) for y in range(CANVAS_H) for x in range(CANVAS_W) if a.getpixel((x, y)) > 0}


def rows_of(mask):
    ys = sorted({y for _x, y in mask})
    return (ys[0], ys[-1]) if ys else None


def analyse(rom, poc):
    _table, frames = U.parse_mapping(rom, U.TYPE_SIGN)
    tiles = U.selector_tiles(rom, U.SEL_DEFAULT)
    out = {"rom_frames": [], "poc": []}
    refs = {}
    for f in frames[1:6]:
        m = rom_mask(f, tiles)
        refs[f["frame"]] = m
        out["rom_frames"].append({
            "frame": f["frame"], "pieces": len(f["pieces"]),
            "piece_origin_xy": [[p["x"], p["y"]] for p in f["pieces"]],
            "opaque_rows_on_canvas": rows_of(m), "opaque_pixels": len(m)})
    if poc is None:
        return out
    for spr in ("SPR_chaos_object_18", "SPR_chaos_thz_sign_prizes"):
        d = json.loads((poc / "sprites" / spr / (spr + ".yy")).read_text())
        sd = poc / "sprites" / spr
        row = {"sprite": spr, "canvas": [d["width"], d["height"]], "origin": [d["sequence"]["xorigin"], d["sequence"]["yorigin"]], "frames": []}
        if spr == "SPR_chaos_object_18":
            for i, fr in enumerate(d["frames"]):
                pm, rm = poc_mask(sd, fr["name"]), refs[i + 1]
                shifted = {(x, y + 4) for x, y in pm}
                row["frames"].append({
                    "rom_frame": i + 1, "poc_opaque_rows": rows_of(pm), "poc_pixels": len(pm), "rom_pixels": len(rm),
                    "xor_same_position": len(pm ^ rm),
                    "xor_if_poc_shifted_down_4": len(shifted ^ {p for p in rm if p[1] >= 4}),   # 0 => POC = ROM art minus its top 4 rows, 4 px high
                    "rom_rows_0_3_pixels": len({p for p in rm if p[1] < 4})})
        else:
            # prize sprites: frames 0..7 are selector $1B (Sonic face) uploads; compare the first eight with the ROM frame composed from $12 tiles overridden by $1B
            tiles_b = dict(tiles)
            tiles_b.update(U.selector_tiles(rom, 0x1B))
            rm = rom_mask(frames[1], tiles_b)
            for i, fr in enumerate(d["frames"][:8]):
                pm = poc_mask(sd, fr["name"])
                shifted = {(x, y + 4) for x, y in pm}
                row["frames"].append({"poc_frame": i, "poc_opaque_rows": rows_of(pm), "poc_pixels": len(pm), "rom_pixels": len(rm),
                                      "xor_same_position": len(pm ^ rm), "xor_if_poc_shifted_down_4": len(shifted ^ {p for p in rm if p[1] >= 4})})
        out["poc"].append(row)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--poc")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    rom = U.load_rom(a.rom)
    res = analyse(rom, Path(a.poc) if a.poc else None)
    res["schema"] = "c1r-sign-registration/1"
    res["rom_sha256"] = hashlib.sha256(Path(a.rom).read_bytes()).hexdigest()
    res["derived"] = {
        "rom_frame_extent_on_screen": "x -16..+15, y -48..-1 relative to the anchor (SAT line +1 => face origin = anchor-camera + (-16,-47))",
        "terrain_space_bias_y": ROM_TERRAIN_BIAS_Y,
        "expected_draw_y_offset_for_bottom_origin_canvas": ROM_TERRAIN_BIAS_Y,
        "poc_draw_y_offset": POC_ADAPTER_Y,
        "poc_extra_offset": POC_ADAPTER_Y - ROM_TERRAIN_BIAS_Y}
    text = json.dumps(res, indent=1, sort_keys=True) + "\n"
    if a.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text)
    print(text)


if __name__ == "__main__":
    main()

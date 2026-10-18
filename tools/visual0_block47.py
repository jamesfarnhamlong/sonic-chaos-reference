#!/usr/bin/env python3
"""VISUAL-0: THZ1 terrain block $47 break-up presentation (what the original actually draws).

Static chain (DECODED DATA / BYTE-VERIFIED ASSEMBLY):

    block $47 collision callback $6AE3 -> $7857
      $7857: D3B3 := 1 (dynamic tile selector), cell := $46, nametable refresh ($23F9),
             allocate type $0F param $40 at (cell X + 16, cell Y + 8)  via $5EB7
      type $0F param $40 init $A060: state 3, spawns type $11 param 0 at the same position via $0371 -> $5EB7
      type $0F state 3: FF 06 $AB, frames $07/$08/$09 (puff), 128-update empty record whose callback $A0C6 removes it
      type $11: rising icon, frame $0D for 32 updates, then removal ($A250)

Dynamic chain (EMULATED ORIGINAL FRAME): the real ROM boots THZ1 in ``tools/sms_frame_harness.py``, Sonic is placed so an
attack posture hits the first $47 cell, and objects, SAT, VRAM, nametable pixels and the sound mailbox are recorded each update.

``--poc PATH`` reads the GameMaker project READ-ONLY (sprite pixels, object source) and states the differences.

Usage:
    python tools/visual0_block47.py ROM [--output build/visual0-block47] [--poc PATH] [--metadata JSON] [--check] [--static-only]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import player_scripts as P  # noqa: E402,F401  (file_offset helper kept for symmetry with the Sonic catalogue)
import rom as R  # noqa: E402
import thz1_object_assets as A  # noqa: E402
from cache_game_data import decode_layout  # noqa: E402

GRAPHICS_MAP = ROOT / "data" / "rom-cache" / "thz1" / "graphics-map.json"
BLOCK_POINTER_TABLE = 0x44000
CELL_XS = (3328, 3360, 3392, 3424)
CELL_Y = 256
TYPE_0F_STATE_TABLE = 0x9FC9            # bank $0C, slot 2
TYPE_11_STATE_TABLE = 0xA22D
SELECTOR_TABLES = {"first_stream_pointers": 0x7CBB, "second_stream_pointers": 0x7CD3}   # player type $01
SELECTOR_DESTINATIONS = ((0x0980, 6), (0x0BC0, 4))
SOUND_PUFF = 0xAB


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hx(v: int, w: int = 2) -> str:
    return "0x%0*X" % (w, v)


def bank12(cpu: int) -> int:
    return 0x30000 + cpu - 0x8000


# ----------------------------------------------------------------------------------------------------------------
# static data
# ----------------------------------------------------------------------------------------------------------------
def block_art(rom: bytes, vram: bytes, block: int, bg_palette, spr_palette) -> dict:
    """Mode-4 background block: 4x4 name-table words from the block mapping (indexed 0..31 plus RGBA)."""
    entry = BLOCK_POINTER_TABLE + block * 2
    cpu = R.u16(rom, entry)
    mapping = BLOCK_POINTER_TABLE + cpu - 0x8000
    words = [R.u16(rom, mapping + 2 * i) for i in range(16)]
    indexed, rgba = bytearray(32 * 32), bytearray(32 * 32 * 4)
    for i, w in enumerate(words):
        tile, hf, vf, pal = w & 0x1FF, w & 0x200, w & 0x400, 16 if w & 0x800 else 0
        for py in range(8):
            row = A.decode_mode4_tile(bytes(vram[tile * 32:tile * 32 + 32]))[7 - py if vf else py]
            for px in range(8):
                c = row[7 - px if hf else px]
                q = ((i // 4) * 8 + py) * 32 + (i % 4) * 8 + px
                indexed[q] = (pal + c) if c else 0
                r, g, b, _ = (spr_palette if pal else bg_palette)[c]
                rgba[q * 4:q * 4 + 4] = bytes((r, g, b, 255))
    return OrderedDict(block=hx(block), pointer_entry_rom=hx(entry, 5), mapping_cpu=hx(cpu, 4), mapping_rom=hx(mapping, 5),
                       name_table_words=[hx(w, 4) for w in words], priority_words=sum(1 for w in words if w & 0x1000),
                       indexed_sha256=sha(bytes(indexed)), rgba_sha256=sha(bytes(rgba))), bytes(indexed), bytes(rgba)


def decode_state_table(rom: bytes, table_cpu: int, count: int, commands):
    base = bank12(table_cpu)
    starts = [R.u16(rom, base + 2 * i) for i in range(count)]
    out = OrderedDict()
    for st, start in enumerate(starts):
        notes = []
        steps, _ = P.parse_script(rom, start, commands, notes)
        ops = []
        for cpu in sorted(steps):
            kind, _, cmd = steps[cpu]
            off = bank12(cpu)
            if kind == "record":
                ops.append(OrderedDict(at=hx(cpu, 4), op="record", duration=rom[off], frame=hx(rom[off + 1]),
                                       callback=hx(R.u16(rom, off + 2), 4)))
            else:
                n = {0: 0, 1: 2, 2: 4, 3: 1, 6: 1, 7: 2, 14: 1, 15: 2}.get(cmd, None)
                arg = " ".join("%02X" % b for b in rom[off + 2:off + 2 + (n or 0)])
                ops.append(OrderedDict(at=hx(cpu, 4), op="FF %02X" % cmd, operands=arg))
        out[st] = OrderedDict(state=st, script_cpu=hx(start, 4), script_rom=hx(off if False else bank12(start), 5), ops=ops,
                              notes=notes)
    return out


def mapping_frames(rom: bytes, ids):
    m = A.object_mapping(rom, 0x0F)
    base = m["mapping_cpu"]
    out = OrderedDict()
    for f in ids:
        cpu = R.u16(rom, A.cpu15_to_rom(base) + 2 * f)
        out[f] = A.parse_frame_record(rom, cpu)
    return m, out


def selector_sources(rom: bytes, selector: int) -> list:
    out = []
    for name, table in SELECTOR_TABLES.items():
        ptr_rom = table + selector * 2
        cpu = R.u16(rom, ptr_rom)
        file = 0x38000 + cpu - 0x8000        # bank $0E
        (dest, tiles) = SELECTOR_DESTINATIONS[len(out)]
        raw = rom[file:file + tiles * 32]
        out.append(OrderedDict(stream=name, pointer_entry_rom=hx(ptr_rom, 5), source_cpu=hx(cpu, 4), source_rom=hx(file, 5),
                               vram_destination=hx(dest, 4), tiles=tiles, first_tile=hx(dest // 32), tile_bytes_sha256=sha(raw),
                               _raw=raw))
    return out


def render_frame(rom, parsed, vram, palette):
    r = A.render_frame(vram, parsed, 0, scale=1, margin=0, palette=palette)
    return r


def static_report(rom: bytes, output: Path | None):
    gm = json.loads(GRAPHICS_MAP.read_text(encoding="utf-8"))
    vram, _ = A.build_vram(rom, gm)
    bg_pal = A.palette_rgba(rom, A.THZ1_BACKGROUND_PALETTE)
    spr_pal = A.thz1_sprite_palette(rom)
    layout, _ = decode_layout(rom)
    cells = [OrderedDict(world=[x, CELL_Y], layout_index=(CELL_Y // 32) * 128 + x // 32,
                         block=hx(layout[(CELL_Y // 32) * 128 + x // 32])) for x in CELL_XS]
    a47, i47, rgba47 = block_art(rom, vram, 0x47, bg_pal, spr_pal)
    a46, i46, rgba46 = block_art(rom, vram, 0x46, bg_pal, spr_pal)
    commands = P.derive_commands(rom)
    t0f = decode_state_table(rom, TYPE_0F_STATE_TABLE, 5, commands)
    t11 = decode_state_table(rom, TYPE_11_STATE_TABLE, 2, commands)
    m, frames = mapping_frames(rom, (0x07, 0x08, 0x09, 0x0D))
    # common sprite tiles used by the puff ($24..$2D): static THZ1 VRAM image at level load
    selector1 = selector_sources(rom, 1)
    vram1 = bytearray(vram)
    for src, (dest, tiles) in zip(selector1, SELECTOR_DESTINATIONS):
        vram1[dest:dest + tiles * 32] = src["_raw"]
    rendered = OrderedDict()
    for f, parsed in frames.items():
        src_vram = vram1 if f == 0x0D else vram
        res = render_frame(rom, parsed, src_vram, spr_pal)
        w, h, rgba, meta = res
        b = meta["bounds"]
        rendered[hx(f)] = OrderedDict(mapping_cpu=hx(parsed["frame_cpu"], 4), mapping_rom=hx(parsed["frame_rom"], 5),
                                      pieces=[OrderedDict(y=p["relative_y"], x=p["relative_x"], tile=hx(p["tile_offset"]))
                                              for p in parsed["pieces"]],
                                      tile_pairs=[hx(p["tile_offset"]) + "+" + hx(p["tile_offset"] + 1) for p in parsed["pieces"]],
                                      bounds=OrderedDict(min_x=b["min_x"], min_y=b["min_y"], width=b["width"], height=b["height"]),
                                      opaque_pixels=meta["nonzero_source_pixels"], rgba_sha256_thz1_palette=sha(rgba))
        if output:
            A.write_rgba_png(output / ("type0F-frame-%02X.png" % f), w, h, rgba)
    if output:
        A.write_rgba_png(output / "block-47.png", 32, 32, rgba47)
        A.write_rgba_png(output / "block-46.png", 32, 32, rgba46)
    static = OrderedDict(
        cells=cells, blocks=OrderedDict([("0x47", a47), ("0x46", a46)]), type_0f_states=t0f, type_11_states=t11,
        mapping_table_cpu=hx(m["mapping_cpu"], 4), mapping_table_rom=hx(m["mapping_rom"], 5), mapping_note="types $0F and $11 share one mapping table",
        frames=rendered, selector_1=[OrderedDict((k, v) for k, v in s.items() if k != "_raw") for s in selector1],
        common_tile_source="puff tiles $24..$2D sit in the THZ1 supplemental stream bank $08 CPU $B340 -> VRAM $0200 (base tile $10); "
                           "docs/graphics.md",
    )
    return static, (vram, i47, i46)


# ----------------------------------------------------------------------------------------------------------------
# emulation
# ----------------------------------------------------------------------------------------------------------------
WORDS: dict = {}


def find_pattern(s, words):
    """Locations (nametable col,row) whose 4x4 words equal ``words`` (row-major)."""
    nb = (s.reg[2] & 0x0E) << 10
    nt = [s.vram[nb + 2 * i] | (s.vram[nb + 2 * i + 1] << 8) for i in range(32 * 28)]
    hits = []
    for r in range(28):
        for c in range(32):
            if all(nt[((r + j) % 28) * 32 + ((c + i) % 32)] == words[j * 4 + i] for j in range(4) for i in range(4)):
                hits.append((c, r))
    return hits


def find_pattern_at(s, words, col, row):
    nb = (s.reg[2] & 0x0E) << 10
    for j in range(4):
        for i in range(4):
            idx = ((row + j) % 28) * 32 + ((col + i) % 32)
            if (s.vram[nb + 2 * idx] | (s.vram[nb + 2 * idx + 1] << 8)) != words[j * 4 + i]:
                return False
    return True


def emulate(rom: bytes, output: Path | None, variant: str, cell: int, vram_static: bytes):
    """Drive the real ROM (THZ1) into one $47 cell and record the original response per object update and per video frame."""
    import object_18 as O
    from sms_frame_harness import BTN_RIGHT, BTN_DOWN, BTN_1  # noqa: F401
    s = O._boot(rom, 0, lambda m: None)
    m = s.mem
    ev = {"break": None, "entry": None, "sound": []}
    updates = []

    def at_entry(site):
        def hook(mm):
            ev["entry"] = site
        return hook

    def vh(lo, n):
        return sha(bytes(s.vram[lo:lo + n]))

    def at_break(mm):
        ev.update({"break": mm.frame, "player_state": mm.mem[0xD501], "player_flags_03": mm.mem[0xD503],
                   "y_velocity_hi": mm.mem[0xD519], "floor_contact_bits_22": mm.mem[0xD522], "side_bits_23": mm.mem[0xD523],
                   "map_cell": mm.u16(0xD354), "sample_x": mm.u16(0xD358), "sample_y": mm.u16(0xD35A), "d162": mm.mem[0xD162],
                   "vram_4C_51_before": vh(0x980, 192), "vram_5E_61_before": vh(0xBC0, 128),
                   "vram_24_2D_equals_static_thz1_vram": bytes(s.vram[0x480:0x5C0]) == bytes(vram_static[0x480:0x5C0])})

    def on_update(mm):
        ix = mm.cpu.ix
        if ev["break"] is not None and 0xD540 <= ix < 0xD540 + 16 * 0x40 and m[ix] in (0x0F, 0x11):
            updates.append(OrderedDict(video_frame=mm.frame - ev["break"], type=hx(m[ix]), state=m[ix + 1], frame=hx(m[ix + 6]),
                                       timer=m[ix + 7], x=mm.u16(ix + 0x11), y=mm.u16(ix + 0x14), flags_04=hx(m[ix + 4]),
                                       param=hx(m[ix + 0x3F])))

    for site, name in ((0x6B11, "$6B11 surface handler $6AE3 tail"), (0x7386, "$7386 side core, right-hand"),
                       (0x73A4, "$73A4 side core, left-hand")):
        s.add_pc_hook(site, at_entry(name))
    s.add_pc_hook(0x7857, at_break)
    s.add_pc_hook(0x7862, lambda mm: ev.update({"d3b3_after_store": mm.mem[0xD3B3]}))
    s.add_pc_hook(0x67E3, lambda mm: ev["sound"].append((mm.frame, mm.cpu.a)))
    s.add_pc_hook(0x5E91, on_update)
    left = CELL_XS[cell]
    land = None
    words47 = [int(w, 16) for w in WORDS["0x47"]]
    words46 = [int(w, 16) for w in WORDS["0x46"]]
    if variant == "top":
        s.w16(0xD511, left + 16); s._write(0xD510, 0); s.w16(0xD514, 190)
        m[0xD501] = m[0xD502] = 0x0A; m[0xD503] |= 0x03; s.w16(0xD516, 0); s.w16(0xD518, 0x0100)
    else:
        s.w16(0xD511, left - 128); s._write(0xD510, 0); s.w16(0xD514, 200)
        m[0xD501] = m[0xD502] = 0x0A; s.w16(0xD516, 0); s.w16(0xD518, 0x0100)
    ring_before = m[0xD29A]
    frames_out, last_pre = [], None
    tick = None

    for f in range(900):
        pad = 0
        if variant == "top" and f < 45:
            s.w16(0xD514, 190); s.w16(0xD518, 0)           # let the camera arrive before the fall
        if variant == "spindash":
            if land is None and (m[0xD522] & 2) and f > 20:
                land = f
            if land is not None:
                t = f - land
                pad = 0 if t < 10 else (BTN_DOWN if t < 14 else (BTN_DOWN | (BTN_1 if t % 2 == 0 else 0) if t < 26 else BTN_RIGHT))
        s.pad = pad
        if ev["break"] is None and f % 6 == 0 and f > 5:
            found = find_pattern(s, words47)
            if found:
                last_pre = found
        s.run_frame()
        if ev["break"] is not None and tick is None:
            tick = 0
        if tick is None:
            continue
        cx, cy = s.u16(0xD174), s.u16(0xD176)
        sat = [OrderedDict(entry=i, tile=hx(n), screen_x=x, screen_top=y + 1, world_x=x + cx, world_top=y + 1 + cy)
               for i, y, x, n in s.sat() if n in (0x24, 0x26, 0x28, 0x2A, 0x2C, 0x5E, 0x60)]
        if tick == 1:
            ev["vram_4C_51_after"] = vh(0x980, 192)
            ev["vram_5E_61_after"] = vh(0xBC0, 128)
        frames_out.append(OrderedDict(video_frame=tick, effect_sat=sat, d3b3=m[0xD3B3], ring_bcd_d29a=hx(m[0xD29A])))
        if tick in (1, 3, 5, 9, 13, 21, 29, 37, 40) and output:
            from PIL import Image
            rgb, _, _, _ = s.render()
            hs, vs = s.line_regs[100][1], s.vscroll_latched
            sx, sy = (left + hs) & 255, (CELL_Y - vs) % 224
            w, h = 96, 128
            px0, py0 = max(0, min(160, sx - 32)), max(0, min(64, sy - 64))
            img = Image.new("RGB", (w, h))
            img.putdata([rgb[py0 + yy][px0 + xx] if py0 + yy < 192 and px0 + xx < 256 else (0, 0, 0)
                         for yy in range(h) for xx in range(w)])
            img.resize((w * 4, h * 4), Image.NEAREST).save(output / ("emu-%s-cell%d-frame%02d.png" % (variant, cell, tick)))
        tick += 1
        if tick > 70:
            break
    keys = ("player_state", "player_flags_03", "y_velocity_hi", "floor_contact_bits_22", "side_bits_23", "map_cell", "sample_x",
            "sample_y", "d162", "d3b3_after_store", "vram_4C_51_before", "vram_4C_51_after", "vram_5E_61_before",
            "vram_5E_61_after", "vram_24_2D_equals_static_thz1_vram")
    return OrderedDict(
        variant=variant, cell=cell, entry_path=ev["entry"],
        break_registers=OrderedDict((k, ev[k]) for k in keys if k in ev),
        sound_requests=[OrderedDict(video_frame=f_ - ev["break"], value=hx(v)) for f_, v in ev["sound"]],
        ring_bcd_before=hx(ring_before), ring_bcd_after=hx(m[0xD29A]),
        nametable_block_47_pattern_locations_before_break=[list(x) for x in (last_pre or [])],
        nametable_at_those_locations_after_break=[
            OrderedDict(col=c, row=r, content="block_46" if find_pattern_at(s, words46, c, r) else
                        "block_47" if find_pattern_at(s, words47, c, r) else "other") for c, r in (last_pre or [])],
        object_updates=updates, video_frames=frames_out)


def summarise(run) -> OrderedDict:
    ups = run["object_updates"]
    t0f = [u for u in ups if u["type"] == "0x0F"]
    t11 = [u for u in ups if u["type"] == "0x11"]

    def seen(tiles):
        fr = [r["video_frame"] for r in run["video_frames"] if any(e["tile"] in tiles for e in r["effect_sat"])]
        return (min(fr), max(fr)) if fr else None

    return OrderedDict(
        type_0F_updates=len(t0f), type_11_updates=len(t11),
        type_0F_frame_runs=_runs([u["frame"] for u in t0f]), type_11_frame_runs=_runs([u["frame"] for u in t11]),
        type_11_y_by_update=[u["y"] for u in t11], type_0F_position=sorted({(u["x"], u["y"]) for u in t0f}),
        type_11_x=sorted({u["x"] for u in t11}),
        puff_visible_video_frames_first_last=seen({"0x24", "0x26", "0x28", "0x2A", "0x2C"}),
        icon_visible_video_frames_first_last=seen({"0x5E", "0x60"}))


def _runs(seq):
    out = []
    for v in seq:
        if out and out[-1][0] == v:
            out[-1][1] += 1
        else:
            out.append([v, 1])
    return [[a, b] for a, b in out]


# ----------------------------------------------------------------------------------------------------------------
# POC (read-only)
# ----------------------------------------------------------------------------------------------------------------
def poc_report(poc: Path, rom: bytes, static) -> dict:
    sys.path.insert(0, str(ROOT / "tools"))
    import visual0_sonic_catalogue as C
    out = OrderedDict()
    spr = poc / "sprites" / "SPR_chaos_object_0F"
    yy = json.loads((spr / "SPR_chaos_object_0F.yy").read_text(encoding="utf-8"))
    out["sprite"] = OrderedDict(resource="SPR_chaos_object_0F", width=yy["width"], height=yy["height"],
                                xorigin=yy["sequence"]["xorigin"], yorigin=yy["sequence"]["yorigin"], frames=len(yy["frames"]))
    gm = json.loads(GRAPHICS_MAP.read_text(encoding="utf-8"))
    vram, _ = A.build_vram(rom, gm)
    pal = A.thz1_sprite_palette(rom)
    mapping, frames = mapping_frames(rom, (7, 8, 9))
    rom_trim = {}
    for f, parsed in frames.items():
        w, h, rgba, meta = render_frame(rom, parsed, vram, pal)
        rom_trim[f] = C.trim(w, h, rgba)
    cmp = []
    for idx, png in enumerate(sorted(spr.glob("*.png"))):
        dec = C.png_rgba(png)
        t = C.trim(*dec) if dec else None
        row = OrderedDict(image=idx, file=png.name)
        if t:
            for f, rt in rom_trim.items():
                if rt and (rt[0], rt[1]) == (t[0], t[1]) and rt[2] == t[2]:
                    row["rom_frame_rgba_equal"] = hx(f)
        cmp.append(row)
    out["pixel_comparison_thz1_palette"] = cmp
    obj = (poc / "objects" / "OBJ_chaos_object_0F_transient" / "Step_0.gml").read_text(encoding="utf-8")
    out["transient_step_source_sha256"] = sha(obj.encode())
    out["has_type_11_object"] = (poc / "objects" / "OBJ_chaos_object_11").exists() or any(
        "object_11" in p.name.lower() and p.name.startswith("OBJ_chaos") for p in (poc / "objects").iterdir())
    out["block47_adapter"] = "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml SCR_chaos_block47_step: creates OBJ_chaos_object_0F_transient only"
    return out


def build(rom: bytes, output: Path | None = None, poc: Path | None = None, static_only: bool = False) -> dict:
    if sha(rom) != R.SHA256:
        raise ValueError("ROM SHA-256 mismatch")
    if output:
        output.mkdir(parents=True, exist_ok=True)
    static, (vram, i47, i46) = static_report(rom, output)
    WORDS.update({k: v["name_table_words"] for k, v in static["blocks"].items()})
    report = OrderedDict(format=1, rom_sha256=sha(rom), evidence="DECODED DATA + BYTE-VERIFIED ASSEMBLY + EMULATED ORIGINAL FRAME",
                         static=static)
    if not static_only:
        runs = [("top", 0), ("spindash", 0)]
        report["emulated"] = []
        for variant, cell in runs:
            r = emulate(rom, output, variant, cell, vram)
            r["summary"] = summarise(r)
            report["emulated"].append(r)
    if poc:
        report["poc"] = poc_report(poc, rom, static)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--poc", type=Path)
    p.add_argument("--metadata", type=Path)
    p.add_argument("--check", action="store_true")
    p.add_argument("--static-only", action="store_true")
    a = p.parse_args()
    rep = build(R.load(a.rom), a.output, a.poc, a.static_only)
    text = json.dumps(rep, indent=1) + "\n"
    if a.metadata:
        if a.check:
            if a.metadata.read_text(encoding="utf-8") != text:
                sys.exit("metadata differs: " + str(a.metadata))
            print("metadata identical")
        else:
            a.metadata.parent.mkdir(parents=True, exist_ok=True)
            a.metadata.write_text(text, encoding="utf-8")
    print(json.dumps({"emulated_runs": len(rep.get("emulated", []))}))


if __name__ == "__main__":
    main()

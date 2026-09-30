#!/usr/bin/env python3
"""Mapped-object screen registration research (object anchor -> visible pixels).

Question: what does the original Sonic Chaos engine do between an object's stored
world coordinate and the final visible sprite pixels?

Evidence classes used in the output (see docs/mapped-object-screen-registration.md):
  BYTE-VERIFIED ASSEMBLY      routine bytes compared with literal expected bytes below
  DECODED DATA                mapping tables / frame records / placement records
  CONTROLLED ROUTINE RESULT   original Z80 routines executed on explicit RAM (RenderOracle)
  EMULATED ORIGINAL FRAME     original game booted in tools/sms_frame_harness.py; its own
                              RAM/VDP state is read back (approximate VDP, exact game code)
  GAMEMAKER ADAPTER ONLY      values read from the POC checkpoint; never ROM facts
  UNRESOLVED

Usage:
  python tools/mapped_object_registration.py ROM --output data/rom-cache/mapped-object-registration.json
  python tools/mapped_object_registration.py ROM --check data/rom-cache/mapped-object-registration.json
  python tools/mapped_object_registration.py ROM --static-only   # skip the emulated-frame section
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import rom as romlib  # noqa: E402
import thz1_object_assets as assets  # noqa: E402

ROM_SHA256 = romlib.SHA256
CONTROL_TYPES = (0x09, 0x10, 0x18, 0x1B, 0x21, 0x26, 0x27, 0x28)

# --------------------------------------------------------------------------- #
# 1. Byte-verified routines.  Expected bytes were transcribed from the ROM and
#    are compared literally; a mismatch means the analysis no longer applies.
# --------------------------------------------------------------------------- #
BYTE_CHECKS = (
    ("slot_render_loop", 0x220E, "dd2100d52100db226fd32140db2271d30614afddb605ca4a22dd7e003dfeef301bc5dd4e04cb69c43523cb79200dcb712009cdc83fcd6a22cdb622c1114000dd1910cf"),
    ("screen_coordinate_prep", 0x3FC8, "dd6e11dd6612ed5b74d1afed52dd751add741bdd6e14dd6615ed5b76d1afed52dd751cdd741dc9"),
    ("y_renderer", 0x226A, "fd2a6fd3dd662bdd6e2a5e2356dd6e1cdd661d19e5d9dd5629dd5e28c1d9dd4605d91a6f131a671309fd75003e40856f3001247cb720057dfe303004fd3600e01313fd23d910dafd226fd3c9"),
    ("x_tile_renderer", 0x22B6, "fd2a71d3dd662bdd6e2a23235e2356ddcb046628071b7b2f5f7a2f57234e2346ed4310d1dd6e1add661b19e5d9dd5629dd5e281313ddcb0466280521080d19ebc1d9dd4605d91a6f131a671309fd75007cb72804fd3600001313fd232a10d17eddcb04662805dd86091803dd8608fd7700232210d1fd23d910cbfd2271d3c9"),
    ("flicker_toggle", 0x2335, "dd342edd7e2e0f0f3805ddcb04bec9ddcb04fec9"),
    ("camera_to_vdp_scroll_regs", 0x4D3E, "3a74d1c601ed443272d12a76d11111001911e000afed5230fb197d3273d1c9"),
    ("vblank_scroll_register_output", 0x538, "4806194e23463a72d180d3bf3e88d3bf3a73d181d3bf3e89d3bf"),
    ("sat_upload_head", 0x1E36, "2134d1afb6c836003a2fd10fdae41f3e00d3bf3e3ff640d3bf2100db0ebe"),
    ("vdp_register_init_table", 0x1D2D, "2682fffffffffb000000ff"),
    ("frame_record_select", 0x6567, "dd6e00260029110080195e2356dd6e06260029195e2356eb7eddcb045e280ab728073c28013df680afdd7705237edd772c237edd772d237edd7728237edd772923dd752add742bc9"),
    ("placement_create", 0x700EB, "c5cd2903c138497efd770002237efd773afd7711237e3dfd773bfd7712237efd773cfd7714237e3dfd773dfd7715237ef640fd7704237efd773f237efd7708237efd770969601100d4afed522cfd753ec9d9c9"),
    # object-floor probe adds $0012 to the anchor Y (docs/thz1-visual-anchor-closure.md)
    ("object_floor_probe_plus_18", 0x7690, "11120019cb7c"),
)

# File offset -> (bank, CPU address) for the Sega mapper's default layout.
def bank_cpu(offset: int) -> tuple[int, int]:
    if offset < 0x4000:
        return 0, offset
    if offset < 0x8000:
        return 1, offset          # slot 1 (bank 1 unless the game re-pages $FFFE)
    return offset // 0x4000, 0x8000 + offset % 0x4000


def routine_checks(rom: bytes) -> list[dict]:
    out = []
    for name, off, hexs in BYTE_CHECKS:
        want = bytes.fromhex(hexs)
        got = rom[off:off + len(want)]
        bank, cpu = bank_cpu(off)
        out.append({
            "name": name, "rom_offset": f"0x{off:05X}", "bank": bank, "cpu": f"0x{cpu:04X}",
            "length": len(want), "bytes": got.hex(), "verified": got == want,
            "evidence": "BYTE-VERIFIED ASSEMBLY",
        })
    return out


# --------------------------------------------------------------------------- #
# 2. Pure-Python model of $3FC8 / $226A / $22B6 (checked against the Z80 result)
# --------------------------------------------------------------------------- #
def s16(v: int) -> int:
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def _r16_15(rom: bytes, cpu: int) -> int:
    """16-bit read through CPU slot 2 with bank $0F mapped (the state during rendering)."""
    return assets.u16(rom, assets.cpu15_to_rom(cpu))


def model_slot(rom: bytes, *, obj_x: int, obj_y: int, cam_x: int, cam_y: int,
               frame_cpu: int, flags: int, art0: int, art1: int) -> list[dict]:
    """Recompute the SAT bytes the original renderer writes for one slot.

    Mirrors $3FC8 (camera subtraction), $226A (Y) and $22B6 (X, tile).  Bank $0F is
    mapped in CPU slot 2 while these run (LD A,15 / LD ($FFFF),A at $05B6/$0716).
    """
    fr = assets.cpu15_to_rom(frame_cpu)
    count = rom[fr]
    coords = assets.u16(rom, fr + 3)
    y_org = assets.u16(rom, fr + 5)
    x_org = assets.u16(rom, fr + 7)
    tiles = assets.u16(rom, fr + 9)
    flip = bool(flags & 0x10)
    scr_x = (obj_x - cam_x) & 0xFFFF
    scr_y = (obj_y - cam_y) & 0xFFFF
    if flip:
        x_org = (-x_org) & 0xFFFF
    by = (scr_y + y_org) & 0xFFFF
    bx = (scr_x + x_org) & 0xFFFF
    xtab = coords + 2 + (0x0D08 if flip else 0)
    out = []
    for i in range(count):
        py = assets.u16(rom, assets.cpu15_to_rom(coords + 4 * i))
        y16 = (py + by) & 0xFFFF
        chk = y16 + 0x40
        hidden = (chk >> 8) != 0 or (chk & 0xFF) < 0x30      # $229A..$22A6
        ybyte = 0xE0 if hidden else (y16 & 0xFF)
        px = assets.u16(rom, assets.cpu15_to_rom(xtab + 4 * i))
        x16 = (px + bx) & 0xFFFF
        xbyte = (x16 & 0xFF) if (x16 >> 8) == 0 else 0        # $2306..$230C
        tile = (rom[assets.cpu15_to_rom(tiles + i)] + (art1 if flip else art0)) & 0xFF
        out.append({"piece": i, "piece_y": s16(py), "piece_x": s16(px), "y16": s16(y16),
                    "sat_y": ybyte, "hidden_by_y_clip": hidden, "x16": s16(x16),
                    "sat_x": xbyte, "x_clipped_to_0": (x16 >> 8) != 0, "tile": tile})
    return out


# --------------------------------------------------------------------------- #
# 3. Controlled execution of the original routines
# --------------------------------------------------------------------------- #
class RenderOracle:
    """Run $6567 (frame select), $3FC8, $226A, $22B6 on explicit slot RAM."""
    RETURN = 0x0100

    def __init__(self, rom: bytes):
        import z80
        self.rom = rom
        self.cpu = z80.Z80Machine()
        self.mem = self.cpu.memory
        self.mem[:0x8000] = rom[:0x8000]
        self._bank(2, 15)
        self.cpu.set_write_callback(self._write)
        self.cpu.mark_addrs(0, 0xC000, self.cpu.WRITE_MARK)
        self.cpu.mark_addrs(0xFFFD, 3, self.cpu.WRITE_MARK)
        self.cpu.set_breakpoint(self.RETURN)

    def _bank(self, slot, bank):
        s = slot * 0x4000
        self.mem[s:s + 0x4000] = self.rom[(bank & 31) * 0x4000:(bank & 31) * 0x4000 + 0x4000]

    def _write(self, address, value):
        if address < 0xC000:
            return
        self.mem[address] = value
        if address == 0xFFFF:
            self._bank(2, value)

    def w16(self, a, v):
        self.mem[a:a + 2] = (v & 0xFFFF).to_bytes(2, "little")

    def call(self, address):
        self.cpu.pc = address
        self.cpu.sp = 0xDFE0
        self.w16(self.cpu.sp, self.RETURN)
        for _ in range(20):
            self.cpu.ticks_to_stop = 100000
            self.cpu.run()
            if self.cpu.pc == self.RETURN:
                return
        raise RuntimeError(f"${address:04X} did not return")

    def render(self, *, type_id, frame_index, obj_x, obj_y, cam_x, cam_y, flags, art0, art1):
        ix = 0xD500
        for i in range(0x40):
            self.mem[ix + i] = 0
        self.cpu.ix = ix
        self.mem[ix + 0] = type_id
        self.mem[ix + 4] = flags
        self.mem[ix + 6] = frame_index
        self.mem[ix + 8] = art0
        self.mem[ix + 9] = art1
        self.w16(ix + 0x11, obj_x)
        self.w16(ix + 0x14, obj_y)
        self.w16(0xD174, cam_x)
        self.w16(0xD176, cam_y)
        self.w16(0xD36F, 0xDB00)
        self.w16(0xD371, 0xDB40)
        self.mem[0xDB00:0xDB80] = b"\xf0" * 64 + b"\x00" * 64
        self.call(0x6567)   # original frame-record -> slot-field loader
        count = self.mem[ix + 5]
        frame_ptr = self.mem[ix + 0x2A] | (self.mem[ix + 0x2B] << 8)
        self.call(0x3FC8)
        scr = (self.mem[ix + 0x1A] | self.mem[ix + 0x1B] << 8,
               self.mem[ix + 0x1C] | self.mem[ix + 0x1D] << 8)
        self.call(0x226A)
        self.call(0x22B6)
        return {
            "piece_count": count, "frame_record_field_2A": f"0x{frame_ptr:04X}",
            "screen_xy_after_3FC8": [s16(scr[0]), s16(scr[1])],
            "sat_y": list(self.mem[0xDB00:0xDB00 + count]),
            "sat_x": [self.mem[0xDB40 + 2 * i] for i in range(count)],
            "sat_tile": [self.mem[0xDB41 + 2 * i] for i in range(count)],
        }


# --------------------------------------------------------------------------- #
# 4. Mapping data for the control types
# --------------------------------------------------------------------------- #
ART_BASES = {0x09: (0x00, 0x00), 0x10: (0x00, 0x00), 0x18: (0x00, 0x00), 0x1B: (0x00, 0x00),
             0x21: (0x86, 0x98), 0x26: (0x72, 0x72), 0x27: (0xAA, 0xAA), 0x28: (0x6A, 0x6A)}


def mapping_data(rom: bytes) -> dict:
    out = {}
    for t in CONTROL_TYPES:
        m = assets.object_mapping(rom, t)
        frames = assets.mapping_frame_pointers(rom, m["mapping_cpu"])
        recs = {}
        for idx, fp in enumerate(frames):
            r = assets.parse_frame_record(rom, fp)
            if not r["piece_count"]:
                continue
            mirrored_ok = True
            for p in r["pieces"]:
                mir = s16(assets.u16(rom, assets.cpu15_to_rom(r["coords_cpu"] + 2 + 0x0D08 + 4 * p["index"])))
                mirrored_ok &= (mir == -p["x_offset"] - 8)
            recs[str(idx)] = {
                "frame_record_cpu": f"0x{fp:04X}", "frame_record_rom": f"0x{r['frame_rom']:05X}",
                "piece_count": r["piece_count"], "y_origin": r["y_origin"], "x_origin": r["x_origin"],
                "piece_y_offsets": [p["y_offset"] for p in r["pieces"]],
                "piece_x_offsets": [p["x_offset"] for p in r["pieces"]],
                "tile_offsets": r["tile_offsets"],
                "mapped_y_range_rel_anchor": [min(p["relative_y"] for p in r["pieces"]),
                                              max(p["relative_y"] for p in r["pieces"]) + 15],
                "mapped_x_range_rel_anchor": [min(p["relative_x"] for p in r["pieces"]),
                                              max(p["relative_x"] for p in r["pieces"]) + 7],
                "mirror_table_is_neg_x_minus_8": mirrored_ok,
            }
        bank, cpu = bank_cpu(m["mapping_rom"])
        out[f"0x{t:02X}"] = {
            "pointer_table_entry_rom": f"0x{m['pointer_table_rom']:05X}",
            "mapping_table_cpu": f"0x{m['mapping_cpu']:04X}", "mapping_table_rom": f"0x{m['mapping_rom']:05X}",
            "mapping_bank": bank, "art_base_normal_aux0": f"0x{ART_BASES[t][0]:02X}",
            "art_base_flipped_aux1": f"0x{ART_BASES[t][1]:02X}",
            "frames": recs, "evidence": "DECODED DATA",
        }
    return out


# --------------------------------------------------------------------------- #
# 5. Emulated original frames
# --------------------------------------------------------------------------- #
# name -> (Sonic start, camera start, frames to run, held buttons per frame index)
EMU_CASES = {
    "loop_type09": ((2800, 420), (2752, 300), 36, None),
    "twist_type09": ((3060, 500), (3000, 440), 36, None),
    "post_twist_type09": ((3330, 800), (3300, 720), 36, None),
    "type10_param04_336_270": ((300, 270), (250, 200), 30, None),
    "type10_param04_1472_110": ((1440, 110), (1380, 40), 30, None),
    "type10_param06_1712_494": ((1650, 480), (1600, 420), 30, None),
    "type21_param08_800_606": ((700, 590), (680, 520), 30, None),
    "type27_2240_112": ((2210, 100), (2150, 40), 30, None),
    "type28_592_464": ((520, 440), (500, 380), 30, None),
    "type1B_1344_864": ((1290, 846), (1200, 780), 100, None),
    "type18_3960_558": ((3880, 540), (3850, 480), 30, None),
    "type26_688_864": ((690, 820), (600, 720), 60, None),
}
BG_ALIGN_CASES = ("loop_type09", "type21_param08_800_606", "type1B_1344_864")
INTERESTING = {0x09, 0x10, 0x18, 0x1B, 0x21, 0x26, 0x27, 0x28}


LAST_MACHINE = {}


def _emulate_case(rom: bytes, name: str, spec) -> list[dict]:
    from sms_frame_harness import SMS, BTN_1, BTN_2

    sonic, cam, frames, _ = spec
    s = SMS(rom)
    snaps: list[dict] = []

    def snapshot(m):
        snaps.append({"frame": m.frame, "ram": bytes(m.mem[0xC000:0xE000])})
        del snaps[:-4]

    s.add_pc_hook(0x2251, snapshot)           # end of the 20-slot render loop, before SAT tail fill
    state = {"done": False}

    def start(m):
        if m.frame > 900 and not state["done"]:   # THZ1 start-position loader ($4E57) return
            m.w16(0xD2D6, cam[0]); m.w16(0xD2D8, cam[1])
            m.w16(0xD511, sonic[0]); m.w16(0xD514, sonic[1])
            state["done"] = True

    s.add_pc_hook(0x4E97, start)
    f = 0
    while True:
        if f < 250:
            s.pad = 0
        elif f < 700:
            s.pad = BTN_1 if f % 40 < 3 else 0
        elif not state["done"]:
            s.pad = (BTN_1 | BTN_2) if f % 60 < 10 else 0
        else:
            s.pad = 0
        s.run_frame(); f += 1
        if state["done"] and s.mem[0xD500] == 1 and s.u16(0xD176) > 0:
            break
        if f > 4000:
            raise RuntimeError("did not reach gameplay")
    results = []
    for i in range(frames):
        s.pad = 0
        s.run_frame()
        rec = _observe(s, rom, snaps)
        if rec:
            rec["frames_after_start"] = i + 1
            results.append(rec)
    LAST_MACHINE["s"] = s
    return results


def _observe(s, rom, snaps):
    vr = sorted(y for _, y, _, _ in s.sat())
    snap = None
    for sn in reversed(snaps):
        buf = []
        for y in sn["ram"][0xDB00 - 0xC000:0xDB40 - 0xC000]:
            if y == 0xD0:
                break
            buf.append(y)
        if sorted(buf) == vr:
            snap = sn
            break
    if snap is None:
        return None
    ram = snap["ram"]

    def r16(a):
        return ram[a - 0xC000] | (ram[a - 0xC000 + 1] << 8)

    cam_x, cam_y = r16(0xD174), r16(0xD176)
    if s.vscroll_latched != (cam_y + 17) % 224 or s.line_regs[100][1] != ((-(cam_x + 1)) & 255):
        return None       # camera changed between SAT build and VDP register latch
    pat = 256 if (s.reg[6] & 4) else 0
    objs = []
    rendered = []
    for k in range(20):
        ix = 0xD500 + k * 0x40
        t = ram[ix - 0xC000]
        cnt = ram[ix - 0xC000 + 5]
        fl = ram[ix - 0xC000 + 4]
        if cnt == 0 or ((t - 1) & 255) >= 0xEF or fl & 0xC0:
            continue
        fp = r16(ix + 0x2A)
        frame_cpu = fp - 5
        frame_index = ram[ix - 0xC000 + 6]
        pieces = model_slot(rom, obj_x=r16(ix + 0x11), obj_y=r16(ix + 0x14), cam_x=cam_x, cam_y=cam_y,
                            frame_cpu=frame_cpu, flags=fl, art0=ram[ix - 0xC000 + 8], art1=ram[ix - 0xC000 + 9])
        rendered.append((k, ix, t, fl, frame_index, frame_cpu, pieces))
    # exact SAT reconstruction check across all slots
    rebuilt = [(p["sat_y"], p["sat_x"], p["tile"]) for *_a, pieces in rendered for p in pieces]
    buf = [(ram[0xDB00 - 0xC000 + i], ram[0xDB40 - 0xC000 + 2 * i], ram[0xDB41 - 0xC000 + 2 * i])
           for i in range(len(rebuilt))]
    if rebuilt != buf:
        return None
    _rgb, layer, _bg, _sp = s.render()
    for k, ix, t, fl, frame_index, frame_cpu, pieces in rendered:
        if t not in INTERESTING:
            continue
        opaque_screen = set()
        for p in pieces:
            if p["hidden_by_y_clip"]:
                continue
            n = p["tile"] & 0xFE
            for r in range(16):
                tb = (pat + n + (r >> 3)) * 32 + (r & 7) * 4
                b = s.vram[tb:tb + 4]
                for c in range(8):
                    bit = 7 - c
                    if ((b[0] | b[1] | b[2] | b[3]) >> bit) & 1:
                        lx = p["sat_x"] + c
                        ly = p["y16"] + 1 + r
                        opaque_screen.add((ly, lx, p["x_clipped_to_0"]))
        if not opaque_screen:
            continue
        ys = [y for y, _x, _c in opaque_screen]
        xs = [x for _y, x, c in opaque_screen if not c]
        vis = {y for (y, x, c) in opaque_screen if 0 <= y < 192 and 0 <= x < 256 and layer[y][x] == "S"}
        ox, oy = r16(ix + 0x11), r16(ix + 0x14)
        objs.append({
            "slot": k, "type": f"0x{t:02X}", "runtime_anchor": [ox, oy], "flags_04": f"0x{fl:02X}",
            "frame_index": frame_index, "frame_record_cpu": f"0x{frame_cpu:04X}",
            "pieces": [{k2: v for k2, v in p.items()} for p in pieces],
            "opaque_screen_lines": [min(ys), max(ys)],
            "opaque_world_rows_bg_space": [cam_y + 17 + min(ys), cam_y + 17 + max(ys)],
            "opaque_world_rows_rel_anchor": [cam_y + 17 + min(ys) - oy, cam_y + 17 + max(ys) - oy],
            "opaque_world_cols_bg_space": [cam_x + 1 + min(xs), cam_x + 1 + max(xs)] if xs else None,
            "opaque_world_cols_rel_anchor": [cam_x + 1 + min(xs) - ox, cam_x + 1 + max(xs) - ox] if xs else None,
            "visible_after_bg_priority_rows": len(vis),
            "visible_after_bg_priority_screen_lines": [min(vis), max(vis)] if vis else None,
        })
    if not objs:
        return None
    return {
        "camera_D174_D176": [cam_x, cam_y], "vdp_r8_hscroll": s.line_regs[100][1], "vdp_r9_vscroll": s.vscroll_latched,
        "r0": s.reg[0], "r1": s.reg[1], "r5": s.reg[5], "r6": s.reg[6],
        "sat_rebuilt_exactly_from_model": True, "objects": objs,
    }


def background_alignment(s, rom, world) -> dict:
    """Best (dy, dx) such that VDP background pixel (x, y) == decoded terrain pixel
    (cam_x + dx + x, cam_y + dy + y), sampled every 3rd pixel outside column 0..7."""
    cam_x, cam_y = s.u16(0xD174), s.u16(0xD176)
    _rgb, _layer, bgi, _sp = s.render()
    best = []
    for dy in range(-40, 41):
        for dx in range(-8, 9):
            match = tot = 0
            for y in range(0, 192, 3):
                wy = cam_y + dy + y
                if wy < 0:
                    continue
                for x in range(8, 256, 3):
                    wx = cam_x + dx + x
                    if wx < 0:
                        continue
                    v = bgi[y][x]
                    v = 0 if v & 15 == 0 else v
                    tot += 1
                    match += (v == world[wy * 4096 + wx])
            best.append((match / tot, dy, dx))
    best.sort(reverse=True)
    return {"camera_at_measurement": [cam_x, cam_y], "vdp_r8_r9": [s.line_regs[100][1], s.vscroll_latched],
            "best_dy": best[0][1], "best_dx": best[0][2], "best_match_fraction": round(best[0][0], 4),
            "runner_up": {"dy": best[1][1], "dx": best[1][2], "match_fraction": round(best[1][0], 4)},
            "meaning": "background screen (x, y) shows terrain-space (cam_x + best_dx + x, cam_y + best_dy + y)"}


def emulated_section(rom: bytes) -> dict:
    import thz1_background_registration as bgreg
    world, _layout, _meta = bgreg.render_indices(rom)
    out = {}
    for name, spec in EMU_CASES.items():
        recs = _emulate_case(rom, name, spec)
        # keep the first record per distinct (type, frame, anchor_y) so changes in state are visible
        seen, keep = set(), []
        for rec in recs:
            for o in rec["objects"]:
                key = (o["type"], o["frame_index"], o["runtime_anchor"][1])
                if key in seen:
                    continue
                seen.add(key)
                keep.append({"frames_after_start": rec["frames_after_start"],
                             "camera_D174_D176": rec["camera_D174_D176"], "vdp_r8_hscroll": rec["vdp_r8_hscroll"],
                             "vdp_r9_vscroll": rec["vdp_r9_vscroll"], "object": o})
        entry = {"evidence": "EMULATED ORIGINAL FRAME", "observations": keep}
        if name in BG_ALIGN_CASES:
            entry["background_alignment"] = background_alignment(LAST_MACHINE["s"], rom, world)
        out[name] = entry
    return out


# --------------------------------------------------------------------------- #
# 6. Controlled-routine fixtures (Z80 execution of the original renderer code)
# --------------------------------------------------------------------------- #
FIXTURES = (
    # name, type, frame, anchor (placement world coords), camera, flags
    ("type09_loop_2880_384", 0x09, 1, (2880, 384), (2704, 308), 0x00),
    ("type09_twist_3124_548", 0x09, 1, (3124, 548), (2964, 446), 0x00),
    ("type09_twist_3160_522", 0x09, 1, (3160, 522), (2964, 446), 0x00),
    ("type09_twist_3208_512", 0x09, 1, (3208, 512), (2964, 446), 0x00),
    ("type10_param04_336_270", 0x10, 11, (336, 270), (250, 200), 0x00),
    ("type21_standing_800_590", 0x21, 1, (800, 590), (604, 490), 0x10),
    ("type27_2237_112", 0x27, 1, (2237, 112), (2114, 60), 0x10),
    ("type28_592_463", 0x28, 1, (592, 463), (424, 382), 0x00),
    ("type1B_rest_1344_864", 0x1B, 14, (1344, 864), (1194, 746), 0x00),
    ("type1B_raised_1344_846", 0x1B, 14, (1344, 846), (1194, 746), 0x00),
    ("type18_3960_558", 0x18, 1, (3960, 558), (3784, 446), 0x00),
    ("type26_extended_688_848", 0x26, 2, (688, 848), (558, 710), 0x00),
)


def controlled_section(rom: bytes) -> list[dict]:
    oracle = RenderOracle(rom)
    rows = []
    for name, t, frame, (ox, oy), (cx, cy), flags in FIXTURES:
        a0, a1 = ART_BASES[t]
        z = oracle.render(type_id=t, frame_index=frame, obj_x=ox, obj_y=oy, cam_x=cx, cam_y=cy,
                          flags=flags, art0=a0, art1=a1)
        m = assets.object_mapping(rom, t)
        frames = assets.mapping_frame_pointers(rom, m["mapping_cpu"])
        model = model_slot(rom, obj_x=ox, obj_y=oy, cam_x=cx, cam_y=cy, frame_cpu=frames[frame],
                           flags=flags, art0=a0, art1=a1)
        model_y = [p["sat_y"] for p in model]
        model_x = [p["sat_x"] for p in model]
        model_t = [p["tile"] for p in model]
        rec = assets.parse_frame_record(rom, frames[frame])
        # Final display convention (VDP, not ROM code): sprite line = SAT_Y + 1 + row;
        # background line L shows world row cam_y + 17 + L (R9 = cam_y + 17 mod 224).
        lines = [((p["y16"] + 1), (p["y16"] + 16)) for p in model if not p["hidden_by_y_clip"]]
        rows.append({
            "name": name, "type": f"0x{t:02X}", "frame_index": frame,
            "runtime_anchor": [ox, oy], "camera_D174_D176": [cx, cy], "flags_04": f"0x{flags:02X}",
            "frame_record_cpu": f"0x{frames[frame]:04X}", "y_origin": rec["y_origin"], "x_origin": rec["x_origin"],
            "piece_y_offsets": [p["y_offset"] for p in rec["pieces"]],
            "screen_anchor_after_3FC8": z["screen_xy_after_3FC8"],
            "sat_y_z80": z["sat_y"], "sat_x_z80": z["sat_x"], "sat_tile_z80": z["sat_tile"],
            "sat_y_model": model_y, "sat_x_model": model_x, "sat_tile_model": model_t,
            "z80_equals_model": (z["sat_y"], z["sat_x"], z["sat_tile"]) == (model_y, model_x, model_t),
            "sat_first_line_last_line_screen": [min(a for a, _b in lines), max(b for _a, b in lines)] if lines else None,
            "evidence": "CONTROLLED ROUTINE RESULT",
        })
    return rows


# --------------------------------------------------------------------------- #
# 7. Interpretation (kept separate from source facts)
# --------------------------------------------------------------------------- #
def rule_section() -> dict:
    return {
        "evidence": "BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT + EMULATED ORIGINAL FRAME",
        "shared_renderer": "one generic path for every slot object: $220E -> $3FC8 -> $226A -> $22B6",
        "other_sat_writers": "none: every reference to $D36F/$D371 in the whole ROM lies inside $220E..$2334",
        "equations": {
            "screen_y": "anchor_y - cam_y  (16-bit; $3FC8: IX+$14 - $D176 -> IX+$1C)",
            "sat_y_word": "screen_y + frame_y_origin + piece_y   ($226A)",
            "sat_y_visible_if": "-16 <= sat_y_word <= 191   ($229A..$22A6; else SAT Y byte = $E0)",
            "sat_x_word": "anchor_x - cam_x + x_origin' + piece_x'   ($22B6; flip negates x_origin and uses the +$0D08 mirrored table)",
            "sat_x_clip": "high byte != 0 -> SAT X byte = 0   ($2306..$230C); R0 bit 5 blanks columns 0..7",
            "vdp_sprite_top_line": "SAT_Y + 1",
            "vdp_r9_vscroll": "(cam_y + 17) mod 224   ($4D3E: ADD HL,$0011 ... mod $00E0 -> $D173 -> R9 at $053E)",
            "vdp_r8_hscroll": "(-(cam_x + 1)) & $FF   ($4D3E: ADD A,1; NEG -> $D172 -> R8)",
            "background_world_row_at_line_L": "cam_y + 17 + L",
            "background_world_col_at_screen_x": "cam_x + 1 + x",
        },
        "consequence": {
            "y": "a sprite pixel with mapping row m appears at terrain-space row anchor_y + y_origin + m + 1 + 17 = anchor_y + y_origin + m + 18",
            "x": "a sprite pixel with mapping column m appears at terrain-space column anchor_x + x_origin' + m + 1",
            "object_anchor_space": "object anchors are terrain-space minus (1, 18); the collision floor probe adds the same 18 at $7690",
        },
    }



# --------------------------------------------------------------------------- #
# 8. POC checkpoint values (GAMEMAKER ADAPTER ONLY - read-only inspection)
# --------------------------------------------------------------------------- #
POC_CHECKPOINT = {
    "repository": "SonicChaos_POC", "branch": "poc/thz1-cleanup",
    "commit": "6819722201b169c4dac136efdb4236c5cf470327",
    "note": "sprite geometry read from sprites/*/*.yy and PNG alpha; adapters from SCR_chaos_render_adapter.gml",
    # type -> sprite, origin, canvas rows/cols of opaque pixels (canvas coordinates), y adapter, note
    "sprites": {
        "0x09": {"sprite": "SPR_chaos_object_09 (frames 0-3 = mapping frames 1,2,4,3)", "origin": [8, 15], "canvas": [16, 16],
                 "opaque_canvas_rows": [0, 15], "opaque_canvas_cols_frame0": [1, 14], "y_adapter": 0,
                 "draw": "draw_sprite(spr, frame, x, y)"},
        "0x10": {"sprite": "SPR_chaos_object_10_04 / _06", "origin": [16, 28], "canvas": [32, 40],
                 "opaque_canvas_rows": [4, 27], "opaque_canvas_cols_frame0": [5, 26], "y_adapter": 18,
                 "draw": "draw_sprite_ext(spr, frame, x, y + 18, ...)"},
        "0x21": {"sprite": "SPR_chaos_object_21", "origin": [16, 36], "canvas": [32, 40],
                 "opaque_canvas_rows": [4, 35], "opaque_canvas_cols_frame0": [4, 24], "y_adapter": 18,
                 "draw": "draw_sprite_ext(spr, frame, x, y + 18, xscale -1)"},
        "0x27": {"sprite": "SPR_chaos_object_27", "origin": [16, 20], "canvas": [32, 24],
                 "opaque_canvas_rows": [5, 19], "opaque_canvas_cols_frame0": [4, 27], "y_adapter": 0,
                 "draw": "draw_self() (object has no Draw event)"},
        "0x28": {"sprite": "SPR_chaos_platform", "origin": [16, 0], "canvas": [32, 16],
                 "opaque_canvas_rows": [0, 15], "opaque_canvas_cols_frame0": [0, 31], "y_adapter": 0,
                 "draw": "instance draws its own sprite at y"},
        "0x18": {"sprite": "SPR_chaos_object_18", "origin": [16, 48], "canvas": [32, 48],
                 "opaque_canvas_rows": [0, 43], "opaque_canvas_cols_frame0": [0, 31], "y_adapter": 22,
                 "draw": "draw_sprite(spr, frame, x, y + 22)"},
        "0x1B": {"sprite": "SPR_chaos_object_1B (crop of canvas rows 4.., cols 4..27)", "origin": [16, 36], "canvas": [32, 40],
                 "opaque_canvas_rows": [12, 35], "opaque_canvas_cols_frame0": [5, 27], "y_adapter": 0,
                 "draw": "draw_sprite_part(spr, 0, 4, 4, 24, visible, x-12, baseY-visible), visible = min(32, 18 + raise)"},
        "0x26": {"sprite": "SPR_chaos_object_26 cap + drawn coil lines", "origin": [16, 24], "canvas": [32, 32],
                 "opaque_canvas_rows": [16, 31], "opaque_canvas_cols_frame0": [8, 23], "y_adapter": 0,
                 "draw": "cap sprite at (x, capY + 17), capY = (placement_y + 12) - raise; coil lines from capY + 7"},
    },
}


def poc_comparison(emulated: dict) -> list[dict]:
    """Original opaque rows (relative to runtime anchor) versus what the POC checkpoint draws."""
    def first(case, typ, frame=None, anchor_y=None):
        for ob in emulated[case]["observations"]:
            o = ob["object"]
            if o["type"] == typ and (frame is None or o["frame_index"] == frame) and \
               (anchor_y is None or o["runtime_anchor"][1] == anchor_y):
                return o
        raise KeyError((case, typ, frame))

    src = {
        "0x09": first("loop_type09", "0x09", 1), "0x10": first("type10_param04_336_270", "0x10", 11),
        "0x21": first("type21_param08_800_606", "0x21", 1), "0x27": first("type27_2240_112", "0x27", 1),
        "0x28": first("type28_592_464", "0x28", 1), "0x18": first("type18_3960_558", "0x18", 1),
    }
    rows = []
    for t, o in src.items():
        c = POC_CHECKPOINT["sprites"][t]
        poc_rows = [c["opaque_canvas_rows"][0] - c["origin"][1] + c["y_adapter"],
                    c["opaque_canvas_rows"][1] - c["origin"][1] + c["y_adapter"]]
        orow = o["opaque_world_rows_rel_anchor"]
        rows.append({
            "type": t, "evidence": "GAMEMAKER ADAPTER ONLY (POC) vs EMULATED ORIGINAL FRAME",
            "poc": {k: c[k] for k in ("sprite", "origin", "canvas", "y_adapter", "draw")},
            "poc_opaque_rows_rel_anchor": poc_rows, "original_opaque_rows_rel_anchor": orow,
            "predicted_poc_minus_original_top": poc_rows[0] - orow[0],
            "predicted_poc_minus_original_bottom": poc_rows[1] - orow[1],
        })
    # type $1B: visible tip height after terrain priority, by raise
    orig = {}
    for ob in emulated["type1B_1344_864"]["observations"]:
        o = ob["object"]
        if o["type"] == "0x1B":
            orig[864 - o["runtime_anchor"][1]] = o["visible_after_bg_priority_rows"]
    c = POC_CHECKPOINT["sprites"]["0x1B"]
    poc_tip = {}
    for raise_px in (0, 6, 12, 18):
        visible = min(32, 18 + raise_px)
        top = 4                                       # crop starts at canvas row 4
        last = top + visible - 1
        poc_tip[raise_px] = max(0, min(last, c["opaque_canvas_rows"][1]) - c["opaque_canvas_rows"][0] + 1)
    rows.append({"type": "0x1B", "evidence": "GAMEMAKER ADAPTER ONLY (POC) vs EMULATED ORIGINAL FRAME",
                 "poc": {k: c[k] for k in ("sprite", "origin", "canvas", "y_adapter", "draw")},
                 "original_visible_tip_rows_above_terrain_by_raise": {str(k): orig[k] for k in sorted(orig)},
                 "poc_visible_opaque_rows_above_floor_by_raise": {str(k): v for k, v in poc_tip.items()}})
    c = POC_CHECKPOINT["sprites"]["0x26"]
    o26 = first("type26_688_864", "0x26", 2, 848)
    cap_top_rel_anchor = 17 - c["origin"][1] + c["opaque_canvas_rows"][0]
    rows.append({"type": "0x26", "evidence": "GAMEMAKER ADAPTER ONLY (POC) vs EMULATED ORIGINAL FRAME",
                 "poc": {k: c[k] for k in ("sprite", "origin", "canvas", "y_adapter", "draw")},
                 "poc_cap_top_rel_anchor": cap_top_rel_anchor,
                 "original_opaque_rows_rel_anchor_frame2": o26["opaque_world_rows_rel_anchor"],
                 "predicted_poc_minus_original_top": cap_top_rel_anchor - o26["opaque_world_rows_rel_anchor"][0],
                 "note": "POC composes its own cap+coil; ROM frame 2 is one 32x24 mapped image"})
    return rows


def build(rom: bytes, static_only: bool = False) -> dict:
    data = {
        "format": 1,
        "rom_sha256": ROM_SHA256,
        "task": "mapped-object screen registration",
        "evidence_classes": ["DECODED DATA", "BYTE-VERIFIED ASSEMBLY", "SOURCE-TRACED BEHAVIOR",
                             "CONTROLLED ROUTINE RESULT", "EMULATED ORIGINAL FRAME",
                             "GAMEMAKER ADAPTER ONLY", "UNRESOLVED"],
        "source_facts": {
            "routine_byte_checks": routine_checks(rom),
            "mapping_tables": mapping_data(rom),
            "controlled_routine_fixtures": controlled_section(rom),
        },
        "interpretation": {"registration_rule": rule_section()},
    }
    if not static_only:
        emu = emulated_section(rom)
        data["source_facts"]["emulated_original_frames"] = emu
        data["interpretation"]["poc_comparison"] = {"poc_checkpoint": {k: v for k, v in POC_CHECKPOINT.items() if k != "sprites"},
                                                    "rows": poc_comparison(emu)}
    return data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--output")
    ap.add_argument("--check")
    ap.add_argument("--static-only", action="store_true")
    a = ap.parse_args()
    rom = romlib.load(a.rom)
    data = build(rom, a.static_only)
    text = json.dumps(data, indent=1, sort_keys=False) + "\n"
    if a.output:
        Path(a.output).write_text(text, encoding="utf-8")
        print(f"wrote {a.output}")
    if a.check:
        stored = json.loads(Path(a.check).read_text(encoding="utf-8"))
        want = data
        if a.static_only:
            stored = {**stored, "source_facts": {k: v for k, v in stored["source_facts"].items()
                                                   if k != "emulated_original_frames"},
                      "interpretation": {k: v for k, v in stored["interpretation"].items() if k != "poc_comparison"}}
        assert stored == want, "cache differs from regenerated data"
        print("mapped-object registration cache matches ROM")
    if not (a.output or a.check):
        print(text)


if __name__ == "__main__":
    main()

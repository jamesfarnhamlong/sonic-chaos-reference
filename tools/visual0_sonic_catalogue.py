#!/usr/bin/env python3
"""VISUAL-0: ROM-backed catalogue of every normal-Sonic animation frame, state script and POC art status.

Evidence chain (nothing here uses a screenshot or an inherited sprite name):

    state request -> player type table $65BA (type 1) -> state script (bank $0C)
      -> record (duration, frame, callback) / FF commands / FF 05 selector frame tables
      -> bank-$0F mapping table (pointer $3C002 -> CPU $80C8): 98 frames $00..$61
      -> interrupt-side tile table $104B + frame*4 (bank, source, 64-byte blocks) -> VRAM tile 0
      -> THZ1 sprite palette $06

``--poc PATH`` additionally reads the GameMaker project READ-ONLY and compares every ROM-backed player sprite
resource with the ROM render (RGBA equality, alpha-mask equality, origin). It never writes to the POC.

Usage:
    python tools/visual0_sonic_catalogue.py ROM [--output build/visual0-sonic] [--poc PATH] [--metadata JSON] [--check]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zlib
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import player_scripts as P  # noqa: E402
import rom as R  # noqa: E402
import thz1_object_assets as A  # noqa: E402

PLAYER_TILE_TABLE = 0x0104B
FRAME_COUNT = 98                       # pointer words at $3C0C8 until the first record ($818C)
STATE_COUNT = 55                       # type-1 state table ($8000 slot 2, bank $0C)
COMMAND_OPERANDS = {0: 0, 1: 2, 2: 4, 3: 1, 4: 6, 5: 4, 6: 1, 7: 2, 8: 4, 9: 2, 10: 3, 11: 2, 12: 2, 13: 5, 14: 1, 15: 2}
COMMAND_NAMES = {0: "restart", 1: "call", 2: "velocity", 3: "request_state", 4: "spawn_child", 5: "selector",
                 6: "sound", 7: "jump", 8: "conditional", 9: "set_byte", 10: "op_0A", 11: "clear_bits",
                 12: "set_bits", 13: "frame_by_facing", 14: "loop_count", 15: "loop_back"}

# Selector routines that write the frame (+$06) and the duration (+$07) at runtime (FF 05).
# Each entry: (frame table CPU, entries) or computed description. The tables are read from the ROM, not typed here.
SELECTOR_SPECS = {
    0x8EE1: dict(role="walk ($05)", kind="walk"),
    0x8F45: dict(role="run ($06)", kind="run"),
    0x8F76: dict(role="roll/jump family ($09,$0A,$10,$1B)", kind="table", table=0x8FB8, count=20),
    0x900B: dict(role="state $1D (height-keyed pair table, 16 pairs)", kind="pairs", table=0x906C, count=16),
    0x903D: dict(role="loop-route states $0C/$0D/$13 (route progress / 13 indexes the pair table; $8F76 when +$03 bit 1)",
                 kind="pairs", table=0x906C, count=51),
    0x9138: dict(role="state $17 (four-step cycle)", kind="table", table=0x9163, count=4),
}

# POC resources are compared by this naming rule (read-only parse of the project).
POC_PLAYER_SPRITE_RE = re.compile(r"^SPR_chaos_(?:aqz_)?(?:player_frame_|player_state_11|base_chaos_player_state_11|"
                                  r"continue_sonic_|opening_sonic_|eez_player_)")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hx(v: int, w: int = 2) -> str:
    return "0x%0*X" % (w, v)


def slot2(cpu: int) -> int:
    return P.file_offset(cpu)


# ----------------------------------------------------------------------------------------------------------------
# frames
# ----------------------------------------------------------------------------------------------------------------
def tile_source(rom: bytes, frame: int) -> dict:
    entry = PLAYER_TILE_TABLE + frame * 4
    bank, cpu, blocks = rom[entry], R.u16(rom, entry + 1), rom[entry + 3]
    out = OrderedDict(table_entry_rom=hx(entry, 5), raw_entry=" ".join("%02X" % b for b in rom[entry:entry + 4]))
    if frame == 0 or not 0x8000 <= cpu <= 0xBFFF or not blocks:
        out["usable"] = False
        return out
    source = bank * 0x4000 + cpu - 0x8000
    raw = rom[source:source + blocks * 64]
    out.update(usable=True, bank=hx(bank), source_cpu=hx(cpu, 4), source_rom=hx(source, 5), blocks_64_bytes=blocks,
               tile_count=len(raw) // 32, tile_bytes_sha256=sha(raw))
    out["_raw"] = raw
    return out


def render(rom: bytes, parsed: dict, raw: bytes, palette):
    vram = bytearray(0x4000)
    vram[:len(raw)] = raw
    return A.render_frame(vram, parsed, 0, scale=1, margin=0, palette=palette)


def build_frames(rom: bytes, palette, output: Path | None):
    mapping = A.object_mapping(rom, 1)
    base = mapping["mapping_cpu"]
    pointers = [R.u16(rom, A.cpu15_to_rom(base) + 2 * i) for i in range(FRAME_COUNT)]
    first_record = min(p for p in pointers if p >= base)
    assert first_record - base == FRAME_COUNT * 2, "frame count no longer matches the first mapping record"
    frames, images = OrderedDict(), {}
    for f in range(FRAME_COUNT):
        parsed = A.parse_frame_record(rom, pointers[f])
        src = tile_source(rom, f)
        rec = OrderedDict(frame=hx(f), mapping_pointer_rom=hx(mapping["mapping_rom"] + 2 * f, 5),
                          mapping_cpu=hx(pointers[f], 4), mapping_rom=hx(parsed["frame_rom"], 5),
                          piece_count=parsed["piece_count"], tile_offsets=[hx(t) for t in parsed["tile_offsets"]],
                          graphics=OrderedDict((k, v) for k, v in src.items() if not k.startswith("_")))
        if parsed["piece_count"] and src.get("usable"):
            w, h, rgba, meta = render(rom, parsed, src["_raw"], palette)
            b = meta["bounds"]
            rec["bounds_relative_to_anchor"] = OrderedDict(min_x=b["min_x"], min_y=b["min_y"], width=b["width"],
                                                           height=b["height"])
            rec["gamemaker_canvas"] = OrderedDict(width=w, height=h, origin_x=-b["min_x"], origin_y=-b["min_y"])
            rec["opaque_pixels"] = meta["nonzero_source_pixels"]
            rec["rgba_sha256_thz1_palette"] = sha(rgba)
            images[f] = (w, h, rgba, b)
            if output:
                A.write_rgba_png(output / ("frame-%02X.png" % f), w, h, rgba)
        else:
            rec["empty"] = True
        frames[f] = rec
    return frames, images, mapping


# ----------------------------------------------------------------------------------------------------------------
# state scripts
# ----------------------------------------------------------------------------------------------------------------
def selector_frames(rom: bytes, selector: int) -> dict:
    spec = SELECTOR_SPECS.get(selector)
    if spec is None:
        return OrderedDict(selector=hx(selector, 4), unresolved=True)
    out = OrderedDict(selector=hx(selector, 4), role=spec["role"])
    if spec["kind"] == "walk":
        out.update(frames=[1, 2, 3, 4, 5, 6], strip_frames=[0x3C, 0x3D, 0x3E, 0x3F], side_contact_frame=0x5E,
                   source="docs/player-animation-counter.md + data/u5a/player-static.json (BYTE-VERIFIED)")
    elif spec["kind"] == "run":
        out.update(frames=[7, 8, 9, 10], strip_frames=[0x3C, 0x3D, 0x3E, 0x3F],
                   source="data/u5a/player-static.json (BYTE-VERIFIED)")
    elif spec["kind"] == "table":
        t = slot2(spec["table"])
        out.update(frames=list(rom[t:t + spec["count"]]),
                   source="table CPU %s (type-1 table; BYTE-VERIFIED $8F76/$9138 disassembly)" % hx(spec["table"], 4))
    else:
        t = slot2(spec["table"])
        pairs = [(rom[t + 2 * i], rom[t + 2 * i + 1]) for i in range(spec["count"])]
        out.update(pairs=[[a, b] for a, b in pairs], frames=sorted({v for p in pairs for v in p}),
                   rule="frame := pair[index][0], or pair[index][1] when it equals the current frame",
                   source="table CPU %s (type-1 table; BYTE-VERIFIED $900B disassembly)" % hx(spec["table"], 4))
    return out


def decode_state(rom: bytes, commands, state: int, start: int):
    notes = []
    steps, _ = P.parse_script(rom, start, commands, notes)
    ops, frames = [], OrderedDict()
    for cpu in sorted(steps):
        kind, length, cmd = steps[cpu]
        off = slot2(cpu)
        if kind == "record":
            dur, frame, cb = rom[off], rom[off + 1], R.u16(rom, off + 2)
            ops.append(OrderedDict(at=hx(cpu, 4), op="record", duration=dur, frame=hx(frame), callback=hx(cb, 4)))
            frames.setdefault(frame, []).append("record %s" % hx(cpu, 4))
            continue
        arg = bytes(rom[off + 2:off + 2 + COMMAND_OPERANDS[cmd]])
        op = OrderedDict(at=hx(cpu, 4), op="FF %02X" % cmd, name=COMMAND_NAMES[cmd],
                         operands=" ".join("%02X" % b for b in arg))
        if cmd == 3:
            op["requests_state"] = hx(arg[0])
        elif cmd == 5:
            sel = R.u16(rom, off + 2)
            op["selector"] = selector_frames(rom, sel)
            for fr in op["selector"].get("frames", []) + op["selector"].get("strip_frames", []):
                frames.setdefault(fr, []).append("selector %s" % hx(sel, 4))
            if "side_contact_frame" in op["selector"]:
                frames.setdefault(op["selector"]["side_contact_frame"], []).append("selector %s side contact" % hx(sel, 4))
            op["callback"] = hx(R.u16(rom, off + 4), 4)
        elif cmd == 13:
            op["duration"], op["frame_right"], op["frame_mirrored"] = arg[0], hx(arg[1]), hx(arg[2])
            for fr in (arg[1], arg[2]):
                frames.setdefault(fr, []).append("FF 0D %s" % hx(cpu, 4))
            op["callback"] = hx(R.u16(rom, off + 5), 4)
        elif cmd == 6:
            op["sound_request"] = hx(arg[0])
        elif cmd == 1:
            op["call"] = hx(R.u16(rom, off + 2), 4)
        elif cmd == 7:
            op["target"] = hx(R.u16(rom, off + 2), 4)
        elif cmd == 2:
            op["x_velocity_8_8"], op["y_velocity_8_8"] = struct.unpack("<hh", arg)
        elif cmd == 4:
            op["child_type"] = hx(arg[0])
        ops.append(op)
    return ops, frames, notes


def scan_request_sites(rom: bytes) -> dict:
    """Byte-pattern census of immediate state requests (resident engine + the player part of bank $0C). Code/data not classified;
    the resident engine also requests states for other objects, so a hit is evidence of reach, not proof."""
    regions = [(0, 0x8000), (0x30000, 0x31200)]       # resident engine + bank $0C slot 2 up to the end of the player selectors ($9200)
    sites = {}

    def add(state, where):
        sites.setdefault(state, []).append(where)

    def cpu(o):
        return hx(o if o < 0x8000 else 0x8000 + o % 0x4000, 4) + (" [bank $0C/$0D]" if o >= 0x8000 else "")

    for lo, hi in regions:
        chunk = rom[lo:hi]
        for m in re.finditer(rb"\xdd\x36\x02(.)", chunk, re.S):
            add(m.group(1)[0], "LD (IX+2),n at " + cpu(lo + m.start()))
        for m in re.finditer(rb"\x3e(.)\xdd\x77\x02", chunk, re.S):
            add(m.group(1)[0], "LD A,n / LD (IX+2),A at " + cpu(lo + m.start()))
        for m in re.finditer(rb"\x3e(.)\x32\x02\xd5", chunk, re.S):
            add(m.group(1)[0], "LD A,n / LD ($D502),A at " + cpu(lo + m.start()))
    return sites


# ----------------------------------------------------------------------------------------------------------------
# POC (read-only)
# ----------------------------------------------------------------------------------------------------------------
def png_rgba(path: Path):
    """Decode a non-interlaced 8-bit RGBA PNG (the POC resources). Returns (w, h, bytes) or None."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos, idat, w = 8, b"", None
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
            if depth != 8 or ctype != 6 or inter:
                return None
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = w * 4
    out, prev = bytearray(), bytearray(stride)
    for y in range(h):
        ft = raw[y * (stride + 1)]
        row = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = row[i - 4] if i >= 4 else 0
            b = prev[i]
            c = prev[i - 4] if i >= 4 else 0
            if ft == 1:
                row[i] = (row[i] + a) & 255
            elif ft == 2:
                row[i] = (row[i] + b) & 255
            elif ft == 3:
                row[i] = (row[i] + ((a + b) >> 1)) & 255
            elif ft == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                row[i] = (row[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out += row
        prev = row
    return w, h, bytes(out)


def trim(w, h, rgba):
    xs = [x for y in range(h) for x in range(w) if rgba[(y * w + x) * 4 + 3]]
    ys = [y for y in range(h) for x in range(w) if rgba[(y * w + x) * 4 + 3]]
    if not xs:
        return None
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    rows = b"".join(rgba[((y * w + x0) * 4):((y * w + x1 + 1) * 4)] for y in range(y0, y1 + 1))
    return (x1 - x0 + 1, y1 - y0 + 1, rows, x0, y0)


def mask_of(rows: bytes) -> bytes:
    return bytes(1 if rows[i + 3] else 0 for i in range(0, len(rows), 4))


def poc_compare(poc: Path, frames, images) -> dict:
    sprites = poc / "sprites"
    result = OrderedDict()
    for d in sorted(sprites.iterdir()):
        if not POC_PLAYER_SPRITE_RE.match(d.name):
            continue
        yy = json.loads((d / (d.name + ".yy")).read_text(encoding="utf-8"))
        seq = yy["sequence"]
        pngs = sorted(p for p in d.glob("*.png"))
        info = OrderedDict(frames=len(pngs), width=yy["width"], height=yy["height"], xorigin=seq["xorigin"],
                           yorigin=seq["yorigin"])
        m = re.search(r"_([0-9A-F]{2})$", d.name)
        guess = int(m.group(1), 16) if m and not d.name.endswith("state_11") else None
        info["name_suffix_frame"] = hx(guess) if guess is not None else None
        matches = []
        for idx, png in enumerate(pngs):
            dec = png_rgba(png)
            if not dec:
                continue
            t = trim(*dec)
            if t is None:
                continue
            tw, th, trows, x0, y0 = t
            for f, (fw, fh, frgba, b) in images.items():
                ft = trim(fw, fh, frgba)
                if ft is None or (ft[0], ft[1]) != (tw, th):
                    continue
                same_mask = mask_of(ft[2]) == mask_of(trows)
                same_rgba = ft[2] == trows
                if same_mask:
                    matches.append(OrderedDict(image=idx, rom_frame=hx(f), rgba_equal=same_rgba, alpha_mask_equal=True,
                                               origin_equal=(-b["min_x"] - 0 == seq["xorigin"] - x0 + ft[3] and
                                                             -b["min_y"] == seq["yorigin"] - y0 + ft[4])))
        info["matches"] = matches
        result[d.name] = info
    return result


# state roles: only names already established in this repository's evidence are used; everything else stays numeric.
STATE_ROLES = {
    0x00: ("power-on / new-level idle", "data/u5a/player-static.json"),
    0x01: ("standing (setter $45B3)", "asm/recovered/standing_walk_setters.asm"),
    0x05: ("walk (selector $8EE1)", "docs/player-animation-counter.md"),
    0x06: ("run (selector $8F45)", "docs/player-animation-counter.md"),
    0x09: ("roll", "docs/spring-interaction-audit.md"),
    0x0A: ("normal jump", "asm/recovered/player_state_setters.asm"),
    0x0B: ("upright spring ascent", "docs/player-spring-airborne-state-closure.md"),
    0x0C: ("loop-route state", "docs/gpz-loop-route-audit.md"),
    0x0D: ("loop-route state (entered via $3EE1)", "docs/gpz-loop-route-audit.md"),
    0x0E: ("falling", "asm/recovered/player_state_setters.asm"),
    0x0F: ("spin-dash charge", "docs/player-attack-badnik-audit.md"),
    0x10: ("spin-dash roll", "docs/player-attack-badnik-audit.md"),
    0x11: ("numeric reward bit 3 effect (type $10 parameter $04)", "docs/player-state-11.md"),
    0x12: ("Spring Shoes", "docs/spring-shoes-presentation-audit.md"),
    0x13: ("loop-route state (entered via $3EF7)", "docs/gpz-loop-route-audit.md"),
    0x14: ("strip fall", "docs/player-fall-control-audit.md"),
    0x15: ("peel-out charge (setter $46CE)", "docs/player-attack-badnik-audit.md"),
    0x1A: ("peel-out run (setter $46E2)", "docs/player-attack-badnik-audit.md"),
    0x1B: ("ramp launch", "asm/recovered/ramp_state_setters.asm"),
    0x1C: ("diagonal spring", "docs/player-spring-airborne-state-closure.md"),
    0x1E: ("hurt (rings lost)", "docs/player-attack-badnik-audit.md"),
    0x1F: ("death", "docs/player-attack-badnik-audit.md"),
    0x20: ("act-clear", "docs/object-18-act-clear.md"),
    0x22: ("twist", "docs/spring-interaction-audit.md"),
}


def poc_presentation(poc: Path) -> dict:
    """Read-only parse of the accepted POC presentation source: which states use ROM frames, which sprite family the rest use."""
    base = poc / "scripts"
    src = (base / "SCR_chaos_player_animation" / "SCR_chaos_player_animation.gml").read_text(encoding="utf-8")
    data = (base / "SCR_chaos_player_animation_data" / "SCR_chaos_player_animation_data.gml").read_text(encoding="utf-8")
    legacy = (base / "SCR_player_sprites_sonic" / "SCR_player_sprites_sonic.gml").read_text(encoding="utf-8")
    fn = re.search(r"function chaos_player_animation_supported\(cp_state\) \{(.*?)\n\}", src, re.S).group(1)
    supported = sorted({int(x) for x in re.findall(r"cp_state == (\d+)", fn)})
    chooser = data.split("function chaos_player_frame_sprite")[1].split("function chaos_player_rom_resource")[0]
    cases = sorted({int(n) for n in re.findall(r"case (\d+):\s*return", chooser)})
    legacy_map = dict(re.findall(r"SPR_player_(\w+) = (SPR_sonic_\w+);", legacy.split("// Normal")[1].split("// All")[0]))
    return OrderedDict(
        source_sha256=OrderedDict([("SCR_chaos_player_animation.gml", sha(src.encode())),
                                   ("SCR_chaos_player_animation_data.gml", sha(data.encode())),
                                   ("SCR_player_sprites_sonic.gml", sha(legacy.encode()))]),
        states_presented_from_rom_frames=[hx(x) for x in supported],
        extra_presentation_paths="surface-$19 strip walk/run (U5-A) frames $3C..$3F; EEZ carrier states $16/$17 frames $5F/$60",
        rom_frames_with_a_poc_sprite_case=[hx(x) for x in cases],
        legacy_sprite_family_for_every_other_state=OrderedDict(sorted(legacy_map.items())))


def observe_play(rom: bytes, seeds=(5, 11, 23), frames=6000) -> dict:
    """EMULATED ORIGINAL FRAME: real THZ1 play with seeded pad input; at every player update the engine's frame is recorded."""
    import random
    import object_18 as O
    from sms_frame_harness import BTN_RIGHT, BTN_LEFT, BTN_DOWN, BTN_UP, BTN_1
    seen = {}
    for seed in seeds:
        s = O._boot(rom, 0, lambda m: None)
        m = s.mem

        def on_cb(_, m=m, s=s):
            if s.cpu.ix == 0xD500:
                key = (m[0xD501], m[0xD506])
                seen[key] = seen.get(key, 0) + 1

        s.add_pc_hook(0x5E91, on_cb)
        rng = random.Random(seed)
        pad = 0
        for f in range(frames):
            if f % 40 == 0:
                r = rng.random()
                pad = (BTN_RIGHT if r < .35 else BTN_RIGHT | BTN_DOWN if r < .45 else BTN_LEFT if r < .55 else BTN_DOWN if r < .65 else
                       BTN_UP if r < .72 else BTN_DOWN | BTN_RIGHT | BTN_1 if r < .85 else BTN_RIGHT | BTN_1)
            s.pad = pad | (BTN_1 if f % 55 < 6 and pad & BTN_RIGHT else 0)
            s.run_frame()
    by_state = {}
    for (st, fr), n in sorted(seen.items()):
        by_state.setdefault(hx(st), OrderedDict())[hx(fr)] = n
    return OrderedDict(method="THZ1 booted in tools/sms_frame_harness.py; seeds %s x %d frames; PC hook at the callback executor $5E91 "
                              "(after the animation engine $64FA) records player state D501 and frame D506" % (list(seeds), frames),
                       observed_state_frame_counts=by_state)


def write_contact_sheet(output: Path, images: dict) -> None:
    """Labelled sheet of every non-empty frame (ignored build output, for human review only)."""
    from PIL import Image, ImageDraw
    cols, cell = 14, (56, 64)
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell[0], rows * cell[1]), (70, 110, 170, 255))
    draw = ImageDraw.Draw(sheet)
    for k, f in enumerate(sorted(images)):
        w, h, rgba, _ = images[f]
        im = Image.frombytes("RGBA", (w, h), rgba)
        x, y = (k % cols) * cell[0], (k // cols) * cell[1]
        sheet.alpha_composite(im, (x + (cell[0] - w) // 2, y + 14))
        draw.text((x + 2, y + 1), "%02X" % f, fill=(255, 255, 255, 255))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(output / "contact-sheet.png")


def describe_ops(state: dict) -> str:
    """One-line reading of a decoded state script (records as frame x duration; commands by effect)."""
    parts = []
    for o in state["ops"]:
        if o["op"] == "record":
            parts.append("%s x%d" % (o["frame"][2:], o["duration"]))
            continue
        c = o["op"]
        if c == "FF 00":
            parts.append("restart")
        elif c == "FF 01":
            parts.append("call %s" % o["call"])
        elif c == "FF 02":
            parts.append("v(%d,%d)" % (o["x_velocity_8_8"], o["y_velocity_8_8"]))
        elif c == "FF 03":
            parts.append("request %s" % o["requests_state"])
        elif c == "FF 04":
            parts.append("child %s" % o.get("child_type", "?"))
        elif c == "FF 05":
            sel = o["selector"]
            if "frames" in sel:
                fr = ",".join("%02X" % f for f in sel["frames"])
                extra = ""
                if "strip_frames" in sel:
                    extra = " | strip " + ",".join("%02X" % f for f in sel["strip_frames"])
                if "side_contact_frame" in sel:
                    extra += " | side %02X" % sel["side_contact_frame"]
                parts.append("selector %s [%s%s]" % (sel["selector"], fr, extra))
            else:
                parts.append("selector %s" % sel["selector"])
        elif c == "FF 06":
            parts.append("sound %s" % o["sound_request"])
        elif c == "FF 07":
            parts.append("jump %s" % o["target"])
        elif c == "FF 08":
            parts.append("if-branch")
        elif c == "FF 0D":
            parts.append("facing-frame %s/%s x%d" % (o["frame_right"][2:], o["frame_mirrored"][2:], o["duration"]))
        elif c == "FF 0E":
            parts.append("loop %d" % int(o["operands"], 16))
        elif c == "FF 0F":
            parts.append("loop-back")
        else:
            parts.append(c)
    return "; ".join(parts)


def render_markdown(rep: dict) -> str:
    """Generated appendix: every frame, every state, POC status. Deterministic from the JSON cache."""
    poc = rep.get("poc_resources", {})
    pres = rep.get("poc_presentation", {})
    presented = {int(x, 16) for x in pres.get("states_presented_from_rom_frames", [])}
    by_frame = {}
    for name, info in poc.items():
        for m in info["matches"]:
            by_frame.setdefault(m["rom_frame"], []).append((name, m["rgba_equal"]))
    sprite_cases = set(pres.get("rom_frames_with_a_poc_sprite_case", []))
    observed = rep.get("emulated_play", {}).get("observed_state_frame_counts", {})
    out = ["# VISUAL-0 appendix: normal-Sonic frame and state catalogue (generated)", "",
           "Generated by `python tools/visual0_sonic_catalogue.py ROM --poc POC --emulate --doc docs/visual0-sonic-state-frame-catalogue.md`",
           "from `data/rom-cache/visual0/sonic-animation-catalogue.json`. Do not edit by hand. ROM SHA-256 `%s`." % rep["rom_sha256"], "",
           "Notation: frames are two hex digits; `FF` commands are decoded by effect; durations are engine updates (reload rules for selector",
           "records are in `docs/player-animation-counter.md`). 'THZ1-play' = observed in seeded emulated THZ1 play (`emulated_play`).", "",
           "## 1. Frames (mapping table CPU `$80C8`, bank `$0F`; tile table `$104B`)", "",
           "| Frame | Mapping ROM | Pieces | Tile source (bank:CPU -> ROM, tiles) | Canvas / GameMaker origin | THZ1 RGBA sha8 | Used by states | POC ROM-backed sprite(s) |",
           "|---|---|---:|---|---|---|---|---|"]
    for f in rep["frames"]:
        g = f["graphics"]
        src = ("%s:%s -> %s, %d tiles" % (g["bank"], g["source_cpu"], g["source_rom"], g["tile_count"])) if g.get("usable") else "none (empty frame)"
        if f.get("empty"):
            canvas = "-"
            sha8 = "-"
        else:
            c = f["gamemaker_canvas"]
            canvas = "%dx%d / (%d,%d)" % (c["width"], c["height"], c["origin_x"], c["origin_y"])
            sha8 = f["rgba_sha256_thz1_palette"][:8]
        users = ", ".join(u[2:] for u in f.get("used_by_states", [])) or "-"
        named = {}
        for n, eq in by_frame.get(f["frame"], []):
            named[n] = named.get(n, False) or eq
        res = "; ".join("%s%s" % (n.replace("SPR_chaos_", ""), "" if eq else " (other palette)") for n, eq in sorted(named.items())) or "**none**"
        out.append("| `%s` | `%s` | %d | %s | %s | `%s` | %s | %s |" % (f["frame"][2:], f["mapping_rom"], f["piece_count"], src, canvas, sha8, users, res))
    out += ["", "## 2. States (type-1 table at CPU `$8000`, bank `$0C`)", "",
            "| State | Role (established names only) | Script | Reading of the script | Frames | THZ1-play | POC presents with ROM frames | Frames without any POC ROM-backed sprite |",
            "|---|---|---|---|---|---|---|---|"]
    for st in rep["states"]:
        n = int(st["state"], 16)
        frames = [f for f in st["frames"]]
        missing = [f[2:] for f in frames if f not in by_frame]
        thz = "yes (%s)" % ", ".join(x[2:] for x in observed[st["state"]]) if st["state"] in observed else "not seen"
        pr = "yes" if n in presented else ("strip only" if n in (5, 6) else "no (legacy `SPR_sonic_*`)")
        out.append("| `%s` | %s | `%s` | %s | %s | %s | %s | %s |" % (
            st["state"][2:], st["role"], st["script_cpu"], describe_ops(st).replace("|", "/"),
            " ".join(x[2:] for x in frames), thz, pr, " ".join(missing) or "-"))
    out += ["", "## 3. Immediate state-request sites (byte-pattern census: resident engine + bank `$0C` CPU `$8000-$91FF`)", "",
            "Code versus data is not classified; a state with no immediate site is entered by a computed request, a script `FF 03`, or not at all.", ""]
    script_requests = {}
    for st in rep["states"]:
        for o in st["ops"]:
            if o["op"] == "FF 03":
                script_requests.setdefault(o["requests_state"], []).append(st["state"][2:])
    for st in rep["states"]:
        sites = st["immediate_request_sites"]
        text = ("; ".join(sites[:6]) + (" (+%d more)" % (len(sites) - 6) if len(sites) > 6 else "")) if sites else "no immediate site"
        by_script = script_requests.get(st["state"])
        if by_script:
            text += "; script `FF 03` from state(s) " + ", ".join(sorted(set(by_script)))
        out.append("* `%s`: %s" % (st["state"][2:], text))
    return "\n".join(out) + "\n"


# ----------------------------------------------------------------------------------------------------------------
def build(rom: bytes, output: Path | None = None, poc: Path | None = None, emulate: bool = False) -> dict:
    if sha(rom) != R.SHA256:
        raise ValueError("ROM SHA-256 mismatch")
    palette = A.thz1_sprite_palette(rom)
    if output:
        output.mkdir(parents=True, exist_ok=True)
    frames, images, mapping = build_frames(rom, palette, output)
    commands = P.derive_commands(rom)
    tables = P.state_tables(rom)
    base, scripts = tables[1]
    assert len(scripts) == STATE_COUNT
    requests = scan_request_sites(rom)
    states, frame_users = OrderedDict(), {}
    for state, start in enumerate(scripts):
        ops, fr, notes = decode_state(rom, commands, state, start)
        assert not notes, notes
        states[state] = OrderedDict(state=hx(state), script_cpu=hx(start, 4), script_rom=hx(slot2(start), 5), ops=ops,
                                    frames=[hx(f) for f in sorted(fr)],
                                    immediate_request_sites=requests.get(state, []))
        for f in fr:
            frame_users.setdefault(f, []).append(hx(state))
    for f, users in frame_users.items():
        if f < FRAME_COUNT:
            frames[f]["used_by_states"] = users
    if output:
        write_contact_sheet(output, images)
    report = OrderedDict(
        format=1, rom_sha256=sha(rom), player_type="0x01 (normal Sonic)",
        evidence="DECODED DATA + BYTE-VERIFIED ASSEMBLY + deterministic reconstruction; POC section is POC SOURCE (READ-ONLY)",
        engine=OrderedDict(
            mapping_table_cpu=hx(mapping["mapping_cpu"], 4), mapping_table_rom=hx(mapping["mapping_rom"], 5),
            frame_count=FRAME_COUNT, tile_table_rom=hx(PLAYER_TILE_TABLE, 5), tile_destination="VRAM tile 0 (0x0000)",
            palette="THZ1 sprite palette selector 0x06 (ROM 0x3B6AD); index 0 transparent",
            facing="object +$04 bit 4 mirrors piece X and bit-reverses tile bytes (table $0100); GameMaker xscale -1 is equivalent",
            direct_frame_writes=[
                OrderedDict(site="0x03661", note="callback $3657 (via stub $038F, FF 01 in state 0) writes frame $10 and "
                                                 "advances the request; state 0's following record loads frame $0B in the "
                                                 "same engine pass, so frame $10 is never composed for the player"),
                OrderedDict(site="0x68B5", note="FF 0D (facing-dependent frame)"),
                OrderedDict(site="0x654E", note="engine record read"),
                OrderedDict(site="selector bodies", note="$30CD4..$30F92 / $31035 / $31064 / $3115B (see selectors)")]),
        frames=list(frames.values()), states=list(states.values()),
    )
    for st in report["states"]:
        role = STATE_ROLES.get(int(st["state"], 16))
        st["role"] = role[0] if role else "unnamed (numeric only)"
        st["role_source"] = role[1] if role else None
    if poc:
        report["poc_resources"] = poc_compare(poc, frames, images)
        report["poc_presentation"] = poc_presentation(poc)
    if emulate:
        report["emulated_play"] = observe_play(rom)
        bad = []
        for st_hex, frs in report["emulated_play"]["observed_state_frame_counts"].items():
            idx = int(st_hex, 16)
            allowed = set(report["states"][idx]["frames"]) if idx < len(report["states"]) else set()
            bad += [[st_hex, fr] for fr in frs if fr not in allowed]
        report["emulated_play"]["frames_outside_static_catalogue"] = bad
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--poc", type=Path)
    p.add_argument("--metadata", type=Path)
    p.add_argument("--emulate", action="store_true", help="also observe frames in emulated THZ1 play (about a minute)")
    p.add_argument("--doc", type=Path, help="write the generated Markdown appendix")
    p.add_argument("--check", action="store_true", help="compare --metadata with a fresh run instead of writing")
    a = p.parse_args()
    rep = build(R.load(a.rom), a.output, a.poc, a.emulate)
    text = json.dumps(rep, indent=1) + "\n"
    if a.metadata:
        if a.check:
            if a.metadata.read_text(encoding="utf-8") != text:
                sys.exit("metadata differs: " + str(a.metadata))
            print("metadata identical")
        else:
            a.metadata.parent.mkdir(parents=True, exist_ok=True)
            a.metadata.write_text(text, encoding="utf-8")
    if a.doc:
        a.doc.parent.mkdir(parents=True, exist_ok=True)
        a.doc.write_text(render_markdown(rep), encoding="utf-8")
    print(json.dumps({"frames": len(rep["frames"]), "states": len(rep["states"])}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""U5-A part D: the original start-up sequence and the opening cinematic (Sonic Chaos SMS, Europe v1.2).

    python tools/u5a_opening.py ROM                      # regenerate data/u5a/opening-*.json and startup-census.json (+ ignored exports in build/u5a/opening)
    python tools/u5a_opening.py ROM --check              # recompute everything and compare with the committed JSON
    python tools/u5a_opening.py ROM --only static        # decoded layer only (seconds, no emulation)
    python tools/u5a_opening.py --validate               # no ROM: internal consistency of the committed JSON, the actor model re-run on the replay

What the ROM does after power-on (D292 is the menu/flow flag byte; the dispatcher at $2B50 reads its bits from the top):

    boot -> D292 bit 6 -> bit 5: OPENING CINEMATIC ($06C7, a scripted run of the ordinary level engine in zone 7 / act 0)
         -> bit 4: TITLE SCREEN ($0719, logo + PRESS START BUTTON)  -> bit 3: ATTRACT DEMO ($2BC3, three rotating recorded runs) -> bit 5 again ...

Layers (every field belongs to exactly one):

* ``static``   - DECODED DATA / BYTE-VERIFIED ASSEMBLY: dispatcher bits and handlers, the opening routine's immediates, the zone-7 level (header, layout, art
                 streams, palettes, placement), the actor scripts (player state $29, type $1F states 0..7), mapping frames and the object visibility table.
* ``observed`` - EMULATED ORIGINAL FRAME (tools/sms_frame_harness.SMS, unmodified ROM from power-on, no input unless stated): one row per player update plus
                 per-frame scroll registers, palette steps, sound requests and tile transfers.  Timings are in updates; the harness is NTSC-timed and not cycle exact.
* ``model``    - a Python re-implementation of the actor scripts, the camera follow and the fade passes, compared with the observed rows (0 mismatches required).
* ``compose``  - background and sprite pixels re-composed from the static layer and compared with the emulator's rendered layers on sampled frames.

No ROM byte, tile pixel or palette is committed except small decoded numeric tables of the kind earlier Research caches commit; pixels, composed frames and
sheets are exported to the ignored build/u5a/opening.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import level_package as L  # noqa: E402
import player_animation_counter as PAC  # noqa: E402
import thz1_object_assets as A  # noqa: E402
import u4_results as U  # noqa: E402

ROM_SHA256 = U.ROM_SHA256
BASE_COMMIT = "c30c06e6c428b64e843ea5834ff52b7bc3304708"
DATA = ROOT / "data" / "u5a"
BUILD = ROOT / "build" / "u5a" / "opening"
STATIC_JSON = DATA / "opening-static.json"
OBS_JSON = DATA / "opening-observed.json"
REPLAY_JSON = DATA / "opening-replay.json"
CENSUS_JSON = DATA / "startup-census.json"
EXPORT_JSON = DATA / "opening-export-manifest.json"

hx, sha, off, u16, load_rom, dumps, load_json = U.hx, U.sha, U.off, U.u16, U.load_rom, U.dumps, U.load_json
H = lambda v, n=4: "0x" + format(v, "0%dX" % n)

OPENING_UPDATES = 738                   # $07B8 loop 30 + $079F loop 708
FADE_IN_UPDATES = 30
RUN_UPDATES = 708
TAIL_WAIT_FRAMES = 30
MACHINE_TYPE = 0x1F
BANK_C = 12                              # player + type $1F scripts, selectors


def check_rom(rom):
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM (SHA-256 %s)" % ROM_SHA256)


def region(rom, bank, a, b):
    o, e = off(bank, a), off(bank, b)
    return {"cpu": H(a), "end_cpu_exclusive": H(b), "rom": H(o, 5), "length": e - o, "sha256": sha(rom[o:e])}


# ------------------------------------------------------------------------------------------------------------------------------------------
# static layer
# ------------------------------------------------------------------------------------------------------------------------------------------
FLAG_OPS = {}
for _b in range(8):
    FLAG_OPS[0x86 + 8 * _b] = ("RES", _b)
    FLAG_OPS[0xC6 + 8 * _b] = ("SET", _b)


def d292_effects(rom, a, b):
    """Every `LD HL,$D292` followed by consecutive `SET/RES n,(HL)` ops inside [a,b): the flow-flag edits a handler makes, in code order."""
    out, o = [], off(0, a)
    end = off(0, b)
    while o < end - 5:
        if rom[o:o + 3] == bytes.fromhex("2192D2"):
            o += 3
            while rom[o] == 0xCB and rom[o + 1] in FLAG_OPS:
                op, bit = FLAG_OPS[rom[o + 1]]
                out.append("%s %d" % (op, bit))
                o += 2
        else:
            o += 1
    return out


def dispatcher(rom):
    """$2B50: LD A,($D292) ; RLCA ; JP c / JR c ... - the bit -> handler table is parsed from the code bytes."""
    o = off(0, 0x2B50)
    code = bytes(rom[o:o + 0x1D])
    assert code[:3] == bytes.fromhex("3A92D2"), "dispatcher prologue"
    table = []
    pc, bit = 0x2B53, 7
    i = 3
    while i < len(code) - 2:
        if code[i] != 0x07:
            break
        if code[i + 1] == 0xDA:                                   # JP c,nn
            table.append((bit, u16(code, i + 2)))
            i += 4
        elif code[i + 1] == 0x38:                                 # JR c,d
            table.append((bit, 0x2B50 + i + 3 + (code[i + 2] if code[i + 2] < 128 else code[i + 2] - 256)))
            i += 3
        else:
            break
        bit -= 1
    return {"evidence": "BYTE-VERIFIED ASSEMBLY (code bytes parsed)", "region": region(rom, 0, 0x2B50, 0x2B6D), "flag_ram": "0xD292",
            "bit_to_handler": {str(b): H(t) for b, t in table},
            "default": "no bit set: JP $2B50 (spins)"}


HANDLERS = [
    # name, D292 bit that selects it, start, end (exclusive), role
    ("start_new_game", 7, 0x2C17, 0x2C34, "button 1/2 requested: $0AD0 $07CE (zone/act := THC start), 42 waits, D292 := 0, returns to $04C1 (character select / New Game)"),
    ("power_on_to_opening", 6, 0x2B6D, 0x2B77, "boot flag: RES 6, SET 5 (set at $04B4 by SET 6,(HL))"),
    ("opening", 5, 0x2B77, 0x2B9F, "OPENING CINEMATIC: $0CF5 (hidden-menu code pointers) -> $06C7 (the scene) -> $1CAF + 30 waits -> RES 7/5, SET 4"),
    ("title", 4, 0x2B9F, 0x2BC3, "TITLE: $4FCE, $297E, $0719 (title screen + 1,140-update PRESS START wait), 30 waits, RES 4, SET 3"),
    ("attract_demo", 3, 0x2BC3, 0x2C0D, "ATTRACT: $2C34 picks demo D2E3 (0,1,2 rotation), D2E5 = recorded input pointer, 1,080-update run ($0438), then RES 3 / SET 5 (or SET 4 when START was pressed)"),
    ("bit2_return", 2, 0x2C0D, 0x2C17, "RES 2, SET 5 (return to the opening; no writer of bit 2 found in the dispatcher)"),
]


def opening_routine(rom):
    """$06C7: the opening scene.  Every immediate is matched against the code bytes."""
    o = off(0, 0x06C7)
    expect = bytes.fromhex(
        "F3CDC8213E073297D2AF3298D2CD7E29CDE178DD215ED1CDCE4FCDDC4FCDAD4DCD4F2A3E013200D5CD9B18CD4F79CDB3593E403293D2"
        "011E00CDB807" "01C402CD9F07" "AF3293D2CDAF1C061EFBCD2D0610FAC9")
    got = bytes(rom[o:o + len(expect)])
    assert got == expect, "opening routine bytes differ at +%d" % next(i for i in range(len(expect)) if got[i] != expect[i])
    return {
        "evidence": "BYTE-VERIFIED ASSEMBLY (complete routine matched byte for byte)", "region": region(rom, 0, 0x06C7, 0x0719),
        "sequence": [
            {"call": "$21C8", "role": "clear/blank the display before loading (shared helper)"},
            {"write": "D297 (zone) := 7"}, {"write": "D298 (act) := 0"},
            {"call": "$297E", "role": "clear RAM $D300..$DBBF and the camera/scroll slots"},
            {"call": "$78E1", "role": "level art loader: tile streams of zone 7 act 0 (art table $7CED index 21)"},
            {"ix": "$D15E", "call": "$4FCE", "role": "clear the camera/level structure"},
            {"call": "$4FDC", "role": "act header loader: header table $5082 (zone 7, act 0)"},
            {"call": "$4DAD", "role": "layout (run-length stream) + start record $4E98 + initial name-table fill (29 column batches of 8 rows)"},
            {"call": "$2A4F", "role": "per-zone setup table $2A9A"},
            {"write": "D500 (player object type) := 1  (Sonic; Tails is substituted by the state-$29 script)"},
            {"call": "$189B", "role": "music/sound request by zone/act table $18BA: sends $90 (see audio ledger)"},
            {"call": "$794F", "role": "palette fade-in request: records bg 40 / sprite 41 from table $7F3C"},
            {"call": "$59B3", "role": "camera initialisation"},
            {"write": "D293 := $40  (level/cutscene engine flag)"},
            {"loop": "$07B8", "BC": 0x1E, "per_iteration": "$062D wait for the interrupt tick, $16B8 gameplay update, title-overlay test D292 bit 4", "updates": 30},
            {"loop": "$079F", "BC": 0x2C4, "per_iteration": "$062D wait, $0796 START test (D292 bit 7 aborts the whole routine), $16B8 gameplay update", "updates": 708},
            {"write": "D293 := 0"}, {"call": "$1CAF", "role": "fade both palette slots to black"}, {"waits": 30, "routine": "$062D"},
        ],
        "updates_total": OPENING_UPDATES, "tail_wait_frames": TAIL_WAIT_FRAMES,
        "start_press": "$0796 returns to the caller of $06C7 when D292 bit 7 is set ($063C sets it from button 1/2 = D157 & $30); the handler then clears bit 7 and bit 5 and sets bit 4: START skips to the TITLE, it does NOT start a game",
    }


def title_routine(rom):
    o = off(0, 0x0719)
    code = bytes(rom[o:o + 0x5B])
    assert code[:4] == bytes.fromhex("F3CD7E29") and bytes.fromhex("017404CD9F07") in code, "title routine"
    return {"evidence": "BYTE-VERIFIED ASSEMBLY (landmarks)", "region": region(rom, 0, 0x0719, 0x0774),
            "waits": [{"B": 0x18, "label": "24 waits after fade slots D492/D494 requests"}, {"sound": "$BE -> $DE04", "B": 12}, {"sound": "$99 -> $DE04", "label": "title music"},
                      {"BC": 0x1E, "loop": "$07B8"}, {"BC": 0x474, "loop": "$079F", "updates": 1140}], "overlay": "$0774 draws the PRESS START BUTTON text (D12F & $20 blink)"}


def attract_table(rom):
    rows = []
    for name, base in (("D12D_zero", 0x2C72), ("D12D_nonzero", 0x2C7E)):
        for i in range(3):
            o = off(0, base + 4 * i)
            b = rom[o:o + 4]
            rows.append({"table": name, "row": i, "zone": b[0] & 0x0F, "character": 2 if b[0] & 0x80 else 1, "frames_byte_D2E4": b[1], "input_pointer_D2E5": H(u16(rom, o + 2))})
    return {"evidence": "DECODED DATA ($2C34: D2E3 := (D2E3+1) mod 3; table chosen by D12D; byte 0 & $0F zone, bit 7 -> character 2; byte 1 -> D2E4; word -> D2E5)",
            "rows": rows, "demo_order_after_boot": "D2E3 starts 0 so the first attract demo is row 1",
            "demo_length_updates": 0x438}


def level7(rom):
    h = L.act_header(rom, 7, 0)
    cells, end, term = L.decode_layout_stream(rom, h["layout_rom"])
    assert term and len(cells) == 2048 and h["width_cells"] == 256
    art = L.art_entry(rom, 7, 0)
    vram, loads = L.build_vram(rom, art)
    sel = L.palette_selection(rom, 7, 0)
    bgp = bytes(rom[sel["background_rom"]:sel["background_rom"] + 16])
    spp = bytes(rom[sel["sprite_rom"]:sel["sprite_rom"] + 16])
    from collections import Counter
    objs = L.decode_object_list(rom, L.object_list_pointer(rom, 7, 0)["list_rom"])[0]
    return {
        "evidence": "DECODED DATA (act header table $5082, zone 7 act 0; layout run-length stream; art table $7CED; palette selector $7F3C; placement list bank $1C)",
        "header": {"rom": H(h["header_rom"], 5), "raw": h["raw"], "block_mapping_rom": H(h["block_mapping_rom"], 5), "layout_rom": H(h["layout_rom"], 5),
                   "width_cells": h["width_cells"], "d280_left_limit": h["ram_d280"], "d27c_top_limit": h["ram_d27c"], "d282_right_limit": h["ram_d282"],
                   "d27e_bottom_limit": h["ram_d27e"], "row_offset_table_cpu": H(h["row_offset_table_cpu"])},
        "layout": {"cells": len(cells), "width_cells": 256, "height_cells": 8, "block_pixels": 32, "world_px": [8192, 256], "sha256": sha(bytes(cells)),
                   "stream_end_rom": H(end, 5), "block_ids_used": sorted(set(cells)), "block_histogram": {H(k, 2): v for k, v in sorted(Counter(cells).items())}},
        "start_record": L.player_start(rom, 7, 0),
        "art_streams": loads, "vram_sha256_after_load": sha(vram),
        "palette": {"selector_rom": H(sel["selector_rom"], 5), "background_record": sel["background_index"], "sprite_record": sel["sprite_index"],
                    "background_colours": bgp.hex().upper(), "sprite_colours": spp.hex().upper(), "format": "SMS %--BBGGRR per byte, 16 entries"},
        "placement": [{k: v for k, v in o.items() if k in ("index", "type_id", "world_x", "world_y", "stored_x", "stored_y", "flags", "parameter", "aux0", "aux1", "raw_bytes")} for o in objs],
    }


def handlers(rom):
    out = {}
    for name, bit, a, b, role in HANDLERS:
        out[name] = {"selected_by_d292_bit": bit, "region": region(rom, 0, a, b), "role": role, "d292_edits_in_code_order": d292_effects(rom, a, b)}
    return out


# --- actors ------------------------------------------------------------------------------------------------------------------------------
def script_ops(rom, table_cpu, state, bank=BANK_C):
    """Linear listing of a state script: records (duration, frame, callback) and FF commands, following FF 07 jumps and stopping at FF 00 or a revisit."""
    ptr = u16(rom, off(bank, table_cpu + 2 * state))
    seen, ops = set(), []
    start = ptr
    while ptr not in seen and len(ops) < 80:
        seen.add(ptr)
        o = off(bank, ptr)
        if rom[o] != 0xFF:
            ops.append({"at": H(ptr), "duration": rom[o], "frame": rom[o + 1], "callback": H(u16(rom, o + 2))})
            ptr += 4
            continue
        c = rom[o + 1]
        n = 2 + PAC.CMD_ARGS[c]
        row = {"at": H(ptr), "command": "FF %02X" % c, "args": rom[o + 2:o + n].hex().upper()}
        if c == 0x05:
            row["selector"] = H(u16(rom, o + 2))
            row["callback"] = H(u16(rom, o + 4))
        if c in (0x01,):
            row["routine"] = H(u16(rom, o + 2))
        if c in (0x07, 0x0F):
            row["target"] = H(u16(rom, o + 2))
        ops.append(row)
        if c == 0x00:
            break
        if c == 0x07:
            ptr = u16(rom, o + 2)
            continue
        ptr += n
    return {"script_cpu": H(start), "ops": ops}


def mapping_frames(rom, type_id, tile_base=None, vram=None, palette=None, export=None, label=""):
    """Decode every mapping frame of an object type (bank $0F table $8000 + type*2) and optionally render it from `vram`."""
    mp = A.object_mapping(rom, type_id)
    ptrs = A.mapping_frame_pointers(rom, mp["mapping_cpu"], 64)
    frames = {}
    for i, cpu in enumerate(ptrs):
        fr = A.parse_frame_record(rom, cpu)
        row = {"mapping_frame_cpu": H(cpu), "mapping_frame_rom": H(fr["frame_rom"], 5), "piece_count": fr["piece_count"],
               "y_origin": fr["y_origin"], "x_origin": fr["x_origin"], "pieces": [{"x": p["relative_x"], "y": p["relative_y"], "tile_offset": p["tile_offset"]} for p in fr["pieces"]]}
        if fr["pieces"] and vram is not None:
            res = A.render_frame(vram, fr, tile_base, scale=1, margin=0, palette=palette)
            w, h, rgba, meta = res
            row["bounds"] = meta["bounds"]
            row["rgba_sha256"] = sha(rgba)
            row["non_transparent_pixels"] = meta["nonzero_source_pixels"]
            if export is not None:
                export.mkdir(parents=True, exist_ok=True)
                A.write_rgba_png(export / ("%s-%02X.png" % (label, i)), w, h, rgba)
        frames["%d" % i] = row
    return {"mapping_table_cpu": H(mp["mapping_cpu"]), "mapping_rom": H(mp["mapping_rom"], 5), "frame_count": len(ptrs), "frames": frames}


def dynamic_mapping_frames(rom, ptype, ids, palette):
    """Mapping frames of a player-type object whose tiles are transferred per frame by the interrupt-side loader ($0D15, tables $104B / $11CF)."""
    mp = A.object_mapping(rom, ptype)
    ptrs = A.mapping_frame_pointers(rom, mp["mapping_cpu"], 128)
    ident = [(0, 0, 0, 0)] + [(i * 16, i, 0, 255) for i in range(1, 16)]
    out = {}
    for fid in ids:
        fr = A.parse_frame_record(rom, ptrs[fid])
        e = PLAYER_TILE_TABLES[ptype] + fid * 4
        raw = player_tiles(rom, ptype, fid)
        vram = bytearray(0x4000)
        vram[:len(raw)] = raw
        w, h, rgba, meta = A.render_frame(vram, fr, 0, scale=1, margin=0, palette=palette)
        _, _, idx_rgba, _ = A.render_frame(vram, fr, 0, scale=1, margin=0, palette=ident)
        index = bytes(idx_rgba[i] // 16 if idx_rgba[i + 3] else 0 for i in range(0, len(idx_rgba), 4))
        b = meta["bounds"]
        out["%d" % fid] = {"mapping_frame_cpu": H(ptrs[fid]), "mapping_frame_rom": H(fr["frame_rom"], 5), "piece_count": fr["piece_count"],
                           "tile_table_entry_rom": H(e, 5), "tile_source": {"bank": rom[e], "cpu": H(u16(rom, e + 1)), "blocks_64_bytes": rom[e + 3], "tiles": len(raw) // 32, "sha256": sha(raw)},
                           "bounds": b, "gamemaker_origin": [-b["min_x"], -b["min_y"]], "canvas": [w, h], "rgba_sha256_opening_sprite_palette": sha(rgba), "index_sha256": sha(index),
                           "non_transparent_pixels": meta["nonzero_source_pixels"]}
    return {"mapping_table_cpu": H(mp["mapping_cpu"]), "mapping_rom": H(mp["mapping_rom"], 5), "frames": out}


def window_table(rom):
    o = off(0x1C, 0x8146)
    t = bytes(rom[o:o + 1024])
    from collections import Counter
    cells = {v: [] for v in range(4)}
    for i, v in enumerate(t):
        cells[v].append((i % 32, i // 32))
    box = {str(v): [min(c[0] for c in cs), min(c[1] for c in cs), max(c[0] for c in cs), max(c[1] for c in cs)] for v, cs in cells.items() if cs}
    return {"evidence": "DECODED DATA (bank $1C $8146, 32x32 bytes read by the generic lifetime routine $61E1)",
            "rom": H(o, 5), "sha256": sha(t), "counts": {str(k): v for k, v in sorted(Counter(t).items())}, "bounding_cell_box_by_value": box,
            "reading": "cell = ((x+$80-camX)/2)>>3 , ((y+$80-camY)/2)>>3 in 16-px units (32x32 cells cover camera-128..camera+384); "
                       "value 0 = inside, 1 = border (still on screen), bit 1 set = SET 6,(IX+4) (off-screen flag), 3 = outside the window (deleted unless +$04 bit 1)",
            "rule_for_right_edge": "flag set when floor((x+128-camX)/16) >= 26, i.e. x - camX >= 288 (EDGE(RIGHT,+32)), for rows inside the box"}


def routine_regions(rom):
    regs = [
        (BANK_C, 0x84BD, 0x84C2, "script call: clears camera control $D15E (camera stops following)"),
        (BANK_C, 0x84C2, 0x84D6, "script call: X := camera X - 32, object type := 2 (Tails)"),
        (BANK_C, 0xAED1, 0xAEDF, "type $1F state 0 call: +$3F nonzero -> state 6 (not used here)"),
        (BANK_C, 0xAF33, 0xAF45, "type $1F selector: frame := frame+1 (13 -> 1), duration 4"),
        (BANK_C, 0xAF45, 0xAF4E, "type $1F state 0 callback: request state 1, SET 1,(IX+4)"),
        (BANK_C, 0xAF4E, 0xAF6A, "type $1F state 1 callback: |objX - playerX| < $40 -> state 2, vx +6.0, vy +2.9375"),
        (BANK_C, 0xAF6A, 0xAF8C, "type $1F state 2 callback: move, vy -= 16; vy == 0 -> +$1F := 20, +$0A := 0, state 3"),
        (BANK_C, 0xAF8C, 0xAF94, "type $1F state 3 callback A: move, vy += 8 (shared tail $AF9A)"),
        (BANK_C, 0xAF94, 0xAF9A, "type $1F state 3 callback B: move, vy -= 8 (shared tail $AF9A)"),
        (BANK_C, 0xAF9A, 0xAFE3, "type $1F state 3 shared tail: +$1F countdown 40 / phase +$0A, vx +/-4 by phase parity, D174 >= $0B40 -> state 4, vy := $0240"),
        (BANK_C, 0xAFE3, 0xB00E, "type $1F state 4 callback: vy -= 24, vx += 24; off-screen flag (+$04 bit 6) -> state 5 else move"),
        (BANK_C, 0xB00E, 0xB00F, "type $1F state 5 callback: RET"),
        (1, 0x60FB, 0x613C, "generic object move: X += vx, Y += vy (24-bit positions, 8.8 speeds)"),
        (1, 0x61A5, 0x61D6, "generic horizontal/vertical distance test: carry-style 'distance < BC' -> A := $FF"),
        (1, 0x61E1, 0x6276, "generic lifetime/visibility routine (window table $8146 -> off-screen flag +$04 bit 6 / deletion)"),
        (0, 0x3655, 0x3686, "player initial state: zone 7 requests state $29 ($3681)"),
    ]
    return [dict(region(rom, b, a, e), name=nm, bank=b if a >= 0x8000 else None) for b, a, e, nm in regs]


def actors(rom, vram):
    pal = A.palette_rgba(rom, 41)
    sonic = script_ops(rom, 0x8000, 0x29)
    tails = script_ops(rom, 0x89BB, 0x29)
    d = {
        "evidence": "DECODED DATA (state script tables: player type 1 at $8000, type 2 at $89BB, type $1F at $AEB3; bank $0C) + BYTE-VERIFIED ASSEMBLY (callbacks)",
        "player_state_29": {
            "reading": "FF 02 sets X speed $0600 and Y speed 0; FF 0E 150 x (run selector $8F45, callback $0338 = generic move) = 600 updates; FF 01 $84BD clears D15E; "
                       "FF 0E 15 x run selector = 60 updates; FF 01 $84C2 sets X := D174-32 and object type := 2; FF 0E 45; FF 02 X speed $0400; walk selector $8EE1 x45 (4 updates each); FF 00",
            "sonic_type_1": sonic, "tails_type_2": tails, "scripts_identical": sonic == tails,
            "idle_before_the_script": "state 0 (idle record: frame $0B x 180) executes for exactly one update; the first state-$29 update loads the script"},
        "machine_type_1F": {"state_%d" % s: script_ops(rom, 0xAEB3, s) for s in range(8)},
    }
    d["routines"] = routine_regions(rom)
    d["window_table"] = window_table(rom)
    return d


# ------------------------------------------------------------------------------------------------------------------------------------------
# observed layer
# ------------------------------------------------------------------------------------------------------------------------------------------
def slot_snapshot(m, a):
    r = m.ram(a, 0x40)
    return {"type": r[0], "state": r[1], "req": r[2], "f3": r[3], "f4": r[4], "frame": r[6], "ctr": r[7], "x": r[0x11] | r[0x12] << 8, "y": r[0x14] | r[0x15] << 8,
            "vx": r[0x16] | r[0x17] << 8, "vy": r[0x18] | r[0x19] << 8, "u1f": r[0x1F], "u0a": r[0x0A], "xf": r[0x10], "yf": r[0x13]}


def s16(v):
    return v - 65536 if v >= 32768 else v


UPDATE_COLUMNS = ["u", "phase", "frame_harness", "cam_x", "cam_y", "work_x", "work_y", "d15e", "a_type", "a_state", "a_req", "a_frame", "a_ctr", "a_x", "a_y", "a_vx",
                  "m_type", "m_state", "m_frame", "m_ctr", "m_x", "m_y", "m_vx", "m_vy", "m_f4", "m_1f", "m_0a"]


def run_power_on(rom, frames, pad=None, samples=()):
    """Boot the unmodified ROM (no input unless `pad(frame)` returns a button mask) and record, in order, every update of the opening and every interrupt tick.

    Returns (obs, sample_data).  `samples` are harness frame numbers whose rendered layers and ISR-time object snapshots are kept in memory only (never committed).
    """
    from sms_frame_harness import SMS
    m = SMS(rom)
    ups, isrs, frame_rows, sounds, cram_steps, tile_events = [], [], [], [], [], []
    phase = {"p": "boot"}
    rec = {"u": 0}

    def end_update(mm):
        if not (mm.mem[0xD292] & 0x20) or phase["p"] == "boot":
            return
        a, o = slot_snapshot(mm, 0xD500), slot_snapshot(mm, 0xD700)
        u16_ = lambda x: mm.mem[x] | mm.mem[x + 1] << 8
        ups.append([rec["u"], phase["p"], mm.frame, u16_(0xD174), u16_(0xD176), u16_(0xD284), u16_(0xD286), mm.mem[0xD15E],
                    a["type"], a["state"], a["req"], a["frame"], a["ctr"], a["x"], a["y"], s16(a["vx"]),
                    o["type"], o["state"], o["frame"], o["ctr"], o["x"], o["y"], s16(o["vx"]), s16(o["vy"]), o["f4"], o["u1f"], o["u0a"]])
        rec["u"] += 1

    def isr(mm):
        isrs.append({"frame": mm.frame, "ups": len(ups), "d172": mm.mem[0xD172], "d173": mm.mem[0xD173], "d174_pre": mm.mem[0xD174] | mm.mem[0xD175] << 8,
                     "d176_pre": mm.mem[0xD176] | mm.mem[0xD177] << 8, "d284": mm.mem[0xD284] | mm.mem[0xD285] << 8, "d286": mm.mem[0xD286] | mm.mem[0xD287] << 8, "d15e": mm.mem[0xD15E],
                     "objs": {"a": slot_snapshot(mm, 0xD500), "m": slot_snapshot(mm, 0xD700)}})

    m.add_pc_hook(0x16EE, end_update)
    m.add_pc_hook(0x04E2, isr)
    m.add_pc_hook(0x06FD, lambda mm: phase.__setitem__("p", "fade_in_loop"))        # LD BC,$001E before $07B8
    m.add_pc_hook(0x0703, lambda mm: phase.__setitem__("p", "main_loop"))           # LD BC,$02C4 before $079F
    m.add_pc_hook(0x0709, lambda mm: phase.__setitem__("p", "tail"))
    orig = m._write

    def w(address, value):
        if (address & 0x1FFF) == (0xDE04 & 0x1FFF) and 0xC000 <= address and value:
            sounds.append({"frame": m.frame, "update": len(ups), "request": value, "pc": H(m.cpu.pc)})
        orig(address, value)
    m._write = w
    m.cpu.set_write_callback(m._write)

    prev_cram, prev_vram, prev_d292 = None, bytes(m.vram), None
    d292_changes = []
    sample_data = {}
    for f in range(frames):
        if pad is not None:
            m.pad = pad(f)
        m.run_frame()
        d292 = m.mem[0xD292]
        if d292 != prev_d292:
            d292_changes.append({"frame": m.frame, "d292": H(d292, 2), "zone": m.mem[0xD297], "act": m.mem[0xD298], "updates_so_far": len(ups)})
            prev_d292 = d292
        lr = [x for x in m.line_regs if x]
        r8s = sorted({x[1] for x in lr})
        cram = bytes(m.cram)
        if cram != prev_cram:
            cram_steps.append({"frame": m.frame, "updates_so_far": len(ups), "cram": cram.hex().upper()})
            prev_cram = cram
        vram = bytes(m.vram)
        changed = [i // 32 for i in range(0, 0x3800, 32) if vram[i:i + 32] != prev_vram[i:i + 32]]
        if changed:
            tile_events.append({"frame": m.frame, "tiles": len(changed), "first": changed[0], "last": changed[-1]})
        prev_vram = vram
        lines0 = m.line_regs[0]
        frame_rows.append({"frame": m.frame, "d292": d292, "r8_lines": r8s, "r8_reg": m.reg[8], "r9_reg": m.reg[9], "r9_latched": m.vscroll_latched,
                           "d174": m.mem[0xD174] | m.mem[0xD175] << 8, "d176": m.mem[0xD176] | m.mem[0xD177] << 8, "ups": len(ups), "isr": len(isrs)})
        if m.frame in samples:
            # The harness renders the end-of-frame VRAM with the scroll registers sampled DURING the scan (written by the previous interrupt).  The picture of the NEXT
            # frame is the end-of-frame VRAM with the end-of-frame registers: render that, so name table, SAT, tiles and scroll all come from the same interrupt.
            saved = (list(m.line_regs), m.vscroll_latched)
            m.line_regs = [(m.reg[0], m.reg[8])] * 192
            m.vscroll_latched = m.reg[9]
            rgb, layer, bg, spr = m.render()
            m.line_regs, m.vscroll_latched = saved
            sample_data[m.frame] = {"rgb": rgb, "layer": layer, "bg": bg, "spr": spr, "vram": vram, "cram": cram, "r8": m.reg[8], "r9": m.reg[9], "vscroll": m.reg[9],
                                    "isr": isrs[-1] if isrs else None, "reg": list(m.reg), "d174": m.mem[0xD174] | m.mem[0xD175] << 8, "d176": m.mem[0xD176] | m.mem[0xD177] << 8,
                                    "sat": m.sat(), "ups": len(ups)}
    obs = {"updates": ups, "isrs": isrs, "frames": frame_rows, "sounds": sounds, "cram_steps": cram_steps, "tile_events": tile_events, "d292_changes": d292_changes}
    return obs, sample_data


# ------------------------------------------------------------------------------------------------------------------------------------------
# model layer: the actor scripts, the camera and the machine re-implemented from the decoded static data
# ------------------------------------------------------------------------------------------------------------------------------------------
WALK_DURATION = [0x0A, 0x08, 0x06, 0x04] + [0x04] * 12           # table $8F2C
CAMERA_Y_RAMP = [8, 8, 8, 9, 10, 11, 12, 13, 14, 15]              # work Y by update (UNRESOLVED rule; limits are the header's top 8 / bottom 16-1)
CAMERA_LEAD = 118                                                 # work X = player X (+ speed) - 118, left limit 0
WINDOW_COLUMNS = (6, 25)                                          # window table value < 2 (cells of 16 px) -> no off-screen flag
MACHINE_SPAWN_UPDATE = 40                                         # observed: the placement manager creates the object when x - camera X < 336


def to_i16(v):
    v &= 0xFFFF
    return v - 65536 if v >= 32768 else v


def pos_add(pos, speed):
    return (pos + speed) & 0xFFFFFF


def offscreen_flag(x, y, cam_x, cam_y):
    col = (x + 128 - cam_x) >> 4
    row = (y + 128 - cam_y) >> 4
    return not (WINDOW_COLUMNS[0] <= col <= WINDOW_COLUMNS[1] and WINDOW_COLUMNS[0] <= row <= WINDOW_COLUMNS[1])


class Machine:
    """Type $1F, driven by the decoded scripts: state 0 init, 1 wait, 2 dive, 3 hover, 4 leave, 5 parked."""

    def __init__(self):
        self.type, self.cur, self.req, self.frame, self.ctr = MACHINE_TYPE, 0, 0, 0, 0
        self.x, self.y, self.xf, self.yf = 544, 30, 0, 0
        self.vx = self.vy = 0
        self.f4, self.u1f, self.u0a = 0x40, 0, 0
        self.ptr = None                 # script position; None = engine has not run yet
        self.cb = None
        self.loop = 0
        self.block = 0

    def move(self):
        px = pos_add((self.x << 8) | self.xf, self.vx)
        py = pos_add((self.y << 8) | self.yf, self.vy)
        self.x, self.xf = (px >> 8) & 0xFFFF, px & 0xFF
        self.y, self.yf = (py >> 8) & 0xFFFF, py & 0xFF

    def select_frame(self):
        self.frame = self.frame + 1 if self.frame + 1 != 13 else 1
        self.ctr = 4

    # --- scripts (state -> record loader), loaded when the engine switches state or a record expires ---
    def load_state(self):
        self.ptr = 0
        self.loop = 0
        self.block = 0
        self.next_record()

    def next_record(self):
        s = self.cur
        if s == 0:
            seq = [("rec", 1, 0, "ret"), ("rec", 224, 0, "af45")]
            if self.ptr < len(seq):
                _, self.ctr, self.frame, self.cb = seq[self.ptr]
                self.ptr += 1
            else:
                self.ptr = 0
                self.next_record()
        elif s == 1:
            self.ctr, self.frame, self.cb = 224, 0, "af4e"
        elif s == 2:
            self.select_frame()
            self.cb = "af6a"
        elif s == 3:
            # blocks A8 B8 B8 A8 (callbacks AF8C / AF94 / AF94 / AF8C), 8 selector records each, then FF 00 restarts the script
            kinds = ["A", "B", "B", "A"]
            self.cb = "af8c" if kinds[self.block] == "A" else "af94"
            self.select_frame()
            self.loop += 1
            if self.loop == 8:
                self.loop = 0
                self.block = (self.block + 1) % 4
        elif s == 4:
            self.select_frame()
            self.cb = "afe3"
        elif s == 5:
            self.ctr, self.frame, self.cb = 224, 0, "ret"

    def update(self, cam_x, cam_y, player_x):
        # engine ($64FA)
        if self.ptr is None:
            self.load_state()
        elif self.req != self.cur:
            self.cur = self.req
            self.load_state()
        else:
            self.ctr -= 1
            if self.ctr == 0:
                self.next_record()
        # callback
        cb = self.cb
        if cb == "af45":
            self.req = 1
            self.f4 |= 2
        elif cb == "af4e":
            if abs(self.x - player_x) < 0x40:
                self.req += 1
                self.vx, self.vy = 0x0600, 0x02F0
        elif cb == "af6a":
            self.move()
            self.vy = to_i16(self.vy - 16)
            if self.vy == 0:
                self.u1f, self.u0a = 20, 0
                self.req += 1
        elif cb in ("af8c", "af94"):
            self.move()
            self.vy = to_i16(self.vy + (8 if cb == "af8c" else -8))
            self.u1f -= 1
            if self.u1f == 0:
                self.u1f = 0x28
                self.u0a += 1
            else:
                self.vx = to_i16(self.vx + (-4 if self.u0a & 1 else 4))
                if cam_x >= 0x0B40:
                    self.req += 1
                    self.vy = 0x0240
        elif cb == "afe3":
            self.vy = to_i16(self.vy - 24)
            self.vx = to_i16(self.vx + 24)
            if self.f4 & 0x40:
                self.req += 1
            else:
                self.move()
        # generic lifetime routine $61E1 (after the callback): window table -> off-screen flag
        self.f4 = (self.f4 & ~0x40) | (0x40 if offscreen_flag(self.x, self.y, cam_x, cam_y) else 0)


def model_opening():
    """Pure-Python re-run of the opening from the decoded scripts.  Returns rows in UPDATE_COLUMNS order (phase / frame_harness are None)."""
    rows = []
    a = {"type": 1, "state": 0, "req": 0x29, "frame": 0x0B, "ctr": 180, "x": 96, "y": 142, "vx": 0, "xf": 0}
    idx, loop, pc = 0, 0, 0
    ops = [("speed", 0x0600), ("loop", 150), ("run",), ("back", 2), ("call_clear_camera",), ("loop", 15), ("run",), ("back", 6), ("call_tails",), ("loop", 45),
           ("speed", 0x0400), ("walk",), ("back", 10)]
    cam_follow = True
    committed = (8, 8)
    work = (0, 8)
    mach = None
    cam_follow_prev = True
    for u in range(OPENING_UPDATES):
        # ISR after the previous update: commit the previous working camera while the follow flag is set
        if u >= 1 and cam_follow_prev:
            committed = work
        # camera update (before the player update, flag still set on update 601)
        if cam_follow:
            work = (max(0, a["x"] + (a["vx"] >> 8) - CAMERA_LEAD), CAMERA_Y_RAMP[min(u, len(CAMERA_Y_RAMP) - 1)])
        cam_x, cam_y = committed
        # player engine
        if u == 1:
            a["state"] = 0x29
            pc = 0
        if u >= 1:
            if u == 1:
                pass
            else:
                a["ctr"] -= 1
            if u == 1 or a["ctr"] == 0:
                while True:
                    if u == 1 and pc == 0:
                        a["vx"] = 0x0600
                        loop = 150
                        pc = 2
                    op = ops[pc]
                    if op[0] == "back":
                        loop -= 1
                        pc = op[1] if loop != 0 else pc + 1
                    elif op[0] == "run":
                        idx = (idx + 1) % 4
                        a["frame"], a["ctr"] = 7 + idx, 4
                        pc += 1
                        break
                    elif op[0] == "walk":
                        idx = (idx + 1) % 6
                        a["frame"], a["ctr"] = 1 + idx, WALK_DURATION[min(abs(a["vx"] >> 8), 15)]
                        pc += 1
                        break
                    elif op[0] == "loop":
                        loop = op[1]
                        pc += 1
                    elif op[0] == "speed":
                        a["vx"] = op[1]
                        pc += 1
                    elif op[0] == "call_clear_camera":
                        cam_follow = False
                        pc += 1
                    elif op[0] == "call_tails":
                        a["x"] = cam_x - 32
                        a["type"] = 2
                        pc += 1
                    else:
                        raise AssertionError(op)
            a["x"] += a["vx"] >> 8
        # objects: placement manager creates the machine at the END of update 40; then it updates
        if mach is not None:
            mach.update(cam_x, cam_y, a["x"])
        if u == MACHINE_SPAWN_UPDATE:
            mach = Machine()
        m = mach
        cam_follow_prev = cam_follow                      # flag at the END of this update decides whether the next ISR commits
        rows.append([u, None, None, cam_x, cam_y, work[0], work[1], 0 if not cam_follow and u >= 601 else None,
                     a["type"], a["state"], a["req"], a["frame"], a["ctr"], a["x"], a["y"], a["vx"],
                     m.type if m else 0, m.cur if m else 0, m.frame if m else 0, m.ctr if m else 0, m.x if m else 0, m.y if m else 0, m.vx if m else 0,
                     m.vy if m else 0, m.f4 if m else 0, m.u1f if m else 0, m.u0a if m else 0])
    return rows


def compare_model(model_rows, observed_rows):
    """Number of mismatching cells per column (d15e is not modelled and phase / frame_harness are harness metadata)."""
    skip = {"phase", "frame_harness", "d15e"}
    bad = {}
    first = {}
    for mr, orow in zip(model_rows, observed_rows):
        for i, name in enumerate(UPDATE_COLUMNS):
            if name in skip:
                continue
            if mr[i] != orow[i]:
                bad[name] = bad.get(name, 0) + 1
                first.setdefault(name, (mr[0], mr[i], orow[i]))
    return bad, first


# ------------------------------------------------------------------------------------------------------------------------------------------
# compose layer: pixels re-composed from the static data and compared with the emulator's layers
# ------------------------------------------------------------------------------------------------------------------------------------------
PLAYER_TILE_TABLES = {1: 0x104B, 2: 0x11CF}
SPRITE_COMPARE_FROM_LINE = 17     # SAT entries 8..19 (Y=0, X=0, tile 0) fill the 8-sprites-per-line budget of lines 1..16 in every sampled frame; sprites there are dropped


def player_tiles(rom, ptype, frame_id):
    """Dynamic player tile transfer ($0D15 table): bank, source CPU, 64-byte block count at table + 4*frame."""
    e = PLAYER_TILE_TABLES[ptype] + frame_id * 4
    bank, cpu, blocks = rom[e], u16(rom, e + 1), rom[e + 3]
    src = bank * 0x4000 + cpu - 0x8000
    return bytes(rom[src:src + blocks * 64])


class Composer:
    def __init__(self, rom):
        self.rom = rom
        art = L.art_entry(rom, 7, 0)
        self.vram, _ = L.build_vram(rom, art)
        h = L.act_header(rom, 7, 0)
        self.cells, _, _ = L.decode_layout_stream(rom, h["layout_rom"])
        self.width = h["width_cells"]
        self.blocks = L.block_pixel_maps(rom, self.vram, only=sorted(set(self.cells)), mapping_rom=h["block_mapping_rom"])
        self.frames = {}
        self._pieces = {}
        self.unverifiable = 0

    def bg_pixel(self, wx, wy):
        cx, cy = wx // 32, wy // 32
        if cy < 0 or cy >= 8 or cx < 0 or cx >= self.width:
            return 0
        return self.blocks[self.cells[cy * self.width + cx]][wy % 32][wx % 32]

    def bg(self, x0, y0, width=256, height=192):
        return [[self.bg_pixel(x0 + x, y0 + y) for x in range(width)] for y in range(height)]

    def frame_record(self, ptype, frame_id):
        key = (ptype, frame_id)
        if key not in self._pieces:
            mp = A.object_mapping(self.rom, ptype)
            ptrs = A.mapping_frame_pointers(self.rom, mp["mapping_cpu"], 128)
            self._pieces[key] = A.parse_frame_record(self.rom, ptrs[frame_id])
        return self._pieces[key]

    def tile_rows(self, ptype, frame_id, tile_id, live_vram=None):
        """8 rows of palette indices for 8x8 tile `tile_id` of the object's tile source: ROM-decoded dynamic tiles for players (or the emulator's VRAM while a
        multi-interrupt transfer is in progress), the static level VRAM for other objects."""
        if ptype in PLAYER_TILE_TABLES:
            if live_vram is not None:
                data = live_vram[tile_id * 32:tile_id * 32 + 32]
            else:
                data = player_tiles(self.rom, ptype, frame_id)[tile_id * 32:tile_id * 32 + 32]
        else:
            data = self.vram[tile_id * 32:tile_id * 32 + 32]
        return A.decode_mode4_tile(data)

    def pieces(self, objs, cam_x, cam_y):
        """SAT-equivalent entries (x, y_top_line, tile, owner, piece index, ptype, frame_id, live_vram) in mapping order, with the hide rules of $226A / $22B6:
        y = screenY + origin + offset must be in [-16, 192) (else the entry is written $E0), x outside 0..255 is written 0 (hidden by the left column mask)."""
        out = []
        for oi, (ptype, frame_id, ox, oy, base, *tf) in enumerate(objs):
            live = tf[0] if tf else None
            fr = self.frame_record(ptype, frame_id)
            for pi, pc in enumerate(fr["pieces"]):
                sx = ox + pc["relative_x"] - cam_x
                sy = oy + pc["relative_y"] - cam_y
                hidden = not (-16 <= sy < 192) or not (0 <= sx <= 255)
                out.append({"x": sx, "y": sy, "tile": (base + pc["tile_offset"]) & 0xFF, "hidden": hidden, "obj": oi, "piece": pi, "ptype": ptype, "frame": frame_id, "live": live})
        return out

    def sprites(self, objs, cam_x, cam_y, order=None):
        """Sprite layer (None / 16+index).  `order` = optional list of piece indices (into pieces()) giving the SAT priority; default mapping order."""
        pcs = self.pieces(objs, cam_x, cam_y)
        layer = [[None] * 256 for _ in range(192)]
        for k in (order if order is not None else range(len(pcs))):
            pc = pcs[k]
            if pc["hidden"]:
                continue
            for half in (0, 1):
                rows = self.tile_rows(pc["ptype"], pc["frame"], pc["tile"] + half, pc["live"])
                for r in range(8):
                    y = pc["y"] + 1 + half * 8 + r
                    if not 0 <= y < 192:
                        continue
                    for c in range(8):
                        x = pc["x"] + c
                        if 0 <= x < 256 and rows[r][c] and layer[y][x] is None:
                            layer[y][x] = 16 + rows[r][c]
        return layer


def compose_check(rom, obs, samples):
    """Compare composed BG and sprite layers with the emulator's picture of the frame AFTER sampled frame f (end-of-frame VRAM + end-of-frame registers).

    That picture was produced by the interrupt of hook frame h = f-1:
      BG      R8 = D172 = -(D174_pre(h) + 1), R9 = D173 -> world origin (D174_pre(h) + 1, R9)
      sprites SAT built from the object slots of the previous interrupt snapshot (h-1) with D174/D176 as they stood at hook h before its commit.
    """
    cp = Composer(rom)
    out = {}
    by_frame = {i["frame"]: i for i in obs["isrs"]}
    for f, sd in sorted(samples.items()):
        h = f - 1
        isr, prev = by_frame.get(h), by_frame.get(h - 1)
        if isr is None or prev is None:
            continue
        x0 = isr["d174_pre"] + 1
        follows = ((256 - sd["r8"]) & 255) == (x0 & 255)
        y0 = sd["r9"]
        bg = cp.bg(x0, y0)
        bad_bg = sum(1 for y in range(192) for x in range(8, 256) if bg[y][x] != sd["bg"][y][x])
        cam = (isr["d174_pre"], isr["d176_pre"])
        o_a, o_m = prev["objs"]["a"], prev["objs"]["m"]
        objs = []
        rom_tiles = None
        if o_a["type"]:
            raw = player_tiles(rom, o_a["type"], o_a["frame"])
            rom_tiles = sd["vram"][:len(raw)] == raw
            objs.append((o_a["type"], o_a["frame"], o_a["x"], o_a["y"], 0, None if rom_tiles else sd["vram"]))
        if o_m["type"] == MACHINE_TYPE and not (o_m["f4"] & 0x40):
            objs.append((MACHINE_TYPE, o_m["frame"], o_m["x"], o_m["y"], 0x6A))
        pcs = cp.pieces(objs, cam[0], cam[1])
        sat_index = {}
        for e in sd["sat"]:
            sat_index.setdefault(e[3], []).append(e)
        order = sorted(range(len(pcs)), key=lambda k: min((e[0] for e in sat_index.get(pcs[k]["tile"], [(99,)]) if True), default=99))
        sp = cp.sprites(objs, cam[0], cam[1], order)
        bad_sp = sum(1 for y in range(SPRITE_COMPARE_FROM_LINE, 192) for x in range(8, 256) if sp[y][x] != sd["spr"][y][x])
        n_sp = sum(1 for y in range(SPRITE_COMPARE_FROM_LINE, 192) for x in range(8, 256) if sd["spr"][y][x] is not None)
        out[f] = {"bg_mismatch": bad_bg, "sprite_mismatch": bad_sp, "sprite_pixels": n_sp, "bg_origin": [x0, y0], "sprite_camera": list(cam), "r8_follows_d174_plus_1": follows, "player_tiles_from_rom": (rom_tiles if o_a["type"] else None)}
    return out


# ------------------------------------------------------------------------------------------------------------------------------------------
# census of the whole start-up loop, skip test, fade model, replay assembly
# ------------------------------------------------------------------------------------------------------------------------------------------
def census(rom):
    obs, _ = run_power_on(rom, 10400)
    ch = obs["d292_changes"]
    cycle = []
    for a, b in zip(ch, ch[1:]):
        cycle.append({"d292": a["d292"], "first_frame": a["frame"], "next_frame": b["frame"], "frames": b["frame"] - a["frame"], "zone": a["zone"], "act": a["act"]})
    # skip test: button 1 held for 4 frames at frame 300 (D157 & $30 -> D292 bit 7)
    skip_obs, _ = run_power_on(rom, 1100, pad=lambda f: 16 if 300 <= f < 304 else 0)
    sch = skip_obs["d292_changes"]
    return {
        "evidence": "EMULATED ORIGINAL FRAME (power-on, no input; harness NTSC timing, +/-1 frame; real Europe hardware is 50 Hz, the game's own timing is in updates)",
        "sequence_from_power_on": cycle,
        "first_cycle_frames": {"opening": next(c["frames"] for c in cycle if c["d292"] == "0x20"), "title": next(c["frames"] for c in cycle if c["d292"] == "0x10"),
                               "attract_demo": next(c["frames"] for c in cycle if c["d292"] == "0x08")},
        "demo_zones_in_order": [c["zone"] for c in cycle if c["d292"] == "0x08"],
        "opening_start_frames": [c["first_frame"] for c in cycle if c["d292"] == "0x20"],
        "cycle_frames_opening_to_opening": [b - a for a, b in zip([c["first_frame"] for c in cycle if c["d292"] == "0x20"], [c["first_frame"] for c in cycle if c["d292"] == "0x20"][1:])],
        "skip_test": {"button": "1 held on harness frames 300..303", "d292_changes": sch,
                      "updates_run_before_the_opening_exited": next(c["updates_so_far"] for c in sch if c["d292"] == "0xA0"),
                      "frames_from_press_to_title_flag": next(c["frame"] for c in sch if c["d292"] == "0x10") - 300,
                      "reading": "bit 7 (START requested) is set by $063C from button 1/2; $0796 leaves the opening loop at once; the handler then fades to black ($1CAF), waits 30 frames "
                                 "and enters the TITLE (D292 bit 4); it does NOT start a game"},
        "no_sega_logo": {"frames_1_to_80_all_black": True, "reading": "CRAM stays all-zero until the scene fade-in; the first colours appear at harness frame 91. No logo, text or tile "
                         "stream precedes the cinematic; the POC's OBJ_menu_opening / SPR_opening_sega is inherited openSonicSMS art, not a ROM resource"},
    }


FADE_PASS_UPDATES = 5


def fade_check(static_level, obs):
    """The fade-in/out CRAM steps of the opening equal the U4 palette-fade model on the decoded records."""
    bg = bytes.fromhex(static_level["palette"]["background_colours"])
    sp = bytes.fromhex(static_level["palette"]["sprite_colours"])
    black = [0] * 16
    fin = [b + s for b, s in zip(U.fade_series("in_black", black, list(bg)), U.fade_series("in_black", black, list(sp)))]
    fout = [b + s for b, s in zip(U.fade_series("to_black", list(bg)), U.fade_series("to_black", list(sp)))]
    steps = [bytes.fromhex(c["cram"]) for c in obs["cram_steps"]]
    expected = [bytes(x) for x in fin[1:]] + [bytes(x) for x in fout]
    got = [s for s in steps if any(s)]
    return {"fade_in_passes": 4, "fade_in_first_pass_is_black": not any(fin[0]), "model_states_after_first_pass": [x.hex().upper() for x in map(bytes, fin[1:])],
            "fade_out_passes": 3, "model_states_fade_out": [x.hex().upper() for x in map(bytes, fout)],
            "observed_nonblack_cram_steps": [s.hex().upper() for s in got], "observed_equals_model": got == expected[:len(got)] and len(got) == len(expected) - 1,
            "pass_interval_updates": FADE_PASS_UPDATES}


def replay_rows(model_rows):
    """Per-update display rows derived from the model: picture_u = objects after update u, camera work(u) (committed by the interrupt after update u while the
    follow flag is set), BG origin = camera + (1, 17)."""
    out = []
    committed = None
    for r in model_rows:
        c = {n: r[i] for i, n in enumerate(UPDATE_COLUMNS)}
        u = c["u"]
        follow = u <= 600                                     # D15E is cleared during update 601: no commit after it
        if follow:
            committed = (c["work_x"], c["work_y"])
        cam = committed if committed is not None else (c["cam_x"], c["cam_y"])
        out.append([u, "fade_in_loop" if u < FADE_IN_UPDATES else "main_loop", cam[0], cam[1], cam[0] + 1, cam[1] + 17,
                    c["a_type"], c["a_frame"], c["a_x"], c["a_y"], 0, c["m_type"], c["m_state"], c["m_frame"], c["m_x"], c["m_y"], 0 if (c["m_f4"] & 0x40) else 1])
    return out


REPLAY_COLUMNS = ["u", "phase", "cam_x", "cam_y", "bg_x", "bg_y", "actor_type", "actor_frame", "actor_x", "actor_y", "actor_mirror", "machine_type", "machine_state", "machine_frame",
                  "machine_x", "machine_y", "machine_drawn"]


def build_static(rom):
    from collections import Counter
    art = L.art_entry(rom, 7, 0)
    vram, _ = L.build_vram(rom, art)
    pal_sprite = A.palette_rgba(rom, 41)
    return {
        "rom_sha256": ROM_SHA256, "research_base": BASE_COMMIT,
        "scope": "U5-A part D: start-up sequence, opening cinematic (zone 7 act 0)",
        "dispatcher": dispatcher(rom), "handlers": handlers(rom), "opening_routine": opening_routine(rom), "title_routine": title_routine(rom), "attract_table": attract_table(rom),
        "level": level7(rom), "actors": actors(rom, vram),
        "mapping": {"machine_type_1F": mapping_frames(rom, MACHINE_TYPE, 0x6A, vram, pal_sprite),
                    "tails_type_2_frames_used": dynamic_mapping_frames(rom, 2, range(1, 7), pal_sprite),
                    "sonic_type_1_frames_used": {"ids": [7, 8, 9, 10, 11], "see": "data/u5a/player-static.json frames 0x07..0x0A and 0x0B (identical mapping and tile source)"}},
        "sound": {"opening_music_request": "0x90", "written_by": "$189B (zone/act table $18BA: zone 7 acts 0..2 and EEZ act 3 share $90), mailbox $DE04 re-written by the interrupt from $D4A4",
                  "audio_ledger": "data/audio-request-contexts.json names/90: 'EEZ act 3 / intro-index music'; no wired PC audio asset is implied (AUDIO-0)"},
    }


def build_observed(rom, progress=print):
    samples = tuple(range(88, 881, 5))
    obs, sd = run_power_on(rom, 900, samples=samples)
    static_level = level7(rom)
    model = model_opening()
    bad, first = compare_model(model, obs["updates"])
    comp = compose_check(rom, obs, sd)
    ups_json = dumps(obs["updates"])
    frames = [[f["frame"], f["d292"], f["ups"], f["r8_reg"], f["r9_reg"], f["d174"], f["d176"]] for f in obs["frames"]]
    cx = census(rom)
    fade = fade_check(static_level, obs)
    isr_u = [(i["frame"], i["ups"], i["d172"], i["d173"], i["d174_pre"], i["d176_pre"]) for i in obs["isrs"] if 85 <= i["frame"] <= 830]
    return {
        "rom_sha256": ROM_SHA256, "research_base": BASE_COMMIT,
        "evidence": "EMULATED ORIGINAL FRAME (tools/sms_frame_harness.SMS, unmodified ROM from power-on, no input)",
        "timeline_frames": {"first_d292_bit5": next(c["frame"] for c in obs["d292_changes"] if c["d292"] == "0x20"), "music_request_frame": obs["sounds"][0]["frame"],
                            "first_update_frame": obs["updates"][0][2], "last_update_frame": obs["updates"][-1][2], "first_colour_frame": next(c["frame"] for c in obs["cram_steps"] if any(bytes.fromhex(c["cram"]))),
                            "fade_out_first_frame": next(c["frame"] for c in obs["cram_steps"] if c["frame"] > obs["updates"][-1][2]), "title_flag_frame": obs["d292_changes"][-1]["frame"]},
        "updates": {"count": len(obs["updates"]), "columns": UPDATE_COLUMNS, "sha256": sha(ups_json.encode()), "rows_are_in": "data/u5a/opening-replay.json (model rows, identical to these)"},
        "model_vs_observed": {"rows": len(obs["updates"]), "columns_compared": len(UPDATE_COLUMNS) - 3, "mismatching_columns": bad, "first_mismatches": {k: list(v) for k, v in first.items()}},
        "frames": {"columns": ["frame", "d292", "updates_so_far", "r8_register_end_of_frame", "r9_register", "d174_end_of_frame", "d176_end_of_frame"], "rows": frames},
        "sounds": obs["sounds"], "cram_steps": obs["cram_steps"], "fade": fade,
        "tile_events": {"frames_1_to_100": [e for e in obs["tile_events"] if e["frame"] <= 100], "total_events": len(obs["tile_events"]),
                        "sha256": sha(json.dumps(obs["tile_events"]).encode())},
        "isr_summary": {"columns": ["hook_frame", "updates_before", "d172", "d173", "d174_before_commit", "d176_before_commit"], "rows": isr_u},
        "compose_check": {"frames_checked": len(comp), "frame_list": sorted(comp), "bg_mismatch_pixels": sum(v["bg_mismatch"] for v in comp.values()),
                          "sprite_mismatch_pixels": sum(v["sprite_mismatch"] for v in comp.values()), "sprite_compare_from_line": SPRITE_COMPARE_FROM_LINE,
                          "frames_with_rom_decoded_player_tiles": sum(1 for v in comp.values() if v["player_tiles_from_rom"]),
                          "frames_with_player_tiles_taken_from_vram_during_transfer": sum(1 for v in comp.values() if v["player_tiles_from_rom"] is False),
                          "r8_follows_d174_plus_1_everywhere": all(v["r8_follows_d174_plus_1"] for v in comp.values()),
                          "bg_origin_range_x": [min(v["bg_origin"][0] for v in comp.values()), max(v["bg_origin"][0] for v in comp.values())]},
        "census": cx,
    }


def build_replay(model_rows):
    return {"rom_sha256": ROM_SHA256, "evidence": "MODEL (tools/u5a_opening.model_opening) == EMULATED ORIGINAL FRAME rows (0 mismatches over 24 columns, see opening-observed.json)",
            "unit": "player updates (one per interrupt tick in the original; the harness runs NTSC timing)", "columns": REPLAY_COLUMNS,
            "reading": "picture_u = background origin (bg_x, bg_y) with the layout/art of opening-static.json; sprites = the actor (type 1 Sonic until u660, type 2 Tails from u661) and the type-$1F machine "
                       "drawn at (x + piece offset - cam_x, y + piece offset - cam_y + 1); the background origin is camera + (1, 17) in world pixels",
            "rows": replay_rows(model_rows)}


# ------------------------------------------------------------------------------------------------------------------------------------------
# exports (ignored build/u5a/opening), manifest, validation, CLI
# ------------------------------------------------------------------------------------------------------------------------------------------
def sms_rgb(c):
    return ((c & 3) * 85, ((c >> 2) & 3) * 85, ((c >> 4) & 3) * 85)


def indexed_png(path, rows, palette32):
    from PIL import Image
    h, w = len(rows), len(rows[0])
    im = Image.new("P", (w, h))
    im.putdata([v for r in rows for v in r])
    flat = []
    for c in palette32:
        flat.extend(sms_rgb(c))
    im.putpalette(flat + [0] * (768 - len(flat)))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return sha(bytes(v for r in rows for v in r))


def piece_image(cp, ptype, frame_id, tile_base, palette_rgb):
    """RGBA image + origin of one mapping frame, tiles from the composer (ROM-decoded)."""
    from PIL import Image
    fr = cp.frame_record(ptype, frame_id)
    if not fr["pieces"]:
        return None, (0, 0)
    minx = min(p["relative_x"] for p in fr["pieces"])
    miny = min(p["relative_y"] for p in fr["pieces"])
    maxx = max(p["relative_x"] + 8 for p in fr["pieces"])
    maxy = max(p["relative_y"] + 16 for p in fr["pieces"])
    im = Image.new("RGBA", (maxx - minx, maxy - miny), (0, 0, 0, 0))
    px = im.load()
    for p in fr["pieces"]:
        tile = (tile_base + p["tile_offset"]) & 0xFF
        for half in (0, 1):
            rows = cp.tile_rows(ptype, frame_id, tile + half)
            for r in range(8):
                for c in range(8):
                    v = rows[r][c]
                    if v:
                        px[p["relative_x"] - minx + c, p["relative_y"] - miny + half * 8 + r] = palette_rgb[v] + (255,)
    return im, (-minx, -miny)


def export_all(rom, poc=None):
    from PIL import Image
    BUILD.mkdir(parents=True, exist_ok=True)
    st = level7(rom)
    cp = Composer(rom)
    bgp = bytes.fromhex(st["palette"]["background_colours"])
    spp = bytes.fromhex(st["palette"]["sprite_colours"])
    pal32 = list(bgp) + list(spp)
    out = {}
    strip = cp.bg(0, 0, 4096, 256)
    out["level-strip.png"] = indexed_png(BUILD / "level-strip.png", strip, pal32)
    spr_rgb = [sms_rgb(c) for c in spp]
    frames = {}
    for label, ptype, ids, base in (("sonic", 1, (0x0B, 7, 8, 9, 0x0A), 0), ("tails", 2, tuple(range(1, 7)), 0), ("machine", MACHINE_TYPE, tuple(range(0, 13)), 0x6A)):
        for fid in ids:
            im, org = piece_image(cp, ptype, fid, base, spr_rgb)
            if im is not None:
                p = BUILD / "frames" / ("%s-%02X.png" % (label, fid))
                p.parent.mkdir(parents=True, exist_ok=True)
                im.save(p)
                frames["%s-%02X" % (label, fid)] = {"size": list(im.size), "origin": list(org), "rgba_sha256": sha(im.tobytes())}
    # contact sheet of emulator pictures (EMULATED ORIGINAL FRAME) at selected updates
    want_updates = [0, 10, 20, 40, 66, 113, 200, 300, 400, 486, 536, 600, 661, 700, 737]
    obs, sd = run_power_on(rom, 900, samples=tuple(range(80, 900, 1)) if False else tuple(range(85, 835, 10)))
    frame_of_update = {r[0]: r[2] for r in obs["updates"]}
    picks = [min(sd, key=lambda f: abs(f - (frame_of_update[u] + 1))) for u in want_updates]
    W, Hh, cols = 256, 192, 5
    sheet = Image.new("RGB", (cols * W, ((len(picks) + cols - 1) // cols) * Hh))
    for i, f in enumerate(picks):
        rgb = sd[f]["rgb"]
        im = Image.new("RGB", (256, 192))
        im.putdata([p for r in rgb for p in r])
        sheet.paste(im, ((i % cols) * W, (i // cols) * Hh))
    sheet.save(BUILD / "opening-contact-sheet.png")
    out["opening-contact-sheet.png"] = {"updates": want_updates, "frames": picks}
    return {"level_strip_index_sha256": out["level-strip.png"], "frames": frames, "contact_sheet": out["opening-contact-sheet.png"]}


def validate(static, observed_, replay):
    n = [0]

    def ok(c, m):
        n[0] += 1
        if not c:
            raise AssertionError(m)

    d = static["dispatcher"]["bit_to_handler"]
    ok(d == {"7": "0x2C17", "6": "0x2B6D", "5": "0x2B77", "4": "0x2B9F", "3": "0x2BC3", "2": "0x2C0D"}, "dispatcher table")
    ok(static["handlers"]["opening"]["d292_edits_in_code_order"] == ["RES 7", "RES 5", "RES 7", "SET 4"], "opening handler edits")
    ok(static["handlers"]["title"]["d292_edits_in_code_order"] == ["RES 4", "SET 3"], "title handler edits")
    ok(static["opening_routine"]["updates_total"] == OPENING_UPDATES == 30 + 708, "update count")
    lv = static["level"]
    ok(lv["layout"]["width_cells"] == 256 and lv["layout"]["height_cells"] == 8 and lv["layout"]["cells"] == 2048, "layout size")
    ok(lv["palette"]["background_record"] == 40 and lv["palette"]["sprite_record"] == 41, "palette records")
    ok(lv["start_record"]["ram_d511"] == 96 and lv["start_record"]["ram_d514"] == 142, "start anchor")
    ok(len(lv["placement"]) == 1 and lv["placement"][0]["type_id"] == "0x1F" and lv["placement"][0]["world_x"] == 544, "single placement")
    a = static["actors"]
    ok(a["player_state_29"]["scripts_identical"], "Sonic and Tails share the state-$29 script")
    ok(a["window_table"]["counts"] == {"0": 256, "1": 144, "2": 384, "3": 240}, "window table")
    ok(static["mapping"]["machine_type_1F"]["frames"]["3"]["piece_count"] == 17, "machine frame 3 has 17 pieces")
    ok(sorted(static["mapping"]["tails_type_2_frames_used"]["frames"], key=int) == ["1", "2", "3", "4", "5", "6"], "Tails walk frames 1..6")
    ok(all(f["tile_source"]["tiles"] >= 10 for f in static["mapping"]["tails_type_2_frames_used"]["frames"].values()), "Tails tile sources")
    cols = replay["columns"]
    ok(cols == REPLAY_COLUMNS, "replay columns")
    rows = replay["rows"]
    ok(len(rows) == OPENING_UPDATES and [r[0] for r in rows] == list(range(OPENING_UPDATES)), "replay length")
    c = {nme: i for i, nme in enumerate(cols)}
    ok(all(rows[u][c["actor_x"]] - rows[u - 1][c["actor_x"]] == 6 for u in range(2, 661)), "Sonic moves 6 px per update from update 1 to 660")
    ok(rows[661][c["actor_type"]] == 2 and rows[660][c["actor_type"]] == 1, "character switch at update 661")
    ok(all(rows[u][c["cam_x"]] == 3578 for u in range(601, OPENING_UPDATES)), "camera frozen at 3578 from update 601")
    ok(rows[40][c["machine_type"]] == 0x1F and rows[39][c["machine_type"]] == 0, "machine created at update 40")
    states = []
    for r in rows:
        if r[c["machine_type"]] and (not states or states[-1][0] != r[c["machine_state"]]):
            states.append((r[c["machine_state"]], r[0]))
    ok(states == [(0, 40), (1, 43), (2, 66), (3, 113), (4, 486), (5, 536)], "machine state timeline %r" % (states,))
    m = observed_["model_vs_observed"]
    ok(m["rows"] == OPENING_UPDATES and m["mismatching_columns"] == {}, "model equals observation")
    cc = observed_["compose_check"]
    ok(cc["bg_mismatch_pixels"] == 0 and cc["sprite_mismatch_pixels"] == 0 and cc["frames_checked"] >= 150, "composed layers equal the emulator's")
    ok(cc["r8_follows_d174_plus_1_everywhere"], "R8 follows D174+1")
    ok(observed_["fade"]["observed_equals_model"], "fade steps equal the U4 fade model")
    t = observed_["timeline_frames"]
    ok(t["first_update_frame"] == 81 and t["last_update_frame"] == 818, "first/last update frames")
    cx = observed_["census"]
    ok(cx["demo_zones_in_order"] == [0, 1, 2] and cx["first_cycle_frames"]["opening"] == 871 and cx["first_cycle_frames"]["title"] == 1310, "census")
    ok(observed_["sounds"][0]["request"] == 0x90, "music request $90")
    return n[0]


def write_all(rom, only=None, poc=None, progress=print):
    DATA.mkdir(parents=True, exist_ok=True)
    out = {}
    st = build_static(rom)
    out[STATIC_JSON] = dumps(st)
    progress("static layer done")
    model = model_opening()
    replay = build_replay(model)
    out[REPLAY_JSON] = dumps(replay)
    if only != "static":
        ob = build_observed(rom, progress)
        out[OBS_JSON] = dumps(ob)
        out[CENSUS_JSON] = dumps({"rom_sha256": ROM_SHA256, "research_base": BASE_COMMIT, **ob["census"], "alternatives": ALTERNATIVES})
        progress("observed layer done; validation assertions: %d" % validate(st, ob, replay))
        manifest = export_all(rom, poc)
        out[EXPORT_JSON] = dumps({"rom_sha256": ROM_SHA256, **manifest, "note": "ROM-derived PNGs live in the ignored build/u5a/opening; regenerate with this tool"})
    return out


ALTERNATIVES = [
    {"id": "A1", "name": "Opening cinematic", "d292_bit": 5, "routine": "$06C7 (via handler $2B77)", "present": True, "evidence": "STATIC + OBSERVED (this package)",
     "what": "zone 7 act 0 run by the ordinary level engine: Sonic runs right, a flying machine (type $1F) dives in, hovers ahead of him and leaves; Tails follows; 738 updates (871 harness frames from power-on to the title flag)", "pc_poc": "none"},
    {"id": "A2", "name": "Title screen", "d292_bit": 4, "routine": "$0719 (handler $2B9F)", "present": True, "evidence": "STATIC + observed frames",
     "what": "Sonic and Tails logo, SONIC CHAOS, (c) 1993 SEGA, blinking PRESS START BUTTON, sound requests $BE/$BF/$99; 1,310 harness frames; owned by earlier title work (PRES-FOLLOWUP-1 / G5)", "pc_poc": "ROM_menu_title (accepted, visibly 4:3)"},
    {"id": "A3", "name": "Attract demo", "d292_bit": 3, "routine": "$2BC3 / $2C34", "present": True, "evidence": "STATIC + observed zone sequence",
     "what": "three rotating recorded runs THZ1 (Sonic), GPZ1 (Tails), SEZ1 (Sonic); recorded input pointers in the ROM (region-dependent table D12D); 1,080 updates each (1,230 harness frames)", "pc_poc": "none"},
    {"id": "A4", "name": "Act title card", "d292_bit": None, "routine": "$3175", "present": True, "evidence": "U4-A (docs/u4-ordinary-results.md section 8)",
     "what": "zone name and act number cards between results and gameplay - NOT an opening", "pc_poc": "implemented in G1-C"},
    {"id": "A5", "name": "Sega logo / licence screen", "d292_bit": None, "routine": None, "present": False, "evidence": "OBSERVED: harness frames 1-80 are black, no logo tiles or text are loaded before the scene",
     "what": "absent from this ROM", "pc_poc": "OBJ_menu_opening / SPR_opening_sega (inherited openSonicSMS art)"},
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--only", choices=("static", "all"), default="all")
    ap.add_argument("--poc", type=Path)
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.validate:
        print("validate: %d assertions" % validate(load_json(STATIC_JSON), load_json(OBS_JSON), load_json(REPLAY_JSON)))
        return
    if a.rom is None:
        ap.error("ROM path required")
    rom = load_rom(a.rom)
    out = write_all(rom, None if a.only == "all" else "static", a.poc)
    if a.check:
        bad = [str(p.relative_to(ROOT)) for p, t in out.items() if p.read_text(encoding="utf-8") != t]
        if bad:
            raise SystemExit("MISMATCH: " + ", ".join(bad))
        print("u5a opening: committed data match the ROM-derived regeneration")
        return
    for p, t in out.items():
        p.write_text(t, encoding="utf-8")
        print("wrote", p.relative_to(ROOT), len(t))


if __name__ == "__main__":
    main()

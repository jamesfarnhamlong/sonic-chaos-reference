#!/usr/bin/env python3
"""U4-B: original TIME OVER, Continue and Game Over presentation (Sonic Chaos SMS, Europe v1.2).

    python tools/u4b_screens.py ROM                 # regenerate data/u4b/*.json and the ignored exports in build/u4b/
    python tools/u4b_screens.py ROM --check         # recompute everything and compare with the committed JSON
    python tools/u4b_screens.py ROM --only static   # static census and exports only (no emulation, a few seconds)
    python tools/u4b_screens.py --validate          # no ROM: internal consistency of the committed JSON

Layers (every field of the output belongs to exactly one):

* ``static``  - DECODED DATA / BYTE-VERIFIED ASSEMBLY read straight from ROM bytes: routine regions, the two compressed tile streams, the
                tilemap blocks and digit glyph table, palette records, wait-loop immediates, sound-request operands, player animation scripts,
                player mapping and tile-transfer sources.  Operands of the draw / palette / loader routines are *parsed from the code bytes*.
* ``compose`` - a Python re-composition of each screen (name table + sprites + palette) from the static layer alone.
* ``observe`` - EMULATED ORIGINAL FRAME runs (tools/g0_rig.py, approximate VDP, cycle-driven Z80, NTSC frame timing).  The composition is compared
                with the emulated VRAM / CRAM / SAT and rendered pixels; every timing is a harness measurement (+/-1 frame).
* ``adapter`` - nothing: this package contains no GameMaker/POC notes that change ROM facts.

No ROM byte, tile pixel or palette is committed except small decoded numeric tables of the kind earlier Research caches already commit
(name-table entries, palette colour bytes, glyph tile ids).  Tile pixels, composed frames and sprite frames are exported to the ignored ``build/u4b``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import tile_decompress as TD  # noqa: E402
import u4_results as U  # noqa: E402
import thz1_object_assets as A  # noqa: E402

ROM_SHA256 = U.ROM_SHA256
BASE_COMMIT = "fdfe8effcf1c03d5ffd621d47c81f56038c5aeb7"
DATA = ROOT / "data" / "u4b"
BUILD = ROOT / "build" / "u4b"
STATIC_JSON = DATA / "death-screens-static.json"
OBS_JSON = DATA / "death-screens-observed.json"
MANIFEST_JSON = DATA / "export-manifest.json"
DOC = ROOT / "docs" / "u4b-time-over-continue-game-over.md"

hx, sha, off, u16, load_rom, dumps, load_json = U.hx, U.sha, U.off, U.u16, U.load_rom, U.dumps, U.load_json
BANK_PALETTE = U.BANK_PALETTE
PAL_BASE = 0xB64D        # bank 14 palette record table, 16 colour bytes per record
RES_SMS = 0xDE04         # sound request mailbox


# ------------------------------------------------------------------------------------------------------------------------------------------
# Routine regions
# (name, bank, start, end_exclusive, role)
ROUTINES = [
    ("timer_update", None, 0x27EE, 0x2885, "clock tick: seconds/minutes BCD, 10:00 sets D44B := $C0 and stops the clock (D2BE := 0), special-stage countdown branch at $2826"),
    ("player_update", None, 0x361D, 0x3657, "per-update player entry; D44B bit 6 calls the death routine $4984 (TIME OVER) before the engine update"),
    ("death_routine", None, 0x4984, 0x49C3, "player death: state $1F, D293 bit 2, keeps D44B bit 7, requests sound $96 (zone < 8)"),
    ("life_lost_branch", None, 0x15F2, 0x1673, "main-loop D293 bit 2: lives -1 at once, death animation loop, fade slots, TIME OVER gate, lives test, reload or last-life branch"),
    ("game_over_branch", None, 0x138A, 0x13C9, "main-loop D293 bit 6 clear: clears, $13ED continue test, Game Over screen + sound $87, waits, fade, title"),
    ("continue_restore", None, 0x13C9, 0x13ED, "continue accepted: lives 3 (type 1) / 5, score := 0, D293 reload flags, back to the main loop"),
    ("continue_screen", None, 0x13ED, 0x1464, "continue test (D2C3 bit 7 cleared), object init, screen draw, sound $94, 16+30 frame set-up, fade-in requests, countdown call, exit fade"),
    ("continue_countdown", None, 0x1464, 0x148C, "frame wait, player update, button test D147 & $30, 116-update digit, digit redraw, sound $B4, expiry"),
    ("continue_accept", None, 0x148C, 0x14AB, "accept: sound $A0, D2C3 -1 with bit 7 set, D526 := $FF (player run script), 180-update wait"),
    ("game_over_screen", None, 0x3436, 0x345B, "tile load (bank 19 stream $B5AF), 3x17 GAME OVER block, fade-in requests (BG record $22, sprite record 7)"),
    ("continue_draw", None, 0x345B, 0x3478, "tile load (same stream), 3x15 CONTINUE block and 2x6 digit/star frame"),
    ("continue_digit_draw", None, 0x3478, 0x3495, "bank 19 page, 1x2 digit glyph from the table at $BF9D + 4*digit"),
    ("time_over_screen", None, 0x3495, 0x34D3, "clears, tile load (bank 16 stream $8A70), 4x17 TIME OVER block, fade-in (BG record $23), 180-wait, fade out, 90-wait, D44B := 0"),
    ("time_over_loader", None, 0x7A28, 0x7A3C, "bank $10, VRAM $1800, tile stream $8A70 through the $24C2 decoder"),
    ("game_over_loader", None, 0x7A50, 0x7A64, "bank $13, VRAM $1800, tile stream $B5AF through the $24C2 decoder"),
    ("blit_2byte", None, 0x2349, 0x2383, "B rows x C columns of 2-byte name-table cells from DE to the name table at HL (wraps at $3F00 -> $3800)"),
    ("blit_address_adjust", None, 0x23C7, 0x23F7, "adds the camera scroll (D174/D176) to the name-table address; zero after $4FCE"),
    ("input_edge_detect", None, 0x2451, 0x2496, "per interrupt: D137 current (pressed = 1), D147/D157 = newly pressed this interrupt (bit 6 masked), history shift"),
    ("frame_wait", None, 0x062D, 0x063C, "EI; waits for the interrupt to set D135, clears it"),
    ("sound_regs", None, 0x18E1, 0x18ED, "DE09..DE0B := 12,1,2 (music fade parameters)"),
    ("fade_slot_reset", None, 0x1CAF, 0x1CBD, "D492/D494 := bit 6 only (fade to black)"),
    ("name_table_clear", None, 0x21DA, 0x220E, "frame wait, name table $3800 x $380 words := $00C0 (LD DE,$00C0), VRAM $1800 x 32 bytes := 0, SAT buffer Y := $F0"),
    ("try_again_screen_out_of_scope", None, 0x34D3, 0x3522, "ending TRY AGAIN card (sound $98, 1-byte cells D2D3 := 0); outside this task, listed so it is not mistaken for Game Over"),
    ("player_state35_callback_sonic", 12, 0x8933, 0x8946, "continue-screen idle callback (type 1): D526 == $FF switches the script to the run records"),
    ("player_state35_run_callback", 12, 0x8946, 0x895A, "run callback: $0338 movement, X speed (+$16/$17) += $0010 per update"),
    ("player_state35_callback_tails", 12, 0x8ECE, 0x8EE1, "continue-screen idle callback (type 2)"),
]

# Wait loops: (name, address of the `LD B,n` immediate); every iteration is one `$062D` frame wait unless noted
WAIT_SITES = [
    ("death_animation_end_wait", 0x1637), ("death_after_fade_wait", 0x164B),
    ("time_over_hold", 0x34B8), ("time_over_after_fade_wait", 0x34C6),
    ("game_over_hold_1", 0x13A8), ("game_over_hold_2", 0x13B0), ("game_over_fade_wait", 0x13BE),
    ("continue_setup_updates", 0x1425), ("continue_after_fade_request", 0x1445), ("continue_accept_hold", 0x149E), ("continue_exit_fade_wait", 0x145B),
]

SPRITE_PALETTE_RECORD = 7


# ------------------------------------------------------------------------------------------------------------------------------------------
# Code-byte parsers
def code_range(rom, a, b):
    return bytes(rom[a:b])


def find_all(rom, pattern, a, b):
    out = []
    p = bytes(pattern)
    i = a
    while True:
        i = rom.find(p, i, b)
        if i < 0:
            return out
        out.append(i)
        i += 1


def parse_loader(rom, a, name):
    """`DI; LD A,bank; CALL $1C6F; LD HL,vram; CALL $1D50; LD HL,src; XOR A; CALL $24C2; RET` read from the code bytes."""
    b = rom[a:a + 0x14]
    ok = (b[0] == 0xF3 and b[1] == 0x3E and b[3:6] == b"\xCD\x6F\x1C" and b[6] == 0x21 and b[9:12] == b"\xCD\x50\x1D" and b[12] == 0x21
          and b[15] == 0xAF and b[16:19] == b"\xCD\xC2\x24" and b[19] == 0xC9)
    if not ok:
        raise ValueError("loader %s at $%04X does not have the expected shape" % (name, a))
    bank, vram, src = b[2], b[7] | b[8] << 8, b[13] | b[14] << 8
    o = off(bank, src)
    dec = TD.decompress_tile_stream(rom, o)
    count = u16(rom, o + 2)
    cmd = o + u16(rom, o + 4)
    ptr = o + 6
    for i in range(count):
        c = TD.extract_command(rom, cmd, i)
        if c == 1:
            ptr += 32
        elif c in (2, 3):
            _, ptr = TD._expand_sparse_tile(rom, ptr)
    end = max(ptr, cmd + (count + 3) // 4)
    return dict(id=name, loader_cpu=hx(a, 4), bank=bank, bank_register_writer="CALL $1C6F (D12B + $FFFF)", vram_destination=hx(vram, 4), first_tile_index=vram // 32,
                source_cpu=hx(src, 4), file_start=hx(o, 5), header=bytes(rom[o:o + 6]).hex(), tile_count=count, stream_file_end_exclusive=hx(end, 5),
                stream_sha256=sha(rom[o:end]), decoded_length=len(dec), decoded_sha256=sha(dec),
                tile_sha256=[sha(dec[i * 32:(i + 1) * 32]) for i in range(count)], decoder="$24C2 with A = 0 (no $0100 remap)"), dec


def parse_blits(rom, a, b):
    """Every `LD HL,nt; LD BC,rows*256+cols; LD DE,src; CALL $2349` in [a,b) (B = rows, C = columns)."""
    out = []
    for i in range(a, b - 11):
        if rom[i] == 0x21 and rom[i + 3] == 0x01 and rom[i + 6] == 0x11 and rom[i + 9:i + 12] == b"\xCD\x49\x23":
            nt = rom[i + 1] | rom[i + 2] << 8
            out.append(dict(call_site=hx(i + 9, 4), nt_address=hx(nt, 4), row=(nt - 0x3800) >> 6, col=(nt & 0x3F) >> 1, cols=rom[i + 4], rows=rom[i + 5],
                            source_cpu=hx(rom[i + 7] | rom[i + 8] << 8, 4)))
    return out


def parse_fade_requests(rom, a, b):
    """`LD HL,D492|D494; LD (HL),flags; [SET 7,(HL)]; INC HL; LD (HL),record` in [a,b)."""
    out = []
    for i in range(a, b - 10):
        if rom[i] == 0x21 and rom[i + 2] == 0xD4 and rom[i + 1] in (0x92, 0x94) and rom[i + 3] == 0x36:
            flags = rom[i + 4]
            j = i + 5
            if rom[j:j + 2] == b"\xCB\xFE":
                flags |= 0x80
                j += 2
            if rom[j] == 0x23 and rom[j + 1] == 0x36:
                out.append(dict(site=hx(i, 4), slot="D492 (background)" if rom[i + 1] == 0x92 else "D494 (sprite)", flags=hx(flags), record=rom[j + 2],
                                meaning={0x80: "fade in from black (bit 7 only)", 0x00: "none"}.get(flags, "flags " + hx(flags))))
    return out


def parse_sound_requests(rom, a, b):
    """`LD A,n; LD (DE04),A` in [a,b)."""
    out = []
    for i in range(a, b - 5):
        if rom[i] == 0x3E and rom[i + 2:i + 5] == b"\x32\x04\xDE":
            out.append(dict(value=hx(rom[i + 1]), store_cpu=hx(i + 2, 4)))
    return out


def read_cells(rom, bank, cpu, n):
    o = off(bank, cpu)
    return [rom[o + 2 * i] | rom[o + 2 * i + 1] << 8 for i in range(n)]


def cell_fields(w):
    return dict(tile=w & 0x1FF, hflip=bool(w & 0x200), vflip=bool(w & 0x400), palette=1 if w & 0x800 else 0, priority=bool(w & 0x1000))


def wait_loops(rom):
    out = {}
    for name, a in WAIT_SITES:
        if rom[a] != 0x06:
            raise ValueError("expected LD B,n at $%04X" % a)
        out[name] = dict(address=hx(a, 4), iterations=rom[a + 1])
    return out


# ------------------------------------------------------------------------------------------------------------------------------------------
# Screens
SCREENS = {
    # id: (blit routine range, loader, bank of the map source)
    "game_over": dict(routine=(0x3436, 0x345B), loader=0x7A50, stream="gameover_continue"),
    "continue": dict(routine=(0x345B, 0x3478), loader=0x7A50, stream="gameover_continue"),
    "time_over": dict(routine=(0x3495, 0x34D3), loader=0x7A28, stream="time_over"),
}
STREAM_LOADERS = dict(gameover_continue=0x7A50, time_over=0x7A28)
MAP_BANK = dict(game_over=0x13, continue_=0x13, time_over=0x10)


def static_census(rom):
    streams, decoded = {}, {}
    for sid, a in STREAM_LOADERS.items():
        streams[sid], decoded[sid] = parse_loader(rom, a, sid)
    # the continue-screen digit routine pages bank 19 itself (`LD A,$13; CALL $1C6F` at $3478)
    if rom[0x3479:0x347B] != b"\x3E\x13":
        raise ValueError("digit routine bank immediate changed")
    screens = {}
    blits_go = parse_blits(rom, 0x3436, 0x345B)
    blits_co = parse_blits(rom, 0x345B, 0x3478)
    blits_to = parse_blits(rom, 0x3495, 0x34D3)
    for sid, blits, bank in (("game_over", blits_go, 0x13), ("continue", blits_co, 0x13), ("time_over", blits_to, 0x10)):
        for b in blits:
            n = b["cols"] * b["rows"]
            cells = read_cells(rom, bank, int(b["source_cpu"], 16), n)
            b["bank"] = bank
            b["file_start"] = hx(off(bank, int(b["source_cpu"], 16)), 5)
            b["cells"] = cells
            b["cells_sha256"] = sha(bytes(x for c in cells for x in (c & 255, c >> 8)))
        screens[sid] = dict(blocks=blits)
    # digit routine: `LD HL,$BF9D` base, `LD HL,$3AE0` destination, `LD BC,$0201`
    d = bytes(rom[0x3478:0x3495])
    if b"\x21\x9D\xBF" not in d or b"\x21\xE0\x3A\x01\x01\x02" not in d:
        raise ValueError("digit routine operands changed")
    digits = []
    for dgt in range(10):
        cells = read_cells(rom, 0x13, 0xBF9D + 4 * dgt, 2)
        digits.append(dict(digit=dgt, top=cells[0], bottom=cells[1], source_cpu=hx(0xBF9D + 4 * dgt, 4)))
    screens["continue"]["digit_draw"] = dict(nt_address="3AE0", row=11, col=16, cols=1, rows=2, table_cpu="BF9D", stride_bytes=4, bank=0x13,
                                             index="D2CB (9 first drawn by the 2x6 block, 8..0 drawn by $3478)", glyphs=digits)
    # palette requests
    fades = {"game_over": parse_fade_requests(rom, 0x3436, 0x345B), "continue": parse_fade_requests(rom, 0x13ED, 0x1464),
             "time_over": parse_fade_requests(rom, 0x3495, 0x34D3)}
    recs = {}
    for lst in fades.values():
        for f in lst:
            n = f["record"]
            o = off(BANK_PALETTE, PAL_BASE + 16 * n)
            recs[str(n)] = dict(cpu=hx(PAL_BASE + 16 * n, 4), file_start=hx(o, 5), sms_colours=list(rom[o:o + 16]), sha256=sha(rom[o:o + 16]))
    sounds = {k: parse_sound_requests(rom, a, b) for k, (a, b) in dict(
        death_routine=(0x4984, 0x49C3), game_over_branch=(0x138A, 0x13C9), continue_screen=(0x13ED, 0x1464), continue_countdown=(0x1464, 0x148C),
        continue_accept=(0x148C, 0x14AB), time_over_screen=(0x3495, 0x34D3), life_lost_branch=(0x15F2, 0x1673)).items()}
    return dict(
        format=1, rom_sha256=ROM_SHA256, base_commit=BASE_COMMIT,
        routines=[U.region(rom, n, b if b is not None else 0, a, e, r) for n, b, a, e, r in ROUTINES],
        tile_streams=streams, screens=screens, fade_requests=fades, palette_records=recs, sound_requests=sounds,
        wait_loops=wait_loops(rom),
        name_table_fill=dict(site="$21DA LD DE,$00C0 ... CALL $1D8A (BC = $0380 words at $3800); then VRAM $1800 x 32 bytes := 0", word=u16(rom, 0x21DB), words=u16(rom, 0x21E5),
                             tile_cleared_vram=hx(u16(rom, 0x21EB), 4), cleared_bytes=u16(rom, 0x21EE), sat_y_fill=hx(rom[0x2200]),
                             note="every cell not drawn by a block holds tile 192; both new tile streams are then loaded at VRAM $1800, so tile 192 is stream tile 0"),
        countdown=dict(initial_digit=rom[0x13FA], initial_digit_site="$13F9 LD A,9", ticks_per_digit_compare=rom[0x1477], compare_site="$1476 CP $74",
                       expiry_compare=rom[0x1480], expiry_site="$147F CP $FF after DEC (D2CB)", digit_redraw_call="$1482", tick_sound=hx(rom[0x1486]), tick_sound_site="$1487",
                       accept_button_mask=hx(rom[0x146E]), accept_test_site="$146A LD A,(D147); AND $30; JR NZ,$148C", accept_sound=hx(rom[0x148D]), accept_sound_site="$148E",
                       music_request=hx(rom[0x141C]), music_site="$141D"),
        player_object=dict(type_source="D2C8 -> D500 at $1405 (1 = Sonic, 2 = Tails)", state=hx(rom[0x140B]), requested_state=hx(rom[0x140F]), x_word_low=hx(rom[0x1413]),
                           y_word_low=hx(rom[0x1417]), x_site="$1410 LD (IX+$11),$80", y_site="$1414 LD (IX+$14),$A0",
                           accept_flag="D526 := $FF at $149B read by the state-$35 callback"),
        lives_restore=dict(sonic=rom[0x13CD], other=rom[0x13D2], site="$13CC LD B,3 / $13D1 LD B,5 selected by D2C8 DEC (type 1 -> 3)"),
        time_over_trigger=dict(site="$281C LD A,$C0 : LD (D44B),A", d44b_value=hx(rom[0x281D]), minutes_compare=hx(rom[0x2818]), note="minutes BCD after +1 minus $10 == 0 -> 10:00; stops the clock D2BE := 0"),
    ), decoded


def streams_overlap(rom, st):
    """Shared tile content between the three new screens' streams and the already-decoded U4 streams."""
    sets = {}
    for sid, s in st["tile_streams"].items():
        sets[sid] = s["tile_sha256"]
    u4 = load_json(ROOT / "data" / "u4" / "ordinary-results-static.json")
    sets["u4_results_160"] = u4["tile_stream"]["tile_sha256"]
    tp = u4["act_title_card"]["tile_stream"]
    if "tile_sha256" in tp:
        sets["u4_act_title"] = tp["tile_sha256"]
    blank = sha(bytes(32))
    out = {}
    names = list(sets)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = sorted((set(sets[a]) & set(sets[b])) - {blank})
            out["%s__%s" % (a, b)] = dict(shared_non_blank_tiles=len(shared), a_tiles=len(sets[a]), b_tiles=len(sets[b]))
    out["blank_tile_present"] = {k: blank in v for k, v in sets.items()}
    return out


# ------------------------------------------------------------------------------------------------------------------------------------------
# Player art (Continue screen sprite)
def parse_simple_script(rom, cpu):
    """Records `duration, frame, callback lo, hi` ending in `FF 07 target` (the only forms the continue scripts use)."""
    o = off(12, cpu)
    recs, p = [], o
    while True:
        if rom[p] == 0xFF:
            if rom[p + 1] != 0x07:
                raise ValueError("unexpected command FF %02X at $%04X" % (rom[p + 1], cpu))
            return recs, 0x8000 + ((rom[p + 2] | rom[p + 3] << 8) - 0x8000), hx(0x8000 + (p - o) + cpu - 0x8000, 4)
        recs.append(dict(updates=rom[p], frame=rom[p + 1], callback=hx(rom[p + 2] | rom[p + 3] << 8, 4)))
        p += 4


def player_art(rom):
    out = {}
    for ptype, idle_cpu in ((1, 0x8913), (2, 0x8EB2)):
        idle, idle_jump, _ = parse_simple_script(rom, idle_cpu)
        cb_o = off(12, idle[0]["callback"] and int(idle[0]["callback"], 16))
        # the idle callback loads the accepted-branch cursor: `LD HL,xxxx` at callback + 5
        accept_cpu = rom[cb_o + 6] | rom[cb_o + 7] << 8
        if rom[cb_o + 5] != 0x21:
            raise ValueError("idle callback shape changed")
        run, run_jump, _ = parse_simple_script(rom, accept_cpu)
        mapping = A.object_mapping(rom, ptype)
        pointers = A.mapping_frame_pointers(rom, mapping["mapping_cpu"], 128)
        table = 0x104B if ptype == 1 else 0x11CF
        frames = {}
        for f in sorted({r["frame"] for r in idle + run}):
            parsed = A.parse_frame_record(rom, pointers[f])
            e = table + f * 4
            bank, cpu, blocks = rom[e], u16(rom, e + 1), rom[e + 3]
            src = bank * 0x4000 + cpu - 0x8000
            raw = rom[src:src + blocks * 64]
            frames[str(f)] = dict(frame=f, mapping_frame_cpu=hx(pointers[f], 4), mapping_frame_rom=hx(parsed["frame_rom"], 5), piece_count=parsed["piece_count"],
                                  y_origin=parsed["y_origin"], x_origin=parsed["x_origin"], pieces=[dict(rel_x=p["relative_x"], rel_y=p["relative_y"], tile_offset=p["tile_offset"]) for p in parsed["pieces"]],
                                  tile_table_entry_rom=hx(e, 5), tile_source_bank=bank, tile_source_cpu=hx(cpu, 4), tile_source_rom=hx(src, 5), transfer_blocks_64=blocks,
                                  tile_count=len(raw) // 32, tile_sha256=sha(raw), vram_destination="0000")
        out[str(ptype)] = dict(type=ptype, name="Sonic" if ptype == 1 else "Tails", state=0x35, idle_script_cpu=hx(idle_cpu, 4), idle_script_file=hx(off(12, idle_cpu), 5), idle=idle,
                               idle_loops_to=hx(idle_jump, 4), accept_script_cpu=hx(accept_cpu, 4), accept_run=run, accept_loops_to=hx(run_jump, 4), run_callback=run[0]["callback"],
                               mapping_table_cpu=hx(mapping["mapping_cpu"], 4), tile_table_cpu=hx(table, 4), sprite_palette_record=SPRITE_PALETTE_RECORD, frames=frames)
    return out


def player_frame_tiles(rom, art, ptype, frame):
    fr = art[str(ptype)]["frames"][str(frame)]
    src = int(fr["tile_source_rom"], 16)
    return bytes(rom[src:src + fr["transfer_blocks_64"] * 64])


# ------------------------------------------------------------------------------------------------------------------------------------------
# Composition
FIRST_BG_TILE = 192


def compose_name_table(st, screen, digit=None):
    """24x32 grid of name-table words for a screen (the `$21DA` fill word elsewhere)."""
    fill = st["name_table_fill"]["word"]
    nt = [[fill] * 32 for _ in range(24)]
    for b in st["screens"][screen]["blocks"]:
        for i, w in enumerate(b["cells"]):
            nt[b["row"] + i // b["cols"]][b["col"] + i % b["cols"]] = w
    if screen == "continue" and digit is not None:
        g = st["screens"]["continue"]["digit_draw"]["glyphs"][digit]
        nt[11][16], nt[12][16] = g["top"], g["bottom"]
    return nt


def render_bg(nt, tiles, first_tile):
    """192x256 palette indices (BG palette 0..15, sprite palette select +16) of a name table whose tiles all come from the loaded stream."""
    img = [[0] * 256 for _ in range(192)]
    for ty in range(24):
        for tx in range(32):
            w = nt[ty][tx]
            k = (w & 0x1FF) - first_tile
            if not 0 <= k < len(tiles):
                raise ValueError("tile %d outside the loaded stream" % (w & 0x1FF))
            px = tiles[k]
            pal = 16 if w & 0x0800 else 0
            hf, vf = w & 0x200, w & 0x400
            for r in range(8):
                src = px[7 - r if vf else r]
                for x in range(8):
                    img[ty * 8 + r][tx * 8 + x] = pal + src[7 - x if hf else x]
    return img


def sprite_layer(art, rom, ptype, frame, x, y):
    """Expected SAT entries and the 8-sprites-per-line-limited sprite index layer for one player frame at screen position (x, y).

    SAT Y byte = screen Y + relative Y (the VDP draws the sprite one line lower), X = screen X + relative X, pattern = tile base 0 + tile offset
    (8x16 sprites): the formula is *verified* against the emulated SAT in the observed layer."""
    fr = art[str(ptype)]["frames"][str(frame)]
    raw = player_frame_tiles(rom, art, ptype, frame)
    tiles = U.tiles_from_decoded(raw)
    sat = []
    layer = [[None] * 256 for _ in range(192)]
    per_line = [0] * 192
    for p in fr["pieces"]:
        sy, sx, n = (y + p["rel_y"]) & 0xFF, (x + p["rel_x"]) & 0xFF, p["tile_offset"]
        sat.append([sy, sx, n])
        top = sy + 1
        for r in range(16):
            ly = top + r
            if not 0 <= ly < 192 or per_line[ly] >= 8:
                continue
            per_line[ly] += 1
            row = tiles[n + (r >> 3)][r & 7]
            for c in range(8):
                lx = sx + c
                if 0 <= lx < 256 and row[c] and layer[ly][lx] is None:
                    layer[ly][lx] = 16 + row[c]
    return sat, layer


def compose_frame(st, art, rom, decoded, screen, digit=None, ptype=None, frame=None, pos=(128, 160)):
    sid = "gameover_continue" if screen != "time_over" else "time_over"
    tiles = U.tiles_from_decoded(decoded[sid])
    nt = compose_name_table(st, screen, digit)
    bg = render_bg(nt, tiles, FIRST_BG_TILE)
    layer = None
    sat = []
    if ptype is not None:
        sat, layer = sprite_layer(art, rom, ptype, frame, *pos)
    flat = [[(layer[y][x] if layer is not None and layer[y][x] is not None else bg[y][x]) for x in range(256)] for y in range(192)]
    return dict(nt=nt, bg=bg, sprite=layer, sat=sat, flat=flat)


def screen_palette(st, screen, sprite_visible=True):
    """CRAM (32 bytes) once the screen's fade-in has finished: BG record (and sprite record 7 for Game Over / Continue)."""
    fr = {f["slot"][:4]: f["record"] for f in st["fade_requests"][screen]}
    bg = st["palette_records"][str(fr["D492"])]["sms_colours"]
    spr = st["palette_records"][str(fr["D494"])]["sms_colours"] if "D494" in fr else None
    return bg, spr


# ------------------------------------------------------------------------------------------------------------------------------------------
# Exports (ignored build/u4b)
def rows_hash(rows):
    return sha(bytes((0xFF if v is None else v) for row in rows for v in row))


def block_rows(tiles, cells, cols, rows, first_tile=FIRST_BG_TILE):
    nt = [[0] * cols for _ in range(rows)]
    for i, w in enumerate(cells):
        nt[i // cols][i % cols] = w
    out = [[0] * (cols * 8) for _ in range(rows * 8)]
    for ty in range(rows):
        for tx in range(cols):
            w = nt[ty][tx]
            k = (w & 0x1FF) - first_tile
            pal = 16 if w & 0x0800 else 0
            hf, vf = w & 0x200, w & 0x400
            for r in range(8):
                src = tiles[k][7 - r if vf else r]
                for x in range(8):
                    out[ty * 8 + r][tx * 8 + x] = pal + src[7 - x if hf else x]
    return out


def png_rgba_rows(path, rows, palette32, transparent0=False):
    """Indexed PNG; palette entry 0 of the sprite half is transparent when `transparent0`."""
    from PIL import Image
    h, w = len(rows), len(rows[0])
    im = Image.new("P", (w, h))
    pal = []
    for c in palette32:
        pal.extend(U.sms_rgb(c))
    pal.extend([0] * (768 - len(pal)))
    im.putpalette(pal)
    im.putdata([0 if v is None else v for row in rows for v in row])
    if transparent0:
        im.info["transparency"] = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, optimize=False, compress_level=9, **({"transparency": 0} if transparent0 else {}))


def export_assets(rom, st, decoded, art, out=BUILD):
    man = dict(format=1, rom_sha256=ROM_SHA256, rows_hash="sha256 of the row-major palette-index bytes (0..31; 255 = transparent); never of PNG bytes", assets={})

    def add(name, rows, pal32, kind, note="", transparent0=False):
        png_rgba_rows(out / name, rows, pal32, transparent0)
        man["assets"][name] = dict(kind=kind, width=len(rows[0]), height=len(rows), index_sha256=rows_hash(rows), note=note)

    go_bg, go_sp = screen_palette(st, "game_over")
    co_bg, co_sp = screen_palette(st, "continue")
    to_bg, _ = screen_palette(st, "time_over")
    pal = dict(game_over=go_bg + go_sp, continue_=co_bg + co_sp, time_over=to_bg + [0] * 16)
    # tile sheets
    for sid, key in (("gameover_continue", "game_over"), ("time_over", "time_over")):
        tiles = U.tiles_from_decoded(decoded[sid])
        sheet = [[0] * 128 for _ in range(((len(tiles) + 15) // 16) * 8)]
        for t, px in enumerate(tiles):
            for r in range(8):
                for x in range(8):
                    sheet[(t // 16) * 8 + r][(t % 16) * 8 + x] = px[r][x]
        add("tiles/%s_vram1800.png" % sid, sheet, pal[key], "tile sheet", "%d tiles, 16 per row, tile index = 192 + sheet position; palette indices 0..15" % len(tiles))
    gtiles = U.tiles_from_decoded(decoded["gameover_continue"])
    ttiles = U.tiles_from_decoded(decoded["time_over"])
    for sid, key, tl in (("game_over", "game_over", gtiles), ("continue", "continue_", gtiles), ("time_over", "time_over", ttiles)):
        for i, b in enumerate(st["screens"][sid]["blocks"]):
            add("blocks/%s_block%d.png" % (sid, i), block_rows(tl, b["cells"], b["cols"], b["rows"]), pal[key], "tilemap block",
                "%dx%d cells at row %d col %d; BG palette" % (b["cols"], b["rows"], b["row"], b["col"]))
    strip = [[0] * 80 for _ in range(16)]
    for g in st["screens"]["continue"]["digit_draw"]["glyphs"]:
        col = block_rows(gtiles, [g["top"], g["bottom"]], 1, 2)
        for r in range(16):
            for x in range(8):
                strip[r][g["digit"] * 8 + x] = col[r][x]
    add("blocks/continue_digit_glyphs.png", strip, pal["continue_"], "glyph strip", "digits 0..9, each 8x16 (the 3AE0 cell pair)")
    # composed frames (static only; sprite frames separate)
    add("frames/game_over.png", compose_frame(st, art, rom, decoded, "game_over")["flat"], pal["game_over"], "composed 256x192 frame",
        "name table from the code operands; tile 0 / unused cells = the all-zero tile (verified against the emulator in every zone tried)")
    add("frames/time_over.png", compose_frame(st, art, rom, decoded, "time_over")["flat"], pal["time_over"], "composed 256x192 frame",
        "BG colour 0 is the record's first colour; no sprites")
    for d in range(10):
        add("frames/continue_digit%d.png" % d, compose_frame(st, art, rom, decoded, "continue", d)["flat"], pal["continue_"], "composed 256x192 frame (no sprite)")
    # player sprite frames (indexed, index 0 transparent) and composed continue frames with the character
    for ptype in ("1", "2"):
        for fk, fr in art[ptype]["frames"].items():
            raw = player_frame_tiles(rom, art, int(ptype), int(fk))
            tiles = U.tiles_from_decoded(raw)
            xs = [p["rel_x"] for p in fr["pieces"]]
            ys = [p["rel_y"] for p in fr["pieces"]]
            x0, y0 = min(xs), min(ys)
            w = max(xs) + 8 - x0
            h = max(ys) + 16 - y0
            img = [[None] * w for _ in range(h)]
            for p in fr["pieces"]:
                for r in range(16):
                    row = tiles[p["tile_offset"] + (r >> 3)][r & 7]
                    for c in range(8):
                        if row[c]:
                            img[p["rel_y"] - y0 + r][p["rel_x"] - x0 + c] = 16 + row[c]
            add("sprites/%s_frame%02X.png" % (art[ptype]["name"].lower(), int(fk)), img, [0] * 16 + co_sp, "player frame",
                "sprite palette record 7, index 0 transparent; origin = (%d, %d) from the top-left; sat tile base 0" % (-x0, -y0), transparent0=True)
        idle = art[ptype]["idle"]
        for i, r in enumerate(idle):
            c = compose_frame(st, art, rom, decoded, "continue", 9, int(ptype), r["frame"])
            add("frames/continue_%s_idle%d.png" % (art[ptype]["name"].lower(), i), c["flat"], pal["continue_"], "composed 256x192 frame with the character",
                "digit 9, state-$35 idle frame $%02X at (128,160)" % r["frame"])
    # palettes and fade ramps
    (out).mkdir(parents=True, exist_ok=True)
    ramps = {}
    black = [0] * 16
    for key, (bg, sp) in dict(game_over=(go_bg, go_sp), continue_=(co_bg, co_sp), time_over=(to_bg, None)).items():
        ramps[key] = dict(background_fade_in_from_black=U.fade_series("in_black", black, bg), background_fade_to_black=U.fade_series("to_black", bg),
                          sprite_fade_in_from_black=(U.fade_series("in_black", black, sp) if sp else None), sprite_fade_to_black=(U.fade_series("to_black", sp) if sp else None))
    (out / "palettes.json").write_text(json.dumps(dict(
        note="SMS 2-bit channels %00BBGGRR; rgb = channel * 85 (the accepted harness expansion; hardware DAC levels are an adapter choice)",
        game_over=dict(background=go_bg, sprite=go_sp), continue_=dict(background=co_bg, sprite=co_sp), time_over=dict(background=to_bg),
        ramps=ramps), indent=1, sort_keys=True), encoding="utf-8", newline="\n")
    man["assets"]["palettes.json"] = dict(kind="palettes+ramps", sha256=sha((out / "palettes.json").read_bytes()))
    return man


# ------------------------------------------------------------------------------------------------------------------------------------------
# Observation
def _import_rig():
    import g0_rig
    return g0_rig


class Probe:
    """Per-frame recorder wrapped around a g0_rig Session."""

    MARKS = [(0x15F2, "life_lost_entry"), (0x15FE, "life_decremented"), (0x1653, "time_over_gate"), (0x3495, "time_over_screen"), (0x34CE, "time_over_exit"),
             (0x1661, "lives_check"), (0x166B, "no_lives_left"), (0x1673, "level_reload"), (0x138A, "last_life_branch"), (0x13ED, "continue_test"),
             (0x13F5, "continue_screen"), (0x1418, "continue_draw_call"), (0x1425, "continue_setup_loop"), (0x1431, "continue_fade_request"),
             (0x144D, "continue_countdown_call"), (0x1464, "countdown_iteration"), (0x1482, "digit_redraw"), (0x148C, "continue_accept"),
             (0x1450, "continue_exit"), (0x13C9, "continue_restore"), (0x139D, "game_over_branch"), (0x13A3, "game_over_sound"), (0x13C6, "game_over_to_title"),
             (0x04B4, "title"), (0x2A00, "new_game_reset")]

    def __init__(self, rom, character=0, start=None):
        g = _import_rig()
        self.g = g
        self.rom = rom
        self.S = g.Session(rom)
        self.S.watch("sound")
        for a, n in self.MARKS:
            self.S.mark_pc(a, n)
        if start:
            self.S.set_start_index(*start)
        self.S.boot_new_game(character=character)
        self.S.run(150)
        self.f0 = None
        self.log = []
        self.frames = 0

    def preset(self, **ram):
        for k, v in ram.items():
            self.S.w(k, v)
        self.S.s.w16(0xD44C, 0x0100)

    def snap_state(self):
        s = self.S.s
        m = self.S.m
        allsat = s.sat()
        sat = [[y, x, n] for _, y, x, n in allsat if y < 0xE0]
        parked = sorted({y for _, y, x, n in allsat if y >= 0xE0})
        return dict(cram=bytes(s.cram).hex(), nt=U.nt_hash(U.nt_words(s.vram)), sat=sat, parked=parked, ptiles=sha(bytes(s.vram[0:0x180]))[:12], regs=[s.reg[7], s.reg[8], s.reg[9]],
                    flow=m[0xD293], d44b=m[0xD44B], tick=m[0xD2CA], digit=m[0xD2CB], continues=m[0xD2C3], lives=m[0xD299], score=[m[0xD29F], m[0xD29E], m[0xD29D]],
                    px=self.S.u16(0xD511), py=self.S.u16(0xD514), xspeed=self.S.u16(0xD516), anim=m[0xD50A], state=m[0xD501])

    def run(self, pad_fn, until, limit):
        """Run frames, recording a change log.  `pad_fn(probe, rel, state)` -> pad bits; `until(probe, rel)` -> stop."""
        self.f0 = self.S.s.frame
        prev = {}
        n_writes = len(self.S.writes)
        for i in range(limit):
            rel = self.S.s.frame - self.f0
            st = self.snap_state()
            pad = pad_fn(self, rel, st) if pad_fn else 0
            self.S.s.pad = pad
            self.S.s.run_frame()
            st = self.snap_state()
            st["rel"] = self.S.s.frame - self.f0
            st["pad"] = pad
            ent = {"f": st["rel"]}
            for k in ("cram", "nt", "sat", "parked", "ptiles", "regs", "flow", "d44b", "digit", "continues", "lives", "score", "state", "pad"):
                if prev.get(k) != st[k]:
                    ent[k] = st[k]
            if st["tick"] != prev.get("tick") and st["tick"] == 0:
                ent["tick0"] = True
            snd = [(f - self.f0, v) for f, a, v in self.S.writes[n_writes:] if a == RES_SMS and v]
            n_writes = len(self.S.writes)
            if snd:
                ent["sound"] = [v for _, v in snd]
            self.trace_extra(st, ent)
            if len(ent) > 1:
                self.log.append(ent)
            prev = st
            self.frames += 1
            if until(self, st["rel"]):
                return st["rel"]
        raise RuntimeError("probe limit reached")

    def trace_extra(self, st, ent):
        pass

    def events(self):
        out = {}
        for n, sn in self.S.events:
            if sn["frame"] >= self.f0:
                out.setdefault(n, []).append(sn["frame"] - self.f0)
        return out


def pad_press(pulses):
    """pad_fn pressing button 1 for one frame at each relative frame in `pulses` (a one-interrupt edge)."""
    g = _import_rig()

    def fn(probe, rel, st):
        return g.BTN_1 if rel in pulses else 0
    return fn


# ------------------------------------------------------------------------------------------------------------------------------------------
# Scenarios
def scenario_defs():
    P = lambda **k: k  # noqa: E731
    return [
        P(id="time_over_lives3", kind="time_over", lives=3, continues=0, character=0, stop="reload", note="TIME OVER with lives left: screen, then the same act restarts"),
        P(id="time_over_no_continue_sonic", kind="time_over", lives=1, continues=0, character=0, stop="title", mash=True,
          note="TIME OVER on the last life with no continue: TIME OVER, Game Over, title; a button pulse every 20 frames is ignored"),
        P(id="time_over_continue_expire_sonic", kind="time_over", lives=1, continues=2, character=0, stop="title", capture=True,
          note="TIME OVER, Continue countdown 9..0 unanswered, Game Over, title; full reference capture"),
        P(id="time_over_continue_expire_tails", kind="time_over", lives=1, continues=2, character=1, stop="title", capture=True, note="same with Tails (object type 2)"),
        P(id="time_over_continue_accept_sonic", kind="time_over", lives=1, continues=2, character=0, stop="reload", press=dict(digit=7, tick=10), capture=True,
          note="TIME OVER, Continue accepted at digit 7 (+10 updates), act restarts"),
        P(id="pit_continue_accept_tails", kind="pit", lives=1, continues=3, character=1, stop="reload", press=dict(digit=5, tick=20), capture=True,
          note="pit death on the last life, Continue accepted as Tails"),
        P(id="pit_continue_accept_first_poll", kind="pit", lives=1, continues=2, character=0, stop="reload", press=dict(first_poll=True),
          note="button edge on the first update the countdown loop is polling"),
        P(id="pit_continue_press_before_countdown", kind="pit", lives=1, continues=2, character=0, stop="title", press=dict(setup=True),
          note="button edge during the 16-update set-up loop (before the countdown polls): ignored, the countdown still runs and expires"),
        P(id="pit_continue_button_held", kind="pit", lives=1, continues=2, character=0, stop="title", hold=True,
          note="button 1 held from before the death: no new edge, so the screen is not accepted"),
        P(id="pit_game_over_no_continue_sonic", kind="pit", lives=1, continues=0, character=0, stop="title", capture=True,
          note="pit death on the last life, no continue: Game Over directly, title"),
        P(id="pit_game_over_no_continue_tails", kind="pit", lives=1, continues=0, character=1, stop="title", note="same with Tails"),
    ]


def zone_matrix_defs():
    return [P for P in ({"id": "zone%d_time_over_continue_expire" % z, "kind": "time_over", "lives": 1, "continues": 1, "character": 0, "stop": "title", "start": (z, 0), "zone": z}
                        for z in range(6))]


def boundary_sweep_defs():
    """Button edge relative to the frame the countdown expires (`rel` < 0 = before): accept or expire?"""
    return [{"id": "boundary_%+d" % d, "rel": d} for d in range(-9, 4)]


# ------------------------------------------------------------------------------------------------------------------------------------------
# Running one scenario
def norm_run_state(st):
    return dict(lives_bcd=hx(st["lives"]), continues_raw=hx(st["continues"]), score_bcd="%02X%02X%02X" % tuple(st["score"]), flow=hx(st["flow"]), d44b=hx(st["d44b"]))


def run_scenario(rom, sc, pulses=None, extra_stop=None):
    """Kill the player on a fresh act start (pit: Y + 400, time_over: clock 9:59.59) and follow the ROM until `stop`.

    Fixtures (all RAM, at a frame boundary during play): run state (lives, continues, emeralds, rings, score, power-up) and the death trigger.
    Button input is scripted: pulses are one-interrupt edges of button 1."""
    g = _import_rig()
    probe = Probe(rom, character=sc["character"], start=sc.get("start"))
    S = probe.S
    pre = dict(lives=sc["lives"], continues=sc["continues"], emeralds=0x07, rings=0x23, score0=0x30, score1=0x12, score2=0x00, powerup=0x04)
    probe.preset(**pre)
    before = norm_run_state(probe.snap_state())
    start = dict(zone=S.m[0xD297], act=S.m[0xD298], character_type=S.m[0xD500], player=[S.u16(0xD511), S.u16(0xD514)])
    if sc["kind"] == "pit":
        S.s.w16(0xD514, S.u16(0xD514) + 400)
        fixture = "RAM player Y +400"
    else:
        S.w("timer_min", 0x09)
        S.w("timer_sec", 0x59)
        S.w("timer_ticks", 59)
        fixture = "RAM clock 09:59.59"
    press = sc.get("press") or {}
    state = dict(done=False)
    ev_names = {n: i for i, (_, n) in enumerate(Probe.MARKS)}

    def first(name):
        e = probe.events().get(name)
        return e[0] if e else None

    def pad_fn(pr, rel, st):
        if sc.get("hold"):
            return g.BTN_1
        if sc.get("mash") and rel % 20 == 0:
            return g.BTN_1
        if pulses is not None:
            return g.BTN_1 if rel in pulses else 0
        if not press or state["done"]:
            return 0
        fire = False
        if "digit" in press and st["digit"] == press["digit"] and st["tick"] == press["tick"] and first("continue_countdown_call") is not None:
            fire = True
        if press.get("first_poll") and first("continue_countdown_call") is not None and st["digit"] == 9:
            fire = True
        if press.get("setup") and first("continue_draw_call") is not None and first("continue_countdown_call") is None and rel > first("continue_draw_call") + 3:
            fire = True
        if fire:
            state["done"] = True
            state["press_rel"] = rel
            return g.BTN_1
        return 0
    stop = sc.get("stop")

    def until(pr, rel):
        ev = probe.events()
        if extra_stop and extra_stop(pr, rel, ev):
            return True
        if rel < 5:
            return False
        if stop == "title":
            return "title" in ev
        if stop == "reload":
            return "level_reload" in ev and S.playing() and rel > ev["level_reload"][0] + 100
        raise ValueError(stop)

    cap = CaptureSet(probe) if sc.get("capture") else None
    if cap:
        probe.trace_extra = cap.trace
    probe.run(pad_fn, until, 6000)
    ev = probe.events()
    end = probe.snap_state()
    out = dict(id=sc["id"], note=sc.get("note", ""), kind=sc["kind"], character=sc["character"], fixture=[fixture, "RAM run state " + json.dumps({k: hx(v) for k, v in pre.items()})],
               start=start, before=before, events={k: v for k, v in sorted(ev.items())}, end=norm_run_state(end), frames=probe.frames, press_rel=state.get("press_rel"),
               pulses=sorted(pulses) if pulses else None)
    death = [sn for n, sn in S.events if n == "life_lost_entry" and sn["frame"] >= probe.f0][:1]
    if death:
        d = death[0]
        out["death_snapshot"] = dict(rel=d["frame"] - probe.f0, clock="%02X:%02X.%02d" % (d["timer"][0], d["timer"][1], d["timer"][2]), d44b=hx(d["timeover"]), lives_bcd=hx(d["lives"]),
                                     continues_raw=hx(d["continues"]), player_state=hx(d["player"][1]), zone=d["zone"], act=d["act"])
    sounds = []
    for ent in probe.log:
        for v in ent.get("sound", []):
            sounds.append([ent["f"], hx(v)])
    out["sound_requests"] = sounds
    out["log"] = probe.log
    if cap:
        out["captures"] = cap.results
        out["accept_trace"] = cap.accept_trace
    return out, probe


class CaptureSet:
    """One-shot render captures taken at fixed offsets from the screen events; compared with the static composition by the caller."""

    def __init__(self, probe):
        self.p = probe
        self.results = {}
        self.accept_trace = []
        self._pending = {}
        self._seen = set()

    def want(self, name, rel):
        self._pending[name] = rel

    def trace(self, st, ent):
        p = self.p
        ev = p.events()
        rel = st["rel"]
        S = p.S
        # schedule captures from the events (offsets are inside the steady part of each screen, after the fade-in has finished)
        sched = (("time_over_steady", "time_over_screen", 120), ("game_over_steady", "game_over_sound", 100), ("continue_steady_9", "continue_countdown_call", 60))
        for name, evn, off_ in sched:
            if evn in ev and name not in self._seen:
                self._seen.add(name)
                self._pending[name] = ev[evn][-1] + off_
        if "continue_countdown_call" in ev and ent.get("digit") is not None and st["digit"] < 9 and 0 <= st["digit"] <= 8:
            name = "continue_steady_%d" % st["digit"]
            if name not in self._seen:
                self._seen.add(name)
                self._pending[name] = rel + 10
        for name, at in list(self._pending.items()):
            if rel >= at:
                del self._pending[name]
                self.results[name] = self.grab(rel)
        if "continue_accept" in ev:
            r0 = ev["continue_accept"][-1]
            if rel >= r0 and len(self.accept_trace) < 200 and not (len(self.accept_trace) and self.accept_trace[-1][0] == rel):
                m = S.m
                self.accept_trace.append([rel, S.u16(0xD511), S.u16(0xD516), m[0xD510], m[0xD515], m[0xD526]])

    def grab(self, rel):
        s = self.p.S.s
        rgb, layer, bg, spr = s.render()
        sat = [[y, x, n] for _, y, x, n in s.sat() if y < 0xE0]
        m = self.p.S.m
        return dict(rel=rel, cram=bytes(s.cram).hex(), nt=U.nt_words(s.vram), bg=bg, sprite=spr, sat=sat, regs=list(s.reg[:16]),
                    player=[m[0xD500], m[0xD501], self.p.S.u16(0xD511), self.p.S.u16(0xD514)],
                    vram_tiles=bytes(s.vram[0:0x4000]), tile0=bytes(s.vram[0:32]).hex())


def expected_cram(st, screen, level_sprite_black=True):
    bg, sp = screen_palette(st, screen)
    return bg + (sp if sp is not None else [0] * 16)


def check_capture(rom, st, decoded, art, name, cap, ptype):
    """Compare one emulated frame with the static composition.  Returns the verdict flags."""
    screen = "time_over" if name.startswith("time_over") else "game_over" if name.startswith("game_over") else "continue"
    digit = int(name.rsplit("_", 1)[1]) if screen == "continue" else None
    sid = "time_over" if screen == "time_over" else "gameover_continue"
    nt = compose_name_table(st, screen, digit)
    emu_nt = [row[:] for row in cap["nt"]]
    res = dict(screen=screen, digit=digit, frame_rel=cap["rel"], name_table_equal=emu_nt == nt, name_table_sha256=U.nt_hash(emu_nt))
    tiles = U.tiles_from_decoded(decoded[sid])
    first = FIRST_BG_TILE
    vram = cap["vram_tiles"]
    res["bg_tiles_equal_decoded_stream"] = bytes(vram[first * 32:(first + len(tiles)) * 32]) == bytes(decoded[sid])
    bg = render_bg(nt, tiles, first)
    res["bg_pixels_equal"] = bg == cap["bg"]
    exp_cram = expected_cram(st, screen)
    res["cram_equal"] = bytes.fromhex(cap["cram"]) == bytes(exp_cram)
    res["cram"] = cap["cram"]
    res["visible_sprites"] = len(cap["sat"])
    res["regs"] = dict(r2=cap["regs"][2], r6=cap["regs"][6], r7=cap["regs"][7], r8=cap["regs"][8], r9=cap["regs"][9], r1=cap["regs"][1], r0=cap["regs"][0])
    if screen == "continue" and ptype:
        match = None
        for r in art[str(ptype)]["idle"]:
            sat, layer = sprite_layer(art, rom, ptype, r["frame"], 128, 160)
            raw = player_frame_tiles(rom, art, ptype, r["frame"])
            if sat == cap["sat"] and layer[1:] == cap["sprite"][1:] and bytes(vram[:len(raw)]) == raw:
                match = r["frame"]
        res["sprite_frame_matched"] = match
        res["sat"] = cap["sat"]
        res["player_object"] = cap["player"]
        res["player_object_equal"] = cap["player"] == [ptype, 0x35, 128, 160]
    else:
        res["sprite_layer_empty_below_line0"] = all(v is None for row in cap["sprite"][1:] for v in row)
    row0 = [v for v in cap["sprite"][0] if v is not None]
    res["line0_parking_sprite_pixels"] = len(row0)
    return res


# ------------------------------------------------------------------------------------------------------------------------------------------
# Derived measurements and checks
def dedupe(seq):
    out = []
    for x in seq:
        if not out or out[-1] != x:
            out.append(x)
    return out


def cram_states(out):
    return [(e["f"], e["cram"]) for e in out["log"] if "cram" in e]


def fade_checks(st, out, screen):
    """Every occurrence of the screen's steady palette: the CRAM states that lead to it must be the model's fade-in from black (4 passes, the
    first of which is still black) and the states that follow it the model's fade-to-black (3 passes)."""
    bg, sp = screen_palette(st, screen)
    steady = bytes(bg + (sp if sp else [0] * 16)).hex()
    black = [0] * 16
    pin = dedupe([bytes(b + (s if sp else [0] * 16)).hex() for b, s in zip(U.fade_series("in_black", black, bg), U.fade_series("in_black", black, sp) if sp else [black] * 4)])
    pout = dedupe([bytes(b + (s if sp else [0] * 16)).hex() for b, s in zip(U.fade_series("to_black", bg), U.fade_series("to_black", sp) if sp else [black] * 3)])
    states = cram_states(out)
    res = []
    for i, (f, c) in enumerate(states):
        if c != steady:
            continue
        prev = [x for _, x in states[max(0, i - len(pin) + 1):i + 1]]
        nxt = [x for _, x in states[i + 1:i + 1 + len(pout)]]
        prev_f = [ff for ff, _ in states[max(0, i - len(pin) + 1):i + 1]]
        nxt_f = [ff for ff, _ in states[i + 1:i + 1 + len(pout)]]
        res.append(dict(steady_reached=f, fade_in_matches_model=(prev == pin[len(pin) - len(prev):] and len(prev) == len(pin)), fade_in_state_frames=prev_f,
                        fade_out_matches_model=(nxt == pout), fade_out_state_frames=nxt_f))
    return dict(steady_cram=steady, model_fade_in_visible_states=len(pin), model_fade_out_states=len(pout), occurrences=res)


def sat_intervals(out, lo, hi):
    """Frames between changes of the player tile block (VRAM tiles 0..11 = the animation frame) inside [lo, hi): the sprite animation cadence."""
    fr = [e["f"] for e in out["log"] if "ptiles" in e and lo <= e["f"] < hi]
    return [b - a for a, b in zip(fr, fr[1:])]


def summarize(st, art, rom, decoded, out):
    ev = out["events"]
    res = dict(id=out["id"], note=out["note"], kind=out["kind"], character=out["character"], fixture=out["fixture"], before=out["before"], end=out["end"],
               death_snapshot=out.get("death_snapshot"), start=out["start"],
               events=ev, frames=out["frames"], press_rel=out["press_rel"], sound_requests=out["sound_requests"])
    states = cram_states(out)
    res["cram_states"] = [[f, c] for f, c in states]
    res["name_table_states"] = [[e["f"], e["nt"]] for e in out["log"] if "nt" in e]
    res["d2c3_states"] = [[e["f"], hx(e["continues"])] for e in out["log"] if "continues" in e]
    res["lives_states"] = [[e["f"], hx(e["lives"])] for e in out["log"] if "lives" in e]
    res["score_states"] = [[e["f"], "%02X%02X%02X" % tuple(e["score"])] for e in out["log"] if "score" in e]
    res["pad_edges"] = [e["f"] for e in out["log"] if e.get("pad")]
    if "captures" in out:
        ptype = 1 if out["character"] == 0 else 2
        res["captures"] = {n: check_capture(rom, st, decoded, art, n, c, ptype) for n, c in out["captures"].items()}
        res["accept_trace"] = out.get("accept_trace") or None
        if ev.get("digit_redraw") and ev.get("continue_countdown_call"):
            lo = ev["continue_countdown_call"][0]
            hi = ev["digit_redraw"][-1] if not ev.get("continue_accept") else ev["continue_accept"][0]
            res["idle_frame_change_intervals"] = sat_intervals(out, lo + 5, hi)
            res["parked_sprite_y_values"] = sorted({y for e in out["log"] if "parked" in e for y in e["parked"]})
    screens = []
    if "time_over_screen" in ev:
        screens.append("time_over")
    if "continue_screen" in ev and ev.get("continue_countdown_call"):
        screens.append("continue")
    if "game_over_sound" in ev:
        screens.append("game_over")
    res["fade_checks"] = {sc: fade_checks(st, out, sc) for sc in screens}
    # derived timeline pieces (harness frames, +/-1)
    d = {}
    if "time_over_screen" in ev:
        d["time_over_entry_to_exit"] = ev["time_over_exit"][0] - ev["time_over_screen"][0]
    if ev.get("digit_redraw"):
        dr = ev["digit_redraw"]
        d["digit_redraw_frames"] = dr
        d["digit_intervals"] = [b - a for a, b in zip(dr, dr[1:])]
    if ev.get("continue_countdown_call") and ev.get("continue_exit") and not ev.get("continue_accept"):
        d["countdown_start_to_expiry"] = [e["f"] for e in out["log"] if e.get("digit") == 255][:1]
    if "game_over_sound" in ev and "game_over_to_title" in ev:
        d["game_over_sound_to_title"] = ev["game_over_to_title"][0] - ev["game_over_sound"][0]
    res["derived"] = d
    return res


# ------------------------------------------------------------------------------------------------------------------------------------------
# Observe everything
def sweep(rom, base_sc, label, pulse_rel_fn, deltas, stop_when):
    rows = []
    for d in deltas:
        sc = dict(base_sc, id="%s%+d" % (label, d))
        out, _ = run_scenario(rom, sc, pulses={pulse_rel_fn(d)}, extra_stop=stop_when)
        ev = out["events"]
        rows.append(dict(delta=d, press_pad_frame=pulse_rel_fn(d), outcome="accepted" if "continue_accept" in ev else "expired" if "game_over_branch" in ev or "continue_exit" in ev else "ignored",
                         accept_event=ev.get("continue_accept", [None])[0], sounds=[s for s in out["sound_requests"] if s[1] in ("A0",)]))
    return rows


def observe_all(rom, st, art, decoded, progress=print, only=None):
    scen = []
    for sc in scenario_defs():
        progress("scenario " + sc["id"])
        out, _ = run_scenario(rom, sc)
        scen.append(summarize(st, art, rom, decoded, out))
    zones = []
    for z in zone_matrix_defs():
        progress("scenario " + z["id"])
        out, _ = run_scenario(rom, dict(z, capture=True))
        s = summarize(st, art, rom, decoded, out)
        s["zone"], s["start"] = z["zone"], out["start"]
        zones.append(s)
    progress("boundary sweeps")
    base = dict(kind="pit", lives=1, continues=2, character=0, stop="title", note="boundary sweep")
    out, _ = run_scenario(rom, dict(base, id="pit_continue_expire_sonic", note="pit death on the last life, countdown unanswered, Game Over, title", capture=True))
    expire_frame = [e["f"] for e in out["log"] if e.get("digit") == 255][0]     # st rel after the frame that expired the countdown
    call_frame = out["events"]["continue_countdown_call"][0]
    baseline = summarize(st, art, rom, decoded, out)
    late = sweep(rom, base, "late", lambda d: expire_frame - 1 + d, range(-9, 4), lambda pr, rel, ev: "continue_accept" in ev or "game_over_branch" in ev)
    early = sweep(rom, base, "early", lambda d: call_frame + d, range(-6, 4), lambda pr, rel, ev: "continue_accept" in ev or (ev.get("digit_redraw") and True))
    return dict(format=1, rom_sha256=ROM_SHA256, base_commit=BASE_COMMIT, harness="tools/g0_rig.py over tools/sms_frame_harness.py (approximate VDP, NTSC frame timing; +/-1 frame)",
                scenarios=scen, zone_matrix=zones, baseline_pit_expire=baseline,
                boundary=dict(expire_frame_after_death_fixture=expire_frame, countdown_call_frame=call_frame, late_press=late, early_press=early,
                              note="press_pad_frame = harness frame whose interrupt carries the one-frame button edge; accepted/expired is the original code's decision"))


# ------------------------------------------------------------------------------------------------------------------------------------------
# Audit of existing Research data and POC assets, audio request ledger
AUDIT_JSON = DATA / "audit.json"
AUDIO_JSON = DATA / "audio-requests.json"

RESEARCH_EVIDENCE = [
    ("docs/g0-campaign-contract.md", "section 7 and T07/T08/T09 transitions: death, TIME OVER at 10:00, Continue (10 digits x 116 updates, button -> lives 3/5, score 0, continues -1) and Game Over -> title; timings only, no graphics"),
    ("data/g0/campaign-oracle.json", "oracle scenarios death_pit_lives3, death_time_over_lives3, death_continue_accept_sonic/_tails, death_continue_timeout, death_game_over_no_continue: run-state and frame checkpoints"),
    ("docs/audio-request-audit.md", "numeric request ledger: $87 $94 $A0 $B4 $96 call sites; no audible meaning claimed"),
    ("data/rom-cache/audio/request-ledger.json", "machine-readable request ledger with call-site triggers and driver pointers"),
    ("docs/u4-ordinary-results.md", "U4-A: shared card tile stream, fade engine, act title card; explicitly leaves TIME OVER, Continue and Game Over unextracted"),
    ("data/u4/ordinary-results-static.json", "U4-A decoded results data (160-tile stream, palette records 3/4/$21, fade constants)"),
    ("tools/u4_results.py", "U4-A fade-engine model reused here (fade_series) and the tile decoder wrapper"),
    ("tools/g0_rig.py", "persistent whole-game emulation session reused for every observed scenario"),
    ("tools/player_scripts.py", "player animation script parser (state $35 is statically present for both player types)"),
    ("tools/thz1_object_assets.py", "player mapping/frame-record parser reused for the Continue-screen character frames"),
    ("docs/player-state-11-graphics.md", "dynamic player tile transfer ($104B table, 12 tiles to VRAM $0000) already decoded for state $11; same mechanism here"),
]


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def research_inventory():
    rows = []
    for rel, what in RESEARCH_EVIDENCE:
        p = ROOT / rel
        rows.append(dict(path=rel, exists=p.exists(), sha256=file_sha(p) if p.exists() else None, covers=what))
    return rows


def png_size(path):
    b = Path(path).read_bytes()
    return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")


def poc_inventory(poc, commit):
    """Inventory of the POC resources that touch these screens (read-only; `poc` is a checkout of the accepted G2-A commit)."""
    poc = Path(poc)
    items = []

    def sprite(name, origin, note):
        d = poc / "sprites" / name
        pngs = sorted(d.glob("*.png"))
        w, h = png_size(pngs[0])
        items.append(dict(resource=name, kind="sprite", files=[str(p.relative_to(poc)).replace("\\", "/") for p in pngs], width=w, height=h,
                          frames_png_sha256=[file_sha(p) for p in pngs], origin=origin, note=note))
    sprite("SPR_chaos_results_tiles", "ROM-derived (U4-A export imported by G1-C)", "160-tile results stream sheet; shares tiles with the TIME OVER stream (see shared_graphics), not with Game Over/Continue")
    sprite("SPR_chaos_ss_continue", "ROM-derived (U4-A continue icon)", "the 2x2 results-card continue icon, not the Continue screen")
    sprite("SPR_chaos_title_tiles", "ROM-derived (U4-A act title stream)", "95-tile act title stream sheet")
    sprite("SPR_menu_game_over", "INHERITED, not from the ROM", "141x16 'GAME OVER' strip from the original GameMaker template, drawn by OBJ_menu_game_over at (250,215); not the ROM presentation")
    for rel, kind, note in (
            ("objects/OBJ_menu_game_over/Draw_0.gml", "object event", "draws SPR_menu_game_over; no fade, no tile, no title transition, no sound request"),
            ("objects/OBJ_player_death/Create_0.gml", "object event", "plays inherited SND_sonic_death, alarm[0]=100, alarm[1]=150"),
            ("objects/OBJ_player_death/Alarm_1.gml", "object event", "global.life > 0 -> room_restart(), else room_goto(ROM_menu_game_over); there is no Continue branch"),
            ("sounds/SND_sonic_death/SND_sonic_death.yy", "sound", "inherited death jingle; not asserted to be request $96"),
            ("rooms/ROM_menu_game_over/ROM_menu_game_over.yy", "room", "inherited game-over room")):
        p = poc / rel
        items.append(dict(resource=rel, kind=kind, exists=p.exists(), sha256=file_sha(p) if p.exists() else None, origin="INHERITED", note=note))
    gm = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in list((poc / "scripts").rglob("*.gml")) + list((poc / "objects").rglob("*.gml")))
    probes = {kw: gm.lower().count(kw.lower()) for kw in ("time over", "timeover", "continue_screen", "$d44b", "chaosContinues")}
    return dict(commit=commit, items=items, text_probes_in_gml=probes,
                no_resource_for=["TIME OVER screen", "Continue screen (banner, countdown digits, star frame, character animation)", "ROM Game Over card", "requests $87 $94 $A0 (and $B4 as countdown tick, $96 as request)"])


def build_audit(poc_path=None):
    prior = load_json(AUDIT_JSON) if AUDIT_JSON.exists() else {}
    poc = prior.get("poc")
    if poc_path:
        import subprocess
        commit = subprocess.run(["git", "-C", str(poc_path), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        poc = poc_inventory(poc_path, commit)
    return dict(format=1, research_main=BASE_COMMIT, research_evidence=research_inventory(), poc=poc)


def build_audio(rom, st):
    ledger = load_json(ROOT / "data" / "rom-cache" / "audio" / "request-ledger.json")
    by_id = {r["request_id"]: r for r in ledger["requests"]}
    triggers = [
        ("$96", 0x49B6, "player death routine $4984, zone < 8; fires on every death (time over, pit, hurt without rings): the same request that precedes the life-lost loop", "death_routine"),
        ("$94", 0x141D, "Continue screen entry: sound written after the screen is drawn and before the 16-update set-up loop", "continue_screen"),
        ("$B4", 0x1487, "each countdown digit change 8..0 ($1482 redraw then the request); nine times per unanswered countdown, none for digit 9 or the expiry", "continue_countdown"),
        ("$A0", 0x148E, "button edge accepted by the countdown loop ($146A..$148C): once, before D2C3 is decremented", "continue_accept"),
        ("$87", 0x13A5, "Game Over screen, written after the card draw and fade request, before the two 240-update holds ($139D branch: no continue, or an expired countdown)", "game_over_branch"),
    ]
    rows = []
    for name, addr, trig, key in triggers:
        v = int(name[1:], 16)
        r = by_id.get(v, {})
        found = [s for s in st["sound_requests"][key] if int(s["store_cpu"], 16) == addr]
        rows.append(dict(request=name, store_cpu=hx(addr, 4), operand_read_from_code=bool(found), trigger=trig, driver_category=r.get("category"), friendly_name=r.get("friendly_name"),
                         name_status=r.get("name_status"), ledger_sites=[hx(s["cpu_address"], 4) for s in r.get("call_sites", [])],
                         poc_support="UNSUPPORTED: no verified audio resource in the POC (G2-A) for this request" if name in ("$94", "$A0", "$87") else
                         "NOT IMPLEMENTED as a request; inherited SND_sonic_death is not asserted to be $96" if name == "$96" else "NOT VERIFIED: no ROM-verified countdown tick asset wired"))
    return dict(format=1, rom_sha256=ROM_SHA256, note="request numbers and trigger points only; no meaning beyond the AUDIO-0 ledger is claimed and no unrelated music or effect is substituted",
                requests=rows, music_fade_regs=dict(site="$18E1", values=[12, 1, 2], addresses=["DE09", "DE0A", "DE0B"],
                                                    called_at=["$1458 (continue exit)", "$13BB (Game Over before the title)", "$34C3 (TIME OVER fade-out)", "$1648 (life-lost fade)"]))


# ------------------------------------------------------------------------------------------------------------------------------------------
# Static document
def shared_tile_map(rom, st, decoded):
    """Which tiles of the new streams are byte-identical to tiles of the already-decoded U4 streams (index pairs, no pixels)."""
    u4 = load_json(ROOT / "data" / "u4" / "ordinary-results-static.json")
    res_sha = u4["tile_stream"]["tile_sha256"]
    res_index = {h: 256 + i for i, h in reversed(list(enumerate(res_sha)))}
    blank = sha(bytes(32))
    out = {}
    for sid, s in st["tile_streams"].items():
        pairs = [[s["first_tile_index"] + i, res_index[h]] for i, h in enumerate(s["tile_sha256"]) if h in res_index and h != blank]
        out[sid] = dict(shared_with_u4_results_stream=pairs, count=len(pairs), note="[tile index in this stream's VRAM layout, tile index of the first identical tile in the U4 results stream (VRAM $2000 + 256)]")
    return out


def build_static(rom):
    st, decoded = static_census(rom)
    art = player_art(rom)
    st["player_art"] = art
    st["streams_overlap"] = streams_overlap(rom, st)
    st["shared_tiles_with_results_stream"] = shared_tile_map(rom, st, decoded)
    st["sprite_placement"] = dict(object_screen_x=128, object_screen_y=160, camera="zero (D15E.. cleared by $4FCE)", sat_y="screen Y + relative Y (the VDP draws one line lower)", sat_x="screen X + relative X",
                                  pattern_base=0, size="8x16", palette="sprite record 7 (D495 request)", verified="observed SAT/VRAM/pixels equal the composition in every capture")
    st["unresolved"] = UNRESOLVED
    st["evidence_classes"] = EVIDENCE_CLASSES
    return st, decoded, art


EVIDENCE_CLASSES = [
    dict(cls="DECODED DATA", what="tile streams, tilemap cells, glyph table, palette records, player scripts/mappings/tile transfers read from ROM bytes"),
    dict(cls="BYTE-VERIFIED ASSEMBLY", what="routine regions with offset/length/SHA-256; operands of the draw, loader, fade-request, wait and sound instructions parsed from the code bytes"),
    dict(cls="SOURCE-TRACED BEHAVIOUR", what="hand disassembly of $15F2..$1673, $138A..$14AB, $3436..$34D3, $27EE..$2884, $4984..$49C3, $361D..$3657, $2349..$23F7, $2451..$2496"),
    dict(cls="MODEL VERIFIED AGAINST THE ORIGINAL CODE", what="Python composition (name table, tiles, palette, sprite SAT/pixels) and the U4 fade model compared with emulated VRAM/CRAM/SAT/rendered pixels"),
    dict(cls="EMULATED ORIGINAL FRAME", what="tools/g0_rig.py runs of the unmodified ROM: event frames, sound writes, CRAM series, button-edge outcomes (harness frames, +/-1)"),
    dict(cls="CONTROLLED VARIANT", what="RAM presets of lives/continues/score/clock/player Y and scripted one-frame button edges; stated per scenario"),
    dict(cls="UNRESOLVED", what="see the unresolved list"),
]

UNRESOLVED = [
    dict(id="U4B-1", item="meaning/timbre of requests $87, $94, $A0 (and $B4, $96): numbers and trigger points only; no audio is extracted or substituted", state="OPEN - AUDIO-0/U5, does not block the screens"),
    dict(id="U4B-2", item="cycle-exact cadence on real hardware: the Continue digit, hold and fade waits are `$062D` frame waits, but the harness shows each as n or n-1 frames and the player-update body is CPU-bound; the +/-1 figures are harness measurements", state="EMULATED, not cycle-proven"),
    dict(id="U4B-3", item="a 7-pixel sprite row at screen line 0 (x 1..7) appears in the emulated Game Over and Continue frames: unused SAT entries are parked at Y=$E0 or Y=$F0 ($21DA writes $F0; the player engine rewrites the first entries to $E0), and an 8x16 sprite at Y=$F0 wraps its last row onto line 0 showing leftover player tile data (X 1..7). Whether real hardware / the TV overscan shows it is unverified; TIME OVER shows none", state="EMULATOR OBSERVATION, hardware unverified; recommend the POC does not draw it"),
    dict(id="U4B-4", item="the frozen level frame faded to black before TIME OVER / Continue / Game Over is level specific (death animation, camera, palettes); only the post-fade black screens are reproducible from tables", state="ADAPTER must keep the last gameplay frame"),
    dict(id="U4B-5", item="real-time duration of the death sequence before the screens ($15F2..$164B: animation loop until D51D == 2, 60 + 90 waits, fade passes) depends on the death type (pit fall distance, hurt arc); only the fixed waits are decoded", state="PARTIAL: waits decoded, animation length per death type measured only for the pit/time-over fixtures"),
    dict(id="U4B-6", item="POC input mapping: the original accepts a NEW press edge of either fire button (D147 & $30, one edge per interrupt); a PC adapter must not accept a held button or a key-repeat", state="DECODED, adapter decision"),
    dict(id="U4B-7", item="Continue availability when D2C3 bit 7 is set at the death (a continue was just used): `$13ED` clears bit 7 first, so a just-used flag never blocks a new Continue screen; verified only through the code and the scenarios above, not through an accepted-continue-then-die run", state="SOURCE-TRACED"),
    dict(id="U4B-8", item="the two-digit field always shows tens digit 0 (cell pair fixed in the 2x6 block); a counter above 9 digits does not exist, so no larger layout is decoded", state="DECODED"),
    dict(id="U4B-9", item="the ending TRY AGAIN card ($34D3, sound $98) is a different screen (stream bank $16 $B1E4, 1-byte cells) and is not part of this package", state="OUT OF SCOPE"),
    dict(id="U4B-10", item="`docs/u4-ordinary-results.md` lists `$21DA` as clearing the name table `:= 0`; the operand is `LD DE,$00C0`, so the fill word is $00C0 (tile 192, which `$21DA` also zeroes). Harmless to U4-A (its card refills VRAM tile 256+), but corrected here", state="NOTE on an accepted document; U4-A text left unchanged"),
    dict(id="U4B-11", item="TIME OVER is reached by presetting the clock to 09:59.59 (RAM) and letting the original `$27EE` roll it to 10:00; no real ten-minute act was played. The trigger operands (BCD `$10` minutes, D44B := $C0) are decoded from the code", state="CONTROLLED VARIANT + BYTE-VERIFIED trigger"),
]


def validate_static(st):
    errs = []
    if st.get("rom_sha256") != ROM_SHA256:
        errs.append("static: ROM hash")
    if st.get("base_commit") != BASE_COMMIT:
        errs.append("static: base commit")
    for r in st["routines"]:
        if r["length"] <= 0 or len(r["sha256"]) != 64:
            errs.append("static: routine " + r["name"])
    for sid, n in (("gameover_continue", 87), ("time_over", 44)):
        s = st["tile_streams"][sid]
        if s["tile_count"] != n or len(s["tile_sha256"]) != n or s["decoded_length"] != 32 * n or s["first_tile_index"] != 192 or s["vram_destination"] != "1800":
            errs.append("static: stream " + sid)
    want = dict(game_over=[(8, 8, 3, 17)], continue_=None, time_over=[(10, 8, 4, 17)])
    got = {k: [(b["row"], b["col"], b["rows"], b["cols"]) for b in v["blocks"]] for k, v in st["screens"].items()}
    if got["game_over"] != want["game_over"] or got["time_over"] != want["time_over"] or got["continue"] != [(3, 9, 3, 15), (11, 13, 2, 6)]:
        errs.append("static: block layout")
    for k, v in st["screens"].items():
        for b in v["blocks"]:
            if len(b["cells"]) != b["rows"] * b["cols"]:
                errs.append("static: cell count " + k)
    dd = st["screens"]["continue"]["digit_draw"]
    if [g["digit"] for g in dd["glyphs"]] != list(range(10)) or (dd["row"], dd["col"]) != (11, 16):
        errs.append("static: digit glyphs")
    # the digit-9 glyph pair equals the 2x6 block's right digit cell pair, digits 8..0 are the redraw targets
    blk = st["screens"]["continue"]["blocks"][1]["cells"]
    if (blk[3], blk[9]) != (dd["glyphs"][9]["top"], dd["glyphs"][9]["bottom"]) or (blk[2], blk[8]) != (dd["glyphs"][0]["top"], dd["glyphs"][0]["bottom"]):
        errs.append("static: initial 09 field is not glyphs 0 and 9")
    fr = {k: [(f["slot"][:4], f["record"], f["flags"]) for f in v] for k, v in st["fade_requests"].items()}
    if fr != {"game_over": [("D492", 0x22, "80"), ("D494", 7, "80")], "continue": [("D492", 0x24, "80"), ("D494", 7, "80")], "time_over": [("D492", 0x23, "80")]}:
        errs.append("static: fade requests")
    w = {k: v["iterations"] for k, v in st["wait_loops"].items()}
    if w != dict(death_animation_end_wait=60, death_after_fade_wait=90, time_over_hold=180, time_over_after_fade_wait=90, game_over_hold_1=240, game_over_hold_2=240,
                 game_over_fade_wait=60, continue_setup_updates=16, continue_after_fade_request=30, continue_accept_hold=180, continue_exit_fade_wait=60):
        errs.append("static: wait loops")
    c = st["countdown"]
    if (c["initial_digit"], c["ticks_per_digit_compare"], c["expiry_compare"], c["tick_sound"], c["accept_sound"], c["music_request"], c["accept_button_mask"]) != (9, 116, 255, "B4", "A0", "94", "30"):
        errs.append("static: countdown constants")
    snd = {k: [s["value"] for s in v] for k, v in st["sound_requests"].items()}
    if snd != dict(death_routine=["96"], game_over_branch=["87"], continue_screen=["94"], continue_countdown=["B4"], continue_accept=["A0"], time_over_screen=[], life_lost_branch=[]):
        errs.append("static: sound requests")
    po = st["player_object"]
    if (po["state"], po["x_word_low"], po["y_word_low"]) != ("35", "80", "A0"):
        errs.append("static: player object")
    if st["name_table_fill"]["word"] != 0xC0 or st["name_table_fill"]["words"] != 0x380:
        errs.append("static: fill word")
    if st["lives_restore"] != dict(sonic=3, other=5, site=st["lives_restore"]["site"]):
        errs.append("static: lives restore")
    if [r["frame"] for r in st["player_art"]["1"]["idle"]] != [17, 18] or [r["frame"] for r in st["player_art"]["2"]["idle"]] != [15, 16]:
        errs.append("static: idle frames")
    if [r["frame"] for r in st["player_art"]["1"]["accept_run"]] != [7, 8, 9, 10] or [r["frame"] for r in st["player_art"]["2"]["accept_run"]] != [7, 8, 9]:
        errs.append("static: run frames")
    for t, a in st["player_art"].items():
        if any(r["updates"] != 8 for r in a["idle"]) or any(r["updates"] != 4 for r in a["accept_run"]):
            errs.append("static: animation cadence")
    for rid, rec in st["palette_records"].items():
        if len(rec["sms_colours"]) != 16:
            errs.append("static: palette record " + rid)
    if st["time_over_trigger"]["d44b_value"] != "C0" or st["time_over_trigger"]["minutes_compare"] != "10":
        errs.append("static: time over trigger")
    return errs


def validate_observed(ob):
    errs = []
    if ob.get("rom_sha256") != ROM_SHA256:
        errs.append("observed: ROM hash")
    allsc = ob["scenarios"] + ob["zone_matrix"] + [ob["baseline_pit_expire"]]
    for s in allsc:
        for name, c in (s.get("captures") or {}).items():
            for key in ("name_table_equal", "bg_tiles_equal_decoded_stream", "bg_pixels_equal", "cram_equal"):
                if not c[key]:
                    errs.append("observed: %s %s %s false" % (s["id"], name, key))
            if c["screen"] == "continue" and c.get("sprite_frame_matched") is None:
                errs.append("observed: %s %s sprite not matched" % (s["id"], name))
            if c["screen"] == "continue" and not c.get("player_object_equal"):
                errs.append("observed: %s %s player object is not (type, $35, 128, 160)" % (s["id"], name))
            if c["screen"] != "continue" and not c.get("sprite_layer_empty_below_line0"):
                errs.append("observed: %s %s stray sprites" % (s["id"], name))
        for sc, fc in s["fade_checks"].items():
            if not fc["occurrences"]:
                errs.append("observed: %s %s no steady palette seen" % (s["id"], sc))
            for o in fc["occurrences"]:
                if not o["fade_in_matches_model"]:
                    errs.append("observed: %s %s fade-in differs from the model" % (s["id"], sc))
                if not o["fade_out_matches_model"]:
                    errs.append("observed: %s %s fade-out differs from the model" % (s["id"], sc))
    by = {s["id"]: s for s in ob["scenarios"]}
    for s in allsc:
        d = s.get("death_snapshot")
        if s["kind"] == "time_over" and (not d or d["clock"] != "10:00.00" or d["d44b"] != "80"):
            errs.append("observed: %s TIME OVER death is not at 10:00.00 with D44B = $80" % s["id"])
        if s["kind"] == "pit" and d and d["d44b"] != "00":
            errs.append("observed: %s pit death has a TIME OVER flag" % s["id"])
    exp = by["time_over_continue_expire_sonic"]
    if "time_over_screen" not in exp["events"] or "game_over_sound" not in exp["events"] or "continue_accept" in exp["events"]:
        errs.append("observed: expire path events")
    if exp["end"]["continues_raw"] != "02":
        errs.append("observed: an expired countdown consumed a continue")
    acc = by["time_over_continue_accept_sonic"]
    if "continue_accept" not in acc["events"] or "game_over_branch" in acc["events"] or acc["end"]["lives_bcd"] != "03" or acc["end"]["score_bcd"] != "000000" or acc["end"]["continues_raw"] != "81":
        errs.append("observed: accept path result")
    tacc = by["pit_continue_accept_tails"]
    if tacc["end"]["lives_bcd"] != "05" or tacc["end"]["score_bcd"] != "000000" or tacc["end"]["continues_raw"] != "82":
        errs.append("observed: tails accept result")
    late = ob["boundary"]["late_press"]
    outcomes = [r["outcome"] for r in late]
    if "accepted" not in outcomes or "expired" not in outcomes or outcomes != sorted(outcomes, key=lambda o: 0 if o == "accepted" else 1):
        errs.append("observed: late boundary sweep is not monotone")
    return errs


def build_all(rom, only=None, progress=print, poc=None):
    st, decoded, art = build_static(rom)
    audit = build_audit(poc)
    audio = build_audio(rom, st)
    ob = None if only == "static" else observe_all(rom, st, art, decoded, progress=progress)
    return st, decoded, art, audit, audio, ob


def emulated_exports(rom, st, art, decoded, out=BUILD):
    """Ignored PNG exports of emulated frames (reference run, Sonic) for visual comparison; hashes are in the observed JSON."""
    sc = [s for s in scenario_defs() if s["id"] == "time_over_continue_expire_sonic"][0]
    o, _ = run_scenario(rom, sc)
    for name, c in o["captures"].items():
        if name in ("time_over_steady", "game_over_steady", "continue_steady_9", "continue_steady_3"):
            bg = c["bg"]
            flat = [[(c["sprite"][y][x] if c["sprite"][y][x] is not None and y > 0 else bg[y][x]) for x in range(256)] for y in range(192)]
            cram = list(bytes.fromhex(c["cram"]))
            png_rgba_rows(out / "emulated" / ("%s.png" % name), flat, cram)


def write_all(rom, only=None, progress=print, poc=None):
    DATA.mkdir(parents=True, exist_ok=True)
    st, decoded, art, audit, audio, ob = build_all(rom, only, progress, poc)
    STATIC_JSON.write_text(dumps(st), encoding="utf-8", newline="\n")
    AUDIT_JSON.write_text(dumps(audit), encoding="utf-8", newline="\n")
    AUDIO_JSON.write_text(dumps(audio), encoding="utf-8", newline="\n")
    man = export_assets(rom, st, decoded, art)
    MANIFEST_JSON.write_text(dumps(man), encoding="utf-8", newline="\n")
    if ob is not None:
        OBS_JSON.write_text(dumps(ob), encoding="utf-8", newline="\n")
        emulated_exports(rom, st, art, decoded)


def check_all(rom, progress=print, only=None):
    problems = []
    st, decoded, art = build_static(rom)
    if dumps(st) != STATIC_JSON.read_text(encoding="utf-8"):
        problems.append("static census differs from the committed file")
    problems += validate_static(st)
    if dumps(build_audio(rom, st)) != AUDIO_JSON.read_text(encoding="utf-8"):
        problems.append("audio request ledger differs from the committed file")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        man = export_assets(rom, st, decoded, art, out=Path(td))
        if dumps(man) != MANIFEST_JSON.read_text(encoding="utf-8"):
            problems.append("export manifest differs from the committed file")
    if only != "static":
        ob = observe_all(rom, st, art, decoded, progress=progress)
        if dumps(ob) != OBS_JSON.read_text(encoding="utf-8"):
            problems.append("observations differ from the committed file")
        problems += validate_observed(ob)
    return problems


# ------------------------------------------------------------------------------------------------------------------------------------------
# Generated tables of docs/u4b-time-over-continue-game-over.md
_MARK = "<!-- %s u4b:%s -->"


def _md(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |" for r in rows]
    return "\n".join(out)


def doc_tables(st, ob, audio):
    t = {}
    t["routines"] = _md([[r["name"], "%s%s-$%s" % ("bank $%02X " % r["bank"] if r["bank"] is not None else "res ", "$" + r["cpu_start"], r["cpu_end_exclusive"]), "0x" + r["file_start"], r["length"],
                          "`%s`" % r["sha256"][:12], r["role"]] for r in st["routines"]], ["routine", "CPU range (end exclusive)", "file", "bytes", "SHA-256", "role"])
    ref = {s["id"]: s for s in ob["scenarios"]}["time_over_continue_expire_sonic"]
    ev = ref["events"]
    rows = [["death fixture frame", ev["life_lost_entry"][0], "clock reaches 10:00 (`$281C` sets D44B := $C0); `$4984` runs, sound `$96`, life -1"],
            ["TIME OVER screen", ev["time_over_screen"][0], "`$3495`: clears, tile load, 4x17 block, fade-in request"],
            ["TIME OVER exit", ev["time_over_exit"][0], "`$34CE`: after 180-update hold, fade-out, 90-update wait; D44B := 0"],
            ["last-life branch", ev["last_life_branch"][0], "`$138A` (D293 bit 6 clear)"],
            ["Continue screen", ev["continue_screen"][0], "`$13F5`: object init, `$345B` draw, sound `$94`"],
            ["Continue fade-in request", ev["continue_fade_request"][0], "`$1431`: BG record $24, sprite record 7 (after the 16-update set-up loop)"],
            ["countdown loop entered", ev["continue_countdown_call"][0], "`$1464` (after the 30-update wait)"],
            ["digit 8 .. digit 0 redrawn", ", ".join(str(x) for x in ev["digit_redraw"]), "`$1482`; sound `$B4` one frame later each"],
            ["countdown expired", ev["continue_exit"][0], "digit underflow to $FF, return, `$1450` exit fade"],
            ["Game Over branch", ev["game_over_branch"][0], "`$139D` after the 60-update exit wait"],
            ["Game Over card / sound `$87`", ev["game_over_sound"][0], "`$13A3`"],
            ["title", ev["title"][0], "`$04B4` after 240 + 240 holds, fade, 60-update wait"]]
    t["timeline"] = _md(rows, ["event", "harness frame after the death fixture", "ROM"])
    b = ob["boundary"]
    t["boundary"] = _md([[r["delta"], r["press_pad_frame"], r["outcome"]] for r in b["early_press"]], ["delta vs countdown-loop entry", "pad frame", "outcome"]) + "\n\n" + \
        _md([[r["delta"], r["press_pad_frame"], r["outcome"]] for r in b["late_press"]], ["delta vs the frame that expires the countdown", "pad frame", "outcome"])
    t["scenarios"] = _md([[s["id"], "pit" if s["kind"] == "pit" else "TIME OVER", "Tails" if s["character"] else "Sonic", s["press_rel"] if s["press_rel"] is not None else "-",
                           "A0" if any(x[1] == "A0" for x in s["sound_requests"]) else "-", "yes" if "game_over_sound" in s["events"] else "no", "yes" if "level_reload" in s["events"] else "no",
                           "%s / %s / %s" % (s["end"]["lives_bcd"], s["end"]["continues_raw"], s["end"]["score_bcd"])] for s in ob["scenarios"]],
                         ["scenario", "death", "character", "button edge (frame)", "`$A0`", "Game Over", "act reloaded", "end lives / D2C3 / score"])
    t["audio"] = _md([[r["request"], "$" + r["store_cpu"], r["trigger"], r["driver_category"], r["friendly_name"] or "unresolved", r["poc_support"]] for r in audio["requests"]],
                     ["request", "store", "trigger", "driver", "ledger name", "POC status"])
    t["unresolved"] = _md([[u["id"], u["item"], u["state"]] for u in st["unresolved"]], ["id", "item", "state"])
    return t


def refresh_doc(path=DOC):
    st, ob, audio = load_json(STATIC_JSON), load_json(OBS_JSON), load_json(AUDIO_JSON)
    text = Path(path).read_text(encoding="utf-8")
    for name, body in doc_tables(st, ob, audio).items():
        a, b = _MARK % ("BEGIN", name), _MARK % ("END", name)
        if a not in text:
            continue
        i, j = text.index(a) + len(a), text.index(b)
        text = text[:i] + "\n" + body + "\n" + text[j:]
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--only", choices=["static"])
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--doc", action="store_true", help="refresh the generated tables inside docs/u4b-time-over-continue-game-over.md from the committed JSON")
    ap.add_argument("--poc", help="path of a POC checkout (G2-A) to refresh the POC inventory in data/u4b/audit.json")
    a = ap.parse_args(argv)
    if a.doc:
        refresh_doc()
        return 0
    if a.validate:
        errs = validate_static(load_json(STATIC_JSON)) + validate_observed(load_json(OBS_JSON))
        print("OK" if not errs else "\n".join(errs))
        return 1 if errs else 0
    rom = load_rom(a.rom or os.environ.get("SONIC_CHAOS_ROM") or ROOT.parent / "source" / "Sonic Chaos (Europe).sms")
    if a.check:
        problems = check_all(rom, only=a.only)
        print("U4-B check: OK" if not problems else "\n".join(problems))
        return 1 if problems else 0
    write_all(rom, only=a.only, poc=a.poc)
    print("wrote", DATA, "exports in", BUILD)
    return 0


if __name__ == "__main__":
    sys.exit(main())

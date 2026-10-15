#!/usr/bin/env python3
"""U4-A: original ordinary act-clear results presentation (Sonic Chaos SMS, Europe v1.2).

    python tools/u4_results.py ROM                 # regenerate data/u4/*.json and the ignored exports in build/u4/
    python tools/u4_results.py ROM --check         # recompute everything and compare with the committed JSON
    python tools/u4_results.py ROM --only static   # static census only (no emulation, a few seconds)
    python tools/u4_results.py --validate          # no ROM: internal consistency of the committed JSON

Layers (each field of the output says which one it belongs to):

* ``static``   - BYTE-VERIFIED ASSEMBLY / DECODED DATA read straight from ROM bytes: routine regions, draw plan operands, tilemaps, the digit
                 glyph table, icon maps, the 160-tile compressed stream, palette records, the fade-engine constants.
* ``compose``  - a Python re-implementation of the ROM draw routines (`$32F9`, `$26D6..$27DE`, `$2F08`, `$33F1`) producing the 32x24 name table; it is
                 *verified* against the emulated VRAM of the original code (`observe`).
* ``observe``  - EMULATED ORIGINAL FRAME runs (tools/g0_rig.py, approximate VDP, cycle-driven Z80): frame offsets, CRAM series, name tables, sounds.
* ``adapter``  - GameMaker presentation notes (348x196). Never mixed into the ROM-native fields.

No ROM byte, tile pixel or palette is written to the committed JSON except small decoded numeric tables of the same kind earlier Research caches
already commit (name-table entries, 2-bit colour values, glyph tile ids).  Tile pixels and composed frames are exported to the ignored ``build/u4/``.
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

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
BASE_COMMIT = "db23e5400db923025d2179aba5a01535c6f64b89"
DATA = ROOT / "data" / "u4"
BUILD = ROOT / "build" / "u4"
STATIC_JSON = DATA / "ordinary-results-static.json"
OBS_JSON = DATA / "ordinary-results-observed.json"
MANIFEST_JSON = DATA / "export-manifest.json"

BANK_RESULTS = 19        # `$79CB` pages bank $13 into slot 2 and every card source below is read from it
BANK_PALETTE = 14        # fade engine and palette records (`$B45A`, `$B64D`)
VRAM_TILES = 0x2000      # `$79D1`: tile stream destination (tile index 256..)
TILE_BASE = 256
NAME_TABLE = 0x3800
FILL_WORD = 0x0121       # `$3302`: whole-screen fill word (tile 289 = solid colour index 13 of the card palette)


# ------------------------------------------------------------------------------------------------------------------------------------------
# ROM helpers
def hx(v, n=2):
    return format(v, "0%dX" % n)


def sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def off(bank, cpu):
    """File offset of a CPU address; `bank` is ignored below $8000 (resident engine) and used for slot 2."""
    if cpu < 0x8000:
        return cpu
    return bank * 0x4000 + cpu - 0x8000


def u16(rom, o):
    return rom[o] | (rom[o + 1] << 8)


def load_rom(path):
    data = Path(path).read_bytes()
    if len(data) != 524288 or hashlib.sha256(data).hexdigest() != ROM_SHA256:
        raise ValueError("Expected the documented Sonic Chaos SMS research ROM (SHA-256 %s)" % ROM_SHA256)
    return data


def region(rom, name, bank, a, b, role):
    o = off(bank, a)
    n = b - a
    return dict(name=name, bank=(bank if a >= 0x8000 else None), cpu_start=hx(a, 4), cpu_end_exclusive=hx(b, 4), file_start=hx(o, 5),
                length=n, first16=bytes(rom[o:o + 16]).hex(), sha256=sha(rom[o:o + n]), role=role)


# (name, bank, start, end_exclusive, role)
ROUTINES = [
    ("act_clear_tail", None, 0x14AE, 0x1543, "main-loop branch for D293 bit 5: fades, results, tally, act += 1, reload request"),
    ("zone_clear_tail", None, 0x1543, 0x15F2, "main-loop branch for D293 bit 4 (act index 2): same tail, zone gate, zone += 1"),
    ("results_card", None, 0x32F9, 0x33F1, "card draw: tile load, fill, banner, labels, panel, continue icons, numbers, fade-in, 60-wait, tally"),
    ("emerald_icons", None, 0x33F1, 0x342A, "up to five 2x2 emerald icons from D2CC bits 0..4"),
    ("palette_white_fill", None, 0x342A, 0x3436, "fills the palette buffer D472..D491 with $3F"),
    ("results_tile_loader", None, 0x79CB, 0x79DF, "bank 19, VRAM $2000, tile stream $949C through the $24C2 decoder"),
    ("tally_loops", None, 0x2D08, 0x2D55, "ring loop (10 raw per ring) then bonus-word loop (1 raw per step)"),
    ("tally_boss_bonus", None, 0x2D55, 0x2D84, "act index 2 only: N steps of 10 raw (N from the table at $2D84)"),
    ("tally_boss_table", None, 0x2D84, 0x2D90, "six 16-bit step counts, one per zone"),
    ("tally_pacing", None, 0x2EE6, 0x2EFB, "step counter D110 and the 255-iteration delay (skipped when a button is held)"),
    ("tally_award", None, 0x2EFB, 0x2F49, "score add via $262F, continue icon redraw, sound $B4 every 16th step"),
    ("score_add", None, 0x262F, 0x26D6, "BCD score add, continue award rule (D2C8 dependent)"),
    ("number_draw", None, 0x26D6, 0x27DF, "ring, bonus and score fields: BCD to digits, zero suppression, 1x2 glyph cells"),
    ("fade_slot_reset", None, 0x1CAF, 0x1CBD, "D492/D494 := bit 6 only (fade to black)"),
    ("palette_upload", None, 0x1CBD, 0x1CD3, "D496 != 0: D472 -> CRAM (32 bytes)"),
    ("animation_freeze", None, 0x1CEB, 0x1D06, "clears four sprite animation slots, D39B (terrain animation pointer), D131/D132"),
    ("sound_regs", None, 0x18E1, 0x18ED, "DE09..DE0B := 12,1,2"),
    ("object_clear", None, 0x297E, 0x2993, "zeroes D300..DBBF, D131/D132"),
    ("camera_clear", None, 0x4FCE, 0x4FDC, "zeroes D15E..D28F"),
    ("name_table_clear", None, 0x21DA, 0x220E, "frame wait, name table $3800 x $380 words := 0, VRAM $1800 x 32, SAT buffer Y := $F0"),
    ("fade_engine", BANK_PALETTE, 0xB45A, 0xB63E, "every 5th frame: per-slot palette step (to white, to black, in from black, in from white, copy)"),
    ("fade_palette_select", BANK_PALETTE, 0xB63E, 0xB64D, "slot +1 -> table address $B64D + 16*index"),
    ("fade_isr_hook", None, 0x058A, 0x0590, "frame interrupt: palette upload, input scan"),
    # act title card (runs at every act load, i.e. between the post-tally black and gameplay)
    ("level_reload_branch", None, 0x1673, 0x1696, "D293 bit 1: $4FCE, $3175 (title card), $2934 loader, $794F fade-in request"),
    ("act_title_card", None, 0x3175, 0x31E2, "name-table fills, fade-in request, sound $88, arrows, text, 180-frame hold, fade-out"),
    ("act_title_arrows", None, 0x31E2, 0x3225, "29 iterations of two 2x3 arrow blocks sliding along rows 1 and 21"),
    ("act_title_text", None, 0x3225, 0x32CA, "zone-name object (32x4) then act-number object (12x4) built by the $2D90 name-table animator"),
    ("act_title_zone_table", None, 0x32CA, 0x32D6, "six pointers (bank 19) to the 32x4 zone-name maps"),
    ("act_title_delay", None, 0x32EE, 0x32F4, "DEC BC / JR NZ busy delay (CPU time, not frames)"),
    ("name_table_animator", None, 0x2D90, 0x2EE6, "per-update scroller for objects D700.. (modes 0..3)"),
    ("title_tile_loader", None, 0x7A12, 0x7A26, "bank 19, VRAM $2000, tile stream $A7E5"),
]


# ------------------------------------------------------------------------------------------------------------------------------------------
# Static census
def _imm(rom, addr, opcode):
    """Operand of `LD rr,nn` / `LD r,n` at a resident CPU address, checking the opcode byte."""
    if rom[addr] != opcode:
        raise ValueError("unexpected opcode at $%04X: %02X != %02X" % (addr, rom[addr], opcode))
    return u16(rom, addr + 1) if opcode in (0x01, 0x11, 0x21) else rom[addr + 1]


def cell(addr):
    """Name-table byte address -> (column, row)."""
    idx = addr - NAME_TABLE
    return (idx % 64) // 2, idx // 64


def tile_stream_info(rom):
    o = off(BANK_RESULTS, 0x949C)
    count = u16(rom, o + 2)
    cmd = o + u16(rom, o + 4)
    data = o + 6
    ptr = data
    for i in range(count):
        c = TD.extract_command(rom, cmd, i)
        if c == 1:
            ptr += 32
        elif c in (2, 3):
            _, ptr = TD._expand_sparse_tile(rom, ptr)
    cmd_end = cmd + (count + 3) // 4
    decoded = TD.decompress_tile_stream(rom, o)
    return dict(bank=BANK_RESULTS, cpu_start="949C", file_start=hx(o, 5), header=bytes(rom[o:o + 6]).hex(), tile_count=count,
                payload_file_range=[hx(data, 5), hx(ptr, 5)], command_file_range=[hx(cmd, 5), hx(cmd_end, 5)],
                stream_file_end_exclusive=hx(max(ptr, cmd_end), 5), stream_sha256=sha(rom[o:max(ptr, cmd_end)]),
                decoded_length=len(decoded), decoded_sha256=sha(decoded), vram_destination=hx(VRAM_TILES, 4), first_tile_index=TILE_BASE,
                tile_sha256=[sha(decoded[i * 32:(i + 1) * 32]) for i in range(count)]), decoded


def draw_plan(rom):
    """The `$32F9` draw operands, read from the code bytes (not typed in)."""
    LDHL, LDBC, LDDE = 0x21, 0x01, 0x11

    def blk(bid, desc, cond, hl, bc, de, kind="tile1", bank=BANK_RESULTS):
        h, b, d = _imm(rom, hl, LDHL), _imm(rom, bc, LDBC), _imm(rom, de, LDDE)
        rows, cols = b >> 8, b & 0xFF
        col, row = cell(h)
        n = rows * cols
        o = off(bank, d)
        raw = bytes(rom[o:o + n * (1 if kind == "tile1" else 2)])
        return dict(id=bid, description=desc, condition=cond, instructions=dict(hl="%04X" % hl, bc="%04X" % bc, de="%04X" % de),
                    routine="$2383" if kind == "tile1" else "$2349", name_table_address=hx(h, 4), col=col, row=row, cols=cols, rows=rows,
                    source_bank=bank, source_cpu=hx(d, 4), source_file=hx(o, 5), source_bytes=len(raw), source_sha256=sha(raw),
                    tiles=[raw[i] for i in range(n)] if kind == "tile1" else [raw[2 * i] | (raw[2 * i + 1] << 8) for i in range(n)],
                    entry_kind=("tile id byte; attribute byte = D2D3 constant" if kind == "tile1" else "16-bit name-table entry from ROM"))

    fill = dict(id="screen_fill", description="whole 32x24 screen filled with one entry", condition="always", instructions=dict(hl="32FC", bc="32FF", de="3302"),
                routine="$1D8A", name_table_address=hx(_imm(rom, 0x32FC, LDHL), 4), cells=_imm(rom, 0x32FF, LDBC), entry=_imm(rom, 0x3302, LDDE))
    blocks = [
        blk("banner_sonic", "SONIC HAS PASSED banner", "D2CD == 0 and D2C8 == 1", 0x3315, 0x3318, 0x331B),
        blk("banner_other", "banner for D2C8 != 1 (Tails)", "D2CD == 0 and D2C8 != 1", 0x3323, 0x3326, 0x3329),
        blk("labels_ordinary", "RING / SPEED / SCORE / CONTINUE labels", "D2CD == 0", 0x332F, 0x3332, 0x3335),
        blk("panel_ordinary", "'x 100' / 'x 10' multiplier panel", "D2CD == 0", 0x333B, 0x333E, 0x3341),
        blk("banner_stage", "Special Stage card banner", "D2CD != 0", 0x3349, 0x334C, 0x334F),
        blk("labels_stage", "Special Stage card labels", "D2CD != 0", 0x3355, 0x3358, 0x335B),
        blk("panel_stage", "multiplier panel (same source as ordinary)", "D2CD != 0", 0x3361, 0x3364, 0x3367),
    ]
    icon_hl = _imm(rom, 0x337C, LDHL)
    icon_sonic = _imm(rom, 0x3374, LDDE)
    icon_other = _imm(rom, 0x3379, LDDE)
    icons = {}
    for key, src in (("sonic", icon_sonic), ("other", icon_other)):
        o = off(BANK_RESULTS, src)
        icons[key] = dict(source_cpu=hx(src, 4), source_file=hx(o, 5), tiles=list(rom[o:o + 4]), source_sha256=sha(rom[o:o + 4]))
    col0, row0 = cell(icon_hl)
    continues = dict(routine="$337F loop (initial) and $2F17..$2F39 (award during tally)", condition="D2C8 == 1 selects the 'sonic' icon", count="min(D2C3 & $7F, 8)",
                     icon=dict(cols=2, rows=2, entry_kind="tile id byte; attribute byte = D2D3"), icons=icons,
                     first_name_table_address=hx(icon_hl, 4), col0=col0, row0=row0, pitch_name_table_bytes=_imm(rom, 0x3397, 0x11),
                     pitch_cells=_imm(rom, 0x3397, 0x11) // 2)
    em_hl = _imm(rom, 0x33F9, LDHL)
    em_de = _imm(rom, 0x33FC, LDDE)
    ecol, erow = cell(em_hl)
    o = off(BANK_RESULTS, em_de)
    slots = []
    for i in range(5):
        raw = bytes(rom[o + 8 * i:o + 8 * i + 8])
        slots.append(dict(slot=i, source_cpu=hx(em_de + 8 * i, 4), source_file=hx(o + 8 * i, 5), col=ecol + 4 * i, row=erow,
                          entries=[raw[2 * k] | (raw[2 * k + 1] << 8) for k in range(4)], source_sha256=sha(raw)))
    emeralds = dict(routine="$33F1", condition="slot i drawn when bit i of D2CC is set (RRCA test), i = 0..4; bit 5 is never drawn here",
                    icon=dict(cols=2, rows=2, entry_kind="16-bit name-table entry from ROM (palette bit 11 included)"),
                    first_name_table_address=hx(em_hl, 4), pitch_name_table_bytes=_imm(rom, 0x3415, 0x11), slots=slots)
    # number fields
    glyph_o = off(BANK_RESULTS, _imm(rom, 0x2774, LDHL))
    glyphs = [dict(digit=("blank" if i == 10 else i), top=rom[glyph_o + 2 * i], bottom=rom[glyph_o + 2 * i + 1]) for i in range(11)]
    fields = [
        dict(id="rings", ram="D29A", bytes=1, digits=2, leading_zero_blank=1, type_code=1, draw_call="$26D6", name_table_address=hx(_imm(rom, 0x26DF, LDDE), 4)),
        dict(id="bonus", ram="D2A6", bytes=2, digits=4, leading_zero_blank=3, type_code=2, draw_call="$26E7", name_table_address=hx(_imm(rom, 0x26F0, LDDE), 4)),
        dict(id="score", ram="D29D", bytes=3, digits=6, leading_zero_blank=5, type_code=3, draw_call="$26F8", name_table_address=hx(_imm(rom, 0x270B, LDDE), 4)),
    ]
    for f in fields:
        a = int(f["name_table_address"], 16)
        f["col"], f["row"] = cell(a)
        f["cell"] = dict(cols=1, rows=2, note="digit n = glyph top tile at (col,row), bottom tile at (col,row+1); next digit one column right")
    score_zero_hl = _imm(rom, 0x271A, LDHL)
    zc, zr = cell(score_zero_hl)
    score_zero = dict(name_table_address=hx(score_zero_hl, 4), col=zc, row=zr, cols=1, rows=2, source_cpu=hx(_imm(rom, 0x2717, 0x11), 4),
                      note="always drawn after the score digits: glyph '0' (table index 0) via $2383; the score therefore reads six BCD digits + a fixed 0 (display factor x10)",
                      skipped_digits_when="D29D | D29E | D29F == 0 (digits are not drawn at all)")
    return dict(fill=fill, blocks=blocks, continues=continues, emeralds=emeralds, digit_glyph_table=dict(source_cpu=hx(_imm(rom, 0x2774, LDHL), 4),
                source_file=hx(glyph_o, 5), entries=glyphs, note="digit n: top tile id, bottom tile id; entry 10 is the blank used for zero suppression"),
                number_fields=fields, score_trailing_zero=score_zero)


def palette_records(rom):
    base = off(BANK_PALETTE, 0xB64D)
    recs = {}
    for idx in (3, 4, 5, TITLE_BG_RECORD):
        o = base + 16 * idx
        recs[str(idx)] = dict(file_start=hx(o, 5), cpu=hx(0xB64D + 16 * idx, 4), sms_colours=list(rom[o:o + 16]), sha256=sha(rom[o:o + 16]))
    return recs


def results_palette(rom):
    """The CRAM the card ends with: BG = record 3 (D492 +1 = 3), sprite = record 4 (D494 +1 = 4); verified against emulated CRAM."""
    recs = palette_records(rom)
    return recs["3"]["sms_colours"], recs["4"]["sms_colours"]


def static_census(rom):
    stream, _ = tile_stream_info(rom)
    plan = draw_plan(rom)
    return dict(
        format=1, rom_sha256=ROM_SHA256, base_commit=BASE_COMMIT,
        routines=[region(rom, n, b, a, e, r) for n, b, a, e, r in ROUTINES],
        tile_stream=stream, draw_plan=plan, act_title_card=title_plan(rom),
        palette_records=palette_records(rom),
        card_palette=dict(background_record=3, sprite_record=4, requests="$33AB: D492 := bit7|bit4, D493 := 3; D494 := bit7|bit4, D495 := 4"),
        boss_bonus_steps=[u16(rom, 0x2D84 + 2 * z) for z in range(6)],
        step_values_bcd=dict(ring=bytes(rom[0x27E5:0x27E8]).hex(), bonus=bytes(rom[0x27E2:0x27E5]).hex(), boss=bytes(rom[0x27EB:0x27EE]).hex(),
                             unused_27E8=bytes(rom[0x27E8:0x27EB]).hex()),
        sound_requests_in_path=dict(note="numbers only; meanings unresolved (U5)", tally_tick="B4 at $2F43 when (D110 & 15) == 0", clear_stop="00 at $14E3/$157A",
                                    stage_card="86 at $33C9 when D2CD == $FF (then 240-frame wait)"),
    )


# ------------------------------------------------------------------------------------------------------------------------------------------
# Act title card static decode
def _bank_bytes(rom, bank, cpu, n):  # noqa: E302
    o = off(bank, cpu)
    return bytes(rom[o:o + n])


def title_plan(rom):
    """Operands of the act title card (`$3175..$32C9`) read from the code bytes; maps read from bank 19."""
    LDHL, LDBC, LDDE = 0x21, 0x01, 0x11
    fills = []
    for hl, bc, de in ((0x317E, 0x3181, 0x3184), (0x318A, 0x318D, 0x3190), (0x3196, 0x3199, 0x319C)):
        a = _imm(rom, hl, LDHL)
        col, row = cell(a)
        fills.append(dict(name_table_address=hx(a, 4), row=row, words=_imm(rom, bc, LDBC), entry=_imm(rom, de, LDDE)))
    arrow_n = _imm(rom, 0x31E2, 0x06)
    arrows = []
    a_start = _imm(rom, 0x31E4, LDHL)
    b_start = _imm(rom, 0x31EA, LDHL)
    for name, start, bc_pc, de_pc, direction in (("arrow_left", a_start, 0x31FB, 0x31FE, -1), ("arrow_right", b_start, 0x3207, 0x320A, +1)):
        bc = _imm(rom, bc_pc, LDBC)
        src = _imm(rom, de_pc, LDDE)
        col, row = cell(start)
        arrows.append(dict(id=name, start_name_table_address=hx(start, 4), start_col=col, start_row=row, rows=bc >> 8, cols=bc & 0xFF, direction_cols_per_iteration=direction,
                           source_cpu=hx(src, 4), tiles=list(_bank_bytes(rom, BANK_RESULTS, src, (bc >> 8) * (bc & 0xFF)))))
    zone_tab = _imm(rom, 0x3231, LDHL)       # resident table at $32CA (bank independent)
    zone_ptrs = [u16(rom, zone_tab + 2 * z) for z in range(6)]
    z_cols = rom[0x3256 + 3]
    z_rows = rom[0x325A + 3]
    z_dest = _imm(rom, 0x324D, LDHL)
    zc, zr = cell(z_dest)
    zones = [dict(zone=z, source_cpu=hx(zone_ptrs[z], 4), tiles=list(_bank_bytes(rom, BANK_RESULTS, zone_ptrs[z], z_cols * z_rows)),
                  source_sha256=sha(_bank_bytes(rom, BANK_RESULTS, zone_ptrs[z], z_cols * z_rows))) for z in range(6)]
    a_ptrs = [_imm(rom, 0x3289, LDHL), _imm(rom, 0x3292, LDHL), _imm(rom, 0x3298, LDHL)]
    a_cols = rom[0x32AA + 3]
    a_rows = rom[0x32AE + 3]
    a_dest = _imm(rom, 0x32A1, LDHL)
    ac, ar = cell(a_dest)
    acts = [dict(act=i, source_cpu=hx(a_ptrs[i], 4), tiles=list(_bank_bytes(rom, BANK_RESULTS, a_ptrs[i], a_cols * a_rows)),
                 source_sha256=sha(_bank_bytes(rom, BANK_RESULTS, a_ptrs[i], a_cols * a_rows))) for i in range(3)]
    stream_cpu = _imm(rom, 0x7A1E, LDHL)
    o = off(BANK_RESULTS, stream_cpu)
    tiles = TD.decompress_tile_stream(rom, o)
    return dict(
        tile_stream=dict(bank=BANK_RESULTS, cpu_start=hx(stream_cpu, 4), file_start=hx(o, 5), tile_count=u16(rom, o + 2), vram_destination=hx(VRAM_TILES, 4),
                         decoded_sha256=sha(tiles), tile_sha256=[sha(tiles[i * 32:(i + 1) * 32]) for i in range(u16(rom, o + 2))]),
        fills=fills, arrow_iterations=arrow_n, arrow_delay_busy_loop=hx(_imm(rom, 0x31F1, LDBC), 4), arrows=arrows,
        zone_object=dict(type_byte=rom[0x3245 + 3], mode=0, cols=z_cols, rows=z_rows, steps=rom[0x325E + 3], dest_name_table_address=hx(z_dest, 4), col=zc, row=zr,
                         table_cpu=hx(zone_tab, 4), maps=zones, delay_busy_loop=hx(_imm(rom, 0x3271, LDBC), 4)),
        act_object=dict(type_byte=rom[0x3281 + 3], mode=1, cols=a_cols, rows=a_rows, steps=rom[0x32B2 + 3], start_name_table_address=hx(a_dest, 4), start_col=ac, start_row=ar,
                        maps=acts, delay_busy_loop=hx(_imm(rom, 0x32BD, LDBC), 4)),
        palette_record=rom[0x31AA + 1], sound_request="%02X" % rom[0x31AC + 1], waits=dict(after_fade_request=rom[0x31B1 + 1], hold=rom[0x31C4 + 1], after_fade_out=rom[0x31D9 + 1],
                                                                                   skip_mask="%02X on D137" % rom[0x31CD + 1]),
        attribute_d2d3=rom[0x31BA],
    )


# Composer: Python image of the ROM draw routines
def bcd_digits(raw_bytes, ndigits):
    """Digits most significant first (the order the ROM draws them); None if any nibble > 9 (the ROM then draws nothing)."""
    ds = []
    for b in raw_bytes:
        lo, hi = b & 15, b >> 4
        if lo > 9 or hi > 9:
            return None
        ds.extend([lo, hi])
    return list(reversed(ds))[-ndigits:] if len(ds) >= ndigits else list(reversed(ds))


def field_cells(plan, field, raw_bytes):
    """[(col,row,top,bottom)] for one number field, honouring the ROM's leading-zero rule."""
    glyph = {g["digit"]: g for g in plan["digit_glyph_table"]["entries"]}
    ds = bcd_digits(raw_bytes, field["digits"])
    if ds is None:
        return []
    out = []
    suppress = field["leading_zero_blank"]
    for i, d in enumerate(ds):
        if suppress and d == 0:
            suppress -= 1
            g = glyph["blank"]
        else:
            suppress = 0
            g = glyph[d]
        out.append((field["col"] + i, field["row"], g["top"], g["bottom"]))
    return out


def compose_name_table(plan, *, d2c8, d2cd, continues, emeralds, rings, bonus, score, d2d3=1, continue_awards=()):
    """32x24 grid of 16-bit name-table words after the card (and tally) has drawn.

    d2c8: 1 = Sonic banner/icons, anything else the other set. d2cd: 0 ordinary card, non-zero stage card. continues: D2C3 (bit 7 ignored).
    rings: D29A (BCD). bonus: D2A6 (16-bit BCD). score: [D29D, D29E, D29F] (low byte first).
    continue_awards: old D2C3 values at each award made during the tally (each draws one more icon).
    """
    nt = [[plan["fill"]["entry"]] * 32 for _ in range(24)]

    def put_tile1(b):
        for r in range(b["rows"]):
            for c in range(b["cols"]):
                nt[b["row"] + r][b["col"] + c] = (d2d3 << 8) | b["tiles"][r * b["cols"] + c]

    ids = {b["id"]: b for b in plan["blocks"]}
    if d2cd == 0:
        put_tile1(ids["banner_sonic" if d2c8 == 1 else "banner_other"])
        put_tile1(ids["labels_ordinary"])
        put_tile1(ids["panel_ordinary"])
    else:
        put_tile1(ids["banner_stage"])
        put_tile1(ids["labels_stage"])
        put_tile1(ids["panel_stage"])
    # continue icons (initial draw: min(count,8))
    cont = plan["continues"]
    n = min(continues & 0x7F, 8)
    icon = cont["icons"]["sonic" if d2c8 == 1 else "other"]["tiles"]
    for i in range(n):
        for r in range(2):
            for c in range(2):
                nt[cont["row0"] + r][cont["col0"] + 2 * i + c] = (d2d3 << 8) | icon[r * 2 + c]
    # awards during the tally ($2F17..$2F39): new icon at index min(old count & $7F, 8)
    for old in continue_awards:
        k = min(old & 0x7F, 8)
        for r in range(2):
            for c in range(2):
                nt[cont["row0"] + r][cont["col0"] + 2 * k + c] = (d2d3 << 8) | icon[r * 2 + c]
    # emeralds
    for s in plan["emeralds"]["slots"]:
        if emeralds >> s["slot"] & 1:
            for k, e in enumerate(s["entries"]):
                nt[s["row"] + k // 2][s["col"] + k % 2] = e
    # numbers
    for f in plan["number_fields"]:
        if f["id"] == "rings":
            raw = [rings]
        elif f["id"] == "bonus":
            raw = [bonus & 0xFF, bonus >> 8]
        else:
            raw = list(score)
            if not any(raw):
                continue
        for col, row, top, bottom in field_cells(plan, f, raw):
            nt[row][col] = (d2d3 << 8) | top
            nt[row + 1][col] = (d2d3 << 8) | bottom
    z = plan["score_trailing_zero"]
    g0 = next(g for g in plan["digit_glyph_table"]["entries"] if g["digit"] == 0)
    nt[z["row"]][z["col"]] = (d2d3 << 8) | g0["top"]
    nt[z["row"] + 1][z["col"]] = (d2d3 << 8) | g0["bottom"]
    return nt


class NameTable:
    """Byte-exact model of the VDP name table as written through `$2383` / `$1D8A` (camera at 0,0)."""

    def __init__(self, fill=0):
        self.b = bytearray(0x700)

    def write(self, addr, value):
        self.b[(addr & 0x3FFF) - 0x3800] = value

    def words(self):
        return [[self.b[(r * 32 + c) * 2] | (self.b[(r * 32 + c) * 2 + 1] << 8) for c in range(32)] for r in range(24)]


def draw_1byte(nt, hl, src, rows, cols, attr):
    """`$2383`: one tile byte per cell plus the constant attribute D2D3; reproduces the ROM's row-wrap bookkeeping (HL advances one byte per cell, the VDP two)."""
    hl &= ~1                              # `$23C7` with the camera at (0,0) only clears bit 0
    de = 0
    for _ in range(rows):
        row_hl = hl
        v = hl
        cur = hl
        for _k in range(cols):
            nt.write(v, src[de])
            nt.write(v + 1, attr)
            v += 2
            de += 1
            cur += 1
            if (cur & 0x3F) == 0:
                cur -= 0x40
                v = cur
        hl = row_hl + 0x40
        if (hl >> 8) == 0x3F:
            hl = (hl & 0xFF) | 0x3800
    return nt


def fill_words(nt, addr, count, word):
    """`$1D8A`: `count` identical 16-bit entries from `addr` (low byte first)."""
    for i in range(count):
        nt.write(addr + 2 * i, word & 0xFF)
        nt.write(addr + 2 * i + 1, word >> 8)


def title_states(tp, zone, act):
    """Name-table words after every observable step of the act title card, in ROM order.

    Returns [(label, words)] with labels ('fills'), ('arrow', i), ('zone', n), ('act', n).  The attribute byte is `D2D3` = 1.
    """
    attr = tp["attribute_d2d3"]
    nt = NameTable()
    for f in tp["fills"]:
        fill_words(nt, int(f["name_table_address"], 16), f["words"], f["entry"])
    out = [("fills", nt.words())]
    a, b = tp["arrows"]
    da, db = int(a["start_name_table_address"], 16), int(b["start_name_table_address"], 16)
    for i in range(tp["arrow_iterations"]):
        draw_1byte(nt, da, a["tiles"], a["rows"], a["cols"], attr)
        draw_1byte(nt, db, b["tiles"], b["rows"], b["cols"], attr)
        da -= 2
        db += 2
        out.append((("arrow", i + 1), nt.words()))
    z = tp["zone_object"]
    zmap = z["maps"][zone]["tiles"]
    ln = z["steps"]
    for n in range(1, z["steps"] + 1):      # mode 0: IX+1F counts up, IX+1E counts down; source = base + 2*((IX+1E) >> 1)
        left = z["steps"] - n
        src_off = 2 * (left >> 1)
        width = min(n, z["cols"])
        dest = int(z["dest_name_table_address"], 16)
        for r in range(z["rows"]):
            draw_1byte(nt, dest + 0x40 * r, zmap[r * z["cols"] + src_off:], 1, width, attr)
        out.append((("zone", n), nt.words()))
    o = tp["act_object"]
    amap = o["maps"][act]["tiles"]
    dest = int(o["start_name_table_address"], 16)
    for n in range(1, o["steps"] + 1):      # mode 1: source constant, destination moves one column left per update
        width = min(n, o["cols"])
        for r in range(o["rows"]):
            draw_1byte(nt, dest + 0x40 * r, amap[r * o["cols"]:], 1, width, attr)
        dest -= 2
        out.append((("act", n), nt.words()))
    return out


def tiles_from_decoded(decoded):
    """List of 8x8 index arrays (planar bitplane order of the SMS Mode 4 pattern)."""
    out = []
    for t in range(len(decoded) // 32):
        px = []
        for r in range(8):
            b0, b1, b2, b3 = decoded[t * 32 + r * 4:t * 32 + r * 4 + 4]
            px.append([((b0 >> (7 - x)) & 1) | (((b1 >> (7 - x)) & 1) << 1) | (((b2 >> (7 - x)) & 1) << 2) | (((b3 >> (7 - x)) & 1) << 3) for x in range(8)])
        out.append(px)
    return out


def render_indexed(nt, tiles, first_tile=TILE_BASE):
    """192 rows of 256 palette indices (0..31: +16 when the entry selects the sprite palette) from a 32x24 grid of name-table words."""
    img = [[0] * 256 for _ in range(192)]
    for ty in range(24):
        for tx in range(32):
            w = nt[ty][tx]
            t = (w & 0x1FF) - first_tile
            if not 0 <= t < len(tiles):
                raise ValueError("tile %d outside the loaded stream" % (w & 0x1FF))
            pal = 16 if w & 0x0800 else 0
            hf, vf = w & 0x0200, w & 0x0400
            for r in range(8):
                src = tiles[t][7 - r if vf else r]
                for x in range(8):
                    img[ty * 8 + r][tx * 8 + x] = pal + src[7 - x if hf else x]
    return img


# ------------------------------------------------------------------------------------------------------------------------------------------
# Fade engine model ($B45A..$B63D).  Channels are 2-bit; a palette entry is %00BBGGRR.
def _ch(c):
    return c & 3, (c >> 2) & 3, (c >> 4) & 3


def _pk(r, g, b):
    return r | (g << 2) | (b << 4)


def fade_pass(kind, cur, target, step):
    """One engine pass over 16 entries.

    kind: 'to_white' (slot bit6|bit4), 'to_black' (bit6), 'in_black' (bit7: climb from black to `target`, `step` = pass counter 0..3),
          'in_white' (bit7|bit4: from the current colours one level per pass towards `target`).
    """
    out = []
    for i in range(16):
        c = _ch(cur[i])
        t = _ch(target[i]) if target is not None else (0, 0, 0)
        if kind == "to_white":
            n = tuple(min(3, x + 1) for x in c)
        elif kind == "to_black":
            n = tuple(max(0, x - 1) for x in c)
        elif kind == "in_black":
            n = tuple(max(0, step - (3 - x)) for x in t)
        elif kind == "in_white":
            n = tuple((x - 1) & 3 if x != y else x for x, y in zip(c, t))
        else:
            raise ValueError(kind)
        out.append(_pk(*n))
    return out


TITLE_BG_RECORD = 0x21     # `$31A9`: D493 := $21 for the act title card
FADE_PASSES = dict(to_white=3, to_black=3, in_black=4, in_white=4)


def fade_series(kind, start, target=None):
    """Palette (16 entries) after each pass; the engine finishes (slot cleared) after FADE_PASSES[kind] passes."""
    states, cur = [], list(start)
    for p in range(FADE_PASSES[kind]):
        cur = fade_pass(kind, cur, target, p if kind == "in_black" else 0)
        states.append(cur)
    return states


def sms_rgb(c):
    r, g, b = _ch(c)
    return (r * 85, g * 85, b * 85)


# ------------------------------------------------------------------------------------------------------------------------------------------
# Exports (ignored build/u4): deterministic indexed graphics
def _png_indexed(path, w, h, rows, palette32):
    from PIL import Image
    im = Image.new("P", (w, h))
    pal = []
    for c in palette32:
        pal.extend(sms_rgb(c))
    pal.extend([0] * (768 - len(pal)))
    im.putpalette(pal)
    im.putdata([v for row in rows for v in row])
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, optimize=False, compress_level=9)


def _rows_hash(rows):
    return sha(bytes(v for row in rows for v in row))


def block_rows(tiles, entries, cols, rows, attr_hi=1, one_byte=True):
    """Indexed rows for a tilemap block rendered alone."""
    nt = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            e = entries[r * cols + c]
            nt[r][c] = (attr_hi << 8 | e) if one_byte else e
    out = [[0] * (cols * 8) for _ in range(rows * 8)]
    for ty in range(rows):
        for tx in range(cols):
            w = nt[ty][tx]
            t = (w & 0x1FF) - TILE_BASE
            pal = 16 if w & 0x0800 else 0
            hf, vf = w & 0x0200, w & 0x0400
            for r in range(8):
                src = tiles[t][7 - r if vf else r]
                for x in range(8):
                    out[ty * 8 + r][tx * 8 + x] = pal + src[7 - x if hf else x]
    return out


def export_assets(rom, census=None, out=BUILD):
    """Write the indexed exports; returns the manifest (hashes of raw index data, never of PNG bytes)."""
    census = census or static_census(rom)
    plan = census["draw_plan"]
    stream, decoded = tile_stream_info(rom)
    tiles = tiles_from_decoded(decoded)
    bg, spr = results_palette(rom)
    pal32 = bg + spr
    manifest = dict(format=1, rom_sha256=ROM_SHA256, rows_hash="sha256 of the row-major palette-index bytes (0..31)", assets={})

    def add(name, rows, kind, note=""):
        h, w = len(rows), len(rows[0])
        _png_indexed(out / name, w, h, rows, pal32)
        manifest["assets"][name] = dict(kind=kind, width=w, height=h, index_sha256=_rows_hash(rows), note=note)

    # tile sheet: 16 tiles per row, tile 0 of the sheet = tile index 256
    sheet = [[0] * 128 for _ in range(((len(tiles) + 15) // 16) * 8)]
    for t, px in enumerate(tiles):
        for r in range(8):
            for x in range(8):
                sheet[(t // 16) * 8 + r][(t % 16) * 8 + x] = px[r][x]
    add("card_tiles_vram2000.png", sheet, "tile sheet", "160 tiles, 16 per row, tile index = 256 + sheet position; palette indices 0..15 (BG record 3)")
    for b in plan["blocks"]:
        add("blocks/%s.png" % b["id"], block_rows(tiles, b["tiles"], b["cols"], b["rows"]), "tilemap block", "attribute high byte D2D3 = 1; BG palette")
    for key in ("sonic", "other"):
        ic = plan["continues"]["icons"][key]
        add("blocks/continue_icon_%s.png" % key, block_rows(tiles, ic["tiles"], 2, 2), "icon")
    for s in plan["emeralds"]["slots"]:
        add("blocks/emerald_icon_%d.png" % s["slot"], block_rows(tiles, s["entries"], 2, 2, one_byte=False), "icon", "entries carry palette bit 11 (sprite palette indices 16..31)")
    glyph_rows = [[0] * (11 * 8) for _ in range(16)]
    for g in plan["digit_glyph_table"]["entries"]:
        i = 0 if g["digit"] == "blank" and False else (10 if g["digit"] == "blank" else g["digit"])
        col = block_rows(tiles, [g["top"], g["bottom"]], 1, 2)
        for r in range(16):
            for x in range(8):
                glyph_rows[r][i * 8 + x] = col[r][x]
    add("blocks/digit_glyphs.png", glyph_rows, "glyph strip", "0..9 then the blank used for zero suppression; each glyph 8x16")
    fill = block_rows(tiles, [plan["fill"]["entry"] & 0xFF], 1, 1, attr_hi=plan["fill"]["entry"] >> 8)
    add("blocks/screen_fill_tile.png", fill, "tile")
    # composed frames used by the verification (deterministic compose, same function the tests compare with the emulator)
    variants = dict(
        sonic_static=dict(d2c8=1, d2cd=0, continues=0, emeralds=0, rings=0, bonus=0, score=[0, 0, 0]),
        sonic_example=dict(d2c8=1, d2cd=0, continues=3, emeralds=0x1F, rings=0x25, bonus=0x0914, score=[0x50, 0x34, 0x12]),
        other_static=dict(d2c8=2, d2cd=0, continues=0, emeralds=0, rings=0, bonus=0, score=[0, 0, 0]),
        other_example=dict(d2c8=2, d2cd=0, continues=3, emeralds=0x1F, rings=0x25, bonus=0x0914, score=[0x50, 0x34, 0x12]),
        stage_static=dict(d2c8=1, d2cd=1, continues=0, emeralds=0, rings=0, bonus=0, score=[0, 0, 0]),
    )
    for name, kw in variants.items():
        nt = compose_name_table(plan, **kw)
        add("frames/%s.png" % name, render_indexed(nt, tiles), "composed 256x192 frame", json.dumps(kw, sort_keys=True))
    # act title card (VRAM $2000 is reloaded with the 95-tile title stream; BG palette = record $21)
    tp = census["act_title_card"]
    tdec = TD.decompress_tile_stream(rom, int(tp["tile_stream"]["file_start"], 16))
    ttiles = tiles_from_decoded(tdec)
    tpal = palette_records(rom)[str(TITLE_BG_RECORD)]["sms_colours"] + [0] * 16

    def add_t(name, rows, kind, note=""):
        h, w = len(rows), len(rows[0])
        _png_indexed(out / name, w, h, rows, tpal)
        manifest["assets"][name] = dict(kind=kind, width=w, height=h, index_sha256=_rows_hash(rows), note=note)
    tsheet = [[0] * 128 for _ in range(((len(ttiles) + 15) // 16) * 8)]
    for t, px in enumerate(ttiles):
        for r in range(8):
            for x in range(8):
                tsheet[(t // 16) * 8 + r][(t % 16) * 8 + x] = px[r][x]
    add_t("title/title_tiles_vram2000.png", tsheet, "tile sheet", "95 tiles, 16 per row, tile index = 256 + sheet position; palette = BG record $21")
    for z in tp["zone_object"]["maps"]:
        add_t("title/zone_name_%d.png" % z["zone"], block_rows(ttiles, z["tiles"], tp["zone_object"]["cols"], tp["zone_object"]["rows"]), "tilemap block", "32x4 name-table block as drawn at col 0,row 7")
    for a in tp["act_object"]["maps"]:
        add_t("title/act_number_%d.png" % a["act"], block_rows(ttiles, a["tiles"], tp["act_object"]["cols"], tp["act_object"]["rows"]), "tilemap block", "12x4 block; final column = start column 31 minus 20")
    for a in tp["arrows"]:
        add_t("title/%s.png" % a["id"], block_rows(ttiles, a["tiles"], a["cols"], a["rows"]), "tilemap block")
    for zone in range(6):
        for act in range(3):
            if zone == 5 and act == 2:
                pass
            states = title_states(tp, zone, act)
            add_t("title/frame_zone%d_act%d.png" % (zone, act), render_indexed(states[-1][1], ttiles), "composed 256x192 final title frame", "name table after the last animator update (hold)")
    # fade ramps (RGB) for the card
    ramps = fade_ramps(rom, census)
    (out).mkdir(parents=True, exist_ok=True)
    (out / "palettes.json").write_text(json.dumps(dict(
        note="SMS 2-bit channels %00BBGGRR; rgb = channel * 85 (the accepted harness expansion; hardware DAC levels are an adapter choice)",
        card_background=dict(sms=bg, rgb=[sms_rgb(c) for c in bg]), card_sprite=dict(sms=spr, rgb=[sms_rgb(c) for c in spr]), ramps=ramps), indent=1, sort_keys=True), encoding="utf-8", newline="\n")
    manifest["assets"]["palettes.json"] = dict(kind="palettes+ramps", sha256=sha((out / "palettes.json").read_bytes()))
    return manifest


def fade_ramps(rom, census=None):
    bg, spr = results_palette(rom)
    white = [0x3F] * 16
    return dict(
        card_fade_in_from_white=dict(kind="in_white", background=[s for s in fade_series("in_white", white, bg)], sprite=[s for s in fade_series("in_white", white, spr)]),
        card_to_white=dict(kind="to_white", background=fade_series("to_white", bg), sprite=fade_series("to_white", spr)),
        white_to_black=dict(kind="to_black", background=fade_series("to_black", white), sprite=fade_series("to_black", white)),
    )


# ------------------------------------------------------------------------------------------------------------------------------------------
# Emulated observation (needs Python >= 3.10 and the `z80` package)
CLEAR_MARKS_ORD = {0x14AE: "clear_entry", 0x14B6: "anim_freeze", 0x14BE: "fade_white_request", 0x14D8: "sound_regs", 0x14E3: "sound_stop", 0x14E8: "object_clear",
                   0x14FC: "card_call", 0x14FF: "post_card_wait", 0x1507: "tail_white_request", 0x1521: "white_fill", 0x1524: "black_request",
                   0x152F: "progress", 0x1534: "act_incremented"}
CLEAR_MARKS_ZONE = {0x1543: "clear_entry", 0x154B: "anim_freeze", 0x1553: "fade_white_request", 0x156D: "sound_regs", 0x157A: "sound_stop", 0x1580: "object_clear",
                    0x1594: "zone_gate", 0x159B: "card_call", 0x159E: "post_card_wait", 0x15A6: "tail_white_request", 0x15C0: "white_fill", 0x15C3: "black_request",
                    0x15CE: "progress", 0x15D6: "zone_store"}
CARD_MARKS = {0x32F9: "card_start", 0x3308: "card_fill", 0x336D: "card_icons", 0x33A2: "card_numbers", 0x33AB: "card_fade_in_request", 0x33C9: "stage_sound",
              0x33D6: "card_wait60", 0x33E2: "tally_call", 0x33E8: "tally_return", 0x2D55: "boss_bonus_call", 0x2D08: "ring_loop_enter", 0x2D54: "tally_end"}
TITLE_MARKS = {0x1673: "level_reload_start", 0x2934: "level_loader", 0x794F: "level_fade_in_request", 0x189B: "level_music_request", 0x168E: "level_reload_done",
               0x3175: "title_start", 0x31A2: "title_fills_done", 0x31AC: "title_sound", 0x31BE: "title_arrows_start", 0x31C1: "title_text_start", 0x31C4: "title_hold_start",
               0x31D3: "title_hold_end", 0x31E1: "title_return"}
# hot addresses (hit once per tally step): hooks perturb the harness's cycle accounting, so they are only attached when step cadence is the question
STEP_MARKS = {0x2D18: "ring_step", 0x2D44: "bonus_step", 0x2D6A: "boss_step"}


def nt_hash(words):
    """SHA-256 of a 24x32 grid of 16-bit name-table words, little-endian, row-major."""
    return sha(bytes(x for row in words for w in row for x in (w & 255, w >> 8)))


def nt_words(vram):
    return [[vram[NAME_TABLE + (r * 32 + c) * 2] | (vram[NAME_TABLE + (r * 32 + c) * 2 + 1] << 8) for c in range(32)] for r in range(24)]


def _import_rig():
    import g0_rig
    import g0_scenarios
    return g0_rig, g0_scenarios


def run_clear(rom, *, character=0, zone=0, act=0, rings=0x25, pre=None, card_override=None, hold_during_tally=None, step_hooks=False, tail_frames=70):
    """One act clear through the original ROM; returns (facts, raw).

    THZ1 uses the real goal-sign chain; every other (zone, act) raises the act-clear flag (bit 5, or bit 4 for act index 2) 60 frames after the act is in
    play (RAM fixture; everything after the flag is unmodified ROM).  `pre` = {RAM name or int address: byte} written once the act is in play.
    `card_override` writes D2CD at `$32F9` entry (CONTROLLED variant: the stage-card branch of the same routine).
    `hold_during_tally` = joypad mask held from `$33E2` on (the tally skips its delay while a button is down).
    """
    rig, _ = _import_rig()
    Session, RAM = rig.Session, rig.RAM
    S = Session(rom)
    sm = S.s
    ev = []                       # (frame, name, pc)
    snaps = {}
    marks = {}
    marks.update(CLEAR_MARKS_ORD)
    marks.update({a: n for a, n in CLEAR_MARKS_ZONE.items() if a not in marks})
    marks[0x1543] = "clear_entry_zone"
    marks.update(CARD_MARKS)
    marks.update(TITLE_MARKS)
    if step_hooks:
        marks.update(STEP_MARKS)

    def mk(name):
        def f(mm):
            ev.append((mm.frame, name, mm.cpu.pc))
        return f
    for a, n in marks.items():
        S.hook(a, mk(n))

    def snap(name, render):
        def f(mm):
            d = dict(frame=mm.frame, vram=bytes(mm.vram), cram=bytes(mm.cram), reg=list(mm.reg), ram=bytes(mm.mem[0xD000:0xE000]), bg=None, sprite_pixels=None)
            if render:
                _, layer, bg_index, _ = mm.render()
                d["bg"] = [list(r) for r in bg_index]
                d["sprite_pixels"] = sum(row.count("S") for row in layer)
            snaps[name] = d
        return f
    for a, n, r in ((0x32F9, "at_card_start", False), (0x33AB, "at_numbers_done", False), (0x33E2, "at_tally_call", True), (0x2D08, "at_ring_loop", False),
                    (0x33E8, "at_tally_return", True)):
        S.hook(a, snap(n, r))
    freeze = {}

    def frz(name):
        def f(mm):
            freeze[name] = dict(frame=mm.frame, nt=sha(bytes(mm.vram[NAME_TABLE:NAME_TABLE + 0x700])), sat=sha(bytes(mm.vram[0x3F00:0x4000])), reg=list(mm.reg),
                                camera=[mm.u16(0xD174), mm.u16(0xD176)], player=[mm.u16(0xD511), mm.u16(0xD514)], tick=mm.mem[0xD135])
        return f
    for a, n in ((0x14AE, "entry"), (0x1543, "entry"), (0x14BE, "t60"), (0x1553, "t60"), (0x14E8, "t186"), (0x1580, "t186")):
        S.hook(a, frz(n))
    buf = {}
    for a in (0x14BE, 0x1553):
        S.hook(a, lambda mm: buf.__setitem__("request", bytes(mm.mem[0xD472:0xD492])))
    titles = {}

    def title_hit(label):
        def f(mm):
            key = (mm.mem[0xD297], mm.mem[0xD298])
            t = titles.setdefault(key, dict(hits=[], states=[], hold=None))
            t["hits"].append((mm.frame, label))
            if label[0] in ("fills", "arrow", "zone", "act"):
                t["states"].append((label, nt_words(mm.vram)))
            if label == "hold":
                t["hold"] = dict(vram_tiles=bytes(mm.vram[VRAM_TILES:VRAM_TILES + 0x1800]), cram=bytes(mm.cram), reg=list(mm.reg))
        return f
    arrow_i, zone_n, act_n = [0], [0], [0]

    def counted(counter, kind):
        def f(mm):
            counter[0] += 1
            title_hit((kind, counter[0]))(mm)
        return f
    S.hook(0x31A2, lambda mm: (arrow_i.__setitem__(0, 0), zone_n.__setitem__(0, 0), act_n.__setitem__(0, 0), title_hit(("fills",))(mm)))
    S.hook(0x3211, counted(arrow_i, "arrow"))
    S.hook(0x3271, counted(zone_n, "zone"))
    S.hook(0x32BD, counted(act_n, "act"))
    S.hook(0x31C4, title_hit("hold"))
    if card_override is not None:
        S.hook(0x32F9, lambda mm: mm._write(0xD2CD, card_override))
    S.watch(0xDE04, 0xD2C3)
    if (zone, act) != (0, 0):
        S.set_start_index(zone, act)
    S.boot_new_game(character=character, arrival=(Session.place_at_sign(0) if (zone, act) == (0, 0) else None))
    S.cram_trace()
    preset = {"rings": rings, "powerup": 0x04, "emeralds": 0x03}
    preset.update(pre or {})
    for k, v in preset.items():
        if isinstance(k, str) and k in RAM:
            S.w(k, v)
        else:
            sm._write(int(k), v & 0xFF)
    sm.w16(0xD44C, 0x0100)
    if (zone, act) == (0, 0):
        S.run_until(lambda s: s.m[0xD293] & 0x30, pad=lambda s: rig.BTN_RIGHT if s.m[0xD501] != 0x20 else 0, limit=3000)
        how = "real goal-sign chain (ARRIVAL fixture 160 px before the sign, PAD right)"
    else:
        S.run(60)
        sm._write(0xD293, S.m[0xD293] | (0x10 if act == 2 else 0x20))
        how = "act-clear flag raised 60 frames after the act is in play (RAM fixture)"
    flag_frame = sm.frame

    def pad(s):
        if hold_during_tally is not None and any(n == "tally_call" for _, n, _ in ev):
            return hold_during_tally
        return 0
    if zone >= 5 and act == 2:
        S.run(1500)
    else:
        nz, na = (zone, act + 1) if act < 2 else (zone + 1, 0)
        S.run_until(lambda s: s.m[0xD297] == nz and s.m[0xD298] == na and s.playing(), pad=pad, limit=6000)
        S.run(tail_frames)
    t0 = next((f for f, n, _ in ev if n in ("clear_entry", "clear_entry_zone") and f >= flag_frame), None)
    window = [bytes(c) for f, c in S.cram_log if t0 <= f < t0 + 60]
    before = next((bytes(c) for f, c in reversed(S.cram_log) if f < t0), None)
    animated = sorted(i for i in range(32) if len({w[i] for w in window + ([before] if before else [])}) > 1)
    facts = dict(zone=zone, act=act, character=character, how=how, animated_cram_entries=animated, flag_to_clear_entry=(t0 - flag_frame) if t0 is not None else None,
                 events=_first_events(ev, t0),
                 steps=_step_stats(ev, t0), cram_before=next((c.hex() for f, c in reversed(S.cram_log) if f < t0), None), palette_buffer_at_fade_request=buf["request"].hex(),
                 cram=[[f - t0, c.hex()] for f, c in S.cram_log if f >= t0],
                 writes=[[f - t0, hex(a), v] for f, a, v in S.writes if f >= t0 and not (a == 0xDE04 and v == 0)])
    return facts, dict(snaps=snaps, ev=ev, t0=t0, S=S, titles=titles, freeze=freeze)


def _first_events(ev, t0):
    seen, out = set(), []
    for f, n, _ in ev:
        if f >= t0 and n not in seen and n not in STEP_MARKS.values():
            seen.add(n)
            out.append([f - t0, n])
    return out


def _step_stats(ev, t0):
    out = {}
    for name in ("ring_step", "bonus_step", "boss_step"):
        frames = [f - t0 for f, n, _ in ev if n == name and f >= t0]
        if not frames:
            continue
        per = {}
        for f in frames:
            per[f] = per.get(f, 0) + 1
        vals = list(per.values())
        out[name] = dict(count=len(frames), first=frames[0], last=frames[-1], frames_spanned=frames[-1] - frames[0] + 1,
                         steps_per_frame_min=min(vals), steps_per_frame_max=max(vals), mean=round(len(frames) / (frames[-1] - frames[0] + 1), 3))
    return out


# ------------------------------------------------------------------------------------------------------------------------------------------
# Verification of one run against the compose / fade models
RAMX = dict(char=0xD2C8, cont=0xD2C3, emer=0xD2CC, card=0xD2CD, d2d3=0xD2D3, rings=0xD29A, bonus=0xD2A6, score=0xD29D, zone=0xD297, act=0xD298)


def _g(snap, a):
    return snap["ram"][a - 0xD000]


def _params(snap, d2cd):
    return dict(d2c8=_g(snap, 0xD2C8), d2cd=d2cd, continues=_g(snap, 0xD2C3), emeralds=_g(snap, 0xD2CC), rings=_g(snap, 0xD29A),
                bonus=_g(snap, 0xD2A6) | (_g(snap, 0xD2A7) << 8), score=[_g(snap, 0xD29D), _g(snap, 0xD29E), _g(snap, 0xD29F)], d2d3=_g(snap, 0xD2D3))


def act_palette_indices(rom, zone, act):
    """(background record, sprite record) the level loader requests (`$794F`: table at $7F3C, two bytes per (3*zone+act))."""
    o = 0x7F3C + 2 * (3 * zone + act)
    return rom[o], rom[o + 1]


def expected_fade_states(rom, buffer_at_request, nxt):
    """Ordered list of 32-byte CRAM states the engine should produce after the clear entry (consecutive duplicates removed).

    `buffer_at_request` is the palette buffer D472..D491 when the first fade is requested (the engine works on the buffer; palette-cycling code writes CRAM
    directly, so for animated acts CRAM and buffer differ in the cycled entries)."""
    bg, spr = results_palette(rom)
    white = [0x3F] * 16
    pre_bg, pre_spr = list(buffer_at_request[:16]), list(buffer_at_request[16:])
    seq = []

    def add(kind, b0, s0, bt=None, st=None):
        sb = fade_series(kind, b0, bt)
        ss = fade_series(kind, s0, st)
        for x, y in zip(sb, ss):
            seq.append(x + y)
        return sb[-1], ss[-1]
    b, sp = add("to_white", pre_bg, pre_spr)
    b, sp = add("in_white", white, white, bg, spr)
    b, sp = add("to_white", b, sp)
    b, sp = add("to_black", white, white)
    # act title card ($3175, every act load): BG in from black to record $21 (D492 only), then $1CAF fades both slots to black
    rec = lambda i: list(rom[off(BANK_PALETTE, 0xB64D) + 16 * i:off(BANK_PALETTE, 0xB64D) + 16 * i + 16])
    black = [0] * 16
    for st in fade_series("in_black", black, rec(TITLE_BG_RECORD)):
        seq.append(st + black)
    for st in fade_series("to_black", rec(TITLE_BG_RECORD)):
        seq.append(st + black)
    nb, ns = act_palette_indices(rom, *nxt)
    add("in_black", black, black, rec(nb), rec(ns))
    out = []
    prev = None
    for st in seq:
        if st != prev:
            out.append(bytes(st))
        prev = st
    return out


def check_run(rom, plan, tiles, decoded, facts, raw, *, card=0, nxt=None, fades=True):
    snaps = raw["snaps"]
    res = {}
    t = snaps["at_tally_call"]
    r = snaps["at_tally_return"]
    awards = []
    cur = _g(snaps["at_numbers_done"], 0xD2C3)
    tally_rel = snaps["at_tally_call"]["frame"] - raw["t0"]
    for f, a, v in facts["writes"]:
        if a == hex(0xD2C3) and f >= tally_rel and v != cur:
            awards.append(cur)
            cur = v
    res["continue_award_old_counts"] = awards
    c0 = _params(snaps["at_numbers_done"], card)
    for name, snap in (("tally_call", t), ("tally_return", r)):
        pr = _params(snap, card)
        pr["continue_awards"] = awards if name == "tally_return" else []
        pr["continues"] = c0["continues"]
        nt = compose_name_table(plan, **pr)
        res["%s_name_table_equals_compose" % name] = nt_words(snap["vram"]) == nt
        res["%s_background_index_equals_compose" % name] = (snap["bg"] == render_indexed(nt, tiles)) if snap["bg"] is not None else None
        res["%s_sprite_pixels" % name] = snap["sprite_pixels"]
    res["tiles_equal_decoded_stream"] = t["vram"][VRAM_TILES:VRAM_TILES + len(decoded)] == decoded
    bgp, spp = results_palette(rom)
    res["cram_equals_palette_records_3_4"] = list(t["cram"]) == bgp + spp
    res["registers_at_card"] = dict(zip(("R0", "R1", "R2", "R5", "R7", "R8", "R9", "R10"), (t["reg"][i] for i in (0, 1, 2, 5, 7, 8, 9, 10))))
    res["d2d3"] = _g(t, 0xD2D3)
    res["name_table_sha256_at_tally_call"] = nt_hash(nt_words(t["vram"]))
    if fades and nxt is not None and facts["palette_buffer_at_fade_request"]:
        animated = set(facts["animated_cram_entries"])
        mask = lambda b: bytes(0 if i in animated else v for i, v in enumerate(b))
        exp = []
        for x in expected_fade_states(rom, bytes.fromhex(facts["palette_buffer_at_fade_request"]), nxt):
            if not exp or mask(x) != exp[-1]:
                exp.append(mask(x))
        prev = mask(bytes.fromhex(facts["cram_before"]))
        ded = []
        for f, c in facts["cram"]:
            m = mask(bytes.fromhex(c))
            if m != prev:
                ded.append(m)
                prev = m
        res["fade_sequence_equals_model"] = ded[:len(exp)] == exp
        res["fade_states_observed_total"] = len(ded)
        res["fade_states_modelled"] = len(exp)
        res["palette_cycled_entries_masked"] = sorted(animated)
    return res


def check_title(rom, tp, raw):
    """Frame-exact comparison of the act title card: ROM-order name-table states, tile data and palette at the hold."""
    decoded = TD.decompress_tile_stream(rom, int(tp["tile_stream"]["file_start"], 16))
    rec = list(rom[off(BANK_PALETTE, 0xB64D) + 16 * tp["palette_record"]:off(BANK_PALETTE, 0xB64D) + 16 * tp["palette_record"] + 16])
    out = {}
    for key, t in sorted(raw["titles"].items()):
        exp = title_states(tp, *key)
        norm = lambda l: (l,) if isinstance(l, str) else tuple(l)
        states_ok = len(t["states"]) == len(exp) and all(norm(a) == norm(b) and wa == wb for (a, wa), (b, wb) in zip(t["states"], exp))
        h = t["hold"]
        out["%d_%d" % key] = dict(states=len(exp), states_equal_model=states_ok, tiles_equal_stream=h["vram_tiles"][:len(decoded)] == decoded,
                                  bg_palette_equals_record=list(h["cram"][:16]) == rec, final_name_table_sha256=nt_hash(exp[-1][1]))
    return out


# ------------------------------------------------------------------------------------------------------------------------------------------
# Scenario set and observation JSON
SONIC_PRE = dict(continues=0x83, emeralds=0x1F, score0=0x90, score1=0x49, score2=0x00)
SCENARIOS = [
    # id, run_clear kwargs, next (zone, act), card type for compose, note
    ("sonic_thz1_baseline", dict(character=0, rings=0x25, step_hooks=True), (0, 1), 0, "real goal-sign chain; per-step hooks for the tally cadence"),
    ("tails_thz1", dict(character=1, rings=0x25), (0, 1), 0, "D2C8 = 2: other banner and other continue icon"),
    ("sonic_award_crossing", dict(character=0, rings=0x25, pre=SONIC_PRE), (0, 1), 0, "3 continues (bit 7 set), 5 emeralds, score 4990 raw: the Sonic award rule fires during the tally"),
    ("sonic_continue_overflow", dict(character=0, rings=0x25, pre=dict(SONIC_PRE, continues=8)), (0, 1), 0, "8 continues already shown: the award draws a ninth icon at slot 8"),
    ("sonic_rings_00", dict(character=0, rings=0x00), (0, 1), 0, "0 rings: ring field '0', no ring loop steps"),
    ("sonic_rings_99", dict(character=0, rings=0x99), (0, 1), 0, "99 rings"),
    ("stage_card_failure", dict(character=0, rings=0x25, card_override=1), (0, 1), 1, "D2CD forced to 1 at $32F9 (controlled branch): Special Stage card layout"),
    ("stage_card_success", dict(character=0, rings=0x25, card_override=0xFF), (0, 1), 0xFF, "D2CD forced to $FF at $32F9: stage card + sound $86 + 240-frame hold"),
    ("held_button_tally", dict(character=0, rings=0x25, hold_during_tally=0x10, step_hooks=True), (0, 1), 0, "button 1 held from the tally call: pacing delay skipped"),
    ("boss_zone0_act2", dict(zone=0, act=2, rings=0x25, pre={0xD2A6: 0x34, 0xD2A7: 0x02}, step_hooks=True), (1, 0), 0, "act index 2: $1543 tail, boss bonus loop (50 steps) before the ring loop"),
    ("boss_zone3_act2", dict(zone=3, act=2, rings=0x25, pre={0xD2A6: 0x34, 0xD2A7: 0x02}, step_hooks=True), (4, 0), 0, "act index 2 in zone 3: 200 boss-bonus steps"),
    ("flag_zone1_act0", dict(zone=1, act=0, rings=0x25), (1, 1), 0, "ordinary $14AE tail in another zone (flag injected)"),
]


def _title_timeline(raw, key):
    t = raw["titles"].get(key)
    if not t:
        return None
    t0 = raw["t0"]
    out = dict(arrow_updates=[], zone_updates=[], act_updates=[])
    for f, lab in t["hits"]:
        if isinstance(lab, tuple) and lab[0] == "arrow":
            out["arrow_updates"].append(f - t0)
        elif isinstance(lab, tuple) and lab[0] == "zone":
            out["zone_updates"].append(f - t0)
        elif isinstance(lab, tuple) and lab[0] == "act":
            out["act_updates"].append(f - t0)
    return out


def freeze_summary(raw):
    e, m, n = (raw["freeze"][k] for k in ("entry", "t60", "t186"))
    return dict(entry_to_60=dict(name_table_equal=e["nt"] == m["nt"], sat_equal=e["sat"] == m["sat"], vdp_registers_equal=e["reg"] == m["reg"], camera_equal=e["camera"] == m["camera"],
                                 player_equal=e["player"] == m["player"]),
                at_60_to_186=dict(name_table_equal=m["nt"] == n["nt"], sat_equal=m["sat"] == n["sat"], vdp_registers_equal=m["reg"] == n["reg"]),
                frames=dict(entry=0, t60=m["frame"] - e["frame"], t186=n["frame"] - e["frame"]))


def observe_scenario(rom, plan, tp, tiles, decoded, sid, kw, nxt, card, keep_cram=True):
    facts, raw = run_clear(rom, **kw)
    res = check_run(rom, plan, tiles, decoded, facts, raw, card=card, nxt=nxt, fades=kw.get("zone", 0) < 5)
    tres = check_title(rom, tp, raw)
    out = dict(kwargs={k: (v if not isinstance(v, dict) else {str(a): b for a, b in v.items()}) for k, v in kw.items() if k != "step_hooks"},
               how=facts["how"], flag_to_clear_entry=facts["flag_to_clear_entry"], events=facts["events"], steps=facts["steps"], checks=res,
               title_cards=tres, next_title_timeline=_title_timeline(raw, nxt), frozen_frame=freeze_summary(raw), sound_and_continue_writes=facts["writes"])
    if keep_cram:
        out["palette_buffer_at_fade_request"] = facts["palette_buffer_at_fade_request"]
        out["cram_changes"] = facts["cram"]
    return out, facts, raw


_KEY_EVENTS = ("clear_entry", "clear_entry_zone", "card_start", "tally_call", "tally_return", "tail_white_request", "white_fill", "progress", "title_start",
               "title_hold_start", "title_hold_end", "title_return")


def zone_matrix(rom, plan, tp, tiles, decoded):
    rows = []
    for zone in range(6):
        for act in range(3):
            facts, raw = run_clear(rom, zone=zone, act=act, rings=0x25)
            if zone >= 5 and act == 2:
                rows.append(dict(zone=zone, act=act, results_card=False,
                                 events=[e for e in facts["events"] if e[1] in ("clear_entry_zone", "zone_gate", "card_call", "progress", "zone_store")]))
                continue
            nxt = (zone, act + 1) if act < 2 else (zone + 1, 0)
            res = check_run(rom, plan, tiles, decoded, facts, raw, card=0, nxt=nxt, fades=True)
            tres = check_title(rom, tp, raw)
            ev = {n: f for f, n in facts["events"]}
            ok = all(v for k, v in res.items() if isinstance(v, bool) and k != "fade_sequence_equals_model")
            rows.append(dict(zone=zone, act=act, results_card=True, tail="zone" if act == 2 else "act", next=list(nxt),
                             relative_frames={k: ev[k] for k in _KEY_EVENTS if k in ev}, compose_and_palette_equal=ok,
                             fade_model_equal=res.get("fade_sequence_equals_model"), name_table_sha256=res["name_table_sha256_at_tally_call"], d2d3=res["d2d3"],
                             title_cards_equal_model={k: v["states_equal_model"] and v["tiles_equal_stream"] and v["bg_palette_equals_record"] for k, v in tres.items()}))
    return rows


HARNESS_NOTE = ("tools/g0_rig.py on tools/sms_frame_harness.py: original Z80 code, approximate VDP, NTSC frame timing (262 lines x 228 cycles; the ROM's own PAL flag D12D is 0 and is "
                "not read anywhere in the results or title path).  Frame offsets are harness frames relative to the act-clear entry ($14AE / $1543); attaching PC hooks can move a later "
                "event by +/-1 frame.  The tally is CPU-bound, so its steps-per-frame figures are per NTSC harness frame, not per PAL frame.")


def observe_all(rom, only=None, progress=print):
    census = static_census(rom)
    plan = census["draw_plan"]
    tp = census["act_title_card"]
    _, decoded = tile_stream_info(rom)
    tiles = tiles_from_decoded(decoded)
    out = dict(format=1, rom_sha256=ROM_SHA256, base_commit=BASE_COMMIT, harness=HARNESS_NOTE, scenarios={})
    for sid, kw, nxt, card, note in SCENARIOS:
        if only and sid not in only:
            continue
        progress("observing " + sid)
        o, _, _ = observe_scenario(rom, plan, tp, tiles, decoded, sid, kw, nxt, card)
        o["note"] = note
        out["scenarios"][sid] = o
    if not only or "zone_matrix" in only:
        progress("observing zone_matrix")
        out["zone_matrix"] = zone_matrix(rom, plan, tp, tiles, decoded)
    return out


# ------------------------------------------------------------------------------------------------------------------------------------------
# JSON, validation, CLI
def dumps(obj, indent=1):
    """Deterministic JSON: sorted keys, lists of scalars on one line."""
    def scalar(v):
        return not isinstance(v, (dict, list))

    def rec(o, level):
        pad = " " * (indent * level)
        if isinstance(o, dict):
            if not o:
                return "{}"
            items = ",\n".join("%s%s: %s" % (pad + " " * indent, json.dumps(k), rec(v, level + 1)) for k, v in sorted(o.items()))
            return "{\n%s\n%s}" % (items, pad)
        if isinstance(o, (list, tuple)):
            if not o:
                return "[]"
            if all(scalar(v) for v in o):
                return json.dumps(list(o))
            items = ",\n".join(pad + " " * indent + rec(v, level + 1) for v in o)
            return "[\n%s\n%s]" % (items, pad)
        return json.dumps(o)
    return rec(obj, 0) + "\n"


def variant_diff(plan):
    """Cells where the stage card differs from the ordinary card (same size blocks)."""
    ids = {b["id"]: b for b in plan["blocks"]}
    out = {}
    for a, b in (("banner_sonic", "banner_stage"), ("banner_other", "banner_stage"), ("labels_ordinary", "labels_stage"), ("panel_ordinary", "panel_stage")):
        x, y = ids[a], ids[b]
        same_shape = (x["cols"], x["rows"], x["col"], x["row"]) == (y["cols"], y["rows"], y["col"], y["row"])
        diff = [[i // x["cols"], i % x["cols"], x["tiles"][i], y["tiles"][i]] for i in range(len(x["tiles"])) if x["tiles"][i] != y["tiles"][i]] if same_shape else None
        out["%s__vs__%s" % (a, b)] = dict(same_geometry=same_shape, differing_cells=diff, differing_cell_count=(len(diff) if diff is not None else None),
                                           same_source=x["source_cpu"] == y["source_cpu"])
    return out


ADAPTER = dict(
    status="GAMEMAKER PRESENTATION ADAPTER PROPOSAL - not ROM data; the ROM facts are in every other section",
    rom_native=dict(screen_px=[256, 192], tile_px=8, name_table_cells=[32, 24], vdp_r0="26 (bit 5: leftmost 8-px column shows the backdrop)", backdrop=(
        "CRAM[16 + (R7 & 15)]: R7 = 0, so sprite-palette entry 0. Results card: record 4 entry 0 = $3F (white, same as the fill tile and the bg index 13). "
        "Act title card: only the BG slot is faded in, so the sprite palette is still black: black left column and black border.")),
    widescreen_348x196=dict(logical_px=[348, 196], centre_offset_px=[46, 2], note=("centre the 256x192 image; paint the 46-px side bars and 2-px top/bottom bars with the ROM backdrop "
        "colour of the same frame and run them through the same CRAM ramp as the image (the backdrop is part of CRAM, so it fades with the card)"),
        keep_left_mask_column=True),
    rgb_expansion="channel * 85 (accepted harness expansion); the ROM stores 2 bits per channel",
    tally_rate=dict(unit="steps per NTSC harness frame", ring_and_bonus_mean=3.067, button_held_mean=6.013, cpu_bound=True,
                    note="a step is ~19.5k T-states without a button and ~9.9k with one; per 50 Hz frame the same code gives ~1.19x more steps. Choose the adapter rate "
                         "from the target frame rate; do not treat the per-frame figure as a ROM constant."),
)


WAIT_SITES = [("act_clear_wait_before_fade", 0x14AE), ("act_clear_fade_to_white_wait", 0x14D0), ("act_clear_after_sound_regs", 0x14DB), ("act_clear_blank_wait", 0x14F4),
              ("act_clear_after_card", 0x14FF), ("act_clear_white_hold", 0x1519), ("act_clear_black_wait", 0x1527), ("card_stage_success_hold", 0x33CE), ("card_before_tally", 0x33DA),
              ("card_after_tally", 0x33E8), ("boss_bonus_after_loop", 0x2D7B), ("zone_clear_wait_before_fade", 0x1543), ("zone_clear_fade_to_white_wait", 0x1565),
              ("zone_clear_after_sound_regs", 0x1570), ("zone_clear_blank_wait", 0x158C), ("zone_clear_after_card", 0x159E), ("zone_clear_white_hold", 0x15B8), ("zone_clear_black_wait", 0x15C6),
              ("title_after_fade_request", 0x31B1), ("title_hold", 0x31C4), ("title_after_fade_out", 0x31D9)]


def wait_loops(rom):
    """`LD B,n` immediates in front of the `EI / CALL $062D / DJNZ` frame-wait loops (one wait per iteration)."""
    out = {}
    for name, a in WAIT_SITES:
        if rom[a] != 0x06:
            raise ValueError("expected LD B,n at $%04X" % a)
        out[name] = dict(address=hx(a, 4), frames=rom[a + 1])
    return out


UNRESOLVED = [
    dict(id="U4-1", item="meaning of the sound request numbers in this path ($B4 tally tick, $86 stage card, $88 title card, 0 stop, level-music table at $18BA)", state="numbers only (see U5 / AUDIO-0)"),
    dict(id="U4-2", item="cycle-exact rates of CPU-bound waits (tally steps, title busy loops $32EE) on a real console; harness gives NTSC-frame figures only", state="EMULATED, not cycle-proven"),
    dict(id="U4-3", item="sub-frame placement of each act-title animator update and arrow iteration (the name-table states and their order are exact; the frame each state is first visible is harness-measured)", state="MEASURED"),
    dict(id="U4-4", item="the frozen gameplay frame that is faded to white before the card is level/act specific (VRAM, SAT, CRAM at the clear entry); it cannot be reproduced from ROM tables alone", state="ADAPTER must capture the last gameplay frame"),
    dict(id="U4-5", item="what drives the sprite change in [0,60) after the clear entry (HUD ring icon, SAT entries 12 and 13); inferred ISR animation slot D452..D46A, cleared by $1CEB", state="INFERRED"),
    dict(id="U4-6", item="D2CC bit 5 (sixth emerald bit) is never drawn on this card; only bits 0..4 have icons", state="DECODED (by design of $33F1); semantics belong to the ending research"),
    dict(id="U4-7", item="label wording is graphics only (read from tiles: RING, SPEED, SCORE, CONTINUE, 'x 100', 'x 10'); there is no text string in the ROM for it", state="DECODED GRAPHICS"),
    dict(id="U4-8", item="D2D3 (attribute byte of every 1-byte-per-cell draw) is 1 in every observed card and title; its only zero writer is $34EA (ending TRY AGAIN screen); the ending -> title -> new game -> clear path was not run here", state="OBSERVED, one path unexercised"),
    dict(id="U4-9", item="act-title animator modes 2 and 3 and the $2E80 type-$11 variant are not reached by the title card (not decoded beyond their bytes)", state="NOT NEEDED"),
    dict(id="U4-10", item="zone 5 act index 2 skips the card (ending selector); the ending screens are outside this task", state="G0 / EEZ-ending research"),
    dict(id="U4-11", item="how the level palette cycling entries interact with the fade passes beyond the entries listed per act (animated entries are masked in the fade comparison)", state="MASKED, listed per scenario"),
]


def build_static(rom):
    census = static_census(rom)
    census["card_variants"] = variant_diff(census["draw_plan"])
    census["wait_loops"] = wait_loops(rom)
    census["adapter"] = ADAPTER
    census["unresolved"] = UNRESOLVED
    census["evidence_classes"] = dict(
        DECODED_DATA="draw plan operands, tilemaps, glyph table, icons, palette records, tile stream, boss table, waits",
        BYTE_VERIFIED_ASSEMBLY="routine regions with offsets, lengths, hashes (and hand disassembly recorded in the specification)",
        SOURCE_TRACED_BEHAVIOR="fade engine passes, number drawing, tally award rule, title animator modes 0 and 1",
        MODEL_VERIFIED_AGAINST_ORIGINAL_CODE="compose_name_table, render_indexed, fade_series, title_states compared with emulated VRAM/CRAM in every scenario",
        EMULATED_ORIGINAL_FRAME="all frame offsets, CRAM series, sound requests, tally cadence",
        CONTROLLED_VARIANT="D2CD forced at $32F9 (stage card layout), 5 RAM presets",
        UNRESOLVED="see unresolved")
    return census


def validate_static(st):
    errs = []
    if st["rom_sha256"] != ROM_SHA256:
        errs.append("rom sha")
    plan = st["draw_plan"]
    n_tiles = st["tile_stream"]["tile_count"]
    ok_tile = lambda t: TILE_BASE <= (t & 0x1FF) < TILE_BASE + n_tiles
    for b in plan["blocks"]:
        if b["col"] + b["cols"] > 32 or b["row"] + b["rows"] > 24 or len(b["tiles"]) != b["cols"] * b["rows"]:
            errs.append("block geometry " + b["id"])
        if not all(ok_tile((1 << 8) | t) for t in b["tiles"]):
            errs.append("block tile range " + b["id"])
    for s in plan["emeralds"]["slots"]:
        if not all(ok_tile(e) for e in s["entries"]):
            errs.append("emerald tile range %d" % s["slot"])
    if len(plan["digit_glyph_table"]["entries"]) != 11:
        errs.append("glyph table")
    for r in st["routines"]:
        if len(r["sha256"]) != 64 or r["length"] <= 0:
            errs.append("routine " + r["name"])
    for k, rec in st["palette_records"].items():
        if len(rec["sms_colours"]) != 16 or any(c > 63 for c in rec["sms_colours"]):
            errs.append("palette " + k)
    tp = st["act_title_card"]
    nt = tp["tile_stream"]["tile_count"]
    for z in tp["zone_object"]["maps"]:
        if len(z["tiles"]) != 128 or not all(TILE_BASE <= (0x100 | t) < TILE_BASE + nt for t in z["tiles"]):
            errs.append("title zone map %d" % z["zone"])
    for a in tp["act_object"]["maps"]:
        if len(a["tiles"]) != 48:
            errs.append("title act map %d" % a["act"])
    if len(st["boss_bonus_steps"]) != 6:
        errs.append("boss steps")
    return errs


def validate_observed(ob):
    errs = []
    for sid, sc in ob["scenarios"].items():
        for k, v in sc["checks"].items():
            if isinstance(v, bool) and not v:
                errs.append("%s: %s" % (sid, k))
        for key, t in sc["title_cards"].items():
            if not (t["states_equal_model"] and t["tiles_equal_stream"] and t["bg_palette_equals_record"]):
                errs.append("%s: title %s" % (sid, key))
        for sp in (sc["checks"].get("tally_call_sprite_pixels"), sc["checks"].get("tally_return_sprite_pixels")):
            if sp not in (0, None):
                errs.append("%s: sprite pixels on the card" % sid)
    zm = ob.get("zone_matrix", [])
    if zm and len(zm) != 18:
        errs.append("zone matrix size")
    for r in zm:
        if r.get("results_card") and not (r["compose_and_palette_equal"] and r["fade_model_equal"] and all(r["title_cards_equal_model"].values())):
            errs.append("zone matrix %d/%d" % (r["zone"], r["act"]))
    return errs


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_all(rom, only=None, progress=print):
    DATA.mkdir(parents=True, exist_ok=True)
    st = build_static(rom)
    STATIC_JSON.write_text(dumps(st), encoding="utf-8", newline="\n")
    manifest = export_assets(rom, st)
    MANIFEST_JSON.write_text(dumps(manifest), encoding="utf-8", newline="\n")
    if only == "static":
        return
    ob = observe_all(rom, progress=progress)
    OBS_JSON.write_text(dumps(ob), encoding="utf-8", newline="\n")


def check_all(rom, progress=print):
    problems = []
    st = build_static(rom)
    if dumps(st) != STATIC_JSON.read_text(encoding="utf-8"):
        problems.append("static census differs from the committed file")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        man = export_assets(rom, st, out=Path(td))
        if dumps(man) != MANIFEST_JSON.read_text(encoding="utf-8"):
            problems.append("export manifest differs from the committed file")
    ob = observe_all(rom, progress=progress)
    if dumps(ob) != OBS_JSON.read_text(encoding="utf-8"):
        problems.append("observations differ from the committed file")
    problems += validate_observed(ob)
    return problems


DOC = ROOT / "docs" / "u4-ordinary-results.md"
_MARK = "<!-- %s u4:%s -->"


def _md(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |" for r in rows]
    return "\n".join(out)


def doc_tables(st, ob):
    """Generated tables of the specification (the prose around them is hand-written)."""
    t = {}
    t["routines"] = _md([("`%s`" % r["name"], ("%02X:" % r["bank"] if r["bank"] is not None else "res ") + "$%s-$%s" % (r["cpu_start"], r["cpu_end_exclusive"]), "0x%s" % r["file_start"],
                          r["length"], "`%s`" % r["sha256"][:12], r["role"]) for r in st["routines"]], ("routine", "CPU range (end exclusive)", "file", "bytes", "SHA-256", "role"))
    plan = st["draw_plan"]
    rows = []
    f = plan["fill"]
    rows.append(("`screen_fill`", "always", "`$1D8A`", "-", "(0,0)", "32x24", "entry `$%04X`" % f["entry"]))
    for b in plan["blocks"]:
        rows.append(("`%s`" % b["id"], b["condition"], b["routine"], "%02X:$%s (0x%s)" % (b["source_bank"], b["source_cpu"], b["source_file"]), "(%d,%d)" % (b["col"], b["row"]),
                     "%dx%d" % (b["cols"], b["rows"]), "tile ids %d..%d" % (min(b["tiles"]) + 256, max(b["tiles"]) + 256)))
    c = plan["continues"]
    for k, ic in c["icons"].items():
        rows.append(("`continue_icon_%s`" % k, "D2C8 %s 1" % ("==" if k == "sonic" else "!="), "`$2383`", "19:$%s" % ic["source_cpu"], "(%d,%d)+2n" % (c["col0"], c["row0"]), "2x2 each, n < 8",
                     "tile ids %s" % ",".join(str(256 + x) for x in ic["tiles"])))
    for s in plan["emeralds"]["slots"]:
        rows.append(("`emerald_%d`" % s["slot"], "D2CC bit %d" % s["slot"], "`$2349`", "19:$%s" % s["source_cpu"], "(%d,%d)" % (s["col"], s["row"]), "2x2", "entries %s" % ",".join("%03X" % e for e in s["entries"])))
    t["blocks"] = _md(rows, ("element", "condition", "routine", "ROM source", "cell (col,row)", "size", "content"))
    t["numbers"] = _md([("`%s`" % x["id"], "`$%s`" % x["ram"], x["bytes"], x["digits"], x["leading_zero_blank"], "(%d,%d)" % (x["col"], x["row"]), x["draw_call"]) for x in plan["number_fields"]]
                       + [("score trailing `0`", "constant", "-", "1", "-", "(%d,%d)" % (plan["score_trailing_zero"]["col"], plan["score_trailing_zero"]["row"]), "`$2383`")],
                       ("field", "source", "BCD bytes", "digit cells", "blank leading zeros", "first cell (col,row)", "routine"))
    t["glyphs"] = _md([(g["digit"], g["top"], g["bottom"]) for g in plan["digit_glyph_table"]["entries"]], ("digit", "top tile id (low byte)", "bottom tile id (low byte)"))
    pal = []
    for k, rec in sorted(st["palette_records"].items(), key=lambda kv: int(kv[0])):
        pal.append(("%s ($%02X)" % (k, int(k)), "0x%s" % rec["file_start"], " ".join("%02X" % c for c in rec["sms_colours"])))
    t["palettes"] = _md(pal, ("record", "file", "16 SMS colours %00BBGGRR"))
    b = ob["scenarios"]["sonic_thz1_baseline"]
    ev = {n: f for f, n in b["events"]}
    names = [("clear_entry", "`$14AE` entered (D293 bit 5 seen by the main loop)"), ("anim_freeze", "`$1CEB`: sprite animation slots, terrain animation pointer, D131/D132 cleared"),
             ("fade_white_request", "D492/D494 := bit6|bit4 (to white), D2D4 := 4"), ("sound_regs", "`$18E1`: DE09..0B := 12,1,2"),
             ("sound_stop", "sound request 0"), ("object_clear", "`$297E`/`$4FCE`/`$21DA` clears, `$342A` white buffer"), ("card_start", "`$32F9`"),
             ("card_numbers", "last draw call of the card"), ("card_fade_in_request", "D492/D494 := bit7|bit4, records 3 and 4"), ("tally_call", "`$2D55`/`$2D08`"),
             ("tally_return", "tally finished"), ("post_card_wait", "back in `$14AE` after the 48-frame wait inside `$32F9`"), ("tail_white_request", "D492/D494 := bit6|bit4"),
             ("white_fill", "`$342A` white buffer (screen is already white)"), ("black_request", "`$1CAF`: D492/D494 := bit6 (to black)"), ("progress", "act := act + 1, D293 bit 1"),
             ("title_start", "`$3175` act title card"), ("title_fills_done", "fills, fade-in request (BG record $21), sound $88"), ("title_arrows_start", "`$31E2` arrows"),
             ("title_text_start", "`$3225` zone and act objects"), ("title_hold_start", "hold up to 180 frames"), ("title_hold_end", "hold over or button"), ("title_return", "`$31E1` return"),
             ("level_loader", "`$2934`"), ("level_fade_in_request", "`$794F`: D492/D494 := bit7 (in from black)")]
    t["timeline"] = _md([(ev[n], n, d) for n, d in names if n in ev], ("harness frame", "event", "what the ROM does"))
    cram = []
    for fr, c in b["cram_changes"]:
        cram.append((fr, c[:8] + "..."))
    t["cram"] = _md(cram, ("harness frame", "CRAM bytes 0..3"))
    tp = st["act_title_card"]
    t["title"] = _md([("fill", "`$%s`" % f["name_table_address"], "%d words" % f["words"], "entry `$%04X`" % f["entry"]) for f in tp["fills"]]
                     + [(a["id"], "(%d,%d)" % (a["start_col"], a["start_row"]), "%dx%d" % (a["cols"], a["rows"]), "%d iterations, %+d col each; 19:$%s" % (tp["arrow_iterations"], a["direction_cols_per_iteration"], a["source_cpu"])) for a in tp["arrows"]]
                     + [("zone name", "(%d,%d)" % (tp["zone_object"]["col"], tp["zone_object"]["row"]), "%dx%d" % (tp["zone_object"]["cols"], tp["zone_object"]["rows"]),
                         "mode 0, %d updates; maps %s" % (tp["zone_object"]["steps"], " ".join("$" + m["source_cpu"] for m in tp["zone_object"]["maps"]))),
                        ("act number", "(%d,%d) start" % (tp["act_object"]["start_col"], tp["act_object"]["start_row"]), "%dx%d" % (tp["act_object"]["cols"], tp["act_object"]["rows"]),
                         "mode 1, %d updates; maps %s" % (tp["act_object"]["steps"], " ".join("$" + m["source_cpu"] for m in tp["act_object"]["maps"])))],
                     ("element", "position", "size", "behaviour"))
    t["unresolved"] = _md([(u["id"], u["item"], u["state"]) for u in st["unresolved"]], ("id", "item", "state"))
    zm = []
    for r in ob["zone_matrix"]:
        if not r["results_card"]:
            zm.append((r["zone"], r["act"], "none", "-", "-", "-", "-", "-"))
            continue
        rf = r["relative_frames"]
        zm.append((r["zone"], r["act"], r["tail"], rf.get("card_start"), rf.get("tally_call"), rf.get("tally_return"), rf.get("progress"), rf.get("title_hold_start")))
    t["zone_matrix"] = _md(zm, ("zone", "act", "tail", "card start", "tally call", "tally return", "progress", "title hold"))
    return t


def refresh_doc(path=DOC, st=None, ob=None):
    st = st or load_json(STATIC_JSON)
    ob = ob or load_json(OBS_JSON)
    text = Path(path).read_text(encoding="utf-8")
    for name, body in doc_tables(st, ob).items():
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
    ap.add_argument("--doc", action="store_true", help="refresh the generated tables inside docs/u4-ordinary-results.md from the committed JSON")
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
        problems = check_all(rom)
        print("U4 check: OK" if not problems else "\n".join(problems))
        return 1 if problems else 0
    write_all(rom, only=a.only)
    print("wrote", STATIC_JSON, MANIFEST_JSON, "" if a.only else OBS_JSON, "exports in", BUILD)
    return 0


if __name__ == "__main__":
    sys.exit(main())

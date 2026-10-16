#!/usr/bin/env python3
"""U3-A: goal-sign prize graphics, reward-table parity and retry behaviour (Sonic Chaos SMS, Europe v1.2).

    python tools/u3_sign_prizes.py ROM                 # regenerate data/u3/*.json and the ignored exports in build/u3/
    python tools/u3_sign_prizes.py ROM --check         # recompute everything and compare with the committed JSON
    python tools/u3_sign_prizes.py ROM --only static   # static census only (no emulation, a second or two)
    python tools/u3_sign_prizes.py ROM --only controlled   # static + Z80 oracle runs (seconds)
    python tools/u3_sign_prizes.py --validate          # no ROM: internal consistency of the committed JSON and re-run of the pure model
    python tools/u3_sign_prizes.py --doc               # refresh the generated tables inside docs/u3-sign-prize-presentation.md

Evidence layers (every JSON section names its own):

* ``static``     - DECODED DATA / BYTE-VERIFIED ASSEMBLY read straight from ROM bytes: routine regions and byte anchors, the dynamic-graphics loader and its
                   selector lists, the six face tile blocks and their palette-index hashes, the type-$18 mapping frames, the per-zone sprite palettes, both prize
                   tables, the time-bonus table and the pure Python model derived from them.
* ``controlled`` - CONTROLLED ROUTINE RESULT: the original Z80 routines ($A8FA, $AB48/$6276, $3104) executed on kosarev/z80 (tools/oracle.py via
                   tools/object_18.py) with explicit RAM, compared cell by cell with the model.
* ``observed``   - EMULATED ORIGINAL FRAME: complete clears of the unmodified ROM in the approximate SMS harness (tools/g0_rig.py).  Fixtures are limited to
                   ARRIVAL placement (player and camera 160 px before the sign), RAM presets named in each scenario, and joypad input; nothing writes a
                   program counter, a bank, an object or the VDP.
* ``adapter``    - GameMaker presentation notes.  Never mixed into the ROM-native fields.

No ROM byte, tile pixel or composed image is written to the committed JSON except decoded numeric tables of the same kind earlier Research caches already
commit (prize tables, time table, 2-bit colours, mapping coordinates) and SHA-256 hashes of the palette-index bytes.  Tile data and every PNG are exported to
the ignored ``build/u3/``.
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

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
BASE_COMMIT = "87ae62b76de35e41c9bb837c1125a54210f2f85c"
DATA = ROOT / "data" / "u3"
BUILD = ROOT / "build" / "u3"
STATIC_JSON = DATA / "sign-prize-static.json"
CONTROLLED_JSON = DATA / "sign-prize-controlled.json"
OBS_JSON = DATA / "sign-prize-observed.json"
MANIFEST_JSON = DATA / "export-manifest.json"
DOC = ROOT / "docs" / "u3-sign-prize-presentation.md"

BANK_OBJ = 0x0C          # object state code of types < $26 (sign $18, child $19)
BANK_FACE = 0x0D         # source bank of the six face tile blocks
BANK_MAP = 0x0F          # type mapping frames
TYPE_SIGN = 0x18
TYPE_CHILD = 0x19
SEL_DEFAULT = 0x12       # sign wake selector ($A87D): 16 face tiles at tile $6A + 48 fixed tiles at tile $7A
SEL_FACES = (0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20)
FACE_TILE0 = 0x6A        # first VRAM tile replaced by every face selector
FACE_TILES = 16
TABLE_ODD_ZONE_PARITY = "A919"   # zones 0, 2, 4 ((zone + 1) odd): THZ, SEZ, and zone 4
TABLE_EVEN_ZONE_PARITY = "A962"  # zones 1, 3, 5
ZONE_NAMES = ("THZ", "GPZ", "SEZ", "MGHZ", "AQZ", "EEZ")   # RQ4 start table order = $D297
PTYPE_SONIC = 1
PTYPE_OTHER = 2          # Tails (D500 = character + 1)


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


def s16(v):
    return v - 65536 if v >= 32768 else v


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
    ("dyn_loader", None, 0x7AC2, 0x7BA6, "dynamic graphics loader: D3B3 selector -> list -> 4 tiles per call to VRAM (bank byte bit 7 = remap through the $0100 table)"),
    ("dyn_selector_table", None, 0x7BA6, 0x7BCA, "18 little-endian list pointers for selectors $10..$21"),
    ("dyn_lists", None, 0x7BCA, 0x7C71, "selector lists, six bytes per entry [bank, tiles, vram_lo, vram_hi, src_lo, src_hi], $FF ends a list"),
    ("sign_wake_states", BANK_OBJ, 0xA867, 0xA88E, "states 0..2: clear class/retry bytes, wait for on-screen, D3B3 := $12"),
    ("sign_contact_state3", BANK_OBJ, 0xA88E, 0xA8C8, "state 3 contact test, timer stop, state 4 (first touch) or 6 (retouch)"),
    ("sign_state4_marker", BANK_OBJ, 0xA8C8, 0xA8CE, "D4A3 := $FF (purpose unresolved)"),
    ("sign_hop_landing", BANK_OBJ, 0xA8CE, 0xA8FA, "state-4 hop physics; at the saved Y calls $A8FA"),
    ("sign_landing_prize", BANK_OBJ, 0xA8FA, 0xA919, "landing: state 5, retouch test (+$35), zone parity table select"),
    ("sign_prize_table_odd", BANK_OBJ, 0xA919, 0xA959, "64-byte BCD ring-count table used when (zone + 1) is odd"),
    ("sign_prize_select_even", BANK_OBJ, 0xA959, 0xA962, "even-parity branch: HL := $A962, CALL $A9FA, JP $A9A2"),
    ("sign_prize_table_even", BANK_OBJ, 0xA962, 0xA9A2, "64-byte BCD ring-count table used when (zone + 1) is even"),
    ("sign_prize_dispatch", BANK_OBJ, 0xA9A2, 0xA9EC, "class -> reward ($03F2 life, rings +$10, continue +1) and D3B3 face selector"),
    ("sign_retry_setup", BANK_OBJ, 0xA9EC, 0xA9FA, "class 0: +$35 := $FF, D3B3 := $20, state 3"),
    ("sign_prize_lookup", BANK_OBJ, 0xA9FA, 0xAA16, "CPIR over a 64-byte table, class = C >> 4 (also stores the ring count at $DC00)"),
    ("sign_retouch_reroll", BANK_OBJ, 0xAA16, 0xAA22, "+$34 := ($D12F & 7) + 1, then the common dispatch"),
    ("sign_camera_pan", BANK_OBJ, 0xAA22, 0xAA47, "sign pan target (signX - $80, signY - $99), vector $0359"),
    ("child19_spawn_vector", BANK_OBJ, 0xAA47, 0xAA4F, "state 5 script call: spawn type $19"),
    ("child19_states", BANK_OBJ, 0xAA4F, 0xAB9F, "type $19 table, scripts, state callbacks and constants (digit cycling, slide-in)"),
    ("child19_bonus_state3", BANK_OBJ, 0xAB48, 0xAB8C, "state 3: $041F bonus word, zero -> $0777, equal digits -> $03F2, panel digits"),
    ("bonus_word_6276", None, 0x6276, 0x62AD, "$041F target: time bucket index, H/L word"),
    ("bonus_time_table", None, 0x62AD, 0x62D5, "ten 4-byte entries: limit word (BCD mmss), L byte, H byte"),
    ("life_award_3104", None, 0x3104, 0x3138, "sound $A9, D299 + 1 capped at $99, HUD digits when D292 = 0"),
    ("vectors_03F2_041F", None, 0x03F2, 0x03F5, "JP $3104"),
    ("vectors_041F", None, 0x041F, 0x0422, "JP $6276"),
    ("level_sprite_palette_index", None, 0x7F3C, 0x7F3C + 36, "(zone * 3 + act) * 2 -> [background palette, sprite palette]"),
    ("sprite_loader_vector_check", None, 0x794F, 0x7979, "palette index loader $794F"),
]

# Instruction fragments the analysis depends on (file bytes are compared with these constants).
ANCHORS = [
    ("loader_called_after_object_pass", None, 0x16D0, "cdd15dcdc27a", "level frame update $16B8: CALL $5DD1 (all objects) then CALL $7AC2 (dynamic graphics), once per update; the alternate branch calls it at $1723"),
    ("loader_pointer_table_base", None, 0x7B5F, "11a67b", "LD DE,$7BA6 (selector table, index = selector - $10)"),
    ("loader_four_tile_cap", None, 0x7AF5, "fe0438023e04", "CP 4 / JR C / LD A,4: at most four tiles per call"),
    ("loader_tile_bytes", None, 0x7AFC, "0e20", "LD C,$20: 32 bytes per tile"),
    ("loader_bank_mask", None, 0x7B24, "e61f", "AND $1F: bank number of the remapped branch"),
    ("loader_finish_clear", None, 0x7B92, "af32b3d3", "XOR A / LD (D3B3),A: the selector is cleared when the list ends"),
    ("wake_selector_12", BANK_OBJ, 0xA87D, "3e1232b3d3", "LD A,$12 / LD (D3B3),A"),
    ("landing_state5_retouch", BANK_OBJ, 0xA8FA, "dd360205dd7e35b7c216aa", "state 5; A := +$35; JP NZ,$AA16 (retouch re-roll)"),
    ("parity_select", BANK_OBJ, 0xA909, "3a97d23c0f30492119a9cdfaa9c3a2a9", "A := ($D297 + 1) >> 1 (carry = bit 0); odd -> $A919"),
    ("dispatch_class_zero", BANK_OBJ, 0xA9A2, "dd7e34b72844", "class 0 -> $A9EC (retry)"),
    ("dispatch_class_one_life", BANK_OBJ, 0xA9A8, "3d2010cdf2033a00d5fe013e1b28313e1d182d", "class 1: CALL $03F2; Sonic (D500 = 1) -> $1B else $1D"),
    ("dispatch_class_two_rings", BANK_OBJ, 0xA9BB, "3d200e3a9ad206108027329ad23e1e181c", "class 2: D29A := (D29A + $10) DAA, carry dropped; selector $1E"),
    ("dispatch_class_three_continue", BANK_OBJ, 0xA9CC, "3d20173ac3d23c27e67f32c3d23a00d5fe013e1d28063e1b1802", "class 3: D2C3 := ((D2C3 + 1) DAA) & $7F; Sonic -> $1D else $1B"),
    ("class_none_art", BANK_OBJ, 0xA9E6, "3e1f32b3d3c9", "everything else (class $FF, 4..8): selector $1F, no reward"),
    ("retry_setup", BANK_OBJ, 0xA9EC, "dd3635ff3e2032b3d3dd360203c9", "+$35 := $FF; D3B3 := $20; state 3"),
    ("lookup_cpir", BANK_OBJ, 0xA9FA, "0140003a9ad2edb1200c3200dc790f0f0f0fe60f18023effdd7734c9", "CPIR over 64 bytes; class = (C >> 4) & 15; no match $FF; stores the count at $DC00"),
    ("reroll", BANK_OBJ, 0xAA16, "3a2fd1e6073cdd7734c3a2a9", "+$34 := ($D12F & 7) + 1; JP $A9A2"),
    ("life_cap", None, 0x3104, "3ea93204de3a99d2fe992806c6", "sound $A9; D299 = $99 -> no increment; else ADD 1, DAA"),
    ("child_bonus_state3", BANK_OBJ, 0xAB48, "cd1f047cb5200321770722a6d2", "CALL $041F; H|L = 0 -> HL := $0777; D2A6 := HL"),
    ("child_equal_digits", BANK_OBJ, 0xAB55, "447de60fb8200d7d0f0f0f0fe60fb82003cdf203", "B := H; low digit and high digit of L must both equal H -> CALL $03F2"),
    ("bonus_rings_term", None, 0x629E, "3a9ad2d6112785276f30037c3c27c9", "A := (D29A - $11) DAA + L (DAA); carry -> H + 1 DAA"),
]


def check_anchors(rom):
    out = []
    for name, bank, cpu, want, note in ANCHORS:
        n = len(bytes.fromhex(want))
        got = bytes(rom[off(bank, cpu):off(bank, cpu) + n]).hex()
        out.append(dict(name=name, bank=bank, cpu=hx(cpu, 4), file=hx(off(bank, cpu), 5), expected=want, actual=got, ok=(got == want), note=note))
    return out


# ------------------------------------------------------------------------------------------------------------------------------------------
# Pure model (no ROM): BCD arithmetic, prize classification, rewards, retouch re-roll, bonus word
def is_bcd(v):
    return (v & 15) <= 9 and (v >> 4) <= 9


def bcd_to_int(v):
    return (v >> 4) * 10 + (v & 15)


def int_to_bcd(n):
    return ((n // 10) << 4) | (n % 10)


def _daa(a, n, h, c):
    adj = 0
    nc = False
    if h or (a & 15) > 9:
        adj |= 6
    if c or a > 0x99:
        adj |= 0x60
        nc = True
    return ((a - adj) if n else (a + adj)) & 0xFF, nc


def add_bcd(a, b):
    """`ADD A,B` then `DAA`: returns (result, carry)."""
    r = a + b
    c = r > 0xFF
    h = ((a & 15) + (b & 15)) > 15
    r &= 0xFF
    res, nc = _daa(r, False, h, c)
    return res, nc


def inc_bcd(a):
    """`INC A` then `DAA` with the carry flag clear on entry (the sign code clears it just before): returns the byte."""
    r = (a + 1) & 0xFF
    h = (a & 15) == 15
    return _daa(r, False, h, False)[0]


def sub_bcd(a, b):
    """`SUB B` then `DAA`: returns (result, carry/borrow)."""
    c = a < b
    h = (a & 15) < (b & 15)
    r = (a - b) & 0xFF
    res, nc = _daa(r, True, h, c)
    return res, nc


def zone_table(zone):
    """$A909: A := zone + 1; RRCA; carry (bit 0 of zone + 1) -> table $A919, else $A962."""
    return TABLE_ODD_ZONE_PARITY if ((zone + 1) & 1) else TABLE_EVEN_ZONE_PARITY


def lookup_class(table, rings):
    """$A9FA: CPIR over the 64 table bytes for the BCD ring count; class = ((63 - index) >> 4) & 15, $FF when absent."""
    for i, b in enumerate(table):
        if b == rings:
            return ((63 - i) >> 4) & 15
    return 0xFF


def reroll_class(d12f):
    return (d12f & 7) + 1


# class -> (effect, selector for Sonic, selector for other/Tails); dispatch at $A9A2
EFFECTS = {
    0: ("retry", 0x20, 0x20),
    1: ("life", 0x1B, 0x1D),
    2: ("rings", 0x1E, 0x1E),
    3: ("continue", 0x1D, 0x1B),
}
SELECTOR_NONE = 0x1F


def effect_of(cls):
    return EFFECTS[cls][0] if cls in EFFECTS else "none"


def art_of(cls, ptype):
    if cls not in EFFECTS:
        return SELECTOR_NONE
    return EFFECTS[cls][1] if ptype == PTYPE_SONIC else EFFECTS[cls][2]


def grant_life(lives):
    """$3104 arithmetic (sound and HUD aside): a counter at $99 is left alone, otherwise ADD 1 / DAA."""
    return lives if lives == 0x99 else add_bcd(lives, 1)[0]


def grant_continue(cont):
    """$A9CF: INC A / DAA / AND $7F (bit 7 = 'continue just used' is dropped; the 80th continue wraps to 0)."""
    return inc_bcd(cont) & 0x7F


def grant_rings(rings):
    """$A9BE: ADD $10 / DAA, carry dropped."""
    return add_bcd(rings, 0x10)[0]


def prize_landing(tables, zone, ptype, rings, retry_flag, d12f, lives, cont):
    """The state of the sign after one `$A8FA` landing.  Returns the fields the ROM routine leaves behind."""
    if retry_flag:
        cls = reroll_class(d12f)
    else:
        cls = lookup_class(tables[zone_table(zone)], rings)
    out = dict(cls=cls, art=art_of(cls, ptype), state=3 if cls == 0 else 5, retry=0xFF if (cls == 0 or retry_flag) else 0, lives=lives, cont=cont, rings=rings,
               life_award=0)
    e = effect_of(cls)
    if e == "life":
        out["lives"] = grant_life(lives)
        out["life_award"] = 1 if out["lives"] != lives else 0
    elif e == "rings":
        out["rings"] = grant_rings(rings)
    elif e == "continue":
        out["cont"] = grant_continue(cont)
    return out


def bonus_word(time_table, time_bcd, rings):
    """$6276: returns the (H, L) word before the child's zero replacement.  `time_table` = [(limit, L, H), ...]; `time_bcd` = D2BF | D2C0 << 8 (BCD mmss)."""
    i = 0
    while time_bcd >= time_table[i][0]:       # SBC HL,DE: carry (stop) when the time is below the limit
        i += 1
    _limit, l0, h0 = time_table[i]
    a, _c = sub_bcd(rings, 0x11)
    a, carry = add_bcd(a, l0)
    h = inc_bcd(h0) if carry else h0
    return h, a


def child_bonus(time_table, time_bcd, rings):
    """Child state 3 ($AB48): D2A6 and the equal-digit life.  Returns (D2A6 word, equal_digit_life 0/1)."""
    h, l = bonus_word(time_table, time_bcd, rings)
    if h == 0 and l == 0:
        h, l = 0x07, 0x77
    equal = 1 if ((l & 15) == h and (l >> 4) == h) else 0
    return (h << 8) | l, equal


def award_sequence(tables, time_table, zone, ptype, rings, time_bcd, lives, cont, retry_flag=0, d12f=0, first_class_override=None):
    """Landing + child: everything G1-D has to produce for one sign (not the tally)."""
    land = prize_landing(tables, zone, ptype, rings, retry_flag, d12f, lives, cont)
    seq = [land]
    if land["cls"] == 0:                      # retry: nothing else happens until the second touch
        land2 = prize_landing(tables, zone, ptype, rings, 1, d12f, lives, cont)
        seq.append(land2)
        land = land2
    word, equal = child_bonus(time_table, time_bcd, land["rings"])
    lives_after = grant_life(land["lives"]) if equal else land["lives"]
    return dict(passes=seq, final_class=land["cls"], final_art=land["art"], rings=land["rings"], continues=land["cont"], lives=lives_after,
                bonus_word=word, equal_digit_life=equal, life_awards=land["life_award"] + (1 if (equal and lives_after != land["lives"]) else 0))


# ------------------------------------------------------------------------------------------------------------------------------------------
# Graphics decoding
def decode_tile(raw):
    """SMS mode-4 planar tile -> 8x8 palette indices."""
    rows = []
    for y in range(8):
        p = raw[y * 4:y * 4 + 4]
        rows.append([sum(((p[k] >> (7 - x)) & 1) << k for k in range(4)) for x in range(8)])
    return rows


def decode_selector_list(rom, selector):
    """Walk the loader's data structure for a selector >= $10 exactly like $7B51/$7B6D."""
    ptr = u16(rom, 0x7BA6 + (selector - 0x10) * 2)
    entries = []
    pos = ptr
    while rom[pos] != 0xFF:
        bank_byte, count = rom[pos], rom[pos + 1]
        vram = u16(rom, pos + 2)
        src = u16(rom, pos + 4)
        bank = bank_byte & 0x1F
        entries.append(dict(list_cpu=hx(pos, 4), bank_byte=bank_byte, bank=bank, remap=bool(bank_byte & 0x80), tiles=count, vram=hx(vram, 4), tile_base=vram // 32,
                            source_cpu=hx(src, 4), source_file=hx(off(bank, src), 5)))
        pos += 6
    return ptr, entries


def entry_bytes(rom, e):
    o = int(e["source_file"], 16)
    return bytes(rom[o:o + e["tiles"] * 32])


def selector_tiles(rom, selector):
    """{vram tile id: 32 raw bytes} written by one selector (no remap in any selector used by the sign)."""
    _ptr, entries = decode_selector_list(rom, selector)
    tiles = {}
    for e in entries:
        if e["remap"]:
            raise ValueError("unexpected remapped entry in selector $%02X" % selector)
        raw = entry_bytes(rom, e)
        for k in range(e["tiles"]):
            tiles[e["tile_base"] + k] = raw[k * 32:(k + 1) * 32]
    return tiles


def parse_mapping(rom, type_id):
    """Type mapping frames (bank $0F): pointer list -> 11-byte records (see docs/thz1-object-graphics.md)."""
    table = u16(rom, 0x3C000 + type_id * 2)
    frames = []
    pos = off(BANK_MAP, table)
    while True:
        p = u16(rom, pos)
        if not 0x8000 <= p <= 0xBFFF:
            break
        frames.append(p)
        pos += 2
    out = []
    for i, p in enumerate(frames):
        o = off(BANK_MAP, p)
        n = rom[o]
        coords = off(BANK_MAP, u16(rom, o + 3)) if n else None
        tiles = off(BANK_MAP, u16(rom, o + 9)) if n else None
        y0, x0 = s16(u16(rom, o + 5)), s16(u16(rom, o + 7))
        pieces = []
        for k in range(n):
            pieces.append(dict(x=x0 + s16(u16(rom, coords + k * 4 + 2)), y=y0 + s16(u16(rom, coords + k * 4)), tile=rom[tiles + k]))
        out.append(dict(frame=i, record_cpu=hx(p, 4), record_file=hx(o, 5), pieces=pieces, extent_word=hx(u16(rom, o + 1), 4),
                        sha256=sha(rom[o:o + 11] + (rom[coords:coords + n * 4] + rom[tiles:tiles + n] if n else b""))))
    return table, out


def compose_frame(frame, tiles, only=None):
    """Composite the frame's 8x16 sprite pieces into palette indices.  Returns (x0, y0, w, h, rows) with 0 = transparent."""
    pcs = frame["pieces"]
    if only is not None:
        pcs = [p for p in pcs if p["tile"] in only]
    x0 = min(p["x"] for p in pcs)
    y0 = min(p["y"] for p in pcs)
    x1 = max(p["x"] + 8 for p in pcs)
    y1 = max(p["y"] + 16 for p in pcs)
    rows = [[0] * (x1 - x0) for _ in range(y1 - y0)]
    for p in pcs:
        for half in (0, 1):
            px = decode_tile(tiles[p["tile"] + half])
            for ry in range(8):
                for rx in range(8):
                    if px[ry][rx]:
                        rows[p["y"] - y0 + half * 8 + ry][p["x"] - x0 + rx] = px[ry][rx]
    return x0, y0, x1 - x0, y1 - y0, rows


def rows_hash(rows):
    return sha(bytes(v for row in rows for v in row))


def sprite_palettes(rom):
    """Per-zone sprite palette via $794F: ($7F3C + (zone * 3 + act) * 2 + 1) -> palette record at $3B64D + 16 * index."""
    out = {}
    for zone in range(6):
        per_act = []
        for act in range(3):
            o = 0x7F3C + (zone * 3 + act) * 2
            per_act.append((rom[o], rom[o + 1]))
        idx = {p[1] for p in per_act}
        sp = per_act[0][1]
        out[str(zone)] = dict(background_index=[p[0] for p in per_act], sprite_index=sp, act_independent=(len(idx) == 1),
                              sprite_colours=list(rom[0x3B64D + 16 * sp:0x3B64D + 16 * sp + 16]))
    return out


def sms_rgb(c):
    return ((c & 3) * 85, ((c >> 2) & 3) * 85, ((c >> 4) & 3) * 85)


def build_adapter():
    """GameMaker handoff.  The ROM-native part is every number that the observed scenarios reproduce; the rest is a proposal and says so."""
    return dict(
        status="GAMEMAKER ADAPTER PROPOSAL (names are suggestions); every number marked rom_native is reproduced by sign-prize-observed.json",
        rom_native=dict(
            face_size_px=[32, 32], face_origin_relative_to_sign_anchor=[-16, -48], sprite_pieces="8 pieces of 8x16 (x -16,-8,0,8 at y -48 and y -32); the post (tiles $7A,$7C at x -8,0 / y -16) is not selector dependent",
            distinct_faces=["eggman ($12 = $1C)", "sonic ($1B)", "tails ($1D)", "ring ($1E)", "bird ($1F)", "blank ($20)"],
            selector_for_first_pass_class={"0": "$20", "1": "sonic: $1B, tails: $1D", "2": "$1E", "3": "sonic: $1D, tails: $1B", "255": "$1F"},
            face_visible_frames="frame 1 only (rest and idle); spin frames 2..4 and 5 never show a prize face",
            update_counts=dict(contact_to_landing=130, contact_to_child_spawn=131, contact_to_bonus_word_and_equal_digit_life=278, contact_to_player_state_20=280,
                               retouch_request_to_landing=65, retouch_spin_updates=64, face_upload_frames=4, face_upload_order=[
                                   "tiles $6A..$6D (pieces 0,1: top row, left half)", "tiles $6E..$71 (pieces 2,3: top row, right half)",
                                   "tiles $72..$75 (pieces 4,5: bottom row, left half)", "tiles $76..$79 (pieces 6,7: bottom row, right half)"],
                               note="the landing update writes D3B3 and the first four tiles in the same frame; the panel completes three frames later"),
            retry="class 0 shows the blank panel ($20) in state 3, the player is free and the timer stays stopped; the next contact is a 64-update spin with the blank panel and then the re-roll",
            no_second_retry="the re-roll class is (D12F & 7) + 1 = 1..8: class 0 cannot occur, so there are at most two landings and the second one is final",
            sprite_palette="the level's sprite palette (record per zone in sprite_palettes.zones)"),
        proposal=dict(
            sign_fields=dict(prizeClass="+$34: 0..8 or 255", retryUsed="+$35 != 0", faceSelector="$12 until a landing, then the selector chosen by the table above", faceUploadAge="frames since the landing update, 0..3 (4+ = complete)",
                             awarded="true once the landing reward ran; never recompute on the retouch spin"),
            landing_call="chaos_goal_sign_land(sign, zone, playerType, rings, retryUsed, rollByte) -> {class, selector, effect}; apply effects to lives/continues/rings exactly once at that update",
            bonus_handoff="G1-C owns D2A6 (child update 147). G1-D must (a) apply the class-2 ring prize BEFORE that update so global.ring is the post-prize value, (b) give the equal-digit life only from the child code path (once), (c) never add a bonus-based award to the class reward",
            lives_continues="D299 lives (BCD, cap $99, sound $A9 even at the cap); D2C3 continues (BCD, bit 7 cleared, wraps 79 -> 00, no sound, no cap)",
            optional_presentation="a 348x196 view changes nothing in the face data: the face is anchor-relative. Do not alter the sign pan or the sign x registration here (GOAL-FOLLOWUP-1 stays parked)"))


# ------------------------------------------------------------------------------------------------------------------------------------------
# Static census
def prize_tables(rom):
    a = list(rom[off(BANK_OBJ, 0xA919):off(BANK_OBJ, 0xA919) + 64])
    b = list(rom[off(BANK_OBJ, 0xA962):off(BANK_OBJ, 0xA962) + 64])
    return {TABLE_ODD_ZONE_PARITY: a, TABLE_EVEN_ZONE_PARITY: b}


def time_table(rom):
    o = 0x62AD
    return [(u16(rom, o + 4 * i), rom[o + 4 * i + 2], rom[o + 4 * i + 3]) for i in range(10)]


def class_vectors(tables):
    """Class of every BCD ring count 00..99 (list index = decimal value of the BCD byte)."""
    out = {}
    for name, t in tables.items():
        out[name] = [lookup_class(t, int_to_bcd(n)) for n in range(100)]
    return out


def build_static(rom):
    tables = prize_tables(rom)
    tt = time_table(rom)
    st = dict(schema="u3-sign-prize-static/1", base_commit=BASE_COMMIT, rom_sha256=ROM_SHA256)
    st["evidence_legend"] = dict(
        DECODED="numbers read from ROM bytes", BYTE_VERIFIED="instruction fragments compared with the constants in tools/u3_sign_prizes.py (anchors)",
        MODEL="pure Python functions of the decoded tables, re-checked against Z80 execution in sign-prize-controlled.json")
    st["routines"] = [region(rom, n, b, a, e, r) for n, b, a, e, r in ROUTINES]
    st["anchors"] = check_anchors(rom)

    # ---- dynamic loader -------------------------------------------------------------------------------------------------------------------
    st["loader"] = dict(
        evidence="BYTE-VERIFIED ASSEMBLY ($7AC2..$7BA6) + SOURCE-TRACED BEHAVIOR",
        ram=dict(D3B3="requested selector (0 = idle)", D3B4="current entry bank byte (0 = none)", D3B5="tiles left in the current entry", D3B6="source CPU pointer",
                 D3B8="VRAM destination", D3BA="next list entry pointer"),
        selector_table_cpu="7BA6", selector_index="selector - $10, 2 bytes per selector",
        tiles_per_call=4, bytes_per_tile=32, entry_bytes=6, entry_layout="[bank|remap<<7, tiles, vram_lo, vram_hi, src_lo, src_hi]",
        first_call="entry pointer fetched ($7B51/$7B6D) and the first four tiles written in the SAME call",
        end_of_list="a $FF entry runs $7B92: D3B3, D3B4, D3B5, D3B6, D3B8 := 0",
        note="the caller is the main-loop frame step: one call per displayed frame (observed: four consecutive frames for a 16-tile entry)")

    # ---- selectors --------------------------------------------------------------------------------------------------------------------------
    sels = {}
    for s in (SEL_DEFAULT,) + SEL_FACES:
        ptr, entries = decode_selector_list(rom, s)
        tiles = selector_tiles(rom, s)
        face = b"".join(tiles[FACE_TILE0 + k] for k in range(FACE_TILES))
        idx = bytes(v for k in range(FACE_TILES) for row in decode_tile(tiles[FACE_TILE0 + k]) for v in row)
        e0 = entries[0]
        sels[hx(s)] = dict(list_cpu=hx(ptr, 4), entries=entries, face_tile_bytes_sha256=sha(face), face_tile_index_sha256=sha(idx),
                           face_index_histogram={str(k): idx.count(k) for k in range(16) if idx.count(k)}, face_source_cpu=e0["source_cpu"], face_source_file=e0["source_file"])
    st["selectors"] = sels
    ident = [k for k in sels if k != hx(SEL_DEFAULT) and sels[k]["face_tile_bytes_sha256"] == sels[hx(SEL_DEFAULT)]["face_tile_bytes_sha256"]]
    st["selector_identities"] = dict(same_face_as_12=ident, note="$1C is byte-identical to the first block of $12 (the sign's default Eggman face); no routine writes $1C to D3B3")
    st["selector_roles"] = {
        "12": dict(role="default face, written by $A87D when the sign wakes (tiles $6A..$79 face + $7A..$A9 fixed spin/back/pole)", face="Dr. Robotnik"),
        "1B": dict(role="life (Sonic) / continue (Tails)", face="Sonic"),
        "1C": dict(role="never selected (identical to $12 face block)", face="Dr. Robotnik"),
        "1D": dict(role="life (Tails) / continue (Sonic)", face="Tails"),
        "1E": dict(role="ring prize (+10 rings), both characters", face="gold ring"),
        "1F": dict(role="no prize (class $FF, retouch classes 4..8)", face="blue bird"),
        "20": dict(role="retry (class 0): blank grey panel", face="blank panel (index 10 fill)"),
    }
    st["face_selector_constants"] = dict(
        life=[EFFECTS[1][1], EFFECTS[1][2]], continue_=[EFFECTS[3][1], EFFECTS[3][2]], rings=EFFECTS[2][1], none=SELECTOR_NONE, retry=EFFECTS[0][1],
        note="[Sonic (D500 = 1), other (Tails, D500 = 2)]; immediates read from $A9B4/$A9B8/$A9C9/$A9DF/$A9E3/$A9E7/$A9F1")
    imm = {a: rom[off(BANK_OBJ, a) ] for a in (0xA9B4, 0xA9B8, 0xA9C9, 0xA9DF, 0xA9E3, 0xA9E7, 0xA9F1)}
    st["face_selector_immediates"] = {hx(a, 4): hx(v) for a, v in imm.items()}

    # ---- sign mapping ------------------------------------------------------------------------------------------------------------------------
    table, frames = parse_mapping(rom, TYPE_SIGN)
    for f in frames:
        for p in f["pieces"]:
            t = p["tile"]
            p["selector_dependent"] = FACE_TILE0 <= t <= FACE_TILE0 + FACE_TILES - 2
    st["sign_mapping"] = dict(evidence="DECODED DATA (bank $0F)", table_cpu=hx(table, 4), type_pointer_file="3C030", frames=frames,
                              sprite_mode="8x16: each piece uses tile and tile + 1; tile numbers are VRAM tile ids (no base added)",
                              face_pieces="frame 1 only: eight pieces tiles $6A,$6C..$78 form a 32 x 32 panel at x -16..+15, y -48..-17 (anchor relative); frame 5 (other side) uses fixed tiles $9A..$A9")

    base = selector_tiles(rom, SEL_DEFAULT)
    comp = {}
    face_only = {FACE_TILE0 + 2 * k for k in range(8)}
    for s in (SEL_DEFAULT,) + SEL_FACES:
        tiles = dict(base)
        tiles.update(selector_tiles(rom, s))
        x0, y0, w, h, rows = compose_frame(frames[1], tiles, only=face_only)
        _fx, _fy, fw, fh, full = compose_frame(frames[1], tiles)
        comp[hx(s)] = dict(face_x=x0, face_y=y0, face_w=w, face_h=h, face_index_sha256=rows_hash(rows), frame1_w=fw, frame1_h=fh, frame1_index_sha256=rows_hash(full),
                           nonzero_face_pixels=sum(1 for r in rows for v in r if v))
    st["composed_frame1"] = comp
    fixed = {}
    for i in range(2, 6):
        _x, _y, w, h, rows = compose_frame(frames[i], base)
        fixed[str(i)] = dict(w=w, h=h, index_sha256=rows_hash(rows))
    st["fixed_frames_with_selector_12"] = dict(frames=fixed, note="frames 2..4 (side views) and 5 (back) use only tiles $7A..$A9, never rewritten by $1B..$20")

    # ---- palettes ----------------------------------------------------------------------------------------------------------------------------
    st["sprite_palettes"] = dict(evidence="DECODED DATA ($7F3C index table, $3B64D records)", zones=sprite_palettes(rom),
                                 note="the sign is a sprite: its colours are the level's sprite palette (CRAM 16..31), one record per zone, act independent")

    # ---- prize tables --------------------------------------------------------------------------------------------------------------------------
    cv = class_vectors(tables)
    rows = {}
    for name, t in tables.items():
        rows[name] = [[hx(x) for x in t[i * 16:(i + 1) * 16] if x != 0xFF] for i in range(4)]
    by_class = {}
    for name in tables:
        d = {}
        for n in range(100):
            d.setdefault(str(cv[name][n]), []).append(hx(int_to_bcd(n)))
        by_class[name] = d
    dups = {name: sorted({hx(x) for x in t if x != 0xFF and t.count(x) > 1}) for name, t in tables.items()}
    st["prize_tables"] = dict(
        evidence="DECODED DATA + BYTE-VERIFIED ASSEMBLY ($A909 parity, $A9FA CPIR)",
        selection="A := ($D297 + 1); RRCA; carry set -> $A919 else $A962: zone parity, NOT act and NOT character",
        zone_to_table={str(z): zone_table(z) for z in range(6)}, zone_names={str(z): n for z, n in enumerate(ZONE_NAMES)},
        class_rule="class = ((63 - index of first CPIR match) >> 4) & 15 = 3 - index // 16; no match -> $FF",
        bytes=dict((k, list(v)) for k, v in tables.items()), rows_by_class_3_to_0=rows, counts_by_class=by_class,
        class_vector_by_decimal_count={k: v for k, v in cv.items()}, duplicates_inside_a_table=dups,
        counts_per_class={name: {k: len(v) for k, v in by_class[name].items()} for name in tables})
    st["reward_effects"] = dict(
        evidence="BYTE-VERIFIED ASSEMBLY ($A9A2..$AA16) + CONTROLLED (sign-prize-controlled.json)",
        first_pass={str(c): dict(effect=EFFECTS[c][0], selector_sonic=EFFECTS[c][1], selector_other=EFFECTS[c][2]) for c in EFFECTS},
        no_prize=dict(effect="none", selector=SELECTOR_NONE),
        life="CALL $03F2 -> $3104: sound $A9, D299 + 1 (DAA) unless D299 = $99; the sound is requested even at the cap",
        continue_="D2C3 := ((D2C3 + 1) DAA) & $7F: the counter wraps 79 -> 00 and bit 7 (continue-used flag) is cleared; NO cap and NO sound",
        rings="D29A := (D29A + $10) DAA, carry dropped (90 -> 00); no sound; the child bonus (and the tally) then read the NEW ring count",
        retry="class 0: +$35 := $FF, D3B3 := $20, requested state 3 (no reward, no child, no sound)",
        retouch_roll=dict(formula="+$34 := ($D12F & 7) + 1; JP $A9A2", classes={str(k): dict(effect=effect_of(k), selector_sonic=art_of(k, 1), selector_other=art_of(k, 2)) for k in range(1, 9)},
                          probability="3 of 8 rolls reward (life, rings, continue each 1/8); 5 of 8 (classes 4..8) give nothing and show $1F; class 0 can never come out"))

    # ---- bonus ----------------------------------------------------------------------------------------------------------------------------------
    st["bonus_word"] = dict(
        evidence="DECODED DATA ($62AD) + BYTE-VERIFIED ASSEMBLY ($6276, $AB48)",
        time_table=[dict(index=i, limit_bcd_mmss=hx(l, 4), l=hx(lo), h=hx(h)) for i, (l, lo, h) in enumerate(tt)],
        rule="H := entry.H of the first entry whose limit is greater than D2C0:D2BF (BCD mm:ss, strict); L := ((D29A - $11) DAA) + entry.L (DAA); a carry would add 1 to H",
        zero_rule="H|L = 0 -> $0777", equal_digit_rule="H = low digit of L = high digit of L (all three digits equal) -> CALL $03F2 (life +1, sound $A9, cap $99)",
        written="D2A6 := HL at the child's state-3 callback (child update 147; +278 updates after the contact)",
        ring_basis="D29A at that moment, i.e. AFTER a class-2 ring prize",
        comparison_with_poc_g1c=dict(
            poc_formula="chaos_results_bonus: H = 9 - i for the first i < 9 with seconds < 29 + 30 * i",
            rom_limits_seconds=[bcd_to_int(l >> 8) * 60 + bcd_to_int(l & 255) for l, _lo, _h in tt[:9]],
            poc_limits_seconds=[29 + 30 * i for i in range(9)],
            differs_at_index=[i for i in range(9) if bcd_to_int(tt[i][0] >> 8) * 60 + bcd_to_int(tt[i][0] & 255) != 29 + 30 * i],
            consequence="the ROM's last bucket (H = 1) ends at 4:59 (299 s); the POC loop ends it at 4:29 (269 s), so 4:29..4:58 gives H = 0 there and H = 1 in the ROM"))
    st["adapter"] = build_adapter()
    st["bonus_interaction"] = dict(
        order="landing at +130 updates (class reward, ring prize) -> child spawn at +131 -> child update 147 (+278): D2A6 + equal-digit life -> player state $20 at +279 -> act flag -> tally (rings x 10, then bonus x 1)",
        class_one_then_equal_digit="both are separate $03F2 calls: a class-1 sign (or a class-1 roll) AND an equal-digit bonus word give +2 lives (cap $99 each)",
        ring_prize_changes_bonus="class 2 adds 10 rings BEFORE the child reads D29A: the bonus L digit pair and the tally ring count both include the prize")
    return st


# ------------------------------------------------------------------------------------------------------------------------------------------
# Controlled Z80 runs (original routines, explicit RAM)
class Oracle3:
    """Original `$A8FA` / `$AB48` on kosarev/z80 through tools/object_18.Fixture (same fixture the earlier sign study used)."""

    def __init__(self, rom):
        import object_18 as O
        self.O = O
        self.f = O.ready_at_state3(rom, "thz1")
        self.m = self.f.m
        self.slot = O.SLOT

    def landing(self, zone, ptype, rings, retry_flag, d12f, lives, cont):
        f, m = self.f, self.m
        f.restore()
        f.w(0x35, 0xFF if retry_flag else 0)
        m[0xD297] = zone
        m[0xD500] = ptype
        m[0xD29A] = rings
        m[0xD299] = lives
        m[0xD2C3] = cont
        m[0xD12F] = d12f
        m[0xD3B3] = 0
        m[0xDE04] = 0
        m[0xDC00] = 0xEE
        f.call_cb(0xA8FA)
        return dict(cls=f.r(0x34), art=m[0xD3B3], state=f.r(2), retry=f.r(0x35), lives=m[0xD299], cont=m[0xD2C3], rings=m[0xD29A], sound=m[0xDE04], dc00=m[0xDC00])

    def child(self, time_bcd, rings, lives):
        f, m = self.f, self.m
        f.restore()
        m[0xD2BF] = time_bcd & 0xFF
        m[0xD2C0] = time_bcd >> 8
        m[0xD29A] = rings
        m[0xD299] = lives
        m[0xDE04] = 0
        m[0xD292] = 0
        f.call_cb(0xAB48)
        return dict(word=m[0xD2A6] | (m[0xD2A7] << 8), lives=m[0xD299], sound=m[0xDE04], digits=[m[0xD3F2], m[0xD3F3], m[0xD3F4]])

    def chain(self, zone, ptype, rings, time_bcd, lives, cont, retry_flag=0, d12f=0):
        """Landing, retry second landing if class 0, then the child — the Z80 version of award_sequence."""
        land = self.landing(zone, ptype, rings, retry_flag, d12f, lives, cont)
        passes = [land]
        if land["cls"] == 0:
            f, m = self.f, self.m
            # the retry state does not touch the counters; state 3 -> second contact -> state 6 -> $A8FA again with +$35 = $FF
            land = self.landing(zone, ptype, rings, 1, d12f, lives, cont)
            passes.append(land)
        ch = self.child(time_bcd, land["rings"], land["lives"])
        return dict(passes=passes, rings=land["rings"], cont=land["cont"], lives=ch["lives"], word=ch["word"])


TIME_SAMPLES = [0x0000, 0x0028, 0x0029, 0x0058, 0x0059, 0x0128, 0x0129, 0x0158, 0x0159, 0x0228, 0x0229, 0x0258, 0x0259, 0x0328, 0x0329, 0x0358, 0x0359,
                0x0429, 0x0458, 0x0459, 0x0900]
BASE_LIVES = 0x12
BASE_CONT = 0x34


def build_controlled(rom, st=None):
    st = st or build_static(rom)
    tables = prize_tables(rom)
    tt = time_table(rom)
    orc = Oracle3(rom)
    ctl = dict(schema="u3-sign-prize-controlled/1", base_commit=BASE_COMMIT, rom_sha256=ROM_SHA256,
               evidence="CONTROLLED ROUTINE RESULT: original $A8FA / $AB48 executed on kosarev/z80 (tools/oracle.py); each result is compared with the pure model")
    ctl["baseline"] = dict(lives=hx(BASE_LIVES), continues=hx(BASE_CONT), note="rings = the scanned count; rows are [class, selector, lives, continues, rings, requested state, +$35]")

    # ---- first-pass scan: both tables, both player types, all 100 BCD counts ----------------------------------------------------------------
    scan = {}
    mismatches = []
    for zone, name in ((0, TABLE_ODD_ZONE_PARITY), (1, TABLE_EVEN_ZONE_PARITY)):
        for ptype in (PTYPE_SONIC, PTYPE_OTHER):
            rows = []
            for n in range(100):
                rings = int_to_bcd(n)
                z = orc.landing(zone, ptype, rings, 0, 0, BASE_LIVES, BASE_CONT)
                p = prize_landing(tables, zone, ptype, rings, 0, 0, BASE_LIVES, BASE_CONT)
                row = [z["cls"], z["art"], z["lives"], z["cont"], z["rings"], z["state"], z["retry"]]
                exp = [p["cls"], p["art"], p["lives"], p["cont"], p["rings"], p["state"], p["retry"]]
                if row != exp:
                    mismatches.append(dict(table=name, ptype=ptype, rings=hx(rings), z80=row, model=exp))
                rows.append(row)
            scan["%s_p%d" % (name, ptype)] = rows
    ctl["first_pass_scan"] = dict(zone_used={TABLE_ODD_ZONE_PARITY: 0, TABLE_EVEN_ZONE_PARITY: 1}, rows=scan, model_mismatches=mismatches)

    # parity: every zone 0..5 (and the act byte is irrelevant)
    par = {}
    for zone in range(6):
        par[str(zone)] = dict(table=zone_table(zone), classes=[orc.landing(zone, PTYPE_SONIC, int_to_bcd(n), 0, 0, BASE_LIVES, BASE_CONT)["cls"] for n in range(100)])
    ctl["zone_parity"] = dict(per_zone=par, all_match_model=all(par[str(z)]["classes"] == class_vectors(tables)[zone_table(z)] for z in range(6)))

    # ---- retouch re-roll: d12f full byte, both players ----------------------------------------------------------------------------------------
    rr = {}
    bad = []
    for ptype in (PTYPE_SONIC, PTYPE_OTHER):
        rows = []
        for d in range(256):
            z = orc.landing(0, ptype, 0x16, 1, d, BASE_LIVES, BASE_CONT)
            p = prize_landing(tables, 0, ptype, 0x16, 1, d, BASE_LIVES, BASE_CONT)
            row = [z["cls"], z["art"], z["lives"], z["cont"], z["rings"], z["state"], z["retry"]]
            if row != [p["cls"], p["art"], p["lives"], p["cont"], p["rings"], p["state"], p["retry"]]:
                bad.append(dict(ptype=ptype, d12f=d))
            rows.append(row)
        rr["p%d" % ptype] = rows
    ctl["retouch_reroll"] = dict(
        note="+$35 = $FF, ring count $16 (class 0 on the odd table): rows indexed by the full D12F byte; the result depends only on D12F & 7",
        rows=rr, depends_only_on_low_three_bits=all(rr["p1"][d] == rr["p1"][d & 7] for d in range(256)), model_mismatches=bad,
        class_zero_reachable=any(r[0] == 0 for rows in rr.values() for r in rows),
        retry_flag_after=sorted({r[6] for rows in rr.values() for r in rows}))
    # the ring count does not matter on a retouch
    ctl["retouch_ring_independence"] = dict(
        all_counts_same_class=all(orc.landing(z, 1, int_to_bcd(n), 1, 5, BASE_LIVES, BASE_CONT)["cls"] == 6 for z in (0, 1) for n in range(100)),
        note="D12F & 7 = 5 -> class 6 for every ring count and both zone parities")

    # ---- caps and wraps ---------------------------------------------------------------------------------------------------------------------------
    caps = dict(lives=[], continues=[], rings=[])
    capbad = []
    for lv in (0x00, 0x01, 0x09, 0x10, 0x98, 0x99):
        z = orc.landing(0, PTYPE_SONIC, 0x55, 0, 0, lv, BASE_CONT)
        caps["lives"].append([lv, z["lives"], z["sound"]])
        if z["lives"] != grant_life(lv):
            capbad.append(("life", lv))
    for ct in list(range(0x00, 0x80)) + [0x80, 0x81, 0x89, 0x99, 0xFF]:
        if ct < 0x80 and not is_bcd(ct):
            continue
        z = orc.landing(0, PTYPE_SONIC, 0x15, 0, 0, BASE_LIVES, ct)
        caps["continues"].append([ct, z["cont"], z["lives"]])
        if z["cont"] != grant_continue(ct):
            capbad.append(("continue", ct))
    for rg in (0x09, 0x19, 0x29, 0x39, 0x49, 0x59, 0x69, 0x79, 0x89):      # class 2 counts of the odd table
        z = orc.landing(0, PTYPE_SONIC, rg, 0, 0, BASE_LIVES, BASE_CONT)
        caps["rings"].append([0, rg, z["rings"]])
        if z["rings"] != grant_rings(rg):
            capbad.append(("rings_odd", rg))
    for rg in (0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80, 0x90):     # class 2 counts of the even table
        z = orc.landing(1, PTYPE_SONIC, rg, 0, 0, BASE_LIVES, BASE_CONT)
        caps["rings"].append([1, rg, z["rings"]])
        if z["rings"] != grant_rings(rg):
            capbad.append(("rings_even", rg))
    ctl["caps"] = dict(
        lives_rows="[lives before, lives after, sound D3.. DE04 (A9 = life sound)]", continues_rows="[before, after, lives after]", rings_rows="[table parity zone, ring count, ring count after]",
        rows=caps, model_mismatches=capbad,
        sound_at_life_cap=sorted({r[2] for r in caps["lives"]}),
        continue_wrap_at_79=[r for r in caps["continues"] if r[0] == 0x79])
    ctl["side_effects"] = dict(
        dc00_after_match=sorted({orc.landing(0, 1, int_to_bcd(n), 0, 0, BASE_LIVES, BASE_CONT)["dc00"] for n in (15, 9, 55, 16)}),
        dc00_after_no_match=orc.landing(0, 1, 0x01, 0, 0, BASE_LIVES, BASE_CONT)["dc00"],
        note="$A9FA stores the matched ring count at $DC00 (initialised to $EE in the fixture); no reader of $DC00 was found by an operand scan (UNRESOLVED, no observable effect)")

    # ---- bonus word -----------------------------------------------------------------------------------------------------------------------------------
    bw = {}
    bwbad = []
    for t in TIME_SAMPLES:
        rows = []
        for n in range(100):
            rings = int_to_bcd(n)
            c = orc.child(t, rings, BASE_LIVES)
            word, eq = child_bonus(tt, t, rings)
            if c["word"] != word or (c["lives"] != BASE_LIVES) != bool(eq):
                bwbad.append(dict(time=hx(t, 4), rings=hx(rings), z80=[c["word"], c["lives"]], model=[word, eq]))
            rows.append(c["word"])
        bw[hx(t, 4)] = rows
    eq_cases = []
    for t in TIME_SAMPLES:
        for n in range(100):
            if child_bonus(tt, t, int_to_bcd(n))[1]:
                eq_cases.append([hx(t, 4), hx(int_to_bcd(n)), hx(child_bonus(tt, t, int_to_bcd(n))[0], 4)])
    ctl["bonus_word"] = dict(
        note="D2A6 for every BCD ring count and 21 time samples (time = D2C0:D2BF BCD mmss); the original $AB48 ran each cell",
        times=[hx(t, 4) for t in TIME_SAMPLES], words_by_time=bw, model_mismatches=bwbad, equal_digit_cases=eq_cases,
        zero_to_0777=[[hx(t, 4), hx(int_to_bcd(n))] for t in TIME_SAMPLES for n in range(100) if bonus_word(tt, t, int_to_bcd(n)) == (0, 0)],
        panel_digit_bytes=dict(example_time="0029", example_rings="99", digits=orc.child(0x0029, 0x99, BASE_LIVES)["digits"],
                               note="D3F2..D3F4 := $2E + 2 * digit (child panel tile offsets, G1-D out of scope)"))

    # ---- full chain matrix (landing + retry + child) -------------------------------------------------------------------------------------------------
    chain_rows = []
    chainbad = []
    interesting = [0x0000, 0x0029, 0x0059, 0x0129, 0x0229, 0x0359, 0x0459, 0x0500]
    for zone in (0, 1):
        for ptype in (PTYPE_SONIC, PTYPE_OTHER):
            for n in range(100):
                for t in interesting:
                    rings = int_to_bcd(n)
                    d12f = (n + t) & 7
                    z = orc.chain(zone, ptype, rings, t, BASE_LIVES, BASE_CONT, 0, d12f)
                    m = award_sequence(tables, tt, zone, ptype, rings, t, BASE_LIVES, BASE_CONT, 0, d12f)
                    row = [zone, ptype, rings, t, z["lives"], z["cont"], z["rings"], z["word"]]
                    exp = [zone, ptype, rings, t, m["lives"], m["continues"], m["rings"], m["bonus_word"]]
                    if row != exp:
                        chainbad.append(dict(z80=row, model=exp))
                    chain_rows.append(row)
    ctl["chain"] = dict(
        note="columns [zone, player type, ring count, time, lives after, continues after, rings after, D2A6]; baseline lives $12, continues $34; a class-0 count retries and is re-rolled with D12F & 7 = (ring + time) & 7",
        times=[hx(t, 4) for t in interesting], rows=chain_rows, rows_sha256=sha(json.dumps(chain_rows).encode()), model_mismatches=chainbad,
        double_life_cases=[dict(zone=r[0], ptype=r[1], rings=hx(r[2]), time=hx(r[3], 4), lives=hx(r[4])) for r in chain_rows if bcd_to_int(r[4]) - bcd_to_int(BASE_LIVES) == 2][:80],
        double_life_count=sum(1 for r in chain_rows if bcd_to_int(r[4]) - bcd_to_int(BASE_LIVES) == 2))
    return ctl


# ------------------------------------------------------------------------------------------------------------------------------------------
# Emulated original frames (g0_rig whole-game session)
def placement_sign(rom, zone, act):
    """Sign anchor of an act from the placement list the creator `$80EB` walks (record world X/Y = stored - 256)."""
    b = 0x1C * 0x4000

    def rd(c):
        return rom[b + c - 0x8000]

    def rd16(c):
        return rd(c) | (rd(c + 1) << 8)
    p = rd16(rd16(0x8546 + 2 * zone) + 2 * act)
    while rd(p) != 0xFF:
        if rd(p) == TYPE_SIGN:
            return rd16(p + 1) - 256, rd16(p + 3) - 256
        p += 9
    raise ValueError("no sign in zone %d act %d" % (zone, act))


def arrival_near(sx, sy):
    def fn(mm):
        mm.w16(0xD2D6, sx - 260)
        mm.w16(0xD2D8, sy - 118)
        mm.w16(0xD511, sx - 160)
        mm.w16(0xD514, sy - 58)
    return fn


def find_sign_slot(m):
    for slot in range(0xD540, 0xDB80, 0x40):
        if m[slot] == TYPE_SIGN:
            return slot
    return None


def find_child_slot(m):
    for slot in range(0xD540, 0xDB80, 0x40):
        if m[slot] == TYPE_CHILD:
            return slot
    return None


def run_clear(rom, st, zone, act, character, rings, *, timer=None, lives=None, continues=None, retry_wait=None, max_frames=3400, shots=True, label=""):
    """One complete ordinary clear of the unmodified ROM.  Returns the observation record.

    Fixtures (all reported in the record): ARRIVAL (player/camera 160 px before the sign), RAM presets at gameplay start (`rings`, optional `timer` mm:ss BCD word,
    `lives`, `continues`), joypad: RIGHT until the sign lands; after a class-0 landing: idle `retry_wait` frames, then LEFT until the second contact; RIGHT again."""
    from g0_rig import Session
    from sms_frame_harness import BTN_RIGHT, BTN_LEFT
    sx, sy = placement_sign(rom, zone, act)
    S = Session(rom)
    if (zone, act) != (0, 0):
        S.set_start_index(zone, act)
    S.boot_new_game(character=character, arrival=arrival_near(sx, sy))
    m = S.m
    pre = dict(rings=rings)
    S.w("rings", rings)
    if timer is not None:
        m[0xD2BF] = timer & 0xFF
        m[0xD2C0] = timer >> 8
        pre["timer_D2C0_D2BF"] = hx(timer, 4)
    if lives is not None:
        m[0xD299] = lives
        pre["lives"] = hx(lives)
    if continues is not None:
        m[0xD2C3] = continues
        pre["continues"] = hx(continues)
    ptype = m[0xD500]
    base = dict(lives=m[0xD299], continues=m[0xD2C3], rings=m[0xD29A], timer=[m[0xD2C0], m[0xD2BF]], D500=ptype, zone=m[0xD297], act=m[0xD298], character=m[0xD2C8])
    ev = []                       # [harness frame, event, detail, sign object updates so far]
    cnt = dict(u=0)

    def emit(frame, name, detail):
        ev.append([frame, name, detail, cnt["u"]])

    def hook_update(mm):
        if mm.mem[mm.cpu.ix] == TYPE_SIGN:       # one scheduler pass over the sign slot = one ROM object update (immune to lag frames)
            cnt["u"] += 1
    f0 = S.s.frame
    cap = dict(roll=None, sign_hook=[])

    def hook_aa19(mm):
        if mm.slot[2] == BANK_OBJ:
            cap["roll"] = mm.mem[0xD12F]
    S.hook(0xAA19, hook_aa19)
    S.hook(0x5DF1, hook_update)

    def hook_land(mm):
        if mm.slot[2] == BANK_OBJ:
            emit(mm.frame - f0 + 1, "landing_call", dict(plus35=mm.mem[mm.cpu.ix + 0x35], rings=mm.mem[0xD29A], d12f=mm.mem[0xD12F]))
    S.hook(0xA8FA, hook_land)

    prev = dict(d3b3=0, state=None, req=None, cls=None, retry=None, lives=m[0xD299], cont=m[0xD2C3], rings=m[0xD29A], d2a6=m[0xD2A6] | (m[0xD2A7] << 8), p501=m[0xD501], d293=m[0xD293],
                face=None, child=False, snd=0, timer=m[0xD2BE])
    sounds = {}
    phase = "right"
    idle_left = 0
    retry_seen_at = None
    face_log = []
    sel_at = {}
    caps = {}
    final_wait = 0
    for i in range(max_frames):
        sl = find_sign_slot(m)
        sst = (m[sl + 1], m[sl + 2]) if sl else None
        if phase == "right" and sl and m[sl + 0x35] == 0xFF and m[sl + 1] == 3 and retry_wait is not None and m[0xD3B3] == 0 and retry_seen_at is None:
            retry_seen_at = i
            phase = "idle"
            idle_left = retry_wait
        if phase == "idle":
            if idle_left <= 0:
                phase = "left"
            else:
                idle_left -= 1
        if phase == "left" and sl and m[sl + 1] == 6:
            phase = "right"
        pad = BTN_RIGHT if phase == "right" else (BTN_LEFT if phase == "left" else 0)
        if m[0xD501] == 0x20:
            pad = 0
        S.s.pad = pad
        S.s.run_frame()
        fr = S.s.frame - f0
        sl = find_sign_slot(m)
        if sl:
            state = m[sl + 1]
            req = m[sl + 2]
            cls = m[sl + 0x34]
            retry = m[sl + 0x35]
            if req != prev["req"] and req in (4, 5, 6) or (req == 3 and prev["req"] == 5):
                emit(fr, "sign_request", dict(request=req, plus34=cls, plus35=retry))
            if state != prev["state"]:
                emit(fr, "sign_state", dict(state=state, plus34=cls, plus35=retry))
            if cls != prev["cls"] and prev["state"] is not None:
                emit(fr, "class_set", dict(plus34=cls))
            prev.update(state=state, req=req, cls=cls, retry=retry)
        if m[0xD2BE] != prev["timer"]:
            emit(fr, "timer_run_flag", dict(D2BE=hx(m[0xD2BE])))
            prev["timer"] = m[0xD2BE]
        d3b3 = m[0xD3B3]
        if d3b3 != prev["d3b3"] and d3b3:
            emit(fr, "selector_write", dict(d3b3=d3b3, bank_byte=m[0xD3B4], tiles_left=m[0xD3B5]))
        prev["d3b3"] = d3b3
        face = sha(S.s.vram[FACE_TILE0 * 32:(FACE_TILE0 + FACE_TILES) * 32])
        if face != prev["face"]:
            face_log.append((fr, cnt["u"], face))
            prev["face"] = face
        for key, addr, label_ in (("lives", 0xD299, "lives"), ("cont", 0xD2C3, "continues"), ("rings", 0xD29A, "rings")):
            if m[addr] != prev[key]:
                emit(fr, label_, dict(before=hx(prev[key]), after=hx(m[addr])))
                prev[key] = m[addr]
        d2a6 = m[0xD2A6] | (m[0xD2A7] << 8)
        if d2a6 != prev["d2a6"]:
            emit(fr, "bonus_word_D2A6", dict(word=hx(d2a6, 4), time=hx(m[0xD2BF] | (m[0xD2C0] << 8), 4), rings=hx(m[0xD29A])))
            prev["d2a6"] = d2a6
        ch = find_child_slot(m)
        if ch and not prev["child"]:
            emit(fr, "child_19_spawned", dict(state=m[ch + 1]))
        prev["child"] = bool(ch)
        if m[0xDE04] != prev["snd"]:
            if m[0xDE04]:
                k = hx(m[0xDE04])
                first, last, count = sounds.get(k, [fr, fr, 0])
                sounds[k] = [first, fr, count + 1]
            prev["snd"] = m[0xDE04]
        if m[0xD501] == 0x20 and prev["p501"] != 0x20:
            emit(fr, "player_state_20", {})
        prev["p501"] = m[0xD501]
        if m[0xD293] & 0x30 and not prev["d293"] & 0x30:
            emit(fr, "act_clear_flag", dict(d293=hx(m[0xD293])))
            prev["d293"] = m[0xD293]
        # composed-frame checks: idle sign (default face), retry panel, landed sign
        if d3b3 == SEL_DEFAULT and "default" not in sel_at:
            sel_at["default"] = fr
        if d3b3 == EFFECTS[0][1] and "retry" not in sel_at:
            sel_at["retry"] = fr
        if sl:
            if "default" in sel_at and "default" not in caps and m[sl + 1] == 3 and m[sl + 0x35] == 0 and fr - sel_at["default"] >= 30:
                caps["default"] = capture_sign(S, st, sl, zone)
            if "retry" in sel_at and "retry" not in caps and m[sl + 1] == 3 and m[sl + 0x35] == 0xFF and fr - sel_at["retry"] >= 10:
                caps["retry"] = capture_sign(S, st, sl, zone)
            if m[sl + 1] == 5 and "final" not in caps:
                final_wait += 1
                if final_wait == 14:
                    caps["final"] = capture_sign(S, st, sl, zone)
        if m[0xD293] & 0x30:
            break
    else:
        emit(S.s.frame - f0, "TIMEOUT", {})
    final = dict(lives=m[0xD299], continues=m[0xD2C3], rings=m[0xD29A], D2A6=m[0xD2A6] | (m[0xD2A7] << 8), timer=[m[0xD2C0], m[0xD2BF]])
    cls_final = prev["cls"]
    rec = dict(sounds={k: v for k, v in sorted(sounds.items())},label=label, zone=zone, act=act, character=character, player_type=ptype, sign=[sx, sy], rings_in=hx(rings), fixtures=_fixtures(pre, retry_wait),
               base=dict(lives=hx(base["lives"]), continues=hx(base["continues"]), rings=hx(base["rings"]), timer_D2C0_D2BF=hx(base["timer"][0] << 8 | base["timer"][1], 4)),
               final=dict(lives=hx(final["lives"]), continues=hx(final["continues"]), rings=hx(final["rings"]), D2A6=hx(final["D2A6"], 4)),
               events=ev, face_uploads=[[f, u, h[:16]] for f, u, h in face_log], roll_D12F=cap["roll"], final_plus34=cls_final, captures=caps)
    return rec


def _fixtures(pre, retry_wait):
    fx = ["ARRIVAL: player and camera placed 160 px before the sign at the start-position loader return ($4E97)", "PAD: RIGHT until the act-clear flag"]
    if pre:
        fx.append("RAM at gameplay start: " + json.dumps(pre, sort_keys=True))
    if retry_wait is not None:
        fx.append("PAD after a class-0 landing: idle %d frames, LEFT until the second contact, then RIGHT" % retry_wait)
    return fx


def capture_sign(S, st, slot, zone):
    """Sign pieces in the SAT, face pixel identity against the static decode, sprite palette, foreground-priority masking."""
    m = S.m
    sat = S.s.sat()
    face_tiles = {FACE_TILE0 + 2 * k for k in range(8)}
    pieces = [(i, y, x, n) for i, y, x, n in sat if n in face_tiles and y < 0xC0]     # entries with Y >= $E0 wrap above the screen (unused slots)
    if len(pieces) != 8:
        return dict(error="face pieces in SAT: %d" % len(pieces), sat=[list(e) for e in sat][:20])
    x0 = min(p[2] for p in pieces)
    y0 = min(p[1] for p in pieces) + 1
    vram_face = bytes(S.s.vram[FACE_TILE0 * 32:(FACE_TILE0 + FACE_TILES) * 32])
    sel_hash = sha(vram_face)
    match_sel = [k for k, v in st["selectors"].items() if v["face_tile_bytes_sha256"] == sel_hash]
    rgb, layer, bg_index, sprite_index = S.s.render()
    tiles = {k: bytes(S.s.vram[k * 32:(k + 1) * 32]) for k in range(FACE_TILE0, FACE_TILE0 + FACE_TILES)}
    _fx, _fy, w, h, rows = compose_frame(dict(pieces=[dict(x=p[2] - x0, y=p[1] + 1 - y0, tile=p[3]) for p in pieces]), tiles)
    ok = masked = other = total = 0
    masked_xy = []
    for yy in range(h):
        for xx in range(w):
            e = rows[yy][xx]
            if not e:
                continue
            total += 1
            px, py = x0 + xx, y0 + yy
            if not (0 <= px < 256 and 0 <= py < 192):
                other += 1
                continue
            s = sprite_index[py][px]
            if s == 16 + e and layer[py][px] == "S":
                ok += 1
            elif s == 16 + e:
                masked += 1
                masked_xy.append([xx, yy])
            else:
                other += 1
    cram = list(S.s.cram[16:32])
    anchor = [m[slot + 0x11] | (m[slot + 0x12] << 8), m[slot + 0x14] | (m[slot + 0x15] << 8)]
    camera = [S.u16(0xD174), S.u16(0xD176)]
    return dict(camera_D174_D176=camera, face_origin_minus_screen_anchor=[x0 - (anchor[0] - camera[0]), y0 - (anchor[1] - camera[1])],
                sat_pieces=[[p[2], p[1] + 1, p[3]] for p in sorted(pieces, key=lambda q: (q[1], q[2]))], face_origin_screen=[x0, y0], sign_anchor_world=[m[slot + 0x11] | (m[slot + 0x12] << 8), m[slot + 0x14] | (m[slot + 0x15] << 8)],
                vram_face_sha256=sel_hash[:16], vram_face_equals_selector=match_sel, sprite_palette_cram=cram,
                sprite_palette_equals_rom_zone=(cram == st["sprite_palettes"]["zones"][str(zone)]["sprite_colours"]), face_pixels_total=total, face_pixels_visible_sprite_on_top=ok,
                face_pixels_masked_by_bg_priority=masked, masked_pixels_face_xy=masked_xy, face_pixels_hidden_other=other)


def run_retry_hold(rom, st, mode, frames=900, rings=0x16, zone=0, act=0):
    """After a class-0 landing leave the sign alone for `frames` frames (`mode`: RIGHT held against the view clamp, or no input) and report the state:
    a retry has no timeout, no child, no act clear; the timer stays stopped; the sign stays in the window (the camera is locked)."""
    from g0_rig import Session
    from sms_frame_harness import BTN_RIGHT
    sx, sy = placement_sign(rom, zone, act)
    S = Session(rom)
    S.boot_new_game(character=0, arrival=arrival_near(sx, sy))
    m = S.m
    S.w("rings", rings)
    retry_at = None
    for i in range(3000):
        sl = find_sign_slot(m)
        if retry_at is None and sl and m[sl + 1] == 3 and m[sl + 0x35] == 0xFF and m[0xD3B3] == 0:
            retry_at = i
        if retry_at is not None and i >= retry_at + frames:
            break
        S.s.pad = BTN_RIGHT if (retry_at is None or mode == "right") and m[0xD501] != 0x20 else 0
        S.s.run_frame()
    sl = find_sign_slot(m)
    cap = capture_sign(S, st, sl, zone) if sl else None
    return dict(mode=mode, frames_held=frames, rings_in=hx(rings), sign_present=bool(sl), sign_state=m[sl + 1] if sl else None, plus34=m[sl + 0x34] if sl else None,
                plus35=m[sl + 0x35] if sl else None, timer_run_D2BE=m[0xD2BE], act_flag_D293=hx(m[0xD293]), child_present=find_child_slot(m) is not None, player_state=m[0xD501],
                continues=hx(m[0xD2C3]), lives=hx(m[0xD299]), rings=hx(m[0xD29A]), player_minus_camera_x=(S.u16(0xD511) - S.u16(0xD174)), retry_face=(cap or {}).get("vram_face_equals_selector"))


def scenario_list():
    """(label, zone, act, character, rings BCD, extra kwargs).  A deliberately bounded set (see the assignment)."""
    s = []
    for r in (0x15, 0x09, 0x55, 0x01):
        s.append(("thz1_sonic_r%02X" % r, 0, 0, 0, r, {}))
    for k in range(9):
        s.append(("thz1_sonic_r16_retouch_wait%d" % k, 0, 0, 0, 0x16, dict(retry_wait=k)))
    for r in (0x15, 0x55, 0x09):
        s.append(("thz1_tails_r%02X" % r, 0, 0, 1, r, {}))
    s.append(("thz1_tails_r16_retouch_wait0", 0, 0, 1, 0x16, dict(retry_wait=0)))
    s.append(("thz1_tails_r16_retouch_wait3", 0, 0, 1, 0x16, dict(retry_wait=3)))
    for zone in range(6):
        for r in (0x15, 0x24):
            s.append(("zone%d_act0_sonic_r%02X" % (zone, r), zone, 0, 0, r, {}))
    for zone in range(6):
        s.append(("zone%d_act1_sonic_r15" % zone, zone, 1, 0, 0x15, {}))
    s.append(("zone1_sonic_r00_even_continue", 1, 0, 0, 0x00, {}))
    s.append(("zone1_sonic_r18_even_retry", 1, 0, 0, 0x18, dict(retry_wait=0)))
    s.append(("thz1_sonic_r99_t0040_two_lives", 0, 0, 0, 0x99, dict(timer=0x0040)))
    s.append(("zone1_sonic_r11_t0500_zero_word_two_lives", 1, 0, 0, 0x11, dict(timer=0x0500)))
    s.append(("thz1_sonic_r55_lives99_cap", 0, 0, 0, 0x55, dict(lives=0x99)))
    s.append(("thz1_sonic_r15_continues79_wrap", 0, 0, 0, 0x15, dict(continues=0x79)))
    s.append(("thz1_sonic_r09_ring_prize_bonus", 0, 0, 0, 0x09, dict(timer=0x0100)))
    return s


def build_observed(rom, st=None, progress=print, only=None):
    st = st or build_static(rom)
    ob = dict(schema="u3-sign-prize-observed/1", base_commit=BASE_COMMIT, rom_sha256=ROM_SHA256,
              evidence="EMULATED ORIGINAL FRAME: unmodified ROM in the approximate SMS harness (frame counts are harness frames, +-1 against ROM updates)",
              scenarios={})
    for label, zone, act, ch, rings, kw in scenario_list():
        if only and label not in only:
            continue
        progress("observe %s" % label)
        ob["scenarios"][label] = run_clear(rom, st, zone, act, ch, rings, label=label, **kw)
    if not only:
        progress("observe retry holds")
        ob["retry_hold"] = {mode: run_retry_hold(rom, st, mode) for mode in ("right", "idle")}
    return ob


# ------------------------------------------------------------------------------------------------------------------------------------------
# Exports (ignored build/u3): deterministic indexed graphics
def _png_indexed(path, w, h, rows, palette16):
    from PIL import Image
    im = Image.new("P", (w, h))
    pal = []
    for c in palette16:
        pal.extend(sms_rgb(c))
    pal.extend([0] * (768 - len(pal)))
    im.putpalette(pal)
    im.putdata([v for row in rows for v in row])
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, optimize=False, compress_level=9)


def export_assets(rom, st=None, out=BUILD):
    """Write raw tile blocks and indexed PNGs; the manifest lists the hash of the palette-index bytes (never of PNG bytes)."""
    st = st or build_static(rom)
    pals = st["sprite_palettes"]["zones"]
    thz = pals["0"]["sprite_colours"]
    man = dict(format=1, rom_sha256=ROM_SHA256, rows_hash="sha256 of the row-major palette-index bytes (0..15, 0 = transparent sprite colour)", assets={})
    _t, frames = parse_mapping(rom, TYPE_SIGN)
    base = selector_tiles(rom, SEL_DEFAULT)
    face_only = {FACE_TILE0 + 2 * k for k in range(8)}

    def add(name, w, h, rows, kind, note="", palette=thz):
        _png_indexed(out / name, w, h, rows, palette)
        man["assets"][name] = dict(kind=kind, width=w, height=h, index_sha256=rows_hash(rows), note=note)

    sheet = {}
    for s in (SEL_DEFAULT,) + SEL_FACES:
        tiles = dict(base)
        tiles.update(selector_tiles(rom, s))
        raw = b"".join(tiles[FACE_TILE0 + k] for k in range(FACE_TILES))
        (out / "tiles").mkdir(parents=True, exist_ok=True)
        (out / "tiles" / ("selector_%s_face_tiles.bin" % hx(s))).write_bytes(raw)
        _x, _y, w, h, rows = compose_frame(frames[1], tiles, only=face_only)
        add("faces/face_%s.png" % hx(s), w, h, rows, "face 32x32", "selector $%s, palette = THZ sprite record" % hx(s))
        _x, _y, w2, h2, full = compose_frame(frames[1], tiles)
        add("frames/frame1_%s.png" % hx(s), w2, h2, full, "sign frame 1", "face + pole, anchor-relative origin (%d,%d)" % (_x, _y))
        sheet[s] = (tiles, rows)
    for i in range(2, 6):
        _x, _y, w, h, rows = compose_frame(frames[i], base)
        add("frames/frame%d_fixed.png" % i, w, h, rows, "sign frame %d" % i, "fixed tiles only; independent of selectors $1B..$20")
    # one contact sheet per zone palette: seven faces side by side
    for z in range(6):
        pal = pals[str(z)]["sprite_colours"]
        W = 7 * 40
        rows = [[0] * W for _ in range(36)]
        for n, s in enumerate((SEL_DEFAULT,) + SEL_FACES):
            fr = sheet[s][1]
            for y in range(32):
                for x in range(32):
                    rows[2 + y][n * 40 + 4 + x] = fr[y][x]
        add("sheets/faces_zone%d.png" % z, W, 36, rows, "contact sheet", "faces $12,$1B,$1C,$1D,$1E,$1F,$20 with the zone %d sprite palette" % z, palette=pal)
    return man


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


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def tables_of(st):
    return {k: list(v) for k, v in st["prize_tables"]["bytes"].items()}


def time_table_of(st):
    return [(int(e["limit_bcd_mmss"], 16), int(e["l"], 16), int(e["h"], 16)) for e in st["bonus_word"]["time_table"]]


def validate_static(st):
    errs = []
    if st["rom_sha256"] != ROM_SHA256:
        errs.append("rom sha")
    if st["base_commit"] != BASE_COMMIT:
        errs.append("base commit")
    for a in st["anchors"]:
        if not a["ok"] or a["expected"] != a["actual"]:
            errs.append("anchor " + a["name"])
    tables = tables_of(st)
    for k, t in tables.items():
        if len(t) != 64:
            errs.append("table length " + k)
    cv = class_vectors(tables)
    if cv != st["prize_tables"]["class_vector_by_decimal_count"]:
        errs.append("class vectors differ from the model")
    for z in range(6):
        if st["prize_tables"]["zone_to_table"][str(z)] != zone_table(z):
            errs.append("zone parity %d" % z)
    # table decode: each BCD count at most once per table; classes 0..3 + $FF only
    for k, t in tables.items():
        vals = [x for x in t if x != 0xFF]
        if len(vals) != len(set(vals)):
            errs.append("duplicate count in " + k)
        if not all(is_bcd(x) for x in vals):
            errs.append("non-BCD count in " + k)
    for k, c in cv.items():
        if set(c) - {0, 1, 2, 3, 0xFF}:
            errs.append("unexpected class in " + k)
    # selectors
    ids = {}
    for k, v in st["selectors"].items():
        e0 = v["entries"][0]
        if e0["tiles"] != FACE_TILES or e0["tile_base"] != FACE_TILE0 or e0["bank"] != BANK_FACE or e0["remap"]:
            errs.append("selector entry " + k)
        ids.setdefault(v["face_tile_bytes_sha256"], []).append(k)
    for k in ("1B", "1D", "1E", "1F", "20"):
        if len(ids[st["selectors"][k]["face_tile_bytes_sha256"]]) != 1:
            errs.append("face %s not unique" % k)
    if sorted(ids[st["selectors"]["12"]["face_tile_bytes_sha256"]]) != ["12", "1C"]:
        errs.append("12/1C identity")
    srcs = [int(st["selectors"][k]["face_source_file"], 16) for k in ("1B", "1C", "1D", "1E", "1F", "20")]
    if any(b - a != 0x200 for a, b in zip(srcs, srcs[1:])):
        errs.append("face blocks are not 512 bytes apart")
    comp = st["composed_frame1"]
    if len({v["face_index_sha256"] for v in comp.values()}) != 6:
        errs.append("composed face hashes (expected 6 distinct among 7 selectors)")
    if comp["12"]["face_index_sha256"] != comp["1C"]["face_index_sha256"]:
        errs.append("12 vs 1C composed")
    # immediates agree with the model constants
    imm = st["face_selector_immediates"]
    want = {"A9B4": EFFECTS[1][1], "A9B8": EFFECTS[1][2], "A9C9": EFFECTS[2][1], "A9DF": EFFECTS[3][1], "A9E3": EFFECTS[3][2], "A9E7": SELECTOR_NONE, "A9F1": EFFECTS[0][1]}
    for a, v in want.items():
        if int(imm[a], 16) != v:
            errs.append("immediate " + a)
    # model-only invariants
    tt = time_table_of(st)
    if [e[2] for e in tt] != [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]:
        errs.append("time table H column")
    if any(e[1] != 0 for e in tt):
        errs.append("time table L column not zero")
    return errs


def validate_controlled(ctl, st):
    errs = []
    tables = tables_of(st)
    tt = time_table_of(st)
    if ctl["first_pass_scan"]["model_mismatches"]:
        errs.append("first-pass scan has Z80/model mismatches")
    for key, rows in ctl["first_pass_scan"]["rows"].items():
        name, p = key.rsplit("_p", 1)
        zone = 0 if name == TABLE_ODD_ZONE_PARITY else 1
        for n, row in enumerate(rows):
            m = prize_landing(tables, zone, int(p), int_to_bcd(n), 0, 0, BASE_LIVES, BASE_CONT)
            if row != [m["cls"], m["art"], m["lives"], m["cont"], m["rings"], m["state"], m["retry"]]:
                errs.append("scan row %s %d" % (key, n))
                break
    if not ctl["zone_parity"]["all_match_model"]:
        errs.append("zone parity")
    rr = ctl["retouch_reroll"]
    if rr["model_mismatches"] or not rr["depends_only_on_low_three_bits"] or rr["class_zero_reachable"] or rr["retry_flag_after"] != [255]:
        errs.append("retouch reroll")
    for key, rows in rr["rows"].items():
        for d, row in enumerate(rows):
            m = prize_landing(tables, 0, int(key[1:]), 0x16, 1, d, BASE_LIVES, BASE_CONT)
            if row != [m["cls"], m["art"], m["lives"], m["cont"], m["rings"], m["state"], m["retry"]]:
                errs.append("reroll row %s %d" % (key, d))
                break
    if ctl["caps"]["model_mismatches"]:
        errs.append("caps")
    for lv, after, sound in ctl["caps"]["rows"]["lives"]:
        if after != grant_life(lv) or sound != 0xA9:
            errs.append("life cap row %02X" % lv)
    for ct, after, _lives in ctl["caps"]["rows"]["continues"]:
        if after != grant_continue(ct):
            errs.append("continue row %02X" % ct)
    if ctl["bonus_word"]["model_mismatches"]:
        errs.append("bonus word")
    for t, rows in ctl["bonus_word"]["words_by_time"].items():
        for n, w in enumerate(rows):
            if child_bonus(tt, int(t, 16), int_to_bcd(n))[0] != w:
                errs.append("bonus cell %s %d" % (t, n))
                break
    if ctl["chain"]["model_mismatches"]:
        errs.append("chain")
    if sha(json.dumps(ctl["chain"]["rows"]).encode()) != ctl["chain"]["rows_sha256"]:
        errs.append("chain hash")
    for r in ctl["chain"]["rows"]:
        zone, ptype, rings, t, lives, cont, rg, word = r
        d12f = (bcd_to_int(rings) + t) & 7
        m = award_sequence(tables, tt, zone, ptype, rings, t, BASE_LIVES, BASE_CONT, 0, d12f)
        if [m["lives"], m["continues"], m["rings"], m["bonus_word"]] != [lives, cont, rg, word]:
            errs.append("chain row %s" % r)
            break
    return errs


def validate_observed(ob, st):
    """Internal consistency of the committed observations against the model and the static art hashes."""
    errs = []
    tables = tables_of(st)
    tt = time_table_of(st)
    tick = {k: v["face_tile_bytes_sha256"][:16] for k, v in st["selectors"].items()}
    for mode, h in ob.get("retry_hold", {}).items():
        if not (h["sign_present"] and h["sign_state"] == 3 and h["plus35"] == 255 and h["plus34"] == 0 and h["timer_run_D2BE"] == 0 and h["act_flag_D293"] == "40"
                and not h["child_present"] and h["retry_face"] == ["20"] and h["rings"] == h["rings_in"] and h["lives"] == "03" and h["continues"] == "00"):
            errs.append("retry hold %s: %s" % (mode, h))
    for label, rec in ob["scenarios"].items():
        evs = rec["events"]
        names = [e[1] for e in evs]
        if "TIMEOUT" in names:
            errs.append(label + ": timeout")
            continue
        if "act_clear_flag" not in names:
            errs.append(label + ": no act-clear flag")
        zone, ptype = rec["zone"], rec["player_type"]
        rings_in = int(rec["rings_in"], 16)
        base = rec["base"]
        lives0, cont0 = int(base["lives"], 16), int(base["continues"], 16)
        lands = [e for e in evs if e[1] == "landing_call"]
        first = lands[0][2]
        rings_at = first["rings"]
        if rings_at != rings_in:
            errs.append(label + ": ring count changed before the landing")
        retry_expected = lookup_class(tables[zone_table(zone)], rings_in) == 0
        expect_landings = 2 if retry_expected else 1
        if len(lands) != expect_landings:
            errs.append("%s: %d landings, expected %d" % (label, len(lands), expect_landings))
        timer = int(base["timer_D2C0_D2BF"], 16)
        roll = rec["roll_D12F"]
        # model: the child reads time at update 147; the timer froze at the contact, so the base timer is not the contact timer when no preset was given
        bonus_evs = [e for e in evs if e[1] == "bonus_word_D2A6"]
        if not bonus_evs:
            errs.append(label + ": no D2A6 write")
        else:
            d = bonus_evs[-1][2]
            t_obs = int(d["time"], 16)
            r_obs = int(d["rings"], 16)
            word, equal = child_bonus(tt, t_obs, r_obs)
            if word != int(d["word"], 16):
                errs.append("%s: D2A6 %s != model %04X" % (label, d["word"], word))
            res = award_sequence(tables, tt, zone, ptype, rings_in, t_obs, lives0, cont0, 0, roll if roll is not None else 0)
            fin = rec["final"]
            if int(fin["lives"], 16) != res["lives"] or int(fin["continues"], 16) != res["continues"] or int(fin["rings"], 16) != res["rings"]:
                errs.append("%s: final counters %s vs model %s" % (label, fin, [hx(res["lives"]), hx(res["continues"]), hx(res["rings"])]))
            fc = rec["final_plus34"]
            if fc != res["final_class"]:
                errs.append("%s: final class %s vs model %s" % (label, fc, res["final_class"]))
            caps = rec["captures"]
            wants = {"default": ["12", "1C"], "final": ["%02X" % res["final_art"]]}
            if retry_expected:
                wants["retry"] = ["20"]
            for name, want in wants.items():
                cap = caps.get(name)
                if cap is None or "error" in cap:
                    errs.append("%s: no %s capture" % (label, name))
                    continue
                if not set(want) & set(cap["vram_face_equals_selector"]):
                    errs.append("%s: %s VRAM face equals %s, expected %s" % (label, name, cap["vram_face_equals_selector"], want))
                if not cap["sprite_palette_equals_rom_zone"]:
                    errs.append("%s: %s sprite palette differs from the ROM record" % (label, name))
                if cap["face_pixels_hidden_other"]:
                    errs.append("%s: %s face pixels hidden by something else" % (label, name))
        # selector writes
        writes = [e[2]["d3b3"] for e in evs if e[1] == "selector_write"]
        if writes[:1] != [SEL_DEFAULT]:
            errs.append(label + ": first selector write is not $12")
        # timing (adapter update_counts): frames are harness frames and agree exactly in every committed scenario
        uc = st["adapter"]["rom_native"]["update_counts"]
        t0 = [e[3] for e in evs if e[1] == "timer_run_flag"][0]
        if lands[0][3] - t0 != uc["contact_to_landing"]:
            errs.append("%s: contact to first landing %d updates" % (label, lands[0][3] - t0))
        last = lands[-1][3]
        spawn = [e[3] for e in evs if e[1] == "child_19_spawned"]
        if spawn != [last + 1]:
            errs.append("%s: child spawn %s vs final landing %d" % (label, spawn, last))
        if [e[3] - last for e in evs if e[1] == "bonus_word_D2A6"] != [uc["contact_to_bonus_word_and_equal_digit_life"] - uc["contact_to_landing"]]:
            errs.append(label + ": bonus word timing")
        if [e[3] - last for e in evs if e[1] == "player_state_20"] != [uc["contact_to_player_state_20"] - uc["contact_to_landing"]]:
            errs.append(label + ": player state 20 timing")
        if retry_expected:
            req6 = [e[3] for e in evs if e[1] == "sign_request" and e[2]["request"] == 6]
            if len(req6) != 1 or lands[-1][3] - req6[0] != uc["retouch_request_to_landing"]:
                errs.append(label + ": retouch request to landing")
        ups = [u for _f, u, _h in rec["face_uploads"]]
        for lu in (e[3] for e in lands):
            if [u for u in ups if lu <= u <= lu + 3] != [lu, lu + 1, lu + 2, lu + 3]:
                errs.append("%s: face upload updates around landing %d" % (label, lu))
    return errs


def check_all(rom, progress=print):
    problems = []
    st = build_static(rom)
    if dumps(st) != STATIC_JSON.read_text(encoding="utf-8"):
        problems.append("static census differs from the committed file")
    ctl = build_controlled(rom, st)
    if dumps(ctl) != CONTROLLED_JSON.read_text(encoding="utf-8"):
        problems.append("controlled results differ from the committed file")
    problems += validate_controlled(ctl, st)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        man = export_assets(rom, st, out=Path(td))
        if dumps(man) != MANIFEST_JSON.read_text(encoding="utf-8"):
            problems.append("export manifest differs from the committed file")
    ob = build_observed(rom, st, progress=progress)
    if dumps(ob) != OBS_JSON.read_text(encoding="utf-8"):
        problems.append("observations differ from the committed file")
    problems += validate_observed(ob, st)
    return problems


def write_all(rom, only=None, progress=print):
    DATA.mkdir(parents=True, exist_ok=True)
    st = build_static(rom)
    STATIC_JSON.write_text(dumps(st), encoding="utf-8", newline="\n")
    man = export_assets(rom, st)
    MANIFEST_JSON.write_text(dumps(man), encoding="utf-8", newline="\n")
    if only == "static":
        return
    ctl = build_controlled(rom, st)
    CONTROLLED_JSON.write_text(dumps(ctl), encoding="utf-8", newline="\n")
    if only == "controlled":
        return
    ob = build_observed(rom, st, progress=progress)
    OBS_JSON.write_text(dumps(ob), encoding="utf-8", newline="\n")


# ------------------------------------------------------------------------------------------------------------------------------------------
# Generated tables for the specification
_MARK = "<!-- %s u3:%s -->"


def _md(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |" for r in rows]
    return "\n".join(out)


def doc_tables(st, ctl, ob):
    t = {}
    t["routines"] = _md([("`%s`" % r["name"], ("%02X:" % r["bank"] if r["bank"] is not None else "res ") + "$%s-$%s" % (r["cpu_start"], r["cpu_end_exclusive"]), "0x%s" % r["file_start"],
                          r["length"], "`%s`" % r["sha256"][:12], r["role"]) for r in st["routines"]], ("routine", "CPU range (end exclusive)", "file", "bytes", "SHA-256", "role"))
    rows = []
    for k in ("12", "1B", "1C", "1D", "1E", "1F", "20"):
        v = st["selectors"][k]
        e = v["entries"]
        rows.append(("$" + k, "`$%s`" % v["list_cpu"], " + ".join("%02X:$%s x%d to tile $%02X" % (x["bank"], x["source_cpu"], x["tiles"], x["tile_base"]) for x in e),
                     "0x" + v["face_source_file"], "`%s`" % v["face_tile_bytes_sha256"][:12], "`%s`" % st["composed_frame1"][k]["face_index_sha256"][:12], st["selector_roles"][k]["face"]))
    t["selectors"] = _md(rows, ("selector", "list", "entries (bank:source, tiles)", "face block file", "tile-byte SHA-256", "32x32 index SHA-256", "face"))
    mp = []
    for f in st["sign_mapping"]["frames"]:
        mp.append((f["frame"], "`$%s`" % f["record_cpu"], len(f["pieces"]), " ".join("$%02X" % p["tile"] for p in f["pieces"]) or "-", "yes" if any(p["selector_dependent"] for p in f["pieces"]) else "no"))
    t["mapping"] = _md(mp, ("frame", "record", "pieces", "tile ids (8x16 each)", "selector-dependent"))
    pal = []
    for z in range(6):
        p = st["sprite_palettes"]["zones"][str(z)]
        pal.append((z, "$%02X" % p["sprite_index"], " ".join("%02X" % c for c in p["sprite_colours"])))
    t["palettes"] = _md(pal, ("zone", "sprite record", "16 SMS colours %00BBGGRR"))
    cls = []
    names = {3: "3 continue (D2C3 +1)", 2: "2 rings +10", 1: "1 life (D299 +1)", 0: "0 retry", 255: "$FF none"}
    for tab in (TABLE_ODD_ZONE_PARITY, TABLE_EVEN_ZONE_PARITY):
        for c in ("3", "2", "1", "0", "255"):
            counts = st["prize_tables"]["counts_by_class"][tab].get(c, [])
            cls.append(("$" + tab, names[int(c)], len(counts), " ".join(counts) if int(c) != 255 else "(all other counts)"))
    t["prize_classes"] = _md(cls, ("table", "class", "counts", "BCD ring counts"))
    rr = []
    for k in range(1, 9):
        e = st["reward_effects"]["retouch_roll"]["classes"][str(k)]
        rr.append(("%d" % (k - 1), k, e["effect"], "$%02X" % e["selector_sonic"], "$%02X" % e["selector_other"]))
    t["reroll"] = _md(rr, ("D12F & 7", "+$34", "effect", "selector Sonic", "selector Tails"))
    tb = []
    for e in st["bonus_word"]["time_table"]:
        tb.append((e["index"], "< %d:%s" % (int(e["limit_bcd_mmss"][:2]), e["limit_bcd_mmss"][2:]) if e["limit_bcd_mmss"] != "FFFF" else "any", "$" + e["h"]))
    t["time_table"] = _md(tb, ("index", "time (D2C0:D2BF)", "H"))
    if ob:
        obs = []
        for label, r in ob["scenarios"].items():
            f = r["final"]
            cap = r["captures"].get("final") or {}
            obs.append((label, "%d/%d" % (r["zone"], r["act"]), "Sonic" if r["player_type"] == 1 else "Tails", "$" + r["rings_in"], r["final_plus34"],
                        ",".join("$" + x for x in cap.get("vram_face_equals_selector", [])) or "-", "%s -> %s" % (r["base"]["lives"], f["lives"]), "%s -> %s" % (r["base"]["continues"], f["continues"]),
                        "$" + r["base"]["rings"] + " -> $" + f["rings"], "$" + f["D2A6"]))
        t["observed"] = _md(obs, ("scenario", "zone/act", "player", "rings in", "class", "face", "lives", "continues", "rings", "D2A6"))
    return t


def refresh_doc(path=DOC, st=None, ctl=None, ob=None):
    st = st or load_json(STATIC_JSON)
    ctl = ctl or load_json(CONTROLLED_JSON)
    ob = ob or load_json(OBS_JSON)
    text = Path(path).read_text(encoding="utf-8")
    for name, body in doc_tables(st, ctl, ob).items():
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
    ap.add_argument("--only", choices=["static", "controlled"])
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--doc", action="store_true", help="refresh the generated tables inside docs/u3-sign-prize-presentation.md from the committed JSON")
    a = ap.parse_args(argv)
    if a.doc:
        refresh_doc()
        return 0
    if a.validate:
        st = load_json(STATIC_JSON)
        errs = validate_static(st) + validate_controlled(load_json(CONTROLLED_JSON), st) + validate_observed(load_json(OBS_JSON), st)
        print("OK" if not errs else "\n".join(errs))
        return 1 if errs else 0
    rom = load_rom(a.rom or os.environ.get("SONIC_CHAOS_ROM") or ROOT.parent / "source" / "Sonic Chaos (Europe).sms")
    if a.check:
        problems = check_all(rom)
        print("U3 check: OK" if not problems else "\n".join(problems))
        return 1 if problems else 0
    write_all(rom, only=a.only)
    print("wrote", STATIC_JSON, MANIFEST_JSON, CONTROLLED_JSON if a.only != "static" else "", OBS_JSON if not a.only else "", "exports in", BUILD)
    return 0


if __name__ == "__main__":
    sys.exit(main())

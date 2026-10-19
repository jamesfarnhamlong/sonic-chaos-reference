#!/usr/bin/env python3
"""VISUAL-1 Part B: surface-$0D breakable terrain (blocks $9B/$9C -> $9D) and its four type-$07 shards.

Primary fixture: the THZ2 bottom-left corridor (six block $9C cells, layout (4..6,22) and (9..11,22)) that leads to the
type-$10 extra-life monitor at world (64,718).

Evidence classes
  DECODED DATA            tables read from the ROM (offset/speed tables, scripts, mapping frames, cull table, layouts)
  BYTE-VERIFIED ASSEMBLY  the routines are disassembled and compared with the exact expected instruction text
  EMULATED ORIGINAL FRAME the unmodified ROM runs in tools/sms_frame_harness.py (approximate VDP, Z80 core) and every
                          object update, name-table write, SAT entry and sound-mailbox write is recorded
  CLOSED-FORM MODEL       a Python re-implementation of the $9B11 / $9BB5 / $60FB arithmetic that must reproduce the
                          emulated per-update positions bit for bit
  POC SOURCE (READ-ONLY)  the accepted GameMaker project is only parsed, never executed or modified

The only deviation from a plain boot is a fixture: the THZ2 start record (four words at ROM $4F0E) is rewritten in a
private in-memory copy of the ROM so the act starts at the foot of the corridor shaft. Nothing is written to disk.

Usage:
    python tools/visual1_shards.py ROM [--output build/visual1] [--poc PATH] [--metadata JSON] [--check] [--static-only]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import level_package as LP  # noqa: E402
import player_scripts as P  # noqa: E402
import rom as R  # noqa: E402
import thz1_object_assets as A  # noqa: E402
import tile_decompress as TD  # noqa: E402
from z80dis import z80  # noqa: E402

# ----------------------------------------------------------------------------------------------------------------
# constants
# ----------------------------------------------------------------------------------------------------------------
BREAK = 0x7898
FLOOR_HANDLER = 0x6B2C
SIDE_RIGHT, SIDE_LEFT = 0x72B6, 0x72DD
CEILING_HANDLER = 0x7464
INIT_CB, MOVE_CB = 0x9B11, 0x9BB5
TABLE_GE0, TABLE_LT0 = 0x9B75, 0x9B95
SHARD_TYPE = 7
SOUND_SHARD = 0xA3
SHARD_FRAME = 15
OBJECT_BASE, OBJECT_STRIDE, SPAWN_SLOTS, LOOP_SLOTS = 0xD540, 0x40, 16, 19
START_TABLE = 0x4E98
CULL_TABLE_BANK1C_CPU = 0x8146          # 32 x 32 bytes, consumed by $61E1
THZ2 = (0, 1)
CORRIDOR_CELLS = ((4, 22), (5, 22), (6, 22), (9, 22), (10, 22), (11, 22))
MONITOR_WORLD = (64, 718)
SPIN_DASH_START = (404, 718)             # foot of the corridor shaft, cell 12 (floor block $01 at row 23)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hx(v: int, w: int = 2) -> str:
    return "0x%0*X" % (w, v)


def s16(v: int) -> int:
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def bank_file(bank: int, cpu: int) -> int:
    return bank * 0x4000 + cpu - 0x8000


def disasm(rom: bytes, start: int, end: int, bank: int = 0) -> list:
    out, a = [], start
    while a < end:
        off = a if bank == 0 else bank_file(bank, a)
        d = z80.decode(rom[off:off + 4], a)
        out.append("%04X %s | %s" % (a, rom[off:off + d.len].hex(" "), z80.disasm(d)))
        a += d.len
    return out


# ----------------------------------------------------------------------------------------------------------------
# static decode
# ----------------------------------------------------------------------------------------------------------------
EXPECT_ASM = OrderedDict([
    # (start, end, bank): key lines that must be present, in order (byte-verified assembly)
    ("break_7898", (0x7898, 0x78E1, 0, [
        "LD A,(0xd162)", "CALL 0x1c6f", "LD A,0x9d", "LD HL,(0xd354)", "LD (HL),A", "CALL 0x23f9",
        "LD HL,(0xd358)", "AND 0xe0", "LD (0xd35c),HL", "LD HL,(0xd35a)", "AND 0xe0", "LD (0xd35e),HL",
        "LD C,7", "LD H,0", "CALL 0x5e9c", "LD H,1", "CALL 0x5e9c", "LD H,2", "CALL 0x5e9c", "LD H,3", "JP 0x5e9c"])),
    ("floor_6b2c", (0x6B2C, 0x6B56, 0, [
        "LD A,(0xd501)", "CP 15", "CP 0x10", "CP 0x15", "CP 0x1a", "BIT 1,(IX+3)", "LD A,0x10", "LD (0xd3b2),A",
        "LD HL,0xfbc0", "LD (0xd518),HL", "RES 1,(IX+0x22)", "SET 0,(IX+3)", "JP 0x7898"])),
    ("side_right_72b6", (0x72B6, 0x72DD, 0, [
        "BIT 1,(IX+3)", "JP z,0x71b8", "LD A,(0xd517)", "BIT 7,A", "NEG", "CP 3", "JP c,0x71b8", "LD HL,(0xd516)",
        "CP 7", "LD BC,0x40", "ADD HL,BC", "LD (0xd516),HL", "JP 0x7898"])),
    ("side_left_72dd", (0x72DD, 0x7306, 0, [
        "BIT 1,(IX+3)", "JP z,0x725d", "LD A,(0xd517)", "BIT 7,A", "NEG", "CP 3", "JP c,0x725d", "LD HL,(0xd516)",
        "NEG", "CP 7", "LD BC,0xffc0", "ADD HL,BC", "LD (0xd516),HL", "JP 0x7898"])),
    ("ceiling_7464", (0x7464, 0x746E, 0, ["LD A,(0xd3c0)", "OR A", "JP z,0x7898", "JP 0x4984"])),
    ("spawn_5e9c", (0x5E9C, 0x5EB7, 0, [
        "LD IY,0xd540", "LD B,0x10", "LD DE,0x40", "LD A,(IY)", "OR A", "JR z,0x5eb0", "ADD IY,DE", "DJNZ 0x5ea5", "RET",
        "LD (IY),C", "LD (IY+0x3f),H", "RET"])),
    ("init_9b11", (0x9B11, 0x9B75, 12, [
        "LD L,(IX+0x3f)", "LD H,0", "ADD HL,HL", "ADD HL,HL", "ADD HL,HL", "LD DE,0x9b75", "LD A,(0xd517)", "AND A",
        "JP p,0x9b26", "LD DE,0x9b95", "ADD HL,DE", "LD BC,(0xd35c)", "LD (IX+0x11),L", "LD (IX+0x12),H",
        "LD BC,(0xd35e)", "LD (IX+0x14),L", "LD (IX+0x15),H", "LD (IX+0x16),A", "LD (IX+0x17),A", "LD (IX+0x18),A",
        "LD (IX+0x19),A", "LD (IX+2),1", "SET 0,(IX+4)", "LD A,(0xd297)", "CP 6", "RET nz", "LD A,(0xd298)", "CP 2",
        "RET nz", "LD (IX+8),0x9c", "RET"])),
    ("move_9bb5", (0x9BB5, 0x9BC8, 12, [
        "BIT 6,(IX+4)", "JP nz,0x0344", "LD BC,0x1000", "LD DE,0xc0", "CALL 0x0350", "JP 0x0338"])),
    ("gravity_5f84", (0x5F84, 0x5FA0, 0, [
        "LD L,(IX+0x18)", "LD H,(IX+0x19)", "ADD HL,DE", "LD E,L", "LD D,H", "BIT 7,H", "JR nz,0x5f99", "XOR A",
        "SBC HL,BC", "JR c,0x5f99", "RET", "LD E,C", "LD D,B", "LD (IX+0x18),E", "LD (IX+0x19),D", "RET"])),
    ("move_60fb", (0x60FB, 0x613C, 0, [
        "LD L,(IX+0x10)", "LD H,(IX+0x11)", "LD E,(IX+0x16)", "LD D,(IX+0x17)", "LD B,(IX+0x12)", "ADD HL,DE", "ADC A,B",
        "LD (IX+0x12),A", "LD (IX+0x10),L", "LD (IX+0x11),H", "LD L,(IX+0x13)", "LD H,(IX+0x14)", "LD E,(IX+0x18)",
        "LD D,(IX+0x19)", "LD B,(IX+0x15)", "ADD HL,DE", "ADC A,B", "LD (IX+0x15),A", "LD (IX+0x13),L",
        "LD (IX+0x14),H"])),
    ("cull_61e1", (0x61E1, 0x6250, 0, [
        "RES 6,(IX+4)", "LD L,(IX+0x11)", "LD H,(IX+0x12)", "LD BC,0x80", "ADD HL,BC", "LD BC,(0xd174)", "SBC HL,BC",
        "JP c,0x624c", "SRL H", "RR L", "OR A", "JP nz,0x624c", "LD L,(IX+0x14)", "LD H,(IX+0x15)", "LD BC,(0xd176)",
        "LD DE,0x8146", "LD A,0x1c", "LD A,(HL)", "CP 3", "JP z,0x624c", "AND 2", "RET z", "SET 6,(IX+4)", "RET"])),
    ("shard_art_loader_79f2", (0x79F2, 0x7A12, 0, [
        "DI", "LD A,14", "CALL 0x1c6f", "LD HL,0xcc0", "CALL 0x1d50", "LD A,(0xd297)", "ADD A,A", "LD DE,0xa3a0", "ADD HL,DE",
        "LD E,(HL)", "LD D,(HL)", "EX DE,HL", "XOR A", "CALL 0x24c2", "RET"])),
    ("level_loader_call_site_295b", (0x2951, 0x295E, 0, ["LD A,(0xd2c8)", "LD (0xd500),A", "DEC A", "CALL nz,0x79df", "CALL 0x79f2"])),
    ("sound_67d5", (0x67D5, 0x67EC, 0, [
        "LD L,(IX+14)", "LD H,(IX+15)", "LD A,(HL)", "INC HL", "LD (IX+14),L", "LD (IX+15),H", "LD (0xde04),A",
        "LD (0xde04),A", "JP 0x653d"])),
])


def verify_assembly(rom: bytes, table: dict | None = None) -> OrderedDict:
    out = OrderedDict()
    for name, (start, end, bank, expect) in (table or EXPECT_ASM).items():
        lines = disasm(rom, start, end, bank)
        texts = [ln.split(" | ", 1)[1] for ln in lines]
        pos, missing = 0, []
        for want in expect:
            try:
                pos = texts.index(want, pos) + 1
            except ValueError:
                missing.append(want)
        if missing:
            raise ValueError("%s: expected instruction(s) not found in order: %r" % (name, missing))
        out[name] = OrderedDict(start=hx(start, 4), end=hx(end, 4), bank=bank, instruction_count=len(lines),
                                bytes_sha256=sha(rom[start:end] if bank == 0 else rom[bank_file(bank, start):bank_file(bank, end)]),
                                verified_subsequence_length=len(expect))
    return out


def type7_scripts(rom: bytes) -> OrderedDict:
    commands = P.derive_commands(rom)
    table_ptr = R.u16(rom, 0x65BA + (SHARD_TYPE - 1) * 2)
    base = bank_file(12, table_ptr)
    starts = [R.u16(rom, base + 2 * i) for i in range(2)]
    out = OrderedDict(state_table_cpu=hx(table_ptr, 4), states=[])
    for st, start in enumerate(starts):
        notes = []
        steps, _ = P.parse_script(rom, start, commands, notes)
        ops = []
        for cpu in sorted(steps):
            kind, _, cmd = steps[cpu]
            off = bank_file(12, cpu)
            if kind == "record":
                ops.append(OrderedDict(at=hx(cpu, 4), op="record", duration=rom[off], frame=rom[off + 1],
                                       callback=hx(R.u16(rom, off + 2), 4)))
            else:
                n = {0: 0, 1: 2, 2: 4, 3: 1, 6: 1, 7: 2, 14: 1, 15: 2}.get(cmd, 0)
                ops.append(OrderedDict(at=hx(cpu, 4), op="FF %02X" % cmd, operands=rom[off + 2:off + 2 + n].hex(" ")))
        out["states"].append(OrderedDict(state=st, script_cpu=hx(start, 4), ops=ops, notes=notes))
    return out


def offset_tables(rom: bytes) -> OrderedDict:
    def table(cpu):
        rows = []
        for q in range(4):
            o = bank_file(12, cpu) + q * 8
            rows.append(OrderedDict(quadrant=q, x_offset=R.u16(rom, o), y_offset=R.u16(rom, o + 2),
                                    x_speed_8_8=s16(R.u16(rom, o + 4)), y_speed_8_8=s16(R.u16(rom, o + 6)),
                                    x_speed_px=s16(R.u16(rom, o + 4)) / 256, y_speed_px=s16(R.u16(rom, o + 6)) / 256))
        return rows
    return OrderedDict(
        selector="LD A,($D517) (player X speed high byte) at the first (init) callback; AND A; JP P -> table $9B75 else $9B95",
        player_x_speed_ge_0_table_9b75=table(TABLE_GE0), player_x_speed_lt_0_table_9b95=table(TABLE_LT0),
        record_bytes="8 bytes: x offset(w) y offset(w) x speed(w) y speed(w), 8.8 signed; entry index = parameter (+$3F)")


def mapping_info(rom: bytes) -> OrderedDict:
    m = A.object_mapping(rom, SHARD_TYPE)
    out = OrderedDict(mapping_table_cpu=hx(m["mapping_cpu"], 4), mapping_table_rom=hx(m["mapping_rom"], 5), frames=OrderedDict())
    for f in (0, SHARD_FRAME):
        cpu = R.u16(rom, A.cpu15_to_rom(m["mapping_cpu"]) + 2 * f)
        p = A.parse_frame_record(rom, cpu)
        out["frames"][str(f)] = OrderedDict(
            frame_cpu=hx(cpu, 4), frame_rom=hx(p["frame_rom"], 5), pieces=[
                OrderedDict(rel_x=q["relative_x"], rel_y=q["relative_y"], tile=hx(q["tile_offset"])) for q in p["pieces"]])
    return out


def cull_table(rom: bytes) -> OrderedDict:
    """The $61E1 visibility map: 32 columns x 32 rows of 16-pixel cells covering screen offset -128..383 on each axis."""
    base = bank_file(0x1C, CULL_TABLE_BANK1C_CPU)
    raw = rom[base:base + 1024]
    rows = ["".join(str(v) for v in raw[r * 32:(r + 1) * 32]) for r in range(32)]
    # value semantics (byte-verified at $623E..$6247): 3 -> removed; bit 1 set -> flagged off-screen; otherwise on-screen
    kept = [(r, c) for r in range(32) for c in range(32) if raw[r * 32 + c] & 2 == 0]
    cols = sorted({c for r, c in kept})
    rws = sorted({r for r, c in kept})
    return OrderedDict(
        table_cpu=hx(CULL_TABLE_BANK1C_CPU, 4), table_rom=hx(bank_file(0x1C, CULL_TABLE_BANK1C_CPU), 5), sha256=sha(raw),
        value_counts={str(v): raw.count(bytes([v])) for v in sorted(set(raw))},
        index="((objY + 128 - camY) / 2 & 0xF8) * 4 + ((objX + 128 - camX) / 2 >> 3 & 31)  (one byte per 16 x 16 screen cell, offset -128)",
        window_before_table="objX + 128 - camX and objY + 128 - camY must each lie in [0,512), i.e. screen offset -128..+383 (else flag + (type 0xFF if +4 bit1 clear))",
        on_screen_cell_columns=OrderedDict(first=cols[0], last=cols[-1], screen_x_from=cols[0] * 16 - 128, screen_x_to=cols[-1] * 16 - 128 + 15),
        on_screen_cell_rows=OrderedDict(first=rws[0], last=rws[-1], screen_y_from=rws[0] * 16 - 128, screen_y_to=rws[-1] * 16 - 128 + 15),
        on_screen_cells=len(kept), rows_text=rows)


SHARD_STREAM_TABLE_BANK0E_CPU = 0xA3A0
SHARD_STREAM_VRAM = 0x0CC0


def static_shard_art(rom: bytes, zone: int, act: int) -> OrderedDict:
    """Tiles $66/$67 exactly as the level loader $2934 -> $79F2 writes them (zone-indexed stream, decoder $24C2)."""
    ptr = R.u16(rom, bank_file(0x0E, SHARD_STREAM_TABLE_BANK0E_CPU) + 2 * zone)
    file = bank_file(0x0E, ptr)
    data = TD.decompress_tile_stream(rom, file)
    sel = LP.palette_selection(rom, zone, act)
    pal = A.palette_rgba(rom, sel["sprite_index"])
    pixels = A.decode_mode4_tile(data[:32]) + A.decode_mode4_tile(data[32:64])
    idx = bytes(v for r in pixels for v in r)
    rgba = bytearray()
    for v in idx:
        rgba += bytes(pal[v])
    top = sum(1 for r in pixels[:8] for v in r if v)
    bottom = sum(1 for r in pixels[8:] for v in r if v)
    return OrderedDict(
        zone=zone, act=act, table_entry_rom=hx(bank_file(0x0E, SHARD_STREAM_TABLE_BANK0E_CPU) + 2 * zone, 5), stream_cpu=hx(ptr, 4),
        stream_rom=hx(file, 5), decoded_tiles=len(data) // 32, vram_destination=hx(SHARD_STREAM_VRAM, 4), tile_pair=["0x66", "0x67"],
        tile_bytes_sha256=sha(data), top_tile_opaque_pixels=top, bottom_tile_opaque_pixels=bottom, visible_half="top" if top and not bottom else "bottom" if bottom and not top else "both" if top else "none",
        sprite_palette_index=sel["sprite_index"], sprite_palette_rom=hx(sel["sprite_rom"], 5), indexed_sha256=sha(idx), rgba_sha256=sha(bytes(rgba)),
        palette_indices_used=sorted({v for v in idx if v}), _rgba=bytes(rgba), _idx=idx, _data=data)


def shard_art_table(rom: bytes) -> OrderedDict:
    rows = OrderedDict()
    for z in range(13):
        rows[str(z)] = clean(static_shard_art(rom, z, 0))
    shared = {}
    for z, r in rows.items():
        shared.setdefault(r["stream_cpu"], []).append(int(z))
    return OrderedDict(
        loader="$2934 CALL $79F2 at $295B (after $4DAD camera/layout, $2A4F, $2A2E and the Tails-only $79DF)", routine="$79F2: bank $0E, VRAM $0CC0, stream pointer word at $A3A0 + 2*zone, decoder $24C2",
        note="the primary level stream also writes $66/$67 earlier (the 'common stream'); the $79F2 write is the last one and is what the shards display",
        zones=rows, streams_shared_by_zones={k: v for k, v in shared.items()})


def census_0d(rom: bytes) -> OrderedDict:
    surf = {b: R.header(rom, b)["flags"] & 31 for b in range(256)}
    out = OrderedDict()
    names = {0: "THZ", 1: "GPZ", 2: "SEZ", 3: "MGHZ", 4: "AQZ", 5: "EEZ", 6: "zone6", 7: "zone7", 8: "SS1", 9: "SS2", 10: "SS3",
             11: "SS4", 12: "SS5"}
    for z in range(13):
        for a in range(3):
            h = LP.act_header(rom, z, a)
            cells, _, _ = LP.decode_layout_stream(rom, h["layout_rom"], 4095)
            hits = [i for i, v in enumerate(cells) if surf[v] == 13]
            if not hits:
                continue
            out["%d/%d" % (z, a)] = OrderedDict(
                zone=names[z], act=a, width=h["width_cells"], cells=len(hits),
                by_block={hx(b): sum(1 for i in hits if cells[i] == b) for b in sorted({cells[i] for i in hits})},
                cell_list=[[i % h["width_cells"], i // h["width_cells"]] for i in hits])
    blocks = OrderedDict()
    for b in (0x9B, 0x9C, 0x9D):
        hd = R.header(rom, b)
        blocks[hx(b)] = OrderedDict(flags=hx(hd["flags"]), surface=hd["flags"] & 31, modifier=hx(hd["modifier"]),
                                    vertical_profile_sha=sha(bytes(hd["vertical"])), horizontal_profile_sha=sha(bytes(hd["horizontal"])))
    return OrderedDict(surface_type=13, blocks=blocks, acts=out,
                       note="zone 6 acts 1-2 carry the same $0D counts as THZ2/THZ3; the init callback sets +$08 := $9C only for zone 6 act 2 (byte-verified at $9B64..$9B70)")


# ----------------------------------------------------------------------------------------------------------------
# closed-form model of the ROM arithmetic
# ----------------------------------------------------------------------------------------------------------------
def model_shard(table_rows, quadrant, cell_x, cell_y, updates, gravity=0xC0):
    """Return the object position/velocity after the init callback and after every later callback.
    Terminal fall speed is $0FC0 (15.75 px/update): the first sum >= $1000 is discarded by $5F84, so the speed stays $0FC0.

    update 0 = the init callback (runs in the break update itself), update k >= 1 = k-th $9BB5 callback.
    Position is 16.8 fixed point per axis; $60FB adds the sign-extended 8.8 velocity to the 24-bit position.
    """
    r = table_rows[quadrant]
    x = ((cell_x + r["x_offset"]) << 8)
    y = ((cell_y + r["y_offset"]) << 8)
    vx, vy = r["x_speed_8_8"], r["y_speed_8_8"]
    out = [OrderedDict(k=0, x=x / 256, y=y / 256, x_int=x >> 8, y_int=y >> 8, vx=vx, vy=vy)]
    for k in range(1, updates + 1):
        nvy = (vy + gravity) & 0xFFFF   # $5F84 with BC = $1000: negative -> stored; 0..$0FFF -> stored; >= $1000 -> NOT stored (speed holds)
        if nvy & 0x8000 or nvy < 0x1000:
            vy = s16(nvy)
        x += vx
        y += vy
        out.append(OrderedDict(k=k, x=x / 256, y=y / 256, x_int=x >> 8, y_int=y >> 8, vx=vx, vy=vy))
    return out


# ----------------------------------------------------------------------------------------------------------------
# emulation
# ----------------------------------------------------------------------------------------------------------------
def patched_rom(rom: bytes, zone: int, act: int, cam, anchor) -> bytes:
    zp = R.u16(rom, START_TABLE + zone * 2)
    rec = R.u16(rom, zp + act * 2)
    b = bytearray(rom)
    b[rec:rec + 8] = struct.pack("<4H", cam[0], cam[1], anchor[0], anchor[1])
    return bytes(b)


class Tracer:
    """Attaches pc hooks.

    ``iteration`` counts entries to the gameplay update $16B8 (one per main-loop pass $1333).  When $D15E bit 6 is set the
    iteration returns early without running the player ($361D) or the object pass ($5DD1); those iterations are not game
    ticks.  ``update`` (= tick) counts player updates $361D, each followed by one object pass in the same iteration.
    """

    def __init__(self, s):
        self.s = s
        self.m = s.mem
        self.update = 0
        self.iteration = 0
        self.iterations = []            # (iteration, video frame, scanline, skipped, d15e)
        self.start = {}                 # update -> (video frame, scanline) when $16B8 was entered
        self.events = []
        self.objects = {}               # update -> list of type-7 snapshots (after the whole update)
        self.pre = {}                   # (update, slot) -> pre-callback snapshot
        self.occupancy = {}
        s.add_pc_hook(0x16B8, self._iteration)
        s.add_pc_hook(0x361D, self._update)
        s.add_pc_hook(0x7AC2, self._end_update)
        s.add_pc_hook(BREAK, self._break)
        s.add_pc_hook(0x5E9C, self._spawn)
        s.add_pc_hook(0x5E91, self._callback)
        s.add_pc_hook(0x67E3, self._sound)
        s.add_pc_hook(0x5EF8, self._delete)
        s.add_pc_hook(INIT_CB, self._init)
        for pc, name in ((FLOOR_HANDLER, "floor_6b2c"), (SIDE_RIGHT, "side_right_72b6"), (SIDE_LEFT, "side_left_72dd"),
                         (CEILING_HANDLER, "ceiling_7464")):
            s.add_pc_hook(pc, self._handler(name))

    def _handler(self, name):
        def hook(mm):
            m = self.m
            self.events.append(OrderedDict(kind="handler_entry", handler=name, update=self.update, video_frame=mm.frame,
                                           player_state=m[0xD501], player_flags03=m[0xD503], player_vx_hi=m[0xD517], player_vx=s16(mm.u16(0xD516)),
                                           player_vy=s16(mm.u16(0xD518)), support_owner_d3c0=m[0xD3C0]))
        return hook

    def obj(self, ix):
        m, s = self.m, self.s
        return OrderedDict(slot=(ix - OBJECT_BASE) // OBJECT_STRIDE, type=m[ix], state=m[ix + 1], req=m[ix + 2], flags04=m[ix + 4],
                           frame=m[ix + 6], timer=m[ix + 7], x=s.u16(ix + 0x11), x_sub=m[ix + 0x10], y=s.u16(ix + 0x14), y_sub=m[ix + 0x13],
                           vx=s16(s.u16(ix + 0x16)), vy=s16(s.u16(ix + 0x18)), param=m[ix + 0x3F], tile_add=m[ix + 8])

    def _iteration(self, mm):
        self.iteration += 1
        d15e = self.m[0xD15E]
        self.iterations.append((self.iteration, mm.frame, mm.line, int(bool(d15e & 0x40)), d15e))

    def _update(self, mm):
        self.update += 1
        self.start[self.update] = (mm.frame, mm.line)

    def _end_update(self, mm):
        snaps = []
        for i in range(LOOP_SLOTS):
            ix = OBJECT_BASE + i * OBJECT_STRIDE
            if self.m[ix] == SHARD_TYPE:
                snaps.append(self.obj(ix))
        self.objects[self.update] = snaps
        self.occupancy[self.update] = [self.m[OBJECT_BASE + i * OBJECT_STRIDE] for i in range(LOOP_SLOTS)]

    def _break(self, mm):
        m = self.m
        self.events.append(OrderedDict(
            kind="break", update=self.update, video_frame=mm.frame, scanline=mm.line, cell_pointer=hx(mm.u16(0xD354), 4),
            cell_index=mm.u16(0xD354) - 0xC001, sample_x=mm.u16(0xD358), sample_y=mm.u16(0xD35A), d162=m[0xD162], d3b2=m[0xD3B2],
            player_state=m[0xD501], player_flags03=m[0xD503], player_x=mm.u16(0xD511), player_y=mm.u16(0xD514),
            player_vx=s16(mm.u16(0xD516)), player_vy=s16(mm.u16(0xD518)), camera=[mm.u16(0xD174), mm.u16(0xD176)],
            caller_return=hx(mm.u16(mm.cpu.sp), 4),
            free_slots_before=sum(1 for i in range(SPAWN_SLOTS) if m[OBJECT_BASE + i * OBJECT_STRIDE] == 0)))

    def _spawn(self, mm):
        self.events.append(OrderedDict(kind="spawn_call", update=self.update, video_frame=mm.frame, type=mm.cpu.c, param=mm.cpu.h))

    def _init(self, mm):
        ix = mm.cpu.ix
        self.events.append(OrderedDict(kind="init_callback", update=self.update, slot=(ix - OBJECT_BASE) // OBJECT_STRIDE,
                                       param=self.m[ix + 0x3F], player_vx_hi=self.m[0xD517], anchor=[mm.u16(0xD35C), mm.u16(0xD35E)],
                                       zone=self.m[0xD297], act=self.m[0xD298]))

    def _callback(self, mm):
        ix = mm.cpu.ix
        if self.m[ix] == SHARD_TYPE:
            self.pre[(self.update, (ix - OBJECT_BASE) // OBJECT_STRIDE)] = self.obj(ix)

    def _sound(self, mm):
        ix = mm.cpu.ix
        self.events.append(OrderedDict(kind="sound_write", update=self.update, video_frame=mm.frame, scanline=mm.line, value=hx(mm.cpu.a),
                                       object_type=self.m[ix], slot=(ix - OBJECT_BASE) // OBJECT_STRIDE,
                                       mailbox_before=hx(self.m[0xDE04]), priority_d0f=hx(self.m[0xDE0F])))

    def _delete(self, mm):
        ix = mm.cpu.ix
        self.events.append(OrderedDict(kind="delete", update=self.update, video_frame=mm.frame, type=self.m[ix],
                                       slot=(ix - OBJECT_BASE) // OBJECT_STRIDE, flags04=self.m[ix + 4], x=mm.u16(ix + 0x11), y=mm.u16(ix + 0x14),
                                       camera=[mm.u16(0xD174), mm.u16(0xD176)]))


# ----------------------------------------------------------------------------------------------------------------
# emulation helpers
# ----------------------------------------------------------------------------------------------------------------
def block_words(rom: bytes, block: int) -> list:
    cpu = R.u16(rom, 0x44000 + block * 2)
    base = 0x44000 + cpu - 0x8000
    return [R.u16(rom, base + 2 * i) for i in range(16)]


def nametable_block(s, world_x: int, world_y: int) -> list:
    """The 4x4 name-table words that display the 32 x 32 world cell at (world_x, world_y) (torus 32 x 28 tiles)."""
    base = (s.reg[2] & 0x0E) << 10
    col0, row0 = (world_x // 8) % 32, (world_y // 8) % 28
    out = []
    for j in range(4):
        for i in range(4):
            idx = ((row0 + j) % 28) * 32 + (col0 + i) % 32
            out.append(s.vram[base + 2 * idx] | (s.vram[base + 2 * idx + 1] << 8))
    return out


def boot_zone(rom: bytes, zone: int, act: int, limit: int = 5000):
    from sms_frame_harness import SMS, BTN_1, BTN_2
    s = SMS(rom)
    st = {"done": False}
    s.add_pc_hook(0x07D5, lambda m: (m._write(0xD297, zone), m._write(0xD298, act)))

    def start(m):
        if m.frame > 300:
            st["done"] = True
    s.add_pc_hook(0x4E97, start)
    for f in range(limit):
        s.pad = 0 if f < 250 else (BTN_1 if f < 700 and f % 40 < 3 else ((BTN_1 | BTN_2) if not st["done"] and f % 60 < 10 else 0))
        s.run_frame()
        if st["done"] and s.mem[0xD500] == 1:
            return s
    raise RuntimeError("did not reach gameplay")


def sprite_palette(s):
    return [A.sms_color(s.cram[16 + i], transparent=(i == 0)) for i in range(16)]


def shard_art(s, sat_tile: int) -> OrderedDict:
    pal = sprite_palette(s)
    vram = bytes(s.vram)
    top = A.tile_pixels(vram, sat_tile)
    bottom = A.tile_pixels(vram, sat_tile + 1)
    rows = top + bottom
    idx = bytes(v for r in rows for v in r)
    rgba = bytearray()
    for v in idx:
        rgba += bytes(pal[v])
    opaque = [[x, y] for y, r in enumerate(rows) for x, v in enumerate(r) if v]
    bb = (min(p[0] for p in opaque), min(p[1] for p in opaque), max(p[0] for p in opaque), max(p[1] for p in opaque)) if opaque else None
    return OrderedDict(
        sat_tile=hx(sat_tile), tile_pair=[hx(sat_tile), hx(sat_tile + 1)], vram_sha256=sha(vram[sat_tile * 32:sat_tile * 32 + 64]),
        top_tile_opaque_pixels=sum(1 for v in sum(top, []) if v), bottom_tile_opaque_pixels=sum(1 for v in sum(bottom, []) if v),
        opaque_pixels=len(opaque), opaque_bbox_in_8x16=list(bb) if bb else None, indexed_sha256=sha(idx), rgba_sha256=sha(bytes(rgba)),
        palette_indices_used=sorted({v for v in idx if v}), sprite_palette_cram=bytes(s.cram[16:32]).hex(), _rgba=bytes(rgba), _idx=idx)


def run_scenario(rom: bytes, zone: int, act: int, anchor, frames: int, pad=None, inject=None, stop_after_break: int | None = None,
                 cam=None, shots=None, watch=(), inject_frame: int = 0):
    """Boot ``zone``/``act`` with the start record rewritten to ``anchor`` (in-memory ROM copy), run, trace."""
    cam = cam or (max(anchor[0] - 104, 0), max(anchor[1] - 112, 0))
    s = boot_zone(patched_rom(rom, zone, act, cam, anchor), zone, act)
    tr = Tracer(s)
    m = s.mem
    if inject and inject_frame == 0:
        inject(s)
    per_frame, images = [], {}
    first_break_frame = None
    nt_watch = {}
    width0 = LP.act_header(rom, zone, act)["width_cells"]
    w9c, w9d = block_words(rom, 0x9C), block_words(rom, 0x9D)
    for (wcx, wcy) in watch:
        nt_watch[wcy * width0 + wcx] = OrderedDict(world=[wcx * 32, wcy * 32], frames=[])
    for f in range(frames):
        if inject and inject_frame and f == inject_frame:
            inject(s)
        s.pad = pad(f) if pad else 0
        before_breaks = sum(1 for e in tr.events if e["kind"] == "break")
        s.run_frame()
        cx, cy = s.u16(0xD174), s.u16(0xD176)
        sat = [OrderedDict(entry=i, tile=hx(n), screen_x=x, screen_y_top=y + 1, world_x=x + cx, world_y_top=y + 1 + cy)
               for i, y, x, n in s.sat() if n == 0x66 or (n & 0xFE) == 0x66]
        breaks = [e for e in tr.events if e["kind"] == "break"]
        for key, wch in nt_watch.items():
            wx, wy = wch["world"]
            words = nametable_block(s, wx, wy)
            wch["frames"].append((s.frame - 1, "C" if words == w9c else "D" if words == w9d else "."))
        per_frame.append(OrderedDict(video_frame=s.frame - 1, update=tr.update, camera=[cx, cy], mailbox=[m[0xDE04], m[0xDE05], m[0xDE06]],
                                     priority_d0f=m[0xDE0F], shard_sat=sat, player=[s.u16(0xD511), s.u16(0xD514), m[0xD501], s16(s.u16(0xD516))]))
        if shots and s.frame in shots:
            images[s.frame] = s.render()[0]
        if stop_after_break and breaks:
            if first_break_frame is None:
                first_break_frame = s.frame
            if s.frame - first_break_frame >= stop_after_break:
                break
    return OrderedDict(tracer=tr, per_frame=per_frame, machine=s, nametable=nt_watch, images=images, rom_width=LP.act_header(rom, zone, act)["width_cells"])


def corridor_pad(f: int, taps: int = 4):
    from sms_frame_harness import BTN_LEFT, BTN_DOWN, BTN_1
    if f < 6:
        return BTN_LEFT
    if f < 12:
        return 0
    if f < 16:
        return BTN_DOWN
    if f < 16 + 3 * taps + 1:
        return BTN_DOWN | (BTN_1 if (f - 16) % 4 == 0 else 0)
    return BTN_LEFT


# ----------------------------------------------------------------------------------------------------------------
# trace -> shard records
# ----------------------------------------------------------------------------------------------------------------
def build_shards(rom: bytes, run: dict, tables: dict) -> OrderedDict:
    tr = run["tracer"]
    breaks = [e for e in tr.events if e["kind"] == "break"]
    inits = [e for e in tr.events if e["kind"] == "init_callback"]
    deletes = [e for e in tr.events if e["kind"] == "delete" and e["type"] == SHARD_TYPE]
    sat_pos = set()
    for pf in run["per_frame"]:
        for e in pf["shard_sat"]:
            sat_pos.add((pf["video_frame"], e["world_x"] + 4, e["world_y_top"] + 16))
    sat_xy = {(x, y) for _, x, y in sat_pos}
    out = OrderedDict(breaks=[], shards=[], model_check=OrderedDict(), sat_check=OrderedDict())
    mismatches, compared, sat_seen, sat_matched = 0, 0, 0, 0
    all_pos = set()
    for bi, b in enumerate(breaks):
        B = b["update"]
        mine = [i for i in inits if i["update"] == B]
        spawn_calls = [e for e in tr.events if e["kind"] == "spawn_call" and e["update"] == B]
        sounds = [e for e in tr.events if e["kind"] == "sound_write" and e["update"] == B]
        width = run["rom_width"]
        cx, cy = (b["cell_index"] % width), b["cell_index"] // width
        rec = OrderedDict(index=bi, update=B, cell=[cx, cy], cell_world=[cx * 32, cy * 32], cell_pointer=b["cell_pointer"],
                          sample=[b["sample_x"], b["sample_y"]], player=OrderedDict(state=b["player_state"], flags03=b["player_flags03"],
                                                                                      x=b["player_x"], y=b["player_y"], vx=b["player_vx"], vy=b["player_vy"]),
                          camera=b["camera"], free_spawn_slots_before=b["free_slots_before"], spawn_calls=len(spawn_calls),
                          slot_types_before=tr.occupancy.get(B - 1, [None] * LOOP_SLOTS)[:SPAWN_SLOTS],
                          shards_created=len(mine), shards_dropped=len(spawn_calls) - len(mine),
                          parameters_created=[i["param"] for i in mine], slots=[i["slot"] for i in mine],
                          video_frame=b["video_frame"], scanline=b["scanline"], d3b2_at_break=b["d3b2"],
                          sound_writes=[OrderedDict(value=s_["value"], slot=s_["slot"], video_frame=s_["video_frame"], scanline=s_["scanline"],
                                                    mailbox_before=s_["mailbox_before"], priority_d0f=s_["priority_d0f"]) for s_ in sounds])
        out["breaks"].append(rec)
        for i in mine:
            slot, q = i["slot"], i["param"]
            dels = [d for d in deletes if d["slot"] == slot and d["update"] > B]
            D = dels[0]["update"] if dels else None
            tab = tables["player_x_speed_lt_0_table_9b95"] if i["player_vx_hi"] & 0x80 else tables["player_x_speed_ge_0_table_9b75"]
            last = (D - 1) if D else max(tr.objects)
            line, tl = [], []
            for u in range(B, last + 1):
                snap = [o for o in tr.objects.get(u, []) if o["slot"] == slot]
                if not snap:
                    break
                o = snap[0]
                tl.append((u - B, o["x"], o["x_sub"], o["y"], o["y_sub"], o["vx"], o["vy"], o["frame"], o["timer"], o["flags04"]))
            model = model_shard(tab, q, i["anchor"][0], i["anchor"][1], len(tl) - 1)
            ok = True
            for (k, x, xs, y, ys, vx, vy, fr, tm, fl), md in zip(tl, model):
                compared += 1
                x24, y24 = (x << 8) | xs, (y << 8) | ys
                if (x24 != int(round(md["x"] * 256)) & 0xFFFFFF or y24 != int(round(md["y"] * 256)) & 0xFFFFFF or vx != md["vx"] or vy != md["vy"]):
                    ok = False
                    mismatches += 1
                all_pos.add((x, y))
            shard = OrderedDict(
                break_index=bi, quadrant=q, slot=slot, spawn_update=B, delete_update=D,
                ticks_alive=(D - B) if D else None, move_callbacks=(D - 1 - B) if D else None, first_sprite_update=B + 1,
                last_sprite_update=(D - 1) if D else None,
                init=OrderedDict(x=tl[0][1], y=tl[0][3], vx_8_8=tl[0][5], vy_8_8=tl[0][6], table=("9B95" if i["player_vx_hi"] & 0x80 else "9B75"),
                                 player_vx_hi=i["player_vx_hi"]),
                delete=OrderedDict(x=dels[0]["x"], y=dels[0]["y"], camera=dels[0]["camera"], flags04=dels[0]["flags04"],
                                   screen=[dels[0]["x"] - dels[0]["camera"][0], dels[0]["y"] - dels[0]["camera"][1]]) if dels else None,
                model_matches_trace=ok, trace=[list(r) for r in tl])
            out["shards"].append(shard)
    for _, x, y in sat_pos:
        sat_seen += 1
        if (x, y) in all_pos:
            sat_matched += 1
    out["model_check"] = OrderedDict(compared_updates=compared, mismatches=mismatches,
                                     rule="x24 = x24 + vx; vy = vy + $00C0 first; y24 = y24 + vy  (callback $9BB5: $0350 gravity then $0338 move)")
    out["sat_check"] = OrderedDict(sat_entries_seen=sat_seen, matching_object_position_with_offset_minus4_minus16=sat_matched)
    return out


def sound_analysis(rom: bytes, run: dict, shards: dict) -> OrderedDict:
    prio = rom[0x0906F + (SOUND_SHARD & 0x7F) - 1]
    out = OrderedDict(request=hx(SOUND_SHARD), script_command="FF 06 A3 at the head of type-$07 state 0 ($9B02), executed in the same update as the break",
                      mailbox_writes_per_break=[len(b["sound_writes"]) for b in shards["breaks"]],
                      priority_byte_rom_0906F_plus_id_minus_1=OrderedDict(rom=hx(0x0906F + (SOUND_SHARD & 0x7F) - 1, 5), value=hx(prio)),
                      arbitration="driver drops a request whose priority byte is below the current $DE0F (audio-request-audit.md); equal is accepted")
    frames = {pf["video_frame"]: pf for pf in run["per_frame"]}
    seq = []
    for b in shards["breaks"]:
        vf = b["video_frame"]
        row = OrderedDict(break_index=b["index"], break_video_frame=vf, mailbox_after_frames=[], priority_after_frames=[])
        for d in range(0, 4):
            pf = frames.get(vf + d)
            if pf:
                row["mailbox_after_frames"].append(pf["mailbox"][0])
                row["priority_after_frames"].append(pf["priority_d0f"])
        intervals = sorted({w["video_frame"] * 2 + (1 if w["scanline"] >= 193 else 0) for w in b["sound_writes"]})
        row["driver_visible_requests"] = len(intervals)              # writes inside one vblank-to-vblank interval collapse into one mailbox byte
        row["priority_before"] = b["sound_writes"][0]["priority_d0f"] if b["sound_writes"] else None
        row["accept_by_rule"] = (int(row["priority_before"], 16) <= prio) if row["priority_before"] else None
        seq.append(row)
    out["per_break"] = seq
    return out


# ----------------------------------------------------------------------------------------------------------------
# scenarios
# ----------------------------------------------------------------------------------------------------------------
def first_sat_tile(run) -> int | None:
    for pf in run["per_frame"]:
        for e in pf["shard_sat"]:
            return int(e["tile"], 16)
    return None


def video_timeline(run, shards) -> OrderedDict:
    """Relation between game ticks and video frames around each break (harness-approximate)."""
    tr = run["tracer"]
    skipped = sum(1 for it in tr.iterations if it[3])
    out = OrderedDict(iterations=len(tr.iterations), skipped_iterations_d15e_bit6=skipped, player_updates=tr.update,
                      note="an iteration of $16B8 with $D15E bit 6 set runs neither the player nor the object pass (no game tick)")
    rows = []
    frames = {pf["video_frame"]: pf for pf in run["per_frame"]}
    nt = run["nametable"]
    for b in shards["breaks"]:
        key = b["cell"][1] * run["rom_width"] + b["cell"][0]
        watch = nt.get(key)
        first_hole = None
        if watch:
            for vf, cls in watch["frames"]:
                if vf >= b["video_frame"] and cls == "D":
                    first_hole = vf
                    break
        first_shard_frame = None
        if b["index"] == 0:
            for pf in run["per_frame"]:
                if pf["video_frame"] >= b["video_frame"] and pf["shard_sat"]:
                    first_shard_frame = pf["video_frame"]
                    break
        t0 = tr.start.get(b["update"])
        t1 = tr.start.get(b["update"] + 1)
        rows.append(OrderedDict(break_index=b["index"], break_update=b["update"], break_video_frame=b["video_frame"],
                                next_update_video_frame=t1[0] if t1 else None,
                                first_video_frame_with_new_nametable=first_hole,
                                first_video_frame_with_shard_sprite_first_break_only=first_shard_frame))
    out["per_break"] = rows
    return out


def nametable_check(rom: bytes, run, shards) -> OrderedDict:
    w9c, w9d = block_words(rom, 0x9C), block_words(rom, 0x9D)
    rows = []
    for key, watch in sorted(run["nametable"].items()):
        cls = "".join(c for _, c in watch["frames"])
        bk = [b for b in shards["breaks"] if b["cell"][1] * run["rom_width"] + b["cell"][0] == key]
        bf = bk[0]["video_frame"] if bk else None
        before = [c for vf, c in watch["frames"] if bf is not None and vf < bf]
        after = [c for vf, c in watch["frames"] if bf is not None and vf >= bf]
        rows.append(OrderedDict(cell_index=key, world=watch["world"], break_video_frame=bf, frames_before_break=len(before),
                                frames_as_block_9c_before=before.count("C"), frames_as_block_9d_before=before.count("D"),
                                frames_as_block_9c_after=after.count("C"), frames_after_break=len(after),
                                all_frames_after_are_block_9d=bool(after) and all(c == "D" for c in after)))
    return OrderedDict(block_9c_words=[hx(w, 4) for w in w9c], block_9d_words=[hx(w, 4) for w in w9d], cells=rows,
                       rule="the struck cell's 4 x 4 name-table words equal block $9C's mapping before the break and block $9D's from the break's own update on")


def write_art_png(path: Path, art: dict, scale: int = 8) -> None:
    rgba = art["_rgba"]
    w, h = 8, 16
    buf = bytearray()
    for y in range(h):
        for sy in range(scale):
            for x in range(w):
                buf += rgba[(y * w + x) * 4:(y * w + x) * 4 + 4] * scale
    A.write_rgba_png(path, w * scale, h * scale, bytes(buf))


def clean(o):
    if isinstance(o, dict):
        return OrderedDict((k, clean(v)) for k, v in o.items() if not k.startswith("_"))
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    return o


def corridor_report(rom: bytes, output: Path | None, tables: dict, taps: int = 4, label: str = "primary") -> tuple:
    render = output is not None and label == "primary"
    run = run_scenario(rom, THZ2[0], THZ2[1], SPIN_DASH_START, 190, pad=lambda f: corridor_pad(f, taps), watch=CORRIDOR_CELLS)
    s = run["machine"]
    sh = build_shards(rom, run, tables)
    tile = first_sat_tile(run)
    art = shard_art(s, tile) if tile is not None else None
    vram_start_sha = None
    rep = OrderedDict(
        label=label, spin_dash_taps=taps, start_anchor=list(SPIN_DASH_START), zone_act=list(THZ2),
        breaks=sh["breaks"], shards=sh["shards"], model_check=sh["model_check"], sat_check=sh["sat_check"],
        sound=sound_analysis(rom, run, sh), timeline=video_timeline(run, sh), nametable=nametable_check(rom, run, sh),
        art=clean(art) if art else None, lives=OrderedDict(
            before=3, after=s.mem[0xD299], monitor_world=list(MONITOR_WORLD), final_player=[s.u16(0xD511), s.u16(0xD514)]),
        summary=summarise_run(sh))
    return rep, run, art


def summarise_run(sh) -> OrderedDict:
    br = sh["breaks"]
    live = [x["ticks_alive"] for x in sh["shards"] if x["ticks_alive"]]
    return OrderedDict(
        breaks=len(br), shards_created=sum(b["shards_created"] for b in br), shards_dropped=sum(b["shards_dropped"] for b in br),
        dropped_by_break=[b["shards_dropped"] for b in br], min_ticks_alive=min(live) if live else None, max_ticks_alive=max(live) if live else None,
        deleted_right_of_view=sum(1 for x in sh["shards"] if x["delete"] and x["delete"]["screen"][0] >= 288),
        deleted_below_view=sum(1 for x in sh["shards"] if x["delete"] and x["delete"]["screen"][1] >= 288),
        deleted_left_of_view=sum(1 for x in sh["shards"] if x["delete"] and x["delete"]["screen"][0] < -32),
        all_model_matches=all(x["model_matches_trace"] for x in sh["shards"]))


def controls(rom: bytes, tables: dict) -> OrderedDict:
    from sms_frame_harness import BTN_LEFT, BTN_RIGHT
    out = OrderedDict()
    # C1: walking (no roll) into the first $9C cell
    run = run_scenario(rom, 0, 1, SPIN_DASH_START, 90, pad=lambda f: BTN_LEFT)
    out["walk_left_no_roll"] = OrderedDict(breaks=sum(1 for e in run["tracer"].events if e["kind"] == "break"),
                                           player_x=run["machine"].u16(0xD511), expected="no break: handler needs +$03 bit 1 (rolling) and |X speed hi| >= 3")

    def roll(vx, state=9):
        def inj(s):
            m = s.mem
            m[0xD501] = m[0xD502] = state
            m[0xD503] |= 2
            s.w16(0xD516, vx & 0xFFFF)
        return inj
    for name, vx, anchor, right in (("roll_left_hi4", -0x400, SPIN_DASH_START, False), ("roll_left_hi3", -0x2C0, SPIN_DASH_START, False),
                                    ("roll_left_hi2", -0x200, SPIN_DASH_START, False), ("roll_right_hi4_from_monitor_room", 0x400, (110, 718), True)):
        run = run_scenario(rom, 0, 1, anchor, 110, inject=roll(vx), inject_frame=40)
        ev = run["tracer"].events
        hs = [e for e in ev if e["kind"] == "handler_entry"]
        brks = [e for e in ev if e["kind"] == "break"]
        inits = [e for e in ev if e["kind"] == "init_callback"]
        out[name] = OrderedDict(
            injected_vx=vx, handler_entries=[(e["handler"], e["player_vx_hi"], e["player_vx"]) for e in hs][:3], breaks=len(brks),
            first_break_cell=[brks[0]["cell_index"] % 128, brks[0]["cell_index"] // 128] if brks else None,
            player_vx_after_break=[b["player_vx"] for b in brks][:1], table_used=[("9B95" if i["player_vx_hi"] & 0x80 else "9B75") for i in inits][:1],
            player_x_end=run["machine"].u16(0xD511))
    return out


def eligible_floor_cell(cells, width, cx, cy):
    surf = {}
    return True


def floor_fixtures(rom: bytes, tables: dict, output: Path | None) -> OrderedDict:
    """Controlled floor-path ($6B2C) breaks: Sonic dropped in the jump posture (+$03 bit 1) onto a $0D cell whose cell above is empty air.

    Not a natural route: the start record is rewritten in memory.  It exposes the same $7898 shards in every zone that has $0D cells,
    with that zone's live VRAM / palette."""
    surf = {b: R.header(rom, b)["flags"] & 31 for b in range(256)}
    out = OrderedDict()

    def inj(s):
        m = s.mem
        m[0xD501] = m[0xD502] = 0x0A
        m[0xD503] |= 3
        s.w16(0xD516, 0)
        s.w16(0xD518, 0x0100)
    for z, a in ((0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (3, 0), (3, 1), (4, 0), (4, 1), (4, 2), (5, 0), (5, 1), (6, 1), (6, 2), (11, 0)):
        h = LP.act_header(rom, z, a)
        cells, _, _ = LP.decode_layout_stream(rom, h["layout_rom"], 4095)
        w = h["width_cells"]
        cands = [(i % w, i // w) for i, v in enumerate(cells) if surf[v] == 13 and i // w >= 3 and surf[cells[i - w]] == 0]
        tried, hit = 0, None
        for (cx, cy) in cands[:6]:
            tried += 1
            anchor = (cx * 32 + 16, cy * 32 - 30)
            run = run_scenario(rom, z, a, anchor, 140, inject=inj, stop_after_break=50, watch=[(cx, cy)])
            if any(e["kind"] == "break" for e in run["tracer"].events):
                hit = (cx, cy, anchor, run)
                break
        key = "%d/%d" % (z, a)
        if not hit:
            out[key] = OrderedDict(
                status=("floor path not applicable: every $0D cell has a non-empty cell above it (tunnel or wall); only the side / ceiling paths can break it" if not cands
                        else "no floor break reproduced"), cells_with_empty_air_above=len(cands), candidates_tried=tried)
            continue
        cx, cy, anchor, run = hit
        sh = build_shards(rom, run, tables)
        tile = first_sat_tile(run)
        art = shard_art(run["machine"], tile) if tile is not None else None
        stat = static_shard_art(rom, z, a)
        out[key] = OrderedDict(
            zone_act=[z, a], cell=[cx, cy], candidates_tried=tried, start_anchor=list(anchor), breaks=sh["breaks"][:2], shards=[
                OrderedDict((k, v) for k, v in x.items() if k != "trace") for x in sh["shards"][:4]],
            shard_positions_first_ticks={str(x["quadrant"]): x["trace"][:6] for x in sh["shards"][:4]},
            model_mismatches=sh["model_check"]["mismatches"], art=clean(art) if art else None,
            static_stream_rgba_equals_emulated=(bool(art) and art["rgba_sha256"] == stat["rgba_sha256"]),
            static_stream_visible_half=stat["visible_half"],
            mailbox_writes=sh["breaks"][0]["sound_writes"] if sh["breaks"] else [],
            handler_used=[e["handler"] for e in run["tracer"].events if e["kind"] == "handler_entry"][:1])
        if output and art and z in (0, 2, 3, 11):
            write_art_png(output / ("shard-art-z%da%d.png" % (z, a)), art)
    return out


def crumble_cross_check(rom: bytes) -> OrderedDict:
    """Adjacent check: the type-$13 crumble shards in SEZ1 display the same live tile pair as the type-$07 shards."""
    px, py = 68 * 32 + 16, 6 * 32 - 18
    s = boot_zone(patched_rom(rom, 2, 0, (px - 104, py - 112), (px, py)), 2, 0)
    seen = []
    for f in range(200):
        s.pad = 0
        s.run_frame()
        if any(s.mem[0xD540 + i * 0x40] == 0x13 and s.mem[0xD540 + i * 0x40 + 0x3F] != 0 for i in range(LOOP_SLOTS)):
            n = sum(1 for _, _, _, n_ in s.sat() if n_ == 0x66)
            if n:
                seen.append((f, n, sha(bytes(s.vram[0xCC0:0xD00]))))
    stat = static_shard_art(rom, 2, 0)
    return OrderedDict(zone_act=[2, 0], crumble_start=[px, py], frames_with_type13_shard_sprites=len(seen),
                       live_tile_pair_sha256=sorted({x[2] for x in seen}), static_stream_tile_bytes_sha256=stat["tile_bytes_sha256"],
                       live_equals_static_final_stream=bool(seen) and all(x[2] == sha(stat["_data"]) for x in seen))


# ----------------------------------------------------------------------------------------------------------------
# images (ignored build/ output only)
# ----------------------------------------------------------------------------------------------------------------
def render_strip(rom: bytes, report: dict, output: Path) -> None:
    from PIL import Image
    b0 = report["breaks"][0]
    bf = b0["video_frame"]
    offsets = [-2, 0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 26, 32, 40]
    shots = {bf + 1 + o for o in offsets}           # run_scenario labels frames by s.frame after the run
    run = run_scenario(rom, THZ2[0], THZ2[1], SPIN_DASH_START, 190, pad=lambda f: corridor_pad(f, report["spin_dash_taps"]), shots=shots)
    cx0, cy0 = b0["cell_world"]
    tiles = []
    for o in offsets:
        rgb = run["images"].get(bf + 1 + o)
        if rgb is None:
            continue
        cam = [pf for pf in run["per_frame"] if pf["video_frame"] == bf + o]
        camx = cam[0]["camera"][0] if cam else 0
        sx = max(0, min(256 - 128, cx0 - camx - 48))
        crop = Image.new("RGB", (128, 96))
        crop.putdata([rgb[y + 56][sx + x] for y in range(96) for x in range(128)])
        tiles.append(crop.resize((256, 192), Image.NEAREST))
    sheet = Image.new("RGB", (256 * 5, 192 * ((len(tiles) + 4) // 5)))
    for i, tl in enumerate(tiles):
        sheet.paste(tl, ((i % 5) * 256, (i // 5) * 192))
    sheet.save(output / "thz2-corridor-first-break-strip.png")


# ----------------------------------------------------------------------------------------------------------------
# POC (read-only)
# ----------------------------------------------------------------------------------------------------------------
def pre_override_pair(rom: bytes, zone: int, act: int) -> OrderedDict:
    """VRAM tiles $66/$67 at the instant the level loader reaches $295B (before $79F2 replaces them), rendered with the ROM sprite palette."""
    from sms_frame_harness import SMS, BTN_1, BTN_2
    s = SMS(rom)
    st = {"done": False, "pair": None}
    s.add_pc_hook(0x07D5, lambda m: (m._write(0xD297, zone), m._write(0xD298, act)))
    s.add_pc_hook(0x4E97, lambda m: st.__setitem__("done", m.frame > 300))
    s.add_pc_hook(0x295B, lambda m: st.__setitem__("pair", bytes(m.vram[0xCC0:0xD00])))
    for f in range(5000):
        s.pad = 0 if f < 250 else (BTN_1 if f < 700 and f % 40 < 3 else ((BTN_1 | BTN_2) if not st["done"] and f % 60 < 10 else 0))
        s.run_frame()
        if st["done"] and s.mem[0xD500] == 1:
            break
    data = st["pair"]
    sel = LP.palette_selection(rom, zone, act)
    pal = A.palette_rgba(rom, sel["sprite_index"])
    pixels = A.decode_mode4_tile(data[:32]) + A.decode_mode4_tile(data[32:64])
    rgba = bytearray()
    for r in pixels:
        for v in r:
            rgba += bytes(pal[v])
    return OrderedDict(zone=zone, act=act, tile_bytes_sha256=sha(data), rgba_sha256=sha(bytes(rgba)), _rgba=bytes(rgba),
                       opaque_pixels=sum(1 for r in pixels for v in r if v))


def function_body(text: str, name: str) -> str | None:
    i = text.find("function " + name)
    if i < 0:
        return None
    j = text.find("{", i)
    depth, k = 0, j
    while k < len(text):
        depth += text[k] == "{"
        depth -= text[k] == "}"
        k += 1
        if depth == 0:
            break
    return text[i:k]


def poc_report(poc: Path, arts: dict, pre: dict) -> OrderedDict:
    import re
    import visual0_sonic_catalogue as C
    out = OrderedDict()
    adapter = (poc / "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml").read_text(encoding="utf-8")
    core = (poc / "scripts/SCR_chaos_core/SCR_chaos_core.gml").read_text(encoding="utf-8")
    body = function_body(adapter, "SCR_chaos_break_block") or ""
    callers = []
    for p in sorted((poc / "scripts").glob("*/*.gml")):
        t = p.read_text(encoding="utf-8", errors="replace")
        if "SCR_chaos_break_block" in t or "SCR_cc_break13" in t:
            callers.append(str(p.relative_to(poc)))
    allsrc = ""
    for p in sorted(list((poc / "scripts").glob("*/*.gml")) + list((poc / "objects").glob("*/*.gml"))):
        allsrc += p.read_text(encoding="utf-8", errors="replace") + "\n"
    out["break_function"] = OrderedDict(
        file="scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml", function="SCR_chaos_break_block", source_sha256=sha(body.encode()),
        creates_instance=("instance_create" in body), plays_sound=("Sound" in body or "audio_" in body), writes_cell_9d=("157" in body),
        pushes_chaos_broken_cells=("chaosBrokenCells" in body), comment_in_source=re.findall(r"//[^\n]*Fragments[^\n]*\n[^\n]*", adapter)[:1],
        callers=callers)
    out["rom_condition_parity"] = OrderedDict(
        floor="SCR_cc_break13_floor: states 15/16/21/26 excluded, rolling flag required, vy := -1088 ($FBC0), floor flag cleared, airborne set: " +
              ("present" if "cp_c.vy = -1088" in core else "ABSENT"),
        side="SCR_cc_break13_side: rolling flag, |vx hi| >= 3, +/-$40 below 7: " + ("present" if "cp_magnitude < 3" in core else "ABSENT"),
        ceiling="owner clear -> break, owner set -> crush death: " + ("present" if "SCR_cc_crush_death" in core else "ABSENT"),
        d3b2_modelled=("D3B2" in allsrc.upper().replace("$D3B2", "D3B2") and "D3B2" in allsrc))
    out["fragment_objects"] = OrderedDict(
        type07_object_in_poc=bool(re.search(r"OBJ_chaos_object_07", allsrc)), instance_creation_for_0d_break=False,
        sound_a3_requests=sorted(set(re.findall(r"scripts/[^\n]*", ""))) or [],
        a3_sources=[p for p in callers if False])
    # sound $A3 appearances (only the type-$13 crumble path)
    a3 = []
    for p in sorted((poc / "scripts").glob("*/*.gml")):
        t = p.read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(t.splitlines(), 1):
            if re.search(r"chaosLastSoundRequest\s*=\s*\$A3\b", line):
                a3.append("%s:%d" % (p.relative_to(poc), n))
    out["fragment_objects"]["sound_a3_requests"] = a3
    out["broken_cell_drawing"] = OrderedDict(
        thz2_terrain=("SPR_chaos_thz2_block_9d" in (poc / "objects/OBJ_chaos_thz2_terrain/Draw_0.gml").read_text(encoding="utf-8")),
        thz3_terrain=("SPR_chaos_thz2_block_9d" in (poc / "objects/OBJ_chaos_thz3_terrain/Draw_0.gml").read_text(encoding="utf-8")))
    sprites = OrderedDict()
    for name in ("SPR_chaos_sez_shard", "SPR_chaos_aqz_shard", "SPR_chaos_ss4_shard", "SPR_chaos_thz2_block_9d", "SPR_chaos_sez_block_9d",
                 "SPR_chaos_mghz_block_9d", "SPR_chaos_aqz_block_9d", "SPR_chaos_gpz_block_9d", "SPR_chaos_eez_block_9d"):
        d = poc / "sprites" / name
        if not d.exists():
            sprites[name] = "absent"
            continue
        yy = json.loads((d / (name + ".yy")).read_text(encoding="utf-8"))
        pngs = sorted(d.glob("*.png"))
        info = OrderedDict(width=yy["width"], height=yy["height"], xorigin=yy["sequence"]["xorigin"], yorigin=yy["sequence"]["yorigin"], frames=len(pngs))
        dec = C.png_rgba(pngs[0]) if pngs else None
        tr_ = C.trim(*dec) if dec else None
        if tr_:
            info["trimmed"] = [tr_[0], tr_[1]]
            info["trimmed_rgba_sha256"] = sha(tr_[2])
            for z, art in arts.items():
                ta = C.trim(8, 16, art["_rgba"])
                info.setdefault("equals_rom_final_stream_79f2", {})[z] = bool(ta and (tr_[0], tr_[1]) == (ta[0], ta[1]) and tr_[2] == ta[2])
            for z, art in pre.items():
                ta = C.trim(8, 16, art["_rgba"])
                info.setdefault("equals_rom_pre_override_common_stream", {})[z] = bool(ta and (tr_[0], tr_[1]) == (ta[0], ta[1]) and tr_[2] == ta[2])
                info.setdefault("alpha_mask_equals_pre_override_common_stream", {})[z] = bool(ta and (tr_[0], tr_[1]) == (ta[0], ta[1]) and C.mask_of(tr_[2]) == C.mask_of(ta[2]))
            for z, art in arts.items():
                ta = C.trim(8, 16, art["_rgba"])
                info.setdefault("alpha_mask_equals_rom_final_stream_79f2", {})[z] = bool(ta and (tr_[0], tr_[1]) == (ta[0], ta[1]) and C.mask_of(tr_[2]) == C.mask_of(ta[2]))
        sprites[name] = info
    out["sprites"] = sprites
    out["type13_shards"] = OrderedDict(
        description="SCR_chaos_sez_s2.gml draws type-$13 (crumbling floor, surface $0C) shards with SPR_chaos_{sez,aqz,ss4}_shard; mapping frame 15 is shared with type $07",
        draw_function="chaos_s2_draw", filter="cp_s.type == $13 and frame == 15; type $07 is not drawn")
    return out


# ----------------------------------------------------------------------------------------------------------------
# build / main
# ----------------------------------------------------------------------------------------------------------------
def build(rom: bytes, output: Path | None = None, poc: Path | None = None, static_only: bool = False) -> dict:
    if sha(rom) != R.SHA256:
        raise ValueError("ROM SHA-256 mismatch")
    if output:
        output.mkdir(parents=True, exist_ok=True)
    tables = offset_tables(rom)
    static = OrderedDict(
        assembly=verify_assembly(rom), type7_scripts=type7_scripts(rom), offset_tables=tables, mapping=mapping_info(rom),
        cull_table=cull_table(rom), census_surface_0d=census_0d(rom), shard_art_streams=shard_art_table(rom),
        gravity=OrderedDict(callback="$9BB5 -> $0350 -> $5F84 (BC = $1000, DE = $00C0) then $0338 -> $60FB", gravity_8_8=0xC0, terminal_8_8=0x0FC0,
                            note="vy += $00C0 first, then position += velocity; sums >= $1000 are discarded so speed holds at $0FC0"),
        object_layout=OrderedDict({"+00": "type", "+01": "current state", "+02": "requested state", "+04": "flags (bit0 set by init; bit6 = culled, set by $61E1)",
                                   "+06": "mapping frame", "+07": "record timer", "+08": "tile add? (init sets $9C only in zone 6 act 2; effect unresolved)",
                                   "+0C/0D": "callback vector", "+0E/0F": "script cursor", "+10..12": "X 8.16 (sub, lo, hi)", "+13..15": "Y 8.16",
                                   "+16/17": "X speed 8.8", "+18/19": "Y speed 8.8", "+3F": "parameter = quadrant 0..3"}))
    report = OrderedDict(format=1, rom_sha256=sha(rom), research_base="ce298af87341d4cce2917461ef4c1b3137f45c91",
                         evidence="DECODED DATA + BYTE-VERIFIED ASSEMBLY + EMULATED ORIGINAL FRAME + CLOSED-FORM MODEL", static=static)
    arts = {}
    if not static_only:
        rep, run, art = corridor_report(rom, output, tables)
        arts["thz2_corridor"] = art
        emu = OrderedDict(primary_corridor=rep, spin_dash_sweep=OrderedDict(), controls=controls(rom, tables), floor_fixtures=floor_fixtures(rom, tables, output),
                          type13_crumble_cross_check=crumble_cross_check(rom))
        for taps in (1, 2, 3, 4):
            r, _, _ = corridor_report(rom, None, tables, taps=taps, label="taps%d" % taps)
            emu["spin_dash_sweep"][str(taps)] = OrderedDict(
                player_vx_at_first_break=r["breaks"][0]["player"]["vx"], summary=r["summary"],
                lives_after=r["lives"]["after"], breaks=len(r["breaks"]),
                shards_created_per_break=[b["shards_created"] for b in r["breaks"]], update_gaps=[b2["update"] - b1["update"] for b1, b2 in zip(r["breaks"], r["breaks"][1:])])
        report["emulated"] = emu
        if output:
            render_strip(rom, rep, output)
            write_art_png(output / "shard-art-thz2.png", art)
        for key, fx in emu["floor_fixtures"].items():
            pass
    if poc and not static_only:
        z, pre = {}, {}
        for zn, zz in (("sez", 2), ("aqz", 4), ("ss4", 11)):
            z[zn] = static_shard_art(rom, zz, 0)
            pre[zn] = pre_override_pair(rom, zz, 0)
        report["poc"] = clean(poc_report(poc, z, pre))
    return clean(report)


def trajectory_table(tables: dict, ticks: int = 48) -> OrderedDict:
    """Position relative to the struck cell's top-left corner after every callback (k = 0 is the init callback of the break tick)."""
    out = OrderedDict()
    for key, name in (("player_x_speed_ge_0_table_9b75", "player_x_speed_hi_ge_0"), ("player_x_speed_lt_0_table_9b95", "player_x_speed_hi_lt_0")):
        rows = tables[key]
        out[name] = OrderedDict()
        for q in range(4):
            m = model_shard(rows, q, 0, 0, ticks)
            out[name][str(q)] = OrderedDict(
                start_offset=[rows[q]["x_offset"], rows[q]["y_offset"]], start_speed_8_8=[rows[q]["x_speed_8_8"], rows[q]["y_speed_8_8"]],
                x_8_8=[int(round(r["x"] * 256)) for r in m], y_8_8=[int(round(r["y"] * 256)) for r in m])
    return out


def implementation_contract(rep: dict) -> OrderedDict:
    st = rep["static"]
    emu = rep.get("emulated", {})
    prim = emu.get("primary_corridor", {})
    cull = st["cull_table"]
    arts = st["shard_art_streams"]["zones"]
    return OrderedDict(
        format=1, scope="surface-$0D breakable terrain (blocks $9B/$9C -> $9D): the four-shard presentation; NOT the THZ1 $47 puff / rising icon",
        evidence="BYTE-VERIFIED ASSEMBLY + DECODED DATA + EMULATED ORIGINAL FRAME (THZ2 corridor, 6 breaks / 21 shards, 0 model mismatches)",
        break_tick=OrderedDict(
            cell="layout cell := $9D in the break tick; the 4 x 4 name-table words change in the same tick (block $9C mapping -> block $9D mapping); there is no intermediate frame, no timer and no hit animation",
            order_inside_tick="player pass (terrain handler -> $7898) first, then the object pass: all four shards run their state-0 record in the break tick",
            paths=OrderedDict(
                floor_6b2c="player state not in {$0F,$10,$15,$1A}; +$03 bit 1 (attack posture); then $D3B2 := $10 (written, never read), Y speed := $FBC0 (-4.25), floor flag cleared, +$03 bit 0 set, break",
                side_right_72b6="+$03 bit 1 and |X speed high byte| >= 3; when the high byte is < 7 the X speed gains +$0040; break",
                side_left_72dd="+$03 bit 1 and |X speed high byte| >= 3; when the negated high byte is < 7 the X speed gains -$0040 (faster leftward); break",
                ceiling_7464="support owner $D3C0 == 0 -> break; owner set -> crush death $4984 (no break)")),
        spawn=OrderedDict(
            objects=4, type=7, parameters=[0, 1, 2, 3], anchor="struck cell top-left = (sample X & $FFE0, sample Y & $FFE0), identical for the four",
            pool="each request takes the first free slot of the 16 spawn slots $D540..$D93F (shared with every object); a request with no free slot is silently dropped (no retry)",
            observed_drops=OrderedDict(corridor_breaks_with_drops=[b["index"] for b in prim.get("breaks", []) if b["shards_dropped"]],
                                       shards_created_per_break=[b["shards_created"] for b in prim.get("breaks", [])],
                                       note="the 4th and 5th breaks of the primary run lost 2 and 1 shards because 12 earlier shards plus 2 level objects filled the pool; dropped parameters are the highest ones (2,3 / 3)")),
        shard_table_selector="player X speed high byte ($D517) at the shard's first (init) callback: >= 0 -> table $9B75, < 0 -> table $9B95",
        shard_tables=st["offset_tables"], trajectory_relative_to_cell_origin=trajectory_table(st["offset_tables"]),
        per_tick=OrderedDict(
            k0="init callback (break tick): position := cell origin + offset, velocity := table, requested state := 1, +$04 bit 0 set; the record shows mapping frame 0 (no pieces): nothing is drawn",
            k_ge_1="record frame 15 (one piece, relative (-4,-16), 8x16 sprite tiles $66/$67); $9BB5: if +$04 bit 6 (culled) the object removes itself, else Y speed += $00C0 (sums >= $1000 are discarded, so the speed saturates at $0FC0), then position += speed",
            integration="x24 += vx; vy := vy + 192 (unless the sum is >= $1000); y24 += vy (gravity BEFORE the move)"),
        lifetime=OrderedDict(
            rule="the shard is removed by its own callback in the tick AFTER the visibility routine $61E1 set +$04 bit 6; the flag is set when the object anchor leaves the cull window",
            cull_window_screen_offsets=OrderedDict(x=[cull["on_screen_cell_columns"]["screen_x_from"], cull["on_screen_cell_columns"]["screen_x_to"]],
                                                   y=[cull["on_screen_cell_rows"]["screen_y_from"], cull["on_screen_cell_rows"]["screen_y_to"]],
                                                   note="screen offset = object X/Y minus camera X/Y in the ROM's 256 x 192 (224-line) window; beyond +/-32 of the 256 x 256 box (values 2/3 of the $8146 map) the flag is set"),
            observed_ticks_alive=OrderedDict(min=prim.get("summary", {}).get("min_ticks_alive"), max=prim.get("summary", {}).get("max_ticks_alive")),
            observed_exits=OrderedDict(below=prim.get("summary", {}).get("deleted_below_view"), right=prim.get("summary", {}).get("deleted_right_of_view"),
                                       left=prim.get("summary", {}).get("deleted_left_of_view")),
            widescreen="the X bound is tied to the 256-pixel window; in a wider view shards that fly right would be culled while still inside the wider view unless the right bound is extended by the extra width (the accepted adapters do this for other objects); the Y bound (>= 288 below the camera) decides most lifetimes"),
        sound=OrderedDict(
            request="$A3 via script command FF 06 at the head of state 0: each of the 4 shards writes it (twice, back to back) in the break tick",
            effective="the driver mailbox keeps one pending byte: writes between two vblank interrupts collapse into one request, so a break yields one driver-visible request (two when the tick straddles a vblank, as in the first corridor break); observed accepted by the driver (priority byte 0x58 versus the current $DE0F); a reissue restarts the effect",
            driver_visible_requests_per_break=[r.get("driver_visible_requests") for r in prim.get("sound", {}).get("per_break", [])],
            note="numeric request only; no PC waveform is claimed; the type-$13 crumble path requests the same $A3"),
        art=OrderedDict(
            source="the shard tile pair $66/$67 is written LAST by the level loader: $2934 -> $79F2 loads a 2-tile stream from bank $0E, pointer table $A3A0 indexed by ZONE (D297), into VRAM $0CC0",
            per_zone={z: OrderedDict(stream_cpu=r["stream_cpu"], visible_half=r["visible_half"], sprite_palette_index=r["sprite_palette_index"], rgba_sha256=r["rgba_sha256"]) for z, r in arts.items()},
            registration="8x16 sprite piece at (object X - 4, object Y - 16); the visible 8x8 is the TOP half for zones SEZ/AQZ/SS1,2,4/SS3,5 (rows Y-16..Y-9) and the BOTTOM half for THZ/GPZ/MGHZ/EEZ (rows Y-8..Y-1)",
            warning="the earlier common-stream pair (16-row brick) is overwritten before play and is NOT what the original shows"),
        differs_from_thz1_block_47=OrderedDict(
            block="$47 (surface $16) -> $46, handler $6AE3/$7857 | $9B/$9C (surface $0D) -> $9D, handler $6B2C/$72B6/$72DD/$7464 -> $7898",
            objects="$47: one type-$0F puff (param $40, frames $07/$08/$09, 37 updates) + one type-$11 rising icon (frame $0D, 33 updates) | $0D: four type-$07 shards (frame 15)",
            sound="$47: $AB from the puff | $0D: $A3 from each shard (collapses to one)",
            reward_and_side_effects="$47: +10 rings, D3B3 := 1 (dynamic tiles) | $0D: no ring/score change, no dynamic tile load; floor path only: D3B2 := $10 and Y speed := $FBC0",
            conclusion="the two effects share no object, sprite, sound or timing; $47's icon must not be used as the contract for destructible terrain"),
        poc_gaps=rep.get("poc", {}).get("break_function", {}) and OrderedDict(
            creates_shards=False, plays_a3=False, shard_art_equals_rom=False, d3b2_modelled=False,
            note="see docs/visual1-loop-shards.md section B6"))


def dumps(rep: dict) -> str:
    return json.dumps(rep, indent=1) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--poc", type=Path)
    p.add_argument("--metadata", type=Path)
    p.add_argument("--check", action="store_true")
    p.add_argument("--static-only", action="store_true")
    p.add_argument("--contract", type=Path, help="also write the implementation contract (needs the emulated run)")
    a = p.parse_args()
    rep = build(R.load(a.rom), a.output, a.poc, a.static_only)
    if a.contract and not a.static_only:
        ctr = implementation_contract(rep)
        text_c = dumps(clean(ctr))
        if a.check:
            if a.contract.read_text(encoding="utf-8") != text_c:
                sys.exit("contract differs: " + str(a.contract))
            print("contract identical")
        else:
            a.contract.parent.mkdir(parents=True, exist_ok=True)
            a.contract.write_text(text_c, encoding="utf-8")
    text = dumps(rep)
    if a.metadata:
        if a.check:
            if a.metadata.read_text(encoding="utf-8") != text:
                sys.exit("metadata differs: " + str(a.metadata))
            print("metadata identical")
        else:
            a.metadata.parent.mkdir(parents=True, exist_ok=True)
            a.metadata.write_text(text, encoding="utf-8")
    print(json.dumps({"breaks": rep.get("emulated", {}).get("primary_corridor", {}).get("summary", {}).get("breaks")}))


if __name__ == "__main__":
    main()

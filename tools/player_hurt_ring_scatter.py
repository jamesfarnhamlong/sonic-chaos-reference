#!/usr/bin/env python3
"""Player hurt / lost-ring scatter audit (shared global mechanic) - research only, deterministic.

Answers: how many rings a hurt emits, the scatter object (type $06) lifecycle, its initial velocities, gravity, floor/ceiling
interaction, bounce decay, lifetime, pickup lockout and box, off-screen removal, interaction with hurt/invulnerability state, the
shared counter path used by terrain rings, and an exact GPZ3 boss example.
Output: data/rom-cache/player-hurt-ring-scatter.json (numeric labels, hashes and 16-byte prefixes only; no ROM image).

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT (original Z80 routines on
tools/oracle.py), EMULATED ORIGINAL FRAME (tools/sms_frame_harness.py, whole game), MODEL (pure-Python re-implementation checked
against the ROM), POC SOURCE (READ-ONLY), UNRESOLVED.

Usage:
  python tools/player_hurt_ring_scatter.py ROM.sms [--check] [--static-only]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import rom as R  # noqa: E402
from oracle import Oracle  # noqa: E402
import platform_spike_collision as P  # noqa: E402

ROM_SHA256 = R.SHA256
OUTPUT = ROOT / "data" / "rom-cache" / "player-hurt-ring-scatter.json"

# ----------------------------------------------------------------------------------------------------------------------
# ROM / RAM constants (all numeric; names are descriptive only)
# ----------------------------------------------------------------------------------------------------------------------
HURT_GATE = 0x48BC          # damage gate: consumes request $D3B0 / contact $D520
HURT_ENTRY = 0x48F7         # shared hurt/death entry (terrain spikes and the gate both reach it)
SPAWN = 0x5E9C              # first-free-slot allocator used by the scatter loop (C = type, H = token)
SCHEDULER = 0x5DD1          # whole object phase (19 slots from $D540)
SLOT_BASE, SLOT_SIZE, SLOT_COUNT = 0xD540, 0x40, 19
SPAWN_SLOTS = 16            # $5E9C scans only the first 16 slots
TYPE_RING = 6
BANK_RING = 12              # type < $26 objects page bank $0C: file $30000, CPU $8000
LOCKOUT_UPDATES = 16        # scheduler passes with the non-collectable callback (U1..U16); first pickup test at U17
SPARKLE_UPDATES = 28
CELL_TABLE_FILE = 0x70146   # bank $1C:$8146, 32 x 32 lifetime cells of 16 px
LAYOUT_BASE = 0xC001
ROW_TABLE_128 = 0x5A97      # ROM table row*128 (THZ layout stride) used as the lab's $D168
HEADER_BANK, HEADER_TABLE = 14, 0x38000

RAM = {
    "ring_counter_bcd": 0xD29A, "life_counter_bcd": 0xD299, "hud_refresh": 0x314A,
    "damage_request": 0xD3B0, "contact_owner": 0xD520, "invulnerability_timer": 0xD3B1,
    "player_state": 0xD501, "player_requested": 0xD502, "player_flags": 0xD503, "player_x": 0xD511, "player_y": 0xD514,
    "player_vx": 0xD516, "player_vy": 0xD518, "camera_x": 0xD174, "camera_y": 0xD176, "sound_request": 0xDE04,
    "water_condition": 0xD443,
}


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def s16(v: int) -> int:
    return (v + 32768) % 65536 - 32768


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def file_of(bank: int, cpu: int) -> int:
    return cpu if cpu < 0x8000 else bank * 0x4000 + cpu - 0x8000


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise SystemExit("ROM must be Sonic Chaos (Europe) v1.2 (SHA-256 eabc8db5...e607)")


# ----------------------------------------------------------------------------------------------------------------------
# Part A - static facts (byte-verified)
# ----------------------------------------------------------------------------------------------------------------------
ROUTINES = [
    # name, bank (None = fixed), cpu start, cpu end (exclusive), role
    ("damage_gate", None, 0x48BC, 0x48F7, "consumes $D3B0 request / $D520 contact; invulnerable countdown; $D532 == 6 clears the request"),
    ("hurt_entry", None, 0x48F7, 0x4984, "state $11 branch, ring test, scatter loop, $D29A := 0, sound $A4, invulnerability $D3B1 := $78, state $1E, knockback"),
    ("death_entry", None, 0x4984, 0x49A4, "no rings: state $1F, vy $FB00 (no scatter)"),
    ("object_allocator", None, 0x5E9C, 0x5EB7, "first free of the first 16 slots at $D540: type := C, token (+$3F) := H"),
    ("object_scheduler_phase", None, 0x5DD1, 0x5DF1, "19 slots, ascending"),
    ("object_scheduler_slot", None, 0x5DF1, 0x5E70, "type < $26: bank $0C, engine $64FA, callback $5E91, then $61E1 when state != 0"),
    ("lifetime_61E1", None, 0x61E1, 0x6276, "viewport / cell lifetime: active, asleep (bit 6), delete ($FF / $FE)"),
    ("move_60FB", None, 0x60FB, 0x613C, "24-bit fixed-point X/Y integration of +$16/+$18"),
    ("gravity_631A", None, 0x631A, 0x6328, "+$18/+$19 += DE"),
    ("ceiling_probe_6168", None, 0x6168, 0x6178, "$7725(BC=0, DE=-16): header flags bit 7 only -> 0 (solid) / $FF (free); one-way (bit 6) cells do not stop a rising ring"),
    ("floor_probe_614E", None, 0x614E, 0x6168, "$7725(BC=0, DE=0): header flags bits 6/7 -> 0 (solid) / $FF (free)"),
    ("overlap_617E", None, 0x617E, 0x61BB, "|dx| < 12 and |dy| < 12 against the player anchor ($D511/$D514)"),
    ("abs_compare_61BB", None, 0x61BB, 0x61D6, "unsigned |HL - DE| < BC helper"),
    ("terrain_probe_7725", None, 0x7725, 0x77B0, "block lookup, returns header byte 0 (flags)"),
    ("ring_counter_3138", None, 0x3138, 0x314A, "BCD +1 of $D29A; carry (100 rings) -> $3104 (sound $A9, $D299 + 1) and $178F"),
    ("ring_init_9A2B", BANK_RING, 0x9A2B, 0x9A7C, "state 0 callback: position, velocities from the index tables, bounce speed, flags"),
    ("ring_tables_9A7C", BANK_RING, 0x9A7C, 0x9A98, "X and Y velocity tables, 7 words each"),
    ("ring_state1_9A98", BANK_RING, 0x9A98, 0x9AF1, "state 1 callbacks: pickup test ($9A98) falls into movement ($9A9E)"),
    ("ring_pickup_9AF1", BANK_RING, 0x9AF1, 0x9AFE, "sound $BF, $0347 (-> $3138), requested state 2"),
    ("ring_scripts_99FB", BANK_RING, 0x99FB, 0x9A2B, "state table + state 0 / state 1 scripts"),
    ("ring_sparkle_script_9BE8", BANK_RING, 0x9BE8, 0x9C08, "state 2 script (frames 5/6), last record callback $034A"),
    ("sparkle_end_64F0", None, 0x64F0, 0x64F5, "type := $FE"),
]


def static_routines(rom: bytes) -> list:
    out = []
    for name, bank, a, b, role in ROUTINES:
        fo = file_of(bank if bank is not None else 0, a)
        fe = file_of(bank if bank is not None else 0, b)
        data = rom[fo:fe]
        out.append({"name": name, "bank": None if bank is None else h(bank, 2), "cpu": h(a), "end": h(b), "file": h(fo, 5),
                    "length": len(data), "sha256": sha(data), "first_16": data[:16].hex(" "), "role": role})
    return out


def decode_script(rom: bytes, cpu: int) -> list:
    """Records `duration frame callback` until an `FF cc ...` command (cc 00 = restart, cc 07 = jump)."""
    recs, a = [], cpu
    while True:
        fo = file_of(BANK_RING, a)
        if rom[fo] == 0xFF:
            cmd = rom[fo + 1]
            if cmd == 0x07:
                recs.append({"command": "jump", "to": h(rom[fo + 2] | rom[fo + 3] << 8)})
            elif cmd == 0x00:
                recs.append({"command": "restart"})
            else:
                recs.append({"command": h(cmd, 2)})
            return recs
        recs.append({"duration": rom[fo], "frame": rom[fo + 1], "callback": h(rom[fo + 2] | rom[fo + 3] << 8)})
        a += 4


def static_object(rom: bytes) -> dict:
    tbl = 0x65BA + (TYPE_RING - 1) * 2
    entry = rom[tbl] | rom[tbl + 1] << 8
    fo = file_of(BANK_RING, entry)
    states = [rom[fo + 2 * i] | rom[fo + 2 * i + 1] << 8 for i in range(3)]
    vx = [s16(rom[file_of(BANK_RING, 0x9A7C) + 2 * i] | rom[file_of(BANK_RING, 0x9A7C) + 2 * i + 1] << 8) for i in range(7)]
    vy = [s16(rom[file_of(BANK_RING, 0x9A8A) + 2 * i] | rom[file_of(BANK_RING, 0x9A8A) + 2 * i + 1] << 8) for i in range(7)]
    mp = 0x3C000 + TYPE_RING * 2
    mptr = rom[mp] | rom[mp + 1] << 8
    frames = {}
    for f in range(8):
        q = rom[file_of(15, mptr) + 2 * f] | rom[file_of(15, mptr) + 2 * f + 1] << 8
        rec = rom[file_of(15, q):file_of(15, q) + 5]
        frames[f] = {"record": h(q), "frame_header": rec.hex(" ")}
    return {
        "evidence": "DECODED DATA + BYTE-VERIFIED ASSEMBLY",
        "type": TYPE_RING, "type_table_entry": f"ROM {h(tbl, 5)} -> bank $0C:{h(entry)} (file {h(fo, 5)})",
        "state_table_cpu": [h(s) for s in states],
        "state_0_init": {"script": decode_script(rom, states[0]), "role": "creation update: position, velocities, bounce speed, flags; requests state 1"},
        "state_1_motion": {"script": decode_script(rom, states[1]), "role": "flight animation frames 1,2,4,3 (4 updates each); records 1-4 callback $9A9E (no pickup), records 5-8 callback $9A98 (pickup test then the same motion), jump back to record 5"},
        "state_2_sparkle": {"script": decode_script(rom, states[2]), "role": "pickup sparkle frames 5/6, 4 updates each, last record callback $034A (type := $FE)"},
        "velocity_tables": {
            "x_table": h(0x9A7C), "y_table": h(0x9A8A), "index_is_token": "+$3F, assigned 0..N-1 in loop order by the allocator call (register H)",
            "x_8_8": vx, "y_8_8": vy,
            "x_px_per_update": [v / 256 for v in vx], "y_px_per_update": [v / 256 for v in vy],
        },
        "mapping": {"table_entry": h(mp, 5), "pointer": h(mptr), "frames": frames,
                    "note": "frames 1-4 = flight animation (state 1), 5/6 = pickup sparkle (state 2); frame 0 = empty (state 0 init); frame 7 is not used by the scripts; which art each frame shows was not rendered here"},
        "init_constants": {"spawn_x": "player X ($D511)", "spawn_y": "player Y ($D514) - 16", "bounce_speed": -1024, "bounce_step": 128,
                           "flags_03": "bits 7 and 6 set (+$03 = $C0): bit 7 makes the shared helper ignore the player's bit-6 gate, bit 6 disables the shared contact helper $6328 (the ring never uses it)",
                           "flags_04": "bit 0 set at init; not read by the ring motion/pickup code (meaning UNRESOLVED)",
                           "state_after_init": 1, "gravity_per_update": 32},
    }


def static_vectors(rom: bytes) -> dict:
    out = {}
    for name, a in (("$0338", 0x338), ("$033B", 0x33B), ("$0347", 0x347), ("$034A", 0x34A), ("$037A", 0x37A), ("$0380", 0x380),
                    ("$03FB", 0x3FB), ("$0431", 0x431), ("$032F", 0x32F), ("$032C", 0x32C)):
        out[name] = h(rom[a + 1] | rom[a + 2] << 8)
    return {"evidence": "BYTE-VERIFIED ASSEMBLY (JP vectors)", "targets": out}


def find_bytes(rom: bytes, start: int, end: int, pattern: bytes) -> list:
    out, i = [], start
    while True:
        i = rom.find(pattern, i, end)
        if i < 0:
            return out
        out.append(i)
        i += 1


def static_shared_paths(rom: bytes) -> dict:
    """Terrain rings (type 7 block probe, $753E) versus object rings: where each reaches the counter."""
    terrain_tail = find_bytes(rom, 0x753E, 0x7680, bytes([0xC3, 0x38, 0x31]))
    pickup = file_of(BANK_RING, 0x9AF1)
    return {
        "evidence": "BYTE-VERIFIED ASSEMBLY",
        "object_ring_pickup_9AF1": rom[pickup:pickup + 13].hex(" "),
        "object_ring_pickup_reads": "LD A,$BF ; LD ($DE04),A ; CALL $0347 ; LD (IX+2),2 ; RET   ($0347 = JP $3138)",
        "terrain_ring_handler_jp_3138_at": [h(x, 5) for x in terrain_tail],
        "counter_routine": "$3138: $D29A := BCD($D29A + 1); on wrap to $00: $3104 (sound $A9, $D299 + 1 capped at $99) and $178F; then $314A HUD refresh",
        "conclusion": "both the layout (terrain) ring and a dropped ring end in the same increment routine $3138; detection, sound sequencing and the visual effect are separate",
    }


def water_scan(rom: bytes) -> dict:
    """Does any scatter-related routine read the water condition $D443 (or write it)?"""
    pat = bytes([0x43, 0xD4])
    rows = []
    for name, bank, a, b, _ in ROUTINES:
        fo = file_of(bank if bank is not None else 0, a)
        fe = file_of(bank if bank is not None else 0, b)
        rows.append({"routine": name, "references_d443": bool(find_bytes(rom, fo, fe, pat))})
    return {"evidence": "BYTE-VERIFIED ASSEMBLY (operand scan of every scatter-related routine)", "rows": rows,
            "any_reference": any(r["references_d443"] for r in rows)}


# ----------------------------------------------------------------------------------------------------------------------
# Part B - pure model (checked against the ROM below)
# ----------------------------------------------------------------------------------------------------------------------

class World:
    """Layout cells (128-wide stride) plus header flags; mirrors `$7725` for the flag byte only."""

    def __init__(self, hdr_flags: list):
        self.cells = {}
        self.flags = hdr_flags

    def put(self, col: int, row: int, block: int) -> None:
        self.cells[(col, row)] = block

    def probe_flags(self, x: int, y: int, de: int) -> int:
        """`$7725(BC=0, DE=de)` for an object whose anchor is (x, y): header byte 0 of the addressed block, 0 outside the map."""
        yy = (y + de + 0x12) & 0xFFFF
        if yy & 0x8000:
            yy = 0
        row = (((yy << 3) & 0xFFFF) >> 8) & 0x7F          # H after three SLA/RL, then L = 2*H (8 bit) indexes the word table
        col = (x & 0xFFFF) >> 5
        idx = row * 128 + col + 1
        if idx > 4095 or idx < 1:                         # address outside $C000..$CFFF -> block $FF, flags 0
            return 0
        return self.flags[self.cells.get(((idx - 1) % 128, (idx - 1) // 128), 0)]


def floor_flags(f: int) -> bool:
    """`$614E`: bits 6 (one-way) or 7 (solid) of the header byte stop a falling ring."""
    return bool(f & 0xC0)


def ceiling_flags(f: int) -> bool:
    """`$6168`: only bit 7 (solid) turns a rising ring around."""
    return bool(f & 0x80)


def lifetime_class(cells: bytes, x: int, y: int, camx: int, camy: int) -> str:
    """`$61E1`: 'active' (bit 6 cleared), 'asleep' (cell value 2: bit 6 set, alive) or 'delete' (cell 3 or outside the 512 window)."""
    dx = (x + 0x80) & 0xFFFF
    if dx < camx:
        return "delete"
    dx = (dx - camx) >> 1
    if dx >> 8:
        return "delete"
    dy = (y + 0x80) & 0xFFFF
    if dy < camy:
        return "delete"
    dy = (dy - camy) >> 1
    if dy >> 8:
        return "delete"
    v = cells[(dy & 0xF8) * 4 + ((dx >> 3) & 0x1F)]
    if v == 3:
        return "delete"
    return "asleep" if (v & 2) else "active"


class RingModel:
    """One type-`$06` object. Position = 24-bit fixed point (fraction byte + 16-bit pixel), velocities 8.8 two's complement."""

    def __init__(self, index: int, px: int, py: int, vx_table: list, vy_table: list):
        self.index = index
        self.x24 = (px & 0xFFFF) << 8
        self.y24 = ((py - 16) & 0xFFFF) << 8
        self.vx, self.vy = vx_table[index] & 0xFFFF, vy_table[index] & 0xFFFF
        self.bounce = 0xFC00
        self.age = 0              # scheduler passes already executed; the spawn update is pass 0
        self.alive = True
        self.bit6 = False
        self.req = 0
        self.cur = 0
        self.sparkle = None
        self.events = []
        self.bounces = []

    @property
    def x(self):
        return (self.x24 >> 8) & 0xFFFF

    @property
    def y(self):
        return (self.y24 >> 8) & 0xFFFF

    def snap(self):
        return (self.cur, self.req, self.x, self.y, s16(self.vx), s16(self.vy), s16(self.bounce))

    def update(self, world: World, cells: bytes, camera: tuple, player: tuple, hud: dict) -> None:
        if not self.alive:
            return
        age = self.age
        self.age += 1
        if age == 0:                                  # state 0 init callback; the scheduler skips `$61E1` for state 0
            self.req = 1
            return
        self.cur = 2 if self.req == 2 else 1
        if self.req == 2:
            self.sparkle += 1
            if self.sparkle == SPARKLE_UPDATES + 1:   # record 8 fetched: callback $034A sets type $FE
                self.alive = False
                self.events.append(("sparkle_end", age))
                return
        else:
            if age > LOCKOUT_UPDATES:                 # callback $9A98 (pickup test) from pass 17
                dx = abs(s16((self.x - player[0]) & 0xFFFF))
                dy = abs(s16((self.y - player[1]) & 0xFFFF))
                if dx < 12 and dy < 12:
                    hud["pickups"] += 1
                    self.req, self.sparkle, self.pick_age = 2, 0, age
                    self.events.append(("pickup", age))
                    self._lifetime(cells, camera, age)
                    return
            self.vy = (self.vy + 0x20) & 0xFFFF
            self.x24 = (self.x24 + s16(self.vx)) & 0xFFFFFF
            self.y24 = (self.y24 + s16(self.vy)) & 0xFFFFFF
            if self.vy & 0x8000:                      # rising: ceiling probe DE = -16
                if ceiling_flags(world.probe_flags(self.x, self.y, -16)):
                    self.vy = (-self.vy) & 0xFFFF
                    self.events.append(("ceiling", age))
            else:                                     # falling / zero: floor probe DE = 0
                if floor_flags(world.probe_flags(self.x, self.y, 0)):
                    nb = self.bounce + 0x80
                    if nb > 0xFFFF:
                        self.alive = False
                        self.events.append(("bounce_exhausted", age))
                        return
                    self.bounce = self.vy = nb
                    self.bounces.append(age)
                    self.events.append(("bounce", age))
            if self.bit6:                             # `BIT 6,(IX+4)` at $9AE7: set by the previous update's $61E1
                self.alive = False
                self.events.append(("offscreen_bit6", age))
                return
        self._lifetime(cells, camera, age)

    def _lifetime(self, cells, camera, age):
        c = lifetime_class(cells, self.x, self.y, camera[0], camera[1])
        if c == "delete":
            self.alive = False
            self.events.append(("offscreen_delete", age))
        else:
            self.bit6 = c == "asleep"


def bcd_inc(v: int) -> tuple:
    """`ADD A,1 ; DAA` -> (new value, carry)."""
    lo = (v & 15) + 1
    hi = v >> 4
    if lo > 9:
        lo, hi = 0, hi + 1
    if hi > 9:
        return (0, True)
    return (hi << 4 | lo, False)


def ring_count_for(bcd: int) -> int:
    """Objects emitted for a BCD ring byte: high nibble (tens digit) + 1, capped at 7; 0 rings -> death, no scatter."""
    return 0 if bcd == 0 else min(7, (bcd >> 4) + 1)


# ----------------------------------------------------------------------------------------------------------------------
# Part C - controlled lab on the original routines
# ----------------------------------------------------------------------------------------------------------------------
class Lab:
    def __init__(self, rom: bytes):
        self.rom = rom
        self.o = Oracle(rom)
        self.m = self.o.mem
        self.o.word(0xD168, ROW_TABLE_128)       # ROM-resident row*128 table; the harness table at $D800 collides with object slots 11..18
        self.hdr = [R.header(rom, t)["flags"] for t in range(256)]
        self.cells = rom[CELL_TABLE_FILE:CELL_TABLE_FILE + 1024]
        self.vx = [v for v in static_object(rom)["velocity_tables"]["x_8_8"]]
        self.vy = [v for v in static_object(rom)["velocity_tables"]["y_8_8"]]
        self.base = bytes(self.m[0xC000:0xE000])

    # --- state ---
    def reset(self):
        self.m[0xC000:0xE000] = self.base
        self.o.word(0xD168, ROW_TABLE_128)

    def snapshot(self) -> bytes:
        return bytes(self.m[0xC000:0xE000])

    def restore(self, snap: bytes):
        self.m[0xC000:0xE000] = snap

    def world(self, cells: dict):
        for i in range(4095):
            self.m[LAYOUT_BASE + i] = 0
        for (c, r), b in cells.items():
            self.m[LAYOUT_BASE + r * 128 + c] = b

    def clear_objects(self):
        for a in range(SLOT_BASE, SLOT_BASE + SLOT_COUNT * SLOT_SIZE):
            self.m[a] = 0

    def player(self, x, y, cur=5, req=5, f3=0, f22=2, d523=0, vx=0, vy=0):
        o, m = self.o, self.m
        o.position(x, y)
        o.word(0xD516, vx & 0xFFFF)
        o.word(0xD518, vy & 0xFFFF)
        m[0xD501], m[0xD502], m[0xD503] = cur, req, f3
        m[0xD522], m[0xD523] = f22, d523
        m[0xD3B0] = m[0xD520] = m[0xD3B1] = 0
        m[0xDE04] = 0

    def camera(self, cx, cy):
        self.o.word(0xD174, cx & 0xFFFF)
        self.o.word(0xD176, cy & 0xFFFF)

    def hurt(self):
        self.call_player(HURT_ENTRY)

    def call_player(self, addr, stubs=(0x062D,)):
        """Run an original player-slot routine; the sound engine call of the state-$11 branch returns at once.

        The CPU core also yields at emulated frame boundaries; those stops are simply resumed."""
        o = self.o
        for a in stubs:
            o.cpu.set_breakpoint(a)
        o.cpu.ix, o.cpu.pc, o.cpu.sp = 0xD500, addr, 0xDFE0
        o.word(o.cpu.sp, o.RETURN)
        for _ in range(400):
            o.cpu.ticks_to_stop = 100000
            o.cpu.run()
            if o.cpu.pc == o.RETURN:
                break
            if o.cpu.pc in stubs:
                o.cpu.pc = o.word(o.cpu.sp)
                o.cpu.sp += 2
        else:
            raise RuntimeError(f"routine ${addr:04X} did not return")
        for a in stubs:
            o.cpu.clear_breakpoint(a)

    def step(self):
        self.o.call(SCHEDULER)

    def slot(self, k: int) -> dict:
        a, o, m = SLOT_BASE + k * SLOT_SIZE, self.o, self.m
        return {"k": k, "type": m[a], "state": m[a + 1], "req": m[a + 2], "f3": m[a + 3], "f4": m[a + 4], "frame": m[a + 6],
                "timer": m[a + 7], "x": o.word(a + 0x11), "y": o.word(a + 0x14), "xf": m[a + 0x10], "yf": m[a + 0x13],
                "vx": s16(o.word(a + 0x16)), "vy": s16(o.word(a + 0x18)), "bounce": s16(o.word(a + 0x3C)), "token": m[a + 0x3F]}

    def rings(self) -> list:
        return [self.slot(k) for k in range(SLOT_COUNT) if self.m[SLOT_BASE + k * SLOT_SIZE] == TYPE_RING]

    def player_row(self) -> dict:
        m, o = self.m, self.o
        return {"state": m[0xD501], "req": m[0xD502], "flags": m[0xD503], "x": o.word(0xD511), "y": o.word(0xD514),
                "vx": s16(o.word(0xD516)), "vy": s16(o.word(0xD518)), "rings": m[0xD29A], "lives": m[0xD299],
                "invulnerability": m[0xD3B1], "sound": m[0xDE04], "floor": m[0xD522]}


def lab_age(lab: Lab, passes: int, away=(6000, 600)) -> None:
    """Run `passes` scheduler passes after a spawn. The player stays at its spawn position for pass 0 (the init callback copies it) and is moved away afterwards."""
    for u in range(passes):
        if u:
            lab.o.position(*away)
        lab.step()


def lab_spawn(lab: Lab, rings_bcd: int, px=1000, py=622, cx=None, cy=None, world: dict | None = None, **pk) -> None:
    lab.reset()
    lab.world(world or {})
    lab.clear_objects()
    lab.player(px, py, **pk)
    lab.camera(px - 128 if cx is None else cx, py - 96 if cy is None else cy)
    lab.m[0xD29A] = rings_bcd
    lab.m[0xD299] = 0x03
    lab.hurt()


# ---------------------------------------------------------------------------------------------------------------------
# Emission rules
# ---------------------------------------------------------------------------------------------------------------------
def emission_table(rom: bytes) -> dict:
    lab = Lab(rom)
    rows, mism = {}, 0
    for tens in range(10):
        for units in range(10):
            bcd = tens << 4 | units
            lab_spawn(lab, bcd)
            n = len(lab.rings())
            pr = lab.player_row()
            rings = tens * 10 + units
            rows[str(rings)] = {"bcd": h(bcd, 2), "objects": n, "player_state": pr["req"], "rings_after": pr["rings"],
                                "sound": h(pr["sound"], 2)}
            if n != ring_count_for(bcd):
                mism += 1
    by_n = {}
    for r, v in rows.items():
        by_n.setdefault(v["objects"], []).append(int(r))
    ranges = {str(n): [min(v), max(v)] for n, v in sorted(by_n.items())}
    # A raw (binary) byte such as 0x64 can never be a ring count; the previous audit's row labels used raw bytes (see correction).
    return {"evidence": "CONTROLLED ROUTINE RESULT ($48F7 executed for all 100 valid BCD ring counts) + MODEL",
            "rule": "objects = min(7, tens_digit + 1) for 1..99 rings; 0 rings -> death ($1F), no scatter. $D29A is BCD, so the 'high nibble' is the decimal TENS digit.",
            "decimal_range_per_object_count": ranges, "mismatches_vs_model": mism,
            "rows": rows,
            "correction_of_previous_table": {
                "previous_text": "(rings >> 4) + 1 ... (1, 1, 2, 3, 5, 7 for 1, 15, 16, 32, 64, 100 rings) in docs/platform-spike-collision-audit.md",
                "problem": "those rows fed RAW byte values 15/16/32/64/100 to $D29A; the byte is BCD, so decimal 15/16/32/64 are stored as $15/$16/$32/$64 and emit 2/2/4/7 objects, and 100 cannot exist",
                "corrected": {"1": 1, "9": 1, "10": 2, "15": 2, "16": 2, "19": 2, "20": 3, "32": 4, "47": 5, "59": 6, "60": 7, "64": 7, "99": 7},
                "poc_consequence": "a POC that computes min(7, (rings >> 4) + 1) from a DECIMAL ring count emits 1 object for 15 rings (ROM: 2), 3 for 32 (ROM: 4) and 5 for 64 (ROM: 7)"},
            "recoverable": "each object is worth exactly +1 ring, so at most 7 of the lost rings can be recollected; the other held rings are gone"}


def hurt_rows(rom: bytes) -> dict:
    lab = Lab(rom)
    out = {}
    for name, rings, kw in (("rings_0_death", 0, {}), ("rings_1", 1, {}), ("rings_47", 0x47, {}), ("rings_99", 0x99, {}),
                            ("rings_47_left_wall_d523_bit3", 0x47, {"d523": 8}), ("rings_47_ceiling_d522_bit0", 0x47, {"f22": 1}),
                            ("rings_47_airborne", 0x47, {"f22": 0, "f3": 1}), ("rings_47_state_11", 0x47, {"cur": 0x11, "req": 0x11})):
        lab_spawn(lab, rings, **kw)
        pr = lab.player_row()
        out[name] = {"requested_state": h(pr["req"], 2), "player_flags_d503": h(pr["flags"], 2), "vx": pr["vx"], "vy": pr["vy"],
                     "invulnerability_timer": pr["invulnerability"], "rings_after": h(pr["rings"], 2), "scatter_objects": len(lab.rings()),
                     "sound": h(pr["sound"], 2), "floor_flag_after": bool(pr["floor"] & 2)}
    return {"evidence": "CONTROLLED ROUTINE RESULT ($48F7; state $11 branch calls the sound engine, which the lab runs as plain ROM)", "rows": out,
            "rules": {
                "rings_gt_0": "state $1E, rings := 0, scatter objects, sound $A4, HUD refresh $314A, $D3B1 := $78, +$03 |= $C1, floor flag cleared, vy -4.0 ($FC00; +1.0 when +$22 bit 0), vx -1.0 ($FF00; +1.0 when $D523 bit 3), $D375 := 0",
                "rings_0": "state $1F, vy -5.0 ($FB00), +$04 := 0, no scatter, no invulnerability",
                "state_11": "rings kept (including 0), no scatter, sound $C3, then the ordinary hurt tail ($4942)"}}


# ---------------------------------------------------------------------------------------------------------------------
# Pool / allocation
# ---------------------------------------------------------------------------------------------------------------------
def pool_cases(rom: bytes) -> dict:
    lab = Lab(rom)
    cases = []

    def run(name, occupied: dict, rings=0x99):
        lab_spawn(lab, 0x01)                     # reset world/objects (single ring, then clear)
        lab.clear_objects()
        lab.player(1000, 622)
        for k, t in occupied.items():
            lab.m[SLOT_BASE + k * SLOT_SIZE] = t
        lab.m[0xD29A] = rings
        lab.hurt()
        pr = lab.player_row()
        got = [(r["k"], r["token"]) for r in lab.rings()]
        cases.append({"case": name, "occupied_slots": {str(k): h(t, 2) for k, t in occupied.items()}, "rings_bcd": h(rings, 2),
                      "scatter_slot_token": got, "player_requested_state": h(pr["req"], 2), "rings_after": h(pr["rings"], 2), "sound": h(pr["sound"], 2)})

    run("empty pool, 99 rings", {})
    run("slots 0-2 occupied", {0: 0x21, 1: 0x21, 2: 0x21})
    run("only slots 1 and 3 occupied", {1: 0x21, 3: 0x21})
    run("slots 0-13 occupied (two free in the first 16)", {k: 0x21 for k in range(14)})
    run("slots 0-15 occupied, 16-18 free", {k: 0x21 for k in range(16)})
    run("slot 0 pending clear ($FF) is not reusable", {0: 0xFF})
    run("slot 0 pending clear ($FE) is not reusable", {0: 0xFE})
    run("47 rings, slots 0-3 occupied", {k: 0x21 for k in range(4)}, rings=0x47)
    return {"evidence": "CONTROLLED ROUTINE RESULT ($48F7 with pre-occupied slots)", "pool": "$D540 + 64*k, k = 0..18 are scheduled; only k = 0..15 are allocatable",
            "cases": cases,
            "rules": ["allocator `$5E9C` returns silently when the first 16 slots are full: no object, the loop continues and the hurt still happens",
                      "the token (+$3F, the velocity-table index) is the loop counter H, so a failed allocation never shifts the indices of the rings that did spawn",
                      "slots 16..18 (`$D940`, `$D980`, `$D9C0`) are never used by the scatter",
                      "a slot is free only when its type byte is $00; deleted objects carry $FF/$FE until the scheduler reaches them again, so they cannot be reused in the same update"]}


# ---------------------------------------------------------------------------------------------------------------------
# Model-vs-ROM sweep
# ---------------------------------------------------------------------------------------------------------------------
def _random_world(rng: random.Random, px: int, py: int, density: float, floor_row=None) -> dict:
    cells = {}
    c0, c1 = max(0, (px >> 5) - 14), min(127, (px >> 5) + 14)
    r0, r1 = max(0, (py >> 5) - 8), min(31, (py >> 5) + 12)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if rng.random() < density:
                cells[(c, r)] = rng.randrange(256)
    if floor_row is not None:
        for c in range(c0, c1 + 1):
            cells[(c, floor_row)] = 1
    return cells


def model_vs_rom(rom: bytes, trials=48, updates=420, seed=0x5CA77E8) -> dict:
    lab = Lab(rom)
    rng = random.Random(seed)
    compared = mismatches = pickups_model = pickups_rom = 0
    first = None
    kinds = {"floor_bounce": 0, "ceiling": 0, "bounce_exhausted": 0, "offscreen_delete": 0, "offscreen_bit6": 0, "pickup": 0, "sparkle_end": 0}
    for t in range(trials):
        px, py = rng.randrange(400, 2800), rng.randrange(200, 900)
        cells = _random_world(rng, px, py, rng.choice((0.0, 0.1, 0.3, 0.6)), floor_row=rng.choice((None, (py >> 5) + 1, (py >> 5) + 2, (py >> 5) + 4)))
        bcd = rng.choice((0x05, 0x15, 0x32, 0x47, 0x64, 0x99))
        camx, camy = px - 128 + rng.randrange(-200, 201), py - 96 + rng.randrange(-200, 201)
        away = rng.random() < 0.4
        plx, ply = (px + rng.randrange(-70, 71), py + rng.randrange(-90, 31)) if not away else (6000, 600)
        lab_spawn(lab, bcd, px, py, camx, camy, cells)
        world = World(lab.hdr)
        world.cells = dict(cells)
        n = len(lab.rings())
        models = [RingModel(i, lab.o.word(0xD511), lab.o.word(0xD514), lab.vx, lab.vy) for i in range(n)]
        hud = {"pickups": 0}
        ctr = bcd
        # after hurt the real player is already at the knockback state; the lab pins position, so the model gets the pinned position
        for u in range(updates):
            if u:                                  # the init callback of pass 0 copies the player position, so the player only moves afterwards
                lab.o.position(plx, ply)
            lab.step()
            for mdl in models:
                mdl.update(world, lab.cells, (camx, camy), (plx, ply), hud)
            ctr_model = 0
            for k, mdl in enumerate(models):
                rec = lab.slot(k)
                alive_rom = rec["type"] == TYPE_RING
                compared += 1
                if alive_rom != mdl.alive:
                    ok = False
                elif not alive_rom:
                    ok = True
                else:
                    got = (rec["state"], rec["req"], rec["x"], rec["y"], rec["vx"], rec["vy"], rec["bounce"])
                    ok = got == mdl.snap()
                if not ok:
                    mismatches += 1
                    if first is None:
                        first = {"trial": t, "update": u, "ring": k, "rom": rec, "model": list(mdl.snap()), "model_alive": mdl.alive}
            # BCD ring counter: pickups add +1 each (no wrap in this sweep: start from 0)
        pr = lab.player_row()
        cnt = (pr["rings"] >> 4) * 10 + (pr["rings"] & 15)
        pickups_rom += cnt
        pickups_model += hud["pickups"]
        if cnt != hud["pickups"]:
            mismatches += 1
            first = first or {"trial": t, "counter_rom": cnt, "counter_model": hud["pickups"]}
        for mdl in models:
            for ev, _ in mdl.events:
                key = "floor_bounce" if ev == "bounce" else ev
                if key in kinds:
                    kinds[key] += 1
    return {"evidence": "MODEL vs CONTROLLED ROUTINE RESULT (original scheduler/object code, random worlds)",
            "trials": trials, "updates_per_trial": updates, "ring_updates_compared": compared, "mismatches": mismatches,
            "first_mismatch": first, "pickups_rom": pickups_rom, "pickups_model": pickups_model, "model_event_counts": kinds,
            "fields_compared": "alive, state (+1), requested (+2), x, y, vx, vy, bounce (+3C); ring counter after each trial",
            "world": "random block ids 0..255 (header flags bits 6/7 are the only thing the probe reads), random camera (+-200 px), random player (pinned) near or far"}


# ---------------------------------------------------------------------------------------------------------------------
# Pickup lockout, box, state independence, effects, sparkle
# ---------------------------------------------------------------------------------------------------------------------
def lockout_and_effects(rom: bytes) -> dict:
    lab = Lab(rom)
    out = {"first_pickup_update_by_index": {}, "player_pinned_on_ring_every_update": True}
    for idx in range(7):
        lab_spawn(lab, 0x99, 1000, 622, 872, 526)
        first = None
        for u in range(0, 30):
            r = lab.slot(idx)
            if u >= 1:
                lab.o.position(r["x"], r["y"]) if r["type"] == TYPE_RING else lab.o.position(6000, 600)
            lab.step()
            if lab.slot(idx)["req"] == 2 and first is None:
                first = u
        out["first_pickup_update_by_index"][str(idx)] = first
    out["rule"] = ("U0 is the hurt update (the object phase runs after the player phase, so the scatter objects run their init callback in the same update); "
                   "records 1-4 of state 1 (callback $9A9E) cover U1..U16 without a pickup test; record 5 (callback $9A98) starts at U17")

    # exact box
    lab_spawn(lab, 0x05, 1000, 622, 872, 526)
    lab_age(lab, 20)
    snap = lab.snapshot()
    ring = lab.slot(0)
    grid, mism = {}, 0
    xs = set()
    for dy in range(-14, 15):
        row = ""
        for dx in range(-14, 15):
            lab.restore(snap)
            lab.o.position(ring["x"] + dx, ring["y"] + dy)
            lab.step()
            hit = lab.slot(0)["req"] == 2
            expect = abs(dx) <= 11 and abs(dy) <= 11
            mism += hit != expect
            row += "#" if hit else "."
        grid[str(dy)] = row
        xs.add(row.index("#") - 14 if "#" in row else None)
    out["pickup_box"] = {"evidence": "CONTROLLED ROUTINE RESULT (29 x 29 offsets between ring anchor and player anchor, tested at pass U20)",
                         "ring_anchor": [ring["x"], ring["y"]], "hit_rows_dx_-14_to_14_by_dy": grid, "mismatches_vs_abs_dx_dy_le_11": mism,
                         "rule": "pickup when |ringX - playerX| <= 11 and |ringY - playerY| <= 11 (SBC against 12, strict), both anchors in integer pixels; the player's extents, sprite and state are not read; the test runs BEFORE the ring's own movement in that update"}

    # state independence
    mat = []
    all_hit = True
    for cur in (0x01, 0x05, 0x0A, 0x1E, 0x1F, 0x20):
        for f3 in (0x00, 0x02, 0x40, 0x80, 0xC1):
            for sel in (0, 3, 6):
                lab_spawn(lab, 0x05, 1000, 622, 872, 526)
                lab_age(lab, 17)
                lab.m[0xD501], lab.m[0xD502], lab.m[0xD503], lab.m[0xD532], lab.m[0xD3B1] = cur, cur, f3, sel, 77
                r = lab.slot(0)
                lab.o.position(r["x"], r["y"])
                lab.step()
                hit = lab.slot(0)["req"] == 2
                all_hit &= hit
                mat.append([cur, f3, sel, hit])
    out["player_state_independence"] = {"evidence": "CONTROLLED ROUTINE RESULT (pass U17, player state x $D503 x power selector $D532, invulnerability timer 77)",
                                        "cases": len(mat), "all_collect": all_hit,
                                        "reading": "the dropped-ring pickup does not read the player state, $D503 (hurt bit 6, blink bit 7), the invulnerability timer or $D532; Sonic can recollect while blinking, while in hurt state $1E and while dying ($1F)"}

    # counter effects
    eff = []
    for ctr, lives in ((0x00, 0x03), (0x09, 0x03), (0x19, 0x03), (0x98, 0x03), (0x99, 0x03), (0x99, 0x99)):
        lab_spawn(lab, 0x05, 1000, 622, 872, 526)
        lab_age(lab, 17)
        lab.m[0xD29A], lab.m[0xD299], lab.m[0xDE04] = ctr, lives, 0
        r = lab.slot(0)
        lab.o.position(r["x"], r["y"])
        lab.step()
        eff.append({"rings_before": h(ctr, 2), "lives_before": h(lives, 2), "rings_after": h(lab.m[0xD29A], 2), "lives_after": h(lab.m[0xD299], 2),
                    "sound_after": h(lab.m[0xDE04], 2), "requested_state": lab.slot(0)["req"]})
    out["pickup_effects"] = {"evidence": "CONTROLLED ROUTINE RESULT", "rows": eff,
                             "reading": "+1 BCD ring through $3138 (the same routine as a layout ring); sound $BF; at 99 -> 00 the carry runs $3104 (sound $A9 replaces $BF, lives +1 capped at $99) and $178F"}

    # sparkle timeline
    lab_spawn(lab, 0x05, 1000, 622, 872, 526)
    lab_age(lab, 17)
    r = lab.slot(0)
    lab.o.position(r["x"], r["y"])
    lab.step()
    tl = []
    for n in range(1, 40):
        lab.o.position(6000, 600)
        lab.step()
        s = lab.slot(0)
        tl.append([n, s["type"], s["state"], s["frame"], s["x"], s["y"]])
        if s["type"] == 0:
            break
    out["sparkle_timeline"] = {"evidence": "CONTROLLED ROUTINE RESULT (rows: update after pickup, type, state, frame, x, y)", "rows": tl,
                               "reading": "frozen at the pickup position (no gravity, no velocity); frames 5,6 alternate every 4 updates from pickup+1; type $FE at pickup+29, $FF at +30, slot zero at +31; a ring cannot be collected twice"}
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Flat floor flights and lifetime
# ---------------------------------------------------------------------------------------------------------------------
def flat_floor(rom: bytes) -> dict:
    """Seven rings, solid floor cell top = player anchor + 18 (standing). Two runs: player gone / player standing still at the spawn point."""
    lab = Lab(rom)
    floor = {(c, 20): 1 for c in range(10, 60)}
    out = {"world": "floor row 20 (top y = 640) solid block $01 (header flags $81); player anchor (1000, 622) = floor top - 18; camera (872, 526); spawn y = 606"}
    for label, present in (("player_absent", False), ("player_stands_still_at_spawn_point", True)):
        lab_spawn(lab, 0x99, 1000, 622, 872, 526, floor)
        world = World(lab.hdr)
        world.cells = dict(floor)
        models = [RingModel(i, 1000, 622, lab.vx, lab.vy) for i in range(7)]
        hud = {"pickups": 0}
        series = {i: {"bounces": [], "end": None} for i in range(7)}
        rows = []
        for u in range(700):
            lab.o.position(*((1000, 622) if (present or u == 0) else (6000, 600)))
            lab.step()
            for i, mdl in enumerate(models):
                mdl.update(world, lab.cells, (872, 526), (1000, 622) if present else (6000, 600), hud)
                rec = lab.slot(i)
                if (rec["type"] == TYPE_RING) != mdl.alive:
                    raise RuntimeError("model/ROM divergence in flat_floor")
                if u < 24 and i in (0, 3):
                    rows.append([i, u, rec["x"], rec["y"], rec["vx"], rec["vy"], rec["state"], rec["req"], rec["frame"]])
        for i, mdl in enumerate(models):
            series[i] = {"bounce_updates": mdl.bounces, "end_event": next(((e, a) for e, a in mdl.events if e in ("pickup", "bounce_exhausted", "offscreen_delete", "offscreen_bit6")), None)}
        out[label] = {"per_ring": {str(i): series[i] for i in range(7)}, "first_24_updates_rings_0_and_3": rows}
    # bounce speed list
    out["bounce_speed_sequence_8_8"] = [-1024 + 128 * k for k in range(1, 8)]
    out["bounce_speed_sequence_px"] = [(-1024 + 128 * k) / 256 for k in range(1, 8)]
    out["bounce_rule"] = "+$3C starts at $FC00; each floor contact adds $0080 and (if no carry) becomes the new Y speed: -3.5, -3.0, -2.5, -2.0, -1.5, -1.0, -0.5; the 8th contact carries out of 16 bits and the ring is deleted ($FF) with no sparkle"
    return out


def ceiling_and_oneway(rom: bytes) -> dict:
    lab = Lab(rom)
    rows = []
    for name, blk in (("solid $01 (flags $81)", 1), ("one-way $0D (flags $41)", 0x0D), ("ring block $40 (flags $07)", 0x40), ("air $00", 0)):
        cells = {(c, 18): blk for c in range(10, 60)}
        # ceiling row 18 bottom = 608; ring spawns at 606 rising: probe y+2 enters row 19 only after crossing 608 -> use ceiling at row 17 (bottom 576)
        cells = {(c, 17): blk for c in range(10, 60)}
        lab_spawn(lab, 0x05, 1000, 622, 872, 526, cells)
        world = World(lab.hdr)
        world.cells = dict(cells)
        m = RingModel(0, 1000, 622, lab.vx, lab.vy)
        hud = {"pickups": 0}
        first_flip = None
        for u in range(60):
            if u:
                lab.o.position(6000, 600)
            lab.step()
            m.update(world, lab.cells, (872, 526), (6000, 600), hud)
            rec = lab.slot(0)
            if rec["type"] == TYPE_RING and (rec["state"], rec["req"], rec["x"], rec["y"], rec["vx"], rec["vy"], rec["bounce"]) != m.snap():
                raise RuntimeError("model/ROM divergence in ceiling_and_oneway")
            if first_flip is None and rec["type"] == TYPE_RING and rec["vy"] > 0 and u > 0:
                first_flip = {"update": u, "y": rec["y"], "vy": rec["vy"]}
        rows.append({"block": name, "ring_turns_around": first_flip})
    return {"evidence": "CONTROLLED ROUTINE RESULT + MODEL", "ceiling_row_17_bottom_y": 576, "rows": rows,
            "rule": "the ceiling probe (anchor Y + 2) tests ONLY header flag bit 7 (solid) of the 32x32 block cell and reverses a rising ring (vy := -vy, bounce count unchanged); one-way cells (bit 6), ring blocks and air do not stop it, so a ring passes UP through one-way platforms and lands on them (the floor probe accepts bit 6 or 7); height profiles and slopes are ignored"}


# ---------------------------------------------------------------------------------------------------------------------
# Lifetime window ($61E1)
# ---------------------------------------------------------------------------------------------------------------------
def lifetime_window(rom: bytes) -> dict:
    lab = Lab(rom)
    cells = lab.cells
    mism, total = 0, 0
    rng = random.Random(61)
    pts = [(dx, 96) for dx in range(-150, 420)] + [(128, dy) for dy in range(-150, 420)]
    pts += [(rng.randrange(-150, 420), rng.randrange(-150, 420)) for _ in range(2500)]
    camx, camy = 1000, 500
    classes_x, classes_y = {}, {}
    for dx, dy in pts:
        x, y = camx + dx, camy + dy
        lab.reset()
        lab.clear_objects()
        a = SLOT_BASE
        lab.m[a], lab.m[a + 1], lab.m[a + 4] = TYPE_RING, 1, 1
        lab.o.word(a + 0x11, x)
        lab.o.word(a + 0x14, y)
        lab.camera(camx, camy)
        lab.o.cpu.ix = a
        lab.o.call(0x61E1)
        deleted = lab.m[a] in (0xFF, 0xFE)
        bit6 = bool(lab.m[a + 4] & 0x40)
        got = "delete" if deleted else ("asleep" if bit6 else "active")
        exp = lifetime_class(cells, x, y, camx, camy)
        total += 1
        mism += got != exp
        if dy == 96 and -150 <= dx < 420:
            classes_x[dx] = got
        if dx == 128 and -150 <= dy < 420:
            classes_y[dy] = got

    def runs(d):
        out, prev, start = [], None, None
        for k in sorted(d):
            if d[k] != prev:
                if prev is not None:
                    out.append([prev, start, last])
                prev, start = d[k], k
            last = k
        out.append([prev, start, last])
        return out
    return {"evidence": "CONTROLLED ROUTINE RESULT ($61E1 executed for 3,640 anchor offsets) + DECODED DATA (cell table)",
            "cases": total, "mismatches_vs_model": mism, "camera": [camx, camy],
            "horizontal_runs_dx_at_dy_96": runs(classes_x), "vertical_runs_dy_at_dx_128": runs(classes_y),
            "cell_table": ["".join(str(c) for c in cells[r * 32:(r + 1) * 32]) for r in range(32)],
            "rule": ("distance d = anchor - camera (X: camera $D174, Y: camera $D176); the table has 32 x 32 cells of 16 px starting at d = -128; cell 3 or d outside [-128, 384) deletes at once; "
                     "cells 0/1 are active; cell 2 sets bit 6 (+$04) which the ring's own callback turns into deletion on the NEXT update (rings never sleep). Net effect for a ring: it is removed one update after "
                     "its anchor leaves the active cells (SMS: X in [camX - 32, camX + 288), Y band analogous); a widescreen adapter must widen the horizontal active band with the displayed width ("
                     "docs/viewport-semantics-audit.md), it is a lifecycle constant, not part of the ring physics"),
            "state_0_exemption": "the creation update (state 0) does not run $61E1"}


# ---------------------------------------------------------------------------------------------------------------------
# Water, invulnerability interplay
# ---------------------------------------------------------------------------------------------------------------------
def second_hurt(rom: bytes) -> dict:
    """A second damage request while scatter objects exist: the gate `$48BC` is run once per update before the object phase."""
    lab = Lab(rom)
    floor = {(c, 20): 1 for c in range(10, 60)}
    lab_spawn(lab, 0x47, 1000, 622, 872, 526, floor)
    events, cleared, new_hurt = [], None, None
    for p in range(1, 260):
        lab.o.position(6000, 600) if p > 1 else None
        if p == 10:
            lab.m[0xD29A], lab.m[0xD3B0] = 0x05, 0xFF
        lab.call_player(HURT_GATE)
        if p == 10:
            events.append({"pass": p, "what": "request while invulnerable", "d3b0_after": lab.m[0xD3B0], "rings_after": h(lab.m[0xD29A], 2),
                           "invulnerability_timer": lab.m[0xD3B1], "scatter_objects": len(lab.rings()), "player_flags": h(lab.m[0xD503], 2)})
        if cleared is None and not (lab.m[0xD503] & 0x80):
            cleared = p
            events.append({"pass": p, "what": "invulnerability bits cleared by the gate", "player_flags": h(lab.m[0xD503], 2), "d3b1": lab.m[0xD3B1]})
            lab.m[0xD3B0], lab.m[0xD29A] = 0xFF, 0x05
            lab.m[0xD522] = 2
        elif cleared is not None and new_hurt is None and p == cleared + 1:
            new_hurt = p
            events.append({"pass": p, "what": "request after invulnerability", "requested_state": h(lab.m[0xD502], 2), "rings_after": h(lab.m[0xD29A], 2),
                           "scatter_slots": [(r["k"], r["token"], r["state"]) for r in lab.rings()], "invulnerability_timer": lab.m[0xD3B1]})
        lab.step()
    return {"evidence": "CONTROLLED ROUTINE RESULT ($48BC once per update, then the object phase)", "events": events,
            "reading": ["a request while +$03 bit 7 is set stays pending ($D3B0 = $FF) but is not acted on ($48BC jumps to the countdown $49F7): no new rings, ring counter untouched; the countdown end ($4A19) clears +$03 bits 7/6 and zeroes $D3B0, discarding it",
                        "after the countdown a fresh request hurts again (set explicitly in this fixture); the scatter objects of the first hurt keep running and the new ones take the next free slots (tokens restart at 0)"]}


def invulnerability_blink(rom: bytes) -> dict:
    """Player blink (not the rings): +$04 bit 7 follows $D3B1 bit 1 during the countdown, except in state $1E."""
    lab = Lab(rom)
    out = {}
    for cur in (0x1E, 0x05):
        lab_spawn(lab, 0x05, 1000, 622, 872, 526)
        lab.m[0xD501] = cur
        seq = []
        for p in range(1, 125):
            lab.call_player(HURT_GATE)
            seq.append([lab.m[0xD3B1], int(bool(lab.m[0xD504] & 0x80)), int(bool(lab.m[0xD503] & 0x80))])
        runs, prev, n = [], None, 0
        for _, hid, _inv in seq:
            if hid != prev:
                if prev is not None:
                    runs.append([prev, n])
                prev, n = hid, 0
            n += 1
        runs.append([prev, n])
        out[f"current_state_{cur:02X}"] = {"hidden_run_lengths_[hidden, updates]": runs[:12], "d3b1_first_last": [seq[0][0], seq[-1][0]],
                                           "invulnerable_bit_cleared_at_gate": next((i + 1 for i, s in enumerate(seq) if not s[2]), None)}
    return {"evidence": "CONTROLLED ROUTINE RESULT ($48BC once per update after a hurt; +$04 bit 7 = player sprite hidden)", "rows": out,
            "reading": "the countdown $D3B1 runs 119..0 once per gate update; while the player's current state is not $1E the sprite is hidden when bit 1 of the decremented counter is set (period 4: two updates hidden, two visible); the invulnerable flag (+$03 bit 7) is cleared at the 121st gate update"}






def water_equivalence(rom: bytes) -> dict:
    lab = Lab(rom)
    runs = []
    floor = {(c, 20): 1 for c in range(10, 60)}
    for water in (0, 1):
        lab_spawn(lab, 0x47, 1000, 622, 872, 526, floor)
        lab.m[0xD443] = water
        tr = [lab.player_row()]
        for u in range(300):
            lab.m[0xD443] = water
            lab.o.position(1000, 622)
            lab.step()
            tr.append([[r["x"], r["y"], r["vx"], r["vy"], r["state"]] for r in lab.rings()])
        runs.append(tr)
    return {"evidence": "CONTROLLED ROUTINE RESULT ($D443 = 0 vs 1 through hurt + 300 scheduler passes) + BYTE-VERIFIED ASSEMBLY (operand scan)",
            "identical": runs[0] == runs[1],
            "reading": "neither the hurt routine nor the scatter object reads the water condition $D443; gravity ($20), velocities, bounce and pickup are identical underwater"}


# ---------------------------------------------------------------------------------------------------------------------
# Part D - GPZ3 boss example (whole game)
# ---------------------------------------------------------------------------------------------------------------------
def gpz3_example(rom: bytes, updates=150) -> dict:
    import gpz51_fullgame as G
    import platform_spike_collision as P
    from thz3_boss_support import Aligned

    out = {}
    for label, take in (("natural_no_recollect", None), ("player_teleports_onto_ring_0_at_k40", 40)):
        s = G.boot(rom)
        m, u = s.mem, s.u16
        e = P.Emu.__new__(P.Emu)
        e.s, e.rom, e.act = s, rom, "gpz3"
        al = Aligned(e)
        state = {"release": None, "log": [], "hurt": None, "pick": None}

        def boss():
            return next((b for b in range(0xD540, 0xDA00, 64) if m[b] == 81 and m[b + 63] == 0), None)

        def park(x, y, flags=0, st=5):
            s.w16(0xD511, x)
            s.w16(0xD514, y)
            s.w16(0xD516, 0)
            s.w16(0xD518, 0)
            m[0xD502], m[0xD503], m[0xD3B1], m[0xD522] = st, flags, 0, 2

        def driver(t):
            b = boss()
            if state["release"] is None:
                if b is None:
                    return
                st = m[b + 1]
                if t >= 630 and st == 7:
                    ball = next(a for a in range(0xD540, 0xDA00, 64) if m[a] == 81 and m[a + 1] == 11)
                    state["release"] = t
                    state["ball"] = [u(ball + 17), u(ball + 20)]
                    park(u(ball + 17) - 10, 266)
                    m[0xD29A] = 0x47
                elif st == 0:
                    park(1760, 238)
                elif st == 14:
                    park(1760, 270)
                else:
                    park(1680, 270)
                return
            k = t - state["release"]
            if take is not None and k == take:
                ring0 = next((a for a in range(0xD540, 0xDA00, 64) if m[a] == TYPE_RING and m[a + 63] == 0), None)
                if ring0 is not None:
                    s.w16(0xD511, u(ring0 + 17))
                    s.w16(0xD514, u(ring0 + 20))
                    state["pick"] = {"k": k, "ring0": [u(ring0 + 17), u(ring0 + 20)], "rings_before": m[0xD29A], "player_state": m[0xD501], "invulnerability": m[0xD3B1], "flags": m[0xD503]}
            rings = []
            for a in range(0xD540, 0xDA00, 64):
                if m[a] == TYPE_RING:
                    rings.append([m[a + 63], (a - 0xD540) // 64, m[a + 1], m[a + 2], u(a + 17), u(a + 20), s16(u(a + 22)), s16(u(a + 24)), s16(u(a + 0x3C)), m[a + 6]])
            state["log"].append({"k": k, "player": [u(0xD511), u(0xD514), s16(u(0xD516)), s16(u(0xD518)), m[0xD501], m[0xD502], m[0xD503], m[0xD3B1], m[0xD29A], m[0xD299], m[0xDE04]],
                                 "camera": [u(0xD174), u(0xD176)], "rings": rings})

        al.run(driver, lambda: {}, 1500, pad=lambda t: 8 if t < 75 else 0, restore=False,
               stop=lambda rows: state["release"] is not None and len(state["log"]) > updates)
        log = state["log"][:updates]
        out[label] = {"release_update": state["release"], "ball_anchor": state.get("ball"), "pick": state["pick"], "rows": log}
    return out


def summarise_gpz3(ex: dict) -> dict:
    nat = ex["natural_no_recollect"]["rows"]
    pick = ex["player_teleports_onto_ring_0_at_k40"]["rows"]

    def tokens(rows):
        d = {}
        for r in rows:
            for t in r["rings"]:
                d.setdefault(t[0], []).append(r["k"])
        return {str(t): [min(v), max(v)] for t, v in sorted(d.items())}
    first, last = nat[0], nat[-1]
    return {"hurt_update_k": 1, "rings_before": "0x47 (47 rings)", "objects_emitted": len(nat[1]["rings"]) if len(nat) > 1 else 0,
            "natural_lifespans_k_first_last": tokens(nat), "after_pick_lifespans_k_first_last": tokens(pick),
            "rings_counter_after_pick": [r["player"][8] for r in pick if r["k"] in (39, 40, 41, 42)]}


# ---------------------------------------------------------------------------------------------------------------------
# POC read-only diagnosis (static text; the POC is never modified)
# ---------------------------------------------------------------------------------------------------------------------
POC_DIVERGENCE = {
    "evidence": "POC SOURCE (READ-ONLY, SonicChaos_POC_thz1_cleanup @ 84c3e10 working tree)",
    "observed": [
        "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml SCR_chaos_hurt_apply: `if (cp_c.hurt_scatter > 0) instance_create(cp_p.x,cp_p.y,OBJ_player_lost_b);` creates exactly ONE legacy decorative object regardless of hurt_scatter",
        "objects/OBJ_player_lost_b: alpha 0.6, alarm[0] = 80 (destroyed after 80 steps), vspeed -8, gravity 0.4 capped at 12, blink alarms 4 steps, Alarm_3 sets global.ring := 0; no floor/ceiling probe, no bounce, no pickup, no velocity table",
        "scripts/SCR_chaos_core/SCR_chaos_core.gml: hurt_scatter = min(7, (rings >> 4) + 1) uses the decimal count; the ROM uses the BCD tens digit",
    ],
    "matches_user_symptom": "rings are lost visually, fade within ~1.3 s and cannot be recollected: consistent with a single non-collectable decoration",
}


# ---------------------------------------------------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------------------------------------------------
IMPLEMENTATION_SUMMARY = {
    "emission": "on hurt with rings > 0 (not state $11): N = min(7, tensDigit(BCD rings) + 1); rings := 0; for H = 0..N-1 allocate the first free slot of the first 16 (type $06, token H); sound $A4; HUD refresh; invulnerability $78; state $1E; knockback vy -4.0, vx -1.0",
    "spawn": "init pass in the hurt update: X = playerX, Y = playerY - 16, vx = X[H], vy = Y[H], bounce = -4.0, flags +03 = $C0, request state 1; no lifetime test in that pass",
    "x_velocity_8_8_by_index": [0, -320, 320, -640, 640, -832, 832],
    "y_velocity_8_8_by_index": [-1280, -1184, -1184, -896, -896, -512, -512],
    "per_update_state1": "[pickup test if pass >= 17] ; vy += 0x20 ; x += vx ; y += vy (24-bit fixed point) ; if vy < 0 and solid(x, y+2) [header bit 7] then vy := -vy ; if vy >= 0 and floor(x, y+18) [header bit 6 or 7] then bounce += 0x80, delete if it carries else vy := bounce ; delete if bit 6 (set by the previous $61E1)",
    "flag_probe": "block = layout[(py+bias) >> 5][x >> 5]; floor probe: header byte 0 bit 7 (solid) or bit 6 (one-way); ceiling probe: bit 7 only; no height profile",
    "pickup": "pass >= 17 and |dx| <= 11 and |dy| <= 11 versus the player anchor; no player-state condition; +1 BCD ring via $3138, sound $BF, ring freezes and plays sparkle frames 5/6 for 28 updates",
    "lifetime": "no timer and no blink: ends at the 8th floor contact (after bounces of -3.5 .. -0.5), at off-screen removal, or by pickup",
}

ADAPTER_NOTES = [
    "Times are object-phase updates (one per game frame). Do not convert to seconds without fixing the display rate.",
    "Presentation: the ring sprite frames come from mapping table `$3C00C` (frames 1-4 flight animation, 5/6 pickup sparkle; draw extents (8,16) / (4,16) are draw boxes and are not used by the pickup test). The sprite anchor offset was not studied here: UNRESOLVED, reuse the accepted type-$09 ring presentation only after checking it against these frames.",
    "Lifecycle: the removal band is camera-relative on BOTH axes ([-32, 288) active, 256-wide SMS view). It is a lifecycle constant: for widescreen derive it from the displayed width as in docs/viewport-semantics-audit.md instead of letting rings die at the old SMS edge or live forever.",
    "Collision: the canonical probes read the block-level header flag at two points only; a POC that substitutes pixel/mask collision will differ on slopes and thin platforms. If a GameMaker adapter must use its own solid test, keep the same two probe points (y+18 falling, y+2 rising) and the one-way rule (landable, not blocking upward).",
    "Ring count: convert the POC's decimal ring count to the ROM rule min(7, tens + 1); never `rings >> 4`.",
    "No alpha fade, no blink and no timer on the lost rings; the player blink (2 updates hidden / 2 visible, 120 updates, none in state $1E) is a separate mechanism.",
    "The recollect pickup must be independent of the player's hurt/invulnerable/dying state and must run before the ring's own movement in the same update.",
]

AGENTS_CANDIDATES = [
    "Player hurt with rings (`$48F7`) is shared by every damage source: `N = min(7, tens digit of BCD $D29A + 1)` type-`$06` objects, ring counter := 0, sound `$A4`, invulnerability `$78`, state `$1E`. `$D29A` is BCD: decimal 15/32/64 rings emit 2/4/7 objects, not 1/3/5 (the old `rings >> 4` table used raw bytes).",
    "A lost ring (type `$06`) is a real collectable: velocities by index X `{0,-1.25,+1.25,-2.5,+2.5,-3.25,+3.25}`, Y `{-5.0,-4.625,-4.625,-3.5,-3.5,-2.0,-2.0}` px/update, gravity +0.125/update with no terminal cap, anchor spawn (playerX, playerY-16), no pickup for 16 updates after the hurt update (first test on the 17th pass), pickup box |dx|,|dy| <= 11 against the player anchor, independent of player/hurt/invulnerability state, +1 ring through the same `$3138` as layout rings, sparkle frames 5/6 for 28 updates.",
    "Lost rings bounce on a coarse 32x32 block flag test (header bit 6 or 7 at (x, y+18) when vy >= 0; header bit 7 at (x, y+2) when vy < 0 reverses vy) with bounce speeds -3.5 .. -0.5 (+0.5 per contact); the 8th floor contact deletes the ring. There is no timer and no flashing; the only other removals are off-screen (`$61E1`, one update later for the ring's own bit-6 check) and pickup. Allocation uses only the first 16 of the 19 object slots and fails silently.",
    "Never substitute the legacy decorative `OBJ_player_lost_b` (alpha, 80-step alarm, no collision) for the canonical scatter object.",
]


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    data = {
        "format": 1,
        "rom_sha256": ROM_SHA256,
        "evidence_classes": ["DECODED DATA", "BYTE-VERIFIED ASSEMBLY", "SOURCE-TRACED BEHAVIOR", "CONTROLLED ROUTINE RESULT", "EMULATED ORIGINAL FRAME", "MODEL", "POC SOURCE (READ-ONLY)", "UNRESOLVED"],
        "ram": {k: h(v) for k, v in RAM.items()},
        "routines": static_routines(rom),
        "vectors": static_vectors(rom),
        "object": static_object(rom),
        "shared_counter_path": static_shared_paths(rom),
        "water": {"static": water_scan(rom)},
        "implementation_summary": IMPLEMENTATION_SUMMARY,
        "poc_divergence": POC_DIVERGENCE,
        "adapter_notes": ADAPTER_NOTES,
        "agents_candidate_updates": AGENTS_CANDIDATES,
        "unresolved": [
            "whether the sprite renderer draws an object whose type is $FE (the last update of a sparkle, callback $034A) - at most one frame, presentation only",
            "SMS sprite-per-scanline flicker of up to 7 rings + player + enemies is a renderer property, not object logic; no ring blink exists in the object code",
        ],
    }
    if static_only:
        return data
    data["emission"] = emission_table(rom)
    data["hurt_rows"] = hurt_rows(rom)
    data["pool"] = pool_cases(rom)
    data["lockout_pickup"] = lockout_and_effects(rom)
    data["flat_floor"] = flat_floor(rom)
    data["ceiling_and_oneway"] = ceiling_and_oneway(rom)
    data["lifetime_window"] = lifetime_window(rom)
    data["water"]["controlled"] = water_equivalence(rom)
    data["second_hurt"] = second_hurt(rom)
    data["invulnerability_blink"] = invulnerability_blink(rom)
    data["model_vs_rom"] = model_vs_rom(rom)
    gp = gpz3_example(rom)
    data["gpz3_boss_example"] = {"evidence": "EMULATED ORIGINAL FRAME (whole GPZ3 game, update aligned; synthetic placement of Sonic at the detached boss ball with 47 rings; the trace stops 150 updates after the hurt, before Sonic (0 rings, standing in the ball's lane) is hit again)",
                                 "summary": summarise_gpz3(gp), **gp}
    return data


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    a = ap.parse_args()
    rom = R.load(a.rom)
    data = build(rom, static_only=a.static_only)
    text = json.dumps(data, indent=1, sort_keys=False) + "\n"
    if a.static_only:
        print("static facts OK:", len(data["routines"]), "routines")
        return
    if a.check:
        assert OUTPUT.read_text(encoding="utf-8") == text, "player-hurt-ring-scatter cache differs"
        print("cache verified:", OUTPUT.name)
    else:
        OUTPUT.write_text(text, encoding="utf-8")
        print("wrote", OUTPUT.relative_to(ROOT), len(text), "bytes")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Viewport-relative semantics audit (research only, deterministic).

What the original ROM expresses relative to the camera / screen edge / spawn window, as opposed to
world space. Output: data/rom-cache/viewport-semantics.json (numeric labels only, no ROM bytes beyond
16-byte routine heads).

Evidence classes (same vocabulary as the earlier studies):
  DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT (original Z80
  routines executed with explicit RAM, tools/oracle.py), EMULATED ORIGINAL FRAME (tools/sms_frame_harness.py),
  UNRESOLVED.

Coordinate vocabulary used below (all ROM-derived):
  cam      = camera X ($D174): world X of screen column 0 of the original 256-px scroll window
  RIGHT    = cam + 256        (exclusive right edge of the original window)
  d        = x - cam          (screen-relative X of a world X)

Usage:
  python tools/viewport_semantics.py ROM.sms            # write the cache
  python tools/viewport_semantics.py ROM.sms --check    # compare with the cache
  python tools/viewport_semantics.py ROM.sms --static-only
  python tools/viewport_semantics.py --markdown         # print the constants table from the cache
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OUTPUT = ROOT / "data" / "rom-cache" / "viewport-semantics.json"

VIEW_W = 256                 # original scroll window width (pixels)
SPAWN_MAP_ROM = 0x70146      # bank $1C CPU $8146, 32x32 bytes
SPAWN_MAP_SIDE = 32
CELL = 16                    # pixels per spawn-map cell

# Synthetic camera positions used by every sweep (not level locations). Includes values around 8-bit
# and 16-bit boundaries and the THZ1 sign camera (3831) so a rule that only fits one place cannot pass.
CAMERAS = [0, 1, 7, 8, 127, 128, 255, 256, 257, 511, 512, 1000, 1337, 2047, 2048, 3831, 3839, 3840, 4095, 5000, 8000, 16000]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def u16(rom: bytes, pos: int) -> int:
    return rom[pos] | (rom[pos + 1] << 8)


def s16(v: int) -> int:
    return v - 65536 if v >= 32768 else v


def rom_of(bank: int, cpu: int) -> int:
    return cpu if cpu < 0x8000 else bank * 0x4000 + cpu - 0x8000


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


EVIDENCE = {
    "DECODED DATA": "ROM tables/records decoded by a parser",
    "BYTE-VERIFIED ASSEMBLY": "routine bytes compared literally and disassembled by hand",
    "SOURCE-TRACED BEHAVIOR": "behavior read from the disassembly, not executed",
    "CONTROLLED ROUTINE RESULT": "original routine executed on a Z80 core with explicit RAM, swept over synthetic cameras",
    "EMULATED ORIGINAL FRAME": "whole original game run in the approximate SMS harness",
    "UNRESOLVED": "not established",
}

CLASSES = {
    "A": "WORLD-SPACE (canonical placement, terrain, level geometry, level limits)",
    "B": "CAMERA-RELATIVE (a function of camera position or camera motion, not of the screen width)",
    "C": "SCREEN-EDGE-RELATIVE (an offset from the left/right/centre of the original 256-px window)",
    "D": "VIEWPORT/SPAWN-WINDOW-RELATIVE (create/sleep/delete bands around the camera window)",
    "E": "PRESENTATION-ONLY (VDP register or sprite/scroll output)",
    "F": "UNRESOLVED",
    "G": "PLAYER-RELATIVE WORLD DISTANCE (added by this audit: neither camera nor screen)",
}


# --------------------------------------------------------------------------- #
# 1. routines (byte-verified regions)
# --------------------------------------------------------------------------- #
# (name, bank, first CPU, end CPU exclusive, purpose)
ROUTINES = [
    ("frame_update", 0, 0x16B8, 0x16EF, "per-frame order: camera $4C90, player $361D, objects $5DD1, $7AC2, placement scan every 4th update"),
    ("camera_update", 1, 0x4C90, 0x4CB0, "camera update entry (needs $D15E bit 7), calls follow, limits, VDP scroll prep"),
    ("camera_limit_x", 1, 0x4CB0, 0x4CF7, "horizontal limit clamp: left inclusive ($D280), right exclusive ($D282)"),
    ("camera_limit_y", 1, 0x4CF7, 0x4D3E, "vertical limit clamp: top ($D27C), bottom ($D27E)"),
    ("camera_to_vdp", 1, 0x4D3E, 0x4D5D, "R8 = -(cam+1), R9 = (camY+17) mod 224 into $D172/$D173"),
    ("vblank_camera_commit", 0, 0x0570, 0x057C, "$D174/$D176 := $D284/$D286 at the vblank handler"),
    ("camera_follow", 1, 0x5832, 0x5935, "follow: dead zone around player screen X/Y target, pan branch, per-axis step"),
    ("camera_follow_init", 1, 0x5935, 0x5956, "copy target offsets into the working registers"),
    ("camera_pan", 1, 0x5956, 0x59B3, "pan to ($D2DA,$D2DC), 1 px per update per axis, limit update"),
    ("camera_vectors", 1, 0x59B3, 0x5A03, "$042B enable, $0407 freeze, $0359 pan on, $035C pan off, $0353 left lock, $0356 right lock"),
    ("level_header_loader", 1, 0x4FDC, 0x5082, "act header -> camera limits $D280/$D27C/$D282/$D27E, follow targets $D288/$D289"),
    ("player_edge_clamp_a", 1, 0x4141, 0x4169, "player X clamp to [cam+16, cam+247] for states < $29 (low byte of playerX-cam)"),
    ("player_edge_clamp_snap", 1, 0x4244, 0x4281, "snap to bound, subtract this update's X speed, clear X speed"),
    ("player_edge_clamp_b", 1, 0x4281, 0x429D, "same clamp, entry used by the $39xx state handlers"),
    ("player_input_step", 0, 0x3FEF, 0x4010, "shared player step ($0404) that calls the clamp"),
    ("object_lifetime", 1, 0x61E1, 0x6276, "post-update visibility/lifetime: spawn-map band test"),
    ("player_distance_helpers", 1, 0x61A5, 0x61D6, "$0383 horizontal / $0386 vertical |object - player| < BC -> $FF"),
    ("placement_scan", 0x1C, 0x8000, 0x8146, "placement scan: same window and map as the lifetime routine"),
    ("screen_coordinate_prep", 0, 0x3FC8, 0x3FEF, "+$1A/+$1C = anchor - camera (screen X/Y, 16-bit)"),
    ("player_pit_screen_y", 0, 0x3BFB, 0x3C15, "player screen Y ($D51C) >= $D8 sets $D293 bit 2"),
    ("vdp_register_init", 0, 0x1D2D, 0x1D33, "R0=$26, R1=$82 (R1 becomes $E2 at runtime), R5=$FF, R6=$FF/$FB"),
    ("player_state20_handler", 0x0C, 0x83A6, 0x840F, "run right; camera freeze above $F8; flag above $120"),
    ("goal_sign_camera_pan", 0x0C, 0xAA22, 0xAA47, "pan target (signX-$80, signY-$99) through $0359"),
    ("child19_init_and_scroll", 0x0C, 0xAA87, 0xAB0A, "type $19: X = cam+$104, Y = camY+$50, moves left 8/update to cam+$85"),
    ("type28_persistence_removal", 0x1E, 0x8908, 0x8925, "type $28 with +$04 bit 1: removed at |dx| >= $280 or |dy| >= $2A0 from the player"),
    ("type27_state1_proximity", 0x1E, 0x89AC, 0x89DF, "type $27 state 1: |dx| < $40 from the player"),
    ("type27_state3_removal", 0x1E, 0x8A29, 0x8A45, "type $27 state 3: |dx| >= $180 from the player"),
    ("boss_trigger_and_pan", 0x1E, 0x9771, 0x97A1, "type $50 state 1/2: player distance trigger and camera pan target"),
    ("boss_patrol_screen_x", 0x1E, 0x9866, 0x988E, "type $50 states 6/12: screen X thresholds $38 / $C8"),
]


def routine_table(rom: bytes) -> list[dict]:
    out = []
    for name, bank, a, z, purpose in ROUTINES:
        o, e = rom_of(bank, a), rom_of(bank, z)
        out.append({"name": name, "bank": bank, "cpu_start": h(a), "cpu_end_exclusive": h(z), "rom_offset": h(o, 5),
                    "length": e - o, "sha256": sha(rom[o:e]), "first_16_bytes": rom[o:o + 16].hex(), "purpose": purpose})
    return out


# --------------------------------------------------------------------------- #
# 2. pure models (used by the tool, the cache and the tests)
# --------------------------------------------------------------------------- #
def band(d: int) -> int:
    """Per-axis band of a screen-relative offset d = world - camera for the lifetime/placement window.
    0 = inside the 256-px view, 1 = within 32 px outside it, 2 = 32..96 px outside, 3 = deletion zone."""
    w = d + 128
    if w < 0 or w >= 512:
        return 3
    u = w >> 4
    if 8 <= u <= 23:
        return 0
    if u in (6, 7, 24, 25):
        return 1
    if 2 <= u <= 5 or 26 <= u <= 29:
        return 2
    return 3


def cell(dx: int, dy: int) -> int:
    return max(band(dx), band(dy))


def lifetime_outcome(dx: int, dy: int, keepalive: bool, token: bool) -> tuple[str, int]:
    """(outcome, bit6) of routine $61E1 for an object at screen-relative (dx, dy)."""
    c = cell(dx, dy)
    if c <= 1:
        return "active", 0
    if c == 2:
        return "asleep", 1
    if keepalive:
        return "asleep", 1
    return ("remove_tracked" if token else "remove_untracked"), 1


def scan_creates(dx: int, dy: int, initial_fill: bool) -> bool:
    """Placement scan $8000: does a record with an empty occupancy byte get created?"""
    c = cell(dx, dy)
    return c == 2 or (c <= 1 and initial_fill)


def clamp_bound(d: int) -> str | None:
    """Player edge clamp: uses the LOW BYTE of d (8-bit wrap)."""
    low = d & 0xFF
    if low < 0x10:
        return "left"
    if low >= 0xF8:
        return "right"
    return None


def state20_flag(d: int) -> bool:
    """$83A6: act-clear flag set when (playerX - cameraX) as unsigned 16-bit > $120."""
    return (d & 0xFFFF) > 0x120


def state20_camera_freeze(d: int) -> bool:
    return (d & 0xFFFF) > 0xF8


def follow_delta_x(k: int, d28a: int) -> int:
    """Camera step from the follow routine $5832: k = low byte of (playerX - target); d28a = current lead."""
    lo, hi = (d28a - 8) & 0xFF, (d28a + 8) & 0xFF
    k &= 0xFF
    if k < d28a:
        if k >= lo:
            return 0
        sub = (k - lo) & 0xFF
        return sub - 256 if sub >= 0xF8 else -7
    if k < hi:
        return 0
    sub = (k - hi) & 0xFF
    return sub if sub < 8 else 7


def limit_x_delta(cam: int, delta: int, left_limit: int, right_limit: int) -> int:
    """$4CB0: a scroll step is dropped (camera stays) when it would leave [left, right)."""
    if delta < 0:
        t = cam + delta
        return 0 if t < left_limit or t < 0 else delta
    if delta > 0:
        return 0 if cam + delta >= right_limit else delta
    return 0


# --------------------------------------------------------------------------- #
# 3. static facts
# --------------------------------------------------------------------------- #
def spawn_map(rom: bytes) -> dict:
    m = rom[SPAWN_MAP_ROM:SPAWN_MAP_ROM + SPAWN_MAP_SIDE * SPAWN_MAP_SIDE]
    closed_form = all(m[r * 32 + c] == max(band((c << 4) - 128), band((r << 4) - 128)) for r in range(32) for c in range(32))
    rows = ["".join(str(v) for v in m[r * 32:(r + 1) * 32]) for r in range(32)]
    counts = {str(v): m.count(v) for v in sorted(set(m))}
    bands = []
    for b in range(4):
        spans = []
        start = None
        for d in range(-130, 390):
            inside = band(d) == b
            if inside and start is None:
                start = d
            if not inside and start is not None:
                spans.append([start, d])
                start = None
        if start is not None:
            spans.append([start, 390])
        bands.append({"band": b, "screen_relative_spans_half_open": spans})
    return {"evidence": "DECODED DATA + CONTROLLED ROUTINE RESULT",
            "rom_offset": h(SPAWN_MAP_ROM, 5), "bank_cpu": "1C:$8146", "side": 32, "cell_pixels": CELL,
            "cell_index": "col = (d + 128) >> 4, row = (dy + 128) >> 4; d + 128 must lie in 0..511 (8-bit after halving)",
            "rows": rows, "value_counts": counts,
            "closed_form_cell_equals_max_of_axis_bands": closed_form,
            "band_definition": {"0": "d in [0,256): exactly the original 256-px window (rows: [0,256) too, taller than the 192-line screen)",
                                "1": "d in [-32,0) and [256,288): 32 px margin each side",
                                "2": "d in [-96,-32) and [288,352): 64 px outer ring",
                                "3": "d in [-128,-96) and [352,384), and anything outside [-128,384): deletion zone"},
            "bands": bands,
            "values": {"0,1": "object active (bit 6 clear)", "2": "alive but asleep (bit 6 set)", "3": "deleted unless +$04 bit 1 (keep-alive)"}}


def level_limits(rom: bytes) -> dict:
    rows = []
    for zone in range(9):
        zp = u16(rom, 0x5082 + zone * 2)
        for act in range(3):
            ap = u16(rom, zp + act * 2)
            left, top, right, bottom = u16(rom, ap + 12), u16(rom, ap + 14), u16(rom, ap + 16), u16(rom, ap + 18)
            rows.append({"zone_index": zone, "act_index": act, "header_rom": h(ap), "left": left, "top": top, "right": right,
                         "bottom": bottom, "right_plus_256": right + VIEW_W,
                         "right_plus_256_multiple_of_256": (right + VIEW_W) % 256 == 0})
    thz = {}
    for act in ("thz1", "thz2", "thz3"):
        p = ROOT / "data" / "rom-cache" / "levels" / act / "layout.json"
        if p.is_file():
            thz[act] = json.loads(p.read_text(encoding="utf-8"))["dimensions"]["width_pixels"]
    rel = {act: {"width_pixels": w, "right_limit_equals_width_minus_256": None} for act, w in thz.items()}
    by = {(r["zone_index"], r["act_index"]): r for r in rows}
    for act, key in (("thz1", (0, 0)), ("thz2", (0, 1)), ("thz3", (0, 2))):
        if act in rel:
            rel[act]["right_limit_equals_width_minus_256"] = by[key]["right"] == rel[act]["width_pixels"] - VIEW_W
    return {"evidence": "DECODED DATA", "header_fields": "act header +12 left, +14 top, +16 right, +18 bottom (words) -> $D280/$D27C/$D282/$D27E",
            "table_rom": "0x5082 zone pointers -> act pointers -> headers",
            "semantics": "left is inclusive (camera >= left); right is EXCLUSIVE (camera < right, so the largest camera is right-1); "
                         "right = world width - 256 in every THZ act (the 256 is the original window width encoded in data)",
            "rows": rows, "thz_world_width_relation": rel,
            "zone_6_aliases_zone_0": True}


def boss_tables(rom: bytes) -> dict:
    trig = rom_of(0x1E, 0x97A1)
    pan = rom_of(0x1E, 0x9808)
    zones = []
    for z in range(7):
        w, hh = u16(rom, trig + z * 4), u16(rom, trig + z * 4 + 2)
        dx, dy = s16(u16(rom, pan + z * 4)), s16(u16(rom, pan + z * 4 + 2))
        zones.append({"zone_index": z, "trigger_abs_dx_lt": w, "trigger_abs_dy_lt": hh, "pan_dx": dx, "pan_dy": dy,
                      "anchor_screen_x_when_pan_complete": -dx, "anchor_screen_y_when_pan_complete": -dy})
    return {"evidence": "DECODED DATA (table bytes) + SOURCE-TRACED BEHAVIOR (use by the type $50 code); only zone 0 is exercised by a placed type",
            "trigger_table_rom": h(trig, 5), "pan_table_rom": h(pan, 5),
            "rows": zones,
            "note": "type $50 (THZ3 boss, zone 0) uses row 0: trigger |dx|<160,|dy|<256 from the PLAYER; pan target = boss anchor + (-256,-160), i.e. "
                    "the boss anchor sits exactly on the original RIGHT edge (screen X 256) when the pan completes. Rows 1..6 are decoded but their "
                    "users are other boss types whose code was not traced (UNRESOLVED)."}


# Screen-relative sites in code outside the THZ-recovered objects. Each is a literal instruction-byte check at the stated
# offset; the OWNER is the type whose state-table pointer is the nearest one below the address in that bank (approximate).
FUTURE_SITES = [
    # (rom offset, expected bytes hex, category, constant meaning, owner_hint)
    (0x79878, "dd7e1afe38d0", "screen_x_compare", "screen X (anchor - camera, low byte) < $38 keeps patrolling, else turn", "type $33/$40-$50 table region (THZ3 boss = $50, documented)"),
    (0x79884, "dd7e1afec8d8", "screen_x_compare", "screen X low byte >= $C8 turns", "type $33/$40-$50 table region (THZ3 boss = $50, documented)"),
    (0x79A0F, "dd7e1acb7fc8fee0", "screen_x_compare", "screen X in $80..$DF enters the patrol state", "type $33/$40-$50 table region (THZ3 boss = $50, documented)"),
    (0x7A385, "dd7e1afed0d8", "screen_x_compare", "screen X < $D0 returns; otherwise compares with the player's screen X ($D51A)", "type $54 region (zone 2 boss placement) - mechanics not traced"),
    (0x7A447, "dd7e1afed4d8", "screen_x_compare", "screen X >= $D4 stops X velocity", "type $54 region (zone 2 boss placement) - mechanics not traced"),
    (0x7A771, "dd7e1afeb030", "screen_x_compare", "screen X >= $B0 skips; then screen Y >= $78 removes (vector $033E)", "type $57 region (spawned object, no zone placement) - mechanics not traced"),
    (0x7A778, "dd7e1cfe7830", "screen_y_compare", "screen Y >= $78 branches to removal", "type $57 region - mechanics not traced"),
    (0x7AA70, "dd7e1a2006fed0", "screen_x_compare", "moving right: screen X >= $D0 zeroes X velocity; moving left: screen X < $30 zeroes it", "type $59 region (zone 4 boss placement) - mechanics not traced"),
    (0x7B080, "dd7e1afe3038", "screen_x_compare", "screen X < $30 (high byte 0) takes the branch at $B092", "type $5E region (zone 5 boss placement) - mechanics not traced"),
    (0x7B0F7, "dd7e1afec0d2", "screen_x_compare", "screen X >= $C0 takes the branch at $B10B", "type $5E region (zone 5 boss placement) - mechanics not traced"),
    (0x7B4AC, "dd7e1add6617cb7c", "screen_x_compare", "moving right: screen X < $F9 returns, else vector $0437; moving left: screen X < 7 ...", "type $5F region - mechanics not traced"),
    (0x7B6F7, "3a1ad5fe55", "player_screen_x_compare", "player screen X ($D51A) compared with $55 and $A5", "type $5F/$60 region - mechanics not traced"),
    (0x03C06, "3a1cd5fed8", "player_screen_y_compare", "player screen Y ($D51C) >= $D8 sets $D293 bit 2 (vertical, below the 192-line screen)", "bank 0 player/level routine"),
    (0x7B696, "2a74d111e0ff19", "spawn_relative_to_camera", "X = camera X - $20 (32 px left of the left edge)", "type $5F region - mechanics not traced"),
    (0x7B6E1, "2a74d1110000", "spawn_relative_to_camera", "X = camera X (left edge) or camera X + $100 (right edge) chosen by +$0A bit 0", "type $5F region - mechanics not traced"),
    (0x7B845, "112000dd7e0a0f", "spawn_relative_to_camera", "X = camera X + $20 or camera X + $E0, Y = camera Y, Y speed +$600", "type $60 region (zone 5 boss placement) - mechanics not traced"),
    (0x7BAB8, "3e3f9026006f11b000", "spawn_relative_to_camera", "X = camera X + $B0 + (table-derived offset)", "type $61 region - mechanics not traced"),
    (0x7ADD6, "2a74d1af", "spawn_relative_to_camera", "X = camera X + 16-bit offset read from a data table, Y = camera Y + offset", "type $5C/$5D region - mechanics not traced"),
    (0x79178, "2a76d111c000", "camera_y_compare", "object Y compared with camera Y + $C0 (bottom of the 192-line screen)", "type $39/$3A region - mechanics not traced"),
    (0x79580, "2a76d122 7ed2".replace(" ", ""), "camera_limit_write", "bottom limit $D27E := camera Y (arena bottom lock)", "type $33/$40-$50 table region, state-4/5 tail (THZ3 boss, documented)"),
    (0x32D9A, "dd6e1add661b", "screen_x_compare", "screen X (16-bit) < $30 respawns the object at world X $C0+rand, Y $20+rand (frame of those writes UNRESOLVED)", "type $1C (bank $0C), not placed in THZ"),
]

CAMERA_VECTOR_CALLS = {
    "$0353 left-limit raise to camera ($59E3)": ("cd5303", ),
    "$0356 right-limit lower to camera ($59F3)": ("cd5603", ),
    "$0359 pan on with target BC/DE ($59C5)": ("cd5903", ),
    "$035C pan off / enable follow ($59D8)": ("cd5c03", ),
    "$0407 camera freeze + left limit := camera ($59B9)": ("cd0704", ),
    "$042B camera enable ($59B3)": ("cd2b04", ),
}


def _bank_cpu(o: int) -> tuple[int, int]:
    b = o // 0x4000
    return b, (0 if b == 0 else 0x4000 if b == 1 else 0x8000) + o % 0x4000


def future_scan(rom: bytes) -> dict:
    sites = []
    for off, expected, cat, meaning, owner in FUTURE_SITES:
        b, c = _bank_cpu(off)
        got = rom[off:off + len(expected) // 2].hex()
        sites.append({"rom_offset": h(off, 5), "bank": b, "cpu": h(c), "bytes": got, "bytes_match_expected": got == expected,
                      "category": cat, "meaning": meaning, "owner_hint": owner})
    vectors = {}
    for name, (pat,) in CAMERA_VECTOR_CALLS.items():
        hits = []
        for m in re.finditer(re.escape(bytes.fromhex(pat)), rom):
            b, c = _bank_cpu(m.start())
            hits.append({"rom_offset": h(m.start(), 5), "bank": b, "cpu": h(c)})
        vectors[name] = hits
    # state-table pointers of the types >= $26 (bank $1E), to map code regions to type numbers
    table = {}
    for t in range(0x26, 0x64):
        table[h(t, 2)] = h(u16(rom, 0x65BA + (t - 1) * 2))
    placements = {}
    for zone in range(9):
        zp = u16(rom, 0x70546 + zone * 2)
        for act in range(3):
            ap = u16(rom, 0x70000 + zp - 0x8000 + act * 2)
            o = 0x70000 + ap - 0x8000
            types: dict[int, int] = {}
            while rom[o] != 0xFF:
                types[rom[o]] = types.get(rom[o], 0) + 1
                o += 9
            placements[f"zone{zone}_act{act}"] = {h(k, 2): v for k, v in sorted(types.items())}
    return {"evidence": "BYTE-VERIFIED ASSEMBLY (instruction bytes at each site) + DECODED DATA (placements, type table); mechanics UNRESOLVED",
            "sites": sites, "camera_vector_call_sites": vectors, "type_state_table_pointers": table,
            "placed_types_by_zone_act": placements,
            "note": "Owner hints use the nearest preceding type state-table pointer in the same bank; they are a navigation aid, not a proof. "
                    "Nothing in this list is claimed to be understood beyond the instruction semantics."}


# --------------------------------------------------------------------------- #
# 4. controlled fixtures (original Z80 routines on tools/oracle.py)
# --------------------------------------------------------------------------- #
class Lab:
    def __init__(self, rom: bytes):
        from oracle import Oracle
        self.rom = rom
        self.o = Oracle(rom)
        self.m = self.o.mem

    def w(self, a, v):
        self.o.word(a, v)

    def camera(self, x, y=None):
        self.w(0xD174, x)
        self.w(0xD284, x)
        if y is not None:
            self.w(0xD176, y)
            self.w(0xD286, y)


def lifetime_fixture(lab: Lab) -> dict:
    o, m = lab.o, lab.m
    S = 0xD740
    cases = bad = 0
    first_bad = None
    edges = []
    for cam in CAMERAS[:8] + [3831, 4095, 8000]:
        for camy in (8, 300):
            for dx in range(-140, 400, 7):
                for dy in (-120, -100, -97, -96, -33, -32, 0, 100, 255, 256, 287, 288, 351, 352):
                    for fl, tok in ((0, 1), (2, 1), (0, 0)):
                        m[S:S + 0x40] = bytes(0x40)
                        m[S], m[S + 1], m[S + 4], m[S + 0x3E] = 0x27, 1, fl, tok
                        o.word(S + 0x11, cam + dx)
                        o.word(S + 0x14, camy + dy)
                        o.word(0xD174, cam)
                        o.word(0xD176, camy)
                        o.cpu.ix = S
                        o.call(0x61E1)
                        got = (m[S], (m[S + 4] >> 6) & 1)
                        out, b6 = lifetime_outcome(dx, dy, bool(fl & 2), bool(tok))
                        want = (0x27 if out in ("active", "asleep") else 0xFE if out == "remove_tracked" else 0xFF, b6)
                        cases += 1
                        if got != want:
                            bad += 1
                            first_bad = first_bad or [cam, camy, dx, dy, fl, tok, got, want]
    # exact horizontal edges at several cameras (dy = 100 keeps the vertical band at 0)
    for cam in (0, 1000, 3831):
        row = {}
        for d in (-97, -96, -33, -32, -1, 0, 255, 256, 287, 288, 351, 352):
            m[S:S + 0x40] = bytes(0x40)
            m[S], m[S + 1], m[S + 4], m[S + 0x3E] = 0x27, 1, 0, 1
            o.word(S + 0x11, cam + d)
            o.word(S + 0x14, 400)
            o.word(0xD174, cam)
            o.word(0xD176, 300)
            o.cpu.ix = S
            o.call(0x61E1)
            row[str(d)] = {"type": h(m[S], 2), "bit6": (m[S + 4] >> 6) & 1}
        edges.append({"camera_x": cam, "by_screen_relative_x": row})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "$61E1 (bank $1C map)", "cases": cases, "mismatches": bad,
            "first_mismatch": first_bad, "edge_samples": edges,
            "rule": "cell = max(band(x-cam), band(y-camY)); cells 0/1 active; 2 asleep (bit 6 set); 3 or outside [-128,384) removed "
                    "($FE with placement token, $FF without) unless +$04 bit 1 keeps it asleep"}


def scan_fixture(lab: Lab) -> dict:
    o, m = lab.o, lab.m
    u = lambda p: u16(lab.rom, p)

    def records(zone, act):
        zp = u(0x70546 + zone * 2)
        ap = u(0x70000 + zp - 0x8000 + act * 2)
        p = 0x70000 + ap - 0x8000
        out = []
        while lab.rom[p] != 0xFF:
            out.append((lab.rom[p], u(p + 1), u(p + 3)))
            p += 9
        return out

    cases = bad = 0
    first_bad = None
    for zone, act in ((0, 0), (0, 1), (0, 2), (3, 2)):
        recs = records(zone, act)
        for cam in list(range(0, 4000, 97)) + CAMERAS:
            for camy in (8, 100, 400, 600):
                for fill in (0, 1):
                    o.bank(2, 0x1C)
                    m[0xD12B] = 0x1C
                    m[0xD400:0xD450] = bytes(0x50)
                    m[0xD700:0xD700 + 12 * 0x40] = bytes(12 * 0x40)
                    m[0xD297], m[0xD298], m[0xD440] = zone, act, fill
                    o.word(0xD174, cam)
                    o.word(0xD176, camy)
                    o.call(0x8000)
                    got = [i for i in range(len(recs)) if m[0xD400 + i]]
                    want, free = [], 11
                    for i, (_, x, y) in enumerate(recs):
                        if scan_creates(x - 256 - cam, y - 256 - camy, fill == 0) and free:
                            free -= 1
                            want.append(i)
                    cases += 1
                    if got != want:
                        bad += 1
                        first_bad = first_bad or [zone, act, cam, camy, fill, got, want]
    # type $27 THZ1 records: creation / active camera-X ranges from the model, spot-checked on the ROM at the boundaries
    recs = records(0, 0)
    bees = [(i, x - 256, y - 256) for i, (t, x, y) in enumerate(recs) if t == 0x27]
    rows = []
    for i, x, y in bees:
        camy = y - 100
        created = []
        for cam in range(x - 420, x + 140):
            o.bank(2, 0x1C)
            m[0xD12B] = 0x1C
            m[0xD400:0xD450] = bytes(0x50)
            m[0xD700:0xD700 + 12 * 0x40] = bytes(12 * 0x40)
            m[0xD297], m[0xD298], m[0xD440] = 0, 0, 1
            o.word(0xD174, cam)
            o.word(0xD176, camy)
            o.call(0x8000)
            if m[0xD400 + i]:
                created.append(cam)
        active = [c for c in range(x - 420, x + 140) if cell(x - c, 100) <= 1]
        rows.append({"record_index": i, "world_x": x, "world_y": y,
                     "steady_state_creation_camera_x": [min(created), max(created)],
                     "creation_screen_relative_x": [x - max(created), x - min(created)],
                     "active_camera_x": [min(active), max(active)],
                     "active_screen_relative_x": [x - max(active), x - min(active)]})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "$8000 (bank $1C)", "cases": cases, "mismatches": bad,
            "first_mismatch": first_bad, "record_pool_capacity": 11, "type_27_thz1": rows,
            "rule": "created iff occupancy byte is 0 and (cell == 2, or cell <= 1 while $D440 == 0 [initial fill]); record X/Y are stored world+256, "
                    "so the test is (storedX-256-cam, storedY-256-camY); at most 11 slots; the scan runs once per 4 object updates"}


def follow_fixture(lab: Lab) -> dict:
    o, m = lab.o, lab.m
    rows = []
    cases = bad = 0
    first_bad = None
    for cam in (0, 1000, 3831, 5000):
        for left in (0, 1):
            for k in range(0, 256):
                m[0xD15E], m[0xD15F] = 0x80, 0
                lab.camera(cam, 300)
                m[0xD504] = 0x10 if left else 0
                tgt = 0x88 if left else 0x68
                a = tgt
                m[0xD288], m[0xD289], m[0xD28A] = tgt, 0x78, a
                m[0xD28C], m[0xD28B] = (a - 8) & 255, (a + 8) & 255
                m[0xD28D], m[0xD28F], m[0xD28E] = 0x78, 0x68, 0x98
                o.word(0xD511, cam + k)
                o.word(0xD514, 300 + 0x78)
                o.cpu.ix = 0xD15E
                o.call(0x5832)
                got = s16(o.word(0xD284) - cam)
                want = follow_delta_x(k, a) if k else 0
                cases += 1
                if got != want:
                    bad += 1
                    first_bad = first_bad or [cam, left, k, got, want]
    # facing slew: D28A moves one pixel per update toward the new lead
    m[0xD15E], m[0xD15F] = 0x80, 0
    lab.camera(1000, 300)
    m[0xD504] = 0x10
    m[0xD28A], m[0xD288], m[0xD289] = 0x68, 0x78, 0x78
    seq = []
    for _ in range(40):
        o.word(0xD511, 1100)
        o.word(0xD514, 420)
        o.cpu.ix = 0xD15E
        o.call(0x5832)
        seq.append(m[0xD28A])
    rows.append({"facing_changed_to_left_lead_sequence_first_5_last_2": seq[:5] + seq[-2:], "updates_to_settle": seq.index(0x88) + 1})
    # pan-mode target offset ($D15F & 3 != 0 -> $78)
    m[0xD15E], m[0xD15F] = 0x80, 1
    m[0xD504] = 0
    m[0xD28A] = 0x68
    o.word(0xD511, 1100)
    o.cpu.ix = 0xD15E
    o.call(0x58E1)
    pan_target = m[0xD288]
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "$5832 / $58E1", "cases": cases, "mismatches": bad, "first_mismatch": first_bad,
            "lead_right_facing": 0x68, "lead_left_facing": 0x88, "lead_in_pan_mode": pan_target, "dead_zone_half_width": 8,
            "player_screen_x_dead_zone_right_facing": [0x60, 0x70], "player_screen_x_dead_zone_left_facing": [0x80, 0x90],
            "max_step_right": 7, "max_step_left": -7, "left_step_quirk": "a step of exactly -8 is kept (A-B = $F8 passes the clamp), -9 and below become -7",
            "slew": rows[0],
            "rule": "k = low byte of (playerX - $D284). k in [lead-8, lead+8] -> no scroll; k >= lead+8: +min(7, k-(lead+8)); "
                    "k < lead-8: max(-7, k-(lead-8)) (exactly -8 allowed); the new target is $D174 + step"}


def pan_fixture(lab: Lab) -> dict:
    o, m = lab.o, lab.m
    rows = []

    def one(cam, camy, tx, ty, zone=0):
        m[0xD15E], m[0xD15F] = 0x80, 1
        lab.camera(cam, camy)
        m[0xD297] = zone
        o.word(0xD2DA, tx)
        o.word(0xD2DC, ty)
        o.word(0xD280, 0)
        o.word(0xD282, 20000)
        o.word(0xD27C, 8)
        o.word(0xD27E, 784)
        m[0xD28A], m[0xD288], m[0xD289] = 0x78, 0x78, 0x78
        o.cpu.ix = 0xD15E
        o.call(0x5832)
        return {"x_step": s16(o.word(0xD284) - cam), "y_step": s16(o.word(0xD286) - camy), "limit_left": o.word(0xD280), "limit_right": o.word(0xD282)}

    cases = bad = 0
    for cam in CAMERAS[:12]:
        for camy in (300, 405, 500):
            for dxv in (-40, -1, 0, 1, 40):
                for dyv in (-40, -1, 0, 1, 40):
                    tx, ty = cam + dxv + 1000, camy + dyv
                    r = one(cam + 1000, camy, tx, ty)
                    exp_x = (dxv > 0) - (dxv < 0)
                    exp_y = (dyv > 0) - (dyv < 0)
                    cases += 1
                    if (r["x_step"], r["y_step"]) != (exp_x, exp_y):
                        bad += 1
    right = one(3825, 446, 3832, 405)
    left = one(3900, 300, 3832, 405)
    z6 = one(3825, 446, 3832, 405, zone=6)
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "$5956 (pan branch of $5832)", "cases": cases, "mismatches": bad,
            "x_speed_px_per_update": 1, "y_speed_px_per_update": 1, "axes_independent_and_simultaneous": True,
            "right_pan_lowers_right_limit_to_target": right, "left_pan_raises_left_limit_to_target": left,
            "zone_6_does_not_move_limits": z6,
            "rule": "each update: X += sign(targetX - camX), Y += sign(targetY - camY); moving right sets $D282 := targetX, moving left sets $D280 := targetX "
                    "(not in zone index 6); pan mode ($D15F bit 0) persists after arrival and disables the follow routine"}


def limit_fixture(lab: Lab) -> dict:
    o, m = lab.o, lab.m
    cases = bad = 0
    for cam, left, right in ((100, 95, 3840), (3835, 0, 3840), (3831, 0, 3832), (500, 500, 600), (0, 0, 3840), (2000, 1990, 2000)):
        for delta in range(-9, 10):
            flag = 4 if delta < 0 else 8 if delta > 0 else 0
            m[0xD15E] = 0x80 | flag
            o.word(0xD174, cam)
            o.word(0xD284, cam + delta)
            o.word(0xD280, left)
            o.word(0xD282, right)
            o.cpu.ix = 0xD15E
            o.call(0x4CB0)
            got = o.word(0xD284) - cam
            want = limit_x_delta(cam, delta, left, right) if flag else 0
            cases += 1
            if got != want:
                bad += 1
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "$4CB0", "cases": cases, "mismatches": bad,
            "left_limit": "inclusive: camera >= $D280", "right_limit": "EXCLUSIVE: camera < $D282, so the camera stops at $D282-1",
            "overshoot_behaviour": "a step that would cross the limit is dropped entirely (the camera does not slide to the limit)",
            "consequence_for_sign_pan": "pan target X = signX-$80 sets $D282 to the same value, hence the camera settles at signX-$81"}


def clamp_fixture(lab: Lab) -> dict:
    o, m = lab.o, lab.m

    def run(entry, cam, d, state=1, vx=0):
        o.word(0xD174, cam)
        o.word(0xD511, cam + d)
        m[0xD510] = 0x55
        o.word(0xD516, vx)
        m[0xD501] = state
        o.cpu.ix = 0xD500
        o.call(entry)
        return o.word(0xD511) - cam, m[0xD510], o.word(0xD516)

    cases = bad = 0
    first_bad = None
    for entry in (0x4281, 0x4141):
        for cam in CAMERAS:
            for d in range(0, 256):
                x, frac, v = run(entry, cam, d)
                b = clamp_bound(d)
                want = {None: d, "left": 0x10, "right": 0xF7}[b]
                cases += 1
                if x != want:
                    bad += 1
                    first_bad = first_bad or [hex(entry), cam, d, x, want]
    # velocity compensation: the snap subtracts this update's X speed and zeroes it
    comp = []
    for vx in (0x0100, 0x0180, 0x0600, 0xFE80):
        x, frac, v = run(0x4281, 3831, 250, vx=vx)
        comp.append({"vx_88": vx, "x_after_minus_cam": x, "fraction_byte": frac, "vx_after": v})
    # wrap hazard: the test reads only the low byte of (playerX - cam)
    wrap = [{"d": d, "x_after_minus_cam": run(0x4281, 1000, d)[0]} for d in (256 + 5, 256 + 100, 256 + 250)]
    # state gate of $4141: states >= $29 skip the clamp
    gate = {h(st, 2): run(0x4141, 1000, 5, state=st)[0] for st in (0, 1, 0x1D, 0x20, 0x28, 0x29, 0x2A, 0x30)}
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routines": "$4281, $4141", "cases": cases, "mismatches": bad, "first_mismatch": first_bad,
            "bounds_relative_to_camera": {"left_snap": 0x10, "right_snap": 0xF7, "left_triggers_below": 0x10, "right_triggers_from": 0xF8},
            "velocity_compensation_samples": comp, "low_byte_wrap_samples": wrap, "state_gate_x_minus_cam_for_d5": gate,
            "rule": "e = low byte of (playerX - cam); e < $10 -> X = cam + $10; e >= $F8 -> X = cam + $F7; the snapped position is reduced by this "
                    "update's X speed (8.8) and X speed is cleared; states >= $29 are not clamped by $4141. Player extents are NOT read."}


def state20_fixture(lab: Lab) -> dict:
    o, m = lab.o, lab.m
    o.bank(2, 0x0C)
    m[0xD12B] = 0x0C
    cases = bad = 0
    first_bad = None
    rows = []
    for act_idx in (0, 1, 2):
        for cam in CAMERAS:
            for diff in (0xF7, 0xF8, 0xF9, 0x11F, 0x120, 0x121, 0x122, 0x200):
                m[0xD293] = 0x40
                m[0xD298] = act_idx
                m[0xD15E] = 0x88
                o.word(0xD280, 12345)
                o.word(0xD174, cam)
                o.word(0xD511, cam + diff)
                o.word(0xD516, 0x0500)
                m[0xD504] = 0x10
                o.cpu.ix = 0xD500
                o.call(0x83A6)
                flag = (m[0xD293] & 0x30) != 0
                frozen = (m[0xD15E] & 0x80) == 0
                cases += 1
                if flag != state20_flag(diff) or frozen != state20_camera_freeze(diff) or (frozen and o.word(0xD280) != cam):
                    bad += 1
                    first_bad = first_bad or [act_idx, cam, diff, flag, frozen]
                if cam == 3831 and act_idx == 0:
                    rows.append({"d": diff, "flag": flag, "camera_frozen": frozen})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "$83A6 (bank $0C)", "cases": cases, "mismatches": bad, "first_mismatch": first_bad,
            "samples_camera_3831": rows,
            "rule": "d = (playerX - cameraX) as unsigned 16-bit: d > $F8 clears $D15E bit 7 and sets $D280 := camera (camera frozen); "
                    "d > $120 (d >= $121 = 289 = RIGHT + 33) sets $D293 bit 5 (act index < 2) / bit 4; the 16-bit compare (unlike the clamp) allows d >= 256"}


def child19_fixture(rom: bytes) -> dict:
    o18 = _load("object_18")
    f = o18.ready_at_state3(rom, "thz1")
    rows = []
    cases = bad = 0
    for cam in (0, 1000, 3832, 5000):
        for camy in (0, 405, 700):
            f.restore()
            f.o.word(0xD174, cam)
            f.o.word(0xD176, camy)
            f.call_cb(0xAA47)
            kid = next(i for i in range(19) if f.m[0xD540 + i * 0x40] == 0x19)
            base = 0xD540 + kid * 0x40
            xs = []
            for _ in range(40):
                f.player(cam - 100, 558, vx=0)
                f.o.word(0xD174, cam)
                f.o.word(0xD176, camy)
                f.update_all()
                xs.append((f.m[base + 1], f.m[base + 0x11] | f.m[base + 0x12] << 8, f.m[base + 0x14] | f.m[base + 0x15] << 8))
            stop = next(x for x in xs if x[0] == 2)
            row = {"camera": [cam, camy], "x_minus_cam_after_first_update": xs[0][1] - cam, "y_minus_camy": xs[0][2] - camy,
                   "state2_first_x_minus_cam": stop[1] - cam}
            rows.append(row)
            cases += 1
            if xs[0][2] - camy != 0x50 or not (0x7D < stop[1] - cam <= 0x85) or xs[0][1] - cam not in (0x104, 0xFC):
                bad += 1
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "type $19 states 0/1 ($AA87/$AAE4)", "cases": cases, "mismatches": bad, "rows": rows,
            "rule": "created at X = cam + $104 (RIGHT + 4), Y = camY + $50; state 1 subtracts 8 per update until X <= cam + $85 "
                    "(centre + 5); every term is relative to the camera at that update"}


def player_distance_fixture(lab: Lab) -> dict:
    o, m = lab.o, lab.m
    S = 0xD740

    def helper(entry, bc, obj, ply, axis_x=True, cam=0):
        m[S:S + 0x40] = bytes(0x40)
        o.word(S + 0x11 if axis_x else S + 0x14, obj)
        o.word(0xD511 if axis_x else 0xD514, ply)
        o.word(0xD174, cam)
        o.word(0xD176, cam)
        o.cpu.ix = S
        o.call(entry, bc=bc)
        return o.cpu.a

    cases = bad = 0
    for bc in (0x40, 0x180, 0x280, 0xA0, 12):
        for cam in CAMERAS:
            for delta in (-bc - 1, -bc, -bc + 1, -1, 0, 1, bc - 1, bc, bc + 1):
                for axis_x, entry in ((True, 0x61A5), (False, 0x61B1)):
                    got = helper(entry, bc, 3000, 3000 + delta, axis_x, cam)
                    want = 0xFF if abs(delta) < bc else 0
                    cases += 1
                    if got != want:
                        bad += 1
    # type $28 persistence removal ($8908), keep-alive bit set
    o.bank(2, 0x1E)
    m[0xD12B] = 0x1E
    rows = []
    t28bad = 0
    for cam in (0, 1000, 3831):
        for dxv, dyv in ((0, 0), (639, 0), (640, 0), (641, 0), (0, 671), (0, 672), (0, 673), (-639, 0), (-640, 0), (-641, 0), (0, -671), (0, -672)):
            m[S:S + 0x40] = bytes(0x40)
            m[S], m[S + 4] = 0x28, 2
            o.word(S + 0x11, 3000)
            o.word(S + 0x14, 3000)
            o.word(0xD511, 3000 + dxv)
            o.word(0xD514, 3000 + dyv)
            o.word(0xD174, cam)
            o.cpu.ix = S
            o.call(0x8908)
            removed = m[S] == 0xFE
            want = abs(dxv) >= 0x280 or abs(dyv) >= 0x2A0
            if removed != want:
                t28bad += 1
            if cam == 0:
                rows.append({"dx": dxv, "dy": dyv, "removed": removed})
    # without the keep-alive bit the routine does nothing
    m[S:S + 0x40] = bytes(0x40)
    m[S], m[S + 4] = 0x28, 0
    o.word(S + 0x11, 3000)
    o.word(0xD511, 0)
    o.cpu.ix = S
    o.call(0x8908)
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "$61A5/$61B1 (vectors $0383/$0386), $8908", "cases": cases, "mismatches": bad,
            "helper_rule": "returns $FF iff |object - player| < BC (strict); independent of the camera for every camera swept",
            "type_28_cases": len(rows) * 3, "type_28_mismatches": t28bad, "type_28_samples_camera_0": rows,
            "type_28_removal_without_keepalive_bit": m[S] == 0xFE,
            "type_28_rule": "with +$04 bit 1 set: removed (type $FE) when |dx| >= $280 (640) or |dy| >= $2A0 (672) from the player"}


# --------------------------------------------------------------------------- #
# 5. emulated original frames
# --------------------------------------------------------------------------- #
def emulated_act_clear_camera(rom: bytes) -> dict:
    o18 = _load("object_18")
    from sms_frame_harness import BTN_RIGHT
    runs = []
    for act_idx, sy, camx0, px0 in ((0, 558, 3700, 3800), (1, 654, 3700, 3800), (0, 558, 3760, 3850)):
        def hook(m, sy=sy, camx0=camx0, px0=px0):
            m.w16(0xD2D6, camx0)
            m.w16(0xD2D8, sy - 118)
            m.w16(0xD511, px0)
            m.w16(0xD514, sy - 58)

        s = o18._boot(rom, act_idx, hook)
        m = s.mem
        contact = None
        rows = []
        for f in range(900):
            done = (m[0xD293] & 0x30) != 0
            s.pad = BTN_RIGHT if not done and m[0xD501] != 0x20 else 0
            s.run_frame()
            b = o18._sign(s)
            if contact is None and b and m[b + 2] == 4:
                contact = f
            if contact is not None:
                rows.append({"rel": f - contact, "cam": (s.u16(0xD174), s.u16(0xD176)), "d15e": m[0xD15E], "d15f": m[0xD15F],
                             "pan": (s.u16(0xD2DA), s.u16(0xD2DC)), "limits_lr": (s.u16(0xD280), s.u16(0xD282)),
                             "px": s.u16(0xD511), "state": m[0xD501], "flag": m[0xD293]})
            if done:
                break
        sign_x = 3960
        c0, last = rows[0], rows[-1]
        final_cam = last["cam"]
        x_done = next(r["rel"] for r in rows if r["cam"][0] == final_cam[0])
        y_done = next(r["rel"] for r in rows if r["cam"][1] == final_cam[1])
        s20 = next(r["rel"] for r in rows if r["state"] == 0x20)
        freeze = next(r["rel"] for r in rows if r["d15e"] & 0x80 == 0)
        hold = [r["px"] - final_cam[0] for r in rows if r["rel"] > 60 and r["state"] != 0x20]
        runs.append({"act_index": act_idx, "start_camera_x": camx0, "start_player_x": px0,
                     "contact_camera": c0["cam"], "pan_target": c0["pan"], "final_camera": final_cam,
                     "pan_x_complete_rel": x_done, "pan_y_complete_rel": y_done,
                     "camera_x_moves_after_pan": any(r["cam"][0] != final_cam[0] for r in rows if r["rel"] > x_done),
                     "camera_y_total_move": c0["cam"][1] - final_cam[1], "camera_x_total_move": final_cam[0] - c0["cam"][0],
                     "right_limit_at_contact_and_end": [c0["limits_lr"][1], last["limits_lr"][1]],
                     "left_limit_end": last["limits_lr"][0],
                     "sign_screen_x_final": sign_x - final_cam[0], "sign_screen_y_final": sy - final_cam[1],
                     "player_held_right_screen_x_min_max": [min(hold), max(hold)] if hold else None,
                     "state20_starts_rel": s20, "camera_frozen_rel": freeze, "flag_rel": last["rel"],
                     "player_x_at_flag": last["px"], "d_at_flag": last["px"] - final_cam[0], "flag_value": last["flag"],
                     "player_x_minus_sign_x_at_flag": last["px"] - sign_x})
    return {"evidence": "EMULATED ORIGINAL FRAME",
            "method": "original ROM booted in tools/sms_frame_harness.py, camera/player placed at the stated start, RIGHT held until $D293 bit 4/5; frames counted from sign contact",
            "runs": runs}


def emulated_bee_scroll(rom: bytes) -> dict:
    o18 = _load("object_18")
    BX, BY = 3504, 224
    out = []
    for step in (1, 2, 3):
        cam0 = BX - 520

        def hook(m, cam0=cam0):
            m.w16(0xD2D6, cam0)
            m.w16(0xD2D8, BY - 100)
            m.w16(0xD511, cam0 + 104)
            m.w16(0xD514, BY)

        s = o18._boot(rom, 0, hook)
        m = s.mem
        cam = cam0
        first = {}
        for f in range(700):
            cam += step
            for a in (0xD174, 0xD284):
                s.w16(a, cam)
            for a in (0xD176, 0xD286):
                s.w16(a, BY - 100)
            s.w16(0xD511, cam + 104)
            s.w16(0xD514, BY)
            s.w16(0xD516, 0)
            s.w16(0xD518, 0)
            s.run_frame()
            for i in range(11):
                b = 0xD700 + i * 0x40
                if m[b] == 0x27 and s.u16(b + 0x3A) == BX:
                    x = s.u16(b + 0x11)
                    first.setdefault("created", {"camera_x": cam, "screen_x": x - cam})
                    if not (m[b + 4] >> 6) & 1:
                        first.setdefault("awake", {"camera_x": cam, "screen_x": x - cam})
                    if x < BX:
                        first.setdefault("first_moved", {"camera_x": cam, "screen_x": x - cam, "x": x})
        out.append({"camera_step_per_frame": step, **first})
        if step == 1:
            pass
    return {"evidence": "EMULATED ORIGINAL FRAME",
            "method": "camera and player placed by the script every frame (camera scrolls right at a fixed rate, player at camera+104), THZ1 type $27 record (3504,224) in an otherwise untouched game",
            "runs": out,
            "expected_from_model": {"creation_screen_x_range": [288, 351], "awake_screen_x_range": [0, 287]}}


def emulated_vdp(rom: bytes) -> dict:
    o18 = _load("object_18")

    def hook(m):
        m.w16(0xD2D6, 3000)
        m.w16(0xD2D8, 400)
        m.w16(0xD511, 3100)
        m.w16(0xD514, 500)

    s = o18._boot(rom, 0, hook)
    seen = set()
    for _ in range(150):
        s.run_frame()
        seen.add((s.reg[0], s.reg[1], s.reg[5], s.reg[6], s.reg[7], s.reg[10]))
    cam, camy = s.u16(0xD174), s.u16(0xD176)
    return {"evidence": "EMULATED ORIGINAL FRAME (VDP register state written by the original code)",
            "registers_seen_during_150_gameplay_frames": [[h(x, 2) for x in t] for t in sorted(seen)],
            "r8_equals_neg_cam_plus_1": s.reg[8] == (-(cam + 1)) & 255, "r9_equals_camy_plus_17_mod_224": s.reg[9] == (camy + 17) % 224,
            "r0_bit5_left_column_mask": bool(s.reg[0] & 0x20),
            "note": "R0 = $26 has bit 5 set. By SMS VDP documentation that masks screen column 0..7 with the backdrop colour, so the visible window is "
                    "x = 8..255 of the 256-px scroll window. The mask is a hardware semantic of the register value, not measured on pixels here."}


# --------------------------------------------------------------------------- #
# 6. classification table
# --------------------------------------------------------------------------- #
def constants_table() -> list[dict]:
    def row(system, constant, rom_address, raw_meaning, frame, cls, w256, implication, confidence, evidence):
        return {"system": system, "constant": constant, "rom_address": rom_address, "raw_meaning": raw_meaning, "coordinate_frame": frame,
                "class": cls, "relationship_to_256px": w256, "widescreen_implication": implication, "confidence": confidence,
                "evidence": evidence}

    CR = "CONTROLLED ROUTINE RESULT"
    ST = "SOURCE-TRACED BEHAVIOR"
    EM = "EMULATED ORIGINAL FRAME"
    DD = "DECODED DATA"
    return [
        # --- presentation / camera definition
        row("view", "scroll window width 256", "VDP init $1D2D (R0..R6)", "name table 32 columns; the camera is the world X of screen column 0", "screen", "E",
            "defines RIGHT = cam + 256", "every RIGHT-relative rule below is relative to the displayed width, not to 256", "high", EM),
        row("view", "R0 = $26 (bit 5)", "ROM $1D2D", "left 8 px column masked by the VDP", "screen", "E", "visible x = 8..255", "presentation only; no gameplay constant reads it", "medium", EM),
        row("camera", "camera X $D174 / Y $D176", "$4D3E, commit $0570", "R8 = -(cam+1), R9 = (camY+17) mod 224; $D174 := $D284 at vblank", "world", "B", "left edge = cam",
            "the left edge is the origin of every screen-relative value; a wide view extends RIGHT only", "high", CR),
        row("camera", "follow lead 104 / 136 (pan mode 120)", "$58E1..$58F3, init $5074", "player screen X target: $68 facing right, $88 facing left, $78 while panning; slews 1 px/update", "screen (left origin)", "B",
            "104 = centre-24, 136 = centre+8", "tuning of where the player sits; relation to the width is not proven (not forced by any other constant)", "high", CR),
        row("camera", "dead zone +-8, max step 7", "$590D/$5912, $5861..$5867, $587F..$5885", "no scroll while player screen X in [lead-8, lead+8]; step capped at +7/-7 px per update", "screen offset / speed", "B",
            "none", "motion constants, independent of width", "high", CR),
        row("camera", "pan speed 1 px/update per axis", "$5964 INC DE, $597C DEC DE, $599F, $59A9", "pan toward ($D2DA,$D2DC); X and Y simultaneous", "world", "B",
            "none", "POC provisional 4 px/update and absent Y pan are adapters, not ROM", "high", CR),
        row("camera", "pan sets limits", "$596D..$597A, $5985..$598F", "moving right: $D282 := target; moving left: $D280 := target (not zone index 6)", "world", "B", "none", "pan target also becomes the lock", "high", CR),
        row("camera", "limits left/top/right/bottom", "act header +12/+14/+16/+18; table $5082", "THZ: left 0, right = width-256 (exclusive), top 8, bottom = height-240", "world", "A",
            "right = world width - 256", "right limit encodes the original window; a wider view needs worldWidth - viewWidth", "high", DD),
        row("camera", "right limit exclusive, left inclusive", "$4CC5 (JR c), $4CE2 (JR nc)", "camera in [left, right-1]; overshooting steps are dropped", "world", "B", "none",
            "camera settles at limit-1 (signX-129 in the sign pan)", "high", CR),
        row("camera", "left lock / right lock", "vectors $0353/$0356 -> $59E3/$59F3", "$D280 := max($D280,cam); $D282 := min($D282,cam)", "world", "B", "arena width = visible width",
            "a right lock at the camera makes the right screen edge the arena wall", "high", ST),
        # --- player
        row("player", "left clamp 16", "$4153 (LD BC,$10), $4156 (CP $10); copy at $428C/$428F", "playerX < cam+16 -> X = cam+16 (minus this update's speed), X speed := 0", "camera-relative", "C",
            "LEFT + 16 (= 8 masked + extent 8, interpretation)", "stays LEFT + 16", "high", CR),
        row("player", "right clamp 247", "$415B (LD BC,$F7), $415E (CP $F8); copy at $4294/$4297", "low byte of (playerX-cam) >= $F8 -> X = cam+$F7", "camera-relative (8-bit)", "C",
            "RIGHT - 9 (= 255 - extent 8, interpretation)", "must follow the displayed right edge or it is an invisible wall; low-byte compare breaks for d >= 256", "high", CR),
        row("player", "state gate $29", "$4144 (CP $29)", "$4141 clamps only states < $29; state $20 (act-clear run) uses its own handler and is not clamped", "state", "F",
            "none", "—", "high", CR),
        row("player", "pit death screen Y >= $D8", "$3C09 (CP $D8) at $3C06", "player screen Y >= 216 sets $D293 bit 2", "screen Y", "C", "vertical, not width", "unaffected by horizontal widening", "medium", "BYTE-VERIFIED ASSEMBLY"),
        # --- act clear
        row("act-clear", "camera freeze d > $F8", "$83C2 (LD DE,$00F8) .. $83CB (CALL $0407), bank $0C", "playerX - cam >= 249: $D15E bit 7 cleared, $D280 := cam", "camera-relative 16-bit", "C", "RIGHT - 7",
            "freeze the camera when the player passes RIGHT - 7", "high", CR),
        row("act-clear", "clear threshold d >= $121", "$83CF (LD HL,$0120) .. $83E7 (SET 5), bank $0C", "(playerX - cam) as unsigned 16-bit > $120 sets $D293 bit 5 (act idx < 2) or bit 4", "camera-relative 16-bit", "C",
            "RIGHT + 33 (exact; = 289)", "player anchor 33 px past the right edge; camera is frozen so it is also a fixed world X once the pan ended", "high", CR),
        row("act-clear", "sign pan target (signX-$80, signY-$99)", "$AA22..$AA47 (bank $0C), vector $0359", "camera pans until the sign sits at screen X 128 / Y 153", "screen centre X, screen Y 153", "C",
            "CENTRE (128); effective camera = target-1 because the right limit is exclusive", "centre the sign in the displayed width: cam = signX - view/2 (-1)", "high", EM),
        row("act-clear", "child $19 X = cam+$104 -> cam+$85, Y = camY+$50", "$AA87.., $AAE4.. (bank $0C)", "spawns at RIGHT + 4, slides left 8 px/update to CENTRE + 5", "screen", "E",
            "RIGHT + 4 / CENTRE + 5", "screen-anchored HUD-like banner: express as RIGHT and CENTRE offsets", "high", CR),
        # --- lifecycle
        row("lifecycle", "active band [-32, 288)", "$61E1, map ROM $70146 (bank 1C $8146)", "cells 0/1: bit 6 clear (updates run, SAT eligible)", "camera-relative", "D",
            "LEFT - 32 .. RIGHT + 32 (map cell 0 = exactly [0,256))", "wake boundary is RIGHT + 32 of the displayed width", "high", CR),
        row("lifecycle", "asleep ring [-96,-32) and [288,352)", "$61E1", "cell 2: alive, bit 6 set, no updates", "camera-relative", "D", "RIGHT + 32 .. RIGHT + 96", "create/sleep ring follows the displayed edges", "high", CR),
        row("lifecycle", "deletion beyond -96 / +352 (window [-128,384))", "$61E1: $61EB/$6209 (LD BC,$0080), $61F9 SRL, $624C", "cell 3 or outside the 512-px window: type $FE (tracked) / $FF unless +$04 bit 1", "camera-relative", "D",
            "LEFT - 96 / RIGHT + 96", "window is 2 x 256 wide because an 8-bit byte holds (d+128)/2: structural limit", "high", CR),
        row("lifecycle", "vertical bands", "$61E1", "same bands on camera Y: cell 0 = [0,256) although the screen is 192 lines", "camera-relative Y", "D", "vertical window 256 tall", "vertical unchanged by horizontal widening", "high", CR),
        row("lifecycle", "creation: cell 2 only (cells 0/1 only at initial fill)", "$8021/$802A (offset $FF80), $8099 (CP 2), $809D (CP 3), $80A2 (LD A,($D440))", "steady scrolling creates objects in the outer ring RIGHT+32..+96 / LEFT-96..-32", "camera-relative", "D",
            "RIGHT + 32 .. RIGHT + 96", "creation ring must sit outside the displayed width or objects pop in", "high", CR),
        row("lifecycle", "scan period 4 updates", "$16D9 (CP 4)", "placement scan every 4th object update", "time", "B", "28 px max camera travel per scan < 64 px ring", "ring width must exceed 4 x max camera speed", "high", ST),
        row("lifecycle", "spawn/despawn tested on the anchor only", "$61EE..$6217", "single point (anchor X,Y), not sprite extents", "world anchor", "D", "none", "sprite size is not part of the window", "high", CR),
        # --- player-relative
        row("type $27", "proximity |dx| < 64", "$89BF (LD BC,$0040), call $89C2 -> $0383", "state 1 -> 2 when the post-move anchor is within 63 px of the player", "player-relative world distance", "G", "none", "unchanged by the view", "high", CR),
        row("type $27", "removal |dx| >= 384 (state 3)", "$8A29 (LD BC,$0180), call $8A2C -> $0383", "type $FE when 384 px or more from the player", "player-relative world distance", "G",
            "384 is NOT derived from the view: it is player-relative; it equals the window's right extent only numerically", "keep as player distance; it exceeds any visible offset from the player (<= 255 left of the camera origin)", "high", CR),
        row("type $28", "persistence radius 640 x 672", "$8908 (BC=$0280/$02A0)", "with keep-alive bit 1: removed when |dx| >= 640 or |dy| >= 672 from the player", "player-relative world distance", "G", "2.5 x 256 numerically only", "player distance, unaffected", "high", CR),
        row("type $26 / $09 / $10 / $21", "contact / proximity", "per object docs", "bespoke player proximity or shared overlap $6328", "player-relative", "G", "none", "none", "high", "see object docs"),
        # --- boss / controllers
        row("type $50", "trigger |dx|<160, |dy|<256", "$9771..$9799, table $97A1 (bank $1E)", "boss starts when the player is within 160 px horizontally", "player-relative world distance", "G", "160 = 128 + 32 numerically", "player distance", "high", CR),
        row("type $50", "pan target boss + (-256, -160)", "$9808 table row 0", "boss anchor sits at screen X 256 (= RIGHT edge) when the arena camera arrives", "anchor-relative", "C",
            "RIGHT (zone 0). Rows 1..5: 192, 224, 208, 128, 128 (users untraced)", "a boss that 'enters at the right edge' needs RIGHT = displayed width, but its patrol below is fixed on the locked camera", "high", ST),
        row("type $50", "patrol turn at screen X $38 / $C8; patrol entry $80..$DF", "$9878, $9884, $9A0F", "low byte of (anchor - camera) with the camera locked at 1679", "camera-relative, camera locked", "B",
            "left-origin; equals a fixed world interval while the camera is locked", "arena positions are world-fixed; keep the locked camera's left edge or convert via the lock value", "high", CR),
        row("type $50", "arena locks", "$8199 call $0353, $81D3 call $035C, $D282 saved/restored", "left limit raised to the camera, right limit lowered to the camera", "camera lock", "B", "arena = displayed window", "locked arena width follows the displayed width", "high", ST),
        row("generic", "screen X low-byte compares", "see future sites", "8-bit compares on (anchor - camera)", "camera-relative 8-bit", "C", "assume 0..255", "8-bit wrap hazard; use full-width integer screen X", "medium", ST),
    ]


def object_type_table() -> list[dict]:
    def row(type_id, tests, classes, adaptation, evidence):
        return {"type": type_id, "viewport_relevant_tests": tests, "classes": classes, "widescreen_adaptation": adaptation, "evidence": evidence}

    gen = "generic lifecycle only"
    return [
        row("$09", ["lifecycle window ($61E1, $8000)", "bespoke player proximity for collection"], ["D", "G"], gen + " (shared adapter)", "SOURCE-TRACED + CONTROLLED"),
        row("$10", ["lifecycle window", "shared overlap $6328 against the player"], ["D", "G"], gen, "SOURCE-TRACED + CONTROLLED"),
        row("$18", ["state 1 waits for bit 6 clear (active band)", "left lock $0353 each gated update", "pan target (signX-$80, signY-$99)", "contact box is world-space"],
            ["D", "B", "C", "A"], "yes: sign pan target = CENTRE of the displayed width (cam = signX - view/2, then -1 from the exclusive limit); lifecycle generic", "CONTROLLED + EMULATED"),
        row("$19", ["X = cam + $104 -> cam + $85, Y = camY + $50"], ["C", "E"], "yes: express as RIGHT + 4 and CENTRE + 5 (screen-anchored banner)", "CONTROLLED"),
        row("player state $20", ["camera freeze at d > $F8", "flag at d > $120 (= RIGHT + 33)", "no edge clamp in this state"], ["C", "B"], "yes: RIGHT + 33 (already adopted by the POC); freeze at RIGHT - 7", "CONTROLLED + EMULATED"),
        row("$21", ["lifecycle window", "world-space patrol and contact"], ["D", "A"], gen, "SOURCE-TRACED + CONTROLLED"),
        row("$26", ["lifecycle window", "bespoke player proximity (|dx| < 12 in $82C9)"], ["D", "G"], gen, "SOURCE-TRACED"),
        row("$27", ["create ring RIGHT+32..+96 and wake at RIGHT+32 (generic)", "|dx| < 64 trigger and |dx| >= 384 removal against the player"], ["D", "G"],
            "yes, through the generic lifecycle adapter only: wake/creation rings at RIGHT + 32 / +96 of the displayed width; canonical placement, trigger 64 and removal 384 unchanged", "CONTROLLED + EMULATED"),
        row("$28", ["lifecycle window", "persistence radius 640 x 672 from the player when bit 1 set"], ["D", "G"], gen, "CONTROLLED"),
        row("$50", ["trigger |dx|<160 from the player", "pan target boss + (-256,-160): boss anchor at the RIGHT edge", "patrol/entry thresholds on screen X ($38, $C8, $80..$DF) with the camera locked",
                    "left/right locks to the camera (arena = displayed window)"], ["G", "C", "B"],
            "yes (boss, later task): arena camera lock and the 'enters at RIGHT' relation must be expressed once; the patrol thresholds are world-fixed while the camera is locked", "SOURCE-TRACED + CONTROLLED + EMULATED"),
    ]


UNRESOLVED = [
    "Whether the follow leads 104/136 were tuned to the 256-px width or are independent preferences; no ROM relation beyond the numbers.",
    "Whether the player clamp literals 16 and 247 are intentionally mask(8)+extent(8) and 255-extent(8); the code uses literals, not extents.",
    "Which boss types use pan-table rows 1..5 and trigger-table rows 1..5 (the table exists for zones 0..6; only zone 0 / type $50 is exercised).",
    "Mechanics of the screen-relative sites in other zones' boss/object code (FUTURE_SITES); only instruction semantics are recorded.",
    "Type $1C: writes absolute world X $C0..$DF / Y $20..$9F when screen X < $30; its coordinate frame and use are not traced.",
    "Level-end camera relationship for zones 7/8 (special stages: right limits 7936/16128, bottom 16) not traced.",
    "How the vertical constants (bottom limit = height - 240, bands 256 tall, pit death screen Y $D8) relate to 192/224/240-line modes.",
    "Second camera-release step in the act-clear chain and what $0407 (freeze) does to follow after the results screen: the engine state is cleared by $4FCE.",
    "Behaviour of $27 contact reach and POC-side widescreen choices are outside this audit.",
]


# --------------------------------------------------------------------------- #
# 7. build
# --------------------------------------------------------------------------- #
def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    out = {
        "format": 1, "rom_sha256": ROM_SHA256, "research_only": True, "poc_untouched": True, "machine_facing_label": "viewport_semantics",
        "evidence_classes": EVIDENCE, "classes": CLASSES,
        "reference_frame": {
            "window_width_px": VIEW_W, "right_edge_definition": "RIGHT = cam + 256 (exclusive); last visible column = cam + 255",
            "active_lines": 192, "left_mask_px_by_r0_bit5": 8,
            "camera_origin": "left edge of the window", "d_definition": "d = world X - camera X",
        },
        "routines": routine_table(rom),
        "spawn_map": spawn_map(rom),
        "level_limits": level_limits(rom),
        "boss_tables": boss_tables(rom),
        "future_risk_scan": future_scan(rom),
        "constants": constants_table(),
        "object_types": object_type_table(),
        "unresolved": UNRESOLVED,
        "static_only": static_only,
    }
    if not static_only:
        lab = Lab(rom)
        out["lifetime_fixture"] = lifetime_fixture(lab)
        out["placement_scan_fixture"] = scan_fixture(Lab(rom))
        out["camera_follow_fixture"] = follow_fixture(Lab(rom))
        out["camera_pan_fixture"] = pan_fixture(Lab(rom))
        out["camera_limit_fixture"] = limit_fixture(Lab(rom))
        out["player_edge_clamp_fixture"] = clamp_fixture(Lab(rom))
        out["state20_fixture"] = state20_fixture(Lab(rom))
        out["child19_fixture"] = child19_fixture(rom)
        out["player_distance_fixture"] = player_distance_fixture(Lab(rom))
        out["emulated_act_clear_camera"] = emulated_act_clear_camera(rom)
        out["emulated_bee_scroll"] = emulated_bee_scroll(rom)
        out["emulated_vdp"] = emulated_vdp(rom)
    return out


def markdown_table(cache: dict) -> str:
    lines = ["| system | constant | ROM address | raw meaning | coordinate frame | 256px relationship | widescreen implication | class | confidence |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in cache["constants"]:
        cells = [r["system"], r["constant"], r["rom_address"], r["raw_meaning"], r["coordinate_frame"], r["relationship_to_256px"],
                 r["widescreen_implication"], r["class"], r["confidence"]]
        lines.append("| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", nargs="?", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    a = ap.parse_args()
    if a.markdown:
        print(markdown_table(json.loads(OUTPUT.read_text(encoding="utf-8"))))
        return
    if a.rom is None:
        ap.error("ROM path required")
    rom = a.rom.read_bytes()
    data = build(rom, a.static_only)
    text = json.dumps(data, indent=1, sort_keys=False) + "\n"
    if a.check:
        cached = OUTPUT.read_text(encoding="utf-8")
        if a.static_only:
            cj = json.loads(cached)
            dj = json.loads(text)
            keys = [k for k in dj if k in cj and k != "static_only"]
            bad = [k for k in keys if cj[k] != dj[k]]
        else:
            bad = [] if cached == text else ["file"]
        print("OK: cache matches the ROM" if not bad else f"MISMATCH in {bad}")
        sys.exit(1 if bad else 0)
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT} ({len(text)} bytes)")


if __name__ == "__main__":
    main()

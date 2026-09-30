#!/usr/bin/env python3
"""Study of THZ1/THZ2 object type $18 (goal sign) and the act-clear chain (research only, deterministic).

Everything is recomputed from the checked ROM. The output is data/rom-cache/object-18-act-clear.json
(machine-facing: numeric labels only).

Evidence classes (same vocabulary as the earlier studies):
  DECODED DATA, BYTE-VERIFIED ASSEMBLY (routine bytes hashed per region and disassembled by hand),
  SOURCE-TRACED BEHAVIOR (read from the disassembly), CONTROLLED ROUTINE RESULT (original Z80 routines
  executed on kosarev/z80 with explicit RAM, tools/oracle.py), EMULATED ORIGINAL FRAME (the complete
  original game booted in tools/sms_frame_harness.py), UNRESOLVED.

Usage:
  python tools/object_18.py ROM.sms                 # write the cache
  python tools/object_18.py ROM.sms --check         # compare with the cache
  python tools/object_18.py ROM.sms --static-only   # no Z80 execution
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OUTPUT = ROOT / "data" / "rom-cache" / "object-18-act-clear.json"
TYPE_SIGN = 0x18
TYPE_CHILD = 0x19
BANK = 0x0C            # object code/state bank for types < $26
SLOT = 0xD700          # slot used by the controlled fixtures (index 7 of the 19-slot pool)
PLACEMENT = {          # (act, ROM offset of the 9-byte record, index0 in its list)
    "thz1": (0x70782, 52),
    "thz2": (0x708F4, 40),
}


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


anim = _load("thz1_animation_reach")


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def u16(rom: bytes, pos: int) -> int:
    return rom[pos] | (rom[pos + 1] << 8)


def s16(v: int) -> int:
    return v - 65536 if v >= 32768 else v


def rom_of(bank: int, cpu: int) -> int:
    """File offset of a CPU address (slot 0/1 = fixed banks 0/1, slot 2 paged)."""
    if cpu < 0x8000:
        return cpu
    return bank * 0x4000 + cpu - 0x8000


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM")


EVIDENCE = {
    "DECODED DATA": "ROM tables/records decoded by a parser",
    "BYTE-VERIFIED ASSEMBLY": "routine bytes compared literally and disassembled by hand",
    "SOURCE-TRACED BEHAVIOR": "behavior read from the disassembly, not executed",
    "CONTROLLED ROUTINE RESULT": "original routine executed on a Z80 core with explicit RAM",
    "EMULATED ORIGINAL FRAME": "whole original game run in the approximate SMS harness",
    "UNRESOLVED": "not established",
}

# --------------------------------------------------------------------------- #
# 1. static facts
# --------------------------------------------------------------------------- #
# (name, bank, first CPU, end CPU exclusive, kind, purpose)
ROUTINES = [
    # type $18 (bank $0C)
    ("goal_state0_init", 0x0C, 0xA867, 0xA873, "code", "state 0 callback: +$03 bit 7, clear +$34/+$35"),
    ("goal_state1_wait_onscreen", 0x0C, 0xA873, 0xA87D, "code", "state 1 callback: wait until +$04 bit 6 clear, request state 2"),
    ("goal_state2_art_selector", 0x0C, 0xA87D, 0xA88E, "code", "state 2 callback: $D3B3 = $12; player requested state $12 -> $0E"),
    ("goal_state3_contact", 0x0C, 0xA88E, 0xA8C4, "code", "state 3 callback: gate, left camera lock, overlap helper, contact effects"),
    ("goal_camera_left_lock_call", 0x0C, 0xA8C4, 0xA8C8, "code", "CALL vector $0353 (D280 = max(D280, camera X))"),
    ("goal_state4_entry_hook", 0x0C, 0xA8C8, 0xA8CE, "code", "state 4 first record callback: $D4A3 = $FF"),
    ("goal_state4_hop_fall", 0x0C, 0xA8CE, 0xA8FA, "code", "state 4 spin callback: accelerate Y (+$10, max $600), move, land at saved Y"),
    ("goal_landing_prize", 0x0C, 0xA8FA, 0xA919, "code", "landing: request state 5, prize lookup by zone parity"),
    ("goal_prize_table_zone_even_index", 0x0C, 0xA919, 0xA959, "data", "4 rows x 16 BCD ring counts (used when ($D297+1) is odd: zone 0 = THZ)"),
    ("goal_prize_table_select_other", 0x0C, 0xA959, 0xA962, "code", "selects the second table"),
    ("goal_prize_table_zone_odd_index", 0x0C, 0xA962, 0xA9A2, "data", "second table (zone 1)"),
    ("goal_prize_dispatch", 0x0C, 0xA9A2, 0xA9EC, "code", "+$34 class -> reward and $D3B3 face selector"),
    ("goal_prize_retry_setup", 0x0C, 0xA9EC, 0xA9FA, "code", "class 0: +$35 = $FF, $D3B3 = $20, back to state 3"),
    ("goal_prize_lookup_cpir", 0x0C, 0xA9FA, 0xAA16, "code", "CPIR of $D29A in the 64-byte table -> +$34"),
    ("goal_prize_random_roll", 0x0C, 0xAA16, 0xAA22, "code", "+$34 = ($D12F & 7) + 1 after a retry"),
    ("goal_camera_pan_lock", 0x0C, 0xAA22, 0xAA47, "code", "vector $0359 with target (X - $80, Y - $99)"),
    ("goal_spawn_child_19", 0x0C, 0xAA47, 0xAA4F, "code", "state 5 script: allocate type $19 through vector $032C"),
    # type $19 (bank $0C)
    ("c19_state_table_and_scripts", 0x0C, 0xAA4F, 0xAA87, "data", "type $19 state table (5 states) and scripts"),
    ("c19_state0_init", 0x0C, 0xAA87, 0xAAC0, "code", "copy text/palette blocks, position off the right edge, bit 7, state 1"),
    ("c19_init_blocks", 0x0C, 0xAAC0, 0xAAE4, "data", "16-byte and 20-byte initial RAM blocks"),
    ("c19_state1_scroll_in", 0x0C, 0xAAE4, 0xAB0A, "code", "move left 8 px per update until X <= cameraX + $85"),
    ("c19_state2_digit_roll", 0x0C, 0xAB0A, 0xAB2A, "code", "cycle the three result digits"),
    ("c19_digit_table", 0x0C, 0xAB2A, 0xAB48, "data", "10 x 3 digit tile triples"),
    ("c19_state3_bonus_compute", 0x0C, 0xAB48, 0xAB8C, "code", "$041F value -> $D2A6; three equal digits call $03F2"),
    ("c19_state4_wait_floor_complete", 0x0C, 0xAB8C, 0xAB9F, "code", "player on floor -> vector $03F5 (player state $20)"),
    # player state $20 and level-complete setter
    ("player_state20_script", 0x0C, 0x839E, 0x83A6, "data", "player state $20 script: FF 05 (call/set callback), FF 00"),
    ("player_state20_handler", 0x0C, 0x83A6, 0x840F, "code", "run right; sets $D293 bit 5 (act idx < 2) or bit 4 once far off screen"),
    ("level_complete_setter", 0x01, 0x4892, 0x48A7, "code", "vector $03F5: $D502 = $20, sound $89 (or $97 when $D298 = 2)"),
    ("camera_release_thunk", 0x01, 0x59B9, 0x59C5, "code", "vector $0407: RES 7,$D15E; $D280 = camera X"),
    ("camera_pan_setter", 0x01, 0x59C5, 0x59D8, "code", "vector $0359: $D15E bit 7, $D15F bit 0, $D2DA = BC, $D2DC = DE"),
    ("camera_left_lock", 0x01, 0x59E3, 0x59F3, "code", "vector $0353: D280 = max(D280, camera X)"),
    ("y_accelerate_clamp", 0x01, 0x5F84, 0x5FA0, "code", "vector $0350: +$18/+$19 += DE, clamped to BC"),
    ("overlap_helper", 0x01, 0x6328, 0x640B, "code", "vector $033B: shared overlap, contact bits in +$21"),
    ("player_type_fix", 0x01, 0x613C, 0x614E, "code", "vector $037D: non-Sonic player requested state $18 -> $0E"),
    ("object_visibility", 0x01, 0x61E1, 0x6276, "code", "post-update visibility / removal"),
    ("bonus_value_lookup", 0x00, 0x6276, 0x62AD, "code", "vector $041F: $D2BF time + $D29A rings -> HL"),
    ("bonus_time_table", 0x00, 0x62AD, 0x62D5, "data", "10 x (BCD time limit, bonus high byte)"),
    # main loop / timer / results (bank 0)
    ("main_loop_dispatch", 0x00, 0x1333, 0x1365, "code", "$D293 bit dispatcher (RLCA chain), frame update otherwise"),
    ("act_clear_sequence_bit5", 0x00, 0x14AE, 0x1543, "code", "$D293 bit 5: act-clear sequence, then $D298 += 1, bit 1"),
    ("zone_clear_sequence_bit4", 0x00, 0x1543, 0x15F2, "code", "$D293 bit 4: act 3 / zone-clear sequence"),
    ("level_frame_update", 0x00, 0x16B8, 0x16EF, "code", "per-frame player/object update used while $D293 selects gameplay"),
    ("timer_tick", 0x00, 0x27EE, 0x285C, "code", "frame interrupt: advance the BCD level timer while $D2BE != 0"),
    ("results_screen_draw", 0x00, 0x32F9, 0x33F1, "code", "act-clear screen: draw, tally, wait"),
    ("results_ring_bonus_tally", 0x00, 0x2D08, 0x2D55, "code", "count $D29A rings and the $D2A6 bonus down, awarding points"),
    ("reward_counter_3104", 0x00, 0x3104, 0x3138, "code", "vector $03F2: sound $A9, $D299 += 1 (BCD, max $99)"),
]

STATE_NAMES = {}   # no names: numeric labels only


def routine_table(rom: bytes) -> list[dict]:
    out = []
    for name, bank, start, end, kind, purpose in ROUTINES:
        off = rom_of(bank, start)
        raw = rom[off:off + (end - start)]
        out.append({
            "name": name, "kind": kind, "purpose": purpose,
            "bank": h(bank, 2), "cpu": h(start), "cpu_end_exclusive": h(end),
            "rom_offset": h(off, 5), "length": end - start,
            "first_16_bytes": raw[:16].hex(), "sha256": sha(raw),
            "evidence": "BYTE-VERIFIED ASSEMBLY" if kind == "code" else "DECODED DATA",
        })
    return out


def placement(rom: bytes) -> dict:
    out = {"evidence": "DECODED DATA + BYTE-VERIFIED ASSEMBLY (creator $700EB)", "records": {}}
    for act, (off, idx0) in PLACEMENT.items():
        raw = rom[off:off + 9]
        out["records"][act] = {
            "rom_offset": h(off, 5), "bank": "0x1C", "cpu": h(0x8000 + off - 0x70000), "index_0_based": idx0,
            "raw_bytes": raw.hex(" ").upper(), "type_id": h(raw[0], 2),
            "stored_x": u16(rom, off + 1), "stored_y": u16(rom, off + 3),
            "world_x": u16(rom, off + 1) - 256, "world_y": u16(rom, off + 3) - 256,
            "flags": h(raw[5], 2), "parameter": h(raw[6], 2), "aux0": h(raw[7], 2), "aux1": h(raw[8], 2),
        }
    a, b = (out["records"][k] for k in ("thz1", "thz2"))
    out["thz1_thz2_identical_except_position"] = (
        a["raw_bytes"][:2] == b["raw_bytes"][:2] and a["raw_bytes"][-14:] == b["raw_bytes"][-14:]
        and a["stored_x"] == b["stored_x"])
    out["thz1_thz2_y_difference"] = b["world_y"] - a["world_y"]
    # cross-check against the level-package caches (type counts: THZ1 1, THZ2 1, THZ3 0)
    counts = {}
    for act in ("thz2", "thz3"):
        objs = json.loads((ROOT / f"data/rom-cache/levels/{act}/objects.json").read_text(encoding="utf-8"))
        counts[act] = sum(1 for r in objs["records"] if r["type_id"] == "0x18")
        if act == "thz2":
            rec = [r for r in objs["records"] if r["type_id"] == "0x18"][0]
            out["records"]["thz2"]["matches_level_package"] = rec["raw_bytes"] == out["records"]["thz2"]["raw_bytes"]
    thz1 = json.loads((ROOT / "data/rom-cache/thz1/object-records.json").read_text(encoding="utf-8"))["records"]
    counts["thz1"] = sum(1 for r in thz1 if r["type_id"] == "0x18")
    out["records"]["thz1"]["matches_level_package"] = any(
        r["type_id"] == "0x18" and r["raw_bytes"] == out["records"]["thz1"]["raw_bytes"] for r in thz1)
    out["count_per_act"] = {k: counts[k] for k in ("thz1", "thz2", "thz3")}
    return out


def _states(rom: bytes, type_id: int) -> dict:
    table = anim.animation_state_table(rom, type_id)
    trace = anim.trace_type(rom, type_id)
    states = []
    for st in trace["states"]:
        states.append({
            "state": st["state_index"], "script_cpu": st["script_cpu"], "script_rom": st["script_rom"],
            "frames": st["frame_indices"], "unresolved": st["unresolved"],
            "records": [{"cpu": r["cpu"], "raw": r["raw"], "duration": r["duration"], "frame": r["frame_index"],
                         "callback": r["callback_cpu"]} for r in st["records"]],
            "commands": [{k: v for k, v in c.items() if k not in ("rom",)} for c in st["commands"]],
        })
    return {"state_table_cpu": h(table["state_table_cpu"]), "state_table_rom": h(table["state_table_rom"], 5),
            "state_count": table["state_count"], "states": states}


def dispatch(rom: bytes) -> dict:
    out = {"evidence": "BYTE-VERIFIED ASSEMBLY + DECODED DATA",
           "chain": [
               "placement creator $80EB (bank $1C) writes type $18 into a slot, state 0",
               "scheduler $5DF1: type < $26 -> map bank $0C, CALL $64FA (animation engine), CALL $5E91 (callback), then $61E1",
               "animation engine: state table = word at $65BA + (type-1)*2; state script = word at table + 2*state",
               "script record (duration, frame, callback word) sets +$0C/+$0D; $5E91 jumps to the callback each update",
           ]}
    for t in (TYPE_SIGN, TYPE_CHILD):
        entry = 0x65BA + (t - 1) * 2
        mp = 0x3C000 + t * 2
        d = _states(rom, t)
        d.update({"type_table_entry_rom": h(entry, 5), "type_table_entry_value": h(u16(rom, entry)),
                  "mapping_pointer_rom": h(mp, 5), "mapping_pointer_value": h(u16(rom, mp)),
                  "mapping_bank": "0x0F", "mapping_rom": h(0x3C000 + u16(rom, mp) - 0x8000, 5)})
        out[h(t, 2)] = d
    return out


def frame_extents(rom: bytes) -> dict:
    """Contact extents (+$2C/+$2D) copied by the animation engine from the mapping frame record bytes 1/2."""
    out = {}
    for t, frames in ((TYPE_SIGN, range(6)), (TYPE_CHILD, range(2))):
        mp = 0x3C000 + u16(rom, 0x3C000 + t * 2) - 0x8000
        rows = []
        for f in frames:
            rec = 0x3C000 + u16(rom, mp + 2 * f) - 0x8000
            rows.append({"frame": f, "record_rom": h(rec, 5), "byte0": rom[rec], "extent_x": rom[rec + 1], "extent_y": rom[rec + 2]})
        out[h(t, 2)] = rows
    return out


def prize_tables(rom: bytes) -> dict:
    a = rom[rom_of(BANK, 0xA919):rom_of(BANK, 0xA919) + 64]
    b = rom[rom_of(BANK, 0xA962):rom_of(BANK, 0xA962) + 64]

    def rows(t):
        return [[x for x in t[i * 16:(i + 1) * 16] if x != 0xFF] for i in range(4)]
    return {
        "evidence": "DECODED DATA (bytes) + BYTE-VERIFIED ASSEMBLY ($A9FA CPIR)",
        "selection": "LD A,($D297); INC A; RRCA; carry -> table at $A919, no carry -> table at $A962 (zone parity, NOT act)",
        "thz_zone_index": 0,
        "thz_table_cpu": "0xA919",
        "rows_thz_table": [[f"{x:02X}" for x in r] for r in rows(a)],
        "other_table_cpu": "0xA962",
        "rows_other_table": [[f"{x:02X}" for x in r] for r in rows(b)],
        "class_rule": "class = 3 - (index_of_first_match // 16) where index is the CPIR position (0..63) of the BCD ring count $D29A; no match = $FF",
        "bonus_time_table": [{"time_limit_bcd": f"{u16(rom, 0x62AD + 4 * i):04X}", "bonus_high_byte": f"{rom[0x62AF + 4 * i + 1]:02X}",
                              "bytes": rom[0x62AD + 4 * i:0x62AD + 4 * i + 4].hex(" ")} for i in range(10)],
    }


# --------------------------------------------------------------------------- #
# 2. controlled routine fixtures (original Z80 code, explicit RAM)
# --------------------------------------------------------------------------- #
class Fixture:
    """Thin wrapper over tools/oracle.py for the goal sign."""

    def __init__(self, rom: bytes, act: str = "thz1"):
        from oracle import Oracle
        self.rom = rom
        self.o = Oracle(rom)
        self.m = self.o.mem
        self.act = act
        off, idx0 = PLACEMENT[act]
        self.rec_cpu = 0x8000 + off - 0x70000
        self.occupancy = 0xD400 + idx0
        self.sx = u16(rom, off + 1) - 256
        self.sy = u16(rom, off + 3) - 256
        self.m[0xD52C], self.m[0xD52D] = 8, 24        # Sonic extents measured in the emulated game (docs)
        self.m[0xD500] = 1
        self.o.word(0xD174, self.sx - 128)
        self.o.word(0xD176, self.sy - 153)
        for a, v in ((0xD280, 0), (0xD282, 4300), (0xD27C, 8), (0xD27E, 900)):
            self.o.word(a, v)
        self.m[0xD297] = 0
        self.m[0xD298] = 0 if act == "thz1" else 1
        self.m[0xD29A] = 0
        self.m[0xD2BE] = 0xFF
        self.snapshot = None

    def create(self):
        self.o.bank(2, 0x1C)
        self.m[0xD12B] = 0x1C
        self.m[SLOT:SLOT + 0x40] = bytes(0x40)
        self.o.cpu.ix = SLOT
        self.o.cpu.hl = self.rec_cpu
        self.o.call(0x80EB, bc=self.occupancy)

    def r(self, off, n=1):
        return sum(self.m[SLOT + off + i] << (8 * i) for i in range(n))

    def w(self, off, v, n=1):
        for i in range(n):
            self.m[SLOT + off + i] = (v >> (8 * i)) & 255

    def player(self, x, y, vx=0, vy=0, req=2, flags=0, ex=8, ey=24):
        self.o.word(0xD511, x)
        self.o.word(0xD514, y)
        self.o.word(0xD516, vx)
        self.o.word(0xD518, vy)
        self.m[0xD502] = req
        self.m[0xD503] = flags
        self.m[0xD52C], self.m[0xD52D] = ex, ey

    def update_slot(self):
        self.m[0xD12B] = BANK
        self.o.cpu.ix = SLOT
        self.o.call(0x5DF1)

    def update_all(self):
        self.o.call(0x5DD1)

    def call_cb(self, cpu, slot=SLOT):
        self.o.bank(2, BANK)
        self.m[0xD12B] = BANK
        self.o.cpu.ix = slot
        self.o.call(cpu)

    def save(self):
        self.snapshot = bytes(self.m[0xC000:0xE000])

    def restore(self):
        self.m[0xC000:0xE000] = self.snapshot

    def snap(self):
        return {"state": self.r(1), "requested": self.r(2), "frame": self.r(6), "timer": self.r(7),
                "callback": h(self.r(0x0C, 2)), "x": self.r(0x11, 2), "y": self.r(0x14, 2),
                "vy": s16(self.r(0x18, 2)), "flags_03": h(self.r(3), 2), "flags_04": h(self.r(4), 2),
                "ext_x": self.r(0x2C), "ext_y": self.r(0x2D), "prize_34": self.r(0x34), "retry_35": self.r(0x35)}


def ready_at_state3(rom: bytes, act: str = "thz1") -> Fixture:
    f = Fixture(rom, act)
    f.create()
    f.player(f.sx - 600, f.sy, req=2)
    for _ in range(5):
        f.update_slot()
    assert f.r(1) == 3 and f.r(2) == 3, "sign did not reach state 3"
    f.save()
    return f


def predicted_contact(dx: int, dy: int, ex: int, ey: int, obj_ex: int = 12, obj_ey: int = 42) -> bool:
    """Exact rule derived from $6328 (see docs/object-18-act-clear.md)."""
    span = (ex + obj_ex) & 0xFF
    if dx >= 0:
        horiz = dx < 256 and dx <= span
    else:
        horiz = dx > -256 and -dx <= span
    if dy >= 0:
        vert = dy < 256 and dy <= ey
    else:
        vert = dy > -256 and -dy <= obj_ey
    return horiz and vert


def contact_trial(f: Fixture, dx: int, dy: int, vx: int = 0x0400, req: int = 2, flags: int = 0,
                  ex: int = 8, ey: int = 24, retry: int = 0) -> bool:
    f.restore()
    f.player(f.sx + dx, f.sy + dy, vx=vx, req=req, flags=flags, ex=ex, ey=ey)
    f.w(0x35, retry)
    f.call_cb(0xA88E)
    return f.r(2) != 3


def contact_fixtures(rom: bytes) -> dict:
    out = {"evidence": "CONTROLLED ROUTINE RESULT"}
    f = ready_at_state3(rom, "thz1")
    out["state3_entry"] = {"snapshot": f.snap(), "note": "frame 1 record bytes give +$2C = 12, +$2D = 42"}

    # --- exact boundary grid, Sonic extents (8,24) -------------------------------------------
    grid = {}
    mism = 0
    total = 0
    for (ex, ey) in ((8, 24), (9, 24), (0, 0), (8, 18), (9, 18)):
        rows = {}
        for dy in range(-50, 31):
            dxs = [dx for dx in range(-40, 41) if contact_trial(f, dx, dy, ex=ex, ey=ey)]
            for dx in range(-40, 41):
                total += 1
                if (dx in dxs) != predicted_contact(dx, dy, ex, ey):
                    mism += 1
            rows[dy] = (min(dxs), max(dxs), len(dxs)) if dxs else None
        hits = {dy: v for dy, v in rows.items() if v}
        grid[f"{ex},{ey}"] = {
            "player_extent_x_D52C": ex, "player_extent_y_D52D": ey,
            "contact_dy_min": min(hits), "contact_dy_max": max(hits),
            "contact_dx_min": min(v[0] for v in hits.values()), "contact_dx_max": max(v[1] for v in hits.values()),
            "rows_contiguous_and_equal": all(v[2] == v[1] - v[0] + 1 for v in hits.values())
            and len({(v[0], v[1]) for v in hits.values()}) == 1,
            "dy_rows_with_contact": len(hits),
        }
    out["boundary_grid"] = {
        "grid_dx": [-40, 40], "grid_dy": [-50, 30], "cells_checked": total, "mismatches_vs_formula": mism,
        "formula": "contact = |dx| <= (playerExtX + 12) and -42 <= dy <= playerExtY, dx = playerX - signX, dy = playerY - signY",
        "by_player_extents": grid,
    }

    # --- edge and far-range cases -----------------------------------------------------------------
    edges = []
    for dx, dy in ((20, 0), (21, 0), (-20, 0), (-21, 0), (0, 24), (0, 25), (0, -42), (0, -43),
                   (255, 0), (256, 0), (-255, 0), (-256, 0), (300, 0), (-300, 0), (0, 255), (0, -255), (0, -256), (0, 300)):
        edges.append({"dx": dx, "dy": dy, "contact": contact_trial(f, dx, dy), "formula": predicted_contact(dx, dy, 8, 24)})
    out["edge_cases_sonic_8_24"] = edges

    # --- gating: movement / requested state / flags ------------------------------------------------
    gates = []
    for name, kw in (
        ("moving_right", dict(vx=0x0400)),
        ("moving_left_negative_speed", dict(vx=0xFC00)),
        ("slowest_nonzero_speed_0001", dict(vx=0x0001)),
        ("standing_still_requested_2", dict(vx=0, req=2)),
        ("standing_still_requested_18", dict(vx=0, req=0x18)),
        ("moving_requested_18", dict(vx=0x0400, req=0x18)),
        ("standing_still_requested_12", dict(vx=0, req=0x12)),
        ("moving_ball_flags_02", dict(vx=0x0400, flags=0x02)),
        ("moving_airborne_flags_01", dict(vx=0x0400, flags=0x01)),
        ("moving_with_D503_bit6", dict(vx=0x0400, flags=0x40)),
        ("standing_still_with_D503_bit6_req_18", dict(vx=0, req=0x18, flags=0x40)),
    ):
        gates.append({"case": name, "contact_triggered": contact_trial(f, 0, 0, **kw)})
    out["gating_at_dx0_dy0"] = gates

    # --- player y velocity is not used ---------------------------------------------------------------
    f.restore()
    f.player(f.sx, f.sy, vx=0x0400, vy=0x0800)
    f.call_cb(0xA88E)
    out["y_velocity_ignored"] = {"contact_with_vy_0800": f.r(2) != 3}

    # --- state after contact, first touch (+$35 = 0) and retouch (+$35 != 0) -------------------------
    effects = {}
    for name, retry in (("first_touch", 0), ("retouch_after_retry", 0xFF)):
        f.restore()
        f.m[0xD2BE] = 0xFF
        f.m[0xD445] = 0x55
        f.m[0xD2BF] = 0x34                      # elapsed seconds BCD (low), unchanged by the contact
        f.o.word(0xD280, 100)
        f.o.word(0xD174, f.sx - 100)
        f.player(f.sx - 10, f.sy - 3, vx=0x0400)
        f.w(0x35, retry)
        f.w(0x18, 0x1234, 2)
        f.m[0xD2BE] = 0xFF
        f.m[0xD15E] = 0
        f.m[0xD15F] = 0
        f.call_cb(0xA88E)
        effects[name] = {
            "requested_state": f.r(2), "timer_flag_D2BE": f.m[0xD2BE], "D445": f.m[0xD445],
            "sign_y_velocity_hi_19": h(f.r(0x19), 2), "sign_y_velocity_lo_18": h(f.r(0x18), 2),
            "left_limit_D280": f.o.word(0xD280), "camera_x_D174": f.o.word(0xD174),
            "pan_flags_D15E_D15F": [h(f.m[0xD15E], 2), h(f.m[0xD15F], 2)],
            "pan_target_D2DA_D2DC": [f.o.word(0xD2DA), f.o.word(0xD2DC)],
            "player_requested_state_D502": h(f.m[0xD502], 2), "player_x_unchanged": f.o.word(0xD511) == f.sx - 10,
            "timer_value_D2BF_unchanged": h(f.m[0xD2BF], 2), "contact_bits_21": h(f.r(0x21) & 0xF, 2),
            "contact_bits_20": h(f.r(0x20), 2),
        }
    out["contact_effects"] = effects

    # --- left camera lock while waiting (no contact) --------------------------------------------------
    f.restore()
    f.o.word(0xD280, 100)
    f.o.word(0xD174, 3850)
    f.player(f.sx - 300, f.sy, vx=0)
    f.call_cb(0xA88E)
    out["left_lock_while_waiting"] = {"D280_after": f.o.word(0xD280), "camera_x": 3850,
                                      "rule": "state 3 runs $0353 every update only when the gate passes (moving or requested state $18)"}
    f.restore()
    f.o.word(0xD280, 100)
    f.o.word(0xD174, 3850)
    f.player(f.sx - 300, f.sy, vx=0x0400)
    f.call_cb(0xA88E)
    out["left_lock_while_waiting"]["D280_after_moving"] = f.o.word(0xD280)
    return out


def hop_fixture(rom: bytes, act: str) -> dict:
    """Run the original scheduler from creation through contact, hop, landing and child spawn."""
    f = ready_at_state3(rom, act)
    f.restore()
    f.m[0xD2BF] = 0x06
    f.player(f.sx - 10, f.sy, vx=0x0400)
    rows = []
    contact_update = None
    sound_log = []
    landing_update = None
    child_update = None
    for u in range(1, 400):
        f.m[0xDE04] = 0
        f.m[0xD3B3] = f.m[0xD3B3]
        if contact_update is not None:
            f.player(f.sx + 200, f.sy, vx=0)              # the player is out of the way afterwards
        f.update_all()
        snd = f.m[0xDE04]
        if snd:
            sound_log.append([u, h(snd, 2)])
        if contact_update is None and f.r(2) == 4:
            contact_update = u
        if contact_update is not None:
            if landing_update is None and f.r(2) == 5:
                landing_update = u
            kid = [i for i in range(19) if f.m[0xD540 + i * 0x40] == TYPE_CHILD]
            if kid and child_update is None:
                child_update = u
            if u - contact_update in (1, 2, 32, 64, 65, 96, 128) or u in (landing_update, child_update):
                rows.append({"update_after_contact": u - contact_update, **f.snap(), "D2BE": f.m[0xD2BE]})
            if child_update is not None and u > child_update + 2:
                break
    ys = [r["y"] for r in rows]
    return {
        "contact_update": contact_update, "landing_update": landing_update, "child_update": child_update,
        "updates_contact_to_landing": landing_update - contact_update,
        "updates_landing_to_child_present": child_update - landing_update,
        "checkpoints": rows, "min_y_seen_in_checkpoints": min(ys),
        "sound_requests_DE04": sound_log[:6] + ["..."] + sound_log[-3:],
        "spin_sound_AA_count": sum(1 for _, v in sound_log if v == "0xAA"),
        "sound_AB_update": next((u - contact_update for u, v in sound_log if v == "0xAB"), None),
        "sound_F8_update": next((u - contact_update for u, v in sound_log if v == "0xF8"), None),
    }


def hop_trace(rom: bytes) -> dict:
    """Y position every update of the hop (THZ1), apex and landing."""
    f = ready_at_state3(rom, "thz1")
    f.restore()
    f.player(f.sx - 10, f.sy, vx=0x0400)
    ys, vys = [], []
    start = None
    for u in range(1, 300):
        if start is not None:
            f.player(f.sx + 200, f.sy, vx=0)
        f.update_all()
        if start is None and f.r(2) == 4:
            start = u
        if start is not None:
            ys.append(f.r(0x14, 2))
            vys.append(s16(f.r(0x18, 2)))
            if f.r(2) == 5:
                break
    apex = min(ys)
    return {"start_y": f.sy, "apex_y": apex, "apex_index": ys.index(apex) + 1, "apex_rise": f.sy - apex,
            "updates": len(ys), "first_y_values": ys[:6], "first_vy_values": vys[:6],
            "max_vy_seen": max(vys), "landing_y": ys[-1],
            "model": "Y velocity starts at $FC00 (+$19 = $FC, +$18 unchanged), += $10 per update (clamp $0600), Y += velocity; "
                     "landing when Y >= saved Y (+$3C/+$3D)"}


def retry_fixture(rom: bytes) -> dict:
    """Class-0 retry: state 3 again, second touch -> state 6 (spin in place) -> random class."""
    f = ready_at_state3(rom, "thz1")
    f.restore()
    f.m[0xD29A] = 0x16                                   # class 0 (retry) on the zone-0 table
    f.m[0xD2C3] = 3
    events = []
    phase = "touch1"
    marks = {}
    for u in range(1, 600):
        near = phase in ("touch1", "touch2")
        f.player(f.sx - 10 if near else f.sx + 300, f.sy, vx=0x0400 if near else 0)
        f.m[0xD12F] = 1                                  # random roll -> class 2 (+10 rings)
        before = (f.r(1), f.r(2))
        f.update_all()
        after = (f.r(1), f.r(2))
        if after != before:
            events.append({"update": u, "phase": phase, "state": after[0], "requested": after[1], "prize_34": f.r(0x34),
                           "retry_35": f.r(0x35), "D3B3": h(f.m[0xD3B3], 2), "rings": h(f.m[0xD29A], 2), "y": f.r(0x14, 2)})
        if phase == "touch1" and after[1] == 4:
            phase, marks["touch1_update"] = "hop", u
        elif phase == "hop" and after == (3, 3):
            phase, marks["back_in_state_3_update"] = "touch2", u
        elif phase == "touch2" and after[1] == 6:
            phase, marks["touch2_update"] = "spin", u
        elif phase == "spin" and after == (5, 5):
            marks["state_5_update"] = u
            break
    return {"evidence": "CONTROLLED ROUTINE RESULT", "marks": marks,
            "updates_touch2_to_state_5": marks["state_5_update"] - marks["touch2_update"], "events": events}


def prize_fixtures(rom: bytes) -> dict:
    f = ready_at_state3(rom, "thz1")
    by_ring = {}
    classes = {}
    for bcd_hi in range(10):
        for bcd_lo in range(10):
            ring = (bcd_hi << 4) | bcd_lo
            f.restore()
            f.w(0x35, 0)
            f.m[0xD29A] = ring
            f.m[0xD2C3] = 3
            f.m[0xD299] = 1
            f.m[0xD500] = 1
            f.m[0xD297] = 0
            f.call_cb(0xA8FA)
            cls = f.r(0x34)
            entry = {"class_34": cls, "D3B3": h(f.m[0xD3B3], 2), "requested_state": f.r(2), "retry_35": f.r(0x35),
                     "rings_after": h(f.m[0xD29A], 2), "D2C3_after": f.m[0xD2C3], "D299_after": f.m[0xD299]}
            by_ring[f"{ring:02X}"] = entry
            classes.setdefault(cls, []).append(f"{ring:02X}")
    # the first pass never gives class 1 through 3 directly for non-matching counts
    out = {"evidence": "CONTROLLED ROUTINE RESULT (original $A8FA on the THZ zone-0 table)",
           "class_to_ring_counts_zone0": {str(k): v for k, v in sorted(classes.items())},
           "effects_by_class": {}}
    # effects per class (sample ring counts)
    for cls, ring in ((255, 0x00), (3, 0x15), (2, 0x09), (1, 0x99), (0, 0x16)):
        for ptype in (1, 2):
            f.restore()
            f.w(0x35, 0)
            f.m[0xD29A] = ring
            f.m[0xD2C3] = 3
            f.m[0xD299] = 1
            f.m[0xD500] = ptype
            f.m[0xD297] = 0
            f.call_cb(0xA8FA)
            out["effects_by_class"][f"class_{cls}_ring_{ring:02X}_player_{ptype}"] = {
                "class_34": f.r(0x34), "D3B3": h(f.m[0xD3B3], 2), "next_state_02": f.r(2), "retry_35": f.r(0x35),
                "rings_D29A": h(f.m[0xD29A], 2), "lives_D2C3": f.m[0xD2C3], "counter_D299": f.m[0xD299]}
    # retry roll
    roll = {}
    for d12f in range(8):
        f.restore()
        f.w(0x35, 0xFF)
        f.m[0xD12F] = d12f
        f.m[0xD29A] = 0x16
        f.m[0xD2C3] = 3
        f.m[0xD299] = 1
        f.m[0xD29A] = 0x16
        f.call_cb(0xA8FA)
        roll[str(d12f)] = {"class_34": f.r(0x34), "D3B3": h(f.m[0xD3B3], 2), "rings": h(f.m[0xD29A], 2),
                           "lives": f.m[0xD2C3], "D299": f.m[0xD299], "state_02": f.r(2)}
    out["retry_roll_after_class_0"] = roll
    # zone parity dependence (not used in THZ)
    f.restore()
    f.w(0x35, 0)
    f.m[0xD29A] = 0x24
    f.m[0xD297] = 1
    f.call_cb(0xA8FA)
    out["zone_1_table_sample_ring_24"] = {"class_34": f.r(0x34), "D3B3": h(f.m[0xD3B3], 2)}
    return out


def lifetime_fixture(rom: bytes) -> dict:
    """The sign never removes itself; the shared off-window cleanup converts an untouched/any-state sign to $FE."""
    out = {"evidence": "CONTROLLED ROUTINE RESULT"}
    f = ready_at_state3(rom, "thz1")
    out["token_3E_at_creation"] = f.r(0x3E)
    out["flags_04_keep_alive_bit1"] = bool(f.r(4) & 2)
    out["occupancy_byte"] = h(f.m[f.occupancy], 2)
    out["type_writes_inside_sign_callbacks"] = "none: no callback in $A867..$AA47 or $AA87..$AB9F writes (IX+0)"
    for name, camx in (("camera_far_right", 3960 + 2000), ("camera_far_left", 3960 - 2000), ("camera_near", 3960 - 128)):
        f.restore()
        f.o.word(0xD174, camx)
        f.player(3000, f.sy, vx=0)
        f.update_all()
        out[name] = {"type_after": h(f.m[SLOT], 2), "state_after": f.r(1), "token_3E_after": f.r(0x3E),
                     "offscreen_bit6": bool(f.r(4) & 0x40)}
    # the sign after the hop (state 5) is also removable once the camera leaves the window
    f.restore()
    f.w(1, 5)
    f.w(2, 5)
    f.o.word(0xD174, 3960 + 2000)
    f.update_all()
    out["state5_camera_far"] = {"type_after": h(f.m[SLOT], 2), "token_3E_after": f.r(0x3E)}
    return out


def child_fixture(rom: bytes) -> dict:
    """Type $19 from spawn to the player-state-$20 request."""
    f = ready_at_state3(rom, "thz1")
    f.restore()
    f.o.word(0xD174, 3832)
    f.o.word(0xD176, 405)
    f.m[0xD2BF], f.m[0xD2C0] = 0x06, 0x00
    f.m[0xD29A] = 0x00
    f.call_cb(0xAA47)                        # the state-5 script call (allocator $032C)
    kid = next(i for i in range(19) if f.m[0xD540 + i * 0x40] == TYPE_CHILD)
    base = 0xD540 + kid * 0x40

    def cr(off, n=1):
        return sum(f.m[base + off + i] << (8 * i) for i in range(n))

    rows, prev = [], None
    floor_on = False
    snd = []
    for u in range(1, 700):
        f.m[0xDE04] = 0
        f.player(3700, 558, vx=0)
        f.m[0xD522] = 2 if floor_on else 0            # floor contact bit $D522.1
        f.m[0xD501] = 5
        f.m[0xD502] = f.m[0xD502] if f.m[0xD502] == 0x20 else 5
        f.o.word(0xD174, 3832)
        f.update_all()
        if f.m[0xDE04]:
            snd.append([u, h(f.m[0xDE04], 2)])
        key = (cr(1), cr(2))
        if key != prev:
            rows.append({"update": u, "state": cr(1), "requested": cr(2), "x": cr(0x11, 2), "y": cr(0x14, 2),
                         "D2A6": h(f.o.word(0xD2A6)), "D3B3": h(f.m[0xD3B3], 2)})
            prev = key
        if u == 400:
            floor_on = True                               # the player touches the floor only now
        if f.m[0xD502] == 0x20:
            rows.append({"update": u, "event": "player requested state $20", "sound": h(f.m[0xDE04], 2),
                         "D502": h(f.m[0xD502], 2)})
            break
    init_x = None
    return {
        "slot_index": kid, "rows": rows, "sound_requests": snd[:3] + ["..."] + snd[-3:],
        "roll_sound_BC_count": sum(1 for _, v in snd if v == "0xBC"),
        "note": "the player's floor bit $D522.1 was withheld until update 400 to show that state 4 waits for it",
    }


def child_position_fixture(rom: bytes) -> dict:
    f = ready_at_state3(rom, "thz1")
    f.restore()
    f.o.word(0xD174, 3832)
    f.o.word(0xD176, 405)
    f.call_cb(0xAA47)
    kid = next(i for i in range(19) if f.m[0xD540 + i * 0x40] == TYPE_CHILD)
    base = 0xD540 + kid * 0x40
    xs = []
    for u in range(1, 40):
        f.player(3700, 558, vx=0)
        f.o.word(0xD174, 3832)
        f.update_all()
        xs.append((f.m[base + 1], f.m[base + 0x11] | f.m[base + 0x12] << 8, f.m[base + 0x14] | f.m[base + 0x15] << 8))
    first_state2 = next(i + 1 for i, r in enumerate(xs) if r[0] == 2)
    return {"x_after_first_updates": [r[1] for r in xs[:4]], "y": xs[0][2], "state_after_first_updates": [r[0] for r in xs[:4]],
            "first_update_in_state_2": first_state2, "x_at_state_2": xs[first_state2 - 1][1],
            "rule": "init: X = cameraX + $104, Y = cameraY($D176) + $50; state 1 subtracts 8 from X each update until X <= cameraX + $85"}


def bonus_fixture(rom: bytes) -> dict:
    """Vector $041F ($6276): the value the child shows and the tally later counts down."""
    f = Fixture(rom)
    rows = []
    for time_bcd, rings in ((0x0000, 0x00), (0x0006, 0x00), (0x0028, 0x00), (0x0029, 0x00), (0x0030, 0x00),
                            (0x0058, 0x11), (0x0059, 0x12), (0x0100, 0x25), (0x0130, 0x50), (0x0429, 0x99),
                            (0x0430, 0x99), (0x0800, 0x10), (0x0800, 0x11)):
        f.o.word(0xD2BF, time_bcd)
        f.m[0xD29A] = rings
        f.o.bank(2, BANK)
        f.o.cpu.hl = 0
        f.o.call(0x6276)
        hl = f.o.cpu.hl
        f.m[0xD299] = 1
        f.o.word(0xD2A6, 0)
        f.call_cb(0xAB48)                                # child state-3 callback: stores $D2A6, equal digits call $03F2
        rows.append({"time_D2BF_bcd": f"{time_bcd:04X}", "rings_D29A_bcd": f"{rings:02X}", "HL": h(hl),
                     "D2A6_after_state3": h(f.o.word(0xD2A6)), "D299_after_state3": f.m[0xD299]})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "samples": rows,
            "note": "L = (rings - $11) in BCD + time-bonus low byte (always 0); the high byte is the time-bonus table entry. "
                    "No borrow is propagated into H. A zero result is replaced by $0777 (state 3 of the child, $AB4B..$AB4F)."}


def player_state20_fixture(rom: bytes) -> dict:
    """Original handler $83A6 run directly for the player slot ($D500)."""
    f = Fixture(rom)
    o, m = f.o, f.m
    o.bank(2, BANK)
    m[0xD12B] = BANK
    rows = []
    for act_idx in (0, 1, 2):
        for diff in (0xF7, 0xF8, 0xF9, 0x11F, 0x120, 0x121, 0x122, 0x200):
            m[0xD293] = 0x40
            m[0xD298] = act_idx
            o.word(0xD174, 1000)
            o.word(0xD511, 1000 + diff)
            o.word(0xD516, 0x0500)
            m[0xD500 + 0x04] = 0x10
            o.cpu.ix = 0xD500
            o.call(0x83A6)
            rows.append({"D298": act_idx, "player_minus_camera_x": diff, "D293_after": h(m[0xD293], 2),
                         "flag_set": (m[0xD293] & 0x30) != 0, "x_velocity_after": o.word(0xD516),
                         "x_after": o.word(0xD511)})
    # velocity model
    vel = []
    m[0xD293] = 0x40
    m[0xD298] = 0
    o.word(0xD174, 1000)
    o.word(0xD511, 1000 + 100)
    o.word(0xD516, 0)
    flagged_after = None
    for i in range(100):
        o.cpu.ix = 0xD500
        o.call(0x83A6)
        vel.append(o.word(0xD516))
        if m[0xD293] & 0x30 and flagged_after is None:
            flagged_after = i + 1
    # cap: keep the player close to the camera so the flag never sets
    m[0xD293] = 0x40
    o.word(0xD516, 0)
    cap = []
    for _ in range(120):
        o.word(0xD511, 1100)
        o.cpu.ix = 0xD500
        o.call(0x83A6)
        cap.append(o.word(0xD516))
    neg = []
    o.word(0xD516, 0xFC00)
    o.word(0xD511, 1100)
    o.cpu.ix = 0xD500
    o.call(0x83A6)
    neg.append(o.word(0xD516))
    return {"evidence": "CONTROLLED ROUTINE RESULT", "handler": "0x83A6 (bank 0x0C)", "cases": rows,
            "velocity_first_6": vel[:6], "velocity_cap_when_flag_not_reached": max(cap), "velocity_after_cap_reached": cap[-1], "updates_until_flag_from_d100": flagged_after, "velocity_from_negative_after_one_update": neg[0],
            "velocity_rule": "v = 0 if v < 0; if high byte < 6: v += $10; then position += v (vector $0338)",
            "flag_rule": "let d = playerX - cameraX (16-bit); if d <= $F8 keep running; else if d <= $120 keep running; else velocity = 0 and "
                         "D293 |= $20 when D298 < 2, D293 |= $10 otherwise. d > $120 means d >= $121 (negative d counts as huge)"}


def complete_setter_fixture(rom: bytes) -> dict:
    f = Fixture(rom)
    out = {}
    for act_idx in (0, 1, 2, 3):
        f.m[0xD298] = act_idx
        f.m[0xD502] = 5
        f.m[0xDE04] = 0
        f.o.call(0x4892)
        out[str(act_idx)] = {"D502": h(f.m[0xD502], 2), "sound_DE04": h(f.m[0xDE04], 2)}
    return {"evidence": "CONTROLLED ROUTINE RESULT", "vector": "0x03F5 -> 0x4892", "by_D298": out,
            "writes": "only $D502 (requested player state) and $DE04 (sound request); no timer, control-lock or progression write"}


def timer_fixture(rom: bytes) -> dict:
    f = Fixture(rom)
    m, o = f.m, f.o
    out = {}
    for name, flag in (("running_D2BE_FF", 0xFF), ("stopped_D2BE_00", 0x00)):
        m[0xD2BE] = flag
        m[0xD2C2] = 0
        o.word(0xD2BF, 0x0058)
        m[0xD294] = 0
        m[0xD292] = 1                                   # suppress the HUD tile writes ($285C tail)
        for _ in range(60):
            o.call(0x27EE)
        out[name] = {"frame_counter_D2C2": m[0xD2C2], "time_D2BF": h(o.word(0xD2BF)), "D2BE": m[0xD2BE]}
    # rollover seconds 59 -> 1:00
    m[0xD2BE] = 0xFF
    m[0xD2C2] = 59
    o.word(0xD2BF, 0x0059)
    o.call(0x27EE)
    out["rollover"] = {"time_D2BF_after": h(o.word(0xD2BF)), "D2C2": m[0xD2C2]}
    return {"evidence": "CONTROLLED ROUTINE RESULT", "tick_routine": "0x27EE", "cases": out,
            "rule": "no change while $D2BE = 0; otherwise $D2C2 += 1 per frame and at 60 the BCD time word $D2BF (seconds, minutes) advances"}


def convergence(rom: bytes) -> dict:
    """Byte evidence that type $18's child and type $50 reach the same setter."""
    def has_call(cpu_start, cpu_end, bank, target):
        raw = rom[rom_of(bank, cpu_start):rom_of(bank, cpu_end)]
        pat = bytes([0xCD, target & 255, target >> 8])
        return [h(cpu_start + i) for i in range(len(raw) - 2) if raw[i:i + 3] == pat]
    boss = json.loads((ROOT / "data/rom-cache/thz3/object-50.json").read_text(encoding="utf-8"))
    r = {x["name"]: x for x in boss["routines"]}
    out = {
        "vector_03F5": {"bytes": rom[0x3F5:0x3F8].hex(" "), "target": "0x4892"},
        "child_19_calls_03F5_at": has_call(0xAB8C, 0xAB9F, BANK, 0x03F5),
        "goal_sign_calls_03F5": has_call(0xA88E, 0xAA47, BANK, 0x03F5),
        "boss_50_state_5_callback": "0x81BD (docs/object-50.md)",
    }
    # the boss routine bytes: search the defeat routine for the $03F5 call
    for name, reg in r.items():
        if reg["kind"] == "code":
            cpu = int(reg["cpu"], 16)
            end = int(reg["cpu_end_exclusive"], 16)
            c = has_call(cpu, end, 0x1E, 0x03F5)
            if c:
                out.setdefault("boss_50_calls_03F5", []).append({"region": name, "at": c})
    out["evidence"] = "BYTE-VERIFIED ASSEMBLY"
    return out


# --------------------------------------------------------------------------- #
# 3. emulated original frames
# --------------------------------------------------------------------------- #
def _boot(rom: bytes, act_idx: int, hook, rings: int = 0):
    from sms_frame_harness import SMS, BTN_1, BTN_2
    s = SMS(rom)
    st = {"done": False}

    def setact(m):
        m._write(0xD297, 0)
        m._write(0xD298, act_idx)

    s.add_pc_hook(0x07D5, setact)

    def start(m):
        if m.frame > 300 and not st["done"]:
            st["done"] = True
            hook(m)

    s.add_pc_hook(0x4E97, start)
    f = 0
    while True:
        if f < 250:
            s.pad = 0
        elif f < 700:
            s.pad = BTN_1 if f % 40 < 3 else 0
        elif not st["done"]:
            s.pad = (BTN_1 | BTN_2) if f % 60 < 10 else 0
        else:
            s.pad = 0
        s.run_frame()
        f += 1
        if st["done"] and s.mem[0xD500] == 1:
            return s
        if f > 4000:
            raise RuntimeError("did not reach gameplay")


def _sign(s):
    for i in range(19):
        b = 0xD540 + i * 0x40
        if s.mem[b] == TYPE_SIGN:
            return b
    return None


def emulated_run(rom: bytes, act_idx: int, rings: int = 0, hostile: bool = False) -> dict:
    from sms_frame_harness import BTN_RIGHT, BTN_LEFT, BTN_DOWN, BTN_1, BTN_2
    sy = (558, 654)[act_idx]

    def hook(m):
        m.w16(0xD2D6, 3700)
        m.w16(0xD2D8, sy - 118)
        m.w16(0xD511, 3800)
        m.w16(0xD514, sy - 58)
        m._write(0xD29A, rings)

    s = _boot(rom, act_idx, hook, rings)
    m = s.mem
    s._write(0xD29A, rings)                  # the level init clears the ring byte after the hook, so preset it here
    base = s.frame
    sound = []
    orig = s._write

    def w(a, v):
        if a == 0xDE04 and v:
            sound.append((s.frame - base, v))
        orig(a, v)
    s._write = w
    s.cpu.set_write_callback(w)
    marks = {}

    def mark(name):
        def fn(mach):
            marks.setdefault(name, mach.frame - base)
        return fn
    flag_pc = {0x83E9: "flag_bit5_set", 0x83ED: "flag_bit4_set"}
    for pc, name in flag_pc.items():
        s.add_pc_hook(pc, mark(name))
    for pc, name in ((0x14AE, "act_clear_sequence_entry"), (0x1543, "zone_clear_sequence_entry"),
                     (0x32F9, "results_screen_draw_entry"), (0x2D08, "ring_tally_entry"), (0x2D28, "bonus_tally_entry"),
                     (0x1538, "act_index_incremented")):
        s.add_pc_hook(pc, mark(name))
    events, prev = [], None
    contact = None
    end = None
    for f in range(2500):
        b = _sign(s)
        done = (m[0xD293] & 0x30) != 0
        if hostile:
            s.pad = (BTN_LEFT | BTN_DOWN | BTN_1 | BTN_2) if m[0xD501] == 0x20 else BTN_RIGHT
        else:
            s.pad = BTN_RIGHT if not done and m[0xD501] != 0x20 else 0
        s.run_frame()
        b = _sign(s)
        kids = [i for i in range(19) if m[0xD540 + i * 0x40] == TYPE_CHILD]
        key = (b and (m[b + 1], m[b + 2]), m[0xD2BE], m[0xD501], m[0xD293], bool(kids), m[0xD3B3])
        if key != prev:
            e = {"frame": f, "player": [s.u16(0xD511), s.u16(0xD514)], "player_D501": h(m[0xD501], 2),
                 "player_extents": [m[0xD52C], m[0xD52D]], "sign_state_req": b and [m[b + 1], m[b + 2]],
                 "sign_y": b and s.u16(b + 0x14), "sign_prize_34_35": b and [m[b + 0x34], m[b + 0x35]],
                 "D2BE": m[0xD2BE], "D293": h(m[0xD293], 2), "child_19_present": bool(kids), "D3B3": h(m[0xD3B3], 2),
                 "camera_x": s.u16(0xD174), "time_D2BF": h(s.u16(0xD2BF)), "rings_D29A": h(m[0xD29A], 2),
                 "lives_D2C3": m[0xD2C3], "D2A6": h(s.u16(0xD2A6))}
            events.append(e)
            prev = key
            if contact is None and b and m[b + 2] == 4:
                contact = f
        if m[0xD298] != act_idx and "act_index_incremented" in marks:
            end = f
            break
    return {
        "evidence": "EMULATED ORIGINAL FRAME",
        "method": f"original ROM booted in tools/sms_frame_harness.py with the new-game init patched to zone 0 / act index {act_idx}; "
                  f"at the start-position loader return the camera is placed at (3700, {sy - 118}) and the player at (3800, {sy - 58}); "
                  "RIGHT is held until D293 bit 4/5 is set. Frame numbers count harness frames after gameplay begins.",
        "rings_preset_D29A": h(rings, 2),
        "hostile_input_during_state_20": hostile,
        "contact_frame_sign_requests_state_4": contact,
        "events": events,
        "marks": marks,
        "marks_relative_to_contact": {k: v - contact for k, v in marks.items()} if contact is not None else {},
        "sound_requests": _dedupe_sound(sound),
        "end_frame_act_index_changed": end,
    }


def _dedupe_sound(log):
    out, prev = [], None
    for fr, v in log:
        if (fr, v) != prev:
            out.append([fr, h(v, 2)])
        prev = (fr, v)
    # collapse the repeating spin ($AA) and roll ($BC) sounds
    summary, i = [], 0
    while i < len(out):
        j = i
        while j + 1 < len(out) and out[j + 1][1] == out[i][1] and out[j + 1][0] - out[j][0] <= 6:
            j += 1
        summary.append([out[i][0], out[i][1]] if i == j else [out[i][0], out[i][1], f"x{j - i + 1} until {out[j][0]}"])
        i = j + 1
    return summary


def emulated_timer_thz3(rom: bytes) -> dict:
    """Forced player state $20 in THZ3: which flag bit, and does the level timer keep running?"""
    def hook(m):
        m.w16(0xD2D6, 1600)
        m.w16(0xD2D8, 80)
        m.w16(0xD511, 1700)
        m.w16(0xD514, 230)

    s = _boot(rom, 2, hook)
    m = s.mem
    base = s.frame
    marks = {}

    def mark(name):
        def fn(mach):
            marks.setdefault(name, mach.frame - base)
        return fn
    s.add_pc_hook(0x83ED, mark("flag_bit4_set"))
    s.add_pc_hook(0x83E9, mark("flag_bit5_set"))
    s.add_pc_hook(0x1543, mark("zone_clear_sequence_entry"))
    s.add_pc_hook(0x14AE, mark("act_clear_sequence_entry"))
    s.add_pc_hook(0x32F9, mark("results_screen_draw_entry"))
    timer_at = {}
    forced = None
    for f in range(1500):
        s.pad = 0
        if f == 30:
            m[0xD502] = 0x20                      # forced: NOT the boss path; isolates the shared tail
            s._write(0xD15E, 0x80)                # fixed camera (as the boss/sign pan leaves it), so the player can leave the screen
            s._write(0xD15F, 0x01)
            s.w16(0xD2DA, s.u16(0xD174))
            s.w16(0xD2DC, s.u16(0xD176))
            forced = f
            timer_at["at_force"] = [m[0xD2BE], s.u16(0xD2BF), m[0xD2C2]]
        s.run_frame()
        if "flag_bit4_set" in marks and "at_flag" not in timer_at:
            timer_at["at_flag"] = [m[0xD2BE], s.u16(0xD2BF), m[0xD2C2]]
        if "zone_clear_sequence_entry" in marks and "at_sequence_entry" not in timer_at:
            timer_at["at_sequence_entry"] = [m[0xD2BE], s.u16(0xD2BF), m[0xD2C2]]
            break
    return {"evidence": "EMULATED ORIGINAL FRAME (forced $D502 = $20; NOT the boss defeat path)",
            "forced_at_frame": forced, "marks": marks,
            "timer_D2BE_D2BF_D2C2": {k: [h(v[0], 2), h(v[1]), v[2]] for k, v in timer_at.items()},
            "D298": m[0xD298], "D293_bit": 4 if m[0xD298] >= 2 else 5}


# --------------------------------------------------------------------------- #
# 4. interpretation
# --------------------------------------------------------------------------- #
def state_machine() -> list[dict]:
    return [
        {"state": 0, "script": "0xA7CA", "callback": "0xA867", "effect": "+$03 bit 7 set (overlap ignores the player's D503 bit-6 gate); +$34 = +$35 = 0; script requests state 1"},
        {"state": 1, "script": "0xA7D3", "callback": "0xA873", "effect": "waits until +$04 bit 6 is clear (object on-screen per $61E1), then requests state 2"},
        {"state": 2, "script": "0xA7D9", "callback": "0xA87D", "effect": "dynamic art selector $D3B3 = $12 (sign art); player requested state $12 becomes $0E; script requests state 3"},
        {"state": 3, "script": "0xA7E2", "callback": "0xA88E", "effect": "frame 1 (+$2C = 12, +$2D = 42). Each update: gate (player speed != 0 or requested state $18); left camera lock $0353; overlap $033B; on contact: timer stop, hop"},
        {"state": 4, "script": "0xA7E8", "callback": "0xA8C8, 0xA8CE", "effect": "spin animation (frames 1..5, duration 2) with sound $F8 once, $AA every 3 records; hop up at -4 px/update, gravity $10/256, lands at the saved Y"},
        {"state": 5, "script": "0xA81F", "callback": "0x032F (idle)", "effect": "FF 01 $AA47 spawns the type-$19 child once, sound $AB, frame 1 held forever (no further transition)"},
        {"state": 6, "script": "0xA82E", "callback": "0x032F (idle)", "effect": "retouch spin: 4 loops of frames 1..5, then callback $A8FA (prize roll again)"},
    ]


def unresolved() -> list[str]:
    return [
        "semantic names of the prize classes and of $D299/$D2C3/$D2A6 beyond what the code proves (D2C3 is treated as lives because bit 7 of it is the game-over flag at $1396)",
        "the purpose of sound requests $F8/$AA/$AB/$BC/$89/$97 (only their numbers are recovered)",
        "the meaning of RAM $D4A3 (written $FF by the state-4 first record callback) and $D445 (cleared at contact; a zone-4 routine increments it)",
        "sign art selectors $1B/$1D/$1E/$1F/$20 (graphics not decoded here; only the selector numbers are recovered)",
        "sub-waits inside $1CEB/$18E1/$4FCE/$21DA (fade/palette helpers) in the act-clear sequence: frame counts between the flag and the results tally are emulated, not derived",
        "whether type $1A (state table at $AB9F) is ever spawned in THZ (nothing in THZ1/THZ2 spawns it in the emulated runs)",
        "exact contact box when the player is in a state whose frame extents differ from (8,24)/(9,24): extents come from each player frame record; only the states observed in emulation are tabulated",
        "THZ3 (act index 2) has no type $18: its completion goes through type $50, studied in docs/object-50.md",
    ]


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    report = {
        "format": 1,
        "rom_sha256": ROM_SHA256,
        "subject": "THZ1/THZ2 object type $18 and the act-clear chain",
        "research_only": True,
        "poc_untouched": True,
        "evidence_classes": EVIDENCE,
        "machine_facing_label": "object_18",
        "placement": placement(rom),
        "dispatch": dispatch(rom),
        "frame_extents": frame_extents(rom),
        "state_machine": state_machine(),
        "routines": routine_table(rom),
        "prize_tables": prize_tables(rom),
        "convergence_with_object_50": convergence(rom),
        "unresolved": unresolved(),
    }
    if not static_only:
        report["controlled_execution"] = {
            "contact": contact_fixtures(rom),
            "hop_thz1": hop_fixture(rom, "thz1"),
            "hop_thz2": hop_fixture(rom, "thz2"),
            "hop_trace_thz1": hop_trace(rom),
            "lifetime": lifetime_fixture(rom),
            "retry_path": retry_fixture(rom),
            "prizes": prize_fixtures(rom),
            "child_19": child_fixture(rom),
            "child_19_position": child_position_fixture(rom),
            "bonus_value": bonus_fixture(rom),
            "player_state_20": player_state20_fixture(rom),
            "level_complete_setter": complete_setter_fixture(rom),
            "timer": timer_fixture(rom),
        }
        report["emulated_original_frames"] = {
            "thz1_rings_0": emulated_run(rom, 0, 0x00),
            "thz1_rings_09": emulated_run(rom, 0, 0x09),
            "thz2_rings_0": emulated_run(rom, 1, 0x00),
            "thz1_hostile_input_during_state_20": emulated_run(rom, 0, 0x00, hostile=True),
            "thz3_forced_state_20": emulated_timer_thz3(rom),
        }
    return report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path, default=OUTPUT)
    p.add_argument("--check", action="store_true")
    p.add_argument("--static-only", action="store_true")
    a = p.parse_args()
    rom = a.rom.read_bytes()
    report = build(rom, a.static_only)
    text = json.dumps(report, indent=2) + "\n"
    if a.check:
        old = a.output.read_text(encoding="utf-8")
        if a.static_only:
            old_j = json.loads(old)
            new_j = json.loads(text)
            for k in new_j:
                if old_j.get(k) != new_j[k]:
                    print("MISMATCH", k)
                    sys.exit(1)
        elif old.replace("\r\n", "\n") != text:
            print("MISMATCH")
            sys.exit(1)
        print("object-18 cache matches ROM")
        return
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(a.output), "routines": len(report["routines"])}))


if __name__ == "__main__":
    main()

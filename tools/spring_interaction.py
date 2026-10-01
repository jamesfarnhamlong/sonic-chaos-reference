#!/usr/bin/env python3
"""Spring interaction audit (mapped type $26, terrain springs, spring-adjacent bounces) - research only, deterministic.

Answers: every spring mechanism, exact activation geometry and gates, launch velocities/state requests/flags, the
parameter semantics of type $26, the gameplay role of $D448, whether spring-launched Sonic is an attacker, the
loop/twist/special-state reach, presentation versus gameplay anchors, and what the original does at the top of the screen.
Output: data/rom-cache/spring-interaction.json (numeric labels only; no ROM bytes beyond 16-byte prefixes).

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT
(original Z80 routines on tools/oracle.py), EMULATED ORIGINAL FRAME (tools/sms_frame_harness.py), UNRESOLVED.

Usage:
  python tools/spring_interaction.py ROM.sms [--check] [--static-only]
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
OUTPUT = ROOT / "data" / "rom-cache" / "spring-interaction.json"
ACTS = ("thz1", "thz2", "thz3")
ACT_INDEX = {"thz1": 0, "thz2": 1, "thz3": 2}
BANK_TYPE26 = 30            # file $78000, CPU $8000
BANK_TYPE21 = 12
LAYOUT_BASE = 0xC001
LAYOUT_W = {"thz1": 128, "thz2": 128, "thz3": 80}
HANDLER_TABLE = 0x6973      # 32 words, indexed by (terrain flags & $1F), jumped through at $6972
OBJ = 0xD540                # first mapped-object slot used as the fixture slot
BLOCK_UPRIGHT = (0x30, 0x31)
BLOCK_HORIZONTAL = (0x32, 0x33, 0x34, 0x35)
BLOCK_DIAGONAL_RIGHT = (0x36, 0x37)     # launch +4.0
BLOCK_DIAGONAL_LEFT = (0x38, 0x39)      # launch -4.0 (tile id >= $38)
BLOCK_CEILING_SPRING = (0x3A, 0x3B)


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def s16(v: int) -> int:
    return (v + 32768) % 65536 - 32768


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


def ranges(values) -> list:
    """Sorted integers -> list of [first, last] runs."""
    s = sorted(set(values))
    if not s:
        return []
    out, a, b = [], s[0], s[0]
    for v in s[1:]:
        if v == b + 1:
            b = v
        else:
            out.append([a, b])
            a = b = v
    out.append([a, b])
    return out


EVIDENCE = {
    "DECODED DATA": "ROM tables/records decoded by a parser",
    "BYTE-VERIFIED ASSEMBLY": "routine bytes compared literally and disassembled by hand",
    "SOURCE-TRACED BEHAVIOR": "behavior read from the disassembly, not executed",
    "CONTROLLED ROUTINE RESULT": "original routine executed on a Z80 core with explicit RAM",
    "EMULATED ORIGINAL FRAME": "whole original game run in the approximate SMS harness",
    "UNRESOLVED": "not established",
}

# (name, bank, first CPU, end CPU exclusive, purpose)
ROUTINES = [
    ("terrain_dispatch_690b", 1, 0x690B, 0x6973, "$690B..$6972: floor sample, previous-surface projection $6F61, then JP (HL) through the 32-word table at $6973"),
    ("terrain_handler_table", 1, 0x6973, 0x69B3, "32 handler words indexed by terrain flags & $1F (type 9 -> $6A75, type $14 -> $6A90)"),
    ("terrain_upright_spring_6a75", 1, 0x6A75, 0x6A90, "type 9: current state != $11, floor flag, Y speed >= 0, $D448=$FF, Y=$F880, $480C"),
    ("terrain_diagonal_spring_6a90", 1, 0x6A90, 0x6ACE, "type $14: current state != $11, floor flag, X=+-4.0, Y=$F900/$FA80, $D448=0, $482D"),
    ("launch_setters_480c", 1, 0x480C, 0x4892, "$480C upright ($0B), $482D diagonal ($1C), $4849/$4868 horizontal (state 9)"),
    ("launch_vector_5f17", 1, 0x5F17, 0x5F27, "vector $035F: IX=player, +$21=0, call $480C"),
    ("proximity_helper_61a5", 1, 0x61A5, 0x61D6, "$0383/$0386/$0389: |object - player| < BC (strict) -> A=$FF"),
    ("side_probe_dispatch_715e", 1, 0x715E, 0x71B2, "right ($716B) and left ($7210) side probe, type dispatch"),
    ("side_core_and_horizontal_spring_71b2", 1, 0x71B2, 0x7210, "right core; type 10 tail at $71FC..$720D ($FA00 -> $4868)"),
    ("side_left_core_7257", 1, 0x7257, 0x72B6, "left core; type 10 tail at $72A2..$72B3 ($0600 -> $4849)"),
    ("ceiling_probe_73c9", 1, 0x73C9, 0x753E, "ceiling pass: type $14 blocks $3A/$3B ($749D) and type $15 ($748F) bounces"),
    ("breakable_bounce_6ae3", 1, 0x6AE3, 0x6B14, "type $16 breakable + bounce (-4.25)"),
    ("breakable_bounce_6b2c", 1, 0x6B2C, 0x6B56, "type $0D breakable + bounce (-4.25)"),
    ("vertical_spring_update_393b", 1, 0x393B, 0x396D, "state $0B and $1C update wrappers ($393B / $3955)"),
    ("falling_463c", 1, 0x463C, 0x4663, "apex/air request: state $0E, vy=+1.0, +3 bit0 set, bit1 CLEARED"),
    ("landing_45ce", 1, 0x45CE, 0x45ED, "landing: +3 bits 0/1/6 cleared, state 5, speed cap $D373=$0400"),
    ("player_bounds_death_401a", 1, 0x401A, 0x402A, "screen Y (+$1C) >= $D0 and not negative -> $4984"),
    ("death_start_4984", 1, 0x4984, 0x49C3, "state $1F, vy=-5.0, $D293 bit 2"),
    ("screen_position_3fc8", 1, 0x3FC8, 0x3FEF, "+$1A/+$1D = position - camera ($D174/$D176) for every object"),
    ("object_creator_80eb", 28, 0x80EB, 0x813C, "placement record -> object slot (+$3F = parameter, +9 = aux1)"),
    ("type26_script_table", BANK_TYPE26, 0x8212, 0x825A, "ten state scripts of type $26"),
    ("type26_init_825a", BANK_TYPE26, 0x825A, 0x82AF, "Y+12 and span decode"),
    ("type26_state7_contact_82af", BANK_TYPE26, 0x82AF, 0x8312, "fixed contact"),
    ("type26_extension_hold_retract", BANK_TYPE26, 0x8312, 0x83B3, "states 1..6"),
    ("type26_state8_span_83bf", BANK_TYPE26, 0x83B3, 0x8401, "span trigger"),
    ("type26_state9_span_launch_8401", BANK_TYPE26, 0x8401, 0x8439, "span launch"),
    ("type21_stomp_b2af", BANK_TYPE21, 0xB2AF, 0xB2E0, "stomp bounce $F940 + $D448=$FF"),
    ("type50_bounce_99ae", BANK_TYPE26, 0x99AE, 0x99E0, "boss top bounce $FC00 + $D448=0"),
    ("badnik_attack_check_5f3d", 1, 0x5F3D, 0x5F77, "type $27 attack gate ($D532==6 or $D503 bit 1)"),
    ("d448_reader_818f", 12, 0x818F, 0x8194, "LD A,($D448); RRCA; RET (state $0B script condition)"),
]


def routine_table(rom: bytes) -> list:
    out = []
    for name, bank, a, b, purpose in ROUTINES:
        o, e = rom_of(bank, a), rom_of(bank, b)
        out.append({"name": name, "bank": bank, "cpu": h(a), "rom_offset": h(o, 5), "end_cpu_exclusive": h(b), "length": b - a,
                    "sha256": sha(rom[o:e]), "first_16_bytes": rom[o:o + 16].hex(), "purpose": purpose})
    return out


# --------------------------------------------------------------------------- #
# static decodes
# --------------------------------------------------------------------------- #
def handler_table(rom: bytes) -> list:
    roles = {9: "upright spring", 0x14: "diagonal spring", 0x12: "ramp launch ($69B2)", 0x0D: "breakable + bounce ($6B2C)",
             0x16: "breakable + bounce ($6AE3)"}
    rows = []
    for t in range(32):
        a = rom[HANDLER_TABLE + 2 * t] | (rom[HANDLER_TABLE + 2 * t + 1] << 8)
        rows.append({"type": h(t, 2), "handler": h(a), "role": roles.get(t, "other or no-op")})
    return rows


def block_headers(rom: bytes) -> dict:
    import rom as R
    out = {}
    for blk in (*BLOCK_UPRIGHT, *BLOCK_HORIZONTAL, *BLOCK_DIAGONAL_RIGHT, *BLOCK_DIAGONAL_LEFT, *BLOCK_CEILING_SPRING, 0x47, 0x9B, 0x9C):
        hd = R.header(rom, blk)

        def rl(a):
            runs, start = [], 0
            for i in range(1, 33):
                if i == 32 or a[i] != a[start]:
                    runs.append([start, i - 1, a[start]])
                    start = i
            return runs
        out[h(blk, 2)] = {"flags": h(hd["flags"], 2), "type": h(hd["flags"] & 0x1F, 2), "modifier": hd["modifier"],
                          "vertical_profile_runs_[first,last,value]": rl(hd["vertical"]), "horizontal_profile_runs_[first,last,value]": rl(hd["horizontal"])}
    return out


def layout_cells(act: str) -> list:
    return json.loads((ROOT / "data" / "rom-cache" / "levels" / act / "layout.json").read_text(encoding="utf-8"))["rows"]


def objects(act: str) -> list:
    return json.loads((ROOT / "data" / "rom-cache" / "levels" / act / "objects.json").read_text(encoding="utf-8"))["records"]


def terrain_cells(act: str) -> list:
    rows = layout_cells(act)
    out = []
    for y, row in enumerate(rows):
        for x, b in enumerate(row):
            if b in BLOCK_UPRIGHT:
                kind = "upright"
            elif b in BLOCK_HORIZONTAL:
                kind = "horizontal_left_half" if b in (0x32, 0x33) else "horizontal_right_half"
            elif b in BLOCK_DIAGONAL_RIGHT:
                kind = "diagonal_right_launch"
            elif b in BLOCK_DIAGONAL_LEFT:
                kind = "diagonal_left_launch"
            elif b in BLOCK_CEILING_SPRING:
                kind = "ceiling_spring"
            else:
                continue
            out.append({"act": act, "block": h(b, 2), "world_x": x * 32, "world_y": y * 32, "kind": kind})
    return out


def type26_placements(act: str) -> list:
    out = []
    for r in objects(act):
        if r["type_id"] != "0x26":
            continue
        p, aux1 = int(r["parameter"], 16), int(r["aux1"], 16)
        x, y = r["world_x"], r["world_y"]
        span = (p & 0x7F) * 16 if p & 0x80 else 0
        strong = (p == 0) if not p & 0x80 else (aux1 == 0)
        rest_y = y + 12
        out.append({"act": act, "record_index": r["index"], "raw_bytes": r["raw_bytes"], "world_x": x, "world_y": y, "parameter": h(p, 2),
                    "aux1": h(aux1, 2), "form": "span" if span else "fixed", "span_width_px": span or None,
                    "span_x_interval_inclusive_exclusive": [x, x + span] if span else None, "strong": strong,
                    "rest_y": rest_y, "contact_player_y_window_inclusive": [rest_y - 33, rest_y - 28],
                    "contact_player_y_window_relative_to_placement": [-21, -16],
                    "contact_player_x_window": [x - 11, x + 11] if not span else None,
                    "launch_y_velocity": "$F8A0 (-7.375)" if strong else "$FB00 (-5.0)", "d448": "$FF" if strong else "$00"})
    return out


# --------------------------------------------------------------------------- #
# controlled lab (original Z80 routines)
# --------------------------------------------------------------------------- #
class Lab:
    def __init__(self, rom: bytes, act: str = "thz1"):
        o = _load("oracle")
        self.rom = rom
        self.o = o.Oracle(rom)
        self.m = self.o.mem
        self.act = act
        if act != "thz1":
            self.load_layout(act)

    def load_layout(self, act: str) -> None:
        cells = [b for row in layout_cells(act) for b in row][:4095]
        self.m[LAYOUT_BASE:LAYOUT_BASE + len(cells)] = bytes(cells)
        self.o.word(0xD16A, -LAYOUT_W[act])
        for row in range(128):
            self.o.word(0xD800 + row * 2, row * LAYOUT_W[act])
        self.act = act

    # ---- player ----
    def player(self, x, y, vx=0, vy=0, floor=0, prev=0, cur=5, req=5, f3=0, d297=0):
        o, m = self.o, self.m
        o.position(x, y)
        o.word(0xD516, vx & 0xFFFF)
        o.word(0xD518, vy & 0xFFFF)
        m[0xD522] = 0x02 if floor else 0
        m[0xD523] = 0
        o.word(0xD36B, 0)           # D36B/D36C are one word; D36C is the previous-update surface flags
        m[0xD36C] = prev
        m[0xD501], m[0xD502], m[0xD503] = cur, req, f3
        m[0xD504] = 0
        m[0xD525] = 0
        m[0xD448] = 0x55
        m[0xD3C0] = 0
        m[0xD297] = d297
        m[0xD373] = 0x00
        m[0xD374] = 0x04
        m[0xDE04] = 0

    def call_ix(self, addr, ix=0xD500, bank=None):
        if bank is not None:
            self.o.bank(2, bank)
        self.o.cpu.ix = ix
        self.o.call(addr)

    def call_hl(self, addr, hl, ix=0xD500):
        """Call a setter that takes its value in HL (the Oracle call() only presets BC/DE)."""
        o = self.o
        o.cpu.ix = ix
        o.cpu.hl = hl & 0xFFFF
        o.cpu.pc = addr
        o.cpu.bc = o.cpu.de = 0
        o.cpu.sp = 0xDFE0
        o.word(o.cpu.sp, o.RETURN)
        for _ in range(20):
            o.cpu.ticks_to_stop = 100000
            o.cpu.run()
            if o.cpu.pc == o.RETURN:
                return
        raise RuntimeError(f"setter ${addr:04X} did not return")

    def call_watch(self, addr, watch, ix=0xD500):
        """Run a routine until it returns or reaches the watched address (returns the address reached)."""
        o = self.o
        o.cpu.set_breakpoint(watch)
        o.cpu.ix = ix
        o.cpu.pc = addr
        o.cpu.bc = o.cpu.de = 0
        o.cpu.sp = 0xDFE0
        o.word(o.cpu.sp, o.RETURN)
        o.cpu.ticks_to_stop = 100000
        o.cpu.run()
        return o.cpu.pc

    def snap(self):
        m, o = self.m, self.o
        return {"cur": m[0xD501], "req": m[0xD502], "f3": m[0xD503], "f4": m[0xD504], "x": o.word(0xD511), "y": o.word(0xD514),
                "vx": o.word(0xD516), "vy": o.word(0xD518), "fl22": m[0xD522], "d448": m[0xD448], "snd": m[0xDE04], "cap": o.word(0xD373)}

    # ---- type $26 object slot ----
    def t26(self, ox, oy, px, py, param=0, vy=0x0100, floor=True, req=5, cur=5, flags4=0x00, state=7, aux1=0x72, f3=0):
        m, o = self.m, self.o
        for a in range(OBJ, OBJ + 0x40):
            m[a] = 0
        m[OBJ] = 0x26
        m[OBJ + 2] = state
        m[OBJ + 4] = flags4
        o.word(OBJ + 0x11, ox)
        o.word(OBJ + 0x14, oy)
        m[OBJ + 0x3F] = param
        m[OBJ + 9] = aux1
        o.word(OBJ + 0x3A, ox)
        self.player(px, py, vy=vy, floor=floor, cur=cur, req=req, f3=f3)

    def t26_run(self, addr):
        self.call_ix(addr, OBJ, BANK_TYPE26)
        s = self.snap()
        s.update({"obj_state": self.m[OBJ + 2], "obj_counter": self.m[OBJ + 0x1E], "obj_x": self.o.word(OBJ + 0x11), "obj_y": self.o.word(OBJ + 0x14),
                  "obj_span": self.o.word(OBJ + 0x34), "obj_p3f": self.m[OBJ + 0x3F]})
        return s


# --------------------------------------------------------------------------- #
# models (the rules recovered from the disassembly); every one is checked against the original routines
# --------------------------------------------------------------------------- #
def model_t26_contact(ox, oy, px, py, vy_negative, floor, req, inactive_bit6) -> bool:
    """State-7 handler $82AF."""
    if inactive_bit6 or vy_negative or not floor or req == 0x21:
        return False
    if abs(px - ox) >= 12:
        return False
    d = (oy - 28) - py
    return 0 <= d < 6


def model_t26_span_trigger(x0, span, oy, px, py, vy_negative, floor, req) -> bool:
    """State-8 handler $83BF."""
    if vy_negative or req == 0x21 or not floor:
        return False
    if not (x0 <= px < x0 + span):
        return False
    return abs(oy - py) < 0x30


def model_terrain_floor_flag(prev_flags, floor, vy_hi, profile_h, probe_y_rel) -> bool:
    """Floor flag at the moment $690B dispatches the new cell (previous-surface projection $6F61)."""
    if vy_hi < 0:
        return bool(floor)
    if prev_flags & 0x80:                        # solid: project when the sampled profile reaches the foot
        return bool(floor) or (profile_h + probe_y_rel >= 32)
    if prev_flags & 0x40:                        # one-way: floor flag cleared, re-set only inside [surface, surface+vy_hi+8]
        return 32 <= profile_h + probe_y_rel < 32 + vy_hi + 9
    return bool(floor)


def model_terrain_trigger(profile_h, probe_y_rel, prev_flags, floor, vy_hi, cur) -> bool:
    if cur == 0x11 or vy_hi < 0:
        return False
    return model_terrain_floor_flag(prev_flags, floor, vy_hi, profile_h, probe_y_rel)


def model_side_hit(h_profile, probe_x_rel, probe_y_rel, right_probe) -> bool:
    """Horizontal spring side tests ($71B2 right core / $7257 left core, same extent rule for both probes)."""
    raw = h_profile[probe_y_rel]
    e = raw & 0x3F
    if e == 0:
        return False
    if raw & 0x40:                              # solid part is the right-hand `e` columns
        return probe_x_rel >= 32 - e
    return probe_x_rel < e


def model_ceiling_hit(v_profile_raw, probe_y_rel) -> bool:
    e = v_profile_raw & 0x3F
    if e == 0:
        return False
    if e != 0x20 and not v_profile_raw & 0x40:
        return False
    return e >= probe_y_rel


# --------------------------------------------------------------------------- #
# 1. type $26 sweeps
# --------------------------------------------------------------------------- #
def t26_geometry(rom: bytes) -> dict:
    lab = Lab(rom)
    ox, oy = 1000, 800
    cases = 0
    dx_pass = []
    for dx in range(-16, 17):
        lab.t26(ox, oy, ox + dx, oy - 31)
        cases += 1
        if lab.t26_run(0x82AF)["obj_state"] != 7:
            dx_pass.append(dx)
    dy_pass = []
    for d in range(-48, 25):                    # player Y relative to the object's current Y (+14)
        lab.t26(ox, oy, ox, oy + d)
        cases += 1
        if lab.t26_run(0x82AF)["obj_state"] != 7:
            dy_pass.append(d)
    # full grid against the model
    mism = 0
    for dx in range(-14, 15):
        for d in range(-40, 12):
            lab.t26(ox, oy, ox + dx, oy + d)
            got = lab.t26_run(0x82AF)["obj_state"] != 7
            cases += 1
            mism += got != model_t26_contact(ox, oy, ox + dx, oy + d, False, True, 5, False)
    edges = []
    for dx in (-13, -12, -11, -10, 10, 11, 12, 13):
        lab.t26(ox, oy, ox + dx, oy - 31)
        edges.append({"dx": dx, "launch": lab.t26_run(0x82AF)["obj_state"] != 7})
        cases += 1
    v_edges = []
    for d in (-35, -34, -33, -32, -29, -28, -27, -26):
        lab.t26(ox, oy, ox, oy + d)
        v_edges.append({"player_y_minus_object_y": d, "launch": lab.t26_run(0x82AF)["obj_state"] != 7})
        cases += 1
    return {"evidence": "CONTROLLED ROUTINE RESULT", "handler": "$82AF (bank $1E)", "cases": cases, "model_mismatches": mism,
            "horizontal_pass_dx_ranges": ranges(dx_pass), "horizontal_rule": "abs(playerX - objectX) < 12 (strict; $0383 -> $61A5 compares |dx| < BC with BC=12)",
            "vertical_pass_ranges_relative_to_object_y": ranges(dy_pass),
            "vertical_rule": "0 <= (objectY - 28) - playerY < 6, i.e. playerY in [objectY-33, objectY-28] inclusive (unsigned 16-bit subtracts at $82DD/$82E4)",
            "coordinates": "player anchor (D511/D514) versus the object's current +$11/+$14; object rest Y = placement Y + 12 (init $825A); no extents, mask or sprite edge involved",
            "horizontal_edges": edges, "vertical_edges": v_edges}


def t26_gates(rom: bytes) -> dict:
    lab = Lab(rom)
    ox, oy = 1000, 800
    py = oy - 31
    out, n = {}, 0

    def trial(**kw):
        nonlocal n
        n += 1
        args = dict(ox=ox, oy=oy, px=ox, py=py)
        args.update(kw)
        lab.t26(**args)
        return lab.t26_run(0x82AF)["obj_state"] != 7

    out["vy_raw_to_launch"] = {h(v): trial(vy=v) for v in (0x0000, 0x0001, 0x00FF, 0x0100, 0x7FFF, 0x8000, 0xFF00, 0xFFFF)}
    out["vy_rule"] = "Y speed high byte bit 7 set (negative) rejects; zero and every positive value pass; low byte irrelevant ($D519 bit 7 tested at $82B4)"
    out["floor_flag_$D522"] = {}
    for v in (0x00, 0x01, 0x02, 0x03, 0xFD, 0xFF):
        lab.t26(ox, oy, ox, py)
        lab.m[0xD522] = v
        n += 1
        out["floor_flag_$D522"][h(v, 2)] = lab.t26_run(0x82AF)["obj_state"] != 7
    out["floor_rule"] = "$D522 bit 1 must be set (floor/object contact flag of the previous player update); other bits irrelevant"
    blocked_req = [r for r in range(0, 0x40) if not trial(req=r)]
    blocked_cur = [c for c in range(0, 0x40) if not trial(cur=c)]
    out["requested_state_$D502_blocking"] = [h(v, 2) for v in blocked_req]
    out["current_state_$D501_blocking"] = [h(v, 2) for v in blocked_cur]
    out["state_rule"] = "ONLY the requested state $D502 == $21 blocks; the current state $D501 is not read. All 64 values of each swept"
    out["object_flags_+4"] = {h(v, 2): trial(flags4=v) for v in (0x00, 0x40, 0x80, 0xBF, 0xC0, 0xFF)}
    out["object_flags_rule"] = "+$04 bit 6 set (object inactive: created with $40 ORed in by $80EB, cleared when the object is awake) rejects; other bits irrelevant"
    out["player_f3_+3"] = {h(v, 2): trial(f3=v) for v in (0x00, 0x01, 0x02, 0x03, 0x41, 0xC3)}
    out["cases"] = n
    return {"evidence": "CONTROLLED ROUTINE RESULT", **out}


def t26_span(rom: bytes) -> dict:
    lab = Lab(rom)
    ox, oy, span = 1296, 620, 160
    n = 0

    def s8(px, py, **kw):
        nonlocal n
        n += 1
        lab.t26(ox + 5, oy, px, py, param=1, state=8, **kw)
        lab.o.word(OBJ + 0x3A, ox)
        lab.o.word(OBJ + 0x34, span)
        return lab.t26_run(0x83BF)
    xs = [dx for dx in range(-6, span + 7) if s8(ox + dx, oy - 30)["obj_state"] != 8]
    ys = [d for d in range(-80, 81) if s8(ox + 10, oy + d)["obj_state"] != 8]
    mism = 0
    for dx in range(-3, span + 4, 1):
        for d in range(-52, 53, 1):
            n += 1
            got = s8(ox + dx, oy + d)["obj_state"] != 8
            mism += got != model_t26_span_trigger(ox, span, oy, ox + dx, oy + d, False, True, 5)
    gates = {"vy_negative": s8(ox + 10, oy, vy=0xFFFF)["obj_state"] != 8, "vy_zero": s8(ox + 10, oy, vy=0)["obj_state"] != 8,
             "no_floor_flag": s8(ox + 10, oy, floor=False)["obj_state"] != 8, "requested_21": s8(ox + 10, oy, req=0x21)["obj_state"] != 8,
             "current_21": s8(ox + 10, oy, cur=0x21)["obj_state"] != 8}
    r = s8(ox + 10, oy)
    out = {"evidence": "CONTROLLED ROUTINE RESULT", "handler_state8": "$83BF", "x_pass_ranges_relative_to_x0": ranges(xs),
           "x_rule": "x0 <= playerX < x0 + span (x0 = placement X restored from +$3A/+$3B each update; span = (parameter & $7F) * 16); no |dx|<12 rule",
           "y_pass_ranges_relative_to_object_y": ranges(ys), "y_rule": "abs(objectY - playerY) < $30 (strict; $0386 -> $61B1 with BC=$30), objectY = placement Y + 12",
           "gates": gates, "gate_rule": "same as state 7: Y speed not negative, floor flag, requested state != $21", "next_state": r["obj_state"],
           "object_x_after_trigger": r["obj_x"], "model_mismatches": mism}
    # state 9: aligned launch
    rows = []
    for p3f in (0, 1):
        for aux in (0, 0x72):
            lab.t26(ox, oy, ox + 0x37, oy - 30, param=p3f, state=9, aux1=aux)
            n += 1
            rr = lab.t26_run(0x8401)
            rows.append({"p3f": p3f, "aux1": h(aux, 2), "vy": h(rr["vy"]), "d448": h(rr["d448"], 2), "next_object_state": rr["obj_state"], "object_x": rr["obj_x"], "requested_player_state": h(rr["req"], 2)})
    out["state9_launch"] = rows
    out["state9_note"] = "playerX & $FFF0 becomes the spring X; launch values are selected by +$3F; D448 and the extension state are written even when $480C then rejects a negative Y speed (checked below)"
    lab.t26(ox, oy, ox + 0x37, oy - 30, param=1, state=9, vy=0xFF00)
    rr = lab.t26_run(0x8401)
    n += 1
    out["state9_with_negative_vy"] = {"requested_player_state": h(rr["req"], 2), "player_vy": h(rr["vy"]), "d448": h(rr["d448"], 2), "next_object_state": rr["obj_state"]}
    out["cases"] = n
    return out


def t26_parameters(rom: bytes) -> dict:
    """Run the real initializer $825A and the contact/launch handlers for every parameter and aux1."""
    lab = Lab(rom)
    rows = []
    n = 0
    for p in (0x00, 0x01, 0x02, 0x7F, 0x80, 0x81, 0x88, 0x8A, 0xFF):
        for aux in (0x00, 0x72):
            m = lab.m
            for a in range(OBJ, OBJ + 0x40):
                m[a] = 0
            m[OBJ] = 0x26
            lab.o.word(OBJ + 0x14, 700)
            m[OBJ + 0x3F] = p
            m[OBJ + 9] = aux
            lab.call_ix(0x825A, OBJ, BANK_TYPE26)
            n += 1
            init = {"state": m[OBJ + 2], "rest_state": m[OBJ + 10], "y": lab.o.word(OBJ + 0x14), "saved_y": lab.o.word(OBJ + 0x3C), "p3f": m[OBJ + 0x3F],
                    "span": lab.o.word(OBJ + 0x34)}
            # contact (fixed: state 7) or span trigger+launch (state 8 then 9)
            ox, oy = 1000, 700 + 12
            rest = init["state"]
            if rest == 7:
                lab.t26(ox, oy, ox, oy - 31, param=m[OBJ + 0x3F], aux1=aux)
                r = lab.t26_run(0x82AF)
                launched = r["obj_state"] != 7
            else:
                lab.t26(ox, oy, ox + 5, oy - 30, param=m[OBJ + 0x3F], state=8, aux1=aux)
                lab.o.word(OBJ + 0x3A, ox)
                lab.o.word(OBJ + 0x34, init["span"])
                r8 = lab.t26_run(0x83BF)
                launched = r8["obj_state"] == 9
                lab.t26(ox, oy, ox + 5, oy - 30, param=m[OBJ + 0x3F], state=9, aux1=aux)
                r = lab.t26_run(0x8401)
            n += 2
            rows.append({"parameter": h(p, 2), "aux1": h(aux, 2), "after_init": init, "triggered": launched,
                         "launch_vy": h(r["vy"]), "launch_vy_signed": s16(r["vy"]) / 256, "d448": h(r["d448"], 2), "extension_state": r["obj_state"],
                         "player_requested_state": h(r["req"], 2), "player_f3_after": r["f3"]})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "rows": rows, "cases": n,
            "semantics": {
                "bit7_clear": "fixed spring; +$3F is the raw parameter: 0 -> strong (-7.375, D448=$FF, extension state 1); nonzero -> weak (-5.0, D448=0); extension state 3 only when the parameter is exactly 1, otherwise state 1 (animation only); the low seven bits are otherwise not read",
                "bit7_set": "concealed span: span = (parameter & $7F) * 16 px starting at the placement X; +$3F is overwritten with 1 (weak) when aux1 (+$09) is nonzero, 0 (strong) when aux1 is zero; every canonical record has aux1 = $72, so span springs are always weak",
                "other": "aux1 only matters for span springs (strength) and for the post-launch extension state of state-9 launches (3 when nonzero, 1 when zero); no parameter changes orientation: type $26 is upright only"}}


def t26_state_matrix(rom: bytes) -> dict:
    lab = Lab(rom)
    ox, oy = 1000, 800
    launched = []
    for req in range(0x40):
        lab.t26(ox, oy, ox, oy - 31, req=req)
        launched.append(lab.t26_run(0x82AF)["obj_state"] != 7)
    return {"evidence": "CONTROLLED ROUTINE RESULT", "requested_state_launches": {h(i, 2): v for i, v in enumerate(launched)},
            "blocked": [h(i, 2) for i, v in enumerate(launched) if not v],
            "meaning": "type $26 contact is player-state agnostic except requested state $21; loop states $0C/$0D/$13, twist $22, act-clear $20, rolling, jumping and falling all pass the gate"}


def t26_script_table(rom: bytes) -> dict:
    base = rom_of(BANK_TYPE26, 0x8212)
    ptrs = [rom[base + 2 * i] | (rom[base + 2 * i + 1] << 8) for i in range(10)]
    rows = []
    for i, p in enumerate(ptrs):
        o = rom_of(BANK_TYPE26, p)
        recs, k = [], 0
        while k < 4:
            if rom[o] == 0xFF:
                recs.append({"cmd": f"FF {rom[o + 1]:02X}"})
                break
            recs.append({"duration": rom[o], "frame": rom[o + 1], "callback": h(rom[o + 2] | (rom[o + 3] << 8))})
            o += 4
            k += 1
        rows.append({"state": i, "script": h(p), "records": recs})
    return {"evidence": "DECODED DATA", "states": rows,
            "roles": {"0": "init request ($825A)", "1": "strong extension ($8312)", "2": "strong hold ($833A)", "3": "weak extension ($837C)", "4": "weak hold ($83A4)",
                      "5": "strong retract ($8349)", "6": "weak retract ($8349)", "7": "fixed contact ($82AF)", "8": "span trigger ($83BF)", "9": "span launch ($8401)"}}


# --------------------------------------------------------------------------- #
# 2. terrain springs
# --------------------------------------------------------------------------- #
PREV_CLASSES = ((0x00, "none"), (0x81, "solid"), (0x41, "one_way"), (0x49, "upright_spring_self"), (0x54, "diagonal_spring_self"), (0xC1, "solid_and_one_way"))


def terrain_vertical(rom: bytes, kind: str, cx: int, cy: int, want: int, hdr: dict) -> dict:
    """Foot-probe (X, Y+18) sweeps for one upright/diagonal cell, every previous-surface class x floor flag x Y speed."""
    import rom as R
    lab = Lab(rom)
    blk = lab.o.collision_sample(cx + 8, cy + 8)["tile"]
    hd = R.header(rom, blk)
    v = hd["vertical"]
    rows, mism, n = [], 0, 0
    for prev, pname in PREV_CLASSES:
        for floor in (1, 0):
            for vy in (0x0000, 0x0100, 0x0300):
                hits_x, hits_y = set(), set()
                for fx in range(cx - 2, cx + 34):
                    for fy in range(cy - 2, cy + 34):
                        lab.player(fx, fy - 18, vy=vy, floor=floor, prev=prev)
                        lab.call_ix(0x690B)
                        n += 1
                        got = lab.m[0xD502] == want
                        inside = cx <= fx < cx + 32 and cy <= fy < cy + 32
                        exp = inside and model_terrain_trigger(v[(fx - cx) & 31], fy - cy, prev, floor, vy >> 8, 5)
                        mism += got != exp
                        if got:
                            hits_x.add(fx - cx)
                            hits_y.add(fy - cy)
                rows.append({"previous_surface": pname, "previous_flags": h(prev, 2), "floor_flag": floor, "vy_hi": vy >> 8,
                             "cell_x_ranges": ranges(hits_x), "probe_y_ranges_relative_to_cell": ranges(hits_y)})
    return {"block": h(blk, 2), "cell": [cx, cy], "launch_state": h(want, 2), "vertical_profile_height_by_x": [r for r in hdr[h(blk, 2)]["vertical_profile_runs_[first,last,value]"]],
            "cases": n, "model_mismatches": mism, "rows": rows}


def terrain_gate_table(rom: bytes) -> dict:
    lab = Lab(rom)
    out = {}
    n = 0
    for name, cx, cy, want in (("upright_blk30", 928, 640, 0x0B), ("diagonal_right_blk36", 2464, 256, 0x1C), ("diagonal_left_blk38", 1664, 512, 0x1C)):
        fx = cx + (16 if name.startswith("upright") else (8 if "right" in name else 24))
        fy = cy + 20
        row = {}
        for vy in (0x8000, 0xFF00, 0xFFFF, 0x0000, 0x0001, 0x0100):
            lab.player(fx, fy - 18, vy=vy, floor=1, prev=0x81)
            lab.call_ix(0x690B)
            n += 1
            row[f"vy_{vy:04X}"] = {"launched": lab.m[0xD502] == want, **{k: (h(v, 4) if k in ("vx", "vy") else v) for k, v in lab.snap().items() if k in ("vx", "vy", "d448", "snd", "f4")}}
        cur = {}
        for c in (0x00, 0x05, 0x09, 0x0A, 0x0B, 0x0E, 0x11, 0x1B, 0x1C):
            lab.player(fx, fy - 18, vy=0, floor=1, prev=0x81, cur=c)
            lab.call_ix(0x690B)
            n += 1
            cur[h(c, 2)] = lab.m[0xD502] == want
        req = {}
        for r in (0x05, 0x0A, 0x11, 0x21):
            lab.player(fx, fy - 18, vy=0, floor=1, prev=0x81, req=r)
            lab.call_ix(0x690B)
            n += 1
            req[h(r, 2)] = lab.m[0xD502] == want
        lab.player(fx, fy - 18, vy=0, floor=1, prev=0x81, f3=0x03)
        lab.call_ix(0x690B)
        n += 1
        row["current_state_launches"] = cur
        row["requested_state_launches"] = req
        out[name] = row
    # D297 (zone byte) selects the diagonal Y speed
    d297 = {}
    for z in range(8):
        lab.player(2464 + 8, 256 + 20 - 18, vy=0, floor=1, prev=0x81, d297=z)
        lab.call_ix(0x690B)
        n += 1
        d297[str(z)] = h(lab.o.word(0xD518))
    out["diagonal_y_speed_by_$D297"] = d297
    out["cases"] = n
    out["rules"] = ["current state $D501 == $11 rejects; every other current state passes (including $0B and $1C: a spring can re-trigger inside its own flight once vy >= 0)",
                    "requested state is not read by the terrain handlers",
                    "Y speed high byte negative rejects; zero passes ($6A80: LD A,(IX+$19); AND A; RET M)",
                    "upright: floor flag required by the handler ($6A7B); diagonal: same ($6A9A)",
                    "diagonal: X speed, facing bit (+4 bit 4) and $D448 are written BEFORE the Y-speed gate of $482D, so a negative Y speed leaves state and Y unchanged but still sets X speed, facing, D448 and sound"]
    return out


def terrain_horizontal(rom: bytes) -> dict:
    import rom as R
    out = {"blocks": {}, "cases": 0}
    for act, cx, cy, blk in (("thz1", 3200, 832, 0x33), ("thz2", 3264, 256, 0x34), ("thz2", 1856, 512, 0x34), ("thz2", 3040, 864, 0x35)):
        lab = Lab(rom, act)
        hd = R.header(rom, blk)
        Hp = hd["horizontal"]
        res = {}
        for side, addr in (("right_probe_$716B", 0x716B), ("left_probe_$7210", 0x7210)):
            pts = {}
            mism = 0
            for x in range(cx - 24, cx + 56):
                for y in range(cy - 30, cy + 34):
                    lab.player(x, y, floor=1)
                    lab.m[0xD523] = 0
                    lab.call_ix(addr)
                    out["cases"] += 1
                    got = lab.m[0xD502] == 9
                    probe_x = x + (9 if addr == 0x716B else -9)
                    probe_y = y + 6
                    inside = cx <= probe_x < cx + 32 and cy <= probe_y < cy + 32
                    exp = inside and model_side_hit(Hp, probe_x - cx, probe_y - cy, addr == 0x716B)
                    mism += got != exp
                    if got:
                        pts[(x, y)] = lab.snap()
            xs = [p[0] - cx for p in pts]
            ys = [p[1] - cy for p in pts]
            vx = sorted({h(v["vx"]) for v in pts.values()})
            res[side] = {"player_x_ranges_relative_to_cell": ranges(xs), "player_y_ranges_relative_to_cell": ranges(ys), "vx": vx, "cap_D373": sorted({h(v["cap"]) for v in pts.values()}),
                         "f3_after": sorted({v["f3"] for v in pts.values()}), "fl22_after": sorted({h(v["fl22"], 2) for v in pts.values()}), "model_mismatches": mism}
        out["blocks"][f"{act}:{h(blk, 2)}@({cx},{cy})"] = res
    lab = Lab(rom)
    gates = {}
    for name, kw in (("baseline", {}), ("current_state_11", {"cur": 0x11}), ("requested_state_11", {"req": 0x11}), ("airborne_no_floor_flag", {"floor": 0}),
                     ("vy_negative", {"vy": 0xFF00}), ("vy_positive", {"vy": 0x0300}), ("f3_airborne", {"f3": 1})):
        lab.player(3200 - 1, 832 + 10, **{"floor": 1, **kw})
        lab.m[0xD523] = 0
        lab.call_ix(0x716B)
        out["cases"] += 1
        gates[name] = {"launched": lab.m[0xD502] == 9, **{k: (h(v) if k in ("vx", "vy") else v) for k, v in lab.snap().items() if k in ("vx", "vy", "f3", "fl22", "cap", "d448")}}
    out["gates"] = gates
    out["rules"] = ["no floor-flag, Y-speed or requested-state gate; only current state != $11 (the spring tail tests $D501 == $11 at $7204/$72AA)",
                    "activation is the ordinary side projection: the side probe point (X +- 9, Y + 6) must lie inside the block's solid horizontal profile and the projection must be non-zero; the launch is applied after the projection moved Sonic out of the wall",
                    "left-half blocks $32/$33: solid columns 0..15 of the cell, rows 8..27; right-half $34/$35: columns 16..31, rows 8..27 (profile bit 6 flips the side)",
                    "right probe launches X = -6.0 ($FA00) via $4868; left probe launches X = +6.0 ($0600) via $4849; Y speed untouched; $D448 untouched; speed cap $D373 = $0600"]
    return out


def terrain_ceiling(rom: bytes) -> dict:
    lab = Lab(rom)
    col, row = 10, 5
    cx, cy = col * 32, row * 32
    idx = LAYOUT_BASE + row * LAYOUT_W["thz1"] + col
    orig = lab.m[idx]
    import rom as R
    out, n = {}, 0
    for blk in (0x3A, 0x3B, 0x36, 0x38):
        v = R.header(rom, blk)["vertical"]
        lab.m[idx] = blk
        hits, mism = [], 0
        for x in range(cx - 4, cx + 36):
            for y in range(cy - 10, cy + 30):
                lab.player(x, y, vy=0xFF00, floor=0)
                lab.call_ix(0x73C9)
                n += 1
                got = lab.m[0xD502] == 0x1B
                px, py_probe = x, y - 6
                inside = cx <= px < cx + 32 and cy <= py_probe < cy + 32
                exp = inside and blk in BLOCK_CEILING_SPRING and model_ceiling_hit(v[(px - cx) & 31], py_probe - cy)
                mism += got != exp
                if got:
                    hits.append((x - cx, py_probe - cy))
        out[h(blk, 2)] = {"cells_hit": len(hits), "cell_x_ranges": ranges([a for a, _ in hits]), "probe_y_ranges_relative_to_cell": ranges([b for _, b in hits]), "model_mismatches": mism}
    lab.m[idx] = 0x3A
    lab.player(cx + 8, cy + 10, vy=0xFF00, floor=0)
    lab.call_ix(0x73C9)
    n += 1
    s = lab.snap()
    out["launch_0x3A"] = {"state": h(s["req"], 2), "vx": h(s["vx"]), "vy": h(s["vy"]), "f3": s["f3"], "fl22": h(s["fl22"], 2), "sound": h(s["snd"], 2)}
    gates = {}
    for name, kw in (("vy_zero", {"vy": 0}), ("vy_positive", {"vy": 0x0100}), ("vy_negative", {"vy": 0xFF00}), ("floor_flag", {"floor": 1}), ("underwater_flag_D3C0_vy0", {"vy": 0})):
        lab.player(cx + 8, cy + 10, **{"floor": 0, "vy": 0xFF00, **kw})
        if name.startswith("underwater"):
            lab.m[0xD3C0] = 1
        lab.call_ix(0x73C9)
        n += 1
        gates[name] = lab.m[0xD502] == 0x1B
    out["gates"] = gates
    lab.m[idx] = orig
    out["cases"] = n
    out["note"] = "blocks $3A/$3B appear in no THZ1/THZ2/THZ3 layout cell (layout scan); type $15 ($748F: Y +7.5 down, no X) has no THZ block either"
    return out


def bounce_blocks(rom: bytes) -> dict:
    """Types $16/$0D: breakable blocks that also rebound the player (-4.25). Included because they are the other terrain launches."""
    lab = Lab(rom)
    out, n = {}, 0
    for name, addr, ex in (("type_16_6AE3", 0x6AE3, "vy>=0 or side contact"), ("type_0D_6B2C", 0x6B2C, "none")):
        rows = {}
        for f3 in (0, 1, 2, 3):
            lab.player(1000, 700, vy=0x0100, floor=0, f3=f3)
            lab.m[0xD522] = 0x04
            lab.m[0xD36B] = 0x47
            lab.o.word(0xD354, 0xC001)
            lab.o.word(0xD358, 1000)
            lab.o.word(0xD35A, 718)
            lab.call_ix(addr)
            n += 1
            rows[f"f3={f3}"] = {"vy": h(lab.o.word(0xD518)), "f3_after": lab.m[0xD503]}
        out[name] = rows
    return {"evidence": "CONTROLLED ROUTINE RESULT", "cases": n, "rows": out,
            "gate": "BIT 1,(IX+3) must be set (the rolling/attack flag $D503 bit 1) and the current state must not be $0F/$10/$15/$1A; then vy = $FBC0 (-4.25), airborne set, floor cleared and the block is replaced ($7857 -> $46, $7898 -> $9D)",
            "relevance": "upright-spring flight has $D503 bit 1 clear (cannot break these); the diagonal spring ($1C) and horizontal spring (state 9) have it set"}


# --------------------------------------------------------------------------- #
# 3. launch table (before / after) from the original setters
# --------------------------------------------------------------------------- #
def launch_table(rom: bytes) -> dict:
    lab = Lab(rom)
    keep_b = ("cur", "req", "f3", "vx", "vy", "fl22", "d448", "cap")
    keep_a = ("cur", "req", "f3", "f4", "vx", "vy", "fl22", "d448", "snd", "cap")

    def fmt(snap, keys):
        return {k: (h(v) if k in ("vx", "vy", "cap") else v) for k, v in snap.items() if k in keys}

    def prep(block=0x36, vy=0x0100, f3=0x03, floor=1, cur=0x0A, d297=0):
        lab.player(1000, 700, vx=0x0123, vy=vy, floor=floor, cur=cur, req=cur, f3=f3, d297=d297)
        lab.o.word(0xD373, 0x0555)
        lab.o.word(0xD36B, block)       # D36B = sampled block id (diagonal direction)
        lab.m[0xD36C] = 0x54

    rows = []

    def add(name, run, note):
        before = lab.snap()
        run()
        rows.append({"mechanism": name, "before": fmt(before, keep_b), "after": fmt(lab.snap(), keep_a), "note": note})

    prep(); add("terrain upright (type 9) $6A75", lambda: lab.call_ix(0x6A75), "vx and cap untouched; state $0B; D448=$FF")
    prep(0x36); add("terrain diagonal, block < $38 $6A90", lambda: lab.call_ix(0x6A90), "vx=+4.0; facing bit +4.4 cleared; D448=0; sound $A6; Y = $F900 (-7.0) because $D297 == 0")
    prep(0x38); add("terrain diagonal, block >= $38 $6A90", lambda: lab.call_ix(0x6A90), "vx=-4.0; facing bit +4.4 set")
    prep(0x36, d297=1); add("terrain diagonal, $D297 != 0", lambda: lab.call_ix(0x6A90), "Y = $FA80 (-5.5)")
    prep(); add("setter $480C, HL=$F880", lambda: lab.call_hl(0x480C, 0xF880), "state $0B; vy=HL; vx/cap untouched")
    prep(); add("setter $482D, HL=$F900", lambda: lab.call_hl(0x482D, 0xF900), "state $1C; vy=HL; +3 bits 0 and 1 set")
    prep(); add("setter $4868 (right probe), HL=$FA00", lambda: lab.call_hl(0x4868, 0xFA00), "state 9; vx=-6.0; cap=$0600; +3 bit 0 clear, bit 1 set; Y speed untouched")
    prep(); add("setter $4849 (left probe), HL=$0600", lambda: lab.call_hl(0x4849, 0x0600), "state 9; vx=+6.0; cap=$0600")
    for name, p, aux in (("type $26 fixed strong (parameter $00) $82AF", 0, 0x72), ("type $26 fixed weak (parameter $01) $82AF", 1, 0x72)):
        lab.t26(1000, 800, 1000, 769, param=p, aux1=aux, vy=0x0100, f3=0x03, cur=0x0A, req=0x0A)
        lab.o.word(0xD516, 0x0123)
        lab.o.word(0xD373, 0x0555)
        add(name, lambda: lab.call_ix(0x82AF, OBJ, BANK_TYPE26), "vx and cap untouched; state $0B; vy -7.375 / -5.0; D448 $FF / 0")
    # negative Y speed: nothing is written by $480C
    prep(); lab.o.word(0xD518, 0xFF00); add("setter $480C with negative Y speed", lambda: lab.call_hl(0x480C, 0xF880), "rejected: no field changes")
    prep(); lab.o.word(0xD518, 0xFF00); add("setter $482D with negative Y speed", lambda: lab.call_hl(0x482D, 0xF900), "rejected: no field changes")
    prep(); lab.o.word(0xD518, 0xFF00); add("setter $4868 with negative Y speed", lambda: lab.call_hl(0x4868, 0xFA00), "NOT gated: horizontal springs launch regardless of Y speed")
    return {"evidence": "CONTROLLED ROUTINE RESULT", "rows": rows,
            "summary": {
                "$480C": "request $0B; vy = HL (unconditional: not additive, not clamped, independent of incoming speed and of the spring strength path); +3 bit 0 set, bit 1 CLEAR; +$22 bit 1 (floor) cleared; vx, facing, speed cap untouched; rejected (nothing written) when the Y speed is negative",
                "$482D": "request $1C; vy = HL; +3 bits 0 AND 1 set (airborne + rolling/attack); floor cleared; vx and facing are written by the caller $6A90 before the gate; rejected when the Y speed is negative",
                "$4849/$4868": "request 9 (rolling); vx = +-6.0 and speed cap $D373 = $0600; +3 bit 0 CLEAR, bit 1 set (grounded roll); floor flag cleared; Y speed untouched; no Y-speed gate",
                "position": "no spring snaps Sonic's position beyond the ordinary terrain projection that precedes it; the type $26 span form moves the OBJECT X to playerX & $FFF0"}}


# --------------------------------------------------------------------------- #
# 4. attacking
# --------------------------------------------------------------------------- #
def attack_tests(rom: bytes) -> dict:
    lab = Lab(rom)
    m, o = lab.m, lab.o
    n = 0
    t27 = {}
    for f3 in (0x00, 0x01, 0x02, 0x03, 0x41, 0x81, 0x83, 0xC3):
        for a in range(OBJ, OBJ + 0x40):
            m[a] = 0
        m[OBJ], m[OBJ + 0x21] = 0x27, 1
        m[0xD503], m[0xD532] = f3, 0
        lab.call_ix(0x5F3D, OBJ, 1)
        n += 1
        t27[h(f3, 2)] = m[OBJ] == 0x0F
    for a in range(OBJ, OBJ + 0x40):
        m[a] = 0
    m[OBJ], m[OBJ + 0x21] = 0x27, 1
    m[0xD503], m[0xD532] = 0, 6
    lab.call_ix(0x5F3D, OBJ, 1)
    n += 1
    power6 = m[OBJ] == 0x0F
    t21 = {}
    for f3 in (0, 1, 2, 3):
        for where in ("above", "beside"):
            for a in range(OBJ, OBJ + 0x40):
                m[a] = 0
            m[OBJ], m[OBJ + 0x21] = 0x21, 1
            o.word(OBJ + 0x14, 500)
            o.word(0xD514, 500 - 4 - 6 if where == "above" else 500 + 10)
            o.word(0xD518, 0)
            m[0xD503], m[0xD532], m[0xD448], m[0xD502], m[0xD501], m[0xD3B0] = f3, 0, 0x55, 5, 5, 0
            lab.call_ix(0xB2B2, OBJ, BANK_TYPE21)
            n += 1
            t21[f"D503={f3}_{where}"] = {"object_type_after": h(m[OBJ], 2), "converted_to_0F": m[OBJ] == 0x0F, "damage_request_D3B0": m[0xD3B0], "player_requested_state": h(m[0xD502], 2),
                                         "vy": h(o.word(0xD518)), "d448": h(m[0xD448], 2)}
    return {"evidence": "CONTROLLED ROUTINE RESULT", "cases": n,
            "type_27_$5F3D_converts_by_D503": t27, "type_27_converts_with_D532_6": power6,
            "type_21_$B2B2_tail": t21,
            "rule": "badnik callbacks test the player's movement flag $D503 bit 1 (the rolling/attack posture) - and for types $27/$21/$50 also power-up $D532 == 6 - never the player state number and never 'airborne' ($D503 bit 0); type $21 additionally resolves top contact (objectY - 4 >= playerY) as a stomp bounce BEFORE the attack test"}


# --------------------------------------------------------------------------- #
# 5. emulated original frames
# --------------------------------------------------------------------------- #
def _emu():
    from sms_frame_harness import BTN_RIGHT, BTN_LEFT, BTN_DOWN, BTN_UP, BTN_1
    return _load("object_18"), dict(RIGHT=BTN_RIGHT, LEFT=BTN_LEFT, DOWN=BTN_DOWN, UP=BTN_UP, B1=BTN_1)


def _boot(rom, act_idx):
    o18, _ = _emu()
    s = o18._boot(rom, act_idx, lambda m: None)
    for _ in range(60):
        s.pad = 0
        s.run_frame()
    return s


def _place(s, x, y, vx=0, vy=0):
    cx, cy = max(x - 104, 0), max(y - 100, 8)
    for a in (0xD174, 0xD284):
        s.w16(a, cx)
    for a in (0xD176, 0xD286):
        s.w16(a, cy)
    s.w16(0xD511, x)
    s.w16(0xD514, y)
    s.w16(0xD516, vx)
    s.w16(0xD518, vy)
    s.mem[0xD440] = 0           # forces the initial-fill creation of mapped objects around the camera


def _rec(s):
    m = s.mem
    return {"cur": m[0xD501], "req": m[0xD502], "f3": m[0xD503], "x": s.u16(0xD511), "y": s.u16(0xD514), "vx": s.u16(0xD516), "vy": s.u16(0xD518), "fl22": m[0xD522],
            "d448": m[0xD448], "sy": s.u16(0xD51C), "camy": s.u16(0xD176), "cap": s.u16(0xD373), "d293": m[0xD293]}


def _run(s, frames, padf, thrust=None):
    tr = []

    def on_cb(_):
        if s.cpu.ix == 0xD500:
            tr.append(_rec(s))
            if thrust is not None:
                s.w16(0xD518, thrust)
    s.add_pc_hook(0x5E91, on_cb)
    for f in range(frames):
        s.pad = padf(f)
        s.run_frame()
    return tr


def _segments(tr, limit=None):
    out, prev = [], None
    for i, t in enumerate(tr[:limit]):
        key = (t["cur"], t["f3"], t["d448"], t["cap"])
        if key != prev:
            out.append({"update": i, "state": h(t["cur"], 2), "f3": t["f3"], "d448": h(t["d448"], 2), "cap": h(t["cap"]), "x": t["x"], "y": t["y"], "vx": s16(t["vx"]), "vy": s16(t["vy"]),
                        "floor_flag": bool(t["fl22"] & 2), "updates": 1})
            prev = key
        else:
            out[-1]["updates"] += 1
    return out


def emulated_flights(rom: bytes) -> dict:
    """THZ1 flights from every spring kind + normal jump/roll, per-update flag record (attack classification)."""
    _, B = _emu()
    cases = [
        ("type26_strong_(688,864)", 0, 688, 846, 0x0100, lambda f: 0, 120),
        ("type26_weak_(1912,864)", 0, 1912, 846, 0x0100, lambda f: 0, 70),
        ("type26_span_8A_(1296,608)", 0, 1300, 590, 0x0100, lambda f: 0, 70),
        ("terrain_upright_(928,640)", 0, 944, 596, 0x0100, lambda f: 0, 120),
        ("terrain_diagonal_right_(2464,256)", 0, 2470, 222, 0x0100, lambda f: 0, 120),
        ("terrain_diagonal_left_(1664,512)", 0, 1688, 478, 0x0100, lambda f: 0, 70),
        ("terrain_horizontal_(3200,832)_run_left", 0, 3262, 790, 0x0100, lambda f: B["LEFT"], 90),
        ("normal_jump_run_then_jump", 0, 600, 600, 0x0100, lambda f: B["RIGHT"] | (B["B1"] if 60 <= f < 75 else 0), 110),
        ("roll_run_then_down", 0, 600, 600, 0x0100, lambda f: B["RIGHT"] | (B["DOWN"] if 60 <= f < 80 else 0), 110),
        ("jump_into_terrain_upright_(928,640)", 0, 600, 600, 0x0100, lambda f: B["RIGHT"] | (B["B1"] if 60 <= f < 61 else 0), 140),
    ]
    rows = []
    for name, act, x, y, vy, pad, frames in cases:
        s = _boot(rom, act)
        _place(s, x, y, vy=vy)
        tr = _run(s, frames, pad)
        rows.append({"case": name, "start": [x, y], "segments": _segments(tr, 140)})
    return {"evidence": "EMULATED ORIGINAL FRAME", "method": "THZ1 booted in tools/sms_frame_harness.py, Sonic teleported with the camera, spring objects force-created ($D440 = 0); PC hook at the player callback entry $5E91 records +$01,+$02,+$03,speeds,flags,$D448,$D373",
            "rows": rows,
            "flag_reading": "f3 = $D503: bit0 airborne, bit1 rolling/attack posture. Spring flights: upright ($0B/$0E) f3=1 (NOT attacking); diagonal $1C f3=3 (attacking) until the apex request $0E clears bit 1; horizontal state 9 f3=2 (attacking, grounded roll); normal jump $0A f3=3; roll 9 f3=2; a jump (f3=3) that lands on the upright spring becomes $0B with f3=1 (the spring clears the attack posture)"}


def emulated_placements(rom: bytes) -> dict:
    """Every canonical spring placement in THZ1/THZ2/THZ3 launched in the original engine."""
    rows = []
    for act in ACTS:
        idx = ACT_INDEX[act]
        for p in type26_placements(act):
            s = _boot(rom, idx)
            span = p["span_width_px"]
            x = p["world_x"] + (5 if span else 0)
            y = p["world_y"] - 18 if not span else p["world_y"] - 20
            _place(s, x, y, vy=0x0100)
            tr = _run(s, 140, lambda f: 0)
            first = next((i for i, t in enumerate(tr) if t["cur"] == 0x0B), None)
            if first is None:
                rows.append({"act": act, "kind": "type26", "world": [p["world_x"], p["world_y"]], "parameter": p["parameter"], "launched": False})
                continue
            seg = tr[first:first + 120]
            n_0b = 0
            for t in seg:
                if t["cur"] != 0x0B:
                    break
                n_0b += 1
            apex = min(t["y"] for t in seg[:n_0b + 30])
            rows.append({"act": act, "kind": "type26", "world": [p["world_x"], p["world_y"]], "parameter": p["parameter"], "launched": True, "d448": h(seg[0]["d448"], 2),
                         "vy": s16(seg[0]["vy"]) / 256, "updates_in_state_0b": n_0b, "start_y": seg[0]["y"], "apex_y": apex, "rise": seg[0]["y"] - apex,
                         "f3_in_flight": sorted({t["f3"] for t in seg[:n_0b]})})
        for c in terrain_cells(act):
            if c["kind"] not in ("upright", "diagonal_right_launch", "diagonal_left_launch"):
                continue
            s = _boot(rom, idx)
            cx, cy = c["world_x"], c["world_y"]
            x = cx + (16 if c["kind"] == "upright" else (8 if c["kind"] == "diagonal_right_launch" else 24))
            _place(s, x, cy - 50, vy=0x0100)
            tr = _run(s, 150, lambda f: 0)
            first = next((i for i, t in enumerate(tr) if t["cur"] in (0x0B, 0x1C)), None)
            if first is None:
                rows.append({"act": act, "kind": c["kind"], "world": [cx, cy], "launched": False})
                continue
            seg = tr[first:first + 130]
            first_state = seg[0]["cur"]
            n_st = 0
            for t in seg:
                if t["cur"] != first_state:
                    break
                n_st += 1
            apex_i = min(range(len(seg)), key=lambda i: seg[i]["y"])
            rows.append({"act": act, "kind": c["kind"], "block": c["block"], "world": [cx, cy], "launched": True, "state": h(first_state, 2), "d448": h(seg[0]["d448"], 2),
                         "vx": s16(seg[0]["vx"]) / 256, "vy": s16(seg[0]["vy"]) / 256, "updates_in_state": n_st, "start_y": seg[0]["y"],
                         "apex_y_within_flight": min(t["y"] for t in seg[:n_st + 40]), "min_screen_y": min(s16(t["sy"]) for t in seg[:n_st + 40]),
                         "died": any(t["cur"] == 0x1F for t in seg)})
    return {"evidence": "EMULATED ORIGINAL FRAME", "rows": rows,
            "note": "apex_y is the lowest world Y within the launch state plus 40 updates; a chain onto another spring can lift a later apex, so the first-launch apex is the comparable figure"}


def emulated_horizontal(rom: bytes) -> dict:
    """Run into every horizontal spring cell from its open side; several start offsets are tried (the approach ground differs per placement)."""
    _, B = _emu()
    rows = []
    for act, cx, cy, blk in (("thz1", 3200, 832, 0x33), ("thz2", 3264, 256, 0x34), ("thz2", 1856, 512, 0x34), ("thz2", 3040, 864, 0x35)):
        left_half = blk in (0x32, 0x33)
        result = {"act": act, "block": h(blk, 2), "cell": [cx, cy], "launched": False}
        for off in (62, 30, 90, 120, 48):
            for dy in (-40, -70, -10):
                s = _boot(rom, ACT_INDEX[act])
                x = cx + off if left_half else cx - off
                _place(s, x, cy + dy, vy=0x0100)
                tr = _run(s, 150, lambda f: B["LEFT"] if left_half else B["RIGHT"])
                first = next((i for i, t in enumerate(tr) if t["cur"] == 9 and t["cap"] == 0x0600), None)
                if first is not None:
                    result = {"act": act, "block": h(blk, 2), "cell": [cx, cy], "launched": True, "start": [x, cy + dy], "vx": s16(tr[first]["vx"]) / 256, "cap": h(tr[first]["cap"]),
                              "f3_low_bits": tr[first]["f3"] & 3, "d448_unchanged": tr[first]["d448"] == tr[first - 1]["d448"]}
                    break
            if result["launched"]:
                break
        rows.append(result)
    return {"evidence": "EMULATED ORIGINAL FRAME", "rows": rows}


def emulated_type26_cycle(rom: bytes) -> dict:
    s0 = None
    out = {}
    for name, x, y, sx, sy in (("strong_(688,864)", 688, 846, 688, 864), ("weak_(1912,864)", 1912, 846, 1912, 864)):
        s = _boot(rom, 0)
        _place(s, x, y, vy=0x0100)
        seq = []
        for f in range(110):
            s.pad = 0
            s.run_frame()
            for i in range(19):
                b = 0xD540 + i * 0x40
                if s.mem[b] == 0x26 and s.u16(b + 0x11) == sx:
                    seq.append((f, s.mem[b + 2], s.u16(b + 0x14), s.mem[b + 0x1E], s.mem[b + 4]))
        tl, prev = [], None
        for f, st, yy, cnt, f4 in seq:
            if (st, yy) != prev:
                tl.append({"frame": f, "requested_state": st, "object_y": yy, "counter_1E": cnt})
            prev = (st, yy)
        launch = next((t["frame"] for t in tl if t["requested_state"] in (1, 3)), None)
        back = next((t["frame"] for t in tl if t["frame"] > (launch or 0) + 3 and t["requested_state"] == 7), None)
        out[name] = {"timeline": tl[:16], "launch_frame": launch, "back_to_contact_state_frame": back, "retrigger_free_updates": (back - launch) if (launch is not None and back) else None}
    return {"evidence": "EMULATED ORIGINAL FRAME", "rows": out}


def emulated_top_of_screen(rom: bytes) -> dict:
    """What the original does when Sonic goes above the top of the level: forced Y speed -8.0 in state $0B."""
    s = _boot(rom, 0)
    _place(s, 2470, 120, vy=0xF800)
    s.mem[0xD502] = 0x0B
    tr = _run(s, 200, lambda f: 0, thrust=0xF800)
    rows = []
    for i, t in enumerate(tr):
        if i % 24 == 0 or t["cur"] == 0x1F:
            rows.append({"update": i, "state": h(t["cur"], 2), "world_y_raw": t["y"], "world_y_signed": s16(t["y"]), "screen_y_signed": s16(t["sy"]), "camera_y": t["camy"], "life_lost_flag_D293_bit2": bool(t["d293"] & 4)})
    return {"evidence": "EMULATED ORIGINAL FRAME",
            "method": "THZ1, Sonic at (2470,120); Y speed forced to -8.0 on every player update for 200 updates (an artificial thrust far beyond any spring; the engine moves him to $0E)",
            "rows": rows, "min_signed_world_y": min(s16(t["y"]) for t in tr), "died": any(t["cur"] == 0x1F for t in tr),
            "camera_y_final": tr[-1]["camy"],
            "reading": "the camera stops at its top limit (8); world Y wraps below zero as an unsigned 16-bit value; screen Y goes arbitrarily negative; no death, no clamp, no state change"}


def death_boundary(rom: bytes) -> dict:
    """Controlled run of $401A: screen Y thresholds. The routine is run until it returns or jumps to the death start $4984."""
    lab = Lab(rom)
    rows = []
    for sy in (-300, -1, 0, 192, 207, 208, 209, 215, 216, 400, 32767):
        lab.player(600, 400, cur=5, req=5)
        lab.o.word(0xD51C, sy & 0xFFFF)
        reached = lab.call_watch(0x401A, 0x4984)
        rows.append({"screen_y_$D51C": sy, "died": reached == 0x4984})
    first = next(r["screen_y_$D51C"] for r in rows if r["died"])
    return {"evidence": "CONTROLLED ROUTINE RESULT", "routine": "$401A (called from $3FEF every shared-movement update)", "rows": rows,
            "first_fatal_screen_y_in_sample": first,
            "rule": "death ($4984: state $1F, vy -5.0, $D293 bit 2) iff signed screen Y ($D51C = playerY - cameraY, computed by $3FC8) is non-negative and >= $D0 (208); negative values (above the camera) are never fatal; the dying-state check at $3C09 uses $D8"}


# --------------------------------------------------------------------------- #
# 6. $D448 and state reach
# --------------------------------------------------------------------------- #
def d448_role(rom: bytes) -> dict:
    occ = []
    i = 0
    while True:
        i = rom.find(b"\x48\xd4", i)
        if i < 0:
            break
        occ.append(i - 1)
        i += 1
    prev = json.loads((ROOT / "data" / "rom-cache" / "player-animation-counter.json").read_text(encoding="utf-8"))
    return {"evidence": "BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT",
            "occurrences_of_address_bytes": [h(o, 5) for o in occ],
            "reader": "ROM $3018F (bank $0C, CPU $818F): LD A,($D448); RRCA; RET - used only by the FF 08 condition at the head of the state $0B animation script",
            "writers": {"$06A87": ["terrain upright spring", "$FF"], "$06AC8": ["terrain diagonal spring", "$00"], "$332CC": ["type $21 stomp", "$FF"],
                        "$782F8": ["type $26 fixed contact", "$FF if parameter 0 else $00"], "$78420": ["type $26 span launch", "$FF if +$3F == 0 else $00"],
                        "$799CA": ["type $50 top bounce", "$00"]},
            "state_0b_entry_guarantee": "$480C is the only code that requests state $0B and every caller ($6A8D, $5F21 through vector $035F from $82FB/$8423/$99D0/$B2D2) writes $D448 first; a stale value is therefore never observed",
            "meaning": "bit 0 only chooses the animation fragment of state $0B when the script is (re)started: set -> hold frame $61 (duration 4, repeating); clear -> frames $1C..$21 cycle. It affects presentation and the animation counter values, nothing else",
            "does_not_affect": "velocity, gravity, apex/landing decisions, controls, collision, attack posture ($D503), damage, terrain-ring parity (docs/player-animation-counter.md sect. 10)",
            "distinction": "strong ($FF): terrain upright, type $26 parameter 0 / aux1 = 0 span, type $21 stomp; weak ($00): type $26 nonzero parameter, boss bounce; diagonal writes 0 but enters $1C which has no D448 reader",
            "persistence": "never cleared by landing, act start or the diagonal spring ($1C does not read it); zeroed only by the boot/reset RAM clears; persistence across acts is irrelevant because of the guarantee above",
            "consistent_with_previous_audit": prev["d448_audit"]["all_occurrences_of_the_address_bytes"] and len(prev["d448_audit"]["all_occurrences_of_the_address_bytes"]) == len(occ)}


def state_reach() -> dict:
    prev = json.loads((ROOT / "data" / "rom-cache" / "terrain-ring-collection.json").read_text(encoding="utf-8"))
    st = prev["state_reach"]
    return {"evidence": "EMULATED ORIGINAL FRAME + SOURCE-TRACED BEHAVIOR (reused from terrain-ring-collection.json)", "source_keys": list(st.keys()),
            "meaning": "the terrain probe $753E sits inside $690B; a state that never calls it never runs $690B, so terrain springs (and the ceiling/side special tiles) cannot trigger in it",
            "state_reach": st}


def special_states() -> dict:
    return {
        "type_26": {"gate": "requested state == $21 only", "loop_states_0C_0D_13": "contact evaluated (not read)", "twist_22": "evaluated", "act_clear_20": "evaluated",
                    "rolling_jump_fall": "evaluated", "spring_flight_0B_1C": "evaluated; Y speed must be non-negative so a launch cannot restart during the rise",
                    "forced_transition": "$480C requests $0B from ANY state whenever the gates pass (it only checks the Y-speed sign), overriding loop/twist/act-clear requests; velocity is overwritten (vy only)"},
        "terrain_upright_diagonal_horizontal_ceiling": {"gate": "current state $11 blocks upright/diagonal/horizontal; the ceiling bounce has no state gate",
                                                         "loop_states_0C_0D_13_and_twist_22_and_20": "not evaluated: these states never call $690B (terrain-ring state reach)",
                                                         "evaluated_states": "see state_reach", "forced_transition": "yes: $0B / $1C / 9 / $1B override the current state"},
    }


# --------------------------------------------------------------------------- #
# 7. presentation / gameplay anchors
# --------------------------------------------------------------------------- #
def anchors() -> dict:
    return {"type_26": {"gameplay_anchor": "object +$11/+$12 (X) and +$14/+$15 (Y); placement X is used unchanged; Y is placement Y + 12 after $825A (rest position)",
                        "contact_window": "player anchor Y in [restY - 33, restY - 28] = [placementY - 21, placementY - 16]; |dx| < 12; floor-standing Sonic has anchor Y = floorSurface - 18 which is placementY - 18 when the floor surface is at the placement Y (verified for the THZ1 control placements)",
                        "mapping_anchor": "mapping $91C0 frame records are drawn relative to the same object coordinates (docs/mapped-object-screen-registration.md: rows -6..+17 for frame 2); at rest the object sits 12 px below the placement Y, so the dormant frame is mostly below the floor line",
                        "animation": "the extension raises the OBJECT Y 7 px per update (+$14), 4 updates = 28 px (rest -> placementY - 16); contact is not evaluated in states 1..6, so the moving art never feeds back into collision",
                        "poc_guidance": "keep the contact window and X rule on the placement-derived rest anchor; do not derive them from the sprite's visible top (it changes with the frame and extension) or the GameMaker mask"},
            "terrain_springs": {"gameplay_anchor": "layout cell + collision header profile only; the visible spring art is ordinary background tiles with no separate object", "probe": "upright/diagonal: (X, Y+18); horizontal: (X+-9, Y+6); ceiling: (X, Y-6)"}}


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #
UNRESOLVED = [
    "Names of the terrain flag types ($09, $14, $0A, $16, $0D) are numeric only; 'spring' follows from the launches, not from a ROM label.",
    "The identity of player state $21 (requested-state gate of type $26, probe dy -14): numeric only.",
    "Exact camera Y scroll speed limits during the rise (the emulated flights stay inside the view; no formal bound was derived).",
    "Which POC mechanism produces the reported top-of-screen death was not reproduced (POC untouched); the ROM facts it must be compared against are in death_and_top_of_screen.",
    "Type $26 states 1..6 art/frame timing was recorded from the script table but not pixel-validated against the SMS frame.",
    "Whether a spring launch can interact with the badnik lifecycle beyond the $D503 gate (e.g. type $27 contact above) was not traced end to end in the emulator.",
    "Behavior outside THZ (other zones' diagonal Y speed $FA80 for $D297 != 0 was verified only as an immediate value, not on a zone layout).",
]


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    out = {
        "format": 1, "rom_sha256": ROM_SHA256, "research_only": True, "poc_untouched": True, "machine_facing_label": "spring_interaction",
        "evidence_classes": EVIDENCE,
        "routines": routine_table(rom),
        "terrain_handler_table": handler_table(rom),
        "terrain_blocks": block_headers(rom),
        "terrain_spring_cells": {act: terrain_cells(act) for act in ACTS},
        "type26_placements": {act: type26_placements(act) for act in ACTS},
        "type26_script_table": t26_script_table(rom),
        "anchors": anchors(),
        "special_states": special_states(),
        "d448": d448_role(rom),
        "state_reach": state_reach(),
        "unresolved": UNRESOLVED, "static_only": static_only,
    }
    if not static_only:
        out["type26_geometry"] = t26_geometry(rom)
        out["type26_gates"] = t26_gates(rom)
        out["type26_span"] = t26_span(rom)
        out["type26_parameters"] = t26_parameters(rom)
        out["type26_state_matrix"] = t26_state_matrix(rom)
        hdr = out["terrain_blocks"]
        out["terrain_upright"] = terrain_vertical(rom, "upright", 928, 640, 0x0B, hdr)
        out["terrain_diagonal_right_launch"] = terrain_vertical(rom, "diagonal", 2464, 256, 0x1C, hdr)
        out["terrain_diagonal_left_launch"] = terrain_vertical(rom, "diagonal", 1664, 512, 0x1C, hdr)
        out["terrain_gates"] = terrain_gate_table(rom)
        out["terrain_horizontal"] = terrain_horizontal(rom)
        out["terrain_ceiling"] = terrain_ceiling(rom)
        out["bounce_blocks"] = bounce_blocks(rom)
        out["launch_table"] = launch_table(rom)
        out["attack_state"] = attack_tests(rom)
        out["death_boundary"] = death_boundary(rom)
        out["emulated_flights"] = emulated_flights(rom)
        out["emulated_placements"] = emulated_placements(rom)
        out["emulated_horizontal"] = emulated_horizontal(rom)
        out["emulated_type26_cycle"] = emulated_type26_cycle(rom)
        out["emulated_top_of_screen"] = emulated_top_of_screen(rom)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    a = ap.parse_args()
    rom = a.rom.read_bytes()
    data = build(rom, a.static_only)
    text = json.dumps(data, indent=1) + "\n"
    if a.check:
        cached = OUTPUT.read_text(encoding="utf-8")
        if a.static_only:
            cj, dj = json.loads(cached), json.loads(text)
            bad = [k for k in dj if k in cj and k != "static_only" and cj[k] != dj[k]]
        else:
            bad = [] if cached == text else ["file"]
        print("OK: cache matches the ROM" if not bad else f"MISMATCH in {bad}")
        sys.exit(1 if bad else 0)
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT} ({len(text)} bytes)")


if __name__ == "__main__":
    main()

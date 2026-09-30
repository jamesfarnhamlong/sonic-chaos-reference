#!/usr/bin/env python3
"""THZ2/THZ3 object parameter deltas for types $26, $10 and $28 (research only).

Every claim is produced either by decoding the canonical level package
(data/rom-cache/levels/*/objects.json) or by executing original ROM routines in
the repository Oracle (a Z80 routine harness, not an emulator).  The ROM is read
from $SONIC_CHAOS_ROM (or --rom) and is never committed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
LEVELS = ROOT / "data" / "rom-cache" / "levels"
OUTPUT = LEVELS / "object-deltas.json"
ACTS = ("thz1", "thz2", "thz3")


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def s16(v: int) -> int:
    return (v + 0x8000) % 0x10000 - 0x8000


def hx(v: int, width: int = 2) -> str:
    return f"0x{v:0{width}X}"


def load_rom(path: str | None = None) -> bytes:
    from rom import load
    return load(path or os.environ["SONIC_CHAOS_ROM"])


def records(act: str, type_id: int) -> list[dict]:
    data = json.loads((LEVELS / act / "objects.json").read_bytes())
    rows = []
    for r in data["records"]:
        if int(r["type_id"], 16) != type_id:
            continue
        rows.append({
            "act": act, "record_index": r["index"], "rom_offset": r["rom_offset"],
            "bank": r["bank"], "cpu": r["cpu"], "raw_bytes": r["raw_bytes"],
            "world_x": r["world_x"], "world_y": r["world_y"], "flags": r["flags"],
            "parameter": r["parameter"], "aux0": r["aux0"], "aux1": r["aux1"],
        })
    return rows


def _oracle(rom: bytes, bank: int):
    from oracle import Oracle
    o = Oracle(rom)
    o.bank(2, bank)
    o.mem[0xD12B] = bank
    return o


def _create_from_record(rom: bytes, rom_offset: int, object_bank: int):
    """Run the original placement creator ($700EB) on a real record, then map the object bank."""
    from oracle import Oracle
    o = Oracle(rom)
    o.bank(2, 0x1C)
    o.mem[0xD700:0xD740] = bytes(0x40)
    o.cpu.ix = 0xD700
    o.cpu.iy = 0xD700
    o.cpu.hl = 0x8000 + (rom_offset - 0x70000)
    o.call(0x80EB, bc=0xD418)
    o.bank(2, object_bank)
    o.mem[0xD12B] = object_bank
    o.cpu.ix = 0xD700
    return o


def _player(o, x: int, y: int, vy: int = 0x0100, state: int = 1) -> None:
    o.word(0xD511, x)
    o.word(0xD514, y)
    o.mem[0xD502] = state
    o.word(0xD518, vy)
    o.mem[0xD522] = 0x02
    o.mem[0xD503] = 0
    o.mem[0xD52C] = 9
    o.mem[0xD52D] = 18


# ----------------------------------------------------------------------------- $26
STRONG = 0xF8A0   # signed 8.8 = -7.375
WEAK = 0xFB00     # signed 8.8 = -5.0
GRAVITY_UPRIGHT_ASCENT = 0x18   # docs/movement.md: $18/256 per update


def rise_model(launch_8_8: int) -> dict:
    """Arithmetic on proven constants: gravity added, then the position moves, until vy >= 0.

    Matches the documented 296.25 px rise for -7.5 (80 updates).  Ignores collisions.
    """
    v = s16(launch_8_8)
    y_units = 0
    updates = 0
    while True:
        v += GRAVITY_UPRIGHT_ASCENT
        if v >= 0:
            break
        y_units += v
        updates += 1
    return {"launch_8_8": s16(launch_8_8), "updates_rising": updates,
            "rise_pixels": round(-y_units / 256, 2),
            "basis": "DERIVED: $480C launch + upright ascent gravity $18; excludes ceilings and the apex wrapper"}


def type26_init(rom: bytes, record: dict) -> dict:
    off = int(record["rom_offset"], 16)
    o = _create_from_record(rom, off, 0x1E)
    created = {
        "type": hx(o.mem[0xD700]), "x": o.word(0xD711), "y": o.word(0xD714),
        "flags_04": hx(o.mem[0xD704]), "parameter_3f": hx(o.mem[0xD73F]),
        "field_08_aux0": hx(o.mem[0xD708]), "field_09_aux1": hx(o.mem[0xD709]),
    }
    o.call(0x825A)
    param = int(record["parameter"], 16)
    result = {
        "created": created,
        "after_init_825A": {
            "requested_state_02": o.mem[0xD702], "rest_state_0a": o.mem[0xD70A],
            "parameter_3f_after": hx(o.mem[0xD73F]), "span_pixels_34": o.word(0xD734),
            "y_14_after": o.word(0xD714), "saved_y_3c": o.word(0xD73C),
            "y_added_by_init": o.word(0xD714) - record["world_y"],
        },
    }
    if param & 0x80:
        assert o.word(0xD734) == (param & 0x7F) * 16
    return result


def type26_span_boundaries(rom: bytes, record: dict, deltas) -> list[dict]:
    off = int(record["rom_offset"], 16)
    rows = []
    for dx in deltas:
        o = _create_from_record(rom, off, 0x1E)
        o.call(0x825A)
        x0 = o.word(0xD73A)
        _player(o, x0 + dx, o.word(0xD714) - 20)
        o.call(0x83BF)
        rows.append({"player_x_minus_object_x": dx, "state_after_83BF": o.mem[0xD702]})
    return rows


def type26_span_activation_y(rom: bytes, record: dict, dys) -> list[dict]:
    off = int(record["rom_offset"], 16)
    rows = []
    for dy in dys:
        o = _create_from_record(rom, off, 0x1E)
        o.call(0x825A)
        _player(o, o.word(0xD73A) + 8, o.word(0xD714) + dy)
        o.call(0x83BF)
        rows.append({"player_y_minus_object_y": dy, "state_after_83BF": o.mem[0xD702]})
    return rows


def type26_span_launch(rom: bytes, record: dict, offset_in_span: int = 37) -> dict:
    off = int(record["rom_offset"], 16)
    o = _create_from_record(rom, off, 0x1E)
    o.call(0x825A)
    x0 = o.word(0xD73A)
    _player(o, x0 + offset_in_span, o.word(0xD714) - 20)
    before = {"player_vy": s16(o.word(0xD518)), "player_state_d502": o.mem[0xD502],
              "object_x": o.word(0xD711)}
    o.mem[0xD702] = 9
    o.call(0x8401)
    return {
        "before": before,
        "object_x_after": o.word(0xD711), "object_x_expected_player_x_and_F0": (x0 + offset_in_span) & 0xFFF0,
        "requested_object_state_02": o.mem[0xD702], "counter_1e": hx(o.mem[0xD71E]),
        "sign_extension_d448": hx(o.mem[0xD448]),
        "player_requested_state_d502": o.mem[0xD502], "player_y_velocity_8_8": s16(o.word(0xD518)),
        "player_flags_d503": hx(o.mem[0xD503]),
    }


def type26_fixed_contact(rom: bytes, record: dict) -> dict:
    off = int(record["rom_offset"], 16)
    o = _create_from_record(rom, off, 0x1E)
    o.call(0x825A)
    o.mem[0xD704] = 0
    ox, oy = o.word(0xD711), o.word(0xD714)
    _player(o, ox, oy - 31)  # inside (oy-34, oy-28]
    o.call(0x82AF)
    return {
        "requested_object_state_02": o.mem[0xD702], "counter_1e": hx(o.mem[0xD71E]),
        "player_requested_state_d502": o.mem[0xD502],
        "player_y_velocity_8_8": s16(o.word(0xD518)), "sign_extension_d448": hx(o.mem[0xD448]),
    }


def layout_context(act: str, record: dict) -> dict:
    layout = json.loads((LEVELS / act / "layout.json").read_bytes())
    surf = {int(b["block_id"], 16): b["collision_surface_type"] for b in layout["block_usage"]}
    flags = {int(b["block_id"], 16): int(b["collision_header_flags"], 16) for b in layout["block_usage"]}
    rows = layout["rows"]
    x0, y = record["world_x"], record["world_y"]
    span = (int(record["parameter"], 16) & 0x7F) * 16
    cols = range(x0 // 32, (x0 + span - 1) // 32 + 1)
    row = y // 32
    ceiling = []
    for c in cols:
        r = row - 1
        while r >= 0 and not (flags[rows[r][c]] & 0x80 and surf[rows[r][c]] in (1, 2, 3)):
            r -= 1
        ceiling.append((c * 32, (r + 1) * 32 if r >= 0 else 0))
    spikes = [(c * 32, r * 32) for r in range(len(rows)) for c in range(len(rows[0])) if surf[rows[r][c]] == 5]
    return {
        "object_cell": [x0 // 32, row], "span_end_exclusive_x": x0 + span,
        "nearest_ceiling_top_y_per_column": ceiling,
        "spike_cells_within_192_px_of_span": [s for s in spikes if abs(s[1] - (y - 32)) <= 32 and x0 - 192 <= s[0] <= x0 + span + 192],
    }


def build_type26(rom: bytes) -> dict:
    all_rows = []
    for act in ACTS:
        for r in records(act, 0x26):
            p = int(r["parameter"], 16)
            r["variant"] = ("span (bit7): trigger width (p&0x7F)*16 px" if p & 0x80 else
                            ("fixed strong" if p == 0 else "fixed weak" if p == 1 else "UNDECODED"))
            r["in_thz1_research"] = act == "thz1" or p in (0, 1)
            all_rows.append(r)
    by_key = {(r["act"], r["record_index"]): r for r in all_rows}
    control_span = by_key[("thz1", 22)]
    new88 = by_key[("thz2", 26)]
    control_fixed_strong = by_key[("thz1", 7)]
    control_fixed_weak = by_key[("thz1", 23)]
    return {
        "placements": all_rows,
        "parameter_decode": {
            "evidence": "BYTE-VERIFIED ASSEMBLY $7825A..$782AE + CONTROLLED ROUTINE RESULT",
            "bit7": "span/concealed mode; when clear the low seven bits are not read (fixed springs use only 0/1 via the strength byte)",
            "low7": "trigger width in pixels = low7 * 16 (four SLA/RL steps; stored at object +$34/+$35)",
            "strength": "object +$3F is rewritten to 1 (weak) and then to 0 (strong) only when placement aux1 (object +$09) is zero; both span records have aux1 $72, so spans are weak",
            "fixed_param_00": "strong: launch $F8A0 (-7.375), extension state 1",
            "fixed_param_01": "weak: launch $FB00 (-5.0), extension state 3",
            "packing": "$88 = bit7 + low7 $08 -> 128 px; $8A = bit7 + low7 $0A -> 160 px. No other bit is tested by the initializer, contact or launch code.",
        },
        "init_fixtures": {
            "thz1_00_control": type26_init(rom, control_fixed_strong),
            "thz1_01_control": type26_init(rom, control_fixed_weak),
            "thz1_8A_control": type26_init(rom, control_span),
            "thz2_88": type26_init(rom, new88),
        },
        "span_x_boundaries": {
            "thz1_8A_control": type26_span_boundaries(rom, control_span, (-1, 0, 1, 159, 160)),
            "thz2_88": type26_span_boundaries(rom, new88, (-1, 0, 1, 127, 128, 159, 160)),
        },
        "span_y_window": {
            "thz1_8A_control": type26_span_activation_y(rom, control_span, (-60, -48, -47, -20, 0, 47, 48)),
            "thz2_88": type26_span_activation_y(rom, new88, (-60, -48, -47, -20, 0, 47, 48)),
        },
        "launch_fixtures": {
            "thz1_8A_control": type26_span_launch(rom, control_span),
            "thz2_88": type26_span_launch(rom, new88),
            "thz1_00_fixed_strong_control": type26_fixed_contact(rom, control_fixed_strong),
            "thz1_01_fixed_weak_control": type26_fixed_contact(rom, control_fixed_weak),
        },
        "rise_model": {"strong_F8A0": rise_model(STRONG), "weak_FB00": rise_model(WEAK)},
        "thz2_88_layout_context": layout_context("thz2", new88),
    }


# ----------------------------------------------------------------------------- $10
def mask_for(rom: bytes, parameter: int) -> int:
    """Table at bank $0C:$A1F0 (ROM $321F0); $A1D3 accepts parameters below $0A."""
    assert parameter < 0x09
    return rom[0x321F0 + parameter]


def build_type10(rom: bytes) -> dict:
    t10 = _load_module("thz1_object_10")
    gfx = _load_module("thz1_object_10_graphics")
    rows = []
    for act in ACTS:
        for r in records(act, 0x10):
            p = int(r["parameter"], 16)
            r["queued_mask_d3a3"] = hx(mask_for(rom, p))
            r["in_thz1_research"] = p in (2, 4, 6)
            rows.append(r)
    table = {hx(p): hx(mask_for(rom, p)) for p in range(9)}  # $321F0..$321F8 recovered; index 9 is outside the table

    def dispatch(parameter: int, d299=0x09, d29a=0x00, player_type=1) -> dict:
        o = t10._contact_oracle(rom, parameter=parameter)
        o.mem[0xD500] = player_type
        o.mem[0xD299] = d299
        o.mem[0xD29A] = d29a
        o.word(0xD516, 0x0123)
        o.word(0xD518, 0x0100)
        o.call(0xA16C)
        contact = t10._contact_result(o)
        o.mem[0xD135] = 1
        o.mem[0xDE04] = 0
        o.call(0x4AA3)
        return {
            "parameter": hx(parameter), "d299_before": hx(d299), "d29a_before": hx(d29a),
            "after_contact": {k: contact[k] for k in ("reward_bits_d3a3", "parameter_after", "object_type_after", "score_bytes_after")},
            "after_dispatch": {
                "reward_bits_d3a3": hx(o.mem[0xD3A3]), "counter_d299": hx(o.mem[0xD299]),
                "counter_d29a": hx(o.mem[0xD29A]), "power_code_d532": hx(o.mem[0xD532]),
                "timer_d44c": o.word(0xD44C), "player_flags_d503": hx(o.mem[0xD503]),
                "player_requested_state_d502": hx(o.mem[0xD502]),
                "player_max_x_d373": hx(o.word(0xD373), 4), "sound_request_de04": hx(o.mem[0xDE04]),
                "player_x_velocity_8_8": s16(o.word(0xD516)), "player_y_velocity_8_8": s16(o.word(0xD518)),
            },
        }

    def ring_pickup(d29a: int) -> dict:
        """Terrain-ring handler tail $3138 (JP from the ring handler): the +1 comparison path."""
        o = _oracle(rom, 0x0C)
        o.mem[0xD299] = 0x09
        o.mem[0xD29A] = d29a
        o.call(0x3138)
        return {"d29a_before": hx(d29a), "d29a_after": hx(o.mem[0xD29A]), "d299_after": hx(o.mem[0xD299])}

    def timer_update(code: int, timer: int, steps: int) -> list[dict]:
        o = _oracle(rom, 0x0C)
        o.mem[0xD532] = code
        o.word(0xD44C, timer)
        o.word(0xD373, 0x0400)
        out = []
        for i in range(steps):
            o.call(0x4A74)
            out.append({"update": i + 1, "power_code_d532": o.mem[0xD532],
                        "timer_d44c": o.word(0xD44C), "player_max_x_d373": hx(o.word(0xD373), 4)})
        return out

    gfx.SELECTORS = (0x01, 0x03, 0x02)
    meta = gfx.build_metadata(rom, None)
    variants = {v["selector"]: v for v in meta["variants"] if v["player_type"] == "0x01"}
    alternate = {v["selector"]: v for v in meta["variants"] if v["player_type"] == "alternate"}
    graphics = {}
    for sel, v in variants.items():
        graphics[sel] = {
            "alternate_player_sources": [{k: s[k] for k in ("source_cpu", "source_rom", "tile_bytes_sha256")}
                                         for s in alternate[sel]["streams"]],
            "sources": [{k: s[k] for k in ("pointer_table_cpu", "source_cpu", "source_rom", "byte_count", "vram_destination", "tile_bytes_sha256")}
                        for s in v["streams"]],
            "frames": [{"frame_index": f["frame_index"], "rgba_sha256": f["rgba_sha256"], "used_tile_indices": f["used_tile_indices"]}
                       for f in v["frames"]],
        }
    init_ctl = {hx(p): t10.run_init_fixture(rom, p) for p in (1, 3, 4)}
    init_alt = {hx(p): t10.run_init_fixture(rom, p, player_type=2) for p in (1, 3)}
    state_entry = {hx(p): t10.run_state_entry_fixture(rom, p) for p in (1, 3, 2)}
    return {
        "placements": rows,
        "mask_table_bank_0C_A1F0": table,
        "init_callback_A149": init_ctl,
        "init_callback_A149_alternate_player_type": init_alt,
        "state_entry_A161_graphics_selector": state_entry,
        "reward_dispatch": {
            "param_01_ring_counter_add": dispatch(1, d29a=0x05),
            "param_01_ring_counter_carry": dispatch(1, d29a=0x95),
            "param_03_power_code": dispatch(3),
            "param_02_control": dispatch(2),
            "param_04_control": dispatch(4),
        },
        "ring_counter_identity_proof": {
            "terrain_ring_pickup_plus_one": ring_pickup(0x05),
            "terrain_ring_pickup_carry": ring_pickup(0x99),
            "note": "The terrain-ring handler (asm/recovered/layout_ring_handler.asm, tail JP $3138) increments the same BCD byte $D29A by 1 and, on wrap to $00, runs the same $3104/$178F pair that type $10 parameter $01 runs on carry. Damage scatter ($0492A, C=6 objects) consumes the tens digit of $D29A and clears it.",
        },
        "power_code_3_per_update_4A74": timer_update(3, 3, 5),
        "power_code_4_per_update_4A74_control": timer_update(4, 2, 3),
        "graphics_selectors": graphics,
    }


# ----------------------------------------------------------------------------- $28
def platform_reversal_period(rom: bytes, aux1: int) -> dict:
    """Execute reversal counter $8925 with B=$10 until it returns $FF (as the vertical/horizontal movers do)."""
    o = _oracle(rom, 0x1E)
    o.mem[0xD700] = 0x28
    o.cpu.ix = 0xD700
    o.mem[0xD709] = aux1
    o.mem[0xD730] = 0x10
    o.mem[0xD734] = aux1
    o.mem[0xD737] = aux1
    updates = 0
    while True:
        o.cpu.ix = 0xD700
        o.call(0x8925, bc=0x1000)
        updates += 1
        if o.cpu.a == 0xFF:
            break
        assert updates < 10000
    return {"aux1": aux1, "updates_until_reverse": updates, "formula_16_x_aux1": 16 * aux1}


def type28_init(rom: bytes, record: dict) -> dict:
    o = _create_from_record(rom, int(record["rom_offset"], 16), 0x1E)
    o.call(0x8585)
    return {
        "parameter": record["parameter"], "aux1": record["aux1"],
        "requested_state_02": o.mem[0xD702], "state_copy_36": o.mem[0xD736],
        "counter_34": o.mem[0xD734], "counter_37": o.mem[0xD737], "step_counter_30": hx(o.mem[0xD730]),
        "axis_flag_25": hx(o.mem[0xD725]), "axis_flag_26": hx(o.mem[0xD726]),
    }


def build_type28(rom: bytes) -> dict:
    rows = []
    for act in ACTS:
        for r in records(act, 0x28):
            r["in_thz1_research"] = (r["parameter"], r["aux1"]) in (("0x0A", "0x09"), ("0x0A", "0x0D"), ("0x84", "0x00"))
            rows.append(r)
    seen = sorted({(r["parameter"], r["aux1"]) for r in rows})
    periods = {hx(a): platform_reversal_period(rom, a) for a in (0x09, 0x0D, 0x13, 0x19)}
    inits = {}
    for r in rows:
        if r["act"] in ("thz1", "thz2"):
            inits[f'{r["act"]}:{r["record_index"]}'] = type28_init(rom, r)
    return {
        "placements": rows,
        "parameter_aux1_combinations_seen": [{"parameter": p, "aux1": a} for p, a in seen],
        "init_8585_fixtures": inits,
        "reversal_period_fixtures": periods,
        "aux1_consumers": "only initializer $85C0 (object +$09 -> +$34/+$37); reversal counter $8925 reloads +$37 from +$34",
    }


def _placements(section: dict, act_ids: dict) -> list[dict]:
    out = []
    for r in section["placements"]:
        if (r["act"], r["record_index"]) in act_ids:
            out.append({k: r[k] for k in ("act", "record_index", "rom_offset", "bank", "cpu", "raw_bytes",
                                          "world_x", "world_y", "flags", "parameter", "aux0", "aux1")})
    return out


def build_variants(t26: dict, t10: dict, t28: dict) -> list[dict]:
    return [
        {
            "type": "0x26", "parameter": "0x88", "aux": {"aux0": "0x72", "aux1": "0x72"},
            "placements": _placements(t26, {("thz2", 26)}),
            "routine": "init $7825A (bank $1E, ROM $7825A); span idle state 8 -> $783BF; activation state 9 -> $78401; shared launch $035F -> $5F17 -> $480C",
            "behavior_delta": "Same code path as THZ1 span $8A; only the trigger width differs: (0x88 & 0x7F) * 16 = 128 px (THZ1 $8A: 160 px). Active for object.X <= player.X < object.X + 128 and |object.Y+12 - player.Y| < 48; launch is weak ($FB00 = -5.0, object state 3) because aux1 = $72 is nonzero.",
            "graphics_delta": "none proven; same mapping base $72 as every $26",
            "evidence": ["BYTE-VERIFIED ASSEMBLY", "CONTROLLED ROUTINE RESULT", "DECODED DATA"],
            "poc_requirement": "Decode bit7 + low7*16 as the span width; feed 128 into the existing THZ1 span logic. No new launch, state or animation logic.",
            "unresolved": ["camera activation/removal, occupancy/respawn (inherited from THZ1 $26 study)"],
        },
        {
            "type": "0x10", "parameter": "0x01", "aux": {"aux0": "0x00", "aux1": "0x00"},
            "placements": _placements(t10, {("thz3", 6)}),
            "routine": "mask lookup $A1D3 (table ROM $321F0) -> dispatcher $4AA3 bit 0 -> $4AC0; carry path $3104 + $178F",
            "behavior_delta": "Queues bit 0 ($D3A3 |= $01). Dispatcher: $D29A = BCD($D29A + $10); refreshes the two-digit display; if the sum wrapped below $10 it also runs $3104 (sound $A9, $D299 +1 capped at $99) and $178F. $D29A is proven to be the same byte the terrain-ring handler increments by 1 and the damage scatter consumes.",
            "graphics_delta": "low selector $01 -> tile sources ROM $399A0 (6 tiles @VRAM $0980) and $39EE0 (4 tiles @$0BC0); frame hashes differ from selectors $02/$04/$06 (see graphics_selectors)",
            "evidence": ["BYTE-VERIFIED ASSEMBLY", "CONTROLLED ROUTINE RESULT", "SOURCE-TRACED BEHAVIOR"],
            "poc_requirement": "Add reward branch only: ring counter += 10 with the existing 100-ring carry (extra award, sound $A9); reuse type-$10 contact, bottom-hit, conversion to $0F, score 10 00 00.",
            "unresolved": ["semantic/user-facing name (numeric only)", "meaning of $178F"],
        },
        {
            "type": "0x10", "parameter": "0x03", "aux": {"aux0": "0x00", "aux1": "0x00"},
            "placements": _placements(t10, {("thz2", 13), ("thz2", 14)}),
            "routine": "mask lookup $A1D3 -> dispatcher $4AA3 bit 2 -> $4B0F; per-update timer $4A74 (JP from $3654)",
            "behavior_delta": "Queues bit 2 ($04). Dispatcher: $D532 = 3, timer $D44C = $0384 (900). No sound, no player state request, no velocity change. While $D532 == 3 the per-update routine $4A74 writes $D373 = $0600 (maximum X speed field; walking states otherwise reset it to $0400) and decrements $D44C. At zero the routine does NOT clear code 3 (it only clears codes 4 and 6), so the timer wraps to $FFFF in the isolated routine.",
            "graphics_delta": "low selector $03 -> tile sources ROM $39B20/$39FE0 for the alternate player; player-type $01 sources and frame hashes in graphics_selectors",
            "evidence": ["BYTE-VERIFIED ASSEMBLY", "CONTROLLED ROUTINE RESULT"],
            "poc_requirement": "Add power code 3: set code and 900-update timer on consumption; while active force the horizontal speed cap to $0600. Do not add sound/state effects. Expiry/clear behavior is unresolved (see unresolved).",
            "unresolved": ["whether anything else clears $D532 == 3 (no explicit writer found in a static scan)",
                           "type $04 history-follower objects (state table $986E, init $98EC keeps them only while $D532 == 3): allocator not located",
                           "semantic/user-facing name (numeric only)"],
        },
        {
            "type": "0x28", "parameter": "0x0A", "aux": {"aux0": "0x6A", "aux1": "0x19 / 0x13"},
            "placements": _placements(t28, {("thz2", 1), ("thz2", 2)}),
            "routine": "init $78585 (aux1 -> +$34/+$37 at $785C0); vertical mover state 11 -> $786DA; reversal counter $78925 (B = $10)",
            "behavior_delta": "aux1 sets the reversal period: 16 * aux1 updates ($19 -> 400, $13 -> 304; THZ1 $09 -> 144, $0D -> 208). Confirmed by executing $8925 until it returns $FF. Parameter $0A, state 11, axis flags 0/0 and every other field are identical to THZ1.",
            "graphics_delta": "none (aux0 $6A unchanged)",
            "evidence": ["BYTE-VERIFIED ASSEMBLY", "CONTROLLED ROUTINE RESULT", "DECODED DATA"],
            "poc_requirement": "Feed canonical aux1 into the existing lift logic as period = 16 * aux1 updates; no other change.",
            "unresolved": ["per-update speed and initial direction are inherited from the THZ1 lift study, not re-executed here"],
        },
        {
            "type": "0x28", "parameter": "0x84", "aux": {"aux0": "0x6A", "aux1": "0x00"},
            "placements": _placements(t28, {("thz2", 3)}),
            "routine": "init $78585 -> state 5 (sag/bob) - unchanged",
            "behavior_delta": "none: identical parameter, flags and aux to the four THZ1 records",
            "graphics_delta": "none", "evidence": ["DECODED DATA", "CONTROLLED ROUTINE RESULT"],
            "poc_requirement": "Reuse the THZ1 sag platform unchanged.", "unresolved": [],
        },
    ]


def build_report(rom: bytes) -> dict:
    assert hashlib.sha256(rom).hexdigest() == ROM_SHA256
    t26, t10, t28 = build_type26(rom), build_type10(rom), build_type28(rom)
    return {
        "format": 1, "rom_sha256": ROM_SHA256, "scope": "THZ2/THZ3 parameter deltas of types $26, $10, $28",
        "evidence_classes": ["DECODED DATA", "BYTE-VERIFIED ASSEMBLY", "SOURCE-TRACED BEHAVIOR",
                             "CONTROLLED ROUTINE RESULT", "ORIGINAL-GAME OBSERVATION", "UNRESOLVED"],
        "variants": build_variants(t26, t10, t28),
        "type_26": t26, "type_10": t10, "type_28": t28,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", nargs="?")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    report = build_report(load_rom(args.rom))
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""MGHZ object $24 and object $2E audit. Research only, deterministic.

Scope (bounded): ONLY type $24 and type $2E.  Not covered: $56/$57/$58, shared-player polish, monitor fixes, later zones.
Output: data/rom-cache/mghz/object-24-2e.json (numeric labels; region hashes only, no ROM bytes or pixels).

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY (z80dis of the callbacks and every shared helper they call),
SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT (original Z80 routines on tools/oracle.py, the real placement creator $80EB and the
real animation engine $64FA on the decoded MGHZ layouts), EMULATED ORIGINAL FRAME (whole game in tools/sms_frame_harness.py booted into
MGHZ1/MGHZ2 with real placements), MODEL (an independent translation checked against the above), UNRESOLVED.

Usage:
  python tools/mghz_object_24_2e.py ROM.sms [--check] [--static-only]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import isometric_platform as I          # noqa: E402  (act_data)
import level_package as L               # noqa: E402
import mghz_object_census as C          # noqa: E402  (state_scripts, decode_records, object_lab_init, frame_record)
import mghz_surface_ceiling as M        # noqa: E402  (GameLab: whole-game rig)
import rom as R                         # noqa: E402
import thz1_animation_reach as A        # noqa: E402
from oracle import Oracle               # noqa: E402

OUTPUT = ROOT / "data" / "rom-cache" / "mghz" / "object-24-2e.json"
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
RESEARCH_BASE = "4149f84"
ZONE = 3
ACTS = ("mghz1", "mghz2", "mghz3")
SLOT = 0xD700                              # controlled-lab object slot (slot index 7)
SLOT_BASE = 0xD540                         # first of 19 object slots; 0x40 bytes each
ZONE_NAMES = ("thz", "gpz", "sez", "mghz", "aqz", "eez")

# shared vectors (fixed bank) used by the two objects: vector -> (target, role)
VECTORS = {
    0x032F: (0x6065, "no-op callback (RET)"),
    0x0338: (0x60FB, "integrate +$16/+$18 velocities into the 24-bit X/Y positions"),
    0x033E: (0x5F54, "defeated-enemy conversion: score $27EB, slot becomes type $0F"),
    0x034A: (0x64F0, "mark slot for removal (type := $FE)"),
    0x037A: (0x614E, "terrain flag probe at anchor (0,+18): $00 if header bit 6 or 7 set, $FF otherwise"),
    0x0383: (0x61A5, "strict |objX - playerX| < BC -> $FF else $00"),
    0x0386: (0x61B1, "strict |objY - playerY| < BC -> $FF else $00"),
    0x0431: (0x631A, "+$18/+$19 += DE (gravity)"),
    0x0434: (0x630B, "shared contact wrapper: $6328 overlap, then D3B0 := $FF if any contact bit"),
}

CALLBACK_RANGES = {            # type -> (bank, start, end exclusive)
    0x24: (0x0C, 0xB490, 0xB50D),
    0x2E: (0x1E, 0x8A8A, 0x8B1A),
}


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def s16(v: int) -> int:
    return (v + 32768) % 65536 - 32768


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM")


def file_of(bank: int, cpu: int) -> int:
    return cpu if cpu < 0x8000 else bank * 0x4000 + (cpu - 0x8000)


def disasm(rom: bytes, bank: int, start: int, end: int) -> list:
    from z80dis import z80
    out, pos = [], start
    while pos < end:
        o = file_of(bank, pos)
        d = z80.decode(rom[o:o + 4], pos)
        out.append({"cpu": h(pos), "bytes": rom[o:o + d.len].hex(), "text": z80.disasm(d)})
        pos += d.len
    return out


# --------------------------------------------------------------------------- #
# 1. static facts: type table, state scripts, code regions, helpers, frames
# --------------------------------------------------------------------------- #
def code_facts(rom: bytes) -> dict:
    out = {}
    for t, (bank, a, b) in CALLBACK_RANGES.items():
        out[h(t, 2)] = {"bank": h(bank, 2), "range_cpu": [h(a), h(b)], "range_file": [h(file_of(bank, a), 5), h(file_of(bank, b), 5)],
                        "sha256": sha(rom[file_of(bank, a):file_of(bank, b)]), "instructions": disasm(rom, bank, a, b)}
    helpers = {}
    for vec, (target, role) in VECTORS.items():
        stub = rom[vec:vec + 3]
        assert stub[0] == 0xC3 and stub[1] | stub[2] << 8 == target, vec
        helpers[h(vec)] = {"vector_jp_target": h(target), "role": role, "fixed_bank": True}
    # the contact wrapper's callee and the object terrain sampler
    regions = [("contact_wrapper_630b", 0x630B, 0x631A, "$6328 then D3B0 := $FF if (+$21 & $0F)"),
               ("terrain_flag_probe_614e", 0x614E, 0x6168, "$7725 at (0,0): D364 bit 6|7 -> $00 else $FF"),
               ("object_terrain_sampler_7725", 0x7725, 0x77B0, "block at (X+BC, Y+DE+$12) of the 32x32 map; header flag byte -> D364"),
               ("overlap_6328", 0x6328, 0x640B, "closed-interval overlap; sets +$21 bits, D520/D521 for objects with +3 bit 7 clear"),
               ("enemy_conversion_5f54", 0x5F54, 0x5F84, "score $262F(HL=$27EB), type $0F, clears +1,+2,+4,+7,+14,+15,+$3E,+$3F"),
               ("integrate_60fb", 0x60FB, 0x613C, "24-bit X/Y += sign-extended 8.8 velocity"),
               ("object_cleanup_5ef8", 0x5EF8, 0x5F17, "type $FE: release D400[+$3E - 1] when +$3E != 0, then zero the slot"),
               ("visibility_61e1", 0x61E1, 0x6276, "post-update window test; bit 6 sleep, $FE/$FF removal unless +$04 bit 1")]
    out["shared_regions"] = [{"name": n, "cpu": h(a), "file": h(a, 5), "length": b - a, "sha256": sha(rom[a:b]), "purpose": why} for n, a, b, why in regions]
    out["vectors"] = helpers
    return out


def state_facts(rom: bytes, t: int) -> dict:
    sc = C.state_scripts(rom, t)
    pub = C.public_script(sc)
    return {"type_table_entry_rom": h(sc["type_table_entry_rom"], 5), "bank": h(sc["bank"], 2), "state_table_cpu": pub["state_table_cpu"],
            "state_table_rom": pub["state_table_rom"], "state_count": sc["state_count"], "state_script_cpus": pub["state_script_cpus"],
            "states": pub["states"], "callbacks": pub["callbacks"], "frames_used": pub["frames_used"], "spawns": pub["spawns"],
            "sets_bit4": pub["sets_bit4"], "clears_bit4": pub["clears_bit4"]}


def frame_headers(rom: bytes, t: int) -> list:
    import thz1_object_assets as G
    m = G.object_mapping(rom, t)
    fps = G.mapping_frame_pointers(rom, m["mapping_cpu"])
    out = []
    for i, p in enumerate(fps):
        fr = G.parse_frame_record(rom, p)
        out.append({"frame": i, "frame_cpu": h(p), "frame_rom": h(fr["frame_rom"], 5), "piece_count": fr["piece_count"], "y_origin": fr["y_origin"],
                    "x_origin": fr["x_origin"], "extent_x": fr["raw_word_1"] & 255, "extent_y": fr["raw_word_1"] >> 8, "tile_offsets": fr["tile_offsets"]})
    return out


# --------------------------------------------------------------------------- #
# 2. placements (all 18 mapped lists) and parameter families
# --------------------------------------------------------------------------- #
def scan_all_zones(rom: bytes) -> dict:
    found, totals, alias = [], {}, []
    for z in range(6):
        for a in range(3):
            ptr = L.object_list_pointer(rom, z, a)
            rows, _ = L.decode_object_list(rom, ptr["list_rom"])
            totals[f"{ZONE_NAMES[z]}{a + 1}"] = len(rows)
            for r in rows:
                if r["type_id"] in ("0x24", "0x2E"):
                    found.append(dict(r, act=f"{ZONE_NAMES[z]}{a + 1}"))
                if r["type_id"] == "0x2D":
                    alias.append(f"{ZONE_NAMES[z]}{a + 1}:{r['index']}")
    return {"lists_scanned": len(totals), "records_per_list": totals, "placements": found, "all_lists_type_2D": alias}


def creator_rule() -> dict:
    return {"routine": "$1C:$80EB (file 0x700EB)", "evidence": "BYTE-VERIFIED ASSEMBLY (asm/recovered/object_placement_create.asm) + CONTROLLED ROUTINE RESULT",
            "record_layout": "type, Xlo, Xhi, Ylo, Yhi, flags, parameter, aux0, aux1 (9 bytes); stored X/Y carry a +256 bias (high byte decremented)",
            "fields": {"+$00": "type", "+$11/+$12": "X = stored X - 256", "+$14/+$15": "Y = stored Y - 256", "+$3A/+$3B": "origin X (copy)", "+$3C/+$3D": "origin Y (copy)",
                       "+$04": "placement flags | $40 (created asleep)", "+$3F": "parameter", "+$08/+$09": "aux0 / aux1", "+$3E": "occupancy token = list index + 1 (1-based), D400[index] := type"}}


def placement_rows(rom: bytes, scan: dict) -> list:
    rows = []
    for p in scan["placements"]:
        t = int(p["type_id"], 16)
        row = {"act": p["act"], "index_1based": p["index"], "zero_based_index": p["zero_based_index"], "rom_offset": p["rom_offset"], "bank_cpu": f"{p['bank']}:{p['cpu']}",
               "raw_bytes": p["raw_bytes"], "type": p["type_id"], "world_x": p["world_x"], "world_y": p["world_y"], "stored_x": p["stored_x"], "stored_y": p["stored_y"],
               "flags": p["flags"], "parameter": p["parameter"], "aux0": p["aux0"], "aux1": p["aux1"], "occupancy_token": p["zero_based_index"] + 1,
               "creation_flags_04": h((int(p["flags"], 16) | 0x40), 2)}
        if t == 0x24:
            prm = int(p["parameter"], 16)
            row["family"] = "right-falling (parameter 0)" if prm == 0 else "left-falling (parameter != 0)"
            row["fall_vx_8_8"] = 0x80 if prm == 0 else -0x80
            row["trigger_x_window"] = [p["world_x"] - 47, p["world_x"] + 47]
        else:
            n = int(p["aux1"], 16)
            row["family"] = "strip trigger (parameter 0)"
            row["strip_x_exclusive_left"] = p["world_x"]
            row["strip_x_inclusive_right"] = p["world_x"] + n * 16
            row["strip_length_px"] = n * 16
            row["trigger_player_y_range"] = [p["world_y"] - 2, p["world_y"] + 2]
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# 3. controlled object lab (original creator, animation engine and callbacks on the decoded act layout)
# --------------------------------------------------------------------------- #
class Lab:
    """One real placement record -> creator $80EB -> two engine+callback passes; cases restore the same RAM image."""

    def __init__(self, rom: bytes, act_key: str, raw: str, player=(0, 0), flags4=0, d12f: int = 0):
        self.rom = rom
        act = C.vram_for_act(rom, int(act_key[-1]) - 1)
        rec = {"type_id": "0x%02X" % int(raw.split()[0], 16), "raw_bytes": raw}
        o, m, _step, (ox, oy) = C.object_lab_init(rom, act, rec)
        self.o, self.m, self.ox, self.oy = o, m, ox, oy
        m[0xD800:0xD900] = bytes(256)          # the Oracle's unused RAM row table overlaps object slots 11..14; the lab points $D168 at the ROM table
        self.type = m[SLOT]
        self.bank = A.animation_bank(self.type)
        m[0xD503] = 0
        self.player(*player)
        self.update()
        self.update()
        if flags4 is not None:
            m[SLOT + 4] = flags4
        m[0xD12F] = d12f
        self.snap = bytes(m[0xC000:0xE000])

    # -- state
    def reset(self) -> None:
        self.m[0xC000:0xE000] = self.snap

    def player(self, px, py, vx=0, vy=0, f3=0, d532=0, face=0, ex=8, ey=24):
        o, m = self.o, self.m
        o.word(0xD511, px)
        o.word(0xD514, py)
        o.word(0xD516, vx & 0xFFFF)
        o.word(0xD518, vy & 0xFFFF)
        m[0xD503] = f3
        m[0xD532] = d532
        m[0xD504] = (m[0xD504] & ~0x10) | (0x10 if face else 0)
        m[0xD52C], m[0xD52D] = ex, ey
        m[0xD520] = m[0xD521] = 0
        m[0xD3B0] = 0

    def update(self) -> int:
        """One scheduler pass for this slot: animation engine $64FA then the state callback (D44F bracket as in $5DD1)."""
        o, m = self.o, self.m
        o.bank(2, self.bank)
        m[0xD12B] = self.bank
        o.cpu.ix = SLOT
        m[0xD44F] = 0xFF
        o.call(0x64FA)
        m[0xD44F] = 0
        cb = m[SLOT + 0xC] | m[SLOT + 0xD] << 8
        if cb:
            o.bank(2, self.bank)
            m[0xD12B] = self.bank
            o.cpu.ix = SLOT
            m[0xD44F] = 0xFF
            o.call(cb)
            m[0xD44F] = 0
        m[0xD12F] = (m[0xD12F] + 1) & 255
        return cb

    def w(self, off: int) -> int:
        return self.o.word(SLOT + off)

    def row(self) -> dict:
        m = self.m
        return {"type": m[SLOT], "state": m[SLOT + 1], "req": m[SLOT + 2], "frame": m[SLOT + 6], "dur": m[SLOT + 7], "f4": m[SLOT + 4],
                "x": self.w(0x11), "xf": m[SLOT + 0x10], "y": self.w(0x14), "yf": m[SLOT + 0x13], "vx": s16(self.w(0x16)), "vy": s16(self.w(0x18)),
                "cb": self.w(0xC), "ex": m[SLOT + 0x2C], "ey": m[SLOT + 0x2D], "p3f": m[SLOT + 0x3F], "t3e": m[SLOT + 0x3E]}


def creator_init(rom: bytes, rows: list) -> list:
    out = []
    for r in rows:
        if not r["act"].startswith("mghz"):
            continue
        lab = Lab(rom, r["act"], r["raw_bytes"], player=(60000, 0))
        m = lab.m
        # fields straight after the creator and before the two engine passes would be hidden by Lab(); re-run the creator only
        act = C.vram_for_act(rom, int(r["act"][-1]) - 1)
        o2, m2, _s, _p = C.object_lab_init(rom, act, {"type_id": r["type"], "raw_bytes": r["raw_bytes"]})
        # object_lab_init has already executed the creator; nothing has run the engine yet
        fresh = {"type": m2[SLOT], "state": m2[SLOT + 1], "req": m2[SLOT + 2], "flags_04": h(m2[SLOT + 4], 2), "base0": h(m2[SLOT + 8], 2), "aux1_or_base1": h(m2[SLOT + 9], 2),
                 "x": o2.word(SLOT + 0x11), "y": o2.word(SLOT + 0x14), "origin_x": o2.word(SLOT + 0x3A), "origin_y": o2.word(SLOT + 0x3C),
                 "param_3f": m2[SLOT + 0x3F], "token_3e": m2[SLOT + 0x3E]}
        out.append({"act": r["act"], "index_1based": r["index_1based"], "after_creator": fresh, "after_two_updates": lab.row(),
                    "callback_after_two_updates": h(lab.w(0xC))})
    return out


# --------------------------------------------------------------------------- #
# 4. object $24: controlled traces, trigger, landing, contact
# --------------------------------------------------------------------------- #
def mghz_rows(rows: list, t: int) -> list:
    return [r for r in rows if r["act"].startswith("mghz") and int(r["type"], 16) == t]


def pos24(x: int, xf: int) -> int:
    return x * 256 + xf


def fixed_step(pos: int, v: int) -> int:
    """$60FB: 24-bit position (16-bit integer + fraction byte) += sign-extended 8.8 velocity, modulo 2^24."""
    return (pos + v) & 0xFFFFFF


def trigger_sweep(rom: bytes, rec: dict) -> dict:
    """State-1 callback $B49A: wake gate, |dx| < $30 (strict), |player vx| < $100 (strict), no vertical test."""
    lab = Lab(rom, rec["act"], rec["raw_bytes"], player=(60000, 0), flags4=0)
    ox = lab.ox
    oy = lab.oy
    cases = 0

    def fires(px, py, vx, flags4=0):
        lab.reset()
        lab.m[SLOT + 4] = flags4
        lab.player(px, py, vx=vx)
        lab.update()
        return lab.m[SLOT + 2] == 2

    dx_hits = [dx for dx in range(-70, 71) if fires(ox + dx, oy + 30, 0)]
    cases += 141
    vx_grid = list(range(-0x180, 0x181)) + [-0x8000, -0x4000, 0x4000, 0x7FFF]
    vx_hits = [v for v in vx_grid if fires(ox, oy + 30, v)]
    cases += len(vx_grid)
    dy_hits = [dy for dy in range(-120, 241, 1) if fires(ox, oy + dy, 0)]
    cases += 361
    asleep = [dx for dx in range(-70, 71) if fires(ox + dx, oy + 30, 0, flags4=0x40)]
    cases += 141
    corners = {f"dx={dx},vx={v}": fires(ox + dx, oy + 30, v) for dx in (-48, -47, 47, 48) for v in (-0x100, -0xFF, 0xFF, 0x100)}
    cases += 16
    return {"object": [ox, oy], "cases": cases, "dx_that_fire_vx0": [min(dx_hits), max(dx_hits)], "dx_count": len(dx_hits),
            "vx_that_fire_dx0": [min(vx_hits), max(vx_hits)], "vx_count": len(vx_hits),
            "vx_extremes_fire": {str(v): (v in vx_hits) for v in (-0x8000, -0x4000, 0x4000, 0x7FFF)},
            "dy_dependence": "none" if len(dy_hits) == 361 else {"fires_for_dy": [min(dy_hits), max(dy_hits)], "count": len(dy_hits)},
            "asleep_flag_0x40_fires": bool(asleep), "corner_cases": corners,
            "rule": "fires iff +$04 bit 6 clear AND |objX - playerX| < 48 AND |playerVX| < $0100 (8.8 signed, 16-bit abs); player Y and state are not read"}


def fall_trace(rom: bytes, rec: dict, max_updates: int = 400) -> dict:
    """Trigger on the first awake update from a stationary player beside the object, then follow to conversion."""
    lab = Lab(rom, rec["act"], rec["raw_bytes"], player=(60000, 0), flags4=0)
    px, py = lab.ox, lab.oy + 60
    lab.player(px, py)
    rows = []
    t_trigger = None
    for u in range(max_updates):
        lab.update()
        r = lab.row()
        r["u"] = u
        rows.append(r)
        if t_trigger is None and r["req"] == 2:
            t_trigger = u
        if r["type"] != int(rec["type"], 16):
            break
    conv = rows[-1]
    fall_rows = [r for r in rows if r["state"] == 3]
    return {"trigger_update": t_trigger, "updates_total": len(rows), "rows": rows, "converted": conv["type"] != int(rec["type"], 16),
            "first_fall_update": fall_rows[0]["u"] if fall_rows else None}


def compact_row(r: dict) -> list:
    return [r["u"], r["state"], r["req"], r["frame"], r["x"], r["xf"], r["y"], r["yf"], r["vx"], r["vy"]]


def shake_and_fall_template(rom: bytes, rec: dict, extra_fall_rows: int = 6) -> dict:
    tr = fall_trace(rom, rec)
    t0 = tr["trigger_update"]
    rows = tr["rows"]
    ff = tr["first_fall_update"]
    part = [compact_row(r) for r in rows[t0:ff + extra_fall_rows]]
    return {"columns": ["update", "state", "requested", "frame", "x", "x_frac", "y", "y_frac", "vx_8_8", "vy_8_8"],
            "trigger_update": t0, "first_state3_update": ff, "rows_from_trigger": part,
            "shake_updates": ff - t0 - 1, "sha256_all_rows": sha(json.dumps([compact_row(r) for r in rows]).encode())}


_FLAG_CACHE: dict = {}


def model_fall(rom: bytes, act_key: str, x0: int, y0: int, param: int) -> dict:
    """Independent translation of states 2-3 + $B4F0 against the decoded map. Returns the conversion update relative to the fall start."""
    a = I.act_data(rom, act_key)
    cells = a["cells"][:4095]
    key = bytes(cells)
    if key not in _FLAG_CACHE:
        _FLAG_CACHE[key] = {b: R.header(rom, b)["flags"] for b in set(cells)}
    flags = _FLAG_CACHE[key]

    def solid(x, y):
        yy = max(y + 18, 0)
        cx, cy = x // 32, yy // 32
        i = cy * a["width"] + cx
        if not (0 <= x < 65536) or not 0 <= i < 4095 or cx >= a["width"]:
            return None
        return bool(flags[cells[i]] & 0xC0)

    px, py = pos24(x0, 0), pos24(y0, 0)
    vx = 0x80 if param == 0 else -0x80
    vy = 0
    for n in range(1, 400):
        px = fixed_step(px, vx)
        py = fixed_step(py, vy)
        vy += 0x10
        x, y = px >> 8, py >> 8
        sol = solid(x, y)
        if sol:
            blk = cells[((y + 18) // 32) * a["width"] + x // 32]
            return {"fall_updates": n, "x": x, "y": y, "x_frac": px & 255, "y_frac": py & 255, "vy_8_8": vy, "cell": [x // 32, (y + 18) // 32],
                    "block": blk, "block_header_flags": h(flags[blk], 2)}
        if sol is None:
            return {"fall_updates": n, "outside_map": True, "x": x, "y": y}
    return {"fall_updates": None}


def landing_table(rom: bytes, rows24: list) -> list:
    out = []
    for r in rows24:
        tr = fall_trace(rom, r)
        t0, ff = tr["trigger_update"], tr["first_fall_update"]
        last = tr["rows"][-1]
        prm = int(r["parameter"], 16)
        mod = model_fall(rom, r["act"], r["world_x"], r["world_y"], prm)
        prev = tr["rows"][-2]
        out.append({"act": r["act"], "index_1based": r["index_1based"], "x": r["world_x"], "y": r["world_y"], "parameter": prm,
                    "trigger_update": t0, "first_fall_update": ff, "converted": tr["converted"], "fall_updates_to_conversion": tr["updates_total"] - ff if tr["converted"] else None,
                    "last_pre_conversion_row": compact_row(prev), "slot_after_conversion": {"type": last["type"], "x": last["x"], "y": last["y"], "state": last["state"]},
                    "model": mod, "model_matches_lab": bool(tr["converted"] and mod.get("fall_updates") == tr["updates_total"] - ff
                                                             and (mod["x"], mod["y"]) == (last["x"], last["y"]))})
    return out


def rects_of(cells) -> list:
    return M.rects(cells)


def overlap_model(dx: int, dy: int, ex: int, ey: int, pex: int = 8, pey: int = 24) -> bool:
    """Closed-interval box overlap used by $6328; dx = playerX - objX, dy = playerY - objY (anchors are bottom-centre)."""
    return abs(dx) <= ex + pex and -ey <= dy <= pey


def contact_call(lab: Lab, dx: int, dy: int, f3: int = 0, d532: int = 0, pex: int = 8) -> tuple:
    """Run the real shared wrapper $0434 ($630B) with the object's current extents."""
    lab.reset()
    lab.player(lab.ox + dx, lab.oy + dy, f3=f3, d532=d532, ex=pex)
    lab.o.cpu.ix = SLOT
    lab.o.call(0x0434)
    m = lab.m
    return (m[0xD3B0], m[SLOT + 0x21] & 0x0F, m[SLOT + 0x20], m[0xD520], m[0xD521] >> 4)


def contact_sweep(rom: bytes, rec: dict) -> dict:
    lab = Lab(rom, rec["act"], rec["raw_bytes"], player=(60000, 0), flags4=0)
    ex, ey = lab.m[SLOT + 0x2C], lab.m[SLOT + 0x2D]
    variants = {"ordinary_8x24": dict(f3=0, pex=8), "state_0F_9x24": dict(f3=0, pex=9), "attack_bit1": dict(f3=0x02, pex=8),
                "player_bit6": dict(f3=0x40, pex=8), "player_bit7_blink": dict(f3=0x80, pex=8), "invincible_d532_6": dict(f3=0, d532=6, pex=8)}
    out = {"object_extents": [ex, ey], "grid": {"dx": [-24, 24], "dy": [-48, 36]}, "variants": {}, "cases": 0}
    mismatches = 0
    for name, kw in variants.items():
        hit, classes = set(), {}
        for dx in range(-24, 25):
            for dy in range(-48, 37):
                res = contact_call(lab, dx, dy, **kw)
                out["cases"] += 1
                if res[0]:
                    hit.add((dx, dy))
                classes.setdefault(res, set()).add((dx, dy))
        model = {(dx, dy) for dx in range(-24, 25) for dy in range(-48, 37) if overlap_model(dx, dy, ex, ey, kw["pex"])}
        expect_hit = model if name not in ("player_bit6",) else set()
        mismatches += len(hit ^ expect_hit)
        out["variants"][name] = {"d3b0_set_rects_dx0_dx1_dy0_dy1": rects_of(hit), "hit_cells": len(hit), "model_cells": len(expect_hit), "mismatch_with_model": len(hit ^ expect_hit),
                                 "classes": [{"d3b0": k[0], "contact_bits_21_low": k[1], "flag_20": k[2], "d520": k[3], "d521_high": k[4], "cells": len(v),
                                              "rects": rects_of(v) if len(v) < 400 else "large"} for k, v in sorted(classes.items())]}
    out["mismatch_total"] = mismatches
    return out


# --------------------------------------------------------------------------- #
# 5. scheduler-faithful lab pass (all 19 slots in order, as $5DD1)
# --------------------------------------------------------------------------- #
def lab_slots(lab: Lab) -> list:
    m, o = lab.m, lab.o
    out = []
    for i in range(19):
        b = SLOT_BASE + i * 0x40
        if m[b]:
            out.append({"slot": i, "type": m[b], "state": m[b + 1], "req": m[b + 2], "frame": m[b + 6], "f4": m[b + 4], "x": o.word(b + 0x11), "y": o.word(b + 0x14),
                        "vx": s16(o.word(b + 0x16)), "vy": s16(o.word(b + 0x18)), "p3f": m[b + 0x3F], "t3e": m[b + 0x3E]})
    return out


def lab_frame(lab: Lab, with_lifecycle: bool = False) -> None:
    """One object scheduler pass over the 19 slots ($5DD1): types >= $F0 go to the $5E70 dispatch table, others run $64FA + callback."""
    o, m = lab.o, lab.m
    for i in range(19):
        b = SLOT_BASE + i * 0x40
        t = m[b]
        if t == 0:
            continue
        o.cpu.ix = b
        if t >= 0xF0:
            tbl = 0x5E70 + 2 * (t & 15)
            target = lab.rom[tbl] | lab.rom[tbl + 1] << 8
            o.call(target)
            continue
        bank = A.animation_bank(t)
        o.bank(2, bank)
        m[0xD12B] = bank
        o.cpu.ix = b
        m[0xD44F] = 0xFF
        o.call(0x64FA)
        m[0xD44F] = 0
        cb = m[b + 0xC] | m[b + 0xD] << 8
        if cb:
            o.bank(2, bank)
            m[0xD12B] = bank
            o.cpu.ix = b
            m[0xD44F] = 0xFF
            o.call(cb)
            m[0xD44F] = 0
        if with_lifecycle and m[b + 1]:
            o.cpu.ix = b
            o.call(0x61E1)
    m[0xD12F] = (m[0xD12F] + 1) & 255


def strip_trigger_sweep(rom: bytes, rec: dict) -> dict:
    lab = Lab(rom, rec["act"], rec["raw_bytes"], player=(60000, 0), flags4=None)
    m = lab.m
    ox, oy = lab.ox, lab.oy
    n = int(rec["aux1"], 16)
    after_init = {"flags_04": h(m[SLOT + 4], 2), "state": m[SLOT + 1], "req": m[SLOT + 2], "range_end_34_35": lab.w(0x34), "origin_3a_3b": lab.w(0x3A),
                  "aux1": m[SLOT + 9], "callback": h(lab.w(0xC))}
    cases = 0

    def fires(px, py, **kw):
        lab.reset()
        lab.player(px, py, **kw)
        lab.update()
        return m[SLOT + 2] == 2, lab.w(0x11)

    x_hits = []
    for px in range(ox - 12, ox + n * 16 + 13):
        f, nx = fires(px, oy)
        cases += 1
        if f:
            x_hits.append(px)
            assert nx == px
    y_hits = [dy for dy in range(-8, 9) if fires(ox + 40, oy + dy)[0]]
    cases += 17
    variants = {}
    for name, kw in {"vx_fast": dict(vx=0x600), "airborne_f3_1": dict(f3=1), "attack_f3_2": dict(f3=2), "blink_f3_80": dict(f3=0x80), "bit6_f3_40": dict(f3=0x40),
                     "d532_6": dict(d532=6), "face_left": dict(face=1)}.items():
        f, _ = fires(ox + 40, oy, **kw)
        variants[name] = f
        cases += 1
    return {"after_init_callback": after_init, "cases": cases, "x_that_fire": [min(x_hits), max(x_hits)], "x_count": len(x_hits), "expected_x_exclusive_left": ox,
            "expected_x_inclusive_right": ox + n * 16, "y_that_fire_dy": [min(y_hits), max(y_hits)], "y_count": len(y_hits), "player_variants_fire_at_mid_strip": variants,
            "rule": "state-1 callback $8AE5: |objY - playerY| < 3 (strict, so dy -2..+2) AND originX < playerX <= originX + aux1*16 (both compared as unsigned 16-bit); "
                    "firing sets requested state 2 and copies playerX into the parent's X; no other player field is read"}




def splash_once(rom: bytes, rec: dict, face: int, tail: int = 40) -> dict:
    """Park the player in the strip at the trigger Y; after the first spawn lift the player out of the Y band and follow every child to removal."""
    lab = Lab(rom, rec["act"], rec["raw_bytes"], player=(60000, 0), flags4=None)
    m, o = lab.m, lab.o
    px, py = lab.ox + 40, lab.oy
    lab.player(px, py, face=face)
    parent_rows, kid_rows, first, left = [], {}, None, False
    for u in range(80):
        lab_frame(lab)
        sl = lab_slots(lab)
        par = next(s for s in sl if s["slot"] == 7)
        kids = [s for s in sl if s["slot"] != 7 and s["type"] in (0x2E, 0xFE, 0xFF)]
        if not left and par["req"] == 2:
            left = True
            lab.player(px, py + 60, face=face)      # leave the Y band once the splash is committed: exactly one generation of children
        if first is None and kids:
            first = u
        parent_rows.append([u, par["state"], par["req"], par["frame"], par["x"], par["y"]])
        for k in kids:
            kid_rows.setdefault(k["slot"], []).append([u - (first if first is not None else u), k["type"], k["state"], k["req"], k["frame"], k["x"], k["y"], k["vx"], k["vy"], k["p3f"]])
        if first is not None and u > first + tail:
            break
    return {"player": [px, py], "face_bit4": face, "spawn_pass": first, "parent_rows_columns": ["pass", "state", "req", "frame", "x", "y"],
            "parent_rows": parent_rows[:first + 12], "kid_columns": ["rel_pass", "type", "state", "req", "frame", "x", "y", "vx_8_8", "vy_8_8", "param"],
            "kids_by_slot": {str(k): v for k, v in sorted(kid_rows.items())}, "parent_flags_04": h(m[SLOT + 4], 2)}


def child_model(px: int, py: int, face: int, param: int, parent_y: int, steps: int = 14) -> list:
    dx, dy = {1: (4, 0), 2: (0, -2), 3: (-4, -4)}[param]
    x, y = pos24(px + dx, 0), pos24(parent_y + dy, 0)
    vx = (0xA0 + 16 * param) if face else (0xFF60 - 16 * param) - 0x10000
    vy = -256
    rows = [[0, x >> 8, y >> 8, vx, vy]]
    for k in range(1, steps):
        x = fixed_step(x, vx)
        y = fixed_step(y, vy)
        vy += 0x10
        rows.append([k, x >> 8, y >> 8, vx, vy])
    return rows


def splash_summary(rom: bytes, rec: dict) -> dict:
    out = {"cases": {}}
    for face in (0, 1):
        sp = splash_once(rom, rec, face)
        first_k = sp["kids_by_slot"]
        kids = {}
        for slot, rows_ in first_k.items():
            prm = rows_[0][9]
            kids[prm] = {"slot": int(slot), "rows": rows_}
        life = {}
        match = {}
        for prm, kd in kids.items():
            rows_ = kd["rows"]
            alive = [r for r in rows_ if r[1] == 0x2E]
            life[str(prm)] = {"slot": kd["slot"], "passes_as_type_2E": len(alive), "first_rel": rows_[0][0], "marked_FE_rel": next((r[0] for r in rows_ if r[1] == 0xFE), None),
                              "marked_FF_rel": next((r[0] for r in rows_ if r[1] == 0xFF), None), "slot_zeroed_rel": rows_[-1][0] + 1 if rows_[-1][1] == 0xFF else None}
            mod = child_model(sp["player"][0], sp["player"][1], face, prm, sp["player"][1])
            match[str(prm)] = all((r[5], r[6], r[7], r[8]) == (m_[1], m_[2], m_[3], m_[4]) for r, m_ in zip([r for r in rows_ if r[1] == 0x2E], mod))
        out["cases"][f"face_bit4={face}"] = {"spawn_pass": sp["spawn_pass"], "player": sp["player"], "parent_rows_columns": sp["parent_rows_columns"], "parent_rows": sp["parent_rows"][-14:],
                                             "child_lifetimes": life, "child_rows_first_16": {str(p): kd["rows"][:16] for p, kd in sorted(kids.items())},
                                             "child_rows_last_3": {str(p): kd["rows"][-3:] for p, kd in sorted(kids.items())}, "model_matches_lab": match,
                                             "sha256_all_child_rows": sha(json.dumps(sp["kids_by_slot"], sort_keys=True).encode())}
    return out


def retrigger_cadence(rom: bytes, rec: dict, passes: int = 60) -> dict:
    lab = Lab(rom, rec["act"], rec["raw_bytes"], player=(60000, 0), flags4=None)
    px, py = lab.ox + 40, lab.oy
    lab.player(px, py)
    spawn_passes, prev = [], 0
    for u in range(passes):
        lab_frame(lab)
        n2 = len([s for s in lab_slots(lab) if s["type"] == 0x2E and s["slot"] != 7 and s["state"] == 0 and s["frame"] == 0 and s["req"] == 3])
        if n2:
            spawn_passes.append(u)
    return {"player": [px, py], "passes": passes, "spawn_passes": spawn_passes,
            "periods": sorted({b - a for a, b in zip(spawn_passes, spawn_passes[1:])}),
            "note": "player stationary inside the strip at the trigger Y; the pool of 11 slots is not full"}


def pool_exhaustion(rom: bytes, rec: dict) -> dict:
    """Free-slot allocator $5EE1 scans slots 7..17 only. Fill k of the 8 other slots with inert asleep type-$24 objects and count children."""
    out = {}
    for free in (0, 1, 2, 3, 10):
        lab = Lab(rom, rec["act"], rec["raw_bytes"], player=(60000, 0), flags4=None)
        m = lab.m
        others = [i for i in range(8, 18)]
        for i in others[free:]:
            b = SLOT_BASE + i * 0x40
            m[b] = 0x24
            m[b + 4] = 0x40
            m[b + 0x3F] = 0
        lab.player(lab.ox + 40, lab.oy)
        seen = set()
        for u in range(12):
            lab_frame(lab)
            for s in lab_slots(lab):
                if s["type"] in (0x2E, 0xFE) and s["slot"] != 7 and s["p3f"]:
                    seen.add(s["p3f"])
        out[str(free)] = {"free_slots_besides_parent": min(free, 10), "children_parameters_created": sorted(seen)}
    return out


# --------------------------------------------------------------------------- #
# 6. whole-game rig (approximate SMS harness booted into MGHZ1 / MGHZ2 with the real placement scan)
# --------------------------------------------------------------------------- #
PAD_RIGHT, PAD_LEFT, PAD_B1 = 8, 4, 16
CONTACT_HOOKS = {0x6328: "overlap_6328", 0x630B: "wrapper_630b", 0x5FA0: "solid_5fa0", 0x5F3D: "attack_gate_5f3d", 0x5F54: "conversion_5f54", 0x48F7: "hurt_48f7"}


class Game:
    """GameLab (real boot into MGHZ n, 90 settle frames) plus PC hooks on the shared contact/conversion helpers."""

    def __init__(self, rom: bytes, key: str):
        self.rom, self.key = rom, key
        self.lab = M.GameLab(rom, key)
        self.s, self.m = self.lab.s, self.lab.m
        self.hits: list = []
        for addr, name in CONTACT_HOOKS.items():
            self.s.add_pc_hook(addr, lambda mm, n=name: self.hits.append((n, mm.cpu.ix, mm.mem[mm.cpu.ix] if mm.cpu.ix >= SLOT_BASE else None)))
        self.contacts: list = []
        self.passes: dict = {}
        self.s.add_pc_hook(0x630B, self._wrapper_entry)
        self.s.add_pc_hook(0x64FA, self._engine_entry)
        self.cells = I.act_data(rom, key)["cells"]
        self.width = I.act_data(rom, key)["width"]
        self.base = self.lab.e.snapshot()

    def _engine_entry(self, mm) -> None:
        ix = mm.cpu.ix
        if SLOT_BASE <= ix < SLOT_BASE + 19 * 0x40:
            slot = (ix - SLOT_BASE) // 0x40
            self.passes[slot] = self.passes.get(slot, 0) + 1

    def _wrapper_entry(self, mm) -> None:
        ix = mm.cpu.ix
        m = mm.mem
        self.contacts.append({"slot": (ix - SLOT_BASE) // 0x40, "type": m[ix], "px": mm.u16(0xD511), "py": mm.u16(0xD514), "ox": mm.u16(ix + 0x11), "oy": mm.u16(ix + 0x14),
                              "ex": m[ix + 0x2C], "ey": m[ix + 0x2D], "pex": m[0xD52C], "pey": m[0xD52D], "f3": m[0xD503]})

    # -- state
    def restore(self) -> None:
        self.lab.e.restore(self.base)
        self.lab.pending = []
        self.lab.pending_info = []
        self.hits.clear()
        self.contacts.clear()

    def snapshot(self):
        return self.lab.e.snapshot()

    def rewind(self, snap) -> None:
        self.lab.e.restore(snap)
        self.lab.pending = []
        self.lab.pending_info = []
        self.hits.clear()
        self.contacts.clear()

    def place(self, x, y, **kw) -> None:
        kw.setdefault("cur", 1)
        kw.setdefault("f3", 0)
        kw.setdefault("floor", True)
        kw.setdefault("prev", 0x82)
        self.restore()
        self.lab.place(x, y, 0, 0, **kw)
        self.hits.clear()

    # -- observation
    def player(self) -> dict:
        s, m = self.s, self.m
        return {"x": s.u16(0xD511), "y": s.u16(0xD514), "vx": s16(s.u16(0xD516)), "vy": s16(s.u16(0xD518)), "cur": m[0xD501], "req": m[0xD502], "f3": m[0xD503],
                "rings": m[0xD29A], "d3b0": m[0xD3B0], "d3b1": m[0xD3B1], "d520": m[0xD520], "d532": m[0xD532], "face": (m[0xD504] >> 4) & 1}

    def objs(self, types=None) -> list:
        s, m = self.s, self.m
        out = []
        for i in range(19):
            b = SLOT_BASE + i * 0x40
            t = m[b]
            if t and (types is None or t in types):
                out.append({"slot": i, "type": t, "state": m[b + 1], "req": m[b + 2], "frame": m[b + 6], "dur": m[b + 7], "f4": m[b + 4], "x": s.u16(b + 0x11), "xf": m[b + 0x10],
                            "y": s.u16(b + 0x14), "yf": m[b + 0x13], "vx": s16(s.u16(b + 0x16)), "vy": s16(s.u16(b + 0x18)), "p3f": m[b + 0x3F], "t3e": m[b + 0x3E],
                            "ex": m[b + 0x2C], "ey": m[b + 0x2D]})
        return out

    def by_token(self, token: int, types=None):
        for o in self.objs(types):
            if o["t3e"] == token:
                return o
        return None

    def frame(self, pad: int = 0) -> None:
        self.s.pad = pad
        self.s.run_frame()

    def score(self) -> int:
        m = self.m
        return int(f"{m[0xD29F]:02X}{m[0xD29E]:02X}{m[0xD29D]:02X}")

    def occupancy(self, index_1based: int) -> int:
        return self.m[0xD400 + index_1based - 1]


def stand_y(cells, width: int, rom: bytes, px: int, from_y: int) -> int | None:
    """Anchor Y of a player standing on the first solid/one-way block cell at column px below from_y (floor top = cell top; foot probe is Y + 18)."""
    flags = {}
    cx = px // 32
    for cy in range(from_y // 32, len(cells) // width):
        b = cells[cy * width + cx]
        if b not in flags:
            flags[b] = R.header(rom, b)["flags"]
        if flags[b] & 0xC0:
            return cy * 32 - 18
    return None


def track_object(g: Game, token: int, frames: int, pad: int = 0, hook=None, stop_on_clear: bool = True) -> dict:
    """Run frames; log the row of the slot that carries placement token `token` (kept through the $0F conversion until the slot is cleared)."""
    rows, events, slot = [], {}, None
    for f in range(frames):
        g.frame(pad)
        if hook:
            hook(g, f)
        if slot is None:
            o = g.by_token(token, (0x24, 0x2E))
            if o is None:
                continue
            slot = o["slot"]
            events["first_seen"] = f
            base_pass = g.passes.get(slot, 0)
        o = next((x for x in g.objs() if x["slot"] == slot), None)
        if o is None:
            events.setdefault("slot_cleared", f)
            rows.append([f, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, g.passes.get(slot, 0) - base_pass])
            if stop_on_clear:
                break
            continue
        rows.append([f, o["type"], o["state"], o["req"], o["frame"], o["x"], o["y"], o["f4"], o["t3e"], o["vx"], o["vy"], g.passes.get(slot, 0) - base_pass])
        if o["type"] == 0x24:
            if not o["f4"] & 0x40:
                events.setdefault("awake", f)
            if o["req"] == 2:
                events.setdefault("trigger_request", f)
            if o["state"] == 2:
                events.setdefault("state2_loaded", f)
            if o["state"] == 3:
                events.setdefault("state3_loaded", f)
        elif o["type"] == 0x0F:
            events.setdefault("converted_to_0F", f)
    return {"columns": ["frame", "type", "state", "req", "frame_idx", "x", "y", "flags_04", "token_3e", "vx", "vy", "engine_pass"], "rows": rows, "events": events}


# --------------------------------------------------------------------------- #
# 7. whole-game fixtures for $24
# --------------------------------------------------------------------------- #
def key_rows(tr: dict, around: list) -> list:
    keep, rows = set(), tr["rows"]
    idx = {r[0]: i for i, r in enumerate(rows)}
    for f in around:
        if f in idx:
            for k in range(max(0, idx[f] - 1), min(len(rows), idx[f] + 2)):
                keep.add(k)
    return [rows[k] for k in sorted(keep)]


def summarize_track(tr: dict) -> dict:
    ev = tr["events"]
    rows = tr["rows"]
    out = {"events": ev, "frames_logged": len(rows), "sha256_rows": sha(json.dumps(rows).encode()), "columns": tr["columns"]}
    if "state3_loaded" in ev and "converted_to_0F" in ev:
        out["fall_frames_state3_to_conversion"] = ev["converted_to_0F"] - ev["state3_loaded"]
        p3 = next(r[11] for r in rows if r[0] == ev["state3_loaded"])
        p0f = next(r[11] for r in rows if r[0] == ev["converted_to_0F"])
        out["fall_engine_passes_state3_to_conversion"] = p0f - p3
    if "trigger_request" in ev and "state3_loaded" in ev:
        out["trigger_to_state3_frames"] = ev["state3_loaded"] - ev["trigger_request"]
    around = [v for k, v in ev.items() if k in ("trigger_request", "state2_loaded", "state3_loaded", "converted_to_0F", "slot_cleared")]
    out["rows_around_events"] = key_rows(tr, around)
    conv = next((r for r in rows if r[1] == 0x0F), None)
    if conv:
        out["converted_row"] = conv
        runs = []
        for r in rows:
            if r[1] == 0x0F:
                if runs and runs[-1][0] == r[4]:
                    runs[-1][1] += 1
                else:
                    runs.append([r[4], 1])
        out["post_conversion_runs"] = runs
    return out


def pair_fixture(g: Game, recA: dict, recB: dict) -> dict:
    tA, tB = recA["index_1based"], recB["index_1based"]
    out = {}
    ox_a, ox_b = recA["world_x"], recB["world_x"]
    cases = {"stand_beside_A_only": (ox_a - 44, tA, tB), "stand_beside_B_only": (ox_b + 43, tB, tA), "stand_between_both": ((ox_a + ox_b) // 2, tA, tB)}
    for name, (px, tfirst, tsecond) in cases.items():
        py = stand_y(g.cells, g.width, g.rom, px, recA["world_y"])
        g.place(px, py, rings=10)
        score0 = g.score()
        both = {}

        def hook(gg, f, both=both):
            for tok in (tA, tB):
                o = gg.by_token(tok, (0x24,))
                if o:
                    both.setdefault(tok, []).append([f, o["state"], o["req"], o["frame"], o["x"], o["y"]])
        trA = track_object(g, tA, 150, hook=hook, stop_on_clear=False)
        # B is tracked from the same run: re-run for B on a rewound identical start
        g.place(px, py, rings=10)
        trB = track_object(g, tB, 150, stop_on_clear=False)
        g.place(px, py, rings=10)
        for _ in range(150):
            g.frame()
        out[name] = {"player": [px, py], "A": dict(summarize_track(trA), token=tA, world=[recA["world_x"], recA["world_y"]], parameter=recA["parameter"]),
                     "B": dict(summarize_track(trB), token=tB, world=[recB["world_x"], recB["world_y"]], parameter=recB["parameter"]),
                     "score_after_150_frames_bcd": f"{g.score():06d}", "score_before": f"{score0:06d}", "occupancy_A": h(g.occupancy(tA), 2), "occupancy_B": h(g.occupancy(tB), 2),
                     "player_after": g.player(), "contact_helper_calls": sorted({(n, t) for n, ix, t in g.hits if n in ("wrapper_630b", "overlap_6328", "conversion_5f54")}, key=str)}
    return out


def landing_whole_game(rom: bytes, games: dict, rows24: list, lab_table: list) -> list:
    out = []
    for r, lab_row in zip(rows24, lab_table):
        g = games[r["act"]]
        prm = int(r["parameter"], 16)
        px = r["world_x"] + 40 if prm else r["world_x"] - 40
        py = stand_y(g.cells, g.width, rom, px, r["world_y"])
        entry = {"act": r["act"], "index_1based": r["index_1based"], "world": [r["world_x"], r["world_y"]], "parameter": prm, "player": [px, py]}
        if py is None:
            entry["error"] = "no floor under the parking column"
            out.append(entry)
            continue
        g.place(px, py, rings=10)
        tr = track_object(g, r["index_1based"], 200, stop_on_clear=False)
        ev = tr["events"]
        conv = next((x for x in tr["rows"] if x[1] == 0x0F), None)
        entry.update({"events": ev, "converted_row_xy": conv and [conv[5], conv[6]], "fall_frames_state3_to_conversion": ev.get("converted_to_0F", 0) - ev.get("state3_loaded", 0) if conv else None,
                      "fall_engine_passes_state3_to_conversion": (next(x[11] for x in tr["rows"] if x[0] == ev["converted_to_0F"]) - next(x[11] for x in tr["rows"] if x[0] == ev["state3_loaded"])) if conv else None,
                      "player_after": {k: v for k, v in g.player().items() if k in ("x", "y", "cur", "rings")},
                      "lab_conversion_xy": [lab_row["slot_after_conversion"]["x"], lab_row["slot_after_conversion"]["y"]],
                      "lab_fall_updates_minus_1": lab_row["fall_updates_to_conversion"] - 1,
                      "matches_lab": bool(conv and [conv[5], conv[6]] == [lab_row["slot_after_conversion"]["x"], lab_row["slot_after_conversion"]["y"]]
                                          and (next(x[11] for x in tr["rows"] if x[0] == ev["converted_to_0F"]) - next(x[11] for x in tr["rows"] if x[0] == ev["state3_loaded"])) == lab_row["fall_updates_to_conversion"] - 1)})
        out.append(entry)
    return out


def run_through(g: Game, recA: dict, recB: dict) -> dict:
    tA, tB = recA["index_1based"], recB["index_1based"]
    out = {}
    for name, start, pad in (("run_right_from_300", 300, PAD_RIGHT), ("start_inside_window_hold_right", recA["world_x"] - 46, PAD_RIGHT), ("run_left_from_620", 620, PAD_LEFT)):
        py = stand_y(g.cells, g.width, g.rom, start, recA["world_y"])
        g.place(start, py, rings=10)
        trig = {}
        samples = []

        def hook(gg, f, trig=trig, samples=samples):
            p = gg.player()
            for tok in (tA, tB):
                o = gg.by_token(tok, (0x24,))
                if o and o["req"] == 2:
                    trig.setdefault(tok, f)
                if o and abs(o["x"] - p["x"]) < 48 and len(samples) < 6:
                    samples.append([f, tok, p["x"] - o["x"], p["vx"], o["state"], o["req"], o["f4"]])
        for f in range(200):
            g.frame(pad)
            hook(g, f)
        out[name] = {"start_x": start, "pad": pad, "triggered_at_frame": {str(k): v for k, v in trig.items()}, "first_in_window_samples_columns": ["frame", "token", "dx_player_minus_obj", "player_vx", "state", "req", "flags_04"],
                     "first_in_window_samples": samples, "player_end": {k: v for k, v in g.player().items() if k in ("x", "y", "cur", "rings")}}
    return out


def contact_fixture(g: Game, recA: dict, recB: dict) -> dict:
    """Fork identical falling states and teleport the player onto the falling object; observe the real shared player-side outcome.

    Per frame the wrapper $630B entry hook records the anchors the object really saw (the player's own update runs first), so every row carries the
    observed (dx, dy) and the model verdict."""
    tA, tB = recA["index_1based"], recB["index_1based"]
    px = recA["world_x"] - 44
    py = stand_y(g.cells, g.width, g.rom, px, recA["world_y"])
    g.place(px, py, rings=10)
    for _ in range(400):
        g.frame()
        o = g.by_token(tA, (0x24,))
        if o and o["state"] == 3 and o["vy"] >= 16 * 20:
            break
    snap = g.snapshot()
    base_obj = g.by_token(tA, (0x24,))
    out = {"fork_object_row": {k: base_obj[k] for k in ("slot", "state", "frame", "x", "y", "vx", "vy")}, "variants": {}}

    def teleport(o, dx, dy, rings, cur, f3, d532, vx, d3b1=0):
        m, s_ = g.m, g.s
        m[0xD3B1] = d3b1
        s_.w16(0xD511, o["x"] + dx)
        s_.w16(0xD514, o["y"] + dy)
        s_.w16(0xD516, vx & 0xFFFF)
        s_.w16(0xD518, 0)
        m[0xD501] = m[0xD502] = cur
        m[0xD503] = f3
        m[0xD522] = 0x02 if cur in (1, 5) else 0
        m[0xD29A] = rings
        m[0xD532] = d532

    def frame_row(f, nh, nc):
        p = g.player()
        seen = [c for c in g.contacts[nc:] if c["type"] == 0x24]
        obs = [[c["slot"], c["px"] - c["ox"], c["py"] - c["oy"], int(overlap_model(c["px"] - c["ox"], c["py"] - c["oy"], c["ex"], c["ey"], c["pex"], c["pey"]) and not c["f3"] & 0x40)]
               for c in seen]
        names = [n for n, ix, t in g.hits[nh:]]
        model_d3b0 = 255 if any(o_[3] for o_ in obs) else 0
        return [f, p["x"], p["y"], p["cur"], p["f3"], p["rings"], p["d3b0"], p["d520"], p["d3b1"], sorted(set(names)), obs, model_d3b0]

    cols = ["frame", "player_x", "player_y", "state", "d503", "rings", "d3b0_end", "d520_end", "d3b1", "helpers_this_frame", "observed_[slot,dx,dy,model_overlap]", "model_d3b0"]

    def run(name, dx, dy, rings=10, cur=1, f3=0, d532=0, vx=0, frames=10, d3b1=0):
        g.rewind(snap)
        teleport(g.by_token(tA, (0x24,)), dx, dy, rings, cur, f3, d532, vx, d3b1)
        rows = []
        for f in range(frames):
            nh, nc = len(g.hits), len(g.contacts)
            g.frame()
            rows.append(frame_row(f, nh, nc))
        out["variants"][name] = {"setup": {"dx": dx, "dy": dy, "rings": rings, "state": cur, "f3": h(f3, 2), "d532": d532, "vx": vx, "d3b1": d3b1}, "rows_columns": cols, "rows": rows,
                                 "rows_where_end_of_frame_d3b0_differs_from_model": [r[0] for r in rows if (r[6] != 0) != (r[11] != 0)],
                                 "first_d3b0_frame": next((r[0] for r in rows if r[6]), None), "hurt_frames": [r[0] for r in rows if "hurt_48f7" in r[9]],
                                 "rings_after": rows[-1][5], "state_after": rows[-1][3], "object_alive": g.by_token(tA, (0x24,)) is not None}

    run("ordinary_10_rings", 0, 8)
    run("zero_rings", 0, 8, rings=0)
    run("rolling_state9_attack_bit1", 0, 8, cur=9, f3=0x02, vx=0x200)
    run("jump_state0A_attack_bit1", 0, 0, cur=0x0A, f3=0x03)
    run("invincible_d532_6", 0, 8, d532=6)
    for name, dx, dy in (("above", 0, -10), ("side_right", 12, 0), ("side_left", -12, 0), ("below", 0, 22), ("just_outside_side", 15, 0), ("just_outside_above", 0, -16),
                         ("just_outside_below", 0, 28)):
        run(name, dx, dy, frames=3)

    run("blinking_bit7_d3b1_120", 0, 8, f3=0x80, d3b1=0x78)
    run("hurt_state_1E_bit6", 0, 8, cur=0x1E, f3=0xC0, d3b1=0x78)
    return out


# --------------------------------------------------------------------------- #
# 8. lifecycle fixtures (whole game, no snapshot reset between teleports)
# --------------------------------------------------------------------------- #
def teleport(g: Game, x: int, y: int | None = None, rings: int = 10, **kw) -> None:
    """Move Sonic (and, through the harness helper, the camera) without restoring the game: objects, occupancy bytes and score persist."""
    if y is None:
        y = stand_y(g.cells, g.width, g.rom, x, 0) or 100
    g.lab.e.place(x, y, 0, 0, cur=kw.get("cur", 1), f3=kw.get("f3", 0), floor=True, rings=rings, prev=0x82)
    g.hits.clear()


def window_scan(g: Game, rec: dict) -> dict:
    """Initial-fill creation and wake band: teleport the camera/player at offsets and read the slot after 5 frames."""
    tok = rec["index_1based"]
    res = []
    for d in range(-520, 521, 4):
        px = rec["world_x"] + d
        if px < 24 or px > 4000:
            continue
        py = stand_y(g.cells, g.width, g.rom, px, 0) or (rec["world_y"] + 90)
        g.place(px, py, rings=10)
        for _ in range(5):
            g.frame()
        o = g.by_token(tok, (0x24, 0x2E))
        cam = g.s.u16(0xD174)
        res.append((rec["world_x"] - cam, o is not None, bool(o and not o["f4"] & 0x40)))
    created = [r[0] for r in res if r[1]]
    awake = [r[0] for r in res if r[2]]
    return {"object_minus_camera_x": {"created_range": [min(created), max(created)] if created else None, "awake_range": [min(awake), max(awake)] if awake else None},
            "sample_step": 4, "samples": len(res), "camera_relative_note": "camera X = D174 after teleport; object X - camera X is the screen column of the anchor"}


def walk_scan(g: Game, rec: dict, direction: int, start_x: int, frames: int = 900) -> dict:
    """Hold RIGHT/LEFT from a start position and log the anchor column (object X - camera X) at creation, wake, sleep and removal."""
    tok = rec["index_1based"]
    py = stand_y(g.cells, g.width, g.rom, start_x, 0 if direction > 0 else rec["world_y"])
    g.place(start_x, py, rings=10)
    log, prev = {}, None
    for f in range(frames):
        g.frame(PAD_RIGHT if direction > 0 else PAD_LEFT)
        o = g.by_token(tok, (0x24, 0x0F, 0x2E))
        cam = g.s.u16(0xD174)
        st = None if o is None else ("asleep" if o["f4"] & 0x40 else "awake")
        if st != prev:
            if st is not None or prev is not None:
                log.setdefault(f"{prev}->{st}", []).append([f, (rec["world_x"] - cam), g.s.u16(0xD511)])
            prev = st
        if g.m[0xD501] == 0x1F:
            break
    return {"direction": "right" if direction > 0 else "left", "start_x": start_x, "transitions_[frame,object_minus_camera_x,player_x]": log}


def lifecycle_24(g: Game, recA: dict, recB: dict) -> dict:
    tA, tB = recA["index_1based"], recB["index_1based"]
    out = {"window": window_scan(g, recA), "walk_right": walk_scan(g, recA, +1, 60),
           "left_side_note": "the left exit is symmetric (same bands, mirrored); a pit right of the MGHZ1 pair prevents a clean left-walking fixture, the initial-fill window scan covers both sides"}
    px = recA["world_x"] - 44
    py = stand_y(g.cells, g.width, g.rom, px, recA["world_y"])
    far = recA["world_x"] + 1500
    # before trigger: leave and come back
    g.place(px, py, rings=10)
    for _ in range(8):
        g.frame()
    before = {"occupancy_A_in_window": g.occupancy(tA)}
    teleport(g, far)
    for _ in range(40):
        g.frame()
    before.update({"A_present_after_leaving": g.by_token(tA, (0x24,)) is not None, "occupancy_A_after_leaving": g.occupancy(tA)})
    teleport(g, px - 24, py)               # return outside the 48-px trigger window so the recreated object is seen idle
    for _ in range(8):
        g.frame()
    a = g.by_token(tA, (0x24,))
    before.update({"A_recreated": a is not None, "A_row_after_return_[state,x,y,flags_04]": a and [a["state"], a["x"], a["y"], a["f4"]], "occupancy_A_after_return": g.occupancy(tA)})
    out["leave_before_trigger"] = before
    # mid-fall: trigger A, leave during the fall, come back
    g.place(px, py, rings=10)
    for _ in range(400):
        g.frame()
        o = g.by_token(tA, (0x24,))
        if o and o["state"] == 3 and o["vy"] >= 16 * 10:
            break
    fall_row = {k: o[k] for k in ("state", "x", "y", "vx", "vy", "f4")}
    teleport(g, far)
    for _ in range(40):
        g.frame()
    mid = {"fall_row_when_leaving": fall_row, "A_present_after_leaving": g.by_token(tA, (0x24,)) is not None, "any_slot_with_type_0F_or_24_at_origin": None,
           "occupancy_A_after_leaving": g.occupancy(tA), "score_after_leaving": f"{g.score():06d}"}
    teleport(g, px - 24, py)
    for _ in range(8):
        g.frame()
    a = g.by_token(tA, (0x24,))
    mid.update({"A_recreated": a is not None, "A_row_after_return_[state,x,y,flags_04,req]": a and [a["state"], a["x"], a["y"], a["f4"], a["req"]], "occupancy_A_after_return": g.occupancy(tA)})
    mid.pop("any_slot_with_type_0F_or_24_at_origin")
    out["leave_mid_fall"] = mid
    # asleep band mid-fall: the callbacks return while +$04 bit 6 is set, so a falling piece left behind by the camera hangs in the air until removal
    g.place(px, py, rings=10)
    for _ in range(400):
        g.frame()
        o = g.by_token(tA, (0x24,))
        if o and o["state"] == 3 and o["vy"] >= 16 * 10:
            break
    freeze = {"fall_row_before": {k: o[k] for k in ("state", "x", "y", "vy", "f4")}}
    aside = recA["world_x"] + 150
    teleport(g, aside, stand_y(g.cells, g.width, g.rom, aside, recA["world_y"]) or py)
    rows = []
    for _ in range(12):
        g.frame()
        o = g.by_token(tA, (0x24,))
        rows.append(o and [o["x"], o["y"], o["vy"], o["f4"], o["frame"]])
    freeze["object_minus_camera_x"] = recA["world_x"] - g.s.u16(0xD174)
    freeze["rows_[x,y,vy,flags_04,frame_idx]_over_12_frames"] = rows
    teleport(g, px, py)
    rows2 = []
    for _ in range(12):
        g.frame()
        o = g.by_token(tA, (0x24,))
        rows2.append(o and [o["x"], o["y"], o["vy"], o["f4"], o["frame"]])
    freeze["after_returning_[x,y,vy,flags_04,frame_idx]"] = rows2
    out["asleep_mid_fall"] = freeze
    # after landing: defeated A is detached from the placement, B (untouched) is recreated
    g.place(px, py, rings=10)
    for _ in range(160):
        g.frame()
    done = {"A_slot_after_landing": g.by_token(tA, (0x24,)) is None, "occupancy_A_after_landing": h(g.occupancy(tA), 2), "score": f"{g.score():06d}"}
    teleport(g, far)
    for _ in range(40):
        g.frame()
    teleport(g, px - 24, py)
    for _ in range(8):
        g.frame()
    done.update({"A_recreated_after_backtrack": g.by_token(tA, (0x24,)) is not None, "B_recreated_after_backtrack": g.by_token(tB, (0x24,)) is not None,
                 "occupancy_A_after_return": h(g.occupancy(tA), 2), "occupancy_B_after_return": h(g.occupancy(tB), 2)})
    out["leave_after_landing"] = done
    return out


# --------------------------------------------------------------------------- #
# 9. whole-game fixtures for $2E
# --------------------------------------------------------------------------- #
def kids_2e(g: Game) -> list:
    return [o for o in g.objs((0x2E,)) if o["p3f"]]


def parent_2e(g: Game, token: int):
    return g.by_token(token, (0x2E,))


def walk_in_2e(g: Game, rec: dict, start_x: int, start_y: int, direction: int, frames: int = 260, pad_extra: int = 0, floor: bool = True) -> dict:
    tok = rec["index_1based"]
    g.place(start_x, start_y, rings=10, floor=floor)
    log, spawns, prev_state = [], [], None
    first_parent = None
    for f in range(frames):
        g.frame((PAD_RIGHT if direction > 0 else PAD_LEFT) | pad_extra)
        p = g.player()
        par = parent_2e(g, tok)
        kids = kids_2e(g)
        if par and first_parent is None:
            first_parent = f
        if par and par["state"] != prev_state:
            log.append([f, "parent_state", prev_state, par["state"], par["x"], par["y"], p["x"], p["y"], p["cur"], p["face"]])
            prev_state = par["state"]
        if par and par["state"] == 2 and prev_state == 2 and not any(r[1] == "spawn" and r[0] == f for r in log):
            pass
        new = [k for k in kids if k["state"] == 0]
        if new:
            spawns.append([f, [[k["slot"], k["p3f"], k["x"], k["y"], k["vx"], k["vy"]] for k in new], p["face"], p["x"], p["y"], par and par["x"]])
        if g.m[0xD501] == 0x1F:
            break
    par_slot = next((o_["slot"] for o_ in g.objs((0x2E,)) if o_["t3e"] == tok), None)
    late = []
    for a_, b_ in zip(spawns, spawns[1:]):
        if b_[0] != a_[0] + 1:
            continue
        for k in a_[1]:
            nxt = next((q for q in b_[1] if q[0] == k[0] and q[1] == k[1]), None)
            if par_slot is not None and k[0] < par_slot and k[4] == 0 and nxt and nxt[4] != 0:
                late.append([a_[0], k[0], k[1]])
    return {"start": [start_x, start_y], "pad": "RIGHT" if direction > 0 else "LEFT", "parent_first_seen_frame": first_parent, "parent_slot": par_slot,
            "children_in_a_slot_below_the_parent_get_their_first_update_one_frame_late_[frame,slot,param]": late,
            "parent_state_changes_columns": ["frame", "what", "from", "to", "parent_x", "parent_y", "player_x", "player_y", "player_state", "player_face_bit4"], "parent_state_changes": log[:14],
            "spawn_passes_columns": ["frame", "[slot,param,x,y,vx,vy]", "player_face_bit4", "player_x", "player_y", "parent_x"], "spawn_passes": spawns[:8], "spawn_pass_count": len(spawns),
            "player_end": {k: v for k, v in g.player().items() if k in ("x", "y", "cur", "rings", "face")}}


def facing_left_burst_2e(g: Game, rec: dict) -> dict:
    """Create the parent from the left, then drop Sonic into the strip from above its right end while holding LEFT: the children must fly right."""
    tok = rec["index_1based"]
    g.place(rec["world_x"] - 100, 750, rings=10, floor=True)
    for _ in range(8):
        g.frame()
    right_end = rec["world_x"] + int(rec["aux1"], 16) * 16 - 20
    teleport(g, right_end, 700)
    rows = []
    for f in range(120):
        g.frame(PAD_LEFT)
        p = g.player()
        for k in kids_2e(g):
            if k["state"] in (0, 3) and k["vx"]:
                rows.append([f, p["face"], k["slot"], k["p3f"], k["x"], k["y"], k["vx"], k["vy"], p["x"], p["y"]])
        if rows and f > rows[0][0] + 3:
            break
    return {"columns": ["frame", "player_face_bit4", "slot", "param", "x", "y", "vx", "vy", "player_x", "player_y"], "first_child_rows": rows[:6],
            "all_child_vx_positive": bool(rows) and all(r[6] > 0 for r in rows), "player_face_bit4_values": sorted({r[1] for r in rows})}


def persistence_2e(g: Game, rec: dict) -> dict:
    """Keep-alive: after the parent's init callback it survives leaving the window; entering from the right on a FRESH load has no parent."""
    tok = rec["index_1based"]
    out = {}
    x0 = rec["world_x"] - 120
    g.place(x0, stand_y(g.cells, g.width, g.rom, x0, rec["world_y"] - 200) or 700, rings=10)
    for _ in range(8):
        g.frame()
    p = parent_2e(g, tok)
    out["near_left_end"] = {"parent_present": p is not None, "flags_04": p and h(p["f4"], 2), "state": p and p["state"], "occupancy": h(g.occupancy(tok), 2)}
    far = rec["world_x"] + int(rec["aux1"], 16) * 16 + 1400
    teleport(g, far)
    for _ in range(60):
        g.frame()
    p = parent_2e(g, tok)
    out["after_leaving_1400px_right"] = {"parent_present": p is not None, "flags_04": p and h(p["f4"], 2), "state": p and p["state"], "x": p and p["x"], "y": p and p["y"],
                                         "occupancy": h(g.occupancy(tok), 2)}
    g.place(far, stand_y(g.cells, g.width, g.rom, far, 0) or 700, rings=10)
    for _ in range(10):
        g.frame()
    p = parent_2e(g, tok)
    out["fresh_load_far_right"] = {"parent_present": p is not None, "occupancy": h(g.occupancy(tok), 2)}
    xr = rec["world_x"] + int(rec["aux1"], 16) * 16 - 10
    g.place(xr, stand_y(g.cells, g.width, g.rom, xr, rec["world_y"] - 200) or 700, rings=10)
    for _ in range(10):
        g.frame()
    p = parent_2e(g, tok)
    out["fresh_load_inside_strip_right_end"] = {"player_x": xr, "camera_x": g.s.u16(0xD174), "parent_present": p is not None, "parent_x_minus_camera_x": p and (p["x"] - g.s.u16(0xD174)),
                                                "window_rule": "object X must lie in [camera-128, camera+384) at creation"}
    return out


def no_contact_2e(g: Game, rec: dict) -> dict:
    """Park Sonic on top of the parent and the children for many frames; nothing in the contact helpers may ever run with IX in a $2E slot."""
    tok = rec["index_1based"]
    x = rec["world_x"] + 60
    g.place(x, rec["world_y"] + 0, rings=10, floor=False)
    # make the strip trigger repeatedly: keep Sonic at the trigger Y (floor flag clear, state falling is irrelevant: the callback reads only X/Y)
    seen_overlap, d3b0_frames = 0, []
    for f in range(120):
        g.s.w16(0xD514, rec["world_y"])
        g.s.w16(0xD518, 0)
        g.frame()
        if g.m[0xD3B0] or g.m[0xD520]:
            d3b0_frames.append(f)
        for k in g.objs((0x2E,)):
            dx, dy = g.s.u16(0xD511) - k["x"], g.s.u16(0xD514) - k["y"]
            if abs(dx) <= 8 + max(k["ex"], 1) and -k["ey"] <= dy <= 24:
                seen_overlap += 1
    ix_types = sorted({t for n, ix, t in g.hits if n in ("wrapper_630b", "overlap_6328", "solid_5fa0", "attack_gate_5f3d", "conversion_5f54") and t is not None})
    return {"frames": 120, "frames_with_geometric_overlap_of_a_2E_box_and_sonic": seen_overlap, "contact_helper_hits_by_slot_type_decimal": ix_types, "type_2E_decimal": 0x2E,
            "any_helper_hit_with_a_2E_slot": 0x2E in ix_types, "frames_with_d3b0_or_d520_set": d3b0_frames, "player_end": {k: v for k, v in g.player().items() if k in ("x", "y", "cur", "rings", "d3b0", "d520")}, "extents_in_slot_examples": sorted({(k["frame"], k["ex"], k["ey"]) for k in g.objs((0x2E,))})}


def static_contact_scan(rom: bytes) -> dict:
    """Whole-callback scan: do the $2E or $24 callbacks reference the contact/solid/attack helper vectors or read +$2C/+$2D?"""
    refs = {}
    for t, (bank, a, b) in CALLBACK_RANGES.items():
        text = disasm(rom, bank, a, b)
        calls = [ins["text"] for ins in text if ins["text"].upper().startswith(("CALL", "JP"))]
        reads = [ins["cpu"] + " " + ins["text"] for ins in text if "0x2c" in ins["text"].lower() or "0x2d" in ins["text"].lower()]
        refs[h(t, 2)] = {"calls_and_jumps": calls, "reads_of_extents_2c_2d": reads}
    return refs


# --------------------------------------------------------------------------- #
# 10. runtime art check against the approved MGHZ board
# --------------------------------------------------------------------------- #
ART_APPROVAL = ROOT / "data" / "rom-cache" / "mghz" / "art-approval.json"


def approved_hashes() -> dict:
    data = json.loads(ART_APPROVAL.read_text(encoding="utf-8"))
    return {int(k, 16): {int(f): v[0] for f, v in subj["frame_hashes"].items()} for k, subj in data["subjects"].items() if k in ("0x24", "0x2E")}


def art_runtime_check(rom: bytes, g: Game, scenario, frames: int) -> dict:
    """Run a whole-game scenario; every frame compare (a) the VRAM tile pixels of each drawn $24/$2E frame with the approved board hash,
    (b) the live sprite palette with the approved CRAM row and (c) the model SAT pieces of every drawn slot with the VRAM SAT.

    The attribute table reaches VRAM late (one logic update, more in lag frames), so (c) queues the expected piece set of each slot at the end of
    every frame and marks it satisfied when the whole set appears in a later VRAM SAT (delay recorded; expiry after 3 frames counts as a miss)."""
    import mapped_object_registration as MR
    import thz1_object_assets as G
    approved = approved_hashes()
    pal_art = json.loads((ROOT / "data" / "rom-cache" / "mghz" / "object-census.json").read_text(encoding="utf-8"))["enemies"]["0x24"]["art"]["sprite_palette_cram"]
    fps = {t: G.mapping_frame_pointers(rom, G.object_mapping(rom, t)["mapping_cpu"]) for t in (0x24, 0x2E)}
    queue: list = []
    cam_prev = None
    stats = {"frames": 0, "slot_frames_checked": 0, "satisfied_by_delay": {}, "missed": 0, "per_type_frame": {}, "unapproved_compositions": [],
             "palette_frames_checked": 0, "palette_frames_equal_to_approved_row": 0}
    for f in range(frames):
        scenario(g, f)
        s, m = g.s, g.m
        sat = {(y, x, n) for (_i, y, x, n) in s.sat()}
        vram = bytes(s.vram)
        cam = (s.u16(0xD174), s.u16(0xD176))
        stats["palette_frames_checked"] += 1
        stats["palette_frames_equal_to_approved_row"] += int(list(s.cram[16:32]) == pal_art)
        for o in g.objs((0x24, 0x2E)):
            if not o["frame"]:
                continue
            b = SLOT_BASE + o["slot"] * 0x40
            alts = []
            for cx, cy in ((cam[0], cam[1]), (s.u16(0xD284), s.u16(0xD286))) + ((cam_prev,) if cam_prev else ()):
                pieces = MR.model_slot(rom, obj_x=o["x"], obj_y=o["y"], cam_x=cx, cam_y=cy, frame_cpu=fps[o["type"]][o["frame"]], flags=m[b + 4], art0=m[b + 8], art1=m[b + 9])
                keys = {(p["sat_y"], p["sat_x"], p["tile"]) for p in pieces if not p.get("hidden_by_y_clip")}
                if keys:
                    alts.append(keys)
            if alts:
                queue.append({"frame": f, "alts": alts, "keys": alts[0], "slot": o["slot"], "obj": [o["type"], o["frame"], o["x"], o["y"], cam[0], cam[1]]})
                stats["slot_frames_checked"] += 1

            rel = C.sat_pieces(rom, o["type"], o["frame"], m[b + 8], m[b + 9], False)
            for p in rel:
                p["pixels"] = G.tile_pixels(vram, p["pattern"]) + G.tile_pixels(vram, p["pattern"] + 1)
            ok = C.composed_hash(rel) == approved[o["type"]][o["frame"]]
            e = stats["per_type_frame"].setdefault(f"{o['type']:02X}:{o['frame']}", {"seen": 0, "hash_matches_approved": 0})
            e["seen"] += 1
            e["hash_matches_approved"] += int(ok)
            if not ok and len(stats["unapproved_compositions"]) < 6:
                stats["unapproved_compositions"].append([f, o["type"], o["frame"], o["slot"]])
        keep = []
        for item in queue:
            if any(k <= sat for k in item["alts"]):
                d = str(f - item["frame"])
                stats["satisfied_by_delay"][d] = stats["satisfied_by_delay"].get(d, 0) + 1
            elif f - item["frame"] >= 3:
                stats["missed"] += 1
                if len(stats.setdefault("missed_examples", [])) < 6:
                    stats["missed_examples"].append({"frame": item["frame"], "keys": sorted(item["keys"]), "slot": item["slot"], "obj": item["obj"],
                                                     "sat_entries_near": sorted(e for e in sat if any(abs(e[1] - k[1]) < 16 and abs(e[0] - k[0]) < 24 for k in item["keys"]))})
            else:
                keep.append(item)
        queue = keep
        stats["frames"] += 1
        cam_prev = cam
    stats["unresolved_at_end_of_run"] = len(queue)
    return stats


# --------------------------------------------------------------------------- #
# 11. static scans: extent readers, creators of $24/$2E, replacement object $0F
# --------------------------------------------------------------------------- #
def extent_readers(rom: bytes) -> dict:
    reads = {0x7E, 0x46, 0x4E, 0x56, 0x5E, 0x66, 0x6E, 0x86, 0x8E, 0x96, 0x9E, 0xA6, 0xAE, 0xB6, 0xBE}
    out = []
    for off in range(len(rom) - 3):
        if rom[off] in (0xDD, 0xFD) and rom[off + 1] in reads and rom[off + 2] in (0x2C, 0x2D):
            bank = off // 0x4000
            out.append({"file": h(off, 5), "bank": h(bank, 2), "cpu": h(off if bank < 2 else 0x8000 + off % 0x4000), "bytes": rom[off:off + 3].hex()})
    in_overlap_family = [r for r in out if 0x5FA0 <= int(r["file"], 16) < 0x6500 and r["bank"] == "0x01"]
    inside_callbacks = [r for r in out if any(r["bank"] == h(b, 2) and a <= int(r["cpu"], 16) < e for _t, (b, a, e) in CALLBACK_RANGES.items())]
    return {"method": "byte scan of the whole 512 KB ROM for (IX|IY+$2C/$2D) register/ALU reads", "total_matches": len(out), "matches": out,
            "inside_shared_overlap_family_5FA0_64FF": len(in_overlap_family), "inside_the_24_or_2E_callback_ranges": inside_callbacks,
            "note": "the fixed-bank matches at $1BFC/$2DC0/$2E3D/$2E61 read +$2C as a different structure's field (sound/HUD style slots); the bank $0C/$1E matches belong to other object types"}


def creator_scan(rom: bytes, scan: dict) -> dict:
    """Who can create type $24 / $2E, and does any other type share their state tables (aliases)?"""
    hits = {"0x24": [], "0x2E": [], "0x2D": []}
    for t in (0x24, 0x2E, 0x2D):
        for off in range(len(rom) - 4):
            if rom[off:off + 4] == bytes([0xFD, 0x36, 0x00, t]) or (rom[off:off + 3] == bytes([0x3E, t, 0xFD]) and rom[off + 3] == 0x77):
                hits[h(t, 2)].append(h(off, 5))
    tables = {}
    for t in range(1, 0x60):
        tab = C.state_table(rom, t)
        tables.setdefault(tab["state_table_cpu"], []).append(t)
    aliases = {h(k): [h(t, 2) for t in v] for k, v in tables.items() if len(v) > 1 and (0x24 in v or 0x2E in v)}
    graph = {}
    for t in range(1, 0x60):
        sc = C.state_scripts(rom, t)
        for sp in sc["spawns"]:
            if sp["type"] in (0x24, 0x2E):
                graph.setdefault(h(sp["type"], 2), []).append({"spawned_by_type": h(t, 2), "state": sp["state"], "dx": sp["dx"], "dy": sp["dy"], "parameter": sp["parameter"]})
    placed_2d = [r for r in scan.get("all_lists_type_2D", [])]
    return {"immediate_type_load_patterns_FD3600nn_and_3Ennfd77": hits, "state_table_alias_groups_containing_24_or_2E": aliases,
            "state_script_spawn_commands_for_24_2E_over_types_01_5F": graph, "type_2D_placements_in_the_18_lists": placed_2d,
            "conclusion": "the only creators are the placement creator ($80EB) and the $2E state-2 script; type $2D shares $2E's state table ($1E:$8A45, type-table entries $6612 and $6614) but is never placed, never spawned and never loaded by an immediate-type pattern, so it is an unused alias, not a dependency"}


def replacement_0f(rom: bytes, pair: dict) -> dict:
    sc = C.public_script(C.state_scripts(rom, 0x0F))
    a = pair["stand_beside_A_only"]["A"]
    conv, clear = a["events"].get("converted_to_0F"), a["events"].get("slot_cleared")
    thz1 = L.build_act(rom, "thz1")
    mg = C.vram_for_act(rom, 0)

    def tiles(vram):
        return sha(bytes(vram)[36 * 32:46 * 32]) if not isinstance(vram, (list, dict)) else None
    return {"conversion_routine": "$5F54 via vector $033E: adds score table entry $27EB to the score (BCD bytes 10 00 00 unless $D292 != 0), sets slot type $0F, clears +1,+2,+4,+7,+14,+15,+$3E,+$3F; keeps position, +8/+9 and the renderer's saved frame pointer",
            "score_added_bcd_bytes": "10 00 00", "score_observed_after_one_landing_whole_game": a and pair["stand_beside_A_only"]["score_after_150_frames_bcd"],
            "placement_detach": "+$3E cleared and D400[index-1] left at the type byte: the placement is consumed for the loaded act (no respawn after backtracking)",
            "state_table": {"bank": sc["bank"], "state_count": sc["state_count"], "frames_used": sc["frames_used"], "states": sc["states"][:3]},
            "whole_game_lifetime_frames_from_conversion_to_slot_clear": (clear - conv) if conv is not None and clear is not None else None,
            "post_conversion_runs_[frame_index,count]": a.get("post_conversion_runs"),
            "art": "the replacement keeps the saved frame pointer for the conversion pass, then its own init writes +8 := 0 and +4 := 1; its frames 7-9 use tile base 0 (VRAM tiles $24..$2C), not the $24 art base $A0",
            "shared_with_thz_and_gpz_enemy_defeats": True,
            "vram_tiles_36_to_45_sha256": {"mghz1_act_vram": sha(bytes(mg["vram"])[36 * 32:46 * 32]), "thz1_act_vram": sha(bytes(thz1["vram"])[36 * 32:46 * 32])}}


# --------------------------------------------------------------------------- #
# 12. classification, checklist, candidates
# --------------------------------------------------------------------------- #
def classification() -> list:
    return [
        {"constant": "$24 trigger |dx| < 48 (strict) and |player vx| < $0100", "class": "PLAYER_DIST(48)", "adapter": "none for X; the vx gate is a player-speed gate (WORLD)"},
        {"constant": "$24 shake offsets (+2,+4,+2,0 x4 px), fall vx +-$80, gravity $10, landing probe (X, Y+18) on 32x32 cells", "class": "WORLD", "adapter": "none"},
        {"constant": "$24 create / wake / sleep / delete band (object X - camera X: create -96..348, awake -32..284; removal at <-96 / >=352)", "class": "EDGE(left,-96/-32), EDGE(right,+32/+96)",
         "adapter": "widescreen needs the generic lifecycle adapter (already tracked); no $24-specific constant"},
        {"constant": "$24 pair spacing 16 px and symmetric +-0.5 px/update drift", "class": "WORLD", "adapter": "none"},
        {"constant": "$2E strip: originX < playerX <= originX + aux1*16, |objY - playerY| < 3", "class": "WORLD", "adapter": "none"},
        {"constant": "$2E parent exists only if it was created while its origin lay in [camera-128, camera+384)", "class": "EDGE(left,-128), EDGE(right,+128 beyond RIGHT)",
         "adapter": "REQUIRED DECISION: a wider view creates the parent earlier/more often (e.g. entering the MGHZ1 oil strip from the right): faithful SMS behaviour = no splash when the parent was never created"},
        {"constant": "$2E parent keep-alive (+$04 bit 1) after its init callback", "class": "WORLD", "adapter": "none; POC may simply keep the emitter for the act"},
        {"constant": "$2E children: spawn offsets (4,0),(0,-2),(-4,-4), vx +-(160+16n)/256 depending on player facing, vy -1.0, gravity $10, 14 passes", "class": "WORLD",
         "adapter": "none"},
        {"constant": "slot pool 7..17 (11 slots) shared by all dynamic objects; children are skipped silently when full", "class": "WORLD (engine capacity)", "adapter": "decide whether the POC emulates the 11-slot pool; fidelity differs only under heavy splash load"},
    ]


def poc_checklist() -> list:
    return [
        "Implement $24 as: created asleep; first update requests state 1 (idle frames 1-3, 8 updates each, repeating); contact is checked every update from state 1 on, before movement.",
        "Trigger (awake, state 1 only): |objX - playerX| < 48 and |playerVX| < $0100 (8.8) -> state 2. No vertical test, no player-state test.",
        "State 2 (17 updates after the trigger update): vx +$0200, 2 updates frame 1; vx -$0200, 2 updates frame 2; repeated 4x (x offsets +2,+4,+2,0 then repeat); then frame 3 for the init update that sets vx = +$80 (parameter 0) or -$80 (parameter != 0), vy = 0, request state 3.",
        "State 3: each update contact, then x += vx, y += vy (24-bit 8.8), vy += $10, then probe the 32x32 block at (x, y+18): header bit 6 or 7 (whole cell, no profile) -> convert. Frames 1,2,3 x4 updates each, repeating.",
        "Convert: score += 10 (BCD bytes 10 00 00), slot becomes shared type $0F at the same x,y (explosion frames 7-9, art base 0), detached from the placement (no respawn this act load).",
        "Contact (shared wrapper $0434): closed boxes, object extents 4x11 (anchor bottom-centre), Sonic 8x24 (9x24 in state $0F); hit when |dx| <= 12 (13) and -11 <= dy <= 24; any posture, including attacking, is hurt (D3B0). Invincibility power-up ($D532 == 6) clears the request; blink (D503 bit 7) holds it back; hurt state (bit 6) disables contact. No rebound, no object state change, no cooldown.",
        "Lifecycle: placement-backed, removable ($FE) when outside the generic window at any state (including mid-fall); recreated fresh at the original position when the camera returns; a landed (converted) $24 never respawns.",
        "Mapped pairs: records come as (parameter 1 at X) + (parameter 0 at X+16): the left piece falls left (-$80), the right piece falls right (+$80); each triggers on its own |dx| < 48 test.",
        "Implement $2E parent as a keep-alive emitter (never deleted after its init callback, +$04 bit 1): strip X in (originX, originX + aux1*16], trigger |objY - playerY| < 3, copies playerX into its own X, 4 updates of frame 4, then spawns 3 children (parameters 1,2,3 at offsets (4,0),(0,-2),(-4,-4)) and immediately re-evaluates the trigger (period 5 updates while Sonic stays in the band).",
        "Children: init update (state 0, frame 0, no movement) sets vx = -(160+16n) if player object flag bit 4 is clear, +(160+16n) if set; vy = -$100; then 12 moving updates (frames 1,2,3 x4) with x += vx, y += vy, vy += $10, then a 13th update that marks the slot removable ($FE -> $FF -> cleared). Never mirrored (+$04 bit 4 stays clear).",
        "$2E has NO contact: its frames carry extents 4x16 / 8x16 but nothing reads them (zero hits of $6328/$630B/$5FA0 with a $2E slot, 120+ overlapping frames).",
        "The 11-slot dynamic pool (slots 7..17) bounds simultaneous splashes: a spawn command silently skips when no slot is free; children in slots below the parent's slot index run one update later.",
        "Art: no new approval required (all drawn frames hash-equal to the approved board, palette row equal). The converted $0F uses the shared explosion art.",
        "Widescreen: only the generic lifecycle band and the $2E parent creation window need an adapter decision; no constant is screen-relative inside $24/$2E logic.",
    ]


def agents_candidates() -> list:
    return [
        "MGHZ `$24` (12 mapped records, MGHZ1/MGHZ2 only, pairs 16 px apart) is a proximity-triggered shake-then-fall hazard: trigger |dx| < 48 and |vx| < $100, 17-update shake, then +-0.5 px/update drift with gravity $10 until the 32x32 cell at (x, y+18) is solid/one-way; landing converts to `$0F` (+10 score, detached); contact is shared `$0434` (any posture is hurt). Audit: `docs/mghz-object-24-2e-audit.md`.",
        "MGHZ `$2E` (1 record per act) is a keep-alive strip emitter, not a contact enemy: placement `aux1` is the strip length in 16-px units (`$13`/`$1B`), Sonic X in (originX, originX + aux1*16] and |objY - playerY| < 3 spawns three splash children (param 1..3) every 5 updates; children fly opposite to the player's object-flag bit 4; no extents are consumed.",
        "Placement `aux1` is not always an art base: `$2E` uses it as strip length; the creator copies it to `+$09` for every type.",
        "Animation script command `spawn` allocates only from object slots 7..17 (`$5EE1`, 11 slots) and silently skips when full; a child in a slot below its parent's index first runs one update later.",
        "Dispatch table `$5E70` is indexed by `type & 15` for types >= `$F0`: `$FE` -> `$626D` (becomes `$FF`), `$FF` -> `$5EF8` (releases `D400[+$3E - 1]` if non-zero and zeroes the slot): removal takes two scheduler passes.",
        "Enemy conversion `$5F54` keeps the old saved frame pointer for the conversion pass; the replacement `$0F` re-initialises its art base to 0 on its first callback.",
    ]


# --------------------------------------------------------------------------- #
# 13. build
# --------------------------------------------------------------------------- #
def timeline_24(tmpl: dict, whole: dict) -> dict:
    t0, ff = tmpl["trigger_update"], tmpl["first_state3_update"]
    a = whole["stand_beside_A_only"]["A"]
    ev = a["events"]
    return {"definition": "T = the update whose state-1 callback $B49A requests state 2 (lab update index t0); whole-game frames count from the teleport",
            "lab": {"T": t0, "shake_updates_T_plus": [1, ff - t0 - 2], "init_update_sets_fall_velocity_T_plus": ff - t0 - 1, "first_falling_update_T_plus": ff - t0},
            "whole_game_pair_A_only": {"created_frame": ev.get("first_seen"), "awake_frame": ev.get("awake"), "trigger_request_frame": ev.get("trigger_request"),
                                       "state2_loaded_frame": ev.get("state2_loaded"), "state3_loaded_frame": ev.get("state3_loaded"), "converted_to_0F_frame": ev.get("converted_to_0F"),
                                       "slot_cleared_frame": ev.get("slot_cleared"), "state3_to_conversion_frames": a.get("fall_frames_state3_to_conversion")}}


def contact_summary(cs: dict) -> dict:
    out = {"object_extents": cs["object_extents"], "grid": cs["grid"], "cases": cs["cases"], "mismatch_with_closed_interval_model": cs["mismatch_total"], "variants": {}}
    ordinary = cs["variants"]["ordinary_8x24"]
    out["axis_classes_ordinary"] = {str(c["contact_bits_21_low"]): {"d521_high": c["d521_high"], "cells": c["cells"]} for c in ordinary["classes"] if c["d3b0"]}
    out["axis_bit_meaning"] = "low nibble of +$21: bit0 = object box above-contact (player above), bit1 = below, bit2 = right side, bit3 = left side (as set by $6328); D521 high nibble mirrors them; ties go vertical"
    for name, v in cs["variants"].items():
        out["variants"][name] = {"hit_rects_dx0_dx1_dy0_dy1": v["d3b0_set_rects_dx0_dx1_dy0_dy1"], "hit_cells": v["hit_cells"], "model_cells": v["model_cells"], "mismatch": v["mismatch_with_model"],
                                 "flag_20_set_in_hits": sorted({c["flag_20"] for c in v["classes"] if c["d3b0"]}), "d520_in_hits": sorted({c["d520"] for c in v["classes"] if c["d3b0"]})}
    return out


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    scan = scan_all_zones(rom)
    rows = placement_rows(rom, scan)
    r24, r2e = mghz_rows(rows, 0x24), mghz_rows(rows, 0x2E)
    census = json.loads((ROOT / "data" / "rom-cache" / "mghz" / "object-census.json").read_text(encoding="utf-8"))
    out = {"format": 1, "rom_sha256": ROM_SHA256, "research_base": RESEARCH_BASE, "research_only": True, "poc_untouched": True,
           "scope": {"in": ["$24", "$2E"], "out": ["$56/$57/$58", "shared-player polish", "monitor fixes", "later-zone rollout"]},
           "evidence_vocabulary": ["DECODED DATA", "BYTE-VERIFIED ASSEMBLY", "SOURCE-TRACED BEHAVIOR", "CONTROLLED ROUTINE RESULT", "EMULATED ORIGINAL FRAME", "MODEL", "UNRESOLVED"],
           "identity": {
               "0x24": {"evidence": "BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT + EMULATED ORIGINAL FRAME",
                        "behavior": "placement-backed hazard: idles, shakes when Sonic is within 48 px horizontally and slower than $100, then drifts +-0.5 px/update outward while accelerating downwards until the 32x32 map cell under it is solid or one-way, where it converts to the shared defeat effect `$0F` (+10 score) and is detached from its placement; hurts Sonic on any overlap (any posture) from state 1 on",
                        "name_status": "no descriptive name adopted; numeric type only (community labels remain leads)"},
               "0x2E": {"evidence": "BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT + EMULATED ORIGINAL FRAME",
                        "behavior": "keep-alive strip emitter (parameter 0) plus its three short-lived particle children (parameters 1..3): emits a 3-particle burst at Sonic's X every 5 updates while Sonic's anchor Y is within +-2 of the emitter Y and X lies in (originX, originX + aux1*16]; no contact box is consumed",
                        "name_status": "no descriptive name adopted; numeric type only (community labels remain leads)"}},
           "placements": {"lists_scanned": scan["lists_scanned"], "total_matching_records": len(scan["placements"]),
                          "by_act": {k: len([r for r in rows if r["act"] == k]) for k in sorted({r["act"] for r in rows})},
                          "later_zone_placements": [r for r in rows if not r["act"].startswith("mghz")],
                          "records": rows, "creator_rule": creator_rule(), "parameter_flag_families": {
                              "0x24": {"flags": "0x00 in all 12 records (no mirror bit, no keep-alive bit)", "parameter_0": 6, "parameter_1": 6, "aux0": "0xA0 (art base)", "aux1": "0xA0 (unused copy)",
                                       "pairs": "6 pairs at (X, X+16), same Y: parameter 1 then parameter 0", "y_values": sorted({r["world_y"] for r in r24})},
                              "0x2E": {"flags": "0x00", "parameter": "0 only; children use 1,2,3 via the spawn command", "aux0": "0x72 (art base)", "aux1": "0x13 (MGHZ1) / 0x1B (MGHZ2) = strip length in 16-px units, NOT an art base"}},
                          "tracking": "token +$3E = index (1-based); D400[index-1] := type at creation; released by the $FE/$FF cleanup; a converted $24 keeps D400 so it is not recreated"},
           "census_cross_check": {"census_placement_counts": {"0x24": len(census["enemies"]["0x24"]["placements"]), "0x2E": len(census["enemies"]["0x2E"]["placements"])},
                                  "this_audit_counts": {"0x24": len(r24), "0x2E": len(r2e)}},
           "creators": creator_scan(rom, scan),
           "static": {"code": code_facts(rom), "state_tables": {"0x24": state_facts(rom, 0x24), "0x2E": state_facts(rom, 0x2E), "0x0F": state_facts(rom, 0x0F)},
                      "frame_headers": {"0x24": frame_headers(rom, 0x24), "0x2E": frame_headers(rom, 0x2E)},
                      "mapping_and_art_from_census": {t: {"mapping": census["enemies"][t]["mapping"], "art": census["enemies"][t]["art"]} for t in ("0x24", "0x2E")},
                      "extent_readers": extent_readers(rom), "callback_helper_references": static_contact_scan(rom)},
           "creator_init": creator_init(rom, rows),
           "corrections_to_object_census": [
               "$24 state 3 does not 'delete itself': when the block under (X, Y+18) is solid/one-way it calls the defeated-enemy conversion $033E ($5F54): +10 score, slot becomes type $0F, detached from the placement.",
               "$0431 is the gravity add (+$18/+$19 += DE), not a contact helper; the contact helper is $0434 ($630B -> $6328).",
               "$2E frame 0 has extents 0x0, frames 1-3 carry 4x16 and frame 4 carries 8x16; 'zero extents' was only frame 0 and no code consumes the others.",
               "$2E placement aux1 ($13 / $1B) is the strip length in 16-px units (parent state-0 callback $8A8A), not an art base and not a mirror base.",
               "The $2E parent is not deleted through $034A; only its children are. After its init callback the parent is keep-alive (+$04 bit 1)."],
           "extent_resolution_2E": {"old_census_claim": "extents 0x0 (no contact box)", "resolved": "frame 0 has extents 0x0; frames 1..3 carry 4x16 and frame 4 carries 8x16 (written to +$2C/+$2D by the animation engine) but no code path reads them for a $2E slot: the callbacks call neither $0434/$033B/$034D nor read +$2C/+$2D, and 120+ overlapping frames in the whole game produced no helper hit with a $2E slot"}}
    if static_only:
        out["static_only"] = True
        return out

    # ---- object $24, controlled
    tmpl = {str(p): shake_and_fall_template(rom, next(r for r in r24 if int(r["parameter"], 16) == p)) for p in (0, 1)}
    lab_table = landing_table(rom, r24)
    first_rec = r24[0]
    cs = contact_sweep(rom, first_rec)
    o24 = {"trigger": {r["act"] + ":" + str(r["index_1based"]): trigger_sweep(rom, r) for r in (r24[0], next(r for r in r24 if r["act"] == "mghz2"))},
           "idle_state_1": "frames 1,2,3 for 8 updates each, repeating (24-update loop); phase depends on the creation update",
           "shake_and_fall_templates_by_parameter": tmpl, "landing_table_controlled": lab_table, "landing_all_match_model": all(x["model_matches_lab"] for x in lab_table),
           "landing_rule": "after each state-3 update (move, gravity) the block header flags of the 32x32 cell at (X, Y+18) are tested: bit 6 or bit 7 set -> convert; the profile/slope is not read; outside the map reads as air",
           "contact": contact_summary(cs)}
    # ---- whole game
    g1, g2 = Game(rom, "mghz1"), Game(rom, "mghz2")
    pair = pair_fixture(g1, r24[0], r24[1])
    o24["timeline"] = timeline_24(tmpl["1"], pair)
    o24["whole_game"] = {"pair_fixture_mghz1_index26_27": pair, "landing_all_12_placements": landing_whole_game(rom, {"mghz1": g1, "mghz2": g2}, r24, lab_table),
                         "run_through_and_slow_entry": run_through(g1, r24[0], r24[1]), "contact_outcomes": contact_fixture(g1, r24[0], r24[1]),
                         "lifecycle_mghz1": lifecycle_24(g1, r24[0], r24[1])}
    o24["replacement_effect_0F"] = replacement_0f(rom, pair)
    out["object_24"] = o24

    # ---- object $2E
    sweeps = {r["act"]: strip_trigger_sweep(rom, r) for r in r2e}
    o2e = {"strip_trigger": sweeps, "splash_burst_controlled": {r["act"]: splash_summary(rom, r) for r in r2e[:1]}, "retrigger_cadence": retrigger_cadence(rom, r2e[0]),
           "slot_pool_exhaustion": pool_exhaustion(rom, r2e[0]), "model_children_rule": {
               "child_vx_8_8": "$FF60 - 16n (object flag bit 4 clear on the PLAYER object $D504) / $00A0 + 16n (bit 4 set)", "child_vy_8_8": "-$0100", "gravity_8_8": "+$10 per moving update",
               "spawn_offsets_by_parameter": {"1": [4, 0], "2": [0, -2], "3": [-4, -4]}, "spawn_position": "parent X (= player X at the trigger update) + dx, parent Y + dy; the spawn command copies +$04 bit 4 (always 0), +$08, +$09"}}
    walk1 = walk_in_2e(g1, r2e[0], 1250, 750, +1)
    walk2 = walk_in_2e(g2, r2e[1], 150, 878, +1, frames=300)
    o2e["whole_game"] = {"mghz1_walk_in_from_left_rim": walk1, "mghz2_walk_in_from_left_rim": walk2, "persistence": persistence_2e(g1, r2e[0]), "facing_left_burst": facing_left_burst_2e(g1, r2e[0]), "no_contact": no_contact_2e(g1, r2e[0])}
    out["object_2e"] = o2e

    # ---- lifecycle classification, art, checklist
    out["lifecycle"] = {"generic_rule": "post-update $61E1 (current state != 0): bit 6 cleared inside the awake band, set in the sleep band; outside the 512-px window -> type $FE (token != 0) or $FF (token 0) unless +$04 bit 1; $FE -> $626D -> $FF -> $5EF8 cleanup", "sleep_gates": {"0x24": "callbacks $B49A/$B4C5/$B4F0 return at once while +$04 bit 6 is set (no trigger, no contact, no movement); state 0 init $B490 ignores bit 6", "0x2E": "none of the callbacks tests bit 6; the parent runs asleep or awake"},
                        "keep_alive": {"0x24": "never", "0x2E": "parent: +$04 bit 1 set by the init callback $8A8A; children: not placement-backed, removed by their own $034A after 14 passes"},
                        "classification": classification()}
    px = r24[0]["world_x"] - 44
    g1.place(px, stand_y(g1.cells, g1.width, rom, px, 112), rings=10)
    art24 = art_runtime_check(rom, g1, lambda gg, f: gg.frame(), 110)
    g1.place(1250, 750, rings=10, floor=True)
    art2e = art_runtime_check(rom, g1, lambda gg, f: gg.frame(PAD_RIGHT), 150)
    out["art"] = {"approved_board": "data/rom-cache/mghz/art-approval.json (approved 2026-10-04)", "frames_reached": {"0x24": [0, 1, 2, 3], "0x2E": [0, 1, 2, 3, 4]},
                  "runtime_check_0x24": art24, "runtime_check_0x2E": art2e,
                  "orientation": "+$04 bit 4 is never set (placement flags 0; scripts never write it; spawn copies it from the parent): all runtime images are the unmirrored board images; the fall direction is motion only",
                  "anchor_and_presentation": "sprite pieces are relative to the object anchor with the tile offsets in the frame records; the saved frame pointer is used by the renderer",
                  "new_visual_approval_required": False,
                  "statement": "All drawn $24 frames 1-3 and $2E frames 1-4 hash-equal the approved board compositions and the live sprite palette equals the approved CRAM row; frame 0 is empty. The shared `$0F` defeat effect is not an MGHZ-specific composition (tiles $24-$2C). No new PNG approval sheet is required."}
    out["poc_fixture_index"] = fixture_index(out)
    out["poc_checklist"] = poc_checklist()
    out["agents_candidate_updates"] = agents_candidates()
    out["unresolved"] = [
        "No human gameplay recording was available; every statement is ROM-code or original-code-in-harness evidence (the SMS harness is approximate: PSG, exact VDP timing and lag-frame pattern are not modelled).",
        "The exact order in which free slots are consumed when real MGHZ scenes contain many other dynamic objects (rings, monitors, enemies) varies with the scene; the 11-slot pool rule is proven, individual scenes are only sampled.",
        "The shared `$0F` effect's own state table is recorded but its audio command is not interpreted here.",
        "Human-facing names of `$24` and `$2E` are not established.",
    ]
    return out


def fixture_index(out: dict) -> list:
    """Named whole-game fixtures on real placements with their headline numbers (full rows live under object_24 / object_2e)."""
    pair = out["object_24"]["whole_game"]["pair_fixture_mghz1_index26_27"]
    a = pair["stand_beside_A_only"]["A"]["events"]
    lf = out["object_24"]["whole_game"]["lifecycle_mghz1"]
    w1 = out["object_2e"]["whole_game"]["mghz1_walk_in_from_left_rim"]
    w2 = out["object_2e"]["whole_game"]["mghz2_walk_in_from_left_rim"]
    land = out["object_24"]["whole_game"]["landing_all_12_placements"]
    return [
        {"name": "mghz1_pair_26_27_stand_beside_left_piece", "path": "object_24.whole_game.pair_fixture_mghz1_index26_27.stand_beside_A_only",
         "setup": "teleport Sonic to (412, 206) standing, 10 rings, 150 frames", "headline": {"frames": a, "score_after": pair["stand_beside_A_only"]["score_after_150_frames_bcd"], "right_piece_untouched": "trigger_request" not in pair["stand_beside_A_only"]["B"]["events"]}},
        {"name": "mghz1_pair_26_27_stand_beside_right_piece", "path": "object_24.whole_game.pair_fixture_mghz1_index26_27.stand_beside_B_only", "setup": "Sonic at (515, 206)",
         "headline": {"only_right_piece_triggers": "trigger_request" in pair["stand_beside_B_only"]["B"]["events"] and "trigger_request" not in pair["stand_beside_B_only"]["A"]["events"]}},
        {"name": "mghz1_pair_26_27_stand_between", "path": "object_24.whole_game.pair_fixture_mghz1_index26_27.stand_between_both", "setup": "Sonic at (464, 206)",
         "headline": {"both_trigger_same_frame": pair["stand_between_both"]["A"]["events"].get("trigger_request") == pair["stand_between_both"]["B"]["events"].get("trigger_request") is not None, "score_after": pair["stand_between_both"]["score_after_150_frames_bcd"]}},
        {"name": "all_12_landings", "path": "object_24.whole_game.landing_all_12_placements", "setup": "Sonic parked 40 px away on the far side from the fall",
         "headline": {"all_match_controlled_lab": all(x["matches_lab"] for x in land), "falling_updates": 56, "fall_distance_px": 96, "x_shift_px": 28}},
        {"name": "run_through_does_not_trigger", "path": "object_24.whole_game.run_through_and_slow_entry", "setup": "hold RIGHT from x=300 / from x=410 / hold LEFT from 620",
         "headline": {k: v["triggered_at_frame"] for k, v in out["object_24"]["whole_game"]["run_through_and_slow_entry"].items()}},
        {"name": "contact_outcomes", "path": "object_24.whole_game.contact_outcomes", "setup": "fork a falling piece at fall update ~20 and teleport Sonic onto it",
         "headline": {k: [v["hurt_frames"], v["rings_after"], v["state_after"]] for k, v in out["object_24"]["whole_game"]["contact_outcomes"]["variants"].items()}},
        {"name": "lifecycle_leave_and_return", "path": "object_24.whole_game.lifecycle_mghz1", "setup": "teleport away 1500 px and back before trigger / mid-fall / after landing",
         "headline": {"before_trigger_recreated": lf["leave_before_trigger"]["A_recreated"], "mid_fall_recreated_fresh": lf["leave_mid_fall"]["A_recreated"], "after_landing_recreated": lf["leave_after_landing"]["A_recreated_after_backtrack"]}},
        {"name": "mghz1_oil_strip_walk_in_from_left", "path": "object_2e.whole_game.mghz1_walk_in_from_left_rim", "setup": "Sonic from (1250,750) holding RIGHT onto the oil", "headline": {"bursts": w1["spawn_pass_count"], "first_parent_state_2_frame": w1["parent_state_changes"][2][0]}},
        {"name": "mghz2_oil_strip_walk_in_from_left", "path": "object_2e.whole_game.mghz2_walk_in_from_left_rim", "setup": "Sonic from (150,878) holding RIGHT into the pit", "headline": {"bursts": w2["spawn_pass_count"]}},
        {"name": "mghz1_2e_keep_alive_and_fresh_right", "path": "object_2e.whole_game.persistence", "setup": "leave 1400 px / fresh load at the right end of the strip", "headline": out["object_2e"]["whole_game"]["persistence"]["fresh_load_inside_strip_right_end"]["parent_present"]},
    ]


def dumps(value) -> str:
    return json.dumps(value, indent=1) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path, default=OUTPUT)
    p.add_argument("--check", action="store_true")
    p.add_argument("--static-only", action="store_true")
    a = p.parse_args()
    rom = L.load_rom(a.rom)
    text = dumps(build(rom, static_only=a.static_only))
    if a.check:
        if a.output.read_text(encoding="utf-8") != text:
            raise SystemExit("MGHZ object $24/$2E cache differs")
        print("MGHZ object $24/$2E cache matches")
    else:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(text, encoding="utf-8")
        print(f"wrote {a.output} ({len(text)} bytes)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Sonic Chaos shared player spring / airborne state closure (Research only, deterministic).

Reconciles the original player states $09, $0A, $0B, $0E, $14, $1B and $1C (and the springs/bounces that enter them) without
using any English state label as evidence: every row is "state $XX - callback, animation frames, flags".

Output: data/rom-cache/player-spring-airborne.json (numeric labels; region hashes and per-frame hashes only, no ROM bytes, no pixels).
Approval board / per-frame PNGs are written to the git-ignored build/player-spring-airborne/ directory.

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT (original Z80 routines on
tools/oracle.py), EMULATED ORIGINAL FRAME (whole game in tools/sms_frame_harness.py, PC hooks), SYNTHETIC CONTROL (state/cells patched in
RAM, never a canonical placement), POC SOURCE (READ-ONLY), UNRESOLVED.

Usage:
  python tools/player_spring_airborne.py ROM.sms [--check] [--static-only] [--board DIR]
  python tools/player_spring_airborne.py ROM.sms --poc-scan POC_SPRITES_DIR      (prints the read-only POC asset comparison)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import level_package as L                       # noqa: E402
import player_animation_counter as PAC          # noqa: E402  (script_program, CMD_ARGS)
import player_state_11_graphics as G            # noqa: E402  (dynamic_source: runtime tile transfer table)
import sez_surfaces_rig as Z                    # noqa: E402  (ZoneGame: whole-game rig with per-update rows)
import spring_interaction as SI                 # noqa: E402  (Lab: controlled oracle routines, object records)
import thz1_object_assets as A                  # noqa: E402  (mapping/render)
import aqz_foundation as F                      # noqa: E402  (AQZ act metadata)
import thz3_boss_support as T3                  # noqa: E402  (THZ3 boss rig)

OUTPUT = ROOT / "data" / "rom-cache" / "player-spring-airborne.json"
BOARD_DIR = ROOT / "build" / "player-spring-airborne"
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
RESEARCH_BASE = "eb4bf953dcb2f1ad57c629543b55c8536eb688cb"
BANK = 12
STATE_TABLE = 0x8000
PLAYER_TYPE = 1

# states the task names, plus the other consumers of the same frame sets found by the script scan
STATES = (0x09, 0x0A, 0x0B, 0x0E, 0x1B, 0x1C)
COMPARATORS = (0x14, 0x10, 0x12, 0x0F, 0x05)
# callback vectors in the fixed low ROM: JP target
VECTORS = {0x039E: "state $0B", 0x03B6: "state $1C", 0x03AD: "state $0E", 0x03B3: "state $0A", 0x03C5: "state $09",
           0x03C8: "state $1B", 0x03A4: "state $10", 0x03DD: "state $0F", 0x03F8: "state $14", 0x03B0: "state $12", 0x03C2: "state $11"}

# whole-game event hooks (CPU address -> label); events are recorded only while bank 1 is mapped in slot 1 (the engine's normal code)
EVENTS = {0x480C: "sp_up", 0x482D: "sp_diag", 0x4849: "sp_hR", 0x4868: "sp_hL", 0x47FB: "set_1B", 0x463C: "apex", 0x45CE: "land",
          0x6AE3: "brk16", 0x6B2C: "brk0D", 0x48F7: "hurt"}


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def s16(v: int) -> int:
    return (v + 32768) % 65536 - 32768


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def u16(rom: bytes, pos: int) -> int:
    return rom[pos] | (rom[pos + 1] << 8)


def rom_of(bank: int, cpu: int) -> int:
    return cpu if bank == 0 and cpu < 0x4000 else bank * 0x4000 + (cpu & 0x3FFF) if cpu >= 0x8000 else cpu


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM")


# --------------------------------------------------------------------------- #
# 1. state scripts, decoded in full (records, commands, callbacks)
# --------------------------------------------------------------------------- #
def vector_target(rom: bytes, vec: int) -> dict:
    assert rom[vec] == 0xC3, "vector is JP nn"
    return {"vector": h(vec), "jp_target": h(u16(rom, vec + 1)), "owner": VECTORS.get(vec, "unlisted")}


def unroll(rom: bytes, state: int, d448_bit0: int = 0, limit: int = 400) -> list:
    """Play-order expansion of one full cycle of the state script: [(frame, duration, callback_vector)] up to the FF 00 restart.

    Interprets FF 08 (condition = $D448 bit 0 for state $0B), FF 0E / FF 0F (loop counter) and FF 07 (jump); a selector (FF 05) is returned as an
    opaque marker because its frame comes from a table (documented separately)."""
    ptr = u16(rom, rom_of(BANK, STATE_TABLE + 2 * state))
    out, loop, steps = [], 0, 0
    while steps < limit:
        steps += 1
        o = rom_of(BANK, ptr)
        if rom[o] != 0xFF:
            out.append({"frame": rom[o + 1], "duration": rom[o], "callback": h(u16(rom, o + 2))})
            ptr += 4
            continue
        c = rom[o + 1]
        if c == 0x00:
            out.append({"restart": True})
            return out
        if c == 0x05:
            out.append({"selector": h(u16(rom, o + 2)), "callback": h(u16(rom, o + 4))})
            ptr += 6
            continue
        if c == 0x07:
            ptr = u16(rom, o + 2)
            continue
        if c == 0x08:
            ptr = u16(rom, o + 4) if d448_bit0 else ptr + 6
            continue
        if c == 0x0E:
            loop = rom[o + 2]
            ptr += 3
            continue
        if c == 0x0F:
            loop -= 1
            ptr = ptr + 4 if loop == 0 else u16(rom, o + 2)
            continue
        raise ValueError(f"unhandled command FF {c:02X} in state ${state:02X}")
    raise RuntimeError("script did not restart")


def rle(items: list) -> list:
    out: list = []
    for it in items:
        if out and out[-1][0] == it:
            out[-1][1] += 1
        else:
            out.append([it, 1])
    return out


def cadence(seq: list) -> list:
    """[(frame, updates)] run-length of consecutive equal frames (durations summed)."""
    out: list = []
    for r in seq:
        if "frame" not in r:
            continue
        if out and out[-1][0] == r["frame"]:
            out[-1][1] += r["duration"]
        else:
            out.append([r["frame"], r["duration"]])
    return [{"frame": h(f, 2), "updates": n} for f, n in out]


def state_scripts(rom: bytes) -> dict:
    out = {}
    for s in (*STATES, *COMPARATORS):
        prog = PAC.script_program(rom, s)
        vecs = sorted({r["callback"] for r in prog if "callback" in r})
        row = {"script_cpu": h(u16(rom, rom_of(BANK, STATE_TABLE + 2 * s))), "script_file": h(rom_of(BANK, u16(rom, rom_of(BANK, STATE_TABLE + 2 * s))), 5),
               "program": prog, "callback_vectors": [vector_target(rom, int(v, 16)) for v in vecs if int(v, 16) in VECTORS]}
        if s == 0x0B:
            weak, strong = unroll(rom, s, 0), unroll(rom, s, 1)
            row["play_order_d448_bit0_clear"] = {"records": [r for r in weak if "frame" in r],
                                                 "cycle_updates": sum(r["duration"] for r in weak if "frame" in r), "frame_cadence": cadence(weak)}
            row["play_order_d448_bit0_set"] = {"records": [r for r in strong if "frame" in r],
                                               "cycle_updates": sum(r["duration"] for r in strong if "frame" in r), "frame_cadence": cadence(strong)}
        elif any("selector" in r for r in prog):
            row["play_order"] = "selector $8F76: frame from a table, duration from the selector (section selector_frame_tables)"
        else:
            u = unroll(rom, s)
            row["play_order"] = {"records": [r for r in u if "frame" in r], "cycle_updates": sum(r["duration"] for r in u if "frame" in r),
                                 "frame_cadence": cadence(u)}
        out[h(s, 2)] = row
    return out


def frame_consumers(rom: bytes) -> dict:
    """Every real player state script (0..$2F, plus the $30..$37 range reported separately) that references each frame family."""
    fam = {"$0E_fall_set_frames_1_to_6": {1, 2, 3, 4, 5, 6}, "tumble_set_frames_1C_to_21": {0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21},
           "tall_pose_frame_61": {0x61}, "spin_set_frames_25_to_29": {0x25, 0x26, 0x27, 0x28, 0x29}}
    out = {k: [] for k in fam}
    for s in range(0, 0x30):
        prog = PAC.script_program(rom, s)
        frames = set()
        for r in prog:
            if "frame" in r:
                frames.add(r["frame"])
            for f in r.get("fragment_at_target", []):
                if "frame" in f:
                    frames.add(f["frame"])
        for k, v in fam.items():
            if frames & v:
                out[k].append({"state": h(s, 2), "frames_used": [h(x, 2) for x in sorted(frames & v)]})
    # the spin set is also produced by selector $8F76 (states $09/$0A/$10/$1B)
    out["spin_set_frames_25_to_29"].extend({"state": h(s, 2), "frames_used": "via selector $8F76 table $8FB8"} for s in (0x09, 0x0A, 0x10, 0x1B))
    return {"evidence": "DECODED DATA (script scan of states $00..$2F, FF 08 fragments included)", "families": out,
            "note": "states $30 and above are not Sonic player scripts used here: $30 mirrors the fall frames for another object kind; state $14 shares the tumble set with $1C"}


def selector_frame_tables(rom: bytes) -> dict:
    sonic, other = rom[rom_of(BANK, 0x8FB8):rom_of(BANK, 0x8FB8) + 20], rom[rom_of(BANK, 0x8FCC):rom_of(BANK, 0x8FCC) + 20]
    dur = rom[rom_of(BANK, 0x8FE0):rom_of(BANK, 0x8FE0) + 16]
    return {"evidence": "DECODED DATA + BYTE-VERIFIED ASSEMBLY ($8F76)",
            "selector": "$8F76 (FF 05 in states $09, $0A, $10, $1B): $D52F += 1, wraps to 0 at 20; frame := table[$D52F]; +$06 := frame; "
                        "duration +$07 := $8FE0[|X speed hi|] when the floor flag (+$22 bit 1) is set, else 3; sets facing from the X speed sign when on the floor",
            "frame_table_object_type_1": [h(x, 2) for x in sonic], "frame_table_other_object_types": [h(x, 2) for x in other],
            "floor_duration_table_8FE0": list(dur), "air_duration": 3, "sonic_frame_ids": sorted(h(x, 2) for x in set(sonic))}


# --------------------------------------------------------------------------- #
# 2. frames: mapping, tile transfer, mirroring (hashes only; PNGs go to build/)
# --------------------------------------------------------------------------- #
FRAME_GROUPS = (
    ("fall_cycle_state_0E", (2, 3, 4, 5, 6, 1), "state $0E records (8 updates each, order 2,3,4,5,6,1)"),
    ("tumble_set_state_0B_weak_1C_14", (0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21), "state $0B ($D448 bit 0 clear, 4 updates each), $1C (8 updates each), $14 (4 updates each)"),
    ("tall_pose_state_0B_strong", (0x61,), "state $0B ($D448 bit 0 set), one record of 4 updates repeated"),
    ("spin_set_states_09_0A_10_1B", (0x25, 0x26, 0x27, 0x28, 0x29), "selector $8F76 frames (context: states $09/$0A/$10/$1B, not newly missing)"),
)
SPRITE_PALETTES = {"thz1": 0x06, "aqz1": None, "aqz2": None, "aqz3": None}


def palette_selectors(rom: bytes) -> dict:
    out = {}
    for name, zone, act in (("thz1", 0, 0), ("aqz1", 4, 0), ("aqz2", 4, 1), ("aqz3", 4, 2)):
        pos = 0x7F3C + 2 * (zone * 3 + act)
        out[name] = {"selector_rom": h(pos, 5), "background": h(rom[pos], 2), "sprite": h(rom[pos + 1], 2),
                     "sprite_palette_rom": h(A.PALETTE_DATA_ROM + rom[pos + 1] * 16, 5)}
    return out


def render_frame_rgba(rom: bytes, frame_id: int, palette) -> tuple:
    mapping = A.object_mapping(rom, PLAYER_TYPE)
    ptrs = A.mapping_frame_pointers(rom, mapping["mapping_cpu"], 128)
    parsed = A.parse_frame_record(rom, ptrs[frame_id])
    source = G.dynamic_source(rom, frame_id)
    vram = bytearray(0x4000)
    vram[:len(source["raw"])] = source["raw"]
    width, height, rgba, meta = A.render_frame(vram, parsed, 0, scale=1, margin=0, palette=palette)
    return parsed, source, width, height, rgba, meta, ptrs[frame_id], mapping


def frame_table(rom: bytes, output: Path | None = None) -> dict:
    sel = palette_selectors(rom)
    palette = A.palette_rgba(rom, int(sel["thz1"]["sprite"], 16))
    frames, pngs = {}, []
    for group, ids, usage in FRAME_GROUPS:
        for fid in ids:
            parsed, source, w, hgt, rgba, meta, cpu, mapping = render_frame_rgba(rom, fid, palette)
            frames[h(fid, 2)] = {
                "group": group, "state_usage": usage,
                "mapping_table_cpu": h(mapping["mapping_cpu"]), "mapping_table_rom": h(mapping["mapping_rom"], 5),
                "mapping_pointer_entry_rom": h(mapping["mapping_rom"] + fid * 2, 5), "mapping_frame_cpu": h(cpu), "mapping_frame_rom": h(parsed["frame_rom"], 5),
                "mapping_record": A.serialise_frame(parsed),
                "graphics_transfer": {k: v for k, v in source.items() if k != "raw"},
                "bounds": meta["bounds"], "canvas_width": w, "canvas_height": hgt,
                "gamemaker_origin_x": -meta["bounds"]["min_x"], "gamemaker_origin_y": -meta["bounds"]["min_y"],
                "tile_bytes_sha256": source["tile_bytes_sha256"], "rgba_sha256_thz1_palette": sha(rgba),
                "non_transparent_pixels": meta["nonzero_source_pixels"],
            }
            pngs.append((fid, w, hgt, rgba))
    out = {"evidence": "DECODED DATA + deterministic reconstruction (bank-$0F mapping table, interrupt-side player tile loader table at $104B)",
           "object_type": "0x01", "tile_base": "0x00", "renderer": {
               "animation_mapping_resolver_cpu": "0x64FA", "sat_y_cpu": "0x226A", "sat_x_tile_cpu": "0x22B6", "dynamic_tile_loader_cpu": "0x0D15",
               "change_detector_cpu": "0x1027", "tile_table_rom": "0x0104B (4 bytes per frame: bank, source CPU, 64-byte block count)",
               "horizontal_mirroring": "object +$04 bit 4 mirrors the piece X positions; LoadPlayerTiles bit-reverses the tile bytes through the ROM table at $0100 "
                                       "into the same VRAM destination; an ordinary horizontal flip of the right-facing image is equivalent (no second extracted set)",
               "piece_geometry": "SMS 8x16 sprite mode, consecutive tile pair per piece; palette index 0 transparent"},
           "palettes": sel, "frames": frames}
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        for fid, w, hgt, rgba in pngs:
            A.write_rgba_png(output / f"frame-{fid:02X}.png", w, hgt, rgba)
    return out


# --------------------------------------------------------------------------- #
# 3. movement: gravity, input tables, wrappers, setters (source-traced + controlled)
# --------------------------------------------------------------------------- #
REGIONS = [
    ("wrapper_0B_393B", 0x393B, 0x3955, "state $0B callback: shared movement $3FEF; requested still $0B? floor flag +$23 bit 1 -> landing $45CE; Y speed high byte >= 0 -> apex request $463C; else facing $48A7"),
    ("wrapper_1C_3955", 0x3955, 0x396D, "state $1C callback: shared movement; requested still $1C? floor flag -> $45CE; Y speed high byte >= 0 -> $463C; no facing update"),
    ("wrapper_0E_3A37", 0x3A37, 0x3A48, "state $0E callback: shared movement; requested still $0E? floor flag +$23 bit 1 -> $45CE; no apex test, no facing update"),
    ("wrapper_0A_3901", 0x3901, 0x393B, "state $0A callback: jump-hold counter $D3B2 (held jump re-pins Y speed to -4.25 / -3.25 water for 13 updates), shared movement, landing unless $D36C = $0D"),
    ("wrapper_09_38C5", 0x38C5, 0x38D1, "state $09 callback: shared movement; requested still 9 -> rolling update $37F4"),
    ("wrapper_1B_38D1", 0x38D1, 0x3901, "state $1B callback: shared movement; requested still $1B and floor flag: clear airborne bit; jump -> $45ED; else near-zero speed -> $45B3"),
    ("setter_fall_463C", 0x463C, 0x4663, "request $0E, Y speed +1.0, airborne SET, attack posture CLEAR (+$03 bit 1), strip marker +$24 bit 0 cleared, $D3BC := 0, floor flag cleared; returns at once when the current state is $0A"),
    ("landing_45CE", 0x45CE, 0x45ED, "airborne/attack/+$03 bit 6 cleared, request state 5, speed cap $D373 := $0400, facing $48A7, $D289 := $60"),
    ("setter_upright_480C", 0x480C, 0x482D, "$480C: Y speed high byte negative -> RET; else request $0B, vy := HL, airborne SET, attack posture CLEAR, floor flag cleared, sound $A6 (written by the caller path)"),
    ("setter_diagonal_482D", 0x482D, 0x4849, "$482D: same Y-speed gate; request $1C, vy := HL, airborne SET, attack posture SET, floor flag cleared"),
    ("setter_horizontal_4849_4868", 0x4849, 0x4892, "$4849/$4868: request 9, vx := +/-HL, cap $D373 := |HL|, airborne CLEAR, attack posture SET, floor flag cleared, sound $A6; no Y-speed gate, Y speed untouched"),
    ("setter_1B_47FB", 0x47FB, 0x480C, "$47FB: request $1B, airborne SET, attack posture SET, floor flag cleared (ceiling springs, ramp launch)"),
    ("ceiling_spring_748F_749D", 0x748F, 0x74E7, "type-$15 ceiling bounce ($748F: vy +7.5) and blocks $3A/$3B ceiling spring ($749D: vx +4.0, vy +5.5, player pushed out of the block)"),
    ("terrain_pass_order_690B", 0x690B, 0x691A, "terrain pass: floor $691A, sides $715E, ceiling pass $73C9, terrain-ring / special probe $753E, merge $64CB"),
    ("ceiling_pass_73C9", 0x73C9, 0x7440, "ceiling pass: returns unless (D3C0 != 0) or (floor flag clear AND Y speed negative); dispatches type $14 to $749D"),
    ("ring_probe_753E", 0x753E, 0x756F, "terrain-ring / special probe: probe point from +$07 parity; type 7 ring, $1D -> $760C, $1A -> $7646, EVERYTHING ELSE tails into $749D (the CP $14 at $7569 is not a branch)"),
    ("facing_48A7", 0x48A7, 0x48BC, "facing: Left held -> +$04 bit 4 set, Right held -> clear, neither -> unchanged"),
    ("vertical_integrator_4097", 0x4097, 0x4141, "Y speed integrator: airborne states add +$18 ($0B), +$24 ($1B), +$30 (others) dry / $0C,$12,$18 water; downward cap +$0700 / water +$0400; floor flag forces $0700 (or $0900 on modifier $0A/$0C)"),
    ("spring_terrain_upright_6A75", 0x6A75, 0x6A90, "terrain type 9: current state $11 rejects, floor flag +$22 bit 1 required, Y speed non-negative required; $D448 := $FF; $480C with HL $F880"),
    ("spring_terrain_diagonal_6A90", 0x6A90, 0x6ACE, "terrain type $14: same gates; vx +/-4.0 and facing, vy $F900 (THZ) / $FA80; $D448 := 0; $482D"),
    ("breakable_6AE3", 0x6AE3, 0x6B14, "type $16 breakable + bounce"), ("breakable_6B2C", 0x6B2C, 0x6B56, "type $0D breakable + bounce"),
]


def region_table(rom: bytes) -> list:
    out = []
    for name, a, b, purpose in REGIONS:
        out.append({"name": name, "cpu": h(a), "end_cpu_exclusive": h(b), "rom_offset": h(a, 5), "length": b - a, "sha256": sha(rom[a:b]), "purpose": purpose})
    return out


def movement_tables(rom: bytes) -> dict:
    import csv
    rows = {}
    with (ROOT / "data" / "movement-tables.csv").open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            st = int(r["state_hex"], 16)
            if st in (*STATES, 0x14):
                rows.setdefault(h(st, 2), {})[r["table"]] = {"first_8_8": int(r["first_8_8"]), "second_8_8": int(r["second_8_8"]), "file_offset": "0x" + r["file_offset"]}
    return {"evidence": "DECODED DATA (data/movement-tables.csv, selected by $4141) + EMULATED fixtures (free_flight)",
            "reading": "pair = (Left-input increment, Right-input increment) in signed 8.8; the table is chosen by the sign of X speed (dry_nonnegative / dry_negative) "
                       "when a direction is held and by no_direction (positive speed, negative speed) when neither is held; water_* replace the dry rows underwater; "
                       "increments near zero speed are doubled; not_selected_by_4141 is data the engine never reads",
            "states": rows}


# --------------------------------------------------------------------------- #
# 4. emulated rig
# --------------------------------------------------------------------------- #
class Rig(Z.ZoneGame):
    """ZoneGame whose engine hooks only fire while the normal engine bank is mapped in slot 1, and whose rows carry the animation fields."""

    def _event(self, name):
        base = super()._event(name)

        def fn(mm):
            if mm.slot[1] != 1:
                return
            base(mm)
            if name.startswith("sp_"):
                self.pending[-1] = f"{name}(HL={mm.cpu.hl:04X})"
        return fn

    def row(self) -> dict:
        r = super().row()
        m = self.m
        r.update(fr=m[0xD506], ctr=m[0xD507], d448=m[0xD448], face=(m[0xD504] >> 4) & 1, fl=(m[0xD522] >> 1) & 1)
        return r


COLUMNS = ["u", "cur", "req", "f3", "frame", "ctr", "x", "y", "vx", "vy", "d448", "face", "floor", "events"]


def pack(rows: list) -> list:
    out = []
    for r in rows:
        out.append([r["u"], r["cur"], r["req"], r["hurtf"], r["fr"], r["ctr"], r["x"] if r["x"] < 32768 else r["x"] - 65536,
                    r["y"] if r["y"] < 32768 else r["y"] - 65536, s16(r["vx"]), s16(r["vy"]), r["d448"], r["face"], r["fl"], list(r["ev"])])
    return out


def segments(packed: list) -> list:
    """State segments: consecutive updates whose EXECUTING state ($D501 after the engine) is the same. d503_values lists the flag values seen
    (the entry update shows the new flags while the old state still executes, see request_changes)."""
    out, prev = [], None
    for p in packed:
        u, cur, req, f3, fr, ctr, x, y, vx, vy, d448, face, fl, ev = p
        if cur != prev:
            out.append({"first_update": u, "state": h(cur, 2), "updates": 0, "d503_values": [], "frames": [], "enter": {"x": x, "y": y, "vx": vx, "vy": vy, "d448": h(d448, 2)}})
            prev = cur
        seg = out[-1]
        seg["updates"] += 1
        if f3 not in seg["d503_values"]:
            seg["d503_values"].append(f3)
        if seg["frames"] and seg["frames"][-1][0] == fr:
            seg["frames"][-1][1] += 1
        else:
            seg["frames"].append([fr, 1])
        seg["exit"] = {"x": x, "y": y, "vx": vx, "vy": vy}
    for seg in out:
        seg["frames"] = [{"frame": h(f, 2), "updates": n} for f, n in seg["frames"]]
    return out


def events_of(packed: list) -> list:
    out = []
    for p in packed:
        u, cur, req, f3, fr, ctr, x, y, vx, vy, d448, face, fl, ev = p
        for e in ev:
            out.append({"update": u, "event": e, "state_executing": h(cur, 2), "requested_after": h(req, 2), "d503_after": f3, "x": x, "y": y, "vx": vx, "vy": vy})
    return out


def launches(packed: list) -> list:
    """Updates at which the requested state changes to a spring/bounce state, with the executing state, to show replacement of a pending request."""
    out = []
    for i in range(1, len(packed)):
        a, b = packed[i - 1], packed[i]
        if b[2] != a[2] or (b[2] in (0x0B, 0x1B, 0x1C, 9) and b[13]):
            pass
        if b[2] != b[1] and b[2] != a[2]:
            out.append({"update": b[0], "executing_state": h(b[1], 2), "requested_before": h(a[2], 2), "requested_after": h(b[2], 2),
                        "events": b[13], "vy_before": a[9], "vy_after": b[9]})
    return out


def scenario(g: Rig, sid: str, mechanism: str, setup: dict, begin: dict, updates: int, pad=None, extra: dict | None = None) -> dict:
    g.begin(**begin)
    rows = g.run(updates, padf=pad or (lambda u, f: 0))
    packed = pack(rows)
    row = {"id": sid, "mechanism": mechanism, "setup": setup, "updates": len(packed), "columns": COLUMNS, "rows": packed,
           "state_segments": segments(packed), "events": events_of(packed), "request_changes": launches(packed)}
    if extra:
        row.update(extra)
    return row


def clear_cells(x0: int, x1: int, y0: int, y1: int) -> dict:
    return {(cx, cy): 0 for cx in range(x0 // 32, x1 // 32 + 1) for cy in range(y0 // 32, y1 // 32 + 1)}


def rig(rom: bytes, zone: int, act: int) -> Rig:
    return Rig(rom, zone, act, hooks=EVENTS)


def flights_thz(rom: bytes) -> dict:
    """Free-flight arcs (cells above cleared: SYNTHETIC CONTROL of the ceiling only) for every upright/diagonal/horizontal launch source."""
    g = rig(rom, 0, 0)
    sc = []
    cases = [
        ("t26_weak_fixed", "mapped type $26 fixed, parameter nonzero (THZ1 (1912,864))", dict(x=1912, y=846, vy=0x0100), (1912 - 64, 1912 + 64, 0, 832)),
        ("t26_strong_fixed", "mapped type $26 fixed, parameter 0 (THZ1 (688,864))", dict(x=688, y=846, vy=0x0100), (688 - 64, 688 + 64, 0, 832)),
        ("t26_span_weak", "mapped type $26 span parameter $8A, aux1 $72 (THZ1 (1296,608))", dict(x=1300, y=590, vy=0x0100), (1296, 1456 + 64, 0, 576)),
        ("terrain_upright", "terrain type 9 block $30 (THZ1 (928,640))", dict(x=944, y=596, vy=0x0100), (928 - 64, 928 + 96, 0, 608)),
        ("terrain_diag_right", "terrain type $14 block $36, THZ vy -7.0 (THZ1 (2464,256))", dict(x=2470, y=222, vy=0x0100), (2464 - 64, 2464 + 320, 0, 224)),
        ("terrain_diag_left", "terrain type $14 block $38, THZ vy -7.0 (THZ1 (1664,512))", dict(x=1688, y=478, vy=0x0100), (1664 - 320, 1664 + 64, 0, 480)),
    ]
    for sid, mech, st, (x0, x1, y0, y1) in cases:
        patch = clear_cells(x0, x1, y0, y1)
        sc.append(scenario(g, sid, mech, {"zone": 0, "act": 0, "start": [st["x"], st["y"]], "start_state": "0x0E", "start_vy": st["vy"], "cells_cleared_above": [x0, x1, y0, y1]},
                           dict(x=st["x"], y=st["y"], vy=st["vy"], cur=0x0E, f3=1, floor=False, width=128, patch=patch), 230 if "strong" in sid or "upright" in sid else 150))
    # horizontal spring, run left into the open side
    sc.append(scenario(g, "terrain_horizontal_run_left", "terrain type 10 block $33 (THZ1 (3200,832)), Left held", {"zone": 0, "act": 0, "start": [3262, 790], "pad": "LEFT"},
                       dict(x=3262, y=790, vy=0x0100, cur=0x0E, f3=1, floor=False, width=128), 80, pad=lambda u, f: 4))
    # jump -> spring
    sc.append(scenario(g, "jump_lands_on_terrain_upright", "normal jump ($0A) landing on terrain type 9 block $30 (THZ1 (928,640))",
                       {"zone": 0, "act": 0, "start": [600, 600], "pad": "RIGHT, B1 at update 60"},
                       dict(x=600, y=600, vy=0x0100, cur=1, f3=0, floor=True, width=128), 170, pad=lambda u, f: 8 | (16 if 60 <= f < 61 else 0)))
    return {"evidence": "EMULATED ORIGINAL FRAME (whole game, THZ1 booted, Sonic teleported; row u = state AFTER player update u)", "scenarios": sc}


def apex_ordering(rom: bytes) -> dict:
    """Synthetic control: is the apex transition or a spring launch decided first when both are due in the same update?

    Sonic is placed in state $0B / $1C one update before the apex (gravity brings Y speed to exactly 0) with the foot probe inside the 16-px top of a spring cell
    patched into open air (AQZ3, previous-surface flags = the spring block's own flags, as when the cell is entered from above)."""
    g = rig(rom, 4, 2)
    width = 80
    base_clear = clear_cells(6 * 32, 29 * 32, 0, 13 * 32)
    out = []
    for sid, cur, f3, vy, block, cx, probe_x, label in (
            ("0B_apex_update_on_upright_spring", 0x0B, 1, -24, 0x30, 14, 14 * 32 + 16, "state $0B at vy -24 (apex next update) over upright block $30"),
            ("1C_apex_update_on_diagonal_spring", 0x1C, 3, -48, 0x36, 14, 14 * 32 + 8, "state $1C at vy -48 (apex next update) over right-diagonal block $36 spring half"),
            ("0B_apex_update_control_no_spring", 0x0B, 1, -24, 0x00, 14, 14 * 32 + 16, "state $0B at vy -24, open air (control)")):
        cy = 7
        patch = dict(base_clear)
        patch[(cx, cy)] = block
        flags = {0x30: 0x49, 0x36: 0x49}.get(block, 0x00)
        g.begin(x=probe_x, y=cy * 32, vx=0, vy=vy & 0xFFFF, cur=cur, f3=f3, floor=False, prev=flags, width=width, patch=patch)
        rows = g.run(8, padf=lambda u, f: 0)
        out.append({"id": sid, "setup": label, "block": h(block, 2), "columns": COLUMNS, "rows": pack(rows)})
    return {"evidence": "EMULATED ORIGINAL FRAME + SYNTHETIC CONTROL (cells patched in RAM; never a canonical placement)", "scenarios": out}


def stomp_and_boss(rom: bytes) -> dict:
    """$21 top stomp and $50 (THZ3 boss) top bounce: end-to-end emulated rows; D448 is preset to the opposite value to show the explicit store."""
    out = []
    g = Rig(rom, 0, 0, hooks={**EVENTS, 0x5F17: "vec5F17"})
    recs = [r for r in SI.objects("thz1") if r["type_id"] == "0x21"]
    r0 = recs[0]
    ex, ey = r0["world_x"], r0["world_y"]
    out.append(scenario(g, "type21_top_stomp", "type $21 enemy top contact (THZ1 (800,606)), vector $035F -> $480C",
                        {"zone": 0, "act": 0, "enemy": [ex, ey], "start": [ex, ey - 48], "start_state": "0x0A", "start_f3": 3, "start_vy": 0x0300, "d448_preset": "0x00"},
                        dict(x=ex, y=ey - 48, vy=0x0300, cur=0x0A, f3=3, floor=False, width=128), 110))
    # THZ3 boss top bounce (type $50): reuse the accepted boss rig, preset D448 = $FF so the explicit store of 0 is visible
    t = T3.Thz3(rom)
    s, m, u = t.s, t.m, t.u
    init = {"at": None}

    def driver(n):
        b = t.boss()
        if not b:
            return
        if init["at"] is None and m[b + 1] in (3, 18):
            s.w16(0xD511, 1696), s.w16(0xD514, 238), s.w16(0xD516, 0), s.w16(0xD518, 0)
        if init["at"] is None and m[b + 1] == 6:
            init["at"] = n
            s.w16(0xD511, u(b + 0x11)), s.w16(0xD514, u(b + 0x14) - 47), s.w16(0xD516, 0), s.w16(0xD518, 256)
            m[0xD503], m[0xD502], m[0xD448] = 3, 10, 0xFF

    def sample():
        r = t.sample_boss()
        r.update(vy=T3.s16(u(0xD518)), f3=m[0xD503], cur=m[0xD501], req=m[0xD502], fr=m[0xD506], ctr=m[0xD507], d448=m[0xD448], y=T3.s16(u(0xD514)), x=u(0xD511),
                 vx=T3.s16(u(0xD516)), face=(m[0xD504] >> 4) & 1, fl=(m[0xD522] >> 1) & 1)
        return r
    rows = t.al.run(driver, sample, 330, pad=lambda n: 8 if n < 75 else 0, restore=False)
    at = init["at"]
    pk = [[i, r["cur"], r["req"], r["f3"], r["fr"], r["ctr"], r["x"], r["y"], r["vx"], r["vy"], r["d448"], r["face"], r["fl"], []] for i, r in enumerate(rows[at:at + 160], 1)]
    out.append({"id": "type50_boss_top_bounce", "mechanism": "type $50 (THZ3 boss) non-rising top contact, helper -> $035F -> $480C with HL $FC00",
                "setup": {"zone": 0, "act": 2, "harness": "tools/thz3_boss_support.py Thz3 (accepted boss rig)", "start_state": "0x0A", "start_f3": 3, "start_vy": 256, "d448_preset": "0xFF"},
                "updates": len(pk), "columns": COLUMNS, "rows": pk, "state_segments": segments(pk), "events": [], "request_changes": launches(pk)})
    return {"evidence": "EMULATED ORIGINAL FRAME", "scenarios": out}


def aqz_chains(rom: bytes) -> dict:
    sc = []
    g3 = rig(rom, 4, 2)
    meta3 = F.ACTS["aqz3"]
    sc.append(scenario(g3, "aqz3_natural_run", "AQZ3 from the natural start (110,238), Right held, no jump: the whole spring corridor, in order",
                       {"zone": 4, "act": 2, "start": [110, 238], "pad": "RIGHT held throughout"},
                       dict(x=110, y=238, cur=1, f3=0, floor=True, width=80), 480, pad=lambda u, f: 8))
    sc.append(scenario(g3, "aqz3_diag_ceiling_chain", "AQZ3 right-diagonal $37 cells at (480,352) onward, started by a fall onto the first spring",
                       {"zone": 4, "act": 2, "start": [488, 350], "start_state": "0x0E"},
                       dict(x=488, y=350, vy=0x0100, cur=0x0E, f3=1, floor=False, width=80), 260))
    sc.append(scenario(g3, "aqz3_left_diag_horizontal_ceiling", "AQZ3 left-diagonal $39 at (1056,288): diagonal -> horizontal spring mid-flight -> landing -> diagonal -> ceiling spring",
                       {"zone": 4, "act": 2, "start": [1072, 286], "start_state": "0x0E"},
                       dict(x=1072, y=286, vy=0x0100, cur=0x0E, f3=1, floor=False, width=80), 150))
    g2 = rig(rom, 4, 1)
    sc.append(scenario(g2, "aqz2_diagonal_shaft", "AQZ2 left-diagonal $39 at (3104,896) with the right-diagonal $37 column at x 2976: zig-zag shaft",
                       {"zone": 4, "act": 1, "start": [3120, 894], "start_state": "0x0E"},
                       dict(x=3120, y=894, vy=0x0100, cur=0x0E, f3=1, floor=False, width=128), 230))
    return {"evidence": "EMULATED ORIGINAL FRAME (AQZ whole game; hooks only count while bank 1 is mapped in slot 1)", "scenarios": sc}


def free_flight(rom: bytes) -> dict:
    """Per-state gravity, horizontal control and facing in open air (AQZ3 cells cleared). One fixture per (state, start vx, input)."""
    g = rig(rom, 4, 2)
    patch = clear_cells(6 * 32, 29 * 32, 0, 13 * 32)
    cases = ((0x0B, 1, -1280), (0x0E, 1, 256), (0x1C, 3, -1408), (0x1B, 3, 1408), (0x0A, 3, -640))
    out = []
    for cur, f3, vy in cases:
        for vx, face in ((0, 0), (512, 0), (-512, 0), (0, 1)):
            for pname, pad in (("none", 0), ("right", 8), ("left", 4)):
                g.begin(x=400, y=150, vx=vx & 0xFFFF, vy=vy & 0xFFFF, cur=cur, f3=f3, floor=False, width=80, patch=patch, face=face,
                        apply=lambda gg: gg.m.__setitem__(0xD448, 0))
                rows = g.run(14, padf=lambda u, f, p=pad: p)
                pk = pack(rows)
                out.append({"state": h(cur, 2), "start_vx": vx, "start_vy": vy, "start_facing": face, "input": pname, "vx": [p[8] for p in pk], "vy": [p[9] for p in pk],
                            "facing": [p[11] for p in pk], "state_seq": sorted({h(p[1], 2) for p in pk}), "d503_seq": sorted({p[3] for p in pk})})
    return {"evidence": "EMULATED ORIGINAL FRAME in open air (SYNTHETIC CONTROL: AQZ3 cells x 192..928 / y 0..416 cleared)",
            "note": "row 0..13 = state after updates 1..14; input is applied by the harness from the first frame, the engine samples it one update later",
            "fixtures": out}


# --------------------------------------------------------------------------- #
# 5. controlled routine sweeps (Oracle, empty layout)
# --------------------------------------------------------------------------- #
def lab_empty(rom: bytes):
    lab = SI.Lab(rom)
    lab.m[0xC001:0xD000] = bytes(0xFFF)
    return lab


def run_wrapper(lab, addr: int, cur: int, f3: int, vy: int, vx: int = 0, floor: int = 0, d3b2: int = 0x20, held: int = 0) -> dict:
    lab.player(1000, 400, vx=vx & 0xFFFF, vy=vy & 0xFFFF, floor=floor, cur=cur, req=cur, f3=f3)
    lab.m[0xD501] = cur
    lab.m[0xD3B2] = d3b2
    lab.m[0xD137] = held
    lab.call_ix(addr)
    s = lab.snap()
    return {"req": h(s["req"], 2), "d503": s["f3"], "vy": s16(s["vy"]), "vx": s16(s["vx"]), "cap": h(s["cap"])}


def wrapper_sweeps(rom: bytes) -> dict:
    lab = lab_empty(rom)
    out = {}
    # apex condition: Y speed (signed) before the update; gravity is added by the shared movement first
    rows = {}
    for name, addr, cur, f3, grav in (("$0B", 0x393B, 0x0B, 1, 24), ("$1C", 0x3955, 0x1C, 3, 48)):
        sweep = []
        for vy in list(range(-grav - 24, grav + 25, 1)) + [255, 256, 1000]:
            r = run_wrapper(lab, addr, cur, f3, vy)
            sweep.append([vy, r["req"], r["d503"], r["vy"]])
        first = next(v for v, req, f, y in sweep if req == "0x0E")
        rows[name] = {"gravity_per_update_8_8": grav, "first_start_vy_that_requests_0E": first,
                      "rule": "request $0E iff the Y speed HIGH BYTE is non-negative after gravity, i.e. start vy >= -gravity (vy after gravity >= 0)",
                      "at_apex": {"request": "0x0E", "vy_set": 256, "d503_after": "airborne bit SET, attack bit CLEAR"},
                      "sample": [x for x in sweep if x[0] in (-grav - 1, -grav, -grav + 1, -1, 0, 1)]}
    out["apex_wrapper"] = rows
    # $0E has no apex test
    out["wrapper_0E_has_no_apex_test"] = [[vy, run_wrapper(lab, 0x3A37, 0x0E, 1, vy)["req"]] for vy in (-2000, -48, -24, -1, 0, 24)]
    # setters reached by the transitions, called directly with the natural flag value of each source state
    setters = {}
    for name, addr, cur, f3 in (("$463C_apex_or_fall", 0x463C, 0x0B, 1), ("$463C_from_$1C", 0x463C, 0x1C, 3), ("$463C_from_$0A_returns_at_once", 0x463C, 0x0A, 3),
                                ("$45CE_landing_from_$0B", 0x45CE, 0x0B, 1), ("$45CE_landing_from_$1C", 0x45CE, 0x1C, 3), ("$45CE_landing_from_$1B", 0x45CE, 0x1B, 3),
                                ("$45CE_landing_from_$0A", 0x45CE, 0x0A, 3), ("$45CE_landing_from_$0E", 0x45CE, 0x0E, 1)):
        lab.player(1000, 400, vx=0, vy=0x0200, floor=0, cur=cur, req=cur, f3=f3)
        lab.m[0xD501] = cur
        lab.m[0xD373], lab.m[0xD374] = 0x00, 0x07
        lab.call_ix(addr)
        s = lab.snap()
        setters[name] = {"request": h(s["req"], 2), "d503_after": s["f3"], "vy_after": s16(s["vy"]), "speed_cap": h(s["cap"])}
    out["setters_called_directly"] = {"evidence": "CONTROLLED ROUTINE RESULT", "rows": setters,
                                      "rule": "$463C: request $0E, vy +1.0, airborne SET, attack CLEAR (and no change when the current state is $0A); $45CE: request state 5, airborne/attack/+$03 bit 6 cleared, speed cap $0400"}
    return out


def spring_gate_matrix(rom: bytes) -> dict:
    """Which of the six states a given spring request can replace: rows = (current state executing, requested state pending)."""
    lab = lab_empty(rom)
    rows = []
    for cur in (0x09, 0x0A, 0x0B, 0x0E, 0x1B, 0x1C, 0x14):
        f3 = {0x09: 2, 0x0A: 3, 0x0B: 1, 0x0E: 1, 0x1B: 3, 0x1C: 3, 0x14: 1}[cur]
        for label, addr, kw in (("terrain_upright_$6A75", 0x6A75, dict(floor=1, vy=0x0100)), ("terrain_upright_$6A75_no_floor", 0x6A75, dict(floor=0, vy=0x0100)),
                                ("terrain_upright_$6A75_rising", 0x6A75, dict(floor=1, vy=-0x0100)), ("terrain_diag_$6A90", 0x6A90, dict(floor=1, vy=0x0100)),
                                ("terrain_diag_$6A90_no_floor", 0x6A90, dict(floor=0, vy=0x0100)),
                                ("terrain_diag_$6A90_rising", 0x6A90, dict(floor=1, vy=-0x0100))):
            lab.player(1000, 400, vx=0, vy=kw["vy"] & 0xFFFF, floor=kw["floor"], cur=cur, req=cur, f3=f3)
            lab.m[0xD501] = cur
            lab.m[0xD36B] = 0x30 if addr == 0x6A75 else 0x36
            lab.call_ix(addr)
            s = lab.snap()
            rows.append({"executing_state": h(cur, 2), "gate": label, "request_after": h(s["req"], 2), "fired": s16(s["vy"]) == (-1920 if addr == 0x6A75 else -1792), "d503_after": s["f3"], "vy_after": s16(s["vy"])})
    return {"evidence": "CONTROLLED ROUTINE RESULT (original handlers $6A75/$6A90 called directly)", "rows": rows,
            "rule": "the six states are all accepted as 'current state' (only $11 rejects); what blocks a spring is the floor flag and a non-negative Y speed, both of which a rising $0B/$1C player lacks"}


def breakable_matrix(rom: bytes) -> dict:
    lab = lab_empty(rom)
    rows = []
    for cur, f3 in ((0x09, 2), (0x0A, 3), (0x0B, 1), (0x0E, 1), (0x1B, 3), (0x1C, 3), (0x14, 1)):
        for name, addr in (("type_0D_$6B2C", 0x6B2C), ("type_16_$6AE3", 0x6AE3)):
            lab.player(1000, 700, vy=0x0100, floor=0, cur=cur, req=cur, f3=f3)
            lab.m[0xD501] = cur
            lab.m[0xD522] = 0x04
            lab.m[0xD36B] = 0x47
            lab.o.word(0xD354, 0xC001)
            lab.o.word(0xD358, 1000)
            lab.o.word(0xD35A, 718)
            lab.call_ix(addr)
            s = lab.snap()
            rows.append({"state": h(cur, 2), "d503_natural": f3, "handler": name, "breaks_and_bounces": s16(s["vy"]) == -1088, "vy_after": s16(s["vy"])})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "rows": rows,
            "rule": "breakable block handlers require the attack posture (+$03 bit 1) and a current state outside $0F/$10/$15/$1A; upright-spring ($0B) and fall ($0E) flights never break them, "
                    "diagonal ($1C), ceiling/ramp ($1B), jump ($0A) and horizontal-spring/roll ($09) do"}


def attack_by_state() -> dict:
    return {"evidence": "SOURCE-TRACED (docs/player-attack-badnik-audit.md: badnik callbacks read $D503 bit 1, or $D532 == 6) + EMULATED flags in the traces",
            "rows": [
                {"state": "0x09", "d503_natural": 2, "attack_bit1": True}, {"state": "0x0A", "d503_natural": 3, "attack_bit1": True},
                {"state": "0x0B", "d503_natural": 1, "attack_bit1": False}, {"state": "0x0E", "d503_natural": 1, "attack_bit1": False},
                {"state": "0x1B", "d503_natural": 3, "attack_bit1": True}, {"state": "0x1C", "d503_natural": 3, "attack_bit1": True},
            ]}


def jump_hold(rom: bytes) -> dict:
    """State $0A wrapper $3901: the held-jump counter $D3B2 re-pins Y speed to -4.25 (-3.25 underwater) while it stays below 14."""
    lab = lab_empty(rom)
    rows = []
    for water in (0, 1):
        for held in (0x00, 0x10, 0x20):
            for ctr in (0, 1, 11, 12, 13, 14, 0x20):
                lab.player(1000, 400, vx=0, vy=0xFF00, floor=0, cur=0x0A, req=0x0A, f3=3)
                lab.m[0xD501], lab.m[0xD3B2], lab.m[0xD137], lab.m[0xD443] = 0x0A, ctr, held, water
                lab.call_ix(0x3901)
                s = lab.snap()
                rows.append({"water": water, "buttons_d137": held, "counter_before": ctr, "counter_after": lab.m[0xD3B2], "vy_before": -256, "vy_after": s16(s["vy"])})
    return {"evidence": "CONTROLLED ROUTINE RESULT ($3901 called directly)", "rows": rows,
            "rule": "no jump button ($D137 bits 4/5 clear): counter := $20 and gravity only; button held: counter += 1 and, while counter < 14, vy := $FBC0 (dry) / $FCC0 (water) before the shared movement (+$30 gravity then applies)"}


def free_flight_water_and_cap(rom: bytes) -> dict:
    """Water gravity and the horizontal speed cap in open air (AQZ3 cells cleared; water flag $D443 written by the fixture)."""
    g = rig(rom, 4, 2)
    patch = clear_cells(6 * 32, 29 * 32, 0, 13 * 32)
    wat, cap = [], []
    for cur, f3, vy in ((0x0B, 1, -640), (0x0E, 1, 128), (0x1C, 3, -640), (0x1B, 3, 640), (0x0A, 3, -320)):
        g.begin(x=400, y=150, vx=0, vy=vy & 0xFFFF, cur=cur, f3=f3, floor=False, width=80, patch=patch, apply=lambda gg: gg.m.__setitem__(0xD443, 1))
        pk = pack(g.run(10, padf=lambda u, f: 0))
        wat.append({"state": h(cur, 2), "vy": [p[9] for p in pk], "vy_delta_per_update": sorted({pk[i + 1][9] - pk[i][9] for i in range(len(pk) - 1)})})
        for start_vx in (1024, 1536):
            g.begin(x=400, y=150, vx=start_vx, vy=vy & 0xFFFF, cur=cur, f3=f3, floor=False, width=80, patch=patch)
            pk = pack(g.run(14, padf=lambda u, f: 8))
            cap.append({"state": h(cur, 2), "start_vx": start_vx, "input": "right", "vx": [p[8] for p in pk], "speed_cap_d373": g.s.u16(0xD373)})
    g.begin(x=400, y=20, vx=0, vy=0, cur=0x0E, f3=1, floor=False, width=80, patch=patch)
    pk = pack(g.run(160, padf=lambda u, f: 0))
    top = max(p[9] for p in pk)
    return {"evidence": "EMULATED ORIGINAL FRAME in open air (SYNTHETIC CONTROL: AQZ3 cells cleared; $D443 = 1 for the water fixtures)",
            "water_gravity": wat, "right_held_from_high_speed": cap, "dry_terminal_fall": {"max_vy": top, "first_update_at_max": next(p[0] for p in pk if p[9] == top)}}


def setter_callers(rom: bytes) -> dict:
    """Every absolute CALL / JP / JP cc reference to the launch and fall setters, located by byte scan of the whole ROM."""
    import re

    def where(o):
        bank = o // 0x4000
        cpu = (o % 0x4000) + (0 if bank == 0 else (0x4000 if bank == 1 else 0x8000))
        return f"bank ${bank:02X}:{cpu:04X}"
    out = {}
    for name, addr in (("$035F upright-launch vector (-> $5F17 -> $480C)", 0x035F), ("$480C upright setter", 0x480C), ("$482D diagonal setter", 0x482D),
                       ("$4849 horizontal setter (left half)", 0x4849), ("$4868 horizontal setter (right half)", 0x4868),
                       ("$47FB $1B setter", 0x47FB), ("$03BF $1B vector (-> $47FB)", 0x03BF), ("$463C fall setter", 0x463C),
                       ("$039B fall vector (-> $463C)", 0x039B), ("$4663 strip fall setter", 0x4663), ("$4699 roll-off-ledge setter", 0x4699)):
        hits = []
        for op in (0xCD, 0xC3, 0xCA, 0xC2, 0xDA, 0xD2):
            for m in re.finditer(re.escape(bytes([op, addr & 255, addr >> 8])), rom):
                hits.append({"site": where(m.start()), "file": h(m.start(), 5), "opcode": f"{op:02X}"})
        out[name] = sorted(hits, key=lambda x: x["file"])
    return {"evidence": "BYTE-VERIFIED (absolute-address scan of the 512 KiB ROM; relative JR sites are not scanned)", "callers": out}


def ceiling_spring_windows(rom: bytes) -> dict:
    """Whole-game sweep of the ceiling-spring block ($3B, header flags $54, vertical profile $50) patched into open air (AQZ3 cells cleared).

    $749D is reached from BOTH the ceiling pass $73C9 (rising, floor clear) and the terrain-ring probe $753E tail (no Y-speed / floor gate), so the block fires
    for a player falling onto it from above as well as for one rising into it from below."""
    g = rig(rom, 4, 2)
    cx, cy = 14, 7
    patch = {**clear_cells(6 * 32, 29 * 32, 0, 13 * 32), (cx, cy): 0x3B}

    def run(x, y, vy, cur, f3):
        g.begin(x=x, y=y, vx=0, vy=vy & 0xFFFF, cur=cur, f3=f3, floor=False, width=80, patch=patch, prev=0x00)
        for r in g.run(48, padf=lambda u, f: 0):
            if any(e.startswith("set_1B") for e in r["ev"]):
                return [r["u"], r["y"], s16(r["vy"]), s16(r["vx"]), r["hurtf"], h(r["req"], 2)]
        return None
    out = {}
    for label, cur, f3, vy, offsets in (("falling_from_above_state_0E", 0x0E, 1, 256, (70, 71, 72, 73, 74, 75)), ("falling_from_above_state_1C", 0x1C, 3, 256, (70, 71, 72, 73, 74, 75)),
                                         ("rising_from_below_state_0B", 0x0B, 1, -1408, (80, 81, 82, 83)), ("rising_from_below_state_1C", 0x1C, 3, -1408, (80, 81, 82, 83))):
        rows = []
        for off in offsets:
            ystart = cy * 32 - off if vy > 0 else cy * 32 + off
            cols = "".join("X" if run(cx * 32 + dx, ystart, vy, cur, f3) else "." for dx in range(32))
            rows.append({"start_y_offset_from_cell_top": -off if vy > 0 else off, "columns_dx_0_to_31_fired": cols, "fire_at_dx_16_[update,y,vy,vx,d503,request]": run(cx * 32 + 16, ystart, vy, cur, f3)})
        out[label] = rows
    return {"evidence": "EMULATED ORIGINAL FRAME + SYNTHETIC CONTROL (block $3B patched into AQZ3 open air at cell (14,7); never a canonical placement)",
            "block_header": {"flags": "0x54", "type": "0x14", "vertical_profile_raw": "0x50 (bit 6 + height 16)", "horizontal_profile": "0"},
            "fixtures": out,
            "reading": "launch = vx +4.0, vy +5.5 (down), request $1B, d503 3, player pushed down out of the block; falling players are caught from cell column 9 on, rising players over the whole width"}


def same_state_horizontal(rom: bytes) -> dict:
    """Executing state $09 touches a horizontal spring (request $09 again): does the wrapper's rolling suffix still run and can opposing input replace the request?"""
    out = {"evidence": "CONTROLLED ROUTINE RESULT ($4849 then $37F4 on the Oracle) + EMULATED ORIGINAL FRAME (THZ1 block $33 at (3200,832), grounded roll running left)"}
    lab = lab_empty(rom)
    ctl = []
    for label, held in (("no_input", 0), ("opposing_left_vs_vx_plus", 4), ("same_direction_right", 8)):
        lab.player(1000, 400, vx=0xFC00, vy=0, floor=1, cur=9, req=9, f3=2)
        lab.m[0xD501], lab.m[0xD137] = 9, held
        lab.call_hl(0x4849, 0x0600)
        a = lab.snap()
        lab.call_ix(0x37F4)
        b = lab.snap()
        ctl.append({"case": label, "after_setter": {"req": h(a["req"], 2), "d503": a["f3"], "vx": s16(a["vx"]), "vy": s16(a["vy"])},
                    "after_rolling_suffix_37F4": {"req": h(b["req"], 2), "d503": b["f3"], "vx": s16(b["vx"]), "vy": s16(b["vy"])}})
    out["controlled"] = ctl
    g = rig(rom, 0, 0)
    cap = []

    def mk(n):
        def fn(mm):
            if mm.slot[1] == 1:
                cap.append({"after": n, "executing": mm.mem[0xD501], "req": h(mm.mem[0xD502], 2), "d503": mm.mem[0xD503], "vx": s16(mm.u16(0xD516)), "vy": s16(mm.u16(0xD518))})
        return fn
    g.hook(0x4867, mk("setter_4849"))
    emu = []
    for label, pad in (("opposing_left", 4), ("no_input", 0), ("same_direction_right", 8)):
        cap.clear()
        g.begin(x=3300, y=850, vx=0xFC00, vy=0, cur=0x09, f3=2, floor=True, width=128)
        rows = g.run(36, padf=lambda u, f, p=pad: p)
        hit = next((r for r in rows if any(e.startswith("sp_h") for e in r["ev"])), None)
        seq = []
        if hit:
            for r in rows:
                if hit["u"] <= r["u"] <= hit["u"] + 3:
                    seq.append({"update": r["u"], "executing": h(r["cur"], 2), "requested": h(r["req"], 2), "d503": r["hurtf"], "vx": s16(r["vx"]), "vy": s16(r["vy"]),
                                "frame": h(r["fr"], 2), "counter": r["ctr"], "events": list(r["ev"])})
        emu.append({"case": label, "setter_exit_snapshot": list(cap), "rows_from_contact": seq})
    out["emulated"] = emu
    out["classification"] = "CANONICAL - preserve it"
    out["rule"] = ("The horizontal setter requests state 9 while state 9 is executing; wrapper $38C5 only tests 'requested == 9', so it continues into the rolling update $37F4. $37F4 tests the SIGN of the X speed "
                   "just written and the held direction: positive vx with Left held -> $47B6, negative vx with Right held -> $47C9 (each: if the airborne bit is clear, sound $A1, attack bit cleared, "
                   "request 7 / 8). Opposing input therefore replaces the request with $07 (or $08) in the same update and clears attack; the animation counter/frame of state 9 is not touched until state 7 starts next update.")
    return out


def correction_notes() -> list:
    return [{"id": "C1", "supersedes": "docs/spring-interaction-audit.md section 2.5 / section 3 'Ceiling $749D' column (needs Y speed negative, floor flag clear)",
             "fact": "that gate belongs to the ceiling pass $73C9 only. $749D is also reached by a tail jump from the terrain-ring probe $753E ($7569 JP $749D, no gate), so a ceiling-spring block ($3A/$3B) also launches "
                     "a player who is FALLING onto it (state $0E vy +400 at AQZ3 update 142). The POC calls its ceiling-spring handler only from the ceiling pass (SCR_cc_ceiling) and its ring-probe hook dispatches surface $1A only.",
             "evidence": "BYTE-VERIFIED ($6914 CALL $753E, $753E..$756B) + EMULATED ORIGINAL FRAME (aqz3_natural_run update 142; ceiling_spring_windows)", "class": "CANONICAL (supersedes earlier gate); POC DIVERGENCE candidate"}]


# --------------------------------------------------------------------------- #
# 6. contracts (assembled from the facts above; asserted by tests against the emulated rows)
# --------------------------------------------------------------------------- #
MECHANISM = {"sp_up": "upright setter $480C", "sp_diag": "diagonal setter $482D", "sp_hR": "horizontal setter $4849/$4868", "sp_hL": "horizontal setter $4849/$4868",
             "set_1B": "$1B setter $47FB (ceiling spring / ramp)", "apex": "fall setter $463C", "land": "landing $45CE", "brk0D": "breakable $6B2C", "brk16": "breakable $6AE3",
             "hurt": "hurt $48F7"}


def handoff_matrix(scenarios: list) -> list:
    """Every observed (executing state, mechanism, requested state) transition in the emulated rows, with counts and the first example."""
    acc: dict = {}
    for sc in scenarios:
        for r in sc["rows"]:
            u, cur, req, f3, fr, ctr, x, y, vx, vy, d448, face, fl, ev = r
            for e in dict.fromkeys(ev):
                k = e.split("(")[0]
                if k not in MECHANISM:
                    continue
                label = MECHANISM[k]
                if k in ("sp_up", "sp_diag"):
                    hl = int(e.split("HL=")[1].rstrip(")"), 16)
                    if vy != s16(hl):
                        label += " (entered, rejected: Y speed negative)"
                elif k in ("sp_hR", "sp_hL"):
                    hl = int(e.split("HL=")[1].rstrip(")"), 16)
                    if abs(vx) != hl:
                        label += " (entered, no effect)"
                key = (h(cur, 2), label, h(req, 2))
                e = acc.setdefault(key, {"executing_state": key[0], "mechanism": key[1], "requested_state": key[2], "count": 0,
                                         "first": {"scenario": sc["id"], "update": u, "vy_after": vy, "d503_after": f3}})
                e["count"] += 1
    return sorted(acc.values(), key=lambda e: (e["executing_state"], e["mechanism"], e["requested_state"]))


def d448_values(scenarios: list) -> list:
    """D448 and the first frame on every entry into state $0B (explicit-store check)."""
    out = []
    for sc in scenarios:
        rows = sc["rows"]
        for i in range(1, len(rows)):
            if rows[i][1] == 0x0B and rows[i - 1][1] != 0x0B:
                out.append({"scenario": sc["id"], "entry_update": rows[i][0], "d448": h(rows[i][10], 2), "first_frame": h(rows[i][4], 2), "vy_first_row": rows[i][9]})
    return out


def approval_board(rom: bytes, path: Path) -> dict:
    """Compact approval board: exact canonical frames grouped by owning state, with frame number / mapping source / state usage."""
    from level_maps import Canvas
    sel = palette_selectors(rom)
    palette = A.palette_rgba(rom, int(sel["thz1"]["sprite"], 16))
    scale, cw = 3, 120
    groups = [
        ("STATE $0E  CALLBACK $03AD TO $3A37  FRAMES $02 $03 $04 $05 $06 $01  8 UPDATES EACH", (2, 3, 4, 5, 6, 1), "FALL CYCLE (APEX / LEDGE / CEILING BUMP)"),
        ("STATE $0B ($D448 BIT0=0)  $1C  $14  FRAMES $1C-$21  ($0B:4  $1C:8  $14:4 UPDATES)", (0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21), "WEAK TYPE $26 / TYPE $50 BOSS BOUNCE / DIAGONAL / STRIP FALL"),
        ("STATE $0B ($D448 BIT0=1)  FRAME $61  (RECORD OF 4 UPDATES, REPEATED)", (0x61,), "STRONG TYPE $26 / TERRAIN UPRIGHT / TYPE $21 STOMP"),
        ("CONTEXT: SELECTOR $8F76 SPIN FRAMES $25-$29  STATES $09 $0A $10 $1B (NOT NEWLY MISSING)", (0x25, 0x26, 0x27, 0x28, 0x29), "BALL / ATTACK POSTURE STATES"),
    ]
    rendered, heights = [], []
    for title, ids, usage in groups:
        cells, hmax = [], 0
        for fid in ids:
            parsed, source, w, hgt, rgba, meta, cpu, mapping = render_frame_rgba(rom, fid, palette)
            cells.append((fid, w, hgt, rgba, cpu, source))
            hmax = max(hmax, hgt)
        rendered.append((title, usage, cells, hmax))
        heights.append(hmax * scale + 52)
    width = max(max(len(g[1]) for g in groups) * cw + 20, 860)
    cv = Canvas(width, sum(heights) + 14 * len(groups) + 10)
    cv.rect(0, 0, cv.w - 1, cv.h - 1, (30, 30, 46))
    y = 8
    for (title, usage, cells, hmax), band in zip(rendered, heights):
        cv.text(10, y, title, (255, 224, 96), 2)
        cv.text(10, y + 14, usage, (150, 200, 255), 2)
        base = y + 32
        for i, (fid, w, hgt, rgba, cpu, source) in enumerate(cells):
            ox = 10 + i * cw
            cv.rect(ox, base, ox + cw - 8, base + hmax * scale + 2, (46, 46, 70))
            for py in range(hgt):
                for px in range(w):
                    q = (py * w + px) * 4
                    if rgba[q + 3]:
                        for dy in range(scale):
                            for dx in range(scale):
                                cv.set(ox + 4 + px * scale + dx, base + 1 + py * scale + dy, rgba[q:q + 3])
            cv.text(ox + 2, base + hmax * scale + 4, "FRAME $%02X" % fid, (255, 255, 255), 2)
            cv.text(ox + 2, base + hmax * scale + 18, "MAP $%04X TILES %02X:%04X" % (cpu, int(source["bank"], 16), int(source["source_cpu"], 16)), (180, 180, 200), 1)
        y += band + 14
    path.parent.mkdir(parents=True, exist_ok=True)
    A.write_rgba_png(path, cv.w, cv.h, bytes(cv.buf))
    return {"width": cv.w, "height": cv.h, "png_sha256": sha(path.read_bytes())}


def read_png_rgba(path: Path):
    """Minimal PNG reader (8-bit RGBA / RGB / palette, non-interlaced) for the read-only POC asset comparison."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, plte, trns, hdr = 8, b"", None, None, None
    while pos < len(data):
        n = int.from_bytes(data[pos:pos + 4], "big")
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            hdr = body
        elif kind == b"PLTE":
            plte = body
        elif kind == b"tRNS":
            trns = body
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    w, hgt = int.from_bytes(hdr[0:4], "big"), int.from_bytes(hdr[4:8], "big")
    depth, ctype, interlace = hdr[8], hdr[9], hdr[12]
    if depth != 8 or interlace or ctype not in (2, 3, 6):
        return None
    bpp = {2: 3, 3: 1, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = w * bpp
    out, prev, p = bytearray(), bytearray(stride), 0
    for _ in range(hgt):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out += line
        prev = line
    px = bytearray()
    for i in range(w * hgt):
        if ctype == 6:
            px += out[i * 4:i * 4 + 4]
        elif ctype == 2:
            px += out[i * 3:i * 3 + 3] + b"\xff"
        else:
            idx = out[i]
            alpha = trns[idx] if trns and idx < len(trns) else 255
            px += plte[idx * 3:idx * 3 + 3] + bytes((alpha,))
    return w, hgt, bytes(px)


def trim_mask(w: int, hgt: int, rgba: bytes):
    pts = [(x, y) for y in range(hgt) for x in range(w) if rgba[(y * w + x) * 4 + 3]]
    if not pts:
        return None
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    rows = [bytes(1 if rgba[(y * w + x) * 4 + 3] else 0 for x in range(x0, x1 + 1)) for y in range(y0, y1 + 1)]
    return x1 - x0 + 1, y1 - y0 + 1, b"".join(rows)


def poc_scan(rom: bytes, sprites_dir: Path) -> dict:
    """READ-ONLY comparison of the recovered frames against every PNG under the POC sprites directory (alpha-silhouette identity, either facing)."""
    sel = palette_selectors(rom)
    palette = A.palette_rgba(rom, int(sel["thz1"]["sprite"], 16))
    want = {}
    for group, ids, usage in (*FRAME_GROUPS, ("sanity_state_11_frames_already_imported", (0x38, 0x39, 0x3A), "positive control")):
        for fid in ids:
            parsed, source, w, hgt, rgba, meta, cpu, mapping = render_frame_rgba(rom, fid, palette)
            t = trim_mask(w, hgt, rgba)
            flipped = b"".join(t[2][r * t[0]:(r + 1) * t[0]][::-1] for r in range(t[1]))
            want[fid] = (t, flipped)
    hits = {fid: [] for fid in want}
    scanned = 0
    for png in sorted(sprites_dir.glob("*/*.png")):
        head = png.read_bytes()[:33]
        pw, ph = int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
        scanned += 1
        if pw * ph > 24000 or pw < 8 or ph < 16:
            continue
        r = read_png_rgba(png)
        if r is None:
            continue
        t = trim_mask(*r)
        if t is None:
            continue
        for fid, (a, fl) in want.items():
            if (t[0], t[1]) == (a[0], a[1]) and t[2] in (a[2], fl):
                hits[fid].append(f"{png.parent.name}/{png.name}")
    return {"png_files_scanned": scanned, "frames": {h(fid, 2): {"silhouette_matches": v} for fid, v in hits.items()}}


def transition_table() -> list:
    def r(src, state, d448, d503, anim, nxt, note=""):
        return {"source_mechanism": src, "state": state, "d448": d448, "d503_on_entry": d503, "animation": anim, "next_canonical_transition": nxt, "note": note}
    return [
        r("mapped type $26 fixed parameter 0 / span with aux1 0 (strong, vy -7.375), terrain upright blocks $30/$31 (vy -7.5), type $21 top stomp (vy -6.75), type $30 (AQZ, strong path)",
          "$0B", "$FF", "1 (airborne set, attack clear)", "frame $61 only: one record (4 updates) repeated; mapping $85AC, 16x48 px, origin (9,44)",
          "apex: wrapper $393B, Y speed high byte >= 0 after gravity (79/80 updates from -7.375/-7.5) -> $463C: request $0E, vy +1.0, d503 1; floor flag -> $45CE (state 5)",
          "a ceiling contact sets vy +1.0, so the same test fires at once"),
        r("mapped type $26 fixed parameter != 0 / span with aux1 != 0 (weak, vy -5.0), type $50 (THZ3 boss) non-rising top bounce (vy -4.0)",
          "$0B", "$00", "1", "frames $1C,$1D,$1E,$1F,$20,$21 x 4 updates (twice), then $1C,$1D x 4, $1E,$1F,$20 x 6, $21 x 8: 82-update cycle that restarts; mapping $82B5.. 24x32 px",
          "apex as above (54 updates from -5.0, 43 from -4.0); landing -> state 5",
          "the weak and boss launches share one animation program; they differ only in Y speed (and therefore ascent length)"),
        r("terrain diagonal blocks $36/$37 (right) $38/$39 (left)", "$1C", "$00 (stored, never read by $1C)", "3 (airborne set, attack set)",
          "frames $1C..$21 x 8 updates each, restart after 48; no $D448 condition",
          "apex: wrapper $3955 -> $463C: request $0E, vy +1.0, d503 1 (attack CLEARED); landing -> state 5; ceiling spring while rising replaces the request with $1B",
          "vx +/-4.0; vy -5.5 outside THZ (-7.0 in THZ); the wrapper does not update facing"),
        r("terrain horizontal blocks $32..$35 (side probe, no gates)", "$09", "untouched", "2 (airborne CLEAR, attack set)", "selector $8F76 spin frames $25..$29",
          "grounded: rolling update $37F4; in the air: update 1 flips a negative Y speed to its magnitude (airborne bit is clear), update 2 the empty-floor test requests $0A with vy 0 (airborne + attack set)",
          "vx +/-6.0, speed cap $0600"),
        r("ceiling blocks $3A/$3B (vx +4.0, vy +5.5), type $15 (vy +7.5), ramp launch $69B2", "$1B", "untouched", "3 (airborne set, attack set)", "selector $8F76 spin frames $25..$29",
          "no apex transition: persists through the whole arc; floor flag -> bit 0 cleared and $1B continues on the ground as an attack until X speed ~0 (state 1) or jump ($45ED -> $0A); a ground-run-off request $463C -> $0E",
          "replaces any pending $0B/$1C/$0E request while Y speed is negative and the floor flag is clear"),
        r("$463C callers: apex wrappers ($393B/$3955), ceiling bump, empty-floor pass $6C7C (run off a ledge from any non-air state except $09), state $11 expiry",
          "$0E", "untouched", "1 (airborne set, attack CLEAR)", "frames $02,$03,$04,$05,$06,$01 x 8 updates each, four full passes then $02..$06, restart ($81E0, 29 records, 232 updates); mapping $8197..$81C3",
          "landing ($3A37 -> $45CE) -> state 5; any spring/bounce request replaces it", "no apex test of its own; horizontal control tables at +/-$10; facing never updated"),
        r("jump button on the floor ($45ED), $09 left in the air by $4699", "$0A", "untouched", "3", "selector $8F76 spin frames $25..$29",
          "stays $0A through ascent, apex and descent (the $463C setter returns at once when the state is $0A); landing $45CE unless $D36C = $0D",
          "held jump re-pins vy to -4.25 (-3.25 underwater) for 13 updates"),
        r("special strip fall setter $4663", "$14", "untouched", "1", "frames $1C..$21 x 4 updates each (script $81C6); callback $03F8 -> $3A48", "landing -> state 5; all-zero air control",
          "third consumer of the tumble frame set"),
    ]


def poc_source_facts() -> dict:
    """READ-ONLY facts about the POC at the accepted baseline (no POC file is touched)."""
    return {"evidence": "POC SOURCE (READ-ONLY)", "poc_commit": "5d99a38d1f439ac02cd9d3010d09f70cc57aa575",
            "files": ["scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml", "scripts/SCR_chaos_spring/SCR_chaos_spring.gml"],
            "facts": [
                "SCR_chaos_core_sprites selects the player sprite from movement flags, not from the ROM state script: 'chaosSpringVisual && vy < 0 -> SPR_player_jump' (line 75), "
                "'move & 1 -> SPR_player_falling' (line 76), 'move & 2 or next == 9 -> SPR_player_spin' (line 74)",
                "SPR_player_jump / SPR_player_falling / SPR_player_spin are the inherited Sonic-2 sprites; none of the frames below exists in the POC project (silhouette scan of 1,146 sprite PNGs, positive control = frames $38-$3A)",
                "chaos_spring26_launch_presentation forces sprite_index = SPR_player_jump on every type-$26 launch (SCR_chaos_spring.gml line 38)",
                "image_xscale follows sign(vx) outside the footwear states (SCR_chaos_core_sprites), but the ROM facing is the +$04 bit 4 flag owned by $48A7 / selector $8F76 / setters",
                "state $12 (Spring Shoes) is drawn with SPR_player_jump although its script frame is $0B (standing pose in the player mapping): adjacent finding, outside this closure",
            ]}


def poc_contract(rom: bytes) -> dict:
    """What must replace the inherited Sonic-2 'jump / fall / spin' selection for the six states."""
    def seq(state, bit0=0):
        u = unroll(rom, state, bit0)
        return [{"frame": h(r["frame"], 2), "updates": r["duration"]} for r in u if "frame" in r]
    return {
        "principle": "Select the sprite from the ROM state that is EXECUTING (+$01 after the engine), restart its record program only when that state changes, and advance by player updates "
                     "(not GameMaker image_speed). The executing state lags the requested state (+$02) by one update. Never infer the sprite from airborne/attack flags or the sign of Y speed.",
        "state_to_presentation": [
            {"state": "0x0B", "condition": "$D448 bit 0 clear, read only when the script (re)starts", "frames": seq(0x0B, 0), "loop": "restart after the last record, re-reading $D448"},
            {"state": "0x0B", "condition": "$D448 bit 0 set, read only when the script (re)starts", "frames": seq(0x0B, 1), "loop": "one 4-update record repeats; $D448 is re-read at each repeat"},
            {"state": "0x1C", "condition": "always", "frames": seq(0x1C), "loop": "restart after frame $21"},
            {"state": "0x14", "condition": "always (strip fall)", "frames": seq(0x14), "loop": "restart after frame $21"},
            {"state": "0x0E", "condition": "always", "frames": seq(0x0E), "loop": "29 records of 8 updates (232 updates): the order $02,$03,$04,$05,$06,$01 four times, then $02..$06, then the script restarts at $02"},
            {"state": "0x09 / 0x0A / 0x10 / 0x1B", "condition": "always", "frames": "selector $8F76: frame = $8FB8[$D52F] (frames $25..$29), duration 3 in the air / $8FE0[|vx hi|] on the floor", "loop": "$D52F wraps at 20"},
        ],
        "replace_in_poc": [
            "the 'chaosSpringVisual / vy<0 -> SPR_player_jump' rule and the unconditional SPR_player_jump on type-$26 launch",
            "the 'move & 1 -> SPR_player_falling' fall rule for state $0E and every other airborne state",
            "the 'move & 2 -> SPR_player_spin' rule for state $1C (diagonal spring): $1C is the tumble set ($1C..$21), not the spin ball",
        ],
        "keep": ["spin ball presentation for $09/$0A/$10/$1B is a separate (inherited-art) question: the canonical frames are $25..$29 (board row 4), not covered by an accepted import"],
        "restart_rules": [
            "a state script restarts only when the executing state changes; requesting the state that is already executing ($1C -> $1C, $0B -> $0B) does NOT restart the frame/counter",
            "a stronger $0B re-launch while a weak script is running keeps the weak frames until the script restarts (D448 is re-read only at restart)",
            "the counter reloads the first record on the update the new state starts executing (one update after the request)",
            "the executing state, not the requested state, owns the sprite: at a launch the old state keeps drawing for the update in which the setter ran",
        ],
        "facing": "mirror by the +$04 bit 4 flag. $0B follows held Left/Right every update ($48A7); $0E, $1C and $14 never update it; $0A/$1B/$09/$10 update it from input only when the selector reloads (every 3 updates in the air). "
                  "Springs set it themselves (diagonal: left block -> set).",
        "approval": "build/player-spring-airborne/approval-board.png (frames $01-$06, $1C-$21, $61, $25-$29)",
    }


def build(rom: bytes, static_only: bool = False, board: Path | None = None) -> dict:
    check_rom(rom)
    board = board or BOARD_DIR
    out = {
        "format": 1, "rom_sha256": ROM_SHA256, "research_base": RESEARCH_BASE, "research_only": True, "poc_untouched": True, "static_only": static_only,
        "scope": "Research only: shared Sonic Chaos spring/airborne player-state closure (states $09, $0A, $0B, $0E, $1B, $1C, with $14 as the third consumer of the tumble frame set)",
        "evidence_classes": ["DECODED DATA", "BYTE-VERIFIED ASSEMBLY", "SOURCE-TRACED BEHAVIOR", "CONTROLLED ROUTINE RESULT", "EMULATED ORIGINAL FRAME", "SYNTHETIC CONTROL", "POC SOURCE", "UNRESOLVED"],
        "regions": region_table(rom),
        "callback_vectors": [vector_target(rom, v) for v in sorted(VECTORS)],
        "state_scripts": state_scripts(rom),
        "frame_consumers": frame_consumers(rom),
        "selector_frame_tables": selector_frame_tables(rom),
        "frames": frame_table(rom, board),
        "approval_board": {**approval_board(rom, board / "approval-board.png"), "file": "build/player-spring-airborne/approval-board.png (git-ignored; regenerate with this tool)",
                           "rows": ["state $0E fall frames", "state $0B weak / $1C / $14 tumble frames", "state $0B strong frame $61", "context spin frames $25..$29"]},
        "movement_tables": movement_tables(rom),
        "attack_by_state": attack_by_state(),
        "transition_table": transition_table(),
        "poc_source_facts": poc_source_facts(),
        "poc_contract": poc_contract(rom),
    }
    if not static_only:
        out["wrapper_sweeps"] = wrapper_sweeps(rom)
        out["spring_gate_matrix"] = spring_gate_matrix(rom)
        out["breakable_matrix"] = breakable_matrix(rom)
        out["free_flight"] = free_flight(rom)
        out["apex_ordering"] = apex_ordering(rom)
        out["jump_hold_state_0A"] = jump_hold(rom)
        out["free_flight_water_and_cap"] = free_flight_water_and_cap(rom)
        out["setter_callers"] = setter_callers(rom)
        out["ceiling_spring_windows"] = ceiling_spring_windows(rom)
        out["same_state_horizontal_spring"] = same_state_horizontal(rom)
        out["corrections"] = correction_notes()
        out["emulated_flights_thz"] = flights_thz(rom)
        out["stomp_and_boss"] = stomp_and_boss(rom)
        out["aqz_chains"] = aqz_chains(rom)
        every = [*out["emulated_flights_thz"]["scenarios"], *out["stomp_and_boss"]["scenarios"], *out["aqz_chains"]["scenarios"]]
        out["handoff_matrix"] = {"evidence": "EMULATED ORIGINAL FRAME (derived from every row of the scenarios above)", "rows": handoff_matrix(every)}
        out["d448_on_entry_to_0B"] = {"evidence": "EMULATED ORIGINAL FRAME", "rows": d448_values(every)}
    return out


def dumps(data: dict) -> str:
    return json.dumps(data, indent=1) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    ap.add_argument("--board", type=Path, default=None, help="write the per-frame PNGs and the approval board here (default build/player-spring-airborne)")
    ap.add_argument("--poc-scan", type=Path, default=None, help="print the READ-ONLY silhouette comparison against a POC sprites directory and exit")
    a = ap.parse_args()
    rom = L.load_rom(a.rom)
    if a.poc_scan:
        print(json.dumps(poc_scan(rom, a.poc_scan), indent=1))
        return
    text = dumps(build(rom, a.static_only, a.board))
    if a.check:
        if OUTPUT.read_text(encoding="utf-8") != text:
            raise SystemExit("cache mismatch: " + str(OUTPUT))
        print("player-spring-airborne cache matches")
    else:
        OUTPUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUTPUT} ({len(text)} bytes)")


if __name__ == "__main__":
    main()

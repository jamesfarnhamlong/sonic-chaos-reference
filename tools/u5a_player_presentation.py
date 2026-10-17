#!/usr/bin/env python3
"""U5-A (parts A-C): Sonic strip run / strip fall, Spring Shoes pose and weak-spring tumble presentation (Sonic Chaos SMS, Europe v1.2).

    python tools/u5a_player_presentation.py ROM                       # regenerate data/u5a/player-*.json (+ ignored exports in build/u5a/)
    python tools/u5a_player_presentation.py ROM --check               # recompute everything and compare with the committed JSON
    python tools/u5a_player_presentation.py ROM --only static         # static layer only (a few seconds, no emulation)
    python tools/u5a_player_presentation.py ROM --poc PATH_TO_POC    # additionally rewrite data/u5a/player-poc-source.json from a POC checkout (read only)
    python tools/u5a_player_presentation.py --validate                # no ROM: internal consistency of the committed JSON

Layers (every field belongs to exactly one):

* ``static``    - DECODED DATA / BYTE-VERIFIED ASSEMBLY: the Sonic walk / run frame selectors ($8EE1 / $8F45), the state scripts, the player mapping
                  records, the player tile-transfer table entries, the sprite palettes of all 18 acts and the surface-$19 census.
* ``observed``  - EMULATED ORIGINAL FRAME (tools/player_fall_control.Lab: the whole unmodified game booted into the act, Sonic placed, pad held from before
                  the first update).  Per-update rows: executing / requested state, the animation frame +$06, the duration counter +$07, the shared selector
                  index $D52F, the strip marker +$24 bit 0, the facing bit +$04 bit 4, position and speed.  Never a replacement for hardware.
* ``poc``       - POC SOURCE (READ-ONLY): which resources, animation programs and branches the POC at the given commit contains.  Regenerated only with --poc.

No ROM byte, tile pixel or palette is committed except small decoded numeric tables of the kind earlier Research caches already commit.  Frame pixels,
indexed PNGs and comparison sheets are exported to the ignored ``build/u5a``.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import level_package as L  # noqa: E402
import player_animation_counter as PAC  # noqa: E402
import player_spring_airborne as PSA  # noqa: E402
import player_state_11_graphics as G  # noqa: E402
import thz1_object_assets as A  # noqa: E402
import u4_results as U  # noqa: E402

ROM_SHA256 = U.ROM_SHA256
BASE_COMMIT = "c30c06e6c428b64e843ea5834ff52b7bc3304708"
POC_COMMIT = "b4737e834982b2985c6fdcb8d4d76cb78c9092c8"
DATA = ROOT / "data" / "u5a"
BUILD = ROOT / "build" / "u5a"
STATIC_JSON = DATA / "player-static.json"
OBS_JSON = DATA / "player-observed.json"
POC_JSON = DATA / "player-poc-source.json"
EXPORT_JSON = DATA / "player-export-manifest.json"

hx, sha, off, u16, load_rom, dumps, load_json = U.hx, U.sha, U.off, U.u16, U.load_rom, U.dumps, U.load_json
H = PSA.h
BANK = 12                       # player-selector / state-script bank (slot 2 while the player updates)

# frame groups: (group id, frame ids, what the original uses them for)
GROUPS = [
    ("stand_and_spring_shoes", (0x0B,), "idle frame (states $00/$01, 180-update record) AND the single record of state $12 (Spring Shoes)"),
    ("strip_walk_run", (0x3C, 0x3D, 0x3E, 0x3F), "walk $05 / run $06 selector frames while the +$24 bit 0 strip marker is set on surface $19"),
    ("ordinary_run", (0x07, 0x08, 0x09, 0x0A), "run $06 selector frames (marker clear or previous surface not $19)"),
    ("ordinary_walk_fall", (0x01, 0x02, 0x03, 0x04, 0x05, 0x06), "walk $05 selector frames; also the ordinary fall $0E records (2,3,4,5,6,1)"),
    ("tumble", (0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21), "weak spring $0B ($D448 bit 0 clear, 4 updates each), diagonal $1C (8 each), strip fall $14 (4 each)"),
    ("tall_strong_spring", (0x61,), "strong spring $0B ($D448 bit 0 set)"),
    ("side_push", (0x5E,), "walk selector side-contact frame ($D523 & $0C), duration 2"),
]
ALL_FRAMES = sorted({f for _, ids, _ in GROUPS for f in ids})
STRIP_ACTS = ("gpz1", "gpz2", "mghz1", "mghz2", "mghz3")        # re-derived below from the layouts, kept as the expectation


def check_rom(rom):
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM (SHA-256 %s)" % ROM_SHA256)


# ------------------------------------------------------------------------------------------------------------------------------------------
# static layer
# ------------------------------------------------------------------------------------------------------------------------------------------
def find_pattern(rom, bank, start, end, pattern):
    """All CPU addresses of `pattern` inside [start, end) of the bank-$0C slot-2 window."""
    a, b = off(bank, start), off(bank, end)
    out, pos = [], rom.find(pattern, a, b)
    while pos != -1:
        out.append(start + pos - a)
        pos = rom.find(pattern, pos + 1, b)
    return out


def selectors(rom):
    """Sonic walk ($8EE1) and run ($8F45) frame selectors; the code bytes are matched in full and every operand below follows from them.

    walk  $8EE1  LD A,(IX+$23) ; AND $0C ; JR NZ,$8F3C            side contact -> frame $5E, duration 2 (tested BEFORE any strip rule)
                  LD C,1 ; LD B,6                                  ordinary base frame and cycle length
                  BIT 0,(IX+$24) ; JR Z,$8F09                      strip marker clear -> ordinary
                  LD A,($D36C) ; AND $1F ; CP $19 ; JR Z,$8F05     previous surface $19 -> strip set
                  RES 0,(IX+$24) ; XOR A ; LD ($D3BC),A ; JR $8F09 otherwise clear the marker and the counter
        $8F05     LD C,$3C ; LD B,4
        $8F09     LD HL,$D52F ; INC (HL) ; LD A,(HL) ; CP B ; JR C,+2 ; XOR A ; LD (HL),A ; ADD A,C ; LD (IX+6),A
    run   $8F45  the same with C = 7 and a fixed cycle length 4 (CP 4); strip C = $3C; duration LD (IX+7),4
    """
    def need(cond, msg):
        if not cond:
            raise AssertionError("selector decode: " + msg)

    w = off(BANK, 0x8EE1)
    walk_hex = ("DD7E23E60C20540E010606DDCB24462817" "3A6CD3E61FFE19280ADDCB2486AF32BCD3" "18040E3C0604" "212FD5347EB83802AF7781DD7706")
    need(rom[w:w + len(walk_hex) // 2] == bytes.fromhex(walk_hex), "walk selector code bytes")
    side = off(BANK, 0x8F3C)
    need(rom[side:side + 9] == bytes.fromhex("DD36065EDD360702C9"), "walk side-contact frame $5E duration 2")
    table = rom[off(BANK, 0x8F2C):off(BANK, 0x8F2C) + 16]
    need(table == bytes.fromhex("0A080604040404040404040404040404"), "walk duration table")
    walk_tail = rom[w + len(walk_hex) // 2:w + len(walk_hex) // 2 + 15]
    need(walk_tail.startswith(bytes.fromhex("3A17D5A7F2208FED446F2600112C8F")), "walk duration lookup via $D517 and $8F2C")
    r = off(BANK, 0x8F45)
    run_hex = ("0E07DDCB244628153A6CD3E61FFE19280ADDCB2486AF32BCD318020E3C" "212FD5347EFE043802AF7781DD7706DD360704C9")
    need(rom[r:r + len(run_hex) // 2] == bytes.fromhex(run_hex), "run selector code bytes")
    return {
        "evidence": "BYTE-VERIFIED ASSEMBLY (the complete selector bodies are matched byte for byte; bank $0C, slot 2)",
        "walk_selector": {
            "cpu": "0x8EE1", "rom": H(w, 5), "sha256": sha(rom[w:w + len(walk_hex) // 2 + 15]),
            "order": "side contact ($D523 & $0C) -> frame $5E, duration 2 (before any strip test); else marker bit 0 set and previous surface "
                     "($D36C & $1F) == $19 -> strip set; else marker cleared and $D3BC zeroed; then the shared index $D52F",
            "ordinary": {"base_frame": 1, "cycle_length": 6, "frames": [1, 2, 3, 4, 5, 6]},
            "strip": {"base_frame": 0x3C, "cycle_length": 4, "frames": [0x3C, 0x3D, 0x3E, 0x3F]},
            "side_contact": {"frame": 0x5E, "duration": 2},
            "duration_by_abs_x_speed_high_byte": list(table),
            "duration_loaded_only_when_the_record_reloads": True,
        },
        "run_selector": {
            "cpu": "0x8F45", "rom": H(r, 5), "sha256": sha(rom[r:r + len(run_hex) // 2]),
            "ordinary": {"base_frame": 7, "cycle_length": 4, "frames": [7, 8, 9, 0x0A]},
            "strip": {"base_frame": 0x3C, "cycle_length": 4, "frames": [0x3C, 0x3D, 0x3E, 0x3F]},
            "duration": 4, "side_contact_branch": False,
        },
        "shared_index": {"ram": "0xD52F", "rule": "INC; if >= cycle_length then 0; frame := index + base_frame",
                         "consequence": "walk and run share ONE index: a $05 <-> $06 change keeps the phase (index mod 4 entering run or strip, mod 6 for ordinary walk)"},
        "marker": {"player_byte": "+$24 bit 0 (RAM $D524)", "set_by": "surface $19 handler $6B23 (floor sample, every contact pass)",
                   "cleared_by": ["walk/run selector when the previous surface is not $19", "normal jump $45ED", "ordinary fall setter $463C",
                                  "surface-zero handler $6C45"], "retained_by": "strip-fall setter $4663",
                   "see": "docs/gpz-surface19-audit.md, docs/player-fall-control-audit.md"},
    }


def program_for(rom, state):
    """Unrolled records (duration, frame) of a plain-record state script, with the unresolved FF commands kept as markers."""
    out = []
    for r in PAC.script_program(rom, state):
        if "frame" in r:
            out.append({"duration": r["record"], "frame": r["frame"], "frame_hex": H(r["frame"], 2), "callback": r["callback"]})
        else:
            out.append({"command": r["cmd"], "args": r.get("args", ""), **({"selector": r["selector"]} if "selector" in r else {})})
    return out


def state_programs(rom):
    states = {}
    for s, why in ((0x00, "power-on / new-level idle"), (0x01, "idle: one 180-update record of frame $0B, then FF 03 02 (request state 2)"),
                   (0x05, "walk: FF 05 selector $8EE1"), (0x06, "run: FF 05 selector $8F45"), (0x0B, "spring ascent (weak/strong)"),
                   (0x0E, "ordinary fall"), (0x12, "Spring Shoes: ONE record, frame $0B, duration 4, FF 00"), (0x14, "strip fall: tumble set, 4 updates each"),
                   (0x1C, "diagonal spring: tumble set, 8 updates each")):
        entry = {"why": why, "script_cpu": H(u16(rom, off(BANK, 0x8000 + 2 * s))), "program": program_for(rom, s)}
        if s == 0x0B:
            weak, strong = PSA.unroll(rom, s, 0), PSA.unroll(rom, s, 1)
            entry["play_order_d448_bit0_clear_weak"] = {"cycle_updates": sum(r["duration"] for r in weak if "frame" in r),
                                                       "frame_cadence": PSA.cadence(weak)}
            entry["play_order_d448_bit0_set_strong"] = {"cycle_updates": sum(r["duration"] for r in strong if "frame" in r),
                                                        "frame_cadence": PSA.cadence(strong)}
        elif s in (0x0E, 0x14, 0x1C, 0x12):
            u = PSA.unroll(rom, s)
            entry["play_order"] = {"cycle_updates": sum(r["duration"] for r in u if "frame" in r), "frame_cadence": PSA.cadence(u)}
        states[H(s, 2)] = entry
    return states


def sprite_palettes(rom):
    """Sprite palette records of the 18 acts and the title-zone opening level; which indices Sonic's frames use; identity across acts."""
    ident = [(0, 0, 0, 0)] + [(i * 16, i, 0, 255) for i in range(1, 16)]
    used = {}
    for fid in ALL_FRAMES:
        parsed, source, w, h, rgba, meta, cpu, mp = PSA.render_frame_rgba(rom, fid, ident)
        used[fid] = sorted({rgba[i] // 16 for i in range(0, len(rgba), 4) if rgba[i + 3]})
    union = sorted({i for v in used.values() for i in v})
    acts = {}
    for z in list(range(6)) + [7]:
        for a in range(3 if z != 7 else 1):
            ps = L.palette_selection(rom, z, a)
            rec = bytes(rom[ps["sprite_rom"]:ps["sprite_rom"] + 16])
            key = ("thz gpz sez mghz aqz eez ? title".split()[z]) + (str(a + 1) if z != 7 else "")
            acts[key] = {"zone": z, "act": a, "sprite_palette_index": ps["sprite_index"], "record": rec.hex().upper(),
                         "sonic_used_entries": [rec[i].__format__("02X") for i in union]}
    sonic_cols = {k: tuple(v["sonic_used_entries"]) for k, v in acts.items()}
    return {"evidence": "DECODED DATA (palette selector table $7F3C, 16-byte records, SMS %--BBGGRR)",
            "indices_used_by_frame": {H(k, 2): v for k, v in used.items()},
            "indices_used_union": union,
            "sonic_colours_identical_in_all_acts": len(set(sonic_cols.values())) == 1,
            "distinct_sonic_colour_sets": len(set(sonic_cols.values())),
            "entry_0": "transparent for sprites (record byte 0 differs per zone: backdrop, never drawn)",
            "entries_12_to_15_differ_between_zones": "not used by any Sonic frame above",
            "acts": acts}


def frame_table(rom, export=None):
    sel = PSA.palette_selectors(rom)
    pal = A.palette_rgba(rom, int(sel["thz1"]["sprite"], 16))
    ident = [(0, 0, 0, 0)] + [(i * 16, i, 0, 255) for i in range(1, 16)]
    frames, pngs = {}, []
    group_of = {f: g for g, ids, _ in GROUPS for f in ids}
    use_of = {f: u for _, ids, u in GROUPS for f in ids}
    for fid in ALL_FRAMES:
        parsed, source, w, hgt, rgba, meta, cpu, mapping = PSA.render_frame_rgba(rom, fid, pal)
        _, _, _, _, idx_rgba, _, _, _ = PSA.render_frame_rgba(rom, fid, ident)
        index = bytes(idx_rgba[i] // 16 if idx_rgba[i + 3] else 0 for i in range(0, len(idx_rgba), 4))
        b = meta["bounds"]
        frames[H(fid, 2)] = {
            "group": group_of[fid], "used_by": use_of[fid],
            "mapping_table_cpu": H(mapping["mapping_cpu"]), "mapping_frame_cpu": H(cpu), "mapping_frame_rom": H(parsed["frame_rom"], 5),
            "mapping_record": A.serialise_frame(parsed),
            "graphics_transfer": {k: v for k, v in source.items() if k != "raw"},
            "bounds_relative_to_player_anchor": b, "canvas_width": w, "canvas_height": hgt,
            "gamemaker_origin_x": -b["min_x"], "gamemaker_origin_y": -b["min_y"],
            "tile_bytes_sha256": source["tile_bytes_sha256"], "rgba_sha256_thz1_palette": sha(rgba), "index_sha256": sha(index),
            "non_transparent_pixels": meta["nonzero_source_pixels"], "facing": "right-facing art; +$04 bit 4 mirrors the pieces (horizontal flip of the right-facing image)",
        }
        pngs.append((fid, w, hgt, rgba))
    if export is not None:
        export.mkdir(parents=True, exist_ok=True)
        for fid, w, hgt, rgba in pngs:
            A.write_rgba_png(export / ("frame-%02X.png" % fid), w, hgt, rgba)
    return {"evidence": "DECODED DATA + deterministic reconstruction (bank-$0F mapping, interrupt-side tile loader table $104B; THZ1 sprite palette)",
            "object_type": "0x01", "palette_note": "pixels are identical in every act (see sprite_palettes); RGBA hash uses the THZ1 record, index hash is palette independent",
            "frames": frames}


def strip_census(rom):
    """Surface-$19 cells per act, straight from layout x collision header (re-derivation of the Research census)."""
    import mghz_foundation as MF
    table = MF.six_zone_surfaces(rom)
    row = table.get("0x19", {})
    return {"evidence": "DECODED DATA (layout cells x collision header flags & $1F, tools/mghz_foundation.six_zone_surfaces)",
            "surface_type": "0x19", "cells_by_act": dict(sorted(row.items())), "acts_with_strips": sorted(row),
            "blocks": "$85/$87 (header $59: one-way bit 6 + type $19, vertical profile 32, modifier 0)"}


def poc_free_static(rom):
    return {
        "rom_sha256": ROM_SHA256, "research_base": BASE_COMMIT, "scope": "U5-A parts A-C: strip animation, Spring Shoes pose, weak-spring tumble",
        "selectors": selectors(rom), "state_programs": state_programs(rom), "frames": frame_table(rom), "sprite_palettes": sprite_palettes(rom),
        "strip_census": strip_census(rom),
    }


# ------------------------------------------------------------------------------------------------------------------------------------------
# observed layer: whole-game emulation (EMULATED ORIGINAL FRAME)
# ------------------------------------------------------------------------------------------------------------------------------------------
def make_lab(rom, zone, act):
    import player_fall_control as PFC

    class FrameLab(PFC.Lab):
        """Lab whose rows are taken at the END of every player update ($4A74, IX = $D500), so lag frames that run two updates lose no row."""

        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.hook_rows = []
            self.s.add_pc_hook(0x4A74, self._end_update)

        def _end_update(self, mm):
            if mm.cpu.ix == 0xD500 and self.upd > 0:
                self.hook_rows.append(self.row())

        def row(self):
            r = super().row()
            m = self.m
            r.update(fr=m[0xD506], ctr=m[0xD507], idx=m[0xD52F], face=(m[0xD504] >> 4) & 1, p24=m[0xD524] & 1, f4=m[0xD504])
            return r

        def run_updates(self, updates, pad):
            """Pad held from before the first update; one row per player update, u = 1 for the first update after place()."""
            self.hook_rows = []
            self.m[0xD137] = self.m[0xD138] = pad
            for _ in range(updates * 3 + 20):
                self.s.pad = pad
                self.s.run_frame()
                if len(self.hook_rows) >= updates:
                    break
            return self.hook_rows[:updates]
    return FrameLab(rom, zone, act)


COLUMNS = ["u", "cur", "req", "frame", "ctr", "d52f", "marker", "face", "x", "y", "vx", "vy", "floor", "d36c", "owner"]


def pack(rows):
    out = []
    for r in rows:
        out.append([r["u"], r["cur"], r["req"], r["fr"], r["ctr"], r["idx"], r["p24"], r["face"], r["x"], r["y"], r["vx"], r["vy"],
                    (r["f22"] >> 1) & 1, r["d36c"], r["d3c0"]])
    return out


def rle(values):
    out = []
    for v in values:
        if out and out[-1][0] == v:
            out[-1][1] += 1
        else:
            out.append([v, 1])
    return out


def summarise(packed):
    c = {n: i for i, n in enumerate(COLUMNS)}
    frames_by_state = {}
    for p in packed:
        frames_by_state.setdefault(H(p[c["cur"]], 2), []).append(p[c["frame"]])
    runs = {k: [[H(f, 2), n] for f, n in rle(v)] for k, v in frames_by_state.items()}
    states = [[H(s, 2), n] for s, n in rle([p[c["cur"]] for p in packed])]
    return {"executing_state_runs": states, "frame_runs_by_executing_state": runs,
            "marker_values": sorted({p[c["marker"]] for p in packed}), "facing_values": sorted({p[c["face"]] for p in packed}),
            "first_update_with_requested_14": next((p[c["u"]] for p in packed if p[c["req"]] == 0x14), None),
            "foot_surfaces_seen": sorted({H(p[c["d36c"]] & 0x1F, 2) for p in packed})}


def run_case(lab, sid, mechanism, begin, pad, updates, extra=None, face=None):
    lab.place(**begin)
    if face is not None:                              # SYNTHETIC: the facing the walk callback ($48A7) would have left before the run was entered
        lab.m[0xD504] = (lab.m[0xD504] & ~0x10) | (0x10 if face else 0)
    rows = lab.run_updates(updates, pad)
    p = pack(rows)
    out = {"id": sid, "mechanism": mechanism, "begin": {k: (H(v, 2) if isinstance(v, int) and k in ("cur", "f3", "prev", "p24") else v) for k, v in begin.items()},
           "pad": {0: "none", 4: "LEFT", 8: "RIGHT"}.get(pad, pad), "synthetic_facing_bit": face, "updates": len(p), "columns": COLUMNS, "rows": p, "summary": summarise(p)}
    if extra:
        out.update(extra)
    return out


def observed(rom):
    cases = []
    g = make_lab(rom, "gpz", 1)                                      # GPZ2: strip (528,686); ordinary solid floor cell (54,8); type-$28 platform (1584,384)
    cases.append(run_case(g, "gpz2_strip_run_right", "GPZ2 strip (528,686), run $06 at +4.0, Right held", dict(x=528, y=686, vx=0x400, vy=0, cur=6, f3=0, floor=True, prev=0x59), 8, 48))
    cases.append(run_case(g, "gpz2_strip_walk_plus3_right", "GPZ2 strip (528,686), walk $05 at +3.0, Right held (slower than maximum: strip fall)",
                          dict(x=528, y=686, vx=0x300, vy=0, cur=5, f3=0, floor=True, prev=0x59), 8, 40))
    cases.append(run_case(g, "gpz2_strip_run_then_release", "GPZ2 strip (528,686), run $06 at +4.0, pad released: run -> walk -> strip fall $14",
                          dict(x=528, y=686, vx=0x400, vy=0, cur=6, f3=0, floor=True, prev=0x59), 0, 48))
    cases.append(run_case(g, "gpz2_strip_stand", "GPZ2 strip (528,686), forced idle $01 (state-conditioned support: stays on the strip)",
                          dict(x=528, y=686, vx=0, vy=0, cur=1, f3=0, floor=True, prev=0x59), 0, 24))
    cases.append(run_case(g, "gpz2_ordinary_run_marker_clear", "control: GPZ2 ordinary solid floor (1748,238), run $06 at +4.0, Right held, marker clear",
                          dict(x=1748, y=238, vx=0x400, vy=0, cur=6, f3=0, floor=True, prev=0x81, p24=0), 8, 24))
    cases.append(run_case(g, "gpz2_ordinary_run_marker_set", "control: same floor, strip marker SET synthetically (+$24 bit 0 = 1): the selector must clear it and use ordinary frames",
                          dict(x=1748, y=238, vx=0x400, vy=0, cur=6, f3=0, floor=True, prev=0x81, p24=1), 8, 24))
    cases.append(run_case(g, "gpz2_platform28_stand", "type-$28 platform GPZ2 (1584,384), parameter $83: Sonic dropped on it from (1584,350) at +3.0, no input; a platform is NOT a strip",
                          dict(x=1584, y=350, vx=0, vy=0x300, cur=0x0E, f3=1, floor=False, prev=0), 0, 60, {"object": "type $28, parameter $83 (docs/isometric-platform-audit.md section 3)"}))
    cases.append(run_case(g, "gpz2_platform28_walk_right", "same drop, Right held: lands (owner $D3C0 set), walks along the platform with the ordinary walk frames",
                          dict(x=1584, y=350, vx=0, vy=0x300, cur=0x0E, f3=1, floor=False, prev=0), 8, 30, {"object": "type $28, parameter $83"}))
    cases.append(run_case(g, "gpz2_deck_1c_walk_run", "terrain surface-$1C isometric deck GPZ2 (cell (4,6)): dropped at (144,94), Right held: walk then run on a deck, marker stays clear",
                          dict(x=144, y=94, vx=0, vy=0x100, cur=0x0E, f3=1, floor=False, prev=0), 8, 80))
    g1 = make_lab(rom, "gpz", 0)                                     # GPZ1: moving type-$28 platform, parameter $89 (horizontal reverser), (1648,320)
    cases.append(run_case(g1, "gpz1_platform28_moving_stand", "MOVING type-$28 platform GPZ1 (1648,320) parameter $89: Sonic dropped on it from (1648,290), no input: carried, idle frame only",
                          dict(x=1648, y=290, vx=0, vy=0x300, cur=0x0E, f3=1, floor=False, prev=0), 0, 120, {"object": "type $28, parameter $89 (state 10 horizontal reverser)"}))
    m = make_lab(rom, "mghz", 0)                                     # MGHZ1: upper strip cells X102..111, Y12 (foot Y 384)
    cases.append(run_case(m, "mghz1_upper_strip_run_left", "MGHZ1 upper strip at (3500,366), run $06 at -4.0, Left held (facing left)",
                          dict(x=3500, y=366, vx=-0x400, vy=0, cur=6, f3=0, floor=True, prev=0x59), 4, 48, face=1))
    cases.append(run_case(m, "mghz1_upper_strip_run_right", "MGHZ1 upper strip (cells X102..111, Y12) at (3408,366), run $06 at +4.0, Right held",
                          dict(x=3408, y=366, vx=0x400, vy=0, cur=6, f3=0, floor=True, prev=0x59), 8, 48))
    return {"evidence": "EMULATED ORIGINAL FRAME (tools/player_fall_control.Lab: unmodified game booted into the act, Sonic and camera teleported, REQUESTED state set so the "
                        "engine loads that state's script, pad held from before the first update)",
            "row_u": "update index; columns are the state AFTER that update's player pass (animation engine, callback, terrain, merge)",
            "columns": COLUMNS, "cases": cases}


# ------------------------------------------------------------------------------------------------------------------------------------------
# POC source layer (READ-ONLY) and a literal transcription of the POC presentation selector
# ------------------------------------------------------------------------------------------------------------------------------------------
def git_head(path):
    import subprocess
    try:
        return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def poc_sprite_facts(poc, name):
    d = Path(poc) / "sprites" / name
    yy = d / (name + ".yy")
    if not yy.is_file():
        return None
    t = yy.read_text(encoding="utf-8")
    pick = lambda key: int(re.search(r'"%s":\s*(-?\d+)' % key, t).group(1))
    frames = len([q for q in d.glob("*.png")])
    return {"width": pick("width"), "height": pick("height"), "xorigin": pick("xorigin"), "yorigin": pick("yorigin"), "frames": frames}


def poc_source_facts(poc):
    """Everything the handoff needs from the POC checkout, parsed from source text (nothing is executed)."""
    poc = Path(poc)
    anim = (poc / "scripts/SCR_chaos_player_animation/SCR_chaos_player_animation.gml").read_text(encoding="utf-8")
    data = (poc / "scripts/SCR_chaos_player_animation_data/SCR_chaos_player_animation_data.gml").read_text(encoding="utf-8")
    adapter = (poc / "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml").read_text(encoding="utf-8")
    sup = re.search(r"function chaos_player_animation_supported\(cp_state\) \{\s*return (.*?);\s*\}", anim, re.S).group(1)
    supported = sorted({int(x) for x in re.findall(r"cp_state == (\d+)", sup)})
    programs = {int(n): json.loads(body) for n, body in re.findall(r"case (\d+):\s*return (\[\[[\d,\[\]\s]*\]\]);", data)}
    sprite_cases = {int(n): {"thz": a.replace("cp_aqz ? ", "").strip(), "aqz": b.strip()} for n, a, b in
                    [(m[0], m[2], m[1]) for m in re.findall(r"case (\d+): return cp_aqz \? (\w+) : (\w+);", data)]}
    rom_resource_cases = sorted(set(re.findall(r"case (SPR_\w+):", data)))
    res = {}
    for sub in ("sprites",):
        for p in sorted((poc / sub).glob("SPR_chaos_*player*")):
            res[p.name] = poc_sprite_facts(poc, p.name)
    legacy = {n: poc_sprite_facts(poc, n) for n in ("SPR_sonic_stop", "SPR_sonic_wait", "SPR_sonic_walk", "SPR_sonic_run", "SPR_sonic_jump", "SPR_sonic_falling",
                                                    "SPR_sonic_spin", "SPR_player_mask")}
    d448 = []
    for f in sorted((poc / "scripts").glob("*/*.gml")):
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if re.search(r"\bd448\s*=[^=]", line) or re.search(r"d448\s*=\s*cp_strong", line):
                d448.append({"file": str(f.relative_to(poc)), "line": i, "text": line.strip()[:160]})
    return {
        "poc_commit": git_head(poc), "evidence": "POC SOURCE (READ-ONLY, text parsed, nothing executed)",
        "presentation_supported_states": {"decimal": supported, "hex": [H(s, 2) for s in supported],
                                          "meaning": "core `next` values whose presentation is driven by chaos_player_animation_program; every other state uses the legacy GameMaker sprite chooser"},
        "programs_by_state": {H(k, 2): v for k, v in sorted(programs.items())},
        "frame_to_sprite_cases": {H(k, 2): v for k, v in sorted(sprite_cases.items())},
        "rom_resource_registration_cases": rom_resource_cases,
        "rom_backed_player_resources": res,
        "legacy_player_resources": legacy,
        "walk_run_in_presentation": {"state_5_walk_supported": 5 in supported, "state_6_run_supported": 6 in supported,
                                     "shadow_tracks_frames": "chaos_player_animation_update tracks selector/frame (cp_a.frame = selector + 1 / 7) for states 5/6 but never presents them; art is the legacy SPR_player_walk/run"},
        "state_12_branch": {"line": next((l.strip() for l in adapter.splitlines() if "cp_state12_visual) cp_sprite" in l), None),
                            "image_index_branch": next((l.strip() for l in adapter.splitlines() if "else if (cp_state12_visual) { image_index = 0" in l), None)},
        "state_12_in_presentation": 18 in supported,
        "d448_writers": d448,
        "strip_marker_in_selector": {"selector_tracking_wrap": "cp_a.selector >= (cp_state == 5 ? 6 : 4) -> 0 (ordinary wrap only, no strip branch)",
                                     "marker_flag_available": "cp_c.special & 1 (set at cp_kind == 25, cleared by SCR_cc_fall / SCR_cc_jump / SCR_cc_anim_update on a non-$19 previous surface)",
                                     "previous_surface_available": "cp_c.previous & 31 == 25"},
    }


def poc_programs_to_frames(program, d448, updates, start_state_change=True):
    """Literal transcription of the record/command interpreter in chaos_player_animation_update (ops 0..4 only).  Returns the frame shown on each update
    of an UNINTERRUPTED stay in one state (ptr=0, counter=0 on entry)."""
    ptr, counter, loop, frame, out = 0, 0, 0, None, []
    for n in range(updates):
        if n > 0 and counter > 1:
            counter -= 1
            out.append(frame)
            continue
        while True:
            op = program[ptr]
            if op[0] == 0:
                counter, frame = op[1], op[2]
                ptr += 1
                break
            if op[0] == 1:
                ptr = 0
            elif op[0] == 2:
                ptr = op[1] if (d448 & 1) else ptr + 1
            elif op[0] == 3:
                loop = op[1]
                ptr += 1
            elif op[0] == 4:
                loop -= 1
                ptr = ptr + 1 if loop == 0 else op[1]
            else:
                raise ValueError("selector op not transcribed")
        out.append(frame)
    return out


def mirror_rows(programs, packed_rows, columns, supported):
    """Feed ROM-observed rows (state requested at the end of the previous update, d448 and requested state at update n) through a transcription of the POC
    selector and return, per update, (rom_frame, poc_frame or None when the POC uses its legacy sprite)."""
    c = {n: i for i, n in enumerate(columns)}
    st = {"state": -1, "ptr": 0, "counter": 0, "loop": 0, "frame": None, "active": False}
    out = []
    prev_req = None
    for r in packed_rows:
        nxt = prev_req if prev_req is not None else r[c["cur"]]
        d448 = r[c["d448"]] if "d448" in c else 0
        out.append((r[c["u"]], r[c["frame"]], poc_step(st, programs, nxt, d448, supported)))
        prev_req = r[c["req"]]
    return out


def poc_step(st, programs, state, d448, supported):
    """One update of the POC selector.  Returns the frame, None when the state is not presented (legacy sprite), or "selector" when the program
    reaches a FF 05 selector op (states $09/$0A/$10/$1B: frames depend on speed and contact inputs and are out of scope here)."""
    changed = st["state"] != state
    st["active"] = state in supported
    if changed:
        st.update(state=state, ptr=0, counter=0, loop=0)
    if not st["active"]:
        return None
    if not changed and st["counter"] > 1:
        st["counter"] -= 1
        return st["frame"]
    prog = programs[state]
    while True:
        op = prog[st["ptr"]]
        if op[0] == 0:
            st["counter"], st["frame"] = op[1], op[2]
            st["ptr"] += 1
            return st["frame"]
        if op[0] == 1:
            st["ptr"] = 0
        elif op[0] == 2:
            st["ptr"] = op[1] if (d448 & 1) else st["ptr"] + 1
        elif op[0] == 3:
            st["loop"] = op[1]
            st["ptr"] += 1
        elif op[0] == 4:
            st["loop"] -= 1
            st["ptr"] = st["ptr"] + 1 if st["loop"] == 0 else op[1]
        else:
            st["frame"] = None
            return "selector"


# ------------------------------------------------------------------------------------------------------------------------------------------
# reused Research evidence (committed caches; no ROM needed) and the assembled outputs
# ------------------------------------------------------------------------------------------------------------------------------------------
CACHES = ("spring-shoes-presentation", "player-spring-airborne", "player-fall-control", "gpz-surface19", "powerup-shoes")


def cache_path(name):
    return ROOT / "data" / "rom-cache" / (name + ".json")


def reused_evidence():
    """Numbers lifted from earlier Research caches, with the cache hashes, so the matrix can say 'existing evidence' precisely."""
    sp = load_json(cache_path("spring-shoes-presentation"))["part_a_presentation"]
    tr = sp["traces"]["mghz1_plain"]
    sa = load_json(cache_path("player-spring-airborne"))
    weak = next(s for s in sa["emulated_flights_thz"]["scenarios"] if s["id"] == "t26_weak_fixed")
    boss = next(s for s in sa["stomp_and_boss"]["scenarios"] if s["id"] == "type50_boss_top_bounce")
    seg_weak = [x for x in weak["state_segments"] if x["state"] == "0x0B"][0]
    fc = load_json(cache_path("player-fall-control"))["part_a_state_14"]
    return {
        "cache_sha256": {n: sha(cache_path(n).read_bytes()) for n in CACHES if cache_path(n).is_file()},
        "spring_shoes_state_12": {
            "source": "data/rom-cache/spring-shoes-presentation.json part_a_presentation (EMULATED ORIGINAL FRAME, MGHZ1 shoes (1552,238))",
            "script": sp["player_state_12_script"]["records"], "script_cpu": sp["player_state_12_script"]["script_cpu"],
            "player_frame_values_in_state_12": tr["player_frame_values_in_state_12"], "player_timer_cycle_first_12": tr["player_timer_cycle_first_12"],
            "player_f4_values_without_input": tr["player_f4_values"], "first_state_12_update": tr["state_12_first_update"],
            "bounce_period_updates": tr["bounce_period_updates"], "shoe_frame_changes_per_bounce": 2,
            "facing": "+$04 bit 4 follows Left/Right (left_right run: values {0,16}); Sonic never mirrored by anything else",
        },
        "weak_spring_t26": {
            "source": "data/rom-cache/player-spring-airborne.json emulated_flights_thz/t26_weak_fixed", "entry_d448": weak["rows"][5][10],
            "state_segment": {k: seg_weak[k] for k in ("first_update", "updates", "frames")},
        },
        "boss_bounce_t50": {"source": "player-spring-airborne.json stomp_and_boss/type50_boss_top_bounce",
                            "frames_first_segment": [x for x in boss["state_segments"] if x["state"] == "0x0B"][0]["frames"][:3]},
        "strip_fall_14": {"source": "player-fall-control.json part_a_state_14 (GPZ2 / MGHZ1)", "setter_4663": fc["setter_diff"]["facts"] if "facts" in fc["setter_diff"] else None},
    }


def build_static(rom):
    out = poc_free_static(rom)
    out["reused_evidence"] = reused_evidence()
    return out


def build_observed(rom):
    return {"rom_sha256": ROM_SHA256, "research_base": BASE_COMMIT, **observed(rom)}


def poc_images(poc, name):
    """Frames of a POC sprite as PIL images in .yy order, with the GameMaker origin."""
    from PIL import Image
    d = Path(poc) / "sprites" / name
    t = (d / (name + ".yy")).read_text(encoding="utf-8")
    ids = re.findall(r'"(?:%Name|name)":\s*"([0-9a-f-]{36})"', t)
    seen, ordered = set(), []
    for i in ids:
        if i not in seen and (d / (i + ".png")).is_file():
            seen.add(i)
            ordered.append(i)
    f = poc_sprite_facts(poc, name)
    return [Image.open(d / (i + ".png")).convert("RGBA") for i in ordered], (f["xorigin"], f["yorigin"])


def poc_pixel_parity(rom, poc):
    """Compare every imported POC player frame resource that has a ROM frame in this tool with the ROM render (THZ1 palette) and the GameMaker origin rule."""
    out = {}
    for fid in ALL_FRAMES:
        name = "SPR_chaos_player_frame_%02X" % fid
        if not (Path(poc) / "sprites" / name).is_dir():
            out[H(fid, 2)] = {"poc_resource": None}
            continue
        ims, org = poc_images(poc, name)
        im, o2 = rom_frame_image(rom, fid)
        out[H(fid, 2)] = {"poc_resource": name, "frames": len(ims), "size_equal": ims[0].size == im.size, "origin_equal": tuple(org) == tuple(o2),
                          "rgba_equal": ims[0].tobytes() == im.tobytes()}
    return out


def rom_frame_image(rom, fid, face=0):
    from PIL import Image
    pal = A.palette_rgba(rom, int(PSA.palette_selectors(rom)["thz1"]["sprite"], 16))
    parsed, source, w, h, rgba, meta, cpu, mp = PSA.render_frame_rgba(rom, fid, pal)
    im = Image.frombytes("RGBA", (w, h), bytes(rgba))
    b = meta["bounds"]
    origin = (-b["min_x"], -b["min_y"])
    if face:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
        origin = (w - origin[0], origin[1])
    return im, origin


def sheet(path, title, rows, scale=3, cell=(150, 176), anchor_color=(255, 0, 255, 255)):
    """rows: list of (row label, [(caption, PIL image, (ox, oy) origin) ...]); every image is drawn with its origin on a magenta cross."""
    from PIL import Image, ImageDraw
    pad, lab_w, head = 8, 190, 28
    ncol = max(len(r[1]) for r in rows)
    cw, ch = cell
    W = lab_w + ncol * (cw + pad) + pad
    Hh = head + len(rows) * (ch + pad + 14) + pad
    im = Image.new("RGBA", (W, Hh), (40, 44, 52, 255))
    dr = ImageDraw.Draw(im)
    dr.text((pad, 8), title, fill=(255, 255, 255, 255))
    for ri, (label, items) in enumerate(rows):
        y0 = head + ri * (ch + pad + 14)
        dr.text((pad, y0 + 4), label, fill=(210, 220, 255, 255))
        for ci, (cap, img, (ox, oy)) in enumerate(items):
            x0 = lab_w + ci * (cw + pad)
            dr.rectangle([x0, y0, x0 + cw, y0 + ch], fill=(18, 18, 24, 255))
            big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
            cx, cy = x0 + cw // 2, y0 + ch - 70
            px, py = cx - ox * scale, cy - oy * scale
            im.paste(big, (px, py), big)
            dr.line([cx - 6, cy, cx + 6, cy], fill=anchor_color)
            dr.line([cx, cy - 6, cx, cy + 6], fill=anchor_color)
            dr.text((x0 + 3, y0 + ch + 1), cap, fill=(200, 200, 200, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(path)
    return sha(im.convert("RGB").tobytes())


def build_sheets(rom, poc, out_dir):
    out = {}
    R = lambda fid, face=0: rom_frame_image(rom, fid, face) + ()
    rows = [("ROM strip $3C-$3F", [("$%02X" % f, *rom_frame_image(rom, f)) for f in (0x3C, 0x3D, 0x3E, 0x3F)]),
            ("ROM ordinary run $07-$0A", [("$%02X" % f, *rom_frame_image(rom, f)) for f in (7, 8, 9, 0x0A)])]
    if poc:
        for n in ("SPR_sonic_run", "SPR_sonic_walk"):
            ims, org = poc_images(poc, n)
            rows.append(("POC legacy " + n, [("f%d" % i, im, org) for i, im in enumerate(ims[:6])]))
    out["u5a-strip-run.png"] = sheet(out_dir / "u5a-strip-run.png", "A: strip run frames (ROM) vs current POC walk/run art", rows)
    rows = [("ROM $0B right / left", [("$0B R", *rom_frame_image(rom, 0x0B)), ("$0B L", *rom_frame_image(rom, 0x0B, 1))])]
    if poc:
        for n in ("SPR_sonic_jump", "SPR_sonic_stop", "SPR_sonic_wait"):
            ims, org = poc_images(poc, n)
            rows.append(("POC legacy " + n, [("f%d" % i, im, org) for i, im in enumerate(ims[:6])]))
    out["u5a-spring-shoes-pose.png"] = sheet(out_dir / "u5a-spring-shoes-pose.png", "B: Spring Shoes pose - ROM frame $0B vs the POC sprite used today (SPR_player_jump)", rows)
    rows = [("ROM tumble $1C-$21", [("$%02X" % f, *rom_frame_image(rom, f)) for f in range(0x1C, 0x22)])]
    if poc:
        rows.append(("POC SPR_chaos_player_frame_1C..21", [(n[-2:], *(lambda r: (r[0][0], r[1]))(poc_images(poc, n))) for n in
                                                          ["SPR_chaos_player_frame_%02X" % f for f in range(0x1C, 0x22)]]))
        for n in ("SPR_sonic_jump", "SPR_sonic_falling"):
            ims, org = poc_images(poc, n)
            rows.append(("POC legacy " + n, [("f%d" % i, im, org) for i, im in enumerate(ims[:6])]))
    out["u5a-tumble.png"] = sheet(out_dir / "u5a-tumble.png", "C: tumble set $1C-$21 (ROM) vs imported POC resources vs legacy jump/fall", rows)
    return out


# ------------------------------------------------------------------------------------------------------------------------------------------
# consistency checks (no ROM needed) - used by --validate and by tests/test_u5a_player_presentation.py
# ------------------------------------------------------------------------------------------------------------------------------------------
def validate(static, observed_, poc=None):
    """Raises AssertionError with the failing statement; returns the number of assertions made."""
    n = [0]

    def ok(cond, msg):
        n[0] += 1
        if not cond:
            raise AssertionError(msg)

    fr = static["frames"]["frames"]
    ok(sorted(fr) == [H(f, 2) for f in ALL_FRAMES], "frame list")
    for f in (0x3C, 0x3D, 0x3E, 0x3F):
        b = fr[H(f, 2)]["bounds_relative_to_player_anchor"]
        ok((b["min_x"], b["min_y"], b["max_x"], b["max_y"]) == (-12, -28, 12, 4), "strip frame bounds %02X" % f)
        ok(fr[H(f, 2)]["gamemaker_origin_x"] == 12 and fr[H(f, 2)]["gamemaker_origin_y"] == 28, "strip origin")
        ok(fr[H(f, 2)]["graphics_transfer"]["tile_count"] == 12 and fr[H(f, 2)]["graphics_transfer"]["vram_destination"] == "0x0000", "strip tiles")
    b = fr["0x0B"]["bounds_relative_to_player_anchor"]
    ok((b["min_x"], b["min_y"], b["max_x"], b["max_y"]) == (-10, -32, 14, 0), "frame 0B bounds")
    ok(fr["0x0B"]["graphics_transfer"]["tile_count"] == 10, "frame 0B tile count")
    ok(len({fr[H(f, 2)]["index_sha256"] for f in (0x3C, 0x3D, 0x3E, 0x3F)}) == 4, "strip frames are four different images")
    sp = static["sprite_palettes"]
    ok(sp["sonic_colours_identical_in_all_acts"] and sp["indices_used_union"] == list(range(1, 12)), "Sonic palette identical in every act")
    sel = static["selectors"]
    ok(sel["walk_selector"]["strip"]["frames"] == [0x3C, 0x3D, 0x3E, 0x3F] and sel["run_selector"]["strip"]["frames"] == [0x3C, 0x3D, 0x3E, 0x3F], "strip frames")
    ok(sel["walk_selector"]["ordinary"]["cycle_length"] == 6 and sel["run_selector"]["ordinary"]["cycle_length"] == 4, "cycle lengths")
    ok(static["strip_census"]["acts_with_strips"] == list(STRIP_ACTS), "strip census")
    sc = static["state_programs"]
    ok([r["frame"] for r in sc["0x12"]["program"] if "frame" in r] == [0x0B], "state $12 has a single frame $0B record")
    ok(sc["0x14"]["play_order"]["cycle_updates"] == 24 and sc["0x1C"]["play_order"]["cycle_updates"] == 48, "tumble cycle lengths")
    ok(sc["0x0B"]["play_order_d448_bit0_clear_weak"]["cycle_updates"] == 82, "weak spring cycle")
    cases = {c["id"]: c for c in observed_["cases"]}
    col = {nme: i for i, nme in enumerate(observed_["columns"])}
    # strip cases: after the carried-over record the run uses ONLY the strip set, every record is 4 updates, order follows the shared index
    for cid in ("gpz2_strip_run_right", "mghz1_upper_strip_run_right", "mghz1_upper_strip_run_left"):
        c = cases[cid]
        runs = c["summary"]["frame_runs_by_executing_state"]["0x06"]
        strip = [r for r in runs if r[0] in ("0x3C", "0x3D", "0x3E", "0x3F")]
        ok(len(strip) >= 8, cid + ": strip frames present")
        ok(all(r[1] == 4 for r in strip[:-1]), cid + ": 4 updates per strip frame")
        order = [int(r[0], 16) - 0x3C for r in strip]
        ok(all((order[i + 1] - order[i]) % 4 == 1 for i in range(len(order) - 1)), cid + ": index order")
        ok(c["summary"]["marker_values"] == [1], cid + ": marker set while on the strip")
    ok(cases["mghz1_upper_strip_run_left"]["summary"]["facing_values"] == [1], "left-facing synthetic")
    for cid in ("gpz2_ordinary_run_marker_clear", "gpz2_ordinary_run_marker_set"):
        runs = cases[cid]["summary"]["frame_runs_by_executing_state"]["0x06"]
        ok(all(r[0] in ("0x07", "0x08", "0x09", "0x0A") for r in runs), cid + ": ordinary run frames only")
        ok(cases[cid]["summary"]["marker_values"] == [0], cid + ": marker cleared by the selector")
    for cid in ("gpz2_platform28_stand", "gpz2_platform28_walk_right", "gpz1_platform28_moving_stand", "gpz2_deck_1c_walk_run"):
        s = cases[cid]["summary"]
        ok(s["marker_values"] == [0], cid + ": riding is not the strip marker")
        allf = {f for v in s["frame_runs_by_executing_state"].values() for f, _ in v}
        ok(not (allf & {"0x3C", "0x3D", "0x3E", "0x3F"}), cid + ": no strip frame while riding/deck walking")
    ok(cases["gpz2_platform28_stand"]["summary"]["frame_runs_by_executing_state"]["0x01"][0][0] == "0x0B", "standing on a type-$28 platform shows frame $0B")
    f = cases["gpz2_strip_walk_plus3_right"]
    ok(f["summary"]["first_update_with_requested_14"] == 1, "walk +3.0 on the strip requests $14 on update 1")
    t14 = f["summary"]["frame_runs_by_executing_state"]["0x14"]
    ok([r[0] for r in t14[:6]] == ["0x1C", "0x1D", "0x1E", "0x1F", "0x20", "0x21"] and all(r[1] == 4 for r in t14[:6]), "strip fall: tumble set at 4 updates each")
    ok(cases["gpz2_strip_stand"]["summary"]["first_update_with_requested_14"] is None, "idle on the strip is not a strip fall")
    if poc is not None:
        programs = {int(k, 16): v for k, v in poc["programs_by_state"].items()}
        supported = set(poc["presentation_supported_states"]["decimal"])
        ok(supported == {9, 10, 11, 14, 16, 20, 27, 28, 33}, "POC supported presentation states")
        pp = poc["pixel_parity_with_rom_frames"]
        for f in (1, 2, 3, 4, 5, 6, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x61):
            ok(pp[H(f, 2)]["poc_resource"] and pp[H(f, 2)]["rgba_equal"] and pp[H(f, 2)]["origin_equal"] and pp[H(f, 2)]["size_equal"], "POC frame %02X equals the ROM frame" % f)
        for f in (7, 8, 9, 0x0A, 0x0B, 0x3C, 0x3D, 0x3E, 0x3F, 0x5E):
            ok(pp[H(f, 2)]["poc_resource"] is None, "POC has no resource for ROM frame %02X" % f)
        ok(5 not in supported and 6 not in supported and 1 not in supported and 18 not in supported, "walk, run, idle and Spring Shoes are not presented from ROM frames")
        for c in observed_["cases"]:
            res = mirror_rows(programs, c["rows"], c["columns"], supported)
            for u, rf, pf in res:
                if isinstance(pf, int):
                    ok(rf == pf, "%s update %d: ROM frame %02X vs POC mirror %02X" % (c["id"], u, rf, pf))
    return n[0]


# ------------------------------------------------------------------------------------------------------------------------------------------
def write_all(rom, only=None, poc=None, progress=print):
    DATA.mkdir(parents=True, exist_ok=True)
    out = {}
    st = build_static(rom)
    frame_table(rom, BUILD / "frames")
    out[STATIC_JSON] = dumps(st)
    progress("static layer done")
    if only != "static":
        ob = build_observed(rom)
        out[OBS_JSON] = dumps(ob)
        progress("observed layer done (%d cases)" % len(ob["cases"]))
    if poc:
        pf = poc_source_facts(poc)
        pf["pixel_parity_with_rom_frames"] = poc_pixel_parity(rom, poc)
        out[POC_JSON] = dumps(pf)
        BUILD.mkdir(parents=True, exist_ok=True)
        sheets = build_sheets(rom, poc, BUILD / "sheets")
        progress("POC layer done; sheets: " + ", ".join(sorted(sheets)))
    manifest = {"rom_sha256": ROM_SHA256, "frames": {H(f, 2): {"png": "build/u5a/frames/frame-%02X.png" % f, "index_sha256": st["frames"]["frames"][H(f, 2)]["index_sha256"],
                                                                "rgba_sha256_thz1_palette": st["frames"]["frames"][H(f, 2)]["rgba_sha256_thz1_palette"]} for f in ALL_FRAMES},
                "note": "ignored build/u5a/ holds the ROM-derived indexed/RGBA frame PNGs and the comparison sheets; regenerate with this tool"}
    out[EXPORT_JSON] = dumps(manifest)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--only", choices=("static", "all"), default="all")
    ap.add_argument("--poc", type=Path, help="POC checkout (read only): regenerates data/u5a/player-poc-source.json and the comparison sheets")
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.validate:
        n = validate(load_json(STATIC_JSON), load_json(OBS_JSON), load_json(POC_JSON) if POC_JSON.is_file() else None)
        print("validate: %d assertions" % n)
        return
    if a.rom is None:
        ap.error("ROM path required")
    rom = load_rom(a.rom)
    out = write_all(rom, None if a.only == "all" else "static", a.poc)
    if a.check:
        bad = [str(p.relative_to(ROOT)) for p, text in out.items() if p.read_text(encoding="utf-8") != text]
        if bad:
            raise SystemExit("MISMATCH: " + ", ".join(bad))
        print("u5a player presentation: committed data match the ROM-derived regeneration")
        return
    for p, text in out.items():
        p.write_text(text, encoding="utf-8")
        print("wrote", p.relative_to(ROOT), len(text))


if __name__ == "__main__":
    main()

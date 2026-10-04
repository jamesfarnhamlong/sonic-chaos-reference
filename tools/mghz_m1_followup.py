#!/usr/bin/env python3
"""MGHZ M1 Windows follow-up audit (Research only, deterministic).

Three narrow questions from the first MGHZ Windows test:
  A. a rising type-$28 platform carries Sonic into overhead terrain;
  B. the animated tile strip $1A8/$1A9 (which scenery, and is a thin horizontal line ROM art?);
  C. does breakable block $0D (blocks $9B/$9C -> $9D) have any presentation change before/during destruction?

Output: data/rom-cache/mghz/m1-windows-followup.json (numeric labels; hashes only, no ROM bytes, no pixels).
Optional: --png DIR writes review renders (needs nothing beyond the standard library; DIR is git-ignored build output).

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT (original Z80 routines), EMULATED ORIGINAL FRAME
(whole game in tools/sms_frame_harness.py booted into MGHZ, PC hooks), SYNTHETIC CONTROL (a layout cell patched in RAM; never a canonical placement), UNRESOLVED.

Usage:
  python tools/mghz_m1_followup.py ROM.sms [--check] [--static-only] [--png DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import isometric_platform as I          # noqa: E402  (act_data)
import level_package as L               # noqa: E402
import mghz_foundation as F             # noqa: E402
import mghz_object_census as C          # noqa: E402
import mghz_surface_ceiling as M        # noqa: E402  (GameLab, header_facts)
import platform_spike_collision as P    # noqa: E402
import rom as R                         # noqa: E402
import thz1_object_assets as G          # noqa: E402

OUTPUT = ROOT / "data" / "rom-cache" / "mghz" / "m1-windows-followup.json"
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
RESEARCH_BASE = "7315df2"
ACTS = M.ACTS
PAD_B1 = 16

# named routines (CPU addresses; fixed bank 1 unless noted)
CEILING_PASS = 0x73C9
CEILING_0D = 0x7464
BREAK = 0x7898
CRUSH_DEATH = 0x4984
FLOOR_0D = 0x6B2C
SIDE_R_0D, SIDE_L_0D = 0x72B6, 0x72DD
TERRAIN_PASS = 0x690B
PLATFORM_CARRY, PLATFORM_SUPPORT = 0x88A0, 0x8814
FRAGMENT_INIT_CB = 0x9B11            # bank $0C
FRAGMENT_TABLES = (0x9B75, 0x9B95)    # bank $0C: player X speed >= 0 / < 0

HOOKS = {0x3FEF: "player_update", 0x402A: "x_integration", 0x4097: "y_integration", TERRAIN_PASS: "terrain_pass", 0x691A: "terrain_floor", 0x715E: "terrain_sides",
         CEILING_PASS: "terrain_ceiling", CEILING_0D: "ceiling_surface_0d", BREAK: "break_7898", CRUSH_DEATH: "crush_death_4984", 0x60FB: "object_move",
         PLATFORM_SUPPORT: "platform_support", 0x6328: "overlap_6328", PLATFORM_CARRY: "platform_carry", 0x23F9: "nametable_refresh_23f9", 0x5E9C: "spawn_object_5e9c"}


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def s16(v: int) -> int:
    return (v + 32768) % 65536 - 32768


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos research ROM")


def squash(seq) -> list:
    out = []
    for n in seq:
        if not out or out[-1] != n:
            out.append(n)
    return out


# --------------------------------------------------------------------------- #
# whole-game rig
# --------------------------------------------------------------------------- #
class Rig:
    """GameLab (original game booted into an MGHZ act) plus extra PC hooks.  Cases restore the settled snapshot."""

    def __init__(self, rom: bytes, key: str):
        self.rom, self.key = rom, key
        self.lab = M.GameLab(rom, key)
        self.s, self.m = self.lab.s, self.lab.m
        self.width = I.act_data(rom, key)["width"]
        self.ev: list = []
        self.cap: dict = {}
        for a, name in HOOKS.items():
            self.s.add_pc_hook(a, lambda mm, n=name, a=a: self._hit(n, a))

    def _hit(self, name: str, addr: int) -> None:
        self.ev.append(name)
        if addr == TERRAIN_PASS:
            self.cap["pass_y"], self.cap["pass_vy"] = self.s.u16(0xD514), s16(self.s.u16(0xD518))
        elif addr == CEILING_0D:
            self.cap["ceil0d_y"], self.cap["ceil0d_d3c0"] = self.s.u16(0xD514), self.m[0xD3C0]
        elif addr == BREAK:
            self.cap["break_pass_y"] = self.s.u16(0xD514)
            self.cap["break_cell_ptr"] = self.m[0xD354] | self.m[0xD355] << 8
        elif addr == CRUSH_DEATH:
            self.cap["death_pass_y"] = self.s.u16(0xD514)
            self.cap["death_d3c0"] = self.m[0xD3C0]

    def cell(self, cx: int, cy: int) -> int:
        return self.m[0xC001 + cy * self.width + cx]

    def platform_slot(self, x: int):
        for i in range(19):
            b = 0xD540 + i * 0x40
            if self.m[b] == 0x28 and abs(self.s.u16(b + 0x11) - x) < 5:
                return b
        return None

    def start(self, x, y, vy=0x100, cur=0x0E, f3=1, rings=0, patch=None, vx=0, floor=False) -> None:
        lab = self.lab
        lab.e.restore()
        lab.e.place(x, y, vx, vy, cur=cur, f3=f3, floor=floor, rings=rings)
        for (cx, cy), blk in (patch or {}).items():
            self.m[0xC001 + cy * self.width + cx] = blk
        self.lab.pending.clear()
        self.lab.pending_info.clear()
        self.ev.clear()
        self.cap.clear()

    def frame(self, platform_x: int, pad: int = 0) -> dict:
        s, m = self.s, self.m
        self.ev.clear()
        self.cap.clear()
        s.pad = pad
        s.run_frame()
        game_events = list(self.lab.pending)
        self.lab.pending.clear()
        self.lab.pending_info.clear()
        b = self.platform_slot(platform_x)
        row = {"y": s.u16(0xD514), "x": s.u16(0xD511), "vx": s16(s.u16(0xD516)), "vy": s16(s.u16(0xD518)), "cur": m[0xD501], "req": m[0xD502], "f3": m[0xD503], "f22": m[0xD522],
               "f23": m[0xD523], "d3c0": m[0xD3C0], "rings": m[0xD29A], "plat_y": s.u16(b + 0x14) if b else None, "plat_state": m[b + 1] if b else None,
               "plat_latch": m[b + 0x31] if b else None, "ev": squash(self.ev + game_events), "cap": dict(self.cap)}
        return row

    def ride(self, platform_x, y, frames, jump=(), vy=0x100, cur=0x0E, f3=1, rings=0, patch=None, retained_vy=None, until=None) -> list:
        self.start(platform_x, y, vy=vy, cur=cur, f3=f3, rings=rings, patch=patch)
        rows, claimed = [], False
        for f in range(frames):
            row = self.frame(platform_x, PAD_B1 if f in jump else 0)
            row["u"] = f
            if retained_vy is not None and not claimed and row["d3c0"] != 0:
                claimed = True
                self.s.w16(0xD518, retained_vy)
                row["vy_overwritten_to"] = retained_vy
            rows.append(row)
            if until and until(row, rows):
                break
        return rows


def first(rows, pred):
    for r in rows:
        if pred(r):
            return r
    return None


def compact(r: dict, keys=("u", "y", "vy", "cur", "f3", "f22", "f23", "d3c0", "plat_y", "ev")) -> dict:
    return {k: r.get(k) for k in keys if k in r}


# --------------------------------------------------------------------------- #
# A. rising platform into overhead terrain
# --------------------------------------------------------------------------- #
def disasm_slice(rom: bytes, start: int, end: int, bank_file: int = 0) -> list:
    from z80dis import z80
    out, a = [], start
    while a < end:
        off = bank_file + (a - (0x8000 if bank_file else 0))
        d = z80.decode(rom[off:off + 4], a)
        out.append(f"{a:04X} {rom[off:off + d.len].hex(' ')} | {z80.disasm(d)}")
        a += d.len
    return out


def platform_scan(rom: bytes) -> dict:
    """Every vertical type-$28 mover in MGHZ1-3 and the overhead blocks on its head-probe path (static, DECODED + BYTE-VERIFIED probe rule)."""
    out = {}
    for key in ACTS:
        a = I.act_data(rom, key)
        w, cells = a["width"], a["cells"][:4095]
        rows = []
        rec = C.decode_records(rom)[key]["records"]
        for r in rec:
            if r["type_id"] != "0x28":
                continue
            p = int(r["parameter"], 16)
            aux1 = int(r["aux1"], 16)
            state = 13 if (p & 0x7F) in (5, 11) else (p & 0x3F) + 1
            vertical = (p & 0x7F) in (5, 11) or state in (2, 6, 11, 12)
            if not vertical:
                continue
            x, y0 = r["world_x"], r["world_y"]
            travel = 16 * aux1
            seen = {}
            for dy in range(travel + 1):
                head = y0 - dy - 14 - 6      # carried rider anchor (platform Y - 14) minus the ceiling probe offset (-6)
                if head < 0:
                    break
                cy = head // 32
                blk = cells[cy * w + x // 32]
                hf = M.header_facts(rom, blk)
                fl = int(hf["flags"], 16)
                if fl & 0xC0:
                    k = (cy, hf["block"])
                    e = seen.setdefault(k, {"cell": [x // 32, cy], "block": hf["block"], "flags": hf["flags"], "surface_type": hf["surface_type"], "platform_y_first": y0 - dy, "platform_y_last": y0 - dy})
                    e["platform_y_last"] = y0 - dy
            rows.append({"record_index": r["index"], "world": [x, y0], "parameter": r["parameter"], "aux1": r["aux1"], "initial_state": state, "state_after_touch": (p & 0x3F) + 1,
                         "travel_updates_up": travel, "overhead_hits": sorted(seen.values(), key=lambda e: -e["platform_y_first"])})
        out[key] = rows
    return out


def fixture_row(r: dict) -> dict:
    d = compact(r, ("u", "y", "vy", "cur", "f3", "f22", "f23", "d3c0", "plat_y", "ev"))
    if r.get("cap"):
        d["cap"] = r["cap"]
    return d


def ride_death(rig: Rig, px: int, plat_y: int, first_row: int, rings: int) -> dict:
    """Natural ride: fall onto the touch-start platform from 39 px above it and do nothing."""
    start_y = plat_y - 39
    rows = rig.ride(px, start_y, 160, rings=rings, until=lambda r, rs: "crush_death_4984" in r["ev"])
    claim = first(rows, lambda r: r["d3c0"] != 0)
    death = first(rows, lambda r: "crush_death_4984" in r["ev"])
    after = rig.frame(px)
    after2 = rig.frame(px)
    out = {"start": {"x": px, "y": start_y, "vy": 0x100, "cur": 14, "f3": 1, "rings_bcd": rings, "platform": [px, plat_y]},
           "support_claim_update": claim["u"] if claim else None, "death_update": death["u"] if death else None,
           "platform_y_at_start_of_death_update": rows[-2]["plat_y"] if len(rows) > 1 else None, "player_y_in_death_pass": death["cap"].get("death_pass_y") if death else None,
           "first_fatal_platform_y_rule": f"platform Y at the start of an update <= (bottom row of the overhead $0D cell) + 20 = {first_row * 32 + 31 + 20}",
           "death_d3c0": death["cap"].get("death_d3c0") if death else None, "events_in_death_update": death["ev"] if death else None,
           "rows_around_death": [fixture_row(r) for r in rows[-6:]],
           "after_death_updates": [fixture_row(dict(after, u="+1")), fixture_row(dict(after2, u="+2"))],
           "player_state_after": {"cur": after["cur"], "req": after["req"], "f3": after["f3"], "vy": after["vy"], "rings": after["rings"]},
           "platform_frozen_after_death": after2["plat_y"] == after["plat_y"]}
    return out


def jump_window(rig: Rig, px: int, plat_y: int) -> dict:
    """Jump press at every update 20..109: does the head reach the breakable cell (break), or does the rider die, or neither within the window?"""
    start_y = plat_y - 39
    table = []
    for j in range(20, 110):
        rows = rig.ride(px, start_y, j + 90, jump=(j, j + 1, j + 2), until=lambda r, rs: "crush_death_4984" in r["ev"] or "break_7898" in r["ev"])
        last = rows[-1]
        outcome = "break" if "break_7898" in last["ev"] else "death" if "crush_death_4984" in last["ev"] else "none"
        table.append({"jump_update": j, "outcome": outcome, "update": last["u"], "pass_y": (last["cap"].get("break_pass_y") or last["cap"].get("death_pass_y")),
                      "vy_after": last["vy"] if outcome != "none" else None})
    runs, cur = [], None
    for t in table:
        if cur and cur["outcome"] == t["outcome"]:
            cur["to"] = t["jump_update"]
        else:
            cur = {"outcome": t["outcome"], "from": t["jump_update"], "to": t["jump_update"]}
            runs.append(cur)
    return {"start": {"x": px, "y": start_y, "platform": [px, plat_y]}, "press": "B1 held for 3 updates starting at jump_update", "outcome_runs": runs,
            "samples": [t for t in table if t["jump_update"] in (20, 55, 56, 60, 80, 100, 101, 102, 103, 104)]}


def break_by_jump(rig: Rig, px: int, plat_y: int, j: int) -> dict:
    start_y = plat_y - 39
    rows = rig.ride(px, start_y, j + 70, jump=(j, j + 1, j + 2), until=lambda r, rs: "break_7898" in r["ev"])
    ev = rows[-1]
    cell = (px // 32, None)
    nxt = [rig.frame(px) for _ in range(3)]
    return {"jump_update": j, "break_update": ev["u"], "player_y_in_break_pass": ev["cap"].get("break_pass_y"), "vy_in_break_update": ev["vy"], "d3c0_in_break_update": ev["d3c0"],
            "events": ev["ev"], "rows": [fixture_row(r) for r in rows[-4:]], "after": [fixture_row(dict(r, u=f"+{i + 1}")) for i, r in enumerate(nxt)]}


def one_way_snap(rig: Rig, px: int, plat_y: int, block_row: int, retained=None) -> dict:
    start_y = plat_y - 39
    top = block_row * 32
    rows = rig.ride(px, start_y, 520, retained_vy=retained, until=lambda r, rs: r["d3c0"] == 0 and len(rs) > 20 and rs[-2]["d3c0"] != 0)
    snap = rows[-1]
    prev = rows[-2]
    snapped = snap["d3c0"] == 0 and prev["d3c0"] != 0
    if not snapped:
        return {"snapped": False}
    pass_y = snap["cap"].get("pass_y")
    return {"retained_vy": retained if retained is not None else "natural", "snapped": True, "snap_update": snap["u"], "player_y_in_pass": pass_y, "player_y_after": snap["y"],
            "platform_y_in_pass": prev["plat_y"], "feet_depth_in_block": (pass_y + 18) - top if pass_y is not None else None, "pass_vy": snap["cap"].get("pass_vy"),
            "y_delta": snap["y"] - prev["y"], "floor_flag_after": snap["f22"], "support_after": snap["d3c0"], "vy_after": snap["vy"],
            "block_top_y": top, "standing_anchor": top - 18, "rows": [fixture_row(r) for r in rows[-4:]]}


def one_way_depth_sweep(rig: Rig, px: int, plat_y: int, block_row: int) -> dict:
    out = []
    for v in (0x000, 0x100, 0x200, 0x300, 0x370, 0x400, 0x500, 0x700):
        r = one_way_snap(rig, px, plat_y, block_row, retained=v)
        out.append({"retained_vy": v, "snap_update": r.get("snap_update"), "feet_depth_in_block": r.get("feet_depth_in_block"), "model_depth": 8 + (v >> 8),
                    "player_y_in_pass": r.get("player_y_in_pass"), "player_y_after": r.get("player_y_after")})
    return {"model": "one-way capture depth = 8 + (retained Y speed >> 8) rows (docs/platform-spike-collision-audit.md 1.5); the carried rider passes through the 32-px-thick one-way block (feet deeper than the depth), "
                     "then snaps to the block's upper surface in the first pass whose feet depth is within the band",
            "rows": out, "matches_model": all(t["feet_depth_in_block"] == t["model_depth"] for t in out if t["snap_update"] is not None)}


def solid_control(rig: Rig) -> dict:
    """SYNTHETIC CONTROL (not a canonical placement): the same MGHZ2 shaft with cells (86,13..15) patched to ordinary solid block $01."""
    px, plat_y = 2768, 624
    rows = rig.ride(px, plat_y - 39, 150, patch={(86, 13): 0x01, (86, 14): 0x01, (86, 15): 0x01})
    bounce = [r["u"] for r in rows if "ceil_bounce" in " ".join(r["ev"]) or "bounce" in r["ev"]]
    pop = first(rows, lambda r: r["u"] > 100 and r["plat_y"] is not None and r["y"] - r["plat_y"] < -20)
    return {"patched_cells": [[86, 13, "0x01"], [86, 14, "0x01"], [86, 15, "0x01"]],
            "ceiling_bounce_updates": bounce, "first_pop_update": pop["u"] if pop else None,
            "rows_around_first_contact": [fixture_row(r) for r in rows[102:110]],
            "rows_around_pop": [fixture_row(r) for r in rows[(pop["u"] - 3 if pop else 125):(pop["u"] + 5 if pop else 133)]],
            "reading": "ordinary solid ceiling with a supported rider: the ceiling pass pushes down / sets Y speed +1.0 but the platform carry (later in the same update) re-places the rider at platform Y - 14, so he stays "
                       "inside the block; once his FEET sample is inside solid blocks the floor projection moves him up to the top of the solid column (one cell per update here). Not an MGHZ placement."}


def update_order(rig: Rig, px: int, plat_y: int) -> dict:
    rig.start(px, plat_y - 39)
    seq = []
    for f in range(40):
        rig.ev.clear()
        rig.s.pad = 0
        rig.s.run_frame()
        if f == 39:
            seq = squash(rig.ev)
    return {"events_in_one_update_while_riding": seq,
            "reading": "player callback first ($3FEF: X/Y integration, terrain pass: floor, sides, ceiling), then the platform callback (move, support $8814, overlap $6328, carry $88A0 = Y := platform Y - 14)."}


def part_a(rig_ref: dict) -> dict:
    rom = rig_ref["rom"]
    scan = platform_scan(rom)
    r2 = rig_ref["mghz2"]
    r1 = rig_ref["mghz1"]
    out = {
        "scope": "type $28 vertical movers in MGHZ1-3 whose carried rider meets overhead terrain",
        "platform_family": {"state_13": "stationary contact platform ($85FE): waits for a contact flag, then enters the touch-start mover", "state_6": "touch-started vertical mover ($87B2): latch +$31 0 -> 1 on any "
                            "contact bit, then the lift callback $86DA (Y speed -1.0 per update, reversal period 16 x aux1 updates via $8925); keeps running without a rider once started",
                            "parameter_rule": "param $05 -> state 13 -> 6; param $0A (also forced rule for $0B) -> state 11 lift"},
        "placements": scan,
        "overhead_summary": {"breakable_0d_shafts": ["mghz2 #12 (2768,624) param $05 aux1 $19: column x cells 86, rows 15..8 = block $9C (surface $0D), then row 7 = $F9 (one-way)",
                                                       "mghz2 #13 (3024,560) param $05 aux1 $14: column x cell 94, rows 12..8 = $9C, then row 7 = $F9"],
                             "one_way_ledges": ["mghz1 #10 (2768,414) param $05 aux1 $0C: row 7 block $F9 ($41, one-way surface type 1)", "mghz1 #11 (2960,830) param $05 aux1 $1C: row 12 block $F9"],
                             "plain_solid_ceilings": "none: no MGHZ vertical-mover path meets an ordinary solid (bit 7, non-$0D) block",
                             "no_overhead_terrain": ["mghz1 #9", "mghz2 #3", "mghz2 #4", "mghz2 #14"]},
        "ceiling_rule": {"entry": "$73C9: runs when the support owner $D3C0 != 0 (rider) or (floor flag clear and Y speed negative); probe = player (X, Y - 24 + 18) = (X, Y - 6); dispatch on terrain type",
                         "type_0d_7464": "$D3C0 == 0 -> $7898 (break); $D3C0 != 0 -> JP $4984 (crush death: requested state $1F, +$03 bit 0, +$04 := 0, Y speed := $FB00 (-5.0), $D375 := 0, +$22 bit 1 cleared, "
                                         "zone < 8: $D293 bit 2, $D44B &= $80, sound $96 via $062D)",
                         "type_0d_has_no_ring_or_invulnerability_gate": True},
        "assembly": {"ceiling_73c9": disasm_slice(rig_ref["rom"], 0x73C9, 0x7416), "ceiling_0d_7464": disasm_slice(rig_ref["rom"], 0x7464, 0x746E), "crush_death_4984": disasm_slice(rig_ref["rom"], 0x4984, 0x49C3)},
        "update_order": update_order(r2, 2768, 624),
    }
    # fixtures
    fx = {}
    fx["mghz2_12_ride_into_breakable_0d"] = {"rings_0": ride_death(r2, 2768, 624, 15, 0), "rings_5": ride_death(r2, 2768, 624, 15, 5)}
    fx["mghz2_13_ride_into_breakable_0d"] = {"rings_0": ride_death(r2, 3024, 560, 12, 0)}
    fx["mghz2_12_jump_window"] = jump_window(r2, 2768, 624)
    fx["mghz2_12_break_by_jump"] = break_by_jump(r2, 2768, 624, 60)
    fx["mghz1_10_one_way_snap_natural"] = one_way_snap(r1, 2768, 414, 7)
    fx["mghz1_11_one_way_snap_natural"] = one_way_snap(r1, 2960, 830, 12)
    fx["mghz1_10_one_way_depth_sweep"] = one_way_depth_sweep(r1, 2768, 414, 7)
    fx["synthetic_solid_control"] = solid_control(r2)
    out["fixtures"] = fx
    # verdict
    d = fx["mghz2_12_ride_into_breakable_0d"]["rings_0"]
    out["verdict"] = {
        "temporarily_embedded_or_jitter": "no for the two real solid cases: the rider is killed in the first pass whose head probe enters the $0D cell; no push-out, no jitter. For the one-way ledges he is carried THROUGH the "
                                          "32-px block (feet inside it) for ~20 updates with a constant Y offset of -14 (no jitter), which is the canonical 'embedded' look",
        "ever_snaps_to_upper_surface": "yes, only for one-way ledges (mghz1 #10/#11): the first pass whose feet depth is within 8 + (Y speed >> 8) rows captures him to the block's upper surface (Y delta up to 11 px in one update, "
                                       "support released, floor flag set). Never for $0D (death first)",
        "classification": "canonical SMS behavior (not a quirk of this harness); a POC that neither kills a supported rider at a $0D ceiling nor reproduces the one-way capture is a POC divergence",
        "death_update_example": d["death_update"], "death_platform_y": d["platform_y_at_start_of_death_update"],
    }
    return out


# --------------------------------------------------------------------------- #
# B. animated strip $1A8/$1A9
# --------------------------------------------------------------------------- #
def tile_rows(vram: bytes, tile: int):
    return G.decode_mode4_tile(vram[tile * 32:tile * 32 + 32])


def strip_vram_variants(rom: bytes, vram: bytes) -> dict:
    out = {"initial": bytes(vram)}
    for name, cpu in (("source_A_8E3D", 0x8E3D), ("source_B_8E1D", 0x8E1D)):
        v = bytearray(vram)
        off = F.bank_file(0x1D, cpu)
        v[0x3500:0x3500 + 64] = rom[off:off + 64]
        out[name] = bytes(v)
    return out


def block_pixels(rom: bytes, act: dict, vram: bytes, blocks) -> dict:
    return L.block_pixel_maps(rom, vram, only=sorted(blocks), mapping_rom=act["descriptor"]["header"]["block_mapping_rom"])


def part_b(rom: bytes, static_only: bool) -> dict:
    manifest = json.loads(F.OUTPUT.read_text(encoding="utf-8"))
    recs = C.decode_records(rom)
    acts = {k: C.vram_for_act(rom, i) for i, k in enumerate(recs)}
    a1 = acts["mghz1"]
    variants = strip_vram_variants(rom, bytes(a1["vram"]))
    # --- consumers
    consumers = {"tile_to_blocks_all_256_blocks": {}, "layout_cells": {}, "sprite_pattern_consumers": {}}
    for tile in (0x1A8, 0x1A9):
        per_act = {}
        for key, a in acts.items():
            blocks = manifest["acts"][key]["blocks"]
            per_act[key] = sorted(h(b["block_id"], 2) for b in blocks if tile in b["tile_ids"])
        consumers["tile_to_blocks_all_256_blocks"][h(tile, 3)] = per_act
    mapping = {}
    for blk in (0xD2, 0xD3):
        b = next(x for x in manifest["acts"]["mghz1"]["blocks"] if x["block_id"] == blk)
        attrs = b["mapping"]["attributes"]
        mapping[h(blk, 2)] = {"attributes_4x4_row_major": [h(v, 4) for v in attrs],
                              "tile_ids": [v & 0x1FF for v in attrs], "h_flip": [bool(v & 0x200) for v in attrs],
                              "rows_0_to_2": "tile $0C0 (all index 0) x12", "row_3": [f"tile {h(v & 0x1FF, 3)}{' hflip' if v & 0x200 else ''}" for v in attrs[12:]],
                              "surface": b["surface"], "header_flags": h(b["headers"][0]["flags"], 2), "priority_tiles": b["priority_tiles"], "palette1_tiles": b["palette1_tiles"]}
    consumers["block_mapping"] = mapping
    for key in ACTS:
        a = I.act_data(rom, key)
        w, cells = a["width"], a["cells"][:4095]
        found = [(i % w, i // w, v) for i, v in enumerate(cells) if v in (0xD2, 0xD3)]
        below, above = {}, {}
        for x, y, v in found:
            if (y + 1) * w + x < len(cells):
                k = h(cells[(y + 1) * w + x], 2)
                below[k] = below.get(k, 0) + 1
            if y > 0:
                k = h(cells[(y - 1) * w + x], 2)
                above[k] = above.get(k, 0) + 1
        twist = twist_cells(rom, key)
        near_twist = []
        for x, y, v in found:
            best = min(((abs(x - tx) + abs(y - ty), tx, ty) for tx, ty in twist), default=None)
            if best and best[0] <= 10:
                near_twist.append({"cell": [x, y], "block": h(v, 2), "nearest_twist_cell": [best[1], best[2]], "manhattan_cells": best[0]})
        consumers["layout_cells"][key] = {"count": len(found), "block_$D2": sum(1 for _, _, v in found if v == 0xD2), "block_$D3": sum(1 for _, _, v in found if v == 0xD3),
                                           "cells": [[x, y, h(v, 2)] for x, y, v in found], "sha256_of_cells": sha(json.dumps(found).encode()),
                                           "block_directly_below": dict(sorted(below.items())), "block_directly_above": dict(sorted(above.items())), "twist_cells_surface_17": len(twist),
                                           "near_twist_within_10_cells": near_twist}
    boss = [r for r in recs["mghz3"]["records"] if r["type_id"] == "0x56"]
    consumers["layout_cells"]["mghz3_boss_area"] = {"boss_record": [boss[0]["world_x"], boss[0]["world_y"]] if boss else None,
                                                     "cells_with_x_ge_boss_x_minus_256": [c for c in consumers["layout_cells"]["mghz3"]["cells"] if boss and c[0] * 32 >= boss[0]["world_x"] - 256]}
    consumers["effect_14_only_writer"] = "level effect $0E (bank $1D $82F7): the only runtime writer of VRAM $3500; static level art loads the initial pair"
    # sprite pattern bank: object art never lands on VRAM tiles $1A8/$1A9 (sprite patterns use tiles 0..255 in MGHZ); the type-$24 subject uses patterns $A0..$AB = VRAM tiles $0A0..$0AB
    consumers["sprite_pattern_consumers"] = {"sprite_pattern_bank": "VRAM tiles 0..255 (patterns index VRAM tile = pattern); tools/thz1_object_assets.tile_pixels masks tile & $FF",
                                              "type_24_patterns": "$A0..$AB -> VRAM tiles $0A0..$0AB, not $1A8/$1A9", "any_object_uses_vram_tile_1a8_1a9": False}
    # --- tiles and frame schedule
    tiles = {}
    for name, v in variants.items():
        tiles[name] = {h(t, 3): {"rows_hex": ["".join(f"{c & 15:X}" for c in row) for row in tile_rows(v, t)], "sha256": sha(v[t * 32:t * 32 + 32])} for t in (0x1A8, 0x1A9)}
    tile_c0 = tile_rows(variants["initial"], 0xC0)
    sched = [(e["update"], h(e["vram_copies"][0]["source_cpu"], 4)) for e in F.run_effect(rom, 14, 32) if e["vram_copies"]]
    block_hashes = {}
    for name, v in variants.items():
        mp = block_pixels(rom, a1, v, {0xD2, 0xD3})
        block_hashes[name] = {h(b, 2): {"bottom_8_rows_index_sha256": sha(bytes(c for row in mp[b][24:] for c in row)), "top_24_rows_all_zero": all(c == 0 for row in mp[b][:24] for c in row),
                                         "nonzero_pixels": sum(1 for row in mp[b] for c in row if c), "bottom_8_rows_distinct_colour_indices": sorted({c & 15 for row in mp[b][24:] for c in row}),
                                         "rows_with_any_nonzero": [y for y, row in enumerate(mp[b]) if any(row)]} for b in (0xD2, 0xD3)}
    line = {}
    for name, v in variants.items():
        mp = block_pixels(rom, a1, v, {0xD2, 0xD3})
        line[name] = {h(b, 2): {"widest_row_nonzero_run": max(max_run(row) for row in mp[b]), "rows_fully_nonzero": [y for y, row in enumerate(mp[b]) if all(row)],
                                "horizontal_line_rows": [y for y, row in enumerate(mp[b]) if max_run(row) >= 16]} for b in (0xD2, 0xD3)}
    out = {"consumers": consumers, "tiles": tiles, "tile_c0_all_zero": all(c == 0 for row in tile_c0 for c in row),
           "effect_14": {"vram_destination": "0x3500", "bytes": 64, "sources": {"A": "0x8E3D", "B": "0x8E1D"}, "source_overlap": "A and B are one 3-tile sequence X0 X1 X2 at $8E1D/$8E3D/$8E5D; B = (X0,X1), A = (X1,X2); X0 == X2",
                         "initial_vram_equals_source": "B", "schedule_updates_zero_based": sched, "period_updates": 4, "first_upload_update": 3, "paused_while_D44E_nonzero": True},
           "block_art_hashes": block_hashes, "thin_line_audit": line,
           "scenery": {"identification": "small animated ground flowers/buds (pairs of mirrored yellow bulbs on a short stem) in the 8-pixel bottom row of the cell directly above the grass-top surface; "
                                         "rows 0..23 of the cell are empty background (tile $0C0)", "evidence": "DECODED DATA + EMULATED ORIGINAL FRAME (nametable scan in the booted game) + review renders", "text_status": "visual identification; pending James' PNG review"}}
    if not static_only:
        out["emulated_nametable"] = emulated_nametable(rom)
    return out


def twist_cells(rom: bytes, key: str) -> list:
    a = I.act_data(rom, key)
    w = a["width"]
    return [(i % w, i // w) for i, v in enumerate(a["cells"][:4095]) if R.header(rom, v)["flags"] & 31 == 0x17]


def max_run(row) -> int:
    best = cur = 0
    for c in row:
        cur = cur + 1 if c else 0
        best = max(best, cur)
    return best


def emulated_nametable(rom: bytes) -> dict:
    rig = Rig(rom, "mghz1")
    rig.start(49 * 32 + 16, 7 * 32 + 8, vy=0, cur=1, f3=0, floor=True)
    for _ in range(60):
        rig.s.pad = 0
        rig.s.run_frame()
    s = rig.s
    nb = (s.reg[2] & 0x0E) << 10
    grid = [[s.vram[nb + (r * 32 + c) * 2] | s.vram[nb + (r * 32 + c) * 2 + 1] << 8 for c in range(32)] for r in range(28)]
    hits = [(r, c, grid[r][c] & 0x1FF, bool(grid[r][c] & 0x200)) for r in range(28) for c in range(32) if grid[r][c] & 0x1FF in (0x1A8, 0x1A9)]
    above_blank = all((grid[r - 1][c] & 0x1FF) == 0xC0 for r, c, _, _ in hits if r > 0)
    return {"evidence": "EMULATED ORIGINAL FRAME (MGHZ1, settled at cell (49,7))", "sprite_pattern_register_r6_bit2": bool(s.reg[6] & 4), "name_table_entries_with_1a8_1a9": len(hits),
            "all_in_bottom_row_of_a_4_row_group": all((r % 4) == 3 for r, _, _, _ in hits), "tile_above_each_is_c0": above_blank,
            "hflip_pairs_follow_pattern": sorted({(t, f) for _, _, t, f in hits}) == [(0x1A8, False), (0x1A8, True), (0x1A9, False), (0x1A9, True)]}


# --------------------------------------------------------------------------- #
# C. breakable $0D
# --------------------------------------------------------------------------- #
def decode_fragment_table(rom: bytes, cpu: int) -> list:
    base = 0x0C * 0x4000 + (cpu - 0x8000)
    out = []
    for q in range(4):
        e = rom[base + 8 * q:base + 8 * q + 8]
        out.append({"quadrant": q, "x_offset": e[0] | e[1] << 8, "y_offset": e[2] | e[3] << 8, "x_speed": s16(e[4] | e[5] << 8), "y_speed": s16(e[6] | e[7] << 8)})
    return out


def block_facts(rom: bytes, manifest: dict) -> dict:
    acts = {k: C.vram_for_act(rom, i) for i, k in enumerate(C.decode_records(rom))}
    anim_tiles = {"effect_14_strip": {0x1A8, 0x1A9}, "terrain_ring_frames": {0x10B, 0x10C, 0x10D, 0x10E}}
    out = {}
    for blk in (0x9B, 0x9C, 0x9D):
        per = {}
        for key in ("mghz1", "mghz2"):
            b = next((x for x in manifest["acts"][key]["blocks"] if x["block_id"] == blk), None)
            if b is None:
                per[key] = None
                continue
            a = acts[key]
            mp = block_pixels(rom, a, bytes(a["vram"]), {blk})[blk]
            idx = sorted({c & 15 for row in mp for c in row if not c & 16})
            per[key] = {"cells": b["cell_count"], "surface": b["surface"], "header_flags": h(b["headers"][0]["flags"], 2), "tile_ids": [h(t, 3) for t in b["tile_ids"]],
                        "priority_tiles": b["priority_tiles"], "uses_animated_tile": sorted(h(t, 3) for t in b["tile_ids"] if any(t in s for s in anim_tiles.values())),
                        "background_palette_indices_used": idx, "uses_cycled_palette_entry_4_or_11": [i for i in idx if i in (4, 11)], "block_index_sha256": sha(bytes(c for row in mp for c in row))}
        out[h(blk, 2)] = per
    return out


def hole_run(rig: Rig, cx: int, cy: int, y_above: int, vy: int, cur: int, f3: int, frames: int = 80, vx: int = 0) -> dict:
    """Spin-jump (attack posture) onto a $9B cell from above on the original game; records the break, nametable refresh and the four fragments."""
    s, m = rig.s, rig.m
    rig.start(cx * 32 + 16, cy * 32 - y_above, vy=vy, cur=cur, f3=f3, vx=vx)
    rows, frags = [], []
    cell0 = rig.cell(cx, cy)
    break_u = None
    for f in range(frames):
        rig.ev.clear()
        s.pad = 0
        s.run_frame()
        ev = squash(rig.ev)
        objs = []
        for i in range(19):
            b = 0xD540 + i * 0x40
            if m[b] == 7:
                objs.append({"slot": i, "x": s.u16(b + 0x11), "y": s.u16(b + 0x14), "vx": s16(s.u16(b + 0x16)), "vy": s16(s.u16(b + 0x18)), "state": m[b + 1], "flags4": m[b + 4], "quadrant": m[b + 0x3F]})
        if "break_7898" in ev and break_u is None:
            break_u = f
            ptr = rig.cap.get("break_cell_ptr", 0xC001)
            idx = ptr - 0xC001
            rows.append({"u": f, "ev": ev, "broken_cell": [idx % rig.width, idx // rig.width], "broken_cell_after": h(m[ptr], 2), "player": [s.u16(0xD511), s.u16(0xD514)], "vy": s16(s.u16(0xD518)),
                         "d3b2": m[0xD3B2], "fragments": objs})
        if objs and break_u is not None:
            frags.append((f, objs))
        if break_u is not None and f > break_u + 3 and not objs:
            break
    life = {}
    for f, objs in frags:
        for o in objs:
            life.setdefault(o["quadrant"], []).append(f)
    return {"start": {"cell": [cx, cy], "player_x": cx * 32 + 16, "player_y": cy * 32 - y_above, "vy": vy, "cur": cur, "f3": f3, "cell_before": h(cell0, 2)}, "break_update": break_u,
            "break_row": rows[0] if rows else None, "fragment_first_state_rows": [frags[0][1]] if frags else None,
            "fragment_life_updates_by_quadrant": {str(q): [v[0] - break_u, v[-1] - break_u, len(v)] for q, v in sorted(life.items())},
            "fragment_x_track_q0": [o["x"] for f, ob in frags for o in ob if o["quadrant"] == 0][:10],
            "fragment_vy_track_q0": [o["vy"] for f, ob in frags for o in ob if o["quadrant"] == 0][:10]}


def part_c(rom: bytes, rig1: Rig | None, static_only: bool) -> dict:
    manifest = json.loads(F.OUTPUT.read_text(encoding="utf-8"))
    sc = C.state_scripts(rom, 7)
    fr = {}
    for fi in (0, 15):
        rec = G.parse_frame_record(rom, G.mapping_frame_pointers(rom, G.object_mapping(rom, 7)["mapping_cpu"])[fi])
        fr[str(fi)] = {"piece_count": rec["piece_count"], "extent_word": h(rec["raw_word_1"], 4), "frame_rom": h(rec["frame_rom"], 5)}
    out = {
        "blocks": block_facts(rom, manifest),
        "triggers": {
            "floor_6b2c": "surface $0D under the foot probe: current state not in {$0F,$10,$15,$1A} AND attack posture (+$03 bit 1): $D3B2 := $10, Y speed := $FBC0 (-4.25), floor flag cleared, airborne, -> $7898",
            "sides_72b6_72dd": "attack posture AND |X speed high byte| >= 3: X speed nudged by +/-$40 when its high byte < 7, -> $7898 (otherwise ordinary wall projection)",
            "ceiling_7464": "support owner $D3C0 == 0 -> $7898; support owner != 0 (platform rider) -> $4984 crush death (see part A)"},
        "break_routine_7898": {"assembly": disasm_slice(rom, 0x7898, 0x78E1),
                               "steps": ["bank select from $D162 (level art bank) via $1C6F", "layout cell := $9D", "block mapping of $9D written to the name table via $23F9 (4x4 tiles, same update)",
                                         "fragment anchor := cell top-left ($D358/$D35A & $E0) -> $D35C/$D35E", "spawn type $07 four times with H = 0..3 via $5E9C"],
                               "no_intermediate_frame": True},
        "replacement_block": {"id": "0x9D", "evidence": "block_facts"},
        "fragment_object_07": {"state_scripts": sc["states"], "state_0": "sound $A3 requested, record frame 0 for 1 update, restart into state set by the init callback ($9B11 sets +$02 := 1)",
                               "state_1": "frame 15 (duration 128, looped), callback $9BB5: if +$04 bit 6 (off-screen) -> delete ($0344); else $0350 with BC=$1000, DE=$00C0 then move $0338; measured +192 (0.75 px) Y speed per update in the emulated run",
                               "frames": fr, "quadrant_in": "+$3F", "init_callback": h(FRAGMENT_INIT_CB),
                               "offset_tables": {"player_x_speed_ge_0_table_9b75": decode_fragment_table(rom, FRAGMENT_TABLES[0]), "player_x_speed_lt_0_table_9b95": decode_fragment_table(rom, FRAGMENT_TABLES[1])},
                               "act_special_case": "zone 6 / act 2 sets +$08 := $9C (not MGHZ)"},
        "answer": {"animation_before_destruction": False, "frame_change_during_destruction": False,
                   "expected_presentation": "instant replacement of the 32x32 cell by $9D (no intermediate block art) plus four shared type-$07 fragment objects (frame 0 for one update, then frame 15) and sound $A3; "
                                            "the only block-side effect is the layout write",
                   "block_art_uses_no_animated_tile": True, "block_art_uses_cycled_palette_entry": "see blocks.*.uses_cycled_palette_entry_4_or_11",
                   "open": ["type-$07 fragment art (pieces of frames 0/15 and which VRAM pattern base the MGHZ stream uses) is not audited here (art task)"]},
        "d3b2_note": "$D3B2 is only ever written (jump setter $4601 = $20, break $6B42 = $10); no reader by absolute address; treated as a jump-hold counter, unresolved but irrelevant to presentation",
    }
    if rig1 is not None and not static_only:
        out["emulated_floor_break"] = hole_run(rig1, 76, 23, 70, 0x300, 0x0A, 3)
        out["emulated_floor_break_moving_left"] = hole_run(rig1, 76, 23, 70, 0x300, 0x0A, 3, vx=-0x200)
    return out


# --------------------------------------------------------------------------- #
# PNG review renders (standard library only)
# --------------------------------------------------------------------------- #
def write_png(path: Path, rows, scale: int = 1) -> None:
    hgt, wid = len(rows), len(rows[0])
    raw = bytearray()
    for r in rows:
        line = b"".join(bytes(p[:3]) * scale for p in r)
        raw += (b"\x00" + line) * scale

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", wid * scale, hgt * scale, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def palette_rgb(rom: bytes, idx: int):
    base = L.PALETTE_DATA + idx * 16
    out = []
    for v in rom[base:base + 16]:
        out.append(((v & 3) * 85, ((v >> 2) & 3) * 85, ((v >> 4) & 3) * 85))
    return out


def render_pngs(rom: bytes, outdir: Path) -> list:
    recs = C.decode_records(rom)
    acts = {k: C.vram_for_act(rom, i) for i, k in enumerate(recs)}
    a1 = acts["mghz1"]
    d = a1["descriptor"]
    bgp = palette_rgb(rom, d["palette"]["background_index"])
    spp = palette_rgb(rom, d["palette"]["sprite_index"])
    variants = strip_vram_variants(rom, bytes(a1["vram"]))
    manifest = json.loads(F.OUTPUT.read_text(encoding="utf-8"))
    written = []

    def colour(c):
        i = c & 15
        return bgp[0] if i == 0 else (spp if c & 16 else bgp)[i]

    def crop(key, vram, left, top, w, hgt):
        a = acts[key]
        maps = block_pixels(rom, a, vram, set(a["cells"][:a["runtime_cells"]]))
        out = []
        for yy in range(hgt):
            row = []
            for xx in range(w):
                wx, wy = left + xx, top + yy
                i = (wy // 32) * a["width"] + wx // 32
                row.append(bgp[0] if wy < 0 or wx < 0 or i >= a["runtime_cells"] else colour(maps[a["cells"][i]][wy % 32][wx % 32]))
            out.append(row)
        return out
    cells = {}
    for k in ACTS:
        ad = I.act_data(rom, k)
        cells[k] = [(i % ad["width"], i // ad["width"]) for i, v in enumerate(ad["cells"][:4095]) if v in (0xD2, 0xD3)]
    picks = [("mghz1-ground-garden", "mghz1", 49, 7), ("mghz1-start-area", "mghz1", 5, 6), ("mghz3-boss-area", "mghz3", 113, 11)]
    twist = {}
    for key in ACTS:
        tw = twist_cells(rom, key)
        best = min(((abs(c[0] - t[0]) + abs(c[1] - t[1]), c) for c in cells[key] for t in tw), default=None)
        if best and best[0] <= 12:
            twist[key] = best[1]
    for key, c in twist.items():
        picks.append((f"{key}-near-twist", key, c[0], c[1]))
    for name, key, cx, cy in picks:
        a = acts[key]
        vr = bytes(a["vram"]) if key != "mghz1" else bytes(a1["vram"])
        # the animated pair is shared by all acts' VRAM builds; apply the same two sources
        for fr, src in (("A", "source_A_8E3D"), ("B", "source_B_8E1D")):
            v = bytearray(vr)
            v[0x3500:0x3500 + 64] = variants[src][0x3500:0x3500 + 64]
            left = max(0, cx * 32 - 160)
            top = max(0, cy * 32 - 100)
            write_png(outdir / f"strip-context-{name}-{fr}.png", crop(key, bytes(v), left, top, 352, 200), 2)
            written.append(f"strip-context-{name}-{fr}.png")
    for name, src in (("A", "source_A_8E3D"), ("B", "source_B_8E1D")):
        mp = block_pixels(rom, a1, variants[src], {0xD2, 0xD3})
        rows = [[colour(c) for c in row] for blk in (0xD2, 0xD3) for row in mp[blk]]
        write_png(outdir / f"strip-blocks-D2-D3-{name}.png", rows, 8)
        written.append(f"strip-blocks-D2-D3-{name}.png")
    return written


# --------------------------------------------------------------------------- #
# build / CLI
# --------------------------------------------------------------------------- #
def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    data = {"format": "mghz-m1-windows-followup-v1", "rom_sha256": sha(rom), "research_base": RESEARCH_BASE, "research_only": True, "poc_untouched": True,
            "scope": {"in": ["A rising $28 platform into overhead terrain", "B animated tiles $1A8/$1A9", "C breakable block $0D presentation"],
                      "out": ["new enemy/boss research", "$24", "$2E", "boss $56", "footwear"]},
            "evidence_classes": ["DECODED DATA", "BYTE-VERIFIED ASSEMBLY", "SOURCE-TRACED BEHAVIOR", "CONTROLLED ROUTINE RESULT", "EMULATED ORIGINAL FRAME", "SYNTHETIC CONTROL", "UNRESOLVED"],
            "static_only": static_only}
    rigs = {"rom": rom}
    if not static_only:
        rigs["mghz1"] = Rig(rom, "mghz1")
        rigs["mghz2"] = Rig(rom, "mghz2")
        data["part_a"] = part_a(rigs)
    else:
        data["part_a"] = {"placements": platform_scan(rom)}
    data["part_b"] = part_b(rom, static_only)
    data["part_c"] = part_c(rom, rigs.get("mghz1"), static_only)
    return data


def dumps(data: dict) -> str:
    return json.dumps(data, indent=1) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    ap.add_argument("--png", type=Path, default=None)
    a = ap.parse_args()
    rom = L.load_rom(a.rom)
    if a.png:
        print("wrote", ", ".join(render_pngs(rom, a.png)))
        return
    text = dumps(build(rom, a.static_only))
    if a.check:
        cached = OUTPUT.read_text(encoding="utf-8")
        if a.static_only:
            cj, dj = json.loads(cached), json.loads(text)
            bad = [k for k in ("part_b", "part_c") if {x: cj[k][x] for x in dj[k] if x in cj[k] and not x.startswith("emulated")} != {x: dj[k][x] for x in dj[k] if x in cj[k] and not x.startswith("emulated")}]
        else:
            bad = [] if cached.replace("\r\n", "\n") == text else ["file"]
        print("OK: cache matches the ROM" if not bad else f"MISMATCH in {bad}")
        sys.exit(1 if bad else 0)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT} ({len(text)} bytes)")


if __name__ == "__main__":
    main()

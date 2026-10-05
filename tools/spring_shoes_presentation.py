#!/usr/bin/env python3
"""Spring Shoes (type $2F / player state $12) presentation, act-clear and detach audit (Research only, deterministic).

Bounded questions:
  A. exact runtime presentation of Spring Shoes (frames, cadence, Sonic-to-shoe registration, mirroring);
  B. act clear while state $12 is active (sign contact, replacement of $12, owner pointer $D3A4, type $2F removal, stall possibility);
  C. which events detach the shoes (type $21 top stomp, mapped springs, side-wall branch, manual jump, terrain spring, hurt).
Not covered: types $24/$2E/$56, Rocket Shoes beyond what the comparison needs.
Output: data/rom-cache/spring-shoes-presentation.json (numeric labels; hashes only, no ROM bytes, no pixels).

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT (original Z80 routines on tools/oracle.py),
EMULATED ORIGINAL FRAME (whole game in tools/sms_frame_harness.py, PC hooks and write watches), SYNTHETIC CONTROL (state/RAM injected, never a canonical placement),
POC SOURCE (READ-ONLY), UNRESOLVED.

Usage:
  python tools/spring_shoes_presentation.py ROM.sms [--check] [--static-only]
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

import isometric_platform as I          # noqa: E402  (act_data, TerrainLab)
import level_package as L               # noqa: E402
import platform_spike_collision as P    # noqa: E402  (Emu: snapshot/restore/place)
import rom as R                         # noqa: E402

OUTPUT = ROOT / "data" / "rom-cache" / "spring-shoes-presentation.json"
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
RESEARCH_BASE = "a779fde"
ZONES = {"thz": 0, "gpz": 1, "sez": 2, "mghz": 3}

# named routines / addresses (CPU; fixed bank 1 unless noted)
STATE12_CALLBACK = 0x3B4E            # trampoline $03B0
OWNER_POSITION, OWNER_POSITION_RET = 0x5F27, 0x5F3C
OWNER_FOLLOW = 0x3BA8
PLAYER_DISPATCH = 0x5E91
SIGN_ACTIVATION = 0xA87D             # bank $0C: type $18 state-2 callback
SIGN_CONTACT = 0xA88E                # bank $0C: type $18 state-3 callback
STOMP_REBOUND, UPRIGHT_SPRING_SETTER = 0x5F17, 0x480C
HURT_TAIL = 0x494F
SHOE_BASE = 0x78B1A                  # bank $1E object $2F tables


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def s16(v: int) -> int:
    return (v + 32768) % 65536 - 32768


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos research ROM")


def u16(rom: bytes, a: int) -> int:
    return rom[a] | rom[a + 1] << 8


def c15(cpu: int) -> int:
    """File offset of a CPU address in slot 2 with bank $0F mapped (object mappings)."""
    return 0x3C000 + cpu - 0x8000


# --------------------------------------------------------------------------- #
# static: type $2F scripts, mappings, player state $12 script
# --------------------------------------------------------------------------- #
def decode_script(rom: bytes, base: int, bank_off: int, ptr: int, limit: int = 12) -> list:
    """Records (duration, frame, callback) until the closing command; commands: FF 00 loop/restart, FF 03 n request state n, FF 07 a jump, FF 04 spawn (object)."""
    out, a, n = [], bank_off + ptr - 0x8000, 0
    while n < limit:
        b = rom[a]
        if b == 0xFF:
            cmd = rom[a + 1]
            if cmd == 0:
                out.append({"command": "00 restart/hold state", "raw": rom[a:a + 2].hex()})
                return out
            if cmd == 3:
                out.append({"command": "03 request state", "state": rom[a + 2], "raw": rom[a:a + 3].hex()})
                a += 3
            elif cmd == 7:
                out.append({"command": "07 jump", "target": h(u16(rom, a + 2)), "raw": rom[a:a + 4].hex()})
                return out
            elif cmd == 4:
                out.append({"command": "04 spawn object", "raw": rom[a:a + 8].hex()})
                a += 8
            else:
                out.append({"command": f"{cmd:02X} (not used by this object)", "raw": rom[a:a + 4].hex()})
                return out
        else:
            out.append({"duration": b, "frame": rom[a + 1], "callback": h(u16(rom, a + 2)), "raw": rom[a:a + 4].hex()})
            a += 4
        n += 1
    return out


def object_scripts(rom: bytes) -> dict:
    """Type $2F state table at bank $1E $8B1A and the six state scripts."""
    states = {}
    for st in range(6):
        ptr = u16(rom, SHOE_BASE + 2 * st)
        states[str(st)] = {"script_cpu": h(ptr), "records": decode_script(rom, SHOE_BASE, 0x78000, ptr)}
    meaning = {
        "0": "creation: init callback $8B5B (request state 1, +$03 bit7 set = non-generic-damage solid)",
        "1": "free on the ground: frames 1 and 2 alternate every 8 updates; callback $8B64 offers attachment",
        "2": "unused script (spawns a type-$0F object); no placement or code requests state 2",
        "3": "attached, just bounced: frame 3 for 12 updates, callback $8BC3, then request state 4",
        "4": "attached, held: frame 4, duration 4 repeated forever, callback $8BC3",
        "5": "detached: frame 4, duration 1 then 8 repeated, callback $8BCE (fall speed +1.5) then $8BD7 (gravity +0.5 and move)",
    }
    return {"evidence": "DECODED DATA + BYTE-VERIFIED ASSEMBLY (bank $1E)", "state_table_rom": h(SHOE_BASE, 5), "states": states, "meaning": meaning,
            "callback_roles": {"$8B64": "state 1: top contact (player not rising, current state != $12) -> $5FA0 -> +$21 bit0: owner pointer $D3A4 := IX, requested player state $12, own state 3; "
                                       "side contact with a grounded attacker: stand + push, no pickup",
                               "$8BC3": "states 3/4: if player current state ($D501) != $12 then own requested state := 5",
                               "$8BCE/$8BD7": "state 5: Y speed +1.5 once, then gravity +$0080 (DE=$80 via $0431) and move ($0338) every update"}}


def mapping_frames(rom: bytes) -> dict:
    """Frame records of type $2F (bank $0F): count, extents, origins, piece offsets and tile ids; plus the player frame $0B record for the registration."""
    def frame(fr_cpu: int) -> dict:
        fr = c15(fr_cpu)
        count, ex, ey = rom[fr], rom[fr + 1], rom[fr + 2]
        coords, y_org, x_org, tiles = u16(rom, fr + 3), s16(u16(rom, fr + 5)), s16(u16(rom, fr + 7)), u16(rom, fr + 9)
        pieces = []
        for i in range(count):
            pieces.append({"piece_y": s16(u16(rom, c15(coords + 4 * i))), "piece_x": s16(u16(rom, c15(coords + 2 + 4 * i))), "tile_offset": rom[c15(tiles + i)]})
        return {"record_cpu": h(fr_cpu), "pieces": count, "extent_x": ex, "extent_y": ey, "y_origin": y_org, "x_origin": x_org, "coords_cpu": h(coords), "tiles_cpu": h(tiles), "piece_list": pieces}
    table = u16(rom, 0x3C000 + 2 * 0x2F)
    frames = {str(i): frame(u16(rom, c15(table) + 2 * i)) for i in range(5)}
    ptable = u16(rom, 0x3C000 + 2 * 1)
    return {"evidence": "DECODED DATA (bank $0F, record layout verified against $6567/$226A/$22B6 by tools/mapped_object_registration.py)",
            "type_2F_table_cpu": h(table), "frames": frames,
            "frame_0": "empty record shared with other objects (never selected by any type-$2F script)",
            "player_frame_0B": frame(u16(rom, c15(ptable) + 2 * 0x0B)),
            "art_bases": {"SEZ": {"aux0": 0x94, "vram_tiles": "$94..$A3", "stream_rom": h(0x26840, 5)}, "MGHZ": {"aux0": 0xAC, "vram_tiles": "$AC..$BB", "stream_rom": h(0x26840, 5)}},
            "note": "frames 3 and 4 share geometry (coords $A3F7, extents 12x48, x origin +4) and differ only in tile ids; frames 1 and 2 share geometry (extents 8x16)"}


def player_state12_script(rom: bytes) -> dict:
    import csv
    rows = {r["state_hex"]: int(r["script_file"], 16) for r in csv.DictReader(open(ROOT / "data" / "sonic-state-scripts.csv", encoding="utf-8"))}
    a = rows["12"]
    recs = decode_script(rom, 0, 0x30000, a - 0x30000 + 0x8000, 4)
    return {"evidence": "DECODED DATA (bank $0C)", "script_cpu": h(a - 0x30000 + 0x8000), "script_rom": h(a, 5), "records": recs,
            "reading": "a single frame: record frame $0B, duration 4, callback trampoline $03B0 (= $3B4E), then FF 00 (restart): the player's animation record never changes while state $12 is current"}


def static_facts(rom: bytes) -> dict:
    regions = []
    for a, b, why in ((0x3B4E, 0x3BC1, "player state $12 callback + owner follow $3BA8"), (0x5F27, 0x5F3D, "owner positioning helper $5F27"), (0x45ED, 0x4663, "normal jump $45ED / fall setter $463C"),
                      (0x480C, 0x4838, "upright spring setter $480C"), (0x494F, 0x49C3, "hurt tail $494F and death setter $4984")):
        regions.append({"cpu": h(a), "end_exclusive": h(b), "rom": h(a, 5), "length": b - a, "sha256": sha(rom[a:b]), "purpose": why})
    for bank, a, b, why in ((30, 0x8B1A, 0x8BE1, "type $2F tables, scripts and callbacks"), (12, 0xA870, 0xA8CE, "type $18 activation $A87D / contact $A88E")):
        off = bank * 0x4000 + a - 0x8000
        regions.append({"bank": bank, "cpu": h(a), "end_exclusive": h(b), "rom": h(off, 5), "length": b - a, "sha256": sha(rom[off:off + b - a]), "purpose": why})
    # opcode scans (whole ROM)
    conv = [p for p in range(len(rom) - 5) if rom[p:p + 5] == bytes.fromhex("3a02d5fe12")]
    d3a4 = [p for p in range(len(rom) - 1) if rom[p:p + 2] == b"\xa4\xd3"]
    d3b3 = [p for p in range(len(rom) - 1) if rom[p:p + 2] == b"\xb3\xd3"]
    ld12 = [p for p in range(len(rom) - 2) if rom[p:p + 3] == bytes.fromhex("3e1232") or rom[p:p + 4] == bytes.fromhex("dd360212")]

    def loc(p):
        return {"rom": h(p, 5), "bank": p // 0x4000, "cpu": h(p if p < 0x8000 else 0x8000 + p % 0x4000)}
    return {"evidence": "BYTE-VERIFIED ASSEMBLY (opcode scans of the whole ROM)", "regions": regions,
            "requested_state_compare_12_sites": [dict(loc(p), role={0x32882: "type $18 state 2 (sign activation)", 0x79765: "type $50 state 0 (boss creation)"}.get(p, "unclassified")) for p in conv],
            "d3a4_operand_sites": [loc(p) for p in d3a4], "d3b3_operand_site_count": len(d3b3),
            "requested_state_12_writers_for_the_player": "only $78B89 (type $2F pickup: LD A,$12; LD ($D502),A); the state-script/animation engine copies it to the current state",
            "owner_pointer": "$D3A4 is written once (pickup, $78B85) and read only by the state-$12 callback ($3B80/$3B90/$3B9F) and $3BAC; no instruction ever clears it",
            "footwear_clear_paths": "exactly two instructions in the ROM compare the REQUESTED player state with $12 and convert it: the type-$18 sign's state-2 callback ($A87D..$A88A, bank $0C: $D3B3 := $12 sign art selector, "
                                    "then requested $12 -> $0E) and the identical sequence at bank $1E $9765 (type $50 state 0, docs/object-50.md section 'state 0'); no instruction clears the owner pointer"}


# --------------------------------------------------------------------------- #
# whole-game lab
# --------------------------------------------------------------------------- #
SLOT_BASE, SLOT_SIZE, SLOT_COUNT = 0xD500, 0x40, 20


class Lab:
    """Boots the ORIGINAL game into (zone, act), settles, snapshots; every case restores the snapshot. place() sets the REQUESTED state and forces the engine to reload that state's script."""

    def __init__(self, rom: bytes, zone: str, act: int):
        from sms_frame_harness import SMS, BTN_1, BTN_2
        self.rom, self.zone, self.act = rom, zone, act
        s = SMS(rom)
        done = [False]

        def select(m):
            m._write(0xD297, ZONES[zone])
            m._write(0xD298, act)

        def start(m):
            if m.frame > 300 and not done[0]:
                done[0] = True
        s.add_pc_hook(0x07D5, select)
        s.add_pc_hook(0x4E97, start)
        for f in range(4000):
            s.pad = 0 if f < 250 else BTN_1 if f < 700 and f % 40 < 3 else (BTN_1 | BTN_2) if not done[0] and f % 60 < 10 else 0
            s.run_frame()
            if done[0] and s.mem[0xD500] == 1:
                break
        else:
            raise RuntimeError("boot failed")
        for _ in range(90):
            s.pad = 0
            s.run_frame()
        self.s, self.m = s, s.mem
        self.key = f"{zone}{act + 1}"
        self.upd = 0
        self.follow: list = []
        self.writes: list = []
        self.watch: set = set()
        s.add_pc_hook(PLAYER_DISPATCH, self._on_dispatch)
        s.add_pc_hook(OWNER_POSITION, self._on_follow_entry)
        s.add_pc_hook(OWNER_POSITION_RET, self._on_follow_ret)
        s.add_pc_hook(SIGN_ACTIVATION, lambda mm: self.writes.append(("sign_activation_callback", mm.frame, mm.cpu.pc)))
        orig = s._write

        def wr(a, v):
            if a in self.watch:
                self.writes.append(("write", s.frame, a, v, s.cpu.pc))
            orig(a, v)
        s.cpu.set_write_callback(wr)
        self.e = P.Emu.__new__(P.Emu)
        self.e.s, self.e.rom, self.e.act = s, rom, self.key
        self.e._place = P._load("spring_interaction")._place
        self.e.base = self.e.snapshot()
        self._cur_follow = None

    # ---- hooks
    def _on_dispatch(self, mm) -> None:
        if mm.cpu.ix == 0xD500:
            self.upd += 1

    def _on_follow_entry(self, mm) -> None:
        owner = mm.cpu.ix
        self._cur_follow = {"hl_offset_added_to_player_y": mm.cpu.hl, "player_x": mm.u16(0xD511), "player_y": mm.u16(0xD514), "owner_frame_at_call": mm.mem[owner + 6], "owner_slot": owner}

    def _on_follow_ret(self, mm) -> None:
        if self._cur_follow is not None:
            o = self._cur_follow["owner_slot"]
            self._cur_follow.update(owner_x_after=mm.u16(o + 0x11), owner_y_after=mm.u16(o + 0x14))
            self.follow.append(self._cur_follow)
            self._cur_follow = None

    # ---- helpers
    def slots(self, t: int) -> list:
        return [SLOT_BASE + i * SLOT_SIZE for i in range(SLOT_COUNT) if self.m[SLOT_BASE + i * SLOT_SIZE] == t]

    def place(self, x, y, vx=0, vy=0, cur=0x0E, f3=1, floor=False, prev=0, rings=0) -> None:
        self.e.restore()
        self.e.place(x, y, vx, vy, cur=cur, f3=f3, floor=floor, rings=rings, prev=prev)
        self.m[0xD501] = 0xFF
        self.m[0xD523] = 0
        self.upd = 0
        self.follow.clear()
        self.writes.clear()

    def teleport(self, x, y, vx=0, vy=0, f3=1) -> None:
        """Move Sonic and the camera (forcing creation of the mapped objects around the camera) without touching state, owner or objects."""
        self.e._place(self.s, x, y, vx & 0xFFFF, vy & 0xFFFF)
        self.m[0xD503] = f3

    def shoe(self) -> int | None:
        sl = self.slots(0x2F)
        return sl[0] if sl else None

    def row(self) -> dict:
        s, m = self.s, self.m
        r = {"u": self.upd, "x": s.u16(0xD511), "y": s.u16(0xD514), "vx": s16(s.u16(0xD516)), "vy": s16(s.u16(0xD518)), "cur": m[0xD501], "req": m[0xD502], "f3": m[0xD503], "f4": m[0xD504],
             "pframe": m[0xD506], "ptimer": m[0xD507], "f22": m[0xD522], "f23": m[0xD523], "d3a4": s.u16(0xD3A4), "d3b1": m[0xD3B1], "rings": m[0xD29A]}
        sh = self.shoe()
        if sh is not None:
            r["shoe"] = {"slot": h(sh), "state": m[sh + 1], "req": m[sh + 2], "frame": m[sh + 6], "timer": m[sh + 7], "f3": m[sh + 3], "f4": m[sh + 4], "x": s.u16(sh + 0x11), "y": s.u16(sh + 0x14)}
        else:
            r["shoe"] = None
        return r

    def run(self, frames: int, padf=None, stop=None, hook=None) -> list:
        """One row per player update (a frame can hold a lag frame with no update); the follow-hook captures of that update are attached."""
        rows, last = [], self.upd
        if padf:
            self.m[0xD137] = self.m[0xD138] = padf(0, 0)
        for f in range(frames):
            self.s.pad = padf(self.upd, f) if padf else 0
            self.follow.clear()
            self.s.run_frame()
            if hook:
                hook(self, f)
            if self.upd != last:
                last = self.upd
                r = self.row()
                r["follow"] = list(self.follow)
                rows.append(r)
                if stop and stop(r, rows):
                    break
        return rows


# --------------------------------------------------------------------------- #
# A. presentation: whole-game traces
# --------------------------------------------------------------------------- #
def slot_pieces(lab: Lab, ix: int) -> list:
    import mapped_object_registration as MR
    s, m = lab.s, lab.m
    return MR.model_slot(lab.rom, obj_x=s.u16(ix + 0x11), obj_y=s.u16(ix + 0x14), cam_x=s.u16(0xD174), cam_y=s.u16(0xD176), frame_cpu=s.u16(ix + 0x2A) - 5, flags=m[ix + 4],
                         art0=m[ix + 8], art1=m[ix + 9])


def sat_check(lab: Lab) -> bool:
    """The SAT buffer ($DB00/$DB40) starts with exactly the pieces the renderer model produces for the player slot followed by the owner slot (every update)."""
    sh = lab.shoe()
    if sh is None:
        return False
    want = [(p["sat_y"], p["sat_x"], p["tile"]) for p in slot_pieces(lab, 0xD500) + slot_pieces(lab, sh)]
    have = [(lab.m[0xDB00 + i], lab.m[0xDB40 + 2 * i], lab.m[0xDB41 + 2 * i]) for i in range(len(want))]
    return want == have


def runs_of(rows: list, keyf) -> list:
    out = []
    for r in rows:
        k = keyf(r)
        if out and out[-1]["value"] == k:
            out[-1]["last_u"] = r["u"]
            out[-1]["length"] += 1
        else:
            out.append({"value": k, "first_u": r["u"], "last_u": r["u"], "length": 1})
    return out


def presentation_trace(lab: Lab, x: int, y: int, padf, frames: int, label: str, vy: int = 0x100, check_sat: bool = True) -> dict:
    lab.place(x, y, 0, vy, cur=0x0E, f3=1)
    sat_ok, sat_bad = [], []

    def hook(l, f):
        if check_sat and l.shoe() is not None and l.m[0xD501] == 0x12:
            ok = sat_check(l)
            sat_ok.append(ok)
            if not ok:
                sat_bad.append(l.upd)
    rows = lab.run(frames, padf=padf, hook=hook)
    state12 = [r for r in rows if r["cur"] == 0x12]
    contacts = [r["u"] for i, r in enumerate(rows) if r["shoe"] and r["shoe"]["state"] == 3 and (i == 0 or not rows[i - 1]["shoe"] or rows[i - 1]["shoe"]["state"] != 3)]
    follow = [(r["u"], r["follow"][0]["hl_offset_added_to_player_y"], r["follow"][0]["owner_frame_at_call"]) for r in rows if r["follow"]]
    first = contacts[0] if contacts else None
    second = contacts[1] if len(contacts) > 1 else None
    win = [r for r in rows if second is not None and second - 2 <= r["u"] <= second + 14]
    off_rel = {}
    if second is not None:
        for u, off, fr in follow:
            if second - 2 <= u <= second + 14:
                off_rel[u - second] = {"offset_y": off, "owner_frame_at_call": fr}

    def compact(r):
        d = {k: r[k] for k in ("u", "x", "y", "vx", "vy", "cur", "req", "f3", "f4", "pframe", "ptimer", "f22", "f23")}
        if r["shoe"]:
            d["shoe"] = {k: r["shoe"][k] for k in ("state", "req", "frame", "timer", "x", "y", "f4")}
        if r["follow"]:
            d["follow_offset_y"] = r["follow"][0]["hl_offset_added_to_player_y"]
            d["follow_owner_frame_at_call"] = r["follow"][0]["owner_frame_at_call"]
        return d
    return {"label": label, "start": {"x": x, "y": y, "vy": vy, "state": "0x0E"},
            "state_12_first_update": state12[0]["u"] if state12 else None, "contact_updates": contacts,
            "bounce_period_updates": [b - a for a, b in zip(contacts, contacts[1:])],
            "shoe_frame_runs": [{"state": v[0], "frame": v[1], "first_u": e["first_u"], "last_u": e["last_u"], "length": e["length"]} for e in runs_of(rows, lambda r: (r["shoe"]["state"], r["shoe"]["frame"]) if r["shoe"] else None)
                                for v in [e["value"]] if v],
            "frame_changes_after_pickup": len([1 for a, b in zip(state12, state12[1:]) if a["shoe"] and b["shoe"] and a["shoe"]["frame"] != b["shoe"]["frame"]]),
            "player_frame_values_in_state_12": sorted({r["pframe"] for r in state12}), "player_timer_cycle_first_12": [r["ptimer"] for r in state12[:12]],
            "player_f4_values": sorted({r["f4"] for r in state12}), "shoe_f4_values": sorted({r["shoe"]["f4"] for r in state12 if r["shoe"]}),
            "shoe_f3_values": sorted({r["shoe"]["f3"] for r in state12 if r["shoe"]}),
            "follow_offsets": {"values": sorted({o for _, o, _ in follow}), "offset_16_updates_per_bounce_relative_to_contact": [k for k, v in sorted(off_rel.items()) if v["offset_y"] == 16]},
            "sat_checks": {"frames_checked": len(sat_ok), "mismatch_updates": sat_bad},
            "rows_first_pickup": [compact(r) for r in rows[:(first + 6) if first else 14] if r["u"] >= (first - 6 if first else 0)],
            "rows_second_bounce_window": [compact(r) for r in win], "follow_offset_rel_second_contact": {str(k): v for k, v in off_rel.items()}}


def art_bounds(lab: Lab, sh: int) -> dict:
    """Opaque pixel bounds of the shoe frames 1..4 relative to the shoe anchor (terrain space, i.e. including the shared +18/+1 presentation constant): from the art actually in VRAM."""
    s, m, rom = lab.s, lab.m, lab.rom
    art0 = m[sh + 8]
    pat = 256 if (s.reg[6] & 4) else 0
    table = u16(rom, 0x3C000 + 2 * 0x2F)
    out = {}
    for fr in range(1, 5):
        rec = c15(u16(rom, c15(table) + 2 * fr))
        count, coords, y_org, x_org, tiles = rom[rec], u16(rom, rec + 3), s16(u16(rom, rec + 5)), s16(u16(rom, rec + 7)), u16(rom, rec + 9)
        rows, cols = [], []
        for i in range(count):
            py, px = s16(u16(rom, c15(coords + 4 * i))), s16(u16(rom, c15(coords + 2 + 4 * i)))
            tile = (rom[c15(tiles + i)] + art0) & 0xFE
            for r in range(16):
                tb = (pat + tile + (r >> 3)) * 32 + (r & 7) * 4
                b = s.vram[tb:tb + 4]
                for c in range(8):
                    if ((b[0] | b[1] | b[2] | b[3]) >> (7 - c)) & 1:
                        rows.append(y_org + py + r + 18)
                        cols.append(x_org + px + c + 1)
        out[str(fr)] = {"opaque_rows_rel_anchor": [min(rows), max(rows)] if rows else None, "opaque_cols_rel_anchor": [min(cols), max(cols)] if cols else None, "opaque_pixels": len(rows)}
    return out


# --------------------------------------------------------------------------- #
# detach / replacement timelines
# --------------------------------------------------------------------------- #
def attach(lab: Lab, x: int, y: int, settle: int = 20) -> int:
    """Natural pickup: Sonic released above the shoes in state $0E; returns the shoe slot."""
    lab.place(x, y, 0, 0x100, cur=0x0E, f3=1)
    lab.run(settle + 20, padf=lambda u, f: 0, stop=lambda r, rs: r["cur"] == 0x12 and r["u"] > 0 and len([q for q in rs if q["cur"] == 0x12]) > settle)
    if lab.m[0xD501] != 0x12 or lab.shoe() is None:
        raise RuntimeError("pickup failed")
    return lab.shoe()


def replacement_timeline(lab: Lab, label: str, setup, padf, frames: int = 160, extra_watch=()) -> dict:
    """Run from an attached state: `setup(lab)` teleports/injects; then record until the shoe slot is gone. Reports the update that REQUESTS a new state, the update that makes it CURRENT,
    the shoe's own state changes, its removal (PC of the write that clears the slot) and the stale owner pointer."""
    sh = lab.shoe()
    lab.watch = {0xD502, 0xD3A4, 0xD3A5, sh} | set(extra_watch)
    lab.writes.clear()
    setup(lab)
    base = lab.upd
    rows = lab.run(frames, padf=(lambda u, f: padf(u - base, f)) if padf else None)
    req_row = next((r for r in rows if r["req"] != 0x12 and r["cur"] == 0x12), None)
    cur_row = next((r for r in rows if r["cur"] != 0x12), None)
    s5 = next((r for r in rows if r["shoe"] and r["shoe"]["state"] == 5), None)
    gone = next((r for r in rows if r["shoe"] is None and cur_row and r["u"] >= cur_row["u"]), None)
    w = [{"frame_index_in_run": None, "what": ("D502" if e[2] == 0xD502 else "D3A4" if e[2] in (0xD3A4, 0xD3A5) else "shoe_slot_type"), "value": e[3], "pc": h(e[4])} for e in lab.writes if e[0] == "write"]
    lab.watch = set()

    def compact(r):
        d = {k: r[k] for k in ("u", "x", "y", "vx", "vy", "cur", "req", "f3", "f22", "f23", "d3a4", "d3b1", "rings")}
        d["shoe"] = {k: r["shoe"][k] for k in ("state", "req", "frame", "x", "y")} if r["shoe"] else None
        return d
    i0 = rows.index(req_row) if req_row else 0
    return {"label": label, "request_update": req_row["u"] if req_row else None, "successor_requested": req_row["req"] if req_row else None,
            "current_state_replaced_update": cur_row["u"] if cur_row else None, "successor_current": cur_row["cur"] if cur_row else None,
            "shoe_state5_first_update": s5["u"] if s5 else None, "shoe_removed_update": gone["u"] if gone else None,
            "owner_pointer_after": h(rows[-1]["d3a4"]), "owner_pointer_changed_by_any_write": any(x["what"] == "D3A4" for x in w),
            "writes": w[:12], "rows_around_request": [compact(r) for r in rows[max(0, i0 - 2):i0 + 8]],
            "shoe_y_path_after_state5": [r["shoe"]["y"] for r in rows if r["shoe"] and r["shoe"]["state"] == 5][:12]}


# --------------------------------------------------------------------------- #
# controlled: the state-$12 callback $3B4E on the decoded MGHZ1 layout (tools/oracle.py)
# --------------------------------------------------------------------------- #
OWNER_SLOT = 0xD700
AIR_X, AIR_Y = 3400, 500


def callback_12_matrix(rom: bytes) -> dict:
    """Every branch of the original state-$12 callback: floor contact / jump press / side wall / none, with the owner slot present. Records what the object phase can observe afterwards."""
    t = I.TerrainLab(rom, "mghz1")
    o, m = t.o, t.o.mem
    w = I.act_data(rom, "mghz1")["width"]
    cx = AIR_X // 32
    rows = []
    cases = [("airborne_no_contact", {}, 0, 0, 0x100), ("floor_contact", {"floor": 1}, 0, 0, 0x200), ("floor_contact_jump_press", {"floor": 1}, 0x10, 0x10, 0x200),
             ("jump_press_airborne", {}, 0x10, 0x10, 0x100), ("side_wall_right", {"wall": 1}, 0, 0, 0x100), ("side_wall_right_and_floor", {"wall": 1, "floor": 1}, 0, 0, 0x200),
             ("floor_contact_hold_right", {"floor": 1}, 8, 0, 0x200)]
    for name, terr, pad, jump, vy in cases:
        m[0xC000:0xE000] = t.base
        y = AIR_Y
        if terr.get("floor"):
            m[0xC001 + 16 * w + cx] = 0x01
            y = 16 * 32 - 18 + 3
        if terr.get("wall"):
            m[0xC001 + 15 * w + cx] = 0x04
        o.word(0xD511, AIR_X)
        o.word(0xD514, y)
        m[0xD510] = m[0xD513] = 0
        o.word(0xD516, 0)
        o.word(0xD518, vy)
        m[0xD501] = m[0xD502] = 0x12
        m[0xD503] = 1
        m[0xD522] = 0
        m[0xD523] = 0
        m[0xD524] = 0
        m[0xD36C] = 0x81 if terr.get("floor") else 0
        m[0xD137] = pad
        m[0xD147] = jump
        o.word(0xD174, AIR_X - 100)
        o.word(0xD51C, 100)
        o.word(0xD373, 0x400)
        m[0xD52C], m[0xD52D] = 8, 24
        m[0xD29A] = 5
        m[0xD135] = 1
        m[0xDE04] = 0
        o.word(0xD3A4, OWNER_SLOT)
        for i in range(0x40):
            m[OWNER_SLOT + i] = 0
        m[OWNER_SLOT] = 0x2F
        m[OWNER_SLOT + 1] = m[OWNER_SLOT + 2] = 4
        m[OWNER_SLOT + 6] = 4
        o.cpu.ix = 0xD500
        o.call(STATE12_CALLBACK)
        rows.append({"case": name, "requested_after": m[0xD502], "vy_after": s16(o.word(0xD518)), "vx_after": s16(o.word(0xD516)), "d522_floor_bit1_after": (m[0xD522] >> 1) & 1,
                     "d522_after": m[0xD522], "f3_after": m[0xD503], "y_after": o.word(0xD514), "owner_requested_state": m[OWNER_SLOT + 2], "sound_request_de04": m[0xDE04], "rings_after": m[0xD29A],
                     "invulnerability_timer_d3b1": m[0xD3B1], "owner_y_after": o.word(OWNER_SLOT + 0x14)})
    return {"evidence": "CONTROLLED ROUTINE RESULT (callback $3B4E, owner slot $D700 present, 5 rings held)", "cases": rows,
            "invariant": "after the callback the object phase always sees D522 bit1 (floor) CLEAR: the rebound ($3B6B), the jump branch ($45ED, $4632) and the hurt tail ($494F, $495B) each clear it, and airborne updates never set it"}


# --------------------------------------------------------------------------- #
# A. presentation scenarios
# --------------------------------------------------------------------------- #
def presentation_section(rom: bytes) -> dict:
    mg = Lab(rom, "mghz", 0)
    out = {"evidence": "EMULATED ORIGINAL FRAME (whole game; SAT buffer compared with the renderer model on every checked frame)"}
    out["mghz1_plain"] = presentation_trace(mg, 1552, 200, lambda u, f: 0, 300, "MGHZ1 shoes (1552,238): released above them, no input, 300 updates")
    out["mghz1_left_right"] = presentation_trace(mg, 1552, 200, lambda u, f: 8 if (u // 40) % 2 == 0 else 4, 260, "same, Right for 40 updates then Left for 40, repeating (facing/mirroring)", check_sat=False)
    sh = mg.shoe()
    out["art_bounds_mghz"] = art_bounds(mg, sh)
    se = Lab(rom, "sez", 0)
    out["sez1_plain"] = presentation_trace(se, 224, 350, lambda u, f: 0, 260, "SEZ1 shoes (224,398), same release (camera scrolls: SAT model check skipped)", check_sat=False)
    out["art_bounds_sez"] = art_bounds(se, se.shoe())
    # equality of the cadence between the two art bases
    a, b = out["mghz1_plain"], out["sez1_plain"]
    att = lambda t: [(x["state"], x["frame"], x["length"]) for x in t["shoe_frame_runs"] if x["state"] in (3, 4)][:6]
    out["cadence_identical_between_zones"] = att(a) == att(b)
    return out


def derived_registration(rom: bytes) -> dict:
    """Sonic-to-shoe registration derived from the decoded mappings and the follow rule; verified against the SAT in presentation_section."""
    mp = mapping_frames(rom)
    def rows(fr, off):
        f = mp["frames"][str(fr)]
        ys = [off + f["y_origin"] + p["piece_y"] for p in f["piece_list"]]
        xs = [f["x_origin"] + p["piece_x"] for p in f["piece_list"]]
        return {"shoe_anchor_dy_from_sonic_anchor": off, "piece_rows_rel_sonic_anchor": [min(ys), max(ys) + 15], "piece_cols_rel_sonic_anchor": [min(xs), max(xs) + 7]}
    pl = mp["player_frame_0B"]
    p_rows = [pl["y_origin"] + p["piece_y"] for p in pl["piece_list"]]
    p_cols = [pl["x_origin"] + p["piece_x"] for p in pl["piece_list"]]
    return {"evidence": "DECODED DATA + SOURCE-TRACED BEHAVIOR ($3BA8: HL := $10 when the owner's frame (+6) is 3 else 11; $5F27: owner X := player X, owner Y := player Y + HL)",
            "rule": "owner anchor = (playerX, playerY + (16 if owner frame == 3 else 11)); the frame tested is the owner's frame AT THE TIME of the player's update (set by the previous object phase)",
            "sonic_frame_0B_rows_rel_anchor": [min(p_rows), max(p_rows) + 15], "sonic_frame_0B_cols_rel_anchor": [min(p_cols), max(p_cols) + 7],
            "shoe_frame_3_compressed": rows(3, 16), "shoe_frame_4_held": rows(4, 11), "shoe_frames_1_2_unattached_only": rows(1, 0),
            "x": "dx = 0 in every frame: the shoe is centred on Sonic's anchor (pieces -8 and 0 after the x origin) and is never mirrored (object +$04 stays 0 while Sonic's bit4 follows facing)",
            "vertical_overlap": "frame 4 overlaps Sonic's lowest piece row by 5 rows (shoe rows -5..+10, Sonic bottom row ends at -1); frame 3 starts directly below it (rows 0..15)"}


# --------------------------------------------------------------------------- #
# B. act clear while state $12
# --------------------------------------------------------------------------- #
SIGN = (3968, 270)           # MGHZ2 type $18 record
SHOES_MGHZ2 = (3760, 494)


def sign_slot(lab: Lab):
    sl = lab.slots(0x18)
    return sl[0] if sl else None


def prepare_mghz2(lab: Lab) -> dict:
    """Natural pickup of the MGHZ2 shoes and a snapshot of the whole machine (cases fork from it)."""
    attach(lab, SHOES_MGHZ2[0], 456)
    return lab.e.snapshot()


def sign_activation(rom: bytes, lab: Lab, snap: dict) -> dict:
    sweep = []
    for sx in range(300, 270, -1):
        lab.e.restore(snap)
        lab.upd = 0
        lab.teleport(SIGN[0] - sx + 104, 200, 0, 0x100)
        conv = None
        for f in range(10):
            lab.s.pad = 0
            lab.s.run_frame()
            if lab.m[0xD502] != 0x12 and conv is None:
                conv = f
        sg = sign_slot(lab)
        sweep.append({"sign_screen_x": sx, "converted_within_10_frames": conv is not None, "sign_state_after": lab.m[sg + 1] if sg else None})
    boundary = [r["sign_screen_x"] for r in sweep if r["converted_within_10_frames"]]
    lab.e.restore(snap)
    lab.upd = 0
    lab.watch = {0xD502, 0xD3A4, 0xD3A5, lab.shoe()}
    lab.writes.clear()
    lab.teleport(SIGN[0] - 200 + 104, 200, 0, 0x100)
    rows = lab.run(70, padf=lambda u, f: 0)
    tl = [{k: r[k] for k in ("u", "cur", "req", "y", "vy", "d3a4")} | {"shoe": r["shoe"] and {k: r["shoe"][k] for k in ("state", "req", "frame")}} for r in rows[:14]]
    w = [{"what": ("D502" if e[2] == 0xD502 else "D3A4" if e[2] in (0xD3A4, 0xD3A5) else "shoe_slot"), "value": e[3], "pc": h(e[4])} for e in lab.writes if e[0] == "write"]
    cb = [{"pc": h(e[2])} for e in lab.writes if e[0] == "sign_activation_callback"]
    lab.watch = set()
    req = next((r for r in rows if r["req"] != 0x12 and r["cur"] == 0x12), None)
    cur = next((r for r in rows if r["cur"] != 0x12), None)
    s5 = next((r for r in rows if r["shoe"] and r["shoe"]["state"] == 5), None)
    gone = next((r for r in rows if r["shoe"] is None and cur and r["u"] >= cur["u"]), None)
    return {"evidence": "EMULATED ORIGINAL FRAME (MGHZ2 type-$18 sign (3968,270); Sonic with attached shoes teleported so that the sign's screen X is varied; no input)",
            "conversion_screen_x_values": boundary, "conversion_screen_x_range": [min(boundary), max(boundary)] if boundary else None, "horizontal_sweep": sweep,
            "timeline": {"request_update": req["u"] if req else None, "requested": req["req"] if req else None, "current_replaced_update": cur["u"] if cur else None,
                         "shoe_state5_first_update": s5["u"] if s5 else None, "shoe_removed_update": gone["u"] if gone else None, "writes": w[:10], "activation_callback_hits": len(cb), "first_rows": tl},
            "reading": "the sign's state-2 callback $A87D runs once when the sign wakes ($61E1: screen X < 288 = RIGHT+32); it writes requested $0E only if the REQUESTED state is $12; the player's next update makes $0E "
                       "current, the shoes see that in their own next update and fall; the owner pointer is never written again"}


def sign_chain(lab: Lab, snap: dict, label: str, x: int, y: int, vx: int, padf, frames: int, inject_awake: bool, jump_after_contact: int | None = None) -> dict:
    lab.e.restore(snap)
    lab.upd = 0
    lab.teleport(x, y, vx, 0x100)
    forced = False
    ev: dict = {}
    for f in range(frames):
        pad = padf(f)
        if jump_after_contact is not None and "sign_contact" in ev and f >= ev["sign_contact"] + jump_after_contact:
            pad |= 16
        lab.s.pad = pad
        lab.s.run_frame()
        sg = sign_slot(lab)
        if sg and inject_awake and not forced and lab.m[sg + 1] <= 1:
            lab.m[sg + 1] = lab.m[sg + 2] = 3          # SYNTHETIC: the sign already woke earlier (without shoes)
            forced = True
        st = lab.m[sg + 1] if sg else None
        if st is not None and st >= 4 and "sign_contact" not in ev:
            ev["sign_contact"] = f
        ch = lab.slots(0x19)
        if ch and "child_spawned" not in ev:
            ev["child_spawned"] = f
        if ch and lab.m[ch[0] + 1] == 4 and "child_state4" not in ev:
            ev["child_state4"] = f
        if lab.m[0xD502] == 0x20 and "request_20" not in ev:
            ev["request_20"] = f
        if lab.m[0xD502] == 0x1E and "hurt_requested" not in ev:
            ev["hurt_requested"] = f
        if lab.m[0xD502] != 0x12 and lab.m[0xD501] == 0x12 and "left_12_request" not in ev:
            ev["left_12_request"] = f
        if lab.m[0xD293] & 0x20 and "act_clear_flag" not in ev:
            ev["act_clear_flag"] = f
            break
    end = {"final_player_state": lab.m[0xD501], "final_requested": lab.m[0xD502], "child_state_at_end": [lab.m[a + 1] for a in lab.slots(0x19)], "sign_state_at_end": [lab.m[a + 1] for a in lab.slots(0x18)],
           "level_timer_d2be": lab.m[0xD2BE], "shoe_present": lab.shoe() is not None, "frames_run": f + 1, "rings": lab.m[0xD29A]}
    return {"label": label, "start": {"x": x, "y": y, "vx": vx, "inject_awake_sign_SYNTHETIC": inject_awake}, "events_frame_index": ev, "end": end}


def act_clear_section(rom: bytes) -> dict:
    lab = Lab(rom, "mghz", 1)
    snap = prepare_mghz2(lab)
    out = {"activation": sign_activation(rom, lab, snap)}
    fx = {}
    fx["natural_conversion_then_walk_into_sign"] = sign_chain(lab, snap, "shoes attached, sign wakes (conversion), hold Right", 3900, 200, 0, lambda f: 8, 700, False)
    fx["synthetic_prewoken_sign_top_contact_stalls"] = sign_chain(lab, snap, "SYNTHETIC pre-woken sign, shoes kept, small rightward drift, vertical contact", 3966, 150, 0x10,
                                                                  lambda f: 8 if f < 3 else 0, 1500, True)
    fx["synthetic_prewoken_sign_top_contact_then_jump"] = sign_chain(lab, snap, "same, then B1 pressed 200 updates after the sign contact", 3966, 150, 0x10, lambda f: 8 if f < 3 else 0, 1500, True,
                                                                     jump_after_contact=200)
    fx["synthetic_prewoken_sign_side_contact"] = sign_chain(lab, snap, "SYNTHETIC pre-woken sign, horizontal contact at speed", 3944, 262, 0x100, lambda f: 8, 1500, True)
    out["chains"] = fx
    out["child_gate"] = {"evidence": "DOCUMENTED + BYTE-VERIFIED (docs/object-18-act-clear.md; type $19 state 4 callback $AB8C)",
                         "rule": "type $19 state 4: every update unless player state is $20: $037D, then if $D522 bit1 (floor) then CALL $03F5 -> $4892 (requested $20); no timeout"}
    out["callback_12_matrix"] = callback_12_matrix(rom)
    return out


# --------------------------------------------------------------------------- #
# C. detach cases
# --------------------------------------------------------------------------- #
def detach_case(lab: Lab, snap: dict, label: str, setup, padf, frames: int = 160, rings: int = 0) -> dict:
    lab.e.restore(snap)
    lab.upd = 0
    lab.m[0xD29A] = rings
    lab.m[0xD3B1] = 0
    t = replacement_timeline(lab, label, setup, padf, frames=frames)
    rows = t["rows_around_request"]
    cur = next((r for r in rows if r["cur"] != 0x12), None)
    t["rings_before"] = rings
    if cur:
        t["at_replacement"] = {k: cur[k] for k in ("vx", "vy", "f3", "d3b1", "rings")}
    t.pop("rows_around_request")
    t.pop("shoe_y_path_after_state5")
    return t


SEZ1_SPRINGS = ((1760, 896, 0), (1472, 864, 1), (1632, 896, 1))      # fixed type-$26 springs (parameter bit 7 clear) whose control run (no shoes) launches Sonic


def mapped_spring_inertness(rom: bytes) -> dict:
    lab = Lab(rom, "sez", 0)
    controls = {}
    for sx, sy, param in SEZ1_SPRINGS:                  # controls first: they start from the pristine boot snapshot
        lab.place(sx, sy + 12 - 90, 0, 0x100, cur=0x0E, f3=1)
        ctrl = lab.run(120, padf=lambda u, f: 0)
        controls[(sx, sy)] = next((q for q in ctrl if q["req"] in (0x0B, 0x1C)), None)
    attach(lab, 224, 350)
    snap = lab.e.snapshot()
    results = []
    for sx, sy, param in SEZ1_SPRINGS:
        ay = sy + 12
        control = controls[(sx, sy)]
        shoes = []
        for dx in range(-12, 13, 4):
            lab.e.restore(snap)
            lab.upd = 0
            lab.teleport(sx + dx, ay - 120, 0, 0x100)
            rows = lab.run(260, padf=lambda u, f: 0)
            reb = [r for r in rows if r["vy"] == -1920]
            spring_req = [r["u"] for r in rows if r["cur"] == 0x12 and r["req"] in (0x0B, 0x1C)]
            other = next((r for r in rows if r["req"] not in (0x12, 0x0B, 0x1C) and r["cur"] == 0x12), None)
            shoes.append({"dx": dx, "rebounds": len(reb), "rebound_y": sorted({r["y"] for r in reb}), "spring_requests": spring_req, "other_first_request": other["req"] if other else None})
        results.append({"spring": {"placement": [sx, sy], "anchor_y": ay, "parameter": param, "window_y": [ay - 33, ay - 28]}, "control_request_state_0E": control["req"] if control else None,
                        "control_request_update": control["u"] if control else None, "with_shoes": shoes})
    return {"evidence": "EMULATED ORIGINAL FRAME (SEZ1 fixed type-$26 springs; control: Sonic in $0E dropped 90 px above the spring; shoes: attached shoes, Sonic dropped 120 px above, 260 updates, X offsets -12..+12)",
            "springs": results, "spring_launches_with_shoes": sum(len(c["spring_requests"]) for r in results for c in r["with_shoes"]),
            "controls_that_launch": sum(1 for r in results if r["control_request_state_0E"] == 0x0B),
            "gates": "$782AF (fixed spring): not off-screen, Y speed >= 0, D522 bit1 (floor), requested state != $21, |dx| < 12 (strict), player Y in springY-33..-28",
            "reading": "no fixed mapped spring ever launches Sonic while the shoes are attached: the shoes' rebound clears D522 bit1 and sets Y speed -7.5 in the same update (callback_12_matrix), and the floor "
                       "contact sits 8 px higher than a standing contact (state-$12 foot offset), outside the spring's 6-px Y window; the other non-$12 requests in the sweep are terrain side walls / neighbouring solid objects"}


def detach_section(rom: bytes) -> dict:
    lab = Lab(rom, "mghz", 0)
    attach(lab, 1552, 200)
    snap = lab.e.snapshot()
    cases = {}
    for nm, rel in (("rising", 8), ("falling", 40), ("floor_contact", 61)):
        cases[f"manual_jump_{nm}"] = detach_case(lab, snap, f"B1 pressed {rel} updates after the attach point ({nm})", lambda l: None, lambda u, f, rel=rel: 16 if rel <= u < rel + 2 else 0)
    cases["type21_top_stomp"] = detach_case(lab, snap, "type $21 (1744,238) stomped from above", lambda l: l.teleport(1744, 150, 0, 0x100), lambda u, f: 0)
    cases["type21_side_contact_with_rings"] = detach_case(lab, snap, "type $21 side/low contact at speed, 5 rings", lambda l: l.teleport(1650, 230, 0x400, 0), lambda u, f: 8, frames=200, rings=5)
    cases["terrain_wall_side_branch_with_rings"] = detach_case(lab, snap, "terrain wall (MGHZ1 shaft wall, X3575), 5 rings", lambda l: l.teleport(3560, 600, 0x100, 0), lambda u, f: 8, rings=5)
    cases["terrain_upright_spring"] = detach_case(lab, snap, "terrain upright spring MGHZ1 cell (110,25)", lambda l: l.teleport(3536, 700, 0, 0x100), lambda u, f: 0)
    return {"evidence": "EMULATED ORIGINAL FRAME (MGHZ1 shoes (1552,238) attached naturally, then Sonic teleported next to the trigger; the shoes, owner pointer and state stay as they are)", "cases": cases,
            "mapped_spring": mapped_spring_inertness(rom)}


# --------------------------------------------------------------------------- #
# object-mirrored side contact, classification, build, CLI
# --------------------------------------------------------------------------- #
def monitor_side_case(rom: bytes) -> dict:
    """SEZ1: a type-$10 monitor (368,238) beside the spring: its $5FA0 side contact mirrors into D523 bit2 and triggers the state-$12 side-wall branch."""
    lab = Lab(rom, "sez", 0)
    attach(lab, 224, 350)
    snap = lab.e.snapshot()
    return detach_case(lab, snap, "SEZ1 monitor $10 (368,238): Sonic with shoes drops beside it (X352)", lambda l: l.teleport(352, 200, 0, 0x100), lambda u, f: 0, frames=140, rings=5)


def poc_facts() -> dict:
    return {"files": ["objects/OBJ_chaos_object_2F/Step_0.gml", "objects/OBJ_chaos_object_2F/Draw_0.gml", "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml", "scripts/SCR_chaos_spring/SCR_chaos_spring.gml"],
            "facts": ["object Step mirrors the ROM states 1/3/4/5 (frames 1/2 every 8 ticks, frame 3 for 12 ticks then 4, detach when player state != $12)",
                      "Sonic sprite in state $12: SPR_player_jump, image_index 0, image_speed 0 (single record), facing from player_flags bit 4",
                      "SCR_chaos_spring: a mapped spring contact is judged on the pre-bounce Y speed / floor flag / anchor of the shoes' relaunch (so a mapped spring CAN launch state $12) - the original never does",
                      "state-$12 side-wall branch uses the $494F hurt movement without damage flags (matches the ROM)"]}


def classification() -> list:
    C, P_, A_, U = "CANONICAL", "POC DIVERGENCE", "EXPLICIT ADAPTER CANDIDATE", "UNRESOLVED"
    return [
        {"id": "P1", "observation": "The shoe sprite shows frames 1/2 (alternating every 8 updates) only while unattached; attached it shows frame 3 for 12 updates after every floor contact and frame 4 otherwise", "class": C,
         "evidence": "object scripts $8B2C/$8B40/$8B49; whole-game traces (contact updates 12/93/174/255: period 81, frame 3 length 12, frame 4 length 69)"},
        {"id": "P2", "observation": "While attached the shoe changes frame exactly twice per bounce (3 at the contact update, 4 twelve updates later); there is no continuous shoe animation", "class": C,
         "evidence": "shoe_frame_runs; the frame-4 record repeats duration 4 without changing frame"},
        {"id": "P3", "observation": "Sonic's animation record is the single frame $0B (duration 4, restart) for the whole of state $12; it changes only with facing (+$04 bit4)", "class": C,
         "evidence": "player script $8346; player_frame_values_in_state_12 = [11]; f4 values {0,16}"},
        {"id": "P4", "observation": "Registration: owner anchor = (player X, player Y + 16 if the owner's frame is 3 else 11), evaluated in the player update from the frame left by the previous object phase; dx = 0; the shoe is never mirrored", "class": C,
         "evidence": "$3BA8/$5F27 hooks (follow_offsets), SAT buffer equals the renderer model on every checked frame except the pickup update, shoe +$04 = 0 while Left/Right alternate"},
        {"id": "P5", "observation": "SEZ (art base $94) and MGHZ (art base $AC) behave identically", "class": C, "evidence": "cadence_identical_between_zones"},
        {"id": "P6", "observation": "The POC object Step and player sprite choice mirror these scripts in source; the reported 'too active' presentation cannot be explained from source and needs a capture compared with the frame fixtures", "class": U,
         "evidence": "POC SOURCE (READ-ONLY); the JSON fixtures give exact update indices"},
        {"id": "B1", "observation": "The sign's contact does not request $20 and does not touch the footwear", "class": C, "evidence": "type $18 state-3 callback; whole-game chains"},
        {"id": "B2", "observation": "The only footwear clear paths are two requested-state conversions $12 -> $0E: type $18 state 2 (sign wakes: screen X < 288 = RIGHT+32) and type $50 state 0 (boss creation)", "class": C,
         "evidence": "opcode scan (2 sites), activation sweep 271..287 converts, 288+ does not"},
        {"id": "B3", "observation": "The sign's wake trigger is an EDGE(RIGHT,+32) relation; on a wide view the generic wake band must be adapted explicitly", "class": A_, "evidence": "docs/viewport-semantics-audit.md generic lifetime bands"},
        {"id": "B4", "observation": "Replacement timeline: request written in the sign's object phase of update N, $0E current in N+1, shoes request state 5 in N+1 and are in state 5 in N+2; the owner pointer $D3A4 is never cleared", "class": C,
         "evidence": "activation timeline (request 3, current 4, shoe state 5 at 5); opcode scan of $D3A4"},
        {"id": "B5", "observation": "Type $2F removes itself only through the generic mapped-object lifetime routine $61E1 (type $FE, tracked placement released); the placement later re-creates the shoes", "class": C,
         "evidence": "write watch: slot type $FE at $625F then free, later $2F written by the placement creator $80F6"},
        {"id": "B6", "observation": "The act-clear child waits for D522 bit1 with no timeout; state $12 clears that bit in every branch, so with shoes attached and the sign already awake a vertical sign contact stalls act completion until a button press, hurt or spring detaches the shoes", "class": C,
         "evidence": "SYNTHETIC pre-woken sign: 1500 updates, child state 4, no request $20; B1 after contact+200 -> request $20 at +90; callback_12_matrix invariant"},
        {"id": "B7", "observation": "Whether that stall is reachable in a canonical placement is not shown: the only shoes within 288 px of a sign are MGHZ2 (3760,494) vs (3968,270) and the sign's wake normally converts the shoes first", "class": U,
         "evidence": "placement census; sign wake always converts when the sign wakes while shoes are attached"},
        {"id": "B8", "observation": "A horizontal sign contact in state $12 is a side-wall hurt (not a stall): the act-clear chain then completes after the landing", "class": C, "evidence": "chains: side contact hurt at the contact update, request $20 at +278"},
        {"id": "C1", "observation": "Type $21 top stomp: successor $0B (via $5F17 -> $480C, Y speed -6.75); shoes detach (state 5 two updates after the request)", "class": C, "evidence": "type21_top_stomp"},
        {"id": "C2", "observation": "Type $21 side/low contact: ordinary damage $1E (rings lost, invulnerability); shoes detach", "class": C, "evidence": "type21_side_contact_with_rings"},
        {"id": "C3", "observation": "Mapped type $26 springs never launch or detach a $12 Sonic (D522 bit1 is always clear after the shoes' callback and the floor contact sits 8 px higher than a standing contact)", "class": C,
         "evidence": "3 SEZ1 springs whose control launches: 0 launches with shoes over 21 x 260 updates; callback_12_matrix. Corrects docs/powerup-shoes-audit.md section 6 (isolated-handler result)"},
        {"id": "C4", "observation": "The POC lets a mapped spring launch state $12 (contact judged on the pre-bounce Y speed/floor)", "class": P_, "evidence": "POC SOURCE (READ-ONLY): SCR_chaos_spring.gml shoe_bounced / shoe_prev_vy"},
        {"id": "C5", "observation": "Side-wall branch ($3B9D -> $494F): requested $1E, shoes detach in the same update, NO ring loss, NO invulnerability; triggered by terrain walls and by object contacts mirrored into D523 bit2/3 (monitor $10, sign $18)", "class": C,
         "evidence": "terrain_wall_side_branch_with_rings (rings 5 -> 5, D3B1 0, +$03 = $01), monitor_side_case, sign side chain"},
        {"id": "C6", "observation": "Terrain upright spring: successor $0B, Y speed -7.5, shoes detach", "class": C, "evidence": "terrain_upright_spring"},
        {"id": "C7", "observation": "Manual jump: successor $0A (-4.25), the owner is set to state 5 in the same update", "class": C, "evidence": "manual_jump_* (rising/falling/floor contact)"},
    ]


def agents_candidates() -> list:
    return [
        "Spring Shoes presentation: attached shoe = frame 3 for 12 updates after every floor contact, frame 4 otherwise (unattached: frames 1/2 every 8); Sonic's record is the single frame $0B; shoe anchor = Sonic X, "
        "Sonic Y + 16 (frame 3) / +11, one-update lag, never mirrored.",
        "A type-$18 sign (and the type-$50 boss) converts a REQUESTED state $12 to $0E when it wakes (screen X < 288 = EDGE(RIGHT,+32)); no other code clears Spring Shoes except the state change itself. $D3A4 is never cleared.",
        "Spring Shoes can stall act completion only in the narrow case of an already-awake sign plus a vertical contact (the child waits for D522 bit1, which state $12 always clears); a side contact hurts instead.",
        "Mapped $26 springs never act on state $12; terrain springs, $21 stomps, damage and manual jump do. The state-$12 side-wall branch hurts without ring loss or invulnerability and is also triggered by object contacts mirrored into D523.",
    ]


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    out: dict = {"rom_sha256": ROM_SHA256, "research_base": RESEARCH_BASE, "scope": "Spring Shoes (type $2F / state $12) presentation, act clear and detach audit; Research only",
                 "evidence_classes": ["DECODED DATA", "BYTE-VERIFIED ASSEMBLY", "SOURCE-TRACED BEHAVIOR", "CONTROLLED ROUTINE RESULT", "EMULATED ORIGINAL FRAME", "SYNTHETIC CONTROL", "POC SOURCE (READ-ONLY)", "UNRESOLVED"],
                 "static_only": static_only}
    part_a = {"object_scripts": object_scripts(rom), "mapping_frames": mapping_frames(rom), "player_state_12_script": player_state12_script(rom), "static_facts": static_facts(rom),
              "registration": derived_registration(rom)}
    part_b: dict = {"callback_12_matrix": callback_12_matrix(rom)}
    part_c: dict = {}
    if not static_only:
        part_a["traces"] = presentation_section(rom)
        part_b.update(act_clear_section(rom))
        part_c = detach_section(rom)
        part_c["object_mirrored_side_contact_monitor"] = monitor_side_case(rom)
    out.update({"part_a_presentation": part_a, "part_b_act_clear": part_b, "part_c_detach": part_c, "classification": classification(), "agents_candidates": agents_candidates(), "poc_source_read_only": poc_facts()})
    return out


def dumps(data: dict) -> str:
    return json.dumps(data, indent=1) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    a = ap.parse_args()
    rom = L.load_rom(a.rom)
    text = dumps(build(rom, a.static_only))
    if a.check:
        if OUTPUT.read_text(encoding="utf-8") != text:
            raise SystemExit("cache mismatch: " + str(OUTPUT))
        print("spring-shoes-presentation cache matches")
    else:
        OUTPUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUTPUT} ({len(text)} bytes)")


if __name__ == "__main__":
    main()

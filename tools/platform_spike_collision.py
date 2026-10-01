#!/usr/bin/env python3
"""THZ platform (type $28) and spike (static terrain type 5 / moving type $1B) collision audit - research only, deterministic.

Answers: every THZ1/THZ2 platform mechanism and its exact support / carry / detach rules, the exact static terrain-spike
probes and damage chain, the moving-spike object contact and timing, the damage gate, player-state exclusions, the update
order of player / platform / terrain / damage, and the presentation anchors.
Output: data/rom-cache/platform-spike-collision.json (numeric labels only; no ROM bytes beyond 16-byte prefixes).

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT (original Z80 routines
on tools/oracle.py), EMULATED ORIGINAL FRAME (tools/sms_frame_harness.py, whole game), POC SOURCE (READ-ONLY), UNRESOLVED.

Usage:
  python tools/platform_spike_collision.py ROM.sms [--check] [--static-only]
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
OUTPUT = ROOT / "data" / "rom-cache" / "platform-spike-collision.json"
ACTS = ("thz1", "thz2", "thz3")
ACT_INDEX = {"thz1": 0, "thz2": 1, "thz3": 2}
LAYOUT_BASE = 0xC001
LAYOUT_W = {"thz1": 128, "thz2": 128, "thz3": 80}
BANK_PLATFORM = 30            # type $28 code and scripts: file $78000, CPU $8000
BANK_SPIKE = 12               # type $1B code and scripts: file $30000, CPU $8000
SLOT = 0xD700                 # fixture object slot (slot index 8 -> object id 9)
PLATFORM_SOLID_ID = 9
FLOOR_HANDLER_TABLE = 0x6973
ROUTINE_FLOOR_SPIKE = 0x6ACE  # terrain type 5 foot handler
HURT_ENTRY = 0x48F7           # shared hurt/death entry reached by every spike path


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def s16(v: int) -> int:
    return (v + 32768) % 65536 - 32768


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rom_of(bank: int, cpu: int) -> int:
    return cpu if cpu < 0x8000 else bank * 0x4000 + cpu - 0x8000


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM")


def _load(name: str):
    if name in sys.modules:
        return sys.modules[name]
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
    "POC SOURCE (READ-ONLY)": "value read from the Windows POC project files; never executed, never modified",
    "UNRESOLVED": "not established",
}

# (name, bank, first CPU, end CPU exclusive, purpose)
ROUTINES = [
    ("platform_init_8585", BANK_PLATFORM, 0x8585, 0x85FE, "type $28 initializer: parameter -> state, flags, counters, object id ($0332)"),
    ("platform_clear_deltas_8577", BANK_PLATFORM, 0x8577, 0x8585, "zero carry deltas +$38/+$39/+$23/+$24 (script call at every state entry)"),
    ("platform_state13_85fe", BANK_PLATFORM, 0x85FE, 0x8628, "stationary contact platform (param &$7F = 5 or 11): contact -> state +$36 (or 14)"),
    ("platform_state1_14_8628", BANK_PLATFORM, 0x8628, 0x8662, "horizontal mover (states 1/14): sign gate on player Y speed, move, X delta, support"),
    ("platform_state10_8662", BANK_PLATFORM, 0x8662, 0x86A1, "horizontal mover with reversal counter (state 10)"),
    ("platform_state2_12_86a1", BANK_PLATFORM, 0x86A1, 0x86DA, "vertical mover without reversal (states 2/12): $8866 gate, move, Y delta, support"),
    ("platform_state11_86da", BANK_PLATFORM, 0x86DA, 0x8719, "vertical mover with reversal counter (state 11, THZ param $0A lifts)"),
    ("platform_state4_8719", BANK_PLATFORM, 0x8719, 0x879A, "touch-triggered falling platform (state 4), unused by THZ placements"),
    ("platform_state5_879a", BANK_PLATFORM, 0x879A, 0x87B2, "static support platform with weight sag (state 5, THZ param $84)"),
    ("platform_state6_87b2", BANK_PLATFORM, 0x87B2, 0x87E2, "touch-started vertical mover (state 6), unused by THZ placements"),
    ("platform_state7_87e2", BANK_PLATFORM, 0x87E2, 0x8812, "touch-started horizontal mover (state 7), unused by THZ placements"),
    ("platform_support_8814", BANK_PLATFORM, 0x8814, 0x8843, "shared support test: owner check, $6328 overlap, claim $D3C0, sag counter, carry"),
    ("platform_clear_8843", BANK_PLATFORM, 0x8843, 0x8866, "shared support clear: sag release, mirrored side-bit clear, release $D3C0 if owner"),
    ("platform_gate_8866", BANK_PLATFORM, 0x8866, 0x88A0, "relative-vertical-speed gate: returns $FF when platform Y speed > player Y speed (signed)"),
    ("platform_carry_88a0", BANK_PLATFORM, 0x88A0, 0x88C1, "carry: player Y = platform Y - (+$2D - 2); player X += +$23/+$24"),
    ("platform_sag_88c1", BANK_PLATFORM, 0x88C1, 0x88FB, "sag down/up one pixel per update (counter +$35, limit 8)"),
    ("platform_sag_88fb", BANK_PLATFORM, 0x88FB, 0x8908, "sag dispatcher: only when +$25 bit 7; +$33 selects down/up"),
    ("platform_keepalive_8908", BANK_PLATFORM, 0x8908, 0x8925, "removal when the player is >= 640 px (X) or >= 672 px (Y) away while +$04 bit 1 is set"),
    ("platform_reverse_counter_8925", BANK_PLATFORM, 0x8925, 0x8947, "reversal period counter (B = $10, +$30 then +$37 reloaded from +$34)"),
    ("platform_reverse_80f1", BANK_PLATFORM, 0x80F1, 0x8105, "negate Y velocity (+$18/+$19)"),
    ("overlap_6328", 1, 0x6328, 0x640B, "shared closed-interval object/player overlap (docs/collision-geometry-audit.md)"),
    ("object_move_60fb", 1, 0x60FB, 0x613C, "integrate +$16/+$17 into X and +$18/+$19 into Y (8.8 fixed point, sign-extended)"),
    ("object_id_606b", 1, 0x606B, 0x6089, "A = ((IX - $D500) >> 6) + 1: object id used as the support owner"),
    ("merge_flags_64cb", 1, 0x64CB, 0x64F0, "player D523 = D522 | (D521 >> 4) unless attacking and unsupported"),
    ("player_update_3fef", 1, 0x3FEF, 0x401A, "shared player updater: clamp, X integration, Y integration, terrain, damage"),
    ("player_x_integration_402a", 1, 0x402A, 0x408D, "player X integration"),
    ("player_y_integration_4097", 1, 0x4097, 0x4141, "player Y integration (returns early when grounded on a platform)"),
    ("terrain_dispatch_690b", 1, 0x690B, 0x6973, "terrain pass: floor sample, previous-surface projection $6F61, type dispatch"),
    ("floor_projection_6f61", 1, 0x6F61, 0x715E, "projection against the PREVIOUS surface flags ($D36C); sets floor bit D522.1"),
    ("floor_spike_handler_6ace", 1, 0x6ACE, 0x6AE3, "terrain type 5, foot probe: tile != $F4/$F5, floor bit, not invulnerable -> $48F7"),
    ("side_probe_dispatch_715e", 1, 0x715E, 0x71B2, "right ($716B) and left ($7210) side probes, type dispatch"),
    ("side_type5_right_7306", 1, 0x7306, 0x7357, "type 5 side tail: right ($7306) and left ($7329); damage only for tiles $F4/$F5"),
    ("ceiling_probe_73c9", 1, 0x73C9, 0x753E, "ceiling pass; type 5 tail $74E7: damage only for tiles $3E/$3F"),
    ("damage_dispatch_48bc", 1, 0x48BC, 0x48F7, "damage gate: +3 bit 7/6, power selector $D532, request $D3B0, contact $D520"),
    ("hurt_48f7", 1, 0x48F7, 0x4984, "hurt: state $11 branch, ring scatter, invulnerability $D3B1, state $1E, knockback"),
    ("death_4984", 1, 0x4984, 0x49C3, "no-ring path: state $1F, Y speed -5.0"),
    ("invulnerability_49f7", 1, 0x49F7, 0x4A2E, "invulnerability countdown $D3B1 and flicker; clears +3 bits 7/6 at zero"),
    ("spike_init_ac7d", BANK_SPIKE, 0xAC7D, 0xAC8B, "type $1B initializer: +$03 bit 7, request state 1, clear cooldown"),
    ("spike_rise_ac8b", BANK_SPIKE, 0xAC8B, 0xACC3, "state 1: contact test FIRST, then Y -= 6 until +$3C - Y == 18"),
    ("spike_hold_acc3", BANK_SPIKE, 0xACC3, 0xACCC, "state 2: contact test only"),
    ("spike_retract_accc", BANK_SPIKE, 0xACCC, 0xACFD, "state 3: Y += 6 until Y >= +$3C; no contact test"),
    ("spike_contact_acfd", BANK_SPIKE, 0xACFD, 0xAD59, "contact helper: cooldown, rising gate, $6328, top -> damage request, side -> push"),
    ("overlap_object_wrapper_033b", 0, 0x033B, 0x033E, "vector $033B -> $6328"),
]


def routine_table(rom: bytes) -> list:
    out = []
    for name, bank, a, b, purpose in ROUTINES:
        o, e = rom_of(bank, a), rom_of(bank, b)
        out.append({"name": name, "bank": bank, "cpu": h(a), "rom_offset": h(o, 5), "end_cpu_exclusive": h(b), "length": b - a,
                    "sha256": sha(rom[o:e]), "first_16_bytes": rom[o:o + 16].hex(), "purpose": purpose})
    return out


# --------------------------------------------------------------------------- #
# data sources
# --------------------------------------------------------------------------- #
def level_json(act: str, name: str):
    return json.loads((ROOT / "data" / "rom-cache" / "levels" / act / name).read_text(encoding="utf-8"))


def layout_rows(act: str) -> list:
    return level_json(act, "layout.json")["rows"]


def records(act: str, type_id: int) -> list:
    want = f"0x{type_id:02X}"
    return [r for r in level_json(act, "objects.json")["records"] if r["type_id"] == want]


def block_header(rom: bytes, blk: int) -> dict:
    import rom as R
    return R.header(rom, blk)


def runs32(profile) -> list:
    out, start = [], 0
    for i in range(1, 33):
        if i == 32 or profile[i] != profile[start]:
            out.append([start, i - 1, h(profile[start], 2)])
            start = i
    return out


# --------------------------------------------------------------------------- #
# object scripts (animation engine records / commands)
# --------------------------------------------------------------------------- #
CMD_PARAM_BYTES = {0x00: 0, 0x01: 2, 0x02: 4, 0x07: 2, 0x09: 2, 0x0C: 2}
CMD_NAMES = {0x00: "loop-or-switch", 0x01: "call-routine", 0x02: "set-velocity(X,Y)", 0x07: "jump-to-script", 0x09: "object[off]=value", 0x0C: "object[off]|=value"}


def decode_script(rom: bytes, bank: int, cpu: int, limit: int = 12) -> list:
    """Decode one state script (records `duration frame callback` and `FF cmd params`) using only commands whose length is byte-verified."""
    o, out = rom_of(bank, cpu), []
    for _ in range(limit):
        if rom[o] != 0xFF:
            out.append({"record": {"duration": rom[o], "frame": rom[o + 1], "callback": h(rom[o + 2] | rom[o + 3] << 8)}})
            o += 4
            continue
        cmd = rom[o + 1]
        n = CMD_PARAM_BYTES.get(cmd)
        if n is None:
            out.append({"command": h(cmd, 2), "undecoded": True})
            break
        p = list(rom[o + 2:o + 2 + n])
        row = {"command": h(cmd, 2), "meaning": CMD_NAMES[cmd], "params": [h(x, 2) for x in p]}
        if cmd == 0x02:
            row["x_speed_8_8"] = s16(p[0] | p[1] << 8)
            row["y_speed_8_8"] = s16(p[2] | p[3] << 8)
        if cmd in (0x01, 0x07):
            row["target_cpu"] = h(p[0] | p[1] << 8)
        out.append(row)
        o += 2 + n
        if cmd in (0x00, 0x07):
            break
    return out


# --------------------------------------------------------------------------- #
# 1. platform inventory
# --------------------------------------------------------------------------- #
def platform_placements() -> dict:
    out = {}
    for act in ACTS:
        rows = []
        for r in records(act, 0x28):
            p = int(r["parameter"], 16)
            aux1 = int(r["aux1"], 16)
            state = ((p & 0x3F) + 1)
            if (p & 0x7F) in (11, 5):
                state = 13
            rows.append({
                "act": act, "record_index": r["index"], "rom_offset": r["rom_offset"], "raw_bytes": r["raw_bytes"],
                "world_x": r["world_x"], "world_y": r["world_y"], "flags": r["flags"], "parameter": r["parameter"], "aux0": r["aux0"], "aux1": r["aux1"],
                "initial_state": state, "weight_sag_flag_+25": bool(p & 0x80), "+26_flag": bool(p & 0x40),
                "reversal_period_updates": 16 * aux1 if state == 11 else None})
        out[act] = rows
    return out


def platform_modes(rom: bytes) -> dict:
    """The 15 type-$28 states: callback, script commands, and whether any THZ placement can reach them."""
    base = rom_of(BANK_PLATFORM, 0x8439)
    placed = {}
    for act, rows in platform_placements().items():
        for r in rows:
            placed.setdefault(r["initial_state"], []).append(f'{act}#{r["record_index"]}')
    meanings = {
        0: "init request (callback $8585)",
        1: "horizontal mover, X speed +1.0, sign gate only (callback $8628)",
        2: "vertical mover, Y speed -1.0, no reversal ($86A1)",
        3: "inert ($8718 = RET)",
        4: "touch-triggered falling platform ($8719)",
        5: "static support platform with weight sag ($879A)",
        6: "touch-started vertical mover ($87B2)",
        7: "touch-started horizontal mover ($87E2)",
        8: "inert ($8812 = RET)",
        9: "inert ($8813 = RET)",
        10: "horizontal mover with reversal ($8662)",
        11: "vertical mover with reversal, Y speed -1.0 initially ($86DA)",
        12: "vertical mover ($86A1) with a delayed script",
        13: "stationary contact platform ($85FE)",
        14: "horizontal mover ($8628) entered from state 13",
    }
    rows = []
    for st in range(15):
        ptr = rom[base + 2 * st] | rom[base + 2 * st + 1] << 8
        rows.append({"state": st, "script_cpu": h(ptr), "script": decode_script(rom, BANK_PLATFORM, ptr), "role_label": meanings[st],
                     "placed_by": placed.get(st, [])})
    return {"evidence": "DECODED DATA + BYTE-VERIFIED ASSEMBLY (commands 00/01/02/07/0C; lengths read from the handlers $66B9..$68CF)", "table_cpu": "0x8439",
            "table_rom_offset": h(base, 5), "states": rows,
            "parameter_rule": "state = (parameter & $3F) + 1; if (parameter & $7F) is 5 or 11 the state is forced to 13; parameter bit 7 -> +$25 = $FF (weight sag), bit 6 -> +$26 = $FF",
            "used_by_thz": sorted(placed), "note": "THZ1/THZ2 placements reach only states 5 and 11. Every other state is supported by the ROM code but has no THZ1/THZ2/THZ3 placement."}


# --------------------------------------------------------------------------- #
# 2. platform controlled lab (original routines on tools/oracle.py)
# --------------------------------------------------------------------------- #
class ObjectLab:
    """One object slot plus the player slot on a fresh Oracle; every case restores the same RAM image."""

    def __init__(self, rom: bytes, type_id: int, record_bytes: bytes, bank: int, flags4: int, cam=(0, 0)):
        from oracle import Oracle
        self.rom, self.bank = rom, bank
        self.o = Oracle(rom)
        self.m = self.o.mem
        o, m = self.o, self.m
        o.bank(2, 0x1C)
        m[0xDA00:0xDA09] = record_bytes
        m[SLOT:SLOT + 0x40] = bytes(0x40)
        o.cpu.ix = SLOT
        o.cpu.iy = SLOT
        o.cpu.hl = 0xDA00
        o.call(0x80EB, bc=0xD418)
        self.ox, self.oy = o.word(SLOT + 0x11), o.word(SLOT + 0x14)
        o.word(0xD174, max(self.ox - 100, 0))
        o.word(0xD176, max(self.oy - 100, 0))
        m[0xD500] = 1
        m[0xD52C], m[0xD52D] = 8, 24
        self.frame()
        self.frame()                       # engine record load + first callback (the initializer runs on the first one)
        m[SLOT + 4] = flags4
        self.snap = bytes(m[0xC000:0xE000])

    def engine(self) -> None:
        self.o.bank(2, self.bank)
        self.m[0xD12B] = self.bank
        self.o.cpu.ix = SLOT
        self.o.call(0x64FA)

    def callback(self) -> int:
        m, o = self.m, self.o
        cb = m[SLOT + 0xC] | m[SLOT + 0xD] << 8
        if cb:
            o.bank(2, self.bank)
            m[0xD12B] = self.bank
            o.cpu.ix = SLOT
            o.call(cb)
        return cb

    def frame(self) -> int:
        self.engine()
        return self.callback()

    def reset(self) -> None:
        self.m[0xC000:0xE000] = self.snap

    def player(self, px, py, vx=0, vy=0, f3=0, cur=1, req=1, ex=8, ey=24, d3c0=0, f22=0):
        o, m = self.o, self.m
        o.word(0xD511, px)
        o.word(0xD514, py)
        o.word(0xD516, vx & 0xFFFF)
        o.word(0xD518, vy & 0xFFFF)
        m[0xD503], m[0xD501], m[0xD502] = f3, cur, req
        m[0xD52C], m[0xD52D] = ex, ey
        m[0xD3C0] = d3c0
        m[0xD522] = f22
        m[0xD520] = m[0xD521] = m[0xD523] = 0

    def obj16(self, off: int) -> int:
        return self.o.word(SLOT + off)


def platform_record(world_x: int, world_y: int, param: int, aux1: int) -> bytes:
    sx, sy = world_x + 256, world_y + 256
    return bytes([0x28, sx & 0xFF, sx >> 8, sy & 0xFF, sy >> 8, 0x00, param, 0x6A, aux1])


def platform_lab(rom: bytes, state_param: int, aux1: int = 0, world=(1024, 512), flags4: int = 0x00) -> ObjectLab:
    return ObjectLab(rom, 0x28, platform_record(world[0], world[1], state_param, aux1), BANK_PLATFORM, flags4)


# --------------------------------------------------------------------------- #
# models of the recovered platform rules (each is checked against the original routines below)
# --------------------------------------------------------------------------- #
def model_gate_8866(plat_vy: int, player_vy: int) -> int:
    """$8866: $FF (no support this update) when the platform Y speed is greater than the player's, both signed 16-bit."""
    return 0xFF if s16(plat_vy) > s16(player_vy) else 0


def model_contact(dx: int, dy: int, ex=8, ey=24, oex=16, oey=16) -> int:
    """Platform-side $6328 outcome as one bit among 1 (player above), 2 (below), 4 (right), 8 (left); 0 = no contact (closed boxes)."""
    span = ex + oex
    if abs(dx) > span:
        return 0
    if dx >= 0:
        c, hbit = span - dx, 4
    else:
        c, hbit = span - (-dx), 8
    if dy >= 0:
        if dy > ey:
            return 0
        lv, vbit = ey - dy, 2
    else:
        if -dy > oey:
            return 0
        lv, vbit = oey - (-dy), 1
    return hbit if c < lv else vbit


def model_support(dx: int, dy: int, plat_vy: int, player_vy: int, ex=8, ey=24, oex=16, oey=16, owner=0) -> bool:
    """Support is claimed iff the platform owns or can claim $D3C0, the gate passes and the contact is the vertical 'player above' bit."""
    if owner not in (0, PLATFORM_SOLID_ID):
        return False
    if model_gate_8866(plat_vy, player_vy):
        return False
    return model_contact(dx, dy, ex, ey, oex, oey) == 1


# --------------------------------------------------------------------------- #
# 3. emulated original frames (tools/sms_frame_harness.py through the shared boot of tools/object_18.py)
# --------------------------------------------------------------------------- #
_REGS = ("af", "bc", "de", "hl", "alt_af", "alt_bc", "alt_de", "alt_hl", "ix", "iy", "sp", "pc", "ir", "iff1", "iff2", "halted", "ticks_to_stop")
PAD = dict(UP=1, DOWN=2, LEFT=4, RIGHT=8, B1=16, B2=32)
PLAYER = 0xD500


class Emu:
    """Boots the original game into a THZ act once, then forks cases from a snapshot (deterministic)."""
    _cache: dict = {}

    def __init__(self, rom: bytes, act: str = "thz1"):
        self.rom = rom
        self.act = act
        si = _load("spring_interaction")
        self.s = si._boot(rom, ACT_INDEX[act])
        self._place = si._place
        for _ in range(3):
            self.s.run_frame()
        self.base = self.snapshot()

    # -- state capture
    def snapshot(self) -> dict:
        s, c = self.s, self.s.cpu
        return {"regs": {r: getattr(c, r) for r in _REGS}, "mem": bytes(s.mem[0:0x10000]), "slot": list(s.slot), "vram": bytes(s.vram),
                "cram": bytes(s.cram), "reg": list(s.reg), "line_regs": list(s.line_regs), "vsc": getattr(s, "vscroll_latched", 0),
                "vdp": {k: getattr(s, k) for k in ("latch", "code", "addr", "buffer", "status", "line", "line_counter", "line_irq", "pad", "frame")}}

    def restore(self, sn: dict | None = None) -> None:
        sn = sn or self.base
        s = self.s
        for k, v in sn["regs"].items():
            setattr(s.cpu, k, v)
        s.mem[0:0x10000] = sn["mem"]
        s.slot = list(sn["slot"])
        s.vram[:] = sn["vram"]
        s.cram[:] = sn["cram"]
        s.reg = list(sn["reg"])
        for k, v in sn["vdp"].items():
            setattr(s, k, v)
        s.line_regs = list(sn["line_regs"])
        s.vscroll_latched = sn["vsc"]

    # -- helpers
    def m(self):
        return self.s.mem

    def u16(self, a: int) -> int:
        return self.s.u16(a)

    def place(self, x, y, vx=0, vy=0, cur=0x0E, f3=1, floor=False, rings=0, prev=None):
        """Teleport Sonic (and the camera, forcing creation of nearby mapped objects) and set the movement/state bytes."""
        s, m = self.s, self.s.mem
        self._place(s, x, y, vx & 0xFFFF, vy & 0xFFFF)
        m[0xD502] = cur                    # REQUESTED state only: the engine loads that state's script/callback on the next update
        m[0xD503] = f3
        m[0xD522] = 0x02 if floor else 0
        s.w16(0xD36B, 0) if prev is None else None
        if prev is not None:
            m[0xD36C] = prev
        m[0xD29A] = rings

    def slot_of(self, type_id: int, nth: int = 0):
        m = self.s.mem
        found = [0xD540 + i * 0x40 for i in range(19) if m[0xD540 + i * 0x40] == type_id]
        return found[nth] if len(found) > nth else None

    def run(self, frames: int, padfn=None, rec=None, stop=None) -> list:
        out = []
        for f in range(frames):
            self.s.pad = padfn(f) if padfn else 0
            self.s.run_frame()
            if rec:
                out.append(rec(self, f))
            if stop and stop(self, f):
                break
        return out


def player_rec(e: Emu) -> dict:
    m, s = e.s.mem, e.s
    return {"x": s.u16(0xD511), "y": s.u16(0xD514), "vx": s16(s.u16(0xD516)), "vy": s16(s.u16(0xD518)), "cur": m[0xD501], "req": m[0xD502], "f3": m[0xD503],
            "f22": m[0xD522], "f23": m[0xD523], "d3c0": m[0xD3C0], "inv": m[0xD3B1], "rings": m[0xD29A]}


# --------------------------------------------------------------------------- #
# 4. static terrain spikes (type 5): controlled terrain pass ($690B) with the hurt entry watched
# --------------------------------------------------------------------------- #
SPIKE_CELLS = {"thz1": [(47, 26), (48, 26), (69, 26), (70, 26)],
               "thz2": [(106, 8), (13, 22), (64, 26), (41, 27), (51, 27)]}
SPIKE_BLOCKS = (0x3C, 0x3D)


class TerrainLab:
    """Runs the original terrain pass $690B (floor $691A, sides $715E, ceiling $73C9, ring probe, merge) for one explicit player state."""

    def __init__(self, rom: bytes, act: str = "thz1"):
        si = _load("spring_interaction")
        self.lab = si.Lab(rom, act)
        self.o, self.m = self.lab.o, self.lab.m
        self.o.cpu.set_breakpoint(HURT_ENTRY)

    def run_terrain(self, x, y, vx=0, vy=0, floor=False, prev=0, cur=5, req=5, f3=None, invulnerable=False, plane=0):
        lab, o, m = self.lab, self.o, self.m
        lab.player(x, y, vx=vx, vy=vy, floor=floor, prev=prev, cur=cur, req=req, f3=(0 if floor else 1) if f3 is None else f3)
        if invulnerable:
            m[0xD503] |= 0x80
        m[0xD3B0] = 0
        m[0xD525] = plane
        o.cpu.ix = 0xD500
        o.cpu.pc = 0x690B
        o.cpu.sp = 0xDFE0
        o.word(o.cpu.sp, o.RETURN)
        hit = False
        for _ in range(60):
            o.cpu.ticks_to_stop = 100000
            o.cpu.run()
            if o.cpu.pc == HURT_ENTRY:
                hit = True
                o.cpu.pc = o.RETURN           # the hurt routine itself is audited separately
                break
            if o.cpu.pc == o.RETURN:
                break
        else:
            raise RuntimeError("terrain pass did not return")
        return {"hit": hit, "x": o.word(0xD511), "y": o.word(0xD514), "floor": bool(m[0xD522] & 2), "ceiling": bool(m[0xD522] & 1),
                "d523": m[0xD523], "tile": m[0xD353], "flags": m[0xD364]}


def terrain_probe_geometry(rom: bytes) -> dict:
    """Probe offsets, read from the code/RAM initializer, plus the floor-handler byte facts."""
    tl = TerrainLab(rom)
    m = tl.m
    sample = {}
    for name, (dx, dy) in {"floor": (0, 0), "right_side": (s16(tl.o.word(0xD49C)), s16(tl.o.word(0xD49E))),
                           "left_side": (s16(tl.o.word(0xD498)), s16(tl.o.word(0xD49A))), "ceiling": (0, -24)}.items():
        sample[name] = {"offset_passed": [dx, dy], "effective_probe_relative_to_anchor": [dx, dy + 18]}
    return {"evidence": "BYTE-VERIFIED ASSEMBLY ($3686, $691A, $715E, $73C9, lookup adds +18 to Y at $7666) + CONTROLLED ROUTINE RESULT", "probes": sample,
            "note": "the anchor is player Y; the lookup adds 18 to the supplied Y offset, so the foot probe is (X, Y+18), the side probes (X-9, Y+6)/(X+9, Y+6), the ceiling probe (X, Y-6)"}


def spike_block_inventory(rom: bytes) -> dict:
    blocks = {}
    for b in SPIKE_BLOCKS:
        hd = block_header(rom, b)
        blocks[h(b, 2)] = {"header_rom_offset": h(hd["address"], 5), "flags": h(hd["flags"], 2), "terrain_type_low5": hd["flags"] & 0x1F,
                           "solid_bit7": bool(hd["flags"] & 0x80), "one_way_bit6": bool(hd["flags"] & 0x40), "alt_plane_bit5": bool(hd["flags"] & 0x20),
                           "modifier": hd["modifier"], "vertical_profile_by_x_runs": runs32(hd["vertical"]), "horizontal_profile_by_y_runs": runs32(hd["horizontal"]),
                           "vertical_profile_value": hd["vertical"][0], "meaning": "foot-probe surface at block row 16 (height 16 from the block bottom)"}
    cells = {}
    for act, lst in SPIKE_CELLS.items():
        rows = layout_rows(act)
        cells[act] = [{"cell": [cx, cy], "world_x": cx * 32, "world_y": cy * 32, "block": h(rows[cy][cx], 2),
                       "left": h(rows[cy][cx - 1], 2), "right": h(rows[cy][cx + 1], 2), "above": h(rows[cy - 1][cx], 2), "below": h(rows[cy + 1][cx], 2)} for cx, cy in lst]
    census = {}
    for act in ACTS:
        census[act] = {h(b, 2): sum(r.count(b) for r in layout_rows(act)) for b in (0x3C, 0x3D, 0x3E, 0x3F, 0xF4, 0xF5)}
    handler = rom[FLOOR_HANDLER_TABLE + 5 * 2] | rom[FLOOR_HANDLER_TABLE + 5 * 2 + 1] << 8
    return {"evidence": "DECODED DATA + BYTE-VERIFIED ASSEMBLY", "blocks": blocks, "cells": cells, "layout_census_of_damaging_tile_ids": census,
            "floor_handler_for_type_5": h(handler),
            "other_threshold_tiles": {"0x3E/0x3F": "ceiling damage tail $74E7..$752C", "0xF4": "right side damage tail via $7349", "0xF5": "left side damage tail via $7349",
                                      "0xF2/0xF3": "type-5 side tiles that skip the requested-state gates"}}


# --------------------------------------------------------------------------- #
# 5. platform controlled sweeps
# --------------------------------------------------------------------------- #
VY_GRID = (-0x400, -0x101, -0x100, -0xFF, -1, 0, 1, 0xFF, 0x100, 0x101, 0x400, 0x700)


def _support_cases(lab: ObjectLab, state: int, vys=VY_GRID, rng=(-30, 30, -30, 30)) -> dict:
    """Every (dx, dy, player vy) cell: real callback vs model (platform Y read back at the moment the contact is tested)."""
    m = lab.m
    pv_after_move = s16(lab.obj16(0x18))            # the lab object already holds its script velocity
    n = mis = 0
    support = {}
    first_mis = []
    for vy in vys:
        for dy in range(rng[2], rng[3] + 1):
            for dx in range(rng[0], rng[1] + 1):
                lab.reset()
                x0, y0 = lab.obj16(0x11), lab.obj16(0x14)
                lab.player(x0 + dx, y0 + dy, vy=vy)
                lab.callback()
                got = m[0xD3C0] == PLATFORM_SOLID_ID
                # contact is tested after the move for movers (state 11) and before the sag for state 5
                y_test = lab.obj16(0x14) if state == 11 else y0
                exp = model_support(dx, (y0 + dy) - y_test, pv_after_move, vy)
                n += 1
                if got != exp:
                    mis += 1
                    if len(first_mis) < 5:
                        first_mis.append([dx, dy, vy])
                if got and vy == 0x100:
                    support.setdefault(dy, []).append(dx)
    region = {str(dy): [min(v), max(v)] for dy, v in sorted(support.items())}
    return {"cases": n, "mismatches": mis, "first_mismatches": first_mis, "support_region_dx_range_by_dy_at_vy_plus_1_0": region,
            "dy_extremes": [min(support), max(support)] if support else None}


def platform_support(rom: bytes) -> dict:
    out = {"evidence": "CONTROLLED ROUTINE RESULT (real callbacks $879A / $86DA)"}
    for state, param, aux in ((5, 0x84, 0), (11, 0x0A, 9)):
        lab = platform_lab(rom, param, aux)
        out[f"state_{state}"] = _support_cases(lab, state)
        out[f"state_{state}"]["fixture"] = {"parameter": h(param, 2), "aux1": h(aux, 2), "platform_extents": [lab.m[SLOT + 0x2C], lab.m[SLOT + 0x2D]],
                                           "platform_speed_8_8": s16(lab.obj16(0x18)), "object_id": lab.m[SLOT + 0x32], "plat_flags_03": h(lab.m[SLOT + 3], 2)}
    return out


def platform_gate(rom: bytes) -> dict:
    """$8866: platform Y speed P against player Y speed p over a full signed grid; the model is `P > p`."""
    lab = platform_lab(rom, 0x0A, 9)
    m, o = lab.m, lab.o
    n = mis = 0
    thresholds = {}
    vals = sorted({v for b in (0x100, 0x80, 0x7F, 1) for v in (-b, b)} | {0, 0x700, -0x700, 0x7FFF, -0x8000, 0x4000, -0x4000})
    for P in vals:
        for p in vals + [P - 1, P + 1, P]:
            p = s16(p)
            lab.reset()
            lab.player(lab.obj16(0x11), lab.obj16(0x14) - 14 - (1 if P else 0), vy=p)
            o.word(SLOT + 0x18, P)
            o.cpu.ix = SLOT
            lab.o.bank(2, BANK_PLATFORM)
            m[0xD12B] = BANK_PLATFORM
            o.call(0x8866)
            got = o.cpu.a
            exp = model_gate_8866(P, p)
            n += 1
            if got != exp:
                mis += 1
    for P in (-0x100, 0, 0x100):
        lo = None
        for p in range(-0x400, 0x401):
            lab.reset()
            o.word(SLOT + 0x18, P)
            o.word(0xD518, p & 0xFFFF)
            o.cpu.ix = SLOT
            o.bank(2, BANK_PLATFORM)
            m[0xD12B] = BANK_PLATFORM
            o.call(0x8866)
            n += 1
            if o.cpu.a == 0 and lo is None:
                lo = p
            if (o.cpu.a == 0) != (not (P > p)):
                mis += 1
        thresholds[str(P)] = {"gate_passes_from_player_vy": lo}
    return {"evidence": "CONTROLLED ROUTINE RESULT ($8866 executed)", "cases": n, "mismatches": mis, "rule": "returns $FF (no support this update) iff platform Y speed > player Y speed, both signed 8.8",
            "pass_threshold_by_platform_speed": thresholds}


def platform_gates_matrix(rom: bytes) -> dict:
    """Owner, player bit-6 gate, platform inactivity, player extents and player state: the only inputs that change the support result."""
    rows = []
    for state, param, aux in ((5, 0x84, 0), (11, 0x0A, 9)):
        lab = platform_lab(rom, param, aux)
        m = lab.m

        def run(**kw):
            lab.reset()
            x0, y0 = lab.obj16(0x11), lab.obj16(0x14)
            f4 = kw.pop("f4", None)
            if f4 is not None:
                m[SLOT + 4] = f4
            f3obj = kw.pop("obj_f3", None)
            if f3obj is not None:
                m[SLOT + 3] = f3obj
            kw.setdefault("vy", 0x700)
            lab.player(x0, y0 - 8, **kw)
            lab.callback()
            return m[0xD3C0]
        base = run()
        rows.append({"state": state, "baseline_supported": base == PLATFORM_SOLID_ID,
                     "owner_none": run(d3c0=0) == PLATFORM_SOLID_ID, "owner_self": run(d3c0=PLATFORM_SOLID_ID) == PLATFORM_SOLID_ID,
                     "owner_other_slot_keeps_d3c0": run(d3c0=5) == 5,
                     "player_d503_bit6_set": run(f3=0x40) == PLATFORM_SOLID_ID, "player_d503_bit1_attack": run(f3=0x02) == PLATFORM_SOLID_ID,
                     "player_d503_bit0_airborne": run(f3=0x01) == PLATFORM_SOLID_ID,
                     "player_extents_9_24_state_0f": run(ex=9) == PLATFORM_SOLID_ID,
                     "platform_f4_bit6_set_inactive": run(f4=0x40) == PLATFORM_SOLID_ID,
                     "platform_f3_bit6_set": run(obj_f3=0xC0) == PLATFORM_SOLID_ID, "platform_f3_bit7_clear": run(obj_f3=0x00, f3=0x40) == PLATFORM_SOLID_ID,
                     "player_current_state_irrelevant": len({run(cur=c, req=c) for c in range(0x34)}) == 1,
                     "player_floor_flag_irrelevant": len({run(f22=f) for f in (0, 2)}) == 1})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "rows": rows,
            "reading": "True = support claimed. owner_other_slot: D3C0 held by another object -> the platform releases nothing and claims nothing (D3C0 unchanged)."}


# --------------------------------------------------------------------------- #
# 6. platform scenarios in the whole original game
# --------------------------------------------------------------------------- #
def _prec(e: Emu, q: int) -> dict:
    return {"plat_x": e.u16(q + 0x11), "plat_y": e.u16(q + 0x14), "plat_vy": s16(e.u16(q + 0x18)), "plat_sag": e.s.mem[q + 0x35]}


def _trace(e: Emu, frames: int, padfn=None, plat_type=0x28, plat_nth=0) -> list:
    rows = []
    for f in range(frames):
        e.s.pad = padfn(f) if padfn else 0
        e.s.run_frame()
        r = player_rec(e)
        q = e.slot_of(plat_type, plat_nth)
        if q is not None:
            r.update(_prec(e, q))
        r["f"] = f
        rows.append(r)
    return rows


def _compact(rows, keys=("f", "x", "y", "vx", "vy", "cur", "f3", "f23", "d3c0", "plat_y")) -> list:
    return [[r.get(k) for k in keys] for r in rows]


def _first(rows, pred):
    for r in rows:
        if pred(r):
            return r["f"]
    return None


def emulated_platform(rom: bytes) -> dict:
    e = Emu(rom, "thz1")
    out = {"evidence": "EMULATED ORIGINAL FRAME", "columns": ["frame", "x", "y", "vx", "vy", "cur_state", "d503", "d523", "d3c0", "platform_y"]}
    lift = (592, 464)
    sag = (1040, 384)

    # P1 landing on the rising lift
    e.restore(); e.place(lift[0], lift[1] - 20, 0, 0x100)
    rows = _trace(e, 14)
    claim = _first(rows, lambda r: r["d3c0"] == PLATFORM_SOLID_ID)
    out["land_on_rising_lift"] = {"rows": _compact(rows[:12]), "support_claim_update": claim, "player_y_minus_platform_y_after_claim": rows[claim]["y"] - rows[claim]["plat_y"] if claim is not None else None,
                                  "landed_update_f3_clear": _first(rows, lambda r: r["f3"] & 1 == 0), "vy_retained_while_standing": sorted({r["vy"] for r in rows[claim + 2:]}) if claim is not None else None}

    # P2 ride through the reversal (first lift reverses after 144 updates)
    e.restore(); e.place(lift[0], lift[1] - 20, 0, 0x100)
    rows = _trace(e, 160)
    out["ride_through_reversal"] = {"rows": _compact(rows[140:152]), "support_continuous": all(r["d3c0"] == PLATFORM_SOLID_ID for r in rows[8:]),
                                    "offsets_player_minus_platform": sorted({r["y"] - r["plat_y"] for r in rows[8:]}), "player_vy_constant": sorted({r["vy"] for r in rows[8:]})}

    # P3 landing on the DESCENDING lift with different retained vertical speeds
    p3 = []
    for vy in (0x000, 0x0FF, 0x100, 0x180, 0x400, 0x700):
        e.restore(); e.place(lift[0], lift[1] - 20, 0, 0x100)
        e.run(150)
        q = e.slot_of(0x28)
        e.place(lift[0], e.u16(q + 0x14) - 28, 0, vy)
        rows = _trace(e, 40)
        claim = _first(rows, lambda r: r["d3c0"] == PLATFORM_SOLID_ID)
        p3.append({"start_vy": vy, "support_claim_update": claim, "vy_at_claim": rows[claim]["vy"] if claim is not None else None,
                   "still_supported_at_update_39": rows[-1]["d3c0"] == PLATFORM_SOLID_ID})
    out["land_on_descending_lift_by_player_vy"] = p3

    # P3b supported player whose retained vy is below the lift's descending speed loses support at the reversal
    e.restore(); e.place(lift[0], lift[1] - 20, 0, 0x100)
    e.run(20)
    e.s.w16(0xD518, 0x0000)             # force the retained vy to 0 while standing (as after landing with vy 0)
    rows = _trace(e, 140)
    lost = _first(rows, lambda r: r["d3c0"] == 0)
    out["supported_with_retained_vy_zero"] = {"support_lost_update": lost, "platform_vy_at_loss": rows[lost]["plat_vy"] if lost is not None else None,
                                              "rows_around_loss": _compact(rows[lost - 2:lost + 8]) if lost is not None else None}

    # P4 step off the edge of the sag platform
    for name, pad in (("right", PAD["RIGHT"]), ("left", PAD["LEFT"])):
        e.restore(); e.place(sag[0], sag[1] - 30, 0, 0x100)
        e.run(30)
        base = e.snapshot()
        rows = _trace(e, 60, lambda f, pad=pad: pad)
        lost = _first(rows, lambda r: r["d3c0"] == 0)
        out[f"step_off_{name}"] = {"support_lost_update": lost, "dx_at_last_supported": (rows[lost - 1]["x"] - sag[0]) if lost else None,
                                   "dx_when_released": (rows[lost]["x"] - sag[0]) if lost is not None else None,
                                   "rows_around_release": _compact(rows[lost - 2:lost + 8]) if lost is not None else None}

    # P5 jump off the platform
    e.restore(); e.place(sag[0], sag[1] - 30, 0, 0x100)
    e.run(30)
    rows = _trace(e, 30, lambda f: PAD["B1"] if f == 2 else 0)
    out["jump_off_sag"] = {"rows": _compact(rows[:12]), "support_lost_update": _first(rows[3:], lambda r: r["d3c0"] == 0)}

    # P6 jump up through the platform from below, P7 run through it from the side
    e.restore(); e.place(sag[0], sag[1] + 40, 0, -0x680, cur=0x0A, f3=3)
    rows = _trace(e, 30)
    out["rising_through_from_below"] = {"rows": _compact(rows[:26:2]), "support_ever_claimed": any(r["d3c0"] for r in rows), "vy_first_update": rows[0]["vy"]}
    e.restore(); e.place(sag[0], sag[1] + 40, 0, -0x680, cur=0x0B, f3=1)
    rows = _trace(e, 30)
    out["rising_through_from_below_not_attacking"] = {"rows": _compact(rows[:26:2]), "support_ever_claimed": any(r["d3c0"] for r in rows), "d523_bit0_seen": any(r["f23"] & 1 for r in rows)}
    e.restore(); e.place(sag[0] - 70, sag[1] + 8, 0x400, 0, cur=0x0A, f3=3)
    rows = _trace(e, 30)
    out["through_from_the_side_at_platform_height"] = {"rows": _compact(rows[:24:2]), "support_ever_claimed": any(r["d3c0"] for r in rows),
                                                       "x_progress_per_update": sorted({rows[i + 1]["x"] - rows[i]["x"] for i in range(10)})}

    # P8 sag: stand 20 updates, step off, platform recovers
    e.restore(); e.place(sag[0], sag[1] - 30, 0, 0x100)
    rows = _trace(e, 24)
    out["sag_while_standing"] = {"platform_y_offset_by_update": [r["plat_y"] - sag[1] for r in rows[1:]], "sag_counter": [r["plat_sag"] for r in rows[1:]]}
    return out


def _rects(cells) -> list:
    """Set of (x, y) -> list of [x0, x1, y0, y1] rectangles (rows merged first, then identical column ranges)."""
    byy = {}
    for x, y in cells:
        byy.setdefault(y, []).append(x)
    rows = {y: tuple(map(tuple, ranges(xs))) for y, xs in byy.items()}
    out, ys = [], sorted(rows)
    i = 0
    while i < len(ys):
        j = i
        while j + 1 < len(ys) and ys[j + 1] == ys[j] + 1 and rows[ys[j + 1]] == rows[ys[i]]:
            j += 1
        for a, b in rows[ys[i]]:
            out.append([a, b, ys[i], ys[j]])
        i = j + 1
    return out


def terrain_foot_sweep(rom: bytes) -> dict:
    """Foot-probe sweep over the whole THZ1 spike pair (x 1504..1567) and every foot row: previous surface x floor flag x Y speed class."""
    tl = TerrainLab(rom, "thz1")
    cx0, cy0 = 1504, 832
    vys = {"rising_-1.0": -0x100, "zero": 0, "descending_+1.0": 0x100, "fast_+7.0": 0x700}
    prevs = {"none_00": 0x00, "solid_81": 0x81, "spike_85": 0x85}
    out, n = {}, 0
    for pn, prev in prevs.items():
        for floor in (False, True):
            for vn, vy in vys.items():
                cells = set()
                for x in range(cx0 - 12, cx0 + 64 + 12):
                    for foot in range(cy0 - 8, cy0 + 40):
                        r = tl.run_terrain(x, foot - 18, vy=vy, floor=floor, prev=prev)
                        n += 1
                        if r["hit"]:
                            cells.add((x, foot))
                out[f"prev_{pn}|floor_{int(floor)}|vy_{vn}"] = {"damaging_cells_[x0,x1,foot_row_y0,y1]": _rects(cells), "count": len(cells)}
    return {"evidence": "CONTROLLED ROUTINE RESULT ($690B executed on the real THZ1 layout; hurt entry $48F7 watched)", "cases": n,
            "block_pair_world": [cx0, cy0, cx0 + 63, cy0 + 31], "coordinates": "x = anchor X (= foot probe X); foot row = anchor Y + 18", "results": out}


def terrain_side_ceiling_sweep(rom: bytes) -> dict:
    """Side and ceiling probes over the spike pair: pushes, damage, and the requested-state gate."""
    tl = TerrainLab(rom, "thz1")
    cx0, cy0 = 1504, 832
    n = dmg_side = dmg_ceil = 0
    right, left, ceil = set(), set(), set()
    for y in range(cy0 - 30, cy0 + 40):               # anchor Y; side probe row = Y + 6
        for x in range(cx0 - 20, cx0 + 12):           # only the right probe (X + 9) can be inside the pair
            r = tl.run_terrain(x, y, vx=0x200, floor=False, prev=0x00, cur=0x0A, req=0x0A, f3=3)
            n += 1
            dmg_side += r["hit"]
            if r["x"] != x:
                right.add((x, y + 6))
        for x in range(cx0 + 64 - 12, cx0 + 64 + 20):  # only the left probe (X - 9) can be inside the pair
            l = tl.run_terrain(x, y, vx=-0x200, floor=False, prev=0x00, cur=0x0A, req=0x0A, f3=3)
            n += 1
            dmg_side += l["hit"]
            if l["x"] != x:
                left.add((x, y + 6))
        for x in range(cx0 - 20, cx0 + 64 + 20):
            c = tl.run_terrain(x, y, vy=-0x300, floor=False, prev=0x81, cur=0x0A, req=0x0A, f3=3)
            n += 1
            dmg_ceil += c["hit"]
            if c["y"] != y:
                ceil.add((x, y - 6))
    gates = []
    for req in range(0x34):
        r = tl.run_terrain(1500, 842, vx=0x200, floor=False, prev=0x00, cur=req, req=req, f3=3)
        l = tl.run_terrain(1572, 842, vx=-0x200, floor=False, prev=0x00, cur=req, req=req, f3=3)
        gates.append({"requested_state": h(req, 2), "right_probe_pushed": r["x"] != 1500, "left_probe_pushed": l["x"] != 1572, "damage": r["hit"] or l["hit"]})
        n += 2
    anomalies = [g["requested_state"] for g in gates if not (g["right_probe_pushed"] and g["left_probe_pushed"])]
    return {"evidence": "CONTROLLED ROUTINE RESULT", "cases": n, "side_probe_damage_cases": dmg_side, "ceiling_probe_damage_cases": dmg_ceil,
            "right_probe_changes_x_[x0,x1,probe_row_y0,y1]": _rects(right), "left_probe_changes_x_[x0,x1,probe_row_y0,y1]": _rects(left),
            "ceiling_probe_changes_y_cells": len(ceil),
            "requested_state_gate": {"states_without_side_push": anomalies, "note": "state $1E (hurt) returns without pushing; state $17 takes the breakable branch ($72B6/$72DD) whose push/break depends on attack posture and |X speed|"},
            "reading": "side pushes exist only for probe rows 16..31 of the spike cell (and the ground block below); rows 0..15 never push; no side or ceiling probe damages a type-5 tile other than $F4/$F5/$3E/$3F, which no THZ layout contains"}


# --------------------------------------------------------------------------- #
# 7. diagonal / high-speed approach to the static spike pair (whole original game)
# --------------------------------------------------------------------------- #
PAIR_L, PAIR_R, PAIR_GROUND_Y = 1504, 1567, 846       # THZ1 cells (47,26)+(48,26); standing anchor Y on the ground row below
PAIR_SPIKE_TOP = 832                                   # world Y of the spike cells (block rows 0..31 = 832..863)


def _spike_run(e: Emu, hurt: list, x0, y0, vx, vy, cur, f3, floor=False, pad=0, frames=48):
    e.restore()
    hurt.clear()
    TERRAIN_HURT.clear()
    e.place(x0, y0, vx, vy, cur=cur, f3=f3, floor=floor)
    path = []
    for f in range(frames):
        e.s.pad = pad
        e.s.run_frame()
        path.append((e.u16(0xD511), e.u16(0xD514), e.s.mem[0xD503] & 1, e.s.mem[0xD501], s16(e.u16(0xD518))))
        if hurt or path[-1][0] < 1420 or path[-1][0] > 1650:
            break
        if f >= 3 and path[-1][2] == 0 and e.s.mem[0xD522] & 2 and abs(s16(e.u16(0xD516))) < 0x100 and f >= 8:
            break
    return path


TERRAIN_HURT: list = []


def _rising_solid_frames(path) -> int:
    """Updates on which the foot probe is inside the solid spike rows while the player's Y speed is negative (hazard and projection skipped)."""
    return sum(1 for x, y, _, _, vy in path if PAIR_L <= x <= PAIR_R and PAIR_SPIKE_TOP + 16 <= y + 18 <= PAIR_SPIKE_TOP + 31 and vy < 0)


def _spike_class(x0, path, hurt) -> str:
    """A damaged by the terrain handler; X hurt by another hazard; E foot in the solid spike rows (rows 16..31 of the cells) and NOT damaged (a phase-through candidate);
    B stopped by the side wall (a side probe in the solid rows, foot never); C crossed the pair without touching it; D no contact (left the window)."""
    if TERRAIN_HURT:
        return "A_damaged"
    if hurt:
        return "X_other_hazard_in_range"
    foot_vy, side_solid = [], False
    for x, y, _, _, vy in path:
        in_cols = lambda px: PAIR_L <= px <= PAIR_R
        if in_cols(x) and PAIR_SPIKE_TOP + 16 <= y + 18 <= PAIR_SPIKE_TOP + 31:
            foot_vy.append(vy)
        side_solid |= (in_cols(x + 9) or in_cols(x - 9)) and PAIR_SPIKE_TOP + 16 <= y + 6 <= PAIR_SPIKE_TOP + 31
    if foot_vy:
        return "E1_foot_in_solid_rows_only_while_rising" if all(v < 0 for v in foot_vy) else "E2_foot_in_solid_rows_not_rising_undamaged"
    if side_solid:
        return "B_stopped_by_wall"
    x = path[-1][0]
    if (x0 < PAIR_L and x > PAIR_R) or (x0 > PAIR_R and x < PAIR_L):
        return "C_crossed_without_contact"
    return "D_no_contact"


def emulated_spike_sweep(rom: bytes) -> dict:
    e = Emu(rom, "thz1")
    hurt = []
    e.s.add_pc_hook(HURT_ENTRY, lambda m: hurt.append((e.s.frame, e.u16(0xD511), e.u16(0xD514))))
    e.s.add_pc_hook(0x6AE0, lambda m: TERRAIN_HURT.append(e.s.frame))      # the type-5 floor handler's jump into the hurt routine
    counts, examples, first_hurt = {}, {}, {}
    total = 0
    rising = {"runs_with_rising_solid_row_updates": 0, "updates": 0, "final_class_of_those_runs": {}, "examples": []}
    starts_left, starts_right, starts_above = (1448, 1472, 1488), (1584, 1600, 1624), (1504, 1519, 1534, 1549, 1564)
    for label, xs in (("from_left", starts_left), ("from_right", starts_right), ("from_above", starts_above)):
        for state_name, cur, f3 in (("jump", 0x0A, 3), ("fall", 0x0E, 1)):
            for y0 in (790, 815, 835):
                for vxn in (-6, -4, -2, 0, 2, 4, 6):
                    for vyn in (-2, 0, 3):
                        for x0 in xs:
                            path = _spike_run(e, hurt, x0, y0, vxn * 256, vyn * 256, cur, f3)
                            cl = _spike_class(x0, path, hurt)
                            total += 1
                            rs = _rising_solid_frames(path)
                            if rs:
                                rising["runs_with_rising_solid_row_updates"] += 1
                                rising["updates"] += rs
                                rising["final_class_of_those_runs"][cl] = rising["final_class_of_those_runs"].get(cl, 0) + 1
                                if len(rising["examples"]) < 4:
                                    rising["examples"].append({"start": [x0, y0], "vx": vxn, "vy": vyn, "state": state_name, "rising_solid_updates": rs, "final_class": cl})
                            key = f"{label}|{state_name}|{cl}"
                            counts[key] = counts.get(key, 0) + 1
                            if cl[0] in "EX" and len(examples.setdefault(cl, [])) < 6:
                                examples[cl].append({"start": [x0, y0], "vx": vxn, "vy": vyn, "state": state_name, "end": list(path[-1][:2]), "frames": len(path)})
                            if cl[0] == "A":
                                first_hurt.setdefault(label, []).append(hurt[0][2] + 18)      # foot row at the hurt entry
    # grounded approaches along the ground row: walk, run, roll
    for label, x0s, pad, sgn in (("ground_from_left", (1440, 1470, 1490), PAD["RIGHT"], 1), ("ground_from_right", (1590, 1620), PAD["LEFT"], -1)):
        for sname, cur, f3 in (("walk", 5, 0), ("run", 6, 0), ("roll", 9, 2)):
            for vxn in (1, 3, 5, 7):
                for x0 in x0s:
                    path = _spike_run(e, hurt, x0, PAIR_GROUND_Y, sgn * vxn * 256, 0x700, cur, f3, floor=True, pad=pad, frames=36)
                    cl = _spike_class(x0, path, hurt)
                    total += 1
                    key = f"{label}|{sname}|{cl}"
                    counts[key] = counts.get(key, 0) + 1
                    if cl[0] in "EX" and len(examples.setdefault(cl, [])) < 6:
                        examples[cl].append({"start": [x0, PAIR_GROUND_Y], "vx": sgn * vxn, "state": sname, "end": list(path[-1][:2])})
    return {"evidence": "EMULATED ORIGINAL FRAME (THZ1 booted; Sonic and the camera teleported; 0 rings so a hit ends in state $1F; hurt entry $48F7 watched by PC hook)",
            "runs": total, "classes": {"A": "damaged by the terrain handler", "B": "stopped by the side wall (side probe in the solid rows), undamaged", "C": "crossed the pair without any solid-row probe contact", "D": "no contact (left the window / never reached the pair)", "E1": "foot probe in the solid spike rows, undamaged, but ONLY on updates where Y speed < 0 (the projection and the hazard are skipped while rising)", "E2": "foot probe in the solid rows while level/descending and undamaged (would be a phase-through; expected 0)", "X": "hurt by another hazard in range (the $1B spike at (1344,864))"},
            "counts": dict(sorted(counts.items())), "examples_of_E_X": examples, "rising_through_solid_rows": rising,
            "foot_row_at_hurt_distinct": sorted({r for v in first_hurt.values() for r in v})}


# --------------------------------------------------------------------------- #
# 8. moving spikes (type $1B)
# --------------------------------------------------------------------------- #
def spike_record(world_x: int, world_y: int) -> bytes:
    sx, sy = world_x + 256, world_y + 256
    return bytes([0x1B, sx & 0xFF, sx >> 8, sy & 0xFF, sy >> 8, 0, 0, 0, 0])


def spike_lab(rom: bytes, world=(1344, 864), flags4=0x00) -> ObjectLab:
    return ObjectLab(rom, 0x1B, spike_record(*world), BANK_SPIKE, flags4)


def spike_placements() -> dict:
    return {act: [{"record_index": r["index"], "rom_offset": r["rom_offset"], "raw_bytes": r["raw_bytes"], "world_x": r["world_x"], "world_y": r["world_y"],
                   "flags": r["flags"], "parameter": r["parameter"], "aux1": r["aux1"]} for r in records(act, 0x1B)] for act in ACTS}


def spike_set_state(lab: ObjectLab, state: int, y: int) -> None:
    """Put the fixture object into one script state at a given Y (engine loads the script/callback), active (+$04 bit 6 clear)."""
    m, o = lab.m, lab.o
    m[SLOT + 2] = state
    o.word(SLOT + 0x14, y)
    m[SLOT + 0x1F] = 0
    lab.engine()
    m[SLOT + 4] = 0
    lab.snap = bytes(m[0xC000:0xE000])


def spike_timeline(rom: bytes) -> dict:
    """One real placement run through the original engine + callbacks; the steady-state cycle is read from the second cycle."""
    lab = spike_lab(rom)
    m = lab.m
    m[SLOT + 4] &= ~0x40
    log = []
    for _ in range(420):
        cb = lab.frame()
        log.append((m[SLOT + 1], lab.obj16(0x14), cb))
    base_y = lab.obj16(0x3C)
    seq = [(s, y) for s, y, _ in log]
    start = next(i for i in range(40, 120) if seq[i][0] == 4 and seq[i - 1][0] == 3)
    period = next(p for p in range(50, 150) if seq[start:start + p] == seq[start + p:start + 2 * p])
    cycle = seq[start:start + period]
    runs = []
    for s, y in cycle:
        if runs and runs[-1][0] == s:
            runs[-1][1] += 1
            runs[-1][3] = y
        else:
            runs.append([s, 1, y, y])
    callbacks = {h(c): sum(1 for _, _, cc in log if cc == c) for c in sorted({c for _, _, c in log})}
    return {"evidence": "CONTROLLED ROUTINE RESULT (engine $64FA + callbacks on a real THZ1 record)", "base_y": base_y, "rise_pixels": 18, "rise_step_pixels": 6,
            "cycle_updates": period, "cycle_runs_[state,updates,y_first,y_last]": runs,
            "states": {"1": "rising: contact test first, then Y -= 6", "2": "raised hold: contact test only", "3": "retract: Y += 6, no test", "4": "hidden hold: no test"},
            "callbacks_seen": callbacks, "contact_tested_in_states": [1, 2]}


def model_spike_outcome(dx, dy, vy, floor, attack, cooldown=0, ex=8, ey=24, oex=16, oey=24) -> str:
    """$ACFD: 'none', 'damage' (request $D3B0, bounce vy $FC00, cooldown 16) or 'push' (state 1, vx 0, X = objX +23 / -23)."""
    if cooldown or vy < 0:
        return "none"
    c = model_contact(dx, dy, ex, ey, oex, oey)
    if c == 0:
        return "none"
    if c == 1:
        return "damage"
    return "push" if (floor and attack) else "none"


def spike_contact_sweep(rom: bytes) -> dict:
    out = {"evidence": "CONTROLLED ROUTINE RESULT (real callbacks $AC8B state 1, $ACC3 state 2; Sonic extents 8,24)"}
    n = mis = 0
    boundaries = {}
    for state, y0 in ((2, 846), (1, 864)):
        lab = spike_lab(rom)
        spike_set_state(lab, state, y0)
        m, o = lab.m, lab.o
        ox, oy = lab.obj16(0x11), lab.obj16(0x14)
        damage = {}
        for name, floor, attack in (("walker_grounded", True, False), ("roller_grounded", True, True), ("airborne", False, False), ("airborne_attack", False, True)):
            for vy in (-0x100, 0, 0x100):
                for dy in range(-30, 31):
                    for dx in range(-30, 31):
                        lab.reset()
                        lab.player(ox + dx, oy + dy, vy=vy, f3=(0 if floor else 1) | (2 if attack else 0), f22=2 if floor else 0)
                        lab.callback()
                        pushed = m[0xD502] == 1 and o.word(0xD511) != ox + dx
                        got = "damage" if m[0xD3B0] == 0xFF else ("push" if pushed else "none")
                        exp = model_spike_outcome(dx, dy, vy, floor, attack)
                        if exp == "push" and not pushed:
                            exp = "push-to-same-x"            # player already at the push X: requested state 1 only
                            if m[0xD502] == 1:
                                exp = got
                        n += 1
                        if got != exp:
                            mis += 1
                            if mis < 6:
                                out.setdefault("first_mismatches", []).append([state, name, vy, dx, dy, got, exp])
                        if got == "damage" and vy == 0x100 and name == "walker_grounded":
                            damage.setdefault(dy, []).append(dx)
        boundaries[str(state)] = {str(dy): [min(v), max(v)] for dy, v in sorted(damage.items())}
    out.update({"cases": n, "mismatches": mis, "damage_region_dx_range_by_dy_relative_to_object_anchor": boundaries,
                "rule": "damage request only when the contact bit is 'player above' (dy in -24..-1 and |dx| <= |dy|, |dx| <= 24), player Y speed >= 0 and cooldown 0; side/below contact never damages; "
                        "side/below contact pushes only a grounded player in attack posture (D503 bit 1) to X = objX +23 (right) / -23 (otherwise), requested state 1, X speed 0"})
    return out


def spike_helper_gates(rom: bytes) -> dict:
    """Cooldown, inactivity and object-state gates of the real callbacks."""
    lab = spike_lab(rom)
    spike_set_state(lab, 2, 846)
    m, o = lab.m, lab.o
    ox, oy = lab.obj16(0x11), lab.obj16(0x14)

    def run(**kw):
        lab.reset()
        m[SLOT + 0x1F] = kw.pop("cooldown", 0)
        f4 = kw.pop("f4", None)
        if f4 is not None:
            m[SLOT + 4] = f4
        lab.player(ox, oy - 12, vy=kw.pop("vy", 0x100), **kw)
        lab.callback()
        return {"damage_request": m[0xD3B0] == 0xFF, "player_vy_after": s16(o.word(0xD518)), "cooldown_after": m[SLOT + 0x1F]}
    gates = {"baseline": run(), "cooldown_16": run(cooldown=16), "cooldown_1": run(cooldown=1), "object_inactive_f4_bit6": run(f4=0x40), "player_rising_vy_-1": run(vy=-1),
             "player_vy_0": run(vy=0), "player_invulnerable_d503_bit7": run(f3=0x80), "player_d503_bit6": run(f3=0x40)}
    states = {}
    for st, y0 in ((1, 864), (2, 846), (3, 852), (4, 864)):
        l2 = spike_lab(rom)
        spike_set_state(l2, st, y0)
        l2.reset()
        l2.player(l2.obj16(0x11), y0 - 12, vy=0x100)
        l2.callback()
        states[str(st)] = {"damage_request": l2.m[0xD3B0] == 0xFF, "callback": h(l2.m[SLOT + 0xC] | l2.m[SLOT + 0xD] << 8)}
    return {"evidence": "CONTROLLED ROUTINE RESULT", "gates": gates, "by_object_state": states}


def spike_move_before_contact(rom: bytes) -> dict:
    """State 1 tests the contact at the pre-move Y: damage rows are relative to the Y the object had when the callback began."""
    lab = spike_lab(rom)
    spike_set_state(lab, 1, 864)
    m = lab.m
    ox = lab.obj16(0x11)
    hits = []
    y_after = None
    for dy in range(-40, 10):
        lab.reset()
        lab.player(ox, 864 + dy, vy=0x100)
        lab.callback()
        y_after = lab.obj16(0x14)
        if m[0xD3B0] == 0xFF:
            hits.append(dy)
    return {"evidence": "CONTROLLED ROUTINE RESULT (state-1 callback from Y=864)", "player_y_minus_864_with_damage_request": ranges(hits), "object_y_after_callback": y_after,
            "reading": "rows -24..-1 are relative to the PRE-move anchor 864; the post-move anchor would be 858; the -6 move happens after the test"}


# --------------------------------------------------------------------------- #
# 9. damage gate and consequences (limited to what spike collision needs)
# --------------------------------------------------------------------------- #
def _call_with_stubs(lab, addr: int, stubs=(0x062D,), watch=()):
    """Run a routine on the player slot; sound/hardware stubs return at once; returns the first watched address reached (or None)."""
    o = lab.o
    for a in (*stubs, *watch):
        o.cpu.set_breakpoint(a)
    o.cpu.ix = 0xD500
    o.cpu.pc = addr
    o.cpu.sp = 0xDFE0
    o.word(o.cpu.sp, o.RETURN)
    reached = None
    for _ in range(200):
        o.cpu.ticks_to_stop = 100000
        o.cpu.run()
        pc = o.cpu.pc
        if pc == o.RETURN:
            break
        if pc in stubs:
            o.cpu.pc = o.word(o.cpu.sp)
            o.cpu.sp += 2
            continue
        if pc in watch:
            reached = pc
            break
        raise RuntimeError(f"unexpected stop at ${pc:04X}")
    for a in (*stubs, *watch):
        o.cpu.clear_breakpoint(a)
    return reached


def damage_gate_matrix(rom: bytes) -> dict:
    """$48BC: which combination of +$03 bits, power selector $D532, request $D3B0 and contact $D520 reaches the hurt entry."""
    si = _load("spring_interaction")
    lab = si.Lab(rom, "thz1")
    m = lab.m
    labels = {0x48F7: "hurt_48f7", 0x49F7: "invulnerability_tick_49f7", 0x4A2E: "bit6_ignore_4a2e", 0x49C3: "contact_with_attack_posture_49c3"}
    rows = []
    for f3 in (0x00, 0x02, 0x40, 0x80, 0xC0):
        for sel in (0, 3, 6):
            for req in (0, 0xFF):
                for contact in (0, 9):
                    lab.player(1000, 500, floor=True, cur=5, req=5, f3=f3)
                    m[0xD532], m[0xD3B0], m[0xD520], m[0xD3B1] = sel, req, contact, 5
                    m[0xD521] = 0
                    reached = _call_with_stubs(lab, 0x48BC, watch=tuple(labels))
                    rows.append({"d503_ie_plus3": h(f3, 2), "d532": sel, "request_d3b0": h(req, 2), "contact_d520": contact, "reaches": labels.get(reached, "return_without_hurt"),
                                 "d3b0_after": h(m[0xD3B0], 2), "d520_after": m[0xD520]})
    return {"evidence": "CONTROLLED ROUTINE RESULT ($48BC executed with the four exits watched)", "cases": len(rows), "rows": rows,
            "reading": "+$03 bit 7 (invulnerable) goes to the countdown $49F7 and ignores any request; bit 6 clears +$20 and returns; $D532 == 6 clears the request; a request or an ordinary contact "
                       "($D520 != 0, not attacking) reaches $48F7. Terrain spikes call $48F7 directly (not through $48BC) after testing +$03 bit 7 themselves."}


def hurt_consequences(rom: bytes) -> dict:
    si = _load("spring_interaction")
    lab = si.Lab(rom, "thz1")
    m, o = lab.m, lab.o

    def hurt(rings, f22=0x02, d523=0, cur=5, f3=0):
        lab.player(1000, 500, floor=bool(f22 & 2), cur=cur, req=cur, f3=f3)
        for i in range(19):
            m[0xD540 + i * 0x40:0xD540 + i * 0x40 + 0x40] = bytes(0x40)
        m[0xD522], m[0xD523], m[0xD29A], m[0xD3B1], m[0xD3A3], m[0xD297] = f22, d523, rings, 0, 0, 0
        _call_with_stubs(lab, HURT_ENTRY)
        s = lab.snap()
        scatter = sum(1 for i in range(19) if m[0xD540 + i * 0x40] == 6)
        return {"requested_state": h(s["req"], 2), "d503": h(s["f3"], 2), "vx": s16(s["vx"]), "vy": s16(s["vy"]), "invulnerability_timer_d3b1": m[0xD3B1], "rings_after": m[0xD29A],
                "scatter_objects_type_06": scatter, "floor_flag_after": bool(m[0xD522] & 2)}
    rows = {"rings_0_death": hurt(0)}
    for r in (1, 15, 16, 31, 32, 63, 64, 100, 255):
        rows[f"rings_{r}"] = hurt(r)
    rows["rings_5_left_wall_bit3_in_d523"] = hurt(5, d523=8)
    rows["rings_5_ceiling_contact_d522_bit0"] = hurt(5, f22=0x01)
    rows["rings_5_airborne"] = hurt(5, f22=0, f3=1)
    rows["rings_5_state_11"] = hurt(5, cur=0x11)
    return {"evidence": "CONTROLLED ROUTINE RESULT ($48F7 executed; sound routine stubbed)", "rows": rows,
            "rules": {"no_rings": "state $1F, Y speed -5.0 ($FB00), X speed unchanged, +$04 := 0, no invulnerability timer",
                      "rings": "state $1E, rings := 0, scatter objects (type $06), $D3B1 := $78 (120 updates), +$03 bits 7,6 and 0 set, floor flag cleared, Y speed -4.0 ($FC00) or +1.0 if +$22 bit 0 (ceiling contact), "
                               "X speed -1.0 ($FF00) or +1.0 if $D523 bit 3 (left wall)",
                      "direction": "knockback X direction depends only on wall flag $D523 bit 3, not on which side the hazard was",
                      "state_11": "current state $11 (numeric reward pose) takes a separate branch ($48F7 -> $4912): rings kept, sound $C3, then the same hurt entry"}}


def invulnerability_countdown(rom: bytes) -> dict:
    si = _load("spring_interaction")
    lab = si.Lab(rom, "thz1")
    m = lab.m
    lab.player(1000, 500, floor=True, cur=0x1E, req=0x1E, f3=0xC1)
    m[0xD3B1] = 0x78
    m[0xD3B0] = 0xFF
    seq = []
    for i in range(130):
        _call_with_stubs(lab, 0x48BC)
        seq.append((m[0xD3B1], m[0xD503] & 0xC0, m[0xD504] & 0x80, m[0xD3B0]))
        if not m[0xD503] & 0x80 and i > 0:
            break
    cleared_at = next(i for i, s in enumerate(seq) if s[1] == 0) + 1
    return {"evidence": "CONTROLLED ROUTINE RESULT ($48BC called repeatedly with +$03 bit 7 set, $D3B1 = $78)", "damage_gate_updates_until_bits_clear": cleared_at,
            "timer_trace_first_6": [s[0] for s in seq[:6]], "pending_request_d3b0_after_clear": seq[-1][3],
            "reading": "$49F7 decrements $D3B1 once per player update ($48BC); at zero +$03 bits 7/6 and +$04 bit 7 are cleared and the pending request $D3B0 is discarded; during the countdown any request is ignored and kept"}


# --------------------------------------------------------------------------- #
# 10. hazards in the whole original game: static spike, $1B spike, state exclusions, update order
# --------------------------------------------------------------------------- #
class Probe:
    """PC hooks that count/label the interesting routines for one emulated run."""
    LABELS = {0x5E9A: "object_callback_dispatch", 0x3FEF: "player_update_3fef", 0x402A: "x_integration", 0x4097: "y_integration", 0x690B: "terrain_pass",
              0x691A: "terrain_floor", 0x715E: "terrain_sides", 0x73C9: "terrain_ceiling", 0x753E: "terrain_ring_probe", 0x64CB: "merge_flags", 0x48BC: "damage_gate",
              0x6ACE: "floor_spike_handler", 0x6AE0: "floor_spike_hurt_jump", 0x48F7: "hurt_entry", 0x60FB: "object_move", 0x6328: "overlap_6328", 0x8814: "platform_support",
              0x88A0: "platform_carry", 0x8843: "platform_clear", 0xACFD: "spike_contact_helper"}

    def __init__(self, e: Emu, addrs=None):
        self.e = e
        self.events: list = []
        self.counts: dict = {}
        for a in (addrs or self.LABELS):
            e.s.add_pc_hook(a, lambda m, a=a: self._hit(a))

    def _hit(self, a):
        e = self.e
        name = self.LABELS[a]
        self.counts[name] = self.counts.get(name, 0) + 1
        if a == 0x5E9A:
            ix = e.s.cpu.ix
            who = "player" if ix == PLAYER else f"object_{e.s.mem[ix]:02X}"
            self.events.append((e.s.frame, f"{who}_callback_{e.s.cpu.hl:04X}"))
        else:
            self.events.append((e.s.frame, name))

    def reset(self):
        self.events.clear()
        self.counts.clear()


def _spike_emu(rom: bytes):
    e = Emu(rom, "thz1")
    return e, Probe(e)


def emulated_static_spike_aftermath(rom: bytes) -> dict:
    """Landing on the static pair with rings, then re-landing during the invulnerability window; and with no rings."""
    e, pr = _spike_emu(rom)
    out = {"evidence": "EMULATED ORIGINAL FRAME"}
    for name, rings in (("with_5_rings", 5), ("no_rings", 0)):
        e.restore()
        pr.reset()
        e.place(1560, 780, 0, 0x100, cur=0x0E, f3=1, rings=rings)
        rows = []
        for f in range(200):
            e.s.pad = 0
            e.s.run_frame()
            r = player_rec(e)
            r["f"] = f
            r["hurt_calls"] = pr.counts.get("hurt_entry", 0)
            r["floor_spike_hurt"] = pr.counts.get("floor_spike_hurt_jump", 0)
            r["plus3"] = e.s.mem[0xD503]
            rows.append(r)
        hit = next((r["f"] for r in rows if r["hurt_calls"]), None)
        out[name] = {"first_hurt_update": hit, "state_after_hit_by_update": [[r["f"], r["cur"], h(r["plus3"], 2), r["vx"], r["vy"], r["inv"]] for r in rows[hit - 1:hit + 8]] if hit is not None else None,
                     "hurt_entry_calls_in_200_updates": rows[-1]["hurt_calls"], "terrain_spike_hurt_calls_in_200_updates": rows[-1]["floor_spike_hurt"],
                     "invulnerability_timer_at_hit+1": rows[hit + 1]["inv"] if hit is not None and name == "with_5_rings" else None,
                     "updates_with_plus3_bit7": sum(1 for r in rows if r["plus3"] & 0x80), "state_sequence": _runs([r["cur"] for r in rows[hit:]]) if hit is not None else None,
                     "final": [rows[-1]["x"], rows[-1]["y"], rows[-1]["cur"]]}
    return out


def _runs(seq) -> list:
    out = []
    for v in seq:
        if out and out[-1][0] == v:
            out[-1][1] += 1
        else:
            out.append([v, 1])
    return out


def emulated_moving_spike_scenarios(rom: bytes) -> dict:
    e, pr = _spike_emu(rom)
    out = {"evidence": "EMULATED ORIGINAL FRAME (real THZ1 type-$1B placement (1344,864); 5 rings unless stated)"}

    def spike(q=None):
        return e.slot_of(0x1B)
    # fall onto the raised spike
    e.restore()
    pr.reset()
    e.place(1344, 790, 0, 0x100, cur=0x0E, f3=1, rings=5)
    rows = []
    for f in range(40):
        e.s.pad = 0
        e.s.run_frame()
        q = spike()
        r = player_rec(e)
        r.update({"f": f, "spike_state": e.s.mem[q + 1] if q else None, "spike_y": e.u16(q + 0x14) if q else None, "d3b0": e.s.mem[0xD3B0], "hurt": pr.counts.get("hurt_entry", 0), "plus3": e.s.mem[0xD503]})
        rows.append(r)
    first_req = next((r["f"] for r in rows if r["d3b0"] == 0xFF), None)
    first_hurt = next((r["f"] for r in rows if r["hurt"]), None)
    out["fall_onto_raised_spike"] = {"rows_[f,y,vy,cur,d3b0,spike_state,spike_y,hurt_calls]": [[r["f"], r["y"], r["vy"], r["cur"], r["d3b0"], r["spike_state"], r["spike_y"], r["hurt"]] for r in rows[max((first_req or 6) - 3, 0):(first_hurt or 20) + 4]],
                                    "damage_request_visible_after_update": first_req, "hurt_entry_update": first_hurt,
                                    "reading": "the object (after the player in the frame) writes the request and bounce; the player's NEXT update consumes it ($48BC at the end of its own pass)"}
    # same while invulnerable
    e.restore()
    pr.reset()
    e.place(1344, 790, 0, 0x100, cur=0x0E, f3=1, rings=5)
    e.s.mem[0xD503] |= 0xC0
    e.s.mem[0xD3B1] = 0x78
    rows = []
    for f in range(40):
        e.s.pad = 0
        e.s.run_frame()
        r = player_rec(e)
        r["hurt"] = pr.counts.get("hurt_entry", 0)
        rows.append(r)
    out["fall_onto_raised_spike_while_invulnerable"] = {"hurt_entry_calls": rows[-1]["hurt"], "vy_trace_first_20": [r["vy"] for r in rows[:20]],
                                                        "reading": "the object still bounces the player (Y speed -4.0) but the request is ignored while +$03 bit 7 is set"}
    # walk into the side of the raised spike (not attacking) and roll into it
    for name, cur, f3, pad_vx in (("walk_into_side", 5, 0, 3), ("roll_into_side", 9, 2, 4)):
        e.restore()
        pr.reset()
        e.place(1344 - 60, 846, pad_vx * 256, 0x700, cur=cur, f3=f3, floor=True, rings=5)
        rows = []
        for f in range(40):
            e.s.pad = PAD["RIGHT"]
            e.s.run_frame()
            q = spike()
            r = player_rec(e)
            r.update({"f": f, "spike_state": e.s.mem[q + 1] if q else None, "hurt": pr.counts.get("hurt_entry", 0)})
            rows.append(r)
        out[name] = {"rows_[f,x,y,vx,cur,spike_state]": [[r["f"], r["x"], r["y"], r["vx"], r["cur"], r["spike_state"]] for r in rows[6:34:3]], "hurt_entry_calls": rows[-1]["hurt"],
                     "x_at_end": rows[-1]["x"]}
    return out


STATE_LIST = [(0x01, "stand", 0, True), (0x05, "walk", 0, True), (0x06, "run", 0, True), (0x09, "roll", 2, True), (0x0A, "jump", 3, False), (0x0E, "fall", 1, False), (0x0B, "spring_0b", 1, False),
              (0x1C, "diag_spring_1c", 3, False), (0x0C, "loop_0c", 1, False), (0x0D, "loop_0d", 1, False), (0x13, "loop_13", 1, False), (0x22, "twist_22", 1, False),
              (0x1E, "hurt_1e", 1, False), (0x1F, "death_1f", 1, False), (0x20, "act_clear_20", 0, True)]


def emulated_state_matrix(rom: bytes) -> dict:
    """Each state is made CURRENT before the hazard update: +$01 = +$02 = state and the script pointer +$0E/$0F cleared, which makes the engine ($64FA, line $0651D)
    reload that state's script and callback at the start of the next update; Sonic is teleported into the hazard in the same step."""
    e, pr = _spike_emu(rom)
    s, mem = e.s, e.s.mem
    rows = []

    def enter(st, x, y, vx, vy, floor, f3, prev=None, fill=True):
        e.restore()
        e.place(x, y, vx, vy, cur=st, f3=f3, floor=floor, rings=5, prev=prev)
        mem[0xD501] = mem[0xD502] = st
        mem[0xD50E] = mem[0xD50F] = 0
        if fill:
            s.run_frame()                 # level-fill frame: mapped objects are created (the hazard is not reached in it)
        pr.reset()

    def go(frames):
        seen, events = [], []
        for f in range(frames):
            s.pad = 0
            s.run_frame()
            seen.append(mem[0xD501])
            events.append((mem[0xD3C0], mem[0xD3B0], pr.counts.get("floor_spike_hurt_jump", 0), pr.counts.get("hurt_entry", 0)))
        return seen, events
    for st, name, f3, grounded in STATE_LIST:
        row = {"state": h(st, 2), "label": name}
        enter(st, 1520, 836 if grounded else 838, 0, 0x100, grounded, f3, prev=0x85, fill=False)
        seen, ev = go(10)
        row["static_spike"] = {"terrain_pass_calls": pr.counts.get("terrain_pass", 0), "damage_gate_calls": pr.counts.get("damage_gate", 0), "floor_spike_hurt_calls": ev[-1][2],
                               "first_hurt_update": next((i for i, x in enumerate(ev) if x[2]), None), "states_seen": _runs(seen)}
        enter(st, 1040, 384 - 34, 0, 0x100, False, 1 if not grounded else f3)
        seen, ev = go(24)
        row["platform"] = {"support_claimed": any(x[0] == PLATFORM_SOLID_ID for x in ev), "first_claim_update": next((i for i, x in enumerate(ev) if x[0] == PLATFORM_SOLID_ID), None),
                           "platform_carry_calls": pr.counts.get("platform_carry", 0), "states_seen": _runs(seen)}
        enter(st, 1344, 812, 0, 0x200, False, 1 if not grounded else f3)
        seen, ev = go(14)
        row["moving_spike"] = {"damage_request_written": any(x[1] == 0xFF for x in ev), "hurt_entry_calls": ev[-1][3], "states_seen": _runs(seen)}
        rows.append(row)
    return {"evidence": "EMULATED ORIGINAL FRAME", "method": "see docstring of emulated_state_matrix", "rows": rows}


def emulated_update_order(rom: bytes) -> dict:
    e, pr = _spike_emu(rom)
    out = {"evidence": "EMULATED ORIGINAL FRAME (PC hooks on the named routines; one frame each, labels in execution order)"}

    def one_frame_events(prep, settle, frames_wanted=1):
        e.restore()
        pr.reset()
        prep()
        for _ in range(settle):
            e.s.pad = 0
            e.s.run_frame()
        pr.reset()
        e.s.pad = 0
        e.s.run_frame()
        names, last = [], None
        for _, n in pr.events:
            if n != last:
                names.append(n)
            last = n
        return names
    out["standing_on_rising_lift"] = one_frame_events(lambda: e.place(592, 444, 0, 0x100), 12)
    out["standing_on_sag_platform"] = one_frame_events(lambda: e.place(1040, 354, 0, 0x100), 12)
    # the frame in which the static spike hurts: run until the hurt entry is first reached and report that frame's events
    e.restore()
    pr.reset()
    e.place(1520, 810, 0, 0x300, cur=0x0E, f3=1, rings=5, prev=0x85)
    for _ in range(30):
        pr.reset()
        e.s.pad = 0
        e.s.run_frame()
        if pr.counts.get("hurt_entry"):
            break
    names, last = [], None
    for _, n in pr.events:
        if n != last:
            names.append(n)
        last = n
    out["static_spike_hurt_frame"] = names
    e.restore()
    pr.reset()
    e.place(1344, 790, 0, 0x100, cur=0x0E, f3=1, rings=5)
    frames = []
    for _ in range(30):
        pr.reset()
        e.s.pad = 0
        e.s.run_frame()
        q = e.slot_of(0x1B)
        frames.append((pr.counts.get("hurt_entry", 0), e.s.mem[0xD3B0], [n for _, n in pr.events]))
        if frames[-1][0]:
            break
    req_idx = next((i for i, f in enumerate(frames) if f[1] == 0xFF), None)
    def squash(lst):
        out2, last2 = [], None
        for n in lst:
            if n != last2:
                out2.append(n)
            last2 = n
        return out2
    out["moving_spike_request_frame"] = squash(frames[req_idx][2]) if req_idx is not None else None
    out["moving_spike_hurt_frame"] = squash(frames[-1][2])
    return out


def contact_flags_after_merge(rom: bytes) -> dict:
    """What the object contact leaves in the player's merged flags D523 ($64CB): is a side/underside contact a wall?"""
    out = {"evidence": "CONTROLLED ROUTINE RESULT (real callback, then $64CB with the player's own D522 clear)"}
    plat = platform_lab(rom, 0x84, 0)
    spk = spike_lab(rom)
    spike_set_state(spk, 2, 846)
    for name, lab, ex_dy in (("platform_state5", plat, 0), ("spike_1b_state2", spk, 0)):
        m, o = lab.m, lab.o
        ox, oy = lab.obj16(0x11), lab.obj16(0x14)
        table = {}
        for label, f3 in (("walker", 0), ("attacking", 2)):
            res = {}
            for tag, dx, dy in (("right_side", 20, 8), ("left_side", -20, 8), ("below", 0, 20), ("above_support_zone", 0, -8), ("far_corner_horizontal", 22, -2)):
                lab.reset()
                lab.player(ox + dx, oy + dy, vy=0x300, f3=f3, f22=0)
                lab.callback()
                o.cpu.ix = 0xD500
                o.bank(2, 0x0C)
                o.call(0x64CB)
                res[tag] = {"d521": h(m[0xD521], 2), "d523": h(m[0xD523], 2), "d3c0": m[0xD3C0], "wall_right_bit2": bool(m[0xD523] & 4), "wall_left_bit3": bool(m[0xD523] & 8), "floor_bit1": bool(m[0xD523] & 2),
                            "ceiling_bit0": bool(m[0xD523] & 1)}
            table[label] = res
        out[name] = table
    out["reading"] = ("platform: side and underside contact leave no wall bits (the clear path $8843 removes them) - the platform is top-only; "
                      "moving spike: a non-attacking player's side contact becomes D523 bit 2/3 (a wall for the X integration); an attacking player is not merged and is pushed out instead")
    return out


# --------------------------------------------------------------------------- #
# 11. horizontal-mode carry (ROM-supported, unused by THZ placements), anchors, POC comparison, unresolved
# --------------------------------------------------------------------------- #
def horizontal_mode_carry(rom: bytes) -> dict:
    """Parameter $00 = state 1 (horizontal mover, X speed +1.0): proves the X-delta carry path that no THZ placement uses."""
    lab = platform_lab(rom, 0x00, 0, world=(1024, 512))
    m, o = lab.m, lab.o
    ox, oy = lab.obj16(0x11), lab.obj16(0x14)
    rows = []
    lab.player(ox, oy - 14, vy=0x190)
    for i in range(6):
        lab.frame()
        rows.append([i, lab.obj16(0x11) - 1024, o.word(0xD511) - 1024, o.word(0xD514) - 512, s16(o.word(0xD516)), m[0xD3C0], s16(o.word(SLOT + 0x23))])
    return {"evidence": "CONTROLLED ROUTINE RESULT (state 1 callback $8628)", "state": m[SLOT + 1], "platform_x_speed_8_8": s16(lab.obj16(0x16)),
            "rows_[update,platform_dx,player_dx,player_dy,player_vx,d3c0,carry_delta_+23]": rows,
            "reading": "the player receives the platform's integer X displacement of that update (+$23/+$24, = new X - old X, computed after the move) added to its X; Y is re-snapped to platform Y - 14; "
                       "no player speed is changed. The vertical movers' +$23/+$24 stays 0, so the lifts and sag platforms carry only in Y."}


def anchors() -> dict:
    return {
        "evidence": "EMULATED ORIGINAL FRAME (SAT + VRAM opaque rows) + BYTE-VERIFIED ASSEMBLY + docs/mapped-object-screen-registration.md",
        "rule": "world row of a sprite line = line + camera Y + 17 (shared registration: VScroll 17 + SAT 1); opaque rows are quoted relative to the object/player anchor Y",
        "type_28_platform": {
            "canonical_placement_anchor": "record X, Y (world, after the $0100 bias is removed)",
            "runtime_anchor": "+$11/+$12 X, +$14/+$15 Y (lifts move it 1 px/update; sag platforms add +0..+8 while ridden)",
            "collision_anchor": "same as the runtime anchor; $6328 box x +-16, y [-16, 0] (extents +$2C/+$2D = 16,16, both frames)",
            "sprite_opaque_rows_relative_to_anchor": "+2..+17 (measured: platform lines 103..118 at anchor world 384, camera Y 266)",
            "support_probe": "player anchor Y after carry = platform Y - 14 (the equivalent terrain foot row anchor+18 = platform Y + 4); player opaque rows -13..+17 (measured standing on the sag platform: world rows 357..387)",
            "visual_overlap": "Sonic's last opaque row (platform Y + 3) is two rows below the platform's first opaque row (platform Y + 2): Sonic is drawn two pixels into the platform top; the collision box top (platform Y - 16) is 18 rows above the visible top",
            "presentation_offset_must_not_move_gameplay": "the 18-row gap between collision top and visible top is canonical; a GameMaker presentation offset must not be absorbed into the support geometry"},
        "type_1b_moving_spike": {
            "canonical_placement_anchor": "record X, Y = 864 (also the hidden/retracted Y = +$3C)",
            "runtime_anchor": "+$14 moves 864 -> 846 in steps of 6",
            "collision_anchor": "runtime anchor; $6328 box x +-16, y [-24, 0]; damage region is the 45-degree cone above the anchor (see audit)",
            "sprite_opaque_rows_relative_to_anchor": "-6..+17 (docs/mapped-object-screen-registration.md, frame $0E shared)",
            "hazard_probe": "player anchor (not the foot): contact needs the player's anchor above the object's anchor by 1..24"},
        "static_spike_terrain": {
            "canonical_placement_anchor": "layout cell (32x32), block $3D / $3C; no object record",
            "collision_anchor": "terrain lookup: foot probe (X, Y+18), side probes (X-9, Y+6)/(X+9, Y+6), ceiling probe (X, Y-6)",
            "surface": "vertical profile 16 for every column: the spike surface is block row 16 (16 px above the block bottom); horizontal profile rows 0..15 = $40 (empty), rows 16..31 = $60 (full width, bit 6)",
            "sprite": "block art $3D (tiles); not an object; presentation offsets do not apply to terrain collision"},
    }


def poc_comparison() -> dict:
    return {
        "evidence": "POC SOURCE (READ-ONLY): SonicChaos_POC_thz1_cleanup @ 7799c34; files read, never executed or modified",
        "files_read": ["scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml", "scripts/SCR_chaos_motion/SCR_chaos_motion.gml", "scripts/SCR_chaos_core/SCR_chaos_core.gml",
                       "objects/OBJ_chaos_platform/Create_0.gml", "objects/OBJ_chaos_spikes/{Create_0,Step_0}.gml"],
        "rows": [
            {"area": "static spike probing", "poc": "SCR_cc_floor: kind 5 -> hazard iff tile not $F4/$F5, (bg & 2) floor flag and (player_flags & 128) == 0, after the previous-surface projection",
             "rom": "$6ACE: same three conditions after $6F61 projection of the previous surface", "verdict": "STRUCTURALLY MATCHES; the outcome depends on the lifetime of the floor flag (bg & 2) which the POC clears in several adapters "
                                                                                                                     "($6C45-type empty-floor path, support clears) - a mismatch is possible only there and is not proven",
             "class": "NOT PROVEN"},
            {"area": "diagonal static-spike phasing", "poc": "no source evidence of a different probe; no ROM-side phasing exists (see audit section 6)",
             "rom": "every approach is damaged, blocked by the side wall, or clears the pair in the air (1,446 emulated runs, 0 undamaged contacts)",
             "verdict": "A POC phase-through is NOT explained by the ROM: candidate causes are POC-side only (floor-flag clearing, previous-surface bookkeeping, side wall rows 16..31, integer-pixel stepping); needs a POC replay",
             "class": "UNRESOLVED (POC-side)"},
            {"area": "moving spike $1B geometry", "poc": "SCR_chaos_spike_step: damage when the player's mask bbox overlaps x +-16 and [baseY-min(32,18+offset), baseY] in states 1/2",
             "rom": "$6328 box x +-24 vs the player's 8-wide box; damage ONLY for the 'player above' cone (dy -24..-1, |dx| <= |dy|), only when the player's Y speed >= 0, with a 16-update cooldown; "
                    "side/below contact never damages; non-attacking side contact is a WALL (D523 bit 2/3); an attacking grounded player is pushed to +-23 and requested state 1",
             "verdict": "MISMATCH (ROM-backed): POC damages on any bbox overlap incl. sides/below/rising and has no cooldown and no wall/push behaviour", "class": "CRITICAL"},
            {"area": "moving spike timing", "poc": "offset +6 per update to 18, hold 48, -6, hold 48; damage check after the move",
             "rom": "contact test BEFORE the Y move in state 1; cycle 102 updates (48 hidden, 3 rising, 48 raised, 3 retracting); no test while retracting/hidden",
             "verdict": "cycle length matches; test order differs by one 6-px step during the 3 rising updates", "class": "EDGE"},
            {"area": "platform support geometry", "poc": "SCR_chaos_platform_overlap: bbox_right >= x-16 and bbox_left < x+16; foot within [y-1, y+20]; previous foot <= previous platform Y; snap anchor = platform y - 19 (POC platform coordinates)",
             "rom": "support iff 'player above' contact of $6328: dy in [-16,-1] and |dx| <= min(24, 8+|dy|) (triangular region), platform Y speed <= player Y speed, anchor snapped to platform Y - 14",
             "verdict": "MISMATCH likely: rectangular sprite-mask overlap vs triangular ROM region; vertical tolerance model differs; snap offset must be re-derived from the ROM (-14 anchor) not the sprite", "class": "EDGE/CRITICAL (needs POC replay)"},
            {"area": "platform speed gate and retained vy", "poc": "support only for vy >= 0; landing sets vy = 0",
             "rom": "gate is relative: support requires player vy >= platform vy (rising lifts allow slightly rising players, descending lifts need vy >= +1.0); landing leaves the player's Y speed untouched (e.g. $0190 stays)",
             "verdict": "MISMATCH (ROM-backed)", "class": "EDGE"},
            {"area": "platform carry order", "poc": "SCR_chaos_world_begin advances platforms BEFORE the player step and re-lands the rider from the platform delta",
             "rom": "player update FIRST (movement, terrain, damage), platform callback afterwards: move, contact test, snap Y = platform Y - 14, X += delta",
             "verdict": "ORDER DIFFERS: the ROM rider is positioned after the platform's move within the same frame; POC positions it before the player step (one-update phase difference)", "class": "EDGE"},
            {"area": "THZ2 lifts", "poc": "Create_0 assigns chaosTravel only for x == 592 (144) and x == 3664 (208)",
             "rom": "THZ2 lifts at (552,720) aux $19 (400 updates) and (3672,608) aux $13 (304 updates)", "verdict": "MISMATCH for THZ2 if the same object is reused (travel 0 = sag behaviour)", "class": "CRITICAL for THZ2"},
            {"area": "sag platform", "poc": "sag +1 per ridden update to 8, then returning flag, decrement; platform y = home + sag",
             "rom": "+1..+8 (8 updates), one hold update at 8, then -1..0 while still ridden; after release rises 1 px/update", "verdict": "MATCHES the recovered sequence", "class": "MATCH"},
            {"area": "damage gating", "poc": "SCR_chaos_apply_hazard_damage: returns when playerSuper/playerBlink/powerInv; ring-loss/death handled by sample-engine objects",
             "rom": "terrain: +$03 bit 7 only; object requests: $48BC gate (+3 bit 7 -> countdown, bit 6 -> ignore, $D532 == 6 -> clear); invulnerability = 120 countdown updates, cleared on the 121st gate update",
             "verdict": "NOT COMPARED in depth (POC sample-engine damage is outside this audit)", "class": "NOT PROVEN"}],
        "rule": "nothing above is a POC bug unless its row says ROM-backed; platform support/geometry rows need a POC replay on Windows before changing code"}


def unresolved() -> list:
    return [
        "player states other than the numerically tested ones were not run through the platform/spike matrix; loop (`$0C/$0D/$13`) and twist (`$22`) states reposition the player, so a teleport cannot exercise platform/spike contact in them",
        "which input sequence reproduces a given phase of the first-frame hurt consequences in the original (the emulated game uses explicit teleports, not recorded play)",
        "object lifecycle (activation, removal, recreation phase) of platforms and $1B spikes: only the persistence radius and the recreate-from-record rule were used; no exhaustive lifecycle audit",
        "the purpose of $D4A5 (written only by $8866 when both speeds are negative) was not traced; nothing in this audit depends on it",
        "state $17 (requested) takes the type-5 breakable branch at the side probes ($72B6/$72DD): its entry condition and effect on spike blocks were located but not exercised",
        "the POC was read but never run: every POC row is source-level only",
        "the sound routine $062D and ring-scatter object behaviour were stubbed/not studied (not part of collision)",
        "original-game visual confirmation (video) of the non-attacking side wall against a raised $1B spike was not performed; the result is emulated-routine evidence",
    ]




def emulated_natural_jumps(rom: bytes) -> dict:
    """No teleport into the block: Sonic stands on the ground row left (or right) of the pair, holds toward it and jumps; one run per start X and jump length."""
    e = Emu(rom, "thz1")
    hurt: list = []
    e.s.add_pc_hook(HURT_ENTRY, lambda m: hurt.append(e.s.frame))
    e.s.add_pc_hook(0x6AE0, lambda m: TERRAIN_HURT.append(e.s.frame))
    counts, examples = {}, {}
    n = 0
    for side, xs, toward in (("left", range(1440, 1500, 3), PAD["RIGHT"]), ("right", range(1572, 1632, 3), PAD["LEFT"])):
        for hold in (1, 4, 8, 16):
            for x0 in xs:
                e.restore()
                hurt.clear()
                TERRAIN_HURT.clear()
                e.place(x0, PAIR_GROUND_Y, 0, 0x700, cur=1, f3=0, floor=True, rings=5)
                path = []
                for f in range(60):
                    e.s.pad = toward | (PAD["B1"] if 3 <= f < 3 + hold else 0)
                    e.s.run_frame()
                    path.append((e.u16(0xD511), e.u16(0xD514), e.s.mem[0xD503] & 1, e.s.mem[0xD501], s16(e.u16(0xD518))))
                    if hurt:
                        break
                cl = _spike_class(x0 if side == "left" else x0, path, hurt)
                n += 1
                counts[f"{side}|{cl}"] = counts.get(f"{side}|{cl}", 0) + 1
                if cl[0] in "E" and len(examples.setdefault(cl, [])) < 5:
                    solid = [(x, y, vy) for x, y, _, _, vy in path if PAIR_L <= x <= PAIR_R and PAIR_SPIKE_TOP + 16 <= y + 18 <= PAIR_SPIKE_TOP + 31]
                    examples[cl].append({"side": side, "start_x": x0, "jump_button_updates": hold, "foot_in_solid_rows_samples_[x,y,vy]": solid[:6], "end": list(path[-1][:2]), "frames": len(path)})
    return {"evidence": "EMULATED ORIGINAL FRAME (Sonic starts standing on the ground row beside the pair, direction held, jump pressed at update 3)", "runs": n,
            "counts": dict(sorted(counts.items())), "examples": examples}


def rising_pass_band(rom: bytes) -> dict:
    """Anchor-Y band in which the foot is inside the solid spike rows but the side probe is above the wall rows: a rising player is neither damaged nor pushed."""
    tl = TerrainLab(rom, "thz1")
    x = 1512                                     # inside the pair for both probes (X-9 = 1503 is outside; X+9 = 1521 inside)
    band = {}
    for label, vy in (("rising_-1.0", -0x100), ("level_0", 0), ("descending_+1.0", 0x100)):
        free, hit, pushed = [], [], []
        for y in range(822, 852):
            r = tl.run_terrain(x, y, vx=0x200, vy=vy, floor=False, prev=0x85, cur=0x0A, req=0x0A, f3=3)
            foot_solid = 848 <= y + 18 <= 863
            if r["hit"]:
                hit.append(y)
            elif r["x"] != x:
                pushed.append(y)
            elif foot_solid:
                free.append(y)
        band[label] = {"foot_in_solid_rows_undamaged_unpushed_anchor_y": ranges(free), "damaged_anchor_y": ranges(hit), "pushed_by_wall_anchor_y": ranges(pushed)}
    return {"evidence": "CONTROLLED ROUTINE RESULT ($690B, THZ1 pair, previous surface = spike $85, airborne)", "x": x, "by_vertical_speed": band,
            "reading": "anchor Y 830..841 puts the foot probe in the solid rows (848..859) while the side probe (Y+6) is above row 848: no wall; a rising player is then untouched, a level/descending player is projected to Y=830 and hurt; "
                       "anchor Y >= 842 puts the side probe in the wall rows (pushed)"}


# --------------------------------------------------------------------------- #
# 12. terrain-backed platform surfaces (stationary one-way platforms)
# --------------------------------------------------------------------------- #
ONE_WAY_CELLS = {"thz1": [(864, 416), (896, 416), (448, 512), (480, 512), (512, 512), (544, 512), (640, 608), (672, 608), (704, 608)]}


def terrain_surface_classes(rom: bytes) -> dict:
    out = {}
    for act in ACTS:
        counts = {}
        for r in layout_rows(act):
            for b in r:
                counts[b] = counts.get(b, 0) + 1
        classes = {}
        for b, n in counts.items():
            f = block_header(rom, b)["flags"]
            key = f"bit7_solid={int(bool(f & 0x80))} bit6_oneway={int(bool(f & 0x40))} alt_plane={int(bool(f & 0x20))} type={f & 0x1F:02X}"
            c = classes.setdefault(key, {"blocks": [], "cells": 0})
            c["blocks"].append(h(b, 2))
            c["cells"] += n
        out[act] = {k: {"blocks": sorted(v["blocks"]), "cells": v["cells"]} for k, v in sorted(classes.items())}
    return {"evidence": "DECODED DATA (block headers via the layout)", "classes_by_act": out,
            "one_way_platform_block": {"0x0D": "flags $41 (bit 6 one-way, type 1), vertical profile 32, horizontal profile $60: a full 32x32 cell that is solid only from above; no side or ceiling core runs (bit 7 clear)",
                                       "0xAF": "flags $4C (one-way, type $0C), one THZ1/THZ2 cell, same profiles"}}


def terrain_one_way_sweep(rom: bytes) -> dict:
    """The terrain-backed one-way platform (block $0D) over its cells: previous surface x floor flag x Y speed class, plus side and ceiling approach."""
    tl = TerrainLab(rom, "thz1")
    cx, cy = 864, 416                           # cells (27,13)+(28,13): left neighbour air, right neighbour $0D
    vys = {"rising_-1.0": -0x100, "zero": 0, "+1.0": 0x100, "+2.0": 0x200, "+4.0": 0x400, "+7.0": 0x700}
    out, n = {}, 0
    for pn, prev in (("none_00", 0x00), ("oneway_41", 0x41), ("solid_81", 0x81)):
        for floor in (False, True):
            for vn, vy in vys.items():
                rows = []
                for foot in range(cy - 4, cy + 40):
                    r = tl.run_terrain(cx + 16, foot - 18, vy=vy, floor=floor, prev=prev)
                    n += 1
                    if r["y"] != foot - 18:
                        rows.append(foot - cy)
                out[f"prev_{pn}|floor_{int(floor)}|vy_{vn}"] = {"projected_foot_rows_relative_to_cell_top": ranges(rows)}
    sides, ceil = 0, 0
    for y in range(cy - 30, cy + 40):
        for x in range(cx - 20, cx + 64 + 20):
            r = tl.run_terrain(x, y, vx=0x200, floor=False, prev=0x41, cur=0x0A, req=0x0A, f3=3)
            c = tl.run_terrain(x, y, vy=-0x300, floor=False, prev=0x41, cur=0x0A, req=0x0A, f3=3)
            n += 2
            # a pure side push moves X only; a ceiling push moves Y upward-rising only
            sides += r["x"] != x
            ceil += (c["y"] != y) and (c["y"] > y)
    return {"evidence": "CONTROLLED ROUTINE RESULT ($690B on the real THZ1 layout)", "cases": n, "cell_world": [cx, cy], "results": out,
            "side_pushes": sides, "ceiling_pushes_on_rising_player": ceil,
            "reading": "support rows are those where the projection moved the player; one-way = no side push and no ceiling push, projection skipped while rising and bounded for descending players"}


# --------------------------------------------------------------------------- #
# 13. platform and static-spike terrain in the same update (synthetic placement: no THZ platform lies over a spike cell)
# --------------------------------------------------------------------------- #
def emulated_platform_vs_spike_terrain(rom: bytes) -> dict:
    """A real sag-platform slot image is cloned over the THZ1 spike pair at several heights; Sonic falls onto it from above (0 rings)."""
    e = Emu(rom, "thz1")
    s, mem = e.s, e.s.mem
    terrain_hurt, hurt = [], []
    s.add_pc_hook(0x6AE0, lambda m: terrain_hurt.append(s.frame))
    s.add_pc_hook(HURT_ENTRY, lambda m: hurt.append(s.frame))
    e.place(1040, 384 - 30, 0, 0x100)
    e.run(3)
    q = e.slot_of(0x28)
    image = bytes(mem[q:q + 0x40])
    base = e.snapshot()
    rows = []
    for plat_y in (830, 835, 838, 840, 842, 845, 850, 856, 862):
        e.restore(base)
        terrain_hurt.clear()
        hurt.clear()
        e.place(1520, 790, 0, 0x100)
        e.run(2)
        for i in range(19):
            b = 0xD540 + i * 0x40
            if mem[b] == 0x28:
                mem[b:b + 0x40] = bytes(0x40)
        for i in range(19):
            b = 0xD540 + i * 0x40
            if mem[b] == 0:
                mem[b:b + 0x40] = image
                for off, val in ((0x11, 1520), (0x14, plat_y), (0x3A, 1520), (0x3C, plat_y)):
                    mem[b + off], mem[b + off + 1] = val & 0xFF, val >> 8
                mem[b + 0x10] = mem[b + 0x13] = mem[b + 0x35] = mem[b + 0x33] = 0
                break
        claim_update, y_at_claim, hurt_update = None, None, None
        for f in range(40):
            s.pad = 0
            s.run_frame()
            if claim_update is None and mem[0xD3C0] == PLATFORM_SOLID_ID:
                claim_update, y_at_claim = f, e.u16(0xD514)
            if hurt and hurt_update is None:
                hurt_update = f
            if claim_update is not None and hurt_update is not None or (claim_update is not None and f > claim_update + 6):
                break
        rows.append({"platform_y": plat_y, "terrain_spike_hurt_update": hurt_update, "support_claim_update": claim_update, "player_y_when_claimed": y_at_claim,
                     "outcome": ("support only (no damage within the window)" if hurt_update is None and claim_update is not None else
                                 "terrain hurt before any platform contact" if hurt_update is not None and claim_update is None else
                                 "support claimed first; on a later player pass (still airborne with the retained falling speed, or carried down by the sinking platform) the foot probe reached the spike surface and the terrain hurt him" if claim_update < hurt_update else
                                 "terrain hurt in the same update as the claim" if claim_update == hurt_update else "terrain hurt, then the platform claimed")})
    return {"evidence": "EMULATED ORIGINAL FRAME (cloned type-$28 state-5 slot at x=1520 over the spike pair; no THZ placement overlaps a spike cell)", "rows": rows,
            "reading": "the player pass (terrain projection + hurt) runs BEFORE the platform contact test of the same update. A platform whose support plane is above the spike surface (anchor Y 830) holds Sonic "
                       "clear; if the support plane is within about one fall step of the surface, the next player pass (the landing is only registered at the END of that pass, so the Y integration still runs with the retained speed) "
                       "or the sinking of a sag platform brings the foot onto the surface and the terrain handler hurts him (the platform never reads the hurt state)"}


# --------------------------------------------------------------------------- #
# build / CLI
# --------------------------------------------------------------------------- #
def _count_cases(node) -> int:
    """Sum every integer field named cases/runs in the report (reported at the end of the study)."""
    total = 0
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("cases", "runs") and isinstance(v, int):
                total += v
            else:
                total += _count_cases(v)
    elif isinstance(node, list):
        for v in node:
            total += _count_cases(v)
    return total


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    out = {
        "format": 1, "rom_sha256": ROM_SHA256, "research_only": True, "poc_untouched": True, "machine_facing_label": "platform_spike_collision",
        "evidence_classes": EVIDENCE,
        "routines": routine_table(rom),
        "platform_placements": platform_placements(),
        "platform_modes": platform_modes(rom),
        "spike_1b_placements": spike_placements(),
        "static_spike_terrain": spike_block_inventory(rom),
        "terrain_probe_geometry": terrain_probe_geometry(rom),
        "anchors": anchors(),
        "poc_comparison": poc_comparison(),
        "unresolved": unresolved(), "static_only": static_only,
    }
    if static_only:
        return out
    out["platform_support"] = platform_support(rom)
    out["platform_gate_8866"] = platform_gate(rom)
    out["platform_gates_matrix"] = platform_gates_matrix(rom)
    out["platform_horizontal_mode_carry"] = horizontal_mode_carry(rom)
    out["platform_emulated"] = emulated_platform(rom)
    out["contact_flags_after_merge"] = contact_flags_after_merge(rom)
    out["terrain_foot_sweep"] = terrain_foot_sweep(rom)
    out["terrain_side_ceiling_sweep"] = terrain_side_ceiling_sweep(rom)
    out["static_spike_diagonal_sweep"] = emulated_spike_sweep(rom)
    out["terrain_surface_classes"] = terrain_surface_classes(rom)
    out["terrain_one_way_platform"] = terrain_one_way_sweep(rom)
    out["static_spike_rising_band"] = rising_pass_band(rom)
    out["static_spike_natural_jumps"] = emulated_natural_jumps(rom)
    out["static_spike_aftermath"] = emulated_static_spike_aftermath(rom)
    out["spike_1b_timeline"] = spike_timeline(rom)
    out["spike_1b_contact_sweep"] = spike_contact_sweep(rom)
    out["spike_1b_gates"] = spike_helper_gates(rom)
    out["spike_1b_move_before_contact"] = spike_move_before_contact(rom)
    out["spike_1b_emulated"] = emulated_moving_spike_scenarios(rom)
    out["damage_gate_48bc"] = damage_gate_matrix(rom)
    out["hurt_consequences"] = hurt_consequences(rom)
    out["invulnerability_countdown"] = invulnerability_countdown(rom)
    out["state_matrix"] = emulated_state_matrix(rom)
    out["update_order"] = emulated_update_order(rom)
    out["platform_vs_spike_terrain"] = emulated_platform_vs_spike_terrain(rom)
    out["counts"] = {"controlled_and_emulated_cases_total": _count_cases(out)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    a = ap.parse_args()
    rom = a.rom.read_bytes()
    data = build(rom, a.static_only)
    text = json.dumps(data, indent=1) + chr(10)
    if a.check:
        cached = OUTPUT.read_text(encoding="utf-8")
        if a.static_only:
            cj, dj = json.loads(cached), json.loads(text)
            bad = [k for k in dj if k in cj and k != "static_only" and cj[k] != dj[k]]
        else:
            bad = [] if cached.replace(chr(13) + chr(10), chr(10)) == text else ["file"]
        print("OK: cache matches the ROM" if not bad else f"MISMATCH in {bad}")
        sys.exit(1 if bad else 0)
    OUTPUT.write_text(text, encoding="utf-8", newline=chr(10))
    print(f"wrote {OUTPUT} ({len(text)} bytes); cases: {data.get('counts')}")


if __name__ == "__main__":
    main()

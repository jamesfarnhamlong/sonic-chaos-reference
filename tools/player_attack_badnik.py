#!/usr/bin/env python3
"""Player attack posture ($D503 bit 1), power-up $D532 and badnik interaction audit (research only, deterministic).

Answers: what makes Sonic count as attacking, every writer/reader of the attack bit, what $D532 == 6 is, the shared
contact path ($6328 -> $D520 -> $48BC), each THZ1/THZ2 enemy's own defeat/damage rule, the rebound, the exact update
order, and the parked type $27 observation.  Output: data/rom-cache/player-attack-badnik.json (numeric labels only).

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT
(original Z80 routines on tools/oracle.py), EMULATED ORIGINAL FRAME (tools/sms_frame_harness.py), UNRESOLVED.

Usage:
  python tools/player_attack_badnik.py ROM.sms [--check] [--static-only]
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
OUTPUT = ROOT / "data" / "rom-cache" / "player-attack-badnik.json"
POC_COMMIT = "7799c3459f59781878574e5d805bb3df4baa057c"
OBJ = 0xD540
BANK_PLAYER = 12


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def s16(v: int) -> int:
    return (v + 32768) % 65536 - 32768


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rom_of(bank: int, cpu: int) -> int:
    return cpu if cpu < 0x8000 else bank * 0x4000 + cpu - 0x8000


def cpu_of(off: int) -> tuple:
    if off < 0x8000:
        return (0 if off < 0x4000 else 1), off
    return off // 0x4000, 0x8000 + off % 0x4000


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def find_all(rom: bytes, pat: bytes) -> list:
    out, i = [], rom.find(pat)
    while i >= 0:
        out.append(i)
        i = rom.find(pat, i + 1)
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
    ("player_frame_361d", 0, 0x361D, 0x3657, "player update: engine $64FA, state callback $5E91, then $4A74"),
    ("shared_movement_3fef", 0, 0x3FEF, 0x401A, "clamp, input, X/Y integrate, terrain $690B, damage/contact $48BC, jump request"),
    ("damage_contact_48bc", 1, 0x48BC, 0x4A33, "D532==6 immunity, D3B0 damage request, D520 contact: attack bounce or damage, hurt, death"),
    ("power_up_timer_4a74", 1, 0x4A74, 0x4AA3, "power-up D532 timer; expiry clears 4 and 6"),
    ("reward_dispatch_4aa3", 1, 0x4AA3, 0x4B46, "monitor reward bits: D532 := 3 / 4 / 6"),
    ("state_setters_45b3", 1, 0x45B3, 0x4892, "every player state request setter and its $D503 effect"),
    ("act_clear_setter_4892", 1, 0x4892, 0x48A7, "request state $20"),
    ("floor_loss_6c72", 1, 0x6C45, 0x6C82, "loss of floor: fall $0E (bit1 clear) or, when rolling, jump $0A (bit1 set)"),
    ("attack_convert_5f3d", 1, 0x5F3D, 0x5F84, "badnik defeat gate: D532==6 or D503 bit 1, then convert to type $0F"),
    ("object_overlap_6328", 1, 0x6328, 0x640B, "shared overlap; sets player D520 (slot id) for non-ghost objects"),
    ("slot_index_606b", 1, 0x606B, 0x607A, "object address -> slot id ((addr-$D500)/$40 + 1)"),
    ("type21_contact_b2af", 12, 0xB2AF, 0xB2EB, "type $21 stomp/attack/damage tail"),
    ("type27_handlers", 30, 0x898E, 0x8A45, "type $27 callbacks"),
    ("type10_contact_a16c", 12, 0xA16C, 0xA1D3, "monitor: attack-bit gate, rebound, break"),
    ("type1b_spike_helper_acfd", 12, 0xACFD, 0xAD59, "moving spike contact helper"),
    ("type05_aura_998a", 12, 0x9959, 0x99FB, "type $05 child: re-asserts D503 bit 7 (and bit 1 for state $15/$1A)"),
    ("peel_out_state_1a_init_8313", 12, 0x8313, 0x831D, "state $1A entry: D503 bit 7, D3B1 := 12"),
    ("twist_exit_95ec_978b", 12, 0x95DD, 0x9610, "twist exit requests state 9 / state $0A without touching bit 1"),
]


def routine_table(rom: bytes) -> list:
    out = []
    for name, bank, a, b, purpose in ROUTINES:
        o, e = rom_of(bank, a), rom_of(bank, b)
        out.append({"name": name, "bank": bank, "cpu": h(a), "rom_offset": h(o, 5), "end_cpu_exclusive": h(b), "length": b - a,
                    "sha256": sha(rom[o:e]), "first_16_bytes": rom[o:o + 16].hex(), "purpose": purpose})
    return out


# --------------------------------------------------------------------------- #
# 1. static scans
# --------------------------------------------------------------------------- #
# Named code regions used to label scan hits (bank 0/1 player code and the bank-12 twist/aura code).
REGIONS = [
    (0, 0x36C6, 0x3713, "state 0/1 standing callback"), (0, 0x3713, 0x3759, "state 3 callback"), (0, 0x3759, 0x3783, "state 4 callback"),
    (0, 0x3783, 0x384D, "state 5 walk callback"), (0, 0x384D, 0x386F, "state 6 run callback"), (0, 0x386F, 0x38C5, "state 7/8 skid callbacks"),
    (0, 0x38C5, 0x3901, "state 9 roll / state $1B callbacks"), (0, 0x3901, 0x393B, "state $0A jump callback"),
    (0, 0x393B, 0x3955, "state $0B upright spring callback"), (0, 0x3955, 0x396D, "state $1C diagonal spring callback"),
    (0, 0x396D, 0x39B6, "state $15 peel-out charge callback"), (0, 0x39B6, 0x39E6, "state $1A peel-out run callback"),
    (0, 0x39E6, 0x3A23, "state $0F spin-dash charge callback"), (0, 0x3A23, 0x3A37, "state $10 spin-dash roll callback"),
    (0, 0x3A37, 0x3A59, "state $0E / $14 falling callbacks"), (0, 0x3A59, 0x3A7C, "state $1D / $1E callbacks"),
    (0, 0x3A7C, 0x3B4E, "state $11 callback"), (0, 0x3B4E, 0x3BA8, "state $12 callback"), (0, 0x3BC6, 0x3C1B, "state $19 / $1F / death callbacks"),
    (0, 0x3C1B, 0x3EFD, "loop states $0C/$0D/$13"), (0, 0x3F00, 0x3F90, "scripted movement routine"),
    (1, 0x401A, 0x402A, "death boundary"), (1, 0x45B3, 0x45CE, "setter: stand (state 1)"), (1, 0x45CE, 0x45ED, "setter: land (state 5)"),
    (1, 0x45ED, 0x463C, "setter: jump (state $0A)"), (1, 0x463C, 0x4663, "setter: fall (state $0E)"), (1, 0x4663, 0x4680, "setter: state $14"),
    (1, 0x4680, 0x4699, "setter: state $1D"), (1, 0x4699, 0x46B0, "setter: jump state without impulse (state $0A)"),
    (1, 0x46B0, 0x46BB, "setter: state 3"), (1, 0x46BB, 0x46CE, "setter: state 4"), (1, 0x46CE, 0x46E2, "setter: state $15 (peel-out charge)"),
    (1, 0x46E2, 0x4701, "setter: state $1A (peel-out run)"), (1, 0x4701, 0x4719, "setter: state $0F (spin-dash charge)"),
    (1, 0x4719, 0x473C, "setter: state $10 (spin-dash roll)"), (1, 0x473C, 0x4775, "setter: state $18"), (1, 0x4775, 0x47A9, "setter: state $11"),
    (1, 0x47A9, 0x47B6, "setter: state 6"), (1, 0x47B6, 0x47C9, "setter: state 7"), (1, 0x47C9, 0x47DC, "setter: state 8"),
    (1, 0x47DC, 0x47FB, "setter: roll (state 9)"), (1, 0x47FB, 0x480C, "setter: ramp launch (state $1B)"),
    (1, 0x480C, 0x482D, "setter: upright spring (state $0B)"), (1, 0x482D, 0x4849, "setter: diagonal spring (state $1C)"),
    (1, 0x4849, 0x4868, "setter: horizontal spring right (state 9)"), (1, 0x4868, 0x4892, "setter: horizontal spring left (state 9)"),
    (1, 0x48BC, 0x4A33, "damage/contact handler $48BC"), (1, 0x4A74, 0x4AA3, "power-up timer"), (1, 0x4AA3, 0x4B46, "reward dispatch"),
    (1, 0x4BC0, 0x4C02, "water-level / speed helper $4BC0"), (1, 0x4C12, 0x4C56, "state $17 carried-by-object callback"),
    (1, 0x4C56, 0x4C90, "carried-by-object position copy"), (1, 0x6945, 0x69B2, "terrain handler dispatch tail"),
    (1, 0x69B2, 0x6A5B, "ramp contact"), (1, 0x6A5D, 0x6ACE, "terrain springs"), (1, 0x6AE3, 0x6B56, "breakable blocks"),
    (1, 0x6C45, 0x6C82, "floor loss (airborne transition)"), (1, 0x6D43, 0x6E56, "terrain special-entry handlers"),
    (1, 0x7646, 0x7666, "terrain type launch: speed 7.0, state $10"),
    (12, 0x8313, 0x831D, "state $1A entry init"), (12, 0x95DD, 0x9830, "twist handlers"),
    (12, 0x9959, 0x99FB, "type $05 child (power-up aura)"),
]


def region_of(bank: int, cpu: int) -> str:
    for b, a, e, name in REGIONS:
        if b == bank and a <= cpu < e:
            return name
    return "other"


PLAYER_CTX_BANKS = {0, 1}


def d503_sites(rom: bytes) -> dict:
    """Every access form to the player movement byte $D503 and to power-up $D532, located by byte scan."""
    out = {"evidence": "BYTE-VERIFIED ASSEMBLY (whole-ROM byte scan; IX forms labelled by enclosing routine)"}

    def abs_hits(pat, kind):
        rows = []
        for o in find_all(rom, pat):
            b, c = cpu_of(o)
            rows.append({"kind": kind, "rom_offset": h(o, 5), "bank": b, "cpu": h(c), "region": region_of(b, c)})
        return rows
    out["d503_absolute"] = abs_hits(b"\x3a\x03\xd5", "LD A,($D503)") + abs_hits(b"\x32\x03\xd5", "LD ($D503),A") + abs_hits(b"\x21\x03\xd5", "LD HL,$D503 (then bit op on (HL))")
    out["d532_absolute"] = abs_hits(b"\x3a\x32\xd5", "LD A,($D532) read") + abs_hits(b"\x32\x32\xd5", "LD ($D532),A write")
    out["d532_other_forms"] = {"LD rr,$D532": [h(o, 5) for o in find_all(rom, b"\x21\x32\xd5") + find_all(rom, b"\x01\x32\xd5") + find_all(rom, b"\x11\x32\xd5")],
                               "note": "the (IX+$32) forms in bank $1E are object fields of other types (IX is not the player there)"}
    ops = {0x40: "BIT", 0x80: "RES", 0xC0: "SET"}
    rows = []
    for o in find_all(rom, b"\xdd\xcb\x03"):
        op = rom[o + 3]
        if op & 0xC0 not in ops:
            continue
        b, c = cpu_of(o)
        rows.append({"op": ops[op & 0xC0], "bit": (op >> 3) & 7, "bank": b, "cpu": h(c), "rom_offset": h(o, 5), "region": region_of(b, c),
                     "ix_is_player": b in PLAYER_CTX_BANKS or region_of(b, c) != "other"})
    out["ix3_bit_ops"] = rows
    out["ix3_bit1_player_writers"] = [r for r in rows if r["bit"] == 1 and r["op"] in ("SET", "RES") and r["ix_is_player"]]
    out["d503_bit1_hl_writers"] = [{"cpu": "0x4B22", "effect": "SET 1 (HL=$D503) with SET 7: invincibility monitor pickup"},
                                   {"cpu": "0x4C7D", "effect": "SET 1: state $17 carried-by-object position copy $4C56"},
                                   {"cpu": "0x99D8", "effect": "SET 1 and SET 7: type $05 aura object (state $15 / $1A)"}]
    return out


# --------------------------------------------------------------------------- #
# controlled lab
# --------------------------------------------------------------------------- #
def lab(rom: bytes):
    """Fresh oracle lab. The sound-request routine $062D is stubbed as RET in the oracle's RAM copy only (it polls hardware)."""
    si = _load("spring_interaction")
    L = si.Lab(rom)
    L.m[0x062D] = 0xC9
    return si, L


SETTERS = [
    (0x45B3, "stand_state_1"), (0x45CE, "land_state_5"), (0x45ED, "jump_state_0A"), (0x463C, "fall_state_0E"), (0x4663, "state_14"),
    (0x4680, "state_1D"), (0x4699, "jump_no_impulse_state_0A"), (0x46B0, "state_3"), (0x46BB, "state_4"), (0x46CE, "state_15_peel_out_charge"),
    (0x46E2, "state_1A_peel_out_run"), (0x4701, "state_0F_spin_dash_charge"), (0x4719, "state_10_spin_dash_roll"), (0x473C, "state_18"),
    (0x47A9, "state_6"), (0x47B6, "state_7"), (0x47C9, "state_8"), (0x47DC, "roll_state_9"), (0x47FB, "ramp_state_1B"),
    (0x480C, "upright_spring_state_0B"), (0x482D, "diagonal_spring_state_1C"), (0x4849, "horizontal_spring_right_state_9"),
    (0x4868, "horizontal_spring_left_state_9"), (0x4942, "hurt_state_1E"), (0x4984, "death_state_1F"), (0x4892, "act_clear_state_20"),
]


def setter_effects(rom: bytes) -> dict:
    """Each setter run against all 256 $D503 values: exact output map of bits 0,1,6,7, requested state, gates."""
    si, L = lab(rom)
    m = L.m
    rows = []
    for addr, name in SETTERS:
        for cur in ((5, 0x0A) if addr == 0x463C else (5,)):
            maps, reqs, errs = {}, set(), 0
            for f3 in range(256):
                L.player(1000, 500, vx=0x200, vy=0, floor=1, cur=cur, req=cur, f3=f3)
                m[0xD3C0] = 0
                m[0xD443] = 0
                m[0xD29A] = 0x10
                m[0xD503] = f3
                try:
                    if addr in (0x480C, 0x482D, 0x4849, 0x4868):
                        L.call_hl(addr, 0xF880 if addr != 0x4849 else 0x0600)
                    else:
                        L.call_ix(addr, 0xD500)
                except Exception:
                    errs += 1
                    continue
                maps[f3] = m[0xD503]
                reqs.add(m[0xD502])
            if not maps:
                rows.append({"setter": h(addr), "name": name, "error": "did not return in the oracle"})
                continue

            def eff(bit):
                outs = {(f >> bit & 1, o >> bit & 1) for f, o in maps.items()}
                if outs <= {(0, 0), (1, 1)}:
                    return "kept"
                if all(o >> bit & 1 for o in maps.values()):
                    return "set"
                if not any(o >> bit & 1 for o in maps.values()):
                    return "cleared"
                return "conditional"
            # bit 1 as a function of (input bit 0, input bit 1)
            b1 = {}
            for f, o in maps.items():
                b1.setdefault(f"in0={f & 1},in1={f >> 1 & 1}", set()).add(o >> 1 & 1)
            rows.append({"setter": h(addr), "name": name, "current_state_when_called": h(cur, 2),
                         "requested_state_results": sorted(h(r, 2) for r in reqs),
                         "bit0_airborne": eff(0), "bit1_attack": eff(1), "bit6_hurt": eff(6), "bit7_invulnerable": eff(7),
                         "bit1_out_by_input_bits01": {k: sorted(v) for k, v in sorted(b1.items())}, "inputs_swept": len(maps)})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "cases": sum(r.get("inputs_swept", 0) for r in rows), "setters": rows,
            "reading": "bit1_attack 'set' = forced 1; 'cleared' = forced 0; 'kept' = untouched. State requests only change $D502; $D501 (the current state that selects the animation frame) switches at the START of the next player update ($64FA), while the bit change is immediate."}


def power_up(rom: bytes) -> dict:
    """$D532: writers, reward branches, timer, expiry, damage immunity."""
    si, L = lab(rom)
    m, o = L.m, L.o
    res = {}
    for name, mask in (("bit2_param3", 0x04), ("bit3_param4", 0x08), ("bit5_param6", 0x20), ("bit4_param5", 0x10)):
        L.player(1000, 500, floor=1, cur=5, req=5, f3=0)
        m[0xD532] = 0
        m[0xD3A3] = mask
        m[0xD500] = 1
        m[0xD297] = 0
        o.word(0xD44C, 0)
        L.call_ix(0x4AA3, 0xD500)
        res[name] = {"mask": h(mask, 2), "D532_after": m[0xD532], "D44C_timer_after": o.word(0xD44C), "D503_after": m[0xD503], "requested_state_after": m[0xD502],
                     "D3A3_after": m[0xD3A3], "D3C4_after": m[0xD3C4]}
    # timer / expiry
    exp = {}
    for code in (0, 3, 4, 6):
        L.player(1000, 500, floor=1, cur=5, req=5, f3=0)
        m[0xD532] = code
        o.word(0xD44C, 1)
        m[0xD3A3] = 0
        o.word(0xD373, 0x0400)
        L.call_ix(0x4A74, 0xD500)
        exp[h(code, 2)] = {"D532_after_timer_reaches_0": m[0xD532], "D44C_after": o.word(0xD44C), "speed_cap_D373_after": h(o.word(0xD373))}
    res["timer_expiry_from_1"] = exp
    # immunity in the damage handler
    imm = {}
    for code in (0, 3, 4, 6):
        L.player(1000, 500, floor=1, cur=5, req=5, f3=0)
        m[0xD532] = code
        m[0xD3B0] = 0xFF
        m[0xD29A] = 0x10
        L.call_ix(0x48BC, 0xD500)
        imm[h(code, 2)] = {"requested_state": h(m[0xD502], 2), "D3B0_after": m[0xD3B0], "rings_after": m[0xD29A]}
    res["damage_request_FF_with_D532"] = imm
    return {"evidence": "CONTROLLED ROUTINE RESULT", "branches": res}


# --------------------------------------------------------------------------- #
# 2. contact and attack gates (controlled)
# --------------------------------------------------------------------------- #
SLOT = 0xD700            # badnik slot 9 -> player D520 receives slot id 9
BANK_T27, BANK_T21, BANK_T10 = 30, 12, 12


def _clear_obj(m, base=SLOT):
    for a in range(base, base + 0x40):
        m[a] = 0


def _player_at(L, f3, d532, x=500, y=500, vx=0, vy=0, cur=5, req=5, rings=0x10):
    L.player(x, y, vx=vx, vy=vy, floor=0, cur=cur, req=req, f3=f3)
    m = L.m
    m[0xD532] = d532
    m[0xD52C], m[0xD52D] = 8, 24
    m[0xD3B0] = 0
    m[0xD520] = 0
    m[0xD521] = 0
    m[0xD29A] = rings
    m[0xD3B1] = 0
    m[0xD29D] = m[0xD29E] = m[0xD29F] = 0


def gate_5f3d(rom: bytes) -> dict:
    """Generic defeat gate $5F3D: all 256 $D503 values x $D532 0..8 x object contact nibble 0/1."""
    si, L = lab(rom)
    m = L.m
    conv = {}
    mism = 0
    for d532 in range(9):
        by_bit1 = {}
        for f3 in range(256):
            for contact in (0, 1):
                _clear_obj(m)
                m[SLOT], m[SLOT + 0x21] = 0x27, contact
                m[0xD503], m[0xD532] = f3, d532
                L.call_ix(0x5F3D, SLOT, 1)
                got = m[SLOT] == 0x0F
                want = contact != 0 and (d532 == 6 or bool(f3 & 2))
                mism += got != want
                if contact:
                    by_bit1.setdefault(f3 >> 1 & 1, set()).add(got)
        conv[h(d532, 2)] = {"converts_when_bit1_clear": sorted(by_bit1[0]), "converts_when_bit1_set": sorted(by_bit1[1])}
    # the converted slot
    _clear_obj(m)
    m[SLOT], m[SLOT + 0x21], m[0xD503] = 0x27, 1, 2
    L.call_ix(0x5F3D, SLOT, 1)
    return {"evidence": "CONTROLLED ROUTINE RESULT", "cases": 9 * 256 * 2, "model_mismatches": mism,
            "rule": "converts iff (object +$21 & 15) != 0 and ($D532 == 6 or $D503 bit 1); every other $D503 bit is irrelevant",
            "by_d532": conv, "converted_slot_type": h(m[SLOT], 2), "converted_slot_p3f_during_call": "0x80 then cleared"}


def contact_handler_48bc(rom: bytes) -> dict:
    """The player's own contact/damage handler: D520 (contact slot id) / D3B0 (damage request) x D503 x D532 x D521 hi nibble."""
    si, L = lab(rom)
    m, o = L.m, L.o
    table = {}
    n = 0
    for f3 in range(16):
        f3v = (f3 & 3) | ((f3 >> 2 & 1) << 6) | ((f3 >> 3 & 1) << 7)
        for d532 in (0, 3, 4, 6):
            for d520 in (0, 9):
                for d3b0 in (0, 0xFF):
                    for hi in (0x00, 0x10, 0x20, 0x30):
                        for rings in (0, 0x10):
                            for cur in (5, 9, 0x11):
                                _player_at(L, f3v, d532, vy=0x0100, cur=cur, req=cur, rings=rings)
                                m[0xD520], m[0xD3B0], m[0xD521] = d520, d3b0, hi
                                L.call_ix(0x48BC, 0xD500)
                                n += 1
                                vy, req = s16(o.word(0xD518)), m[0xD502]
                                if req in (0x1E, 0x1F) and req != cur:
                                    out = "death" if req == 0x1F else "hurt"
                                elif vy == -0x300:
                                    out = "rebound_up_-3.0"
                                elif vy == 0x80:
                                    out = "rebound_down_+0.5"
                                elif d520 == 0 and d3b0 == 0:
                                    out = "none"
                                else:
                                    out = "contact_ignored"
                                key = (f3v, d532, d520, d3b0, hi, rings, cur)
                                table[key] = out
    mism = 0
    for (f3v, d532, d520, d3b0, hi, rings, cur), out in table.items():
        mism += model_48bc(f3v, d532, d520, d3b0, hi, rings, cur) != out
    return {"evidence": "CONTROLLED ROUTINE RESULT", "cases": n, "model_mismatches": mism,
            "inputs": "D503 bits 0,1,6,7 (16 combos), D532 in {0,3,4,6}, D520 in {0,9}, D3B0 in {0,FF}, D521 high nibble in {0..3}, rings {0,>0}, current state in {5,9,$11}",
            "rules_in_priority_order": [
                "D503 bit 7 set -> invulnerable path ($49F7): no contact or damage processing",
                "D503 bit 6 set -> hurt/dying path ($4A2E): D520 cleared, nothing else",
                "D532 == 6 -> D3B0 and D520 cleared, no damage, no rebound",
                "D3B0 != 0 -> damage whatever D503 bit 1 is (state $11: clears D532, hurt without ring test; else rings == 0 -> death $1F, else scatter rings + hurt $1E)",
                "D520 == 0 -> nothing",
                "D520 != 0 and D503 bit 1 set (attacking): D521 bit 4 -> vy := +0.5 unless current state is 9; else D521 bit 5 -> vy := -3.0 (floor flag cleared, airborne set); else nothing; D520 cleared",
                "D520 != 0 and D503 bit 1 clear -> damage exactly as for D3B0 != 0"],
            "model_function": "model_48bc"}


def model_48bc(f3, d532, d520, d3b0, hi, rings, cur):
    if f3 & 0x80 or f3 & 0x40 or d532 == 6:
        return "contact_ignored" if d520 or d3b0 else "none"
    hurt = "hurt" if cur == 0x11 or rings else "death"
    if d3b0:
        return hurt
    if not d520:
        return "none"
    if f3 & 2:
        if hi & 0x10:
            return "contact_ignored" if cur == 9 else "rebound_down_+0.5"
        if hi & 0x20:
            return "rebound_up_-3.0"
        return "contact_ignored"
    return hurt


CONDITIONS = [("standing_or_walking", 0x00, 0), ("airborne_only_bit0", 0x01, 0), ("attack_bit1_grounded", 0x02, 0), ("jump_bits01", 0x03, 0),
              ("invincible_D532_6", 0x00, 6), ("invincible_and_bit1", 0x02, 6)]


def _setup_t27(L, dx, dy, f3, d532):
    m, o = L.m, L.o
    _clear_obj(m)
    m[SLOT] = 0x27
    m[SLOT + 4] = 0x10
    m[SLOT + 0x3E] = 25
    o.word(SLOT + 0x11, 500)
    o.word(SLOT + 0x14, 500)
    o.word(SLOT + 0x16, 0xFD80)
    m[SLOT + 0x2C], m[SLOT + 0x2D] = 9, 14
    _player_at(L, f3, d532, x=500 + dx, y=500 + dy)


def sweep_type27(rom: bytes) -> dict:
    """Type $27 state-1 callback ($89AC) over a dx/dy grid and the attack conditions."""
    si, L = lab(rom)
    m, o = L.m, L.o
    n = mism = 0
    overlap = set()
    hi_cells = {}
    per_cond = {}
    for name, f3, d532 in CONDITIONS:
        conv = damage_request = 0
        for dy in range(-34, 40):
            for dx in range(-24, 25):
                _setup_t27(L, dx, dy, f3, d532)
                L.call_ix(0x89AC, SLOT, BANK_T27)
                n += 1
                ov = (m[0xD721] & 15) != 0 or m[SLOT] == 0x0F
                if name == "standing_or_walking":
                    overlap.add((dx, dy)) if ov else None
                    if ov:
                        hi_cells.setdefault(m[0xD521] >> 4, []).append((dx, dy))
                got = m[SLOT] == 0x0F
                want = (dx, dy) in overlap and (d532 == 6 or bool(f3 & 2))
                mism += got != want
                conv += got
                damage_request += m[0xD3B0] != 0
        per_cond[name] = {"cells_converted": conv, "D3B0_ever_set_by_callback": damage_request}
    xs = [c[0] for c in overlap]
    ys = [c[1] for c in overlap]
    regions = {}
    for hv, cells in sorted(hi_cells.items()):
        regions[h(hv, 1)] = {"cells": len(cells), "dx_range": [min(c[0] for c in cells), max(c[0] for c in cells)], "dy_range": [min(c[1] for c in cells), max(c[1] for c in cells)]}
    return {"evidence": "CONTROLLED ROUTINE RESULT", "callback": "0x89AC (bank $1E state 1)", "cases": n, "model_mismatches": mism,
            "overlap_box_player_minus_object": {"dx": [min(xs), max(xs)], "dy": [min(ys), max(ys)], "cells": len(overlap)},
            "D521_high_nibble_regions_after_callback": regions,
            "per_condition": per_cond,
            "rule": "overlap && ($D532 == 6 || $D503 bit 1) -> $5F3D converts to $0F; overlap otherwise -> callback returns (NO $D3B0 request) but $6328 has already set player D520 (object +3 bit 7 clear) so $48BC hurts a non-attacking player on the next player update"}


def sweep_type21(rom: bytes) -> dict:
    """Type $21 contact tail ($B2AF) over dx/dy and the attack conditions."""
    si, L = lab(rom)
    m, o = L.m, L.o
    n = mism = 0
    per = {}
    for name, f3, d532 in CONDITIONS:
        stomp = conv = dmg = 0
        stomp_cells, conv_cells, dmg_cells = [], [], []
        for dy in range(-40, 36):
            for dx in range(-26, 27):
                _clear_obj(m)
                m[SLOT] = 0x21
                o.word(SLOT + 0x11, 500)
                o.word(SLOT + 0x14, 500)
                m[SLOT + 0x2C], m[SLOT + 0x2D] = 0x0B, 0x1A
                _player_at(L, f3, d532, x=500 + dx, y=500 + dy)
                o.word(0xD518, 0)
                m[0xD448] = 0x55
                L.call_ix(0xB2AF, SLOT, BANK_T21)
                n += 1
                is_stomp = m[0xD502] == 0x0B and o.word(0xD518) == 0xF940
                is_conv = m[SLOT] == 0x0F
                is_dmg = m[0xD3B0] == 0xFF
                overlap_model = abs(dx) <= 19 and -26 <= dy <= 24
                want = "none"
                if overlap_model:
                    want = "stomp" if dy <= -4 else ("convert" if (d532 == 6 or f3 & 2) else "damage_request")
                got = "stomp" if is_stomp else ("convert" if is_conv else ("damage_request" if is_dmg else "none"))
                mism += got != want
                if got == "stomp":
                    stomp += 1
                    stomp_cells.append((dx, dy))
                elif got == "convert":
                    conv += 1
                    conv_cells.append((dx, dy))
                elif got == "damage_request":
                    dmg += 1
                    dmg_cells.append((dx, dy))

        def bb(c):
            return {"cells": len(c), "dx": [min(x for x, _ in c), max(x for x, _ in c)], "dy": [min(y for _, y in c), max(y for _, y in c)]} if c else {"cells": 0}
        per[name] = {"stomp_bounce": bb(stomp_cells), "converted": bb(conv_cells), "damage_request_D3B0": bb(dmg_cells)}
    return {"evidence": "CONTROLLED ROUTINE RESULT", "callback": "0xB2AF (bank $0C)", "cases": n, "model_mismatches": mism, "per_condition": per,
            "rule": "overlap (|dx| <= 19, -26 <= dy <= 24) -> if player Y <= objectY - 4: stomp bounce (vy $F940, request $0B, $D448 $FF, attack bit cleared by $480C) REGARDLESS of attack bit/D532 and the badnik survives; else $D503 bit 1 or $D532 == 6 -> convert; else D3B0 := $FF. Object +3 bit 7 is set at init, so $6328 never sets D520 for type $21",
            "stomp_does_not_convert": True}


def sweep_monitor(rom: bytes) -> dict:
    """Type $10 monitor ($A16C): attack bit is mandatory; D532 == 6 alone does not break it."""
    t10 = _load("thz1_object_10")
    n = 0
    per = {}
    for name, f3, d532 in CONDITIONS:
        classes = {}
        for vy in (0x0100, 0xFF00, 0):
            for dy in range(-30, 31, 2):
                for dx in range(-22, 23, 2):
                    orc = t10._contact_oracle(rom, parameter=2, delta_x=dx, delta_y=dy, player_flags=f3, player_y_velocity=vy, power_up=d532)
                    orc.call(0xA16C)
                    n += 1
                    broke = orc.mem[0xD3A3] != 0
                    vyp = s16(orc.word(0xD518))
                    cls = "no_effect"
                    if broke:
                        cls = "break_rebound_-4.0" if vyp == -0x400 else "break"
                    elif orc.mem[0xD702] == 3:
                        cls = "bottom_hit_player_vy_+2.0_object_up"
                    classes[cls] = classes.get(cls, 0) + 1
        per[name] = dict(sorted(classes.items()))
    return {"evidence": "CONTROLLED ROUTINE RESULT", "callback": "0xA16C (bank $0C)", "cases": n, "per_condition": per,
            "rule": "break/bounce/bottom-hit all require $D503 bit 1 (the very first test after the $5FA0 projection); $D532 == 6 alone does nothing. Requested player states $0F/$10/$15/$1A reject a top break; a non-negative, non-zero player Y speed is required; state 9 breaks without a rebound; the monitor sets object +3 bit 7 so the generic D520 damage path never sees it"}



# --------------------------------------------------------------------------- #
# 3. emulated original frames
# --------------------------------------------------------------------------- #
def _emu():
    si = _load("spring_interaction")
    from sms_frame_harness import BTN_RIGHT, BTN_LEFT, BTN_DOWN, BTN_UP, BTN_1
    return si, dict(RIGHT=BTN_RIGHT, LEFT=BTN_LEFT, DOWN=BTN_DOWN, UP=BTN_UP, B1=BTN_1)


def _snapshot(s):
    m = s.mem
    return {"cur": m[0xD501], "req": m[0xD502], "f3": m[0xD503], "d532": m[0xD532], "x": s.u16(0xD511), "y": s.u16(0xD514),
            "vx": s16(s.u16(0xD516)), "vy": s16(s.u16(0xD518)), "d520": m[0xD520], "d3b0": m[0xD3B0], "d3b1": m[0xD3B1], "rings": m[0xD29A]}


def run_objects_view(s, frames, padf):
    """Per frame, snapshot at $5DD1 (start of the object phase): what a badnik callback of that frame sees."""
    tr = []
    s.add_pc_hook(0x5DD1, lambda m: tr.append(_snapshot(m)))
    for f in range(frames):
        s.pad = padf(f)
        s.run_frame()
    return tr


# states whose entering setter leaves $D503 bit 1 set ($45ED/$4699 -> $0A, $4701 -> $0F, $4719 -> $10, $47DC/$4849/$4868 -> 9, $47FB -> $1B, $482D -> $1C)
ATTACK_SET_STATES = {0x09, 0x0A, 0x0F, 0x10, 0x1B, 0x1C}


def legacy_attack(t):
    """The POC legacy approximation: airborne OR rolling bit (move & 3), not state $11."""
    return t["cur"] != 0x11 and (t["f3"] & 3) != 0


def canonical_attack(t):
    return bool(t["f3"] & 2) or t["d532"] == 6


def segments(tr, limit=None):
    out, prev = [], None
    for i, t in enumerate(tr[:limit]):
        key = (t["cur"], t["req"], t["f3"], t["d532"])
        if key != prev:
            out.append({"first_update": i, "state": h(t["cur"], 2), "requested": h(t["req"], 2), "D503": h(t["f3"], 2), "D532": t["d532"], "updates": 1,
                        "x": t["x"], "y": t["y"], "vy_first": t["vy"], "vy_last": t["vy"], "badnik_sees_attack": canonical_attack(t), "legacy_playerJump": legacy_attack(t)})
            prev = key
        else:
            out[-1]["updates"] += 1
            out[-1]["vy_last"] = t["vy"]
    return out


def natural_timelines(rom: bytes) -> dict:
    si, B = _emu()
    R_, L_, D_, U_, B1 = B["RIGHT"], B["LEFT"], B["DOWN"], B["UP"], B["B1"]
    cases = [
        ("stand", 0, 142, 654, lambda f: 0, 30),
        ("walk", 0, 142, 654, lambda f: R_, 50),
        ("run", 0, 142, 654, lambda f: R_, 130),
        ("jump_tap_from_run", 0, 142, 654, lambda f: R_ | (B1 if 70 <= f < 73 else 0), 130),
        ("jump_hold_from_run", 0, 142, 654, lambda f: R_ | (B1 if 70 <= f < 90 else 0), 150),
        ("roll_from_run", 0, 142, 654, lambda f: R_ | (D_ if 70 <= f < 78 else 0), 140),
        ("spin_dash_charge_and_release", 0, 142, 654, lambda f: (D_ if 5 <= f < 70 else 0) | (B1 if f in (15, 16, 17, 30, 31, 32) else 0), 120),
        ("peel_out_charge_and_release", 0, 142, 654, lambda f: (U_ if 5 <= f < 70 else 0) | (B1 if f in (15, 16, 17) else 0), 260),
        ("walk_off_ledge", 0, 980, 654, lambda f: R_, 110),
        ("roll_off_ledge", 0, 900, 654, lambda f: R_ | (D_ if 20 <= f < 28 else 0), 140),
        ("ramp_curve_1B", 0, 142, 654, lambda f: R_, 200),
        ("upright_spring_type26_strong_(688,864)", 0, 688, 846, lambda f: 0, 130),
        ("upright_spring_type26_weak_(1912,864)", 0, 1912, 846, lambda f: 0, 80),
        ("terrain_upright_spring_(928,640)", 0, 944, 596, lambda f: 0, 130),
        ("terrain_diagonal_spring_right_(2464,256)", 0, 2470, 222, lambda f: 0, 130),
        ("terrain_horizontal_spring_run_left_(3200,832)", 0, 3262, 790, lambda f: L_, 100),
        ("jump_into_terrain_upright_spring", 0, 600, 600, lambda f: R_ | (B1 if 60 <= f < 61 else 0), 150),
    ]
    rows = []
    n_updates = 0
    legacy_fp = canonical_total = legacy_total = 0
    fp_by_state = {}
    disagree = {}
    for name, act, x, y, padf, frames in cases:
        s = si._boot(rom, act)
        si._place(s, x, y, vy=0x0100)
        tr = run_objects_view(s, frames, padf)
        n_updates += len(tr)
        for t in tr:
            lg, cn = legacy_attack(t), canonical_attack(t)
            legacy_total += lg
            canonical_total += cn
            if (t["cur"] in ATTACK_SET_STATES) != bool(t["f3"] & 2):
                k = f"current_state {h(t['cur'], 2)} requested {h(t['req'], 2)} D503 {h(t['f3'], 2)}"
                disagree[k] = disagree.get(k, 0) + 1
            if lg and not cn:
                legacy_fp += 1
                fp_by_state[h(t["cur"], 2)] = fp_by_state.get(h(t["cur"], 2), 0) + 1
        rows.append({"case": name, "act": act, "start": [x, y], "updates": len(tr), "segments": segments(tr, 200)})
    return {"evidence": "EMULATED ORIGINAL FRAME",
            "method": "THZ1 booted in tools/sms_frame_harness.py, Sonic teleported with the camera; a PC hook at $5DD1 (start of the object phase) records the player's $D501/$D502/$D503/$D532 that every badnik callback of that frame sees",
            "cases": rows, "updates_recorded": n_updates,
            "legacy_vs_canonical": {"updates_legacy_playerJump_true": legacy_total, "updates_canonical_attack_true": canonical_total,
                                    "updates_legacy_true_but_canonical_false": legacy_fp, "by_state_of_those_updates": dict(sorted(fp_by_state.items()))},
            "state_vs_attack_bit_disagreement_updates": {
                "attack_set_states": sorted(h(x, 2) for x in ATTACK_SET_STATES),
                "meaning": "updates where $D501 (the state that selects the animation script/frame in that update) is not the state whose own setter normally leaves the attack bit that way; the bit changes in the callback of one update, $D501 follows at the start of the next",
                "counts": dict(sorted(disagree.items()))}}


def _find_obj(s, types):
    for i in range(19):
        a = 0xD540 + 0x40 * i
        if s.mem[a] in types:
            return a
    return None


def _boot_with(si, rom, act, typ, near):
    s = si._boot(rom, act)
    si._place(s, near[0], near[1])
    for _ in range(4):
        s.pad = 0
        s.run_frame()
    return s, _find_obj(s, (typ,))


CONTACT_SPECS = {
    "type27": {"typ": 0x27, "act": 0, "near": (2288, 700), "poses": [
        ("normal_jump_falling_onto_it", 0x0A, 3, -30, 0, 0, 0x300, 0), ("normal_jump_ascending_from_below", 0x0A, 3, 22, 0, 0, -0x200, 0),
        ("rolling_from_the_side", 9, 2, 0, -22, 0x200, 0, 0), ("upright_spring_fall_state_0B", 0x0B, 1, -30, 0, 0, 0x300, 0),
        ("falling_state_0E_after_apex_or_ledge", 0x0E, 1, -30, 0, 0, 0x300, 0), ("diagonal_spring_state_1C", 0x1C, 3, -30, 0, 0, 0x300, 0),
        ("walking_from_the_side", 5, 0, 0, -22, 0x200, 0, 0), ("invincible_falling_state_0E", 0x0E, 1, -30, 0, 0, 0x300, 6),
        ("invincible_walking_from_the_side", 5, 0, 0, -22, 0x200, 0, 6)]},
    "type21": {"typ": 0x21, "act": 0, "near": (1248, 800), "poses": [
        ("jump_falling_onto_top", 0x0A, 3, -30, 0, 0, 0x300, 0), ("falling_state_0E_onto_top", 0x0E, 1, -30, 0, 0, 0x300, 0),
        ("rolling_from_the_side", 9, 2, 0, -24, 0x300, 0, 0), ("walking_from_the_side", 5, 0, 0, -24, 0x300, 0, 0),
        ("invincible_walking_from_the_side", 5, 0, 0, -24, 0x300, 0, 6)]},
}


def contact_trials(rom: bytes) -> dict:
    """Forced-pose trials in the whole original game: the pose is written, everything after is the original code."""
    si, _ = _emu()
    out = {}
    for key, spec in CONTACT_SPECS.items():
        rows = []
        for name, cur, f3, dy, dx, vx, vy, d532 in spec["poses"]:
            s, a = _boot_with(si, rom, spec["act"], spec["typ"], spec["near"])
            ox, oy = s.u16(a + 0x11), s.u16(a + 0x14)
            s.w16(0xD511, ox + dx)
            s.w16(0xD514, oy + dy)
            s.w16(0xD516, vx & 0xFFFF)
            s.w16(0xD518, vy & 0xFFFF)
            s.mem[0xD501] = s.mem[0xD502] = cur
            s.mem[0xD503], s.mem[0xD532], s.mem[0xD522] = f3, d532, 0
            s.mem[0xD29A], s.mem[0xD3B0], s.mem[0xD520] = 0x10, 0, 0
            tl = []
            for i in range(12):
                s.pad = 0
                s.run_frame()
                tl.append({"u": i, "state": s.mem[0xD501], "req": s.mem[0xD502], "f3": s.mem[0xD503], "vy": s16(s.u16(0xD518)), "rings": s.mem[0xD29A],
                           "D520": s.mem[0xD520], "D3B0": s.mem[0xD3B0], "object_type": s.mem[a]})
            conv = next((r["u"] for r in tl if r["object_type"] == 0x0F), None)
            hurt = next((r["u"] for r in tl if r["req"] in (0x1E, 0x1F)), None)
            bounce = next((r for r in tl if r["vy"] in (-0x300, -0x6C0) or (conv is not None and r["u"] > conv and r["vy"] == 0x80)), None)
            rows.append({"pose": name, "start_state": h(cur, 2), "start_D503": h(f3, 2), "start_D532": d532, "converted_at_update": conv,
                         "hurt_or_death_requested_at_update": hurt, "rings_after": tl[-1]["rings"], "rebound_vy_8_8": bounce["vy"] if bounce else None,
                         "rebound_update": bounce["u"] if bounce else None, "D503_after_12": h(tl[-1]["f3"], 2), "state_after_12": h(tl[-1]["state"], 2),
                         "first_updates": tl[:7]})
        out[key] = {"object_world_position_after_settle": [ox, oy], "trials": rows}
    return {"evidence": "EMULATED ORIGINAL FRAME (pose forced at update 0; ring counter $D29A forced to $10 so damage is not death)", **out}


def frame_event_order(rom: bytes) -> dict:
    """The order of the original routines inside one update that contains a contact (PC hooks)."""
    si, _ = _emu()
    s, a = _boot_with(si, rom, 0, 0x27, (2288, 700))
    ox, oy = s.u16(a + 0x11), s.u16(a + 0x14)
    s.w16(0xD511, ox)
    s.w16(0xD514, oy - 30)
    s.w16(0xD516, 0)
    s.w16(0xD518, 0x300)
    s.mem[0xD501] = s.mem[0xD502] = 0x0A
    s.mem[0xD503], s.mem[0xD532], s.mem[0xD29A] = 3, 0, 0x10
    names = {0x361D: "player update entry $361D", 0x64FA: "animation engine $64FA", 0x5E91: "callback dispatcher $5E91", 0x3FEF: "shared movement $3FEF",
             0x48BC: "contact/damage handler $48BC", 0x4A74: "power-up timer $4A74 (end of player update)", 0x5DD1: "object scheduler $5DD1",
             0x6328: "overlap $6328", 0x5F3D: "attack gate $5F3D", 0x5F54: "enemy conversion $5F54"}
    ev = []

    def mk(addr):
        def f(m):
            ev.append((addr, m.cpu.ix))
        return f
    for addr in names:
        s.add_pc_hook(addr, mk(addr))
    frames = []
    for i in range(8):
        ev.clear()
        s.pad = 0
        s.run_frame()
        seq = []
        for addr, ix in ev:
            if addr in (0x64FA, 0x5E91, 0x3FEF) and ix != 0xD500:
                continue
            tag = names[addr] + (" (player)" if addr in (0x64FA, 0x5E91, 0x3FEF) else "")
            if addr == 0x6328:
                tag += f" IX=${ix:04X}"
            if not seq or seq[-1] != tag:
                seq.append(tag)
        frames.append({"update": i, "order": seq, "object_type": s.mem[a], "D520": s.mem[0xD520], "player_vy": s16(s.u16(0xD518)), "D503": s.mem[0xD503]})
    contact = next(f for f in frames if f["object_type"] == 0x0F)
    return {"evidence": "EMULATED ORIGINAL FRAME", "contact_update": contact, "following_update": frames[contact["update"] + 1], "frames": frames}


# --------------------------------------------------------------------------- #
# 4. curated, evidence-labelled statements (each backed by a section above)
# --------------------------------------------------------------------------- #
def bit_model() -> dict:
    return {
        "evidence": "BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT (setter_effects, contact_handler_48bc)",
        "byte": "$D503 = player object +$03 (IX = $D500)",
        "bits": {
            "0": "airborne (set by every launch/jump/fall setter, cleared by landing $45CE, stand $45B3, state 6/7/8 setters, horizontal springs, roll $47DC)",
            "1": "ATTACK POSTURE: the only thing player-side contact ($48BC), $5F3D, type $21, the monitor, the moving spike side bump and the boss read. Not 'airborne', not 'rolling by sprite'",
            "2": "not referenced by player code", "3": "read by the animation engine ($6502) as a state-switch lock; no player code sets it",
            "4": "not referenced", "5": "not referenced",
            "6": "hurt/dying: $6328 returns before any contact (+$20/+$21 stay clear) and $48BC takes the $4A2E path; set by $4942, $3BF4/$3BFF; cleared by landing $45CE and at invulnerability end",
            "7": "invulnerable (post-hit blink, $D3B1 timer $78 / $0C): $6328 still reports contact but does not set the +$20 overlap flag, $48BC takes $49F7 (no damage); set by $4942, $4B24 (invincibility pickup), $8313 (state $1A entry), type $05 object"},
        "attack_posture_definition": "(D503 & 2) != 0, OR power-up D532 == 6; both tests exist at $48CA/$5F3D/$B2D5; the monitor, boss and moving-spike side bump test bit 1 only",
        "persistence": {
            "across_state_transitions": "bit 1 is only changed by the setters listed in setter_effects and by the three HL writers; every other state change (loop entry $3EAB/$3EE1/$3EF7, twist entry/exit $95EC/$978F, hurt $4942, death $4984, act-clear $4892, standing callbacks) leaves it as it was",
            "landing": "$45CE clears bits 0, 1, 6 and requests state 5 (it is requested in the callback; $D501 changes at the start of the next update)",
            "apex_and_fall": "the normal jump ($0A) never calls the fall setter ($463C returns when the current state is $0A): bit 1 stays set through ascent, apex and descent until landing. Spring apex ($0B/$1C) and every other fall ($463C from state != $0A: ledge, apex, state $11 end) CLEARS bit 1",
            "damage_and_death": "hurt $4942 and death $4984 do NOT clear bit 1 (they set bit 6, which disables contact); the next landing clears it",
            "walking_off_a_ledge": "$6C7C: fall setter $463C -> state $0E, bit 0 set, bit 1 cleared; when the current state is 9 (rolling): $4699 -> state $0A with bits 0 and 1 set (still attacking)"}}


def d532_model() -> dict:
    return {
        "evidence": "BYTE-VERIFIED ASSEMBLY (all 5 writers, 5 readers) + CONTROLLED ROUTINE RESULT (power_up)",
        "meaning": "player power-up selector: 0 none, 3 speed-up (X speed cap $0600 each update, timer $D44C := 900), 4 timer $12C (player type 1; sets state $11), 6 invincibility (timer 600, D503 |= $82 at pickup, stars = type $05 child)",
        "writers": {"$4AE8": ":= 4 (reward bit 3, only when $D500 == 1)", "$4B13": ":= 3 (reward bit 2)", "$4B3C": ":= 6 (reward bit 5; spawns type $05 aura when it was not already 6)",
                    "$4AA0": ":= 0 when the timer reaches 0 and the code is 4 or 6 (code 3 is NOT cleared here)", "$48FF": ":= 0 when damaged in state $11"},
        "readers": {"$48CA": "$48BC: == 6 -> D3B0 and D520 cleared, no damage, no rebound", "$4A74/$4A8F": "timer service", "$5F43": "$5F3D: == 6 -> convert regardless of D503",
                    "$B2DD": "type $21 tail: == 6 -> convert", "$998A (bank $0C)": "type $05 aura keeps D503 bit 7 set while == 6, else deletes itself",
                    "$98EC (bank $0C)": "type $04 speed trail: runs only while == 3"},
        "why_enemy_callbacks_treat_6_specially": "not an enemy-specific rule: 6 is the invincibility power-up. It substitutes for D503 bit 1 in the shared defeat gate $5F3D and in type $21, and makes $48BC ignore every contact; the monitor ($A17A) and the boss do not test it",
        "lifetime": "set by the monitor, 600 updates, cleared by $4A74 at timer 0; no other clear exists in player code (state-$11 damage clears 4); act start RAM clear is not traced here (UNRESOLVED for persistence across acts)",
        "poc_note": "global.powerInv is the right owner; 'playerSuper' has no ROM counterpart"}


def rebound_model() -> dict:
    return {
        "evidence": "CONTROLLED ROUTINE RESULT (contact_handler_48bc, sweep_type21, sweep_monitor) + EMULATED (contact_trials)",
        "enemy_defeat_by_type27": "the callback converts the badnik only; it writes nothing to the player. The player's own handler $48BC applies the rebound one update later from $D520 and the high nibble of $D521 (side of contact from $6328)",
        "type27_from_above_player_in_dy_-14..-1": {"vy": -768, "meaning": "$FD00 = -3.0", "rule": "$D521 bit 5; overwrites incoming Y speed (incoming speed does not matter); floor flag cleared, airborne set; requested state unchanged; D503 unchanged (attack bit persists); applied at the next player update inside $48BC"},
        "type27_from_below_player_in_dy_+7..+24": {"vy": 128, "meaning": "$0080 = +0.5", "rule": "$D521 bit 4; not applied when the current state is 9 (rolling); no state change"},
        "type27_from_the_side": "no rebound (D521 bits 6/7 only)",
        "type21_top": {"vy": -1728, "meaning": "$F940 = -6.75, request $0B, $D448 = $FF, bit 1 cleared by $480C, badnik NOT defeated, any attack posture or none", "condition": "overlap and playerY <= objectY - 4"},
        "type21_attack": "side/low contact with bit 1 or D532 == 6: defeated, no rebound (the object sets +3 bit 7 so D520 is never raised)",
        "monitor": {"from_above_moving_down": "vy := $FC00 (-4.0), no rebound if the current state is 9", "from_below": "vy := +2.0 ($0200), monitor rises", "needs": "D503 bit 1 (D532 == 6 alone does nothing)"},
        "poc_mismatch": "POC type $21 calls SCR_physics_jump_objects() after a defeat (some rebound); the ROM gives none for a side defeat"}


def non_attacking_contact() -> dict:
    return {
        "evidence": "CONTROLLED ROUTINE RESULT + EMULATED ORIGINAL FRAME (contact_trials: type $27 walking/falling hurts, rings 16 -> 0, $1E, D3B1 120)",
        "type27": "DAMAGES. The callback only returns, but $6328 raises D520 (object +3 bit 7 is clear) and $48BC hurts the non-attacking player on the NEXT player update (rings 0 -> death $1F). This CORRECTS the earlier reading 'ordinary contact requests no damage'; what is true is that the callback never writes D3B0",
        "type27_stall": "the callback returns before its movement/timer on every overlap update (stall is real)",
        "type21": "side/low contact writes D3B0 := $FF (damage). Top contact (playerY <= objectY - 4) is a stomp bounce, never damage",
        "type1b_moving_spike": "top contact writes D3B0 := $FF whatever bit 1 is (only D532 == 6 saves Sonic); side contact with bit 1 and the floor flag bumps Sonic to state 1 (docs/platform-spike-collision-audit.md)",
        "type28_platform_type26_type09": "no damage (they set bit 7 or use their own proximity test)",
        "invulnerability": "D503 bit 7 (set by hurt $4942, timer $D3B1 = $78): $48BC takes $49F7, no damage, no rebound; contact is still computed",
        "vertical_direction": "type $21 is the only badnik whose outcome depends on above/below ($B2B7 compare). Type $27's contact flag direction decides only the rebound, not damage"}


def badnik_census() -> dict:
    return {
        "evidence": "DECODED DATA (placement census) + CONTROLLED ROUTINE RESULT (sweeps) + EMULATED",
        "thz1": {"0x21": 6, "0x27": 3, "0x10_monitors": 5, "0x1B_moving_spikes": 4},
        "thz2": {"0x21": 5, "0x27": 4, "0x10_monitors": 5, "0x1B_moving_spikes": 0},
        "enemy_types": ["0x21", "0x27"],
        "no_other_enemy": "the census (data/rom-cache/levels/object-census.json) has no other THZ1/THZ2 type that converts to $0F: $09 ring, $10 monitor, $18 sign, $1B spike, $26 spring, $28 platform. THZ3 adds only boss $50",
        "types": {
            "0x21": {"collision_routine": "$B2AF -> $033B ($6328), tail $B2B2", "attack_test": "D532 == 6 or D503 bit 1, read at object-update time (after the player update of the same frame)",
                     "damage": "D3B0 := $FF", "defeat": "$5F54 conversion to $0F (+score)", "top_vs_side": "top (playerY <= objY-4) = stomp bounce BEFORE the attack test, badnik survives; side/low = attack/damage",
                     "bottom": "no separate case: dy -3..+24 is the 'low' branch", "reads_attack_before_or_after_movement": "after the player movement of that frame; the object moves (patrol) before the contact tail in the same callback",
                     "rebound_after_defeat": "none", "box": "|dx| <= 19, dy -26..+24"},
            "0x27": {"collision_routine": "$033B ($6328) at the start of every state callback, then $0323 ($5F3D) on overlap", "attack_test": "$5F3D: D532 == 6 or D503 bit 1 (same predicate as $21)",
                     "damage": "none from the callback; generic D520 -> $48BC damage on the next player update", "defeat": "$5F54", "top_vs_side": "no difference for the badnik; the rebound differs (above -3.0, below +0.5, side none)",
                     "contact_movement": "on overlap the callback returns before moving", "rebound_after_defeat": "-3.0 from above (next update), +0.5 from below, none from the side", "box": "|dx| <= 17, dy -14..+24"},
            "0x10": {"collision_routine": "$034D ($5FA0 -> $6328)", "attack_test": "D503 bit 1 only (D532 == 6 does not break it)", "damage": "none (solid, bit 7 set)", "defeat": "reward + type $0F (not an enemy)"},
            "0x1B": {"collision_routine": "$ACFD -> $033B", "attack_test": "side bump reads bit 1 + floor flag; top damage ignores it", "damage": "D3B0 := $FF on top contact"},
            "0x50_thz3": {"attack_test": "D503 bit 1 only", "damage": "D3B0 := $FF + 2-update cooldown", "note": "docs/object-50.md; D532 == 6 not tested"}},
        "shared_vs_per_object": "ONE shared player-side rule ($48BC: D532 == 6 immune; D3B0 damages regardless of attack; D520 + bit 1 -> rebound else damage) and ONE shared defeat gate ($5F3D, used by $27 only in THZ). $21, the monitor and the boss own their tests (each reads $D503 directly). The predicates agree for $27/$21 (bit 1 or D532 == 6) and differ for the monitor/boss (bit 1 only)"}


def poc_migration_table() -> dict:
    """Read-only inspection of POC 7799c345; classification only, no POC change."""
    rows = [
        ("SCR_chaos_adapter.gml:30", "global.playerJump = !state11 && (move & 3) != 0", "legacy definition; (move&3) includes airborne-without-attack ($0B,$0E)", "retire; split into chaosAttackPosture (bit 1) and airborne (bit 0)"),
        ("SCR_chaos_adapter.gml:35", "global.chaosAttackPosture = !state11 && (move & 2) != 0", "canonical bit; the state-$11 exclusion is not in the ROM predicate (bit 1 is simply cleared by $4775)", "KEEP as the canonical attack bit; consumers should add 'or powerInv (D532==6)' where the ROM does"),
        ("SCR_chaos_adapter.gml:31", "global.playerJumpSpring = next == 11 || next == 28", "physics-only (jump-spring gravity/control), not an attack predicate", "should remain as is (airborne/spring physics)"),
        ("SCR_chaos_adapter.gml:32", "global.playerSpinDash = next == 15", "state $0F only; the released roll $10 is covered by bit 1", "should use canonical attack posture (bit 1 already set in $0F/$10)"),
        ("SCR_chaos_adapter.gml:242 (SCR_chaos_block47_step)", "(move&2) || OBJ_player_char_spin || playerJump || playerSpinDash", "breakable block $47/$6AE3 requires bit 1 and excludes states $0F/$10/$15/$1A (docs/spring-interaction-audit.md)", "should use canonical attack posture + the four-state exclusion"),
        ("SCR_chaos_adapter.gml:310-311 (type21 top bounce)", "playerJump = true; playerJumpSpring = true", "the ROM clears bit 1 on the stomp ($480C): spring-flight is not attacking", "should set airborne + spring physics but NOT attack"),
        ("SCR_chaos_adapter.gml:425 (sample_damage)", "place_meeting(OBJ_badniks) && !playerJump && !playerSpinDash -> hazard damage", "generic contact damage keyed on the legacy predicate; ROM keys on D520 && !(bit1 || D532==6)", "should use canonical attack posture (+powerInv) and the ROM's rebound/ignore split"),
        ("OBJ_chaos_object_27/Step_0.gml:58", "OBJ_player_char_spin || playerJump || playerSpinDash || playerSuper || powerInv -> destroy", "THE parked observation: playerJump is true in $0B/$0E (upright spring fall, apex, ledge fall)", "should use canonical attack posture or powerInv (D532==6); drop playerSuper (no ROM counterpart)"),
        ("OBJ_chaos_object_27/Step_0.gml:62", "ordinary overlap: no damage, exit", "ROM: the callback requests no damage, but $6328 raises D520 and $48BC hurts a non-attacking player next update", "unresolved in POC: needs ROM-faithful contact damage + -3.0/+0.5 rebound after a defeat"),
        ("OBJ_chaos_object_21/Step_0.gml:73", "(!state11 && (spin || playerJump || playerSpinDash)) || playerSuper || powerInv", "type $21 tests D503 bit 1 or D532==6 only", "should use canonical attack posture or powerInv; the top-bounce branch is already ROM-ordered"),
        ("OBJ_chaos_object_21/Step_0.gml:80", "with (cp_p) SCR_physics_jump_objects() after defeat", "no player rebound in the ROM for a $21 side defeat", "should be removed (enemy-specific)"),
        ("OBJ_chaos_object_10/Step_0.gml:69", "!state11 && (spin || playerJump || playerSpinDash)", "monitor requires bit 1 ONLY; D532==6 alone does not break it", "should use canonical attack posture (not powerInv)"),
        ("SCR_badnik_death.gml / SCR_monitor_collisions.gml", "playerJump / playerSpinDash / Super / powerInv checks on legacy OBJ_badniks/OBJ_monitors (OBJ_badnik_1)", "legacy sample-engine objects, not canonical THZ objects", "should remain legacy (not part of the ROM-derived THZ set)"),
        ("SCR_physics_spring.gml:23-36", "global.playerJump = true on spring contact", "physics for the legacy spring; ROM: upright spring clears bit 1, diagonal sets it", "should set airborne; attack only for the diagonal ($1C)"),
        ("SCR_physics_speed.gml:6,74,97,107,126,135; OBJ_player_char/Step_0.gml:150-451", "playerJump gates ground friction/jump-physics", "airborne/physics predicate, not attack", "should use airborne status (bit 0) / state, remain as is"),
        ("SCR_physics_ramp.gml:8, SCR_physics_ramp_spin.gml:8; OBJ_chaos_controls/Step_0.gml:39", "playerJump == false gates", "airborne/physics/checkpoint predicate", "should use airborne status"),
        ("OBJ_player_char_spin Step_0/Step_2 (playerJump)", "legacy spin object", "legacy character object, not the chaosCore", "should remain legacy"),
    ]
    return {"evidence": "SOURCE READ of POC checkout 7799c3459f59781878574e5d805bb3df4baa057c (read-only; no POC file modified)",
            "poc_commit": POC_COMMIT,
            "classification_legend": ["canonical attack posture", "airborne status", "rolling status", "enemy-specific", "unresolved"],
            "rows": [{"location": a, "current": b, "rom_comparison": c, "migration": d} for a, b, c, d in rows]}


def thz3_dependency_census() -> dict:
    """Read-only census from the existing caches (levels/thz3, object-census, platform/spike, spring, ring audits)."""
    def load(rel):
        return json.loads((ROOT / "data" / "rom-cache" / rel).read_text(encoding="utf-8"))
    L = {a: load(f"levels/{a}/layout.json") for a in ("thz1", "thz2", "thz3")}
    use = {a: {b["block_id"]: b for b in L[a]["block_usage"]} for a in L}
    covered = set(use["thz1"]) | set(use["thz2"])
    thz3_blocks = sorted(use["thz3"])
    new = [b for b in thz3_blocks if b not in covered]
    objs = load("levels/thz3/objects.json")["records"]
    by_type = {}
    for r in objs:
        by_type.setdefault(r["type_id"], []).append([r["world_x"], r["world_y"], r["parameter"]])
    spring_blocks = {"upright": ["0x30", "0x31"], "horizontal": ["0x32", "0x33", "0x34", "0x35"], "diagonal": ["0x36", "0x37", "0x38", "0x39"]}
    present = {k: sorted(set(v) & set(thz3_blocks)) for k, v in spring_blocks.items()}
    rings = load("levels/thz3/rings.json")
    return {
        "evidence": "DECODED DATA (cached layouts/objects) + references to accepted research; no new ROM tracing",
        "terrain": {"blocks_used_in_thz3": len(thz3_blocks), "blocks_already_used_by_thz1_or_thz2": len(thz3_blocks) - len(new), "blocks_new_to_thz3": new,
                    "collision_surface_types_used": sorted({u["collision_surface_type"] for u in use["thz3"].values() if isinstance(u["collision_surface_type"], int)}),
                    "spring_blocks_present": present, "ring_blocks_present": sorted(set(thz3_blocks) & {"0x40", "0x41", "0x42", "0x43"}),
                    "spike_blocks_present": sorted(set(thz3_blocks) & {"0x3C", "0x3D"}), "terrain_ring_counts": rings["counts"],
                    "verdict": "every THZ3 terrain block is already exercised by the accepted THZ1/THZ2 populations: no new collision/terrain mechanism"},
        "objects_thz3": by_type,
        "object_dependencies": {
            "0x09": {"status": "researched and Windows accepted (strict <12 proximity)", "docs": "docs/object-09.md"},
            "0x26": {"status": "researched (strong x4 in THZ3: fixed, parameter 0)", "docs": "docs/spring-interaction-audit.md"},
            "0x10": {"status": "researched; parameter 1 (+10 rings) covered by docs/thz2-thz3-object-deltas.md; attack gate = bit 1 only (this audit)", "docs": "docs/object-10.md"},
            "0x1B": {"status": "researched for THZ1; THZ3 placement (752,128) outside the platform/spike audit's measured set but same routine ($ACFD)", "docs": "docs/platform-spike-collision-audit.md"},
            "0x50": {"status": "boss: full study exists; DEFERRABLE for ordinary traversal; attack gate = bit 1 only", "docs": "docs/object-50.md",
                     "unresolved_children": ["type $12", "type $34", "type $0A", "type $0F effect roles", "palette consumer $D494/$D495", "state $20 act-clear screen / next-level load"]}},
        "prerequisites_for_ordinary_traversal": ["canonical THZ3 layout/rings/objects import (levels/thz3)", "shared widescreen viewport/lifecycle adapter (accepted)", "type $26 strong springs, terrain springs, rings (accepted)", "type $10 reward 1 (new branch, trivial)",
                                                 "canonical attack posture migration (this audit) so the boss and monitors read bit 1", "type $1B at (752,128) (same routine as THZ1)"],
        "boss_only_deferrable": ["type $50 and children $12/$34/$0A", "camera lock / boss music / arena art selector $13 and palette $0C", "defeat -> state $20 -> act-clear screen (shared $18/$19/$20 chain does not apply: no sign in THZ3)"],
        "recommended_next_scope": "THZ3 foundation (layout, rings, springs, monitors, one $1B) immediately after the canonical attack-posture migration; hold the boss until its five follow-up objects and the act-clear screen are studied"}


def unresolved() -> list:
    return [
        "Super Peel-Out ($15/$1A): in an ordinary charge and release (36+ updates emulated) bit 1 stays CLEAR; the type $05 param-$FF aura that sets bits 1|7 is spawned only after a very long charge script (loop counter $D2); untested beyond that (peel-out is not in the POC)",
        "Loop states $0C/$0D/$13 and twist $22 are not reachable in THZ1/THZ2 natural runs; their bit-1 behaviour is BYTE-VERIFIED (no writers in the loop/twist code except the exit setters) but not emulated",
        "Act-clear state $20: setter leaves bit 1 untouched (controlled); not emulated end to end here",
        "Animation frame identity (is a given state's frame a ball?) was NOT established; the 'visually unrolled' discussion uses state numbers and the one-update state/bit lag only",
        "James's Windows observation could not be replayed (needs the POC build); the ROM-side mechanism that reproduces 'destroyed from above while apparently unrolled' is the POC's legacy playerJump predicate",
        "$D532 persistence across act changes (RAM clear not traced); code 3 is not cleared at timer expiry by $4A74 (other clear not found)",
        "Type $1B THZ3 placement (752,128) not measured",
    ]


def parked_observation() -> dict:
    return {
        "question": "type $27 destroyed from above while Sonic appears unrolled",
        "can_the_rom_do_it": {
            "visually_unrolled_with_bit1_set": "YES, for ONE update at jump start: the jump request ($45ED) sets bit 1 in the callback of update n while $D501 (the animation state) is still 5/6 until update n+1 (natural_timelines: state $06/$05 requested $0A with D503 $03). Also state $1C (diagonal spring) is attacking by design",
            "D532_6_while_unrolled": "YES while invincible (stars), any pose: the invincibility pickup sets bits 1|7 and D532 6 substitutes for bit 1",
            "upright_spring_or_falling_unrolled_and_destroys_bee": "NO: contact_trials show state $0B/$0E (D503 = 1) does NOT convert the bee and the bee hurts Sonic (rings 16 -> 0, $1E)",
            "enemy_specific_other_condition": "NO: $5F3D is the only gate; it reads bit 1 and D532 only"},
        "classification": "B (POC global.playerJump false positive) as the persistent cause: legacy playerJump = (move & 3) != 0 is true in $0B (upright spring), $0E (post-apex / ledge fall) which the ROM treats as NOT attacking; the single canonical one-update window (jump start) is C-class timing but is 1/60 s",
        "secondary": "D: POC type $27 ordinary overlap does not hurt; the ROM hurts through D520/$48BC and also rebounds an attacker (-3.0 above / +0.5 below)",
        "not_reproduced": "the Windows run itself (UNRESOLVED E for the exact trigger Sonic state; every ROM-possible state is classified above)"}


# --------------------------------------------------------------------------- #
# build / check
# --------------------------------------------------------------------------- #
def attack_matrix(setters: dict, timelines: dict) -> dict:
    by = {r["setter"]: r for r in setters["setters"] if "error" not in r}

    def b1(addr):
        r = by.get(h(addr))
        return r["bit1_attack"] if r else "n/a"
    rows = [
        ("standing", "$01", "$45B3 stand / $45CE land", b1(0x45B3), False, "standing callbacks write no bit 1"),
        ("walking", "$05", "$45CE land", b1(0x45CE), False, ""), ("running", "$06", "$47A9 state-6 setter", b1(0x47A9), False, ""),
        ("crouch", "$04", "$46BB", b1(0x46BB), False, ""), ("look-up", "$03", "$46B0", b1(0x46B0), False, ""),
        ("skid", "$07/$08", "$47B6/$47C9 (gated on bit 0 clear)", b1(0x47B6), False, "both setters return early while bit 0 is set (airborne); when they fire they clear bit 1"),
        ("ordinary jump ascending", "$0A", "$45ED", b1(0x45ED), True, "bit 1 set when the jump starts (needs bit 0 clear)"),
        ("jump apex", "$0A", "none: $0A never calls $463C", "kept", True, "no apex transition for the normal jump"),
        ("jump falling", "$0A", "none", "kept", True, ""),
        ("jump landing request", "$0A -> $05", "$45CE", b1(0x45CE), False, "cleared at the request; $D501 still $0A for one more update (ball state, not attacking)"),
        ("rolling", "$09", "$47DC / ramp contact $6A02", b1(0x47DC), True, ""),
        ("spin-dash charge", "$0F", "$4701", b1(0x4701), True, "attacking while charging"),
        ("spin-dash roll", "$10", "$4719 / terrain $7654", b1(0x4719), True, ""),
        ("peel-out charge", "$15", "$46CE", b1(0x46CE), False, "kept; aura object (bits 1|7) only after a very long charge"),
        ("peel-out run", "$1A", "$46E2", b1(0x46E2), False, "kept; bit 7 for 12 updates"),
        ("ramp launch", "$1B", "$47FB", b1(0x47FB), True, ""),
        ("upright spring", "$0B", "$480C", b1(0x480C), False, "bit 0 set, bit 1 cleared"),
        ("spring apex / ledge fall", "$0E", "$463C", b1(0x463C), False, "bit 0 set, bit 1 cleared"),
        ("diagonal spring", "$1C", "$482D", b1(0x482D), True, "attacking until the apex request $463C"),
        ("horizontal spring", "9", "$4849/$4868", b1(0x4849), True, "grounded roll"),
        ("loop", "$0C/$0D/$13", "entry $3EAB/$3EE1/$3EF7 (no D503 write)", "kept", "inherits", "exit: bit 1 -> state 9 else 6 ($3CAB); $0D launch -> $0A with bits 0|1"),
        ("twist", "$22", "entry/exit $95EC (no D503 write)", "kept", "inherits", "exit requests state 9 / $0A WITHOUT setting bit 1: ball state, possibly not attacking"),
        ("hurt", "$1E", "$4942", b1(0x4942), "ignored", "bit 1 kept but bit 6 disables all contact"),
        ("death", "$1F", "$4984", "kept", "ignored", "bit 6 set by the callbacks"),
        ("act clear", "$20", "$4892", b1(0x4892), "inherits", "no D503 write"),
        ("state $11", "$11", "$4775", b1(0x4775), False, ""),
        ("invincible (D532 6)", "any", "$4B1D pickup", "set", True, "stars aura keeps bit 7; D532 6 substitutes for bit 1"),
    ]
    return {"evidence": "CONTROLLED ROUTINE RESULT (setter column) + EMULATED (natural_timelines) + BYTE-VERIFIED (kept/inherits rows)",
            "columns": ["situation", "state", "set/clear by", "bit1_effect_of_setter", "badnik_sees_attacking", "note"],
            "rows": [list(r) for r in rows],
            "emulated_state_vs_bit_windows": timelines["state_vs_attack_bit_disagreement_updates"]["counts"]}


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    out = {"format": "player-attack-badnik/1", "machine_facing_label": "player_attack_badnik", "static_only": static_only, "rom_sha256": ROM_SHA256, "research_only": True, "poc_untouched": True, "evidence_classes": EVIDENCE,
           "routines": routine_table(rom), "sites": d503_sites(rom), "d503_model": bit_model(), "d532_model": d532_model(),
           "badnik_census": badnik_census(), "rebound_model": rebound_model(), "non_attacking_contact": non_attacking_contact(),
           "poc_consumers": poc_migration_table(), "thz3_dependency_census": thz3_dependency_census(), "unresolved": unresolved()}
    out["update_order"] = {"evidence": "BYTE-VERIFIED + EMULATED (frame_event_order)", "per_update": [
        "$361D player: $64FA animation engine (applies the PREVIOUS update's requested state to $D501, runs the script)", "$5E91 state callback -> $3FEF shared movement: input, X/Y integrate, terrain $690B, then $48BC (contact/damage handler) and the jump request $45ED",
        "$4A74 power-up timer (end of player update)", "$5DD1 object scheduler: each object's own callback: $6328 overlap (sets D520 / D521 / +$21), $5F3D/$B2B2 defeat gate, $5F54 conversion, D3B0 damage request",
        "next update: $48BC consumes D520/D3B0 after that update's movement"],
        "consequences": ["a badnik always sees the attack bit left by the player's callback of the SAME update (movement already applied), never the previous update's",
                         "a state requested in update n changes $D501 (animation frame) at the start of update n+1, but its D503 effect is immediate: the frame shown in update n can contradict the bit (jump start: unrolled frame + attack bit; landing: ball frame + no attack)",
                         "player rebound/damage caused by an object overlap in update n is applied in update n+1 AFTER that update's movement",
                         "object damage request D3B0 and contact D520 are consumed once per player update; D520 is cleared by the bounce path or the hurt path"]}
    if static_only:
        return out
    out["setter_effects"] = setter_effects(rom)
    out["power_up_controlled"] = power_up(rom)
    out["gate_5f3d"] = gate_5f3d(rom)
    out["contact_handler_48bc"] = contact_handler_48bc(rom)
    out["type27_sweep"] = sweep_type27(rom)
    out["type21_sweep"] = sweep_type21(rom)
    out["monitor_sweep"] = sweep_monitor(rom)
    out["natural_timelines"] = natural_timelines(rom)
    out["contact_trials"] = contact_trials(rom)
    out["frame_event_order"] = frame_event_order(rom)
    out["attack_matrix"] = attack_matrix(out["setter_effects"], out["natural_timelines"])
    out["parked_type27_observation"] = parked_observation()
    controlled = sum(out[k]["cases"] for k in ("setter_effects", "gate_5f3d", "contact_handler_48bc", "type27_sweep", "type21_sweep", "monitor_sweep"))
    out["counts"] = {"controlled_cases": controlled, "emulated_updates_recorded": out["natural_timelines"]["updates_recorded"],
                     "emulated_contact_trials": sum(len(out["contact_trials"][k]["trials"]) for k in ("type27", "type21")),
                     "model_mismatches": sum(out[k]["model_mismatches"] for k in ("gate_5f3d", "contact_handler_48bc", "type27_sweep", "type21_sweep"))}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--static-only", action="store_true")
    args = ap.parse_args()
    rom = Path(args.rom).read_bytes()
    result = build(rom, args.static_only)
    text = json.dumps(result, indent=1, sort_keys=True) + "\n"
    if args.check:
        have = OUTPUT.read_text(encoding="utf-8")
        if have != text:
            print("MISMATCH: cache differs from a fresh build")
            sys.exit(1)
        print("cache matches")
        return
    if not args.static_only:
        OUTPUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUTPUT} ({len(text)} bytes)")
    else:
        print(text[:500])


if __name__ == "__main__":
    main()

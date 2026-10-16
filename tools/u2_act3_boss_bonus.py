#!/usr/bin/env python3
"""U2-A: Act 3 boss completion and bonus-object tracing (Sonic Chaos SMS, Europe v1.2).

    python tools/u2_act3_boss_bonus.py ROM                 # regenerate data/u2/*.json
    python tools/u2_act3_boss_bonus.py ROM --check         # recompute everything and compare with the committed JSON
    python tools/u2_act3_boss_bonus.py ROM --only static   # static + controlled only (seconds)
    python tools/u2_act3_boss_bonus.py --validate          # no ROM: consistency of the committed JSON and the pure model

Evidence tiers (every record names its own):

* SOURCE      - bytes/regions/anchors read from the ROM and decoded tables (state tables, script ownership, the fixed bonus table, routine hashes).
* CONTROLLED  - original Z80 routines executed on kosarev/z80 (tools/oracle.py) with explicit RAM.
* EMULATED    - the unmodified ROM running whole fights, clears and results in the approximate SMS harness.  The six fights are driven by the
                existing, already accepted fixture harnesses (tools/thz3_boss_support.py, gpz51_fullgame.py, sez54_fullgame.py, mghz56_fullgame.py,
                aqz59_game.py, eez_boss_game.py): arena ARRIVAL placement plus *synthetic player placement/attack writes at update boundaries*.  Every boss,
                bonus, results and zone-clear routine is the unmodified ROM; no controller-only playthrough is claimed.  This module only OBSERVES them.
* FIXTURE     - every injected value (D293 bit, ring count, timer, character, emerald flags) is named in the record.
* POC SOURCE-READ - GameMaker source read read-only (G1-D `d9275fe`), never run, never proof of ROM behaviour.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
BASE_COMMIT = "1fb25857470f7c867d763c435a324befea751c12"
DATA = ROOT / "data" / "u2"
STATIC_JSON = DATA / "act3-boss-bonus-static.json"
CONTROLLED_JSON = DATA / "act3-boss-bonus-controlled.json"
OBS_JSON = DATA / "act3-boss-bonus-observed.json"
DOC = ROOT / "docs" / "u2-act3-boss-bonus.md"

BANK_BOSS = 0x1E     # object code of types >= $26 that matter here ($50..$62)
BANK_OBJ = 0x0C      # object code of types < $26 (the bonus object $0A)
ZONES = ("THZ", "GPZ", "SEZ", "MGHZ", "AQZ", "EEZ")
BOSS_TYPE = {0: 0x50, 1: 0x51, 2: 0x54, 3: 0x56, 4: 0x59, 5: 0x61}   # the controller object each zone's act-3 placement creates


def hx(v, n=2):
    return format(v, "0%dX" % n)


def sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def off(bank, cpu):
    return cpu if cpu < 0x8000 else bank * 0x4000 + cpu - 0x8000


def u16(rom, o):
    return rom[o] | (rom[o + 1] << 8)


def load_rom(path):
    data = Path(path).read_bytes()
    if len(data) != 524288 or hashlib.sha256(data).hexdigest() != ROM_SHA256:
        raise ValueError("Expected the documented Sonic Chaos SMS research ROM (SHA-256 %s)" % ROM_SHA256)
    return data


def region(rom, name, bank, a, b, role):
    o = off(bank, a)
    return dict(name=name, bank=(bank if a >= 0x8000 else None), cpu_start=hx(a, 4), cpu_end_exclusive=hx(b, 4), file_start=hx(o, 5), length=b - a,
                first16=bytes(rom[o:o + 16]).hex(), sha256=sha(rom[o:o + b - a]), role=role)


# ------------------------------------------------------------------------------------------------------------------------------------------
# Observer: passive hooks installed on every harness SMS created inside the `with` block
SPAWN_VECTOR = 0x5E9C        # $032C -> $5E9C : object creator, C = type, H = parameter
STATE20_ROUTINE = 0x03F5     # $03F5 (JP $4892) : request player state $20
PC_EVENTS = {
    0x14AE: "act_clear_tail", 0x1543: "zone_clear_tail", 0x1594: "zone_results_gate", 0x32F9: "results_card", 0x2D55: "boss_bonus_loop",
    0x2D08: "tally_loops", 0x15CE: "zone_increment", 0x1538: "act_increment", 0x1365: "end_path", 0x18ED: "ending_selector",
    0x83E7: "flag_bit5_set", 0x83ED: "flag_bit4_set", 0x04B4: "title_entry", 0x4E97: "start_position_return", 0x9C93: "bonus_obj_compute",
    0x18FE: "ending_full_sonic", 0x1A41: "ending_partial_sonic", 0x1ACD: "ending_other_character",
}
WATCH_TYPES = {0x0A, 0x0F, 0x12, 0x34, 0x50, 0x51, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F, 0x60, 0x61, 0x62, 0x63}
WATCH = {0xD2A6: "D2A6lo", 0xD2A7: "D2A6hi", 0xD293: "D293", 0xD297: "zone", 0xD298: "act", 0xD299: "lives", 0xD2C3: "continues", 0xD2CC: "emeralds",
         0xD2BE: "timer_run", 0xD29D: "score0", 0xD29E: "score1", 0xD29F: "score2"}


class Observer:
    """Collects ordered events from whatever harness runs inside the context.  It never writes game state."""

    def __init__(self):
        self.runs = []          # one event list per SMS instance created inside the context
        self._saved = None

    @property
    def events(self):
        """The run with the most events (the harnesses build auxiliary machines for controlled cases after their main fight)."""
        return max(self.runs, key=len) if self.runs else []

    def __enter__(self):
        import sms_frame_harness as H
        self.H = H
        self._saved = (H.SMS.__init__, H.SMS.add_pc_hook)
        orig_init, orig_add = self._saved
        obs = self

        def add(sms, address, fn):
            # the harnesses re-register hooks and rely on REPLACE semantics: keep that, and chain the observer's own hook in front
            mine = sms.__dict__.setdefault("_u2_mine", {}).get(address)
            if mine is None or fn is mine:
                orig_add(sms, address, fn)
                return

            def both(mm, mine=mine, fn=fn):
                mine(mm)
                fn(mm)
            orig_add(sms, address, both)

        def init(sms, rom):
            orig_init(sms, rom)
            obs.runs.append([])
            obs._attach(sms, obs.runs[-1], orig_add)

        H.SMS.__init__ = init
        H.SMS.add_pc_hook = add
        return self

    def __exit__(self, *a):
        self.H.SMS.__init__, self.H.SMS.add_pc_hook = self._saved
        return False

    def _attach(self, sms, ev, orig_add):
        m = sms.mem

        def add(sms_, address, fn):
            sms_.__dict__.setdefault("_u2_mine", {})[address] = fn
            orig_add(sms_, address, fn)

        def snap():
            return dict(zone=m[0xD297], act=m[0xD298], score=[m[0xD29F], m[0xD29E], m[0xD29D]], D2A6=m[0xD2A6] | (m[0xD2A7] << 8), rings=m[0xD29A],
                        time=[m[0xD2C0], m[0xD2BF]], clear=m[0xD293], lives=m[0xD299], continues=m[0xD2C3], emeralds=m[0xD2CC],
                        player=[m[0xD511] | (m[0xD512] << 8), m[0xD514] | (m[0xD515] << 8)], camera=[m[0xD2D6] | (m[0xD2D7] << 8), m[0xD2D8] | (m[0xD2D9] << 8)])

        def pc_hook(pc, name):
            def hook(mm):
                if 0x4000 <= pc < 0x8000 and mm.slot[1] != 1:
                    return
                if pc in (0x83E7, 0x83ED, 0x9C93) and mm.slot[2] != BANK_OBJ:
                    return
                d = snap()
                d.update(frame=sms.frame, ev=name)
                ev.append(d)
            return hook

        def spawn(mm):
            sp = mm.cpu.sp
            d = snap()
            d.update(frame=sms.frame, ev="spawn", type=mm.cpu.c, param=mm.cpu.h, parent_type=m[mm.cpu.ix], parent_state=m[mm.cpu.ix + 1], ret=m[sp] | (m[sp + 1] << 8), bank=mm.slot[2])
            ev.append(d)

        def s20(mm):
            sp = mm.cpu.sp
            d = snap()
            d.update(frame=sms.frame, ev="state20_request",parent_type=m[mm.cpu.ix], ret=m[sp] | (m[sp + 1] << 8), bank=mm.slot[2], act_index=m[0xD298], player_state=m[0xD501])
            ev.append(d)

        for pc, name in PC_EVENTS.items():
            add(sms, pc, pc_hook(pc, name))
        add(sms, SPAWN_VECTOR, spawn)
        add(sms, STATE20_ROUTINE, s20)
        # RAM changes are POLLED once per frame (hooking the write callback perturbs the harnesses that snapshot and restore the CPU)
        prev = {a: m[a] for a in WATCH}
        orig_run = sms.run_frame

        slot_prev = {b: m[b] for b in range(0xD540, 0xDA00, 64)}
        state_prev = {b: m[b + 1] for b in range(0xD540, 0xDA00, 64)}

        def run_frame():
            orig_run()
            for b in range(0xD540, 0xDA00, 64):
                if m[b] != slot_prev[b]:
                    if m[b] in WATCH_TYPES or slot_prev[b] in WATCH_TYPES:
                        d = snap()
                        d.update(frame=sms.frame, ev="slot_type", slot=b, old=slot_prev[b], new=m[b], param=m[b + 0x3F], state=m[b + 1])
                        ev.append(d)
                    slot_prev[b] = m[b]
                if m[b] in WATCH_TYPES and m[b + 1] != state_prev[b]:
                    d = snap()
                    d.update(frame=sms.frame, ev="slot_state", slot=b, type=m[b], old=state_prev[b], new=m[b + 1], param=m[b + 0x3F])
                    ev.append(d)
                state_prev[b] = m[b + 1]
            for a, name in WATCH.items():
                if m[a] != prev[a]:
                    d = snap()
                    d.update(frame=sms.frame, ev="write_" + name, old=prev[a], new=m[a])
                    ev.append(d)
                    prev[a] = m[a]
        sms.run_frame = run_frame

    def summary(self):
        """Compact, ordered, de-duplicated view used by the JSON: first occurrence of each (event, key) plus every D2A6/flag/zone change."""
        out, seen = [], set()
        score_writes = []
        for e in self.events:
            n = e["ev"]
            if n.startswith("write_score"):
                score_writes.append(e)
                continue
            if n == "spawn":
                key = (n, e["type"], e["param"], e["parent_type"])
                if key in seen:
                    continue
                seen.add(key)
            elif n == "state20_request":
                key = (n, e["parent_type"], e["ret"])
                if key in seen:
                    continue
                seen.add(key)
            elif n in ("write_timer_run",):
                pass
            out.append(e)
        return out, score_writes


# ------------------------------------------------------------------------------------------------------------------------------------------
# BCD helpers and the pure model (the $0A bonus word is the raw $041F word: NO zero replacement, NO equal-digit life)
def bcd_to_int(v):
    return (v >> 4) * 10 + (v & 15)


def bcd_digits_int(bs):
    return int("".join(format(b, "02X") for b in bs))


def model_bonus_word(time_table, time_bcd, rings):
    import u3_sign_prizes as U3
    h, l = U3.bonus_word(time_table, time_bcd, rings)
    return (h << 8) | l


def word_to_raw_units(word):
    """The tally pays D2A6 at +1 raw unit per step with the low byte first: units = BCD digits of H*100 + L."""
    return (word >> 8) * 100 + bcd_to_int(word & 255)


# ------------------------------------------------------------------------------------------------------------------------------------------
# Static census
ROUTINES = [
    ("creator_5E9C", None, 0x5E9C, 0x5EB7, "vector $032C: C = type, H = parameter, first free slot from $D540 (16 slots); no free slot -> RET with nothing created"),
    ("player_state20_4892", None, 0x4892, 0x48A7, "vector $03F5: D502 := $20, request $89 (act index != 2) or $97 (act index 2)"),
    ("act_clear_tail_14AE", None, 0x14AE, 0x1543, "main-loop tail for D293 bit 5 (act index 0/1)"),
    ("zone_clear_tail_1543", None, 0x1543, 0x15F2, "main-loop tail for D293 bit 4 (act index 2): fades, results gate $1594, zone increment $15CE"),
    ("tally_loops_2D08", None, 0x2D08, 0x2D55, "ring loop (10 raw per ring) then the D2A6 bonus-word loop (1 raw per step)"),
    ("boss_bonus_loop_2D55", None, 0x2D55, 0x2D84, "act index 2 only: N steps of 10 raw before the tally loops"),
    ("boss_bonus_table_2D84", None, 0x2D84, 0x2D90, "six 16-bit step counts, one per zone"),
    ("bonus_word_6276", None, 0x6276, 0x62AD, "$041F: time bucket + (D29A - $11) -> HL"),
    ("bonus_time_table_62AD", None, 0x62AD, 0x62D5, "ten 4-byte entries: limit mm:ss BCD, L, H"),
    ("state20_handler_83A6", BANK_OBJ, 0x83A6, 0x8400, "player state $20 handler: run right, sets D293 bit 5 (act index < 2) or bit 4 (act index 2) beyond cameraX + $120"),
    ("bonus_object_0A", BANK_OBJ, 0x9C58, 0x9CAC, "type $0A: 3-entry state table, state-0 and sparkle-emitter scripts, state-0 callback (D2A6 for parameter 0), player-position copy"),
    ("boss_release_81BD", BANK_BOSS, 0x81BD, 0x8212, "shared state-5 release: floor gate, camera/limits, $03F5, allocate $0A parameter 0, convert to $0F; $81F4 = MGHZ3 branch"),
    ("boss_state5_script_961E", BANK_BOSS, 0x961E, 0x9632, "script of state 5 of $50/$54/$56/$60: record whose callback is $81BD"),
    ("aqz_state5_script_A7F0", BANK_BOSS, 0xA7F0, 0xA85B, "script of state 5 of $59 (callback record at $A857 -> $81BD)"),
    ("gpz_head_release_9D26", BANK_BOSS, 0x9D26, 0x9D58, "GPZ3 head state 14 grounded release: limits, $0A parameter 0, $03F5"),
    ("eez_61_state5_script_B9FF", BANK_BOSS, 0xB9FF, 0xBA37, "$61 state 5 script: two spawns of type $0A parameter 1 (dx +4/-4) after 24 updates"),
    ("eez_61_state5_callback_BB1A", BANK_BOSS, 0xBB1A, 0xBB51, "$61 state 5 callback: early clear D293 := $50 unless Sonic with D2CC = $1F"),
    ("eez_61_final_BB61", BANK_BOSS, 0xBB61, 0xBB76, "$61 state 7: D2CC |= $20, D293 := $50, type := $FF"),
    ("zone_results_gate_1594", None, 0x1594, 0x15F2, "zone >= 5 skips the results card"),
]

ANCHORS = [
    ("zone_clear_flag_state20", BANK_OBJ, 0x83DD, "3a98d2fe0230062193d2cbeec92193d2cb", "act index (D298) < 2 -> D293 bit 5, else bit 4"),
    ("state20_request", None, 0x4892, "3e203202d50e893a98d2fe0220020e97793204dec9", "D502 := $20; sound $89, or $97 when D298 = 2"),
    ("bonus_obj_state0_callback", BANK_OBJ, 0x9C86, "dd360201dd7e3fb7c0dd360202cd1f0422", "$0A state 0: request state 1; parameter != 0 -> stay (sparkle); parameter 0 -> state 2, CALL $041F, D2A6 := HL (no zero replacement, no life)"),
    ("release_floor_gate_shared", BANK_BOSS, 0x81BD, "dd7e00fe562830cd7d033a22d5cb4fc82a74d12280d2cd", "$81BD: type $56 -> $81F4 branch; else CALL $037D, floor bit 1 required"),
    ("release_limits_pan", BANK_BOSS, 0x81CD, "2a74d12280d2cd5c03dd6625dd6e2722", "D280 := camera X; CALL $035C (release pan); D282 := saved right limit (+$25/+$27)"),
    ("release_tail_81DF", BANK_BOSS, 0x81DF, "cdf5030e0a2600cd2c03dd363f80dd363e00c33e03cd", "CALL $03F5, allocate $0A parameter 0, +$3F := $80, +$3E := 0, JP $033E (convert to $0F)"),
    ("release_mghz_branch_81F4", BANK_BOSS, 0x81F4, "cd5c03dd6625dd6e272282d22a11d5111c0dafed52d83a22d5cb4fc8", "MGHZ3: restore right limit, player X >= $0D1C and floor bit 1, then JR $81DF (no left-limit write)"),
    ("gpz_head_release_9D26", BANK_BOSS, 0x9D26, "3a22d5cb4fc82a74d12280d2018007ed4382d2116000ed537ed2cd5c03cd2b04dd3600ffdd363e000e0a2600cd2c03c3f503", "GPZ3 head state 14: floor bit 1; limits camera..$0780; $035C; $042B; type $FF; $0A parameter 0; JP $03F5"),
    ("eez_61_state5_early_clear", BANK_BOSS, 0xBB1A, "3a00d5fe0120073accd2fe1f28053e503293", "Sonic (D500 = 1) with D2CC = $1F waits; every other case D293 := $50"),
    ("eez_61_state7_final", BANK_BOSS, 0xBB61, "cd99813accd2f62032ccd23e503293d2dd3600ffc97c", "D2CC |= $20; D293 := $50; type := $FF"),
    ("boss_bonus_loop_2D55", None, 0x2D55, "3a98d2fe02c03a97d28721842d16005f194e2346c5cd052ff3cdf826fbcde62ec10b78b120ee060cfbcd2d0610fac932", "act index 2 only; steps from $2D84 + zone * 2"),
    ("boss_bonus_table_2D84", None, 0x2D84, "320064009600c800fa005802", "50 100 150 200 250 600 steps of 10 raw"),
    ("zone_results_gate_1594", None, 0x1594, "3a97d2fe053033cdf9320630fbcd2d0610fa2192d43600cbf6cbe62194d43600cbf6cbe60660fbcd", "zone >= 5 skips the results screen $32F9"),
    ("eez_61_state5_spawn_op", BANK_BOSS, 0xBA12, "ff040a0400000001", "script op FF 04: spawn type $0A, dx +4, dy 0, parameter 1 (the second spawn, dx -4, follows at $BA37-ish)"),
]


def check_anchors(rom):
    out = []
    for name, bank, cpu, want, note in ANCHORS:
        n = len(bytes.fromhex(want))
        got = bytes(rom[off(bank, cpu):off(bank, cpu) + n]).hex()
        out.append(dict(name=name, bank=bank, cpu=hx(cpu, 4), file=hx(off(bank, cpu), 5), expected=want, actual=got, ok=(got == want), note=note))
    return out


def state_table(rom, bank, table):
    """State script pointers of a type: the table ends where the first script after it begins (pointers >= table)."""
    o = off(bank, table)
    ptrs, limit = [], None
    for i in range(48):
        if limit is not None and table + 2 * i >= limit:
            break
        p = u16(rom, o + 2 * i)
        ptrs.append(p)
        if p > table and (limit is None or p < limit):
            limit = p
    return ptrs


def type_states(rom, t):
    bank = BANK_OBJ if t < 0x26 else BANK_BOSS
    table = u16(rom, 0x65BA + (t - 1) * 2)
    return bank, table, state_table(rom, bank, table)


CALLBACK_SITES = {
    "release_81BD": 0x81BD,      # state-5 release callback (shared)
    "gpz_head_release_9D26": 0x9D26,
}

STATE_TYPES = (0x0A, 0x0F, 0x12, 0x34, 0x50, 0x51, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F, 0x60, 0x61, 0x62)


def script_owner(rom, cpu):
    """(type, state) pairs owning the script that contains `cpu`: the script start is the greatest state pointer of ANY boss type that is <= cpu."""
    tabs = {}
    for t in STATE_TYPES:
        bank, table, ptrs = type_states(rom, t)
        if bank == BANK_BOSS:
            tabs[t] = ptrs
    allp = sorted({p for ptrs in tabs.values() for p in ptrs if p >= 0x8000})
    below = [p for p in allp if p <= cpu]
    if not below or cpu - below[-1] >= 0x80:
        return []
    start = below[-1]
    return [dict(type=t, state=i, script=hx(start, 4)) for t, ptrs in tabs.items() for i, p in enumerate(ptrs) if p == start]


def find_callback_references(rom, bank, cpu):
    """Little-endian occurrences of a callback address inside a bank (script records / vectors); CALL/JP operands are listed separately."""
    d = rom[bank * 0x4000:(bank + 1) * 0x4000]
    pat = bytes([cpu & 255, cpu >> 8])
    out, i = [], d.find(pat)
    while i != -1:
        pre = d[i - 1] if i else 0
        out.append(dict(cpu=hx(0x8000 + i, 4), kind="call_or_jump_operand" if pre in (0xCD, 0xC3) else "data_word", context=d[max(0, i - 3):i + 3].hex()))
        i = d.find(pat, i + 1)
    return out


def script_ops(rom, bank, start, limit=60):
    """Minimal FF-command decoder (same grammar as docs/object-50.md)."""
    pc, seen, out = start, set(), []
    while len(out) < limit:
        if pc in seen:
            out.append(dict(cpu=hx(pc, 4), op="loops_back"))
            break
        seen.add(pc)
        o = off(bank, pc)
        b = rom[o]
        if b != 0xFF:
            out.append(dict(cpu=hx(pc, 4), op="record", duration=b, frame=rom[o + 1], callback=hx(u16(rom, o + 2), 4)))
            pc += 4
            continue
        c = rom[o + 1]
        a = rom[o + 2:o + 10]
        e = dict(cpu=hx(pc, 4), cmd=hx(c))
        w = lambda i: a[i] | (a[i + 1] << 8)
        s = lambda v: v - 65536 if v >= 32768 else v
        if c == 0:
            e.update(op="restart_state"); out.append(e); break
        if c == 3:
            e.update(op="request_state", state=a[0]); out.append(e); break
        if c == 1:
            e.update(op="call", target=hx(w(0), 4)); pc += 4
        elif c == 2:
            e.update(op="velocity", x=s(w(0)), y=s(w(2))); pc += 6
        elif c == 4:
            e.update(op="spawn", type=hx(a[0]), dx=s(w(1)), dy=s(w(3)), parameter=hx(a[5])); pc += 8
        elif c == 5:
            e.update(op="call_set_callback", target=hx(w(0), 4), callback=hx(w(2), 4)); pc += 6
        elif c == 6:
            e.update(op="sound", sound=hx(a[0])); pc += 3
        elif c == 7:
            e.update(op="jump", target=hx(w(0), 4)); pc = w(0)
        elif c == 9:
            e.update(op="set_field", offset=hx(a[0]), value=hx(a[1])); pc += 4
        elif c == 0x0E:
            e.update(op="loop_count", count=a[0]); pc += 3
        elif c == 0x0F:
            e.update(op="loop_jump", target=hx(w(0), 4)); pc += 4
        else:
            e.update(op="unknown"); out.append(e); break
        out.append(e)
    return out


def boss_bonus_table(rom):
    steps = [u16(rom, 0x2D84 + 2 * i) for i in range(6)]
    return dict(steps=steps, raw_units=[s * 10 for s in steps], used_zones=[0, 1, 2, 3, 4], unused_zone=5,
                note="$2D55 reads word [zone] (D297) and awards N steps of 10 raw before the tally loops; zone 5 never reaches it (results skipped)")


def g0_spine_disclosure():
    d = json.loads((ROOT / "data" / "g0" / "campaign-oracle.json").read_text(encoding="utf-8"))
    acts = d["campaign_spine"]["acts"]
    rows = [dict(zone=a["zone"], act=a["act"], how=a["how"]) for a in acts]
    return dict(source="data/g0/campaign-oracle.json campaign_spine.acts", fixtures=d["campaign_spine"]["fixtures"], rows=rows,
                injected_or_forced=sum(1 for r in rows if "real sign chain" not in r["how"]), natural_sign_chain=sum(1 for r in rows if "real sign chain" in r["how"]),
                note="the 6 act-index-2 rows of the spine are a forced player state $20 (THZ3) or an injected D293 flag: none of them contains a boss defeat, a $0A object or a D2A6 write")


POC_SOURCE_READ = [
    dict(file="scripts/SCR_chaos_boss/SCR_chaos_boss.gml", lines="173-179, 220-228", fact="chaos_boss_bonus(seconds, rings): H = max(0, 9 - floor(seconds / 30)); L = (rings - 11) mod 100; steps = H * 100 + L",
         versus_rom="ROM bucket limits are strict mm:ss BCD 0:29, 0:59, 1:29, ... 3:59, 4:59 (not floor(s/30)); the POC formula flips one second early on every boundary and has no 4:59 last bucket"),
    dict(file="scripts/SCR_chaos_boss/SCR_chaos_boss.gml (and gpz/mghz/sez boss scripts)", lines="223 / 205 / 313 / 361", fact="global.chaosBossClearScore = ring * 10 + steps + 500",
         versus_rom="the fixed boss bonus is zone dependent 500/1000/1500/2000/2500 (table $2D84), not a constant 500; and it is a results-tally component, not a pre-computed clear score"),
    dict(file="scripts/SCR_chaos_level/SCR_chaos_level.gml", lines="476-493", fact="chaos_act_complete: results only for act < 3; act 3 keeps the developer return (90 ticks) or zoneGoto progression + SCR_save_game",
         versus_rom="the ROM runs the same results/tally/title tail for act index 2 (D293 bit 4 -> $1543) with the fixed boss bonus first"),
    dict(file="scripts/SCR_chaos_results/SCR_chaos_results.gml", lines="29-40", fact="chaos_results_bonus: G1-D corrected ROM word incl. the sign child's zero -> 777 replacement",
         versus_rom="correct for the sign child $19; the boss object $0A has NO zero replacement (zero stays zero) and no equal-digit life"),
]


def build_static(rom):
    import u3_sign_prizes as U3
    st = dict(schema="u2-act3-boss-bonus-static/1", base_commit=BASE_COMMIT, rom_sha256=ROM_SHA256)
    st["tiers"] = dict(SOURCE="decoded ROM bytes, hashes, anchors, script decode", CONTROLLED="Z80 oracle", EMULATED="unmodified ROM in the harness with disclosed fixtures", FIXTURE="named injected values",
                       POC_SOURCE_READ="G1-D d9275feeca1a799928b6eb1a866d32275c4024b5, read only")
    st["routines"] = [region(rom, n, b, a, e, r) for n, b, a, e, r in ROUTINES]
    st["anchors"] = check_anchors(rom)
    st["fixed_boss_bonus"] = boss_bonus_table(rom)
    tt = U3.time_table(rom)
    st["bonus_word_inputs"] = dict(time_table=[dict(limit_bcd_mmss=hx(l, 4), l=hx(lo), h=hx(h)) for l, lo, h in tt], timer_bytes="D2BF = seconds BCD, D2C0 = minutes BCD", rings_byte="D29A (BCD)",
                                   formula="L = ((D29A - $11) DAA) + entry.L (DAA); H = entry.H; carry -> H + 1 (never happens: all entry.L = 0)")

    # --- type tables, state scripts, defeat producers ----------------------------------------------------------------------------------------
    types = {}
    for t in STATE_TYPES:
        bank, table, ptrs = type_states(rom, t)
        types[hx(t)] = dict(bank=bank, table=hx(table, 4), states=len(ptrs), state_scripts=[hx(p, 4) for p in ptrs])
    st["type_state_tables"] = types
    refs = {}
    for name, cpu in (("81BD", 0x81BD), ("9D26", 0x9D26)):
        refs[name] = dict(references=find_callback_references(rom, BANK_BOSS, cpu), script_owners=[])
        for r in refs[name]["references"]:
            if r["kind"] == "data_word":
                refs[name]["script_owners"] += [dict(site=r["cpu"], type=hx(o["type"]), state=o["state"], script=o["script"]) for o in script_owner(rom, int(r["cpu"], 16))]
    st["release_callback_references"] = refs
    allocs = []
    for cpu in (0x81E2, 0x9D4E):
        o = off(BANK_BOSS, cpu)
        allocs.append(dict(cpu=hx(cpu, 4), file=hx(o, 5), bytes=bytes(rom[o:o + 7]).hex(), meaning="LD C,$0A / LD H,0 / CALL $032C"))
    st["bonus_object_allocation_sites"] = dict(
        immediate_creator_calls=allocs,
        scanned="every `LD C,$0A` / `LD A,$0A` / `LD BC,$000A` / `LD DE,$000A` within 16 bytes of CALL/JP $032C, $032F or $0332 in banks $0C, $1D, $1E, $1F: exactly the two sites above",
        script_spawn_ops=[dict(cpu=x["cpu"], **{k: v for k, v in x.items() if k != "cpu"}) for x in script_ops(rom, BANK_BOSS, 0xB9FF) if x.get("op") == "spawn"],
        note="the only other source of a $0A object is the object's own script ($0A parameter 0 state 2 spawns $0A parameter $FF sparkles) and the EEZ $61 state-5 script (parameter 1)")
    zones = {}
    owners_81bd = refs["81BD"]["script_owners"]
    zones["0"] = dict(zone="THZ", controller=hx(0x50), producer="$81BD via state-5 script $961E", owner_state=5, gate="floor bit 1 ($D522 bit 1)", mechanism="release_81BD")
    zones["1"] = dict(zone="GPZ", controller=hx(0x51), producer="$9D26 head state 14 (grounded)", owner_state=14, gate="floor bit 1 ($D522 bit 1)", mechanism="gpz_head_release_9D26")
    zones["2"] = dict(zone="SEZ", controller=hx(0x54), producer="$81BD via state-5 script $961E", owner_state=5, gate="floor bit 1", mechanism="release_81BD")
    zones["3"] = dict(zone="MGHZ", controller=hx(0x56), producer="$81BD -> $81F4 branch -> $81DF", owner_state=5, gate="player X >= $0D1C (3356) AND floor bit 1; no left-limit write", mechanism="release_81BD")
    zones["4"] = dict(zone="AQZ", controller=hx(0x59), producer="$81BD via state-5 script $A7F0 (record $A857)", owner_state=5, gate="floor bit 1", mechanism="release_81BD")
    zones["5"] = dict(zone="EEZ", controller=hx(0x61), producer="NONE: $61 writes D293 := $50 directly (state 5 early clear BB28, or state 7 final BB6C)", owner_state="5 or 7",
                      gate="state 5: any case except Sonic with D2CC == $1F; state 7: after contact", mechanism="eez_61_direct_flag",
                      bonus_object="script spawns $0A parameter 1 (sparkles) 24 updates into state 5; parameter 1 never writes D2A6; results card skipped")
    st["zones"] = zones
    shared = [(int(o["type"], 16), o["state"]) for o in owners_81bd]
    st["shared_release_users"] = dict(type_state_pairs=[dict(type=hx(t), state=s) for t, s in sorted(set(shared))],
                                      note="type $60 (EEZ mid boss) lists the same state-5 script but its observed route never enters state 5 (UNVERIFIED reachability); $5E/$5F/$62 do not")

    # --- the $0A object ---------------------------------------------------------------------------------------------------------------------------
    bank, table, ptrs = type_states(rom, 0x0A)
    st["bonus_object_0A"] = dict(
        evidence="SOURCE (decoded states, $9C86 anchor) + CONTROLLED + EMULATED",
        states=[dict(state=i, script=hx(p, 4)) for i, p in enumerate(ptrs)],
        script_state0=script_ops(rom, BANK_OBJ, ptrs[0]), script_state2=script_ops(rom, BANK_OBJ, ptrs[2]),
        semantics=dict(
            parameter_0="state 0 callback: request state 1, then (parameter == 0) request state 2, HL := $041F, D2A6 := HL, copy the player's X/Y; state 2 is a sparkle emitter every 8 updates ($0A parameter $FF at player Y - 12 / Y - 8) that never ends",
            parameter_nonzero="the callback returns after `LD (IX+2),1`: no D2A6 write (state 1 script: sparkle, 28 updates)",
            no_zero_replacement="D2A6 is stored exactly as $041F returns it: H|L = 0 stays 0 (the sign child $19 replaces 0 by $0777 and grants a life for equal digits; $0A does neither)",
            first_run="the object is allocated in the boss's defeat update; its first update (state 0 callback) is the NEXT update, so D2A6 reads the timer and D29A of that update"),
        writers_of_D2A6=["0C:AB52 sign child $19 (zero -> $0777, equal-digit life)", "0C:9C96 boss bonus object $0A parameter 0", "1E:$94BD Special Stage success (seconds left << 8)", "tally decrement $2D08 loops"])
    st["g0_spine_disclosure"] = g0_spine_disclosure()
    st["poc_source_read"] = dict(commit="d9275feeca1a799928b6eb1a866d32275c4024b5", entries=POC_SOURCE_READ, note="read-only; not run; not ROM evidence")
    return st


# ------------------------------------------------------------------------------------------------------------------------------------------
# Controlled Z80 experiments
TIMES = [0x0000, 0x0028, 0x0029, 0x0058, 0x0059, 0x0128, 0x0129, 0x0158, 0x0159, 0x0228, 0x0229, 0x0258, 0x0259, 0x0328, 0x0329, 0x0358, 0x0359, 0x0429, 0x0458, 0x0459, 0x0900]
SLOT = 0xD700


def lab(rom, bank):
    from oracle import Oracle
    o = Oracle(rom)
    m = o.mem
    m[0xD540:0xDA00] = bytes(0x4C0)
    m[0xD52C], m[0xD52D] = 8, 24
    o.bank(2, bank)
    m[0xD12B] = bank
    return o, m


def release_case(rom, t, floor, px, saved=2304, addr=0x81BD, d298=2, fill_pool=False):
    o, m = lab(rom, BANK_BOSS)
    m[SLOT] = t
    m[SLOT + 1] = m[SLOT + 2] = 5 if addr == 0x81BD else 14
    m[SLOT + 0x25], m[SLOT + 0x27] = saved >> 8, saved & 255
    m[0xD298] = d298
    o.word(0xD174, 3060)
    o.word(0xD176, 100)
    o.word(0xD280, 0)
    o.word(0xD282, 5000)
    o.word(0xD511, px)
    o.word(0xD514, 300)
    m[0xD522] = floor
    m[0xD502] = 5
    m[0xDE04] = 0
    o.word(0xD2A6, 0)
    m[0xD2BF], m[0xD2C0], m[0xD29A] = 0x20, 0, 0x47
    if fill_pool:
        for b in range(0xD540, 0xDA00, 64):
            if b != SLOT:
                m[b] = 0xFE
    o.cpu.ix = SLOT
    o.call(addr)
    created = [dict(slot=hx(b, 4), type=hx(m[b]), parameter=m[b + 0x3F]) for b in range(0xD540, 0xDA00, 64) if m[b] and b != SLOT and m[b] != 0xFE]
    return dict(type_before=hx(t), floor=floor, player_x=px, d298=d298, pool_full=fill_pool, boss_type_after=hx(m[SLOT]), boss_state_after=m[SLOT + 1], parameter_after=hx(m[SLOT + 0x3F]),
                token_after=m[SLOT + 0x3E], player_requested_state=hx(m[0xD502]), sound=hx(m[0xDE04]), left_limit=o.word(0xD280), right_limit=o.word(0xD282), created=created, D2A6=o.word(0xD2A6))


def build_controlled(rom, st=None):
    import u3_sign_prizes as U3
    st = st or build_static(rom)
    tt = U3.time_table(rom)
    ctl = dict(schema="u2-act3-boss-bonus-controlled/1", base_commit=BASE_COMMIT, rom_sha256=ROM_SHA256,
               evidence="CONTROLLED ROUTINE RESULT: original routines on kosarev/z80 (tools/oracle.py) with explicit RAM; the shared release is run with a hand-built boss slot (FIXTURE)")
    # ---- release routines -----------------------------------------------------------------------------------------------------------------------
    rel = []
    for t, px in ((0x50, 3000), (0x54, 3000), (0x59, 3000), (0x56, 3355), (0x56, 3356), (0x56, 3500)):
        for fl in (0, 2):
            rel.append(release_case(rom, t, fl, px))
    rel.append(release_case(rom, 0x51, 2, 1700, addr=0x9D26))
    rel.append(release_case(rom, 0x51, 0, 1700, addr=0x9D26))
    ctl["release"] = dict(rows=rel, note="state-5 release (types $50/$54/$56/$59 via $81BD) and the GPZ3 head release ($9D26) with D298 = 2: without floor bit 1 nothing happens; with it the player state is $20 (sound $97), "
                          "one $0A parameter 0 exists, the boss slot becomes $0F (GPZ: $FF) and D2A6 is still 0 (written by the $0A object's first update)")
    ctl["release_act_index_sound"] = {str(d): release_case(rom, 0x50, 2, 3000, d298=d)["sound"] for d in (0, 1, 2)}
    ctl["allocation_failure"] = release_case(rom, 0x50, 2, 3000, fill_pool=True)
    ctl["allocation_failure"]["note"] = "all other 15 slots occupied: $032C returns without creating $0A; the boss still converts, player state $20 is still requested, D2A6 stays 0 (no invented fallback)"

    # ---- the $0A object: parameter semantics and the bonus word grid -----------------------------------------------------------------------------
    o, m = lab(rom, BANK_OBJ)
    prm = []
    for param in (0, 1, 0x80, 0xFF):
        m[SLOT:SLOT + 64] = bytes(64)
        m[SLOT] = 0x0A
        m[SLOT + 0x3F] = param
        o.word(0xD2A6, 0xBEEF)
        m[0xD2BF], m[0xD2C0], m[0xD29A], m[0xD299] = 0x20, 0, 0x47, 0x12
        o.word(0xD511, 1234)
        o.word(0xD514, 345)
        o.cpu.ix = SLOT
        o.call(0x9C86)
        prm.append(dict(parameter=hx(param), requested_state=m[SLOT + 2], D2A6=hx(o.word(0xD2A6), 4), lives=hx(m[0xD299]), position=[o.word(SLOT + 0x11), o.word(SLOT + 0x14)] if param == 0 else None))
    ctl["bonus_object_parameters"] = dict(rows=prm, note="D2A6 preset $BEEF: only parameter 0 overwrites it (to $0936 for 20 seconds / $47 rings); D299 is never touched")
    grid, bad = {}, []
    zero_cases = []
    for t in TIMES:
        row = []
        for n in range(100):
            r = U3.int_to_bcd(n)
            m[SLOT:SLOT + 64] = bytes(64)
            m[SLOT] = 0x0A
            o.word(0xD2A6, 0xBEEF)
            m[0xD2BF], m[0xD2C0], m[0xD29A], m[0xD299] = t & 255, t >> 8, r, 0x12
            o.cpu.ix = SLOT
            o.call(0x9C86)
            w = o.word(0xD2A6)
            exp = model_bonus_word(tt, t, r)
            if w != exp or m[0xD299] != 0x12:
                bad.append([hx(t, 4), hx(r), w, exp])
            if w == 0:
                zero_cases.append([hx(t, 4), hx(r)])
            row.append(w)
        grid[hx(t, 4)] = row
    ctl["bonus_word_grid"] = dict(times=[hx(t, 4) for t in TIMES], rows=grid, model_mismatches=bad, zero_words_left_as_zero=zero_cases,
                                  note="$9C86 executed for every BCD ring count and 21 time samples; equals the U3 model of $041F, zero stays zero, no life")
    # ---- fixed boss bonus table ---------------------------------------------------------------------------------------------------------------------
    ctl["fixed_boss_bonus"] = st["fixed_boss_bonus"]
    return ctl


# ------------------------------------------------------------------------------------------------------------------------------------------
# Emulated fights (observed through the harnesses; fixtures disclosed)
FIGHTS = {
    "THZ3": dict(zone=0, harness="tools/thz3_boss_support.py defeat_chain", fixtures=["arena ARRIVAL (camera 1500,80 / player 1604,238)", "synthetic player placement/attack writes at update boundaries", "rings preset $47"]),
    "GPZ3": dict(zone=1, harness="tools/gpz51_fullgame.py build", fixtures=["arena ARRIVAL (camera 1500,96 / player 1604,238)", "synthetic player placement/attack writes", "rings preset $47"]),
    "SEZ3": dict(zone=2, harness="tools/sez54_fullgame.py build (fight)", fixtures=["ZoneGame arena placement (3060,620)", "synthetic attack writes", "rings preset $47"]),
    "MGHZ3": dict(zone=3, harness="tools/mghz56_fullgame.py build", fixtures=["arena ARRIVAL (camera 2940,256 / player 3044,430)", "synthetic attack writes", "rings preset $47"]),
    "AQZ3": dict(zone=4, harness="tools/aqz59_game.py build (first fight_9 chain)", fixtures=["ZoneGame arena placement (1800,238)", "synthetic attack writes", "rings preset $47"]),
}
EEZ_VARIANTS = {"EEZ3_sonic_flags1F": (0x1F, 1), "EEZ3_sonic_flags00": (0x00, 1), "EEZ3_sonic_flags3F": (0x3F, 1)}


def run_fight(rom, key):
    (ROOT / "build").mkdir(exist_ok=True)
    with Observer() as O:
        if key == "THZ3":
            import thz3_boss_support as M
            M.defeat_chain(rom)
        elif key == "GPZ3":
            import gpz51_fullgame as M
            M.build(rom)
        elif key == "SEZ3":
            import sez54_fullgame as M
            M.build(rom)
        elif key == "MGHZ3":
            import mghz56_fullgame as M
            M.build(rom, with_camera_replay=False)
        elif key == "AQZ3":
            import aqz59_game as M
            M.build(rom)
        else:
            import eez_boss_game as M
            flags, ch = EEZ_VARIANTS[key]
            M.build(rom, flags=flags, character=ch)
    return O.events


BOSS_TYPES = (0x50, 0x51, 0x54, 0x56, 0x59, 0x5E, 0x5F, 0x60, 0x61, 0x62, 0xFF)


def analyze(events, zone, boss_type):
    """Reduce an ordered event list to one record.  The segment starts at the creation of the boss controller preceding the first $0A (or, for EEZ, the controller's
    creation) and ends at the first terminal event of the clear chain."""
    ev = events
    first_bonus = next((i for i, e in enumerate(ev) if e["ev"] == "slot_type" and e["new"] == 0x0A and e["param"] == 0), None)
    anchor = first_bonus if first_bonus is not None else next((i for i, e in enumerate(ev) if e["ev"] == "slot_type" and e["new"] == boss_type), 0)
    start = anchor
    while start > 0 and not (ev[start]["ev"] == "slot_type" and ev[start]["new"] == boss_type):
        start -= 1
    terminal = "title_entry" if zone == 5 else "zone_increment"
    end = next((i for i in range(anchor, len(ev)) if ev[i]["ev"] == terminal), len(ev) - 1)
    seg = ev[start:end + 1]

    def first(name, after=0):
        return next((e for e in seg[after:] if e["ev"] == name), None)

    def frames(name):
        return [e["frame"] for e in seg if e["ev"] == name]

    path, last = [], None
    for e in seg:
        if e["ev"] == "slot_state" and e["type"] in BOSS_TYPES:
            key = (e["type"], e["new"])
            if key != last:
                path.append([e["frame"], e["type"], e["new"]])
                last = key
    bonus_objs = [[e["frame"], e["param"]] for e in seg if e["ev"] == "slot_type" and e["new"] == 0x0A]
    compute = [dict(frame=e["frame"], time=e["time"], rings=e["rings"], D2A6_before=e["D2A6"]) for e in seg if e["ev"] == "bonus_obj_compute"]
    sets, prev = [], 0
    for e in seg:
        if e["D2A6"] != 0 and prev == 0 and e["ev"] in ("write_D2A6lo", "write_D2A6hi"):
            sets.append(dict(frame=e["frame"], word=e["D2A6"], time=e["time"], rings=e["rings"]))
        prev = e["D2A6"]
    s20 = [dict(frame=e["frame"], parent_type=e["parent_type"], caller=hx(e["ret"], 4), bank=e["bank"], act_index=e["act_index"]) for e in seg if e["ev"] == "state20_request"]
    d293 = [[e["frame"], e["old"], e["new"]] for e in seg if e["ev"] == "write_D293"]
    rec = dict(zone=zone, controller_type=boss_type, boss_state_path=path, bonus_objects_created=bonus_objs, bonus_compute_inputs=compute, D2A6_sets=sets, state20_requests=s20, D293_writes=d293)
    names = ("flag_bit4_set", "zone_clear_tail", "zone_results_gate", "results_card", "boss_bonus_loop", "tally_loops", "zone_increment", "end_path", "ending_selector",
             "ending_full_sonic", "ending_partial_sonic", "ending_other_character", "title_entry", "start_position_return")
    rec["tail_frames"] = {n: frames(n)[:3] for n in names if frames(n)}
    rec["counts"] = dict(boss_bonus_loop=len(frames("boss_bonus_loop")), tally_loops=len(frames("tally_loops")), results_card=len(frames("results_card")), zone_increment=len(frames("zone_increment")),
                         bonus_objects_param0=sum(1 for _f, p in bonus_objs if p == 0), D2A6_sets=len(sets), flag_bit4_set=len(frames("flag_bit4_set")))
    a, b, c = first("boss_bonus_loop"), first("tally_loops"), first("zone_increment")
    if a and b and c:
        s0, s1, s2 = bcd_digits_int(a["score"]), bcd_digits_int(b["score"]), bcd_digits_int(c["score"])
        rings = b["rings"]
        rec["score"] = dict(at_boss_bonus_loop=s0, at_tally_loops=s1, at_zone_increment=s2, fixed_bonus=s1 - s0, tally_total=s2 - s1, rings_bcd_at_tally=hx(rings),
                            ring_units=bcd_to_int(rings) * 10, word_at_tally=b["D2A6"], word_units=word_to_raw_units(b["D2A6"]))
    first_e = seg[0]
    nxt = next((e for e in ev[end:] if e["ev"] == "start_position_return"), None) if zone < 5 else ev[end]
    after = nxt if nxt else seg[-1]
    rec["retained"] = dict(lives=[first_e["lives"], after["lives"]], continues=[first_e["continues"], after["continues"]], emeralds=[first_e["emeralds"], after["emeralds"]],
                           zone_act_before=[first_e["zone"], first_e["act"]], zone_act_after=[after["zone"], after["act"]], score_before=bcd_digits_int(first_e["score"]), score_after=bcd_digits_int(after["score"]))
    if zone < 5 and nxt:
        rec["next_start"] = dict(zone=nxt["zone"], act=nxt["act"], player=nxt["player"], camera_target=nxt["camera"])
    base = s20[0]["frame"] if s20 else (d293[0][0] if d293 else None)
    if base is not None:
        rel = {n: [f - base for f in fr] for n, fr in rec["tail_frames"].items()}
        rel["D2A6_set"] = [s["frame"] - base for s in sets]
        rel["state20_request"] = [s["frame"] - base for s in s20]
        rec["frames_relative_to_defeat"] = dict(base_frame=base, base_event="first $03F5 player-state-$20 request (hook frame)" if s20 else "first D293 clear write (polled frame)", offsets=rel)
    return rec


def build_observed(rom, st=None, progress=print, only=None):
    ob = dict(schema="u2-act3-boss-bonus-observed/1", base_commit=BASE_COMMIT, rom_sha256=ROM_SHA256,
              evidence="EMULATED ORIGINAL FRAMES with FIXTURE-driven player placement (harness list per record); frames are harness frames of the run that contains the chain",
              fights={}, injected_clears={})
    for key, meta in FIGHTS.items():
        if only and key not in only:
            continue
        progress("fight " + key)
        ev = run_fight(rom, key)
        rec = analyze(ev, meta["zone"], BOSS_TYPE[meta["zone"]])
        rec.update(label=key, harness=meta["harness"], fixtures=meta["fixtures"], evidence_class="EMULATED (natural boss defeat chain, synthetic player driver)")
        ob["fights"][key] = rec
    for key, (flags, ch) in EEZ_VARIANTS.items():
        if only and key not in only:
            continue
        progress("fight " + key)
        ev = run_fight(rom, key)
        rec = analyze(ev, 5, 0x61)
        rec.update(label=key, harness="tools/eez_boss_game.py build", fixtures=["ZoneGame arena placement (2050,430)", "synthetic contact writes", "RAM D2CC := $%02X, D2C8 := %d" % (flags, ch), "rings preset $47"],
                   evidence_class="EMULATED (natural boss chain, synthetic player driver)", emerald_flags_in=flags, character_in=ch)
        ob["fights"][key] = rec
    return ob


# ------------------------------------------------------------------------------------------------------------------------------------------
# Injected clears (what the G0 campaign spine did): a RAM flag, no boss, no $0A object
def run_injected(rom, zone, rings=0x47, settle=150, limit=7000):
    from g0_rig import Session
    with Observer() as O:
        S = Session(rom)
        S.set_start_index(zone, 2)
        S.boot_new_game(character=0)
        S.w("rings", rings)
        S.run(settle)
        S.s._write(0xD293, S.m[0xD293] | 0x10)
        S.run_until(lambda s: s.m[0xD297] != zone and s.playing(), limit=limit)
        S.run(10)
    return O.events


def analyze_injected(events, zone):
    inj = next(i for i, e in enumerate(events) if e["ev"] == "write_D293" and e["new"] & 0x10)
    seg = events[inj:]
    rec = analyze(seg, zone, 0xFFFF)
    return rec


def build_injected(rom, progress=print, only=None):
    out = {}
    for zone in range(5):
        key = "%s3_injected_flag" % ZONES[zone]
        if only and key not in only:
            continue
        progress("injected " + key)
        ev = run_injected(rom, zone)
        rec = analyze_injected(ev, zone)
        rec.update(label=key, evidence_class="FIXTURE + EMULATED (D293 bit 4 written by RAM at gameplay start; no boss exists)",
                   fixtures=["START_INDEX zone %d act 2 (natural RQ4 start record)" % zone, "RAM D29A := $47", "RAM D293 |= $10 after 150 frames (what tools/g0_scenarios.py campaign_spine did)"])
        out[key] = rec
    return out


# ------------------------------------------------------------------------------------------------------------------------------------------
# Validation (no ROM)
def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dumps(obj, indent=1):
    def scalar(v):
        return not isinstance(v, (dict, list))

    def rec(o, level):
        pad = " " * (indent * level)
        if isinstance(o, dict):
            if not o:
                return "{}"
            items = ",\n".join("%s%s: %s" % (pad + " " * indent, json.dumps(k), rec(v, level + 1)) for k, v in sorted(o.items(), key=lambda kv: str(kv[0])))
            return "{\n%s\n%s}" % (items, pad)
        if isinstance(o, (list, tuple)):
            if not o:
                return "[]"
            if all(scalar(v) for v in o):
                return json.dumps(list(o))
            items = ",\n".join(pad + " " * indent + rec(v, level + 1) for v in o)
            return "[\n%s\n%s]" % (items, pad)
        return json.dumps(o)
    return rec(obj, 0) + "\n"


def time_table_of_u3():
    import u3_sign_prizes as U3
    st3 = U3.load_json(U3.STATIC_JSON)
    return U3.time_table_of(st3)


def rq4_start(zone):
    d = load_json(ROOT / "data" / "rq4" / "start-registration.json")
    for r in d["static"]["table"]:
        if r["zone"] == zone and r["act"] == 0:
            return r
    return None


def validate_static(st):
    errs = []
    if st["rom_sha256"] != ROM_SHA256 or st["base_commit"] != BASE_COMMIT:
        errs.append("identity")
    for a in st["anchors"]:
        if not a["ok"] or a["expected"] != a["actual"]:
            errs.append("anchor " + a["name"])
    fb = st["fixed_boss_bonus"]
    if fb["steps"] != [50, 100, 150, 200, 250, 600] or fb["raw_units"] != [500, 1000, 1500, 2000, 2500, 6000]:
        errs.append("fixed bonus table")
    own = {(o["type"], o["state"]) for o in st["release_callback_references"]["81BD"]["script_owners"]}
    for need in (("50", 5), ("54", 5), ("56", 5), ("59", 5), ("60", 5)):
        if need not in own:
            errs.append("release owner %s" % (need,))
    if {(o["type"], o["state"]) for o in st["release_callback_references"]["9D26"]["script_owners"]} != {("51", 14)}:
        errs.append("gpz release owner")
    allocs = {a["cpu"] for a in st["bonus_object_allocation_sites"]["immediate_creator_calls"]}
    if allocs != {"81E2", "9D4E"}:
        errs.append("allocation sites")
    spawns = st["bonus_object_allocation_sites"]["script_spawn_ops"]
    if [(s["type"], s["parameter"]) for s in spawns] != [("0A", "01"), ("0A", "01")]:
        errs.append("eez spawn ops")
    z = st["zones"]
    if sorted(z) != ["0", "1", "2", "3", "4", "5"]:
        errs.append("zone records")
    g = st["g0_spine_disclosure"]
    if len(g["rows"]) != 18 or g["natural_sign_chain"] != 2:
        errs.append("g0 disclosure")
    if [(r["zone"], r["act"]) for r in g["rows"] if r["act"] == 2] != [(zn, 2) for zn in range(6)]:
        errs.append("g0 act-3 rows")
    for r in st["routines"]:
        if len(r["sha256"]) != 64:
            errs.append("hash " + r["name"])
    s0 = [o["op"] for o in st["bonus_object_0A"]["script_state0"]]
    if s0 != ["record", "restart_state"]:
        errs.append("0A state 0 script")
    return errs


def validate_controlled(ctl, st):
    errs = []
    rows = ctl["release"]["rows"]
    by = lambda t, fl, px: next(r for r in rows if r["type_before"] == t and r["floor"] == fl and r["player_x"] == px)
    for t, px in (("50", 3000), ("54" if False else "50", 3000)):
        pass
    for t, px in (("50", 3000), ("54", 3000), ("59", 3000), ("56", 3356), ("56", 3500)):
        r = by(t, 2, px)
        if not (r["boss_type_after"] == "0F" and r["player_requested_state"] == "20" and r["sound"] == "97" and [c["type"] for c in r["created"]] == ["0A"] and r["created"][0]["parameter"] == 0 and r["D2A6"] == 0 and r["right_limit"] == 2304):
            errs.append("release %s" % t)
        if by(t, 0, px)["boss_type_after"] != t or by(t, 0, px)["created"]:
            errs.append("release without floor %s" % t)
    if by("56", 2, 3355)["created"] or by("56", 2, 3355)["boss_type_after"] != "56":
        errs.append("mghz x gate")
    if by("56", 2, 3356)["left_limit"] != 0 or by("50", 2, 3000)["left_limit"] != 3060:
        errs.append("mghz left limit write")
    g = by("51", 2, 1700)
    if not (g["boss_type_after"] == "FF" and g["player_requested_state"] == "20" and [c["type"] for c in g["created"]] == ["0A"] and g["right_limit"] == 1920):
        errs.append("gpz release")
    if by("51", 0, 1700)["created"]:
        errs.append("gpz floor gate")
    if ctl["release_act_index_sound"] != {"0": "89", "1": "89", "2": "97"}:
        errs.append("state 20 sound")
    af = ctl["allocation_failure"]
    if af["created"] or af["boss_type_after"] != "0F" or af["player_requested_state"] != "20" or af["D2A6"] != 0:
        errs.append("allocation failure")
    p = {r["parameter"]: r for r in ctl["bonus_object_parameters"]["rows"]}
    if p["00"]["D2A6"] != "0936" or any(p[k]["D2A6"] != "BEEF" for k in ("01", "80", "FF")) or any(r["lives"] != "12" for r in p.values()):
        errs.append("0A parameters")
    if ctl["bonus_word_grid"]["model_mismatches"]:
        errs.append("bonus grid")
    tt = time_table_of_u3()
    for tm, row in ctl["bonus_word_grid"]["rows"].items():
        for n, w in enumerate(row):
            if model_bonus_word(tt, int(tm, 16), (n // 10) * 16 + n % 10) != w:
                errs.append("grid cell %s %d" % (tm, n))
                break
    if ctl["bonus_word_grid"]["zero_words_left_as_zero"] != [["0459", "11"], ["0900", "11"]]:
        errs.append("zero words")
    return errs


def _int_to_bcd(n):
    return ((n // 10) << 4) | (n % 10)


def validate_observed(ob, st):
    errs = []
    fixed = st["fixed_boss_bonus"]["raw_units"]
    tt = time_table_of_u3()
    for key, r in ob["fights"].items():
        zone = r["zone"]
        c = r["counts"]
        if zone < 5:
            if (c["boss_bonus_loop"], c["tally_loops"], c["results_card"], c["zone_increment"], c["bonus_objects_param0"], c["D2A6_sets"], c["flag_bit4_set"]) != (1, 1, 1, 1, 1, 1, 1):
                errs.append("%s counts %s" % (key, c))
            sc = r.get("score")
            if not sc:
                errs.append(key + ": no score record")
                continue
            if sc["fixed_bonus"] != fixed[zone]:
                errs.append("%s fixed bonus %s" % (key, sc["fixed_bonus"]))
            if sc["tally_total"] != sc["ring_units"] + sc["word_units"]:
                errs.append("%s tally %s != rings %s + word %s" % (key, sc["tally_total"], sc["ring_units"], sc["word_units"]))
            if r["retained"]["score_after"] - r["retained"]["score_before"] != sc["fixed_bonus"] + sc["tally_total"]:
                errs.append(key + ": score delta")
            comp = r["bonus_compute_inputs"]
            sets = r["D2A6_sets"]
            if len(comp) != 1 or len(sets) != 1:
                errs.append(key + ": compute/set")
            else:
                tm = comp[0]["time"][0] << 8 | comp[0]["time"][1]
                if model_bonus_word(tt, tm, comp[0]["rings"]) != sets[0]["word"]:
                    errs.append("%s D2A6 %04X vs model %04X" % (key, sets[0]["word"], model_bonus_word(tt, tm, comp[0]["rings"])))
            if r["retained"]["zone_act_after"] != [zone + 1, 0] or r["retained"]["lives"][0] != r["retained"]["lives"][1] or r["retained"]["continues"][0] != r["retained"]["continues"][1] or \
                    r["retained"]["emeralds"][0] != r["retained"]["emeralds"][1]:
                errs.append(key + ": retained state")
            tf = r["tail_frames"]
            order = ["zone_clear_tail", "zone_results_gate", "results_card", "boss_bonus_loop", "tally_loops", "zone_increment"]
            if not all(tf[a][0] <= tf[b][0] for a, b in zip(order, order[1:])):
                errs.append(key + ": tail order")
            st20 = [s for s in r["state20_requests"] if s["bank"] == BANK_BOSS]
            if len(st20) < 1 or st20[0]["act_index"] != 2:
                errs.append(key + ": state 20 request")
            if r["bonus_objects_created"] and r["state20_requests"] and min(f for f, p in r["bonus_objects_created"] if p == 0) < min(s["frame"] for s in st20):
                errs.append(key + ": $0A before the state-$20 request")
            ns = r.get("next_start")
            q = rq4_start(zone + 1)
            if not ns or not q or ns["player"] != q["player"]:
                errs.append("%s next start %s vs %s" % (key, ns, q and q["player"]))
        else:
            if c["boss_bonus_loop"] or c["results_card"] or c["tally_loops"] or c["bonus_objects_param0"] or c["D2A6_sets"]:
                errs.append("%s: EEZ must have no results, fixed bonus or $0A parameter 0" % key)
            if not r["tail_frames"].get("ending_selector") or not r["tail_frames"].get("title_entry") or r["tail_frames"].get("results_card"):
                errs.append(key + ": EEZ terminal route")
            branch = {"EEZ3_sonic_flags1F": "ending_full_sonic", "EEZ3_sonic_flags00": "ending_partial_sonic", "EEZ3_sonic_flags3F": "ending_full_sonic"}[key]
            if not r["tail_frames"].get(branch):
                errs.append("%s: expected %s" % (key, branch))
            if r["retained"]["emeralds"][1] & 0x3F != (0x3F if "full" in branch else r["retained"]["emeralds"][1] & 0x3F):
                errs.append(key + ": emerald byte")
    for key, r in ob["injected_clears"].items():
        zone = r["zone"]
        sc = r.get("score")
        if r["bonus_objects_created"] or r["D2A6_sets"] or r["state20_requests"]:
            errs.append(key + ": an injected clear must have no $0A, no D2A6 write and no boss state-$20 request")
        if not sc or sc["fixed_bonus"] != fixed[zone] or sc["tally_total"] != sc["ring_units"] or sc["word_units"] != 0:
            errs.append("%s injected score %s" % (key, sc))
        if r["retained"]["zone_act_after"] != [zone + 1, 0]:
            errs.append(key + ": injected rollover")
    return errs


# ------------------------------------------------------------------------------------------------------------------------------------------
# Generation and checks
def write_all(rom, only=None, progress=print):
    DATA.mkdir(parents=True, exist_ok=True)
    st = build_static(rom)
    STATIC_JSON.write_text(dumps(st), encoding="utf-8", newline="\n")
    ctl = build_controlled(rom, st)
    CONTROLLED_JSON.write_text(dumps(ctl), encoding="utf-8", newline="\n")
    if only == "static":
        return
    ob = build_observed(rom, st, progress=progress)
    ob["injected_clears"] = build_injected(rom, progress=progress)
    OBS_JSON.write_text(dumps(ob), encoding="utf-8", newline="\n")


def check_all(rom, progress=print):
    problems = []
    st = build_static(rom)
    if dumps(st) != STATIC_JSON.read_text(encoding="utf-8"):
        problems.append("static census differs from the committed file")
    ctl = build_controlled(rom, st)
    if dumps(ctl) != CONTROLLED_JSON.read_text(encoding="utf-8"):
        problems.append("controlled results differ from the committed file")
    problems += validate_controlled(ctl, st)
    ob = build_observed(rom, st, progress=progress)
    ob["injected_clears"] = build_injected(rom, progress=progress)
    if dumps(ob) != OBS_JSON.read_text(encoding="utf-8"):
        problems.append("observations differ from the committed file")
    problems += validate_observed(ob, st)
    return problems


# ------------------------------------------------------------------------------------------------------------------------------------------
# Generated tables for the specification
_MARK = "<!-- %s u2:%s -->"


def _md(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |" for r in rows]
    return "\n".join(out)


FIGHT_ORDER = ["THZ3", "GPZ3", "SEZ3", "MGHZ3", "AQZ3", "EEZ3_sonic_flags1F", "EEZ3_sonic_flags00", "EEZ3_sonic_flags3F"]
INJECTED_ORDER = ["%s3_injected_flag" % z for z in ZONES[:5]]


def doc_tables(st, ctl, ob):
    t = {}
    t["routines"] = _md([("`%s`" % r["name"], ("%02X:" % r["bank"] if r["bank"] is not None else "res ") + "$%s-$%s" % (r["cpu_start"], r["cpu_end_exclusive"]), "0x%s" % r["file_start"], r["length"],
                          "`%s`" % r["sha256"][:12], r["role"]) for r in st["routines"]], ("routine", "CPU range (end exclusive)", "file", "bytes", "SHA-256", "role"))
    rows = []
    for k in "012345":
        z = st["zones"][k]
        rows.append((z["zone"] + "3", "$" + z["controller"], z["producer"], z["owner_state"], z["gate"]))
    t["producers"] = _md(rows, ("zone", "controller", "defeat/clear producer", "state", "release gate"))
    fb = st["fixed_boss_bonus"]
    t["fixed_bonus"] = _md([(ZONES[i], fb["steps"][i], fb["raw_units"][i], "used" if i < 5 else "never reached (results skipped)") for i in range(6)], ("zone", "steps of 10 raw", "raw units", "status"))
    obs = []
    for key, r in [(k, ob["fights"][k]) for k in FIGHT_ORDER]:
        sc = r.get("score")
        tf = r["tail_frames"]
        if r["zone"] < 5:
            obs.append((key, r["bonus_objects_created"][0][0] if r["bonus_objects_created"] else "-", "$%04X" % r["D2A6_sets"][0]["word"], r["state20_requests"][0]["frame"] if r["state20_requests"] else "-", tf["flag_bit4_set"][0],
                        tf["results_card"][0], sc["fixed_bonus"], sc["ring_units"], sc["word_units"], sc["tally_total"], "%d/%d -> %d/%d" % tuple(r["retained"]["zone_act_before"] + r["retained"]["zone_act_after"])))
        else:
            obs.append((key, "-", "-", "-", "-", "-", 0, 0, 0, 0, "%d/%d -> %d/%d" % tuple(r["retained"]["zone_act_before"] + r["retained"]["zone_act_after"])))
    t["observed"] = _md(obs, ("fight", "$0A param 0 frame", "D2A6", "state-$20 request", "flag bit 4", "results card", "fixed bonus", "ring units", "word units", "tally total", "zone/act"))
    inj = []
    for key, r in [(k, ob["injected_clears"][k]) for k in INJECTED_ORDER]:
        sc = r["score"]
        inj.append((key, len(r["bonus_objects_created"]), len(r["D2A6_sets"]), sc["fixed_bonus"], sc["ring_units"], sc["word_units"], sc["tally_total"]))
    tl = []
    for key, r in [(k, ob["fights"][k]) for k in FIGHT_ORDER]:
        o = r["frames_relative_to_defeat"]["offsets"]
        g = lambda n: o[n][0] if n in o and o[n] else "-"
        tl.append((key, g("state20_request"), g("D2A6_set"), g("flag_bit4_set"), g("zone_clear_tail"), g("results_card"), g("boss_bonus_loop"), g("tally_loops"), g("zone_increment"), g("ending_selector"), g("title_entry")))
    t["timeline"] = _md(tl, ("fight", "$03F5 request", "D2A6 set", "flag bit 4 ($83ED)", "$1543", "results card", "$2D55 fixed bonus", "$2D08 tally", "zone increment $15CE", "ending selector", "title"))
    t["injected"] = _md(inj, ("injected clear", "$0A objects", "D2A6 writes", "fixed bonus", "ring units", "word units", "tally total"))
    eez = []
    for key in ("EEZ3_sonic_flags1F", "EEZ3_sonic_flags00", "EEZ3_sonic_flags3F"):
        r = ob["fights"][key]
        tf = r["tail_frames"]
        branch = next((n for n in ("ending_full_sonic", "ending_partial_sonic", "ending_other_character") if n in tf), "-")
        eez.append((key, "$%02X" % r["emerald_flags_in"], "$%02X" % next((w[2] for w in r["D293_writes"] if w[2] == 0x50), 0), "yes" if "results_card" in tf else "no", branch, "$%02X" % r["retained"]["emeralds"][1]))
    t["eez"] = _md(eez, ("variant", "D2CC in", "last clear write D293", "results card", "ending branch", "D2CC out"))
    return t


def refresh_doc(path=DOC, st=None, ctl=None, ob=None):
    st, ctl, ob = st or load_json(STATIC_JSON), ctl or load_json(CONTROLLED_JSON), ob or load_json(OBS_JSON)
    text = Path(path).read_text(encoding="utf-8")
    for name, body in doc_tables(st, ctl, ob).items():
        a, b = _MARK % ("BEGIN", name), _MARK % ("END", name)
        if a not in text:
            continue
        i, j = text.index(a) + len(a), text.index(b)
        text = text[:i] + "\n" + body + "\n" + text[j:]
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--only", choices=["static"])
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--doc", action="store_true", help="refresh the generated tables inside docs/u2-act3-boss-bonus.md from the committed JSON")
    a = ap.parse_args(argv)
    if a.doc:
        refresh_doc()
        return 0
    if a.validate:
        st = load_json(STATIC_JSON)
        errs = validate_static(st) + validate_controlled(load_json(CONTROLLED_JSON), st) + validate_observed(load_json(OBS_JSON), st)
        print("OK" if not errs else "\n".join(errs))
        return 1 if errs else 0
    rom = load_rom(a.rom or os.environ.get("SONIC_CHAOS_ROM") or ROOT.parent / "source" / "Sonic Chaos (Europe).sms")
    if a.check:
        problems = check_all(rom)
        print("U2 check: OK" if not problems else "\n".join(problems))
        return 1 if problems else 0
    write_all(rom, only=a.only)
    print("wrote", STATIC_JSON, CONTROLLED_JSON, "" if a.only else OBS_JSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())

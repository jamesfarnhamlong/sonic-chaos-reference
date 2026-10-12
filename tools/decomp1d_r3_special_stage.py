#!/usr/bin/env python3
"""DECOMP-1D-R3: special-stage completion (U1) and invalid-record reachability (U3).

    python tools/decomp1d_r3_special_stage.py /path/to/SonicChaos.sms [--output data/decomp1d/r3-special-stage-reachability.json]
                                              [--controlled] [--doc docs/decomp-1d-r3-special-stage-reachability.md] [--check]

DECOMP-1D-R2 left two dependencies open:

* U1 - can ``$D293`` bit 4 (zone complete) be raised while the game runs a special stage ($D297 in 8..12)?
* U3 - what does a special stage do when the level loader ``$2A4F`` selects a record outside the nine verified ones, and can
  such a stage be left?

Method (everything is derived from the canonical ROM; nothing is taken from the POC or from external lists):

1. ``setter_sites``       the three flag writers decoded in place, with their physical offset, bank and CPU address.
2. ``object_universe``    every object type's state table and every script callback, parsed the way the animation engine
                          reads them (the DECOMP-1C parser, parameterised by bank).
3. ``provenance``         which (type, state, callback) can reach each setter, by recursive descent confined to the bank the
                          scheduler pages in; the level-clear routine ``$4892`` and its callers; writers of the player state.
4. ``creation``           how an object of each type can come to exist (placement list, ``FF 04`` child, allocator, in-place
                          conversion) and the closure of that relation from the types a special stage places.
5. ``placement``          the object-list table of bank ``$1C`` for every zone/act, resolved with the mapper state its
                          reader runs under.
6. ``dispatch``           the main-loop dispatcher executed over every flag combination (priority, masked bits) and the
                          effect of the zone-complete path with ``$D297`` in 8..12.
7. ``loader``             the record chain of ``$2A4F`` for every special-stage zone and every 8-bit act, the mapper state
                          at its dereferences, the bytes it consumes and the routines the slot types select.
8. ``controlled``         (optional, slow) the original Z80 code run in the DECOMP harness from a forced stage entry.

Executed lemmas use the fail-closed interpreter of DECOMP-1D-R2 (extended here, additively, with the index registers).
Controlled execution proves a result *for the state it is given*; it does not show that the state is reachable.
"""
import argparse
import contextlib
import hashlib
import json
import os
import re
import sys
from collections import OrderedDict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1d_r2_zone_act as R2  # noqa: E402
import player_scripts as P  # noqa: E402
import rom_flow as F  # noqa: E402
from z80dis import z80  # noqa: E402

OUTPUT = ROOT / "data" / "decomp1d" / "r3-special-stage-reachability.json"
DOC = ROOT / "docs" / "decomp-1d-r3-special-stage-reachability.md"
BASE_COMMIT = "fcdfb58861787e242cf3732e301ddd3a25cb79f8"
ROM_SIZE = 524288
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"

BANK = 0x4000
ZONE, ACT, SAVED_ZONE = R2.ZONE, R2.ACT, R2.SAVED_ZONE
STATE_FLAGS, SPECIAL_FLAGS = R2.STATE_FLAGS, R2.SPECIAL_FLAGS
EMERALDS = R2.EMERALDS
SS_ZONES = (8, 9, 10, 11, 12)
SS_ENTRY = 0x178F
LOADER = R2.LOADER
LEVEL_CLEAR_STUB, LEVEL_CLEAR = 0x03F5, 0x4892
OBJECT_TYPE_TABLE = P.TYPE_TABLE                  # $65BA
PLACEMENT_BANK = 0x1C
PLACEMENT_TABLE = 0x8546                          # zone pointer table, bank $1C slot 2
SLOT_DISPATCH_BANK = 0x1D
SLOT_DISPATCH_TABLE = 0x8028
HEADER_TABLE = 0x5082                             # level header table read by $4FDC (slot 1)
RECORD_FIELDS = ("D2E0", "D399", "D39B", "D452", "D45A", "D462", "D46A")
hx = R2.hx

# The three writers of $D293 bit 4 that DECOMP-1D-R2 found (physical ROM offsets).
SETTER_OFFSETS = (0x303ED, 0x7BB2A, 0x7BB6E)
LEVEL_CLEAR_CALLERS = (0x32B9B, 0x781DF, 0x79D55)  # CALL/JP $03F5 sites found by byte search (re-derived below)


class Unresolved(Exception):
    """A value needs state (a bank, RAM contents) that no ROM-derived argument supplies."""


# --- 0. an additive extension of the fail-closed interpreter ---------------------------------------------------------
_IDX = re.compile(r"^\((IX|IY)(?:\+(0x[0-9a-fA-F]+|\d+))?\)$")


class Interp3(R2.Interp):
    """``R2.Interp`` plus ``IX``/``IY`` (as 16-bit registers) with ``(IX+d)``/``(IY+d)`` operands, ``LD IX/IY,nn``,
    ``PUSH``/``POP`` and ``LD (nn),rr`` forms the base class already has. Everything else still raises ``Unmodelled``."""

    def __init__(self, *a, ix=0, iy=0, **k):
        super().__init__(*a, **k)
        self.ix, self.iy = ix & 0xFFFF, iy & 0xFFFF

    def file_of(self, cpu):
        """Mapper semantics of this task (premise P-M2): a bank register value is taken modulo the number of 16 KB banks of the
        image (32), as the address lines of a 512 KB cartridge allow. R2's interpreter did not need this."""
        banks = len(self.rom) // BANK
        if cpu < 0x4000:
            return cpu
        if cpu < 0x8000:
            if self.slot1 is None:
                raise R2.Unmodelled("slot-1 bank unverified at $%04X" % cpu)
            return (self.slot1 % banks) * BANK + cpu - 0x4000
        if cpu < 0xC000:
            if self.slot2 is None:
                raise R2.Unmodelled("slot-2 bank unverified at $%04X" % cpu)
            return (self.slot2 % banks) * BANK + cpu - 0x8000
        return None

    def _idx_addr(self, operand):
        m = _IDX.match(operand.strip())
        if not m:
            return None
        base = self.ix if m.group(1) == "IX" else self.iy
        disp = int(m.group(2), 0) if m.group(2) else 0
        return (base + disp) & 0xFFFF

    def val(self, operand):
        a = self._idx_addr(operand)
        return self.read(a) if a is not None else super().val(operand)

    def put8(self, operand, value):
        a = self._idx_addr(operand)
        if a is not None:
            self.write(a, value)
        else:
            super().put8(operand, value)

    def step(self):
        f = self.file_of(self.pc)
        if f is None:
            raise R2.Unmodelled("pc in RAM $%04X" % self.pc)
        d = z80.decode(bytes(self.rom[f:f + 4]), self.pc)
        if not d.len or d.op == F.OP.NONI:
            raise R2.Unmodelled("undecodable at $%04X" % self.pc)
        text = z80.disasm(d)
        mn, _, rest = text.partition(" ")
        ops = [o.strip() for o in re.split(r",(?![^()]*\))", rest)] if rest else []
        mn = mn.upper()
        if mn == "LD" and len(ops) == 2 and ops[0] in ("IX", "IY") and not ops[1].startswith("("):
            if ops[0] == "IX":
                self.ix = int(ops[1], 0) & 0xFFFF
            else:
                self.iy = int(ops[1], 0) & 0xFFFF
            self.pc += d.len
            self.steps += 1
            return text
        if mn in ("PUSH", "POP") and ops[0] in ("IX", "IY", "HL", "DE", "BC"):
            self.steps += 1
            if mn == "PUSH":
                self.stack.append(self.ix if ops[0] == "IX" else self.iy if ops[0] == "IY" else self.get16(ops[0]))
            else:
                v = self.stack.pop()
                if ops[0] == "IX":
                    self.ix = v
                elif ops[0] == "IY":
                    self.iy = v
                else:
                    self.set16(ops[0], v)
            self.pc += d.len
            return text
        return super().step()


def execute3(rom, start, ram, slot1=1, slot2=None, stops=(), regs=None, ix=0, iy=0, limit=400):
    m = Interp3(rom, ram=ram, slot1=slot1, slot2=slot2, regs=regs, ix=ix, iy=iy)
    why = m.run(start, stops, limit=limit)
    return m, why


# --- 1. the ROM ------------------------------------------------------------------------------------------------------
def verify_rom(rom):
    if len(rom) != ROM_SIZE:
        raise ValueError("ROM size %d, expected %d" % (len(rom), ROM_SIZE))
    got = hashlib.sha256(rom).hexdigest()
    if got != ROM_SHA256:
        raise ValueError("ROM SHA-256 %s is not the canonical Europe image" % got)
    return got


def word(rom, off):
    return rom[off] | rom[off + 1] << 8


def bank_of(off):
    return off // BANK


def context_of(off):
    """Mapper context of a physical offset: resident code (banks 0/1, slots 0/1) or a bank paged into slot 2."""
    if off < 0x4000:
        return OrderedDict([("bank", 0), ("slot", 0), ("cpu", off)])
    if off < 0x8000:
        return OrderedDict([("bank", 1), ("slot", 1), ("cpu", off), ("premise", "slot 1 holds bank 1 (DECOMP-1D R3)")])
    return OrderedDict([("bank", off // BANK), ("slot", 2), ("cpu", 0x8000 + off % BANK)])


def slot2_off(bank, cpu):
    return bank * BANK + cpu - 0x8000


# --- 2. the three setter sites ---------------------------------------------------------------------------------------
def decode_site(rom, off):
    d = F.decode(rom, off)
    return d, z80.disasm(d)


# (feeder offset, site offset): execution starts at the feeder so the value stored is the one the code builds
SETTER_FEEDERS = {0x303ED: 0x303EA, 0x7BB2A: 0x7BB28, 0x7BB6E: 0x7BB6C}


def setter_sites(rom):
    """Decode the three bit-4 writers in place and execute their local flag effect from an empty flag byte."""
    rows = []
    for off in SETTER_OFFSETS:
        d, text = decode_site(rom, off)
        ctx = context_of(off)
        feeder = SETTER_FEEDERS[off]
        fctx = context_of(feeder)
        m = Interp3(rom, ram={STATE_FLAGS: 0}, slot1=1, slot2=bank_of(off))
        m.run(fctx["cpu"], stops=(ctx["cpu"] + d.len,))
        effect = m.ram[STATE_FLAGS]
        fd, ftext = decode_site(rom, feeder)
        rows.append(OrderedDict([("file_offset", off), ("bank", ctx["bank"]), ("slot", ctx["slot"]), ("cpu", ctx["cpu"]),
                                 ("bytes", rom[off:off + d.len].hex()), ("asm", text), ("feeder_asm", ftext),
                                 ("d293_after_from_zero", effect), ("raises_bit_4", bool(effect & 0x10))]))
    return rows


_CACHE = {}


def _cached(key, rom, fn):
    k = (key, hashlib.sha256(rom).hexdigest())
    if k not in _CACHE:
        _CACHE[k] = fn()
    return _CACHE[k]


def bit4_census(rom):
    """Re-derive the writers of $D293 bit 4 with the R2 flag-setter scan, plus every immediate materialisation of the address (HL, DE, BC,
    IX, IY and the $E000 mirror) with the instructions that follow, so the three sites are found, not assumed."""
    code = _cached("code", rom, lambda: R2.Code(rom))
    setters = R2.flag_setters(rom, code, STATE_FLAGS)
    rows = R2.bit_effects(rom, code, setters)
    raisers = R2.setters_of_bit(rows, 4)
    mats = []
    for pat, name in ((b"\x21\x93\xd2", "LD HL"), (b"\x11\x93\xd2", "LD DE"), (b"\x01\x93\xd2", "LD BC"), (b"\xdd\x21\x93\xd2", "LD IX"),
                      (b"\xfd\x21\x93\xd2", "LD IY"), (b"\x21\x93\xf2", "LD HL (mirror)"), (b"\x32\x93\xf2", "LD (nn),A (mirror)")):
        i = rom.find(pat)
        while i != -1:
            seq, p = [], i
            for _ in range(2):
                d = F.decode(rom, p)
                seq.append(z80.disasm(d))
                p += d.len
            mats.append(OrderedDict([("file_offset", i), ("form", name), ("next", seq[1])]))
            i = rom.find(pat, i + 1)
    return OrderedDict([("bit4_raisers", raisers), ("matches_setter_sites", raisers == sorted(SETTER_OFFSETS)),
                        ("absolute_stores", len(setters["absolute_stores"])), ("hl_bit_ops", len(setters["hl_bit_ops"])),
                        ("wide_stores", setters["wide_stores"]),
                        ("materialisations", mats), ("materialisation_forms_other_than_hl", sorted({m["form"] for m in mats} - {"LD HL"}))])


def bit4_survival(rom, uni):
    """Writers that can *remove* ``$D293`` bit 4 (``RES 4``, or a store whose value lacks bit 4 or is unknown) and which of them
    run in the stage's per-frame code, in the callbacks of the types a stage places and of the players, or inside the IM 1 closure.
    Only the main-loop handlers themselves clear it, after the dispatcher has acted."""
    code = _cached("code", rom, lambda: R2.Code(rom))
    rows = R2.bit_effects(rom, code, R2.flag_setters(rom, code, STATE_FLAGS))
    clears = [r for r in rows if ("clears" in r and 4 in r["clears"]) or ("assigns" in r and (r["assigns"] is None or not (r["assigns"] >> 4) & 1))]
    frame, _ind, _s2 = resident_reach(rom, [0x16B8, 0x173F], {})
    stage_types = (1, 2, 0x10, 0x26, 0x2F, 0x31)
    in_types, _o, _s = callback_closure(rom, uni, stage_types)
    inside_irq = {w["file_offset"] for w in interrupt_closure_writers(rom)["d293_writers_inside"]}
    off = [r["file_offset"] for r in clears]
    return OrderedDict([("bit4_clearing_writers", [OrderedDict([("file_offset", r["file_offset"]), ("op", r["op"])]) for r in clears]),
                        ("in_frame_update_closure", [o for o in off if o in frame]),
                        ("in_stage_object_closures", [o for o in off if o in in_types]),
                        ("in_im1_closure", [o for o in off if o in inside_irq])])


def interrupt_closure_writers(rom):
    """Do any writers of the two state-flag bytes run inside the IM 1 closure (DECOMP-1D R1/R2 conditional walk)? An asynchronous
    clear of D293 bit 4 would need one."""
    def compute():
        code = _cached("code", rom, lambda: R2.Code(rom))
        walk = R2.irq_closure(rom)
        visited = set(walk["visited"])
        out = OrderedDict([("closure_instructions", len(visited))])
        for name, addr in (("d293", STATE_FLAGS), ("d294", SPECIAL_FLAGS)):
            rows = R2.bit_effects(rom, code, R2.flag_setters(rom, code, addr))
            out["%s_writers_inside" % name] = [OrderedDict([("file_offset", r["file_offset"]), ("op", r["op"])]) for r in rows
                                               if r["file_offset"] in visited]
        return out
    return _cached("irq", rom, compute)


# --- 3. the object universe ------------------------------------------------------------------------------------------
@contextlib.contextmanager
def script_bank(bank):
    old = P.SCRIPT_BANK
    P.SCRIPT_BANK = bank
    try:
        yield
    finally:
        P.SCRIPT_BANK = old


def type_bank(t):
    """Bank the scheduler pages in for type ``t`` (``$5DF1``: types below $26 use bank 12, $26..$EF bank $1E)."""
    return 12 if t < 0x26 else 0x1E


def scheduler_facts(rom):
    """The bank selection of the object scheduler ``$5DF1``, decoded from the ROM: types below the compare constant page
    bank 12, the rest page bank $1E (types ``$F0+`` take a separate table)."""
    expect = (("compare", 0x5DFD, "CP 0x26"), ("low_bank", 0x5E06, "LD A,12"), ("high_bank", 0x5E36, "LD A,0x1e"),
              ("special_split", 0x5DF6, "CP 0xf0"))
    out = OrderedDict()
    for name, off, want in expect:
        got = decode_site(rom, off)[1]
        if got != want:
            raise ValueError("scheduler %s at $%04X is %r, expected %r" % (name, off, got, want))
        out[name] = OrderedDict([("file_offset", off), ("asm", got)])
    return out


def type_count(rom):
    """Entries of the type table at $65BA whose word points into slot 2 ($8000-$BFFF); the table ends at the first that does not."""
    n = 0
    while 0x8000 <= word(rom, OBJECT_TYPE_TABLE + 2 * n) < 0xC000:
        n += 1
    return n


def state_table(rom, ty, bases):
    """(table_cpu, [script cpu per state]) of a type: the table ends where the lowest script it points at starts, and never
    runs into the next distinct table (some types keep their scripts below the table)."""
    bank = type_bank(ty)
    base = word(rom, OBJECT_TYPE_TABLE + 2 * (ty - 1))
    with script_bank(bank):
        first = word(rom, P.file_offset(base))
        higher = [b for b in bases if b > base]
        limit = ((higher[0] if higher else 0xC000) - base) // 2
        n = min(limit, (first - base) // 2) if first > base else limit
        while True:
            ws = [word(rom, P.file_offset(base + 2 * i)) for i in range(n)]
            plausible = [w for w in ws if base <= w < 0xC000]
            if not plausible:
                break
            m = min((min(plausible) - base) // 2, n)
            if m == n:
                break
            n = m
        ws = [word(rom, P.file_offset(base + 2 * i)) for i in range(n)]
    return base, ws


def object_universe(rom):
    """Parse every type's scripts. Returns ``{type: {bank, table, states: [{script, callbacks, steps, notes}]}}``."""
    n_types = type_count(rom)
    commands = P.derive_commands(rom)
    by_bank = {}
    for ty in range(1, n_types + 1):
        by_bank.setdefault(type_bank(ty), set()).add(word(rom, OBJECT_TYPE_TABLE + 2 * (ty - 1)))
    uni = OrderedDict()
    for ty in range(1, n_types + 1):
        bank = type_bank(ty)
        base, scripts = state_table(rom, ty, sorted(by_bank[bank]))
        states = []
        with script_bank(bank):
            for s in scripts:
                notes = []
                steps, cbs = P.parse_script(rom, s, commands, notes)
                states.append(OrderedDict([("script", s), ("steps", steps), ("callbacks", cbs), ("notes", notes)]))
        uni[ty] = OrderedDict([("bank", bank), ("table", base), ("states", states)])
    return uni, commands


def callback_vectors(entry):
    """Slot-2 words a type's scripts make the engine execute (record callbacks, FF 05/0D vectors, executed operands)."""
    vecs = OrderedDict()
    for st, state in enumerate(entry["states"]):
        for c in state["callbacks"]:
            for key in ("vector", "selector"):
                v = c[key]
                if v and 0x8000 <= v < 0xC000:
                    vecs.setdefault(v, []).append(st)
    return vecs


def descend_bank(rom, bank, entries):
    lo, hi = bank * BANK, (bank + 1) * BANK
    seeds = [lo + e - 0x8000 for e in entries]
    return F.descend(rom, seeds, lo, hi)


def reach_map(rom, uni, targets):
    """For each target file offset: the (type, state, vector) callbacks whose descent reaches it, plus the computed jumps
    the descent could not follow (those make a 'not reached' claim partial)."""
    out = OrderedDict((t, []) for t in targets)
    cache = {}
    for ty, entry in uni.items():
        for v, sts in callback_vectors(entry).items():
            key = (entry["bank"], v)
            if key not in cache:
                cache[key] = descend_bank(rom, entry["bank"], [v])
            reached, notes = cache[key]
            for t in targets:
                if t in reached:
                    out[t].append(OrderedDict([("type", ty), ("states", sorted(set(sts))), ("vector", v),
                                               ("bank", entry["bank"]), ("instructions", len(reached))]))
    return out


def script_vectors_naming(uni, targets):
    """Script callbacks/selectors (any window) that equal one of ``targets``: a callback vector naming a routine is an entry the
    byte search for CALL/JP would miss."""
    out = []
    for ty, entry in uni.items():
        for st, state in enumerate(entry["states"]):
            for c in state["callbacks"]:
                for key in ("vector", "selector"):
                    if c[key] in targets:
                        out.append(OrderedDict([("type", ty), ("state", st), ("field", key), ("value", c[key])]))
    return out


def level_clear_callers(rom):
    """Every encoding of CALL/JP $03F5 and CALL/JP $4892 in the image (byte search, so alignment hides nothing)."""
    rows = []
    for target in (LEVEL_CLEAR_STUB, LEVEL_CLEAR):
        for op, name in ((0xCD, "CALL"), (0xC3, "JP")):
            pat = bytes([op, target & 0xFF, target >> 8])
            i = rom.find(pat)
            while i != -1:
                rows.append(OrderedDict([("file_offset", i), ("op", name), ("target", target), ("context", context_of(i))]))
                i = rom.find(pat, i + 1)
    return rows


# --- 4. provenance of the player-state route -------------------------------------------------------------------------
def resident_reach(rom, roots, cache):
    """Instructions of the resident engine (file offsets below $8000) reachable from ``roots``; transfers into slot 2 from
    resident code are recorded, not followed (the bank would be ambiguous)."""
    reached, indirect, slot2 = {}, set(), set()
    work = sorted(roots)
    seen = set()
    while work:
        t = work.pop()
        if t in seen or t >= 0x8000:
            continue
        seen.add(t)
        if t not in cache:
            cache[t] = F.descend(rom, [t], 0, 0x8000)
        r, notes = cache[t]
        reached.update(r)
        indirect.update(n[1] for n in notes if n[0] == "indirect")
        for off in r:
            d = F.decode(rom, off)
            if d.op in F.TRANSFER_OPS:
                tg = F._addr_operand(d)
                if tg is None:
                    continue
                if tg < 0x8000:
                    work.append(tg)
                elif tg < 0xC000:
                    slot2.add(off)
    return reached, sorted(indirect), sorted(slot2)


# Table-indexed computed jumps inside object code. Each entry is checked against the instructions that build the index before it is
# believed (``jump_destinations``); ``bound`` names the instruction that limits the index, or None when only the table extent does.
JUMP_SPECS = OrderedDict([
    (0x5FB8, dict(bank=None, tables=[0x5FB9], entries=16, skip_first=True, bound="AND 15 / RET z (index 0 returns)",
                  pattern=["LD A,(IX+0x21)", "AND 15", "RET z", "ADD A,A", "LD E,A", "LD D,0", "LD HL,0x5fb9", "ADD HL,DE",
                           "LD A,(HL)", "INC HL", "LD H,(HL)", "LD L,A", "JP (HL)"], start=0x5FA6)),
    (0x6972, dict(bank=None, tables=[0x6973], entries=32, skip_first=False, bound="AND 0x1f",
                  pattern=["LD A,(0xd364)", "LD (0xd36c),A", "AND 0x1f", "ADD A,A", "LD L,A", "LD H,0", "LD DE,0x6973", "ADD HL,DE",
                           "LD E,(HL)", "INC HL", "LD D,(HL)"], start=0x695E)),
    (0x77EC, dict(bank=None, tables=[0x77ED], entries=32, skip_first=False, bound="AND 0x1f",
                  pattern=["LD A,(0xd364)", "AND 0x1f", "ADD A,A", "LD L,A", "LD H,0", "LD DE,0x77ed", "ADD HL,DE", "LD E,(HL)",
                           "INC HL", "LD D,(HL)", "EX DE,HL", "JP (HL)"], start=0x77DB)),
    (0x311BB, dict(bank=12, tables=[0x91BC], entries=16, skip_first=False, bound="SUB 0x74 / JP c / CP 0x10 / JR nc",
                   pattern=["LD A,B", "ADD A,A", "LD E,A", "LD D,0", "LD HL,0x91bc", "ADD HL,DE", "LD A,(HL)", "INC HL", "LD H,(HL)",
                            "LD L,A", "JP (HL)"], start=0x91AE,
                   bound_pattern=["LD A,(0xd36d)", "SUB 0x74", "LD B,A", "JP c,0x91e2", "CP 0x10", "JR nc,0x91e2", "JP 0x91ae"], bound_start=0x9198)),
    (0x314F4, dict(bank=12, tables=None, entries=28, skip_first=False, bound=None,
                   pattern=["LD A,(IX+0x38)", "AND 3", "ADD A,A", "LD E,A", "LD D,0", "LD HL,0x94f5", "ADD HL,DE", "LD A,(HL)",
                            "INC HL", "LD H,(HL)", "LD L,A", "LD A,(0xd353)", "SUB 0x58", "ADD A,A", "LD E,A", "LD D,0", "ADD HL,DE",
                            "LD A,(HL)", "INC HL", "LD H,(HL)", "LD L,A", "LD DE,0x95dd", "PUSH DE", "JP (HL)"], start=0x94D1)),
])


def _jump_words(rom, spec):
    bank = spec["bank"]
    rd = (lambda c: word(rom, c)) if bank is None else (lambda c: word(rom, slot2_off(bank, c)))
    if spec["tables"] is not None:
        out = []
        for base in spec["tables"]:
            out += [rd(base + 2 * i) for i in range(spec["entries"])][1 if spec["skip_first"] else 0:]
        return out
    ptrs = [rd(0x94F5 + 2 * i) for i in range(4)]                  # $314F4: four sub-tables of 28 words, spacing checked below
    spacing = {b - a for a, b in zip(ptrs, ptrs[1:])}
    if spacing != {2 * spec["entries"]}:
        raise ValueError("$314F4 sub-table spacing is %s, not %d" % (sorted(spacing), 2 * spec["entries"]))
    return [rd(p + 2 * i) for p in ptrs for i in range(spec["entries"])]


def _decode_run(rom, bank, cpu, count):
    off = cpu if bank is None else slot2_off(bank, cpu)
    out = []
    for _ in range(count):
        d = F.decode(rom, off)
        out.append(z80.disasm(d))
        off += d.len
    return out


def jump_destinations(rom, site):
    """Destinations of a table-indexed computed jump after checking the instructions that build and bound the index; None when
    ``site`` is not in ``JUMP_SPECS``; raises when its bytes differ. ``valid`` are the destinations that are code addresses in the
    right window; ``invalid`` come from index values the bound admits but the table does not cover."""
    spec = JUMP_SPECS.get(site)
    if spec is None:
        return None
    if _decode_run(rom, spec["bank"], spec["start"], len(spec["pattern"])) != spec["pattern"]:
        raise ValueError("jump at $%05X no longer matches its specification" % site)
    if spec.get("bound_pattern") and _decode_run(rom, spec["bank"], spec["bound_start"], len(spec["bound_pattern"])) != spec["bound_pattern"]:
        raise ValueError("bound of the jump at $%05X no longer matches its specification" % site)
    words = sorted(set(_jump_words(rom, spec)))
    lo, hi = (0x0000, 0x8000) if spec["bank"] is None else (0x8000, 0xC000)
    return OrderedDict([("site", site), ("bank", spec["bank"]), ("bound", spec["bound"]),
                        ("destinations", [w for w in words if lo <= w < hi]), ("invalid", [w for w in words if not lo <= w < hi])])


def callback_closure(rom, uni, types, cache=None):
    """Everything a set of object types can execute: the callbacks' descent in their bank, the resident routines they call and the
    destinations of the table-indexed computed jumps in ``JUMP_SPECS`` that this code contains (a fixpoint). Returns
    (instructions, computed jumps left open, resident->slot-2 transfers not followed). A jump counts as open when its
    index is not bounded by an instruction (only the table extent limits it) or it is not in ``JUMP_SPECS``."""
    cache = {} if cache is None else cache
    reached, open_jumps, res_roots, s2_notes = {}, set(), set(), set()
    bank_roots, seen_bank = {}, {}
    for ty in types:
        for v in callback_vectors(uni[ty]):
            bank_roots.setdefault(uni[ty]["bank"], set()).add(v)
    jumps_seen = set()
    while True:
        progressed = False
        for bank, roots in sorted(bank_roots.items()):
            new = sorted(roots - seen_bank.setdefault(bank, set()))
            if not new:
                continue
            progressed = True
            seen_bank[bank] |= set(new)
            r, notes = descend_bank(rom, bank, new)
            reached.update(r)
            jumps_seen.update(n[1] for n in notes if n[0] == "indirect")
            for off in r:
                d = F.decode(rom, off)
                if d.op in F.TRANSFER_OPS:
                    tg = F._addr_operand(d)
                    if tg is not None and tg < 0x8000:
                        res_roots.add(tg)
        rr, ri, s2 = resident_reach(rom, res_roots, cache)
        if any(off not in reached for off in rr):
            progressed = True
        reached.update(rr)
        jumps_seen.update(ri)
        s2_notes.update(s2)
        for site in sorted(jumps_seen):
            if site in open_jumps:
                continue
            res = None
            try:
                res = jump_destinations(rom, site)
            except ValueError:
                res = None
            if res is None:
                open_jumps.add(site)
                continue
            if JUMP_SPECS[site]["bound"] is None or res["invalid"]:
                open_jumps.add(site)            # followed below as well, but the index is unbounded or reaches non-code words
            for dest in res["destinations"]:
                if res["bank"] is None:
                    if dest not in res_roots and dest < 0x8000:
                        res_roots.add(dest)
                        progressed = True
                elif 0x8000 <= dest < 0xC000 and dest not in seen_bank.setdefault(res["bank"], set()):
                    bank_roots.setdefault(res["bank"], set()).add(dest)
                    progressed = True
        if not progressed:
            break
    return reached, sorted(open_jumps), sorted(s2_notes)


def player_state_writers(rom, uni, cache=None):
    """Writers of the player's state byte ($D502 = IX+2 of the player slot) inside everything the two player types can run,
    plus every absolute store to $D502 in the image with its value source."""
    reached, indirect, s2 = callback_closure(rom, uni, (1, 2), cache)
    ix2 = []
    for off in sorted(reached):
        d = F.decode(rom, off)
        t = z80.disasm(d)
        if t.startswith("LD (IX+2),") or t.startswith("INC (IX+2)") or t.startswith("DEC (IX+2)"):
            m = re.match(r"LD \(IX\+2\),(0x[0-9a-f]+|\d+)$", t)
            ix2.append(OrderedDict([("file_offset", off), ("asm", t), ("value", int(m.group(1), 0) if m else None)]))
    absolute = []
    pat = bytes([0x32, ZONE_STATE_LO, ZONE_STATE_HI])
    i = rom.find(pat)
    while i != -1:
        prev2 = rom[i - 2:i]
        if prev2[0] == 0x3E:
            kind, val = "immediate", prev2[1]
        elif rom[i - 3:i] == bytes([0x32, 0x01, 0xD5]) and rom[i - 5] == 0x3E:
            kind, val = "immediate (shared with $D501)", rom[i - 4]
        else:
            kind, val = "computed", None
        absolute.append(OrderedDict([("file_offset", i), ("context", context_of(i)), ("kind", kind), ("value", val)]))
        i = rom.find(pat, i + 1)
    return OrderedDict([("closure_instructions", len(reached)), ("ix_plus_2_writers", ix2),
                        ("absolute_d502_stores_in_image", absolute), ("computed_jumps_not_followed", [hx(o) for o in indirect]),
                        ("resident_to_slot2_transfers_not_followed", [hx(o) for o in s2])])


ZONE_STATE_LO, ZONE_STATE_HI = 0x02, 0xD5               # operand of LD ($D502),A


# --- 5. how an object of a given type can come to exist -------------------------------------------------------------
ALLOCATORS = OrderedDict([(0x5E9C, "C"), (0x032C, "C"), (0x5EB7, "B"), (0x0371, "B")])   # pool $D540: type in C or B
ALLOCATOR_BODIES = ((0x5E9C, 0x5EB7), (0x5EB7, 0x5EE1))     # their own 'LD (IY),r' stores are the allocation itself
SLOT_TYPE_ALLOCATOR = (0x1CD3, 0x1CEB)                      # $1CD3 writes D452-slot types (DECOMP-1D R1 lemma C, U4)
# Stores through IY that are not object-type stores. Each is verified in ``_allowlisted`` before it is believed.
SPRITE_BUFFER_STORES = (0x2293, 0x22A6, 0x2303, 0x230A, 0x2324)             # sprite-table writer: IY is a RAM cursor advanced by INC IY
DESTROY_MARKERS = (0xFE, 0xFF)                              # '(IX),$FE/$FF' frees the slot, it does not create a type


def _writes_reg(text, reg):
    """True when ``text`` may change register ``reg`` (conservative: any CALL except to a pool allocator, which keeps C)."""
    t = text.upper()
    if t.startswith("CALL"):
        m = re.match(r"CALL (0x[0-9a-f]+)$", text)
        return not (m and int(m.group(1), 0) in (0x5E9C, 0x032C) and reg == "C")
    return (t.startswith("LD %s," % reg) or (t.startswith("POP ") and reg in t.split()[1]) or t.startswith("EXX")
            or t.startswith("INC %s" % reg) or t.startswith("DEC %s" % reg) or t.startswith("LD BC,")
            or t.startswith("DJNZ") and reg == "B")


def preceding_immediate(rom, reached, site, reg, depth=10):
    """Value of ``LD reg,n`` that dominates ``site`` along the fall-through chain inside ``reached``, or None when the chain
    forks (two fall-through predecessors, or any instruction on it is also the target of a branch), leaves the reached set or
    passes an instruction that may change the register."""
    ends, targets = {}, set()
    for off, ln in reached.items():
        ends.setdefault(off + ln, []).append(off)
        d = F.decode(rom, off)
        if d.op in F.TRANSFER_OPS:
            tg = F._addr_operand(d)
            t = F.resolve_target(off, tg) if tg is not None else None
            if t is not None:
                targets.add(t)
    cur = site
    for _ in range(depth):
        if cur in targets:
            return None
        preds = ends.get(cur, [])
        if len(preds) != 1:
            return None
        cur = preds[0]
        d = F.decode(rom, cur)
        text = z80.disasm(d)
        m = re.match(r"LD %s,(0x[0-9a-f]+|\d+)$" % reg, text)
        if m:
            return int(m.group(1), 0)
        if _writes_reg(text, reg) or F.is_terminal(d):
            return None
    return None


# An allocation inside a counted loop whose body saves and restores BC around the call: the register keeps its value although the loop
# head is a branch target. Verified against the loop's own instructions before it is believed.
LOOP_ALLOCATIONS = {0x492F: dict(register="C", value=6, start=0x4929,
                                 body=["LD B,A", "LD C,6", "LD H,0", "PUSH BC", "CALL 0x5e9c", "POP BC", "INC H", "DJNZ 0x492e"])}
ALLOCATOR_STUBS = (0x032C, 0x0371)                          # 'JP $5E9C' / 'JP $5EB7' entry stubs: their callers are the sites


def _allowlisted(rom, off, text):
    """Reason a store through (IY) is not an object-type store, or None. Every reason is checked against the bytes."""
    for lo, hi in ALLOCATOR_BODIES:
        if lo <= off < hi:
            return "body of the pool allocator $%04X (its callers are the creation sites)" % lo
    if SLOT_TYPE_ALLOCATOR[0] <= off < SLOT_TYPE_ALLOCATOR[1]:
        return "slot-type allocator $1CD3 (the four D452 slots, not object types; U4)"
    if off in SPRITE_BUFFER_STORES:
        window = [z80.disasm(F.decode(rom, o)) for o in sorted(_linear_starts(rom, off, 24))]
        if "INC IY" in window:
            return "sprite-table cursor store (IY advanced by INC IY within the loop)"
        raise ValueError("sprite-buffer allowlist entry at $%04X no longer matches the ROM" % off)
    return None


def _linear_starts(rom, off, n):
    out, p = set(), off
    for _ in range(n):
        out.add(p)
        p += F.decode(rom, p).len
    return out


def type_creation_sites(rom, reached):
    """Instructions in ``reached`` that put a type byte into a slot: pool allocators (type in C or B), ``LD (IX/IY),n`` and
    register forms. ``value`` is None when the register's value is not an immediate on the fall-through chain."""
    rows = []
    for off in sorted(reached):
        d = F.decode(rom, off)
        t = z80.disasm(d)
        if d.op in (F.OP.CALL, F.OP.JP):
            tg = F._addr_operand(d)
            if off in ALLOCATOR_STUBS:
                rows.append(OrderedDict([("file_offset", off), ("kind", "not a type store"), ("asm", t), ("value", None),
                                         ("why", "allocator entry stub; its callers are the creation sites")]))
                continue
            if tg in ALLOCATORS:
                v = preceding_immediate(rom, reached, off, ALLOCATORS[tg])
                loop = LOOP_ALLOCATIONS.get(off)
                if v is None and loop and ALLOCATORS[tg] == loop["register"] and _decode_run(rom, None, loop["start"], len(loop["body"])) == loop["body"]:
                    v = loop["value"]
                rows.append(OrderedDict([("file_offset", off), ("kind", "allocator $%04X" % tg), ("asm", t), ("value", v)]))
                continue
        m = re.match(r"LD \((IX|IY)\),(.+)$", t)
        if m:
            src = m.group(2)
            why = _allowlisted(rom, off, t) if m.group(1) == "IY" else None
            if why:
                rows.append(OrderedDict([("file_offset", off), ("kind", "not a type store"), ("asm", t), ("value", None), ("why", why)]))
                continue
            if re.match(r"(0x[0-9a-f]+|\d+)$", src):
                v = int(src, 0)
                rows.append(OrderedDict([("file_offset", off), ("kind", "destroy marker" if v in DESTROY_MARKERS else "conversion"),
                                         ("asm", t), ("value", v)]))
            else:
                reg = src.strip().upper()
                v = preceding_immediate(rom, reached, off, reg) if len(reg) == 1 else None
                if v in DESTROY_MARKERS:
                    rows.append(OrderedDict([("file_offset", off), ("kind", "destroy marker"), ("asm", t), ("value", v)]))
                else:
                    rows.append(OrderedDict([("file_offset", off), ("kind", "register store"), ("asm", t), ("value", None)]))
    return rows


def script_children(rom, uni):
    """``FF 04`` child allocations: {parent type: [(child type, state, script address)]} (operand 0 is the child's type)."""
    out = OrderedDict()
    for ty, entry in uni.items():
        with script_bank(entry["bank"]):
            for st, state in enumerate(entry["states"]):
                for p, (kind, ln, cmd) in state["steps"].items():
                    if kind == "command" and cmd == 4:
                        out.setdefault(ty, []).append((rom[P.file_offset(p + 2)], st, p))
    return out


# A register store the instruction chain cannot resolve, resolved by a separate, evidenced argument.
CHARACTER_CONVERSION = 0x30475        # LD (IX),A with A = $D2C8 + 1 (player type follows the character byte)


def character_writers(rom):
    """Absolute stores of the character byte $D2C8 with the instructions that build the stored value (all listed)."""
    rows = []
    pat = bytes([0x32, 0xC8, 0xD2])
    i = rom.find(pat)
    while i != -1:
        ctx = rom[max(0, i - 8):i + 3].hex(" ")
        rows.append(OrderedDict([("file_offset", i), ("context", context_of(i)), ("bytes", ctx)]))
        i = rom.find(pat, i + 1)
    return rows


def character_domain(rom):
    """Values the character byte can hold: the constants/rotation writers executed, then closed under the two relative
    writers (``$3576`` decrement while non-zero, ``$3585`` increment while below 1; both executed)."""
    out = {0, 1}                                              # $3072 (XOR A), $32E8F/$32E99 (0 / 1)
    for b in (0x00, 0x80):                                    # $2C58..$2C5D: bit 7 of a table byte picks 1 or 2
        m = Interp3(rom, ram={0xC000: b}, slot1=1, slot2=None, regs={"H": 0xC0, "L": 0x00})
        m.run(0x2C58, stops=(0x2C5D,))
        out.add(m.reg["A"])
    todo = sorted(out)
    while todo:
        v = todo.pop()
        for entry in (0x3576, 0x3585):
            m = Interp3(rom, ram={0xD2C8: v, 0xDE04: 0}, slot1=1, slot2=None)
            m.run(entry)
            n = m.ram[0xD2C8]
            if n not in out:
                out.add(n)
                todo.append(n)
    return sorted(out)


def creation_graph(rom, uni):
    """Edges parent -> child type from ``FF 04`` children, pool allocations and in-place conversions reachable from each
    type's callbacks (resident callees included). Unresolved sites (register-valued stores, computed jumps) are listed."""
    cache = {}
    children = script_children(rom, uni)
    edges, unresolved, indirect = [], [], OrderedDict()
    for ty, entry in uni.items():
        for child, st, p in children.get(ty, []):
            edges.append(OrderedDict([("src", ty), ("dst", child), ("kind", "FF 04 child"), ("state", st), ("script", p)]))
        reached, ind, s2 = callback_closure(rom, uni, (ty,), cache)
        if ind:
            indirect[ty] = [hx(o) for o in ind]
        for site in type_creation_sites(rom, reached):
            if site["kind"] in ("destroy marker", "not a type store"):
                continue
            if site["value"] is None:
                unresolved.append(OrderedDict([("src", ty), ("file_offset", site["file_offset"]), ("asm", site["asm"]),
                                               ("kind", site["kind"])]))
            else:
                edges.append(OrderedDict([("src", ty), ("dst", site["value"]), ("kind", site["kind"]),
                                          ("file_offset", site["file_offset"])]))
    return OrderedDict([("edges", edges), ("unresolved_sites", unresolved), ("computed_jumps_by_type", indirect)])


def frame_creation_sites(rom, roots=(0x16B8, 0x173F)):
    """Creation sites in the resident code the special-stage main loop runs each frame (``$16B8``: player update, object
    scheduler, placement call) - code that belongs to no object type."""
    reached, indirect, s2 = resident_reach(rom, roots, {})
    return OrderedDict([("roots", [hx(r) for r in roots]), ("instructions", len(reached)),
                        ("sites", type_creation_sites(rom, reached)), ("computed_jumps_not_followed", [hx(o) for o in indirect]),
                        ("resident_to_slot2_transfers", [hx(o) for o in s2])])


def closure_from(graph, roots, extra=()):
    """Types reachable from ``roots`` along the creation edges (plus ``extra`` edges); deterministic worklist."""
    adj = {}
    for e in list(graph["edges"]) + list(extra):
        adj.setdefault(e["src"], set()).add(e["dst"])
    seen, work = set(), sorted(roots)
    while work:
        t = work.pop()
        if t in seen:
            continue
        seen.add(t)
        work.extend(sorted(adj.get(t, ())))
    return sorted(seen)


# --- 6. the placement lists ($8000 in bank $1C) ---------------------------------------------------------------------
def placement_pointer(rom, zone, act):
    """List pointer the placement routine fetches for (zone, act): executes ``$8000..$8018`` under slot 2 = bank $1C."""
    m = Interp3(rom, ram={ZONE: zone, ACT: act}, slot1=1, slot2=PLACEMENT_BANK)
    m.run(0x8000, stops=(0x8019,))
    return m.get16("HL")


def read_cpu(rom, cpu, slot1, slot2):
    """One byte at a CPU address under an explicit mapper state; RAM and unknown banks are unresolved."""
    cpu &= 0xFFFF
    if cpu < 0x4000:
        return rom[cpu]
    if cpu < 0x8000:
        if slot1 is None:
            raise Unresolved("slot 1 bank unverified at $%04X" % cpu)
        return rom[slot1 * BANK + cpu - 0x4000]
    if cpu < 0xC000:
        if slot2 is None:
            raise Unresolved("slot 2 bank unverified at $%04X" % cpu)
        return rom[slot2 * BANK + cpu - 0x8000]
    raise Unresolved("RAM at $%04X" % cpu)


def parse_list(rom, ptr, slot1=1, slot2=PLACEMENT_BANK, limit=2000):
    """Walk an object list the way ``$8031`` does (9-byte entries, first byte $FF ends it)."""
    entries, cpu = [], ptr
    try:
        while len(entries) < limit:
            b = read_cpu(rom, cpu, slot1, slot2)
            if b == 0xFF:
                return OrderedDict([("entries", entries), ("terminated", True), ("error", None)])
            entries.append(OrderedDict([("type", b), ("x", read_cpu(rom, cpu + 1, slot1, slot2) | read_cpu(rom, cpu + 2, slot1, slot2) << 8),
                                        ("y", read_cpu(rom, cpu + 3, slot1, slot2) | read_cpu(rom, cpu + 4, slot1, slot2) << 8)]))
            cpu += 9
    except Unresolved as e:
        return OrderedDict([("entries", entries), ("terminated", False), ("error", str(e))])
    return OrderedDict([("entries", entries), ("terminated", False), ("error", "entry limit %d" % limit)])


def verified_lists(rom):
    """Lists the table selects for the in-range pairs (zone 0..15, act 0..2): the placement analogue of R2's nine records."""
    return sorted({placement_pointer(rom, z, a) for z in range(16) for a in range(3)})


def placement_rows(rom, n_types, zones=SS_ZONES):
    known = verified_lists(rom)
    rows = []
    for z in zones:
        for a in range(256):
            p = placement_pointer(rom, z, a)
            row = OrderedDict([("zone", z), ("act", a), ("list", p), ("known_list", p in known)])
            lst = parse_list(rom, p)
            types = sorted({e["type"] for e in lst["entries"]})
            row["entries"] = len(lst["entries"])
            row["terminated"] = lst["terminated"]
            row["error"] = lst["error"]
            row["types"] = types
            row["types_outside_table"] = [t for t in types if t > n_types]
            rows.append(row)
    return rows, known


def declared_edges(rom):
    """Edges for the register store ``$30475`` (type := character + 1) from the character byte's executed domain."""
    dom = character_domain(rom)
    return [OrderedDict([("src", src), ("dst", c + 1), ("kind", "player type follows character byte"),
                         ("file_offset", CHARACTER_CONVERSION), ("character_domain", dom)]) for src in (1, 2) for c in dom]


def trigger_types(rom, uni):
    """Types that can run each route to a bit-4 flag. A: types whose callbacks reach a CALL/JP $03F5 (level clear:
    player state $20 -> $303ED); B: types whose callbacks reach a $D293 := $50 store."""
    callers = [r["file_offset"] for r in level_clear_callers(rom) if r["file_offset"] >= 0x8000]
    reach = reach_map(rom, uni, sorted(set(callers) | set(SETTER_OFFSETS)))
    a = sorted({x["type"] for c in callers for x in reach[c]})
    b = sorted({x["type"] for t in (0x7BB2A, 0x7BB6E) for x in reach[t]})
    return OrderedDict([("A_level_clear_callers", a), ("B_d293_50_writers", b), ("reach", reach)])


FRAME_NODE = -1       # pseudo-type for the resident main-loop code, which belongs to no object type


def natural_closure(rom, uni, graph, frame, list_types, extra):
    """Types an object universe seeded with ``list_types`` (a placement list), the two player types and the resident per-frame code
    can create (placement is the only source of the first; the others follow the creation edges)."""
    frame_edges = [OrderedDict([("src", FRAME_NODE), ("dst", site["value"]), ("kind", site["kind"]), ("file_offset", site["file_offset"])])
                   for site in frame["sites"]
                   if site["value"] is not None and (site["kind"] == "conversion" or site["kind"].startswith("allocator"))]
    roots = set(list_types) | {1, 2, FRAME_NODE}
    return [t for t in closure_from(OrderedDict([("edges", list(graph["edges"]) + frame_edges)]), roots, extra) if t >= 0]


# --- 7. the main-loop dispatcher and the zone-complete path ------------------------------------------------------------
DISPATCH_START = 0x1336
DISPATCH_STOPS = OrderedDict([(0x1365, "end path $1365"), (0x138A, "level start $138A"), (0x14AE, "act complete $14AE"),
                              (0x1543, "zone complete $1543"), (0x15F2, "life lost $15F2"), (0x1673, "level reload $1673"),
                              (0x1696, "pause $1696"), (0x135D, "normal frame $16B8"), (0x183F, "stage success $183F"),
                              (0x1815, "stage failure $1815"), (0x17B0, "stage start $17B0"), (0x1786, "stage frame $16B8")])


def dispatch_target(rom, d294, d293, start=DISPATCH_START, stops=None):
    """Address the main-loop dispatch reaches for the two flag bytes (executed from ``start`` until a stop address)."""
    m = Interp3(rom, ram={SPECIAL_FLAGS: d294, STATE_FLAGS: d293}, slot1=1, slot2=None)
    m.run(start, stops=tuple(DISPATCH_STOPS if stops is None else stops))
    return m.pc


def dispatcher_table(rom):
    """The dispatch of ``$1333`` executed for every ``$D293`` with ``$D294`` in {0, stage mode with every combination of
    bits 6, 5, 3}. ``table[d294][d293]`` is the address the dispatch reaches."""
    table = OrderedDict()
    for d294 in [0x00] + [0x80 | b for b in range(0, 0x80) if b & ~0x68 == 0]:
        table[d294] = [dispatch_target(rom, d294, d293) for d293 in range(256)]
    ss = table[0x80]
    return OrderedDict([("table", table),
                        ("stage_mode_honoured_d293_bits", [b for b in range(8) if ss[1 << b] != 0x1786]),
                        ("stage_mode_ignored_d293_bits", [b for b in range(8) if ss[1 << b] == 0x1786])])


def stage_mode_facts(rom):
    """Priority facts derived from the executed dispatch: the D294 bits that pre-empt every D293 flag, the D293 winner among
    set honoured bits, and the outcome for the flag combinations that matter to U1."""
    t = dispatcher_table(rom)["table"]
    ss = t[0x80]
    prio = []
    for bit in (5, 4, 2, 0):
        winner_of_all = all(ss[v] == ss[1 << bit] for v in range(256) if v & (1 << bit) and not any(v & (1 << b) for b in prio))
        prio.append(bit) if winner_of_all else None
    return OrderedDict([
        ("d294_preempts_d293", OrderedDict((("bit%d" % b, hx(t[0x80 | (1 << b)][0x10])) for b in (6, 5, 3)))),
        ("d293_bit4_in_stage_mode", hx(ss[0x10])), ("d293_bit4_normal_mode", hx(t[0x00][0x40 | 0x10])),
        ("bit4_with_bit5_in_stage_mode", hx(ss[0x30])), ("bit4_with_d294_bit5", hx(t[0xA0][0x10])),
        ("bit4_with_d294_bit6", hx(t[0xC0][0x10])), ("bit4_with_d294_bit3", hx(t[0x88][0x10])),
        ("d293_priority_in_stage_mode", prio),
        ("d293_bits_ignored_in_stage_mode", [b for b in range(8) if ss[1 << b] == 0x1786]),
        ("d293_bits_ignored_in_normal_mode", [b for b in range(8) if t[0x00][1 << b] == 0x135D])])


def zone_complete_in_stage(rom):
    """What ``$1543`` does with ``$D297`` in 8..12 (executed lemmas): the results screen is skipped (``CP 5``), act := 0,
    zone := zone + 1, and the zone >= 6 branch raises bit 7. Nothing in that path clears the stage-mode flag ``$D294``."""
    rows = OrderedDict()
    for z in SS_ZONES:
        m = Interp3(rom, ram={ZONE: z}, slot1=1, slot2=None)
        m.run(0x1594, stops=(0x159B, 0x15CE))
        skip_results = m.pc == 0x15CE
        m2, _ = R2.execute(rom, 0x15CE, {ZONE: z, ACT: 7}, stops=(0x15DE, 0x15E8))
        m3, _ = R2.execute(rom, m2.pc, {STATE_FLAGS: 0x50, ZONE: m2.ram[ZONE]}, stops=(0x1333,))
        flags_after = m3.ram[STATE_FLAGS]
        rows[z] = OrderedDict([("results_screen_skipped", skip_results), ("zone_after", m2.ram[ZONE]), ("act_after", m2.ram[ACT]),
                               ("branch", hx(m2.pc)), ("d293_after_from_0x50", flags_after),
                               ("d294_written", SPECIAL_FLAGS in {a for a, _v in m3.writes})])
    return rows


def return_after_zone_complete(rom):
    """After a stage-mode zone-complete the timer/death exit runs ``$1869``; the dispatch then sees D293 with bit 7 set."""
    m, _ = R2.execute(rom, 0x1869, {SAVED_ZONE: 0, ZONE: 9, SPECIAL_FLAGS: 0x80, STATE_FLAGS: 0xC0}, stops=(0x1333,))
    d293 = m.ram[STATE_FLAGS]
    return OrderedDict([("d293_at_return", d293), ("d294_at_return", m.ram[SPECIAL_FLAGS]),
                        ("normal_dispatch_target", hx(dispatch_target(rom, m.ram[SPECIAL_FLAGS], d293)))])


def interrupt_window(rom):
    """Decoded window around the zone-complete store pair: interrupts are enabled when the pair runs, so (zone, 0) and
    (zone + 1, 0) are both observable by an interrupt; the music index of each pair is computed."""
    run = _decode_run(rom, None, 0x15C8, 18)
    di_in_window = any(t.startswith("DI") for t in run)
    ei_first = run[0] == "EI"
    pairs = []
    for z in SS_ZONES:
        for tag, (zz, aa) in transient_pairs((z, 7), [("act", 0), ("zone", z + 1)])[1:]:      # the initial act is not known
            idx = (3 * zz + aa) & 0xFF
            pairs.append(OrderedDict([("start_zone", z), ("state", tag), ("zone", zz), ("act", aa), ("music_index", idx),
                                      ("inside_music_table", idx <= 38), ("byte_read", rom[0x18BA + idx])]))
    over = [p for p in pairs if not p["inside_music_table"]]
    return OrderedDict([("window", run), ("ei_at_15C8", ei_first), ("di_in_window", di_in_window), ("pairs", pairs),
                        ("summary", "$15C8 executes EI and no DI follows before the stores at $15CF and $15D6, so an interrupt can observe (zone, 0) between them; "
                                    "of the observable pairs only (13, 0) leaves the 39-entry music table (index 39)" if ei_first and not di_in_window and len(over) == 1 else
                                    "window facts differ from the expected shape")])


GRAPHICS_ROW_TABLE, GRAPHICS_ROW_LEN = 0x7CED, 7


def graphics_table_rows(rom):
    """Rows of the graphics-load table read by ``$78E1`` (bank 1, 7-byte rows indexed by (3*zone + act) mod 256). Its extent by the
    rule the R1/R2 tables use: a row is table data while it starts below the lowest second-level pointer (bytes 5-6) seen so far -
    here the first row points at the data that follows the table."""
    rows, addr, low = [], GRAPHICS_ROW_TABLE, 0xFFFF
    while addr < low:
        row = rom[addr:addr + GRAPHICS_ROW_LEN]
        rows.append(bytes(row))
        low = min(low, row[5] | row[6] << 8)
        addr += GRAPHICS_ROW_LEN
    return rows


def graphics_threshold(rom, zone):
    """First act whose graphics row index (3*zone + act) mod 256 is outside the table."""
    n = len(graphics_table_rows(rom))
    return next(a for a in range(256) if ((3 * zone + a) & 0xFF) >= n)


# --- 8. the loader: record chain, mapper context, consumed bytes, slot-type routines ---------------------------------
HEADER_STOP = 0x5014            # after '$4FFF LD (IX+4),A' .. '$5011 LD (IX+5),A': D162 (layout bank) and D163 are stored
HEADER_BANK_ADDR, HEADER_BANK2_ADDR = 0xD162, 0xD163
LOADER_RECORD_POINTER_STOP = 0x2A6D


def header_chain(rom, zone, act):
    """``$4FDC`` for (zone, act): the header pointer it fetches and the two bank bytes it stores (``$D162`` from header byte 0,
    ``$D163`` from byte 3). Returns ``(header, d162, d163, error)``; ``error`` is set when the pointer needs slot 2."""
    try:
        m, _ = execute3(rom, 0x4FDC, {ZONE: zone, ACT: act}, slot1=1, slot2=None, stops=(HEADER_STOP,))
    except (R2.Unmodelled, Unresolved) as e:
        return None, None, None, str(e)
    return m.iy, m.ram[HEADER_BANK_ADDR], m.ram[HEADER_BANK2_ADDR], None


def loader_context_facts(rom):
    """Facts that make ``slot 2 at $2A4F = $D162`` an argument rather than an observation (all derived from the ROM):
    the call order in ``$2934``, the mapper writes reachable from ``$4DAD``, and where ``$D162`` comes from."""
    callee = [z80.disasm(F.decode(rom, o)) for o in (0x2948, 0x294B)]
    reached, notes = F.descend(rom, [0x4DAD], 0, 0x8000)
    setters = []
    for off in sorted(reached):
        d = F.decode(rom, off)
        t = z80.disasm(d)
        if t.startswith("CALL 0x1c6f"):
            setters.append(OrderedDict([("file_offset", off), ("prev", z80.disasm(F.decode(rom, _prev(rom, reached, off))))]))
        if "0xffff" in t or "0xfffe" in t or "0xfffd" in t:
            setters.append(OrderedDict([("file_offset", off), ("asm", t)]))
    helper = [z80.disasm(F.decode(rom, o)) for o in (0x1C6F, 0x1C72)]
    return OrderedDict([("call_sequence_before_loader", ["CALL 0x4dad", "CALL 0x2a4f"]), ("callees", callee),
                        ("mapper_helper_1C6F", helper), ("mapper_writes_reachable_from_4DAD", setters),
                        ("leaves_resident_range_from_4DAD", [n for n in notes if n[0] != "indirect"]),
                        ("final_slot2_source", "A = ($D162) at $4E1F, inside the $4E13 loop (B = $1D); $D162 = IX+4 of $D15E"),
                        ("d162_writer", z80.disasm(F.decode(rom, 0x4FFF))), ("d162_source", z80.disasm(F.decode(rom, 0x4FFC)))])


def _prev(rom, reached, off):
    for o, ln in reached.items():
        if o + ln == off:
            return o
    raise ValueError("no predecessor for $%05X" % off)


def physical_of(ptr, slot2_bank, slot1_bank=1):
    """Physical ROM offset of a CPU address under the derived mapper state (None for RAM or an unresolved slot-2 bank)."""
    if ptr < 0x4000:
        return ptr
    if ptr < 0x8000:
        return slot1_bank * BANK + ptr - 0x4000
    if ptr < 0xC000:
        return None if slot2_bank is None else (slot2_bank % 32) * BANK + ptr - 0x8000
    return None


def classify_pointer(ptr, verified, slot2_bank):
    if ptr in verified:
        return "verified record"
    if ptr < 0x4000:
        return "bank 0 (fixed)"
    if ptr < 0x8000:
        return "slot 1 (bank 1 by premise)"
    if ptr < 0xC000:
        return "slot 2 (bank $%02X)" % slot2_bank if slot2_bank is not None else "slot 2 (bank unresolved)"
    return "RAM"


def slot_dispatch_words(rom):
    """The 21 table words of the slot-type dispatcher ``$74027`` (bank $1D): the supported handlers (R1 lemma C)."""
    return [word(rom, slot2_off(SLOT_DISPATCH_BANK, SLOT_DISPATCH_TABLE + 2 * i)) for i in range(21)]


def slot_type_target(rom, t):
    """Destination of the jump ``$8018..$8027`` makes for slot type ``t`` (executed under slot 2 = bank $1D, IY pointing at a
    slot record whose first byte is ``t``)."""
    m = Interp3(rom, ram={0xC000: t}, slot1=1, slot2=SLOT_DISPATCH_BANK, iy=0xC000)
    m.run(0x8018, stops=(0x8027,))
    return m.get16("HL")


def slot_dispatch_caller(rom):
    """The interrupt-handler code that runs the slot-type dispatcher: while D293 bit 6 is set and bit 1 clear it maps bank $1D into
    slot 2 and calls $8000 (decoded, not assumed)."""
    run = _decode_run(rom, None, 0x5A2, 17)
    expect = ["LD A,(0xd293)", "BIT 6,A", "JR z,0x05c9", "LD A,(0xd293)", "BIT 1,A", "JR nz,0x05c9", "LD A,(0xd131)", "OR A", "JR nz,0x05c1",
              "LD A,15", "LD (0xffff),A", "CALL 0x220e", "CALL 0x1027", "LD A,0x1d", "LD (0xffff),A", "CALL 0x8000"]
    if run[:16] != expect:
        raise ValueError("the slot-dispatch call site differs from the expected sequence: %s" % run)
    return OrderedDict([("file_offset", 0x5C6), ("sequence", expect), ("runs_when", "D293 bit 6 set and bit 1 clear (every frame, in the IM 1 handler)")])


def slot_type_classes(rom, supported):
    """Where every slot-type byte 0..255 sends the dispatcher (executed), grouped by destination class."""
    by_class, ram = OrderedDict(), []
    for t in range(256):
        dest = slot_type_target(rom, t)
        cls = classify_destination(rom, dest, supported)
        by_class.setdefault(cls, []).append(t)
        if cls == "RAM":
            ram.append([t, dest])
    return OrderedDict([("counts", OrderedDict((k, len(v)) for k, v in by_class.items())),
                        ("types_by_class", OrderedDict((k, _ranges(v)) for k, v in by_class.items())),
                        ("types_that_jump_into_ram", ram)])


def classify_destination(rom, dest, supported):
    if dest in supported:
        return "supported handler"
    if dest < 0x0320:
        return "resident (restart/boot area)"
    if dest < 0x0450:
        return "resident jump stub" if rom[dest] == 0xC3 else "resident stub area (not a stub start)"
    if dest < 0x4000:
        return "resident code"
    if dest < 0x8000:
        return "slot 1 code (bank 1)"
    if dest < 0xC000:
        return "bank $1D code/data outside the handler list"
    return "RAM"


def loader_record(rom, zone, act, verified, supported):
    """Everything the loader does for (zone, act) with the mapper state the call chain gives it."""
    hdr, d162, d163, herr = header_chain(rom, zone, act)
    row = OrderedDict([("zone", zone), ("act", act), ("header", hdr), ("slot2_bank", d162 if herr is None else None),
                       ("slot2_error", herr)])
    try:
        probe = Interp3(rom, ram={ZONE: zone, ACT: act}, slot1=1, slot2=None)
        probe.run(LOADER, stops=(0x2A61,))                       # after 'LD E,(HL) / INC HL / LD D,(HL)': DE = first-level pointer
        first = probe.get16("DE")
        probe.run(0x2A61, stops=(0x2A69,))                       # after 'ADD HL,DE': HL = address of the second table word
        second_at = probe.get16("HL")
        probe.run(0x2A69, stops=(LOADER_RECORD_POINTER_STOP,))
        ptr = probe.get16("HL")
    except (R2.Unmodelled, Unresolved) as e:
        row.update([("first_pointer", None), ("second_read_at", None), ("record_pointer", None), ("class", "unresolved"), ("error", str(e))])
        return row
    row["first_pointer"], row["second_read_at"] = first, second_at
    row["record_pointer"] = ptr
    row["record_physical"] = physical_of(ptr, row["slot2_bank"])
    row["class"] = classify_pointer(ptr, verified, row["slot2_bank"])
    if ptr >= 0xC000:
        row["error"] = "record pointer in RAM: the bytes are not ROM-derivable"
        return row
    try:
        m = Interp3(rom, ram={ZONE: zone, ACT: act}, slot1=1, slot2=row["slot2_bank"])
        m.run(LOADER, stops=())
    except (R2.Unmodelled, Unresolved) as e:
        row["error"] = str(e)
        return row
    ram = m.ram
    row["record"] = OrderedDict([("D2E0", ram[0xD2E0] | ram[0xD2E1] << 8), ("D399", ram[0xD399] | ram[0xD39A] << 8),
                                 ("D39B", ram[0xD39B] | ram[0xD39C] << 8)])
    types = [ram[a] for a in R2.SLOT_TYPES]
    row["slot_types"] = types
    row["slot_targets"] = []
    for t in types:
        dest = slot_type_target(rom, t)
        row["slot_targets"].append(OrderedDict([("type", t), ("destination", dest), ("class", classify_destination(rom, dest, supported))]))
    return row


# --- 9. controlled execution in the DECOMP harness -------------------------------------------------------------------
# The harness (tools/sms_frame_harness.py) runs the original Z80 code with the Sega mapper, 8 KB RAM, an approximate VDP and the
# frame/line interrupts. It is not an emulator of the console and nothing here is hardware validation. A controlled run is a proof
# only for the state it is given: the stage entry is *forced* (what $178F stores after its guards), so it says what the code does
# once the state exists, never that the state can be reached.
class HarnessUnavailable(Exception):
    pass


def _harness():
    try:
        import sms_frame_harness as H
    except ImportError as e:                                    # the z80 core is a declared dependency (requirements.txt)
        raise HarnessUnavailable(str(e))
    return H


def _machine_class(H):
    class Machine(H.SMS):
        """SMS harness that also samples the program counter after every execution chunk: a pc in RAM is recorded."""

        def __init__(self, rom):
            super().__init__(rom)
            self.ram_exec = []                                  # (frame, pc, slot2) of the first samples with pc >= $C000
            self.watch = {}                                     # RAM address -> [(frame, value)] (capped)

        def _write(self, address, value):
            super()._write(address, value)
            if address >= 0xC000 and self.watch:
                key = 0xC000 + (address & 0x1FFF)
                log = self.watch.get(key)
                if log is not None and len(log) < 400:
                    log.append((self.frame, value & 0xFF))

        def _run_cycles(self, n):
            remaining = n
            while remaining > 0:
                if self._irq_asserted():
                    self.cpu.on_handle_active_int()
                chunk = min(remaining, 32)
                self.cpu.ticks_to_stop = chunk
                events = self.cpu.run()
                used = chunk - self.cpu.ticks_to_stop
                if events & self.cpu._BREAKPOINT_HIT:
                    hook = self.pc_hooks.get(self.cpu.pc)
                    if hook:
                        hook(self)
                    self._step_over()
                if self.cpu.pc >= 0xC000 and len(self.ram_exec) < 8:
                    self.ram_exec.append((self.frame, self.cpu.pc, self.slot[2]))
                if used <= 0:
                    used = chunk
                remaining -= used
    return Machine


def boot_machine(rom, saved_zone=0, act=0, limit=4000):
    """Boot the original game to the first playable frame of (saved_zone, act) by driving the start button."""
    H = _harness()
    s = _machine_class(H)(rom)
    done = [False]

    def select(m):
        m._write(ZONE, saved_zone)
        m._write(ACT, act)

    def placed(m):
        if m.frame >= 300:
            done[0] = True

    s.add_pc_hook(0x07D5, select)           # new-game init, after $D297/$D298 were cleared
    s.add_pc_hook(0x4E97, placed)           # start-position loader return
    for t in range(limit):
        s.pad = 0 if t < 250 else H.BTN_1 if t < 700 and t % 40 < 3 else (H.BTN_1 | H.BTN_2) if not done[0] and t % 60 < 10 else 0
        s.run_frame()
        if done[0] and s.mem[0xD500] == 1:
            s.pad = 0
            return s
    raise RuntimeError("the harness did not reach gameplay within %d frames" % limit)


def _snap(s):
    m = s.mem
    return OrderedDict([("frame", s.frame), ("zone", m[ZONE]), ("act", m[ACT]), ("saved_zone", m[SAVED_ZONE]),
                        ("d293", m[STATE_FLAGS]), ("d294", m[SPECIAL_FLAGS]), ("timer_run", m[0xD2BE]),
                        ("timer", m[0xD2BF] | m[0xD2C0] << 8), ("player_type", m[0xD500]), ("player_state", m[0xD502]),
                        ("slot2_bank", s.slot[2]), ("slot_types", [m[a] for a in R2.SLOT_TYPES])])


ENTRY_BOUND = 1200      # frames after the forced entry within which the stage must become active (it does in ~250 in every in-domain case)
EXIT_BOUND = 1500       # frames after the stage became active within which the accelerated timer's exit must have happened (~100 expected)
NATURAL_EXIT_BOUND = 4000      # the natural timer needs 59 seconds = 3,540 frames


def controlled_stage_case(rom, ss_zone, act, saved_zone=0, accelerate=True, post_return=0, max_frames=None,
                          injections=None, booted=None, watch=(), entry_bound=ENTRY_BOUND, exit_bound=None):
    """Force a special-stage entry (zone ``ss_zone``, level act ``act``) in the original code and observe it.

    ``accelerate``: once the stage has run 60 frames, ``$D2BF`` is set to 0 so the timer's own timeout branch runs within one
    second instead of after 59. Everything downstream of that store is the original code. ``injections`` is an optional list of
    (frames after the stage became active, address, bit mask) used by the U1 experiments to raise a flag the ROM was not shown to
    raise on its own (labelled as injected in the result). The run is bounded deterministically: it stops ``entry_bound`` frames
    after the entry if the stage never became active, ``exit_bound`` frames after it became active if it never exited (default
    ``EXIT_BOUND``, or ``NATURAL_EXIT_BOUND`` without the accelerated timer), and in any case at ``max_frames``."""
    if exit_bound is None:
        exit_bound = EXIT_BOUND if accelerate else NATURAL_EXIT_BOUND
    if max_frames is None:
        max_frames = entry_bound + exit_bound + post_return + 400
    s = booted() if booted else boot_machine(rom, saved_zone, 0)
    m = s.mem
    s.pad = 0
    for _ in range(100):
        s.run_frame()
    base_frame = s.frame
    s.watch = {a: [] for a in watch}
    m[EMERALDS] = (1 << (ss_zone - 8)) - 1 if ss_zone < 13 else 0x1F
    m[ACT] = act
    m[0xD2BE], m[SPECIAL_FLAGS], m[0xD2CD] = 0, 0x88, 1
    loader, after, trace = [], [], []

    def on_loader(mm):
        loader.append(OrderedDict([("frame", mm.frame - base_frame), ("zone", mm.mem[ZONE]), ("act", mm.mem[ACT]),
                                   ("slot1_bank", mm.slot[1]), ("slot2_bank", mm.slot[2]), ("shadow_d12b", mm.mem[0xD12B]),
                                   ("d162", mm.mem[0xD162])]))

    def on_loader_return(mm):
        r = mm.mem
        after.append(OrderedDict([("frame", mm.frame - base_frame), ("D2E0", r[0xD2E0] | r[0xD2E1] << 8),
                                  ("D399", r[0xD399] | r[0xD39A] << 8), ("D39B", r[0xD39B] | r[0xD39C] << 8),
                                  ("slot_types", [r[a] for a in R2.SLOT_TYPES])]))

    s.add_pc_hook(LOADER, on_loader)
    s.add_pc_hook(0x294E, on_loader_return)
    entered = active_at = exit_at = None
    bound_hit = None
    accelerated = False
    prev, last_change = None, 0
    longest_same = same = 0
    pending = sorted(injections or [])
    injected = []
    tail = 0
    tail_pcs, last_iff1, prev_d294, prev_player, exit_info = deque(maxlen=200), None, None, None, None
    for i in range(max_frames):
        s.run_frame()
        tail_pcs.append(s.cpu.pc >> 8)
        if s.cpu.iff1:
            last_iff1 = i
        z, d294 = m[ZONE], m[SPECIAL_FLAGS]
        key = (z, m[ACT], m[STATE_FLAGS], d294, m[0xD2BE])
        if key != prev:
            if len(trace) < 60:
                trace.append(OrderedDict([("f", i), ("zone", z), ("act", m[ACT]), ("d293", key[2]), ("d294", d294), ("timer_run", key[4])]))
            prev = key
        sig = (s.cpu.pc, s.cpu.sp)
        same = same + 1 if sig == last_change else 0
        last_change = sig
        longest_same = max(longest_same, same)
        if entered is None and z >= 8:
            entered = i
        if entered is not None and active_at is None and d294 == 0x80 and m[0xD2BE] == 0xFF:
            active_at = i
        if active_at is not None:
            while pending and i - active_at >= pending[0][0]:
                _t, addr, mask, *mode = pending.pop(0)
                if callable(mask):
                    mask = mask(s)
                if mode and mode[0] == "set":
                    m[addr] = mask
                else:
                    m[addr] |= mask
                injected.append(OrderedDict([("frame", i), ("address", addr), ("value" if mode and mode[0] == "set" else "mask", mask)]))
            if accelerate and not accelerated and i - active_at >= 60 and d294 & 0x80:
                m[0xD2BF] = 0
                accelerated = True
        if entered is not None and exit_at is None and active_at is not None and d294 == 0 and z == m[SAVED_ZONE]:
            exit_at = i
        if exit_at is None and entered is not None and active_at is not None and d294 == 0:
            exit_at = i                                       # stage flag cleared without the restore: reported as is
        if exit_at == i:
            exit_info = OrderedDict([("d294_before", prev_d294), ("d293", m[STATE_FLAGS]), ("player_state_before", prev_player)])
        prev_d294, prev_player = d294, m[0xD502]
        if exit_at is not None:
            tail += 1
            if tail > post_return:
                break
        elif active_at is None and i >= entry_bound:
            bound_hit = "entry"
            break
        elif active_at is not None and i - active_at >= exit_bound:
            bound_hit = "exit"
            break
    return OrderedDict([
        ("ss_zone", ss_zone), ("act", act), ("saved_zone", saved_zone), ("accelerated_timer", accelerate and accelerated), ("bound_hit", bound_hit),
        ("entered_frame", entered), ("active_frame", active_at), ("exit_frame", exit_at),
        ("loader_calls", loader), ("loader_results", after), ("injected", injected),
        ("ram_execution_samples", [list(x) for x in s.ram_exec]), ("longest_identical_pc_run_frames", longest_same),
        ("trace", trace), ("final", _snap(s)), ("final_pc", s.cpu.pc), ("iff1_at_end", bool(s.cpu.iff1)), ("last_iff1_frame", last_iff1),
        ("pc_pages_last_200_frames", sorted(set(tail_pcs))), ("exit_info", exit_info),
        ("watched_writes", OrderedDict((hx(a), [[f - base_frame, v] for f, v in log]) for a, log in sorted(s.watch.items())))])


_BOOTED = {}


def _case_worker(args):
    rom_key, ss_zone, act, saved_zone, kw, rom = args
    booted = _BOOTED.get((rom_key, saved_zone))
    return controlled_stage_case(rom, ss_zone, act, saved_zone=saved_zone, booted=(lambda: booted) if booted is not None else None, **kw)


def controlled_sweep(rom, cases, saved_zone=0, workers=None, **kw):
    """Run ``cases`` ((ss_zone, act) pairs). Every case starts from the identical post-boot state: with ``fork`` the booted machine is
    built once in the parent and each case runs in a fresh forked worker (the parent's machine is never run); without it every
    case boots its own machine. The original game is deterministic, so results do not depend on the schedule. Extra keyword
    arguments (and any injected callables) must be picklable, i.e. module-level."""
    import multiprocessing
    key = hashlib.sha256(rom).hexdigest()
    workers = max(1, workers or min(4, os.cpu_count() or 1))
    if "fork" not in multiprocessing.get_all_start_methods():
        return [_case_worker((key, z, a, saved_zone, kw, rom)) for z, a in cases]
    if (key, saved_zone) not in _BOOTED:
        _BOOTED[(key, saved_zone)] = boot_machine(rom, saved_zone, 0)
    jobs = [(key, z, a, saved_zone, kw, None) for z, a in cases]
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(processes=workers, maxtasksperchild=1) as pool:
        return pool.map(_case_worker, jobs, chunksize=1)


# --- 10. how a state with a given (special-stage zone, act) can be reached, and what the return does -------------------------
def entry_routes(rom, world, cap=40):
    """Fewest special-stage entries needed before a stage is entered at (special-stage zone, act), by breadth-first search over
    the ROM-derived events of DECOMP-1D-R2 (act complete below act 2, zone complete from act 2, the entry guard, the return that
    adds one to the act). Every entry assumes the 100 rings are collected (U6) and every success assumes its emerald bit can be
    set (U2): the result says what the *code* permits, not that a player can do it."""
    ss_zone_by_mask = {}
    for z, masks in world.ss_zones.items():
        for m in masks:
            ss_zone_by_mask[m & 0x1F] = z
    start = (0, 0, 0)
    best = {start: (0, [("new_game", (0, 0, 0))])}
    entries = OrderedDict()
    queue = [start]
    while queue:
        nxt = []
        for st in queue:
            z, a, mask = st
            dist, path = best[st]
            events = []
            flag = world.level_end[a]
            if flag & 0x20:
                events.append(("act_complete", (z, world.act_complete[a][0], mask), 0))
            if flag & 0x10:
                nz, na, pc = world.zone_complete[z]
                if pc != 0x15E8:
                    events.append(("zone_complete", (nz, na, mask), 0))
            if world.guard["armed_only_when_character_1_zone_lt_6_emeralds_not_full"] and z < 6 and (mask & 0x1F) != 0x1F:
                sz = ss_zone_by_mask[mask & 0x1F]
                restored, untouched, _sp, flags = world.ss_exit[z]
                na = world.act_complete[a][0] if flags & 0x20 and untouched else a
                key = (sz, a)
                if key not in entries or entries[key][0] > dist:
                    entries[key] = (dist, path)
                events.append(("special_stage_failed", (restored, na, mask), 1))
                events.append(("special_stage_succeeded", (restored, na, mask | 1 << (sz - 8)), 1))
            for name, new, cost in events:
                if new[1] > cap:
                    continue
                nd = dist + cost
                if new not in best or best[new][0] > nd:
                    best[new] = (nd, path + [(name, new)])
                    nxt.append(new)
        queue = nxt
    return entries


def route_text(path):
    return " -> ".join("%s%s" % (n, tuple(s)) for n, s in path)


def type5_rows(rom, loader_rows):
    """Special-stage (zone, act) rows whose record carries a slot type the dispatcher sends to the type-5 handler, with the
    nested zone-indexed jump that handler then makes (zone 8..12 is outside its 12-entry table)."""
    entries, end = R2.nested_table(rom)
    rows = []
    for r in loader_rows:
        if "slot_targets" not in r:
            continue
        for k, tg in enumerate(r["slot_targets"]):
            if tg["destination"] == 0x81BF:
                for b in (0, 1):
                    addr = R2.nested_word_address(rom, r["zone"], b)
                    rows.append(OrderedDict([("zone", r["zone"]), ("act", r["act"]), ("slot", k), ("type", tg["type"]), ("b", b),
                                             ("table_word_address", addr), ("inside_table", addr < end),
                                             ("destination", R2.nested_target(rom, r["zone"], b))]))
    return rows, end


def return_reload_classes(rom, verified, supported):
    """After a stage returns, the act-complete path adds one to the act and the level is reloaded for (saved zone, act + 1):
    the loader class of that pair for every saved zone 0..5 and every act the stage can have been entered with."""
    out = OrderedDict()
    for z in range(6):
        bad = []
        for a in range(256):
            r = loader_record(rom, z, (a + 1) & 0xFF, verified, supported)
            if r["class"] != "verified record":
                bad.append(a)
        out[str(z)] = OrderedDict([("entry_acts_whose_reload_is_out_of_domain", _ranges(bad)), ("count", len(bad))])
    return out


def _ranges(values):
    out, start, prev = [], None, None
    for v in values:
        if start is None:
            start = prev = v
        elif v == prev + 1:
            prev = v
        else:
            out.append([start, prev])
            start = prev = v
    if start is not None:
        out.append([start, prev])
    return out


# --- 11. verdict rules (pure functions: they take derived facts, not the ROM) ------------------------------------------
VERDICT_U1 = ("PROVEN REACHABLE", "PROVEN EXCLUDED", "PARTIAL", "UNPROVEN")
VERDICT_U3 = ("PROVEN RETURNABLE", "PROVEN BLOCKED", "PARTIAL", "UNPROVEN")
SUPPORTED_TARGET_CLASSES = ("supported handler", "resident jump stub")


def route_grounding(conditions, discharged=()):
    """A route is grounded only when every premise it rests on has been discharged; otherwise it is conditional on them."""
    open_ = sorted(set(conditions) - set(discharged))
    return ("grounded", []) if not open_ else ("conditional", open_)


def route_status(trigger_types, closure, unresolved_edges, open_jumps):
    """Is a flag route reachable under a closed model? ``trigger_types`` can run the route; ``closure`` is every type the
    scenario can create. Returns ``(status, why)`` with status in
    * 'present'        - a trigger type is in the closure (not excluded; whether it is *scheduled* is a separate fact);
    * 'excluded'       - none is, and no unresolved creation edge or computed jump leaves the model open;
    * 'excluded_so_far'- none is in the resolved closure, but an unresolved edge or computed jump could still create one."""
    hit = sorted(set(trigger_types) & set(closure))
    if hit:
        return "present", "trigger types in the closure: %s" % ", ".join("$%02X" % t for t in hit)
    if unresolved_edges or open_jumps:
        return "excluded_so_far", ("no trigger type in the resolved closure; %d unresolved creation edge(s) and %d open computed jump(s) "
                                   "(%s) are not excluded" % (len(unresolved_edges), len(open_jumps), ", ".join(str(j) for j in sorted(open_jumps))))
    return "excluded", "no trigger type in the closure and no unresolved creation edge or computed jump"


def flag_survives(dispatch, d294, flag_mask, intervening_clears=()):
    """Does a raised ``$D293`` bit reach a handler in the given dispatch table before something removes it? ``dispatch`` maps
    d294 -> a 256-entry list of targets. A pre-empting ``$D294`` bit or an intervening clear of the bit means it does not."""
    if any(c & flag_mask for c in intervening_clears):
        return False, "cleared before the dispatcher looks"
    target = dispatch[d294][flag_mask]
    return target not in (0x1786, 0x135D), hx(target)


def transient_pairs(initial, stores):
    """States an interrupt can observe while a sequence of byte stores updates (zone, act): ``stores`` is a list of
    ('zone'|'act', value). The initial and every intermediate pair are returned, the final one marked."""
    z, a = initial
    out = [("initial", (z, a))]
    for i, (name, v) in enumerate(stores):
        if name == "zone":
            z = v
        else:
            a = v
        out.append(("after_store_%d" % (i + 1) if i < len(stores) - 1 else "final", (z, a)))
    return out


def u1_verdict(routes):
    """``routes``: [{name, status, grounded}] with status in {'reachable', 'present', 'excluded', 'excluded_so_far', 'open'}.
    PROVEN REACHABLE needs a grounded route that is reachable; PROVEN EXCLUDED needs every route excluded; a mix in which at
    least one route is resolved (excluded, excluded so far, present) is PARTIAL; no resolved route is UNPROVEN."""
    states = [r["status"] for r in routes]
    if any(r["status"] == "reachable" and r.get("grounded") for r in routes):
        return "PROVEN REACHABLE"
    if states and all(x == "excluded" for x in states):
        return "PROVEN EXCLUDED"
    if any(x in ("excluded", "excluded_so_far", "present", "reachable") for x in states):
        return "PARTIAL"
    return "UNPROVEN"


def _returned(case):
    return case is not None and case["exit_frame"] is not None and case["active_frame"] is not None and not case["ram_execution_samples"] \
        and case["final"]["zone"] == case["saved_zone"]


def u3_row_verdict(static, case, natural=None, premises_ok=True):
    """Verdict for one out-of-domain (zone, act). ``static``: loader_record row; ``case``: the accelerated-timer controlled run (or None);
    ``natural``: the same state run with the natural 59-second timer (or None).
    * PROVEN RETURNABLE needs every pointer resolved from the ROM, every slot type to select a supported handler or a resident jump
      stub, and BOTH controlled runs to activate the stage, raise no RAM execution and return with the zone restored (the accelerated
      run alone is not enough: garbage handlers that run every frame can change what happens over 59 seconds);
    * PROVEN BLOCKED is reserved for a ROM-supported guard or terminal path (none was found for these rows);
    * PARTIAL when the record was read but a later step is unresolved or a run did not return, or when the stage load stalls with interrupts
      disabled before the loader is reached (no record is consulted);
    * UNPROVEN when the pointer chain itself cannot be resolved from the ROM."""
    if static["class"] == "verified record":
        return "IN DOMAIN"
    if case is not None and not case["loader_calls"] and (stuck_kind(case) or "").startswith("interrupts disabled"):
        return "PARTIAL"                      # the stage load stalls before the loader runs: the record is not reached, the lookup is not in doubt
    if "slot_targets" not in static or static.get("error") or static["class"] in ("unresolved", "RAM") \
            or static["slot2_bank"] is None:
        return "UNPROVEN"
    supported = all(t["class"] in SUPPORTED_TARGET_CLASSES for t in static["slot_targets"])
    if case is None:
        return "PARTIAL"
    if supported and _returned(case) and _returned(natural) and premises_ok:
        return "PROVEN RETURNABLE"
    return "PARTIAL"


def stuck_kind(case):
    """Why a stage that never became active made no progress (None when it did, or when RAM was executed): the machine sits in code with
    interrupts disabled (no timer, no frame interrupt), or restarted at the title, or simply had not finished within the bound."""
    if case["active_frame"] is not None or case["ram_execution_samples"]:
        return None
    pages = case["pc_pages_last_200_frames"]
    if case["final"]["zone"] == 7:
        return "restarted at the title"
    if not case["iff1_at_end"] and pages and pages[-1] - pages[0] <= 3:
        return "interrupts disabled, pc confined to $%02X00-$%02XFF" % (pages[0], pages[-1])
    return "no progress within the bound"


def controlled_outcome(case):
    """One word for what a controlled run did."""
    if case is None:
        return "not run"
    if case["ram_execution_samples"]:
        later_title = case["final"]["zone"] == 7
        return "executed RAM, then reset to title" if later_title and case["exit_frame"] is None else \
            ("executed RAM, stage never active" if case["active_frame"] is None else "executed RAM, stage active")
    if case["active_frame"] is None:
        return "stage never active"
    if case["exit_frame"] is None:
        return "stage active, no exit"
    return "returned" if case["final"]["zone"] == case["saved_zone"] or case["final"]["zone"] == 7 else "exit without restore"


# --- 12. evidence assembly -------------------------------------------------------------------------------------------
PREMISES = [
    "P1 Standard Sega mapper semantics (DECOMP-1D R4). Slot 0 is bank 0 (R2 census); slot 1 is bank 1 whenever resident code reads "
    "$4000-$7FFF (DECOMP-1D R3); slot 2 is whatever the instruction sequence last wrote through $1C6F, derived below, never assumed.",
    "P2 A bank register value is taken modulo the number of 16 KB banks of the image (32): the address lines of a 512 KB cartridge. "
    "R2 never needed this; R3 does, because a garbage header byte can name a bank above 31.",
    "P3 An interrupt that fires while a derived mapper state is in force restores it (the IM 1 handler saves and restores slot 2 "
    "through the $D12B shadow; DECOMP-1D R1 interrupt model).",
    "P4 Controlled execution is the DECOMP harness (z80 core, Sega mapper, approximate VDP): the original code with zeroed power-on "
    "RAM. It is not an emulator of the console and not hardware validation. The stage entry is forced (the stores $178F makes after "
    "its guards), so a run says what the code does once the state exists, never that the state can occur.",
    "P5 The sweep accelerates the special-stage timer (D2BF := 0 sixty frames after the stage is active) so the timer's own timeout branch runs. "
    "Acceleration changes what garbage handlers can do over 59 seconds, so every row whose accelerated run returned is run again with the natural "
    "timer, the threshold cases are run both ways, and a PROVEN RETURNABLE verdict needs both runs to return.",
    "P6 Player inputs, 100-ring collection (U6) and the emerald masks (U2) are adversarial/free: a route that needs them is "
    "'conditional' on them and is never reported as grounded.",
]

UNRESOLVED = [
    OrderedDict([("id", "U1-open"), ("kind", "new"), ("text", "Out-of-domain placement lists (special-stage zone 8 act >= 15, zone 9 >= 12, zone 10 >= 9, zone 11 >= 6, "
                 "zone 12 >= 3) name boss/level-clear types and type bytes above the type table. Whether such an entry is created "
                 "(camera window and spawn-map cell) and whether its object reaches the level-clear call were not evaluated.")]),
    OrderedDict([("id", "N1"), ("kind", "new"), ("text", "At least 42 zone readers and 21 act readers exist (R2 listed them). R3 resolved the loader, the header "
                 "table ($4FDC), the placement table ($8000 in bank $1C) and the music table; the graphics table at $7CED, the start-position table "
                 "at $4E98 and the palette routine were not analysed. Every out-of-domain stage depends on all of them at once.")]),
    OrderedDict([("id", "N2"), ("kind", "new"), ("text", "A slot type or object type outside its table (slot types $15-$7F/$95-$FF, object types $64-$EF) dispatches through "
                 "bytes that are not table data; destinations that are RAM addresses make the next instructions RAM-determined.")]),
    OrderedDict([("id", "N3"), ("kind", "new"), ("text", "The sweep forces D2BF := 0 (P5), and the harness zero-fills RAM at power-on; the contents real hardware has there are not defined by the ROM, "
                 "so every RAM-dependent run (jumps into RAM, reads of RAM pointers) is a statement about the harness state only.")]),
    OrderedDict([("id", "U2"), ("kind", "inherited"), ("text", "Emerald masks are object-supplied ($794A7, $7BB69); a special-stage zone above 8 needs bits 0..3 set. "
                 "Every route to zones 9..12 is reported conditional on them.")]),
    OrderedDict([("id", "U4"), ("kind", "inherited"), ("text", "Allocator / kernel-vector path to type-5 slots ($1CD3) - untouched.")]),
    OrderedDict([("id", "U5"), ("kind", "inherited"), ("text", "Register-addressed block moves with an unresolved destination (R2 census: 19 in discovered code, 18 outside) - untouched.")]),
    OrderedDict([("id", "U6"), ("kind", "inherited"), ("text", "The character byte and reaching 100 rings are player-supplied; R3 re-derived the character byte's domain ({0,1,2}) and uses it for one conversion edge.")]),
    OrderedDict([("id", "R2-R5,S1"), ("kind", "inherited"), ("text", "DECOMP-1D assumptions R2 (register-addressed stores), R3 (slot 1), R4 (mapper semantics), R5 (instruction universe) and S1 (stack discipline) are unchanged.")]),
]


def collapse(rows, key, fields):
    """Group consecutive acts of one zone with an identical ``key(row)``; each group keeps ``fields`` of its first row."""
    out, cur = [], None
    for r in rows:
        k = (r["zone"], key(r))
        if cur is not None and cur[0] == k and r["act"] == cur[1]["acts"][1] + 1:
            cur[1]["acts"][1] = r["act"]
            continue
        entry = OrderedDict([("zone", r["zone"]), ("acts", [r["act"], r["act"]])])
        for f in fields:
            entry[f] = r.get(f)
        cur = (k, entry)
        out.append(entry)
    return out


def case_summary(case):
    """Compact, deterministic summary of one controlled run (the full trace stays out of the committed evidence)."""
    ram = case["ram_execution_samples"]
    load = case["loader_calls"][0] if case["loader_calls"] else None
    res = case["loader_results"][0] if case["loader_results"] else None
    return OrderedDict([("zone", case["ss_zone"]), ("act", case["act"]), ("outcome", controlled_outcome(case)),
                        ("active_frame", case["active_frame"]), ("exit_frame", case["exit_frame"]),
                        ("ram_pc", ram[0][1] if ram else None), ("ram_frame", ram[0][0] if ram else None),
                        ("slot2_at_loader", load["slot2_bank"] if load else None), ("d162_at_loader", load["d162"] if load else None),
                        ("loader_calls", len(case["loader_calls"])),
                        ("record_types_loaded", res["slot_types"] if res else None),
                        ("final_zone", case["final"]["zone"]), ("final_act", case["final"]["act"]),
                        ("final_d293", case["final"]["d293"]), ("longest_identical_pc_run", case["longest_identical_pc_run_frames"]),
                        ("stuck", stuck_kind(case)), ("iff1_at_end", case["iff1_at_end"]), ("last_iff1_frame", case["last_iff1_frame"]),
                        ("final_pc", case["final_pc"]), ("exit_info", case["exit_info"])])


def thresholds(rows, ok):
    out = OrderedDict()
    for z in SS_ZONES:
        zs = [r for r in rows if r["zone"] == z]
        first = next((r["act"] for r in zs if not ok(r)), None)
        back = [r["act"] for r in zs if first is not None and r["act"] > first and ok(r)]
        out[str(z)] = OrderedDict([("first_out_of_domain_act", first), ("in_domain_again_at", back[:3])])
    return out


def build(rom, controlled=None):
    sha = verify_rom(rom)
    world = R2.World(rom)
    _ptrs, records, _safe = R2.loader_tables(rom)
    verified = set(records)
    supported = set(slot_dispatch_words(rom))
    uni, commands = object_universe(rom)
    n_types = type_count(rom)
    states_total = sum(len(e["states"]) for e in uni.values())
    notes_total = sum(len(s["notes"]) for e in uni.values() for s in e["states"])

    # 1-3: sites and provenance
    sites = setter_sites(rom)
    trig = trigger_types(rom, uni)
    reach = OrderedDict()
    for off in list(SETTER_OFFSETS) + list(LEVEL_CLEAR_CALLERS):
        reach[hx(off)] = [OrderedDict([("type", x["type"]), ("states", x["states"]), ("vector", hx(x["vector"])), ("bank", x["bank"])])
                          for x in trig["reach"][off]]
    callers = level_clear_callers(rom)
    psw = player_state_writers(rom, uni)
    level_end = R2.level_end_flag(rom)
    script_state_writes = OrderedDict()
    for ty, entry in uni.items():
        with script_bank(entry["bank"]):
            vals = sorted({rom[P.file_offset(p + 2)] for st in entry["states"] for p, (k, ln, cmd) in st["steps"].items()
                           if k == "command" and cmd == 3})
        if ty in (1, 2):
            script_state_writes[str(ty)] = vals

    # 4: creation
    graph = creation_graph(rom, uni)
    frame = frame_creation_sites(rom)
    declared = declared_edges(rom)
    by_kind = OrderedDict()
    for e in graph["edges"]:
        by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1

    # 5: placement
    prow, known = placement_rows(rom, n_types)
    setter_types = sorted(set(trig["A_level_clear_callers"]) | set(trig["B_d293_50_writers"]))
    for r in prow:
        r["trigger_types"] = sorted(set(r["types"]) & set(setter_types))
    closures = OrderedDict()
    for z in SS_ZONES:
        for a in range(0, 3):
            r = next(x for x in prow if x["zone"] == z and x["act"] == a)
            cl = natural_closure(rom, uni, graph, frame, r["types"], declared)
            closures["%d/%d" % (z, a)] = OrderedDict([("list", hx(r["list"])), ("placed_types", r["types"]), ("closure", cl),
                                                      ("trigger_types_in_closure", sorted(set(cl) & set(setter_types)))])
    distinct_lists = sorted({r["list"] for r in prow if r["known_list"]})
    closure_union = sorted({t for v in closures.values() for t in v["closure"]})
    unresolved_closure = [u for u in graph["unresolved_sites"] if u["src"] in closure_union and u["file_offset"] != CHARACTER_CONVERSION]
    open_jumps = sorted({j for t in closure_union for j in graph["computed_jumps_by_type"].get(t, [])})
    ood_rows = sum(1 for r in prow if not r["known_list"])
    ood_with_trigger = sum(1 for r in prow if not r["known_list"] and r["trigger_types"])
    st_A, why_A = route_status(trig["A_level_clear_callers"], closure_union, unresolved_closure, open_jumps)
    st_B, why_B = route_status(trig["B_d293_50_writers"], closure_union, unresolved_closure, open_jumps)

    # 6: dispatch
    dtab = dispatcher_table(rom)
    facts = stage_mode_facts(rom)
    surv = bit4_survival(rom, uni)
    between = surv["in_frame_update_closure"] + surv["in_stage_object_closures"] + surv["in_im1_closure"]
    survive, survive_at = flag_survives(dtab["table"], 0x80, 0x10, intervening_clears=[0x10] if between else [])
    facts["bit4_survives_to_the_dispatcher_in_stage_mode"] = OrderedDict([("survives", survive), ("handler", survive_at), ("clearing_writers", surv)])
    zc = zone_complete_in_stage(rom)
    ret = return_after_zone_complete(rom)

    # 7: loader rows
    lrows = []
    for z in SS_ZONES:
        for a in range(256):
            lrows.append(loader_record(rom, z, a, verified, supported))
    for r in lrows:
        case = controlled["sweep"].get((r["zone"], r["act"])) if controlled else None
        nat = controlled["natural"].get((r["zone"], r["act"])) if controlled else None
        r["controlled"] = case_summary(case) if case else None
        r["natural_outcome"] = controlled_outcome(nat) if nat else None
        r["verdict"] = u3_row_verdict(r, case, nat)
    t5, nested_end = type5_rows(rom, lrows)
    reload_classes = return_reload_classes(rom, verified, supported)
    routes = entry_routes(rom, world)

    # thresholds for the other tables the stage run reads
    thr = OrderedDict([("loader_record", thresholds(lrows, lambda r: r["class"] == "verified record")),
                       ("placement_list", thresholds(prow, lambda r: r["known_list"])),
                       ("level_header", thresholds(lrows, lambda r: r["header"] is not None and r["header"] < 0x5300 and r["header"] >= 0x5276)),
                       ("zone_music", OrderedDict((str(z), OrderedDict([("first_out_of_domain_act", next(a for a in range(256) if ((3 * z + a) & 0xFF) > 38))]))
                                                  for z in SS_ZONES)),
                       ("graphics_rows", OrderedDict((str(z), OrderedDict([("first_out_of_domain_act", graphics_threshold(rom, z))])) for z in SS_ZONES))])

    verdict_rows = [r for r in lrows if r["verdict"] != "IN DOMAIN"]
    vcount = OrderedDict()
    for r in verdict_rows:
        vcount[r["verdict"]] = vcount.get(r["verdict"], 0) + 1
    per_zone = OrderedDict()
    for z in SS_ZONES:
        c = OrderedDict()
        for r in verdict_rows:
            if r["zone"] == z:
                c[r["verdict"]] = c.get(r["verdict"], 0) + 1
        per_zone[str(z)] = c

    matrix = OrderedDict()
    for r in lrows:
        c = r["controlled"]
        label = (c["outcome"] + ("; " + c["stuck"] if c and c.get("stuck") else "")) if c else "not run"
        cls = r["class"].split(" (")[0]
        matrix.setdefault(cls, OrderedDict())
        matrix[cls][label] = matrix[cls].get(label, 0) + 1
    u1_routes = [
        OrderedDict([("name", "player state $20 -> $303ED, natural special-stage objects (acts inside the verified list set)"), ("status", st_A),
                     ("grounded", False), ("basis", why_A)]),
        OrderedDict([("name", "type $61 -> $7BB2A / $7BB6E, natural special-stage objects"), ("status", st_B), ("grounded", False), ("basis", why_B)]),
        OrderedDict([("name", "out-of-domain placement lists (acts beyond the verified list set)"), ("status", "present"), ("grounded", False),
                     ("basis", "%d of %d out-of-domain list rows name at least one trigger type; creation (camera window, spawn-map cell) and the boss "
                               "fight were not evaluated" % (ood_with_trigger, ood_rows))]),
    ]
    u1_overall = u1_verdict(u1_routes)

    doc = OrderedDict()
    doc["format"] = 1
    doc["task"] = "DECOMP-1D-R3"
    doc["rom_sha256"] = sha
    doc["generator"] = "tools/decomp1d_r3_special_stage.py"
    doc["base_commit"] = BASE_COMMIT
    doc["evidence_tier"] = ("static ROM-derived evidence (decoded sites, recursive descent, executed lemmas on a fail-closed interpreter) plus "
                            "controlled execution of the original Z80 code in the DECOMP harness; not an emulator run of the console, not hardware")
    doc["premises"] = PREMISES
    doc["setter_sites"] = sites
    doc["setter_census"] = bit4_census(rom)
    doc["scheduler"] = scheduler_facts(rom)
    doc["object_universe"] = OrderedDict([("types", n_types), ("state_tables", states_total), ("script_parse_notes", notes_total),
                                          ("type_table", "$65BA, %d words pointing into slot 2; types below $26 page bank 12, $26..$EF bank $1E" % n_types)])
    doc["provenance"] = OrderedDict([
        ("sites_reached_by", reach),
        ("level_clear", OrderedDict([("routine", "$4892 via the stub $03F5"), ("effect", "D502 := $20 (player state $20) and sound $89, or $97 when D298 == 2"),
                                     ("callers", callers), ("script_vectors_naming_the_routine", script_vectors_naming(uni, (LEVEL_CLEAR_STUB, LEVEL_CLEAR))),
                                     ("trigger_types_A", trig["A_level_clear_callers"])])),
        ("player_state_20_callback", OrderedDict([("vector", "$83A6 (bank 12)"), ("reached_by", reach[hx(0x303ED)]),
                                                  ("flag_by_act", OrderedDict([("act_0", level_end[0]), ("act_1", level_end[1]), ("act_2", level_end[2]), ("act_255", level_end[255])])),
                                                  ("act_ge_2_always_sets_bit4", all(level_end[a] == level_end[2] for a in range(2, 256)))])),
        ("type_61", OrderedDict([("trigger_types_B", trig["B_d293_50_writers"]),
                                 ("note", "state 5 callback $BB1A stores $50 unless D500 == 1 and D2CC == $1F; state 7 callback $BB61 stores $50 and sets D2CC bit 5")])),
        ("player_state_writers", psw),
        ("script_state_changes_FF03_players", script_state_writes)])
    doc["creation"] = OrderedDict([
        ("edges_by_kind", by_kind), ("edge_count", len(graph["edges"])),
        ("non_placement_edges", [e for e in graph["edges"] if e["kind"] != "FF 04 child"]),
        ("ff04_children", OrderedDict((str(t), sorted({c for c, _s, _p in v})) for t, v in sorted(script_children(rom, uni).items()))),
        ("unresolved_sites", graph["unresolved_sites"]), ("declared_edges", declared),
        ("character_byte_writers", character_writers(rom)),
        ("frame_loop", frame), ("computed_jumps_by_type", OrderedDict((str(k), v) for k, v in graph["computed_jumps_by_type"].items()))])
    doc["placement"] = OrderedDict([
        ("table", "bank $1C: $8546 + 2*zone (8-bit) -> word; + 2*act (8-bit) -> list pointer; entries are 9 bytes, first byte $FF ends"),
        ("verified_lists", [hx(k) for k in known]), ("special_stage_lists", [hx(k) for k in distinct_lists if k >= 0x9875]),
        ("natural_closure", closures),
        ("columns", ["zone", "act", "list", "known_list", "entries", "terminated", "error", "types_outside_table_count", "trigger_types"]),
        ("rows", [[r["zone"], r["act"], hx(r["list"]), r["known_list"], r["entries"], r["terminated"], r["error"],
                   len(r["types_outside_table"]), " ".join("%02X" % t for t in r["trigger_types"])] for r in prow
                  if r["known_list"] or r["act"] < 40 or r["act"] in (127, 128, 129, 255)]),
        ("rows_note", "all acts of the five special-stage zones were resolved; the committed table keeps the in-domain rows, acts 0..39 and the 8-bit wrap points"),
        ("trigger_type_row_counts", OrderedDict((("%02X" % t), sum(1 for r in prow if t in r["trigger_types"] and not r["known_list"]))
                                                for t in setter_types)),
        ("out_of_domain_rows", sum(1 for r in prow if not r["known_list"])),
        ("out_of_domain_rows_with_trigger_types", sum(1 for r in prow if not r["known_list"] and r["trigger_types"])),
        ("out_of_domain_rows_with_types_outside_table", sum(1 for r in prow if not r["known_list"] and r["types_outside_table"])),
        ("out_of_domain_rows_unterminated", sum(1 for r in prow if not r["known_list"] and not r["terminated"]))])
    doc["dispatch"] = OrderedDict([("facts", facts), ("stage_mode_honoured_d293_bits", dtab["stage_mode_honoured_d293_bits"]),
                                   ("stage_mode_ignored_d293_bits", dtab["stage_mode_ignored_d293_bits"]),
                                   ("d294_values_executed", [hx(k) for k in dtab["table"]]),
                                   ("interrupt_closure_writers", interrupt_closure_writers(rom)),
                                   ("zone_complete_in_stage", OrderedDict((str(k), v) for k, v in zc.items())), ("return_after_zone_complete", ret)])
    doc["loader"] = OrderedDict([
        ("expression", "p1 = word[$2A9A + 2*zone (8-bit)]; record = word[p1 + 2*act (8-bit)]; bytes +0..+9 -> D2E0, D399, D39B and four slot types"),
        ("context_facts", loader_context_facts(rom)),
        ("verified_records", [hx(r) for r in records]), ("supported_slot_handlers", [hx(w) for w in sorted(supported)]),
        ("slot_dispatch_caller", slot_dispatch_caller(rom)), ("slot_type_classes", slot_type_classes(rom, supported)),
        ("thresholds", thr),
        ("class_counts", OrderedDict((str(z), OrderedDict(sorted(
            collections_counter([r["class"].split(" (")[0] for r in lrows if r["zone"] == z]).items()))) for z in SS_ZONES)),
        ("columns", ["zone", "act", "header", "slot2_bank", "record_pointer", "class", "slot_types", "first_pointer", "second_read_at",
                     "record_physical", "slot_target_classes", "verdict", "outcome", "active_frame", "exit_frame", "ram_pc", "final_zone", "final_act",
                     "stuck", "natural_outcome", "loader_calls"]),
        ("rows", [_loader_row(r) for r in lrows]),
        ("row_legend", "slot_target_classes: s = supported handler, j = resident jump stub, r = resident code/stub area, b = bank $1D outside the list, "
                       "x = RAM address; ram_pc is the first program-counter sample at or above $C000"),
        ("type5_rows", t5), ("nested_table_end", hx(nested_end)), ("return_reload", reload_classes)])
    def _conditions(path):
        return ["U6"] + (["U2"] if any(n == "special_stage_succeeded" for n, _s in path) else [])
    doc["entry_routes"] = OrderedDict([("assumes", "U6 (100 rings at every stage entry) and U2 (an emerald bit per success)"),
                                       ("fewest_prior_entries", OrderedDict(("%d/%d" % k, OrderedDict([("entries", v[0]), ("route", route_text(v[1])),
                                                                                                         ("grounding", route_grounding(_conditions(v[1])))]))
                                                                            for k, v in sorted(routes.items())
                                                                            if k[0] in SS_ZONES and (k[1] in (0, 1, 2, 3, 6, 9, 12) or k[1] == 40)))])
    doc["graphics_table"] = OrderedDict([("address", "$%04X" % GRAPHICS_ROW_TABLE), ("row_length", GRAPHICS_ROW_LEN), ("rows", len(graphics_table_rows(rom))),
                                         ("reader", "$78E1 (bank 1): IY = $7CED + 7*L with L = (3*zone + act) mod 256, executed with interrupts disabled"),
                                         ("extent_rule", "first row's second-level pointer is the address of the data after the table")])
    doc["controlled"] = controlled["meta"] if controlled else OrderedDict([("status", "not run")])
    doc["music_zone_13"] = OrderedDict([("index_zone_13_act_0", (3 * 13) & 0xFF), ("table_entries", 39), ("byte_read", rom[0x18BA + 39]),
                                        ("sound_request_value", hx(rom[0x18BA + 39])), ("note", "index 39 is the first byte of the code at $18E1")])
    doc["verdicts"] = OrderedDict([
        ("U1", OrderedDict([("verdict", u1_overall), ("routes", u1_routes),
                            ("summary", "all three bit-4 writers are identified, the stage dispatcher honours bit 4, and the natural stage universe cannot create a "
                                        "type that reaches any of them except through four open computed jumps; out-of-domain placement lists name such types "
                                        "and remain open")])),
        ("U3", OrderedDict([("counts", vcount), ("by_zone", per_zone), ("rows_examined", len(lrows)), ("static_class_by_controlled_outcome", matrix),
                            ("overall", "PARTIAL" if verdict_rows else "UNPROVEN")]))])
    # interrupt window of the zone-complete store pair
    win = interrupt_window(rom)
    doc["interrupt_window"] = win
    # static derivation versus the controlled observation (validation, not proof)
    if controlled:
        mism, compared = [], 0
        for r in lrows:
            c = controlled["sweep"].get((r["zone"], r["act"]))
            if c and c["loader_calls"] and r["slot2_bank"] is not None:
                compared += 1
                if c["loader_calls"][0]["slot2_bank"] != r["slot2_bank"] % 32:
                    mism.append([r["zone"], r["act"], r["slot2_bank"], c["loader_calls"][0]["slot2_bank"]])
        doc["controlled"]["static_slot2_vs_observed"] = OrderedDict([("compared", compared), ("mismatches", mism[:20]), ("mismatch_count", len(mism))])
        mism2 = []
        for r in lrows:
            c = controlled["sweep"].get((r["zone"], r["act"]))
            if c and c["loader_results"] and r.get("slot_types") and c["loader_results"][0]["slot_types"] != r["slot_types"]:
                mism2.append([r["zone"], r["act"], r["slot_types"], c["loader_results"][0]["slot_types"]])
        doc["controlled"]["static_slot_types_vs_observed"] = OrderedDict([("mismatch_count", len(mism2)), ("mismatches", mism2[:20])])
    if controlled:
        stall = OrderedDict()
        for z in SS_ZONES:
            acts = [r["act"] for r in lrows if r["zone"] == z and r["controlled"] and (r["controlled"].get("stuck") or "").startswith("interrupts disabled")]
            stall[str(z)] = OrderedDict([("first_stalled_act", min(acts) if acts else None), ("graphics_table_threshold", thr["graphics_rows"][str(z)]["first_out_of_domain_act"])])
        doc["controlled"]["first_interrupts_disabled_stall_vs_graphics_threshold"] = stall
        n_rows = len(graphics_table_rows(rom))
        cross = OrderedDict()
        for r in lrows:
            c = r["controlled"]
            inside = ((3 * r["zone"] + r["act"]) & 0xFF) < n_rows
            group = "returned" if c["outcome"] == "returned" else ("stalled with interrupts disabled" if (c.get("stuck") or "").startswith("interrupts disabled")
                                                                 else "other")
            cross.setdefault("graphics row in table" if inside else "graphics row outside the table", OrderedDict())
            key = cross["graphics row in table" if inside else "graphics row outside the table"]
            key[group] = key.get(group, 0) + 1
        doc["controlled"]["graphics_row_vs_outcome"] = cross
    reload_rows = reload_classes
    zc12 = zc[12]
    doc["interaction"] = OrderedDict([
        ("Q1_out_of_domain_stage_instantiating_completion_callbacks", OrderedDict([
            ("answer", "conditional"), ("evidence", "%d of %d out-of-domain placement-list rows name trigger types (A: level-clear callers, B: type $61); "
                                                  "creation and the boss defeat were not evaluated" % (ood_with_trigger, ood_rows)),
            ("per_type_row_counts", OrderedDict((("%02X" % t), sum(1 for r in prow if t in r["trigger_types"] and not r["known_list"])) for t in setter_types))])),
        ("Q2_zone_complete_selecting_an_unverified_record", OrderedDict([
            ("answer", "no loader call follows"),
            ("evidence", "the stage-mode dispatcher ignores D293 bits 1 (reload), 3, 6 and 7, and $1543 never clears D294, so $2A4F is not called for the "
                         "new (zone + 1, 0); those pairs also select verified records"),
            ("new_pairs", [[z + 1, 0, loader_record(rom, z + 1, 0, verified, supported)["class"]] for z in SS_ZONES])])),
        ("Q3_return_preserving_a_high_act", OrderedDict([
            ("answer", "yes, as a conditional chain"),
            ("evidence", "the return adds one to the act; the reload for (saved zone, act + 1) leaves the verified records for the entry acts listed"),
            ("reload_out_of_domain_entry_acts_by_saved_zone", reload_rows)])),
        ("Q4_partial_zone_act_update_seen_by_an_interrupt", OrderedDict([
            ("answer", "yes, for one pair; harmless for the consumers analysed"),
            ("evidence", win["summary"]), ("transient_pairs", win["pairs"])]))])
    doc["effect_on_r2"] = OrderedDict([
        ("accepted_r2_evidence_changed", False),
        ("zone_complete_in_special_stage_edge", OrderedDict([
            ("r2_state", "ungrounded; target modelled as (zone + 1, 0, END) immediately"),
            ("r3_state", "retained as unresolved: not supported (no natural producer inside the resolved universe), not excluded (open jumps, out-of-domain lists)"),
            ("correction_if_the_edge_is_taken", "executed: the stage stays active (D294 unchanged) at (zone + 1, 0); the stage's own exit then restores the saved "
                                                 "zone and the dispatcher takes the end path because D293 bit 7 survives; the results screen and the act increment are skipped"),
            ("executed_lemma_zone_12", zc12)])),
        ("unknown_record_paths", "the two table reads are resolved for every special-stage (zone, act); the record's bank, bytes and slot-type destinations are resolved "
                                 "for %d of the %d out-of-domain rows (%d record pointers are in RAM and %d banks are unresolved: not ROM-derivable); the R2 'grounded' "
                                 "definition (record in the nine verified records) is unchanged, so no state becomes grounded" % (
                                     sum(1 for r in lrows if r["class"] != "verified record" and "slot_targets" in r and r["slot2_bank"] is not None
                                         and not r.get("error")),
                                     sum(1 for r in lrows if r["class"] != "verified record"),
                                     sum(1 for r in lrows if r["class"] == "RAM"),
                                     sum(1 for r in lrows if r["class"] != "verified record" and r["class"] != "RAM" and r["slot2_bank"] is None)))])
    t5n = len(t5)
    doc["propositions"] = OrderedDict([
        ("A", OrderedDict([("r2_status", "PARTIAL"), ("r3_effect", "no change of status"),
                           ("detail", "a zone-complete in special-stage zone 12 would make the pair (13, 0): music index 39 reads byte $%02X (the first byte of the code at "
                                      "$18E1) as a sound request; no injection run requested it; (13, 0) is reachable only through U1's open routes"
                                      % rom[0x18BA + 39])])),
        ("B", OrderedDict([("r2_status", "DISPROVEN"), ("r3_effect", "no change of status"),
                           ("detail", "the proven part (zone <= 15, act <= 2 select nine records) and the per-zone safe bounds stand; R3 adds that leaving the bound is "
                                      "not an immediate fault for every row: see the U3 verdicts")])),
        ("C", OrderedDict([("r2_status", "PARTIAL"), ("r3_effect", "adds a conditional route, status unchanged"),
                           ("detail", "%d row(s) of the out-of-domain records put a type-5 slot beside special-stage zone 12 (act 127), outside the 12-entry nested table; "
                                      "destinations $%04X/$%04X; the route needs a stage entry at act 127" % (
                                          t5n, t5[0]["destination"] if t5 else 0, t5[1]["destination"] if t5 else 0))])),
        ("R1", OrderedDict([("status", "PARTIALLY CLOSED (unchanged)"),
                            ("detail", "no dispatcher is promoted; four computed jumps in object/engine code stay open ($314F4, $6972, $6C98, $77EC), two of them with an "
                                       "index that reaches one word past their table ($6972, $77EC: destination $DDC9, RAM)")]))])
    doc["unresolved"] = UNRESOLVED
    doc["baseline"] = OrderedDict([("structurally_classified_bytes", 156887), ("recovered_assembly_bytes", 13988), ("recovered_regions", 113),
                                   ("unknown_bytes", 367401), ("contradictory_claims", 0), ("changed_by_r3", False)])
    return doc, OrderedDict([("lrows", lrows), ("prow", prow), ("world", world)])


_TARGET_CODE = {"supported handler": "s", "resident jump stub": "j", "resident code": "r", "resident stub area (not a stub start)": "r",
                "resident (restart/boot area)": "r", "slot 1 code (bank 1)": "r", "bank $1D code/data outside the handler list": "b", "RAM": "x"}


def _loader_row(r):
    c = r.get("controlled") or {}
    return [r["zone"], r["act"], hx(r["header"]) if r["header"] is not None else None, r["slot2_bank"],
            hx(r["record_pointer"]) if r.get("record_pointer") is not None else None, r["class"],
            " ".join("%02X" % t for t in r.get("slot_types", [])),
            hx(r["first_pointer"]) if r.get("first_pointer") is not None else None, hx(r["second_read_at"]) if r.get("second_read_at") is not None else None,
            ("$%05X" % r["record_physical"]) if r.get("record_physical") is not None else None,
            "".join(_TARGET_CODE[t["class"]] for t in r.get("slot_targets", [])) or None, r["verdict"], c.get("outcome"),
            c.get("active_frame"), c.get("exit_frame"), hx(c["ram_pc"]) if c.get("ram_pc") is not None else None,
            c.get("final_zone"), c.get("final_act"), c.get("stuck"), r.get("natural_outcome"), c.get("loader_calls")]


def collections_counter(items):
    out = {}
    for x in items:
        out[x] = out.get(x, 0) + 1
    return out


# --- 13. the controlled-execution campaign ---------------------------------------------------------------------------------
NATURAL_CASES = ((8, 0), (8, 8), (8, 9), (9, 8), (9, 9), (10, 5), (10, 6), (11, 8), (11, 9), (12, 5), (12, 6), (12, 3))
U1_WATCH = (STATE_FLAGS, SPECIAL_FLAGS, ZONE, ACT, 0xDE04)


def _u1_summary(case):
    """What a flag injection did: the zone/act/flag sequence, the sound requests, the end state."""
    seq = [(t["f"], t["zone"], t["act"], t["d293"], t["d294"]) for t in case["trace"]]
    sounds = sorted({v for _f, v in case["watched_writes"].get(hx(0xDE04), []) if v})
    z = case["ss_zone"]
    zones = [t[1] for t in seq]
    return OrderedDict([
        ("ss_zone", z), ("injected", case["injected"]), ("active_frame", case["active_frame"]), ("exit_frame", case["exit_frame"]),
        ("zone_sequence", [x for i, x in enumerate(zones) if i == 0 or x != zones[i - 1]]),
        ("reached_zone_plus_one", (z + 1) in zones),
        ("stage_flag_during_limbo", sorted({t[4] for t in seq if t[1] == z + 1})),
        ("d293_during_limbo", sorted({t[3] for t in seq if t[1] == z + 1})),
        ("d293_at_exit", case["exit_info"]["d293"] if case["exit_info"] else None),
        ("d293_after_return", case["final"]["d293"]), ("final_zone", case["final"]["zone"]),
        ("sound_requests_after_injection", [hx(v) for v in sounds if v not in (0x8A, 0x8F)]),
        ("ram_execution_samples", case["ram_execution_samples"])])


OFFSCREEN = 0x130       # player x relative to the camera: past the $120 the state-$20 callback tests for


def _camera_x(m):
    return m.mem[0xD174] | m.mem[0xD175] << 8


def _player_x_low(m):
    return (_camera_x(m) + OFFSCREEN) & 0xFF


def _player_x_high(m):
    return ((_camera_x(m) + OFFSCREEN) >> 8) & 0xFF


def run_controlled(rom, workers=None, cases=None):
    """The whole campaign: every (special-stage zone, act 0..255) with the accelerated timer, the natural-timer threshold cases, the
    U1 flag injections and the forced player-state experiments. Slow (about half an hour for every row); deterministic. ``cases``
    restricts the sweep (used by the tests)."""
    cases = [(z, a) for z in SS_ZONES for a in range(256)] if cases is None else list(cases)
    sweep = controlled_sweep(rom, cases, workers=workers)
    by_case0 = OrderedDict(((c["ss_zone"], c["act"]), c) for c in sweep)
    returned = [k for k, c in by_case0.items() if controlled_outcome(c) == "returned"]
    natural_cases = sorted((set(NATURAL_CASES) & set(by_case0)) | set(returned))
    natural = controlled_sweep(rom, natural_cases, workers=workers, accelerate=False)
    inj = controlled_sweep(rom, [(z, 0) for z in SS_ZONES], workers=workers, injections=[(0, STATE_FLAGS, 0x10)], post_return=1500,
                           watch=U1_WATCH)
    forced = controlled_sweep(rom, [(8, 2)], workers=1, accelerate=False, injections=[(30, 0xD502, 0x20, "set")], exit_bound=700,
                              watch=(STATE_FLAGS, 0xD502))
    offscreen = controlled_sweep(rom, [(8, 2)], workers=1, accelerate=False, exit_bound=900, watch=(STATE_FLAGS, SPECIAL_FLAGS, ZONE, ACT),
                                 injections=[(30, 0xD502, 0x20, "set"), (30, 0xD511, _player_x_low, "set"), (30, 0xD512, _player_x_high, "set")])
    by_case = by_case0
    natural_by_case = OrderedDict(((c["ss_zone"], c["act"]), c) for c in natural)
    meta = OrderedDict([
        ("harness", "tools/sms_frame_harness.py (z80 core, Sega mapper, approximate VDP); original code, zero-filled power-on RAM"),
        ("entry", "forced: D2CC = (1 << (zone-8)) - 1, D298 = act, D2BE = 0, D294 = $88, D2CD = 1 (what $178F stores after its guards), "
                  "after 100 frames of level play in zone 0 act 0"),
        ("accelerated_timer", "D2BF := 0 sixty frames after the stage is active (P5)"),
        ("bounds", OrderedDict([("entry_bound_frames", ENTRY_BOUND), ("exit_bound_frames_accelerated", EXIT_BOUND),
                                ("exit_bound_frames_natural", NATURAL_EXIT_BOUND)])),
        ("cases", len(cases)),
        ("outcome_counts", OrderedDict(sorted(collections_counter([controlled_outcome(c) for c in sweep]).items()))),
        ("natural_timer_runs", OrderedDict([
            ("columns", ["zone", "act", "outcome", "exit_frame", "final_zone", "ram_pc", "exit_d294_before", "exit_d293"]),
            ("rows", [[c["ss_zone"], c["act"], controlled_outcome(c), c["exit_frame"], c["final"]["zone"],
                       hx(c["ram_execution_samples"][0][1]) if c["ram_execution_samples"] else None,
                       c["exit_info"]["d294_before"] if c["exit_info"] else None, c["exit_info"]["d293"] if c["exit_info"] else None]
                      for c in natural])])),
        ("natural_vs_accelerated", OrderedDict([("compared", len(natural)), ("outcome_differences", [
            [c["ss_zone"], c["act"], controlled_outcome(c), controlled_outcome(by_case[(c["ss_zone"], c["act"])])]
            for c in natural if controlled_outcome(c) != controlled_outcome(by_case[(c["ss_zone"], c["act"])])])])),
        ("u1_flag_injection", [_u1_summary(c) for c in inj]),
        ("forced_player_state_20", OrderedDict([("zone", 8), ("act", 2), ("injected", forced[0]["injected"]),
                                                ("d293_writes", forced[0]["watched_writes"][hx(STATE_FLAGS)]),
                                                ("final", forced[0]["final"]),
                                                ("reading", "state $20 stayed in force for the observed window; the callback's position test did not "
                                                            "pass and D293 bit 4 was not raised")])),
        ("forced_player_state_20_offscreen", OrderedDict([
            ("zone", 8), ("act", 2), ("injected", offscreen[0]["injected"]), ("d293_writes", offscreen[0]["watched_writes"][hx(STATE_FLAGS)]),
            ("zone_writes", offscreen[0]["watched_writes"][hx(ZONE)]), ("act_writes", offscreen[0]["watched_writes"][hx(ACT)]),
            ("d294_writes", offscreen[0]["watched_writes"][hx(SPECIAL_FLAGS)]),
            ("reading", "with the state forced to $20 and the player placed $%X right of the camera the original callback $83A6 raised D293 bit 4 on its next "
                        "update (act 2); the stage-mode dispatcher then ran $1543 and the stage continued at (zone + 1, 0). The state itself was forced: "
                        "provenance of state $20 inside a stage is the open question." % OFFSCREEN)])),
        ("loader_slot2_equals_d162_mod_32", all(c["loader_calls"][0]["slot2_bank"] == c["loader_calls"][0]["d162"] % 32
                                               for c in sweep if c["loader_calls"])),
    ])
    return OrderedDict([("sweep", by_case), ("natural", natural_by_case), ("meta", meta)])


# --- 14. rendering, checking, command line -----------------------------------------------------------------------------------
BEGIN = "<!-- r3-generated:begin -->"
END_MARK = "<!-- r3-generated:end -->"


def _scalar(o):
    return not isinstance(o, (dict, list, tuple))


def _fmt(o, level=0):
    """Indented JSON in which every list of scalars is on one line (one row of a table per line); deterministic."""
    pad = " " * level
    if isinstance(o, dict):
        if not o:
            return "{}"
        body = (",\n").join("%s %s: %s" % (pad, json.dumps(str(k), ensure_ascii=True), _fmt(v, level + 1)) for k, v in o.items())
        return "{\n" + body + "\n" + pad + "}"
    if isinstance(o, (list, tuple)):
        if all(_scalar(x) for x in o):
            return json.dumps(list(o), ensure_ascii=True, separators=(", ", ": "))
        body = (",\n").join("%s %s" % (pad, _fmt(x, level + 1)) for x in o)
        return "[\n" + body + "\n" + pad + "]"
    return json.dumps(o, ensure_ascii=True)


def dumps(doc):
    return _fmt(doc) + "\n"


def static_view(doc):
    """The part of the evidence that does not depend on the controlled campaign (compared by ``--check`` without ``--controlled``)."""
    d = json.loads(json.dumps(doc))
    d.pop("controlled", None)
    d["verdicts"].pop("U3", None)
    keep = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    d["loader"]["columns"] = [d["loader"]["columns"][i] for i in keep]
    d["loader"]["rows"] = [[r[i] for i in keep] for r in d["loader"]["rows"]]
    d["loader"].pop("row_legend", None)
    d.pop("interaction", None)
    return d


def _group(label):
    if label == "returned":
        return "returned"
    if "executed RAM" in label:
        return "executed RAM"
    if "interrupts disabled" in label:
        return "stalled, interrupts disabled"
    if "restarted at the title" in label:
        return "restarted at the title"
    return "other"


GROUPS = ("returned", "stalled, interrupts disabled", "executed RAM", "restarted at the title", "other")


def render_block(doc):
    u1, u3 = doc["verdicts"]["U1"], doc["verdicts"]["U3"]
    thr = doc["loader"]["thresholds"]
    lines = [BEGIN, "", "| Question | Verdict |", "|---|---|", "| U1 - zone completion inside a special stage | **%s** |" % u1["verdict"],
             "| U3 - out-of-domain record: overall | **%s** |" % u3["overall"], "",
             "U3 verdicts for the %d out-of-domain special-stage rows (zones 8-12 x acts 0-255; %d in-domain rows are not verdict rows):" % (
                 sum(u3["counts"].values()), u3["rows_examined"] - sum(u3["counts"].values())), "",
             "| Zone | " + " | ".join(("PROVEN RETURNABLE", "PROVEN BLOCKED", "PARTIAL", "UNPROVEN")) + " |", "|---|---:|---:|---:|---:|"]
    for z in ("8", "9", "10", "11", "12"):
        c = u3["by_zone"][z]
        lines.append("| %s | %d | %d | %d | %d |" % (z, c.get("PROVEN RETURNABLE", 0), c.get("PROVEN BLOCKED", 0), c.get("PARTIAL", 0), c.get("UNPROVEN", 0)))
    lines += ["", "Static record class by what the controlled run did (accelerated timer; all 1,280 rows, in-domain included):", "",
              "| Record class | " + " | ".join(GROUPS) + " |", "|---|" + "---:|" * len(GROUPS)]
    for cls, outs in u3["static_class_by_controlled_outcome"].items():
        agg = dict.fromkeys(GROUPS, 0)
        for label, n in outs.items():
            agg[_group(label)] += n
        lines.append("| %s | %s |" % (cls, " | ".join(str(agg[g]) for g in GROUPS)))
    ctl = doc["controlled"]
    if "natural_vs_accelerated" in ctl:
        nv = ctl["natural_vs_accelerated"]
        lines += ["", "Natural 59-second timer versus the accelerated one: %d rows run both ways, %d differ (a PROVEN RETURNABLE verdict needs both runs to return): %s." % (
            nv["compared"], len(nv["outcome_differences"]), ", ".join("(%d, %d)" % (z, a) for z, a, _n, _c in nv["outcome_differences"]) or "none")]
    lines += ["", "| Setter | Physical offset | Bank / CPU | Reached by (type, state) |", "|---|---|---|---|"]
    reach = doc["provenance"]["sites_reached_by"]
    for site in doc["setter_sites"]:
        who = "; ".join("$%02X st %s" % (x["type"], ",".join(str(t) for t in x["states"])) for x in reach[hx(site["file_offset"])])
        lines.append("| `%s` | `$%05X` | $%02X / `$%04X` | %s |" % (site["asm"], site["file_offset"], site["bank"], site["cpu"], who))
    lines += ["", "First out-of-domain act per special-stage zone, by table:", "", "| Table | " + " | ".join("zone %s" % z for z in ("8", "9", "10", "11", "12")) + " |",
              "|---|" + "---:|" * 5]
    for key, name in (("loader_record", "loader record ($2A4F)"), ("placement_list", "object list ($8000, bank $1C)"), ("level_header", "level header ($4FDC)"),
                      ("zone_music", "zone music ($18A0)"), ("graphics_rows", "graphics rows ($78E1)")):
        lines.append("| %s | %s |" % (name, " | ".join(str(thr[key][z]["first_out_of_domain_act"]) for z in ("8", "9", "10", "11", "12"))))
    lines.append("")
    for route in u1["routes"]:
        lines.append("* U1 route - %s: **%s** (%s)" % (route["name"], route["status"], route["basis"]))
    lines += ["", END_MARK]
    return "\n".join(lines)


def update_doc(path, doc):
    text = Path(path).read_text(encoding="utf-8")
    block = render_block(doc)
    if BEGIN in text and END_MARK in text:
        a, b = text.index(BEGIN), text.index(END_MARK) + len(END_MARK)
        text = text[:a] + block + text[b:]
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    Path(path).write_text(text, encoding="utf-8")


def doc_block(path):
    text = Path(path).read_text(encoding="utf-8")
    if BEGIN not in text or END_MARK not in text:
        return None
    return text[text.index(BEGIN):text.index(END_MARK) + len(END_MARK)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("rom", nargs="?", default=os.environ.get("SONIC_CHAOS_ROM"))
    ap.add_argument("--output", default=str(OUTPUT))
    ap.add_argument("--doc", default=None, help="rewrite the generated block of this markdown file")
    ap.add_argument("--controlled", action="store_true", help="run the controlled-execution campaign (several minutes)")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--check", action="store_true", help="fail if the committed evidence differs from a fresh run")
    args = ap.parse_args(argv)
    if not args.rom:
        print("pass the ROM path or set SONIC_CHAOS_ROM", file=sys.stderr)
        return 2
    rom = Path(args.rom).read_bytes()
    try:
        verify_rom(rom)
    except ValueError as e:
        print("the ROM is not the canonical Europe v1.2 image: %s" % e, file=sys.stderr)
        return 2
    out = Path(args.output)
    if args.check and not args.controlled:
        doc, _ = build(rom)
        if not out.is_file():
            print("no committed evidence", file=sys.stderr)
            return 1
        committed = json.loads(out.read_text(encoding="utf-8"))
        if static_view(doc) != static_view(committed):
            print("static evidence differs from a fresh run", file=sys.stderr)
            return 1
        print("static evidence matches (controlled block not re-run)")
        return 0
    controlled = run_controlled(rom, workers=args.workers) if args.controlled else None
    doc, _ = build(rom, controlled=controlled)
    text = dumps(doc)
    if args.check:
        if not out.is_file() or out.read_text(encoding="utf-8") != text:
            print("evidence differs from a fresh run", file=sys.stderr)
            return 1
        print("evidence matches")
        return 0
    if controlled is None and out.is_file():
        old = json.loads(out.read_text(encoding="utf-8"))
        if old.get("controlled", {}).get("status") != "not run":
            print("refusing to overwrite committed controlled evidence without --controlled", file=sys.stderr)
            return 3
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    if args.doc:
        update_doc(args.doc, doc)
    print("wrote %s: U1=%s U3=%s" % (out, doc["verdicts"]["U1"]["verdict"], doc["verdicts"]["U3"]["overall"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

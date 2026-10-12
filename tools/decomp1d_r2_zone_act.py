#!/usr/bin/env python3
"""DECOMP-1D-R2: zone/act invariant proof for the three consumers R1 left conditional.

    python tools/decomp1d_r2_zone_act.py /path/to/SonicChaos.sms [--output data/decomp1d/r2-zone-act-invariants.json]

DECOMP-1D-R1 left three dispatchers conditional on facts about the game's zone ($D297) and act ($D298) bytes:

* Proposition A - the zone-music table read at $18A0 indexes ``3*$D297+$D298`` (8-bit) into a 39-entry table;
* Proposition B - the level loader at $2A4F selects a record from ``$D297``/``$D298`` (proposed: zone <= 15, act <= 2);
* Proposition C - the nested dispatcher at $741F1 (bank $1D) indexes its table by ``$D297`` (proposed: zone 0..5 whenever a
  type-5 slot reaches it).

This is *not* the DECOMP-1D assumption R2 (register-addressed stores); the name is only the milestone's.

Method (everything is derived from the ROM; nothing is copied from the POC or from external lists):

1. ``census``       every way the ROM can write the three bytes: absolute stores in every encoding (``LD (nn),A``,
                    ``LD (nn),rr``, ``LD (nn),IX/IY``), their $E000 mirror, immediate pointer materialisations that reach the
                    bytes, and block moves. Anything that cannot be resolved is *listed*, never assumed benign.
2. ``classify``     each store site's value source, by decoding the instructions that feed it.
3. ``Interp``       a small fail-closed concrete Z80 interpreter. The index expressions of the three consumers, the
                    writers' value computations and the guards are *executed* for every input, not pattern-matched.
4. ``Model``        the zone/act transition system whose events are the writer sites; each event carries the ROM facts
                    that justify it and a *grounded* flag (it does not rest on a dependency this task could not discharge).
5. verdicts         PROVEN needs every writer classified, every domain bounded, no unresolved predecessor and no open
                    dependency; DISPROVEN needs a counterexample whose every step is grounded; otherwise PARTIAL/UNPROVEN.

Controlled execution (the interpreter) is corroboration of arithmetic; the proofs are static ROM-derived arguments.
"""
import argparse
import json
import os
import re
import sys
from collections import OrderedDict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1d_banked_flow as D  # noqa: E402
import rom_flow as F  # noqa: E402
from z80dis import z80  # noqa: E402

BANK = 0x4000
ZONE, ACT, SAVED_ZONE = 0xD297, 0xD298, 0xD296
STATE_FLAGS, SPECIAL_FLAGS = 0xD293, 0xD294
EMERALDS, CHARACTER, RING_COUNT, SELECT_INDEX = 0xD2CC, 0xD2C8, 0xD29A, 0xD2C9
SHADOW = 0xD12B
OUTPUT = ROOT / "data" / "decomp1d" / "r2-zone-act-invariants.json"
BASE_COMMIT = "2dcaa09beabe90329deed83af27f2912d19a232f"
ACT_CAP = 40            # the transition model is explored to this act; reaching the cap is reported, not hidden
hx = D.hx


# --- a small fail-closed concrete interpreter ---------------------------------------------------------------------
class Unmodelled(Exception):
    pass


R8 = ("A", "B", "C", "D", "E", "H", "L")
R16 = {"BC": ("B", "C"), "DE": ("D", "E"), "HL": ("H", "L")}
CONDS = ("nz", "z", "nc", "c")


def _num(text):
    return int(text.strip(), 0)


class Interp:
    """Concrete interpreter over a whitelist of Z80 instructions.

    Registers are concrete bytes; RAM is a dict (a read of an address that was never written or supplied raises, so a
    result never rests on an invented value); ROM is read through the supplied slot-1/slot-2 banks (slot 0 is bank 0, which
    :func:`slot0_is_fixed` checks); writes to ROM or the mapper raise. Flags: only Z and C are modelled.
    """

    def __init__(self, rom, ram=None, slot1=1, slot2=2, regs=None):
        self.rom, self.ram = rom, dict(ram or {})
        self.slot1, self.slot2 = slot1, slot2
        self.reg = dict.fromkeys(R8, 0)
        self.reg.update(regs or {})
        self.z = self.c = False
        self.writes = []                      # (cpu address, value) in order
        self.reads = []                       # RAM addresses read
        self.steps = 0
        self.pc = 0
        self.stack = []
        self.returned = False

    # memory ------------------------------------------------------------------------------------------------------
    def file_of(self, cpu):
        if cpu < 0x4000:
            return cpu
        if cpu < 0x8000:
            if self.slot1 is None:
                raise Unmodelled("slot-1 bank unverified at $%04X" % cpu)
            return self.slot1 * BANK + cpu - 0x4000
        if cpu < 0xC000:
            if self.slot2 is None:
                raise Unmodelled("slot-2 bank unverified at $%04X" % cpu)
            return self.slot2 * BANK + cpu - 0x8000
        return None

    def read(self, cpu):
        cpu &= 0xFFFF
        f = self.file_of(cpu)
        if f is not None:
            if f >= len(self.rom):
                raise Unmodelled("read beyond the ROM at $%04X" % cpu)
            return self.rom[f]
        key = cpu & 0xDFFF if cpu >= 0xE000 else cpu
        if key not in self.ram:
            raise Unmodelled("read of unsupplied RAM $%04X" % cpu)
        self.reads.append(key)
        return self.ram[key]

    def write(self, cpu, value):
        cpu &= 0xFFFF
        if cpu < 0xC000 or cpu >= 0xFFFC:
            raise Unmodelled("write to ROM/mapper at $%04X" % cpu)
        key = cpu & 0xDFFF if cpu >= 0xE000 else cpu
        self.ram[key] = value & 0xFF
        self.writes.append((key, value & 0xFF))

    # registers ---------------------------------------------------------------------------------------------------
    def get16(self, name):
        hi, lo = R16[name]
        return self.reg[hi] << 8 | self.reg[lo]

    def set16(self, name, value):
        hi, lo = R16[name]
        self.reg[hi], self.reg[lo] = (value >> 8) & 0xFF, value & 0xFF

    def val(self, operand):
        operand = operand.strip()
        if operand in R8:
            return self.reg[operand]
        if operand == "(HL)":
            return self.read(self.get16("HL"))
        if operand.startswith("(0x"):
            return self.read(_num(operand[1:-1]))
        return _num(operand)

    def put8(self, operand, value):
        operand = operand.strip()
        value &= 0xFF
        if operand in R8:
            self.reg[operand] = value
        elif operand == "(HL)":
            self.write(self.get16("HL"), value)
        elif operand.startswith("(0x"):
            self.write(_num(operand[1:-1]), value)
        else:
            raise Unmodelled("destination %r" % operand)

    def cond(self, name):
        if name == "nz":
            return not self.z
        if name == "z":
            return self.z
        if name == "nc":
            return not self.c
        if name == "c":
            return self.c
        raise Unmodelled("condition %r" % name)

    # execution ---------------------------------------------------------------------------------------------------
    def step(self):
        f = self.file_of(self.pc)
        if f is None:
            raise Unmodelled("pc in RAM $%04X" % self.pc)
        d = z80.decode(bytes(self.rom[f:f + 4]), self.pc)
        if not d.len or d.op == F.OP.NONI:
            raise Unmodelled("undecodable at $%04X" % self.pc)
        text = z80.disasm(d)
        self.steps += 1
        nxt = self.pc + d.len
        mn, _, rest = text.partition(" ")
        mn = mn.upper()
        ops = [o for o in re.split(r",(?![^()]*\))", rest)] if rest else []
        if mn == "NOP":
            pass
        elif mn == "LD":
            self._ld(ops)
        elif mn in ("INC", "DEC"):
            self._incdec(mn, ops[0].strip())
        elif mn in ("ADD", "SUB", "AND", "OR", "XOR", "CP"):
            self._alu(mn, ops)
        elif mn in ("RLCA", "RRCA"):
            a = self.reg["A"]
            if mn == "RLCA":
                self.c, self.reg["A"] = bool(a & 0x80), ((a << 1) | (a >> 7)) & 0xFF
            else:
                self.c, self.reg["A"] = bool(a & 1), ((a >> 1) | (a << 7)) & 0xFF
        elif mn == "EX" and [o.strip() for o in ops] == ["DE", "HL"]:
            de, hl = self.get16("DE"), self.get16("HL")
            self.set16("DE", hl)
            self.set16("HL", de)
        elif mn == "JR" or mn == "JP":
            if len(ops) == 2:
                if self.cond(ops[0].strip()):
                    nxt = _num(ops[1])
            elif ops[0].strip().startswith("("):
                raise Unmodelled("computed jump")
            else:
                nxt = _num(ops[0])
        elif mn == "CALL":
            if len(ops) == 2:
                if self.cond(ops[0].strip()):
                    self.stack.append(nxt)
                    nxt = _num(ops[1])
            else:
                self.stack.append(nxt)
                nxt = _num(ops[0])
        elif mn == "RET":
            if not ops or self.cond(ops[0].strip()):
                if not self.stack:
                    self.returned = True
                    return text
                nxt = self.stack.pop()
        elif mn == "DJNZ":
            self.reg["B"] = (self.reg["B"] - 1) & 0xFF
            if self.reg["B"]:
                nxt = _num(ops[0])
        elif mn in ("SET", "RES"):
            bit = int(ops[0])
            target = ops[1].strip()
            v = self.val(target)
            self.put8(target, (v | 1 << bit) if mn == "SET" else (v & ~(1 << bit)))
        elif mn == "BIT":
            self.z = not (self.val(ops[1]) >> int(ops[0])) & 1
        else:
            raise Unmodelled("instruction %r at $%04X" % (text, self.pc))
        self.pc = nxt
        return text

    def _ld(self, ops):
        dst, src = ops[0].strip(), ops[1].strip()
        if dst in R16 and src.startswith("(0x"):
            addr = _num(src[1:-1])
            self.reg[R16[dst][1]], self.reg[R16[dst][0]] = self.read(addr), self.read(addr + 1)
        elif dst in R16 and not src.startswith("("):
            self.set16(dst, _num(src))
        elif dst.startswith("(0x") and src in R16:
            addr = _num(dst[1:-1])
            self.write(addr, self.reg[R16[src][1]])
            self.write(addr + 1, self.reg[R16[src][0]])
        elif dst in R8 or dst.startswith("("):
            if dst.startswith("(") and src.startswith("("):
                raise Unmodelled("memory-to-memory load")
            self.put8(dst, self.val(src))
        else:
            raise Unmodelled("load %s,%s" % (dst, src))

    def _incdec(self, mn, op):
        if op in R16:
            self.set16(op, self.get16(op) + (1 if mn == "INC" else -1))
            return
        v = (self.val(op) + (1 if mn == "INC" else -1)) & 0xFF
        self.put8(op, v)
        self.z = v == 0

    def _alu(self, mn, ops):
        if mn == "ADD" and ops[0].strip() == "HL":
            total = self.get16("HL") + self.get16(ops[1].strip())
            self.c = total > 0xFFFF
            self.set16("HL", total)
            return
        if len(ops) == 2:
            if ops[0].strip() != "A":
                raise Unmodelled("ALU destination")
            operand = ops[1]
        else:
            operand = ops[0]
        a, b = self.reg["A"], self.val(operand)
        if mn == "ADD":
            r = a + b
            self.c, a = r > 0xFF, r & 0xFF
        elif mn == "SUB":
            self.c, a = b > a, (a - b) & 0xFF
        elif mn == "AND":
            a, self.c = a & b, False
        elif mn == "OR":
            a, self.c = a | b, False
        elif mn == "XOR":
            a, self.c = a ^ b, False
        else:                                  # CP
            self.c, self.z = b > a, a == b
            return
        self.reg["A"] = a
        self.z = a == 0

    def run(self, start, stops=(), limit=400):
        """Execute from ``start`` until the pc reaches one of ``stops`` (not executed) or the outermost RET is taken.
        Returns ``"stop"`` or ``"ret"``. Anything else raises :class:`Unmodelled`."""
        self.pc, self.returned = start, False
        stops = set(stops)
        for _ in range(limit):
            if self.pc in stops:
                return "stop"
            self.step()
            if self.returned:
                return "ret"
        raise Unmodelled("step limit from $%04X" % start)


class Code:
    """The aligned-instruction universe: every instruction the DECOMP-1D mapper-aware walk reaches from the reset, IM 1 and
    NMI vectors (``Facts.walk``; restarts followed). A byte pattern outside it is *not* shown to be data - the walk has open
    computed jumps - so such hits are reported as ``undiscovered`` rather than dismissed."""

    def __init__(self, rom, roots=None):
        self.rom = rom
        self.walk = D.Facts.of(rom).walk if roots is None else D.state_walk(rom, list(roots), SHADOW, follow_restart=True)
        self.starts = {}
        for off in self.walk["visited"]:
            d = F.decode(rom, off)
            if not F.is_invalid(d):
                self.starts[off] = d
        self._ends = {}
        for off, d in self.starts.items():
            if not F.is_terminal(d):
                self._ends.setdefault(off + d.len, []).append(off)

    def __contains__(self, off):
        return off in self.starts

    def predecessors(self, off):
        """Fall-through predecessors: instructions of the universe that end exactly at ``off``."""
        return sorted(self._ends.get(off, []))


def slot0_mapper_stores(rom, code):
    """Stores to the slot-0 mapper register $FFFD. Those in discovered code must all write 0 for slot 0 to be bank 0
    throughout; a byte-pattern hit outside the discovered code (tile data, say) is listed separately, not dismissed."""
    in_code, outside = [], []
    for off, kind in D.store_pattern_sites(rom, 0xFFFD):
        if off in code and kind == "LD (nn),A":
            k, v, _ev = feeder_of_a(rom, code, off)
            in_code.append(OrderedDict([("file_offset", off), ("value", v if k == "const" else None)]))
        else:
            outside.append(off)
    return OrderedDict([("in_discovered_code", in_code), ("outside_discovered_code", outside),
                        ("slot0_is_bank_0_in_code", all(r["value"] == 0 for r in in_code))])


# --- 1. census ------------------------------------------------------------------------------------------------------
TARGETS = OrderedDict([("zone", ZONE), ("act", ACT), ("saved_zone", SAVED_ZONE)])


def store_census(rom, addrs=None):
    """Every encoding of an absolute store that writes ``addr`` or its $E000 mirror. Wide stores (rr, IX, IY) covering the
    byte are included. Alignment-independent: a hit in data is listed too (and classified as such if unclassifiable)."""
    out = OrderedDict()
    for name, addr in (addrs or TARGETS).items():
        sites = []
        for a, alias in ((addr, False), (addr + 0x2000, True)):
            for off, kind in D.store_pattern_sites(rom, a):
                sites.append(OrderedDict([("file_offset", off), ("form", kind), ("mirror_alias", alias)]))
        out[name] = sorted(sites, key=lambda s: (s["file_offset"], s["form"]))
    return out


def decode_at(rom, off):
    d = F.decode(rom, off)
    return d, ("??" if F.is_invalid(d) else z80.disasm(d))


def preceding(code, off, count=3):
    """The instructions that lead into ``off`` along the unique fall-through of the discovered-code universe."""
    return code.chain(off, count)


OP_JP, OP_CALL = F.OP.JP, F.OP.CALL


PRESERVES_A = re.compile(r"^(LD \(0x[0-9a-f]+\),(A|HL|DE|BC|SP)|LD [BCDEHL],A|INC (HL|DE|BC)|DEC (HL|DE|BC)|PUSH |NOP|LD \([HLDEBC]+\),A)$")


def local_predecessor(rom, off):
    """The instruction that ends at ``off`` when the discovered-code universe does not cover it: the unique decode of
    1..4 bytes whose length lands exactly on ``off`` and that falls through."""
    found = []
    for length in range(1, 5):
        d = F.decode(rom, off - length)
        if not F.is_invalid(d) and d.len == length and not F.is_terminal(d) and d.op not in (OP_JP,):
            found.append((off - length, z80.disasm(d)))
    if len(found) > 1:
        # a misaligned shorter decode can also land on ``off``; accept the one that is an A-feeder pattern if only one is
        found = [x for x in found if re.match(r"^(LD A,(0x[0-9a-f]+|\d+)|XOR A)$", x[1])]
    return found[0] if len(found) == 1 else None


def feeder_of_a(rom, code, off):
    """What A holds when the instruction at ``off`` executes, from the straight-line instructions before it.

    Returns ``(kind, value, evidence)`` with kind in ``const``, ``copy`` (value is the RAM address), ``increment``
    (value is the RAM address that was loaded and incremented), ``other`` (value is the feeding text) or ``none``."""
    ev, cur = [], off
    for _ in range(6):
        preds = code.predecessors(cur) if cur in code or code.predecessors(cur) else []
        pred = (preds[0], z80.disasm(code.starts[preds[0]])) if len(preds) == 1 else (local_predecessor(rom, cur) if not preds else None)
        if pred is None:
            return "none", None, ev
        cur, text = pred
        ev.insert(0, text)
        if PRESERVES_A.match(text):
            continue
        if text == "XOR A":
            return "const", 0, ev
        m = re.match(r"LD A,(0x[0-9a-f]+|\d+)$", text)
        if m:
            return "const", _num(m.group(1)), ev
        if text == "RET nz":
            pp = code.predecessors(cur)
            prev = (z80.disasm(code.starts[pp[0]]) if len(pp) == 1 else None)
            if prev == "OR A":
                ev.insert(0, prev)
                return "const", 0, ev
            return "other", text, ev
        if text == "INC A":
            q = code.predecessors(cur)
            prev = z80.disasm(code.starts[q[0]]) if len(q) == 1 else None
            m = re.match(r"LD A,\((0x[0-9a-f]+)\)$", prev or "")
            if m:
                ev.insert(0, prev)
                return "increment", _num(m.group(1)), ev
            return "other", text, ev
        m = re.match(r"LD A,\((0x[0-9a-f]+)\)$", text)
        if m:
            return "copy", _num(m.group(1)), ev
        return "other", text, ev
    return "none", None, ev


def classify_store(rom, code, site, addr):
    """Value source of the store at ``site``. Fail-closed: anything not recognised is ``unclassified`` (and the writer set is
    then reported as not fully classified)."""
    d, text = decode_at(rom, site["file_offset"])
    if site["form"] != "LD (nn),A":
        return OrderedDict([("kind", "unclassified"), ("reason", "wide store %s" % site["form"]), ("evidence", [text])])
    kind, value, ev = feeder_of_a(rom, code, site["file_offset"])
    ev = ev + [text]
    undiscovered = site["file_offset"] not in code
    out = OrderedDict()
    if kind == "const":
        out.update([("kind", "const"), ("value", value)])
    elif kind == "increment" and value == addr:
        out["kind"] = "increment"
    elif kind == "copy":
        out.update([("kind", "copy"), ("source", hx(value))])
    elif kind == "other" and (value in ("LD A,(HL)", "LD A,B") or str(value).startswith(("AND ", "OR "))):
        out["kind"] = "computed"
    else:
        out.update([("kind", "unclassified"), ("reason", "feeder %r not recognised" % (value,))])
    if undiscovered:
        out["in_discovered_code"] = False
    out["evidence"] = ev
    return out


def pointer_materialisations(rom, code, lo=0xD290, hi=0xD298, span=6):
    """Immediate loads ``LD rr,nn`` / ``LD IX|IY,nn`` whose value lies in [lo, hi] (or its mirror).

    Each is followed for up to ``span`` straight-line instructions to find the stores made through the loaded pair. A hit
    is ``resolved`` when only ``SET/RES/LD (HL),x`` style stores through an unmodified pair follow (the written address
    is then exact) and ``unresolved`` otherwise (pointer arithmetic, a reload, a block move, an index register with a
    displacement). Unresolved hits are listed and keep the writer set open; they are never assumed benign."""
    forms = (("HL", b"\x21"), ("DE", b"\x11"), ("BC", b"\x01"), ("IX", b"\xdd\x21"), ("IY", b"\xfd\x21"))
    hits = set()
    for name, prefix in forms:
        for base in (0, 0x2000):
            for v in range(lo + base, hi + base + 1):
                needle = prefix + bytes([v & 0xFF, v >> 8])
                i = rom.find(needle)
                while i != -1:
                    hits.add((i, name, v))
                    i = rom.find(needle, i + 1)
    out = []
    for off, name, v in sorted(hits):
        pos = off + len(forms[[f[0] for f in forms].index(name)][1]) + 2
        ins, p = [], pos
        for _ in range(span):
            d = F.decode(rom, p)
            if F.is_invalid(d):
                break
            ins.append(z80.disasm(d))
            p += d.len
            if F.is_terminal(d) or d.op in (OP_JP, OP_CALL):
                break
        res = OrderedDict([("file_offset", off), ("register", name), ("value", v), ("next", ins[:4])])
        if off not in code:
            res["status"], res["why"], res["touches_targets"] = "undiscovered", "not in the discovered-code universe", None
            out.append(res)
            continue
        if name in ("IX", "IY"):
            res["status"], res["why"] = "unresolved", "index-register displacement writes are not interpreted"
            res["touches_targets"] = None
            out.append(res)
            continue
        pair, addr, writes, status, why = name, v, [], "resolved", None
        for t in ins:
            mn, _, rest = t.partition(" ")
            mn = mn.upper()
            ops = [o.strip() for o in re.split(r",(?![^()]*\))", rest)] if rest else []
            tokens = set(re.findall(r"[A-Z]+", " ".join(ops).upper()))
            if mn in ("JP", "JR", "CALL", "RET", "DJNZ", "RST"):
                break
            if mn == "LD" and ops and ops[0] == pair:
                break                                                  # the pair is replaced: later stores use a new value
            if mn in ("INC", "DEC") and ops == [pair]:
                addr += 1 if mn == "INC" else -1
            elif mn == "LD" and ops and ops[0] == "(%s)" % pair:
                writes.append(addr)
            elif mn in ("SET", "RES") and len(ops) == 2 and ops[1] == "(%s)" % pair:
                writes.append(addr)
            elif pair not in tokens or (len(ops) == 2 and ops[1] == "(%s)" % pair and mn in ("LD", "ADD", "SUB", "CP", "AND", "OR", "XOR")) \
                    or (mn == "BIT" and ops[-1:] == ["(%s)" % pair]) or (mn in ("CP", "AND", "OR", "XOR", "SUB") and ops == ["(%s)" % pair]):
                pass                                                   # no use of the pair, or a read through it
            else:
                status, why = "unresolved", "pair used by %r" % t
                break
        res["status"] = status
        if why:
            res["why"] = why
        res["resolved_writes"] = [hx(a) for a in writes]
        res["touches_targets"] = (any(a in (ZONE, ACT, SAVED_ZONE) or a - 0x2000 in (ZONE, ACT, SAVED_ZONE) for a in writes)
                                  if status == "resolved" else None)
        out.append(res)
    return out


def block_move_sites(rom, code):
    """Every LDIR/LDDR/LDI/LDD, with the destination range when both DE and BC are immediate loads on the straight
    line before it; otherwise ``unresolved``."""
    out = []
    for sig, name in ((b"\xed\xb0", "LDIR"), (b"\xed\xb8", "LDDR"), (b"\xed\xa0", "LDI"), (b"\xed\xa8", "LDD")):
        i = rom.find(sig)
        while i != -1:
            out.append((i, name))
            i = rom.find(sig, i + 1)
    result = []
    for off, name in sorted(out):
        de = bc = hl = None
        for back in range(24, 0, -1):
            p, ok, got_de, got_bc, got_hl, clobber = off - back, True, None, None, None, False
            while p < off:
                d = F.decode(rom, p)
                if F.is_invalid(d) or F.is_terminal(d) or d.op in (OP_JP, OP_CALL):
                    ok = False
                    break
                t = z80.disasm(d)
                m = re.match(r"LD (DE|BC|HL),(0x[0-9a-f]+|\d+)$", t)
                if m:
                    if m.group(1) == "DE":
                        got_de = _num(m.group(2))
                    elif m.group(1) == "HL":
                        got_hl = _num(m.group(2))
                    else:
                        got_bc = _num(m.group(2))
                elif re.search(r"\b(DE|BC)\b", t) and not t.startswith(("PUSH", "POP")) and "LD (" not in t:
                    clobber = True
                elif t.startswith(("POP DE", "POP BC", "EXX", "EX DE,HL", "INC DE", "INC BC", "DEC DE", "DEC BC")):
                    clobber = True
                p += d.len
            if ok and p == off and got_de is not None and got_bc is not None and not clobber:
                de, bc = got_de, got_bc
                hl = got_hl if got_hl is not None else hl
        rec = OrderedDict([("file_offset", off), ("op", name)])
        if off not in code:
            rec["status"], rec["touches_targets"] = "undiscovered", None
        elif de is not None and name == "LDIR":
            rec["status"] = "resolved"
            rec["destination"] = [hx(de), hx(de + bc - 1)]
            rec["touches_targets"] = any(de <= t_ <= de + bc - 1 or de <= t_ + 0x2000 <= de + bc - 1 for t_ in (ZONE, ACT, SAVED_ZONE))
            rec["fill_zero"] = bool(hl is not None and hl == de - 1 and rom[off - 2:off] == b"\x36\x00")
        else:
            rec["status"] = "unresolved"
            rec["touches_targets"] = None
        result.append(rec)
    return result


def boot_clear(rom, code):
    """The reset/restart RAM clear (``LD (HL),0`` + ``LDIR`` with DE = HL + 1): the resolved block moves that zero a target."""
    out = []
    for site in block_move_sites(rom, code):
        if site["op"] == "LDIR" and site["status"] == "resolved" and site["touches_targets"] and site.get("fill_zero"):
            off = site["file_offset"]
            out.append(OrderedDict([("file_offset", off), ("clears", site["destination"]),
                                    ("writes_value_zero", rom[off - 2:off] == b"\x36\x00")]))
    return out


# --- 2. dispatcher bit maps -----------------------------------------------------------------------------------------
def rlca_chain(rom, start, count=12, rot0=0):
    """Starting at ``start`` (just after a ``LD A,(flags)``), decode the ``RLCA`` / ``JP cc`` chain and return
    ``{bit: (cc, target)}`` for the branches that test the carry (the bit rotated out)."""
    bits, rot, p = OrderedDict(), rot0, start
    for _ in range(count * 3):
        d = F.decode(rom, p)
        t = z80.disasm(d) if not F.is_invalid(d) else "??"
        if t == "RLCA":
            rot += 1
        elif t.startswith("JP "):
            m = re.match(r"JP (c|nc),(0x[0-9a-f]+)$", t)
            if not m:
                break
            bits[7 - (rot - 1)] = (m.group(1), _num(m.group(2)))
        else:
            break
        p += d.len
    return bits


def flag_setters(rom, code, flag_addr):
    """Every way the ROM sets or clears a bit of ``flag_addr``: ``SET/RES b,(HL)`` that follows ``LD HL,flag_addr`` on the
    straight line, absolute stores (with the immediate value where one precedes), and wide stores."""
    out = OrderedDict([("hl_bit_ops", []), ("absolute_stores", []), ("wide_stores", [])])
    needle = b"\x21" + bytes([flag_addr & 0xFF, flag_addr >> 8])
    i = rom.find(needle)
    while i != -1:
        p, seq = i + 3, []
        for _ in range(3):
            d = F.decode(rom, p)
            if F.is_invalid(d):
                break
            t = z80.disasm(d)
            seq.append((p, t))
            p += d.len
            if not (t.startswith(("SET", "RES", "INC", "LD (HL)", "BIT"))):
                break
        for q, t in seq:
            if t.startswith(("SET ", "RES ")) and t.endswith("(HL)"):
                out["hl_bit_ops"].append(OrderedDict([("hl_load", i), ("file_offset", q), ("op", t)]))
            elif t.startswith("LD (HL),"):
                out["hl_bit_ops"].append(OrderedDict([("hl_load", i), ("file_offset", q), ("op", t)]))
        i = rom.find(needle, i + 1)
    for off, kind in D.store_pattern_sites(rom, flag_addr):
        rec = OrderedDict([("file_offset", off), ("form", kind)])
        (out["absolute_stores"] if kind == "LD (nn),A" else out["wide_stores"]).append(rec)
    return out


# --- 3. consumers (executed) ----------------------------------------------------------------------------------------
class Consumer:
    """A consumer's index computation, executed for every (zone, act) input."""

    def __init__(self, rom, name, start, read_pc, base, slot2, extent, zone_addr=ZONE, act_addr=ACT):
        self.rom, self.name, self.start, self.read_pc = rom, name, start, read_pc
        self.base, self.slot2, self.extent = base, slot2, extent
        self.zone_addr, self.act_addr = zone_addr, act_addr

    def address(self, zone, act, extra=None):
        ram = {self.zone_addr: zone, self.act_addr: act}
        ram.update(extra or {})
        m = Interp(self.rom, ram=ram, slot1=1, slot2=self.slot2)
        why = m.run(self.start, stops=(self.read_pc,))
        if why != "stop":
            raise Unmodelled("%s: expression ended at RET" % self.name)
        return m.get16("HL")

    def index(self, zone, act, extra=None):
        return self.address(zone, act, extra) - self.base

    def valid(self, zone, act, extra=None):
        return 0 <= self.index(zone, act, extra) < self.extent


def music_consumer(rom):
    return Consumer(rom, "zone_music_read", 0x18A0, 0x18B2, 0x18BA, 2, table_extent_by_code_entry(rom, 0x18BA))


def table_extent_by_code_entry(rom, base, search=0x80):
    """Entries between ``base`` and the first address above it that is the target of a ``CALL``/``JP`` (i.e. code, not
    table). The first such target bounds the table from above."""
    targets = set()
    for op in (0xCD, 0xC3):
        i = rom.find(bytes([op]))
        while i != -1:
            t = rom[i + 1] | rom[i + 2] << 8 if i + 2 < len(rom) else None
            if t is not None and base < t <= base + search:
                targets.add(t)
            i = rom.find(bytes([op]), i + 1)
    return (min(targets) - base) if targets else None


# --- 4. the transition model ----------------------------------------------------------------------------------------
def explore(initial, step, cap=ACT_CAP, grounded_only=False, skip_classes=(), classes=None):
    """Breadth-first exploration of a finite transition system.

    ``initial`` is a list of ``(state, grounded)``; ``step(state)`` yields ``(event, next_state, grounded, intermediates)``.
    A state is ``(zone, act, mode, saved)``. With ``grounded_only`` an edge whose ``grounded`` flag is False is not taken,
    so the result is the set of states reachable using only edges that rest on nothing unresolved; ``skip_classes`` drops
    events of the given classes (``classes`` maps event name -> class) so a path can be restricted to normal play. A state
    whose act exceeds ``cap`` is cut off and returned in ``cut`` (a cap is reported, never silently applied).

    Returns ``(seen, cut, intermediates)``; ``intermediates`` maps every transient (zone, act) pair a taken edge passes
    through to the event that produces it."""
    seen, cut, inters, dq = OrderedDict(), set(), OrderedDict(), deque()
    for s, g in initial:
        if (g or not grounded_only) and s not in seen:
            seen[s] = (None, "initial", ())
            dq.append(s)
    while dq:
        s = dq.popleft()
        for ev, nxt, ng, inter in step(s):
            if grounded_only and not ng:
                continue
            if classes and classes.get(ev) in skip_classes:
                continue
            if nxt[1] > cap:
                cut.add(nxt)
                continue
            for pair in inter:
                inters.setdefault(tuple(pair), ev)
            if nxt not in seen:
                seen[nxt] = (s, ev, inter)
                dq.append(nxt)
    return seen, sorted(cut), inters


def path_to(table, state):
    chain = []
    while state is not None and state in table:
        parent, ev, inter = table[state]
        chain.append(OrderedDict([("state", list(state)), ("via", ev),
                                  ("intermediate", [list(x) for x in inter])]))
        state = parent
    return list(reversed(chain))


# --- 5. executed facts ----------------------------------------------------------------------------------------------
def execute(rom, start, ram, slot2=2, slot1=1, stops=(), regs=None):
    m = Interp(rom, ram=ram, slot1=slot1, slot2=slot2, regs=regs)
    why = m.run(start, stops)
    return m, why


def select_table_pairs(rom):
    """The level-select pair for every select index 0..$11 (executes $0815..$0829)."""
    out = OrderedDict()
    for i in range(0x12):
        m, _ = execute(rom, 0x0815, {SELECT_INDEX: i})
        out[i] = (m.ram[ZONE], m.ram[ACT])
    return out


def select_index_step(rom, v):
    """Both writers of the select index that the select loop can run ($08A2 decrement, $08AC increment) on value ``v``."""
    res = []
    for entry in (0x08A2, 0x08AC):
        m, _ = execute(rom, entry, {SELECT_INDEX: v})
        res.append(m.ram.get(SELECT_INDEX, v))
    return res


def select_index_domain(rom):
    """Least fixpoint of the select index from 0 under the two loop writers; the loop writers are executed, not assumed."""
    seen, todo = {0}, [0]
    while todo:
        v = todo.pop()
        for n in select_index_step(rom, v):
            if n not in seen:
                seen.add(n)
                todo.append(n)
    return sorted(seen)


def rotation_rows(rom):
    """Zone/act/character written by the rotating selection ($2C34), for every value of its counter and both tables."""
    out = set()
    for counter in range(256):
        for table in (0, 1):
            m, _ = execute(rom, 0x2C34, {0xD2E3: counter, 0xD12D: table})
            out.add((m.ram[ZONE], m.ram[ACT], m.ram[CHARACTER]))
    return sorted(out)


def special_stage_zone(rom, zone_in=3):
    """The special-stage zone written by $187B for every emerald byte, and the saved zone it copies."""
    zones = OrderedDict()
    for mask in range(256):
        m, _ = execute(rom, 0x187B, {ZONE: zone_in, EMERALDS: mask})
        zones.setdefault(m.ram[ZONE], []).append(mask)
        assert m.ram[SAVED_ZONE] == zone_in
    return zones


def special_stage_entry_guard(rom):
    """Executes $178F over a grid and records which RAM bytes it reads and when it arms the special stage ($D294 := $88)."""
    reads, armed = set(), []
    for c8 in (0, 1, 2, 3, 255):
        for z in (0, 1, 5, 6, 7, 8, 12, 13, 255):
            for mask in (0x00, 0x01, 0x0F, 0x1E, 0x1F, 0x20, 0x3F, 0xFF):
                m, _ = execute(rom, 0x178F, {CHARACTER: c8, ZONE: z, EMERALDS: mask, 0xD2BE: 0, 0xD2C2: 0,
                                             SPECIAL_FLAGS: 0, 0xD2CD: 0})
                reads.update(m.reads)
                if m.ram.get(SPECIAL_FLAGS) == 0x88:
                    armed.append((c8, z, mask))
    rule = all(((c8 == 1 and z < 6 and (mask & 0x1F) != 0x1F)) for c8, z, mask in armed)
    complete = all(((c8, z, mask) in set(armed)) for c8 in (1,) for z in (0, 1, 5) for mask in (0x00, 0x01, 0x0F, 0x1E, 0x20))
    return OrderedDict([("reads", sorted(hx(a) for a in reads)), ("reads_act", ACT in reads),
                        ("armed_only_when_character_1_zone_lt_6_emeralds_not_full", rule),
                        ("armed_for_all_sampled_such_inputs", complete)])


def level_end_flag(rom):
    """The flag the level-end trigger at $303DD raises, per act (executes it with slot 2 = bank $0C)."""
    out = OrderedDict()
    for act in range(256):
        m, _ = execute(rom, 0x83DD, {ACT: act, STATE_FLAGS: 0}, slot2=0x0C)
        out[act] = m.ram[STATE_FLAGS]
    return out


def zone_complete_effect(rom):
    """$15CE..$15D9: act := 0, zone := zone + 1, then the branch on zone >= 6 ($15DE / $15E8)."""
    out = OrderedDict()
    for z in range(256):
        m, _ = execute(rom, 0x15CE, {ZONE: z, ACT: 7}, stops=(0x15DE, 0x15E8))
        out[z] = (m.ram[ZONE], m.ram[ACT], m.pc)
    return out


def special_stage_exit_effect(rom):
    """$1869..$1878: the zone restored from the saved zone, whether the act is left untouched, the special-flag byte after
    and the state-flag byte after (bit 5 raised = the act-complete path)."""
    out = OrderedDict()
    for saved in range(16):
        res = []
        for act in (4, 77):
            m, _ = execute(rom, 0x1869, {SAVED_ZONE: saved, ZONE: 9, ACT: act, SPECIAL_FLAGS: 0x80, STATE_FLAGS: 0x40},
                           stops=(0x1333,))
            res.append((m.ram[ZONE], m.ram[ACT] == act, m.ram[SPECIAL_FLAGS], m.ram[STATE_FLAGS]))
        assert res[0] == res[1]
        out[saved] = res[0]
    return out


def act_complete_effect(rom):
    out = OrderedDict()
    for a in range(256):
        m, _ = execute(rom, 0x152F, {ACT: a, STATE_FLAGS: 0x60}, stops=(0x1333,))
        out[a] = (m.ram[ACT], m.ram[STATE_FLAGS])
    return out


# --- 6. the loader (Proposition B) ---------------------------------------------------------------------------------
LOADER = 0x2A4F
ZONE_TABLE = 0x2A9A
SLOT_TYPES = (0xD452, 0xD45A, 0xD462, 0xD46A)


def loader_run(rom, zone, act):
    """Execute the level loader for (zone, act). Returns ``(record_pointer, slot_types, error)``; ``error`` is set (and the
    rest ``None``) when the run needs memory whose bank is unverified - e.g. a record pointer into slot 1 or slot 2 - so a
    garbage pointer is *unresolved*, never interpreted."""
    m = Interp(rom, ram={ZONE: zone, ACT: act}, slot1=None, slot2=None)
    try:
        m.run(LOADER, stops=(0x2A6D,))                 # HL = record pointer, just before LD E,(HL)
        ptr = m.get16("HL")
        m.run(0x2A6D, stops=())
    except Unmodelled as e:
        return None, None, str(e)
    return ptr, tuple(m.ram[a] for a in SLOT_TYPES), None


def loader_tables(rom):
    """Record pointers for every (zone 0..15, act 0..255); the set R of records the proposed domain selects; per-zone
    safe act bound (largest A such that acts 0..A all select a record of R)."""
    ptr = OrderedDict()
    for z in range(16):
        for a in range(256):
            rec, types, err = loader_run(rom, z, a)
            ptr[(z, a)] = (rec, types, err)
    proposed = sorted({ptr[(z, a)][0] for z in range(16) for a in range(3) if ptr[(z, a)][2] is None})
    safe = OrderedDict()
    for z in range(16):
        a = -1
        while a + 1 < 256 and ptr[(z, a + 1)][0] in proposed and ptr[(z, a + 1)][2] is None:
            a += 1
        safe[z] = a
    return ptr, proposed, safe


# --- 7. the nested dispatcher (Proposition C) ----------------------------------------------------------------------
NESTED_START, NESTED_JP = 0x81E0, 0x81F1
NESTED_BANK = 0x1D
NESTED_TABLE = 0x81F2


def nested_word_address(rom, zone, b):
    """Address of the table word fetched for (zone, B): HL just before ``LD E,(HL)`` at $81ED."""
    m = Interp(rom, ram={ZONE: zone}, slot1=1, slot2=NESTED_BANK, regs={"B": b})
    m.run(NESTED_START, stops=(0x81ED,))
    return m.get16("HL")


def nested_target(rom, zone, b):
    m = Interp(rom, ram={ZONE: zone}, slot1=1, slot2=NESTED_BANK, regs={"B": b})
    m.run(NESTED_START, stops=(NESTED_JP,))
    return m.get16("HL")


def nested_table(rom):
    """Table extent by the code's own words: read words from the base while the word's address is below the lowest target
    seen so far (a word at or above the lowest target is code, not table). Returns ``(entries, end_address)``."""
    entries, addr, low = [], NESTED_TABLE, 0xFFFF
    while addr < low:
        off = NESTED_BANK * BANK + addr - 0x8000
        t = rom[off + 1] << 8 | rom[off]
        entries.append(t)
        low = min(low, t)
        addr += 2
    return entries, addr


# --- 8. flow facts --------------------------------------------------------------------------------------------------
def operand_addresses(rom, start, end):
    """Absolute data addresses named by the instructions decoded linearly from ``start`` to ``end``."""
    out, p = [], start
    while p < end:
        d = F.decode(rom, p)
        if F.is_invalid(d):
            break
        for kind, value in d.operands:
            if kind.name == "ADDR_DEREF":
                out.append(value)
        p += d.len
    return out


CALL_JUMP_OPCODES = OrderedDict(
    [(0xCD, "CALL"), (0xC3, "JP")]
    + [(op, "CALL cc") for op in (0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC)]
    + [(op, "JP cc") for op in (0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA)])


def call_sites(rom, target):
    """File offsets of ``CALL/JP target`` encodings, conditional forms included (byte scan, alignment-independent)."""
    out = []
    for op, kind in CALL_JUMP_OPCODES.items():
        needle = bytes([op, target & 0xFF, target >> 8])
        i = rom.find(needle)
        while i != -1:
            out.append((i, kind))
            i = rom.find(needle, i + 1)
    return sorted(out)


def bit_effects(rom, code, setters):
    """Which bits each setter of a flag byte sets or clears; the value stored by an absolute store is the A feeder."""
    rows = []
    for rec in setters["hl_bit_ops"]:
        m = re.match(r"(SET|RES) (\d),\(HL\)", rec["op"])
        if m:
            rows.append(OrderedDict([("file_offset", rec["file_offset"]), ("op", rec["op"]),
                                     ("sets" if m.group(1) == "SET" else "clears", [int(m.group(2))])]))
        else:
            m = re.match(r"LD \(HL\),(0x[0-9a-f]+|\d+)$", rec["op"])
            rows.append(OrderedDict([("file_offset", rec["file_offset"]), ("op", rec["op"]),
                                     ("assigns", _num(m.group(1)) if m else None)]))
    for rec in setters["absolute_stores"]:
        kind, value, ev = feeder_of_a(rom, code, rec["file_offset"])
        rows.append(OrderedDict([("file_offset", rec["file_offset"]), ("op", "LD (nn),A"), ("feeder", ev[-1] if ev else None),
                                 ("assigns", value if kind == "const" else None)]))
    return sorted(rows, key=lambda r: r["file_offset"])


def setters_of_bit(rows, bit):
    sets = []
    for r in rows:
        if "sets" in r and bit in r["sets"]:
            sets.append(r["file_offset"])
        elif "assigns" in r:
            if r["assigns"] is None:
                sets.append(r["file_offset"])          # value unknown: may set the bit
            elif r["assigns"] >> bit & 1:
                sets.append(r["file_offset"])
    return sorted(sets)


def straight_line_forward(rom, off, limit=20):
    out, p = [], off
    for _ in range(limit):
        d = F.decode(rom, p)
        if F.is_invalid(d):
            break
        out.append((p, z80.disasm(d), d))
        if F.is_terminal(d) or d.op in (OP_JP, OP_CALL) or F._addr_operand(d) is not None:
            break
        p += d.len
    return out


def adjacent_pairs(rom, census, limit=18):
    """Pairs of zone/act stores on one straight line (calls included, other branches end the line): their order, the
    instructions between them, and whether an ``EI`` or ``CALL`` between them could let an interrupt or another routine
    observe the half-updated pair."""
    zone_sites = {s["file_offset"] for s in census["zone"] if s["form"] == "LD (nn),A"}
    act_sites = {s["file_offset"] for s in census["act"] if s["form"] == "LD (nn),A"}
    pairs = []
    for first in sorted(zone_sites | act_sites):
        kind = "zone" if first in zone_sites else "act"
        other = act_sites if kind == "zone" else zone_sites
        p, between = first + 3, []
        for _ in range(limit):
            d = F.decode(rom, p)
            if F.is_invalid(d):
                break
            t = z80.disasm(d)
            if p in other:
                pairs.append(OrderedDict([("first", kind), ("first_offset", first), ("second_offset", p),
                                          ("between", between), ("call_or_ei_between",
                                                                 any(x.startswith(("CALL", "EI")) for x in between))]))
                break
            if F.is_terminal(d) or d.op in (OP_JP,) or (F._addr_operand(d) is not None and d.op != OP_CALL):
                break
            between.append(t)
            p += d.len
    return pairs


def flow_facts(rom, code):
    """Mechanical facts about the game-state machine that the zone/act argument rests on."""
    fx = OrderedDict()
    fx["state_dispatch_d293"] = OrderedDict((str(b), [c, hx(t)]) for b, (c, t) in rlca_chain(rom, 0x1340).items())
    fx["special_dispatch_d294"] = OrderedDict((str(b), [c, hx(t)]) for b, (c, t) in rlca_chain(rom, 0x133A).items())
    fx["special_sub_dispatch_d294"] = OrderedDict((str(b), [c, hx(t)]) for b, (c, t) in rlca_chain(rom, 0x1762, rot0=1).items())
    fx["special_sub_dispatch_d293"] = OrderedDict((str(b), [c, hx(t)]) for b, (c, t) in rlca_chain(rom, 0x1772).items())
    d293 = bit_effects(rom, code, flag_setters(rom, code, STATE_FLAGS))
    d294 = bit_effects(rom, code, flag_setters(rom, code, SPECIAL_FLAGS))
    fx["d293_setters"] = d293
    fx["d294_setters"] = d294
    fx["d293_bit5_setters"] = [hx(x) for x in setters_of_bit(d293, 5)]
    fx["d293_bit4_setters"] = [hx(x) for x in setters_of_bit(d293, 4)]
    fx["d294_bit3_setters"] = [hx(x) for x in setters_of_bit(d294, 3)]
    fx["callers_special_stage_entry_178F"] = [OrderedDict([("file_offset", o), ("kind", k), ("in_discovered_code", o in code)])
                                              for o, k in call_sites(rom, 0x178F)]
    fx["callers_special_stage_save_187B"] = [OrderedDict([("file_offset", o), ("kind", k), ("in_discovered_code", o in code)])
                                             for o, k in call_sites(rom, 0x187B)]
    fx["callers_music_189B"] = [OrderedDict([("file_offset", o), ("kind", k), ("in_discovered_code", o in code)])
                                for o, k in call_sites(rom, 0x189B)]
    fx["callers_loader_2A4F"] = [OrderedDict([("file_offset", o), ("kind", k), ("in_discovered_code", o in code)])
                                 for o, k in call_sites(rom, 0x2A4F)]
    ring_paths = OrderedDict()
    for name, a, b in (("single_ring_3138_to_call", 0x3138, 0x3147), ("ten_ring_4AC0_to_jump", 0x4AC0, 0x4AD7)):
        ring_paths[name] = OrderedDict([("range", [hx(a), hx(b)]),
                                        ("reads_act", ACT in operand_addresses(rom, a, b)),
                                        ("reads_zone", ZONE in operand_addresses(rom, a, b))])
    fx["ring_paths_to_special_stage"] = ring_paths
    fx["act_increment_chain_14AE_to_1538"] = OrderedDict([
        ("branches_between", [t for _, t, d in _linear(rom, 0x14AE, 0x1538) if t.startswith(("JP", "JR", "RET"))]),
        ("calls", sorted({t for _, t, d in _linear(rom, 0x14AE, 0x1538) if t.startswith("CALL")}))])
    return fx


def _linear(rom, a, b):
    out, p = [], a
    while p < b:
        d = F.decode(rom, p)
        if F.is_invalid(d):
            break
        out.append((p, z80.disasm(d), d))
        p += d.len
    return out


# --- 9. the transition model ----------------------------------------------------------------------------------------
PLAY, SS, TITLE, END = "play", "ss", "title", "end"


class World:
    """Everything the model needs, derived from the ROM by the executed lemmas above."""

    EVENT_CLASS = {"level_select": "hidden_menu", "rotation_demo": "attract_demo", "zero_restart": "normal",
                   "act_complete": "normal", "zone_complete": "normal", "special_stage_enter": "normal",
                   "special_stage_return": "normal", "title_reset": "normal", "zone_complete_in_special_stage": "normal"}

    def __init__(self, rom):
        self.rom = rom
        self.pairs = select_table_pairs(rom)
        self.rotation = rotation_rows(rom)
        self.ss_zones = special_stage_zone(rom)
        self.guard = special_stage_entry_guard(rom)
        self.level_end = level_end_flag(rom)
        self.zone_complete = zone_complete_effect(rom)
        self.ss_exit = special_stage_exit_effect(rom)
        self.act_complete = act_complete_effect(rom)
        self.ptr, self.records, self.safe = loader_tables(rom)

    def record_valid(self, zone, act):
        if zone > 15:
            return False
        rec, types, err = self.ptr[(zone, act & 0xFF)]
        return err is None and rec in self.records

    def act_inc(self, act):
        return (act + 1) & 0xFF

    def initial_states(self):
        return [((0, 0, PLAY, 0), True), ((7, 0, TITLE, 0), True)]

    def step(self, state):
        z, a, mode, saved = state
        out = []
        if mode == TITLE:
            for (pz, pa) in sorted(set(self.pairs.values())):
                out.append(("level_select", (pz, pa, PLAY, 0), self.record_valid(pz, pa), [(pz, a)]))
            for (rz, ra, _c) in self.rotation:
                out.append(("rotation_demo", (rz, ra, PLAY, 0), self.record_valid(rz, ra), [(rz, a)]))
            out.append(("zero_restart", (0, 0, PLAY, 0), True, [(0, a)]))
            return out
        if mode == END:
            out.append(("title_reset", (7, 0, TITLE, 0), True, [(7, a)]))
            return out
        if mode == PLAY:
            out.append(("zero_restart", (0, 0, PLAY, 0), True, [(0, a)]))
            flag = self.level_end[a]
            if flag & 0x20:                                                      # bit 5: act complete (INC act)
                na = self.act_complete[a][0]
                out.append(("act_complete", (z, na, PLAY, 0), self.record_valid(z, na), []))
            if flag & 0x10:                                                      # bit 4: zone complete
                nz, na, pc = self.zone_complete[z]
                to_end = pc == 0x15E8
                out.append(("zone_complete", (nz, na, END if to_end else PLAY, 0),
                            (not to_end) and self.record_valid(nz, na), [(z, 0)]))
            if self.guard["armed_only_when_character_1_zone_lt_6_emeralds_not_full"] and z < 6:
                for zss in sorted(self.ss_zones):
                    ok = zss == min(self.ss_zones) and self.record_valid(zss, a)
                    out.append(("special_stage_enter", (zss, a, SS, z), ok, []))
            return out
        if mode == SS:
            if True:                                   # a zone-complete flag can be raised in a special stage (unresolved trigger)
                nz, na0, pc = self.zone_complete[z]
                out.append(("zone_complete_in_special_stage", (nz, na0, END, 0), False, [(z, 0)]))
            restored, act_untouched, special, flags = self.ss_exit[saved]
            na = self.act_complete[a][0] if flags & 0x20 and act_untouched else a  # bit 5 raised -> the act-complete path
            ok = self.record_valid(z, a) and self.record_valid(restored, na)
            out.append(("special_stage_return", (restored, na, PLAY, 0), ok, [(restored, a)]))
            return out
        return out


def explore_world(world, cap=ACT_CAP):
    """Three explorations: every edge; grounded edges; grounded edges of normal play only (no hidden menu, no attract demo)."""
    cls = world.EVENT_CLASS
    out = OrderedDict()
    out["any"] = explore(world.initial_states(), world.step, cap, classes=cls)
    out["grounded"] = explore(world.initial_states(), world.step, cap, grounded_only=True, classes=cls)
    out["normal"] = explore(world.initial_states(), world.step, cap, grounded_only=True,
                            skip_classes=("hidden_menu", "attract_demo"), classes=cls)
    return out


def summarize_states(table):
    by_mode = OrderedDict()
    for (z, a, mode, saved) in table:
        rec = by_mode.setdefault(mode, {"zones": set(), "acts": set()})
        rec["zones"].add(z)
        rec["acts"].add(a)
    return OrderedDict((m, OrderedDict([("zones", sorted(r["zones"])), ("acts", [min(r["acts"]), max(r["acts"])])]))
                       for m, r in sorted(by_mode.items()))


def writer_assessment(rom, code, targets=None):
    """Is the writer set of ``targets`` (name -> address) closed? Every absolute store (any encoding, mirror included) must
    be classified, no pointer materialisation or block move may be unresolved. Returns the pieces and ``closed``."""
    targets = targets or TARGETS
    census = store_census(rom, targets)
    classes = OrderedDict((n, [(s, classify_store(rom, code, s, targets[n])) for s in sites]) for n, sites in census.items())
    unclassified = [(n, s["file_offset"]) for n, rows in classes.items() for s, c in rows
                    if c["kind"] in ("unclassified", "undiscovered") or c.get("in_discovered_code") is False]
    lo, hi = min(targets.values()) - 8, max(targets.values())
    pm = pointer_materialisations(rom, code, lo, hi)
    bm = block_move_sites(rom, code)
    unresolved_pm = [p["file_offset"] for p in pm if p["status"] == "unresolved" or p.get("touches_targets")]
    unresolved_bm = [b["file_offset"] for b in bm
                     if b["status"] == "unresolved" or (b.get("touches_targets") and not b.get("fill_zero"))]
    return OrderedDict([("census", census), ("classes", classes), ("unclassified", unclassified), ("pointers", pm),
                        ("block_moves", bm), ("unresolved_pointers", unresolved_pm), ("unresolved_block_moves", unresolved_bm),
                        ("closed", not unclassified and not unresolved_pm and not unresolved_bm)])


def find_violations(tabs, bad, grounded_key="grounded"):
    """States of the any-path table for which ``bad(state)`` holds, split into those also reached by grounded edges and
    the shortest path to the first grounded one (a counterexample)."""
    any_t, grd_t = tabs["any"][0], tabs[grounded_key][0]
    every = [s for s in any_t if bad(s)]
    grounded = [s for s in every if s in grd_t]
    witness = None
    if grounded:
        first = min(grounded, key=lambda s: (s[1], s[0], s[2], s[3]))
        witness = path_to(grd_t, first)
    return every, grounded, witness


def survivors(states, types_of, zone_ok):
    """States whose loaded slot types include a type-5 slot although the zone cannot index the nested dispatcher's table
    (a type-5 slot that survives, or is created in, a zone outside the table)."""
    return [s for s in states if s[0] not in zone_ok and 5 in (types_of(s) or ())]


# --- 10. propositions -----------------------------------------------------------------------------------------------
FORBIDDEN_REQUESTS = (0xC5, 0xD3)         # the request-byte range R1 could not discharge for the zone-music route


def derive_status(counterexample, closed, proven_parts):
    """PROVEN needs a closed argument (every writer classified, every domain bounded, no unresolved predecessor or open
    dependency); DISPROVEN needs a counterexample whose every step is grounded; otherwise PARTIAL when some sub-claim is
    proven and UNPROVEN when none is. A counterexample outranks everything: it is a fact about the ROM."""
    if counterexample:
        return "DISPROVEN"
    if closed:
        return "PROVEN"
    return "PARTIAL" if proven_parts else "UNPROVEN"


def valid_ranges(consumer, zones, acts=range(256)):
    out = OrderedDict()
    for z in zones:
        ok = [a for a in acts if consumer.valid(z, a)]
        runs, start, prev = [], None, None
        for a in ok:
            if start is None:
                start = prev = a
            elif a == prev + 1:
                prev = a
            else:
                runs.append([start, prev])
                start = prev = a
        if start is not None:
            runs.append([start, prev])
        out[z] = runs
    return out


def best_path(tabs, state):
    """Shortest event chain to ``state``: prefer normal play, then grounded edges, then any edge."""
    for key in ("normal", "grounded", "any"):
        if state in tabs[key][0]:
            return key, path_to(tabs[key][0], state)
    return None, []


def evaluate_music(rom, tabs):
    cons = music_consumer(rom)
    any_t, grd_t = tabs["any"][0], tabs["grounded"][0]
    inter_any, inter_g = tabs["any"][2], tabs["grounded"][2]
    rows, grounded_rows = [], []
    for st in any_t:
        z, a = st[0], st[1]
        idx = cons.index(z, a)
        if not 0 <= idx < cons.extent:
            addr = cons.address(z, a)
            rec = OrderedDict([("state", list(st)), ("index", idx), ("table_address", hx(addr)),
                               ("byte", rom[addr] if addr < 0x4000 else None),
                               ("in_forbidden_range", FORBIDDEN_REQUESTS[0] <= rom[addr] <= FORBIDDEN_REQUESTS[1]
                                if addr < 0x4000 else None),
                               ("grounded", st in grd_t), ("kind", "state")])
            rows.append(rec)
            if st in grd_t:
                grounded_rows.append(rec)
    inter_rows = []
    for (z, a), ev in inter_any.items():
        idx = cons.index(z, a)
        if not 0 <= idx < cons.extent:
            inter_rows.append(OrderedDict([("pair", [z, a]), ("index", idx), ("event", ev), ("kind", "intermediate"),
                                           ("grounded", (z, a) in inter_g)]))
    rows.sort(key=lambda r: (r["state"][1], r["state"][0], r["state"][2]))
    witness = None
    if rows:
        first = rows[0]
        key, path = best_path(tabs, tuple(first["state"]))
        witness = OrderedDict([("state", first["state"]), ("index", first["index"]), ("path_class", key), ("path", path)])
    forbidden = [r for r in rows if r["in_forbidden_range"]]
    gi = [r for r in inter_rows if r["grounded"]]
    wrap = [(z, a) for z in range(256) for a in range(256) if (3 * z + a) > 255 and cons.index(z, a) != 3 * z + a]
    ev = OrderedDict([
        ("consumer", OrderedDict([("entry", "$18A0"), ("physical_offset", 0x18A0), ("bank", 0), ("slot", 0),
                                  ("read", "$18B2"), ("table_base", hx(cons.base)), ("table_entries", cons.extent),
                                  ("table_end_rule", "the first CALL/JP target above the base ($18E1) is code")])),
        ("index_expression", "L = (3*zone + act) mod 256, H = 0, address = $18BA + L; executed from $18A0 for every pair"),
        ("eight_bit_wrap", OrderedDict([("wrapping_pairs_counted", len(wrap)),
                                        ("example", [wrap[0][0], wrap[0][1], cons.index(*wrap[0])] if wrap else None)])),
        ("valid_act_ranges_by_zone", OrderedDict((str(z), r) for z, r in valid_ranges(cons, range(0, 14)).items())),
        ("max_zone_valid_for_acts_0_to_2", max(z for z in range(0, 41) if all(cons.valid(z, a) for a in range(3)))),
        ("states_checked", len(any_t)),
        ("state_violations_any_path", len(rows)),
        ("state_violations_grounded", len(grounded_rows)),
        ("intermediate_pairs_checked", len(inter_any)),
        ("intermediate_violations_any_path", len(inter_rows)),
        ("intermediate_violations_grounded", len(gi)),
        ("smallest_violation_any_path", witness),
        ("violations_in_forbidden_request_range", len(forbidden)),
        ("first_forbidden_witness", forbidden[0] if forbidden else None),
        ("smallest_forbidden_act_by_special_stage_zone", OrderedDict(
            (str(z), min((r["state"][1] for r in forbidden if r["state"][0] == z), default=None)) for z in range(8, 13))),
    ])
    return ev, rows, grounded_rows, inter_rows, gi


def evaluate_loader(rom, world, tabs):
    any_t, grd_t, nrm_t = tabs["any"][0], tabs["grounded"][0], tabs["normal"][0]
    bad_any, bad_g, bad_n = [], [], []
    for st in any_t:
        if st[1] > 2 or st[0] > 15:
            rec = OrderedDict([("state", list(st))])
            bad_any.append(rec)
            if st in grd_t:
                bad_g.append(rec)
            if st in nrm_t:
                bad_n.append(rec)
    key = lambda r: (r["state"][1], r["state"][0], r["state"][2])
    witness = None
    pool = bad_n or bad_g
    if pool:
        first = min(pool, key=key)
        k, path = best_path(tabs, tuple(first["state"]))
        witness = OrderedDict([("state", first["state"]), ("path_class", k), ("path", path)])
    acts_any = sorted({s[1] for s in any_t})
    ev = OrderedDict([
        ("proposed_bounds", OrderedDict([("zone_max", 15), ("act_max", 2)])),
        ("consumer", OrderedDict([("entry", "$2A4F"), ("physical_offset", LOADER), ("bank", 0), ("slot", 0),
                                  ("zone_table", hx(ZONE_TABLE)), ("index_expression",
                                   "record = word[word[$2A9A + 2*zone (8-bit)] + 2*act (8-bit)]; record fields +6..+9 are the "
                                   "four initial slot types ($D452/$D45A/$D462/$D46A)")])),
        ("records_selected_by_proposed_domain", [hx(r) for r in world.records]),
        ("slot_types_by_record", OrderedDict((hx(r), list(next(world.ptr[(z, a)][1] for z in range(16) for a in range(3)
                                                                if world.ptr[(z, a)][0] == r))) for r in world.records)),
        ("sufficiency", "zone <= 15 and act <= 2 select only these nine records (all 48 combinations executed)"),
        ("safe_act_bound_by_zone", OrderedDict((str(z), world.safe[z]) for z in range(16))),
        ("safe_act_bound_rule", "largest A such that acts 0..A all select one of the nine records; beyond it the word read is "
                                "record data used as a pointer (an unverified-bank read, never interpreted here)"),
        ("reachable_zone_values_any_path", sorted({s[0] for s in any_t})),
        ("reachable_act_range_any_path", [min(acts_any), max(acts_any)]),
        ("states_beyond_proposed_bounds_any_path", len(bad_any)),
        ("states_beyond_proposed_bounds_grounded", len(bad_g)),
        ("states_beyond_proposed_bounds_normal_play", len(bad_n)),
        ("grounded_counterexample", witness),
    ])
    return ev, bad_any, bad_g, bad_n


def evaluate_nested(rom, world, tabs):
    any_t, grd_t = tabs["any"][0], tabs["grounded"][0]
    entries, end = nested_table(rom)
    zone_ok = sorted({z for z in range(256) if all(nested_word_address(rom, z, b) + 1 < end for b in (0, 1))})
    type5_records = sorted({world.ptr[(z, a)][0] for z in range(16) for a in range(3) if 5 in world.ptr[(z, a)][1]})
    type5_zones = sorted({z for z in range(16) if any(5 in world.ptr[(z, a)][1] for a in range(3))})
    cand_any, cand_g, unresolved = [], [], []
    for st in any_t:
        z, a = st[0], st[1]
        if z in zone_ok:
            continue
        rec, types, err = world.ptr[(z, a)] if z <= 15 else (None, None, "zone beyond the loader table")
        if err is not None:
            unresolved.append(OrderedDict([("state", list(st)), ("why", err), ("grounded", st in grd_t)]))
        elif 5 in types:
            r = OrderedDict([("state", list(st)), ("record", hx(rec)), ("types", list(types)), ("grounded", st in grd_t)])
            cand_any.append(r)
            if st in grd_t:
                cand_g.append(r)
    ev = OrderedDict([
        ("consumer", OrderedDict([("entry", "$741F1"), ("physical_offset", 0x741F1), ("bank", NESTED_BANK), ("cpu", "$81F1"),
                                  ("index_read_at", "$741E0"), ("table_base", hx(NESTED_TABLE)),
                                  ("table_entries", len(entries)), ("table_end", hx(end)),
                                  ("table_end_rule", "words below the lowest destination (R1 region rule)")])),
        ("index_expression", "word at $81F2 + 2*(((2*zone) mod 256 + B) mod 128), B in {0,1}; zone is the only RAM read"),
        ("zones_inside_table_exhaustive", zone_ok),
        ("records_with_a_type_5_slot", [hx(r) for r in type5_records]),
        ("zones_whose_own_acts_select_a_type_5_record", type5_zones),
        ("states_outside_table_zone_with_type_5_any_path", len(cand_any)),
        ("states_outside_table_zone_with_type_5_grounded", len(cand_g)),
        ("states_outside_table_zone_with_unresolved_record", len(unresolved)),
        ("unresolved_state_examples", unresolved[:6]),
    ])
    return ev, cand_any, cand_g, unresolved, zone_ok


# --- 11. closures and consumers -------------------------------------------------------------------------------------
def irq_closure(rom, root=ROOT):
    """The conditional IM 1 closure DECOMP-1D-R1 built (partial dispatches followed): the code an interrupt can run."""
    import decomp1d_r1_closure as R
    import rom_ledger as RL
    regions = json.loads((root / "asm" / "recovered" / "regions.json").read_text(encoding="utf-8"))
    facts = D.Facts.of(rom)
    baseline = RL.build_ledger(rom, root, reviewed=False)
    ctx = D.Context(baseline["claims"])
    doms = R.data_domains(rom)
    for dom in doms.values():
        if dom.get("non_code_files"):
            ctx = R.with_data(ctx, dom["non_code_files"], dom.get("non_code_label", "DATA"))
    walk, _disp, _proofs, _uni = R.resolve(rom, regions, facts, ctx, SHADOW, True, doms)
    return walk


def reads_of(rom, addr):
    """File offsets of ``LD A,(addr)`` / ``LD rr,(addr)`` style absolute loads of ``addr`` (byte scan)."""
    out = []
    for prefix in (b"\x3a", b"\x2a", b"\xed\x4b", b"\xed\x5b", b"\xed\x7b", b"\xdd\x2a", b"\xfd\x2a"):
        needle = prefix + bytes([addr & 0xFF, addr >> 8])
        i = rom.find(needle)
        while i != -1:
            out.append(i)
            i = rom.find(needle, i + 1)
    return sorted(out)


ASSIGNED_READS = {0x018A0: "A: zone-music index ($18A0)", 0x018A7: "A: zone-music index ($18A7)",
                  0x02A53: "B: loader zone ($2A53)", 0x02A61: "B: loader act ($2A61)",
                  0x741E0: "C: nested dispatcher zone ($741E0)"}


def interrupt_view(rom, walk, census):
    visited = set(walk["visited"])
    writer_sites = {s["file_offset"] for k in census for s in census[k]}
    readers = OrderedDict()
    for name, addr in (("zone", ZONE), ("act", ACT)):
        readers[name] = [hx(o) for o in reads_of(rom, addr) if o in visited]
    d2c9 = [o for o, _ in D.store_pattern_sites(rom, SELECT_INDEX)]
    return OrderedDict([
        ("closure_instructions", len(visited)),
        ("closure_open_edges", [[e[0]] + list(e[1:]) for e in walk["open_edges"]]),
        ("writer_sites_inside_closure", sorted(hx(o) for o in writer_sites if o in visited)),
        ("select_index_writers_inside_closure", sorted(hx(o) for o in d2c9 if o in visited)),
        ("readers_inside_closure", readers),
        ("music_callers_inside_closure", [hx(o) for o, _k in call_sites(rom, 0x189B) if o in visited]),
        ("loader_callers_inside_closure", [hx(o) for o, _k in call_sites(rom, LOADER) if o in visited]),
        ("consumer_entries_inside_closure", OrderedDict((n, (o in visited)) for n, o in
                                                        (("music_189B", 0x189B), ("loader_2A4F", 0x2A4F),
                                                         ("nested_741E0", 0x741E0)))),
    ])


def select_loop_view(rom):
    walk = D.state_walk(rom, [(0x085A, 1, "U")], SHADOW)
    writers = [o for o, _ in D.store_pattern_sites(rom, SELECT_INDEX)]
    return OrderedDict([("closure_instructions", len(walk["visited"])), ("open_edges", len(walk["open_edges"])),
                        ("select_index_writers", sorted(hx(o) for o in writers)),
                        ("writers_reachable_from_select_loop", sorted(hx(o) for o in writers if o in walk["visited"]))])


def other_zone_consumers(rom):
    """Every absolute read of the zone and act bytes, with the three assigned consumers marked. The unassigned readers are
    not analysed in this task (they are listed so none is silently out of the census)."""
    rows = []
    for name, addr in (("zone", ZONE), ("act", ACT)):
        for o in reads_of(rom, addr):
            rows.append(OrderedDict([("byte", name), ("file_offset", o), ("assigned", ASSIGNED_READS.get(o))]))
    return rows


def slot_lifetime_facts(rom):
    """Where the four initial slot-type bytes are cleared and the object RAM is wiped, relative to each zone change.
    Mechanical: the straight-line calls between a transition's entry and the zone/act store that changes the level."""
    def calls(a, b):
        return sorted({t for _, t, _d in _linear(rom, a, b) if t.startswith("CALL")})
    rows = OrderedDict()
    rows["zone_complete_$1543_to_$15D6"] = calls(0x1543, 0x15D6)
    rows["act_complete_$14AE_to_$1538"] = calls(0x14AE, 0x1538)
    rows["special_stage_start_$17B0_to_$17E5"] = calls(0x17B0, 0x17E8)
    clears = [o for o, _ in call_sites(rom, 0x1CEB)]
    return OrderedDict([("clear_slot_types_call_sites_$1CEB", [hx(o) for o in clears]),
                        ("slot_type_clear_routine", "$1CEB zeroes $D452/$D45A/$D462/$D46A and $D39B, nothing else"),
                        ("object_ram_wipe", "$297E zeroes $D300-$DBBF (LDIR $D301.., 2239 bytes)"),
                        ("calls_on_transition_paths", rows)])


def r1_relationship(root=ROOT):
    path = root / "data" / "decomp1d" / "r1-interrupt-closure.json"
    r1 = json.loads(path.read_text(encoding="utf-8"))
    verdict = r1["verdict"]
    by_site = {d["site"]: d for d in r1["open_conditions"]}
    return verdict, by_site, r1["open_conditions"]


# --- 12. build ------------------------------------------------------------------------------------------------------
PREMISES = [
    "P1 Standard Sega mapper semantics (R4 of DECOMP-1D). Slot 0 is bank 0: the only stores to the slot-0 mapper register "
    "$FFFD are in the boot sequence (listed in the census). Slot 2 is bank $1D for the nested dispatcher (R1's assumption "
    "for the routine at $8000); a record pointer into slot 1 or 2 is never interpreted (its bank is unverified).",
    "P2 Player and level inputs (collisions, ring pickups, pressed buttons) are adversarial: every transition the ROM "
    "permits is treated as possible. A path is *grounded* when every step is permitted by the code alone and none rests on "
    "a dependency this task did not discharge.",
    "P3 Register-addressed writers whose pointer is computed (not an immediate) and block moves with an unresolved "
    "destination are listed, never assumed benign; this is DECOMP-1D assumption R2 and it stays open.",
    "P4 The discovered-code universe is the DECOMP-1D walk; byte-pattern hits outside it (object-callback code in banked "
    "ROM) are reported separately and are classified by the same value-source analysis where the encoding is unambiguous.",
]

UNRESOLVED = [
    ("U1", "zone-complete trigger inside a special stage",
     "D293 bit 4 is raised by $303ED (guarded only by act >= 2) and by the $50 stores at $7BB2A/$7BB6E, all in object-callback "
     "code outside the discovered universe. The special-stage dispatcher ($176F) honours bit 4, so a zone-complete while the "
     "zone is 8..12 would run the zone increment on a special-stage zone. Not excluded; modelled as an ungrounded edge."),
    ("U2", "emerald masks are object-supplied",
     "$D2CC is written at $794A7 (OR with the object byte IX+$3F) and $7BB69 (OR $20). The masks are not derived here, so a "
     "special-stage zone above 8 (which needs emerald bits 0..3 set) is not grounded."),
    ("U3", "special stages loaded from a garbage record pointer",
     "For a special-stage zone (8..12) the loader's act-table walk leaves the nine records at act 9 (zones 8, 9, 11) or act "
     "6 (zones 10, 12); the record pointer is then record data, read through an unverified bank. Whether such a stage can be "
     "left is not known."),
    ("U4", "allocator / kernel-vector route to a type-5 slot",
     "Inherited from DECOMP-1D-R1 (ALLOCATOR lemma): only the direct callers of $1CD3 are enumerated; the kernel vector $0374 "
     "can be entered through callback stubs with an unknown C."),
    ("U5", "register-addressed block moves",
     "Block moves whose destination is not an immediate (listed in the census) could, in principle, cover the zone/act bytes."),
    ("U6", "D2C8 and reaching 100 rings are player-supplied",
     "Treated as adversarial inputs (premise P2); the code permits both."),
]


def build(rom, root=ROOT, irq_walk=None):
    import rom_ledger as RL
    code = Code(rom)
    wa = writer_assessment(rom, code)
    census, classes, unclassified = wa["census"], wa["classes"], wa["unclassified"]
    mirror_hits = [s["file_offset"] for rows in census.values() for s in rows if s["mirror_alias"]]
    wide_hits = [s["file_offset"] for rows in census.values() for s in rows if s["form"] != "LD (nn),A"]
    pm = pointer_materialisations(rom, code)
    bm = wa["block_moves"]
    boot = boot_clear(rom, code)
    world = World(rom)
    tabs = explore_world(world)
    allr, grd, nrm = tabs["any"][0], tabs["grounded"][0], tabs["normal"][0]
    fx = flow_facts(rom, code)
    pairs = adjacent_pairs(rom, census)
    walk = irq_walk if irq_walk is not None else irq_closure(rom, root)
    irq = interrupt_view(rom, walk, census)
    sel = select_loop_view(rom)
    a_eval, a_all, a_g, a_ia, a_ig = evaluate_music(rom, tabs)
    b_eval, b_all, b_g, b_n = evaluate_loader(rom, world, tabs)
    c_eval, c_all, c_g, c_unres, zone_ok = evaluate_nested(rom, world, tabs)
    slot0_stores = slot0_mapper_stores(rom, code)
    select_domain = select_index_domain(rom)
    ss_zone = special_stage_zone(rom)
    r1_verdict, r1_by_site, r1_open = r1_relationship(root)

    writers = OrderedDict()
    for name, rows in classes.items():
        out = []
        for s, c in rows:
            off = s["file_offset"]
            rec = OrderedDict([("file_offset", off), ("bank", off // BANK if off >= 0x4000 else 0), ("cpu", F.cpu_address(off)),
                               ("form", s["form"]), ("mirror_alias", s["mirror_alias"]), ("asm", decode_at(rom, off)[1])])
            rec.update(c)
            out.append(rec)
        writers[name] = out
    value_domains = OrderedDict([
        ("zone", OrderedDict([
            ("title_literal", 7),
            ("zero_literal_writers", [hx(s["file_offset"]) for s, c in classes["zone"] if c["kind"] == "const" and c["value"] == 0]),
            ("level_select_pairs", [[z, a] for z, a in sorted(set(world.pairs.values()))]),
            ("level_select_index_domain", [min(select_domain), max(select_domain)]),
            ("rotation_rows_zone_act_character", [list(r) for r in world.rotation]),
            ("special_stage_zone_emerald_byte_counts", OrderedDict((str(z), len(m)) for z, m in sorted(ss_zone.items()))),
            ("saved_zone_restore", "copy of $D296, itself a copy of the zone taken at the special-stage save ($187B), reached "
                                   "only after the $178F guard (zone < 6)"),
            ("zone_increment", "zone + 1 after the act reset; the branch on zone >= 6 selects the end path ($15E8)"),
        ])),
        ("act", OrderedDict([
            ("zero_literal_writers", [hx(s["file_offset"]) for s, c in classes["act"] if c["kind"] == "const"]),
            ("level_select_acts", sorted({a for _, a in world.pairs.values()})),
            ("increment_sites", [hx(s["file_offset"]) for s, c in classes["act"] if c["kind"] == "increment"]),
            ("increment_guard", "none: no branch between $14AE and $1538 (flow facts)"),
        ])),
    ])

    increments_unguarded = not fx["act_increment_chain_14AE_to_1538"]["branches_between"]
    ss_entry_unguarded_by_act = (not fx["ring_paths_to_special_stage"]["single_ring_3138_to_call"]["reads_act"]
                                 and not fx["ring_paths_to_special_stage"]["ten_ring_4AC0_to_jump"]["reads_act"]
                                 and not world.guard["reads_act"])
    writers_classified = not unclassified
    unresolved_block = wa["unresolved_block_moves"]
    unresolved_pm = wa["unresolved_pointers"]
    open_deps = bool(UNRESOLVED)
    statuses = OrderedDict()
    statuses["A"] = derive_status(counterexample=bool(a_g or a_ig),
                                  closed=(writers_classified and not a_all and not a_ia and not unresolved_block
                                          and not unresolved_pm and not open_deps), proven_parts=True)
    statuses["B"] = derive_status(counterexample=bool(b_n or b_g),
                                  closed=(writers_classified and not b_all and not unresolved_block and not unresolved_pm
                                          and not open_deps), proven_parts=True)
    statuses["C"] = derive_status(counterexample=bool(c_g),
                                  closed=(writers_classified and not c_all and not c_unres and not unresolved_block
                                          and not unresolved_pm and not open_deps), proven_parts=True)

    doc = OrderedDict()
    doc["format"] = 1
    doc["task"] = "DECOMP-1D-R2"
    doc["rom_sha256"] = RL.ROM_SHA256
    doc["generator"] = "tools/decomp1d_r2_zone_act.py"
    doc["base_commit"] = BASE_COMMIT
    doc["evidence_tier"] = ("static ROM-derived evidence; index arithmetic, writer value computations and guards are executed "
                            "by a fail-closed concrete interpreter; not an execution trace and not an emulator run")
    doc["premises"] = PREMISES
    doc["census"] = OrderedDict([
        ("absolute_store_sites", OrderedDict((k, len(v)) for k, v in census.items())),
        ("wide_or_index_register_store_hits", wide_hits),
        ("mirror_alias_store_hits", mirror_hits),
        ("slot0_mapper_register_stores", OrderedDict([
            ("in_discovered_code", [OrderedDict([("file_offset", hx(r["file_offset"])), ("value", r["value"])])
                                    for r in slot0_stores["in_discovered_code"]]),
            ("outside_discovered_code", [hx(o) for o in slot0_stores["outside_discovered_code"]]),
            ("slot0_is_bank_0_in_code", slot0_stores["slot0_is_bank_0_in_code"])])),
        ("pointer_materialisations", OrderedDict([
            ("scanned_value_range", ["$D290", "$D298"]), ("hits", len(pm)),
            ("resolved", sum(1 for p in pm if p["status"] == "resolved")),
            ("undiscovered_code", sorted(hx(p["file_offset"]) for p in pm if p["status"] == "undiscovered")),
            ("unresolved", sorted(hx(p["file_offset"]) for p in pm if p["status"] == "unresolved")),
            ("resolved_hits_that_write_a_target", sorted(hx(p["file_offset"]) for p in pm if p.get("touches_targets")))])),
        ("block_moves", OrderedDict([
            ("sites", len(bm)), ("resolved", sum(1 for b in bm if b["status"] == "resolved")),
            ("resolved_that_touch_a_target", [hx(b["file_offset"]) for b in bm if b.get("touches_targets")]),
            ("unresolved_in_discovered_code", sorted(hx(b["file_offset"]) for b in bm if b["status"] == "unresolved")),
            ("undiscovered_code", sum(1 for b in bm if b["status"] == "undiscovered"))])),
        ("boot_and_restart_ram_clear", boot),
        ("unclassified_or_undiscovered_store_sites", [[n, hx(o)] for n, o in unclassified]),
        ("all_readers", other_zone_consumers(rom)),
    ])
    doc["writers"] = writers
    doc["value_domains"] = value_domains
    doc["flow_facts"] = fx
    doc["slot_lifetime"] = slot_lifetime_facts(rom)
    doc["intermediate_states"] = OrderedDict([
        ("adjacent_zone_act_store_pairs", [OrderedDict([("first", p["first"]), ("first_offset", hx(p["first_offset"])),
                                                        ("second_offset", hx(p["second_offset"])), ("between", p["between"]),
                                                        ("call_or_ei_between", p["call_or_ei_between"])]) for p in pairs]),
        ("interrupt_view", irq),
        ("select_loop_view", sel),
        ("rule", "an interrupt can run the music routine and the nested dispatcher (inside the IM 1 closure), so the transient "
                 "pairs between two adjacent stores are consumer inputs for A and C; the loader runs on the main thread only"),
    ])
    doc["transition_model"] = OrderedDict([
        ("act_cap", ACT_CAP),
        ("event_classes", OrderedDict(sorted(World.EVENT_CLASS.items()))),
        ("level_end_flag_by_act", OrderedDict([("act_0_1", hx(world.level_end[0])), ("act_2_to_255", hx(world.level_end[2]))])),
        ("special_stage_entry_guard", world.guard),
        ("special_stage_return", OrderedDict((str(k), list(v)) for k, v in sorted(world.ss_exit.items()) if k in (0, 3, 5))),
        ("zone_complete", OrderedDict((str(k), [v[0], v[1], hx(v[2])]) for k, v in sorted(world.zone_complete.items())
                                      if k in (0, 4, 5, 6, 12))),
        ("states", OrderedDict((k, len(tabs[k][0])) for k in tabs)),
        ("summary_any_path", summarize_states(allr)), ("summary_grounded", summarize_states(grd)),
        ("summary_grounded_normal_play", summarize_states(nrm)),
        ("states_cut_at_act_cap", OrderedDict((k, len(tabs[k][1])) for k in tabs)),
        ("grounded_rule", "an edge is grounded when every record it loads is one of the nine records of the proposed domain "
                          "and a special stage is the one entered with no emerald bit set (the others need object-supplied masks)"),
        ("act_growth_mechanism", OrderedDict([
            ("increment_unguarded", increments_unguarded), ("special_stage_entry_unguarded_by_act", ss_entry_unguarded_by_act),
            ("explanation", "a 100-ring pickup arms the special stage whatever the act; its return raises D293 bit 5 and the "
                            "act-complete path increments the act ($1538) with no bound")])),
    ])
    doc["unresolved_dependencies"] = [OrderedDict([("id", i), ("title", t), ("text", x)]) for i, t, x in UNRESOLVED]
    doc["propositions"] = OrderedDict()
    for key, title, ev in (("A", "zone-music table read at $18A0", a_eval), ("B", "level loader record selection at $2A4F", b_eval),
                           ("C", "nested dispatcher $741F1 in bank $1D", c_eval)):
        rec = OrderedDict([("title", title), ("status", statuses[key])])
        rec.update(ev)
        doc["propositions"][key] = rec
    n_sites = sum(len(v) for v in census.values())
    doc["propositions"]["A"]["writers"] = ("all %d absolute stores to the three bytes are classified (see writers); the act is "
                                           "unbounded through $1538" % n_sites)
    first_bad = OrderedDict((str(z), next((a for a in range(256) if not music_consumer(rom).valid(z, a)), None))
                            for z in range(8, 13))
    doc["propositions"]["A"]["first_violating_act_by_special_stage_zone"] = first_bad
    doc["propositions"]["B"]["sub_claims"] = OrderedDict([
        ("sufficiency_of_zone_le_15_and_act_le_2", "PROVEN (all 48 combinations executed; nine records; slot types from them)"),
        ("zone_le_15_whenever_the_loader_runs", "PARTIAL (every writer but U1 gives <= 12; U1 would reach 13)"),
        ("act_le_2_whenever_the_loader_runs", "DISPROVEN (grounded counterexample)"),
        ("invalid_combinations", "not rejected: the loader never validates; out-of-range acts alias the following zones' "
                                 "tables, and past the last pointer the record pointer is record data")])
    doc["propositions"]["C"]["exclusions"] = OrderedDict([
        ("type_5_records_in_zone_table_order", "records $2B0A, $2B1E, $2B28 only"),
        ("construct_type_5_through_the_loader_with_zone_gt_5", "none within the nine records for any act the model reaches on "
                                                               "a grounded path; special stages at act >= 9 / >= 6 read a "
                                                               "garbage pointer (U3)"),
        ("construct_type_5_through_the_allocator", "not excluded (U4)"),
        ("survive_a_zone_change", "slot types are cleared by $1CEB and the object RAM by $297E before the reload on the "
                                  "zone-complete, act-complete and special-stage-start paths (slot_lifetime); title, "
                                  "restart and continue entries were not traced"),
    ])
    doc["r1_relationship"] = OrderedDict([
        ("r1_overall", "PARTIALLY CLOSED (unchanged)"),
        ("dispatchers", OrderedDict([
            ("$08137", OrderedDict([
                ("closed_by_r2", "nothing: the zone-music route is not shown to stay inside the table"),
                ("still_open", "ZONE/ACT lemma (A is PARTIAL: a table over-read in a special stage needs act >= %s at zone 8, "
                               ">= %s at zone 9, >= %s at zone 10, >= %s at zone 11 or >= %s at zone 12 - all behind U2/U3) "
                               "and the SOUND TEST $D2BF lemma (untouched by R2)" % tuple(first_bad[str(z)] for z in range(8, 13))),
                ("other_dependencies", ["sound-test closure has unresolved computed jumps (R1)", "U1, U2, U3"])])),
            ("$74027", OrderedDict([
                ("closed_by_r2", "the record-fetch dependency is *not* closed as stated (act <= 2 is DISPROVEN); a weaker "
                                 "statement is: for zone <= 15 and act <= the per-zone safe bound the four slot types come "
                                 "from the nine records"),
                ("still_open", "ALLOCATOR / kernel-vector lemma (every caller of $1CD3 passes C <= 20)"),
                ("other_dependencies", ["U3 (act beyond the safe bound), U4"])])),
            ("$741F1", OrderedDict([
                ("closed_by_r2", "the table extent (12 entries) and the zones that index inside it are exact; no grounded "
                                 "path puts a type-5 slot beside a zone outside the table"),
                ("still_open", "type-5 slot creation by the allocator, zone-complete inside a special stage, and "
                               "special stages at garbage records"),
                ("other_dependencies", ["U1, U3, U4"])]))])),
        ("r1_open_conditions_read", [OrderedDict([("site", c["site"]), ("status", c["status"])]) for c in r1_open]),
        ("r1_verdict_read", r1_verdict["r1"]),
    ])
    doc["verdict"] = OrderedDict([
        ("A", statuses["A"]), ("B", statuses["B"]), ("C", statuses["C"]),
        ("r1_overall_changes", False),
        ("supported_bounds", OrderedDict([
            ("zone_values_on_grounded_paths", sorted({s[0] for s in grd})),
            ("zone_values_on_any_modelled_path", sorted({s[0] for s in allr})),
            ("act_values_on_grounded_paths", [min(s[1] for s in grd), max(s[1] for s in grd)]),
            ("music_index_in_table_iff", "(3*zone + act) mod 256 <= 38"),
            ("loader_safe_act_by_zone", OrderedDict((str(z), world.safe[z]) for z in range(16))),
            ("nested_dispatcher_zones", zone_ok)])),
        ("real_counterexamples", (["B: act 3 reachable in normal play (new game, act 0 -> 1 -> 2, 100 rings, special stage, "
                                  "return)"] if b_n else [])),
        ("unresolved_writers", [], ),
    ])
    doc["verdict"]["unresolved_writers"] = [[n, hx(o)] for n, o in unclassified]
    doc["ledger_effect"] = OrderedDict([("changed", False),
                                        ("note", "No recovered region, seed or classification is added or changed.")])
    return doc, dict(code=code, world=world, tabs=tabs, a=(a_all, a_g, a_ia, a_ig), b=(b_all, b_g, b_n),
                     c=(c_all, c_g, c_unres), fx=fx, irq=irq, sel=sel, bm=bm, pm=pm, census=census, classes=classes,
                     statuses=statuses, zone_ok=zone_ok, unclassified=unclassified)


# --- 13. output -----------------------------------------------------------------------------------------------------
BEGIN, END_MARK = "<!-- r2-generated:begin -->", "<!-- r2-generated:end -->"


def dumps(doc):
    return json.dumps(doc, indent=1, ensure_ascii=True) + "\n"


def render_block(doc):
    P = doc["propositions"]
    lines = [BEGIN, "", "| Proposition | Status |", "|---|---|"]
    for k in "ABC":
        lines.append("| %s - %s | **%s** |" % (k, P[k]["title"], P[k]["status"]))
    w = doc["census"]["absolute_store_sites"]
    lines += ["", "Writer census: %d zone, %d act and %d saved-zone absolute stores; wide / index-register hits: %d; mirror hits: %d."
              % (w["zone"], w["act"], w["saved_zone"], len(doc["census"]["wide_or_index_register_store_hits"]),
                 len(doc["census"]["mirror_alias_store_hits"])), ""]
    tm = doc["transition_model"]
    lines.append("Modelled states (act cap %d): %d on any path, %d grounded, %d grounded in normal play." % (
        tm["act_cap"], tm["states"]["any"], tm["states"]["grounded"], tm["states"]["normal"]))
    ex = P["B"]["grounded_counterexample"]
    if ex:
        lines += ["", "Counterexample to B (normal play): " + " -> ".join(
            "%s%s" % (step["via"], tuple(step["state"][:2])) for step in ex["path"]), ""]
    sb = doc["verdict"]["supported_bounds"]
    lines.append("Music index is inside the table iff `%s`; nested-dispatcher zones inside the table: %s." % (
        sb["music_index_in_table_iff"], sb["nested_dispatcher_zones"]))
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
    ap.add_argument("--check", action="store_true", help="fail if the committed evidence differs from a fresh run")
    args = ap.parse_args(argv)
    import rom_ledger as RL
    rom_path = Path(args.rom) if args.rom else RL.DEFAULT_ROM
    rom = rom_path.read_bytes()
    import hashlib
    if len(rom) != RL.ROM_SIZE or hashlib.sha256(rom).hexdigest() != RL.ROM_SHA256:
        print("the ROM is not the canonical Europe v1.2 image", file=sys.stderr)
        return 2
    doc, _ctx = build(rom)
    text = dumps(doc)
    out = Path(args.output)
    if args.check:
        if not out.is_file() or out.read_text(encoding="utf-8") != text:
            print("evidence differs from a fresh run", file=sys.stderr)
            return 1
        print("evidence matches")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    if args.doc:
        update_doc(args.doc, doc)
    print("wrote %s: A=%s B=%s C=%s" % (out, doc["propositions"]["A"]["status"], doc["propositions"]["B"]["status"],
                                       doc["propositions"]["C"]["status"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

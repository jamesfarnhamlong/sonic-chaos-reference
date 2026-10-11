#!/usr/bin/env python3
"""DECOMP-1D: bank-aware control-flow proof for ``CALL $8000``-style transfers.

    python tools/decomp1d_banked_flow.py /path/to/SonicChaos.sms [--output data/decomp1d/banked-flow.json]

DECOMP-1A/1B/1C never resolve a resident ``CALL`` into slot 2 (CPU ``$8000-$BFFF``): the bank is whatever the
mapper register holds, so the CPU address alone names sixteen... in fact 32 different routines. This module adds
one narrow, fully re-derivable proof of the bank, and refuses everything else.

A transfer is *supported* only when the original ROM instructions show all of the following:

1. The caller is a ``CALL nn`` (``nn`` in ``$8000-$BFFF``) at a file offset below ``$8000`` inside byte-verified
   recovered assembly.
2. The two instructions directly before it, in the same recovered region, are ``LD A,n`` and ``CALL setter``, where
   ``setter`` decodes to exactly ``LD (shadow),A / LD ($FFFF),A / RET``. ``$FFFF`` is the Sega mapper's slot-2 bank
   register, so slot 2 holds bank ``n`` from the ``RET`` until something else writes the register.
3. The ``CALL setter`` returns to the caller instruction (no instruction between them) and nothing can enter the
   sequence in the middle: no decoded CALL/JP/JR/DJNZ in recovered or hardware-vector-reachable code targets the
   setter call or the banked call, and every 16-bit literal equal to those addresses lies in bytes the ledger's
   independent structural evidence classifies as non-code.
4. Interrupts cannot leave slot 2 changed: the NMI handler touches no mapper register; the IM 1 handler returns only
   through the tail that rewrites ``$FFFF`` from the shadow the setter wrote first; the handler's resident call
   closure never stores to the shadow; and no byte sequence anywhere in the ROM stores to the shadow outside the
   resident engine.

The destination is ``bank * $4000 + (nn - $8000)``. Nothing is keyed by the CPU address, so two ``CALL $8000`` sites
with different banks give two different file offsets (see ``ambiguity``), and a site without the proof stays unresolved
with the reason recorded.

Residual assumptions that a static analysis cannot discharge are listed in ``RESIDUAL_ASSUMPTIONS`` and written into
the evidence; the ledger refuses an evidence file that drops them. This is static control-flow evidence, not an
execution trace.
"""
import argparse
import bisect
import hashlib
import json
import sys
from collections import OrderedDict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import rom_flow as F  # noqa: E402
from z80dis import z80  # noqa: E402

OP = F.OP
BANK = 0x4000
ROM_BANKS = 32
SLOT2_LO, SLOT2_HI = 0x8000, 0xC000
MAPPER = OrderedDict([(0xFFFC, "cartridge control"), (0xFFFD, "slot 0 bank"), (0xFFFE, "slot 1 bank"),
                      (0xFFFF, "slot 2 bank")])
SLOT2_REGISTER = 0xFFFF
VECTOR_RESET, VECTOR_IRQ, VECTOR_NMI = 0x0000, 0x0038, 0x0066
RESTART = 0x0450
BANKED_PREFIX = "banked_"
OUTPUT = ROOT / "data" / "decomp1d" / "banked-flow.json"
NON_CODE = ("DATA", "GRAPHICS", "COMPRESSED", "MUSIC", "PADDING")

RESIDUAL_ASSUMPTIONS = (
    OrderedDict([("id", "R1"), ("text",
        "The banked routines the IM 1 handler calls (listed in interrupt_model.irq.banked_callees) are not walked. "
        "No byte sequence in banks 2-31 stores to the mapper shadow, but those routines could transfer into a "
        "resident routine that does; that is not excluded.")]),
    OrderedDict([("id", "R2"), ("text",
        "Register-addressed stores (LD (HL),r / (IX+d) / block moves) that alias $FFFF or the shadow are not modelled; "
        "only absolute-address stores are.")]),
    OrderedDict([("id", "R3"), ("text",
        "Slot 1 is bank 1 whenever the IM 1 handler starts. Absolute stores to $FFFE/$FFFD exist in the reset path and "
        "the handler, plus the byte patterns listed in mapper_model.slot1_register_stores; those patterns lie in "
        "compressed data, in bytes with no classification, or in CODE-classified bytes that are not decoded here, so "
        "they cannot be shown not to be instructions.")]),
    OrderedDict([("id", "R4"), ("text",
        "Standard Sega mapper semantics (a write to $FFFF selects a 16 KiB bank for $8000-$BFFF; bank numbers are "
        "taken modulo the 32 pages in the ROM). Only the ROM's own use of the register corroborates this; no "
        "emulator trace is used.")]),
)


def hx(v):
    return "$%04X" % v if v < 0x10000 else "$%05X" % v


# --- instruction pattern helpers ---------------------------------------------------------------
def _is_reg(operand, name):
    return operand[0].name == "REG" and getattr(operand[1], "name", None) == name


def abs_store_a(d):
    """``LD (nn),A`` -> nn, else None."""
    if d.op == OP.LD and len(d.operands) == 2 and d.operands[0][0].name == "ADDR_DEREF" and _is_reg(d.operands[1], "A"):
        return d.operands[0][1]
    return None


def abs_load_a(d):
    if d.op == OP.LD and len(d.operands) == 2 and d.operands[1][0].name == "ADDR_DEREF" and _is_reg(d.operands[0], "A"):
        return d.operands[1][1]
    return None


def imm_load_a(d):
    if d.op == OP.LD and len(d.operands) == 2 and _is_reg(d.operands[0], "A") and d.operands[1][0].name == "IMM":
        return d.operands[1][1]
    return None


def is_ret(d):
    return d.op == OP.RET and not F._has_cond(d)


def asm(rom, off):
    d = F.decode(rom, off)
    return "%s" % z80.disasm(d) if d.len else "??"


def file_offset(bank, cpu):
    return bank * BANK + (cpu - SLOT2_LO)


# --- mapper setter -------------------------------------------------------------------------------
def mapper_setter(rom, entry):
    """Shape proof of ``LD (shadow),A / LD ($FFFF),A / RET`` at a resident ``entry``; None if it differs."""
    if not 0 <= entry < F.RESIDENT_END - 8:
        return None
    p, parts = entry, []
    for _ in range(3):
        d = F.decode(rom, p)
        if F.is_invalid(d):
            return None
        parts.append((p, d))
        p += d.len
    (a0, d0), (a1, d1), (a2, d2) = parts
    shadow = abs_store_a(d0)
    if shadow is None or not 0xC000 <= shadow < 0xE000 or abs_store_a(d1) != SLOT2_REGISTER or not is_ret(d2):
        return None
    return OrderedDict([("entry", entry), ("shadow", shadow), ("register", SLOT2_REGISTER),
                        ("instructions", [OrderedDict([("offset", a), ("bytes", rom[a:a + F.decode(rom, a).len].hex()),
                                                       ("asm", asm(rom, a))]) for a, _ in parts]),
                        ("order", "shadow is stored before the register, so an interrupt between the two stores "
                                  "still leaves register == shadow")])


# --- decoded-instruction universe ------------------------------------------------------------------
def resident_descent(rom):
    """Instruction offsets reached from reset, IM 1 and NMI over the resident engine (CALL/JP/JR/DJNZ and
    fall-through only; indirect jumps and slot-2 calls are not followed). Same rule as DECOMP-1B."""
    ins = {}
    for root in (VECTOR_RESET, VECTOR_IRQ, VECTOR_NMI):
        queue = deque([root])
        while queue:
            p = queue.popleft()
            if p in ins or not 0 <= p < F.RESIDENT_END:
                continue
            d = F.decode(rom, p)
            if F.is_invalid(d) or p + d.len > F.RESIDENT_END:
                continue
            ins[p] = d.len
            if d.op in F.TRANSFER_OPS:
                a = F._addr_operand(d)
                t = F.resolve_target(p, a) if a is not None else None
                if t is not None and t < F.RESIDENT_END:
                    queue.append(t)
            if not F.is_terminal(d):
                queue.append(p + d.len)
    return ins


class Facts:
    """ROM-derived indices shared by every proof in one process (cached per ROM image)."""
    _cache = {}

    def __init__(self, rom):
        self.rom = rom
        self.descent = resident_descent(rom)
        self.interrupt = None

    @classmethod
    def of(cls, rom):
        key = hashlib.sha256(rom).digest()
        if key not in cls._cache:
            cls._cache[key] = cls(rom)
        return cls._cache[key]


def region_instruction_list(rom, regions):
    """{region name: [(offset, length, decoded)]} for recovered CODE regions."""
    return {r["name"]: F.region_instructions(rom, r) for r in F.code_regions(regions)}


def all_decoded(rom, regions, facts):
    """Instruction start -> length over recovered CODE and hardware-vector-reachable resident code."""
    ins = dict(facts.descent)
    for r in F.code_regions(regions):
        for p, n, _ in F.region_instructions(rom, r):
            ins[p] = n
    return ins


def transfer_sites(rom, instrs):
    """{resident file offset: [(site, op)]} for decoded CALL/JP/JR/DJNZ with a resolvable resident target."""
    out = {}
    for p in sorted(instrs):
        d = F.decode(rom, p)
        if d.op in F.TRANSFER_OPS:
            a = F._addr_operand(d)
            t = F.resolve_target(p, a) if a is not None else None
            if t is not None and t < F.RESIDENT_END:
                out.setdefault(t, []).append((p, d.op.name))
    return out


# --- word literals ---------------------------------------------------------------------------------
def word_hits(rom, value):
    needle = bytes([value & 0xFF, value >> 8])
    out, i = [], rom.find(needle)
    while i != -1:
        out.append(i)
        i = rom.find(needle, i + 1)
    return out


class Context:
    """Independent structural classes (non-code intervals and code-classified intervals) from ledger claims."""

    def __init__(self, claims=None):
        self.available = claims is not None
        self.non_code, self.code = [], []
        for c in claims or ():
            if c["primary"] in NON_CODE:
                self.non_code.append((c["start"], c["end"], c["primary"]))
            elif c["primary"] == "CODE":
                self.code.append((c["start"], c["end"]))
        self.non_code.sort()
        self.code.sort()

    def non_code_class(self, offsets):
        """Class name when every offset is covered by a non-code claim and by no CODE claim, else None."""
        if not self.available:
            return None
        cls = set()
        for o in offsets:
            hit = next((c for lo, hi, c in self.non_code if lo <= o < hi), None)
            if hit is None or any(lo <= o < hi for lo, hi in self.code):
                return None
            cls.add(hit)
        return "/".join(sorted(cls))


def classify_word_hit(rom, offset, value, starts, instrs, ctx):
    """How one 16-bit literal equal to ``value`` sits in the ROM."""
    i = bisect.bisect_right(starts, offset + 1) - 1          # last instruction starting at or before offset+1
    for j in (i, i - 1):
        if j >= 0:
            s = starts[j]
            if s <= offset + 1 < s + instrs[s] or s <= offset < s + instrs[s]:
                d = F.decode(rom, s)
                kind = "transfer_operand" if d.op in F.TRANSFER_OPS else "literal_operand"
                return OrderedDict([("offset", offset), ("class", kind), ("instruction", s), ("asm", asm(rom, s))])
    cls = ctx.non_code_class((offset, offset + 1))
    if cls:
        return OrderedDict([("offset", offset), ("class", "inert_data"), ("ledger_class", cls)])
    return OrderedDict([("offset", offset), ("class", "unexplained")])


def sequence_blockers(rom, interior, instrs, ctx):
    """Entries into the middle of a setup sequence: decoded transfers and address literals that are not inert."""
    sites = transfer_sites(rom, instrs)
    starts = sorted(instrs)
    blockers, benign = [], []
    for addr in interior:
        for site, op in sites.get(addr, ()):
            blockers.append(OrderedDict([("kind", "transfer"), ("target", addr), ("site", site), ("op", op)]))
        for off in word_hits(rom, addr):
            row = classify_word_hit(rom, off, addr, starts, instrs, ctx)
            row["literal"] = addr
            (benign if row["class"] == "inert_data" else blockers).append(row)
    return blockers, benign


# --- interrupt model -------------------------------------------------------------------------------
STORE_FORMS = (  # byte encodings of absolute stores whose last two bytes are the address
    ("LD (nn),A", bytes([0x32])), ("LD (nn),HL", bytes([0x22])),
    ("LD (nn),BC", bytes([0xED, 0x43])), ("LD (nn),DE", bytes([0xED, 0x53])),
    ("LD (nn),HL", bytes([0xED, 0x63])), ("LD (nn),SP", bytes([0xED, 0x73])),
    ("LD (nn),IX", bytes([0xDD, 0x22])), ("LD (nn),IY", bytes([0xFD, 0x22])))


def store_pattern_sites(rom, address, width=1):
    """File offsets of every absolute-store encoding that writes ``address`` (alignment-independent)."""
    out = []
    for kind, prefix in STORE_FORMS:
        wide = kind != "LD (nn),A"
        for a in (range(address - 1, address + 1) if wide and width else (address,)):
            needle = prefix + bytes([a & 0xFF, a >> 8])
            if a != address and (not wide or a + 2 <= address):
                continue
            i = rom.find(needle)
            while i != -1:
                out.append((i, kind))
                i = rom.find(needle, i + 1)
    return sorted(set(out))


def _walk_top_level(rom, roots, limit=2000):
    """IM 1 / NMI top-level body with every CALL stepped over as an opaque callee that may remap slot 2.

    Returns (exits, dirty_stores, instructions, problems): ``exits`` lists (offset, slot2_matches_shadow) for every
    RET/RETI/RETN reached.
    """
    seen, exits, problems, visited = set(), [], [], set()
    stack = [(r, False) for r in roots]
    while stack and len(seen) < limit:
        pc, dirty = stack.pop()
        prev_load = None
        while True:
            if (pc, dirty) in seen:
                break
            seen.add((pc, dirty))
            visited.add(pc)
            if not 0 <= pc < F.RESIDENT_END:
                problems.append(("leaves_resident", pc))
                break
            d = F.decode(rom, pc)
            if F.is_invalid(d):
                problems.append(("invalid", pc))
                break
            store = abs_store_a(d)
            if store == SLOT2_REGISTER:
                dirty = not (prev_load is not None and prev_load[0] == "shadow")
            prev_load = ("shadow", abs_load_a(d)) if abs_load_a(d) is not None else None
            if d.op in (OP.RET, OP.RETI, OP.RETN):
                exits.append((pc, dirty))
                if not F._has_cond(d):
                    break
            elif d.op == OP.CALL:
                dirty = True                              # an opaque callee may remap slot 2
            elif d.op in (OP.JP, OP.JR, OP.DJNZ):
                t = F._addr_operand(d)
                if t is None:
                    problems.append(("indirect", pc))
                    break
                if t >= F.RESIDENT_END:
                    problems.append(("leaves_resident", pc))
                    break
                stack.append((t, dirty))
            if F.is_terminal(d):
                break
            pc += d.len
    return exits, visited, problems


def _closure(rom, root, shadow):
    """Resident call closure of the IM 1 handler with a mapper-state-aware slot 1.

    Returns a dict of facts. Banked callees are recorded but not walked; ``restart`` edges (JP to the reset path
    ``DI / LD SP,$DFF0``) discard the interrupted context and are not followed.
    """
    seen, walked = set(), set()
    stores, banked, restart, problems = [], [], [], []
    stack = [(root, 1)]          # R3: slot 1 is bank 1 when the handler starts
    while stack:
        pc, s1 = stack.pop()
        prev = None
        while True:
            if (pc, s1) in seen:
                break
            seen.add((pc, s1))
            walked.add(pc)
            d = F.decode(rom, pc)
            if F.is_invalid(d) or pc >= F.RESIDENT_END:
                problems.append(("invalid_or_non_resident", pc))
                break
            sa = abs_store_a(d)
            if sa in MAPPER or sa == shadow:
                stores.append((pc, sa))
            if sa == 0xFFFE:
                s1 = prev if isinstance(prev, int) else ("S" if prev == "shadow" else "U")
            la = abs_load_a(d)
            prev = "shadow" if la is not None else imm_load_a(d)
            if d.op in (OP.CALL, OP.JP, OP.JR, OP.DJNZ):
                t = F._addr_operand(d)
                if t is None:
                    problems.append(("indirect", pc))
                elif t == RESTART:
                    restart.append(pc)
                elif t < 0x4000:
                    stack.append((t, s1))
                elif t < F.RESIDENT_END:
                    if s1 == 1:
                        stack.append((t, s1))
                    elif isinstance(s1, int):
                        banked.append((pc, t, "slot1=%d" % s1, file_offset(s1, t + 0x4000)))
                    else:
                        problems.append(("slot1_unknown", pc))
                else:
                    banked.append((pc, t, "slot2", None))
            elif d.op in (OP.JP,):
                problems.append(("indirect", pc))
            if is_ret(d) or F.is_terminal(d):
                break
            pc += d.len
    return walked, stores, banked, restart, problems


def interrupt_model(rom):
    """NMI / IM 1 behaviour with respect to the slot-2 register and its shadow, derived from the ROM."""
    setter = mapper_setter(rom, 0x1C6F)
    shadow = setter["shadow"] if setter else None
    out = OrderedDict()
    reasons = []
    # NMI (pause button)
    nmi_exits, nmi_pcs, nmi_problems = _walk_top_level(rom, [VECTOR_NMI])
    nmi_stores = sorted(pc for pc in nmi_pcs if abs_store_a(F.decode(rom, pc)) in MAPPER or
                        (shadow is not None and abs_store_a(F.decode(rom, pc)) == shadow))
    nmi_calls = sorted(pc for pc in nmi_pcs if F.decode(rom, pc).op == OP.CALL)
    nmi_ok = bool(nmi_exits) and not nmi_problems and not nmi_stores and not nmi_calls
    out["nmi"] = OrderedDict([("vector", VECTOR_NMI), ("instructions", len(nmi_pcs)),
                              ("mapper_or_shadow_stores", nmi_stores), ("calls", nmi_calls),
                              ("exits", [e for e, _ in nmi_exits]), ("problems", nmi_problems),
                              ("leaves_mapper_untouched", nmi_ok)])
    if not nmi_ok:
        reasons.append("nmi_handler_not_proven_mapper_neutral")
    # IM 1
    exits, pcs, problems = _walk_top_level(rom, [VECTOR_IRQ])
    bad = [e for e, dirty in exits if dirty]
    restore_sites = sorted(pc for pc in pcs if abs_store_a(F.decode(rom, pc)) == SLOT2_REGISTER)
    restores = [pc for pc in restore_sites
                if abs_load_a(F.decode(rom, pc - 3)) == shadow and pc - 3 in pcs and shadow is not None]
    contract = bool(exits) and not bad and not problems and shadow is not None
    out_irq = OrderedDict([("vector", VECTOR_IRQ), ("top_level_instructions", len(pcs)),
                           ("exits", [OrderedDict([("offset", e), ("slot2_matches_shadow", not dirty)]) for e, dirty in exits]),
                           ("exit_restore_stores", restores), ("top_level_problems", problems),
                           ("exit_contract", "every RET reached from the vector, with callees treated as opaque and "
                                             "every register store other than LD A,(shadow) / LD ($FFFF),A treated "
                                             "as a change, leaves $FFFF equal to the shadow"),
                           ("exit_contract_holds", contract)])
    if not contract:
        reasons.append("irq_exit_contract_not_proven")
    walked, stores, banked, restart, cproblems = _closure(rom, VECTOR_IRQ, shadow)
    shadow_stores = sorted(pc for pc, a in stores if a == shadow)
    out_irq["resident_closure"] = OrderedDict([
        ("instructions", len(walked)),
        ("shadow_store_sites", shadow_stores),
        ("register_stores", [OrderedDict([("offset", pc), ("register", MAPPER[a])]) for pc, a in sorted(stores) if a in MAPPER]),
        ("restart_edges", sorted(restart)),
        ("restart_rule", "a JP to $0450 (DI / LD SP,$DFF0) discards the interrupted context and does not return to it"),
        ("problems", sorted(set(cproblems)))])
    out_irq["banked_callees"] = [OrderedDict([("call_site", s), ("cpu_target", t), ("mapping", m), ("file_offset", f)])
                                 for s, t, m, f in sorted(set(banked))]
    closure_ok = not shadow_stores and not cproblems
    if not closure_ok:
        reasons.append("shadow_store_or_unmodelled_edge_in_irq_closure")
    out["irq"] = out_irq
    # ROM-wide shadow stores
    sites = [(o, k) for o, k in store_pattern_sites(rom, shadow, 1)] if shadow is not None else []
    # a 16-bit store at shadow-1 also writes the shadow
    wide = [(o, k) for o, k in (store_pattern_sites(rom, shadow - 1, 2) if shadow is not None else []) if k != "LD (nn),A"]
    all_sites = sorted(set(sites + wide))
    banked_sites = [o for o, _ in all_sites if o >= F.RESIDENT_END]
    out["shadow_store_patterns"] = OrderedDict([
        ("shadow", shadow), ("sites", [OrderedDict([("offset", o), ("form", k)]) for o, k in all_sites]),
        ("outside_resident_engine", banked_sites)])
    if banked_sites:
        reasons.append("shadow_store_pattern_in_banked_rom")
    out["banked_callee_scan_note"] = "see residual_assumptions R1"
    out["supported"] = not reasons
    out["reasons"] = reasons
    return out


def mapper_register_stores(rom):
    """ROM-wide absolute stores to each mapper register, with the value stored when it is an immediate load."""
    out = OrderedDict()
    for reg, name in MAPPER.items():
        rows = []
        for off, kind in store_pattern_sites(rom, reg, 1):
            row = OrderedDict([("offset", off), ("form", kind)])
            if off < F.RESIDENT_END and kind == "LD (nn),A":
                prev = None
                for back in (2, 3):
                    q = off - back
                    d = F.decode(rom, q) if q >= 0 else None
                    if d is not None and not F.is_invalid(d) and q + d.len == off:
                        prev = imm_load_a(d)
                        break
                if prev is not None:
                    row["immediate_value"] = prev
            rows.append(row)
        out[hx(reg)] = OrderedDict([("register", name), ("sites", rows)])
    return out


# --- the banked-call proof ---------------------------------------------------------------------------
def _site_context(rom, regions, caller):
    for r in F.code_regions(regions):
        if r["start"] <= caller < r["end"]:
            return r, F.region_instructions(rom, r)
    return None, None


def prove_banked_call(rom, regions, caller, ctx=None, facts=None, interrupt=None):
    """Everything known about the slot-2 ``CALL`` at ``caller``. Always returns a record; ``status`` is
    ``supported`` or ``unresolved`` and ``reasons`` explains the latter."""
    facts = facts or Facts.of(rom)
    ctx = ctx or Context(None)
    d = F.decode(rom, caller) if 0 <= caller < len(rom) - 4 else None
    rec = OrderedDict([("caller", caller), ("status", "unresolved"), ("reasons", [])])
    reasons = rec["reasons"]
    if d is None or F.is_invalid(d):
        reasons.append("caller_does_not_decode")
        return rec
    rec["instruction"] = OrderedDict([("bytes", rom[caller:caller + d.len].hex()), ("asm", asm(rom, caller))])
    target = F._addr_operand(d)
    if d.op != OP.CALL or target is None:
        reasons.append("not_a_direct_call")
        return rec
    rec["cpu_target"] = target
    if not SLOT2_LO <= target < SLOT2_HI:
        reasons.append("target_not_in_slot_2")
    if caller >= F.RESIDENT_END:
        reasons.append("caller_not_in_resident_engine")
    region, ins = _site_context(rom, regions, caller)
    if region is None:
        reasons.append("caller_not_in_byte_verified_recovered_code")
    else:
        rec["region"] = region["name"]
    if reasons:
        _hint(rom, rec, caller)
        return rec
    idx = next(i for i, (p, _, _) in enumerate(ins) if p == caller)
    if idx < 2:
        reasons.append("no_bank_setup_before_call")
        _hint(rom, rec, caller)
        return rec
    (p_ld, n_ld, d_ld), (p_set, n_set, d_set) = ins[idx - 2], ins[idx - 1]
    value = imm_load_a(d_ld)
    setter_entry = F._addr_operand(d_set) if d_set.op == OP.CALL else None
    if setter_entry is None:
        reasons.append("no_bank_setup_before_call")
        _hint(rom, rec, caller)
        return rec
    setter = mapper_setter(rom, setter_entry)
    if setter is None:
        reasons.append("callee_is_not_a_recognised_mapper_setter")
    if value is None:
        reasons.append("bank_value_not_an_immediate")
    elif not 0 <= value < ROM_BANKS:
        reasons.append("bank_value_outside_the_rom")
    if p_set + n_set != caller:
        reasons.append("setter_does_not_return_to_the_call")
    if reasons:
        return rec
    seq = [OrderedDict([("offset", p), ("bytes", rom[p:p + n].hex()), ("asm", asm(rom, p))])
           for p, n in ((p_ld, n_ld), (p_set, n_set), (caller, d.len))]
    rec["sequence"] = seq
    rec["bank_selection"] = OrderedDict([
        ("instruction", p_ld), ("value", value), ("setter_call", p_set), ("setter", setter),
        ("register", "slot 2 bank ($FFFF)"), ("shadow", setter["shadow"])])
    rec["mapper_state_at_call"] = OrderedDict([
        ("slot2_bank", value),
        ("basis", "LD A,n directly before CALL setter; setter stores A to the shadow then $FFFF and returns to the "
                  "call; nothing executes in between")])
    rec["destination"] = OrderedDict([
        ("bank", value), ("cpu", target), ("file_offset", file_offset(value, target)),
        ("rule", "bank * $4000 + (cpu - $8000)")])
    instrs = all_decoded(rom, regions, facts)
    blockers, benign = sequence_blockers(rom, [p_set, caller], instrs, ctx)
    if not ctx.available:
        blockers.append(OrderedDict([("kind", "no_structural_context"),
                                     ("note", "literal classification needs the ledger's independent claims")]))
    rec["sequence_integrity"] = OrderedDict([
        ("interior_addresses", [p_set, caller]), ("entries_into_sequence", blockers),
        ("inert_literals", benign),
        ("scanned", "decoded CALL/JP/JR/DJNZ in recovered and hardware-vector-reachable code, and every 16-bit "
                    "literal in the ROM")])
    if blockers:
        reasons.append("something_can_enter_the_sequence_midway")
    model = interrupt if interrupt is not None else (facts.interrupt or interrupt_cached(rom, facts))
    rec["interrupt_safety"] = OrderedDict([("supported", model["supported"]), ("reasons", model["reasons"]),
                                           ("shadow", setter["shadow"]),
                                           ("model", "data/decomp1d/banked-flow.json interrupt_model")])
    if not model["supported"]:
        reasons.extend(model["reasons"])
    if model.get("irq") and model["irq"]["exit_restore_stores"]:
        pass
    if not reasons:
        rec["status"] = "supported"
        rec["follow_safely"] = True
        rec["follow_rule"] = ("code executing in slot 2 cannot remap slot 2 without leaving itself, so a descent "
                              "confined to the destination bank may resolve same-bank slot-2 targets")
        rec["residual_assumptions"] = [a["id"] for a in RESIDUAL_ASSUMPTIONS]
    else:
        rec["follow_safely"] = False
    return rec


def _hint(rom, rec, caller):
    """For a call without proof, note a direct register write directly before it (information only)."""
    p = caller
    d1 = None
    for back in (3, 2):
        q = p - back
        d = F.decode(rom, q) if q >= 0 else None
        if d is not None and not F.is_invalid(d) and q + d.len == p:
            d1 = (q, d)
            break
    if d1 and abs_store_a(d1[1]) == SLOT2_REGISTER:
        q = d1[0]
        for back in (2, 3):
            r = q - back
            d = F.decode(rom, r) if r >= 0 else None
            if d is not None and not F.is_invalid(d) and r + d.len == q and imm_load_a(d) is not None:
                rec["unproven_bank_hint"] = OrderedDict([
                    ("bank", imm_load_a(d)), ("pattern", "LD A,n / LD ($FFFF),A directly before the call"),
                    ("why_not_claimed", "informational only: this module claims no entry without a recovered "
                                        "caller and the shadow-based interrupt proof")])
                return


def interrupt_cached(rom, facts):
    if facts.interrupt is None:
        facts.interrupt = interrupt_model(rom)
    return facts.interrupt


def slot2_calls(rom, regions, facts):
    """Every resident CALL/JP into slot 2 in recovered or hardware-vector-reachable code."""
    recovered = set()
    for r in F.code_regions(regions):
        for p, _, _ in F.region_instructions(rom, r):
            recovered.add(p)
    out = {}
    for p in sorted(set(facts.descent) | recovered):
        d = F.decode(rom, p)
        if d.op in (OP.CALL, OP.JP):
            t = F._addr_operand(d)
            if t is not None and SLOT2_LO <= t < SLOT2_HI:
                out[p] = (d.op.name, t, p in recovered)
    return out


def supported_entries(rom, regions, ctx=None, facts=None):
    """{destination file offset: [proof records]} for every supported banked call in recovered code."""
    facts = facts or Facts.of(rom)
    ctx = ctx or Context(None)
    out = {}
    for site, (op, target, in_recovered) in slot2_calls(rom, regions, facts).items():
        if op != "CALL" or not in_recovered:
            continue
        rec = prove_banked_call(rom, regions, site, ctx, facts)
        if rec["status"] == "supported":
            out.setdefault(rec["destination"]["file_offset"], []).append(rec)
    return out


# --- banked dispatch tables --------------------------------------------------------------------------
def _fetch_pattern(ins, idx):
    """True if the four instructions before ``ins[idx]`` (a JP (HL)) are LD A,(HL) / INC HL / LD H,(HL) / LD L,A."""
    if idx < 4:
        return False
    a, b, c, d = (x[2] for x in ins[idx - 4:idx])
    return (a.op == OP.LD and _is_reg(a.operands[0], "A") and a.operands[1][0].name == "REG_DEREF"
            and getattr(a.operands[1][1], "name", None) == "HL"
            and b.op == OP.INC and _is_reg(b.operands[0], "HL")
            and c.op == OP.LD and _is_reg(c.operands[0], "H") and c.operands[1][0].name == "REG_DEREF"
            and d.op == OP.LD and _is_reg(d.operands[0], "L") and _is_reg(d.operands[1], "A"))


def table_extent(rom, table, instr_offsets):
    """Number of consecutive words at ``table`` that are valid same-bank slot-2 code pointers.

    A word is valid when it points into slot 2, the target is not a byte of known code that is not an instruction
    start, and the instruction there decodes. The table stops at the first invalid word or at known code.
    """
    bank = table // BANK
    n = 0
    while True:
        p = table + 2 * n
        if p + 2 > (bank + 1) * BANK or any(p + k in instr_offsets for k in (0, 1)):
            break
        w = rom[p] | rom[p + 1] << 8
        if not SLOT2_LO <= w < SLOT2_HI:
            break
        d = F.decode(rom, file_offset(bank, w))
        if F.is_invalid(d):
            break
        n += 1
    return n


def find_tables(rom, entry_closure):
    """Bank-resolved dispatch tables loaded and consumed inside code reached from a supported entry.

    ``entry_closure`` maps instruction offset -> length. A table is a ``LD HL,nn`` (nn in slot 2) whose straight-line
    continuation, with no transfer and no branch target inside it, reaches ``JP (HL)`` through the word fetch
    ``LD A,(HL) / INC HL / LD H,(HL) / LD L,A``.
    """
    starts = sorted(entry_closure)
    ins = [(p, entry_closure[p], F.decode(rom, p)) for p in starts]
    targets = set()
    for p, n, d in ins:
        if d.op in F.TRANSFER_OPS:
            a = F._addr_operand(d)
            t = F.resolve_target(p, a) if a is not None else None
            if t is not None:
                targets.add(t)
    covered = set()
    for p, n, _ in ins:
        covered.update(range(p, p + n))
    out = []
    for i, (p, n, d) in enumerate(ins):
        if d.op != OP.LD or len(d.operands) != 2 or not _is_reg(d.operands[0], "HL") or d.operands[1][0].name != "IMM":
            continue
        imm = d.operands[1][1]
        if not SLOT2_LO <= imm < SLOT2_HI or p < F.RESIDENT_END:
            continue
        j = i + 1
        while j < len(ins) and ins[j][0] == ins[j - 1][0] + ins[j - 1][1] and ins[j][2].op not in F.TRANSFER_OPS \
                and not F.is_terminal(ins[j][2]) and ins[j][0] not in targets:
            j += 1
        if j >= len(ins) or ins[j][0] != ins[j - 1][0] + ins[j - 1][1] or not F.is_indirect_jump(ins[j][2]):
            continue
        if ins[j][0] in targets or not _fetch_pattern(ins, j):
            continue
        table = file_offset(p // BANK, imm)
        words = table_extent(rom, table, covered)
        if words:
            out.append(OrderedDict([("table", table), ("words", words), ("end", table + 2 * words),
                                    ("load_site", p), ("consumer", ins[j][0])]))
    return out


def entry_closure(rom, regions, ctx=None, facts=None):
    """{destination: {instruction offset: length}} confined to the destination bank, from supported entries only."""
    out = {}
    for dest in supported_entries(rom, regions, ctx, facts):
        lo = dest // BANK * BANK
        reached, _ = F.descend(rom, [dest], lo, lo + BANK)
        out.setdefault(dest, {}).update(reached)
    return out


def table_word_target(rom, table, index):
    w = rom[table + 2 * index] | rom[table + 2 * index + 1] << 8
    return file_offset(table // BANK, w)


def seed_support(rom, regions, ctx=None, facts=None):
    """{file offset: via} DECOMP-1A review seeds proven by this module (empty when nothing is supported)."""
    facts = facts or Facts.of(rom)
    out = OrderedDict()
    for dest, recs in sorted(supported_entries(rom, regions, ctx, facts).items()):
        out.setdefault(dest, OrderedDict([("banked_transfer", OrderedDict([
            ("caller", recs[0]["caller"]), ("bank", recs[0]["destination"]["bank"]),
            ("cpu", recs[0]["cpu_target"])]))]))
    for dest, closure in sorted(entry_closure(rom, regions, ctx, facts).items()):
        for t in find_tables(rom, closure):
            for i in range(t["words"]):
                off = table_word_target(rom, t["table"], i)
                out.setdefault(off, OrderedDict([("bank_table", OrderedDict([
                    ("table", t["table"]), ("words", t["words"]), ("load_site", t["load_site"]),
                    ("consumer", t["consumer"]), ("index", i)]))]))
    return out


# --- verification used by the ledger -----------------------------------------------------------------
def verify_seed(rom, regions, offset, via, ctx, facts=None):
    """Re-derive one banked seed; returns True or raises ValueError naming the stale/unsupported claim."""
    facts = facts or Facts.of(rom)
    if "banked_transfer" in via:
        c = via["banked_transfer"]
        rec = prove_banked_call(rom, regions, c["caller"], ctx, facts)
        if rec["status"] != "supported":
            raise ValueError("banked seed %s: caller %s is not a supported banked transfer (%s)"
                             % (hx(offset), hx(c["caller"]), ", ".join(rec["reasons"])))
        d = rec["destination"]
        if d["file_offset"] != offset or d["bank"] != c["bank"] or rec["cpu_target"] != c["cpu"]:
            raise ValueError("banked seed %s is stale: the ROM resolves caller %s to bank $%02X cpu %s file %s"
                             % (hx(offset), hx(c["caller"]), d["bank"], hx(rec["cpu_target"]), hx(d["file_offset"])))
        return True
    if "bank_table" in via:
        c = via["bank_table"]
        for dest, closure in entry_closure(rom, regions, ctx, facts).items():
            for t in find_tables(rom, closure):
                if t["table"] == c["table"]:
                    if (t["words"], t["load_site"], t["consumer"]) != (c["words"], c["load_site"], c["consumer"]):
                        raise ValueError("bank table seed %s is stale: table %s now proves %d words, load %s, consumer %s"
                                         % (hx(offset), hx(c["table"]), t["words"], hx(t["load_site"]), hx(t["consumer"])))
                    if not 0 <= c["index"] < t["words"] or table_word_target(rom, t["table"], c["index"]) != offset:
                        raise ValueError("bank table seed %s: word %d of table %s does not point there"
                                         % (hx(offset), c["index"], hx(c["table"])))
                    return True
        raise ValueError("bank table seed %s: no dispatch table at %s is reached from a supported banked entry"
                         % (hx(offset), hx(c["table"])))
    raise ValueError("unknown banked seed kind %r" % (sorted(via),))


# --- recovered regions of this milestone ------------------------------------------------------------
REGISTRY = (
    OrderedDict([("name", "banked_entry_70000"), ("start", 0x70000), ("end", 0x700CB),
                 ("entries", [OrderedDict([("offset", 0x70000), ("via", OrderedDict([("banked_transfer", OrderedDict([
                     ("caller", 0x16E7), ("bank", 0x1C), ("cpu", 0x8000)]))]))])])]),
    OrderedDict([("name", "banked_dispatch_7013E"), ("start", 0x7013E), ("end", 0x70146),
                 ("entries", [OrderedDict([("offset", 0x7013F), ("via", OrderedDict([("bank_table", OrderedDict([
                     ("table", 0x700CB), ("words", 16), ("load_site", 0x700BD), ("consumer", 0x700CA), ("index", 0)]))]))]),
                              OrderedDict([("offset", 0x7013E), ("via", OrderedDict([("bank_table", OrderedDict([
                     ("table", 0x700CB), ("words", 16), ("load_site", 0x700BD), ("consumer", 0x700CA), ("index", 1)]))]))])])]),
)


def prove_region(rom, regions, entry):
    """Confined descent from the region's own entries must fetch every byte, end terminal, and touch no DATA."""
    lo, hi = entry["start"], entry["end"]
    reached, notes = F.descend(rom, [e["offset"] for e in entry["entries"]], lo, hi)
    covered = set()
    for a, n in reached.items():
        covered.update(range(a, a + n))
    data = {b for r in regions if r["kind"] == "data" for b in range(r["start"], r["end"])}
    last = max(reached) if reached else None
    internal, exits = [], []
    for p in sorted(reached):
        d = F.decode(rom, p)
        if d.op in F.TRANSFER_OPS:
            a = F._addr_operand(d)
            t = F.resolve_target(p, a) if a is not None else None
            (internal if t is not None and lo <= t < hi else exits).append((p, t))
    return OrderedDict([
        ("name", entry["name"]), ("bounds", [lo, hi]),
        ("every_byte_reached", covered == set(range(lo, hi))),
        ("instructions", len(reached)),
        ("last_instruction_terminal", last is not None and F.is_terminal(F.decode(rom, last))),
        ("internal_targets_are_instruction_starts", all(t in reached for _, t in internal)),
        ("touches_recovered_data", bool(covered & data)),
        ("exits", [OrderedDict([("site", s), ("target", t)]) for s, t in exits]),
        ("unresolved_exits", [OrderedDict([("kind", k), ("offset", o)]) for k, o in notes if k in ("indirect", "invalid", "falls_off")])])


def verify_registered_regions(rom, regions, ctx, facts=None):
    """Every recovered region whose name starts with ``banked_`` must be a registered one with live evidence."""
    facts = facts or Facts.of(rom)
    by_name = {e["name"]: e for e in REGISTRY}
    for r in regions:
        if not r["name"].startswith(BANKED_PREFIX):
            continue
        e = by_name.get(r["name"])
        if e is None or (r["start"], r["end"], r["kind"]) != (e["start"], e["end"], "code"):
            raise ValueError("recovered region %s is not a registered DECOMP-1D banked region" % r["name"])
        for ent in e["entries"]:
            verify_seed(rom, regions, ent["offset"], ent["via"], ctx, facts)
        proof = prove_region(rom, regions, e)
        if not (proof["every_byte_reached"] and proof["last_instruction_terminal"]
                and proof["internal_targets_are_instruction_starts"] and not proof["touches_recovered_data"]):
            raise ValueError("recovered region %s does not prove out from its entries" % r["name"])
    return True


# --- evidence document --------------------------------------------------------------------------------
def build(rom, root=ROOT):
    import rom_ledger as RL      # late import: rom_ledger imports this module
    regions = json.loads((root / "asm" / "recovered" / "regions.json").read_text(encoding="utf-8"))
    facts = Facts.of(rom)
    baseline = RL.build_ledger(rom, root, reviewed=False)
    ctx = Context(baseline["claims"])
    interrupt = interrupt_cached(rom, facts)
    doc = OrderedDict()
    doc["format"] = 1
    doc["rom_sha256"] = RL.ROM_SHA256
    doc["generator"] = "tools/decomp1d_banked_flow.py"
    doc["evidence_tier"] = ("static ROM-derived control-flow evidence under the listed residual assumptions; "
                            "not an execution trace")
    doc["mapper_model"] = OrderedDict([
        ("registers", OrderedDict((hx(a), n) for a, n in MAPPER.items())),
        ("slot_2", OrderedDict([("cpu", [SLOT2_LO, SLOT2_HI]), ("register", hx(SLOT2_REGISTER)),
                                 ("file_offset", "bank * $4000 + (cpu - $8000)"), ("rom_banks", ROM_BANKS)])),
        ("setters", [mapper_setter(rom, 0x1C6F)]),
        ("slot1_register_stores", mapper_register_stores(rom)["$FFFE"]["sites"]),
        ("slot0_register_stores", mapper_register_stores(rom)["$FFFD"]["sites"]),
        ("control_register_stores", mapper_register_stores(rom)["$FFFC"]["sites"]),
        ("slot2_register_stores", mapper_register_stores(rom)["$FFFF"]["sites"])])
    doc["interrupt_model"] = interrupt
    doc["residual_assumptions"] = list(RESIDUAL_ASSUMPTIONS)
    all_calls = slot2_calls(rom, regions, facts)
    calls = OrderedDict((s, c) for s, c in all_calls.items() if s < F.RESIDENT_END)
    transfers = []
    for site, (op, target, in_recovered) in calls.items():
        if op == "CALL" and in_recovered:
            transfers.append(prove_banked_call(rom, regions, site, ctx, facts))
        else:
            rec = OrderedDict([("caller", site), ("status", "unresolved"), ("cpu_target", target),
                               ("reasons", ["caller_not_in_byte_verified_recovered_code" if not in_recovered
                                            else "not_a_call_instruction"])])
            _hint(rom, rec, site)
            transfers.append(rec)
    doc["banked_transfers"] = transfers
    doc["not_examined"] = OrderedDict([
        ("slot2_transfers_from_slot_2_code", len(all_calls) - len(calls)),
        ("reason", "code that itself executes in slot 2 cannot remap slot 2, so its slot-2 targets are same-bank and are "
                   "already resolved by the DECOMP-1A rule (rom_flow.resolve_target)")])
    by_cpu = OrderedDict()
    for t in transfers:
        row = OrderedDict([("caller", t["caller"]), ("status", t["status"])])
        if t["status"] == "supported":
            row["bank"], row["file_offset"] = t["destination"]["bank"], t["destination"]["file_offset"]
        elif "unproven_bank_hint" in t:
            row["unproven_bank_hint"] = t["unproven_bank_hint"]["bank"]
        by_cpu.setdefault(hx(t["cpu_target"]), []).append(row)
    banks_8000 = sorted({t["destination"]["bank"] for t in transfers if t["status"] == "supported" and t["cpu_target"] == 0x8000}
                        | {t["unproven_bank_hint"]["bank"] for t in transfers if t["cpu_target"] == 0x8000 and "unproven_bank_hint" in t})
    doc["ambiguity"] = OrderedDict([
        ("rule", "the CPU address never classifies anything: only a supported record names a file offset"),
        ("banks_seen_for_cpu_8000", banks_8000),
        ("note", "CALL $8000 reaches bank $1C from the gameplay frame update and bank $1D from the interrupt handler; "
                 "only the former is supported"),
        ("slot2_transfers_by_cpu_address", by_cpu)])
    dests = supported_entries(rom, regions, ctx, facts)
    doc["supported_entries"] = [OrderedDict([("file_offset", d), ("bank", r[0]["destination"]["bank"]),
                                            ("cpu", r[0]["cpu_target"]), ("callers", [x["caller"] for x in r])])
                                for d, r in sorted(dests.items())]
    closures = entry_closure(rom, regions, ctx, facts)
    tables = []
    for dest, closure in sorted(closures.items()):
        for t in find_tables(rom, closure):
            row = OrderedDict(t)
            row["entry"] = dest
            row["words_resolved"] = [OrderedDict([("index", i), ("cpu", rom[t["table"] + 2 * i] | rom[t["table"] + 2 * i + 1] << 8),
                                                  ("file_offset", table_word_target(rom, t["table"], i))])
                                     for i in range(t["words"])]
            row["next_word_after_table"] = rom[t["end"]] | rom[t["end"] + 1] << 8
            tables.append(row)
    doc["dispatch_tables"] = tables
    doc["registered_regions"] = [prove_region(rom, regions, e) for e in REGISTRY]
    doc["registered"] = [r["name"] for r in regions if r["name"].startswith(BANKED_PREFIX)]
    doc["findings"] = findings(rom, tables, baseline["claims"], facts)
    doc["ledger_effect"] = ledger_effect(rom, root, regions, RL)
    return doc


def findings(rom, tables, claims, facts):
    """Observations that need a reviewer's decision; nothing here changes a classification."""
    out = []
    for t in tables:
        over = [c for c in claims if c["primary"] == "CODE" and c["start"] < t["end"] and c["end"] > t["table"]
                and c["start"] <= t["table"] and "audit_manifests" in c.get("importers", ())]
        if over:
            out.append(OrderedDict([
                ("id", "F1"), ("kind", "table_inside_code_claim"),
                ("table", [t["table"], t["end"]]),
                ("claims", [OrderedDict([("start", c["start"]), ("end", c["end"]), ("names", c["names"]),
                                         ("sources", c["sources"])]) for c in over]),
                ("detail", "a hash-verified audit manifest claims this range as CODE although it contains the %d-word "
                           "dispatch table; the table is not registered as DATA because that would make the ledger "
                           "contradictory. Correct at the audit source (as DECOMP-1A did for object-50) after review."
                           % t["words"])]))
    skip = (0x5E0, 0x5F6)
    ins = {}
    for root in (VECTOR_RESET, VECTOR_IRQ, VECTOR_NMI):
        queue = deque([root])
        while queue:
            p = queue.popleft()
            if p in ins or not 0 <= p < F.RESIDENT_END:
                continue
            d = F.decode(rom, p)
            if F.is_invalid(d) or p + d.len > F.RESIDENT_END:
                continue
            ins[p] = d.len
            if d.op in F.TRANSFER_OPS and p not in skip:
                a = F._addr_operand(d)
                t = F.resolve_target(p, a) if a is not None else None
                if t is not None and t < F.RESIDENT_END:
                    queue.append(t)
            if not F.is_terminal(d):
                queue.append(p + d.len)
    only = sorted(set(facts.descent) - set(ins))
    out.append(OrderedDict([
        ("id", "F2"), ("kind", "decomp1b_vector_reachability_slot1_edges"),
        ("detail", "The IM 1 handler calls $4000 at $05E0 and $05F6 after mapping bank 2 into slot 1, so those calls enter "
                   "file $8000+, not the bank-1 code at file $4000 that DECOMP-1B's resident descent follows."),
        ("instructions_reached_only_through_these_edges", len(only)),
        ("bytes_reached_only_through_these_edges", sum(facts.descent[p] for p in only)),
        ("effect", "affects only the vector_reachability and dependency_map figures in data/decomp1b/callers.json; no ledger "
                   "claim depends on them (reviews and recovered regions rest on recovered code). Reported, not changed, so "
                   "the historical output still reproduces.")]))
    return out


EFFECT_KEYS = ("classified_bytes", "unknown_bytes", "recovered_bytes", "recovered_code_bytes",
               "independent_structural_bytes", "classified_by_recovery_only_bytes",
               "recovered_and_independently_classified_bytes", "contested_bytes")


def ledger_effect(rom, root, regions, RL):
    """Ledger totals with and without the DECOMP-1D regions (the evidence tools' own before/after)."""
    names = {r["name"] for r in regions if r["name"].startswith(BANKED_PREFIX)}
    before = RL.build_ledger(rom, root, drop_regions=names)
    after = RL.build_ledger(rom, root)
    rows = {(r["start"], r["end"], r["name"]): r for r in before["unclassified_range_claims"]["ranges"]}
    changed = []
    for r in after["unclassified_range_claims"]["ranges"]:
        b = rows[(r["start"], r["end"], r["name"])]
        if b["status"] != r["status"] or b["bytes_by_class"] != r["bytes_by_class"]:
            changed.append(OrderedDict([("start", r["start"]), ("end", r["end"]), ("name", r["name"]),
                                        ("before", OrderedDict([("status", b["status"]), ("bytes_by_class", b["bytes_by_class"])])),
                                        ("after", OrderedDict([("status", r["status"]), ("bytes_by_class", r["bytes_by_class"])]))]))
    return OrderedDict([
        ("note", "before = the same tree with the banked_ regions set aside; both include the committed reviewed-ranges.json"),
        ("before", OrderedDict((k, before["totals"][k]) for k in EFFECT_KEYS)),
        ("after", OrderedDict((k, after["totals"][k]) for k in EFFECT_KEYS)),
        ("by_category_before", before["totals"]["by_category"]), ("by_category_after", after["totals"]["by_category"]),
        ("recovered_regions", OrderedDict([("before", before["recovered_manifest"]["regions"]), ("after", after["recovered_manifest"]["regions"])])),
        ("contradictory_pairs", after["overlaps"]["stats"]["contradictory_pairs"]),
        ("audit_ranges_changed", changed)])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("rom", nargs="?")
    ap.add_argument("--output", default=str(OUTPUT))
    args = ap.parse_args(argv)
    import rom_ledger as RL
    doc = build(RL.load_rom(args.rom or RL.DEFAULT_ROM))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_bytes((json.dumps(doc, indent=1) + "\n").encode("utf-8"))
    sup = [t for t in doc["banked_transfers"] if t["status"] == "supported"]
    print("slot-2 transfers: %d, supported: %d, entries: %s, interrupt model supported: %s"
          % (len(doc["banked_transfers"]), len(sup), [hx(e["file_offset"]) for e in doc["supported_entries"]],
             doc["interrupt_model"]["supported"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

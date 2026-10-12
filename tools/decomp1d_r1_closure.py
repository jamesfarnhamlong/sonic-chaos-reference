#!/usr/bin/env python3
"""DECOMP-1D-R1: bounded proofs for the computed jumps in the IM 1 handler's banked callees.

    python tools/decomp1d_r1_closure.py /path/to/SonicChaos.sms [--output data/decomp1d/r1-interrupt-closure.json]

DECOMP-1D left assumption R1 open because three ``JP (HL)`` sites in the interrupt handler's banked callees have index
registers the code does not obviously bound. This module re-derives each site from the ROM and decides, per site, what
the code itself guarantees. It never infers a table's extent from neighbouring plausible-looking words.

The unit of proof is a *dominating chain*. Starting at the computed jump, walk backwards while every instruction has
exactly one known predecessor (fall-through or decoded transfer) and no 16-bit literal elsewhere in the ROM could name
it. Every execution that reaches the jump then passes through the whole chain. From the farthest chain instruction at
which the index register is still free (loaded from RAM or otherwise unknown), the chain is executed concretely, with
:mod:`z80_exec`, once for each of the 256 values of A:

* ``site``      the value reaches the jump; the destination (``HL``) and the table word that supplied it are exact;
* ``off_chain`` a known, taken branch leaves the chain, so the value does not reach the jump in this activation;
* ``undecided`` an instruction or condition on the chain cannot be evaluated exactly. Any undecided value makes the
                site unproven: the domain is never silently shrunk.

Index wrapping (``ADD A,A`` drops its carry), masks (``AND 3``), compare/branch guards and subtractions are therefore
modelled by execution, not by pattern matching. The result is the *code-defined domain*: exactly the register values
for which the jump can execute, and for each the exact destination.

What the code defines is not always what is safe. Every destination is checked (``descent_check``) and every table
word must lie in the table region delimited by the code itself (the words below the lowest valid target). A
destination that fails, or a word outside the table region, is *unsupported*. A dispatcher is **proven** only when its
code-defined domain contains no unsupported entry, or when an independent ROM-derived data proof removes the
unsupported values from the domain. Otherwise it is **partial**: the supported destinations are followed in the
*conditional* walk only, the official walk keeps an open edge, and nothing is promoted.

This is static control-flow evidence, not an execution trace. Residual assumptions (R2-R4 of DECOMP-1D, stack
discipline, and the discovered-code universe) are listed in the evidence and are not discharged here.
"""
import argparse
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1d_banked_flow as D  # noqa: E402
import rom_flow as F  # noqa: E402
import z80_exec as X  # noqa: E402
from z80dis import z80  # noqa: E402

OP = F.OP
BANK = 0x4000
OUTPUT = ROOT / "data" / "decomp1d" / "r1-interrupt-closure.json"
SHADOW = 0xD12B
SLOT1_SHADOW = 0xD12A
MAPPER_REGISTERS = (0xFFFC, 0xFFFD, 0xFFFE, 0xFFFF)
IRQ_ROOT = (0x0038, 1, "U")          # R3: slot 1 is bank 1 when the handler starts
MAX_ROUNDS = 24

hx = D.hx


def slot_of(cpu):
    return cpu >> 14


def window_base(cpu):
    return cpu & 0xC000


# --- the discovered-code universe ----------------------------------------------------------------------
class Universe:
    """Decoded instructions (with the CPU addresses they execute at) and the edges between them."""

    VECTORS = (0x0000, 0x0038, 0x0066)         # hardware vectors (file offset = CPU address)

    def __init__(self, rom, contexts, ctx=None, entries=()):
        self.rom, self.ctx = rom, ctx
        self.entries = frozenset(e for e in entries if e is not None) | frozenset(self.VECTORS)   # file offsets entered from outside
        self.cpus = {}                       # file offset -> set of CPU addresses
        self.ins = {}                        # file offset -> length
        self.by_target = {}                  # CPU target -> [(file, cpu, op name)]
        self.fall_in = {}                    # file offset of the next instruction -> [(file, cpu)]
        self.computed = []                   # (file, cpu) of every JP (HL)/(IX)/(IY) seen
        for f, cpus in contexts.items():
            for cpu in cpus:
                d = z80.decode(bytes(rom[f:f + 4]), cpu)
                if F.is_invalid(d):
                    continue
                self.cpus.setdefault(f, set()).add(cpu)
                self.ins[f] = d.len
                if d.op in F.TRANSFER_OPS:
                    t = F._addr_operand(d)
                    if t is not None:
                        self.by_target.setdefault(t, []).append((f, cpu, d.op.name))
                    elif d.op == OP.JP:
                        self.computed.append((f, cpu))
                if not F.is_terminal(d):
                    self.fall_in.setdefault(f + d.len, []).append((f, cpu))
        self.starts = sorted(self.ins)

    def preds(self, f, cpu):
        """Known predecessors of the instruction at (file ``f``, CPU ``cpu``), banks respected for same-slot banked code."""
        out = {}
        for pf, pcpu in self.fall_in.get(f, ()):
            if pcpu + self.ins[pf] == cpu:
                out[pf] = (pf, pcpu, "fallthrough")
        for pf, pcpu, op in self.by_target.get(cpu, ()):
            if slot_of(pcpu) == slot_of(cpu) and slot_of(cpu) in (1, 2) and pf // BANK != f // BANK:
                continue                     # a banked site in the same slot branches inside its own bank
            out.setdefault(pf, (pf, pcpu, op))
        if f in self.entries:
            out[-1] = (-1, cpu, "entry")     # a hardware vector or walk root: entered from outside the discovered code
        return sorted(out.values())

    OPERAND_OPCODES = frozenset([0x01, 0x11, 0x21, 0x31, 0x22, 0x2A, 0x32, 0x3A, 0xC3, 0xCD]
                                + [0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA]
                                + [0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC])
    ED_OPERAND = frozenset([0x43, 0x4B, 0x53, 0x5B, 0x63, 0x6B, 0x73, 0x7B])
    INDEX_OPERAND = frozenset([0x21, 0x22, 0x2A])

    def operand_position(self, off):
        """True when a 16-bit literal at ``off`` sits where an instruction's nn operand would be."""
        r = self.rom
        if off >= 1 and r[off - 1] in self.OPERAND_OPCODES:
            return True
        if off >= 2 and r[off - 2] == 0xED and r[off - 1] in self.ED_OPERAND:
            return True
        return off >= 2 and r[off - 2] in (0xDD, 0xFD) and r[off - 1] in self.INDEX_OPERAND

    def literals(self, f, cpu):
        """16-bit literals equal to ``cpu`` that could be an instruction operand, as (decoded, unclassified).

        * a decoded transfer operand is a real edge and is counted in ``preds``;
        * bytes the ledger classifies as non-code are inert;
        * a word that is not in an nn-operand position cannot be named by an instruction (table words are covered by the
          proofs of the computed jumps that read them);
        * ``decoded`` literals (``LD HL,nn`` and similar in discovered code) materialise the address and break a chain;
        * ``unclassified`` literals sit in operand position inside bytes no evidence classifies as data or code. They
          cannot be shown inert; they are recorded as a caveat (residual assumption R5) and do not break a chain."""
        decoded, unclassified = [], []
        for off in D.word_hits(self.rom, cpu):
            row = D.classify_word_hit(self.rom, off, cpu, self.starts, self.ins, self.ctx or D.Context(None))
            if row["class"] == "literal_operand":
                # the literal must be the instruction's trailing nn operand, not an opcode/operand byte coincidence
                n = self.ins[row["instruction"]]
                if n >= 3 and row["instruction"] + n == off + 2:
                    decoded.append(row)
            elif row["class"] == "unexplained" and self.operand_position(off):
                unclassified.append(row)
        return decoded, unclassified

    def region(self, f, cpu, budget=72):
        """Backward predecessor closure of an instruction, breadth-first, up to ``budget`` instructions.

        Returns (nodes, preds): ``preds[node]`` is (known predecessors, decoded literals naming the node)."""
        key = (f, cpu)
        nodes, order, preds = {key}, [key], {}
        i = 0
        while i < len(order):
            n = order[i]
            i += 1
            pr = self.preds(*n)
            decoded, unclassified = self.literals(*n)
            preds[n] = (pr, decoded, unclassified)
            for pf, pcpu, _ in pr:
                k = (pf, pcpu)
                if pf >= 0 and k not in nodes and len(nodes) < budget:      # pf = -1 marks an entry from outside the code
                    nodes.add(k)
                    order.append(k)
        return nodes, preds


def contexts_from(rom, regions, *walks):
    """{file offset: {cpu}} from recovered code and any number of walker results."""
    ctxs = {}
    for r in F.code_regions(regions):
        for p, _, _ in F.region_instructions(rom, r):
            ctxs.setdefault(p, set()).add(F.cpu_address(p))
    for w in walks:
        for f, cpus in w["cpu_at"].items():
            ctxs.setdefault(f, set()).update(cpus)
    return ctxs


# --- destination checks ----------------------------------------------------------------------------------
def _mapped(cpu, s1, s2):
    return D._mapped(cpu, s1, s2)


def descent_check(rom, s1, s2, entry, cap=6000):
    """Confined descent from ``entry`` (CPU address): the destination is *not code* when it hits an undecodable byte,
    transfers into RAM/mapper space, or runs past its 16 KiB window. Passing this check proves nothing by itself."""
    base = window_base(entry)
    seen, stack, problems, externals = set(), [entry], [], set()
    steps = 0
    while stack:
        cpu = stack.pop()
        while True:
            if cpu in seen:
                break
            seen.add(cpu)
            f = _mapped(cpu, s1, s2)
            if f is None or cpu >= 0xC000:
                problems.append(("unmapped", cpu))
                break
            d = z80.decode(bytes(rom[f:f + 4]), cpu)
            if F.is_invalid(d):
                problems.append(("invalid", cpu))
                break
            steps += 1
            if steps > cap:
                problems.append(("cap", cpu))
                break
            if d.op in F.TRANSFER_OPS:
                t = F._addr_operand(d)
                if t is None:
                    externals.add(("computed", cpu))
                elif t >= 0xC000:
                    problems.append(("ram_target", cpu, t))
                elif window_base(t) == base:
                    stack.append(t)
                else:
                    externals.add(("leaves_window", t))
            if F.is_terminal(d):
                break
            cpu += d.len
            if window_base(cpu) != base:
                problems.append(("falls_off_window", cpu))
                break
    return OrderedDict([("ok", not problems), ("instructions", steps), ("problems", problems[:6]),
                        ("problem_count", len(problems))])


def ledger_class(ctx, f):
    """Non-code class of file offset ``f`` from the ledger's independent claims or evidence added to the context."""
    if ctx is None:
        return None
    hit = next((c for lo, hi, c in ctx.non_code if lo <= f < hi), None)
    return hit


def with_data(ctx, intervals, label):
    """A copy of ``ctx`` that also classifies ``intervals`` (half-open file ranges) as non-code ``label``."""
    out = D.Context(None)
    out.available = True if ctx is None else ctx.available
    out.non_code = sorted(list(ctx.non_code if ctx is not None else []) + [(lo, hi, label) for lo, hi in intervals])
    out.code = list(ctx.code) if ctx is not None else []
    return out


# --- the dispatch proof --------------------------------------------------------------------------------
def _ranges(values):
    out, vals = [], sorted(values)
    for v in vals:
        if out and out[-1][1] == v - 1:
            out[-1][1] = v
        else:
            out.append([v, v])
    return [hx2(a) if a == b else "%s-%s" % (hx2(a), hx2(b)) for a, b in out]


def hx2(v):
    return "$%02X" % v


def _word_pair(m, hl):
    """The last two consecutive ROM reads whose little-endian word equals ``hl`` (the table word fetch)."""
    reads = m.rom_reads
    for i in range(len(reads) - 1, 0, -1):
        (c0, f0), (c1, f1) = reads[i - 1], reads[i]
        if c1 == c0 + 1 and f1 == f0 + 1 and (m.rom[f0] | m.rom[f1] << 8) == hl:
            return c0, f0
    return None


def _decide(rom, m1, m2, start, site_cpu, allowed, cache=None):
    """Run ``start`` for all 256 values of A. Returns (runs, mode) when every value is decided, else (None, reason)."""
    reason = None
    for free in (False, True):
        runs, bad = {}, None
        for a0 in range(256):
            r = X.run(rom, m1, m2, start, site_cpu, a0, chain=allowed, free=free, cache=cache)
            if r.outcome in ("unmodelled", "returned") or (r.outcome == "site" and r.hl is None):
                bad = r.detail or "destination register unknown at the site"
                break
            runs[a0] = r
        if bad is None:
            return runs, ("free" if free else "start")
        reason = bad
    return None, reason


BUDGETS = (16, 24, 32, 40, 48)


def prove_dispatch(rom, site_file, uni, s1, s2, data_domain=None, ctx=None, budgets=BUDGETS):
    """Prove ``site_file`` at several region sizes and keep the tightest decided result.

    Every decided result is sound; a larger region reaches farther back (more guards) but can hit loops that cannot be
    decided. The kept record has the fewest distinct destinations, then the fewest table words, then the largest
    region; ``region_budget`` names it. If no size decides, the last failure is returned."""
    best = last = None
    for b in budgets:
        p = _prove(rom, site_file, uni, s1, s2, data_domain, ctx, b)
        last = p
        if "domain" not in p:
            continue                                  # not decided at this size
        entries = p.get("table", {}).get("entries", [])
        # an "unreachable" result is accepted only when no size gives destinations (it is the least conservative)
        key = (p["status"] == "unreachable", len({r["target_cpu"] for r in entries}),
               p.get("table", {}).get("words_read", 0), -b)
        if best is None or key <= best[0]:
            best = (key, p)
    return last if best is None else best[1]


def _prove(rom, site_file, uni, s1, s2, data_domain, ctx, budget):
    cpus = sorted(uni.cpus.get(site_file, ()))
    rec = OrderedDict([("site", site_file), ("status", "unproven"), ("reasons", [])])
    if len(cpus) != 1:
        rec["reasons"].append("site_cpu_context_ambiguous" if cpus else "site_not_in_discovered_code")
        return rec
    cpu = cpus[0]
    d = z80.decode(bytes(rom[site_file:site_file + 4]), cpu)
    if not (d.op == OP.JP and len(d.operands) == 1 and d.operands[0][0].name == "REG_DEREF"
            and d.operands[0][1].name == "HL"):
        rec["reasons"].append("not_jp_hl")
        return rec
    rec.update([("cpu", cpu), ("bank", site_file // BANK), ("slot", slot_of(cpu)), ("region_budget", budget)])
    site = (site_file, cpu)
    if slot_of(cpu) == 1:
        m1, m2 = site_file // BANK, s2_default(s2)
    elif slot_of(cpu) == 2:
        m1, m2 = s1, site_file // BANK
    else:
        m1, m2 = s1, s2_default(s2)
    nodes, preds = uni.region(site_file, cpu, budget)
    if len(nodes) < 2:
        rec["reasons"].append("no_known_predecessor")
        return rec
    # starts: nodes some of whose predecessors are outside the region (or that a decoded literal names, or that nobody
    # branches to); every other node's predecessors are all inside, so entry is only through a start.
    def pred_keys(n):
        return {(pf, pc) for pf, pc, _ in preds[n][0]}

    starts = {n for n in nodes if n != site and (not pred_keys(n) <= nodes or not preds[n][0] or preds[n][1])}
    succ = {n: set() for n in nodes}
    for n in nodes:
        for p in pred_keys(n):
            if p in nodes:
                succ[p].add(n)
    decided, failures, cache, discarded = {}, {}, {}, set()
    for _ in range(400):
        # region reachable forward from the starts; any node with an outside predecessor becomes a start
        region, stack = set(starts), list(starts)
        while stack:
            n = stack.pop()
            for t in succ[n]:
                if t not in region and t not in discarded:        # an edge into a replaced start leaves the region
                    region.add(t)
                    stack.append(t)
        extra = {n for n in region if n != site and n not in starts and not pred_keys(n) <= region}
        if extra:
            starts |= extra
            continue
        allowed = {c for _, c in region}
        pending = [n for n in sorted(starts) if n not in decided]
        if not pending:
            break
        n = pending[0]
        runs, how = _decide(rom, m1, m2, n[1], cpu, allowed, cache)
        if runs is not None:
            decided[n] = (runs, how)
            continue
        failures[n] = how
        discarded.add(n)
        starts.discard(n)
        # the undecidable start is replaced by the nodes that follow it; one already replaced (a loop back to it) is not
        # re-added, because everything that leaves it is covered by its own replacements
        forward = {t for t in succ[n] if t not in discarded}
        if site in forward or not (forward or starts):
            rec["reasons"].append("domain_not_decidable")
            rec["undecided_detail"] = how
            return rec
        starts |= forward
        # nodes only reachable through the discarded start leave the region on the next pass
        decided = {k: v for k, v in decided.items() if k in starts}
    else:
        rec["reasons"].append("domain_not_decidable")
        rec["undecided_detail"] = "collapse did not converge"
        return rec
    if not decided:
        rec["reasons"].append("no_entry_into_the_region")
        rec["undecided_detail"] = "no instruction of the region has a known way in, so nothing is decided"
        return rec

    def free_events(n):
        runs, how = decided[n]
        if how != "free":
            return []
        events = {r.machine.free_at for r in runs.values() if r.outcome == "site"}
        return [OrderedDict([("cpu", c), ("asm", D.asm(rom, _mapped(c, m1, m2)))]) for c in sorted(e for e in events if e is not None)]

    rec["starts"] = [OrderedDict([("file", n[0]), ("cpu", n[1]), ("asm", D.asm(rom, n[0])),
                                  ("mode", "A holds the enumerated value at the start" if decided[n][1] == "start"
                                   else "the first load of an unknown byte into A takes the enumerated value"),
                                  ("unknown_load", free_events(n))]) for n in sorted(decided)]
    rec["entry_integrity"] = OrderedDict([
        ("rule", "every region instruction that is not a start has all its known predecessors inside the region; "
                 "starts are entered with arbitrary register state"),
        ("region_instructions", len(region)),
        ("collapsed_starts", [OrderedDict([("file", n[0]), ("cpu", n[1]), ("reason", failures[n])]) for n in sorted(failures)]),
        ("unclassified_operand_literals", sorted({r["offset"] for n in region for r in preds[n][2]})),
        ("scanned", "decoded instructions of the explored closure, recovered code and the reset/IM 1/NMI walk")])
    rec["region"] = [OrderedDict([("file", n[0]), ("cpu", n[1]), ("asm", D.asm(rom, n[0])),
                                  ("start", n in starts),
                                  ("predecessors", [OrderedDict([("file", p), ("cpu", pc), ("how", how)])
                                                    for p, pc, how in preds[n][0]])])
                     for n in sorted(region, key=lambda k: k[1])]
    # code-defined domain: union over the starts
    entries = OrderedDict()
    stack_values = set()
    reaching, leaving = set(), 0
    for n, (runs, how) in decided.items():
        for a0, r in runs.items():
            if r.outcome == "site":
                reaching.add(a0)
                wp = _word_pair(r.machine, r.hl)
                entries.setdefault((wp[0] if wp else None, r.hl), set()).add(a0)
                for v, origin in r.machine.stack:
                    if origin == "push" and isinstance(v, int):
                        stack_values.add(v)
            else:
                leaving += 1
    rec["domain"] = OrderedDict([("register", "A at the starts"), ("values", sorted(reaching)),
                                 ("ranges", _ranges(reaching)), ("count", len(reaching)),
                                 ("start_runs_leaving_region", leaving), ("undecided", 0)])
    if not entries:
        rec["status"] = "unreachable"
        rec["reasons"] = []
        rec["supported_targets"] = []
        return rec
    if any(wp is None for wp, _ in entries):
        rec["reasons"].append("destination_not_a_rom_table_word")
        return rec
    rec["pushed_continuations"] = sorted(stack_values)
    base = min(w for w, _ in entries)
    rows, valid_targets = [], []
    for (w, t), vals in sorted(entries.items()):
        tf = _mapped(t, m1, m2)
        chk = descent_check(rom, m1, m2, t) if tf is not None else OrderedDict([("ok", False), ("problems", [("unmapped", t)])])
        lc = ledger_class(ctx, tf) if tf is not None else None
        ok = bool(chk["ok"]) and lc is None
        rows.append(OrderedDict([("word_cpu", w), ("word_file", _mapped(w, m1, m2)), ("target_cpu", t),
                                 ("target_file", tf), ("values", _ranges(vals)), ("descent_ok", chk["ok"]),
                                 ("descent_problems", chk["problems"][:3]), ("ledger_non_code", lc),
                                 ("valid", ok)]))
        rows[-1]["_vals"] = vals
        if ok and window_base(t) == window_base(w):
            valid_targets.append(t)
    table_end = min([t for t in valid_targets if t >= base], default=None)
    loads = {e["asm"] for st in rec["starts"] for e in st["unknown_load"]}
    if not all(st["unknown_load"] for st in rec["starts"]):
        loads = set()                 # a start that is not an unknown load has no data meaning
    for row in rows:
        w = row["word_cpu"]
        row["in_table_region"] = base <= w and (table_end is None or w < table_end)
        row["supported"] = bool(row["valid"] and row["in_table_region"])
    if data_domain is not None and loads and loads <= set(data_domain.get("applies_to_unknown_loads", ())):
        for row in rows:
            row["in_data_domain"] = bool(row["_vals"] & set(data_domain["values"]))
    rec["table"] = OrderedDict([
        ("base", base), ("words_read", len(rows)), ("footprint_end", max(w for w, _ in entries) + 2),
        ("region_end", table_end),
        ("region_rule", "words below the lowest valid destination; a destination can never lie inside its own table"),
        ("entries", [OrderedDict((k, v) for k, v in row.items() if k != "_vals") for row in rows])])
    unsupported_values = sorted({v for row in rows if not row["supported"] for v in row["_vals"]})
    supported_values = sorted({v for row in rows if row["supported"] for v in row["_vals"]})
    rec["code_domain"] = OrderedDict([("supported_values", _ranges(supported_values)),
                                      ("unsupported_values", _ranges(unsupported_values))])
    effective_unsupported = unsupported_values
    if data_domain is not None and loads and loads <= set(data_domain.get("applies_to_unknown_loads", ())):
        rec["data_domain"] = OrderedDict([("values", _ranges(sorted(data_domain["values"]))),
                                          ("evidence", data_domain["evidence"])])
        effective_unsupported = [v for v in unsupported_values if v in data_domain["values"]]
    elif data_domain is not None:
        rec["data_domain_ignored"] = "the proof's unknown loads %s are not the ones the data proof covers" % sorted(loads)
    rec["unsupported_in_effective_domain"] = _ranges(effective_unsupported)
    sup_targets = sorted({row["target_cpu"] for row in rows if row["supported"]})
    rec["supported_targets"] = sup_targets
    if not effective_unsupported:
        rec["status"] = "proven"
        rec["reasons"] = []
    else:
        rec["status"] = "partial" if sup_targets else "unproven"
        rec["reasons"].append("domain_contains_unsupported_entries" if sup_targets else "no_supported_destination")
    return rec


def s2_default(s2):
    return s2 if isinstance(s2, int) else 3


def dispatch_spec(proof, include_partial):
    """The walker's view of a proof: the destinations to follow and whether they are all of them. A jump proven never to
    execute has an empty, complete set; a partial one is followed only in the conditional walk and stays an open edge."""
    if proof["status"] in ("proven", "unreachable") or (include_partial and proof["status"] == "partial"):
        targets = sorted(set(proof["supported_targets"]) | set(proof.get("pushed_continuations", ())))
        return {"targets": targets, "complete": proof["status"] in ("proven", "unreachable")}
    return None


# --- fixed point: resolve every computed jump the walk meets --------------------------------------------
def resolve(rom, regions, facts, ctx, shadow, include_partial, data_domains=None, rounds=MAX_ROUNDS, roots=(IRQ_ROOT,)):
    """Iterate walk -> prove every open computed jump -> re-walk with the resolved sets until nothing changes.

    ``include_partial`` selects the *conditional* walk (supported entries of partially proven dispatchers are followed
    but the jump stays an open edge); without it only fully proven dispatchers are followed (the *official* walk).
    Returns (walk, dispatch, proofs, universe)."""
    data_domains = data_domains or {}
    dispatch, proofs = {}, {}
    walk = uni = None
    for _ in range(rounds):
        walk = D.state_walk(rom, list(roots), shadow, dispatch=dispatch)
        uni = Universe(rom, contexts_from(rom, regions, facts.walk, walk), ctx, entries={D._mapped(r[0], r[1], r[2]) for r in roots})
        sites = set(dispatch) | {e[1] for e in walk["open_edges"] if e[0] in ("indirect_jump", "partial_dispatch")}
        new_proofs, new_dispatch = {}, {}
        for site in sorted(sites):
            p = prove_dispatch(rom, site, uni, 1, 3, ctx=ctx, data_domain=data_domains.get(site))
            new_proofs[site] = p
            spec = dispatch_spec(p, include_partial)
            if spec is not None:
                new_dispatch[site] = spec
        if new_dispatch == dispatch and set(new_proofs) == set(proofs):
            proofs = new_proofs
            break
        dispatch, proofs = new_dispatch, new_proofs
    else:
        raise RuntimeError("computed-jump resolution did not reach a fixed point")
    return walk, dispatch, proofs, uni


# --- memory-write audit of a walk -------------------------------------------------------------------------
def norm_ram(addr):
    """Physical RAM cell: $E000-$FFFF mirrors $C000-$DFFF."""
    return 0xC000 + (addr & 0x1FFF) if addr >= 0xC000 else addr


PROTECTED_RAM = (SLOT1_SHADOW, SHADOW)
PROTECTED_NORM = frozenset(norm_ram(a) for a in PROTECTED_RAM)
ROTATES = (OP.RLC, OP.RRC, OP.RL, OP.RR, OP.SLA, OP.SRA, OP.SLL, OP.SRL, OP.SET, OP.RES, OP.INC, OP.DEC)
WIDE_SOURCES = ("HL", "BC", "DE", "SP", "IX", "IY")


def memory_writes(d):
    """[(form, address, width)] for the memory writes of one decoded instruction (stack pushes are not listed).

    forms: ``abs`` (known address), ``hl``/``de``/``bc`` (register-addressed), ``ix``/``iy`` (address = base + address)
    where ``address`` is the displacement, ``block_de``/``block_hl`` (block moves and block input)."""
    op, ops = d.op, d.operands
    out = []

    def target(operand, width=1):
        k = operand[0].name
        if k == "ADDR_DEREF":
            out.append(("abs", operand[1], width))
        elif k == "REG_DEREF" and operand[1].name in ("HL", "DE", "BC"):
            out.append((operand[1].name.lower(), None, width))
        elif k == "MEM_DISPL_IX":
            out.append(("ix", operand[1], width))
        elif k == "MEM_DISPL_IY":
            out.append(("iy", operand[1], width))

    if op == OP.LD and len(ops) == 2:
        src = ops[1]
        wide = src[0].name == "REG" and src[1].name in WIDE_SOURCES
        target(ops[0], 2 if wide else 1)
    elif op in ROTATES and ops:
        target(ops[-1])
    elif op in (OP.RLD, OP.RRD):
        out.append(("hl", None, 1))
    elif op in (OP.LDI, OP.LDIR, OP.LDD, OP.LDDR):
        out.append(("block_de", None, 1))
    elif op in (OP.INI, OP.INIR, OP.IND, OP.INDR):
        out.append(("block_hl", None, 1))
    return out


def hits_protected(addr, width):
    cells = {norm_ram(addr + k) for k in range(width)}
    raw = {addr + k for k in range(width)}
    return bool(cells & PROTECTED_NORM), bool(raw & set(MAPPER_REGISTERS))


def write_audit(rom, walk):
    """Every memory write in the instructions a walk visited, classified by what can be said about its address."""
    absolute, hits_shadow, hits_mapper = [], [], []
    rst = []
    forms = {}
    ix_loads = {"ix": set(), "iy": set()}
    ix_other = {"ix": [], "iy": []}
    for f in sorted(walk["visited"]):
        cpus = sorted(walk["cpu_at"].get(f, ())) or [F.cpu_address(f)]
        d = z80.decode(bytes(rom[f:f + 4]), cpus[0])
        if d.op == OP.RST:
            rst.append(f)
        for reg in ("IX", "IY"):
            r = reg.lower()
            if d.op == OP.LD and d.operands and d.operands[0][0].name == "REG" and d.operands[0][1].name == reg:
                if d.operands[1][0].name == "IMM":
                    ix_loads[r].add(d.operands[1][1])
                else:
                    ix_other[r].append(f)
            elif d.op in (OP.POP, OP.INC, OP.DEC, OP.ADD, OP.EX) and any(
                    o[0].name == "REG" and o[1].name == reg for o in d.operands[:1]):
                ix_other[r].append(f)
        for form, addr, width in memory_writes(d):
            forms.setdefault(form, []).append(f)
            if form == "abs":
                sh, mp = hits_protected(addr, width)
                absolute.append((f, addr, width))
                if sh:
                    hits_shadow.append((f, addr, width))
                if mp:
                    hits_mapper.append((f, addr, width))
    footprints = {}
    for r in ("ix", "iy"):
        offs = forms.get(r, [])
        if not offs:
            continue
        bases = sorted(ix_loads[r])
        reaches = []
        for f in offs:
            d = z80.decode(bytes(rom[f:f + 4]), (sorted(walk["cpu_at"].get(f, ())) or [F.cpu_address(f)])[0])
            for form, disp, width in memory_writes(d):
                if form == r:
                    for b in bases:
                        for k in range(width):
                            reaches.append((b + disp + k) & 0xFFFF)
        footprints[r] = OrderedDict([
            ("stores", len(offs)), ("immediate_bases", bases), ("other_writers", sorted(ix_other[r])),
            ("footprint", [min(reaches), max(reaches)] if reaches else None),
            ("reaches_protected", any(hits_protected(a, 1)[0] or hits_protected(a, 1)[1] for a in reaches)),
            ("bounded", not ix_other[r] and bool(bases))])
    return OrderedDict([
        ("instructions", len(walk["visited"])),
        ("absolute_stores", len(absolute)),
        ("absolute_store_hits_shadow", [OrderedDict([("offset", f), ("address", a), ("width", w)]) for f, a, w in hits_shadow]),
        ("absolute_store_hits_mapper_register", sorted({(f, a) for f, a, _ in hits_mapper})),
        ("mapper_register_store_sites", sorted({f for f, a, w in absolute if any(m in range(a, a + w) for m in MAPPER_REGISTERS)})),
        ("rst_instructions", rst),
        ("register_addressed", OrderedDict((k, len(v)) for k, v in sorted(forms.items()) if k != "abs")),
        ("register_addressed_sites", OrderedDict((k, sorted(set(v))) for k, v in sorted(forms.items())
                                                 if k not in ("abs",))),
        ("index_register_footprints", footprints)])


# --- sequence integrity over the expanded closure --------------------------------------------------------
CALLERS = (0x16E7, 0x1737)


def expanded_sequence_check(rom, regions, facts, ctx, walk):
    """DECOMP-1D's entry-into-the-sequence check repeated over the instructions the resolved dispatchers add."""
    instrs = D.all_decoded(rom, regions, facts)
    instrs.update(walk["visited"])
    sites = D.target_index(rom, regions, facts)
    for tf, rows in walk["targets"].items():
        if tf < F.RESIDENT_END:
            sites.setdefault(tf, [])
            sites[tf] = sorted(set(sites[tf]) | set(rows))
    out, clean = [], True
    for caller in CALLERS:
        interior = [caller - 3, caller]
        blockers, benign = D.sequence_blockers(rom, interior, instrs, ctx, sites)
        clean = clean and not blockers
        out.append(OrderedDict([("caller", caller), ("interior", interior), ("entries_into_sequence", blockers),
                                ("inert_literals", len(benign))]))
    return OrderedDict([("instructions_considered", len(instrs)), ("callers", out), ("clean", clean)])


def mirror_alias_scan(rom):
    """Absolute stores whose address aliases the shadow through the $E000-$FFFF RAM mirror."""
    out = OrderedDict()
    for name, addr in (("shadow", SHADOW), ("slot1_shadow", SLOT1_SHADOW)):
        sites = []
        for a in (addr, addr + 0x2000):
            sites += [(o, k, a) for o, k in D.store_pattern_sites(rom, a, 1)]
            sites += [(o, k, a) for o, k in D.store_pattern_sites(rom, a, 2) if k != "LD (nn),A"]   # 16-bit stores at a-1 and a
        out[name] = OrderedDict([("address", addr), ("mirror", addr + 0x2000),
                                 ("store_encodings", [OrderedDict([("offset", o), ("form", k), ("address", a)])
                                                      for o, k, a in sorted(set(sites))]),
                                 ("outside_resident_engine", sorted({o for o, k, a in sites if o >= F.RESIDENT_END}))])
    return out


# --- evidence document -----------------------------------------------------------------------------------
TASK_SITES = (0x086E8, 0x08137, 0x74027)
BASE_COMMIT = "eec2a0d7602fd56eb0aee641bf85a0413d47cf5a"

RESIDUAL = (
    OrderedDict([("id", "R1"), ("text",
        "Interrupt preservation of the slot-2 mapper register and its shadow $D12B across the handler's banked callees. "
        "See verdict for the state after DECOMP-1D-R1.")]),
    OrderedDict([("id", "R2"), ("status", "OPEN"), ("text",
        "Register-addressed stores ((HL), (DE), (BC), (IX+d), (IY+d), block moves) that could alias $FFFC-$FFFF or the "
        "shadow or its RAM mirror are not modelled. Absolute stores are, in every encoding, including the mirror; "
        "register-addressed stores are only counted and classified.")]),
    OrderedDict([("id", "R3"), ("status", "OPEN"), ("text",
        "Slot 1 is bank 1 whenever the IM 1 handler starts (unchanged from DECOMP-1D). The dispatchers resolved here "
        "assume the handler's own mappings (slot 1 = bank 2, slot 2 = bank 3 for the sound driver; slot 2 = bank $1D for "
        "the routine at $8000).")]),
    OrderedDict([("id", "R4"), ("status", "OPEN"), ("text",
        "Standard Sega mapper semantics, corroborated only by the ROM's own register use; no emulator or hardware trace.")]),
    OrderedDict([("id", "R5"), ("status", "NEW"), ("text",
        "The instruction universe is the code discovered by the reset/IM 1/NMI walk, the recovered regions and the "
        "resolved dispatchers. Entry-integrity proofs hold against that universe; operand-position 16-bit literals in "
        "bytes no evidence classifies are listed per proof and are not shown inert.")]),
    OrderedDict([("id", "S1"), ("status", "NEW"), ("text",
        "Stack discipline: RET is treated as returning to the caller. Handlers that deliberately unwind (POP HL / POP HL / "
        "RET) return to a caller the walk also reaches; the walk does not model stack contents.")]),
)


def _site_summary(rom, p):
    out = OrderedDict([("site", p["site"]), ("cpu", p.get("cpu")), ("bank", p.get("bank")), ("status", p["status"]),
                       ("reasons", p["reasons"])])
    for k in ("region_budget", "starts", "domain", "code_domain", "data_domain", "unsupported_in_effective_domain",
              "supported_targets", "pushed_continuations", "table", "entry_integrity", "region", "undecided_detail"):
        if k in p:
            out[k] = p[k]
    return out


def walk_stats(rom, walk, audit):
    vis = walk["visited"]
    resident = sum(1 for f in vis if f < F.RESIDENT_END)
    return OrderedDict([
        ("instructions", len(vis)), ("resident_instructions", resident), ("banked_instructions", len(vis) - resident),
        ("undecodable", [list(e) for e in walk["invalid"]]),
        ("open_edges", [[e[0]] + list(e[1:]) for e in walk["open_edges"]]),
        ("restart_edges", walk["restart"]),
        ("shadow_stores_by_absolute_address", sorted({f for f, a in walk["stores"] if a in (SHADOW, SLOT1_SHADOW)})),
        ("write_audit", audit)])


def derive_verdict(official_walk, official_audit, cond_walk, cond_audit, cond_proofs, off_proofs):
    inventory = OrderedDict((hx(s), p["status"]) for s, p in sorted(cond_proofs.items()))
    n_sup = sum(1 for p in cond_proofs.values() if p["status"] in ("proven", "unreachable"))
    n_partial = sum(1 for p in cond_proofs.values() if p["status"] == "partial")
    n_bad = sum(1 for p in cond_proofs.values() if p["status"] == "unproven")
    shadow_hit = bool(cond_audit["absolute_store_hits_shadow"]) or bool(cond_walk["stores"] and any(
        a == SHADOW for _, a in cond_walk["stores"]))
    undecodable = bool(cond_walk["invalid"])
    rst = bool(cond_audit.get("rst_instructions")) or bool(official_audit.get("rst_instructions"))
    official_open = bool(official_walk["open_edges"]) or bool(official_audit.get("rst_instructions"))
    reasons = []
    if shadow_hit:
        state = "OPEN"
        reasons.append("an absolute store to the shadow or its mirror exists in the followed closure")
    elif undecodable:
        state = "OPEN"
        reasons.append("an undecodable byte is reachable in the followed closure")
    elif rst and not (n_sup or n_partial):
        state = "OPEN"
        reasons.append("a restart instruction in the followed closure is not modelled")
    elif not official_open and n_partial == 0 and n_bad == 0:
        state = "CLOSED"
    elif n_sup or n_partial:
        state = "PARTIALLY CLOSED"
    else:
        state = "OPEN"
    return OrderedDict([
        ("r1", state), ("computed_jump_sites", inventory),
        ("proven_or_unreachable", n_sup), ("partial", n_partial), ("unproven", n_bad),
        ("official_walk_open_edges", len(official_walk["open_edges"])),
        ("conditional_walk_open_edges", len(cond_walk["open_edges"])),
        ("shadow_store_in_followed_closure", shadow_hit), ("undecodable_in_followed_closure", undecodable),
        ("restart_instructions_in_followed_closure", rst),
        ("reasons", reasons)])


LEMMAS = {
    0x08137: [
        "ZONE/ACT: whenever $18A0 runs, 3*$D297+$D298 <= 38 (otherwise the music-table read at $18B2 continues into code "
        "bytes from $18E1, which include request bytes in $C5-$D3)",
        "SOUND TEST: $D2BF changes only at $0B38 and $0BCC while the sound-test loop runs (its closure has unresolved "
        "computed jumps, so stores at the other writers are not excluded)"],
    0x74027: [
        "RECORD FETCH: $D297 <= 15 and $D298 <= 2 whenever the level loader at $2A4F runs, so the four slot types come "
        "from the nine records (types 0-14)",
        "ALLOCATOR: every caller of $1CD3 passes C <= 20; only the direct call sites (C = 7, 9, 16) are enumerated, the "
        "kernel vector $0374 can also be entered through callback stubs with an unknown C"],
    0x741F1: [
        "ZONE TYPE: while a slot of type 5 runs, $D297 <= 5 (type 5 occurs only in the records of zones 2, 4 and 5)"],
}


def open_conditions(cond_proofs):
    out = []
    for s, p in sorted(cond_proofs.items()):
        if p["status"] in ("partial", "unproven"):
            out.append(OrderedDict([
                ("site", s), ("cpu", p.get("cpu")), ("status", p["status"]),
                ("unsupported_values", p.get("unsupported_in_effective_domain", [])),
                ("unknown_load", [OrderedDict([("asm", e["asm"]), ("cpu", e["cpu"])])
                                  for st in p.get("starts", []) for e in st.get("unknown_load", [])][:1]),
                ("lemmas_that_would_discharge_it", LEMMAS.get(s, ["a ROM-derived bound on the index at the unknown load"]))]))
    return out


def supporting_evidence(rom, con_walk):
    """Evidence for the dispatchers whose index comes from game state (sites B, C and the zone-indexed jump)."""
    import decomp1d_r1_sources as SRC
    ledger_ids = None
    ledger = ROOT / "data" / "rom-cache" / "audio" / "request-ledger.json"
    if ledger.is_file():
        ledger_ids = {r["request_id"] for r in json.loads(ledger.read_text(encoding="utf-8"))["requests"]}
    loop = D.state_walk(rom, [(0x0B6D, 1, "U")], SHADOW, follow_restart=True)
    d2bf = sorted({f for f in loop["visited"]
                   for form, a, w in memory_writes(z80.decode(bytes(rom[f:f + 4]), F.cpu_address(f)))
                   if form == "abs" and a <= SRC.SOUND_TEST < a + w})
    other_d2bf = [o for o, _ in D.store_pattern_sites(rom, SRC.SOUND_TEST, 1)] + \
        [o for o, k in D.store_pattern_sites(rom, SRC.SOUND_TEST, 2) if k != "LD (nn),A"]
    iy0 = []
    for f in sorted(con_walk["visited"]):
        if f // BANK == 0x1D:
            d = z80.decode(bytes(rom[f:f + 4]), sorted(con_walk["cpu_at"].get(f, {F.cpu_address(f)}))[0])
            if any(form == "iy" and disp == 0 for form, disp, width in memory_writes(d)):
                iy0.append(f)
    return OrderedDict([
        ("site_b_request_byte", OrderedDict([
            ("audio0_ledger_ids_used", ledger_ids is not None),
            ("sources", SRC.request_sources(rom, ledger_ids)),
            ("sound_test", OrderedDict([
                ("clamp", SRC.sound_test_clamp(rom)),
                ("writers_of_d2bf", sorted(set(other_d2bf))),
                ("writers_inside_the_sound_test_loop_closure", d2bf),
                ("loop_closure_instructions", len(loop["visited"])),
                ("loop_closure_open_edges", sorted({tuple(e) for e in loop["open_edges"]})),
                ("conclusion", "open: the loop's closure contains unresolved computed jumps, so a store to $D2BF outside "
                               "$0B38/$0BCC cannot be excluded")]))])),
        ("site_c_slot_type", OrderedDict([
            ("sources", SRC.slot_type_sources(rom)),
            ("stores_to_iy_plus_0_in_bank_1d_closure", iy0)]))])


def stray_targets(proofs):
    """Destinations of entries a proof does not support, checked against the interiors of the proven dispatchers: an
    unresolved destination that lands inside a proven region (not at one of its starts) would void that proof."""
    interior = {}
    for p in proofs.values():
        if p["status"] in ("proven", "unreachable") and "region" in p:
            for n in p["region"]:
                if not n["start"]:
                    interior.setdefault(n["file"], []).append(p["site"])
    out = []
    for p in proofs.values():
        for e in p.get("table", {}).get("entries", []):
            if e["supported"] or e["target_file"] is None:
                continue
            if e["target_file"] in interior:
                out.append(OrderedDict([("dispatcher", p["site"]), ("values", e["values"]), ("target_cpu", e["target_cpu"]),
                                        ("target_file", e["target_file"]), ("inside_region_of", interior[e["target_file"]])]))
    return out


def build(rom, root=ROOT, data_domains=None):
    import rom_ledger as RL      # late import: rom_ledger imports decomp1d_banked_flow
    regions = json.loads((root / "asm" / "recovered" / "regions.json").read_text(encoding="utf-8"))
    facts = D.Facts.of(rom)
    baseline = RL.build_ledger(rom, root, reviewed=False)
    ledger_ctx = D.Context(baseline["claims"])
    ctx = ledger_ctx
    for dom in (data_domains or {}).values():
        if dom.get("non_code_files"):
            ctx = with_data(ctx, dom["non_code_files"], dom.get("non_code_label", "DATA"))
    setter = D.mapper_setter(rom, 0x1C6F)
    shadow = setter["shadow"]
    if shadow != SHADOW:
        raise RuntimeError("the slot-2 shadow is not $D12B")
    base_walk = D.state_walk(rom, [IRQ_ROOT], shadow)
    open_before = sorted(base_walk["indirect"])
    if open_before != sorted(TASK_SITES):
        raise RuntimeError("the DECOMP-1D open computed jumps are not the three task sites: %s" % [hx(x) for x in open_before])
    off_walk, off_disp, off_proofs, _ = resolve(rom, regions, facts, ctx, shadow, False, data_domains)
    con_walk, con_disp, con_proofs, uni = resolve(rom, regions, facts, ctx, shadow, True, data_domains)
    off_audit = write_audit(rom, off_walk)
    con_audit = write_audit(rom, con_walk)
    base_audit = write_audit(rom, base_walk)
    new_code = sorted(set(con_walk["visited"]) - set(base_walk["visited"]))
    new_audit = OrderedDict()
    new_stores = [(f, a) for f, a in con_walk["stores"] if f in set(new_code)]
    new_audit["newly_reachable_instructions"] = len(new_code)
    new_audit["stores_to_mapper_registers_or_shadow_by_ld_nn_a"] = [list(x) for x in sorted(set(new_stores))]
    new_audit["absolute_stores_in_new_code"] = len([1 for f in new_code for form, a, w in memory_writes(
        z80.decode(bytes(rom[f:f + 4]), sorted(con_walk["cpu_at"].get(f, {F.cpu_address(f)}))[0])) if form == "abs"])
    new_audit["register_addressed_writes_in_new_code"] = OrderedDict(
        (k, sum(1 for f in new_code for form, a, w in memory_writes(
            z80.decode(bytes(rom[f:f + 4]), sorted(con_walk["cpu_at"].get(f, {F.cpu_address(f)}))[0])) if form == k))
        for k in ("hl", "de", "bc", "ix", "iy", "block_de", "block_hl"))
    interrupt = D.interrupt_model(rom)
    doc = OrderedDict()
    doc["format"] = 1
    doc["task"] = "DECOMP-1D-R1"
    doc["rom_sha256"] = RL.ROM_SHA256
    doc["generator"] = "tools/decomp1d_r1_closure.py"
    doc["base_commit"] = BASE_COMMIT
    doc["evidence_tier"] = ("static ROM-derived control-flow evidence with exact concrete evaluation of the index "
                            "arithmetic (tools/z80_exec.py); not an execution trace")
    doc["task_sites_rederived"] = OrderedDict([
        ("decomp1d_open_computed_jumps", [hx(x) for x in open_before]),
        ("matches_task_table", open_before == sorted(TASK_SITES)),
        ("sites", [OrderedDict([("file_offset", s), ("bank", s // BANK),
                                ("cpu", sorted(uni.cpus[s])[0] if s in uni.cpus else None),
                                ("instruction", D.asm(rom, s)), ("bytes", rom[s:s + 1].hex())]) for s in sorted(TASK_SITES)])])
    doc["interrupt_contract"] = OrderedDict([
        ("vector", "IM 1 $0038: DI / PUSH AF / IN A,($BF) / RLCA / JP C,$04E2 (vblank) else JP $0650 (line interrupt, no mapper access)"),
        ("irq_exit_contract", interrupt["irq"]["exit_contract"]),
        ("irq_exits", interrupt["irq"]["exits"]),
        ("irq_exit_restore_stores", interrupt["irq"]["exit_restore_stores"]),
        ("exit_restoration", "LD A,($D12A) / LD ($FFFE),A at $0607; LD A,($D12B) / LD ($FFFF),A at $060D; both rewrite the "
                             "registers from their RAM shadows immediately before POP/EI/RET"),
        ("nmi", interrupt["nmi"]),
        ("restart_paths", OrderedDict([
            ("followed", False),
            ("rule", "a JP to $0450 (DI / LD SP) discards the interrupted context; the walk does not follow it"),
            ("sites_in_baseline_closure", base_walk["restart"]),
            ("sites_in_conditional_closure", con_walk["restart"])])),
        ("top_level_exit_contract_holds", interrupt["irq"]["exit_contract_holds"])])
    doc["dispatchers"] = [_site_summary(rom, p) for _, p in sorted(con_proofs.items())]
    doc["destinations"] = [OrderedDict([
        ("site", p["site"]), ("status", p["status"]),
        ("supported", [OrderedDict([("values", e["values"]), ("word_file", e["word_file"]), ("target_cpu", e["target_cpu"]),
                                    ("target_file", e["target_file"])]) for e in p.get("table", {}).get("entries", []) if e["supported"]]),
        ("unsupported", [OrderedDict([("values", e["values"]), ("word_file", e["word_file"]), ("target_cpu", e["target_cpu"]),
                                      ("descent_ok", e["descent_ok"]), ("in_table_region", e["in_table_region"])])
                         for e in p.get("table", {}).get("entries", []) if not e["supported"]])])
        for _, p in sorted(con_proofs.items())]
    doc["official_walk"] = walk_stats(rom, off_walk, off_audit)
    doc["conditional_walk"] = walk_stats(rom, con_walk, con_audit)
    doc["baseline_walk"] = OrderedDict([("instructions", len(base_walk["visited"])),
                                        ("open_edges", [[e[0]] + list(e[1:]) for e in base_walk["open_edges"]]),
                                        ("write_audit", base_audit)])
    doc["newly_reachable_code"] = new_audit
    doc["unsupported_destinations_inside_proven_regions"] = stray_targets(con_proofs)
    doc["expanded_sequence_integrity"] = expanded_sequence_check(rom, regions, facts, ledger_ctx, con_walk)
    doc["mirror_alias_scan"] = mirror_alias_scan(rom)
    doc["supporting_evidence"] = supporting_evidence(rom, con_walk)
    doc["open_conditions"] = open_conditions(con_proofs)
    doc["residual_assumptions"] = list(RESIDUAL)
    doc["verdict"] = derive_verdict(off_walk, off_audit, con_walk, con_audit, con_proofs, off_proofs)
    doc["ledger_effect"] = OrderedDict([
        ("changed", False),
        ("note", "No recovered region, seed or classification is added; the deferred DECOMP-1D regions stay deferred for "
                 "Manager review.")])
    return doc


def destinations_block(doc):
    """Compact machine-readable destination list embedded in docs/decomp-1d-r1-interrupt-closure.md."""
    def f5(v):
        return None if v is None else "0x%05X" % v

    def c4(v):
        return "0x%04X" % v

    out = []
    for d in doc["dispatchers"]:
        rows = d.get("table", {}).get("entries", [])
        sup = [r for r in rows if r["supported"]]
        out.append(OrderedDict([
            ("jp_hl_file", f5(d["site"])), ("jp_hl_cpu", c4(d["cpu"])), ("bank", d["bank"]), ("status", d["status"]),
            ("table_cpu", c4(d["table"]["base"]) if "table" in d else None),
            ("supported", [OrderedDict([("values", r["values"]), ("word_file", f5(r["word_file"])),
                                        ("target_cpu", c4(r["target_cpu"])), ("target_file", f5(r["target_file"]))])
                           for r in sup]),
            ("unsupported_values", d.get("code_domain", {}).get("unsupported_values", [])),
            ("unsupported_in_effective_domain", d.get("unsupported_in_effective_domain", [])),
            ("pushed_continuations", [c4(c) for c in d.get("pushed_continuations", [])])]))
    return out


DOC_BLOCK = ("<!-- DESTINATIONS_START -->", "<!-- DESTINATIONS_END -->")
DOC_PATH = ROOT / "docs" / "decomp-1d-r1-interrupt-closure.md"


def render_block(block):
    return "%s\n```json\n%s\n```\n%s" % (DOC_BLOCK[0], json.dumps(block, indent=1), DOC_BLOCK[1])


def update_doc(path, block):
    """Replace the machine-readable destination block of the document in place."""
    text = Path(path).read_text(encoding="utf-8")
    lo, hi = text.index(DOC_BLOCK[0]), text.index(DOC_BLOCK[1]) + len(DOC_BLOCK[1])
    Path(path).write_bytes((text[:lo] + render_block(block) + text[hi:]).encode("utf-8"))


def doc_block(path):
    """The destination list currently embedded in the document."""
    text = Path(path).read_text(encoding="utf-8")
    inner = text[text.index(DOC_BLOCK[0]) + len(DOC_BLOCK[0]):text.index(DOC_BLOCK[1])]
    return json.loads(inner.replace("```json", "").replace("```", ""))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("rom", nargs="?")
    ap.add_argument("--output", default=str(OUTPUT))
    ap.add_argument("--destinations", action="store_true", help="print the compact destination list as JSON and exit")
    ap.add_argument("--update-doc", action="store_true", help="also rewrite the destination block of the document")
    args = ap.parse_args(argv)
    import rom_ledger as RL
    rom = RL.load_rom(args.rom or os.environ.get("SONIC_CHAOS_ROM") or RL.DEFAULT_ROM)
    doc = build(rom, data_domains=data_domains(rom))
    if args.destinations:
        print(json.dumps(destinations_block(doc), indent=1))
        return 0
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_bytes((json.dumps(doc, indent=1) + "\n").encode("utf-8"))
    if args.update_doc:
        update_doc(DOC_PATH, destinations_block(doc))
    v = doc["verdict"]
    print("R1 verdict: %s; sites %s" % (v["r1"], dict(v["computed_jump_sites"])))
    return 0


def data_domains(rom):
    """ROM-derived restrictions of the index registers, keyed by site, with the evidence that justifies them."""
    import decomp1d_r1_streams as S
    streams = S.analyse(rom)
    evidence = OrderedDict((k, v) for k, v in streams.items() if k not in ("values", "applies_to_unknown_loads"))
    evidence["stream_data_intervals"] = len(streams["data_files"])
    evidence = OrderedDict((k, v) for k, v in evidence.items() if k not in ("data_files",))
    return {0x086E8: {"values": streams["values"], "applies_to_unknown_loads": streams["applies_to_unknown_loads"],
                      "evidence": evidence, "non_code_files": streams["data_files"], "non_code_label": "SOUND_STREAM"}}


if __name__ == "__main__":
    sys.exit(main())

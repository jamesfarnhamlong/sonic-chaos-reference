#!/usr/bin/env python3
"""DECOMP-1D-R4A: residual object-dispatch closure (the four computed jumps DECOMP-1D-R3 left open).

    python tools/decomp1d_r4a_object_dispatch.py /path/to/SonicChaos.sms [--output data/decomp1d/r4a-object-dispatch-closure.json]
                                                 [--doc docs/decomp-1d-r4a-object-dispatch-closure.md] [--check]

R3 could not close four table-indexed computed jumps in the code a special stage runs (physical offsets ``$314F4``, ``$6972``,
``$77EC``, ``$6C98``). All four are *terrain-surface* dispatchers of the shared collision engine, not object-creation code: the
index is the surface type (or the block id) that the block-lookup routines ``$7666``/``$7725`` read out of the block header
table. This module re-derives, from the canonical ROM only:

1. the instructions that build and bound each index and the table each jump reads (``jump_facts``);
2. every writer of the registers that feed them (``D364`` surface byte, ``D353`` block id, ``D36B`` its copy, ``D2E0`` header-table
   pointer) and the code regions between the lookup and the jump (``feeders``);
3. the complete index domain, by enumerating all 256 block ids in both header planes (``header_domain``);
4. the destinations those indices can reach, and what the code behind them can create (``creation``);
5. whether anything behind them reaches the level-clear callers, the bit-4 setters, or object type ``$61`` (``u1``).

It reuses the accepted R3 machinery (fail-closed interpreter, recursive descent, creation-site scanner) and the accepted
Special Stage caches as read-only inputs; it writes only its own evidence. Premises are listed in the output, never assumed silently.
"""
import argparse
import json
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1d_r2_zone_act as R2  # noqa: E402
import decomp1d_r3_special_stage as R3  # noqa: E402
import rom as ROMTOOLS  # noqa: E402
import rom_flow as F  # noqa: E402
from z80dis import z80  # noqa: E402

OUTPUT = ROOT / "data" / "decomp1d" / "r4a-object-dispatch-closure.json"
DOC = ROOT / "docs" / "decomp-1d-r4a-object-dispatch-closure.md"
BASE_COMMIT = "8af1f0366a3620d20b0a1341017d272968c5cfbb"        # Research main after DECOMP-1D-R3 integration
SS_DIR = ROOT / "data" / "rom-cache" / "special-stages"
R3_JSON = ROOT / "data" / "decomp1d" / "r3-special-stage-reachability.json"
BEGIN = "<!-- r4a-generated:begin -->"
END_MARK = "<!-- r4a-generated:end -->"

hx = R3.hx
word = R3.word
HEADER_TABLE = 0x38000            # physical: bank 14, CPU $8000 (block id -> header pointer, words); verified through the loader record
HEADER_BASE = 0x30000             # pointer words are added to this physical base (bank 12 + $8000 window arithmetic of rom.header)
D364, D353, D36B, D2E0 = 0xD364, 0xD353, 0xD36B, 0xD2E0
SURFACE_MASK = 0x1F

# 16-bit absolute memory instructions: opcode (prefix) -> kind.
_ABS_OPS = OrderedDict([((0x3A,), "read"), ((0x32,), "write"), ((0x2A,), "read"), ((0x22,), "write"),
                        ((0xED, 0x4B), "read"), ((0xED, 0x5B), "read"), ((0xED, 0x6B), "read"), ((0xED, 0x7B), "read"),
                        ((0xED, 0x43), "write"), ((0xED, 0x53), "write"), ((0xED, 0x63), "write"), ((0xED, 0x73), "write"),
                        ((0x21,), "address constant"), ((0x11,), "address constant"), ((0x01,), "address constant"),
                        ((0x31,), "address constant")])


# --- 1. byte-level census of references to a RAM variable ---------------------------------------------------------------
def absolute_references(rom, addr):
    """Every encoding of an absolute 16-bit access to ``addr`` anywhere in the image (byte search, so alignment hides nothing)."""
    lo, hi = addr & 0xFF, addr >> 8
    rows = []
    for i in range(1, len(rom) - 1):
        if rom[i] != lo or rom[i + 1] != hi:
            continue
        for prefix, kind in _ABS_OPS.items():
            start = i - len(prefix)
            if start >= 0 and tuple(rom[start:i]) == prefix:
                rows.append(OrderedDict([("file_offset", start), ("kind", kind), ("bytes", rom[start:i + 2].hex()),
                                         ("context", R3.context_of(start))]))
                break
    return rows


def writer_census(rom):
    out = OrderedDict()
    for name, addr in (("D364", D364), ("D353", D353), ("D36B", D36B), ("D2E0", D2E0)):
        refs = absolute_references(rom, addr)
        out[name] = OrderedDict([
            ("address", addr),
            ("writes", [r["file_offset"] for r in refs if r["kind"] == "write"]),
            ("reads", [r["file_offset"] for r in refs if r["kind"] == "read"]),
            ("address_constants", [r["file_offset"] for r in refs if r["kind"] == "address constant"])])
    return out


# --- 2. the header table -----------------------------------------------------------------------------------------------
def header_domain(rom):
    """Surface byte of every block id in both header planes (plane 1 is the ``+7`` alternate header read when bit 5 is set and
    ``(IX+0x25)`` is non-zero). ``candidates[id]`` is every value ``D364`` can take for that block id."""
    rows, by_surface = [], OrderedDict()
    for b in range(256):
        cand = []
        for plane in (0, 1):
            flags = ROMTOOLS.header(rom, b, plane)["flags"]
            if flags not in cand:
                cand.append(flags)
        rows.append(OrderedDict([("id", b), ("flags", cand), ("surfaces", sorted({c & SURFACE_MASK for c in cand}))]))
        for s in rows[-1]["surfaces"]:
            by_surface.setdefault(s, []).append(b)
    by_surface = OrderedDict(sorted(by_surface.items()))
    return OrderedDict([("rows", rows), ("ids_by_surface", by_surface), ("surfaces_present", sorted(by_surface)),
                        ("surfaces_absent", [s for s in range(32) if s not in by_surface])])


def d2e0_values(rom):
    """``D2E0`` is stored once (the loader, ``$2A71``) from the first word of the record the loader reads; value per verified record."""
    d = R3.decode_site(rom, 0x2A71)[1]
    recs = [0x2AF6, 0x2B00, 0x2B0A, 0x2B14, 0x2B1E, 0x2B28, 0x2B32, 0x2B3C, 0x2B46]
    return OrderedDict([("writer", OrderedDict([("file_offset", 0x2A71), ("asm", d)])),
                        ("verified_record_values", OrderedDict((hx(r), word(rom, r)) for r in recs)),
                        ("all_equal", len({word(rom, r) for r in recs}) == 1), ("table_physical", HEADER_TABLE)])


# --- 3. the code between a lookup and a jump -----------------------------------------------------------------------------
LOOKUP_ENTRIES = (0x7666, 0x7725)
LOOKUP_WRITERS = (0x76CB, 0x76DC, 0x76EE, 0x7792, 0x77A2, 0x77B8, 0x77BD)


def reach_facts(rom, roots, writers):
    reached, indirect, slot2 = R3.resident_reach(rom, roots, {})
    hits = sorted(o for o in writers if o in reached)
    tg = set()
    for off in reached:
        d = F.decode(rom, off)
        if d.op in F.TRANSFER_OPS:
            t = F._addr_operand(d)
            if t is not None:
                tg.add(t)
    return OrderedDict([("roots", [hx(r) for r in roots]), ("instructions", len(reached)),
                        ("writer_instructions_reached", [hx(o) for o in hits]),
                        ("calls_a_lookup_entry", sorted(hx(t) for t in LOOKUP_ENTRIES if t in tg)),
                        ("computed_jumps_not_followed", [hx(o) for o in indirect]),
                        ("resident_to_slot2_transfers", [hx(o) for o in slot2])])


def interrupt_facts(rom, writers):
    """IM 1 closure of DECOMP-1D R2 (the conditional walk R3 also uses): does it contain a writer or a lookup entry?"""
    walk = R2.irq_closure(rom)
    visited = set(walk["visited"])
    sites = sorted(set(writers) | {0x6955, 0x2A71} | set(LOOKUP_ENTRIES))
    return OrderedDict([("closure_instructions", len(visited)), ("writers_lookups_or_d2e0_store_inside", [hx(o) for o in sites if o in visited]),
                        ("computed_jumps", [hx(o) for o in walk["indirect"]]), ("open_edges", [[k, hx(v)] for k, v in walk["open_edges"]])])


KNOWN_ROOTS = (0x0000, 0x0038, 0x0066, 0x16B8, 0x173F)


def known_code(rom, uni):
    """Instruction starts (file offset -> length) of every routine this analysis can reach: the reset/IM 1/NMI vectors and the per-frame
    code, plus the callback closure of every object type (R3 descent, resident callees included)."""
    def compute():
        reached, _i, _s = R3.resident_reach(rom, KNOWN_ROOTS, {})
        reached = dict(reached)
        more, _o, _n = R3.callback_closure(rom, uni, tuple(uni))
        reached.update(more)
        return reached
    return R3._cached("r4a-known", rom, compute)


def classify_hit(known, off):
    if off in known:
        return "instruction start in known code"
    for back in range(1, 4):
        if off - back in known and off - back + known[off - back] > off:
            return "inside a known instruction (operand or opcode bytes)"
    return "outside known code (not shown to be data)"


def transfers_into(rom, lo, hi, known=None):
    """Absolute CALL/JP/JP cc/CALL cc whose target lies in ``[lo, hi]`` (byte search), classified against the known-code universe."""
    ops = (0xCD, 0xC3, 0xC2, 0xCA, 0xD2, 0xDA, 0xC4, 0xCC, 0xD4, 0xDC, 0xE2, 0xEA, 0xF2, 0xFA, 0xE4, 0xEC, 0xF4, 0xFC)
    rows = []
    for i in range(len(rom) - 2):
        if rom[i] in ops and lo <= rom[i + 1] | rom[i + 2] << 8 <= hi:
            rows.append(OrderedDict([("file_offset", i), ("bytes", rom[i:i + 3].hex()), ("target", rom[i + 1] | rom[i + 2] << 8),
                                     ("class", classify_hit(known, i) if known is not None else None), ("context", R3.context_of(i))]))
    return rows


def word_hits(rom, value):
    """Every little-endian occurrence of ``value`` (table words and pointer data show up here)."""
    lo, hi = value & 0xFF, value >> 8
    return [i for i in range(len(rom) - 1) if rom[i] == lo and rom[i + 1] == hi]


def entry_facts(rom, known, lo, hi, entries):
    """Absolute transfers into a dispatcher's routine: hits that are instructions of known code must target an expected entry; a hit inside
    another instruction is an operand coincidence; a hit outside known code is listed and stays an assumption (P5)."""
    rows = transfers_into(rom, lo, hi, known)
    starts = [r for r in rows if r["class"] == "instruction start in known code"]
    return OrderedDict([("expected_entries", list(entries)), ("transfers", rows),
                        ("targets_of_known_code_hits", sorted({r["target"] for r in starts})),
                        ("known_code_hits_only_at_expected_entries", all(r["target"] in entries for r in starts)),
                        ("hits_inside_known_instructions", [r["file_offset"] for r in rows if r["class"].startswith("inside")]),
                        ("hits_outside_known_code", [r["file_offset"] for r in rows if r["class"].startswith("outside")])])


# --- 4. the four jumps ---------------------------------------------------------------------------------------------------
def _table(rom, base, n):
    return [word(rom, base + 2 * i) for i in range(n)]


def jump_6972(rom, dom):
    spec = R3.jump_destinations(rom, 0x6972)            # verifies the instruction pattern; raises when the bytes differ
    table = _table(rom, 0x6973, 33)
    surfaces = dom["surfaces_present"]
    reachable = sorted(surfaces)
    return OrderedDict([("site", 0x6972), ("spec", spec), ("index", "D364 & $1F"), ("table_cpu", 0x6973), ("table_entries", 31),
                        ("index_values_reached", reachable), ("index_31_reached", 31 in reachable),
                        ("words_past_the_table", table[31:33]),
                        ("destinations_by_surface", OrderedDict((s, table[s]) for s in reachable))])


def jump_77ec(rom, dom):
    spec = R3.jump_destinations(rom, 0x77EC)
    table = _table(rom, 0x77ED, 33)
    reachable = sorted(dom["surfaces_present"])
    return OrderedDict([("site", 0x77EC), ("spec", spec), ("index", "D364 & $1F"), ("table_cpu", 0x77ED), ("table_entries", 31),
                        ("index_values_reached", reachable), ("index_31_reached", 31 in reachable),
                        ("words_past_the_table", table[31:33]),
                        ("destinations_by_surface", OrderedDict((s, table[s]) for s in reachable))])


C98_PATTERN = ["LD A,(0xd36b)", "CP 0x83", "JR z,0x6cb9", "SUB 0x48", "RET c", "ADD A,A", "LD L,A", "LD H,0", "LD DE,0x6c99",
               "ADD HL,DE", "LD E,(HL)", "INC HL", "LD D,(HL)", "EX DE,HL", "JP (HL)"]


def c98_destination(rom, block_id):
    """Instruction semantics of ``$6C82..$6C98`` for ``D36B = block_id`` (cross-checked against the interpreter below)."""
    if block_id == 0x83:
        return 0x6CB9
    if block_id < 0x48:
        return None                                      # RET c
    off = ((block_id - 0x48) * 2) & 0xFF
    return word(rom, 0x6C99 + off)


def jump_6c98(rom, dom, KNOWN):
    if R3._decode_run(rom, None, 0x6C82, len(C98_PATTERN)) != C98_PATTERN:
        raise ValueError("the dispatcher at $6C82 no longer matches its specification")
    table_end = min(word(rom, 0x6C99 + 2 * i) for i in range(16))          # the first destination follows the table
    entries = (table_end - 0x6C99) // 2
    ids16 = dom["ids_by_surface"].get(16, [])
    # fail-closed interpreter cross-check on every block id
    mismatches = []
    for b in range(256):
        m = R3.Interp3(rom, ram={D36B: b}, slot1=1, slot2=None)
        try:
            m.run(0x6C82, stops=(0x6C98, 0x6CB9), limit=60)
            got = m.get16("HL") if m.pc == 0x6C98 else 0x6CB9 if m.pc == 0x6CB9 else None
        except Exception:                                  # noqa: BLE001 - RET c ends the run at the caller (empty stack)
            got = None
        if got != c98_destination(rom, b):
            mismatches.append(b)
    reached = OrderedDict((b, c98_destination(rom, b)) for b in ids16)
    inside = all(b == 0x83 or 0x48 <= b < 0x48 + entries for b in ids16)
    dests = sorted({v for v in reached.values() if v is not None})
    return OrderedDict([("site", 0x6C98), ("pattern", C98_PATTERN), ("index", "(D36B - $48) * 2 (8-bit), D36B = block id; $83 branches first"),
                        ("table_cpu", 0x6C99), ("table_entries", entries), ("table_end_cpu", table_end),
                        ("word_after_table", word(rom, 0x6C99 + 2 * entries)),
                        ("surface_16_block_ids", ids16), ("all_ids_inside_table_or_special_case", inside),
                        ("destination_by_block_id", reached), ("destinations", dests), ("interpreter_mismatches", mismatches),
                        ("entry_points", OrderedDict([("jump_table_6972_entry_16", word(rom, 0x6973 + 2 * 16)),
                                                      ("absolute_transfers_into_6C82_6C98", entry_facts(rom, KNOWN, 0x6C82, 0x6C98, ())),
                                                      ("word_hits_6C82", word_hits(rom, 0x6C82))]))])


def jump_314f4(rom, dom):
    spec = R3.jump_destinations(rom, 0x314F4)
    gate = ["LD A,(0xd364)", "AND 0x3f", "CP 0x17", "JP nz,0x95e4"]
    if R3._decode_run(rom, 12, 0x94C7, len(gate)) != gate:
        raise ValueError("the surface gate of $314F4 no longer matches its specification")
    ids = sorted({b for r in dom["rows"] for f in r["flags"] if f & 0x3F == 0x17 for b in (r["id"],)})
    idx = [b - 0x58 for b in ids]
    sub = [R3.word(rom, R3.slot2_off(12, 0x94F5 + 2 * i)) for i in range(4)]
    between, cpu = [], 0x94D1                                  # after the gate's JP nz, up to the read of D353
    while cpu < 0x94E2:
        d = F.decode(rom, R3.slot2_off(12, cpu))
        between.append(z80.disasm(d))
        cpu += d.len
    transfers = [t for t in between if t.split()[0].upper() in ("CALL", "JP", "JR", "RST", "DJNZ", "RET")]
    return OrderedDict([("site", 0x314F4), ("spec", spec), ("gate", "D364 & $3F == $17 (surface $17, bit 5 clear)"),
                        ("gate_instructions", gate), ("index", "(D353 - $58) * 2 into one of four 28-word sub-tables"),
                        ("sub_table_pointers", sub), ("entries_per_sub_table", 28),
                        ("gate_block_ids", ids), ("index_values", [min(idx), max(idx)] if idx else None),
                        ("all_ids_inside_sub_table", bool(ids) and min(idx) >= 0 and max(idx) < 28),
                        ("invalid_destinations", spec["invalid"]), ("destinations", spec["destinations"]),
                        ("instructions_between_gate_and_d353_read", between), ("transfers_between", transfers),
                        ("between_gate_and_index", "no CALL/JP between $314C7 (D364 read) and $314E2 (D353 read): the same lookup supplies both")])


# --- 5. what the destinations can run and create --------------------------------------------------------------------------
KNOWN_TABLE_JUMPS = ("$5FB8", "$311BB")        # closed in R3 (specified, bounded, followed): their destinations are followed there


def closure_of(rom, res_roots, bank_roots, jump_dests):
    """Recursive descent from resident roots and (bank, cpu) roots. ``jump_dests`` maps computed-jump sites (``$hex``) to
    ``[(bank or None, [cpu...])]``; sites found but not listed stay open. Returns (reached, open_jumps, slot2_transfers)."""
    cache, reached = {}, {}
    res, banks = set(res_roots), {b: set(v) for b, v in bank_roots.items()}
    seen_res, seen_bank, open_jumps, slot2 = set(), {}, set(), set()
    followed = set()
    while True:
        progressed = False
        new_res = sorted(res - seen_res)
        if new_res:
            seen_res |= set(new_res)
            progressed = True
            r, ind, s2 = R3.resident_reach(rom, new_res, cache)
            reached.update(r)
            slot2.update(s2)
            open_jumps.update(hx(o) for o in ind)
        for bank, roots in sorted(banks.items()):
            new = sorted(roots - seen_bank.setdefault(bank, set()))
            if not new:
                continue
            seen_bank[bank] |= set(new)
            progressed = True
            r, notes = R3.descend_bank(rom, bank, new)
            reached.update(r)
            open_jumps.update(hx(n[1]) for n in notes if n[0] == "indirect")
            for off in r:
                d = F.decode(rom, off)
                if d.op in F.TRANSFER_OPS:
                    t = F._addr_operand(d)
                    if t is not None and t < 0x8000:
                        res.add(t)
        for site in sorted(open_jumps):
            if site in followed or site not in jump_dests:
                continue
            followed.add(site)
            progressed = True
            for bank, cpus in jump_dests[site]:
                for c in cpus:
                    if bank is None or c < 0x8000:
                        res.add(c)
                    else:
                        banks.setdefault(bank, set()).add(c)
        if not progressed:
            break
    left = sorted(j for j in open_jumps if j not in jump_dests)
    return reached, left, sorted(hx(o) for o in slot2)


def creation_scan(rom, reached):
    rows = R3.type_creation_sites(rom, reached)
    real = [r for r in rows if r["kind"] not in ("destroy marker", "not a type store")]
    return OrderedDict([("instructions", len(reached)), ("sites", len(rows)),
                        ("creation_sites", [OrderedDict([("file_offset", r["file_offset"]), ("kind", r["kind"]), ("asm", r["asm"]),
                                                         ("value", r["value"])]) for r in real]),
                        ("destroy_markers", sum(1 for r in rows if r["kind"] == "destroy marker"))])


def trigger_reach(rom, reached):
    """Does the code reach a level-clear caller, a bit-4 setter, or a CALL/JP to the level-clear routine?"""
    offs = set(R3.LEVEL_CLEAR_CALLERS) | set(R3.SETTER_OFFSETS)
    hit = sorted(o for o in offs if o in reached)
    calls = []
    for off in reached:
        d = F.decode(rom, off)
        if d.op in (F.OP.CALL, F.OP.JP) and F._addr_operand(d) in (R3.LEVEL_CLEAR, R3.LEVEL_CLEAR_STUB):
            calls.append(off)
    return OrderedDict([("setters_or_callers_reached", [hx(o) for o in hit]), ("calls_to_level_clear", [hx(o) for o in sorted(calls)])])


def jump_dest_table(rom, j6972, j77ec, j6c98, j314):
    """Destinations of every table jump the closure can contain: the four resolved here (reachable indices only) and the two R3 closed."""
    out = OrderedDict()
    out["$6972"] = [(None, sorted(set(j6972["destinations_by_surface"].values())))]
    out["$77EC"] = [(None, sorted(set(j77ec["destinations_by_surface"].values())))]
    out["$6C98"] = [(None, j6c98["destinations"])]
    out["$314F4"] = [(12, j314["destinations"])]
    for site in (0x5FB8, 0x311BB):
        r = R3.jump_destinations(rom, site)
        out[hx(site)] = [(r["bank"], r["destinations"])]
    return out


def destination_checks(rom, bank, cpus):
    """Each destination must decode as an instruction in the window its jump runs in (a table word is not trusted otherwise)."""
    rows = []
    for c in sorted(set(cpus)):
        off = c if bank is None else R3.slot2_off(bank, c)
        ok = (0 <= c < 0x8000) if bank is None else (0x8000 <= c < 0xC000)
        d = F.decode(rom, off) if ok else None
        rows.append(OrderedDict([("cpu", c), ("in_window", ok), ("decodes", bool(d and d.len and d.op != F.OP.NONI))]))
    return rows


def surface_creation_map(rom, dom, j6972, j77ec, jd):
    """Creation sites statically reachable from the handler of each surface (floor table $6973, second table $77ED)."""
    out = OrderedDict()
    for name, j in (("$6972", j6972), ("$77EC", j77ec)):
        rows = OrderedDict()
        for surf, dest in j["destinations_by_surface"].items():
            reached, left, s2 = closure_of(rom, [dest], {}, jd)
            sc = creation_scan(rom, reached)
            rows[str(surf)] = OrderedDict([("handler", dest), ("instructions", len(reached)),
                                           ("created_types", sorted({x["value"] for x in sc["creation_sites"] if x["value"] is not None})),
                                           ("unresolved_creation_sites", [x["file_offset"] for x in sc["creation_sites"] if x["value"] is None]),
                                           ("computed_jumps_left_open", left)])
        out[name] = rows
    return out


def j5e6f(rom):
    pat = ["AND 15", "ADD A,A", "LD L,A", "LD H,0", "LD DE,0x5e70", "ADD HL,DE", "LD E,(HL)", "INC HL", "LD D,(HL)", "EX DE,HL", "JP (HL)"]
    if R3._decode_run(rom, None, 0x5E61, len(pat)) != pat:
        raise ValueError("the dispatcher at $5E6F no longer matches its specification")
    words = _table(rom, 0x5E70, 16)
    return OrderedDict([("site", 0x5E6F), ("pattern", pat), ("index", "A & 15"), ("table_cpu", 0x5E70), ("table_entries", 16),
                        ("table_end_cpu", 0x5E90), ("destinations", sorted(set(words))), ("bounded_by_instruction", True)])


# --- 6. adjacent notes: the other two resident computed jumps in R3's frame-loop evidence ------------------------------------
def adjacent_notes(rom):
    r3 = json.loads(R3_JSON.read_text(encoding="utf-8"))
    return OrderedDict([
        ("r3_frame_loop_computed_jumps_not_followed", r3["creation"]["frame_loop"]["computed_jumps_not_followed"]),
        ("named_in_r3_open_list", ["$314F4", "$6972", "$6C98", "$77EC"]),
        ("not_named_in_r3_open_list", ["$5E6F", "$5E9A", "$6695"]),
        ("$5E9A", OrderedDict([("asm", [R3.decode_site(rom, 0x5E91)[1], R3.decode_site(rom, 0x5E94)[1], R3.decode_site(rom, 0x5E9A)[1]]),
                               ("what", "JP (HL) with HL = (IX+12),(IX+13): the per-object callback pointer; zero returns"),
                               ("status", "OPEN - destinations are the callback vectors the scripts install (R3 callback_vectors); "
                                          "other writers of (IX+12)/(IX+13) were not censused in R3 or here")])),
        ("$6695", OrderedDict([("asm", R3.decode_site(rom, 0x6695)[1]),
                               ("what", "script-command dispatcher: index = the byte after $FF, table $6696 of 16 words (DECOMP-1C HANDLER_TABLE)"),
                               ("status", "OPEN - the index is script data; the 16 handlers are DECOMP-1C's; not re-derived here")])),
    ])


# --- 7. reconciliation with the accepted Special Stage research ----------------------------------------------------------
def accepted_inputs():
    manifest = json.loads((SS_DIR / "implementation-manifest.json").read_text(encoding="utf-8"))
    census = json.loads((SS_DIR / "object-census.json").read_text(encoding="utf-8"))
    follow = json.loads((SS_DIR / "followup.json").read_text(encoding="utf-8"))
    return manifest, census, follow


def reconciliation(rom):
    manifest, census, follow = accepted_inputs()
    act2 = follow["act_index2_reachability"]
    stage_surfaces = sorted(int(s) for s in manifest["surfaces"])
    census_types = sorted(int(t, 16) for t in census["types"])
    per_stage = OrderedDict()
    for key, st in census["stages"].items():
        z = manifest["stages"][key]["descriptor"]["zone"]
        ptr = R3.placement_pointer(rom, z, 0)
        lst = R3.parse_list(rom, ptr)
        types = OrderedDict()
        for e in lst["entries"]:
            types["%02X" % e["type"]] = types.get("%02X" % e["type"], 0) + 1
        accepted = OrderedDict((k.replace("0x", "").upper().zfill(2), v) for k, v in st["type_counts"].items())
        per_stage[key] = OrderedDict([("zone", z), ("r3_list_types", OrderedDict(sorted(types.items()))),
                                      ("accepted_type_counts", OrderedDict(sorted(accepted.items()))),
                                      ("equal", dict(types) == dict(accepted)), ("list_terminated", lst["terminated"])])
    return OrderedDict([
        ("accepted_sources", ["reports/special-stages-canonical-audit.md", "docs/special-stages-foundation-audit.md", "docs/special-stages-followup-audit.md",
                              "docs/special-stages-traversal-audit.md", "docs/special-stages-powerups-audit.md", "docs/special-stages-goal-ring-audit.md",
                              "docs/special-stages-progression-audit.md", "data/rom-cache/special-stages/implementation-manifest.json",
                              "data/rom-cache/special-stages/object-census.json", "data/rom-cache/special-stages/followup.json"]),
        ("act3", OrderedDict([
            ("syntactically_permitted", "the entry gate $178F reads the character byte, the zone and the emerald mask; it does not read the act index"),
            ("reachable_under_forced_state", "a forced entry at act index 2 returns to act index 3 (accepted SS-A1/progression audit; R2 proposition B; R3 return_reload)"),
            ("reachable_through_original_gameplay", "NOT ESTABLISHED, and contradicted for ordinary entry by the accepted census"),
            ("accepted_census", OrderedDict([("act_index2_maximum_rings", act2["act_index2_maximums"]),
                                             ("any_act_index2_reaches_100", act2["any_act_index2_reaches_100"]),
                                             ("ring_counter_reset", act2["ring_counter_reset"]), ("note", act2["note"])])),
            ("r2_claim", "R2 proposition B counterexample labelled 'normal play': 100 rings in an act-index-2 act, taken as a free input (R2 U6)"),
            ("disposition", "R2's verdicts are not rewritten. Proposition B stays DISPROVEN as a statement about the syntactic and forced-state "
                            "model. As a statement about original gameplay the accepted census governs: the act-3 return is dormant, because the "
                            "census puts the maximum at 83 rings in any act-index-2 act. The census is an upper bound conditional on its ring-source "
                            "completeness (every terrain quadrant, $09 ring and +10 monitor; $3138/$4AC0 as the only entry routes); R4A reuses it "
                            "and does not re-derive it."),
        ])),
        ("object_universe", OrderedDict([
            ("accepted_placed_types", census_types), ("per_stage", per_stage),
            ("all_stage_lists_equal", all(v["equal"] for v in per_stage.values())),
            ("accepted_stage_surfaces", stage_surfaces),
            ("disposition", "R3's placed-type set for the five stage lists equals the accepted census; R3 re-derived it, R4A adopts the accepted proof.")])),
        ("r3_open_conditions_resolved_by_accepted_work", [
            OrderedDict([("r3", "U1-open: placed types of the five stages"), ("accepted", "object-census.json (placements by stage)"), ("status", "resolved, reused")]),
            OrderedDict([("r3", "act-3 'normal play' counterexample (R2 B)"), ("accepted", "followup.json act_index2_reachability"), ("status", "reconciled, not rewritten")]),
        ]),
        ("r3_open_conditions_not_resolved_by_accepted_work", [
            "out-of-domain placement lists and loader records (U1-open, U3): the accepted work covers only the five stages' own records",
            "the four computed jumps: closed here",
            "two further resident computed jumps listed in R3's frame-loop evidence ($5E9A, $6695), see adjacent notes",
            "graphics-decompressor termination: R4B"]),
    ])


# --- 8. assembling the evidence ----------------------------------------------------------------------------------------------
PREMISES = [
    "P1 Block ids are bytes: every value 0..255 is treated as possible in the layout RAM (the loader's layout and runtime edits are not "
    "enumerated); the lookups also produce id $FF with surface 0 when the cell pointer leaves $C000-$CFFF. The bounds below hold for every id.",
    "P2 The header table is the ROM table at physical $38000 (bank 14, CPU $8000): D2E0 is stored once, by the loader (physical $2A71), from the "
    "first word of the record it reads, and that word is $8000 in all nine verified records (every act of zones 0-15 with act <= 2, including "
    "the five stages). Records outside those nine (R3 U3) are not covered: for them D2E0 is whatever the record holds.",
    "P3 D364, D353 and D36B are written only by the instructions listed in writer_census (byte search of the whole image). Register-addressed "
    "stores and block moves with an unresolved destination (DECOMP-1D R2 census; inherited U5) are not excluded as writers by this task.",
    "P4 An interrupt does not run the lookup routines or change the variables between a lookup and its jump (IM 1 reach: interrupt_reach); "
    "the interrupt handler's own transfers into slot-2 code are recorded, not followed (R3 premise P3 restores the mapper).",
    "P5 Entry into each dispatcher's code is by the paths listed in entry_6972, entry_77EC and entry_points. Byte-search hits that are not instruction starts of the "
    "known-code universe (reset/IM 1/NMI, per-frame code, every object type's callback closure) are classified; those outside it are not shown to be data "
    "(R2 policy), are reported, and the conclusions assume they are not executed.",
    "P6 Standard Sega mapper semantics (DECOMP-1D R4) and the R3 mapper premises for slot 1 (bank 1) and the slot-2 banks the callers set.",
]


def build(rom):
    sha = R3.verify_rom(rom)
    uni, _commands = R3.object_universe(rom)
    dom = header_domain(rom)
    d2e0 = d2e0_values(rom)
    writers = writer_census(rom)
    known = known_code(rom, uni)
    j6972, j77ec, j6c98, j314 = jump_6972(rom, dom), jump_77ec(rom, dom), jump_6c98(rom, dom, known), jump_314f4(rom, dom)
    adj = adjacent_notes(rom)
    five = j5e6f(rom)

    writer_sites = list(LOOKUP_WRITERS)
    feeders = OrderedDict([
        ("writer_census", writers),
        ("expected", OrderedDict([("D364", [0x76DC, 0x76EE, 0x77A2, 0x77BD]), ("D353", [0x76CB, 0x7792, 0x77B8]), ("D36B", [0x6955]), ("D2E0", [0x2A71])])),
        ("lookup_sources", OrderedDict([
            ("$7666", "reads D2E0 + 2*id (word), then byte 0 of that header into D364 (76DC), byte +7 into D364 when bit 5 is set and (IX+0x25) is non-zero (76EE)"),
            ("$7725", "same table, byte 0 of the header into D364 (77A2)"),
            ("out of layout", "$77B0: D353 := $FF, D364 := 0 (77B8, 77BD)")])),
        ("d2e0", d2e0),
        ("between_lookup_and_6972", reach_facts(rom, [0x6F61], writer_sites)),
        ("between_lookup_and_77EC", reach_facts(rom, [0x70E7], writer_sites)),
        ("interrupt_reach", interrupt_facts(rom, writer_sites)),
        ("entry_6972", entry_facts(rom, known, 0x6900, 0x6972, (0x690B, 0x691A))),
        ("entry_77EC", entry_facts(rom, known, 0x77CB, 0x77EC, (0x77CB,))),
    ])

    jump_dests = jump_dest_table(rom, j6972, j77ec, j6c98, j314)
    # new destinations (not followed by R3): $6C98 and $5E6F; every resolved jump's reachable destinations as a single closure
    new_res = sorted(set(j6c98["destinations"]) | set(five["destinations"]))
    reached_new, left_new, s2_new = closure_of(rom, new_res, {}, jump_dests)
    scan_new = creation_scan(rom, reached_new)
    reached_314, left_314, s2_314 = closure_of(rom, [], {12: j314["destinations"]}, jump_dests)
    scan_314 = creation_scan(rom, reached_314)
    res_all = sorted(set(j6972["destinations_by_surface"].values()) | set(j77ec["destinations_by_surface"].values()))
    reached_all, left_all, s2_all = closure_of(rom, res_all, {}, jump_dests)
    scan_all = creation_scan(rom, reached_all)

    def per(reached, scan, left, s2):
        return OrderedDict([("reach", scan), ("trigger_reach", trigger_reach(rom, reached)), ("computed_jumps_left_open", left),
                            ("resident_to_slot2_transfers", s2)])

    creation = OrderedDict([
        ("$6C98_and_$5E6F_destinations", per(reached_new, scan_new, left_new, s2_new)),
        ("$314F4_destinations", per(reached_314, scan_314, left_314, s2_314)),
        ("$6972_and_$77EC_destinations", per(reached_all, scan_all, left_all, s2_all)),
    ])
    new_edges = []
    for src in (1, 2):
        for s in scan_new["creation_sites"]:
            if s["value"] is not None:
                new_edges.append(OrderedDict([("src", src), ("dst", s["value"]), ("kind", s["kind"]), ("file_offset", s["file_offset"])]))
    unresolved_new = [s for s in scan_new["creation_sites"] if s["value"] is None]

    # natural closure per stage, with and without the new edges
    graph = R3.creation_graph(rom, uni)
    frame = R3.frame_creation_sites(rom)
    declared = R3.declared_edges(rom)
    trig = R3.trigger_types(rom, uni)
    setter_types = sorted(set(trig["A_level_clear_callers"]) | set(trig["B_d293_50_writers"]))
    closures, union = OrderedDict(), set()
    R3_CLOSURE_UNION = set()
    for z in R3.SS_ZONES:
        ptr = R3.placement_pointer(rom, z, 0)
        types = sorted({e["type"] for e in R3.parse_list(rom, ptr)["entries"]})
        base = R3.natural_closure(rom, uni, graph, frame, types, declared)
        with_new = R3.natural_closure(rom, uni, graph, frame, types, list(declared) + new_edges)
        closures[str(z)] = OrderedDict([("placed_types", types), ("r3_closure", base), ("r4a_closure", with_new),
                                        ("unchanged", base == with_new), ("trigger_types_in_closure", sorted(set(with_new) & set(setter_types)))])
        union |= set(with_new)
        R3_CLOSURE_UNION |= set(base)
    union = sorted(union)
    open_after = ["$5E9A", "$6695"]
    unresolved_closure = [u for u in graph["unresolved_sites"] if u["src"] in union and u["file_offset"] != R3.CHARACTER_CONVERSION] + unresolved_new
    st_a, why_a = R3.route_status(trig["A_level_clear_callers"], union, unresolved_closure, open_after)
    st_b, why_b = R3.route_status(trig["B_d293_50_writers"], union, unresolved_closure, open_after)
    census_types = sorted(int(t, 16) for t in accepted_inputs()[1]["types"])
    created_outside_census = sorted(set(union) - set(census_types) - {1, 2})

    surf_map = surface_creation_map(rom, dom, j6972, j77ec, jump_dests)
    stage_surfaces = sorted(int(x) for x in accepted_inputs()[0]["surfaces"])
    site_values = sorted({x["value"] for sc in (scan_new, scan_314, scan_all) for x in sc["creation_sites"] if x["value"] is not None})
    dest_checks = OrderedDict([("$6972", destination_checks(rom, None, j6972["destinations_by_surface"].values())),
                               ("$77EC", destination_checks(rom, None, j77ec["destinations_by_surface"].values())),
                               ("$6C98", destination_checks(rom, None, j6c98["destinations"])),
                               ("$314F4", destination_checks(rom, 12, j314["destinations"]))])
    creation["surface_creation_map"] = surf_map
    creation["stage_surface_creation"] = OrderedDict(
        (str(sv), OrderedDict([("floor_handler", surf_map["$6972"][str(sv)]["handler"]), ("created_types", surf_map["$6972"][str(sv)]["created_types"]),
                               ("second_table_creates", surf_map["$77EC"][str(sv)]["created_types"])])) for sv in stage_surfaces)
    creation["site_values_not_in_r3_closure"] = sorted(set(site_values) - set(R3_CLOSURE_UNION))
    creation["destination_checks"] = dest_checks
    trigger_hits = [trigger_reach(rom, r) for r in (reached_new, reached_314, reached_all)]
    no_trigger = all(not h["setters_or_callers_reached"] and not h["calls_to_level_clear"] for h in trigger_hits)

    # verdicts
    def site_verdict(j, key_bounded, reaches):
        return OrderedDict([("bounded", key_bounded), ("verdict", "CLOSED (premise-conditional: P1-P6)" if key_bounded else "OPEN"),
                            ("reaches_out_of_table_word", False if key_bounded else None), ("reaches_level_clear_or_type_61", reaches)])

    b6972 = (31 not in dom["surfaces_present"]) and d2e0["all_equal"] and writers["D364"]["writes"] == feeders["expected"]["D364"]
    b6c98 = j6c98["all_ids_inside_table_or_special_case"] and not j6c98["interpreter_mismatches"]
    b314 = j314["all_ids_inside_sub_table"] and not j314["invalid_destinations"]
    verdicts = OrderedDict([
        ("$6972", site_verdict(j6972, b6972, False)),
        ("$77EC", site_verdict(j77ec, b6972, False)),
        ("$6C98", site_verdict(j6c98, b6c98, False)),
        ("$314F4", site_verdict(j314, b314, False)),
        ("all_four_bounded", bool(b6972 and b6c98 and b314)),
        ("can_introduce_types_outside_accepted_census", False),
        ("can_reach_level_clear_callback_or_type_61", False if no_trigger else None),
        ("object_creation_closure", OrderedDict([
            ("status", "PARTIAL"),
            ("basis", "the four named jumps are bounded and add no creation edge; the closure for the in-domain stages is unchanged "
                      "(%s). The route status stays '%s' only because two further resident computed jumps ($5E9A, $6695) are open and "
                      "out-of-domain placement lists are outside the accepted universe." % ("types " + ", ".join("$%02X" % t for t in union), st_a))])),
        ("u1", OrderedDict([("r3", "PARTIAL"), ("r4a", "PARTIAL"), ("route_A_status", st_a), ("route_A_why", why_a),
                            ("route_B_status", st_b), ("route_B_why", why_b),
                            ("change", "the four jumps no longer keep U1 open; U1 stays PARTIAL for the reasons named in route_*_why and R3's out-of-domain items")])),
    ])
    return OrderedDict([
        ("format", 1), ("task", "DECOMP-1D-R4A residual object dispatch closure"), ("rom_sha256", sha), ("generator", "tools/decomp1d_r4a_object_dispatch.py"),
        ("base_commit", BASE_COMMIT),
        ("evidence_tier", "static ROM-derived evidence (decoded instructions, recursive descent, byte-search census, fail-closed interpreter); "
                          "no controlled execution was needed and none is claimed; not hardware validation"),
        ("premises", PREMISES), ("reconciliation", reconciliation(rom)), ("header_domain", OrderedDict([
            ("table_physical", HEADER_TABLE), ("surfaces_present", dom["surfaces_present"]), ("surfaces_absent", dom["surfaces_absent"]),
            ("ids_by_surface", OrderedDict((str(k), v) for k, v in dom["ids_by_surface"].items())),
            ("surface_31_block_ids", dom["ids_by_surface"].get(31, [])),
            ("plane_flags_differ_for_ids", [r["id"] for r in dom["rows"] if len(r["flags"]) > 1]),
            ("bit_5_ids", [r["id"] for r in dom["rows"] if any(f & 0x20 for f in r["flags"])])])),
        ("feeders", feeders),
        ("jumps", OrderedDict([("$6972", j6972), ("$77EC", j77ec), ("$6C98", j6c98), ("$314F4", j314)])),
        ("adjacent_resident_jumps", OrderedDict([("$5E6F", five)] + list(adj.items()))),
        ("creation", creation), ("natural_closure", closures), ("union_closure", union),
        ("created_types_outside_accepted_placed_census", created_outside_census),
        ("verdicts", verdicts),
        ("stage_interface", stage_interface(rom, dom)),
        ("unresolved", [
            OrderedDict([("id", "R4A-1"), ("text", "two resident computed jumps in R3's frame-loop evidence, $5E9A (per-object callback pointer) and $6695 (script command index), are not named in R3's open list and are not closed here.")]),
            OrderedDict([("id", "R4A-2"), ("text", "indirect writers of D364/D353/D36B/D2E0 (R2 U5: register-addressed block moves with unresolved destinations) are not excluded.")]),
            OrderedDict([("id", "R4A-3"), ("text", "records outside the nine verified ones can change D2E0 (R3 U3); the bounds hold for the verified records only.")]),
            OrderedDict([("id", "R4A-4"), ("text", "the interrupt handler's transfers into slot-2 code were recorded, not followed (R3 P3).")]),
            OrderedDict([("id", "R4A-5"), ("text", "act-3 reachability through original gameplay rests on the accepted ring census (an upper bound over its recorded ring sources); not re-derived.")]),
            OrderedDict([("id", "R4B"), ("text", "termination of the graphics decompressor on out-of-table rows: not investigated here.")]),
        ]),
        ("baseline", OrderedDict([("structurally_classified_bytes", 156887), ("recovered_assembly_bytes", 13988), ("recovered_regions", 113),
                                  ("unknown_bytes", 367401), ("contradictory_claims", 0), ("changed_by_r4a", False)])),
    ])


def stage_interface(rom, dom):
    manifest, census, _ = accepted_inputs()
    stage_surfaces = sorted(int(s) for s in manifest["surfaces"])
    return OrderedDict([
        ("source_of_truth", "data/rom-cache/special-stages/implementation-manifest.json (not duplicated here)"),
        ("usable_now", ["stage metadata, entry gate, exit contract and zone indexing (manifest indexing/entry/exit)",
                        "the five stage layouts, block tables, start/camera/limits and ring/object placements (manifest stages, object-census)",
                        "the surface handlers for the surfaces listed below (manifest surfaces, surface_consumers)",
                        "object contracts $10 (monitors 4/5/6), $26, $2F, $31 (special-stage census, powerups, goal-ring, traversal audits)"]),
        ("stage_surfaces", stage_surfaces),
        ("stage_surfaces_that_reach_a_residual_dispatcher", OrderedDict([
            ("$6972/$77EC", "all of them: every stage surface dispatches through the shared floor/side tables (accepted, shared engine)"),
            ("$6C98", "none: surface 16 is %s in the stage layouts" % ("present" if 16 in stage_surfaces else "not present")),
            ("$314F4", "none: surface 23 is %s in the stage layouts" % ("present" if 23 in stage_surfaces else "not present"))])),
        ("residual_dispatchers_affecting_ordinary_implementation", False),
        ("newly_established_object_creation_behaviour", "none"),
    ])


# --- 9. rendering, checking, command line --------------------------------------------------------------------------------------
_fmt, dumps = R3._fmt, R3.dumps


def render_block(doc):
    v = doc["verdicts"]
    lines = [BEGIN, "", "| Dispatcher | Bound | Verdict |", "|---|---|---|"]
    j = doc["jumps"]
    lines.append("| `$6972` floor dispatcher | D364 & $1F; surfaces present %s; $1F absent | **%s** |" % (
        ",".join(str(s) for s in doc["header_domain"]["surfaces_present"]), v["$6972"]["verdict"]))
    lines.append("| `$77EC` second dispatcher | same index, same domain | **%s** |" % v["$77EC"]["verdict"])
    lines.append("| `$6C98` surface-16 sub-dispatcher | block ids %s | **%s** |" % (
        ", ".join(str(b) for b in j["$6C98"]["surface_16_block_ids"]), v["$6C98"]["verdict"]))
    lines.append("| `$314F4` bank-12 callback dispatch | gate surface $17, block ids %d-%d, %d of 28 entries | **%s** |" % (
        j["$314F4"]["gate_block_ids"][0], j["$314F4"]["gate_block_ids"][-1], len(j["$314F4"]["gate_block_ids"]), v["$314F4"]["verdict"]))
    lines += ["", "| Question | Answer |", "|---|---|",
              "| Completely bounded and resolved | %s |" % ("yes, all four (premise-conditional)" if v["all_four_bounded"] else "no"),
              "| Adds object types beyond R3's closure (itself a superset of the accepted placed census) | %s |" % ("no" if not v["can_introduce_types_outside_accepted_census"] else "yes"),
              "| Reaches the level-clear callback or type $61 | %s |" % ("no" if v["can_reach_level_clear_callback_or_type_61"] is False else "open"),
              "| Object-creation closure | **%s** |" % v["object_creation_closure"]["status"],
              "| U1 | **%s** (route A %s, route B %s) |" % (v["u1"]["r4a"], v["u1"]["route_A_status"], v["u1"]["route_B_status"]),
              "", "Closure types (all five stages, with the new edges): %s." % ", ".join("$%02X" % t for t in doc["union_closure"]), "", END_MARK]
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
    if not args.rom:
        print("pass the ROM path or set SONIC_CHAOS_ROM", file=sys.stderr)
        return 2
    rom = Path(args.rom).read_bytes()
    try:
        R3.verify_rom(rom)
    except ValueError as e:
        print("the ROM is not the canonical Europe v1.2 image: %s" % e, file=sys.stderr)
        return 2
    out = Path(args.output)
    doc = build(rom)
    text = dumps(doc)
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
    print("wrote %s: closure=%s all_four_bounded=%s" % (out, doc["verdicts"]["object_creation_closure"]["status"], doc["verdicts"]["all_four_bounded"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

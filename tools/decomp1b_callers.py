#!/usr/bin/env python3
"""DECOMP-1B: engine caller recovery evidence.

    python tools/decomp1b_callers.py /path/to/SonicChaos.sms [--output data/decomp1b/callers.json]

Everything is recomputed from the ROM, ``asm/recovered/regions.json`` and the DECOMP-1A review; nothing is
trusted from a cache. Four sections are written:

* ``vector_reachability``: recursive descent over the resident engine (banks 0/1) from the three Z80/SMS
  hardware entry points (reset ``$0000``, IM 1 interrupt ``$0038``, NMI ``$0066``). It follows CALL / JP / JR /
  DJNZ and fall-through only; it never follows an indirect jump, so what it reaches is statically reachable
  CODE, not an execution trace. This is the root that DECOMP-1A lacked: its callers had to be byte-verified
  assembly, and no assembly covered the boot code or the main loop.
* ``dependency_map``: for each priority range, the entry, every decoded call site that targets it, whether
  that site is recovered assembly, whether the vector descent reaches it, and the compressed chain of
  transfers from a hardware vector. Entries nothing decodable calls are reported as such.
* ``candidates``: what recovering each candidate caller region would add to the DECOMP-1A fixed point
  (simulated against the evidence as it stood before DECOMP-1B).
* ``recovered_callers``: for each region DECOMP-1B registered, the proof of its entries, instruction
  boundaries, exits, call/jump targets and the check that no byte is left unreached (no embedded table).
"""
import argparse
import json
import sys
from collections import OrderedDict, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1a_review as RV  # noqa: E402
import rom_flow as F  # noqa: E402
import rom_ledger as RL  # noqa: E402

OUTPUT = ROOT / "data" / "decomp1b" / "callers.json"
RESIDENT = 0x8000
VECTORS = ((0x0000, "reset"), (0x0038, "IM 1 interrupt"), (0x0066, "NMI"))

# Regions registered by DECOMP-1B: (name, start, end, entries). Entries are the addresses control flow
# arrives at from outside the region; every other byte must be reached from them.
RECOVERED = (
    ("main_loop_dispatch", 0x1333, 0x1365, (0x1333,)),
    ("main_loop_bit1_handler", 0x1673, 0x1696, (0x1673,)),
    ("gameplay_frame_update", 0x16B8, 0x1753, (0x16B8, 0x16EF, 0x173F)),
    ("level_load_sequence", 0x2934, 0x297E, (0x2934,)),
)

# Priority ranges from the DECOMP-1B brief (audit bounds from DECOMP-1A section 8) and the entries inside them.
PRIORITY = (
    ("camera_update", 0x04C90, 0x04CB0, (0x4C90,)),
    ("camera_limit_x", 0x04CB0, 0x04CF7, (0x4CB0,)),
    ("camera_limit_y", 0x04CF7, 0x04D3E, (0x4CF7,)),
    ("camera_to_vdp", 0x04D3E, 0x04D5D, (0x4D3E,)),
    ("camera_follow", 0x05832, 0x05935, (0x5832,)),
    ("camera_follow_init", 0x05935, 0x05956, (0x5935,)),
    ("player_update", 0x0361D, 0x03657, (0x361D,)),
    ("player_wrapper_0A", 0x03901, 0x0393B, (0x3901,)),
    ("player_wrapper_0E_14", 0x03A37, 0x03A59, (0x3A37, 0x3A48)),
    ("level_header_loader", 0x04FDC, 0x05082, (0x4FDC,)),
)

# Candidate callers examined for entry value (region extents proved by confined descent from their entries).
CANDIDATES = RECOVERED + (
    ("level_intro_setup", 0x06C7, 0x0719, (0x06C7,)),
    ("mode_handler_1696", 0x1696, 0x16B8, (0x1696,)),
    ("player_state_callback_stubs", 0x0380, 0x044F, tuple(range(0x380, 0x44F, 3))),
)

STUB_TABLE = (0x0380, 0x044F)

# Regions DECOMP-1C added later; this report describes the evidence as it stood before them.
LATER_PREFIXES = ("callback_stubs_", "dispatch_target_")


def later_regions(root=ROOT):
    regions = json.loads((root / "asm" / "recovered" / "regions.json").read_text(encoding="utf-8"))
    return {r["name"] for r in regions if r["name"].startswith(LATER_PREFIXES)}


def hx(v):
    return "$%04X" % v if v < 0x10000 else "$%05X" % v


def decode_all(rom, start, end):
    out, p = OrderedDict(), start
    while p < end:
        d = F.decode(rom, p)
        if F.is_invalid(d) or p + d.len > end:
            return None
        out[p] = d
        p += d.len
    return out


def vector_descent(rom):
    """Breadth-first descent from the hardware vectors over [0, $8000). Returns (instructions, parent, indirect, invalid).

    Roots are closed in order (reset first), so a byte reachable from reset is explained by its shortest path from
    reset rather than by whichever interrupt path was found first. ``parent`` maps an instruction to
    ``(previous instruction, "fall" | op name)``.
    """
    ins, parent, indirect, invalid = {}, {}, [], []
    for root, _ in VECTORS:
        queue = deque([(root, None)])
        while queue:
            p, via = queue.popleft()
            if p in ins or not 0 <= p < RESIDENT:
                continue
            d = F.decode(rom, p)
            if F.is_invalid(d) or p + d.len > RESIDENT:
                invalid.append(p)
                continue
            ins[p] = d.len
            parent[p] = via
            if F.is_indirect_jump(d):
                indirect.append(p)
            if d.op in F.TRANSFER_OPS:
                target = F._addr_operand(d)
                if target is not None:
                    t = F.resolve_target(p, target)
                    if t is not None and t < RESIDENT:
                        queue.append((t, (p, d.op.name)))
            if not F.is_terminal(d):
                queue.append((p + d.len, (p, "fall")))
    return ins, parent, sorted(indirect), sorted(invalid)


def chain(parent, target):
    """Transfers (not fall-through steps) from a hardware vector to ``target``, oldest first."""
    steps, p, seen = [], target, set()
    while p is not None and p not in seen:
        seen.add(p)
        via = parent.get(p)
        if via is None:
            steps.append((p, "vector"))
            break
        site, kind = via
        if kind != "fall":
            steps.append((p, "%s at %s" % (kind, hx(site))))
        p = site
    return steps[::-1]


def targets_of(rom, instructions):
    """{target_file_offset: [(site, op)]} over instruction offsets (resident, or same-bank slot 2)."""
    out = defaultdict(list)
    for p in instructions:
        d = F.decode(rom, p)
        if d.op in F.TRANSFER_OPS:
            target = F._addr_operand(d)
            if target is not None:
                t = F.resolve_target(p, target)
                if t is not None:
                    out[t].append((p, d.op.name))
    return out


class Classes:
    def __init__(self, ledger):
        self.segments = [(s["start"], s["end"], s["primary"]) for s in ledger["segments"]]

    def at(self, offset):
        lo, hi = 0, len(self.segments) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            s, e, c = self.segments[mid]
            if offset < s:
                hi = mid - 1
            elif offset >= e:
                lo = mid + 1
            else:
                return c
        return "UNKNOWN"


def owner_entry(call_targets, site):
    """Nearest preceding CALL target at or below ``site`` (the routine that most plausibly contains it)."""
    best = None
    for t in call_targets:
        if t <= site and (best is None or t > best):
            best = t
    return best


SCRIPT_TABLE = 0x65BA     # per-object-type pointer to its state-script pointer table (object_animation_engine, $651D-$6533)
SCRIPT_BANK_BASE = 0x30000  # bank 12 (file $30000) is mapped at $8000 while the player's scripts run ($3637-$363C)


def player_state_scripts(rom, types=(1, 2)):
    """{(type, state): (script_cpu, span_end_cpu)} from the type table at $65BA, read from the ROM.

    The state table of a type starts at its pointer; its length is the point where the first script starts
    (the tables are followed immediately by script data). A script runs to the next script start in the bank.
    """
    word = lambda cpu: rom[SCRIPT_BANK_BASE + cpu - 0x8000] | rom[SCRIPT_BANK_BASE + cpu - 0x7FFF] << 8
    tables = {}
    for ty in types:
        base = rom[SCRIPT_TABLE + 2 * (ty - 1)] | rom[SCRIPT_TABLE + 2 * (ty - 1) + 1] << 8
        n = (word(base) - base) // 2           # upper bound: the first script starts after the table
        while True:
            m = (min(w for w in (word(base + 2 * i) for i in range(n)) if base <= w < 0xC000) - base) // 2
            if m == n:
                break
            n = m
        tables[ty] = (base, [word(base + 2 * i) for i in range(n)])
    starts = sorted({a for _, ws in tables.values() for a in ws})
    out = {}
    for ty, (base, ws) in tables.items():
        for state, a in enumerate(ws):
            nxt = next((x for x in starts if x > a), a + 0x80)
            out[(ty, state)] = (a, nxt)
    return out


def script_word_census(rom, stubs, scripts):
    """Where a JP-stub address occurs as a little-endian word inside a player state script (supporting evidence only:
    it is not a parse of the script, so it shows the vector is present in that state's script bytes)."""
    found = []
    for st in stubs:
        for (ty, state), (a, b) in sorted(scripts.items()):
            hits = [cpu for cpu in range(a, b - 1)
                    if rom[SCRIPT_BANK_BASE + cpu - 0x8000] == st & 255 and rom[SCRIPT_BANK_BASE + cpu - 0x7FFF] == st >> 8]
            if hits:
                first = SCRIPT_BANK_BASE + hits[0] - 0x8000
                found.append(OrderedDict([("stub", st), ("type", ty), ("state", state), ("script_cpu", a),
                                          ("occurrences", len(hits)), ("first_word_offset_in_script", hits[0] - a),
                                          ("first_immediately_after_ff05_selector", rom[first - 4] == 0xFF and rom[first - 3] == 0x05)]))
    return found


def dependency_map(rom, regions, ins, parent, review):
    scripts = player_state_scripts(rom)
    recovered = {}
    for r in F.code_regions(regions):
        for p, n, _ in F.region_instructions(rom, r):
            recovered[p] = r["name"]
    rec_targets = targets_of(rom, recovered)
    vec_targets = targets_of(rom, ins)
    call_targets = sorted({t for t, sites in vec_targets.items() if any(op == "CALL" for _, op in sites)}
                          | {v for v, _ in VECTORS})
    unresolved = {tuple(u["bounds"]): u for u in review["unresolved"]}
    rows = []
    for name, lo, hi, entries in PRIORITY:
        row = OrderedDict([("name", name), ("range", [lo, hi])])
        cluster = next((u for b, u in unresolved.items() if b[0] <= lo and hi <= b[1]), None)
        row["decomp1a_status"] = ("unresolved: " + cluster["reason"]) if cluster else "resolved in the supplied review"
        row["entries"] = []
        for e in entries:
            callers = []
            for site, op in sorted(set(list(rec_targets.get(e, [])) + list(vec_targets.get(e, [])))):
                callers.append(OrderedDict([
                    ("site", site), ("op", op), ("owner_entry", owner_entry(call_targets, site)),
                    ("site_is_recovered_assembly", site in recovered),
                    ("site_reached_from_vector", site in ins)]))
            if e in ins:
                steps = chain(parent, e)
            else:
                steps = []
            stubs = [s for s in range(STUB_TABLE[0], STUB_TABLE[1], 3)
                     if rom[s] == 0xC3 and rom[s + 1] | rom[s + 2] << 8 == e]
            words = script_word_census(rom, stubs, scripts)
            row["entries"].append(OrderedDict([
                ("entry", e), ("direct_callers", callers),
                ("reached_from_hardware_vector", e in ins),
                ("transfer_chain_from_vector", [OrderedDict([("to", a), ("via", v)]) for a, v in steps]),
                ("jp_stub_entries", stubs),
                ("stub_word_in_state_scripts", words),
                ("blocked_only_by", "no decoded CALL/JP/JR reaches it" if not callers else
                 "its callers are in unrecovered code (none is byte-verified assembly)"
                 if not any(c["site_is_recovered_assembly"] for c in callers) else "none")]))
        rows.append(row)
    return rows


def prove_region(rom, regions, classes, name, start, end, entries):
    """Entry, boundary and extent proof for one code region (does not trust regions.json)."""
    insns = decode_all(rom, start, end)
    proof = OrderedDict([("name", name), ("bounds", [start, end])])
    if insns is None:
        proof["error"] = "bytes do not decode to whole instructions inside the bounds"
        return proof
    reached, notes = F.descend(rom, list(entries), start, end)
    last = list(insns.items())[-1]
    proof["instructions"] = len(insns)
    proof["bytes"] = end - start
    proof["entries"] = list(entries)
    proof["every_byte_reached_from_entries"] = sorted(reached) == sorted(insns)
    proof["unreached_instruction_offsets"] = [p for p in insns if p not in reached]
    proof["final_instruction_is_terminal"] = F.is_terminal(last[1])
    proof["stop_notes"] = [[k, p] for k, p in notes]
    data_overlap = [r["name"] for r in regions if r["kind"] == "data" and r["start"] < end and start < r["end"]]
    proof["touches_recovered_data"] = data_overlap
    own = set(insns)
    loads_inside = []
    transfers, exits = [], []
    for p, d in insns.items():
        for kind, value in d.operands:
            if kind.name == "IMM" and start <= value < end and d.op.name == "LD":
                loads_inside.append([p, value])
        if d.op in F.TRANSFER_OPS or d.op == F.OP.RET or F.is_indirect_jump(d):
            target = F._addr_operand(d) if d.op in F.TRANSFER_OPS else None
            resolved = F.resolve_target(p, target) if target is not None else None
            internal = resolved is not None and start <= resolved < end
            transfers.append(OrderedDict([
                ("site", p), ("op", d.op.name), ("conditional", F._has_cond(d)),
                ("target", target), ("target_offset", resolved), ("internal", internal),
                ("target_class_baseline", None if resolved is None or internal else classes.at(resolved)),
                ("bank_note", "slot-2 target from resident code: bank chosen at run time" if target is not None and resolved is None else None)]))
            if not internal and F.is_terminal(d):
                exits.append(p)
    proof["table_loads_inside_region"] = loads_inside
    proof["transfers"] = transfers
    proof["fall_through_off_end"] = not F.is_terminal(last[1])
    # a branch target that is not an instruction start would invalidate the boundaries
    proof["internal_targets_are_instruction_starts"] = all(t["target_offset"] in own for t in transfers if t["internal"])
    return proof


def entry_support(rom, regions, ins, parent, start, end, entries):
    """Support for each external entry: decoded call sites outside the region plus the vector chain."""
    vec_targets = targets_of(rom, ins)
    recovered = {}
    for r in F.code_regions(regions):
        if r["start"] == start and r["end"] == end:
            continue
        for p, n, _ in F.region_instructions(rom, r):
            recovered[p] = r["name"]
    rec_targets = targets_of(rom, recovered)
    out = []
    for e in entries:
        sites = sorted(set(list(vec_targets.get(e, [])) + list(rec_targets.get(e, []))))
        outside = [(s, op) for s, op in sites if not start <= s < end]
        out.append(OrderedDict([
            ("entry", e),
            ("external_sites", [OrderedDict([("site", s), ("op", op), ("recovered_assembly", s in recovered)])
                                for s, op in outside]),
            ("reached_from_hardware_vector", e in ins),
            ("transfer_chain_from_vector", [OrderedDict([("to", a), ("via", v)]) for a, v in chain(parent, e)])
            if e in ins else []]))
    return out


def simulate_candidates(rom, review_without):
    """What each candidate would add on top of the pre-DECOMP-1B evidence."""
    names = {c[0] for c in RECOVERED} | later_regions()
    base = review_without
    base_bytes = sum(c["end"] - c["start"] for r in base["code_flow_reviews"] for c in r["claims"])
    base_seeds = {s["offset"] for r in base["code_flow_reviews"] for s in r["seeds"]}
    rows = []
    for name, lo, hi, entries in CANDIDATES:
        extra = [OrderedDict([("name", name), ("start", lo), ("end", hi), ("bank", lo // RL.BANK_SIZE),
                              ("kind", "code"), ("bytes", hi - lo), ("instructions", 0), ("file", name + ".asm")])]
        try:
            doc = RV.build(rom, ROOT, extra_regions=extra, drop_regions=names, script_seeds=False)
        except Exception as exc:  # a candidate that cannot be simulated is reported, not hidden
            rows.append(OrderedDict([("name", name), ("bounds", [lo, hi]), ("error", str(exc))]))
            continue
        claimed = sum(c["end"] - c["start"] for r in doc["code_flow_reviews"] for c in r["claims"])
        seeds = {s["offset"] for r in doc["code_flow_reviews"] for s in r["seeds"]}
        rows.append(OrderedDict([
            ("name", name), ("bounds", [lo, hi]), ("region_bytes", hi - lo),
            ("new_supported_entries", sorted(seeds - base_seeds)),
            ("new_code_bytes_classified", claimed - base_bytes),
            ("unresolved_clusters_after", len(doc["unresolved"]))]))
    extra = [OrderedDict([("name", n), ("start", lo), ("end", hi), ("bank", lo // RL.BANK_SIZE), ("kind", "code"),
                          ("bytes", hi - lo), ("instructions", 0), ("file", n + ".asm")]) for n, lo, hi, _ in RECOVERED]
    doc = RV.build(rom, ROOT, extra_regions=extra, drop_regions=names, script_seeds=False)
    claimed = sum(c["end"] - c["start"] for r in doc["code_flow_reviews"] for c in r["claims"])
    seeds = {s["offset"] for r in doc["code_flow_reviews"] for s in r["seeds"]}
    combined = OrderedDict([("regions", [n for n, _, _, _ in RECOVERED]),
                            ("new_supported_entries", sorted(seeds - base_seeds)),
                            ("new_code_bytes_classified", claimed - base_bytes),
                            ("unresolved_clusters_after", len(doc["unresolved"])),
                            ("unresolved_unknown_bytes_after", sum(u["unknown_bytes"] for u in doc["unresolved"]))])
    return OrderedDict([("baseline_code_bytes_claimed", base_bytes), ("baseline_supported_entries", len(base_seeds)),
                        ("baseline_unresolved_unknown_bytes", sum(u["unknown_bytes"] for u in base["unresolved"])),
                        ("candidates", rows), ("selected_combined", combined)])


def build(rom, root=ROOT):
    regions = json.loads((root / "asm" / "recovered" / "regions.json").read_text(encoding="utf-8"))
    later = later_regions(root)
    ledger = RL.build_ledger(rom, root, reviewed=False, drop_regions=later)
    classes = Classes(ledger)
    ins, parent, indirect, invalid = vector_descent(rom)
    names = {c[0] for c in RECOVERED} | later
    # the dependency map describes why DECOMP-1A could not reach the ranges, so it uses the evidence without 1B
    review_without = RV.build(rom, root, drop_regions=names, script_seeds=False)
    prior_regions = [r for r in regions if r["name"] not in names]
    doc = OrderedDict()
    doc["format"] = 1
    doc["rom_sha256"] = RL.ROM_SHA256
    doc["generator"] = "tools/decomp1b_callers.py"
    doc["vector_reachability"] = OrderedDict([
        ("roots", [OrderedDict([("address", a), ("name", n)]) for a, n in VECTORS]),
        ("scope", "resident engine, banks 0 and 1 ($0000-$7FFF); CALL/JP/JR/DJNZ and fall-through only"),
        ("instructions", len(ins)), ("bytes", sum(ins.values())),
        ("indirect_jumps_not_followed", indirect), ("undecodable_stops", invalid),
        ("evidence_tier", "static control-flow evidence (statically reachable CODE), not an execution trace")])
    doc["dependency_map"] = dependency_map(rom, prior_regions, ins, parent, review_without)
    doc["candidates"] = simulate_candidates(rom, review_without)
    recovered = []
    for name, lo, hi, entries in RECOVERED:
        r = prove_region(rom, regions, classes, name, lo, hi, entries)
        r["entry_support"] = entry_support(rom, regions, ins, parent, lo, hi, entries)
        r["registered"] = any(x["name"] == name and x["start"] == lo and x["end"] == hi for x in regions)
        recovered.append(r)
    doc["recovered_callers"] = recovered
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("rom", nargs="?", default=str(RL.DEFAULT_ROM))
    ap.add_argument("--output", default=str(OUTPUT))
    args = ap.parse_args(argv)
    doc = build(RL.load_rom(args.rom))
    Path(args.output).write_bytes((json.dumps(doc, indent=1) + "\n").encode("utf-8"))
    print("vector-reachable instructions: %d; candidates: %d; recovered callers: %d"
          % (doc["vector_reachability"]["instructions"], len(doc["candidates"]["candidates"]), len(doc["recovered_callers"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())

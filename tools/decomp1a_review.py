#!/usr/bin/env python3
"""Build data/rom-ledger/reviewed-ranges.json (DECOMP-1A).

    python tools/decomp1a_review.py /path/to/SonicChaos.sms [--output data/rom-ledger/reviewed-ranges.json]

Starting from the hash-verified audit ranges that state no code/data kind
(``unclassified_range_claims``), this proposes CODE claims only where the ROM
itself supports static reachability:

* an entry point is the target of a CALL/JP/JR/DJNZ at an instruction of
  byte-verified recovered code (or of a claim this tool already supported), or is a
  word of a recovered dispatch table whose address recovered code loads and
  whose consumer jumps through ``JP (HL)``;
* recursive descent from the supported entries, confined to the audit range(s),
  fetches each claimed byte as an instruction and never touches a recovered
  DATA region.

Only bytes that are UNKNOWN in the baseline ledger are claimed. Everything else
is written to ``unresolved`` with the evidence still missing. The ledger
generator (``rom_ledger.import_reviewed``) re-verifies every entry; this file is
a proposal, not trusted input.
"""
import argparse
import json
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import rom_flow as F  # noqa: E402
import player_scripts as PS  # noqa: E402
import rom_ledger as RL  # noqa: E402

DISPATCH_TABLES = ("floor_dispatch_table", "object_floor_dispatch",
                   "animation_command_table", "object_lifecycle_dispatch")
OUTPUT = ROOT / RL.REVIEWED


def clusters(ranges):
    """Merge audit ranges that overlap (not merely touch) into clusters."""
    out = []
    for r in sorted(ranges, key=lambda r: (r["start"], r["end"], r["name"])):
        if out and r["start"] < out[-1]["end"]:
            out[-1]["end"] = max(out[-1]["end"], r["end"])
            out[-1]["audit_ranges"].append(r)
        else:
            out.append({"start": r["start"], "end": r["end"], "audit_ranges": [r]})
    return out


def runs_of(offsets):
    out = []
    for lo, hi in offsets:
        if out and out[-1][1] == lo:
            out[-1] = (out[-1][0], hi)
        else:
            out.append((lo, hi))
    return out


def build(rom, root=ROOT, extra_regions=(), drop_regions=(), script_seeds=True):
    """``extra_regions``/``drop_regions`` (DECOMP-1B) let a caller ask what a hypothetical recovered
    region would support, or what the evidence was before one existed; ``script_seeds=False`` (DECOMP-1C) leaves
    out the player-script dispatch seeds. The defaults change nothing."""
    baseline = RL.build_ledger(rom, root, reviewed=False, drop_regions=drop_regions)
    regions = json.loads((root / "asm" / "recovered" / "regions.json").read_text(encoding="utf-8"))
    regions = [r for r in regions if r["name"] not in drop_regions] + list(extra_regions)
    by_name = {r["name"]: r for r in regions}
    unknown = set()
    for s in baseline["segments"]:
        if s["primary"] == "UNKNOWN":
            unknown.update(range(s["start"], s["end"]))
    recovered_data = set()
    for r in regions:
        if r["kind"] == "data":
            recovered_data.update(range(r["start"], r["end"]))
    todo = [c for c in clusters(baseline["unclassified_range_claims"]["ranges"])
            if any(b in unknown for b in range(c["start"], c["end"]))]

    proven = {}
    for r in F.code_regions(regions):
        for p, n, _ in F.region_instructions(rom, r):
            proven[p] = n
    # dispatch-table seeds with their load proofs
    table_seeds = {}
    for name in DISPATCH_TABLES:
        region = by_name[name]
        loaders = sorted(p for p in proven if _loads(rom, p, region["start"]))
        if not loaders or not _consumer_jumps(rom, regions, loaders[0]):
            continue
        for i in range((region["end"] - region["start"]) // 2):
            table_seeds.setdefault(RL.dispatch_table_word(rom, region, i),
                                   {"table": name, "index": i, "load_site": loaders[0]})

    # DECOMP-1C: words that parsed player scripts make the engine execute (callback vectors and command operands)
    for off, via in (PS.dispatch_seeds(rom).items() if script_seeds else ()):
        table_seeds.setdefault(off, {"player_script": via})

    state = {id(c): {"seeds": OrderedDict(), "reached": {}} for c in todo}
    changed = True
    while changed:
        changed = False
        sites = defaultdict(list)
        for p in sorted(proven):
            d = F.decode(rom, p)
            if d.op in F.TRANSFER_OPS:
                target = F._addr_operand(d)
                if target is not None:
                    t = F.resolve_target(p, target)
                    if t is not None:
                        sites[t].append(p)
        for c in todo:
            st = state[id(c)]
            for off in range(c["start"], c["end"]):
                if off in st["seeds"]:
                    continue
                # a proof site that is itself one of this cluster's unknown bytes would be self-supporting
                outside = [x for x in sites.get(off, ()) if not (c["start"] <= x < c["end"] and x in unknown)]
                if outside:
                    st["seeds"][off] = {"site": outside[0]}
                elif off in table_seeds:
                    st["seeds"][off] = table_seeds[off]
            if not st["seeds"]:
                continue
            reached, notes = F.descend(rom, list(st["seeds"]), c["start"], c["end"])
            if reached != st["reached"]:
                st["reached"] = reached
                st["notes"] = notes
            for a, n in reached.items():
                if a not in proven and all(b in unknown for b in range(a, a + n)):
                    proven[a] = n
                    changed = True

    reviews, unresolved = [], []
    for c in todo:
        st = state[id(c)]
        reached = st["reached"]
        claimed = [(a, a + n) for a, n in sorted(reached.items())
                   if all(b in unknown for b in range(a, a + n))]
        if any(b in recovered_data for a, n in reached.items() for b in range(a, a + n)):
            raise ValueError("flow reaches recovered DATA in cluster %s" % RL.hx(c["start"]))
        runs = runs_of(claimed)
        left = runs_of([(b, b + 1) for b in range(c["start"], c["end"])
                        if b in unknown and not any(lo <= b < hi for lo, hi in runs)])
        audit = [OrderedDict([("start", a["start"]), ("end", a["end"]), ("name", a["name"]),
                              ("source", a["source"])]) for a in c["audit_ranges"]]
        if runs:
            reviews.append(OrderedDict([
                ("id", len(reviews)), ("bounds", [c["start"], c["end"]]),
                ("bank", c["start"] // RL.BANK_SIZE), ("audit_ranges", audit),
                ("seeds", [OrderedDict([("offset", o), ("via", v)]) for o, v in sorted(st["seeds"].items())]),
                ("claims", [OrderedDict([("start", lo), ("end", hi), ("primary", "CODE"), ("subtype", "routine")])
                            for lo, hi in runs]),
                ("verification", "static recursive descent from the supported entries, confined to bounds, fetches every claimed "
                                 "byte as an instruction and reaches no recovered DATA region"),
                ("uncertainty", "statically reachable CODE (control-flow evidence); not an execution trace; the routine's purpose and "
                                "any subsystem label are audit text, not established here"),
            ]))
        if left:
            unresolved.append(OrderedDict([
                ("bounds", [c["start"], c["end"]]), ("bank", c["start"] // RL.BANK_SIZE),
                ("audit_ranges", audit),
                ("unknown_runs", [[lo, hi] for lo, hi in left]),
                ("unknown_bytes", sum(hi - lo for lo, hi in left)),
                ("reason", _reason(c, st, runs)),
                ("evidence_needed", _needed(c, st))]))
    return OrderedDict([("format", 1), ("rom_sha256", RL.ROM_SHA256),
                        ("generator", "tools/decomp1a_review.py"),
                        ("code_flow_reviews", reviews), ("unresolved", unresolved)])


def _loads(rom, p, address):
    d = F.decode(rom, p)
    return d.op == F.OP.LD and any(k.name == "IMM" and v == address for k, v in d.operands)


def _consumer_jumps(rom, regions, load_site):
    for r in F.code_regions(regions):
        if r["start"] <= load_site < r["end"]:
            return any(F.is_indirect_jump(d) for p, _, d in F.region_instructions(rom, r) if p > load_site)
    return False


def _reason(c, st, runs):
    if not st["seeds"]:
        bank = c["start"] // RL.BANK_SIZE
        if bank >= 2:
            return ("no statically supported entry point: no CALL/JP from byte-verified code in the same bank targets it, "
                    "and it is not a word of a recovered dispatch table")
        return "no statically supported entry point: no CALL/JP from byte-verified or already-supported code targets it"
    if runs:
        return "entry points supported, but flow does not reach every byte of the audited range"
    return "entry points supported but they fetch no UNKNOWN byte"


def _needed(c, st):
    if c["start"] // RL.BANK_SIZE >= 2:
        return ("a bank-resolved entry: a CALL/JP from verified code in the same bank, a decoded "
                "callback/script-pointer table entry, or a Z80 PC trace with the mapper state; or a pointer "
                "consumer that fixes the extent if the range is a table")
    return ("a supported caller (CALL/JP/JR from verified code), a decoded jump-table consumer, or a Z80 PC trace; "
            "for a table, an instruction that loads its address and indexes it")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("rom", nargs="?", default=str(RL.DEFAULT_ROM))
    ap.add_argument("--output", default=str(OUTPUT))
    args = ap.parse_args(argv)
    doc = build(RL.load_rom(args.rom))
    Path(args.output).write_bytes((json.dumps(doc, indent=1) + "\n").encode("utf-8"))
    n = sum(c["end"] - c["start"] for r in doc["code_flow_reviews"] for c in r["claims"])
    u = sum(x["unknown_bytes"] for x in doc["unresolved"])
    print("reviews: %d, CODE bytes claimed: %d, unresolved clusters: %d, unresolved UNKNOWN bytes: %d"
          % (len(doc["code_flow_reviews"]), n, len(doc["unresolved"]), u))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""DECOMP-1C: which JP stubs at $0380-$044F are supported by ROM structure and verified control flow.

    python tools/decomp1c_callbacks.py /path/to/SonicChaos.sms

Writes ``data/decomp1c/callbacks.json`` (every parsed player-script callback and executed word, the support for each
stub and the unproven stubs) and ``data/decomp1c/derived-regions.json`` (the runs of supported stubs and the handler
routines reached from them or from script operands, which ``tools/recover.py`` registers as recovered assembly).

A stub is *supported* when at least one of these holds, each recomputed from the ROM:

* a player state script (parsed by ``tools/player_scripts.py`` the way the animation engine reads it) stores its
  address into the callback vector ``IX+12/13`` (a record's callback field, ``FF 05`` or ``FF 0D``), which player update
  executes with ``JP (HL)`` at ``$5E9A``;
* a player state script has the engine execute its address through ``JP (HL)`` as a command operand
  (``FF 01``, ``FF 05``, ``FF 08``);
* a CALL/JP/JR in byte-verified recovered assembly (other than the stub regions this tool derives) or in code
  statically reachable from a hardware vector targets it.

The stub table's geometry (consecutive ``JP`` instructions) is reported as a structural fact; it is not itself
evidence that an individual stub is entered, so unsupported stubs are listed and left UNKNOWN.
"""
import argparse
import json
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1a_review as RV  # noqa: E402
import decomp1b_callers as B1  # noqa: E402
import player_scripts as PS  # noqa: E402
import rom_flow as F  # noqa: E402
import rom_ledger as RL  # noqa: E402

OUTPUT = ROOT / "data" / "decomp1c" / "callbacks.json"
DERIVED = ROOT / "data" / "decomp1c" / "derived-regions.json"
STUB_PREFIX = "callback_stubs_"
HANDLER_PREFIX = "dispatch_target_"
JP = 0xC3


def hx(v):
    return "$%04X" % v


def is_stub(rom, a):
    return a + 3 <= F.RESIDENT_END and rom[a] == JP and (rom[a + 1] | rom[a + 2] << 8) < F.RESIDENT_END


def stub_geometry(rom, anchors):
    """Maximal run of consecutive 3-byte JP instructions containing the anchor stubs (a structural fact)."""
    lo = min(anchors)
    hi = max(anchors)
    while is_stub(rom, lo - 3):
        lo -= 3
    while is_stub(rom, hi + 3):
        hi += 3
    return lo, hi + 3


def vector_targets_of(rom, regions, ins):
    """{resident target: [(site, op, source)]} from recovered CODE regions and vector-reachable instructions."""
    out = defaultdict(list)
    recovered = set()
    for r in F.code_regions(regions):
        for p, n, d in F.region_instructions(rom, r):
            recovered.add(p)
            if d.op in F.TRANSFER_OPS:
                a = F._addr_operand(d)
                t = F.resolve_target(p, a) if a is not None else None
                if t is not None and t < F.RESIDENT_END:
                    out[t].append((p, d.op.name, "recovered assembly"))
    for p in ins:
        if p in recovered:
            continue
        d = F.decode(rom, p)
        if d.op in F.TRANSFER_OPS:
            a = F._addr_operand(d)
            t = F.resolve_target(p, a) if a is not None else None
            if t is not None and t < F.RESIDENT_END:
                out[t].append((p, d.op.name, "hardware-vector descent"))
    return out


def region_dict(name, lo, hi):
    return OrderedDict([("name", name), ("start", lo), ("end", hi), ("bank", lo // RL.BANK_SIZE), ("kind", "code"),
                        ("bytes", hi - lo), ("instructions", 0), ("file", name + ".asm")])


def handler_regions(rom, root, stub_runs, derived_names):
    """Reviewed CODE runs that are entered only through player-callback dispatch and prove out as whole routines.

    A run qualifies when every seed of its review is a JP-stub destination (the JP is in a supported stub run) or a
    word a parsed player script makes the engine execute, at least one such entry lies inside the run, confined
    descent from the entries inside the run fetches every byte of it, its last instruction is terminal and every
    relative branch stays inside the run.
    """
    extra = [region_dict("%s%04X" % (STUB_PREFIX, a), a, b) for a, b in stub_runs]
    review = RV.build(rom, root, extra_regions=extra, drop_regions=derived_names)

    def stub_site(site):
        return any(a <= site < b for a, b in stub_runs)

    out = []
    for x in review["code_flow_reviews"]:
        if not all("player_script" in s["via"] or ("site" in s["via"] and stub_site(s["via"]["site"])) for s in x["seeds"]):
            continue
        for c in x["claims"]:
            entries = [s["offset"] for s in x["seeds"] if c["start"] <= s["offset"] < c["end"]]
            insns = B1.decode_all(rom, c["start"], c["end"])
            if not entries or insns is None:
                continue
            reached, _ = F.descend(rom, entries, c["start"], c["end"])
            if sorted(reached) != sorted(insns) or not F.is_terminal(list(insns.values())[-1]):
                continue
            relative = [(p, F.resolve_target(p, F._addr_operand(d))) for p, d in insns.items()
                        if d.op in (F.OP.JR, F.OP.DJNZ)]
            if any(t not in insns for _, t in relative):         # the assembly needs every JR/DJNZ target as a label
                continue
            via = {s["offset"]: s["via"] for s in x["seeds"]}
            out.append(OrderedDict([
                ("name", "%s%05X" % (HANDLER_PREFIX, c["start"])), ("start", c["start"]), ("end", c["end"]),
                ("instructions", len(insns)), ("entries", entries),
                ("entry_support", [OrderedDict([("entry", e), ("via", "player_script" if "player_script" in via[e] else "jp_stub"),
                                                ("detail", via[e].get("player_script") or via[e])]) for e in entries])]))
    return sorted(out, key=lambda r: r["start"])


def build(rom, root=ROOT):
    regions = json.loads((root / "asm" / "recovered" / "regions.json").read_text(encoding="utf-8"))
    derived_names = {r["name"] for r in regions if r["name"].startswith((STUB_PREFIX, HANDLER_PREFIX))}
    base = [r for r in regions if r["name"] not in derived_names]
    scripts = PS.parse_scripts(rom)
    ins = B1.vector_descent(rom)[0]
    direct = vector_targets_of(rom, base, ins)

    # every address a player script makes the engine execute, in the caller's own address space
    support = defaultdict(lambda: OrderedDict([("script_callbacks", []), ("script_executed", []), ("direct_callers", [])]))
    words = []
    for row in scripts["callbacks"]:
        for field, cpu_key, off_key in (("vector", "operand_cpu", "operand_offset"),
                                       ("selector", "selector_operand_cpu", "selector_operand_offset")):
            v = row.get(field)
            if not v:
                continue
            ref = OrderedDict([("type", row["type"]), ("state", row["state"]), ("script_cpu", row["script_cpu"]),
                               ("command", row["kind"]), ("operand_cpu", row[cpu_key]), ("operand_offset", row[off_key]),
                               ("value", v)])
            words.append((field, v, ref))
            if v < F.RESIDENT_END:
                support[v]["script_callbacks" if field == "vector" else "script_executed"].append(ref)
    for t, sites in direct.items():
        if (t - 0x380) % 3 == 0 and is_stub(rom, t):
            for s, op, src in sites:
                support[t]["direct_callers"].append(OrderedDict([("site", s), ("op", op), ("source", src)]))

    # the table is the run of consecutive JP stubs the scripts point into; direct callers elsewhere do not extend it
    anchors = [a for a, v in support.items() if is_stub(rom, a) and (v["script_callbacks"] or v["script_executed"])]
    lo, hi = stub_geometry(rom, anchors)
    stubs, supported = [], []
    for a in range(lo, hi, 3):
        s = support.get(a)
        has = bool(s and (s["script_callbacks"] or s["script_executed"] or s["direct_callers"]))
        dest = rom[a + 1] | rom[a + 2] << 8
        stubs.append(OrderedDict([
            ("stub", a), ("destination", dest), ("supported", has),
            ("script_callback_refs", len(s["script_callbacks"]) if s else 0),
            ("script_executed_refs", len(s["script_executed"]) if s else 0),
            ("direct_callers", s["direct_callers"] if s else []),
            ("first_script_ref", (s["script_callbacks"] or s["script_executed"] or [None])[0] if s else None),
            ("state_scripts", sorted({(r["type"], r["state"]) for r in (s["script_callbacks"] + s["script_executed"])}) if s else [])]))
        if has:
            supported.append(a)
    runs = []
    for a in supported:
        if runs and runs[-1][1] == a:
            runs[-1][1] = a + 3
        else:
            runs.append([a, a + 3])

    handlers = handler_regions(rom, root, runs, derived_names)
    resident_other = sorted({v for f, v, r in words if f == "vector" and v < F.RESIDENT_END and not (lo <= v < hi)})
    slot2_vectors = sorted({v for f, v, r in words if f == "vector" and v >= F.RESIDENT_END})
    executed_slot2 = sorted({v for f, v, r in words if f == "selector" and v >= F.RESIDENT_END})

    doc = OrderedDict()
    doc["format"] = 1
    doc["rom_sha256"] = RL.ROM_SHA256
    doc["generator"] = "tools/decomp1c_callbacks.py"
    doc["evidence_tier"] = "static: ROM structure plus control flow; no execution trace and no claim the game enters the state"
    doc["engine_facts"] = scripts["engine_facts"]
    doc["commands"] = scripts["commands"]
    doc["tables"] = scripts["tables"]
    doc["parse_summary"] = OrderedDict([
        ("states", len(scripts["states"])), ("callback_rows", len(scripts["callbacks"])),
        ("record_callbacks", sum(1 for r in scripts["callbacks"] if r["kind"] == "record")),
        ("command_callbacks", sum(1 for r in scripts["callbacks"] if r["kind"] != "record" and r["vector"])),
        ("notes", scripts["notes"])])
    doc["stub_table"] = OrderedDict([
        ("bounds", [lo, hi]), ("stubs", len(stubs)),
        ("structure", "consecutive 3-byte JP instructions with resident destinations; a structural fact, not entry evidence"),
        ("supported", len(supported)), ("unsupported", [s["stub"] for s in stubs if not s["supported"]])])
    doc["stubs"] = stubs
    doc["stub_regions"] = [OrderedDict([("name", "%s%04X" % (STUB_PREFIX, a)), ("start", a), ("end", b)]) for a, b in runs]
    doc["handler_regions"] = handlers
    doc["other_script_vectors"] = OrderedDict([("resident_outside_stub_table", resident_other), ("slot2_in_bank_12", slot2_vectors),
                                               ("executed_slot2_in_bank_12", executed_slot2)])
    doc["states"] = scripts["states"]
    doc["callbacks"] = scripts["callbacks"]
    return doc


def derived_region_doc(doc):
    rows = [OrderedDict([("name", r["name"]), ("start", r["start"]), ("end", r["end"]), ("role", "jp_stub_run")]) for r in doc["stub_regions"]]
    rows += [OrderedDict([("name", r["name"]), ("start", r["start"]), ("end", r["end"]), ("role", "dispatch_target")]) for r in doc["handler_regions"]]
    return json.dumps(rows, indent=1) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("rom", nargs="?", default=str(RL.DEFAULT_ROM))
    ap.add_argument("--output", default=str(OUTPUT))
    ap.add_argument("--derived", default=str(DERIVED))
    args = ap.parse_args(argv)
    doc = build(RL.load_rom(args.rom))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_bytes((json.dumps(doc, indent=1) + "\n").encode("utf-8"))
    Path(args.derived).write_bytes(derived_region_doc(doc).encode("utf-8"))
    st = doc["stub_table"]
    print("stubs: %d supported of %d (%s-%s); stub regions: %d; handler regions: %d; callback rows: %d"
          % (st["supported"], st["stubs"], hx(st["bounds"][0]), hx(st["bounds"][1]), len(doc["stub_regions"]),
             len(doc["handler_regions"]), doc["parse_summary"]["callback_rows"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

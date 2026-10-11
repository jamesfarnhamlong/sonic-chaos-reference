#!/usr/bin/env python3
"""DECOMP-1A tests: reviewed classifications, flow evidence, contradiction resolution.

Tests that need the canonical ROM skip without SONIC_CHAOS_ROM or
../source/Sonic Chaos (Europe).sms; the rest read only committed metadata.
"""
import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1a_review as RV  # noqa: E402
import rom_flow as F  # noqa: E402
import rom_ledger as RL  # noqa: E402

LEDGER = ROOT / "data" / "rom-ledger" / "ledger.json"
REVIEWED = ROOT / RL.REVIEWED
REGIONS = ROOT / "asm" / "recovered" / "regions.json"
OBJECT50 = ROOT / "data" / "rom-cache" / "thz3" / "object-50.json"
ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(RL.DEFAULT_ROM)))


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == RL.ROM_SIZE and hashlib.sha256(data).hexdigest() == RL.ROM_SHA256:
            return data
    return None


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class FlowPrimitiveTests(unittest.TestCase):
    """rom_flow on tiny synthetic images (no ROM)."""

    def rom(self, blob, at=0x100):
        image = bytearray(0x2000)
        image[at:at + len(blob)] = blob
        return bytes(image)

    def test_descent_follows_calls_and_stops_at_ret(self):
        # 0100: CALL 0108 / RET ; 0108: INC A / RET
        rom = self.rom(bytes([0xCD, 0x08, 0x01, 0xC9, 0, 0, 0, 0, 0x3C, 0xC9]))
        reached, notes = F.descend(rom, [0x100], 0x100, 0x10A)
        self.assertEqual(sorted(reached), [0x100, 0x103, 0x108, 0x109])
        self.assertEqual(F.runs(reached), [(0x100, 0x104), (0x108, 0x10A)])
        self.assertEqual(notes, [])

    def test_conditional_branch_falls_through_and_branches(self):
        # JR Z,+1 ; NOP ; RET
        rom = self.rom(bytes([0x28, 0x01, 0x00, 0xC9]))
        reached, _ = F.descend(rom, [0x100], 0x100, 0x104)
        self.assertEqual(sorted(reached), [0x100, 0x102, 0x103])

    def test_branch_out_of_range_is_not_followed(self):
        rom = self.rom(bytes([0xC3, 0x00, 0x05]))               # JP 0500
        reached, notes = F.descend(rom, [0x100], 0x100, 0x103)
        self.assertEqual(sorted(reached), [0x100])
        self.assertEqual(notes, [("leaves_range", 0x100)])

    def test_invalid_opcode_and_fall_off_are_reported(self):
        reached, notes = F.descend(self.rom(bytes([0xED, 0x00])), [0x100], 0x100, 0x102)
        self.assertEqual((reached, notes), ({}, [("invalid", 0x100)]))
        reached, notes = F.descend(self.rom(bytes([0x00, 0x00])), [0x100], 0x100, 0x102)
        self.assertEqual(sorted(reached), [0x100, 0x101])
        self.assertEqual(notes, [("leaves_range", 0x102)])
        _, notes = F.descend(self.rom(bytes([0x3E])), [0x100], 0x100, 0x101)    # LD A,n cut by the bound
        self.assertEqual(notes, [("falls_off", 0x100)])

    def test_indirect_jump_is_flagged_and_terminal(self):
        reached, notes = F.descend(self.rom(bytes([0xE9, 0x00])), [0x100], 0x100, 0x102)   # JP (HL)
        self.assertEqual(sorted(reached), [0x100])
        self.assertEqual(notes, [("indirect", 0x100)])

    def test_target_resolution_rules(self):
        self.assertEqual(F.resolve_target(0x6000, 0x1234), 0x1234)              # resident target
        self.assertIsNone(F.resolve_target(0x6000, 0x8123))                     # resident site, slot-2 target: ambiguous
        self.assertEqual(F.resolve_target(0x30100, 0x8123), 0x30000 + 0x123)    # slot-2 site: same bank
        self.assertIsNone(F.resolve_target(0x30100, 0xC123))


class ReviewedClaimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = load(LEDGER)
        cls.reviewed = load(REVIEWED)
        cls.claims = [c for c in cls.ledger["claims"] if "reviewed_ranges" in c["importers"]]

    def test_reviewed_file_and_ledger_agree(self):
        self.assertEqual(self.reviewed["rom_sha256"], RL.ROM_SHA256)
        wanted = sorted((c["start"], c["end"]) for r in self.reviewed["code_flow_reviews"] for c in r["claims"])
        self.assertEqual(sorted((c["start"], c["end"]) for c in self.claims), wanted)
        self.assertEqual(self.ledger["reviewed"]["claims"], len(wanted))
        self.assertEqual(self.ledger["reviewed"]["code_bytes"], sum(e - s for s, e in wanted))

    def test_claim_provenance_and_class(self):
        for c in self.claims:
            self.assertEqual(c["primary"], "CODE")
            self.assertEqual(c["evidence"], "reviewed_flow_verified")
            self.assertEqual(c["basis"], "independent")
            self.assertFalse(c["recovered"])
            self.assertIn(RL.REVIEWED, c["sources"])
            self.assertGreaterEqual(len(c["sources"]), 2, "needs the audit source as well")
        for r in self.reviewed["code_flow_reviews"]:
            lo, hi = r["bounds"]
            self.assertTrue(r["seeds"] and r["audit_ranges"])
            self.assertTrue(r["verification"] and r["uncertainty"])
            for c in r["claims"]:
                self.assertTrue(lo <= c["start"] < c["end"] <= hi)
            for a in r["audit_ranges"]:
                self.assertTrue(a["source"].startswith("data/rom-cache/"))

    def test_reviewed_bytes_were_unknown_and_recovery_is_unchanged(self):
        regions = load(REGIONS)
        recovered = sum(r["bytes"] for r in regions)
        self.assertEqual(self.ledger["totals"]["recovered_bytes"], recovered)
        for s in self.ledger["segments"]:
            if any(c["id"] in s["claims"] for c in self.claims):
                self.assertEqual(s["primary"], "CODE")
                self.assertEqual(s["recovery"], "not_recovered")
                self.assertEqual(s["classification_basis"], "independent")
        recovered_ranges = [(r["start"], r["end"]) for r in regions]
        for c in self.claims:
            for lo, hi in recovered_ranges:
                self.assertFalse(c["start"] < hi and c["end"] > lo, "review re-describes recovered bytes")

    def test_unresolved_accounting_is_consistent(self):
        unresolved = self.reviewed["unresolved"]
        self.assertEqual(self.ledger["reviewed"]["unresolved_unknown_bytes"],
                         sum(u["unknown_bytes"] for u in unresolved))
        segs = self.ledger["segments"]
        for u in unresolved:
            self.assertTrue(u["reason"] and u["evidence_needed"])
            n = 0
            for lo, hi in u["unknown_runs"]:
                for s in segs:
                    if s["start"] < hi and s["end"] > lo:
                        self.assertEqual(s["primary"], "UNKNOWN")
                        n += min(s["end"], hi) - max(s["start"], lo)
            self.assertEqual(n, u["unknown_bytes"])

    def test_range_statuses_cover_all_211_ranges(self):
        rows = self.ledger["unclassified_range_claims"]["ranges"]
        self.assertEqual(len(rows), self.ledger["unclassified_range_claims"]["count"])
        for r in rows:
            self.assertEqual(sum(r["bytes_by_class"].values()), r["end"] - r["start"])
            unknown = r["bytes_by_class"].get("UNKNOWN", 0)
            self.assertEqual(r["status"], "classified" if not unknown else
                             "unresolved" if unknown == r["end"] - r["start"] else "partial")
        mixed = [r for r in rows if "CODE" in r["bytes_by_class"] and "DATA" in r["bytes_by_class"]]
        self.assertTrue(mixed, "mixed code/data audit ranges must be subdivided, not forced into one class")

    def test_independent_coverage_grows_only_by_reviewed_and_audit_bytes(self):
        t = self.ledger["totals"]
        self.assertEqual(t["independent_structural_bytes"] + t["classified_by_recovery_only_bytes"],
                         t["classified_bytes"])
        self.assertEqual(t["contested_bytes"], 0)


class ContradictionResolutionTests(unittest.TestCase):
    def test_audit_cache_is_corrected_at_its_source(self):
        routines = {r["name"]: r for r in load(OBJECT50)["routines"]}
        self.assertNotIn("0x66B6", routines["anim_cmd_dispatch"]["cpu_end_exclusive"])
        self.assertEqual((routines["anim_cmd_dispatch"]["kind"], routines["anim_cmd_dispatch"]["cpu_end_exclusive"]),
                         ("code", "0x6696"))
        table = routines["anim_cmd_pointer_table"]
        self.assertEqual((table["kind"], table["rom_offset"], table["length"]), ("data", "0x06696", 32))

    def test_ledger_has_no_contradiction_and_table_is_data(self):
        ledger = load(LEDGER)
        self.assertEqual(ledger["overlaps"]["stats"]["contradictory_pairs"], 0)
        self.assertEqual(ledger["overlaps"]["contradictory"], [])
        seg = next(s for s in ledger["segments"] if s["start"] <= 0x6696 < s["end"])
        self.assertEqual((seg["primary"], seg["contested"], seg["recovery"]), ("DATA", False, "recovered"))
        self.assertEqual(seg["start"], 0x6696)
        self.assertEqual(seg["end"], 0x66B6)

    def test_contradiction_detection_still_works(self):
        a = RL.make_claim(0x6680, 0x66B6, "CODE", "t", "t", "manifest_hash_verified")
        b = RL.make_claim(0x6696, 0x66B6, "DATA", "t", "t", "byte_verified_assembly")
        segments, conflicts = RL.resolve(RL.dedupe_claims([a, b]))
        self.assertEqual(conflicts["stats"]["contradictory_pairs"], 1)
        self.assertEqual([s["primary"] for s in segments if s["start"] == 0x6696], ["UNKNOWN"])


class RomBackedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        if cls.rom is None:
            raise unittest.SkipTest("canonical ROM not available (set SONIC_CHAOS_ROM)")
        cls.regions = load(REGIONS)

    def tamper(self, edit):
        """Run import_reviewed against a temp tree whose reviewed file was edited."""
        doc = copy.deepcopy(load(REVIEWED))
        edit(doc)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "data" / "rom-ledger").mkdir(parents=True)
            (root / "asm" / "recovered").mkdir(parents=True)
            shutil.copy(REGIONS, root / "asm" / "recovered" / "regions.json")
            (root / RL.REVIEWED).write_text(json.dumps(doc), encoding="utf-8")
            return RL.import_reviewed(self.rom, root, self.regions)

    def test_committed_reviews_verify(self):
        claims, summary = RL.import_reviewed(self.rom, ROOT, self.regions)
        self.assertEqual(summary["claims"], len(claims))
        self.assertGreater(len(claims), 0)

    def test_stale_or_inconsistent_entries_are_rejected(self):
        def shift_seed(doc):
            doc["code_flow_reviews"][0]["seeds"][0]["offset"] += 1

        def fake_site(doc):
            doc["code_flow_reviews"][0]["seeds"][0]["via"] = {"site": 0x4}

        def grow_claim(doc):
            r = doc["code_flow_reviews"][0]
            r["claims"][0]["end"] = r["bounds"][1] + 1

        def wrong_rom(doc):
            doc["rom_sha256"] = "0" * 64

        def claim_outside_flow(doc):
            r = next(x for x in doc["code_flow_reviews"] if len(x["claims"]) == 1)
            r["claims"][0]["start"] += 1          # splits the first instruction

        for edit in (shift_seed, fake_site, grow_claim, wrong_rom):
            with self.assertRaises(ValueError, msg=edit.__name__):
                self.tamper(edit)
        # an unreached byte (or an instruction split) never verifies
        with self.assertRaises(ValueError):
            self.tamper(claim_outside_flow)

    def test_claim_over_recovered_data_is_refused(self):
        data = next(r for r in self.regions if r["kind"] == "data" and r["end"] <= F.RESIDENT_END)

        def reach_data(doc):
            r = doc["code_flow_reviews"][0]
            r["bounds"] = [min(r["bounds"][0], data["start"]), max(r["bounds"][1], data["end"])]
            r["claims"].append({"start": data["start"], "end": data["end"], "primary": "CODE", "subtype": "routine"})

        with self.assertRaises(ValueError):
            self.tamper(reach_data)

    def test_review_never_changes_recovered_or_baseline_classes(self):
        base = RL.build_ledger(self.rom, ROOT, reviewed=False)
        final = RL.build_ledger(self.rom, ROOT)
        self.assertEqual(base["totals"]["recovered_bytes"], final["totals"]["recovered_bytes"])
        self.assertEqual(final["totals"]["classified_bytes"] - base["totals"]["classified_bytes"],
                         final["reviewed"]["code_bytes"])
        unknown_before = sum(s["length"] for s in base["segments"] if s["primary"] == "UNKNOWN")
        unknown_after = sum(s["length"] for s in final["segments"] if s["primary"] == "UNKNOWN")
        self.assertEqual(unknown_before - unknown_after, final["reviewed"]["code_bytes"])
        for cat in ("DATA", "COMPRESSED", "GRAPHICS", "MUSIC", "PADDING"):
            self.assertEqual(base["totals"]["by_category"][cat], final["totals"]["by_category"][cat])

    def test_builder_reproduces_the_committed_review_file(self):
        doc = RV.build(self.rom)
        self.assertEqual(json.dumps(doc, indent=1) + "\n",
                         REVIEWED.read_bytes().replace(RL.CRLF, RL.LF).decode("utf-8"))

    def test_animation_dispatcher_and_table_boundaries(self):
        regions = {r["name"]: r for r in self.regions}
        disp, table = regions["animation_command_dispatch"], regions["animation_command_table"]
        handlers = regions["animation_command_handlers"]
        self.assertEqual((disp["end"], table["start"], table["end"], handlers["start"]),
                         (0x6696, 0x6696, 0x66B6, 0x66B6))
        instrs = F.region_instructions(self.rom, disp)
        self.assertTrue(F.is_indirect_jump(instrs[-1][2]))                    # JP (HL) at $6695
        loads = [p for p, _, d in instrs if d.op == F.OP.LD and any(k.name == "IMM" and v == 0x6696
                                                                    for k, v in d.operands)]
        self.assertTrue(loads)
        starts = {p for p, _, _ in F.region_instructions(self.rom, handlers)}
        for i in range(16):
            self.assertIn(RL.dispatch_table_word(self.rom, table, i), starts)


if __name__ == "__main__":
    unittest.main()

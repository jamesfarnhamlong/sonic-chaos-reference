#!/usr/bin/env python3
import importlib.util
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("closure", ROOT / "tools/thz1_closure_audit.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ClosureAuditTests(unittest.TestCase):
    def setUp(self):
        self.audit = m.build_audit()

    def test_canonical_counts_and_populations(self):
        counts = self.audit["canonical_counts"]
        self.assertEqual(counts["raw_object_records"], 53)
        self.assertEqual(counts["placed_types"], 8)
        self.assertEqual(counts["layout_ring_positions"], 142)
        self.assertEqual(sum(counts["type_counts"].values()), 53)

    def test_poc_count_gate(self):
        poc = self.audit["poc_verification"]
        self.assertEqual((poc["type_10"], poc["type_21"], poc["type_27"]), (5, 6, 3))
        self.assertEqual((poc["moving_spikes"], poc["static_spikes"], poc["platforms"]), (4, 4, 6))
        self.assertEqual((poc["terrain_springs"], poc["layout_rings"]), (9, 142))
        self.assertEqual(poc["legacy_layout_monitors"], 0)
        self.assertFalse(poc["fabricated_finish_marker_treated_as_canonical"])

    def test_command_09_closed_only_animation_gap(self):
        command = self.audit["command_09"]
        self.assertEqual(command["semantics"], "object[offset] = immediate")
        self.assertEqual(command["total_command_bytes"], 4)
        self.assertEqual(command["remaining_type_28_animation_gaps"], 0)

    def test_allowed_classifications_and_explicit_blockers(self):
        allowed = {"CLOSED", "BLOCKER", "ACCEPTED ADAPTER", "FUTURE FIDELITY"}
        self.assertTrue(all(x["classification"] in allowed for x in self.audit["objects"]))
        self.assertTrue(all(x["classification"] in allowed for x in self.audit["terrain_mechanics"]))
        self.assertEqual(Counter(x["classification"] for x in self.audit["objects"])["BLOCKER"], 1)
        self.assertEqual(len(self.audit["blockers"]), 2)
        self.assertEqual(self.audit["overall_conclusion"], "THZ1 POC BLOCKED")

    def test_committed_json_regenerates(self):
        committed = json.loads((ROOT / "data/rom-cache/thz1/closure-audit.json").read_text())
        self.assertEqual(committed, self.audit)


if __name__ == "__main__":
    unittest.main(verbosity=2)

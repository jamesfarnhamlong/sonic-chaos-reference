#!/usr/bin/env python3
"""Independent arithmetic and metadata tests for the type-$27 report tool."""

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "thz1_object_27.py"
spec = importlib.util.spec_from_file_location("thz1_object_27", TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Object27Tests(unittest.TestCase):
    def test_horizontal_comparisons_are_strict(self):
        self.assertTrue(m.horizontal_test(63, 0x40))
        self.assertFalse(m.horizontal_test(64, 0x40))
        self.assertFalse(m.horizontal_test(65, 0x40))
        self.assertTrue(m.horizontal_test(383, 0x180))
        self.assertFalse(m.horizontal_test(384, 0x180))
        self.assertFalse(m.horizontal_test(385, 0x180))

    def test_counter_underflow_trajectory(self):
        result = m.expected_oscillation()
        self.assertEqual(result["updates"], 129)
        self.assertEqual(result["add_callbacks"], 65)
        self.assertEqual(result["subtract_callbacks"], 64)
        self.assertEqual(result["displacement_8_8"], 3)
        self.assertEqual(result["velocity_before_reset_8_8"], 3)
        self.assertEqual(result["counter_after"], 0xFF)

    def test_all_thz1_records_match_verified_fields(self):
        placements = m.load_placements()
        self.assertEqual(
            [(row["world_x"], row["world_y"]) for row in placements],
            [(3504, 224), (2288, 768), (2240, 112)],
        )
        self.assertTrue(all(row["flags"] == "0x10" for row in placements))
        self.assertTrue(all(row["parameter"] == "0x00" for row in placements))
        self.assertTrue(all(row["aux0"] == "0xAA" for row in placements))
        self.assertTrue(all(row["aux1"] == "0xAA" for row in placements))


if __name__ == "__main__":
    unittest.main(verbosity=2)

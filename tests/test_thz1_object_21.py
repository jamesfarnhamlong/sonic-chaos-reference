#!/usr/bin/env python3
"""Synthetic arithmetic tests for the type-$21 report tool."""

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "thz1_object_21.py"
spec = importlib.util.spec_from_file_location("thz1_object_21", TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Object21Tests(unittest.TestCase):
    def test_parameter_controls_left_bound(self):
        self.assertEqual(m.parameter_left_bound(1000, 2), 968)
        self.assertEqual(m.parameter_left_bound(1000, 8), 872)

    def test_strict_integer_bound_causes_half_pixel_overshoot(self):
        self.assertEqual(m.first_left_reversal_tick(2), 65)
        self.assertEqual(m.first_left_reversal_tick(8), 257)

    def test_all_thz1_records_use_verified_art_bases(self):
        placements = m.load_placements()
        self.assertEqual(len(placements), 6)
        self.assertEqual(
            sorted(int(row["parameter"], 16) for row in placements),
            [2, 3, 4, 6, 6, 8],
        )
        self.assertTrue(all(row["aux0"] == "0x86" for row in placements))
        self.assertTrue(all(row["aux1"] == "0x98" for row in placements))


if __name__ == "__main__":
    unittest.main(verbosity=2)

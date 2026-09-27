#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOSURE = json.loads((ROOT / "data/rom-cache/thz1/final-runtime-closure.json").read_text(encoding="utf-8"))
COVERAGE = json.loads((ROOT / "data/rom-cache/thz1/poc-coverage.json").read_text(encoding="utf-8"))


class FinalRuntimeClosureTests(unittest.TestCase):
    def test_type21_sat_bounds_all_six_and_fixture_subset(self):
        rows = CLOSURE["type_21"]["placements"]
        self.assertEqual(len(rows), 6)
        self.assertEqual([x["stable_anchor_y"] for x in rows], [590, 846, 302, 878, 270, 238])
        self.assertTrue(all(x["visible_top"] == x["stable_anchor_y"] - 31 for x in rows))
        self.assertTrue(all(x["visible_bottom"] == x["stable_anchor_y"] for x in rows))
        self.assertTrue(all(x["blank_rows_between_sprite_and_terrain"] == 17 for x in rows))
        self.assertEqual(CLOSURE["type_21"]["controlled_fixture_world_x"], [800, 3296, 2400])

    def test_block47_exact_cells_tiles_palette_and_collision(self):
        b = CLOSURE["block_47"]
        self.assertTrue(b["all_four_cells_verified"])
        self.assertEqual([x["world"] for x in b["cells"]],
                         [[3328, 256], [3360, 256], [3392, 256], [3424, 256]])
        self.assertTrue(all(x["block_id"] == "0x47" for x in b["cells"]))
        self.assertEqual((b["mapping_cpu"], b["mapping_rom"]), ("0x8A20", "0x44A20"))
        self.assertEqual(len(b["pieces"]), 16)
        self.assertEqual([x["attribute"] for x in b["pieces"]][4:7],
                         ["0x1917", "0x1918", "0x1B17"])
        headers = b["collision_headers"]
        self.assertEqual([x["raw"] for x in headers],
                         ["96 00 D0 8C 10 95 FF", "B0 00 F0 8C 30 95 FF"])
        self.assertEqual(headers[0]["vertical_profile"],
                         ["0x17", "0x17"] + ["0x18"] * 28 + ["0x17", "0x17"])
        self.assertTrue(b["terrain_behavior"]["creates_transient_object_on_break"])
        self.assertEqual(b["terrain_behavior"]["replacement_block"], "0x46")
        self.assertFalse(b["canonical_red_magenta"])
        self.assertFalse(b["poc_18_5_colour_comparison"]["exact_match"])
        self.assertEqual(b["classification"], "INTERACTIVE TERRAIN")

    def test_type27_creation_and_first_display_boundaries(self):
        rows = CLOSURE["type_27"]["placements"]
        self.assertEqual(rows[0]["creation_camera_x_inclusive"], [3153, 3600])
        self.assertEqual(rows[0]["active_callback_and_sat_camera_x_inclusive"], [3217, 3536])
        self.assertEqual(rows[0]["actual_nonzero_pixel_camera_x_inclusive"], [3237, 3515])
        self.assertTrue(all(x["creation_to_first_nonempty_frame_updates"] == 2 for x in rows))
        self.assertTrue(CLOSURE["type_27"]["can_first_display_inside_visible_viewport"])

    def test_all_53_records_exactly_once_and_separate_populations(self):
        rows = COVERAGE["raw_object_population"]["records"]
        self.assertEqual(len(rows), 53)
        self.assertEqual([x["record_index"] for x in rows], list(range(1, 54)))
        self.assertEqual(len({x["rom_offset"] for x in rows}), 53)
        self.assertEqual(COVERAGE["missing_record_indices"],
                         list(range(14, 22)) + list(range(37, 53)))
        self.assertEqual(COVERAGE["separate_populations"]["layout_derived_rings"]["count"], 142)
        self.assertEqual(COVERAGE["answer"], "NO, WITH EXACT MISSING RECORDS/ENTITIES")


if __name__ == "__main__":
    unittest.main(verbosity=2)

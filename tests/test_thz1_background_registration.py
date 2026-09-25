import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from thz1_background_registration import build


class THZ1BackgroundRegistration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cached = json.loads((ROOT / "data/rom-cache/thz1/background-registration.json").read_text())
        cls.report = build((ROOT.parent / "Sonic Chaos (Europe).sms").read_bytes())

    def test_source_chain_and_layout_cells(self):
        self.assertEqual(self.report["source"]["block_pointer_table_rom"], "0x44000")
        first, second = self.report["patches"]
        self.assertEqual(next(x for x in first["layout_cells"] if x["world_origin"] == [320, 288])["block_id"], "0x01")
        self.assertEqual(next(x for x in second["layout_cells"] if x["world_origin"] == [1472, 128])["block_id"], "0x01")

    def test_platform_pixels_begin_at_collision_surface(self):
        for patch in self.report["patches"]:
            transition = next(x for x in patch["sample_x_palette_transitions"]
                              if x["y"] >= patch["surface_y"])
            self.assertEqual(transition["y"], patch["surface_y"])
            self.assertNotEqual(transition["palette_index"], 0)

    def test_committed_poc_comparison_is_exact_at_platform(self):
        for patch in self.cached["patches"]:
            self.assertTrue(patch["poc_18_5"]["platform_exact_rgba_match"])


if __name__ == "__main__":
    unittest.main()

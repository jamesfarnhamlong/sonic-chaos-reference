import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from player_state_11_graphics import build


class PlayerState11Graphics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build((ROOT.parent / "Sonic Chaos (Europe).sms").read_bytes())

    def test_mapping_and_dynamic_sources(self):
        frames = self.report["frames"]
        self.assertEqual([x["mapping_frame_cpu"] for x in frames], ["0x83E9", "0x83F4", "0x83FF"])
        self.assertEqual([x["graphics_transfer"]["source_rom"] for x in frames],
                         ["0x15980", "0x15B00", "0x15C80"])
        self.assertTrue(all(x["graphics_transfer"]["tile_count"] == 12 for x in frames))

    def test_exact_output_hashes_and_anchor(self):
        self.assertEqual([x["render"]["rgba_sha256"] for x in self.report["frames"]], [
            "39007e36a7ec3e9888df5919d824667da84a4c0fdbf79cca6971ba03b7976c41",
            "22364cea9bd4190b07c28aad386f011699577e3d6fd105e851ed6980be05fc45",
            "da066dd9609909a66e41b12048eae0b361460a1deb1e11d2f2dd181c05f6029e",
        ])
        for frame in self.report["frames"]:
            self.assertEqual((frame["render"]["canvas_width"], frame["render"]["canvas_height"]), (24, 32))
            self.assertEqual((frame["render"]["gamemaker_origin_x"], frame["render"]["gamemaker_origin_y"]), (16, 32))

    def test_palette_and_committed_cache(self):
        self.assertEqual(self.report["palette"]["selector"], "0x06")
        self.assertEqual(self.report["palette"]["rgba"][0][3], 0)
        cached = json.loads((ROOT / "data/rom-cache/thz1/player-state-11-graphics.json").read_text())
        self.assertEqual(cached, self.report)


if __name__ == "__main__":
    unittest.main()

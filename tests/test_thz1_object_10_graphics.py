#!/usr/bin/env python3
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "thz1_object_10_graphics.py"
spec = importlib.util.spec_from_file_location("graphics10", TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Graphics10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidates = list(ROOT.parent.glob("Sonic Chaos*.sms"))
        if not candidates:
            raise unittest.SkipTest("canonical ROM not adjacent to repository")
        cls.meta = m.build_metadata(candidates[0].read_bytes())

    def variant(self, selector, player="0x01"):
        return next(x for x in self.meta["variants"] if x["selector"] == selector and x["player_type"] == player)

    def test_exact_pointers(self):
        expected = {
            "0x02": ("0x9A60", "0x9F60"),
            "0x04": ("0x9D60", "0xA160"),
            "0x06": ("0x9BE0", "0xA060"),
        }
        for selector, pointers in expected.items():
            self.assertEqual(tuple(x["source_cpu"] for x in self.variant(selector)["streams"]), pointers)

    def test_transfer_contract(self):
        for selector in ("0x02", "0x04", "0x06"):
            streams = self.variant(selector)["streams"]
            self.assertEqual([x["byte_count"] for x in streams], [192, 128])
            self.assertEqual([x["vram_destination"] for x in streams], ["0x0980", "0x0BC0"])
            self.assertEqual(streams[0]["resulting_tile_indices"], [f"0x{x:02X}" for x in range(0x4C, 0x52)])
            self.assertEqual(streams[1]["resulting_tile_indices"], [f"0x{x:02X}" for x in range(0x5E, 0x62)])

    def test_alternate_pointers_preserved(self):
        expected = {
            "0x02": ("0xA1E0", "0xA320"),
            "0x04": ("0x9D60", "0xA060"),
            "0x06": ("0x9BE0", "0xA060"),
        }
        for selector, pointers in expected.items():
            self.assertEqual(tuple(x["source_cpu"] for x in self.variant(selector, "alternate")["streams"]), pointers)

    def test_palette_and_composition_are_explicit(self):
        self.assertEqual(self.meta["palette"]["sprite_palette_selector"], "0x06")
        self.assertEqual(self.meta["palette"]["raw_sha256"], "c6715cef80884efccdc74a30c6c85023858169524ded2be963e16badb1f677e2")
        self.assertIn("0x4C-0x51", self.meta["composition"]["frame_0B"])
        self.assertIn("does not reference", self.meta["composition"]["frame_0C"])

    def test_output_hashes_are_stable(self):
        expected = {
            "0x02": ("f55ed4545fe648ba2c0365d55a2b3cd5593706437edcdea4ea48da2ced40d4a5", "2bb087b4bcc265ee2ba8b8ba038772b6615d7d5fe1f4aeb43625d694900b3b6d"),
            "0x04": ("0a90b35b41e64896bb4447f5a670fa92c2cc2f9acad67fa589e9890595a7c0f0", "4e142bbe120b2f47d5f9dea69c1f414240ff4543d3796004cc933c66cf63abc4"),
            "0x06": ("a523f7a53d4f35b7ba6101062b1fb0e4f6d8171a42ecdcb7f9fac19bde01411d", "3790c8bee0dd4f9d53a803616ac75123f346a55b11b7a80a87c1ab80247f24f0"),
        }
        for selector, (tile_hash, rgba_hash) in expected.items():
            variant = self.variant(selector)
            self.assertEqual(variant["streams"][0]["tile_bytes_sha256"], tile_hash)
            self.assertEqual(variant["frames"][0]["rgba_sha256"], rgba_hash)
            self.assertEqual(variant["frames"][1]["rgba_sha256"], "9571cc57547acfb52bf993cea93cfece3a0c3b0a31ace0f79e71ffe5f795a3a7")

    def test_committed_metadata_matches(self):
        committed = json.loads((ROOT / "data/rom-cache/thz1/object-10-graphics.json").read_text())
        self.assertEqual(committed, self.meta)


if __name__ == "__main__":
    unittest.main(verbosity=2)

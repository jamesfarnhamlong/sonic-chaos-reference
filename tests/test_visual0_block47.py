"""VISUAL-0 THZ1 block $47 break-up: committed evidence consistency, ROM regeneration of the static chain."""
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import visual0_block47 as B

CACHE = ROOT / "data/rom-cache/visual0/block47-break.json"


def find_rom():
    for candidate in (os.environ.get("SONIC_CHAOS_ROM"), ROOT.parent / "Sonic Chaos (Europe).sms",
                      ROOT.parent / "source" / "Sonic Chaos (Europe).sms"):
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    return None


class CommittedCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(CACHE.read_text(encoding="utf-8"))
        cls.static = cls.d["static"]
        cls.runs = {r["variant"]: r for r in cls.d["emulated"]}

    def test_cells_and_blocks(self):
        self.assertEqual([c["block"] for c in self.static["cells"]], ["0x47"] * 4)
        closure = json.loads((ROOT / "data/rom-cache/thz1/final-runtime-closure.json").read_text(encoding="utf-8"))
        # the independent task-08 render of block $47 must hash identically (palette-aware RGBA)
        self.assertEqual(self.static["blocks"]["0x47"]["rgba_sha256"], closure["block_47"]["rgba_sha256"])
        # the replacement block $46 is nothing but the empty tile $C0 in all sixteen cells
        self.assertEqual(set(self.static["blocks"]["0x46"]["name_table_words"]), {"0x00C0"})
        self.assertEqual(self.static["blocks"]["0x47"]["priority_words"], 9)

    def test_type_0f_state_3_script(self):
        ops = self.static["type_0f_states"]["3"]["ops"]
        self.assertEqual(ops[0]["op"], "FF 06")
        self.assertEqual(ops[0]["operands"], "AB")
        records = [(o["frame"], o["duration"]) for o in ops if o["op"] == "record"]
        self.assertEqual(records, [("0x07", 4), ("0x08", 4), ("0x09", 4), ("0x07", 4), ("0x08", 4), ("0x09", 8), ("0x08", 4),
                                   ("0x07", 4), ("0x07", 1), ("0x00", 128)])
        self.assertEqual(ops[-2]["callback"], "0xA0C6")        # terminal callback selects removal

    def test_type_11_script(self):
        s1 = self.static["type_11_states"]["1"]["ops"]
        rec = [o for o in s1 if o["op"] == "record"]
        self.assertEqual([(o["frame"], o["duration"], o["callback"]) for o in rec],
                         [("0x0D", 32, "0xA244"), ("0x00", 128, "0xA250")])
        self.assertEqual(self.static["frames"]["0x0D"]["tile_pairs"], ["0x5E+0x5F", "0x60+0x61"])

    def test_selector_one_sources(self):
        s = self.static["selector_1"]
        self.assertEqual([x["source_rom"] for x in s], ["0x399A0", "0x39EE0"])
        self.assertEqual([x["vram_destination"] for x in s], ["0x0980", "0x0BC0"])

    def test_emulated_responses_are_identical_for_both_entry_paths(self):
        top, spin = self.runs["top"], self.runs["spindash"]
        self.assertEqual(top["entry_path"], "$6B11 surface handler $6AE3 tail")
        self.assertEqual(spin["entry_path"], "$7386 side core, right-hand")
        self.assertEqual(spin["break_registers"]["player_state"], 0x10)        # a natural spin-dash roll broke the block
        for r in (top, spin):
            self.assertEqual(r["ring_bcd_before"], "0x00")
            self.assertEqual(r["ring_bcd_after"], "0x10")
            self.assertEqual([s["value"] for s in r["sound_requests"]], ["0xAB"])
            self.assertEqual(r["break_registers"]["d3b3_after_store"], 1)
            self.assertTrue(r["break_registers"]["vram_24_2D_equals_static_thz1_vram"])
            self.assertNotEqual(r["break_registers"]["vram_4C_51_before"], r["break_registers"]["vram_4C_51_after"])
            self.assertEqual(r["break_registers"]["vram_5E_61_before"], r["break_registers"]["vram_5E_61_after"])
            s = r["summary"]
            self.assertEqual(s["type_0F_frame_runs"], [["0x00", 1], ["0x07", 4], ["0x08", 4], ["0x09", 4], ["0x07", 4], ["0x08", 4],
                                                       ["0x09", 8], ["0x08", 4], ["0x07", 5], ["0x00", 1]])
            self.assertEqual(s["type_11_frame_runs"], [["0x0D", 33], ["0x00", 1]])
            self.assertEqual(len(s["type_0F_position"]), 1)
            (x, y), = s["type_0F_position"]
            self.assertEqual((x % 32, y), (16, 264))                               # cell X + 16, cell Y + 8
            self.assertEqual(s["type_11_x"], [x])
            self.assertEqual(s["type_11_y_by_update"][:3], [264, 259, 254])
        self.assertEqual(top["summary"]["type_11_y_by_update"], spin["summary"]["type_11_y_by_update"])

    def test_only_the_struck_cell_changes(self):
        top = self.runs["top"]
        contents = [x["content"] for x in top["nametable_at_those_locations_after_break"]]
        self.assertEqual(contents, ["block_46", "block_47", "block_47", "block_47"])
        self.assertEqual([x["content"] for x in self.runs["spindash"]["nametable_at_those_locations_after_break"]], ["block_46"])

    def test_poc_comparison(self):
        poc = self.d["poc"]
        self.assertEqual([c.get("rom_frame_rgba_equal") for c in poc["pixel_comparison_thz1_palette"]], ["0x07", "0x08", "0x09"])
        self.assertFalse(poc["has_type_11_object"])


@unittest.skipIf(find_rom() is None, "ROM not supplied (set SONIC_CHAOS_ROM)")
class Regeneration(unittest.TestCase):
    def test_static_chain_regenerates_exactly(self):
        rom = B.R.load(find_rom())
        fresh = B.build(rom, static_only=True)
        cached = json.loads(CACHE.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(json.dumps(fresh["static"])), cached["static"])

    def test_negative_control_other_block_differs(self):
        rom = B.R.load(find_rom())
        fresh = B.build(rom, static_only=True)
        self.assertNotEqual(fresh["static"]["blocks"]["0x47"]["rgba_sha256"], fresh["static"]["blocks"]["0x46"]["rgba_sha256"])


if __name__ == "__main__":
    unittest.main()

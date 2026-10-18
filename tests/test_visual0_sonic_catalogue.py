"""VISUAL-0 normal-Sonic frame/state catalogue: committed cache consistency, and (when the ROM is supplied) regeneration."""
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import visual0_sonic_catalogue as C

CACHE = ROOT / "data/rom-cache/visual0/sonic-animation-catalogue.json"


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
        cls.frames = {f["frame"]: f for f in cls.d["frames"]}
        cls.states = {s["state"]: s for s in cls.d["states"]}

    def test_shape(self):
        self.assertEqual(len(self.d["frames"]), 98)
        self.assertEqual(len(self.d["states"]), 55)
        self.assertTrue(self.frames["0x00"]["empty"])
        self.assertTrue(all(not f.get("empty") for k, f in self.frames.items() if k != "0x00"))

    def test_every_script_frame_exists_and_only_one_frame_is_unreferenced(self):
        used = set()
        for s in self.d["states"]:
            used |= set(s["frames"])
        self.assertTrue(used <= set(self.frames))
        self.assertEqual(sorted(set(self.frames) - used - {"0x00"}), ["0x3B"])

    def test_known_state_scripts(self):
        walk_ops = self.states["0x05"]["ops"]
        sel = [o for o in walk_ops if o["op"] == "FF 05"][0]["selector"]
        self.assertEqual(sel["selector"], "0x8EE1")
        self.assertEqual(sel["frames"], [1, 2, 3, 4, 5, 6])
        self.assertEqual(sel["strip_frames"], [0x3C, 0x3D, 0x3E, 0x3F])
        self.assertEqual(sel["side_contact_frame"], 0x5E)
        roll = [o for o in self.states["0x09"]["ops"] if o["op"] == "FF 05"][0]["selector"]
        self.assertEqual(len(roll["frames"]), 20)
        self.assertEqual(sorted(set(roll["frames"])), [0x25, 0x26, 0x27, 0x28, 0x29])
        loop = [o for o in self.states["0x0D"]["ops"] if o["op"] == "FF 05"][0]["selector"]
        self.assertEqual(loop["selector"], "0x903D")
        self.assertEqual(len(loop["pairs"]), 51)
        self.assertEqual(self.states["0x1E"]["frames"], ["0x17"])
        self.assertEqual(self.states["0x1F"]["frames"], ["0x18"])
        self.assertEqual(self.states["0x0F"]["frames"], ["0x22", "0x23", "0x24"])
        self.assertEqual(self.states["0x11"]["frames"], ["0x38", "0x39", "0x3A"])
        self.assertEqual(self.states["0x12"]["frames"], ["0x0B"])

    def test_state_11_hashes_match_the_earlier_independent_extraction(self):
        earlier = json.loads((ROOT / "data/rom-cache/thz1/player-state-11-graphics.json").read_text(encoding="utf-8"))
        expect = {x["animation_frame_index"]: x["render"]["rgba_sha256"] for x in earlier["frames"]}
        for f, h in expect.items():
            self.assertEqual(self.frames[f]["rgba_sha256_thz1_palette"], h)

    def test_poc_thz1_resources_are_pixel_identical_and_aqz_ones_are_palette_variants(self):
        res = self.d["poc_resources"]
        thz = {k: v for k, v in res.items() if k.startswith("SPR_chaos_player_frame_")}
        self.assertEqual(len(thz), 23)
        for name, info in thz.items():
            self.assertEqual(len(info["matches"]), 1, name)
            self.assertTrue(info["matches"][0]["rgba_equal"], name)
            self.assertTrue(info["matches"][0]["origin_equal"], name)
        for name, info in res.items():
            if name.startswith("SPR_chaos_aqz_player_frame_"):
                self.assertTrue(info["matches"][0]["alpha_mask_equal"], name)
                self.assertFalse(info["matches"][0]["rgba_equal"], name)   # negative control: a different palette really differs

    def test_poc_presentation_boundary(self):
        pres = self.d["poc_presentation"]
        self.assertEqual(pres["states_presented_from_rom_frames"],
                         ["0x09", "0x0A", "0x0B", "0x0E", "0x10", "0x12", "0x14", "0x1B", "0x1C", "0x21"])
        # states that THZ1 play actually used but the POC draws with inherited SPR_sonic_* art
        observed = {int(k, 16) for k in self.d["emulated_play"]["observed_state_frame_counts"]}
        presented = {int(x, 16) for x in pres["states_presented_from_rom_frames"]}
        for state in (0x01, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x0F, 0x1E, 0x1F, 0x20):
            self.assertIn(state, observed)
            self.assertNotIn(state, presented)

    def test_emulated_play_is_inside_the_static_catalogue(self):
        play = self.d["emulated_play"]
        self.assertEqual(play["frames_outside_static_catalogue"], [])
        self.assertGreaterEqual(len(play["observed_state_frame_counts"]), 20)


@unittest.skipIf(find_rom() is None, "ROM not supplied (set SONIC_CHAOS_ROM)")
class Regeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = C.R.load(find_rom())
        cls.fresh = C.build(cls.rom)
        cls.cached = json.loads(CACHE.read_text(encoding="utf-8"))

    def test_frames_states_engine_are_regenerated_exactly(self):
        for key in ("engine", "frames", "states"):
            fresh = json.loads(json.dumps(self.fresh[key]))
            cached = self.cached[key]
            self.assertEqual(fresh, cached, key)

    def test_negative_control_wrong_palette_changes_the_hash(self):
        frame1 = self.cached["frames"][1]["rgba_sha256_thz1_palette"]
        other_palette = C.A.palette_rgba(self.rom, 0)
        mapping = C.A.object_mapping(self.rom, 1)
        ptr = C.R.u16(self.rom, C.A.cpu15_to_rom(mapping["mapping_cpu"]) + 2)
        parsed = C.A.parse_frame_record(self.rom, ptr)
        src = C.tile_source(self.rom, 1)
        w, h, rgba, _ = C.render(self.rom, parsed, src["_raw"], other_palette)
        self.assertNotEqual(C.sha(rgba), frame1)

    def test_markdown_is_deterministic(self):
        text = C.render_markdown(self.cached)
        self.assertEqual(text, (ROOT / "docs/visual0-sonic-state-frame-catalogue.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

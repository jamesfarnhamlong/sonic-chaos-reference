#!/usr/bin/env python3
"""U5-A part D tests: the original start-up sequence and the opening cinematic.

Part 1 needs no ROM: committed JSON consistency (the same validation `--validate` runs), the actor/camera/machine model re-run and compared with the committed
per-update replay, the fade model on the committed palette records, negative controls, and the decoded flow facts.
Part 2 needs the canonical ROM (SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms) and the `z80` package: it re-decodes the static layer, replays the first
300 frames of the unmodified ROM against the committed per-update rows and re-composes background and sprites for sample frames.  The complete regeneration
check is `python tools/u5a_opening.py ROM --check` (about one minute).
"""
import copy
import hashlib
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import u5a_opening as O  # noqa: E402

ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")))
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == 524288 and hashlib.sha256(data).hexdigest() == ROM_SHA:
            return data
    return None


STATIC = O.load_json(O.STATIC_JSON)
OBS = O.load_json(O.OBS_JSON)
REPLAY = O.load_json(O.REPLAY_JSON)
CENSUS = O.load_json(O.CENSUS_JSON)
rom_only = unittest.skipIf(canonical_rom() is None, "verified ROM not available")
C = {n: i for i, n in enumerate(O.REPLAY_COLUMNS)}


class CommittedData(unittest.TestCase):
    def test_validate_function_passes(self):
        self.assertGreaterEqual(O.validate(STATIC, OBS, REPLAY), 25)

    def test_hashes_and_sizes(self):
        for d in (STATIC, OBS, REPLAY):
            self.assertEqual(d["rom_sha256"], ROM_SHA)
        for p in (O.STATIC_JSON, O.OBS_JSON, O.REPLAY_JSON, O.CENSUS_JSON):
            self.assertLess(p.stat().st_size, 200_000, p)

    def test_model_reproduces_the_replay(self):
        rows = O.replay_rows(O.model_opening())
        self.assertEqual(rows, REPLAY["rows"])

    def test_model_is_independent_of_the_emulator_data(self):
        # the observed block records zero mismatching columns for all 738 updates
        self.assertEqual(OBS["model_vs_observed"]["rows"], 738)
        self.assertEqual(OBS["model_vs_observed"]["mismatching_columns"], {})

    def test_flow_facts(self):
        s = STATIC
        self.assertEqual(s["dispatcher"]["bit_to_handler"]["5"], "0x2B77")
        self.assertEqual(s["opening_routine"]["updates_total"], 738)
        seq = [x for x in s["opening_routine"]["sequence"] if "loop" in x]
        self.assertEqual([(x["loop"], x["BC"]) for x in seq], [("$07B8", 0x1E), ("$079F", 0x2C4)])
        self.assertEqual(s["level"]["header"]["width_cells"], 256)
        self.assertEqual(s["level"]["layout"]["height_cells"], 8)

    def test_state_29_script_is_shared_by_sonic_and_tails(self):
        a = STATIC["actors"]["player_state_29"]
        self.assertTrue(a["scripts_identical"])
        ops = a["sonic_type_1"]["ops"]
        self.assertEqual([o.get("command") for o in ops][:4], ["FF 02", "FF 0E", "FF 05", "FF 0F"])
        self.assertEqual(ops[1]["args"], "96")                    # 150 iterations of the run selector (4 updates each)
        self.assertEqual(ops[0]["args"], "00060000")             # X speed $0600 = 6.0 px per update

    def test_machine_scripts(self):
        m = STATIC["actors"]["machine_type_1F"]
        self.assertEqual(m["state_5"]["ops"][0]["duration"], 224)
        self.assertEqual(sum(1 for o in m["state_3"]["ops"] if o.get("command") == "FF 05"), 4)
        cbs = [o["callback"] for o in m["state_3"]["ops"] if o.get("command") == "FF 05"]
        self.assertEqual(cbs, ["0xAF8C", "0xAF94", "0xAF94", "0xAF8C"])

    def test_replay_story(self):
        rows = REPLAY["rows"]
        xs = [r[C["actor_x"]] for r in rows]
        self.assertEqual(xs[0], 96)
        self.assertEqual(xs[1], 102)
        self.assertEqual(xs[660], 96 + 6 * 660)
        self.assertEqual(xs[661], 3550)                               # Tails: camera X - 32 + 4
        self.assertEqual(rows[661][C["actor_type"]], 2)
        self.assertEqual(rows[737][C["actor_x"]], 3854)
        mach = [(r[0], r[C["machine_state"]]) for r in rows if r[C["machine_type"]]]
        self.assertEqual(mach[0], (40, 0))
        self.assertEqual(mach[-1], (737, 5))

    def test_camera_rule(self):
        rows = REPLAY["rows"]
        for u in range(1, 601):
            self.assertEqual(rows[u][C["cam_x"]], max(0, rows[u][C["actor_x"]] - 118), u)       # follows the actor 118 px behind
            self.assertEqual(rows[u][C["bg_x"]], rows[u][C["cam_x"]] + 1)
        self.assertEqual({rows[u][C["cam_x"]] for u in range(601, 738)}, {3578})

    def test_fade_model(self):
        f = OBS["fade"]
        self.assertTrue(f["observed_equals_model"])
        self.assertEqual(f["fade_in_passes"], 4)
        self.assertEqual(f["fade_out_passes"], 3)
        self.assertEqual(f["pass_interval_updates"], 5)

    def test_compose_check_results(self):
        c = OBS["compose_check"]
        self.assertEqual((c["bg_mismatch_pixels"], c["sprite_mismatch_pixels"]), (0, 0))
        self.assertGreaterEqual(c["frames_checked"], 150)
        self.assertTrue(c["r8_follows_d174_plus_1_everywhere"])

    def test_census(self):
        self.assertEqual(CENSUS["demo_zones_in_order"], [0, 1, 2])
        self.assertEqual(CENSUS["first_cycle_frames"], {"opening": 871, "title": 1310, "attract_demo": 1230})
        ids = {a["id"]: a for a in CENSUS["alternatives"]}
        self.assertFalse(ids["A5"]["present"])
        self.assertTrue(ids["A1"]["present"])
        self.assertEqual(CENSUS["skip_test"]["frames_from_press_to_title_flag"], 63)

    def test_music_request(self):
        self.assertEqual([s["request"] for s in OBS["sounds"]][:1], [0x90])

    # ---- negative controls ----------------------------------------------------------------------------------------------------------
    def test_negative_control_wrong_machine_trigger_distance(self):
        saved = O.Machine.update

        def bad(self, cam_x, cam_y, player_x):
            if self.cb == "af4e":
                self.cb = "never"
            return saved(self, cam_x, cam_y, player_x)
        O.Machine.update = bad
        try:
            rows = O.replay_rows(O.model_opening())
        finally:
            O.Machine.update = saved
        self.assertNotEqual(rows, REPLAY["rows"])

    def test_negative_control_wrong_camera_lead(self):
        saved = O.CAMERA_LEAD
        O.CAMERA_LEAD = 117
        try:
            rows = O.replay_rows(O.model_opening())
        finally:
            O.CAMERA_LEAD = saved
        self.assertNotEqual(rows, REPLAY["rows"])

    def test_negative_control_validate_detects_a_broken_replay(self):
        bad = copy.deepcopy(REPLAY)
        bad["rows"][300][C["actor_x"]] += 1
        with self.assertRaises(AssertionError):
            O.validate(STATIC, OBS, bad)


@rom_only
class RomBacked(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = O.load_rom(ROM_PATH)

    def test_static_layer_regenerates(self):
        self.assertEqual(O.dumps(O.build_static(self.rom)), O.STATIC_JSON.read_text(encoding="utf-8"))

    def test_first_300_frames_match_the_committed_updates(self):
        obs, samples = O.run_power_on(self.rom, 300, samples=(150, 280))
        rows = O.replay_rows(O.model_opening())
        cols = O.UPDATE_COLUMNS
        model = O.model_opening()
        bad, _ = O.compare_model(model[:len(obs["updates"])], obs["updates"])
        self.assertEqual(bad, {})
        self.assertGreater(len(obs["updates"]), 200)
        self.assertEqual(obs["sounds"][0]["request"], 0x90)
        res = O.compose_check(self.rom, obs, samples)
        for f, v in res.items():
            self.assertEqual((v["bg_mismatch"], v["sprite_mismatch"]), (0, 0), f)
        self.assertEqual(len(rows), 738)
        self.assertEqual(len(cols), 27)

    def test_window_table_and_actor_scripts_regenerate(self):
        w = O.window_table(self.rom)
        self.assertEqual(w["counts"], STATIC["actors"]["window_table"]["counts"])
        self.assertEqual(w["sha256"], STATIC["actors"]["window_table"]["sha256"])


if __name__ == "__main__":
    unittest.main()

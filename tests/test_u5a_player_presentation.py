#!/usr/bin/env python3
"""U5-A parts A-C tests: strip run / strip fall, Spring Shoes pose, weak-spring tumble.

Part 1 needs no ROM: committed JSON consistency (the same validation `--validate` runs), the POC-selector transcription replayed over the committed ROM
observations and over the committed Research spring/airborne cache, reused-evidence hashes, negative controls and size/hygiene checks.
Part 2 needs the canonical ROM (SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms) and the `z80` package: it re-derives the static layer, re-runs two
whole-game fixtures and checks the selector code bytes.  The complete regeneration check is
`python tools/u5a_player_presentation.py ROM --check [--poc POC_CHECKOUT]` (about ten seconds).
"""
import copy
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import u5a_player_presentation as P  # noqa: E402

ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")))
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == 524288 and hashlib.sha256(data).hexdigest() == ROM_SHA:
            return data
    return None


STATIC = P.load_json(P.STATIC_JSON)
OBS = P.load_json(P.OBS_JSON)
POC = P.load_json(P.POC_JSON)
rom_only = unittest.skipIf(canonical_rom() is None, "verified ROM not available")


class CommittedData(unittest.TestCase):
    def test_validate_function_passes(self):
        self.assertGreaterEqual(P.validate(STATIC, OBS, POC), 200)

    def test_files_are_small_and_pixel_free(self):
        for p in (P.STATIC_JSON, P.OBS_JSON, P.POC_JSON, P.EXPORT_JSON):
            self.assertLess(p.stat().st_size, 200_000, p)
        text = P.STATIC_JSON.read_text(encoding="utf-8")
        self.assertNotIn('"rgba":', text)
        self.assertNotIn("PNG", text)

    def test_base_commit_and_rom_hash(self):
        self.assertEqual(STATIC["rom_sha256"], ROM_SHA)
        self.assertEqual(OBS["rom_sha256"], ROM_SHA)
        self.assertEqual(POC["poc_commit"], P.POC_COMMIT)

    def test_strip_frames_geometry(self):
        fr = STATIC["frames"]["frames"]
        for f in ("0x3C", "0x3D", "0x3E", "0x3F"):
            self.assertEqual(fr[f]["canvas_width"], 24)
            self.assertEqual(fr[f]["canvas_height"], 32)
            self.assertEqual((fr[f]["gamemaker_origin_x"], fr[f]["gamemaker_origin_y"]), (12, 28))
        self.assertEqual((fr["0x0B"]["gamemaker_origin_x"], fr["0x0B"]["gamemaker_origin_y"]), (10, 32))
        # the four strip frames and the standing frame are distinct images
        self.assertEqual(len({fr[f]["index_sha256"] for f in ("0x0B", "0x3C", "0x3D", "0x3E", "0x3F", "0x07", "0x08", "0x09", "0x0A")}), 9)

    def test_sonic_palette_is_identical_in_every_act(self):
        pal = STATIC["sprite_palettes"]
        self.assertTrue(pal["sonic_colours_identical_in_all_acts"])
        self.assertEqual(len(pal["acts"]), 19)                      # 18 acts + the title-zone opening level
        self.assertEqual(pal["indices_used_union"], list(range(1, 12)))

    def test_strip_census(self):
        c = STATIC["strip_census"]["cells_by_act"]
        self.assertEqual(c, {"gpz1": 21, "gpz2": 24, "mghz1": 56, "mghz2": 26, "mghz3": 41})

    def test_selector_constants(self):
        s = STATIC["selectors"]
        self.assertEqual(s["walk_selector"]["side_contact"], {"frame": 0x5E, "duration": 2})
        self.assertEqual(s["walk_selector"]["strip"]["frames"], [0x3C, 0x3D, 0x3E, 0x3F])
        self.assertEqual(s["run_selector"]["duration"], 4)
        self.assertFalse(s["run_selector"]["side_contact_branch"])

    def test_state_12_is_one_frame_0b(self):
        prog = [r for r in STATIC["state_programs"]["0x12"]["program"] if "frame" in r]
        self.assertEqual([(r["duration"], r["frame"]) for r in prog], [(4, 0x0B)])
        self.assertEqual(STATIC["reused_evidence"]["spring_shoes_state_12"]["player_frame_values_in_state_12"], [11])

    def test_tumble_programs(self):
        sp = STATIC["state_programs"]
        self.assertEqual([x["frame"] for x in sp["0x14"]["play_order"]["frame_cadence"]], ["0x1C", "0x1D", "0x1E", "0x1F", "0x20", "0x21"])
        self.assertEqual({x["updates"] for x in sp["0x14"]["play_order"]["frame_cadence"]}, {4})
        self.assertEqual({x["updates"] for x in sp["0x1C"]["play_order"]["frame_cadence"]}, {8})
        self.assertEqual(sp["0x0B"]["play_order_d448_bit0_clear_weak"]["cycle_updates"], 82)
        self.assertEqual(sp["0x0B"]["play_order_d448_bit0_set_strong"]["cycle_updates"], 4)

    def test_reused_cache_hashes_still_match(self):
        for name, digest in STATIC["reused_evidence"]["cache_sha256"].items():
            self.assertEqual(hashlib.sha256(P.cache_path(name).read_bytes()).hexdigest(), digest, name)


class PocTranscription(unittest.TestCase):
    """The POC selector (literal transcription) shown ROM-observed state sequences must reproduce the ROM frame on every presented update."""

    @classmethod
    def setUpClass(cls):
        cls.programs = {int(k, 16): v for k, v in POC["programs_by_state"].items()}
        cls.supported = set(POC["presentation_supported_states"]["decimal"])

    def run_rows(self, columns, rows):
        res = P.mirror_rows(self.programs, rows, columns, self.supported)
        presented = [(u, rf, pf) for u, rf, pf in res if isinstance(pf, int)]
        return presented, [x for x in presented if x[1] != x[2]]

    def test_strip_fall_and_weak_spring_cases_match(self):
        total = 0
        for c in OBS["cases"]:
            presented, bad = self.run_rows(c["columns"], c["rows"])
            self.assertEqual(bad, [], c["id"])
            total += len(presented)
        self.assertGreater(total, 90)

    def test_research_spring_airborne_cache_matches(self):
        sa = P.load_json(P.cache_path("player-spring-airborne"))
        total = 0
        for grp in ("emulated_flights_thz", "stomp_and_boss", "aqz_chains"):
            for s in sa[grp]["scenarios"]:
                presented, bad = self.run_rows(s["columns"], s["rows"])
                self.assertEqual(bad, [], (grp, s["id"]))
                total += len(presented)
        self.assertGreater(total, 1500)

    def test_negative_control_wrong_tumble_order_is_detected(self):
        programs = copy.deepcopy(self.programs)
        rec = [op for op in programs[20] if op[0] == 0]
        rec[0][2], rec[1][2] = rec[1][2], rec[0][2]
        case = next(c for c in OBS["cases"] if c["id"] == "gpz2_strip_walk_plus3_right")
        res = P.mirror_rows(programs, case["rows"], case["columns"], self.supported)
        self.assertTrue(any(isinstance(pf, int) and rf != pf for _, rf, pf in res))

    def test_negative_control_wrong_d448_branch_is_detected(self):
        sa = P.load_json(P.cache_path("player-spring-airborne"))
        weak = next(s for s in sa["emulated_flights_thz"]["scenarios"] if s["id"] == "t26_weak_fixed")
        rows = copy.deepcopy(weak["rows"])
        di = weak["columns"].index("d448")
        for r in rows:
            r[di] = 255                                         # pretend the spring were strong: the POC would show the tall pose $61
        res = P.mirror_rows(self.programs, rows, weak["columns"], self.supported)
        self.assertTrue(any(isinstance(pf, int) and rf != pf for _, rf, pf in res))

    def test_pixel_parity_and_missing_resources(self):
        pp = POC["pixel_parity_with_rom_frames"]
        for f in ("0x01", "0x02", "0x03", "0x04", "0x05", "0x06", "0x1C", "0x1D", "0x1E", "0x1F", "0x20", "0x21", "0x61"):
            self.assertTrue(pp[f]["rgba_equal"] and pp[f]["origin_equal"], f)
        for f in ("0x07", "0x08", "0x09", "0x0A", "0x0B", "0x3C", "0x3D", "0x3E", "0x3F", "0x5E"):
            self.assertIsNone(pp[f]["poc_resource"], f)

    def test_poc_does_not_present_walk_run_idle_or_shoes(self):
        for s in (1, 5, 6, 18):
            self.assertNotIn(s, self.supported)
        self.assertIn("SPR_player_jump", POC["state_12_branch"]["line"])


class ObservedFixtures(unittest.TestCase):
    def case(self, cid):
        return next(c for c in OBS["cases"] if c["id"] == cid)

    def test_strip_run_uses_only_strip_frames_after_the_carried_record(self):
        runs = self.case("gpz2_strip_run_right")["summary"]["frame_runs_by_executing_state"]["0x06"]
        self.assertEqual([r[0] for r in runs[1:5]], ["0x3F", "0x3C", "0x3D", "0x3E"])
        self.assertTrue(all(r[1] == 4 for r in runs[:-1]))

    def test_run_left_keeps_the_left_facing_bit(self):
        c = self.case("mghz1_upper_strip_run_left")
        self.assertEqual(c["summary"]["facing_values"], [1])
        self.assertEqual(c["synthetic_facing_bit"], 1)

    def test_marker_set_on_ordinary_floor_is_cleared_by_the_selector(self):
        c = self.case("gpz2_ordinary_run_marker_set")
        self.assertEqual(c["summary"]["marker_values"], [0])
        self.assertEqual(c["summary"]["frame_runs_by_executing_state"]["0x06"][1][0], "0x0A")

    def test_platform_riding_is_not_the_strip(self):
        for cid in ("gpz2_platform28_stand", "gpz2_platform28_walk_right", "gpz1_platform28_moving_stand", "gpz2_deck_1c_walk_run"):
            self.assertEqual(self.case(cid)["summary"]["marker_values"], [0], cid)
        m = self.case("gpz1_platform28_moving_stand")
        xs = [r[m["columns"].index("x")] for r in m["rows"]]
        self.assertGreater(xs[-1] - xs[10], 90)                  # the moving platform carries Sonic ~100 px while he shows the idle frame
        self.assertEqual({f for f, _ in m["summary"]["frame_runs_by_executing_state"]["0x01"]}, {"0x0B"})

    def test_walk_below_maximum_on_the_strip_requests_the_special_fall_at_once(self):
        c = self.case("gpz2_strip_walk_plus3_right")
        self.assertEqual(c["summary"]["first_update_with_requested_14"], 1)
        self.assertEqual(c["summary"]["frame_runs_by_executing_state"]["0x14"][0], ["0x1C", 4])

    def test_run_then_release_chain(self):
        c = self.case("gpz2_strip_run_then_release")
        self.assertEqual([s for s, _ in c["summary"]["executing_state_runs"][:3]], ["0x06", "0x05", "0x14"])

    def test_negative_control_validate_detects_a_broken_strip_order(self):
        bad = copy.deepcopy(OBS)
        case = next(c for c in bad["cases"] if c["id"] == "gpz2_strip_run_right")
        runs = case["summary"]["frame_runs_by_executing_state"]["0x06"]
        runs[1], runs[2] = runs[2], runs[1]
        with self.assertRaises(AssertionError):
            P.validate(STATIC, bad, POC)


@rom_only
class RomBacked(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = P.load_rom(ROM_PATH)

    def test_selector_bytes_and_static_layer_regenerate(self):
        self.assertEqual(P.dumps(P.build_static(self.rom)), P.STATIC_JSON.read_text(encoding="utf-8"))

    def test_two_whole_game_fixtures_regenerate(self):
        g = P.make_lab(self.rom, "gpz", 1)
        a = P.run_case(g, "gpz2_strip_run_right", "x", dict(x=528, y=686, vx=0x400, vy=0, cur=6, f3=0, floor=True, prev=0x59), 8, 48)
        b = P.run_case(g, "gpz2_ordinary_run_marker_set", "x", dict(x=1748, y=238, vx=0x400, vy=0, cur=6, f3=0, floor=True, prev=0x81, p24=1), 8, 24)
        for new in (a, b):
            old = next(c for c in OBS["cases"] if c["id"] == new["id"])
            self.assertEqual(new["rows"], old["rows"])

    def test_poc_free_frames_are_ordinary_player_frames(self):
        # the POC already contains frames 01-06, 1C-21, 61: the ROM render of those must equal what the Research cache recorded earlier
        sa = P.load_json(P.cache_path("player-spring-airborne"))
        fr = STATIC["frames"]["frames"]
        for f in ("0x1C", "0x1D", "0x1E", "0x1F", "0x20", "0x21", "0x61"):
            self.assertEqual(fr[f]["rgba_sha256_thz1_palette"], sa["frames"]["frames"][f]["rgba_sha256_thz1_palette"], f)


if __name__ == "__main__":
    unittest.main()

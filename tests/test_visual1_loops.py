"""VISUAL-1 Part A: THZ1 loop presentation ($0C/$0D/$13, selector $903D, frames $2A..$5D).

``CommittedCache`` needs no ROM.  ``Regeneration`` re-executes the original ROM (set SONIC_CHAOS_ROM).
"""
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import visual1_loops as L

CACHE = ROOT / "data/rom-cache/visual1/loops-thz1.json"
CONTRACT = ROOT / "data/visual1/loop-contract.json"
SEARCH = ROOT / "data/rom-cache/visual1/loops-natural-search.json"


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
        cls.s = cls.d["static"]
        cls.e = cls.d["emulated"]
        cls.c = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.scen = {sc["name"]: sc for grp in ("natural", "controlled") for sc in cls.e[grp]}

    def test_assembly_verified(self):
        for name in ("dispatch_6c82", "entry_left_6cba", "entry_right_6ccd", "entry_setup_3eab", "route_right_3c1b", "route_left_3dae", "selector_903d",
                     "selector_roll_8f76", "stubs_03c8", "divide_2605"):
            self.assertIn(name, self.s["assembly"])

    def test_dispatch_table(self):
        rows = self.s["dispatch"]["rows"]
        self.assertEqual({k: v["handler"] for k, v in rows.items() if k in ("0x50", "0x51", "0x52")},
                         {"0x50": "0x6CBA", "0x51": "0x6CBA", "0x52": "0x6CCD"})
        self.assertTrue(all(rows["0x%02X" % b]["handler"] == "0x6CB9" for b in range(0x48, 0x50)))

    def test_pair_table(self):
        pt = self.s["pair_table"]
        self.assertEqual(pt["divisor"], 13)
        self.assertEqual(pt["pairs"][:4], [[1, 2], [3, 4], [5, 6], [42, 43]])
        self.assertEqual(pt["pairs"][9], [64, 65])
        self.assertEqual(pt["pairs"][23], [92, 93])
        self.assertEqual((pt["first_rotated_pair_index"], pt["last_rotated_pair_index"], pt["rotated_pairs"]), (3, 23, 21))
        self.assertEqual(len(pt["rotated_frames"]), 42)                                  # $2A..$35 and $40..$5D
        self.assertEqual(pt["progress_at_first_walk_pair_after"], 312)
        self.assertTrue(pt["pairs_from_24_all_walk"])

    def test_route_tables_mirror_each_other(self):
        r = self.s["route_tables"]
        self.assertEqual(r["right_3c1b"]["y_sha256"], r["left_3dae"]["y_sha256"])        # same heights
        self.assertNotEqual(r["right_3c1b"]["x_sha256"], r["left_3dae"]["x_sha256"])      # mirrored X
        for k in ("0", "16", "72", "144", "216", "288", "360", "384"):
            self.assertEqual(r["right_3c1b"]["samples"][k][0], -r["left_3dae"]["samples"][k][0])
            self.assertEqual(r["right_3c1b"]["samples"][k][1], r["left_3dae"]["samples"][k][1])

    def test_roll_selector(self):
        rs = self.s["roll_selector"]
        self.assertEqual(rs["frames"], [37, 38, 39, 40, 41, 38, 39, 40, 37, 41, 39, 40, 37, 38, 41, 40, 37, 38, 39, 41])
        self.assertEqual(rs["durations_by_abs_x_speed_hi"][:8], [10, 8, 6, 5, 4, 3, 2, 2])

    def test_thz1_inventory(self):
        inv = self.s["thz1"]
        self.assertEqual(inv["block_57_cells_in_thz1"], 0)
        a, b = inv["structures"]
        self.assertEqual((a["cells_x"], a["cells_y"], a["right_gate_cells"], a["left_gate_cells"]), ([72, 75], [9, 13], [[74, 13]], [[73, 13]]))
        self.assertEqual((b["cells_x"], b["cells_y"], b["right_gate_cells"], b["left_gate_cells"]), ([88, 91], [12, 16], [[90, 16]], [[89, 16]]))
        self.assertEqual((a["right_gate_world_x"], b["right_gate_world_x"]), ([2368], [2880]))
        self.assertEqual(a["alt_gate_cells"] + b["alt_gate_cells"], [])

    def test_every_traversal_follows_the_source_rules(self):
        n = 0
        for sc in self.scen.values():
            for tv in sc["traversals"]:
                n += 1
                self.assertEqual(tv["selector_rule_violations"], 0, sc["name"])
                self.assertEqual(tv["route_model_check"]["progress_mismatches"], 0, sc["name"])
                self.assertEqual(tv["route_model_check"]["model_outcome"], tv["route_model_check"]["observed_outcome"]
                                 if tv["route_model_check"]["observed_outcome"] != "none" else tv["route_model_check"]["model_outcome"], sc["name"])
        self.assertGreaterEqual(n, 14)

    def test_natural_entries_from_the_real_start(self):
        for seed in (13, 6, 97):
            sc = self.scen["natural_seed_%d" % seed]
            self.assertTrue(sc["evidence"].startswith("NATURAL"))
            self.assertTrue(sc["traversals"])
            for tv in sc["traversals"]:
                e = tv["entry_context"]
                self.assertEqual((e["route"], tv["state"], e["plane"], e["cur_block"], e["prev_block"]), ("right_3eab", "0x0C", 0, 0x52, 0x51))
                self.assertIn(e["x"], range(2368, 2373) if e["y"] < 470 else range(2880, 2886))
        sc13 = self.scen["natural_seed_13"]
        self.assertEqual([tv["entry_context"]["vx"] for tv in sc13["traversals"]], [1024, 1024])
        self.assertEqual([tv["ticks_in_state"] for tv in sc13["traversals"]], [111, 111])
        self.assertEqual({tv["exit_event"]["kind"] for tv in sc13["traversals"]}, {"exit_right_3ca9"})

    def test_natural_search_summary(self):
        s = json.loads(SEARCH.read_text(encoding="utf-8"))
        self.assertEqual(s["seeds"], [0, 120])
        entries = [(r[0], e) for r in s["rows"] for e in r[2]]
        self.assertEqual({e[1] for _, e in entries}, {12})                                 # only $0C was ever entered naturally
        self.assertEqual(sum(1 for r in s["rows"] if r[2]), 9)
        self.assertEqual(len(entries), self.e["natural_search"]["entries_seen"]["state_0c"])

    def test_slow_entries_bail_out(self):
        sc = self.scen["natural_seed_6"]
        outcomes = [(tv["entry_context"]["vx"], "bailout" if tv["bailout_event"] else "exit") for tv in sc["traversals"]]
        self.assertEqual(outcomes[:3], [(128, "bailout"), (128, "bailout"), (242, "bailout")])
        bailed = [tv for tv in sc["traversals"] if tv["bailout_event"]]
        for tv in bailed:
            self.assertEqual(tv["after"]["state"], 0x1D)                                   # falling state after the bailout
        starts = self.e["entry_speed_by_start_position"]
        self.assertEqual([starts[k][0]["entry_vx"] for k in ("2272", "2290", "2300", "2335")], [512, 352, 208, 128])
        self.assertEqual({starts[k][0]["outcome"] for k in starts}, {"bailout"})

    def test_minimum_completing_speed(self):
        inj = self.e["route_speed_injection"]
        self.assertEqual((inj["0x0355"]["observed_outcome"], inj["0x0355"]["observed_ticks"]), ("bailout", 86))
        self.assertEqual((inj["0x0356"]["observed_outcome"], inj["0x0356"]["observed_ticks"]), ("exit", 183))
        for v in inj.values():
            self.assertEqual(v["progress_mismatches"], 0)
            self.assertEqual(v["observed_outcome"], v["model_outcome"])
        self.assertEqual(L.route_model(0x0356)[1], "exit")
        self.assertEqual(L.route_model(0x0355)[1], "bailout")

    def test_right_traversal_frames_and_timing(self):
        tv = self.scen["hold_right_from_(2100,380)"]["traversals"][0]
        self.assertEqual((tv["ticks_in_state"], tv["entry_context"]["vx"], tv["progress_at_last_tick"]), (111, 1024, 384))
        self.assertEqual(tv["facing_bit4_values"], [0])
        self.assertEqual(tv["plane_values_in_order"], [0, 1])
        self.assertEqual([f for f, _ in tv["frame_runs"]][:8], [1, 3, 42, 46, 48, 50, 64, 66])
        self.assertEqual(tv["after"]["state"], 6)
        self.assertTrue(all(n in (6, 3) for _, n in tv["frame_runs"]))                       # records last 6 updates (last one cut by the exit)
        self.assertEqual(tv["rotated_frames_used"][0], 42)

    def test_left_traversal_is_mirrored(self):
        tv = self.scen["right_then_left_into_loop_1"]["traversals"][1]
        self.assertEqual((tv["state"], tv["entry_context"]["route"], tv["entry_context"]["plane"]), ("0x0D", "left_3ee1", 1))
        self.assertEqual(tv["facing_bit4_values"], [1])
        self.assertEqual((tv["entry_context"]["cur_block"], tv["entry_context"]["prev_block"]), (0x51, 0x52))
        self.assertEqual(tv["plane_values_in_order"], [1, 0])
        self.assertLess(tv["entry_context"]["vx"], 0)
        self.assertEqual(tv["after"]["state"], 6)

    def test_rolling_uses_the_alternate_selector(self):
        tv = self.scen["spin_dash_roll_through_both_loops"]["traversals"][0]
        self.assertEqual(tv["rolling_values"], [1])
        self.assertEqual(tv["selector_to_roll_calls"], tv["selector_calls"])
        self.assertEqual(set(tv["distinct_frames"]), {37, 38, 39, 40, 41})
        self.assertEqual(tv["rotated_frames_used"], [])
        self.assertEqual(tv["after"]["state"], 9)                                            # rolling exit keeps the ball state
        run = self.scen["natural_seed_6"]["traversals"][3]
        self.assertEqual(run["rolling_values"], [1])
        self.assertEqual(run["after"]["state"], 9)
        slow = self.scen["roll_started_while_running"]["traversals"][0]
        durations = [d for _, d in slow["frame_runs"]]
        self.assertEqual(durations[:3], [6, 6, 6])
        self.assertEqual(durations[3:6], [8, 8, 8])                                          # duration grows as the X speed high byte falls

    def test_sprite_composition_matches_the_real_sat(self):
        for sc in self.scen.values():
            c = sc["sat_composition"]
            if not c:
                continue
            self.assertEqual(c["loop_matched"], c["loop_frames"], sc["name"])
            self.assertEqual(c["matched_only_under_wrong_convention"], 0, sc["name"])
        left = self.scen["right_then_left_into_loop_1"]["sat_composition"]
        self.assertGreater(left["loop_facing_set_frames"], 100)
        self.assertEqual(left["loop_facing_set_matched"], left["loop_facing_set_frames"])

    def test_poc_findings(self):
        poc = self.d["poc"]
        for side in ("right", "left"):
            self.assertTrue(poc["movement_tables"][side]["equals_rom_x"])
            self.assertTrue(poc["movement_tables"][side]["equals_rom_y"])
        self.assertTrue(poc["loop_tick"]["presentation_rotation"])
        self.assertFalse(poc["loop_tick"]["selects_rom_frames_2a_5d"])
        self.assertEqual(poc["poc_frame_sprites"]["loop_rotation_frames_missing"], 42)
        self.assertFalse(poc["loop_entry"]["uses_block_transition"])
        self.assertTrue(poc["loop_entry"]["speed_cap_px"])

    def test_contract_is_consistent_with_the_cache(self):
        c = self.c
        self.assertEqual(c["route_algorithm"]["minimum_completing_entry_speed_8_8"], 0x0356)
        self.assertEqual(c["route_algorithm"]["updates_at_1024"], 111)
        self.assertEqual(c["frame_selection"]["rotation_ends_at_progress"], 312)
        ref = c["reference_traversals"]
        self.assertEqual(len(ref["right_running_entry_vx_1024"]["ticks"]), 111)
        self.assertEqual(ref["left_running_entry_vx_-944"]["entry"]["f04"] >> 4 & 1, 1)       # Sonic already faces left when the left route is entered
        self.assertEqual(c["natural_evidence"]["seeds"], [13, 6, 97])


class ModelUnit(unittest.TestCase):
    def test_route_model_reference_points(self):
        rows, outcome = L.route_model(1024)
        self.assertEqual((outcome, len(rows), rows[-1][0]), ("exit", 111, 384))
        rows, outcome = L.route_model(0x0355)
        self.assertEqual((outcome, len(rows)), ("bailout", 86))
        rows, outcome = L.route_model(-944, left=True)
        self.assertEqual((outcome, len(rows)), ("exit", 128))

    def test_pair_model(self):
        pairs = [(1, 2), (3, 4), (5, 6), (42, 43)]
        self.assertEqual(L.pair_model(pairs, 0, 9), 1)
        self.assertEqual(L.pair_model(pairs, 0, 1), 2)
        self.assertEqual(L.pair_model(pairs, 39, 0), 42)
        self.assertEqual(L.pair_model(pairs, 39, 42), 43)

    def test_negative_control_wrong_decel_changes_outcome(self):
        # a route with the wrong first-half deceleration (11 instead of 10) would not reproduce the observed 183-update completion at $0356
        base = L.route_model(0x0356)
        self.assertEqual(base[1], "exit")
        self.assertEqual(len(base[0]), 183)


@unittest.skipIf(find_rom() is None, "ROM not supplied (set SONIC_CHAOS_ROM)")
class Regeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = L.R.load(find_rom())
        cls.cached = json.loads(CACHE.read_text(encoding="utf-8"))

    def test_static_section_regenerates_exactly(self):
        fresh = L.build(self.rom, static_only=True)
        self.assertEqual(json.loads(L.dumps(fresh))["static"], self.cached["static"])

    def test_natural_seed_13_replays_from_the_real_start(self):
        pairs = [tuple(p) for p in L.pair_table(self.rom)["pairs"]] + [(1, 2), (3, 4), (5, 6)] * 27
        sc, _ = L.natural_replay(self.rom, 13, 1700, pairs)
        got = json.loads(json.dumps(L.V.clean(sc)))
        want = [x for x in self.cached["emulated"]["natural"] if x["name"] == "natural_seed_13"][0]
        self.assertEqual(got, want)

    def test_spin_dash_roll_scenario_replays(self):
        from sms_frame_harness import BTN_RIGHT, BTN_DOWN, BTN_1
        pairs = [tuple(p) for p in L.pair_table(self.rom)["pairs"]] + [(1, 2), (3, 4), (5, 6)] * 27

        def spin(f):
            if f < 30:
                return 0
            if f < 34:
                return BTN_DOWN
            if f < 58:
                return BTN_DOWN | (BTN_1 if (f - 34) % 4 == 0 else 0)
            return BTN_RIGHT
        sc, _ = L.scenario(self.rom, "spin_dash_roll_through_both_loops", "x", lambda: L.boot_thz1_patched(self.rom, (2250, 430)), spin, 300, pairs)
        want = [x for x in self.cached["emulated"]["controlled"] if x["name"] == "spin_dash_roll_through_both_loops"][0]
        self.assertEqual(json.loads(json.dumps(L.V.clean(sc["traversals"]))), want["traversals"])

    def test_negative_control_no_loop_without_the_gate(self):
        from sms_frame_harness import BTN_LEFT
        # walking left from the loop floor never reaches the right gate: no loop state at all
        s = L.boot_thz1_patched(self.rom, (2300, 430))
        tr = L.LoopTracer(s)
        L.run_pad(s, tr, lambda f: BTN_LEFT, 120)
        self.assertEqual([t for t in tr.ticks if t["state"] in L.LOOP_STATES], [])

    def test_speed_injection_threshold(self):
        pairs = [tuple(p) for p in L.pair_table(self.rom)["pairs"]] + [(1, 2), (3, 4), (5, 6)] * 27
        inj = L.injected_speed_runs(self.rom, pairs, speeds=(0x0355, 0x0356))
        self.assertEqual(json.loads(json.dumps(inj)), {k: v for k, v in self.cached["emulated"]["route_speed_injection"].items() if k in ("0x0355", "0x0356")})


if __name__ == "__main__":
    unittest.main()

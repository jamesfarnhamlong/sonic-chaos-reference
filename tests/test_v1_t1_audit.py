"""V1/T1 audit: ROM-free consistency tests of the committed JSON (the tool itself needs the ROM: tools/v1_t1_trace.py --check)."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import v1_t1_register as R  # noqa: E402

V1 = json.loads((ROOT / "data/v1/twist-audit.json").read_text())
T1 = json.loads((ROOT / "data/t1/transition-audit.json").read_text())


class TwistContract(unittest.TestCase):
    def test_oracle_formula(self):
        self.assertEqual([R.frame_at(n) for n in range(0, 16)], [0x25] * 3 + [0x26] * 3 + [0x27] * 3 + [0x28] * 3 + [0x29] * 3 + [0x25])

    def test_static_script_matches_contract(self):
        recs = V1["static"]["script"]["records"]
        self.assertEqual([(r["duration"], r["frame"]) for r in recs], [(3, hex(f).replace("0x", "0x").upper().replace("0X", "0x")) for f in R.FRAMES])
        self.assertEqual(V1["static"]["script"]["cycle_updates"], 15)

    def test_strip_code_never_writes_frame_or_facing(self):
        w = V1["static"]["direct_writers_in_twist_code"]
        self.assertEqual((w["IX+6_frame_writes"], w["IX+4_flag_writes"]), (0, 0))

    def test_every_emulated_traversal_follows_the_oracle(self):
        sc = V1["emulated_scenarios"]
        self.assertGreaterEqual(len(sc), 10)
        for name, s in sc.items():
            self.assertTrue(s["entered"], name)
            self.assertTrue(s["frame_rule_holds_every_update"], name)
            first = [int(x, 16) for x in s["frame_sequence_first_17"]]
            self.assertEqual(first, [R.frame_at(n) for n in range(len(first))], name)

    def test_facing_is_inherited_not_derived(self):
        sc = V1["emulated_scenarios"]
        self.assertEqual(sc["THZ1_left_run_facing_left"]["facing_bit4_values_inside"], [16])
        self.assertEqual(sc["THZ1_left_run_facing_flag_clear"]["facing_bit4_values_inside"], [0])
        self.assertEqual(sc["MGHZ2_right_run"]["facing_bit4_values_inside"], [0])
        self.assertLess(sc["MGHZ2_right_run"]["vx_range"][0], 0)       # vx negative inside the chute while facing stays clear

    def test_variants_and_entry_rules(self):
        sc = V1["emulated_scenarios"]
        self.assertEqual(sc["THZ1_right_run"]["variants_seen"], [0])
        self.assertEqual(sc["THZ1_left_run_facing_left"]["variants_seen"], [1])
        self.assertEqual(sc["MGHZ2_right_run"]["variants_seen"], [2])
        self.assertEqual(sc["MGHZ2_right_slow_0x0200"]["entry"]["magnitude"], 160)   # 0x0500 << 5 >> 8

    def test_census(self):
        c = V1["static"]["census"]
        self.assertEqual(sorted(c), ["mghz2", "thz1", "thz2", "thz3"])
        self.assertEqual([c[k]["cells"] for k in ("thz1", "thz2", "thz3", "mghz2")], [22, 66, 22, 28])
        p = V1["static"]["block_priority"]
        self.assertEqual(sum(b["priority_cells_of_16"] for b in p["thz1"]["blocks_with_priority"].values()), 192)
        self.assertEqual(sum(b["priority_cells_of_16"] for b in p["mghz2"]["blocks_with_priority"].values()), 75)
        self.assertTrue(V1["static"]["thz_priority_sets_identical_across_acts"])

    def test_level_art_is_static(self):
        a = V1["level_art_animation_probe"]
        self.assertEqual(a["THZ1"]["bg_tiles_changed_during_strip"], [])
        self.assertEqual(a["MGHZ2"]["bg_tiles_changed_during_strip"], [])
        self.assertEqual(a["MGHZ_ambient_cycle"]["changed_colour_indices"], [4, 11])


class Transitions(unittest.TestCase):
    def test_all_twelve_acts_share_the_clear_timeline(self):
        g = T1["goal"]["ordinary_act_clear"]
        self.assertEqual(len(g), 12)
        for k, v in g.items():
            self.assertEqual(v["state20_update_after_contact"], 280, k)
            self.assertIn(v["flag_update_after_contact"], (308, 309), k)
            self.assertEqual(v["camera_settled_vs_sign"], [-129, -153], k)
            self.assertEqual(v["flag_player_minus_camera"], 289, k)
            self.assertEqual(v["unexpected_pool_types"] and [t for t in v["unexpected_pool_types"] if t not in ("0x2F", "0x0D", "0x10", "0x30")], [], k)

    def test_fade_chain(self):
        for k, v in T1["post_flag_transition"].items():
            cram = [e for e in v["events"] if e[0] == "cram"]
            self.assertIn(1008, [e[2] for e in cram], k)           # white
            self.assertEqual(cram[-1][2], 0, k)                    # black before the next level
            self.assertTrue(any(e[0] == "r1" and e[2] == 162 for e in v["events"]), k)

    def test_boss_release_is_rate_limited_in_the_rom(self):
        for z in ("THZ", "SEZ", "MGHZ"):
            m = T1["boss"][z]["milestones"]
            self.assertLessEqual(m["release_max_camera_step"], 7, z)
        self.assertEqual(T1["boss"]["THZ"]["milestones"]["pan_end_camera"], [1679, 78])

    def test_sparkle_trail(self):
        s = T1["defeat_sparkle_trail"]
        self.assertEqual(s["spawn_interval_updates"], [8])
        self.assertEqual(s["world_displacement_during_life"], [[0, 0]])
        self.assertEqual(s["spawn_offset_from_player_anchor_first_6"], [[0, -12], [0, -8]] * 3)

    def test_register(self):
        rows = R.reg_rows()
        ids = [r["id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(json.loads((ROOT / "data/t1/discrepancy-register.json").read_text())["rows"], json.loads(json.dumps(rows)))


if __name__ == "__main__":
    unittest.main()

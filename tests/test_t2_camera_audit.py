"""T2 camera-ownership audit: ROM-free checks of the committed traces, contracts and register.

    python -m unittest tests.test_t2_camera_audit

The traces themselves are regenerated with `python tools/t2_camera_audit.py ROM --check` (needs the ROM, about 2 minutes) and
`node tools/t2_poc_model.js --check` (needs the accepted POC checkout, read only). These tests assert the facts the report relies on, and the
`TargetContract` class states what a corrected POC must satisfy (it reads the same JSON shape a POC model run produces).
"""
import json
import unittest
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "data" / "t2"
ZONES = ["THZ", "GPZ", "SEZ", "MGHZ", "AQZ", "EEZ"]


def load(n):
    return json.loads((D / n).read_text())


class TestStatic(unittest.TestCase):
    def setUp(self):
        self.s = load("owner-map.json")

    def test_player_clamp_constants(self):
        c = self.s["player_clamp"]
        self.assertEqual((c["state_gate_below"], c["left_edge"], c["right_edge"]), (0x29, 0x10, 0xF7))

    def test_shared_boss_helpers_call_the_camera_vectors(self):
        rows = self.s["rows"]
        calls = {(r["bank"], r["cpu"], r["target"]) for r in rows if r["op"] in ("call", "jp")}
        for k in (("0x1E", "0x8199", "raise_left_limit_to_camera"), ("0x1E", "0x9799", "lower_right_limit_to_camera"), ("0x1E", "0x97FD", "pan_on"),
                  ("0x1E", "0x81D3", "pan_off_enable"), ("0x1E", "0x81F4", "pan_off_enable"), ("0x0C", "0xA8C4", "raise_left_limit_to_camera"),
                  ("0x0C", "0x83CB", "freeze_camera"), ("0x0C", "0xAA43", "pan_on")):
            self.assertIn(k, calls, k)

    def test_no_object_other_than_goal_sign_and_bosses_raises_the_left_limit(self):
        raisers = {(r["bank"], r["cpu"]) for r in self.s["rows"] if r.get("target") == "raise_left_limit_to_camera"}
        self.assertEqual(raisers, {("0x0C", "0xA8C4"), ("0x1E", "0x8199")})

    def test_boss_tables(self):
        t = self.s["boss_tables"]
        trig = {r["zone_or_encounter"]: (r["dx"], r["dy"]) for r in t["trigger_table_97A1"]["rows"]}
        pan = {r["zone_or_encounter"]: (r["dx"], r["dy"]) for r in t["pan_table_9808"]["rows"]}
        self.assertEqual(trig["THZ"], (160, 256))
        self.assertEqual(trig["AQZ"], (96, 304))
        self.assertEqual(pan["THZ"], (-256, -160))
        self.assertEqual([pan[k][0] for k in ("THZ", "GPZ", "SEZ", "MGHZ", "AQZ", "EEZ first ($5E)")], [-256, -192, -224, -208, -128, -128])
        # boss anchors reproduce the documented pan targets: SEZ3 (3200,622)->(2976,462)? the row offsets are applied to the RUNTIME anchor (see doc)
        self.assertEqual(pan["MGHZ"][1], -32)


class TestClamp(unittest.TestCase):
    def test_bare_lock_still_clamps(self):
        c = load("clamp-scope.json")["cases"]["THZ3"]
        self.assertEqual(c["camera_x_after"], [c["synthetic_lock_camera_x"]])
        self.assertTrue(13 <= min(c["player_screen_x_min"].values()) <= 16)
        self.assertTrue(247 <= max(c["player_screen_x_max"].values()) <= 249)


class TestBossArrival(unittest.TestCase):
    def setUp(self):
        self.z = load("boss-arrival.json")["zones"]

    def test_six_zones(self):
        self.assertEqual(list(self.z), ZONES)

    def test_created_off_screen_right_with_sonic_near_the_lead(self):
        for k, v in self.z.items():
            c = v["created"]
            self.assertTrue(330 <= c["boss_screen_x"] <= 345, k)
            self.assertTrue(100 <= c["player_screen_x"] <= 130, k)

    def test_player_never_beyond_the_rom_clamp(self):
        for k, v in self.z.items():
            self.assertLessEqual(v["max_player_screen_x_any_update"], 249, k)

    def test_boss_first_on_screen_to_the_right_of_sonic_except_sez3_relocation(self):
        for k, v in self.z.items():
            f = v["first_anchor_on_screen"]
            self.assertIsNotNone(f, k)
            if k == "SEZ":
                self.assertFalse(f["boss_right_of_player"])
                self.assertEqual((f["boss_world_x"], f["boss_screen_x"]), (3136, 209))
            else:
                self.assertTrue(f["boss_right_of_player"], k)
                self.assertTrue(254 <= f["boss_screen_x"] <= 255, k)

    def test_lock_and_pan(self):
        z = self.z
        self.assertEqual(z["GPZ"]["right_limit_first_changed"]["limit_right"], 1664)
        self.assertGreater(z["GPZ"]["right_limit_first_changed"]["ahead_of_camera_by"], 200)       # world-fixed lock at creation
        for k in ("THZ", "SEZ", "MGHZ", "AQZ", "EEZ"):
            self.assertEqual(z[k]["right_limit_first_changed"]["ahead_of_camera_by"], -4, k)         # right limit at the camera at the trigger
        self.assertEqual(z["THZ"]["pan"]["end_camera"], [1679, 78])
        self.assertEqual(z["SEZ"]["pan"]["end_camera"], [2975, 462])
        self.assertEqual(z["AQZ"]["pan"]["end_camera"], [1727, 78])
        self.assertEqual(z["EEZ"]["pan"]["end_camera"][0], 1951)
        for k, v in z.items():
            if "pan" in v:
                self.assertLessEqual(v["pan"]["max_camera_step"], 2, k)

    def test_camera_steps_bounded(self):
        for k, v in self.z.items():
            self.assertLessEqual(v["max_camera_step_x_any_update"], 8, k)


class TestSignWait(unittest.TestCase):
    def test_all_acts(self):
        z = load("sign-wait.json")["zones"]
        self.assertEqual(sorted(z), ["GPZ2", "MGHZ2", "SEZ2", "THZ1"])
        for k, v in z.items():
            self.assertFalse(v["sign_contacted_during_trace"], k)
            self.assertTrue(268 <= v["left_limit_first_tracks_camera"]["sign_minus_camera"] <= 287, k)     # awake window: screen X < 288
            self.assertTrue(13 <= v["player_screen_x_min_while_walking_back"] <= 16, k)                     # the ROM keeps Sonic on screen
            self.assertEqual(v["camera_x_min_after_turn"], v["camera_x_at_turn"], k)                        # no back-scroll


class TestPocBaseline(unittest.TestCase):
    """What the accepted POC C1-I computes in the node VM. These document the defect; a corrected POC makes them FAIL, which is intended."""

    def setUp(self):
        self.m = load("poc-model.json")

    def test_thz3_unclamped_between_creation_and_pan(self):
        for r in self.m["thz3"]:
            self.assertGreater(r["updates_player_beyond_view_right"], 0, r["view_width"])
            self.assertGreater(r["player_screen_x_max_after_lock"], r["view_width"], r["view_width"])
            self.assertEqual(r["first_update_player_right_of_boss_spawn_x"], 123)

    def test_sign_wait_unclamped_before_contact(self):
        for r in self.m["sign_wait"]:
            self.assertFalse(r["contact_during_trace"])
            self.assertGreater(r["updates_with_player_left_of_view"], 100, r["view_width"])
            self.assertLess(r["player_screen_x_min_walking_back"], 0)


class TargetContract(unittest.TestCase):
    """Acceptance predicate for a corrected POC (run against a model JSON of the same shape)."""

    @staticmethod
    def satisfied(model):
        ok = all(r["updates_player_beyond_view_right"] == 0 and r["player_screen_x_max_after_lock"] <= r["view_width"] - 9 for r in model["thz3"])
        ok = ok and all(r["updates_with_player_left_of_clamp16"] <= 2 and r["player_screen_x_min_walking_back"] >= 14 for r in model["sign_wait"])
        return ok

    def test_baseline_fails_target_by_design(self):
        self.assertFalse(self.satisfied(load("poc-model.json")))

    def test_synthetic_corrected_model_passes(self):
        m = {"thz3": [{"view_width": 256, "updates_player_beyond_view_right": 0, "player_screen_x_max_after_lock": 247}],
             "sign_wait": [{"updates_with_player_left_of_clamp16": 0, "player_screen_x_min_walking_back": 16}]}
        self.assertTrue(self.satisfied(m))


class TestRegister(unittest.TestCase):
    def test_register_is_classified_and_unique(self):
        r = load("discrepancy-register.json")
        ids = [x["id"] for x in r["rows"]]
        self.assertEqual(len(ids), len(set(ids)))
        for x in r["rows"]:
            self.assertIn(x["classification"], r["classes"], x["id"])
        self.assertTrue({"T2-01", "T2-02", "T2-03", "T2-04"} <= set(ids))

    def test_matrix_covers_six_zones(self):
        m = load("boss-camera-matrix.json")["zones"]
        self.assertEqual(list(m), ["THZ3", "GPZ3", "SEZ3", "MGHZ3", "AQZ3", "EEZ3"])
        for k, v in m.items():
            for f in ("trigger", "lock", "pan_target", "release", "player_boundary"):
                self.assertTrue(v[f], (k, f))

    def test_contracts_have_one_player_bounds_rule(self):
        c = load("ownership-contracts.json")
        self.assertEqual(c["player_bounds"]["id"], "O-P1")
        self.assertEqual(len(c["owners"]), 9)


if __name__ == "__main__":
    unittest.main()

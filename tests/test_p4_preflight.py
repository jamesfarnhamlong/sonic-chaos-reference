"""P4 preflight: ROM-free checks of the final V1/T1 re-baseline, the numeric contract and the S0 findings.

    python -m unittest tests.test_p4_preflight

Regenerate: see tools/p4_rebaseline.py, tools/p4_proposal_model.js, tools/s0_start_fall.js, tools/p4_s0.py. The historical T3 data (data/t3, C1-I) is not touched.
"""
import json
import unittest
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "data" / "p4"
S = json.loads((D / "baseline-summary.json").read_text())["zones"]
C = json.loads((D / "p4-contract.json").read_text())["packages"]
ZONES = ["THZ3", "GPZ3", "SEZ3", "MGHZ3", "AQZ3", "EEZ3"]
WIDTHS = ["w256", "w348", "w400"]


def r(z, k, w, sc="hold"):
    return S[z][f"{k}_{w}_{sc}"]


class TestRebaseline(unittest.TestCase):
    def test_thz3_was_corrected_by_v1t1(self):
        for w in WIDTHS:
            self.assertEqual(r("THZ3", "v1t1", w)["player"]["updates_beyond_right_clamp_plus_4"], 0, w)
            self.assertGreater(r("THZ3", "c1i", w)["player"]["updates_beyond_right_clamp_plus_4"], 40, w)
            step = r("THZ3", "v1t1", w)["camera"]["creation_update_step"]
            self.assertTrue(0 < step[0] <= 7 and step[1] == 0, (w, step))
            self.assertEqual(r("THZ3", "v1t1", w)["camera"]["x_retreat"]["pixels"], 0)
            self.assertEqual(r("THZ3", "v1t1", w)["pan_end"]["camera"], [1679, 78])

    def test_other_five_zones_are_unchanged_by_v1t1(self):
        for z in ("GPZ3", "SEZ3", "MGHZ3", "AQZ3", "EEZ3"):
            for w in WIDTHS:
                for sc in ("hold", "stop"):
                    a, b = r(z, "c1i", w, sc), r(z, "v1t1", w, sc)
                    for key in ("created", "pan_start", "pan_end", "first_visible", "fight_activation", "camera", "player", "right_limit"):
                        self.assertEqual(a[key], b[key], (z, w, sc, key))

    def test_persisting_problems_numbers(self):
        self.assertEqual([r("GPZ3", "v1t1", w)["camera"]["x_retreat"]["pixels"] for w in WIDTHS], [12, 92, 144])
        self.assertEqual([r("AQZ3", "v1t1", w)["camera"]["x_retreat"]["pixels"] for w in WIDTHS], [166, 76, 22])
        self.assertFalse(any(r("AQZ3", "v1t1", w)["right_limit"]["lowered_before_pan"] for w in WIDTHS))
        self.assertEqual([r("GPZ3", "v1t1", w)["camera"]["creation_update_step"] for w in WIDTHS], [[-12, -11], [-4, -4], [-4, -4]])
        self.assertEqual(r("SEZ3", "v1t1", "w256")["camera"]["creation_update_step"], [-12, -16])
        self.assertEqual(r("AQZ3", "v1t1", "w256")["camera"]["creation_update_step"], [-12, -19])
        self.assertEqual(r("MGHZ3", "v1t1", "w256", "stop")["camera"]["creation_update_step"], [0, -7])
        self.assertEqual([r("MGHZ3", "v1t1", w, "stop")["camera"]["y_total_up"] for w in WIDTHS], [29, 32, 51])
        self.assertEqual([r("EEZ3", "v1t1", w)["camera"]["pan_max_abs_step"][1] for w in WIDTHS], [49, 25, 25])

    def test_eez3_snap_is_reachable_from_any_standing_trigger(self):
        """Corroboration: camera Y before the pan is Sonic-y minus the follow lead, the new bottom limit is boss-y - 160 = 334."""
        for w in WIDTHS:
            e = r("EEZ3", "v1t1", w, "stop")
            self.assertGreater(e["created"]["camera_previous"][1], 333 - 1 + 7, w)        # camera Y before the pan is already below the bottom limit


class TestContract(unittest.TestCase):
    def test_model_meets_the_contract(self):
        for z, pk in (("GPZ3", "T3-C"), ("SEZ3", "T3-E"), ("MGHZ3", "T3-E")):
            for k, v in C[pk]["zones"][z].items():
                self.assertEqual(v["after_model"]["x_retreat"], 0, (z, k))
        for k, v in C["T3-A"]["zones"]["AQZ3"].items():
            self.assertEqual(v["after_model"]["x_retreat"], 0, k)
        for z, zr in C["T3-A"]["zones"].items():
            for k, v in zr.items():
                step = v["after_model"]["creation_step"]
                self.assertTrue(0 <= step[0] <= 7 and abs(step[1]) <= 7, (z, k, step))
                self.assertEqual(v["after_model"]["sonic_beyond_clamp_plus_4"], 0, (z, k))

    def test_gpz3_final_camera_formula(self):
        for w, width in (("w256", 256), ("w348", 348), ("w400", 400)):
            after = C["T3-C"]["zones"]["GPZ3"][f"{w}_hold"]["after_model"]
            self.assertEqual(after["pan_end_camera"][0], 1663 if width == 256 else 1664 - (width - 256) - 1)

    def test_aqz3_lock(self):
        for k, v in C["T3-B"]["zones"]["AQZ3"].items():
            self.assertFalse(v["before_v1t1"]["right_limit_lowered_before_pan"], k)
            self.assertTrue(v["after_model"]["right_limit_lowered_before_pan"], k)

    def test_eez3_pan(self):
        for k, v in C["T3-D"]["zones"]["EEZ3"].items():
            self.assertLessEqual(v["after_model"]["pan_max_step"][1], 1, k)
            self.assertEqual(v["after_model"]["pan_end_camera"], [1951, 334], k)

    def test_mghz3_standing_vertical_after(self):
        for w in WIDTHS:
            self.assertEqual(C["T3-A"]["zones"]["MGHZ3"][f"{w}_stop"]["after_model"]["y_up_down"], [11, 0], w)

    def test_pan_ends_unchanged_by_the_model(self):
        for pk, zr in C.items():
            for z, cfgs in zr["zones"].items():
                for k, v in cfgs.items():
                    a, b = v["before_v1t1"]["pan_end_camera"], v["after_model"]["pan_end_camera"]
                    if z == "EEZ3":
                        self.assertEqual(a[0], b[0], (z, k))                      # Y 333 -> 334 is the point of T3-D
                    elif z == "AQZ3":
                        self.assertLessEqual(abs(a[0] - b[0]), 1, (z, k))          # settles at 1727 or 1728
                        self.assertEqual(a[1], b[1], (z, k))
                    else:
                        self.assertEqual(a, b, (z, k))


class TestS0(unittest.TestCase):
    def setUp(self):
        self.f = json.loads((D / "s0-source-findings.json").read_text())

    def test_poc_start_fall_matches_the_rom_drop(self):
        fall = self.f["poc_start_fall"]
        self.assertEqual((fall["GPZ1"]["drop_px"], fall["GPZ1"]["y_at_landing"]), (14, 398))     # ROM 384 -> 398 (T2 zone-start.json)
        self.assertEqual((fall["MGHZ1"]["drop_px"], fall["MGHZ1"]["y_at_landing"]), (14, 206))    # ROM 192 -> 206
        self.assertEqual(fall["THZ1"]["drop_px"], 0)
        self.assertEqual(fall["GPZ1"]["first_floor_contact_update"], 12)

    def test_anchor_table(self):
        self.assertEqual(len(self.f["anchors"]), 14)
        files = {a["file"] for a in self.f["anchors"]}
        for need in ("scripts/SCR_chaos_results/SCR_chaos_results.gml", "objects/OBJ_chaos_zone/Create_0.gml", "scripts/SCR_chaos_debug_select/SCR_chaos_debug_select.gml"):
            self.assertIn(need, files)

    def test_routes(self):
        self.assertEqual(set(self.f["routes"]), {"zone_title", "death_respawn", "level_select", "data_select_start"})


if __name__ == "__main__":
    unittest.main()

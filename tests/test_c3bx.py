"""C3-BX: numeric acceptance tests on the committed series (ROM-free, POC-free). They pin the findings and the acceptance contract of the candidates."""
import json, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
X = json.loads((ROOT / "data/c3bx/exit-matrix.json").read_text())
E = json.loads((ROOT / "data/c3bx/entrance-matrix.json").read_text())


class TestExitBaseline(unittest.TestCase):
    def test_rom_aqz3_follows_to_world_edge(self):
        r = X["rom"]["AQZ3"]
        self.assertEqual((r["cam0"], r["cam_final"], r["cam_max"]), (1727, 2303, 2304))
        self.assertEqual((r["first_move"], r["clear"], r["px_clear"]), (36, 180, 2595))
        self.assertEqual(r["steady_scr"], 118)

    def test_p4_aqz3_wide_camera_never_moves(self):
        for w, short in (("w348", 485), ("w400", 433)):
            r = X["poc_p4"]["AQZ3"][w]
            self.assertEqual((r["cam_final"], r["first_move"], r["freeze_flag"], r["short"]), (1727, None, 0, short))
            self.assertLess(r["px_clear"], 2200)          # the run ends ~480 px short of the ROM's 2595

    def test_p4_aqz3_256_follows(self):
        r = X["poc_p4"]["AQZ3"]["w256"]
        self.assertLessEqual(r["short"], 4)
        self.assertEqual(r["px_clear"], 2592)

    def test_early_freeze_in_other_zones(self):
        self.assertEqual(X["poc_p4"]["SEZ3"]["w348"]["short"], 402)
        self.assertEqual(X["poc_p4"]["MGHZ3"]["w348"]["short"], 172)
        self.assertLessEqual(X["poc_p4"]["THZ3"]["w348"]["short"], 6)
        self.assertEqual(X["poc_p4"]["GPZ3"]["w348"]["short"], 0)

    def test_state20_startup_lag_is_shared(self):
        for z in ("THZ3", "SEZ3", "AQZ3"):
            self.assertEqual(X["poc_p4"][z]["w256"]["clear"] - X["rom"][z]["clear"], 7 if z != "AQZ3" else 7)


class TestCandidateContract(unittest.TestCase):
    def test_a1_a2_world_identical_at_all_widths(self):
        for z in ("THZ3", "SEZ3", "MGHZ3", "AQZ3"):
            ref = X["candidate_A1_A2"][z]["w256"]
            for w in ("w348", "w400"):
                r = X["candidate_A1_A2"][z][w]
                self.assertLessEqual(r["short"], 6, (z, w))
                self.assertEqual(r["back_scroll"], 0, (z, w))
                self.assertLessEqual(abs(r["px_clear"] - ref["px_clear"]), 4, (z, w))

    def test_aqz3_exit_acceptance(self):
        for w in ("w348", "w400"):
            r = X["candidate_A1_A2"]["AQZ3"][w]
            self.assertLessEqual(r["first_move"], 66)
            self.assertEqual(r["clear"], X["candidate_A1_A2"]["AQZ3"]["w256"]["clear"])
            self.assertTrue(2590 <= r["px_clear"] <= 2596)
            self.assertTrue(150 <= r["steady_scr"] <= 190)      # follow lead, not the screen edge

    def test_a1_alone_is_not_enough_at_348(self):
        self.assertEqual(X["candidate_A1"]["AQZ3"]["w348"]["short"], 22)
        self.assertGreater(X["candidate_A1"]["AQZ3"]["w348"]["steady_scr"], 200)


class TestNoRegressionAt256(unittest.TestCase):
    def test_candidates_leave_256_unchanged(self):
        for z in ("THZ3", "GPZ3", "SEZ3", "MGHZ3", "AQZ3"):
            self.assertEqual(X["candidate_A1_A2"][z]["w256"], X["poc_p4"][z]["w256"], z)


class TestEntrance(unittest.TestCase):
    def test_thz3_baseline_pop_in(self):
        for w, anchor in (("w348", 314), ("w400", 340)):
            fv = E["zones"]["THZ3"]["p4_" + w + "_stop"]["first_visible"]
            self.assertEqual((fv["columns"], fv["anchor_screen"][0]), (40, anchor))
        self.assertEqual(E["zones"]["THZ3"]["rom_w256_stop"]["first_visible"]["columns"], 5)

    def test_thz3_b1(self):
        t = E["thz3_walk_on"]
        for w in ("w256", "w348", "w400"):
            b = t["B1_" + w]
            self.assertEqual(b["fight"]["boss_x"], 1902)                  # world fight position is the ROM's at every width
            self.assertEqual(b["walk_px"], 34)
            self.assertLessEqual(b["summary"]["first_visible"]["columns"], 8)
            self.assertEqual(b["summary"]["x_retreat"], 0)
        self.assertEqual(t["p4_w400"]["fight"]["boss_x"], 1896)           # P4: the stop depends on where the pan is when the gate fires
        self.assertEqual(t["B1_w348"]["fight"]["camera_x"], 1587)
        self.assertEqual(t["B1_w256"]["fight"], t["p4_w256"]["fight"])

    def test_other_zones_entrance_unchanged(self):
        for z in ("GPZ3", "SEZ3", "MGHZ3", "AQZ3", "EEZ3"):
            for k, v in E["zones"][z].items():
                self.assertEqual(v["x_retreat"], 0, (z, k))


class TestPatches(unittest.TestCase):
    def test_patch_table_wellformed(self):
        out = subprocess.run(["node", "-e", "const P=require('./tools/c3bx_candidates.js').PATCHES;console.log(JSON.stringify(Object.fromEntries(Object.entries(P).map(([k,v])=>[k,v.length]))))"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(json.loads(out.stdout), {"B1": 3, "A1": 2, "A2": 5})


if __name__ == "__main__":
    unittest.main()

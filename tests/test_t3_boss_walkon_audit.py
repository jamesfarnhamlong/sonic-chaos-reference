"""T3 boss walk-on and widescreen framing audit: ROM-free checks of the committed series, summary and registers.

    python -m unittest tests.test_t3_boss_walkon_audit

The series are regenerated with `python tools/t3_boss_walkon_audit.py ROM --check rom` (needs the ROM, about 1 minute) and
`POC=<checkout> node tools/t3_poc_boss_run.js --check` (needs the accepted POC checkout, read only); the summary and registers are regenerated
ROM-free with `--check summary` and `python tools/t3_register.py --check`. These tests assert the facts the report relies on, and
`TargetContract` states what a corrected POC must satisfy (it reads the same summary shape a POC re-run produces).
"""
import json
import unittest
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "data" / "t3"
ZONES = ["THZ3", "GPZ3", "SEZ3", "MGHZ3", "AQZ3", "EEZ3"]


def load(n):
    return json.loads((D / n).read_text())


SUM = load("boss-walkon-summary.json")["zones"]


def S(z, k):
    return SUM[z][k]


class TargetContract:
    """What a corrected POC must satisfy at the boss arrival, for one summary entry (zone, config). The ROM satisfies it by construction."""

    @staticmethod
    def violations(s, width, standing=False):
        """standing = the 'stop' scenario (Sonic waits at the trigger): the camera Y must then stay within the ordinary follow zone (+-16) until the pan."""
        v = []
        if standing and s["created"]["camera_previous"] and s["pan_start"]:
            if abs(s["pan_start"]["camera"][1] - s["created"]["camera_previous"][1]) > 16:
                v.append("camera Y leaves the ordinary follow zone (+-16) between creation and the pan")
        if s["camera"]["x_retreat"]["pixels"] > 0:
            v.append("camera X retreats between boss creation and the end of the pan")
        c = s["camera"]["creation_update_step"]
        if c is not None and (c[0] < 0 or abs(c[0]) > 7 or abs(c[1]) > 7):
            v.append("camera takeover step at creation (backward X or > 7 px)")
        if max(s["camera"]["pan_max_abs_step"]) > (2 if width == 256 else 4):
            v.append("pan step above the ROM rate (2 at 256, 4 at wide)")
        if s["player"]["updates_beyond_right_clamp_plus_4"] > 0:
            v.append("Sonic beyond EDGE(RIGHT,-9)+4")
        rl = s["right_limit"]
        if rl["at_creation"] in (0, None) or rl["first_lowered_update"] is None:
            pass
        return v


class TestSeries(unittest.TestCase):
    def test_files_and_row_counts(self):
        rom, poc = load("rom-series.json"), load("poc-series.json")
        for z in ZONES:
            for sc in ("hold", "stop"):
                self.assertEqual(len(rom["zones"][z][sc]["u"]), 450, (z, sc))
                for w in ("w256", "w348"):
                    self.assertEqual(len(poc["zones"][z][w][sc]["u"]), 450, (z, w, sc))
        self.assertEqual(poc["poc_checkout_head"], "69527335011bacf22ff16bd25d3a94874a1fa563")

    def test_frame_extents_byte_verified_numbers(self):
        ext = load("frame-extents.json")["types"]

        def f(t, n):
            return ext[t][n]
        self.assertEqual((f("0x50", 1)["min_x"], f("0x50", 1)["max_x_excl"], f("0x50", 1)["min_y"], f("0x50", 1)["max_y_excl"]), (-20, 20, -48, 0))
        self.assertEqual((f("0x51", 1)["min_x"], f("0x51", 1)["max_x_excl"]), (-12, 12))
        self.assertEqual((f("0x54", 1)["min_x"], f("0x54", 1)["max_x_excl"], f("0x54", 1)["min_y"]), (-20, 20, -80))
        self.assertEqual((f("0x56", 1)["min_x"], f("0x56", 1)["max_x_excl"]), (-16, 16))
        self.assertEqual(f("0x50", 0)["pieces"], 0)          # frame 0 is the shared empty record

    def test_summary_is_a_rebuild_of_the_series(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
        import t3_boss_walkon_audit as A
        rom, ext, poc = load("rom-series.json"), load("frame-extents.json"), load("poc-series.json")
        again = json.loads(json.dumps(A.build_summary(rom, ext, poc)))
        self.assertEqual(again, load("boss-walkon-summary.json"))


class TestRom(unittest.TestCase):
    def test_rom_camera_never_retreats_and_never_snaps_at_boss_creation(self):
        for z in ZONES:
            for sc in ("rom_hold", "rom_stop"):
                s = S(z, sc)
                self.assertEqual(s["camera"]["x_retreat"]["pixels"], 0, (z, sc))
                step = s["camera"]["creation_update_step"]
                if step is not None:                      # None: created inside the start-up transient
                    self.assertLessEqual(max(abs(v) for v in step), 7, (z, sc))
                    self.assertGreaterEqual(step[0], 0, (z, sc))

    def test_rom_satisfies_the_target_contract(self):
        for z in ZONES:
            for sc in ("rom_hold", "rom_stop"):
                self.assertEqual(TargetContract.violations(S(z, sc), 256), [], (z, sc))

    def test_rom_relocations(self):
        r = {z: S(z, "rom_hold")["relocations"] for z in ZONES}
        self.assertEqual(r["THZ3"], [])
        self.assertEqual(r["MGHZ3"], [])
        self.assertEqual([(x["from_"], x["to"]) for x in r["GPZ3"]], [([1728, 270], [1856, 270])])
        self.assertEqual([(x["from_"], x["to"]) for x in r["SEZ3"]], [([3200, 622], [3136, 430])])
        self.assertEqual([(x["from_"], x["to"]) for x in r["AQZ3"]], [([1856, 238], [1856, 14])])
        self.assertEqual([(x["from_"], x["to"]) for x in r["EEZ3"]], [([2080, 494], [2208, 494])])
        self.assertEqual(r["GPZ3"][0]["u"] - S("GPZ3", "rom_hold")["created"]["u"], 1)          # one update after creation

    def test_rom_gpz3_limit_is_world_fixed_and_270_px_ahead(self):
        rl = S("GPZ3", "rom_hold")["right_limit"]
        self.assertEqual((rl["first_lowered_value"], rl["at_creation"]), (1664, 2304))
        self.assertEqual(rl["first_lowered_update"] - S("GPZ3", "rom_hold")["created"]["u"], 1)

    def test_rom_lock_follows_the_trigger_in_five_zones(self):
        for z in ("THZ3", "SEZ3", "MGHZ3", "AQZ3", "EEZ3"):
            rl = S(z, "rom_hold")["right_limit"]
            self.assertTrue(rl["lowered_before_pan"], z)
            self.assertLess(rl["first_lowered_value"], rl["at_creation"], z)

    def test_rom_first_visible_entries(self):
        cols = {z: S(z, "rom_hold")["first_visible"]["visible_columns"] for z in ZONES}
        self.assertEqual((cols["THZ3"], cols["MGHZ3"], cols["AQZ3"], cols["EEZ3"]), (5, 4, 1, 15))      # slivers at the right edge
        self.assertEqual(S("SEZ3", "rom_hold")["first_visible"]["anchor_screen"][1], 1)                  # drops in from the top
        fv = S("GPZ3", "rom_hold")["first_visible"]
        self.assertEqual((fv["anchor_screen"], fv["visible_columns"]), ([193, 173], 24))                 # emerges in place

    def test_rom_mghz3_vertical_pan_is_tiny_when_sonic_stands(self):
        s = S("MGHZ3", "rom_stop")
        self.assertEqual(s["camera"]["y_total_up"] + s["camera"]["y_total_down"], 2)
        self.assertEqual(s["pan_end"]["camera"][1], 256)

    def test_rom_scene_in_a_348_window_shows_more_of_the_boss(self):
        self.assertEqual(S("THZ3", "rom_hold_same_camera_in_348")["first_visible"]["visible_columns"], 40)
        self.assertEqual(S("MGHZ3", "rom_hold_same_camera_in_348")["first_visible"]["visible_columns"], 32)
        self.assertEqual(S("EEZ3", "rom_hold_same_camera_in_348")["first_visible"]["visible_columns"], 32)
        a, b = S("AQZ3", "rom_hold")["first_visible"]["u"], S("AQZ3", "rom_hold_same_camera_in_348")["first_visible"]["u"]
        self.assertEqual(a - b, 90)
        for z in ("GPZ3", "SEZ3"):
            self.assertEqual(S(z, "rom_hold")["first_visible"]["visible_columns"], S(z, "rom_hold_same_camera_in_348")["first_visible"]["visible_columns"])


class TestPocC1I(unittest.TestCase):
    def test_gpz3_rollback_at_348(self):
        s, n = S("GPZ3", "poc_w348_hold"), S("GPZ3", "poc_w256_hold")
        self.assertEqual(s["camera"]["x_retreat"]["pixels"], 92)
        self.assertEqual(s["pan_end"]["camera"], [1571, 112])
        self.assertEqual(n["pan_end"]["camera"][0], 1663)
        self.assertEqual(n["camera"]["x_retreat"]["pixels"], 12)          # 256: only the takeover snap
        self.assertEqual((s["pan_start"]["player_world_x"], s["pan_end"]["player_world_x"]), (1976, 1911))    # the clamp carries Sonic back
        self.assertEqual(s["right_limit"]["at_creation"], 1664)         # the limit is never width-adjusted
        self.assertEqual(S("GPZ3", "poc_w348_stop")["camera"]["x_retreat"]["pixels"], 92)

    def test_gpz3_retreat_grows_with_how_far_sonic_ran(self):
        sweep = {r["stop_world_x"]: r["camera_x_retreat"] for r in load("poc-series.json")["gpz3_w348_stop_x_sweep"]}
        self.assertEqual([sweep[x] for x in (1550, 1650)], [8, 8])                    # the creation takeover only
        self.assertEqual([sweep[x] for x in (1700, 1740, 1760, 1800, 1850)], [31, 71, 91, 92, 92])

    def test_creation_takeover_steps_at_256(self):
        self.assertEqual(S("GPZ3", "poc_w256_hold")["camera"]["creation_update_step"], [-12, -11])
        self.assertEqual(S("SEZ3", "poc_w256_hold")["camera"]["creation_update_step"], [-12, -16])
        self.assertEqual(S("AQZ3", "poc_w256_hold")["camera"]["creation_update_step"], [-12, -19])
        self.assertEqual(S("MGHZ3", "poc_w256_hold")["camera"]["creation_update_step"], [0, -7])
        self.assertEqual(S("THZ3", "poc_w256_hold")["camera"]["creation_update_step"], [0, 0])
        self.assertEqual(S("EEZ3", "poc_w256_hold")["camera"]["creation_update_step"], [2, 0])         # no takeover step (ordinary 2 px follow)

    def test_mghz3_vertical_excursion(self):
        a, b = S("MGHZ3", "poc_w256_stop"), S("MGHZ3", "poc_w348_stop")
        self.assertEqual((a["camera"]["y_total_up"], a["camera"]["y_total_down"]), (29, 18))
        self.assertEqual((b["camera"]["y_total_up"], b["camera"]["y_total_down"]), (32, 21))
        self.assertEqual((a["pan_end"]["camera"], b["pan_end"]["camera"]), ([3060, 256], [2968, 256]))
        self.assertEqual((a["pan_end"]["u"] - a["pan_start"]["u"], b["pan_end"]["u"] - b["pan_start"]["u"]), (78, 8))

    def test_aqz3_never_locks_the_right_limit_before_the_pan(self):
        for k in ("poc_w256_hold", "poc_w348_hold", "poc_w256_stop", "poc_w348_stop"):
            rl = S("AQZ3", k)["right_limit"]
            self.assertEqual(rl["at_creation"], 2304, k)
            self.assertFalse(rl["lowered_before_pan"], k)
        self.assertEqual(S("AQZ3", "poc_w256_hold")["camera"]["x_retreat"]["pixels"], 166)
        self.assertEqual(S("AQZ3", "poc_w348_hold")["camera"]["x_retreat"]["pixels"], 76)

    def test_other_zones_lock_the_right_limit_at_the_trigger(self):
        for z in ("THZ3", "SEZ3", "MGHZ3"):
            for w in ("poc_w256_hold", "poc_w348_hold"):
                self.assertTrue(S(z, w)["right_limit"]["lowered_before_pan"], (z, w))

    def test_eez3_pan_start_snap(self):
        self.assertEqual(S("EEZ3", "poc_w256_hold")["camera"]["pan_max_abs_step"][1], 49)
        self.assertEqual(S("EEZ3", "poc_w348_hold")["camera"]["pan_max_abs_step"][1], 25)
        self.assertEqual(S("EEZ3", "rom_hold")["camera"]["pan_max_abs_step"][1], 1)

    def test_eez3_wide_relocation_keeps_the_rom_sliver(self):
        r = S("EEZ3", "poc_w348_hold")["relocations"][0]
        self.assertEqual((r["from_"], r["to"]), ([2080, 494], [2300, 494]))
        self.assertEqual(S("EEZ3", "poc_w348_hold")["first_visible"]["visible_columns"], S("EEZ3", "rom_hold")["first_visible"]["visible_columns"])

    def test_thz3_pops_in_wide_and_is_unclamped(self):
        self.assertEqual(S("THZ3", "poc_w348_hold")["first_visible"]["visible_columns"], 38)
        self.assertEqual(S("THZ3", "poc_w256_hold")["first_visible"]["visible_columns"], 1)
        self.assertGreater(S("THZ3", "poc_w256_hold")["player"]["screen_x_max"], 400)           # T2-01

    def test_known_contract_violations_of_c1i(self):
        """The documented baseline. When a corrected POC is re-run, the expected set shrinks; update EXPECTED with the register."""
        got = {}
        for z in ZONES:
            for w, width in (("poc_w256_hold", 256), ("poc_w348_hold", 348)):
                v = TargetContract.violations(S(z, w), width)
                if v:
                    got[(z, w)] = len(v)
        expected = {
            ("THZ3", "poc_w256_hold"): 1, ("THZ3", "poc_w348_hold"): 1,                                   # Sonic beyond the clamp (T2-01)
            ("GPZ3", "poc_w256_hold"): 2, ("GPZ3", "poc_w348_hold"): 2,                                   # retreat + takeover step
            ("SEZ3", "poc_w256_hold"): 2, ("SEZ3", "poc_w348_hold"): 2,
            ("MGHZ3", "poc_w256_hold"): 0, ("MGHZ3", "poc_w348_hold"): 0,
            ("AQZ3", "poc_w256_hold"): 3, ("AQZ3", "poc_w348_hold"): 2,
            ("EEZ3", "poc_w256_hold"): 1, ("EEZ3", "poc_w348_hold"): 1,                                   # pan step
        }
        expected = {k: v for k, v in expected.items() if v}
        self.assertEqual(got, expected)


class TestVerticalRule(unittest.TestCase):
    """Where Sonic is grounded at the trigger (THZ3, SEZ3, MGHZ3) the camera Y must stay inside the ordinary follow zone until the pan."""

    def test_rom_satisfies_it(self):
        for z in ("THZ3", "SEZ3", "MGHZ3"):
            self.assertEqual(TargetContract.violations(S(z, "rom_stop"), 256, standing=True), [], z)

    def test_c1i_violates_it_in_sez3_and_mghz3_at_both_widths(self):
        for z in ("SEZ3", "MGHZ3"):
            for k, w in (("poc_w256_stop", 256), ("poc_w348_stop", 348)):
                self.assertTrue(any("ordinary follow zone" in v for v in TargetContract.violations(S(z, k), w, standing=True)), (z, k))
        for z in ("THZ3",):
            for k, w in (("poc_w256_stop", 256), ("poc_w348_stop", 348)):
                self.assertEqual(TargetContract.violations(S(z, k), w, standing=True), [], (z, k))


class TestRegisters(unittest.TestCase):
    def test_register_vocabulary(self):
        reg = load("discrepancy-register.json")["rows"]
        self.assertEqual(len({r["id"] for r in reg}), len(reg))
        for r in reg:
            self.assertIn(r["status"], ("proven-match", "adapter-difference", "proven-gap", "not-audited", "unresolved"), r["id"])
            for k in ("scope", "finding", "rom_datum", "poc_code_path", "comparison_method", "gameplay_impact", "proposed_work_group", "acceptance_proof"):
                self.assertTrue(r[k] != "", (r["id"], k))

    def test_adapter_register_kinds_and_anchors_unique_per_file(self):
        rows = load("adapter-register.json")["rows"]
        kinds = {"ROM-recovered", "deliberate widescreen adapter", "legacy non-ROM rule", "omission of a ROM rule"}
        seen = set()
        for r in rows:
            self.assertIn(r["kind"], kinds, r["id"])
            key = (r["file"], r["anchor"], r["line_at_c1i"])
            self.assertNotIn(key, seen, r["id"])
            seen.add(key)

    def test_matrix_has_all_zones_and_configs(self):
        m = load("boss-framing-matrix.json")["zones"]
        self.assertEqual(list(m), ZONES)
        for z in ZONES:
            self.assertEqual(list(m[z]["configs"]), ["rom_hold", "poc_w256_hold", "poc_w348_hold"])
            self.assertIn("mode", m[z]["entry_mode"])


if __name__ == "__main__":
    unittest.main()

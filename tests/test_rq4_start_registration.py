#!/usr/bin/env python3
"""RQ4 tests: original campaign start-coordinate and camera registration.

Part 1 needs no ROM: the committed data/rq4/start-registration.json must be internally consistent, must agree with the G0-R start table, must keep the
headline facts and must reject corrupted copies (negative controls).  Part 2 needs the canonical ROM (SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms)
and the `z80` package: it recomputes the static table and replays THZ1 and THZ3 (fresh load, pit-death reload) against the committed file.
The full regeneration check is `python tools/rq4_start_registration.py ROM --check` (about 40 seconds).
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

import rq4_start_registration as R  # noqa: E402

DATA = json.loads((ROOT / "data" / "rq4" / "start-registration.json").read_text(encoding="utf-8"))
G0 = json.loads((ROOT / "data" / "g0" / "campaign-contract.json").read_text(encoding="utf-8"))
ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")))


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == 524288 and hashlib.sha256(data).hexdigest() == R.ROM_SHA256:
            return data
    return None


def by_name(name):
    return next(r for r in DATA["summary"] if r["name"] == name)


class CommittedData(unittest.TestCase):
    def test_validates(self):
        self.assertEqual(R.validate(DATA), [])

    def test_table_equals_g0(self):
        g0 = {(r["zone"], r["act"]): r for r in G0["start_positions"]}
        self.assertEqual(len(g0), 18)
        for t in DATA["static"]["table"]:
            r = g0[(t["zone"], t["act"])]
            self.assertEqual(t["camera"], [r["camera_x"], r["camera_y"]])
            self.assertEqual(t["player"], [r["player_x"], r["player_y"]])

    def test_loader_stores_record_unchanged_and_commits_camera(self):
        for r in DATA["summary"]:
            self.assertTrue(r["player_matches_record_at_entry"], r["name"])
            self.assertTrue(r["camera_committed_at_first_update_equals_record"], r["name"])
            self.assertEqual(r["terrain_shift_x"], 0, r["name"])

    def test_reload_equals_fresh(self):
        for r in DATA["summary"]:
            self.assertTrue(r["reload_equals_fresh"], r["name"])

    def test_thz_headlines(self):
        t1, t2, t3 = by_name("THZ1"), by_name("THZ2"), by_name("THZ3")
        self.assertEqual((t1["record_player"], t1["settled_player"], t1["terrain_shift_y"]), ([142, 654], [142, 654], 0))
        self.assertEqual((t2["record_player"], t2["settled_player"], t2["terrain_shift_y"]), ([110, 398], [110, 398], 0))
        self.assertEqual((t3["record_player"], t3["settled_player"], t3["terrain_shift_y"]), ([110, 224], [110, 238], 14))
        self.assertEqual(t1["record_camera"], [38, 530])
        self.assertEqual(t1["settled_camera"], [38, 542])
        self.assertEqual(t1["entry_screen_anchor"], [104, 124])
        self.assertEqual(t1["settled_screen_anchor"], [104, 112])

    def test_sprite_registration_is_one_shape(self):
        for r in DATA["summary"]:
            self.assertEqual(r["sprite_opaque_rect_rel_anchor"], dict(left=-9, right=9, top=-30, bottom=0), r["name"])
            self.assertEqual(r["foot_world_row"], r["settled_player"][1] + 17)

    def test_start_is_not_always_rest(self):
        shifted = {r["name"]: r["terrain_shift_y"] for r in DATA["summary"] if r["terrain_shift_y"]}
        self.assertEqual(shifted, {"THZ3": 14, "GPZ1": 14, "GPZ2": 14, "GPZ3": 14, "SEZ3": -7, "MGHZ1": 14, "MGHZ3": 14, "EEZ1": 14, "EEZ3": 14})

    def test_fixture_sweep_depenetration(self):
        rows = {(r["zone"], r["act"], r["start_dy"]): r for r in DATA["fixture_sweeps"]["rows"]}
        for dy in (-8, -5, -4, -1, 0, 1, 4, 5, 8):
            self.assertEqual(rows[(0, 0, dy)]["settled"], [142, 654], dy)
        self.assertEqual(rows[(0, 0, 4)]["after_passes"]["1"][:2], [142, 658])
        self.assertEqual(rows[(0, 0, 4)]["after_passes"]["2"][:2], [142, 654])      # ROM snaps an embedded 658 up to 654 at pass 2
        self.assertEqual(rows[(0, 1, -5)]["settled"], [110, 398])
        self.assertEqual(rows[(0, 2, -5)]["settled"], [110, 238])

    def test_doc_table_matches_render(self):
        doc = (ROOT / "docs" / "rq4-campaign-start-registration.md").read_text(encoding="utf-8")
        a, b = "<!-- BEGIN handoff-table -->", "<!-- END handoff-table -->"
        body = doc[doc.index(a) + len(a):doc.index(b)].strip()
        self.assertEqual(body, R.handoff_table(DATA).strip())

    def test_negative_controls(self):
        for mutate in (
            lambda d: d["summary"][0].__setitem__("record_player", [142, 658]),
            lambda d: d["summary"][0].__setitem__("camera_committed_at_first_update_equals_record", False),
            lambda d: d["summary"][3].__setitem__("reload_equals_fresh", False),
            lambda d: d["static"]["table"].pop(),
            lambda d: d.__setitem__("rom_sha256", "0" * 64),
        ):
            bad = copy.deepcopy(DATA)
            mutate(bad)
            self.assertTrue(R.validate(bad), "mutation was not detected")


@unittest.skipUnless(canonical_rom() is not None, "canonical ROM not available")
class AgainstRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import z80  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("z80 package not installed")
        cls.rom = canonical_rom()

    def test_static_table(self):
        self.assertEqual(R.static_census(self.rom), DATA["static"])

    def test_replay_thz1_and_thz3(self):
        for z, a in ((0, 0), (0, 2)):
            got = R.observe_act((str(ROM_PATH), z, a))
            want = next(o for o in DATA["observations"] if o["zone"] == z and o["act"] == a)
            self.assertEqual(got, want)


if __name__ == "__main__":
    unittest.main()

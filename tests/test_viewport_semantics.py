#!/usr/bin/env python3
"""Viewport-semantics audit: cache-driven tests (no ROM) plus ROM-backed controlled sweeps.

The ROM-backed class runs when a matching ROM is found (set SONIC_CHAOS_ROM) and skips otherwise.
Every ROM-backed test re-runs the original routine over synthetic camera positions that differ from the
ones used to generate the cache, so a rule that only fits one level location cannot pass.
"""
import hashlib
import importlib.util
import json
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
CACHE = ROOT / "data" / "rom-cache" / "viewport-semantics.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("viewport_semantics", ROOT / "tools" / "viewport_semantics.py")
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)

# cameras deliberately not in vs.CAMERAS
OTHER_CAMERAS = [3, 99, 129, 300, 777, 1500, 2600, 3333, 4000, 6001, 12345]


def matching_rom():
    candidates = []
    if os.environ.get("SONIC_CHAOS_ROM"):
        candidates.append(Path(os.environ["SONIC_CHAOS_ROM"]))
    candidates += [ROOT.parent / "Sonic Chaos (Europe).sms", ROOT.parent / "source" / "Sonic Chaos (Europe).sms",
                   ROOT / "Sonic Chaos (Europe).sms"]
    for path in candidates:
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == ROM_SHA:
            return path
    return None


ROM = matching_rom()
ROM_BYTES = ROM.read_bytes() if ROM else None


def lab():
    return vs.Lab(ROM_BYTES)


class ProvenanceTests(unittest.TestCase):
    def test_header(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertTrue(D["research_only"])
        self.assertTrue(D["poc_untouched"])
        self.assertEqual(D["machine_facing_label"], "viewport_semantics")
        self.assertFalse(D["static_only"])

    def test_no_rom_dump(self):
        for r in D["routines"]:
            self.assertLessEqual(len(r["first_16_bytes"]), 32)
        self.assertNotIn("cram_bytes", json.dumps(D))

    def test_every_routine_is_hashed(self):
        self.assertGreaterEqual(len(D["routines"]), 25)
        for r in D["routines"]:
            self.assertEqual(len(r["sha256"]), 64)
            self.assertGreater(r["length"], 0)

    def test_every_constant_row_is_complete_and_classified(self):
        self.assertGreaterEqual(len(D["constants"]), 30)
        for r in D["constants"]:
            for key in ("system", "constant", "rom_address", "raw_meaning", "coordinate_frame", "class", "relationship_to_256px",
                        "widescreen_implication", "confidence", "evidence"):
                self.assertTrue(r[key], (r["constant"], key))
            self.assertIn(r["class"], D["classes"])
            self.assertIn(r["confidence"], ("high", "medium", "low"))


class ModelTests(unittest.TestCase):
    """Pure models: no ROM, no cache."""

    def test_band_edges_are_edge_relative(self):
        # the band spans do not depend on any camera: only on d = x - camera
        self.assertEqual([vs.band(d) for d in (-129, -128, -97, -96, -33, -32, -1, 0, 255, 256, 287, 288, 351, 352, 383, 384)],
                         [3, 3, 3, 2, 2, 1, 1, 0, 0, 1, 1, 2, 2, 3, 3, 3])

    def test_cell_is_chebyshev_of_axis_bands(self):
        for dx in range(-140, 400, 5):
            for dy in range(-140, 400, 5):
                self.assertEqual(vs.cell(dx, dy), max(vs.band(dx), vs.band(dy)))

    def test_lifecycle_outcomes(self):
        self.assertEqual(vs.lifetime_outcome(287, 100, False, True), ("active", 0))
        self.assertEqual(vs.lifetime_outcome(288, 100, False, True), ("asleep", 1))
        self.assertEqual(vs.lifetime_outcome(351, 100, False, True), ("asleep", 1))
        self.assertEqual(vs.lifetime_outcome(352, 100, False, True), ("remove_tracked", 1))
        self.assertEqual(vs.lifetime_outcome(352, 100, True, True), ("asleep", 1))
        self.assertEqual(vs.lifetime_outcome(-97, 100, False, False), ("remove_untracked", 1))
        self.assertEqual(vs.lifetime_outcome(-96, 100, False, True), ("asleep", 1))

    def test_creation_ring(self):
        self.assertFalse(vs.scan_creates(287, 100, False))      # active band: not created in steady state
        self.assertTrue(vs.scan_creates(287, 100, True))        # ...but created during the initial fill
        self.assertTrue(vs.scan_creates(288, 100, False))
        self.assertTrue(vs.scan_creates(351, 100, False))
        self.assertFalse(vs.scan_creates(352, 100, True))

    def test_state20_threshold_is_right_plus_33(self):
        self.assertFalse(vs.state20_flag(288))
        self.assertTrue(vs.state20_flag(289))
        self.assertEqual(0x121, vs.VIEW_W + 33)
        for cam in vs.CAMERAS + OTHER_CAMERAS:
            # the same relationship at every camera: playerX = cam + RIGHT_OFFSET
            self.assertFalse(vs.state20_flag((cam + 288) - cam))
            self.assertTrue(vs.state20_flag((cam + 289) - cam))

    def test_state20_camera_freeze_threshold(self):
        self.assertFalse(vs.state20_camera_freeze(0xF8))
        self.assertTrue(vs.state20_camera_freeze(0xF9))

    def test_clamp_uses_the_low_byte(self):
        self.assertEqual(vs.clamp_bound(15), "left")
        self.assertIsNone(vs.clamp_bound(16))
        self.assertIsNone(vs.clamp_bound(247))
        self.assertEqual(vs.clamp_bound(248), "right")
        self.assertEqual(vs.clamp_bound(256 + 5), "left")       # wrap hazard

    def test_follow_delta_quirk(self):
        self.assertEqual([vs.follow_delta_x(k, 0x68) for k in (87, 88, 89, 95, 96, 112, 113, 119, 120, 200)], [-7, -8, -7, -1, 0, 0, 1, 7, 7, 7])
        self.assertEqual(vs.follow_delta_x(0x80, 0x88), 0)

    def test_limit_semantics(self):
        self.assertEqual(vs.limit_x_delta(3831, 1, 0, 3832), 0)     # right limit exclusive
        self.assertEqual(vs.limit_x_delta(3830, 1, 0, 3832), 1)
        self.assertEqual(vs.limit_x_delta(100, -5, 95, 4000), -5)   # left limit inclusive
        self.assertEqual(vs.limit_x_delta(100, -6, 95, 4000), 0)


class CacheTests(unittest.TestCase):
    """The committed cache, no ROM needed."""

    def test_spawn_map_is_closed_form(self):
        sm = D["spawn_map"]
        self.assertTrue(sm["closed_form_cell_equals_max_of_axis_bands"])
        self.assertEqual(sm["value_counts"], {"0": 256, "1": 144, "2": 384, "3": 240})
        self.assertEqual(sm["rows"][12], "33222211000000000000000011222233")
        self.assertEqual(sm["rows"][0], "3" * 32)
        spans = {b["band"]: b["screen_relative_spans_half_open"] for b in sm["bands"]}
        self.assertEqual(spans[0], [[0, 256]])
        self.assertEqual(spans[1], [[-32, 0], [256, 288]])
        self.assertEqual(spans[2], [[-96, -32], [288, 352]])

    def test_limits_encode_width_minus_256(self):
        rel = D["level_limits"]["thz_world_width_relation"]
        for act in ("thz1", "thz2", "thz3"):
            self.assertTrue(rel[act]["right_limit_equals_width_minus_256"], act)
        for r in D["level_limits"]["rows"]:
            self.assertTrue(r["right_plus_256_multiple_of_256"], r)
        self.assertEqual(D["level_limits"]["rows"][0]["right"], 3840)

    def test_boss_tables(self):
        rows = D["boss_tables"]["rows"]
        self.assertEqual((rows[0]["trigger_abs_dx_lt"], rows[0]["trigger_abs_dy_lt"], rows[0]["pan_dx"], rows[0]["pan_dy"]), (160, 256, -256, -160))
        self.assertEqual([r["anchor_screen_x_when_pan_complete"] for r in rows[:6]], [256, 192, 224, 208, 128, 128])

    def test_future_sites_bytes_match(self):
        for s in D["future_risk_scan"]["sites"]:
            self.assertTrue(s["bytes_match_expected"], s)
        calls = D["future_risk_scan"]["camera_vector_call_sites"]
        self.assertEqual(sum(len(v) for v in calls.values()), 13)

    def test_future_zone_bosses_are_placed_in_act_3(self):
        p = D["future_risk_scan"]["placed_types_by_zone_act"]
        self.assertIn("0x50", p["zone0_act2"])
        self.assertIn("0x51", p["zone1_act2"])
        self.assertIn("0x54", p["zone2_act2"])
        self.assertIn("0x56", p["zone3_act2"])
        self.assertIn("0x59", p["zone4_act2"])
        self.assertIn("0x5E", p["zone5_act2"])

    def test_all_fixtures_have_no_mismatches_and_enough_cases(self):
        minimum = {"lifetime_fixture": 70000, "placement_scan_fixture": 2000, "camera_follow_fixture": 2000, "camera_pan_fixture": 900,
                   "camera_limit_fixture": 100, "player_edge_clamp_fixture": 11000, "state20_fixture": 500, "child19_fixture": 12,
                   "player_distance_fixture": 1900}
        total = 0
        for key, n in minimum.items():
            self.assertGreaterEqual(D[key]["cases"], n, key)
            self.assertEqual(D[key]["mismatches"], 0, key)
            total += D[key]["cases"]
        self.assertGreater(total, 85000)

    def test_act_clear_emulated_runs(self):
        for r in D["emulated_act_clear_camera"]["runs"]:
            self.assertEqual(r["final_camera"][0], 3831)                       # target 3832, right limit exclusive
            self.assertEqual(r["pan_target"][0], 3832)
            self.assertFalse(r["camera_x_moves_after_pan"])                   # camera is fixed long before state $20
            self.assertLess(r["pan_x_complete_rel"], 10)
            self.assertLess(r["pan_y_complete_rel"], r["state20_starts_rel"])
            self.assertEqual(r["d_at_flag"], 0x121)
            self.assertEqual(r["player_x_minus_sign_x_at_flag"], 160)
            self.assertIn(r["sign_screen_x_final"], (129,))
            self.assertEqual(r["sign_screen_y_final"], 153)
            self.assertLess(r["camera_frozen_rel"], r["flag_rel"])
        self.assertEqual({r["camera_y_total_move"] for r in D["emulated_act_clear_camera"]["runs"]}, {41})

    def test_bee_entry_is_the_generic_ring(self):
        for r in D["emulated_bee_scroll"]["runs"]:
            self.assertTrue(344 <= r["created"]["screen_x"] <= 351, r)
            self.assertTrue(284 <= r["awake"]["screen_x"] <= 287, r)
            self.assertLess(r["first_moved"]["screen_x"], 288)
        for row in D["placement_scan_fixture"]["type_27_thz1"]:
            self.assertEqual(row["creation_screen_relative_x"], [-96, 351])
            self.assertEqual(row["active_screen_relative_x"], [-32, 287])

    def test_vdp(self):
        v = D["emulated_vdp"]
        self.assertTrue(v["r8_equals_neg_cam_plus_1"] and v["r9_equals_camy_plus_17_mod_224"] and v["r0_bit5_left_column_mask"])
        self.assertEqual(v["registers_seen_during_150_gameplay_frames"], [["0x26", "0xE2", "0xFF", "0xFB", "0x00", "0xFF"]])


@unittest.skipUnless(ROM_BYTES, "matching ROM not found (set SONIC_CHAOS_ROM)")
class RomBackedTests(unittest.TestCase):
    """Original routines on the Z80 core, swept over cameras that are NOT the ones used to build the cache."""

    @classmethod
    def setUpClass(cls):
        cls.lab = lab()

    def test_rom_hash_and_routine_regions(self):
        self.assertEqual(hashlib.sha256(ROM_BYTES).hexdigest(), ROM_SHA)
        table = {r["name"]: r for r in vs.routine_table(ROM_BYTES)}
        for r in D["routines"]:
            self.assertEqual(table[r["name"]]["sha256"], r["sha256"], r["name"])

    def test_spawn_map_matches_closed_form(self):
        sm = vs.spawn_map(ROM_BYTES)
        self.assertTrue(sm["closed_form_cell_equals_max_of_axis_bands"])
        self.assertEqual(sm["rows"], D["spawn_map"]["rows"])

    def test_state20_threshold_over_many_cameras(self):
        o, m = self.lab.o, self.lab.m
        o.bank(2, 0x0C)
        m[0xD12B] = 0x0C
        n = 0
        for act_idx in (0, 1, 2):
            for cam in OTHER_CAMERAS + [0, 65535 - 1000]:
                for diff in range(0xF0, 0x130):
                    m[0xD293], m[0xD298], m[0xD15E] = 0x40, act_idx, 0x88
                    o.word(0xD174, cam)
                    o.word(0xD511, (cam + diff) & 0xFFFF)
                    o.word(0xD516, 0x0500)
                    m[0xD504] = 0x10
                    o.cpu.ix = 0xD500
                    o.call(0x83A6)
                    n += 1
                    self.assertEqual((m[0xD293] & 0x30) != 0, diff >= 0x121, (act_idx, cam, diff))
                    self.assertEqual((m[0xD15E] & 0x80) == 0, diff >= 0xF9, (act_idx, cam, diff))
                    if diff >= 0x121:
                        self.assertEqual(m[0xD293] & 0x30, 0x20 if act_idx < 2 else 0x10)
        self.assertGreater(n, 1500)

    def test_lifetime_over_other_cameras(self):
        o, m = self.lab.o, self.lab.m
        S = 0xD780
        n = 0
        for cam in OTHER_CAMERAS:
            for camy in (50, 333):
                for dx in range(-140, 400, 3):
                    for dy in (-100, 0, 191, 260, 300):
                        m[S:S + 0x40] = bytes(0x40)
                        m[S], m[S + 1], m[S + 3 + 1], m[S + 0x3E] = 0x27, 1, 0, 1
                        o.word(S + 0x11, cam + dx)
                        o.word(S + 0x14, camy + dy)
                        o.word(0xD174, cam)
                        o.word(0xD176, camy)
                        o.cpu.ix = S
                        o.call(0x61E1)
                        out, b6 = vs.lifetime_outcome(dx, dy, False, True)
                        want = 0x27 if out in ("active", "asleep") else 0xFE
                        n += 1
                        self.assertEqual((m[S], (m[S + 4] >> 6) & 1), (want, b6), (cam, camy, dx, dy))
        self.assertGreater(n, 5000)

    def test_inclusive_exclusive_edges_for_every_camera(self):
        o, m = self.lab.o, self.lab.m
        S = 0xD780
        for cam in vs.CAMERAS + OTHER_CAMERAS:
            for d, want in ((-96, "asleep"), (-97, "gone"), (-33, "asleep"), (-32, "active"), (255, "active"), (287, "active"),
                            (288, "asleep"), (351, "asleep"), (352, "gone")):
                m[S:S + 0x40] = bytes(0x40)
                m[S], m[S + 1], m[S + 0x3E] = 0x27, 1, 1
                o.word(S + 0x11, cam + d)
                o.word(S + 0x14, 400)
                o.word(0xD174, cam)
                o.word(0xD176, 300)
                o.cpu.ix = S
                o.call(0x61E1)
                got = "gone" if m[S] == 0xFE else "asleep" if (m[S + 4] >> 6) & 1 else "active"
                self.assertEqual(got, want, (cam, d))

    def test_placement_scan_over_other_cameras(self):
        o, m = self.lab.o, self.lab.m
        u = lambda p: vs.u16(ROM_BYTES, p)
        zp = u(0x70546)
        ap = u(0x70000 + zp - 0x8000)
        p = 0x70000 + ap - 0x8000
        recs = []
        while ROM_BYTES[p] != 0xFF:
            recs.append((ROM_BYTES[p], u(p + 1), u(p + 3)))
            p += 9
        n = 0
        for cam in OTHER_CAMERAS + list(range(40, 3900, 311)):
            for camy in (30, 250, 520):
                for fill in (0, 1):
                    o.bank(2, 0x1C)
                    m[0xD12B] = 0x1C
                    m[0xD400:0xD450] = bytes(0x50)
                    m[0xD700:0xD700 + 12 * 0x40] = bytes(12 * 0x40)
                    m[0xD297], m[0xD298], m[0xD440] = 0, 0, fill
                    o.word(0xD174, cam)
                    o.word(0xD176, camy)
                    o.call(0x8000)
                    got = [i for i in range(len(recs)) if m[0xD400 + i]]
                    want, free = [], 11
                    for i, (_, x, y) in enumerate(recs):
                        if vs.scan_creates(x - 256 - cam, y - 256 - camy, fill == 0) and free:
                            free -= 1
                            want.append(i)
                    n += 1
                    self.assertEqual(got, want, (cam, camy, fill))
        self.assertGreater(n, 100)

    def test_player_edge_clamp_over_other_cameras(self):
        o, m = self.lab.o, self.lab.m
        for entry in (0x4281, 0x4141):
            for cam in OTHER_CAMERAS:
                for d in range(0, 256):
                    o.word(0xD174, cam)
                    o.word(0xD511, cam + d)
                    m[0xD510], m[0xD501] = 0, 1
                    o.word(0xD516, 0)
                    o.cpu.ix = 0xD500
                    o.call(entry)
                    b = vs.clamp_bound(d)
                    want = {None: d, "left": 0x10, "right": 0xF7}[b]
                    self.assertEqual(o.word(0xD511) - cam, want, (hex(entry), cam, d))

    def test_clamp_is_not_applied_to_states_29_and_up(self):
        o, m = self.lab.o, self.lab.m
        for st in (0x29, 0x2A, 0x30):
            o.word(0xD174, 1000)
            o.word(0xD511, 1005)
            m[0xD501] = st
            o.word(0xD516, 0)
            o.cpu.ix = 0xD500
            o.call(0x4141)
            self.assertEqual(o.word(0xD511), 1005)

    def test_follow_over_other_cameras(self):
        o, m = self.lab.o, self.lab.m
        for cam in OTHER_CAMERAS:
            for left in (0, 1):
                for k in range(1, 256):
                    m[0xD15E], m[0xD15F] = 0x80, 0
                    self.lab.camera(cam, 300)
                    m[0xD504] = 0x10 if left else 0
                    lead = 0x88 if left else 0x68
                    m[0xD288], m[0xD289], m[0xD28A] = lead, 0x78, lead
                    m[0xD28C], m[0xD28B] = lead - 8, lead + 8
                    m[0xD28D], m[0xD28F], m[0xD28E] = 0x78, 0x68, 0x98
                    o.word(0xD511, cam + k)
                    o.word(0xD514, 420)
                    o.cpu.ix = 0xD15E
                    o.call(0x5832)
                    self.assertEqual(vs.s16(o.word(0xD284) - cam), vs.follow_delta_x(k, lead), (cam, left, k))

    def test_pan_is_one_pixel_per_axis_for_any_camera(self):
        o, m = self.lab.o, self.lab.m
        for cam in [c for c in OTHER_CAMERAS if c >= 200]:
            for tx_off, ty_off in ((50, -50), (-50, 50), (1, 1), (0, 0), (-1, 0)):
                m[0xD15E], m[0xD15F] = 0x80, 1
                self.lab.camera(cam, 400)
                m[0xD297] = 0
                o.word(0xD2DA, cam + tx_off)
                o.word(0xD2DC, 400 + ty_off)
                o.word(0xD280, 0)
                o.word(0xD282, 20000)
                o.word(0xD27C, 8)
                o.word(0xD27E, 784)
                m[0xD28A] = 0x78
                o.cpu.ix = 0xD15E
                o.call(0x5832)
                sx = (tx_off > 0) - (tx_off < 0)
                sy = (ty_off > 0) - (ty_off < 0)
                self.assertEqual((vs.s16(o.word(0xD284) - cam), vs.s16(o.word(0xD286) - 400)), (sx, sy))

    def test_camera_limit_clamp_over_many_limits(self):
        o, m = self.lab.o, self.lab.m
        for right in (3832, 3840, 2304, 500):
            for cam in (right - 8, right - 3, right - 1, 100):
                for delta in range(-9, 10):
                    flag = 4 if delta < 0 else 8 if delta > 0 else 0
                    m[0xD15E] = 0x80 | flag
                    o.word(0xD174, cam)
                    o.word(0xD284, cam + delta)
                    o.word(0xD280, 90)
                    o.word(0xD282, right)
                    o.cpu.ix = 0xD15E
                    o.call(0x4CB0)
                    want = vs.limit_x_delta(cam, delta, 90, right) if flag else 0
                    self.assertEqual(vs.s16(o.word(0xD284) - cam), want, (right, cam, delta))

    def test_player_relative_helpers_ignore_the_camera(self):
        o, m = self.lab.o, self.lab.m
        S = 0xD780
        for cam in OTHER_CAMERAS:
            for bc in (0x40, 0x180):
                for delta in (-bc - 1, -bc, -bc + 1, 0, bc - 1, bc, bc + 1):
                    m[S:S + 0x40] = bytes(0x40)
                    o.word(S + 0x11, 2500)
                    o.word(0xD511, 2500 + delta)
                    o.word(0xD174, cam)
                    o.cpu.ix = S
                    o.call(0x61A5, bc=bc)
                    self.assertEqual(o.cpu.a, 0xFF if abs(delta) < bc else 0, (cam, bc, delta))

    def test_type_28_persistence_radius(self):
        o, m = self.lab.o, self.lab.m
        o.bank(2, 0x1E)
        m[0xD12B] = 0x1E
        S = 0xD780
        for cam in OTHER_CAMERAS[:4]:
            for dx, dy, removed in ((639, 0, False), (640, 0, True), (0, 671, False), (0, 672, True), (-640, 0, True), (-639, -671, False)):
                m[S:S + 0x40] = bytes(0x40)
                m[S], m[S + 4] = 0x28, 2
                o.word(S + 0x11, 3000)
                o.word(S + 0x14, 3000)
                o.word(0xD511, 3000 + dx)
                o.word(0xD514, 3000 + dy)
                o.word(0xD174, cam)
                o.cpu.ix = S
                o.call(0x8908)
                self.assertEqual(m[S] == 0xFE, removed, (cam, dx, dy))

    def test_cache_regenerates_static_part(self):
        fresh = vs.build(ROM_BYTES, static_only=True)
        for key in ("routines", "spawn_map", "level_limits", "boss_tables", "future_risk_scan", "constants", "object_types", "unresolved"):
            self.assertEqual(fresh[key], D[key], key)


if __name__ == "__main__":
    unittest.main()

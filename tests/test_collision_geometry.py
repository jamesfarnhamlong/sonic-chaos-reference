#!/usr/bin/env python3
"""Collision-geometry audit: cache-driven tests (no ROM) plus ROM-backed re-execution.

Regenerating everything from the ROM: `python tools/collision_geometry.py ROM --check` or `tests/verify_cache.py ROM`.
The ROM-backed classes run when a matching ROM is found (set SONIC_CHAOS_ROM) and skip otherwise.
"""
import hashlib
import importlib.util
import json
import os
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
CACHE = ROOT / "data" / "rom-cache" / "collision-geometry.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("collision_geometry", ROOT / "tools" / "collision_geometry.py")
tool = importlib.util.module_from_spec(spec)
sys.modules["collision_geometry"] = tool
spec.loader.exec_module(tool)


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
needs_rom = unittest.skipUnless(ROM, "matching ROM not available (set SONIC_CHAOS_ROM)")


def base_case(**kw):
    c = {"ox": 1000, "oy": 500, "px": 1000, "py": 500, "ex": 8, "ey": 24, "oex": 12, "oey": 42, "f3": 0x80, "d503": 0,
         "b21": 0x50, "d521": 0x0A, "d520": 0x33, "ix": 0xD700, "d523": 0, "camx": 900}
    c.update(kw)
    return c


class ProvenanceTests(unittest.TestCase):
    def test_scope(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertTrue(D["research_only"])
        self.assertTrue(D["poc_untouched"])
        self.assertEqual(D["machine_facing_label"], "collision_geometry")

    def test_no_rom_dumps(self):
        text = json.dumps(D)
        for word in ("cram_bytes", "tile_pixels", "rgba", "palette_bytes"):
            self.assertNotIn(word, text)


class PlayerExtentTests(unittest.TestCase):
    P = D["player_extents"]

    def test_every_sonic_state_enumerated(self):
        self.assertEqual([r["state"] for r in self.P["sonic_type_1"]], list(range(0x34)))

    def test_sonic_extents(self):
        s = self.P["sonic_summary"]
        self.assertEqual(s["distinct_extent_pairs"], [[8, 24], [9, 24]])
        self.assertEqual(s["states_with_other_extents"], {"15": [[9, 24]]})
        self.assertEqual(len(s["states_with_8_24_only"]), 0x34 - 1)
        for r in self.P["sonic_type_1"]:
            want = [[9, 24]] if r["state"] == 0x0F else [[8, 24]]
            self.assertEqual(r["extents_x_y"], want, hex(r["state"]))

    def test_states_named_in_the_task(self):
        rows = {r["state"]: r for r in self.P["sonic_type_1"]}
        for state in (0x0B, 0x0E, 0x18, 0x20, 0x11, 0x0F):            # spring, ..., reward state, act-clear run
            self.assertIn(state, rows)
        self.assertEqual(rows[0x18]["extents_x_y"], [[8, 24]])
        self.assertEqual(rows[0x20]["extents_x_y"], [[8, 24]])
        self.assertEqual(rows[0x20]["frames"], [1, 2, 3, 4, 5, 6])
        self.assertEqual(rows[0x0F]["frames"], [34, 35, 36])

    def test_type2_has_large_frames(self):
        big = {r["state"] for r in self.P["type_2"] if [12, 32] in r["extents_x_y"]}
        self.assertEqual(big, {0x16, 0x17, 0x2A})

    def test_emulated_play_agrees(self):
        obs = D["emulated_player_extents"]["observed_by_current_state"]
        self.assertGreaterEqual(len(obs), 15)
        for state, ext in obs.items():
            if state == "0x00":
                continue
            self.assertEqual(ext, [[9, 24]] if state == "0x0F" else [[8, 24]], state)
        self.assertEqual(D["emulated_player_extents"]["frames"], 8000)

    def test_only_helpers_read_the_fields(self):
        f = D["extent_fields"]
        reads = sorted(int(r["cpu"], 16) for r in f["absolute_reads_of_D52C_D52D"])
        self.assertEqual(reads, [0x5FE0, 0x6023, 0x6052, 0x6358, 0x6376, 0x6397, 0x643B, 0x6458, 0x6478])
        self.assertEqual(f["absolute_writes_of_D52C_D52D"], [])
        engine = [w for w in f["index_register_writes_of_extent_fields"] if w["bank"] == "0x01"]
        self.assertEqual(sorted(w["cpu"] for w in engine), ["0x6595", "0x659A"])


class OverlapSpecTests(unittest.TestCase):
    G = D["overlap_6328"]["grid"]

    def test_grid_recorded(self):
        self.assertGreaterEqual(self.G["cases_compared"], 60000)
        self.assertEqual(self.G["mismatches"], 0)
        self.assertGreater(self.G["contact_cases"], 10000)
        self.assertGreater(self.G["no_contact_cases"], 10000)

    def test_model_edges(self):
        m = tool.model_6328
        inside = lambda **kw: (m(base_case(**kw))["b21"] & 15) != 0
        self.assertTrue(inside(px=1020))              # dx = +20 = 8 + 12
        self.assertFalse(inside(px=1021))
        self.assertTrue(inside(px=980))
        self.assertFalse(inside(px=979))
        self.assertTrue(inside(py=524))               # dy = +24 (player extent only)
        self.assertFalse(inside(py=525))
        self.assertTrue(inside(py=458))               # dy = -42 (object extent only)
        self.assertFalse(inside(py=457))
        self.assertFalse(inside(px=1000 + 256))
        self.assertFalse(inside(px=1000 - 256))
        self.assertFalse(inside(ex=255, oex=0, px=1000 - 256))

    def test_model_bits_and_penetration(self):
        m = tool.model_6328
        self.assertEqual(m(base_case(px=1010, py=500))["b21"], 0x04)      # deep in Y, shallow in X: horizontal, player right
        self.assertEqual(m(base_case(px=990, py=500))["b21"], 0x08)
        self.assertEqual(m(base_case(px=1000, py=520))["b21"], 0x02)      # player below
        self.assertEqual(m(base_case(px=1000, py=470))["b21"], 0x01)      # player above (vPen 12 < hPen 20)
        # exact tie: hPen == vPen selects the vertical axis
        tie = base_case(ex=8, oex=12, ey=24, oey=42, px=1000 + 4, py=500 + 4)   # hPen 16, vPen 20 -> horizontal
        self.assertEqual(m(tie)["b21"], 0x04)
        tie = base_case(ex=8, oex=12, ey=24, oey=42, px=1000 + 4, py=500)       # hPen 16, vPen 24
        self.assertEqual(m(tie)["b21"], 0x04)
        tie = base_case(ex=8, oex=8, ey=24, oey=42, px=1000, py=500 + 8)        # hPen 16, vPen 16: tie -> vertical
        self.assertEqual(m(tie)["b21"], 0x02)

    def test_gates(self):
        m = tool.model_6328
        self.assertEqual(m(base_case(f3=0x40))["b21"] & 15, 0)
        self.assertEqual(m(base_case(f3=0x00, d503=0x40))["b21"] & 15, 0)      # player bit 6 blocks unless +$03 bit 7
        self.assertNotEqual(m(base_case(f3=0x80, d503=0x40))["b21"] & 15, 0)
        r = m(base_case(d503=0x80))
        self.assertEqual(r["b20"], 0)
        self.assertEqual(m(base_case(d503=0x00))["b20"], 1)

    def test_outputs(self):
        r = tool.model_6328(base_case(f3=0x00, ix=0xD540, px=1000, py=520))
        self.assertEqual(r["d520"], 2)                                # slot id of $D540
        self.assertEqual(r["d521"] & 0xF0, (0x02 ^ 0x03) << 4)        # mirrored vertical contact
        self.assertEqual(r["b21"] & 0xF0, 0)                          # high nibble cleared on success
        r = tool.model_6328(base_case(px=2000))
        self.assertEqual(r["b21"], 0x50)                              # failure keeps the high nibble, clears the low nibble

    def test_spec_text_mentions_intervals(self):
        self.assertIn("anchor is the bottom edge", D["overlap_6328"]["rule"]["interval_form"])


class SolidSpecTests(unittest.TestCase):
    G = D["solid_5FA0"]["grid"]

    def test_grid_recorded(self):
        self.assertGreaterEqual(self.G["cases_compared"], 20000)
        self.assertEqual(self.G["mismatches"], 0)
        c = self.G["classification_counts"]
        for k in ("player_above", "player_below", "player_left", "player_right", "position_pushed", "position_not_pushed"):
            self.assertGreater(c[k], 100, k)

    def test_dispatch_table(self):
        d = D["solid_5FA0"]["dispatch"]
        self.assertEqual(d["nibble 1 (player above)"], "$5FF1")
        self.assertEqual(d["nibble 2 (player below)"], "$5FDA")
        self.assertEqual(d["nibble 4 (player right)"], "$6038")
        self.assertEqual(d["nibble 8 (player left)"], "$6009")

    def test_model_actions(self):
        m = tool.model_5fa0
        above = m(base_case(py=470))
        self.assertEqual(above["py"], 500 - 42)                       # standing on the top edge: objectY - objectExtY
        below = m(base_case(py=520))
        self.assertEqual(below["py"], 500 + 24)                       # objectY + playerExtY
        right = m(base_case(px=1015, py=500))
        self.assertEqual(right["px"], 1000 + 12 + 8)
        left = m(base_case(px=985, py=500))
        self.assertEqual(left["px"], 1000 - (12 + 8))
        # blocked by the combined contact flag
        self.assertEqual(m(base_case(py=470, d523=1))["py"], 470)
        self.assertEqual(m(base_case(py=520, d523=2))["py"], 520)
        self.assertEqual(m(base_case(px=1015, d523=4))["px"], 1015)
        self.assertEqual(m(base_case(px=985, d523=8))["px"], 985)
        # near the camera edge the side pushes are suppressed
        self.assertEqual(m(base_case(px=985, camx=985 - 0x20))["px"], 985)      # px == camX + $20: unchanged
        self.assertEqual(m(base_case(px=985, camx=985 - 0x21))["px"], 980)
        self.assertEqual(m(base_case(px=1015, camx=1015 - 0xE0))["px"], 1020)
        self.assertEqual(m(base_case(px=1015, camx=1015 - 0xE1))["px"], 1015)

    def test_no_velocity_or_state_write(self):
        self.assertIn("NONE", D["solid_5FA0"]["velocity_and_state"])


class HelperMatrixTests(unittest.TestCase):
    T = D["helper_matrix"]["types"]

    def helpers(self, t):
        return set(self.T[t]["helpers"])

    def test_overlap_users(self):
        for t in ("0x18", "0x1B", "0x21", "0x27", "0x28"):
            self.assertIn("overlap_6328", self.helpers(t), t)
        self.assertEqual(self.T["0x27"]["helpers"]["overlap_6328"], 3)
        self.assertEqual(self.T["0x28"]["helpers"]["overlap_6328"], 4)

    def test_solid_users(self):
        self.assertIn("solid_5FA0", self.helpers("0x10"))
        self.assertIn("solid_5FA0", self.helpers("0x50"))
        for t in ("0x18", "0x1B", "0x21", "0x26", "0x27", "0x28"):
            self.assertNotIn("solid_5FA0", self.helpers(t), t)

    def test_spring_has_no_overlap(self):
        h = self.helpers("0x26")
        self.assertNotIn("overlap_6328", h)
        self.assertIn("proximity_x_61A5", h)
        self.assertIn("proximity_y_61B1", h)
        self.assertIn("vertical_spring_setter_5F17", h)

    def test_rings_use_the_anchor_box(self):
        self.assertIn("ring_pickup_box_617E", self.helpers("0x09"))
        self.assertNotIn("overlap_6328", self.helpers("0x09"))

    def test_object_extents(self):
        ext = lambda t, s: self.T[t]["extents_by_state"][str(s)]
        self.assertEqual(ext("0x10", 2), [[10, 24]])
        self.assertEqual(ext("0x18", 3), [[12, 42]])
        self.assertEqual(ext("0x1B", 2), [[16, 24]])
        self.assertEqual(ext("0x21", 3), [[11, 26]])
        self.assertEqual(ext("0x26", 1), [[8, 32]])
        self.assertEqual(ext("0x27", 1), [[9, 14]])
        self.assertEqual(ext("0x28", 5), [[16, 16]])
        self.assertEqual(ext("0x50", 6), [[20, 48]])

    def test_attack_and_bounce_helpers(self):
        self.assertIn("attack_check_5F3D", self.helpers("0x27"))
        self.assertIn("vertical_spring_setter_5F17", self.helpers("0x21"))
        self.assertIn("destroy_convert_5F54", self.helpers("0x10"))
        self.assertIn("level_complete_4892", self.helpers("0x19"))
        self.assertIn("level_complete_4892", self.helpers("0x50"))


class SweepTests(unittest.TestCase):
    rows = {(r["type"], r["state"]): r for r in D["callback_sweeps"]["rows"]}

    def test_boxes_match_the_formula(self):
        for key in (("0x10", 2), ("0x1B", 2), ("0x27", 1), ("0x27", 2), ("0x28", 5), ("0x21", 3)):
            r = self.rows[key]
            self.assertTrue(r["rectangular"], key)
            self.assertEqual((r["cells_only_in_formula"], r["cells_only_in_callback"]), (0, 0), key)

    def test_sonic_boxes(self):
        self.assertEqual((self.rows[("0x10", 2)]["contact_dx"], self.rows[("0x10", 2)]["contact_dy"]), ([-18, 18], [-24, 24]))
        self.assertEqual((self.rows[("0x1B", 2)]["contact_dx"], self.rows[("0x1B", 2)]["contact_dy"]), ([-24, 24], [-24, 24]))
        self.assertEqual((self.rows[("0x27", 1)]["contact_dx"], self.rows[("0x27", 1)]["contact_dy"]), ([-17, 17], [-14, 24]))
        self.assertEqual((self.rows[("0x21", 3)]["contact_dx"], self.rows[("0x21", 3)]["contact_dy"]), ([-19, 19], [-26, 24]))
        self.assertEqual((self.rows[("0x28", 5)]["contact_dx"], self.rows[("0x28", 5)]["contact_dy"]), ([-24, 24], [-16, 24]))

    def test_platform_state2_moves_first(self):
        r = self.rows[("0x28", 2)]
        self.assertEqual(r["cells_only_in_formula"], r["cells_only_in_callback"])       # a one-pixel shift, same area
        self.assertEqual(r["cells"], 2009)

    def test_spring_26(self):
        s = D["spring_26"]
        self.assertEqual(s["contact_dx"], [-11, 11])                    # strict < 12
        self.assertEqual(s["contact_dy_relative_to_object_Y"], [-33, -28])
        self.assertTrue(s["rectangular"])
        g = s["gates_at_dx0_dy_minus_30"]
        self.assertTrue(g["baseline"])
        self.assertFalse(g["player_moving_up_D519_bit7"])
        self.assertFalse(g["no_floor_contact_D522_bit1"])
        self.assertFalse(g["requested_state_21"])
        self.assertFalse(g["object_offscreen_bit6"])

    def test_proximity_and_ring_box(self):
        p = D["proximity"]
        res = {r["dx"]: r["result_A"] for r in p["x_proximity_61A5_bc_12"]}
        self.assertEqual((res[11], res[12], res[-11], res[-12]), (255, 0, 255, 0))
        ring = {(r["dx"], r["dy"]): r["hit"] for r in p["ring_box_617E"]}
        self.assertTrue(ring[(11, 11)])
        self.assertFalse(ring[(12, 0)])
        self.assertFalse(ring[(0, 12)])
        self.assertFalse(ring[(-12, 0)])


class TerrainTests(unittest.TestCase):
    T = D["terrain_constants"]

    def test_side_probes(self):
        p = self.T["side_probe_offsets"]
        self.assertEqual((p["left_x"], p["right_x"], p["y_both"]), (-9, 9, -12))
        self.assertTrue(p["bytes_at_3686"].startswith("dd 7e 00 3d 20 1d 01 f7 ff 11 f4 ff"))

    def test_no_state_dependence(self):
        self.assertIn("no state-dependent", self.T["state_dependence"])
        self.assertIn("no terrain routine reads", self.T["terrain_never_reads_extents"])


class AssumptionAuditTests(unittest.TestCase):
    A = D["assumption_audit"]

    def test_classes(self):
        classes = {a["class"].split(" ")[0] for a in self.A}
        self.assertTrue({"TEST-ONLY", "EDGE", "CRITICAL", "NOT"} <= classes)

    def test_critical_entries(self):
        crit = [a["where"] for a in self.A if a["class"] == "CRITICAL"]
        self.assertEqual(len(crit), 3)
        joined = " ".join(crit)
        self.assertIn("OBJ_ring", joined)
        self.assertIn("SCR_monitor_collisions", joined)
        self.assertIn("goal sign", joined)

    def test_type10_fixture_was_corrected(self):
        """The cached type-$10 boundary fixture is now produced with Sonic's (8,24) and agrees with the recovered rule."""
        stored = json.loads((ROOT / "data/rom-cache/thz1/object-10.json").read_text(encoding="utf-8"))
        rows = stored["controlled_original_routine_fixtures"]["contact"]["overlap_boundaries"]
        by = {(r["axis"], r["delta"]): int(r["contact_bits_21"], 16) for r in rows}
        self.assertEqual(sorted(by), [("bottom", 23), ("bottom", 24), ("bottom", 25), ("horizontal_right", 17), ("horizontal_right", 18),
                                      ("horizontal_right", 19), ("top", -25), ("top", -24), ("top", -23)])
        for (axis, delta), bits in by.items():
            dx, dy = (delta, 0) if axis == "horizontal_right" else (0, delta)
            self.assertEqual(bits != 0, tool._pred(dx, dy, 8, 24, 10, 24), (axis, delta))
        # the superseded (9,18) rule would have disagreed at exactly these two cells
        old = {(a, d) for (a, d) in [("horizontal_right", 19), ("bottom", 19)]
               if tool._pred(*((d, 0) if a == "horizontal_right" else (0, d)), 9, 18, 10, 24) != tool._pred(*((d, 0) if a == "horizontal_right" else (0, d)), 8, 24, 10, 24)}
        self.assertEqual(old, {("horizontal_right", 19), ("bottom", 19)})
        self.assertTrue(all(a["status"].startswith("CORRECTED") for a in D["assumption_audit"] if a["repo"] == "research"))

    def test_type21_type27_type50_fixtures_unchanged(self):
        # fixture offsets are inside both boxes, so the recorded results do not depend on the extent assumption
        for dx, dy, oex, oey in ((0, 0, 11, 26), (0, 4, 11, 26), (0, 0, 9, 14), (26, 0, 20, 48), (-26, 0, 20, 48), (0, 10, 20, 48), (0, -40, 20, 48)):
            self.assertEqual(tool._pred(dx, dy, 9, 18, oex, oey), tool._pred(dx, dy, 8, 24, oex, oey), (dx, dy, oex, oey))


class PocMaskTests(unittest.TestCase):
    def test_mask_derivation(self):
        m = D["poc_player_mask"]
        self.assertEqual(m["chaosAnchorOffset"], 5)
        self.assertEqual(m["mask_relative_to_rom_anchor"], {"x": [-4, 6], "y": [-12, 18]})
        self.assertEqual(m["rom_overlap_box_relative_to_rom_anchor_sonic"], {"x": [-8, 8], "y": [-24, 0]})

    def test_interval_form_equals_the_formula(self):
        """Closed-interval overlap of [px-Ex, px+Ex] x [py-Ey, py] with the object box equals the recovered rule."""
        for ex, ey, oex, oey in ((8, 24, 12, 42), (9, 24, 10, 24), (8, 24, 16, 16)):
            for dx in range(-50, 51):
                for dy in range(-70, 50):
                    interval = (dx - ex <= oex and dx + ex >= -oex) and (dy - ey <= 0 and dy >= -oey)
                    self.assertEqual(interval, tool._pred(dx, dy, ex, ey, oex, oey), (ex, ey, oex, oey, dx, dy))

    def test_audit_entries_reference_poc(self):
        poc = [a for a in D["assumption_audit"] if a["repo"] == "poc"]
        self.assertGreaterEqual(len(poc), 9)
        self.assertTrue(any("SCR_chaos_spike_step" in a["where"] for a in poc))
        self.assertTrue(any("OBJ_chaos_object_27" in a["where"] for a in poc))


class ChangedRegionTests(unittest.TestCase):
    def test_difference_between_old_and_recovered_extents(self):
        """Cells whose contact result differs between (9,18) and (8,24) for each object: a 1-px column pair and a 6-row band."""
        for oex, oey in ((10, 24), (16, 16), (16, 24), (11, 26), (9, 14), (12, 42)):
            diff = {(dx, dy) for dx in range(-60, 61) for dy in range(-80, 80)
                    if tool._pred(dx, dy, 9, 18, oex, oey) != tool._pred(dx, dy, 8, 24, oex, oey)}
            self.assertTrue(diff)
            cols = {dx for dx, dy in diff if abs(dx) == 9 + oex}
            rows = {dy for dx, dy in diff if 18 < dy <= 24}
            self.assertEqual(cols, {-(9 + oex), 9 + oex})
            self.assertEqual(rows, set(range(19, 25)))


@needs_rom
class RomBackedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()

    def test_overlap_sample_against_original(self):
        from oracle import Oracle
        o = Oracle(self.rom)
        o.bank(2, 0x0C)
        m = o.mem
        rng = random.Random(77)
        n = 0
        for i in range(3000):
            c = tool._overlap_case(rng, i % 4 == 0)
            ix = c["ix"]
            o.word(ix + 0x11, c["ox"])
            o.word(ix + 0x14, c["oy"])
            o.word(0xD511, c["px"])
            o.word(0xD514, c["py"])
            m[0xD52C], m[0xD52D] = c["ex"], c["ey"]
            m[ix + 0x2C], m[ix + 0x2D] = c["oex"], c["oey"]
            m[ix + 3], m[ix + 0x21], m[ix + 0x20] = c["f3"], c["b21"], 0x77
            m[0xD503], m[0xD521], m[0xD520] = c["d503"], c["d521"], c["d520"]
            o.cpu.ix = ix
            o.call(0x6328)
            got = {"b20": m[ix + 0x20], "b21": m[ix + 0x21], "d520": m[0xD520], "d521": m[0xD521]}
            self.assertEqual(got, tool.model_6328(c), c)
            n += 1
        self.assertEqual(n, 3000)

    def test_player_extents_for_named_states(self):
        for state, want in ((0x01, [(8, 24)]), (0x0B, [(8, 24)]), (0x0F, [(9, 24)]), (0x18, [(8, 24)]), (0x20, [(8, 24)])):
            w = tool._engine_walk(self.rom, 1, state, 0x0300)
            self.assertEqual(sorted({(f[1], f[2]) for f in w["frames"]}), want, hex(state))

    def test_sign_contact_uses_sonic_extents(self):
        (oex, oey), hits = tool._sweep(self.rom, 0x18, 3, 0xA88E, rng=(-30, 30, -50, 30))
        self.assertEqual((oex, oey), (12, 42))
        xs = [a for a, b in hits]
        ys = [b for a, b in hits]
        self.assertEqual((min(xs), max(xs), min(ys), max(ys)), (-20, 20, -42, 24))

    def test_full_cache_regenerates(self):
        self.assertEqual(json.loads(json.dumps(tool.build(self.rom))), D)


if __name__ == "__main__":
    unittest.main()

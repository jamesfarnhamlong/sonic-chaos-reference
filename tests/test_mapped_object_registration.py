#!/usr/bin/env python3
"""Locks the mapped-object screen-registration research (cache driven, no ROM needed).

Regenerating the cache from the ROM is done by tests/verify_cache.py and
`tools/mapped_object_registration.py ROM --check data/rom-cache/mapped-object-registration.json`.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT / "data/rom-cache/mapped-object-registration.json").read_text(encoding="utf-8"))
SF = D["source_facts"]
EMU = SF["emulated_original_frames"]
FIX = {f["name"]: f for f in SF["controlled_routine_fixtures"]}
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"


def objects(case, typ):
    return [o for o in EMU[case]["observations"] if o["object"]["type"] == typ]


class RoutineTests(unittest.TestCase):
    def test_rom_hash_recorded(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)

    def test_renderer_routines_byte_verified_at_addresses(self):
        checks = {c["name"]: c for c in SF["routine_byte_checks"]}
        self.assertTrue(all(c["verified"] for c in checks.values()))
        self.assertEqual(checks["slot_render_loop"]["cpu"], "0x220E")
        self.assertEqual(checks["slot_render_loop"]["rom_offset"], "0x0220E")
        self.assertEqual(checks["screen_coordinate_prep"]["cpu"], "0x3FC8")
        self.assertEqual(checks["screen_coordinate_prep"]["rom_offset"], "0x03FC8")
        # $3FC8: LD L,(IX+$11); LD H,(IX+$12); LD DE,($D174); ...; LD (IX+$1A),L
        self.assertTrue(checks["screen_coordinate_prep"]["bytes"].startswith("dd6e11dd6612ed5b74d1"))
        self.assertIn("ed5b76d1", checks["screen_coordinate_prep"]["bytes"])  # camera Y $D176

    def test_no_gamemaker_values_in_source_facts(self):
        text = json.dumps(SF)
        for word in ("adapter", "GameMaker", "draw_sprite"):
            self.assertNotIn(word, text)


class MappingTests(unittest.TestCase):
    def test_type09_table_addresses(self):
        t = SF["mapping_tables"]["0x09"]
        self.assertEqual((t["mapping_table_cpu"], t["mapping_table_rom"], t["mapping_bank"]),
                         ("0x8C71", "0x3CC71", 15))
        f = t["frames"]["1"]
        self.assertEqual((f["frame_record_cpu"], f["frame_record_rom"]), ("0x8CE3", "0x3CCE3"))
        self.assertEqual(f["piece_y_offsets"], [-16, -16])  # signed decoding
        self.assertEqual(f["piece_x_offsets"], [-8, 0])
        self.assertEqual(f["mapped_y_range_rel_anchor"], [-16, -1])

    def test_tile_offsets_even_and_mirror_table(self):
        for typ, t in SF["mapping_tables"].items():
            for n, f in t["frames"].items():
                self.assertTrue(all(o % 2 == 0 for o in f["tile_offsets"]), (typ, n))
                self.assertTrue(f["mirror_table_is_neg_x_minus_8"], (typ, n))


class FixtureTests(unittest.TestCase):
    def test_z80_equals_model_everywhere(self):
        self.assertEqual(len(FIX), 12)
        for f in FIX.values():
            self.assertTrue(f["z80_equals_model"], f["name"])

    def test_type09_2880_384(self):
        f = FIX["type09_loop_2880_384"]
        self.assertEqual(f["screen_anchor_after_3FC8"], [2880 - 2704, 384 - 308])
        self.assertEqual(f["sat_y_z80"], [60, 60])  # 76 + 0 - 16
        self.assertEqual(f["sat_x_z80"], [168, 176])
        self.assertEqual(f["sat_tile_z80"], [16, 18])
        self.assertEqual(f["sat_first_line_last_line_screen"], [61, 76])

    def test_type09_twist_fixture(self):
        f = FIX["type09_twist_3124_548"]
        self.assertEqual(f["camera_D174_D176"], [2964, 446])
        self.assertEqual(f["sat_y_z80"], [548 - 446 - 16] * 2)  # 86

    def test_type21_flipped(self):
        f = FIX["type21_standing_800_590"]
        self.assertEqual(f["sat_y_z80"][0], 68)
        self.assertEqual(f["sat_y_z80"][-1], 84)


class EmulatedOriginalTests(unittest.TestCase):
    def test_piece_arithmetic(self):
        n = 0
        for v in EMU.values():
            for o in v["observations"]:
                cam_y = o["camera_D174_D176"][1]
                ob = o["object"]
                for p in ob["pieces"]:
                    n += 1
                    if p["hidden_by_y_clip"]:
                        continue
                    y = ob["runtime_anchor"][1] - cam_y + p["piece_y"]
                    # $226A adds the frame y origin; every mapped frame here has origin 0 or is folded into y16
                    self.assertEqual(p["sat_y"], p["y16"])
                    self.assertGreaterEqual(p["y16"] - y, -256)
        self.assertGreater(n, 100)

    def test_vdp_scroll_registers(self):
        for v in EMU.values():
            for o in v["observations"]:
                cx, cy = o["camera_D174_D176"]
                self.assertEqual(o["vdp_r9_vscroll"], (cy + 17) % 224)
                self.assertEqual(o["vdp_r8_hscroll"], (-(cx + 1)) & 255)

    def test_background_alignment_is_dx1_dy17(self):
        for case, v in EMU.items():
            a = v.get("background_alignment")
            if a:
                self.assertEqual((a["best_dy"], a["best_dx"]), (17, 1), case)
                self.assertGreaterEqual(a["best_match_fraction"], 0.95)
                self.assertGreater(a["best_match_fraction"], a["runner_up"]["match_fraction"])

    def test_type09_rows_rel_anchor(self):
        for case in ("loop_type09", "twist_type09", "post_twist_type09"):
            for o in objects(case, "0x09"):
                self.assertEqual(o["object"]["opaque_world_rows_rel_anchor"], [2, 17])

    def test_rows_per_type(self):
        want = {"0x10": [-6, 17], "0x21": [-14, 17], "0x27": [3, 17], "0x28": [2, 17], "0x18": [-30, 17]}
        seen = set()
        for v in EMU.values():
            for o in v["observations"]:
                t = o["object"]["type"]
                if t in want:
                    seen.add(t)
                    self.assertEqual(o["object"]["opaque_world_rows_rel_anchor"], want[t], t)
        self.assertEqual(seen, set(want))

    def test_type1b_all_states_share_bottom(self):
        rows = [o["object"]["opaque_world_rows_rel_anchor"] for o in objects("type1B_1344_864", "0x1B")]
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r[1] == 17 for r in rows))


class RuleTests(unittest.TestCase):
    def test_rule(self):
        r = D["interpretation"]["registration_rule"]
        self.assertIn("+ 17", r["equations"]["vdp_r9_vscroll"])
        self.assertIn("anchor_y + y_origin + m + 18", r["consequence"]["y"])
        self.assertIn("m + 1", r["consequence"]["x"])

    def test_poc_comparison_is_labelled_adapter_only(self):
        rows = {r["type"]: r for r in D["interpretation"]["poc_comparison"]["rows"]}
        self.assertEqual(rows["0x09"]["predicted_poc_minus_original_top"], -17)
        self.assertEqual(rows["0x10"]["predicted_poc_minus_original_top"], 0)
        self.assertEqual(rows["0x21"]["predicted_poc_minus_original_top"], 0)
        for r in rows.values():
            self.assertIn("GAMEMAKER ADAPTER ONLY", r["evidence"])
        self.assertEqual(D["interpretation"]["poc_comparison"]["poc_checkpoint"]["commit"],
                         "6819722201b169c4dac136efdb4236c5cf470327")


if __name__ == "__main__":
    unittest.main()

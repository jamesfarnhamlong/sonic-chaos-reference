#!/usr/bin/env python3
"""Gigapolis surface-$1C and type-$28/$83 audit regression locks."""
import hashlib
import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
CACHE = ROOT / "data" / "rom-cache" / "isometric-platform.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("isometric_platform", ROOT / "tools" / "isometric_platform.py")
tool = importlib.util.module_from_spec(spec)
sys.modules["isometric_platform"] = tool
spec.loader.exec_module(tool)


def matching_rom():
    candidates = []
    if os.environ.get("SONIC_CHAOS_ROM"):
        candidates.append(Path(os.environ["SONIC_CHAOS_ROM"]))
    candidates += [ROOT.parent / "source" / "Sonic Chaos (Europe).sms", ROOT / "Sonic Chaos (Europe).sms"]
    for path in candidates:
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == ROM_SHA:
            return path
    return None


ROM_PATH = matching_rom()


class TestIdentityAndCensus(unittest.TestCase):
    def test_canonical_rom_and_scope(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertTrue(D["research_only"])
        self.assertTrue(D["poc_untouched"])

    def test_identity_is_two_mechanisms(self):
        self.assertEqual(D["identity"]["terrain_surface"], "0x1C")
        self.assertEqual(D["identity"]["mapped_object_examined_separately"], "0x28")
        self.assertIn("two distinct systems", D["identity"]["finding"])

    def test_surface_1c_acts_and_count(self):
        c = D["terrain_census"]
        self.assertEqual(c["acts_with_surface_1c"], ["gpz1", "gpz2", "gpz3"])
        self.assertEqual([c["acts"][a]["count"] for a in c["acts_with_surface_1c"]], [212, 116, 90])
        self.assertEqual(c["total_cells"], 418)

    def test_surface_cell_manifest_hash(self):
        self.assertEqual(D["terrain_census"]["coordinate_hash_sha256"],
                         "e057b15a3c699ce51aa9105fc2133d3911d5d57740e82b42d1a23588df572bc7")

    def test_surface_blocks_are_exact(self):
        self.assertEqual(list(D["terrain_blocks"]), [f"0x{x:02X}" for x in range(0x8C, 0x98)])
        for b in D["terrain_blocks"].values():
            self.assertEqual((b["flags"], b["surface_type"], b["modifier"]), ("0x9C", 28, "0x00"))

    def test_surface_blocks_are_graphically_transparent(self):
        for b in D["terrain_blocks"].values():
            self.assertEqual(b["decoded_nonzero_palette_pixels"], 0)
            self.assertEqual(b["decoded_palette_indices"], [0])
            self.assertEqual(b["presentation"], "transparent/background colour only")

    def test_surface_and_parameter_83_do_not_overlap(self):
        c = D["type_28_terrain_contexts"]
        self.assertEqual(c["state4_total"], 32)
        self.assertEqual(c["state4_over_surface_1c"], 0)


class TestTerrainGeometry(unittest.TestCase):
    def test_flat_and_ramp_profiles(self):
        b = D["terrain_blocks"]
        for key in ("0x8C", "0x8D", "0x8E", "0x8F"):
            self.assertEqual(b[key]["effective_surface_1c_height_runs"], [[0, 31, "0x10"]])
        self.assertEqual(b["0x90"]["effective_surface_1c_height_runs"][:4],
                         [[0, 1, "0x01"], [2, 3, "0x02"], [4, 5, "0x03"], [6, 7, "0x04"]])
        self.assertEqual(b["0x93"]["effective_surface_1c_height_runs"][-1], [30, 31, "0x01"])

    def test_bit6_forces_full_height_only_for_previous_1c(self):
        for key in ("0x94", "0x95", "0x96", "0x97"):
            self.assertEqual(D["terrain_blocks"][key]["vertical_profile_runs"], [[0, 31, "0x54"]])
            self.assertEqual(D["terrain_blocks"][key]["effective_surface_1c_height_runs"], [[0, 31, "0x20"]])

    def test_boundary_sweep_case_count(self):
        self.assertEqual(D["surface_1c_boundary_sweeps"]["cases"], 15537)

    def test_boundary_sweep_surfaces_match_profiles(self):
        blocks = D["surface_1c_boundary_sweeps"]["per_block_floor_boundaries"]
        for key, block in blocks.items():
            expected = D["terrain_blocks"][key]["effective_surface_1c_height_runs"]
            # Every row records the original routine's boundary, while this check
            # locks the independently decoded height used to select that boundary.
            self.assertEqual(len(block["local_x_rows"]), 32)
            self.assertEqual([r["surface_local_y"] for r in block["local_x_rows"]],
                             [32 - r["effective_height"] for r in block["local_x_rows"]])
            self.assertTrue(expected)

    def test_rising_from_below_is_not_projected(self):
        a = {r["label"]: r for r in D["surface_1c_boundary_sweeps"]["selected_top_side_underside_approaches"]}
        self.assertFalse(a["from_below_rising"]["after"]["floor"])
        self.assertEqual(a["from_below_rising"]["after"]["vx"], 0)

    def test_horizontal_profile_does_not_make_a_side_wall(self):
        a = {r["label"]: r for r in D["surface_1c_boundary_sweeps"]["selected_top_side_underside_approaches"]}
        self.assertEqual(a["from_left_at_surface"]["after"]["vx"], 0x700)
        self.assertEqual(a["from_right_at_surface"]["after"]["vx"], -0x700)

    def test_isolated_side_and_underside_profiles(self):
        rows = D["surface_1c_boundary_sweeps"]["isolated_block_side_underside_sweeps"]
        for key in ("0x8C", "0x8D", "0x8E", "0x8F", "0x90", "0x91", "0x92", "0x93"):
            self.assertEqual(rows[key]["from_left_side_probe_local_y_changed_ranges"], [])
            self.assertEqual(rows[key]["ceiling_probe_local_y_changed_ranges"], [[27, 31]])
        for key in ("0x94", "0x95", "0x96"):
            self.assertEqual(rows[key]["from_left_side_probe_local_y_changed_ranges"], [[0, 15]])
            self.assertEqual(rows[key]["ceiling_probe_local_y_changed_ranges"], [[15, 20]])
        self.assertEqual(rows["0x97"]["from_left_side_probe_local_y_changed_ranges"], [[0, 23]])
        self.assertEqual(rows["0x97"]["ceiling_probe_local_y_changed_ranges"], [[15, 20]])


class TestParameter83(unittest.TestCase):
    def test_gp2_introduction(self):
        p = D["type_28_census"]["acts"]["gpz2"]["placements"]
        r = next(x for x in p if x["parameter"] == "0x83")
        self.assertEqual((r["world_x"], r["world_y"], r["initial_state"], r["aux1"]), (1584, 384, 4, "0x0B"))

    def test_support_triangle(self):
        region = D["type_28_parameter_83_sweep"]["support_region_dx_range_by_dy"]
        self.assertEqual(sorted(map(int, region)), list(range(-16, 0)))
        for dy in range(-16, 0):
            self.assertEqual(region[str(dy)], [-8 + dy, 8 - dy])

    def test_support_sweep_counts(self):
        s = D["type_28_parameter_83_sweep"]
        self.assertEqual(s["contact_flag_cases"], 2009)
        self.assertEqual(s["support_owner_claim_cases"], 544)
        self.assertEqual(s["cases"], 6640)

    def test_side_and_underside_do_not_project(self):
        probes = {r["name"]: r for r in D["type_28_parameter_83_sweep"]["selected_contacts"]}
        for name in ("left_side", "right_side", "underside_rising"):
            self.assertEqual(probes[name]["before"], probes[name]["after"])
            self.assertEqual(probes[name]["support_owner"], 0)
            self.assertEqual(probes[name]["trigger_phase"], "0x00")

    def test_player_states_do_not_change_support(self):
        rows = D["type_28_parameter_83_sweep"]["player_state_velocity_attack_matrix"]
        for r in rows:
            self.assertEqual(r["supported"], r["player_vy_8_8"] >= 0)

    def test_attack_and_floor_flags_do_not_change_support(self):
        rows = D["type_28_parameter_83_sweep"]["player_state_velocity_attack_matrix"]
        grouped = {}
        for r in rows:
            grouped.setdefault((r["state"], r["player_vy_8_8"]), []).append(r["supported"])
        self.assertTrue(all(v == [v[0], v[0]] for v in grouped.values()))

    def test_delay_gravity_and_sag_timing(self):
        s = D["type_28_parameter_83_sweep"]
        self.assertEqual((s["first_trigger_update"], s["first_falling_phase_update"]), (0, 81))
        self.assertEqual((s["first_sag_move_update"], s["first_gravity_update"], s["first_fall_integer_y_move_update"]),
                         (0, 82, 84))
        ys = [r[1] for r in s["timeline"][:18]]
        self.assertEqual((min(ys), max(ys), ys[8], ys[16]), (512, 520, 520, 512))

    def test_triggered_inactive_platform_is_consumed(self):
        rows = {r["phase_before"]: r for r in D["type_28_parameter_83_sweep"]["inactive_lifecycle"]}
        self.assertEqual(rows["0x00"]["type_after"], "0x28")
        for phase in ("0x80", "0xFF"):
            self.assertEqual((rows[phase]["type_after"], rows[phase]["tracking_token_after"]), ("0xFE", 0))


class TestReuseAndGraphics(unittest.TestCase):
    def test_mgh_parameter_83_counts(self):
        acts = D["type_28_census"]["acts"]
        self.assertEqual([acts[a]["parameter_counts"].get("0x83", 0) for a in ("mghz1", "mghz2", "mghz3")], [7, 7, 11])

    def test_mgh_exact_parameter_83_coordinates(self):
        got = {a: [(r["world_x"], r["world_y"]) for r in D["type_28_census"]["acts"][a]["placements"] if r["parameter"] == "0x83"]
               for a in ("mghz1", "mghz2", "mghz3")}
        self.assertEqual(got["mghz1"], [(752,736),(912,768),(1072,800),(1232,800),(1968,768),(2064,736),(2160,736)])
        self.assertEqual(got["mghz2"], [(848,608),(1072,608),(1264,608),(1392,608),(3056,736),(3312,800),(3792,800)])
        self.assertEqual(got["mghz3"], [(528,352),(592,384),(656,416),(720,448),(784,480),(848,512),
                                        (2160,640),(2288,640),(2416,640),(2544,640),(2672,640)])

    def test_other_parameter_83_appearances(self):
        acts = D["type_28_census"]["acts"]
        got = {a: v["parameter_counts"].get("0x83", 0) for a, v in acts.items() if v["parameter_counts"].get("0x83", 0)}
        self.assertEqual(got, {"gpz2": 1, "sez1": 2, "mghz1": 7, "mghz2": 7, "mghz3": 11, "eez1": 3, "eez3": 1})

    def test_mapping_is_shared_but_art_differs(self):
        g = D["graphics"]
        self.assertEqual((g["mapping_cpu"], g["frame_1"]["piece_count"]), ("0x9217", 4))
        self.assertNotEqual(g["zone_art"]["gpz"]["decoded_art_sha256"], g["zone_art"]["mghz"]["decoded_art_sha256"])
        self.assertEqual([g["zone_art"][z]["decoded_tile_count"] for z in ("gpz", "mghz")], [6, 8])
        self.assertEqual(g["zone_art"]["gpz"]["renderer_relative_bounds_inclusive"], [-16, 2, 7, 17])
        self.assertEqual(g["zone_art"]["mghz"]["renderer_relative_bounds_inclusive"], [-16, 2, 15, 17])


class TestEmulatorTraces(unittest.TestCase):
    def test_surface_trace_has_no_object_owner(self):
        for name in ("fall_to_surface_1c", "roll_across_surface_1c", "rocket_shoes_across_surface_1c"):
            self.assertTrue(all(r[8] == 0 for r in D["selected_emulator_traces"][name]))

    def test_rocket_state_crosses_surface(self):
        rows = D["selected_emulator_traces"]["rocket_shoes_across_surface_1c"]
        self.assertTrue(all(r[5] == 0x11 and r[2] == 28 for r in rows))

    def test_gp2_trace_triggers_sags_and_falls(self):
        rows = D["selected_emulator_traces"]["gpz2_near_parameter_83"]
        self.assertTrue(any(r[5] and r[9] == 0x80 for r in rows))
        self.assertTrue(any(r[9] == 0xFF and r[8] > 392 for r in rows))


@unittest.skipUnless(ROM_PATH, "canonical ROM not available")
class TestROMRegeneration(unittest.TestCase):
    def test_full_cache_regenerates_byte_for_byte(self):
        rebuilt = tool.dumps(tool.build(tool.load_rom(ROM_PATH)))
        self.assertEqual(rebuilt, CACHE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

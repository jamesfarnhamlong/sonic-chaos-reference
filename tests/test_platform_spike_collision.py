#!/usr/bin/env python3
"""Platform / spike collision audit: cache-driven tests (no ROM) plus ROM-backed re-execution.

Regenerating everything from the ROM: `python tools/platform_spike_collision.py ROM --check` or `tests/verify_cache.py ROM`.
The ROM-backed classes run when a matching ROM is found (set SONIC_CHAOS_ROM) and skip otherwise.
"""
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
CACHE = ROOT / "data" / "rom-cache" / "platform-spike-collision.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("platform_spike_collision", ROOT / "tools" / "platform_spike_collision.py")
tool = importlib.util.module_from_spec(spec)
sys.modules["platform_spike_collision"] = tool
spec.loader.exec_module(tool)


def matching_rom():
    candidates = []
    if os.environ.get("SONIC_CHAOS_ROM"):
        candidates.append(Path(os.environ["SONIC_CHAOS_ROM"]))
    candidates += [ROOT.parent / "Sonic Chaos (Europe).sms", ROOT.parent / "source" / "Sonic Chaos (Europe).sms", ROOT / "Sonic Chaos (Europe).sms"]
    for path in candidates:
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == ROM_SHA:
            return path
    return None


ROM_PATH = matching_rom()
ROM = ROM_PATH.read_bytes() if ROM_PATH else None


class TestCacheIdentity(unittest.TestCase):
    def test_hash_and_flags(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertTrue(D["research_only"])
        self.assertTrue(D["poc_untouched"])

    def test_case_total(self):
        self.assertGreater(D["counts"]["controlled_and_emulated_cases_total"], 250000)


class TestPlatformInventory(unittest.TestCase):
    def test_placements(self):
        p = D["platform_placements"]
        self.assertEqual([len(p[a]) for a in ("thz1", "thz2", "thz3")], [6, 3, 0])
        states = {(r["parameter"], r["initial_state"]) for a in p for r in p[a]}
        self.assertEqual(states, {("0x0A", 11), ("0x84", 5)})
        periods = {(r["act"], r["world_x"], r["world_y"]): r["reversal_period_updates"] for a in p for r in p[a] if r["initial_state"] == 11}
        self.assertEqual(periods, {("thz1", 592, 464): 144, ("thz1", 3664, 512): 208, ("thz2", 552, 720): 400, ("thz2", 3672, 608): 304})

    def test_fifteen_states_only_5_and_11_are_placed(self):
        modes = D["platform_modes"]
        self.assertEqual(len(modes["states"]), 15)
        self.assertEqual(modes["used_by_thz"], [5, 11])
        cb = {r["state"]: next(x["record"]["callback"] for x in r["script"] if "record" in x) for r in modes["states"]}
        self.assertEqual(cb[5], "0x879A")
        self.assertEqual(cb[11], "0x86DA")

    def test_object_28_is_not_a_spike(self):
        self.assertEqual([len(D["spike_1b_placements"][a]) for a in ("thz1", "thz2", "thz3")], [4, 0, 1])
        self.assertEqual({r["world_y"] for r in D["spike_1b_placements"]["thz1"]}, {864})


class TestPlatformModels(unittest.TestCase):
    def test_gate_is_signed_greater_than(self):
        for P in (-0x300, -0x100, -1, 0, 1, 0x100, 0x300):
            for p in (-0x400, -0x101, -0x100, -0xFF, -1, 0, 1, 0xFF, 0x100, 0x101, 0x400):
                self.assertEqual(tool.model_gate_8866(P, p), 0xFF if P > p else 0)

    def test_support_region_is_the_triangle(self):
        for dy in range(-30, 31):
            for dx in range(-30, 31):
                expect = (-16 <= dy <= -1) and abs(dx) <= min(24, 8 - dy)
                self.assertEqual(tool.model_contact(dx, dy) == 1, expect, (dx, dy))

    def test_sweeps_have_no_mismatches(self):
        for st in ("state_5", "state_11"):
            self.assertEqual(D["platform_support"][st]["mismatches"], 0)
            self.assertEqual(D["platform_support"][st]["cases"], 44652)
        self.assertEqual(D["platform_gate_8866"]["mismatches"], 0)

    def test_support_boundaries(self):
        s5 = D["platform_support"]["state_5"]["support_region_dx_range_by_dy_at_vy_plus_1_0"]
        self.assertEqual(s5["-16"], [-24, 24])
        self.assertEqual(s5["-1"], [-9, 9])
        self.assertEqual(D["platform_support"]["state_5"]["dy_extremes"], [-16, -1])
        # the lift moves 1 px up before the contact test: the same region relative to the pre-move anchor
        self.assertEqual(D["platform_support"]["state_11"]["dy_extremes"], [-17, -2])

    def test_gate_threshold_equals_platform_speed(self):
        th = D["platform_gate_8866"]["pass_threshold_by_platform_speed"]
        self.assertEqual({k: v["gate_passes_from_player_vy"] for k, v in th.items()}, {"-256": -256, "0": 0, "256": 256})

    def test_gate_matrix(self):
        for r in D["platform_gates_matrix"]["rows"]:
            self.assertTrue(r["baseline_supported"])
            self.assertTrue(r["player_current_state_irrelevant"])
            self.assertTrue(r["player_floor_flag_irrelevant"])
            self.assertTrue(r["player_d503_bit6_set"])           # the platform's +$03 bit 7 bypasses the player's bit-6 gate
            self.assertFalse(r["platform_f3_bit6_set"])


class TestPlatformEmulated(unittest.TestCase):
    def test_rising_lift_landing(self):
        e = D["platform_emulated"]["land_on_rising_lift"]
        self.assertEqual(e["player_y_minus_platform_y_after_claim"], -14)
        self.assertEqual(e["landed_update_f3_clear"], e["support_claim_update"] + 1)
        self.assertEqual(len(e["vy_retained_while_standing"]), 1)

    def test_ride_through_reversal(self):
        e = D["platform_emulated"]["ride_through_reversal"]
        self.assertTrue(e["support_continuous"])
        self.assertEqual(e["offsets_player_minus_platform"], [-14])

    def test_retained_zero_vy_loses_support_at_reversal(self):
        e = D["platform_emulated"]["supported_with_retained_vy_zero"]
        self.assertEqual(e["platform_vy_at_loss"], 256)

    def test_step_off(self):
        right, left = D["platform_emulated"]["step_off_right"], D["platform_emulated"]["step_off_left"]
        self.assertEqual(right["dx_at_last_supported"], 22)
        self.assertEqual(left["dx_at_last_supported"], -21)

    def test_sag_cycle(self):
        sag = D["platform_emulated"]["sag_while_standing"]["platform_y_offset_by_update"]
        i = sag.index(1)
        self.assertEqual(sag[i:i + 17], [1, 2, 3, 4, 5, 6, 7, 8, 8, 7, 6, 5, 4, 3, 2, 1, 0])

    def test_no_side_or_underside_collision(self):
        pe = D["platform_emulated"]
        self.assertFalse(pe["rising_through_from_below"]["support_ever_claimed"])
        self.assertFalse(pe["rising_through_from_below_not_attacking"]["support_ever_claimed"])
        self.assertFalse(pe["through_from_the_side_at_platform_height"]["support_ever_claimed"])
        f = D["contact_flags_after_merge"]["platform_state5"]["walker"]
        self.assertFalse(f["right_side"]["wall_left_bit3"] or f["right_side"]["wall_right_bit2"])
        self.assertFalse(f["left_side"]["wall_left_bit3"] or f["left_side"]["wall_right_bit2"])

    def test_horizontal_mode_carries_x(self):
        rows = D["platform_horizontal_mode_carry"]["rows_[update,platform_dx,player_dx,player_dy,player_vx,d3c0,carry_delta_+23]"]
        for r in rows:
            self.assertEqual(r[1], r[2])
            self.assertEqual(r[3], -14)
            self.assertEqual(r[4], 0)

    def test_update_order(self):
        order = D["update_order"]["standing_on_rising_lift"]
        self.assertLess(order.index("player_callback_0395"), order.index("object_28_callback_86DA"))
        i = order.index("object_28_callback_86DA")
        self.assertEqual(order[i + 1:i + 5], ["object_move", "platform_support", "overlap_6328", "platform_carry"])
        self.assertLess(order.index("terrain_pass"), order.index("damage_gate"))


class TestStaticSpikes(unittest.TestCase):
    def test_blocks(self):
        b = D["static_spike_terrain"]["blocks"]
        for k in ("0x3C", "0x3D"):
            self.assertEqual(b[k]["flags"], "0x85")
            self.assertEqual(b[k]["terrain_type_low5"], 5)
            self.assertEqual(b[k]["vertical_profile_value"], 16)
            self.assertEqual(b[k]["horizontal_profile_by_y_runs"], [[0, 15, "0x40"], [16, 31, "0x60"]])
        c = D["static_spike_terrain"]["layout_census_of_damaging_tile_ids"]
        self.assertEqual({a: (c[a]["0x3C"], c[a]["0x3D"]) for a in c}, {"thz1": (0, 4), "thz2": (2, 3), "thz3": (0, 0)})
        for a in c:
            for t in ("0x3E", "0x3F", "0xF4", "0xF5"):
                self.assertEqual(c[a][t], 0)

    def test_probe_geometry(self):
        p = D["terrain_probe_geometry"]["probes"]
        self.assertEqual(p["floor"]["effective_probe_relative_to_anchor"], [0, 18])
        self.assertEqual(p["right_side"]["effective_probe_relative_to_anchor"], [9, 6])
        self.assertEqual(p["left_side"]["effective_probe_relative_to_anchor"], [-9, 6])

    def test_foot_sweep_rules(self):
        r = D["terrain_foot_sweep"]["results"]
        box = [[1504, 1567, 832, 863]]
        low = [[1504, 1567, 848, 863]]
        for prev in ("none_00", "solid_81", "spike_85"):
            for vy in ("rising_-1.0", "zero", "descending_+1.0", "fast_+7.0"):
                self.assertEqual(r[f"prev_{prev}|floor_1|vy_{vy}"]["damaging_cells_[x0,x1,foot_row_y0,y1]"], box)       # grounded: any foot row of the cell
        for vy in ("zero", "descending_+1.0", "fast_+7.0"):
            self.assertEqual(r[f"prev_solid_81|floor_0|vy_{vy}"]["damaging_cells_[x0,x1,foot_row_y0,y1]"], low)       # airborne: rows 16..31 only
            self.assertEqual(r[f"prev_spike_85|floor_0|vy_{vy}"]["damaging_cells_[x0,x1,foot_row_y0,y1]"], low)
            self.assertEqual(r[f"prev_none_00|floor_0|vy_{vy}"]["count"], 0)                                           # first sample after air: no damage
        for prev in ("none_00", "solid_81", "spike_85"):
            self.assertEqual(r[f"prev_{prev}|floor_0|vy_rising_-1.0"]["count"], 0)

    def test_no_side_or_ceiling_damage(self):
        s = D["terrain_side_ceiling_sweep"]
        self.assertEqual(s["side_probe_damage_cases"], 0)
        self.assertEqual(s["ceiling_probe_damage_cases"], 0)
        self.assertEqual(s["ceiling_probe_changes_y_cells"], 0)
        self.assertEqual(s["requested_state_gate"]["states_without_side_push"], ["0x1E"])

    def test_rising_band(self):
        b = D["static_spike_rising_band"]["by_vertical_speed"]
        self.assertEqual(b["rising_-1.0"]["foot_in_solid_rows_undamaged_unpushed_anchor_y"], [[830, 841]])
        self.assertEqual(b["rising_-1.0"]["pushed_by_wall_anchor_y"], [[842, 851]])
        self.assertEqual(b["level_0"]["damaged_anchor_y"], [[830, 845]])
        self.assertEqual(b["descending_+1.0"]["damaged_anchor_y"], [[830, 845]])

    def test_diagonal_sweep_has_no_descending_phase_through_from_outside(self):
        c = D["static_spike_diagonal_sweep"]["counts"]
        self.assertGreater(D["static_spike_diagonal_sweep"]["runs"], 1000)
        outside = {k: v for k, v in c.items() if k.startswith(("from_left", "from_right", "ground_"))}
        self.assertFalse([k for k in outside if "E2_" in k or "X_" in k])
        self.assertTrue([k for k in c if "A_damaged" in k])
        self.assertTrue([k for k in c if "B_stopped_by_wall" in k])
        self.assertEqual(sum(v for k, v in c.items() if k.startswith("ground_") and "A_damaged" in k), 0)    # a grounded approach meets the wall first

    def test_hurt_chain_aftermath(self):
        a = D["static_spike_aftermath"]
        self.assertEqual(a["with_5_rings"]["updates_with_plus3_bit7"], 120)
        self.assertEqual(a["with_5_rings"]["hurt_entry_calls_in_200_updates"], 2)           # damaged again when the invulnerability ends
        self.assertEqual(a["no_rings"]["hurt_entry_calls_in_200_updates"], 1)


class TestPlatformVersusSpike(unittest.TestCase):
    def test_terrain_pass_precedes_platform_contact(self):
        rows = {r["platform_y"]: r for r in D["platform_vs_spike_terrain"]["rows"]}
        self.assertIsNone(rows[830]["terrain_spike_hurt_update"])
        self.assertIsNotNone(rows[830]["support_claim_update"])
        for y in (845, 850, 856, 862):
            self.assertIsNotNone(rows[y]["terrain_spike_hurt_update"])
            self.assertIsNone(rows[y]["support_claim_update"])


class TestMovingSpike(unittest.TestCase):
    def test_cycle(self):
        t = D["spike_1b_timeline"]
        self.assertEqual(t["cycle_updates"], 102)
        self.assertEqual(t["cycle_runs_[state,updates,y_first,y_last]"], [[4, 48, 864, 864], [1, 3, 858, 846], [2, 48, 846, 846], [3, 3, 852, 864]])
        self.assertEqual(t["contact_tested_in_states"], [1, 2])

    def test_contact_sweep(self):
        s = D["spike_1b_contact_sweep"]
        self.assertEqual(s["mismatches"], 0)
        self.assertEqual(s["cases"], 89304)
        region = s["damage_region_dx_range_by_dy_relative_to_object_anchor"]["2"]
        self.assertEqual(sorted(int(k) for k in region), list(range(-24, 0)))
        for dy, (lo, hi) in region.items():
            self.assertEqual((lo, hi), (-min(24, -int(dy)), min(24, -int(dy))))

    def test_gates(self):
        g = D["spike_1b_gates"]["gates"]
        self.assertTrue(g["baseline"]["damage_request"])
        self.assertEqual(g["baseline"]["player_vy_after"], -1024)
        self.assertEqual(g["baseline"]["cooldown_after"], 16)
        for k in ("cooldown_16", "cooldown_1", "object_inactive_f4_bit6", "player_rising_vy_-1"):
            self.assertFalse(g[k]["damage_request"], k)
        self.assertTrue(g["player_vy_0"]["damage_request"])
        self.assertTrue(g["player_invulnerable_d503_bit7"]["damage_request"])      # the object writes the request; $48BC ignores it
        st = D["spike_1b_gates"]["by_object_state"]
        self.assertEqual({k: v["damage_request"] for k, v in st.items()}, {"1": True, "2": True, "3": False, "4": False})

    def test_test_before_move(self):
        m = D["spike_1b_move_before_contact"]
        self.assertEqual(m["player_y_minus_864_with_damage_request"], [[-24, -1]])
        self.assertEqual(m["object_y_after_callback"], 858)

    def test_side_contact_is_a_wall_for_non_attacking_player(self):
        f = D["contact_flags_after_merge"]["spike_1b_state2"]
        self.assertTrue(f["walker"]["left_side"]["wall_right_bit2"])
        self.assertTrue(f["walker"]["right_side"]["wall_left_bit3"])
        self.assertFalse(f["attacking"]["left_side"]["wall_right_bit2"])

    def test_emulated_request_is_consumed_next_update(self):
        e = D["spike_1b_emulated"]["fall_onto_raised_spike"]
        self.assertEqual(e["hurt_entry_update"], e["damage_request_visible_after_update"] + 1)
        self.assertEqual(D["spike_1b_emulated"]["fall_onto_raised_spike_while_invulnerable"]["hurt_entry_calls"], 0)
        self.assertEqual(D["spike_1b_emulated"]["walk_into_side"]["hurt_entry_calls"], 0)
        self.assertEqual(D["spike_1b_emulated"]["roll_into_side"]["hurt_entry_calls"], 0)


class TestDamage(unittest.TestCase):
    def test_hurt_consequences(self):
        r = D["hurt_consequences"]["rows"]
        self.assertEqual((r["rings_0_death"]["requested_state"], r["rings_0_death"]["vy"]), ("0x1F", -1280))
        for k in ("rings_1", "rings_100", "rings_255"):
            self.assertEqual((r[k]["requested_state"], r[k]["vx"], r[k]["vy"], r[k]["invulnerability_timer_d3b1"], r[k]["rings_after"]), ("0x1E", -256, -1024, 120, 0))
        self.assertEqual(r["rings_5_left_wall_bit3_in_d523"]["vx"], 256)
        self.assertEqual(r["rings_5_ceiling_contact_d522_bit0"]["vy"], 256)
        self.assertEqual([r[f"rings_{n}"]["scatter_objects_type_06"] for n in (1, 15, 16, 32, 64, 100)], [1, 1, 2, 3, 5, 7])

    def test_invulnerability(self):
        self.assertEqual(D["invulnerability_countdown"]["damage_gate_updates_until_bits_clear"], 121)

    def test_gate_matrix(self):
        rows = D["damage_gate_48bc"]["rows"]

        def reach(f3, sel, req, contact):
            return next(r["reaches"] for r in rows if (r["d503_ie_plus3"], r["d532"], r["request_d3b0"], r["contact_d520"]) == (f3, sel, req, contact))
        self.assertEqual(reach("0x00", 0, "0xFF", 0), "hurt_48f7")
        self.assertEqual(reach("0x80", 0, "0xFF", 0), "invulnerability_tick_49f7")
        self.assertEqual(reach("0x40", 0, "0xFF", 0), "bit6_ignore_4a2e")
        self.assertEqual(reach("0x00", 6, "0xFF", 0), "return_without_hurt")


class TestOneWayTerrain(unittest.TestCase):
    def test_rows(self):
        r = D["terrain_one_way_platform"]["results"]
        self.assertEqual(r["prev_oneway_41|floor_0|vy_zero"]["projected_foot_rows_relative_to_cell_top"], [[1, 8]])
        self.assertEqual(r["prev_oneway_41|floor_0|vy_+7.0"]["projected_foot_rows_relative_to_cell_top"], [[1, 15]])
        self.assertEqual(r["prev_oneway_41|floor_0|vy_rising_-1.0"]["projected_foot_rows_relative_to_cell_top"], [])
        self.assertEqual((D["terrain_one_way_platform"]["side_pushes"], D["terrain_one_way_platform"]["ceiling_pushes_on_rising_player"]), (0, 0))


@unittest.skipIf(ROM is None, "matching ROM not found (set SONIC_CHAOS_ROM)")
class TestRomBacked(unittest.TestCase):
    def test_routine_bytes(self):
        self.assertEqual(tool.routine_table(ROM), D["routines"])

    def test_static_sections_regenerate(self):
        s = tool.build(ROM, static_only=True)
        for k, v in s.items():
            if k != "static_only":
                self.assertEqual(v, D[k], k)

    def test_platform_support_regenerates(self):
        got = tool.platform_support(ROM)
        self.assertEqual(got, D["platform_support"])

    def test_gate_regenerates(self):
        self.assertEqual(tool.platform_gate(ROM), D["platform_gate_8866"])

    def test_spike_sweeps_regenerate(self):
        self.assertEqual(tool.spike_contact_sweep(ROM), D["spike_1b_contact_sweep"])
        self.assertEqual(tool.spike_timeline(ROM), D["spike_1b_timeline"])
        self.assertEqual(tool.spike_helper_gates(ROM), D["spike_1b_gates"])

    def test_terrain_sweeps_regenerate(self):
        self.assertEqual(tool.terrain_foot_sweep(ROM), D["terrain_foot_sweep"])
        self.assertEqual(tool.terrain_side_ceiling_sweep(ROM), D["terrain_side_ceiling_sweep"])
        self.assertEqual(tool.rising_pass_band(ROM), D["static_spike_rising_band"])
        self.assertEqual(tool.terrain_one_way_sweep(ROM), D["terrain_one_way_platform"])

    def test_damage_regenerates(self):
        self.assertEqual(tool.damage_gate_matrix(ROM), D["damage_gate_48bc"])
        self.assertEqual(tool.hurt_consequences(ROM), D["hurt_consequences"])
        self.assertEqual(tool.invulnerability_countdown(ROM), D["invulnerability_countdown"])

    def test_emulated_platform_regenerates(self):
        self.assertEqual(json.loads(json.dumps(tool.emulated_platform(ROM))), D["platform_emulated"])
        self.assertEqual(json.loads(json.dumps(tool.emulated_update_order(ROM))), D["update_order"])


if __name__ == "__main__":
    unittest.main()

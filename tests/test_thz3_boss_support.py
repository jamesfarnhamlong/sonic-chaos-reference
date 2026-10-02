#!/usr/bin/env python3
"""THZ3 boss/support audit and $1B/$28 closure: cache-driven tests (no ROM) plus ROM-backed re-execution of selected sections.

Full regeneration: `python tools/thz3_boss_support.py ROM --check` (several minutes). The ROM-backed classes run when a matching ROM is
found (set SONIC_CHAOS_ROM) and skip otherwise.
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
D = json.loads((ROOT / "data/rom-cache/thz3-boss-support.json").read_text(encoding="utf-8"))
M = json.loads((ROOT / "data/rom-cache/thz3/implementation-manifest.json").read_text(encoding="utf-8"))
A, B = D["part_a"], D["part_b"]

spec = importlib.util.spec_from_file_location("thz3_boss_support", ROOT / "tools" / "thz3_boss_support.py")
tool = importlib.util.module_from_spec(spec)
sys.modules["thz3_boss_support"] = tool
spec.loader.exec_module(tool)


def matching_rom():
    cands = []
    if os.environ.get("SONIC_CHAOS_ROM"):
        cands.append(Path(os.environ["SONIC_CHAOS_ROM"]))
    cands += [ROOT.parent / "Sonic Chaos (Europe).sms", ROOT.parent / "source" / "Sonic Chaos (Europe).sms"]
    for p in cands:
        if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == ROM_SHA:
            return p.read_bytes()
    return None


ROM = matching_rom()


def rt(x):
    return json.loads(json.dumps(x))


class TestIdentity(unittest.TestCase):
    def test_flags(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertTrue(D["research_only"] and D["poc_untouched"])
        self.assertEqual(M["rom_sha256"], ROM_SHA)

    def test_counts(self):
        self.assertGreater(D["counts"]["controlled_cases_total"], 70000)


class TestA1Cooldown(unittest.TestCase):
    def test_cooldown_disables_helper_entirely(self):
        s = A["a1_cooldown_side_wall"]["cooldown_positive_summary"]
        self.assertFalse(s["helper_ran_any"] or s["any_d521_contact"] or s["any_wall"] or s["any_push"] or s["any_damage_or_bounce"])

    def test_active_rows(self):
        s = A["a1_cooldown_side_wall"]["cooldown_zero_summary"]
        self.assertTrue(s["helper_ran_all"])
        self.assertEqual({tuple(r[:2]) for r in s["contact_rows_with_push"]},
                         {("side_right", "attacker_grounded"), ("side_left", "attacker_grounded"), ("below_vertical_dominated", "attacker_grounded")})
        self.assertEqual([r[2] for r in s["contact_rows_with_push"]], [23, -23, -23])

    def test_sixteen_inactive_updates(self):
        for k, v in A["a1_cooldown_side_wall"]["sequence_summary"].items():
            self.assertEqual(v["inactive_updates"], list(range(1, 17)), k)
            self.assertEqual(v["first_active_update_after_damage"], 17)
            self.assertEqual(v["first_wall_or_push_update"], 17)

    def test_decrement_scope(self):
        sc = A["a1_cooldown_side_wall"]["cooldown_decrement_scope"]
        self.assertEqual([sc[k]["cooldown_after_one_callback"] for k in "1234"], [15, 15, 16, 16])
        self.assertEqual(sc["state2_inactive_bit6"]["cooldown_after_one_callback"], 16)

    def test_remainder_carries_across_hidden_phase(self):
        runs = A["a1_cooldown_side_wall"]["cooldown_across_cycle"][1]["runs_[state,updates,y,cooldown]"]
        hidden = [r for r in runs if r[0] == 4]
        self.assertEqual(hidden[0][3], 12)


class TestA2Push(unittest.TestCase):
    def test_model_equal(self):
        self.assertEqual(A["a2_grounded_push"]["mismatches_vs_model"], 0)
        self.assertGreater(A["a2_grounded_push"]["cases"], 14000)

    def test_independence(self):
        self.assertEqual(A["a2_grounded_push"]["independence"]["mismatches"], 0)

    def test_gates(self):
        g = A["a2_grounded_push"]["posture_gates"]
        self.assertEqual(g["grounded_attacker"]["push_x"], 23)
        self.assertEqual(g["grounded_attacker_below"]["push_x"], -23)
        for k in ("grounded_walker", "airborne_attacker", "airborne_walker"):
            self.assertIsNone(g[k]["push_x"])

    def test_model_function(self):
        self.assertEqual(tool.model_push(3, 10), -23)       # below, vertical dominated, dx > 0
        self.assertEqual(tool.model_push(11, 10), 23)       # horizontal dominated
        self.assertEqual(tool.model_push(1, 0), 23)
        self.assertEqual(tool.model_push(0, 0), -23)
        self.assertIsNone(tool.model_push(0, -12))


class TestA3Lifecycle(unittest.TestCase):
    def test_lift_phase_depends_on_arrival(self):
        arr = A["a3_lifecycle"]["lift_28"]["arrival_dependence"]
        self.assertEqual(len({a["y_100_updates_after_creation"] for a in arr if a["approach"].startswith("from_left")}), 1)
        self.assertGreater(len({a["y_at_absolute_update_330"] for a in arr}), 2)

    def test_lift_keep_alive_radius(self):
        for r in A["a3_lifecycle"]["lift_28"]["keep_alive_player_distance"]:
            if abs(r["player_dx_while_away"]) < 640:
                self.assertTrue(r["continuous_with_free_run"])
                self.assertEqual(r["updates_alive_while_away"], r["away_updates"])
            else:
                self.assertEqual(r["updates_alive_while_away"], 0)

    def test_lift_moves_asleep(self):
        rows = A["a3_lifecycle"]["lift_28"]["asleep_motion"]["first_rows_[Y,state,+04]"]
        self.assertEqual(rows[0], [464, 0, 64])
        self.assertEqual(rows[2], [463, 11, 66])
        self.assertTrue(all(r[2] & 0x40 for r in rows))

    def test_spike_starts_at_wake(self):
        for c in A["a3_lifecycle"]["spike_1b"]["creation_and_wake"]:
            ev = c["events_since_creation"]
            self.assertEqual(ev[0][1]["state"], 0)
            self.assertTrue(ev[1][1]["asleep_bit6"] and ev[1][1]["state"] == 1)
            self.assertFalse(ev[2][1]["asleep_bit6"])
            self.assertEqual(ev[3][1]["state"], 2)

    def test_spike_deleted_and_restarted(self):
        ev = A["a3_lifecycle"]["spike_1b"]["deletion_and_recreation_events_[update,row]"]
        self.assertTrue(any(e[1] is None for e in ev))
        after = [e for e in ev if e[0] > 300]
        self.assertEqual(after[0][1]["state"], 0)


class TestA4Static(unittest.TestCase):
    def test_classes(self):
        t = A["a4_static_spike_aligned"]["class_totals_aligned"]
        self.assertEqual(sum(t.values()) + 60, A["a4_static_spike_aligned"]["runs"])
        self.assertEqual(t["E2"], 4)
        self.assertGreater(t["A_"], 400)

    def test_ten_legacy_rows(self):
        rows = A["a4_static_spike_aligned"]["legacy_ten_cases_replayed"]
        self.assertEqual(len(rows), 10)
        self.assertEqual(sum(1 for r in rows if r["aligned_class"].startswith("E1")), 6)
        self.assertEqual(sum(1 for r in rows if r["aligned_class"].startswith("A_")), 4)
        for r in rows:
            self.assertEqual(r["teleport_initial_state"]["state_d501"], 1)
            self.assertEqual(r["aligned_rows_first_8_updates"][1]["state_d501"], r["teleport_initial_state"]["requested_d502"])


class TestSupportObjects(unittest.TestCase):
    def test_type_12(self):
        t = B["b2_support_objects"]["controlled"]["type_12"]
        self.assertEqual(t["updates_until_type_FF"], 97)
        self.assertEqual(t["initial_sat_y_DB34_DB3F"], [16] * 4 + [32] * 4 + [0] * 4)

    def test_type_34(self):
        t = B["b2_support_objects"]["controlled"]["type_34"]
        self.assertEqual(t["lifetime_by_parameter_and_D12F_bit0"]["D12F_bit0_1"]["4"], 130)
        self.assertEqual(t["lifetime_by_parameter_and_D12F_bit0"]["D12F_bit0_0"]["4"], 250)
        self.assertEqual(list(t["art_base_by_zone_D297"].values()), [0xA2, 0x96, 0x74, 0x6E, 0xB2, 0xB2, 0x88, 0xDD])

    def test_type_0a(self):
        t = B["b2_support_objects"]["controlled"]["type_0a"]
        for r in t["param_0_init"]:
            self.assertEqual(r["D2A6_after_init"], r["routine_041F_HL"])
            self.assertEqual(r["state_after_init"], 2)
        self.assertEqual(t["sparkle_param_FF"]["updates_until_removed"], 28)
        self.assertEqual([s["update"] for s in t["emitter_spawns_first_80_updates"][:3]], [8, 16, 24])

    def test_type_0f(self):
        self.assertEqual(B["b2_support_objects"]["controlled"]["type_0f"]["updates_until_removed"], 38)


class TestArena(unittest.TestCase):
    def test_timeline(self):
        t = B["b3_arena_camera"]["timeline"]
        self.assertEqual(t["state_1_at"], 2)
        self.assertEqual(t["trigger_row"]["right_limit_D282"], t["trigger_row"]["left_limit_D280"])
        self.assertEqual(t["state_3_row"]["pan_target"], [1680, 78])
        self.assertEqual(t["state_3_row"]["bottom_limit_D27E"], 78)
        self.assertEqual(B["b3_arena_camera"]["pan"]["x_end"], 1679)
        self.assertEqual(B["b3_arena_camera"]["pan"]["y_end"], 78)

    def test_trigger_boundary(self):
        self.assertEqual(B["b3_arena_camera"]["trigger_boundaries"]["state_1_trigger"]["mismatches_vs_rule"], 0)
        c = B["b3_arena_camera"]["trigger_boundaries"]["creation_window_steady_scroll_camera_x"]
        self.assertEqual((c["first"], c["last"]), (1585, 1648))

    def test_clamp(self):
        c = B["b3_arena_camera"]["player_clamp"]
        self.assertEqual(c["camera_x"], 1679)
        self.assertEqual((c["min_player_x_running_left"], c["max_player_x_running_right"]), (1694, 1927))

    def test_patrol_range(self):
        self.assertEqual(B["b3_arena_camera"]["final_lock"]["boss_patrol_x_range"], [1726, 1887])


class TestContact(unittest.TestCase):
    def test_grid(self):
        g = B["b4_boss_contact"]
        self.assertEqual(g["mismatches_vs_model"], 0)
        self.assertGreater(g["cases"], 60000)
        self.assertTrue(g["states_6_9_12_15_identical_outcomes"])

    def test_postures(self):
        c = B["b4_boss_contact"]["outcome_counts_by_posture_state_6"]
        for p in ("attacker_ball_grounded", "attacker_jump_airborne", "invincible_pickup_state", "hurt_state_bit6_with_bit1"):
            self.assertEqual(c[p]["hit"], 3320, p)
        for p in ("walker_grounded", "invincible_after_landing_bit1_clear", "invulnerable_blink_non_attacking", "hurt_state_bit6_without_bit1"):
            self.assertEqual(c[p]["player_damage_request"], 3320, p)
        for p in c:
            self.assertEqual(c[p]["top_bounce"], 841)

    def test_effects(self):
        e = B["b4_boss_contact"]["effects"]
        self.assertEqual((e["hit_from_left_side"]["player_vx"], e["hit_from_right_side"]["player_vx"], e["hit_from_below"]["player_vy"]), (-1536, 1536, 1536))
        self.assertEqual(e["top_bounce"]["player_vy"], -1024)
        self.assertEqual(e["final_hit"]["requested"], 4)
        self.assertEqual(e["plain_side_contact"]["cooldown_1E"], 2)


class TestDefeat(unittest.TestCase):
    def test_hits(self):
        f = B["b6_defeat_act_clear"]["fight"]
        self.assertEqual(f["hit_intervals"], [22] * 7)
        self.assertEqual(f["state_4_to_conversion_updates"], 148)
        self.assertEqual([c["dx"] for c in f["child_offsets_from_boss_anchor"]], [-8, 8, 0, -8, -8])

    def test_clear(self):
        f = B["b6_defeat_act_clear"]["fight"]
        self.assertIn(f["act_clear_flag_set_frames_after_conversion"], range(175, 195))
        self.assertGreater(f["player_and_camera_at_flag"]["difference"], 0x120)
        self.assertEqual(f["next_zone_act"], [1, 0])
        self.assertEqual(f["timer_run_flag_D2BE_values_seen"], [255])

    def test_score_decomposition(self):
        for r in B["b6_defeat_act_clear"]["variants"]["rows"]:
            if r["variant"].endswith("held_after_defeat"):
                continue
            self.assertEqual(r["score_after"], r["rings_decimal"] * 10 + r["d2a6_steps"] + 500, r["variant"])

    def test_input_lock(self):
        v = {r["variant"]: r for r in B["b6_defeat_act_clear"]["variants"]["rows"]}
        a, b = v["rings_47"], v["rings_47_buttons_held_after_defeat"]
        self.assertEqual(a["player_and_camera_at_flag"], b["player_and_camera_at_flag"])
        self.assertEqual(a["flag_after_conversion_frames"], b["flag_after_conversion_frames"])


class TestManifest(unittest.TestCase):
    def test_shape(self):
        self.assertEqual(len(M["placements"]), 10)
        self.assertEqual(M["boss"]["hit_points"], 8)
        self.assertEqual(M["boss"]["vulnerable_states"], [6, 9, 12, 15])
        self.assertEqual(len(M["boss"]["states"]), 19)
        self.assertGreater(len(M["boss"]["contact_fixtures"]), 100)

    def test_assets_no_invention(self):
        self.assertTrue(all("status" in a for a in M["assets"]))


@unittest.skipUnless(ROM, "matching ROM not found")
class TestRomBacked(unittest.TestCase):
    def test_a1(self):
        self.assertEqual(rt(tool.a1_cooldown_side_wall(ROM)), A["a1_cooldown_side_wall"])

    def test_a2(self):
        self.assertEqual(rt(tool.a2_grounded_push(ROM)), A["a2_grounded_push"])

    def test_support_controlled(self):
        self.assertEqual(rt(tool.support_controlled(ROM)), B["b2_support_objects"]["controlled"])
        self.assertEqual(rt(tool.support_static(ROM)), B["b2_support_objects"]["static"])

    def test_trigger(self):
        self.assertEqual(rt(tool.trigger_boundaries(ROM)), B["b3_arena_camera"]["trigger_boundaries"])

    def test_contact_grid(self):
        g = tool.boss_contact_grid(ROM)
        g["manifest_fixtures"] = B["b4_boss_contact"]["manifest_fixtures"]
        self.assertEqual(rt(g), B["b4_boss_contact"])

    def test_arena_and_chain(self):
        arena = tool.arena_camera(ROM)
        stored = {k: v for k, v in B["b3_arena_camera"].items() if k not in ("trigger_boundaries", "constants")}
        self.assertEqual(rt(arena), stored)
        self.assertEqual(rt(tool.defeat_chain(ROM)), B["b6_defeat_act_clear"]["fight"])

    def test_lifecycle_and_static_spike(self):
        self.assertEqual(rt(tool.a3_lifecycle(ROM)), A["a3_lifecycle"])

    def test_aligned_replay_deterministic(self):
        rows = tool.a4_static_spike_aligned(ROM)["legacy_ten_cases_replayed"]
        self.assertEqual(rt(rows), A["a4_static_spike_aligned"]["legacy_ten_cases_replayed"])


if __name__ == "__main__":
    unittest.main()

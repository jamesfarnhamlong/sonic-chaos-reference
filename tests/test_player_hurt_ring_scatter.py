#!/usr/bin/env python3
"""Player hurt / lost-ring scatter audit: cache-driven tests (no ROM) plus ROM-backed re-execution.

Regenerating everything from the ROM: `python tools/player_hurt_ring_scatter.py ROM --check` or `tests/verify_cache.py ROM`.
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
CACHE = ROOT / "data" / "rom-cache" / "player-hurt-ring-scatter.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("player_hurt_ring_scatter", ROOT / "tools" / "player_hurt_ring_scatter.py")
tool = importlib.util.module_from_spec(spec)
sys.modules["player_hurt_ring_scatter"] = tool
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
CELLS = bytes(int(c) for row in D["lifetime_window"]["cell_table"] for c in row)
FLOOR = {(c, 20): 1 for c in range(10, 60)}
HDR = [0] * 256
HDR[1], HDR[0x0D], HDR[0x40] = 0x81, 0x41, 0x07


class TestCache(unittest.TestCase):
    def test_rom_identity_and_scope(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertEqual(D["format"], 1)
        names = {r["name"] for r in D["routines"]}
        for n in ("hurt_entry", "object_allocator", "ring_init_9A2B", "ring_state1_9A98", "lifetime_61E1", "ring_counter_3138"):
            self.assertIn(n, names)
        for r in D["routines"]:
            self.assertEqual(len(r["sha256"]), 64)
            self.assertGreater(r["length"], 0)

    def test_every_audit_question_has_a_section(self):
        for key in ("emission", "object", "pool", "lockout_pickup", "flat_floor", "ceiling_and_oneway", "lifetime_window", "water",
                    "second_hurt", "invulnerability_blink", "gpz3_boss_example", "poc_divergence", "agents_candidate_updates", "shared_counter_path"):
            self.assertIn(key, D)


class TestEmission(unittest.TestCase):
    def test_count_rule_is_bcd_tens_plus_one_capped_at_7(self):
        rows = D["emission"]["rows"]
        self.assertEqual(len(rows), 100)
        for rings in range(100):
            expect = 0 if rings == 0 else min(7, rings // 10 + 1)
            self.assertEqual(rows[str(rings)]["objects"], expect, rings)
            self.assertEqual(rows[str(rings)]["player_state"], 0x1F if rings == 0 else 0x1E)
            self.assertEqual(rows[str(rings)]["rings_after"], 0)
        self.assertEqual(D["emission"]["mismatches_vs_model"], 0)

    def test_ranges(self):
        self.assertEqual(D["emission"]["decimal_range_per_object_count"],
                         {"0": [0, 0], "1": [1, 9], "2": [10, 19], "3": [20, 29], "4": [30, 39], "5": [40, 49], "6": [50, 59], "7": [60, 99]})

    def test_bcd_correction_of_the_previous_binary_table(self):
        c = D["emission"]["correction_of_previous_table"]["corrected"]
        self.assertEqual((c["15"], c["32"], c["64"]), (2, 4, 7))
        self.assertEqual(tool.ring_count_for(0x15), 2)
        self.assertEqual(tool.ring_count_for(0x32), 4)
        self.assertEqual(tool.ring_count_for(0x64), 7)
        self.assertEqual(tool.ring_count_for(0), 0)

    def test_hurt_consequences(self):
        r = D["hurt_rows"]["rows"]
        self.assertEqual((r["rings_47"]["requested_state"], r["rings_47"]["scatter_objects"], r["rings_47"]["sound"]), ("0x1E", 5, "0xA4"))
        self.assertEqual((r["rings_47"]["vx"], r["rings_47"]["vy"], r["rings_47"]["invulnerability_timer"], r["rings_47"]["player_flags_d503"]), (-256, -1024, 120, "0xC1"))
        self.assertEqual((r["rings_0_death"]["requested_state"], r["rings_0_death"]["scatter_objects"]), ("0x1F", 0))
        self.assertEqual(r["rings_47_state_11"]["scatter_objects"], 0)
        self.assertEqual(r["rings_47_state_11"]["rings_after"], "0x47")
        self.assertEqual((r["rings_47_left_wall_d523_bit3"]["vx"], r["rings_47_ceiling_d522_bit0"]["vy"]), (256, 256))


class TestObject(unittest.TestCase):
    def test_velocity_tables(self):
        vt = D["object"]["velocity_tables"]
        self.assertEqual(vt["x_8_8"], [0, -320, 320, -640, 640, -832, 832])
        self.assertEqual(vt["y_8_8"], [-1280, -1184, -1184, -896, -896, -512, -512])
        self.assertEqual(vt["x_px_per_update"], [0, -1.25, 1.25, -2.5, 2.5, -3.25, 3.25])
        self.assertEqual(vt["y_px_per_update"], [-5.0, -4.625, -4.625, -3.5, -3.5, -2.0, -2.0])

    def test_scripts(self):
        o = D["object"]
        s1 = [r for r in o["state_1_motion"]["script"] if "duration" in r]
        self.assertEqual([r["frame"] for r in s1], [1, 2, 4, 3, 1, 2, 4, 3])
        self.assertEqual([r["callback"] for r in s1], ["0x9A9E"] * 4 + ["0x9A98"] * 4)
        self.assertTrue(all(r["duration"] == 4 for r in s1))
        self.assertEqual(o["state_1_motion"]["script"][-1], {"command": "jump", "to": "0x9A17"})
        s2 = [r for r in o["state_2_sparkle"]["script"] if "duration" in r]
        self.assertEqual(len(s2), 8)
        self.assertEqual([r["frame"] for r in s2], [5, 6] * 4)
        self.assertEqual(s2[-1]["callback"], "0x034A")
        self.assertEqual(sum(r["duration"] for r in s2), 32)
        self.assertEqual(o["init_constants"]["bounce_speed"], -1024)
        self.assertEqual(o["init_constants"]["gravity_per_update"], 32)

    def test_pool_rules(self):
        cases = {c["case"]: c for c in D["pool"]["cases"]}
        self.assertEqual(cases["empty pool, 99 rings"]["scatter_slot_token"], [[k, k] for k in range(7)])
        self.assertEqual(cases["slots 0-13 occupied (two free in the first 16)"]["scatter_slot_token"], [[14, 0], [15, 1]])
        self.assertEqual(cases["slots 0-15 occupied, 16-18 free"]["scatter_slot_token"], [])
        self.assertEqual(cases["slots 0-15 occupied, 16-18 free"]["player_requested_state"], "0x1E")      # the hurt still happens
        self.assertEqual(cases["slots 0-15 occupied, 16-18 free"]["rings_after"], "0x00")
        self.assertEqual(cases["slot 0 pending clear ($FF) is not reusable"]["scatter_slot_token"][0], [1, 0])


class TestPickup(unittest.TestCase):
    def test_lockout_is_exactly_16_updates(self):
        self.assertEqual(set(D["lockout_pickup"]["first_pickup_update_by_index"].values()), {tool.LOCKOUT_UPDATES + 1})

    def test_box(self):
        b = D["lockout_pickup"]["pickup_box"]
        self.assertEqual(b["mismatches_vs_abs_dx_dy_le_11"], 0)
        for dy in range(-14, 15):
            row = b["hit_rows_dx_-14_to_14_by_dy"][str(dy)]
            expect = ("." * 3 + "#" * 23 + "." * 3) if abs(dy) <= 11 else "." * 29
            self.assertEqual(row, expect, dy)

    def test_no_player_state_condition(self):
        s = D["lockout_pickup"]["player_state_independence"]
        self.assertTrue(s["all_collect"])
        self.assertEqual(s["cases"], 90)

    def test_effects(self):
        rows = D["lockout_pickup"]["pickup_effects"]["rows"]
        self.assertEqual([r["rings_after"] for r in rows], ["0x01", "0x10", "0x20", "0x99", "0x00", "0x00"])
        self.assertEqual([r["sound_after"] for r in rows], ["0xBF"] * 4 + ["0xA9"] * 2)
        self.assertEqual([r["lives_after"] for r in rows], ["0x03", "0x03", "0x03", "0x03", "0x04", "0x99"])
        self.assertEqual(tool.bcd_inc(0x09), (0x10, False))
        self.assertEqual(tool.bcd_inc(0x99), (0x00, True))

    def test_sparkle_timeline(self):
        rows = D["lockout_pickup"]["sparkle_timeline"]["rows"]
        by = {r[0]: r for r in rows}
        self.assertEqual([by[n][3] for n in (1, 4, 5, 8, 9, 12, 13, 16, 17, 20, 21, 24, 25, 28)], [5, 5, 6, 6, 5, 5, 6, 6, 5, 5, 6, 6, 5, 5])
        self.assertEqual((by[28][1], by[29][1], by[30][1], by[31][1]), (6, 0xFE, 0xFF, 0))
        self.assertEqual({(r[4], r[5]) for r in rows if r[1]}, {(rows[0][4], rows[0][5])})           # frozen


class TestMotion(unittest.TestCase):
    def test_flat_floor_series(self):
        ab = D["flat_floor"]["player_absent"]["per_ring"]
        self.assertEqual(ab["0"]["bounce_updates"], [83, 137, 184, 223, 254, 276, 291])
        self.assertEqual(ab["0"]["end_event"], ["bounce_exhausted", 298])
        self.assertEqual(D["flat_floor"]["bounce_speed_sequence_8_8"], [-896, -768, -640, -512, -384, -256, -128])
        pr = D["flat_floor"]["player_stands_still_at_spawn_point"]["per_ring"]
        self.assertEqual(pr["0"]["end_event"], ["pickup", 81])

    def test_ceiling_and_one_way(self):
        rows = {r["block"]: r["ring_turns_around"] for r in D["ceiling_and_oneway"]["rows"]}
        self.assertEqual(rows["solid $01 (flags $81)"]["update"], 8)
        for k in ("one-way $0D (flags $41)", "ring block $40 (flags $07)", "air $00"):
            self.assertEqual(rows[k]["update"], 41)          # apex of the free flight: not stopped by the cell

    def test_model_flat_floor(self):
        world = tool.World(HDR)
        world.cells = dict(FLOOR)
        vx = D["object"]["velocity_tables"]["x_8_8"]
        vy = D["object"]["velocity_tables"]["y_8_8"]
        m = tool.RingModel(0, 1000, 622, vx, vy)
        hud = {"pickups": 0}
        for _ in range(400):
            m.update(world, CELLS, (872, 526), (6000, 600), hud)
        self.assertEqual(m.bounces, [83, 137, 184, 223, 254, 276, 291])
        self.assertFalse(m.alive)
        self.assertEqual(hud["pickups"], 0)

    def test_model_gravity_and_first_updates(self):
        vx = D["object"]["velocity_tables"]["x_8_8"]
        vy = D["object"]["velocity_tables"]["y_8_8"]
        world = tool.World(HDR)
        m = tool.RingModel(3, 1000, 622, vx, vy)
        m.update(world, CELLS, (872, 526), (6000, 600), {"pickups": 0})
        self.assertEqual((m.x, m.y, m.req), (1000, 606, 1))                    # init update: spawn at (playerX, playerY - 16)
        m.update(world, CELLS, (872, 526), (6000, 600), {"pickups": 0})
        self.assertEqual((m.x, m.y), (997, 602))                                # vy -3.5 + 0.125, vx -2.5: matches the controlled run
        self.assertEqual(tool.s16(m.vy), -864)

    def test_probe_rules(self):
        self.assertTrue(tool.floor_flags(0x81) and tool.floor_flags(0x41) and not tool.floor_flags(0x07) and not tool.floor_flags(0))
        self.assertTrue(tool.ceiling_flags(0x81) and not tool.ceiling_flags(0x41) and not tool.ceiling_flags(0x07))
        w = tool.World(HDR)
        w.cells = {(31, 20): 1}
        self.assertEqual(w.probe_flags(1000, 622, 0), 0x81)                      # y + 0 + 18 = 640 -> row 20, x 1000 -> column 31
        self.assertEqual(w.probe_flags(1000, 621, 0), 0)
        self.assertEqual(w.probe_flags(-5, 622, 0), 0)                           # outside the map -> block $FF -> flags 0
        self.assertEqual(w.probe_flags(1000, 0xFFF0, 0), 0)

    def test_pickup_box_in_model(self):
        vx = D["object"]["velocity_tables"]["x_8_8"]
        vy = D["object"]["velocity_tables"]["y_8_8"]
        for dx, dy, hit in ((11, 11, True), (12, 0, False), (0, 12, False), (-11, -11, True), (-12, -12, False)):
            m = tool.RingModel(0, 1000, 622, vx, vy)
            hud = {"pickups": 0}
            for _ in range(17):
                m.update(tool.World(HDR), CELLS, (872, 526), (6000, 600), hud)
            player = (m.x + dx, m.y + dy)
            m.update(tool.World(HDR), CELLS, (872, 526), player, hud)
            self.assertEqual(hud["pickups"] == 1, hit, (dx, dy))

    def test_model_lockout(self):
        vx = D["object"]["velocity_tables"]["x_8_8"]
        vy = D["object"]["velocity_tables"]["y_8_8"]
        m = tool.RingModel(0, 1000, 622, vx, vy)
        hud = {"pickups": 0}
        first = None
        for u in range(30):
            m.update(tool.World(HDR), CELLS, (872, 526), (m.x, m.y), hud)
            if hud["pickups"] and first is None:
                first = u
        self.assertEqual(first, 17)


class TestLifetime(unittest.TestCase):
    def test_runs(self):
        lw = D["lifetime_window"]
        expect = [["delete", -150, -97], ["asleep", -96, -33], ["active", -32, 287], ["asleep", 288, 351], ["delete", 352, 419]]
        self.assertEqual(lw["horizontal_runs_dx_at_dy_96"], expect)
        self.assertEqual(lw["vertical_runs_dy_at_dx_128"], expect)
        self.assertEqual(lw["mismatches_vs_model"], 0)
        self.assertEqual(lw["cases"], 3640)

    def test_model_classification(self):
        for d, cls in ((-97, "delete"), (-96, "asleep"), (-33, "asleep"), (-32, "active"), (287, "active"), (288, "asleep"), (351, "asleep"), (352, "delete")):
            self.assertEqual(tool.lifetime_class(CELLS, 1000 + d, 596, 1000, 500), cls, d)
        self.assertEqual(tool.lifetime_class(CELLS, 1000 - 129, 596, 1000, 500), "delete")


class TestInteractions(unittest.TestCase):
    def test_model_equals_rom_everywhere(self):
        mv = D["model_vs_rom"]
        self.assertEqual(mv["mismatches"], 0)
        self.assertGreater(mv["ring_updates_compared"], 50000)
        self.assertEqual(mv["pickups_rom"], mv["pickups_model"])
        for k in ("floor_bounce", "ceiling", "bounce_exhausted", "offscreen_bit6", "offscreen_delete", "pickup", "sparkle_end"):
            self.assertGreater(mv["model_event_counts"][k], 0, k)

    def test_water(self):
        self.assertTrue(D["water"]["controlled"]["identical"])
        self.assertFalse(D["water"]["static"]["any_reference"])

    def test_second_hurt_and_blink(self):
        ev = D["second_hurt"]["events"]
        self.assertEqual(ev[0]["scatter_objects"], 5)
        self.assertEqual(ev[0]["rings_after"], "0x05")
        self.assertEqual(ev[1]["pass"], 121)
        self.assertEqual(ev[2]["requested_state"], "0x1E")
        self.assertEqual(ev[2]["scatter_slots"][-1][1], 0)                                  # new token 0 takes the next free slot
        b = D["invulnerability_blink"]["rows"]
        self.assertEqual(b["current_state_1E"]["hidden_run_lengths_[hidden, updates]"], [[0, 124]])
        self.assertEqual(b["current_state_05"]["hidden_run_lengths_[hidden, updates]"][:4], [[1, 2], [0, 2], [1, 2], [0, 2]])
        self.assertEqual(b["current_state_05"]["invulnerable_bit_cleared_at_gate"], 121)

    def test_terrain_and_dropped_paths_share_the_counter(self):
        s = D["shared_counter_path"]
        self.assertTrue(s["terrain_ring_handler_jp_3138_at"])
        self.assertIn("$3138", s["object_ring_pickup_reads"])

    def test_poc_diagnosis_recorded(self):
        text = " ".join(D["poc_divergence"]["observed"])
        self.assertIn("OBJ_player_lost_b", text)
        self.assertIn("alarm[0] = 80", text)


class TestGpz3Example(unittest.TestCase):
    G = D["gpz3_boss_example"]
    NAT = G["natural_no_recollect"]["rows"]
    PICK = G["player_teleports_onto_ring_0_at_k40"]["rows"]

    def test_hurt_and_spawn(self):
        r1, r2 = self.NAT[0], self.NAT[1]
        self.assertEqual(r1["rings"], [])
        self.assertEqual(r1["player"][8], 0x47)
        self.assertEqual(r2["player"][8], 0)
        self.assertEqual(r2["player"][7], 120)
        self.assertEqual((r2["player"][5], r2["player"][6]), (0x1E, 0xC1))
        self.assertEqual(len(r2["rings"]), 5)
        px, py = r1["player"][0], r1["player"][1]
        vx = D["object"]["velocity_tables"]["x_8_8"]
        vy = D["object"]["velocity_tables"]["y_8_8"]
        for tok, ring in enumerate(r2["rings"]):
            self.assertEqual((ring[0], ring[1]), (tok, tok))                                  # token == slot in an empty pool
            self.assertEqual((ring[4], ring[5]), (px, py - 16))
            self.assertEqual((ring[6], ring[7], ring[8]), (vx[tok], vy[tok], -1024))

    def test_off_screen_removal_matches_the_band(self):
        camx = self.NAT[1]["camera"][0]
        last = {}
        for r in self.NAT:
            for t in r["rings"]:
                last[t[0]] = t
        for tok in (1, 2, 3, 4):
            d = last[tok][4] - camx
            self.assertTrue(d < -32 or d >= 288, (tok, d))                    # the last visible row is already in the asleep zone
        self.assertEqual(set(last), {0, 1, 2, 3, 4})
        self.assertTrue(any(t[0] == 0 for t in self.NAT[-1]["rings"]))        # token 0 is still flying at the end of the trace

    def test_recollection_during_invulnerability(self):
        pick = self.G["player_teleports_onto_ring_0_at_k40"]["pick"]
        self.assertEqual((pick["k"], pick["rings_before"], pick["player_state"], pick["flags"]), (40, 0, 0x1E, 0xC1))
        before, after = self.PICK[39], self.PICK[40]
        self.assertEqual((before["player"][8], after["player"][8]), (0, 1))
        self.assertEqual([t[3] for t in after["rings"] if t[0] == 0], [2])        # ring 0 requested the sparkle state
        last0 = max(r["k"] for r in self.PICK if any(t[0] == 0 for t in r["rings"]))
        self.assertEqual(last0, 69)                                               # pickup update 40 + 29
        for tok in (1, 2, 3, 4):
            self.assertEqual([r["k"] for r in self.NAT if any(t[0] == tok for t in r["rings"])][-1],
                             [r["k"] for r in self.PICK if any(t[0] == tok for t in r["rings"])][-1])

    def test_natural_run_has_no_pickup(self):
        self.assertTrue(all(r["player"][8] == 0 for r in self.NAT[1:]))


@unittest.skipUnless(ROM, "matching Sonic Chaos ROM not found (set SONIC_CHAOS_ROM)")
class TestRomBacked(unittest.TestCase):
    def test_static_regenerates(self):
        self.assertEqual(json.loads(json.dumps(tool.static_routines(ROM))), D["routines"])
        self.assertEqual(json.loads(json.dumps(tool.static_object(ROM))), D["object"])
        self.assertEqual(json.loads(json.dumps(tool.static_shared_paths(ROM))), D["shared_counter_path"])
        self.assertEqual(json.loads(json.dumps(tool.water_scan(ROM))), D["water"]["static"])

    def test_emission_and_hurt_regenerate(self):
        self.assertEqual(json.loads(json.dumps(tool.emission_table(ROM))), D["emission"])
        self.assertEqual(json.loads(json.dumps(tool.hurt_rows(ROM))), D["hurt_rows"])
        self.assertEqual(json.loads(json.dumps(tool.pool_cases(ROM))), D["pool"])

    def test_pickup_and_flights_regenerate(self):
        self.assertEqual(json.loads(json.dumps(tool.lockout_and_effects(ROM))), D["lockout_pickup"])
        self.assertEqual(json.loads(json.dumps(tool.flat_floor(ROM))), D["flat_floor"])
        self.assertEqual(json.loads(json.dumps(tool.ceiling_and_oneway(ROM))), D["ceiling_and_oneway"])
        self.assertEqual(json.loads(json.dumps(tool.lifetime_window(ROM))), D["lifetime_window"])

    def test_model_sweep_regenerates(self):
        self.assertEqual(json.loads(json.dumps(tool.model_vs_rom(ROM))), D["model_vs_rom"])
        self.assertEqual(json.loads(json.dumps(tool.water_equivalence(ROM))), D["water"]["controlled"])
        self.assertEqual(json.loads(json.dumps(tool.second_hurt(ROM))), D["second_hurt"])
        self.assertEqual(json.loads(json.dumps(tool.invulnerability_blink(ROM))), D["invulnerability_blink"])

    def test_gpz3_example_regenerates(self):
        gp = json.loads(json.dumps(tool.gpz3_example(ROM)))
        for k in ("natural_no_recollect", "player_teleports_onto_ring_0_at_k40"):
            self.assertEqual(gp[k], D["gpz3_boss_example"][k])

    def test_rom_velocity_tables_equal_model_constants(self):
        vt = tool.static_object(ROM)["velocity_tables"]
        self.assertEqual(vt["x_8_8"], D["object"]["velocity_tables"]["x_8_8"])
        self.assertEqual(vt["y_8_8"], D["object"]["velocity_tables"]["y_8_8"])


if __name__ == "__main__":
    unittest.main()

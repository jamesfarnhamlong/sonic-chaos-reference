#!/usr/bin/env python3
"""THZ1/THZ2 object type $18 and act-clear study: cache-driven tests (no ROM) plus ROM-backed regeneration.

Regenerating everything from the ROM: `python tools/object_18.py ROM --check` or
`tests/verify_cache.py ROM`. The ROM-backed class here runs when a matching ROM is found
(set SONIC_CHAOS_ROM) and skips otherwise.
"""
import hashlib
import importlib.util
import json
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
CACHE = ROOT / "data" / "rom-cache" / "object-18-act-clear.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))
CE = D["controlled_execution"]
EM = D["emulated_original_frames"]

spec = importlib.util.spec_from_file_location("object_18", ROOT / "tools" / "object_18.py")
tool = importlib.util.module_from_spec(spec)
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


def routines():
    return {r["name"]: r for r in D["routines"]}


class ProvenanceTests(unittest.TestCase):
    def test_rom_hash_and_scope(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertTrue(D["research_only"])
        self.assertTrue(D["poc_untouched"])
        self.assertEqual(D["machine_facing_label"], "object_18")

    def test_cache_holds_no_rom_pixels_or_dumps(self):
        text = json.dumps(D)
        for word in ("cram_bytes", "tile_pixels", "rgba", "palette_bytes"):
            self.assertNotIn(word, text)
        for r in D["routines"]:
            self.assertLessEqual(len(r["first_16_bytes"]), 32)
            self.assertNotIn("bytes", r)


class PlacementTests(unittest.TestCase):
    def test_records(self):
        p = D["placement"]["records"]
        self.assertEqual(p["thz1"]["raw_bytes"], "18 78 10 2E 03 00 00 00 00")
        self.assertEqual((p["thz1"]["world_x"], p["thz1"]["world_y"]), (3960, 558))
        self.assertEqual(p["thz2"]["raw_bytes"], "18 78 10 8E 03 00 00 00 00")
        self.assertEqual((p["thz2"]["world_x"], p["thz2"]["world_y"]), (3960, 654))
        self.assertEqual((p["thz1"]["rom_offset"], p["thz2"]["rom_offset"]), ("0x70782", "0x708F4"))
        for act in ("thz1", "thz2"):
            self.assertEqual((p[act]["flags"], p[act]["parameter"], p[act]["aux0"], p[act]["aux1"]), ("0x00",) * 4)
            self.assertTrue(p[act]["matches_level_package"])

    def test_counts_and_difference(self):
        self.assertEqual(D["placement"]["count_per_act"], {"thz1": 1, "thz2": 1, "thz3": 0})
        self.assertTrue(D["placement"]["thz1_thz2_identical_except_position"])
        self.assertEqual(D["placement"]["thz1_thz2_y_difference"], 96)


class DispatchTests(unittest.TestCase):
    def test_sign_dispatch(self):
        s = D["dispatch"]["0x18"]
        self.assertEqual((s["type_table_entry_rom"], s["type_table_entry_value"]), ("0x065E8", "0xA7BC"))
        self.assertEqual(s["state_count"], 7)
        self.assertEqual([x["script_cpu"] for x in s["states"]],
                         ["0xA7CA", "0xA7D3", "0xA7D9", "0xA7E2", "0xA7E8", "0xA81F", "0xA82E"])
        self.assertEqual((s["mapping_pointer_value"], s["mapping_rom"]), ("0x8EAE", "0x3CEAE"))
        callbacks = {x["state"]: sorted({r["callback"] for r in x["records"]}) for x in s["states"]}
        self.assertEqual(callbacks[0], ["0xA867"])
        self.assertEqual(callbacks[1], ["0xA873"])
        self.assertEqual(callbacks[2], ["0xA87D"])
        self.assertEqual(callbacks[3], ["0xA88E"])
        self.assertEqual(callbacks[4], ["0xA8C8", "0xA8CE"])
        self.assertEqual(callbacks[5], ["0x032F"])
        self.assertEqual(callbacks[6], ["0x032F", "0xA8FA"])       # spin loops, then the landing/prize routine again
        self.assertTrue(all(x["unresolved"] is None for x in s["states"]))

    def test_sign_scripts(self):
        st = {x["state"]: x for x in D["dispatch"]["0x18"]["states"]}
        self.assertEqual(st[3]["records"][0]["raw"], "E0 01 8E A8")            # duration $E0, frame 1
        self.assertEqual([c["target_state"] for c in st[0]["commands"] if "target_state" in c], [1])
        self.assertEqual([c["target_state"] for c in st[2]["commands"] if "target_state" in c], [3])
        spawn = [c for c in st[5]["commands"] if c.get("meaning") == "call_routine"]
        self.assertEqual(spawn[0]["target_cpu"], "0xAA47")
        self.assertEqual(st[4]["frames"], [1, 2, 3, 4, 5])
        self.assertEqual(st[6]["frames"], [1, 2, 3, 4, 5])
        sounds = [c["sound_id"] for c in st[4]["commands"] if c.get("meaning") == "sound_request"]
        self.assertEqual(sounds[0], "0xF8")
        self.assertIn("0xAA", sounds)

    def test_child_dispatch(self):
        c = D["dispatch"]["0x19"]
        self.assertEqual((c["type_table_entry_rom"], c["type_table_entry_value"]), ("0x065EA", "0xAA4F"))
        self.assertEqual(c["state_count"], 5)
        self.assertEqual([x["script_cpu"] for x in c["states"]], ["0xAA59", "0xAA5F", "0xAA65", "0xAA78", "0xAA81"])
        cb = {x["state"]: sorted({r["callback"] for r in x["records"]}) for x in c["states"]}
        self.assertEqual(cb[0], ["0xAA87"])
        self.assertEqual(cb[1], ["0xAAE4"])
        self.assertEqual(cb[2], ["0xAB0A"])
        self.assertEqual(cb[3], ["0xAB48"])
        self.assertEqual(cb[4], ["0xAB8C"])

    def test_frame_extents(self):
        f = {r["frame"]: r for r in D["frame_extents"]["0x18"]}
        self.assertEqual((f[1]["extent_x"], f[1]["extent_y"]), (12, 42))
        self.assertEqual((f[0]["extent_x"], f[0]["extent_y"]), (0, 0))

    def test_routine_bytes(self):
        r = routines()
        self.assertEqual((r["goal_state3_contact"]["cpu"], r["goal_state3_contact"]["rom_offset"],
                          r["goal_state3_contact"]["length"]), ("0xA88E", "0x3288E", 54))
        self.assertTrue(r["goal_state3_contact"]["first_16_bytes"].startswith("3a02d5fe18"))         # LD A,($D502); CP $18
        self.assertTrue(r["goal_state0_init"]["first_16_bytes"].startswith("ddcb03feaf"))        # SET 7,(IX+3); XOR A
        self.assertTrue(r["level_complete_setter"]["first_16_bytes"].startswith("3e203202d50e89"))  # LD A,$20; LD ($D502),A; LD C,$89
        self.assertTrue(r["player_state20_handler"]["first_16_bytes"].startswith("ddcb04beaf"))
        self.assertTrue(r["overlap_helper"]["first_16_bytes"].startswith("afdd7720dd7e21"))        # XOR A; LD (IX+$20),A; LD A,(IX+$21)


class ContactRuleTests(unittest.TestCase):
    """Exact rule: overlap helper $6328 with sign extents (12, 42) and the player's current-frame extents."""

    C = CE["contact"]

    def test_state3_entry_extents(self):
        s = self.C["state3_entry"]["snapshot"]
        self.assertEqual((s["state"], s["requested"], s["frame"], s["ext_x"], s["ext_y"]), (3, 3, 1, 12, 42))
        self.assertEqual(s["flags_03"], "0x80")                # bit 7: ignore the player's D503 bit-6 gate

    def test_formula_matches_every_grid_cell(self):
        g = self.C["boundary_grid"]
        self.assertEqual(g["mismatches_vs_formula"], 0)
        self.assertEqual(g["cells_checked"], 5 * 81 * 81)

    def test_sonic_box(self):
        g = self.C["boundary_grid"]["by_player_extents"]["8,24"]
        self.assertEqual((g["contact_dx_min"], g["contact_dx_max"]), (-20, 20))
        self.assertEqual((g["contact_dy_min"], g["contact_dy_max"]), (-42, 24))
        self.assertTrue(g["rows_contiguous_and_equal"])
        g = self.C["boundary_grid"]["by_player_extents"]["9,24"]
        self.assertEqual((g["contact_dx_min"], g["contact_dx_max"]), (-21, 21))

    def test_other_extents(self):
        g = self.C["boundary_grid"]["by_player_extents"]
        self.assertEqual((g["0,0"]["contact_dx_min"], g["0,0"]["contact_dx_max"], g["0,0"]["contact_dy_max"]), (-12, 12, 0))
        self.assertEqual(g["8,18"]["contact_dy_max"], 18)

    def test_edges_are_inclusive(self):
        e = {(x["dx"], x["dy"]): x for x in self.C["edge_cases_sonic_8_24"]}
        self.assertTrue(e[(20, 0)]["contact"])
        self.assertFalse(e[(21, 0)]["contact"])
        self.assertTrue(e[(-20, 0)]["contact"])
        self.assertFalse(e[(-21, 0)]["contact"])
        self.assertTrue(e[(0, 24)]["contact"])
        self.assertFalse(e[(0, 25)]["contact"])
        self.assertTrue(e[(0, -42)]["contact"])
        self.assertFalse(e[(0, -43)]["contact"])
        for x in self.C["edge_cases_sonic_8_24"]:
            self.assertEqual(x["contact"], x["formula"])

    def test_formula_function(self):
        f = tool.predicted_contact
        self.assertTrue(f(20, 0, 8, 24))
        self.assertFalse(f(21, 0, 8, 24))
        self.assertTrue(f(-20, 0, 8, 24))
        self.assertFalse(f(-21, 0, 8, 24))
        self.assertTrue(f(0, 24, 8, 24))
        self.assertFalse(f(0, 25, 8, 24))
        self.assertTrue(f(0, -42, 8, 24))
        self.assertFalse(f(0, -43, 8, 24))
        self.assertFalse(f(256, 0, 8, 24))
        self.assertFalse(f(-256, 0, 8, 24))
        self.assertTrue(f(9 + 12, 0, 9, 24))

    def test_world_boxes(self):
        # player anchor range that triggers, per act, for Sonic (8, 24)
        for act, (sx, sy) in (("thz1", (3960, 558)), ("thz2", (3960, 654))):
            p = D["placement"]["records"][act]
            self.assertEqual((p["world_x"], p["world_y"]), (sx, sy))
            self.assertEqual((sx - 20, sx + 20, sy - 42, sy + 24), (3940, 3980, sy - 42, sy + 24))

    def test_gate(self):
        g = {x["case"]: x["contact_triggered"] for x in self.C["gating_at_dx0_dy0"]}
        self.assertTrue(g["moving_right"])
        self.assertTrue(g["moving_left_negative_speed"])
        self.assertTrue(g["slowest_nonzero_speed_0001"])
        self.assertFalse(g["standing_still_requested_2"])
        self.assertTrue(g["standing_still_requested_18"])
        self.assertTrue(g["moving_requested_18"])
        self.assertFalse(g["standing_still_requested_12"])
        self.assertTrue(g["moving_ball_flags_02"])
        self.assertTrue(g["moving_airborne_flags_01"])
        self.assertTrue(g["moving_with_D503_bit6"])
        self.assertTrue(g["standing_still_with_D503_bit6_req_18"])
        self.assertTrue(self.C["y_velocity_ignored"]["contact_with_vy_0800"])

    def test_contact_effects(self):
        first = self.C["contact_effects"]["first_touch"]
        self.assertEqual(first["requested_state"], 4)
        self.assertEqual(first["timer_flag_D2BE"], 0)
        self.assertEqual(first["D445"], 0)
        self.assertEqual(first["sign_y_velocity_hi_19"], "0xFC")
        self.assertEqual(first["pan_flags_D15E_D15F"], ["0x80", "0x01"])
        self.assertEqual(first["pan_target_D2DA_D2DC"], [3960 - 128, 558 - 153])
        self.assertEqual(first["player_requested_state_D502"], "0x02")         # the player is not touched
        self.assertTrue(first["player_x_unchanged"])
        retouch = self.C["contact_effects"]["retouch_after_retry"]
        self.assertEqual(retouch["requested_state"], 6)
        self.assertEqual(retouch["timer_flag_D2BE"], 0)
        self.assertEqual(retouch["pan_flags_D15E_D15F"], ["0x00", "0x00"])

    def test_left_lock_only_with_gate(self):
        lock = self.C["left_lock_while_waiting"]
        self.assertEqual(lock["D280_after"], 100)
        self.assertEqual(lock["D280_after_moving"], 3850)


class HopTests(unittest.TestCase):
    def test_timeline_identical_in_thz1_and_thz2(self):
        for k in ("hop_thz1", "hop_thz2"):
            h = CE[k]
            self.assertEqual(h["contact_update"], 1)
            self.assertEqual(h["updates_contact_to_landing"], 130)
            self.assertEqual(h["landing_update"], 131)
            self.assertEqual(h["child_update"], 132)
            self.assertEqual(h["spin_sound_AA_count"], 32)
            self.assertEqual((h["sound_F8_update"], h["sound_AB_update"]), (1, 131))
            self.assertEqual(h["checkpoints"][-1]["state"], 5)
            self.assertEqual(h["checkpoints"][-1]["callback"], "0x032F")
        a, b = CE["hop_thz1"], CE["hop_thz2"]
        self.assertEqual([r["y"] - 558 for r in a["checkpoints"]], [r["y"] - 654 for r in b["checkpoints"]][:len(a["checkpoints"])])

    def test_hop_model(self):
        t = CE["hop_trace_thz1"]
        self.assertEqual((t["start_y"], t["apex_y"], t["apex_rise"], t["landing_y"]), (558, 432, 126, 558))
        self.assertEqual(t["first_vy_values"], [-1024, -1024, -1024, -1008, -992, -976])
        self.assertEqual(t["first_y_values"][:3], [558, 558, 558])
        self.assertEqual(t["max_vy_seen"], 1024)
        self.assertEqual(t["updates"], 131)


class LifetimeTests(unittest.TestCase):
    L = CE["lifetime"]

    def test_sign_removed_only_by_shared_cleanup(self):
        self.assertEqual(self.L["token_3E_at_creation"], 53)           # index 52 + 1
        self.assertFalse(self.L["flags_04_keep_alive_bit1"])
        self.assertEqual(self.L["occupancy_byte"], "0x18")
        for k in ("camera_far_right", "camera_far_left", "state5_camera_far"):
            self.assertEqual(self.L[k]["type_after"], "0xFE", k)
        self.assertEqual(self.L["camera_near"]["type_after"], "0x18")
        self.assertEqual(self.L["camera_near"]["state_after"], 3)


class PrizeTests(unittest.TestCase):
    P = CE["prizes"]

    def test_tables_from_rom(self):
        t = D["prize_tables"]
        self.assertEqual(t["thz_table_cpu"], "0xA919")
        self.assertEqual(t["rows_thz_table"][0], ["15", "30", "40", "60"])
        self.assertEqual(t["rows_thz_table"][1], ["09", "19", "29", "39", "49", "59", "69", "79", "89"])
        self.assertEqual(t["rows_thz_table"][2], ["99", "97", "95", "88", "77", "65", "55"])
        self.assertEqual(t["rows_thz_table"][3], ["16", "28", "32", "44", "58"])
        self.assertEqual(t["rows_other_table"][0], ["00", "24", "48", "72"])
        self.assertIn("zone parity", t["selection"])

    def test_class_by_ring_count(self):
        c = self.P["class_to_ring_counts_zone0"]
        self.assertEqual(c["3"], ["15", "30", "40", "60"])
        self.assertEqual(c["2"], ["09", "19", "29", "39", "49", "59", "69", "79", "89"])
        self.assertEqual(c["1"], ["55", "65", "77", "88", "95", "97", "99"])
        self.assertEqual(c["0"], ["16", "28", "32", "44", "58"])
        self.assertEqual(len(c["255"]), 100 - 4 - 9 - 7 - 5)

    def test_effects(self):
        e = self.P["effects_by_class"]
        self.assertEqual((e["class_2_ring_09_player_1"]["rings_D29A"], e["class_2_ring_09_player_1"]["D3B3"]), ("0x19", "0x1E"))
        self.assertEqual(e["class_3_ring_15_player_1"]["lives_D2C3"], 4)
        self.assertEqual((e["class_3_ring_15_player_1"]["D3B3"], e["class_3_ring_15_player_2"]["D3B3"]), ("0x1D", "0x1B"))
        self.assertEqual(e["class_1_ring_99_player_1"]["counter_D299"], 2)
        self.assertEqual((e["class_1_ring_99_player_1"]["D3B3"], e["class_1_ring_99_player_2"]["D3B3"]), ("0x1B", "0x1D"))
        self.assertEqual(e["class_255_ring_00_player_1"]["D3B3"], "0x1F")
        r0 = e["class_0_ring_16_player_1"]
        self.assertEqual((r0["next_state_02"], r0["retry_35"], r0["D3B3"]), (3, 255, "0x20"))
        self.assertEqual(e["class_255_ring_00_player_1"]["next_state_02"], 5)

    def test_retry_roll(self):
        r = self.P["retry_roll_after_class_0"]
        self.assertEqual([r[str(i)]["class_34"] for i in range(8)], [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(r["2"]["lives"], 4)
        self.assertEqual(r["1"]["rings"], "0x26")
        self.assertTrue(all(r[str(i)]["state_02"] == 5 for i in range(8)))


class RetryTests(unittest.TestCase):
    def test_retry_path(self):
        r = CE["retry_path"]
        self.assertEqual(r["marks"], {"touch1_update": 1, "back_in_state_3_update": 132, "touch2_update": 133, "state_5_update": 199})
        self.assertEqual(r["updates_touch2_to_state_5"], 66)
        ev = {(e["update"]): e for e in r["events"]}
        self.assertEqual((ev[131]["requested"], ev[131]["retry_35"], ev[131]["D3B3"]), (3, 255, "0x20"))
        self.assertEqual((ev[134]["state"], ev[198]["requested"], ev[198]["prize_34"]), (6, 5, 2))
        self.assertEqual((ev[198]["rings"], ev[198]["D3B3"]), ("0x26", "0x1E"))
        self.assertEqual(ev[198]["update"] - ev[134]["update"], 64)            # 4 loops x 8 records x 2 updates


class ChildTests(unittest.TestCase):
    def test_child_timeline(self):
        rows = {r["update"]: r for r in CE["child_19"]["rows"] if "state" in r}
        self.assertEqual((rows[1]["x"], rows[1]["y"]), (3832 + 0x104, 405 + 0x50))
        self.assertEqual(rows[18]["requested"], 2)
        self.assertEqual(rows[19]["state"], 2)
        self.assertEqual(rows[147]["state"], 3)
        self.assertEqual(rows[148]["state"], 4)
        self.assertEqual(rows[147]["D2A6"], "0x0989")
        done = CE["child_19"]["rows"][-1]
        self.assertEqual((done["event"], done["sound"], done["D502"]), ("player requested state $20", "0x89", "0x20"))
        self.assertEqual(done["update"], 401)                                   # waited for the withheld floor bit
        self.assertEqual(CE["child_19"]["roll_sound_BC_count"], 32)
        self.assertEqual(CE["child_19_position"]["first_update_in_state_2"], 19)
        self.assertEqual(CE["child_19_position"]["x_at_state_2"], 3832 + 0x85 - 1)

    def test_bonus_value(self):
        s = {(r["time_D2BF_bcd"], r["rings_D29A_bcd"]): r["HL"] for r in CE["bonus_value"]["samples"]}
        self.assertEqual(s[("0006", "00")], "0x0989")
        self.assertEqual(s[("0029", "00")], "0x0889")
        self.assertEqual(s[("0058", "11")], "0x0800")
        self.assertEqual(s[("0059", "12")], "0x0701")
        self.assertEqual(s[("0429", "99")], "0x0188")
        self.assertEqual(s[("0800", "10")], "0x0099")
        last = [r for r in CE["bonus_value"]["samples"] if (r["time_D2BF_bcd"], r["rings_D29A_bcd"]) == ("0800", "11")][0]
        self.assertEqual((last["HL"], last["D2A6_after_state3"], last["D299_after_state3"]), ("0x0000", "0x0777", 2))  # zero -> $0777, equal digits reward
        for r in CE["bonus_value"]["samples"][:-1]:
            self.assertEqual(r["D2A6_after_state3"], r["HL"])
            self.assertEqual(r["D299_after_state3"], 1)


class ActClearTests(unittest.TestCase):
    P = CE["player_state_20"]

    def test_flag_boundary(self):
        rows = {(r["D298"], r["player_minus_camera_x"]): r for r in self.P["cases"]}
        for act in (0, 1, 2):
            self.assertFalse(rows[(act, 0x120)]["flag_set"])
            self.assertTrue(rows[(act, 0x121)]["flag_set"])
            self.assertFalse(rows[(act, 0xF9)]["flag_set"])
            self.assertEqual(rows[(act, 0x121)]["x_velocity_after"], 0)
        self.assertEqual(rows[(0, 0x121)]["D293_after"], "0x60")
        self.assertEqual(rows[(1, 0x121)]["D293_after"], "0x60")
        self.assertEqual(rows[(2, 0x121)]["D293_after"], "0x50")

    def test_velocity(self):
        self.assertEqual(self.P["velocity_first_6"], [16, 32, 48, 64, 80, 96])
        self.assertEqual(self.P["velocity_cap_when_flag_not_reached"], 0x600)
        self.assertEqual(self.P["velocity_from_negative_after_one_update"], 16)

    def test_setter(self):
        s = CE["level_complete_setter"]["by_D298"]
        self.assertEqual(s["0"], {"D502": "0x20", "sound_DE04": "0x89"})
        self.assertEqual(s["1"], {"D502": "0x20", "sound_DE04": "0x89"})
        self.assertEqual(s["2"], {"D502": "0x20", "sound_DE04": "0x97"})

    def test_timer_rule(self):
        t = CE["timer"]["cases"]
        self.assertEqual(t["running_D2BE_FF"]["time_D2BF"], "0x0059")
        self.assertEqual(t["stopped_D2BE_00"]["time_D2BF"], "0x0058")
        self.assertEqual(t["rollover"]["time_D2BF_after"], "0x0100")

    def test_main_loop_routines_present(self):
        r = routines()
        self.assertEqual((r["act_clear_sequence_bit5"]["cpu"], r["zone_clear_sequence_bit4"]["cpu"]), ("0x14AE", "0x1543"))
        self.assertEqual(r["results_ring_bonus_tally"]["cpu"], "0x2D08")
        self.assertEqual(r["timer_tick"]["cpu"], "0x27EE")


class EmulatedTests(unittest.TestCase):
    def rel(self, k, name):
        return EM[k]["marks"][name] - EM[k]["marks"]["flag_bit5_set"]

    def test_chain_timings(self):
        for k in ("thz1_rings_0", "thz1_rings_09", "thz2_rings_0", "thz1_hostile_input_during_state_20"):
            r = EM[k]
            c = r["contact_frame_sign_requests_state_4"]
            self.assertEqual(r["marks"]["flag_bit5_set"] - c, 309 if k != "thz2_rings_0" else 310)
            self.assertEqual(self.rel(k, "act_clear_sequence_entry"), 1)
            self.assertEqual(self.rel(k, "results_screen_draw_entry"), 199)
            self.assertEqual(self.rel(k, "ring_tally_entry"), 275)
        self.assertEqual(EM["thz1_rings_0"]["marks_relative_to_contact"]["flag_bit5_set"], 309)

    def test_timer_stops_at_contact(self):
        for k in ("thz1_rings_0", "thz2_rings_0"):
            ev = EM[k]["events"]
            at_contact = next(e for e in ev if e["sign_state_req"] == [3, 4])
            self.assertEqual(at_contact["D2BE"], 0)
            before = [e for e in ev if e["frame"] < at_contact["frame"] and e["sign_state_req"] == [3, 3]]
            self.assertTrue(all(e["D2BE"] == 255 for e in before))
            self.assertTrue(all(e["D2BE"] == 0 for e in ev if e["frame"] >= at_contact["frame"]))
            self.assertEqual(at_contact["player_extents"], [8, 24])

    def test_no_player_lock_before_state_20(self):
        ev = EM["thz1_rings_0"]["events"]
        between = [e for e in ev if e["sign_state_req"] in ([4, 4], [4, 5], [5, 5]) and e["player_D501"] != "0x20"]
        self.assertTrue(between)
        self.assertTrue(all(e["player_D501"] in ("0x05", "0x06") for e in between))

    def test_flag_bits_by_act(self):
        self.assertEqual(EM["thz1_rings_0"]["events"][-2]["D293"], "0x60")
        self.assertEqual(EM["thz2_rings_0"]["events"][-2]["D293"], "0x60")
        self.assertEqual(EM["thz3_forced_state_20"]["D293_bit"], 4)
        self.assertIn("flag_bit4_set", EM["thz3_forced_state_20"]["marks"])
        self.assertEqual(EM["thz3_forced_state_20"]["marks"]["flag_bit4_set"], EM["thz3_forced_state_20"]["marks"]["zone_clear_sequence_entry"])

    def test_thz3_timer_not_stopped(self):
        t = EM["thz3_forced_state_20"]["timer_D2BE_D2BF_D2C2"]
        self.assertEqual(t["at_force"][0], "0xFF")
        self.assertEqual(t["at_flag"][0], "0xFF")

    def test_prize_in_full_game(self):
        ev = {e["frame"]: e for e in EM["thz1_rings_09"]["events"]}
        landing = ev[197]
        self.assertEqual((landing["sign_prize_34_35"], landing["D3B3"], landing["rings_D29A"]), ([2, 0], "0x1E", "0x19"))
        self.assertEqual(ev[347]["D2A6"], "0x0908")          # bonus computed from the boosted ring count

    def test_sound_sequence(self):
        s = EM["thz1_rings_0"]["sound_requests"]
        ids = [x[1] for x in s]
        self.assertEqual(ids, ["0x81", "0xF8", "0xAA", "0xAB", "0xBC", "0x89", "0xB4"])


class ConvergenceTests(unittest.TestCase):
    def test_both_paths_call_the_same_vector(self):
        c = D["convergence_with_object_50"]
        self.assertEqual(c["vector_03F5"], {"bytes": "c3 92 48", "target": "0x4892"})
        self.assertEqual(c["child_19_calls_03F5_at"], ["0xAB9B"])
        self.assertEqual(c["boss_50_calls_03F5"], [{"region": "boss_defeat_complete_state5", "at": ["0x81DF"]}])
        self.assertEqual(c["goal_sign_calls_03F5"], [])

    def test_unresolved_list_present(self):
        self.assertGreaterEqual(len(D["unresolved"]), 6)


@unittest.skipUnless(matching_rom(), "matching ROM not available (set SONIC_CHAOS_ROM)")
class RomRegenerationTests(unittest.TestCase):
    def test_static_sections_regenerate(self):
        rom = matching_rom().read_bytes()
        built = tool.build(rom, static_only=True)
        for key, value in built.items():
            self.assertEqual(D[key], value, key)

    def test_full_cache_regenerates(self):
        rom = matching_rom().read_bytes()
        self.assertEqual(json.loads(json.dumps(tool.build(rom))), D)


if __name__ == "__main__":
    unittest.main()

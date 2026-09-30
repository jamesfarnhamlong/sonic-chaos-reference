#!/usr/bin/env python3
"""THZ3 object type $50 study: cache-driven tests (no ROM) plus ROM-backed regeneration.

Regenerating everything from the ROM: `python tools/object_50.py ROM --check` or
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
CACHE = ROOT / "data" / "rom-cache" / "thz3" / "object-50.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))
CE = D["controlled_execution"]
EM = D["emulated_original_frames"]
STATES = {s["state"]: s for s in D["states"]}

spec = importlib.util.spec_from_file_location("object_50", ROOT / "tools" / "object_50.py")
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


class ProvenanceTests(unittest.TestCase):
    def test_rom_hash_and_scope(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertTrue(D["research_only"])
        self.assertTrue(D["poc_untouched"])

    def test_cache_holds_no_rom_pixels_or_palette_dumps(self):
        text = json.dumps(D)
        for word in ("cram_bytes", "tile_pixels", "rgba", "palette_bytes"):
            self.assertNotIn(word, text)
        for r in D["routines"]:
            self.assertLessEqual(len(r["first_16_bytes"]), 32)   # only a short prefix + SHA-256 of each region
            self.assertNotIn("bytes", r)

    def test_machine_facing_label_stays_numeric(self):
        self.assertEqual(D["subject"], "THZ3 object type $50")
        self.assertIn("object_50", D["identity"]["machine_facing_label"])


class PlacementTests(unittest.TestCase):
    def test_sole_placement(self):
        p = D["placement"]
        self.assertEqual(p["rom_offset"], "0x708FE")
        self.assertEqual((p["bank"], p["cpu"]), ("0x1C", "0x88FE"))
        self.assertEqual(p["raw_bytes"], "50 90 08 EE 01 00 00 00 00")
        self.assertEqual((p["stored_x"], p["stored_y"]), (2192, 494))
        self.assertEqual((p["world_x"], p["world_y"]), (1936, 238))
        self.assertEqual((p["flags"], p["parameter"], p["aux0"], p["aux1"]), ("0x00",) * 4)
        self.assertEqual(p["count_in_all_acts"], 1)
        self.assertTrue(p["record_matches_level_package"])

    def test_placement_matches_level_package_cache(self):
        objs = json.loads((ROOT / "data/rom-cache/levels/thz3/objects.json").read_text(encoding="utf-8"))
        first = objs["records"][0]
        self.assertEqual((first["type_id"], first["world_x"], first["world_y"]), ("0x50", 1936, 238))
        census = json.loads((ROOT / "data/rom-cache/levels/object-census.json").read_text(encoding="utf-8"))
        self.assertIn("0x50", json.dumps(census))

    def test_creation_fields(self):
        f = CE["creation"]["fields"]
        self.assertEqual((f["type"], f["state"], f["requested"]), ("0x50", 0, 0))
        self.assertEqual((f["x"], f["y"], f["saved_x_3A"], f["saved_y_3C"]), (1936, 238, 1936, 238))
        self.assertEqual((f["flags_04"], f["parameter_3F"], f["aux0_08"], f["aux1_09"], f["token_3E"]),
                         ("0x40", 0, 0, 0, 1))
        self.assertEqual(CE["creation"]["occupancy_byte_D400"], "0x50")

    def test_placement_window_samples(self):
        got = {(tuple(s["camera"]), s["initial_fill"]): s["created"] for s in CE["placement_window"]["samples"]}
        self.assertTrue(got[((1600, 0), 0)])
        self.assertTrue(got[((1600, 0), 1)])
        self.assertTrue(got[((1836, 100), 0)])
        for cam in ((1552, 0), (1500, 0), (2064, 0), (2200, 0)):
            self.assertFalse(got[(cam, 0)])


class DispatchTests(unittest.TestCase):
    def test_dispatch_chain(self):
        d = D["dispatch"]
        self.assertEqual(d["type_table_entry_rom"], "0x06658")
        self.assertEqual(d["type_table_entry_value"], "0x958B")
        self.assertEqual((d["state_table_bank"], d["state_table_cpu"], d["state_table_rom"]), ("0x1E", "0x958B", "0x7958B"))
        self.assertEqual(d["state_count"], 19)
        self.assertEqual(d["scheduler"]["engine"], "0x64FA")
        self.assertEqual(d["scheduler"]["callback_dispatch"], "0x5E91")
        self.assertEqual(d["scheduler"]["type_ge_26_branch"], "0x5E31")
        self.assertIn("0x33", d["shares_state_table_with_types"])
        self.assertIn("0x50", d["shares_state_table_with_types"])
        self.assertEqual(len(d["shares_state_table_with_types"]), 18)

    def test_mapping_pointer(self):
        m = D["dispatch"]["mapping_table"]
        self.assertEqual((m["pointer_entry_rom"], m["pointer_value"], m["bank"], m["rom"]),
                         ("0x3C0A0", "0x94C6", "0x0F", "0x3D4C6"))
        g = D["graphics"]["mapping"]
        self.assertEqual((g["cpu"], g["rom"], g["frame_count"]), ("0x94C6", "0x3D4C6", 7))
        self.assertEqual([f["record_cpu"] for f in D["graphics"]["frames"]],
                         ["0xA0E4", "0x94D4", "0x94DF", "0x94EA", "0x94F5", "0x9500", "0x950B"])

    def test_state_table_targets(self):
        cpus = D["dispatch"]["state_script_cpus"]
        self.assertEqual(cpus, ["0x95B1", "0x95BA", "0x95C0", "0x95C6", "0x95CC", "0x961E", "0x9632", "0x9640",
                                "0x967A", "0x9688", "0x9694", "0x96B6", "0x96C0", "0x96CE", "0x9708", "0x9716",
                                "0x9720", "0x9742", "0x9624"])
        for n, cpu in enumerate(cpus):
            self.assertEqual(STATES[n]["script_cpu"], cpu)
            self.assertEqual(int(STATES[n]["script_rom"], 16), 0x78000 + int(cpu, 16) - 0x8000)

    def test_callback_addresses_per_state(self):
        expected = {0: "0x974C", 1: "0x9771", 2: "0x97C1", 3: "0x9828", 5: "0x81BD", 6: "0x985B", 7: "0x9989",
                    8: "0x9997", 9: "0x9903", 10: "0x9989", 11: "0x9997", 12: "0x985B", 13: "0x9989",
                    14: "0x9997", 15: "0x9931", 16: "0x9989", 17: "0x9997", 18: "0x9A09"}
        for n, cb in expected.items():
            self.assertEqual(STATES[n]["callbacks_in_script"], [cb], n)
        self.assertEqual(STATES[4]["callbacks_in_script"], ["0x032F"])

    def test_routine_regions(self):
        r = {x["name"]: x for x in D["routines"]}
        self.assertEqual((r["boss_contact_damage"]["cpu"], r["boss_contact_damage"]["rom_offset"],
                          r["boss_contact_damage"]["length"]), ("0x99AE", "0x799AE", 91))
        self.assertTrue(r["boss_contact_damage"]["first_16_bytes"].startswith("dd7e1efe00"))   # LD A,(IX+$1E); CP 0
        self.assertTrue(r["boss_init_state0"]["first_16_bytes"].startswith("ddcb04ce3a97d2"))  # SET 1,(IX+4); LD A,($D297)
        self.assertTrue(r["animation_engine"]["first_16_bytes"].startswith("dd7e0e"))
        self.assertEqual(r["level_complete_setter"]["rom_offset"], "0x04892")
        self.assertEqual(r["enemy_destroy_conversion"]["cpu"], "0x5F54")
        for x in D["routines"]:
            self.assertEqual(len(x["sha256"]), 64)


class StateMachineTests(unittest.TestCase):
    def test_all_19_states_reachable_from_state_0(self):
        edges = {}
        for t in D["transitions"]:
            srcs = [t["from"]] if isinstance(t["from"], int) else [int(x) for x in str(t["from"]).split("/")]
            for s in srcs:
                if isinstance(t["to"], int):
                    edges.setdefault(s, set()).add(t["to"])
        seen, todo = {0}, [0]
        while todo:
            for n in edges.get(todo.pop(), ()):
                if n not in seen:
                    seen.add(n)
                    todo.append(n)
        self.assertEqual(seen, set(range(19)))

    def test_static_request_targets_are_valid_states(self):
        for s in D["states"]:
            for e in s["script"]:
                if e["op"] == "request_state":
                    self.assertIn(e["state"], STATES)
        self.assertEqual([e["state"] for e in STATES[4]["script"] if e["op"] == "request_state"], [5])

    def test_transition_edges(self):
        pairs = {(t["from"], t["to"]) for t in D["transitions"] if isinstance(t["from"], int)}
        for a, b in ((0, 1), (1, 2), (2, 3), (3, 18), (18, 6), (6, 9), (9, 12), (12, 15), (15, 6),
                     (6, 7), (6, 8), (9, 10), (9, 11), (12, 13), (12, 14), (15, 16), (15, 17),
                     (7, 6), (8, 6), (10, 9), (11, 9), (13, 12), (14, 12), (16, 15), (17, 15), (4, 5)):
            self.assertIn((a, b), pairs)

    def test_patrol_cycle_order_and_period(self):
        ev = CE["patrol_cycle"]["events"]
        order = [(e["state"], e["requested"]) for e in ev]
        for a in ((18, 6), (6, 9), (9, 12), (12, 15), (15, 6)):
            self.assertIn(a, order)
        first = next(e["update"] for e in ev if (e["state"], e["requested"]) == (6, 9))
        second = [e["update"] for e in ev if (e["state"], e["requested"]) == (6, 9)][1]
        self.assertEqual(second - first, 721)
        mirrored = {e["state"]: e["flags_04"] for e in ev}
        self.assertEqual(mirrored[12], "0x10")
        self.assertEqual(mirrored[6], "0x00")
        self.assertEqual(mirrored[15], "0x00")

    def test_state_1_and_18_boundaries(self):
        cases = {(c["dx"], c["dy"]): c["requested_after"] for c in CE["state_1_trigger"]["cases"]}
        self.assertEqual(cases[(159, 255)], 2)
        self.assertEqual(cases[(160, 255)], 1)
        self.assertEqual(cases[(159, 256)], 1)
        self.assertEqual(cases[(-159, -255)], 2)
        self.assertEqual(CE["state_1_trigger"]["zone0_words"], [160, 256])
        exits = {c["screen_x_low"]: c["requested_after"] for c in CE["state_18_exit"]["cases"]}
        self.assertEqual(exits, {0x7F: 18, 0x80: 6, 0xDF: 6, 0xE0: 18, 0xE1: 18})

    def test_state_0_2_3_effects(self):
        s0 = CE["state_0_init"]
        self.assertEqual(s0["after"]["requested"], 1)
        self.assertEqual((s0["sound_request_DE04"], s0["D44E"], s0["D4A5"]), ("0x8C", 1, 0))
        self.assertEqual(s0["child_slot_D540"], {"type": "0x12", "parameter_3F": "0x97"})
        self.assertEqual((s0["left_limit_D280"], s0["saved_right_limit_25_27"]), (1600, 2304))
        s2 = CE["state_2_wait_and_camera_target"]
        self.assertEqual(s2["while_child_present"]["requested"], 2)
        self.assertEqual(s2["after_child_gone"]["requested"], 3)
        self.assertEqual((s2["bottom_limit_D27E"], s2["pan_target_x_D2DA"], s2["pan_target_y_D2DC"]), (78, 1680, 78))
        s3 = CE["state_3_setup"]
        self.assertEqual((s3["D3B3"], s3["D494"], s3["D495"], s3["aux1_09"]), ("0x13", "0x20", "0x0C", "0x48"))
        self.assertEqual((s3["after"]["health"], s3["after"]["vx"], s3["after"]["requested"], s3["flags_03"]),
                         (8, -128, 18, "0x80"))


class ContactAndHealthTests(unittest.TestCase):
    def rows(self, case):
        return [m for m in CE["contact_matrix"]["cases"] if m["case"] == case]

    def test_attack_hit_in_every_patrol_state(self):
        expected = {6: 8, 9: 11, 12: 14, 15: 17}
        for r in self.rows("attack_from_left_side") + self.rows("attack_from_right_side") + self.rows("attack_from_below"):
            res = r["result"]
            self.assertEqual(res["requested"], expected[r["start_state"]])
            self.assertEqual((res["health"], res["timer_1F"], res["saved_state_0B"]), (7, 20, r["start_state"]))
            self.assertEqual((res["sound_DE04"], res["palette_command_slot_D452"], res["damage_request_D3B0"]),
                             ("0xB6", 7, "0x00"))
            self.assertEqual(res["player_requested_state_D502"], "0x1B")

    def test_knockback_by_contact_bit(self):
        by = {r["case"]: r["result"] for r in CE["contact_matrix"]["cases"] if r["start_state"] == 6}
        self.assertEqual((by["attack_from_left_side"]["contact_bits_21"], by["attack_from_left_side"]["player_vx"]), ("0x08", -1536))
        self.assertEqual((by["attack_from_right_side"]["contact_bits_21"], by["attack_from_right_side"]["player_vx"]), ("0x04", 1536))
        self.assertEqual((by["attack_from_below"]["contact_bits_21"], by["attack_from_below"]["player_vy"]), ("0x02", 1536))

    def test_top_contact_bounces_and_never_damages_the_boss(self):
        expected = {6: 7, 9: 10, 12: 13, 15: 16}
        for case in ("top_contact_attacking", "top_contact_plain"):
            for r in self.rows(case):
                res = r["result"]
                self.assertEqual(res["requested"], expected[r["start_state"]])
                self.assertEqual(res["health"], 8)
                self.assertEqual((res["contact_bits_21"], res["player_requested_state_D502"], res["sound_DE04"]),
                                 ("0x01", "0x0B", "0xA6"))
                self.assertEqual((res["player_vy"], res["D448"], res["damage_request_D3B0"]), (-1024, 0, "0x00"))

    def test_plain_contact_damages_the_player_with_two_update_cooldown(self):
        for r in self.rows("plain_side_contact"):
            res = r["result"]
            self.assertEqual((res["damage_request_D3B0"], res["cooldown_1E"], res["health"]), ("0xFF", 2, 8))
            self.assertEqual(res["palette_command_slot_D452"], 0)
        cd = CE["cooldown"]
        self.assertEqual(cd["contact_ignored_while_cooldown_active"]["contact_bits_21"], "0x00")
        self.assertEqual(cd["contact_ignored_while_cooldown_active"]["cooldown_1E"], 1)
        self.assertEqual(cd["attack_ignored_while_cooldown_active"]["health"], 8)

    def test_no_contact_far_away(self):
        for r in self.rows("no_contact"):
            self.assertEqual(r["result"]["contact_bits_21"], "0x00")
            self.assertEqual(r["result"]["health"], 8)

    def test_health_eight_hits(self):
        h = CE["health"]
        self.assertEqual(h["initial_value_state_3"], 8)
        self.assertEqual(h["countdown"], [7, 6, 5, 4, 3, 2, 1])
        last = h["last_hit_from_1"]
        self.assertEqual((last["health"], last["requested"]), (0, 4))
        self.assertEqual(h["hit_in_state_18_does_not_change_health"], 8)
        for r in CE["contact_state_18"]:
            self.assertEqual((r["result"]["requested"], r["result"]["health"]), (18, 8))
        by = {r["case"]: r["result"] for r in CE["contact_state_18"]}
        self.assertEqual(by["plain_side_contact"]["damage_request_D3B0"], "0xFF")
        self.assertEqual(by["attack_from_left_side"]["player_requested_state_D502"], "0x1B")

    def test_reaction_states_last_20_updates_and_return(self):
        rows = {r["state"]: r for r in CE["reaction_states"]}
        for state, saved in ((7, 6), (8, 6), (10, 9), (11, 9), (13, 12), (14, 12), (16, 15), (17, 15)):
            self.assertEqual(rows[state]["saved_state"], saved)
            self.assertEqual(rows[state]["updates_until_return"], 20, state)
            self.assertEqual(rows[state]["end"]["requested"], saved)
        for state in (8, 11, 14, 17):                       # damaged: frozen, velocity cleared, accelerate phase
            self.assertEqual(rows[state]["x_end"] - rows[state]["x_moved_from"] in (0, -1), True)
            self.assertEqual(rows[state]["end"]["phase_32"], 1)
        for state in (7, 10, 13, 16):                       # bounce: keeps moving
            self.assertGreater(abs(rows[state]["x_end"] - rows[state]["x_moved_from"]), 5)


class SpawnAndCompletionTests(unittest.TestCase):
    def test_state_4_spawns_and_length(self):
        d = CE["state_4_defeat"]
        offsets = [(e["dx"], e["dy"]) for e in d["spawn_events"]]
        self.assertEqual(offsets, [(-8, 0), (8, 0), (0, -16), (-8, -24), (-8, -24)])
        self.assertEqual({e["type"] for e in d["spawn_events"]}, {"0x34"})
        self.assertEqual({e["parameter_3F"] for e in d["spawn_events"]}, {"0x04"})
        self.assertEqual([e["update"] for e in d["spawn_events"]], [1, 1, 2, 3, 4])
        self.assertEqual(d["update_state_5_reached"], 148)
        s4 = [e for e in STATES[4]["script"] if e["op"] == "spawn"]
        self.assertEqual([(e["dx"], e["dy"], e["type"], e["parameter"]) for e in s4],
                         [(-8, 0, "0x34", "0x04"), (8, 0, "0x34", "0x04"), (0, -16, "0x34", "0x04"),
                          (-8, -24, "0x34", "0x04"), (-8, -24, "0x34", "0x04")])
        loops = [e for e in STATES[4]["script"] if e["op"] == "set_loop_counter"]
        self.assertEqual(loops[0]["count"], 24)

    def test_state_5_completion_requires_floor(self):
        no_floor, floor, act1 = CE["state_5_completion"]
        self.assertEqual((no_floor["slot_type"], no_floor["slot_state"]), ("0x50", 5))
        self.assertEqual(no_floor["child_type_0A_slots"], [])
        self.assertEqual((floor["slot_type"], floor["slot_state"], floor["slot_token_3E"], floor["slot_param_3F"]),
                         ("0x0F", 0, 0, 0))
        self.assertEqual(floor["player_requested_state_D502"], "0x20")
        self.assertEqual(floor["sound_DE04"], "0x97")
        self.assertEqual(act1["sound_DE04"], "0x89")
        self.assertEqual(floor["right_limit_D282"], 2304)
        self.assertEqual((floor["D15E"], floor["D15F"]), ("0x80", "0x00"))
        self.assertEqual(len(floor["child_type_0A_slots"]), 1)
        self.assertEqual(floor["child_type_0A_slots"][0][1], 0)
        self.assertEqual(floor["occupancy_byte_D400"], "0x50")            # never re-created

    def test_no_score_for_type_50_but_score_for_type_21(self):
        boss, ordinary = CE["score_gate_5F54"]
        self.assertEqual((boss["type"], boss["slot_type_after"]), ("0x50", "0x0F"))
        self.assertEqual(boss["ram_changed_outside_slot"], ["0xD12B"])          # only the harness bank variable
        self.assertIn("0xD29D", ordinary["ram_changed_outside_slot"])           # score byte changes for type $21

    def test_offscreen_removal_only_without_keep_alive(self):
        a, b = CE["offscreen_removal"]
        self.assertEqual((a["type_after"], a["state_after"]), ("0xFE", 0))
        self.assertEqual(b["type_after"], "0x50")

    def test_palette_flash_command(self):
        seq = CE["palette_flash_command_7"]["per_call_D48F_D490_step_counter"]
        writes = [(i, s[0], s[1]) for i, s in enumerate(seq) if s[0] or s[1]]
        self.assertEqual(writes[0], (3, 63, 63))          # white on the 4th call
        self.assertEqual(writes[-1][1:], (53, 32))        # back to the normal colours 4 calls later


class GraphicsTests(unittest.TestCase):
    def test_dynamic_art_source(self):
        a = D["graphics"]["art_source"]
        self.assertTrue(a["resolved"])
        dl = a["dynamic_load"]
        self.assertEqual((dl["selector"], dl["list_cpu"]), ("0x13", "0x7BD8"))
        got = [(l["bank"], l["source_cpu"], l["source_rom"], l["tile_count"], l["vram_destination"],
                l["first_tile"], l["last_tile"], l["bit_reversed_copy"]) for l in dl["loads"]]
        self.assertEqual(got, [("0x0A", "0x8940", "0x28940", 72, "0x05C0", "0x2E", "0x75", False),
                               ("0x0A", "0x8940", "0x28940", 44, "0x0EC0", "0x76", "0xA1", True),
                               ("0x09", "0xABA0", "0x26BA0", 12, "0x1440", "0xA2", "0xAD", False)])
        self.assertEqual(a["tile_base_mirrored_plus_09"].split()[0], "0x48")

    def test_palette(self):
        p = D["graphics"]["palette"]
        self.assertEqual((p["boss_sprite_palette_index"], p["boss_sprite_palette_rom"]), ("0x0C", "0x3B70D"))
        self.assertEqual((p["level_sprite_palette_index"], p["level_sprite_palette_rom"]), ("0x06", "0x3B6AD"))
        self.assertEqual(sorted(p["differs_at_colors"]), ["13", "14", "15"])
        self.assertTrue(EM["unattended_intro_and_patrol"]["sprite_cram_after_state_3_equals_palette_0C"])

    def test_reachable_frames_and_orientation(self):
        g = D["graphics"]
        self.assertEqual(g["reachable_frames"], [0, 1, 2, 3, 4, 5, 6])
        o = g["frames_by_orientation"]
        self.assertEqual(o["normal_frames"], [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(o["mirrored_frames"], [1, 2, 3, 4])
        self.assertEqual({n: v["orientation"] for n, v in o["per_state"].items() if v["orientation"] == "mirrored"},
                         {"12": "mirrored", "13": "mirrored", "14": "mirrored"})
        self.assertEqual(STATES[6]["frames_reached"], [1, 2])
        self.assertEqual(STATES[7]["frames_reached"], [1, 2, 3, 4])
        self.assertEqual(STATES[9]["frames_reached"], [5])
        self.assertEqual(STATES[10]["frames_reached"], [5, 6])
        self.assertEqual(STATES[18]["frames_reached"], [1, 2])
        for n in (0, 1, 2, 3, 4, 5):
            self.assertEqual(STATES[n]["frames_reached"], [0])

    def test_frame_geometry(self):
        frames = D["graphics"]["frames"]
        self.assertEqual(frames[0]["piece_count"], 0)
        for f in frames[1:]:
            self.assertEqual(f["piece_count"], 13)
            self.assertEqual((f["contact_extent_x_plus_2C"], f["contact_extent_y_plus_2D"]), (20, 48))
            self.assertEqual(f["bounds_unmirrored"], {"min_x": -20, "max_x_exclusive": 20, "min_y": -48, "max_y_exclusive": 0})
            self.assertEqual(f["bounds_mirrored"], {"min_x": -20, "max_x_exclusive": 20, "min_y": -48, "max_y_exclusive": 0})
        # frames 5/6 do not fit the 44-tile mirrored copy; frames 1-4 do
        use = D["graphics"]["tile_usage"]
        for n in ("1", "2", "3", "4"):
            self.assertTrue(use[n]["fits_mirrored_copy_46_to_89"], n)
        for n in ("5", "6"):
            self.assertFalse(use[n]["fits_mirrored_copy_46_to_89"], n)

    def test_animation_records(self):
        def recs(n):
            return [(e["duration"], e["frame"], e["callback"]) for e in STATES[n]["script"] if e["op"] == "record"]
        self.assertEqual(recs(6), [(16, 1, "0x985B"), (16, 2, "0x985B")])
        self.assertEqual(recs(12), [(16, 1, "0x985B"), (16, 2, "0x985B")])
        self.assertEqual(recs(18), [(16, 1, "0x9A09"), (16, 2, "0x9A09")])
        self.assertEqual(recs(8), [(4, 1, "0x9997"), (4, 2, "0x9997")])
        self.assertEqual(recs(9), [(8, 5, "0x9903")])
        self.assertEqual(recs(15), [(8, 5, "0x9931")])
        self.assertEqual(recs(0), [(224, 0, "0x974C")])
        self.assertEqual(STATES[0]["script"][0], {"cpu": "0x95B1", "cmd": "0x06", "op": "sound", "sound": "0x8C"})

    def test_game_sat_matches_decoded_frame(self):
        c = EM["sat_comparison_state_6"]
        self.assertTrue(c["all_found"])
        self.assertEqual((c["expected_entries"], c["found_in_game_sat"]), (13, 13))


class EmulatedTimelineTests(unittest.TestCase):
    def ev(self, name):
        return EM[name]["events"]

    def test_intro_timeline(self):
        by = {(e["state"], e["requested"]): e["frame_index"] for e in reversed(self.ev("unattended_intro_and_patrol"))}
        self.assertEqual(by[(0, 1)], 5)
        self.assertEqual(by[(1, 2)], 10)
        self.assertEqual(by[(2, 3)], 105)
        self.assertEqual(by[(18, 6)], 177)
        intro = EM["unattended_intro_and_patrol"]
        self.assertEqual((intro["dynamic_art_requested_at_frame"], intro["dynamic_art_finished_at_frame"]), (106, 138))
        self.assertEqual(intro["sound_requests"][:2], [[0, "0x81"], [5, "0x8C"]])
        e106 = next(e for e in intro["events"] if e["frame_index"] == 106)
        self.assertEqual(e106["limits_left_right_bottom"], [1600, 1680, 78])

    def test_eight_hit_defeat(self):
        d = EM["eight_hit_defeat"]
        hp = [e["health"] for e in d["events"] if e["state"] == 6 and e["requested"] == 8]
        self.assertEqual(hp, [7, 6, 5, 4, 3, 2, 1])
        self.assertEqual([e["health"] for e in d["events"] if e["state"] == 6 and e["requested"] == 4], [0])
        self.assertEqual((d["state_4_frame"], d["state_5_frame"]), (356, 504))
        hits = [e["frame_index"] for e in d["events"] if e["requested"] == 8 and e["state"] == 6]
        self.assertEqual(hits, [201, 223, 245, 267, 289, 311, 333])
        self.assertEqual(sum(1 for s in d["sound_requests"] if s[1] == "0xB6"), 1)   # de-duplicated log; one per hit in the raw log
        self.assertEqual([c[1:2] for c in d["children_type_34_first_seen"]], [[356], [357], [358], [359], [360]])

    def test_defeat_and_completion_frames(self):
        a = EM["eight_hit_defeat"]["after_defeat"]
        self.assertEqual((a["frame_index"], a["slot_D700_type"]), (506, "0x0F"))
        self.assertEqual(a["player_requested_state"], 32)
        self.assertEqual(a["limits_left_right_bottom"], [1679, 2304, 78])
        self.assertEqual(a["occupancy_D400"], "0x50")
        types = sorted(t for _, t in a["objects"])
        self.assertIn("0x0A", types)
        self.assertEqual((a["act_complete_flag_set_at_frame"], a["act_complete_flag_bit"]), (687, 4))
        self.assertEqual(a["frames_defeat_to_flag"], 181)
        self.assertEqual(a["next_zone_act_after_completion"], [1, 0])
        self.assertEqual(a["frames_defeat_to_next_zone"], 1041)
        sounds = [s[1] for s in EM["eight_hit_defeat"]["sound_requests"]]
        self.assertIn("0x97", sounds)

    def test_hit_flash_in_game(self):
        flash = EM["eight_hit_defeat"]["sprite_palette_colors_13_14_changes"]
        self.assertIn([205, 63, 63], flash)
        self.assertIn([209, 53, 32], flash)


class IdentityAndControlTests(unittest.TestCase):
    def test_boss_verdict_is_backed_by_evidence(self):
        self.assertEqual(D["identity"]["classification"].split()[0], "boss")
        self.assertGreaterEqual(len(D["identity"]["evidence"]), 6)

    def test_control_summary(self):
        c = D["camera_and_level_control"]
        self.assertIn("none", c["player_lockout"])
        self.assertIn("$8C", c["music"])
        self.assertIn("$D293", c["act_complete"])
        self.assertIn("none found", c["terrain_mutation"])
        self.assertEqual(D["collision_and_damage"]["health"],
                         {"initial": 8, "decrement": 1, "storage": "+$26", "zero_action": "request state 4",
                          "hits_required": 8, "damage_by_top_contact": 0})

    def test_unresolved_and_follow_ups_are_recorded(self):
        self.assertTrue(any("$12" in x for x in D["unresolved"]))
        tasks = " ".join(t["task"] for t in D["follow_up_tasks"])
        for t in ("$12", "$34", "$0A", "$0F"):
            self.assertIn(t, tasks)


@unittest.skipIf(matching_rom() is None, "matching ROM not available (set SONIC_CHAOS_ROM)")
class RomBackedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = matching_rom().read_bytes()

    def test_rom_is_byte_identical_reference(self):
        self.assertEqual(len(self.rom), 524288)
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(), ROM_SHA)

    def test_routine_hashes_match_rom(self):
        for r in D["routines"]:
            off = int(r["rom_offset"], 16)
            raw = self.rom[off:off + r["length"]]
            self.assertEqual(hashlib.sha256(raw).hexdigest(), r["sha256"], r["name"])
            self.assertEqual(raw[:16].hex(), r["first_16_bytes"], r["name"])

    def test_placement_state_table_and_mapping_from_rom(self):
        self.assertEqual(self.rom[0x708FE:0x70907].hex(" ").upper(), D["placement"]["raw_bytes"])
        self.assertEqual(int.from_bytes(self.rom[0x6658:0x665A], "little"), 0x958B)
        table = [int.from_bytes(self.rom[0x7958B + 2 * i:0x7958D + 2 * i], "little") for i in range(19)]
        self.assertEqual([f"0x{x:04X}" for x in table], D["dispatch"]["state_script_cpus"])
        self.assertEqual(int.from_bytes(self.rom[0x3C0A0:0x3C0A2], "little"), 0x94C6)

    def test_static_regeneration_is_identical(self):
        fresh = tool.build(self.rom, static_only=True)
        for key, value in fresh.items():
            self.assertEqual(value, D[key], key)

    def test_controlled_execution_regenerates_identically(self):
        self.assertEqual(tool.fixtures(self.rom), D["controlled_execution"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

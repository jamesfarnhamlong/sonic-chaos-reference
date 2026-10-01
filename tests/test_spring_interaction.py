#!/usr/bin/env python3
"""Spring interaction audit: cache-driven tests (no ROM) plus ROM-backed controlled sweeps.

The ROM-backed class re-runs the original routines on seeds, positions and layouts that are NOT the ones used to build
the cache (random objects, random cells of every act, random flags) and compares them with the recovered rules in
tools/spring_interaction.py. It skips without the ROM (set SONIC_CHAOS_ROM).
"""
import hashlib
import importlib.util
import json
import os
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
CACHE = ROOT / "data" / "rom-cache" / "spring-interaction.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("spring_interaction", ROOT / "tools" / "spring_interaction.py")
si = importlib.util.module_from_spec(spec)
spec.loader.exec_module(si)


def matching_rom():
    candidates = []
    if os.environ.get("SONIC_CHAOS_ROM"):
        candidates.append(Path(os.environ["SONIC_CHAOS_ROM"]))
    candidates += [ROOT.parent / "Sonic Chaos (Europe).sms", ROOT.parent / "source" / "Sonic Chaos (Europe).sms", ROOT / "Sonic Chaos (Europe).sms"]
    for path in candidates:
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == ROM_SHA:
            return path
    return None


ROM = matching_rom()
ROM_BYTES = ROM.read_bytes() if ROM else None


def hx(s):
    return int(s, 16)


class ProvenanceTests(unittest.TestCase):
    def test_header(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertTrue(D["research_only"] and D["poc_untouched"])
        self.assertEqual(D["machine_facing_label"], "spring_interaction")
        self.assertFalse(D["static_only"])

    def test_routines_hashed_and_no_rom_dump(self):
        self.assertGreaterEqual(len(D["routines"]), 25)
        for r in D["routines"]:
            self.assertEqual(len(r["sha256"]), 64)
            self.assertLessEqual(len(r["first_16_bytes"]), 32)

    def test_terrain_handler_table(self):
        rows = {r["type"]: r for r in D["terrain_handler_table"]}
        self.assertEqual(len(rows), 32)
        self.assertEqual(rows["0x09"]["handler"], "0x6A75")
        self.assertEqual(rows["0x14"]["handler"], "0x6A90")
        self.assertEqual(rows["0x12"]["handler"], "0x69B2")


class Type26Tests(unittest.TestCase):
    def test_contact_geometry(self):
        g = D["type26_geometry"]
        self.assertEqual(g["horizontal_pass_dx_ranges"], [[-11, 11]])
        self.assertEqual(g["vertical_pass_ranges_relative_to_object_y"], [[-33, -28]])
        self.assertEqual(g["model_mismatches"], 0)
        self.assertEqual({e["dx"]: e["launch"] for e in g["horizontal_edges"]}, {-13: False, -12: False, -11: True, -10: True, 10: True, 11: True, 12: False, 13: False})
        self.assertEqual({e["player_y_minus_object_y"]: e["launch"] for e in g["vertical_edges"]},
                         {-35: False, -34: False, -33: True, -32: True, -29: True, -28: True, -27: False, -26: False})

    def test_gates(self):
        g = D["type26_gates"]
        self.assertEqual(g["requested_state_$D502_blocking"], ["0x21"])
        self.assertEqual(g["current_state_$D501_blocking"], [])
        for v, ok in g["vy_raw_to_launch"].items():
            self.assertEqual(ok, hx(v) < 0x8000, v)
        for v, ok in g["floor_flag_$D522"].items():
            self.assertEqual(ok, bool(hx(v) & 2), v)
        for v, ok in g["object_flags_+4"].items():
            self.assertEqual(ok, not hx(v) & 0x40, v)
        self.assertTrue(all(g["player_f3_+3"].values()))

    def test_span_triggers(self):
        s = D["type26_span"]
        self.assertEqual(s["x_pass_ranges_relative_to_x0"], [[0, 159]])
        self.assertEqual(s["y_pass_ranges_relative_to_object_y"], [[-47, 47]])
        self.assertEqual(s["model_mismatches"], 0)
        self.assertEqual(s["gates"], {"vy_negative": False, "vy_zero": True, "no_floor_flag": False, "requested_21": False, "current_21": True})
        self.assertEqual(s["next_state"], 9)
        self.assertEqual(s["object_x_after_trigger"], 1296)
        by = {(r["p3f"], r["aux1"]): r for r in s["state9_launch"]}
        self.assertEqual(by[(0, "0x72")]["vy"], "0xF8A0")
        self.assertEqual(by[(1, "0x72")]["vy"], "0xFB00")
        self.assertEqual(by[(1, "0x00")]["next_object_state"], 1)
        self.assertEqual(by[(1, "0x72")]["next_object_state"], 3)
        self.assertEqual(s["state9_with_negative_vy"]["requested_player_state"], "0x05")
        self.assertEqual(s["state9_with_negative_vy"]["d448"], "0x00")

    def test_parameter_semantics(self):
        for r in D["type26_parameters"]["rows"]:
            p, aux = hx(r["parameter"]), hx(r["aux1"])
            init = r["after_init"]
            if p & 0x80:
                self.assertEqual(init["state"], 8)
                self.assertEqual(init["span"], (p & 0x7F) * 16)
                self.assertEqual(init["p3f"], 1 if aux else 0)
                strong = not aux
            else:
                self.assertEqual(init["state"], 7)
                self.assertEqual(init["span"], 0)
                self.assertEqual(init["p3f"], p)
                strong = p == 0
            self.assertEqual(init["y"], 712)   # +12 shift of a 700 placement
            if init["span"] or not p & 0x80:
                self.assertTrue(r["triggered"], r)
                self.assertEqual(r["launch_vy"], "0xF8A0" if strong else "0xFB00")
                self.assertEqual(r["d448"], "0xFF" if strong else "0x00")
                self.assertEqual(r["player_requested_state"], "0x0B")
                self.assertEqual(r["player_f3_after"], 1)
            else:
                self.assertFalse(r["triggered"])   # span 0 never matches the empty interval

    def test_canonical_placements(self):
        counts = {a: len(D["type26_placements"][a]) for a in D["type26_placements"]}
        self.assertEqual(counts, {"thz1": 4, "thz2": 10, "thz3": 4})
        for act, rows in D["type26_placements"].items():
            for r in rows:
                p = hx(r["parameter"])
                self.assertEqual(r["rest_y"], r["world_y"] + 12)
                self.assertEqual(r["contact_player_y_window_inclusive"], [r["rest_y"] - 33, r["rest_y"] - 28])
                self.assertEqual(r["contact_player_y_window_relative_to_placement"], [-21, -16])
                self.assertEqual(r["span_width_px"], (p & 0x7F) * 16 if p & 0x80 else None)
                self.assertEqual(r["strong"], (p == 0) if not p & 0x80 else False)
        thz1 = {(r["world_x"], r["world_y"]): r["parameter"] for r in D["type26_placements"]["thz1"]}
        self.assertEqual(thz1, {(688, 864): "0x00", (3568, 768): "0x00", (1296, 608): "0x8A", (1912, 864): "0x01"})
        thz2 = {(r["world_x"], r["world_y"]): r for r in D["type26_placements"]["thz2"]}
        self.assertEqual(thz2[(1504, 896)]["span_width_px"], 128)
        self.assertEqual(thz2[(1504, 896)]["span_x_interval_inclusive_exclusive"], [1504, 1632])
        self.assertEqual(thz2[(3472, 288)]["parameter"], "0x01")

    def test_state_matrix_and_script_table(self):
        m = D["type26_state_matrix"]
        self.assertEqual(m["blocked"], ["0x21"])
        self.assertEqual(len(m["requested_state_launches"]), 64)
        recs = {s["state"]: s for s in D["type26_script_table"]["states"]}
        self.assertEqual([recs[i]["records"][0]["callback"] for i in range(10)],
                         ["0x825A", "0x8312", "0x833A", "0x837C", "0x83A4", "0x8349", "0x8349", "0x82AF", "0x83BF", "0x8401"])

    def test_emulated_cycle(self):
        c = D["emulated_type26_cycle"]["rows"]
        self.assertEqual(c["strong_(688,864)"]["retrigger_free_updates"], 42)
        self.assertEqual(c["weak_(1912,864)"]["retrigger_free_updates"], 20)
        ys = [t["object_y"] for t in c["strong_(688,864)"]["timeline"][:7]]
        self.assertEqual(ys, [864, 876, 876, 869, 862, 855, 848])


class TerrainTests(unittest.TestCase):
    def test_models_match_original(self):
        for key in ("terrain_upright", "terrain_diagonal_right_launch", "terrain_diagonal_left_launch"):
            self.assertEqual(D[key]["model_mismatches"], 0, key)
            self.assertGreater(D[key]["cases"], 40000)
        self.assertEqual(D["terrain_horizontal"]["cases"] > 40000, True)
        for blk, res in D["terrain_horizontal"]["blocks"].items():
            for side, r in res.items():
                self.assertEqual(r["model_mismatches"], 0, (blk, side))
        for blk in ("0x3A", "0x3B", "0x36", "0x38"):
            self.assertEqual(D["terrain_ceiling"][blk]["model_mismatches"], 0, blk)

    def _rows(self, key):
        return {(r["previous_surface"], r["floor_flag"], r["vy_hi"]): r for r in D[key]["rows"]}

    def test_upright_regions(self):
        rows = self._rows("terrain_upright")
        for vy in (0, 1, 3):
            self.assertEqual(rows[("none", 1, vy)]["cell_x_ranges"], [[0, 31]])
            self.assertEqual(rows[("none", 1, vy)]["probe_y_ranges_relative_to_cell"], [[0, 31]])
            self.assertEqual(rows[("none", 0, vy)]["cell_x_ranges"], [])
            self.assertEqual(rows[("solid", 0, vy)]["probe_y_ranges_relative_to_cell"], [[16, 31]])
            self.assertEqual(rows[("one_way", 1, vy)]["probe_y_ranges_relative_to_cell"], [[16, 24 + vy]])
            self.assertEqual(rows[("upright_spring_self", 0, vy)]["probe_y_ranges_relative_to_cell"], [[16, 24 + vy]])
            self.assertEqual(rows[("solid_and_one_way", 1, vy)]["probe_y_ranges_relative_to_cell"], [[0, 31]])

    def test_diagonal_regions_follow_the_spring_half(self):
        right = self._rows("terrain_diagonal_right_launch")
        left = self._rows("terrain_diagonal_left_launch")
        for vy in (0, 1, 3):
            self.assertEqual(right[("one_way", 1, vy)]["cell_x_ranges"], [[0, 15]])
            self.assertEqual(left[("one_way", 1, vy)]["cell_x_ranges"], [[16, 31]])
            self.assertEqual(right[("solid", 0, vy)]["cell_x_ranges"], [[0, 15]])
            self.assertEqual(left[("solid", 0, vy)]["cell_x_ranges"], [[16, 31]])
            self.assertEqual(right[("solid", 1, vy)]["cell_x_ranges"], [[0, 31]])
            self.assertEqual(right[("diagonal_spring_self", 0, vy)]["probe_y_ranges_relative_to_cell"], [[16, 24 + vy]])

    def test_gates(self):
        g = D["terrain_gates"]
        for name in ("upright_blk30", "diagonal_right_blk36", "diagonal_left_blk38"):
            r = g[name]
            self.assertFalse(r["vy_8000"]["launched"] or r["vy_FF00"]["launched"] or r["vy_FFFF"]["launched"])
            self.assertTrue(r["vy_0000"]["launched"] and r["vy_0001"]["launched"] and r["vy_0100"]["launched"])
            self.assertEqual({k for k, v in r["current_state_launches"].items() if not v}, {"0x11"})
            self.assertTrue(all(r["requested_state_launches"].values()))
        up = g["upright_blk30"]["vy_0100"]
        self.assertEqual((up["vy"], up["d448"]), ("0xF880", 255))
        dr, dl = g["diagonal_right_blk36"], g["diagonal_left_blk38"]
        self.assertEqual((dr["vy_0100"]["vx"], dr["vy_0100"]["vy"], dr["vy_0100"]["d448"]), ("0x0400", "0xF900", 0))
        self.assertEqual((dl["vy_0100"]["vx"], dl["vy_0100"]["vy"], dl["vy_0100"]["f4"]), ("0xFC00", "0xF900", 16))
        self.assertEqual(dr["vy_FF00"]["vx"], "0x0400")           # vx is written before the Y-speed gate
        self.assertEqual(g["diagonal_y_speed_by_$D297"], {"0": "0xF900", "1": "0xFA80", "2": "0xFA80", "3": "0xFA80", "4": "0xFA80", "5": "0xFA80", "6": "0xFA80", "7": "0xFA80"})

    def test_horizontal(self):
        hz = D["terrain_horizontal"]
        left_half = hz["blocks"]["thz1:0x33@(3200,832)"]
        self.assertEqual(left_half["right_probe_$716B"]["vx"], ["0xFA00"])
        self.assertEqual(left_half["left_probe_$7210"]["vx"], ["0x0600"])
        self.assertEqual(left_half["right_probe_$716B"]["player_y_ranges_relative_to_cell"], [[2, 21]])
        self.assertEqual(left_half["right_probe_$716B"]["player_x_ranges_relative_to_cell"], [[-9, 6]])   # probe X +9 -> columns 0..15
        self.assertEqual(left_half["left_probe_$7210"]["player_x_ranges_relative_to_cell"], [[9, 24]])    # probe X -9 -> columns 0..15
        right_half = hz["blocks"]["thz2:0x34@(3264,256)"]
        self.assertEqual(right_half["right_probe_$716B"]["player_x_ranges_relative_to_cell"], [[7, 22]])  # columns 16..31
        for res in hz["blocks"].values():
            for r in res.values():
                self.assertEqual(r["cap_D373"], ["0x0600"])
                self.assertEqual(r["f3_after"], [2])
        g = hz["gates"]
        self.assertTrue(all(g[k]["launched"] for k in ("baseline", "requested_state_11", "airborne_no_floor_flag", "vy_negative", "vy_positive", "f3_airborne")))
        self.assertFalse(g["current_state_11"]["launched"])
        self.assertEqual(g["baseline"]["d448"], 85)       # untouched fixture value
        self.assertTrue(all(r["launched"] for r in D["emulated_horizontal"]["rows"]))

    def test_ceiling_blocks(self):
        c = D["terrain_ceiling"]
        for blk in ("0x3A", "0x3B"):
            self.assertEqual(c[blk]["cell_x_ranges"], [[0, 31]])
            self.assertEqual(c[blk]["probe_y_ranges_relative_to_cell"], [[0, 16]])
        self.assertEqual(c["0x36"]["cells_hit"] + c["0x38"]["cells_hit"], 0)
        self.assertEqual(c["launch_0x3A"], {"state": "0x1B", "vx": "0x0400", "vy": "0x0580", "f3": 3, "fl22": "0x01", "sound": "0xA6"})
        self.assertEqual(c["gates"], {"vy_zero": False, "vy_positive": False, "vy_negative": True, "floor_flag": False, "underwater_flag_D3C0_vy0": True})
        cells = [x for a in D["terrain_spring_cells"].values() for x in a]
        self.assertFalse([x for x in cells if x["kind"] == "ceiling_spring"])

    def test_block_census(self):
        cells = D["terrain_spring_cells"]
        count = {a: {} for a in cells}
        for a, rows in cells.items():
            for r in rows:
                count[a][r["kind"]] = count[a].get(r["kind"], 0) + 1
        self.assertEqual(count["thz1"], {"upright": 2, "horizontal_left_half": 1, "diagonal_right_launch": 4, "diagonal_left_launch": 2})
        self.assertEqual(count["thz2"].get("upright"), 2)
        self.assertEqual(count["thz2"].get("diagonal_right_launch"), 2)
        self.assertEqual(count["thz3"].get("upright"), 2)
        self.assertEqual(count["thz3"].get("diagonal_right_launch"), 1)

    def test_launch_table(self):
        rows = {r["mechanism"]: r for r in D["launch_table"]["rows"]}
        up = rows["terrain upright (type 9) $6A75"]
        self.assertEqual((up["after"]["req"], up["after"]["vy"], up["after"]["vx"], up["after"]["f3"], up["after"]["d448"]), (0x0B, "0xF880", "0x0123", 1, 0xFF))
        dg = rows["terrain diagonal, block < $38 $6A90"]["after"]
        self.assertEqual((dg["req"], dg["vx"], dg["vy"], dg["f3"], dg["d448"]), (0x1C, "0x0400", "0xF900", 3, 0))
        hz = rows["setter $4868 (right probe), HL=$FA00"]["after"]
        self.assertEqual((hz["req"], hz["vx"], hz["cap"], hz["f3"]), (9, "0xFA00", "0x0600", 2))
        self.assertEqual(rows["setter $480C with negative Y speed"]["after"]["req"], 10)
        self.assertEqual(rows["setter $4868 with negative Y speed"]["after"]["req"], 9)
        for k in ("type $26 fixed strong (parameter $00) $82AF", "type $26 fixed weak (parameter $01) $82AF"):
            self.assertEqual(rows[k]["after"]["vx"], "0x0123")
            self.assertEqual(rows[k]["after"]["cap"], "0x0555")


class AttackAndStateTests(unittest.TestCase):
    def test_badnik_attack_gate_is_the_rolling_flag(self):
        a = D["attack_state"]
        for f3, conv in a["type_27_$5F3D_converts_by_D503"].items():
            self.assertEqual(conv, bool(hx(f3) & 2), f3)
        self.assertTrue(a["type_27_converts_with_D532_6"])
        t = a["type_21_$B2B2_tail"]
        for f3 in range(4):
            self.assertEqual(t[f"D503={f3}_beside"]["converted_to_0F"], bool(f3 & 2))
            self.assertEqual(t[f"D503={f3}_above"]["player_requested_state"], "0x0B")      # top contact is a stomp whatever the flags
            self.assertFalse(t[f"D503={f3}_above"]["converted_to_0F"])

    def test_flight_flags(self):
        flights = {r["case"]: r for r in D["emulated_flights"]["rows"]}

        def seg(case, state):
            return [s for s in flights[case]["segments"] if s["state"] == state]
        for case in ("type26_strong_(688,864)", "type26_weak_(1912,864)", "type26_span_8A_(1296,608)", "terrain_upright_(928,640)"):
            for st in ("0x0B", "0x0E"):
                for s in seg(case, st):
                    self.assertEqual(s["f3"] & 3, 1, (case, st))                  # airborne, NOT rolling/attacking
        for case in ("terrain_diagonal_right_(2464,256)", "terrain_diagonal_left_(1664,512)"):
            s1c = seg(case, "0x1C")
            self.assertTrue(s1c)
            self.assertTrue(all(s["f3"] & 3 == 3 for s in s1c))                   # airborne AND attacking
            self.assertTrue(all(s["f3"] & 3 == 1 for s in seg(case, "0x0E")[:1]))  # apex request clears bit 1
        self.assertTrue(all(s["f3"] & 3 == 2 for s in seg("terrain_horizontal_(3200,832)_run_left", "0x09")))
        self.assertTrue(all(s["f3"] & 3 == 3 for s in seg("normal_jump_run_then_jump", "0x0A")))
        self.assertTrue(all(s["f3"] & 3 == 2 for s in seg("roll_run_then_down", "0x09")))
        jump = flights["jump_into_terrain_upright_(928,640)"]["segments"]
        order = [(s["state"], s["f3"] & 3) for s in jump if s["state"] in ("0x0A", "0x0B")]
        self.assertEqual(order[:2], [("0x0A", 3), ("0x0B", 1)])          # an attacking jump becomes a non-attacking spring flight

    def test_d448(self):
        d = D["d448"]
        self.assertEqual(d["occurrences_of_address_bytes"], ["0x06A87", "0x06AC8", "0x3018F", "0x332CC", "0x782F8", "0x78420", "0x799CA"])
        self.assertTrue(d["consistent_with_previous_audit"])
        flights = {r["case"]: r for r in D["emulated_flights"]["rows"]}
        self.assertEqual([s["d448"] for s in flights["type26_strong_(688,864)"]["segments"] if s["state"] == "0x0B"], ["0xFF"])
        self.assertEqual([s["d448"] for s in flights["type26_weak_(1912,864)"]["segments"] if s["state"] == "0x0B"][0], "0x00")
        # persists through landing in the emulator (the strong value is still there after the state returns to 5/1)
        self.assertEqual(flights["type26_strong_(688,864)"]["segments"][-1]["d448"], "0xFF")

    def test_emulated_placements_all_launch(self):
        rows = D["emulated_placements"]["rows"]
        self.assertTrue(all(r["launched"] for r in rows))
        t26 = [r for r in rows if r["kind"] == "type26"]
        self.assertEqual(len(t26), 18)
        for r in t26:
            p = hx(r["parameter"])
            strong = p == 0
            self.assertEqual(r["vy"], -7.375 if strong else -5.0)
            self.assertEqual(r["d448"], "0xFF" if strong else "0x00")
        for r in rows:
            if r["kind"] == "upright":
                self.assertEqual((r["state"], r["vy"], r["d448"]), ("0x0B", -7.5, "0xFF"))
            if r["kind"].startswith("diagonal"):
                self.assertEqual((r["state"], r["vy"], r["d448"], abs(r["vx"])), ("0x1C", -7.0, "0x00", 4.0))
                self.assertEqual(r["vx"] > 0, r["kind"] == "diagonal_right_launch")

    def test_state_reach_reuses_terrain_ring_cache(self):
        sr = D["state_reach"]["state_reach"]
        self.assertTrue(sr)


class TopOfScreenTests(unittest.TestCase):
    def test_death_rule(self):
        b = D["death_boundary"]
        for r in b["rows"]:
            self.assertEqual(r["died"], 208 <= r["screen_y_$D51C"] <= 32767, r)
        self.assertEqual(b["first_fatal_screen_y_in_sample"], 208)

    def test_original_never_kills_above_the_top(self):
        t = D["emulated_top_of_screen"]
        self.assertFalse(t["died"])
        self.assertLess(t["min_signed_world_y"], -1000)
        self.assertEqual(t["camera_y_final"], 8)
        for r in t["rows"]:
            self.assertFalse(r["life_lost_flag_D293_bit2"])
            self.assertNotEqual(r["state"], "0x1F")

    def test_canonical_flights_stay_inside_the_view(self):
        rows = [r for r in D["emulated_placements"]["rows"] if r["act"] == "thz1"]
        for r in rows:
            self.assertFalse(r.get("died"))
            self.assertGreaterEqual(r.get("min_screen_y", 99), 20)
        thz1_apex = min(r.get("apex_y_within_flight", r.get("apex_y")) for r in rows)
        self.assertGreaterEqual(thz1_apex, 127)          # the highest canonical THZ1 apex: world Y 127, well below the level top
        for r in D["emulated_placements"]["rows"]:
            self.assertFalse(r.get("died"))


@unittest.skipUnless(ROM_BYTES, "matching ROM not available (set SONIC_CHAOS_ROM)")
class RomBackedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lab = si.Lab(ROM_BYTES)

    def test_static_sections_match_the_rom(self):
        built = si.build(ROM_BYTES, static_only=True)
        for k in ("routines", "terrain_handler_table", "terrain_blocks", "terrain_spring_cells", "type26_placements", "type26_script_table", "d448"):
            self.assertEqual(built[k], D[k], k)

    def test_type26_contact_random(self):
        rng = random.Random(26_001)
        lab = self.lab
        for _ in range(4000):
            ox, oy = rng.randrange(200, 3500), rng.randrange(200, 1000)
            px, py = ox + rng.randrange(-16, 17), oy - 28 + rng.randrange(-12, 8)
            vy = rng.choice([0, 1, 0x80, 0xFF, 0x100, 0x7FFF, 0x8000, 0xFF00, 0xFFFF])
            floor, req = rng.random() < 0.8, rng.choice([5, 9, 0x0A, 0x0C, 0x13, 0x20, 0x21, 0x22])
            f4 = rng.choice([0x00, 0x40, 0x80])
            lab.t26(ox, oy, px, py, vy=vy, floor=floor, req=req, flags4=f4, param=rng.choice([0, 1]))
            got = lab.t26_run(0x82AF)["obj_state"] != 7
            self.assertEqual(got, si.model_t26_contact(ox, oy, px, py, vy >= 0x8000, floor, req, bool(f4 & 0x40)), (ox, oy, px, py, vy, floor, req, f4))

    def test_type26_span_random(self):
        rng = random.Random(26_002)
        lab = self.lab
        for _ in range(3000):
            x0, oy = rng.randrange(300, 3000), rng.randrange(200, 1000)
            span = rng.choice([16, 128, 160, 240])
            px, py = x0 + rng.randrange(-8, span + 8), oy + rng.randrange(-60, 61)
            vy = rng.choice([0, 0x200, 0xFF80])
            floor, req = rng.random() < 0.8, rng.choice([5, 0x0A, 0x21])
            lab.t26(x0 + 7, oy, px, py, param=1, state=8, vy=vy, floor=floor, req=req)
            lab.o.word(OBJ_ADDR + 0x3A, x0)
            lab.o.word(OBJ_ADDR + 0x34, span)
            got = lab.t26_run(0x83BF)["obj_state"] != 8
            self.assertEqual(got, si.model_t26_span_trigger(x0, span, oy, px, py, vy >= 0x8000, floor, req))

    def test_terrain_vertical_random_cells_all_acts(self):
        import rom as R
        rng = random.Random(9_001)
        for act in si.ACTS:
            lab = si.Lab(ROM_BYTES, act)
            cells = [c for c in si.terrain_cells(act) if c["kind"] in ("upright", "diagonal_right_launch", "diagonal_left_launch")]
            self.assertTrue(cells)
            for _ in range(2500):
                c = rng.choice(cells)
                blk = int(c["block"], 16)
                v = R.header(ROM_BYTES, blk)["vertical"]
                want = 0x0B if c["kind"] == "upright" else 0x1C
                fx, fy = c["world_x"] + rng.randrange(-3, 35), c["world_y"] + rng.randrange(-3, 35)
                prev = rng.choice([0x00, 0x81, 0x41, 0x49, 0x54, 0xC1])
                floor, vy = rng.choice([0, 1]), rng.choice([0x0000, 0x0080, 0x0100, 0x0240, 0x0300, 0x0500, 0xFF00])
                cur = rng.choice([5, 9, 0x0A, 0x0B, 0x11, 0x1C])
                lab.player(fx, fy - 18, vy=vy, floor=floor, prev=prev, cur=cur)
                lab.call_ix(0x690B)
                got = lab.m[0xD502] == want
                inside = c["world_x"] <= fx < c["world_x"] + 32 and c["world_y"] <= fy < c["world_y"] + 32
                exp = inside and si.model_terrain_trigger(v[(fx - c["world_x"]) & 31], fy - c["world_y"], prev, floor, (vy >> 8) if vy < 0x8000 else -1, cur)
                self.assertEqual(got, exp, (act, c, fx, fy, prev, floor, vy, cur))

    def test_terrain_horizontal_random_cells(self):
        import rom as R
        rng = random.Random(9_002)
        for act in ("thz1", "thz2"):
            lab = si.Lab(ROM_BYTES, act)
            cells = [c for c in si.terrain_cells(act) if c["kind"].startswith("horizontal")]
            for _ in range(2000):
                c = rng.choice(cells)
                Hp = R.header(ROM_BYTES, int(c["block"], 16))["horizontal"]
                x, y = c["world_x"] + rng.randrange(-20, 52), c["world_y"] + rng.randrange(-10, 38)
                right = rng.random() < 0.5
                lab.player(x, y, floor=rng.choice([0, 1]), vy=rng.choice([0, 0x200, 0xFF00]), cur=rng.choice([5, 9, 0x0A]))
                lab.m[0xD523] = 0
                lab.call_ix(0x716B if right else 0x7210)
                px, py = x + (9 if right else -9), y + 6
                inside = c["world_x"] <= px < c["world_x"] + 32 and c["world_y"] <= py < c["world_y"] + 32
                exp = inside and si.model_side_hit(Hp, px - c["world_x"], py - c["world_y"], right)
                self.assertEqual(lab.m[0xD502] == 9, exp, (act, c, x, y, right))

    def test_death_rule_random(self):
        rng = random.Random(401_000)
        lab = self.lab
        for _ in range(400):
            sy = rng.randrange(-32768, 32768)
            lab.player(600, 400)
            lab.o.word(0xD51C, sy & 0xFFFF)
            reached = lab.call_watch(0x401A, 0x4984)
            self.assertEqual(reached == 0x4984, sy >= 0xD0, sy)

    def test_attack_gate_random(self):
        rng = random.Random(5_003)
        lab = self.lab
        m = lab.m
        for _ in range(500):
            f3, d532 = rng.randrange(256), rng.choice([0, 1, 6, 7])
            for a in range(si.OBJ, si.OBJ + 0x40):
                m[a] = 0
            m[si.OBJ], m[si.OBJ + 0x21] = 0x27, rng.choice([1, 2, 4, 0x11])
            m[0xD503], m[0xD532] = f3, d532
            lab.call_ix(0x5F3D, si.OBJ, 1)
            self.assertEqual(m[si.OBJ] == 0x0F, bool(f3 & 2) or d532 == 6, (f3, d532))


OBJ_ADDR = si.OBJ

if __name__ == "__main__":
    unittest.main()

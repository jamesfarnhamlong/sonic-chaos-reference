#!/usr/bin/env python3
"""THZ2/THZ3 object parameter deltas ($26 $88, $10 $01/$03, $28 aux1).

Cache-driven tests always run; the ROM-backed class regenerates the cache from the ROM
(set SONIC_CHAOS_ROM) and skips otherwise.  No test encodes a guessed meaning: every
expected value below is a decoded record, an executed original routine result, or
arithmetic on such values.
"""
import hashlib
import importlib.util
import json
import os
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
CACHE = ROOT / "data" / "rom-cache" / "levels" / "object-deltas.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))
T26, T10, T28 = D["type_26"], D["type_10"], D["type_28"]

spec = importlib.util.spec_from_file_location("thz2_thz3_object_deltas", ROOT / "tools" / "thz2_thz3_object_deltas.py")
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


def rec(section, act, index):
    return next(r for r in section["placements"] if r["act"] == act and r["record_index"] == index)


class PlacementTests(unittest.TestCase):
    def test_rom_hash(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)

    def test_type26_counts_and_parameters(self):
        for act, expected in (("thz1", {"0x00": 2, "0x01": 1, "0x8A": 1}),
                              ("thz2", {"0x00": 8, "0x01": 1, "0x88": 1}),
                              ("thz3", {"0x00": 4})):
            rows = [r for r in T26["placements"] if r["act"] == act]
            self.assertEqual(dict(Counter(r["parameter"] for r in rows)), expected, act)
        self.assertTrue(all(r["aux0"] == "0x72" and r["aux1"] == "0x72" and r["flags"] == "0x00" for r in T26["placements"]))

    def test_the_only_88_placement(self):
        rows = [r for r in T26["placements"] if r["parameter"] == "0x88"]
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["act"], r["record_index"], r["rom_offset"], r["raw_bytes"], r["world_x"], r["world_y"]),
                         ("thz2", 26, "0x7086D", "26 E0 06 80 04 00 88 72 72", 1504, 896))

    def test_type10_counts_and_parameters(self):
        for act, expected in (("thz1", {"0x02": 1, "0x04": 2, "0x06": 2}),
                              ("thz2", {"0x02": 1, "0x03": 2, "0x04": 1, "0x06": 1}),
                              ("thz3", {"0x01": 1})):
            rows = [r for r in T10["placements"] if r["act"] == act]
            self.assertEqual(dict(Counter(r["parameter"] for r in rows)), expected, act)
        self.assertEqual([(r["world_x"], r["world_y"]) for r in T10["placements"] if r["parameter"] == "0x03"],
                         [(336, 302), (2784, 270)])
        self.assertEqual([(r["act"], r["world_x"], r["world_y"]) for r in T10["placements"] if r["parameter"] == "0x01"],
                         [("thz3", 1456, 366)])

    def test_type28_combinations(self):
        combos = {(r["act"], r["parameter"], r["aux1"]) for r in T28["placements"]}
        self.assertIn(("thz2", "0x0A", "0x19"), combos)
        self.assertIn(("thz2", "0x0A", "0x13"), combos)
        self.assertEqual(sum(r["act"] == "thz3" for r in T28["placements"]), 0)
        self.assertEqual(sorted((r["world_x"], r["world_y"]) for r in T28["placements"] if r["act"] == "thz2"),
                         [(552, 720), (1552, 304), (3672, 608)])

    def test_new_variant_placements_listed(self):
        v = {(x["type"], x["parameter"], x["aux"]["aux1"]): x for x in D["variants"]}
        self.assertEqual([(p["world_x"], p["world_y"]) for p in v[("0x26", "0x88", "0x72")]["placements"]], [(1504, 896)])
        self.assertEqual(len(v[("0x10", "0x03", "0x00")]["placements"]), 2)
        self.assertEqual(len(v[("0x10", "0x01", "0x00")]["placements"]), 1)


class Type26Tests(unittest.TestCase):
    def test_flag_decoding(self):
        init = T26["init_fixtures"]
        self.assertEqual(init["thz2_88"]["after_init_825A"]["span_pixels_34"], (0x88 & 0x7F) * 16)
        self.assertEqual(init["thz2_88"]["after_init_825A"]["span_pixels_34"], 128)
        self.assertEqual(init["thz1_8A_control"]["after_init_825A"]["span_pixels_34"], 160)
        for key in ("thz2_88", "thz1_8A_control"):
            after = init[key]["after_init_825A"]
            self.assertEqual((after["requested_state_02"], after["rest_state_0a"], after["parameter_3f_after"]), (8, 8, "0x01"))
            self.assertEqual(after["y_added_by_init"], 12)
        self.assertEqual(init["thz1_00_control"]["after_init_825A"]["parameter_3f_after"], "0x00")
        self.assertEqual(init["thz1_00_control"]["after_init_825A"]["requested_state_02"], 7)

    def test_span_boundaries(self):
        rows88 = {r["player_x_minus_object_x"]: r["state_after_83BF"] for r in T26["span_x_boundaries"]["thz2_88"]}
        self.assertEqual([rows88[k] for k in (-1, 0, 1, 127, 128, 159, 160)], [8, 9, 9, 9, 8, 8, 8])
        rows8a = {r["player_x_minus_object_x"]: r["state_after_83BF"] for r in T26["span_x_boundaries"]["thz1_8A_control"]}
        self.assertEqual([rows8a[k] for k in (-1, 0, 1, 159, 160)], [8, 9, 9, 9, 8])

    def test_span_y_window(self):
        for key in ("thz2_88", "thz1_8A_control"):
            rows = {r["player_y_minus_object_y"]: r["state_after_83BF"] for r in T26["span_y_window"][key]}
            self.assertEqual([rows[k] for k in (-60, -48, -47, -20, 0, 47, 48)], [8, 8, 9, 9, 9, 9, 8])

    def test_launch_values(self):
        for key in ("thz2_88", "thz1_8A_control"):
            r = T26["launch_fixtures"][key]
            self.assertEqual((r["requested_object_state_02"], r["counter_1e"], r["player_requested_state_d502"],
                              r["player_y_velocity_8_8"]), (3, "0x1C", 11, -1280))
            self.assertEqual(r["object_x_after"], r["object_x_expected_player_x_and_F0"])
        strong = T26["launch_fixtures"]["thz1_00_fixed_strong_control"]
        weak = T26["launch_fixtures"]["thz1_01_fixed_weak_control"]
        self.assertEqual((strong["requested_object_state_02"], strong["player_y_velocity_8_8"]), (1, -1888))
        self.assertEqual((weak["requested_object_state_02"], weak["player_y_velocity_8_8"]), (3, -1280))

    def test_rise_model_matches_documented_reference(self):
        self.assertEqual(tool.rise_model(0xF880)["rise_pixels"], 296.25)  # docs/audit-2026-09-21.md (-7.5)
        self.assertEqual(T26["rise_model"]["weak_FB00"]["rise_pixels"], 130.84)
        self.assertEqual(T26["rise_model"]["strong_F8A0"]["rise_pixels"], 286.41)

    def test_layout_context(self):
        ctx = T26["thz2_88_layout_context"]
        self.assertEqual(ctx["span_end_exclusive_x"], 1632)
        self.assertIn([1632, 864], ctx["spike_cells_within_192_px_of_span"])
        self.assertTrue(all(top == 608 for _, top in ctx["nearest_ceiling_top_y_per_column"]))


class Type10Tests(unittest.TestCase):
    def test_mask_table(self):
        t = T10["mask_table_bank_0C_A1F0"]
        self.assertEqual((t["0x01"], t["0x02"], t["0x03"], t["0x04"], t["0x06"]), ("0x01", "0x02", "0x04", "0x08", "0x20"))

    def test_init_and_state_entry(self):
        for p in ("0x01", "0x03"):
            self.assertEqual(T10["init_callback_A149"][p]["parameter_after"], p)
            self.assertEqual(T10["init_callback_A149_alternate_player_type"][p]["parameter_after"], p)
            self.assertEqual(T10["state_entry_A161_graphics_selector"][p]["graphics_selector_d3b3"], p)

    def test_param_01_reward(self):
        add = T10["reward_dispatch"]["param_01_ring_counter_add"]["after_dispatch"]
        self.assertEqual((add["reward_bits_d3a3"], add["counter_d29a"], add["counter_d299"], add["sound_request_de04"]),
                         ("0x00", "0x15", "0x09", "0x00"))
        carry = T10["reward_dispatch"]["param_01_ring_counter_carry"]["after_dispatch"]
        self.assertEqual((carry["counter_d29a"], carry["counter_d299"], carry["sound_request_de04"]), ("0x05", "0x10", "0xA9"))
        self.assertEqual(T10["reward_dispatch"]["param_01_ring_counter_add"]["after_contact"]["score_bytes_after"], "10 00 00")

    def test_ring_counter_identity(self):
        proof = T10["ring_counter_identity_proof"]
        self.assertEqual(proof["terrain_ring_pickup_plus_one"]["d29a_after"], "0x06")
        self.assertEqual((proof["terrain_ring_pickup_carry"]["d29a_after"], proof["terrain_ring_pickup_carry"]["d299_after"]),
                         ("0x00", "0x10"))

    def test_param_03_power_code(self):
        r = T10["reward_dispatch"]["param_03_power_code"]
        self.assertEqual(r["after_contact"]["reward_bits_d3a3"], "0x04")
        a = r["after_dispatch"]
        self.assertEqual((a["power_code_d532"], a["timer_d44c"], a["sound_request_de04"], a["counter_d29a"], a["counter_d299"]),
                         ("0x03", 900, "0x00", "0x00", "0x09"))
        self.assertEqual(a["player_max_x_d373"], "0x0400")  # dispatch alone does not change it

    def test_power_code_3_per_update(self):
        rows = T10["power_code_3_per_update_4A74"]
        self.assertTrue(all(r["player_max_x_d373"] == "0x0600" and r["power_code_d532"] == 3 for r in rows))
        self.assertEqual([r["timer_d44c"] for r in rows], [2, 1, 0, 65535, 65534])  # code 3 is not cleared at zero
        control = T10["power_code_4_per_update_4A74_control"]
        self.assertEqual([r["power_code_d532"] for r in control], [4, 0, 0])  # code 4 is cleared at zero
        self.assertTrue(all(r["player_max_x_d373"] == "0x0400" for r in control))

    def test_controls_unchanged(self):
        d2 = T10["reward_dispatch"]["param_02_control"]["after_dispatch"]
        self.assertEqual((d2["counter_d299"], d2["sound_request_de04"]), ("0x10", "0xA9"))
        d4 = T10["reward_dispatch"]["param_04_control"]["after_dispatch"]
        self.assertEqual((d4["power_code_d532"], d4["timer_d44c"], d4["player_requested_state_d502"], d4["player_max_x_d373"]),
                         ("0x04", 300, "0x11", "0x0700"))

    def test_graphics_selectors(self):
        g = T10["graphics_selectors"]
        self.assertEqual(g["0x01"]["sources"][0]["source_rom"], "0x399A0")
        self.assertEqual(g["0x01"]["sources"][1]["source_rom"], "0x39EE0")
        self.assertEqual([f["frame_index"] for f in g["0x03"]["frames"]], ["0x0B", "0x0C"])
        self.assertEqual(len({g[s]["frames"][0]["rgba_sha256"] for s in g}), 3)
        # the fixed frame 0x0C is shared with the THZ1 selectors (docs/object-10.md)
        self.assertEqual(len({g[s]["frames"][1]["rgba_sha256"] for s in g}), 1)


class Type28Tests(unittest.TestCase):
    def test_reversal_period_formula(self):
        for aux1, row in ((0x09, 144), (0x0D, 208), (0x13, 304), (0x19, 400)):
            fx = T28["reversal_period_fixtures"][f"0x{aux1:02X}"]
            self.assertEqual(fx["updates_until_reverse"], row)
            self.assertEqual(fx["updates_until_reverse"], 16 * aux1)

    def test_init_fields(self):
        for key, aux1 in (("thz2:1", 25), ("thz2:2", 19), ("thz1:1", 9), ("thz1:2", 13)):
            f = T28["init_8585_fixtures"][key]
            self.assertEqual((f["requested_state_02"], f["counter_34"], f["counter_37"], f["step_counter_30"]), (11, aux1, aux1, "0x10"))
        sag = T28["init_8585_fixtures"]["thz2:3"]
        self.assertEqual((sag["requested_state_02"], sag["counter_34"], sag["axis_flag_25"]), (5, 0, "0xFF"))
        self.assertEqual(sag, {**T28["init_8585_fixtures"]["thz1:3"], "aux1": sag["aux1"]})


@unittest.skipUnless(matching_rom(), "matching Sonic Chaos ROM not available")
class RomRegenerationTests(unittest.TestCase):
    def test_cache_regenerates_byte_for_byte(self):
        rom = matching_rom().read_bytes()
        report = tool.build_report(rom)
        self.assertEqual(json.dumps(report, indent=2) + "\n", CACHE.read_bytes().decode("utf-8").replace("\r\n", "\n"))

    def test_placements_match_rom_bytes(self):
        rom = matching_rom().read_bytes()
        for section in (T26, T10, T28):
            for r in section["placements"]:
                off = int(r["rom_offset"], 16)
                self.assertEqual(" ".join(f"{b:02X}" for b in rom[off:off + 9]), r["raw_bytes"])

    def test_dispatch_targets(self):
        rom = matching_rom().read_bytes()
        # type $26 state table $78212: state 7 -> fixed idle $82AF via script $8254; states 8/9 -> $83BF/$8401
        def word(cpu, base=0x78000):
            return rom[base + cpu - 0x8000] | rom[base + cpu + 1 - 0x8000] << 8
        self.assertEqual(word(0x8212 + 2 * 8), 0x83B3)
        self.assertEqual(word(0x8212 + 2 * 9), 0x83B9)
        self.assertEqual(word(0x83B3 + 2), 0x83BF)
        self.assertEqual(word(0x83B9 + 2), 0x8401)
        self.assertEqual(word(0x8254 + 2), 0x82AF)
        # type $28 state table $78439: state 11 script calls $86DA
        s11 = word(0x8439 + 2 * 11)
        self.assertEqual(rom[0x78000 + s11 - 0x8000 + 10:0x78000 + s11 - 0x8000 + 14].hex(), "e001da86")
        # reward dispatcher branches $4AA3: bit0 -> $4AC0, bit2 -> $4B0F
        self.assertEqual(rom[0x4AA7:0x4AAB].hex(), "cb4720" + f"{0x4AC0 - 0x4AAB:02x}")  # BIT 0,A ; JR nz,$4AC0
        self.assertEqual(rom[0x4AAF:0x4AB3].hex(), "cb5720" + f"{0x4B0F - 0x4AB3:02x}")  # BIT 2,A ; JR nz,$4B0F


if __name__ == "__main__":
    unittest.main()

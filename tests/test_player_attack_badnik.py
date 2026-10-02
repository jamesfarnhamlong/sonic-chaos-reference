#!/usr/bin/env python3
"""Player attack posture / badnik audit: cache-driven tests (no ROM) plus ROM-backed random sweeps.

The ROM-backed class re-runs the original routines on random inputs that are NOT the ones used to build the cache and compares
them with the recovered rules in tools/player_attack_badnik.py. It skips without the ROM (set SONIC_CHAOS_ROM).
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
CACHE = ROOT / "data" / "rom-cache" / "player-attack-badnik.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("player_attack_badnik", ROOT / "tools" / "player_attack_badnik.py")
pab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pab)


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


def setter(name, cur=None):
    rows = [r for r in D["setter_effects"]["setters"] if r["name"] == name and (cur is None or r["current_state_when_called"] == cur)]
    assert len(rows) == 1, name
    return rows[0]


class ProvenanceTests(unittest.TestCase):
    def test_header(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertTrue(D["research_only"] and D["poc_untouched"])
        self.assertEqual(D["machine_facing_label"], "player_attack_badnik")
        self.assertFalse(D["static_only"])

    def test_routines_hashed_and_no_rom_dump(self):
        self.assertGreaterEqual(len(D["routines"]), 15)
        for r in D["routines"]:
            self.assertEqual(len(r["sha256"]), 64)
            self.assertLessEqual(len(r["first_16_bytes"]), 32)

    def test_counts(self):
        c = D["counts"]
        self.assertGreaterEqual(c["controlled_cases"], 70000)
        self.assertEqual(c["model_mismatches"], 0)
        self.assertGreaterEqual(c["emulated_updates_recorded"], 2000)


class SiteScanTests(unittest.TestCase):
    def test_d532_has_exactly_five_writers(self):
        writes = [r for r in D["sites"]["d532_absolute"] if "write" in r["kind"]]
        self.assertEqual(sorted(r["cpu"] for r in writes), ["0x48FF", "0x4AA0", "0x4AE8", "0x4B13", "0x4B3C"])

    def test_bit1_player_writers_are_the_setters(self):
        regs = {r["region"] for r in D["sites"]["ix3_bit1_player_writers"]}
        for want in ("setter: jump (state $0A)", "setter: upright spring (state $0B)", "setter: diagonal spring (state $1C)", "setter: state $0F (spin-dash charge)"):
            self.assertIn(want, regs)
        self.assertNotIn("setter: hurt", " ".join(regs))

    def test_hl_writers(self):
        self.assertEqual([w["cpu"] for w in D["sites"]["d503_bit1_hl_writers"]], ["0x4B22", "0x4C7D", "0x99D8"])


class SetterTests(unittest.TestCase):
    def test_bit1_effects(self):
        self.assertEqual(setter("jump_state_0A")["bit1_attack"], "conditional")
        self.assertEqual(setter("jump_no_impulse_state_0A")["bit1_attack"], "set")
        self.assertEqual(setter("upright_spring_state_0B")["bit1_attack"], "cleared")
        self.assertEqual(setter("diagonal_spring_state_1C")["bit1_attack"], "set")
        self.assertEqual(setter("horizontal_spring_left_state_9")["bit1_attack"], "set")
        self.assertEqual(setter("fall_state_0E", "0x05")["bit1_attack"], "cleared")
        self.assertEqual(setter("fall_state_0E", "0x0A")["bit1_attack"], "kept")        # a normal jump never falls into $0E
        self.assertEqual(setter("land_state_5")["bit1_attack"], "cleared")
        self.assertEqual(setter("land_state_5")["bit6_hurt"], "cleared")
        self.assertEqual(setter("hurt_state_1E")["bit1_attack"], "kept")
        self.assertEqual(setter("death_state_1F")["bit1_attack"], "kept")
        self.assertEqual(setter("act_clear_state_20")["bit1_attack"], "kept")
        self.assertEqual(setter("state_0F_spin_dash_charge")["bit1_attack"], "set")
        self.assertEqual(setter("ramp_state_1B")["bit1_attack"], "set")
        self.assertEqual(setter("roll_state_9")["bit0_airborne"], "cleared")

    def test_hurt_sets_bits_6_and_7(self):
        r = setter("hurt_state_1E")
        self.assertEqual((r["bit6_hurt"], r["bit7_invulnerable"]), ("set", "set"))

    def test_power_up_values(self):
        b = D["power_up_controlled"]["branches"]
        self.assertEqual((b["bit2_param3"]["D532_after"], b["bit2_param3"]["D44C_timer_after"]), (3, 900))
        self.assertEqual((b["bit3_param4"]["D532_after"], b["bit3_param4"]["D44C_timer_after"]), (4, 300))
        self.assertEqual((b["bit5_param6"]["D532_after"], b["bit5_param6"]["D44C_timer_after"], b["bit5_param6"]["D503_after"]), (6, 600, 0x82))
        exp = b["timer_expiry_from_1"]
        self.assertEqual((exp["0x04"]["D532_after_timer_reaches_0"], exp["0x06"]["D532_after_timer_reaches_0"]), (0, 0))
        self.assertEqual(exp["0x03"]["D532_after_timer_reaches_0"], 3)
        imm = b["damage_request_FF_with_D532"]
        self.assertEqual(imm["0x06"]["rings_after"], 16)
        self.assertEqual(imm["0x00"]["rings_after"], 0)


class GateTests(unittest.TestCase):
    def test_5f3d(self):
        g = D["gate_5f3d"]
        self.assertEqual(g["model_mismatches"], 0)
        for code, row in g["by_d532"].items():
            self.assertEqual(row["converts_when_bit1_set"], [True])
            self.assertEqual(row["converts_when_bit1_clear"], [True] if code == "0x06" else [False])

    def test_48bc_model(self):
        c = D["contact_handler_48bc"]
        self.assertEqual(c["model_mismatches"], 0)
        self.assertEqual(c["cases"], 6144)

    def test_type27_sweep(self):
        s = D["type27_sweep"]
        self.assertEqual(s["model_mismatches"], 0)
        self.assertEqual(s["overlap_box_player_minus_object"]["dx"], [-17, 17])
        self.assertEqual(s["overlap_box_player_minus_object"]["dy"], [-14, 24])
        for name, row in s["per_condition"].items():
            self.assertEqual(row["D3B0_ever_set_by_callback"], 0, name)
        pc = s["per_condition"]
        self.assertEqual(pc["airborne_only_bit0"]["cells_converted"], 0)
        self.assertEqual(pc["standing_or_walking"]["cells_converted"], 0)
        self.assertEqual(pc["jump_bits01"]["cells_converted"], 1365)
        self.assertEqual(pc["invincible_D532_6"]["cells_converted"], 1365)
        self.assertEqual(s["D521_high_nibble_regions_after_callback"]["0x2"]["dy_range"], [-14, -1])
        self.assertEqual(s["D521_high_nibble_regions_after_callback"]["0x1"]["dy_range"], [7, 24])

    def test_type21_sweep(self):
        s = D["type21_sweep"]
        self.assertEqual(s["model_mismatches"], 0)
        self.assertTrue(s["stomp_does_not_convert"])
        jump = s["per_condition"]["jump_bits01"]
        self.assertEqual(jump["stomp_bounce"]["dy"], [-26, -4])
        self.assertEqual(jump["converted"]["dy"], [-3, 24])
        self.assertEqual(jump["damage_request_D3B0"]["cells"], 0)
        walk = s["per_condition"]["standing_or_walking"]
        self.assertEqual(walk["stomp_bounce"]["cells"], jump["stomp_bounce"]["cells"])     # the stomp ignores the attack bit
        self.assertEqual(walk["converted"]["cells"], 0)
        self.assertEqual(s["per_condition"]["airborne_only_bit0"]["converted"]["cells"], 0)

    def test_monitor_needs_bit1_only(self):
        m = D["monitor_sweep"]["per_condition"]
        self.assertEqual(m["invincible_D532_6"], {"no_effect": 2139})
        self.assertEqual(m["airborne_only_bit0"], {"no_effect": 2139})
        self.assertEqual(m["jump_bits01"], m["attack_bit1_grounded"])
        self.assertGreater(m["jump_bits01"]["break_rebound_-4.0"], 0)


class EmulatedTests(unittest.TestCase):
    def cases(self):
        return {c["case"]: c for c in D["natural_timelines"]["cases"]}

    def test_normal_jump_keeps_the_attack_bit_through_apex_and_fall(self):
        seg = [s for s in self.cases()["jump_hold_from_run"]["segments"] if s["state"] == "0x0A" and s["requested"] == "0x0A"]
        self.assertTrue(seg and all(s["D503"] == "0x03" for s in seg))
        self.assertTrue(any(s["vy_first"] < 0 for s in seg) and any(s["vy_last"] > 0 for s in seg))

    def test_jump_start_and_landing_windows(self):
        counts = D["natural_timelines"]["state_vs_attack_bit_disagreement_updates"]["counts"]
        self.assertGreaterEqual(counts["current_state 0x06 requested 0x0A D503 0x03"], 1)     # unrolled frame, attack bit set
        self.assertGreaterEqual(counts["current_state 0x0A requested 0x05 D503 0x00"], 1)     # ball state, attack bit clear

    def test_upright_spring_and_ledge_fall_are_not_attacking(self):
        for name in ("upright_spring_type26_strong_(688,864)", "terrain_upright_spring_(928,640)", "walk_off_ledge"):
            for s in self.cases()[name]["segments"]:
                if s["state"] in ("0x0B", "0x0E") and int(s["D503"], 16) & 1:      # airborne updates (the landing update already cleared bit 0)
                    self.assertFalse(s["badnik_sees_attack"], (name, s))
                    self.assertTrue(s["legacy_playerJump"], (name, s))

    def test_diagonal_spring_attacks_until_the_apex(self):
        segs = self.cases()["terrain_diagonal_spring_right_(2464,256)"]["segments"]
        flight = [s for s in segs if s["state"] == "0x1C" and s["requested"] == "0x1C"]
        apex = [s for s in segs if s["state"] == "0x1C" and s["requested"] == "0x0E"]
        self.assertTrue(apex and not apex[0]["badnik_sees_attack"])      # the apex request clears bit 1 while $D501 is still $1C
        self.assertTrue(flight and all(s["badnik_sees_attack"] for s in flight))
        after = [s for s in segs if s["state"] == "0x0E"]
        self.assertTrue(after and not after[0]["badnik_sees_attack"])

    def test_legacy_false_positive_census(self):
        lc = D["natural_timelines"]["legacy_vs_canonical"]
        self.assertGreater(lc["updates_legacy_true_but_canonical_false"], 100)
        for state in lc["by_state_of_those_updates"]:
            self.assertIn(state, ("0x0B", "0x0E", "0x01", "0x05", "0x0A", "0x1C"))

    def test_peel_out_does_not_set_the_attack_bit_in_an_ordinary_charge(self):
        for s in self.cases()["peel_out_charge_and_release"]["segments"]:
            if s["state"] in ("0x15", "0x1A") and s["requested"] in ("0x15", "0x1A"):
                self.assertEqual(int(s["D503"], 16) & 2, 0)

    def test_contact_trials_type27(self):
        t = {r["pose"]: r for r in D["contact_trials"]["type27"]["trials"]}
        for pose in ("upright_spring_fall_state_0B", "falling_state_0E_after_apex_or_ledge", "walking_from_the_side"):
            self.assertIsNone(t[pose]["converted_at_update"], pose)
            self.assertIsNotNone(t[pose]["hurt_or_death_requested_at_update"], pose)
            self.assertEqual(t[pose]["rings_after"], 0)
        for pose in ("normal_jump_falling_onto_it", "diagonal_spring_state_1C", "rolling_from_the_side", "invincible_falling_state_0E"):
            self.assertIsNotNone(t[pose]["converted_at_update"], pose)
            self.assertIsNone(t[pose]["hurt_or_death_requested_at_update"], pose)
        self.assertEqual(t["normal_jump_falling_onto_it"]["rebound_vy_8_8"], -768)
        self.assertEqual(t["normal_jump_falling_onto_it"]["rebound_update"], t["normal_jump_falling_onto_it"]["converted_at_update"] + 1)
        self.assertEqual(t["normal_jump_ascending_from_below"]["rebound_vy_8_8"], 128)
        self.assertIsNone(t["rolling_from_the_side"]["rebound_vy_8_8"])
        self.assertEqual(t["normal_jump_falling_onto_it"]["D503_after_12"], "0x03")           # attack bit persists after the rebound

    def test_contact_trials_type21(self):
        t = {r["pose"]: r for r in D["contact_trials"]["type21"]["trials"]}
        for pose in ("jump_falling_onto_top", "falling_state_0E_onto_top"):
            self.assertIsNone(t[pose]["converted_at_update"])
            self.assertEqual(t[pose]["rebound_vy_8_8"], -1728)
            self.assertEqual(t[pose]["D503_after_12"], "0x01")
        self.assertIsNotNone(t["rolling_from_the_side"]["converted_at_update"])
        self.assertIsNone(t["walking_from_the_side"]["converted_at_update"])
        self.assertEqual(t["walking_from_the_side"]["rings_after"], 0)

    def test_frame_order(self):
        o = D["frame_event_order"]["contact_update"]["order"]
        idx = {name: o.index(name) for name in o}
        self.assertLess(idx["player update entry $361D"], idx["callback dispatcher $5E91 (player)"])
        self.assertLess(idx["callback dispatcher $5E91 (player)"], idx["contact/damage handler $48BC"])
        self.assertLess(idx["power-up timer $4A74 (end of player update)"], idx["object scheduler $5DD1"])
        self.assertLess(idx["object scheduler $5DD1"], idx["attack gate $5F3D"])
        self.assertLess(idx["attack gate $5F3D"], idx["enemy conversion $5F54"])


class DocumentationTests(unittest.TestCase):
    def test_poc_table_covers_known_consumers(self):
        text = json.dumps(D["poc_consumers"])
        for needle in ("OBJ_chaos_object_27", "OBJ_chaos_object_21", "OBJ_chaos_object_10", "SCR_chaos_adapter.gml:30", "SCR_physics_spring"):
            self.assertIn(needle, text)
        self.assertEqual(D["poc_consumers"]["poc_commit"], "7799c3459f59781878574e5d805bb3df4baa057c")

    def test_thz3_census(self):
        t = D["thz3_dependency_census"]
        self.assertEqual(t["terrain"]["blocks_new_to_thz3"], [])
        self.assertEqual(sorted(t["objects_thz3"]), ["0x09", "0x10", "0x1B", "0x26", "0x50"])

    def test_census_types(self):
        self.assertEqual(D["badnik_census"]["enemy_types"], ["0x21", "0x27"])
        self.assertEqual(D["badnik_census"]["thz1"]["0x21"], 6)
        self.assertEqual(D["badnik_census"]["thz2"]["0x27"], 4)

    def test_census_matches_the_object_census_cache(self):
        for act in ("thz1", "thz2"):
            records = json.loads((ROOT / "data" / "rom-cache" / "levels" / act / "objects.json").read_text(encoding="utf-8"))["records"]
            for t in ("0x21", "0x27"):
                self.assertEqual(sum(r["type_id"] == t for r in records), D["badnik_census"][act][t], (act, t))


@unittest.skipUnless(ROM_BYTES, "needs the research ROM (SONIC_CHAOS_ROM)")
class RomBackedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.si, cls.L = pab.lab(ROM_BYTES)

    def test_48bc_random_inputs(self):
        L, m, o = self.L, self.L.m, self.L.o
        rng = random.Random(20260601)
        for _ in range(1500):
            f3 = rng.choice([0, 1, 2, 3, 0x40, 0x41, 0x42, 0x43, 0x80, 0x81, 0x82, 0x83, 0xC0, 0xC1, 0xC2, 0xC3])
            d532 = rng.choice([0, 3, 4, 6])
            d520 = rng.choice([0, rng.randint(1, 20)])
            d3b0 = rng.choice([0, 0xFF])
            hi = rng.choice([0x00, 0x10, 0x20, 0x30])
            rings = rng.choice([0, rng.randint(1, 0x50)])
            cur = rng.choice([5, 9, 0x11, 0x0A])
            pab._player_at(L, f3, d532, vy=0x0100, cur=cur, req=cur, rings=rings)
            m[0xD520], m[0xD3B0], m[0xD521] = d520, d3b0, hi
            L.call_ix(0x48BC, 0xD500)
            vy, req = pab.s16(o.word(0xD518)), m[0xD502]
            if req in (0x1E, 0x1F) and req != cur:
                got = "death" if req == 0x1F else "hurt"
            elif vy == -0x300:
                got = "rebound_up_-3.0"
            elif vy == 0x80:
                got = "rebound_down_+0.5"
            elif d520 == 0 and d3b0 == 0:
                got = "none"
            else:
                got = "contact_ignored"
            want = pab.model_48bc(f3, d532, d520, d3b0, hi, 1 if rings else 0, cur)
            self.assertEqual(got, want, (f3, d532, d520, d3b0, hi, rings, cur))

    def test_5f3d_random(self):
        L, m = self.L, self.L.m
        rng = random.Random(7)
        for _ in range(600):
            f3, d532, contact = rng.randrange(256), rng.randrange(10), rng.choice([0, 1, 2, 4, 8, 15])
            pab._clear_obj(m)
            m[pab.SLOT], m[pab.SLOT + 0x21] = 0x27, contact
            m[0xD503], m[0xD532] = f3, d532
            L.call_ix(0x5F3D, pab.SLOT, 1)
            want = contact != 0 and (d532 == 6 or bool(f3 & 2))
            self.assertEqual(m[pab.SLOT] == 0x0F, want, (f3, d532, contact))

    def test_type27_random_positions(self):
        L, m = self.L, self.L.m
        rng = random.Random(99)
        for _ in range(800):
            dx, dy = rng.randint(-30, 30), rng.randint(-40, 45)
            f3, d532 = rng.choice([0, 1, 2, 3]), rng.choice([0, 6])
            pab._setup_t27(L, dx, dy, f3, d532)
            L.call_ix(0x89AC, pab.SLOT, pab.BANK_T27)
            overlap = abs(dx) <= 17 and -14 <= dy <= 24
            self.assertEqual(m[pab.SLOT] == 0x0F, overlap and (d532 == 6 or bool(f3 & 2)), (dx, dy, f3, d532))
            self.assertEqual(m[0xD3B0], 0)

    def test_type21_random_positions(self):
        L, m, o = self.L, self.L.m, self.L.o
        rng = random.Random(5)
        for _ in range(800):
            dx, dy = rng.randint(-30, 30), rng.randint(-40, 40)
            f3, d532 = rng.choice([0, 1, 2, 3]), rng.choice([0, 6])
            pab._clear_obj(m)
            m[pab.SLOT] = 0x21
            o.word(pab.SLOT + 0x11, 500)
            o.word(pab.SLOT + 0x14, 500)
            m[pab.SLOT + 0x2C], m[pab.SLOT + 0x2D] = 0x0B, 0x1A
            pab._player_at(L, f3, d532, x=500 + dx, y=500 + dy)
            o.word(0xD518, 0)
            L.call_ix(0xB2AF, pab.SLOT, pab.BANK_T21)
            overlap = abs(dx) <= 19 and -26 <= dy <= 24
            if not overlap:
                self.assertEqual((m[pab.SLOT], m[0xD3B0], m[0xD502]), (0x21, 0, 5))
            elif dy <= -4:
                self.assertEqual((m[pab.SLOT], m[0xD502], o.word(0xD518)), (0x21, 0x0B, 0xF940))
            elif d532 == 6 or f3 & 2:
                self.assertEqual(m[pab.SLOT], 0x0F)
            else:
                self.assertEqual((m[pab.SLOT], m[0xD3B0]), (0x21, 0xFF))

    def test_cache_is_deterministic_for_the_static_part(self):
        fresh = json.loads(json.dumps(pab.build(ROM_BYTES, static_only=True)))
        for key in ("routines", "sites", "d503_model", "d532_model", "badnik_census", "rebound_model", "non_attacking_contact", "poc_consumers", "thz3_dependency_census", "update_order", "unresolved"):
            self.assertEqual(fresh[key], D[key], key)


if __name__ == "__main__":
    unittest.main()

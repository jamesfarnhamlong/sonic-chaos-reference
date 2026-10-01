#!/usr/bin/env python3
"""Player animation counter `+$07`: cache-driven tests (no ROM) plus ROM-backed differential tests of the shadow model.

The ROM-backed class uses different seeds, speeds and sequences than the cache generator and skips without the ROM
(set SONIC_CHAOS_ROM).
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
CACHE = ROOT / "data" / "rom-cache" / "player-animation-counter.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("player_animation_counter", ROOT / "tools" / "player_animation_counter.py")
pac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pac)

ELIGIBLE = pac.ELIGIBLE_STATES


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


class ProvenanceTests(unittest.TestCase):
    def test_header(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertTrue(D["research_only"] and D["poc_untouched"])
        self.assertEqual(D["machine_facing_label"], "player_animation_counter")
        self.assertFalse(D["static_only"])

    def test_routines_hashed(self):
        self.assertGreaterEqual(len(D["routines"]), 12)
        for r in D["routines"]:
            self.assertEqual(len(r["sha256"]), 64)
            self.assertLessEqual(len(r["first_16_bytes"]), 32)


class SiteTests(unittest.TestCase):
    def test_only_engine_and_selectors_write_the_counter(self):
        s = D["plus07_sites"]
        self.assertEqual(s["absolute_and_iy_writes_to_d507"], 0)
        dec = s["sites"]["dec_inc_ix"]
        self.assertEqual([r["cpu"] for r in dec], ["0x6510"])
        writes = {r["cpu"]: r["role"] for r in s["sites"]["write_ix"] if r["role"] and not r["role"].startswith("other")}
        for cpu in ("0x6549", "0x68AB", "0x8F28", "0x8F40", "0x8F71", "0x8FB4", "0x9007", "0x9038", "0x915E"):
            self.assertIn(cpu, writes)
        reads = [r["cpu"] for r in s["sites"]["bit_ix"] + s["sites"]["read_ix"] if r["role"] and not r["role"].startswith("other")]
        self.assertIn("0x7544", reads)

    def test_update_order_is_documented(self):
        o = D["update_order"]
        self.assertEqual(len(o["per_player_update"]), 5)
        self.assertEqual(len(o["consequences"]), 3)


class SelectorTests(unittest.TestCase):
    def test_tables(self):
        s = D["selectors"]
        self.assertEqual(s["selector_8ee1_walk_state_05"]["table"], [10, 8, 6, 4] + [4] * 12)
        self.assertEqual(s["selector_8f76_states_09_0A_10_1B"]["table"], [10, 8, 6, 5, 4, 3] + [2] * 10)
        self.assertEqual(s["selector_8f45_run_state_06"]["rule"], "+$07 := 4 always")


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.sch = D["schedules"]

    def test_eligible_set(self):
        self.assertEqual(D["eligible_states_static"], ["0x%02X" % s for s in ELIGIBLE])
        self.assertEqual(len(ELIGIBLE), 26)
        dyn = D["dynamic_eligibility"]
        self.assertEqual(dyn["observed_probing"], ["0x%02X" % s for s in ELIGIBLE])
        self.assertEqual(dyn["never_held"], [])

    def test_constant_states(self):
        for st, d in (("0x03", 6), ("0x04", 224), ("0x06", 4), ("0x0E", 8), ("0x0F", 2), ("0x12", 4), ("0x14", 4), ("0x17", 3), ("0x19", 4),
                      ("0x1A", 2), ("0x1C", 8), ("0x1D", 6)):
            self.assertEqual(self.sch[st]["loaded_durations_first_60_reloads_rle"], [[d, 60]], st)
            self.assertFalse(self.sch[st]["depends_on_inputs"], st)

    def test_multi_record_states(self):
        self.assertEqual(self.sch["0x01"]["loaded_durations_first_60_reloads_rle"][:4], [[180, 1], [64, 1], [180, 1], [64, 1]])
        self.assertEqual(self.sch["0x07"]["loaded_durations_first_60_reloads_rle"][:2], [[8, 1], [224, 1]])
        self.assertEqual(self.sch["0x11"]["loaded_durations_first_60_reloads_rle"][:4], [[8, 1], [4, 1], [8, 1], [4, 1]])
        self.assertEqual(self.sch["0x1E"]["loaded_durations_first_60_reloads_rle"][:3], [[1, 1], [2, 1], [4, 1]])
        self.assertEqual(self.sch["0x15"]["loaded_durations_first_60_reloads_rle"][:5], [[6, 4], [5, 4], [4, 4], [3, 8], [2, 40]])
        self.assertEqual(self.sch["0x0B"]["loaded_durations_first_60_reloads_rle"][:3], [[4, 14], [6, 3], [8, 1]])

    def test_input_dependence(self):
        self.assertEqual({k for k, v in self.sch["0x05"]["input_dependence"].items() if v}, {"x_speed_hi", "side_contact"})
        for st in ("0x09", "0x0A", "0x10", "0x1B"):
            self.assertEqual({k for k, v in self.sch[st]["input_dependence"].items() if v}, {"x_speed_hi", "floor"}, st)
        self.assertEqual({k for k, v in self.sch["0x0B"]["input_dependence"].items() if v}, {"d448_bit0"})
        dependent = {st for st, v in self.sch.items() if v["depends_on_inputs"]}
        self.assertEqual(dependent, {"0x05", "0x09", "0x0A", "0x0B", "0x10", "0x1B"})


class FixtureTests(unittest.TestCase):
    def test_differential_counts(self):
        f = D["differential_fixture"]
        self.assertEqual(f["mismatches"], 0)
        self.assertGreaterEqual(f["cases"], 60000)
        self.assertGreater(0.7, f["parity_set_fraction"])
        self.assertLess(0.3, f["parity_set_fraction"])
        s = D["selector_sweep"]
        self.assertEqual(s["mismatches"], 0)
        self.assertGreaterEqual(s["cases"], 600)
        t = D["transition_fixtures"]
        self.assertEqual(t["mismatches"], 0)
        self.assertGreaterEqual(t["cases"], 400)

    def test_probe_depth_after_the_counter_update(self):
        n = 0
        for rows in D["transition_fixtures"]["scenarios"].values():
            for r in rows:
                self.assertEqual(r["probe_y_from_anchor"], -8 if r["bit0"] == 0 else 2)
                n += 1
        self.assertGreaterEqual(n, 400)

    def test_transitions(self):
        sc = D["transition_fixtures"]["scenarios"]
        c = lambda name: [r["counter_after"] for r in sc[name]]
        # stand -> walk replaces the counter at once with the new selector value (speed 1 -> table 8)
        self.assertEqual(c("stand_to_walk")[3:6], [176, 8, 7])
        # walk -> run: the run selector (4) replaces the walk counter immediately
        self.assertEqual(c("walk_to_run")[4:8], [4, 3, 4, 3])
        # run -> jump (air): 3,2,1 cycle; jump -> fall: 8-update records
        seq = c("run_to_jump_to_fall_to_land")
        self.assertEqual(seq[6:12], [3, 2, 1, 3, 2, 1])
        self.assertEqual(seq[18:20], [8, 7])
        # roll entry on the floor at speed 6 selects 2; leaving the state reloads immediately
        roll = c("run_to_roll_to_stand")
        self.assertEqual(roll[5:9], [2, 1, 2, 1])
        self.assertEqual(roll[29], 180)
        # air roll uses the constant 3 and switches to the floor table when the floor bit appears at a reload
        air = c("roll_in_air_then_land")
        self.assertEqual(air[:9], [3, 2, 1] * 3)
        self.assertEqual(air[9:13], [4, 3, 2, 1])
        # a state change every update reloads every update
        self.assertEqual(c("state_change_every_update"), [179, 6, 4, 6, 6, 4, 180, 6])

    def test_direct_writes_do_not_replace_a_running_counter(self):
        rows = {r["case"]: r for r in D["direct_write_fixtures"]["rows"]}
        walk = rows["walk speed 0 -> 6 at update 4"]["counter_sequence"]
        self.assertEqual(walk[:12], [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 4, 3])
        side = rows["side contact for updates 3..6 while walking"]["counter_sequence"]
        self.assertEqual(side[:8], [4, 3, 2, 1, 2, 1, 2, 1])
        locked = rows["+$03 bit 3 set (never set by any recovered ROM code)"]
        self.assertEqual(locked["state_after"], "0x01")

    def test_emulated_play(self):
        e = D["emulated_play"]
        self.assertGreater(e["player_updates"], 5000)
        self.assertEqual(e["model_mismatches"], 0)
        self.assertEqual(e["unmodelled_stop"], 0)
        self.assertEqual(e["probe_calls"], e["probe_value_equals_engine_value"])
        self.assertGreater(e["probe_calls"], 5000)


@unittest.skipUnless(ROM_BYTES, "matching ROM not found (set SONIC_CHAOS_ROM)")
class RomBackedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pac._init_modelled(ROM_BYTES)
        cls.lab = pac.Lab(ROM_BYTES)

    def test_routine_hashes(self):
        table = {r["name"]: r for r in pac.routine_table(ROM_BYTES)}
        for r in D["routines"]:
            self.assertEqual(table[r["name"]]["sha256"], r["sha256"], r["name"])

    def test_static_part_regenerates(self):
        fresh = pac.build(ROM_BYTES, static_only=True)
        for key in ("routines", "plus07_sites", "update_order", "selectors", "eligible_states_static", "modelled_states", "schedules", "unresolved"):
            self.assertEqual(fresh[key], D[key], key)

    def test_differential_with_new_seeds(self):
        """Random state/input walks (seeds and speed sets not used by the cache): model == original engine on +$07, state, pointer, loop counter."""
        lab, m = self.lab, self.lab.m
        states = [s for s in ELIGIBLE if s in pac.MODELLED_STATES]
        n = 0
        for seed in (11, 12, 13):
            rng = random.Random(seed)
            for ep in range(60):
                lab.reset()
                mod = pac.Model(ROM_BYTES)
                mod.cur = 1
                req = rng.choice(states)
                for k in range(150):
                    if rng.random() < 0.2:
                        req = rng.choice(states)
                    hi = rng.randrange(0, 256) if rng.random() < 0.2 else rng.choice([0, 1, 2, 3, 4, 5, 6, 7, 9])
                    floor, side, d448 = rng.random() < 0.5, rng.random() < 0.2, rng.randrange(2)
                    got = lab.engine(req, hi, floor, side, d448, rng.choice([0, 0x19]), rng.randrange(64))
                    want = mod.step(req, hi, floor, side, d448)
                    n += 1
                    self.assertEqual((got, m[0xD501], m[0xD50E] | m[0xD50F] << 8, m[0xD533]), (want, mod.cur, mod.ptr, mod.loop), (seed, ep, k, req, hi, floor, side, d448))
                    req = m[0xD502]
        self.assertGreaterEqual(n, 25000)

    def test_every_speed_byte_for_each_selector(self):
        lab = self.lab
        for state in (5, 6, 9, 0x0A, 0x10, 0x1B, 0x17, 0x1D):
            for hi in range(256):
                for floor in (False, True):
                    for side in (False, True):
                        lab.reset()
                        mod = pac.Model(ROM_BYTES)
                        lab.prime(mod)
                        self.assertEqual(lab.engine(state, hi, floor, side, 0), mod.step(state, hi, floor, side, 0), (state, hi, floor, side))

    def test_probe_depth_follows_the_counter_after_the_engine(self):
        lab = self.lab
        rng = random.Random(99)
        for _ in range(300):
            lab.reset()
            mod = pac.Model(ROM_BYTES)
            lab.prime(mod)
            for k in range(12):
                st = rng.choice([1, 5, 6, 9, 0x0A, 0x0E, 0x0B, 0x1B])
                hi, floor = rng.randrange(0, 9), rng.random() < 0.5
                got = lab.engine(st, hi, floor, False, 0)
                self.assertEqual(got, mod.step(st, hi, floor, False, 0))
                self.assertEqual(lab.probe_depth(), -8 if got % 2 == 0 else 2)

    def test_state_entry_replaces_the_counter_same_update(self):
        lab = self.lab
        for a, b in ((1, 5), (5, 6), (6, 0x0A), (0x0A, 0x0E), (0x0E, 6), (6, 9), (9, 1), (0x0B, 0x0E)):
            lab.reset()
            lab.prime()
            for _ in range(7):
                lab.engine(a, 3, True, False, 0)
            mod = pac.Model(ROM_BYTES)
            mod.cur = a
            mod.step(a, 3, True, False, 0)
            first_b = lab.engine(b, 3, True, False, 0)
            m2 = pac.Model(ROM_BYTES)
            self.assertEqual(first_b, m2.step_state_run(b, 3, True, False, 0, 1)[0])


if __name__ == "__main__":
    unittest.main()

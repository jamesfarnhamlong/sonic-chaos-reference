#!/usr/bin/env python3
"""Terrain-ring collection ($753E): cache-driven tests (no ROM) plus ROM-backed controlled sweeps.

The ROM-backed class re-runs the original routine on positions and layouts that are NOT the ones used to build the
cache (seeded random points over whole levels, random rings with random offsets) and skips without the ROM
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
CACHE = ROOT / "data" / "rom-cache" / "terrain-ring-collection.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("terrain_ring_collection", ROOT / "tools" / "terrain_ring_collection.py")
trc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trc)


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


def layout_rows(act):
    return json.loads((ROOT / "data" / "rom-cache" / "levels" / act / "layout.json").read_text(encoding="utf-8"))["rows"]


PRES = {0x40: [1, 1, 0, 0], 0x41: [0, 0, 1, 1], 0x42: [1, 0, 0, 0], 0x43: [0, 1, 0, 0], 0x44: [0, 0, 1, 0], 0x45: [0, 0, 0, 1]}


class ProvenanceTests(unittest.TestCase):
    def test_header(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertTrue(D["research_only"] and D["poc_untouched"])
        self.assertEqual(D["machine_facing_label"], "terrain_ring_collection")
        self.assertFalse(D["static_only"])

    def test_routines_hashed_and_no_rom_dump(self):
        self.assertGreaterEqual(len(D["routines"]), 12)
        for r in D["routines"]:
            self.assertEqual(len(r["sha256"]), 64)
            self.assertLessEqual(len(r["first_16_bytes"]), 32)


class ModelTests(unittest.TestCase):
    def test_probe_point_offsets(self):
        self.assertEqual(trc.probe_point(100, 200, 0), (100, 192))      # -26 + 18
        self.assertEqual(trc.probe_point(100, 200, 1), (100, 202))      # -16 + 18
        self.assertEqual(trc.probe_point(100, 5, 0), (100, 0))          # negative -> 0
        self.assertEqual(trc.probe_point(100, 7, 0), (100, 0))
        self.assertEqual(trc.probe_point(100, 8, 0), (100, 0))
        self.assertEqual(trc.probe_point(100, 9, 0), (100, 1))

    def test_quadrant_and_cell(self):
        self.assertEqual([trc.quadrant(x, y) for x, y in ((0, 0), (16, 0), (0, 16), (16, 16), (31, 31), (32, 32), (63, 63))], [0, 1, 2, 3, 3, 0, 3])
        self.assertEqual(trc.cell_of(1416, 88), (44, 2))

    def test_anchor_region_edges_are_inclusive(self):
        r0 = trc.anchor_region(1408, 80, 0)
        r1 = trc.anchor_region(1408, 80, 1)
        self.assertEqual(r0, {"x": [1408, 1423], "y": [88, 103]})
        self.assertEqual(r1, {"x": [1408, 1423], "y": [78, 93]})
        # both parities overlap on 16 - 10 = 6 rows and together cover 26 rows
        self.assertEqual(r0["y"][0] - r1["y"][0], 10)

    def test_collects_requires_presence(self):
        self.assertTrue(trc.collects(0x41, 0, 16, PRES))
        self.assertFalse(trc.collects(0x41, 0, 0, PRES))
        self.assertFalse(trc.collects(0x46, 0, 0, PRES))
        self.assertTrue(trc.collects(0x40, 16, 0, PRES))
        self.assertFalse(trc.collects(0x42, 16, 0, PRES))


class CacheTests(unittest.TestCase):
    def test_tables(self):
        rows = {r["block"]: r for r in D["quadrant_tables"]["rows"]}
        self.assertEqual(rows["0x40"]["quadrants_with_ring"], ["top_left", "top_right"])
        self.assertEqual(rows["0x40"]["replacement_after_collect"], {"top_left": "0x43", "top_right": "0x42"})
        self.assertEqual(rows["0x41"]["replacement_after_collect"], {"bottom_left": "0x45", "bottom_right": "0x44"})
        for b in ("0x42", "0x43", "0x44", "0x45"):
            self.assertEqual(list(rows[b]["replacement_after_collect"].values()), ["0x46"])
        self.assertEqual(D["header_types"]["blocks_of_type_7"], ["0x40", "0x41", "0x42", "0x43", "0x44", "0x45"])
        self.assertEqual(D["header_types"]["all_zones_use_table_cpu"], ["8000"])

    def test_ring_counts_match_the_level_packages(self):
        for act, n in (("thz1", 142), ("thz2", 133), ("thz3", 6)):
            self.assertEqual(D["act_rings"][act]["ring_quadrants"], n)
            self.assertTrue(D["act_rings"][act]["equal"])

    def test_probe_coordinates(self):
        f = D["probe_coordinate_fixture"]
        self.assertEqual(f["mismatches"], 0)
        self.assertGreaterEqual(f["cases"], 800)
        self.assertEqual(f["effective_probe_offsets_from_anchor_y"], {"bit0_clear": -8, "bit0_set": 2})
        self.assertEqual(D["model"]["effective_probe_y_from_anchor"], {"0": -8, "1": 2})

    def test_collection_sweeps(self):
        total = 0
        for act, quads in (("thz1", 142), ("thz2", 133), ("thz3", 6)):
            f = D["collection_fixture"][act]
            self.assertEqual(f["ring_quadrants"], quads)
            self.assertEqual(f["mismatches"], 0, act)
            self.assertGreater(f["collected_cases"], 0)
            total += f["cases"]
        self.assertGreater(total, 200000)

    def test_exact_region(self):
        r = D["region_fixture"]
        for row in r["rows"]:
            self.assertEqual(row["anchor_x_accepted"], row["expected"]["x"])
            self.assertEqual(row["anchor_y_accepted"], row["expected"]["y"])
            self.assertEqual((row["width"], row["height"]), (16, 16))
        self.assertEqual(r["union_anchor_y_either_parity"][1] - r["union_anchor_y_either_parity"][0] + 1, 26)
        self.assertEqual(r["overlap_anchor_y_both_parities"][1] - r["overlap_anchor_y_both_parities"][0] + 1, 6)

    def test_direction_and_state_independence(self):
        self.assertEqual(D["direction_fixture"]["not_collected"], 0)
        self.assertEqual(D["direction_fixture"]["cases"], 1600)

    def test_effects(self):
        e = D["effects_fixture"]
        s = {r["d29a_before"]: r for r in e["samples"]}
        self.assertEqual(s["00"]["d29a_after"], "01")
        self.assertEqual(s["09"]["d29a_after"], "10")
        self.assertEqual(s["99"]["d29a_after"], "00")
        self.assertEqual(s["99"]["d299_after"], 1)
        self.assertEqual(s["00"]["effect_xy"], [1416, 88])
        self.assertEqual(s["00"]["slot0_type"], 3)
        self.assertEqual(s["00"]["sound"], "0xBF")
        for c in e["replacement_chain"]:
            self.assertTrue(c["collected"])
            self.assertEqual(c["cell_after"], c["expected_cell_after"])

    def test_other_surface_types_share_the_probe(self):
        rows = {(r["label"], r["plus22"]): r for r in D["other_types_fixture"]["rows"]}
        self.assertEqual(rows[("type_1d", 0)]["d29a"], "0x10")
        self.assertEqual(rows[("type_1d", 0)]["cell_after"], "0x46")
        self.assertEqual(rows[("type_1a", 2)]["requested_state"], 16)
        self.assertEqual(rows[("type_1a", 2)]["x_speed"], 0x700)
        self.assertEqual(rows[("type_1a", 0)]["x_speed"], 0)

    def test_state_reach(self):
        sr = D["state_reach"]
        probing = set(sr["states_that_may_probe"])
        for st in ("0x01", "0x05", "0x06", "0x09", "0x0A", "0x0B", "0x0E", "0x1B", "0x1C"):
            self.assertIn(st, probing)
        for st in ("0x0C", "0x0D", "0x13", "0x20", "0x22"):
            self.assertIn(st, sr["states_that_do_not"])
        self.assertEqual(sr["excluded_states"], ["0x37", "0x38", "0x39", "0x3A", "0x3B", "0x3C"])

    def test_forced_states_agree_with_static_reach(self):
        rows = {r["state"]: r for r in D["emulated_forced_states"]["rows"]}
        for st in ("0x01", "0x05", "0x06", "0x09", "0x0A", "0x0B", "0x0E", "0x1B", "0x1C"):
            self.assertGreater(rows[st]["frames_in_state"], 0)
            self.assertEqual(rows[st]["probe_calls_in_state"], rows[st]["frames_in_state"], st)
        for st in ("0x0C", "0x0D", "0x13", "0x22"):
            self.assertGreater(rows[st]["frames_in_state"], 0)
            self.assertEqual(rows[st]["probe_calls_in_state"], 0, st)

    def test_timer_bit_is_the_animation_countdown(self):
        frac = {r["state"]: r["bit0_set_fraction"] for r in D["timer_fixture"]["states"]}
        self.assertEqual(frac["0x09"], 0.68)        # rolling: durations 3,2,1 -> bit 0 set 2/3 of the updates
        self.assertEqual(frac["0x0A"], 0.68)        # jump
        self.assertLess(frac["0x05"], 0.5)
        seq = {r["state"]: r["plus07_after_each_engine_update_first_26"] for r in D["timer_fixture"]["states"]}
        self.assertEqual(seq["0x09"][:6], [3, 2, 1, 3, 2, 1])
        self.assertEqual(seq["0x05"][:11], [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 10])
        h = D["emulated_play"]["by_state_bit0_clear_set"]
        self.assertGreater(h["0x0A"][1], 1.8 * h["0x0A"][0])     # played jumps: odd twice as often as even

    def test_frame_order(self):
        e = D["emulated_play"]
        self.assertGreater(e["probe_calls"], 4000)
        self.assertGreaterEqual(e["frames_where_x_and_y_integration_precede_the_probe"], 0.99 * e["frames_with_a_probe"])
        self.assertGreaterEqual(e["frames_where_clamp_precedes_the_probe"], 0.99 * e["frames_with_a_probe"])
        same, total = e["probe_position_equals_same_frame_end_position"]
        self.assertGreaterEqual(same, 0.98 * total)
        top = next(iter(e["event_sequences_per_frame"]))
        self.assertEqual(top, "step_3fef > clamp > x_integrate > y_integrate > probe > move_48bc")


@unittest.skipUnless(ROM_BYTES, "matching ROM not found (set SONIC_CHAOS_ROM)")
class RomBackedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pres, cls.repl = trc.tables(ROM_BYTES)

    def test_routine_hashes(self):
        table = {r["name"]: r for r in trc.routine_table(ROM_BYTES)}
        for r in D["routines"]:
            self.assertEqual(table[r["name"]]["sha256"], r["sha256"], r["name"])

    def test_tables_match_the_cache(self):
        self.assertEqual(trc.quadrant_tables(ROM_BYTES), D["quadrant_tables"])
        self.assertEqual(trc.header_types(ROM_BYTES), D["header_types"])

    def test_random_points_over_whole_levels(self):
        """Seeded random points anywhere in THZ1/THZ2/THZ3 (not only near rings): collected iff the model says so."""
        rng = random.Random(20260930)
        n = hits = 0
        for act in ("thz1", "thz2", "thz3"):
            lab = trc.Lab(ROM_BYTES)
            rows = layout_rows(act)
            lab.set_layout(rows)
            ring_cells = [(cx, cy) for cy, r in enumerate(rows) for cx, b in enumerate(r) if b in self.pres]
            for i in range(6000):
                if i % 2:
                    cx, cy = rng.choice(ring_cells)
                    x = cx * 32 + rng.randrange(-6, 38)
                    y = cy * 32 + rng.randrange(-30, 62)
                else:
                    x = rng.randrange(0, len(rows[0]) * 32)
                    y = rng.randrange(-20, len(rows) * 32 + 8)
                bit0 = rng.randrange(2)
                px, py = trc.probe_point(x, y, bit0)
                in_map = (px >> 5) < lab.width and (py >> 5) < len(rows)
                paddr = lab.cell_addr(px >> 5, py >> 5) if in_map else None
                block = rows[py >> 5][px >> 5] if in_map else 0
                if paddr is not None:
                    lab.m[paddr] = block
                t = lab.trial(x, y, bit0, vx=rng.choice((0, 0x600, 0xFA00)), vy=rng.choice((0, 0x500, 0xFB00)), req=rng.choice((1, 5, 9, 10, 11, 14)))
                want = trc.collects(block, px, py, self.pres)
                n += 1
                hits += want
                self.assertEqual(t["counter"] == 1, want, (act, x, y, bit0))
                if want:
                    cell_after = lab.m[paddr]
                    quad = trc.quadrant(px, py)
                    self.assertEqual(cell_after, self.repl[block][quad], (act, x, y, bit0))
                    self.assertEqual(t["effect_xy"], (px, py))
                    lab.m[paddr] = block
        self.assertGreater(n, 15000)
        self.assertGreater(hits, 1000)

    def test_exact_edges_for_random_rings_in_every_act(self):
        rng = random.Random(77)
        for act in ("thz1", "thz2", "thz3"):
            lab = trc.Lab(ROM_BYTES)
            rows = layout_rows(act)
            lab.set_layout(rows)
            rq = [r for r in trc.ring_quadrants(rows, self.pres)]
            for r in rng.sample(rq, min(12, len(rq))):
                cx, cy = r["cell"]
                addr = lab.cell_addr(cx, cy)
                orig = rows[cy][cx]
                for bit0 in (0, 1):
                    reg = trc.anchor_region(r["left"], r["top"], bit0)
                    # isolate: the probe must stay inside this quadrant, so test the edge row/column exactly
                    for x, y, want in ((reg["x"][0], reg["y"][0], True), (reg["x"][1], reg["y"][1], True), (reg["x"][0] - 1, reg["y"][0], False) if (r["left"] & 31) else (None, None, None),
                                       (reg["x"][0], reg["y"][0] - 1, False) if (r["top"] & 31) else (None, None, None)):
                        if x is None:
                            continue
                        lab.m[addr] = orig
                        got = lab.trial(x, y, bit0)["counter"] == 1
                        # a neighbouring quadrant of the same cell may legitimately collect when the probe lands there
                        px, py = trc.probe_point(x, y, bit0)
                        block = rows[py >> 5][px >> 5]
                        self.assertEqual(got, trc.collects(block, px, py, self.pres))
                        if (px >> 4 << 4, py >> 4 << 4) == (r["left"], r["top"]):
                            self.assertTrue(got)
                        lab.m[addr] = orig

    def test_cache_static_part_regenerates(self):
        fresh = trc.build(ROM_BYTES, static_only=True)
        for key in ("routines", "header_types", "quadrant_tables", "act_rings", "model", "state_reach", "unresolved"):
            self.assertEqual(fresh[key], D[key], key)


if __name__ == "__main__":
    unittest.main()

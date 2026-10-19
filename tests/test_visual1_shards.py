"""VISUAL-1 Part B: surface-$0D breakable terrain and its four type-$07 shards (THZ2 corridor primary fixture).

``CommittedCache`` needs no ROM.  ``Regeneration`` re-executes the original ROM (set SONIC_CHAOS_ROM) and must reproduce the cache.
"""
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import visual1_shards as V

CACHE = ROOT / "data/rom-cache/visual1/shards-thz2.json"
CONTRACT = ROOT / "data/visual1/shard-contract.json"


def find_rom():
    for candidate in (os.environ.get("SONIC_CHAOS_ROM"), ROOT.parent / "Sonic Chaos (Europe).sms",
                      ROOT.parent / "source" / "Sonic Chaos (Europe).sms"):
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    return None


class CommittedCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(CACHE.read_text(encoding="utf-8"))
        cls.s = cls.d["static"]
        cls.e = cls.d["emulated"]
        cls.p = cls.e["primary_corridor"]
        cls.c = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_assembly_chain_verified(self):
        for name in ("break_7898", "floor_6b2c", "side_right_72b6", "side_left_72dd", "ceiling_7464", "spawn_5e9c", "init_9b11", "move_9bb5", "gravity_5f84",
                     "move_60fb", "cull_61e1", "shard_art_loader_79f2", "level_loader_call_site_295b", "sound_67d5"):
            self.assertIn(name, self.s["assembly"])
            self.assertGreater(self.s["assembly"][name]["verified_subsequence_length"], 3)

    def test_type7_scripts(self):
        st = self.s["type7_scripts"]["states"]
        self.assertEqual([(o["op"], o["operands"]) for o in st[0]["ops"][:1]], [("FF 06", "a3")])
        rec0 = [o for o in st[0]["ops"] if o["op"] == "record"]
        self.assertEqual([(o["duration"], o["frame"], o["callback"]) for o in rec0], [(1, 0, "0x9B11")])
        rec1 = [o for o in st[1]["ops"] if o["op"] == "record"]
        self.assertEqual([(o["duration"], o["frame"], o["callback"]) for o in rec1], [(128, 15, "0x9BB5")])

    def test_offset_tables_exact(self):
        t = self.s["offset_tables"]
        ge = [(r["x_offset"], r["y_offset"], r["x_speed_8_8"], r["y_speed_8_8"]) for r in t["player_x_speed_ge_0_table_9b75"]]
        lt = [(r["x_offset"], r["y_offset"], r["x_speed_8_8"], r["y_speed_8_8"]) for r in t["player_x_speed_lt_0_table_9b95"]]
        self.assertEqual(ge, [(4, 0, -512, -1024), (20, 0, 128, -768), (4, 20, -512, -256), (20, 20, 128, -512)])
        self.assertEqual(lt, [(4, 0, -128, -768), (20, 0, 512, -1024), (4, 20, -128, -512), (20, 20, 512, -256)])

    def test_mapping_and_registration(self):
        m = self.s["mapping"]["frames"]
        self.assertEqual(m["0"]["pieces"], [])
        self.assertEqual(m["15"]["pieces"], [{"rel_x": -4, "rel_y": -16, "tile": "0x66"}])

    def test_gravity_constants(self):
        g = self.s["gravity"]
        self.assertEqual((g["gravity_8_8"], g["terminal_8_8"]), (0xC0, 0x0FC0))

    def test_cull_table_window(self):
        c = self.s["cull_table"]
        self.assertEqual((c["on_screen_cell_columns"]["screen_x_from"], c["on_screen_cell_columns"]["screen_x_to"]), (-32, 287))
        self.assertEqual((c["on_screen_cell_rows"]["screen_y_from"], c["on_screen_cell_rows"]["screen_y_to"]), (-32, 287))
        self.assertEqual(c["rows_text"][12], "33222211000000000000000011222233")

    def test_census(self):
        acts = self.s["census_surface_0d"]["acts"]
        self.assertEqual(acts["0/1"]["cell_list"], [[4, 22], [5, 22], [6, 22], [9, 22], [10, 22], [11, 22]])
        self.assertEqual(acts["0/1"]["by_block"], {"0x9C": 6})
        self.assertNotIn("0/0", acts)                        # THZ1 has no $0D cell
        self.assertEqual(acts["11/0"]["cells"], 41)          # SS4
        for z in ("8/0", "9/0", "10/0", "12/0"):
            self.assertNotIn(z, acts)                        # the other special stages have none
        self.assertEqual(sum(a["cells"] for k, a in acts.items() if k.startswith("2/")), 139 + 6 + 13 + 87 + 7 + 1)

    def test_shard_art_streams_per_zone(self):
        z = self.s["shard_art_streams"]["zones"]
        half = {k: v["visible_half"] for k, v in z.items()}
        self.assertEqual(half, {"0": "bottom", "1": "bottom", "2": "top", "3": "bottom", "4": "top", "5": "bottom", "6": "bottom", "7": "bottom",
                                "8": "top", "9": "top", "10": "top", "11": "top", "12": "top"})
        self.assertEqual({v["decoded_tiles"] for v in z.values()}, {2})
        self.assertEqual(self.s["shard_art_streams"]["streams_shared_by_zones"]["0xA3C0"], [0, 6, 7])

    def test_corridor_primary_fixture(self):
        p = self.p
        self.assertEqual(p["start_anchor"], [404, 718])
        cells = [tuple(b["cell"]) for b in p["breaks"]]
        self.assertEqual(sorted(cells), [(4, 22), (5, 22), (6, 22), (9, 22), (10, 22), (11, 22)])
        self.assertEqual(cells, [(11, 22), (10, 22), (9, 22), (6, 22), (5, 22), (4, 22)])       # right to left
        self.assertEqual({b["player"]["state"] for b in p["breaks"]}, {0x10})                  # spin-dash roll
        self.assertTrue(all(b["player"]["vx"] < 0 and b["player"]["flags03"] & 2 for b in p["breaks"]))
        self.assertEqual(p["summary"]["shards_created"], 21)
        self.assertEqual(p["summary"]["dropped_by_break"], [0, 0, 0, 2, 1, 0])
        self.assertTrue(p["summary"]["all_model_matches"])
        self.assertEqual(p["model_check"]["mismatches"], 0)
        self.assertEqual((p["lives"]["before"], p["lives"]["after"]), (3, 4))                   # the extra-life monitor was reached
        for b in p["breaks"]:
            self.assertEqual(b["d3b2_at_break"], 0)                                             # side path never writes $D3B2
            self.assertEqual(len(b["sound_writes"]), b["shards_created"])          # a dropped request creates no object, hence no sound
            self.assertEqual({w["value"] for w in b["sound_writes"]}, {"0xA3"})

    def test_shard_trajectories(self):
        for sh in self.p["shards"]:
            self.assertTrue(sh["model_matches_trace"])
            self.assertEqual(sh["init"]["table"], "9B95")                                      # Sonic moves left
            # first sprite tick is the one after the break tick, deletion at least 22 updates later
            self.assertEqual(sh["first_sprite_update"], sh["spawn_update"] + 1)
            self.assertGreaterEqual(sh["ticks_alive"], 22)
            self.assertLessEqual(sh["ticks_alive"], 30)
            self.assertEqual(sh["trace"][0][7], 0)                                             # mapping frame 0 in the break tick
            self.assertTrue(all(r[7] == 15 for r in sh["trace"][1:]))
            self.assertEqual(sh["trace"][1][8], 128)                                           # record timer starts at 128
        quadrant_offsets = {(0, 4, 0), (1, 20, 0), (2, 4, 20), (3, 20, 20)}
        for sh in self.p["shards"]:
            b = self.p["breaks"][sh["break_index"]]
            self.assertIn((sh["quadrant"], sh["init"]["x"] - b["cell_world"][0], sh["init"]["y"] - b["cell_world"][1]), quadrant_offsets)

    def test_lifetimes_are_cull_driven(self):
        for sh in self.p["shards"]:
            sx, sy = sh["delete"]["screen"]
            self.assertTrue(sx >= 288 or sy >= 288 or sx < -32, sh["delete"])                  # beyond the +/-32 margin of the 256 x 256 box
            self.assertEqual(sh["delete"]["flags04"] & 0x40, 0x40)

    def test_hole_appears_in_the_break_frame(self):
        for row in self.p["timeline"]["per_break"]:
            self.assertEqual(row["first_video_frame_with_new_nametable"], row["break_video_frame"])
        for c in self.p["nametable"]["cells"]:
            self.assertTrue(c["all_frames_after_are_block_9d"])
            self.assertEqual(c["frames_as_block_9d_before"], 0)
            self.assertGreater(c["frames_as_block_9c_before"], 0)

    def test_sound(self):
        s = self.p["sound"]
        self.assertEqual(s["request"], "0xA3")
        self.assertEqual(s["priority_byte_rom_0906F_plus_id_minus_1"]["value"], "0x58")
        self.assertTrue(all(r["accept_by_rule"] for r in s["per_break"]))

    def test_art_matches_static_stream(self):
        art = self.p["art"]
        st = self.s["shard_art_streams"]["zones"]["0"]
        self.assertEqual(art["rgba_sha256"], st["rgba_sha256"])
        self.assertEqual((art["top_tile_opaque_pixels"], art["bottom_tile_opaque_pixels"]), (0, 64))
        self.assertEqual(art["opaque_bbox_in_8x16"], [0, 8, 7, 15])

    def test_floor_fixtures_in_other_zones(self):
        ff = self.e["floor_fixtures"]
        for key in ("2/0", "2/1", "2/2", "3/0", "3/1", "4/0", "4/1", "4/2", "5/1", "11/0"):
            r = ff[key]
            self.assertEqual(r["handler_used"], ["floor_6b2c"])
            self.assertEqual(r["model_mismatches"], 0)
            self.assertTrue(r["static_stream_rgba_equals_emulated"])
            self.assertEqual(r["breaks"][0]["shards_created"], 4)
            self.assertEqual({s["init"]["table"] for s in r["shards"]}, {"9B75"})              # standing/falling player: X speed >= 0
        for key in ("0/1", "0/2", "1/0", "1/1", "5/0", "6/1", "6/2"):
            self.assertIn("status", ff[key])
        self.assertIn("floor path not applicable", ff["0/1"]["status"])
        self.assertTrue(self.e["type13_crumble_cross_check"]["live_equals_static_final_stream"])

    def test_controls(self):
        c = self.e["controls"]
        self.assertEqual(c["walk_left_no_roll"]["breaks"], 0)
        self.assertGreater(c["roll_left_hi4"]["breaks"], 0)
        self.assertGreater(c["roll_left_hi3"]["breaks"], 0)
        self.assertEqual(c["roll_left_hi2"]["breaks"], 0)                                      # |speed high byte| < 3: no break
        self.assertEqual(c["roll_right_hi4_from_monitor_room"]["table_used"], ["9B75"])
        self.assertEqual(c["roll_left_hi4"]["table_used"], ["9B95"])

    def test_spin_dash_sweep_is_stable(self):
        sw = self.e["spin_dash_sweep"]
        self.assertEqual(set(sw), {"1", "2", "3", "4"})
        for v in sw.values():
            self.assertEqual(v["breaks"], 6)
            self.assertEqual(v["lives_after"], 4)
            self.assertTrue(v["summary"]["all_model_matches"])
            self.assertEqual(v["summary"]["shards_dropped"], 3)

    def test_poc_findings(self):
        poc = self.d["poc"]
        self.assertFalse(poc["break_function"]["creates_instance"])
        self.assertFalse(poc["break_function"]["plays_sound"])
        self.assertFalse(poc["fragment_objects"]["type07_object_in_poc"])
        self.assertEqual(poc["fragment_objects"]["sound_a3_requests"], ["scripts/SCR_chaos_sez_s2/SCR_chaos_sez_s2.gml:118"])   # type $13 only
        for name in ("SPR_chaos_sez_shard", "SPR_chaos_ss4_shard"):
            sp = poc["sprites"][name]
            self.assertTrue(all(sp["equals_rom_pre_override_common_stream"].values()))
            self.assertFalse(any(sp["equals_rom_final_stream_79f2"].values()))
            self.assertFalse(any(sp["alpha_mask_equals_rom_final_stream_79f2"].values()))
        for name in ("SPR_chaos_thz2_block_9d", "SPR_chaos_sez_block_9d", "SPR_chaos_mghz_block_9d"):
            self.assertIn("trimmed", poc["sprites"][name])

    def test_contract_is_consistent_with_the_cache(self):
        c = self.c
        self.assertEqual(c["spawn"]["objects"], 4)
        self.assertEqual(c["spawn"]["observed_drops"]["shards_created_per_break"], [4, 4, 4, 2, 3, 4])
        self.assertEqual(c["per_tick"]["integration"], "x24 += vx; vy := vy + 192 (unless the sum is >= $1000); y24 += vy (gravity BEFORE the move)")
        t = c["trajectory_relative_to_cell_origin"]["player_x_speed_hi_lt_0"]["1"]
        self.assertEqual((t["x_8_8"][0], t["y_8_8"][0]), (20 * 256, 0))
        self.assertEqual(t["y_8_8"][1], 0 + (-1024 + 192))
        self.assertEqual(c["art"]["per_zone"]["2"]["visible_half"], "top")
        self.assertIn("no object, sprite, sound or timing", c["differs_from_thz1_block_47"]["conclusion"])


class ModelUnit(unittest.TestCase):
    """Closed-form model checks that need no ROM."""

    TABLE = [{"x_offset": 4, "y_offset": 0, "x_speed_8_8": -128, "y_speed_8_8": -768}] * 4

    def test_gravity_before_move(self):
        m = V.model_shard(self.TABLE, 0, 0, 0, 2)
        self.assertEqual([r["vy"] for r in m], [-768, -576, -384])
        self.assertEqual([r["y"] for r in m], [0.0, -2.25, -3.75])

    def test_terminal_velocity_holds(self):
        m = V.model_shard(self.TABLE, 0, 0, 0, 40)
        self.assertEqual(max(r["vy"] for r in m), 0x0FC0)
        self.assertEqual(m[-1]["vy"], 0x0FC0)

    def test_negative_control_wrong_gravity_differs(self):
        a = V.model_shard(self.TABLE, 0, 0, 0, 10)
        b = V.model_shard(self.TABLE, 0, 0, 0, 10, gravity=0x200)
        self.assertNotEqual([r["y"] for r in a], [r["y"] for r in b])


@unittest.skipIf(find_rom() is None, "ROM not supplied (set SONIC_CHAOS_ROM)")
class Regeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = V.R.load(find_rom())
        cls.cached = json.loads(CACHE.read_text(encoding="utf-8"))

    def test_static_section_regenerates_exactly(self):
        fresh = V.build(self.rom, static_only=True)
        self.assertEqual(json.loads(json.dumps(fresh["static"])), self.cached["static"])

    def test_primary_corridor_replays(self):
        tables = V.offset_tables(self.rom)
        rep, run, art = V.corridor_report(self.rom, None, tables)
        got = json.loads(json.dumps(V.clean(rep)))
        want = self.cached["emulated"]["primary_corridor"]
        for key in ("breaks", "shards", "summary", "sound", "model_check", "nametable", "timeline"):
            self.assertEqual(got[key], want[key], key)

    def test_floor_path_in_sez_regenerates(self):
        tables = V.offset_tables(self.rom)
        fx = V.floor_fixtures(self.rom, tables, None)
        want = self.cached["emulated"]["floor_fixtures"]["2/0"]
        self.assertEqual(json.loads(json.dumps(V.clean(fx["2/0"]))), want)

    def test_negative_control_tampered_model_fails_against_the_original(self):
        tables = V.offset_tables(self.rom)
        run = V.run_scenario(self.rom, 0, 1, V.SPIN_DASH_START, 120, pad=lambda f: V.corridor_pad(f, 4), watch=V.CORRIDOR_CELLS)
        good = V.build_shards(self.rom, run, tables)
        self.assertEqual(good["model_check"]["mismatches"], 0)
        tables["player_x_speed_lt_0_table_9b95"][1]["x_speed_8_8"] += 1                      # tamper with one table entry
        bad = V.build_shards(self.rom, run, tables)
        self.assertGreater(bad["model_check"]["mismatches"], 0)

    def test_rom_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            V.build(self.rom[:-1] + b"\x00", static_only=True)


if __name__ == "__main__":
    unittest.main()

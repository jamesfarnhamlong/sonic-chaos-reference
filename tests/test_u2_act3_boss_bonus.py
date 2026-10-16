#!/usr/bin/env python3
"""U2-A tests: Act 3 boss clear and bonus-object tracing.

Every test class names its evidence tier: SOURCE (decoded bytes), CONTROLLED (Z80 oracle), EMULATED (unmodified ROM, fixture-driven fights), FIXTURE (injected RAM, i.e. NOT a
natural clear) and POC SOURCE-READ (GameMaker source transcribed, never run).  Part 1 needs no ROM; part 2 needs the canonical ROM, Python >= 3.10 and the `z80` package.
The complete regeneration check is `python tools/u2_act3_boss_bonus.py ROM --check` (about five minutes).
"""
import copy
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import u2_act3_boss_bonus as U  # noqa: E402
import u3_sign_prizes as U3  # noqa: E402

ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")))
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == 524288 and hashlib.sha256(data).hexdigest() == ROM_SHA:
            return data
    return None


def poc_boss_bonus_h(seconds):
    """POC SOURCE-READ: chaos_boss_bonus in SCR_chaos_boss.gml (G1-D d9275fe) transcribed, not executed."""
    return max(0, 9 - seconds // 30)


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st = U.load_json(U.STATIC_JSON)
        cls.ctl = U.load_json(U.CONTROLLED_JSON)
        cls.ob = U.load_json(U.OBS_JSON)
        cls.tt = U.time_table_of_u3()
        cls.fights = cls.ob["fights"]
        cls.inj = cls.ob["injected_clears"]


class SourceTier(Base):
    """SOURCE: decoded ROM bytes and the committed census."""

    def test_identity_and_canonical_files(self):
        for d in (self.st, self.ctl, self.ob):
            self.assertEqual(d["rom_sha256"], ROM_SHA)
            self.assertEqual(d["base_commit"], "1fb25857470f7c867d763c435a324befea751c12")
        for path in (U.STATIC_JSON, U.CONTROLLED_JSON, U.OBS_JSON):
            self.assertEqual(U.dumps(json.loads(path.read_text(encoding="utf-8"))), path.read_text(encoding="utf-8"))

    def test_validators_pass(self):
        self.assertEqual(U.validate_static(self.st), [])
        self.assertEqual(U.validate_controlled(self.ctl, self.st), [])
        self.assertEqual(U.validate_observed(self.ob, self.st), [])

    def test_anchors(self):
        self.assertGreaterEqual(len(self.st["anchors"]), 13)
        for a in self.st["anchors"]:
            self.assertTrue(a["ok"], a["name"])
            self.assertEqual(a["expected"], a["actual"])

    def test_fixed_boss_bonus_table_is_separate_from_the_word(self):
        fb = self.st["fixed_boss_bonus"]
        self.assertEqual(fb["steps"], [50, 100, 150, 200, 250, 600])
        self.assertEqual(fb["raw_units"], [500, 1000, 1500, 2000, 2500, 6000])
        self.assertEqual(fb["used_zones"], [0, 1, 2, 3, 4])

    def test_only_two_immediate_allocation_sites_for_type_0A(self):
        sites = self.st["bonus_object_allocation_sites"]["immediate_creator_calls"]
        self.assertEqual({s["cpu"] for s in sites}, {"81E2", "9D4E"})
        for s in sites:
            self.assertEqual(s["bytes"][:10], "0e0a2600cd")      # LD C,$0A / LD H,0 / CALL

    def test_release_callback_owners(self):
        own = {(o["type"], o["state"]) for o in self.st["release_callback_references"]["81BD"]["script_owners"]}
        self.assertEqual(own, {("50", 5), ("54", 5), ("56", 5), ("60", 5), ("59", 5)})
        self.assertEqual({(o["type"], o["state"]) for o in self.st["release_callback_references"]["9D26"]["script_owners"]}, {("51", 14)})
        self.assertNotIn(("61", 5), own)                       # EEZ's controller never calls the shared release

    def test_zone_records(self):
        z = self.st["zones"]
        self.assertEqual([z[k]["zone"] for k in "012345"], list(U.ZONES))
        self.assertEqual([z[k]["controller"] for k in "012345"], ["50", "51", "54", "56", "59", "61"])
        self.assertIn("NONE", z["5"]["producer"])
        self.assertIn("3356", z["3"]["gate"])

    def test_bonus_object_script_and_states(self):
        o = self.st["bonus_object_0A"]
        self.assertEqual(len(o["states"]), 3)
        self.assertEqual([x["op"] for x in o["script_state0"]], ["record", "restart_state"])
        self.assertEqual(o["script_state0"][0]["callback"], "9C86")
        spawns = [x for x in o["script_state2"] if x["op"] == "spawn"]
        self.assertEqual({(s["type"], s["parameter"]) for s in spawns}, {("0A", "FF")})
        self.assertIn("0C:9C96", " ".join(o["writers_of_D2A6"]))

    def test_eez_script_spawns_only_parameter_one_sparkles(self):
        sp = self.st["bonus_object_allocation_sites"]["script_spawn_ops"]
        self.assertEqual([(s["type"], s["parameter"], s["dx"]) for s in sp], [("0A", "01", 4), ("0A", "01", -4)])

    def test_g0_spine_disclosure_distinguishes_forced_and_natural(self):
        g = self.st["g0_spine_disclosure"]
        self.assertEqual((g["natural_sign_chain"], g["injected_or_forced"], len(g["rows"])), (2, 16, 18))
        boss = [r for r in g["rows"] if r["act"] == 2]
        self.assertEqual(len(boss), 6)
        self.assertEqual(sum("forced player state" in r["how"] for r in boss), 1)
        self.assertEqual(sum("act-clear flag raised" in r["how"] for r in boss), 5)

    def test_negative_corrupted_static_is_detected(self):
        bad = copy.deepcopy(self.st)
        bad["fixed_boss_bonus"]["steps"][0] = 49
        self.assertTrue(U.validate_static(bad))
        bad = copy.deepcopy(self.st)
        bad["anchors"][0]["ok"] = False
        self.assertTrue(U.validate_static(bad))
        bad = copy.deepcopy(self.st)
        bad["release_callback_references"]["81BD"]["script_owners"] = [o for o in bad["release_callback_references"]["81BD"]["script_owners"] if o["type"] != "56"]
        self.assertTrue(U.validate_static(bad))


class ControlledTier(Base):
    """CONTROLLED: original routines on the Z80 core with hand-built slots (FIXTURE disclosed in the record)."""

    def row(self, t, floor, px):
        return next(r for r in self.ctl["release"]["rows"] if r["type_before"] == t and r["floor"] == floor and r["player_x"] == px)

    def test_release_requires_floor_bit_and_requests_state20_once(self):
        for t, px in (("50", 3000), ("54", 3000), ("59", 3000), ("56", 3356)):
            on, off = self.row(t, 2, px), self.row(t, 0, px)
            self.assertEqual((on["boss_type_after"], on["player_requested_state"], on["sound"], on["right_limit"]), ("0F", "20", "97", 2304), t)
            self.assertEqual([(c["type"], c["parameter"]) for c in on["created"]], [("0A", 0)], t)
            self.assertEqual(on["D2A6"], 0)             # the object, not the release, writes D2A6 (one update later)
            self.assertEqual((off["boss_type_after"], off["created"], off["player_requested_state"]), (t, [], "05"), t)

    def test_mghz_world_x_gate_and_missing_left_limit_write(self):
        self.assertEqual(self.row("56", 2, 3355)["created"], [])
        self.assertEqual(self.row("56", 2, 3355)["boss_type_after"], "56")
        self.assertEqual(self.row("56", 2, 3356)["boss_type_after"], "0F")
        self.assertEqual(self.row("56", 2, 3356)["left_limit"], 0)       # $81F4 branch does not write D280
        self.assertEqual(self.row("50", 2, 3000)["left_limit"], 3060)

    def test_gpz_head_release(self):
        g, off = self.row("51", 2, 1700), self.row("51", 0, 1700)
        self.assertEqual((g["boss_type_after"], g["player_requested_state"], g["right_limit"], [c["type"] for c in g["created"]]), ("FF", "20", 1920, ["0A"]))
        self.assertEqual(off["created"], [])

    def test_state20_sound_follows_act_index(self):
        self.assertEqual(self.ctl["release_act_index_sound"], {"0": "89", "1": "89", "2": "97"})

    def test_absent_0A_is_not_replaced_by_a_fallback(self):
        af = self.ctl["allocation_failure"]
        self.assertEqual((af["created"], af["boss_type_after"], af["player_requested_state"], af["D2A6"]), ([], "0F", "20", 0))

    def test_only_parameter_zero_writes_D2A6_and_never_awards_a_life(self):
        rows = {r["parameter"]: r for r in self.ctl["bonus_object_parameters"]["rows"]}
        self.assertEqual(rows["00"]["D2A6"], "0936")
        self.assertEqual(rows["00"]["requested_state"], 2)
        for k in ("01", "80", "FF"):
            self.assertEqual((rows[k]["D2A6"], rows[k]["requested_state"]), ("BEEF", 1))
        self.assertTrue(all(r["lives"] == "12" for r in rows.values()))

    def test_word_grid_equals_the_u3_model_and_keeps_zero(self):
        g = self.ctl["bonus_word_grid"]
        self.assertEqual(len(g["times"]), 21)
        for tm, row in g["rows"].items():
            self.assertEqual(len(row), 100)
            for n, w in enumerate(row):
                self.assertEqual(w, U.model_bonus_word(self.tt, int(tm, 16), U3.int_to_bcd(n)), (tm, n))
        self.assertEqual(g["zero_words_left_as_zero"], [["0459", "11"], ["0900", "11"]])
        # the sign child would replace those two by $0777 (U3); the boss object does not
        self.assertEqual(U3.child_bonus(self.tt, 0x0459, 0x11)[0], 0x0777)
        self.assertEqual(g["rows"]["0459"][11], 0)

    def test_equal_digit_words_exist_but_no_life_is_possible_from_0A(self):
        g = self.ctl["bonus_word_grid"]
        eq = [(tm, n) for tm, row in g["rows"].items() for n, w in enumerate(row) if w and ((w >> 8) == ((w >> 4) & 15) == (w & 15))]
        self.assertEqual(len(eq), 19)          # the 21 U3 equal-digit cases minus the two zero words that stay zero here
        self.assertTrue(all(r["lives"] == "12" for r in self.ctl["bonus_object_parameters"]["rows"]))

    def test_negative_corrupted_controlled_is_detected(self):
        bad = copy.deepcopy(self.ctl)
        bad["bonus_word_grid"]["rows"]["0029"][50] ^= 1
        self.assertTrue(U.validate_controlled(bad, self.st))
        bad = copy.deepcopy(self.ctl)
        bad["release"]["rows"][1]["created"] = []
        self.assertTrue(U.validate_controlled(bad, self.st))
        bad = copy.deepcopy(self.ctl)
        bad["allocation_failure"]["created"] = [dict(type="0A")]
        self.assertTrue(U.validate_controlled(bad, self.st))


class EmulatedTier(Base):
    """EMULATED: whole boss fights/clears of the unmodified ROM; the player is placed/attacks by fixture writes (see each record's `fixtures`)."""

    ORDINARY = ("THZ3", "GPZ3", "SEZ3", "MGHZ3", "AQZ3")

    def test_each_ordinary_boss_clear_happens_exactly_once(self):
        for k in self.ORDINARY:
            c = self.fights[k]["counts"]
            self.assertEqual((c["boss_bonus_loop"], c["tally_loops"], c["results_card"], c["zone_increment"], c["bonus_objects_param0"], c["D2A6_sets"], c["flag_bit4_set"]), (1,) * 7, k)

    def test_fixed_bonus_and_word_are_separate_score_components(self):
        for i, k in enumerate(self.ORDINARY):
            sc = self.fights[k]["score"]
            self.assertEqual(sc["fixed_bonus"], [500, 1000, 1500, 2000, 2500][i], k)
            self.assertEqual(sc["tally_total"], sc["ring_units"] + sc["word_units"], k)
            self.assertEqual(sc["ring_units"], 470)                                 # rings $47 (fixture) x 10
            self.assertEqual(self.fights[k]["retained"]["score_after"], sc["fixed_bonus"] + sc["tally_total"], k)
            self.assertNotEqual(sc["word_units"], 0)

    def test_D2A6_value_follows_the_model_at_the_compute_update(self):
        for k in self.ORDINARY:
            comp = self.fights[k]["bonus_compute_inputs"][0]
            word = self.fights[k]["D2A6_sets"][0]["word"]
            tm = comp["time"][0] << 8 | comp["time"][1]
            self.assertEqual(word, U.model_bonus_word(self.tt, tm, comp["rings"]), k)
        self.assertEqual({self.fights[k]["D2A6_sets"][0]["word"] for k in ("THZ3", "GPZ3", "SEZ3", "MGHZ3")}, {0x0936})
        self.assertEqual(self.fights["AQZ3"]["D2A6_sets"][0]["word"], 0x0836)       # 0:40 -> H = 8

    def test_object_0A_is_created_by_the_release_in_the_state20_update_and_writes_one_update_later(self):
        for k in self.ORDINARY:
            r = self.fights[k]
            s20 = [s for s in r["state20_requests"] if s["bank"] == 30][0]
            created = r["bonus_objects_created"][0][0]
            # frame conventions: hook events carry the frame being run, polled events the frame just completed (+1)
            self.assertEqual(created - s20["frame"], 1, k)                       # polled creation = the update after the release update's hook
            self.assertEqual(r["bonus_compute_inputs"][0]["frame"], created, k)  # $9C93 runs in the object's first update = the next update
            self.assertEqual(r["D2A6_sets"][0]["frame"] - r["bonus_compute_inputs"][0]["frame"], 1, k)
            self.assertEqual(s20["act_index"], 2)
        self.assertEqual({self.fights[k]["state20_requests"][0]["caller"] for k in ("THZ3", "SEZ3", "MGHZ3", "AQZ3")}, {"81E2"})
        self.assertEqual(self.fights["GPZ3"]["state20_requests"][0]["caller"], "5E55")     # JP $03F5 at $9D55 returns to the scheduler

    def test_flag_chain_order_and_results_spacing(self):
        for k in self.ORDINARY:
            tf = self.fights[k]["tail_frames"]
            self.assertLess(self.fights[k]["state20_requests"][0]["frame"], tf["flag_bit4_set"][0])
            self.assertEqual(tf["zone_clear_tail"][0] - tf["flag_bit4_set"][0], 1)
            self.assertIn(tf["results_card"][0] - tf["flag_bit4_set"][0], (198, 199))
            self.assertEqual(tf["zone_results_gate"][0], tf["results_card"][0])
            self.assertLess(tf["boss_bonus_loop"][0], tf["tally_loops"][0])
            self.assertLess(tf["tally_loops"][0], tf["zone_increment"][0])
            self.assertEqual([w[2] for w in self.fights[k]["D293_writes"]], [0x50])

    def test_mghz_clears_one_frame_after_the_request(self):
        tf = self.fights["MGHZ3"]["tail_frames"]
        self.assertEqual(tf["flag_bit4_set"][0] - self.fights["MGHZ3"]["state20_requests"][0]["frame"], 1)
        self.assertEqual(len(self.fights["MGHZ3"]["bonus_objects_created"]), 1)       # no time for sparkles
        for k in ("THZ3", "GPZ3", "SEZ3", "AQZ3"):
            self.assertGreater(len(self.fights[k]["bonus_objects_created"]), 1)

    def test_zone_rollover_retains_run_state_and_lands_on_the_rq4_start(self):
        rq4 = U.load_json(ROOT / "data" / "rq4" / "start-registration.json")["static"]["table"]
        for i, k in enumerate(self.ORDINARY):
            r = self.fights[k]["retained"]
            self.assertEqual(r["zone_act_after"], [i + 1, 0])
            self.assertEqual((r["lives"][0], r["continues"][0], r["emeralds"][0]), (r["lives"][1], r["continues"][1], r["emeralds"][1]))
            want = next(x for x in rq4 if x["zone"] == i + 1 and x["act"] == 0)
            self.assertEqual(self.fights[k]["next_start"]["player"], want["player"])
            self.assertEqual(self.fights[k]["next_start"]["camera_target"], want["camera"])

    def test_boss_state_paths_reach_the_release_state(self):
        for k, (typ, final) in {"THZ3": (0x50, 4), "SEZ3": (0x54, 4), "MGHZ3": (0x56, 4), "AQZ3": (0x59, 10)}.items():
            states = [s for _f, t, s in self.fights[k]["boss_state_path"] if t == typ]
            self.assertIn(final, states, k)
        self.assertIn(14, [s for _f, t, s in self.fights["GPZ3"]["boss_state_path"] if t == 0x51])

    def test_eez_has_no_results_no_fixed_bonus_no_0A_parameter_zero_and_direct_flag(self):
        for k in ("EEZ3_sonic_flags1F", "EEZ3_sonic_flags00", "EEZ3_sonic_flags3F"):
            r = self.fights[k]
            c = r["counts"]
            self.assertEqual((c["boss_bonus_loop"], c["results_card"], c["tally_loops"], c["bonus_objects_param0"], c["D2A6_sets"], c["flag_bit4_set"]), (0,) * 6, k)
            self.assertEqual(r["state20_requests"], [], k)
            self.assertEqual([w[2] for w in r["D293_writes"] if w[2] != 0x40][:1], [0x50])
            self.assertEqual(r["retained"]["score_before"], r["retained"]["score_after"])
            self.assertEqual(r["retained"]["zone_act_after"], [6, 0])
            self.assertIn("ending_selector", r["tail_frames"])
            self.assertIn("title_entry", r["tail_frames"])
            self.assertNotIn("results_card", r["tail_frames"])

    def test_eez_ending_branch_by_emerald_flags(self):
        f = self.fights
        self.assertIn("ending_full_sonic", f["EEZ3_sonic_flags1F"]["tail_frames"])       # Sonic with $1F waits for the sixth Emerald
        self.assertEqual(f["EEZ3_sonic_flags1F"]["retained"]["emeralds"], [0x1F, 0x3F])
        self.assertIn("ending_partial_sonic", f["EEZ3_sonic_flags00"]["tail_frames"])    # early clear in state 5, no sixth bit
        self.assertEqual(f["EEZ3_sonic_flags00"]["retained"]["emeralds"], [0, 0])
        self.assertIn("ending_full_sonic", f["EEZ3_sonic_flags3F"]["tail_frames"])       # D2CC != $1F -> early clear, bits already $3F
        self.assertEqual(f["EEZ3_sonic_flags3F"]["retained"]["emeralds"], [0x3F, 0x3F])
        # the early clear precedes the final contact only when the $1F rule does not hold
        self.assertLess(f["EEZ3_sonic_flags00"]["tail_frames"]["title_entry"][0] - f["EEZ3_sonic_flags00"]["D293_writes"][0][0],
                        f["EEZ3_sonic_flags1F"]["tail_frames"]["title_entry"][0] - f["EEZ3_sonic_flags1F"]["D293_writes"][0][0])

    def test_fixture_disclosure_present(self):
        for k, r in self.fights.items():
            self.assertTrue(r["fixtures"] and r["harness"] and "EMULATED" in r["evidence_class"], k)
            self.assertTrue(any("synthetic" in f for f in r["fixtures"]), k)

    def test_negative_corrupted_observation_is_detected(self):
        bad = copy.deepcopy(self.ob)
        bad["fights"]["SEZ3"]["score"]["fixed_bonus"] = 500
        self.assertTrue(U.validate_observed(bad, self.st))
        bad = copy.deepcopy(self.ob)
        bad["fights"]["THZ3"]["counts"]["boss_bonus_loop"] = 2
        self.assertTrue(U.validate_observed(bad, self.st))
        bad = copy.deepcopy(self.ob)
        bad["fights"]["EEZ3_sonic_flags00"]["counts"]["results_card"] = 1
        self.assertTrue(U.validate_observed(bad, self.st))
        bad = copy.deepcopy(self.ob)
        bad["fights"]["MGHZ3"]["D2A6_sets"][0]["word"] ^= 1
        self.assertTrue(U.validate_observed(bad, self.st))


class FixtureTier(Base):
    """FIXTURE: the G0-style injected D293 flag.  These clears are NOT boss defeats and carry no bonus word."""

    KEYS = ["THZ3_injected_flag", "GPZ3_injected_flag", "SEZ3_injected_flag", "MGHZ3_injected_flag", "AQZ3_injected_flag"]

    def test_injected_clear_has_fixed_bonus_and_rings_only(self):
        for i, k in enumerate(self.KEYS):
            r = self.inj[k]
            self.assertEqual((r["bonus_objects_created"], r["D2A6_sets"], r["state20_requests"]), ([], [], []), k)
            self.assertEqual((r["score"]["fixed_bonus"], r["score"]["tally_total"], r["score"]["word_units"]), ([500, 1000, 1500, 2000, 2500][i], 470, 0), k)
            self.assertEqual(r["retained"]["zone_act_after"], [i + 1, 0])
            self.assertIn("FIXTURE", r["evidence_class"])

    def test_injected_versus_natural_differ_by_exactly_the_word(self):
        for nat_key, inj_key in zip(("THZ3", "GPZ3", "SEZ3", "MGHZ3", "AQZ3"), self.KEYS):
            nat, inj = self.fights[nat_key], self.inj[inj_key]
            self.assertEqual(nat["retained"]["score_after"] - inj["retained"]["score_after"], nat["score"]["word_units"], nat_key)

    def test_premature_flag_means_no_boss_object_and_no_bonus(self):
        for r in self.inj.values():
            self.assertEqual(r["counts"]["bonus_objects_param0"], 0)
            self.assertEqual(r["counts"]["flag_bit4_set"], 0)         # the $83ED path (player state $20 handler) never ran

    def test_negative_an_injected_record_with_a_word_is_rejected(self):
        bad = copy.deepcopy(self.ob)
        bad["injected_clears"]["THZ3_injected_flag"]["D2A6_sets"] = [dict(frame=1, word=1, time=[0, 0], rings=0)]
        self.assertTrue(U.validate_observed(bad, self.st))


class DocumentTier(Base):
    def test_document_tables_are_current(self):
        text = U.DOC.read_text(encoding="utf-8")
        for name, body in U.doc_tables(self.st, self.ctl, self.ob).items():
            block = U._MARK % ("BEGIN", name) + "\n" + body + "\n" + U._MARK % ("END", name)
            self.assertIn(block, text, name)


class PocSourceRead(Base):
    """POC SOURCE-READ: formulas transcribed from G1-D d9275fe; never executed, never ROM proof."""

    def test_boss_bonus_formula_differs_from_the_rom_on_37_seconds(self):
        def rom_h(sec):
            mm, ss = divmod(sec, 60)
            return U3.bonus_word(self.tt, ((mm // 10) << 12) | ((mm % 10) << 8) | ((ss // 10) << 4) | (ss % 10), 0x47)[0]
        bad = [s for s in range(600) if rom_h(s) != poc_boss_bonus_h(s)]
        self.assertEqual(len(bad), 37)
        self.assertEqual(bad[:9], [29, 59, 89, 119, 149, 179, 209, 239, 270])
        self.assertEqual(bad[-1], 298)

    def test_constant_500_is_wrong_for_zones_1_to_4(self):
        self.assertEqual([x for x in self.st["fixed_boss_bonus"]["raw_units"][:5] if x != 500], [1000, 1500, 2000, 2500])

    def test_poc_entries_recorded(self):
        p = self.st["poc_source_read"]
        self.assertEqual(p["commit"], "d9275feeca1a799928b6eb1a866d32275c4024b5")
        self.assertEqual(len(p["entries"]), 4)


class RomRecomputation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        if cls.rom is None or sys.version_info < (3, 10):
            raise unittest.SkipTest("canonical ROM / Python >= 3.10 not available")
        cls.st = U.build_static(cls.rom)

    def test_static_census_is_byte_identical_and_deterministic(self):
        self.assertEqual(U.dumps(self.st), U.STATIC_JSON.read_text(encoding="utf-8"))
        self.assertEqual(U.dumps(U.build_static(self.rom)), U.dumps(self.st))

    def test_controlled_results_are_byte_identical(self):
        self.assertEqual(U.dumps(U.build_controlled(self.rom, self.st)), U.CONTROLLED_JSON.read_text(encoding="utf-8"))

    def test_two_representative_fights_reproduce_the_committed_records(self):
        committed = U.load_json(U.OBS_JSON)
        ob = U.build_observed(self.rom, self.st, progress=lambda s: None, only=["THZ3", "EEZ3_sonic_flags00"])
        for k in ("THZ3", "EEZ3_sonic_flags00"):
            self.assertEqual(U.dumps(ob["fights"][k]), U.dumps(committed["fights"][k]), k)

    def test_one_injected_clear_reproduces(self):
        committed = U.load_json(U.OBS_JSON)
        inj = U.build_injected(self.rom, progress=lambda s: None, only=["MGHZ3_injected_flag"])
        self.assertEqual(U.dumps(inj["MGHZ3_injected_flag"]), U.dumps(committed["injected_clears"]["MGHZ3_injected_flag"]))


if __name__ == "__main__":
    unittest.main()

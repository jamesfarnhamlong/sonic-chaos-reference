#!/usr/bin/env python3
"""G0-R tests: the ordinary-campaign ROM contract.

Part 1 needs no ROM: it checks the committed contract/oracle/ledger for internal consistency, re-evaluates every expectation on the committed
oracle, runs negative controls on the evaluator and checks that the narrative's generated tables equal a fresh render.
Part 2 needs the canonical ROM (SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms) and Python >= 3.10 with the `z80` package: it recomputes the static
census and replays four whole-game scenarios, comparing them with the committed oracle byte for byte.  The full regeneration check is
`python tools/g0_campaign.py ROM --check` (about two minutes).
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

import g0_campaign as G  # noqa: E402
import g0_contract as C  # noqa: E402
import g0_doc as D  # noqa: E402

DATA = ROOT / "data" / "g0"
ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")))
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == 524288 and hashlib.sha256(data).hexdigest() == ROM_SHA:
            return data
    return None


class CommittedData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = load("campaign-oracle.json")
        cls.contract = load("campaign-contract.json")
        cls.ledger = load("g1-g2-ledger.json")
        G.build_expectations()

    def test_identity(self):
        self.assertEqual(self.contract["rom_sha256"], ROM_SHA)
        self.assertEqual(self.contract["base_commit"], "0bb7390813a8fa4320ef35253a2c39598eee8e08")
        self.assertEqual(self.ledger["poc_ss5"], "a13c4c96fbc1cff44566efaf416b4c078fbae3cc")

    def test_oracle_registry_matches_committed_oracle(self):
        self.assertEqual(list(self.oracle), [sid for sid, _, _ in G.ORACLE])

    def test_every_expectation_holds_on_committed_oracle(self):
        fails = G.evaluate(self.oracle)
        self.assertEqual([(e["scenario"], e["path"], why) for e, why in fails], [])
        self.assertGreater(len(G.EXPECT), 300)

    def test_contract_records_the_same_expectations(self):
        self.assertEqual(len(self.contract["expectations"]), len(G.EXPECT))
        self.assertTrue(all(e["ok"] for e in self.contract["expectations"]))
        self.assertEqual(self.contract["expectation_failures"], [])

    def test_every_scenario_is_checked_by_some_expectation(self):
        checked = {e["scenario"] for e in G.EXPECT}
        self.assertEqual(sorted(set(self.oracle) - checked), [])

    def test_evaluator_negative_controls(self):
        base = self.oracle
        for sid, path, bad in (("death_pit_lives3", ("end", "lives_bcd"), "03"), ("clear_thz1_rings00", ("end_in_play", "act"), 0),
                               ("ring100_tails", ("stage_entered",), True), ("special_stage_success", ("exit_state", "emeralds"), "00")):
            o = copy.deepcopy(base)
            cur = o[sid]
            for k in path[:-1]:
                cur = cur[k]
            cur[path[-1]] = bad
            self.assertTrue(G.evaluate(o), (sid, path))
        o = copy.deepcopy(base)
        o["ending_tails"]["counts"]["ending_full_sonic"] = 1
        self.assertTrue(any(e["op"] == "absent" for e, _ in G.evaluate(o)))
        o = copy.deepcopy(base)
        del o["restart_matrix"]["acts"][7]["same"]
        self.assertTrue(G.evaluate(o))

    def test_transition_references(self):
        ids = [t["id"] for t in self.contract["transitions"]]
        self.assertEqual(len(ids), len(set(ids)))
        for t in self.contract["transitions"]:
            for o in t["oracle"]:
                self.assertIn(o, self.oracle, (t["id"], o))
            for f in self.contract["fields"]:
                self.assertIn(f, t["effects"], (t["id"], f))
        for o in self.contract["outcomes"]:
            for ref in o["transition"].split("/"):
                self.assertIn(ref, ids, o)

    def test_forced_only_alias_is_not_normalised(self):
        t16 = next(t for t in self.contract["transitions"] if t["id"] == "T16")
        self.assertTrue(t16.get("forced_only"))
        self.assertIn("FORCED-ONLY", t16["name"])
        others = [t for t in self.contract["transitions"] if t["id"] != "T16"]
        self.assertFalse(any(t.get("forced_only") for t in others))
        self.assertTrue(any("83" in e for e in t16["evidence"]))

    def test_ledger_consistency(self):
        pk = self.ledger["ordered_dependency_ledger"]
        ids = [p["id"] for p in pk]
        self.assertEqual(len(ids), len(set(ids)))
        orders = {p["id"]: p["order"] for p in pk}
        self.assertEqual(sorted(orders.values()), list(range(1, len(pk) + 1)))
        t_ids = {t["id"] for t in self.contract["transitions"]}
        u_ids = {u["id"] for u in self.contract["unresolved"]}
        for p in pk:
            for d in p["depends_on"]:
                self.assertLess(orders[d], p["order"], (p["id"], d))
            for a in p["acceptance"]:
                self.assertIn(a, self.oracle, (p["id"], a))
            for c in p["contract"]:
                if c.startswith("T"):
                    self.assertIn(c, t_ids)
            for g in p["gaps"]:
                self.assertTrue(any(u in g for u in u_ids), (p["id"], g))
        self.assertTrue(all(p["status"] for p in pk))

    def test_reconciliation_covers_the_campaign_features(self):
        have = {r["id"] for r in self.ledger["fullgame0_reconciliation"]}
        for i in range(1, 13):
            self.assertIn("CAMP-%02d" % i, have)
        for i in range(1, 11):
            self.assertIn("LIFE-%02d" % i, have)
        self.assertEqual({q["id"] for q in self.ledger["fullgame0_questions"]}, {"Q1", "Q2", "Q3", "Q4", "Q12"})
        camp8 = next(r for r in self.ledger["fullgame0_reconciliation"] if r["id"] == "CAMP-08")
        self.assertEqual(camp8["g0"], "SUPERSEDED")
        self.assertTrue(any(s["id"] == "SP7" and "foreground" in s["finding"] for s in self.ledger["static_poc_observations"]))

    def test_continue_counter_correction_is_recorded(self):
        ram = {r["name"]: r for r in self.contract["ram"]}
        self.assertIn("continues", ram["continues"]["role"].lower())
        self.assertIn("lives", ram["lives"]["role"].lower())
        self.assertIn("CONTINUE", self.contract["sign_prize_tables"]["correction"])

    def test_boss_bonus_table(self):
        t = self.contract["act3_boss_bonus_table"]
        self.assertEqual(t["raw_total"], [500, 1000, 1500, 2000, 2500, 6000])
        self.assertEqual(t["used_zones"], [0, 1, 2, 3, 4])

    def test_palette_fade_answer_is_supported_by_all_three_runs(self):
        a = self.contract["palette_fade_answer"]
        self.assertEqual(a["status"], "resolved")
        self.assertTrue(a["answer"].startswith("YES"))
        self.assertEqual(set(a["emulated"]), {"clear_thz1_rings00", "special_stage_success", "special_stage_timeout"})
        for sid, r in a["emulated"].items():
            self.assertGreater(r["to_black_frame"], r["to_white_frame"], sid)
            self.assertGreater(r["to_white_frame"], r["tally_returned"], sid)
            self.assertLess(r["to_black_frame"], r["act_incremented"], sid)
            self.assertEqual([b for _, b in r["palette_steps_after_tally"]][-3:], [192, 96, 0], sid)
            self.assertEqual(max(b for _, b in r["palette_steps_after_tally"]), 288, sid)

    def test_restart_positions_match_the_rom_table(self):
        sp = {(r["zone"], r["act"]): r for r in self.contract["start_positions"]}
        self.assertEqual(len(sp), 18)
        for r in self.oracle["restart_matrix"]["acts"]:
            s = sp[(r["zone"], r["act"])]
            self.assertEqual(r["fresh_start"][0], s["player_x"], r)
            self.assertLessEqual(abs(r["fresh_start"][1] - s["player_y"]), 16, r)
            self.assertEqual(r["after_death"], r["fresh_start"])

    def test_no_rom_bytes_in_committed_files(self):
        for name in ("campaign-oracle.json", "campaign-contract.json", "g1-g2-ledger.json"):
            text = (DATA / name).read_text(encoding="utf-8")
            self.assertLess(len(text), 1_500_000)
        for r in self.contract["routines"]:
            self.assertEqual(sorted(r), ["end", "length", "name", "sha256", "start"])
            self.assertLess(r["length"], 400)

    def test_narrative_tables_equal_fresh_render(self):
        text = D.DOC.read_text(encoding="utf-8")
        a, b = text.index(D.BEGIN) + len(D.BEGIN), text.index(D.END)
        self.assertEqual(text[a:b], "\n\n" + D.render_tables(self.contract, self.ledger) + "\n")
        for needle in ("FORCED-ONLY", "D2C3", "palette", "Special Stage", "EEZ"):
            self.assertIn(needle, text)

    def test_every_oracle_fixture_is_declared(self):
        for sid, o in self.oracle.items():
            self.assertTrue(o.get("fixtures"), sid)


@unittest.skipUnless(canonical_rom() is not None, "canonical ROM not available")
class RomBacked(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        cls.contract = load("campaign-contract.json")
        cls.oracle = load("campaign-oracle.json")
        sys.path.insert(0, str(ROOT / "tools"))

    def test_static_census_is_reproducible(self):
        self.assertEqual(G.routine_hashes(self.rom), self.contract["routines"])
        self.assertEqual(G.writer_census(self.rom), self.contract["writer_census"])
        self.assertEqual(G.start_positions(self.rom), self.contract["start_positions"])
        self.assertEqual(G.act3_bonus_table(self.rom), self.contract["act3_boss_bonus_table"])
        self.assertEqual(G.prize_tables(self.rom), self.contract["sign_prize_tables"])

    def test_classified_writers_exist(self):
        census = {r["name"]: {int(s["cpu"], 16): s for s in r["sites"]} for r in G.writer_census(self.rom)}
        for (name, cpu), role in G.CLASSIFIED.items():
            self.assertIn(cpu, census[name], (name, hex(cpu), role))

    def test_no_unlisted_life_writer_in_resident_code(self):
        sites = [s for r in G.writer_census(self.rom) if r["name"] == "lives" for s in r["sites"] if s["kind"].startswith("ST")]
        self.assertEqual(sorted(s["cpu"] for s in sites), ["13D4", "15FB", "3113", "355D"])

    def test_live_scenarios_equal_committed_oracle(self):
        try:
            import z80  # noqa: F401
        except ImportError:
            self.skipTest("z80 package not installed (needs Python >= 3.10)")
        import g0_scenarios as S
        for sid, fn, kw in G.ORACLE:
            if sid in ("new_game_sonic", "death_pit_lives3", "ring100_sonic", "ring100_tails", "score_continue_rule"):
                got = json.loads(json.dumps(getattr(S, fn)(self.rom, **kw)))
                self.assertEqual(got, self.oracle[sid], sid)


if __name__ == "__main__":
    unittest.main()

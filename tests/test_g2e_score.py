#!/usr/bin/env python3
"""G2-E tests: the score owner, the score display and every score award.

Part 1 needs no ROM: committed JSON consistency (the same validation `--validate` runs), an independent re-run of the BCD/threshold model against the committed
sweep, the event-to-award matrix against the evidence it cites, the proposed contract against the POC's stateless threshold formula, and negative controls.
Part 2 needs the canonical ROM (SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms) and the `z80` package: it regenerates the static layer, the
controlled adder/gate sweeps, one object fixture per defeat family and one results-card case from the unmodified ROM.  The complete regeneration check is
`python tools/g2e_score.py ROM --check` (about four minutes).
"""
import copy
import hashlib
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import g2e_score as G  # noqa: E402

ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")))


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == 524288 and hashlib.sha256(data).hexdigest() == G.ROM_SHA256:
            return data
    return None


STATIC = G.load_json(G.STATIC_JSON)
CONTROLLED = G.load_json(G.CONTROLLED_JSON)
OBSERVED = G.load_json(G.OBSERVED_JSON)
POC = G.load_json(G.POC_JSON)
MATRIX = G.load_json(G.MATRIX_JSON)
CONTRACT = G.load_json(G.CONTRACT_JSON)
rom_only = unittest.skipIf(canonical_rom() is None, "verified ROM not available")


def poc_threshold(before_raw, add_raw, period):
    """The POC's stateless G2-B formula (SCR_chaos_adapter.gml chaos_continue_score_add), in raw units."""
    return (before_raw + add_raw) // period - before_raw // period


class CommittedData(unittest.TestCase):
    def test_validate_function_passes(self):
        n = G.validate(STATIC, CONTROLLED, OBSERVED, POC, MATRIX["rows"], CONTRACT)
        self.assertGreaterEqual(n, 200)

    def test_sizes_and_hashes(self):
        for d in (STATIC, CONTROLLED, OBSERVED):
            self.assertEqual(d["rom_sha256"], G.ROM_SHA256)
        for p in (G.STATIC_JSON, G.CONTROLLED_JSON, G.OBSERVED_JSON, G.POC_JSON, G.MATRIX_JSON, G.CONTRACT_JSON):
            self.assertLess(p.stat().st_size, 200_000, p)

    def test_only_two_writers_of_the_score_bytes(self):
        self.assertEqual(STATIC["writer_census"]["callers"]["262F"], ["0x02F0C", "0x05F81"])
        self.assertEqual(STATIC["writer_census"]["callers"]["2F00_ring_step"], ["0x02D18"])
        self.assertEqual(STATIC["writer_census"]["callers"]["2EFB_word_step"], ["0x02D44"])
        self.assertEqual(STATIC["writer_census"]["callers"]["2F05_boss_step"], ["0x02D6A"])

    def test_award_table_values_and_the_dead_entry(self):
        raw = [e["raw_units"] for e in STATIC["award_table"]["entries"]]
        self.assertEqual(raw, [1, 10, 50, 10])
        self.assertEqual(STATIC["award_table"]["referenced_by_ld_hl_in_fixed_code"]["0x27E8"], [])
        self.assertEqual([e["displayed_points"] for e in STATIC["award_table"]["entries"]], [10, 100, 500, 100])

    def test_gate_and_flat_award(self):
        g = CONTROLLED["type_gate"]
        self.assertEqual((g["amount_raw"], g["amount_bcd_le"]), (10, "100000"))
        self.assertTrue(g["awarding_types"].startswith("0x00..0x4F"))
        self.assertEqual(g["non_awarding_types"], "0x50..0xFF")

    def test_every_object_family_that_scores_is_listed(self):
        self.assertEqual(STATIC["of_which_placed_or_script_spawned"], ["0x10", "0x20", "0x21", "0x23", "0x24", "0x25", "0x27", "0x2C", "0x38", "0x3D"])
        self.assertIn("0x29", STATIC["state_table_aliases_never_placed_or_script_spawned"])
        placed = STATIC["placements"]["counts"]
        for t in ("0x10", "0x20", "0x21", "0x23", "0x24", "0x25", "0x27", "0x2C", "0x38", "0x3D"):
            self.assertIn(t, placed)
        for t in ("0x29", "0x2A", "0x2B", "0x33"):
            self.assertNotIn(t, placed)

    def test_solid_contact_vector_is_not_a_score_path(self):
        kinds = [s["kind"] for s in STATIC["conversion_sites"]]
        self.assertEqual(kinds.count("5F3D_attack_gated"), 8)
        self.assertEqual(kinds.count("5F54_conversion"), 12)
        self.assertEqual(kinds.count("5FA0_solid_contact_not_score"), 9)

    def test_bosses_reach_the_gate_but_score_nothing(self):
        boss = next(a for a in OBSERVED["natural_census"]["acts"] if a["act"] == "4.2")
        self.assertGreaterEqual(len(boss["gate_events"]), 6)
        self.assertEqual(boss["award_events"], [])
        self.assertEqual(boss["final_score_bcd_le"], "000000")

    def test_natural_census_awards_are_always_the_flat_value(self):
        n = 0
        for a in OBSERVED["natural_census"]["acts"]:
            for e in a["award_events"]:
                self.assertEqual(e["table"], "0x27EB")
                n += 1
        self.assertEqual(n, 19)

    def test_awards_repeat_only_after_a_death_reload(self):
        for a in OBSERVED["natural_census"]["acts"]:
            seen = {}
            for g in a["gate_events"]:
                if int(g["type"], 16) >= 0x50:
                    continue
                key = (g["type"], g["token"])
                if key in seen:
                    self.assertLess(g["lives"], seen[key], a["act"])        # the act was reloaded by a death in between
                seen[key] = g["lives"]

    def test_no_second_award_for_a_defeated_placement(self):
        for r in OBSERVED["revisit"]["acts"]:
            self.assertEqual(sum(p["gate_events_for_same_token"] for p in r["revisit_passes"]), 0)

    # ---- the independent model ---------------------------------------------------------------------------------------------------------
    def test_model_reproduces_the_committed_sweep(self):
        sw = CONTROLLED["score_adder"]["cycle_sweep"]
        for ch, n, first in ((1, sw["sonic_awards"], sw["sonic_new_thousand_values"]), (2, sw["tails_awards"], sw["tails_new_thousand_values"])):
            awards = [(k + 1) % 1000 for k in range(1000) if G.model_add(k * 1000 + 990, 10, ch, 0)[1]]
            self.assertEqual(len(awards), n)
            self.assertEqual(awards[:len(first)], first)
        self.assertEqual((sw["sonic_awards"], sw["tails_awards"]), (200, 334))

    def test_wrap_rows(self):
        w = CONTROLLED["score_adder"]["wrap"]
        for who in ("sonic", "tails"):
            self.assertEqual((w[who]["before"], w[who]["after"], w[who]["continues_after"]), (999990, 0, 1))
            self.assertEqual((w[who]["dead_cap_d2a3"], w[who]["dead_flag_d2bb"]), ("909999", 2))

    def test_tails_wrap_award_breaks_the_3000_period(self):
        sw = CONTROLLED["score_adder"]["cycle_sweep"]
        self.assertTrue(sw["tails_wrap_award_is_1000_raw_after_the_999000_award"])
        self.assertEqual(sw["tails_last_three_new_thousand_values"], [996, 999, 0])
        # the POC's stateless formula pays Tails at 999,000 but not at the wrap; the ROM pays at both
        self.assertEqual(poc_threshold(998990, 10, 3000), 1)
        self.assertEqual(poc_threshold(999990, 10, 3000), 0)

    def test_tails_two_separate_award_events_near_the_wrap(self):
        # event 1: 998,990 -> 999,000 raw pays one continue; event 2: 999,990 -> 0 pays one more; neither event pays two
        after1, c1 = G.model_add(998990, 10, 2, 0)
        self.assertEqual((after1, c1), (999000, 1))
        after2, c2 = G.model_add(999990, 10, 2, c1)
        self.assertEqual((after2, c2), (0, 2))
        _, c_between = G.model_add(999000, 10, 2, c1)
        self.assertEqual(c_between, c1)                                    # nothing between the two events
        # the same two crossings on the original adder (committed controlled rows)
        corners = {(c["before"], c["character"]): c for c in CONTROLLED["score_adder"]["corners"]}
        self.assertEqual(corners[(998990, 2)]["after"], 999000)
        self.assertEqual(corners[(998990, 2)]["continues_after"], 1)
        self.assertEqual(corners[(999990, 2)]["after"], 0)
        self.assertEqual(corners[(999990, 2)]["continues_after"], 1)       # fixture starts each row at D2C3 = 0: exactly one per event
        # Sonic: unchanged, one award at the wrap and none at 999,000
        self.assertEqual(G.model_add(998990, 10, 1, 0)[1], 0)
        self.assertEqual(G.model_add(999990, 10, 1, 0)[1], 1)

    def test_contract_states_both_tails_events(self):
        rules = {r["id"]: r["rule"] for r in CONTRACT["rules"]}
        self.assertIn("TWO separate award events", rules["S8"])
        self.assertIn("999,000", rules["S8"])
        self.assertNotIn("needs no code before G6", rules["S8"])
        self.assertIn("BOTH characters", rules["S7"])
        self.assertTrue(any("two events" in c for c in CONTRACT["acceptance_checks"]))
        self.assertTrue(any("one continue for both characters" in c for c in CONTRACT["acceptance_checks"]))
        doc = (ROOT / "docs" / "g2e-score-owner-hud.md").read_text(encoding="utf-8")
        self.assertIn("in G2-E scope", doc)
        self.assertNotIn("needs no code before G6", doc)

    def test_poc_formula_matches_the_rom_for_sonic_across_the_cycle(self):
        for k in range(1000):
            raw = k * 1000 + 990
            self.assertEqual(poc_threshold(raw, 10, 5000), G.model_add(raw, 10, 1, 0)[1], raw)

    def test_poc_formula_matches_the_rom_for_tails_inside_the_cycle(self):
        for k in range(999):
            raw = k * 1000 + 990
            self.assertEqual(poc_threshold(raw, 10, 3000), G.model_add(raw, 10, 2, 0)[1], raw)

    # ---- display -----------------------------------------------------------------------------------------------------------------------
    def test_fixed_glyph_is_digit_zero(self):
        h = STATIC["hud"]
        self.assertTrue(h["fixed_block"]["equals_digit_0_glyph"])
        self.assertEqual(h["fixed_block"]["tile_ids"], h["digit_glyph_table"]["pairs_top_bottom_tile_ids"][0])
        self.assertEqual(h["digit_field"]["leading_zero_blank"], 5)
        self.assertIn("none", h["gameplay_hud"])

    def test_card_cases(self):
        cases = {c["case"]: c for c in OBSERVED["results_card"]["cases"]}
        self.assertEqual(cases["zero"]["card_start"]["field_text"], "      0")
        self.assertEqual(cases["ten_raw"]["card_start"]["field_text"], "    100")
        self.assertEqual(cases["raw_12340"]["card_start"]["field_text"], " 123400")
        self.assertEqual(cases["raw_999999"]["card_start"]["field_text"], "9999990")
        w = cases["wrap_to_zero_one_ring"]["tally_return"]
        self.assertEqual((w["score_ram"], w["continues"], w["field_text"]), ("000000", 1, "9999900"))

    # ---- matrix and contract -----------------------------------------------------------------------------------------------------------
    def test_matrix_statuses_against_the_poc_probes(self):
        by_id = {p["id"]: p for p in POC["probes"]}
        rows = {r["id"]: r for r in MATRIX["rows"]}
        for rid in ("E01", "E02", "E03", "E04", "E09"):
            self.assertEqual(rows[rid]["poc_status"], "MISSING")
        for rid in ("E05", "E06", "E07", "E08"):
            self.assertEqual(rows[rid]["poc_status"], "MIS-SCALED")
            self.assertEqual(rows[rid]["poc_units_should_add"], 100)
        for rid in ("E10", "E11", "E12", "E13", "E14", "E15"):
            self.assertEqual(rows[rid]["poc_status"], "CORRECT")
        for pid in ("enemy_20_23", "enemy_3d", "enemy_38", "enemy_24_post"):
            self.assertIn(pid, by_id)
        for pid in ("monitor_10", "enemy_21", "enemy_25", "enemy_27_2c"):
            self.assertIn("bytes", by_id[pid]["role"])
        self.assertEqual(rows["E11"]["rom_displayed_points"], 100)
        self.assertEqual(rows["E12"]["rom_displayed_points"], 10)

    def test_contract_and_acceptance(self):
        ids = [r["id"] for r in CONTRACT["rules"]]
        self.assertEqual(ids[:3], ["S1", "S2", "S3"])
        self.assertEqual(len(CONTRACT["smallest_poc_changes"]), 4)

    # ---- negative controls -------------------------------------------------------------------------------------------------------------
    def test_negative_control_wrong_wrap_modulus(self):
        w = CONTROLLED["score_adder"]["wrap"]["sonic"]
        self.assertNotEqual((w["before"] + 10) % 999999, w["after"])         # a 6-digit-minus-one modulus would give 1, the ROM gives 0
        self.assertEqual((w["before"] + 10) % 1000000, w["after"])

    def test_negative_control_validate_detects_a_changed_award(self):
        bad = copy.deepcopy(OBSERVED)
        bad["natural_census"]["acts"][0]["award_events"][0]["table"] = "0x27E5"
        with self.assertRaises(AssertionError):
            G.validate(STATIC, CONTROLLED, bad, POC, MATRIX["rows"], CONTRACT)

    def test_negative_control_validate_detects_a_wrong_status_set(self):
        bad = copy.deepcopy(MATRIX["rows"])
        for r in bad:
            if r["poc_status"] == "MIS-SCALED":
                r["poc_status"] = "CORRECT"
        with self.assertRaises(AssertionError):
            G.validate(STATIC, CONTROLLED, OBSERVED, POC, bad, CONTRACT)


@rom_only
class RomBacked(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = G.load_rom(ROM_PATH)

    def test_static_layer_regenerates(self):
        static, _ = G.build_static(self.rom)
        self.assertEqual(G.dumps(static), G.STATIC_JSON.read_text(encoding="utf-8"))

    def test_adder_and_gate_regenerate(self):
        self.assertEqual(G.controlled_add(self.rom), CONTROLLED["score_adder"])
        self.assertEqual(G.controlled_gate(self.rom), CONTROLLED["type_gate"])

    def test_one_fixture_per_family(self):
        _, keys = G.build_static(self.rom)
        rows = G.contact_matrix(self.rom, {k: v for k, v in keys.items() if k[0] in (0x27, 0x25)})
        committed = {(r["type"], r["parameter"]): r for r in CONTROLLED["contact_matrix"]}
        for r in rows:
            self.assertEqual(r, committed[(r["type"], r["parameter"])])
        auto = G.autonomous_types(self.rom, {k: v for k, v in keys.items() if k[0] == 0x24 and k[2] == "0x00" or k[0] == 0x38 and k[2] == "0x00"})
        self.assertTrue(all(t["first_award"]["score"] == "100000" for t in auto["trials"]))

    def test_results_card_case(self):
        static = STATIC
        cases = G.card_cases(self.rom, static["hud"]["digit_glyph_table"]["pairs_top_bottom_tile_ids"], only=("zero", "ten_raw"))
        committed = {c["case"]: c for c in OBSERVED["results_card"]["cases"]}
        self.assertEqual(len(cases), 2)
        for c in cases:
            self.assertEqual(c, committed[c["case"]])


if __name__ == "__main__":
    unittest.main()

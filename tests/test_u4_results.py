#!/usr/bin/env python3
"""U4-A tests: original ordinary act-clear results presentation.

Part 1 needs no ROM: committed JSON consistency, models re-run on the committed plan (card compose, fade engine, act title animator), negative controls,
timeline invariants of the committed observations and the generated tables of docs/u4-ordinary-results.md.
Part 2 needs the canonical ROM (SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms), Python >= 3.10 and the `z80` package: it recomputes the static census,
the export hashes and replays four original-ROM clears against the committed observations.  The complete regeneration check is
`python tools/u4_results.py ROM --check` (about three minutes).
"""
import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import u4_results as U  # noqa: E402

ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")))
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == 524288 and hashlib.sha256(data).hexdigest() == ROM_SHA:
            return data
    return None


class CommittedData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st = U.load_json(U.STATIC_JSON)
        cls.ob = U.load_json(U.OBS_JSON)
        cls.man = U.load_json(U.MANIFEST_JSON)
        cls.plan = cls.st["draw_plan"]
        cls.tp = cls.st["act_title_card"]

    # ---------------------------------------------------------------- identity / structure
    def test_identity(self):
        for d in (self.st, self.ob, self.man):
            self.assertEqual(d["rom_sha256"], ROM_SHA)
        self.assertEqual(self.st["base_commit"], "db23e5400db923025d2179aba5a01535c6f64b89")

    def test_static_validates(self):
        self.assertEqual(U.validate_static(self.st), [])

    def test_observed_validates(self):
        self.assertEqual(U.validate_observed(self.ob), [])

    def test_files_are_canonical_dumps(self):
        for path in (U.STATIC_JSON, U.OBS_JSON, U.MANIFEST_JSON):
            self.assertEqual(U.dumps(json.loads(path.read_text(encoding="utf-8"))), path.read_text(encoding="utf-8"))

    def test_routine_regions_cover_the_documented_entry_points(self):
        names = {r["name"] for r in self.st["routines"]}
        for n in ("act_clear_tail", "zone_clear_tail", "results_card", "tally_loops", "tally_boss_bonus", "fade_engine", "number_draw", "act_title_card", "name_table_animator"):
            self.assertIn(n, names)
        r = {x["name"]: x for x in self.st["routines"]}
        self.assertEqual((r["act_clear_tail"]["cpu_start"], r["results_card"]["cpu_start"], r["tally_loops"]["cpu_start"]), ("14AE", "32F9", "2D08"))
        self.assertEqual(r["fade_engine"]["bank"], 14)

    # ---------------------------------------------------------------- draw plan
    def test_draw_plan_geometry(self):
        b = {x["id"]: x for x in self.plan["blocks"]}
        self.assertEqual((b["banner_sonic"]["col"], b["banner_sonic"]["row"], b["banner_sonic"]["cols"], b["banner_sonic"]["rows"]), (0, 2, 32, 4))
        self.assertEqual((b["labels_ordinary"]["col"], b["labels_ordinary"]["row"], b["labels_ordinary"]["cols"], b["labels_ordinary"]["rows"]), (3, 8, 8, 11))
        self.assertEqual((b["panel_ordinary"]["col"], b["panel_ordinary"]["row"], b["panel_ordinary"]["cols"], b["panel_ordinary"]["rows"]), (21, 8, 5, 5))
        self.assertEqual(b["panel_ordinary"]["source_cpu"], b["panel_stage"]["source_cpu"])
        self.assertEqual((self.plan["continues"]["col0"], self.plan["continues"]["row0"], self.plan["continues"]["pitch_cells"]), (14, 17, 2))
        self.assertEqual([(s["col"], s["row"]) for s in self.plan["emeralds"]["slots"]], [(8 + 4 * i, 20) for i in range(5)])
        self.assertEqual(self.plan["emeralds"]["pitch_name_table_bytes"], 8)
        f = {x["id"]: (x["col"], x["row"], x["digits"], x["leading_zero_blank"]) for x in self.plan["number_fields"]}
        self.assertEqual(f, {"rings": (18, 8, 2, 1), "bonus": (16, 11, 4, 3), "score": (13, 14, 6, 5)})
        self.assertEqual((self.plan["score_trailing_zero"]["col"], self.plan["score_trailing_zero"]["row"]), (19, 14))

    def test_card_variants(self):
        v = self.st["card_variants"]
        self.assertTrue(v["panel_ordinary__vs__panel_stage"]["same_source"])
        self.assertEqual(v["panel_ordinary__vs__panel_stage"]["differing_cell_count"], 0)
        self.assertGreater(v["labels_ordinary__vs__labels_stage"]["differing_cell_count"], 0)
        self.assertTrue(v["banner_sonic__vs__banner_stage"]["same_geometry"])

    def test_boss_table_and_step_values(self):
        self.assertEqual(self.st["boss_bonus_steps"], [50, 100, 150, 200, 250, 600])
        self.assertEqual(self.st["step_values_bcd"]["ring"], "100000")
        self.assertEqual(self.st["step_values_bcd"]["bonus"], "010000")
        self.assertEqual(self.st["step_values_bcd"]["boss"], "100000")

    def test_wait_loops(self):
        w = self.st["wait_loops"]
        self.assertEqual([w[k]["frames"] for k in ("act_clear_wait_before_fade", "act_clear_fade_to_white_wait", "act_clear_after_sound_regs", "act_clear_blank_wait")], [60, 96, 30, 12])
        self.assertEqual([w[k]["frames"] for k in ("card_before_tally", "card_after_tally", "act_clear_after_card", "act_clear_white_hold", "act_clear_black_wait")], [60, 48, 48, 96, 48])
        for a, b in (("act_clear", "zone_clear"),):
            for k in ("wait_before_fade", "fade_to_white_wait", "after_sound_regs", "blank_wait", "after_card", "white_hold", "black_wait"):
                self.assertEqual(w["%s_%s" % (a, k)]["frames"], w["%s_%s" % (b, k)]["frames"], k)

    # ---------------------------------------------------------------- compose model (no ROM)
    def test_compose_reproduces_committed_card_hash(self):
        ob = self.ob["scenarios"]["sonic_thz1_baseline"]["checks"]
        nt = U.compose_name_table(self.plan, d2c8=1, d2cd=0, continues=0, emeralds=3, rings=0x25, bonus=0x0914, score=[0, 0, 0])
        self.assertEqual(U.nt_hash(nt), ob["name_table_sha256_at_tally_call"])

    def test_zero_suppression_rules(self):
        fields = {f["id"]: f for f in self.plan["number_fields"]}
        glyph = {g["digit"]: (g["top"], g["bottom"]) for g in self.plan["digit_glyph_table"]["entries"]}
        cells = U.field_cells(self.plan, fields["rings"], [0x05])
        self.assertEqual([(c[2], c[3]) for c in cells], [glyph["blank"], glyph[5]])
        cells = U.field_cells(self.plan, fields["rings"], [0x00])
        self.assertEqual([(c[2], c[3]) for c in cells], [glyph["blank"], glyph[0]])
        cells = U.field_cells(self.plan, fields["bonus"], [0x07, 0x00])
        self.assertEqual([(c[2], c[3]) for c in cells], [glyph["blank"]] * 3 + [glyph[7]])
        cells = U.field_cells(self.plan, fields["score"], [0x50, 0x34, 0x12])         # 123450: six digits, nothing blanked
        self.assertEqual([(c[2], c[3]) for c in cells], [glyph[d] for d in (1, 2, 3, 4, 5, 0)])
        self.assertEqual([c[0] for c in cells], list(range(13, 19)))
        cells = U.field_cells(self.plan, fields["score"], [0x50, 0x34, 0x00])         # 003450: two leading zeros blanked, the inner zero is kept
        self.assertEqual([(c[2], c[3]) for c in cells], [glyph["blank"]] * 2 + [glyph[d] for d in (3, 4, 5, 0)])
        self.assertEqual(U.field_cells(self.plan, fields["rings"], [0x1A]), [])      # invalid BCD: the ROM draws nothing

    def test_score_zero_skips_digits_but_draws_trailing_zero(self):
        nt = U.compose_name_table(self.plan, d2c8=1, d2cd=0, continues=0, emeralds=0, rings=0, bonus=0, score=[0, 0, 0])
        blank = U.compose_name_table(self.plan, d2c8=1, d2cd=0, continues=0, emeralds=0, rings=0, bonus=0, score=[0, 0, 0])
        self.assertEqual(nt, blank)
        z = self.plan["score_trailing_zero"]
        self.assertEqual(nt[z["row"]][z["col"]] & 0xFF, next(g["top"] for g in self.plan["digit_glyph_table"]["entries"] if g["digit"] == 0))
        self.assertEqual(nt[13][14], U.FILL_WORD)                                  # digit cells stay on the fill word

    def test_continue_icons_cap_and_award_slot(self):
        c = self.plan["continues"]
        nt = U.compose_name_table(self.plan, d2c8=1, d2cd=0, continues=0x8F, emeralds=0, rings=0, bonus=0, score=[0, 0, 0])
        drawn = [i for i in range(10) if c["col0"] + 2 * i < 32 and nt[c["row0"]][c["col0"] + 2 * i] != U.FILL_WORD]
        self.assertEqual(drawn, list(range(8)))                                    # bit 7 ignored, capped at 8
        nt2 = U.compose_name_table(self.plan, d2c8=1, d2cd=0, continues=8, emeralds=0, rings=0, bonus=0, score=[0, 0, 0], continue_awards=[8])
        self.assertNotEqual(nt2[c["row0"]][c["col0"] + 16], U.FILL_WORD)           # ROM quirk: the ninth icon lands in slot 8 (cols 30-31)
        other = U.compose_name_table(self.plan, d2c8=2, d2cd=0, continues=1, emeralds=0, rings=0, bonus=0, score=[0, 0, 0])
        self.assertNotEqual(nt[c["row0"]][c["col0"]], other[c["row0"]][c["col0"]])  # the other character has its own icon

    def test_emerald_slots_follow_d2cc_bits(self):
        for mask in (0x00, 0x01, 0x1F, 0x20, 0x3F):
            nt = U.compose_name_table(self.plan, d2c8=1, d2cd=0, continues=0, emeralds=mask, rings=0, bonus=0, score=[0, 0, 0])
            shown = [s["slot"] for s in self.plan["emeralds"]["slots"] if nt[s["row"]][s["col"]] != U.FILL_WORD]
            self.assertEqual(shown, [i for i in range(5) if mask >> i & 1])

    def test_stage_card_differs_from_ordinary(self):
        a = U.compose_name_table(self.plan, d2c8=1, d2cd=0, continues=0, emeralds=0, rings=0, bonus=0, score=[0, 0, 0])
        b = U.compose_name_table(self.plan, d2c8=1, d2cd=1, continues=0, emeralds=0, rings=0, bonus=0, score=[0, 0, 0])
        self.assertNotEqual(a, b)
        self.assertEqual(a[8][21:26], b[8][21:26])                                  # shared multiplier panel

    # ---------------------------------------------------------------- fade engine model
    def test_fade_engine_endpoints_and_pass_counts(self):
        start = [0x00, 0x15, 0x2A, 0x3F, 0x31, 0x0C, 0x23, 0x38] * 2
        target = [0x30, 0x0F, 0x28, 0x1B, 0x06, 0x3A, 0x00, 0x33] * 2
        w = U.fade_series("to_white", start)
        self.assertEqual(len(w), 3)
        self.assertEqual(w[-1], [0x3F] * 16)
        b = U.fade_series("to_black", [0x3F] * 16)
        self.assertEqual([x[0] for x in b], [0x2A, 0x15, 0x00])
        i = U.fade_series("in_black", [0] * 16, target)
        self.assertEqual(len(i), 4)
        self.assertEqual(i[0], [0] * 16)                                            # first pass shows black
        self.assertEqual(i[-1], target)
        h = U.fade_series("in_white", [0x3F] * 16, target)
        self.assertEqual(h[-1], target)
        self.assertEqual(len(h), 4)

    def test_fade_negative_controls(self):
        target = [0x30, 0x0F, 0x28, 0x1B] * 4
        wrong = list(target)
        wrong[0] ^= 1
        self.assertNotEqual(U.fade_series("in_black", [0] * 16, target)[-1], wrong)
        self.assertNotEqual(U.fade_series("to_white", [0] * 16)[0], [0x3F] * 16)    # one level per pass, not a jump

    def test_committed_fade_changes_follow_the_five_frame_grid(self):
        sc = self.ob["scenarios"]["sonic_thz1_baseline"]
        frames = [f for f, _ in sc["cram_changes"]]
        runs = [[frames[0]]]
        for f in frames[1:]:
            (runs[-1].append(f) if f - runs[-1][-1] == 5 else runs.append([f]))
        self.assertTrue(all(len(r) <= 3 for r in runs))
        self.assertEqual([len(r) for r in runs][:5], [3, 3, 3, 3, 3])
        for r in runs:                                   # passes inside one fade are exactly 5 frames apart
            self.assertTrue(all(b - a == 5 for a, b in zip(r, r[1:])))

    # ---------------------------------------------------------------- act title card (no ROM)
    def test_title_states_final_hash_matches_committed_observation(self):
        sc = self.ob["scenarios"]["sonic_thz1_baseline"]
        for key, t in sc["title_cards"].items():
            z, a = (int(x) for x in key.split("_"))
            states = U.title_states(self.tp, z, a)
            self.assertEqual(len(states), 1 + 29 + 32 + 21)
            self.assertEqual(U.nt_hash(states[-1][1]), t["final_name_table_sha256"])

    def test_title_zone_animator_reveals_columns_progressively(self):
        states = U.title_states(self.tp, 0, 0)
        fills = states[0][1]
        zone = [s for lab, s in states if isinstance(lab, tuple) and lab[0] == "zone"]
        self.assertEqual(len(zone), 32)
        for n in (1, 8, 16, 31):                         # update n only touches columns 0..n-1 of rows 7..10
            for r in range(7, 11):
                self.assertEqual(zone[n - 1][r][n:], fills[r][n:], (n, r))
        self.assertEqual(zone[-1][7][:32], [0x100 | t for t in self.tp["zone_object"]["maps"][0]["tiles"][:32]])
        self.assertNotEqual(zone[7][7][:8], zone[-1][7][:8])    # the first columns still change after update 8

    def test_title_maps_differ_per_zone_and_act(self):
        self.assertEqual(len({m["source_sha256"] for m in self.tp["zone_object"]["maps"]}), 6)
        self.assertEqual(len({m["source_sha256"] for m in self.tp["act_object"]["maps"]}), 3)

    # ---------------------------------------------------------------- committed observations
    def test_baseline_timeline(self):
        sc = self.ob["scenarios"]["sonic_thz1_baseline"]
        ev = {n: f for f, n in sc["events"]}
        self.assertEqual((ev["clear_entry"], ev["anim_freeze"], ev["sound_regs"], ev["sound_stop"], ev["card_start"]), (0, 60, 156, 186, 198))
        self.assertEqual(ev["tally_call"] - ev["card_start"], 76)
        self.assertEqual(ev["tail_white_request"] - ev["tally_return"], 95)
        self.assertEqual(ev["progress"] - ev["white_fill"], 48)
        self.assertEqual(ev["white_fill"] - ev["tail_white_request"], 96)
        self.assertEqual(ev["title_start"] - ev["progress"], 1)

    def test_every_act_clear_has_the_same_shape(self):
        rows = [r for r in self.ob["zone_matrix"] if r["results_card"]]
        self.assertEqual(len(rows), 17)
        for r in rows:
            rf = r["relative_frames"]
            self.assertIn(rf["card_start"], (198, 199))
            self.assertEqual(rf["tally_call"] - rf["card_start"], 76)
            self.assertEqual(r["d2d3"], 1)
            self.assertEqual(r["tail"], "zone" if r["act"] == 2 else "act")
        # the card is zone/act independent: identical name table for the same preset in all injected clears (THZ1 uses the real sign chain: its bonus word differs)
        self.assertEqual(len({r["name_table_sha256"] for r in rows if (r["zone"], r["act"]) != (0, 0)}), 1)
        self.assertNotEqual(rows[0]["name_table_sha256"], rows[1]["name_table_sha256"])
        self.assertFalse([r for r in self.ob["zone_matrix"] if r["zone"] == 5 and r["act"] == 2 and r["results_card"]])

    def test_boss_tail_differences(self):
        b = self.ob["scenarios"]["boss_zone0_act2"]
        ev = {n: f for f, n in b["events"]}
        self.assertIn("clear_entry_zone", ev)
        self.assertEqual(b["steps"]["boss_step"]["count"], 50)
        self.assertEqual(self.ob["scenarios"]["boss_zone3_act2"]["steps"]["boss_step"]["count"], 200)
        self.assertEqual(self.ob["scenarios"]["boss_zone3_act2"]["steps"]["ring_step"]["count"], 25)
        self.assertGreater(ev["ring_loop_enter"] - ev["tally_call"], 12)             # boss loop plus its 12-frame wait precede the ring loop

    def test_tally_cadence_and_button_skip(self):
        base = self.ob["scenarios"]["sonic_thz1_baseline"]["steps"]
        held = self.ob["scenarios"]["held_button_tally"]["steps"]
        self.assertEqual((base["ring_step"]["count"], base["bonus_step"]["count"]), (25, 914))
        self.assertGreater(held["bonus_step"]["mean"], 1.8 * base["bonus_step"]["mean"])
        ev = {n: f for f, n in self.ob["scenarios"]["held_button_tally"]["events"]}
        self.assertEqual(ev["title_hold_end"], ev["title_hold_start"])               # a held button skips the 180-frame hold at once

    def test_award_and_overflow_scenarios(self):
        self.assertEqual(self.ob["scenarios"]["sonic_award_crossing"]["checks"]["continue_award_old_counts"], [0x83])
        self.assertEqual(self.ob["scenarios"]["sonic_continue_overflow"]["checks"]["continue_award_old_counts"], [8])

    def test_stage_card_variants(self):
        base = {n: f for f, n in self.ob["scenarios"]["sonic_thz1_baseline"]["events"]}
        ok = self.ob["scenarios"]["stage_card_success"]
        ev = {n: f for f, n in ok["events"]}
        self.assertEqual(ev["tally_call"] - base["tally_call"], 240)                  # the $FF card holds 240 frames before its 60-frame wait
        self.assertEqual(ev["stage_sound"], ev["card_fade_in_request"])
        snd = [w for w in ok["sound_and_continue_writes"] if w[1] == "0xde04"]
        self.assertEqual(snd[0][2], 0x86)
        fail = {n: f for f, n in self.ob["scenarios"]["stage_card_failure"]["events"]}
        self.assertEqual(fail["tally_call"], base["tally_call"])
        self.assertNotIn("stage_sound", fail)

    def test_frozen_frame_and_sprite_free_card(self):
        fz = self.ob["scenarios"]["sonic_thz1_baseline"]["frozen_frame"]
        self.assertTrue(fz["entry_to_60"]["name_table_equal"] and fz["entry_to_60"]["player_equal"] and fz["entry_to_60"]["camera_equal"])
        self.assertTrue(fz["at_60_to_186"]["sat_equal"] and fz["at_60_to_186"]["name_table_equal"])
        for sc in self.ob["scenarios"].values():
            self.assertEqual(sc["checks"]["tally_call_sprite_pixels"], 0)

    def test_registers_at_card(self):
        regs = self.ob["scenarios"]["sonic_thz1_baseline"]["checks"]["registers_at_card"]
        self.assertEqual(regs, {"R0": 38, "R1": 226, "R2": 255, "R5": 255, "R7": 0, "R8": 0, "R9": 0, "R10": 255})

    # ---------------------------------------------------------------- manifest, adapter, doc
    def test_manifest_assets(self):
        a = self.man["assets"]
        self.assertEqual(len([k for k in a if k.startswith("title/frame_")]), 18)
        self.assertEqual(len([k for k in a if k.startswith("blocks/")]), 7 + 2 + 5 + 2)
        for k, v in a.items():
            self.assertEqual(len(v.get("index_sha256") or v["sha256"]), 64, k)

    def test_adapter_is_marked_as_adapter(self):
        ad = self.st["adapter"]
        self.assertIn("ADAPTER", ad["status"])
        self.assertEqual(ad["widescreen_348x196"]["centre_offset_px"], [46, 2])
        self.assertEqual(ad["rom_native"]["screen_px"], [256, 192])

    def test_unresolved_items_are_listed(self):
        self.assertGreaterEqual(len(self.st["unresolved"]), 10)
        self.assertEqual(len({u["id"] for u in self.st["unresolved"]}), len(self.st["unresolved"]))

    def test_doc_generated_tables_are_current(self):
        text = U.DOC.read_text(encoding="utf-8")
        for name, body in U.doc_tables(self.st, self.ob).items():
            a, b = U._MARK % ("BEGIN", name), U._MARK % ("END", name)
            if a in text:
                self.assertEqual(text[text.index(a) + len(a):text.index(b)].strip("\n"), body, name)
        self.assertIn(U._MARK % ("BEGIN", "timeline"), text)

    def test_validators_catch_corruption(self):
        bad = copy.deepcopy(self.ob)
        bad["scenarios"]["sonic_thz1_baseline"]["checks"]["tiles_equal_decoded_stream"] = False
        self.assertTrue(U.validate_observed(bad))
        bad = copy.deepcopy(self.st)
        bad["draw_plan"]["blocks"][0]["cols"] = 40
        self.assertTrue(U.validate_static(bad))


@unittest.skipUnless(canonical_rom() is not None, "canonical ROM not available (set SONIC_CHAOS_ROM)")
class AgainstRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        cls.st = U.load_json(U.STATIC_JSON)
        cls.ob = U.load_json(U.OBS_JSON)
        cls.fresh = U.build_static(cls.rom)

    def test_static_census_equals_committed(self):
        self.assertEqual(U.dumps(self.fresh), U.STATIC_JSON.read_text(encoding="utf-8"))

    def test_export_hashes_equal_committed(self):
        with tempfile.TemporaryDirectory() as td:
            man = U.export_assets(self.rom, self.fresh, out=Path(td))
            self.assertEqual(U.dumps(man), U.MANIFEST_JSON.read_text(encoding="utf-8"))
            self.assertTrue((Path(td) / "frames" / "sonic_example.png").is_file())

    def test_exported_png_is_indexed_and_matches_hash(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            man = U.export_assets(self.rom, self.fresh, out=Path(td))
            im = Image.open(Path(td) / "frames" / "sonic_example.png")
            self.assertEqual((im.mode, im.size), ("P", (256, 192)))
            idx = bytes(im.getdata())
            self.assertEqual(hashlib.sha256(idx).hexdigest(), man["assets"]["frames/sonic_example.png"]["index_sha256"])
            self.assertLess(max(idx), 32)

    def test_tile_stream_decodes_to_the_vram_image(self):
        info, decoded = U.tile_stream_info(self.rom)
        self.assertEqual(info["tile_count"], 160)
        self.assertEqual(len(decoded), 160 * 32)
        self.assertEqual(U.sha(decoded), self.st["tile_stream"]["decoded_sha256"])

    def test_tile_stream_matches_tile_hashes_of_the_planar_decode(self):
        _, decoded = U.tile_stream_info(self.rom)
        tiles = U.tiles_from_decoded(decoded)
        self.assertEqual(len(tiles), 160)
        # tile 289 (fill) is a solid colour: every pixel index equal to 13
        fill = tiles[U.FILL_WORD - U.TILE_BASE]
        self.assertEqual({p for row in fill for p in row}, {13})

    def test_baseline_replay_matches_committed(self):
        plan = self.fresh["draw_plan"]
        _, decoded = U.tile_stream_info(self.rom)
        tiles = U.tiles_from_decoded(decoded)
        o, _, raw = U.observe_scenario(self.rom, plan, self.fresh["act_title_card"], tiles, decoded, "sonic_thz1_baseline", dict(character=0, rings=0x25, step_hooks=True), (0, 1), 0)
        o["note"] = self.ob["scenarios"]["sonic_thz1_baseline"]["note"]
        self.assertEqual(U.dumps(o), U.dumps(self.ob["scenarios"]["sonic_thz1_baseline"]))

    def test_tails_and_award_replays_match_committed(self):
        plan = self.fresh["draw_plan"]
        _, decoded = U.tile_stream_info(self.rom)
        tiles = U.tiles_from_decoded(decoded)
        for sid, kw, nxt, card, note in U.SCENARIOS:
            if sid not in ("tails_thz1", "sonic_continue_overflow"):
                continue
            o, _, _ = U.observe_scenario(self.rom, plan, self.fresh["act_title_card"], tiles, decoded, sid, kw, nxt, card)
            o["note"] = note
            self.assertEqual(U.dumps(o), U.dumps(self.ob["scenarios"][sid]), sid)

    def test_boss_replay_matches_committed(self):
        plan = self.fresh["draw_plan"]
        _, decoded = U.tile_stream_info(self.rom)
        tiles = U.tiles_from_decoded(decoded)
        for sid, kw, nxt, card, note in U.SCENARIOS:
            if sid != "boss_zone0_act2":
                continue
            o, _, _ = U.observe_scenario(self.rom, plan, self.fresh["act_title_card"], tiles, decoded, sid, kw, nxt, card)
            o["note"] = note
            self.assertEqual(U.dumps(o), U.dumps(self.ob["scenarios"][sid]))

    def test_invalid_rom_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.sms"
            p.write_bytes(b"\0" * 524288)
            with self.assertRaises(ValueError):
                U.load_rom(p)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""U4-B tests: original TIME OVER, Continue and Game Over presentation.

Part 1 needs no ROM: committed JSON consistency, the fade model re-run on the committed palettes and CRAM series, timeline and input-edge invariants of the
committed observations, audio-request ledger, audit inventory, export manifest, negative controls and the generated tables of the documentation.
Part 2 needs the canonical ROM (SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms), Python >= 3.10 and the `z80` package: it recomputes the static census, the
export hashes and the audio ledger, and replays three original-ROM scenarios against the committed observations.  The complete regeneration check is
`python tools/u4b_screens.py ROM --check` (about five minutes).
"""
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import u4b_screens as B  # noqa: E402

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
        cls.st = B.load_json(B.STATIC_JSON)
        cls.ob = B.load_json(B.OBS_JSON)
        cls.man = B.load_json(B.MANIFEST_JSON)
        cls.audio = B.load_json(B.AUDIO_JSON)
        cls.audit = B.load_json(B.AUDIT_JSON)
        cls.by = {s["id"]: s for s in cls.ob["scenarios"]}

    # ---------------------------------------------------------------- identity / structure
    def test_identity(self):
        for d in (self.st, self.ob, self.man, self.audio):
            self.assertEqual(d["rom_sha256"], ROM_SHA)
        self.assertEqual(self.st["base_commit"], "fdfe8effcf1c03d5ffd621d47c81f56038c5aeb7")
        self.assertEqual(self.audit["research_main"], "fdfe8effcf1c03d5ffd621d47c81f56038c5aeb7")

    def test_static_validates(self):
        self.assertEqual(B.validate_static(self.st), [])

    def test_observed_validates(self):
        self.assertEqual(B.validate_observed(self.ob), [])

    def test_files_are_canonical_dumps(self):
        for path in (B.STATIC_JSON, B.OBS_JSON, B.MANIFEST_JSON, B.AUDIO_JSON, B.AUDIT_JSON):
            self.assertEqual(B.dumps(json.loads(path.read_text(encoding="utf-8"))), path.read_text(encoding="utf-8"))

    def test_no_pixels_or_rom_bytes_committed(self):
        # tile pixels never appear: only hashes; the committed static document stays small
        self.assertLess(B.STATIC_JSON.stat().st_size, 400_000)
        for s in self.st["tile_streams"].values():
            self.assertNotIn("decoded", s)
            self.assertEqual(len(s["decoded_sha256"]), 64)

    # ---------------------------------------------------------------- decoded layout
    def test_tile_indices_stay_inside_the_loaded_streams(self):
        for key, sid in (("game_over", "gameover_continue"), ("continue", "gameover_continue"), ("time_over", "time_over")):
            n = self.st["tile_streams"][sid]["tile_count"]
            cells = [c for b in self.st["screens"][key]["blocks"] for c in b["cells"]]
            if key == "continue":
                cells += [x for g in self.st["screens"]["continue"]["digit_draw"]["glyphs"] for x in (g["top"], g["bottom"])]
            for c in cells:
                self.assertTrue(192 <= (c & 0x1FF) < 192 + n, (key, hex(c)))
            self.assertTrue(192 <= self.st["name_table_fill"]["word"] < 192 + n)

    def test_blocks_do_not_overlap(self):
        for key, v in self.st["screens"].items():
            seen = set()
            for b in v["blocks"]:
                for r in range(b["rows"]):
                    for c in range(b["cols"]):
                        cell = (b["row"] + r, b["col"] + c)
                        self.assertNotIn(cell, seen)
                        seen.add(cell)
            self.assertTrue(all(0 <= r < 24 and 0 <= c < 32 for r, c in seen))

    def test_continue_digit_field(self):
        dd = self.st["screens"]["continue"]["digit_draw"]
        co = self.st["screens"]["continue"]["blocks"][1]
        # the 2x6 block holds star, blank, tens digit 0, ones digit 9, blank, star; $3478 rewrites only the ones column (col 16)
        self.assertEqual((co["row"], co["col"], co["cols"], co["rows"]), (11, 13, 6, 2))
        self.assertEqual((dd["row"], dd["col"]), (11, co["col"] + 3))
        nt = B.compose_name_table(self.st, "continue", 4)
        self.assertEqual((nt[11][16], nt[12][16]), (dd["glyphs"][4]["top"], dd["glyphs"][4]["bottom"]))
        self.assertEqual((nt[11][15], nt[12][15]), (dd["glyphs"][0]["top"], dd["glyphs"][0]["bottom"]))
        self.assertEqual(len({(g["top"], g["bottom"]) for g in dd["glyphs"]}), 10, "ten distinct glyph pairs")

    def test_palette_records_and_requests(self):
        req = self.st["fade_requests"]
        self.assertEqual([(f["slot"][:4], f["record"]) for f in req["game_over"]], [("D492", 0x22), ("D494", 7)])
        self.assertEqual([(f["slot"][:4], f["record"]) for f in req["continue"]], [("D492", 0x24), ("D494", 7)])
        self.assertEqual([(f["slot"][:4], f["record"]) for f in req["time_over"]], [("D492", 0x23)])
        self.assertEqual(sorted(self.st["palette_records"]), ["34", "35", "36", "7"])
        self.assertEqual(self.st["palette_records"]["34"]["sms_colours"], self.st["palette_records"]["36"]["sms_colours"])

    def test_shared_graphics_inventory(self):
        ov = self.st["streams_overlap"]
        self.assertEqual(ov["gameover_continue__u4_results_160"]["shared_non_blank_tiles"], 0)
        self.assertEqual(ov["gameover_continue__time_over"]["shared_non_blank_tiles"], 0)
        self.assertGreater(ov["time_over__u4_results_160"]["shared_non_blank_tiles"], 0)
        shared = self.st["shared_tiles_with_results_stream"]["time_over"]
        self.assertEqual(shared["count"], len(shared["shared_with_u4_results_stream"]))
        self.assertEqual(self.st["shared_tiles_with_results_stream"]["gameover_continue"]["count"], 0)

    def test_player_scripts_and_art(self):
        a = self.st["player_art"]
        self.assertEqual([r["updates"] for r in a["1"]["idle"]] + [r["updates"] for r in a["2"]["idle"]], [8, 8, 8, 8])
        self.assertEqual(a["1"]["tile_table_cpu"], "104B")
        self.assertEqual(a["2"]["tile_table_cpu"], "11CF")
        for t in ("1", "2"):
            for f in a[t]["frames"].values():
                self.assertEqual(f["tile_count"], 2 * f["piece_count"] if f["piece_count"] == 6 else f["tile_count"])
                self.assertEqual(f["vram_destination"], "0000")
        p = self.st["sprite_placement"]
        self.assertEqual((p["object_screen_x"], p["object_screen_y"], p["pattern_base"]), (128, 160, 0))

    # ---------------------------------------------------------------- composition verdicts (emulated frames equal the composition)
    def test_every_capture_matches_the_composition(self):
        n = 0
        for s in self.ob["scenarios"] + self.ob["zone_matrix"] + [self.ob["baseline_pit_expire"]]:
            for name, c in (s.get("captures") or {}).items():
                n += 1
                self.assertTrue(c["name_table_equal"] and c["bg_pixels_equal"] and c["cram_equal"] and c["bg_tiles_equal_decoded_stream"], (s["id"], name))
                if c["screen"] == "continue":
                    self.assertIn(c["sprite_frame_matched"], (17, 18) if s["character"] == 0 else (15, 16), (s["id"], name))
                    self.assertEqual(c["player_object"], [1 if s["character"] == 0 else 2, 0x35, 128, 160], (s["id"], name))
                else:
                    self.assertEqual(c["visible_sprites"], 0)
        self.assertGreater(n, 100)

    def test_all_six_zones_give_identical_screens(self):
        zs = self.ob["zone_matrix"]
        self.assertEqual([z["zone"] for z in zs], list(range(6)))
        for z in zs[1:]:
            self.assertEqual(sorted(z["captures"]), sorted(zs[0]["captures"]))
            for name, c in z["captures"].items():
                self.assertEqual(c["name_table_sha256"], zs[0]["captures"][name]["name_table_sha256"], (z["id"], name))
            # the three screens' steady palettes are identical in every zone
            for sc in ("time_over", "continue", "game_over"):
                self.assertEqual(z["fade_checks"][sc]["steady_cram"], zs[0]["fade_checks"][sc]["steady_cram"])
        ev0 = zs[0]["events"]
        for z in zs[1:]:
            for k in ("time_over_screen", "time_over_exit", "continue_screen", "game_over_sound", "title"):
                self.assertLessEqual(abs(z["events"][k][0] - ev0[k][0]), 1, (z["id"], k))

    def test_line0_parking_sprite_is_recorded(self):
        c = self.by["time_over_continue_expire_sonic"]["captures"]
        self.assertEqual(c["time_over_steady"]["line0_parking_sprite_pixels"], 0)
        self.assertGreater(c["game_over_steady"]["line0_parking_sprite_pixels"], 0)
        self.assertTrue(any(u["id"] == "U4B-3" for u in self.st["unresolved"]))

    # ---------------------------------------------------------------- fades
    def test_fade_model_on_committed_palettes(self):
        for sc, key in (("game_over", "game_over"), ("continue", "continue"), ("time_over", "time_over")):
            bg, sp = B.screen_palette(self.st, key)
            black = [0] * 16
            states = B.U.fade_series("in_black", black, bg)
            self.assertEqual(states[0], black, "first pass is still black")
            self.assertEqual(states[-1], bg)
            self.assertEqual(len(B.dedupe([bytes(x).hex() for x in states])), 4)
        for s in self.ob["scenarios"] + self.ob["zone_matrix"]:
            for sc, fc in s["fade_checks"].items():
                self.assertTrue(fc["occurrences"], (s["id"], sc))
                for o in fc["occurrences"]:
                    self.assertTrue(o["fade_in_matches_model"] and o["fade_out_matches_model"], (s["id"], sc))
                    # one state every 5 frames
                    for fr in (o["fade_in_state_frames"][1:], o["fade_out_state_frames"]):     # the first fade-in state is the preceding black one
                        self.assertTrue(all(b - a == 5 for a, b in zip(fr, fr[1:])), (s["id"], sc, fr))

    def test_fade_shapes_by_screen(self):
        ref = self.by["time_over_continue_expire_sonic"]["fade_checks"]
        self.assertEqual(ref["time_over"]["model_fade_in_visible_states"], 4)       # 3 passes change colours + the final steady state
        self.assertEqual(ref["time_over"]["model_fade_out_states"], 3)
        self.assertEqual(len(ref["continue"]["occurrences"]), 2)                    # fade-out on expiry, then Game Over's own fade-in is another screen
        self.assertTrue(ref["time_over"]["steady_cram"].endswith("00" * 16))        # sprite half stays black on TIME OVER

    # ---------------------------------------------------------------- timeline
    def ev(self, sid, name, i=0):
        return self.by[sid]["events"][name][i]

    def test_time_over_is_reached_at_ten_minutes(self):
        for s in self.ob["scenarios"] + self.ob["zone_matrix"]:
            d = s["death_snapshot"]
            if s["kind"] == "time_over":
                self.assertEqual((d["clock"], d["d44b"]), ("10:00.00", "80"), s["id"])
                self.assertIn(d["rel"], (1, 2), s["id"])                      # the next clock update after the 09:59.59 preset, +/-1 frame
                self.assertIn("time_over_screen", s["events"])
            else:
                self.assertEqual(d["d44b"], "00", s["id"])
                self.assertNotIn("time_over_screen", s["events"])
        self.assertEqual(self.st["time_over_trigger"]["minutes_compare"], "10")

    def test_time_over_timeline(self):
        for sid in ("time_over_lives3", "time_over_no_continue_sonic", "time_over_continue_expire_sonic"):
            d = self.ev(sid, "time_over_exit") - self.ev(sid, "time_over_screen")
            self.assertTrue(270 <= d <= 285, (sid, d))      # 180 + 90 waits plus tile load and three fade passes
        self.assertEqual(self.ev("time_over_lives3", "life_lost_entry"), 2)
        self.assertNotIn("time_over_screen", self.by["pit_game_over_no_continue_sonic"]["events"])
        self.assertEqual(self.by["time_over_lives3"]["end"]["lives_bcd"], "02")
        self.assertEqual(self.by["time_over_lives3"]["end"]["d44b"], "00")

    def test_countdown_cadence(self):
        s = self.by["time_over_continue_expire_sonic"]
        iv = s["derived"]["digit_intervals"]
        self.assertEqual(len(s["derived"]["digit_redraw_frames"]), 9)
        self.assertTrue(all(115 <= x <= 117 for x in iv), iv)
        total = s["events"]["continue_exit"][0] - s["events"]["continue_countdown_call"][0]
        self.assertTrue(1155 <= total <= 1165, total)      # 10 digits x 116 updates
        snd = [x[1] for x in s["sound_requests"]]
        self.assertEqual(snd, ["96", "94"] + ["B4"] * 9 + ["87"])
        for a, b in zip(s["events"]["digit_redraw"], [x[0] for x in s["sound_requests"] if x[1] == "B4"]):
            self.assertIn(b - a, (1, 2))

    def test_idle_animation_cadence(self):
        s = self.by["time_over_continue_expire_sonic"]
        iv = s["idle_frame_change_intervals"]
        self.assertTrue(iv and all(7 <= x <= 9 for x in iv), iv)           # 8 updates per frame, +/-1
        self.assertIn(8, iv)
        self.assertEqual(s["parked_sprite_y_values"], [224, 240])          # unused SAT entries are parked at Y=$E0 or $F0

    def test_game_over_timeline(self):
        for sid in ("time_over_no_continue_sonic", "pit_game_over_no_continue_sonic", "pit_game_over_no_continue_tails", "time_over_continue_expire_sonic"):
            d = self.ev(sid, "game_over_to_title") - self.ev(sid, "game_over_sound")
            self.assertTrue(535 <= d <= 545, (sid, d))     # 240 + 240 holds, fade passes, 60-update wait
            self.assertEqual(self.ev(sid, "title"), self.ev(sid, "game_over_to_title"))
        # direct Game Over: the card is up 8 updates after the branch, the sound one frame after
        d = self.ev("pit_game_over_no_continue_sonic", "game_over_sound") - self.ev("pit_game_over_no_continue_sonic", "game_over_branch")
        self.assertTrue(6 <= d <= 10, d)
        # after an expired countdown the exit fade (60 updates) precedes the card
        e = self.by["time_over_continue_expire_sonic"]["events"]
        self.assertTrue(55 <= e["game_over_branch"][0] - e["continue_exit"][0] <= 65)
        self.assertEqual(self.by["time_over_no_continue_sonic"]["end"]["continues_raw"], "00")

    def test_buttons_do_not_skip_time_over_or_game_over(self):
        s = self.by["time_over_no_continue_sonic"]
        self.assertGreater(len(s["pad_edges"]), 20)           # a button pulse every 20 frames throughout
        base = self.by["pit_game_over_no_continue_sonic"]
        self.assertTrue(535 <= self.ev("time_over_no_continue_sonic", "game_over_to_title") - self.ev("time_over_no_continue_sonic", "game_over_sound") <= 545)
        self.assertIn("game_over_sound", s["events"])
        self.assertIn("title", base["events"])

    # ---------------------------------------------------------------- accepted / expired branches and input edge
    def test_expired_branch_consumes_nothing(self):
        for sid in ("time_over_continue_expire_sonic", "time_over_continue_expire_tails", "pit_continue_press_before_countdown", "pit_continue_button_held"):
            s = self.by[sid]
            self.assertEqual(s["end"]["continues_raw"], "02", sid)
            self.assertIn("game_over_sound", s["events"], sid)
            self.assertNotIn("continue_accept", s["events"], sid)
            self.assertNotIn("A0", [x[1] for x in s["sound_requests"]], sid)

    def test_accepted_branch(self):
        for sid, lives, cont in (("time_over_continue_accept_sonic", "03", "81"), ("pit_continue_accept_first_poll", "03", "81"), ("pit_continue_accept_tails", "05", "82")):
            s = self.by[sid]
            self.assertEqual((s["end"]["lives_bcd"], s["end"]["continues_raw"], s["end"]["score_bcd"]), (lives, cont, "000000"), sid)
            snd = [x[1] for x in s["sound_requests"]]
            self.assertEqual(snd.count("A0"), 1)
            self.assertNotIn("87", snd)
            e = s["events"]
            self.assertIn(e["continue_accept"][0] - s["press_rel"], (0, 1), sid)                                              # +/-1 harness
            # 180-update run hold, then exit fade and 60-update wait, then the restore
            self.assertTrue(175 <= e["continue_exit"][0] - e["continue_accept"][0] <= 185, sid)
            self.assertTrue(55 <= e["continue_restore"][0] - e["continue_exit"][0] <= 65, sid)
            self.assertTrue(0 <= e["level_reload"][0] - e["continue_restore"][0] <= 2, sid)
            self.assertEqual([x[1] for x in s["sound_requests"] if x[0] > e["continue_accept"][0]][0], "A0")
        # the unanswered countdown plays nine ticks, an early answer fewer
        self.assertEqual([x[1] for x in self.by["pit_continue_accept_tails"]["sound_requests"]].count("B4"), 4)

    def test_run_trace_after_accept(self):
        for sid in ("time_over_continue_accept_sonic", "pit_continue_accept_tails"):
            tr = self.by[sid]["accept_trace"]
            self.assertGreater(len(tr), 150)
            xs = [r[1] for r in tr]
            self.assertEqual(xs[0], 128)
            self.assertTrue(all(b >= a for a, b in zip(xs, xs[1:])), "monotone run to the right")
            self.assertGreater(xs[-1], xs[0] + 100)
            sp = [r[2] for r in tr]
            self.assertTrue(all(b >= a and (b - a) % 0x10 == 0 and b - a <= 0x20 for a, b in zip(sp, sp[1:])), "speed word += $0010 per update (two updates may share a frame)")
            self.assertEqual(sp[0], 0)

    def test_input_edge_boundaries(self):
        b = self.ob["boundary"]
        late = {r["delta"]: r["outcome"] for r in b["late_press"]}
        self.assertTrue(all(late[d] == "accepted" for d in range(-9, 1)))
        self.assertTrue(all(late[d] == "expired" for d in range(1, 4)))
        early = {r["delta"]: r["outcome"] for r in b["early_press"]}
        self.assertTrue(all(early[d] == "ignored" for d in range(-6, 1)))
        self.assertTrue(all(early[d] == "accepted" for d in range(1, 4)))
        for r in b["late_press"]:
            self.assertEqual(r["outcome"] == "accepted", r["accept_event"] is not None)

    # ---------------------------------------------------------------- audio
    def test_audio_requests(self):
        rows = {r["request"]: r for r in self.audio["requests"]}
        self.assertEqual(sorted(rows), ["$87", "$94", "$96", "$A0", "$B4"])
        self.assertEqual({k: r["store_cpu"] for k, r in rows.items()}, {"$96": "49B6", "$94": "141D", "$B4": "1487", "$A0": "148E", "$87": "13A5"})
        for k in ("$87", "$94", "$A0"):
            self.assertTrue(rows[k]["poc_support"].startswith("UNSUPPORTED"))
            self.assertTrue(rows[k]["operand_read_from_code"])
        self.assertEqual(rows["$A0"]["name_status"], "unresolved")
        self.assertIsNone(rows["$A0"]["friendly_name"])
        self.assertIn("$03566", [("$%05X" % int(x, 16)) for x in rows["$A0"]["ledger_sites"]] + ["$03566"])
        self.assertNotIn("SND_sonic_death", json.dumps(self.audio["requests"][0].get("friendly_name")))

    def test_audio_requests_observed_exactly(self):
        for s in self.ob["scenarios"]:
            seen = [x[1] for x in s["sound_requests"]]
            for v in seen:
                self.assertIn(v, ("96", "94", "B4", "A0", "87", "88", "81"), (s["id"], v))
            self.assertEqual(seen[0], "96")
            if "game_over_sound" in s["events"]:
                self.assertEqual(seen.count("87"), 1)

    # ---------------------------------------------------------------- audit
    def test_audit_inventory(self):
        poc = self.audit["poc"]
        self.assertEqual(poc["commit"], "b91b833aff15e9668f9c7404c2b70dbc003f9f19")
        items = {i["resource"]: i for i in poc["items"]}
        self.assertTrue(items["SPR_menu_game_over"]["origin"].startswith("INHERITED"))
        self.assertEqual((items["SPR_menu_game_over"]["width"], items["SPR_menu_game_over"]["height"]), (141, 16))
        self.assertTrue(items["SPR_chaos_results_tiles"]["origin"].startswith("ROM-derived"))
        self.assertTrue(any("TIME OVER" in x for x in poc["no_resource_for"]))
        for r in self.audit["research_evidence"]:
            self.assertTrue(r["exists"], r["path"])
            if r["exists"]:
                self.assertEqual(r["sha256"], hashlib.sha256((ROOT / r["path"]).read_bytes()).hexdigest(), "audit hash is stale: " + r["path"])

    # ---------------------------------------------------------------- manifest
    def test_manifest(self):
        a = self.man["assets"]
        for name in ("frames/game_over.png", "frames/time_over.png", "frames/continue_digit0.png", "frames/continue_digit9.png", "frames/continue_sonic_idle0.png",
                     "frames/continue_tails_idle1.png", "tiles/gameover_continue_vram1800.png", "tiles/time_over_vram1800.png", "blocks/continue_digit_glyphs.png",
                     "sprites/sonic_frame11.png", "sprites/tails_frame0F.png", "palettes.json"):
            self.assertIn(name, a)
        for name, v in a.items():
            if name.endswith(".png"):
                self.assertEqual(len(v["index_sha256"]), 64)
                self.assertEqual((v["width"] > 0, v["height"] > 0), (True, True))
        self.assertEqual((a["frames/game_over.png"]["width"], a["frames/game_over.png"]["height"]), (256, 192))
        # distinct frames really are distinct data
        self.assertEqual(len({a["frames/continue_digit%d.png" % d]["index_sha256"] for d in range(10)}), 10)

    def test_exports_are_git_ignored(self):
        r = subprocess.run(["git", "check-ignore", "-q", "build/u4b/frames/game_over.png"], cwd=ROOT)
        self.assertEqual(r.returncode, 0)

    # ---------------------------------------------------------------- documentation
    def test_doc_tables_are_current(self):
        text = B.DOC.read_text(encoding="utf-8")
        for name, body in B.doc_tables(self.st, self.ob, self.audio).items():
            a, b = B._MARK % ("BEGIN", name), B._MARK % ("END", name)
            self.assertIn(a, text, name)
            self.assertEqual(text[text.index(a) + len(a):text.index(b)].strip(), body.strip(), name)

    # ---------------------------------------------------------------- negative controls
    def test_validators_reject_corruption(self):
        st = copy.deepcopy(self.st)
        st["wait_loops"]["time_over_hold"]["iterations"] = 179
        self.assertTrue(B.validate_static(st))
        st = copy.deepcopy(self.st)
        st["countdown"]["ticks_per_digit_compare"] = 115
        self.assertTrue(B.validate_static(st))
        st = copy.deepcopy(self.st)
        st["screens"]["time_over"]["blocks"][0]["row"] = 9
        self.assertTrue(B.validate_static(st))
        ob = copy.deepcopy(self.ob)
        ob["scenarios"][2]["captures"]["time_over_steady"]["bg_pixels_equal"] = False
        self.assertTrue(B.validate_observed(ob))
        ob = copy.deepcopy(self.ob)
        ob["scenarios"][2]["fade_checks"]["continue"]["occurrences"][0]["fade_in_matches_model"] = False
        self.assertTrue(B.validate_observed(ob))
        ob = copy.deepcopy(self.ob)
        ob["boundary"]["late_press"][3]["outcome"] = "expired"
        self.assertTrue(B.validate_observed(ob))
        ob = copy.deepcopy(self.ob)
        {s["id"]: s for s in ob["scenarios"]}["time_over_continue_expire_sonic"]["end"]["continues_raw"] = "01"
        self.assertTrue(B.validate_observed(ob))

    def test_unresolved_list_is_explicit(self):
        ids = {u["id"] for u in self.st["unresolved"]}
        self.assertTrue({"U4B-1", "U4B-2", "U4B-3", "U4B-4", "U4B-10"} <= ids)
        classes = {c["cls"] for c in self.st["evidence_classes"]}
        self.assertTrue({"DECODED DATA", "EMULATED ORIGINAL FRAME", "UNRESOLVED", "SOURCE-TRACED BEHAVIOUR"} <= classes)


@unittest.skipUnless(canonical_rom() is not None, "canonical ROM not available (set SONIC_CHAOS_ROM)")
class AgainstTheRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        cls.st, cls.decoded, cls.art = B.build_static(cls.rom)

    def test_static_census_reproduces(self):
        self.assertEqual(B.dumps(self.st), B.STATIC_JSON.read_text(encoding="utf-8"))
        self.assertEqual(B.validate_static(self.st), [])

    def test_audio_ledger_reproduces(self):
        self.assertEqual(B.dumps(B.build_audio(self.rom, self.st)), B.AUDIO_JSON.read_text(encoding="utf-8"))

    def test_export_hashes_reproduce(self):
        with tempfile.TemporaryDirectory() as td:
            man = B.export_assets(self.rom, self.st, self.decoded, self.art, out=Path(td))
            self.assertEqual(B.dumps(man), B.MANIFEST_JSON.read_text(encoding="utf-8"))
            self.assertTrue((Path(td) / "frames" / "continue_sonic_idle0.png").is_file())

    def test_fill_and_loader_operands_come_from_code(self):
        self.assertEqual(B.u16(self.rom, 0x21DB), 0x00C0)
        self.assertEqual(self.rom[0x13A5 - 2:0x13A5 + 3], bytes([0x3E, 0x87, 0x32, 0x04, 0xDE]))
        self.assertEqual(self.rom[0x141D - 2:0x141D + 3], bytes([0x3E, 0x94, 0x32, 0x04, 0xDE]))
        self.assertEqual(self.rom[0x148E - 2:0x148E + 3], bytes([0x3E, 0xA0, 0x32, 0x04, 0xDE]))
        self.assertEqual(self.rom[0x281C:0x2820], bytes([0x3E, 0xC0, 0x32, 0x4B]))

    def _replay(self, sid):
        sc = {s["id"]: s for s in B.scenario_defs()}[sid]
        out, _ = B.run_scenario(self.rom, sc)
        return B.summarize(self.st, self.art, self.rom, self.decoded, out)

    def test_replay_direct_game_over(self):
        s = self._replay("pit_game_over_no_continue_sonic")
        want = {x["id"]: x for x in B.load_json(B.OBS_JSON)["scenarios"]}["pit_game_over_no_continue_sonic"]
        self.assertEqual(B.dumps(s), B.dumps(want))

    def test_replay_accept_and_check_flags(self):
        s = self._replay("pit_continue_accept_first_poll")
        want = {x["id"]: x for x in B.load_json(B.OBS_JSON)["scenarios"]}["pit_continue_accept_first_poll"]
        self.assertEqual(B.dumps(s), B.dumps(want))

    def test_replay_time_over_with_lives(self):
        s = self._replay("time_over_lives3")
        want = {x["id"]: x for x in B.load_json(B.OBS_JSON)["scenarios"]}["time_over_lives3"]
        self.assertEqual(B.dumps(s), B.dumps(want))
        self.assertEqual(s["end"]["lives_bcd"], "02")


if __name__ == "__main__":
    unittest.main()

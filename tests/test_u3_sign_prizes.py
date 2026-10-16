#!/usr/bin/env python3
"""U3-A tests: goal-sign prize graphics, reward-table parity and retry behaviour.

Part 1 needs no ROM: committed JSON consistency, the pure model re-run on the committed tables, positive and negative controls, the 100-count scan of both
zone-parity tables, Sonic/Tails art classes, retry and retouch rules, life/continue/ring awards and caps, the equal-digit bonus interaction, hash identity between
the static census and the export manifest, and the committed emulated timelines.
Part 2 needs the canonical ROM (SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms), Python >= 3.10 and the `z80` package: it recomputes the static census, the
index-byte hashes of every exported PNG, the Z80 oracle results and a bounded set of emulated clears against the committed files.  The complete regeneration check is
`python tools/u3_sign_prizes.py ROM --check` (about three minutes).
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

import u3_sign_prizes as U  # noqa: E402

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
        cls.ctl = U.load_json(U.CONTROLLED_JSON)
        cls.ob = U.load_json(U.OBS_JSON)
        cls.man = U.load_json(U.MANIFEST_JSON)
        cls.tables = U.tables_of(cls.st)
        cls.tt = U.time_table_of(cls.st)

    # ---------------------------------------------------------------- identity / structure
    def test_identity(self):
        for d in (self.st, self.ctl, self.ob, self.man):
            self.assertEqual(d["rom_sha256"], ROM_SHA)
        for d in (self.st, self.ctl, self.ob):
            self.assertEqual(d["base_commit"], "87ae62b76de35e41c9bb837c1125a54210f2f85c")

    def test_files_are_canonical_dumps(self):
        for path in (U.STATIC_JSON, U.CONTROLLED_JSON, U.OBS_JSON, U.MANIFEST_JSON):
            self.assertEqual(U.dumps(json.loads(path.read_text(encoding="utf-8"))), path.read_text(encoding="utf-8"))

    def test_static_validates(self):
        self.assertEqual(U.validate_static(self.st), [])

    def test_controlled_validates(self):
        self.assertEqual(U.validate_controlled(self.ctl, self.st), [])

    def test_observed_validates(self):
        self.assertEqual(U.validate_observed(self.ob, self.st), [])

    def test_all_anchor_fragments_match(self):
        self.assertGreaterEqual(len(self.st["anchors"]), 18)
        for a in self.st["anchors"]:
            self.assertTrue(a["ok"], a["name"])
            self.assertEqual(a["expected"], a["actual"], a["name"])

    def test_routine_regions_unique_and_ordered(self):
        names = [r["name"] for r in self.st["routines"]]
        self.assertEqual(len(names), len(set(names)))
        for r in self.st["routines"]:
            self.assertEqual(len(r["sha256"]), 64)
            self.assertGreater(r["length"], 0)

    def test_no_pixel_data_in_committed_json(self):
        # tile bytes and index rows are hashed only; palettes are 16 two-bit-per-channel colour bytes
        for k, v in self.st["selectors"].items():
            self.assertEqual(set(v), {"list_cpu", "entries", "face_tile_bytes_sha256", "face_tile_index_sha256", "face_index_histogram", "face_source_cpu", "face_source_file"})
        for v in self.st["composed_frame1"].values():
            self.assertTrue(all(not isinstance(x, list) for x in v.values()))
        for path in (U.STATIC_JSON, U.CONTROLLED_JSON, U.OBS_JSON, U.MANIFEST_JSON):
            self.assertLess(path.stat().st_size, 300_000)

    # ---------------------------------------------------------------- selector art
    def test_selector_lists(self):
        for k in ("12", "1B", "1C", "1D", "1E", "1F", "20"):
            e = self.st["selectors"][k]["entries"][0]
            self.assertEqual((e["bank"], e["tiles"], e["tile_base"], e["remap"]), (13, 16, 0x6A, False), k)
        # $12 has a second, fixed entry; the face selectors do not
        self.assertEqual([len(self.st["selectors"][k]["entries"]) for k in ("12", "1B", "1C", "1D", "1E", "1F", "20")], [2, 1, 1, 1, 1, 1, 1])
        e12 = self.st["selectors"]["12"]["entries"][1]
        self.assertEqual((e12["bank"], e12["tiles"], e12["tile_base"]), (9, 48, 0x7A))

    def test_face_source_blocks_are_512_bytes_apart(self):
        src = {k: int(self.st["selectors"][k]["face_source_file"], 16) for k in ("1B", "1C", "1D", "1E", "1F", "20")}
        self.assertEqual(src["1B"], 0x354BC)
        self.assertEqual([src[k] - src[p] for p, k in zip(("1B", "1C", "1D", "1E", "1F"), ("1C", "1D", "1E", "1F", "20"))], [0x200] * 5)

    def test_selector_12_and_1C_are_identical_and_1C_unused(self):
        s = self.st["selectors"]
        self.assertEqual(s["12"]["face_tile_bytes_sha256"], s["1C"]["face_tile_bytes_sha256"])
        self.assertEqual(self.st["selector_identities"]["same_face_as_12"], ["1C"])
        for scan in self.ctl["first_pass_scan"]["rows"].values():
            self.assertNotIn(0x1C, {row[1] for row in scan})
        for rows in self.ctl["retouch_reroll"]["rows"].values():
            self.assertNotIn(0x1C, {row[1] for row in rows})

    def test_six_distinct_faces(self):
        c = self.st["composed_frame1"]
        self.assertEqual(len({v["face_index_sha256"] for v in c.values()}), 6)
        self.assertEqual(len({v["frame1_index_sha256"] for v in c.values()}), 6)
        self.assertEqual(c["12"]["face_index_sha256"], c["1C"]["face_index_sha256"])
        for v in c.values():
            self.assertEqual((v["face_w"], v["face_h"], v["face_x"], v["face_y"]), (32, 32, -16, -48))

    def test_blank_panel_is_mostly_one_colour(self):
        hist = self.st["selectors"]["20"]["face_index_histogram"]
        self.assertGreater(hist["10"], 600)
        self.assertEqual(set(hist), {"0", "6", "7", "10", "11"})

    def test_mapping_face_pieces(self):
        frames = {f["frame"]: f for f in self.st["sign_mapping"]["frames"]}
        dep = [p for p in frames[1]["pieces"] if p["selector_dependent"]]
        self.assertEqual([p["tile"] for p in dep], [0x6A, 0x6C, 0x6E, 0x70, 0x72, 0x74, 0x76, 0x78])
        self.assertEqual({(p["x"], p["y"]) for p in dep}, {(x, y) for x in (-16, -8, 0, 8) for y in (-48, -32)})
        for i in (2, 3, 4, 5):
            self.assertFalse(any(p["selector_dependent"] for p in frames[i]["pieces"]), i)
        self.assertEqual(len(frames[0]["pieces"]), 0)

    def test_sprite_palettes_per_zone(self):
        z = self.st["sprite_palettes"]["zones"]
        self.assertEqual([z[str(i)]["sprite_index"] for i in range(6)], [6, 7, 8, 9, 10, 11])
        self.assertTrue(all(v["act_independent"] for v in z.values()))
        # zones 1 and 5 use different records with identical colours; the zones differ only in colour 0 (backdrop) and, for SEZ/AQZ, colours 13..15
        self.assertEqual(len({tuple(v["sprite_colours"]) for v in z.values()}), 5)
        self.assertEqual(z["1"]["sprite_colours"], z["5"]["sprite_colours"])
        self.assertEqual({tuple(v["sprite_colours"][1:13]) for v in z.values()}, {tuple(z["0"]["sprite_colours"][1:13])})
        for v in z.values():
            self.assertEqual(len(v["sprite_colours"]), 16)
            self.assertTrue(all(c < 64 for c in v["sprite_colours"]))

    def test_manifest_matches_static_composition(self):
        a = self.man["assets"]
        for k, v in self.st["composed_frame1"].items():
            self.assertEqual(a["faces/face_%s.png" % k]["index_sha256"], v["face_index_sha256"], k)
            self.assertEqual(a["frames/frame1_%s.png" % k]["index_sha256"], v["frame1_index_sha256"], k)
        for i in (2, 3, 4, 5):
            self.assertEqual(a["frames/frame%d_fixed.png" % i]["index_sha256"], self.st["fixed_frames_with_selector_12"]["frames"][str(i)]["index_sha256"])
        self.assertEqual(len([n for n in a if n.startswith("sheets/")]), 6)

    # ---------------------------------------------------------------- tables, parity, 100-count scan
    def test_table_bytes(self):
        t = self.tables
        self.assertEqual([x for x in t["A919"][:16] if x != 0xFF], [0x15, 0x30, 0x40, 0x60])
        self.assertEqual([x for x in t["A919"][16:32] if x != 0xFF], [0x09, 0x19, 0x29, 0x39, 0x49, 0x59, 0x69, 0x79, 0x89])
        self.assertEqual([x for x in t["A919"][32:48] if x != 0xFF], [0x99, 0x97, 0x95, 0x88, 0x77, 0x65, 0x55])
        self.assertEqual([x for x in t["A919"][48:64] if x != 0xFF], [0x16, 0x28, 0x32, 0x44, 0x58])
        self.assertEqual([x for x in t["A962"][:16] if x != 0xFF], [0x00, 0x24, 0x48, 0x72])
        self.assertEqual([x for x in t["A962"][16:32] if x != 0xFF], [0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80, 0x90])
        self.assertEqual([x for x in t["A962"][32:48] if x != 0xFF], [0x98, 0x96, 0x94, 0x87, 0x77, 0x33, 0x11])
        self.assertEqual([x for x in t["A962"][48:64] if x != 0xFF], [0x18, 0x36, 0x45, 0x81, 0x89])

    def test_zone_parity_selection(self):
        self.assertEqual([U.zone_table(z) for z in range(6)], ["A919", "A962", "A919", "A962", "A919", "A962"])
        self.assertEqual(self.st["prize_tables"]["zone_names"], {"0": "THZ", "1": "GPZ", "2": "SEZ", "3": "MGHZ", "4": "AQZ", "5": "EEZ"})
        self.assertEqual(self.ctl["zone_parity"]["all_match_model"], True)

    def test_hundred_count_scan_both_tables(self):
        for name in ("A919", "A962"):
            vec = U.class_vectors(self.tables)[name]
            self.assertEqual(len(vec), 100)
            counts = {c: vec.count(c) for c in set(vec)}
            self.assertEqual(counts, {3: 4, 2: 9, 1: 7, 0: 5, 255: 75})
            for n in range(100):
                bcd = U.int_to_bcd(n)
                idx = [i for i, b in enumerate(self.tables[name]) if b == bcd]
                if idx:
                    self.assertEqual(vec[n], 3 - idx[0] // 16, (name, n))
                else:
                    self.assertEqual(vec[n], 255, (name, n))
        # the two tables disagree almost everywhere: only $77 (life) is a prize in both with the same class
        a, b = U.class_vectors(self.tables)["A919"], U.class_vectors(self.tables)["A962"]
        both = [(U.int_to_bcd(n), a[n], b[n]) for n in range(100) if a[n] != 255 and b[n] != 255]
        self.assertEqual(both, [(0x30, 3, 2), (0x40, 3, 2), (0x60, 3, 2), (0x77, 1, 1), (0x89, 2, 0)])

    def test_no_duplicate_or_nonbcd_counts(self):
        for name, t in self.tables.items():
            vals = [x for x in t if x != 0xFF]
            self.assertEqual(len(vals), len(set(vals)), name)
            self.assertTrue(all(U.is_bcd(x) for x in vals), name)
        self.assertEqual(self.st["prize_tables"]["duplicates_inside_a_table"], {"A919": [], "A962": []})

    def test_first_pass_scan_matches_model_all_cells(self):
        for key, rows in self.ctl["first_pass_scan"]["rows"].items():
            name, p = key.rsplit("_p", 1)
            zone = 0 if name == "A919" else 1
            self.assertEqual(len(rows), 100)
            for n, row in enumerate(rows):
                m = U.prize_landing(self.tables, zone, int(p), U.int_to_bcd(n), 0, 0, U.BASE_LIVES, U.BASE_CONT)
                self.assertEqual(row, [m["cls"], m["art"], m["lives"], m["cont"], m["rings"], m["state"], m["retry"]], (key, n))
        self.assertEqual(self.ctl["first_pass_scan"]["model_mismatches"], [])

    # ---------------------------------------------------------------- Sonic / Tails art, rewards
    def test_sonic_tails_art_classes(self):
        self.assertEqual([U.art_of(c, 1) for c in (0, 1, 2, 3, 255, 4, 8)], [0x20, 0x1B, 0x1E, 0x1D, 0x1F, 0x1F, 0x1F])
        self.assertEqual([U.art_of(c, 2) for c in (0, 1, 2, 3, 255, 4, 8)], [0x20, 0x1D, 0x1E, 0x1B, 0x1F, 0x1F, 0x1F])
        # the life face is the player's own face; the continue face is the other character's
        rows = self.ctl["first_pass_scan"]["rows"]
        self.assertEqual(rows["A919_p1"][55][1], 0x1B)      # decimal index 55 = BCD $55, life, Sonic
        self.assertEqual(rows["A919_p2"][55][1], 0x1D)
        self.assertEqual(rows["A919_p1"][15][1], 0x1D)                    # BCD $15, continue, Sonic -> Tails face
        self.assertEqual(rows["A919_p2"][15][1], 0x1B)

    def test_rewards_and_effects(self):
        t = self.tables
        base = (U.BASE_LIVES, U.BASE_CONT)
        life = U.prize_landing(t, 0, 1, 0x55, 0, 0, *base)
        self.assertEqual((life["lives"], life["cont"], life["rings"], life["art"], life["state"]), (0x13, 0x34, 0x55, 0x1B, 5))
        cont = U.prize_landing(t, 0, 1, 0x15, 0, 0, *base)
        self.assertEqual((cont["lives"], cont["cont"], cont["rings"], cont["art"]), (0x12, 0x35, 0x15, 0x1D))
        rings = U.prize_landing(t, 0, 1, 0x09, 0, 0, *base)
        self.assertEqual((rings["lives"], rings["cont"], rings["rings"], rings["art"]), (0x12, 0x34, 0x19, 0x1E))
        none = U.prize_landing(t, 0, 1, 0x01, 0, 0, *base)
        self.assertEqual((none["lives"], none["cont"], none["rings"], none["art"], none["state"], none["retry"]), (0x12, 0x34, 0x01, 0x1F, 5, 0))
        retry = U.prize_landing(t, 0, 1, 0x16, 0, 0, *base)
        self.assertEqual((retry["cls"], retry["art"], retry["state"], retry["retry"], retry["rings"]), (0, 0x20, 3, 0xFF, 0x16))

    def test_caps_and_wraps(self):
        self.assertEqual(U.grant_life(0x98), 0x99)
        self.assertEqual(U.grant_life(0x99), 0x99)
        self.assertEqual(U.grant_life(0x09), 0x10)
        self.assertEqual(U.grant_continue(0x09), 0x10)
        self.assertEqual(U.grant_continue(0x79), 0x00)             # wraps: the 80th continue
        self.assertEqual(U.grant_continue(0x80), 0x01)             # bit 7 (continue just used) is dropped
        self.assertEqual(U.grant_rings(0x89), 0x99)
        self.assertEqual(U.grant_rings(0x90), 0x00)                # carry dropped (even table count)
        for lv, after, sound in self.ctl["caps"]["rows"]["lives"]:
            self.assertEqual(after, U.grant_life(lv))
            self.assertEqual(sound, 0xA9)                          # the life sound plays even at the cap
        self.assertEqual([r for r in self.ctl["caps"]["rows"]["lives"] if r[0] == 0x99], [[0x99, 0x99, 0xA9]])
        self.assertIn([0x79, 0x00, U.BASE_LIVES], self.ctl["caps"]["rows"]["continues"])

    def test_bcd_helpers_against_python_arithmetic(self):
        for a in range(100):
            for b in (1, 10, 17):
                r, c = U.add_bcd(U.int_to_bcd(a), U.int_to_bcd(b))
                self.assertEqual((U.bcd_to_int(r), c), ((a + b) % 100, a + b >= 100))
                r, c = U.sub_bcd(U.int_to_bcd(a), U.int_to_bcd(b))
                self.assertEqual((U.bcd_to_int(r), c), ((a - b) % 100, a < b))

    # ---------------------------------------------------------------- retry / retouch
    def test_retouch_roll_table(self):
        for p, rows in self.ctl["retouch_reroll"]["rows"].items():
            for d in range(256):
                self.assertEqual(rows[d][0], (d & 7) + 1)
            self.assertEqual([r[0] for r in rows[:8]], [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertFalse(self.ctl["retouch_reroll"]["class_zero_reachable"])
        self.assertEqual(self.ctl["retouch_reroll"]["retry_flag_after"], [255])
        self.assertTrue(self.ctl["retouch_reroll"]["depends_only_on_low_three_bits"])
        self.assertTrue(self.ctl["retouch_ring_independence"]["all_counts_same_class"])

    def test_retouch_outcomes_by_roll(self):
        t = self.tables
        want = {0: "life", 1: "rings", 2: "continue", 3: "none", 4: "none", 5: "none", 6: "none", 7: "none"}
        for d, effect in want.items():
            res = U.prize_landing(t, 0, 1, 0x16, 1, d, U.BASE_LIVES, U.BASE_CONT)
            self.assertEqual(U.effect_of(res["cls"]), effect, d)
            self.assertEqual(res["state"], 5)
        self.assertEqual(sum(1 for e in want.values() if e != "none"), 3)

    def test_retry_cannot_repeat(self):
        t = self.tables
        for zone in (0, 1):
            for n in range(100):
                rings = U.int_to_bcd(n)
                for d in range(8):
                    first = U.prize_landing(t, zone, 1, rings, 0, d, U.BASE_LIVES, U.BASE_CONT)
                    if first["cls"] != 0:
                        continue
                    again = U.prize_landing(t, zone, 1, rings, 1, d, U.BASE_LIVES, U.BASE_CONT)
                    self.assertNotEqual(again["cls"], 0)
                    self.assertEqual(again["state"], 5)

    def test_retry_count_set(self):
        for zone, want in ((0, [0x16, 0x28, 0x32, 0x44, 0x58]), (1, [0x18, 0x36, 0x45, 0x81, 0x89])):
            got = [U.int_to_bcd(n) for n in range(100) if U.lookup_class(self.tables[U.zone_table(zone)], U.int_to_bcd(n)) == 0]
            self.assertEqual(got, want)

    # ---------------------------------------------------------------- equal-digit bonus word and interaction
    def test_time_table(self):
        self.assertEqual([e[2] for e in self.tt], [9, 8, 7, 6, 5, 4, 3, 2, 1, 0])
        self.assertEqual([e[0] for e in self.tt], [0x29, 0x59, 0x129, 0x159, 0x229, 0x259, 0x329, 0x359, 0x459, 0xFFFF])
        self.assertTrue(all(e[1] == 0 for e in self.tt))

    def test_bonus_word_examples(self):
        tt = self.tt
        self.assertEqual(U.bonus_word(tt, 0x0001, 0x15), (9, 0x04))
        self.assertEqual(U.bonus_word(tt, 0x0001, 0x00), (9, 0x89))            # 0 rings: no borrow into H
        self.assertEqual(U.bonus_word(tt, 0x0459, 0x11), (0, 0x00))
        self.assertEqual(U.child_bonus(tt, 0x0459, 0x11), (0x0777, 1))        # zero -> $0777 -> equal digits -> life
        self.assertEqual(U.child_bonus(tt, 0x0040, 0x99), (0x0888, 1))
        self.assertEqual(U.child_bonus(tt, 0x0001, 0x99), (0x0988, 0))
        self.assertEqual(U.child_bonus(tt, 0x0001, 0x10), (0x0999, 1))

    def test_last_time_bucket_ends_at_459_not_429(self):
        tt = self.tt
        self.assertEqual(U.bonus_word(tt, 0x0428, 0x11)[0], 1)
        self.assertEqual(U.bonus_word(tt, 0x0429, 0x11)[0], 1)        # a 4:29 cut-off would give 0 here
        self.assertEqual(U.bonus_word(tt, 0x0458, 0x11)[0], 1)
        self.assertEqual(U.bonus_word(tt, 0x0459, 0x11)[0], 0)
        cmp = self.st["bonus_word"]["comparison_with_poc_g1c"]
        self.assertEqual(cmp["differs_at_index"], [8])
        self.assertEqual(cmp["rom_limits_seconds"][-1], 299)
        self.assertEqual(cmp["poc_limits_seconds"][-1], 269)

    def test_equal_digit_cases_are_exactly_the_diagonal(self):
        cases = {(t, r) for t, r, _w in self.ctl["bonus_word"]["equal_digit_cases"]}
        want = set()
        for t in self.ctl["bonus_word"]["times"]:
            for n in range(100):
                w, eq = U.child_bonus(self.tt, int(t, 16), U.int_to_bcd(n))
                digits = {(w >> 8) & 15, (w >> 4) & 15, w & 15}
                self.assertEqual(eq, 1 if len(digits) == 1 and (w >> 8) < 10 else 0, (t, n, w))
                if eq:
                    want.add((t, "%02X" % U.int_to_bcd(n)))
        self.assertEqual(cases, want)
        self.assertEqual(len(cases), 21)

    def test_zero_word_replacement(self):
        self.assertEqual(self.ctl["bonus_word"]["zero_to_0777"], [["0459", "11"], ["0900", "11"]])

    def test_ring_prize_feeds_the_bonus(self):
        t, tt = self.tables, self.tt
        with_prize = U.award_sequence(t, tt, 0, 1, 0x09, 0x0100, 0x12, 0x34)
        self.assertEqual(with_prize["rings"], 0x19)
        self.assertEqual(with_prize["bonus_word"], 0x0708)          # 0x19 - 0x11 = 0x08 (not 0x09 - 0x11 -> 0x98)
        self.assertEqual(U.child_bonus(tt, 0x0100, 0x09)[0], 0x0798)

    def test_class_one_plus_equal_digit_is_two_lives(self):
        t, tt = self.tables, self.tt
        r = U.award_sequence(t, tt, 0, 1, 0x99, 0x0040, 0x12, 0x34)
        self.assertEqual((r["lives"], r["life_awards"], r["bonus_word"]), (0x14, 2, 0x0888))
        r = U.award_sequence(t, tt, 1, 1, 0x11, 0x0500, 0x12, 0x34)           # even table class 1 and the zero word
        self.assertEqual((r["lives"], r["life_awards"], r["bonus_word"]), (0x14, 2, 0x0777))
        r = U.award_sequence(t, tt, 0, 1, 0x99, 0x0040, 0x99, 0x34)           # cap: neither adds
        self.assertEqual((r["lives"], r["life_awards"]), (0x99, 0))
        r = U.award_sequence(t, tt, 0, 1, 0x99, 0x0040, 0x98, 0x34)           # only the first reaches 99
        self.assertEqual((r["lives"], r["life_awards"]), (0x99, 1))

    def test_class_award_never_comes_from_the_bonus_word(self):
        # a non-prize ring count with an equal-digit word gives exactly one life, and a class-1 count without one gives one
        t, tt = self.tables, self.tt
        r = U.award_sequence(t, tt, 1, 1, 0x99, 0x0040, 0x12, 0x34)           # $99 is no prize on the even table, but $0888 is equal-digit
        self.assertEqual((r["final_class"], r["life_awards"]), (0xFF, 1))
        r = U.award_sequence(t, tt, 0, 1, 0x55, 0x0001, 0x12, 0x34)
        self.assertEqual((r["final_class"], r["life_awards"]), (1, 1))

    def test_double_life_cases_from_the_chain(self):
        ch = self.ctl["chain"]
        self.assertEqual(ch["model_mismatches"], [])
        self.assertEqual(ch["double_life_count"], 14)
        for c in ch["double_life_cases"]:
            self.assertEqual(int(c["lives"], 16), 0x14)

    # ---------------------------------------------------------------- negative controls
    def test_negative_corrupted_table_is_detected(self):
        bad = copy.deepcopy(self.st)
        bad["prize_tables"]["bytes"]["A919"][0] = 0x16               # duplicate of a class-0 count
        self.assertTrue(U.validate_static(bad))

    def test_negative_swapped_tables_change_every_zone(self):
        swapped = {"A919": self.tables["A962"], "A962": self.tables["A919"]}
        a, b = U.class_vectors(self.tables), U.class_vectors(swapped)
        self.assertNotEqual(a, b)
        self.assertEqual(U.lookup_class(self.tables[U.zone_table(0)], 0x15), 3)
        self.assertEqual(U.lookup_class(self.tables[U.zone_table(1)], 0x15), 0xFF)
        self.assertEqual(U.lookup_class(self.tables[U.zone_table(1)], 0x00), 3)
        self.assertEqual(U.lookup_class(self.tables[U.zone_table(0)], 0x00), 0xFF)

    def test_negative_wrong_art_and_wrong_effect_are_detected(self):
        bad = copy.deepcopy(self.ctl)
        bad["first_pass_scan"]["rows"]["A919_p1"][55][1] = 0x1D
        self.assertTrue(U.validate_controlled(bad, self.st))
        bad = copy.deepcopy(self.ctl)
        bad["caps"]["rows"]["lives"][-1][1] = 0x00
        self.assertTrue(U.validate_controlled(bad, self.st))
        bad = copy.deepcopy(self.ctl)
        bad["bonus_word"]["words_by_time"]["0029"][99] ^= 0x0001
        self.assertTrue(U.validate_controlled(bad, self.st))
        bad = copy.deepcopy(self.ctl)
        bad["chain"]["rows"][5][4] ^= 1
        self.assertTrue(U.validate_controlled(bad, self.st))

    def test_negative_observation_defects_are_detected(self):
        bad = copy.deepcopy(self.ob)
        rec = bad["scenarios"]["thz1_sonic_r55"]
        rec["final"]["lives"] = "03"
        self.assertTrue(U.validate_observed(bad, self.st))
        bad = copy.deepcopy(self.ob)
        bad["scenarios"]["thz1_tails_r15"]["captures"]["final"]["vram_face_equals_selector"] = ["1D"]
        self.assertTrue(U.validate_observed(bad, self.st))
        bad = copy.deepcopy(self.ob)
        ev = bad["scenarios"]["thz1_sonic_r15"]["events"]
        for e in ev:
            if e[1] == "landing_call":
                e[3] += 1
        self.assertTrue(U.validate_observed(bad, self.st))

    # ---------------------------------------------------------------- committed emulation
    def test_scenario_set_covers_the_assignment(self):
        sc = self.ob["scenarios"]
        for needed in ("thz1_sonic_r15", "thz1_sonic_r09", "thz1_sonic_r55", "thz1_sonic_r01", "thz1_tails_r15", "thz1_tails_r55"):
            self.assertIn(needed, sc)
        self.assertEqual([k for k in sc if k.startswith("thz1_sonic_r16_retouch_wait")], ["thz1_sonic_r16_retouch_wait%d" % i for i in range(9)])
        for zone in range(6):
            for r in ("15", "24"):
                self.assertIn("zone%d_act0_sonic_r%s" % (zone, r), sc)
            self.assertIn("zone%d_act1_sonic_r15" % zone, sc)

    def test_every_retouch_class_1_to_8_was_observed(self):
        got = set()
        for k, r in self.ob["scenarios"].items():
            if "retouch_wait" in k and r["player_type"] == 1:
                got.add(r["final_plus34"])
        self.assertEqual(got, {1, 2, 3, 4, 5, 6, 7, 8})

    def test_observed_parity_matrix(self):
        sc = self.ob["scenarios"]
        for zone in range(6):
            odd = U.zone_table(zone) == "A919"
            self.assertEqual(sc["zone%d_act0_sonic_r15" % zone]["final_plus34"], 3 if odd else 255, zone)
            self.assertEqual(sc["zone%d_act0_sonic_r24" % zone]["final_plus34"], 255 if odd else 3, zone)
            self.assertEqual(sc["zone%d_act1_sonic_r15" % zone]["final_plus34"], 3 if odd else 255, zone)
            for key in ("zone%d_act0_sonic_r15" % zone, "zone%d_act0_sonic_r24" % zone):
                self.assertEqual(sc[key]["base"]["continues"], "00")
        self.assertEqual(sc["zone1_sonic_r00_even_continue"]["final"]["continues"], "01")

    def test_observed_sonic_and_tails_faces(self):
        sc = self.ob["scenarios"]
        face = lambda k: sc[k]["captures"]["final"]["vram_face_equals_selector"]
        self.assertEqual((face("thz1_sonic_r55"), face("thz1_tails_r55")), (["1B"], ["1D"]))
        self.assertEqual((face("thz1_sonic_r15"), face("thz1_tails_r15")), (["1D"], ["1B"]))
        self.assertEqual((face("thz1_sonic_r09"), face("thz1_tails_r09")), (["1E"], ["1E"]))
        self.assertEqual(face("thz1_sonic_r01"), ["1F"])
        self.assertEqual(sc["thz1_sonic_r15"]["player_type"], 1)
        self.assertEqual(sc["thz1_tails_r15"]["player_type"], 2)
        for k in sc:
            self.assertEqual(sc[k]["captures"]["default"]["vram_face_equals_selector"], ["12", "1C"], k)

    def test_observed_award_cases(self):
        sc = self.ob["scenarios"]
        self.assertEqual((sc["thz1_sonic_r55"]["base"]["lives"], sc["thz1_sonic_r55"]["final"]["lives"]), ("03", "04"))
        self.assertEqual((sc["thz1_sonic_r15"]["base"]["continues"], sc["thz1_sonic_r15"]["final"]["continues"]), ("00", "01"))
        self.assertEqual((sc["thz1_sonic_r09"]["base"]["rings"], sc["thz1_sonic_r09"]["final"]["rings"]), ("09", "19"))
        self.assertEqual(sc["thz1_sonic_r55_lives99_cap"]["final"]["lives"], "99")
        self.assertEqual(sc["thz1_sonic_r15_continues79_wrap"]["final"]["continues"], "00")
        self.assertEqual((sc["thz1_sonic_r99_t0040_two_lives"]["final"]["lives"], sc["thz1_sonic_r99_t0040_two_lives"]["final"]["D2A6"]), ("05", "0888"))
        self.assertEqual((sc["zone1_sonic_r11_t0500_zero_word_two_lives"]["final"]["lives"], sc["zone1_sonic_r11_t0500_zero_word_two_lives"]["final"]["D2A6"]), ("05", "0777"))
        self.assertEqual(sc["thz1_sonic_r09_ring_prize_bonus"]["final"]["D2A6"], "0708")
        # tails start with 5 lives and 3 continues
        self.assertEqual((sc["thz1_tails_r55"]["base"]["lives"], sc["thz1_tails_r15"]["base"]["continues"]), ("05", "03"))

    def test_life_sound_counts(self):
        sc = self.ob["scenarios"]
        self.assertEqual(sc["thz1_sonic_r55"]["sounds"]["A9"][2], 1)
        self.assertEqual(sc["thz1_sonic_r99_t0040_two_lives"]["sounds"]["A9"][2], 2)
        self.assertEqual(sc["thz1_sonic_r55_lives99_cap"]["sounds"]["A9"][2], 1)      # sound at the cap too
        self.assertNotIn("A9", sc["thz1_sonic_r15"]["sounds"])
        self.assertNotIn("A9", sc["thz1_sonic_r09"]["sounds"])

    def test_observed_timeline_is_in_sign_updates(self):
        uc = self.st["adapter"]["rom_native"]["update_counts"]
        self.assertEqual((uc["contact_to_landing"], uc["contact_to_child_spawn"], uc["contact_to_bonus_word_and_equal_digit_life"], uc["contact_to_player_state_20"]), (130, 131, 278, 280))
        self.assertEqual((uc["retouch_request_to_landing"], uc["retouch_spin_updates"], uc["face_upload_frames"]), (65, 64, 4))

    def test_retry_blank_panel_is_displayed_between_touches(self):
        for k, r in self.ob["scenarios"].items():
            if "retouch" in k or "retry" in k:
                self.assertEqual(r["captures"]["retry"]["vram_face_equals_selector"], ["20"], k)
                self.assertTrue(r["captures"]["retry"]["sprite_palette_equals_rom_zone"], k)

    def test_foreground_priority_masking_is_recorded(self):
        masked = {k: r["captures"]["final"]["face_pixels_masked_by_bg_priority"] for k, r in self.ob["scenarios"].items()}
        self.assertEqual({k for k, v in masked.items() if v}, {"zone2_act0_sonic_r15", "zone2_act0_sonic_r24"})
        for r in self.ob["scenarios"].values():
            for name, c in r["captures"].items():
                self.assertEqual(c["face_pixels_hidden_other"], 0)
                if name != "default":       # the idle capture is taken while the camera still scrolls (the SAT shows the previous update's camera)
                    self.assertEqual(c["face_origin_minus_screen_anchor"], [-16, -47])       # mapping (-16,-48) + the VDP's one-line sprite offset

    def test_sprite_palette_matches_rom_for_every_zone(self):
        for k, r in self.ob["scenarios"].items():
            for c in r["captures"].values():
                self.assertTrue(c["sprite_palette_equals_rom_zone"], k)
                self.assertEqual(c["sprite_palette_cram"], self.st["sprite_palettes"]["zones"][str(r["zone"])]["sprite_colours"])

    def test_retry_has_no_timeout_child_or_act_clear(self):
        self.assertEqual(sorted(self.ob["retry_hold"]), ["idle", "right"])
        for mode, h in self.ob["retry_hold"].items():
            self.assertEqual(h["frames_held"], 900)
            self.assertEqual((h["sign_state"], h["plus34"], h["plus35"]), (3, 0, 255), mode)
            self.assertEqual((h["timer_run_D2BE"], h["act_flag_D293"], h["child_present"]), (0, "40", False), mode)
            self.assertEqual((h["lives"], h["continues"], h["rings"]), ("03", "00", "16"), mode)
            self.assertEqual(h["retry_face"], ["20"])
        self.assertEqual(self.ob["retry_hold"]["right"]["player_minus_camera_x"], 247)       # view clamp cam + $F7

    def test_poc_prize_rows_equal_the_rom_tables(self):
        # chaos_thz_prize_rows / chaos_gpz_prize_rows (POC G1-C, read-only comparison on 2026-10-16) as decimal renderings of the raw bytes
        thz = [[21, 48, 64, 96], [9, 25, 41, 57, 73, 89, 105, 121, 137], [153, 151, 149, 136, 119, 101, 85], [22, 40, 50, 68, 88]]
        gpz = [[0, 36, 72, 114], [16, 32, 48, 64, 80, 96, 112, 128, 144], [152, 150, 148, 135, 119, 51, 17], [24, 54, 69, 129, 137]]
        for name, rows in (("A919", thz), ("A962", gpz)):
            self.assertEqual([[x for x in self.tables[name][i * 16:(i + 1) * 16] if x != 0xFF] for i in range(4)], rows)

    def test_document_tables_are_current(self):
        text = U.DOC.read_text(encoding="utf-8")
        for name, body in U.doc_tables(self.st, self.ctl, self.ob).items():
            block = U._MARK % ("BEGIN", name) + "\n" + body + "\n" + U._MARK % ("END", name)
            self.assertIn(block, text, name)

    def test_zones_in_observations(self):
        self.assertEqual({r["zone"] for r in self.ob["scenarios"].values()}, {0, 1, 2, 3, 4, 5})


class RomRecomputation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        if cls.rom is None or sys.version_info < (3, 10):
            raise unittest.SkipTest("canonical ROM / Python >= 3.10 not available")
        cls.st = U.build_static(cls.rom)

    def test_static_census_is_byte_identical(self):
        self.assertEqual(U.dumps(self.st), U.STATIC_JSON.read_text(encoding="utf-8"))

    def test_static_is_deterministic(self):
        self.assertEqual(U.dumps(U.build_static(self.rom)), U.dumps(self.st))

    def test_exports_match_committed_manifest_and_stored_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            man = U.export_assets(self.rom, self.st, out=Path(td))
            self.assertEqual(U.dumps(man), U.MANIFEST_JSON.read_text(encoding="utf-8"))
            from PIL import Image
            for name, a in man["assets"].items():
                im = Image.open(Path(td) / name)
                self.assertEqual(im.size, (a["width"], a["height"]))
                self.assertEqual(hashlib.sha256(bytes(im.getdata())).hexdigest(), a["index_sha256"], name)
            for s in ("12", "1B", "1C", "1D", "1E", "1F", "20"):
                raw = (Path(td) / "tiles" / ("selector_%s_face_tiles.bin" % s)).read_bytes()
                self.assertEqual(len(raw), 512)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), self.st["selectors"][s]["face_tile_bytes_sha256"])

    def test_pixel_index_identity_of_every_selector_through_two_decoders(self):
        # decode the 16 tiles a second, independent way (numpy-free bit loops written differently) and compare the composed hash
        for s in (0x12, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20):
            tiles = U.selector_tiles(self.rom, s)
            idx = bytearray()
            for k in range(16):
                raw = tiles[0x6A + k]
                for y in range(8):
                    b0, b1, b2, b3 = raw[4 * y:4 * y + 4]
                    for x in range(8):
                        sh = 7 - x
                        idx.append(((b0 >> sh) & 1) + 2 * ((b1 >> sh) & 1) + 4 * ((b2 >> sh) & 1) + 8 * ((b3 >> sh) & 1))
            self.assertEqual(hashlib.sha256(bytes(idx)).hexdigest(), self.st["selectors"]["%02X" % s]["face_tile_index_sha256"])

    def test_prize_tables_come_from_the_rom_bytes(self):
        t = U.prize_tables(self.rom)
        self.assertEqual({k: list(v) for k, v in t.items()}, U.tables_of(U.load_json(U.STATIC_JSON)))

    def test_controlled_results_match_z80_for_a_sample(self):
        orc = U.Oracle3(self.rom)
        tables = U.prize_tables(self.rom)
        tt = U.time_table(self.rom)
        for zone in (0, 1):
            for n in (0, 9, 15, 16, 24, 55, 99):
                rings = U.int_to_bcd(n)
                for pt in (1, 2):
                    z = orc.landing(zone, pt, rings, 0, 3, 0x12, 0x34)
                    m = U.prize_landing(tables, zone, pt, rings, 0, 3, 0x12, 0x34)
                    self.assertEqual((z["cls"], z["art"], z["lives"], z["cont"], z["rings"]), (m["cls"], m["art"], m["lives"], m["cont"], m["rings"]))
        for d in range(8):
            z = orc.landing(0, 1, 0x16, 1, d, 0x12, 0x34)
            self.assertEqual(z["cls"], d + 1)
        c = orc.child(0x0040, 0x99, 0x12)
        self.assertEqual((c["word"], c["lives"], c["sound"]), (0x0888, 0x13, 0xA9))
        c = orc.child(0x0459, 0x11, 0x12)
        self.assertEqual((c["word"], c["lives"]), (0x0777, 0x13))

    def test_controlled_json_is_reproduced(self):
        ctl = U.build_controlled(self.rom, self.st)
        self.assertEqual(U.dumps(ctl), U.CONTROLLED_JSON.read_text(encoding="utf-8"))

    def test_bounded_emulated_clears_match_committed_observations(self):
        committed = U.load_json(U.OBS_JSON)["scenarios"]
        wanted = ["thz1_sonic_r15", "thz1_sonic_r55", "thz1_tails_r15", "zone1_act0_sonic_r24", "thz1_sonic_r16_retouch_wait2"]
        ob = U.build_observed(self.rom, self.st, progress=lambda s: None, only=wanted)
        for k in wanted:
            self.assertEqual(U.dumps(ob["scenarios"][k]), U.dumps(committed[k]), k)


if __name__ == "__main__":
    unittest.main()

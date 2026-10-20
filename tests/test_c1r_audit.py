"""C1-R audit tests.

Cache classes run without a ROM.  ROM classes need the verified ROM (SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms) and skip otherwise.

    python -m unittest tests.test_c1r_audit
"""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import c1r_build_register as B  # noqa: E402
import c1r_camera_model as M  # noqa: E402

TRACE = json.loads((ROOT / "data/c1r/camera-look-trace.json").read_text())
REG = json.loads((ROOT / "data/c1r/gameplay-fidelity-register.json").read_text())
CON = json.loads((ROOT / "data/c1r/implementation-contracts.json").read_text())
SIGN = json.loads((ROOT / "data/c1r/sign-registration.json").read_text())
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"


def find_rom():
    cands = []
    if os.environ.get("SONIC_CHAOS_ROM"):
        cands.append(Path(os.environ["SONIC_CHAOS_ROM"]))
    cands.append(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")
    for c in cands:
        if c.is_file() and hashlib.sha256(c.read_bytes()).hexdigest() == ROM_SHA:
            return c
    return None


def scenario(name):
    return next(s for s in TRACE["scenarios"] if s["name"] == name)


def col(sc, name):
    i = sc["columns"].index(name)
    return [r[i] for r in sc["rows"]]


class TraceAndModel(unittest.TestCase):
    def test_schema(self):
        self.assertEqual(TRACE["schema"], "c1r-camera-look-trace/2")
        self.assertEqual(TRACE["rom_sha256"], ROM_SHA)
        for sc in TRACE["scenarios"]:
            self.assertTrue(all(len(r) == len(sc["columns"]) for r in sc["rows"]), sc["name"])

    def test_model_replays_every_update(self):
        """The pure-Python follow model reproduces the next update's working camera and both leads in all 3,557 recorded updates."""
        total = 0
        for sc in TRACE["scenarios"]:
            ix = {c: i for i, c in enumerate(sc["columns"])}
            rows = sc["rows"]
            for a, b in zip(rows, rows[1:]):
                cam = M.Camera(a[ix["work_x"]], a[ix["work_y"]], a[ix["lead_x"]], a[ix["lead_y"]], limits=(0, 100000, 8, 784))
                cam.update(a[ix["px"]], a[ix["py"]], bool(a[ix["face"]]), a[ix["lead_target"]], pan_mode=bool(a[ix["pan"]] & 3))
                self.assertEqual((cam.cam_x, cam.cam_y, cam.lead_x, cam.lead_y), (b[ix["work_x"]], b[ix["work_y"]], b[ix["lead_x"]], b[ix["lead_y"]]), (sc["name"], total))
                total += 1
        self.assertGreaterEqual(total, 3500)

    def test_idle_wait_is_180_updates(self):
        sc = scenario("idle_wait")
        st = col(sc, "state")
        first2 = st.index(2)
        self.assertEqual(st[:first2].count(1), 180)

    def test_look_up(self):
        sc = scenario("look_up_hold_release")
        cy, lead, tgt, py = col(sc, "cam_y"), col(sc, "lead_y"), col(sc, "lead_target"), col(sc, "py")
        self.assertEqual(sorted(set(tgt)), [96, 184])
        self.assertEqual(lead[149], 184)
        self.assertEqual(cy[149] - cy[0], -56)
        self.assertEqual(py[149] - cy[149], 168)
        self.assertEqual(py[-1] - cy[-1], 112)                     # returns to the lower zone edge
        first = next(i for i, c in enumerate(cy) if c != cy[0])
        self.assertEqual(first, 35)

    def test_look_down(self):
        sc = scenario("look_down_hold_release")
        cy, lead, tgt, py = col(sc, "cam_y"), col(sc, "lead_y"), col(sc, "lead_target"), col(sc, "py")
        self.assertEqual(sorted(set(tgt)), [48, 96])
        self.assertEqual(lead[149], 48)
        self.assertEqual(cy[149] - cy[0], 48)
        self.assertEqual(py[149] - cy[149], 64)
        self.assertEqual(py[-1] - cy[-1], 80)                      # hysteresis: rests at the upper zone edge

    def test_closed_form_helper_agrees_with_trace(self):
        first, final = M.look_displacement(112, M.Y_LEAD_LOOK_UP, 150)
        self.assertEqual(final, 168)
        self.assertEqual(first, 33)                                # 33 lead steps before the zone edge passes Sonic
        _first, final = M.look_displacement(112, M.Y_LEAD_CRAWL, 150)
        self.assertEqual(final, 64)

    def test_peel_out(self):
        sc = scenario("peel_out_ordinary")
        st, vx, mv = col(sc, "state"), col(sc, "vx"), col(sc, "move")
        self.assertIn(21, st)
        self.assertIn(26, st)
        self.assertEqual(max(vx), 1792)                            # +$0700 at the release
        self.assertEqual(sum(1 for m in mv if m & 0x80), 12)       # invulnerable window, D3B1 = $0C
        self.assertEqual(st.index(26) - st.index(21), 63)          # charge lasts while Up is held: 62 updates after the request frame + 1
        hr = scenario("peel_out_hold_right")
        self.assertGreaterEqual(sum(1 for x in col(hr, "vx") if x == 1792), 30)

    def test_peel_out_aura(self):
        """The star aura (object type 5) appears exactly 60 + 24 + 210 x 8 = 1,764 frames after state $15 starts."""
        sc = scenario("peel_out_long_hold")
        entry_frame = sc["rows"][col(sc, "state").index(21)][0]
        aura = next(f for f, types in sc["object_type_changes_by_frame"] if 5 in types)
        self.assertEqual(aura - entry_frame, 1764)


class SignRegistration(unittest.TestCase):
    def test_poc_art_is_rom_art_minus_top_four_rows(self):
        base = next(p for p in SIGN["poc"] if p["sprite"] == "SPR_chaos_object_18")
        self.assertEqual(len(base["frames"]), 5)
        for f in base["frames"]:
            self.assertEqual(f["xor_if_poc_shifted_down_4"], 0)
            self.assertEqual(f["poc_opaque_rows"], [0, 43])
            self.assertGreater(f["rom_rows_0_3_pixels"], 0)
        prize = next(p for p in SIGN["poc"] if p["sprite"] == "SPR_chaos_thz_sign_prizes")
        self.assertEqual(len(prize["frames"]), 8)
        self.assertTrue(all(f["xor_if_poc_shifted_down_4"] == 0 for f in prize["frames"]))
        self.assertEqual(SIGN["derived"]["poc_extra_offset"], 4)
        self.assertEqual(SIGN["derived"]["expected_draw_y_offset_for_bottom_origin_canvas"], 18)

    def test_rom_frames_are_48_rows(self):
        for f in SIGN["rom_frames"]:
            self.assertEqual(f["opaque_rows_on_canvas"], [0, 47])
        self.assertEqual(SIGN["rom_frames"][0]["pieces"], 10)


class RegisterAndContracts(unittest.TestCase):
    def test_register_is_current(self):
        reg, con = B.build()
        self.assertEqual(reg, REG)
        self.assertEqual(con, CON)

    def test_register_schema(self):
        ids = [r["id"] for r in REG["rows"]]
        self.assertEqual(len(ids), len(set(ids)))
        need = {"id", "subsystem", "rom_ref", "evidence", "confidence", "canonical_rom_behaviour", "current_poc_behaviour", "classification", "existing_coverage",
                "user_visible_impact", "implementation_risk", "recommended_action", "track", "dependencies"}
        for r in REG["rows"]:
            self.assertTrue(need <= set(r), r["id"])
            self.assertIn(r["classification"], B.CLASSES)
            self.assertIn(r["track"], B.TRACKS)
            self.assertTrue(r["evidence"], r["id"])
            for e in r["evidence"]:
                self.assertIn(e["class"], B.EVIDENCE)
            if r["classification"] == "MATCH":
                self.assertIn("match_basis", r, r["id"])           # a match is never 'no bug seen'
        self.assertEqual(REG["counts"]["rows"], len(ids))
        self.assertEqual(sum(REG["counts"]["by_classification"].values()), len(ids))

    def test_references_resolve(self):
        ids = {r["id"] for r in REG["rows"]}
        dec = {d["id"] for d in CON["decisions_required_before_dispatch"]}
        for r in REG["rows"]:
            for d in r["dependencies"] + r["related"]:
                self.assertTrue(d in ids or d in dec, (r["id"], d))
        for it in CON["items"]:
            for e in it["rom_evidence"]:
                self.assertTrue(e in ids or e.startswith("data/"), (it["id"], e))
            for d in it["dependencies"]:
                self.assertTrue(any(d.startswith(x) for x in list(ids) + list(dec) + ["I"]), (it["id"], d))
        for t in ("C1-I",):
            self.assertTrue(any(r["track"] == t for r in REG["rows"]))

    def test_c1i_rows_are_covered_by_an_item(self):
        covered = set()
        for it in CON["items"]:
            covered.update(e for e in it["rom_evidence"] if e in {r["id"] for r in REG["rows"]})
        for r in REG["rows"]:
            if r["track"] == "C1-I":
                self.assertIn(r["id"], covered, r["id"])

    def test_no_rom_bytes_committed(self):
        for p in (ROOT / "data" / "c1r").glob("*.json"):
            self.assertLess(p.stat().st_size, 400_000, p)


@unittest.skipUnless(find_rom(), "verified ROM not available")
class RomBacked(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = find_rom().read_bytes()

    def test_lead_writers(self):
        """Every `LD (D289),A` in the ROM and the immediate that precedes it: 13 writers = $B8 look-up, $30 crouch, $78 level init, ten x $60."""
        found = []
        i = 0
        while True:
            i = self.rom.find(bytes([0x32, 0x89, 0xD2]), i)
            if i < 0:
                break
            found.append((i - 1, self.rom[i - 1]))
            i += 1
        self.assertEqual(len(found), 13)
        values = dict(found)
        self.assertEqual(sorted(values.values()), [0x30, 0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x78, 0xB8])
        self.assertEqual({off for off, v in found if v == 0xB8}, {0x371A})
        self.assertEqual({off for off, v in found if v == 0x30}, {0x3760})

    def test_peel_out_constants(self):
        self.assertEqual(self.rom[0x46E2:0x46E5], bytes([0x21, 0x00, 0x07]))         # LD HL,$0700 (max speed and speed)
        self.assertEqual(self.rom[0x46DC:0x46DE], bytes([0x3E, 0xAC]))               # charge sound request after LD (IX+2),$15
        self.assertEqual(self.rom[0x46FB:0x46FD], bytes([0x3E, 0xBE]))               # release sound request after LD (IX+2),$1A
        self.assertEqual(self.rom[0x3719:0x371E], bytes([0x3E, 0xB8, 0x32, 0x89, 0xD2]))
        self.assertEqual(self.rom[0x375F:0x3764], bytes([0x3E, 0x30, 0x32, 0x89, 0xD2]))

    def test_sign_tool_is_current(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import c1r_sign_registration as S
        import u3_sign_prizes as U
        res = json.loads(json.dumps(S.analyse(U.load_rom(str(find_rom())), None)))
        self.assertEqual(res["rom_frames"], SIGN["rom_frames"])


if __name__ == "__main__":
    unittest.main()

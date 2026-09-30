#!/usr/bin/env python3
"""THZ1/THZ2/THZ3 level-package tests (THZ1 is the control fixture)."""
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS = ROOT / "data" / "rom-cache" / "levels"
spec = importlib.util.spec_from_file_location("level_export", ROOT / "tools" / "level_export.py")
export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)
L = export.L

EXPECTED = {
    "thz1": dict(layout=0x48000, end=0x48BA9, objects=0x705AE, term=0x7078B, dims=(128, 32), raw=53, types=8,
                 terrain=142, nine=(24, 11, 13),
                 cells="8c489abb1061b142f5bb730f89e42bacf71c5a436ac659665b29c309ab95841f",
                 terrain_hash="fcdd77998cc7b7b70ac9bfed765ce0ee783b6d42f6eb20e5d9837bd9272c1794",
                 all_hash="3740a3a9c2b88ccef1cee20bb0be915f52ae449c66560574b7c515973bc1e240"),
    "thz2": dict(layout=0x48BA9, end=0x49815, objects=0x7078C, term=0x708FD, dims=(128, 32), raw=41, types=7,
                 terrain=133, nine=(13, 9, 4),
                 cells="f82a410cf15d0464357d43e3ac5519b3ac09f9ba88ae902ea213e8f6fdb9cd87",
                 terrain_hash="58c06312aec331d99fc0f6bf6b9133418cd0ee0449c2c64ee07d0558cbc5cebf",
                 all_hash="adf48eb1ef0c446c76b31888f5a996dfa6960e9d87404eee9a5def200d362022"),
    "thz3": dict(layout=0x49815, end=0x49C25, objects=0x708FE, term=0x70958, dims=(80, 16), raw=10, types=5,
                 terrain=6, nine=(3, 3, 0),
                 cells="ed8d7ccc54cf372580edd678750bb8cf01a3772141562d0ee61f8f78bc8f1923",
                 terrain_hash="53525821d99c0cfedbf96a97a7627feb3809664e21f1a005a2be1f0a9710cddb",
                 all_hash="bbbffbf210311549cb92e98b226871c981de3fff77594022dd4bc69e52eab521"),
}


def load(*parts):
    return json.loads(LEVELS.joinpath(*parts).read_text(encoding="utf-8"))


def text(path):
    """File text with universal newlines (CRLF checkouts compare equal)."""
    return path.read_text(encoding="utf-8")


def matching_rom():
    candidates = []
    if os.environ.get("SONIC_CHAOS_ROM"):
        candidates.append(Path(os.environ["SONIC_CHAOS_ROM"]))
    candidates += [ROOT.parent / "Sonic Chaos (Europe).sms", ROOT / "Sonic Chaos (Europe).sms"]
    for path in candidates:
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == L.ROM_SHA256:
            return path
    return None


class CommittedPackageTests(unittest.TestCase):
    """Consistency of the committed JSON; no ROM needed."""

    def test_dimensions_and_layout_shape(self):
        for act, exp in EXPECTED.items():
            lay = load(act, "layout.json")
            w, h = exp["dims"]
            self.assertEqual((lay["dimensions"]["width_cells"], lay["dimensions"]["height_cells"]), (w, h))
            self.assertEqual(len(lay["rows"]), h)
            self.assertTrue(all(len(r) == w for r in lay["rows"]))
            self.assertEqual(lay["layout_stream"]["rom_offset"], f"0x{exp['layout']:05X}")
            self.assertEqual(lay["layout_stream"]["end_offset_exclusive"], f"0x{exp['end']:05X}")
            self.assertTrue(all(lay["dimensions"]["consistency_checks"].values()))

    def test_layout_hashes_stable(self):
        for act, exp in EXPECTED.items():
            lay = load(act, "layout.json")
            flat = bytes(c for row in lay["rows"] for c in row)
            self.assertEqual(hashlib.sha256(flat).hexdigest(), exp["cells"])
            self.assertEqual(lay["cells_sha256"], exp["cells"])

    def test_layout_streams_are_contiguous(self):
        self.assertEqual(EXPECTED["thz1"]["end"], EXPECTED["thz2"]["layout"])
        self.assertEqual(EXPECTED["thz2"]["end"], EXPECTED["thz3"]["layout"])

    def test_object_table_boundaries_and_counts(self):
        for act, exp in EXPECTED.items():
            obj = load(act, "objects.json")
            lst = obj["list"]
            self.assertEqual(lst["start_rom"], f"0x{exp['objects']:05X}")
            self.assertEqual(lst["terminator_rom"], f"0x{exp['term']:05X}")
            self.assertEqual(lst["record_count"], exp["raw"])
            self.assertEqual(len(obj["records"]), exp["raw"])
            self.assertEqual(lst["record_bytes"], 9 * exp["raw"])
            self.assertEqual(len({r["type_id"] for r in obj["records"]}), exp["types"])
        self.assertEqual(EXPECTED["thz1"]["term"] + 1, EXPECTED["thz2"]["objects"])
        self.assertEqual(EXPECTED["thz2"]["term"] + 1, EXPECTED["thz3"]["objects"])

    def test_no_duplicate_or_phantom_placements(self):
        for act, exp in EXPECTED.items():
            recs = load(act, "objects.json")["records"]
            self.assertEqual(len({r["rom_offset"] for r in recs}), len(recs))
            self.assertEqual(len({r["raw_bytes"] for r in recs}), len(recs))
            start = int(recs[0]["rom_offset"], 16)
            for n, r in enumerate(recs):
                self.assertEqual(int(r["rom_offset"], 16), start + 9 * n)
                self.assertEqual(len(r["raw_bytes"].split()), 9)
            rings = load(act, "rings.json")["rings"]
            self.assertEqual(len({r["id"] for r in rings}), len(rings))
            nine = [r for r in recs if r["type_id"] == "0x09"]
            self.assertEqual(sum(r["source_class"] != "terrain" for r in rings), len(nine))

    def test_ring_counts_and_hashes(self):
        for act, exp in EXPECTED.items():
            rj = load(act, "rings.json")
            raw, vis, hid = exp["nine"]
            c = rj["counts"]
            self.assertEqual((c["terrain"], c["object_09_raw_records"], c["object_09_visible"], c["object_09_hidden"]),
                             (exp["terrain"], raw, vis, hid))
            self.assertEqual(c["initial_visible_population"], exp["terrain"] + vis)
            self.assertEqual(rj["hashes"]["terrain_coordinates_sha256"], exp["terrain_hash"])
            self.assertEqual(rj["hashes"]["all_rings_sha256"], exp["all_hash"])
            self.assertEqual(L.coordinate_hash(L.ring_hash_rows(rj["rings"])), exp["all_hash"])

    def test_thz1_control_known_points(self):
        rj = load("thz1", "rings.json")
        vis = {(r["world_x"], r["world_y"]) for r in rj["rings"] if r["source_class"] == "object_09_visible"}
        for p in export.CONTROL_LOOP + export.CONTROL_TWIST + export.CONTROL_POST_TWIST:
            self.assertIn(p, vis)
        self.assertEqual(rj["counts"]["initial_visible_population"], 153)

    def test_type09_parameters_only_known(self):
        for act in EXPECTED:
            params = {r["parameter"] for r in load(act, "objects.json")["records"] if r["type_id"] == "0x09"}
            self.assertLessEqual(params, {"0x00", "0x01"})

    def test_census_new_types(self):
        census = load("object-census.json")
        self.assertEqual(census["acts"]["thz2"]["new_types_vs_thz1"], [])
        self.assertEqual(census["acts"]["thz3"]["new_types_vs_thz1"], ["0x50"])
        row = {t["type_id"]: t for t in census["types"]}["0x50"]
        self.assertEqual(row["classes"], ["C", "D"])

    def test_asset_pointers(self):
        a = load("thz3", "assets.json")
        by = {t["type_id"]: t for t in a["object_types"]}
        self.assertEqual(by["0x50"]["mapping"]["pointer_table_rom"], "0x3C0A0")
        self.assertEqual(by["0x50"]["mapping"]["mapping_cpu"], "0x94C6")
        self.assertEqual(by["0x50"]["mapping"]["mapping_rom"], "0x3D4C6")
        self.assertEqual(by["0x26"]["mapping"]["mapping_cpu"], "0x91C0")
        self.assertEqual(a["palettes"]["sprite"]["rom"], "0x3B6AD")
        self.assertEqual(a["palettes"]["background"]["rom"], "0x3B79D")
        self.assertNotIn("reference_sheet", by["0x50"])  # no invented graphics


@unittest.skipIf(matching_rom() is None, "matching ROM not available (set SONIC_CHAOS_ROM)")
class RomRegenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = L.load_rom(matching_rom())

    def test_descriptors_match_historical_leads(self):
        for act, exp in EXPECTED.items():
            d = L.build_descriptor(self.rom, act)
            self.assertEqual(d["layout"]["rom"], exp["layout"])
            self.assertEqual(d["objects"]["list_rom"], exp["objects"])
            self.assertEqual((d["layout"]["width_cells"], d["layout"]["height_cells"]), exp["dims"])
            self.assertTrue(all(v["agrees"] for v in L.compare_historical(d).values()))

    def test_thz1_control_fixture(self):
        export._ROM[0] = self.rom
        act = L.build_act(self.rom, "thz1")
        result = export.verify_thz1_control(self.rom, act)
        self.assertTrue(all(result.values()))
        self.assertEqual(len(act["terrain_rings"]), 142)

    def test_ring_blocks_from_rom_tables(self):
        sem = L.ring_block_semantics(self.rom)
        self.assertEqual(sem["ring_blocks"], [0x40, 0x41, 0x42, 0x43, 0x44, 0x45])

    def test_type09_runtime_semantics(self):
        checks = export.type09_runtime_checks(self.rom, {0, 1})
        self.assertEqual(checks[0]["requested_state"], 1)
        self.assertEqual(checks[1]["requested_state"], 3)

    def test_thz1_terrain_matches_existing_renderer(self):
        bg = export._load("thz1_background_registration")
        world, _, _ = bg.render_indices(self.rom)
        act = L.build_act(self.rom, "thz1")
        blocks = L.block_pixel_maps(self.rom, act["vram"])
        for index in (0, 500, 2047, 4000):
            ox, oy = (index % 128) * 32, (index // 128) * 32
            for y in (0, 15, 31):
                row = bytes(blocks[act["cells"][index]][y])
                self.assertEqual(world[(oy + y) * 4096 + ox:(oy + y) * 4096 + ox + 32], row)

    def test_committed_json_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            export.build_all(self.rom, Path(tmp))
            files = ["layout.json", "rings.json", "objects.json", "assets.json", "manifest.json"]
            for act in EXPECTED:
                for name in files:
                    self.assertEqual(text(Path(tmp) / act / name), text(LEVELS / act / name), f"{act}/{name}")
            self.assertEqual(text(Path(tmp) / "object-census.json"), text(LEVELS / "object-census.json"))

    def test_rom_hash_unchanged(self):
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(), L.ROM_SHA256)


if __name__ == "__main__":
    unittest.main()

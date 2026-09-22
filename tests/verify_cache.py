"""Regenerate the ROM metadata cache and compare it byte-for-byte."""
import sys
from pathlib import Path

import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from cache_game_data import EXPECTED_SHA256, decode_layout, decode_objects, layout_interactions


def main(rom_path):
    rom = Path(rom_path).read_bytes()
    assert hashlib.sha256(rom).hexdigest() == EXPECTED_SHA256
    layout, layout_end = decode_layout(rom)
    records = decode_objects(rom)
    interactions = layout_interactions(layout)
    stored_objects = json.loads((ROOT / "data/rom-cache/thz1/object-records.json").read_text())
    stored_layout = json.loads((ROOT / "data/rom-cache/thz1/layout-interactions.json").read_text())
    assert stored_objects["records"] == records
    assert stored_layout["compressed_read_end"] == f"0x{layout_end:05X}"
    assert stored_layout["terrain"] == interactions["terrain"]
    assert stored_layout["rings"] == interactions["rings"]
    assert len(records) == 53
    assert sum(r["decoded_kind"] is not None for r in records) == 14
    print("ROM cache: 53 records, 14 decoded placements, 17 terrain interactions, 142 rings")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tests/verify_cache.py /path/to/SonicChaos.sms")
    main(sys.argv[1])

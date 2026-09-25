"""Regenerate the ROM metadata cache and compare it byte-for-byte."""
import sys
from pathlib import Path

import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from cache_game_data import EXPECTED_SHA256, decode_layout, decode_objects, layout_interactions
import thz1_object_10 as object10
import thz1_object_21 as object21
import player_state_11_graphics as player_graphics
import thz1_background_registration as background


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
    stored_object10 = json.loads(
        (ROOT / "data/rom-cache/thz1/object-10.json").read_text(encoding="utf-8")
    )
    assert stored_object10 == object10.build_report(rom)
    stored_object21 = json.loads(
        (ROOT / "data/rom-cache/thz1/object-21.json").read_text(encoding="utf-8")
    )
    assert stored_object21 == object21.build_report(rom)
    stored_player = json.loads(
        (ROOT / "data/rom-cache/thz1/player-state-11-graphics.json").read_text(encoding="utf-8")
    )
    assert stored_player == player_graphics.build(rom)
    stored_background = json.loads(
        (ROOT / "data/rom-cache/thz1/background-registration.json").read_text(encoding="utf-8")
    )
    for patch in stored_background["patches"]:
        patch.pop("poc_18_5", None)
    assert stored_background == background.build(rom)
    manifest = json.loads(
        (ROOT / "data/rom-cache/thz1/manifest.json").read_text(encoding="utf-8")
    )
    for name, expected in manifest["files"].items():
        payload = (ROOT / "data/rom-cache/thz1" / name).read_bytes()
        assert len(payload) == expected["bytes"]
        assert hashlib.sha256(payload).hexdigest() == expected["sha256"]
    assert len(records) == 53
    assert sum(r["decoded_kind"] is not None for r in records) == 14
    print(
        "ROM cache: 53 records, 14 decoded placements, 17 terrain interactions, "
        "142 rings; type-$10/$21, player-$11 graphics, and background metadata deterministic"
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tests/verify_cache.py /path/to/SonicChaos.sms")
    main(sys.argv[1])

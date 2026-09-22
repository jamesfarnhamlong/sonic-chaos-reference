"""Export verified THZ1 Sonic Chaos graphics streams to an ignored build folder.

This tool consumes metadata from data/rom-cache/thz1/graphics-map.json.
It writes ROM-derived bytes only under the requested output directory; the
recommended/default location is build/, which is ignored by Git.

Python 3.10+.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from tile_decompress import apply_rom_remap, decompress_tile_stream, read_u16le

DEFAULT_MAP = ROOT / "data" / "rom-cache" / "thz1" / "graphics-map.json"


def parse_hex(value):
    if isinstance(value, int):
        return value
    return int(value, 16)


def slot2_rom_offset(bank, cpu_address):
    if not 0x8000 <= cpu_address <= 0xBFFF:
        raise ValueError(f"slot-2 CPU address outside $8000-$BFFF: ${cpu_address:04X}")
    return bank * 0x4000 + (cpu_address - 0x8000)


def verify_source_tables(rom, metadata):
    level = metadata["level_art"]
    table_rom = parse_hex(level["table_rom_offset"])
    expected = bytes.fromhex(level["thz1_entry_raw"])
    actual = rom[table_rom:table_rom + len(expected)]
    if actual != expected:
        raise AssertionError(
            f"THZ1 level-art entry differs at ROM ${table_rom:05X}: "
            f"{actual.hex(' ').upper()}"
        )

    supplemental = metadata["supplemental_list"]
    list_rom = parse_hex(supplemental["rom_offset"])
    cursor = list_rom
    for entry in supplemental["entries"]:
        expected = bytes.fromhex(entry["raw"])
        actual = rom[cursor:cursor + 5]
        if actual != expected:
            raise AssertionError(
                f"supplemental entry differs at ROM ${cursor:05X}: "
                f"{actual.hex(' ').upper()}"
            )
        bank_byte = expected[0]
        bank = bank_byte & 0x1F
        cpu = expected[3] | (expected[4] << 8)
        declared = parse_hex(entry["stream_rom_offset"])
        calculated = slot2_rom_offset(bank, cpu)
        if calculated != declared:
            raise AssertionError(
                f"{entry['id']}: declared ROM ${declared:05X}, "
                f"calculated ${calculated:05X}"
            )
        cursor += 5

    if rom[cursor] != 0xFF:
        raise AssertionError("THZ1 supplemental list terminator is not $FF")


def stream_manifest(rom, stream):
    offset = parse_hex(stream["stream_rom_offset"])
    raw = decompress_tile_stream(rom, offset)
    if stream.get("transform_remap"):
        raw = apply_rom_remap(raw, rom)

    tile_count = len(raw) // 32
    expected = stream.get("expected_tile_count")
    if expected is not None and tile_count != expected:
        raise AssertionError(
            f"{stream['id']}: decoded {tile_count} tiles; expected {expected}"
        )

    return raw, {
        "id": stream["id"],
        "stream_rom_offset": f"0x{offset:05X}",
        "stream_cpu_address": stream["stream_cpu_address"],
        "bank_byte": stream["bank_byte"],
        "vram_destination": stream["vram_destination"],
        "base_tile": stream["base_tile"],
        "transform_remap": bool(stream.get("transform_remap")),
        "tile_count": tile_count,
        "byte_count": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "header": {
            "tile_count": read_u16le(rom, offset + 2),
            "command_offset": f"0x{read_u16le(rom, offset + 4):04X}",
            "raw": " ".join(f"{b:02X}" for b in rom[offset:offset + 6]),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build" / "thz1-graphics",
    )
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    metadata = json.loads(args.map.read_text())
    digest = hashlib.sha256(rom).hexdigest()
    if digest != metadata["rom_sha256"]:
        raise ValueError("ROM hash differs; graphics offsets are revision-specific")

    verify_source_tables(rom, metadata)

    args.output.mkdir(parents=True, exist_ok=True)
    manifests = []

    streams = [metadata["level_art"]["primary_stream"]]
    streams.extend(metadata["supplemental_list"]["entries"])

    for stream in streams:
        raw, manifest = stream_manifest(rom, stream)
        out_dir = args.output / stream["id"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "raw_tiles.bin").write_bytes(raw)
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        manifests.append(manifest)

    summary = {
        "rom_sha256": digest,
        "source_map": str(args.map),
        "streams": manifests,
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(json.dumps({
        "output": str(args.output),
        "streams": len(manifests),
        "tiles": sum(item["tile_count"] for item in manifests),
    }, indent=2))


if __name__ == "__main__":
    main()

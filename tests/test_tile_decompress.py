"""Tests for the Sonic Chaos tile-stream decompressor and THZ1 graphics map."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from tile_decompress import (
    _rr,
    _xor_reconstruct,
    decompress_tile_stream,
    extract_command,
)


def make_header(tile_count, command_offset):
    return bytes([
        0x00, 0x00,
        tile_count & 0xFF, (tile_count >> 8) & 0xFF,
        command_offset & 0xFF, (command_offset >> 8) & 0xFF,
    ])


class TileDecompressTests(unittest.TestCase):
    def test_two_bit_commands_are_low_pair_first(self):
        data = bytes([0xE4])
        self.assertEqual([extract_command(data, 0, i) for i in range(4)], [0, 1, 2, 3])

    def test_command_zero(self):
        data = make_header(1, 6) + bytes([0x00])
        self.assertEqual(decompress_tile_stream(data), bytes(32))

    def test_command_one_raw_copy(self):
        raw = bytes(range(32))
        data = make_header(1, 38) + raw + bytes([0x01])
        self.assertEqual(decompress_tile_stream(data), raw)

    def test_sparse_expansion(self):
        bitmap = bytes([0x05, 0x00, 0x00, 0x00])
        payload = bytes([0xAA, 0xBB])
        command_offset = 6 + len(bitmap) + len(payload)
        data = make_header(1, command_offset) + bitmap + payload + bytes([0x02])
        expected = bytearray(32)
        expected[0] = 0xAA
        expected[2] = 0xBB
        self.assertEqual(decompress_tile_stream(data), bytes(expected))

    def test_rr_carry(self):
        self.assertEqual(_rr(0x01, 0), (0x00, 1))
        self.assertEqual(_rr(0x00, 1), (0x80, 0))

    def test_sparse_crosses_register_boundary(self):
        bitmap = bytes([0x00, 0x01, 0x00, 0x00])
        payload = bytes([0xA5])
        command_offset = 6 + len(bitmap) + len(payload)
        data = make_header(1, command_offset) + bitmap + payload + bytes([0x02])
        expected = bytearray(32)
        expected[8] = 0xA5
        self.assertEqual(decompress_tile_stream(data), bytes(expected))

    def test_command_three_xor(self):
        expected = bytes([
            0, 1, 2, 2, 6, 7, 0, 0,
            8, 9, 2, 2, 14, 15, 0, 0,
            16, 17, 2, 2, 22, 23, 0, 0,
            24, 25, 2, 2, 30, 31, 0, 0,
        ])
        tile = bytearray(range(32))
        _xor_reconstruct(tile)
        self.assertEqual(bytes(tile), expected)

        bitmap = bytes([0xFF, 0xFF, 0xFF, 0xFF])
        payload = bytes(range(32))
        command_offset = 6 + 4 + 32
        data = make_header(1, command_offset) + bitmap + payload + bytes([0x03])
        self.assertEqual(decompress_tile_stream(data), expected)

    def test_multiple_tiles(self):
        raw = bytes(range(32))
        command_offset = 6 + len(raw)
        data = make_header(2, command_offset) + raw + bytes([0x04])
        self.assertEqual(decompress_tile_stream(data), bytes(32) + raw)

    def test_truncated_inputs(self):
        with self.assertRaises(ValueError):
            decompress_tile_stream(bytes(5))

        data = make_header(1, 7) + bytes([0xAA, 0x01])
        with self.assertRaises(ValueError):
            decompress_tile_stream(data)

        bitmap = bytes([0x03, 0x00, 0x00, 0x00])
        data = make_header(1, 10) + bitmap + bytes([0x02])
        with self.assertRaises(ValueError):
            decompress_tile_stream(data)


class GraphicsMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.map = json.loads(
            (ROOT / "data" / "rom-cache" / "thz1" / "graphics-map.json").read_text()
        )

    def test_primary_mapping(self):
        level = self.map["level_art"]
        self.assertEqual(level["table_rom_offset"], "0x07CED")
        self.assertEqual(level["thz1_entry_raw"], "10 00 18 9E 8F 13 7E")
        self.assertEqual(level["primary_stream"]["stream_rom_offset"], "0x40F9E")
        self.assertEqual(level["primary_stream"]["expected_tile_count"], 251)

    def test_supplemental_stream_offsets(self):
        for entry in self.map["supplemental_list"]["entries"]:
            raw = bytes.fromhex(entry["raw"])
            bank = raw[0] & 0x1F
            cpu = raw[3] | (raw[4] << 8)
            expected = bank * 0x4000 + (cpu - 0x8000)
            self.assertEqual(expected, int(entry["stream_rom_offset"], 16))

    def test_object_mapping_offsets(self):
        for item in self.map["object_sprite_mappings"]:
            cpu = int(item["mapping_cpu_address"], 16)
            expected = 0x3C000 + (cpu - 0x8000)
            self.assertEqual(expected, int(item["mapping_rom_offset"], 16))


if __name__ == "__main__":
    unittest.main(verbosity=2)

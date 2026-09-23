#!/usr/bin/env python3
"""Synthetic tests for thz1_object_assets.py.

These tests do not replace the hard ROM-anchor validation in the real tool.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "thz1_object_assets.py"

spec = importlib.util.spec_from_file_location("thz1_object_assets", TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ParserTests(unittest.TestCase):
    def test_pointer_formula(self):
        rom = bytearray(0x40000)
        # Type $21 entry is at $3C042 and points to CPU $911B.
        rom[0x3C042:0x3C044] = bytes([0x1B, 0x91])
        got = m.object_mapping(bytes(rom), 0x21)
        self.assertEqual(got["pointer_table_rom"], 0x3C042)
        self.assertEqual(got["mapping_cpu"], 0x911B)
        self.assertEqual(got["mapping_rom"], 0x3D11B)

    def test_mapping_pointer_list_stops_at_frame_record(self):
        rom = bytearray(0x40000)
        pos = m.cpu15_to_rom(0x911B)
        # Real structural pattern for type $21 mapping:
        # A0E4, 9121, 912C, then frame record starts 06 0B...
        rom[pos:pos+8] = bytes([0xE4,0xA0, 0x21,0x91, 0x2C,0x91, 0x06,0x0B])
        self.assertEqual(
            m.mapping_frame_pointers(bytes(rom), 0x911B),
            [0xA0E4, 0x9121, 0x912C],
        )

    def test_frame_record_parser(self):
        rom = bytearray(0x40000)
        frame_cpu = 0x91C8
        frame_rom = m.cpu15_to_rom(frame_cpu)
        # Known type-$26 frame-0 record from the checked ROM dump.
        record = bytes([0x04,0x08,0x20,0x77,0xA2,0,0,0,0,0xE9,0x91])
        rom[frame_rom:frame_rom+11] = record

        coords_rom = m.cpu15_to_rom(0xA277)
        # Four simple (y,x) pairs.
        coords = (
            (0,0), (0,8), (16,0), (16,8)
        )
        p = coords_rom
        for y,x in coords:
            rom[p:p+2] = int(y & 0xFFFF).to_bytes(2,"little")
            rom[p+2:p+4] = int(x & 0xFFFF).to_bytes(2,"little")
            p += 4

        tiles_rom = m.cpu15_to_rom(0x91E9)
        rom[tiles_rom:tiles_rom+4] = bytes([0,2,4,6])

        got = m.parse_frame_record(bytes(rom), frame_cpu)
        self.assertEqual(got["piece_count"], 4)
        self.assertEqual(got["raw_word_1"], 0x2008)
        self.assertEqual(got["coords_cpu"], 0xA277)
        self.assertEqual(got["tile_list_cpu"], 0x91E9)
        self.assertEqual(got["tile_offsets"], [0,2,4,6])
        self.assertEqual(
            [(p["relative_y"],p["relative_x"]) for p in got["pieces"]],
            list(coords),
        )

    def test_mode4_planar_decode(self):
        # One row: palette indices 1,2,4,8 then zeroes.
        raw = bytearray(32)
        raw[0] = 0b10000000
        raw[1] = 0b01000000
        raw[2] = 0b00100000
        raw[3] = 0b00010000
        pix = m.decode_mode4_tile(bytes(raw))
        self.assertEqual(pix[0], [1,2,4,8,0,0,0,0])

    def test_sms_cram_decode(self):
        self.assertEqual(m.sms_color(0x00), (0, 0, 0, 255))
        self.assertEqual(m.sms_color(0x3F), (255, 255, 255, 255))
        self.assertEqual(m.sms_color(0x1B), (255, 170, 85, 255))
        self.assertEqual(m.sms_color(0x38, transparent=True), (0, 170, 255, 0))

    def test_thz1_sprite_palette_selection(self):
        rom = bytearray(m.PALETTE_DATA_ROM + 0x200)
        rom[m.LEVEL_PALETTE_INDEX_ROM:m.LEVEL_PALETTE_INDEX_ROM+2] = bytes([0x15,0x06])
        start = m.PALETTE_DATA_ROM + 0x06 * 16
        rom[start:start+16] = bytes(range(16))
        got = m.thz1_sprite_palette(bytes(rom))
        self.assertEqual(got[0][3], 0)
        self.assertEqual(got[1], m.sms_color(1))


if __name__ == "__main__":
    unittest.main(verbosity=2)

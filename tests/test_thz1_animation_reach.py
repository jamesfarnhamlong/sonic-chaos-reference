#!/usr/bin/env python3
"""Synthetic tests for thz1_animation_reach.py."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Stub v2 module dependency by importing the real local v2 tool. The disposable
# research repo should already contain thz1_object_assets.py from the previous pass.
TOOL = ROOT / "tools" / "thz1_animation_reach.py"
spec = importlib.util.spec_from_file_location("thz1_animation_reach", TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class AnimationTests(unittest.TestCase):
    def make_rom(self):
        return bytearray(0x80000)

    def put_cpu(self, rom, bank, cpu, data):
        pos = bank * 0x4000 + (cpu - 0x8000)
        rom[pos:pos+len(data)] = data

    def test_state_count_from_first_script(self):
        rom = self.make_rom()
        type_id = 0x09
        # $65BA + ($09-1)*2 -> CPU $9000
        entry = m.ANIM_TYPE_TABLE_ROM + (type_id - 1) * 2
        rom[entry:entry+2] = bytes([0x00, 0x90])
        # table at bank $0C:$9000, first script at $9006 => 3 states
        self.put_cpu(rom, 0x0C, 0x9000, bytes([
            0x06,0x90, 0x0C,0x90, 0x12,0x90
        ]))
        got = m.animation_state_table(bytes(rom), type_id)
        self.assertEqual(got["state_count"], 3)
        self.assertEqual(got["state_script_cpus"], [0x9006,0x900C,0x9012])

    def test_static_record_then_loop(self):
        rom = self.make_rom()
        self.put_cpu(rom, 0x0C, 0x9100, bytes([
            0x20,0x0E,0x34,0x12, 0xFF,0x00
        ]))
        got = m.parse_state_script(bytes(rom),0x0C,0x9100,0)
        self.assertEqual(got["frame_indices"], [0x0E])
        self.assertIsNone(got["unresolved"])

    def test_command6_and_jump7(self):
        rom = self.make_rom()
        self.put_cpu(rom, 0x0C, 0x9200, bytes([
            0xFF,0x06,0xA7,
            0xE0,0x0E,0x8B,0xAC,
            0xFF,0x07,0x03,0x92
        ]))
        got = m.parse_state_script(bytes(rom),0x0C,0x9200,0)
        self.assertEqual(got["frame_indices"], [0x0E])
        self.assertIsNone(got["unresolved"])

    def test_velocity_and_orientation_field_commands(self):
        rom = self.make_rom()
        self.put_cpu(rom, 0x0C, 0x9250, bytes([
            0xFF,0x02,0x00,0x00,0x00,0x02,
            0xFF,0x0C,0x04,0x10,
            0x08,0x01,0x68,0xB2,
            0xFF,0x0B,0x04,0xEF,
            0x08,0x02,0x64,0xB2,
            0xFF,0x00,
        ]))
        got = m.parse_state_script(bytes(rom),0x0C,0x9250,0)
        self.assertEqual(got["frame_indices"], [1, 2])
        self.assertIsNone(got["unresolved"])
        commands = [x.get("meaning") for x in got["commands"]]
        self.assertIn("set_velocity_8_8", commands)
        self.assertIn("or_object_field", commands)
        self.assertIn("and_object_field", commands)
        velocity = next(
            x for x in got["commands"]
            if x.get("meaning") == "set_velocity_8_8"
        )
        self.assertEqual(velocity["x_velocity_raw"], "0x0000")
        self.assertEqual(velocity["y_velocity_raw"], "0x0200")

    def test_command3_state_transition(self):
        rom = self.make_rom()
        self.put_cpu(rom, 0x0C, 0x9300, bytes([
            0x30,0x0E,0xC3,0xAC, 0xFF,0x03,0x03
        ]))
        got = m.parse_state_script(bytes(rom),0x0C,0x9300,0)
        self.assertEqual(got["frame_indices"], [0x0E])
        self.assertEqual(got["commands"][-1]["target_state"], 3)
        self.assertIsNone(got["unresolved"])

    def test_command1_call_then_continue(self):
        rom = self.make_rom()
        self.put_cpu(rom, 0x0C, 0x9500, bytes([
            0xFF,0x01,0x47,0xAA,
            0x40,0x01,0x2F,0x03,
            0xFF,0x00
        ]))
        got = m.parse_state_script(bytes(rom),0x0C,0x9500,0)
        self.assertEqual(got["frame_indices"], [0x01])
        self.assertEqual(got["commands"][0]["meaning"], "call_routine")
        self.assertIsNone(got["unresolved"])

    def test_commands_0e_0f_loop_counter(self):
        rom = self.make_rom()
        self.put_cpu(rom, 0x0C, 0x9600, bytes([
            0xFF,0x0E,0x02,
            0x02,0x01,0x2F,0x03,
            0xFF,0x0F,0x03,0x96,
            0x02,0x02,0x2F,0x03,
            0xFF,0x00
        ]))
        got = m.parse_state_script(bytes(rom),0x0C,0x9600,0)
        self.assertEqual(got["frame_indices"], [0x01,0x02])
        self.assertIsNone(got["unresolved"])

    def test_unknown_control_stops(self):
        rom = self.make_rom()
        self.put_cpu(rom, 0x0C, 0x9400, bytes([0xFF,0x05,0x99,0x88]))
        got = m.parse_state_script(bytes(rom),0x0C,0x9400,0)
        self.assertIsNotNone(got["unresolved"])
        self.assertEqual(got["unresolved"]["command"], "0x05")


if __name__ == "__main__":
    unittest.main(verbosity=2)

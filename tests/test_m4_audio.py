"""Focused M4 driver contracts; private-ROM tests skip if input is absent."""
import json
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import m4_audio as M
import audio1_psg_trace as T


class Evidence(unittest.TestCase):
    def test_finite_title_is_not_silent_recurrence_loop(self):
        x=json.loads((ROOT/'data/m4/driver-evidence.json').read_text())['music']['99']
        self.assertEqual(x['first_all_music_inactive'],1189)
        self.assertEqual(x['last_tick_with_non_off_register'],1182)
        self.assertEqual(x['recurrence']['writes_per_period'],0)

    def test_opening_adapter_matches_accepted_exit(self):
        x=json.loads((ROOT/'data/m4/opening-evidence.json').read_text())
        for row in x['rows']:
            self.assertEqual(row['title_handoff_tick']-row['post_entry_tick'],40)
            self.assertEqual(row['title_handoff_tick']-row['proposed_audio_fade_tick'],33)


@unittest.skipUnless(os.environ.get('SONIC_CHAOS_ROM'),'requires private ROM')
class Driver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=T.load_rom(os.environ['SONIC_CHAOS_ROM'])

    def test_numeric_evidence_reproduces(self):
        self.assertEqual(M.evidence(self.rom),json.loads((ROOT/'data/m4/driver-evidence.json').read_text()))

    def test_deterministic_capture(self):
        a=M.capture(self.rom,0x99,1300)[1]
        self.assertEqual(a,M.capture(self.rom,0x99,1300)[1])

    def test_priority_low_equal_high(self):
        for current,accepted in ((0x37,True),(0x38,True),(0x39,False)):
            d=T.Driver(self.rom);d.mem[0xDE0F]=current;d.request(0xBF);d.call(0x407F)
            self.assertEqual(d.mem[0xDE03]==0xBF,accepted)

    def test_zero_and_f8(self):
        d=T.Driver(self.rom);d.request(0x81);d.tick()
        before=bytes(d.mem[0xDE40:0xDF90]);d.request(0);d.call(0x407F);d.call(0x4119)
        self.assertEqual(bytes(d.mem[0xDE40:0xDF90]),before)
        d.request(0xF8);d.tick()
        self.assertEqual(d.active(),[]);self.assertEqual(d.psg.att,[15]*4)

    def test_repeated_equal_sfx_replaces_and_extends_steal(self):
        for second in (0xBF,0xA6):
            d=T.Driver(self.rom);d.request(0x81)
            end=105+(20 if second==0xBF else 40)
            for tick in range(1,end+1):
                if tick==100:d.request(0xBF)
                if tick==105:d.request(second)
                d.tick()
                if 105<=tick<end:
                    self.assertTrue(d.mem[0xDF30]&128)
                    self.assertTrue(d.mem[0xDEA0]&4)
            self.assertFalse(d.mem[0xDF30]&128)
            self.assertTrue(d.mem[0xDEA0]&16)

    def test_music_request_cancels_sfx(self):
        d=T.Driver(self.rom);d.request(0xBF);d.tick();self.assertTrue(d.active(T.SFX_CH))
        d.request(0x99);d.tick();self.assertFalse(d.active(T.SFX_CH))

    def test_pause_freezes_channels_and_resume_runs(self):
        d=T.Driver(self.rom);d.request(0x81)
        for _ in range(40):d.tick()
        d.mem[0xDE08]=0x80;d.tick();frozen=bytes(d.mem[0xDE40:0xDF90])
        for _ in range(20):d.tick();self.assertEqual(bytes(d.mem[0xDE40:0xDF90]),frozen)
        self.assertEqual(d.psg.att,[15]*4)
        d.mem[0xDE08]=0
        for _ in range(3):d.tick()
        self.assertNotEqual(bytes(d.mem[0xDE40:0xDF90]),frozen)


if __name__=='__main__':unittest.main()

"""ROM-driven strip behavior, including state-conditioned stopping."""
import json
import os
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import gpz_surface19 as S
import level_package as L

class StripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))
        if not path.is_file():raise unittest.SkipTest('local canonical ROM unavailable')
        cls.rom=L.load_rom(path)
        cls.value=S.build(cls.rom)

    def test_regenerated_cache(self):
        self.assertEqual(S.dumps(self.value),S.OUTPUT.read_text())

    def test_stop_falls_and_fast_supports(self):
        f=self.value['fixtures']
        for name in ('slow','stopped_walk'):
            self.assertEqual(f[name][1]['requested'],0x14)
            self.assertEqual(f[name][1]['vy'],256)
            self.assertFalse(f[name][1]['floor'])
            self.assertGreater(f[name][-1]['y'],718)
        for name in ('fast_right','fast_left','stopped_idle'):
            self.assertTrue(all(r['y']==686 and r['floor'] for r in f[name]))

    def test_release_and_reentry(self):
        f=self.value['fixtures']
        self.assertEqual([r['requested'] for r in f['decelerate'][:3]],[6,5,0x14])
        self.assertTrue(all(r['requested']==6 and r['y']==686 and r['floor'] for r in f['exit_and_reenter'][-8:]))
        self.assertTrue(all(r['plane']==0 for rows in f.values() for r in rows))

    def test_bit0_reset_and_counter_consumers(self):
        lab=S.Lab(self.rom)
        o,m=lab.o,lab.m;m[0xD524]=3;m[0xD3BC]=17
        m[0xD501]=0x18 # isolated no-surface branch returns before ordinary falling setter
        o.call(0x6C45)
        self.assertEqual(m[0xD524]&3,0)
        self.assertEqual(m[0xD3BC],17)
        for address in (0x45ED,0x463C,0x4663):
            lab=S.Lab(self.rom);o,m=lab.o,lab.m
            m[0xD524]=1;m[0xD3BC]=17;o.call(address)
            self.assertEqual(m[0xD3BC],0)
            self.assertEqual(m[0xD524]&1,1 if address==0x4663 else 0)

    def test_floor_matrix_size_and_speed_boundaries(self):
        self.assertEqual(len(self.value['support_matrix']),96)
        self.assertEqual(sum(r['cases'] for r in self.value['speed_sweep']['walk']),12291)
        self.assertEqual(self.value['speed_sweep']['run']['cases'],2561)

if __name__=='__main__':unittest.main()

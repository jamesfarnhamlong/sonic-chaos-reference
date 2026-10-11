"""AUDIO-0 original-routine and evidence-boundary regressions."""
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import audio_requests as A
import rom as R
ROM=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))

class AudioRequests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=R.load(ROM)
        cls.d=A.extract(cls.rom)
        cls.by_id={e['request_id']:e for e in cls.d['requests']}

    def test_reproducible_ledger(self):
        self.assertEqual(A.OUT.read_text(),json.dumps(self.d,indent=2)+'\n')
        self.assertEqual(A.extract(self.rom),self.d)

    def test_original_dispatch_and_request_evidence(self):
        self.assertEqual(self.d['summary']['categories'],dict(control=2,music=31,sfx=37))
        self.assertEqual(self.d['summary']['unique_ids'],70)
        self.assertEqual(self.d['unreviewed_store_candidates'],[])
        for e in self.by_id.values():
            for s in e['call_sites']:
                p=s['rom_offset']
                if s['kind']=='direct':
                    self.assertEqual(self.rom[p-2:p],bytes((0x3E,e['request_id'])))
                    self.assertEqual(self.rom[p:p+3],bytes((0x32,4,0xDE)))
                if s['kind']=='script_command_06':
                    self.assertEqual(self.rom[p:p+3],bytes((255,6,e['request_id'])))
                    self.assertEqual(R.u16(self.rom,s['state_pointer_rom']),s['script_start_cpu'])

    def test_zero_is_not_silence(self):
        self.assertEqual(self.d['controlled_results']['zero'],dict(selected=0x80,channel_state_unchanged=True))
        self.assertTrue(self.d['controlled_results']['f8_all_channels_inactive'])

    def test_equal_priority_restarts_and_lower_priority_drops(self):
        rows=self.d['controlled_results']['ring_priority']
        self.assertEqual([x['selected_request'] for x in rows],[0xBF,0xBF,0x80])
        self.assertTrue(all(x['pending']==0 for x in rows))
        self.assertTrue(all(x['initialized_stream_headers_repeated'] for x in self.d['controlled_results']['repeated_requests']))

    def test_silent_sneakers_counterfactual(self):
        normal,sneakers=self.d['controlled_results']['invincibility_then_sneakers']
        self.assertEqual(normal['requests'],[dict(update=600,request_id=0x81)])
        self.assertTrue(normal['final_music_active'])
        self.assertEqual(sneakers['requests'],[])
        self.assertEqual(sneakers['timer_first_zero_at'],1000)
        self.assertEqual(sneakers['timer_first_underflow_at'],1001)
        self.assertEqual(sneakers['final_selector'],3)
        self.assertIsNotNone(sneakers['music_first_inactive_update'])
        self.assertFalse(sneakers['final_music_active'])

    def test_special_stages_and_clear_selection(self):
        sites=self.by_id[0x8F]['call_sites']
        self.assertEqual({(s['zone'],s['act']) for s in sites if s['kind']=='zone_act_table' and s['zone']>=8},
                         {(z,a) for z in range(8,13) for a in range(3)})
        self.assertTrue(any(s['rom_offset']==0x4B0B for s in self.by_id[0xF8]['call_sites']))
        self.assertTrue(any(s['rom_offset']==0x7640 for s in self.by_id[0xBF]['call_sites']))
        self.assertTrue(any(s['rom_offset']==0x48A3 for s in self.by_id[0x97]['call_sites']))
        self.assertTrue(any(s['rom_offset']==0x4790 and 'zone8' in s['trigger'] for s in self.by_id[0x85]['call_sites']))

    def test_no_names_from_pointer_proximity(self):
        for rid in (0x8E,0x99,0x9B,0xA8,0xB2,0xC1):
            self.assertIsNone(self.by_id[rid]['friendly_name'])
        self.assertEqual(self.d['summary']['ids_without_verified_call_sites'],
                         ['0x8E','0x9B','0x9C','0x9D','0x9E','0x9F','0xA8','0xB2','0xC1'])

    def test_version_guard_and_curated_site_fail_closed(self):
        with patch.object(Path,'read_bytes',return_value=bytes(524288)):
            with self.assertRaises(ValueError):R.load('invalid.sms')
        r=bytearray(self.rom);r[0x4790]=0
        with self.assertRaisesRegex(ValueError,'curated immediate store'):A.extract(r)

if __name__=='__main__':unittest.main()

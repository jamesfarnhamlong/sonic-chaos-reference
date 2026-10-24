"""P0R exact emission regressions and retained incorrect-model negative controls."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import audio1_psg_trace as T
from m5p0r_emission import Registers,EmissionModel
from m5p0r_proof import CASES,compare,OUT,PUBLIC,PRIOR

def evidence(name):return json.loads((PUBLIC/name).read_text())

class RegisterProtocol(unittest.TestCase):
    def test_no_write_holds_register_and_explicit_off_changes_it(self):
        r=Registers();r.write(0xE5);r.write(0xF2)
        before=r.snapshot()
        for _ in range(104):self.assertEqual(r.snapshot(),before)
        r.write(0xFF);self.assertEqual(r.attenuation[3],15)

    def test_zero_restore_is_data_to_last_latch(self):
        r=Registers();r.write(0xB4);r.write(0)
        self.assertEqual(r.attenuation[1],0)
        r.write(0xB4);r.write(0xE4)
        self.assertEqual(r.attenuation[1],4);self.assertEqual(r.noise,4)

    def test_frequency_data_and_attenuation_data_remain_distinct(self):
        r=Registers();r.write(0xC1);r.write(0x12)
        self.assertEqual(r.tone[2],0x121)
        r.write(0xD5);r.write(2)
        self.assertEqual(r.attenuation[2],2);self.assertEqual(r.tone[2],0x121)

class SafeEvidence(unittest.TestCase):
    def test_exact_focused_gate_and_reused_regressions(self):
        x=evidence('emission-results.json')
        self.assertEqual(x['status'],'PASS');self.assertEqual(x['focused_original_cases'],12)
        self.assertEqual(sum(c['ticks'] for c in x['cases'].values()),2329)
        self.assertTrue(all(c['failures']==[] for c in x['cases'].values()))
        self.assertEqual(x['cached_ownership_cases'],1480);self.assertEqual(x['cached_ownership_failures'],[])
        self.assertEqual(x['new_full_matrix_pair_captures'],0)
        self.assertEqual((x['recovery_cases'],x['recovery_facts'],x['recovery_matches']),(111,159,159))

    def test_b6_and_ba_before_after_not_tolerance_changes(self):
        x=evidence('boundary-closure.json')
        self.assertEqual((x['B6']['prior_dry_projection_tick45'],x['B6']['original_tick45_attenuation'],x['B6']['corrected_tick45_attenuation']),(0,4,4))
        self.assertEqual(x['B6']['authentic_solo_tick16_attenuation'],0)
        self.assertEqual(x['B6']['corrected_solo_tick16_attenuation'],0)
        self.assertEqual((x['BA']['prior_static_stem_attenuation'],x['BA']['original_tick34_attenuation'],x['BA']['corrected_tick34_attenuation']),(0,15,15))

    def test_unchanged_static_stem_is_insufficient(self):
        x=evidence('composition-feasibility.json')
        self.assertEqual(x['static_B8_zero_source_ticks_during_required_hold'],list(range(159,167)))
        self.assertEqual(x['carrier_experiment']['held_ticks_restored'],104)
        self.assertFalse(x['carrier_experiment']['production_approved'])
        self.assertFalse(x['carrier_experiment']['matched_entry']['sample_equal'])
        self.assertLessEqual(x['carrier_experiment']['matched_entry']['max_error_outside_first_sample_of_tick_lsb'],2)

    def test_ba_large_error_is_not_waived_as_phase(self):
        x=evidence('composition-feasibility.json')
        self.assertEqual(x['BA_energy']['tick'],34)
        self.assertEqual(x['BA_energy']['reference_voice_rms_lsb'][1],0)
        self.assertGreater(x['BA_energy']['composed_voice_rms_lsb'][1],8000)
        self.assertLess(x['BA_context']['after']['max_tick_rms_error_percent_peak'],4.1)
        self.assertLess(abs(x['BA_context']['after_energy']['residual_energy_accounting_lsb2']),3)
        self.assertEqual(x['A3_constant_DC_qualification'],'unchanged; original first735 samples constant -4096, AC RMS0')

@unittest.skipUnless(os.environ.get('SONIC_CHAOS_ROM') and (OUT/'dry-emission-bank.json').exists(),'requires private authenticated ROM and dry intent bank')
class OriginalDriver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=T.load_rom(os.environ['SONIC_CHAOS_ROM']);cls.bank=json.loads((OUT/'dry-emission-bank.json').read_text())

    def test_all_required_controls_exact_bytes_all_registers_including_muted(self):
        for name,events in CASES.items():
            result=compare(self.rom,self.bank,events)
            self.assertEqual(result['failures'],[],name)

    def test_held_output_contract_rejects_known_incorrect_selector(self):
        from m5p0_model import Model
        from m5p1_proof import select_voice
        legacy_bank=json.loads((PRIOR/'dry-event-bank.json').read_text())
        old=Model(legacy_bank);old.direct(0x81);new=EmissionModel(self.bank);new.direct(0x81)
        for tick in range(1,169):
            for kind,rid in CASES['B8-BC'].get(tick,[]):old.direct(rid);new.direct(rid)
            old.tick();new.tick()
            if 63<=tick<=166:
                self.assertIsNone(select_voice(old,3))
                self.assertEqual(new.psg.noise,5);self.assertEqual(new.psg.attenuation[3],2)
                self.assertTrue(new.channels[6].waiting)
            if tick==167:
                self.assertTrue(new.channels[6].flags&128);self.assertEqual(new.psg.attenuation[3],15)
            if tick==168:self.assertFalse(new.channels[6].flags&128)

    def test_same_b6_original_solo_quirk_and_correct_music_context(self):
        a=compare(self.rom,self.bank,{},ticks=70,music=0xB6)
        b=compare(self.rom,self.bank,CASES['B6-A0'])
        self.assertEqual(a['failures'],[]);self.assertEqual(b['failures'],[])
        self.assertEqual(compare(self.rom,self.bank,{6:[('request',0xBC)]},ticks=159,music=0xB8)['failures'],[])
        # A stateless dry readback must fail the in-music contract, not be waived.
        old=json.loads((PRIOR/'package/library/B6/private-registers.json').read_text())['states'][15][2][1]
        expected=evidence('boundary-closure.json')['B6']['original_tick45_attenuation']
        with self.assertRaises(AssertionError):self.assertEqual(old,expected)

    def test_ba_false_audible_guard_includes_original_off_states(self):
        m=EmissionModel(self.bank);m.direct(0x81)
        for tick in range(1,35):
            for kind,rid in CASES['BA-partial'].get(tick,[]):m.direct(rid)
            m.tick()
        self.assertEqual(m.psg.attenuation[1],15)
        old=json.loads((PRIOR/'package/library/BA/private-registers.json').read_text())['states'][4][2][1]
        with self.assertRaises(AssertionError):self.assertEqual(old,m.psg.attenuation[1])

    def test_parent_archive_and_m4_untouched(self):
        p=PRIOR/'SonicChaos_M5_P0P1_20261024_PROOF_PRIVATE.zip'
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),'3adf174848e83fc40644a7e12142dbd44062c25c5dff674d09df031fe4b9881f')
        old=json.loads((PRIOR/'package/M4-preservation.json').read_text())['sha256']
        self.assertEqual(len(old),47)
        self.assertTrue(all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in old.items()))

if __name__=='__main__':unittest.main()

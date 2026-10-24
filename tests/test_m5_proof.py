"""P0/P1 proof regressions. Passing tests preserve explicit composition FAILs."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import audio1_psg_trace as T
from m5p0_model import Model
import m5p0_proof as P0

def evidence(name):return json.loads((ROOT/'data/m5-proof'/name).read_text())

class NumericProof(unittest.TestCase):
    def test_complete_bounded_ownership_coverage(self):
        x=evidence('p0-result.json')
        self.assertEqual(x['scenarios'],1480)
        self.assertEqual(x['arbitration_assertions'],4864)
        self.assertEqual(x['recovery_matches'],159)
        self.assertEqual(x['recovery_assertions'],159)
        self.assertEqual(x['recovery_cases'],111)
        self.assertEqual(x['m4_interruption_controls'],192)
        self.assertEqual(x['m4_loop_controls'],4)
        self.assertEqual(x['failures'],[])

    def test_solo_render_results_preserve_failed_duration_gate(self):
        x=evidence('p1-library.json')
        self.assertEqual(set(x),{'88','A0','A3','AC','B6','BA','BC','C0','B8'})
        for v in x.values():
            self.assertTrue(v['deterministic'])
            self.assertEqual(v['pitch']['windows_off_by_more_than_25_cents'],0)
            self.assertEqual(v['sanity']['clipped_frames'],0)
            self.assertEqual(v['experimental_four_voice_reconstruction_max_lsb'],0)
        self.assertEqual(x['A3']['envelope']['voice3']['mismatched_ticks'],1)
        self.assertEqual(x['BC']['mix_sha256'],x['C0']['mix_sha256'])
        self.assertNotEqual(x['BC']['header']['priority_byte'],x['C0']['header']['priority_byte'])

    def test_no_aggregate_pass_hides_fixed_rate_failure(self):
        x=evidence('coupled-noise.json')['fixed-B8-BC']
        self.assertLess(x['envelope_correlation'],.81)
        self.assertEqual(x['register_projection_mismatches']['audible_attenuation'][3],104)
        self.assertEqual(x['register_projection_mismatches']['audible_noise_controls'],104)
        self.assertFalse(x['sample_equal'])
        gate=evidence('gate.json')
        self.assertEqual(gate['overall'],'HOLD')
        self.assertEqual(gate['composition_parity'],'FAIL')

    def test_chunk_reconstruction_and_negative_controls(self):
        x=evidence('chunk-proof.json')
        self.assertEqual(x['reconstructed_exact'],[True]*4)
        self.assertEqual(x['sample_address_assertions'],4064)
        self.assertTrue(x['missing_rejected']);self.assertTrue(x['corrupt_rejected'])
        self.assertEqual(x['mono_chunk_max_bytes'],6021120)
        self.assertEqual(x['native_cache_performance'],'NOT TESTED')

    def test_production_budget_and_m4_preservation(self):
        x=evidence('measured-budget.json')
        self.assertLess(x['scratch_bytes'],2*1024**3)
        self.assertLess(x['archive_bytes'],512*1024**2)
        self.assertTrue(x['m4_all_preserved']);self.assertEqual(x['m4_preserved_files'],47)
        self.assertTrue(all(c['fresh_process'] for c in x['render_calls']))

class ChunkNegatives(unittest.TestCase):
    def test_manifest_chunk_corruption_and_missing(self):
        from m5p1_proof import ChunkReader,sha
        P0.PRIVATE.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=P0.PRIVATE) as temp:
            folder=Path(temp);data=(5).to_bytes(2,'little')*16
            entry=dict(file='sentinel.pcm',first_sample=0,samples=16,bytes=32,sha256=sha(data))
            manifest=dict(rate=44100,bits=16,channels=1,chunk_ticks=4096,voices=[dict(samples=16,chunks=[entry])])
            raw=json.dumps(manifest).encode();(folder/'manifest.json').write_bytes(raw);(folder/'sentinel.pcm').write_bytes(data)
            trusted=sha(raw)
            self.assertEqual(ChunkReader(folder,trusted).sample(0,15),5)
            with self.assertRaises(ValueError):ChunkReader(folder,'0'*64)
            (folder/'sentinel.pcm').write_bytes(b'xx'+data[2:])
            with self.assertRaises(ValueError):ChunkReader(folder,trusted).load(0,0)
            (folder/'sentinel.pcm').unlink()
            with self.assertRaises(ValueError):ChunkReader(folder,trusted).load(0,0)

    def test_manifest_address_and_path_validation(self):
        from m5p1_proof import ChunkReader,sha
        with tempfile.TemporaryDirectory(dir=P0.PRIVATE) as temp:
            folder=Path(temp)
            for entry in (dict(file='../outside.pcm',first_sample=0,samples=1,bytes=2,sha256='0'*64),
                          dict(file='safe.pcm',first_sample=1,samples=1,bytes=2,sha256='0'*64)):
                raw=json.dumps(dict(rate=44100,bits=16,channels=1,chunk_ticks=4096,voices=[dict(samples=1,chunks=[entry])])).encode()
                (folder/'manifest.json').write_bytes(raw)
                with self.assertRaises(ValueError):ChunkReader(folder,sha(raw))

    @unittest.skipUnless((P0.PRIVATE/'package/chunks-82/manifest.json').exists(),'requires private chunk proof')
    def test_real_chunk_boundaries_and_loops(self):
        from m5p1_proof import ChunkReader,sha
        folder=P0.PRIVATE/'package/chunks-82';r=ChunkReader(folder,sha((folder/'manifest.json').read_bytes()))
        cut=1879*735;period=6912*735
        for c in range(4):
            for pos in (cut,4096*735-1,4096*735,8192*735,cut+period,cut+period+1):
                mapped=cut+(pos-cut)%period if pos>=cut else pos
                self.assertEqual(r.sample(c,pos,cut,period),r.sample(c,mapped))

@unittest.skipUnless(os.environ.get('SONIC_CHAOS_ROM'),'requires authenticated private ROM')
class OriginalDriver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=T.load_rom(os.environ['SONIC_CHAOS_ROM'])
        cls.bank=json.loads((P0.PRIVATE/'dry-event-bank.json').read_text()) if (P0.PRIVATE/'dry-event-bank.json').exists() else P0.bank(cls.rom)
        assert cls.bank['rom_sha256']==T.ROM_SHA256

    def test_all_recorded_pair_restart_music_reset_cases(self):
        old=json.loads((ROOT/'data/m5/interactions.json').read_text())
        for name,x in old['scenarios'].items():
            self.assertEqual(P0.model_timeline(self.bank,{int(k):v for k,v in x['events'].items()},x['ticks']),x['transitions'],name)

    def test_authentic_irq_transfer_direct_and_deferred_zero(self):
        for direct,deferred,expected in ((0xA0,0,0xA0),(0xA0,0xBF,0xBF),(0,0xA0,0xA0),(0,0,0)):
            d=T.Driver(self.rom);d.request(direct);d.mem[0xD4A4]=deferred
            m=Model(self.bank);m.direct(direct);m.game(deferred)
            P0.original_transfer(d);m.transfer()
            self.assertEqual(d.mem[0xDE04],expected);self.assertEqual(m.mail[0],expected)
            self.assertEqual(d.mem[0xD4A4],0)

    def test_write_inhibit_does_not_silence_held_noise(self):
        d=T.Driver(self.rom);d.request(0x81);m=Model(self.bank);m.direct(0x81)
        for tick in range(1,169):
            if tick==30:d.request(0xB8);m.direct(0xB8)
            if tick==35:d.request(0xBC);m.direct(0xBC)
            d.tick();m.tick()
            self.assertEqual(m.snapshot()['flags'],[d.mem[a]&0xC4 for a in T.CHANNELS])
            if 63<=tick<=166:
                self.assertTrue(m.channels[6].waiting)
                self.assertTrue(d.mem[0xDF60]&16)
                self.assertEqual(d.psg.att[3],2)  # hardware register stays audible
                self.assertEqual(d.psg.noise,5)
        self.assertEqual(d.psg.att[3],15)

    def test_f8_and_terminal_fade_order(self):
        for priority,admitted in ((0x57,True),(0x58,False),(0x78,False)):
            d=T.Driver(self.rom);d.mem[0xDE0F]=priority;d.request(0xF8);d.call(0x407F)
            m=Model(self.bank);m.priority=priority;m.direct(0xF8);m.arbitration()
            self.assertEqual(d.mem[0xDE03]==0xF8,admitted)
            self.assertEqual(m.selected==0xF8,admitted)
        x=P0.compare_case(self.rom,self.bank,0x81,{35:[('fade',(12,1,2))],57:[('request',0x99)]},80)
        self.assertEqual(x['failures'],[])
        x=P0.compare_case(self.rom,self.bank,0x81,{30:[('pause',1)],35:[('stop',0)]},80)
        self.assertEqual(x['failures'],[])

    def test_three_slots_and_fixed_rate_diagnostic(self):
        for ev in ({30:[('request',0xAC)],35:[('request',0xA0)],79:[('request',0xA6)]},
                   {30:[('request',0xB8)],35:[('request',0xBC)]}):
            self.assertEqual(P0.compare_case(self.rom,self.bank,0x81,ev,210)['failures'],[])

if __name__=='__main__':unittest.main()

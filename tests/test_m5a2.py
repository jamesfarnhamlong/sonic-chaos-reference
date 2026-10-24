"""SCSP hostile-input controls and bounded original-driver proof contracts."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from bank import MAGIC, canonical, pack, records, unpack
from decoder import DecodeError, Decoder


def synthetic(stream=(0x81,2,0xF2,0)):
    data = {'17464':0x34,'17465':2}
    data.update({str(0x5200+i):v for i,v in enumerate(stream)})
    return dict(version=1,horizon=20,
        source_sha256='eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607',
        priority={'0':0,'129':128,'248':0x57},
        programs={'129':dict(multiplier=1,tempo=0,source_offset=0x9000,header_length=10,
             header_sha256='0'*64,streams=[dict(latch=0x80,pointer=0x5200,transpose=0,volume=0,flags=128)])},
        data=data)


def encode_metadata(meta):
    raw=canonical(meta)
    return MAGIC+struct.pack('<I',len(raw))+zlib.compress(raw)+hashlib.sha256(raw).digest()


class HostileData(unittest.TestCase):
    def start(self,stream):
        m=Decoder(unpack(pack(synthetic(stream))))
        m.direct(0x81)
        return m

    def test_compact_round_trip(self):
        self.assertEqual(unpack(pack(synthetic())),synthetic())

    def test_truncated_and_wrong_data_rejected(self):
        blob=pack(synthetic())
        for data in (blob[:-1],b'WRONG'+blob[5:],blob[:18]+bytes([blob[18]^1])+blob[19:]):
            with self.assertRaises(DecodeError): unpack(data)

    def test_source_version_and_record_hash_validation(self):
        for key,value in [('version',2),('source_sha256','0'*64)]:
            b=synthetic();b[key]=value
            with self.assertRaises(DecodeError): unpack(pack(b))
        meta=records(synthetic());meta['segments'][0]['sha256']='0'*64
        with self.assertRaises(DecodeError): unpack(encode_metadata(meta))

    def test_lengths_and_pointer_validation(self):
        b=synthetic();b['programs']['129']['streams'][0]['pointer']=0x5300
        with self.assertRaises(DecodeError): unpack(pack(b))
        meta=records(synthetic());meta['segments'][0]['length']+=1
        with self.assertRaises(DecodeError): unpack(encode_metadata(meta))

    def test_expansion_size_bound(self):
        blob=MAGIC+struct.pack('<I',2**30)+zlib.compress(b'{}')+bytes(32)
        with self.assertRaises(DecodeError): unpack(blob)

    def test_unknown_or_unverified_opcodes_fail(self):
        for opcode in (0xE1,0xE3,0xEF,0xFF):
            m=self.start((opcode,0))
            with self.assertRaises(DecodeError):m.tick()

    def test_truncated_opcode_operand_fails(self):
        m=self.start((0xE0,1,2))
        with self.assertRaises(DecodeError):m.tick()

    def test_pointer_escape_fails(self):
        m=self.start((0xF6,0,0))
        with self.assertRaises(DecodeError):m.tick()

    def test_instant_infinite_loop_fails(self):
        m=self.start((0xF6,0,0x52))
        with self.assertRaisesRegex(DecodeError,'budget'):m.tick()

    def test_stack_and_loop_index_bounds(self):
        for stream in ((0xF9,0),(0xF8,0,0x52),(0xF7,3,1,0,0x52)):
            m=self.start(stream)
            with self.assertRaises(DecodeError):m.tick()

    def test_unknown_request_is_not_silence(self):
        m=Decoder(synthetic())
        with self.assertRaises(DecodeError):m.direct(0x90)

    def test_unsupported_horizon_fails(self):
        with self.assertRaises(DecodeError):Decoder(synthetic(),21)
        m=Decoder(synthetic(),1);m.direct(0x81);m.tick()
        with self.assertRaises(DecodeError):m.tick()

    def test_finite_termination_and_missing_termination(self):
        m=self.start((0x81,2,0xF2,0))
        m.tick();self.assertTrue(m.ch[0][0]&128)
        m.tick();m.tick();self.assertFalse(m.ch[0][0]&128)
        m=self.start((0x81,2,1))
        with self.assertRaises(DecodeError):
            for _ in range(6):m.tick()


class MeasuredEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate=json.loads((ROOT/'data/m5-a2/emission.json').read_text())

    def test_every_tick_byte_and_state_exact(self):
        for name,digest in self.gate['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/'tools/m5a2'/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),digest)
        self.assertEqual(len(self.gate['cases']),20)
        for case in self.gate['cases'].values():
            self.assertEqual(case['status'],'PASS')
            self.assertEqual(case['ticks'],case['compared_ticks'])
            self.assertEqual(case['failures'],[])

    def test_new_pcm_measurements_retained(self):
        pcm=json.loads((ROOT/'data/m5-a2/pcm.json').read_text())
        self.assertEqual(set(pcm['cases']),set(self.gate['cases']))
        for case in pcm['cases'].values():
            self.assertEqual(case['core_register_counter_lfsr_failures'],[])
            self.assertTrue(case['partition_invariant'])
            self.assertLessEqual(case['versus_original_MAME']['max_lsb'],5)
        self.assertGreater(max(c['versus_original_MAME']['max_lsb'] for c in pcm['cases'].values()),0)

    def test_catalogue_has_exact_original_70_ids(self):
        old=json.loads((ROOT/'data/m5/catalogue.json').read_text())['entries']
        new=json.loads((ROOT/'data/m5-a2/coverage.json').read_text())['entries']
        self.assertEqual([r['request_id'] for r in new],[r['request_id'] for r in old])

    def test_candidate_has_no_trace_or_rom_import(self):
        text=(ROOT/'tools/m5a2/decoder.py').read_text()
        for forbidden in ('import z80','audio1_psg_trace','dry-event-bank','dry-emission-bank'):
            self.assertNotIn(forbidden,text)

    def test_authenticated_loop_termination_recovery_and_negative_controls(self):
        f=json.loads((ROOT/'data/m5-a2/facts.json').read_text())
        self.assertEqual(f['loop']['period_ticks'],2688)
        self.assertTrue(f['loop']['original_state_repeated'])
        self.assertTrue(f['loop']['subsequent_emission_identical'])
        self.assertEqual(f['loop']['subsequent_continuation_ticks'],419)
        self.assertEqual(f['finite_inactive_ticks']['88'],212)
        self.assertEqual(f['finite_inactive_ticks']['99'],1189)
        self.assertEqual(f['physical_inhibited_noise_hold_ticks'],104)
        self.assertEqual(f['music_tone1_read_recovered_tick'],61)
        self.assertEqual(f['wrong_pitch_data_detected_tick'],1)
        self.assertEqual(f['missing_terminal_output_detected_tick'],135)

    def test_fresh_process_runtime_isolation(self):
        f=json.loads((ROOT/'data/m5-a2/isolation.json').read_text())
        self.assertTrue(f['fresh_process'])
        self.assertFalse(f['ROM_reopened'])
        self.assertTrue(f['PCM_file_identical'])


if __name__=='__main__':unittest.main()

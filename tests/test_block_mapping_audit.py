"""Non-bank-aligned pointer regression and exhaustive original-code checks."""
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import block_mapping_audit as A
import gpz_foundation as F
import level_package as L


class PointerRegression(unittest.TestCase):
    def test_non_aligned_table_is_not_pointer_base(self):
        r = bytearray(0x4C000)
        r[0x45640:0x45642] = (0xA360).to_bytes(2, 'little')
        r[0x46360:0x46380] = b'\xC0\x00' * 16
        r[0x479A0:0x479C0] = b'\xff' * 32
        m = L.block_mapping(r, 0x45640, 0)
        self.assertEqual((m['cpu'], m['rom'], m['attributes']),
                         (0xA360, 0x46360, [0xC0]*16))

    def test_invalid_cpu_pointer_is_rejected(self):
        r = bytearray(0x48000)
        with self.assertRaises(ValueError):
            L.block_mapping(r, 0x45640, 0)


class OriginalRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = Path(os.environ.get('SONIC_CHAOS_ROM', str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))
        if not p.is_file():
            raise unittest.SkipTest('canonical local ROM unavailable')
        cls.r = L.load_rom(p)
        cls.audit = A.build(cls.r)

    def test_both_original_consumers_all_18_acts_regenerate(self):
        self.assertEqual(A.dumps(self.audit), A.OUTPUT.read_text(encoding='utf-8'))
        self.assertEqual(sum(a['original_consumer_checks'] for a in self.audit['acts'].values()), 9216)

    def test_representative_pointer_and_pixel_fixtures(self):
        fixtures = self.audit['gpz_fixtures']
        self.assertEqual((fixtures['0x00']['cpu'], fixtures['0x00']['rom']), (0x9840, 0x45840))
        self.assertEqual((fixtures['0x3C']['cpu'], fixtures['0x3C']['rom'], fixtures['0x3C']['nonzero_pixels']),
                         (0x9F20, 0x45F20, 384))
        self.assertEqual((fixtures['0x8C']['cpu'], fixtures['0x8C']['rom'], fixtures['0x8C']['nonzero_pixels']),
                         (0xA360, 0x46360, 512))
        self.assertEqual(fixtures['0x3C']['palette_index_sha256'],
                         'aee96c13cb89abd37b74d8391f8664085015b521c642824bf83eecc7bc17e188')
        self.assertEqual(fixtures['0x8C']['palette_index_sha256'],
                         '39a8f04e764f53c8bff03ebfd881780ea39985b1871619bd76cc01c122a4bf26')
        for b in range(0x8C, 0x98):
            f = fixtures[L.hx(b, 2)]
            self.assertTrue(f['old_attributes_all_ffff'])
            self.assertGreater(f['nonzero_pixels'], 0)

    def test_all_289_exported_records_match_bank_memory(self):
        x = json.loads(F.OUTPUT.read_text(encoding='utf-8'))
        count = 0
        for a in x['acts'].values():
            for b in a['blocks']:
                m = b['mapping']
                cpu = L.u16(self.r, 0x45640 + 2*b['block_id'])
                off = 0x44000 + cpu - 0x8000
                self.assertEqual((m['cpu'], m['rom']), (cpu, off))
                self.assertEqual(b['mapping_sha256'], L.sha256(self.r[off:off+32]))
                self.assertEqual(m['attributes'], [L.u16(self.r, off+2*i) for i in range(16)])
                count += 1
        self.assertEqual(count, 289)


if __name__ == '__main__':
    unittest.main()

"""Special Stage foundation versus original ROM routines."""
import os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'tools'))
import ss_foundation as F
import level_package as L
from oracle import Oracle
ROM = Path(os.environ.get('SONIC_CHAOS_ROM', str(ROOT.parent / 'source/Sonic Chaos (Europe).sms')))


class Foundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = L.load_rom(ROM); cls.m, cls.c, cls.acts = F.build(cls.r)

    def test_regeneration(self):
        for n, v in [('implementation-manifest.json', self.m), ('object-census.json', self.c)]:
            self.assertEqual((F.OUT / n).read_text(encoding='utf-8'), F.dumps(v))

    def test_dimensions_starts_limits(self):
        want = {'ss1': ([512, 8], [111, 118], [0, 15], 16128, 16), 'ss2': ([24, 64], [111, 1838], [0, 1727], 512, 1808),
                'ss3': ([128, 24], [143, 622], [31, 526], 3840, 528), 'ss4': ([256, 16], [142, 366], [30, 254], 7936, 272),
                'ss5': ([48, 32], [143, 878], [31, 768], 1280, 784)}
        for k, (wh, start, cam, right, bottom) in want.items():
            a = self.m['stages'][k]; o = a['original_loaders']
            self.assertEqual(a['dimensions_cells'], wh)
            self.assertEqual([o['start']['0xd511'], o['start']['0xd514']], start)
            self.assertEqual([o['start']['0xd2d6'], o['start']['0xd2d8']], cam)
            self.assertEqual(o['header']['0xd282'], right); self.assertEqual(o['header']['0xd27e'], bottom)
            self.assertEqual(a['mapping_check']['mismatches'], 0)

    def test_census(self):
        self.assertEqual({k: v['type_counts'] for k, v in self.c['stages'].items()},
            {'ss1': {'0x10': 1, '0x31': 1}, 'ss2': {'0x10': 1, '0x2F': 7, '0x31': 1}, 'ss3': {'0x10': 7, '0x31': 1},
             'ss4': {'0x10': 6, '0x26': 5, '0x31': 1}, 'ss5': {'0x10': 3, '0x31': 1}})
        for k, bit in (('ss1', 1), ('ss2', 2), ('ss3', 4), ('ss4', 8), ('ss5', 16)):
            ring = [x for x in self.c['stages'][k]['records'] if x['type_id'] == '0x31']
            self.assertEqual(int(ring[0]['parameter'], 16), bit)

    def test_zone_selection_rule_original_routine(self):
        for mask in range(32):
            o = Oracle(self.r); o.mem[0xD297] = 3; o.mem[0xD2CC] = mask; o.call(0x187B)
            n = 0
            while n < 4 and mask >> n & 1: n += 1
            self.assertEqual(o.mem[0xD297], 8 + n); self.assertEqual(o.mem[0xD296], 3)

    def test_entry_gate_original_routine(self):
        for char in (1, 2):
            for zone in range(0, 9):
                for mask in (0, 0x0F, 0x1F, 0x20, 0x3F):
                    o = Oracle(self.r); o.mem[0xD2C8] = char; o.mem[0xD297] = zone; o.mem[0xD2CC] = mask; o.mem[0xD294] = 0
                    o.call(0x178F)
                    enter = char == 1 and zone < 6 and (mask & 0x1F) != 0x1F
                    self.assertEqual(o.mem[0xD294], 0x88 if enter else 0, (char, zone, mask))
                    self.assertEqual(o.mem[0xD2CD], 1 if enter else 0)


if __name__ == '__main__':
    unittest.main()

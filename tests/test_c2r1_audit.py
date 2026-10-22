"""ROM-free evidence consistency; no implementation-mirroring runtime tests."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class C2R1Evidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT/'data/c2r1/source-audit.json').read_text())
        cls.register = json.loads((ROOT/'data/c2r1/fidelity-register.json').read_text())['findings']

    def test_exact_authorised_parents(self):
        self.assertEqual(self.data['baseline'], 'd1ef8fc42571fb01829d370671a96287d9ae6d93')
        self.assertEqual(self.data['researchParent'], '637180aa3d658916b86af84b48b428ab2753f04a')

    def test_boundary_oracles_and_controls(self):
        cached=json.loads((ROOT/'data/rom-cache/collision-geometry.json').read_text())
        extents={r['state']:r['extents_x_y'] for r in cached['player_extents']['sonic_type_1']}
        self.assertEqual(extents[15], [[9,24]])
        gaps = []
        for row in self.data['rows']:
            if not row['id'].startswith('C2-EXT-'):
                self.assertEqual(row['actual'], row['oracle'])
                continue
            extent = extents[row['input']['state']][0][0]
            dx, dy = abs(row['input']['dx']), row['input']['dy']
            if row['id'] == 'C2-EXT-21':
                expected = 2 if dx <= extent + 11 else 0
            else:
                object_height = 16 if row['id'] == 'C2-EXT-28' else 24
                # Inclusive rectangles; equal penetrations choose vertical.
                top = dx <= extent + 16 and -object_height <= dy < 0 and extent+16-dx >= object_height+dy
                expected = bool(top) if row['id'] == 'C2-EXT-28' else int(top)
            self.assertEqual(row['oracle'], expected)
            self.assertEqual(row['status'], 'proven-match' if row['actual'] == expected else 'proven-gap')
            if row['status'] == 'proven-gap':
                gaps.append(row)
                self.assertEqual(row['input']['state'], 15)
        self.assertEqual(len(gaps), 12)
        self.assertEqual({r['width'] for r in gaps}, {256,348})

    def test_traces_do_not_claim_rom_or_windows(self):
        self.assertEqual(len(self.data['searches']),48)
        self.assertTrue(all(s['error'] is None and s['flips']==0 for s in self.data['searches']))
        self.assertEqual(len(self.data['coverage']),48)
        self.assertEqual(sum(bool(x.get('trace')) for x in self.data['coverage']),46)
        self.assertTrue(all(x['status'] in ('unresolved','not-audited') for x in self.data['coverage']))
        self.assertTrue(all(x.get('error') is None for x in self.data['coverage']))

    def test_register_completeness(self):
        self.assertEqual(len({x['id'] for x in self.register}),len(self.register))
        for x in self.register:
            for key in ['scope','canonical','poc_callsite','comparison','gameplay_impact','proposed_group','acceptance_or_remaining_limitation']:
                self.assertTrue(x[key])
            self.assertFalse(x['new_rom_execution'])
            self.assertFalse(x['windows_acceptance'])
        self.assertEqual({x['id'] for x in self.register if x['status']=='proven-gap'}, {'C2-EXT-21','C2-EXT-1B','C2-EXT-28'})

    def test_raw_gate_exceptions_preserved(self):
        gate=json.loads((ROOT/'data/c2r1/gate/results.json').read_text())
        self.assertEqual(sum(x['status']==0 for x in gate),8)
        self.assertEqual([x['test'] for x in gate if x['status']==1],['verify_aqz_p2_terrain_preservation.js'])
        self.assertEqual([x['test'] for x in gate if x['status'] is None],['verify_visual_p2_shards.js'])

if __name__ == '__main__':
    unittest.main()

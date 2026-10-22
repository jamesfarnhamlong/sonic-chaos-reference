"""Focused cached-evidence gates; no native/ROM execution claim.

Optional private-ROM regeneration is a separate m1_census --check command.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import m1_census as M

def validate(d):
    assert d['poc_commit'] == M.POC_SHA
    assert d['rom_sha256'] == M.O.ROM_SHA256
    frames = d['tails_mapping']['frames']
    assert len(frames) == 89 and frames['0']['piece_count'] == 0
    for k, f in frames.items():
        if k == '0':
            continue
        b = f['bounds']
        assert f['gamemaker_origin'] == [-b['min_x'], -b['min_y']]
        assert len(f['index_sha256']) == 64
        assert f['tile_source']['blocks_64_bytes'] * 2 == f['tile_source']['tiles']
    states = d['tails_states']
    assert set(states) == {f'{i:02X}' for i in range(0x36)}
    for state in states.values():
        assert len(state['ops']) < 80, 'script decoder safety cap reached'
        for op in state['ops']:
            if 'frame' in op:
                assert str(op['frame']) in frames
    return True

class M1Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads((ROOT / 'data/m1/tails-asset-census.json').read_text())

    def test_geometry_transfer_state_closure(self):
        self.assertTrue(validate(self.d))

    def test_wrong_origin_rejected(self):
        d = copy.deepcopy(self.d)
        d['tails_mapping']['frames']['18']['gamemaker_origin'][0] += 1
        with self.assertRaises(AssertionError):
            validate(d)

    def test_missing_animation_frame_rejected(self):
        d = copy.deepcopy(self.d)
        del d['tails_mapping']['frames']['18']
        with self.assertRaises(AssertionError):
            validate(d)

    def test_flight_and_continue_records(self):
        s = self.d['tails_states']
        self.assertEqual([(o['frame'], o['duration']) for o in s['18']['ops'] if 'frame' in o], [(18,4),(19,4),(20,4)])
        self.assertEqual([(o['frame'], o['duration']) for o in s['35']['ops'] if 'frame' in o], [(15,8),(16,8)])
        self.assertEqual(s['11']['script_cpu'], s['00']['script_cpu'])

    def test_choice_input_and_title_cues(self):
        code = {a:t for r in self.d['code_contracts'] for a,t in r['instructions']}
        self.assertEqual(code['0x3534'], 'BIT 5,A')
        self.assertEqual(code['0x356D'], 'BIT 2,A')
        self.assertEqual(code['0x3571'], 'BIT 3,A')
        self.assertEqual(code['0x0754'], 'LD A,0x99')
        self.assertEqual(code['0x30BA'], 'LD A,0x82')
        self.assertEqual(code['0x3F09'], 'JP nz,0x463c')
        self.assertEqual(code['0x4AE5'], 'RET nz')

    def test_resources_and_palettes(self):
        r = self.d['poc_resources']
        genuine = [x for x in r if x['resource'].startswith('SPR_chaos_')]
        self.assertEqual(len(genuine), 11)
        self.assertEqual(len(r)-len(genuine), 29)
        self.assertEqual(len(self.d['stage_palettes']), 18)
        self.assertEqual([p['sprite_record'] for p in self.d['stage_palettes'][::3]], [6,7,8,9,10,11])
        self.assertEqual([x['decoded_tiles'] for x in self.d['frontend_streams']], [297,153])

    def test_attract_table_order_and_region(self):
        a = self.d['attract']
        self.assertEqual(a['demo_length_updates'], 1080)
        self.assertEqual([(r['zone'],r['character']) for r in a['rows'][:3]], [(2,1),(0,1),(1,2)])
        self.assertEqual(len({r['input_pointer_D2E5'] for r in a['rows']}),6)

    def test_wrong_rom_fails_before_asset_access(self):
        with self.assertRaises(ValueError):
            M.build(b'wrong ROM', Path('does-not-exist'))

    def test_required_reports_and_no_asset_payloads(self):
        for f in ['m0-reconciliation-report.md','m1-tails-frontend-contract.md','m1-audio-readiness.md']:
            self.assertTrue((ROOT/'docs'/f).is_file())
        self.assertEqual(sorted(p.suffix for p in (ROOT/'data/m1').iterdir()), ['.json'])

if __name__ == '__main__':
    unittest.main()

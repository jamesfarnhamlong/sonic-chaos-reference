"""Regression locks for decoded GPZ gates and original Z80 route fixtures."""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import gpz_loop_route as G
from rom import load, SHA256

D = json.loads(G.OUTPUT.read_text())


class CachedRouteTests(unittest.TestCase):
    def test_four_layout_gates(self):
        self.assertEqual([(g['act'], g['gate_world']) for g in D['gates']],
                         [('gpz1',[2080,256]), ('gpz1',[2560,320]),
                          ('gpz2',[1888,224]), ('gpz3',[768,192])])
        self.assertEqual(D['rom_sha256'], SHA256)

    def test_trigger_matrix_no_speed_or_player_state_gate(self):
        self.assertEqual(len(D['contact_matrix']),576)
        for r in D['contact_matrix']:
            expected = r['state']
            if r['floor']:
                if r['current_block'] == 0x51:
                    if r['plane'] and r['previous_block']==0x52:
                        expected=0x0D
                elif r['current_block']==0x52 and not r['plane']:
                    if r['previous_block']==0x57:
                        expected=0x13
                    elif r['previous_block']==0x51:
                        expected=0x0C
            self.assertEqual(r['requested'], expected, r)
            self.assertEqual(r['return'], 0x100 if expected != r['state'] else 0x101)

    def test_shared_relative_path_and_ordinary_restoration(self):
        relative=[]
        for t in D['traversal_fixtures']:
            e=t['entry']; x,y=e['origin']
            self.assertEqual((e['current'],e['requested'],e['plane'],e['vx'],e['vy']),
                             (5,0x13,0,1024,1792))
            self.assertEqual((len(t['updates']),t['first_plane1_update']),(117,47))
            for r in t['updates']:
                self.assertEqual(r['current'],0x13)
                self.assertNotIn(0x690B,r['routine_calls'])
                self.assertNotIn(0x7666,r['routine_calls'])
                self.assertEqual(r['plane'],int(r['progress_16_8']>>8 >= 144))
            final=t['updates'][-1]
            self.assertEqual((final['requested'],final['vx'],final['vy'],final['plane'],
                              final['flags'],final['floor']), (0x0A,0,1024,1,3,False))
            ordinary=t['ordinary_update_after_exit']
            self.assertEqual((ordinary['current'],ordinary['plane']),(0x0A,1))
            self.assertIn(0x690B,ordinary['routine_calls'])
            self.assertIn(0x7666,ordinary['routine_calls'])
            relative.append([(r['x']-x,r['y']-y,r['vx'],r['progress_16_8'])
                             for r in t['updates']])
        self.assertTrue(all(r==relative[0] for r in relative))

    def test_slow_bailout_and_input_independence(self):
        controls=D['control_fixtures']
        for t in controls[:3]:
            r=t['updates'][-1]
            self.assertEqual((r['requested'],r['vy'],r['flags'],r['floor']),
                             (0x1D,128,1,False))
            self.assertIn(0x4680,r['routine_calls'])
        self.assertEqual(controls[3]['input']['vx'],854)
        self.assertEqual(controls[3]['updates'][-1]['requested'],0x0A)
        baseline=D['traversal_fixtures'][-1]['updates']
        for t in controls[4:7]+controls[8:]:
            self.assertEqual(t['updates'],baseline)
        for r in controls[7]['updates']:
            self.assertTrue(r['flags']&2)

    def test_progress_plane_and_exit_boundaries(self):
        for r in D['progress_boundary_fixtures']:
            p=r['progress_before_16_8']+r['vx_before']
            a=r['after']
            self.assertEqual(a['progress_16_8'],p)
            self.assertEqual(a['plane'],int(p>>8>=144))
            expected=0x0A if p>>8>=416 else (0x1D if p>>8<144 and r['vx_before']<10 else 0x13)
            self.assertEqual(a['requested'],expected)


class OriginalRoutineTests(unittest.TestCase):
    def test_cache_reproduced_by_verified_rom(self):
        candidates=[Path(os.environ.get('SONIC_CHAOS_ROM','missing.sms')),
                    ROOT.parent/'source/Sonic Chaos (Europe).sms']
        p=next((p for p in candidates if p.is_file()),None)
        if p is None:
            self.skipTest('canonical local ROM required')
        self.assertEqual(G.build(load(p)),D)


if __name__ == '__main__':
    unittest.main()

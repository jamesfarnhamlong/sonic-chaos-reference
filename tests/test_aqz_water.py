"""AQZ A2 original-routine, scheduling, restore and source regression locks."""
import json
import os
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import aqz_water as W
import aqz_water_game as G
import aqz_foundation as F
import level_package as L
ROM=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))
COUNTS={}
def tally(k,n):COUNTS[k]=n
def tearDownModule():print('AQZ A2 evidence vectors:',COUNTS,'total',sum(COUNTS.values()))

class Water(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=L.load_rom(ROM);cls.v=W.build(cls.r);cls.g=G.build(cls.r)
    def test_rom_and_reproducible_caches(self):
        self.assertEqual(L.sha256(self.r),L.ROM_SHA256)
        self.assertEqual(W.OUTPUT.read_text(encoding='utf-8'),F.dumps(self.v))
        self.assertEqual(G.OUTPUT.read_text(encoding='utf-8'),F.dumps(self.g))
        for x in self.v['source_regions'].values():self.assertEqual(L.sha256(self.r[x['file']:x['file']+x['length']]),x['sha256'])
        tally('source_hashes',len(self.v['source_regions']))
    def test_entry_exit_sweep(self):
        rows=self.v['crossing_vectors'];self.assertEqual(len(rows),1540)
        self.assertEqual({x['dy'] for x in rows},set(range(-5,6)))
        self.assertFalse(self.v['contracts']['crossing']['exit_effect']);tally('crossings',len(rows))
    def test_timer_rollovers_and_allocator_failure(self):
        rows=self.v['timer_vectors'];self.assertEqual(len(rows),216)
        self.assertTrue(any(x['coarse']==16 and x['requested']==31 for x in rows))
        self.assertTrue(any(x['fine']==255 and x['result_fine']==0 and x['coarse']==x['result_coarse'] for x in rows))
        tally('timer_boundaries',len(rows))
    def test_affected_physics_and_input_tables(self):
        p=self.v['physics'];self.assertEqual(len(p['vertical']),1792);self.assertEqual(len(p['control']),1650)
        self.assertEqual(self.v['contracts']['player_states']['17']['water_gravity'],0)
        self.assertIsNone(self.v['contracts']['player_states']['19']['water_gravity'])
        # Hurt continues through shared movement/water, unlike death/loops.
        self.assertEqual(self.r[0x03AA:0x03AD],bytes.fromhex('C3713A'))
        self.assertEqual(self.r[0x3A71:0x3A74],bytes.fromhex('CDEF3F'))
        # These old helpers have no pointer references anywhere in this ROM.
        for addr in (0x4B94,0x4BA5):self.assertNotIn(addr.to_bytes(2,'little'),self.r)
        tally('physics',len(p['vertical'])+len(p['control'])+len(p['jump']))
    def test_bubble_air_recovery_and_state_reachability(self):
        o=self.v['objects'];self.assertEqual([o['scripts'][str(t)]['state_count'] for t in (12,13,14,50)],[4,3,2,2])
        self.assertFalse(any(x['requested']==37 for x in o['bubble_contact'] if x['callback']==0x9D50))
        for x in o['air_reset']:self.assertEqual(x['result_fine'],x['fine']);self.assertEqual(x['result_coarse'],0)
        self.assertEqual(len(o['waterline_edges']),112)
        tally('bubble_contact_and_air',len(o['bubble_contact'])+len(o['air_reset'])+len(o['initializers'])+len(o['waterline_edges']))
    def test_animation_scheduler_lifecycle_and_pressure(self):
        c=self.v['lifecycle'];rows=c['emitter']
        born=[x['update'] for i,x in enumerate(rows) if any(y['type']==12 and not any(z['slot']==y['slot'] and z['type']==12 for z in rows[i-1]['children']) for y in x['children'])]
        self.assertEqual(born,[130,250,362,490,610,722])
        self.assertFalse(any(y['type']==12 for x in c['emitter_pool_pressure'] for y in x['children']))
        self.assertEqual([x['update'] for x in c['countdown'] if x['sound']==181],[2,122,242,362,482,602])
        self.assertEqual(c['splash'][13]['type'],255);self.assertEqual(c['splash'][14]['type'],0)
        self.assertEqual(c['restart']['fine'],0);self.assertEqual(c['creator_act_2']['objects'],[])
        tally('object_scheduler',sum(len(c[n]) for n in ('emitter','emitter_pool_pressure','splash','countdown')))
    def test_raster_boundary_and_strip_positions(self):
        r=self.v['raster'];self.assertEqual(len(r['boundary_vectors']),18)
        self.assertEqual(r['strip_tables']['1'],r['strip_tables']['0'][8:]+r['strip_tables']['0'][:8])
        tally('raster',len(r['boundary_vectors'])+len(r['strip_vectors']))
    def test_whole_game_order_drowning_and_restart(self):
        for a in self.g['acts'].values():
            self.assertTrue(a['history_independent_replay']);self.assertGreater(a['complete_cpu_state_bytes'],32)
            f=a['fixtures'];d=f['drowning'];self.assertEqual(len(d),2040)
            self.assertEqual((d[1319]['fine'],d[1319]['air']),(0,11));self.assertEqual(d[-1]['req'],31)
            self.assertTrue(all(x['rings']==0x32 for x in d))
            ev=f['entry'][0]['ev'];self.assertLess(ev.index('water'),ev.index('xmove'));self.assertLess(ev.index('terrain'),ev.index('objects'))
            self.assertTrue(any('restart_clear' in x['ev'] for x in f['drowning_death_restart']))
        tally('whole_game_updates',sum(len(rows) for a in self.g['acts'].values() for rows in a['fixtures'].values()))

if __name__=='__main__':unittest.main()

"""Small census completeness/provenance locks, reusing the accepted contracts."""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import spring_application_census as C
import level_package as L

D=json.loads(C.OUT.read_text(encoding='utf-8'))


class CensusTests(unittest.TestCase):
    def test_unique_ids_and_scope(self):
        self.assertEqual(len(D['acts']),15)
        self.assertEqual(len(D['occurrences']),800)
        self.assertEqual(len({o['id'] for o in D['occurrences']}),800)

    def test_required_fields(self):
        for o in D['occurrences']:
            for c in o['applications']:
                self.assertTrue({'mechanism','launch_vx','launch_vy','requested_player_state',
                                 'd448_write','expected_d503','expected_animation_family'}<=c.keys())

    def test_all_mapped_strengths(self):
        rows=[o for o in D['occurrences'] if o.get('type_id') in (38,48)]
        self.assertEqual(len(rows),54)
        for o in rows:
            strong=o['aux1']==0 if o['parameter']&128 else o['parameter']==0
            c=o['applications'][0]
            self.assertEqual(c['d448_write'],255 if strong else 0)
            self.assertEqual(c['launch_vy'],-7.375 if strong else -5)
        self.assertEqual(sum(o['applications'][0]['strength']=='weak' for o in rows),16)

    def test_special_cases(self):
        boss=next(o for o in D['occurrences'] if o.get('type_id')==80)
        self.assertEqual((boss['world_x'],boss['world_y']),(1936,238))
        self.assertEqual(boss['applications'][0],C.upright('type $50 boss bounce',-4,False))
        self.assertFalse(any(o.get('type_id') in (38,48) for o in D['occurrences'] if o['act_key']=='aqz2'))
        strong_spans=[o for o in D['occurrences'] if o.get('type_id')==38 and o['parameter']&128 and o['aux1']==0]
        self.assertEqual([(o['act_key'],o['world_x'],o['world_y']) for o in strong_spans],[('sez1',336,736),('sez1',1088,544)])

    def test_ceiling_paths(self):
        rows=[o for o in D['occurrences'] if o.get('block_id') in (58,59)]
        self.assertEqual(len(rows),22)
        self.assertEqual(sum(o['act_key']=='aqz3' for o in rows),7)
        for o in rows:
            self.assertEqual([a['requested_player_state'] for a in o['applications']],[28,27])

    def test_accepted_thz_cache(self):
        old=json.loads((ROOT/'data/rom-cache/spring-interaction.json').read_text())
        # Prior census enumerates the same closed THZ placements; new census widens coverage only.
        for act in ('thz1','thz2','thz3'):
            self.assertEqual(sum(o.get('type_id')==38 and o['act_key']==act for o in D['occurrences']),
                             len(old['type26_placements'][act]))

    def test_rom_regeneration(self):
        path=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))
        if not path.is_file(): self.skipTest('local ROM unavailable')
        self.assertEqual(C.build(L.load_rom(path)),D)

    def test_cache_evidence_hashes(self):
        import hashlib
        for name,digest in D['accepted_cache_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/'data/rom-cache'/name).read_bytes()).hexdigest(),digest)


if __name__=='__main__': unittest.main()

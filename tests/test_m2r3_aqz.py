"""Contract checks across independently generated ROM and Package B evidence."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class AQZEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v=json.loads((ROOT/'data/m2r3/evidence.json').read_text())
        cls.p=json.loads((ROOT/'data/m2r3/package-controls.json').read_text())
        cls.g=json.loads((ROOT/'data/m2r3/gameplay.json').read_text())

    def test_private_palette_pixels_not_wrong_import(self):
        p=self.v['private_package'];self.assertEqual(len(p['frames']),176)
        self.assertTrue(all(x['alpha_values']==[255] for x in p['frames']))
        self.assertTrue(all(x['wrong_proxy_indices']==[254] for x in p['frames'] if x['format']=='indexed'))
        self.assertEqual(len(p['decoder_controls']),45)

    def test_zone_binding_and_raster_are_separate(self):
        p=self.v['palette'];tails=[x for x in p['frames'] if x['character']==2]
        self.assertEqual(len(tails),88)
        self.assertTrue(all(x['opaque_stage6_to11_equal'] for x in tails))
        self.assertNotEqual(p['sources']['split_irq_cram'],p['sources']['fully_submerged_cram'])
        self.assertEqual(len(p['cram_controls']),8)
        self.assertEqual(sum(x['copied'] for x in p['cram_controls']),6)

    def test_all_placements_and_correct_object_identity(self):
        inv=self.v['inventory']['acts'];self.assertEqual([len(inv[k]['spears']) for k in ('aqz1','aqz2')],[8,3])
        pair=[s['placement'] for s in inv['aqz1']['spears'][:2]]
        self.assertEqual([(s['world_x'],s['world_y']) for s in pair],[(1104,686),(1232,686)])
        self.assertTrue(all(s['placement']['type_id']=='0x3C' for a in inv.values() for s in a['spears']))

    def test_character_water_and_plane_independence(self):
        grouped={}
        for row in self.v['spears']['rows']:
            # Remove character/water/plane; all remaining output must be identical.
            key=tuple(row[:2]+row[5:11]);grouped.setdefault(key,set()).add(tuple(row[11:]))
        self.assertTrue(all(len(x)==1 for x in grouped.values()))

    def test_positive_negative_contact_edges(self):
        rows=self.v['spears']['rows']
        base=[r for r in rows if r[0:5]==[0,12,2,255,0] and r[7:11]==[0,0,0,0]]
        self.assertEqual({(r[5],r[6]):r[11] for r in base},
            {(0,0):255,(-11,0):255,(11,0):255,(12,0):0,(0,-13):255,(0,-14):0,(0,24):255,(0,25):0})
        self.assertTrue(all(r[11]==0 for r in rows if r[7] or r[8] or r[9]&64))

    def test_spear_never_projects_character(self):
        self.assertTrue(all(r[13:]==[0,0] for r in self.v['spears']['rows']))

    def test_damage_protection_is_not_attack_immunity(self):
        rows=[r for r in self.v['spears']['rows'] if r[5:9]==[0,0,0,0]]
        self.assertTrue(all(r[12]==30 for r in rows if r[9]==2 and r[10]==0))
        self.assertTrue(all(r[12]==5 for r in rows if r[10]==6 or r[9]&192))

    def test_frozen_package_comparisons(self):
        p=self.p;self.assertEqual(p['contact_controls'],22528)
        self.assertEqual(p['contact_mismatches'],0);self.assertEqual(p['terrain_controls'],1152)
        self.assertEqual(p['terrain_mismatches'],[])
        self.assertEqual(sum(x['updates'] for x in p['motions']),1980)

    def test_terrain_direction_is_not_generic_spike_rectangle(self):
        rows=self.v['terrain_controls']
        self.assertEqual(sum(x['output']['hit'] for x in rows),176)
        self.assertTrue(all(not x['output']['hit'] for x in rows if x['approach']!='land'))
        self.assertEqual({x['block'] for x in rows},{4,60,61})

    def test_original_scheduler_positive_and_negative(self):
        self.assertEqual(len(self.g['cases']),4)
        for case in self.g['cases']:
            self.assertEqual(len(case['rows']),200)
            self.assertEqual(bool(case['hurt_updates']),case['mode']=='ground')
            self.assertEqual(len(case['observed_spears']),2)


if __name__=='__main__':unittest.main()

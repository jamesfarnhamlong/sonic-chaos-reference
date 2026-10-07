"""AQZ fresh decode, original routines, complete census and original renderer locks."""
import json
import os
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import aqz_foundation as F
import aqz_art_approval as A
import aqz_original_checks as O
import level_package as L
import mghz_object_census as C
CHECKS={}
def tally(name,n=1):CHECKS[name]=CHECKS.get(name,0)+n
def tearDownModule():print('AQZ evidence checks:',CHECKS,'total',sum(CHECKS.values()))
ROM=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))
EXPECTED={'aqz1':([168,24],[110,206],[0,99],[5120,528],4032,123,5,35,0x713E5),
          'aqz2':([128,32],[110,558],[0,447],[3840,784],4095,50,10,30,0x71521),
          'aqz3':([80,16],[110,238],[0,132],[2304,272],1280,4,0,4,0x71630)}

class Foundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=L.load_rom(ROM);cls.m,cls.c,cls.acts=F.build(cls.r)
        cls.art,cls.pixels=A.build(cls.r)
    def test_identity_and_regeneration(self):
        self.assertEqual(L.sha256(self.r),L.ROM_SHA256)
        self.assertEqual(self.m['research_base'],F.BASE)
        for name,value in [('implementation-manifest.json',self.m),('object-census.json',self.c),('art-approval.json',self.art)]:
            self.assertEqual((F.OUT/name).read_text(encoding='utf-8'),F.dumps(value));tally('cache_regeneration')
    def test_metadata_and_original_loaders(self):
        for k,e in EXPECTED.items():
            a=self.m['acts'][k];d=a['descriptor'];h=d['header'];s=d['start']
            self.assertEqual(a['dimensions_cells'],e[0]);self.assertEqual(a['dimensions_pixels'],[v*32 for v in e[0]])
            self.assertEqual([s['ram_d511'],s['ram_d514']],e[1]);self.assertEqual([s['ram_d2d6'],s['ram_d2d8']],e[2])
            self.assertEqual([h['ram_d282'],h['ram_d27e']],e[3]);self.assertEqual([h['ram_d280'],h['ram_d27c']],[0,8])
            self.assertEqual(a['layout']['runtime_written_cells'],e[4]);self.assertEqual(len(a['rings']['terrain']),e[5]);self.assertEqual(len(a['rings']['object09']),e[6])
            self.assertEqual(d['objects']['list_rom'],e[8]);self.assertTrue(all(d['consistency'].values()));tally('metadata',11)
            check=a['original_loaders'];self.assertEqual(check['start']['0xd511'],e[1][0]);self.assertEqual(check['header']['0xd282'],e[3][0])
            self.assertEqual(check['layout_cells_checked'],e[4]);self.assertTrue(check['unwritten_sentinel_intact']);tally('original_layout_cells',e[4])
        self.assertEqual(self.m['acts']['aqz2']['layout']['unloaded_cells'],[{'index':4095,'block':self.acts['aqz2']['cells'][4095]}])
        self.assertEqual(self.m['acts']['aqz1']['layout']['unloaded_cells'],[])
        self.assertEqual(self.m['acts']['aqz3']['layout']['unloaded_cells'],[])
    def test_mapping_original_consumers(self):
        for a in self.m['acts'].values():
            v=a['mapping_check'];self.assertEqual((v['bank'],v['table_cpu'],v['table_file']),(20,0x9320,0x51320))
            self.assertEqual((v['original_consumer_checks'],v['mismatches']),(512,0));self.assertEqual(v['historical_error_bytes'],0x1320)
            self.assertEqual(v['historical_different_blocks'],256);tally('original_mapping_consumers',512)
            for b in a['blocks']:
                mp=b['mapping'];self.assertEqual(mp['rom'],20*0x4000+mp['cpu']-0x8000)
                self.assertEqual(mp['pointer_entry_rom'],0x51320+2*b['id']);self.assertEqual(len(mp['attributes']),16)
                for h in b['headers']:
                    self.assertEqual(h['vertical'],list(self.r[h['vertical_pointer']:h['vertical_pointer']+32]))
                    self.assertEqual(h['horizontal'],list(self.r[h['horizontal_pointer']:h['horizontal_pointer']+32]))
                tally('decoded_blocks')
    def test_complete_object_records(self):
        total=0
        for k,e in EXPECTED.items():
            a=self.c['acts'][k];self.assertEqual(a['count'],e[7]);self.assertEqual(sum(a['type_counts'].values()),e[7])
            self.assertEqual(self.r[a['terminator_file']],255)
            for x in a['records']:
                off=int(x['rom_offset'],16);raw=bytes.fromhex(x['raw_bytes']);self.assertEqual(raw,self.r[off:off+9])
                self.assertEqual(x['world_x'],x['stored_x']-256);self.assertEqual(x['world_y'],x['stored_y']-256)
                self.assertEqual(x['placement_token'],x['index']);self.assertEqual(x['act'],k)
                self.assertEqual(x['original_creator']['token'],x['index'])
                self.assertEqual(x['original_creator']['flags'],int(x['flags'],16)|64)
                self.assertEqual(x['original_creator']['art_bases'],[int(x['aux0'],16),int(x['aux1'],16)]);tally('original_placement_creators')
                self.assertIn(x['classification'],F.CLASSES);self.assertEqual(x['bank'],'0x1C');total+=1;tally('mapped_records')
        self.assertEqual(total,69)
        self.assertEqual({t:v['placements'] for t,v in self.c['types'].items() if v['placements']},
            {'0x09':15,'0x0C':2,'0x10':14,'0x18':2,'0x30':2,'0x3C':11,'0x3D':19,'0x3F':3,'0x59':1})
    def test_reuse_is_parameter_guarded(self):
        self.assertTrue(self.c['platform_reuse_recon']['tables_identical'])
        self.assertIn('state14',self.c['platform_reuse_recon']['aqz2_override'])
        for a in self.c['acts'].values():
            for x in a['records']:
                if x['type_id']=='0x3F':self.assertEqual(x['classification'],'AQZ_SPECIFIC_RECOVERED')
                if x['type_id'] in ('0x09','0x10','0x18'):self.assertTrue(x['contract']);tally('reuse_records')
        for name,v in self.c['shared_systems'].items():self.assertGreater(v['regions_checked'],0);self.assertEqual(v['hash_mismatches'],[]);tally('shared_source_regions',v['regions_checked'])
        for name in ('spring26','platform28','spike1b','spring_shoes2f'):self.assertEqual(self.c['system_presence'][name]['mapped'],0)
        self.assertEqual(self.c['system_presence']['rocket_shoes']['mapped'],2)
    def test_palettes_loads_and_effects(self):
        for a in self.m['acts'].values():
            self.assertEqual(a['graphics']['palettes']['background']['index'],25);self.assertEqual(a['graphics']['palettes']['sprite']['index'],10)
            self.assertEqual(len(a['graphics']['loads']),9);self.assertEqual(a['graphics']['loads'][0]['stream_rom'],'0x58000')
            self.assertEqual(a['graphics']['loads'][0]['tile_count'],232);tally('graphics_loads',9)
        e=self.m['effects'];self.assertEqual(set(e),{'5','11'})
        self.assertEqual(e['5']['cadence'],[3]);self.assertEqual(e['5']['boss_active_events'],[]);self.assertEqual(len(e['5']['unique_copies']),2)
        self.assertEqual(e['11']['cadence'],[8]);self.assertEqual(e['11']['boss_active_events'],e['11']['events']);self.assertEqual(len(e['11']['unique_copies']),16)
        self.assertEqual({(c['vram'],c['length']) for c in e['11']['unique_copies']},{(0x3000,448)})
        self.assertEqual({(c['vram'],c['length']) for c in e['5']['unique_copies']},{(0x2e20,32)})
    def test_environment_gates(self):
        e=self.m['environment']
        for row in e['gates']:
            active=row['zone']==4 and row['act']<2
            self.assertEqual((row['water'],row['timer']),(0,0) if active else (255,7));tally('water_zone_gates')
        self.assertEqual([x['water'] for x in e['boundary']],[0,0,255,255,255]);tally('waterline_boundaries',5)
        self.assertEqual(e['waterline_initializers']['aqz1'],568);self.assertEqual(e['waterline_initializers']['aqz2'],788)
        self.assertEqual(self.c['boss']['framework_row']['trigger_dx_lt'],96)
        self.assertEqual(self.c['types']['0x59']['script']['state_count'],21)
        self.assertEqual(self.c['boss']['children'],['0x5A','0x5B','0x5C','0x5D'])
        self.assertEqual(self.c['boss']['child5c_frame_selector']['frames'],list(range(16,24)));tally('original_child_frame_selectors',1024)
    def test_visual_original_renderer(self):
        self.assertEqual(self.art['status'],'APPROVED');self.assertEqual(self.art['approved_by'],'James')
        for s in self.pixels['subjects'].values():
            for f in s['frames']:
                for im in f['images']:
                    self.assertEqual(C.composed_hash(im['pieces']),im['composed_index_sha256']);tally('original_renderer_compositions')
        self.assertEqual(len(self.art['animated']['effect11']),16)
    def test_guarded_whole_game_complete_snapshot(self):
        value=O.build(self.r);self.assertEqual(F.dumps(value),O.OUTPUT.read_text(encoding='utf-8'))
        for k,v in value['acts'].items():
            self.assertTrue(v['history_independent_replay']);self.assertGreater(v['complete_cpu_state_bytes'],32)
            self.assertEqual(v['layout_mismatches'],[]);self.assertEqual(v['layout_cells_checked'],EXPECTED[k][4]);tally('wholegame_replay_updates',96)

if __name__=='__main__':unittest.main()

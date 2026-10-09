"""Fresh final-zone data versus original ROM consumers."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import eez_foundation as F
import level_package as L
ROM=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))

class Foundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=L.load_rom(ROM);cls.m,cls.c,cls.acts=F.build(cls.r)
    def test_regeneration(self):
        self.assertEqual(L.sha256(self.r),L.ROM_SHA256)
        for n,v in [('implementation-manifest.json',self.m),('object-census.json',self.c)]:
            self.assertEqual((F.OUT/n).read_text(encoding='utf-8'),F.dumps(v))
    def test_loaders_and_dimensions(self):
        for k,wh,start,cam,count in [('eez1',[128,32],[238,864],[126,752],4095),('eez2',[128,32],[170,430],[58,318],4095),('eez3',[112,32],[110,288],[0,176],3584)]:
            a=self.m['acts'][k];d=a['descriptor'];o=a['original_loaders']
            self.assertEqual(a['dimensions_cells'],wh);self.assertEqual(o['cells_checked'],count)
            self.assertEqual([o['start']['0xd511'],o['start']['0xd514']],start)
            self.assertEqual([o['start']['0xd2d6'],o['start']['0xd2d8']],cam)
            self.assertTrue(o['sentinel']);self.assertTrue(all(d['consistency'].values()))
            self.assertEqual(a['mapping_check']['original_consumer_checks'],512)
            self.assertEqual(a['mapping_check']['mismatches'],0)
            self.assertEqual(a['mapping_check']['historical_error_bytes'],0x24E0)
            self.assertEqual(a['mapping_check']['historical_different_blocks'],256)
    def test_census_and_creators(self):
        totals={}
        for k,n in [('eez1',19),('eez2',35),('eez3',5)]:
            a=self.c['acts'][k];self.assertEqual(a['count'],n);self.assertEqual(self.r[a['terminator_file']],255)
            for x in a['records']:
                off=int(x['rom_offset'],16);self.assertEqual(bytes.fromhex(x['raw_bytes']),self.r[off:off+9])
                self.assertEqual(x['original_creator']['x'],x['world_x']&65535)
                self.assertEqual(x['original_creator']['y'],x['world_y']&65535)
                self.assertEqual(x['original_creator']['token'],x['index'])
                totals[x['type_id']]=totals.get(x['type_id'],0)+1
        self.assertEqual(totals,{'0x09':6,'0x10':7,'0x17':5,'0x18':2,'0x26':2,'0x28':9,'0x2C':9,'0x36':10,'0x38':7,'0x5E':1,'0x60':1})
    def test_rings_surfaces_effects(self):
        self.assertEqual([len(a['rings']['terrain']) for a in self.m['acts'].values()],[146,276,0])
        self.assertEqual(set(self.m['effects']),{'5','6','8','13'})
        self.assertEqual(set(map(int,self.m['surfaces'])),{0,1,2,3,5,7,9,10,11,12,13,14,19,20,22,26})
        for a in self.m['acts'].values():
            self.assertEqual(a['graphics']['palettes']['background']['index'],26)
            self.assertEqual(a['graphics']['palettes']['sprite']['index'],11)
            for b in a['blocks']:
                self.assertEqual(b['mapping']['rom'],20*0x4000+b['mapping']['cpu']-0x8000)

if __name__=='__main__':unittest.main()

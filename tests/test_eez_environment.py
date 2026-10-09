import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import eez_foundation as F
import eez_environment as E
import eez_transport as T
import rom as R

class Environment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=R.load(ROOT.parent/'source/Sonic Chaos (Europe).sms')
    def test_environment_sweeps_and_cache(self):
        v=E.build(self.r);self.assertEqual(sum(v['checks'].values()),5200)
        self.assertEqual((F.OUT/'environment-gates.json').read_text(encoding='utf-8'),F.dumps(v))
    def test_transport_routes_and_cache(self):
        v=T.build(self.r);self.assertEqual(v['checks'],44800)
        self.assertEqual((F.OUT/'transport-state21.json').read_text(encoding='utf-8'),F.dumps(v))
    def test_original_boot_evidence(self):
        v=json.loads((F.OUT/'original-checks.json').read_text())
        self.assertEqual(v['rom_sha256'],R.SHA256)
        self.assertEqual(sum(a['layout_cells_checked'] for a in v['acts'].values()),11774)
        for a in v['acts'].values():
            self.assertEqual(a['layout_mismatches'],[]);self.assertTrue(a['history_independent_replay'])
            self.assertEqual(a['complete_cpu_state_bytes'],65580)

if __name__=='__main__':unittest.main()

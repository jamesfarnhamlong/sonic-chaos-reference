"""Public metadata tests; private original execution/PCM has separate receipts."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'data/m5-g1r2'
def load(name):return json.loads((PUB/name).read_text())

class Evidence(unittest.TestCase):
    def test_coverage(self):
        e=load('evidence.json');self.assertEqual(e['cases'],25)
        self.assertEqual(set(n[:2] for n in e['cases_detail']),{'83','93','8F'})
    def test_exact_recurrence_and_beyond_horizon(self):
        for name in load('evidence.json')['cases_detail']:
            c=load(name+'.json');r=c['recurrence'];self.assertGreater(r['first_tick'],max(map(int,c['schedule']['events'])))
            self.assertEqual(r['repeat_tick']-r['first_tick'],r['period_ticks'])
            self.assertGreater(c['ticks'],8400);self.assertGreaterEqual(c['ticks'],r['repeat_tick']+r['period_ticks'])
            self.assertTrue(c['original_state_write_transfer_period_exact'])
    def test_receipts(self):
        e=load('evidence.json');ticks=samples=0
        for name in e['cases_detail']:
            c=load(name+'.json');v=load(name+'-verified.json')
            self.assertEqual(v['status'],'PASS');self.assertTrue(v['isolated_exact']);self.assertGreaterEqual(v['renewals'],1)
            self.assertEqual(v['state_PSG_transfer_PCM_native_partition_mismatches'],0)
            self.assertEqual(v['samples'],735*v['ticks']);self.assertEqual(v['ticks'],c['state400_shadow_ticks'])
            self.assertEqual(v['physical_PSG_resets_at_events_checkpoints_recurrences'],0)
            self.assertEqual(len(c['bank_canonical_sha256']),64);ticks+=v['ticks'];samples+=v['samples']
        self.assertEqual((ticks,samples),(e['ticks'],e['samples']))
    def test_epoch_and_clock(self):
        for rid in ('83','93','8F'):
            c=load(rid+'-epoch.json');self.assertEqual(c['accepted_music_epochs'],[[1,int(rid,16)],[250,int(rid,16)]])
        c=load('8F-clock.json');self.assertEqual(c['accepted_music_epochs'],[[1,143],[690,143]])
        self.assertIn(30,c['reset_ticks']);self.assertNotIn([30,248],c['accepted_music_epochs'])
        self.assertEqual(sum(a==[['request',181]] for a in c['schedule']['events'].values()),10)
    def test_competing_late_events(self):
        for rid in ('83','93','8F'):
            c=load(rid+'-competing.json');self.assertIn('4190',c['schedule']['events']);self.assertIn('4300',c['schedule']['events'])
    def test_negatives(self):
        n=load('negatives.json');self.assertEqual(len(n),27);self.assertTrue(all(v['detected'] for v in n.values()))
    def test_no_scope_expansion(self):
        e=load('evidence.json');self.assertEqual(e['arbitrary_gameplay_phase_continuation'],'HOLD')
        self.assertEqual(e['other_music_programmes'],'HOLD_NOT_EXPANDED');self.assertFalse(e['old_solo_certificates_reused']);self.assertFalse(e['native_GameMaker_tested'])
    def test_progression_under_suppression(self):
        e=load('evidence.json')
        for name,d in e['cases_detail'].items():
            self.assertTrue(d['final_music_active_slots'])
            self.assertTrue(any(d['phases']['beyond_former_horizon']['music_slot_progress_updates']))
            if '-BF-' in name or '-A6-' in name:self.assertTrue(d['suppression_clear_ticks'])

if __name__=='__main__':unittest.main()

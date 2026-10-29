"""Public decision integrity; bounded searches are not induction evidence."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'data/m5-g1r3'
def load(p):return json.loads((PUB/p).read_text())

class Decision(unittest.TestCase):
    def test_honest_hold(self):
        d=load('decision.json');self.assertEqual(d['decision'],'HOLD')
        for k in ('general_solution_proved','architectural_impossibility_proved','replacement_runtime_shown_necessary','continuation_permission','old_execution_repeated'):self.assertFalse(d[k])
        self.assertEqual(d['new_exact_history_certificates'],0);self.assertTrue(d['stop_for_manager_review'])
    def test_search_scope(self):
        r=load('search-results.json');self.assertEqual(len(r['cases']),2);self.assertFalse(r['continuation_permission'])
        self.assertEqual(sum(c['ticks'] for c in r['cases'].values()),1024)
        self.assertEqual(sum(c['samples'] for c in r['cases'].values()),752640)
        for c in r['cases'].values():
            self.assertEqual(c['state_PSG_transfer_PCM_native_mismatches'],0);self.assertFalse(c['induction_proved']);self.assertEqual(c['horizon_unchanged'],4200)
    def test_obstructions_are_scoped(self):
        c=load('cached-obstructions.json');self.assertEqual(c['new_original_execution_ticks'],0)
        self.assertEqual(c['music_plus_write_mask_counterexample']['slot_offset_changes'],[[2,31]])
        self.assertEqual(c['inactive_BF_residue']['tick'],50);self.assertEqual(len(c['inactive_BF_residue']['nonzero_offsets']),20)
        self.assertFalse(c['synthetic_unreachable_pointer_guard']['natural_reachability_claimed'])
    def test_guards_retained(self):
        n=load('negative-controls.json');self.assertEqual(len(n['cases']),6);self.assertTrue(all(x['detected'] for x in n['cases'].values()))
        self.assertFalse(n['continuation_permission'])
    def test_pinned_sources_unchanged(self):
        import hashlib
        a=load('source-audit.json');self.assertFalse(a['source_translation_equivalence_proved']);self.assertFalse(a['closed_reachable_state_family_proved'])
        for p,r in a['methods'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_text().encode()).hexdigest(),r['file_sha256'])
    def test_no_native_claim(self):
        d=load('decision.json');self.assertEqual(d['new_native_GameMaker_tests'],0);self.assertTrue(d['existing_caps_unchanged'])

if __name__=='__main__':unittest.main()

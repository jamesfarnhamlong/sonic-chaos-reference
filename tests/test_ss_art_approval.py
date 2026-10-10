"""Special Stage visual package index (pixels live only in ignored build/)."""
import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'tools'))
CACHE = ROOT / 'data/rom-cache/special-stages/art-approval.json'


class ArtApproval(unittest.TestCase):
    def test_index(self):
        d = json.loads(CACHE.read_text(encoding='utf-8'))
        self.assertTrue(d['approval'].startswith('PENDING'))
        ids = [b['id'] for b in d['boards']]
        for want in ('map-ss1', 'map-ss2', 'map-ss3', 'map-ss4', 'map-ss5', 'terrain-outdoor', 'terrain-interior', 'objects-new', 'monitors-emulated', 'goal-ring-in-situ', 'results'):
            self.assertIn(want, ids)
        ded = {(x['type'], x['stage']): x['pixel_identical_to_approved_zone_art'] for x in d['dedup']}
        self.assertTrue(ded[(0x2F, 2)] and ded[(0x26, 4)])                 # already-approved Spring Shoes / spring art is not re-submitted
        self.assertFalse(any(ded[(0x31, s)] for s in range(1, 6)))          # the five goal-ring colourways are new
        ring = next(b for b in d['boards'] if b['id'] == 'objects-new')
        self.assertEqual({c['type'] for c in ring['cells']}, {0x31})


if __name__ == '__main__':
    unittest.main()

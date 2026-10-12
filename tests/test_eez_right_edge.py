import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import eez_right_edge as E
import rom


class RightEdge(unittest.TestCase):
    def test_original_boundary_sweep(self):
        r=rom.load(ROOT.parent/'source/Sonic Chaos (Europe).sms')
        cached=json.loads((ROOT/'data/rom-cache/eez/right-edge-threat.json').read_text())
        self.assertEqual(E.boundaries(r),cached['boundaries'])

    def test_scheduler_evidence_contract(self):
        v=json.loads((ROOT/'data/rom-cache/eez/right-edge-threat.json').read_text())
        self.assertEqual(v['rom_sha256'],rom.SHA256)
        self.assertEqual(v['natural']['updates'],781)
        self.assertEqual(v['natural']['event_counts']['death'],1)
        s=v['stationary']
        self.assertEqual(s['updates'],12000)
        self.assertEqual(s['late_player_x'],[2198])
        self.assertEqual(s['late_boss_x_range'],[2107,2143])
        self.assertEqual(s['late_body_overlaps'],0)
        self.assertEqual(s['late_jump_count'],0)
        self.assertEqual(s['late_child_damage_count'],258)
        jump=next(e for e in s['selected_events'] if e['event']=='select_jump')
        self.assertEqual((jump['actor'][0],jump['player'][0]),(2172,2198))


if __name__=='__main__':unittest.main()

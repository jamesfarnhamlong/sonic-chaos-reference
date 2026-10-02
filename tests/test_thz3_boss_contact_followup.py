"""Focused ROM/cached oracles for THZ3 contact and presentation."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import thz3_boss_contact_followup as tool
D=json.loads(tool.OUTPUT.read_text())


class ContactFollowup(unittest.TestCase):
    def test_verified_identity(self):
        self.assertEqual(D['rom_sha256'],tool.base.ROM_SHA256)
        self.assertTrue(D['research_only'] and D['poc_untouched'])

    def test_velocity_flags_and_floor_sweep(self):
        self.assertEqual(D['response']['cases'],8000)
        self.assertEqual(D['response']['mismatches'],[])
        for r in D['response']['examples']:
            p=r['after']['player'];before=r['before']
            self.assertEqual(p['current'],5) # requested state changes, current waits
            if r['region'] in ('left','right'):
                self.assertEqual(p['vy'],-before['vy'])
                self.assertEqual(p['vx'],-1536 if r['region']=='left' else 1536)
                self.assertEqual(p['flags'],before['flags'])

    def test_geometry_every_boundary(self):
        self.assertEqual(D['geometry']['cases'],17700)
        self.assertEqual(D['geometry']['mismatches'],[])
        edges={(r['dx'],r['dy']):r['contact'] for r in D['geometry']['boundary_examples']}
        self.assertEqual([edges[(x,-34)] for x in (13,14,15)],[1,1,4])
        self.assertEqual([edges[(0,y)] for y in (-49,-48,-21,-20,-19,-1,0,24,25)],
                         [0,1,1,1,4,4,2,2,0])

    def test_top_clears_attack_without_requiring_it(self):
        for r in D['immunity']:
            if r['state']==18 or r['region']!='top':continue
            p=r['before_damage_consumer'];flags=r['flags']
            self.assertEqual(p['flags'],(flags|1)&~2)
            self.assertEqual((p['vy'],p['floor'],p['requested']),(-1024,0,11))
            self.assertEqual(r['boss_contact']['sound'],0xA6)
            self.assertEqual(r['boss_contact']['health'],8)

    def test_hurt_and_blink_do_not_block_boss_attack(self):
        for r in D['immunity']:
            if r['state']==18 or r['region']=='top':continue
            p=r['before_damage_consumer'];q=r['after_damage_consumer']
            if r['flags']&2:
                self.assertEqual(r['boss_contact']['health'],7)
                self.assertEqual(r['boss_contact']['cooldown_1E'],0)
                self.assertEqual(p['requested'],27)
            elif r['flags']&0xC0:
                self.assertEqual(r['boss_contact']['health'],8)
                self.assertEqual(r['boss_contact']['cooldown_1E'],2)
                for k in ('vx','vy','flags','requested','floor'):
                    self.assertEqual(p[k],q[k])

    def test_power_immunity_is_not_attack(self):
        for r in D['immunity']:
            if r['power']!=6 or r['flags']!=0 or r['region']=='top':continue
            self.assertEqual(r['boss_contact']['health'],8)
            self.assertEqual(r['after_damage_consumer']['damage_request'],0)
            self.assertEqual(r['after_damage_consumer']['requested'],0)

    def test_cooldown_is_two_whole_helpers_then_active(self):
        for r in D['cooldown']['rows']:
            if r['region']=='top' or r['flags']&2:continue
            seq=r['sequence']
            self.assertEqual(seq[0]['result']['cooldown_1E'],2)
            self.assertEqual([x['cooldown'] for x in seq[1:4]],[1,0,2])
            self.assertEqual([x['player']['damage_request'] for x in seq[1:4]],[0,0,255])
            self.assertEqual(seq[1]['x'],seq[2]['x'])
            self.assertEqual(seq[3]['x'],seq[1]['x']-2)

    def test_cooldown_decrement_scope_and_entry_exception(self):
        for r in D['cooldown']['decrement_scope']:
            self.assertEqual(r['cooldown'],1 if r['state'] in tool.STATES else 2)
            if r['state']==18:self.assertEqual(r['player']['damage_request'],255)

    def test_reaction_first_active_update_21(self):
        for r in D['reaction_recontact']:
            seq=r['timeline']
            if r['region']=='left':
                self.assertEqual([x['health'] for x in seq[1:21]],[7]*20)
                self.assertEqual(seq[21]['health'],6)
            else:
                self.assertEqual([x['player']['requested'] for x in seq[1:21]],[0]*20)
                self.assertEqual(seq[21]['player']['requested'],11)
            self.assertEqual(seq[20]['reaction'],0)
            self.assertEqual(seq[21]['reaction'],20)

    def test_all_hit_counts_and_phase_feedback(self):
        self.assertEqual(len(D['progression']),96)
        for r in D['progression']:
            c=r['contact'];hp=r['before_health']
            self.assertEqual((c['health'],c['flash'],c['sound'],c['player_requested_state']),
                             (hp-1,7,0xB6,27))
            self.assertEqual(c['requested'],4 if hp==1 else r['state']+2)
            if hp>1:
                self.assertEqual([x['state'] for x in r['timeline'][:20]],[r['state']+2]*20)
                self.assertEqual(r['timeline'][19]['vx'],0)
                self.assertEqual(r['timeline'][19]['phase'],1)
            else:self.assertEqual(r['timeline'][1]['frame'],0)

    def test_direction_facing_phase_independence(self):
        for r in D['independence']:
            p=r['player'];region=r['region']
            self.assertEqual(p['vx'],-1536 if region=='left' else 1536 if region=='right' else 128)
            self.assertEqual(p['vy'],-1024 if region=='top' else 1536 if region=='below' else -768)
            self.assertEqual(p['visibility'],r['player_facing_D504'])

    def test_palette_command_four_call_delay_four_white_calls(self):
        seq=D['flash'][:8]
        self.assertEqual([x['colors'] for x in seq],[[53,32]]*3+[[63,63]]*4+[[53,32]])
        self.assertEqual(seq[7]['command'],0)

    def test_actual_cram_transfer_delay(self):
        rows=D['aligned']['rows'];hit=D['aligned']['hit_driver_update']-D['aligned']['created']
        self.assertEqual([r['update']-hit for r in rows if r['cram'][13:15]==[63,63]],[5,6,7,8])
        before,after=D['aligned']['contact_hooks']
        self.assertEqual(after['vy'],-before['vy'])
        self.assertEqual(after['vx'],-1536)
        self.assertEqual(after['current'],before['current'])
        self.assertEqual(after['requested'],27)

    def test_entry_script_and_palette_timeline(self):
        rows=D['aligned']['rows']
        self.assertEqual([(n,rows[n]['boss_state'],rows[n]['mapping'],rows[n]['timer'])
                          for n in (0,1,2,18,101,102,103,119,135,151,167,171)],
                         [(0,0,0,0),(1,0,0,224),(2,1,0,224),(18,2,0,224),(101,2,0,141),
                          (102,3,0,224),(103,18,1,16),(119,18,2,16),(135,18,1,16),
                          (151,18,2,16),(167,18,1,16),(171,6,1,16)])
        self.assertEqual(next(r['update'] for r in rows if r['onscreen_matched_pieces']),104)
        self.assertEqual(rows[106]['cram'][13:16],[53,32,63])
        self.assertEqual(rows[134]['art_request'],0)
        self.assertEqual(rows[171]['sat_previous_update_matches'],13)

    def test_repeated_top_bounces_are_bounded(self):
        free,tracked=D['top_runs']
        self.assertEqual(free['bounce_updates'],[1])
        self.assertEqual(tracked['bounce_updates'],[1,69,137,205])
        self.assertEqual(tracked['minimum_screen_y'],28)
        for n in tracked['bounce_updates']:
            self.assertEqual(tracked['rows'][n]['flags']&3,1)


class RomReplay(unittest.TestCase):
    def test_complete_focused_replay(self):
        paths=[Path(os.environ['SONIC_CHAOS_ROM'])] if os.environ.get('SONIC_CHAOS_ROM') else []
        paths += [ROOT.parent/'source/Sonic Chaos (Europe).sms']
        rom=next((p.read_bytes() for p in paths if p.is_file() and
                  hashlib.sha256(p.read_bytes()).hexdigest()==tool.base.ROM_SHA256),None)
        if rom is None:self.skipTest('verified local ROM unavailable')
        self.assertEqual(tool.build(rom),D)


if __name__=='__main__':unittest.main()

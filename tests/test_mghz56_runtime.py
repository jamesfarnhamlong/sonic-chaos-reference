"""MGHZ3 dependency-chain regression locks and original-ROM regeneration."""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import mghz56_runtime as B
import mghz56_fullgame as F
import rom as R

D=json.loads(B.OUTPUT.read_text())
M=json.loads(B.MANIFEST.read_text())
G=json.loads(F.OUTPUT.read_text())
S=D['static']


def local_rom():
    candidates=[Path(os.environ['SONIC_CHAOS_ROM'])] if os.environ.get('SONIC_CHAOS_ROM') else []
    candidates.append(ROOT.parent/'source/Sonic Chaos (Europe).sms')
    for p in candidates:
        if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==R.SHA256:return R.load(p)
    return None


ROM=local_rom()


class CacheTests(unittest.TestCase):
    def test_identity_scope(self):
        self.assertEqual(D['rom_sha256'],R.SHA256)
        self.assertEqual(D['research_base'],'7ba4d8a7bfb7f8164462fbf50db05c4b63cec0fe')
        self.assertTrue(D['research_only'] and D['poc_untouched'])
        self.assertEqual(M['state_counts'],{'86':13,'87':4,'88':2})

    def test_placement_and_map(self):
        p=S['placement']
        self.assertEqual((p['index'],p['type_id'],p['parameter'],p['world_x'],p['world_y']),(12,'0x56','0x00',3269,288))
        self.assertEqual((p['bank'],p['cpu'],p['rom_offset']),('0x1C','0x93DB','0x713DB'))
        self.assertEqual((S['act']['width'],S['act']['height'],S['act']['header']['width_cells']),(3840,768,120))
        self.assertEqual(S['initial']['slots'][0]['placement_token'],12)

    def test_state_table_sources(self):
        self.assertEqual([(v['state_table_cpu'],v['state_count']) for v in S['scripts'].values()],
                         [(0xA4C4,13),(0xA6D7,4),(0xA78A,2)])
        self.assertTrue(all(op['op']!='unknown' for sc in S['scripts'].values() for st in sc['states'] for op in st['ops']))

    def test_shared_intro_defeat_tables(self):
        sc=S['scripts']['86']
        self.assertEqual(sc['state_script_cpus'][:6],[0x95B1,0x95BA,0x95C0,0xA4DE,0x95CC,0x961E])
        self.assertEqual(sc['frames'],list(range(7)))

    def test_projectile_script_chain(self):
        self.assertEqual(S['scripts']['86']['spawns'][-2:],
            [dict(state=8,type=87,dx=-20,dy=-8,parameter=0),dict(state=9,type=87,dx=-16,dy=-8,parameter=1)])
        self.assertEqual(S['scripts']['87']['spawns'],
            [dict(state=3,type=88,dx=0,dy=0,parameter=0),dict(state=3,type=88,dx=0,dy=0,parameter=1)])

    def test_creation_band_scanner(self):
        x=D['creation_camera']['scan_screen_x_by_fill']
        self.assertEqual(x['1'],list(range(-96,-32))+list(range(288,352)))
        self.assertEqual(x['0'],list(range(-96,352)))

    def test_trigger_boundaries(self):
        for dx,dy,req in D['thresholds']['triggers']:
            self.assertEqual(req==2,abs(dx)<160 and abs(dy)<304)

    def test_init_camera_target(self):
        row=S['trigger_camera_tables']['mghz_row']
        self.assertEqual([row[k] for k in ('trigger_dx_lt','trigger_dy_lt','camera_x_offset','camera_y_offset')],[160,304,-208,-32])
        self.assertEqual(S['shared_pan_setup']['pan'],[3061,256])
        self.assertEqual(S['shared_pan_setup']['limits'][3],256)

    def test_fullgame_camera_is_exclusive(self):
        fight=[v for v in G['rows'] if 250<=v['update']<=400]
        self.assertTrue(all(v['camera']==[3060,256] for v in fight))
        self.assertTrue(all(v['pan']==[3061,256] for v in fight))

    def test_exact_body_and_child_extents(self):
        f={v['frame']:v for v in S['art']['frames']}
        self.assertTrue(all(f[i]['extent_x_y']==[16,48] for i in range(1,7)))
        self.assertEqual([f[i]['extent_x_y'] for i in range(11,16)],[[12,16],[8,16],[4,16],[4,16],[4,16]])
        self.assertEqual([f[i]['piece_count'] for i in range(11,16)],[3,2,1,1,1])

    def test_geometry_ties(self):
        self.assertEqual([B.overlap_model(*p) for p in ((0,-48),(0,-49),(24,0),(25,0),(0,24),(0,25),(16,-40))],
                         [1,0,4,0,2,0,1])
        self.assertEqual(B.overlap_model(25,0,ex=9),4)

    def test_top_only_hp_and_attack_bit(self):
        for v in D['contacts']['cases']:
            allow,attack,_,_,_,_,point,_,_,_,before,_=v
            self.assertEqual(before['hp'],9 if allow and attack and point==[0,-48] else 10)
            self.assertEqual(bool(before['player']['damage']),not attack)

    def test_hp_zero_is_alive_until_underflow(self):
        rows=D['thresholds']['health']
        self.assertEqual([r['hp'] for r in rows],list(range(9,-1,-1))+[255])
        self.assertEqual([r['requested'] for r in rows],[6]*10+[4])
        self.assertEqual([h['before_hp'] for h in G['hits']],list(range(10,-1,-1)))

    def test_eight_contact_call_cooldown(self):
        rows=D['thresholds']['repeated_contact']
        self.assertEqual([r[0] for i,r in enumerate(rows) if i==0 or r[1]!=rows[i-1][1]],[0,8,16,24])
        self.assertEqual([r[2] for r in rows[:9]],[8,7,6,5,4,3,2,1,8])

    def test_grounded_below_is_death_setup(self):
        for v in D['contacts']['cases']:
            self.assertFalse(v[10]['death_flag']) # these representatives are airborne
        for v in D['clear']['rows']:
            self.assertEqual(v['player']['requested']==32,v['x']>=3356 and bool(v['floor']&2))
        if ROM:
            lab=B.Lab(ROM)
            for attack in (0,2):
                for inv in (0,128):
                    result=B.prepare(lab,dy=24,floor=2,attack=attack,inv=inv)
                    self.assertTrue(result['death_flag'])
                    self.assertEqual(result['player']['requested'],27 if attack else 31)

    def test_projectile_launch_velocities(self):
        rows=D['children']['launch']
        for row in rows:
            b=next(v for v in row['row']['slots'] if v['slot']==B.SLOT)
            expected=-512 if row['type']==87 and row['parameter']==0 else -544
            self.assertEqual(b['vx'],expected)
            self.assertEqual(b['vy'],(-112 if row['parameter']==0 else 112) if row['type']==88 else 0)

    def test_projectile_early_removal_gate(self):
        for sleep,counter,x,y,type_id,param in D['children']['removal_gates']:
            removed=bool(sleep) or (counter%2==0 and x<176 and y>=120)
            self.assertEqual(type_id==15,removed)
            self.assertEqual(param,0)

    def test_projectile_attack_hurt_independence(self):
        rows=D['children']['contact_geometry']
        for frame in (11,12,15):
            group=[v for v in rows if v['frame']==frame]
            self.assertTrue(all(v['damage_requests']==0 for v in group if v['hurt']))
            self.assertEqual(len({v['damage_requests'] for v in group if not v['hurt']}),1)

    def test_script_child_same_update_initialization(self):
        events=D['cycles']['rows']['9']['events']
        child=next(v for v in events[0]['slots'] if v['type']==87)
        self.assertGreater(child['slot'],B.SLOT)
        self.assertEqual((child['state'],child['requested']),(0,1))
        split=next(row for row in events if any(v['type']==88 for v in row['slots']))
        kids=[v for v in split['slots'] if v['type']==88]
        self.assertEqual(sorted(v['parameter'] for v in kids),[0,1])
        self.assertTrue(all(v['state']==0 and v['requested']==1 for v in kids))

    def test_defeat_sequence_duration(self):
        rows=D['cycles']['rows']['4']['events']
        gate=next(v for v in rows if any(s['type']==86 and s['state']==5 for s in v['slots']))
        self.assertEqual(gate['tick'],148)

    def test_flash_restores_mghz_palette(self):
        rows=D['feedback']['rows']
        self.assertEqual([r['colors'] for r in rows],[[42,21]]*3+[[63,63]]*4+[[42,21]]*3)
        self.assertEqual(rows[-1]['command'],0)

    def test_art_is_already_approved(self):
        approved=json.loads((ROOT/'data/rom-cache/mghz/art-approval.json').read_text())['subjects']['0x56']
        self.assertFalse(M['art']['new_visual_approval_required'])
        self.assertEqual(M['art']['reachable_frames'],list(range(7))+list(range(11,16)))
        for fr in S['art']['frames']:
            if fr['frame']:
                self.assertEqual(fr['images'][0]['composed_index_sha256'],approved['frame_hashes'][str(fr['frame'])][0])

    def test_mapping_and_dynamic_sources(self):
        self.assertEqual({v['mapping_cpu'] for v in S['art']['mapping'].values()},{0x9861})
        self.assertEqual([(v['tile_base'],v['tile_count'],v['source_rom']) for v in S['art']['loads']],[(46,64,0x17680),(110,12,0x26BA0)])

    def test_timer_continues_and_results_advances(self):
        self.assertTrue(all(v['timer_running']==255 for v in G['rows'] if 200<=v['update']<=537))
        names={m['name'] for m in G['marks']}
        self.assertTrue({'call_32F9_results_screen','results_call_2D08_ring_and_time_tally','zone_clear_advance_15CE','level_load_requested_15DE'}<=names)
        self.assertEqual((G['rows'][-1]['zone'],G['rows'][-1]['act']),(4,0))

    def test_coordinate_classes_not_silent_scaling(self):
        constants={v['name']:v for v in M['constants']}
        self.assertEqual(constants['placement/pole']['relationship'],'WORLD')
        self.assertEqual(constants['trigger']['relationship'],'PLAYER_DIST')
        self.assertEqual(constants['boss-specific clear gate']['relationship'],'WORLD')
        self.assertEqual(constants['state20 completion']['relationship'],'EDGE')
        self.assertEqual(constants['arena camera']['relationship'],'LOCKED_CAMERA')

    def test_assertion_count(self):
        self.assertEqual(D['assertions'],894975)
        self.assertEqual(sum(v['assertions'] for v in D.values() if isinstance(v,dict) and 'assertions' in v),894975)
        self.assertEqual(G['assertions'],8)

    def test_warning_exact_bytes(self):
        source=D['reconciliation']['sources'][0]
        self.assertEqual((source['bank'],source['file']),(30,0x7A77F))
        self.assertEqual([(v['cpu'],v['bytes']) for v in source['instructions']],
                         [('0xA77F','cd3404'),('0xA782','c9')])

    def test_all_warning_calls_contact_and_immunity(self):
        for case in D['reconciliation']['warning']['rows']:
            self.assertEqual(len(case['rows']),24)
            for row in case['rows']:
                self.assertEqual(bool(row['pending']),not case['hurt'])
                self.assertEqual(row['rings_after_consumer'],0x47 if case['hurt'] or case['inv'] or case['power']==6 else 0)
                self.assertEqual(row['frame'],14 if (row['call']-1)%8<4 else 13)

    def test_warning_closed_geometry(self):
        self.assertEqual(M['warning_contact']['sonic_closed_contact'],{'x':[-12,12],'y':[-16,24]})
        self.assertEqual(len(D['reconciliation']['warning']['geometry']),4)

    def test_selector_z_flag_boundary(self):
        x=D['reconciliation']['selector']
        self.assertEqual(sum(x['counts'].values()),65536*9)
        for row in x['boundaries']:
            special=row['body_vy']>=0 and row['body_y']==430
            self.assertEqual(row['helper_z'],special)
            self.assertEqual(row['requested'],6 if row['player_y']<row['body_y'] or special else 7)

    def test_camera_release_both_directions_before_gate(self):
        replay=G['camera_release_replay']
        self.assertGreater(replay['clear_gate_update'],replay['release_update'])
        moves=[p['candidate'][0]-p['camera'][0] for p in replay['phases'] if p['phase']=='after_camera_before_player']
        self.assertTrue(any(v>0 for v in moves) and any(v<0 for v in moves))
        self.assertEqual(moves[0],0) # release occurs after this update's camera phase
        for p in replay['phases']:
            if p['phase']=='after_release_before_clear_gate':self.assertEqual(p['limits'],[replay['retained_left'],3584])

    def test_camera_no_player_speed_cap_and_limits(self):
        x=D['reconciliation']['camera']
        self.assertEqual((x['routine'],x['max_right_step'],x['max_left_step']),(0x5832,7,-7))
        self.assertTrue(any(v['candidate_delta']==-8 for v in x['rows']))
        for row in x['rows']:
            expected=row['camera']+row['candidate_delta']
            self.assertEqual(row['limited_candidate'],expected if 2954<=expected<3584 else row['camera'])

    def test_fullgame_phase_counter_is_recorded(self):
        self.assertTrue(all('counter' in row and 'pre_driver' in row for row in G['rows']))
        self.assertTrue(all('counter' in p for p in G['phases']))
        self.assertEqual(G['fixture_reconstruction']['counter_frame_offsets'],
                         sorted({(v['counter']-v['frame'])&255 for v in G['rows']}))

    def test_driver_y_is_distinct_from_physics(self):
        self.assertTrue(any(row['player'][1]==430 and row['pre_driver']['player'][1]==398 for row in G['rows']))
        self.assertTrue(any(p['phase']=='after_player_before_objects' and p['player'][1]==398 for p in G['phases']))
        self.assertEqual(D['reconciliation']['reconciliation_base'],M['reconciliation_base'])


@unittest.skipUnless(ROM,'verified ROM unavailable')
class RomTests(unittest.TestCase):
    def test_runtime_and_manifest_regenerate(self):
        actual=B.build(ROM)
        self.assertEqual(actual,D)
        self.assertEqual(B.implementation_manifest(actual),M)

    def test_fullgame_regenerates(self):
        self.assertEqual(F.build(ROM),G)

    def test_region_hashes(self):
        for v in S['regions']:
            self.assertEqual(hashlib.sha256(ROM[v['file'][0]:v['file'][1]]).hexdigest(),v['sha256'])


if __name__=='__main__':unittest.main()

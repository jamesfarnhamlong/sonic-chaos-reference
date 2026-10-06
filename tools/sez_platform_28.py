"""Original-ROM SEZ type $28 state 7 and state 5 no-sag audit. No POC writes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import rom as R
import platform_spike_collision as P
import sez_object_census as C
import level_package as L

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/rom-cache/sez/platform-28-runtime.json'
S = P.SLOT
COUNTS = {}


def check(group, actual, expected):
    COUNTS[group] = COUNTS.get(group, 0) + 1
    if actual != expected:
        raise AssertionError((group, actual, expected))


def lab(rom, param=0x86, aux=24, world=(1024, 512)):
    q = P.platform_lab(rom, param, aux, world, flags4=2 if param == 0x86 else 0)
    # ObjectLab's initial parked player is outside $8908's keepalive range.
    # Restore the numeric type for these explicitly controlled callbacks.
    q.m[S] = 0x28
    q.snap = bytes(q.m[0xC000:0xE000])
    return q


def state(q):
    return dict(type=q.m[S], current=q.m[S+1], requested=q.m[S+2],
                x=q.obj16(0x11), y=q.obj16(0x14), vx=R.s16(q.obj16(0x16)), vy=R.s16(q.obj16(0x18)),
                latch=q.m[S+0x31], tick=q.m[S+0x30], period=q.m[S+0x37],
                sag=q.m[S+0x35], sag_release=q.m[S+0x33], contact=q.m[S+0x21],
                owner=q.m[0xD3C0], px=q.o.word(0xD511), py=q.o.word(0xD514),
                pvx=R.s16(q.o.word(0xD516)), pvy=R.s16(q.o.word(0xD518)),
                f3=q.m[0xD503], f22=q.m[0xD522], frame=q.m[S+6],
                dx=R.s16(q.obj16(0x23)))


def placements(rom):
    return [dict(act=act, **row) for act, data in C.decode_records(rom).items()
            for row in data['records'] if row['type_id']=='0x28']


def creator(rom):
    act=L.build_act(rom,'sez1',C.F.ACTS['sez1'])
    sweep=C.platform_parameter_sweep(rom,act)
    check('creator',sweep['parameters_run'],56)
    for p,row in sweep['by_parameter'].items():
        v=int(p,16)
        check('creator',row['state'],C.platform_state(v))
        check('creator',row['axis_flag_25'],255 if v&128 else 0)
    rows=[]
    for p in (0x83,0x84,0x04,0x86):
        raw=P.platform_record(1024,512,p,24 if p==0x86 else 106)
        o,m,step,_=C.C.object_lab_init(rom,act,{'type_id':'0x28','raw_bytes':raw.hex()})
        def fields():
            return {f'0x{k:02X}':m[S+k] for k in range(64)}
        created=fields()
        o.position(1024,452)  # inside keepalive but outside trigger
        step(); initialized=fields()
        step(); entered=fields()
        check('creator',m[S],40)
        check('creator',m[S+2],C.platform_state(p))
        q=lab(rom,p,24 if p==0x86 else 106)
        check('creator',q.m[S+0x31],0)
        check('creator',q.obj16(0x3a),1024)
        check('creator',q.obj16(0x3c),512)
        rows.append(dict(parameter=p,created_fields=created,initializer_fields=initialized,
                         script_entered_fields=entered,after_two_updates=state(q),
                         fields={f'0x{k:02X}':q.m[S+k] for k in
                                 (3,4,8,9,0x1e,0x1f,0x23,0x24,0x25,0x26,0x27,
                                  0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3a,0x3b,0x3c,0x3d,0x3e,0x3f)}))
    return dict(exhaustive=sweep,sez_parameters=rows,
                fixture_note='Creator uses original $80EB. After script load, controlled lab restores type $28 and active flags; initial far-player $8908 deletion is excluded from initialization fields.')


def trigger_sweep(rom):
    q=lab(rom)
    vectors=[]
    speeds=(-1,0,1,256)
    for vy in speeds:
        for dy in range(-25,30):
            for dx in range(-26,27):
                q.reset()
                q.player(1024+dx,512+dy,vy=vy)
                q.callback()
                triggered=(-24<=dx<=24 and -16<=dy<=24)
                check('trigger_rectangle',q.obj16(0x11),1025 if triggered else 1024)
                check('trigger_rectangle',q.m[S+0x31],int(triggered))
                supported=triggered and vy>=0 and P.model_contact(dx-1,dy)==1
                check('trigger_postmove_support',q.m[0xD3C0],9 if supported else 0)
                check('trigger_postmove_support',q.o.word(0xD511),1024+dx+int(supported))
                if vy in (-1,0) and dx in (-25,-24,0,24,25) and dy in (-17,-16,-14,-1,0,24,25):
                    vectors.append(dict(input=dict(dx=dx,dy=dy,vy=vy),output=state(q)))
    # All 52 player states, attack/floor flags and owner choices: trigger precedes support gates.
    for cur in range(52):
        for f3 in (0,1,2,3,0x40,0x80):
            for floor in (0,2):
                for owner in (0,9,7):
                    q.reset();q.player(1024,498,vy=0,cur=cur,req=cur,f3=f3,d3c0=owner,f22=floor)
                    q.callback()
                    check('trigger_player_gates',q.obj16(0x11),1025)
                    check('trigger_player_gates',q.m[0xD3C0],owner if owner else 9)
                    check('trigger_player_gates',q.m[0xD503],f3)
                    check('trigger_player_gates',q.m[0xD522],floor)
                    check('trigger_player_gates',(q.m[0xD501],q.m[0xD502]),(cur,cur))
    return dict(vectors=vectors,grid=dict(dx=[-26,26],dy=[-25,29],vy=list(speeds)),
                trigger='Pre-move closed rectangle |dx|<=24, -16<=dy<=24; any of contact bits 0..3 starts motion. No speed/floor/attack/state/owner gate.',
                support='Post-move triangular top test; pre-move dx is replaced by dx-1 on first motion update; relative Y speed and owner apply only to support.')


def movement_sweep(rom):
    timelines=[]
    for aux in (1,2,24,28,48,106,255,0):
        q=lab(rom,aux=aux)
        n=16*(aux or 256)
        vector=[]
        for u in range(1,2*n+4):
            # Side trigger does not sag. Subsequent synthetic player stays nearby but out of contact.
            q.player(q.obj16(0x11)+24 if u==1 else q.obj16(0x11),q.obj16(0x14) if u==1 else q.obj16(0x14)-60,vy=0)
            q.frame()
            expected_x=1024+u if u<=n else 1024+2*n-u if u<=2*n else 1024
            check('movement',q.obj16(0x11),expected_x)
            check('movement',R.s16(q.obj16(0x16)),-256 if n<=u<2*n else 256)
            check('movement',q.m[S+0x31],1 if u<n else 2 if u<2*n else 0)
            check('movement',q.obj16(0x14),512)
            check('movement',q.m[S+6],1)
            if u in (1,2,n-1,n,n+1,2*n-1,2*n,2*n+1,2*n+3): vector.append(dict(u=u,**state(q)))
        # A new side overlap restarts on the next callback with no timer reset needed.
        q.player(1048,512);q.frame()
        check('restart',q.obj16(0x11),1025)
        check('restart',q.m[S+0x31],1)
        timelines.append(dict(aux1=aux,leg_updates=n,range_x_origin_relative=[0,n],vectors=vector))
    return timelines


def state5_comparison(rom):
    traces={}
    for aux in (0,24,28,48,106,255):
        for p in (4,132):
            q=lab(rom,p,aux)
            ys=[]
            for u in range(1,22):
                q.player(1024,q.obj16(0x14)-14,vx=123,vy=456)
                q.frame();ys.append(q.obj16(0x14)-512)
                sag=[1,2,3,4,5,6,7,8,8,7,6,5,4,3,2,1,0,0,0,0,0][u-1] if p==132 else 0
                check('state5_sag',ys[-1],sag)
                check('state5_sag',q.obj16(0x11),1024)
                check('state5_sag',q.o.word(0xD514),q.obj16(0x14)-14)
                check('state5_sag',(q.o.word(0xD516),q.o.word(0xD518)),(123,456))
            traces[f'{p:02X}/{aux:02X}']=ys
    # State 5 pre-sag triangle and signed gate, identical for both parameters.
    for p in (4,132):
        q=lab(rom,p,106)
        for dy in range(-18,3):
            for dx in range(-26,27):
                for vy in (-1,0,1,256):
                    q.reset();q.player(1024+dx,512+dy,vy=vy);q.callback()
                    support=P.model_support(dx,dy,0,vy)
                    check('state5_support',q.m[0xD3C0],9 if support else 0)
        for flags in (0x40,0x42):
            q.reset();q.m[S+4]=flags;q.player(1024,498,vy=256);q.callback()
            check('state5_sleep',q.m[0xD3C0],0)
            check('state5_sleep',q.obj16(0x14),512)
        q.reset();q.player(1024,498,vy=256);q.callback()
        check('state5_sleep_resume',q.m[S+0x35],1 if p==132 else 0)
        q.m[S+4]|=64;q.callback()
        check('state5_sleep_resume',q.m[S+0x35],1 if p==132 else 0)
        q.m[S+4]&=~64;q.player(1024,q.obj16(0x14)-14,vy=256);q.callback()
        check('state5_sleep_resume',q.m[S+0x35],2 if p==132 else 0)
    return dict(traces=traces,result='Bit 7 is the weight-sag enable, not a movement-axis selector. $04 stays fixed; $84 sags vertically 8 px and returns. Aux1 does not control state-5 movement.',
                support_order='gate $8866 -> owner/top $8814 -> sag $88FB -> carry $88A0',
                velocity='Both initial X/Y speeds zero, no horizontal/vertical travel oscillator; support preserves player velocities.')


def lifecycle_sweep(rom):
    q=lab(rom)
    vectors=[]
    for axis,limit in (('x',640),('y',672)):
        for d in (-limit-1,-limit,-limit+1,0,limit-1,limit,limit+1):
            q.reset();q.player(1024+(d if axis=='x' else 0),512+(d if axis=='y' else 0))
            q.o.cpu.ix=S;q.o.bank(2,30);q.o.call(0x8908)
            expected=0xfe if abs(d)>=limit else 0x28
            check('keepalive',q.m[S],expected)
            vectors.append(dict(axis=axis,distance=d,type=q.m[S]))
    # Motion is independent of camera and bit6, even while asleep.
    for camera in ((0,0),(500,100),(2000,900)):
        for flags in (2,0x42):
            q.reset();q.m[S+4]=flags;q.m[S+0x31]=1
            q.o.word(0xD174,camera[0]);q.o.word(0xD176,camera[1]);q.player(1024,452)
            q.callback()
            check('sleep_motion',q.obj16(0x11),1025)
            check('sleep_motion',q.m[S+0x30],15)
            q.reset();q.m[S+4]=flags;q.player(1024,498,vy=256);q.callback()
            check('sleep_trigger_support',q.obj16(0x11),1025)
            check('sleep_trigger_support',q.m[0xD3C0],9)
    return dict(keepalive_vectors=vectors,sleep='State7 sets keepalive at script entry, even before trigger. Its callback ignores bit6: motion, counters, contact and sag continue asleep. Generic lifecycle still updates bit6/SAT eligibility.',
                deletion='Original $8908 marks $FE if |platformX-playerX|>=640 OR |platformY-playerY|>=672. It then returns to the callback (not an immediate callback abort). Cleanup releases the placement token, so recreation starts from decoded origin.',
                camera_scan=C.scan_code(rom,30,[0x87E2],'sez_platform_state7'))


def extra_boundaries(rom):
    q=lab(rom)
    for aux in range(256):
        q=lab(rom,aux=aux)
        for latch,vx,expected_latch in ((1,256,2),(2,-256,0)):
            q.reset();q.m[S+0x31]=latch;q.m[S+0x30]=1;q.m[S+0x37]=1
            q.o.word(S+0x16,vx);q.player(1024,452);q.callback()
            check('all_aux_reversal',q.m[S+0x37],aux)
            check('all_aux_reversal',q.m[S+0x30],16)
            check('all_aux_reversal',R.s16(q.obj16(0x16)),-vx)
            check('all_aux_reversal',q.m[S+0x31],expected_latch)
    # Shared signed velocity helper, including both-negative/fractional cases.
    gate=P.platform_gate(rom)
    check('shared_signed_gate',gate['mismatches'],0)
    COUNTS['shared_signed_gate_cases']=gate['cases']
    # State $0F uses ex=9; trigger expands through the shared extent helper, not a new state rule.
    q=lab(rom)
    for ex in (8,9):
        for dx in range(-27,28):
            for dy in (-17,-16,-1,0,24,25):
                q.reset();q.player(1024+dx,512+dy,ex=ex,cur=15 if ex==9 else 5);q.callback()
                check('extent_trigger',q.obj16(0x11),1025 if abs(dx)<=16+ex and -16<=dy<=24 else 1024)
    # The callback does not clamp X to its saved origin; corrupt/synthetic X continues the timed excursion.
    q.reset();q.o.word(S+0x11,1200);q.m[S+0x31]=1;q.player(1200,452);q.callback()
    check('no_origin_clamp',q.obj16(0x11),1201)
    # Trigger+move even if rising, but no carry; player velocities stay untouched.
    vectors=[]
    for dy in (-16,-14,-1,0,24):
        q.reset();q.player(1024,512+dy,vx=512,vy=-1024,f3=3,cur=10,req=10);q.callback()
        check('rising_trigger',q.obj16(0x11),1025)
        check('rising_trigger',q.m[0xD3C0],0)
        check('rising_trigger',(q.o.word(0xD516),R.s16(q.o.word(0xD518))),(512,-1024))
        vectors.append(dict(dy=dy,output=state(q)))
    q.reset();q.m[S+0x31]=2;q.m[S+0x30]=1;q.m[S+0x37]=1
    q.o.word(S+0x11,1025);q.o.word(S+0x16,-256);q.player(1025,498,vy=256)
    q.callback();returned=state(q)
    check('continuous_rider_restart',(q.obj16(0x11),q.m[S+0x31]),(1024,0))
    q.callback();restarted=state(q)
    check('continuous_rider_restart',(q.obj16(0x11),q.m[S+0x31]),(1025,1))
    return dict(signed_gate=gate,rising_trigger_vectors=vectors,continuous_rider_restart=[returned,restarted],
                bounds='Counter-derived displacement, not a coordinate clamp. No terrain sampling in state7 or state5. Aux1 zero wraps to 256 blocks / 4096 updates per leg (unused by SEZ).')


def make_game(rom, act):
    from sez_surfaces_rig import ZoneGame
    g=ZoneGame(rom,2,act,hooks={0x87E2:'s7',0x879A:'s5',0x690B:'terrain',0x8814:'support',
                                0x88A0:'carry',0x5DD1:'objects',0x60FB:'move',0x6328:'overlap',
                                0x5EF8:'cleanup'})
    def snap():
        out=[]
        for row in g.objs((0x28,)):
            b=0xD540+row['slot']*64
            out.append(dict(row,latch=g.m[b+0x31],tick=g.m[b+0x30],period=g.m[b+0x37],
                            sag=g.m[b+0x35],release=g.m[b+0x33],token=g.m[b+0x3e],
                            origin_x=g.s.u16(b+0x3a),origin_y=g.s.u16(b+0x3c)))
        return out
    g._snap_objs=snap
    return g


def target(row, origin):
    return next((o for o in row['o'] if o['origin_x']==origin[0] and o['origin_y']==origin[1]),None)


def compact(row, origin):
    return {k:row[k] for k in ('u','x','y','vx','vy','cur','req','f3','f22','f23','d3c0','ev')} | {'platform':target(row,origin)}


def whole_game(rom):
    games={i:make_game(rom,i) for i in (0,1)}
    out=[]
    for rec in placements(rom):
        p=int(rec['parameter'],16)
        if p not in (4,132,134): continue
        g=games[int(rec['act'][-1])-1]
        origin=(rec['world_x'],rec['world_y'])
        x,y=origin
        aux=int(rec['aux1'],16)
        # Natural placement creation, actual terrain/player updates and rider carry.
        g.begin(x,y-14,vy=256,cur=14,f3=1,floor=False,prev=0,types=(0x28,))
        rows=g.run(45)
        first=next((r for r in rows if target(r,origin) and target(r,origin)['state']==(7 if p==134 else 5)),None)
        check('whole_natural_creation',first is not None,True)
        supported=[r for r in rows if target(r,origin) and r['d3c0']==target(r,origin)['slot']+2]
        check('whole_natural_support',bool(supported),True)
        for row in supported:
            check('whole_rider_snap',row['y'],target(row,origin)['y']-14)
        item=dict(act=rec['act'],index=rec['index'],origin=list(origin),parameter=p,aux1=aux,
                  natural_first_callback=compact(first,origin),natural_rider_vectors=[compact(r,origin) for r in rows[:12]],
                  supported_updates=len(supported))
        if p==134:
            # Full cycle on original placement/layout/scheduler. Park player above the mover after
            # initial contact, at EVERY player update boundary; no terrain/map/platform writes.
            active={'follow':True}
            engine=g._engine_hook
            def follow(mm):
                engine(mm)
                if not g.recording or mm.cpu.ix!=0xD500 or not active['follow']: return
                objs=g._snap_objs()
                o=next((o for o in objs if o['origin_x']==x and o['origin_y']==y and o['state']==7),None)
                if o and o['latch']:
                    mm.w16(0xD511,o['x']);mm.w16(0xD514,o['y']-60)
                    mm.w16(0xD516,0);mm.w16(0xD518,0)
                    g.m[0xD3C0]=0;g.m[0xD522]=0;g.m[0xD503]=1
                    for a in (0xD174,0xD284):mm.w16(a,max(0,o['x']-104))
                    for a in (0xD176,0xD286):mm.w16(a,max(8,o['y']-100))
            g.hook(0x64FA,follow)
            g.begin(x,y-14,vy=256,cur=14,f3=1,floor=False,prev=0,types=(0x28,))
            n=16*aux
            rows=g.run(2*n+14)
            start=next(r['u'] for r in rows if target(r,origin) and target(r,origin)['x']==x+1)
            for u in range(1,2*n+1):
                row=rows[start+u-2];o=target(row,origin)
                check('whole_cycle',o is not None,True)
                check('whole_cycle',o['x'],x+u if u<=n else x+2*n-u)
                check('whole_cycle',o['vx'],-256 if n<=u<2*n else 256)
                check('whole_cycle',o['latch'],1 if u<n else 2 if u<2*n else 0)
            item['whole_cycle']=dict(fixture='Natural mapped creation and original layout/scheduler; player/camera parked nearby above mover at each player-engine boundary after first trigger; no platform writes.',
                                     first_motion_update=start,leg_updates=n,
                                     vectors=[compact(rows[start+u-2],origin) for u in (1,2,n-1,n,n+1,2*n-1,2*n)],
                                     updates_checked=2*n)
            # Restore history independence: first case must be identical after a long full-cycle run.
            active['follow']=False
            g.hook(0x64FA,engine)
            g.begin(x,y-14,vy=256,cur=14,f3=1,floor=False,prev=0,types=(0x28,))
            again=g.run(45)
            canonical=lambda rr:[compact(r,origin) for r in rr[:12]]
            check('restore_history_independence',canonical(again),item['natural_rider_vectors'])
        out.append(item)
    # Extra scenarios share the same natural SEZ1 #4 placement and original terrain.
    g=games[0]
    origin=(1584,96)
    g.begin(1584,82,vy=256,cur=14,f3=1,floor=False,prev=0,types=(0x28,))
    jumped=g.run(35,padf=lambda u,f:16 if 12<=u<15 else 0)
    jump_rows=[r for r in jumped if r['vy']<0]
    check('whole_jump',bool(jump_rows),True)
    first_jump=jump_rows[0]
    check('whole_jump',first_jump['d3c0'],0)
    check('whole_jump',target(first_jump,origin)['latch'],1)
    out.append(dict(scenario='natural_jump_off',vectors=[compact(r,origin) for r in jumped[10:18]]))
    # Sleeping motion: camera displaced only after natural trigger; player stays above the object.
    engine=g._engine_hook
    def sleep(mm):
        engine(mm)
        if not g.recording or mm.cpu.ix!=0xD500: return
        o=next((o for o in g._snap_objs() if (o['origin_x'],o['origin_y'])==origin and o['latch']),None)
        if o and len(g.rows)>=8:
            mm.w16(0xD511,o['x']);mm.w16(0xD514,o['y']-60);mm.w16(0xD518,0)
            for a in (0xD174,0xD284):mm.w16(a,o['x']+400)
            g.m[0xD3C0]=0;g.m[0xD522]=0;g.m[0xD503]=1
    g.hook(0x64FA,sleep)
    g.begin(1584,82,vy=256,cur=14,f3=1,floor=False,prev=0,types=(0x28,))
    asleep=g.run(26)
    sleeping=[r for r in asleep if target(r,origin) and target(r,origin)['f4']&64]
    moving_sleep=[r for r in sleeping if target(r,origin)['latch']]
    check('whole_sleep',len(moving_sleep)>5,True)
    for row in moving_sleep:
        prev=asleep[row['u']-2]
        check('whole_sleep_motion',target(row,origin)['x'],target(prev,origin)['x']+1)
    out.append(dict(scenario='sleep_during_motion',fixture='Camera only moved 400 px right of platform at each player-update boundary; player parked nearby above it. Original lifecycle sets bit6.',
                    vectors=[compact(r,origin) for r in asleep[7:14]]))
    # Delete a moving natural platform through its own player-distance gate, then recreate.
    def away_return(mm):
        engine(mm)
        if not g.recording or mm.cpu.ix!=0xD500:return
        n=len(g.rows)
        if n==12:g.e._place(mm,3000,700,0,0)
        if 12<=n<28:
            mm.w16(0xD511,3000);mm.w16(0xD514,700);mm.w16(0xD518,0)
        if n==28:g.e._place(mm,1584,36,0,0)
        if n>=28:
            mm.w16(0xD511,1584);mm.w16(0xD514,36);mm.w16(0xD518,0)
        if n>=12:g.m[0xD3C0]=0;g.m[0xD522]=0;g.m[0xD503]=1
    g.hook(0x64FA,away_return)
    g.begin(1584,82,vy=256,cur=14,f3=1,floor=False,prev=0,types=(0x28,))
    restored=g.run(48)
    absent=[r['u'] for r in restored[15:28] if target(r,origin) is None]
    recreated=[r for r in restored[28:] if target(r,origin) and target(r,origin)['state']==7]
    check('whole_recreation',bool(absent),True)
    check('whole_recreation',bool(recreated),True)
    for row in recreated:
        o=target(row,origin)
        check('whole_recreation',(o['x'],o['y'],o['latch'],o['tick'],o['period']),(1584,96,0,16,24))
    out.append(dict(scenario='delete_and_recreate',fixture='Player/camera teleport at update boundaries 12 -> (3000,700), 28 -> (1584,36); player parked out of contact after return.',
                    absence_updates=absent,vectors=[compact(restored[i],origin) for i in (11,12,13,15,27,28,31,36,47)]))
    g.hook(0x64FA,engine)
    return out


def contract():
    return dict(
        parameter_decoding=dict(state='13 if (p & 127) in (5,11) else (p & 63)+1',
                                sag_enable='p bit7 -> +$25=$FF, else 0',bit6='p bit6 -> +$26=$FF, else 0'),
        initialization=dict(origin_words={'x':58,'y':60},extent=[16,16],
                            fields={'0x30':16,'0x31':0,'0x33':0,'0x35':0,'0x34':'aux1','0x37':'aux1',
                                    '0x36':'(p & 63)+1','0x32':'((slot-$D500)>>6)+1',
                                    '0x23/24':0,'0x38/39':0,'0x1E/1F/27':0},
                            flags='Initializer sets +$03 bit7. Placement flags/aux bases come from original creator; $86 script sets +$04 bit1 before its first callback.'),
        state7=dict(parameter=134,state=7,bank=30,callback_cpu='0x87E2',callback_file='0x787E2',
                    script_cpu='0x84A9',frame=1,initial_velocity_8_8=[256,0],
                    aux1='Blocks of 16 moving callbacks per leg; byte zero wraps to 256 blocks. No coordinate-limit comparison.',
                    latch={'0':'waiting for contact','1':'outbound +1 px/update','2':'return -1 px/update'},
                    trigger=dict(anchor='pre-move',x_abs_lte='playerExtentX+16 (24 ordinarily, 25 in state $0F)',y_inclusive=[-16,24],
                                 predicate='($6328 contact & 15)!=0; top, underside and either side all trigger',
                                 exclusions='No player-speed, state, floor, attack or platform-owner gate; platform +$03 bit7 bypasses the shared hurt/contact-bit6 gate.'),
                    timeline=['$8908 player-distance removal test (even waiting)',
                              'If latch=0: shared overlap; no overlap returns before movement/support/counter. On overlap set latch=1.',
                              '$8662: move once using incoming X speed; compute integer X delta; support/sag/carry if player Y speed nonnegative, otherwise release support.',
                              '$8925: decrement +$30; on zero reload16 and decrement +$37; on zero reload aux1 and negate X velocity via $0437->$62F7.',
                              'After move/reversal: negative X speed selects latch2; nonnegative speed preserves latch1 but converts latch2 to0.'],
                    travel=dict(outbound='originX .. originX+16*(aux1 or 256)',returning='back to originX',
                                bounds_kind='object-origin-relative displacement, counter-derived, no clamp',
                                first_motion='same callback/update as overlap trigger',
                                reversal='after moving on the final callback of each leg; next callback moves in new direction',
                                stop='Final return move resets latch0. A rider still overlapping on the next callback immediately retriggers.',
                                leave='Leaving/jumping after trigger does not stop the timed excursion.',
                                terrain='No platform terrain probes or projection; objects pass through terrain. Player still receives ordinary terrain processing first.',
                                y='Y speed remains zero; only shared sag moves Y 0..8 px.'),
                    lifecycle=dict(generic='Keepalive bit1 disables generic lifetime deletion from first state7 script entry, even before contact. Generic lifecycle still sets bit6.',
                                   sleep='No bit6 early return in state7/$8662: waiting trigger, movement and support still run asleep. No reinitialization on wake.',
                                   own_delete={'x_abs_gte':640,'y_abs_gte':672,'relationship':'PLAYER_DIST','type':254},
                                   deletion_order='$8908 marks FE but the same callback continues; cleanup occurs in a later scheduler pass.',
                                   recreation='FE cleanup zeros D400[token-1] and slot; mapped recreation starts at canonical placement with counters/latch reset.'),
                    presentation='Frame1 throughout; no state7-specific sound, animation or facing changes. Sag follows shared +$25 dispatcher.'),
        state5=dict(parameters=[4,132],state=5,bank=30,callback_cpu='0x879A',callback_file='0x7879A',frame=1,
                    velocity_8_8=[0,0],axis_variant_result='Sag enable only; no orthogonal movement variant.',
                    no_sag_parameter=4,sag_parameter=132,sag_offsets=[1,2,3,4,5,6,7,8,8,7,6,5,4,3,2,1,0],
                    aux='Aux1 is initialized into +$34/37 but state5 does not use the travel counters.',
                    order='bit6 early-return -> signed gate $8866 -> owner/top support -> optional sag -> carry',
                    lifecycle='Generic mapped lifecycle, no script-set keepalive; sleep returns before contact/sag/release. Wake keeps existing sag fields; recreation resets them.'),
        shared_support=dict(geometry=dict(dy_inclusive=[-16,-1],abs_dx_lte='playerExtentX+abs(dy)',extent='Ordinary player8x24; platform16x16'),
                            owner='D3C0 is zero or this platform id; a different owner blocks support, not state7 trigger.',
                            speed='signed platformVy<=playerVy; state7 horizontal path is specifically playerVy>=0',
                            tested_anchor='state7 post-move/pre-sag; state5 pre-sag',
                            carry=dict(player_y='platformY-(extentY-2) = platformY-14 after sag',player_x='add integer X delta computed before reversal',velocity='preserved'),
                            release='Shared $8843 clears mirrored side bits and releases D3C0 only if this platform owns it; sag returns toward0.',
                            flags='Object contact writes D521; shared merge feeds D523 on the next player pass. Support alone does not set D522 terrain-floor or change player movement flags/state.',
                            scheduling='Camera -> player engine/terrain -> object scheduler/contact/carry -> periodic placement scan; next player update registers landing from merged support.',
                            shoes='No platform-specific state or D532 selector: Spring Shoes $12/Rocket $11 use the same gate/geometry. Their player updates may supply different Y speeds or inherited flags; shared routines do not replace their state.'),
        viewport=[dict(kind='WORLD',value='canonical placement anchors'),
                  dict(kind='object-origin-relative',value='16*aux1 travel displacement and 0..8 sag; never scale'),
                  dict(kind='PLAYER_DIST',value='strict retention |dx|<640 and |dy|<672; never scale'),
                  dict(kind='lifecycle/EDGE',value='Generic mapped create/awake/sleep/SAT bands use viewport edges; state7 keepalive exception remains'),
                  dict(kind='GameMaker adapter only',value='Existing post-wake retention policy may be applied explicitly where appropriate; it does not replace state7 player-distance removal. No new widescreen rule proposed.')],
        unresolved=['No remaining ROM runtime dependency for these SEZ variants. POC integration and Windows acceptance remain pending.',
                    'Whole-game evidence uses the approximate SMS harness with guarded snapshot restore; no hardware-emulation fidelity claim.'])


def build(rom, include_game=True):
    P.check_rom(rom)
    COUNTS.clear()
    out=dict(format=1,rom_sha256=R.SHA256,rom_bytes=len(rom),research_base='6e169d78f0918c74db4f12d89e410dc50423e3e8',
             scope='SEZ type $28 parameters $86/$04; $83/$84 controls. Research only; no POC changes.',
             evidence=['decoded data','byte-verified assembly','source-traced behavior','controlled routine result','emulated original update'],
             placements=placements(rom),contract=contract(),creator=creator(rom),trigger_oracles=trigger_sweep(rom),
             movement_oracles=movement_sweep(rom),state5_comparison=state5_comparison(rom),
             lifecycle=lifecycle_sweep(rom),boundary_oracles=extra_boundaries(rom))
    out['source_regions']=[{k:v for k,v in row.items() if k!='first_16_bytes'} for row in P.routine_table(rom)
                           if row['name'].startswith(('platform_','overlap_','object_move_','merge_flags_','player_update_'))]
    for name,bank,a,b in (
            ('state_scripts',30,0x8439,0x8585),('placement_creator',28,0x80EB,0x813E),
            ('x_velocity_negate',1,0x62F7,0x630B),('player_distance_x_y',1,0x61A5,0x61D6),
            ('visibility_lifetime',1,0x61E1,0x6276),('placement_cleanup',1,0x5EF8,0x5F17),
            ('object_scheduler',1,0x5DD1,0x5E70)):
        off=P.rom_of(bank,a)
        out['source_regions'].append(dict(name=name,bank=bank,cpu=f'0x{a:04X}',rom_offset=f'0x{off:05X}',
                                          end_cpu_exclusive=f'0x{b:04X}',length=b-a,sha256=hashlib.sha256(rom[off:off+b-a]).hexdigest()))
    out['whole_game']=whole_game(rom) if include_game else None
    out['assertions']=dict(COUNTS)
    out['assertion_total']=sum(COUNTS.values())
    return out


def dumps(data):
    return json.dumps(data,indent=2)+'\n'


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('rom',type=Path)
    a.add_argument('--check',action='store_true')
    a.add_argument('--controlled-only',action='store_true')
    args=a.parse_args()
    rom=R.load(args.rom)
    data=build(rom,include_game=not args.controlled_only)
    if args.check:
        old=json.loads(OUTPUT.read_text(encoding='utf-8'))
        if args.controlled_only:
            for k,v in data.items():
                if k not in ('whole_game','assertions','assertion_total'):check('cache_'+k,v,old[k])
        else:check('cache',data,old)
        print('OK: platform cache matches ROM;',data['assertion_total'],'assertions')
    elif args.controlled_only:
        print(json.dumps(data['assertions']),data['assertion_total'])
    else:
        OUTPUT.write_text(dumps(data),encoding='utf-8',newline='\n')
        print('wrote',OUTPUT,data['assertion_total'],'assertions')


if __name__=='__main__':
    main()

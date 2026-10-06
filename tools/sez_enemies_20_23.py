"""SEZ S4: original-ROM enemy $20/$23 runtime and whole-game oracles."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import rom as R
import sez_object_census as C
import platform_spike_collision as P
from oracle import Oracle

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/rom-cache/sez/enemies-20-23-runtime.json'
S = P.SLOT
COUNTS = {}

def check(group, got, want):
    COUNTS[group] = COUNTS.get(group, 0) + 1
    if got != want:
        raise AssertionError((group, got, want))

def placements(r):
    return [dict(act=a, **p) for a,d in C.decode_records(r).items()
            for p in d['records'] if p['type_id'] in ('0x20','0x23')]

def lab(r, rec=None, t=0x20):
    rec = rec or next(p for p in placements(r) if int(p['type_id'],16)==t)
    act = C.vram_for_act(r, int(rec['act'][-1])-1)
    o,m,step,origin = C.C.object_lab_init(r,act,rec)
    return o,m,step,origin

def state(o,m,b=S):
    return dict(type=m[b],current=m[b+1],requested=m[b+2],frame=m[b+6],duration=m[b+7],
                flags3=m[b+3],flags4=m[b+4],x=o.word(b+0x11),y=o.word(b+0x14),
                x_fraction=m[b+0x10],y_fraction=m[b+0x13],vx=R.s16(o.word(b+0x16)),vy=R.s16(o.word(b+0x18)),
                timer=m[b+0x1e],contact=m[b+0x21],floor=m[b+0x22],extent=[m[b+0x2c],m[b+0x2d]],
                callback=o.word(b+12),token=m[b+0x3e],parameter=m[b+0x3f])

def controlled_placements(r):
    out=[]
    for rec in placements(r):
        o,m,step,origin=lab(r,rec)
        initial=state(o,m)
        created_fields={f'0x{k:02X}':m[S+k] for k in range(64)}
        vectors=[]; transitions=[]; previous=None; trace=[]
        for u in range(1,421):
            # Exclude lifecycle: creator marks asleep, whereas actual post-callback
            # visibility clears it. This fixture exercises the active callback.
            m[S+4]&=~64
            step(); row=dict(u=u,**state(o,m));trace.append(row)
            if row['requested']!=previous:
                transitions.append(row);previous=row['requested']
            if u<=4 or u in (10,11,20,21,32,48,64,65,66,87,88,89,128,129,256,420):vectors.append(row)
        check('placements',len(trace),420)
        check('placements',m[S],int(rec['type_id'],16))
        check('orientation',bool(m[S+4]&16),rec['type_id']=='0x20')
        normalized=[dict(v,x=v['x']-origin[0],y=v['y']-origin[1]) for v in trace]
        out.append(dict(act=rec['act'],index=rec['index'],initial=initial,creator_fields=created_fields,vectors=vectors,transitions=transitions,
                        relative_signature_sha256=hashlib.sha256(json.dumps(normalized,sort_keys=True).encode()).hexdigest(),
                        trace_sha256=hashlib.sha256(json.dumps(trace,sort_keys=True).encode()).hexdigest(),
                        updates=420,final=trace[-1],fixture='Original creator, act layout, engine and callbacks; player out of contact; sleep cleared before each callback; lifecycle excluded.'))
    return out

def contact_oracles(r):
    out={}
    for t,ex,ey,label in ((0x20,7,20,'0x20'),(0x23,9,26,'0x23'),(0x23,7,20,'0x23_frame2')):
        o=Oracle(r);m=o.mem;o.cpu.ix=S;o.bank(2,12);m[0xD12B]=12
        o.word(S+0x11,1024);o.word(S+0x14,512)
        m[S+0x2c],m[S+0x2d]=ex,ey
        vectors=[]
        for px in (8,9):
            m[0xD52C],m[0xD52D]=px,24
            for dy in range(-ey-2,27):
                for dx in range(-ex-px-2,ex+px+3):
                    m[S+3]=m[0xD503]=m[S+0x21]=m[0xD520]=m[0xD521]=0
                    o.position(1024+dx,512+dy);o.call(0x6328)
                    want=P.model_contact(dx,dy,px,24,ex,ey)
                    check('contact_geometry',m[S+0x21],want)
                    if dx in (-ex-px-1,-ex-px,0,ex+px,ex+px+1) and dy in (-ey-1,-ey,-1,0,24,25):
                        vectors.append(dict(player_extent_x=px,dx=dx,dy=dy,contact=want,D520=m[0xD520],D521=m[0xD521]))
        reactions=[]
        m[0xD52C]=8
        for f3 in range(256):
            for inv in (0,6):
                for dx,dy in ((0,-ey),(0,24),(-ex-8,0),(ex+8,0)):
                    m[S]=t;m[S+1]=m[S+2]=3 if t==32 else 1
                    m[S+3]=0;m[S+4]=16 if t==32 else 0;m[S+0x21]=0
                    m[S+0x3e]=7;m[S+0x3f]=1;m[0xD406]=t
                    m[0xD503]=f3;m[0xD532]=inv;m[0xD520]=m[0xD521]=m[0xD3B0]=0
                    m[0xD292]=0;m[0xD29D:0xD2A0]=bytes(3)
                    o.position(1024+dx,512+dy);o.call(0x6328)
                    nibble=m[S+0x21]&15
                    if nibble:o.call(0x5F3D)
                    defeated=not bool(f3&64) and bool(inv==6 or f3&2)
                    check('contact_defeat',m[S],15 if defeated else t)
                    check('defeat_token',m[S+0x3e],0 if defeated else 7)
                    check('defeat_occupancy',m[0xD406],t)
                    if defeated:check('score',list(m[0xD29D:0xD2A0]),[0x10,0,0])
                    if f3 in (0,1,2,3,0x40,0x42,0x80,0x82):
                        reactions.append(dict(f3=f3,d532=inv,dx=dx,dy=dy,type=m[S],contact=nibble,
                                              D520=m[0xD520],D521=m[0xD521],token=m[S+0x3e],occupancy=m[0xD406],score_bcd=list(m[0xD29D:0xD2A0])))
        out[label]=dict(extent=[ex,ey],normal_box=dict(x=[-ex-8,ex+8],y=[-ey,24]),
                              state_0f_box=dict(x=[-ex-9,ex+9],y=[-ey,24]),vectors=vectors,reactions=reactions)
    return out

def source(r):
    out={}
    for t in (0x20,0x23):
        sc=C.C.state_scripts(r,t)
        out[f'0x{t:02X}']=dict(state_table=C.C.public_script(sc),code=C.type_scan(r,t))
    out['shared_helpers']={name:dict(file_offset=start,bank=start//0x4000,cpu=start if start<0x8000 else 0x8000+start%0x4000,
                                    bytes=end-start,sha256=hashlib.sha256(r[start:end]).hexdigest())
        for name,start,end in [('move',0x60FB,0x612B),('landing_flags',0x614E,0x6168),('overlap',0x6328,0x640B),
                ('defeat',0x5F3D,0x5F84),('visibility',0x61E1,0x626D),('scheduler',0x5DD1,0x5E70),
                ('engine',0x64FA,0x65AF),('object_terrain',0x7725,0x77B1),('object_floor',0x77CB,0x7857),
                ('floor_projection',0x70E7,0x715F),('smoke',0x31FC9,0x32101)]}
    return out

def whole_game(r):
    from sez_surfaces_rig import ZoneGame
    out=[]
    for ai in (0,1):
        g=ZoneGame(r,2,ai,hooks={0x5DD1:'objects',0x690B:'terrain',0xB100:'20init',0xB119:'20walk',
                    0xB14C:'20hop',0xB3FD:'23launch',0xB412:'23leap',0xB439:'23rest',
                    0x60FB:'move',0x6328:'overlap',0x614E:'support',0x77CB:'floor',0x48BC:'player_contact'})
        def snap():
            result=[]
            for row in g.objs((0x20,0x23,0x0f)):
                b=0xD540+row['slot']*64
                result.append(dict(row,token=g.m[b+0x3e],timer=g.m[b+0x1e],xf=g.m[b+0x10],yf=g.m[b+0x13],
                                   callback=g.s.u16(b+12),extent=[g.m[b+0x2c],g.m[b+0x2d]]))
            return result
        g._snap_objs=snap
        engine=g._engine_hook
        follow={'token':None,'origin':None}
        def park(mm):
            engine(mm)
            if g.recording and mm.cpu.ix!=0xD500 and g.m[mm.cpu.ix] in (32,35):
                g.pending.append('enemy_engine')
            if mm.cpu.ix!=0xD500 or not g.recording:return
            obj=next((v for v in snap() if v['token']==follow['token']),None)
            x,y=(obj['x'],obj['y']) if obj else follow['origin']
            # Controlled player/camera only; original creation, enemy and terrain
            # callbacks remain intact. Keep the player safely below contact.
            mm.w16(0xD511,x+60);mm.w16(0xD514,y+60)
            mm.w16(0xD516,0);mm.w16(0xD518,0)
            g.m[0xD503]=1;g.m[0xD501]=g.m[0xD502]=14;g.m[0xD522]=0
            g.m[0xD3C0]=0
            for a in (0xD174,0xD284):mm.w16(a,max(0,x-100))
            for a in (0xD176,0xD286):mm.w16(a,max(8,y-100))
        g.hook(0x64FA,park)
        for rec in [p for p in placements(r) if p['act']==f'sez{ai+1}']:
            # The natural record ordinal is the occupancy token (one based).
            follow.update(token=rec['index'],origin=(rec['world_x'],rec['world_y']))
            def apply(q):
                q.m[0xD400:0xD480]=bytes(128)
                q.m[0xD540:0xDA00]=bytes(0x4c0)
            g.begin(rec['world_x']+60,rec['world_y']+60,cur=14,f3=1,floor=False,prev=0,
                    apply=apply,types=(0x20,0x23,0x0f))
            rows=g.run(425)
            trace=[dict(u=row['u'],enemy=next((v for v in row['o'] if v['token']==rec['index']),None),events=row['ev']) for row in rows[:425]]
            first=next((v for v in trace if v['enemy']),None)
            check('whole_creation',first is not None,True)
            active=[v for v in trace if v['enemy']]
            check('whole_active_updates',len(active)>400,True)
            changes=[];prev=None
            for v in active:
                obj=v['enemy'];key=obj['req']
                if key!=prev:changes.append(v);prev=key
                check('whole_orientation',bool(obj['f4']&16),rec['type_id']=='0x20' and obj['state']!=0)
                cbname='20walk' if obj['state']==3 else '20hop' if obj['state']==4 else '23leap' if obj['state']==1 else '23rest' if obj['state']==2 else None
                if cbname and cbname in v['events']:
                    check('whole_scheduler_order',v['events'].index('objects')<v['events'].index('enemy_engine')<v['events'].index(cbname),True)
            item=dict(act=rec['act'],index=rec['index'],token=rec['index'],updates=len(trace),
                      first=first,transitions=changes,
                      vectors=[v for v in trace if v['u']<=8 or v['u'] in (32,64,65,66,88,89,128,129,256,420,425)],
                      trace_sha256=hashlib.sha256(json.dumps(trace,sort_keys=True).encode()).hexdigest(),
                      fixture='Guarded boot snapshot; original natural placement allocator and act terrain; clear object pool/occupancy at initial update boundary, then park only player/camera each player-engine entry. No enemy/map writes.')
            out.append(item)
            print(f"whole-game {rec['act']} #{rec['index']}: {len(active)} live updates",flush=True)
        # A/B/A history independence: rerun the final natural fixture after an
        # unrelated first-placement case, using the guarded restore each time.
        expected=trace
        g.begin(1232,202,cur=14,f3=1,floor=False,prev=0,apply=apply,types=(0x20,0x23,0x0f));g.run(30)
        g.begin(rec['world_x']+60,rec['world_y']+60,cur=14,f3=1,floor=False,prev=0,apply=apply,types=(0x20,0x23,0x0f))
        again=g.run(425)
        actual=[dict(u=row['u'],enemy=next((v for v in row['o'] if v['token']==rec['index']),None),events=row['ev']) for row in again[:425]]
        check('restore_history_independence',actual,expected)
    return out

def motion_terrain_oracles(r):
    o,m,step,origin=lab(r)
    # Synthetic uniform maps use real canonical block headers/profiles. Keep
    # the act's original stride and terrain decoder; don't stub terrain calls.
    m[0xC001:0xD000]=bytes(4095)
    o.position(5000,0)
    def reset(t=32,x=1024,y=512,vx=-128,vy=512):
        m[S:S+64]=bytes(64);m[S]=t;m[S+0x2c]=7 if t==32 else 9;m[S+0x2d]=20 if t==32 else 26
        o.word(S+0x11,x);o.word(S+0x14,y);o.word(S+0x16,vx);o.word(S+0x18,vy)
        o.bank(2,12);m[0xD12B]=12;o.cpu.ix=S;m[0xD503]=m[0xD532]=0
    trigger=[];landing=[]
    for block in range(256):
        m[0xC001:0xD000]=bytes([block])*4095
        for vx in (-128,128):
            reset(vx=vx);o.call(0xB18E)
            check('terrain_trigger',o.cpu.a,255 if block in (71,246,247) else 0)
            check('terrain_coordinates',o.word(0xD358),1024+(-4 if vx<0 else 4))
            check('terrain_coordinates',o.word(0xD35A),522)
            check('terrain_block',m[0xD353],block)
        reset();o.call(0x614E)
        flags=m[0xD364]
        check('landing_flags',o.cpu.a,0 if flags&192 else 255)
        landing.append(dict(block=block,flags=flags,result=o.cpu.a))
        if block in (0,71,246,247):trigger.append(dict(block=block,flags=flags,trigger=block in (71,246,247)))
    m[0xC001:0xD000]=bytes(4095)
    timer=[]
    for n in range(256):
        reset();m[S+0x1e]=n;m[S+2]=3;o.call(0xB119)
        check('timer_decrement',m[S+0x1e],(n-1)&255)
        check('timer_transition',m[S+2],4 if n==1 else 3)
        check('timer_velocity',R.s16(o.word(S+0x18)),-768 if n==1 else 512)
        check('timer_no_trigger_motion',o.word(S+0x11),1024 if n==1 else 1023)
        if n in (0,1,2,128,255):timer.append(dict(input=n,output=state(o,m)))
    # Triggered hop has no movement, identical for all three blocks.
    for block in (71,246,247):
        m[0xC001:0xD000]=bytes([block])*4095
        reset();m[S+0x1e]=128;m[S+2]=3;o.call(0xB119)
        check('early_hop',(m[S+2],m[S+0x1e],o.word(S+0x11),o.word(S+0x14),R.s16(o.word(S+0x18))),(4,127,1024,512,-768))
    # Gravity and landing use updated signed speed, after integration. Uniform
    # solid block: landing gate depends on flags, even away from its profile.
    gravity=[]
    for t,cb,gravity_step in ((32,0xB14C,32),(35,0xB412,16)):
        for block in (0,71):
            m[0xC001:0xD000]=bytes([block])*4095
            for vy in range(-gravity_step-2,gravity_step+3):
                reset(t=t,vy=vy,vx=-128 if t==32 else -256);m[S+2]=4 if t==32 else 1
                o.call(cb)
                new=vy+gravity_step;land=block==71 and new>=0
                check('gravity_transition',m[S+2],(3 if t==32 else 2) if land else (4 if t==32 else 1))
                check('gravity_speed',R.s16(o.word(S+0x18)),512 if land and t==32 else new)
                if t==32:check('hop_landing_no_projection',o.word(S+0x14),(512*256+vy)//256)
                if vy in (-gravity_step-1,-gravity_step,-1,0,1):gravity.append(dict(type=t,block=block,initial_vy=vy,output=state(o,m)))
    # Sleep freezes only $20 callback. Engine animation still advances.
    sleep=[]
    for t in (32,35):
        oo,mm,ss,_=lab(r,t=t);ss();mm[S+4]&=~64;ss()
        mm[S+4]|=64;before=state(oo,mm);ss();after=state(oo,mm)
        check('sleep_animation',after['duration'],before['duration']-1)
        if t==32:check('sleep_callback',(after['x'],after['y'],after['timer']),(before['x'],before['y'],before['timer']))
        else:check('sleep_callback',after['x'],before['x']-1)
        sleep.append(dict(type=t,before=before,after=after))
    animation=[]
    for t,st,period,frames in ((32,3,20,[1]*10+[2]*10),(32,4,8,[1]*4+[2]*4),(35,2,23,[2]*12+[1]*4+[2]*6+[1])):
        oo,mm,ss,_=lab(r,t=t);ss();mm[S+1]=mm[S+2]=st;mm[S+0xe]=mm[S+0xf]=0
        got=[];extents=[]
        # Engine-only fixture isolates frame cadence from contact/terrain.
        for u in range(period*2 if t==32 else period):
            oo.bank(2,12);mm[0xD12B]=12;oo.cpu.ix=S;oo.call(0x64FA)
            got.append(mm[S+6]);check('animation_cadence',mm[S+6],frames[u%period])
            extent=[mm[S+44],mm[S+45]];extents.append(extent)
            check('animation_extent',extent,[9,26] if t==35 and mm[S+6]==1 else [7,20])
        animation.append(dict(type=t,state=st,frames=got,extents=extents))
    # $20 has no parameter reader. Exhaustively replay identical coordinates,
    # including terrain-triggered hops, under every possible parameter byte.
    ref=None;parameter_hash=None
    rec=next(p for p in placements(r) if p['type_id']=='0x20')
    for p in range(256):
        raw=bytearray.fromhex(rec['raw_bytes']);raw[6]=p
        rr=dict(rec,raw_bytes=raw.hex());oo,mm,ss,_=lab(r,rr)
        rows=[]
        for u in range(180):
            mm[S+4]&=~64;ss();row=state(oo,mm);row.pop('parameter');rows.append(row)
        if ref is None:ref=rows;parameter_hash=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
        check('parameter_equivalence',rows,ref)
    unusual=[]
    # Canonical floor dispatch is shared but depends on block/profile. Record
    # every block at every foot row with real sampler/projection/dispatch.
    for block in range(256):
        m[0xC001:0xD000]=bytes([block])*4095
        rows=[]
        for footrow in range(32):
            reset(y=512+footrow-18);m[S+0x22]=0
            o.call(0x77CB)
            dx=R.s16(o.word(S+0x11)-1024)
            floor=bool(m[S+0x22]&2)
            check('floor_x_handler',dx,(-256 if block==240 else 256) if floor and m[0xD364]&31==14 else 0)
            check('floor_preserves_velocity',(R.s16(o.word(S+0x16)),o.word(S+0x18)),(-128,512))
            rows.append(dict(footrow=footrow,dx=dx,dy=R.s16(o.word(S+0x14)-(512+footrow-18)),floor=floor))
        unusual.append(dict(block=block,flags=m[0xD364],rows=rows))
    return dict(trigger_vectors=trigger,timer_vectors=timer,landing_blocks=landing,gravity_boundary_vectors=gravity,
                animation_vectors=animation,unusual_terrain_floor=unusual,
                sleep_vectors=sleep,parameter_equivalence=dict(parameters=list(range(256)),updates_each=180,
                 signature_sha256=parameter_hash,excluded_field='+$3F parameter; all other observed runtime fields identical'))

def lifecycle_oracles(r):
    vectors=[]
    for t in (32,35):
        o,m,step,_=lab(r,t=t);step();m[S+4]&=~64;step()
        for axis in ('x','y'):
            for d in range(-130,386):
                m[S]=t;m[S+1]=3 if t==32 else 1;m[S+4]=16 if t==32 else 0;m[S+0x3e]=7
                o.word(S+0x11,1024+(d if axis=='x' else 0));o.word(S+0x14,1024+(d if axis=='y' else 0))
                o.word(0xD174,1024);o.word(0xD176,1024);o.cpu.ix=S;o.call(0x61E1)
                delete=d<-96 or d>=352;sleep=delete or d<-32 or d>=288
                check('lifecycle_delete',m[S],254 if delete else t)
                check('lifecycle_sleep',bool(m[S+4]&64),sleep)
                if d in (-129,-128,-97,-96,-33,-32,-1,0,255,256,287,288,351,352,383,384):
                    vectors.append(dict(type=t,axis=axis,relative=d,type_after=m[S],asleep=bool(m[S+4]&64)))
        # Tracked cleanup releases occupancy; detached smoke cleanup doesn't.
        for token in (0,7):
            m[S]=254 if token else 255;m[S+0x3e]=token;m[0xD406]=t
            o.cpu.ix=S;o.call(0x5EF8)
            check('cleanup_occupancy',m[0xD406],0 if token else t)
    return dict(vectors=vectors,visible='Both axes [0,256); drawing height differs from lifecycle height.',
                creation='Original mapped scan $1C:$8000 once per four updates: initial fill includes inner bands; steady scrolling creates in the outer ring [-96,-32) or [288,352), subject to both-axis table classification and free slots.',
                awake='Both axes [-32,288); outside is asleep, subject to outer deletion.',
                lifetime='Both axes [-96,352); outside becomes $FE when placement token is nonzero.',
                callback_sleep={'0x20':'Animation progresses; walking/hopping movement/contact/timer pause on prior sleep bit.',
                                '0x23':'No callback sleep gate: animation/contact/movement/rest progress until deletion.'},
                keepalive=False,player_distance_removal=False,viewport='EDGE relationships, canonical 256 px X and Y lifecycle table; no player-distance deletion.',
                adapter='POC may apply the already accepted post-wake horizontal retention adapter. It is not canonical ROM behavior.')

def interaction_oracles(r):
    import player_attack_badnik as A
    shared=A.contact_handler_48bc(r)
    check('shared_player_handler',shared['model_mismatches'],0)
    COUNTS['shared_player_matrix_cases']=shared['cases']
    callbacks=[];smoke=[]
    for t in (32,35):
        for cb in ((0xB119,0xB14C) if t==32 else (0xB412,0xB439)):
            for f3 in (0,1,2,3,64,128,130):
                o,m,step,_=lab(r,t=t);step();m[S+4]&=~64;step()
                o.word(S+0x11,1024);o.word(S+0x14,512);o.word(S+0x16,-128 if t==32 else -256);o.word(S+0x18,256)
                m[S+0x10]=m[S+0x13]=0;m[S+0x1e]=128
                # $20 hopping integrates before contact; others test at old anchor.
                px=1023 if cb==0xB14C else 1024;py=513 if cb==0xB14C else 512
                o.position(px,py-10);m[0xD503]=f3;m[0xD532]=0
                o.cpu.ix=S;o.call(cb)
                eligible=not f3&64
                defeated=eligible and bool(f3&2)
                check('callback_contact',m[S],15 if defeated else t)
                # Eligible non-attack overlap takes early return too: no timer
                # decrement, gravity or floor work after shared contact.
                if eligible:
                    check('contact_early_return_timer',m[S+0x1e],128)
                    check('contact_early_return_gravity',o.word(S+0x18),256)
                callbacks.append(dict(type=t,callback=cb,f3=f3,output=state(o,m),D520=m[0xD520],D521=m[0xD521]))
        o,m,step,_=lab(r,t=t);step();m[S+4]&=~64;step()
        m[S+0x21]=1;m[0xD503]=2;m[0xD406]=t;m[S+0x3e]=7;m[0xDE04]=0
        before=bytes(m[S:S+64])
        o.cpu.ix=S;o.call(0x5F3D)
        cleared=(1,2,4,7,14,15,0x3e,0x3f)
        for off in range(64):check('conversion_fields',m[S+off],15 if off==0 else 0 if off in cleared else before[off])
        check('smoke_conversion',m[S],15)
        check('conversion_saved_frame',m[S+6],1)
        check('conversion_mirror_clear',m[S+4],0)
        check('smoke_conversion_sound',m[0xDE04],0)
        timeline=[];last=None
        for u in range(1,50):
            step();st=state(o,m);key=(st['type'],st['current'],st['frame'],m[0xDE04])
            if key!=last:timeline.append(dict(u=u,**st,sound=m[0xDE04]));last=key
            check('smoke_occupancy',m[0xD406],t)
            if m[S]==255:break
        check('smoke_terminal',m[S],255)
        check('smoke_sound',m[0xDE04],196)
        smoke.append(dict(original_type=t,timeline=timeline))
    return dict(shared_player_handler=shared,callback_vectors=callbacks,smoke=smoke,
                defeat=dict(type=15,score_decimal=10,score_bcd_little_endian=[16,0,0],parameter_after=0,token_after=0,
                  conversion_draw='Saved mapping/piece pointers and frame/art bases survive conversion, flags4 becomes0: same-update renderer draws the inherited last enemy frame without bit4 mirror. Next update type0F initializes blank frame0 and bases0; following update soundC4, then smoke frames7/8/9.',
                  occupancy='Retained: natural enemy does not recreate until act occupancy reset.',
                  sound='No immediate sound in enemy/conversion callback. Type $0F state-1 callback $03EF->$61D6 queues $C4 in $DE04 only if it is zero.',
                  cleanup='$FE dispatch -> $626D -> $FF; later $FF dispatch -> $5EF8 releases token if nonzero and zeroes slot. Converted smoke has token zero.',
                  smoke_state_table=C.C.public_script(C.C.state_scripts(r,15))))

def whole_interaction_lifecycle(r):
    from sez_surfaces_rig import ZoneGame
    g=ZoneGame(r,2,0,hooks={0x5DD1:'objects',0x48BC:'player_contact',0x5F3D:'defeat',0x6328:'overlap',
                0xB119:'20walk',0xB412:'23leap',0x61E1:'visibility',0x5EF8:'cleanup'})
    engine=g._engine_hook;oncb=g._on_callback;cfg={};target_slot=[None];injected=[False]
    def snap():
        return [dict(o,token=g.m[0xD540+64*o['slot']+0x3e]) for o in g.objs()]
    g._snap_objs=snap
    def park(mm):
        engine(mm)
        if mm.cpu.ix!=0xD500 or not g.recording:return
        n=len(g.rows);x,y=cfg['origin']
        away=cfg.get('away',False) and 12<=n<28
        if n==12 and cfg.get('away'):g.e._place(mm,3600,900,0,0)
        if n==28 and cfg.get('away'):g.e._place(mm,x+60,y+60,0,0)
        if not injected[0] or cfg.get('away'):
            mm.w16(0xD511,3600 if away else x+60);mm.w16(0xD514,900 if away else y+60)
            mm.w16(0xD516,0);mm.w16(0xD518,0);g.m[0xD503]=1;g.m[0xD522]=0
            g.m[0xD501]=g.m[0xD502]=14
            for a in (0xD174,0xD284):mm.w16(a,3500 if away else x-100)
            for a in (0xD176,0xD286):mm.w16(a,800 if away else max(8,y-100))
    def cb(mm):
        oncb(mm);b=mm.cpu.ix
        if not g.recording or b==0xD500 or g.m[b]!=cfg['type'] or g.m[b+0x3e]!=cfg['token']:return
        target_slot[0]=(b-0xD540)//64
        if cfg.get('contact') and not injected[0] and g.m[b+1]==(3 if cfg['type']==32 else 1) and not g.m[b+4]&64:
            x=mm.u16(b+0x11);y=mm.u16(b+0x14)
            mm.w16(0xD511,x);mm.w16(0xD514,y-10);mm.w16(0xD516,0);mm.w16(0xD518,0)
            g.m[0xD503]=cfg['f3'];g.m[0xD532]=cfg['d532'];g.m[0xD29A]=0x10
            g.m[0xD522]=0;injected[0]=True
    g.hook(0x64FA,park);g.hook(0x5E91,cb)
    def run(rec,**kwargs):
        cfg.clear();cfg.update(origin=(rec['world_x'],rec['world_y']),type=int(rec['type_id'],16),token=rec['index'],**kwargs)
        target_slot[0]=None;injected[0]=False
        def apply(q):
            q.m[0xD400:0xD480]=bytes(128);q.m[0xD540:0xDA00]=bytes(0x4c0)
        x,y=cfg['origin'];g.begin(x+60,y+60,cur=14,f3=1,floor=False,prev=0,apply=apply,types=(32,35,15,254,255))
        rows=g.run(55 if cfg.get('away') else 12)
        return [dict(u=v['u'],player={k:v[k] for k in ('x','y','vx','vy','cur','req','f3','f22')},events=v['ev'],
                     enemy=next((o for o in v['o'] if o['slot']==target_slot[0]),None),
                     token_enemy=next((o for o in v['o'] if o['token']==rec['index']),None)) for v in rows]
    out=[]
    for t in (32,35):
        rec=next(p for p in placements(r) if p['act']=='sez1' and int(p['type_id'],16)==t)
        for f3,inv in ((0,0),(2,0),(0,6),(64,0),(130,0)):
            rows=run(rec,contact=True,f3=f3,d532=inv)
            check('whole_contact_injected',injected[0],True)
            defeated=next((v for v in rows if v['enemy'] and v['enemy']['type']==15),None)
            check('whole_contact_conversion',defeated is not None,not bool(f3&64) and bool(f3&2 or inv==6))
            if defeated:
                check('whole_contact_token',defeated['enemy']['token'],0)
                check('whole_contact_defeat_event','defeat' in defeated['events'],True)
                check('whole_contact_order',defeated['events'].index('objects')<defeated['events'].index('defeat'),True)
            out.append(dict(type=t,scenario='contact',f3=f3,d532=inv,vectors=rows[:8]))
        rows=run(rec,away=True)
        check('whole_delete_absence',all(v['token_enemy'] is None for v in rows[17:27]),True)
        recreated=next((v for v in rows[28:] if v['token_enemy'] and v['token_enemy']['type']==t),None)
        check('whole_recreated',recreated is not None,True)
        check('whole_recreate_anchor',(recreated['token_enemy']['x'],recreated['token_enemy']['y']),cfg['origin'])
        out.append(dict(type=t,scenario='ordinary_delete_recreate',vectors=[rows[i] for i in (2,11,12,13,14,17,27,28,29,30,31,54)],
                        fixture='Only player/camera teleports at update12 away and update28 back; original lifecycle/cleanup/placement scan recreates at canonical anchor.'))
        rows=run(rec,contact=True,f3=2,d532=0,away=True)
        check('whole_defeated_not_recreated',all(v['token_enemy'] is None for v in rows[28:]),True)
        out.append(dict(type=t,scenario='defeated_no_recreate',vectors=[rows[i] for i in (2,11,13,17,28,31,54)]))
    return out

def contract():
    return {
      '0x20':dict(wake='State 0 callback $B100 initializes vx=-128, vy=512, timer128, requests3; no movement/contact. Following engine entry loads state3 and bit4=1.',
        contact_extents_by_frame={'0':[0,0],'1':[7,20],'2':[7,20]},
        parameter='All 256 values have identical callback traces at identical coordinates; +$3F never read. Natural $00/$01 are behaviorally identical.',
        walking=dict(state=3,vx_8_8=-128,vy_8_8=512,animation=[[10,1],[10,2]],
          order=['prior sleep-bit gate','pre-move $6328 contact; overlap returns through $5F3D even without defeat','timer=(timer-1)&255','if timer==0 request hop, skip terrain probe','sample anchor+(sign(vx)*4,+10); exact block in {0x47,0xF6,0xF7} requests same hop','otherwise integrate $60FB then floor $77CB'],
          hop_request=dict(state=4,vy_8_8=-768,no_move_on_trigger=True,timer_not_reset=True),ledge='No edge-turn or gravity acceleration while walking: continues left, vy remains +2. Terrain floor projection may change Y; surface $0E can teleport X by ±256.'),
        hopping=dict(state=4,animation=[[4,1],[4,2]],gravity_8_8=32,
          order=['prior sleep-bit gate','integrate X/Y','contact; overlap returns before gravity/landing','vy+=32','if updated signed vy<0 return','sample anchor+(0,+18): header bit6 or7 means land','landing requests3, vy512, timer128; no floor projection until next walking callback']),
        orientation='Bit4=1 in both visible state scripts; no facing reversal. Frame0 initialization is blank. Approved composition is bit4=1.'),
      '0x23':dict(wake='State0 callback $B3FD sets vx=-256,vy=-512,requests1; no contact/move. Next engine entry loads state1.',
        contact_extents_by_frame={'0':[0,0],'1':[9,26],'2':[7,20]},
        leaping=dict(state=1,animation=[[224,1]],vx_8_8=-256,initial_vy_8_8=-512,gravity_8_8=16,
          order=['pre-move contact; overlap returns before motion/gravity/landing','integrate X/Y','vy+=16','if updated signed vy<0 return','sample anchor+(0,+18): header bit6 or7 means land','request2, write unused +$1E=64, then same-update $77CB projection']),
        rest=dict(state=2,records=[[12,2,'contact'],[4,1,'contact'],[6,2,'contact'],[224,1,'relaunch']],
          contact_callbacks=22,relaunch='Next script record calls $B3FD once, sets velocities and requests1; following engine entry changes state. Does not wait 224 updates to relaunch.',
          period='Terrain dependent. Flat natural floor gives 65 leap callbacks +22 rest callbacks +1 relaunch callback =88; not a fixed movement timer.'),
        orientation='Natural flags bit4=0 throughout, unmirrored approved composition. No facing/reversal update.',
        unusual_terrain='Flag-only landing gate can request rest away from the true floor profile; $77CB then projects only if profile/proximity allows. No support retest in rest. No ledge turn; resumes leftward leap.'),
      'shared':dict(fixed_point='8.8 velocity added to 16.8 anchor accumulator by $60FB before gravity; no terminal-speed cap in these callbacks.',
        contact='Shared $6328 closed overlap; minimum penetration axis, vertical wins ties. Hurt bit6 suppresses overlap for ordinary enemy; blinking bit7 leaves overlap/defeat eligible but suppresses touch marker and player damage/rebound. Attack bit1 or D532==6 defeats on eligible overlap, independent of airborne bit0.',
        rebound='Next player $48BC: attacking top -> -768 (-3.0), clear floor/set airborne; bottom ->128 (+0.5) except current state9; sides preserve Y. D532==6 and bit7 suppress rebound.',
        damage='Non-attack eligible overlap queues D520; next player handler requests ordinary hurt/ring scatter if rings>0, death if none, with existing Rocket Shoes exception. Sound ring loss $A4; ordinary death $96.',
        floor='Object $77CB clears floor bit1, samples canonical block/profile, projects through $70E7, then dispatches low5 surface bits. Only $0E handler $7836 adds X=-256 for block$F0, +256 otherwise when projection set floor bit1. Ordinary surfaces never reverse vx.',
        scheduling='Player engine/callback/terrain/contact precede object scheduler. Each enemy engine loads animation before callback; post-callback visibility sets sleep for next callback. State0 initialization does not consult sleep. Active $20 walk/$23 leap/$23 rest contact before movement; $20 hop moves before contact. Conversion is immediate; smoke script initializes next object update.'),
      'unresolved':[],
      'art':'Normal frames0..2 use approved bit4=1 for20 and bit4=0 for23. Conversion briefly draws inherited20 frame with bit4=0; this composition already exists in the supplied package. No additional board generated.'}

def build(r,include_game=True):
    COUNTS.clear()
    d=dict(schema_version=1,rom_sha256=R.SHA256,rom_bytes=len(r),
           evidence=['decoded data','source-traced behavior','controlled routine result','whole-game fixture'],
           placements=placements(r),source=source(r),controlled_placements=controlled_placements(r),contact=contact_oracles(r),
           motion_terrain=motion_terrain_oracles(r),lifecycle=lifecycle_oracles(r),interaction=interaction_oracles(r),contract=contract())
    if include_game:
        d['whole_game']=whole_game(r)
        d['whole_interaction_lifecycle']=whole_interaction_lifecycle(r)
    groups={}
    for t in (32,35):
        ids={(p['act'],p['index']) for p in d['placements'] if int(p['type_id'],16)==t}
        signatures={}
        for p in d['controlled_placements']:
            if (p['act'],p['index']) in ids:signatures.setdefault(p['relative_signature_sha256'],[]).append([p['act'],p['index']])
        groups[f'0x{t:02X}']=dict(groups=signatures,coordinate_independent=len(signatures)==1)
    d['natural_signature_comparison']=groups
    d['contract']['shared']['first_active_update']='If natural creation occurs after object pass N: N+1 initializes state0 (visibility skipped); N+2 loads active script. $20 N+2 callback still sees creator sleep bit and returns, then visibility clears it: first movement/contact N+3. $23 ignores sleep: first leap/contact N+2.'
    d['assertions']=dict(COUNTS);d['assertion_total']=sum(COUNTS.values())
    return d

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--check',action='store_true');p.add_argument('--no-game',action='store_true')
    a=p.parse_args();r=R.load(a.rom);d=build(r,not a.no_game)
    if a.check:check('cache',d,json.loads(OUTPUT.read_text(encoding='utf-8')))
    else:OUTPUT.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(assertions=d['assertion_total'],placements=len(d['placements']))))

if __name__=='__main__':main()

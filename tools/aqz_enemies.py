"""AQZ A4: original-ROM type $3C/$3D contracts and controlled oracle vectors."""
import argparse
import itertools
import json
from pathlib import Path
import aqz_foundation as F
import level_package as L
import mghz_object_census as C
import sez_object_census as SC
import platform_spike_collision as P
import rom as R
from oracle import Oracle
S=P.SLOT
OUTPUT=F.OUT/'enemies-3c-3d-runtime.json'
BASE='932e091be7a80f3353abac9143b7cef151ce74a6'
COUNTS={}

def check(k,a,b):
    COUNTS[k]=COUNTS.get(k,0)+1
    assert a==b,(k,a,b)

def placements(r):
    census=json.loads((F.OUT/'object-census.json').read_text(encoding='utf-8'));out=[]
    for name,act in census['acts'].items():
        for rec in act['records']:
            if rec['type_id'] not in ('0x3C','0x3D'):continue
            row={k:rec[k] for k in ('index','zero_based_index','rom_offset','bank','cpu','raw_bytes','type_id','stored_x','stored_y','world_x','world_y','flags','parameter','aux0','aux1')}
            row['act']=int(name[-1])-1
            off=int(rec['rom_offset'],16);assert r[off:off+9]==bytes.fromhex(rec['raw_bytes'])
            out.append(row)
    assert len(out)==30
    return out

class Lab:
    def __init__(self,r,rec):
        self.o=Oracle(r);self.m=self.o.mem;self.rec=rec;self.ox,self.oy=rec['world_x'],rec['world_y'];o,m=self.o,self.m
        o.bank(2,28);m[0xDA00:0xDA09]=bytes.fromhex(rec['raw_bytes']);o.cpu.ix=o.cpu.iy=S;o.cpu.hl=0xDA00
        o.call(0x80EB,bc=0xD400+rec['index']-1)
        m[0xD500]=1;m[0xD52C]=8;m[0xD52D]=24;m[0xD297]=4;m[0xD298]=rec['act']
        o.word(0xD174,self.ox-100);o.word(0xD176,max(0,self.oy-100));o.word(0xD450,(568,788)[rec['act']])
        self.player(self.ox+100,self.oy+60);self.snap=bytes(m[0xC000:0xE000])
    def reset(self):self.m[0xC000:0xE000]=self.snap
    def player(self,x,y,f3=0,selector=0,ex=8):
        self.o.position(x,y);self.m[0xD503]=f3;self.m[0xD532]=selector;self.m[0xD52C]=ex;self.m[0xD52D]=24
        self.m[0xD520]=self.m[0xD521]=self.m[0xD3B0]=0
    def call(self,pc):
        self.o.bank(2,30);self.m[0xD12B]=30;self.o.cpu.ix=S;self.o.call(pc)
    def engine(self):self.call(0x64FA)
    def callback(self):self.call(self.o.word(S+12))
    def step(self):
        self.engine();self.callback();self.m[0xD12F]=(self.m[0xD12F]+1)&255

def state(q):
    o,m=q.o,q.m
    return dict(type=m[S],current=m[S+1],requested=m[S+2],frame=m[S+6],duration=m[S+7],flags3=m[S+3],flags4=m[S+4],
        x=o.word(S+17),y=o.word(S+20),fractions=[m[S+16],m[S+19]],vx=R.s16(o.word(S+22)),vy=R.s16(o.word(S+24)),
        counter=m[S+53],scratch=m[S+52],parameter=m[S+63],token=m[S+62],extent=[m[S+44],m[S+45]],
        contact=m[S+33],D520=m[0xD520],D521=m[0xD521],D3B0=m[0xD3B0],frame_clock=m[0xD12F],callback=o.word(S+12))

def traces(r,recs):
    out=[];signatures={}
    for rec in recs:
        q=Lab(r,rec);initial=list(q.m[S:S+64]);rows=[]
        for u in range(1,241):
            q.m[S+4]&=~64;q.step();rows.append(dict(u=u,**state(q)))
            check('natural_controlled_type',q.m[S],int(rec['type_id'],16))
        key=(rec['type_id'],rec['parameter'])
        relative=[{k:v for k,v in row.items() if k not in ('token','u')}|dict(x=row['x']-q.ox,y=row['y']-q.oy) for row in rows]
        if key in signatures:check('coordinate_independence',relative,signatures[key])
        else:signatures[key]=relative
        out.append(dict(placement=rec,creator_fields=initial,rows=rows))
    return out

def boundary_vectors(r,recs):
    c=next(x for x in recs if x['type_id']=='0x3C');d=next(x for x in recs if x['type_id']=='0x3D');out={}
    q=Lab(r,c);rows=[]
    for param in range(256):
        q.reset();q.m[S+63]=param;q.call(0x9251)
        check('3c_parameter',(q.m[S+2],q.o.word(S+20)),(1,q.oy) if param==0 else (5,q.oy+12))
    for cb,sleep,clock in itertools.product((0x926F,0x9274,0x9284),(0,64),range(256)):
        q.reset();q.m[S+44]=3;q.m[S+45]=13;q.m[S+4]=sleep;q.m[0xD12F]=clock;q.player(q.ox,q.oy);q.call(cb)
        delta={0x926F:-4,0x9274:4,0x9284:0}[cb]
        check('3c_motion_before_gate',q.o.word(S+20),q.oy+delta)
        check('3c_contact_cadence',q.m[0xD3B0],255 if not sleep and clock%2==0 else 0)
        if clock in (0,1,254,255):rows.append(dict(cb=cb,sleep=sleep,clock=clock,output=state(q)))
    out['3c_parity_sleep']=rows
    q=Lab(r,d);rows=[]
    for param in range(256):
        q.reset();q.m[S+63]=param;q.call(0x9304)
        expected=3 if param==255 else 1 if param==0 else 0
        check('3d_parameter_request',q.m[S+2],expected)
        check('3d_parameter_decrement',q.m[S+63],param if param in (0,255) else param-1)
        rows.append(dict(parameter=param,output=state(q)))
    out['3d_parameter_init']=rows
    rows=[]
    for dy,vy,counter,req,sleep in itertools.product(range(-3,4),(-256,-24,-1,0,1,24,256),(0,1,2,32,255),(1,2),(0,64)):
        q.reset();q.m[S+4]=sleep;q.m[S+2]=req;q.m[S+53]=counter;q.o.word(S+20,q.oy+dy);q.o.word(S+24,vy);q.o.word(S+22,192);q.call(0x932B)
        if sleep:want=(q.oy+dy,vy,counter,req,q.ox)
        elif counter:want=(q.oy+dy,vy,counter-1,3-req if counter==1 else req,q.ox)
        else:
            new=vy+24;y=q.oy+dy+new//256;want=(y,new,32 if new>=0 and y>=q.oy else 0,req,q.ox)
        check('3d_origin_counter_boundary',(q.o.word(S+20),R.s16(q.o.word(S+24)),q.m[S+53],q.m[S+2],q.o.word(S+17)),want)
        rows.append(dict(dy=dy,vy=vy,counter=counter,requested=req,sleep=sleep,output=state(q)))
    out['3d_origin_counter']=rows
    # No enemy water read: same callbacks with independent water/raster/clock inputs.
    rows=[]
    for rec,cb in [(c,0x926F),(c,0x9274),(c,0x9284),(d,0x932B)]:
        q=Lab(r,rec);reference=None
        for water,line,raster,clock in itertools.product((0,255),(0,568,788,65535),(0,96,192,255),(0,1,254,255)):
            q.reset();q.m[S+4]=0;q.m[0xD443]=water;q.o.word(0xD450,line);q.m[0xD132]=raster;q.m[0xD12F]=clock
            q.o.word(S+24,-512);q.o.word(S+22,192);q.call(cb);row=state(q);row.pop('frame_clock')
            if reference is None:reference=row
            check('water_visual_independence',row,reference)
        rows.append(dict(type=rec['type_id'],callback=cb,output=reference))
    out['water_controls']=rows
    return out

def animation(r,recs):
    out={}
    for t in (60,61):
        rec=next(x for x in recs if int(x['type_id'],16)==t);q=Lab(r,rec);frames=[]
        sc=C.state_scripts(r,t)
        for st in range(sc['state_count']):
            q.reset();q.m[S+1]=q.m[S+2]=st;q.m[S+14]=q.m[S+15]=0;rows=[]
            for u in range(1,161):
                q.engine();row=state(q);rows.append(row)
                check('frame_in_approved_set',row['frame'] in sc['frames'],True)
                if row['frame'] not in [x['frame'] for x in frames]:frames.append(dict(frame=row['frame'],extent=row['extent']))
            out[f'{t:02X}_state{st}']=rows
        out[f'{t:02X}_frame_extents']=sorted(frames,key=lambda x:x['frame'])
    return out

def contact(r,recs,anim):
    out={}
    for t in (60,61):
        rec=next(x for x in recs if int(x['type_id'],16)==t);q=Lab(r,rec);shapes=anim[f'{t:02X}_frame_extents'];vectors=[];reactions=[]
        for shape in shapes:
            if shape['frame']==0:continue
            ex,ey=shape['extent']
            for px,dx,dy in itertools.product((8,9),range(-ex-11,ex+12),range(-ey-2,27)):
                q.reset();q.m[S+44]=ex;q.m[S+45]=ey;q.player(q.ox+dx,q.oy+dy,ex=px);q.call(0x6328)
                check('contact_geometry',q.m[S+33],P.model_contact(dx,dy,px,24,ex,ey))
            for f3,selector,dx,dy in itertools.product(range(256),(0,6),(0,-ex-8,ex+8),(-ey,0,24)):
                q.reset();q.m[S+44]=ex;q.m[S+45]=ey;q.m[S+4]=0;q.m[0xD12F]=0;q.m[0xD400+rec['index']-1]=t
                q.player(q.ox+dx,q.oy+dy,f3,selector);q.m[0xD29D:0xD2A0]=bytes(3)
                q.call(0x9284 if t==60 else 0x932B)
                defeat=t==61 and not f3&64 and (bool(f3&2) or selector==6)
                check('contact_type',q.m[S],15 if defeat else t)
                check('defeat_token',q.m[S+62],0 if defeat else rec['index'])
                check('defeat_occupancy',q.m[0xD400+rec['index']-1],t)
                check('score_bcd',list(q.m[0xD29D:0xD2A0]),[16,0,0] if defeat else [0,0,0])
                check('forced_hurt',q.m[0xD3B0],255 if t==60 and not f3&64 else 0)
                if f3 in (0,1,2,3,64,66,128,130):reactions.append(dict(frame=shape['frame'],f3=f3,selector=selector,dx=dx,dy=dy,output=state(q),score=list(q.m[0xD29D:0xD2A0])))
            vectors.append(dict(frame=shape['frame'],extent=[ex,ey],normal=dict(x=[-ex-8,ex+8],y=[-ey,24]),state0f=dict(x=[-ex-9,ex+9],y=[-ey,24])))
        out[f'{t:02X}']=dict(geometry=vectors,reactions=reactions)
    return out

def player_outcomes(r,recs):
    rows=[]
    for t,ey in ((60,13),(61,21)):
        rec=next(x for x in recs if int(x['type_id'],16)==t);q=Lab(r,rec)
        for f3,selector,cur,(dx,dy) in itertools.product(range(256),(0,6),(5,9),((0,-ey),(0,24),(-11,0),(11,0))):
            q.reset();q.m[S+44]=3;q.m[S+45]=ey;q.m[S+4]=0;q.m[0xD12F]=0
            q.player(q.ox+dx,q.oy+dy,f3,selector);q.m[0xD501]=q.m[0xD502]=cur;q.m[0xD29A]=0x32
            q.o.word(0xD516,123);q.o.word(0xD518,77);q.call(0x9284 if t==60 else 0x932B)
            q.o.cpu.ix=0xD500;q.o.call(0x48BC)
            hurt=not f3&192 and selector!=6 and (t==60 or not f3&2)
            check('player_damage_request',q.m[0xD502],30 if hurt else cur)
            if not hurt and not f3&192 and selector!=6 and t==61 and f3&2:
                wanted=-768 if dy<0 else 128 if dy==24 and cur!=9 else 77
                check('player_rebound',R.s16(q.o.word(0xD518)),wanted)
            if f3 in (0,1,2,3,64,66,128,130):rows.append(dict(type=t,f3=f3,selector=selector,current=cur,dx=dx,dy=dy,requested=q.m[0xD502],vx=R.s16(q.o.word(0xD516)),vy=R.s16(q.o.word(0xD518)),rings=q.m[0xD29A]))
    return rows

def nonnatural_state3(r,recs):
    out=[];rec=next(x for x in recs if x['type_id']=='0x3D')
    for sleep in (0,64):
        q=Lab(r,rec);q.m[S+63]=255;q.m[S+4]=sleep;rows=[]
        for u in range(1,161):
            q.step();rows.append(dict(u=u,**state(q)))
            if q.m[S]==255:break
        check('state3_delete_first_tail_callback',(len(rows),q.o.word(S+20)),(138,q.oy))
        check('state3_upper_endpoint',rows[40]['y'],q.oy-20)
        out.append(dict(synthetic='parameterFF, not present in natural census; original local initializer/script/callbacks only',sleep=sleep,rows=rows))
    return out

def contracts():
    return dict(
        type3c=dict(parameters={'00':'initial request1; frame1; no anchor shift','01':'initial request5; Y +=12 once; frame2; same for every nonzero parameter'},
            graph={'0':'parameter0->1; nonzero->5','1':'4 calls Y-=4 ->2','2':'32 dwell calls ->3','3':'4 calls Y+=4 ->4','4':'32 dwell calls ->1','5':'4 calls Y+=4 ->6','6':'32 dwell calls ->7','7':'4 calls Y-=4 ->8','8':'32 dwell calls ->5'},
            motion='integer WORLD Y writes, fractions and velocities untouched; 16px legs,72-call cycles; no origin clamp, terrain or water input',
            contact='after movement, only awake and VBlank-owned D12F bit0==0 (increment0603/0606); 0434->630B->6328, any contact sets D3B0=FF. No defeat helper, no score, no conversion even with attack or selector6. Player-side selector6 ignores damage; attack alone does not protect against D3B0.',
            asleep='script durations/transitions and Y movement continue; contact skipped'),
        type3d=dict(parameters={'00':'initializer requests1 immediately','04':'decrement parameter on four initializer callbacks, fifth requests1','08':'eight decrement callbacks, ninth requests1','FF':'nonnatural initializer selects3, base08=70, clears mirror bit4'},
            graph={'0':'parameter countdown->1; FF->3','1':'frames1/2 alternate8 calls; gravity24/256; integrate vx+192/256, initial vy-512/256; on descending integerY>=savedOriginY set35=32','2':'same, vx-192/256, frames3/4; requested toggles1/2 when32-call counter reaches0','3':'nonnatural: -0.5Y40calls; stationary frames2/3/4/1/2/3/4 each8; +0.5Y40; nominal16-call frame1 record deletesFF on FIRST92FF callback, not after16'},
            dwell='counter>0: contact first, decrement then return without gravity/move; at1 request opposite state; next engine installs launch velocities, fractions retained. Overlap returns before decrement/movement even without defeat.',
            boundary='descending updated vy>=0 and unsigned integer WORLD Y>=saved origin+$3C/+3D; inclusive. Neither D450 nor screen waterline. No coordinate clamp; fractions/overshoot retained.',
            contact='awake, before counter/gravity/movement:6328 then5F3D on overlap. Selector6 or D503 bit1 defeats; ordinary nonattack overlap leaves D520 for next player damage. Contact freezes current motion even when not defeated.',
            defeat='type0F; reset state/request/frame timer/script pointer/flags4/token/parameter; score100 (BCD low byte10). Placement occupancy remains spent; ordinary backtracking cannot recreate until act restart.',
            asleep='active932B returns immediately: counter/gravity/movement/contact frozen, script animation advances. Initializer9304 ignores sleep and continues parameter decrement/state request. No keepalive.',
            grouping='independent per-slot parameter countdown/counter and origin; no communication with triplet neighbours, global clock or waterline'),
        player_contact='6328 closed interval, frame-specific extents; player ex8 or state0F ex9, ey24. D503 bit6 suppresses overlap. Bit7 suppresses object contact-status byte but not contact nibble/D520 or3D defeat; player48BC skips damage/rebound while blinking. Shared3D rebound on next player update: top -3, below +0.5, side none; state9 suppresses only below rebound, selector6 suppresses both. 3C forces hurt regardless attack unless selector6 or player hurt/blink suppresses player-side processing.',
        water='neither family nor called move/overlap/gravity/forced-hurt/defeat helper reads D443/D450/D131/D132. 3C alone reads D12F for contact parity. 3D origin compare and per-object counter were mischaracterized as waterline/time in A1 reconnaissance. No drag/buoyancy/raster coupling.',
        lifecycle='ordinary mapped EDGE lifecycle; callbacks precede generic61E1 visibility, so observe previous sleep flag; periodic original mapped creator; ordinary deletion FE->FF->zero releases token, fresh creation reinitializes parameter/offset/phase. 3D defeat clears token first, retaining occupancy; 3C has no defeat path. No new PLAYER_DIST/CENTER/LOCKED_CAMERA constant.',
        scheduling='player motion/water/terrain/damage then enemy script engine/callback, generic lifecycle, periodic creation, renderer; 3C moves before contact,3D contacts before motion; D520/D3B0 consumed by following player callback',
        art='approved A1 frames3C0..2 and3D0..4; direction via distinct mapping frames; no routine sets whole-sprite mirror for natural parameters; preserve original SAT compositions',
        viewport={'coordinates_and_saved_origin':'WORLD','generic_create_sleep_delete':'EDGE canonical256px'},unresolved=[])

def build(r):
    COUNTS.clear();check('rom',F.digest(r),L.ROM_SHA256);recs=placements(r)
    ani=animation(r,recs)
    v=dict(rom_sha256=L.ROM_SHA256,research_base=BASE,tool_sha256=F.digest(Path(__file__).read_text(encoding='utf-8').encode()),
        source_regions={n:F.source(r,*v) for n,v in dict(type3c=(30,0x91F1,0x9291),type3d=(30,0x9291,0x9379),forced_hurt=(0,0x630B,0x631A),gravity=(0,0x631A,0x6328),overlap=(0,0x6328,0x640B),defeat=(0,0x5F3D,0x5F84),player_contact=(0,0x48BC,0x49F7),scheduler=(0,0x5DD1,0x5F17),lifecycle=(0,0x61E1,0x6276),creator=(28,0x8000,0x813C),clock_increment=(0,0x0603,0x0607)).items()},
        scripts={f'{t:02X}':C.public_script(C.state_scripts(r,t)) for t in (60,61)},
        code_scans={f'{t:02X}':SC.type_scan(r,t)[1] for t in (60,61)},contracts=contracts(),placements=traces(r,recs),boundaries=boundary_vectors(r,recs),animation=ani,contact=contact(r,recs,ani),player_outcomes=player_outcomes(r,recs),nonnatural_state3=nonnatural_state3(r,recs))
    v['assertions']=dict(COUNTS);v['assertion_total']=sum(COUNTS.values());return v

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();v=build(L.load_rom(a.rom))
    if a.check:assert OUTPUT.read_text(encoding='utf-8')==F.dumps(v)
    else:OUTPUT.write_text(F.dumps(v),encoding='utf-8')
    print(v['assertions'],v['assertion_total'])
if __name__=='__main__':main()

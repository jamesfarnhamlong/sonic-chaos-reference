"""SEZ3 $54/$55 original-ROM scripts, routine oracles and implementation contract."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import rom as R
import sez_object_census as C
import mghz56_runtime as M
from oracle import Oracle

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'data/rom-cache/sez/boss-54-runtime.json'
S=0xD700
COUNTS={}

def check(group,got,want):
    COUNTS[group]=COUNTS.get(group,0)+1
    assert got==want,(group,got,want)

class Lab:
    def __init__(self,r):
        self.r=r
        self.rec=next(p for p in C.decode_records(r)['sez3']['records'] if p['type_id']=='0x54')
        self.o,self.m,_,self.origin=C.C.object_lab_init(r,C.vram_for_act(r,2),self.rec)
        self.m[0xD297]=2;self.m[0xD298]=2
        self.m[0xD52C]=8;self.m[0xD52D]=24
        self.o.word(0xD174,2900);self.o.word(0xD176,462)
        self.o.word(0xD280,0);self.o.word(0xD282,3840)
        self.o.word(0xD27C,8);self.o.word(0xD27E,784)
        self.m[0xDB34:0xDB40]=bytes([16]*4+[32]*4+[0]*4)
    def call(self,pc,slot=S):
        self.o.bank(2,30);self.m[0xD12B]=30;self.o.cpu.ix=slot;self.o.call(pc)
    def step(self):
        self.m[0xD135]=1;self.o.call(0x5DD1)
        self.m[0xD12F]=(self.m[0xD12F]+1)&255
    def snap(self):
        o,m=self.o,self.m
        return dict(slots=[dict(slot=b,type=m[b],state=m[b+1],requested=m[b+2],frame=m[b+6],duration=m[b+7],
            x=o.word(b+17),y=o.word(b+20),fx=m[b+16],fy=m[b+19],vx=R.s16(o.word(b+22)),vy=R.s16(o.word(b+24)),
            extent=[m[b+44],m[b+45]],flags3=m[b+3],flags4=m[b+4],hp=m[b+38],cooldown=m[b+52],
            defeated=m[b+53],drop=m[b+54],counter=m[b+30],token=m[b+62],parameter=m[b+63])
            for b in range(0xD540,0xDA00,64) if 0<m[b]<0xF0],player=M.player(o),
            camera=[o.word(0xD174),o.word(0xD176)],limits=[o.word(v) for v in (0xD280,0xD282,0xD27C,0xD27E)],
            pan=[o.word(0xD2DA),o.word(0xD2DC)],boss_active=m[0xD44E],timer_running=m[0xD2BE])

def prepare(lab,dx=0,dy=-48,attack=2,frame=1,cooldown=0,hp=8,hurt=0,inv=0,ex=8,vy=256,floor=0,terrain=0,power=0,drop=0,flags3=0):
    o,m=lab.o,lab.m
    m[S:S+64]=bytes(64);m[S]=84;m[S+1]=m[S+2]=7;m[S+3]=flags3
    m[S+38]=hp;m[S+52]=cooldown;m[S+54]=drop;m[S+6]=frame
    fr=C.C.G.parse_frame_record(lab.r,C.C.frame_pointers(lab.r,84)[1][frame]);p=fr['frame_rom']
    m[S+44]=lab.r[p+1];m[S+45]=lab.r[p+2]
    o.word(S+17,3100);o.word(S+20,580)
    m[0xD500:0xD540]=bytes(64);m[0xD500]=1;m[0xD501]=m[0xD502]=5
    m[0xD503]=attack|hurt|inv;m[0xD52C]=ex;m[0xD52D]=24;m[0xD532]=power
    m[0xD522]=floor;m[0xD523]=terrain;m[0xD29A]=0x47
    o.position(3100+dx,580+dy);o.word(0xD516,384);o.word(0xD518,vy)
    m[0xD3B0]=m[0xD3B1]=m[0xD520]=m[0xD521]=m[0xDE04]=0
    m[0xD135]=1;lab.call(0xA3D8)
    return dict(bits=m[S+33],hp=m[S+38],cooldown=m[S+52],defeated=m[S+53],requested=m[S+2],player=M.player(o))

def projected(dx,dy,bit,ex,ox,oy,terrain=0,camera=2900):
    x,y=3100+dx,580+dy
    if bit==1 and not terrain&1:y=580-oy
    if bit==2 and not terrain&2:y=604
    if bit==8 and not terrain&8 and camera+32<x:x=3100-ox-ex
    if bit==4 and not terrain&4 and x<=camera+224:x=3100+ox+ex
    return x,y

def contacts(r):
    lab=Lab(r);rows=[];geometry=[]
    for frame in (1,2,3,4,5,6,7,8,15,16):
        fr=C.C.G.parse_frame_record(r,C.C.frame_pointers(r,84)[1][frame]);p=fr['frame_rom'];ox,oy=r[p+1:p+3]
        geometry.append(dict(frame=frame,extent=[ox,oy],sonic_normal_box=[-ox-8,ox+8,-oy,24],sonic_0f_box=[-ox-9,ox+9,-oy,24]))
        for ex,dx,dy in itertools.product((8,9),range(-ox-11,ox+12),range(-oy-2,27)):
            got=prepare(lab,dx,dy,frame=frame,ex=ex)
            bit=M.overlap_model(dx,dy,ex=ex,ox=ox,oy=oy)
            x,y=projected(dx,dy,bit,ex,ox,oy)
            hit=bool(bit and bit!=2 and y<=564)
            check('geometry',got['bits'],bit)
            check('hp_geometry',got['hp'],7 if hit else 8)
            check('projection',[got['player']['x'],got['player']['y']],[x,y])
    for attack,hurt,inv,power,cd,drop,point,floor,terrain in itertools.product(
            (0,2),(0,64),(0,128),(0,6),(0,1,18),(0,255),((0,-80),(0,-24),(0,24),(-28,-24),(28,-24),(28,0)),(0,2),(0,15)):
        got=prepare(lab,*point,attack=attack,hurt=hurt,inv=inv,power=power,cooldown=cd,drop=drop,floor=floor,terrain=terrain)
        bit=0 if hurt else M.overlap_model(*point,ox=20,oy=80)
        x,y=projected(*point,bit,8,20,80,terrain)
        hit=bool(not drop and bit and bit!=2 and max(0,cd-1)==0 and y<=564)
        check('posture_hp',got['hp'],7 if hit else 8)
        check('posture_contact',got['bits'],bit)
        check('posture_sound',got['player']['sound'],182 if bit and not drop else 0)
        check('below_damage',got['player']['damage'],255 if bit==2 and floor and not drop else 0)
        check('posture_rebound',got['player']['requested'],27 if attack and bit and not drop else 5)
        rows.append(dict(attack=attack,hurt=hurt,blink=inv,power=power,cooldown=cd,drop=drop,point=list(point),floor=floor,terrain=terrain,result=got))
    health=[]
    for hp in range(9):
        got=prepare(lab,dy=-80,hp=hp);check('hp_zero',got['hp'],(hp-1)&255)
        check('hp_zero',got['requested'],4 if hp==1 else 7)
        health.append(dict(before=hp,result=got))
    first=prepare(lab,dy=-80);repeat=[dict(call=0,result=first)]
    for t in range(1,40):
        lab.o.position(3100,500);lab.call(0xA3D8)
        repeat.append(dict(call=t,hp=lab.m[S+38],cooldown=lab.m[S+52]))
    check('cooldown',[(v['call'],v.get('hp',v.get('result',{}).get('hp'))) for i,v in enumerate(repeat) if i==0 or v.get('hp')!=repeat[i-1].get('hp',repeat[i-1].get('result',{}).get('hp'))],[(0,7),(18,6),(36,5)])
    immune=[]
    for st,attack,hurt,blink,power,point in itertools.product((6,11),(0,2),(0,64),(0,128),(0,6),((0,-80),(0,24),(-28,0))):
        prepare(lab,*point,attack=attack,hurt=hurt,inv=blink,power=power,floor=2)
        o,m=lab.o,lab.m;m[S+1]=m[S+2]=st;m[S+38]=8;m[S+52]=0;m[S+4]=2
        o.word(S+24,0);o.position(3100+point[0],580+point[1]);o.word(0xD516,384);o.word(0xD518,256)
        m[0xD502]=5;m[0xD3B0]=m[0xDE04]=0
        lab.call(0xA2EA if st==6 else 0xA396)
        bit=0 if hurt else M.overlap_model(*point,ox=20,oy=80)
        check('immune_posture_hp',m[S+38],8)
        check('entry_damage',m[0xD3B0],255 if st==6 and bit and not attack else 0)
        check('entry_rebound',m[0xD502],27 if st==6 and bit and attack else 5)
        immune.append(dict(state=st,attack=attack,hurt=hurt,blink=blink,power=power,point=list(point),after=lab.snap()))
    return dict(geometry=geometry,posture_boundary_vectors=rows,immune_state_vectors=immune,health=health,repeated_contact=repeat,
        hp_rule='After solid projection, non-bottom contact and playerY <= bossY-16; attack bit is NOT an HP prerequisite. +34 decrements before test. Zero after DEC requests4 immediately and sets35=FF; initial8 needs8 hits. Starting0 wraps255 without defeat.',
        response='Attack bit D503.1 alone enables8105: top vy=-4; bottom vy=+6; right vx=+6; left vx=-6; side negates incomingvy; requests1B preservingfloor/flags. D5326 does not replace attack. Hurt D503.6 suppresses overlap unless object03.7; boss never sets03.7. Blink D503.7 does not suppress overlap/HP.',
        damage='Combat only bottom-classified AND floor bit1 queuesD3B0=FF regardless attack; other nonattack contacts project and can damage boss without hurting Sonic. State6 uses814D: any nonattack overlap queuesdamage; attackers rebound, HP unaffected.',
        feedback='B6 requested on every eligible non-drop contact even during HP cooldown; command7 flash on damaging hit only. Existing shared four-call delay/four-call flash applies with SEZ palette14.')

def children(r):
    lab=Lab(r);o,m=lab.o,lab.m;rows=[]
    for attack,hurt,inv,power,dx,dy in itertools.product((0,2),(0,64),(0,128),(0,6),range(-12,13),range(-6,27)):
        prepare(lab,dx,dy,attack=attack,hurt=hurt,inv=inv,power=power)
        m[S]=85;m[S+3]=0;m[0xD3B0]=0;o.word(S+22,0);o.word(S+24,0)
        o.position(3100+dx,580+dy)
        lab.call(0xA4A4)
        bit=0 if hurt else M.overlap_model(dx,dy,ox=2,oy=4)
        check('child_contact',bool(m[0xD3B0]),bool(bit))
        check('child_attack_inert',m[S],85)
    for asleep,parent,hp,y in itertools.product((0,64),(0,84,15),(0,8),(622,623,624,625,626,627)):
        m[S:S+64]=bytes(64);m[S]=85;m[S+1]=m[S+2]=3;m[S+4]=asleep
        m[0xD740]=parent;m[0xD766]=hp
        o.word(S+17,3100);o.word(S+20,y);o.word(S+22,-768);o.word(S+24,704);o.position(2900,500)
        lab.call(0xA4A4);check('child_threshold',m[S+2],2 if y+2>=626 else 3)
        check('child_movement',[o.word(S+17),o.word(S+20)],[3097,y+2])
        rows.append(dict(sleep=asleep,parent=parent,parent_hp=hp,y=y,after=lab.snap()))
    m[S:S+64]=bytes(64);m[S]=85;lab.call(0xA481)
    check('child_init',[m[S+2],R.s16(o.word(S+22)),R.s16(o.word(S+24))],[3,-768,704])
    m[S+63]=255;m[0xD29D:0xD2A0]=bytes(3);lab.call(0xA49D)
    check('child_smoke',[m[S],m[S+62],m[S+63],list(m[0xD29D:0xD2A0])],[15,0,0,[0,0,0]])
    return dict(boundary_vectors=rows,extents=[2,4],sonic_boxes={'normal':[-10,10,-4,24],'0f':[-11,11,-4,24]},
        velocity_8_8=[-768,704],gravity=0,contact='630B queues damage on closed6328 overlap, before movement. Attack cannot defeat55; hurt suppresses overlap, blink/invincibility handled by48BC nextplayerupdate.',
        lifetime='Independent dynamic token0; no parent lookup, no keepalive, no sleep callback gate. After movement WORLD(y)>=626 requests2; next state2 callback converts0F with no score and parameter0. Generic lifetime/sleep flags still computed.',
        states={'0':'8 blank callbacks; first init requests3, writesvx-3/vy+2.75','1':'frame17 duration8 requests2; no natural entry','2':'frame17 duration8 converts0F','3':'17/19/18/19 duration3 each; contact before movement'},
        reachable=[0,3,2],unreachable=[1])

def camera(r):
    import viewport_semantics as V
    lab=Lab(r);o,m=lab.o,lab.m;scan={};triggers=[]
    for fill in (0,1):
        xs=[]
        for sx in range(-129,386):
            m[0xD400:0xD450]=bytes(80);m[0xD700:0xD9C0]=bytes(0x2C0)
            m[0xD440]=fill;o.word(0xD174,3200-sx);o.word(0xD176,590)
            o.bank(2,28);o.call(0x8000)
            expected=V.scan_creates(sx,32,fill==0)
            check('scanner',bool(m[0xD404]),expected)
            if expected:xs.append(sx)
        scan[str(fill)]=xs
    lab=Lab(r);o,m=lab.o,lab.m
    for dx,dy in itertools.product((-161,-160,-159,0,159,160,161),(-305,-304,-303,0,303,304,305)):
        m[S+2]=1;o.position(3200+dx,622+dy);lab.call(0x9771)
        check('trigger',m[S+2],2 if abs(dx)<160 and abs(dy)<304 else 1)
        triggers.append([dx,dy,m[S+2]])
    lab=Lab(r);o,m=lab.o,lab.m;before=lab.snap();lab.call(0x974C);intro=lab.snap()
    m[o.word(S+52)]=0;lab.call(0x97C1);pan=lab.snap();lab.call(0xA291);init=lab.snap()
    check('initial',[o.word(S+17),o.word(S+20),R.s16(o.word(S+24)),m[S+38],m[S+2],m[0xD3B3],m[0xD495]],[3136,430,192,8,6,21,14])
    check('pan',pan['pan'],[2976,462]);check('pan',pan['limits'][3],462)
    gates=[]
    for x,floor in itertools.product((2975,3000,3355,3356),(0,2)):
        lab=Lab(r);o,m=lab.o,lab.m;m[S+1]=m[S+2]=5;m[S+37]=13;m[S+39]=0
        o.position(x,620);m[0xD522]=floor;lab.call(0x81BD)
        check('clear_gate',m[0xD502],32 if floor else 5)
        gates.append(dict(x=x,floor=floor,after=lab.snap()))
    return dict(scan_screen_x=scan,trigger_vectors=triggers,creator=before,shared_init=intro,pan_setup=pan,combat_init=init,clear_vectors=gates,
        baseline=dict(placement=[3200,622],target=[2976,462],settled=[2975,462],pan_rate=[1,1],trigger_strict=[160,304],
            camera_right_saved=3840,clear_requires_floor=True,clear_world_x_gate=None),
        classification={'placement':'WORLD','trigger':'PLAYER_DIST','create_sleep_delete':'EDGE','pan_target':'LOCKED_CAMERA',
            'world_y610_622_626':'WORLD','right_stop212':'EDGE(RIGHT,-44)','escape208':'EDGE(RIGHT,-48)',
            'player_clamp':'EDGE(LEFT,+16) / EDGE(RIGHT,-9)','state20_clear':'EDGE(RIGHT,+33)'})

def cycles(r):
    out={}
    for start in (6,7,8,9,10,11,12,4):
        lab=Lab(r);o,m=lab.o,lab.m;lab.call(0xA291);m[S+1]=m[S+2]=start;m[S+4]=2
        o.word(S+20,622 if start in (7,8,9,10) else 430);o.position(2980,620)
        rows=[]
        for u in range(600):
            lab.step();rows.append(dict(u=u+1,**lab.snap()))
        check('cycle_length',len(rows),600)
        events=[];old=None
        for row in rows:
            key=[(v['slot'],v['type'],v['state'],v['requested']) for v in row['slots']]
            if key!=old:events.append(row)
            old=key
        out[str(start)]=dict(updates=600,events=events,vectors=[rows[i] for i in (0,1,2,7,8,15,31,32,63,127,147,148,255,511,599)],
            sha256=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())
    return out

def boundaries(r):
    lab=Lab(r);o,m=lab.o,lab.m;rows=[]
    # Explicit callback-order and transition boundaries, including final-hit arbitration.
    for pc,st in ((0xA2EA,6),(0xA2FA,7),(0xA312,8),(0xA32A,9),(0xA339,10),(0xA396,11)):
        for y,vy,hp in itertools.product((609,610,621,622),(-24,0,24),(1,8)):
            prepare(lab,dy=-80,hp=hp);m[S+1]=m[S+2]=st;m[S+38]=hp;m[S+52]=m[S+53]=0
            m[S+4]=2;o.word(S+20,y);o.word(S+24,vy);o.word(S+22,0)
            o.position(3100,y-80);m[0xD503]=2;m[0xD523]=0;m[0xDE04]=0
            m[S+26]=100;m[0xD51A]=100
            lab.call(pc)
            row=dict(callback=pc,state=st,y=y,vy=vy,hp_before=hp,after=lab.snap())
            if st in (6,11):check('immune_state',m[S+38],hp)
            else:check('callback_hit',m[S+38],hp-1)
            if hp==1 and st in (7,8,9,10):
                # The request4 written by A3D8 may be overwritten later in SAME callback.
                expected=4
                if st==7 and R.s16(o.word(S+24))>=0:expected=5
                if st in (8,9) and o.word(S+20)>=610:expected=5
                if st==10 and o.word(S+20)>=622:expected=7
                check('final_hit_arbitration',m[S+2],expected)
            rows.append(row)
    selectors=[]
    for dx,counter,sx,px in itertools.product((-1,0,95,96,97),(0,1,2,3),(207,208,211,212),(207,208,211,212)):
        prepare(lab,dx=-100,dy=100);m[S+1]=m[S+2]=10;m[S+30]=counter
        o.word(S+20,622);o.word(S+24,0);o.word(S+22,0);o.position(3100-dx,700)
        m[S+26]=sx;m[0xD51A]=px;lab.call(0xA339)
        check('bounce_selector',R.s16(o.word(S+22)),128 if dx<96 else -128)
        check('bounce_counter',[m[S+30],R.s16(o.word(S+24))],[0,-1152] if counter+1>=3 else [counter+1,-896])
        check('escape_selector',m[S+2],11 if sx>=208 and px>=sx else 7)
        selectors.append([dx,counter,sx,px,R.s16(o.word(S+22)),R.s16(o.word(S+24)),m[S+2]])
    return dict(callback_order_final_hit=rows,bounce_escape_selectors=selectors,
        final_hit_rule='HP0 sets35=FF and request4 immediately. Later callback instructions still run: state7 nonnegative updatedvy increments4 to5; states8/9 y>=610 increment4 to5; state10 y>=622 overwrites4 with7/11. Next combat A3D8 sees35 and requests4 again, but the same transition may overwrite again. Requests5 skip explosion script; preserve this ROM arbitration rather than forcing an atomic defeat state.')

def lifecycle_feedback_allocator(r):
    lab=Lab(r);o,m=lab.o,lab.m;life=[]
    for t,keep,axis,rel in itertools.product((84,85),(0,2),(17,20),range(-129,386)):
        m[S:S+64]=bytes(64);m[S]=t;m[S+4]=keep;m[S+62]=5 if t==84 else 0
        o.word(S+17,3100);o.word(S+20,580);o.word(0xD174,3000);o.word(0xD176,480)
        o.word(S+axis,(3000 if axis==17 else 480)+rel);lab.call(0x61E1)
        outer=not -96<=rel<352
        check('lifecycle_type',m[S],(254 if t==84 else 255) if outer and not keep else t)
        check('lifecycle_sleep',bool(m[S+4]&64),not -32<=rel<288)
        if rel in (-97,-96,-33,-32,0,255,256,287,288,351,352):
            life.append(dict(type=t,keepalive=keep,axis=axis,relative=rel,after_type=m[S],asleep=bool(m[S+4]&64)))
    pal=list(r[C.L.PALETTE_DATA+14*16:C.L.PALETTE_DATA+15*16]);m[0xD48F:0xD491]=bytes(pal[13:15]);m[0xD452:0xD456]=bytes((7,0,0,0));flash=[]
    for n in range(1,11):
        o.bank(2,29);m[0xD12B]=29;o.cpu.iy=0xD452;o.call(0x8018)
        check('palette_flash',list(m[0xD48F:0xD491]),[63,63] if 4<=n<8 else pal[13:15])
        flash.append(dict(call=n,colors=list(m[0xD48F:0xD491]),command=m[0xD452],counter=m[0xD455]))
    # Exhausted command4 allocator still advances scripts. Compare the boss to an
    # unsaturated scheduler, using the same initial state and player/camera.
    alloc=[]
    for saturated in (False,True):
        lab=Lab(r);o,m=lab.o,lab.m;lab.call(0xA291);m[S+1]=m[S+2]=7;m[S+4]=2
        o.word(S+20,622);o.word(S+24,-896);o.position(2980,620)
        if saturated:
            for b in range(0xD740,0xD9C0,64):m[b]=0xF0
        rows=[]
        for n in range(28):lab.step();rows.append(lab.snap())
        check('allocator_child_count',any(v['type']==85 for row in rows for v in row['slots']),not saturated)
        alloc.append(dict(saturated=saturated,boss=[next(v for v in row['slots'] if v['slot']==S) for row in rows],
            child_vectors=[row for row in rows if any(v['type']==85 for v in row['slots'])][:3]))
    check('allocator_parent_continues',alloc[0]['boss'],alloc[1]['boss'])
    hud_failure=[]
    for tail_type in (0,0xF0):
        lab=Lab(r);o,m=lab.o,lab.m
        for b in range(0xD540,0xD940,64):m[b]=0xF0
        m[S]=84;m[0xD940]=tail_type;lab.call(0x974C)
        check('hud_failure_pointer',o.word(S+52),0xD940)
        m[S+2]=2;lab.call(0x97C1)
        check('hud_failure_wait',m[S+2],3 if tail_type==0 else 2)
        hud_failure.append(dict(tail_type=tail_type,hud_pointer=o.word(S+52),requested=m[S+2]))
    return dict(lifecycle=life,flash=flash,allocator=alloc,hud_failure=hud_failure,
        hud_failure_rule='If all16 HUD allocator slots are occupied,81A6 still saves exhausted IY=D940. State2 waits on that unrelated slot type; zero proceeds, nonzero stalls until it clears. This is canonical exhaustion behavior, not a missing subsystem.')

def static(r):
    scripts={f'0x{t:02X}':C.C.public_script(C.C.state_scripts(r,t)) for t in (84,85)}
    lab=Lab(r);rec={k:v for k,v in lab.rec.items() if k!='raw_bytes'}
    frames=sorted({f for t in (84,85) for f in C.C.state_scripts(r,t)['frames']})
    vram,_=C.vram_for_act(r,2)['vram'],None
    # Foundation builds the static art; boss selector15 replaces dynamic tiles.
    vram=bytearray(vram);cpu,dyn=C.D.dynamic_list_for_selector(r,21);C.D.apply_dynamic_entries(vram,r,dyn)
    approved=json.loads((ROOT/'data/rom-cache/sez/art-approval.json').read_text())['subjects']['0x54'];art=[]
    for f in frames:
        fr=C.C.strip_pixels(C.C.frame_record(r,84,f,0,0,bytes(vram)))
        check('approved_art',fr['images'][0]['composed_index_sha256'],approved['frame_hashes'][str(f)][0]);art.append(fr)
    regions=[]
    for name,bank,start,end in (('boss',30,0xA1DC,0xA455),('child',30,0xA455,0xA4C4),
        ('shared_intro',30,0x974C,0x9828),('shared_reaction_clear',30,0x8105,0x8212),('defeat_script',30,0x95CC,0x9624),
        ('solid_projection',0,0x5FA0,0x6065),('closed_overlap',0,0x6328,0x640B),('child_damage',0,0x630B,0x631A),
        ('scheduler',0,0x5DD1,0x5F17),('lifecycle',0,0x61E1,0x6276),('camera_pan',0,0x5956,0x5A03)):
        lo=start if start<0x8000 else bank*0x4000+start-0x8000
        hi=end if end<0x8000 else bank*0x4000+end-0x8000
        regions.append(dict(name=name,bank=bank,cpu=[start,end],file=[lo,hi],sha256=hashlib.sha256(r[lo:hi]).hexdigest()))
    return dict(placement=rec,scripts=scripts,art=dict(frames=art,dynamic_selector=21,dynamic_list_cpu=cpu,palette=14,
        approved_package='data/rom-cache/sez/art-approval.json',new_approval_required=False,orientation='unmirrored; no bit4 writes in54/55'),sources=regions)

def contract():
    return dict(state_graph=dict(boss={'0':[1],'1':[2],'2':[3],'3':[6],'6':[9],'7':[8,4,5],'8':[9,4,5],
        '9':[10,4,5],'10':[7,11,4],'11':[12,4],'12':[8],'4':[5],'5':['0F']},child={'0':[3],'3':[2],'2':['0F'],'1':[2]},
        boss_reachable=list(range(13)),child_natural_reachable=[0,2,3],child_unreachable=[1],
        note='54 state5 can convert during first callback and be absent in end-of-update samples. Final-hit same-callback request arbitration is separately locked.'),
        initialization=dict(world=[3200,622],creator_state=[0,0],flags3=0,flags4=64,bases=[0,0],parameter=0,token=5,
            combat_world=[3136,430],vx_8_8=0,vy_8_8=192,hp=8,requested=6,
            cleared_fields=[52,53,54,10,30,22,23],dynamic_selector=21,palette=14,keepalive_flag4_bit1=True),
        movement={
            '6':dict(order=['814D solid/contact','integrate','WORLD(y)>=622 ->9'],vy_8_8=192,contact_hp=False),
            '7':dict(order=['integrate','cached screenX right stop','vy+=24','A3D8','updated signedvy>=0 -> INC requested'],
                animation='two repeats of (2f3,2f4), three repeats spawn55(-16,-36,param0)+(3f3,3f4), then loop2f1,8f3,2f2,8f4'),
            '8':dict(order=['integrate','cached screenX right stop','A3D8','vy+=48','WORLD(y)>=610 -> INC requested'],animation=[[4,5],[4,7],[4,6],[4,8]]),
            '9':dict(order=['A3D8','integrate','WORLD(y)>=610 -> INC requested'],sound_entry=166,animation=[[2,15],[2,16]]),
            '10':dict(order=['A3D8','integrate','WORLD(y)>=622 bounce/select'],animation=[[2,15],[2,16]],
                bounce='increment1E; >=3 resets0 and vy=-1152 else vy=-896. vx=+128 when objectX-playerX<96 (includingnegative) else-128. CachedscreenX>=208 and cachedplayerScreenX>=cachedbossScreenX requests11 else7.'),
            '11':dict(entry_vx_8_8=0,entry_vy_8_8=-2048,order=['vy+=32','integrate','36=FF','A3D8','prior sleepbit6 ->INC requested'],animation=[[4,5],[4,7],[4,6],[4,8]]),
            '12':dict(records='32 blank no-op callbacks, then vx0/vy512; first nextrecordcallback followsplayerX,36=0,requests8; no movement in that callback'),
            'right_stop':'Only nonnegativevx: cachedscreenX low byte>=212 zerosvx, AFTER integration. Leftward travel has no mirroredleftstop.',
            'terrain':'No terrain probes, gravity floor solver or D12F selector in54/55. WORLD(y) thresholds define arena motion; child can pass through terrain until626.'},
        lifecycle=dict(boss='Mapped token5; shared init setskeepalive04.1, so outerband sets sleep but never generic deletion. Init andcombat callbacks do not pause on sleep;11 uses prior sleepbit to leave flight. Defeat5 converts0F and detachesplacementtoken; occupancy staysreserved.',
            child='Dynamic token0, no keepalive. Generic awake[-32,288), outer[-96,352) on BOTH axes at256; beyondouter setsFF and scheduler cleanup later. Sleep flag does not stopchildcallback. Verticalofftop can delete before626.',
            visible='EDGE [LEFT,RIGHT), height256 lifecycle table; renderer/display height differs. Preserve accepted generic definitions.',
            widescreen='Keep WORLD anchors/vertical thresholds and PLAYER_DIST strict constants. Camera reframing and screen208/212 relationships require explicit POC adapters; dynamic55 does not inherit mapped post-wake retention automatically.'),
        scheduling='Camera, then player/terrain, then ascending-slot object engine/callback, then visibility/lifecycle. Script children use5EE1 D700..D980 (11 slots); later allocated slots can execute the same update; earlier free slots wait until next update. HUD/bonus5E9C uses D540..D900 (16 slots). Spawn failure consumes operands and continues the parent. Frame extents are installed before callbacks; child overrides2x4. ScreenX/Y +1A/+1C are cached by renderer3FC8 (caller2240), not by61E1; callbacks read the latest renderer values, potentially stale when rendering is skipped. Sleep flags come from the previous lifecycle call. Do not replace these with fresh anchor-camera calculations.',
        support=dict(hud='12 once atshared974C via81A6; state2 waits pointedslot type0, notcameraarrival. No combat-init secondHUD.',
            explosions='State4 shared95CC: five34/parameter4 at[-8,0],[8,0],[0,-16],[-8,-24],[-8,-24]; sharedrecord/callframe-restoration script; normal fullgame explosionphase148 updates.',
            smoke='5F54 convertsboss/expired55 to0F, token0,param0; types>=50 no ordinarybadnikscore.',
            bonus='81BD floorbit1 only, noSEZworldX gate: restore savedrightlimit, leftlimit=currentcamera, releasepan, requestplayer20, allocate0Aparameter0, convertboss0F. Shared0A bonus andFFsparkles; no sign18.'),
        progression='Timer remainsrunning duringfight/defeat; floor-gatedstate20, EDGE(RIGHT,+33) sharedclear, sharedresults/progression ->zone3act0 MGHZ1. Results replacementart/audio remainsoutofscope.',
        unresolved=[],agents_candidates=['SEZ3 $54 HP gate ignores attack posture: attack bit controls rebound; post-projection height/cooldown controls HP. Child55 is independent, damage-only and uses dynamic lifecycle. Eight successful HP decrements reachzero.',
            'SEZ3 camera settles2975,462; WORLD floor thresholds610/622 and child626. Final-hit request can be overwritten later in callback; preserve documented arbitration. Clear usesfloor-only sharedbossgate and progressesMGHZ1.'])

def build(r):
    COUNTS.clear()
    data=dict(format=1,rom_sha256=hashlib.sha256(r).hexdigest(),research_base='8b7fc8aeaec6f5a57f9aa9b6a58d9f579b62514c',
        status='Research closed; Manager review/merge required; POC Windows acceptance pending',
        evidence=['decoded data','byte-verified assembly','source-traced behavior','controlled routine result','emulated original frame'],
        static=static(r),contact=contacts(r),child=children(r),arena=camera(r),boundaries=boundaries(r),cycles=cycles(r),
        lifecycle_feedback_allocator=lifecycle_feedback_allocator(r),contract=contract())
    data['assertions']=dict(COUNTS);data['assertion_total']=sum(COUNTS.values())
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--check',action='store_true');args=p.parse_args()
    data=build(R.load(args.rom))
    if args.check:assert data==json.loads(OUTPUT.read_text(encoding='utf-8'))
    else:OUTPUT.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(assertions=data['assertion_total'])))

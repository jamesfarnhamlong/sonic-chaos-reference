"""MGHZ3 $56/$57/$58: decoded scripts and original-Z80 boundary/scheduler oracles.

No ROM bytes or pixels are committed. Synthetic RAM writes occur before calls.
Run with verified local ROM; --check compares the deterministic canonical cache.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import rom as R
import level_package as L
import isometric_platform as I
import mghz_object_census as C
import mghz_object_24_2e as Q
import thz3_boss_support as B
import thz1_type18_dynamic_graphics as D
import viewport_semantics as V
from oracle import Oracle

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/rom-cache/mghz/boss-56-runtime.json'
MANIFEST = ROOT / 'data/rom-cache/mghz/boss-56-implementation-manifest.json'
SLOT = 0xD700


class Lab:
    def __init__(self, r):
        self.r = r
        self.o = o = Oracle(r)
        self.m = m = o.mem
        a = I.act_data(r, 'mghz3')
        m[0xC001:0xD000] = bytes((a['cells'] + [0]*4095)[:4095])
        o.word(0xD168, a['header']['row_offset_table_cpu'])
        o.word(0xD16A, -a['width'])
        for addr, value in ((0xD280,0),(0xD282,3584),(0xD27C,8),(0xD27E,528),
                            (0xD174,3060),(0xD176,256)):
            o.word(addr,value)
        m[0xD540:0xDA00] = bytes(0x4C0)
        rec = next(v for v in a['objects'] if v['type_id']=='0x56')
        o.bank(2,28);o.cpu.hl=int(rec['cpu'],16);o.cpu.iy=SLOT
        o.call(0x80EB,bc=0xD40B)  # record12 occupancy byte -> token12
        m[0xD297]=3;m[0xD298]=2;m[0xD52C]=8;m[0xD52D]=24
        m[0xDB34:0xDB40] = bytes([16]*4+[32]*4+[0]*4)
        o.position(3100,288)

    def call(self, pc, slot=SLOT):
        self.o.bank(2,30);self.m[0xD12B]=30;self.o.cpu.ix=slot
        self.o.call(pc)

    def step(self):
        self.m[0xD135]=1
        self.o.call(0x5DD1)
        self.m[0xD12F]=(self.m[0xD12F]+1)&255

    def snap(self, tick=0):
        o,m=self.o,self.m
        slots=[]
        for b in range(0xD540,0xDA00,64):
            if not 0<m[b]<0xF0:continue
            slots.append(dict(slot=b,type=m[b],parameter=m[b+63],state=m[b+1],requested=m[b+2],
                frame=m[b+6],timer=m[b+7],x=o.word(b+17),y=o.word(b+20),
                vx=R.s16(o.word(b+22)),vy=R.s16(o.word(b+24)),
                extent=[m[b+44],m[b+45]],hp=m[b+38],cooldown=m[b+56],
                saved_x=o.word(b+58),hud_owner=o.word(b+52),placement_token=m[b+62],flags=m[b+3],flags4=m[b+4]))
        return dict(tick=tick,slots=slots,player=player(o),camera=[o.word(0xD174),o.word(0xD176)],
            limits=[o.word(v) for v in (0xD280,0xD282,0xD27C,0xD27E)],
            pan=[o.word(0xD2DA),o.word(0xD2DC)],scroll=[m[0xD15E],m[0xD15F]],
            timer_running=m[0xD2BE],dynamic=m[0xD3B3],palette=m[0xD495])


def player(o):
    m=o.mem
    return dict(x=o.word(0xD511),y=o.word(0xD514),vx=R.s16(o.word(0xD516)),vy=R.s16(o.word(0xD518)),
        state=m[0xD501],requested=m[0xD502],flags=m[0xD503],floor=m[0xD522],
        damage=m[0xD3B0],owner=m[0xD520],contact=m[0xD521],sound=m[0xDE04],rings=m[0xD29A])


def prepare(lab,dx=0,dy=-48,attack=2,frame=1,allow=255,cooldown=0,hp=10,
            hurt=0,inv=0,ex=8,vy=256,floor=0,terrain=0,type_id=86,power=0):
    o,m=lab.o,lab.m;b=SLOT
    m[b:b+64]=bytes(64);m[b]=type_id;m[b+1]=m[b+2]=6;m[b+3]=0x80
    m[b+38]=hp;m[b+56]=cooldown;m[b+6]=frame
    fr=C.frame_pointers(lab.r,86)[1][frame];off=C.G.parse_frame_record(lab.r,fr)['frame_rom']
    m[b+44]=lab.r[off+1];m[b+45]=lab.r[off+2]
    o.word(b+17,3269);o.word(b+20,350)
    m[0xD500:0xD540]=bytes(64);m[0xD500]=1;m[0xD501]=m[0xD502]=5
    m[0xD503]=attack|hurt|inv;m[0xD52C]=ex;m[0xD52D]=24
    m[0xD522]=floor;m[0xD523]=terrain;m[0xD29A]=0x47
    m[0xD532]=power
    o.position(3269+dx,350+dy);o.word(0xD516,384);o.word(0xD518,vy)
    m[0xD3B0]=m[0xD3B1]=m[0xD520]=m[0xD521]=m[0xDE04]=0
    m[0xD293]=0
    m[0xD135]=1  # satisfy IRQ wait on the grounded-below death path; no CPU/VDP IRQ in Oracle
    lab.o.cpu.a=allow;lab.call(0xA62D)
    return dict(bits=m[b+33],hp=m[b+38],cooldown=m[b+56],requested=m[b+2],player=player(o),
                death_flag=bool(m[0xD293]&4),palette_commands=list(m[0xD452:0xD472:8]))


def overlap_model(dx,dy,ex=8,ox=16,oy=48):
    if abs(dx)>ex+ox or dy < -oy or dy>24:return 0
    return (1 if dy<0 else 2) if ex+ox-abs(dx)>=((oy+dy) if dy<0 else 24-dy) else (8 if dx<0 else 4)


def contacts(r):
    lab=Lab(r);checks=0;cases=[]
    for ex,frame in itertools.product((8,9),(1,2,3,4,5,6,11,12,13,14,15)):
        fr=C.G.parse_frame_record(r,C.frame_pointers(r,86)[1][frame])
        ox,oy=fr['raw_word_1']&255,fr['raw_word_1']>>8
        # Exhaustively execute shared projection AND the boss attack/damage branch.
        for dx,dy in itertools.product(range(-ox-ex-2,ox+ex+3),range(-oy-2,27)):
            got=prepare(lab,dx,dy,frame=frame,ex=ex)
            expected=overlap_model(dx,dy,ex,ox,oy)
            assert got['bits']==expected,(frame,dx,dy,got,expected)
            assert got['hp']==(9 if expected==1 else 10)
            checks+=2
    for allow,attack,hurt,inv,power,cd,point,floor,vy,terrain in itertools.product(
            (0,255),(0,2),(0,64),(0,128),(0,6),(0,1,8),
            ((0,-48),(0,24),(-24,0),(24,0),(0,0)),(0,2),(-256,256),(0,15)):
        # power selector is independent of this attack-bit-only branch.
        got=prepare(lab,*point,allow=allow,attack=attack,hurt=hurt,inv=inv,
                    cooldown=cd,floor=floor,vy=vy,terrain=terrain,power=power)
        before=got
        lab.m[0xD135]=1
        # Record consumer result separately; pending damage is processed next player update.
        lab.o.cpu.ix=0xD500;lab.o.call(0x48BC)
        after=player(lab.o)
        assert before['hp']==(9 if attack and allow and point==(0,-48) and cd<=1 else 10)
        assert before['death_flag']==(point in ((0,24),(0,0)) and bool(floor))
        assert bool(before['player']['damage'])==(attack==0)
        checks+=3
        # Compact representative cases; sweep digest records all results.
        cases.append([allow,attack,hurt,inv,power,cd,list(point),floor,vy,terrain,before,after])
    return dict(assertions=checks,geometry='closed intervals; minimum penetration, vertical wins ties',
                sweep_rows=len(cases),sweep_sha256=hashlib.sha256(json.dumps(cases,sort_keys=True).encode()).hexdigest(),
                cases=[v for v in cases if v[2:6]==[0,0,0,0] and v[7]==0 and v[8]==256 and v[9]==0])


def thresholds(r):
    lab=Lab(r);o,m=lab.o,lab.m;checks=0;triggers=[];bounds=[]
    for dx,dy in itertools.product((-161,-160,-159,0,159,160,161),(-305,-304,-303,0,303,304,305)):
        m[SLOT+2]=1;o.position(3269+dx,288+dy);lab.call(0x9771)
        expected=abs(dx)<160 and abs(dy)<304
        assert (m[SLOT+2]==2)==expected;checks+=1
        triggers.append([dx,dy,m[SLOT+2]])
    for vy,y,pc in itertools.product((-32768,-256,-1,0,1,256,32767),range(280,440),(0xA69F,0xA6B8)):
        o.word(SLOT+24,vy);o.word(SLOT+20,y);lab.call(pc)
        expected=vy>=0 and y>=430 if pc==0xA69F else vy<0 and y<288
        assert (o.cpu.a==255)==expected;checks+=1
        if y in (287,288,289,429,430,431):bounds.append([pc,vy,y,o.cpu.a])
    health=[]
    for n in range(11):
        got=prepare(lab,hp=10-n)
        assert got['hp']==(9-n)&255 and got['requested']==(4 if n==10 else 6)
        health.append(got);checks+=1
    first=prepare(lab,hp=10)
    repeated=[[0,first['hp'],first['cooldown']]]
    for t in range(1,26):
        # Contact repositioning is necessary: projection moves player out.
        o.position(3269,302);o.cpu.a=255;lab.call(0xA62D)
        repeated.append([t,m[SLOT+38],m[SLOT+56]])
    assert [v[0] for i,v in enumerate(repeated) if i==0 or v[1]!=repeated[i-1][1]]==[0,8,16,24]
    checks+=1
    rng=[]
    for counter in range(256):
        m[0xD12F]=counter;lab.call(0xA5FD)
        expected=8+((counter+r[0x200+counter])&1)
        assert m[SLOT+2]==expected;checks+=1;rng.append(m[SLOT+2])
    return dict(assertions=checks,triggers=triggers,vertical_bounds=bounds,health=health,
                repeated_contact=repeated,throw_selector_by_counter=rng)


def projection_guards(r):
    lab=Lab(r);rows=[];checks=0
    for camera,terrain,point in itertools.product((2980,3060,3220),range(16),((0,-40),(0,16),(-20,0),(20,0))):
        lab.o.word(0xD174,camera)
        got=prepare(lab,*point,attack=0,allow=0,terrain=terrain)
        x,y=3269+point[0],350+point[1]
        bit=overlap_model(*point)
        if bit==1 and not terrain&1:y=302
        if bit==2 and not terrain&2:y=374
        if bit==8 and not terrain&8 and camera+32<x:x=3245
        if bit==4 and not terrain&4 and x<=camera+224:x=3293
        assert [got['player']['x'],got['player']['y']]==[x,y]
        checks+=1;rows.append(dict(camera=camera,terrain_bits=terrain,point=list(point),result=got))
    return dict(assertions=checks,rows=rows,dependency='Boss directly calls complete $5FA0, including D523 terrain guards and camera+32/camera+224 side guards. No POC monitor edits made.')


def cycles(r):
    out={};checks=0
    for state in (6,7,8,9,10,11,12,4):
        lab=Lab(r);o,m=lab.o,lab.m
        # Initialization owns HP/palette/HUD; start directly after intro for cycle isolation.
        lab.call(0xA576);m[SLOT+1]=m[SLOT+2]=state
        m[SLOT+4]=2;o.word(SLOT+20,288 if state in (6,8,9,11,12,4) else 430)
        o.position(3100,350);rows=[]
        for t in range(280):
            try:lab.step()
            except RuntimeError as e:raise RuntimeError((state,t,lab.snap(t))) from e
            rows.append(lab.snap(t))
        events=[];old=None
        for row in rows:
            sig=[(v['slot'],v['type'],v['state'],v['requested']) for v in row['slots']]
            if sig!=old:events.append(row)
            old=sig
        out[str(state)]=dict(events=events,rows=rows if state==7 else None,
            trajectory_sha256=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())
        if state in (8,9):
            kid=next(v for v in rows[0]['slots'] if v['type']==87)
            assert kid['parameter']==state-8 and kid['state']==0;checks+=1
        if state==9:
            assert any(v['type']==88 for row in rows for v in row['slots']);checks+=1
    return dict(assertions=checks,rows=out,
                method='Original $5DD1 ascending-slot scheduler, stationary player/camera, D12F increment once per call; not full-game physics/IRQs.')


def child_sweeps(r):
    lab=Lab(r);o,m=lab.o,lab.m;checks=0;launch=[];gates=[]
    for t,param in itertools.product((87,88),(0,1)):
        prepare(lab,dx=-100,dy=0,type_id=t)
        m[SLOT+63]=param;o.word(SLOT+20,350)
        lab.call(0xA72D if t==87 else 0xA79A)
        row=lab.snap();launch.append(dict(type=t,parameter=param,row=row))
        assert R.s16(o.word(SLOT+22))==(-512 if t==87 and param==0 else -544)
        assert R.s16(o.word(SLOT+24))==(-112 if param==0 else 112) if t==88 else o.word(SLOT+24)==0
        checks+=2
    for sleep,counter,sx,sy in itertools.product((0,64),(0,1),(0,175,176,255),(0,119,120,255)):
        prepare(lab,dx=-100,dy=0,type_id=87);m[SLOT+4]=sleep;m[0xD12F]=counter
        m[SLOT+26]=sx;m[SLOT+28]=sy
        m[0xD29D:0xD2A0]=bytes(3)
        lab.call(0xA761)
        convert=bool(sleep) or (counter%2==0 and sx<176 and sy>=120)
        assert (m[SLOT]==15)==convert;checks+=1
        # $5F77 skips ordinary-enemy score for every type >= $50.
        assert list(m[0xD29D:0xD2A0])==[0,0,0];checks+=1
        gates.append([sleep,counter,sx,sy,m[SLOT],m[SLOT+63]])
    # No parent pointer or defeat test is read by $57/$58 movement/contact callback.
    geometry=[]
    for frame,attack,hurt,inv in itertools.product((11,12,15),(0,2),(0,64),(0,128)):
        hits=0
        fr=C.G.parse_frame_record(r,C.frame_pointers(r,86)[1][frame])
        ox,oy=fr['raw_word_1']&255,fr['raw_word_1']>>8
        for dx,dy in itertools.product(range(-ox-10,ox+11),range(-18,27)):
            prepare(lab,dx,dy,frame=frame,type_id=87,attack=attack,hurt=hurt,inv=inv)
            # Spawned children do not carry the controller's +$03 bit7.
            m[SLOT+3]=0;m[0xD3B0]=m[0xD520]=m[0xD521]=0;m[0xD12F]=1
            o.word(SLOT+22,0);o.word(SLOT+24,0)
            lab.call(0xA761)
            expected=bool(overlap_model(dx,dy,ox=ox,oy=oy)) and not hurt
            assert bool(m[0xD3B0])==expected
            assert m[SLOT]==87  # attack posture cannot defeat this projectile
            checks+=2;hits+=bool(m[0xD3B0])
        geometry.append(dict(frame=frame,attack=attack,hurt=hurt,inv=inv,damage_requests=hits))
    return dict(assertions=checks,launch=launch,removal_gates=gates,contact_geometry=geometry,
                ownership='No boss owner pointer: independent slots; parent defeat does not directly delete existing projectiles.')


def creation_camera(r):
    lab=Lab(r);o,m=lab.o,lab.m;checks=0;created={};pan=[]
    for fill in (0,1):
        xs=[]
        for sx in range(-129,386):
            m[0xD400:0xD450]=bytes(80);m[0xD700:0xD9C0]=bytes(0x2C0)
            m[0xD297]=3;m[0xD298]=2;m[0xD440]=fill
            o.word(0xD174,3269-sx);o.word(0xD176,256)
            o.bank(2,28);o.call(0x8000)
            expected=V.scan_creates(sx,32,fill==0)
            assert bool(m[0xD40B])==expected;checks+=1
            if expected:xs.append(sx)
        created[str(fill)]=xs
    lab=Lab(r);o,m=lab.o,lab.m
    for requested in (5,18):
        m[0xD502]=requested;lab.call(0x974C)
        assert m[0xD502]==(14 if requested==18 else requested);checks+=1
    # Original pan follows both axes simultaneously. Right limit is exclusive.
    o.word(0xD174,2954);o.word(0xD176,318)
    m[o.word(SLOT+52)]=0;lab.call(0x97C1)
    for t in range(112):
        x=min(3060,2954+t);y=max(256,318-t)
        o.word(0xD174,x);o.word(0xD176,y);o.word(0xD284,x);o.word(0xD286,y)
        o.cpu.ix=0xD15E
        o.call(0x5956)
        assert o.word(0xD284)==x+1 and o.word(0xD286)==max(256,y-1);checks+=1
        pan.append([t,x,y,o.word(0xD284),o.word(0xD286),o.word(0xD280),o.word(0xD282)])
    # Allocator $5EE1 has eleven slots and skips the spawn operands on exhaustion.
    saturated=Lab(r);so,sm=saturated.o,saturated.m
    for b in range(0xD700,0xD9C0,64):sm[b]=0xF0
    sm[SLOT]=86;sm[SLOT+1]=sm[SLOT+2]=9;sm[SLOT+4]=2
    saturated.step()
    assert not any(sm[b] in (87,88) for b in range(0xD540,0xDA00,64));checks+=1
    return dict(assertions=checks,scan_screen_x_by_fill=created,pan=pan,
        pan_method='Independent routine calls at explicit camera positions; returns candidate D284/D286, not a full camera commit. Full-game trace confirms final3060/256 with exclusive3061 right limit.',
        allocator='Script children: $5EE1 pool D700..D980 (11 slots); HUD/bonus: $5E9C D540..D900 (16 slots); scheduler D540..D9C0 (19 slots).')


def clear_gates(r):
    lab=Lab(r);o,m=lab.o,lab.m;rows=[];checks=0
    for x,floor in itertools.product((3355,3356,3357),(0,2)):
        prepare(lab,dx=-100,dy=0);m[SLOT+1]=m[SLOT+2]=5
        m[SLOT+37]=14;m[SLOT+39]=0;o.position(x,430);m[0xD522]=floor
        lab.call(0x81BD)
        got=player(o);expected=x>=3356 and bool(floor&2)
        assert (got['requested']==32)==expected;checks+=1
        rows.append(dict(x=x,floor=floor,type=m[SLOT],player=got,
                         right_limit=o.word(0xD282),slots=lab.snap()['slots']))
        m[0xD540:0xD700]=bytes(0x1C0)
    return dict(assertions=checks,rows=rows,gate='WORLD(playerX)>=3356 AND floor bit1; NOT the THZ floor-only gate')


def feedback(r):
    lab=Lab(r);o,m=lab.o,lab.m;rows=[]
    pal=list(r[L.PALETTE_DATA+15*16:L.PALETTE_DATA+16*16])
    m[0xD48F],m[0xD490]=pal[13],pal[14]
    m[0xD452:0xD456]=bytes((7,0,0,0))
    for n in range(1,11):
        o.bank(2,29);m[0xD12B]=29;o.cpu.iy=0xD452;o.call(0x8018)
        colors=list(m[0xD48F:0xD491])
        assert colors==([63,63] if 4<=n<8 else pal[13:15])
        rows.append(dict(call=n,command=m[0xD452],counter=m[0xD455],colors=colors,pending=m[0xD496]))
    sounds=dict(boss_music=140,fall_entry=173,landing=185,projectile_launch=190,attack_contact=182,
                grounded_below_death=150,explosion=196,clear_jingle=151,tally=180)
    sources=[]
    for sound in sorted(set(sounds.values())):
        entry=0x90E1+(sound-0x81)*2;cpu=R.u16(r,entry);off=cpu+0x4000
        sources.append(dict(id=sound,pointer_file=entry,stored_cpu=cpu,file=off,header_word=R.u16(r,off)))
    return dict(assertions=10,flash_command=7,cram_entries=[29,30],restored=pal[13:15],rows=rows,
                sounds=sounds,sound_sources=sources,
                audio_policy='Numeric requests and existing shared sound engine; no substitute audio.')


def static(r):
    a=I.act_data(r,'mghz3');rec=next(v for v in a['objects'] if v['type_id']=='0x56')
    scripts={str(t):C.state_scripts(r,t) for t in (86,87,88)}
    lab=Lab(r);initial=lab.snap();lab.call(0x974C);init=lab.snap();
    # Mark HUD owner cleared before shared camera setup.
    lab.m[lab.o.word(SLOT+52)]=0;lab.call(0x97C1);pan=lab.snap()
    # Frame and source hashes already approved in foundation; prove each reachable frame.
    vram,_=L.build_vram(r,L.art_entry(r,3,2));vram=bytearray(vram)
    dyn_cpu,dyn=D.dynamic_list_for_selector(r,22);D.apply_dynamic_entries(vram,r,dyn)
    art=[];approved=json.loads((ROOT/'data/rom-cache/mghz/art-approval.json').read_text())['subjects']['0x56']
    frames=sorted({f for sc in scripts.values() for f in sc['frames']})
    for f in frames:
        fr=C.strip_pixels(C.frame_record(r,86,f,0,0,bytes(vram)))
        if f:
            assert fr['images'][0]['composed_index_sha256']==approved['frame_hashes'][str(f)][0]
        art.append(fr)
    regions=[]
    for name,bank,start,end in (('boss_scripts_callbacks',30,0xA4C4,0xA6D7),
         ('child_scripts_callbacks',30,0xA6D7,0xA7BA),('shared_intro',30,0x974C,0x9828),
         ('shared_reaction_clear',30,0x8105,0x8212),('solid_projection',0,0x5FA0,0x6065),
         ('closed_overlap',0,0x6328,0x640B),('scheduler_allocator',0,0x5DD1,0x5F17),
         ('script_child_spawn',0,0x671F,0x67A1),('flash',29,0x83C6,0x83FE),
         ('camera_pan',0,0x5956,0x59B3),('grounded_below_death',0,0x4984,0x49C3),
         ('player_clear_request',0,0x4892,0x48BC)):
        lo=Q.file_of(bank,start);hi=Q.file_of(bank,end)
        regions.append(dict(name=name,bank=bank,cpu=[start,end],file=[lo,hi],sha256=hashlib.sha256(r[lo:hi]).hexdigest()))
    return dict(placement=rec,act=dict(width=a['width']*32,height=a['height']*32,header=a['header']),
        scripts=scripts,initial=initial,shared_init=init,shared_pan_setup=pan,
        trigger_camera_tables=C.boss_tables(r),art=dict(mapping={str(t):{k:v for k,v in C.frame_pointers(r,t)[0].items() if k!='pointer_raw'} for t in (86,87,88)},
        dynamic_selector=22,dynamic_list_cpu=dyn_cpu,loads=[dict(v,source_sha256=hashlib.sha256(r[v['source_rom']:v['source_rom']+v['tile_count']*32]).hexdigest()) for v in dyn],palette_index=15,
        palette=list(r[L.PALETTE_DATA+15*16:L.PALETTE_DATA+16*16]),frames=art,
        approval='Reachable nonblank frames match previously approved 2026-10-04 foundation board; no new composition requested.'),
        regions=regions,support=B.support_static(r))


def build(r):
    data=dict(format=1,rom_sha256=R.SHA256,research_base='7ba4d8a7bfb7f8164462fbf50db05c4b63cec0fe',
        scope=['MGHZ3 $56','$57','$58','direct support/clear dependencies'],
        evidence=['DECODED DATA','BYTE-VERIFIED ASSEMBLY','CONTROLLED ROUTINE RESULT'],
        research_only=True,poc_untouched=True,
        static=static(r),contacts=contacts(r),thresholds=thresholds(r),cycles=cycles(r),children=child_sweeps(r),clear=clear_gates(r),creation_camera=creation_camera(r),feedback=feedback(r),projection_guards=projection_guards(r))
    data['assertions']=sum(data[k]['assertions'] for k in ('contacts','thresholds','cycles','children','clear','creation_camera','feedback','projection_guards'))
    return data


def implementation_manifest(data):
    def rule(name,kind,value,source,adapter):
        return dict(name=name,relationship=kind,canonical=value,source=source,widescreen_candidate=adapter)
    return dict(format=1,rom_sha256=R.SHA256,research_base=data['research_base'],
        status='Research closed; review/merge before POC consumption; Windows gameplay acceptance pending',
        runtime='data/rom-cache/mghz/boss-56-runtime.json',fullgame='data/rom-cache/mghz/boss-56-fullgame.json',
        documentation='docs/mghz3-boss-56-audit.md',
        identities={'86':'MGHZ3 controller/body; numeric identity authoritative',
                    '87':'delayed left-moving projectile; parameter1 splits into two $58 children',
                    '88':'left-moving diagonal projectile; parameter0 up, parameter1 down'},
        placement=data['static']['placement'],state_counts={'86':13,'87':4,'88':2},
        baseline=dict(viewport_width=256,camera_target=[3061,256],settled_camera=[3060,256],
            boss_anchor=[3269,288],body_extents=[16,48],sonic_extents=[8,24],
            body_contact={'x_inclusive':[-24,24],'y_inclusive':[-48,24],'classification':'minimum penetration; vertical wins ties'},
            hp_byte_initial=10,damaging_hits_to_defeat=11,hp_underflow=255,hit_cooldown_calls=8,
            vulnerable_states=[6,7,8,9],nonvulnerable_contact_states=[10,11,12],
            clear_world_x=3356,clear_requires_floor_bit1=True,timer_stops_on_boss_defeat=False),
        dependencies=[dict(type=t,role=role,source=source) for t,role,source in (
            (18,'HUD slide-away; recreated at combat init','shared $81A6 / bank0C state table'),
            (87,'parent $56 states8/9 child','bank1E $A510/$A51C'),
            (88,'$57 parameter1 splits into params0/1','bank1E $A709'),
            (52,'five parameter4 explosion puffs','shared state4 $95CC'),
            (10,'parameter0 bonus controller and parameterFF sparkle trail','shared $81DF'),
            (15,'boss and expired-projectile conversion/poof','shared $033E -> $5F54'))],
        art=dict(approval=data['static']['art']['approval'],new_visual_approval_required=False,
                 original_approval='data/rom-cache/mghz/art-approval.json',
                 mapping_cpu=0x9861,mapping_bank=15,mapping_file=0x3D861,
                 reachable_frames=[v['frame'] for v in data['static']['art']['frames']],
                 dynamic_selector=22,loads=data['static']['art']['loads'],palette_index=15,
                 whole_bitmap_mirror=False,registration='SAT piece coordinates canonical; existing terrain-relative +(1,18) renderer/presentation adapter; collision stays at world anchor'),
        constants=[
            rule('placement/pole','WORLD',[3269,288],'bank1C:$93DB file$713DB','Keep anchor and terrain unchanged'),
            rule('trigger','PLAYER_DIST',{'strict_x_lt':160,'strict_y_lt':304},'bank1E:$97A1 row3','Do not widen'),
            rule('mapped creation','EDGE',{'left':[-96,-33],'right':[32,95]},'bank1C:$8000/$8146','Apply generic viewport bands; initial-fill exception retained'),
            rule('arena camera','LOCKED_CAMERA',[3060,256],'bank1E:$9808 row3; fixed bank:$5956','Keep baseline lock; any reframing must be explicit'),
            rule('nominal body screen X','LOCKED_CAMERA',208,'row3 pan dx -208','Equivalent at256 to RIGHT-48 or CENTER+80; intended widening is unproven. Keep WORLD anchor'),
            rule('player clamp','EDGE',{'left':16,'right':-9},'shared player edge clamp','Use full-width edge comparison; avoid SMS low-byte wrap'),
            rule('solid side projection guards','EDGE',{'left':32,'right':-32},'$6009/$6038','Preserve side-push D523 guards and edge relationship in boss contact adapter'),
            rule('body vertical turn/floor','WORLD',{'rise_strict_lt':288,'fall_inclusive_ge':430},'$A6B8/$A69F','Do not move with viewport height'),
            rule('projectile early removal screen X','EDGE',{'right':-80,'raw_lt':176},'$A771','Explicit candidate follows right edge; only on even D12F'),
            rule('projectile early removal screen Y','LOCKED_CAMERA',{'top_plus':120,'raw_ge':120},'$A778','Keep fixed vertical camera relationship; paired with screen X condition'),
            rule('projectile lifetime','EDGE',{'awake_margin':32,'outer_margin':96},'$61E1','$57/$58 are transient projectiles; no mapped-enemy QoL retention by default'),
            rule('boss-specific clear gate','WORLD',3356,'bank1E:$8200','Do not scale; restore camera limits and require grounded player'),
            rule('state20 completion','EDGE',{'right_plus':33,'raw_ge':289},'bank0C:$83ED','Reuse explicit RIGHT+33 widescreen adapter'),
            rule('state20 camera freeze','EDGE',{'right_minus':7},'shared player state20','Reuse existing viewport adapter')],
        integration_constraints=['Original ascending-slot script/callback/lifecycle ordering; child allocation can execute later slots in the same update',
            'Use attack bit D503.1; airborne status, visual frame and invincibility selector are not substitutes',
            'Controller uses full shared solid projection before attack/damage; preserve terrain/camera guards',
            'Boss hit cooldown restricts HP decrement only, not contact, sound or player rebound',
            'Independent projectiles are not killed by parent defeat',
            'No timer stop; MGHZ-specific world3356+floor gate before shared clear path',
            'Shared monitor fix and parked player presentation defects remain separate'],
        unresolved=['Windows/gameplay acceptance and choice of optional widescreen arena reframing',
                    'State10 exists but no request to it is reached from audited $56 init/combat code; preserve table without inventing a trigger',
                    'No controller-only full-fight replay; approximate VDP/IRQ harness uses update-aligned synthetic attack fixtures',
                    'Results graphics/audio integration remains the existing POC deferred shared presentation scope'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom');p.add_argument('--check',action='store_true');a=p.parse_args()
    data=build(R.load(a.rom));s=json.dumps(data,indent=2)+'\n'
    manifest=json.dumps(implementation_manifest(data),indent=2)+'\n'
    if a.check:
        assert OUTPUT.read_text(encoding='utf-8')==s,'MGHZ56 cache differs'
        assert MANIFEST.read_text(encoding='utf-8')==manifest,'MGHZ56 manifest differs'
    else:
        OUTPUT.write_text(s,encoding='utf-8');MANIFEST.write_text(manifest,encoding='utf-8')
    print(json.dumps(dict(assertions=data['assertions'],output=str(OUTPUT))))


if __name__=='__main__':main()

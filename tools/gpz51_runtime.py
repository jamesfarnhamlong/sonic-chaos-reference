"""Dedicated $51 runtime oracle. No art generation; ROM is local-only.

All synthetic writes precede a controlled routine/scheduler call or occur at
the full-game $1336 update boundary. Numeric states are decimal in JSON.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import rom as R
from oracle import Oracle
import gpz_enemy_approval as A
import gpz51_composition as C

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT/'data/rom-cache/gpz/boss-51-runtime.json'
SLOT = 0xD700

def player(o):
    m=o.mem
    return dict(x=o.word(0xD511),y=o.word(0xD514),vx=R.s16(o.word(0xD516)),
        vy=R.s16(o.word(0xD518)),state=m[0xD501],requested=m[0xD502],
        flags=m[0xD503],floor=m[0xD522],rings=m[0xD29A],
        damage=m[0xD3B0],contact_owner=m[0xD520],contact_bits=m[0xD521],
        invulnerability=m[0xD3B1],sound=m[0xDE04])

class Lab:
    def __init__(self,r,y=160,x=1500):
        self.r=r;self.o=Oracle(r);self.m=self.o.mem;o,m=self.o,self.m
        m[0xD540:0xDA00]=bytes(0x4C0)
        o.position(x,y);o.word(0xD174,1664);o.word(0xD176,96)
        m[0xD297]=1;m[0xD298]=2;m[0xD52C]=8;m[0xD52D]=24
        m[0xDB34:0xDB40]=bytes([16]*4+[32]*4+[0]*4)
        o.bank(2,28);o.cpu.hl=0x8DF6;o.cpu.iy=SLOT;o.call(0x80EB,bc=0xD418)
    def call(self,pc,slot=SLOT):
        self.o.bank(2,30);self.m[0xD12B]=30;self.o.cpu.ix=slot;self.o.call(pc)
    def step(self):self.o.call(0x5DD1)
    def snap(self,tick):
        o,m=self.o,self.m
        slots=[]
        for b in range(0xD540,0xDA00,64):
            if m[b] not in (0x51,0x34,0x12,0x0A,0x06):continue
            slots.append(dict(slot=b,type=m[b],parameter=m[b+63],state=m[b+1],
                requested_state=m[b+2],frame=m[b+6],timer=m[b+7],
                x=o.word(b+17),y=o.word(b+20),vx=R.s16(o.word(b+22)),vy=R.s16(o.word(b+24)),
                lower_support=o.word(b+52),upper_predecessor=o.word(b+54),
                phase=m[b+31],phase_counter=m[b+30],mode=m[b+50],health=m[b+38],
                mux=m[b+39],extent=[m[b+44],m[b+45]],flags=m[b+3]))
        return dict(tick=tick,slots=slots,player=player(o),camera=[o.word(0xD174),o.word(0xD176)],
            limits=[o.word(a) for a in (0xD280,0xD282,0xD27C,0xD27E)],
            pan=[o.word(0xD2DA),o.word(0xD2DC)],scroll=[m[0xD15E],m[0xD15F]],timer_running=m[0xD2BE])
    def settle(self):
        for _ in range(233):self.step()
        return self.snap(232)

def signatures(rows):
    out=[];old=None
    for row in rows:
        sig=[(v['slot'],v['type'],v['parameter'],v['state'],v['requested_state']) for v in row['slots']]
        if sig!=old:out.append(row)
        old=sig
    return out

def cycles(r):
    out={}
    for y,x,name in ((64,1500,'mode0_left'),(160,1500,'mode1_left'),
                     (256,1500,'mode2_left'),(160,2200,'mode1_right')):
        lab=Lab(r,y,x);rows=[]
        for t in range(1000):lab.step();rows.append(lab.snap(t))
        # Store a complete normal cycle, including fixed-point motion, links,
        # animation records, multiplexer and coexisting old/new children.
        launches=[];previous={}
        for row in rows:
            current={v['slot']:v for v in row['slots']}
            for slot,v in current.items():
                old=previous.get(slot)
                if v['state'] in (11,15,19,20) and (old is None or old['state']!=v['state']):
                    launches.append(dict(tick=row['tick'],**v))
            previous=current
        out[name]=dict(player=[x,y],events=signatures(rows),
            rows=rows if name=='mode1_left' else None,
            launches=launches,
            limits='Controlled original scheduler; static player, camera and no IRQ/VDP replay.')
    return out

def prepare_contact(lab,parameter,dx,dy,flags=2,power=0,st=7,ex=8,vy=256,vx=128,mux=None):
    o,m=lab.o,lab.m;b=SLOT+parameter*64
    m[SLOT:SLOT+320]=bytes(320)
    for n in range(5):
        a=SLOT+n*64;m[a]=81;m[a+63]=n;m[a+1]=7 if n==0 else 6
        o.word(a+17,1856);o.word(a+20,270);o.word(a+52,a+64 if n<4 else 0);o.word(a+54,a-64 if n else 0)
        m[a+44]=12;m[a+45]=32
    m[b+1]=m[b+2]=st;m[SLOT+38]=8
    m[SLOT+39]=((parameter-1)%5 if parameter==0 else parameter) if mux is None else mux
    m[0xD500:0xD540]=bytes(64);m[0xD500]=1;m[0xD501]=m[0xD502]=5
    m[0xD503]=flags;m[0xD532]=power;m[0xD52C]=ex;m[0xD52D]=24;m[0xD522]=2
    o.position(1856+dx,270+dy);o.word(0xD516,vx);o.word(0xD518,vy)
    m[0xD3B0]=m[0xD3B1]=m[0xD520]=m[0xD521]=m[0xDE04]=0;m[0xD29A]=0x47
    return b

def contacts(r):
    lab=Lab(r);settled=lab.settle()
    extents={str(v['parameter']):v['extent'] for v in settled['slots'] if v['type']==81}
    # Frame extents are also regenerated directly from approved mappings below.
    frames=json.loads((ROOT/'data/rom-cache/gpz/enemy-art-approval.json').read_text())['types']['81']['frames']
    cases=[]
    points=dict(top=(0,-31),below=(0,23),left=(-19,0),right=(19,0),center=(0,0),
                outside_x=(21,0),outside_y=(0,-33))
    for parameter,flags,power,region in itertools.product(range(5),(0,1,2,3,0x40,0x42,0x80,0x82),(0,6),points):
        b=prepare_contact(lab,parameter,*points[region],flags=flags,power=power,st=7 if parameter==0 else 6)
        # Calling state callback retains follow-lower behavior: matching supports
        # are set to the desired anchor after follow via the table's phase0 row.
        # Contact helper alone isolates geometry and mux, head damage branch is
        # then tested separately through the actual callback below.
        lab.call(0xA0F5,b)
        before=player(lab.o)
        lab.o.cpu.ix=0xD500;lab.o.call(0x48BC)
        cases.append(dict(parameter=parameter,region=region,flags=flags,power=power,
            contact=mread(lab,b),before_consumer=before,after_consumer=player(lab.o)))
    grids=[]
    for ex in (8,9):
        failures=0;count=0;digest=hashlib.sha256()
        for dx,dy in itertools.product(range(-23,24),range(-35,28)):
            b=prepare_contact(lab,0,dx,dy,ex=ex)
            lab.call(0xA0F5,b);got=lab.m[b+33]&15
            want=overlap(dx,dy,ex)
            failures+=got!=want;count+=1;digest.update(bytes([got]))
        assert failures==0,(ex,failures)
        grids.append(dict(player_extent_x=ex,cases=count,mismatches=failures,classification_sha256=digest.hexdigest()))
    mux=[]
    for parameter,start in itertools.product(range(5),range(5)):
        b=prepare_contact(lab,parameter,0,-10,mux=start)
        lab.call(0xA0F5,b)
        mux.append(dict(parameter=parameter,start=start,end=lab.m[SLOT+39],contact=lab.m[b+33]&15))
    detached=[]
    for flags,power,region in itertools.product((0,2,0x40,0x42,0x80,0x82),(0,6),points):
        b=prepare_contact(lab,1,*points[region],flags=flags,power=power)
        lab.call(0xA0E6,b);before=player(lab.o)
        lab.o.cpu.ix=0xD500;lab.o.call(0x48BC)
        detached.append(dict(flags=flags,power=power,region=region,before_consumer=before,after_consumer=player(lab.o)))
    return dict(extents=extents,approved_frame_metadata=frames,geometry_sweeps=grids,
        mux=mux,attached_cases=cases,detached_cases=detached,
        scope='A0F5/A0E6 + real player damage consumer; head callback and state reach tested separately.')

def overlap(dx,dy,ex=8):
    if abs(dx)>ex+12 or dy < -32 or dy>24:return 0
    horizontal=ex+12-abs(dx);vertical=24-dy if dy>=0 else 32+dy
    return (4 if dx>=0 else 8) if horizontal<vertical else (2 if dy>=0 else 1)

def mread(lab,b):
    m=lab.m
    return dict(bits=m[b+33]&15,state=m[b+1],requested=m[b+2],head_health=m[SLOT+38],mux=m[SLOT+39])

def head_hits(r):
    lab=Lab(r);initial=lab.settle();snapshot=bytes(lab.m[0xC000:0xE000]);cases=[]
    for flags,power,mux,region,vy in itertools.product((0,1,2,3,0x40,0x42,0x80,0x82),(0,6),range(5),
                    ('top','below','left','right'),(-768,0,768)):
        lab.m[0xC000:0xE000]=snapshot
        # First follow-only callback predicts the current update's anchor.
        lab.o.position(1500,160);lab.call(0x9E4B)
        x,y=lab.o.word(SLOT+17),lab.o.word(SLOT+20)
        lab.m[0xC000:0xE000]=snapshot
        dx,dy=dict(top=(0,-31),below=(0,23),left=(-19,0),right=(19,0))[region]
        lab.o.position(x+dx,y+dy);lab.o.word(0xD516,128);lab.o.word(0xD518,vy)
        lab.m[0xD503]=flags;lab.m[0xD532]=power;lab.m[SLOT+39]=mux
        lab.m[0xD29A]=0x47;lab.m[0xD3B1]=120 if flags&128 else 0
        lab.m[0xD520]=lab.m[0xD521]=lab.m[0xD3B0]=lab.m[0xDE04]=0
        lab.call(0x9E29)
        before=player(lab.o);contact=mread(lab,SLOT)
        lab.o.cpu.ix=0xD500;lab.o.call(0x48BC)
        cases.append(dict(flags=flags,power=power,mux=mux,region=region,incoming_vy=vy,
            contact=contact,player=before,after_consumer=player(lab.o)))
    # Run real scripts after one successful attack; no repeated synthetic contact.
    lab.m[0xC000:0xE000]=snapshot;lab.m[SLOT+2]=13;rows=[]
    lab.o.position(1500,160)
    for t in range(65):lab.step();rows.append(lab.snap(t))
    health=[]
    for hp in range(1,11):
        lab.m[0xC000:0xE000]=snapshot;lab.m[SLOT+38]=hp;lab.m[SLOT+2]=13;lab.step()
        health.append(dict(before=hp,after=lab.m[SLOT+38],state=lab.m[SLOT+1],requested=lab.m[SLOT+2]))
    recontacts=[]
    for start_mux in range(5):
        lab.m[0xC000:0xE000]=snapshot;lab.m[SLOT+2]=13;lab.m[SLOT+39]=start_mux
        timeline=[]
        for t in range(64):
            saved=bytes(lab.m[0xC000:0xE000]);lab.call(0x9E4B)
            x,y=lab.o.word(SLOT+17),lab.o.word(SLOT+20);lab.m[0xC000:0xE000]=saved
            lab.o.position(x-19,y);lab.m[0xD503]=2
            lab.step()
            timeline.append(dict(tick=t,state=lab.m[SLOT+1],requested=lab.m[SLOT+2],
                health=lab.m[SLOT+38],mux=lab.m[SLOT+39]))
            if lab.m[SLOT+38]<7:break
        recontacts.append(dict(start_mux=start_mux,rows=timeline))
    return dict(cases=cases,reaction_rows=rows,health_decrements=health,recontacts=recontacts)

def defeat(r):
    lab=Lab(r);lab.settle();lab.m[SLOT+38]=1;lab.m[SLOT+2]=13
    rows=[]
    for t in range(290):lab.step();rows.append(lab.snap(t))
    # Floor gate remains closed for 290 calls, then opens. No state forcing after hit.
    lab.m[0xD522]=2
    for t in range(290,310):lab.step();rows.append(lab.snap(t))
    return dict(events=signatures(rows),rows=rows,
        scope='Final-hit requested state13, original scheduler/supports, static player; floor held clear until call290.')

def boundaries(r):
    lab=Lab(r);rows=[]
    for x,y in itertools.product(range(1659,1670),range(91,102)):
        lab.m[SLOT+7]=224;lab.o.word(SLOT+14,0);lab.o.word(0xD174,x);lab.o.word(0xD176,y)
        lab.call(0x9AF7)
        rows.append(dict(camera=[x,y],timer=lab.m[SLOT+7],script=lab.o.word(SLOT+14)))
    removals=[]
    for pc,parameter,x in itertools.product((0x9FD2,0xA005,0xA06A,0xA087),(1,2),(1535,1536,1599,1600,1601,1663,1664,1919,1920,1921,2047,2048,2112)):
        b=prepare_contact(lab,parameter,100,0,st=11);lab.o.word(b+17,x)
        lab.m[SLOT+1]=7;lab.o.word(b+22,0);lab.o.word(b+24,0);lab.o.position(1500,100)
        lab.call(pc,b)
        removals.append(dict(callback=pc,parameter=parameter,x_before=x,x_after=lab.o.word(b+17),type=lab.m[b]))
    floors=[]
    for f in range(256):
        lab=Lab(r);lab.m[0xD522]=f;lab.m[0xD2BE]=255;lab.o.word(0xD174,1664)
        lab.call(0x9D26)
        floors.append(dict(floor_flags=f,type=lab.m[SLOT],requested=lab.m[0xD502],
            limits=[lab.o.word(a) for a in (0xD280,0xD282,0xD27E)],timer_running=lab.m[0xD2BE]))
    return dict(camera_ready_sweep=rows,detached_removal_sweep=removals,floor_gate_sweep=floors)

def removal_sweep(r):
    lab=Lab(r);counts=[]
    for pc in (0x9FD2,0xA005,0xA06A,0xA087):
        failures=0;digest=hashlib.sha256()
        # Covers complete low-byte domains around both world thresholds.
        for x in range(1280,2304):
            b=prepare_contact(lab,1,100,0,st=11);m,o=lab.m,lab.o
            o.word(b+17,x);o.word(b+22,0);o.word(b+24,-32)
            m[SLOT+1]=7;m[SLOT+50]=0;o.position(1500,100)
            lab.call(pc,b);after=o.word(b+17)
            want=((after&255)<64 and after>>8<7) if pc in (0x9FD2,0xA06A) else ((after&255)>=128 and after>>8>=7)
            got=m[b]==255;failures+=got!=want;digest.update(bytes([got]))
        assert failures==0
        counts.append(dict(callback=pc,cases=1024,mismatches=failures,sha256=digest.hexdigest()))
    return counts

def throw_sweep(r):
    lab=Lab(r);rows=[]
    # Counter overflow is computed AFTER movement and before direction selection.
    for mode,param,px,phase in itertools.product(range(3),range(1,5),(1500,1799,1800,1801,2200),(0,251,252,253,254,255)):
        b=prepare_contact(lab,param,100,0,st=10);m,o=lab.m,lab.o
        m[SLOT+50]=mode;m[SLOT+1]=7;m[b+31]=phase
        o.position(px,100);o.word(b+17,1800);o.word(b+22,0);o.word(b+56,2)
        lab.call(0x9F4E,b)
        inc=1+((px+param+1800)&3)
        direction=11 if px<1800 else 15
        expected=((19 if px<1800 else 20) if param&1 else direction) if phase+inc>255 else 10
        assert m[b+2]==expected,(mode,param,px,phase,m[b+2],expected)
        rows.append(dict(mode=mode,parameter=param,player_x=px,phase_before=phase,
            increment=inc,phase_after=m[b+31],requested=m[b+2]))
    return rows

def hurt_variants(r):
    lab=Lab(r);rows=[]
    for detached,flags,power,rings,ceiling,state in itertools.product((False,True),(0,2,0x40,0x80),(0,6),(0,0x47),(0,1),(5,)):
        b=prepare_contact(lab,1,-19,0,flags=flags,power=power)
        m=lab.m;m[0xD29A]=rings;m[0xD522]=2|ceiling;m[0xD501]=state;m[0xD3B1]=120 if flags&128 else 0
        lab.call(0xA0E6 if detached else 0xA0F5,b);before=player(lab.o)
        o=lab.o;o.cpu.ix=0xD500
        # Ordinary no-ring death waits for an IRQ at $062D. Capture at that
        # boundary instead of claiming this subroutine harness supplies IRQs.
        o.cpu.set_breakpoint(0x062D);o.cpu.pc=0x48BC;o.cpu.sp=0xDFE0;o.word(o.cpu.sp,o.RETURN)
        for _ in range(20):
            o.cpu.ticks_to_stop=100000;o.cpu.run()
            if o.cpu.pc in (o.RETURN,0x062D):break
        else:raise RuntimeError('hurt consumer did not reach return/wait')
        stopped_at=o.cpu.pc;o.cpu.clear_breakpoint(0x062D)
        rows.append(dict(detached=detached,flags=flags,power=power,rings=rings,ceiling=ceiling,
            state=state,consumer_stopped_at=stopped_at,before_consumer=before,after_consumer=player(lab.o)))
    return rows

def build(r):
    return dict(format=1,rom_sha256=R.SHA256,canonical_base='d214c60',
        evidence='DECODED DATA + SOURCE-TRACED BEHAVIOR + CONTROLLED ORIGINAL ROUTINE/SCHEDULER RESULT',
        approved_art='data/rom-cache/gpz/enemy-art-approval.json; unchanged',
        source=dict(bank=30,cpu_start=0x9A3A,cpu_end=0xA1D4,file_start=0x79A3A,
            sha256=hashlib.sha256(r[0x79A3A:0x7A1D4]).hexdigest()),
        sway_table=dict(bank=30,cpu=0xA154,file=0x7A154,
            offsets=[[R.s16(R.u16(r,p)),R.s16(R.u16(r,p+2))] for p in range(0x7A154,0x7A1D4,4)]),
        scripts=A.states(r,81),cycles=cycles(r),contacts=contacts(r),head_hits=head_hits(r),
        defeat=defeat(r),boundaries=boundaries(r),throw_sweep=throw_sweep(r),hurt_variants=hurt_variants(r),
        detached_removal_sweep=removal_sweep(r))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom');p.add_argument('--check',action='store_true')
    a=p.parse_args();r=R.load(a.rom);d=build(r);s=json.dumps(d,separators=(',',':'))+'\n'
    if a.check:assert CACHE.read_text()==s,'runtime cache differs'
    else:CACHE.write_text(s)
    print('Verified ROM; generated $51 runtime fixtures:',CACHE)

if __name__=='__main__':main()

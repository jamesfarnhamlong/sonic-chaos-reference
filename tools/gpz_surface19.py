"""Bounded original-routine audit of GPZ surface $19; no POC changes."""
import argparse
import hashlib
import json
from pathlib import Path
import isometric_platform as I
import level_package as L

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/rom-cache/gpz-surface19.json'

def signed(v):
    return v - 65536 if v & 32768 else v

class Lab(I.TerrainLab):
    def __init__(self, rom, state=5, speed=1024, x=528, y=686):
        super().__init__(rom, 'gpz2')
        o,m=self.o,self.m
        o.position(x,y);o.word(0xD516,speed);o.word(0xD518,0)
        m[0xD501]=m[0xD502]=state;m[0xD503]=0
        m[0xD522]=2;m[0xD523]=2;m[0xD36C]=0x59
        m[0xD297]=1;m[0xD298]=1;m[0xD52C]=8;m[0xD52D]=24
        o.word(0xD174,x-100);o.word(0xD51C,100)
        o.word(0xD373,1024);m[0xD12B]=14

    def snapshot(self):
        o,m=self.o,self.m
        return dict(x=o.word(0xD511),y=o.word(0xD514),vx=signed(o.word(0xD516)),
                    vy=signed(o.word(0xD518)),current=m[0xD501],requested=m[0xD502],
                    special=m[0xD524],counter=m[0xD3BC],plane=m[0xD525],
                    movement_flags=m[0xD503],floor=bool(m[0xD522]&2),surface=m[0xD36C])

    def step(self, pad=0):
        o,m=self.o,self.m
        m[0xD137]=pad;m[0xD147]=0
        o.word(0xD174,o.word(0xD511)-100)
        o.bank(2,12);m[0xD12B]=12;o.call(0x64FA);o.call(0x5E91)
        return self.snapshot()

def speed_sweep(rom):
    rows=[]
    # Enter AFTER the shared movement/terrain call to isolate the exact state
    # selection comparison. $3791 is the original walk callback suffix.
    for maximum in (2,4,6):
        for speed in range(-2048,2049):
            lab=Lab(rom,speed=speed);o,m=lab.o,lab.m
            m[0xD524]=1;m[0xD374]=maximum
            o.call(0x3791)
            expected=6 if abs(speed)//256==maximum else 0x14
            if m[0xD502]!=expected:raise AssertionError((maximum,speed,m[0xD502],expected))
        rows.append(dict(maximum_high_byte=maximum,cases=4097,
                         run_abs_speed_range=[maximum*256,maximum*256+255],
                         other_speeds_request=0x14))
    for speed in range(-1280,1281):
        lab=Lab(rom,6,speed);o,m=lab.o,lab.m
        o.call(0x3856)
        high=(speed & 65535)>>8
        magnitude=(-high)&255 if high&128 else high
        expected=5 if magnitude<4 else 6
        if m[0xD502]!=expected:raise AssertionError(('run',speed,m[0xD502]))
    return dict(walk=rows,run=dict(cases=2561,
                positive_minimum_to_remain_run=1024,negative_maximum_to_remain_run=-769,
                rule='abs(signed high byte(vx)) >= 4; fractional left/right asymmetry'))

def fixtures(rom):
    out={}
    for name,state,speed,pad,n in [('fast_right',6,1024,8,24),('fast_left',6,-1024,4,8),
                                  ('slow',5,768,8,18),('stopped_walk',5,0,0,18),
                                  ('stopped_idle',1,0,0,18),('decelerate',6,1024,0,30)]:
        lab=Lab(rom,state,speed)
        rows=[lab.snapshot()]
        rows.extend(lab.step(pad) for _ in range(n))
        out[name]=rows
    # Escape the strip after falling; original ordinary landing then selector
    # cleans the bit, followed by a new explicit placement at the strip.
    lab=Lab(rom,5,0);rows=[lab.step() for _ in range(12)]
    lab.o.position(110,448);lab.o.word(0xD518,0);lab.m[0xD36C]=0x81
    rows.extend(lab.step() for _ in range(16))
    if not lab.snapshot()['floor'] or lab.snapshot()['special']&1:
        raise AssertionError('synthetic ordinary landing failed')
    lab.o.position(528,686);lab.o.word(0xD516,1024);lab.o.word(0xD518,0)
    lab.m[0xD501]=lab.m[0xD502]=6;lab.m[0xD522]=2;lab.m[0xD503]=0
    rows.extend(lab.step(8) for _ in range(8));out['exit_and_reenter']=rows
    return out

def support_matrix(rom):
    rows=[]
    for x in (496,528):
      for plane in (0,1):
       for current in (1,5,6,0x14):
        for requested in (5,6,0x14):
         for bit in (0,1):
          lab=Lab(rom,current,0,x,693);o,m=lab.o,lab.m
          m[0xD502]=requested;m[0xD524]=bit;m[0xD525]=plane
          o.call(0x691A)
          expected=693 if bit and requested==0x14 else 686
          if o.word(0xD514)!=expected:raise AssertionError(lab.snapshot())
          rows.append(dict(x=x,plane=plane,current=current,requested=requested,
                           bit0_before=bit,y_after=expected,block=m[0xD36B]))
    return rows

def build(rom):
    sites=[]
    roles={0x4605:'normal jump reset',0x465C:'ordinary fall reset',0x467D:'special strip fall reset',
           0x6B1F:'surface1B increment',0x6B28:'surface19 increment',0x703E:'bit1 sinking projection numeric read',
           0x30D1C:'other-character run selector exit reset',0x30F01:'Sonic walk selector exit reset',
           0x30F5C:'Sonic run selector exit reset'}
    for p in range(len(rom)-2):
        if rom[p:p+2]==bytes.fromhex('bcd3'):
            sites.append(dict(operand_rom=p,bank=p//0x4000,
                              cpu=(p if p<0x8000 else 0x8000+p%0x4000),role=roles[p]))
    if {s['operand_rom'] for s in sites}!=set(roles):raise AssertionError('operand inventory changed')
    regions={}
    for a,b in [(0x3783,0x37CC),(0x384D,0x386F),(0x3A48,0x3A59),
                (0x45ED,0x4680),(0x6B14,0x6B2C),(0x6FBB,0x7056)]:
        regions[f'{a:04X}']=dict(rom=a,bank=a//0x4000,cpu=a,length=b-a,
                                sha256=hashlib.sha256(rom[a:b]).hexdigest())
    for a,b in [(0x8CB4,0x8D36),(0x8EE1,0x8F76)]:
        off=0x30000+a-0x8000
        regions[f'0C:{a:04X}']=dict(rom=off,bank=12,cpu=a,length=b-a,
                                 sha256=hashlib.sha256(rom[off:off+b-a]).hexdigest())
    return dict(rom_sha256=hashlib.sha256(rom).hexdigest(),
                evidence='CONTROLLED ROUTINE RESULT; source-traced consumers',
                d3bc_operand_sites=sites,source_regions=regions,
                speed_sweep=speed_sweep(rom),support_matrix=support_matrix(rom),fixtures=fixtures(rom))

def dumps(value):return json.dumps(value,indent=2)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args()
    value=dumps(build(L.load_rom(a.rom)))
    if a.check:
        if OUTPUT.read_text()!=value:raise SystemExit('cache mismatch')
    else:OUTPUT.write_text(value,encoding='utf-8')
    print('surface19: 14,852 signed-speed cases plus deterministic update fixtures')

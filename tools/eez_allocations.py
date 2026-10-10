"""Execute original animation interpreter command4 under every pool capacity."""
import argparse
import eez_foundation as F
import level_package as L
from oracle import Oracle
S=0xD540

def build(r):
    rows=[];checks=0
    for t,st,n,expected in [(54,3,32,[55]),(56,3,1,[57,57]),(56,4,1,[56]),(96,0,1,[99]),(96,12,1,[97])]:
        for free in range(12):
            o=Oracle(r);m=o.mem;o.cpu.ix=S;o.bank(2,30);m[0xD12B]=30
            m[0xD540:0xDA00]=bytes(0x4C0);m[S]=t;m[S+1]=m[S+2]=st;m[S+4]=16
            o.word(S+17,1500);o.word(S+20,494);o.word(S+58,1500);o.position(100,100)
            for j in range(11):m[0xD700+j*64]=0 if j<free else 255
            seen=set();events=[]
            for u in range(n):
                o.cpu.ix=S;o.bank(2,30);m[0xD12B]=30;o.call(0x64FA)
                for b in range(0xD700,0xD9C0,64):
                    if m[b] not in (0,255) and b not in seen:
                        seen.add(b);events.append(dict(update=u,slot=b,type=m[b],parameter=m[b+63],x=o.word(b+17),y=o.word(b+20),bases=list(m[b+8:b+10])))
            actual=[x['type'] for x in events]
            assert actual==expected[:free],(t,st,free,actual,expected);checks+=1
            rows.append(dict(type=t,state=st,free=free,events=events,parent_type=m[S],requested=m[S+2]))
    rewards=[]
    for gate in range(256):
        o=Oracle(r);m=o.mem;o.cpu.ix=S;m[S]=56;m[0xD292]=gate;m[0xD29D:0xD2A0]=bytes(3);o.call(0x5F54)
        assert list(m[0xD29D:0xD2A0])==([16,0,0] if not gate else [0,0,0]);checks+=1
        assert m[S]==15;checks+=1
    o=Oracle(r);o.mem[0xD29D:0xD2A0]=bytes((16,0,0));o.call(0x26F8)
    assert list(o.mem[0xD2B4:0xD2BA])==[0,1,0,0,0,0];checks+=1
    assert L.u16(r,0x271B)==0x3BA6 and L.u16(r,0x2718)==0xA516;checks+=1
    return dict(rom_sha256=L.ROM_SHA256,assertions=checks,cases=rows,
       reward=dict(accumulator_increment_bcd=[16,0,0],displayed_points=100,score_gate='D292==0',
           proof='26F8 draws six accumulator digits from3B9A, then2717..2725 writes static zero glyphA516 at3BA6, appending a seventh digit. BCD accumulator+10 means displayed+100.5F54 conversion itself still occurs when score gate blocks addition.',
           source=[F.A.source(r,0,0x262F,0x2691),F.A.source(r,0,0x26F8,0x27EB),F.A.source(r,0,0x5F54,0x5F84)]),
       contract='Actual64FA interpreter, original command4 eleven-slot allocation5EE1. Failed allocations advance script without retry; no synthetic fallback child. Isolated parent script fixture does not run child scheduler. Whole-game scheduler traces are separate.')

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();v=build(L.load_rom(a.rom));(F.OUT/'allocation-checks.json').write_text(F.dumps(v),encoding='utf-8');print(v['assertions'])

if __name__=='__main__':main()

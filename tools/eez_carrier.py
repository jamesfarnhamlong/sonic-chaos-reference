"""Mapped17 carrier and player16/17 source/overlap contract."""
import argparse,itertools
import eez_foundation as F
import level_package as L
import mghz_object_census as C
import mghz56_runtime as M
from oracle import Oracle
S=0xD700

def build(r):
    o=Oracle(r);o.bank(2,12);o.cpu.ix=S;m=o.mem
    frame=C.frame_record(r,23,1,0,0,bytes(0x4000))
    ox,oy=frame['extent_x_y'];checks=0;rows=[]
    for dx,dy,attack,hurt,st in itertools.product(range(-ox-10,ox+11),range(-oy-2,27),(0,2),(0,64),(5,23)):
        m[S:S+64]=bytes(64);m[S]=23;m[S+44]=ox;m[S+45]=oy
        o.word(S+17,1000);o.word(S+20,1000);o.word(0xD3A6,0)
        m[0xD501]=m[0xD502]=st;m[0xD503]=attack|hurt;m[0xD504]=0
        m[0xD52C]=8;m[0xD52D]=24;o.position(1000+dx,1000+dy)
        o.call(0xA741)
        bit=M.overlap_model(dx,dy,ox=ox,oy=oy)&13 if not hurt and st!=23 else 0
        expected=22 if bit else st
        assert m[0xD502]==expected,(dx,dy,attack,hurt,st,m[0xD502],expected)
        assert o.word(0xD3A6)==(S if bit else 0)
        checks+=2
        if dx==0 and dy in (-oy,0,24):rows.append([dx,dy,attack,hurt,st,m[0xD502],o.word(0xD3A6)])
    for param in (0,2,3,255):
        m[S+63]=param;o.word(S+17,1234);o.word(S+20,567);o.word(S+22,65472);o.word(S+24,1024)
        o.cpu.iy=S;o.cpu.ix=0xD500;m[0xD503]=0;m[0xD504]=0
        o.call(0x4C56)
        assert [o.word(a) for a in (0xD511,0xD514,0xD516,0xD518)]==[1234,567,65472,1024]
        assert m[0xD503]&2;assert bool(m[0xD504]&16)==(param!=2);checks+=3
    scripts={f'0x{t:02X}':C.public_script(C.state_scripts(r,t)) for t in (23,1)}
    scripts['0x01']['states']=[v for v in scripts['0x01']['states'] if v['state'] in (22,23)]
    return dict(rom_sha256=L.ROM_SHA256,checks=checks,geometry=[ox,oy],vectors=rows,scripts=scripts,
        regions=[F.A.source(r,12,0xA582,0xA78C),F.A.source(r,0,0x4C02,0x4C90)],
        block_lists=dict(continuation=list(r[0x32777:0x32786]),obstacle=list(r[0x32786:0x3278C])),
        contracts=dict(
            capture='A741 returns immediately if current player17. Otherwise advances own hurt cooldown flag3bit6/counter1F, then6328. Remove contact bit1 (bottom), retain top/side bits0/2/3. Any retained overlap stores owner slot D3A6, clears playerflag3bits0/1, requests16. Attack posture does not gate capture; shared6328 hurt gate still applies.',
            init='A5D3 requests1. Natural records parameter02. State1 velocity script VY+1; asleep returns; capture ->clear placement token, request parameter(2), VY+4. Awake no capture ->move+floor and save probed block D36E.',
            state2='accelerateVX +1/16 while highbyte<4; probe(+16,-16) against six obstacle IDs; then capture; floor contact continues motion; otherwise request4,VY+1. Obstacle with floorbit proceeds bounce, else fall4.',
            state3='negative-side counterpart: magnitude test via negation, accelerate negativeVX -1/16; probe(-16,-16). Natural parameter02 does not initially choose3; other requests must be source-traced.',
            state4='probe signed16,-16; obstacle zerosVX. Gravity helper5F84 adds+1/8 with rejection at+6 ceiling (does not clamp). Until floor:move/floor/saveD36E. On floor and prior marker in15-byte continue list requests parameter again,VY+4. Other floor ->bounce path.',
            bounce='soundBB,clear actor floorbit1,clear player hidebit7,VY-4,VX0,request5. If D3A6 owns this actor clear owner and call494F hurt helper on player. State5 gravity+1/4 ceiling6; on floor request6.',
            state6='frame1 duration16,then frame0 duration3 callback64F5 clears ownflags; A72B clears placement token/parameter. No reward or badnik attack defeat.',
            player16='frame5F duration1 callback4C02 copies actor X/Y/VX/VY to Sonic and sets attack, actor hidden; script835E requests17. Facing flag4bit4 derives from carrier parameter==2, not signVX.',
            player17='4C12 copies actor state, terrain ring probe753E, hurt48BC, movement401A. If requested hurt/death1E/1F OR buttonbits4/5 then detach:unhideactor,set counter1F16/hurtflag3bit6,request actor parameter,clear owner,ordinary setter45ED. Otherwise retains carrier; player normal terrain update is not substituted.',
            semantics='WORLD anchors and collision probes; generic viewport lifecycle still governs mapped actor before capture, canonical token cleared on capture. No dynamic allocations; no viewport-scaled distances. Player updates precede actor movement, so attachment sees prior actor position.',
            unresolved='Natural whole-game capture/continuation/detach and final6 cleanup cadence still require trace; no complete A4 closure claimed by isolated overlap sweep.'))

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();v=build(L.load_rom(a.rom))
    (F.OUT/'carrier-17.json').write_text(F.dumps(v),encoding='utf-8');print('carrier assertions',v['checks'])

if __name__=='__main__':main()

"""Original terrain entry -> player21 route -> common movement/terrain order."""
import argparse
import eez_foundation as F
import level_package as L
from sez_surfaces_rig import ZoneGame

def build(r):
    g=ZoneGame(r,5,0,hooks={0x16D0:'after_player',0x16D3:'after_objects'});s,m=g.s,g.m;cpu=bytes(s.cpu.get_state_view());events=[]
    def restore():g.e.restore();s.cpu.get_state_view()[:]=cpu
    g.restore_snapshot=restore
    def event(mm):
        if not g.recording:return
        if mm.cpu.pc>=0x8000 and s.slot[2]!=12:return
        events.append(dict(u=len(g.rows),pc=mm.cpu.pc,ix=mm.cpu.ix,player=[m[0xD501],m[0xD502],s.u16(0xD511),s.u16(0xD514),s.u16(0xD516),s.u16(0xD518)],block=m[0xD36B],prior=m[0xD36D],latch=m[0xD3C6]))
    for pc in (0x6D43,0x916B,0x91DC,0x60FB,0x690B,0x90F7):g.hook(pc,event)
    def setup(q):s.w16(0xD174,0);s.w16(0xD176,272)
    g.begin(110,360,vy=256,cur=14,floor=False,apply=setup)
    rows=g.run(96)
    assert any(e['pc']==0x6D43 for e in events),'natural terrain entry not reached'
    assert any(e['pc']==0x916B for e in events),'player21 not reached'
    for i,e in enumerate(events):
        if e['pc']==0x91DC:
            following=events[i+1:i+4]
            assert following and following[0]['pc']==0x60FB,'route did not move first'
    return dict(rom_sha256=L.ROM_SHA256,method=__doc__,fixture='Natural EEZ1 block7F at WORLD(96,384); Sonic110,360,VY+1,state0E. Original terrain, no route/state writes after begin.',updates=len(rows),events=events,rows=rows,
                assertions=2+sum(e['pc']==0x91DC for e in events))

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();v=build(L.load_rom(a.rom));(F.OUT/'transport-game-checks.json').write_text(F.dumps(v),encoding='utf-8');print(v['assertions'],sorted({e['player'][0] for e in v['events']}))

if __name__=='__main__':main()

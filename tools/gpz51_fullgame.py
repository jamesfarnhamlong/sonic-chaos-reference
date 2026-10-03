"""Update-aligned GPZ3 original-game fight/clear trace; no asset exports."""
import argparse,json
from pathlib import Path
import rom as R
from sms_frame_harness import SMS,BTN_1,BTN_2
from thz3_boss_support import Aligned,PC_MARKS
import platform_spike_collision as P

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'data/rom-cache/gpz/boss-51-fullgame.json'

def boot(r):
    s=SMS(r);done=[False]
    def select(m):m._write(0xD297,1);m._write(0xD298,2)
    def place(m):
        if done[0] or m.frame<300:return
        done[0]=True
        m.w16(0xD2D6,1500);m.w16(0xD2D8,96);m.w16(0xD511,1604);m.w16(0xD514,238)
    s.add_pc_hook(0x07D5,select);s.add_pc_hook(0x4E97,place)
    for t in range(4000):
        s.pad=0 if t<250 else BTN_1 if t<700 and t%40<3 else (BTN_1|BTN_2) if not done[0] and t%60<10 else 0
        s.run_frame()
        if done[0] and s.mem[0xD500]==1:return s
    raise RuntimeError('GPZ3 boot failed')

def build(r):
    s=boot(r);m=s.mem;u=s.u16
    e=P.Emu.__new__(P.Emu);e.s=s;e.rom=r;e.act='gpz3';al=Aligned(e)
    marks=[];writes=[];counter=[0];released=[False];hits=[]
    def mark(pc,name,bank=None):
        def hook(machine):
            if bank is not None and machine.slot[2]!=bank:return
            if 0x4000<=pc<0x8000 and machine.slot[1]!=1:return
            # Bound repetitive marks while keeping every hit and first clear gate.
            if name=='floor_clear_gate' and not (m[0xD522]&2):return
            if name=='head_hit_entry':hits.append(dict(update=counter[0],health=m[0xD726]))
            if name in ('floor_clear_gate','head_hit_entry') or not any(v['name']==name for v in marks):
                marks.append(dict(update=counter[0],frame=s.frame,name=name,pc=pc,bank=machine.slot[2],
                    zone=m[0xD297],act=m[0xD298],player=[u(0xD511),u(0xD514)],camera=[u(0xD174),u(0xD176)],
                    floor=m[0xD522],rings=m[0xD29A],flags=m[0xD293]))
        s.add_pc_hook(pc,hook)
    for pc,name in PC_MARKS.items():mark(pc,name,12 if pc==0x83ED else None)
    mark(0x9CAC,'head_hit_entry',30);mark(0x9D26,'floor_clear_gate',30)
    orig=s._write
    def write(a,v):
        if a in (0xDE04,0xD502,0xD293,0xD2BE,0xD297,0xD298) and m[a]!=v:
            writes.append(dict(update=counter[0],frame=s.frame,address=a,value=v))
        orig(a,v)
    s._write=write;s.cpu.set_write_callback(write)
    def boss():return next((b for b in range(0xD540,0xDA00,64) if m[b]==81 and m[b+63]==0),None)
    def park(x,y,flags=0,st=5):
        s.w16(0xD511,x);s.w16(0xD514,y);s.w16(0xD516,0);s.w16(0xD518,0)
        m[0xD502]=st;m[0xD503]=flags;m[0xD3B1]=0;m[0xD522]=2;m[0xD29A]=0x47
        # Fixture isolation between contacts, before the player update.
        m[0xD520]=m[0xD3B0]=0
    def driver(t):
        counter[0]=t
        b=boss()
        if released[0]:return
        if b is None:return
        st=m[b+1]
        if st==0:
            park(1760,238)
            return
        if st==14:
            # The separate controlled fixture tests the closed floor gate.
            # Here the original terrain pass supplies the grounded handoff.
            park(1760,270)
            return
        if st==7 and t>350 and m[b+39]==4:
            # Predict next follow anchor from the actual lower support and sway
            # table. Synthetic attacking placement occurs before player update;
            # original player physics/terrain/object order runs afterwards.
            phase=m[b+31]+(1 if (m[b+30]+1)&7==0 else 0)
            p=(phase&31)*4+0x7A154
            dx=R.s16(R.u16(r,p));dy=R.s16(R.u16(r,p+2));lower=u(b+52)
            park(u(lower+17)+dx-18,u(lower+20)+dy,2,9)
        elif st!=0:park(1680,270)
    def sample():
        b=boss();slots=[]
        if b is None and hits:released[0]=True
        for a in range(0xD540,0xDA00,64):
            if 0<m[a]<0xF0:
                slots.append(dict(slot=a,type=m[a],parameter=m[a+63],state=m[a+1],requested=m[a+2],
                    frame=m[a+6],timer=m[a+7],x=u(a+17),y=u(a+20),health=m[a+38],mux=m[a+39],
                    lower=u(a+52),upper=u(a+54)))
        return dict(update=counter[0],frame=s.frame,zone=m[0xD297],act=m[0xD298],slots=slots,
            player=[u(0xD511),u(0xD514)],velocity=[R.s16(u(0xD516)),R.s16(u(0xD518))],
            state=m[0xD501],requested=m[0xD502],player_flags=m[0xD503],floor=m[0xD522],
            rings=m[0xD29A],camera=[u(0xD174),u(0xD176)],pan=[u(0xD2DA),u(0xD2DC)],
            limits=[u(a) for a in (0xD280,0xD282,0xD27C,0xD27E)],
            scroll=[m[0xD15E],m[0xD15F]],clear=m[0xD293],timer_running=m[0xD2BE],
            time=[m[0xD2BF],m[0xD2C0]],bonus=u(0xD2A6),score=list(m[0xD29D:0xD2A0]))
    rows=al.run(driver,sample,4500,pad=lambda t:8 if t<75 else 0,restore=False,
        stop=lambda rows:rows[-1]['zone']!=1)
    (ROOT/'build/gpz51-fullgame-debug.json').write_text(json.dumps(dict(hits=hits,marks=marks,rows=rows),separators=(',',':')))
    assert hits,'no head hits reached'
    assert any(v['name']=='floor_clear_gate' for v in marks),'clear gate not reached'
    assert any(v['name']=='call_32F9_results_screen' for v in marks),'results not reached'
    assert rows[-1]['zone']==2,'next zone not reached'
    return dict(format=1,rom_sha256=R.SHA256,evidence='EMULATED ORIGINAL FRAME, update-aligned',
        method='Original GPZ3 loader, camera1500/96 player1604/238. Right held75 frames. Original player/terrain update selects mode2 (health10). After350 updates, synthetic attacking placement at head left edge when mux4; park safely between hits, reset pending contact/rings at each fixture boundary. Stop writes after head deletion. Original physics, terrain, scheduler, camera, bonus, results and next-zone loader execute.',
        limits='Approximate SMS VDP/IRQ harness; synthetic attack driver is not a recorded controller-only playthrough.',
        hits=hits,marks=marks,writes=writes,rows=rows)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom');p.add_argument('--check',action='store_true');a=p.parse_args()
    data=build(R.load(a.rom));s=json.dumps(data,separators=(',',':'))+'\n'
    if a.check:assert OUTPUT.read_text()==s,'fullgame cache differs'
    else:OUTPUT.write_text(s)
    print('Verified GPZ3 full fight/results/next-zone trace',len(data['rows']),'updates')
if __name__=='__main__':main()

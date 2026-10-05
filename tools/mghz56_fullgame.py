"""Update-boundary MGHZ3 original-game intro, eleven-hit fight, results/progression.

Synthetic placements exercise real player/terrain/object/camera/results code; this
is not a controller-only playthrough. No gameplay routines are substituted.
"""
import argparse
import json
from pathlib import Path
import rom as R
from sms_frame_harness import SMS, BTN_1, BTN_2
from thz3_boss_support import Aligned, PC_MARKS
import platform_spike_collision as P
from mghz_m1_followup import write_png

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'data/rom-cache/mghz/boss-56-fullgame.json'


def boot(r):
    s=SMS(r);done=[False]
    def select(m):m._write(0xD297,3);m._write(0xD298,2)
    def place(m):
        if done[0] or m.frame<300:return
        done[0]=True
        m.w16(0xD2D6,2940);m.w16(0xD2D8,256)
        m.w16(0xD511,3044);m.w16(0xD514,430)
    s.add_pc_hook(0x07D5,select);s.add_pc_hook(0x4E97,place)
    for t in range(4000):
        s.pad=0 if t<250 else BTN_1 if t<700 and t%40<3 else (BTN_1|BTN_2) if not done[0] and t%60<10 else 0
        s.run_frame()
        if done[0] and s.mem[0xD500]==1:return s
    raise RuntimeError('MGHZ3 boot failed')


def build(r,png=False,release_delay=0,with_camera_replay=True):
    s=boot(r);m=s.mem;u=s.u16
    e=P.Emu.__new__(P.Emu);e.s=s;e.rom=r;e.act='mghz3';al=Aligned(e)
    marks=[];writes=[];counter=[0];released=[False];hits=[];screens=[];phases=[];pre_driver=[None];release_start=[None]
    def phase(name):
        def hook(machine):
            if 0x8000<=machine.cpu.pc<0xC000 and machine.slot[2]!=30:return
            if machine.cpu.pc==0xA77F and m[machine.cpu.ix]!=87:return
            phases.append(dict(update=counter[0],frame=s.frame,phase=name,counter=m[0xD12F],
                player=[u(0xD511),u(0xD514)],velocity=[R.s16(u(0xD516)),R.s16(u(0xD518))],
                flags=m[0xD503],floor=m[0xD522],rings=m[0xD29A],damage=m[0xD3B0],
                camera=[u(0xD174),u(0xD176)],candidate=[u(0xD284),u(0xD286)],
                limits=[u(0xD280),u(0xD282)],scroll=[m[0xD15E],m[0xD15F]],
                lead=m[0xD28A],ix=machine.cpu.ix,cpu_a=machine.cpu.a,cpu_f=machine.cpu.f))
        return hook
    for pc,name in ((0x16CA,'before_camera'),(0x16CD,'after_camera_before_player'),
                    (0x16D0,'after_player_before_objects'),(0x16D3,'after_objects'),
                    (0x81F4,'before_release'),(0x8200,'after_release_before_clear_gate'),
                    (0xA77F,'warning_contact'),(0xA626,'selector_after_helper')):
        s.add_pc_hook(pc,phase(name))
    def mark(pc,name,bank=None):
        def hook(machine):
            if bank is not None and machine.slot[2]!=bank:return
            if 0x4000<=pc<0x8000 and machine.slot[1]!=1:return
            if name=='damaging_hit':hits.append(dict(update=counter[0],before_hp=m[machine.cpu.ix+38]))
            if name=='damaging_hit' or not any(v['name']==name for v in marks):
                marks.append(dict(update=counter[0],frame=s.frame,name=name,pc=pc,bank=machine.slot[2],
                    zone=m[0xD297],act=m[0xD298],player=[u(0xD511),u(0xD514)],camera=[u(0xD174),u(0xD176)],
                    floor=m[0xD522],clear=m[0xD293]))
        s.add_pc_hook(pc,hook)
    for pc,name in PC_MARKS.items():mark(pc,name,12 if pc==0x83ED else None)
    for pc,name in ((0x974C,'boss_init'),(0x9799,'trigger'),(0x97FD,'camera_pan_setup'),
                   (0xA576,'combat_init'),(0xA681,'damaging_hit'),(0x81DF,'bonus_clear_spawn')):
        mark(pc,name,30)
    orig=s._write
    def write(a,v):
        if a in (0xDE04,0xD502,0xD293,0xD2BE,0xD297,0xD298,0xD495,0xD3B3) and m[a]!=v:
            writes.append(dict(update=counter[0],frame=s.frame,address=a,value=v))
        orig(a,v)
    s._write=write;s.cpu.set_write_callback(write)
    def boss():return next((b for b in range(0xD540,0xDA00,64) if m[b]==86),None)
    def park(x,y,flags=0,st=5,vy=0,floor=2):
        s.w16(0xD511,x);s.w16(0xD514,y);s.w16(0xD516,0);s.w16(0xD518,vy)
        m[0xD502]=st;m[0xD503]=flags;m[0xD3B1]=0;m[0xD522]=floor;m[0xD29A]=0x47
        m[0xD520]=m[0xD3B0]=0
    def driver(t):
        counter[0]=t
        pre_driver[0]=dict(player=[u(0xD511),u(0xD514)],counter=m[0xD12F],
                           velocity=[R.s16(u(0xD516)),R.s16(u(0xD518))],floor=m[0xD522])
        b=boss()
        if released[0]:return
        if b is None:
            if hits:released[0]=True
            return
        st=m[b+1]
        if st<=3:park(min(u(0xD174)+235,3160),430);return
        if st==4 and release_delay:park(3260,430);return
        if st==5 and release_delay:
            if release_start[0] is None:release_start[0]=t
            age=t-release_start[0]
            if age<release_delay:
                park(3260 if age<release_delay//2 else min(u(0xD174)+40,3320),430);return
        if st in (4,5):park(3356,430);return
        if st in (6,7,8,9) and t>300 and m[b+56]<=1:
            park(u(b+17),u(b+20)-49,3,10,256,0)
        else:park(3100,430)
    def sample():
        b=boss();slots=[]
        for a in range(0xD540,0xDA00,64):
            if 0<m[a]<0xF0:
                slots.append(dict(slot=a,type=m[a],parameter=m[a+63],state=m[a+1],requested=m[a+2],
                    frame=m[a+6],timer=m[a+7],x=u(a+17),y=u(a+20),
                    vx=R.s16(u(a+22)),vy=R.s16(u(a+24)),hp=m[a+38],cooldown=m[a+56],flags4=m[a+4]))
        row=dict(update=counter[0],frame=s.frame,counter=m[0xD12F],
            sample_phase='update boundary AFTER synthetic driver, BEFORE camera/player/objects',
            pre_driver=pre_driver[0],zone=m[0xD297],act=m[0xD298],slots=slots,
            player=[u(0xD511),u(0xD514)],velocity=[R.s16(u(0xD516)),R.s16(u(0xD518))],
            state=m[0xD501],requested=m[0xD502],player_flags=m[0xD503],floor=m[0xD522],rings=m[0xD29A],
            camera=[u(0xD174),u(0xD176)],pan=[u(0xD2DA),u(0xD2DC)],
            limits=[u(a) for a in (0xD280,0xD282,0xD27C,0xD27E)],
            clear=m[0xD293],timer_running=m[0xD2BE],time=[m[0xD2BF],m[0xD2C0]],
            bonus=u(0xD2A6),score=list(m[0xD29D:0xD2A0]),palette=m[0xD495],dynamic=m[0xD3B3])
        if png and b and u(0xD174)==3060 and m[b+6] and len(screens)<8 and not any(v[0]==m[b+1] for v in screens):
            # Full original renderer for local visual review, captured before external writes next update.
            screens.append((m[b+1],s.render()[0]))
        return row
    rows=al.run(driver,sample,4500,restore=False,stop=lambda rows:rows[-1]['zone']!=3)
    debug=dict(hits=hits,marks=marks,writes=writes,rows=rows,phases=phases)
    (ROOT/'build/mghz56-fullgame-debug.json').write_text(json.dumps(debug,separators=(',',':')))
    assert len(hits)==11,('expected eleven hits',hits)
    assert [h['before_hp'] for h in hits]==list(range(10,-1,-1))
    assert any(v['name']=='call_32F9_results_screen' for v in marks),'results not reached'
    assert rows[-1]['zone']==4 and rows[-1]['act']==0,'AQZ1 not reached'
    if png:
        out=ROOT/'build/mghz56-review';out.mkdir(exist_ok=True)
        for st,rgb in screens:write_png(out/f'original-state-{st:02x}.png',rgb,2)
    offsets=sorted({(row['counter']-row['frame'])&255 for row in rows})
    settled=sorted({p['player'][1] for p in phases if p['phase']=='after_player_before_objects'
                    and p['update']<400 and next((v['player'][1] for v in rows if v['update']==p['update']),None)==430})
    assert all(p['counter'] in range(256) for p in phases)
    camera_replay=None;assertions=5
    if with_camera_replay:
        delayed=build(r,release_delay=24,with_camera_replay=False)
        release=next(p['update'] for p in delayed['phases'] if p['phase']=='after_release_before_clear_gate')
        gate=next(p['update'] for p in delayed['marks'] if p['name']=='bonus_clear_spawn')
        selected=[p for p in delayed['phases'] if release<=p['update']<=gate+1]
        moves=[p['candidate'][0]-p['camera'][0] for p in selected if p['phase']=='after_camera_before_player']
        assert any(v>0 for v in moves) and any(v<0 for v in moves)
        assert gate>release
        retained_left=next(p['limits'][0] for p in selected if p['phase']=='after_release_before_clear_gate')
        assert all(p['limits']==[retained_left,3584] for p in selected if p['phase']=='after_release_before_clear_gate')
        assertions+=3
        camera_replay=dict(method='In state04 hold playerX3260 so same-visit state05 cannot clear. After driver first observes05, hold gate false for24 updates: X3260 for12 then cameraX+40 (capped3320) for12, then3356. Original camera/player/object code executes.',
                           release_update=release,clear_gate_update=gate,retained_left=retained_left,phases=selected)
    return dict(format=2,rom_sha256=R.SHA256,evidence='EMULATED ORIGINAL FRAME, update-aligned',
        method='Original MGHZ3 loader camera2940/256 player3044/430; trigger driver parks player in camera window. After300 updates, synthetic downward attacking placement at boss top on ready combat visits. Park safely between hits; world3356/430 in defeat states. Stop writes after controller converts to smoke. Real terrain/scheduler/IRQ/camera/clear/results/progression execute.',
        limits='Approximate SMS VDP/IRQ harness; synthetic attacks are not a controller-only gameplay observation.',
        fixture_reconstruction=dict(counter_frame_offsets=offsets,settled_y_after_driver430=settled,
            counter_policy='Use recorded counter at the relevant phase; frame+96 is not a ROM rule. Counter advances at IRQ $0606; frame is harness bookkeeping.',
            player_policy='Rows preserve driver input. pre_driver and after_player_before_objects phases record actual physics state; do not infer parked Y from the driver-written430.'),
        assertions=assertions,camera_release_replay=camera_replay,**debug)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom');p.add_argument('--check',action='store_true');p.add_argument('--png',action='store_true');a=p.parse_args()
    data=build(R.load(a.rom),a.png);s=json.dumps(data,separators=(',',':'))+'\n'
    if a.check:assert OUTPUT.read_text()==s,'fullgame cache differs'
    else:OUTPUT.write_text(s)
    print(json.dumps(dict(hits=len(data['hits']),updates=len(data['rows']),marks=data['marks'])))


if __name__=='__main__':main()

"""Original final-act boss chain with boundary-only synthetic player control.

Boss HP/state/position are never rewritten. Contact fixtures place an attacking
Sonic at each original contact callback. End chase uses synthetic player X.
This is a controlled chain trace, not a player-input-only fight.
"""
import argparse
import eez_foundation as F
import level_package as L
import rom as R
from sez_surfaces_rig import ZoneGame

def build(r,flags=0,delay=0,angle=None,character=1):
    g=ZoneGame(r,5,2,hooks={0x16D0:'after_player',0x16D3:'after_objects'})
    s,m=g.s,g.m;events=[];last={};counts={};active=[False]
    cpu=bytes(s.cpu.get_state_view())
    def restore():g.e.restore();s.cpu.get_state_view()[:]=cpu
    g.restore_snapshot=restore
    def find(t):return next((b for b in range(0xD540,0xDA00,64) if m[b]==t),None)
    oldengine=g._engine_hook
    def park(mm):
        oldengine(mm)
        if not active[0] or mm.cpu.ix!=0xD500:return
        if find(97):x,y=3456,470
        elif not m[0xD4A7]:x,y=2050,430
        else:
            x,y=2434,430
            if not find(96):s.w16(0xD174,2144);s.w16(0xD176,334)
        s.w16(0xD511,x);s.w16(0xD514,y);s.w16(0xD516,0);s.w16(0xD518,0)
        m[0xD501]=m[0xD502]=14;m[0xD503]=2;m[0xD522]=0;m[0xD3B0]=0;m[0xD29A]=0x47;m[0xD532]=0
    def contact(mm):
        if not active[0]:return
        b=mm.cpu.ix
        if m[b] not in (94,96):return
        if m[b]==94 and len(g.rows)<delay:return
        if m[b]==96 and angle is not None and m[b+10]&1!=angle:return
        # Only player fixture writes: original overlap/contact chooses outcome.
        s.w16(0xD511,s.u16(b+17));s.w16(0xD514,s.u16(b+20)-m[b+45])
        s.w16(0xD516,0);s.w16(0xD518,256);m[0xD503]=2;m[0xD522]=0;m[0xD501]=m[0xD502]=9
        counts[m[b]]=counts.get(m[b],0)+1
    g.hook(0x64FA,park);g.hook(0xB2EC,contact);g.hook(0xB741,contact)
    def final_player(mm):
        if not active[0] or m[mm.cpu.ix]!=97:return
        s.w16(0xD511,2700 if mm.cpu.pc==0xBA87 else 3456)
        s.w16(0xD514,470);m[0xD503]=2
    g.hook(0xBA87,final_player);g.hook(0xBA96,final_player)
    def final_overlap(mm):
        b=mm.cpu.ix
        if active[0] and m[b]==97 and m[b+1] in (5,6):
            s.w16(0xD511,s.u16(b+17));s.w16(0xD514,s.u16(b+20));m[0xD503]=2
    g.hook(0x033B,final_overlap)
    def loader_camera(mm):
        if active[0] and mm.slot[2]==28 and m[0xD4A7] and not find(96) and not find(97):
            s.w16(0xD174,2144);s.w16(0xD176,334)
    g.hook(0x8000,loader_camera)
    def observe(mm):
        if not active[0]:return
        for b in range(0xD540,0xDA00,64):
            if m[b] not in (94,95,96,97,98,99):continue
            row=[m[b],m[b+1],m[b+2],m[b+38],m[b+56]]
            if last.get(b)!=row:
                events.append(dict(u=len(g.rows),slot=b,fields=row,x=s.u16(b+17),y=s.u16(b+20),camera=[s.u16(0xD174),s.u16(0xD176)],D4A5=m[0xD4A5],D4A7=m[0xD4A7],D3E7=m[0xD3E7],clear=m[0xD293]))
                last[b]=row
    g.hook(0x16D3,observe)
    # Natural loader entry: camera fixture permits mapped boss creation band.
    def setup(q):
        s.w16(0xD174,1536);s.w16(0xD176,334);m[0xD2CC]=flags;m[0xD2C8]=character
    active[0]=True;g.begin(2050,430,width=112,cur=14,f3=2,floor=False,types=(94,95,96,97,98,99),apply=setup)
    rows=g.run(4200+delay,stop=lambda row,rs: bool(m[0xD293]&0x10) or m[0xD297]!=5)
    result=dict(rom_sha256=L.ROM_SHA256,method=__doc__,complete_cpu_state_bytes=len(cpu),supplied_ending_character=character,supplied_collected_flags=flags,contact_delay=delay,second_contact_angle_parity=angle,updates=len(rows),events=events,contact_callback_calls=counts,
        final=dict(zone=m[0xD297],act=m[0xD298],clear=m[0xD293],D4A7=m[0xD4A7],D4A5=m[0xD4A5],camera=[s.u16(0xD174),s.u16(0xD176)],emerald_flags=m[0xD2CC],player=[s.u16(0xD511),s.u16(0xD514)],types=[m[b] for b in range(0xD540,0xDA00,64) if m[b]]))
    assert m[0xD293]&16,'controlled boss chain did not clear'
    active[0]=False;terminal=[];title=[False];ending_frame=[None];scene_frames=[];scene_meta=[]
    def terminal_hook(mm):
        terminal.append(dict(pc=mm.cpu.pc,frame=mm.frame,zone=m[0xD297],act=m[0xD298],character=m[0xD2C8],flags=m[0xD2CC],player=m[0xD500],state=m[0xD501]))
        if mm.cpu.pc==0x04B4:title[0]=True
        if mm.cpu.pc==0x18ED:ending_frame[0]=mm.frame
    for pc in (0x1543,0x15CE,0x15E8,0x1365,0x18ED,0x18FE,0x1A41,0x1ACD,0x34D3,0x04B4):g.hook(pc,terminal_hook)
    for _ in range(20000):
        s.pad=0;s.run_frame()
        if ending_frame[0] is not None and s.frame-ending_frame[0] in (16,128,512,1024,1536,1664,2048,4096,8192,9400):
            rgb=s.render()[0];meta=dict(elapsed=s.frame-ending_frame[0],frame=s.frame,player=[m[0xD500],m[0xD501],m[0xD506]],
                actors=[dict(type=m[b],state=m[b+1],frame=m[b+6],x=s.u16(b+17),y=s.u16(b+20)) for b in range(0xD540,0xDA00,64) if m[b] not in (0,255)],sat=s.sat(),cram=list(s.cram),rgb_sha256=L.sha256(bytes(c for row in rgb for px in row for c in px)))
            scene_meta.append(meta);scene_frames.append(dict(meta=meta,rgb=rgb))
        if title[0]:break
    result['terminal_trace']=terminal;result['returned_to_title']=title[0]
    assert title[0],'original terminal path did not return within bound'
    result['ending_scene_frames']=scene_meta
    out=F.ROOT/'build/eez-approval';out.mkdir(parents=True,exist_ok=True)
    (out/f'ending-flags{flags}-delay{delay}-angle{angle}-char{character}.json').write_text(F.dumps(scene_frames),encoding='utf-8')
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--flags',type=int,default=0);p.add_argument('--delay',type=int,default=0);p.add_argument('--angle',type=int,choices=(0,1));p.add_argument('--character',type=int,choices=(1,2),default=1);a=p.parse_args();v=build(L.load_rom(a.rom),a.flags,a.delay,a.angle,a.character)
    name=f'boss-game-character{a.character}.json' if a.character!=1 else f'boss-game-delay{a.delay}-angle{a.angle}.json' if a.delay or a.angle is not None else 'boss-game-checks.json' if a.flags==0 else f'boss-game-flags-{a.flags}.json'
    (F.OUT/name).write_text(F.dumps(v),encoding='utf-8');print(v['updates'],v['final'],len(v['events']),v['contact_callback_calls'])

if __name__=='__main__':main()

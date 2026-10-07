"""AQZ water whole-game fixtures; complete CPU/RAM/VDP restore, boundary writes.

Synthetic placements are labelled; original code, canonical layout and scheduler
are retained. This is a software SMS harness, not a hardware raster observation.
"""
import argparse
from pathlib import Path
import aqz_foundation as F
import level_package as L
from sez_surfaces_rig import ZoneGame

OUTPUT=F.OUT/'water-game-checks.json'
HOOKS={0x4C90:'camera',0x4B46:'water',0x4141:'control',0x402A:'xmove',0x4097:'ymove',0x690B:'terrain',0x753E:'rings',0x5DD1:'objects',0x9DDD:'controller',0x9DED:'raster_prepare',0x9D39:'air_bubble',0x9FAA:'splash',0x9500:'countdown',0x9555:'drown_tail',0x0652:'line_irq',0x4A74:'reward',0x297E:'restart_clear'}

def build(r):
    result=dict(rom_sha256=L.ROM_SHA256,method=__doc__,acts={})
    for act in (0,1):
        g=ZoneGame(r,4,act,hooks=HOOKS);s,m=g.s,g.m;line=(568,788)[act];width=(168,128)[act]
        cpu=bytes(s.cpu.get_state_view())
        def restore():
            g.e.restore();s.cpu.get_state_view()[:]=cpu
        g.restore_snapshot=restore
        palette_checks={'irq':0,'restore':0};palette_hashes=set()
        def irq_done(mm):
            if m[0xD132]!=255 or m[0xD443]:
                assert bytes(s.cram)==r[0x0688:0x06A8]
                palette_checks['irq']+=1;palette_hashes.add(F.digest(bytes(s.cram)))
        def palette_restored(mm):
            assert bytes(s.cram)==bytes(m[0xD472:0xD492]);palette_checks['restore']+=1
        g.hook(0x0683,irq_done);g.hook(0x1CD2,palette_restored)
        oldrow=g.row
        def row():
            out=oldrow();out.update(water=m[0xD443],fine=m[0xD444],air=m[0xD445],waterline=s.u16(0xD450),raster=m[0xD132],split=m[0xD131],rings=m[0xD29A],sound=m[0xDE04],selector=m[0xD532]);return out
        g.row=row
        traces={}
        def begin(y,vy=0,state=14,attack=1,apply=None,x=944,vx=0):
            def setup(mm):
                s.w16(0xD176,line-96);s.w16(0xD286,line-96);m[0xD443]=0;m[0xD444]=m[0xD445]=0
                if apply:apply(mm)
            g.begin(x,y,vy=vy,vx=vx,cur=state,f3=attack,floor=False,width=width,types=(12,13,14,50),apply=setup)
        for name,y,vy in [('entry',line-2,256),('exit',line+1,-832)]:
            begin(y,vy,state=10 if name=='exit' else 14,attack=3 if name=='exit' else 1);rows=g.run(12);assert len(rows)>=12
            traces[name]=rows[:12]
        assert any(x['water']==255 for x in traces['entry']),traces['entry']
        assert any(x['water']==0 for x in traces['exit'])
        def bob(mm):
            if mm.cpu.ix==0xD500:
                s.w16(0xD514,line+(1 if len(g.rows)%2==0 else -1));s.w16(0xD518,0)
        g.pre[0x4B46]=bob;begin(line);traces['surface_bobbing']=g.run(12)[:12];g.pre.clear()
        assert {x['water'] for x in traces['surface_bobbing']}=={0,255}
        def hold(mm):
            if mm.cpu.ix==0xD500:s.w16(0xD514,line+40);s.w16(0xD518,0)
        g.pre[0x4B46]=hold
        def held_rings(mm):m[0xD29A]=0x32
        begin(line+40,apply=held_rings);rows=g.run(2050,stop=lambda x,xs:x['req']==31 or x['cur'] in (31,40));traces['drowning']=rows
        assert all(x['rings']==0x32 for x in rows)
        assert any(x['air']==11 for x in rows),(act,len(rows),max(x['air'] for x in rows),[(x['u'],x['cur'],x['req'],x['air']) for x in rows if x['cur']==37][:20])
        assert any(x['req']==31 or x['cur'] in (31,40) for x in rows),(act,len(rows),rows[-1])
        g.pre.clear()
        # Continue the original countdown/death callbacks until the real restart.
        # No hold hook remains; screen death and the main game own the transition.
        before=len(rows);continued=g.run(2600,max_frames=3200)
        traces['drowning_death_restart']=continued[before:2600]
        assert any('restart_clear' in x['ev'] for x in traces['drowning_death_restart']),[(x['u'],x['cur'],x['req'],x['o'],x['ev']) for x in continued[2040:2045]]
        if act==0:
            def monitor_hold(mm):
                if mm.cpu.ix==0xD500 and m[0xD532]!=4:
                    s.w16(0xD514,430);s.w16(0xD518,0);m[0xD503]=3
            g.pre[0x4B46]=monitor_hold
            begin(430,state=10,attack=3,x=1664);traces['mapped_rocket_monitor']=g.run(100)[:100];g.pre.clear()
            assert any(x['selector']==4 for x in traces['mapped_rocket_monitor'])
            injected=[False]
            def natural_entry(mm):
                if mm.cpu.ix==0xD500 and not injected[0]:s.w16(0xD514,line+1);s.w16(0xD518,0);injected[0]=True
            g.pre[0x4B46]=natural_entry
            natural=g.run(124,padf=lambda u,f:2);g.pre.clear();traces['mapped_reward_water_entry']=natural[100:124]
            assert any(x['water']==255 and x['selector']==4 for x in traces['mapped_reward_water_entry'])
            injected[0]=False
            def natural_exit(mm):
                if mm.cpu.ix==0xD500 and not injected[0]:s.w16(0xD514,line+1);s.w16(0xD518,-832);injected[0]=True
            g.pre[0x4B46]=natural_exit
            natural=g.run(148,padf=lambda u,f:1);g.pre.clear();traces['mapped_reward_water_exit']=natural[124:148]
            assert any(x['water']==0 and x['selector']==4 for x in traces['mapped_reward_water_exit'])
        # Whole-game original air object callback; synthetic large bubble at player.
        def air_setup(mm):
            m[0xD443]=255;m[0xD444]=119;m[0xD445]=11
            b=0xD700;m[b:b+64]=bytes(64);m[b]=12;m[b+1]=m[b+2]=3;m[b+3]=128;m[b+6]=3;m[b+7]=200
            s.w16(b+12,0x9D39);s.w16(b+14,0x9CF2);s.w16(b+17,944);s.w16(b+20,line+40);s.w16(b+24,-192);m[b+44]=8;m[b+45]=16
        begin(line+40,apply=air_setup);traces['air_recovery']=g.run(24)[:24]
        assert any(x['req']==37 or x['cur']==37 for x in traces['air_recovery']),traces['air_recovery'][:3]
        assert any(x['air']==0 for x in traces['air_recovery'])
        # Underwater Rocket path uses actual reward processor, then state11.
        def rocket_setup(mm):m[0xD3A3]=8
        begin(line-2,vy=256,apply=rocket_setup);traces['rocket_entry']=g.run(24,padf=lambda u,f:2)[:24]
        assert any(x['selector']==4 and x['cur']==17 for x in traces['rocket_entry'])
        def rocket_exit(mm):m[0xD3A3]=8;m[0xD443]=255
        begin(line+1,apply=rocket_exit);traces['rocket_exit']=g.run(24,padf=lambda u,f:1)[:24]
        assert any(x['selector']==4 and x['water']==0 for x in traces['rocket_exit'])
        # Controller raster receives camera writes at its original callback boundary.
        for delta in (0,1,192,193):
            def cam(mm,d=delta):
                if mm.slot[2]==12:s.w16(0xD176,line-d)
            g.pre[0x9DDD]=cam;begin(line-20);traces[f'camera_delta_{delta}']=g.run(4)[:4];g.pre.clear()
        # Restart clear is original $297E; stop routine via an isolated Oracle test
        # elsewhere. Full game snapshot replay demonstrates clean fresh-act state.
        begin(line-2,256);replay=g.run(12)[:12];assert replay==traces['entry']
        result['acts'][f'aqz{act+1}']=dict(complete_cpu_state_bytes=len(cpu),history_independent_replay=True,fixtures=traces,
            original_palette_checks=palette_checks,irq_cram_sha256=sorted(palette_hashes),
            synthetic_controls='player/camera placement, held drowning anchor, large bubble and queued Rocket reward; no code patched; canonical terrain retained')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();v=build(L.load_rom(a.rom))
    if a.check:assert OUTPUT.read_text(encoding='utf-8')==F.dumps(v)
    else:OUTPUT.write_text(F.dumps(v),encoding='utf-8')
    print({k:{n:len(rows) for n,rows in v['fixtures'].items()} for k,v in v['acts'].items()})

if __name__=='__main__':main()

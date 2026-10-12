"""256-wide original scheduler right-edge audit; boundary-only entry fixture."""
import argparse
import json
from pathlib import Path
import rom
from sez_surfaces_rig import ZoneGame
from oracle import Oracle


def boundaries(r):
    """Original routine sweeps; broad bound is distinct from observed patrol."""
    o=Oracle(r);o.bank(2,30);o.cpu.ix=b=0xD700;m=o.mem
    checks=0;max_step=0;selectors=[]
    for x in range(192):
        for frame in range(1,5):
            m[b:b+64]=bytes(64);m[b+6]=frame;o.word(b+17,1951+x)
            o.call(0xB114)
            step=o.word(b+17)-(1951+x)
            assert step==[6,13,4,13][frame-1]
            max_step=max(max_step,x+step);checks+=1
    assert max_step==204
    for x in range(2100,2209):
        for frame in range(1,6):
            m[b:b+64]=bytes(64);m[b+2]=6;m[b+6]=frame
            o.word(b+17,x);o.position(2198,494);m[0xD522]=2
            o.call(0xB257)
            jump=m[b+11]==11
            assert jump==(frame not in (3,4) and abs(2198-x)<48)
            if jump:assert o.word(b+22)==0 and o.word(b+24)==0xFC00
            selectors.append([x,frame,jump]);checks+=1
    for x in (2143,2149,2155,2172,2208):
        for y in range(430,496):
            for frame in range(1,6):
                m[b:b+64]=bytes(64);m[b]=94;m[b+6]=frame
                m[b+44]=16;m[b+45]=48 if frame==5 else 64
                m[0xD52C]=8;m[0xD52D]=24;m[0xD503]=0;m[0xD520]=0
                o.word(b+17,x);o.word(b+20,y);o.position(2198,494)
                o.call(0x6328)
                if x<=2172:assert not m[b+33]&15 and m[0xD520]==0
                checks+=1
    return dict(checks=checks,patrol_screen_upper_bound=204,
        bound_method='All cached screen X0..191 and walking frames1..4 passed through original B114; largest 191+13=204. This is a conservative phase-independent bound, not the observed repeating endpoint.',
        jump_at_2172=[v for v in selectors if v[0]==2172],
        ordinary_player_body_reach=24, observed_first_jump_gap=26)


def compact(v):
    samples=v['samples'];es=v['events'];late=[s for s in samples if s['u']>650]
    return dict(fixture=v['fixture'],updates=v['updates'],stationary_probe=v['stationary_probe'],
        probe_after=v['probe_after'],probe_x=v['probe_x'],hold_right=v['hold_right'],
        camera=sorted(set((s['cx'],s['cy']) for s in late)),
        late_player_x=sorted(set(s['x'] for s in late)),
        late_boss_x_range=[min(o['x'] for s in late for o in s['objects'] if o['type']==94),
                           max(o['x'] for s in late for o in s['objects'] if o['type']==94)],
        event_counts={k:sum(e['event']==k for e in es) for k in sorted(set(e['event'] for e in es))},
        late_child_damage_count=sum(e['event']=='child_damage' and e['u']>650 for e in es),
        late_body_overlaps=sum(e['event']=='overlap_D520' and e['type']==94 and e['u']>650 for e in es),
        late_jump_count=sum(e['event']=='select_jump' and e['u']>650 for e in es),
        selected_events=[e for e in es if e['event'] in ('hurt','death','select_jump')]+
                        [e for e in es if e['event']=='overlap_D520' and e['type']==94][:3],
        child_damage_examples=[e for e in es if e['event']=='child_damage' and e['u']>650][:3],
        child_parameters=sorted(set(e['param'] for e in es if e['event']=='child_init' and e['u']>650)),
        early_state_samples=[s for s in samples if s['u'] in (330,331,392,393,402,486,584,742,780,781)])


def trace(r, updates=5000, start=1900, hold=True, probe=False, probe_after=650, probe_x=2198):
    g = ZoneGame(r, 5, 2, hooks={0x16D0: 'after_player', 0x16D3: 'after_objects'})
    s, m = g.s, g.m
    cpu = bytes(s.cpu.get_state_view())
    def restore():
        g.e.restore()
        s.cpu.get_state_view()[:] = cpu
    g.restore_snapshot = restore
    events, samples = [], []
    def event(name):
        def fn(mm):
            if not g.recording:
                return
            b = mm.cpu.ix
            events.append(dict(u=len(g.rows)+1, event=name, slot=b, type=m[b],
                state=m[b+1], req=m[b+2], frame=m[b+6], param=m[b+63],
                player=[s.u16(0xD511), s.u16(0xD514)], camera=[s.u16(0xD174),s.u16(0xD176)],
                actor=[s.u16(b+17),s.u16(b+20)], floor=m[0xD522], hurt=m[0xD503],
                target=m[b+11]))
        return fn
    for pc, name in ((0xB257,'decision'),(0xB299,'select_jump'),(0xB3D5,'child_init'),
                     (0x48F7,'hurt'),(0x4984,'death'),(0xB077,'left_patrol'),(0xB0ED,'right_patrol'),
                     (0x6314,'child_damage'),(0xB323,'body_bottom_damage')):
        g.hook(pc,event(name))
    def overlap(mm):
        if m[mm.cpu.ix] in (94,95):
            event('overlap_D520')(mm)
    g.hook(0x63E0,overlap)
    old=g._engine_hook
    def park(mm):
        old(mm)
        if probe and g.recording and len(g.rows)>=probe_after and mm.cpu.ix==0xD500:
            # Controlled stationary exposure, not an input-only survival claim.
            s.w16(0xD511,probe_x);s.w16(0xD514,494)
            s.w16(0xD516,0);s.w16(0xD518,0)
            m[0xD501]=m[0xD502]=5;m[0xD503]=0;m[0xD522]=2
            m[0xD520]=m[0xD3B0]=m[0xD532]=0
    g.hook(0x64FA,park)
    def observe(mm):
        if g.recording:
            samples.append(dict(u=len(g.rows)+1, x=s.u16(0xD511), y=s.u16(0xD514),
                cx=s.u16(0xD174), cy=s.u16(0xD176), state=m[0xD501], floor=m[0xD522],
                hurt=m[0xD503], pending_hurt=m[0xD520], rings=m[0xD29A],
                objects=g.objs((94,95))))
    g.hook(0x16D3,observe)
    def setup(q):
        for a,v in ((0xD174,start-112),(0xD284,start-112),(0xD176,318),(0xD286,318)):
            s.w16(a,v)
    g.begin(start,430,cur=14,floor=False,rings=99,types=(94,95),apply=setup)
    g.run(updates,padf=lambda u,f: 0 if probe and u>=probe_after else 8 if hold or u<650 else 0,
          stop=lambda row,rs: row['req']==31 or m[0xD297]!=5)
    return dict(rom_sha256=rom.SHA256, fixture='One entry placement/camera write; original player, scheduler, camera and boss thereafter; 99 rings; RIGHT input then optionally release after update650.',
                hold_right=hold, stationary_probe=probe, probe_after=probe_after, probe_x=probe_x, start=start, updates=len(g.rows), events=events, samples=samples)


def main():
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--updates',type=int,default=5000)
    p.add_argument('--release',action='store_true');p.add_argument('--probe',action='store_true');p.add_argument('--probe-after',type=int,default=650);p.add_argument('--probe-x',type=int,default=2198);p.add_argument('--start',type=int,default=1900);p.add_argument('--audit',action='store_true');a=p.parse_args()
    if a.audit:
        r=rom.load(a.rom)
        natural=compact(trace(r,1800,hold=False))
        stationary=compact(trace(r,12000,hold=False,probe=True,probe_after=200))
        assert natural['late_child_damage_count']>0 and natural['event_counts']['death']==1
        assert stationary['late_boss_x_range']==[2107,2143]
        assert stationary['late_body_overlaps']==stationary['late_jump_count']==0
        assert stationary['late_child_damage_count']>100
        v=dict(rom_sha256=rom.SHA256,natural=natural,stationary=stationary,boundaries=boundaries(r))
        path=Path(__file__).resolve().parents[1]/'data/rom-cache/eez/right-edge-threat.json'
        path.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
        print(path,v['boundaries']['checks'],stationary['late_child_damage_count']);return
    v=trace(rom.load(a.rom),a.updates,a.start,not a.release,a.probe,a.probe_after,a.probe_x)
    out=Path(__file__).resolve().parents[1]/'build/eez-right-edge'
    out.mkdir(parents=True,exist_ok=True)
    path=out/f'trace-{a.start}-{a.release}-{a.probe}-{a.probe_after}-{a.probe_x}.json';path.write_text(json.dumps(v),encoding='utf-8')
    settled=[s for s in v['samples'] if s['u']>650]
    print('saved',path,'updates',v['updates'])
    print('camera',sorted(set((s['cx'],s['cy']) for s in settled)))
    print('player',min((s['x'] for s in settled),default=None),max((s['x'] for s in settled),default=None))
    print('boss',min((o['x'] for s in settled for o in s['objects'] if o['type']==94),default=None),max((o['x'] for s in settled for o in s['objects'] if o['type']==94),default=None))
    print('special event counts',{k:sum(e['event']==k for e in v['events']) for k in ('hurt','death','select_jump','child_damage','body_bottom_damage')})


if __name__=='__main__':main()

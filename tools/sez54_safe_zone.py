"""Focused original-game selector traces. Only initial approach placement is synthetic."""
import argparse
import hashlib
import json
from pathlib import Path
import rom as R
from sez_surfaces_rig import ZoneGame, PAD

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/rom-cache/sez/boss-54-safe-zone.json'
TARGETS = ['right','left','rightwait','leftwait','rightmaxwait',2991,2992,3000,3010,3020,3080,3120,3150,3158,3159,3182,3183,3187,3190,3200,3210,3220,3222]

def oracle(r):
    from sez54_runtime import Lab, S
    lab=Lab(r);o,m=lab.o,lab.m
    lab.call(0xA291);m[S+1]=m[S+2]=6;m[S+4]=2;o.position(2992,622);lab.step()
    o.word(0xD174,2975);o.word(S+17,3187)
    render=[]
    render_id=m[S+5]
    for flags,visible in ((2,True),(66,True),(130,True),(2,False)):
        m[S+4]=flags;m[S+5]=render_id if visible else 0;m[S+26]=199
        o.call(0x220E)
        expected=212 if flags==2 and visible else 199
        assert m[S+26]==expected
        render.append(dict(flags4=flags,render_id=m[S+5],before=199,after=m[S+26]))
    vectors=[]
    for bx in (0,207,208,209,212,255):
        for px in range(256):
            m[S+1]=m[S+2]=10;m[S+4]=2;m[S+26]=bx;m[S+30]=0;m[S+53]=m[S+54]=0
            o.word(S+17,3187);o.word(S+20,622);o.word(S+22,0);o.word(S+24,0)
            o.position(3222,622);m[0xD503]=64;m[0xD51A]=px
            lab.call(0xA339)
            expected=11 if bx>=208 and px>=bx else 7
            assert m[S+2]==expected
            vectors.append(m[S+2])
    regions=[('selector',0x7A339,0x7A396),('renderer_gate',0x220E,0x2251),('cache_writer',0x3FC8,0x3FEF)]
    return dict(renderer_vectors=render,selector_cases=len(vectors),
        selector_result_sha256=hashlib.sha256(bytes(vectors)).hexdigest(),
        source_hashes=[dict(name=n,file=[a,b],sha256=hashlib.sha256(r[a:b]).hexdigest()) for n,a,b in regions],
        method='Controlled original renderer gate and complete state10 callback. Selector sweep suppresses overlap with synthetic player hurt flag and varies cached bytes independently of fixed world anchors; not natural gameplay.')

def build(r, targets, updates=1800, sweep=False):
    g = ZoneGame(r, 2, 2, hooks={0x16D0: 'after_player', 0x16D3: 'after_objects'})
    s, m = g.s, g.m
    # Preserve the core's complete exported state, including frame_tick, pending
    # index-prefix and interrupt shadow. The shared register-only restore leaves
    # frame_tick history-dependent; do not inject a NOP into this fixture.
    cpu_snapshot=bytes(s.cpu.get_state_view())
    def restore():
        g.e.restore()
        s.cpu.get_state_view()[:]=cpu_snapshot
    g.restore_snapshot=restore
    events = []
    def snap(pc):
        b = s.cpu.ix
        return dict(u=len(g.rows)+1, frame=s.frame, pc=pc, slot=b,
            camera=[s.u16(0xD174),s.u16(0xD176)],
            player=[s.u16(0xD511),s.u16(0xD514)], player_cache=list(m[0xD51A:0xD51E]),
            boss=[s.u16(b+17),s.u16(b+20)], boss_cache=list(m[b+26:b+30]),
            state=m[b+1], request=m[b+2], flags4=m[b+4], frame_id=m[b+6], render_id=m[b+5])
    for pc in (0xA385,0xA391,0xA395,0x3FC8,0x3FEE,0x2220):
        def hook(mm, pc=pc):
            b=s.cpu.ix
            if g.recording and (pc>=0xA000 and s.slot[2]==30 and m[b]==84 or pc<0xA000 and (b==0xD500 or m[b]==84)):
                events.append(snap(pc))
        g.hook(pc,hook)
    original_row=g.row
    def row():
        v=original_row()
        v['boss']=[dict(slot=b,state=m[b+1],request=m[b+2],x=s.u16(b+17),y=s.u16(b+20),cache=list(m[b+26:b+30]),flags4=m[b+4],hp=m[b+38])
            for b in range(0xD540,0xDA00,64) if m[b]==84]
        return v
    g.row=row
    out=[]
    placement=[None]
    original_engine=g._engine_hook
    def engine(mm):
        original_engine(mm)
        if mm.cpu.ix==0xD500 and g.recording and placement[0] is not None and s.u16(0xD174)==2975 and s.u16(0xD176)==462:
            s.w16(0xD511,placement[0]);s.w16(0xD516,0);m[0xD510]=0
            events.append(dict(u=len(g.rows)+1,pc='controlled_once',x=placement[0]))
            placement[0]=None
    g.hook(0x64FA,engine)
    for target in targets:
        events.clear()
        placement[0]=target if isinstance(target,int) else None
        g.begin(3060,620,rings=0x47)
        waiting=[False]
        def pad(u,f):
            x=s.u16(0xD511)
            if isinstance(target,int):return 0
            if target=='right':return PAD['RIGHT']
            if target=='left':return PAD['LEFT']
            if target in ('rightwait','leftwait'):
                edge=3220 if target=='rightwait' else 2992
                if (x>=edge if target=='rightwait' else x<=edge) and s.u16(0xD174)==2975:waiting[0]=True
                return 0 if waiting[0] else PAD['RIGHT' if target=='rightwait' else 'LEFT']
            if target=='rightmaxwait':return PAD['RIGHT'] if u<400 else 0
            raise ValueError(target)
        rows=g.run(updates,padf=pad,stop=lambda v,rs:v['cur'] in ((0x1E,0x1F,0x21) if sweep else (0x1F,0x21)))
        trace=dict(target=target,rows=rows,events=list(events))
        (ROOT/'build'/f'sez54-safe-{target}.json').write_text(json.dumps(trace,separators=(',',':')))
        selectors=[v for v in events if v['pc']==0xA385]
        escapes=[v for v in events if v['pc']==0xA391]
        last_write={};render_skips=[];selector_evidence=[]
        for event in events:
            if event['pc']==0x3FEE:last_write[event['slot']]=event
            if event['pc']==0x2220 and (not event['render_id'] or event['flags4']&0xC0):render_skips.append(event)
            if event['pc']==0xA385:
                bp=last_write.get(event['slot']);pp=last_write.get(0xD500)
                selector_evidence.append(dict(selector=event,boss_last_refresh=bp,player_last_refresh=pp,
                    boss_cache_age=event['u']-bp['u'] if bp else None,
                    player_cache_age=event['u']-pp['u'] if pp else None,
                    fresh_would_escape=((event['boss'][0]-event['camera'][0])&255)>=208 and
                        ((event['player'][0]-event['camera'][0])&255)>=((event['boss'][0]-event['camera'][0])&255),
                    cached_would_escape=event['boss_cache'][0]>=208 and event['player_cache'][0]>=event['boss_cache'][0]))
        placed=next((v['u'] for v in events if v['pc']=='controlled_once'),0)
        settled=[v for v in rows if v['d174']==2975 and v['boss'] and v['u']>placed]
        result=dict(target=target,updates=len(rows),selectors=selectors,escapes=escapes,
            player_range=[min(v['x'] for v in settled),max(v['x'] for v in settled)] if settled else None,
            first_hurt=next((v['u'] for v in rows if v['cur']==0x1E),None),
            placement_update=placed,selector_evidence=selector_evidence,
            renderer_skip_count=len(render_skips),renderer_skip_examples=render_skips[:8],
            states=sorted({b['state'] for v in rows for b in v['boss']}),
            last=rows[-1],trace_sha256=hashlib.sha256(json.dumps(trace,sort_keys=True).encode()).hexdigest())
        out.append(result)
        if sweep:
            result=dict(target=target,placement_update=placed,first_hurt=result['first_hurt'],
                escapes=escapes,trace_sha256=result['trace_sha256'],last_player=[rows[-1]['x'],rows[-1]['y']],
                updates=len(rows))
            out[-1]=result
        print(json.dumps(dict(target=target,updates=len(rows),selectors=len(selectors),escapes=len(escapes),first_hurt=next((v['u'] for v in rows if v['cur']==0x1E),None),last_x=rows[-1]['x'],last_state=rows[-1]['cur'])),flush=True)
    return dict(rom_sha256=R.SHA256,method='Original whole-game execution in approximate SMS harness; boot selects SEZ3; initial approach placement at (3060,620). String targets use pad input only thereafter. Integer targets add one X/zero-X-speed/fraction placement at first settled camera update, then neutral input. Never write caches, boss, camera, health, flags or state during observation.',runs=out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--targets',default=','.join(map(str,TARGETS)));p.add_argument('--updates',type=int,default=1800);p.add_argument('--check',action='store_true');p.add_argument('--sweep',action='store_true');a=p.parse_args()
    targets=[x if x in ('right','left','rightwait','leftwait','rightmaxwait') else int(x) for x in a.targets.split(',')]
    if a.sweep:targets=list(range(2991,3223))
    data=build(R.load(a.rom),targets,a.updates,sweep=a.sweep)
    if not a.sweep:data['controlled_oracle']=oracle(R.load(a.rom))
    output=OUTPUT.with_name('boss-54-stationary-sweep.json') if a.sweep else OUTPUT
    if a.check:assert json.loads(json.dumps(data))==json.loads(output.read_text())
    else:output.write_text(json.dumps(data,indent=2)+'\n')

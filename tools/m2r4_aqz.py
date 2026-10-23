"""Research-only original-code AQZ palette and reverse/jump trace collector.

No private pixels/ROM payload are written. Arrival/speed/state seeded once;
thereafter original scheduler, terrain and mapped objects execute normally.
"""
import argparse, hashlib, itertools, json
from pathlib import Path
import rom as R
import aqz_water as W
import level_package as L
from oracle import Oracle
from sez_surfaces_rig import ZoneGame
from m2r3_aqz import source

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/m2r4'
H=lambda b:hashlib.sha256(b).hexdigest()
PHASE_KEYS=['xu','yu','vx','vy','state','next','move','held','pressed','jump_ticks','water','input_delta','surface_delta','bg','contacts','player_flags','camera_x','camera_y','line']

def save(name,value):
    (OUT/name).write_text(json.dumps(value,separators=(',',':'))+'\n')

def snap(s):
    m=s.mem
    out={k:m[a] for k,a in dict(character=0xD500,state=0xD501,next=0xD502,move=0xD503,
        player_flags=0xD504,bg=0xD522,contacts=0xD523,objects=0xD521,support=0xD3C0,
        plane=0xD525,previous=0xD36C,modifier=0xD369,water=0xD443,held=0xD137,
        pressed=0xD147,jump_ticks=0xD3B2,special=0xD524,surface_counter=0xD3BC,
        frame_counter=0xD12F,probe_counter=0xD507,d448=0xD448).items()}
    for k,a in dict(vx=0xD516,vy=0xD518,maximum=0xD373,input_delta=0xD375,surface_delta=0xD377).items():out[k]=R.s16(s.u16(a))
    for k,a in dict(xu=0xD510,yu=0xD513).items():out[k]=int.from_bytes(bytes(m[a:a+3]),'little')
    out.update(camera_x=s.u16(0xD174),camera_y=s.u16(0xD176),line=s.u16(0xD450),zone=4,
        camera_limits=[s.u16(a) for a in (0xD280,0xD27C,0xD282,0xD27E)],
        damage_request=m[0xD3B0],contact=m[0xD520],contact_nib=m[0xD521],
        invuln=m[0xD3B1],rings=(m[0xD29A]>>4)*10+(m[0xD29A]&15),foot_block=m[0xD36B])
    return out

def palette(r):
    o=W.lab(r);m=o.mem;rows=[]
    for act,char,prior,delta in itertools.product((1,2),(1,2),(0,255),(0,1,191,192,193)):
        line=(568,788)[act-1];m[0xD500]=char;m[0xD131]=prior;m[0xD132]=77
        m[0xD492:0xD496]=bytes(4);o.word(0xD176,line-delta);o.word(0xD450,line)
        o.call(0x9DED)
        rows.append(dict(act=act,character=char,delta=delta,prior=prior,enabled=m[0xD131],
            raster=m[0xD132],requests=[m[0xD493],m[0xD495]]))
    sources=W.raster(r)['palette_modes']
    # Execute original IRQ and saved-palette restore as in accepted R3.
    from m2r3_aqz import palettes
    old=json.loads((ROOT/'data/m2r3/evidence.json').read_text())['palette']
    # Original data independently re-read; existing art-index census is reused.
    assert sources==old['sources']
    histories=[]
    for char in (1,2):
        m[0xD500]=char;m[0xD131]=0;m[0xD132]=255;base='above';history=[]
        for delta in (193,191,1,0,1,193):
            m[0xD492:0xD496]=bytes(4);o.word(0xD176,568-delta);o.word(0xD450,568);o.call(0x9DED)
            requests=[m[0xD493],m[0xD495]]
            if requests==[48,49]:base='full'
            elif requests==[25,10]:base='above'
            history.append(dict(delta=delta,enabled=m[0xD131],raster=m[0xD132],requests=requests,
                original_saved_base=base,upper=base,lower='split' if m[0xD131] else base))
        histories.append(dict(character=char,classification='original9DED execution plus source-backed queued-palette completion model; not natural camera reachability',rows=history))
    # Independently execute the actual saved-CRAM restoration with full49 data.
    from sms_frame_harness import SMS
    full_restore=[]
    for char in (1,2):
        s=SMS(r);s.mem[0xD500]=char;s.mem[0xD472:0xD492]=bytes(sources['fully_submerged_cram']);s.mem[0xD496]=128
        s.cpu.pc=0x1CBD;s.cpu.sp=0xDFE0;s.w16(s.cpu.sp,0x0100);s.cpu.set_breakpoint(0x0100)
        for _ in range(20):
            s.cpu.ticks_to_stop=100000;s.cpu.run()
            if s.cpu.pc==0x0100:break
        assert bytes(s.cram)==bytes(sources['fully_submerged_cram'])
        full_restore.append(dict(character=char,cram_sha256=H(bytes(s.cram))))
    skim=[]
    for act,char,dy,vx,vy,attack in itertools.product((1,2),(1,2),(-1,0,1),(-1024,-1023,1023,1024),(-1,0),(0,2)):
        line=(568,788)[act-1];m[0xD540:0xD940]=bytes(1024)
        m[0xD500]=char;m[0xD298]=act-1;m[0xD503]=attack;m[0xD443]=255
        o.position(816,line+dy);o.word(0xD450,line);o.word(0xD516,vx);o.word(0xD518,vy);o.call(0x4BC0)
        skim.append(dict(act=act,character=char,dy=dy,vx=vx,vy=vy,attack=attack,
            water=m[0xD443],result_vx=R.s16(o.word(0xD516)),result_vy=R.s16(o.word(0xD518))))
    return dict(rom_sha256=R.SHA256,sources=sources,boundaries=rows,skim_controls=skim,
        histories=histories,full_saved_restore=full_restore,
        frames=old['frames'],original_irq_restore=palettes(r)['cram_controls'],
        code=[source(r,*v) for v in [(12,0x9DED,0x9E55),(0,0x4BC0,0x4C09),
            (0,0x3901,0x3938),(0,0x3FEF,0x402A),(0,0x4141,0x429D)]])

def gameplay(r):
    cases=[]
    for act in (0,1):
        g=ZoneGame(r,4,act,hooks={0x4BC0:'skim',0x45ED:'jump',0x4097:'gravity',
            0x402A:'xmove',0x4141:'accel',0x690B:'terrain',0x48F7:'hurt',0x69B2:'ramp'})
        cpu=bytes(g.s.cpu.get_state_view())
        def restore():g.e.restore();g.s.cpu.get_state_view()[:]=cpu
        g.restore_snapshot=restore
        stages=[];pending=[None];returns=set();starts=[];phases=[]
        def phase(name,mm):
            if g.recording and mm.cpu.ix==0xD500:
                v=snap(mm);phases.append([len(g.rows)+1,name]+[v[k] for k in PHASE_KEYS])
        for address,name in [(0x4BC0,'water_before'),(0x4141,'input_before'),(0x402A,'x_before'),(0x4097,'y_before'),(0x690B,'terrain_before')]:
            g.pre[address]=lambda mm,n=name:phase(n,mm)
        g.hook(0x4B55,lambda mm:phase('water_after',mm))
        def engine(mm):
            g._engine_hook(mm)
            if g.recording and mm.cpu.ix==0xD500:starts.append(dict(u=len(g.rows)+1,core=snap(mm)))
        g.s.add_pc_hook(0x64FA,engine)
        def end(mm):
            if pending[0] is not None:
                pending[0]['after']=snap(mm);stages.append(pending[0]);pending[0]=None
        def shared(mm):
            if not g.recording or mm.cpu.ix!=0xD500:return
            ret=mm.u16(mm.cpu.sp)
            if ret not in returns:g.hook(ret,end);returns.add(ret)
            pending[0]=dict(u=len(g.rows)+1,before=snap(mm))
        g.hook(0x3FEF,shared)
        oldrow=g.row
        def row():
            v=oldrow();v['core']=snap(g.s);return v
        g.row=row
        # Authentic corridor: AQZ1 lower opening floor Y686; AQZ2 floor Y942.
        # Speed seeding is explicit; these do not establish entrance reachability.
        fixtures=[(mode,hold) for mode,hold in itertools.product(('ground','air_attack','air_plain','surface_attack'),('tap','hold'))]
        fixtures += [('ground_forward','none'),('ground_reverse','none'),('ground_slow','tap'),('ground_charge','tap')]
        for char,direction,(mode,hold) in itertools.product((1,2),(-1,1),fixtures):
            ground=mode.startswith('ground')
            line=(568,788)[act];floor_y=(686,942)[act]
            y=floor_y if ground else line+8 if mode=='surface_attack' else line+60
            cur=5 if ground else 10 if mode!='air_plain' else 14
            flags=0 if ground else 3 if mode!='air_plain' else 1
            def setup(mm):
                mm.m[0xD500]=mm.m[0xD2C8]=char;mm.m[0xD443]=255
                mm.m[0xD3B2]=32;mm.s.w16(0xD373,1792)
                mm.s.w16(0xD174,680);mm.s.w16(0xD176,min(line-96,(528,784)[act]))
            stages.clear();starts.clear();phases.clear();pending[0]=None
            speed=0 if mode=='ground_charge' else 256 if mode=='ground_slow' else 1536
            g.begin(816,y,vx=direction*speed,vy=0,cur=cur,f3=flags,
                floor=ground,face=direction<0,prev=0x82,width=(168,128)[act],apply=setup,types=(13,60))
            def pad(u,f):
                if mode=='ground_charge':
                    if u<5:return 2|(16 if u==2 else 0)
                    d=direction if u<14 else -direction
                    return (8 if d>0 else 4)|(16 if u==16 else 0)
                d=direction if u<8 or mode=='ground_forward' else -direction
                return (8 if d>0 else 4)|(16 if hold!='none' and 10<=u<(11 if hold=='tap' else 30) else 0)
            rows=g.run(100,padf=pad)[:100]
            cases.append(dict(id=f'a{act+1}-c{char}-d{direction}-{mode}-{hold}',act=act+1,
                character=char,direction=direction,mode=mode,jump=hold,
                fixture='one-time arrival/state seed; speed0 for charge,1px for slow,6px otherwise; input-only thereafter; original layout/objects',
                sequence='default same direction intervals0..7; opposite8 onward; fresh Jump interval10, tap1 or hold20; forward/reverse no-jump controls; charge Down0..4+freshJump2,release5,reverse14,freshJump16; actual polled held/fresh recorded',
                rows=[dict(u=x['u'],frame=x['fr'],core=x['core'],events=x['ev']) for x in rows],
                starts=[x for x in starts if x['u']<=100],
                phases=[x for x in phases if x[0]<=100],
                shared=[x for x in stages if x['u']<=100]))
        print('original act',act+1,'cases',len(cases),flush=True)
    return dict(rom_sha256=R.SHA256,method=__doc__,phase_columns=['u','phase']+PHASE_KEYS,cases=cases)

def main():
    p=argparse.ArgumentParser();p.add_argument('rom',type=Path);p.add_argument('--gameplay',action='store_true');a=p.parse_args()
    r=R.load(a.rom);OUT.mkdir(exist_ok=True,parents=True)
    save('palette-original.json',palette(r))
    if a.gameplay:save('original-game.json',gameplay(r))

if __name__=='__main__':main()

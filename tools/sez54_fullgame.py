"""Guarded whole-game SEZ3 boss scenarios; writes occur at player-update boundaries."""
import argparse
import hashlib
import json
from pathlib import Path
import rom as R
from sez_surfaces_rig import ZoneGame

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'data/rom-cache/sez/boss-54-fullgame.json'

def build(r,debug=False):
    g=ZoneGame(r,2,2,hooks={0x16D0:'after_player',0x16D3:'after_objects',0xA3D8:'boss_contact',0xA4A4:'child_contact'})
    s,m=g.s,g.m
    def slots():
        return [dict(slot=b,type=m[b],state=m[b+1],req=m[b+2],frame=m[b+6],duration=m[b+7],x=s.u16(b+17),y=s.u16(b+20),
            vx=R.s16(s.u16(b+22)),vy=R.s16(s.u16(b+24)),hp=m[b+38],cooldown=m[b+52],defeated=m[b+53],drop=m[b+54],
            token=m[b+62],f3=m[b+3],f4=m[b+4]) for b in range(0xD540,0xDA00,64) if 0<m[b]<0xF0]
    g._snap_objs=slots
    original_row=g.row
    def row():
        v=original_row();v.update(zone=m[0xD297],act=m[0xD298],limits=[s.u16(a) for a in (0xD280,0xD282,0xD27C,0xD27E)],
            pan=[s.u16(0xD2DA),s.u16(0xD2DC)],timer=m[0xD2BE],clear=m[0xD293],player_req=m[0xD502],damage=m[0xD3B0]);return v
    g.row=row
    marks=[];spawns=[]
    for pc,name,bank in ((0x974C,'init',30),(0x9799,'trigger',30),(0x97FD,'pan',30),(0xA291,'combat_init',30),
        (0xA429,'hp_decrement',30),(0x81DF,'bonus_spawn',30),(0x32F9,'results',None),(0x4E97,'act_loader',None)):
        def mark(mm,pc=pc,name=name,bank=bank):
            if not g.recording or (bank is not None and s.slot[2]!=bank):return
            marks.append(dict(u=len(g.rows)+1,event=name,pc=pc,zone=m[0xD297],act=m[0xD298],ix=mm.cpu.ix,
                hp_before=m[mm.cpu.ix+38] if name=='hp_decrement' else None))
        g.hook(pc,mark)
    def spawn(mm):
        if g.recording and m[mm.cpu.ix]==84:
            spawns.append(dict(u=len(g.rows)+1,type=m[s.u16(mm.cpu.ix+14)]))
    g.hook(0x5EE1,spawn)
    mode=['cycle']
    def park(x,y,flags=0,floor=2,st=5):
        s.w16(0xD511,x);s.w16(0xD514,y);s.w16(0xD516,0);s.w16(0xD518,0)
        m[0xD501]=m[0xD502]=st;m[0xD503]=flags;m[0xD522]=floor;m[0xD3B0]=m[0xD3B1]=m[0xD520]=0;m[0xD29A]=0x47
    original_engine=g._engine_hook
    def engine(mm):
        original_engine(mm)
        if not g.recording or mm.cpu.ix!=0xD500:return
        if mode[0]=='case':return
        b=next((b for b in range(0xD540,0xDA00,64) if m[b]==84),None)
        if b is None and len(g.rows)>100:return
        if b is None or m[b+1]<3:park(3060,620)
        elif m[b+1] not in (4,5):park(3000,620)
    g.hook(0x64FA,engine)
    # Contact injections run after the real player/terrain update, before objects.
    case=[None]
    def after_player(mm):
        if not g.recording:return
        b=next((b for b in range(0xD540,0xDA00,64) if m[b]==84),None)
        if mode[0]=='case' and b is not None:
            c=case[0];park(s.u16(b+17)+c['point'][0],s.u16(b+20)+c['point'][1],c['attack']|c['hurt']|c['blink'],c['floor'])
            m[0xD532]=c['power'];m[0xD523]=0;s.w16(0xD518,256);return
        if mode[0]!='fight':return
        if b is not None and m[b+1] in (7,8,9,10) and m[b+52]<=1 and not m[b+53]:
            park(s.u16(b+17),s.u16(b+20)-80,3,0,10);s.w16(0xD518,256);m[0xD523]=0
    g.pre[0x16D0]=after_player
    def run(name,updates):
        marks.clear();spawns.clear();g.begin(3060,620,rings=0x47,types=(84,85,52,18,15,10))
        rows=g.run(updates,stop=lambda v,rs:v['zone']==3 and v['cur']==5)
        (ROOT/f'build/sez54-{name}-debug.json').write_text(json.dumps(dict(rows=rows,marks=marks),separators=(',',':')))
        transitions=[];old=None
        for v in rows:
            b=next((o for o in v['o'] if o['type']==84),None)
            key=(b['state'],b['req']) if b else None
            if key!=old:transitions.append(dict(u=v['u'],boss=b,camera=[v['d174'],v['d176']],zone=v['zone'],act=v['act']))
            old=key
        return dict(updates=len(rows),transitions=transitions,marks=list(marks),spawns=list(spawns),last=rows[-1],
            trajectory_sha256=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest(),
            states=sorted({o['state'] for v in rows for o in v['o'] if o['type']==84}),
            max_children=max(sum(o['type']==85 for o in v['o']) for v in rows),
            children_after_final_hit=[dict(u=v['u'],children=[o for o in v['o'] if o['type']==85]) for v in rows
                if any(o['type']==84 and o['defeated']==255 for o in v['o']) and any(o['type']==85 for o in v['o'])][:5])
    cycle=run('cycle',1100)
    replay=run('replay',1100)
    assert cycle==replay,'history-independent snapshot replay diverged'
    mode[0]='fight';fight=run('fight',4500)
    assert [v['hp_before'] for v in fight['marks'] if v['event']=='hp_decrement']==list(range(8,0,-1))
    assert fight['last']['zone']==3 and fight['last']['act']==0 and fight['last']['cur']==5
    assert len([v for v in fight['spawns'] if v['type']==52])==5
    assert fight['children_after_final_hit'] and fight['max_children']==3
    assert set(cycle['states']+fight['states'])==set(range(13))-{5}
    # State5 is transient: bonus_spawn hook observes its callback even if its type
    # has already become0F at the next row. All thirteen are source-reachable.
    from sez54_runtime import Lab,prepare
    import itertools
    lab=Lab(r);contact_cases=[];mode[0]='case'
    for attack,hurt,blink,power,point in itertools.product((0,2),(0,64),(0,128),(0,6),((0,-64),(0,-24),(-28,-24),(0,24))):
        case[0]=dict(attack=attack,hurt=hurt,blink=blink,power=power,point=list(point),floor=2)
        # Use original creator + combat initializer fields, then force the
        # audited state9 for a controlled whole-game contact boundary fixture.
        lab=Lab(r);lab.call(0xA291);base=bytes(lab.m[0xD700:0xD740])
        def apply(gg,base=base):
            gg.m[0xD540:0xDA00]=bytes(0x4C0);gg.m[0xD700:0xD740]=base
            gg.m[0xD701]=9;gg.m[0xD702]=9;gg.m[0xD704]=2
            gg.s.w16(0xD711,3100);gg.s.w16(0xD714,580);gg.s.w16(0xD716,0);gg.s.w16(0xD718,0)
            gg.s.w16(0xD174,2900);gg.s.w16(0xD176,462)
            gg.m[0xD404]=1
        g.begin(3000,620,rings=0x47,apply=apply,types=(84,85,52,18,15,10))
        rows=g.run(1);v=rows[0];b=next(o for o in v['o'] if o['type']==84)
        expect=prepare(lab,*point,frame=15,attack=attack,hurt=hurt,inv=blink,power=power,floor=2)
        assert b['hp']==expect['hp'],(case[0],v,expect)
        assert v['damage']==expect['player']['damage'],(case[0],v,expect)
        contact_cases.append(dict(input=case[0],row=v))
    return dict(cycle=cycle,fight=fight,contact_cases=contact_cases,assertions=6+2*len(contact_cases),
        guarded_replay_identical=True,method='ZoneGame hidden-state guarded restore; real game player/terrain/camera/scheduler/results. Synthetic player writes before player update and contact writes after player update; boss callbacks unchanged. Contact cases use original creator/init fields with forced state9; natural cycle/fight use real mapped creation.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--check',action='store_true');args=p.parse_args()
    data=build(R.load(args.rom))
    if args.check:assert data==json.loads(OUTPUT.read_text(encoding='utf-8'))
    else:OUTPUT.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(assertions=data['assertions'],fight_updates=data['fight']['updates'],contact_cases=len(data['contact_cases']))))

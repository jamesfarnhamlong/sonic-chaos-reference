"""AQZ A4 natural placement loader/scheduler fixtures, complete CPU snapshots.

Synthetic boundary player/camera controls are explicit; enemy/code/layout untouched.
"""
import argparse
from pathlib import Path
import aqz_foundation as F
import aqz_enemies as A
import level_package as L
from sez_surfaces_rig import ZoneGame
OUTPUT=F.OUT/'enemies-3c-3d-game-checks.json'

def build(r):
    out=dict(rom_sha256=L.ROM_SHA256,research_base=A.BASE,method=__doc__,placements=[],cases=[])
    for act in (0,1):
        g=ZoneGame(r,4,act,hooks={0x5DD1:'objects',0x9251:'3c_init',0x926F:'3c_up',0x9274:'3c_down',0x9284:'3c_contact',0x9304:'3d_init',0x932B:'3d_active',0x630B:'forced_hurt',0x5F3D:'defeat_gate',0x48BC:'player_contact',0x48F7:'hurt',0x49C3:'rebound',0x61E1:'lifecycle',0x80EB:'creator'})
        s,m=g.s,g.m;cpu=bytes(s.cpu.get_state_view())
        def restore():g.e.restore();s.cpu.get_state_view()[:]=cpu
        g.restore_snapshot=restore
        target={'rec':None,'mode':'passive','contact':False}
        def snap():
            rows=[];rec=target['rec']
            for o in g.objs((60,61,15)):
                b=0xD540+o['slot']*64
                if s.u16(b+58)!=rec['world_x'] or s.u16(b+60)!=rec['world_y']:continue
                rows.append(dict(o,origin=[s.u16(b+58),s.u16(b+60)],token=m[b+62],parameter=m[b+63],counter=m[b+53],
                    fractions=[m[b+16],m[b+19]],extent=[m[b+44],m[b+45]],flags3=m[b+3],contact=m[b+33],callback=s.u16(b+12)))
            return rows
        g._snap_objs=snap;oldrow=g.row
        def row():
            rec=target['rec'];return dict(oldrow(),water=m[0xD443],waterline=s.u16(0xD450),clock=m[0xD12F],occupancy=m[0xD400+rec['index']-1],score=list(m[0xD29D:0xD2A0]))
        g.row=row
        def hold(mm):
            rec=target['rec'];mode=target['mode'];os=snap();live=next((o for o in os if o['type'] in (60,61)),None)
            x,y=(live['x'],live['y']) if live else (rec['world_x'],rec['world_y'])
            u=len(g.rows)
            if mode=='delete_recreate':
                x,y=rec['world_x']+(1000 if 32<=u<56 else 0),rec['world_y']
                cam=x-(320 if u<12 or 56<=u<80 else 100)
            elif mode=='sleep_wake':cam=x-(320 if u<12 or 32<=u<48 else 100)
            elif mode=='defeat_backtrack':
                cam=rec['world_x']+(1000 if 40<=u<64 else -320 if u<12 or 64<=u<80 else -100)
            else:cam=x-(320 if u<12 else 100)
            if cam<0:cam=x+64 # near the left world edge, use LEFT-64 creation band
            s.w16(0xD174,cam);s.w16(0xD176,max(0,y-100))
            active=mode in ('attack','ordinary','invincible','hurt','blink','defeat_backtrack') and u>=16 and live and live['frame']!=0
            if target['contact']:return
            s.w16(0xD511,x if active else x+60);s.w16(0xD514,y if active else y+60);s.w16(0xD516,0);s.w16(0xD518,0)
            flags={'attack':3,'defeat_backtrack':3,'ordinary':1,'invincible':1,'hurt':65,'blink':129}.get(mode,129)
            m[0xD503]=flags;m[0xD532]=6 if mode=='invincible' else 0
            if flags&128:m[0xD3B1]=240
            m[0xD502]=10 if mode in ('attack','defeat_backtrack') else 14
            m[0xD522]=0;m[0xD3C0]=0
        g.pre[0x5DD1]=hold
        def water_probe(mm):
            rec=target['rec'];b=mm.cpu.ix
            if target['mode']=='waterline_probe' and m[b]==61 and s.u16(b+58)==rec['world_x']:s.w16(0xD450,rec['world_y']-10)
        g.pre[0x932B]=water_probe
        def detect(mm):
            if not g.recording or mm.cpu.ix==0xD500:return
            b=mm.cpu.ix;rec=target['rec']
            if m[b] in (60,61,15) and s.u16(b+58)==rec['world_x'] and s.u16(b+60)==rec['world_y']:
                if target['mode'] in ('attack','ordinary','invincible','blink','defeat_backtrack') and m[b+33]&15:target['contact']=True
        g.hook(0x5F42,detect);g.hook(0x6313,detect)
        def compact(x):return {k:x[k] for k in ('u','x','y','vx','vy','cur','req','f3','d520','d521','d3c0','d174','d176','water','waterline','clock','occupancy','score','ev','o')}
        def run(rec,mode,n):
            target.update(rec=rec,mode=mode,contact=False)
            g.begin(rec['world_x']+60,rec['world_y']+60,cur=14,f3=129,floor=False,rings=0x32,width=(168,128)[act],types=(60,61,15))
            rows=g.run(n);assert len(rows)>=n,(rec,mode,len(rows));return [compact(x) for x in rows[:n]]
        recs=[x for x in A.placements(r) if x['act']==act]
        for rec in recs:
            rows=run(rec,'passive',180);live=[o for x in rows for o in x['o'] if o['type'] in (60,61)]
            assert len(live)>150,(rec,'creation/retention',len(live))
            assert all(o['origin']==[rec['world_x'],rec['world_y']] for o in live)
            out['placements'].append(dict(placement=rec,rows=rows))
        # Coordinate-independent path cases represented once per act/type/parameter.
        seen=set()
        for rec in recs:
            key=(rec['type_id'],rec['parameter'])
            if key in seen:continue
            seen.add(key)
            cases={}
            for mode in ('attack','ordinary','invincible','hurt','blink','sleep_wake','delete_recreate','defeat_backtrack')+(('waterline_probe',) if rec['type_id']=='0x3D' else ()):
                rows=run(rec,mode,112);cases[mode]=rows
                if mode=='delete_recreate':
                    assert any(not x['o'] for x in rows[40:56]),(rec,'delete')
                    assert any(x['o'] for x in rows[85:]),(rec,'recreate')
                if mode in ('attack','invincible','defeat_backtrack'):
                    defeated=any(o['type']==15 for x in rows for o in x['o'])
                    assert defeated==(rec['type_id']=='0x3D'),(rec,mode,'defeat verdict')
                if mode=='hurt':assert not any(o['type']==15 for x in rows for o in x['o'])
                if mode=='blink':assert not any('hurt' in x['ev'] for x in rows),(rec,'blink suppression')
                if mode=='ordinary':assert any('hurt' in x['ev'] for x in rows),(rec,'ordinary damage')
                if mode=='defeat_backtrack' and rec['type_id']=='0x3D':
                    assert not any(o['type']==61 for x in rows[80:] for o in x['o']),('spent recreation',rec)
                if mode=='waterline_probe':
                    live=[o for x in rows for o in x['o'] if o['type']==61]
                    assert any(o['y']<rec['world_y']-10 for o in live) and any(o['y']>=rec['world_y']-10 for o in live)
                    passive=next(p['rows'] for p in out['placements'] if p['placement']==rec)
                    assert [[o for o in x['o'] if o['type']==61] for x in rows]==[[o for o in x['o'] if o['type']==61] for x in passive[:112]],('waterline_motion_independence',rec)
            out['cases'].append(dict(placement=rec,cases=cases))
        # Independent full-state restore after the parameter/contact fixture history.
        rec=recs[-1];expected=next(x['rows'] for x in out['placements'] if x['placement']==rec)
        assert run(rec,'passive',180)==expected,('complete_snapshot_replay',act)
    out['row_count']=sum(len(x['rows']) for x in out['placements'])+sum(len(v) for x in out['cases'] for v in x['cases'].values())
    out['fixture']='Natural original loader/slots/callbacks/layout retained. Synthetic player/camera boundary controls make isolated paths reachable; contact cases stop player writes after first qualifying overlap so following original player damage/rebound can execute. Passive uses blinking flag for terrain protection; lifecycle journey uses canonical screenX320 creation band then100 wake band. No enemy or occupancy injection.'
    out['complete_snapshot_replay_acts']=[0,1]
    out['tool_sha256']=F.digest(Path(__file__).read_text(encoding='utf-8').encode());return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();v=build(L.load_rom(a.rom))
    if a.check:assert OUTPUT.read_text(encoding='utf-8')==F.dumps(v)
    else:OUTPUT.write_text(F.dumps(v),encoding='utf-8')
    print('AQZ A4 natural placements',len(v['placements']),'rows',v['row_count'])
if __name__=='__main__':main()

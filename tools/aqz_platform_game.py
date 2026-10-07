"""Natural AQZ $3F loader/scheduler traces, with labelled boundary player writes.

No platform is injected. Complete CPU bytes (prefix/EI shadow/frame_tick included),
RAM, VDP and harness snapshot are restored; original code and layout are retained.
"""
import argparse
from pathlib import Path
import aqz_foundation as F
import aqz_platform_3f as A
import level_package as L
from sez_surfaces_rig import ZoneGame
OUTPUT=F.OUT/'platform-3f-game-checks.json'

def build(r):
    out=dict(rom_sha256=L.ROM_SHA256,method=__doc__,placements=[])
    for rec in A.placements(r):
        act=rec['act'];g=ZoneGame(r,4,act,hooks={0x4B46:'water',0x5DD1:'objects',0x80EB:'creator',0x85FE:'gate13',0x8719:'fall',0x87E2:'excursion',0x8628:'route_x',0x86A1:'route_y'})
        s,m=g.s,g.m;cpu=bytes(s.cpu.get_state_view())
        def restore():g.e.restore();s.cpu.get_state_view()[:]=cpu
        g.restore_snapshot=restore
        def snap():
            rows=[]
            for o in g.objs((63,)):
                b=0xD540+o['slot']*64
                if s.u16(b+58)!=rec['world_x']:continue
                rows.append(dict(o,origin=[s.u16(b+58),s.u16(b+60)],fractions=[m[b+16],m[b+19]],
                    token=m[b+62],flags3=m[b+3],timer=m[b+30],fall=m[b+39],sag=m[b+53],sag_return=m[b+51],
                    tick=m[b+48],latch=m[b+49],reload=m[b+52],period=m[b+55],carry_x=s.u16(b+35),carry_y=s.u16(b+56)))
            return rows
        g._snap_objs=snap
        oldrow=g.row
        def row():return dict(oldrow(),water=m[0xD443],waterline=s.u16(0xD450),occupancy=m[0xD400+rec['index']-1])
        g.row=row
        def compact(row):
            return {k:row[k] for k in ('u','x','y','vx','vy','cur','req','f3','f22','f23','d3c0','d174','d176','ev','o','water','waterline','occupancy')}
        def hold(mm):
            os=snap();x,y=(os[0]['x'],os[0]['y']) if os else (rec['world_x'],rec['world_y'])
            if mode=='delete_recreate':
                x,y=rec['world_x']+(1000 if 24<=len(g.rows)<48 else 0),rec['world_y']
                s.w16(0xD174,x-(320 if 48<=len(g.rows)<72 else 100));s.w16(0xD176,y-100)
            s.w16(0xD511,x);s.w16(0xD514,y-offset);s.w16(0xD516,0);s.w16(0xD518,1792 if offset==14 else 0)
            m[0xD502]=14
            if mode=='rider':m[0xD503]=0x81
        g.pre[0x4B46]=hold
        g.pre[0x5DD1]=hold
        traces={}
        for mode,offset,n in [('passive',60,24),('rider',14,{131:180,134:1630,139:740}[int(rec['parameter'],16)]),('delete_recreate',60,120)]:
            g.begin(rec['world_x'],rec['world_y']-offset,cur=14,f3=1,floor=False,width=(168,128)[act],types=(63,))
            rows=g.run(n);assert len(rows)>=n,(mode,len(rows));rows=[compact(x) for x in rows[:n]]
            assert any(x['o'] for x in rows),(rec,mode)
            live=[o for x in rows for o in x['o']]
            assert all(o['p3f']==int(rec['parameter'],16) and o['origin']==[rec['world_x'],rec['world_y']] for o in live)
            if mode=='rider':
                expected={131:4,134:7,139:14}[int(rec['parameter'],16)]
                assert any(o['state']==expected for o in live),(rec,expected,{o['state'] for o in live})
                assert any(x['d3c0'] for x in rows),(rec,'no carry')
            if mode=='delete_recreate':
                assert any(not x['o'] for x in rows[30:48]),(rec,'no deletion')
                assert any(x['o'] and x['o'][0]['x']==rec['world_x'] for x in rows[55:]),(rec,'no recreation')
            traces[mode]=rows
        # Replay from complete snapshot, without register-only/NOP repairs.
        mode='passive';offset=60;g.begin(rec['world_x'],rec['world_y']-offset,cur=14,f3=1,floor=False,width=(168,128)[act],types=(63,))
        replay=[compact(x) for x in g.run(24)[:24]]
        assert replay==traces['passive'],('complete_snapshot_replay',rec)
        out['placements'].append(dict(placement=rec,synthetic='Player anchor/velocity/request14 held at original water-test and object-phase boundaries; platforms exclusively created by original mapped loader. Rider follows live platform anchor, Vy=7 to pass the relative-speed gate, movement flag3=81 prevents unrelated terrain damage interrupting the scripted path. Canonical terrain remains active before object-phase contact write. Delete/recreate case also writes camera: leave by1000, return through canonical right outer creation band (screenX320), then wake at screenX100.',traces=traces,replay_equal=True))
    out['row_count']=sum(len(t) for p in out['placements'] for t in p['traces'].values())
    out['tool_sha256']=F.digest(Path(__file__).read_text(encoding='utf-8').encode())
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();v=build(L.load_rom(a.rom))
    if a.check:assert OUTPUT.read_text(encoding='utf-8')==F.dumps(v)
    else:OUTPUT.write_text(F.dumps(v),encoding='utf-8')
    print('Natural platform game rows',v['row_count'])
if __name__=='__main__':main()

"""Arrival-assisted original AQZ1 routes: unmodified layout/objects/code.

Player, character and camera are seeded once at an update boundary. Subsequent
movement is input only. This is not a natural route from the act entrance.
"""
import argparse
import json
from pathlib import Path
import rom as R
from sez_surfaces_rig import ZoneGame

ROOT=Path(__file__).resolve().parents[1]


def build(r):
    g=ZoneGame(r,4,0,hooks={0x9251:'spear_init',0x9284:'spear_contact',0x630B:'forced_hurt',0x48F7:'hurt',0x61E1:'lifecycle'})
    cpu=bytes(g.s.cpu.get_state_view())
    def restore():g.e.restore();g.s.cpu.get_state_view()[:]=cpu
    g.restore_snapshot=restore
    cases=[]
    for character,mode in ((c,m) for c in (1,2) for m in ('ground','above')):
        def setup(mm):
            m=mm.m;s=mm.s;m[0xD500]=m[0xD2C8]=character
            s.w16(0xD174,900);s.w16(0xD176,540)
        g.begin(1024,686 if mode=='ground' else 600,cur=5 if mode=='ground' else 10,
                f3=0 if mode=='ground' else 3,floor=mode=='ground',prev=0x82,rings=0x32,
                width=168,apply=setup,types=(60,))
        rows=g.run(200,padf=lambda u,f:8 if u<130 else 0)
        # Every spear record includes the actual live slot and origin token.
        compact=[]
        for x in rows[:200]:
            compact.append({k:x[k] for k in ('u','x','y','cur','req','f3','d12f','d174','d176','ev','o')})
        cases.append(dict(character=character,mode=mode,rows=compact,
            observed_spears=sorted(set(o[0] for row in compact for o in row['o'])),
            hurt_updates=[x['u'] for x in compact if 'hurt' in x['ev']]))
    return dict(method=__doc__,rom_sha256=R.SHA256,cases=cases)


def main():
    p=argparse.ArgumentParser();p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args()
    v=build(R.load(a.rom));text=json.dumps(v,indent=2)+'\n';out=ROOT/'data/m2r3/gameplay.json'
    if a.check:assert out.read_text()==text
    else:out.write_text(text)
    print(json.dumps([{k:v for k,v in x.items() if k!='rows'} for x in v['cases']]))


if __name__=='__main__':main()

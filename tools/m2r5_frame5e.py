"""Arrival-assisted original sign routes; never inject state or contacts."""
import sys,json,argparse,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import rom as R
import g2e_score as G
from g0_rig import Session

CASES=[(4,1,0,5120,430),(5,1,1,4096,686),(10,3,0,4096,366),(16,5,0,4096,430)]
def run(rom,case,offset=0):
    act,zone,sub,width,y=case
    ses=Session(rom);ses.set_start_index(zone,sub)
    rows=[];writes=[];active=[False]
    def snap(s):
        m=s.mem
        return dict(frame=s.frame,x=s.u16(0xD511),y=s.u16(0xD514),state=m[0xD501],request=m[0xD502],bg=m[0xD522],contacts=m[0xD523],selected=m[0xD506],counter=m[0xD507],camx=s.u16(0xD174))
    def engine(s):
        if active[0] and s.cpu.ix==0xD500:rows.append(snap(s))
    ses.hook(0x64FA,engine)
    old=ses.s._write
    def write(a,v):
        if active[0] and a in (0xD522,0xD523) and ses.m[a]!=v:
            writes.append(dict(pc=ses.s.cpu.pc,bank=ses.s.slot[2],address=a,value=v,**snap(ses.s)))
        old(a,v)
    ses.s._write=write;ses.s.cpu.set_write_callback(write)
    def arrival(s):
        s.w16(0xD2D6,width-400);s.w16(0xD2D8,max(0,y-120))
        s.w16(0xD511,width-300+offset);s.w16(0xD514,y-40)
    ses.boot_new_game(character=1,arrival=arrival)
    active[0]=True
    for i in range(1100):
        ses.s.pad=8 if ses.m[0xD501]!=32 else 0
        ses.s.run_frame()
        if ses.m[0xD297]!=zone or ses.m[0xD298]!=sub:break
        if any(r['selected']==94 and r['request']==32 for r in rows):break
    return dict(act=act,fixture='START_INDEX + ARRIVAL position/camera only; then Right until state20, neutral thereafter',injected_state_contact=False,rows=rows,writes=writes,end=ses.snap())
def main():
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--phases',action='store_true');a=p.parse_args();rom=R.load(a.rom)
    if a.phases:
        cases=[]
        for case in CASES:
            for offset in (1,2,3,4,5):
                print(case[0],offset,flush=True);cases.append(dict(offset=offset,**run(rom,case,offset)))
        (ROOT/'data/m2r5/phase-routes.json').write_text(json.dumps(cases,indent=2)+'\n');return
    out=dict(rom_sha256=R.SHA256,evidence='Actual Z80 in approximate SMS harness; controlled arrival, NOT input-only full act',cases=[])
    for case in CASES:
        print('running',case[0],flush=True);out['cases'].append(run(rom,case))
        d=ROOT/'data/m2r5';d.mkdir(parents=True,exist_ok=True);(d/'original-sign-routes.json').write_text(json.dumps(out,indent=2)+'\n')
    out['source']=[]
    for bank,start,end in [(0,0x7666,0x7740),(0,0x716B,0x7210),(0,0x64CB,0x64F0),(12,0xAB8C,0xABA0),(12,0x83A6,0x840F)]:
        out['source'].append(dict(bank=bank,start=start,end=end,instructions=G.disasm(rom,bank,start,end)))
    (d/'original-sign-routes.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()

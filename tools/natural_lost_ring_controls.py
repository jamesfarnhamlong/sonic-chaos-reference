"""Whole-game controlled projectile placement; player is free after initial fixture.
Only camera is held to the stated reference. Original type-$5D init/contact,
player callbacks and scheduler execute. Not a natural projectile birth.
"""
import json
from pathlib import Path
import rom as R
from sez_surfaces_rig import ZoneGame

def build(r):
 out=[]
 for zone,act,x,y,cx,cy in [(4,2,1000,238,872,78),(4,2,1856,238,1727,78),(4,2,1743,238,1727,78),(4,2,1750,238,1727,78)]:
  g=ZoneGame(r,zone,act);s,m=g.s,g.m;cpu=bytes(s.cpu.get_state_view())
  def restore():g.e.restore();s.cpu.get_state_view()[:]=cpu
  g.restore_snapshot=restore
  def setup(gg):
   m[0xD540:0xDA00]=bytes(0x4C0)
   s.w16(0xD174,cx);s.w16(0xD176,cy)
   b=0xD700;m[b]=93;s.w16(b+17,x+4);s.w16(b+20,y)
   if x==1000:
    floor_block=m[0xC001+8*80+58]
    m[0xC001:0xD000]=bytes(4095)
    for col in range(80):m[0xC001+8*80+col]=floor_block
  old=g._engine_hook
  def camera(mm):
   old(mm)
   if g.recording and mm.cpu.ix==0xD500:
    s.w16(0xD174,cx);s.w16(0xD176,cy)
    if len(g.rows)==130 and x in (1743,1750):
     b=0xD700;m[b:b+64]=bytes(64);m[b]=93;s.w16(b+17,s.u16(0xD511)+4);s.w16(b+20,238)
    if x==1000:
     for b in range(0xD540,0xDA00,64):
      if m[b] not in (0,6,93):m[b:b+64]=bytes(64)
  g.hook(0x64FA,camera)
  g.begin(x,y,cur=1,floor=True,rings=1,vy=1792,apply=setup,types=(6,93))
  rows=g.run(240)
  out.append(dict(zone=zone,act=act,x=x,y=y,camera=[cx,cy],rows=rows))
 return dict(rom_sha256=R.SHA256,method=__doc__,cases=out)
if __name__=='__main__':
 import sys
 d=build(R.load(sys.argv[1]));p=Path(__file__).resolve().parents[1]/'data/rom-cache/natural-lost-ring-controls.json';p.write_text(json.dumps(d,indent=1)+'\n')
 for c in d['cases']:print(c['zone'],c['x'],'hurt',next((v['u'] for v in c['rows'] if v['req']==30),None),'pickup',next((v['u'] for v in c['rows'] if v['u']>4 and v['rings']),None),'end',[(k,c['rows'][-1][k]) for k in ('x','y','rings')])

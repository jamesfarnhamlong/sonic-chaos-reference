"""Natural AQZ3 body-hit trace; ROM stays local.
Player/camera parking before release is a fixture. The boss is never rewritten.
After release there are no player writes. The actual boss contact requests hurt.
"""
import json
from pathlib import Path
import rom as R
from sez_surfaces_rig import ZoneGame

def run(rom):
 g=ZoneGame(rom,4,2,hooks={0x48F7:'hurt',0x16D0:'after_player',0x16D3:'after_objects'})
 s,m=g.s,g.m
 cpu=bytes(s.cpu.get_state_view())
 def restore():
  g.e.restore();s.cpu.get_state_view()[:]=cpu
 g.restore_snapshot=restore
 release=[None];events=[]
 def snap(tag):
  return dict(tag=tag,u=len(g.rows),player=[s.u16(0xD511),s.u16(0xD514),R.s16(s.u16(0xD516)),R.s16(s.u16(0xD518)),m[0xD501],m[0xD502],m[0xD503],m[0xD522],m[0xD523],m[0xD29A]],rings=[dict(slot=b,state=m[b+1],req=m[b+2],x=s.u16(b+17),y=s.u16(b+20),vx=R.s16(s.u16(b+22)),vy=R.s16(s.u16(b+24)),callback=s.u16(b+12),counter=m[b+7]) for b in range(0xD540,0xDA00,64) if m[b]==6])
 old=g._engine_hook
 def driver(mm):
  old(mm)
  if not g.recording or mm.cpu.ix!=0xD500:return
  if len(g.rows)<12:s.w16(0xD174,1540);s.w16(0xD176,46)
  if release[0] is not None:
   events.append(snap('boundary'));return
  shots=[b for b in range(0xD540,0xDA00,64) if m[b]==89 and m[b+1] in (9,10) and 214<=s.u16(b+20)<=248 and 1780<=s.u16(b+17)<=1940]
  x=s.u16(shots[0]+17) if shots else 1800
  s.w16(0xD511,x);s.w16(0xD514,238);s.w16(0xD516,0);s.w16(0xD518,1792)
  m[0xD501]=m[0xD502]=1;m[0xD503]=0 if shots else 128;m[0xD522]=2;m[0xD523]=0;m[0xD3B1]=0 if shots else 240;m[0xD29A]=1;m[0xD532]=0
  if shots:release[0]=len(g.rows);events.append(snap('release'))
 g.hook(0x64FA,driver)
 for pc,name in [(0x48F7,'hurt_entry'),(0x494F,'hurt_velocity'),(0x5E9C,'allocation'),(0x16D0,'after_player'),(0x16D3,'after_objects'),(0x9A2B,'ring_init'),(0x9A9E,'ring_motion'),(0x9A98,'pickup_eligible'),(0x9AF1,'pickup')]:
  def hook(mm,pc=pc,name=name):
   if g.recording and release[0] is not None and (pc<0x8000 or s.slot[2]==12):events.append(snap(name))
  g.hook(pc,hook)
 g.begin(1800,238,rings=1,types=(6,89,93))
 g.run(4000,stop=lambda v,rs:release[0] is not None and len(rs)>release[0]+310)
 assert release[0] is not None,('no natural body contact reached fixture',g.rows[-1])
 return dict(rom_sha256=R.SHA256,release=release[0],events=events)

if __name__=='__main__':
 import sys
 result=run(R.load(sys.argv[1]));out=Path(__file__).resolve().parents[1]/'data/rom-cache/natural-lost-ring-hurt.json'
 out.write_text(json.dumps(result,indent=1)+'\n');print('wrote',out,'events',len(result['events']))

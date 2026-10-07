"""AQZ3 original loader/scheduler/renderer fight traces, complete exported CPU restore.
Synthetic player/camera controls run at update boundaries; boss and children are never placed or rewritten.
"""
import argparse,json
import aqz_foundation as F
import aqz59_runtime as A
import rom as R
from sez_surfaces_rig import ZoneGame
OUTPUT=F.OUT/'boss-59-game-checks.json'
def build(r):
 g=ZoneGame(r,4,2,hooks={0x16D0:'after_player',0x16D3:'after_objects',0x61E1:'lifecycle',0x48F7:'hurt'})
 s,m=g.s,g.m;cpu=bytes(s.cpu.get_state_view())
 def restore():g.e.restore();s.cpu.get_state_view()[:]=cpu
 g.restore_snapshot=restore
 mode=['cycle'];marks=[];blocked=[[]];released=[False];clear_start=[None]
 def boss():return next((b for b in range(0xD540,0xDA00,64) if m[b]==89),None)
 def snap():
  return [dict(slot=b,type=m[b],state=m[b+1],request=m[b+2],frame=m[b+6],duration=m[b+7],x=s.u16(b+17),y=s.u16(b+20),fractions=[m[b+16],m[b+19]],vx=R.s16(s.u16(b+22)),vy=R.s16(s.u16(b+24)),angle=m[b+10],hp=m[b+38],counter30=m[b+30],cooldown31=m[b+31],field34=m[b+52],field35=m[b+53],field38=m[b+56],field23=m[b+35],field24=m[b+36],parameter=m[b+63],token=m[b+62],extent=list(m[b+44:b+46]),cached_screen=list(m[b+26:b+30]),flags3=m[b+3],flags4=m[b+4],callback=s.u16(b+12)) for b in range(0xD540,0xDA00,64) if m[b] in (89,90,91,92,93,52,18,15,10)]
 g._snap_objs=snap;oldrow=g.row
 def row():return dict(oldrow(),zone=m[0xD297],act=m[0xD298],timer=m[0xD2BE],clear=m[0xD293],limits=[s.u16(a) for a in (0xD280,0xD282,0xD27C,0xD27E)],pan=[s.u16(0xD2DA),s.u16(0xD2DC)],water=m[0xD443],waterline=s.u16(0xD450),sprite_palette=m[0xD495],selector=m[0xD3B3],occupancy=m[0xD400])
 g.row=row;oldengine=g._engine_hook
 def park(x,y,flags=129,st=14,floor=0):
  s.w16(0xD511,x);s.w16(0xD514,y);s.w16(0xD516,0);s.w16(0xD518,0);m[0xD503]=flags;m[0xD3B1]=240 if flags&128 else 0;m[0xD501]=m[0xD502]=st;m[0xD522]=floor;m[0xD29A]=0x47;m[0xD532]=0
 def hold(mm):
  oldengine(mm)
  if not g.recording or mm.cpu.ix!=0xD500:return
  b=boss()
  if released[0]:return
  if b is None and len(g.rows)>500:released[0]=True;return
  park(1800,238)
  if len(g.rows)<12:s.w16(0xD174,1540);s.w16(0xD176,46)
 g.hook(0x64FA,hold)
 def contact(mm):
  if not g.recording or released[0]:return
  child=next((b for b in range(0xD540,0xDA00,64) if m[b]==90 and m[b+1] in (1,2) and not m[b+31]),None)
  if child and mode[0]!='passive_children':park(s.u16(child+17),s.u16(child+20),3,10);s.w16(0xD518,256)
  b=boss()
  if b is None:return
  st=m[b+1]
  if mode[0].startswith('fight') and len(g.rows)>1400 and st in (9,10,17,20):
   final=int(mode[0].split('_')[1])
   if m[b+38]>0 or st==final:
    park(s.u16(b+17),s.u16(b+20)-8,3,10);s.w16(0xD518,256)
  if mode[0] in ('nonattack','invincibility','hurt','blink') and st in (9,10,17,20) and len(g.rows)>700:
   flags={'nonattack':1,'invincibility':1,'hurt':65,'blink':131}[mode[0]]
   park(s.u16(b+17),s.u16(b+20)-8,flags,10);s.w16(0xD518,256);m[0xD532]=6 if mode[0]=='invincibility' else 0
  if st==16 and mode[0].startswith('fight'):park(s.u16(b+17),s.u16(b+20),1,14)
  if st==5:
   if clear_start[0] is None:clear_start[0]=len(g.rows)
   m[0xD522]=0 if mode[0]=='fight_9_floor_wait' and len(g.rows)-clear_start[0]<180 else 2
 g.pre[0x16D0]=contact
 for pc,name in ((0x974C,'intro'),(0x9799,'trigger'),(0x97FD,'pan'),(0xA9A5,'combat_init'),(0xAAFC,'hp_hit'),(0xAD17,'5a_underflow'),(0x81DF,'clear'),(0xAE0F,'5c_delay_setup'),(0xAEA3,'5c_complete'),(0x4E97,'act_load'),(0x32F9,'results')):
  def mark(mm,pc=pc,name=name):
   if not g.recording or (pc>=0x8000 and s.slot[2]!=30) or (0x4000<=pc<0x8000 and s.slot[1]!=1):return
   b=mm.cpu.ix;marks.append(dict(u=len(g.rows)+1,event=name,ix=b,type=m[b],state=m[b+1],hp=m[b+38],parameter=m[b+63],zone=m[0xD297],act=m[0xD298],player=[s.u16(0xD511),s.u16(0xD514)],camera=[s.u16(0xD174),s.u16(0xD176)],floor=m[0xD522],pan=[s.u16(0xD2DA),s.u16(0xD2DC)]))
  g.hook(pc,mark)
 def exhausted(mm):
  if not g.recording or mode[0]!='exhaustion' or m[mm.cpu.ix]!=89:return
  blocked[0]=[(b,m[b]) for b in range(0xD700,0xD9C0,64) if not m[b]]
  for b,_ in blocked[0]:m[b]=255
 def fail(mm):
  if not g.recording or mode[0]!='exhaustion':return
  marks.append(dict(u=len(g.rows)+1,event='allocation_failure',ix=mm.cpu.ix))
  for b,v in blocked[0]:m[b]=v
  blocked[0]=[]
 g.hook(0x5EE1,exhausted);g.hook(0x5EF4,fail)
 cases=[]
 for name,n in [('cycle',3000),('fight_9',6000),('fight_10',6000),('fight_17',6000),('fight_9_floor_wait',6000),('exhaustion',900),('passive_children',1500),('nonattack',1000),('invincibility',1000),('hurt',1000),('blink',1000),('cycle',3000)]:
  mode[0]=name;marks.clear();released[0]=False;clear_start[0]=None;g.begin(1800,238,rings=0x47,types=(89,90,91,92,93,52,18,15,10));rows=g.run(n,stop=lambda v,rs:v['zone']==5 and v['cur']==5)
  transitions=[];old=None
  for v in rows:
   b=next((o for o in v['o'] if o['type']==89),None);key=(b['state'],b['request']) if b else None
   if old!=key:transitions.append(dict(u=v['u'],boss=b));old=key
  case=dict(name=name,rows=rows,marks=list(marks),transitions=transitions,states=sorted({o['state'] for v in rows for o in v['o'] if o['type']==89}),children=sorted({(o['type'],o['state'],o['parameter']) for v in rows for o in v['o'] if 90<=o['type']<=93}))
  if name.startswith('fight'):
   assert [v['hp'] for v in marks if v['event']=='hp_hit']==list(range(10,-1,-1))
   assert set(case['states'])==set(range(21))-{4}
   assert rows[-1]['zone']==5 and rows[-1]['act']==0 and rows[-1]['cur']==5,(name,rows[-1])
   assert {v['parameter'] for v in marks if v['event']=='5c_delay_setup'}==set(range(7))
  if name=='fight_9_floor_wait':
   clear=next(v for v in marks if v['event']=='clear');assert clear['u']-clear_start[0]>=180
  if name in ('nonattack','invincibility','hurt'):assert not any(v['event']=='hp_hit' for v in marks)
  if name=='blink':assert any(v['event']=='hp_hit' for v in marks)
  cases.append(case)
 assert cases[0]==cases[-1],'complete-state replay differs after three fights and exhaustion'
 return dict(rom_sha256=F.digest(r),research_base=A.BASE,method=__doc__,complete_cpu_state_bytes=len(cpu),cases=cases[:-1],replay_identical=True,replay_rows=3000,rows=sum(len(c['rows']) for c in cases[:-1]),assertions=22,exhaustion_method='At allocator entry temporarily occupy all empty command4 slots with FF; at failure restore their pre-call occupancy. Boss/script/children unchanged; failure executes original carry path.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--check',action='store_true');a=p.parse_args();d=build(R.load(a.rom))
 if a.check:assert OUTPUT.read_text()==F.dumps(d)
 else:OUTPUT.write_text(F.dumps(d),encoding='utf-8')
 print(dict(rows=d['rows'],cases=[(c['name'],len(c['rows']),c['states']) for c in d['cases']]))

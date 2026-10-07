"""AQZ3 boss $59..$5D original routine vectors; canonical 256px contracts."""
import argparse,itertools,json
from pathlib import Path
import rom as R
import aqz_foundation as F
import mghz_object_census as C
import sez_object_census as SC
import mghz56_runtime as M
from oracle import Oracle
S=0xD700
OUTPUT=F.OUT/'boss-59-runtime.json'
BASE='c4ec2ee1e1bbf86b38939352691da09859f75c33'
COUNTS={}
def check(k,a,b):
 COUNTS[k]=COUNTS.get(k,0)+1
 assert a==b,(k,a,b)
class Lab:
 def __init__(self,r,slot=S):
  self.slot=slot
  self.r=r;self.o=Oracle(r);self.m=self.o.mem
  self.m[0xD540:0xDA00]=bytes(0x4C0);self.m[0xD297]=4;self.m[0xD298]=2
  self.m[0xD52C]=8;self.m[0xD52D]=24;self.o.word(0xD174,1727);self.o.word(0xD176,78)
  self.o.word(0xD282,2560);self.o.word(0xD27E,320)
  self.prepare()
 def prepare(self,t=89,st=9,frame=2,x=1856,y=160):
  o,m=self.o,self.m;m[self.slot:self.slot+64]=bytes(64);m[self.slot]=t;m[self.slot+1]=m[self.slot+2]=st;m[self.slot+4]=2;m[self.slot+38]=10;m[self.slot+30]=255
  o.word(self.slot+17,x);o.word(self.slot+20,y);self.frame(frame);o.position(x+100,y);m[0xD501]=m[0xD502]=5;m[0xD503]=0;m[0xD532]=0;m[0xD522]=0;m[0xD523]=0;m[0xD3B0]=m[0xDE04]=0
 def frame(self,f):
  m=self.m;m[self.slot+6]=f;p=C.G.parse_frame_record(self.r,C.frame_pointers(self.r,m[self.slot])[1][f])['frame_rom'];m[self.slot+44:self.slot+46]=self.r[p+1:p+3]
 def call(self,pc,bc=0,de=0):
  self.o.bank(2,30);self.m[0xD12B]=30;self.o.cpu.ix=self.slot;self.o.call(pc,bc=bc,de=de)
 def snap(self):
  m,o=self.m,self.o
  return dict(type=m[self.slot],state=m[self.slot+1],request=m[self.slot+2],frame=m[self.slot+6],duration=m[self.slot+7],x=o.word(self.slot+17),y=o.word(self.slot+20),fractions=[m[self.slot+16],m[self.slot+19]],vx=R.s16(o.word(self.slot+22)),vy=R.s16(o.word(self.slot+24)),angle=m[self.slot+10],saved_request=m[self.slot+11],counter30=m[self.slot+30],cooldown31=m[self.slot+31],contact=m[self.slot+33],field23=m[self.slot+35],field24=m[self.slot+36],hp=m[self.slot+38],field34=m[self.slot+52],field35=m[self.slot+53],field38=m[self.slot+56],token=m[self.slot+62],parameter=m[self.slot+63],flags3=m[self.slot+3],flags4=m[self.slot+4],player=M.player(o),fixed_parent=list(m[0xD71E:0xD735]))
def contact_vectors(r):
 q=Lab(r);m,o=q.m,q.o;geo=[];posture=[]
 # AAB5 is common tail after movement/gravity. This isolates HP vs projection/rebound.
 for frame in (1,2,3,4,7):
  q.prepare(frame=frame);ox,oy=m[S+44:S+46];geo.append(dict(frame=frame,extent=[ox,oy],normal=[-ox-8,ox+8,-oy,24],state0f=[-ox-9,ox+9,-oy,24]))
  for ex,dx,dy in itertools.product((8,9),range(-ox-11,ox+12),range(-oy-2,27)):
   q.prepare(frame=frame);m[0xD52C]=ex;m[0xD503]=2;o.position(1856+dx,160+dy);o.word(0xD518,256);q.call(0xAAB5)
   bit=M.overlap_model(dx,dy,ex=ex,ox=ox,oy=oy)
   check('boss_geometry',m[S+33]&15,bit);check('boss_hp_geometry',m[S+38],9 if bit else 10)
 for attack,hurt,blink,power,cd,hp,pt in itertools.product((0,2),(0,64),(0,128),(0,6),(0,1,2,16),(0,1,10),((0,-64),(0,24),(-28,0),(28,0),(0,-65))):
  q.prepare();m[0xD503]=attack|hurt|blink;m[0xD532]=power;m[S+31]=cd;m[S+38]=hp;o.position(1856+pt[0],160+pt[1]);o.word(0xD516,384);o.word(0xD518,256);q.call(0xAAB5)
  bit=0 if hurt else M.overlap_model(*pt,ox=20,oy=64);hit=bool(bit and attack and max(0,cd-1)==0)
  check('posture_hp',m[S+38],(hp-1)&255 if hit else hp);check('posture_borrow',m[S+10],255 if hit and hp==0 else 0)
  check('posture_feedback',m[0xDE04],182 if hit else 0);check('rebound_separate',m[0xD502],27 if bit and attack else 5)
  posture.append(dict(attack=attack,hurt=hurt,blink=blink,power=power,cooldown=cd,hp=hp,point=pt,result=q.snap()))
 return dict(geometry=geo,posture=posture)
def boundaries(r):
 q=Lab(r);o,m=q.o,q.m;out={};rows=[]
 for dx,dy in itertools.product((-97,-96,-95,0,95,96,97),(-305,-304,-303,0,303,304,305)):
  q.prepare(st=1,y=238);o.position(1856+dx,238+dy);q.call(0x9771);check('trigger',m[S+2],2 if abs(dx)<96 and abs(dy)<304 else 1);rows.append([dx,dy,m[S+2]])
 out['trigger']=rows;rows=[]
 for y in (-32768,-1,0,237,238,239,240,32767):
  q.prepare(y=y);q.call(0xABF2);check('world_y',q.o.cpu.a,255 if 238<y<32768 else 0);rows.append([y,q.o.cpu.a])
 out['world_y']=rows;rows=[]
 for direction,sx in itertools.product((-160,160),range(256)):
  q.prepare();o.word(S+22,direction);o.word(S+24,-1536);m[S+26]=sx;q.call(0xAA6C)
  expected=0 if (direction<0 and sx<48) or (direction>0 and sx>=208) else direction
  check('cached_screen_stop',R.s16(o.word(S+22)),expected)
  if sx in (0,47,48,207,208,255):rows.append(dict(vx=direction,cached_x=sx,result=q.snap()))
 out['cached_screen']=rows;rows=[]
 for hp in range(12):
  q.prepare();m[S+38]=hp;m[0xD503]=2;o.position(1856,96);q.call(0xAAB5);check('hp_underflow',m[S+38],(hp-1)&255);check('hp_defeat',m[S+10],255 if hp==0 else 0);rows.append(q.snap())
 out['hp']=rows
 # Fixed-parent child contact path: attack is irrelevant; one initial health unit needs two contacts.
 q=Lab(r,0xD740);o,m=q.o,q.m;T=q.slot;rows=[]
 for attack,hurt,blink,power,hp,bits in itertools.product((0,2),(0,64),(0,128),(0,6),(0,1),(1,2,4,8)):
  q.prepare(90,3,28);m[T+38]=hp;m[T+33]=bits;m[0xD503]=attack|hurt|blink;m[0xD532]=power;m[T+11]=1;m[0xD734]=6;q.call(0xACE3)
  check('5a_hp',(m[T+38],m[0xD734]),((hp-1)&255,5 if hp==0 else 6));check('5a_return',m[T+2],4 if hp==0 else 1)
  check('5a_vertical_response',R.s16(o.word(T+24)),512 if bits&1 else -512);rows.append(q.snap())
 out['5a_contact_return']=rows;rows=[]
 for param in range(7):
  q.prepare(92,2,0);m[T+63]=param;m[0xD723]=255;q.call(0xADBE)
  off=30*0x4000+0xAEB1-0x8000+param*4;dx=R.s16(R.u16(r,off));dy=R.s16(R.u16(r,off+2));ang,turn=r[30*0x4000+0xAEC9-0x8000+param*2:30*0x4000+0xAEC9-0x8000+param*2+2]
  check('5c_reset',[o.word(T+17),o.word(T+20),m[T+10],m[T+56],m[T+48],m[T+2]],[(1727+dx)&65535,(78+dy)&65535,ang,turn,16+32*param,5]);rows.append(dict(parameter=param,camera_offsets=[dx,dy],initial_angle=ang,angle_step=R.s8(turn) if hasattr(R,'s8') else turn-256 if turn>127 else turn,wait=16+32*param,result=q.snap()))
 out['5c_parameters']=rows;out['5c_selector']=F.child5c_frames(r)
 return out
def allocation(r):
 q=Lab(r);m,o=q.m,q.o;rows=[]
 for free in range(12):
  m[0xD700:0xD9C0]=bytes([255])*0x2C0
  if free<11:m[0xD700+64*free]=0
  o.cpu.ix=0xD540;q.call(0x5EE1)
  check('allocator',bool(o.cpu.f&1),free==11);check('allocator_slot',o.cpu.iy,0xD700+64*min(free,11));rows.append(dict(free_index=free if free<11 else None,carry=bool(o.cpu.f&1),iy=o.cpu.iy))
 return rows
def camera_clear(r):
 import viewport_semantics as V
 q=Lab(r);o,m=q.o,q.m;scanner={}
 for fill in (0,1):
  xs=[]
  for sx in range(-129,386):
   m[0xD400:0xD450]=bytes(80);m[0xD540:0xDA00]=bytes(0x4C0);m[0xD440]=fill;o.word(0xD174,1856-sx);o.word(0xD176,138);o.bank(2,28);o.call(0x8000)
   yes=bool(m[0xD400]);check('mapped_create',yes,V.scan_creates(sx,32,fill==0))
   if yes:xs.append(sx)
  scanner[str(fill)]=xs
 gates=[]
 for floor,x in itertools.product((0,1,2,3),(1600,1727,2000,2500)):
  q=Lab(r);o,m=q.o,q.m;q.prepare(st=5);m[S+37]=10;m[S+39]=0;m[0xD522]=floor;o.position(x,238);q.call(0x81BD)
  check('clear_floor',m[0xD502],32 if floor&2 else 5);check('clear_conversion',m[S],15 if floor&2 else 89)
  if floor&2:check('clear_restored_limit',o.word(0xD282),2560)
  gates.append(dict(floor=floor,x=x,result=q.snap(),limits=[o.word(0xD280),o.word(0xD282)],pan=[o.word(0xD2DA),o.word(0xD2DC)]))
 hud=[]
 for free in range(17):
  q=Lab(r);o,m=q.o,q.m;m[0xD540:0xD940]=bytes([255])*0x400
  if free<16:m[0xD540+free*64]=0
  q.call(0x81A6);check('hud_allocator_pointer',o.word(S+52),0xD540+64*min(free,16))
  hud.append(dict(free_index=free if free<16 else None,stored_pointer=o.word(S+52)))
 # Shared start loader, next-zone target established independently from fight.
 q=Lab(r);q.m[0xD297]=5;q.m[0xD298]=0;q.o.call(0x4E57)
 start=[q.o.word(a) for a in (0xD511,0xD514,0xD2D6,0xD2D8)];check('next_start',start,[238,864,126,752])
 return dict(scanner=scanner,clear_gate=gates,hud_allocator=hud,next_start=start)

def support(r):
 rows=[]
 for param,parity in itertools.product((2,8),(0,1)):
  q=Lab(r,0xD740);o,m=q.o,q.m;q.prepare(52,0,0);m[q.slot+63]=param;frames=[]
  for u in range(1,600):
   m[0xD12F]=parity;q.call(0x64FA);q.call(o.word(q.slot+12));frames.append(m[q.slot+6])
   if m[q.slot]==255:break
  check('puff_duration',u,(param+1)*(26 if parity else 50))
  rows.append(dict(parameter=param,clock_bit0=parity,updates=u,frames=sorted(set(frames)),art=list(m[q.slot+8:q.slot+10])))
 return dict(puffs=rows,shared_sources={n:F.source(r,*p) for n,p in dict(command4=(0,0x671F,0x67A1),puff=(30,0x8C73,0x8D17),clear=(30,0x81BD,0x81F4),flash=(29,0x83C6,0x83FE),hud_allocator=(0,0x5E9C,0x5EF8),angular_velocity=(0,0x6089,0x60F9)).items()})

def script_spawns(r):
 rows=[]
 for st,n in ((5,6),(6,400),(10,16),(11,6),(13,3),(14,20)):
  q=Lab(r);o,m=q.o,q.m;q.prepare(st=0,frame=0);m[S+2]=st;m[S+30]=6
  seen=set();events=[]
  for u in range(n):
   q.call(0x64FA)
   for b in range(0xD740,0xD9C0,64):
    if m[b] and b not in seen:seen.add(b);events.append(dict(u=u+1,slot=b,type=m[b],parameter=m[b+63],x=o.word(b+17),y=o.word(b+20),art=list(m[b+8:b+10]),flags=m[b+4]))
  expected={5:5,6:6,10:1,11:5,13:1,14:7}[st];check('script_spawn_count',len(events),expected)
  if st==14:check('seven_parameter_order',[v['parameter'] for v in events],list(range(7)));check('same_update_burst',len({v['u'] for v in events}),1)
  rows.append(dict(state=st,events=events,result=q.snap()))
 exhaustion=[]
 for free in range(11):
  q=Lab(r);o,m=q.o,q.m;q.prepare(st=0,frame=0);m[S+2]=14
  for b in range(0xD740,0xD9C0,64):m[b]=255
  for j in range(free):m[0xD740+j*64]=0
  for u in range(20):q.call(0x64FA)
  actual=[m[b+63] for b in range(0xD740,0xD9C0,64) if m[b]==92];check('script_partial_allocation',actual,list(range(min(free,7))))
  exhaustion.append(dict(free_slots=free,parameters=actual,script_state=q.snap()))
 return dict(success=rows,partial_failure=exhaustion)

def child_vectors(r):
 q=Lab(r,0xD740);o,m=q.o,q.m;T=q.slot;rows=[]
 # Every child uses actual separate D740; fixed parent D700 stays separate.
 for t,cb,frame in ((90,0xAC71,28),(91,0xAD4D,11),(92,0xADAE,14),(92,0xAE3B,16),(93,0xAF1E,24)):
  for sleep,attack,hurt,blink,power,pt in itertools.product((0,64),(0,2),(0,64),(0,128),(0,6),((0,0),(0,-32),(0,24),(-12,0),(12,0),(0,-33))):
   q.prepare(t,1,frame);m[T+4]=2|sleep;m[T+11]=128;m[T+31]=4;m[0xD503]=attack|hurt|blink;m[0xD532]=power;o.position(1856+pt[0],160+pt[1]);o.word(T+22,-128);o.word(T+24,-512)
   q.call(cb);rows.append(dict(type=t,callback=cb,sleep=sleep,attack=attack,hurt=hurt,blink=blink,power=power,point=pt,result=q.snap()))
   if t==91:check('5b_no_contact',m[0xD3B0],0);check('5b_delete',m[T],255 if sleep else 91)
   if t==92 and cb==0xADAE:check('5c_sleep_state',m[T+2],2 if sleep else 1)
   if t==93:check('5d_sleep_delete',m[T],255 if sleep else 93)
 # Exact original lookup result (signed byte *128, arithmetic shift4).
 angular=[]
 for angle in range(256):
  q.prepare(92,3,16);m[T+10]=angle;m[T+11]=128;q.call(0x036E)
  def sine(a):v=r[0x200+(a&255)];return v-256 if v&128 else v
  check('angular_vx',R.s16(o.word(T+22)),sine(angle)*8);check('angular_vy',R.s16(o.word(T+24)),sine(angle+192)*8)
  angular.append([angle,R.s16(o.word(T+22)),R.s16(o.word(T+24))])
 # Child callbacks have no water/raster dependency. Compare complete RAM output
 # while excluding only the deliberately changed input bytes.
 water=[]
 for t,cb,frame in ((89,0xAA6C,2),(89,0xAB1D,7),(90,0xAC71,28),(91,0xAD4D,11),(92,0xADAE,14),(92,0xAE3B,16),(93,0xAF1E,24)):
  reference=None
  for flag,line,raster in itertools.product((0,255),(0,568,788,65535),(0,96,192,255)):
   q.prepare(t,9 if t==89 else 1,frame);m[T+11]=128;m[T+31]=4;o.word(T+22,-128);o.word(T+24,-512);m[0xD443]=flag;o.word(0xD450,line);m[0xD131]=raster;m[0xD132]=raster;q.call(cb)
   v=q.snap()
   if reference is None:reference=v
   else:check('water_independent',v,reference)
  water.append(dict(type=t,callback=cb,cases=32))
 return dict(contact_sleep_vectors=rows,angular_velocity=angular,water=water)

def contracts():
 return dict(
  callbacks={
   '974C':'keepalive4.1, bossactiveD44E=zone+1=5, D4A5=0, allocateHUD12/storepointer34/35, savecameraRight25/27, req1; requestedSpringShoes12->fall0E',
   '9771':'refreshsavedrightlimit, strictabsX<96 andabsY<304 ->camera mode59F3,req2; noawake gate needed separately',
   '97C1':'waitstoredHUDpointerbyte==0; installcamera target boss+(-128,-160),upperYtarget78, req3. No waitforpanarrival',
   'A9A5':'dynamicselector23,palette16queuebit5,allocateHUDagain;req6;integerY-=224;hp26=10;counter30=field34=6;23/24=0',
   'A9E0':'RET; only state4, no naturalincomingrequest',
   'A9E1':'state6 script call onceeach64-recordrestart: decrementcounter30; zero ->req7,counter30=64; creates6 type5A at relative(0,+224)',
   'A9F3':'state7 waitsfield34==0 (six5Aunderflows). Then decrements30; borrowafter65eligiblecalls ->req8,zeroallvelocities',
   'AA13':'state8 solidcontact814D, integrate,vy+=16,ifpositiveintegerY>238 ->vy=-1536,vx=-160,req9,angle10/counter30/cooldown31=0',
   'AA4D':'script17-tail faceplayer: bossX<playerX givesvx+160 else-160;vy=-1536',
   'AA68':'state10 sets30=FF thenfallsintoAA6C eachcallback',
   'AA6C':'cachedX stop left<48/right>=208 beforeintegrate; integrate,vy+=48; ifnonnegativevyandpositiveY>238 ->req17,zeroallvelocities,RETURN; elseAAB5',
   'AAB5':'angle10!=0 ->req11,zeroVX,RETURN. Else cooldown31decrement;solid5FA0; oncontact8105attackrebound. Ifcooldown0andattack:command7,B6,req20,cooldown16,hpSUB1;borrowsetsangleFFandRETURN. Tailcounter30==0andabsplayerY-bossY<32 ->req10 canoverwrite20',
   'AB1D':'state11 vy+=32 BEFOREintegrate,solid814D;Y<=238 andcounter30==16 ->counter0;Y>238 ->req12,cooldown31=48,vx0,vy-256,counter30=96',
   'AB60':'state12 contact814D; compute31-1, store/RETunlesszero. At31==1 leaveit1 andintegrate everycall; counter30--,borrowafter97moves ->clearobject03.7,req13,zeroVY,counter30=0',
   'AB8D':'state13 contact814D; waitfixedD724!=0 from5Basleepdeath;req14,clear23/24,counter30=16',
   'ABA5':'state14 contact814D then30--;borrowafter17callbacks ->30=6,req18. Scriptsfirstwait16records thenall7spawnsoneenginepass',
   'ABEB':'states18/19 integrate thencontact814D. Script18 vx0 vy-384 for32calls then23=FF req15. Script19 vx0 vy384 for32 thenreq16',
   'ABBA':'state15 contact814D; waits30==0 fromsix5Ccompletions thenreq19,30=64',
   'ABCB':'state16 if30==0 req14,30=16 RETURN;otherwise30--,contact814D;anynibble->req5. Timeoutrepeatschildren; noHP/attackprerequisite',
   '81BD':'state5 afterpuff/blinkscript:camera617Eeachcall;floorbit1 gates59D8release,restoreRight25/27,state20via03F5,allocate0A0,convert0Ftoken0param0no score'},
  boss=dict(initial_counter=10,damaging_contacts=11,defeat='SUB1 borrow sets angle10=FF; reaching zero survives. State20 requested on every damaging contact; subsequent tail can overwrite with10 when counter30==0 and PLAYER_DIST(Y)<32.',contact='AAB5 decrements cooldown31 before solid5FA0; 8105 rebound requires attack independently of cooldown; HP additionally requires cooldown==0 and attack. No D532 substitute. Hurt suppresses6328; blink does not suppress overlap/HP. Ordinary nonattack combat contact projects only; entry/defeat callbacks814D queue hurt for nonattack.',cooldown=16,rebound=dict(top_vy=-1024,bottom_vy=1536,left_vx=-1536,right_vx=1536,side_vy='negate incoming',requested=27,preserve_floor=True),feedback='command7 and B6 only on damaging combat contact; shared palette flash uses palette16.',reachable=list(range(4))+list(range(5,21)),external_only=[4]),
  child5a=dict(init='AC38 keepalive4.1, clear03.7, req1, WORLD(2048,238), vx-128 vy-512, hp1,counter30=2,cooldown31=0',movement='AC71 clearcontact; cooldown31>0 decrements/skips overlap; otherwise6328 any contact savesreq->3 and returns beforegravity/move. Gravity+20/256 beforemove; nonnegativevy and signedpositiveY>238 resetsvy-512. Three landings underflowcounter2 then faceplayer at vx+/-128 req1/2.',contact='No attack/selector prerequisite. State3 ACE3: cooldown4, integrate once, restore savedreq, vy+512 if top bit else-512, command7/B6, hpSUB1. Second contact underflows1->0->FF, decrements fixedD734, req4.',cleanup='state4 AD24 parameter0 converts0F no score; no parent type/liveness check; multiple independent children coexist; six scheduled across state6.'),
  child5b=dict(init='keepalive req1 vy-256',active='AD4D if asleep setsFF and fixedD724=FF, otherwiseintegrate; no contact. Parent waitsD724 in state13.',role='presentation/support signal, no gameplay overlap'),
  child5c=dict(init='req1 keepalive, counter30=0,angle0,magnitude11=128;036E velocitylookup.',states='1 move then forcedhurt630B then ifsleepreq2. 2 waits fixedD723!=0 then camera-relative relocation/angle tables, req5,delay48=16+32*p. 5 delays N decrements then nextcallreq3,cooldown31=4. 3 selectorAE5B duration3 before AE3B move, decrement31; every4callsAE88 turn/recomputevelocity; forcedhurt; WORLD Y>238 req4. 4 parameter0,decrementfixedD71E,convert0F.',motion='signed ROM sinebyte($0200+angle)*magnitude arithmetic>>4 for vx; angle+192 forvy; no gravity. AE88 negative step updates onlyangle>=80; positiveonlyangle<176. Frames negative angle>=88->20/21 else22/23;positive angle<168->16/17 else18/19; counter30parity advances eachselector.',parameter6='Reads adjoiningdata beyond six-entry tables: offset(-400,-400), angle217,step-82,wait208. No corrective clamp; moves offscreen and may remain keepalive without countercompletion. Intended0..5 completions decrement6->0; do not require seven completions.',parent='FixedD723,D71E; not ownership pointer. No parent sweep or type check; initialprojectiles and later curved hazards forcehurt; none attack-defeatable.'),
  child5d=dict(init='req1,counter31=0,vx-576,vy0. PLAYER_DIST(absY)<32 leavesdirection0; otherwise playerabove->FF/below->1.',active='AF1E asleep deletesFF; awake integrate, forcedhurt630B, then vy += -8/256 ifdirectionFF or +8/256 if1; no furtherplayerretarget; frames24/25every2calls; no parentlookup.'),
  allocator=dict(command4='5EE1 first zero slotD700..D980 (11), carryfailure no spawn and script continues; inherits positioned spawn/art as original command4',hud_bonus='5E9C firstzeroD540..D900 (16); no successflag. 81A6 stores IY evenfailure (past endD940). No guaranteedHUD/spawn.',scheduler='ascending64bytes; childallocatedafterparent samepass gets engine/init, precedingfreedslot waitsnextpass; keepalive exempts genericdeletion butsleepbitcontinuescomputed.'),
  arena=dict(trigger='strict PLAYER_DIST(absX)<96,absY<304; sharedframework intro beforetrigger setsD44E=5',target=[1728,78],settled=[1727,78],pan_rate=[1,1],camera='state2 waits HUD disappearance then installs offset(-128,-160), upperY78,req3; combatinit whilepaninprogress, no arrivalgate',horizontal_stop='prior-render cached +1A: vx<0 stopsat<48; vx>=0 stopsat>=208. Preserve cachedbyte, not world-minuscurrentcamera.'),
  clear=dict(path='underflow -> angleFF ->11 ->12 ->13 waits5B ->14 ->18 ->15 waitschildcounter0 ->19 ->16; state16 overlap within64calls ->5; otherwise14 repeat. 5 puffs8/blinks then81BD; floorbit1 only; releasepan,restore savedrightlimit,requestplayer20,allocate0A0,convert0F token0/param0.',timer='continues; no ordinary18 sign',boss_active='D44E remains5 through parent conversion/bonus/results; shared next-act initialization clears it to0',progression=dict(zone=5,act=0,player=[238,864],camera=[126,752])),
  viewport=[dict(kind='WORLD',value=238,use='boss/5A/5C positive integerY threshold, strict>'),dict(kind='PLAYER_DIST',value=[96,304],use='boss trigger strict'),dict(kind='PLAYER_DIST',value=32,use='Y distance boss tail/5D init'),dict(kind='LOCKED_CAMERA',value=[1727,78],use='settled arena'),dict(kind='CENTER',value=-128,use='camera target X relative boss'),dict(kind='EDGE',value=[48,208],use='cachedscreenX stop canonical256'),dict(kind='EDGE',value=[-16,80,64,192,272],use='5C canonicalscreenoffsets')],
  water='No directD443/D450/D131/D132 dependency; sharedplayer hurt/physics can respond indirectly. AQZ3 boot containsno0D controllers; A2 transitionreset applies.',art='A1 approved0..29mappingframes reused. No wholebitmapflip, syntheticart ornewboard.')

def build(r):
 COUNTS.clear();check('rom',F.digest(r),R.ROM_SHA256 if hasattr(R,'ROM_SHA256') else 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607')
 graphs={f'0x{t:02X}':C.public_script(C.state_scripts(r,t)) for t in range(89,94)}
 q=Lab(r);q.prepare(st=3,y=238);q.call(0xA9A5);init=q.snap();check('init',[init['y'],init['hp'],init['request'],q.m[0xD3B3],q.m[0xD495]],[14,10,6,23,16])
 result=dict(rom_sha256=F.digest(r),research_base=BASE,placement=next(x for x in json.loads((F.OUT/'object-census.json').read_text())['acts']['aqz3']['records'] if x['type_id']=='0x59'),state_graphs=graphs,initialization=init,contacts=contact_vectors(r),boundaries=boundaries(r),allocator=allocation(r),children=child_vectors(r),support=support(r),script_spawns=script_spawns(r),camera_clear=camera_clear(r),contracts=contracts(),code_scans={str(t):SC.type_scan(r,t)[1] for t in range(89,94)},tool_hashes={n:F.digest((F.ROOT/'tools'/n).read_bytes().replace(b'\r\n',b'\n')) for n in ('aqz59_runtime.py','aqz59_game.py')},source_hashes={str(t):F.source(r,30,*p) for t,p in enumerate(((0xA7BA,0xAC08),(0xAC08,0xAD2B),(0xAD2B,0xAD60),(0xAD60,0xAED5),(0xAED5,0xAF4C)),89)},coverage=dict(COUNTS))
 result['assertions']=sum(COUNTS.values());return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--check',action='store_true');a=p.parse_args();d=build(R.load(a.rom))
 if a.check:assert OUTPUT.read_text()==F.dumps(d)
 else:OUTPUT.write_text(F.dumps(d),encoding='utf-8')
 print(d['coverage'])

"""AQZ A3 original-ROM platform contracts and executable oracle vectors."""
import argparse
import itertools
from pathlib import Path
import aqz_foundation as F
import level_package as L
import mghz_object_census as C
import platform_spike_collision as P
import rom as R
from oracle import Oracle
S=P.SLOT
OUTPUT=F.OUT/'platform-3f-runtime.json'
BASE='172724dc34fe8750a4c36d82c4f5cd0e83a89e0d'
COUNTS={}
def check(name,a,b):
    COUNTS[name]=COUNTS.get(name,0)+1
    assert a==b,(name,a,b)

def placements(r):
    out=[]
    for act in (0,1):
        ptr=L.object_list_pointer(r,4,act);rows,_=L.decode_object_list(r,ptr['list_rom'])
        out += [dict(act=act,**x) for x in rows if x['type_id']=='0x3F']
    return out

def lab(r,rec,type_id=63):
    raw=bytearray.fromhex(rec['raw_bytes']);raw[0]=type_id
    q=P.ObjectLab(r,type_id,bytes(raw),30,2 if int(rec['parameter'],16)==134 else 0)
    q.m[S]=type_id;q.m[0xD297]=4;q.m[0xD298]=rec['act'];q.snap=bytes(q.m[0xC000:0xE000])
    return q

def fields(q):
    return dict(type=q.m[S],state=q.m[S+1],requested=q.m[S+2],x=q.obj16(17),y=q.obj16(20),
        fractions=[q.m[S+16],q.m[S+19]],vx=R.s16(q.obj16(22)),vy=R.s16(q.obj16(24)),
        counter=q.m[S+7],frame=q.m[S+6],flags3=q.m[S+3],flags4=q.m[S+4],
        timer=q.m[S+30],fall=q.m[S+39],sag=q.m[S+53],sag_return=q.m[S+51],tick=q.m[S+48],latch=q.m[S+49],reload=q.m[S+52],period=q.m[S+55],
        owner=q.m[0xD3C0],px=q.o.word(0xD511),py=q.o.word(0xD514),pvx=R.s16(q.o.word(0xD516)),pvy=R.s16(q.o.word(0xD518)),
        carry_x=R.s16(q.obj16(35)),carry_y=R.s16(q.obj16(56)),token=q.m[S+62])

def creator(r,recs):
    out=[]
    for rec in recs:
        o=Oracle(r);m=o.mem;o.bank(2,28);m[0xDA00:0xDA09]=bytes.fromhex(rec['raw_bytes']);o.cpu.ix=S;o.cpu.iy=S;o.cpu.hl=0xDA00
        o.call(0x80EB,bc=0xD400+rec['index']-1);created=list(m[S:S+64]);m[0xD297]=4;m[0xD298]=rec['act'];o.position(rec['world_x'],rec['world_y']-80)
        o.word(0xD174,rec['world_x']-100);o.word(0xD176,rec['world_y']-100)
        states=[]
        for i in range(2):
            o.bank(2,30);o.cpu.ix=S;o.call(0x64FA);cb=o.word(S+12);o.bank(2,30);o.cpu.ix=S;o.call(cb);states.append(list(m[S:S+64]))
        check('creator',(o.word(S+58),o.word(S+60)),(rec['world_x'],rec['world_y']))
        check('creator',created[62],rec['index'])
        check('creator',m[S+2],{131:4,134:7,139:13}[int(rec['parameter'],16)])
        out.append(dict(placement=rec,creator_fields=created,initializer_fields=states[0],entered_fields=states[1]))
    return out

def equivalence(r,recs):
    out=[]
    for rec in recs[:2]:
        a,b=lab(r,rec),lab(r,rec,40)
        for u in range(1,1650):
            for q in (a,b):
                q.player(q.obj16(17),q.obj16(20)-8 if u<20 else q.obj16(20)-60,vy=1792)
                q.frame()
            aa,bb=bytearray(a.m[0xC000:0xE000]),bytearray(b.m[0xC000:0xE000])
            for addr in (0xD418,0xDA00,S,S+42,S+43):aa[addr-0xC000]=bb[addr-0xC000]=0
            check('type_alias_full_ram',aa,bb)
        out.append(dict(parameter=rec['parameter'],updates=1649,normalized_only='type bytes in slot, placement scratch and source record; mapping pointer +2A/+2B differs by type',ram_sha256=F.digest(aa)))
    return out

def gate(r,rec):
    q=lab(r,rec);rows=[]
    for zone,act,param,dy,vy,sleep in itertools.product(range(6),range(3),(5,11,139),(-17,-16,-1,0,24),(-1,0,1),(0,64)):
        q.reset();q.m[0xD297]=zone;q.m[0xD298]=act;q.m[S+63]=param;q.m[S+54]=(param&63)+1;q.m[S+4]=sleep
        q.player(q.ox,q.oy+dy,vy=vy);q.callback()
        eligible=not sleep and vy>=0 and -16<=dy<=-1
        expected=14 if eligible and zone==4 and act==1 else (param&63)+1 if eligible else 13
        check('state13_gate',q.m[S+2],expected)
        rows.append(dict(zone=zone,act=act,param=param,dy=dy,vy=vy,sleep=sleep,requested=q.m[S+2]))
    return rows

def support(r,recs):
    rows=[]
    for rec in recs:
        q=lab(r,rec)
        for dx,dy,vy,water in itertools.product(range(-26,27),range(-18,26),(-256,0,256),(0,255)):
            q.reset();q.m[0xD443]=water;q.o.word(0xD450,788);q.m[S+37]=0 # disable sag in geometry-only control
            q.player(q.ox+dx,q.oy+dy,vx=123,vy=vy)
            q.o.cpu.ix=S;q.o.bank(2,30);q.o.call(0x8814)
            expected=P.model_contact(dx,dy)==1
            check('shared_geometry',q.m[0xD3C0],9 if expected else 0)
            if expected:
                check('carry_y',q.o.word(0xD514),q.oy-14);check('carry_velocity',(q.o.word(0xD516),R.s16(q.o.word(0xD518))),(123,vy))
        # Velocity gate is in callbacks, not the support helper itself.
        for pv,ov in itertools.product((-512,-256,-1,0,1,256,512),repeat=2):
            q.reset();q.o.word(S+24,ov);q.player(q.ox,q.oy-14,vy=pv);q.o.cpu.ix=S;q.o.bank(2,30);q.o.call(0x8866)
            check('relative_vy',q.o.cpu.a,255 if ov>pv else 0)
            rows.append(dict(parameter=rec['parameter'],player_vy=pv,platform_vy=ov,gate=q.o.cpu.a))
    return rows

def route(r,rec):
    out={}
    for name,sleep in [('awake',0),('asleep',64)]:
        q=lab(r,rec);q.player(q.ox,q.oy-14,vy=0);q.callback();check('state14_trigger',q.m[S+2],14)
        q.m[S+37]=0;q.m[S+4]=sleep;rows=[]
        for u in range(1,690):
            q.player(q.obj16(17),q.obj16(20)-60,vy=1792);q.frame()
            if u<=576:
                dx=min(u,160)+max(0,min(u-224,96));dy=max(0,min(u-160,64))-max(0,min(u-320,256))
                check('route_positions',(q.obj16(17),q.obj16(20)),(q.ox+dx*(2 if sleep else 1),q.oy+dy*(2 if sleep else 1)))
            rows.append(dict(update=u,**fields(q)))
            if q.m[S]>=240:break
        out[name]=rows
    q=lab(r,rec);q.m[S+39]=128;q.m[S+4]=64;q.m[S+1]=q.m[S+2]=14;q.o.word(S+12,0x8719)
    token=q.m[S+62];q.m[0xD400+token-1]=1;q.callback();check('spent_delete',q.m[S],254);check('spent_token',q.m[S+62],0)
    q.o.cpu.ix=S;q.o.call(0x5EF8);check('spent_occupancy',q.m[0xD400+token-1],1)
    out['spent']=dict(token=token,occupancy=q.m[0xD400+token-1],cleared_slot=list(q.m[S:S+64]))
    return out

def variants(r,recs):
    out=[]
    for rec in recs[:2]:
        q=lab(r,rec);rows=[]
        for u in range(1,1651 if int(rec['parameter'],16)==134 else 110):
            q.player(q.obj16(17),q.obj16(20)-14 if u==1 else q.obj16(20)-60,vy=1792);q.frame()
            rows.append(dict(update=u,**fields(q)))
        if rec['parameter']=='0x86':
            check('86_leg',(rows[799]['x'],rows[799]['vx'],rows[799]['latch']),(q.ox+800,-256,2))
            check('86_return',(rows[1599]['x'],rows[1599]['vx'],rows[1599]['latch']),(q.ox,256,0))
        else:
            check('83_delay',(rows[80]['timer'],rows[80]['fall'],rows[80]['vy']),(0,128,0))
            check('83_fall',(rows[81]['fall'],rows[81]['vy'],rows[82]['vy']),(255,0,48))
        out.append(dict(parameter=rec['parameter'],rows=rows))
    return out

def boundaries(r,recs):
    out=[]
    q=lab(r,recs[0])
    for axis,limit in [('x',640),('y',672)]:
        for d in (-limit-1,-limit,-limit+1,0,limit-1,limit,limit+1):
            q.reset();q.player(q.ox+(d if axis=='x' else 0),q.oy+(d if axis=='y' else 0));q.o.cpu.ix=S;q.o.bank(2,30);q.o.call(0x8908)
            check('retention',q.m[S],254 if abs(d)>=limit else 63);out.append(dict(axis=axis,distance=d,type=q.m[S]))
    for rec in recs:
        q=lab(r,rec);q.player(q.ox,q.oy-60);q.o.word(0xD174,q.ox+1000);q.o.word(0xD176,q.oy)
        q.m[S+4]&=~2;q.o.cpu.ix=S;q.o.call(0x61E1)
        check('generic_delete',q.m[S],254)
        token=q.m[S+62];q.m[0xD400+token-1]=1
        q.o.call(0x5EF8);check('release_occupancy',q.m[0xD400+token-1],0)
        out.append(dict(parameter=rec['parameter'],cleanup_slot=list(q.m[S:S+64]),token=token,occupancy=q.m[0xD400+token-1]))
        # Water inputs alone are irrelevant to the same original callback.
        pairs=[]
        for water,line in [(0,0),(255,788)]:
            q.reset();q.m[0xD443]=water;q.o.word(0xD450,line);q.player(q.ox,q.oy-14,vy=1792);q.callback();pairs.append(fields(q))
        check('water_callback_identical',pairs[0],pairs[1])
        out.append(dict(parameter=rec['parameter'],water_pair=pairs))
        if rec['parameter'] in ('0x83','0x8B'):
            q.reset();q.m[S+37]=0;q.m[S+39]=255;q.o.word(S+12,0x8719);q.o.word(S+24,512)
            q.player(q.ox,q.oy-14,vy=0);q.callback()
            check('fall_sign_only_gate',(q.m[0xD3C0],q.o.word(S+24),q.o.word(0xD518)),(9,560,0))
            out.append(dict(parameter=rec['parameter'],fall_sign_only_gate=fields(q)))
    return out

def callback_support(r,rec):
    q=lab(r,rec);rows=[]
    for cb,dx,dy,pv,ov,owner in itertools.product((0x8628,0x86A1),(-25,-24,-23,0,23,24,25),(-17,-16,-14,-1,0,24,25),(-256,0,256),(-256,0,256),(0,8,9)):
        q.reset();q.m[S+37]=0;q.m[S+4]=0;q.o.word(S+12,cb);q.o.word(S+22,0);q.o.word(S+24,ov if cb==0x86A1 else 0)
        q.player(q.ox+dx,q.oy+dy,vy=pv);q.m[0xD3C0]=owner;q.callback()
        moved_y=ov//256 if cb==0x86A1 else 0
        eligible=(pv>=0 if cb==0x8628 else ov<=pv) and owner in (0,9) and P.model_contact(dx,dy-moved_y)==1
        check('callback_support',q.m[0xD3C0],9 if eligible else 8 if owner==8 else 0)
        rows.append(dict(callback=cb,dx=dx,dy=dy,player_vy=pv,platform_vy=ov,owner_in=owner,owner_out=q.m[0xD3C0],player_y=q.o.word(0xD514)))
    return rows

def contracts():
    return dict(
        placements={'aqz1#1':dict(parameter=134,initial=7,aux1=50,leg_updates=800,excursion_pixels=800,world=[2128,480]),
                    'aqz1#2':dict(parameter=131,initial=4,delay=80,world=[3408,272]),
                    'aqz2#2':dict(parameter=139,initial=13,contact_request=14,world=[2096,669])},
        alias='type28/type3F share bank1E state table8439, initializer8585 and all callbacks; dispatcher maps both to bank1E. Type byte not read by reachable platform callbacks. Art and parameter data remain distinct.',
        initializer='bit7 flags3; bit7 parameter enables sag25, bit6 sets26; req=(p&63)+1 saved36, p&127 in5/11 overrides req13; aux1->34/37, tick30=16, owner32 from slot; deltas/sag/latch/scratch zero; flags render C0/02',
        state4='frame1, speed0; 1E=80. Top-classified contact after support/sag sets27=80. Subsequent active callbacks decrement delay; following callback sets27=FF, next begins gravity48/256 with no cap. Move before support once falling. Only playerVy>=0 is required: unlike86A1, no relative platform/player speed gate. Sleep with27!=0 sets runtime parameter3F=80, clears placement token and marksFE, leaving occupancy spent until act restart; idle sleep returns.',
        state7='frame1, keepalive bit1, vx256. Any shared rectangle contact triggers31=1 and moves immediately; support after move. 30 counts16 moving calls, 37 counts aux1 such groups, reload and negate vx after movement/carry. At negative vx latch2, after full return nonnegative vx latch0. Aux50=800 calls/pixels each leg, not50px. Sag0..8 via25 independent of movement. Asleep does not pause; own strict player-distance640X/672Y retention marksFE but finishes callback. Cleanup releases occupancy; recreation resets everything.',
        state13='awake, playerVy>=0, shared overlap classifies top bit0: requests36; zone4 act1 overrides request to14 regardless of type or parameter. p5/11 first select13; 8B alone is not state14 predicate. No carry/support-owner acquisition in this gate callback.',
        state14='helper8577 zeros carry deltas at each direction change; vx+1 160 calls, vy+1 64, vx+1 96, vy-1 128+128. Frame1 throughout. No acceleration or terrain probe. No-rider displacement(+256,-192) after576 movement calls. Tail sets1E80 and2780, speed0; jumps8489 callback8719 without changing numeric current/requested state14. Thus waits80 active calls then same unbounded falling tail as4. No transition to numeric4. Sag can offset route Y by0..8.',
        asleep_route='8628/86A1 first integrate once when asleep then continue normal code and integrate again: two movement steps per callback, timers unchanged. Horizontal carry delta includes only second integration. Generic lifecycle may then delete, since state14 does not set keepalive. Post-route falling tail uses8719 spent-token deletion.',
        support='ordinary Sonic triangle dy=-16..-1 inclusive, abs(dx)<=8+abs(dy), different owner blocks. 8628/8662 and falling8719 require playerVy>=0; route vertical86A1 requires signed platformVy<=playerVy. Falling state4/state14 tail deliberately has no relative-speed gate. Sag before carry, riderY=platformY-14; add integer horizontal delta; preserve XY speeds/state/floor flags; shared contact bits merge next player phase.',
        water='no D443/D450/controller/underwater-flag reads in reachable callbacks/helpers. Changing water flag/line alone cannot change platform. Water affects player-provided Y speed before support via A2; indirect eligibility can differ. State14 no-rider route Y669->733->477 stays above788; later fall may cross without drag/buoyancy.',
        lifecycle='mapped creator stores raw-derived WORLD coordinates plus origins, flags|64 and canonical token. Generic create/wake/sleep/delete use accepted 256px EDGE bands; callback precedes lifecycle update, so previous asleep flag is observed. FE->FF->zero; token release except spent8719 clears token first. Generic fresh recreation only for released occupancy.',
        scheduling='camera, player movement/water/terrain, then object animation and callback, then generic lifecycle, periodic mapped creation. No source code or placement changed.',
        viewport={'placement':'WORLD','route_and_excursion':'WORLD origin-relative','keepalive':'PLAYER_DIST(640,672)','generic_lifecycle':'EDGE canonical256px'},
        art='approved A1 frame0/1 mappings, aux0 tile base80; aux1=32/00 is counter data, not a second tile base; no new reachable frames or synthetic compositions',unresolved=[])

def build(r):
    COUNTS.clear();recs=placements(r);check('rom',F.digest(r),L.ROM_SHA256)
    check('shared_tables',C.state_scripts(r,63)['states'],C.state_scripts(r,40)['states'])
    value=dict(rom_sha256=L.ROM_SHA256,research_base=BASE,tool_sha256=F.digest(Path(__file__).read_text(encoding='utf-8').encode()),
        source_regions={n:F.source(r,*v) for n,v in dict(script=(30,0x8439,0x8585),callbacks=(30,0x8585,0x8947),creator=(28,0x8000,0x813C),scheduler=(0,0x5DD1,0x5F17),overlap=(0,0x6328,0x6459)).items()},
        scripts=C.public_script(C.state_scripts(r,63)),contracts=contracts(),creators=creator(r,recs),reuse=equivalence(r,recs),gate_vectors=gate(r,recs[2]),support_vectors=support(r,recs),route=route(r,recs[2]),variants=variants(r,recs),boundaries=boundaries(r,recs),callback_support=callback_support(r,recs[2]))
    value['assertions']=dict(COUNTS);value['assertion_total']=sum(COUNTS.values());return value

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();v=build(L.load_rom(a.rom))
    if a.check:check('cache',OUTPUT.read_text(encoding='utf-8'),F.dumps(v))
    else:OUTPUT.write_text(F.dumps(v),encoding='utf-8')
    print(v['assertions'],v['assertion_total'])
if __name__=='__main__':main()

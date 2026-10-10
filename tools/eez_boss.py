"""Final-act source graph, first-parent contact sweep and terminal flag rules.

Source graphs and boundary sweeps complement original controlled whole-chain
traces; they do not claim input-only fights or Windows acceptance.
"""
import argparse,itertools
import eez_foundation as F
import level_package as L
import mghz_object_census as C
import mghz56_runtime as M
import thz1_type18_dynamic_graphics as D
import rom as R
from oracle import Oracle
S=0xD700

def build(r):
    o=Oracle(r);o.bank(2,30);o.cpu.ix=S;m=o.mem;m[0xD12B]=30;m[0xD52C]=8;m[0xD52D]=24;checks={};vectors=[]
    def eq(k,a,b):checks[k]=checks.get(k,0)+1;assert a==b,(k,a,b)
    for frame,attack,hurt,ground,cd,hp,point in itertools.product((1,5),(0,2),(0,64),(0,2),(0,1,2,16),(0,1,16),((0,-64),(0,-48),(0,24),(-24,0),(24,0),(25,0))):
        m[S:S+64]=bytes(64);m[S]=94;m[S+6]=frame;m[S+38]=hp;m[S+55]=cd
        extent=[16,64 if frame==1 else 48];m[S+44:S+46]=bytes(extent)
        o.word(S+17,2208);o.word(S+20,494);o.position(2208+point[0],494+point[1])
        m[0xD501]=m[0xD502]=9;m[0xD503]=attack|hurt;m[0xD522]=ground;m[0xD532]=0;m[0xDE04]=0;m[0xD3B0]=0
        o.word(0xD516,256);o.word(0xD518,256);o.call(0xB2EC)
        skip=frame!=5 and attack and ground
        bit=0 if skip or hurt else M.overlap_model(*point,ox=16,oy=extent[1])
        damaging=not skip and cd==0 and bit&1 and attack
        eq('5e_hp',m[S+38],(hp-1)&255 if damaging else hp)
        eq('5e_cooldown',m[S+55],cd if skip else 16 if damaging else max(0,cd-1))
        eq('5e_feedback',m[0xDE04],182 if not skip and cd==0 and bit and not bit&2 and attack else 0)
        if point==(0,-48) and hp==1:vectors.append([frame,attack,hurt,ground,cd,m[S+38],m[S+55],m[S+2]])
    geometry=[]
    for frame,ex in itertools.product(range(1,6),(8,9)):
        fr=C.frame_record(r,94,frame,0,0,bytes(0x4000));ox,oy=fr['extent_x_y'];geometry.append([frame,ex,ox,oy])
        for dx,dy in itertools.product(range(-ox-ex-2,ox+ex+3),range(-oy-2,27)):
            m[S:S+64]=bytes(64);m[S]=94;m[S+6]=frame;m[S+38]=16;m[S+44:S+46]=bytes((ox,oy));o.word(S+17,2208);o.word(S+20,494)
            o.position(2208+dx,494+dy);m[0xD52C]=ex;m[0xD52D]=24;m[0xD503]=2;m[0xD522]=0;m[0xDE04]=0
            o.call(0xB2EC);bit=M.overlap_model(dx,dy,ex=ex,ox=ox,oy=oy)
            eq('5e_complete_geometry',[m[S+33]&15,m[S+38]],[bit,15 if bit&1 else 16])
    for frame,req,floor,dx,phase in itertools.product(range(6),range(14),(0,2),range(-49,50),(0,1)):
        m[S:S+64]=bytes(64);m[S+6]=frame;m[S+2]=req;m[S+52]=phase;o.word(S+17,2208);o.position(2208+dx,494);m[0xD522]=floor;o.word(S+22,123);o.word(S+24,456)
        o.call(0xB257)
        if frame in (3,4):expected=[req,0,0,0,phase,123,456]
        elif abs(dx)<48 and floor&2 and req!=11:expected=[13,req,11,8,phase,0,64512]
        else:
            choose_attack=(phase+1)&1 and req not in (9,10,11)
            chosen=(9 if dx>0 else 10) if choose_attack else (7 if dx>0 else 6)
            expected=[13,req,chosen,8,phase+1,123,456]
        eq('5e_decision',[m[S+2],m[S+10],m[S+11],m[S+30],m[S+52],o.word(S+22),o.word(S+24)],expected)
    rows=[]
    second=[]
    for angle,attack,hurt,asleep,disabled,point in itertools.product((0,1),(0,2),(0,64),(0,64),(0,255),((0,-32),(0,-33),(0,24),(-28,0),(28,0),(29,0))):
        o.bank(2,30);m[0xD12B]=30;m[S:S+64]=bytes(64);m[S]=96;m[S+1]=m[S+2]=9
        m[S+10]=angle;m[S+44]=20;m[S+45]=32;m[S+4]=asleep;m[S+38]=disabled
        o.word(S+17,2464);o.word(S+20,414);o.position(2464+point[0],414+point[1])
        o.word(0xD516,0);o.word(0xD518,256);m[0xD501]=m[0xD502]=9;m[0xD503]=attack|hurt;m[0xD3B0]=0;m[0xDE04]=0;m[0xD523]=0;m[0xD522]=0;m[0xD52C]=8;m[0xD52D]=24
        m[S+55]=3  # movement route3 avoids other phase changes in this fixture
        # Death helper4984 waits on IRQ at062D. Preserve its writes and skip
        # only that wait in this interrupt-free routine oracle.
        o.cpu.set_breakpoint(0x062D);o.cpu.pc=0xB741;o.cpu.sp=0xDFE0;o.word(o.cpu.sp,o.RETURN)
        for _ in range(20):
            o.cpu.ticks_to_stop=100000;o.cpu.run()
            if o.cpu.pc==0x062D:
                o.cpu.pc=o.word(o.cpu.sp);o.cpu.sp+=2
            elif o.cpu.pc==o.RETURN:break
        assert o.cpu.pc==o.RETURN
        o.cpu.clear_breakpoint(0x062D)
        bit=0 if hurt or asleep or disabled else M.overlap_model(*point,ox=20,oy=32)
        hit=bool(bit&1 and attack)
        eq('60_hit_latch',m[S+53],int(hit))
        eq('60_hit_phase',m[S+2],10 if hit and angle else 9)
        eq('60_disabled',m[S+38],255 if hit and not angle else disabled)
        death=bool(bit and not hit)
        assert m[0xDE04]==(182 if hit else 150 if death else 0),(angle,attack,hurt,asleep,disabled,point,bit,m[S+33],m[0xD502],m[0xDE04])
        eq('60_hit_sound',m[0xDE04],182 if hit else 150 if death else 0)
        eq('60_death_request',m[0xD502],31 if death else 27 if hit else 9)
        if hit:second.append([angle,attack,hurt,asleep,disabled,point,m[S+2],m[S+38]])
    for y in (0,493,494,495,32767,32768,65535):
        o.word(S+20,y);o.call(0xB2DB);eq('5e_world_floor',o.cpu.a,255 if y>494 else 0)
    for angle,px,turn in itertools.product(range(256),range(256),(0,1)):
        m[S:S+64]=bytes(64);m[S+10]=angle;m[S+31]=turn;o.word(0xD174,2000);m[0xD51A]=px
        o.call(0xB67F)
        odd=(angle+1)&1
        route=(1 if odd else 0) if px<85 else (0 if odd else 1) if px>=165 else 3 if not turn else 2
        eq('60_route_entry',[m[S+2],m[S+10],m[S+55],o.word(S+17),o.word(S+20),o.word(S+22),o.word(S+24)],
           [9,(angle+1)&255,route,2000 if odd else 2256,414 if route in (0,2) else 480,896 if odd else (-896)&65535,0])
    for param,parity in itertools.product(range(256),(0,1)):
        o.bank(2,30);m[0xD12B]=30;m[S:S+64]=bytes(64);m[S+63]=param;m[0xD12F]=parity
        o.call(0xB3D5)
        phase=6 if param==254 else 2 if param==1 else 4 if param==255 else 5 if parity else 1
        vx=0 if param==254 or (param not in (1,255) and parity) else -768 if param==1 else -672 if param==255 else -608
        vy=768 if param==1 else 48 if param==255 else 0
        eq('5f_initial',[m[S+2],o.word(S+22),o.word(S+24),m[S+10]],[phase,vx&65535,vy,0 if param==254 else 8])
    for counter,camera,current,px in itertools.product(range(256),(0,3200,3328),(0,3400,3504,3600),(3455,3456)):
        m[S:S+64]=bytes(64);m[S+1]=m[S+2]=2;m[S+30]=counter;o.word(S+17,current);o.word(0xD174,camera);o.position(px,0)
        o.call(0xBA96)
        n=(counter+1)&127;offset=n if n<64 else 127-n
        target=camera+176+offset
        eq('61_chase',[m[S+2],o.word(S+17),m[S+30]],
           [3,current,counter] if px>=3456 else [2,current if current>=target else min(target,3504),(counter+1)&255])
    for dx in range(-114,115):
        m[S:S+64]=bytes(64);m[S+1]=m[S+2]=1;o.word(S+17,2752);o.word(S+20,494);o.position(2752+dx,494)
        o.call(0xBA87);eq('61_trigger',m[S+2],2 if abs(dx)<112 else 1)
    for phase,v in itertools.product((0,1),range(65536)):
        m[S:S+64]=bytes(64);m[S+52]=phase;o.word(S+24,v);o.word(S+20,414);o.call(0xBC86)
        new=(v+(-2 if phase else 2))&65535
        flip=(bool(new&32768) and (new&255)<224) if phase else (not new&32768 and (new&255)>=32)
        eq('63_oscillator',[o.word(S+24),m[S+52]],[new,phase+int(flip)])
    allocations=[]
    for free in range(12):
        m[0xD700:0xD9C0]=bytes([255])*704
        if free<11:m[0xD700+free*64]=0
        o.call(0x5EE1);eq('command4_pool',[o.cpu.iy,bool(o.cpu.f&1)],[0xD700+free*64,free==11])
        allocations.append([free,o.cpu.iy,bool(o.cpu.f&1)])
    m[S:S+64]=bytes(64);o.cpu.iy=0xD800;o.call(0xB389);eq('5f_parent_pointer',o.word(0xD838),S)
    o.call(0xB585);eq('60_controller_pointer',o.word(S+56),0xD800)
    endings=[]
    for pc in (0x18FE,0x1A41,0x1ACD):o.cpu.set_breakpoint(pc)
    for char,flags in itertools.product((0,1,2),range(256)):
        m[0xD2C8]=char;m[0xD2CC]=flags;o.cpu.pc=0x18ED
        for _ in range(20):
            o.cpu.ticks_to_stop=100000;o.cpu.run()
            if o.cpu.pc in (0x18FE,0x1A41,0x1ACD):break
        expected=0x1ACD if char!=1 else 0x18FE if flags&63==63 else 0x1A41
        eq('ending_selector',o.cpu.pc,expected)
        if flags in (0,31,63,255):endings.append([char,flags,o.cpu.pc])
    o.cpu.set_breakpoint(0x1333)
    for zone in range(6):
        m[0xD297]=zone;m[0xD298]=2;m[0xD293]=80;o.cpu.pc=0x15CE
        for _ in range(20):
            o.cpu.ticks_to_stop=100000;o.cpu.run()
            if o.cpu.pc==0x1333:break
        eq('zone_terminal',[m[0xD297],m[0xD298],m[0xD293]],[zone+1,0,192 if zone==5 else 66])
    for pc in (0x18FE,0x1A41,0x1ACD,0x1333):o.cpu.clear_breakpoint(pc)
    for current,flags in itertools.product((0,1,2),range(256)):
        m[0xD500]=current;m[0xD2CC]=flags;m[0xD293]=64;m[S]=97;m[S+44]=m[S+45]=0
        o.word(S+17,1000);o.word(S+20,1000);o.position(0,0);m[0xD503]=64
        o.call(0xBB1A)
        eq('61_early_clear',m[0xD293],64 if current==1 and flags==31 else 80)
        m[0xD2CC]=flags;m[0xD293]=64;m[S]=97;o.call(0xBB61)
        eq('61_final_flags',[m[0xD2CC],m[0xD293],m[S]],[flags|32,80,255])
        if flags in (0,31,63):rows.append([current,flags,m[0xD2CC],m[0xD293]])
    dynamic={}
    for selector in (24,25,26,33):
        cpu,entries=D.dynamic_list_for_selector(r,selector);dynamic[str(selector)]=dict(cpu=cpu,entries=entries)
    return dict(rom_sha256=L.ROM_SHA256,checks=checks,assertions=sum(checks.values()),contact_vectors=vectors,
        completion_vectors=rows,ending_vectors=endings,second_parent_vectors=second,geometry=geometry,allocations=allocations,scripts={f'0x{t:02X}':C.public_script(C.state_scripts(r,t)) for t in list(range(94,100))+[21,31,34]},
        graphics=dynamic,regions=[F.A.source(r,30,0xAF4C,0xBCCE),F.A.source(r,0,0x18ED,0x1B5E),F.A.source(r,0,0x1333,0x138A),F.A.source(r,0,0x1543,0x15F2)],
        framework=C.boss_tables(r),
        contracts=dict(
            trigger='5E row5 strict PLAYER_DIST(96,304);60 gated by D4A7 then shared row6, same thresholds. Initial placement5E(2080,494),60(2464,494). Camera targets(1952,334)/(2336,334) from WORLD offsets(-128,-160); generic exclusive pan semantics retained.',
            first_parent='5E 14 states;B011 keepalive,bossactive6,D4A5=0,HUD12,right-limit save. B02B selector24,palette17,newX+128,VX-0.75,counterE0,HP16,D4A7=0,state12. States6/7 patrol with callback frame selectors1..4 and screen-X thresholds48/192; states9/10 launch5F;state11 jump;state13 eight-call attack-selection pause.',
            contact5e='B2EC: pending defeat38 ->state4. Otherwise palette restore; frame!=5 with attacking+grounded player returns before overlap/cooldown. Shared5FA0 contact. Cooldown37 decrements and skips damage while nonzero. Bottom contact sets hurt request. Other attacking contact rebounds via8105; only topbit0 decrementsHP. HP reaches0 ->state4,defeat38FF; cooldown16,soundB6 and palette entries13/14 flashwhite. Not THZ top-immunity.',
            defeat5e='shared explosion state4 ->ownstate5: VY-1 and20 loops of frame20/0 duration2 each, thenVX+2,VY0,delay32, sameflash. B217 waits asleepbit6 thenzerosVX,countdownborrow ->D280=cameraX,releasepan,restore savedrightlimit,D4A7FF,token0,param80,typeFE. No ordinary player20/bonus clear at this intermediate boss.',
            child5f='seven states and parameter-specific initialization:1 bouncing(-3,+3) with3 floor rebounds;0 parity selects projectile or tethered attachment;FF special(-2.625,+0.1875),FE parent link. Callback B389 stores parent pointer in child38/39. B463 checks WORLD Y>494 ->shareddefeat, then asleep delete; movement, forcedhurt, cached screen7/249 X reversal. B4FC follows parent X with8-step Y wobble. Full scripts preserve callbacks/velocities/frame timing.',
            second_parent='60 state0 command4 creates63 andB585 stores IY pointer38/39;B624 waits D4A7!=0,clearsD3E7,D4A5=1,HUD/rightsave,state2. State3 waits pointed-slot type!=63,then selector25,state7,Y414,counter32. State7/8 delay ->state9 repeated flight orstate10 escape when field26 nonzero. State9 chooses routes from player cachedscreenX thresholds55/A5 and angle parity; screenedge placements0/256,turnspawns32/224 and cameraY; WORLD Y414/480.',
            contact60='state9 B741 while awake andfield26==0: shared5FA0; attacking top contact setsfield35,feedbacksoundB6,paletteflash;ANY other overlap invokes4984 immediate DEATH (state1F,sound96), bypassing ordinary ring-loss hurt. No general HP decrement. Successful odd-angle contact immediately requests10;even sets26FF andcounter32; passingawake->asleep requests8/delay80 thenescape. Routine oracle skips only IRQ wait062D after death writes.',
            defeat60='state10script35 explosionchildren and timer33calls ->state11,VX+0.75,VY0,field23=FD00;state11 alternatingVY±1 passeswith35 children; asleep ->state12;state12command4 creates61, B92D releasespan/restoresright,signalsD4A7FF,convertsFE without player20.',
            controller63='selector33,keepalive,Y414;waitawake thenframes1..5 duration32,6/7 duration8;vertical oscillator accelerates±2/256 between signed thresholds;thenVX-2.5 untilasleep->state3delete. This is dependency for60 entry, not inferred scenery.',
            final61='initializer stops timerD2BE=0,bossactive6,selector26,palette17,D4A5=2,HUD/rightsave;WORLD(2752,494). Wait strict |dx|<112, state2chase: triangular128-call offset176..239 fromcameraX, forwardonly capWORLD3504. WORLD playerX>=3456 ->state3 script32+64 delay thenstate4; gravity+1/16, motions0.25/-4 etc retained in scripts.',
            final62='WORLD(3536,430),keepalive;bob±0.5 in8-call halves;D3E7nonzero ->state2bob±1 then soundBE andrise-1 untilasleep;clearsD3E7/deletes. 61 waits D3E7zero afterrise thenstate5; state5 emits0Aparam1 at±4, gravity4/256,settlesstate6,overlap->7. State7 sets collectedflagsbit5 and D293=50,delete. Earlystate5 clearsimmediately except Sonic with collectedflags exactly1F.',
            endgame='D29350 haszone-clearbit4;1543 results/transition skips32F9 whenzone>=5.15CE resetsact, incrementszone to6,setsbit7 ratherthannextactbit1.1333bit7 invokes1365 ->18ED ending, then clearsflags andjumps04B4. Ending selector: D2C8==1 and(D2CC&3F)==3F enters18FE; D2C8==1 partial ->1A41;othercharacter ->1ACD. Full source is retained; no invented credits/art.',
            ending_full='18FE scene usesbank9BD90,player1state31,type22,sound8D,backgroundpalettes2A..2F,1500calls each exceptfinal3000;repeatuntilD3C1FF. Thenbank14B23A,type15 parameters0..3,waitD766FF. Exact visible text/credits attribution requires graphics/scene trace.',
            ending_partial='1A41 scene bank9B600,player1state33,type1Fparam1 at144,88,sound9A,palettes2A/29;waitplayerdeletion,fade,34D3 timed scene bankload7A3C,palette25,sound98,thenreturn.',
            route60='B67F counter borrow starts flight; odd angleVX+3.5 atcameraX,evenVX-3.5 atcameraX+256. Player cachedscreenX<85 chooses route1/0 forodd/even; >=165 chooses0/1; middle alternates3/2. Routes0/2 Y414,1/3 Y480. B7BC moves BEFORE acceleration. Route0 addsVy32/256 until>=448/256 then subtracts8/256 toward0 and acceleratesX16/256. Route1 mirrored upward with strict threshold below-448/256. Route2 first pass setsXcamera+32odd/+224even,YcameraY,Vy+6,Vx±1.625,then subtractsVy32/256 eachlaterpass. Route3 acceleratesX16/256. No viewport-dependent world offsets.',
            oscillator63='BC86 moves before Vy update. Phase even adds2/256 and flips when new signnonnegative AND new lowbyte>=20hex; odd subtracts2/256 and flips when new signnegative AND new lowbyte<E0hex. At natural velocities this oscillates through+32/256 and-34/256; do not replace the lowbyte/sign tests with a generic float clamp.',
            validation_limits='Source graphs and full controlled chain traces are separate evidence. Both60 angle branches and Sonic ending branches execute to title; long passive5E paths observed plus exhaustive decision/contact sweeps. Not an input-only fight. Art approval and scene raster fidelity remain James review; do not claim Windows acceptance.'))

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();v=build(L.load_rom(a.rom))
    (F.OUT/'boss-endgame-recon.json').write_text(F.dumps(v),encoding='utf-8');print(v['checks'],v['assertions'])

if __name__=='__main__':main()

"""AQZ A2: verified source, original-routine sweeps and canonical water contracts.

No pixels or ROM dump; all oracle inputs are explicit synthetic controls.
"""
import argparse
import itertools
from pathlib import Path
import aqz_foundation as F
import level_package as L
import rom as R
import mghz_object_census as C
import thz1_object_assets as G
import powerup_shoes as Shoes
from oracle import Oracle

OUTPUT=F.OUT/'water-runtime.json'
BASE='d1661de8b44b7904dd1c250c6fa53b8f4c24b735'
SLOT=0xD700

def lab(r,bank=12):
    o=Oracle(r);o.bank(2,bank);o.mem[0xD297]=4
    o.word(0xD450,568);o.position(128,600)
    return o

def slots(o):
    return [dict(slot=b,type=o.mem[b],parameter=o.mem[b+63]) for b in range(0xD540,0xD940,64) if o.mem[b]]

def crossings(r):
    o=lab(r);rows=[]
    for dy,flag,vy,vx,attack in itertools.product(range(-5,6),(0,255),(-1280,-1,0,1,1024),(-1280,-1024,-1023,0,1023,1024,1280),(0,2)):
        m=o.mem;m[0xD540:0xD940]=bytes(1024)
        o.position(128,568+dy);m[0xD443]=flag;m[0xD503]=attack
        o.word(0xD516,vx);o.word(0xD518,vy)
        before=bytes(m[0xD500:0xD540]);o.call(0x4BC0)
        expected=dy>=0
        # The speed gate uses the signed high byte, not abs(full fixed point).
        high=(vx>>8)&255;high=256-high if high&128 else high
        bounce=expected and vy>=0 and attack and high>=4
        assert m[0xD443]==(255 if expected else 0)
        assert R.s16(o.word(0xD518))==(-768 if bounce else vy)
        assert o.word(0xD516)==vx&65535
        assert slots(o)==([dict(slot=0xD540,type=14,parameter=0)] if expected and not flag else [])
        changed=[i for i,(a,b) in enumerate(zip(before,m[0xD500:0xD540])) if a!=b]
        assert set(changed)<=set((24,25))
        rows.append(dict(dy=dy,prior_water=flag,vy=vy,vx=vx,attack=attack,water=m[0xD443],result_vy=R.s16(o.word(0xD518)),splash=bool(slots(o))))
    return rows

def timers(r):
    o=lab(r);rows=[]
    for dy,fine,coarse,full in itertools.product((-1,0,1),(0,118,119,120,254,255),(0,10,11,15,16,17),(False,True)):
        m=o.mem;m[0xD540:0xD940]=bytes([1 if full else 0])*1024
        m[0xD443]=255;m[0xD444]=fine;m[0xD445]=coarse;m[0xD502]=5;m[0xD503]=0
        o.position(128,568+dy);o.word(0xD518,0);o.call(0x4B46)
        rolled=dy>=0 and ((fine+1)&255)>=120
        nf=0 if rolled else ((fine+1)&255) if dy>=0 else fine
        nc=(coarse+1)&255 if rolled else coarse if dy>=0 else 0
        assert (m[0xD444],m[0xD445])==(nf,nc)
        assert m[0xD502]==(31 if rolled and nc==17 else 5)
        assert sum(x['type']==50 for x in slots(o))==(1 if rolled and nc==11 and not full else 0)
        rows.append(dict(dy=dy,fine=fine,coarse=coarse,pool_full=full,result_fine=nf,result_coarse=nc,requested=m[0xD502],countdown=sum(x['type']==50 for x in slots(o))))
    return rows

def physics(r):
    o=lab(r);rows=[]
    for state,water,air,vy,forced,surface in itertools.product((3,4,5,6,9,10,11,14,17,18,20,27,30,31,37,40),(0,255),(0,1),(-1280,-1,0,1000,1023,1024,1792),(0,2),(0,10)):
        m=o.mem;m[0xD501]=state;m[0xD443]=water;m[0xD503]=air;m[0xD522]=forced;m[0xD369]=surface;m[0xD3C0]=0
        o.word(0xD518,vy);o.word(0xD513,0);m[0xD515]=0;o.call(0x4097)
        if state==17:expected=vy
        elif air:expected=min(vy+(12 if state==11 else 18 if state==27 else 24) if water else vy+(24 if state==11 else 36 if state==27 else 48),1024 if water else 1792)
        else:expected=abs(vy)
        if forced:expected=2304 if surface==10 else 1792
        assert R.s16(o.word(0xD518))==expected,(state,water,air,vy,forced,surface,expected,R.s16(o.word(0xD518)))
        rows.append(dict(state=state,water=water,air=air,vy=vy,forced=forced,surface=surface,result_vy=expected))
    controls=[]
    for state,water,vx,pad in itertools.product(range(55),(0,255),(-1024,-127,0,127,1024),(0,4,8)):
        m=o.mem;m[0xD501]=state;m[0xD443]=water;m[0xD137]=pad;m[0xD369]=0
        o.word(0xD511,128);o.word(0xD174,0);o.word(0xD516,vx);o.word(0xD375,0x1234);o.word(0xD377,0x5678)
        o.call(0x4141)
        controls.append(dict(state=state,water=water,vx=vx,pad=pad,input_acceleration=R.s16(o.word(0xD375)),slope_acceleration=R.s16(o.word(0xD377))))
    jumps=[]
    for water,state in itertools.product((0,255),(3,5,9,14,17)):
        m=o.mem;m[0xD501]=state;m[0xD502]=state;m[0xD503]=0;m[0xD443]=water;m[0xD36B]=0;m[0xD522]=2
        o.word(0xD514,600);o.word(0xD518,0);o.call(0x45ED)
        assert R.s16(o.word(0xD518))==(0 if state==17 else -832 if water else -1088)
        jumps.append(dict(state=state,water=water,vy=R.s16(o.word(0xD518)),requested=m[0xD502],flags=m[0xD503],floor=m[0xD522],y=o.word(0xD514)))
    return dict(vertical=rows,control=controls,jump=jumps,
        horizontal_tables={name:[[R.s16(R.u16(r,a+i*4+j*2)) for j in range(2)] for i in range(32)] for name,a in [('dry_positive',0x429D),('dry_negative',0x431D),('neutral',0x439D),('water_positive',0x441D),('water_negative',0x449D)]},
        slope_table=dict(cpu=0x459D,sha256=F.digest(r[0x459D:0x45B3])),
        unreachable_helpers=dict(halve_maximum=0x4B94,quarter_motion=0x4BA5,note='No CALL/JP references to these helpers in the verified ROM; do not apply them to underwater loops.'))

def raster(r):
    o=lab(r);rows=[]
    for delta,enabled in itertools.product((-1,0,1,2,191,192,193,255,256),(0,255)):
        m=o.mem;o.word(0xD176,568-delta);o.word(0xD450,568);m[0xD131]=enabled;m[0xD132]=77;m[0xD492]=m[0xD494]=0;m[0xD493]=m[0xD495]=0
        o.call(0x9DED)
        assert m[0xD131]==(255 if 0<delta<=192 else 0)
        assert m[0xD132]==(delta if 0<delta<=192 else 255 if enabled else 77)
        assert [m[0xD493],m[0xD495]]==([48,49] if delta<=0 and enabled else [25,10] if delta>192 and enabled else [0,0])
        rows.append(dict(screen_delta=delta,prior_enabled=enabled,enabled=m[0xD131],line=m[0xD132],palette_requests=[m[0xD493],m[0xD495]]))
    positions=[]
    for param,cx in itertools.product((0,1),(0,257,5120)):
        m=o.mem;o.cpu.ix=SLOT;m[SLOT:SLOT+64]=bytes(64);m[SLOT+63]=param;o.word(0xD174,cx)
        for update in range(1,33):
            o.call(0x9EFE);expected=cx+R.u16(r,12*0x4000+(0x9F2B if param==0 else 0x9F4B)-0x8000+(update%16)*2)
            assert o.word(SLOT+17)==expected
            positions.append(dict(parameter=param,camera_x=cx,update=update,x=o.word(SLOT+17)))
    fixed=r[0x0688:0x06A8];selected=r[L.PALETTE_DATA+48*16:L.PALETTE_DATA+50*16]
    return dict(boundary_vectors=rows,strip_vectors=positions,strip_tables={str(p):[R.u16(r,12*0x4000+a-0x8000+i*2) for i in range(16)] for p,a in [(0,0x9F2B),(1,0x9F4B)]},
        palette_modes=dict(split_irq_cram=list(fixed),fully_submerged_cram=list(selected),
            above_water_cram=list(r[L.PALETTE_DATA+25*16:L.PALETTE_DATA+26*16]+r[L.PALETTE_DATA+10*16:L.PALETTE_DATA+11*16]),
            color_encoding='SMS CRAM: red=bits0..1, green=bits2..3, blue=bits4..5, each component*85',
            split_irq_cram_sha256=F.digest(fixed),fully_submerged_palette_sha256=F.digest(selected),identical=False,
            differing_indices=[i for i,(a,b) in enumerate(zip(fixed,selected)) if a!=b],
            rule='split IRQ copies fixed $0688 bytes directly; fully submerged camera path requests palette48/49 from bank0E:B64D. These are different colors, not interchangeable.'),
        viewport='EDGE(TOP, delta), 0 < WORLD(waterline)-cameraY <= 192; canonical 192-line domain',
        irq=dict(cpu=0x0652,cram_source=F.source(r,0,0x0688,0x06A8),count=32,
            condition='D132 != FF OR D443 != 0; copies fixed 32-byte palette, clears register0 bit4, sets D496 for next palette restore',
            enable_vector=0x040A,enable_target=0x1C9B,disable_vector=0x040D,disable_target=0x1CA8,
            enable='R0=$36 (line IRQ bit4); conditional on (D492 & CF)==0',disable='R0=$26',
            arm='Vblank $04EF..$0513: D131 nonzero and (D492 & CF)==0 writes D132 to R10, then sets R0 bit4',
            restore='$0627 -> $1CBD restores D472[32] to CRAM and clears D496 on a guarded vblank',
            note='SMS line counter reload/underflow semantics apply; D132 is the register value, not a synthetic pixel cut.'))

def object_vectors(r):
    out={};o=lab(r);m=o.mem
    for t in (12,13,14,50):out[str(t)]=C.public_script(C.state_scripts(r,t))
    initial=[]
    for t,p,a in [(12,0,0x9CF6),(12,1,0x9CF6),(12,2,0x9CF6),(12,3,0x9CF6),(13,0,0x9DAD),(13,1,0x9DAD),(14,0,0x9FAA),(50,0,0x9500)]:
        for act in (0,1):
            o.bank(2,30 if t==50 else 12);o.cpu.ix=SLOT;m[SLOT:SLOT+64]=bytes(64);m[SLOT]=t;m[SLOT+63]=p;m[0xD298]=act
            o.word(SLOT+17,100);o.word(SLOT+20,800);o.word(0xD174,256);o.position(128,600);o.call(a)
            initial.append(dict(type=t,parameter=p,act=act,requested=m[SLOT+2],flags3=m[SLOT+3],flags4=m[SLOT+4],art=[m[SLOT+8],m[SLOT+9]],x=o.word(SLOT+17),y=o.word(SLOT+20),vy=R.s16(o.word(SLOT+24))))
    bubble=[]
    for cb,dx,dy,frame,phase,sleep,hurt in itertools.product((0x9D50,0x9D39),(-20,-16,-1,0,1,16,20),(-30,-24,-1,0,1,16,24,30),(0,1,2,3),(0,1,3),(0,64),(0,64)):
        o.bank(2,12);o.cpu.ix=SLOT;m[SLOT:SLOT+64]=bytes(64);m[SLOT]=12;m[SLOT+3]=128;m[SLOT+4]=sleep;m[SLOT+6]=frame;m[SLOT+44]=8;m[SLOT+45]=16
        m[0xD52C]=8;m[0xD52D]=24;m[0xD503]=hurt;m[0xD12F]=phase;m[0xD2E2]=0;m[0xD502]=5
        o.position(128+dx,600+dy);o.word(SLOT+17,128);o.word(SLOT+20,600);o.word(SLOT+24,-192);o.call(cb)
        contact=cb==0x9D39 and not sleep and phase!=0 and abs(dx)<=16 and -16<=dy<=24
        assert m[0xD502]==(37 if contact else 5),(cb,dx,dy,phase,sleep,hurt,m[0xD502])
        assert m[SLOT]==(254 if contact or sleep else 12)
        bubble.append(dict(callback=cb,dx=dx,dy=dy,frame=frame,phase=phase,sleep=sleep,player_hurt=hurt,requested=m[0xD502],type=m[SLOT]))
    air=[]
    for fine,coarse in itertools.product((0,119),(0,10,11,16,17)):
        m[0xD444]=fine;m[0xD445]=coarse;o.cpu.ix=0xD500;o.bank(2,12);o.call(0x836F);assert (m[0xD444],m[0xD445])==(fine,0)
        air.append(dict(fine=fine,coarse=coarse,result_fine=m[0xD444],result_coarse=m[0xD445]))
    water_edges=[]
    for cb,dy,phase,sleep in itertools.product((0x9D50,0x9D39),range(-3,4),range(4),(0,64)):
        o.bank(2,12);o.cpu.ix=SLOT;m[SLOT:SLOT+64]=bytes(64);m[SLOT]=12;m[SLOT+4]=sleep;m[SLOT+45]=16
        m[0xD2E2]=phase;m[0xD12F]=0;o.word(0xD450,568);o.word(SLOT+20,568+16+dy);o.word(SLOT+24,-192)
        o.call(cb);removed=bool(sleep or phase and dy<0);assert m[SLOT]==(254 if removed else 12)
        water_edges.append(dict(callback=cb,extent_y=16,dy_above_extent_line=dy,phase=phase,sleep=sleep,removed=removed))
    return dict(scripts=out,initializers=initial,bubble_contact=bubble,air_reset=air,waterline_edges=water_edges)

def lifecycle(r):
    o=lab(r);m=o.mem;out={}
    # Full original object scheduler, including animation commands and child allocator.
    def trace(t,p,x,y,updates,full=False):
        m[0xD540:0xDA00]=bytes(1216);o.cpu.ix=SLOT
        if full:
            for b in range(0xD700,0xD9C0,64):m[b]=14;m[b+1]=m[b+2]=1;m[b+7]=200;o.word(b+12,0x032F)
        m[SLOT:SLOT+64]=bytes(64);m[SLOT]=t;m[SLOT+63]=p;o.word(SLOT+17,x);o.word(SLOT+20,y)
        o.word(0xD174,0);o.word(0xD176,500);o.position(128,600);m[0xD445]=11
        rows=[]
        for u in range(1,updates+1):
            m[0xD12F]=u&255;m[0xD2E2]=u&3;m[0xDE04]=0
            if full:o.cpu.ix=SLOT;o.bank(2,12);o.call(0x5DF1)
            else:o.call(0x5DD1)
            rows.append(dict(update=u,type=m[SLOT],state=m[SLOT+1],requested=m[SLOT+2],frame=m[SLOT+6],counter=m[SLOT+7],sound=m[0xDE04],children=[dict(slot=b,type=m[b],parameter=m[b+63],state=m[b+1]) for b in range(0xD540,0xDA00,64) if b!=SLOT and m[b]]))
        return rows
    out['emitter']=trace(12,0,128,686,725)
    out['emitter_pool_pressure']=trace(12,0,128,686,370,True)
    out['splash']=trace(14,0,128,568,20)
    out['countdown']=trace(50,0,128,600,730)
    # Original complete act RAM clear resets the fine timer and all objects.
    m[0xD300:0xDBC0]=bytes([170])*2240;m[0xD131]=m[0xD132]=255;o.call(0x297E)
    assert not any(m[0xD300:0xDBC0]);assert (m[0xD131],m[0xD132])==(0,0)
    out['restart']=dict(cpu=0x297E,cleared_range=[0xD300,0xDBC0],fine=m[0xD444],coarse=m[0xD445],water=m[0xD443],controllers=slots(o))
    o.cpu.ix=0xD500
    for act in (0,1,2):
        m[0xD540:0xD940]=bytes(1024);m[0xD298]=act;o.word(0xD450,0);o.call(0x2A2E)
        out[f'creator_act_{act}']=dict(waterline=o.word(0xD450),objects=slots(o))
    controller=[]
    for act in (0,1):
        m[0xD540:0xDA00]=bytes(1216);m[0xD298]=act;o.word(0xD176,500);o.word(0xD174,0);o.call(0x2A2E)
        for u in range(1,5):
            o.call(0x5DD1)
            controller.append(dict(act=act,update=u,line=o.word(0xD450),controllers=[dict(slot=b,type=m[b],state=m[b+1],requested=m[b+2],x=o.word(b+17),y=o.word(b+20)) for b in (0xD540,0xD580)]))
        o.word(0xD174,5120);o.word(0xD176,0);o.call(0x5DD1);o.call(0x5DD1)
        assert [m[0xD540],m[0xD580]]==[13,13]
    out['controllers']=controller
    return out

def contracts(r):
    states={}
    sc=C.state_scripts(r,1)
    for state in (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,19,20,26,27,28,30,31,32,37,40):
        states[str(state)]=dict(state=state,script_cpu=sc['states'][state]['script_cpu'],
            water_gravity=12 if state==11 else 18 if state==27 else 24,
            dry_gravity=24 if state==11 else 36 if state==27 else 48,
            gravity_unit='1/256 px/update squared; only when $4097 takes airborne branch',
            water_down_cap=1024,dry_down_cap=1792,
            control_table_water=[[R.s16(R.u16(r,a+state*4+j*2)) for j in range(2)] for a in (0x441D,0x449D)] if state<30 else None,
            control_table_dry=[[R.s16(R.u16(r,a+state*4+j*2)) for j in range(2)] for a in (0x429D,0x431D)] if state<30 else None,
            neutral_control=[R.s16(R.u16(r,0x439D+state*4+j*2)) for j in range(2)] if state<30 else None)
    for state in (12,13,19):states[str(state)].update(water_gravity=None,dry_gravity=None,water_down_cap=None,dry_down_cap=None,exception='route table integration; no $3FEF/$4B46/$4097 call, water flag and air timer remain latched during route; no underwater slowing')
    states['15'].update(water_gravity=0,dry_gravity=0,water_down_cap=None,dry_down_cap=None,exception='stationary spindash charge $396D calls terrain/damage/edge clamp, no shared movement or water updater; release setter +/-7 unchanged')
    states['17'].update(water_gravity=0,dry_gravity=0,water_down_cap=None,dry_down_cap=None,exception='Rocket $4097 goes straight to integration; Up/Down +/-64, neutral +/-32; signed-high-byte clamp as existing powerup-shoes vectors; maxX7, thrust dry16/water2, doubled at abs(vx)<128')
    states['32'].update(water_gravity=0,dry_gravity=0,water_down_cap=None,dry_down_cap=None,exception='clear $0C:$83A6 zeros vy, adds vx16 until high byte>=6; $0338 integration, no water updater/terrain/ring probe')
    states['37'].update(water_gravity=0,dry_gravity=0,water_down_cap=None,dry_down_cap=None,exception='air state $25: sound AE; 16 updates frame54 callback $836F clears D445; no movement or timer; then requests fall0E')
    states['40'].update(exception='drowning callback $3BFB fixes vy128 while screenY<216; at >=216 sets D293 bit2 and vy4096, then $4097 uses stale water flag and its cap4; no new water test or terrain')
    states['31'].update(exception='death callback $3BF0 -> $4097, hides blinking and sets flag3 bit6; water flag stays latched, gravity24/cap4; no water updater, terrain, damage/ring loss')
    return dict(
        crossing=dict(cpu=0x4BC0,zone_gate=[4,0,1],entry='unsigned player anchor Y >= WORLD waterline; equality submerged',exit='Y < waterline',
            modifications='D443 only; on entry allocate0E parameter0; no velocity scaling, floor/input/latch/animation/sound writes in crossing routine',
            repeated_gate='while submerged: vy>=0, attack bit1 and abs(signed vx HIGH BYTE)>=4 sets vy=-768; negative fractional vx uses its high byte, not abs(vx)',
            exit_effect=False,order='within $3FEF before screen-death, input tables, X/Y movement and terrain; flag can lag final Y by one update'),
        controllers=dict(type=13,bank=12,table=0x9D9B,reachable_states=[0,1],state2='alias of state1, no AQZ request path',
            creator=0x2A2E,parameters=[0,1],creation='first two free 16-slot allocator slots, sequential params0 then1; sets initial WORLD768 after both attempts',
            authority='both callbacks $9DDD prepare raster from previous D450 then publish their identical object WORLD Y (568/788); neither exclusively owns D450',
            strips='parameter0 offsets8..248 stride16; parameter1 same table rotated8 positions; index increments before lookup, wraps16 every callback',
            cadence='one callback per gameplay object pass, independent of 128-update animation-record restart',
            keepalive='+$04 bit1 prevents out-of-range deletion; generic lifecycle can mark asleep bit6 but callback does not gate it',
            gameplay='both redundantly publish authoritative waterline and prepare raster; parameters only change strip X; no separate presentation-only controller',
            failure='creator silently tolerates full pool; no retry; if both allocations fail initial768 persists; restart clears pool first so normal creation succeeds',
            first_pass='state0 initializes object Y but leaves D450=768; next pass state1 parameter0 prepares raster using768 then publishes568/788, parameter1 prepares from updated568/788 then republishes',
            restart='original $297E clears D300..DBBF, includes flags/timers/objects; $2934 calls clear, level data/load, $2A2E creator; AQZ3 skips creator/updater'),
        drowning=dict(updater=0x4B46,unit='calls of shared player-water updater, not wall clock',fine_address=0xD444,coarse_address=0xD445,
            increment='water true increments fine byte; if resulting byte>=120 resets0 then increments coarse; byte overflow255->0 does not roll coarse',
            reset='entry never resets either counter; exit resets coarse0 only; air state25 resets coarse0 only; restart clears both',
            thresholds=[dict(coarse=11,action='allocate type32 parameter0'),dict(coarse=17,action='request player1F, no direct ring/death setup')],
            non_threshold='no warning threshold besides11 and17; every rollover attempts small breath bubble0C param3 if R bit2 clear',
            allocation='16-slot allocator5E9C silently drops failed spawn; does not retry threshold32; request1F still happens at17; without countdown no9555 tail or camera lock/death setup, no invented fallback',
            countdown=dict(type=50,table_bank=30,table_cpu=0x94C6,states=[0,1],spawn='initializer playerX,playerY-34; following callback playerX,playerY-40',
                frames=[21,20,19,18,17,16],durations=[120]*6,sound=181,blink='+$07 counter bit2 controls +$04 bit7 every callback',
                removal='follow callback deletes FF when D445==0; otherwise tracks irrespective of water flag; keepalive bit1',
                tail='frame1 calls9555 immediately: req28, flag3 bit0, flag4=0, vy0, D3750, clear floor bit1, sound96, camera lower bound=cameraY, deleteFF'),
            death='countdown tail bypasses hurt/lost-ring helper; neither updater nor tail changes ring counter; no-ring death setter4984 is separate',
            freeze='loops0C/0D/13, air25, clear20, death1F/28 and stationary spindash charge0F do not call water updater; count calls, preserve stale water flag'),
        bubbles=dict(type=12,table_bank=12,table_cpu=0x9CAC,placements=[dict(act='aqz1',x=768,y=686,parameter=0),dict(act='aqz2',x=2496,y=942,parameter=0)],
            states=dict(emitter=1,small=2,large=3),parameters={'0':'mapped emitter ->1','1':'small emitted ->2','2':'large emitted ->3','3':'player breath ->2; initializer overrides XY to playerX/playerY-16'},
            initialization='base8E/8E; bit7 flags3 prevents shared contact from damaging player; vy=-192 for every parameter including inert emitter',
            emitter='128/120/112 update records, spawn1/1/2 after each; 360-update cycle; original scheduler births at130,250,362 then490,610,722 from zero object',
            child_allocator='command4 uses5EE1 poolD700..D980 eleven slots; failed command advances to next record without retry; player breath uses distinct16-slot5E9C',
            motion='vy=-192; vx integrates +/-4 acceleration selected by D12F bit4 (0 -> -4,1 ->+4); no gravity/cap; original0338 24-bit XY integration',
            termination='callbacks test asleep bit6 every update; on D2E2&3 !=0 test objectY - extentY < D450 and deleteFE; equality survives; mapped emitter inert callback does not test waterline',
            large='state3 frames1/2 each16 then frame3 repeating224; only frame3 callback9D39 checks contact on D12F&3 !=0 (3 of4 phases)',
            contact='shared6328 closed overlap: ordinary Sonic8x24 plus bubble8x16 gives abs(dx)<=16 and dy=-16..24; flags3 bit7 allows even hurt player; callback request25 and deleteFE',
            air='only qualifying large callback; no parameter/frame guard inside callback (script reachability supplies restriction); soundAE and coarse reset happen in player state25 next update, fine preserved',
            removal='FE -> next object pass marksFF through626D -> following pass5EF8 clears64 bytes and placement token; dynamic bubbles have no token'),
        splash=dict(type=14,table_bank=12,table_cpu=0x9F8B,states=[0,1],creator='dry->submerged edge only from4BC0',
            initialization='playerX, WORLD D450; baseA4; +$04 bit0; request1',frames=[1,2,3],durations=[4,4,4],sound=175,
            ending='frame0 delete callback0362 immediately on next record; original calls frames at2,6,10,FF at14, cleared at15',
            contact=False,movement=False,exit_spawn=False,failure='silent16-slot drop; D443 still set; no later retry while submerged'),
        player_states=states,
        shared=dict(jump='45ED/3901: dry -1088 / water -832, fixed-point; jump hold updates same launch for first13 held calls; existing latch/attack/floor rules unchanged',
            maximum='D373 is not halved: ordinary4, roll6, spindash7, Rocket7; actual setters/terrain may supply another cap',
            control='4141 selects441D/449D water vs429D/431D dry; two signed direction entries per state; opposing acceleration signs are significant; acceleration doubles when abs(vx)<128; neutral439D and slope459D unchanged',
            forced_floor='D522 bit1 branch overrides Y speed after gravity to7, or9 when D369=0A/0C; overrides underwater cap4; grounded flags3 bit0 clear bypasses gravity',
            walk='underwater37A4 skips run transition47A9 and strip-fall test4663; crouch3713 bypasses Sonic jump-fly selector473C; spin dash release remains +/-7',
            springs='terrain/mapped launch setters have no D443 branch: accepted launch values unchanged; subsequent spring0B uses water gravity12/cap4 and horizontal tables',
            terrain='booster1A, crumble0C/type13, breakables, collision handlers and ring probe do not read D443; no new water terrain contract; loops use route tables and pause updater',
            hurt='same494F initial launch and recoverable scatter; hurt state1E callback03AA ->3A71 ->3FEF continues water updater and uses4097 gravity24/cap4; damage/scatter initial launch remains unchanged',
            effects='5 every3 and boss-paused;11 every8 and not boss-paused; graphics copies unchanged, neither writes CRAM/priority; common raster palette changes displayed colors including affected sprites/terrain; no refraction or scanline horizontal-scroll change in0652'),
        scheduling=['camera/background4C90','player animation64FA','player callback: water+air4B46 where called','screen death401A','control4141','X402A','Y4097','terrain floor/sides/ceiling/rings690B','damage48BC','reward4A74','objects5DD1 sequential19 slots: animation then callback then lifecycle','mapped creation bank1C:8000 every fourth D2E2 pass','renderer220E/1027 moved into main split path16EF; normal renderer in vblank05B0','effects bank1D:8000 in eligible vblank; line IRQ interrupts copy fixed CRAM and next guarded vblank restores palette'],
        viewport=dict(waterline='WORLD(568/788)',raster='EDGE(TOP, waterline-cameraY), canonical active192 lines',strip_x='EDGE(LEFT, table offset8..248), two phases covering256px',
            bubble_contact='PLAYER_DIST closed overlap; never widen',countdown='PLAYER_DIST(0,-34/-40)',camera_death='LOCKED_CAMERA lower bound = current cameraY at countdown tail; state28 uses EDGE(TOP,+216)'))

def build(r):
    assert F.digest(r)==L.ROM_SHA256
    return dict(format=1,rom_sha256=L.ROM_SHA256,research_base=BASE,evidence='byte-verified assembly and controlled original routines; whole-game checks stored separately',
        tool_sha256=F.digest(Path(__file__).read_text(encoding='utf-8').encode()),
        source_regions={k:F.source(r,*v) for k,v in dict(water=(0,0x4B46,0x4C02),controller_bubble_effect=(12,0x9CAC,0x9FC9),countdown=(30,0x94C6,0x958B),player=(0,0x361D,0x4B46),raster_irq=(0,0x0652,0x06A8),raster_setup=(0,0x1C9B,0x1CD3),creator=(0,0x2A2E,0x2A4F),allocator=(0,0x5E9C,0x5F17)).items()},
        waterlines=dict(aqz1=568,aqz2=788,aqz3=None,initial_creator=768,classification='WORLD'),
        crossing_vectors=crossings(r),timer_vectors=timers(r),physics=physics(r),raster=raster(r),objects=object_vectors(r),lifecycle=lifecycle(r),contracts=contracts(r),
        rocket_shared=dict(reward=Shoes.reward_fixture(r),vertical=Shoes.vertical_sweep(r),termination=Shoes.rocket_termination_fixtures(r),proof='same fixed-bank state11 / reward selector04; D443 selects water acceleration table; no AQZ-specific Rocket callback'),
        unresolved=[])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();value=build(L.load_rom(a.rom))
    if a.check:assert OUTPUT.read_text(encoding='utf-8')==F.dumps(value)
    else:OUTPUT.write_text(F.dumps(value),encoding='utf-8')
    print('AQZ water original-routine vectors',len(value['crossing_vectors']),len(value['timer_vectors']),len(value['physics']['vertical']),len(value['objects']['bubble_contact']))

if __name__=='__main__':main()

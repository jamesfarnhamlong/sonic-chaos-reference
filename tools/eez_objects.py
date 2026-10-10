"""Zone5 numeric families36/37/38/39: source contracts and controlled sweeps."""
import argparse,itertools
import eez_foundation as F
import level_package as L
import mghz_object_census as C
import rom as R
from oracle import Oracle
S=0xD700

def build(r):
    o=Oracle(r);o.bank(2,30);o.cpu.ix=S;m=o.mem
    checks={};vectors={}
    def eq(k,a,b):
        checks[k]=checks.get(k,0)+1;assert a==b,(k,a,b)
    def reset(t):
        m[S:S+64]=bytes(64);m[S]=t;m[S+1]=m[S+2]=2
        m[0xD503]=0;m[0xD3B0]=0;m[0xD297]=5;m[0xD298]=0
        m[0xD52C]=8;m[0xD52D]=24;o.position(5000,0)
    rows=[]
    for param,x in itertools.product(range(256),(0,256,65535)):
        reset(54);m[S+63]=param;o.word(S+17,x);o.call(0x8DF6)
        eq('36_endpoint',o.word(S+52),(x+param*16)&65535);eq('36_request',m[S+2],1)
    for sleep,x,player,vx in itertools.product((0,64),range(999,1018),range(998,1019),(-256,256)):
        reset(54);m[S+4]=sleep;o.word(S+17,x);o.word(S+58,1000);o.word(S+52,1016);o.word(S+22,vx);o.position(player,0)
        o.call(0x8E39)
        stop=(x<=1000 or player>=x) if vx<0 else (x>=1016 or player<=x)
        clamp=1000 if vx<0 and x<=1000 else 1016 if vx>0 and x>=1016 else x
        eq('36_stop',m[S+2],3 if stop else 2)
        eq('36_move',o.word(S+17),clamp if stop else (x+(-1 if vx<0 else 1))&65535)
        eq('36_acceleration',R.s16(o.word(S+22)),vx if stop else vx+(-16 if vx<0 else 16))
    for param in range(256):
        reset(56);m[S+63]=param;o.call(0x8FC5)
        eq('38_init_state',m[S+2],4 if param==1 else 5 if param==2 else 1)
        eq('38_init_counter',m[S+30],32)
        if param not in (1,2):eq('38_init_velocity',[o.word(S+22),o.word(S+24)],[64,0])
        reset(57);m[S+63]=param;o.word(S+17,1200);o.call(0x9107)
        eq('39_init_velocity',[R.s16(o.word(S+22)),R.s16(o.word(S+24))],[-512,-1408] if param==0 else [-384,-1024])
        eq('39_origin',o.word(S+58),1200)
    rows=[]
    for countdown,turn in itertools.product(range(256),range(4)):
        reset(56);m[S+31]=countdown;m[S+30]=turn;o.word(S+17,1000);o.word(S+20,1000);o.word(S+22,64)
        o.call(0x9029)
        eq('38_wait_state',m[S+2],3 if countdown==0 else 2)
        eq('38_wait_counter',m[S+31],(countdown-1)&255)
        if countdown:eq('38_turn_counter',m[S+30],2 if turn==0 else turn-1)
        if countdown in (0,1,32):rows.append([countdown,turn,m[S+2],m[S+30],m[S+31],R.s16(o.word(S+22))])
    vectors['38_countdowns']=rows
    rows=[]
    for act,x,y in itertools.product(range(3),(0,31,32,65535),(0,31,32,1000)):
        reset(55);m[0xD298]=act;m[S+63]=1;o.word(S+52,x);o.word(S+54,y);o.call(0x8ED0)
        ex=(x&0xFF00)|((x&224)+15);aligned=(y&0xFF00)|((y&224)+24)
        ey=(aligned+(-88 if act==1 else -120))&65535
        eq('37_terrain_spawn',[o.word(S+17),o.word(S+20),o.word(S+24),m[S+8],m[S+2]],[ex,ey,1088,124,3])
        rows.append([act,x,y,ex,ey])
    vectors['37_terrain_spawn']=rows
    # Direct non-positioned terrain allocation must not be confused with
    # command4 child initialization: parameter distinguishes the two paths.
    out=dict(rom_sha256=L.ROM_SHA256,checks=checks,assertions=sum(checks.values()),vectors=vectors,
        scripts={f'0x{t:02X}':C.public_script(C.state_scripts(r,t)) for t in (54,55,56,57)},
        regions=[F.A.source(r,30,0x8DA3,0x90E7),F.A.source(r,30,0x90E7,0x9190)],
        contracts=dict(
            type36=dict(initial='8DF6 stores WORLD originX+parameter*16 in34/35; requests1; canonical record origin retained in3A/3B.',
                state1='8E1E asleep bit6 returns; selects VX -1 if objectX>=playerX, +1 otherwise; request2.',
                state2='8E39 does not check sleep; compares WORLD unsigned X with left origin or right origin+parameter16, clamps if crossed. Player crossing/equality in approach direction also requests3. Otherwise moves using current VX then increases magnitude by1/16. No contact/attack helper.',
                state3='script flashes frames6/7 for8,8,4,4,2,2,1,1 updates; command4 allocates37 at0,+8 parameter0; then frame6 for32,request1. No badnik reward/defeat path.',
                lifetime='generic mapped lifecycle; state1 sleeps, state2 still executes while asleep; command4 allocation uses canonical11-slot pool, no guaranteed child on exhaustion.'),
            type37=dict(initial='parameter0 child: state1,VY+2.5. Nonzero terrain path: base7C,state3, WORLD X floor-cellX aligned32+15; WORLD Y cellY aligned32+24 minus88 in act1,minus120 otherwise; VY+4.25.',
                state1='8F23 sleep ->request2 without movement/contact. Awake forced hurt630B before move then solid/oneway anchor probe614E; empty retains1, solid requests2.',
                state2='frames2/3/4/5 for6 each, then frame0 delete8F3E; no pickup or score.',
                state3='8F43 moves first; compare WORLD cellY-24 versus objectY; <= boundary applies forced hurt, otherwise request2. No extra attack defeat.',
                dependency='surface0B replaces block B1 withB2 before allocating type37 parameter1, stores probed cellX/Y in34..37 and D35C/D35E. terrain-effects.json tests exhaustion; no restoration callback exists, replacement persists until map reload.'),
            type38=dict(initial='8FC5 counter30=32; parameter1 ->state4 (script spawns38 parameter2), parameter2 ->state5; all other values state1,VX+0.25,VY0.',
                state1='forced hurt630B first, then strict |dx|<32 and |dy|<32. Outside: move and decrement30; underflow resets32/reversesVX. Inside: state2,counter30=2,counter31=32, no move.',
                state2='forced hurt first; counter31 subtract1, borrow requests3 without movement. Otherwise move; counter30 subtract1,borrow resets2/reversesVX. 32 movement calls followed by transition on33rd.',
                state3='command4 emits39 parameter0 and1; frame1/2 duration2 then callback5F54 conversion to defeated/reward chain. This is autonomous self-conversion, not attack-bit defeat.',
                state4='spawns38 parameter2, invisible frame0/128 forever. Pool capacity may therefore affect repeat allocation each script restart.',
                state5='gravity+1/16 before move, anchor solid/oneway test; landing ->state6,VX-0.75.',
                state6='forced hurt and same strict32 trigger. Otherwise test anchor block44/45/46; these permit move, others request2 with counters2/32 and VX+0.25,VY0.',
                lifetime='generic mapped/child scheduling; parameter1 is a producer, no explicit keepalive script flag.'),
            type39=dict(initial='9107 state1; parameter0 VX-2,VY-5.5; nonzero VX-1.5,VY-4; save originX, counter30=0.',
                state1='forced hurt before9178 WORLD Y > cameraY+192 request3; when30nonzero reflectX around origin; move; gravity+0.25; request2 unconditionally.',
                state2and3='forced hurt,9178 threshold, reflectX, counter30=FF, request1. Threshold-request3 is overwritten by the callback tail; unused9173 delete routine must not be invented as the actual callback.',
                lifetime='generic lifecycle remains deletion authority; explicit WORLD-vs-camera EDGE(BOTTOM) comparison does not itself delete; no lifetime timer, no attack defeat.'),
            reuse='09/10/18/26 consume shared contracts;28 state13 zone4act1 override does not apply zone5. Parameters05/8B require their shared state13 route rather than treating8B as AQZ14;2C parameters00/01 require existing GPZ contract.'))
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();v=build(L.load_rom(a.rom))
    (F.OUT/'objects-36-39.json').write_text(F.dumps(v),encoding='utf-8');print(v['checks'],v['assertions'])

if __name__=='__main__':main()

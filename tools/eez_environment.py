"""Controlled zone5 environment gates; entry transport, conveyor, type3A.

Transport state21 routing and type37 cell restoration remain separate dependencies.
"""
import argparse,itertools
import eez_foundation as F
import level_package as L
from oracle import Oracle

def build(r):
    out=dict(rom_sha256=L.ROM_SHA256,evidence='byte-verified assembly and controlled original routines',checks={},vectors={})
    def eq(name,a,b):
        out['checks'][name]=out['checks'].get(name,0)+1
        assert a==b,(name,a,b)
    o=Oracle(r);m=o.mem;o.cpu.ix=0xD500
    vectors=[]
    for zone,block,latch,free in itertools.product(range(6),(10,11,12),(0,1,255),range(17)):
        m[0xD540:0xD940]=bytes([1])*1024
        if free<16:m[0xD540+free*64]=0
        m[0xD297]=zone;m[0xD36B]=block;m[0xD3F7]=latch
        o.call(0x6A5D)
        hit=zone==5 and block==11 and latch==0 and free<16
        eq('floor01_allocator',sum(m[b]==58 for b in range(0xD540,0xD940,64)),int(hit))
        if hit:eq('floor01_parameter',m[0xD540+free*64+63],0)
        vectors.append([zone,block,latch,free,int(hit)])
    out['vectors']['floor01']=vectors
    vectors=[]
    for floor,x,frac in itertools.product((0,1,2,3,128,255),(0,1,255,256,32768,65535),(0,1,255)):
        m[0xD522]=floor;o.position(x,100);m[0xD510]=frac;o.word(0xD516,321)
        o.call(0x6B56);expected=(x-1)&65535 if floor&2 else x
        eq('conveyor_x',o.word(0xD511),expected);eq('conveyor_fraction',m[0xD510],frac);eq('conveyor_velocity',o.word(0xD516),321)
        vectors.append([floor,x,frac,o.word(0xD511)])
    out['vectors']['conveyor']=vectors
    vectors=[]
    for block,st,vx,vy,y in itertools.product((0x74,0x7E,0x7F,0x80,0x81,0x82,0x83),(5,24,33),(-1,0,1),(-1,0,1),(15,16,31,32)):
        m[0xD353]=block;m[0xD36B]=block;m[0xD36D]=170
        m[0xD501]=m[0xD502]=st;m[0xD503]=0;m[0xD522]=2;m[0xDE04]=0
        o.position(100,y);o.word(0xD516,vx);o.word(0xD518,vy)
        o.call(0x6D43)
        fire=st!=33 and ((block==0x7F and vy>=0) or (block==0x81 and vx>=0 and y%32<16) or (block==0x82 and y%32<16 and (st==24 or vx<=0)))
        eq('transport_request',m[0xD502],33 if fire else st)
        eq('transport_sound',m[0xDE04],165 if fire else 0)
        ex,ey=(0,1536) if fire and block==0x7F else (1536,0) if fire and block==0x81 else (-1536,0) if fire else (vx,vy)
        eq('transport_velocity',[o.word(0xD516),o.word(0xD518)],[ex&65535,ey&65535])
        eq('transport_floor',m[0xD522],2 if block==0x80 else 0)
        eq('transport_flag',m[0xD503]&1,0 if block==0x80 else 1)
        vectors.append([block,st,vx,vy,y,m[0xD502],o.word(0xD516),o.word(0xD518)])
    out['vectors']['transport_entry']=vectors
    o.bank(2,30);o.cpu.ix=0xD700
    vectors=[]
    for x,y in itertools.product((0,7,8,255,256,65535),(0,31,32,65503,65535)):
        o.position(x,y);o.call(0x91BA)
        # Y alignment deliberately discards low-byte carry after ADD 6.
        raw=(y+32)&65535;expected=(raw&0xFF00)|(((raw&255)&224)+6)
        eq('3a_anchor',[o.word(0xD711),o.word(0xD714)],[(x&0xFFF8)|3,expected])
        vectors.append([x,y,o.word(0xD711),o.word(0xD714)])
    out['vectors']['3a_anchor']=vectors
    for requested,block in itertools.product(range(44),(10,11,12)):
        m[0xD700]=58;m[0xD3F7]=255;m[0xD502]=requested;m[0xD36B]=block
        o.call(0x91DB);remove=requested==23 or block!=11
        eq('3a_lifecycle',[m[0xD700],m[0xD3F7]],[255,0] if remove else [58,255])
    out['contracts']=dict(
        floor01='$6A5D: zone==5, floor-probed block D36B==0B, D3F7==0 -> 16-slot allocator 5E9C type3A parameter0. No explicit floor-bit gate. Pool full returns without allocation.',
        conveyor='$6B56 surface0E: floor bit1 required; WORLD X -= 1 including 24-bit carry; preserves X velocity and fractional byte. Player terrain pass, not camera-relative.',
        transport_entry='$6D43 surface13: block80 immediate RET. Otherwise copy D36B to D36D, clear floorbit1,set flag3bit0. 7F falling/nonrising launches down; 81 nonnegativeVX and Ymod32<16 launches right; 82 Ymod32<16 and (state18 or VX<=0) launches left. Current21 blocks launch; soundA5, state21, speed6.0 along axis, other speed0. Block80 rising branch is unreachable from routine entry.',
        effect3a='$1E:91A8 sets D3F7=FF,bases92/92,request1. 91BA aligns player WORLD X to8 +3 and WORLD Y+32 to32 +6; animation alternates frames1/0 for2 updates each. 91DB deletes/clears latch when requested player17 OR floor-probed block !=0B. Gate is set on initializer, not allocation.',
        remaining='surface0B replacement/type37; state21 full transport graph; terrain/player dispatch ordering need whole-game closure. These contracts alone do not close A2.')
    out['regions']=[F.A.source(r,0,0x6A5D,0x6A75),F.A.source(r,0,0x6B56,0x6B78),F.A.source(r,0,0x6D43,0x6E56),F.A.source(r,30,0x9190,0x91F1)]
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--check',action='store_true');args=p.parse_args()
    value=build(L.load_rom(args.rom));path=F.OUT/'environment-gates.json'
    if args.check:assert path.read_text(encoding='utf-8')==F.dumps(value)
    else:path.write_text(F.dumps(value),encoding='utf-8')
    print(value['checks'],sum(value['checks'].values()))

if __name__=='__main__':main()

"""Surface0B allocation/replacement and original effect contracts."""
import argparse,itertools
import eez_foundation as F
import level_package as L
import mghz_foundation as M
from oracle import Oracle

def build(r):
    o=Oracle(r);m=o.mem;o.cpu.ix=0xD500;rows=[];checks=0
    for floor,free in itertools.product((0,1,2,3),range(17)):
        o.bank(2,30);m[0xD12B]=30;m[0xD162]=20;o.word(0xD164,0xA4E0)
        m[0xD540:0xD940]=bytes([1])*1024
        if free<16:m[0xD540+free*64]=0
        m[0xC100]=177;o.word(0xD354,0xC100);o.word(0xD358,608);o.word(0xD35A,736)
        m[0xD522]=floor;m[0xD523]=2;m[0xD501]=m[0xD502]=5
        o.call(0x6BAA)
        hit=bool(floor&2);count=sum(m[b]==55 for b in range(0xD540,0xD940,64))
        assert count==int(hit and free<16);assert m[0xC100]==(178 if hit else 177);checks+=2
        if hit:
            dest=0xD540+free*64
            assert [o.word(dest+52),o.word(dest+54),o.word(0xD35C),o.word(0xD35E)]==[608,736,608,736];checks+=1
            if free<16:assert m[dest+63]==1;checks+=1
        rows.append([floor,free,m[0xC100],count])
    effects={}
    for eid in (5,6,8,13):
        pc=L.u16(r,M.bank_file(29,M.EFFECT_JUMP_TABLE)+eid*2)
        effects[str(eid)]=dict(cpu=pc,events=F.S.run_effect(r,eid,384,zone=5,bg_palette=26,sprite_palette=11),
            paused=F.S.run_effect(r,eid,384,zone=5,d44e=6,bg_palette=26,sprite_palette=11))
    return dict(rom_sha256=L.ROM_SHA256,checks=checks,vectors=rows,effects=effects,
        source=[F.A.source(r,0,0x6BAA,0x6BFD),F.A.source(r,29,0x8259,0x82F7),F.A.source(r,29,0x8442,0x8471)],
        contracts=dict(
            surface0b='floorbit1 required. Replace probed WORLD cellB1->B2 before 16-slot allocation of37 parameter1. Store cellX/Y D35C/D35E and destination34..37. Exhaustion still mutates terrain and writes coordinates through IY=D940; do not create guaranteed child or restore terrain on failure.',
            restoration='37 scripts/callbacks8ED0..8F60 contain no terrain restoration call. B1->B2 persists until map reload; retain cached replacement mapping. Generic object deletion does not restore it.',
            effect5='shared dispatcher81BF;zone5 chooses64-byte paired-frame stream toVRAM3020 every3calls;bossactive pauses. This destination/source differs from SEZ single tile158; use zone-aware data.',
            effect6='8259 every30calls,alternateindex2,paired96-byte copies8EFD/8F5D swap VRAM2A80/2FC0. Bossactive pauses counter and copies.',
            effect8='8442 every8calls,12 palettepairs at1D:9961 toD480/D481 (background indices14/15),dirtyFF. Does not test bossactive; same palette animation continues.',
            effect13='82BC every8calls,indexmod4,table82EF ->96bytes toVRAM3760. Bossactive pauses; copies8FBD/901D/907D/90DD in table order. No engine-added frames.',
            dispatch='shared effect dispatcher requires D492zero; eight-byte slots. Ring uploader is separate every8globalD12Fupdates. WORLD terrain and original VRAM/palette timing, no widescreen scaling.'))

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();v=build(L.load_rom(a.rom))
    (F.OUT/'terrain-effects.json').write_text(F.dumps(v),encoding='utf-8');print('terrain assertions',v['checks'])

if __name__=='__main__':main()

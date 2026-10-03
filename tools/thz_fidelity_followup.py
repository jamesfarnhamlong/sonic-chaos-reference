"""Research-only THZ visual and update-path diagnostic. Generated art stays in build/."""
from pathlib import Path
import argparse, json, hashlib
import thz3_boss_support as b
import thz1_object_assets as a
import thz1_object_27 as o27
from thz1_background_registration import decode_rgba_png
from oracle import Oracle

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'reports/thz-fidelity-followup.json'

def bee(rom, out):
    vram, loads = a.build_vram(rom, a.load_json(a.GRAPHICS_MAP))
    frames = a.mapping_frame_pointers(rom, a.object_mapping(rom, 0x27)['mapping_cpu'])
    rows=[]; images=[]
    runtime=b.psc.Emu(rom)
    runtime_equal=bytes(runtime.s.vram[0x1540:0x1680])==vram[0x1540:0x1680]
    for index, ptr in enumerate(frames):
        f=a.parse_frame_record(rom,ptr)
        for mirror in (False, True):
            if not f['piece_count']: continue
            o=Oracle(rom);o.bank(2,15);o.cpu.ix=0xD700
            m=o.mem;m[0xD704]=16 if mirror else 0;m[0xD705]=f['piece_count']
            m[0xD708]=m[0xD709]=0xAA
            o.word(0xD728,f['coords_cpu']);o.word(0xD72A,ptr+5)
            o.word(0xD71A,128);o.word(0xD71C,80)
            o.word(0xD36F,0xDC00);o.word(0xD371,0xDD00)
            o.call(0x226A);o.call(0x22B6)
            pieces=[]
            for i in range(f['piece_count']):
                tile=m[0xDD01+i*2]
                pieces.append(dict(x=m[0xDD00+i*2]-128,y=m[0xDC00+i]-80,
                                   sat_tile=tile,pattern=tile&254))
            rows.append(dict(frame=index,mirror=mirror,record=a.serialise_frame(f),sat=pieces))
            expected=[dict(x=(-p['relative_x']-8 if mirror else p['relative_x']),
                           y=p['relative_y'],sat_tile=(0xAA+p['tile_offset'])&255,
                           pattern=(0xAA+p['tile_offset'])&254) for p in f['pieces']]
            assert pieces==expected, 'decoded mapping differs from original SAT renderer'
            # Independent reconstruction from the actual original renderer's SAT.
            im=bytearray(64*48*4)
            pal=a.thz1_sprite_palette(rom)
            for p in pieces:  # earlier SAT sprite wins overlaps
                pix=a.tile_pixels(vram,p['pattern'])+a.tile_pixels(vram,p['pattern']+1)
                for y,line in enumerate(pix):
                    for x,c in enumerate(line):
                        xx,yy=p['x']+32+x,p['y']+24+y+18
                        pos=(yy*64+xx)*4
                        if c and 0<=xx<64 and 0<=yy<48 and not im[pos+3]:
                            im[pos:pos+4]=bytes(pal[c])
            scaled=bytearray(256*192*4)
            for yy in range(192):
                for xx in range(256):
                    pos=(yy//4*64+xx//4)*4
                    scaled[(yy*256+xx)*4:(yy*256+xx)*4+4]=im[pos:pos+4]
            a.write_rgba_png(out/f'bee-{index}-{int(mirror)}.png',256,192,scaled)
            images.append((index,mirror,bytes(im)))
    # Read-only comparison to the existing imported assets and draw scale.
    poc=ROOT.parent/'SonicChaos_POC_thz1_cleanup'
    spr=poc/'sprites/SPR_chaos_object_27'
    yy=json.loads((spr/'SPR_chaos_object_27.yy').read_text())
    comparisons=[]; sheet=bytearray(bytes((70,90,110,255))* (192*96))
    for index in (1,2):
        png=spr/(yy['frames'][index-1]['name']+'.png')
        w,h,rgba=decode_rgba_png(png.read_bytes()); dst=bytearray(64*48*4)
        decoded=a.parse_frame_record(rom,frames[index])
        pw,ph,preview,_=a.render_frame(vram,decoded,0xAA,scale=1,margin=4,palette=a.thz1_sprite_palette(rom))
        assert (pw,ph)==(w,h)
        preview_diff=sum(rgba[i:i+4]!=preview[i:i+4] for i in range(0,len(rgba),4)
                         if rgba[i+3] or preview[i+3])
        for y in range(h):
            for x in range(w):
                xx=32+yy['sequence']['xorigin']-x-1
                yypos=24+y-yy['sequence']['yorigin']+18
                if 0<=xx<64 and 0<=yypos<48:
                    dst[(yypos*64+xx)*4:(yypos*64+xx)*4+4]=rgba[(y*w+x)*4:(y*w+x)*4+4]
        normal=next(im for i,mi,im in images if i==index and not mi)
        canonical=next(im for i,mi,im in images if i==index and mi)
        def differences(im):
            return sum(dst[i:i+4]!=im[i:i+4] for i in range(0,len(im),4)
                       if dst[i+3] or im[i+3])
        comparisons.append(dict(frame=index,poc_png_sha256=b.sha(png.read_bytes()),
                                poc_import_vs_research_normal_pixels=preview_diff,
                                poc_vs_original_pixels=differences(canonical)))
        # Columns: Research normal preview, actual POC draw, original mirrored SAT.
        for col,im in enumerate((normal,bytes(dst),canonical)):
            for y in range(48):
                for x in range(64):
                    src=(y*64+x)*4; pos=(((index-1)*48+y)*192+col*64+x)*4
                    if im[src+3]:sheet[pos:pos+4]=im[src:src+4]
    scaled=bytearray(768*384*4)
    for y in range(384):
        for x in range(768):
            src=(y//4*192+x//4)*4;pos=(y*768+x)*4
            scaled[pos:pos+4]=sheet[src:src+4]
    a.write_rgba_png(out/'bee-contact-sheet.png',768,384,scaled)
    return dict(loads=loads,rows=rows,runtime_vram_equal=runtime_equal,
                animation=o27.animation_summary(rom),
                remap_is_bit_reversal=all(rom[0x100+i]==int(f'{i:08b}'[::-1],2) for i in range(256)),
                sprite_palette_cpu=0xB6AD,sprite_palette_file=0x3B6AD,
                palette_values=list(rom[0x3B6AD:0x3B6BD]),
                runtime_vram_sha256=b.sha(bytes(runtime.s.vram[0x1540:0x1680])),
                runtime_registers=list(runtime.s.reg),poc_comparison=comparisons,
                sheet_columns=['Research normal preview','POC image_xscale=-1','Original mirrored SAT'])

def rec(t):
    m,u=t.m,t.u
    z=dict(current=m[0xD501],requested=m[0xD502],flags=m[0xD503],floor=m[0xD522],
           contacts=m[0xD523],x=u(0xD511),y=u(0xD514),vx=b.s16(u(0xD516)),vy=b.s16(u(0xD518)))
    boss=t.boss()
    if boss:z.update(boss_x=u(boss+0x11),boss_y=u(boss+0x14),boss_state=m[boss+1],bits=m[boss+0x21]&15)
    return z

def boss_run(rom, mode):
    t=b.Thz3(rom);s,m,u=t.s,t.m,t.u
    events=[];start=[None]; hit=[False]
    def hook(stage):
        def h(machine):
            if start[0] is None:return
            boss_stages=('before_8105','at_8105','after_8105','helper','after_helper')
            if stage in boss_stages and (s.slot[2]!=30 or s.cpu.ix!=t.boss()):return
            if stage not in boss_stages and s.cpu.ix!=0xD500:return
            events.append(dict(update=t.al.count-1-start[0],stage=stage,**rec(t)))
            if stage=='after_8105':hit[0]=True
        return h
    for pc,label in ((0x3FEF,'player_update'),(0x4097,'vertical'),(0x690B,'terrain'),(0x64CB,'merge'),
                     (0x99AE,'helper'),(0x8105,'at_8105'),(0x99DD,'before_8105'),(0x99E0,'after_8105'),
                     (0x480C,'top_setter'),(0x4810,'top_setter_guard')):
        s.add_pc_hook(pc,hook(label))
    def driver(n):
        boss=t.boss()
        if not boss:return
        if start[0] is None:
            if m[boss+1] in (3,18):
                s.w16(0xD511,1696);s.w16(0xD514,238);s.w16(0xD516,0);s.w16(0xD518,0)
            if m[boss+1]==6:
                start[0]=n
                dx,y,vx,vy,state,flags,floor={
                    'roll':(-70,238,1536,0,9,2,2),
                    'descending':(-36,208,1536,768,10,3,0),
                    'rising':(-36,208,1536,-768,10,3,0),
                    'top':(0,190,0,0,10,3,0),
                }[mode]
                s.w16(0xD511,u(boss+0x11)+dx);s.w16(0xD514,y)
                s.w16(0xD516,vx);s.w16(0xD518,vy)
                m[0xD501]=m[0xD502]=state;m[0xD503]=flags;m[0xD522]=floor
                m[0xD520]=m[0xD521]=m[0xD523]=0;m[0xD29A]=0x50
        # No player/velocity writes after the single aligned approach setup.
    rows=t.al.run(driver,lambda:rec(t),310,pad=lambda n:b.psc.PAD['RIGHT'] if n<75 else 0,restore=False)
    contact=next(e['update'] for e in events if e['stage'] in ('at_8105','top_setter'))
    events=[e for e in events if e['update']<=contact+3 or e['stage'] in ('at_8105','after_8105','top_setter')]
    return dict(mode=mode,start=start[0],events=events,rows=rows[start[0]:] if start[0] is not None else [])

def grounded_sweep(rom):
    """Every signed high byte plus low-byte edges at the next vertical updater."""
    o=Oracle(rom);m=o.mem;cases=0;bad=[]
    for state in (9,27):
        for flags in (2,3):
            for modifier in (0,10,12):
                for hi in range(256):
                    for lo in (0,255):
                        m[0xD501]=state;m[0xD503]=flags;m[0xD522]=2
                        m[0xD3C0]=0;m[0xD443]=0;m[0xD369]=modifier
                        o.position(1800,238);m[0xD513]=0
                        o.word(0xD518,(hi<<8)|lo);o.call(0x4097)
                        expected=2304 if modifier in (10,12) else 1792
                        cases+=1
                        if o.word(0xD518)!=expected:bad.append([state,flags,modifier,hi,lo,o.word(0xD518)])
    return dict(cases=cases,mismatches=bad,scope='Original $4097; floor bit set; all signed high bytes with low-byte 00/FF; states 9/27, grounded/airborne flags, modifiers 0/0A/0C; terrain projection not part of this isolated sweep.')

def flag_control(rom):
    rows=[]
    for flags,floor in ((2,2),(3,0)):
        o=Oracle(rom);m=o.mem;m[0xD501]=27;m[0xD503]=flags;m[0xD522]=floor
        m[0xD369]=m[0xD3C0]=m[0xD443]=0
        o.position(1869,238);m[0xD513]=0;o.word(0xD518,-1792)
        o.call(0x4097)
        rows.append(dict(flags=flags,floor=floor,vy_after=b.s16(o.word(0xD518)),y=o.word(0xD514)))
    return rows

def build(rom,out):
    b.check_rom(rom)
    r=dict(rom_sha256=b.sha(rom),research_only=True,poc_untouched=True,
           evidence='Decoded data; original renderer and movement routines; update-aligned original game in approximate SMS harness; read-only GameMaker comparison. Pending review, no canonical documentation changes.')
    r['bee']=bee(rom,out)
    r['boss']=[boss_run(rom,x) for x in ('roll','descending','rising','top')]
    r['grounded_sweep']=grounded_sweep(rom);r['flag_control']=flag_control(rom)
    regions=[('renderer',0,0x226A,0x2335),('vertical_update',1,0x4097,0x4141),
             ('floor_projection',1,0x6F61,0x6FBB),('rebound',30,0x8105,0x814D),
             ('boss_contact',30,0x99AE,0x9A09),('top_setter',1,0x480C,0x482D)]
    r['code_evidence']=[dict(name=n,bank=bank,cpu_start=lo,cpu_end=hi,
                             file_offset=b.rom_of(bank,lo),sha256=b.sha(rom[b.rom_of(bank,lo):b.rom_of(bank,lo)+hi-lo]))
                        for n,bank,lo,hi in regions]
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument('rom',type=Path);p.add_argument('--part',default='both',choices=('both','bee','boss'))
    p.add_argument('--check',action='store_true');p.add_argument('--metadata',action='store_true');args=p.parse_args()
    rom=args.rom.read_bytes();b.check_rom(rom)
    out=ROOT/'build/thz-fidelity-followup';out.mkdir(parents=True,exist_ok=True)
    r=dict(rom_sha256=hashlib.sha256(rom).hexdigest())
    if args.part=='both':r=build(rom,out)
    elif args.part=='bee':r['bee']=bee(rom,out)
    elif args.part=='boss':
        r['boss']=[boss_run(rom,x) for x in ('roll','descending','rising','top')]
        r['grounded_sweep']=grounded_sweep(rom)
    (out/f'{args.part}.json').write_text(json.dumps(r,indent=2)+'\n')
    if args.check:
        assert args.part=='both'
        assert r==json.loads(OUTPUT.read_text()), 'report replay differs'
    if args.metadata:
        assert args.part=='both'
        OUTPUT.write_text(json.dumps(r,indent=2)+'\n')
    print(out)
if __name__=='__main__':main()

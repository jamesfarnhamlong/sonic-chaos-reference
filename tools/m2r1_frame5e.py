"""Narrow Tails state20 investigation. Private ROM input, metadata-only output.

Original code executes in the repository's approximate SMS harness. Forced RAM
cases and arrival fixtures are labelled; no natural full-stage claim.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import rom as R
import g2e_score as G
import u5a_opening as O
import object_50 as B50
from oracle import Oracle
from g0_rig import Session

def sha(b):
    return hashlib.sha256(b).hexdigest()

def static(rom):
    out = {'rom_sha256': R.SHA256, 'source': []}
    for bank, start, end in [(12,0x839E,0x840F),(12,0x8EE1,0x8F2C),(12,0x8F3C,0x8F45),
                              (0,0x6562,0x65AF),(0,0x67A1,0x67C1),(0,0x361D,0x3657),
                              (0,0x4892,0x48A7),(0,0x0D15,0x0D45),(0,0x220E,0x226A),
                              (0,0x0785,0x0796),(12,0xAB8C,0xABA0),(30,0x81BD,0x8212),
                              (0,0x64CB,0x64F0),(0,0x60FB,0x613C)]:
        off = start if start < 0x8000 else bank*16384 + start-0x8000
        out['source'].append({'bank':bank,'start':start,'end':end,
                              'sha256':sha(rom[off:off+end-start]),'instructions':G.disasm(rom,bank,start,end)})
    out['mapping'] = []
    for char, base in [(1,0x80C8),(2,0x85BF)]:
        addr = base + 2*0x5E
        ptr = R.u16(rom,15*16384+addr-0x8000)
        out['mapping'].append({'character':char,'table_bank':15,'table_cpu':base,'frame':94,
                               'entry_cpu':addr,'pointer_cpu':ptr,
                               'pointer_effective_rom_offset':ptr if ptr<0x400 else (ptr if ptr<0x8000 else 15*16384+ptr-0x8000)})
    out['tails_transfer_record']={'table_cpu':0x11CF,'frame':94,'entry_cpu':0x1347,
                                 'bank':rom[0x1347],'source_cpu':R.u16(rom,0x1348),
                                 'blocks64':rom[0x134A]}
    return out

def routines(rom):
    rows = []
    for char in (1,2):
        for contact in (0,1,2,4,8,12,16,255):
            o = Oracle(rom); o.bank(2,12); m=o.mem
            m[0xD500]=char; m[0xD501]=32; m[0xD502]=32
            o.word(0xD50E,0); m[0xD523]=contact; o.word(0xD516,0x400)
            o.call(0x64FA)
            row = {'character':char,'contact':contact,'frame':m[0xD506], 'duration':m[0xD507],
                   'mapping_count':m[0xD505], 'extent':[m[0xD52C],m[0xD52D]],
                   'piece_pointer':o.word(0xD528),'origin_pointer':o.word(0xD52A),
                   'callback':o.word(0xD50C),'script_pointer':o.word(0xD50E), 'selector_phase':m[0xD52F]}
            assert row['frame']==(94 if contact&12 else 2)
            assert row['callback']==0x83A6
            before = [m[0xD506],m[0xD507],o.word(0xD516)]
            o.bank(2,12);o.call(0x83A6)
            row['callback_result']={'frame_duration_vx_before':before,
                                    'x_after':o.word(0xD511),'vx_after':o.word(0xD516),
                                    'contact_after':m[0xD523],'requested':m[0xD502]}
            rows.append(row)
    return rows

def setter_controls(rom):
    rows=[]
    for act in (0,1,2):
        for contact in (2,6,10,14):
            o=Oracle(rom);m=o.mem;m[0xD500]=2;m[0xD522]=2;m[0xD523]=contact
            m[0xD298]=act;m[0xD502]=5;o.call(0x4892)
            rows.append({'act':act,'ground_background':m[0xD522],'contact_before':contact,
                         'contact_after':m[0xD523],'request':m[0xD502],'sound':m[0xDE04]})
            assert m[0xD523]==contact and m[0xD502]==32
    return rows

def hidden_controls(rom):
    rows=[]
    for flags in (0,8):
        o=Oracle(rom);o.bank(2,12);m=o.mem
        m[0xD500]=2;m[0xD501]=m[0xD502]=32;m[0xD523]=4;m[0xD504]=flags
        o.word(0xD50E,0);o.call(0x64FA)
        rows.append({'flags':flags,'frame':m[0xD506],'mapping_count':m[0xD505],
                     'piece_pointer':o.word(0xD528),'origin_pointer':o.word(0xD52A)})
        assert m[0xD506]==94 and m[0xD505]==(0 if flags&8 else 230)
    return rows

def boss_gate_controls(rom):
    rows=[]
    for floor in (0,2):
        for contact in (2,6,10,14):
            f=B50.Fixture(rom);f.create();f.m[0xD500]=2
            f.m[0xD502]=5;f.m[0xD522]=floor;f.m[0xD523]=contact
            f.call_bank(30,0x81BD)
            rows.append({'background':floor,'contact':contact,'request':f.m[0xD502],
                         'contact_after':f.m[0xD523], 'boss_type_after':f.r(0)})
            assert f.m[0xD502]==(32 if floor else 5)
            assert f.m[0xD523]==contact
    return rows

def capture_png(s, path):
    from PIL import Image
    rgb = s.render()[0]
    flat=bytes(v for row in rgb for c in row for v in c)
    im=Image.frombytes('RGB',(256,192),flat);im.save(path)
    return {'rgb_sha256':sha(flat),'png_sha256':sha(path.read_bytes())}

def run_case(rom, label, char=1, arrival=False, side=None, limit=1000, outdir=None, backtrack=False, act=0):
    ses=Session(rom)
    injected=[False]; rows=[]; pending={}; active=[False]; screenshots=[]; calls=[]; transfers=[]
    def engine(s):
        if s.cpu.ix!=0xD500:return
        if active[0] and side is not None and not injected[0]:
            injected[0]=True
            s._write(0xD501,32);s._write(0xD502,32);s.w16(0xD50E,0)
            s._write(0xD523,side)
        if s.mem[0xD502]==32:
            pending.clear();pending.update({'frame':s.frame,'phase':'engine',
               'cur':s.mem[0xD501],'req':s.mem[0xD502],'contact':s.mem[0xD523],
               'x':s.u16(0xD511),'y':s.u16(0xD514),'camx':s.u16(0xD174),
               'prior_frame':s.mem[0xD506],'prior_count':s.mem[0xD505]})
    ses.hook(0x64FA,engine)
    def mapread(s):
        if s.cpu.ix==0xD500 and s.mem[0xD502]==32:
            pending['mapping_read_cpu']=s.cpu.hl
            pending['mapping_read_bank_slots']=list(s.slot)
    ses.hook(0x657F,mapread)
    def after(s):
        if s.mem[0xD502]==32 and pending:
            r=dict(pending);r.update({'selected':s.mem[0xD506],'duration':s.mem[0xD507],
               'count':s.mem[0xD505],'piece_ptr':s.u16(0xD528),'origin_ptr':s.u16(0xD52A),
               'flags':s.mem[0xD504],'callback':s.u16(0xD50C)})
            rows.append(r)
    ses.hook(0x363F,after)
    def callback(s):
        if active[0] and s.slot[2]==12 and s.cpu.ix==0xD500 and s.mem[0xD501]==32:
            calls.append({'frame':s.frame,'x':s.u16(0xD511),'vx':s.u16(0xD516)})
    ses.hook(0x83A6,callback)
    def transfer(s):
        if active[0] and s.mem[0xD500]==char+1 and s.mem[0xD34F]==94:
            transfers.append({'frame':s.frame,'tile_frame_shadow':s.mem[0xD34F],
                              'mapper_bank':s.cpu.a,'source_cpu':s.cpu.de,'blocks64':s.cpu.b,
                              'length_bytes':s.cpu.b*64,'source_is_ram':s.cpu.de>=0xC000})
    ses.hook(0x0D42,transfer)
    if arrival and act: ses.set_start_index(0,act)
    setup=Session.place_at_sign(act) if arrival else None
    ses.boot_new_game(character=char,arrival=setup,settle=90 if not arrival else 0)
    active[0]=True
    start=ses.s.frame
    for i in range(limit):
        signs=[0xD540+j*64 for j in range(19) if ses.m[0xD540+j*64]==0x18]
        touched=any(ses.m[a+2]>=4 for a in signs)
        ses.s.pad=(4 if backtrack and touched else 8) if arrival and ses.m[0xD501]!=32 else 0
        ses.s.run_frame()
        if side is not None and i in (0,1,2,3,7,15,31,63) and outdir is not None:
            p=outdir/f'{label}-{i:02d}.png'
            screenshots.append({'step':i,**capture_png(ses.s,p),
               'sat_shadow_sha256':sha(bytes(ses.m[0xDB00:0xDC00])),
               'vram_sha256':sha(bytes(ses.s.vram)),
               'tile0_384_sha256':sha(bytes(ses.s.vram[:384])),
               'sat_cursor_y':ses.s.u16(0xD36F),'sat_cursor_xtile':ses.s.u16(0xD371),
               'flow':ses.m[0xD293],'state':ses.m[0xD501], 'selected':ses.m[0xD506],
               'cpu_pc':ses.s.cpu.pc,'cpu_sp':ses.s.cpu.sp,'bank_slots':list(ses.s.slot)})
        if arrival and ses.m[0xD298]!=act:break
        if side is not None and i>=63:break
    return {'label':label,'evidence':'EMULATED ORIGINAL CODE, approximate VDP',
            'setup':'ARRIVAL player/camera near THZ1 sign; unmodified sign chain' if arrival else
                    'normal Tails selection then forced state20/contact at player engine entry',
            'character':char+1,'act':act,'backtrack_after_contact':backtrack,
            'injected_state_contact':side,'elapsed_frames':ses.s.frame-start,
            'rows':rows,'callbacks':calls,'tile_transfers':transfers,'screenshots':screenshots,'end':ses.snap()}

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--check',action='store_true')
    ns=p.parse_args()
    rom=R.load(ns.rom)
    out=static(rom);out['controlled_routines']=routines(rom);out['setter_controls']=setter_controls(rom)
    out['boss_gate_controls']=boss_gate_controls(rom)
    out['hidden_controls']=hidden_controls(rom)
    private=ROOT/'build/m2r1';private.mkdir(parents=True,exist_ok=True)
    out['sessions']=[]
    for label,char,arr,side,limit in [('tails-clear',1,False,0,64),('tails-side',1,False,4,64),
                                   ('sonic-side',0,False,4,64),('tails-sign',1,True,None,1400)]:
        print('running',label,flush=True)
        out['sessions'].append(run_case(rom,label,char,arr,side,limit,private))
    for act in (0,1):
        label=f'tails-sign-backtrack-act{act+1}'
        print('running',label,flush=True)
        out['sessions'].append(run_case(rom,label,1,True,None,1800,private,True,act))
    out['conclusion']='UNRESOLVED natural reachability; malformed original forced branch established'
    out['limitations']=['No input-only full-act or boss-defeat route in this task.',
                        'Sign sessions seed arrival position/camera; subsequent sign/child handoff is original code.',
                        'VDP timing/overflow is approximate; no hardware or cycle-exact confirmation.',
                        'Forced corruption is scene/RAM dependent, not a legitimate transferable sprite.']
    dest=ROOT/'data/m2r1/frame5e-evidence.json'
    text=json.dumps(out,indent=2)+'\n'
    if ns.check: assert dest.read_text()==text
    else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
    print('M2-R1 evidence written/checked',flush=True)

if __name__=='__main__':main()

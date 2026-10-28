"""Targeted original pitch reads and92 channel alias/lifecycle, not a catalogue census."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
import audio1_psg_trace as T
from m5c7batch.proof import OUT,PUB,load,save,sha,canonical,MUSIC

def run(path):
    rom=T.load_rom(path);reports={}
    for rid in MUSIC:
        d=T.Driver(rom);notes=[];reading=False
        def begin(q):
            nonlocal reading
            reading=True
        def end(q):
            nonlocal reading
            reading=False
        def read(q):
            if reading and not 0x4436<=q.cpu.hl<0x44C2:
                notes.append(dict(tick=q.update,slot=T.CHANNELS.index(q.cpu.ix),index=q.cpu.bc,address=q.cpu.hl,transpose=q.mem[q.cpu.ix+5],source_sha256=sha(bytes(q.mem[q.cpu.hl:q.cpu.hl+2]))))
        d.hook(0x4415,begin);d.hook(0x4426,end);d.hook(0x4422,read);d.request(rid)
        for _ in range(4200):d.tick()
        reports[f'{rid:02X}']=dict(out_of_region_reads=len(notes),first=notes[0] if notes else None,addresses=sorted({n['address'] for n in notes}),private_reads_sha256=sha(canonical(notes)))
        save(OUT/f'{rid:02X}-pitch-reads.json',notes)
    # No new92 loop search: use the completed original operations/certificate.
    prior=load(ROOT.parent/'private-research/m5-c7-1/92-boundaries.json')
    loops=prior['loops'];alias=[x for x in loops if x['before']['index']==4]
    assert len(alias)==4 and all(x['before']['slot']==2 and x['before']['channel'][9]==48 for x in alias)
    # Re-execute only the original handler from each possible stale byte43.
    # This validates alias preservation and8-bit wrap, not natural reachability.
    from m5a2.bank import unpack
    from m5c7batch.alias92 import Decoder
    bank=unpack((OUT/'92.scsp').read_bytes());checks=0
    for stale in range(256):
        d=T.Driver(rom);d.request(0x92);d.tick();m=Decoder(bank);m.direct(0x92);m.tick()
        addr=T.CHANNELS[2];d.mem[addr+43]=stale;m.ch[2][43]=stale
        d.cpu.ix=addr;d.cpu.de=0x87C2;d.cpu.a=4;d.call(0x4849)
        p=m.command(2,0xF7,0x87C2)
        assert list(d.mem[addr:addr+48])==list(m.ch[2]) and d.cpu.de+1==p
        checks+=1
    # Inspect every naturally reached F8 dispatch, including stack occupancy.
    d=T.Driver(rom);calls=[]
    def op(q):
        if q.cpu.a in (0xF8,0xF9):calls.append(dict(tick=q.update,slot=T.CHANNELS.index(q.cpu.ix),opcode=q.cpu.a,cursor=q.mem[q.cpu.ix+9],alias=q.mem[q.cpu.ix+43]))
    d.hook(0x46D9,op);d.request(0x92)
    for _ in range(7807):d.tick()
    collisions=[x for x in calls if x['slot']==2 and x['opcode']==0xF8 and x['cursor']==44]
    save(OUT/'92-stack-operations.json',calls)
    save(PUB/'source.json',dict(ROM_sha256=T.ROM_SHA256,pitch_reads=reports,alias92=dict(reused_original_loop=load(ROOT/'data/m5-c7-1/boundaries.json')['per_ID']['92']['loop'],stale_counter_cases_exact=checks,synthetic_stale_not_natural_reachability=True,original_alias_operations=len(alias),alias_cursors=sorted({x['before']['channel'][9] for x in alias}),original_call_return_operations=len(calls),tone2_offset43_stack_writes=len(collisions),stack_operations_sha256=sha(canonical(calls)),scope='exact92 tone2 command87C1, cursor48 only; active call contexts remain denied',F7_instruction_sha256=sha(rom[0x8849:0x8860]))))
    print('original pitch reads and256 stale alias cases PASS; stack collisions',len(collisions),flush=True)

if __name__=='__main__':run(sys.argv[1])

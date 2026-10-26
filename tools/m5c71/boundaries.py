"""Original-only causal boundary and full-period continuation proof; no decoder."""
import argparse
from collections import Counter
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import audio1_psg_trace as T
from m5c71.research import IDS,OUT,PUB,save,load,key,sha,canonical

def run(path):
    rom=T.load_rom(path);out={}
    for rid in IDS:
        rec=load(PUB/'preflight.json')['cases'][f'{rid:02X}-solo']['recurrence']
        a,p=rec['first_tick'],rec['period_ticks'];end=a+2*p
        d=T.Driver(rom);keys=[];writes=[];transfers=[];notes=[];loops=[];tables=[];commands=Counter();reloads=Counter();pending=None;note_active=False
        def note_start(q):
            nonlocal note_active
            note_active=True
        def note_end(q):
            nonlocal note_active
            note_active=False
        def note(q):
            if note_active and (q.cpu.hl>=0x44C2 or q.cpu.hl<0x4436):
                notes.append(dict(tick=q.update,slot=T.CHANNELS.index(q.cpu.ix) if q.cpu.ix in T.CHANNELS else None,IX=q.cpu.ix,index=q.cpu.bc,address=q.cpu.hl,transpose=q.mem[q.cpu.ix+5],word=q.mem[q.cpu.hl]|q.mem[q.cpu.hl+1]<<8))
        def loop(q):
            nonlocal pending
            pending=dict(tick=q.update,slot=T.CHANNELS.index(q.cpu.ix),index=q.cpu.a,channel=list(q.mem[q.cpu.ix:q.cpu.ix+48]),pointer=q.cpu.de)
        def ret(q):
            nonlocal pending
            if pending:
                loops.append(dict(before=pending,after=dict(pointer=q.cpu.de,channel=list(q.mem[q.cpu.ix:q.cpu.ix+48]))));pending=None
        def transfer(q):transfers.append([q.update,T.CHANNELS.index(q.cpu.ix),q.cpu.de,q.mem[q.cpu.de]|q.mem[q.cpu.de+1]<<8])
        d.hook(0x4415,note_start);d.hook(0x4426,note_end);d.hook(0x4422,note);d.hook(0x4849,loop);d.hook(0x485B,ret)
        d.hook(0x47B4,transfer);d.hook(0x481C,transfer)
        d.hook(0x46D9,lambda q:commands.update([q.cpu.a]))
        d.hook(0x42F6,lambda q:reloads.update([q.cpu.iy+3]))
        d.hook(0x4610,lambda q:tables.append([q.update,T.CHANNELS.index(q.cpu.ix),q.mem[q.cpu.ix+8],q.mem[q.cpu.ix+31],q.cpu.a]))
        d.request(rid)
        for tick in range(1,end+1):
            start=len(d.writes);d.tick();keys.append(sha(key(d)));writes.append([v for _,v in d.writes[start:]])
        def edges(start):return [[t-start,*rest] for t,*rest in transfers if start<t<=start+p]
        certificate=dict(first_tick=a,repeat_tick=a+p,period_ticks=p,original_ticks=end,
            full_period_state_mismatching_ticks=sum(x!=y for x,y in zip(keys[a:a+p],keys[a+p:a+2*p])),
            full_period_write_mismatching_ticks=sum(x!=y for x,y in zip(writes[a:a+p],writes[a+p:a+2*p])),
            transfer_edges_identical=edges(a)==edges(a+p),edges_per_period=len(edges(a)),edge_sha256=sha(canonical(edges(a))),
            state_includes='all400 driver RAM bytes DE00..DF8F + shared IY + logical PSG registers and data latch',
            physical_PSG_reset_allowed=False,candidate_horizon=4200,candidate_renewal_eligible=False,
            bounded_contract='Unmodified candidate must reject at4201; no safe candidate continuation until blocked source paths are separately authenticated and supported. Original deterministic recurrence alone authorises no runtime reset/renewal.')
        assert not certificate['full_period_state_mismatching_ticks'] and not certificate['full_period_write_mismatching_ticks'] and certificate['transfer_edges_identical']
        # Each actual reached F7 is checked against recovered index+39 arithmetic,
        # including aliases into the nominal call-stack area, never simulated away.
        checks=0
        for event in loops:
            b=event['before'];c=b['channel'];i=b['index'];offset=(i+39)&255
            if offset>=48:continue
            after=event['after']['channel'];expected=c.copy();count=c[offset] or d.mem[b['pointer']+1];expected[offset]=(count-1)&255
            assert after==expected,(rid,b['tick'],i,[(j,c[j],expected[j],after[j]) for j in range(48) if expected[j]!=after[j]])
            checks+=1
        extended=[x for x in loops if x['before']['index']>2]
        first=extended[0]['before'] if extended else None
        out[f'{rid:02X}']=dict(loop=certificate,out_of_validated_pitch_table_reads=len(notes),first_out_of_validated_pitch_read={k:v for k,v in notes[0].items() if k!='word'} if notes else None,
            unsupported_F7_indices=sorted({x['before']['index'] for x in extended}),first_unsupported_F7=dict(tick=first['tick'],slot=first['slot'],index=first['index'],channel_offset=(first['index']+39)&255) if first else None,
            extended_F7_operations=len(extended),extended_F7_stack_cursors=sorted({x['before']['channel'][9] for x in extended}),
            original_F7_state_assertions=checks,original_F7_operations=len(loops),original_table_reads=len(tables),original_shared_IY_reload_count=sum(reloads.values()),
            reached_command_counts={f'{k:02X}':v for k,v in sorted(commands.items())},private_operation_sha256=sha(canonical(dict(notes=notes,loops=loops,tables=tables,transfers=transfers))),
            ROM_instruction_receipts={f'{lo:04X}-{hi:04X}':sha(rom[lo+0x4000:hi+0x4000+1]) for lo,hi in [(0x4415,0x4426),(0x4849,0x485F)]})
        save(OUT/f'{rid:02X}-boundaries.json',dict(notes=notes,loops=loops,tables=tables,transfers=transfers,state_hashes=keys,certificate=certificate))
        print(f'{rid:02X}',out[f'{rid:02X}'],flush=True)
    save(PUB/'boundaries.json',dict(ROM_sha256=T.ROM_SHA256,candidate_decoder_imported=False,per_ID=out))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');run(p.parse_args().rom)

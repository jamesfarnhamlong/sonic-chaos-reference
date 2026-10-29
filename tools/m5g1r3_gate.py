"""Decision-gate evidence: reuse frozen traces; two bounded counterexample searches.

No continuation authority is issued. No horizon, loader or decoder is changed.
"""
import argparse
import ast
import gzip
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tools/m5a0')]
from m5g1r import canonical,sha,save,load
from m5g1r_evidence import fullkey
from m5c9.runtime import state
PRIVATE=ROOT.parent/'private-research'
OUT=PRIVATE/'m5-g1r3'
PUB=ROOT/'data/m5-g1r3'
DLL=ROOT.parent/'sonic-chaos-reference-m5-a1l/build/m5-a1l/psg-a1l.dll'
CASES={
 'dense-retrigger':dict(initial=0x83,events={str(t):[['request',0xBF]] for t in range(2,258)},ticks=512),
 'reader-release-boundaries':dict(initial=0x83,events={str(t):[['request',0xBF]] for t in (2,3,21,22,23,49,50,51,127,128,129,255,256,257,419,420,421)},ticks=512)
}

def cached():
    solo_path=PRIVATE/'m5-c7-1r83/solo-original.json'
    interrupted_path=PRIVATE/'m5-g1r2/83-BF-30-original.jsonl.gz'
    solo=load(solo_path)['rows']
    with gzip.open(interrupted_path,'rt') as f:items=[json.loads(line) for line in f]
    # Authenticate the reused interrupted capture against the accepted receipt.
    digest=hashlib.sha256()
    for item in items:digest.update(canonical(item)+b'\n')
    assert digest.hexdigest()==load(ROOT/'data/m5-g1r2/83-BF-30.json')['original_capture_sha256']
    # Authenticate the solo rows against their accepted original state hashes.
    solo_object=load(solo_path)
    assert sha(canonical(solo_object))==load(ROOT/'data/m5-c7-1r83/original.json')['cases']['solo']['capture_sha256']
    assert len(solo)==len(solo_object['states'])==4200
    assert all(fullkey(r)==h for r,h in zip(solo,solo_object['states']))
    rows=[x['row'] for x in items];facts=[]
    for t,(a,b) in enumerate(zip(solo,rows),1):
        changes=[(i,j) for i in range(4) for j in range(1,48) if a['channel_bytes'][i][j]!=b['channel_bytes'][i][j]]
        if changes:
            facts.append(dict(tick=t,slot_offset_changes=[list(x) for x in changes],solo_music_sha256=sha(canonical(a['channel_bytes'][:4])),interrupted_music_sha256=sha(canonical(b['channel_bytes'][:4]))));break
    assert facts and facts[0]['tick']==30 and [2,31] in facts[0]['slot_offset_changes']
    residual=rows[49]['channel_bytes'][5];assert residual[0]==0 and any(residual[1:])
    # Test only the actual accepted API: an unlisted future ring is rejected.
    from m5g1r2 import Capability
    cap=Capability('83-BF-30');cap.request(0xBF)
    try:cap.tick()
    except ValueError as e:exact_reject=str(e)
    else:raise AssertionError('R2 unexpectedly admits arbitrary request')
    # A complete equality relation without a well-formedness invariant is not
    # enough: sparse DATA does not cover every possible stream pointer.
    from m5c71r83.contract import Decoder,unpack
    bank=unpack((PRIVATE/'m5-g1r/83.scsp').read_bytes());m=Decoder(bank);m.direct(0x83);m.tick()
    missing=next(p for p in range(0x5000,0xC000) if str(p) not in bank['data'])
    m.ch[0][3:5]=missing.to_bytes(2,'little');m.ch[0][10]=1
    try:m.tick()
    except ValueError as e:guard=str(e)
    else:raise AssertionError('sparse-pointer guard not retained')
    # This seed is not asserted reachable under83/BF. It refutes unrestricted
    # all-state totality, not source/candidate equality on reachable states.
    result=dict(reused_completed_original_execution=True,new_original_execution_ticks=0,solo_file_sha256=sha(solo_path.read_bytes()),interrupted_capture_sha256=digest.hexdigest(),music_plus_write_mask_counterexample=facts[0],inactive_BF_residue=dict(tick=50,slot=5,nonzero_offsets=[i for i,x in enumerate(residual) if x],state_sha256=sha(bytes(residual))),exact_schedule_API_rejection=exact_reject,synthetic_unreachable_pointer_guard=dict(detected=True,message=guard,natural_reachability_claimed=False),decision='HOLD',continuation_permission=False)
    save(PUB/'cached-obstructions.json',result)

def original(rompath):
    import audio1_psg_trace as T
    from m5c71.research import snapshot,key
    rom=T.load_rom(rompath);OUT.mkdir(parents=True,exist_ok=True);reports={}
    ranges=[(0x4000,0x40B0),(0x41A7,0x4267),(0x4267,0x4341),(0x4341,0x43E5),(0x4415,0x4427),(0x4546,0x4639),(0x47C8,0x481C),(0x4849,0x487E)]
    for name,s in CASES.items():
        d=T.Driver(rom);d.request(0x83);edges=[];digest=hashlib.sha256()
        def edge(q):edges.append([q.update,T.CHANNELS.index(q.cpu.ix),q.mem[q.cpu.de]|q.mem[q.cpu.de+1]<<8])
        d.hook(0x47B4,edge);d.hook(0x481C,edge)
        with gzip.open(OUT/(name+'-original.jsonl.gz'),'wb') as f:
            for t in range(1,s['ticks']+1):
                for kind,v in s['events'].get(str(t),[]):d.request(v)
                start=len(d.writes);ne=len(edges);d.tick();r=snapshot(d,start);h=sha(key(d));assert fullkey(r)==h
                encoded=canonical(dict(row=r,state400=h,transfers=edges[ne:]))+b'\n';f.write(encoded);digest.update(encoded)
        reports[name]=dict(ticks=s['ticks'],requests=len(s['events']),capture_sha256=digest.hexdigest())
    save(OUT/'schedules.json',CASES)
    save(PUB/'original-searches.json',dict(cases=reports,ROM_sha256=T.ROM_SHA256,source_block_sha256={f'{a:04X}-{b:04X}':sha(rom[a+0x4000:b+0x4000]) for a,b in ranges},counterexample_search_only=True,continuation_permission=False))

def verify():
    import numpy as np
    from backend import PSG
    from m5c71r83.contract import Decoder,unpack
    bank=unpack((PRIVATE/'m5-g1r/83.scsp').read_bytes());reports={}
    assert sha(DLL.read_bytes())=='47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65'
    for name,s in CASES.items():
        m=Decoder(bank);assert m.limit==4200;m.direct(0x83);capture=hashlib.sha256();pcm=hashlib.sha256();native=hashlib.sha256()
        with gzip.open(OUT/(name+'-original.jsonl.gz'),'rt') as f,PSG(DLL) as chip,PSG(DLL) as ref:
            for t,line in enumerate(f,1):
                o=json.loads(line);capture.update(canonical(o)+b'\n')
                for kind,v in s['events'].get(str(t),[]):m.direct(v)
                ne=len(m.loops);m.tick();r=state(m)
                assert canonical(r)==canonical(o['row']) and fullkey(r)==o['state400'],(name,t,'state')
                assert [[a,i,q] for a,i,p,q in m.loops[ne:]]==o['transfers'],(name,t,'transfers')
                chip.write(r['ports']);ref.write(o['row']['ports']);before=chip.state();assert before==ref.state()
                a=chip.render();b=ref.render();assert np.array_equal(a,b) and chip.state()==ref.state()
                pcm.update(a.tobytes());native.update(canonical([before,chip.state()]))
        assert capture.hexdigest()==load(PUB/'original-searches.json')['cases'][name]['capture_sha256']
        reports[name]=dict(ticks=t,samples=t*735,state_PSG_transfer_PCM_native_mismatches=0,PCM_sha256=pcm.hexdigest(),native_sha256=native.hexdigest(),horizon_unchanged=4200,induction_proved=False)
    save(PUB/'search-results.json',dict(cases=reports,bank_canonical_sha256=sha(canonical(bank)),A1L_sha256=sha(DLL.read_bytes()),decision='HOLD',continuation_permission=False))

def audit():
    paths=['tools/m5a2/decoder.py','tools/m5a2b1/decoder.py','tools/m5a2c2/decoder.py','tools/m5c71r83/contract.py','tools/m5a2/bank.py','tools/m5g1r2.py']
    methods={}
    for p in paths:
        text=(ROOT/p).read_text();tree=ast.parse(text)
        methods[p]=dict(file_sha256=sha(text.encode()),newline_normalization='LF',functions={f.name:dict(line=f.lineno,source_sha256=sha(ast.get_source_segment(text,f).encode())) for f in ast.walk(tree) if isinstance(f,ast.FunctionDef)})
    save(PUB/'source-audit.json',dict(parent='a057504dacb09a9c994bc55991e14237497e2e6e',management='2794060c68d3d253472590c69c520b9e0a0bb107',methods=methods,decision='HOLD',source_translation_equivalence_proved=False,closed_reachable_state_family_proved=False,continuation_permission=False))

def negatives():
    from m5c71r83.contract import Decoder,unpack
    bank=unpack((PRIVATE/'m5-g1r/83.scsp').read_bytes());m=Decoder(bank);m.direct(0x83);m.tick();results={}
    def reject(name,fn):
        try:fn()
        except ValueError as e:results[name]=dict(detected=True,message=str(e))
        else:raise AssertionError('missed guard '+name)
    reject('raw-83-pitch-pair',lambda:m.byte(0x4634))
    reject('83-pitch-pair-outside-reader',lambda:m.word(0x4634))
    reject('unverified-opcode',lambda:m.command(0,0xEF,0x5000))
    index3=next(int(p) for p,v in bank['data'].items() if v==3)
    reject('F7-index3',lambda:m.command(0,0xF7,index3))
    reject('horizon4201',lambda:Decoder(bank,4201))
    # No production budget change: request the ordinary tick after4200.
    m.tick_number=4200;reject('ordinary-window-exhaustion',m.tick)
    save(PUB/'negative-controls.json',dict(cases=results,synthetic_guard_tests_only=True,continuation_permission=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['cached','original','verify','audit','negatives']);p.add_argument('rom',nargs='?');a=p.parse_args()
    if a.mode=='original':original(a.rom)
    else:globals()[a.mode]()

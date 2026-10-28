"""Original-frozen differential; private demand extraction is never a runtime oracle."""
import argparse
import copy
import gzip
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5c71.research import save,load,sha,canonical
OUT=ROOT.parent/'private-research/m5-c9'
PUB=ROOT/'data/m5-c9'
IDS=(0x91,0x93,0x95,0x8B,0x90,0x82,0x8C,0x8D)

def rows(name):
    with gzip.open(OUT/(name+'-original.jsonl.gz'),'rt') as f:
        for line in f:yield json.loads(line)
def fingerprint(r):return sha(canonical({k:v for k,v in r.items() if k!='ports'}))

def policy():
    result={}
    for rid in IDS:
        r=load(PUB/f'{rid:02X}-solo.json')
        result[f'{rid:02X}']={k:r[k] for k in ('programme_sha256','header_sha256','reader_scopes','pair_hashes')}
    save(PUB/'reader-policy.json',result)

def build(path):
    import audio1_psg_trace as T
    from m5a2.proof import ExtractionData
    from m5c9.contract import Decoder,pack,unpack
    from m5c71r83.proof import csnapshot
    rom=T.load_rom(path);policy()
    basepath=ROOT.parent/'private-research/m5-a2c6/programs.scsp';baseblob=basepath.read_bytes()
    assert sha(baseblob)=='677e65cc6038bb193e9813b5890b2127dfa7d5b0b71f0553867995659d2ba5a6'
    from m5a2.bank import unpack as old_unpack,records
    base=old_unpack(baseblob);results={};certs={}
    for rid in IDS:
        tag=f'{rid:02X}';name=tag+'-solo';original=load(PUB/(name+'.json'));contract=load(OUT/(name+'-contract.json'))
        bank=copy.deepcopy(base);bank['programs'][str(rid)]=contract['programme']
        class Data(ExtractionData):
            def __missing__(self,k):
                p=int(k)
                if 0x4630<=p<0x4636:
                    pair=p&~1
                    if sha(rom[pair+0x4000:pair+0x4002])!=original['pair_hashes'].get(str(pair)):raise ValueError('new unqualified C9 source pair')
                    self[k]=rom[p+0x4000];return self[k]
                return super().__missing__(k)
        data=Data(rom);data.update(base['data']);bank['data']=data
        # Diagnostic extraction traversal may cross windows, but grants no runtime capability.
        # The independent original is already frozen; every tick must match before certification.
        m=Decoder(bank);m.direct(rid);bad=[];edges=[];checkpoints={};repeat_signature=None;first_signature=None;completion_signature=None;rejection=None;count=0;ordered=0
        digest=__import__('hashlib').sha256();rec=original['recurrence'];finite=original['finite_release_tick']
        for t,o in enumerate(rows(name),1):
            if m.tick_number==4200:m.tick_number=0
            try:m.tick()
            except ValueError as e:rejection=dict(tick=t,message=str(e));break
            c=csnapshot(m)
            for k,v in o['row'].items():
                if canonical(c[k])!=canonical(v):bad.append(dict(tick=t,field=k))
            actual=[[t,i,q] for tick,i,p,q in m.loops if tick==m.tick_number]
            if actual!=o['transfers']:bad.append(dict(tick=t,field='transfers'))
            m.loops=[];count=t;ordered+=len(c['ports']);digest.update(canonical(o)+b'\n')
            if t%4200==0:checkpoints[str(t)]=fingerprint(c)
            if rec and t==rec['first_tick']:first_signature=fingerprint(c)
            if rec and t==rec['repeat_tick']:repeat_signature=fingerprint(c)
            if finite and t==finite:completion_signature=fingerprint(c)
        assert not bad,(tag,bad[:5])
        if rejection:
            results[tag]=dict(status='HOLD',rejection=rejection,ticks=count);print(tag,results[tag],flush=True);continue
        assert digest.hexdigest()==original['original_capture_sha256']
        if rec:assert first_signature==repeat_signature
        bank['data']=dict(data)
        for s in records(bank)['segments']:
            p,n=s['address'],s['length'];assert sha(rom[p+0x4000:p+0x4000+n])==s['sha256']
        blob=pack(bank);(OUT/(tag+'.scsp')).write_bytes(blob);checked=unpack(blob);assert checked==bank
        # Record source demand hashes only; complete records remain private.
        save(OUT/(tag+'-records.json'),records(bank))
        certs[tag]=dict(request_id=rid,bank_canonical_sha256=sha(canonical(bank)),SCSP_sha256=sha(blob),checkpoints=checkpoints,recurrence=rec,repeat_fingerprint=repeat_signature,finite_release_tick=finite,completion_fingerprint=completion_signature,finite_proof_end=count if finite else None)
        results[tag]=dict(status='PASS diagnostic; runtime gate pending',ticks=count,ordered_bytes=ordered,failure_count=len(bad),SCSP_sha256=sha(blob),SCSP_bytes=len(blob),header_sha256=contract['programme']['header_sha256'],programme_sha256=contract['programme_sha256'],source_segments_sha256=sha(canonical(records(bank))),prior_records_retained=all(bank['data'][k]==v for k,v in base['data'].items()) and all(bank['programs'][k]==v for k,v in base['programs'].items()))
        print(tag,'original/state/ordered PSG exact',count,flush=True)
    save(PUB/'capabilities.json',certs);save(PUB/'diagnostic.json',results)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');build(p.parse_args().rom)

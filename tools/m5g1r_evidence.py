"""Full400 shadow verification, unchanged-capability negatives and public summary."""
import copy
import gzip
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import m5g1r as G

def fullkey(r):
    # Entire DE00..DF8F: unrepresented globals are independently checked zero.
    ram=bytearray(400)
    for offset,value in zip((1,2,3,4,5,6,9,10,11,13,21,22),r['globals']):ram[offset]=value
    ram[15]=r['priority'];ram[17]=r['saved_noise']
    for offset,c in zip((64,112,160,208,256,304,352),r['channel_bytes']):ram[offset:offset+48]=bytes(c)
    return G.sha(ram+r['shared_IY'].to_bytes(2,'little')+G.canonical([r['registers'],r['latch']*16]))

def run():
    from m5a2.decoder import DecodeError
    from m5c9.runtime import Decoder as C9
    from m5c9.contract import unpack
    reports={};checks=0
    for name in G.cases():
        n=0
        with gzip.open(G.OUT/(name+'-original.jsonl.gz'),'rt') as f:
            for line in f:
                r=json.loads(line);assert fullkey(r['row'])==r['state400'],(name,n);n+=1
        reports[name]=n;checks+=n
    negatives={}
    def reject(name,fn):
        try:fn()
        except (ValueError,AssertionError) as e:negatives[name]=dict(detected=True,message=str(e))
        else:raise AssertionError('missed negative '+name)
    for rid in (0x91,0x93,0x95,0x90,0x8B,0x8C):
        tag=f'{rid:02X}'
        reject(tag+'-repacked-no-solo-certificate',lambda rid=rid:C9(unpack((G.OUT/f'{rid:02X}.scsp').read_bytes())))
        bank=unpack((G.PRIVATE/'m5-c9'/f'{rid:02X}.scsp').read_bytes())
        for action in ('SFX','same','other','fade'):
            m=C9(bank);m.direct(rid)
            for _ in range(10):m.tick()
            if action=='fade':m.fade=[12,1,2]
            else:m.direct(0xBF if action=='SFX' else rid if action=='same' else 0x81)
            for _ in range(4190):m.tick()
            reject(tag+'-'+action+'-4201',m.tick)
    # Both older certificate implementations must still revoke after requests.
    from m5c71r83.contract import unpack as r83unpack
    from m5c71r83.renewal import Decoder as R83
    from m5c7batch.renewal import Decoder as Batch
    from m5a2.bank import unpack as legacy
    for rid,p,cls,loader in [(0x83,G.PRIVATE/'m5-c7-1r83/programs.scsp',R83,r83unpack),(0x92,G.PRIVATE/'m5-c7-batch/92.scsp',Batch,legacy),(0x8F,G.PRIVATE/'m5-c7-batch/82-8B-8C-8D-8F-90.scsp',Batch,legacy)]:
        m=cls(loader(p.read_bytes()));m.direct(rid)
        for _ in range(10):m.tick()
        m.direct(0xBF)
        for _ in range(4190):m.tick()
        reject(f'{rid:02X}-SFX-4201',m.tick)
    with gzip.open(G.OUT/'81-BF-30-original.jsonl.gz','rt') as f:row=json.loads(next(f))
    for label,mutate in [('channel',lambda r:r['channel_bytes'][0].__setitem__(3,r['channel_bytes'][0][3]^1)),('priority',lambda r:r.__setitem__('priority',1)),('latch',lambda r:r.__setitem__('latch',(r['latch']+1)%8)),('IY',lambda r:r.__setitem__('shared_IY',r['shared_IY']^1))]:
        changed=copy.deepcopy(row['row']);mutate(changed)
        reject('full400-mutant-'+label,lambda changed=changed:check_equal(fullkey(changed),row['state400']))
    verified=G.load(G.PUB/'verified.json')['cases'];assert set(verified)==set(G.cases())
    assert all(r['status']=='PASS' and r['isolated_exact'] for r in verified.values())
    G.save(G.PUB/'evidence.json',dict(cases=len(verified),ticks=checks,samples=sum(r['samples'] for r in verified.values()),full400_shadow_ticks=checks,full400_shadow_mismatches=0,negative_controls=negatives,groups={k:sum(s['group']==k for s in G.cases().values()) for k in sorted({s['group'] for s in G.cases().values()})},native_GameMaker_tested=False,continuation_granted=False,source_schedules_sha256=G.sha(G.canonical(G.cases()))))
    print('full400 shadow',checks,'ticks; negatives',len(negatives),'caught',flush=True)

def check_equal(a,b):assert a==b,'full state corruption detected'

if __name__=='__main__':run()

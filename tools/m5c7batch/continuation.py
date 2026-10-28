"""New bounded continuation traces; reuse original C7-1 $92 loop certificate."""
import argparse
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5c7batch.proof import OUT,PUB,load,save,sha,canonical,snapshot,key
CASES={0x92:('92.scsp',511,4159),0x8F:('82-8B-8C-8D-8F-90.scsp',78,1326)}

def original(path):
    import audio1_psg_trace as T
    rom=T.load_rom(path);manifest=load(OUT/'oracle-manifest.json')
    for rid,(_,a,b) in CASES.items():
        d=T.Driver(rom);rows=[];transfers=[];states=[]
        def edge(q):transfers.append([q.update,T.CHANNELS.index(q.cpu.ix),q.mem[q.cpu.de]|q.mem[q.cpu.de+1]<<8])
        d.hook(0x47B4,edge);d.hook(0x481C,edge);d.request(rid)
        for t in range(1,13001):
            start=len(d.writes);d.tick();rows.append(snapshot(d,start));states.append(sha(key(d)))
        assert states[a-1]==states[b-1] and states[a:b]==states[b:b+b-a]
        private=dict(rows=rows,transfers=transfers,states=states)
        name=f'{rid:02X}-long';save(OUT/(name+'-original.json'),private);manifest[name]=sha(canonical(private))
        print(name,'original continuation frozen',flush=True)
    save(OUT/'oracle-manifest.json',manifest)

def candidate():
    from m5a2.bank import unpack
    from m5c7batch.alias92 import Decoder as Bounded
    from m5c7batch.renewal import fingerprint,Decoder
    from m5c71r83.proof import csnapshot
    certs={}
    for rid,(bankname,a,b) in CASES.items():
        bank=unpack((OUT/bankname).read_bytes());m=Bounded(bank);m.direct(rid);states=[]
        for t in range(1,b+1):m.tick();states.append(fingerprint(m))
        assert states[a-1]==states[b-1]
        certs[f'{rid:02X}']=dict(request_id=rid,bank_canonical_sha256=sha(canonical(bank)),state_sha256=states[b-1],first_tick=a,repeat_tick=b,period_ticks=b-a)
    save(PUB/'continuation-certificates.json',certs)
    manifest=load(OUT/'oracle-manifest.json');result={}
    for rid,(bankname,a,b) in CASES.items():
        name=f'{rid:02X}-long';o=load(OUT/(name+'-original.json'));assert sha(canonical(o))==manifest[name]
        bank=unpack((OUT/bankname).read_bytes());m=Decoder(bank);m.direct(rid);rows=[];edges=[];renewals=[];n=0
        for t in range(1,13001):
            m.tick();rows.append(csnapshot(m));edges.extend([[t,i,q] for tick,i,p,q in m.loops if tick==t])
            if m.renewal_count!=n:renewals.append(m.last_renewal_tick);n=m.renewal_count
        bad=[dict(tick=t,field=k) for t,(c,r) in enumerate(zip(rows,o['rows']),1) for k in r if canonical(c[k])!=canonical(r[k])]
        assert not bad and edges==o['transfers']
        assert all(canonical(rows[j]['ports'])==canonical(rows[j+b-a]['ports']) for j in range(a,b))
        schedule=dict(initial=rid,events={},ticks=13000,renew=True)
        save(OUT/(name+'-candidate.json'),dict(rows=rows,schedule=schedule))
        result[name]=dict(status='PASS',ticks=13000,requested_ticks=13000,failure_count=0,renewal_ticks=renewals,ordered_bytes=sum(len(r['ports']) for r in rows))
        # Reuse grouped PCM/isolation runner by giving long scenarios an ordinary receipt.
        save(PUB/f'emission-{rid:02X}-long.json',dict(cases={name:result[name]},bank=bankname,SCSP_sha256=sha((OUT/bankname).read_bytes())))
        print(name,'exact continuation PASS',renewals,flush=True)
    save(PUB/'continuation.json',dict(cases=result,original400_RAM_exact=True,driver_or_chip_resets_at_loop=0,scope='only pinned uninterrupted solos; any subsequent host request/fade revokes renewal'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['original','candidate']);p.add_argument('rom',nargs='?');a=p.parse_args()
    original(a.rom) if a.phase=='original' else candidate()

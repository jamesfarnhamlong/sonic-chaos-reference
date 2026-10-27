"""Negative controls and unchanged C6 frozen-state regression (no new originals)."""
import copy
import struct
import zlib
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5c71r83.proof import OUT,PUB,C6,csnapshot,apply,save,load,sha,canonical
from m5c71r83.contract import unpack,pack,Decoder,DecodeError
from m5c71r83.renewal import Decoder as Renewing
from m5a2.bank import records,unpack as legacy_unpack,MAGIC

def wire(meta):
    raw=canonical(meta);return MAGIC+struct.pack('<I',len(raw))+zlib.compress(raw,9)+bytes.fromhex(sha(raw))

def run():
    blob=(OUT/'programs.scsp').read_bytes();bank=unpack(blob);neg={}
    def reject(name,fn):
        try:fn()
        except (DecodeError,ValueError) as e:neg[name]=dict(detected=True,error=str(e))
        else:raise AssertionError('negative was accepted: '+name)
    def changed_data(address,value):
        b=copy.deepcopy(bank);b['data'][str(address)]=value;return pack(b)
    reject('legacy-loader-still-rejects-pair',lambda:legacy_unpack(blob))
    reject('wrong-pair-byte-recomputed-container',lambda:unpack(changed_data(0x4634,bank['data'][str(0x4634)]^1)))
    b=copy.deepcopy(bank);b['data'][str(0x4633)]=0;reject('forged-adjacent-region',lambda:unpack(pack(b)))
    b=copy.deepcopy(bank);b['data'][str(0x4600)]=0;reject('forged-executable-region',lambda:unpack(pack(b)))
    meta=records(bank);pair=next(s for s in meta['segments'] if s['address']==0x4634)
    pair['length']=3;pair['hex']+='00';pair['sha256']=sha(bytes.fromhex(pair['hex']))
    reject('forged-extended-pair-length',lambda:unpack(wire(meta)))
    b=copy.deepcopy(bank);del b['data'][str(0x4635)];reject('truncated-pair-record',lambda:unpack(pack(b)))
    meta=records(bank);pair=next(s for s in meta['segments'] if s['address']==0x4634);pair['sha256']='0'*64
    reject('wrong-pair-segment-hash',lambda:unpack(wire(meta)))
    reject('truncated-container',lambda:unpack(blob[:40]))
    corrupt=bytearray(blob);corrupt[-1]^=1;reject('corrupt-container-hash',lambda:unpack(bytes(corrupt)))
    b=copy.deepcopy(bank);del b['programs']['131'];reject('pair-without83-owner',lambda:unpack(pack(b)))
    b=copy.deepcopy(bank);b['programs']['131']['streams'][1]['pointer']=0x4634
    reject('forged83-header-stream',lambda:unpack(pack(b)))
    b=copy.deepcopy(bank);b['programs']['131']['header_sha256']='0'*64
    reject('forged83-source-header-hash',lambda:unpack(pack(b)))
    m=Decoder(bank);m.direct(0x83)
    reject('direct-pair-byte',lambda:m.byte(0x4634))
    reject('direct-pair-word',lambda:m.word(0x4634))
    reject('unaligned-pair-word',lambda:m.word(0x4635))
    reject('invalid-pointer',lambda:m.byte(0x4636))
    # Even with the owning channel armed, command handlers may not borrow note
    # lookup permissions to branch/call into these two source bytes.
    m=Decoder(bank);m.direct(0x83);m.tick();m._reader=1
    reject('command-word-cannot-use-pair',lambda:m.command(1,0xF6,0x4634))
    m._reader=0;reject('wrong-reader',lambda:m.word(0x4634))
    m._reader=1;m.owners[1]=0x81;reject('wrong-owner',lambda:m.word(0x4634))
    reject('unsupported-E2',lambda:Decoder(bank).command(0,0xE2,0xB800))
    b=copy.deepcopy(bank);b['data'][str(0xB800)]=4
    reject('unchanged-F7-index4-bound',lambda:Decoder(b).command(2,0xF7,0xB800))
    reject('constructor-horizon4201',lambda:Decoder(bank,horizon=4201))
    b=copy.deepcopy(bank);b['horizon']=4201;reject('SCSP-horizon4201',lambda:unpack(pack(b)))
    def until_rejected(m,events=None):
        m.direct(0x83)
        for t in range(1,4202):
            if events:events(m,t)
            try:m.tick()
            except DecodeError:
                assert t==4201 and getattr(m,'renewal_count',0)==0
                raise
    reject('bounded-execution4201',lambda:until_rejected(Decoder(bank)))
    reject('SFX-revokes-renewal',lambda:until_rejected(Renewing(bank),lambda m,t:m.direct(0xBF) if t==3000 else None))
    reject('retrigger-revokes-renewal',lambda:until_rejected(Renewing(bank),lambda m,t:m.direct(0x83) if t==100 else None))
    reject('signature-mismatch-no-renewal',lambda:until_rejected(Renewing(bank),lambda m,t:m.ch[6].__setitem__(42,1) if t==3595 else None))
    def interrupted_after_renewal():
        m=Renewing(bank);m.direct(0x83)
        for t in range(1,7274):
            if t==4000:m.direct(0xBF)
            try:m.tick()
            except DecodeError:
                assert t==7273 and m.renewal_count==1
                raise
    reject('SFX-after-first-renewal-still-expires',interrupted_after_renewal)
    b=copy.deepcopy(bank);b['data'][str(0x4436)]^=1
    reject('wrong-ordinary-source-byte-renewal-bank',lambda:Renewing(b))
    # Ordinary-source corruption remains detectable against the independent
    # oracle even where legacy segment checksums have been deliberately rebuilt.
    b=copy.deepcopy(bank)
    for k in b['data']:
        if 0x4436<=int(k)<0x44C2 and int(k)%2==0:b['data'][k]^=1
    m=Decoder(b);m.direct(0x83);original=load(OUT/'solo-original.json')['rows'];wrongtick=None
    for t in range(1,33):
        m.tick()
        if canonical(m.writes)!=canonical(original[t-1]['ports']):wrongtick=t;break
    assert wrongtick;neg['wrong-ordinary-pitch-differential']=dict(detected=True,first_difference_tick=wrongtick)
    # Preservation: replay all accepted C6 schedules with the new bounded
    # subclass and compare every field to their immutable accepted captures.
    from m5a2c6.proof import allcases
    regressions={}
    for name,(rid,events,ticks) in allcases().items():
        m=Decoder(bank);m.direct(rid);old=load(C6/(name+'.json'))['candidate']
        assert len(old)==ticks
        for t in range(1,ticks+1):
            for kind,v in events.get(t,[]):
                if kind=='mailbox':m.direct(*v)
                else:apply(m,kind,v)
            m.tick();row=csnapshot(m)
            assert all(canonical(row[k])==canonical(v) for k,v in old[t-1].items()),(name,t)
        regressions[name]=dict(ticks=ticks,exact=True)
    assert canonical(unpack((C6/'programs.scsp').read_bytes()))==canonical(legacy_unpack((C6/'programs.scsp').read_bytes()))
    save(PUB/'negatives.json',dict(controls=neg,total=len(neg),all_detected=True))
    save(PUB/'preservation.json',dict(C6_cases=regressions,C6_ticks=sum(c['ticks'] for c in regressions.values()),
        C6_bank_sha256=sha((C6/'programs.scsp').read_bytes()),old_bank_new_loader_identical=True,
        C71_private_archive_sha256=sha((ROOT.parent/'releases/SonicChaos_M5_C7_1_20261026_RESEARCH_PRIVATE.zip').read_bytes()),
        accepted_A1L_sha256=sha((ROOT.parent/'sonic-chaos-reference-m5-a1l/build/m5-a1l/psg-a1l.dll').read_bytes()),
        new92_support=False,legacy_sources_modified=False))
    print('negatives',len(neg),'C6 frozen regressions',len(regressions),sum(c['ticks'] for c in regressions.values()))

if __name__=='__main__':run()

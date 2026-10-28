"""Source receipts, fail-closed negative controls and per-ID qualification ledger."""
import copy
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5c7batch.proof import OUT,PUB,load,save,sha,canonical,MUSIC,SFX
from m5a2.bank import unpack,pack
from m5a2c2.decoder import Decoder as Legacy
from m5c7batch.alias92 import Decoder as Alias
from m5c7batch.renewal import Decoder as Renewing

def run():
    negatives={}
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError) as e:negatives[name]=dict(detected=True,error=type(e).__name__,message=str(e))
        else:raise AssertionError('negative accepted: '+name)
    b92=unpack((OUT/'92.scsp').read_bytes())
    def prepared(bank=None):
        m=Alias(copy.deepcopy(b92) if bank is None else bank);m.direct(0x92);m.tick();return m
    for cursor in (42,44,46):
        def probe(cursor=cursor):
            m=prepared();m.ch[2][9]=cursor;m.command(2,0xF7,0x87C2)
        reject('92-active-stack-'+str(cursor),probe)
    def wrong_owner():
        m=prepared();m.owners[2]=0x81;m.command(2,0xF7,0x87C2)
    reject('92-wrong-owner',wrong_owner)
    def wrong_slot():
        m=prepared();m.command(1,0xF7,0x87C2)
    reject('92-wrong-slot',wrong_slot)
    def changed_index():
        b=copy.deepcopy(b92);b['data'][str(0x87C2)]=3;m=prepared(b);m.command(2,0xF7,0x87C2)
    reject('92-index3',changed_index)
    def changed_command():
        b=copy.deepcopy(b92);b['data'][str(0x87C3)]^=1;m=prepared(b);m.command(2,0xF7,0x87C2)
    reject('92-command-hash',changed_command)
    def changed_header():
        b=copy.deepcopy(b92);b['programs']['146']['header_sha256']='0'*64;m=prepared(b);m.command(2,0xF7,0x87C2)
    reject('92-header-hash',changed_header)
    def forged_metadata():
        b=copy.deepcopy(b92);b['programs']['146']['streams'][0]['transpose']+=1;m=prepared(b);m.command(2,0xF7,0x87C2)
    reject('92-forged-metadata-with-original-header-hash',forged_metadata)
    def old_guard():
        m=Legacy(b92);m.direct(0x92)
        for _ in range(3266):m.tick()
    reject('legacy-index4-still-denied',old_guard)
    reject('bounded-constructor4201',lambda:Alias(b92,4201))
    def horizon():
        m=Alias(b92);m.direct(0x92)
        for _ in range(4201):m.tick()
    reject('bounded-execution4201',horizon)
    reject('unknown-E2',lambda:prepared().command(2,0xE2,0x87C2))
    reject('pitch4634-still-denied',lambda:prepared().word(0x4634))
    reject('corrupt-SCSP',lambda:unpack((OUT/'92.scsp').read_bytes()[:-1]+b'0'))
    reject('truncated-SCSP',lambda:unpack((OUT/'92.scsp').read_bytes()[:30]))
    for rid,bankname in ((0x92,'92.scsp'),(0x8F,'82-8B-8C-8D-8F-90.scsp')):
        bank=unpack((OUT/bankname).read_bytes())
        def modified_bank(bank=bank):
            b=copy.deepcopy(bank);b['programs'][str(rid)]['tempo']^=1;Renewing(b)
        reject(f'{rid:02X}-renew-modified-bank',modified_bank)
        for kind in ('request','fade','state'):
            def revoked(kind=kind,rid=rid,bank=bank):
                m=Renewing(bank);m.direct(rid)
                for t in range(1,4202):
                    if t==100:
                        if kind=='request':m.direct(rid)
                        elif kind=='fade':m.fade=[12,1,2]
                        else:m.ch[0][42]^=1
                    m.tick()
            reject(f'{rid:02X}-renew-revoked-'+kind,revoked)
    save(PUB/'negative.json',dict(cases=negatives,all_detected=all(r['detected'] for r in negatives.values())))
    emissions={};pcms={};banks={}
    for p in sorted(PUB.glob('emission-*.json')):
        e=load(p);emissions.update(e['cases']);banks.update({name:e['bank'] for name in e['cases']})
    for p in sorted(PUB.glob('pcm-*.json')):pcms.update(load(p)['cases'])
    pre=load(PUB/'preflight.json')['cases'];records={};ledger={}
    for rid in (*MUSIC,0x92,*SFX):
        tag=f'{rid:02X}';name=tag+'-solo';bankname=banks[name];bank=unpack((OUT/bankname).read_bytes());m=(Alias if rid==0x92 else Legacy)(bank)
        m.direct(rid);visited=set();read=m.byte
        def observe(p):visited.add(p);return read(p)
        m.byte=observe
        # Keep rejection tick excluded from qualified prefixes, but record every source read demanded.
        for _ in range(emissions[name]['ticks']):m.tick()
        record=dict(header=bank['programs'][str(rid)],data=sorted([p,bank['data'][str(p)]] for p in visited))
        save(OUT/(tag+'-source-records.json'),record)
        records[tag]=dict(header_sha256=record['header']['header_sha256'],program_metadata_sha256=sha(canonical(record['header'])),record_sha256=sha(canonical(record)),source_bytes=len(visited),SCSP_sha256=sha((OUT/bankname).read_bytes()))
        related={k:v for k,v in emissions.items() if k.startswith(tag+'-')};assert all(not c['failure_count'] for c in related.values())
        assert all(k in pcms and pcms[k]['status']=='PASS' for k in related)
        blocker=None
        if emissions[name].get('rejection'):blocker=emissions[name]['rejection']
        elif rid in (0x82,0x8C,0x8D):blocker=dict(message='complete original lifecycle exceeds4200 / no eligible in-window recurrence; bounded prefix only',tick=4201)
        status='HOLD' if blocker else 'GO scoped Research'
        context='matched prefixes only; incomplete programme' if blocker else 'solo and81 overlay, listed600-tick schedules only' if rid>=0xA0 else 'bounded4200 schedules and pinned uninterrupted13000 solo'
        ledger[tag]=dict(status=status,blocker=blocker,exact_solo_ticks=emissions[name]['ticks'],contexts=context,native_F2_playable=False,original_release_tick=pre[name].get('release_tick'),original_recurrence=pre[name].get('recurrence'))
    save(PUB/'source-records.json',records)
    save(PUB/'verdict.json',dict(management_sha='89b32f3dfabdfc195a1a21a295d639c0cf658e77',research_parent='9961b05eb9962bdeb43983028aa4b9ca4b802cec',baseline_F2_playable=39,new_native_F2=0,per_ID=ledger,new_scoped_Research_GO=[k for k,v in ledger.items() if v['status'].startswith('GO')],HOLD=[k for k,v in ledger.items() if v['status']=='HOLD'],exact_ticks=sum(c['ticks'] for c in emissions.values()),exact_A1L_samples=sum(c['samples'] for c in pcms.values()),negative_controls=len(negatives),private_payloads_published=False))
    print('negative guards',len(negatives),'new scoped GO',[k for k,v in ledger.items() if v['status'].startswith('GO')],flush=True)

if __name__=='__main__':run()

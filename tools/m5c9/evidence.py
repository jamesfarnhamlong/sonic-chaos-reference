"""Private-payload negative controls and source-safe per-ID C9 delivery ledger."""
import copy
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5c9.proof import OUT,PUB,IDS,save,load,sha,canonical
from m5c9.contract import Decoder as Bounded,unpack,pack,policies
from m5c9.runtime import Decoder
from m5a2c2.decoder import Decoder as Legacy
from m5a2.bank import unpack as old_unpack

def run():
    negatives={};policy=policies();cap=load(PUB/'capabilities.json')
    def reject(name,fn):
        try:fn()
        except ValueError as e:negatives[name]=dict(detected=True,message=str(e))
        else:raise AssertionError('negative was accepted: '+name)
    for rid in IDS:
        tag=f'{rid:02X}';blob=(OUT/(tag+'.scsp')).read_bytes();bank=unpack(blob)
        reject(tag+'-truncated',lambda:unpack(blob[:30]))
        reject(tag+'-checksum',lambda:unpack(blob[:-1]+bytes([blob[-1]^1])))
        def altered_header():
            b=copy.deepcopy(bank);b['programs'][str(rid)]['tempo']^=1;unpack(pack(b))
        reject(tag+'-header-metadata',altered_header)
        reject(tag+'-constructor4201',lambda:Decoder(bank,4201))
        def bounded_limit():
            m=Bounded(bank);m.direct(rid)
            for _ in range(4201):m.tick()
        reject(tag+'-ordinary4201',bounded_limit)
        def changed_bank():
            b=copy.deepcopy(bank);key=next(iter(b['data']));b['data'][key]^=1;Decoder(b)
        reject(tag+'-continuation-bank',changed_bank)
        for event in ('same-request','other-request','fade'):
            def revoke(event=event):
                m=Decoder(bank);m.direct(rid)
                for t in range(1,4202):
                    if t==100:
                        if event=='same-request':m.direct(rid)
                        elif event=='other-request':m.direct(0x88)
                        else:m.fade=[12,1,2]
                    m.tick()
            reject(tag+'-revoke-'+event,revoke)
        def checkpoint_state():
            m=Decoder(bank);m.direct(rid)
            for _ in range(4200):m.tick()
            m.ch[0][42]^=1;m.tick()
        reject(tag+'-checkpoint-state',checkpoint_state)
        # Mixed state is only bounded within the original window, never silently renewed.
        def late_revoke():
            m=Decoder(bank);m.direct(rid)
            for _ in range(4201):m.tick()
            m.direct(rid);m.tick()
        reject(tag+'-late-request',late_revoke)
        def unknown():
            m=Bounded(bank);m.direct(rid);m.tick();m.command(0,0xE2,bank['programs'][str(rid)]['streams'][0]['pointer'])
        reject(tag+'-unknown-E2',unknown)
        if policy[tag]['reader_scopes']:
            slot,transpose,p,index=policy[tag]['reader_scopes'][0]
            reject(tag+'-legacy-loader-keeps-pitch-guard',lambda:old_unpack(blob))
            for kind in ('direct-byte','direct-word','owner','slot','transpose','raw-mode','command-reader','wrong-address'):
                def reader_scope(kind=kind):
                    m=Bounded(bank);m.direct(rid);m.tick();m._reader=slot;m.ch[slot][5]=transpose
                    if kind=='direct-byte':m.byte(p);return
                    if kind=='direct-word':m._reader=None
                    elif kind=='owner':m.owners[slot]=0x83
                    elif kind=='slot':m._reader=(slot+1)%3
                    elif kind=='transpose':m.ch[slot][5]^=1
                    elif kind=='raw-mode':m.ch[slot][0]|=8
                    elif kind=='command-reader':m._command=True
                    elif kind=='wrong-address':m.word(p+1);return
                    m.word(p)
                reject(tag+'-pitch-'+kind,reader_scope)
            def forged_pitch():
                b=copy.deepcopy(bank);b['data'][str(p)]^=1;unpack(pack(b))
            reject(tag+'-pitch-recomputed-container-hashes',forged_pitch)
            def omitted_pitch():
                b=copy.deepcopy(bank);b['data'].pop(str(p));unpack(pack(b))
            reject(tag+'-pitch-truncated-pair',omitted_pitch)
        else:
            reject(tag+'-no-pitch-permission',lambda:Bounded(bank).word(0x4634))
        rec=cap[tag]['recurrence']
        if rec:
            def recurrence_state():
                m=Decoder(bank);m.direct(rid)
                for _ in range(rec['repeat_tick']):m.tick()
                m.ch[0][42]^=1;m.tick()
            reject(tag+'-recurrence-state',recurrence_state)
        else:
            release=cap[tag]['finite_release_tick']
            def finite_mismatch():
                m=Decoder(bank);m.direct(rid)
                for _ in range(release-1):m.tick()
                m.ch[0][42]^=1;m.tick()
            reject(tag+'-finite-completion-state',finite_mismatch)
            def finite_end():
                m=Decoder(bank);m.direct(rid)
                for _ in range(cap[tag]['finite_proof_end']+1):m.tick()
            reject(tag+'-finite-proof-exhausted',finite_end)
    save(PUB/'negative.json',dict(cases=negatives,count=len(negatives),all_detected=True))
    ledger={};total_ticks=total_samples=0
    for rid in IDS:
        tag=f'{rid:02X}';r=load(PUB/(tag+'-solo-verified.json'));o=load(PUB/(tag+'-solo.json'));assert r['status']=='PASS'
        total_ticks+=r['ticks'];total_samples+=r['samples']
        ledger[tag]=dict(verdict='GO scoped Research',blocker=None,solo_ticks=r['ticks'],samples=r['samples'],SCSP_sha256=r['SCSP_sha256'],programme_sha256=o['programme_sha256'],reader_scopes=o['reader_scopes'],pair_hashes=o['pair_hashes'],original_recurrence=o['recurrence'],finite_release_tick=o['finite_release_tick'],scope='pinned uninterrupted solo; listed checkpoint/recurrence or finite-completion contract only',native_F2_playable=False)
    for name in ('90-opening-fade','90-eez3-retrigger'):
        r=load(PUB/(name+'-verified.json'));assert r['status']=='PASS';total_ticks+=r['ticks'];total_samples+=r['samples']
    save(PUB/'verdict.json',dict(management_sha='0ee614a7e040bdcc566f3816fa419b2c41343dea',research_parent='96ae9ea877abbdb7419647aff72807c456ffcc42',per_ID=ledger,new_Research_GO=8,Research_HOLD=[],Research_catalogue_qualified=63,qualification_is_scoped=True,baseline_native_F2=39,new_native_F2=0,total_verified_ticks=total_ticks,total_exact_A1L_samples=total_samples,negative_controls=len(negatives),existing55_reproved=False,original83_scope_changed=False,clock=3546893,rate=44100,tick_samples=735,global4200_changed=False))
    print('negative controls',len(negatives),'PASS; new Research GO8; total',total_ticks,total_samples,flush=True)

if __name__=='__main__':run()

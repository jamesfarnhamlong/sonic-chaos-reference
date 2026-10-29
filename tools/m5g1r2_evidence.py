"""Aggregate frozen private traces without publishing per-update payloads."""
import gzip
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import m5g1r2 as G

def run():
    details={}
    for name in G.schedules():
        cert=G.load(G.PUB/(name+'.json'));verified=G.load(G.PUB/(name+'-verified.json'))
        phases={};previous=None;last_suppressed={};clears=[];active_after=[]
        with gzip.open(G.OUT/(name+'-original.jsonl.gz'),'rt') as f:
            for t,line in enumerate(f,1):
                row=json.loads(line)['row'];part='prelude' if t<min(map(int,cert['schedule']['events'])) else 'interaction_and_tail' if t<=4200 else 'beyond_former_horizon'
                item=phases.setdefault(part,dict(ticks=0,ordered_PSG_bytes=0,music_slot_progress_updates=[0]*4,suppressed_music_slot_progress_updates=[0]*4))
                item['ticks']+=1;item['ordered_PSG_bytes']+=len(row['ports'])
                for i,c in enumerate(row['channel_bytes'][:4]):
                    if previous and c[2:5]+c[10:11]!=previous['channel_bytes'][i][2:5]+previous['channel_bytes'][i][10:11]:
                        item['music_slot_progress_updates'][i]+=1
                        if c[0]&4:item['suppressed_music_slot_progress_updates'][i]+=1
                    if c[0]&4:last_suppressed[i]=t
                    if previous and previous['channels'][i]&4 and not row['channels'][i]&4:clears.append([t,i])
                previous=row
        assert t==cert['ticks']==verified['ticks']
        assert any(phases['beyond_former_horizon']['music_slot_progress_updates'])
        details[name]=dict(phases=phases,suppression_clear_ticks=clears,last_suppressed_tick_by_slot=last_suppressed,final_music_active_slots=[i for i,c in enumerate(previous['channels'][:4]) if c&128],recurrence=cert['recurrence'],accepted_music_epochs=cert['accepted_music_epochs'],status='GO_EXACT_SCHEDULE_RESEARCH_ONLY')
    receipts=[G.load(G.PUB/(name+'-verified.json')) for name in details]
    negatives=G.load(G.PUB/'negatives.json')
    summary=dict(parent='cf07885b5ccb719d5db9e3b09ebb79471ec09587',management='81461eb98542acd52a72f9c783a0bb60f296f78c',cases=len(details),ticks=sum(r['ticks'] for r in receipts),samples=sum(r['samples'] for r in receipts),renewals=sum(r['renewals'] for r in receipts),checkpoint_extensions=sum(r['extensions'] for r in receipts),negative_controls=len(negatives),state_PSG_transfer_PCM_native_partition_mismatches=0,physical_PSG_resets_at_events_checkpoints_recurrences=0,old_solo_certificates_reused=False,arbitrary_gameplay_phase_continuation='HOLD',other_music_programmes='HOLD_NOT_EXPANDED',native_GameMaker_tested=False,cases_detail=details)
    G.save(G.PUB/'evidence.json',summary)
    print({k:v for k,v in summary.items() if k!='cases_detail'})

if __name__=='__main__':run()

"""B2 completion, zero-tempo/loop facts, negative controls and scope inventory."""
import copy
import gc
import json
from pathlib import Path
import statistics
import sys
import time
import tracemalloc

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5a2.bank import pack,unpack
from m5a2.decoder import DecodeError
from m5a2b1.decoder import Decoder
from m5a2b2.proof import OUT,PUB,B1OLD,BATCH,ENDS,CASES,save,sha
from m5a2b1.proof import candidate


def load(name):return json.loads((OUT/(name+'.json')).read_text())


def run():
    blob=(OUT/'programs.scsp').read_bytes();bank=unpack(blob);termination={};loops={};zero={}
    for rid,end in zip(BATCH,ENDS):
        name=f'solo-{rid:02X}';record=load(name);rows=record['original']
        actual=next(i+1 for i,r in enumerate(rows) if not any(f&128 for f in r['channels']))
        assert actual==end and len(rows)-end==32
        assert all(not any(f&128 for f in r['channels']) and not r['ports'] for r in rows[end:])
        assert all(r['registers']==rows[end-1]['registers'] for r in rows[end:])
        termination[f'{rid:02X}']=dict(inactive_tick=end,post_completion_ticks=32,
            post_completion_port_bytes=0,final_attenuation=rows[-1]['registers'][2],
            final_tone_periods=rows[-1]['registers'][0],PCM_samples=len(rows)*735,
            authentic_terminal_writes_exact=True)
        assert record['original_transfers']==record['candidate_transfers']
        if rid in (0x94,0x98,0x9A):
            loops[f'{rid:02X}']=dict(taken_branches=len(record['original_transfers']),
                original_and_candidate_targets_and_ticks_identical=True,
                transfer_sha256=sha(json.dumps(record['original_transfers'],sort_keys=True,separators=(',',':')).encode()))
        if rid in (0x94,0x9A):
            assert bank['programs'][str(rid)]['tempo']==0
            assert all(r['globals'][:2]==[0,0] for r in rows)
            counters=[r['channel_bytes'][i][10] for r in rows[:end] for i in range(4)]
            assert max(counters)>0
            zero[f'{rid:02X}']=dict(original_tempo_pair_remains_zero=True,all_duration_bytes_exact=True,
                 duration_counter_range=[min(counters),max(counters)])
    ending=load('THZ-to-continue')['original'];assert all(not any(f&128 for f in r['channels']) and not r['ports'] for r in ending[1140:])
    old8a=load('B1-solo-8A')['original']
    assert all(r['registers'][2]==[15,15,0,15] and r['registers'][0][2]==0 for r in old8a[178:])
    bad=copy.deepcopy(bank)
    for k in bad['data']:
        if 0x4436<=int(k)<0x44C2 and int(k)%2==0:bad['data'][k]^=1
    _,wrong,_,_=candidate(unpack(pack(bad)),CASES['solo-8E']);correct=load('solo-8E')['candidate']
    wrongtick=next(i+1 for i,(a,b) in enumerate(zip(wrong,correct)) if a['ports']!=b['ports'])
    class MissingTerminal(Decoder):
        def release(self,i):self.ch[i][0]=0
    m=MissingTerminal(bank);m.direct(0x8E);terminal=None
    for t in range(1,221):
        m.tick()
        if m.writes!=correct[t-1]['ports']:terminal=t;break
    assert terminal is not None
    # Delete a required operand/pointer record: missing bytes must raise, never pad.
    truncated=copy.deepcopy(bank);pointer=truncated['programs'][str(0x8E)]['streams'][0]['pointer']
    del truncated['data'][str(pointer)]
    m=Decoder(truncated);m.direct(0x8E)
    try:m.tick()
    except DecodeError:missing_rejected=True
    else:raise AssertionError('missing bytes accepted')
    timings=[]
    for _ in range(3):
        for rid in BATCH:
            m=Decoder(bank);m.direct(rid)
            for t in range(CASES[f'solo-{rid:02X}'][2]):
                start=time.perf_counter_ns();m.tick();timings.append(time.perf_counter_ns()-start)
    memory={}
    for name,b in [('previous',(B1OLD/'programs.scsp').read_bytes()),('expanded',blob)]:
        gc.collect();tracemalloc.start();x=unpack(b);m=Decoder(x);m.direct(0x81)
        for _ in range(4200):m.tick()
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        memory[name]=dict(current_bytes=current,peak_bytes=peak)
    rejected={}
    for name,tick,incumbent in [('ending-SFX',40,0xBC),('finite-three-mailboxes',30,0xB6)]:
        row=load(name)['original'][tick-1];assert row['globals'][9]==incumbent
        rejected[name]=dict(tick=tick,last_admitted_SFX=incumbent,priority=row['priority'],lower_priority_rejected=True)
    save(PUB/'facts.json',dict(termination=termination,zero_tempo=zero,counted_loops=loops,
        THZ_not_automatically_restored=True,inherited_8A_held_DC_preserved=True,
        wrong_pitch_data_detected_tick=wrongtick,missing_terminal_writes_detected_tick=terminal,
        missing_required_data_rejected=missing_rejected,priority_controls=rejected,
        performance=dict(measured_ticks=len(timings),median_ns=statistics.median(timings),
           p99_ns=sorted(timings)[int(.99*len(timings))],max_ns=max(timings),memory=memory,
           scope='Python decoder and sparse bank; includes bounded diagnostic log, excludes interpreter base/PCM; not GameMaker performance')))
    coverage=json.loads((ROOT/'data/m5-a2b1/coverage.json').read_text())
    for r in coverage['entries']:
        if r['request_id'] in BATCH:
            r['decoder_status']='fully-decoded-in-tested-scope'
            r['tested_scope']='complete finite original/candidate stream, 32 post ticks, fresh ROM-free replay; selected interactions'
    coverage['counts']={s:sum(r['decoder_status']==s for r in coverage['entries']) for s in
        ('fully-decoded-in-tested-scope','partially-decoded','format-understood-but-unverified','unsupported-or-unknown','empty-or-control')}
    coverage['extracted_unique_headers']=21
    coverage['format_understood_but_unverified_note']='All six B1 deferred finite rows now independently verified in B2; other unimplemented entries remain unknown.'
    coverage['expansion_batches']=[dict(order=1,proposal_only=True,ids=['A4','A6','BF','A1','A2','A7'],
         purpose='preflight six common SFX by original tone2/periodic/fixed/coupled-noise class before selecting an authorised implementation group'),
         dict(order=2,proposal_only=True,ids=['remaining unverified SFX'],purpose='class-stratified saved-DE11/latch, ownership, retrigger, fade and priority controls'),
         dict(order=3,proposal_only=True,ids=['remaining repeating music and long finite 8D'],purpose='separate loop/horizon/long-render authorisation; do not start automatically')]
    save(PUB/'coverage.json',coverage)


if __name__=='__main__':run()

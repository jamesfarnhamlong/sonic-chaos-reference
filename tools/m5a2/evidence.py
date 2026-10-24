"""Safe coverage, loop/termination facts, negative controls and resource figures."""
import copy
import gc
import json
from pathlib import Path
import statistics
import sys
import time
import tracemalloc

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from bank import pack,unpack,records,canonical
from decoder import Decoder
from m5a2.proof import CASES,IDS,OUT,PUB,save,sha,apply


def simulate(bank,case):
    initial,events,ticks=case
    m=Decoder(bank);m.direct(initial)
    rows=[]
    for t in range(1,ticks+1):
        for kind,v in events.get(t,[]):
            apply(m,kind,v)
        m.tick();rows.append(m.snapshot())
    return rows


def run():
    bank=unpack((OUT/'programs.scsp').read_bytes())
    catalogue=json.loads((ROOT/'data/m5/catalogue.json').read_text())['entries']
    entries=[]
    for r in catalogue:
        rid=r['request_id']
        if rid in IDS:
            status='fully-decoded-in-tested-scope'
            scope='4200 ticks, original recurrence and 419 subsequent ticks' if rid==0x81 else 'complete finite solo plus selected interactions'
        elif r['category']=='control' or 0x9B<=rid<=0x9F:
            status='empty-or-control'
            scope='00 and F8 tested; empty headers retained from R1, no new execution'
        else:
            status='unsupported-or-unknown'
            scope='header format understood; stream opcode/path/loop coverage NOT scanned or extracted'
        entries.append(dict(request_id=rid,request_hex=r['request_hex'],friendly_name=r['friendly_name'],
            category=r['category'],decoder_status=status,tested_scope=scope,
            unique_program_header=r.get('driver_header',{}).get('header_rom'),
            equal_solo_output_ids=r.get('equal_solo_command_output_ids',[]),
            header_alias_ids=r.get('header_alias_ids',[]),lifecycle=r['execution']['lifecycle']))
    statuses={s:sum(e['decoder_status']==s for e in entries) for s in
              ('fully-decoded-in-tested-scope','partially-decoded','format-understood-but-unverified','unsupported-or-unknown','empty-or-control')}
    save(PUB/'coverage.json',dict(total_request_ids=70,entries=entries,counts=statuses,
         format_understood_but_unverified_note='Header decoding applies to all indexed records. Unselected stream language coverage remains unknown; no speculative promotion.',
         request_vs_program_vs_output='IDs have independent priority/context; headers can alias; equal solo output does not establish equal contextual behavior.',
         extracted_unique_headers=len({bank['programs'][str(i)]['source_offset'] for i in IDS}),
         inherited_indexed_header_records=68,
         inherited_distinct_bounded_solo_emission_hashes=len({r['execution']['classified_prefix_write_sha256'] for r in catalogue if r['category']!='control'}),
         audible_output_count='not inferred from bounded emission fingerprints or header count',
         expansion_batches=[dict(order=1,ids=['84','85','86','87','89','8A','8E','94','96','97','98','9A'],
             purpose='remaining finite short music; verify used opcodes first, bound each original run'),
             dict(order=2,ids=['A1','A2','A4','A6','A7','A9','AA','AB','BF'],purpose='common tone and periodic-noise SFX; stratify clock/restore contexts'),
             dict(order=3,ids=['remaining SFX and aliases'],purpose='class-based admission/replacement/fade controls, not full Cartesian render'),
             dict(order=4,ids=['82','83','8B','8F','92','93','95'],purpose='repeating music after strict stream opcode scan and explicit loop budget'),
             dict(order=5,ids=['8D','8C','90','91'],purpose='separate long-content budget; no long renders in A2')]))
    def load(name):return json.loads((OUT/f'{name}.json').read_text())
    loop=load('THZ-loop')
    a,b=loop['candidate'][1092],loop['candidate'][3780]
    statekeys=['channel_bytes','globals','registers','latch','saved_noise','priority']
    repeated=all(a[k]==b[k] for k in statekeys)
    continuation=all(x['ports']==y['ports'] for x,y in zip(loop['candidate'][1093:1512],loop['candidate'][3781:4200]))
    original_loop=all(loop['original'][1092][k]==loop['original'][3780][k] for k in statekeys)
    assert repeated and continuation and original_loop
    ends={}
    for rid in IDS:
        if rid==0x81:continue
        name={0x88:'finite-88',0x99:'finite-99'}.get(rid,f'solo-{rid:02X}')
        rows=load(name)['candidate']
        ends[f'{rid:02X}']=next(i for i,r in enumerate(rows,1) if not any(f&128 for f in r['channels']))
    blocked=load('BC-A3-blocked')['candidate']
    blocked_reset=load('priority-blocked-reset')['candidate']
    # Priority rejection does not initialize A3 or reset the active B6 slots.
    assert blocked[34]['priority']==0x60 and blocked[34]['globals'][9]==0xBC
    assert blocked_reset[2]['priority']==0x68 and any(f&128 for f in blocked_reset[2]['channels'])
    recovery=load('multi-slot')['candidate']
    suppressed=[i+1 for i,r in enumerate(recovery) if r['channels'][1]&4]
    resumed=next(i+1 for i,r in enumerate(recovery) if i+1>max(suppressed) and r['channels'][1]&128 and not r['channels'][1]&20)
    held=load('finite88-fade-recovery')['candidate']
    heldticks=[i+1 for i,r in enumerate(held) if 40<=i+1<=47 and r['registers'][2][3]<15]
    assert len(heldticks)==8 and heldticks[0]==40 and heldticks[-1]==47
    physical=load('fixed-hold')['candidate']
    physicalticks=[i+1 for i,r in enumerate(physical) if r['channels'][6]&16 and r['channels'][6]&128 and r['registers'][2][3]<15]
    assert physicalticks==list(range(63,167))
    assert all(r['registers'][1]==5 and r['registers'][2][3]==2 for r in physical[62:166])
    assert physical[166]['registers'][2][3]==15 and physical[166]['channels'][6]&128
    assert not physical[167]['channels'][6]&128
    mutated=copy.deepcopy(bank)
    for k in mutated['data']:
        if 0x4436<=int(k)<0x44C2 and int(k)%2==0:mutated['data'][k]^=1
    wrong=simulate(unpack(pack(mutated)),CASES['finite-88'])
    correct=load('finite-88')['candidate']
    wrongtick=next(i+1 for i,(x,y) in enumerate(zip(wrong,correct)) if x['ports']!=y['ports'])
    class BrokenTermination(Decoder):
        def release(self,i):self.ch[i][0]=0
    m=BrokenTermination(bank);m.direct(0x88);badend=None
    for t in range(1,241):
        m.tick()
        if m.writes!=correct[t-1]['ports']:
            badend=t;break
    assert wrongtick and badend
    # Timing without tracing, then separate allocation measurement with tracing.
    times=[]
    for _ in range(3):
        m=Decoder(bank);m.direct(0x81)
        for t in range(4200):
            start=time.perf_counter_ns();m.tick();times.append(time.perf_counter_ns()-start)
    gc.collect();tracemalloc.start()
    measured=unpack((OUT/'programs.scsp').read_bytes());m=Decoder(measured);m.direct(0x81)
    for _ in range(4200):m.tick()
    current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    safe=dict(loop=dict(first_tick=1093,repeat_tick=3781,period_ticks=2688,
        full_channel_and_global_state_repeated=repeated,original_state_repeated=original_loop,
        subsequent_continuation_ticks=419,subsequent_emission_identical=continuation,
        original_control_flow_transfers_match=True),finite_inactive_ticks=ends,
        priority_blocked_controls=['BC then A3','B6 then F8'],music_tone1_suppressed_ticks=len(suppressed),music_tone1_read_recovered_tick=resumed,
        finite_fade_resumed_noise_ticks=heldticks,physical_inhibited_noise_hold_ticks=len(physicalticks),
        physical_noise_hold_interval=[63,166],wrong_pitch_data_detected_tick=wrongtick,
        missing_terminal_output_detected_tick=badend,
        performance=dict(measured_ticks=len(times),median_ns=statistics.median(times),p99_ns=sorted(times)[int(len(times)*.99)],
           max_ns=max(times),python_tracemalloc_current_bytes=current,python_tracemalloc_peak_bytes=peak,
           channel_storage_bytes=336,A1L_native_state_bytes=296,bank_and_decoder_allocation_scope='Python decoded sparse bank plus decoder state, bounded diagnostic transfer log; excludes PCM/trace arrays and interpreter base',
           GameMaker_decoder_performance='NOT MEASURED'),
        source=dict(parent='ad6aa301a7cc37a75f36a3d15c4804bcaa37b02b',management='ec0c979556404d000487dc1f7a44651cddcbf121',
           ROM=bank['source_sha256'],private_program_sha256=sha((OUT/'programs.scsp').read_bytes())))
    save(PUB/'facts.json',safe)
    save(OUT/'source-records.json',records(bank))
    print(json.dumps(safe,indent=2))


if __name__=='__main__':run()

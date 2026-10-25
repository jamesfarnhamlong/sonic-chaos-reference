"""C6 measured preflighted tone2, ownership, native continuity and frozen regression evidence."""
import argparse
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
import numpy as np
import audio1_psg_trace as T
from m5a2.bank import unpack, DecodeError as BankError
from m5a2c2.decoder import Decoder
from m5a2.decoder import DecodeError
from m5a2c3.original_noise import OriginalNoise
from m5a2c3.noise_diagnostic import observe,wav
from m5a2c6.proof import OUT,PUB,C5OLD,BATCH,ENDS,CASES,save


class AllControls(OriginalNoise):
    def __init__(self,rom):
        self.all_controls=[]
        super().__init__(rom)

    def _out(self,port,value):
        control=port&255 in (0x7E,0x7F) and value&128 and value>>4&7==6
        if control:before=self.native.state()
        super()._out(port,value)
        if control:
            after=self.native.state()
            self.all_controls.append(dict(tick=self.update,byte=value,mode=value&7,RNG_before=before[21],RNG_after=after[21],
                noise_counter_before=before[16],noise_counter_after=after[16],tone2_period=after[11],noise_period=after[12]))


def load(name):return json.loads((OUT/(name+'.json')).read_text())


def run(rom):
    bank=unpack((OUT/'programs.scsp').read_bytes());pre=json.loads((PUB/'preflight.json').read_text())['rows']
    gate=json.loads((PUB/'emission.json').read_text());pcm_gate=json.loads((PUB/'pcm.json').read_text())
    terminal={};native_context={};controls={};negatives={}
    # Complete decoded-data synthesis before creating the independent Z80 in every case.
    for name,case in CASES.items():
        pcm,native=observe(bank,case)
        initial,events,ticks=case;d=AllControls(rom);d.request(initial);reference=[]
        for tick in range(1,ticks+1):
            for kind,value in events.get(tick,[]):
                if kind=='request':d.request(value)
                elif kind=='fade':d.mem[0xDE09:0xDE0C]=bytes(value)
            d.tick();s=d.native.state()
            reference.append(dict(tick=tick,noise_control=s[6],noise_attenuation=s[7],tone2_register=s[4],tone2_period=s[11],
              noise_period=s[12],noise_counter=s[16],RNG=s[21],music_tone2_flags=d.mem[T.MUSIC_CH[2]],SFX_flags=[d.mem[a] for a in T.SFX_CH]))
        assert reference==native['frames'],name
        assert d.all_controls==native['controls'],name
        assert len(d.F3_states)==gate['cases'][name]['opcodes'].get('F3',0),name
        assert not pcm_gate['cases'][name]['register_counter_LFSR_failures']
        save(OUT/(name+'-native.json'),dict(candidate=native,original=dict(frames=reference,controls=d.F3_states)))
        d.close();f=native['frames'];c=[{k:v for k,v in r.items() if k!='qualification'} for r in d.F3_states];controls[name]=c
        muted=sum(a['RNG']!=b['RNG'] for a,b in zip(f,f[1:]) if a['noise_attenuation']==15 and b['noise_attenuation']==15)
        native_context[name]=dict(core_state_reference_exact=True,F3_count=len(c),F3_ticks=[x['tick'] for x in c],F3_modes=[x['mode'] for x in c],
            instant_F3_states_exact=True,all_F3_preserve_noise_countdown=all(x['noise_counter_before']==x['noise_counter_after'] for x in c),
            tone2_period_values=len({x['tone2_register'] for x in f}),noise_counter_range=[min(x['noise_counter'] for x in f),max(x['noise_counter'] for x in f)],
            RNG_changes_across_muted_frame_pairs=muted,maximum_simultaneous_SFX_slots=max(sum(bool(v&128) for v in x['SFX_flags']) for x in f))
    for rid,end in zip(BATCH,ENDS):
        name=f'solo-{rid:02X}';r=load(name);rows=r['original'];original=next(x for x in pre if x['request_id']==rid)
        assert next(i+1 for i,x in enumerate(rows) if not any(f&128 for f in x['channels']))==end
        assert len(rows)-end==32 and all(not x['ports'] and not any(f&128 for f in x['channels']) for x in rows[end:])
        assert all(x['registers']==rows[end-1]['registers'] for x in rows[end:]) and rows[-1]['registers'][2]==[15]*4
        assert original['post_completion_observed_ticks']==128 and original['post_inactive_physically_enabled_ticks']==0
        assert native_context[name]['F3_ticks']==[] and original['F3_executions']==0
        terminal[f'{rid:02X}']=dict(inactive_tick=end,candidate_post_ticks=32,original_preflight_post_ticks=128,final_attenuation=rows[-1]['registers'][2],post_writes=0,PCM_samples=len(rows)*735)
    # Repeat the accepted C3 dedup negative on the expanded bank; never used in playback.
    for rid in (0xB0,0xB7):
        case=(rid,{},39);good,gs=observe(bank,case);wrong,bs=observe(bank,case,deduplicate_noise_controls=True)
        badticks=sum(a['RNG']!=b['RNG'] for a,b in zip(gs['frames'],bs['frames']))
        error=int(np.abs(good.astype(np.int32)-wrong.astype(np.int32)).max())
        assert badticks==36 and error==16384
        second=gs['controls'][1];assert second['RNG_after']==32768 and second['RNG_before']!=32768
        assert second['noise_counter_before']==second['noise_counter_after']==21
        wav(OUT/f'C3-{rid:02X}-negative-dedup.wav',wrong)
        negatives[f'{rid:02X}']=dict(LFSR_mismatching_ticks=badticks,max_signed16_error=error,second_F3=second)
    class MissingTerminal(Decoder):
        def release(self,i):self.ch[i][0]=0
    class NoPitchModulation(Decoder):
        def pitch(self,c):return self.cw(c,11) if c[1]==0xC0 else super().pitch(c)
    class NoTableEnvelope(Decoder):
        def env(self,c):return 0 if c[1]==0xC0 else super().env(c)
    bad={}
    for rid in BATCH:
        expected=load(f'solo-{rid:02X}')['candidate'];bad[f'{rid:02X}']={}
        cls=NoPitchModulation if rid==0xB4 else NoTableEnvelope
        for label,wrong in [('wrong_pitch_or_envelope',cls),('missing_terminal',MissingTerminal)]:
            m=wrong(bank);m.direct(rid);fail=None
            for tick in range(1,len(expected)+1):
                m.tick()
                if m.writes!=expected[tick-1]['ports']:fail=tick;break
            assert fail is not None
            bad[f'{rid:02X}'][label+'_detected_tick']=fail
        start=next(r['header']['streams'][0]['stream_cpu'] for r in pre if r['request_id']==rid)
        for label in ['missing_required_byte','unsupported_command_E2']:
            altered=copy.deepcopy(bank)
            if label=='missing_required_byte':del altered['data'][str(start)]
            else:altered['data'][str(start)]=0xE2
            m=Decoder(altered);m.direct(rid)
            try:m.tick()
            except DecodeError as e:bad[f'{rid:02X}'][label]=dict(rejected=True,reason=str(e))
            else:raise AssertionError(label+' silently accepted')
    corrupt=bytearray((OUT/'programs.scsp').read_bytes());corrupt[-1]^=1
    try:unpack(bytes(corrupt))
    except BankError:corrupt_rejected=True
    else:raise AssertionError('corrupt new bank accepted')
    admissions={name:load(name)['SFX_admissions'] for name in CASES}
    assert admissions['tone2-priority-chain']==[[30,0xC2],[40,0xBD],[42,0xB4],[80,0xC2]]
    assert admissions['B4-block-lower']==[[1,0xB4],[40,0xBD]]
    assert admissions['B4-rejected-reset']==[[1,0xB4],[40,0xC2]]
    for name in ['B4-retrigger','BD-retrigger','C2-retrigger']:
        assert len(admissions[name])==4 and not controls[name]
    recovery={}
    for name in ['THZ-B4','THZ-BD','THZ-C2']:
        rows=load(name)['original'];i=2
        sup=[t+1 for t,r in enumerate(rows) if r['channels'][i]&4]
        nxt=next(t+1 for t,r in enumerate(rows) if t+1>max(sup) and r['channels'][i]&128 and not r['channels'][i]&20)
        recovery[name]=dict(suppression=[min(sup),max(sup)],next_read=nxt)
    interaction={}
    for name in ['white-A3-to-B4','periodic-B7-to-BD','fixed-B8-with-B4','coupled-A7-to-C2','noise-B0-over-C2','B4-BA-concurrent']:
        rows=load(name)['original'];overlap=[];audible=[];inhibited=[];held=[]
        for t,r in enumerate(rows,1):
            c=r['channel_bytes'];a=r['registers'][2]
            if c[5][0]&128 and c[6][0]&128:overlap.append(t)
            if a[2]<15 and a[3]<15:audible.append(t)
            if c[6][0]&16:inhibited.append(t)
            if c[6][0]&16 and a[3]<15:held.append(t)
        interaction[name]=dict(simultaneous_tone2_noise_slot_ticks=len(overlap),first_overlap_tick=overlap[0] if overlap else None,
            physical_tone2_and_noise_enabled_ticks=len(audible),noise_write_inhibited_ticks=len(inhibited),noise_write_inhibited_but_enabled_ticks=len(held),
            noise_write_inhibited_but_enabled_range=[min(held),max(held)] if held else None,
            maximum_simultaneous_SFX_slots=native_context[name]['maximum_simultaneous_SFX_slots'])
    assert interaction['fixed-B8-with-B4']['physical_tone2_and_noise_enabled_ticks']>0
    assert interaction['B4-BA-concurrent']['maximum_simultaneous_SFX_slots']==3
    # The wrong saved-pointer reload is detected even if the immediate port bytes agree.
    class SavedPointerReload(Decoder):
        def pitch(self,c):
            reload=c[1]==0xC0 and c[7]&128 and c[20]==1 and c[23]==1
            v=super().pitch(c)
            if reload:c[23]=self.byte(self.cw(c,16)+3)
            return v
    class NoTranspose(Decoder):
        def command(self,i,op,p):return p+1 if op==0xFB else super().command(i,op,p)
    class NoCountedBranch(Decoder):
        def command(self,i,op,p):return p+4 if op==0xF7 else super().command(i,op,p)
    operation_negatives={}
    for label,cls,rid in [('saved_pointer_reload',SavedPointerReload,0xB4),('omitted_transpose',NoTranspose,0xC2),('omitted_counted_branch',NoCountedBranch,0xC2)]:
        expected=load(f'solo-{rid:02X}')['candidate'];m=cls(bank);m.direct(rid);first_state=first_write=None
        for tick in range(1,len(expected)+1):
            m.tick();e=expected[tick-1]
            if first_state is None and [list(c) for c in m.ch]!=e['channel_bytes']:first_state=tick
            if first_write is None and m.writes!=e['ports']:first_write=tick
        assert first_state is not None
        operation_negatives[label]=dict(first_channel_state_difference=first_state,first_ordered_write_difference=first_write)
    # Historical class counts do not execute or promote any further ID.
    coverage=json.loads((ROOT/'data/m5-a2c5/coverage.json').read_text())
    for row in coverage['entries']:
        if row['request_id'] in BATCH:
            row.pop('original_only_preflight',None);row['decoder_status']='fully-decoded-in-tested-scope';row['tested_scope']='complete solo +32 post, original-only +128 physical check, selected tone2/envelope/phase/priority/noise/recovery contexts and ROM-free replay'
    coverage['counts']={s:sum(r['decoder_status']==s for r in coverage['entries']) for s in ('fully-decoded-in-tested-scope','partially-decoded','format-understood-but-unverified','unsupported-or-unknown','empty-or-control')}
    coverage['extracted_unique_headers']=39
    coverage['format_understood_but_unverified_note']='C6 B4/BD/C2 independently verified in scope; no original-only pending rows promoted without candidate proof.'
    p1c=json.loads((ROOT/'data/m5-p1c/coverage.json').read_text());unverified={r['request_id'] for r in coverage['entries'] if r['decoder_status']=='unsupported-or-unknown'}
    classes={k:[f'{i:02X}' for i in ids if i in unverified] for k,ids in p1c['classes'].items()}
    remaining=dict(source='accepted historical P1C original-only classes intersected with C6 unverified catalogue; no new execution of remaining IDs',classes=classes,counts={k:len(v) for k,v in classes.items()},remaining_music=sum(r['request_id'] in unverified and r['category']=='music' for r in coverage['entries']),qualification='Class metadata does not verify stream grammar, envelope paths or candidate execution of remaining IDs.')
    remaining['fresh_preflight_only']=[]
    remaining['historical_tone2_not_freshly_inspected']=[i for i in classes['tone2-only'] if i not in remaining['fresh_preflight_only']]
    coverage['remaining_original_classes']=remaining
    coverage['expansion_batches']=[dict(order=1,proposal_only=True,ids=[],purpose='strategic recommendation: separately authorised isolated GameMaker decoder/SCSP feasibility gate; no native work begun'),dict(order=2,proposal_only=True,ids=classes['tone2-only']+classes['coupled-white-noise-single-F3'],purpose='alternative bounded future catalogue preflight only after Manager selection; no extra IDs executed')]
    save(PUB/'coverage.json',coverage)
    times=[];active_times=[];idle_times=[]
    for _ in range(50):
        for rid in BATCH:
            m=Decoder(bank);m.direct(rid)
            for _ in range(CASES[f'solo-{rid:02X}'][2]):
                active=any(c[0]&128 for c in m.ch) or any(m.mail)
                start=time.perf_counter_ns();m.tick();elapsed=time.perf_counter_ns()-start;times.append(elapsed)
                (active_times if active else idle_times).append(elapsed)
    memory={}
    for name,blob in [('previous',(C5OLD/'programs.scsp').read_bytes()),('expanded',(OUT/'programs.scsp').read_bytes())]:
        gc.collect();tracemalloc.start();b=unpack(blob);m=Decoder(b);m.direct(0x81)
        for _ in range(4200):m.tick()
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();memory[name]=dict(current_bytes=current,peak_bytes=peak)
    save(PUB/'facts.json',dict(termination=terminal,native_diagnostics=native_context,F3_controls=controls,C3_duplicate_control_negative=negatives,negative_controls=bad,corrupt_SCSP_rejected=corrupt_rejected,noise_interactions=interaction,operation_negatives=operation_negatives,admissions=admissions,music_recovery=recovery,DE11_restore_contexts={n:load(n)['saved_noise_restores'] for n in CASES},remaining_original_classes=remaining,
      performance=dict(ticks=len(times),median_ns=statistics.median(times),p99_ns=sorted(times)[int(.99*len(times))],max_ns=max(times),active_ticks=len(active_times),active_median_ns=statistics.median(active_times),idle_ticks=len(idle_times),idle_median_ns=statistics.median(idle_times),memory=memory,scope='Python sparse bank/decoder and bounded diagnostics; excludes interpreter base/PCM; NOT GameMaker performance')))
    print('tone2 native continuity, envelope/terminal/data negatives, inherited dedup and operation negatives and catalogue PASS')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();run(T.load_rom(a.rom))

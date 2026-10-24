"""Bounded P0R feasibility diagnostics AFTER exact emission gate.

Reuses prior references. Only four small new MAME diagnostic targets (plus one
fresh-process carrier repeat). No new synthesis, long songs or phase bank.
All binary output is private; accepted P0/P1 package is read-only.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import tempfile
import numpy as np
import audio1_psg_trace as T
import audio1b_render as R
import audio1b_analyze as A
import audio1b_checks as C
from m5p0r_probe import Trace,OUT,PRIOR
from m5p0r_emission import EmissionModel
from m5p0r_proof import PUBLIC,save,compare
from m5p1_proof import comparison_metrics,mono,wav,spectral
PIN='36821f4cfb6a1b6e386f1b468504245c21c6e24a2cbb0cba4b268703c96334a0'
ROOT=Path(__file__).resolve().parents[1]

def sha(data):return hashlib.sha256(data).hexdigest()
def render(rows,label):
    assert sha(Path(os.environ['AUDIO1B_VGM2WAV']).read_bytes())==PIN
    assert len(rows)<=210,'bounded diagnostic only'
    vgm=R.build_vgm(rows);assert not R.vgm_matches(rows,vgm)
    folder=OUT/'pcm';folder.mkdir(parents=True,exist_ok=True)
    receipt=folder/f'{label}-render.json';path=folder/f'{label}.wav'
    key=sha(vgm+Path(os.environ['AUDIO1B_VGM2WAV']).read_bytes())
    if receipt.exists() and path.exists():
        meta=json.loads(receipt.read_text())
        if meta['cache_key']==key and sha(path.read_bytes())==meta['wav_sha256']:
            return mono(path),meta
    temp_root=OUT/'renderer-temp';temp_root.mkdir(parents=True,exist_ok=True)
    tempfile.tempdir=str(temp_root.resolve())
    t=time.perf_counter();pcm,_=R.render_libvgm(vgm,len(rows)*735,'MAME')
    assert len(pcm)>=len(rows)*735 and np.array_equal(pcm[:,0],pcm[:,1])
    pcm=pcm[:len(rows)*735,0]
    (folder/f'{label}.vgm').write_bytes(vgm);wav(folder/f'{label}.wav',pcm)
    meta=dict(ticks=len(rows),samples=len(pcm),seconds=time.perf_counter()-t,pcm_sha256=sha(pcm.tobytes()),vgm_sha256=sha(vgm),
        cache_key=key,wav_sha256=sha(path.read_bytes()))
    save(receipt,meta);return pcm,meta

def rows_for(rom,rid,ticks,events=None,saved_noise=None):
    d=Trace(rom)
    if saved_noise is not None:d.mem[0xDE11]=saved_noise
    d.request(rid);rows=[];states=[]
    for tick in range(1,ticks+1):
        for r in (events or {}).get(tick,[]):d.request(r)
        n=len(d.writes);d.tick();rows.append([v for _,v in d.writes[n:]]);states.append(d.psg.state())
    return rows,states

def force_carrier(rows,last_active_tick=138):
    # Existing pinned attenuation-forcing technique; retain every clock/control
    # write and the continuous sample index. Only noise amplitude is exposed.
    rows=R.attenuation_stem(rows,3);latch=0;out=[]
    for tick,row in enumerate(rows,1):
        fixed=[]
        for byte in row:
            if byte&128:latch=(byte>>4)&7
            if tick<=last_active_tick and latch==7:byte=(byte&0xF0) if byte&128 else 0
            fixed.append(byte)
        if tick==1:fixed=[0xF0]+fixed
        out.append(fixed)
    return out

def gain_carrier(carrier,attenuation):
    # Exact INTEGER volume ratios of the pinned MAME core, not a new synth.
    table=[int(8192*2**(-i/3)+.5) for i in range(15)]+[0]
    result=np.empty_like(carrier,dtype=np.int32)
    for i,level in enumerate(attenuation):
        sl=slice(i*735,(i+1)*735)
        result[sl]=np.rint(carrier[sl].astype(float)*table[level]/table[0]).astype(np.int32)
    return result

def phase_energy(reference,composed,ref_voices,cand_voices):
    def centered(x):return np.asarray(x,dtype=float).reshape(-1,735)-np.asarray(x,dtype=float).reshape(-1,735).mean(axis=1,keepdims=True)
    x=centered(reference);y=centered(composed);a=np.sqrt(np.mean(x*x,axis=1));b=np.sqrt(np.mean(y*y,axis=1));tick=int(np.argmax(np.abs(a-b)))
    rv=np.array([centered(v)[tick] for v in ref_voices]);cv=np.array([centered(v)[tick] for v in cand_voices])
    ref_self=float(np.mean(rv*rv,axis=1).sum());cand_self=float(np.mean(cv*cv,axis=1).sum())
    ref_cross=float(sum(2*np.mean(rv[i]*rv[j]) for i in range(4) for j in range(i+1,4)))
    cand_cross=float(sum(2*np.mean(cv[i]*cv[j]) for i in range(4) for j in range(i+1,4)))
    observed=float(np.mean(y[tick]**2)-np.mean(x[tick]**2));self_delta=cand_self-ref_self;cross_delta=cand_cross-ref_cross
    return dict(tick=tick+1,reference_mix_rms_lsb=float(a[tick]),composed_mix_rms_lsb=float(b[tick]),
        reference_voice_rms_lsb=list(map(float,np.sqrt(np.mean(rv*rv,axis=1)))),
        composed_voice_rms_lsb=list(map(float,np.sqrt(np.mean(cv*cv,axis=1)))),
        observed_energy_delta_lsb2=observed,self_energy_delta_lsb2=self_delta,cross_covariance_delta_lsb2=cross_delta,
        residual_energy_accounting_lsb2=observed-self_delta-cross_delta,
        cross_covariance_fraction=cross_delta/observed if observed else None,
        qualification='algebraic energy accounting; not a listening acceptance or proof that every phase error is harmless')

def run(rom):
    gate=json.loads((PUBLIC/'emission-results.json').read_text());assert gate['status']=='PASS'
    OUT.mkdir(parents=True,exist_ok=True)
    parent_zip=PRIOR/'SonicChaos_M5_P0P1_20261024_PROOF_PRIVATE.zip'
    assert sha(parent_zip.read_bytes())=='3adf174848e83fc40644a7e12142dbd44062c25c5dff674d09df031fe4b9881f'
    # Static source has no recoverable carrier where the original output was off.
    folder=PRIOR/'package/scenarios/fixed-B8-BC'
    original=mono(folder/'continuous.wav');old=mono(folder/'composed-experiment.wav')
    original_voices=[mono(folder/f'continuous-voice{c}.wav') for c in range(4)]
    old_voices=[mono(folder/f'composed-voice{c}.wav') for c in range(4)]
    source=mono(PRIOR/'package/diagnostic-B8/raw3.wav')
    zeros=[t for t in range(63,167) if not np.any(source[(t-30)*735:(t-29)*735])]
    # Bounded constant-volume carrier, same intrinsic B8 clock/control schedule.
    dry,dry_states=rows_for(rom,0xB8,159)
    carrier,carrier_meta=render(force_carrier(dry),'B8-carrier-diagnostic')
    repeat,repeat_meta=render(force_carrier(dry),'B8-carrier-repeat')
    assert np.array_equal(carrier,repeat)
    original_states=json.loads((folder/'private-timeline.json').read_text())['registers']
    revised=[v.astype(np.int32) for v in old_voices]
    desired=[s[2][3] for s in original_states[29:168]]
    gain=gain_carrier(carrier[:len(desired)*735],desired)
    revised[3][29*735:168*735]=gain
    new=sum(revised)
    assert np.abs(new).max()<32768
    wav(OUT/'pcm/B8-BC-carrier-composed.wav',new)
    wav(OUT/'pcm/B8-BC-carrier-noise.wav',revised[3])
    metric=comparison_metrics(original,new,original_voices,revised)
    def pitch(name,voices):
        rows=json.loads((OUT/f'{name}-comparison.json').read_text())['rows'][:len(voices[0])//735]
        return C.pitch_report([r['ports'] for r in rows],[np.repeat(v[:,None],2,axis=1) for v in voices])
    metric['pitch']=pitch('B8-BC',revised)
    hold=slice(62*735,166*735)
    hold_rms=A.tick_rms(revised[3][hold]);ref_rms=A.tick_rms(original_voices[3][hold])
    # Match entry conditions to isolate the issue from accepted arbitrary-entry phase.
    matched,matched_states=rows_for(rom,0xB8,159,{6:[0xBC]})
    matched_reference,matched_meta=render(R.attenuation_stem(matched,3),'B8-BC-matched-entry-reference')
    matched_prediction=gain_carrier(carrier,[s[2][3] for s in matched_states])
    wav(OUT/'pcm/B8-BC-matched-entry-predicted.wav',matched_prediction)
    difference=matched_prediction.astype(float)-matched_reference.astype(float)
    boundaries=np.arange(len(difference))%735==0
    # B6: preserve solo semantics; demonstrate a separate authentic DE11 context.
    b6_rows,b6_states=rows_for(rom,0xB6,47,saved_noise=0xE4)
    b6_new,b6_meta=render(R.attenuation_stem(b6_rows,1),'B6-music-restore-context-tone1')
    b6_old=mono(PRIOR/'package/library/B6/raw1.wav')
    changed=[i+1 for i in range(47) if not np.array_equal(b6_old[i*735:(i+1)*735],b6_new[i*735:(i+1)*735])]
    b6_diff=np.flatnonzero(b6_old.astype(np.int32)!=b6_new.astype(np.int32))
    b6_folder=PRIOR/'package/scenarios/B6-A0'
    b6_ref=mono(b6_folder/'continuous.wav');b6_oldmix=mono(b6_folder/'composed-experiment.wav')
    b6_refs=[mono(b6_folder/f'continuous-voice{c}.wav') for c in range(4)]
    b6_candidates=[mono(b6_folder/f'composed-voice{c}.wav').astype(np.int32) for c in range(4)]
    b6_candidates[1][29*735:56*735]=b6_new[:27*735]
    b6_mix=sum(b6_candidates);assert np.abs(b6_mix).max()<32768
    wav(OUT/'pcm/B6-A0-context-composed.wav',b6_mix)
    ba=PRIOR/'package/scenarios/BA-partial'
    ba_energy=phase_energy(mono(ba/'continuous.wav'),mono(ba/'composed-experiment.wav'),
        [mono(ba/f'continuous-voice{c}.wav') for c in range(4)],[mono(ba/f'composed-voice{c}.wav') for c in range(4)])
    # BA's false-audible tick has the same dry DE11=0 data-latch mechanism.
    ba_rows,ba_states=rows_for(rom,0xBA,45,saved_noise=0xE4)
    ba_new,ba_meta=render(R.attenuation_stem(ba_rows,1),'BA-music-restore-context-tone1')
    ba_old=mono(PRIOR/'package/library/BA/raw1.wav')
    ba_changed=[i+1 for i in range(45) if not np.array_equal(ba_old[i*735:(i+1)*735],ba_new[i*735:(i+1)*735])]
    ba_candidates=[mono(ba/f'composed-voice{c}.wav').astype(np.int32) for c in range(4)]
    ba_refs=[mono(ba/f'continuous-voice{c}.wav') for c in range(4)]
    # AC replaces tone1 at36; only BA's six originally occupied blocks change.
    ba_candidates[1][29*735:35*735]=ba_new[:6*735]
    ba_mix=sum(ba_candidates);assert np.abs(ba_mix).max()<32768
    wav(OUT/'pcm/BA-partial-context-composed.wav',ba_mix)
    results=dict(register_gate='PASS before PCM work',parent_proof_preserved=True,static_B8_zero_source_ticks_during_required_hold=zeros,
        carrier_experiment=dict(production_approved=False,format='44100Hz signed16 mono;159ticks',
            own_cursor_never_restarted_at_hold=True,deterministic=True,render=carrier_meta,repeat_render=repeat_meta,
            continuous_entry_phase='original arbitrary music-entry phase not recreated by a standalone carrier',
            before=json.loads((ROOT/'data/m5-proof/coupled-noise.json').read_text())['fixed-B8-BC'],after=metric,
            held_ticks_restored=int(np.count_nonzero(hold_rms>1)),required_held_ticks=104,
            held_tick_rms_correlation=A.corr(ref_rms,hold_rms),held_noise_rms_mean_reference_lsb=float(np.mean(ref_rms)),
            held_noise_rms_mean_candidate_lsb=float(np.mean(hold_rms)),noise_reference=spectral(original_voices[3]),noise_candidate=spectral(revised[3]),
            matched_entry=dict(render=matched_meta,sample_max_error_lsb=int(np.abs(difference).max()),
                rms_error_lsb=float(np.sqrt(np.mean(difference**2))),sample_equal=bool(np.array_equal(matched_reference,matched_prediction)),
                max_error_outside_first_sample_of_tick_lsb=int(np.abs(difference[~boundaries]).max()),
                nonboundary_samples_over5_lsb=int(np.count_nonzero(np.abs(difference[~boundaries])>5)),
                waveform_correlation=A.corr(matched_reference,matched_prediction),
                envelope_correlation=A.corr(A.tick_rms(matched_reference),A.tick_rms(matched_prediction)))),
        B6_context=dict(render=b6_meta,changed_source_ticks=changed,correct_context_attenuation_tick16=b6_states[15][2][1],
            changed_samples_in_tick17=int(np.count_nonzero((b6_diff>=16*735)&(b6_diff<17*735))),
            original_solo_not_rewritten=True,before=json.loads((ROOT/'data/m5-proof/coupled-noise.json').read_text())['B6-A0'],
            after=dict(comparison_metrics(b6_ref,b6_mix,b6_refs,b6_candidates),pitch=pitch('B6-A0',b6_candidates))),
        BA_energy=ba_energy,BA_context=dict(render=ba_meta,changed_source_ticks=ba_changed,
            correct_context_attenuation_source_tick5=ba_states[4][2][1],
            before=json.loads((ROOT/'data/m5-proof/coupled-noise.json').read_text())['BA-partial'],
            after=dict(comparison_metrics(mono(ba/'continuous.wav'),ba_mix,ba_refs,ba_candidates),pitch=pitch('BA-partial',ba_candidates)),
            after_energy=phase_energy(mono(ba/'continuous.wav'),ba_mix,ba_refs,ba_candidates)),
        render_count=5,overall='HOLD for full M5; bounded carrier extension not the existing static-stem representation',
        A3_constant_DC_qualification='unchanged; original first735 samples constant -4096, AC RMS0',native_listening='NOT PERFORMED')
    assert sha(parent_zip.read_bytes())=='3adf174848e83fc40644a7e12142dbd44062c25c5dff674d09df031fe4b9881f'
    save(PUBLIC/'composition-feasibility.json',results)
    print(json.dumps(dict(zeros=zeros,held_restored=results['carrier_experiment']['held_ticks_restored'],
        B8_before=results['carrier_experiment']['before']['envelope_correlation'],B8_after=metric['envelope_correlation'],
        B6_changed_ticks=changed,BA_before=ba_energy,BA_after=results['BA_context']['after']['envelope_correlation'],
        matched_entry=results['carrier_experiment']['matched_entry']),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();run(T.load_rom(a.rom))

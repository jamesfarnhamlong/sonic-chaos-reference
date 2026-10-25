"""C5 PCM gate using unchanged B1 synthesis and immutable A2/B1 PCM."""
import json
from pathlib import Path
import sys
import tempfile
import wave

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tools/m5a0')]
import numpy as np
from m5a2.bank import unpack
from backend import PSG
import audio1b_render as R
from m5a2c2.runtime import render,wav
from m5a2c5.proof import CASES,OUT,PUB,OLD,save,sha,prior_path,prior_pcm_path
from m5a2.pcm import diff,DLL,A0,EXE,PIN


def read(path):
    with wave.open(str(path)) as w:
        assert w.getnchannels()==1 and w.getframerate()==44100
        return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')


def render_ports(rows,dll):
    with PSG(dll) as chip:
        blocks=[]
        for row in rows:chip.write(row);blocks.append(chip.render())
    return np.concatenate(blocks)


def original_pcm(rows):
    vgm=R.build_vgm(rows);assert not R.vgm_matches(rows,vgm)
    pcm,_=R.render_libvgm(vgm,len(rows)*735,'MAME',exe=str(EXE))
    assert len(pcm)>=len(rows)*735 and np.array_equal(pcm[:,0],pcm[:,1])
    return pcm[:len(rows)*735,0],vgm


def run():
    temp=OUT/'renderer-temp';temp.mkdir(parents=True,exist_ok=True);tempfile.tempdir=str(temp.resolve())
    assert sha(EXE.read_bytes())==PIN
    assert sha(DLL.read_bytes())=='47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65'
    bank=unpack((OUT/'programs.scsp').read_bytes());gate=json.loads((PUB/'emission.json').read_text())
    assert all(c['status']=='PASS' for c in gate['cases'].values())
    results={};regressions={}
    for name in gate['cases']:
        case=json.loads((OUT/(name+'.json')).read_text())['case']
        initial,events,ticks=case;schedule=dict(initial=initial,events=events,ticks=ticks)
        pcm,states=render(bank,schedule,DLL);split,splitstates=render(bank,schedule,DLL,split=True)
        assert np.array_equal(pcm,split) and states==splitstates
        if prior_path(name):
            prior_folder,prior_name=prior_pcm_path(name)
            expected=read(prior_folder/'pcm'/prior_name/'candidate.wav')
            assert np.array_equal(pcm,expected)
            regressions[name]=dict(ticks=ticks,PCM_identical_to_accepted_parent=True,partition_invariant=True)
            continue
        folder=OUT/'pcm'/name;folder.mkdir(parents=True,exist_ok=True)
        save(folder/'schedule.json',schedule);wav(folder/'candidate.wav',pcm)
        rows=json.loads((OUT/(name+'.json')).read_text())
        ports=[r['ports'] for r in rows['original']];candidate_ports=[r['ports'] for r in rows['candidate']]
        refstates=[]
        with PSG(A0) as chip:
            for row in ports:chip.write(row);chip.render();refstates.append(chip.state()[:22])
        statefail=[i+1 for i,(x,y) in enumerate(zip(states,refstates)) if x[:22]!=y]
        ref,vgm=original_pcm(ports);wav(folder/'reference.wav',ref);(folder/'reference.vgm').write_bytes(vgm)
        voices={}
        for voice in range(4):
            v=render_ports(R.attenuation_stem(candidate_ports,voice),DLL)
            o,_=original_pcm(R.attenuation_stem(ports,voice))
            wav(folder/f'candidate-voice{voice}.wav',v);wav(folder/f'reference-voice{voice}.wav',o)
            vr=np.sqrt(np.mean(v.astype(float).reshape(-1,735)**2,axis=1))
            ore=np.sqrt(np.mean(o.astype(float).reshape(-1,735)**2,axis=1))
            voices[str(voice)]=dict(**diff(v,o),block_RMS_envelope_max_delta=float(abs(vr-ore).max()))
        metric=diff(pcm,ref)
        results[name]=dict(ticks=ticks,samples=len(pcm),continuous_mix=metric,voices=voices,
            register_counter_LFSR_failures=statefail,partition_invariant=True,
            PCM_sha256=sha(pcm.tobytes()),reference_PCM_sha256=sha(ref.tobytes()),
            max_over_mix_and_voices=max([metric['max_lsb']]+[x['max_lsb'] for x in voices.values()]),
            attenuation_register_and_driver_envelope_state_exact=True)
        print(name,metric,'voice max',max(x['max_lsb'] for x in voices.values()),'state failures',len(statefail),flush=True)
    save(PUB/'pcm.json',dict(cases=results,regressions=regressions,A1L_DLL_sha256=sha(DLL.read_bytes()),
        original_renderer_sha256=PIN,thresholds_changed=False,clock_hz=3546893,rate=44100,tick_samples=735,
        original_PCM_identity_claim=False,listening='NOT PERFORMED'))
    assert all(not x['register_counter_LFSR_failures'] for x in results.values())
    assert all(x['max_over_mix_and_voices']<=5 for x in results.values()),'NEW discrepancy outside previously observed range: Manager investigation required'


if __name__=='__main__':run()

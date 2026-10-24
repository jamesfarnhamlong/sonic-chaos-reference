"""Continuous PCM comparison AFTER independent decoder/original emission gate."""
import json
import os
from pathlib import Path
import sys
import time
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools'),str(ROOT/'tools/m5a0'),str(Path(__file__).parent)]
import numpy as np
from m5a2.proof import CASES, OUT, PUB, save, sha
from bank import unpack
from runtime import render, wav
from backend import PSG
import audio1b_render as R

DLL = ROOT.parent/'sonic-chaos-reference-m5-a1l/build/m5-a1l/psg-a1l.dll'
A0 = ROOT.parent/'sonic-chaos-reference-m5-a0/build/m5-a0/psg-a0.dll'
EXE = ROOT.parent/'sonic-chaos-reference-m4/build/m4/renderer/libvgm-build/bin/vgm2wav.exe'
PIN = '36821f4cfb6a1b6e386f1b468504245c21c6e24a2cbb0cba4b268703c96334a0'


def diff(a,b):
    e = a.astype(np.int32)-b.astype(np.int32)
    return dict(max_lsb=int(abs(e).max()), rms_lsb=float(np.sqrt(np.mean(e.astype(float)**2))),
                unequal_samples=int(np.count_nonzero(e)))


def run():
    temporary = OUT/'renderer-temp'
    temporary.mkdir(parents=True,exist_ok=True)
    tempfile.tempdir = str(temporary.resolve())
    assert sha(EXE.read_bytes()) == PIN
    assert DLL.exists() and A0.exists()
    gate = json.loads((PUB/'emission.json').read_text())
    assert all(c['status']=='PASS' for c in gate['cases'].values())
    bank = unpack((OUT/'programs.scsp').read_bytes())
    results = {}
    for name, (initial, events, ticks) in CASES.items():
        schedule = dict(initial=initial,events={str(k):v for k,v in events.items()},ticks=ticks)
        folder = OUT/'pcm'/name
        folder.mkdir(parents=True,exist_ok=True)
        save(folder/'schedule.json',schedule)
        start = time.perf_counter()
        pcm, states = render(bank,schedule,DLL)
        elapsed = time.perf_counter()-start
        fresh, freshstates = render(bank,schedule,DLL,split=True)
        assert np.array_equal(pcm,fresh) and states==freshstates
        # Only the reference path opens original-driver rows.
        original = json.loads((OUT/f'{name}.json').read_text())['original']
        ports = [r['ports'] for r in original]
        refstates, aligned = [], []
        with PSG(A0) as chip:
            for row in ports:
                chip.write(row)
                chip.render()
                refstates.append(chip.state()[:22])
        statefail = [i+1 for i,(a,b) in enumerate(zip(states,refstates)) if a[:22]!=b]
        vgm = R.build_vgm(ports)
        assert not R.vgm_matches(ports,vgm)
        ref, _ = R.render_libvgm(vgm,ticks*735,'MAME',exe=str(EXE))
        assert len(ref)>=len(pcm) and np.array_equal(ref[:,0],ref[:,1])
        ref = ref[:len(pcm),0]
        wav(folder/'candidate.wav',pcm)
        wav(folder/'original-MAME.wav',ref)
        (folder/'original.vgm').write_bytes(vgm)
        metrics = diff(pcm,ref)
        results[name] = dict(ticks=ticks,samples=len(pcm),versus_original_MAME=metrics,
            core_register_counter_lfsr_failures=statefail,partition_invariant=True,
            seconds_decoder_and_synthesis=elapsed,pcm_sha256=sha(pcm.tobytes()),
            reference_pcm_sha256=sha(ref.tobytes()),within_previously_approved_5_lsb=metrics['max_lsb']<=5)
        print(name,metrics,'core failures',len(statefail),flush=True)
    save(PUB/'pcm.json',dict(cases=results,A1L_dll_sha256=sha(DLL.read_bytes()),
        original_renderer_sha256=PIN,A0_diagnostic_sha256=sha(A0.read_bytes()),
        scope='PAL 3546893 Hz / 44100 mono / 735 frames per driver tick; continuous state',
        listening='NOT PERFORMED',threshold_changed=False))


if __name__ == '__main__': run()

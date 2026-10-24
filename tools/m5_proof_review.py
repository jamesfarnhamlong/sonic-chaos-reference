"""Review EXISTING private proof files and rebuild its manifest/ZIP; no renderer.

Run after P0/P1. Retains failures, records the HOLD gate and source hashes.
No ROM or GameMaker file is read or changed by this review.
"""
import hashlib
import json
from pathlib import Path
import time
import zipfile
import numpy as np
from m5p1_proof import PRIVATE,OUT,PUBLIC,mono,save,sha,directory_bytes,PIN

def review():
    start=time.perf_counter()
    timeline=json.loads((OUT/'scenarios/fixed-B8-BC/private-timeline.json').read_text())
    held=[i+1 for i,(state,flags) in enumerate(zip(timeline['registers'],timeline['flags'])) if i+1>=63 and flags[6]&16 and state[2][3]<15]
    assert held==list(range(63,167))
    a3=mono(OUT/'library/A3/raw3.wav')[:735].astype(np.float64)
    diagnostics=dict(fixed_rate_hold=dict(first_tick=63,last_tick=166,ticks=len(held),
        noise_control=5,held_attenuation=2,active_noise_write_inhibited=True,
        explanation='F2 tone2 completion emits tone2-off (DF), marks noise bit4 but does not emit noise-off; last PSG noise output persists. Envelope end emits noise-off at167.'),
        a3_duration_proxy=dict(raw_register_vs_AC_RMS_gate='FAIL',mismatched_ticks=1,first_tick_min_lsb=int(a3.min()),
            first_tick_max_lsb=int(a3.max()),first_tick_ac_rms_lsb=float(np.sqrt(np.mean((a3-a3.mean())**2))),
            interpretation='constant DC in first735 samples despite non-off attenuation; register gate is not equivalent to oscillating/audible output. No PCM altered.'),
        b6_attenuation_projection_mismatches=1,b6_status='unresolved single-tick boundary; preserved, not waived',
        generic_fade='retained approved approximation; not register/sample parity',
        hardware_listening='NOT PERFORMED')
    save(PUBLIC/'diagnostics.json',diagnostics)
    gate=dict(overall='HOLD',bounded_ownership_dispatch='PASS',complete_P0_output_state='HOLD',
        composition_parity='FAIL',solo_format_determinism_pitch='PASS',
        solo_A3_register_vs_AC_RMS_proxy='FAIL one startup tick; constant DC measured',
        four_voice_residual='EXPERIMENT reconstructs solo mixes exactly; not an approved runtime algorithm',
        chunk_bytes_and_addressing='PASS',native_cache='NOT TESTED',
        blockers=['Write-inhibit is not PSG mute; fixed-rate B8+BC candidate loses held noise output104 ticks',
            'One B6 tone1 attenuation projection tick remains unresolved',
            'Fresh standalone oscillator/noise phases and coherent mix interference remain unlike continuous execution'],
        p2_p3='NOT AUTHORIZED',game_maker_changes=False,further_rendering='STOPPED; review uses existing captures only')
    save(PUBLIC/'gate.json',gate);save(OUT/'FINAL_GATE_HOLD.json',dict(gate=gate,diagnostics=diagnostics))
    combined=json.loads((OUT/'proof-results.json').read_text())
    combined['p0']=json.loads((PUBLIC/'p0-result.json').read_text());combined['final_gate']=gate
    save(OUT/'proof-results.json',combined)
    (OUT/'README_PRIVATE.txt').write_text(
        'M5 P0/P1 PRIVATE PROOF: OVERALL HOLD / COMPOSITION FAIL.\n'
        'Ownership/dispatch projection passes; this is NOT complete output-state parity.\n'
        'B8+BC demonstrates104 ticks of lost held noise in the candidate composition.\n'
        'A3 AC-RMS duration proxy has one startup-tick FAIL; original PCM retained.\n'
        'Reference and deliberately failing experimental compositions are included for review.\n'
        'No listening/hardware/native cache acceptance. No GameMaker release. No P2/P3.\n'
        'Original derived audio and timing metadata: PRIVATE, DO NOT PUBLISH.\n'
        'No original ROM or renderer binary included. Authenticate every manifest file.\n',encoding='utf-8')
    source_names=('m5p0_model.py','m5p0_proof.py','m5p1_proof.py','m5_proof_review.py')
    root=Path(__file__).resolve().parents[1]
    sources={f'tools/{name}':sha((root/'tools'/name).read_bytes()) for name in source_names}
    save(OUT/'source-provenance.json',dict(research_parent='7d700d0f2d51812d48d9743443e688bc1f9c5793',source_sha256=sources,
        pins=dict(renderer_binary_sha256=PIN,libvgm_commit='a6eed945ecf4e5a25cf82004779c6f7e4fd5c319',psg_clock=3546893,rate=44100,bits=16)))
    manifest=dict(rom_sha256='eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607',
        renderer_sha256=PIN,rate=44100,bits=16,ticks_per_second=60,clock=3546893,gate=gate,files={})
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and path!=OUT/'manifest.json':
            if path.suffix.lower() not in ('.json','.txt','.wav','.vgm','.pcm'):raise ValueError('unexpected private package member type')
            manifest['files'][path.relative_to(OUT).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha(path.read_bytes()))
    save(OUT/'manifest.json',manifest)
    archive=PRIVATE/'SonicChaos_M5_P0P1_20261024_PROOF_PRIVATE.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for rel in manifest['files']:z.write(OUT/rel,rel)
        z.write(OUT/'manifest.json','manifest.json')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(manifest['files'])+1
        for rel,v in manifest['files'].items():assert sha(z.read(rel))==v['sha256']
    receipt=dict(archive_name=archive.name,sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,
        members=len(manifest['files'])+1,crc_and_hashes='PASS',manifest_sha256=sha((OUT/'manifest.json').read_bytes()),overall_gate='HOLD')
    save(PUBLIC/'private-package-receipt.json',receipt)
    budget=json.loads((PUBLIC/'measured-budget.json').read_text())
    budget.update(archive_bytes=archive.stat().st_size,package_payload_bytes=directory_bytes(OUT),scratch_bytes=directory_bytes(PRIVATE),
        metadata_review_archive_seconds=time.perf_counter()-start)
    speed=budget['aggregate_timeline_per_wall_second']
    budget['long_target_extrapolations']={
        name:dict(prefix_body_ticks=n,five_renderer_pass_timeline_seconds=n/60*5,
            naive_wall_seconds_at_measured_rate=n/60*5/speed,one_mono_body_bytes=n*735*2,
            caution='not rendered; startup overhead, disk, float-array peaks and seam scan can change cost substantially')
        for name,n in (('90',807+19768),('91',395+32256),('8C',497+80640))}
    save(PUBLIC/'measured-budget.json',budget)
    print(json.dumps(dict(gate=gate['overall'],package=receipt),indent=2))

if __name__=='__main__':review()

"""Finalize safe P0R boundaries/preservation and PRIVATE sidecar; no rendering."""
import hashlib
import json
from pathlib import Path
import zipfile
from m5p0r_proof import ROOT,PUBLIC,OUT,PRIOR,save

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    parent=PRIOR/'SonicChaos_M5_P0P1_20261024_PROOF_PRIVATE.zip'
    expected='3adf174848e83fc40644a7e12142dbd44062c25c5dff674d09df031fe4b9881f'
    assert sha(parent)==expected
    old=json.loads((PRIOR/'package/M4-preservation.json').read_text())['sha256']
    assert all(sha(Path(p))==v for p,v in old.items())
    gate=json.loads((PUBLIC/'emission-results.json').read_text());assert gate['status']=='PASS'
    def rows(name):return json.loads((OUT/f'{name}-comparison.json').read_text())['rows']
    b8=rows('B8-BC');b6=rows('B6-A0');solo=rows('B6-solo-context');ba=rows('BA-partial')
    held=[r for r in b8 if 63<=r['tick']<=166]
    assert len(held)==104 and all(r['original'][1]==5 and r['original'][2][3]==2 and r['model'][1]==5 and r['model'][2][3]==2 for r in held)
    boundaries=dict(rom_sha256=gate['rom_sha256'],management='293b5a32a7c8af25117c6c88d7e383d3bb36b161',
        held_noise=dict(first_tick=63,last_tick=166,ticks=104,control=5,attenuation=2,
            ordinary_writes_inhibited=True,noise_stream_active_at167=bool(b8[166]['channels'][6]&128),
            terminal_off_tick167_attenuation=b8[166]['original'][2][3],stream_finished168=not bool(b8[167]['channels'][6]&128)),
        B6=dict(original_tick44_attenuation=b6[43]['original'][2][1],original_tick45_attenuation=b6[44]['original'][2][1],
            corrected_tick45_attenuation=b6[44]['model'][2][1],prior_dry_projection_tick45=0,
            authentic_solo_tick16_attenuation=solo[15]['original'][2][1],corrected_solo_tick16_attenuation=solo[15]['model'][2][1],
            root_cause='context-dependent saved DE11 restore byte0 is data to last latched tone1 attenuation in solo capture; in music a valid noise latch E4 is restored',
            cpu_locations=dict(tone1_attenuation_out='4543',restore_load='47F0',restore_out='47F3',own_off='4810')),
        BA=dict(original_tick34_attenuation=ba[33]['original'][2][1],corrected_tick34_attenuation=ba[33]['model'][2][1],
            prior_static_stem_attenuation=0,root_cause='same solo restore-byte/data-latch contamination; previous audible-only guard omitted false-audible cases'),
        preservation=dict(parent_proof_sha256=expected,parent_proof_unchanged=True,M4_payloads_checked=len(old),M4_payloads_unchanged=True),
        recommendation='CONDITIONAL GO only for a separately authorized small carrier/context-asset proof batch; full M5 and GameMaker remain HOLD',
        full_static_stem_architecture='insufficient unchanged; zero carrier samples cannot be recovered by gain or gating; finite fixed-rate carrier extension demonstrated, not universal')
    save(PUBLIC/'boundary-closure.json',boundaries)
    (OUT/'README_PRIVATE.txt').write_text('M5-P0R PRIVATE SIDECAR. No ROM/core binary. Do not publish WAV/VGM/dry intent streams.\nExact bounded emission gate passes; current baked static stems remain insufficient for complete M5.\nCarrier and music-restore-context files are experiments, not accepted runtime assets.\nOriginal P0/P1 package and M4 PCM preserved. No P2/P3 or GameMaker permission.\n',encoding='utf-8')
    sources={p.name:sha(p) for p in (ROOT/'tools').glob('m5p0r_*.py')}
    manifest=dict(parent_proof_sha256=expected,source_sha256=sources,
        research_parent='e8494d52ec30b9bc86d29f5c4f4824f4586e21e3',management='293b5a32a7c8af25117c6c88d7e383d3bb36b161',
        rom_sha256=gate['rom_sha256'],renderer_sha256='36821f4cfb6a1b6e386f1b468504245c21c6e24a2cbb0cba4b268703c96334a0',
        rate=44100,bits=16,driver_ticks_per_second=60,psg_clock=3546893,
        register_gate='PASS',production='HOLD pending Manager review',files={})
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name!='sidecar-manifest.json':
            if p.suffix.lower() not in ('.json','.txt','.wav','.vgm'):raise ValueError('unexpected sidecar member')
            manifest['files'][p.relative_to(OUT).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p))
    save(OUT/'sidecar-manifest.json',manifest)
    archive=ROOT/'build/SonicChaos_M5_P0R_20261024_DIAGNOSTIC_PRIVATE.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for rel in manifest['files']:z.write(OUT/rel,rel)
        z.write(OUT/'sidecar-manifest.json','sidecar-manifest.json')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(manifest['files'])|{'sidecar-manifest.json'}
        assert all(hashlib.sha256(z.read(k)).hexdigest()==v['sha256'] for k,v in manifest['files'].items())
    receipt=dict(archive_name=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,members=len(manifest['files'])+1,
        crc_and_member_hashes='PASS',parent_proof_unchanged=True,manifest_sha256=sha(OUT/'sidecar-manifest.json'))
    save(PUBLIC/'private-sidecar-receipt.json',receipt);print(json.dumps(dict(boundaries=boundaries,sidecar=receipt),indent=2))

if __name__=='__main__':run()

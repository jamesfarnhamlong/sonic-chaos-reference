"""Private A2 evidence archive; no DLL, ROM or inherited package mutation."""
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from m5a2.proof import CASES,OUT,PUB,save,sha
from m5p1c import preservation


def run():
    preserved=preservation()
    older=[('sonic-chaos-reference-m5-a0/build/SonicChaos_M5_A0_20261024_STATEFUL_PRIVATE.zip',
            '580725052986dcf5b79718fd2dd1ebfe93f09ed5ba0b9db879cea53c8343f004'),
           ('sonic-chaos-reference-m5-a1l/build/SonicChaos_M5_A1L_20261024_HELPER_EXPERIMENT_PRIVATE.zip',
            '426c884c7e6d9b16437e5186386b0930cb3034cc356b6ac6c3ee81e0172178e2'),
           ('sonic-chaos-reference-m5-p1c/build/SonicChaos_M5_P1C_20261024_PROOF_PRIVATE.zip',
            'fbd5264b6c07ed9bb04d63350a7c9e8a0b854a19208012f92adc4d96f9a9984c')]
    for path,expected in older:
        p=ROOT.parent/path
        assert sha(p.read_bytes())==expected
        preserved['private_archives'].append(dict(name=p.name,sha256=expected,unchanged=True))
    poc=ROOT.parent/'SonicChaos_POC_release_m4'
    assert subprocess.check_output(['git','-C',str(poc),'rev-parse','HEAD'],text=True).strip()=='11bff34356d5f5d979218896dc95fdc4bb265eae'
    assert not subprocess.check_output(['git','-C',str(poc),'status','--porcelain'],text=True).strip()
    preserved['accepted_POC_clean']=True
    emission=json.loads((PUB/'emission.json').read_text())
    assert len(emission['cases'])==20 and all(c['status']=='PASS' for c in emission['cases'].values())
    assert json.loads((PUB/'isolation.json').read_text())['PCM_file_identical']
    members={}
    for name in ('bank.json','programs.scsp','source-records.json'):
        members['private/'+name]=OUT/name
    for name in CASES:
        members['private/captures/'+name+'.json']=OUT/(name+'.json')
        for p in (OUT/'pcm'/name).iterdir():
            if p.is_file():members['private/pcm/'+name+'/'+p.name]=p
    safe=[]
    for directory,pattern in [('tools/m5a2','*.py'),('tests','test_m5a2.py'),('docs','m5-a2-*.md'),('data/m5-a2','*.json')]:
        for p in sorted((ROOT/directory).glob(pattern)):
            if p.name in ('private-package.json','verification.json'):continue
            key='safe/'+p.relative_to(ROOT).as_posix();members[key]=p;safe.append(p.relative_to(ROOT).as_posix())
    payload={name:sha(p.read_bytes()) for name,p in sorted(members.items())}
    manifest=dict(version=1,scope='PRIVATE bounded decoder proof; no DLL or complete audio catalogue',
                  sha256=payload,preservation=preserved,
                  stale_exploratory_failure_files='retained locally; excluded from this final archive')
    archive=ROOT.parent/'releases/SonicChaos_M5_A2_20261024_DECODER_FINAL_PRIVATE.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,p in sorted(members.items()):z.write(p,name)
        z.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(sha(z.read(n))==h for n,h in payload.items())
        count=len(z.infolist());total=sum(i.file_size for i in z.infolist())
    receipt=dict(name=archive.name,sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,
                 members=count,payload_bytes=total,CRC_and_all_member_hashes='PASS',
                 program_data_sha256=sha((OUT/'programs.scsp').read_bytes()),
                 prior_preservation=preserved,contains_DLL=False,contains_ROM=False,
                 safe_source_inventory=safe)
    save(PUB/'private-package.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('prior_preservation','safe_source_inventory')},indent=2))


if __name__=='__main__':run()

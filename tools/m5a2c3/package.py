"""New private evidence package, read-only preservation of accepted milestones."""
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5a2c3.proof import OUT,PUB,OLD,B1OLD,B2OLD,C1OLD,C2OLD,save,sha
from m5p1c import preservation


def run():
    preserved=preservation()
    previous=[('sonic-chaos-reference-m5-a0/build/SonicChaos_M5_A0_20261024_STATEFUL_PRIVATE.zip',
               '580725052986dcf5b79718fd2dd1ebfe93f09ed5ba0b9db879cea53c8343f004'),
              ('sonic-chaos-reference-m5-a1l/build/SonicChaos_M5_A1L_20261024_HELPER_EXPERIMENT_PRIVATE.zip',
               '426c884c7e6d9b16437e5186386b0930cb3034cc356b6ac6c3ee81e0172178e2'),
              ('sonic-chaos-reference-m5-p1c/build/SonicChaos_M5_P1C_20261024_PROOF_PRIVATE.zip',
               'fbd5264b6c07ed9bb04d63350a7c9e8a0b854a19208012f92adc4d96f9a9984c'),
              ('releases/SonicChaos_M5_A2_20261024_DECODER_FINAL_PRIVATE.zip',
               'b085b6b1d32d6453fa234c0f64365d7e9c6f39ce93920f333aae7df5208fe370'),
              ('releases/SonicChaos_M5_A2B1_20261025_FINITE_PRIVATE.zip',
               '1542d29671a0b9301565b80ae9fa76b8c71bfecd4dfe811e4ec9cc891eb440b5'),
              ('releases/SonicChaos_M5_A2B2_20261025_FINITE_PRIVATE.zip',
               '38a3a4f99c7733b2a114d9f3f7bbfb2a591ba03fde118767f0f3d0f2c9dd1c76'),
              ('releases/SonicChaos_M5_A2C1_20261025_COMMON_SFX_PRIVATE.zip',
               '9a0c2c34c72b6bb792d441211ea5c30562b681a51fac08de4af61923d8f6378e'),
              ('releases/SonicChaos_M5_A2C2_20261025_FD_NOISE_PRIVATE.zip',
               'a8f0306bf999d129baa7d36d662a815fbd4dcd0672693855aa48193852407091')]
    for rel,digest in previous:
        p=ROOT.parent/rel;assert sha(p.read_bytes())==digest
        preserved['private_archives'].append(dict(name=p.name,sha256=digest,unchanged=True))
    assert sha((OLD/'programs.scsp').read_bytes())=='c0118830a4f7779b8d53d4b6cefd129487633689532e52500cddcd6f4dddfaf1'
    assert sha((B1OLD/'programs.scsp').read_bytes())=='0668b6d432b6631513eacd56674279f02eb89ccccdb6e4fee74d717c6dfab486'
    assert sha((B2OLD/'programs.scsp').read_bytes())=='00f89cee32b1a9c31f887504182dfbed724e32ebab659f3eb7e1c923db4bc74c'
    assert sha((C1OLD/'programs.scsp').read_bytes())=='9a8721d5993c4ddecfed13f9bdd49f0ace238ab292117f266b425fc8978c8409'
    assert sha((C2OLD/'programs.scsp').read_bytes())=='fbc69aa85ed782089630197ce791769b6a25ace2abccf47147e1e81f1c434052'
    poc=ROOT.parent/'SonicChaos_POC_release_m4'
    assert subprocess.check_output(['git','-C',str(poc),'rev-parse','HEAD'],text=True).strip()=='11bff34356d5f5d979218896dc95fdc4bb265eae'
    assert not subprocess.check_output(['git','-C',str(poc),'status','--porcelain'],text=True).strip()
    preserved['accepted_POC_clean']=True
    a1p=ROOT.parent/'M5-A1P';manifest=json.loads((a1p/'evidence/source-manifest.json').read_text())
    assert all(sha((a1p/p).read_bytes())==digest for p,digest in manifest['sources'].items())
    assert sha((a1p/'datafiles/m5_psg.dll').read_bytes())==manifest['host_dll_sha256']
    assert sha((ROOT.parent/'output/M5_A1P/M5_A1P.win').read_bytes())==manifest['compiled_vm_data_sha256']
    preserved['A1P']=dict(source_files=len(manifest['sources']),source_hashes_match=True,
        native_DLL_unchanged=True,compiled_VM_unchanged=True,source_manifest_sha256=sha((a1p/'evidence/source-manifest.json').read_bytes()))
    gate=json.loads((PUB/'emission.json').read_text());assert len(gate['cases'])==99
    assert all(c['status']=='PASS' for c in gate['cases'].values())
    assert len(json.loads((PUB/'isolation.json').read_text())['cases'])==3
    members={}
    for p in OUT.glob('*.json'):
        members['private/'+p.name]=p
    members['private/programs.scsp']=OUT/'programs.scsp'
    for p in (OUT/'pcm').rglob('*'):
        if p.is_file():members['private/'+p.relative_to(OUT).as_posix()]=p
    for p in (OUT/'isolated').glob('*.wav'):members['private/isolated/'+p.name]=p
    for folder,pattern in [('tools/m5a2c3','*.py'),('tools/m5a2c2','*.py'),('tools/m5a2c1','*.py'),('tools/m5a2b2','*.py'),('tools/m5a2b1','*.py'),('tools/m5a2','*.py'),('tests','test_m5a2*.py'),
                           ('docs','m5-a2c3-*.md'),('data/m5-a2c3','*.json')]:
        for p in sorted((ROOT/folder).glob(pattern)):
            if p.name in ('private-package.json','verification.json'):continue
            members['safe/'+p.relative_to(ROOT).as_posix()]=p
    payload={n:sha(p.read_bytes()) for n,p in sorted(members.items())}
    manifest=dict(scope='private common SFX decoder proof; no game or PSG component release',
                  sha256=payload,preservation=preserved,parent='f3eeb6e66b44852d4d6245bec19db0ce3c820a1a')
    archive=ROOT.parent/'releases/SonicChaos_M5_A2C3_20261025_NOISE_MULTISLOT_PRIVATE.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,p in sorted(members.items()):z.write(p,name)
        z.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(sha(z.read(n))==h for n,h in payload.items())
        count=len(z.infolist());total=sum(i.file_size for i in z.infolist())
    receipt=dict(name=archive.name,sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,
        members=count,payload_bytes=total,CRC_and_all_member_hashes='PASS',ROM_and_DLL_excluded=True,
        program_sha256=sha((OUT/'programs.scsp').read_bytes()),preservation=preserved)
    save(PUB/'private-package.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='preservation'},indent=2))


if __name__=='__main__':run()

"""Private evidence package with CRC/member hashes; never includes ROM or DLL."""
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from m5c71r83.proof import OUT,PUB,save,sha

def run():
    files={f'private/{p.relative_to(OUT).as_posix()}':p for p in OUT.rglob('*') if p.is_file()}
    for folder in ('tools/m5c71r83','data/m5-c7-1r83'):
        files.update({p.relative_to(ROOT).as_posix():p for p in (ROOT/folder).glob('*') if p.is_file() and p.suffix in ('.py','.json') and p.name!='package.json'})
    for name in ('docs/m5-c7-1r83-pitch-region.md','tests/test_m5c71r83.py'):files[name]=ROOT/name
    assert all(p.suffix.lower() not in ('.sms','.rom','.gg','.dll','.exe') for p in files.values())
    hashes={n:sha(p.read_bytes()) for n,p in files.items()}
    dest=ROOT.parent/'releases/SonicChaos_M5_C7_1R83_20261027_RESEARCH_PRIVATE.zip'
    assert not dest.exists(),'preserve existing archive; select a fresh destination'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,p in sorted(files.items()):z.write(p,n)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None and len(z.namelist())==len(files)
        assert all(sha(z.read(n))==h for n,h in hashes.items())
    save(OUT/'archive-member-hashes.json',hashes)
    receipt=dict(name=dest.name,sha256=sha(dest.read_bytes()),bytes=dest.stat().st_size,members=len(files),CRC_and_member_hashes_verified=True,ROM_DLL_EXE_excluded=True,public_distribution=False)
    save(PUB/'package.json',receipt);print(receipt)

if __name__=='__main__':run()

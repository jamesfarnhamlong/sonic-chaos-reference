"""Private research archive; reject ROM/DLL members and verify every stored hash."""
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from m5c71.research import OUT,PUB,save,sha

def run():
    files={f'private/{p.relative_to(OUT).as_posix()}':p for p in OUT.rglob('*') if p.is_file()}
    for folder in ('tools/m5c71','data/m5-c7-1'):
        files.update({p.relative_to(ROOT).as_posix():p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.json') and p.name!='package.json'})
    for name in ('docs/m5-c7-1-original-music.md','tests/test_m5c71.py'):files[name]=ROOT/name
    assert all(p.suffix.lower() not in ('.sms','.gg','.rom','.dll','.exe') for p in files.values())
    hashes={name:sha(p.read_bytes()) for name,p in files.items()}
    archive=ROOT.parent/'releases/SonicChaos_M5_C7_1_20261026_RESEARCH_PRIVATE.zip'
    assert not archive.exists(),'preserve an existing archive; choose a distinct destination'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,p in sorted(files.items()):z.write(p,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(files)
        assert all(sha(z.read(n))==h for n,h in hashes.items())
    save(OUT/'archive-member-hashes.json',hashes)
    save(PUB/'package.json',dict(name=archive.name,sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,members=len(files),all_member_hashes_verified=True,CRC_verified=True,ROM_DLL_excluded=True,full_song_integration_eligible=False))
    print(archive.name,sha(archive.read_bytes()),len(files))

if __name__=='__main__':run()

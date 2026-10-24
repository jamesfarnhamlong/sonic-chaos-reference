"""Restore/check a private M4 asset ZIP using an independently supplied ZIP hash.

python tools/m4_restore_audio.py PRIVATE.zip TARGET --sha256 EXPECTED [--check]
Never deletes files. Verified members are skipped; replacements use atomic writes.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

def digest(b):return hashlib.sha256(b).hexdigest()

def restore(archive,target,expected,check=False):
    archive=Path(archive);target=Path(target).resolve()
    if digest(archive.read_bytes())!=expected:raise ValueError('archive SHA-256 mismatch')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:raise ValueError('ZIP CRC failure')
        manifest=json.loads(z.read('manifest.json'))
        files=dict(manifest['files'])
        files['manifest.json']=dict(sha256=digest(z.read('manifest.json')))
        if len(z.namelist())!=len(set(z.namelist())):raise ValueError('duplicate ZIP member')
        if set(z.namelist())!=set(files):raise ValueError('ZIP inventory differs from manifest')
        pending=[];verified=0
        # Validate everything before the first write.
        for name,meta in files.items():
            rel=PurePosixPath(name)
            if rel.is_absolute() or '..' in rel.parts or '\\' in name or ':' in name:
                raise ValueError('unsafe ZIP member')
            dest=(target/Path(*rel.parts)).resolve()
            if target not in dest.parents:raise ValueError('member escapes target')
            data=z.read(name)
            if digest(data)!=meta['sha256']:raise ValueError('member SHA mismatch')
            if dest.exists() and digest(dest.read_bytes())==meta['sha256']:verified+=1
            else:pending.append((dest,data))
        if not check:
            for dest,data in pending:
                dest.parent.mkdir(parents=True,exist_ok=True)
                tmp=dest.with_name(dest.name+'.m4-restoring')
                tmp.write_bytes(data);tmp.replace(dest)
    return dict(verified_existing=verified,missing_or_different=len(pending),
                restored=0 if check else len(pending),check_only=check)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive');p.add_argument('target')
    p.add_argument('--sha256',required=True);p.add_argument('--check',action='store_true')
    a=p.parse_args();result=restore(a.archive,a.target,a.sha256,a.check)
    print(json.dumps(result))
    if a.check and result['missing_or_different']:raise SystemExit(1)

if __name__=='__main__':main()

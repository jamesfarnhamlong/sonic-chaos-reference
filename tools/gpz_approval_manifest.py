"""Freeze approved GPZ art metadata; never copy local ROM graphics into Git.

The legacy boss files are rejected history. Only corrected boss frames and the
unchanged approved regular/support runtime frames are eligible for later import.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import rom as R

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'data/rom-cache/gpz/approved-art-manifest.json'

def eligible(path):
    name=Path(path).name
    if path.startswith('build/gpz51-correction/'):
        return name.startswith('51-frame-')
    if name.startswith('type-25-frame-'):return True
    return name.startswith(('type-2c-frame-','type-34-frame-','type-0a-frame-','type-0f-frame-')) and name.endswith('-bit4-0.png')

def build():
    records=[];superseded=[]
    for folder in ('gpz-enemy-approval','gpz51-correction'):
        base=ROOT/'build'/folder
        manifest=json.loads((base/'png-manifest.json').read_text())
        for row in manifest['images']:
            path=f'build/{folder}/{row["file"]}'
            record=dict(path=path,sha256=row['sha256'],size=row['size'])
            payload=(ROOT/path).read_bytes()
            assert hashlib.sha256(payload).hexdigest()==record['sha256'],path+' PNG changed'
            assert payload[:8]==b'\x89PNG\r\n\x1a\n',path
            assert list(struct.unpack('>II',payload[16:24]))==record['size'],path
            if folder=='gpz-enemy-approval' and row['file'].startswith('type-51-'):
                superseded.append(record)
            else:
                record['eligible_for_import']=eligible(path);records.append(record)
    records.sort(key=lambda r:r['path']);superseded.sort(key=lambda r:r['path'])
    return dict(format=1,rom_sha256=R.SHA256,approval_date='2026-10-03',
        approved_types=['$25','$2C','$51','$34','$0A','$0F'],
        approval='EXPLICIT USER APPROVAL; CORRECTED $51 REPLACES PRIOR WRONG COMPOSITION',
        images=records,approved_runtime_frames=[r['path'] for r in records if r['eligible_for_import']],
        unchanged_non_boss_count=41,superseded_boss_images=superseded,
        composition=dict(normal_stack=['head $00','ball $01','ball $02','ball $03'],
            throws=[3,2,1],regrowth=[1,2,3],mode2_extra_ball=4,
            landing_dust=dict(type='$51',parameter='$11',frames=[10,11],runtime_used=True)),
        registration=dict(canvas=[128,112],anchor=[64,56],terrain_presentation=[1,18]),
        storage='PNG/ROM/video local-only; Git contains metadata, tools, tests and audits.',
        gate='Art approval only; POC implementation/handoff and main integration require separate instruction.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    d=build();s=json.dumps(d,indent=2)+'\n'
    if a.check:assert CACHE.read_text()==s,'approved manifest differs'
    else:CACHE.write_text(s)
    print(len(d['images']),'current PNG hashes verified;',len(d['approved_runtime_frames']),'approved runtime frames;',len(d['superseded_boss_images']),'superseded boss images')

if __name__=='__main__':main()

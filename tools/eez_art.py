"""Extract new final-zone terrain and numeric object compositions for review.

Known shared object families are omitted. Boss dynamic VRAM is deferred to A5.
Only metadata/hashes committed; all pixel arrays remain in ignored build/.
"""
import argparse,json
from pathlib import Path
import eez_foundation as F
import level_package as L
import mghz_object_census as C
import mghz_art_approval as A

def main():
    p=argparse.ArgumentParser();p.add_argument('rom',type=Path);args=p.parse_args()
    r=L.load_rom(args.rom);m,c,acts=F.build(r)
    out=F.ROOT/'build/eez-approval';out.mkdir(parents=True,exist_ok=True)
    data=dict(acts={},subjects={},animated={});meta=dict(status='PENDING_JAMES_REVIEW',rom_sha256=L.ROM_SHA256,
        composition='original SAT piece offsets, reverse SAT precedence; no bitmap reflection/redraw',subjects={},terrain={},
        deferred='boss 5E/60 and children need dynamic graphics/initializer reachability before approval')
    for k,a in acts.items():
        d=a['descriptor'];blocks=A.block_maps(r,a,a['vram'],{b['id'] for b in m['acts'][k]['blocks']})
        data['acts'][k]=dict(width=a['width'],height=a['height'],runtime_cells=a['runtime_cells'],cells=a['cells'],
            blocks={str(b):px for b,px in blocks.items()},background=A.pal(r,26),sprite=A.pal(r,11),
            camera=[d['start']['ram_d2d6'],d['start']['ram_d2d8']])
        meta['terrain'][k]={str(b):L.sha256(bytes(v for row in px for v in row)) for b,px in blocks.items()}
    for t in (0x17,0x36,0x38):
        k,rec=next((k,x) for k,a in c['acts'].items() for x in a['records'] if int(x['type_id'],16)==t)
        bases=[int(rec['aux0'],16),int(rec['aux1'],16)]
        frames=[C.frame_record(r,t,fi,*bases,bytes(acts[k]['vram']),flips=(False,)) for fi in C.state_scripts(r,t)['frames']]
        key=f'{t:02X}'
        data['subjects'][key]=dict(frames=frames,palette=A.pal(r,11),label=f'zone5 type ${t:02X}; original mapping origins; script frames, reachability pending')
        meta['subjects'][key]=dict(bases=bases,frames=[C.strip_pixels(f) for f in frames])
    (out/'preview-input.json').write_text(F.dumps(data),encoding='utf-8')
    (F.OUT/'art-approval.json').write_text(F.dumps(meta),encoding='utf-8')
    print(out/'preview-input.json')

if __name__=='__main__':main()

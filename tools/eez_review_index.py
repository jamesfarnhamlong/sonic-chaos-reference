"""Index only current numeric composition/effect/ending boards, no stale previews."""
import json
import eez_foundation as F
import level_package as L

def main():
    out=F.ROOT/'build/eez-approval';d=json.loads((out/'preview-input.json').read_text());meta=json.loads((F.OUT/'art-approval.json').read_text())
    names=['terrain.png']+[f'object-{k}.png' for k in d['subjects']]+[f'effect-{k}.png' for k in d['animated']]
    names += ['ending-flags0-delay0-angleNone-char1.png','ending-flags31-delay0-angleNone-char1.png','ending-flags0-delay0-angleNone-char2.png']
    index=dict(rom_sha256=L.ROM_SHA256,status='PENDING_JAMES_REVIEW',boards=[],
       rules='Original decoded pixels/piece origins; known shared object families omitted; static terrain deduplicated against all256 indexed compositions for all15 prior acts. Ending frames are original approximate-harness rasters, no redrawing.',
       recreate='eez_art.py ROM; eez_boss_game.py ROM [--flags31 or --character2]; bundled Pillow Python eez_art_render.py; eez_review_index.py',
       review_limits='No visual approval claimed. Ending raster samples preserve original SAT/CRAM but approximate VDP timing; they are not hardware-perfect screenshots.')
    lines=['# Zone5 new composition review','',index['rules'],'','James approval pending. Cyan crosses mark canonical object origins.','']
    for name in names:
        path=out/name;assert path.is_file(),path
        index['boards'].append(dict(file=name,sha256=L.sha256(path.read_bytes()),bytes=path.stat().st_size))
        lines += [f'## {name}','',f'![{name}]({path.as_posix()})','']
    (F.OUT/'approval-board-index.json').write_text(F.dumps(index),encoding='utf-8')
    (out/'REVIEW.md').write_text('\n'.join(lines),encoding='utf-8');print(len(names),'boards',out/'REVIEW.md')

if __name__=='__main__':main()

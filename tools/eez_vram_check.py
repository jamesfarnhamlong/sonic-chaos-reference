"""Check final-zone static tile decode against original boot VRAM."""
import argparse
import eez_foundation as F
import level_package as L
from sez_surfaces_rig import ZoneGame

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');args=p.parse_args();r=L.load_rom(args.rom)
    g=ZoneGame(r,5,0);m,c,acts=F.build(r);a=acts['eez1']
    touched=set()
    for e in m['effects'].values():
        for cp in e['unique_copies']:touched.update(range(cp['vram']//32,(cp['vram']+cp['length']+31)//32))
    touched.update(m['ring_animation']['tile_ids'])
    used={attr&511 for b in m['acts']['eez1']['blocks'] for attr in b['mapping']['attributes']}
    rows=[]
    for t in sorted(used):
        if t in touched:continue
        expected=a['vram'][t*32:t*32+32];actual=bytes(g.s.vram[t*32:t*32+32])
        if actual!=expected:rows.append(dict(tile=t,expected=L.sha256(expected),actual=L.sha256(actual)))
    out=dict(rom_sha256=L.ROM_SHA256,used_tiles=len(used),excluded_animated_tiles=sorted(touched),mismatches=rows)
    (F.OUT/'vram-check.json').write_text(F.dumps(out),encoding='utf-8');print(out)

if __name__=='__main__':main()

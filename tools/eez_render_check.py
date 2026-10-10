"""Original harness raster and raw tile rows for suspect board compositions.
No raster pixels enter version control. Renderer is approximate, not hardware.
"""
import argparse
import eez_foundation as F
import level_package as L
from sez_surfaces_rig import ZoneGame

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();r=L.load_rom(a.rom)
    g=ZoneGame(r,5,0);m,c,acts=F.build(r);s=g.s;act=acts['eez1']
    used=sorted({x&511 for b in m['acts']['eez1']['blocks'] for x in b['mapping']['attributes']})
    # Direct byte comparisons for suspect static tiles, including both banks.
    ids=sorted(set(range(124,146))|{192,347,348,349,350})
    checks=[]
    for t in ids:
        expected=act['vram'][t*32:t*32+32];actual=bytes(s.vram[t*32:t*32+32])
        assert expected==actual,t
        checks.append(dict(tile=t,sha256=L.sha256(actual)))
    rgb=s.render()[0];out=F.ROOT/'build/eez-approval'
    (out/'original-raster.json').write_text(F.dumps(dict(rgb=rgb)),encoding='utf-8')
    result=dict(rom_sha256=L.ROM_SHA256,checks=checks,assertions=len(checks),
                explanation='Original boot VRAM matches suspect terrain blank/star fields and base7C projectile tiles byte-for-byte; sparse pixels are not introduced by extractor. Harness screenshot is supplemental evidence, not hardware approval.')
    (F.OUT/'render-check.json').write_text(F.dumps(result),encoding='utf-8');print(result)

if __name__=='__main__':main()

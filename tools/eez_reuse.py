"""Zone5 parameter-specific shared initializer equivalence and source inventory."""
import argparse
import eez_foundation as F
import level_package as L
import mghz_object_census as C
import sez_object_census as S

def build(r):
    manifest,census,acts=F.build(r);rows=[];checks=0
    for key,act in acts.items():
        for rec in census['acts'][key]['records']:
            t=int(rec['type_id'],16)
            if t not in F.CONTRACTS:continue
            results=[]
            for zone in (1,5):
                o,m,step,_=C.object_lab_init(r,act,rec);m[0xD297]=zone;m[0xD298]=act['descriptor']['act']
                step();step();b=C.SLOT
                results.append(list(m[b:b+64]))
            assert results[0]==results[1],(key,rec['index'],t,results);checks+=1
            if t==40:
                p=int(rec['parameter'],16);expected=13 if p&127 in (5,11) else (p&63)+1
                assert results[1][2]==expected,(p,results[1][2]);checks+=1
            rows.append(dict(act=key,placement=rec['index'],type=t,parameter=rec['parameter'],two_updates=results[1],zone1_zone5_identical=True,contract=F.CONTRACTS[t]))
    scans={f'0x{t:02X}':S.type_scan(r,t)[1] for t in sorted(set(F.CONTRACTS)|{23,54,55,56,57,58,94,95,96,97,98,99})}
    return dict(rom_sha256=L.ROM_SHA256,assertions=checks,cases=rows,source_scans=scans,
        scope='Initializer equivalence at same canonical zone5 placement/act/parameter, only zone byte varied1vs5. This does not replace earlier family contact/lifecycle contracts.28 parameter8B waits13 then12;05 waits13 then6. AQZ2 override14 is excluded by zone5. Generic lifecycle and existing badnik/monitor/spring semantics are imported by reference, not by appearance.')

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();v=build(L.load_rom(a.rom));(F.OUT/'shared-reuse.json').write_text(F.dumps(v),encoding='utf-8');print(v['assertions'])

if __name__=='__main__':main()

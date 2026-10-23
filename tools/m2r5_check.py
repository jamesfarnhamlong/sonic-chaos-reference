"""Focused evidence/provenance checks; no private payload output."""
import json,hashlib,zipfile,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/m2r5'
def main():
 p=argparse.ArgumentParser();p.add_argument('package');p.add_argument('zip');a=p.parse_args()
 base=json.loads((D/'original-sign-routes.json').read_text());phase=json.loads((D/'phase-routes.json').read_text());pc=json.loads((D/'package-controls.json').read_text())
 assert len(base['cases'])==4 and len(phase)==20
 bad=[]
 for c in base['cases']+phase:
  assert c['injected_state_contact'] is False
  clear=[r for r in c['rows'] if r['request']==32];assert clear
  selected=[r for r in clear if r['selected']==94]
  if selected:
   assert all(r['bg']==6 and r['contacts']==6 for r in selected)
   bad.append([c['act'],c.get('offset',0)])
  else:assert all(r['contacts']==2 for r in clear)
 assert bad==[[act,o] for act in (4,5,10,16) for o in (1,2,5)]
 assert len(pc['rows'])==12
 for r in pc['rows']:assert r['bg']==(6 if r['offset']==9 else 2)
 digest=hashlib.sha256(Path(a.zip).read_bytes()).hexdigest()
 assert digest=='2e67e2561cd79c2353d6caaf8685d46e02a59f3a9edd945ef20fcf17ad72377e'
 with zipfile.ZipFile(a.zip) as z:
  for s in pc['sources']:
   suffix='scripts/'+s['script']+'/'+s['script']+'.gml'
   names=[n for n in z.namelist() if n.replace('\\','/').endswith(suffix)];assert len(names)==1
   assert hashlib.sha256(z.read(names[0])).hexdigest()==s['sha256']
   assert hashlib.sha256((Path(a.package)/suffix).read_bytes()).hexdigest()==s['sha256']
 out=dict(status='PASS',baseline_routes=4,phase_routes=20,bad_branch_routes=bad,package_contact_controls=12,package_zip_sha256=digest,source_zip_matches=5,
 disposition='Original arrival-assisted input-owned reachability PROVEN at four signs; entrance-to-goal and exact native timing UNRESOLVED. POC no-draw remains intentional exception.')
 (D/'summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()

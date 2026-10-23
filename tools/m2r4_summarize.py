"""Summarize numeric evidence, preserving mismatches rather than approving runtime."""
import collections,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/m2r4'
def load(n):return json.loads((D/n).read_text())
def main():
    o=load('original-game.json');c=load('package-comparison.json');p=load('private-checks.json')
    columns=o['phase_columns'];ci={k:i for i,k in enumerate(columns)}
    samples=[];skim_count=overwritten=0;repeated=[]
    for f in o['cases']:
        after={r[0]:r for r in f['phases'] if r[1]=='water_after'};passed=[]
        for r in f['phases']:
            if r[1]!='water_before':continue
            get=lambda k:r[ci[k]]
            qualifies=get('yu')//256>=get('line') and get('vy')>=0 and get('move')&2 and abs(get('vx')>>8)>=4
            if not qualifies:continue
            a=after[r[0]];assert a[ci['vy']]==-768
            skim_count+=1;passed.append(r[0])
            end=next((s['after'] for s in f['shared'] if s['u']==r[0]),None)
            if end and end['vy']!=-744:overwritten+=1
            if f['id']=='a1-c1-d1-air_attack-tap':samples.append(dict(id=f['id'],u=r[0],before_vx=get('vx'),before_vy=get('vy'),after_gate_vy=-768,after_shared=end))
        if len(passed)>1:repeated.append(dict(id=f['id'],updates=passed))
    divergent=[dict(id=f['id'],width=f['width'],first_difference=f['first_difference']) for f in c['free_runs'] if f['first_difference']]
    width=[]
    for a,b in zip(c['free_runs'][::2],c['free_runs'][1::2]):
        differences=[i+1 for i,(x,y) in enumerate(zip(a['rows'],b['rows'])) if x!=y]
        if differences:width.append(dict(id=a['id'],first=differences[0],updates=len(differences)))
    values=[f['changed_from_above_pixels']['split']/f['opaque_count'] for f in p['tails']]
    phase_pairs=0;phase_differences=[]
    for f,cf in zip(o['cases'],c['shared']):
        lookup={(r[0],r[1]):r for r in f['phases']}
        for comparison in cf['comparisons']:
            for r in comparison['phases']:
                before=lookup[(r[0],r[1])];phase_pairs+=1
                if r[2:]!=before[2:]:phase_differences.append(dict(id=f['id'],u=r[0],phase=r[1]))
    v=dict(original_cases=len(o['cases']),original_updates=sum(len(f['rows']) for f in o['cases']),
        source_summary=c['summary'],actual_skim_impulses=skim_count,skim_later_overwritten=overwritten,
        phase_snapshot_pairs=phase_pairs,phase_snapshot_differences=phase_differences,
        palette_history_differences=[dict(character=f['character'],row=r) for f in c['palette_histories'] for r in f['rows'] if r['different']],
        repeated_skim_cases=repeated,skim_examples=samples,
        tails_changed_pixel_fraction_range=[min(values),max(values)],
        shared_difference_signatures=dict(collections.Counter(','.join(r['differences']) for f in c['shared'] for r in f['comparisons'] if r['differences'])),
        continuous_first_differences=divergent,width_sensitive_runs=width,
        classification=dict(palette='UNRESOLVED-WINDOWS; ordinary selector/decoder/data match; conditional full-base-to-split upper selection mismatch in controlled history',
            reversal='UNRESOLVED-WINDOWS; retained-momentum jump and repeated skim reproduced and paired; exact reported severity/location not established',
            shared_50='42 type1E side-dispatch differences, including2 related requested-state differences;8 no-ring death-field differences. Not vertical skim divergence.',
            full_runs='156/192 match all9 selected trajectory/state fields over100 updates;36 diverge at side-contact or object hurt lifecycle. Camera replay and initial state are controlled.'))
    (D/'summary.json').write_text(json.dumps(v,indent=2)+'\n')
    print(json.dumps({k:v[k] for k in ('original_cases','original_updates','source_summary','actual_skim_impulses','skim_later_overwritten','shared_difference_signatures')}))
if __name__=='__main__':main()

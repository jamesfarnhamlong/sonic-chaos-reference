"""Review summary and source/test receipts; no canonical management edits."""
import subprocess
import sys
import platform
from importlib.metadata import version
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from m5c71r83.proof import OUT,PUB,save,load,sha

def run():
    e=load(PUB/'emission.json');c=load(PUB/'continuation.json');p=load(PUB/'pcm.json');n=load(PUB/'negatives.json')
    preserved=load(PUB/'preservation.json')
    assert preserved['C71_private_archive_sha256']==load(ROOT/'data/m5-c7-1/package.json')['sha256']
    a4b=ROOT.parent/'SonicChaos_POC_m5a4b'
    assert subprocess.check_output(['git','-C',str(a4b),'rev-parse','HEAD'],text=True).strip()=='afdd6a1e62e5e61234159266a05bcddab825faf9'
    assert subprocess.check_output(['git','-C',str(a4b),'status','--porcelain'])==b''
    tests={}
    for pattern,count in [('test_m5a2*.py',136),('test_m5c71*.py',18)]:
        r=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',pattern],cwd=ROOT,capture_output=True,text=True)
        assert r.returncode==0 and f'Ran {count} tests' in r.stderr,r.stderr
        tests[pattern]=dict(passed=count,failed=0);print(r.stderr.strip())
    protected=['tools/m5a2','tools/m5a2b1','tools/m5a2c2','tools/m5a2c6','tools/m5c71','data/m5-a2c6','data/m5-c7-1']
    assert subprocess.check_output(['git','diff','7496725dd1a1cc1dda339e1334931b7a5a495198','--',*protected],cwd=ROOT)==b''
    report=dict(verdict='GO within tested research scope; not GameMaker integration approval',request='83',new92_support=False,
        authority=dict(parent='7496725dd1a1cc1dda339e1334931b7a5a495198',management='759cbd8a8077b75a8d5609de63281fc9aa2ced63',B0='3d31a7c6a0f26bdaa22901f74db01fdb78aaa8df'),
        previously_rejected_boundary=dict(tick=2784,source_addresses=[0x4634,0x4635],outcome='PASS using exact authenticated two-byte note-reader DATA contract'),
        totals=dict(original_candidate_scenarios=7,original_candidate_ticks=sum(x['ticks'] for x in e['cases'].values())+c['case']['ticks'],
            ordered_PSG_bytes=sum(x['ordered_bytes'] for x in e['cases'].values())+c['case']['ordered_bytes'],
            state_emission_failures=sum(x['failure_count'] for x in e['cases'].values())+c['case']['failure_count'],
            exact_continuous_A1L_samples=sum(x['samples'] for x in p['cases'].values()),PCM_differences=sum(x['PCM_mismatches'] for x in p['cases'].values()),
            native_before_after_mismatching_ticks=sum(x['native_before_after_state_mismatching_ticks'] for x in p['cases'].values()),
            isolated_replays=len(p['cases']),negative_controls=n['total'],negative_controls_detected=n['total'],public_tests_passed=154,public_tests_failed=0,
            inherited_C6_frozen_comparisons=158,inherited_C6_frozen_ticks=42075),
        tests=tests,environment=dict(python=platform.python_version(),z80=version('z80'),numpy=version('numpy')),
        continuation=dict(eligible='uninterrupted83 solo only; pinned bank + exact full relevant state; no original state or chip reset',
            period_ticks=3072,renewal_ticks=c['renewal_ticks'],horizon=4200,global_guard_unchanged=True,
            interrupted_gameplay_long_play='HOLD outside this certificate; tested interactions verified only within4200; any new host request/fade revokes further renewals'),
        minimum_region=load(PUB/'original.json')['minimum_region'],header_sha256=e['header_sha256'],complete83_record_sha256=e['complete83_record_sha256'],
        private_bank_sha256=e['bank_sha256'],private_bank_bytes=e['bank_bytes'],legacy_sources_and_proofs_unchanged=True,
        limitations=['seeded original sound-driver IRQ-equivalent entry, not natural game route or physical SMS timing',
            'no GameMaker/A4B/A1L or management change, no other new request support',
            'exact same-A1L PCM; no new analogue/MAME identity or listening claim',
            '13000 original/candidate ticks sampled; longer solo continuation follows exact-state recurrence induction, not infinite measured execution',
            'general gameplay/SFX long-play renewal not certified; no blanket integration or Sound Test approval'])
    save(PUB/'verdict.json',report)
    preserved['A4B_HEAD']='afdd6a1e62e5e61234159266a05bcddab825faf9';preserved['A4B_clean']=True
    save(PUB/'preservation.json',preserved)
    sources={}
    for folder in ['tools/m5c71r83',*protected[:5]]:
        for f in (ROOT/folder).glob('*.py'):sources[f.relative_to(ROOT).as_posix()]=sha(f.read_bytes().replace(b'\r\n',b'\n'))
    save(PUB/'source-receipts.json',sources)
    print(report['totals'])

if __name__=='__main__':run()

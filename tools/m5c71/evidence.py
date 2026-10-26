"""Private-source negatives, publication receipts, and bounded eligibility report."""
import copy
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5c71.research import OUT,PUB,IDS,CASES,load,save,sha,canonical
from m5a2.bank import unpack,pack,records
from m5a2c2.decoder import Decoder
from m5a2.decoder import DecodeError
from m5a2c2.proof import candidate

def run():
    bank=unpack((OUT/'programs.scsp').read_bytes());checks={}
    def reject(name,fn):
        try:fn()
        except (DecodeError,ValueError) as e:checks[name]=dict(rejected=True,error=str(e))
        else:raise AssertionError(name)
    reject('unknown-E2',lambda:Decoder(bank).command(0,0xE2,0xB800))
    reject('unvalidated-4634',lambda:Decoder(bank).byte(0x4634))
    mutated=copy.deepcopy(bank);mutated['data'][str(0xB800)]=4
    reject('F7-index4',lambda:Decoder(mutated).command(2,0xF7,0xB800))
    reject('horizon4201-constructor',lambda:Decoder(bank,horizon=4201))
    def idle_horizon():
        m=Decoder(bank)
        for _ in range(4201):m.tick()
    reject('horizon4201-execution',idle_horizon)
    # A forged source region is rejected even if its record/container hashes are
    # internally recomputed: never let a packaging workaround bypass the guard.
    mutated=copy.deepcopy(bank);mutated['data'][str(0x4634)]=0
    reject('SCSP-forged-executable-record',lambda:unpack(pack(mutated)))
    blob=bytearray((OUT/'programs.scsp').read_bytes());blob[-1]^=1
    reject('SCSP-corrupt-checksum',lambda:unpack(bytes(blob)))
    reject('SCSP-truncated',lambda:unpack(bytes(blob[:30])))
    mutated=copy.deepcopy(bank)
    for k in mutated['data']:
        if 0x4436<=int(k)<0x44C2 and int(k)%2==0:mutated['data'][k]^=1
    for rid in IDS:
        name=f'{rid:02X}-solo';good=load(OUT/(name+'-original.json'))['rows']
        _,wrong,_,_=candidate(mutated,(rid,{},32))
        first=next(t for t,(x,y) in enumerate(zip(wrong,good),1) if canonical(x['ports'])!=canonical(y['ports']))
        checks[f'{rid:02X}-wrong-pitch-detected']=dict(rejected=True,first_ordered_write_difference_tick=first)
    em=load(PUB/'emission.json');pcm=load(PUB/'pcm.json');pre=load(PUB/'preflight.json');bounds=load(PUB/'boundaries.json')
    total=sum(c['ticks'] for c in em['cases'].values());samples=sum(c['samples'] for c in pcm['cases'].values())
    report=dict(authority=dict(research_parent='45b15a578285add733fa1def9a7e7174c0215c2d',management='759cbd8a8077b75a8d5609de63281fc9aa2ced63'),
        per_ID={f'{rid:02X}':dict(verdict='HOLD',full_song_GameMaker_eligible=False,original_lifecycle='independently authenticated repeating driver state',
            original_loop=bounds['per_ID'][f'{rid:02X}']['loop'],rejected_tick=em['cases'][f'{rid:02X}-solo']['rejection']['tick'],
            matched_solo_prefix_ticks=em['cases'][f'{rid:02X}-solo']['ticks'],SCSP_receipt=em['per_ID'][f'{rid:02X}'],
            provenance='ROM hash authenticated; candidate demand extraction; every saved segment checked against source; original data and partial SCSP private. Per-ID canonical header+address/value records are prefix-only, never a full-song authenticity receipt.') for rid in IDS},
        totals=dict(original_scenarios=len(CASES),original_scenario_ticks=sum(c['ticks'] for c in pre['cases'].values()),
            separate_original_boundary_loop_ticks=sum(c['loop']['original_ticks'] for c in bounds['per_ID'].values()),
            completed_candidate_scenarios=sum(c['status']=='PASS' for c in em['cases'].values()),guard_rejected_solo_scenarios=2,
            matched_candidate_ticks=total,matched_ordered_PSG_bytes=sum(c['ordered_bytes'] for c in em['cases'].values()),
            state_emission_mismatches=sum(c['failure_count'] for c in em['cases'].values()),exact_A1L_PCM_samples=samples,
            PCM_mismatches=sum(c['PCM_mismatches'] for c in pcm['cases'].values()),native_state_mismatching_ticks=sum(c['native_state_mismatching_ticks'] for c in pcm['cases'].values()),
            negative_controls=len(checks),negative_controls_detected=sum(c['rejected'] for c in checks.values())),
        negatives=checks,horizon=4200,decoder_semantics_changed=False,SCSP_format_changed=False,
        continuation='Original full-loop certificates exist for both IDs. No candidate continuation or horizon renewal is eligible because both solo paths are rejected before their repeat boundary. Do not splice WAVs, skip the operation, reset driver/chip or renew coverage counters.',
        next_source_gates={'83':'Independently scope data-as-code pitch reads at4634/4635, schema/extractor least-privilege provenance and full-song exact state/PSG/A1L comparisons; do not globally permit executable-region records.',
                           '92':'Independently scope F7 index4 at channel+43, call-stack alias/stale byte lifecycle under restart and interference; do not globally enlarge loop-index bounds.'},
        limitations=['seeded IRQ-equivalent sound driver only, no natural game route or SMS hardware timing','no GameMaker changes, build or human listening','exact A1L identity is same-core original-versus-candidate; no new MAME or analogue waveform identity claim','no full candidate loop playback and no full-song promotion','context partners were already accepted C6 requests, no other new request authenticated'])
    save(PUB/'verdict.json',report)
    source={}
    for folder in ('tools/m5a2','tools/m5a2b1','tools/m5a2c2','tools/m5c71'):
        for f in (ROOT/folder).glob('*.py'):source[f.relative_to(ROOT).as_posix()]=sha(f.read_bytes().replace(b'\r\n',b'\n'))
    for name in ('tools/audio1_psg_trace.py','tools/m5a0/backend.py','tools/m5a2c3/original_noise.py'):
        source[name]=sha((ROOT/name).read_bytes().replace(b'\r\n',b'\n'))
    save(PUB/'source-receipts.json',source)
    print(report['totals'])

if __name__=='__main__':run()

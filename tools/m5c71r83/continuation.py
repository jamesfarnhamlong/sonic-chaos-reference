"""Compare opt-in83 renewal to the already frozen13000-tick original oracle."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5c71r83.proof import OUT,PUB,csnapshot,compare,load,save,canonical,sha
from m5c71r83.contract import unpack
from m5c71r83.renewal import Decoder,fingerprint,STATE_SHA256

def run():
    bank=unpack((OUT/'programs.scsp').read_bytes());m=Decoder(bank);m.direct(0x83);rows=[];renewals=[];count=0;edges=[]
    for t in range(1,13001):
        m.tick();rows.append(csnapshot(m))
        edges.extend([[t,i,q] for tick,i,p,q in m.loops if tick==t])
        if m.renewal_count!=count:
            renewals.append(m.last_renewal_tick);count=m.renewal_count
    result=compare('solo-long',m,rows,load(PUB/'original.json'),edges)
    assert renewals==[3594,6666,9738,12810]
    assert len(m.loops)<=64 and m.transfer_log_dropped>0
    # Full candidate recurrence includes every compared channel/global/PSG field,
    # not only the compact signature checked by renewal at runtime.
    def strip(r):return {k:v for k,v in r.items() if k!='ports'}
    assert canonical(strip(rows[521]))==canonical(strip(rows[3593]))
    assert all(canonical(strip(rows[i]))==canonical(strip(rows[i+3072])) for i in range(522,3594))
    original=load(OUT/'solo-long-original.json');states=original['states']
    assert states[521]==states[3593]
    assert states[522:3594]==states[3594:6666]
    assert [r['ports'] for r in rows[522:3594]]==[r['ports'] for r in rows[3594:6666]]
    save(PUB/'continuation.json',dict(case=result,renewal_ticks=renewals,period_ticks=3072,first_tick=522,repeat_tick=3594,
        bank_pinned=True,state_sha256=STATE_SHA256,complete_candidate_period_exact=True,original_full400_RAM_period_exact=True,
        continuation_eligible='only uninterrupted83 solo, pinned bank, exact state certificate; later requests/fades revoke renewals',
        original_horizon=4200,global_guard_changed=False,driver_or_PSG_state_reset=False,diagnostic_transfer_log_cap=64,log_entries_dropped=m.transfer_log_dropped))

if __name__=='__main__':run()

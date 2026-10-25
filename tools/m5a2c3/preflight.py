"""Three noise/multi-slot SFX: original-only classes and original-driven core diagnostics."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
import audio1_psg_trace as T
from m5a2c3.original_noise import OriginalNoise
from m5a2.proof import save,sha
from m5a2b1.preflight import structural

OUT=ROOT.parent/'private-research/m5-a2c3'
PUB=ROOT/'data/m5-a2c3'
IDS=(0xB0,0xB7,0xBA)
BATCH=IDS[:3]
SUPPORTED={0xE0,0xE1,0xE6,0xE7,0xF0,0xF2,0xF3,0xF5,0xF6,0xF7,0xF8,0xF9,0xFB,0xFD}


def run(rom):
    catalogue={r['request_id']:r for r in json.loads((ROOT/'data/m5/catalogue.json').read_text())['entries']}
    rows=[]
    for rid in IDS:
        h=T.header_facts(rom,rid);h['stream_initial_flags']=[rom[h['header_rom']+4+6*i] for i in range(h['stream_count'])]
        # SFX noise slots use the ordinary tone reader, not music-noise syntax.
        syntax={'channels':h['streams']}
        if any(f&8 for f in h['stream_initial_flags']):
            scan=dict(qualification='raw initial mode: dynamic original path below; generic music syntax scan not applied')
        else:scan=structural(rom,syntax)
        d=OriginalNoise(rom);ops=Counter();f3=[];restores=[];env=set();pitch=set();active_slots=set();enabled=[0]*4;max_simultaneous=0;slot_release={};previous_active=set()
        d.hook(0x46D9,lambda q:ops.update([q.cpu.a]))
        d.hook(0x4753,lambda q:f3.append(q.mem[q.cpu.de]))
        d.hook(0x47F3,lambda q:restores.append(dict(tick=q.update,data_latch=q.psg.latch//16,DE11=q.mem[0xDE11])))
        d.hook(0x4546,lambda q:env.add(q.mem[q.cpu.ix+8]))
        d.hook(0x42AF,lambda q:pitch.add(q.mem[q.cpu.ix+7]))
        d.request(rid);end=None;held=[]
        for t in range(1,501):
            d.tick()
            current_active={i for i,a in enumerate(T.SFX_CH) if d.mem[a]&128}
            max_simultaneous=max(max_simultaneous,len(current_active))
            for i in previous_active-current_active:slot_release[str(i)]=t
            previous_active=current_active
            for i,a in enumerate(T.SFX_CH):
                if d.mem[a]&128:active_slots.add(i)
            for i,a in enumerate(d.psg.att):enabled[i]+=a<15
            if not d.active() and end is None:end=t
            if end is not None and any(a<15 for a in d.psg.att):held.append(t)
            if end is not None and t>=end+128:break
        if end is None:raise ValueError('preflight finite budget exceeded')
        d.close()
        music=T.Driver(rom);music.request(0x81);suppressed=set();last_suppressed={};releases=[]
        music.hook(0x47F3,lambda q:releases.append(dict(tick=q.update,data_latch=q.psg.latch//16,DE11=q.mem[0xDE11])))
        for t in range(1,30+end+80):
            if t==30:music.request(rid)
            music.tick()
            if t>=30:
                for i,a in enumerate(T.MUSIC_CH):
                    if music.mem[a]&4:suppressed.add(i);last_suppressed[str(i)]=t
        modes=sorted({v&7 for v in f3})
        cls='tone-only' if not f3 else 'tone2-clocked periodic noise' if modes==[3] else 'tone2-clocked white noise' if modes==[7] else 'fixed-rate noise' if all(m&3!=3 for m in modes) else 'mixed noise classes'
        if max_simultaneous>1 and any(s['latch']=='0xa0' for s in h['streams']):cls='tone1 plus '+cls
        row=dict(request_id=rid,label=catalogue[rid]['friendly_name'],implementation_authorised=rid in BATCH,
            header=h,syntax=scan,original_inactive_tick=end,post_completion_observed_ticks=128,
            original_F3_native_diagnostics=d.F3_states,diagnostic_backend='accepted original-core adapter driven only by original writes; rendered output discarded, no candidate PCM',
            reached_opcodes={f'{k:02X}':v for k,v in sorted(ops.items())},unverified_opcodes=[f'{k:02X}' for k in sorted(set(ops)-SUPPORTED)],
            output_class=cls,F3_control_modes=modes,F3_executions=len(f3),repeated_F3=len(f3)>len(set(f3)),
            physical_noise_attenuation_enabled_ticks=enabled[3],SFX_slots_used=sorted(active_slots),maximum_simultaneous_SFX_slots=max_simultaneous,slot_release_ticks=slot_release,
            initial_envelope_base=h['envelope_table_cpu'],volume_envelope_selectors=sorted(env),pitch_selectors=sorted(pitch),
            table_pitch_required=any(0<x<128 for x in pitch),solo_DE11_latch_restores=restores,
            final_physical_registers=d.psg.state(),post_inactive_physically_enabled_ticks=len(held),
            THZ_context=dict(suppressed_music_channels=sorted(suppressed),last_suppression_ticks=last_suppressed,DE11_restores=releases),
            priority=catalogue[rid]['priority'],source_header_sha256=sha(rom[h['header_rom']:h['header_rom']+4+6*h['stream_count']]),
            classification_boundary='fresh seeded original-only observations; no candidate/PCM promotion or arbitrary-pair guarantee',
            remaining_contexts=['replacement, retrigger and priority phases beyond this one context','eligible envelope control/held-output variants under interference'])
        rows.append(row);print(f'{rid:02X}',end,cls,row['reached_opcodes'],'pitch',row['pitch_selectors'],'slots',row['SFX_slots_used'],'postheld',len(held))
    save(PUB/'preflight.json',dict(ROM_sha256=T.ROM_SHA256,rows=rows,candidate_PCM_rendered=False,reference_state_diagnostic_only=True,candidate_promoted=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();run(T.load_rom(a.rom))

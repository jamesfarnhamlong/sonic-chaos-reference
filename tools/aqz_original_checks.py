"""Guarded AQZ original-game boot/layout and history-independent replay checks.

Uses the complete CPU exported state (prefix, EI shadow and frame tick included),
plus the existing RAM/VDP/harness snapshot. Fixture writes at engine boundaries.
No register-only restore or injected NOP workaround.
"""
import argparse
from pathlib import Path
import aqz_foundation as F
import level_package as L
from sez_surfaces_rig import ZoneGame

OUTPUT=F.OUT/'original-checks.json'

def build(r):
    out=dict(rom_sha256=L.ROM_SHA256,method=__doc__,acts={})
    for key,meta in F.ACTS.items():
        g=ZoneGame(r,4,meta['act'],hooks={0x16D0:'after_player',0x16D3:'after_objects'})
        s,m=g.s,g.m;a=L.build_act(r,key,meta)
        cpu_snapshot=bytes(s.cpu.get_state_view())
        def restore():
            g.e.restore();s.cpu.get_state_view()[:]=cpu_snapshot
        g.restore_snapshot=restore
        actual=bytes(m[0xC001:0xC001+a['runtime_cells']]);expected=bytes(a['cells'][:a['runtime_cells']])
        changes=[dict(index=i,expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
        assert not changes,(key,changes)
        water=dict(line=s.u16(0xD450),flag=m[0xD443],screen_line=m[0xD132],irq_enabled=m[0xD131],
            controllers=[dict(type=m[b],state=m[b+1],parameter=m[b+63],x=s.u16(b+17),y=s.u16(b+20)) for b in range(0xD540,0xDA00,64) if m[b]==13])
        def replay():
            st=a['descriptor']['start'];g.begin(st['ram_d511'],st['ram_d514'],width=a['width'],types=(12,13,14,48,60,61,63,89))
            rows=g.run(48)
            assert len(rows)>=48
            return F.digest(F.dumps(rows[:48]).encode())
        first=replay();second=replay();assert first==second,(key,first,second)
        out['acts'][key]=dict(layout_cells_checked=len(actual),layout_mismatches=changes,layout_sha256=F.digest(actual),
            water=water,complete_cpu_state_bytes=len(cpu_snapshot),replay_updates=48,replay_sha256=first,history_independent_replay=True,
            zone=m[0xD297],act=m[0xD298])
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true');args=p.parse_args()
    value=build(L.load_rom(args.rom))
    if args.check:assert OUTPUT.read_text(encoding='utf-8')==F.dumps(value)
    else:OUTPUT.write_text(F.dumps(value),encoding='utf-8')
    print({k:(v['layout_cells_checked'],v['water'],v['history_independent_replay']) for k,v in value['acts'].items()})

if __name__=='__main__':main()

"""Zone5 boot, original layout, complete CPU restore and VRAM reconnaissance."""
import argparse
from pathlib import Path
import eez_foundation as F
import level_package as L
from sez_surfaces_rig import ZoneGame

def build(r):
    out=dict(rom_sha256=L.ROM_SHA256,acts={})
    for key,meta in F.ACTS.items():
        g=ZoneGame(r,5,meta['act'],hooks={0x16D0:'after_player',0x16D3:'after_objects'})
        s,m=g.s,g.m;a=L.build_act(r,key,meta);state=bytes(s.cpu.get_state_view())
        def restore():g.e.restore();s.cpu.get_state_view()[:]=state
        g.restore_snapshot=restore
        actual=bytes(m[0xC001:0xC001+a['runtime_cells']]);expected=bytes(a['cells'][:a['runtime_cells']])
        changes=[dict(index=i,expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
        assert not changes,(key,changes)
        def replay():
            st=a['descriptor']['start'];g.begin(st['ram_d511'],st['ram_d514'],width=a['width'],types=(23,54,55,56,57,58,94,95,96,97,98,99))
            rows=g.run(48);assert len(rows)>=48
            return L.sha256(F.dumps(rows[:48]).encode())
        first=replay();second=replay();assert first==second,(key,first,second)
        out['acts'][key]=dict(layout_cells_checked=len(actual),layout_mismatches=changes,
            layout_sha256=L.sha256(actual),complete_cpu_state_bytes=len(state),replay_updates=48,
            replay_sha256=first,history_independent_replay=True,zone=m[0xD297],act=m[0xD298])
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('rom',type=Path);a=p.parse_args()
    v=build(L.load_rom(a.rom));(F.OUT/'original-checks.json').write_text(F.dumps(v),encoding='utf-8');print(v)

if __name__=='__main__':main()

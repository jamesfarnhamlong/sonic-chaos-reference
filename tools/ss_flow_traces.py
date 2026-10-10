"""SS-A1/A5: whole-game entry and exit traces (success, death, timeout) from the original ROM in the approximate SMS harness."""
import argparse
import json
from pathlib import Path
import rom as R
from ss_rig import SSRig, STAGE_ZONE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/rom-cache/special-stages/flow-traces.json'
RING = {1: (15248, 118), 2: (None, None)}


def snap(g):
    s, m = g.s, g.m
    return dict(flow=m[0xD293], mode=m[0xD294], zone=m[0xD297], act=m[0xD298], emeralds=m[0xD2CC], card=m[0xD2CD], continues=m[0xD2C3],
                lives=m[0xD299], rings=m[0xD29A], timer=[m[0xD2C0], m[0xD2BF]], timer_run=m[0xD2BE], d2a6=s.u16(0xD2A6),
                score=[m[0xD29F], m[0xD29E], m[0xD29D]], player=[m[0xD500], m[0xD501], m[0xD502], s.u16(0xD511), s.u16(0xD514)])


def exit_trace(g, kind, ring_xy, maxf=20000):
    s, m = g.s, g.m
    if kind == 'success':
        g.begin(ring_xy[0], ring_xy[1], cur=0x0E, f3=1, floor=False, rings=0)
    elif kind == 'death':
        g.begin(300, 130, cur=0x0E, f3=1, floor=False, rings=0)
    else:
        g.begin(111, 118, cur=5, f3=0, floor=True, rings=0)
    log, prev, done = [], None, None
    for f in range(maxf):
        s.pad = 0
        s.run_frame()
        sn = snap(g)
        key = (sn['flow'], sn['mode'], sn['zone'], sn['act'], sn['emeralds'], sn['card'], sn['continues'])
        if key != prev:
            log.append(dict(frame=f, **sn)); prev = key
        if m[0xD297] != g.stage + 7 and m[0xD294] == 0 and m[0xD293] == 0x40 and m[0xD500] == 1 and done is None and f > 300:
            done = f
        if done and f > done + 90:
            break
    return log


def build(r):
    out = dict(format=1, rom_sha256=R.SHA256, evidence='EMULATED ORIGINAL FRAME; whole-game controlled trace, approximate SMS harness',
               stage1_exits={}, origin_act_index_quirk={})
    for kind in ('success', 'death', 'timeout'):
        g = SSRig(r, 1)
        out['stage1_exits'][kind] = dict(entry=g.entry_log, trace=exit_trace(g, kind, RING[1]))
    for origin in ((0, 0), (0, 2), (1, 2), (5, 2)):
        g = SSRig(r, 1, origin=origin)
        t = exit_trace(g, 'death', RING[1], maxf=4000)
        out['origin_act_index_quirk'][f'zone{origin[0]}_act{origin[1]}'] = dict(
            entry_saved_zone=g.entry_log[1]['saved_zone'], loaded_after=[(x['frame'], x['zone'], x['act'], x['player'][3:]) for x in t if x['flow'] in (0x40, 0x42)][-2:],
            final=t[-1])
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('rom', type=Path); p.add_argument('--check', action='store_true'); a = p.parse_args()
    d = json.dumps(build(R.load(a.rom)), indent=2) + '\n'
    if a.check:
        assert OUT.read_text(encoding='utf-8') == d
    else:
        OUT.write_text(d, encoding='utf-8')
    print('ok')

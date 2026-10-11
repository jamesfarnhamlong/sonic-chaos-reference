"""Special Stage follow-up evidence: Large Rings, SS3 final junction input, act-index-2 reachability census, Entry Fail mechanism.

Everything here is derived from the ROM (original routines / whole-game traces in the approximate SMS harness).  Observations by James and community
documentation are recorded in the docs, never in this cache.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
import level_package as L
import rom as R
import eez_transport as ET
from oracle import Oracle
from sez_surfaces_rig import ZoneGame
from ss_rig import SSRig
from ss_search import restore, take
import ss_foundation as F

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/rom-cache/special-stages/followup.json'
PAD_UP = 1


def large_rings(r):
    """Surface type $1D (block $B8) in the terrain-ring probe $753E: one collection per 32x32 cell, any quadrant, +$10 BCD."""
    def probe(block, px, py, parity, start=0x05):
        o = Oracle(r); m = o.mem
        m[0xC001 + 10 * 128 + 10] = block
        o.word(0xD511, 10 * 32 + px); o.word(0xD514, 10 * 32 + py)
        m[0xD507] = parity; m[0xD29A] = start; m[0xD299] = 3; m[0xD2C8] = 1; m[0xD297] = 8; m[0xD2CC] = 0; m[0xD294] = 0x80
        o.cpu.ix = 0xD500; m[0xD500] = 1
        o.call(0x753E)
        return dict(cell=m[0xC001 + 10 * 128 + 10], rings_bcd=m[0xD29A], lives=m[0xD299], mode=m[0xD294])
    pts = ((16, 10, 0), (2, 26, 0), (30, 20, 1), (4, 6, 1))
    manifest = json.loads((F.OUT / 'implementation-manifest.json').read_text(encoding='utf-8'))
    cells = {k: v['cells'].get(k, 0) for k, v in [('29', manifest['surfaces']['29'])] for k in manifest['stages']}
    return dict(surface=0x1D, block=0xB8, replacement_block=0x46, probe_results=[probe(0xB8, *p) for p in pts],
                wrap_past_99=probe(0xB8, 16, 10, 0, start=0x95), cells_per_stage=cells, rings_per_cell=10,
                normal_acts_containing_surface_1D=0, note='$69B1 (floor handler) is a no-op; the collection is the $753E probe branch.')


def ss3_final_junction(r):
    inputs = json.loads((ROOT / 'data/rom-cache/special-stages/natural-inputs.json').read_text(encoding='utf-8'))['ss3']
    g = SSRig(r, 3); s, m = g.s, g.m
    table = [int.from_bytes(r[0x311BC + 2 * i:0x311BE + 2 * i], 'little') for i in range(16)]
    pend, ev, fr = [], [], [0]

    def entry(block):
        def f(mm):
            if s.slot[2] != 12:
                return
            pend.append(dict(frame=fr[0], block=block, pre=[s.u16(0xD511), s.u16(0xD514), s.u16(0xD516), s.u16(0xD518)], pad=m[0xD137]))
        return f
    for i, a in enumerate(table):
        g.hook(a, entry(0x74 + i))

    def tail(mm):
        if s.slot[2] != 12 or not pend:
            return
        p = pend.pop(); p['post'] = [s.u16(0xD511), s.u16(0xD514), s.u16(0xD516), s.u16(0xD518), m[0xD3C6]]; ev.append(p)
    g.hook(0x91DC, tail)
    inv = []
    g.hook(0x4B1D, lambda mm: inv.append(dict(frame=fr[0], x=s.u16(0xD511), y=s.u16(0xD514))))
    restore(g, (g.e.base, g.base_cpu))
    flat = []
    for pad, n in inputs:
        for _ in range(n):
            s.pad = pad; s.run_frame(); fr[0] += 1; flat.append(pad)
            if m[0xD294] & 0x60:
                break
        if m[0xD294] & 0x60:
            break
    broken = list(inv)
    decisions = [e for e in ev if e['block'] in (0x7A, 0x7B, 0x7C, 0x7D) and e['post'][4] == 255]
    d = decisions[-1]
    options = {}
    for pad in range(16):
        res = ET.model(d['block'], d['pre'][0], d['pre'][1], d['pre'][2], d['pre'][3], pad)
        options.setdefault(f'vx={res[2]},vy={res[3]}', []).append(pad)
    # counterfactual from a frame boundary before the junction: hold one direction only while Sonic is on the junction cell, then neutral
    f0 = d['frame'] - 14
    restore(g, (g.e.base, g.base_cpu))
    for f in range(f0):
        s.pad = flat[f]; s.run_frame()
    snap = take(g)
    cf = {}
    for name, pad in (('neutral', 0), ('Up', PAD_UP), ('Down', 2), ('Left', 4), ('Right', 8)):
        restore(g, snap)
        end = None
        for f in range(f0, f0 + 900):
            x, y = s.u16(0xD511), s.u16(0xD514)
            s.pad = pad if (d['pre'][0] - 20 <= x <= d['pre'][0] + 40 and d['pre'][1] - 24 <= y <= d['pre'][1] + 24) else 0
            s.run_frame()
            if m[0xD294] & 0x60:
                break
        end = (s.u16(0xD511), s.u16(0xD514), m[0xD501])
        cf[name] = dict(end_position=list(end[:2]), end_state=end[2], mode=hex(m[0xD294]), timer=hex(m[0xD2BF]),
                        reaches_emerald_room=end[0] > 3600)
    return dict(junction_block=0x7A, junction_count_in_stage=sum(1 for c in json.loads((F.OUT / 'implementation-manifest.json').read_text(encoding='utf-8'))['stages']['ss3']['blocks'] if c['id'] == 0x7A and c['cells'] == 1),
                natural_route_decisions=len(decisions), decision=dict(frame=d['frame'], pre=d['pre'], pad_held=d['pad'], post=d['post']),
                pad_bit_meaning='bit0 = Up (UP=1, DOWN=2, LEFT=4, RIGHT=8)', router_options=options, counterfactual=cf,
                invincibility_monitors_broken_on_natural_route=len(broken), monitors_broken=broken)


def ss3_repeated_sections(r):
    """Layout comparison of the five lower room+tube sections (21-cell pitch, rows 10..23) against the first one."""
    a = F.L.build_act(r, 'ss3', dict(zone=10, act=0, name='SS3')); w, c = a['width'], a['cells']
    def sec(i):
        return [[c[y * w + 2 + i * 21 + k] for k in range(21)] for y in range(10, 24)]
    base = sec(0)
    return {f'section{i}': sum(1 for y in range(14) for k in range(21) if base[y][k] == sec(i)[y][k]) for i in range(1, 5)} | dict(cells_compared_per_section=14 * 21)


def act_index2_census(r):
    rows = {}
    for z in range(6):
        for act in range(3):
            a = L.build_act(r, f'z{z}a{act}', dict(zone=z, act=act, name='x'))
            cells = a['cells'][:a['runtime_cells']]
            recs, _ = L.decode_object_list(r, a['descriptor']['objects']['list_rom'])
            large = sum(1 for c in cells if R.header(r, c)['flags'] & 31 == 0x1D)
            t9 = sum(1 for x in recs if x['type_id'] == '0x09')
            m1 = sum(1 for x in recs if x['type_id'] == '0x10' and x['parameter'] == '0x01')
            rows[f'zone{z}_act{act}'] = dict(terrain_ring_quadrants=len(a['terrain_rings']), type09_rings=t9, large_ring_cells=large, plus10_monitors=m1,
                                             maximum_obtainable=len(a['terrain_rings']) + t9 + 10 * large + 10 * m1)
    act2 = {k: v['maximum_obtainable'] for k, v in rows.items() if k.endswith('act2')}
    return dict(per_act=rows, act_index2_maximums=act2, any_act_index2_reaches_100=any(v >= 100 for v in act2.values()),
                ring_counter_reset='$2A4F (called by the level loader $2934) zeroes $D29A at every act load',
                note='upper bound: every ring quadrant, $09 ring and +10 source collected with none lost')


def entry_fail(r):
    g = ZoneGame(r, 0, 0); s, m = g.s, g.m
    base = (g.e.snapshot(), bytes(s.cpu.get_state_view()))
    state = dict(v=0, done=False)
    prior = s.pc_hooks.get(0x64FA)

    def inj(mm):
        if prior:
            prior(mm)
        if state['done'] or mm.cpu.ix != 0xD500:
            return
        state['done'] = True
        m[0xD29A] = 0x99; m[0xD2C2] = state['v']
        sp = mm.cpu.sp - 2; mm.mem[sp] = 0xFA; mm.mem[sp + 1] = 0x64; mm.cpu.sp = sp; mm.cpu.pc = 0x3138
    g.hook(0x64FA, inj)
    res = {}
    for v in range(60):
        g.e.restore(base[0]); s.cpu.get_state_view()[:] = base[1]
        state.update(v=v, done=False); m[0xD2CC] = 0
        loaded = fail = None
        for f in range(420):
            s.pad = 0; s.run_frame()
            if m[0xD297] == 8 and loaded is None:
                loaded = f
            if m[0xD294] & 0x20:
                fail = f; break
        res[v] = (loaded, fail)
    failing = [v for v, (_, f) in res.items() if f is not None]
    return dict(variable='$D2C2 (60-frame tick counter) at the moment the 100th ring is collected', values_tested=60, failing_values=failing,
                failure_frame={str(v): res[v][1] for v in failing}, stage_loaded_frame=res[0][0],
                mechanism=['entry ($178F -> $1753) stops the timer ($D2BE := 0) but leaves $D2C2 stale',
                           'level loader $2934 zeroes $D2BF/$D2C0 and sets the timer-run flag $D2BE := $FF, then waits a frame ($062D)',
                           'the per-second tick ($27EE) in special-stage mode ($D294 bit7) decrements $D2BF; 0 - 1 = $FF -> $2846 sets $D294 bit5 (stage failure)',
                           'stale $D2C2 = 59 ticks on the first frame; the stage timer $59 is only written afterwards ($17F1) and $1758 resets $D2C2 later'],
                outcome='stage is flagged failed as soon as it becomes playable: no completion possible; normal failure return to the next act')


def build(r):
    d = dict(format=1, rom_sha256=L.ROM_SHA256, research_base='ce431507bd0a49437e9559326dbac3ca9c0b0206', stage='Special Stage follow-up',
             evidence='original routines and whole-game traces (approximate SMS harness); observations/community claims are documentation only')
    d['large_rings'] = large_rings(r)
    d['ss3_final_junction'] = ss3_final_junction(r)
    d['ss3_repeated_sections'] = ss3_repeated_sections(r)
    d['act_index2_reachability'] = act_index2_census(r)
    d['entry_fail'] = entry_fail(r)
    return d


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('rom', type=Path); p.add_argument('--check', action='store_true'); a = p.parse_args()
    d = json.dumps(build(R.load(a.rom)), indent=2) + '\n'
    if a.check:
        assert OUT.read_text(encoding='utf-8') == d
    else:
        OUT.write_text(d, encoding='utf-8')
    print('ok')

"""SS-A2: Special Stage terrain surfaces, tube/transport reuse proof and natural traversal traces."""
import argparse
import itertools
import json
from collections import Counter
from pathlib import Path
import level_package as L
import rom as R
import mghz_foundation as M
import eez_transport as ET
from oracle import Oracle
from ss_rig import SSRig, PAD
import ss_foundation as F

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/rom-cache/special-stages/traversal.json'

# surface id -> (role, earlier contract); handler addresses come from the ROM floor-dispatch table.
SURFACES = {
    0x00: ('no special handler (decor / empty)', None),
    0x01: ('zone-5-only handler $6A5D; returns at once when zone != 5 (inert in every Special Stage)', 'docs/eez-environment-audit.md'),
    0x02: ('plain solid (handler $6A5B = RET)', None),
    0x03: ('plain solid slope (handler $6A5C = RET)', None),
    0x07: ('terrain ring (probe $753E)', 'docs/terrain-ring-collection.md'),
    0x09: ('terrain upright spring $6A75', 'docs/spring-interaction-audit.md'),
    0x0A: ('terrain horizontal spring (tested inside side cores)', 'docs/spring-interaction-audit.md'),
    0x0C: ('crumble ledge $6B79', 'docs/sez-surfaces-0c-13-1a-audit.md'),
    0x0D: ('breakable block $0D', 'docs/mghz-m1-windows-followup.md'),
    0x13: ('transport / tube entry $6D43 (+ state $21)', 'docs/eez-environment-audit.md'),
    0x14: ('terrain diagonal / ceiling spring $6A90 (zone != 0 -> Y -5.5)', 'docs/spring-interaction-audit.md'),
    0x16: ('floor break/bounce/reward $6AE3', 'docs/gpz-foundation-audit.md'),
    0x1D: ('no-op handler $69B1 (decor/platform art, no special rule)', None),
}
SWEEP = dict(block=range(0x74, 0x84), x=(0, 14, 31), y=(0, 14, 16, 31), vel=((-1536, 0), (1536, 0), (0, -1536), (0, 1536), (64, 0)), pad=range(16))


def route_sweep(r, zone):
    """Run the original route handlers ($0C:$91BC table) under a Special Stage zone byte and compare with the final-zone model."""
    o = Oracle(r); o.bank(2, 12); m = o.mem; o.cpu.ix = 0xD500
    table = [int.from_bytes(r[0x311BC + 2 * i:0x311BE + 2 * i], 'little') for i in range(16)]
    o.cpu.set_breakpoint(0x91DC)
    checks = 0
    for block, x, y, vel, pad in itertools.product(SWEEP['block'], SWEEP['x'], SWEEP['y'], SWEEP['vel'], SWEEP['pad']):
        vx, vy = vel
        m[0xD297] = zone
        o.position(256 + x, 256 + y); o.word(0xD516, vx); o.word(0xD518, vy); m[0xD137] = pad; m[0xD3C6] = 0
        o.cpu.pc = table[block - 0x74]; o.cpu.sp = 0xDFE0; o.word(o.cpu.sp, o.RETURN)
        for _ in range(20):
            o.cpu.ticks_to_stop = 100000; o.cpu.run()
            if o.cpu.pc == 0x91DC:
                break
        assert o.cpu.pc == 0x91DC
        actual = [o.word(0xD511), o.word(0xD514), o.word(0xD516), o.word(0xD518), m[0xD3C6]]
        assert actual == ET.model(block, 256 + x, 256 + y, vx, vy, pad), (zone, block, x, y, vx, vy, pad)
        checks += 1
    return checks


def natural_route_events(r, stage, start, pad_fn, updates):
    """Whole-game traversal; every original route-handler execution is compared with the final-zone model at the common tail."""
    g = SSRig(r, stage)
    table = [int.from_bytes(r[0x311BC + 2 * i:0x311BE + 2 * i], 'little') for i in range(16)]
    pending = []
    events = []
    s, m = g.s, g.m

    def entry(block):
        def f(mm):
            if s.slot[2] != 12 or not g.recording:
                return
            pending.append(dict(block=block, u=len(g.rows), pre=[s.u16(0xD511), s.u16(0xD514), s.u16(0xD516), s.u16(0xD518)], pad=m[0xD137]))
        return f

    for i, a in enumerate(table):
        g.hook(a, entry(0x74 + i))

    def tail(mm):
        if s.slot[2] != 12 or not g.recording or not pending:
            return
        p = pending.pop()
        post = [s.u16(0xD511), s.u16(0xD514), s.u16(0xD516), s.u16(0xD518), m[0xD3C6]]
        exp = ET.model(p['block'], p['pre'][0], p['pre'][1], p['pre'][2], p['pre'][3], p['pad'])
        events.append(dict(update=p['u'], block=p['block'], pre=p['pre'], pad=p['pad'], post=post, matches_model=post == exp))
    g.hook(0x91DC, tail)
    g.begin(start[0], start[1], cur=5, f3=0, floor=True, rings=0)
    rows = g.run(updates, padf=pad_fn)
    states = []
    prev = None
    for v in rows:
        if v['cur'] != prev:
            states.append(dict(u=v['u'], state=v['cur'], x=v['x'], y=v['y'])); prev = v['cur']
    changed = [e for e in events if e['post'] != e['pre'] + [0] or True]
    moves = [e for e in events if e['post'][4] == 255]
    return dict(updates=len(rows), state_changes=states[:40], route_handler_calls=len(events), route_decisions=len(moves),
                all_match_model=all(e['matches_model'] for e in events), decisions=moves[:30], camera=[(v['u'], v['d174'], v['x']) for v in rows[::25]][:40])


def surface_table(r):
    manifest = json.loads((F.OUT / 'implementation-manifest.json').read_text(encoding='utf-8'))
    consumers = manifest['surface_consumers']
    handlers = consumers[0][1]['handlers'] if isinstance(consumers, list) else consumers['floor_dispatch_table']['handlers']
    out = {}
    for sid, row in sorted(manifest['surfaces'].items(), key=lambda kv: int(kv[0])):
        s = int(sid)
        role, doc = SURFACES[s]
        out[sid] = dict(handler=handlers.get('0x%02X' % s), role=role, earlier_contract=doc, blocks=row['blocks'], cells=row['cells'])
    return out


def build(r):
    d = dict(format=1, rom_sha256=L.ROM_SHA256, research_base=F.BASE, stage='SS-A2 traversal',
             evidence='byte-verified handlers; original route handlers under stage zone bytes; whole-game natural traces in the approximate SMS harness')
    d['surfaces'] = surface_table(r)
    d['route_zone_independence'] = {str(z): route_sweep(r, z) for z in range(8, 13)}
    d['camera_lead'] = dict(routine='$58E1', normal=dict(left=0x68, right=0x88, default=0x78),
                            tube_or_pan=dict(condition='$D15F & 3 != 0 (state $21 callback sets bit1; pan lock bit0)', target=0x78),
                            slew_per_update=1, frame='screen X lead of the camera follow; WORLD/EDGE: CENTER-relative, not widened by this package')
    d['natural_traversal'] = {
        'ss3_first_tube': natural_route_events(r, 3, (143, 622), lambda u, f: PAD['RIGHT'] | PAD['B1'] if u < 45 else 0, 330),
        'ss5_start': natural_route_events(r, 5, (143, 878), lambda u, f: PAD['RIGHT'] | PAD['B1'] if u < 45 else 0, 400)}
    return d


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('rom', type=Path); p.add_argument('--check', action='store_true'); a = p.parse_args()
    d = json.dumps(build(R.load(a.rom)), indent=2) + '\n'
    if a.check:
        assert OUT.read_text(encoding='utf-8') == d
    else:
        OUT.write_text(d, encoding='utf-8')
    print('ok')

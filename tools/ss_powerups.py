"""SS-A3: Special Stage power-up / reward census, shared-contract reuse and stage-specific overrides."""
import argparse
import json
from pathlib import Path
import level_package as L
import rom as R
from oracle import Oracle
from ss_rig import SSRig
import ss_foundation as F

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/rom-cache/special-stages/powerups.json'

# monitor parameter -> reward-queue bit tested by $4AA3 (queue D3A3)
MONITOR_BITS = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}


def monitor_sweep(r):
    """Run the original reward dispatcher ($4AA3) for every queue bit under every zone byte; report only deviations from zone 0."""
    def run(zone, bit):
        o = Oracle(r); m = o.mem
        m[0xD297] = zone; m[0xD500] = 1; m[0xD2C8] = 1; m[0xD3A3] = 1 << bit; m[0xD29A] = 0x95; m[0xD299] = 3; m[0xD532] = 0; m[0xD2CC] = 0
        o.cpu.ix = 0xD500; m[0x062D] = 0xC9           # frame-wait stubbed (the routine only waits one frame for sound)
        o.call(0x4AA3)
        return dict(selector=m[0xD532], power_timer=o.word(0xD44C), power_copy=o.word(0xD3A1), clock_pause=m[0xD3C4], lives=m[0xD299], rings=m[0xD29A],
                    d503=m[0xD503], mode=m[0xD294], result_card=m[0xD2CD], sound=m[0xDE04], requested_state=m[0xD502])
    out = {}
    for bit in range(6):
        rows = {z: run(z, bit) for z in range(13)}
        out[str(bit)] = dict(zone0=rows[0], deviations={str(z): {k: [rows[0][k], v] for k, v in rw.items() if v != rows[0][k]}
                                                         for z, rw in rows.items() if rw != rows[0]})
    return out


def clock_trace(r):
    g = SSRig(r, 2); m, s = g.m, g.s
    g.begin(336, 500, vy=0x200, cur=0x0A, f3=2, floor=False, rings=0)
    first = None; ticks = []; prev = None
    for f in range(760):
        s.pad = 0; s.run_frame()
        if m[0xD3C4] == 11 and first is None:
            first = f
        if first is not None and m[0xD3C4] != prev:
            ticks.append(dict(frame=f - first, d3c4=m[0xD3C4], timer=m[0xD2BF], sound=m[0xDE04]))
        prev = m[0xD3C4]
    resume = None
    for f in range(first + 700, first + 900):
        s.pad = 0; s.run_frame()
        if m[0xD2BF] != 0x58 and resume is None:
            resume = f - first
    return dict(pickup_sound=0xF8, ticks=ticks, timer_frozen_at=0x58, timer_first_changed_after_frames=resume)


def rocket_trace(r, stage, monitor):
    g = SSRig(r, stage); m, s = g.m, g.s
    g.begin(monitor[0], monitor[1] - 40, vy=0x200, cur=0x0A, f3=2, floor=False, rings=0)
    first = last = None; row = {}
    for f in range(3800):
        s.pad = 0; s.run_frame()
        if m[0xD501] == 0x11 and first is None:
            first = f; row = dict(selector=m[0xD532], power_timer=s.u16(0xD44C), power_copy=s.u16(0xD3A1))
        if first is not None and m[0xD501] != 0x11 and last is None:
            last = f; row.update(left_state=m[0xD501], frames_in_state=f - first); break
        if m[0xD294] & 0x60:
            row['stage_ended'] = hex(m[0xD294]); break
    row.setdefault('frames_in_state', None)
    row['still_active_after_frames'] = (3800 if last is None and 'stage_ended' not in row else None)
    return row


def spring_shoes_trace(r):
    g = SSRig(r, 2); m, s = g.m, g.s
    g.begin(496, 1700, vy=0x100, cur=0x0E, f3=1, floor=False, rings=0)
    out = dict(entered_state=None, launch_vy=None, relaunch_vy=[])
    prevvy = None
    for f in range(400):
        s.pad = 0; s.run_frame()
        vy = s.u16(0xD518); vy = vy - 65536 if vy > 32767 else vy
        if m[0xD501] == 0x12 and out['entered_state'] is None:
            out['entered_state'] = f; out['launch_vy'] = vy
        elif out['entered_state'] is not None and prevvy is not None and vy < -1800 and prevvy > -1800:
            out['relaunch_vy'].append(vy)
        prevvy = vy
    out['d3a4'] = s.u16(0xD3A4)
    return out


def spring_trace(r):
    g = SSRig(r, 4); m, s = g.m, g.s
    out = {}
    for name, sx, sy, x0 in (('param0_1616', 1616, 448, 1650), ('param1_1424', 1424, 384, 1460), ('param1_1488', 1488, 416, 1520), ('param1_1552', 1552, 448, 1585)):
        g.begin(x0, sy - 34, cur=5, f3=0, floor=True, rings=0)
        res = None
        for f in range(160):
            s.pad = 4; s.run_frame()
            vy = s.u16(0xD518); vy = vy - 65536 if vy > 32767 else vy
            if m[0xD501] == 0x0B:
                res = dict(state=0x0B, vy=vy, d448=m[0xD448]); break
        out[name] = res
    return out


def build(r):
    census = json.loads((F.OUT / 'object-census.json').read_text(encoding='utf-8'))
    rows = {}
    for k, st in census['stages'].items():
        for x in st['records']:
            rows.setdefault(f"{x['type_id']}/{x['parameter']}", {})[k] = rows.get(f"{x['type_id']}/{x['parameter']}", {}).get(k, 0) + 1
    d = dict(format=1, rom_sha256=L.ROM_SHA256, research_base=F.BASE, stage='SS-A3 powerups',
             evidence='original reward dispatcher under zone bytes + whole-game traces (approximate SMS harness) + static zone-read scan of the ROM')
    d['placements'] = rows
    d['monitor_parameter_effects'] = {str(p): dict(queue_bit=b) for p, b in MONITOR_BITS.items()}
    d['monitor_sweep'] = monitor_sweep(r)
    d['clock_monitor_param5'] = clock_trace(r)
    d['rocket_shoes'] = dict(ss1=rocket_trace(r, 1, (112, 142)), ss4=rocket_trace(r, 4, (304, 238)))
    d['spring_shoes_ss2'] = spring_shoes_trace(r)
    d['springs_ss4'] = spring_trace(r)
    return d


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('rom', type=Path); p.add_argument('--check', action='store_true'); a = p.parse_args()
    d = json.dumps(build(R.load(a.rom)), indent=2) + '\n'
    if a.check:
        assert OUT.read_text(encoding='utf-8') == d
    else:
        OUT.write_text(d, encoding='utf-8')
    print('ok')

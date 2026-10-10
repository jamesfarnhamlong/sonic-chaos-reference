"""SS-A5: five-stage progression, persistence of completion flags, repeat behavior and closure."""
import argparse
import json
from pathlib import Path
import level_package as L
import rom as R
from oracle import Oracle
from sez_surfaces_rig import ZoneGame
import ss_foundation as F

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/rom-cache/special-stages/progression.json'


def sequence(r, outcomes):
    """Drive the ORIGINAL gate ($178F), selector ($187B) and ring callback ($1E:$9489) through repeated 100-ring entries.

    outcomes: per entry True (ring collected) / False (failure).  Returns the visited zones and the final completion bits."""
    emeralds = 0
    visited = []
    for ok in outcomes:
        o = Oracle(r); m = o.mem
        m[0xD2C8] = 1; m[0xD297] = 2; m[0xD2CC] = emeralds; m[0xD294] = 0
        o.call(0x178F)
        if m[0xD294] != 0x88:
            visited.append(None)
            continue
        o.call(0x187B)
        zone = m[0xD297]
        visited.append(zone)
        if ok:
            o.bank(2, 0x1E)
            m[0xD740:0xD740 + 64] = bytes(64)
            m[0xD740] = 0x31; m[0xD741] = 1; m[0xD743] = 0x80; m[0xD76C] = 8; m[0xD76D] = 16; m[0xD77F] = 1 << (zone - 8)
            o.word(0xD751, 100); o.word(0xD754, 100); o.word(0xD511, 100); o.word(0xD514, 100)
            m[0xD52C] = 8; m[0xD52D] = 24; m[0xD503] = 0
            o.cpu.ix = 0xD740
            o.call(0x9489)
            assert m[0xD294] & 0x40
        emeralds = m[0xD2CC]
    return dict(outcomes=outcomes, visited_zones=visited, final_bits=emeralds)


def persistence(r):
    out = {}
    for name, lives, cont in (('death_with_lives', 2, 0), ('game_over_no_continue', 1, 0), ('game_over_with_continue', 1, 2)):
        g = ZoneGame(r, 0, 0); s, m = g.s, g.m
        m[0xD299] = lives; m[0xD2CC] = 0x07; m[0xD2C3] = cont; m[0xD29D] = 0x34; m[0xD29E] = 0x12
        done = [False]
        prior = s.pc_hooks.get(0x64FA)

        def inj(mm):
            if prior:
                prior(mm)
            if done[0] or mm.cpu.ix != 0xD500:
                return
            done[0] = True
            sp = mm.cpu.sp - 2; mm.mem[sp] = 0xFA; mm.mem[sp + 1] = 0x64; mm.cpu.sp = sp; mm.cpu.pc = 0x4984
        g.hook(0x64FA, inj)
        from sms_frame_harness import BTN_1
        zones = []
        for f in range(3000):
            s.pad = BTN_1 if (f > 900 and f % 50 < 5) else 0
            s.run_frame()
            if not zones or zones[-1] != m[0xD297]:
                zones.append(m[0xD297])
        out[name] = dict(start=dict(lives=lives, continues=cont, emeralds=7), end=dict(zone=m[0xD297], act=m[0xD298], lives=m[0xD299], emeralds=m[0xD2CC],
                                                                               continues=m[0xD2C3], score=[m[0xD29F], m[0xD29E], m[0xD29D]]), zones_visited=zones)
    o = Oracle(r); m = o.mem
    m[0xD2CC] = 0x1F; m[0xD29A] = 5; m[0xD2C8] = 1
    o.call(0x2A00)
    out['new_game_reset_2A00'] = dict(emeralds_after=m[0xD2CC], rings_after=m[0xD29A])
    return out


def build(r):
    d = dict(format=1, rom_sha256=L.ROM_SHA256, research_base=F.BASE, stage='SS-A5 progression',
             evidence='original gate/selector/ring callback executed in sequence; whole-game persistence traces in the approximate SMS harness')
    d['sequences'] = dict(
        all_succeed=sequence(r, [True] * 7),
        fail_stage2_twice=sequence(r, [True, False, False, True, True, True, True, True]),
        fail_stage1_forever=sequence(r, [False] * 3))
    d['persistence'] = persistence(r)
    d['ending_link'] = dict(
        source='docs/eez-boss-endgame-audit.md; data/rom-cache/eez/boss-game-flags-31.json',
        facts=['type $61 state 5 ($1E:$BB1A): Sonic with $D2CC == $1F does not take the immediate final-clear branch',
               'type $61 state 7 ($1E:$BB61): $D2CC |= $20 (sixth bit), $D293 = $50, delete',
               'ending selector $18ED: Sonic with $D2CC & $3F == $3F takes the full ending ($18FE); partial flags take $1A41; other characters take $1ACD'],
        stage_reward='the five special-stage completion bits are the only way to reach $1F; no object other than type $31 writes bits 0..4')
    return d


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('rom', type=Path); p.add_argument('--check', action='store_true'); a = p.parse_args()
    d = json.dumps(build(R.load(a.rom)), indent=2) + '\n'
    if a.check:
        assert OUT.read_text(encoding='utf-8') == d
    else:
        OUT.write_text(d, encoding='utf-8')
    print('ok')

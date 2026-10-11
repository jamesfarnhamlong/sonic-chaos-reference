"""Original scheduler replay of every natural EEZ $17 record.

One canonical carrier/player boundary seed per case, stable fixture camera,
occupied other placement bytes, then original code and action-button input.
No per-update player teleport, owner repair or movement substitution.
"""
import argparse
import json
import eez_foundation as F
import level_package as L
from sez_surfaces_rig import ZoneGame


def build(raw):
    census = json.loads((F.OUT/'object-census.json').read_text())
    cases = []
    checks = 0
    for act, data in census['acts'].items():
        g = ZoneGame(raw, 5, int(act[-1])-1, hooks={0x16D0: 'after_player', 0x16D3: 'after_objects'})
        s, m = g.s, g.m
        cpu = bytes(s.cpu.get_state_view())

        def restore():
            g.e.restore()
            s.cpu.get_state_view()[:] = cpu
        g.restore_snapshot = restore
        for record in data['records']:
            if record['type_id'] != '0x17':
                continue
            for button in (16, 32):
                copies = []
                events = []
                copy_before = [None]
                carrier_x, carrier_y = record['world_x'], record['world_y']
                attached_ticks = [0]
                def engine(mm):
                    if not g.recording or mm.cpu.ix != 0xD500:
                        return
                    s.w16(0xD174, max(0, carrier_x-112))
                    s.w16(0xD176, max(8, carrier_y-100))

                def before_copy(mm):
                    if not g.recording or mm.cpu.ix != 0xD500:
                        return
                    owner = s.u16(0xD3A6)
                    copy_before[0] = ([s.u16(owner+i) for i in (17, 20, 22, 24)],
                                      [m[0xD510], m[0xD513]], owner, m[0xD501])

                def after_copy(mm):
                    nonlocal checks
                    if not g.recording or mm.cpu.ix != 0xD500:
                        return
                    words, fractions, owner, state = copy_before[0]
                    actual = [s.u16(a) for a in (0xD511, 0xD514, 0xD516, 0xD518)]
                    assert actual == words
                    assert [m[0xD510], m[0xD513]] == fractions
                    checks += 2
                    copies.append(dict(update=len(g.rows), player_state=state,
                                       owner=owner, words=actual, fractions=fractions))
                    if state == 23:
                        attached_ticks[0] += 1

                def observe(mm):
                    if not g.recording:
                        return
                    events.append(dict(update=len(g.rows),
                        player=[m[0xD501], m[0xD502], s.u16(0xD511), s.u16(0xD514), s.u16(0xD3A6)],
                        actor=[m[0xD540], m[0xD541], m[0xD542], s.u16(0xD551), s.u16(0xD554),
                               s.u16(0xD556), s.u16(0xD558), m[0xD543], m[0xD544], m[0xD55F], m[0xD57E]],
                        occupancy=m[0xD400+record['index']-1]))

                # add_pc_hook replaces a previous callback at the same address.
                g.hook(0x4C56, before_copy)
                g.hook(0x4C7A, after_copy)
                g.hook(0x16D3, observe)
                g.hook(0x4C90, engine)

                def setup(q):
                    m[0xD540:0xDA00] = bytes(0x4C0)
                    b = record['original_creator']
                    m[0xD540] = 23
                    m[0xD544] = b['flags']
                    m[0xD548:0xD54A] = bytes(b['art_bases'])
                    m[0xD57E], m[0xD57F] = b['token'], b['parameter']
                    s.w16(0xD551, carrier_x)
                    s.w16(0xD554, carrier_y)
                    s.w16(0xD57A, carrier_x)
                    m[0xD400:0xD440] = bytes([255])*64
                    m[0xD510], m[0xD513] = 77, 99
                    s.w16(0xD3A6, 0)
                    s.w16(0xD174, max(0, carrier_x-112))
                    s.w16(0xD176, max(8, carrier_y-100))

                g.begin(carrier_x, carrier_y-16, cur=14, f3=2, floor=False, apply=setup, types=(23,))
                rows = g.run(100, padf=lambda u, f: button if 8 <= attached_ticks[0] < 11 else 0)
                assert len(rows) >= 100
                assert {22, 23} <= {v['player_state'] for v in copies}
                assert attached_ticks[0] >= 8
                assert any(e['player'][4] == 0xD540 for e in events)
                assert any(e['actor'][9] == 16 and e['actor'][7] & 64 and e['player'][4] == 0 for e in events)
                assert any(e['actor'][10] == 0 and e['occupancy'] == 255 for e in events)
                checks += 6
                cases.append(dict(act=act, index=record['index'], rom=record['rom_offset'],
                                  world=[carrier_x, carrier_y], button=button,
                                  updates=len(rows), copies=copies, events=events))
    assert len(cases) == 10
    checks += 1
    return dict(rom_sha256=L.ROM_SHA256, assertions=checks, cases=cases,
                fixture=__doc__, limits='Controlled natural-record scheduler fixtures; not input-only whole-act traversal or visual acceptance.')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('rom')
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    v = build(L.load_rom(a.rom))
    dest = F.OUT/'carrier-game-checks.json'
    if a.check:
        assert dest.read_text(encoding='utf-8') == F.dumps(v)
    else:
        dest.write_text(F.dumps(v), encoding='utf-8')
    print('carrier scheduler assertions', v['assertions'], 'cases', len(v['cases']))


if __name__ == '__main__':
    main()

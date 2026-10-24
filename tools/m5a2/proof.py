"""Private extraction and separate Z80 differential gate; safe numeric reports only."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools'), str(Path(__file__).parent)]
from decoder import Decoder
from bank import pack, unpack, canonical, records
import audio1_psg_trace as T

OUT = ROOT.parent / 'private-research/m5-a2'
PUB = ROOT / 'data/m5-a2'
IDS = (0x88, 0x99, 0x81, 0xAC, 0xB6, 0xA3, 0xBC, 0xB8, 0xA0)
CASES = {
    'finite-88': (0x88, {}, 240),
    'finite-99': (0x99, {}, 1220),
    'THZ-loop': (0x81, {}, 4200),
    'multi-slot': (0x81, {30: [('request', 0xB6)], 35: [('request', 0xA0)]}, 180),
    'AC-replacement': (0x81, {30: [('request', 0xAC)], 35: [('request', 0xA0)]}, 180),
    'A3-BC': (0x81, {30: [('request', 0xA3)], 35: [('request', 0xBC)]}, 180),
    'BC-A3-blocked': (0x81, {30: [('request', 0xBC)], 35: [('request', 0xA3)]}, 180),
    'finite-fade': (0x81, {30: [('request', 0xB8)], 35: [('request', 0xBC)],
                            40: [('fade', [12, 1, 2])]}, 100),
    'fixed-hold': (0x81, {30: [('request',0xB8)],35: [('request',0xBC)]},210),
    'finite88-fade-recovery': (0x88, {30: [('request', 0xAC)], 35: [('request', 0xA0)],
                                     40: [('fade', [12, 1, 2])]}, 90),
    'music-interruption': (0x81, {100: [('request', 0x88)], 340: [('request', 0x81)]}, 500),
    'reset-then-fresh': (0xB8, {3: [('request', 0xF8)], 5: [('request', 0xA3)]}, 90),
    'priority-blocked-reset': (0xB6, {3: [('request', 0xF8)]}, 80),
    'three-mailboxes': (0x81,{30:[('mailbox',[0xBC,0]),('mailbox',[0xA3,1]),('mailbox',[0xB6,2])]},100),
    **{f'solo-{rid:02X}': (rid, {}, 180) for rid in IDS if rid >= 0xA0},
}


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + '\n')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def apply(model,kind,value):
    if kind=='request':model.direct(value)
    elif kind=='mailbox':model.direct(*value)
    elif kind=='fade':model.fade=list(value)
    else:raise ValueError('unknown host action')


class ExtractionData(dict):
    """Candidate-led DATA demand extraction. Never called by the oracle."""
    def __init__(self, rom):
        super().__init__()
        self.rom = rom

    def __missing__(self, key):
        p = int(key)
        if not (0x4436 <= p < 0x44C2 or 0x48AC <= p < 0xC000):
            raise ValueError(f'data read crosses executable region {p:04x}')
        v = self.rom[p + 0x4000]
        self[key] = v
        return v


def extract(rom):
    data = ExtractionData(rom)
    bank = dict(version=1, horizon=4200, source_sha256=T.ROM_SHA256,
                priority={str(i): T.priority_byte(rom, i) for i in (*range(0x81, 0xC5), 0xF8)},
                programs={}, data=data)
    bank['priority']['0'] = 0
    for rid in IDS:
        h = T.header_facts(rom, rid)
        hrom = h['header_rom']
        channels = h.get('channels', h.get('streams'))
        streams = []
        for n, s in enumerate(channels):
            streams.append(dict(latch=int(s['latch'], 16), pointer=s['stream_cpu'],
                                transpose=s['transpose'], volume=s['volume'],
                                flags=128 if rid < 0xA0 else rom[hrom + 4 + n * 6]))
        length = 6 + 4 * len(streams) if rid < 0xA0 else 4 + 6 * len(streams)
        bank['programs'][str(rid)] = dict(streams=streams, multiplier=h['duration_multiplier'],
            tempo=h.get('tempo_byte', 0), source_offset=hrom, header_length=length,
            header_sha256=sha(rom[hrom:hrom + length]))
    for name, (initial, events, ticks) in CASES.items():
        m = Decoder(bank)
        m.direct(initial)
        for t in range(1, ticks + 1):
            for kind, v in events.get(t, []):
                apply(m,kind,v)
            try:
                m.tick()
            except Exception:
                print('extraction failure', name, t, 'pointers', [m.cw(c,3) for c in m.ch], 'transfers',m.loops[-5:])
                raise
    bank['data'] = dict(data)
    # Independently check each extracted run against the authenticated source.
    for segment in records(bank)['segments']:
        p, n = segment['address'], segment['length']
        assert sha(rom[p+0x4000:p+0x4000+n]) == segment['sha256']
    return bank


def run(rom):
    bank = extract(rom)
    save(OUT / 'bank.json', bank)
    packed = pack(bank)
    (OUT / 'programs.scsp').write_bytes(packed)
    bank = unpack(packed)
    reports = {}
    for name, (initial, events, ticks) in CASES.items():
        m = Decoder(bank)
        m.direct(initial)
        rows, times, ops = [], [], []
        for t in range(1, ticks + 1):
            for kind, v in events.get(t, []):
                apply(m,kind,v)
            start = time.perf_counter_ns()
            m.tick()
            times.append(time.perf_counter_ns() - start)
            rows.append(m.snapshot())
            rows[-1]['channel_bytes'] = [list(c) for c in m.ch]
            rows[-1]['globals'] = [*m.tempo, m.selected, *m.mail, *m.fade,
                                   m.last_sfx, m.noise_offset, m.fade_noise_volume]
            ops.append(m.ops)
        d = T.Driver(rom)
        transfers = []
        def transfer(q):
            transfers.append((q.update, T.CHANNELS.index(q.cpu.ix),
                              q.mem[q.cpu.de] | q.mem[q.cpu.de+1] << 8))
        d.hook(0x47B4, transfer)
        d.hook(0x481C, transfer)
        d.request(initial)
        failures, original = [], []
        for t in range(1, ticks + 1):
            for kind, v in events.get(t, []):
                if kind == 'request': d.request(v)
                elif kind == 'mailbox': d.mem[0xDE04+v[1]]=v[0]
                else: d.mem[0xDE09:0xDE0C] = bytes(v)
            start = len(d.writes)
            d.tick()
            o = dict(ports=[b for _, b in d.writes[start:]], registers=d.psg.state(),
                     latch=d.psg.latch // 16, saved_noise=d.mem[0xDE11],
                     channels=[d.mem[a] & 0xD4 for a in T.CHANNELS], priority=d.mem[0xDE0F])
            o['channel_bytes'] = [list(d.mem[a:a+48]) for a in T.CHANNELS]
            o['globals'] = [d.mem[a] for a in (0xDE01,0xDE02,0xDE03,0xDE04,0xDE05,0xDE06,
                                              0xDE09,0xDE0A,0xDE0B,0xDE0D,0xDE15,0xDE16)]
            original.append(o)
            for k in o:
                if o[k] != rows[t - 1][k]: failures.append(dict(tick=t, field=k))
            if failures:
                save(OUT / f'{name}-first-failure.json', dict(failures=failures, candidate=rows[t-1],
                     original=o, original_channels=[list(d.mem[a:a+48]) for a in T.CHANNELS]))
                break
        projected = [(t, i, target) for t, i, source, target in m.loops]
        if not failures and projected != transfers:
            failures.append(dict(tick=0,field='control-flow-transfers'))
        save(OUT / f'{name}.json', dict(candidate=rows, original=original, failures=failures, loops=m.loops))
        reports[name] = dict(ticks=ticks, compared_ticks=len(original), failures=failures,
            status='FAIL' if failures else 'PASS', ordered_bytes=sum(len(r['ports']) for r in rows),
            control_flow_transfers=len(m.loops), max_stream_ops_per_tick=max(ops),
            opcodes={f'{k:02X}':v for k,v in sorted(m.opcodes.items())},
            decoder_median_ns=sorted(times)[len(times)//2], decoder_max_ns=max(times))
        print(name, reports[name], flush=True)
    raw = json.dumps(bank, separators=(',', ':')).encode()
    save(PUB / 'emission.json', dict(cases=reports, rom_sha256=T.ROM_SHA256,
         fixture_sha256=sha(raw), json_bytes=len(raw), zlib_json_bytes=len(zlib.compress(raw)),
         extracted_data_bytes=len(bank['data']), candidate_uses_oracle=False,
         packed_bytes=len(packed), packed_sha256=sha(packed),
         source_sha256={name:sha((Path(__file__).parent/name).read_bytes().replace(b'\r\n',b'\n')) for name in ('decoder.py','bank.py','proof.py')},
         source_hash_policy='UTF-8 source, CRLF normalized to LF for Git checkout reproducibility',
         segment_count=len(records(bank)['segments']),
         record_json_bytes=len(canonical(records(bank)))))
    assert all(c['status']=='PASS' for c in reports.values()), 'exact original emission/state gate failed'
    return reports


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('rom')
    a = p.parse_args()
    run(T.load_rom(a.rom))

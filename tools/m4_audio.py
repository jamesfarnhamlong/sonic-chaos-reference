"""M4 numeric research and optional PRIVATE asset preparation; no GameMaker edits.

python tools/m4_audio.py ROM evidence --out data/m4/driver-evidence.json
python tools/m4_audio.py ROM assets --out build/m4/private

Asset mode reuses AUDIO-1B's renderer. Full write logs, read maps, VGM and PCM
stay under ignored build/. Evidence mode exports counts/hashes, never streams.
"""
import argparse
import hashlib
import json
from pathlib import Path
import audio1_psg_trace as T

ROOT = Path(__file__).resolve().parents[1]
MUSIC = (0x90, 0x99, 0x82, 0x81)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def capture(rom, rid, ticks, events=None):
    d = T.Driver(rom)
    d.request(rid)
    reads = [[] for _ in range(4)]
    def read(dd):
        if dd.cpu.ix in T.MUSIC_CH:
            reads[T.MUSIC_CH.index(dd.cpu.ix)].append(dd.update)
    d.hook(0x4341, read)
    rows, inactive, silent = [], None, None
    for tick in range(1, ticks + 1):
        for kind, value in (events or {}).get(tick, []):
            if kind == 'request':
                d.request(value)
            elif kind == 'fade':
                d.mem[0xDE09:0xDE0C] = bytes(value)
            elif kind == 'pause':
                d.mem[0xDE08] = value
        start = len(d.writes)
        d.tick()
        rows.append([b for _, b in d.writes[start:]])
        if inactive is None and not d.music_active():
            inactive = tick
        if silent is None and all(a == 15 for a in d.psg.att):
            silent = tick
    return d, rows, [sorted(set(r)) for r in reads], inactive, silent


def evidence(rom):
    music = {}
    for rid, ticks in ((0x99, 1300), (0x82, 7042), (0x81, 3781), (0x90, 900)):
        d, rows, reads, inactive, silent = capture(rom, rid, ticks)
        packed = b''.join(t.to_bytes(4, 'little') + bytes([b])
                          for t, row in enumerate(rows, 1) for b in row)
        psg = T.Psg(); last_non_off = None
        for tick, row in enumerate(rows, 1):
            for b in row:
                psg.write(b)
            if any(a < 15 for a in psg.att):
                last_non_off = tick
        music[f'{rid:02X}'] = dict(ticks=ticks, header=T.header_facts(rom, rid),
            first_all_music_inactive=inactive, first_all_attenuations_off=silent,
            last_tick_with_non_off_register=last_non_off,
            write_count=sum(map(len, rows)), write_log_sha256=digest(packed),
            stream_read_counts=list(map(len, reads)))
        if rid != 0x90:
            music[f'{rid:02X}']['recurrence'] = T.recurrence(rom, rid)
    # Static request ownership: only safe addresses, IDs and span hashes escape.
    sites = []
    for name, off, rid in (('title', 0x754, 0x99), ('choice', 0x30BA, 0x82)):
        assert rom[off:off+5] == bytes((0x3E, rid, 0x32, 0x04, 0xDE))
        sites.append(dict(owner=name, load_rom=off, store_rom=off+2, request=rid,
                          destination=0xDE04, span_sha256=digest(rom[off:off+5])))
    # $189B calculates zone*3+act and writes D4A4; original opening is zone7/act0.
    table = rom[0x18BA:0x18BA+24]
    assert table[0] == 0x81 and table[17] == 0x90 and table[21] == 0x90
    # Explicitly observe finite title and restart from a playing title.
    _, restart, _, _, _ = capture(rom, 0x99, 500, {300: [('request', 0x99)]})
    _, fresh, _, _, _ = capture(rom, 0x99, 201)
    same = restart[299:] == fresh
    # Requests replace one mailbox byte; this is not a FIFO.
    last = {}
    for ids in ((0x81, 0x99), (0x99, 0x81)):
        d = T.Driver(rom)
        for rid in ids:
            d.request(rid)
        d.tick()
        solo = T.Driver(rom); solo.request(ids[-1]); solo.tick()
        last['-'.join(f'{r:02X}' for r in ids)] = d.writes == solo.writes
    fades = []
    for at in (10, 78, 308, 608, 745):
        d, rows, _, inactive, _ = capture(rom, 0x90, at+30,
            {at: [('fade', (12, 1, 2))]})
        fades.append(dict(fade_tick=at, first_music_inactive=inactive,
                          reset_after_inclusive_ticks=inactive-at+1 if inactive else None))
    return dict(schema_version=1, rom_sha256=T.ROM_SHA256,
        evidence='new controlled original Z80 driver execution; no hardware/native/audio render',
        music=music, direct_sites=sites,
        indexed_owners=dict(THZ=table[0], EEZ3=table[17], opening=table[21]),
        title_restart_psg_equal_fresh=same, last_mailbox_write_wins=last,
        opening_phase_fades=fades,
        title_interruption=title_interruption(rom),
        priority={f'{i:02X}':T.priority_byte(rom, i) for i in range(0x81, 0xC5)})


def title_interruption(rom):
    """Unlike an OFF write, clearing suppression bit4 identifies stream recovery."""
    results = []
    for sfx, active in ((0xBF,20),(0xA6,40)):
        matches = 0
        for at in range(100,124):
            d = T.Driver(rom); d.request(0x99)
            reads = []; recovered = None
            d.hook(0x4341, lambda q: reads.append(q.update) if q.cpu.ix == 0xDEA0 else None)
            for tick in range(1,at+active+60):
                if tick == at:
                    d.request(sfx)
                before = d.mem[0xDEA0]
                d.tick()
                if tick > at+active and before & 16 and not d.mem[0xDEA0] & 16:
                    recovered = recovered or tick
            expected = next((t for t in reads if t > at+active),None)
            matches += recovered == expected and recovered is not None
        results.append(dict(sfx=sfx,phases=24,suppression_clear_matches_stream_read=matches))
    return results


def private_assets(rom, out):
    """Preparation export, not an accepted production library.

    Leaves loop cuts untouched for a joint-stem seam scan and native validation.
    No truncated preview is ever marked loopable. Never put this output in Git.
    """
    import audio1b_render as R
    out = Path(out).resolve()
    build = (ROOT / 'build').resolve()
    if build not in out.parents:
        raise SystemExit('private assets must be inside this worktree build/')
    renderer = R.available_renderers().get('libvgm_mame')
    if renderer is None:
        raise SystemExit('set AUDIO1B_VGM2WAV to the existing pinned MAME-core tool')
    out.mkdir(parents=True, exist_ok=True)
    manifest = dict(rom_sha256=T.ROM_SHA256, clock=R.PAL, rate=R.RATE,
                    renderer=R.PINS['libvgm'], assets=[], status='preparation; seam/listening gates pending')
    # Render at least two recurrence bodies; the opening is deliberately finite.
    lengths = {0x90:800, 0x99:1300, 0x82:130+2*6912, 0x81:1093+2*2688,
               0xBF:41, 0xA6:61}
    for rid, ticks in lengths.items():
        _, rows, reads, inactive, _ = capture(rom, rid, ticks)
        vgm = R.build_vgm(rows)
        assert not R.vgm_matches(rows, vgm)
        (out / f'{rid:02X}.vgm').write_bytes(vgm)
        mix = renderer.render(vgm, ticks*735)
        R.write_wav(out/f'{rid:02X}_mix.wav', mix)
        pcm = []
        for ch in range(4):
            v = renderer.render(R.build_vgm(R.attenuation_stem(rows, ch)), ticks*735)
            pcm.append(v)
            R.write_wav(out/f'{rid:02X}_ch{ch}.wav', v)
        error = int(abs(sum(p.astype('int32') for p in pcm)-mix.astype('int32')).max())
        (out/f'{rid:02X}_reads.json').write_text(json.dumps(reads))
        manifest['assets'].append(dict(request=rid,ticks=ticks,
            first_music_inactive=inactive,stem_sum_max_lsb=error,
            loop_ready=False,files={p.name:digest(p.read_bytes()) for p in out.glob(f'{rid:02X}_*.wav')}))
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return dict(output=str(out), assets=len(manifest['assets']), status=manifest['status'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom'); p.add_argument('mode', choices=('evidence','assets'))
    p.add_argument('--out', required=True)
    a = p.parse_args(); rom = T.load_rom(a.rom)
    if a.mode == 'evidence':
        result = evidence(rom)
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(result, indent=2)+'\n')
        print('numeric evidence written; no private streams exported')
    else:
        print(json.dumps(private_assets(rom, a.out)))


if __name__ == '__main__':
    main()

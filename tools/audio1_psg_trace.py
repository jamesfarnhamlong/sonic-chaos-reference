"""AUDIO-1: execute the ORIGINAL Sonic Chaos sound driver and log its SN76489 writes.

    python tools/audio1_psg_trace.py PATH/TO/SonicChaos.sms --summary
    python tools/audio1_psg_trace.py PATH/TO/SonicChaos.sms --pilot --check
    python tools/audio1_psg_trace.py PATH/TO/SonicChaos.sms --dump 0x90 --frames 900 --out build/audio1/90.json

This is NOT an SMS emulator and renders no audio. It maps the driver banks, delivers
a request through the same mailbox the IRQ uses ($DE04), calls the driver entry
($4000) once per simulated update and records every `OUT ($7F),n` PSG write. The
full per-update write log is copyrighted-music-derived, so it is only written to an
explicit --out path (keep it under ignored build/). The committed manifest keeps only
counts, durations and hashes. The ROM SHA-256 is verified before anything runs.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import z80

ROM_SHA256 = 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607'
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'data/audio1/pilot-trace-summary.json'

RETURN = 0x0100
SOUND_BANKS = ((1, 2), (2, 3))             # slot -> bank: sound code in slot1, bank3 in slot2
MUSIC_CH = (0xDE40, 0xDE70, 0xDEA0, 0xDED0)  # tone0, tone1, tone2, noise
SFX_CH = (0xDF00, 0xDF30, 0xDF60)
CHANNELS = MUSIC_CH + SFX_CH
PILOT = (0x90, 0x82, 0x81, 0xBF, 0xA6)
PSG_CLOCK = {'NTSC': 3579545, 'PAL': 3546893}


def load_rom(path):
    rom = Path(path).read_bytes()
    got = hashlib.sha256(rom).hexdigest()
    if got != ROM_SHA256:
        raise SystemExit(f'ROM SHA-256 mismatch: {got}')
    return rom


class Psg:
    """SN76489 register file as seen through the port-$7F byte protocol."""

    def __init__(self):
        self.tone = [0, 0, 0]
        self.noise = 0
        self.att = [15, 15, 15, 15]
        self.latch = 0

    def write(self, v):
        if v & 0x80:
            self.latch = v & 0x70
            ch, is_att, d = (v >> 5) & 3, v & 0x10, v & 15
            if is_att:
                self.att[ch] = d
            elif ch == 3:
                self.noise = d & 7
            else:
                self.tone[ch] = (self.tone[ch] & 0x3F0) | d
        else:
            ch = (self.latch >> 5) & 3
            if self.latch & 0x10:
                self.att[ch] = v & 15
            elif ch == 3:
                self.noise = v & 7
            elif ch < 3:
                self.tone[ch] = (self.tone[ch] & 15) | ((v & 0x3F) << 4)

    def state(self):
        return (tuple(self.tone), self.noise, tuple(self.att))


class Driver:
    def __init__(self, rom):
        import z80 as _z
        self.rom = rom
        self.cpu = _z.Z80Machine()
        self.mem = self.cpu.memory
        self.mem[:0x4000] = rom[:0x4000]
        for slot, bank in SOUND_BANKS:
            self.mem[slot*0x4000:slot*0x4000+0x4000] = rom[bank*0x4000:bank*0x4000+0x4000]
        self.cpu.set_breakpoint(RETURN)
        self.hooks = {}
        self.cpu.set_output_callback(self._out)
        self.cpu.set_input_callback(lambda port: 0xFF)
        self.writes = []
        self.psg = Psg()
        self.mem[0xDE00:0xDF90] = bytes(0x190)
        self.mem[0xDE03] = 0x80   # same idle baseline as accepted AUDIO-0 fixtures
        self.update = 0

    def _out(self, port, value):
        port &= 0xFF
        if port == 0x7F or port == 0x7E:
            self.writes.append((self.update, value & 0xFF))
            self.psg.write(value & 0xFF)

    def call(self, addr):
        self.cpu.pc = addr
        self.cpu.sp = 0xDFE0
        self.mem[self.cpu.sp:self.cpu.sp+2] = RETURN.to_bytes(2, 'little')
        for _ in range(100000):
            self.cpu.ticks_to_stop = 100000
            self.cpu.run()
            pc = self.cpu.pc
            if pc == RETURN:
                return
            if pc in self.hooks:
                self.hooks[pc](self)
                self.cpu.clear_breakpoint(pc)
                self.cpu.ticks_to_stop = 1
                self.cpu.run()
                self.cpu.set_breakpoint(pc)
        raise RuntimeError(f'call ${addr:04X} did not return')

    def hook(self, addr, fn):
        self.hooks[addr] = fn
        self.cpu.set_breakpoint(addr)

    def request(self, rid):
        self.mem[0xDE04] = rid          # IRQ-equivalent mailbox delivery

    def tick(self):
        self.update += 1
        self.call(0x4000)

    def active(self, chans=CHANNELS):
        return [a for a in chans if self.mem[a] & 0x80]

    def music_active(self):
        return any(self.mem[a] & 0x80 for a in MUSIC_CH)


def run_request(rom, rid, frames, pre=None):
    """Return (driver, per-update snapshots). `pre` is an optional callback(driver, update)."""
    d = Driver(rom)
    d.request(rid)
    snaps = []
    for n in range(frames):
        if pre:
            pre(d, n)
        d.tick()
        snaps.append(dict(update=d.update, psg=d.psg.state(),
                          flags=[d.mem[a] for a in CHANNELS],
                          ptr=[d.mem[a+3] | d.mem[a+4] << 8 for a in CHANNELS],
                          tempo=(d.mem[0xDE01], d.mem[0xDE02]), fade=d.mem[0xDE09]))
    return d, snaps


def u16(rom, o):
    return rom[o] | rom[o+1] << 8


def priority_byte(rom, rid):
    return rom[0x906F + (rid & 0x7F) - 1]


def header_facts(rom, rid):
    """Structural header metadata only (no stream payload)."""
    h = u16(rom, 0x90E1 + 2*(rid - 0x81)) + 0x4000
    out = dict(header_rom=h, envelope_table_cpu=u16(rom, h), priority_byte=priority_byte(rom, rid))
    if rid < 0xA0:
        n = rom[h+2]
        out.update(kind='music', channel_count=n, duration_multiplier=rom[h+4], tempo_byte=rom[h+5],
                   channels=[dict(latch=hex(0x80 + 0x20*i), stream_cpu=u16(rom, h+6+4*i),
                                  transpose=rom[h+8+4*i] - (256 if rom[h+8+4*i] > 127 else 0),
                                  volume=rom[h+9+4*i]) for i in range(n)])
    else:
        n = rom[h+3]
        out.update(kind='sfx', duration_multiplier=rom[h+2], stream_count=n,
                   streams=[dict(latch=hex(rom[h+5+6*i]), stream_cpu=u16(rom, h+6+6*i),
                                 transpose=rom[h+8+6*i], volume=rom[h+9+6*i]) for i in range(n)])
    return out


def recurrence(rom, rid, limit=40000):
    """First exact repeat of driver RAM $DE00..$DF8F while the request plays alone.

    Also checks that the PSG write stream of the next full period is byte-identical to
    the first, which is what makes a seamless loop cut of a rendering defensible."""
    d = Driver(rom)
    d.request(rid)
    seen = {}
    for u in range(1, limit):
        d.tick()
        k = bytes(d.mem[0xDE00:0xDF90])
        if k in seen:
            first, period = seen[k], u - seen[k]
            for _ in range(period):
                d.tick()
            win1 = [(uu - first, b) for uu, b in d.writes if first < uu <= first + period]
            win2 = [(uu - first - period, b) for uu, b in d.writes if first + period < uu <= first + 2*period]
            return dict(first_seen_update=first, repeat_update=u, period_updates=period,
                        next_period_psg_writes_identical=win1 == win2, writes_per_period=len(win1))
        seen[k] = u
    return None


def command_usage(rom, rid, frames=3000):
    """Histogram of stream command bytes ($E0..$FF) the driver actually dispatches at $46D9."""
    d = Driver(rom)
    used = {}

    def on_cmd(dd):
        used[dd.cpu.a] = used.get(dd.cpu.a, 0) + 1

    d.hook(0x46D9, on_cmd)
    d.request(rid)
    for _ in range(frames):
        d.tick()
    return {f'0x{k:02X}': v for k, v in sorted(used.items())}


def sfx_facts(rom, rid):
    d = Driver(rom)
    d.request(rid)
    end = None
    slots = set()
    for n in range(1, 600):
        d.tick()
        act = [hex(a) for a in SFX_CH if d.mem[a] & 0x80]
        slots.update(act)
        if not act and end is None:
            end = n
            break
    return dict(sfx_slots_used=sorted(slots), last_active_update=end - 1 if end else None,
                priority_stored_while_active=priority_byte(rom, rid) & 0x7F)


def steal_facts(rom, music, sfx, at=200, span=80):
    """SFX over running music: which music channel is flagged, and when it recovers."""
    d = Driver(rom)
    d.request(music)
    first_flag = restore = None
    for u in range(1, at + span):
        if u == at:
            d.request(sfx)
        d.tick()
        flagged = [i for i, a in enumerate(MUSIC_CH) if d.mem[a] & 4]
        if u >= at and flagged and first_flag is None:
            first_flag = (u, flagged)
        if first_flag and not any(d.mem[a] & 4 for a in MUSIC_CH) and restore is None:
            restore = u
    return dict(music=f'0x{music:02X}', sfx=f'0x{sfx:02X}', request_update=at,
                first_steal_flag_update=first_flag[0] if first_flag else None,
                stolen_music_channel_indices=first_flag[1] if first_flag else None,
                steal_flag_cleared_update=restore)


def summarize(rom, rid, frames=3000):
    d, snaps = run_request(rom, rid, frames)
    log = b''.join(u.to_bytes(4, 'little') + bytes([b]) for u, b in d.writes)
    rec = dict(request_id=f'0x{rid:02X}', header=header_facts(rom, rid),
               stream_commands_executed=command_usage(rom, rid, frames), updates_simulated=frames,
               psg_write_count=len(d.writes), first_psg_write_update=min((u for u, _ in d.writes), default=None),
               write_log_sha256=hashlib.sha256(log).hexdigest(),
               write_log_sha256_note='hash of (update:u32le, byte) records for the simulated span; not audio')
    if rid < 0xA0:
        rec['exact_driver_state_recurrence'] = recurrence(rom, rid)
        rec['music_channels_inactive_within_span'] = not d.music_active()
    else:
        rec.update(sfx_facts(rom, rid))
        rec['steal_over_0x81'] = steal_facts(rom, 0x81, rid)
    return rec


def insitu_compare(rom, frames=4000):
    """Cross-check the isolated driver against the game's own IRQ path (sms_frame_harness).

    Boots the ROM unattended in the repo's approximate SMS frame harness and records, per
    driver entry ($4000 with the sound bank mapped): the mailbox byte, the pause/fade
    control bytes $DE08..$DE0B (written by game code) and every PSG byte emitted. The
    isolated Driver then replays ONLY those inputs and must emit identical PSG bytes tick
    for tick. Evidence label: EMULATED ORIGINAL FRAMES (approximate VDP/timing; not hardware)."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import sms_frame_harness as H

    class Sms(H.SMS):
        cur = None

        def _out(self, port, value):
            if (port & 0xFF) == 0x7F and self.cur is not None:
                self.cur.append(value)
            return super()._out(port, value)

    m = Sms(rom)
    ticks, inputs, per_frame = [], [], {}

    def hook(mm):
        if mm.slot[1] != 2:          # only the sound-bank copy of $4000
            return
        inputs.append((mm.mem[0xDE04], tuple(mm.mem[0xDE08:0xDE0C])))
        per_frame[mm.frame] = per_frame.get(mm.frame, 0) + 1
        mm.cur = []
        ticks.append(mm.cur)

    m.add_pc_hook(0x4000, hook)
    for _ in range(frames):
        m.run_frame()
    reqs = [(t, r) for t, (r, _) in enumerate(inputs) if r]
    if not reqs:
        return dict(error='no request reached the driver in the simulated frames')
    start = reqs[0][0]
    d = Driver(rom)
    match, stop = 0, 'span end'
    for t in range(start, len(ticks) - 1):       # last captured tick may be partial
        req, ctl = inputs[t]
        if req:
            d.request(req)
        d.mem[0xDE08] = ctl[0]
        if ctl[1] and not d.mem[0xDE09]:        # game-side direct fade start ($18E1)
            d.mem[0xDE09], d.mem[0xDE0A], d.mem[0xDE0B] = ctl[1:]
        w0 = len(d.writes)
        d.tick()
        if [b for _, b in d.writes[w0:]] != ticks[t]:
            stop = f'PSG bytes differ at driver tick {t}'
            break
        match += 1
    window = [per_frame.get(f, 0) for f in range(200, 260)]
    return dict(evidence='EMULATED ORIGINAL FRAMES via tools/sms_frame_harness.py (approximate; not hardware)',
                frames_simulated=frames, driver_ticks_captured=len(ticks), region_flag_d12d=m.mem[0xD12D],
                driver_entries_per_60_frames=sum(window),
                requests_replayed=[dict(tick=t, id=f'0x{r:02X}') for t, r in reqs],
                game_fade_starts=[t for t, (_, c) in enumerate(inputs) if c[1] and (t == 0 or not inputs[t-1][1][1])],
                first_request_tick=start, consecutive_identical_ticks=match, stopped_because=stop)


def write_vgm(path, writes, updates, clock):
    """Minimal VGM 1.50: SN76489 only, one 735-sample wait per 60 Hz driver update."""
    body = bytearray()
    cur = 1
    by = {}
    for u, b in writes:
        by.setdefault(u, []).append(b)
    for u in range(1, updates + 1):
        for b in by.get(u, ()):
            body += bytes((0x50, b))
        body += bytes((0x62,))
    body += bytes((0x66,))
    hdr = bytearray(0x40)
    hdr[0:4] = b'Vgm '
    hdr[0x08:0x0C] = (0x150).to_bytes(4, 'little')
    hdr[0x0C:0x10] = clock.to_bytes(4, 'little')
    hdr[0x18:0x1C] = (updates * 735).to_bytes(4, 'little')
    hdr[0x24:0x28] = (60).to_bytes(4, 'little')
    hdr[0x28:0x2A] = (0x0009).to_bytes(2, 'little')    # SEGA VDP PSG feedback taps (bits 0 and 3)
    hdr[0x2A] = 16                                     # 16-bit noise shift register
    hdr[0x34:0x38] = (0x0C).to_bytes(4, 'little')
    data = bytes(hdr) + bytes(body)
    data = data[:4] + (len(data) - 4).to_bytes(4, 'little') + data[8:]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(data)
    return len(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('rom')
    ap.add_argument('--summary', action='store_true')
    ap.add_argument('--pilot', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--dump', type=lambda x: int(x, 0))
    ap.add_argument('--frames', type=int, default=900)
    ap.add_argument('--out')
    ap.add_argument('--insitu', action='store_true')
    ap.add_argument('--vgm', type=lambda x: int(x, 0), help='export request as a local VGM (keep under ignored build/)')
    ap.add_argument('--clock', type=int, default=PSG_CLOCK['PAL'])
    a = ap.parse_args()
    rom = load_rom(a.rom)
    if a.insitu:
        print(json.dumps(insitu_compare(rom), indent=1))
        return
    if a.vgm is not None:
        d, _ = run_request(rom, a.vgm, a.frames)
        n = write_vgm(a.out or f'build/audio1/{a.vgm:02X}.vgm', d.writes, a.frames, a.clock)
        print(f'wrote {n} bytes; derived from copyrighted ROM data, do not commit')
        return
    if a.dump is not None:
        d, snaps = run_request(rom, a.dump, a.frames)
        out = dict(rom_sha256=ROM_SHA256, request=a.dump, writes=d.writes)
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(json.dumps(out))
            print(f'wrote {len(d.writes)} PSG writes to {a.out}')
        else:
            print(len(d.writes), 'PSG writes (use --out to save)')
        return
    if a.pilot or a.summary:
        res = dict(rom_sha256=ROM_SHA256, psg_ticks_per_second_nominal=60,
                   method='original driver executed via kosarev/z80, banks 2/3 mapped, one $4000 call per update; not an SMS emulator',
                   requests=[summarize(rom, r) for r in PILOT])
        text = json.dumps(res, indent=1, sort_keys=True) + '\n'
        if a.check:
            if MANIFEST.exists() and MANIFEST.read_text() != text:
                print('MISMATCH vs', MANIFEST)
                sys.exit(1)
            print('ok' if MANIFEST.exists() else 'no committed manifest to compare; printed only')
        else:
            MANIFEST.parent.mkdir(parents=True, exist_ok=True)
            MANIFEST.write_text(text)
            print('wrote', MANIFEST)
        print(text)


if __name__ == '__main__':
    main()

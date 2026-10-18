"""AUDIO-1B: render the original driver's PSG output to audible WAV files (local, ignored).

Pipeline: hash-verified ROM -> original Z80 driver (tools/audio1_psg_trace.py) -> PSG bytes per
driver tick -> VGM 1.50 -> renderer (Game_Music_Emu via ctypes, libvgm via its vgm2wav) -> WAV.

Nothing generated here may be committed: VGM and WAV data are derived from the ROM. Output goes
under ignored build/. See docs/audio1b-render-validation.md for setup and findings.

    python tools/audio1b_render.py ROM samples --out build/audio1/audio1b
    python tools/audio1b_render.py ROM validate --out build/audio1/audio1b

Environment: AUDIO1B_GME_LIB (libgme shared library), AUDIO1B_VGM2WAV (patched libvgm vgm2wav).
"""
import argparse
import ctypes
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audio1_psg_trace as T   # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RATE = 44100
TICK_SAMPLES = 735                 # 44100 / 60 exactly: one driver tick per VGM wait
PAL = T.PSG_CLOCK['PAL']           # provisional, per AUDIO-1B authorisation
DEFAULT_OUT = ROOT / 'build/audio1/audio1b'
SUMMARY = ROOT / 'data/audio1b/render-validation-summary.json'
PINS = dict(game_music_emu=dict(tag='0.6.5', commit='9e23d10f9fd2a6a2f33b10912dd8dc7153258995', licence='LGPL-2.1'),
            libvgm=dict(commit='a6eed945ecf4e5a25cf82004779c6f7e4fd5c319',
                        licence='no top-level licence file; sn76496.c BSD-3-Clause (Salmoria); sn76489.c (Maxim) states none'))

SAMPLES = (                        # (file stem, request id, kind, ticks or None = until silent)
    ('90_opening', 0x90, 'music', 900),
    ('82_title', 0x82, 'music', 900),
    ('81_thz', 0x81, 'music', 900),
    ('BF_ring', 0xBF, 'sfx', None),
    ('A6_spring', 0xA6, 'sfx', None),
)


# ------------------------------------------------------------------ driver capture
def run_scenario(rom, events, ticks, hooks=None):
    """Run the original driver. events: {tick(1-based): [('req', id) | ('fade', (de09,de0a,de0b))]}.

    Values are applied immediately BEFORE that tick, mirroring the game: the IRQ stores the
    mailbox byte, then calls the driver. Returns per-tick PSG bytes and the Driver."""
    d = T.Driver(rom)
    for addr, fn in (hooks or {}).items():
        d.hook(addr, fn)
    per_tick = []
    for t in range(1, ticks + 1):
        for kind, val in events.get(t, ()):
            if kind == 'req':
                d.request(val)
            elif kind == 'fade':
                d.mem[0xDE09], d.mem[0xDE0A], d.mem[0xDE0B] = val
        w0 = len(d.writes)
        d.tick()
        per_tick.append([b for _, b in d.writes[w0:]])
    return per_tick, d



def attenuation_stem(per_tick, keep):
    """Stem that keeps the complete write schedule but forces every OTHER channel's attenuation to 15.

    Keeping every write preserves the renderer's internal time segmentation, so the stem shares the
    mix's oscillator/noise phase (verified: GME phase of idle oscillators depends on segmentation, so
    deleting other channels' writes would change the waveform, not just remove channels)."""
    out, latch = [], 0
    for writes in per_tick:
        row = []
        for v in writes:
            if v & 0x80:
                latch = v
            ch, is_att = (latch >> 5) & 3, bool(latch & 0x10)
            if is_att and ch != keep:
                v = (v & 0xF0) | 0x0F if v & 0x80 else (v & 0xF0) | 0x0F
            row.append(v)
        out.append(row)
    # other channels may hold a non-15 attenuation from before the first tick: force at start
    pre = [0x90 | (c << 5) | 0x0F for c in range(4) if c != keep]
    out[0] = pre + out[0]
    return out


def sfx_ticks_until_silent(rom, rid, limit=400):
    """First tick (inclusive) after which every PSG attenuation is 15 (the release tick)."""
    d = T.Driver(rom)
    d.request(rid)
    for t in range(1, limit):
        d.tick()
        if all(a == 15 for a in d.psg.att):
            return t
    raise RuntimeError(f'${rid:02X} never reached silence in {limit} ticks')


# ------------------------------------------------------------------ VGM
def build_vgm(per_tick, clock=PAL, tick_samples=TICK_SAMPLES):
    """VGM 1.50, SN76489 only. Writes for tick k happen at sample (k-1)*735; one wait per tick."""
    body = bytearray()
    for writes in per_tick:
        for b in writes:
            body += bytes((0x50, b))
        body += bytes((0x61,)) + struct.pack('<H', tick_samples)
    body += b'\x66'
    hdr = bytearray(0x40)
    hdr[0:4] = b'Vgm '
    hdr[0x08:0x0C] = struct.pack('<I', 0x150)
    hdr[0x0C:0x10] = struct.pack('<I', clock)
    hdr[0x18:0x1C] = struct.pack('<I', len(per_tick) * tick_samples)
    hdr[0x24:0x28] = struct.pack('<I', 60)
    hdr[0x28:0x2A] = struct.pack('<H', 0x0009)     # Sega VDP PSG noise taps: bits 0 and 3
    hdr[0x2A] = 16                                 # 16-bit noise shift register
    hdr[0x34:0x38] = struct.pack('<I', 0x0C)       # data starts at 0x40
    data = bytes(hdr) + bytes(body)
    return data[:4] + struct.pack('<I', len(data) - 4) + data[8:]


def parse_vgm(data):
    """Independent VGM reader for the subset we emit. Returns (header, [(sample_time, byte)], total)."""
    if data[:4] != b'Vgm ':
        raise ValueError('not a VGM')
    h = dict(eof=struct.unpack_from('<I', data, 4)[0], version=struct.unpack_from('<I', data, 8)[0],
             sn_clock=struct.unpack_from('<I', data, 0x0C)[0], total_samples=struct.unpack_from('<I', data, 0x18)[0],
             loop_offset=struct.unpack_from('<I', data, 0x1C)[0], feedback=struct.unpack_from('<H', data, 0x28)[0],
             width=data[0x2A], data_offset=struct.unpack_from('<I', data, 0x34)[0])
    pos = 0x34 + h['data_offset']
    t, events = 0, []
    while True:
        op = data[pos]
        if op == 0x50:
            events.append((t, data[pos + 1]))
            pos += 2
        elif op == 0x61:
            t += struct.unpack_from('<H', data, pos + 1)[0]
            pos += 3
        elif op == 0x62:
            t += 735
            pos += 1
        elif op == 0x63:
            t += 882
            pos += 1
        elif op == 0x66:
            break
        else:
            raise ValueError(f'unsupported VGM opcode {op:#x} at {pos:#x}')
    return h, events, t


def vgm_matches(per_tick, data, clock=PAL):
    """Round-trip check: parsed VGM events equal the driver capture, tick for tick."""
    h, events, total = parse_vgm(data)
    want = [((k) * TICK_SAMPLES, b) for k, w in enumerate(per_tick) for b in w]
    problems = []
    if events != want:
        problems.append('event list differs')
    if total != len(per_tick) * TICK_SAMPLES or h['total_samples'] != total:
        problems.append('sample count differs')
    if h['sn_clock'] != clock or h['feedback'] != 0x0009 or h['width'] != 16 or h['loop_offset'] != 0:
        problems.append('header fields differ')
    if h['eof'] != len(data) - 4:
        problems.append('EOF offset differs')
    return problems



def kss_bytes(rom, rid):
    """Wrap the unmodified sound region (ROM $8000..$FFFF = CPU $4000..$BFFF) plus a 15-byte stub as a
    KSS file, so Game_Music_Emu's own Z80 core (Kss_Cpu) can execute the original driver. This is the
    independent-Z80 cross-check: no kosarev/z80, no repo harness. Contains ROM bytes: local only."""
    init = bytes([0x3E, 0x80, 0x32, 0x03, 0xDE,        # LD A,$80 ; LD ($DE03),A  (same idle baseline as the harness)
                  0x3E, rid, 0x32, 0x04, 0xDE,         # LD A,id  ; LD ($DE04),A  (mailbox)
                  0xC9])                               # RET
    play = bytes([0xCD, 0x00, 0x40, 0xC9])             # CALL $4000 ; RET   (once per 1/60 s)
    stub_at = 0xC000
    blob = bytes(rom[0x8000:0x10000]) + init + play
    hdr = b'KSCC' + struct.pack('<HHHH', 0x4000, len(blob), stub_at, stub_at + len(init)) + bytes([0, 0, 0, 0x02])
    return hdr + blob


# ------------------------------------------------------------------ WAV
def write_wav(path, pcm):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(np.ascontiguousarray(pcm, dtype='<i2').tobytes())


def read_wav(path):
    with wave.open(str(path), 'rb') as w:
        assert w.getsampwidth() == 2 and w.getframerate() == RATE, (w.getsampwidth(), w.getframerate())
        ch = w.getnchannels()
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2')
    return raw.reshape(-1, ch)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def pcm_sha256(pcm):
    return sha256(np.ascontiguousarray(pcm, dtype='<i2').tobytes())


# ------------------------------------------------------------------ Game_Music_Emu
class EqStruct(ctypes.Structure):
    _fields_ = [('treble', ctypes.c_double), ('bass', ctypes.c_double)] + [(f'd{i}', ctypes.c_double) for i in range(2, 10)]


class Gme:
    """Thin ctypes binding. Every non-null error string raises: failures are never swallowed."""

    def __init__(self, lib=None):
        lib = lib or os.environ.get('AUDIO1B_GME_LIB')
        if not lib or not Path(lib).exists():
            raise FileNotFoundError('set AUDIO1B_GME_LIB to a built libgme shared library')
        self.path = str(lib)
        L = self.lib = ctypes.CDLL(self.path)
        L.gme_open_data.argtypes = [ctypes.c_void_p, ctypes.c_long, ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
        L.gme_open_data.restype = ctypes.c_char_p
        for fn in ('gme_start_track', 'gme_play'):
            getattr(L, fn).restype = ctypes.c_char_p
        L.gme_start_track.argtypes = [ctypes.c_void_p, ctypes.c_int]
        L.gme_play.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
        L.gme_delete.argtypes = [ctypes.c_void_p]
        L.gme_mute_voices.argtypes = [ctypes.c_void_p, ctypes.c_int]
        L.gme_ignore_silence.argtypes = [ctypes.c_void_p, ctypes.c_int]
        L.gme_set_fade.argtypes = [ctypes.c_void_p, ctypes.c_int]
        L.gme_set_equalizer.argtypes = [ctypes.c_void_p, ctypes.POINTER(EqStruct)]
        L.gme_equalizer.argtypes = [ctypes.c_void_p, ctypes.POINTER(EqStruct)]
        L.gme_set_stereo_depth.argtypes = [ctypes.c_void_p, ctypes.c_double]
        L.gme_enable_accuracy.argtypes = [ctypes.c_void_p, ctypes.c_int]
        L.gme_voice_count.argtypes = [ctypes.c_void_p]
        L.gme_voice_name.argtypes = [ctypes.c_void_p, ctypes.c_int]
        L.gme_voice_name.restype = ctypes.c_char_p
        L.gme_set_autoload_playback_limit.argtypes = [ctypes.c_void_p, ctypes.c_int]

    @staticmethod
    def _chk(err):
        if err:
            raise RuntimeError(f'Game_Music_Emu error: {err.decode()}')

    def render(self, vgm, samples, eq='default', mute_mask=0, chunk=4096):
        """Render exactly `samples` stereo frames at 44.1 kHz. eq: 'default' keeps GME's VGM
        equalizer (treble -14 dB, bass 80 Hz); 'flat' sets treble 0 dB, bass 1 Hz."""
        L = self.lib
        emu = ctypes.c_void_p()
        buf = ctypes.create_string_buffer(vgm, len(vgm))
        self._chk(L.gme_open_data(ctypes.cast(buf, ctypes.c_void_p), len(vgm), ctypes.byref(emu), RATE))
        try:
            # NOTE (verified, GME 0.6.5): equalizer and voice-mute calls made AFTER gme_start_track
            # are silently ignored for VGM; they must precede it.
            if eq == 'flat':
                e = EqStruct()
                L.gme_equalizer(emu, ctypes.byref(e))
                e.treble, e.bass = 0.0, 1.0
                L.gme_set_equalizer(emu, ctypes.byref(e))
            elif eq != 'default':
                raise ValueError(eq)
            if mute_mask:
                L.gme_mute_voices(emu, mute_mask)
            self._chk(L.gme_start_track(emu, 0))
            L.gme_ignore_silence(emu, 1)
            L.gme_set_autoload_playback_limit(emu, 0)
            L.gme_set_fade(emu, 1_000_000_000)
            out = np.zeros(samples * 2, dtype='<i2')
            done = 0
            while done < samples:
                n = min(chunk, samples - done)
                block = (ctypes.c_short * (n * 2))()
                self._chk(L.gme_play(emu, n * 2, block))
                out[done * 2:(done + n) * 2] = np.frombuffer(block, dtype='<i2')
                done += n
            return out.reshape(-1, 2)
        finally:
            L.gme_delete(emu)

    def describe(self, vgm):
        L = self.lib
        emu = ctypes.c_void_p()
        buf = ctypes.create_string_buffer(vgm, len(vgm))
        self._chk(L.gme_open_data(ctypes.cast(buf, ctypes.c_void_p), len(vgm), ctypes.byref(emu), RATE))
        try:
            e = EqStruct()
            L.gme_equalizer(emu, ctypes.byref(e))
            return dict(voices=[L.gme_voice_name(emu, i).decode() for i in range(L.gme_voice_count(emu))],
                        default_treble_db=e.treble, default_bass_hz=e.bass, library=self.path)
        finally:
            L.gme_delete(emu)


# ------------------------------------------------------------------ libvgm
def render_libvgm(vgm, samples, core, exe=None):
    """Render through libvgm's vgm2wav with a chosen SN76489 core ('MAME' or 'MAXM')."""
    exe = exe or os.environ.get('AUDIO1B_VGM2WAV')
    if not exe or not Path(exe).exists():
        raise FileNotFoundError('set AUDIO1B_VGM2WAV to the built vgm2wav')
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / 'in.vgm', Path(tmp) / 'out.wav'
        src.write_bytes(vgm)
        env = dict(os.environ, VGM_SN_CORE=core)
        r = subprocess.run([exe, '--samplerate', '44100', '--bps', '16', '--fade', '0', '--loops', '1', str(src), str(dst)],
                           capture_output=True, text=True, env=env)
        if r.returncode != 0 or not dst.exists():
            raise RuntimeError(f'vgm2wav failed ({r.returncode}): {r.stderr.strip()}')
        pcm = read_wav(dst)
    return pcm, r.stderr


# ------------------------------------------------------------------ renderer abstraction
class GmeRenderer:
    def __init__(self, gme, eq):
        self.gme, self.eq, self.name = gme, eq, f'gme_{eq}'

    def render(self, vgm, samples):
        return self.gme.render(vgm, samples, eq=self.eq)


class LibvgmRenderer:
    def __init__(self, core, exe=None):
        self.core, self.exe = core, exe
        self.name = {'MAME': 'libvgm_mame', 'MAXM': 'libvgm_maxim'}[core]

    def render(self, vgm, samples):
        pcm, _ = render_libvgm(vgm, samples, self.core, self.exe)
        if len(pcm) < samples:
            pcm = np.vstack([pcm, np.zeros((samples - len(pcm), 2), dtype=pcm.dtype)])
        return pcm[:samples]


PRIMARY = 'libvgm_mame'


def available_renderers():
    out = {}
    exe = os.environ.get('AUDIO1B_VGM2WAV')
    if exe and Path(exe).exists():
        out[PRIMARY] = LibvgmRenderer('MAME')
        out['libvgm_maxim'] = LibvgmRenderer('MAXM')
    lib = os.environ.get('AUDIO1B_GME_LIB')
    if lib and Path(lib).exists():
        g = Gme(lib)
        out['gme_flat'] = GmeRenderer(g, 'flat')
        out['gme_default'] = GmeRenderer(g, 'default')
    return out


# ------------------------------------------------------------------ build the five samples
def build_samples(rom, out_dir, renderer):
    out_dir = Path(out_dir) / renderer.name
    rows = []
    for stem, rid, kind, ticks in SAMPLES:
        n = ticks or sfx_ticks_until_silent(rom, rid)
        per_tick, _ = run_scenario(rom, {1: [('req', rid)]}, n)
        vgm = build_vgm(per_tick)
        problems = vgm_matches(per_tick, vgm)
        if problems:
            raise RuntimeError(f'VGM export check failed for ${rid:02X}: {problems}')
        pcm = renderer.render(vgm, n * TICK_SAMPLES)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f'{stem}.vgm').write_bytes(vgm)
        write_wav(out_dir / f'{stem}.wav', pcm)
        rows.append(dict(renderer=renderer.name, file=stem, request_id=f'0x{rid:02X}', ticks=n, seconds=round(n / 60, 4),
                         samples=n * TICK_SAMPLES, vgm_sha256=sha256(vgm), wav_sha256=sha256((out_dir / f'{stem}.wav').read_bytes()),
                         pcm_sha256=pcm_sha256(pcm), vgm_bytes=len(vgm), psg_writes=sum(len(w) for w in per_tick)))
    return rows


def environment():
    import platform
    return dict(python=platform.python_version(), numpy=np.__version__, platform=platform.platform(), machine=platform.machine(),
                renderer_pins=PINS)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('rom')
    ap.add_argument('command', choices=['samples', 'validate', 'timeline'])
    ap.add_argument('--request', type=lambda x: int(x, 0), default=0x81)
    ap.add_argument('--ticks', type=int, default=3781)
    ap.add_argument('--out', default=str(DEFAULT_OUT))
    ap.add_argument('--renderer', default=None, help='default: every available renderer')
    ap.add_argument('--write-summary', action='store_true', help='write data/audio1b/render-validation-summary.json (metrics and hashes only)')
    a = ap.parse_args()
    rom = T.load_rom(a.rom)
    if a.command == 'timeline':
        import audio1b_checks as C
        reads, pt = C.stream_reads(rom, a.request, a.ticks)
        out = Path(a.out) / f'tone2_stream_reads_{a.request:02X}.json'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(dict(request=a.request, ticks=a.ticks, tone2_stream_read_ticks=reads)))
        print(json.dumps(dict(file=str(out), reads=len(reads), first=reads[:5], sha256=sha256(out.read_bytes()))))
        return
    rends = available_renderers()
    if not rends:
        raise SystemExit('no renderer available: set AUDIO1B_VGM2WAV and/or AUDIO1B_GME_LIB (see docs/audio1b-render-validation.md)')
    if a.command == 'samples':
        rows = []
        for name, r in rends.items():
            if a.renderer in (None, name):
                rows += build_samples(rom, a.out, r)
        print(json.dumps(rows, indent=1))
    else:
        import audio1b_checks as C
        res = C.run_all(rom, a.out, rends)
        res['environment'] = environment()
        text = json.dumps(res, indent=1, sort_keys=True, default=str) + '\n'
        Path(a.out).mkdir(parents=True, exist_ok=True)
        (Path(a.out) / 'validation.json').write_text(text)
        if a.write_summary:
            SUMMARY.parent.mkdir(parents=True, exist_ok=True)
            SUMMARY.write_text(text)
        print(text)


if __name__ == '__main__':
    main()

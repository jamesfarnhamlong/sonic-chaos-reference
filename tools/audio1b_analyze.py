"""AUDIO-1B: independent reference PSG synthesiser and audio measurements.

The synthesiser follows the SN76489 rules directly (tone counters, 2 dB attenuation,
noise LFSR) and shares no code with Game_Music_Emu or libvgm. It is deliberately simple
(box-filter resampling, aliasing allowed): its job is to cross-check pitch, timing,
envelopes and noise sequence of the real renderers, not to be a listening renderer.

Written by the same author as the exporter, so agreement with it is NOT independent
evidence about the exporter; it is independent of the two third-party renderer cores.
"""
import numpy as np

ATT = np.array([10 ** (-2.0 * n / 20.0) for n in range(15)] + [0.0])

# Noise LFSR variants (shift left-to-right: new = parity(reg & taps) << (width-1) | reg >> 1)
SEGA = dict(width=16, taps=0x0009)    # Sega VDP PSG (Master System / Game Gear / Mega Drive)
TI = dict(width=15, taps=0x0003)      # classic TI SN76489 for contrast


def lfsr_bits(n, variant=SEGA, white=True):
    reg = 1 << (variant['width'] - 1)
    out = np.zeros(n, dtype=np.uint8)
    for i in range(n):
        out[i] = reg & 1
        fb = bin(reg & variant['taps']).count('1') & 1 if white else reg & 1
        reg = (reg >> 1) | (fb << (variant['width'] - 1))
    return out


def decode_ticks(per_tick):
    """Replay per-tick PSG bytes into per-tick register snapshots (state AFTER the tick's writes)."""
    tone, noise, att, latch = [1, 1, 1], 0, [15] * 4, 0
    snaps, noise_written = [], []
    for writes in per_tick:
        nw = False
        for v in writes:
            if v & 0x80:
                latch = v & 0x70
                ch, is_att, d = (v >> 5) & 3, v & 0x10, v & 15
                if is_att:
                    att[ch] = d
                elif ch == 3:
                    noise, nw = d & 7, True
                else:
                    tone[ch] = (tone[ch] & 0x3F0) | d
            else:
                ch = (latch >> 5) & 3
                if latch & 0x10:
                    att[ch] = v & 15
                elif ch == 3:
                    noise, nw = v & 7, True
                else:
                    tone[ch] = (tone[ch] & 15) | ((v & 0x3F) << 4)
        snaps.append((tuple(tone), noise, tuple(att)))
        noise_written.append(nw)
    return snaps, noise_written


def reference_render(per_tick, clock, rate=44100, tick_samples=735, channels=(0, 1, 2, 3)):
    """Return float32 mono samples, len = ticks * tick_samples."""
    snaps, nwrite = decode_ticks(per_tick)
    f_psg = clock / 16.0
    n_ticks = len(per_tick)
    total = n_ticks * tick_samples
    # PSG-step boundary of every output-sample edge
    edges = np.floor(np.arange(total + 1) * (f_psg / rate) + 0.5).astype(np.int64)
    out = np.zeros(total, dtype=np.float64)
    cnt = [1, 1, 1]
    state = [0, 0, 0]
    white_seq = lfsr_bits(65536, SEGA, True)
    shifts = 0
    nstate, ncnt = 0, 1
    noise_edge_prev = 0
    for t in range(n_ticks):
        s0, s1 = t * tick_samples, (t + 1) * tick_samples
        j0, j1 = edges[s0], edges[s1]
        n = int(j1 - j0)
        tone, noise, att = snaps[t]
        steps = np.arange(n)
        sq = []
        for c in range(3):
            period = max(int(tone[c]), 1)
            first = cnt[c] - 1
            if first < 0:
                first = 0
            ntog = np.where(steps >= first, (steps - first) // period + 1, 0)
            sq.append((state[c] + ntog) & 1)
            total_tog = int(ntog[-1]) if n else 0
            if total_tog:
                last_tog = first + (total_tog - 1) * period
                cnt[c] = period - (n - 1 - last_tog)
            else:
                cnt[c] = cnt[c] - n
            state[c] = int((state[c] + total_tog) & 1)
        # noise
        if nwrite[t]:
            shifts, nstate = 0, 0
        nf = noise & 3
        if nf == 3:
            prev = np.concatenate(([noise_edge_prev], sq[2][:-1]))
            shift_idx = np.cumsum((sq[2] == 1) & (prev == 0))
            noise_edge_prev = int(sq[2][-1]) if n else noise_edge_prev
        else:
            half = 16 << nf
            first = ncnt - 1
            ntog = np.where(steps >= first, (steps - first) // half + 1, 0)
            tog_state = (nstate + ntog) & 1
            prev = np.concatenate(([nstate], tog_state[:-1]))
            shift_idx = np.cumsum((tog_state == 1) & (prev == 0))
            total_tog = int(ntog[-1]) if n else 0
            if total_tog:
                last_tog = first + (total_tog - 1) * half
                ncnt = half - (n - 1 - last_tog)
            else:
                ncnt = ncnt - n
            nstate = int(tog_state[-1]) if n else nstate
        nbits = white_seq[(shifts + shift_idx) % 65535] if (noise & 4) else lfsr_bits_cached(shifts, shift_idx)
        shifts += int(shift_idx[-1]) if n else 0
        sig = np.zeros(n)
        for c in range(3):
            if c in channels:
                sig += ATT[att[c]] * (sq[c] * 2.0 - 1.0)
        if 3 in channels:
            sig += ATT[att[3]] * (nbits.astype(np.float64) * 2.0 - 1.0)
        # box-filter down to the output rate
        idx = edges[s0:s1 + 1] - j0
        csum = np.concatenate(([0.0], np.cumsum(sig)))
        seg = (csum[idx[1:]] - csum[idx[:-1]]) / np.maximum(np.diff(idx), 1)
        out[s0:s1] = seg
    return (out / 4.0).astype(np.float32)


_periodic_cache = {}


def lfsr_bits_cached(shifts, shift_idx):
    if 'p' not in _periodic_cache:
        _periodic_cache['p'] = lfsr_bits(65536, SEGA, False)
    return _periodic_cache['p'][(shifts + shift_idx) % 16]


# ---------------------------------------------------------------- measurements
def mono(pcm):
    """int16 [n,2] -> float32 mono; also reports whether the channels are identical."""
    return pcm.astype(np.float32).mean(axis=1) / 32768.0, bool(np.array_equal(pcm[:, 0], pcm[:, 1]))


def tick_rms(x, tick_samples=735, ac=True):
    """Per-tick RMS. ac=True removes each tick's mean first so renderer DC/bass-filter tails
    are not mistaken for sound."""
    n = len(x) // tick_samples
    seg = x[:n * tick_samples].reshape(n, tick_samples).astype(np.float64)
    if ac:
        seg = seg - seg.mean(axis=1, keepdims=True)
    return np.sqrt((seg ** 2).mean(axis=1))


def estimate_hz(seg, rate=44100, fmin=60.0, fmax=3000.0):
    """Autocorrelation pitch estimate for a short, mostly periodic segment."""
    seg = seg - seg.mean()
    if np.abs(seg).max() < 1e-4:
        return None
    n = len(seg)
    ac = np.correlate(seg, seg, mode='full')[n - 1:]
    lo, hi = int(rate / fmax), min(int(rate / fmin), n - 2)
    if hi <= lo:
        return None
    k = lo + int(np.argmax(ac[lo:hi]))
    if 0 < k < n - 1:
        a, b, c = ac[k - 1], ac[k], ac[k + 1]
        den = a - 2 * b + c
        shift = 0.5 * (a - c) / den if den else 0.0
        k = k + shift
    return rate / k


def corr(a, b):
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])

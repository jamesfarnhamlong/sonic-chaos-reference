"""AUDIO-1B validation experiments. Everything here is measured; nothing is asserted by name.

Evidence labels used in results:
  harness-only  - compared against the AUDIO-1 driver harness / the exporter (same author)
  independent   - compared against a separately written renderer core (libvgm MAME / Maxim cores)
                  or the independent numpy reference synthesiser in audio1b_analyze.py
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audio1_psg_trace as T       # noqa: E402
import audio1b_analyze as A        # noqa: E402
import audio1b_render as R         # noqa: E402

TS = R.TICK_SAMPLES
SILENT_REL = 0.02        # a tick is "silent" when its AC RMS < 2 % of the median audible-tick RMS
ROM_PATH = [None]


# ------------------------------------------------------------------ 1. audio sanity
def sanity(pcm):
    x, same = A.mono(pcm)
    peak = int(np.abs(pcm.astype(np.int32)).max())
    nz = np.flatnonzero(np.abs(pcm[:, 0]) > 2)
    return dict(frames=len(pcm), stereo_channels_identical=same, peak=peak,
                clipped_frames=int((np.abs(pcm.astype(np.int32)) >= 32767).any(axis=1).sum()),
                headroom_db=round(float(20 * np.log10(32767 / max(peak, 1))), 2), rms=round(float(np.sqrt((x ** 2).mean())), 5),
                dc_offset=round(float(x.mean()), 6), leading_silent_frames=int(nz[0]) if len(nz) else len(pcm),
                trailing_silent_frames=int(len(pcm) - 1 - nz[-1]) if len(nz) else len(pcm), non_silent=bool(len(nz) > 0))


# ------------------------------------------------------------------ 2. stems, pitch, durations
def stems(renderer, per_tick, n_samples):
    """Per-PSG-channel stems via attenuation forcing (renderer-independent, schedule-preserving)."""
    return [renderer.render(R.build_vgm(R.attenuation_stem(per_tick, v)), n_samples) for v in range(4)]


def expected_gate(snaps, c):
    """Per tick: should channel c be audible according to the PSG register file."""
    if c < 3:
        return np.array([s[2][c] < 15 and s[0][c] > 1 for s in snaps])
    return np.array([s[2][3] < 15 for s in snaps])


def pitch_windows(per_tick, stem_pcm, clock=R.PAL, min_ticks=3):
    """Constant-period, constant-attenuation windows of >= min_ticks: (ch, first tick, len, exp Hz, measured Hz, cents)."""
    snaps, _ = A.decode_ticks(per_tick)
    out = []
    for c in range(3):
        x, _ = A.mono(stem_pcm[c])
        gate = expected_gate(snaps, c)
        periods = [s[0][c] for s in snaps]
        t = 0
        while t < len(snaps):
            if not gate[t]:
                t += 1
                continue
            u = t
            while u + 1 < len(snaps) and gate[u + 1] and periods[u + 1] == periods[t] and snaps[u + 1][2][c] == snaps[t][2][c]:
                u += 1
            if u - t + 1 >= min_ticks:
                exp = clock / (32.0 * periods[t])
                meas = A.estimate_hz(x[t * TS:(u + 1) * TS], fmin=max(40.0, exp * 0.5), fmax=min(8000.0, exp * 1.6))
                if meas:
                    out.append((c, t + 1, u - t + 1, exp, float(meas), float(1200 * np.log2(meas / exp))))
            t = u + 1
    return out


def pitch_report(per_tick, stem_pcm, clock=R.PAL, off_cents=25.0, min_ticks=3):
    w = pitch_windows(per_tick, stem_pcm, clock, min_ticks)
    cents = np.array([abs(o[5]) for o in w])
    bad = [o for o in w if abs(o[5]) > off_cents]
    per_ch = {c: dict(windows=sum(1 for o in w if o[0] == c), off=sum(1 for o in bad if o[0] == c),
                      first_off_tick=min([o[1] for o in bad if o[0] == c], default=None)) for c in range(3)}
    return dict(windows=len(w), median_abs_cents=round(float(np.median(cents)), 3) if len(cents) else None,
                p95_abs_cents=round(float(np.percentile(cents, 95)), 3) if len(cents) else None,
                max_abs_cents=round(float(cents.max()), 3) if len(cents) else None,
                windows_off_by_more_than_25_cents=len(bad), per_channel=per_ch)


def duration_report(per_tick, stem_pcm):
    """Audible/silent tick pattern of each stem against the PSG registers (DC-removed RMS)."""
    snaps, _ = A.decode_ticks(per_tick)
    res = {}
    for c in range(4):
        r = A.tick_rms(A.mono(stem_pcm[c])[0], TS)
        gate = expected_gate(snaps, c)
        if not gate.any():
            res[f'voice{c}'] = dict(expected_audible_ticks=0, measured_audible_ticks=int((r > 1e-3).sum()))
            continue
        meas = r > SILENT_REL * np.median(r[gate])
        res[f'voice{c}'] = dict(expected_audible_ticks=int(gate.sum()), measured_audible_ticks=int(meas.sum()),
                                mismatched_ticks=int((meas != gate).sum()),
                                first_mismatch_ticks=[int(i + 1) for i in np.flatnonzero(meas != gate)[:5]])
    return res


def sfx_length_report(rom, rid, pcm):
    """Registers say how many ticks are audible; the driver says how many it occupies the channel."""
    pt, _ = R.run_scenario(rom, {1: [('req', rid)]}, R.sfx_ticks_until_silent(rom, rid))
    snaps, _ = A.decode_ticks(pt)
    audible = int(expected_gate(snaps, 2).sum())
    x = pcm[:, 0].astype(np.float64)
    last = int(np.flatnonzero(np.abs(x) > 0.01 * np.abs(x).max())[-1])
    return dict(request_id=f'0x{rid:02X}', channel_active_ticks_driver=sfx_active_ticks(rom, rid), audible_ticks_from_registers=audible,
                expected_audible_samples=audible * TS, last_sample_above_1pct_peak=last + 1,
                delta_samples=last + 1 - audible * TS, delta_ms=round((last + 1 - audible * TS) / R.RATE * 1000, 3))


# ------------------------------------------------------------------ 3. independent renderer agreement
def renderer_agreement(per_tick, vgm, renderers, clock=R.PAL):
    n = len(per_tick) * TS
    ref = A.reference_render(per_tick, clock)
    sig = {'reference': ref}
    for name, r in renderers.items():
        sig[name] = A.mono(r.render(vgm, n))[0]
    rms = {k: A.tick_rms(v, TS) for k, v in sig.items()}
    names = list(sig)
    return dict(tick_rms_correlation={f'{a}~{b}': round(A.corr(rms[a], rms[b]), 4) for i, a in enumerate(names) for b in names[i + 1:]},
                rms_vs_reference={k: round(float(np.sqrt((v ** 2).mean()) / max(np.sqrt((ref ** 2).mean()), 1e-9)), 3) for k, v in sig.items()},
                waveform_correlation_with_reference={k: round(A.corr(v[:n], ref[:n]), 4) for k, v in sig.items() if k != 'reference'})


# ------------------------------------------------------------------ 4. noise variant
def noise_decode(x, clock, p2, n_bits, offset_samples=0):
    """Read the LFSR bit stream when noise is clocked by tone 2 (NF=3): one output bit per noise shift."""
    step = 32.0 * p2 * R.RATE / clock
    idx = np.clip(((np.arange(n_bits) + 0.5) * step + offset_samples).astype(int), 0, len(x) - 1)
    return (x[idx] > np.median(x)).astype(np.uint8)


def noise_variant_test(renderers, clock=R.PAL, p2=0x60, n_bits=1200):
    """Which LFSR does each renderer apply: Sega 16-bit (taps 0,3) or TI 15-bit (taps 0,1)?

    The VGM header chooses (feedback pattern and shift width). We render both header variants as a
    negative control: a renderer that ignores the header would score identically for both."""
    n_ticks = int(n_bits * 32.0 * p2 / clock * 60) + 12
    per_tick = [[0xC0 | (p2 & 15), p2 >> 4, 0xDF, 0xE7, 0xF0]] + [[] for _ in range(n_ticks - 1)]
    seqs = {'sega16': A.lfsr_bits(n_bits + 8, A.SEGA), 'ti15': A.lfsr_bits(n_bits + 8, A.TI)}

    def score(bits):
        best = {}
        for name, seq in seqs.items():
            top = 0.0
            for off in range(-3, 4):
                for inv in (0, 1):
                    a = bits[max(off, 0):n_bits + min(off, 0)]
                    b = seq[max(-off, 0):max(-off, 0) + len(a)] ^ inv
                    top = max(top, float((a == b).mean()))
            best[name] = round(top, 3)
        return best

    out = {}
    for label, fb, width in (('vgm_header_sega_0009_w16', 0x0009, 16), ('vgm_header_ti_0003_w15', 0x0003, 15)):
        vgm = bytearray(R.build_vgm(per_tick, clock))
        vgm[0x28:0x2A] = fb.to_bytes(2, 'little')
        vgm[0x2A] = width
        for name, r in renderers.items():
            try:
                out[f'{label}/{name}'] = score(noise_decode(A.mono(r.render(bytes(vgm), len(per_tick) * TS))[0], clock, p2, n_bits))
            except Exception as e:
                out[f'{label}/{name}'] = f'error: {e}'
    out['reference_synth_sega'] = score(noise_decode(A.reference_render(per_tick, clock), clock, p2, n_bits))
    return out


# ------------------------------------------------------------------ 5. determinism
def determinism(rom, renderer_name):
    per_tick, _ = R.run_scenario(rom, {1: [('req', 0x81)]}, 300)
    vgm = R.build_vgm(per_tick)
    r = R.available_renderers()[renderer_name]
    a = R.pcm_sha256(r.render(vgm, 300 * TS))
    b = R.pcm_sha256(r.render(vgm, 300 * TS))
    code = ("import sys;sys.path.insert(0,%r);import audio1b_render as R,audio1_psg_trace as T;"
            "rom=T.load_rom(%r);pt,_=R.run_scenario(rom,{1:[('req',0x81)]},300);v=R.build_vgm(pt);"
            "print(R.pcm_sha256(R.available_renderers()[%r].render(v,300*735)))") % (str(Path(__file__).resolve().parent), str(ROM_PATH[0]), renderer_name)
    sub = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    fresh = sub.stdout.strip()
    again, _ = R.run_scenario(rom, {1: [('req', 0x81)]}, 300)
    return dict(renderer=renderer_name, same_process_twice=a == b, fresh_process=(fresh == a), fresh_process_error=sub.stderr.strip()[-200:] or None,
                vgm_regenerates_identically=R.build_vgm(again) == vgm, vgm_sha256=R.sha256(vgm), pcm_sha256=a)


# ------------------------------------------------------------------ 6. loop continuity
def loop_report(rom, renderer, rid=0x81, lead=1093, period=2688, periods=3, with_stems=True):
    total = lead + period * periods
    per_tick, _ = R.run_scenario(rom, {1: [('req', rid)]}, total)
    pcm = renderer.render(R.build_vgm(per_tick), total * TS)
    x = pcm[:, 0].astype(np.int32)
    a, L = lead * TS, period * TS
    res = dict(renderer=renderer.name, request_id=f'0x{rid:02X}', lead_in_ticks=lead, period_ticks=period, periods_rendered=periods,
               rendered_seconds=round(total / 60, 2), psg_bytes_identical_next_period=per_tick[lead:lead + period] == per_tick[lead + period:lead + 2 * period])
    pairs = []
    for k in range(periods - 1):
        s, t = a + k * L, a + (k + 1) * L
        d = np.abs(x[s:s + L] - x[t:t + L])
        bad_ticks = np.flatnonzero(d.reshape(-1, TS).max(axis=1) > 0)
        pairs.append(dict(periods=f'{k + 1}->{k + 2}', sample_exact=bool(d.max() == 0), differing_sample_fraction=round(float((d > 0).mean()), 4),
                          max_abs_diff=int(d.max()), differing_ticks=int(len(bad_ticks)), of_ticks=period,
                          rms_diff_over_rms_signal=round(float(np.sqrt((d.astype(np.float64) ** 2).mean()) / np.sqrt((x[s:s + L].astype(np.float64) ** 2).mean())), 4)))
    res['period_pairs'] = pairs
    body = x[a + L:a + 2 * L]
    steps = np.abs(np.diff(body))
    res['seam_when_looping_body_2'] = dict(wrap_jump=int(abs(int(body[0]) - int(body[-1]))), ordinary_step_p99_9=round(float(np.percentile(steps, 99.9)), 1),
                                           ordinary_step_max=int(steps.max()),
                                           natural_continuation_jump=int(abs(int(x[a + 2 * L]) - int(body[-1]))) if len(x) > a + 2 * L else None)
    # Seam quality over candidate loop starts: any start >= first recurrence tick is a valid body.
    jumps = np.abs(x[a:a + 200 * TS:TS // 7].astype(np.int64) - x[a + L - 1:a + L - 1 + 200 * TS:TS // 7].astype(np.int64))
    res['seam_scan'] = dict(candidates=int(len(jumps)), median_jump=int(np.median(jumps)), best_jump=int(jumps.min()),
                            fraction_below_p99_9_ordinary_step=round(float((jumps < np.percentile(steps, 99.9)).mean()), 3))
    if with_stems:
        st = stems(renderer, per_tick[:lead + 2 * period], (lead + 2 * period) * TS)
        res['per_channel_period1_vs_2'] = {
            name: dict(sample_exact=bool(np.array_equal(s_[a:a + L, 0], s_[a + L:a + 2 * L, 0])),
                       equal_sample_fraction=round(float((s_[a:a + L, 0] == s_[a + L:a + 2 * L, 0]).mean()), 4))
            for name, s_ in zip(('tone0', 'tone1', 'tone2', 'noise'), st)}
    r1 = A.tick_rms(x[a:a + L].astype(np.float64), TS)
    r2 = A.tick_rms(x[a + L:a + 2 * L].astype(np.float64), TS)
    res['tick_rms_correlation_period1_vs_2'] = round(A.corr(r1, r2), 5)
    return res, per_tick, pcm


# ------------------------------------------------------------------ 7. SFX over music: tone-2 note events, gate, stems
def sfx_active_ticks(rom, sfx):
    d = T.Driver(rom)
    d.request(sfx)
    n = 0
    for t in range(1, 200):
        d.tick()
        if d.mem[0xDF30] & 0x80:
            n = t
    return n


def stream_reads(rom, rid, ticks, channel_addr=0xDEA0):
    """Ticks on which the music stream is read for the given channel (hook at $4341). Every read
    clears the channel's 'suppressed until next read' flag (bit 4), whatever the byte turns out to be."""
    events = []

    def on_read(d):
        if d.cpu.ix == channel_addr:
            events.append(d.update)

    per_tick, _ = R.run_scenario(rom, {1: [('req', rid)]}, ticks, hooks={0x4341: on_read})
    return sorted(set(events)), per_tick


def tone2_write_ticks(per_tick):
    """Ticks containing any write to PSG channel 2 (period or attenuation), with latch tracking."""
    out, latch = [], 0
    for t, writes in enumerate(per_tick):
        hit = False
        for v in writes:
            if v & 0x80:
                latch = v
            if (latch >> 5) & 3 == 2:
                hit = True
        if hit:
            out.append(t + 1)
    return out


def steal_phase_test(rom, music, sfx, request_ticks, after=150):
    """The restore rule, tested against the executed driver at many request phases: after the SFX
    frees the channel at tick `end`, the music channel writes tone 2 again at the first stream read
    after `end`, and not before."""
    k = sfx_active_ticks(rom, sfx)
    rows = []
    for s in request_ticks:
        n = s + k + after
        reads, _ = stream_reads(rom, music, n)
        per_tick, _ = R.run_scenario(rom, {1: [('req', music)], s: [('req', sfx)]}, n)
        end = s + k
        resume = [t for t in tone2_write_ticks(per_tick) if t > end]
        pred = [e for e in reads if e > end]
        rows.append(dict(request_tick=s, driver_first_tone2_write_after_sfx=resume[0] if resume else None,
                         first_stream_read_after_sfx=pred[0] if pred else None,
                         match=bool(resume and pred and resume[0] == pred[0]),
                         silent_ticks_after_sfx=(resume[0] - end) if resume else None))
    return dict(music=f'0x{music:02X}', sfx=f'0x{sfx:02X}', sfx_channel_active_ticks=k, phases=len(rows),
                matches=sum(r['match'] for r in rows), max_silent_ticks_after_sfx=max(r['silent_ticks_after_sfx'] for r in rows),
                mismatches=[r for r in rows if not r['match']])


def steal_audio_test(rom, renderer, music, sfx, s, tail=150):
    """SFX interruption: ground truth (the executed driver's combined PSG log, rendered) versus a
    stems + gate + one-shot reconstruction. Compared on the tone-2 channel only, where the
    interruption happens, plus a check that the other three channels are untouched.

    Oscillator PHASE is not comparable (the SFX one-shot starts a fresh oscillator while the real
    chip continues the music's), so envelope and pitch are compared, not samples."""
    k = sfx_active_ticks(rom, sfx)
    n = s + k + tail
    gt_ticks, _ = R.run_scenario(rom, {1: [('req', music)], s: [('req', sfx)]}, n)
    gt_stems = [A.mono(p)[0] for p in stems(renderer, gt_ticks, n * TS)]
    reads, solo_ticks = stream_reads(rom, music, n)
    solo = [A.mono(p)[0] for p in stems(renderer, solo_ticks, n * TS)]
    end = s + k
    resume = min([e for e in reads if e > end] or [n + 1])
    gate = np.ones(n * TS)
    gate[(s - 1) * TS:(resume - 1) * TS] = 0.0
    sfx_ticks, _ = R.run_scenario(rom, {1: [('req', sfx)]}, k + 1)
    sfx_wave = A.mono(renderer.render(R.build_vgm(sfx_ticks), (k + 1) * TS))[0]
    off = (s - 1) * TS
    gated = solo[2] * gate
    gated[off:off + len(sfx_wave)] += sfx_wave
    naive = solo[2].copy()
    naive[off:off + len(sfx_wave)] += sfx_wave
    gt2 = gt_stems[2]
    r_gt, r_g, r_n = (A.tick_rms(v, TS) for v in (gt2, gated, naive))
    w = slice(s - 1, resume + 3)
    scale = float(r_gt.max())

    def pitch_agree(x):
        ok = tot = 0
        for t in range(s - 1, resume + 3):
            a, b = x[t * TS:(t + 1) * TS], gt2[t * TS:(t + 1) * TS]
            if np.sqrt((b ** 2).mean()) < 0.01 * scale:
                tot += 1
                ok += int(np.sqrt((a ** 2).mean()) < 0.02 * scale)
                continue
            fa, fb = A.estimate_hz(a, fmin=100, fmax=4000), A.estimate_hz(b, fmin=100, fmax=4000)
            tot += 1
            ok += int(bool(fa and fb and fa > 0 and fb > 0 and abs(1200 * np.log2(float(fa) / float(fb))) < 25))
        return round(ok / max(tot, 1), 3)

    others = max(float(np.abs(gt_stems[c] - solo[c]).max()) for c in (0, 1, 3))
    return dict(music=f'0x{music:02X}', sfx=f'0x{sfx:02X}', request_tick=s, sfx_active_ticks=k, tone2_resume_tick=int(resume),
                tone2_silenced_ticks=int(resume - s),
                other_channels_max_abs_diff_lsb=round(others * 32768, 1),
                tone2_envelope_correlation_gate=round(A.corr(r_gt[w], r_g[w]), 4),
                tone2_envelope_correlation_naive_mix=round(A.corr(r_gt[w], r_n[w]), 4),
                tone2_envelope_max_err_gate_pct_of_peak=round(100 * float(np.abs(r_gt[w] - r_g[w]).max() / scale), 2),
                tone2_envelope_max_err_naive_pct_of_peak=round(100 * float(np.abs(r_gt[w] - r_n[w]).max() / scale), 2),
                tone2_pitch_agreement_gate=pitch_agree(gated), tone2_pitch_agreement_naive_mix=pitch_agree(naive),
                tone2_ticks_after_resume_envelope_correlation=round(A.corr(r_gt[resume + 3:], r_g[resume + 3:]), 4))


# ------------------------------------------------------------------ 8. opening
def opening_harness_timeline(rom):
    """Original opening in the repo's approximate frame harness (PAL-like cadence, D12D = 0):
    request / scene end / music fade / title, in main-loop updates and driver ticks since the
    $90 request, for the natural run and for a skip (Button 1) at several updates."""
    sys.path.insert(0, str(R.ROOT / 'tools'))
    import sms_frame_harness as H

    def run(press_wait):
        m = H.SMS(rom)
        st = dict(ticks=0, waits=0)
        ev = []

        def drv(mm):
            if mm.slot[1] == 2:
                st['ticks'] += 1

        def wait(mm):
            st['waits'] += 1
            if press_wait is not None and st['waits'] == press_wait:
                mm.pad = H.BTN_1
            if press_wait is not None and st['waits'] == press_wait + 6:
                mm.pad = 0

        def mk(name):
            return lambda mm: ev.append((name, st['waits'], st['ticks']))

        m.add_pc_hook(0x4000, drv)
        m.add_pc_hook(0x062D, wait)
        for name, addr in (('request_189B', 0x06EF), ('scene_end_fade_1CAF', 0x1CAF), ('music_fade_18E1', 0x18E1), ('title_0719', 0x0719)):
            m.add_pc_hook(addr, mk(name))
        for _ in range(1300):
            m.run_frame()
        base = next(e for e in ev if e[0] == 'request_189B')
        out = {}
        for name, w, t in ev:
            if name not in out:
                out[name] = dict(updates_since_request=w - base[1], driver_ticks_since_request=t - base[2])
        return out

    res = {'natural': run(None)}
    for u in (70, 300, 600):
        res[f'skip_pressed_at_update_{u}'] = run(30 + u)
    return dict(evidence='EMULATED ORIGINAL FRAMES (approximate harness, PAL-like cadence 1.2 ticks/update; not hardware)', scenarios=res)


def opening_render(rom, renderer, scene_end_updates=738, wait=30, cadence=1.0):
    """Render $90 with the game-side fade ($18E1 -> DE09/DE0A/DE0B = 12/1/2) placed
    (scene_end + wait) updates after the request, converted to driver ticks by `cadence`."""
    fade_before_tick = int(round((scene_end_updates + wait) * cadence)) + 1
    d = T.Driver(rom)
    d.request(0x90)
    inactive = None
    per_tick = []
    for t in range(1, fade_before_tick + 80):
        if t == fade_before_tick:
            d.mem[0xDE09], d.mem[0xDE0A], d.mem[0xDE0B] = 12, 1, 2
        w0 = len(d.writes)
        d.tick()
        per_tick.append([b for _, b in d.writes[w0:]])
        if not d.music_active():
            inactive = t
            break
    n = inactive
    pcm = renderer.render(R.build_vgm(per_tick[:n]), n * TS)
    return dict(scene_end_updates=scene_end_updates, wait_updates=wait, cadence_ticks_per_update=cadence, fade_written_before_tick=fade_before_tick,
                music_inactive_at_tick=inactive, fade_ticks=inactive - fade_before_tick + 1, rendered_ticks=n, seconds=round(n / 60, 3),
                pcm_sha256=R.pcm_sha256(pcm)), pcm


# ------------------------------------------------------------------ 9. independent Z80: GME runs the original driver itself
def kss_crosscheck(rom, gme, rid, ticks):
    """GME's own Z80 core (Kss_Cpu) executes the unmodified sound bank; its per-voice audio is
    compared with the register values produced by the repo harness (kosarev/z80). GME fixes the
    KSS PSG clock at NTSC 3,579,545 Hz, so expected pitch uses that clock. The first play call
    occurs one frame after init, hence the 735-sample alignment."""
    kss = R.kss_bytes(rom, rid)
    pt, _ = R.run_scenario(rom, {1: [('req', rid)]}, ticks)
    st = [gme.render(kss, (ticks + 1) * TS, eq='flat', mute_mask=0xF ^ (1 << v))[TS:] for v in range(4)]
    clock = T.PSG_CLOCK['NTSC']
    w = pitch_windows(pt, st, clock=clock, min_ticks=3 if rid < 0xA0 else 1)
    cents = np.array([abs(o[5]) for o in w])
    bad = [o for o in w if abs(o[5]) > 25]
    gate_mismatch = {}
    snaps, _ = A.decode_ticks(pt)
    for c in range(3):
        r = A.tick_rms(A.mono(st[c])[0], TS)
        g = expected_gate(snaps, c)
        if g.any():
            meas = r > SILENT_REL * np.median(r[g])
            gate_mismatch[f'tone{c}'] = int((meas != g).sum())
    return dict(request_id=f'0x{rid:02X}', ticks=ticks, windows=len(w), median_abs_cents=round(float(np.median(cents)), 3) if len(cents) else None,
                p95_abs_cents=round(float(np.percentile(cents, 95)), 3) if len(cents) else None,
                windows_off_by_more_than_25_cents=len(bad), off_per_channel={c: sum(1 for o in bad if o[0] == c) for c in range(3)},
                audible_tick_pattern_mismatches=gate_mismatch)


# ------------------------------------------------------------------ everything
def run_all(rom, out_dir, renderers):
    ROM_PATH[0] = ROM_PATH[0] or R.ROOT / 'roms/SonicChaos.sms'
    primary = renderers[R.PRIMARY]
    res = dict(rom_sha256=T.ROM_SHA256, primary_renderer=R.PRIMARY, renderers=list(renderers), psg_clock_hz=R.PAL, sample_rate=R.RATE,
               ticks_per_second=60, samples_per_tick=TS, export_roundtrip={}, per_sample={})
    for stem, rid, kind, ticks in R.SAMPLES:
        n = ticks or R.sfx_ticks_until_silent(rom, rid)
        pt, _ = R.run_scenario(rom, {1: [('req', rid)]}, n)
        vgm = R.build_vgm(pt)
        res['export_roundtrip'][stem] = R.vgm_matches(pt, vgm) or 'ok'
        row = {}
        for name, r in renderers.items():
            pcm = r.render(vgm, n * TS)
            st = stems(r, pt, n * TS)
            mix_sum = sum(s.astype(np.int64) for s in st)
            row[name] = dict(sanity=sanity(pcm), pitch=pitch_report(pt, st), durations=duration_report(pt, st),
                             stems_sum_vs_mix_max_abs_diff=int(np.abs(mix_sum - pcm.astype(np.int64)).max()))
            if kind == 'sfx':
                row[name]['length'] = sfx_length_report(rom, rid, pcm)
                row[name]['pitch_tick_level'] = pitch_report(pt, st, min_ticks=1)
        row['agreement'] = renderer_agreement(pt, vgm, renderers)
        res['per_sample'][stem] = row
    if 'gme_flat' in renderers:
        g = renderers['gme_flat'].gme
        res['independent_z80_kss'] = {f'{rid:02X}': kss_crosscheck(rom, g, rid, n if n else R.sfx_ticks_until_silent(rom, rid))
                                      for _, rid, _, n in R.SAMPLES}
    res['noise_variant'] = noise_variant_test(renderers)
    res['determinism'] = {name: determinism(rom, name) for name in renderers}
    res['loop_81'] = {name: loop_report(rom, renderers[name])[0] for name in (R.PRIMARY, 'gme_flat') if name in renderers}
    res['steal_driver_rule'] = {f'{m:02X}/{s:02X}': steal_phase_test(rom, m, s, range(150, 700, 23))
                                for m, s in ((0x81, 0xBF), (0x81, 0xA6), (0x82, 0xBF), (0x82, 0xA6), (0x90, 0xBF))}
    res['steal_audio'] = [steal_audio_test(rom, primary, 0x81, sfx, s) for sfx in (0xBF, 0xA6) for s in (200, 331, 702)]
    res['opening_harness'] = opening_harness_timeline(rom)
    op = {}
    for label, args in (('natural_nominal_60hz_adapter', dict()), ('natural_pal_cadence_original', dict(cadence=1.2)),
                        ('skip_at_update_300', dict(scene_end_updates=300))):
        info, pcm = opening_render(rom, primary, **args)
        R.write_wav(Path(out_dir) / primary.name / f'opening_{label}.wav', pcm)
        op[label] = info
    res['opening_render'] = op
    return res

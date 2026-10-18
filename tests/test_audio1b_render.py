"""AUDIO-1B regressions.

ROM-free tests always run. Tests needing the verified local ROM and the locally built renderers
(AUDIO1B_VGM2WAV for libvgm, AUDIO1B_GME_LIB for Game_Music_Emu) are skipped when either is missing.
No generated audio is ever written to the repository.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import audio1_psg_trace as T
import audio1b_analyze as A
import audio1b_checks as C
import audio1b_render as R

SUMMARY = ROOT / 'data/audio1b/render-validation-summary.json'


def local_rom():
    for cand in (os.environ.get('SONIC_CHAOS_ROM'), str(ROOT / 'roms/SonicChaos.sms')):
        if cand and Path(cand).exists():
            data = Path(cand).read_bytes()
            if hashlib.sha256(data).hexdigest() == T.ROM_SHA256:
                C.ROM_PATH[0] = Path(cand)
                return data
    return None


ROM = local_rom()
RENDERERS = R.available_renderers() if ROM is not None else {}
HAVE_MAME = R.PRIMARY in RENDERERS
HAVE_GME = 'gme_flat' in RENDERERS


class RomFree(unittest.TestCase):
    def test_vgm_roundtrip_and_header(self):
        per_tick = [[0x9F, 0xBF, 0xDF, 0xFF], [0xC5, 0x05, 0xD1], [], [0xDF]]
        vgm = R.build_vgm(per_tick)
        self.assertEqual(R.vgm_matches(per_tick, vgm), [])
        h, events, total = R.parse_vgm(vgm)
        self.assertEqual((h['version'], h['sn_clock'], h['feedback'], h['width']), (0x150, 3546893, 0x0009, 16))
        self.assertEqual(total, 4 * 735)
        self.assertEqual(events[4], (735, 0xC5))

    def test_vgm_check_detects_tampering(self):
        per_tick = [[0xC5, 0x05, 0xD1], [0xD2]]
        bad = bytearray(R.build_vgm(per_tick))
        bad[0x28] = 0x03                                   # TI feedback pattern
        self.assertIn('header fields differ', R.vgm_matches(per_tick, bytes(bad)))
        other = R.build_vgm([[0xC5, 0x05, 0xD1], [0xD3]])
        self.assertIn('event list differs', R.vgm_matches(per_tick, other))

    def test_attenuation_stem_forces_other_channels_silent_and_keeps_schedule(self):
        per_tick = [[0x80 | 3, 0x10, 0x91], [0xA2, 0x0E, 0xB2, 0xD5, 0xF3], [0x93, 0xBF]]
        stem1 = R.attenuation_stem(per_tick, 1)
        flat = [b for t in stem1 for b in t]
        self.assertIn(0xB2, flat)                          # kept channel's attenuation untouched
        self.assertNotIn(0x91, flat)                       # tone 0 attenuation forced to 15
        self.assertEqual([len(t) for t in stem1][1:], [len(t) for t in per_tick][1:])   # same write schedule
        self.assertTrue(all((b & 0xF) == 0xF for b in flat if (b & 0x90) == 0x90 and ((b >> 5) & 3) != 1))

    def test_reference_synth_pitch_attenuation_and_noise_sequences(self):
        clock = R.PAL
        per_tick = [[0x80 | (254 & 15), 254 >> 4, 0x90]] + [[] for _ in range(29)]
        x = A.reference_render(per_tick, clock)
        f = A.estimate_hz(x[735 * 5:735 * 25])
        self.assertAlmostEqual(1200 * np.log2(f / (clock / (32 * 254))), 0, delta=1.0)
        per2 = per_tick[:1] + [[] for _ in range(9)] + [[0x95]] + [[] for _ in range(9)]
        r = A.tick_rms(A.reference_render(per2, clock))
        self.assertAlmostEqual(r[15] / r[5], 10 ** (-10 / 20), delta=0.01)
        sega, ti = A.lfsr_bits(40, A.SEGA), A.lfsr_bits(40, A.TI)
        self.assertEqual(int(np.flatnonzero(sega)[0]), 15)       # 16-bit register: first 1 after 15 zeros
        self.assertEqual(int(np.flatnonzero(ti)[0]), 14)         # 15-bit register: after 14 zeros
        self.assertFalse(np.array_equal(sega, ti))

    def test_wav_is_deterministic_and_lossless(self):
        pcm = (np.arange(2000).reshape(-1, 2) % 2000 - 1000).astype('<i2')
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a.wav', Path(tmp) / 'b.wav'
            R.write_wav(a, pcm)
            R.write_wav(b, pcm)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertTrue(np.array_equal(R.read_wav(a), pcm))

    def test_kss_wrapper_layout(self):
        fake = bytes(range(256)) * 2048                    # 512 KB stand-in, not ROM data
        k = R.kss_bytes(fake, 0x82)
        self.assertEqual(k[:4], b'KSCC')
        self.assertEqual(k[0x10:0x10 + 0x8000], fake[0x8000:0x10000])
        self.assertEqual(int.from_bytes(k[6:8], 'little'), 0x8000 + 11 + 4)
        self.assertIn(bytes([0x3E, 0x82, 0x32, 0x04, 0xDE]), k)

    def test_renderer_pins_match_build_script(self):
        script = (ROOT / 'tools/audio1b_build_renderers.sh').read_text()
        self.assertIn(R.PINS['game_music_emu']['commit'], script)
        self.assertIn(R.PINS['libvgm']['commit'], script)

    def test_summary_is_metadata_only_and_consistent(self):
        text = SUMMARY.read_text()
        s = json.loads(text)
        self.assertEqual(s['rom_sha256'], T.ROM_SHA256)
        self.assertEqual(s['psg_clock_hz'], 3546893)
        self.assertNotIn('/home/', text)
        self.assertNotIn('/tmp/', text)
        self.assertTrue(all(v == 'ok' for v in s['export_roundtrip'].values()))
        op = s['opening_render']['natural_nominal_60hz_adapter']
        self.assertEqual((op['fade_written_before_tick'], op['fade_ticks']), (769, 23))

    def test_no_generated_audio_or_rom_is_tracked(self):
        try:
            files = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split('\n')
        except (OSError, subprocess.CalledProcessError):
            self.skipTest('not a git checkout')
        bad = [f for f in files if re.search(r'\.(sms|gg|vgm|vgz|wav|ogg|mp3|flac|kss)$', f, re.I)]
        self.assertEqual(bad, [])


@unittest.skipUnless(ROM is not None and HAVE_MAME, 'needs verified local ROM and AUDIO1B_VGM2WAV')
class WithMameRenderer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = RENDERERS[R.PRIMARY]

    def render(self, rid, ticks=None):
        n = ticks or R.sfx_ticks_until_silent(ROM, rid)
        pt, _ = R.run_scenario(ROM, {1: [('req', rid)]}, n)
        vgm = R.build_vgm(pt)
        return pt, vgm, self.r.render(vgm, n * R.TICK_SAMPLES)

    def test_samples_are_audible_unclipped_and_pitch_exact(self):
        for rid in (0x90, 0x82, 0x81):
            pt, vgm, pcm = self.render(rid, 900)
            s = C.sanity(pcm)
            self.assertTrue(s['non_silent'])
            self.assertEqual(s['clipped_frames'], 0)
            self.assertGreater(s['headroom_db'], 1.0)
            self.assertEqual(s['leading_silent_frames'], 0)
            st = C.stems(self.r, pt, 900 * R.TICK_SAMPLES)
            p = C.pitch_report(pt, st)
            self.assertGreater(p['windows'], 50)
            self.assertEqual(p['windows_off_by_more_than_25_cents'], 0, f'${rid:02X}')
            self.assertLess(p['max_abs_cents'], 10.0)
            self.assertLessEqual(int(np.abs(sum(x.astype(np.int64) for x in st) - pcm.astype(np.int64)).max()), 16)

    def test_sfx_lengths_are_sample_exact(self):
        for rid, active, audible in ((0xBF, 20, 20), (0xA6, 40, 36)):
            _, _, pcm = self.render(rid)
            rep = C.sfx_length_report(ROM, rid, pcm)
            self.assertEqual(rep['channel_active_ticks_driver'], active)
            self.assertEqual(rep['audible_ticks_from_registers'], audible)
            self.assertLessEqual(abs(rep['delta_samples']), 2)

    def test_render_is_deterministic(self):
        d = C.determinism(ROM, R.PRIMARY)
        self.assertTrue(d['same_process_twice'] and d['fresh_process'] and d['vgm_regenerates_identically'])

    def test_noise_follows_vgm_header_and_sega_variant_matches(self):
        res = C.noise_variant_test({R.PRIMARY: self.r})
        self.assertGreaterEqual(res['vgm_header_sega_0009_w16/libvgm_mame']['sega16'], 0.99)
        self.assertLess(res['vgm_header_sega_0009_w16/libvgm_mame']['ti15'], 0.7)
        self.assertGreaterEqual(res['vgm_header_ti_0003_w15/libvgm_mame']['ti15'], 0.99)
        self.assertGreaterEqual(res['reference_synth_sega']['sega16'], 0.99)

    def test_steal_restore_rule_matches_driver_at_many_phases(self):
        for music, sfx in ((0x81, 0xBF), (0x81, 0xA6), (0x82, 0xBF)):
            r = C.steal_phase_test(ROM, music, sfx, range(150, 400, 37))
            self.assertEqual(r['matches'], r['phases'], r['mismatches'])

    def test_gated_stems_reproduce_interrupted_tone2_where_naive_mix_does_not(self):
        r = C.steal_audio_test(ROM, self.r, 0x81, 0xA6, 331)
        self.assertEqual(r['other_channels_max_abs_diff_lsb'], 0.0)
        self.assertGreater(r['tone2_envelope_correlation_gate'], 0.999)
        self.assertLess(r['tone2_envelope_max_err_gate_pct_of_peak'], 1.0)
        self.assertGreater(r['tone2_envelope_max_err_naive_pct_of_peak'], 20.0)

    def test_pcm_loop_is_not_sample_continuous_even_though_psg_loops_exactly(self):
        res, _, _ = C.loop_report(ROM, self.r, periods=2, with_stems=False)
        self.assertTrue(res['psg_bytes_identical_next_period'])
        self.assertFalse(res['period_pairs'][0]['sample_exact'])

    def test_opening_fade_timing_for_nominal_pal_and_skip(self):
        for kwargs, fade_before in (({}, 769), ({'cadence': 1.2}, 923), ({'scene_end_updates': 300}, 331)):
            info, pcm = C.opening_render(ROM, self.r, **kwargs)
            self.assertEqual(info['fade_written_before_tick'], fade_before)
            self.assertEqual(info['fade_ticks'], 23)
            self.assertEqual(len(pcm), info['rendered_ticks'] * R.TICK_SAMPLES)


@unittest.skipUnless(ROM is not None and HAVE_GME, 'needs verified local ROM and AUDIO1B_GME_LIB')
class WithGme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = RENDERERS['gme_flat'].gme

    def test_voice_mute_must_precede_start_track(self):
        pt, _ = R.run_scenario(ROM, {1: [('req', 0xBF)]}, 21)
        vgm = R.build_vgm(pt)
        n = 21 * R.TICK_SAMPLES
        muted = self.g.render(vgm, n, eq='flat', mute_mask=0xF)
        self.assertEqual(int(np.abs(muted).max()), 0)

    def test_independent_z80_reproduces_register_pitch_on_82_and_81(self):
        for rid in (0x82, 0x81):
            r = C.kss_crosscheck(ROM, self.g, rid, 900)
            self.assertEqual(r['windows_off_by_more_than_25_cents'], 0)
            self.assertLess(r['p95_abs_cents'], 5.0)

    def test_gme_known_pitch_defect_on_90_is_documented(self):
        """Marker: GME 0.6.5 plays wrong tone-2/tone-0 pitch on $90 (also via its own Z80). If this
        starts failing, GME was fixed or changed: re-run the validation and update the report."""
        pt, _ = R.run_scenario(ROM, {1: [('req', 0x90)]}, 900)
        st = C.stems(RENDERERS['gme_flat'], pt, 900 * R.TICK_SAMPLES)
        self.assertGreater(C.pitch_report(pt, st)['windows_off_by_more_than_25_cents'], 20)


if __name__ == '__main__':
    unittest.main()

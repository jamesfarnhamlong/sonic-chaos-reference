"""AUDIO-1 feasibility regressions.

ROM-free tests always run. Tests that execute the original driver need the verified
local ROM (SONIC_CHAOS_ROM, or ignored roms/SonicChaos.sms) and are skipped otherwise.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import audio1_psg_trace as T

PLAN = ROOT / 'data/audio1/pilot-plan.json'
LEDGER = ROOT / 'data/rom-cache/audio/request-ledger.json'
EVIDENCE = {'verified', 'source-traced', 'proposed', 'unresolved'}


def local_rom():
    for cand in (os.environ.get('SONIC_CHAOS_ROM'), str(ROOT / 'roms/SonicChaos.sms')):
        if cand and Path(cand).exists():
            data = Path(cand).read_bytes()
            if hashlib.sha256(data).hexdigest() == T.ROM_SHA256:
                return data
    return None


class RomFree(unittest.TestCase):
    def test_psg_latch_and_data_protocol(self):
        p = T.Psg()
        p.write(0x80 | 0x0A)       # tone0 low nibble
        p.write(0x15)              # data byte: high 6 bits
        self.assertEqual(p.tone[0], (0x15 << 4) | 0x0A)
        p.write(0xBF)              # tone1 attenuation 15
        p.write(0xDF)
        p.write(0xE4)              # noise: white, rate 0
        p.write(0xF3)              # noise attenuation 3
        self.assertEqual((p.att[1], p.att[2], p.noise, p.att[3]), (15, 15, 4, 3))
        p.write(0xC1)              # tone2 low nibble, then a data byte keeps latch on tone2
        p.write(0x02)
        self.assertEqual(p.tone[2], 0x021)

    def test_attenuation_latch_then_data_byte(self):
        p = T.Psg()
        p.write(0x90)              # tone0 attenuation latch
        p.write(0x03)              # data byte updates attenuation, not tone
        self.assertEqual((p.att[0], p.tone[0]), (3, 0))

    def test_vgm_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'x.vgm'
            n = T.write_vgm(out, [(1, 0x9F), (2, 0xBF)], 3, T.PSG_CLOCK['PAL'])
            data = out.read_bytes()
        self.assertEqual(len(data), n)
        self.assertEqual(data[:4], b'Vgm ')
        self.assertEqual(int.from_bytes(data[4:8], 'little'), len(data) - 4)
        self.assertEqual(int.from_bytes(data[0x0C:0x10], 'little'), 3546893)
        self.assertEqual(int.from_bytes(data[0x18:0x1C], 'little'), 3 * 735)
        self.assertEqual(data[0x2A], 16)
        self.assertEqual(data[-1], 0x66)

    def test_plan_matches_audio0_ledger(self):
        plan = json.loads(PLAN.read_text())
        ledger = {e['request_id']: e for e in json.loads(LEDGER.read_text())['requests']}
        self.assertEqual(plan['rom_sha256'], T.ROM_SHA256)
        self.assertEqual([r['request_id'] for r in plan['pilot']], [0x90, 0x82, 0x81, 0xBF, 0xA6])
        for r in plan['pilot']:
            e = ledger[r['request_id']]
            self.assertEqual(r['category'], e['category'])
            self.assertEqual(r['header_rom'], e['sound_pointer']['target_rom'])
            self.assertEqual(r['priority_byte'], e['arbitration_priority_byte'])
            for claim in r['claims']:
                self.assertIn(claim['evidence'], EVIDENCE)
            self.assertTrue(r['unresolved'])

    def test_plan_distinguishes_driver_from_adapter(self):
        plan = json.loads(PLAN.read_text())
        self.assertIn('original_driver_behaviour', plan['layers'])
        self.assertIn('documented_adapter_decisions', plan['layers'])
        self.assertEqual(plan['driver_tick']['nominal_hz'], 60)

    def test_committed_summary_agrees_with_plan(self):
        summary = json.loads(T.MANIFEST.read_text())
        plan = {r['request_id']: r for r in json.loads(PLAN.read_text())['pilot']}
        self.assertEqual(summary['rom_sha256'], T.ROM_SHA256)
        for r in summary['requests']:
            rid = int(r['request_id'], 16)
            self.assertEqual(r['header']['header_rom'], plan[rid]['header_rom'])
            if rid < 0xA0:
                self.assertTrue(r['exact_driver_state_recurrence']['next_period_psg_writes_identical'])

    def test_no_rom_or_rendered_audio_is_tracked(self):
        try:
            files = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split('\n')
        except (OSError, subprocess.CalledProcessError):
            self.skipTest('not a git checkout')
        bad = [f for f in files if f.lower().endswith(('.sms', '.gg', '.vgm', '.vgz', '.wav', '.ogg', '.mp3', '.flac'))]
        self.assertEqual(bad, [])


@unittest.skipIf(local_rom() is None, 'verified local ROM not available')
class WithRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = local_rom()

    def test_committed_pilot_summary_regenerates(self):
        committed = json.loads(T.MANIFEST.read_text())
        regenerated = [T.summarize(self.rom, r) for r in T.PILOT]
        self.assertEqual(committed['requests'], regenerated)

    def test_zero_is_not_silence_and_f8_is_silence(self):
        d = T.Driver(self.rom)
        d.request(0x81)
        for _ in range(300):
            d.tick()
        d.request(0x00)
        d.tick()
        self.assertTrue(d.music_active())
        d.request(0xF8)
        w0 = len(d.writes)
        d.tick()
        self.assertFalse(d.music_active())
        self.assertEqual([b for _, b in d.writes[w0:]][-4:], [0x9F, 0xBF, 0xDF, 0xFF])

    def test_ring_steals_tone2_and_music_recovers_at_next_note(self):
        s = T.steal_facts(self.rom, 0x81, 0xBF)
        self.assertEqual(s['stolen_music_channel_indices'], [2])
        self.assertGreater(s['steal_flag_cleared_update'], s['first_steal_flag_update'])
        # while stolen, no tone-2 latch ($C0..$CF) from the music stream is emitted after SFX end
        d = T.Driver(self.rom)
        d.request(0x81)
        for _ in range(219):
            d.tick()
        self.assertTrue(d.mem[0xDEA0] & 0x80 and not d.mem[0xDEA0] & 4)

    def test_pilot_sfx_lengths(self):
        self.assertEqual(T.sfx_facts(self.rom, 0xBF)['last_active_update'], 20)
        self.assertEqual(T.sfx_facts(self.rom, 0xA6)['last_active_update'], 40)

    def test_priority_rule_equal_accepted_lower_dropped(self):
        d = T.Driver(self.rom)
        d.mem[0xDE0F] = 0x38
        d.request(0xA6)
        d.call(0x407F)
        self.assertEqual(d.mem[0xDE03] & 0x7F, 0x26)       # equal priority accepted
        d = T.Driver(self.rom)
        d.mem[0xDE0F] = 0x39
        d.request(0xA6)
        d.call(0x407F)
        self.assertEqual(d.mem[0xDE03], 0x80)              # lower priority dropped (idle baseline)

    def test_game_gameplay_fade_takes_23_updates(self):
        d = T.Driver(self.rom)
        d.request(0x81)
        for _ in range(300):
            d.tick()
        d.mem[0xDE09], d.mem[0xDE0A], d.mem[0xDE0B] = 12, 1, 2
        n = 0
        while d.music_active():
            d.tick()
            n += 1
        self.assertEqual(n, 23)

    def test_isolated_driver_matches_game_irq_path(self):
        r = T.insitu_compare(self.rom)
        ids = [q['id'] for q in r['requests_replayed']]
        for needed in ('0x90', '0x81', '0xBF', '0xA6'):
            self.assertIn(needed, ids)
        self.assertEqual(r['stopped_because'], 'span end')
        self.assertGreaterEqual(r['consecutive_identical_ticks'], 4500)
        self.assertEqual(r['driver_entries_per_60_frames'], 72)


if __name__ == '__main__':
    unittest.main()

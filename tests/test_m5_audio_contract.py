"""M5 numeric evidence and focused original-ROM regressions; no audio rendering."""
import json
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import audio1_psg_trace as T
import m5_audio_contract as M

def read(name):return json.loads((ROOT/'data/m5'/name).read_text(encoding='utf-8'))

class ExistingEvidence(unittest.TestCase):
    def test_complete_ids_and_classification(self):
        rows=read('catalogue.json')['entries']
        self.assertEqual([r['request_id'] for r in rows],[0]+list(range(0x81,0xC5))+[0xF8])
        self.assertEqual([sum(r['category']==k for r in rows) for k in ('music','sfx','control')],[31,37,2])
        self.assertTrue(all(r['execution']['lifecycle']!='unresolved' for r in rows))

    def test_recurrences_are_not_finite_silence(self):
        rows=read('catalogue.json')['entries']
        looping=[r for r in rows if r['execution']['lifecycle']=='repeating']
        self.assertEqual(len(looping),11)
        for r in looping:
            rec=r['execution']['recurrence']
            self.assertGreater(rec['writes_per_period'],0)
            self.assertTrue(rec['subsequent_period_writes_identical'])
        title=next(r for r in rows if r['request_id']==0x99)
        self.assertEqual(title['execution']['finite_inactive_tick'],1189)
        self.assertEqual(title['call_sites'][-1]['rom_offset'],0x756)

    def test_duplicate_output_preserves_request_priorities(self):
        rows={r['request_id']:r for r in read('catalogue.json')['entries']}
        for a,b in ((0xA8,0xC2),(0xBB,0xC4),(0xBC,0xC0)):
            self.assertEqual(rows[a]['execution']['classified_prefix_write_sha256'],rows[b]['execution']['classified_prefix_write_sha256'])
            self.assertNotEqual(rows[a]['priority']['table_byte'],rows[b]['priority']['table_byte'])
            self.assertNotEqual(rows[a]['driver_header']['header_rom'],rows[b]['driver_header']['header_rom'])

    def test_empty_rows_are_not_playable(self):
        for r in read('catalogue.json')['entries']:
            if 0x9B<=r['request_id']<=0x9F:
                self.assertEqual(r['execution']['finite_inactive_tick'],1)
                self.assertIn('unavailable',r['sound_test_disposition'])

    def test_pair_coverage_and_global_priority_clear(self):
        d=read('interactions.json')
        self.assertEqual(d['arbitration_assertions'],4864)
        self.assertEqual(len(d['scenarios']),1480)
        e=d['scenarios']['BF-A3']['transitions']
        x=next(r for r in e if r['tick']==50)
        self.assertEqual(x['priority'],0)
        self.assertFalse(x['flags'][5]&128)
        self.assertTrue(x['flags'][6]&128)
        x=next(r for r in d['scenarios']['AC-A0']['transitions'] if r['tick']==35)
        self.assertTrue(all(f&128 for f in x['flags'][4:]))

    def test_recovery_and_fade_scope(self):
        d=read('extensions.json')
        self.assertEqual(len(d['recovery']),111)
        for row in d['recovery']:
            for ch in row['channels']:
                if ch['release_tick']:self.assertTrue(ch['recovery_matches_reader'])
            self.assertNotIn('eligible_reads_after_request',row)
        fade={r['tick']:r for r in d['controls']['fade']}
        self.assertTrue(any(f&128 for f in fade[34]['flags'][4:]))
        self.assertFalse(any(f&128 for f in fade[35]['flags'][4:]))
        self.assertEqual(fade[57]['flags'],[0]*7)

    def test_production_storage_derived(self):
        d=read('production-estimate.json')
        self.assertEqual(d['music_four_stems_bytes'],186645*735*2*4)
        self.assertEqual(d['mono_chunk_bytes'],6021120)
        self.assertFalse(d['loop_cuts_selected_for_new_tracks'])

@unittest.skipUnless(os.environ.get('SONIC_CHAOS_ROM'),'requires authenticated private ROM')
class OriginalDriver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rom=T.load_rom(os.environ['SONIC_CHAOS_ROM'])

    def test_all_header_priorities_and_initial_flags(self):
        for row in read('catalogue.json')['entries']:
            rid=row['request_id']
            if not 0x81<=rid<=0xC4:continue
            h=T.header_facts(self.rom,rid)
            if rid>=0xA0:
                for i,s in enumerate(h['streams']):s['initial_flags']=self.rom[h['header_rom']+4+6*i]
            self.assertEqual(h,row['driver_header'])

    def test_empty_streams_terminate_immediately(self):
        for rid in range(0x9B,0xA0):
            h=T.header_facts(self.rom,rid)
            self.assertTrue(all(self.rom[s['stream_cpu']+0x4000]==0xF2 for s in h['channels']))
            d=T.Driver(self.rom);d.request(rid);d.tick()
            self.assertFalse(d.music_active())
            # Preserve the unusual register residue; never assert analogue silence.
            self.assertEqual(d.psg.tone[2],0)
            self.assertEqual(d.psg.att[2],0)

    def test_f8_is_priority_arbitrated(self):
        self.assertEqual(T.priority_byte(self.rom,0xF8),0x57)
        for current,expected in ((0,True),(0x57,True),(0x58,False),(0x78,False)):
            d=T.Driver(self.rom);d.mem[0xDE0F]=current;d.request(0xF8);d.call(0x407F)
            self.assertEqual(d.mem[0xDE03]==0xF8,expected)
        a=M.timeline(self.rom,{30:[0xA0],35:[0xF8]},40)
        self.assertIn('DF30',a['final_active'])

    def test_equal_output_pairs_reproduce(self):
        for a,b in ((0xA8,0xC2),(0xBB,0xC4),(0xBC,0xC0)):
            self.assertEqual(M.scan(self.rom,a)['classified_prefix_write_sha256'],M.scan(self.rom,b)['classified_prefix_write_sha256'])

    def test_mailbox_last_write_and_zero(self):
        for requests in ((0xA0,0xBF),(0xBF,0xA0),(0xA0,0)):
            a=T.Driver(self.rom);b=T.Driver(self.rom)
            for rid in requests:a.request(rid)
            b.request(requests[-1]);a.tick();b.tick()
            self.assertEqual(a.writes,b.writes)

    def test_music_reinitializes_and_clears_all_slots(self):
        for rid in range(0x81,0xA0):
            a=T.Driver(self.rom);a.request(0xAC)
            for _ in range(10):a.tick()
            a.request(rid);a.tick()
            self.assertFalse(a.active(T.SFX_CH))
            a.request(rid);a.tick()
            b=T.Driver(self.rom);b.request(rid);b.tick()
            self.assertEqual(bytes(a.mem[0xDE40:0xDF90]),bytes(b.mem[0xDE40:0xDF90]))

    def test_three_slot_coexistence_and_partial_release(self):
        d=M.timeline(self.rom,{30:[0xAC],35:[0xA0]},84)
        rows={x['tick']:x for x in d['transitions']}
        self.assertTrue(all(x&128 for x in rows[35]['flags'][4:]))
        self.assertEqual(rows[78]['priority'],0)
        self.assertTrue(rows[78]['flags'][4]&128)
        self.assertTrue(rows[78]['flags'][5]&128)
        self.assertFalse(rows[78]['flags'][6]&128)

    def test_fade_cancels_effects_and_terminal_fade_erases_selection(self):
        d=T.Driver(self.rom);d.request(0x81)
        for tick in range(1,58):
            if tick==30:d.request(0xAC)
            if tick==35:d.mem[0xDE09:0xDE0C]=bytes((12,1,2))
            if tick==57:d.request(0x99)
            d.tick()
            if tick==35:self.assertFalse(d.active(T.SFX_CH))
        self.assertFalse(d.active())
        d.request(0x99);d.tick();self.assertTrue(d.music_active())

    def test_pause_preserves_pending_mail_until_resume(self):
        d=T.Driver(self.rom);d.request(0x81);d.tick()
        d.mem[0xDE08]=128;d.tick();frozen=bytes(d.mem[0xDE40:0xDF90])
        d.request(0xA0)
        for _ in range(10):d.tick()
        self.assertEqual(bytes(d.mem[0xDE40:0xDF90]),frozen)
        self.assertEqual(d.mem[0xDE04],0xA0)
        d.mem[0xDE08]=0;d.tick()
        self.assertEqual(d.mem[0xDE04],0)
        self.assertTrue(d.mem[0xDF30]&128)

if __name__=='__main__':unittest.main()

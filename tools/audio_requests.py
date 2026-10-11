"""AUDIO-0: deterministic request evidence, not a PSG emulator or song decoder."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import csv
import rom as R
import player_scripts as P
import mghz_object_census as C
from oracle import Oracle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/rom-cache/audio/request-ledger.json'
CURATION = ROOT / 'data/audio-request-contexts.json'
CHANNELS = (0xDE40, 0xDE70, 0xDEA0, 0xDED0)

def digest(b):
    return hashlib.sha256(b).hexdigest()

def address(p, slot=2):
    return dict(rom_offset=p, bank=p//0x4000,
                cpu_address=p if p<0x8000 else slot*0x4000+p%0x4000)

def driver(rom):
    o = Oracle(rom)
    o.bank(1, 2); o.bank(2, 3)
    o.mem[0xDE00:0xDF90] = bytes(0x190)
    o.mem[0xDE03] = 0x80
    return o

def issue(o, rid):
    o.mem[0xDE04] = rid
    o.call(0x407F)
    selected = o.mem[0xDE03]
    o.call(0x4119)
    return selected

def control_traces(rom):
    rows=[]
    for rid in (0x81,0x84,0x85,0x8A,0x8F):
        o=driver(rom); o.mem[0xDE04]=rid
        ended=None
        for frame in range(1,1501):
            o.call(0x4000)
            if not any(o.mem[x]&0x80 for x in CHANNELS):
                ended=frame; break
        rows.append(dict(request_id=rid, first_inactive_update=ended, limit=1500,
                         evidence='controlled original driver calls; no PSG rendering, IRQ or real-time claim'))
    # Restart comparison at dispatch boundary, before any channel update.
    restarts=[]
    for rid in (0x81,0x84,0x85,0xBF,0xC4):
        o=driver(rom); issue(o,rid)
        active=[x for x in CHANNELS+(0xDF00,0xDF30,0xDF60) if o.mem[x]&128]
        initial={x:bytes(o.mem[x:x+11]) for x in active}
        for _ in range(10): o.call(0x4000)
        issue(o,rid)
        restarts.append(dict(request_id=rid, initialized_stream_headers_repeated=all(bytes(o.mem[x:x+11])==b for x,b in initial.items()), compared_channel_bases=active, compared_bytes_per_channel=11))
    o=driver(rom); issue(o,0x81)
    before=bytes(o.mem[0xDE40:0xDF90]); zero_selected=issue(o,0)
    zero_unchanged=bytes(o.mem[0xDE40:0xDF90])==before
    issue(o,0xF8)
    silence=not any(o.mem[x]&0x80 for x in CHANNELS+(0xDF00,0xDF30,0xDF60))
    priority=[]
    for current in (0,0x38,0x7F):
        o=driver(rom);o.mem[0xDE0F]=current;o.mem[0xDE04]=0xBF;o.call(0x407F)
        priority.append(dict(current_priority=current, selected_request=o.mem[0xDE03], pending=o.mem[0xDE04]))
    # Execute the original reward/timer routine with original resident bank 1,
    # then the driver with sound banks. Only IRQ delivery of D4A4 is supplied.
    scenarios=[]
    for sneakers_at in (None,100):
        o=driver(rom);issue(o,0x84);o.mem[0xD532]=6;o.word(0xD44C,600)
        o.mem[0xD297]=0;o.mem[0xD298]=0;o.mem[0xD4A3]=0
        requests=[];expired=None;inactive=None;zero_at=None;underflow_at=None
        for frame in range(1,1201):
            o.bank(1,1)
            if frame==sneakers_at: o.mem[0xD3A3]=4
            prior=o.mem[0xD532]
            o.call(0x4A74)
            if o.word(0xD44C)==0 and zero_at is None:zero_at=frame
            if o.word(0xD44C)==65535 and underflow_at is None:underflow_at=frame
            if prior and not o.mem[0xD532] and expired is None:expired=frame
            if o.mem[0xD4A4]:
                o.mem[0xDE04]=o.mem[0xD4A4];o.mem[0xD4A4]=0
            if o.mem[0xDE04]:requests.append(dict(update=frame,request_id=o.mem[0xDE04]))
            o.bank(1,2);o.bank(2,3);o.call(0x4000)
            if inactive is None and not any(o.mem[x]&0x80 for x in CHANNELS):inactive=frame
        scenarios.append(dict(sneakers_at=sneakers_at, selector_expired_at=expired,
                              requests=requests, timer_first_zero_at=zero_at,timer_first_underflow_at=underflow_at, music_first_inactive_update=inactive,
                              final_selector=o.mem[0xD532], final_music_active=any(o.mem[x]&128 for x in CHANNELS)))
    return dict(track_activity=rows, repeated_requests=restarts,
                zero=dict(selected=zero_selected, channel_state_unchanged=zero_unchanged),
                f8_all_channels_inactive=silence, ring_priority=priority,
                invincibility_then_sneakers=scenarios)

def extract(rom):
    contexts=json.loads(CURATION.read_text())
    P.engine_facts(rom);commands=P.derive_commands(rom)
    # Minimum driver/control evidence is hashed over explicit, reviewed spans.
    spans=[(0x807F,0x80B0),(0x8119,0x8138),(0x8168,0x81A7),
           (0x81A7,0x822B),(0x83E5,0x8415),(0x18E1,0x18ED),
           (0x4A74,0x4B46),(0x67D5,0x67EC),(0x5DF1,0x5E61)]
    records={}
    def get(rid):
        return records.setdefault(rid,dict(request_id=rid,request_hex=f'0x{rid:02X}',category='unknown',
                         friendly_name=None,name_status='unresolved',evidence=[],call_sites=[]))
    for row in csv.DictReader((ROOT/'data/sound-index-sms.csv').read_text().splitlines()):
        rid=int(row['id_hex'],16);p=int(row['pointer_file'],16)
        ptr=R.u16(rom,p)
        if ptr!=int(row['stored_address'],16) or ptr+0x4000!=int(row['file_offset'],16):
            raise ValueError('sound index differs from ROM')
        e=get(rid);e['category']='music' if rid<0xA0 else 'sfx'
        e['sound_pointer']=dict(pointer_rom=p,stored_cpu=ptr,target_rom=ptr+0x4000)
        e['evidence'].append('original driver dispatch: ROM 0x08119..0x08138, 0x08168..0x081A7; sound bank 2 in slot 1')
        e['arbitration_priority_byte']=rom[0x906F+(rid&127)-1]
    get(0).update(category='control',friendly_name='empty pending request (not silence)',name_status='driver-proven')
    get(0xF8).update(category='control',friendly_name='reset / silence',name_status='driver-proven')
    for key, val in contexts['names'].items():
        get(int(key,16)).update(friendly_name=val['name'],name_status='context-supported',name_evidence=val['source'])
    # These exact sites are individually source-reviewed; immediate request IDs
    # are regenerated, never supplied by the friendly-name annotation.
    handled=set()
    for key, ctx in contexts['direct_sites'].items():
        p=int(key,16)
        if rom[p:p+3]!=bytes((0x32,4,0xDE)) or rom[p-2]!=0x3E:
            raise ValueError(f'curated immediate store differs at {p:05X}')
        rid=rom[p-1];handled.add(p)
        get(rid)['call_sites'].append(dict(address(p),kind='direct',
                   trigger=ctx['trigger'],trigger_status=ctx['status'],evidence_source=ctx['source'],
                   instruction_sha256=digest(rom[p-2:p+3])))
    # Table-driven normal music, including every Special Stage and non-gameplay zone.
    for zone in range(13):
        for act in range(3):
            p=0x18BA+zone*3+act;rid=rom[p]
            get(rid)['call_sites'].append(dict(address(0x18B3),kind='zone_act_table',
                  table_operand_rom=p,zone=zone,act=act,
                  trigger='UpdateMusic $189B, when D4A3 == 0; index = zone*3 + act',
                  trigger_status='source-traced',evidence_source='docs/special-stages-foundation-audit.md; ROM 0x0189B..0x018BA'))
    for rid in (0x89,0x97):
        get(rid)['call_sites'].append(dict(address(0x48A3),kind='conditional_direct',
                  trigger='player clear setter $4892: act index 2 selects $97, other acts $89',
                  trigger_status='source-traced',evidence_source='docs/object-18-act-clear.md; ROM 0x04892..0x048AB'))
    handled.update((0x18B3,0x48A3,0x5CF,0x67E3,0x67E6,0xC33))
    # Use the accepted bounded object parser. It records syntactic state entry,
    # not proof that every pointer-table alias is instantiated during gameplay.
    notes=[]
    for ty in range(1,100):
        sc=C.state_scripts(rom,ty)
        if ty<=2:
            old=P.SCRIPT_BANK;P.SCRIPT_BANK=12
            try:
                states=[]
                for state,start in enumerate(sc['state_script_cpus']):
                    n=[];steps,_=P.parse_script(rom,start,commands,n)
                    states.append((state,[p for p,v in steps.items() if v[0]=='command' and v[2]==6]))
                    notes.extend(dict(type_id=ty,state=state,note=k,cpu=p) for k,p in n)
            finally:P.SCRIPT_BANK=old
        else:
            states=[(s['state'],[x['cpu'] for x in s['ops'] if x['op']=='sound']) for s in sc['states']]
            notes.extend(dict(type_id=ty,state=s['state'],note='bounded script ended without explicit terminator')
                         for s in sc['states'] if not s['cleanly_terminated'])
        for state,sites in states:
            for cpu in sites:
                p=sc['bank']*0x4000+cpu-0x8000
                if rom[p:p+2]!=bytes((255,6)):raise ValueError('script sound command mismatch')
                rid=rom[p+2]
                get(rid)['call_sites'].append(dict(address(p),kind='script_command_06',
                     type_id=ty,state=state,table_entry_rom=sc['type_table_entry_rom'],
                     state_pointer_rom=sc['state_table_rom']+state*2,
                     script_start_cpu=sc['state_script_cpus'][state],operand_rom=p+2,
                     trigger=f'type ${ty:02X} state ${state:02X} reaches this script command',
                     trigger_status='static script path; gameplay instantiation not inferred',
                     evidence_source='ROM scheduler $5DF1; table $65BA; engine/handler $67D5; bounded accepted script parser',
                     instruction_sha256=digest(rom[p:p+3])))
    # Preserve unresolved matches, without promoting raw byte matches to code.
    candidates=[]
    for p in range(len(rom)-2):
        if rom[p:p+3]==bytes((0x32,4,0xDE)) and p not in handled:
            candidates.append(dict(address(p),candidate_id=rom[p-1] if rom[p-2]==0x3E else None,
                                   status='unreviewed byte-pattern lead; not a verified call site'))
    dataflow=[dict(address(0x5CF),source='D4A4',meaning='IRQ forwards nonzero deferred request, clears latch; may overwrite DE04'),
              dict(address(0xC33),source='D2BF',meaning='sound-test user selection on button bit $20; unrestricted value, not gameplay evidence'),
              dict(address(0x67E3),source='FF06 operand',meaning='script handler writes operand twice at $67E3 and $67E6; no delay between stores')]
    for e in records.values():
        e['call_sites'].sort(key=lambda s:(s['rom_offset'],s.get('type_id',0),s.get('state',0),s.get('zone',0),s.get('act',0)))
        e['confidence']='driver-classified; trigger evidence is per site; no audible playback claimed'
    ordered=[records[k] for k in sorted(records)]
    return dict(schema_version=1,rom_sha256=R.SHA256,base_main='6874337671d01891909a1b5d439e0baba3fbfb80',
                scope='AUDIO-0 request/control audit; static request paths plus controlled original CPU routines',
                address_rules='ROM offsets are integers, half-open spans. Bank 2 driver executes in slot 1 ($4000); gameplay banks 12/30 execute in slot 2 ($8000).',
                summary=dict(unique_ids=len(ordered),categories=dict(Counter(e['category'] for e in ordered)),
                             friendly_names_supported=sum(e['friendly_name'] is not None for e in ordered),
                             named_by_category=dict(Counter(e['category'] for e in ordered if e['friendly_name'] is not None)),
                             ids_with_sites_by_category=dict(Counter(e['category'] for e in ordered if e['call_sites'])),
                             unknown_names=[e['request_hex'] for e in ordered if e['friendly_name'] is None],
                             ids_without_verified_call_sites=[e['request_hex'] for e in ordered if not e['call_sites']]),
                reviewed_spans=[dict(start=a,end=b,sha256=digest(rom[a:b])) for a,b in spans],
                requests=ordered,shared_dataflow_sites=dataflow,unreviewed_store_candidates=candidates,
                script_parser_notes=notes,controlled_results=control_traces(rom))

DOC=ROOT/'docs/audio-request-audit.md'
TABLE_START='<!-- AUDIO_TABLE_START -->'
TABLE_END='<!-- AUDIO_TABLE_END -->'

def render_table(data):
    lines=['| ID | Driver category | Supported context name | Verified ROM request locations |',
           '|---|---|---|---|']
    for e in data['requests']:
        sites=sorted({s['rom_offset'] for s in e['call_sites']})
        locations=', '.join(f'${p:05X}' for p in sites) or 'none found'
        lines.append(f"| ${e['request_id']:02X} | {e['category']} | {e['friendly_name'] or 'unknown'} | {locations} |")
    return '\n'.join(lines)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('rom');ap.add_argument('--check',action='store_true');a=ap.parse_args()
    data=extract(R.load(a.rom))
    text=json.dumps(data,indent=2)+'\n'
    doc=DOC.read_text()
    before,body=doc.split(TABLE_START)
    _,after=body.split(TABLE_END)
    rendered=before+TABLE_START+'\n'+render_table(data)+'\n'+TABLE_END+after
    if a.check:
        if OUT.read_text()!=text:raise SystemExit('audio ledger differs; regenerate')
        if doc!=rendered:raise SystemExit('audio human index differs; regenerate')
    else:
        OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(text)
        DOC.write_text(rendered)
    print(json.loads(text)['summary'])
if __name__=='__main__':main()

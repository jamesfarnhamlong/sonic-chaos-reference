"""M5 metadata-only original-driver probes. Never exports audio or stream bytes.

python tools/m5_audio_contract.py PRIVATE_ROM catalogue
python tools/m5_audio_contract.py PRIVATE_ROM interactions
Outputs safe numeric evidence under data/m5; no renderer is invoked.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import audio1_psg_trace as T

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/m5'

def save(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    if name=='interactions.json':
        # One bounded numeric scenario per line keeps public review manageable.
        header=json.dumps({k:v for k,v in value.items() if k!='scenarios'},indent=2).rstrip()[:-1].rstrip()
        body=',\n'.join('    '+json.dumps(k)+': '+json.dumps(v,separators=(',',':')) for k,v in value['scenarios'].items())
        output=header+',\n  "scenarios": {\n'+body+'\n  }\n}\n'
    else:output=json.dumps(value,indent=2)+'\n'
    (OUT / name).write_text(output, encoding='utf-8')

def scan(rom, rid, limit=30000):
    """Stop at inactive state or exact RAM+register recurrence; verify next period.

    No PCM oscillator phase claim. RAM includes every channel and global driver byte.
    """
    d=T.Driver(rom); d.request(rid)
    channels=T.MUSIC_CH if rid<0xA0 else T.SFX_CH
    seen={}; active=set(); audible=set(); last=[None]*4; releases={}
    reads=[0]*4
    def on_read(q):
        if q.cpu.ix in T.MUSIC_CH: reads[T.MUSIC_CH.index(q.cpu.ix)]+=1
    d.hook(0x4341,on_read)
    digest=hashlib.sha256(); end=None; recurrence=None
    for tick in range(1,limit+1):
        start=len(d.writes); before=d.active(channels); d.tick()
        for addr in d.active(channels): active.add(addr)
        for addr in before:
            if not d.mem[addr]&128: releases[f'{addr:04X}']=tick
        for ch,a in enumerate(d.psg.att):
            if a<15: audible.add(ch); last[ch]=tick
        for _,b in d.writes[start:]: digest.update(tick.to_bytes(4,'little')+bytes([b]))
        if not d.active(channels): end=tick; break
        state=bytes(d.mem[0xDE00:0xDF90])+repr(d.psg.state()).encode()
        if state in seen:
            first=seen[state]; period=tick-first
            w1=[(u-first,b) for u,b in d.writes if first<u<=tick]
            for _ in range(period): d.tick()
            w2=[(u-tick,b) for u,b in d.writes if tick<u<=tick+period]
            recurrence=dict(first_tick=first,period_ticks=period,
                subsequent_period_writes_identical=w1==w2,writes_per_period=len(w1))
            break
        seen[state]=tick
    return dict(ticks_to_classification=tick,finite_inactive_tick=end,
        lifecycle='finite' if end else ('repeating' if recurrence and recurrence['writes_per_period'] else 'unresolved'),
        recurrence=recurrence,active_channel_addresses=[f'{a:04X}' for a in sorted(active)],
        release_ticks=releases,audible_register_channels=sorted(audible),last_non_off_ticks=last,
        audible_note='register attenuation below 15, not measured PCM or listening',
        tone_read_counts=reads,classified_prefix_write_sha256=digest.hexdigest(),limit_ticks=limit)

def catalogue(rom):
    ledger=json.loads((ROOT/'data/rom-cache/audio/request-ledger.json').read_text())
    groups=defaultdict(list)
    for rid in range(0x81,0xC5): groups[T.header_facts(rom,rid)['header_rom']].append(rid)
    rows=[]
    corrections={0x82:'Character-selection music',0x99:'Finite title music',
        0x90:'Opening / Electric Egg Zone act 3 music',0xA0:'Character-choice / Continue confirmation feedback',
        0xBE:'Title lead-in / MGHZ projectile script feedback'}
    for old in ledger['requests']:
        rid=old['request_id']; row=dict(old)
        row['friendly_name']=corrections.get(rid,old['friendly_name']) or f'Unknown ${rid:02X}'
        if row['friendly_name']=='unknown':row['friendly_name']=f'Unknown ${rid:02X}'
        row['historical_friendly_name']=old['friendly_name']
        row['observed_gameplay_use']='not established per ID; static sites are not observed gameplay'
        row['accepted_PC_M4_observation']='Chief reported scoped Windows PASS; see management600951f' if rid in (0x81,0x82,0x90,0x99,0xBF,0xA6) else 'not individually established'
        if rid==0x90:row['observed_gameplay_use']='inherited approximate original opening-frame harness evidence; not every indexed context'
        if rid in (0x99,0xBE):
            off=0x754 if rid==0x99 else 0x744
            assert rom[off:off+5]==bytes((0x3E,rid,0x32,0x04,0xDE))
            row['call_sites']=list(row['call_sites'])+[dict(rom_offset=off+2,bank=0,cpu_address=off+2,kind='direct',trigger='original title scene request',trigger_status='M4/M5 byte-verified source; not new natural gameplay',instruction_sha256=hashlib.sha256(rom[off:off+5]).hexdigest(),evidence_source='M4 pilot specification; original title source $0719')]
        if rid==0x82:
            row['historical_call_sites']=row['call_sites']
            row['call_sites']=[dict(s,trigger='character-selection scene $3065; original title music is separate99') for s in row['call_sites']]
        row['source_context_present']=bool(old['call_sites'])
        if rid in (0x99,0xBE):row['source_context_present']=True
        row['provenance']=['AUDIO-0 request-ledger.json at 8df6e7e','M4 pilot/production contract at 8df6e7e','M5 original-driver controlled execution']
        if 0x81<=rid<=0xC4:
            h=T.header_facts(rom,rid); facts=scan(rom,rid,250000 if rid in (0x8C,0x91) else 30000)
            if rid>=0xA0:
                for i,s in enumerate(h['streams']):s['initial_flags']=rom[h['header_rom']+4+6*i]
            row['driver_header']=h; row['execution']=facts
            aliases=[v for v in groups[h['header_rom']] if v!=rid]
            row['header_alias_ids']=aliases
            row['identity']='same-header alias' if aliases else 'distinct header; acoustic distinctness not asserted'
            if not facts['audible_register_channels']:row['identity']='register-silent in complete classified run' if facts['lifecycle']!='unresolved' else 'unresolved audibility'
            row['initialization']='music reset + all header channels' if rid<0xA0 else 'replace header-selected SFX slots; preserve other active slots'
            row['priority']={'table_byte':T.priority_byte(rom,rid),'stored':T.priority_byte(rom,rid)&127,'admission':'raw table byte >= current global DE0F; equal admitted'}
            row['stop_replace_fade']='admitted F8/music init resets all; same-ID admitted restarts; direct fade cancels SFX then attenuates music; see driver contract'
            row['confidence']='ROM-executed header/lifecycle; inherited source-traced request contexts; no natural-use or acoustic-name inference'
        else:
            row['identity']='control-only';row['priority']={'table_byte':None if rid==0 else T.priority_byte(rom,rid),'stored':None if rid==0 else T.priority_byte(rom,rid)&127,'admission':'00 ignored; F8 raw priority57 hex can be dropped above57'}
            row['initialization']='none' if rid==0 else 'reset all seven channel structures and PSG attenuation'
            row['execution']={'lifecycle':'control-only'}
            row['stop_replace_fade']='00 cancels pending byte only, no stop; admitted F8 resets/silences; lower-priority F8 drops'
        rows.append(row)
        print(f'{rid:02X}: {row["execution"]["lifecycle"]}',flush=True)
    by_hash=defaultdict(list)
    for row in rows:
        if 'classified_prefix_write_sha256' in row['execution']:
            by_hash[row['execution']['classified_prefix_write_sha256']].append(row['request_id'])
    for row in rows:
        rid=row['request_id']
        if 0x81<=rid<=0xC4:
            row['equal_solo_command_output_ids']=[i for i in by_hash[row['execution']['classified_prefix_write_sha256']] if i!=rid]
            row['identity']='distinct solo command-output target' if not row['equal_solo_command_output_ids'] else 'duplicate solo command output; request identity/priority retained'
            row['sound_test_disposition']='playable after private production validation'
        if 0x9B<=rid<=0x9F:
            row['identity']='empty music streams; all four immediately terminate; tone2 period-zero register residue, audibility unresolved'
            row['sound_test_disposition']='unavailable empty stream; no valid musical output; do not play'
        elif row['category']=='control':row['sound_test_disposition']='control action; no PCM asset'
    save('catalogue.json',dict(schema_version=1,rom_sha256=T.ROM_SHA256,
        research_parent='8df6e7e65ea93f7e49f0f975137eb55c0c5e5bf5',management='600951fde25ab27b3acf4bc6c6881f3f13654100',
        method='original isolated Z80 driver, no PCM/no hardware/no GameMaker',entries=rows))

def timeline(rom, events, ticks=180):
    d=T.Driver(rom); d.request(0x81); transitions=[]; previous=None
    for tick in range(1,ticks+1):
        for rid in events.get(tick,[]):d.request(rid)
        d.tick()
        state=([d.mem[a]&0xC4 for a in T.CHANNELS],d.mem[0xDE0F])
        if state!=previous:
            transitions.append(dict(tick=tick,flags=state[0],priority=state[1]))
            previous=state
    return dict(events={str(t):v for t,v in events.items()},ticks=ticks,transitions=transitions,
        final_active=[f'{a:04X}' for a in d.active()],final_attenuation=list(d.psg.att))

def interactions(rom):
    # All SFX x all attainable stored-priority bytes: original arbitration routine.
    checks=0
    for rid in list(range(0xA0,0xC5))+[0xF8]:
        for current in range(128):
            d=T.Driver(rom);d.mem[0xDE0F]=current;d.request(rid);d.call(0x407F)
            assert (d.mem[0xDE03]==rid)==(T.priority_byte(rom,rid)>=current)
            checks+=1
    cat=json.loads((OUT/'catalogue.json').read_text())['entries']
    representatives={}
    for r in cat:
        if r['category']=='sfx':
            key=tuple(s['latch'] for s in r['driver_header']['streams'])
            representatives.setdefault(key,r['request_id'])
    scenarios={}
    ids=list(representatives.values())
    for a in range(0xA0,0xC5):
        for b in range(0xA0,0xC5):
            scenarios[f'{a:02X}-{b:02X}']=timeline(rom,{30:[a],35:[b]},500)
    for rid in range(0xA0,0xC5):
        scenarios[f'{rid:02X}-restart']=timeline(rom,{30:[rid],35:[rid]},500)
        scenarios[f'{rid:02X}-music']=timeline(rom,{30:[rid],35:[0x99]},80)
        scenarios[f'{rid:02X}-reset']=timeline(rom,{30:[rid],35:[0xF8]},80)
    save('interactions.json',dict(rom_sha256=T.ROM_SHA256,method='controlled original Z80 driver; numeric state transitions only',
        arbitration_assertions=checks,representatives=[dict(latches=list(k),id=v) for k,v in representatives.items()],scenarios=scenarios))

def extensions(rom):
    loops={}
    for rid in (0x8C,0x90,0x91):
        d=T.Driver(rom);d.request(rid);seen=[{} for _ in range(4)];found=[None]*4
        # Include shared tempo and volume/noise globals; omit unrelated channel RAM.
        for tick in range(1,170000):
            d.tick()
            for ch,addr in enumerate(T.MUSIC_CH):
                if found[ch]:continue
                reg=(d.psg.tone[ch],d.psg.att[ch]) if ch<3 else (d.psg.noise,d.psg.tone[2],d.psg.att[3])
                shared=bytes(d.mem[0xDE15:0xDE17]) if ch==3 else b''
                key=bytes(d.mem[0xDE01:0xDE03])+shared+bytes(d.mem[addr:addr+48])+repr(reg).encode()
                if key in seen[ch]:found[ch]=dict(first_tick=seen[ch][key],period_ticks=tick-seen[ch][key])
                else:seen[ch][key]=tick
            if all(found):break
        loops[f'{rid:02X}']=found
    # Full register state equality is checked over two projected periods separately.
    for rid_hex,channels in loops.items():
        rid=int(rid_hex,16);n=max(x['first_tick']+2*x['period_ticks'] for x in channels)
        d=T.Driver(rom);d.request(rid);states=[[] for _ in range(4)]
        for tick in range(1,n+1):
            d.tick()
            for ch in range(4):
                states[ch].append((d.psg.tone[ch],d.psg.att[ch]) if ch<3 else (d.psg.noise,d.psg.tone[2],d.psg.att[3]))
        for ch,x in enumerate(channels):
            a=x['first_tick'];p=x['period_ticks'];x['next_period_registers_identical']=states[ch][a:a+p]==states[ch][a+p:a+2*p]
    # Per-slot music restoration: actual bit4 clear and separate tone/noise readers.
    recovery=[]
    for rid in range(0xA0,0xC5):
        for at in (200,331,702):
            d=T.Driver(rom);d.request(0x81);reads=[[] for _ in range(4)];events=[]
            def read(q):
                if q.cpu.ix in T.MUSIC_CH:reads[T.MUSIC_CH.index(q.cpu.ix)].append(q.update)
            d.hook(0x4341,read);d.hook(0x4650,read)
            prev=None
            for tick in range(1,at+300):
                if tick==at:d.request(rid)
                d.tick()
                state=([d.mem[a] for a in T.CHANNELS],d.mem[0xDE0F])
                if tick>=at and state!=prev:events.append(dict(tick=tick,flags=state[0],priority=state[1]))
                prev=state
            # Publish only counts and release/recovery facts, never full stream-read maps.
            summary=[]
            for ch,addr in enumerate(T.MUSIC_CH):
                suppressed=next((e['tick'] for e in events if e['flags'][ch]&4),None)
                release=next((e['tick'] for e in events if suppressed and e['tick']>suppressed and not e['flags'][ch]&4),None)
                clear=next((e['tick'] for e in events if release and e['tick']>release and not e['flags'][ch]&20),None)
                expected=next((t for t in reads[ch] if release and t>release),None)
                summary.append(dict(channel=ch,suppressed_tick=suppressed,release_tick=release,
                    recovery_tick=clear,next_reader_tick=expected,recovery_matches_reader=clear==expected if release else None,
                    reader_calls=len(reads[ch])))
            recovery.append(dict(id=rid,request_tick=at,channels=summary))
    controls={}
    for mode in ('fade','pause'):
        d=T.Driver(rom);d.request(0x81);rows=[]
        for tick in range(1,140):
            if tick==30:d.request(0xBA)
            if tick==35:
                if mode=='fade':d.mem[0xDE09:0xDE0C]=bytes((12,1,2))
                else:d.mem[0xDE08]=128
            if tick==45 and mode=='pause':d.request(0xBF)
            if tick==55 and mode=='pause':d.mem[0xDE08]=0
            d.tick()
            if 29<=tick<=65:rows.append(dict(tick=tick,flags=[d.mem[a] for a in T.CHANNELS],priority=d.mem[0xDE0F],mailbox=d.mem[0xDE04],pause=d.mem[0xDE08],fade=d.mem[0xDE09],att=list(d.psg.att)))
        controls[mode]=rows
    save('extensions.json',dict(rom_sha256=T.ROM_SHA256,method='controlled Z80 original-driver; numeric-only evidence',
        channel_loop_candidates=loops,recovery=recovery,controls=controls,
        code_spans=[dict(cpu_start=a,cpu_end=b,sha256=hashlib.sha256(rom[a+0x4000:b+0x4000]).hexdigest()) for a,b in
            ((0x4000,0x407F),(0x407F,0x4119),(0x41A7,0x422B),(0x4341,0x434F),(0x464A,0x4674),(0x47C8,0x481C))]))

def reports(rom):
    cat=json.loads((OUT/'catalogue.json').read_text())
    lines=['# M5 complete indexed audio catalogue','',
        '24 October 2026. Research-only contract; no M5 PCM was rendered.',
        'Machine authority: [catalogue.json](../data/m5/catalogue.json).',
        'Source: accepted M4 research8df6e7e; management main600951f; private POC11bff343.',
        'All68 indexed headers were executed against the SHA-256-authenticated ROM.',
        'Each row retains all inherited request contexts, addresses and evidence; later corrections are additive.',
        'Static request sites, isolated playback and observed natural use are distinct fields.',
        'No-site and unknown-name entries are not automatically silent or unused.','',
        '## Complete matrix','',
        'Priority is the raw hexadecimal lookup byte; stored value is masked to7 bits.',
        'End is the first inactive tick from request-at1, not padded WAV duration.',
        'Loop notation is first repeated driver state / period in ticks (60/s).',
        'Slot addresses and every initialization field are in JSON. Sites below are deduplicated ROM offsets.',
        'Unknown labels deliberately remain numeric.','',
        '| ID | Kind | Verified label / requesting event | Priority | Lifecycle | Equal solo output | Request sites |',
        '|---|---|---|---|---|---|---|']
    for r in cat['entries']:
        x=r['execution'];rec=x.get('recurrence')
        life=f'loop {rec["first_tick"]}/{rec["period_ticks"]}' if rec else (f'end {x["finite_inactive_tick"]}' if 'finite_inactive_tick' in x else 'control only')
        if 0x9B<=r['request_id']<=0x9F:life='empty; unavailable'
        aliases=', '.join(f'${i:02X}' for i in r.get('equal_solo_command_output_ids',[])) or '—'
        sites=', '.join(f'${i:05X}' for i in sorted(set(s['rom_offset'] for s in r['call_sites']))) or 'none verified'
        pr=r['priority']['table_byte'];pr='—' if pr is None else f'${pr:02X}'
        lines.append(f'| ${r["request_id"]:02X} | {r["category"]} | {r["friendly_name"]} | {pr} | {life} | {aliases} | {sites} |')
    lines+=['','## Reconciliation and limits','',
        'AUDIO-0 is preserved unchanged as historical evidence. Its82 “Title / character-selection” label is narrowed to character selection;99 is the finite original title cue, verified at ROM0756. BE title lead-in at0746 is added alongside its existing projectile contexts.90 remains opening **and EEZ3**, not an opening-only composition.',
        '00 is empty pending request, never silence. F8 is reset/silence only when admitted; its priority57 can be rejected. The accepted M4 unconditional F8 reset is a documented adapter difference pending review.',
        'All37 effects terminate. Eleven music entries repeat; fifteen nonempty music entries are finite. Five more indexed music entries9B–9F immediately end; all four streams begin with F2. They leave a period-zero tone2 attenuation residue in the register model, so silence at a physical output is not asserted. Do not render them as five playable tracks.',
        'No two IDs share the same header pointer. Three effect pairs have equal complete solo command hashes (A8/C2, BB/C4, BC/C0), despite distinct headers/priorities. This supports shared PCM targets, not merging requests or acoustic names.60 nonempty distinct command-output targets is the production estimate.',
        'The JSON reports every driver header, initialized flags, category, priority, finite/loop facts, per-slot release ticks, output identity, source contexts and confidence. Natural original-game use is not individually established for the whole catalogue. M4 Chief Windows observation is stored separately for its six accepted IDs.',
        'Companions: [driver integration](m5-driver-integration-contract.md), [Sound Test](m5-sound-test-contract.md), [production plan](m5-production-plan.md), [Manager handover](m5-manager-handover.md).']
    (ROOT/'docs/m5-audio-catalogue.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    music=[r for r in cat['entries'] if r['category']=='music' and r['request_id']<0x9B]
    ticks=sum((r['execution']['recurrence']['first_tick']+r['execution']['recurrence']['period_ticks']) if r['execution']['recurrence'] else r['execution']['finite_inactive_tick'] for r in music)
    save('production-estimate.json',dict(rom_sha256=T.ROM_SHA256,distinct_nonempty_command_targets=60,nonempty_music_ids=26,distinct_sfx_targets=34,
        music_prefix_plus_body_ticks=ticks,music_four_stems_bytes=ticks*735*2*4,chunk_ticks=4096,mono_chunk_bytes=4096*735*2,
        estimate_only=True,loop_cuts_selected_for_new_tracks=False))

def poc_inventory(poc):
    poc=Path(poc)
    head=subprocess.check_output(['git','-C',str(poc),'rev-parse','HEAD'],text=True).strip()
    if head!='11bff34356d5f5d979218896dc95fdc4bb265eae':raise ValueError('requires exact accepted M4 POC')
    rows=[];files=[]
    for folder in ('scripts','objects'):
        for path in sorted((poc/folder).rglob('*.gml')):
            data=path.read_bytes();hits=[]
            for line,text in enumerate(data.decode('utf-8-sig').splitlines(),1):
                if re.search(r'chaos_audio_(?:write|gameplay|request|scene|fade)\(',text):
                    code=text.split('//',1)[0]
                    hits.append(dict(line=line,numeric_candidates=sorted(set(int(h,16) for h in re.findall(r'\$([0-9A-Fa-f]{2})\b',code))),
                        dynamic_or_wrapper=bool(re.search(r'chaos_audio_(?:write|gameplay|request)\(cp_',code))))
            if hits:
                rows.append(dict(path=path.relative_to(poc).as_posix(),sha256=hashlib.sha256(data).hexdigest(),sites=hits))
    for rel in ('scripts/SCR_chaos_debug_select/SCR_chaos_debug_select.gml','scripts/SCR_buttons/SCR_buttons.gml','objects/OBJ_chaos_debug_select/Step_0.gml','objects/OBJ_chaos_debug_select/Draw_0.gml'):
        files.append(dict(path=rel,sha256=hashlib.sha256((poc/rel).read_bytes()).hexdigest()))
    save('poc-preflight.json',dict(commit=head,visibility_verified='private via authenticated GitHub connector 24 October2026',
        method='read-only accepted local source, matched commit; syntactic call inventory, not runtime event proof',
        source_call_inventory=rows,sound_test_sources=files))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('mode',choices=['catalogue','interactions','extensions','reports','poc']);p.add_argument('--poc');a=p.parse_args()
    rom=T.load_rom(a.rom)
    if a.mode=='poc':poc_inventory(a.poc)
    else:globals()[a.mode](rom)

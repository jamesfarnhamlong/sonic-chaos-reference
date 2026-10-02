"""Focused THZ3 contact/presentation ROM oracle; reuses the existing boss harness.

Run: .venv/Scripts/python tools/thz3_boss_contact_followup.py ROM [--check]
No ROM bytes or graphic dumps are emitted. All whole-game writes occur at $1336.
"""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import thz3_boss_support as base

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/rom-cache/thz3/boss-contact-followup.json'
STATES = (6, 9, 12, 15)
POINTS = {'left': (-26, 0), 'right': (26, 0), 'below': (0, 23), 'top': (0, -40)}


def player(lab):
    m, o = lab.m, lab.o
    return dict(current=m[0xD501], requested=m[0xD502], flags=m[0xD503],
                floor=m[0xD522], vx=base.s16(o.word(0xD516)), vy=base.s16(o.word(0xD518)),
                damage_request=m[0xD3B0], hurt_timer=m[0xD3B1], visibility=m[0xD504])


def case(lab, state, dx, dy, **kw):
    r = lab.case(state, dx, dy, **kw)
    r.update(player=player(lab), boss_current=lab.r(1), boss_frame=lab.r(6),
             boss_timer=lab.r(7), boss_flags=lab.r(4), reaction=lab.r(0x1F))
    return r


def response_sweep(rom):
    lab = base.BossLab(rom)
    rows, mismatches, count = [], [], 0
    # Also vary D503 bit 4; both floor/airborne combinations, both attack/hurt
    # bits and invulnerability bit are tested. D532 is independently varied.
    for st, region, flags, power, vx, vy in itertools.product(
            STATES, POINTS, (2, 3, 0x12, 0x13, 0x42, 0x43, 0x82, 0x83, 0xC2, 0xC3),
            (0, 6), (-1536, -1, 0, 1, 1536), (-2048, -1, 0, 1, 2048)):
        dx, dy = POINTS[region]
        floor = 2 if not flags & 1 else 0
        r = case(lab, st, dx, dy, d503=flags, d522=floor, d532=power, vx=vx, vy=vy)
        p = r['player']
        if region == 'top':
            want = (vx, -1024 if vy >= 0 else vy, (flags | 1) & ~2 if vy >= 0 else flags,
                    floor & ~2 if vy >= 0 else floor, 11 if vy >= 0 else 0, 8, st+1)
        else:
            want = (-1536 if region == 'left' else 1536 if region == 'right' else vx,
                    1536 if region == 'below' else -vy, flags, floor, 27, 7, st+2)
        got = (p['vx'], p['vy'], p['flags'], p['floor'], p['requested'], r['health'], r['requested'])
        count += 1
        if got != want:
            mismatches.append(dict(state=st, region=region, flags=flags, power=power, vx=vx, vy=vy, got=got, want=want))
        if flags == 3 and power == 0 and vx == 0 and vy in (-2048, 0, 2048):
            rows.append(dict(state=st, region=region, before=dict(vx=vx, vy=vy, flags=flags, floor=floor), after=r))
    return dict(cases=count, mismatches=mismatches, examples=rows)


def geometry_sweep(rom):
    lab = base.BossLab(rom)
    count, mismatches, edges = 0, [], []
    # Exhaustive normal-Sonic rectangle including an exterior one-pixel rim;
    # every minimum-depth tie and +/-1 classification boundary is covered.
    for st, dx, dy in itertools.product(STATES, range(-29,30), range(-49,26)):
        r = case(lab, st, dx, dy, d503=3)
        c = base.psc.model_contact(dx, dy, 8, 24, 20, 48)
        want = base.boss_model(st, c, True, 0, 256, 8)
        got = base.boss_outcome(r, st, 8)
        count += 1
        if r['contact_bits'] != c or got != want:
            mismatches.append([st,dx,dy,c,r['contact_bits'],want,got])
        if st == 6 and ((dx in (-15,-14,-13,13,14,15) and dy in (-35,-34,-33)) or
                        (dx == 0 and dy in (-49,-48,-21,-20,-19,-1,0,24,25))):
            edges.append(dict(dx=dx,dy=dy,contact=c,result=got))
    return dict(cases=count,mismatches=mismatches,boundary_examples=edges)


def immunity(rom):
    lab = base.BossLab(rom)
    rows = []
    for st, region, flags, power in itertools.product((*STATES,18), POINTS,
            (0,2,0x40,0x42,0x80,0x82,0xC0,0xC2), (0,6)):
        r = case(lab, st, *POINTS[region], d503=flags, d522=2, d532=power, vy=512, vx=128)
        before_merge = player(lab)
        # The damage request is consumed on the NEXT player update. Here isolate
        # $48BC (no terrain/movement), with a nonzero i-frame timer and rings.
        lab.m[0xD29A] = 0x20
        lab.m[0xD3B1] = 30 if flags & 0x80 else 0
        lab.m[0xD520] = 0
        lab.o.cpu.ix = 0xD500
        lab.o.call(0x48BC)
        rows.append(dict(state=st,region=region,flags=flags,power=power,boss_contact=r,
                         before_damage_consumer=before_merge,after_damage_consumer=player(lab)))
    return rows


def cooldown(rom):
    lab = base.BossLab(rom)
    rows=[]
    for region, flags in itertools.product(POINTS, (0,2,0x80,0x82,0x40,0x42)):
        first=case(lab,6,*POINTS[region],d503=flags)
        sequence=[dict(update=0,result=first)]
        # Original $99AE helper only: a fresh overlap is imposed per call so
        # projection cannot accidentally move the player out of the test.
        for n in range(1,5):
            lab.o.position(lab.r(0x11,2)-26,lab.r(0x14,2))
            lab.m[0xD3B0]=0
            lab.call_bank(30,0x99AE)
            sequence.append(dict(update=n,cooldown=lab.r(0x1E),player=player(lab),health=lab.r(0x26),
                                 x=lab.o.word(0xD511),contact_bits=lab.r(0x21)&15))
        rows.append(dict(region=region,flags=flags,sequence=sequence))
    # Actual state callbacks: reaction paths must never run contact, and do not
    # decrement +1E. Check both top and hit reaction for all fighting phases.
    scope=[]
    for st in range(6,19):
        case(lab,st,-26,0,d503=0,cooldown=2,reaction=20)
        scope.append(dict(state=st,cooldown=lab.r(0x1E),health=lab.r(0x26),player=player(lab)))
    return dict(rows=rows,decrement_scope=scope)


def progression(rom):
    lab=base.BossLab(rom)
    rows=[]
    for st,hp,region in itertools.product(STATES,range(8,0,-1),('left','right','below')):
        r=case(lab,st,*POINTS[region],d503=3,health=hp,vy=768,vx=128)
        timeline=[]
        for n in range(1,24):
            # No artificial fresh contact in the subsequent callbacks.
            lab.o.position(1700,80)
            lab.step()
            timeline.append(dict(update=n,state=lab.r(1),requested=lab.r(2),frame=lab.r(6),
                                 timer=lab.r(7),reaction=lab.r(0x1F),vx=base.s16(lab.r(0x16,2)),
                                 phase=lab.r(0x32),flags=lab.r(4),health=lab.r(0x26)))
        rows.append(dict(hit=9-hp,state=st,region=region,before_health=hp,contact=r,timeline=timeline))
    return rows


def flash(rom):
    lab=base.o50.Fixture(rom)
    lab.o.bank(2,29);lab.m[0xD12B]=29
    lab.m[0xD48F],lab.m[0xD490]=0x35,0x20
    lab.m[0xD452:0xD456]=bytes((7,0,0,0))
    rows=[]
    for n in range(1,11):
        lab.o.cpu.iy=0xD452
        lab.o.call(0x8018) # real per-record dispatcher; cleared command 0 is RET
        rows.append(dict(call=n,command=lab.m[0xD452],step=lab.m[0xD454],counter=lab.m[0xD455],
                         colors=[lab.m[0xD48F],lab.m[0xD490]],pending=lab.m[0xD496]))
    return rows


def entry_and_hit_trace(rom):
    t=base.Thz3(rom)
    m,s,u=t.m,t.s,t.u
    sound=base.o50._sound_logger(s)
    contacts=[]
    def contact_hook(label):
        def hook(machine):
            if machine.slot[2]!=30 or machine.cpu.ix!=t.boss():return
            contacts.append(dict(stage=label,update=t.al.count-1,current=m[0xD501],requested=m[0xD502],
                                 flags=m[0xD503],floor=m[0xD522],vx=base.s16(u(0xD516)),vy=base.s16(u(0xD518))))
        return hook
    s.add_pc_hook(0x99DD,contact_hook('before_8105'))
    s.add_pc_hook(0x99E0,contact_hook('after_8105'))
    hit={'at':None}
    def driver(n):
        b=t.boss()
        if not b:return
        if m[b+1] in (3,18):
            s.w16(0xD511,1696);s.w16(0xD514,238)
            s.w16(0xD516,0);s.w16(0xD518,0)
        if m[b+1]==6 and hit['at'] is None:
            hit['at']=n
            s.w16(0xD511,u(b+0x11)-26);s.w16(0xD514,u(b+0x14)-8)
            s.w16(0xD516,0);s.w16(0xD518,768)
            m[0xD503]=3;m[0xD502]=10
        elif hit['at'] is not None and n>hit['at']:
            s.w16(0xD511,1696);s.w16(0xD514,80)
            s.w16(0xD516,0);s.w16(0xD518,0)
    def sample():
        b=t.boss()
        r=t.sample_boss()
        r.update(frame=s.frame,cram=list(s.cram[16:32]),flash=list(m[0xD452:0xD456]),
                 player_flags=m[0xD503],player_floor=m[0xD522],player_req=m[0xD502],
                 player_vx=base.s16(u(0xD516)),player_vy=base.s16(u(0xD518)),
                 queue=[list(m[a:a+4]) for a in range(0xD452,0xD472,8)],
                 art_request=m[0xD3B3],palette_request=[m[0xD494],m[0xD495]],
                 hud=base._hud_rows(m),sprite_palette_pending=m[0xD496])
        if b:
            sat=base.o50._sat_comparison(rom,s,b)
            r.update(mapping=m[b+6],timer=m[b+7],flags=m[b+4],hud_child_type=m[u(b+0x34)],sat=sat,
                     boss_screen_y=u(b+0x1C),sat_entries=[list(x[1:]) for x in s.sat()])
        return r
    rows=t.al.run(driver,sample,320,pad=lambda n:base.psc.PAD['RIGHT'] if n<75 else 0,restore=False)
    first=next(i for i,r in enumerate(rows) if r['boss'] is not None)
    mappings=base.o50.frame_table(rom)['frames']
    for i,r in enumerate(rows):
        if r['boss'] is None:continue
        found,visible=0,0
        if i and rows[i-1]['boss'] is not None:
            p=rows[i-1];have={tuple(x) for x in r['sat_entries']}
            for piece in mappings[p['mapping']]['pieces']:
                x=p['boss_screen_x']+piece['x'];y=p['boss_screen_y']+piece['y']
                if (y&255,x&255,piece['tile_offset']) in have:
                    found+=1
                    if 0<=x<256 and -15<=y<192:visible+=1
        r['sat_previous_update_matches']=found
        r['onscreen_matched_pieces']=visible
        del r['sat_entries']
        del r['sat']
    return dict(created=first,hit_driver_update=hit['at'],rows=[dict(update=i-first,**r) for i,r in enumerate(rows) if i>=first],
                sounds=[list(x) for x in sound],contact_hooks=contacts,
                note='Rows sample start-of-update RAM after aligned driver writes; state requested in prior update promotes in the upcoming update. CRAM reflects completed IRQ transfers. Contact hooks capture actual before/after velocities without driver overwrites.')


def top_runs(rom):
    runs=[]
    for track_x in (False,True):
        t=base.Thz3(rom);s,m,u=t.s,t.m,t.u
        sound=base.o50._sound_logger(s)
        initial={'at':None}
        def driver(n):
            b=t.boss()
            if not b:return
            if initial['at'] is None and m[b+1] in (3,18):
                s.w16(0xD511,1696);s.w16(0xD514,238);s.w16(0xD516,0);s.w16(0xD518,0)
            if initial['at'] is None and m[b+1]==6:
                initial['at']=n
                s.w16(0xD511,u(b+0x11));s.w16(0xD514,u(b+0x14)-47)
                s.w16(0xD516,0);s.w16(0xD518,256)
                m[0xD503]=3;m[0xD502]=10
            elif track_x and initial['at'] is not None:
                # Only X is synthetic; Y/state/attack/gravity/contact run freely.
                s.w16(0xD511,u(b+0x11));s.w16(0xD516,0)
        def sample():
            r=t.sample_boss()
            r.update(vy=base.s16(u(0xD518)),flags=m[0xD503],floor=m[0xD522],req=m[0xD502],
                     signed_y=base.s16(u(0xD514)),sound=m[0xDE04])
            return r
        rows=t.al.run(driver,sample,480,pad=lambda n:base.psc.PAD['RIGHT'] if n<75 else 0,restore=False)
        at=initial['at']
        rows=rows[at:]
        bounces=[i for i in range(1,len(rows)) if rows[i]['vy']<0 and rows[i-1]['vy']>=0 and rows[i]['req']==11]
        runs.append(dict(track_x_only=track_x,initial_update=at,bounce_updates=bounces,
                         minimum_signed_y=min(r['signed_y'] for r in rows),
                         minimum_screen_y=min(r['signed_y']-r['cam_y'] for r in rows),
                         rows=[dict(update=i,**r) for i,r in enumerate(rows)],sounds=[list(x) for x in sound]))
    return runs


def independence(rom):
    lab=base.BossLab(rom);rows=[]
    for phase,bvx,facing,region in itertools.product((0,1,255),(-512,0,512),(0,16),POINTS):
        case(lab,6,100,100,d503=3,vx=128,vy=768)
        lab.w(0x16,bvx&65535,2);lab.w(0x32,phase)
        lab.m[0xD504]=facing
        lab.o.position(lab.r(0x11,2)+POINTS[region][0],lab.r(0x14,2)+POINTS[region][1])
        lab.call_bank(30,0x99AE)
        rows.append(dict(phase=phase,boss_vx=bvx,player_facing_D504=facing,region=region,
                         player=player(lab),health=lab.r(0x26),cooldown=lab.r(0x1E)))
    return rows


def reaction_recontact(rom):
    rows=[]
    for st,region in itertools.product(STATES,('left','top')):
        lab=base.BossLab(rom)
        r=case(lab,st,*POINTS[region],d503=3)
        timeline=[dict(update=0,result=r)]
        for n in range(1,24):
            lab.o.position(lab.r(0x11,2)+POINTS[region][0],lab.r(0x14,2)+POINTS[region][1])
            lab.o.word(0xD518,256);lab.m[0xD503]=3;lab.m[0xD502]=0
            lab.step()
            timeline.append(dict(update=n,state=lab.r(1),requested=lab.r(2),health=lab.r(0x26),
                                 reaction=lab.r(0x1F),cooldown=lab.r(0x1E),player=player(lab)))
        rows.append(dict(state=st,region=region,timeline=timeline))
    return rows


def evidence(rom):
    regions=[('rebound',30,0x8105,0x814D),('contact',30,0x99AE,0x9A09),
             ('top_setter',1,0x480C,0x482D),('flash',29,0x83C6,0x83FE),
             ('damage_consumer',1,0x48BC,0x4A33),('state_reactions',30,0x9989,0x99AE),
             ('palette_consumer',14,0xB45A,0xB4AE),('palette_pointer',14,0xB63E,0xB650),
             ('cram_transfer',0,0x1CBD,0x1CD3),('command_dispatch',29,0x8000,0x8028),
             ('command_queue',0,0x1CD3,0x1CEB),('command_clear',0,0x1D06,0x1D14)]
    return [dict(name=n,bank=b,cpu_start=a,cpu_end=e,rom_offset=base.rom_of(b,a),
                 sha256=hashlib.sha256(rom[base.rom_of(b,a):base.rom_of(b,a)+e-a]).hexdigest()) for n,b,a,e in regions]


def build(rom):
    base.check_rom(rom)
    return dict(format=1,rom_sha256=base.ROM_SHA256,research_only=True,poc_untouched=True,
                supplements='data/rom-cache/thz3-boss-support.json',
                precise_rules=dict(vulnerable_states=list(STATES),
                    hit_response_8_8={'8':[-1536,'negate_incoming_vy'],'4':[1536,'negate_incoming_vy'],
                                     '2':['preserve_incoming_vx',1536]},
                    hit_requested_player_state=27,hit_preserves_movement_and_floor_flags=True,
                    top_nonrising_vy_8_8=-1024,top_requested_state=11,top_requires_attack=False,
                    harmful_contact_skipped_updates=[1,2],harmful_contact_next_active=3,
                    reaction_skipped_updates=list(range(1,21)),reaction_next_active=21,
                    entry_18_uses_contact_cooldown=False,entry_18_can_damage_boss=False,
                    flash_command=7,flash_sprite_palette_entries=[13,14],flash_cram_entries=[29,30],
                    flash_command_call_write_white=4,flash_command_call_restore=8,
                    flash_values=[63,63],restored_values=[53,32],hit_sound=182,
                    arena_clamp='unchanged canonical WORLD-space'),
                evidence=evidence(rom),response=response_sweep(rom),geometry=geometry_sweep(rom),
                immunity=immunity(rom),cooldown=cooldown(rom),progression=progression(rom),
                flash=flash(rom),aligned=entry_and_hit_trace(rom),top_runs=top_runs(rom),independence=independence(rom),
                reaction_recontact=reaction_recontact(rom))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('rom',type=Path);ap.add_argument('--check',action='store_true')
    args=ap.parse_args();data=build(args.rom.read_bytes())
    text=json.dumps(data,indent=1)+'\n'
    if args.check:
        assert json.loads(OUTPUT.read_text())==data,'cache mismatch'
        print('OK: focused follow-up matches verified ROM')
    else:
        with OUTPUT.open('w',encoding='utf-8',newline='\n') as out:
            out.write(text)
        print('wrote',OUTPUT,'response cases',data['response']['cases'],'geometry cases',data['geometry']['cases'])
    assert not data['response']['mismatches'],data['response']['mismatches'][:3]
    assert not data['geometry']['mismatches'],data['geometry']['mismatches'][:3]


if __name__=='__main__':main()

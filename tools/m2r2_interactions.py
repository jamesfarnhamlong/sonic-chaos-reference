"""Character interaction audit; private hash-gated ROM, metadata-only outputs."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import rom as R
import level_package as L
import g2e_score as G
import thz1_object_10 as M
from oracle import Oracle
from g0_rig import Session

def source(r):
    regions=[]
    for b,a,e in [(12,0xA149,0xA1F0),(12,0xA1F9,0xA22D),(0,0x4A74,0x4B46),(0,0x7C71,0x7CBB),
                  (30,0x8B64,0x8BE1),(0,0x178F,0x17B0),(0,0x613C,0x614E),
                  (12,0x9138,0x9163),(0,0x71A0,0x71B2),(0,0x7245,0x7257),
                  (12,0xA9A2,0xA9FA),(30,0xBB1A,0xBB2D)]:
        off=a if a<0x8000 else b*16384+a-0x8000
        regions.append(dict(bank=b,start=a,end=e,sha256=hashlib.sha256(r[off:off+e-a]).hexdigest(),instructions=G.disasm(r,b,a,e)))
    hits=[]
    for i in range(len(r)-2):
        if r[i:i+3] in (bytes.fromhex('3a00d5'),bytes.fromhex('3ac8d2')):
            hits.append(dict(rom_offset=i,bank=i//16384,cpu=i if i<32768 else 0x8000+i%16384))
    return dict(regions=regions,absolute_character_read_candidates=hits,
                scan_limit='Opcode candidates, not an exhaustive control-flow proof; indirect IX/type and table dispatch also reviewed.')

def placements(r):
    out=[]
    for z in list(range(6))+list(range(8,13)):
        for a in range(3):
            if z>=8 and a:continue
            for p in L.decode_object_list(r,L.object_list_pointer(r,z,a)['list_rom'])[0]:
                if p['type_id'] in ('0x10','0x2F'):
                    out.append(dict(zone=z,act=a,type=int(p['type_id'],16),parameter=int(p['parameter'],16),
                                    x=p['world_x'],y=p['world_y'],rom_offset=p['rom_offset'],aux0=p['aux0'],aux1=p['aux1']))
    return out

def controls(r):
    rows=[]
    for c in (1,2):
        for p in range(1,7):
            init=M.run_init_fixture(r,p,c);effective=int(init['parameter_after'],16)
            o=M._contact_oracle(r,parameter=effective);o.mem[0xD500]=c;o.mem[0xD2C8]=c
            o.mem[0xD299]=3;o.mem[0xD29A]=0x20;o.mem[0x062D]=0xC9
            o.mem[0xD726]=0x40;o.call(0xA16C)
            contact=M._contact_result(o);selector=o.mem[0xD3B3];queued=o.mem[0xD3A3]
            o.cpu.ix=0xD500;o.call(0x4AA3)
            reward=dict(rings=o.mem[0xD29A],lives=o.mem[0xD299],selector=o.mem[0xD532],
                        timer=o.word(0xD44C),requested=o.mem[0xD502],flags=o.mem[0xD503],clock=o.mem[0xD3C4])
            # Only selectors 1..6 use these 6-entry tables (parameter 0 is not a monitor).
            pointers=[]
            for base,n in ((0x7CBB if c==1 else 0x7CC7,192),(0x7CD3 if c==1 else 0x7CDF,128)):
                ptr=R.u16(r,base+2*effective);off=14*16384+ptr-0x8000
                pointers.append(dict(cpu=ptr,length=n,sha256=hashlib.sha256(r[off:off+n]).hexdigest()))
            rows.append(dict(character=c,placement_parameter=p,effective_parameter=effective,init=init,
                             graphics_selector=selector,art_layers=pointers,contact=contact,queued=queued,reward=reward))
            assert effective==(1 if c==2 and p==4 else p)
            assert selector==effective and queued==1<<(effective-1)
            assert contact['object_type_after']=='0x0F' and contact['placement_token_after']==0
            if effective==1: assert reward['rings']==0x30
            if effective==2: assert reward['lives']==4
            if effective==3: assert (reward['selector'],reward['timer'])==(3,900)
            if effective==4: assert (reward['selector'],reward['timer'],reward['requested'])==(4,300,17)
            if effective==5: assert reward['clock']==11
            if effective==6: assert (reward['selector'],reward['timer'])==(6,600)
    negative=[]
    for c in (1,2):
        for attack,vy,req,dy in [(0,256,5,-20),(2,-256,5,-20),(2,0,5,-20),(2,256,15,-20),(2,256,5,20)]:
            o=M._contact_oracle(r,player_flags=attack,player_y_velocity=vy,requested_state=req,delta_y=dy)
            o.mem[0xD500]=c;o.call(0xA16C)
            result=M._contact_result(o);assert result['object_type_after']=='0x10'
            negative.append(dict(character=c,attack=attack,vy=vy,requested=req,dy=dy,result=result))
    timers=[]
    for c in (1,2):
        for sel in (3,4,6):
            for t in (0,1,2):
                o=Oracle(r);o.mem[0xD500]=c;o.mem[0xD2C8]=c;o.mem[0xD532]=sel;o.word(0xD44C,t)
                o.call(0x4A74)
                timers.append(dict(character=c,selector_before=sel,timer_before=t,selector_after=o.mem[0xD532],timer_after=o.word(0xD44C),maximum=o.word(0xD373)))
                assert o.word(0xD44C)==(t-1)&65535
                assert o.mem[0xD532]==(0 if t==1 and sel in (4,6) else sel)
    forced=[]
    for c in (1,2):
        o=Oracle(r);o.mem[0x062D]=0xC9;o.mem[0xD500]=c;o.mem[0xD3A3]=8;o.call(0x4AA3)
        forced.append(dict(character=c,queue=o.mem[0xD3A3],selector=o.mem[0xD532],request=o.mem[0xD502]))
        assert o.mem[0xD532]==(4 if c==1 else 0)
    shoes=[]
    for c in (1,2):
        for dy in (-16,80):
            o=Oracle(r);o.bank(2,30);o.mem[0xD12B]=30;o.cpu.ix=0xD700
            o.mem[0xD700]=47;o.mem[0xD703]=128;o.mem[0xD72C]=8;o.mem[0xD72D]=16
            o.mem[0xD500]=c;o.mem[0xD501]=o.mem[0xD502]=14;o.mem[0xD52C]=8;o.mem[0xD52D]=24
            o.word(0xD711,500);o.word(0xD714,500);o.word(0xD511,500);o.word(0xD514,500+dy);o.word(0xD518,256)
            o.call(0x8B64)
            shoes.append(dict(character=c,dy=dy,requested=o.mem[0xD502],owner=o.word(0xD3A4),shoe_request=o.mem[0xD702]))
            assert o.mem[0xD502]==(18 if dy==-16 else 14)
    import u3_sign_prizes as U
    sign=[]
    for c in (1,2):
        rig=U.Oracle3(r)
        for z in range(6):
            for rings in (0x01,0x09,0x15,0x16,0x24,0x55,0x99):
                sign.append(dict(character=c,zone=z,rings_before=rings,result=rig.landing(z,c,rings,0,0,3,0)))
    extra=[]
    for c in (1,2):
        for value in (0x98,0x99):
            o=Oracle(r);o.mem[0xD500]=c;o.mem[0xD299]=value;o.call(0x3104)
            extra.append(dict(character=c,lives_before=value,lives_after=o.mem[0xD299]))
            assert o.mem[0xD299]==0x99
    wraps=[]
    for c in (1,2):
        o=Oracle(r);o.mem[0xD500]=c;o.mem[0xD2C8]=c;o.mem[0xD29A]=0x95;o.mem[0xD299]=3;o.mem[0xD3A3]=1
        o.call(0x4AA3)
        wraps.append(dict(character=c,rings=o.mem[0xD29A],lives=o.mem[0xD299],mode=o.mem[0xD294],card=o.mem[0xD2CD]))
        assert o.mem[0xD29A]==5 and o.mem[0xD299]==4 and o.mem[0xD294]==(0x88 if c==1 else 0)
    animation=[]
    for c in (1,2):
        for state in (17,18):
            o=Oracle(r);o.bank(2,12);o.mem[0xD500]=c;o.mem[0xD501]=o.mem[0xD502]=state;o.word(0xD50E,0)
            o.call(0x64FA)
            animation.append(dict(character=c,state=state,frame=o.mem[0xD506],callback=o.word(0xD50C),requested=o.mem[0xD502],extent=[o.mem[0xD52C],o.mem[0xD52D]]))
    carrier=[]
    for c in (1,2):
        for velocity in (256,65280):
            o=Oracle(r);o.bank(2,12);o.mem[0xD500]=c;o.word(0xD516,velocity);o.call(0x9138)
            carrier.append(dict(character=c,vx=velocity,frame=o.mem[0xD506],duration=o.mem[0xD507]))
            assert o.mem[0xD506] in ((0x5F,0x60) if c==1 else (0x56,0x57))
    cancel=[]
    for c in (1,2):
        for state in (5,24):
            o=Oracle(r);o.mem[0xD500]=c;o.mem[0xD502]=state;o.call(0x613C)
            cancel.append(dict(character=c,requested_before=state,requested_after=o.mem[0xD502]))
            assert o.mem[0xD502]==(14 if c==2 and state==24 else state)
    return dict(monitors=rows,negative_contact=negative,timer_edges=timers,forced_rocket_reward=forced,spring_attachment=shoes,
                sign_rewards=sign,life_cap=extra,ring_wrap=wraps,equipment_animation=animation,carrier_animation=carrier,flight_contact_cancel=cancel)

def gameplay(r,c,arrival=False):
    ses=Session(r);events=[]
    def event(name):
        def f(s):
            if s.slot[2]!=12 and name not in ('reward','art','ring_awarded','rocket_setup'):return
            a=s.cpu.ix
            if name not in ('reward','art','ring_awarded','rocket_setup') and s.mem[a]!=16:return
            events.append(dict(event=name,frame=s.frame,slot=a,parameter=s.mem[a+63] if name!='reward' else None,
                               x=s.u16(0xD511),y=s.u16(0xD514),state=s.mem[0xD501],
                               queue=s.mem[0xD3A3],rings=s.mem[0xD29A],selector=s.mem[0xD3B3],power=s.mem[0xD532]))
        return f
    for pc,name in [(0xA149,'init_before'),(0xA161,'init_after'),(0xA1D3,'break'),(0x4AA3,'reward'),(0x7C71,'art'),(0x4ACB,'ring_awarded'),(0x4775,'rocket_setup')]:ses.hook(pc,event(name))
    def place(s):
        s.w16(0xD2D6,208);s.w16(0xD2D8,152)
        s.w16(0xD511,336);s.w16(0xD514,220)
    ses.boot_new_game(character=c-1,settle=0,arrival=place if arrival else None)
    start=ses.s.frame
    for i in range(500):
        # Ordinary input-only route from authentic THZ1 start; no RAM/arrival fixtures.
        x=ses.u16(0xD511)
        ses.run(1,(16 if i in (60,150,240,330) else 0) if arrival else 8 | (16 if 250<x<350 else 0))
        if any(e['event']=='break' for e in events) and i>180:break
    # Omit empty per-update dispatch calls, retain only queued rewards and transitions.
    events=[e for e in events if e['event']!='reward' or e['queue']]
    return dict(character=c,evidence='ROM gameplay proven (arrival-assisted, approximate SMS harness)' if any(e['event']=='break' for e in events) else 'unresolved input-only break',
                setup='ARRIVAL camera (208,152), player (336,220), then Button1 taps at 60/150/240/330; no object/state/VDP/PC injection' if arrival else 'normal new game; input-only Right, Button1 while X 251..349; no RAM writes',elapsed=ses.s.frame-start,events=events,end=ses.snap())

def shoe_gameplay(r,c):
    ses=Session(r);ses.set_start_index(2,0)
    def arrival(s):
        s.w16(0xD2D6,96);s.w16(0xD2D8,280);s.w16(0xD511,224);s.w16(0xD514,348)
    ses.boot_new_game(character=c-1,arrival=arrival)
    rows=[];last=None
    for i in range(300):
        ses.run(1,16 if i==180 else 0)
        m=ses.m;owner=ses.u16(0xD3A4)
        row=dict(step=i,state=m[0xD501],requested=m[0xD502],frame=m[0xD506],owner=owner,
                 shoe_state=m[owner+1] if 0xD540<=owner<0xDB80 else None,
                 shoe_frame=m[owner+6] if 0xD540<=owner<0xDB80 else None,
                 vy=ses.u16(0xD518),extent=[m[0xD52C],m[0xD52D]])
        key=(row['state'],row['requested'],row['frame'],row['shoe_state'],row['shoe_frame'])
        if key!=last:rows.append(row);last=key
    assert any(x['state']==18 for x in rows)
    assert any(x['step']>=180 and x['requested']==10 for x in rows)
    return dict(character=c,evidence='ROM gameplay proven (arrival-assisted, approximate SMS harness)',
                setup='START_INDEX SEZ1; ARRIVAL camera(96,280),player(224,348); no object/state injection; Button1 at step180',rows=rows,end=ses.snap())

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--gameplay',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    r=R.load(a.rom)
    out=dict(schema_version=1,rom_sha256=R.SHA256,baseline='d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98',source=source(r),placements=placements(r),controls=controls(r))
    dest=ROOT/'data/m2r2/evidence.json';dest.parent.mkdir(parents=True,exist_ok=True)
    if a.gameplay:
        out['gameplay']=[]
        for c in (1,2):
            for arrival in (False,True):
                print('gameplay character',c,'arrival',arrival,flush=True);out['gameplay'].append(gameplay(r,c,arrival))
        out['spring_gameplay']=[shoe_gameplay(r,c) for c in (1,2)]
    elif dest.exists():out['gameplay']=json.loads(dest.read_text()).get('gameplay',[])
    if not a.gameplay and dest.exists():out['spring_gameplay']=json.loads(dest.read_text()).get('spring_gameplay',[])
    text=json.dumps(out,indent=2)+'\n'
    if a.check:assert dest.read_text()==text
    else:dest.write_text(text)
    print('M2-R2 metadata checks passed',flush=True)
if __name__=='__main__':main()

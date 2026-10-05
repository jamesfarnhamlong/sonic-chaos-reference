"""Focused original-Z80 regression oracles for the reviewed $56 package errors."""
import hashlib
import itertools
import json
import rom as R
import mghz_object_24_2e as Q
import viewport_semantics as V


def build(r, B):
    sources=[]
    for name,bank,start,end in (
        ('warning_contact',30,0xA77F,0xA783),('selector',30,0xA613,0xA62D),
        ('selector_flags',30,0xA69F,0xA6B8),('clear_release',30,0x81F4,0x8212),
        ('camera_update',1,0x4C90,0x4CB0),('camera_limits',1,0x4CB0,0x4CF7),
        ('camera_follow',1,0x5832,0x5956),('follow_enable',1,0x59D8,0x59E3),
        ('update_order',0,0x16B8,0x16EF),('irq_counter_increment',0,0x0603,0x0607),
        ('counter_reset',0,0x0759,0x075D)):
        sources.append(dict(name=name,bank=bank,file=Q.file_of(bank,start),
                            instructions=Q.disasm(r,bank,start,end)))
    assert r[Q.file_of(30,0xA77F):Q.file_of(30,0xA783)]==bytes.fromhex('cd3404c9')
    checks=1
    lab=B.Lab(r);o,m=lab.o,lab.m;s=B.SLOT
    selector=[]
    # Exhaustive player 16-bit Y for each requested body/velocity boundary.
    digest=hashlib.sha256();counts={6:0,7:0}
    for by,vy in itertools.product((429,430,431),(-1,0,1)):
        o.word(s+20,by);o.word(s+24,vy)
        lab.call(0xA69F)
        z=bool(o.cpu.f&64);a=o.cpu.a
        assert z==(vy>=0 and by==430);checks+=1
        for py in range(65536):
            o.word(0xD514,py);lab.call(0xA613)
            expected=6 if py<by or (vy>=0 and by==430) else 7
            assert m[s+2]==expected,(py,by,vy,m[s+2]);checks+=1
            counts[expected]+=1;digest.update(bytes((m[s+2],)))
            if py in (by-1,by,by+1):
                selector.append(dict(player_y=py,body_y=by,body_vy=vy,helper_a=a,helper_z=z,requested=m[s+2]))
    warning=[]
    for parameter,attack,hurt,inv,power in itertools.product((0,1),(0,2),(0,64),(0,128),(0,6)):
        lab=B.Lab(r);o,m=lab.o,lab.m
        m[s:s+64]=bytes(64);m[s]=87;m[s+2]=1;m[s+4]=2;m[s+63]=parameter
        o.word(s+17,3200);o.word(s+20,350)
        lab.step() # blank state00 visit, successor requests warning01
        rows=[]
        for call in range(1,25):
            o.position(3200,350);m[0xD503]=attack|hurt|inv;m[0xD532]=power
            m[0xD501]=m[0xD502]=5;m[0xD522]=0;m[0xD29A]=0x47
            m[0xD3B0]=m[0xD520]=m[0xD521]=0;m[0xD3B1]=0
            lab.step()
            pending=m[0xD3B0]
            assert m[s+1]==1 and m[s+6]==(14 if (call-1)%8<4 else 13)
            assert [m[s+44],m[s+45]]==[4,16]
            assert bool(pending)==(not hurt)
            assert [o.word(s+17),o.word(s+20)]==[3200,350] and m[s]==87
            checks+=4
            o.cpu.ix=0xD500;o.call(0x48BC)
            rings=m[0xD29A]
            assert rings==(0 if not (hurt or inv or power==6) else 0x47);checks+=1
            rows.append(dict(call=call,frame=m[s+6],timer=m[s+7],counter=m[0xD12F],callback_counter=lab.scheduler_counter,
                             pending=pending,rings_after_consumer=rings,player=B.player(o)))
        warning.append(dict(parameter=parameter,attack=attack,hurt=hurt,inv=inv,power=power,rows=rows))
    geometry=[]
    for frame,ex in itertools.product((13,14),(8,9)):
        for dx,dy in itertools.product(range(-15,16),range(-18,27)):
            B.prepare(lab,dx,dy,frame=frame,type_id=87)
            m[s+3]=0;m[0xD52C]=ex;m[0xD3B0]=m[0xD520]=m[0xD521]=0
            lab.call(0xA77F)
            expected=abs(dx)<=ex+4 and -16<=dy<=24
            assert bool(m[0xD3B0])==expected;checks+=1
        geometry.append(dict(frame=frame,sonic_extent_x=ex,x_inclusive=[-ex-4,ex+4],y_inclusive=[-16,24]))
    camera=[]
    lab=B.Lab(r);o,m=lab.o,lab.m
    for cam,lead,left_facing,k,vx in itertools.product(
            (2954,2961,3060,3576,3583),(104,120,136),(0,1),range(256),(-1536,0,1536)):
        o.word(0xD174,cam);o.word(0xD284,cam);o.word(0xD176,256);o.word(0xD286,256)
        o.word(0xD280,2954);o.word(0xD282,3061)
        m[s]=86;m[s+1]=m[s+2]=5;m[s+37]=14;m[s+39]=0
        m[0xD15E]=128;m[0xD15F]=1;m[0xD522]=0
        m[0xD504]=16 if left_facing else 0
        m[0xD28A]=lead;m[0xD28B]=lead+8;m[0xD28C]=lead-8
        m[0xD289]=m[0xD28D]=120;m[0xD28E]=136;m[0xD28F]=104
        o.position(cam+k,376);o.word(0xD516,vx)
        lab.call(0x81BD)
        assert o.word(0xD280)==2954 and o.word(0xD282)==3584 and m[0xD15F]&1==0;checks+=1
        o.cpu.ix=0xD15E;o.call(0x5832)
        newlead=lead+(1 if lead<(136 if left_facing else 104) else -1 if lead>(136 if left_facing else 104) else 0)
        delta=V.follow_delta_x(k,newlead) if k else 0
        assert R.s16(o.word(0xD284)-cam)==delta;checks+=1
        o.call(0x4CB0)
        expected=cam+delta if 2954<=cam+delta<3584 else cam
        assert o.word(0xD284)==expected;checks+=1
        if vx==0 and k in (0,95,96,104,112,120,128,136,144,200,255):
            camera.append(dict(camera=cam,lead=lead,facing_left=left_facing,screen_x_low=k,
                               next_lead=newlead,candidate_delta=delta,limited_candidate=expected))
    return dict(assertions=checks,reconciliation_base='badba9d085906054e4f15fa1d1a960ca2ae0abdd',
        sources=sources,
        selector=dict(condition={'state06':{'any':[{'unsigned_player_y_lt_body_y':True},
                {'all':[{'signed_body_vy_ge':0},{'body_world_y_eq':430}]}]},'otherwise':7},
            sweep_player_y=[0,65535],body_y=[429,430,431],body_vy=[-1,0,1],
            counts={str(k):v for k,v in counts.items()},sha256=digest.hexdigest(),boundaries=selector),
        warning=dict(callback_cpu=0xA77F,contact_vector=0x0434,calls=24,rows=warning,geometry=geometry,
            timing='Camera then player/hurt consumer then ascending object scheduler. Each warning call queues overlap damage; player consumes it next update. Blank state00 has no contact; warning starts on next slot visit. Warning has no movement.'),
        camera=dict(routine=0x5832,enable_vector=0x035C,lead_right=104,lead_left=136,lead_slew=1,
            deadzone_half_width=8,max_right_step=7,max_left_step=-7,exact_minus8_preserved=True,
            saved_right=3584,retained_left_fixture=2954,limit_rule='retained D280 <= candidate < restored D282; reject overshoot, do not clamp to boundary',
            begins='State05 callback disables pan/restores right limit before testing WORLD playerX>=3356 and grounded. Camera phase has already run; follow resumes next update, even if clear gate is false.',
            speed_dependency='Position error and working lead; no player velocity read or min(player speed) cap',rows=camera))

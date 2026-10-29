"""Independent original gameplay-writer schedules and full-state epoch probes.

Controlled routine execution, with inherited frame-wait stub; no natural route.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import m5g1r as G
import audio1_psg_trace as T

def mapgame(d):d.mem[0x4000:0x8000]=d.rom[0x4000:0x8000]
def mapsound(d):
    for slot,bank in T.SOUND_BANKS:d.mem[slot*0x4000:(slot+1)*0x4000]=d.rom[bank*0x4000:(bank+1)*0x4000]

def writers(rom):
    reports={};schedules={}
    for name,zone,bit,sneakers in [('inv',0,5,False),('inv-sneakers',0,5,True),('rocket',0,3,False),('ss1-rocket',8,3,False),('ss4-rocket',11,3,False)]:
        d=T.Driver(rom);d.mem[0x062D]=0xC9 # inherited controlled wait stub, NOT gameplay timing
        d.mem[0xD297]=zone;d.mem[0xD298]=0;d.mem[0xD500]=1;d.mem[0xD2C8]=1;d.cpu.ix=0xD500
        initial=0x8F if zone>=8 else 0x81;d.request(initial);events={};writes=[];inactive=None;prior=0;expiry=None
        for t in range(1,1501):
            mapgame(d);d.cpu.ix=0xD500 # re-establish caller's player context after driver IX use
            if t==30:d.mem[0xD3A3]=1<<bit
            if sneakers and t==130:d.mem[0xD3A3]=4
            before=d.mem[0xD532];d.call(0x4A74)
            if before and not d.mem[0xD532]:expiry=t
            direct=d.mem[0xDE04];deferred=d.mem[0xD4A4]
            if deferred:d.mem[0xDE04]=deferred;d.mem[0xD4A4]=0
            delivered=d.mem[0xDE04]
            if t>1 and (direct or deferred):
                events[str(t)]=[['request',delivered]];writes.append(dict(tick=t,direct=direct,deferred=deferred,delivered=delivered))
            mapsound(d);d.tick()
            if t>30 and inactive is None and not d.music_active():inactive=t
        schedules['writer-'+name]=dict(initial=initial,events=events,ticks=1500,group='original-writer-power')
        reports[name]=dict(zone=zone,queue_bit=bit,sneakers_tick=130 if sneakers else None,writes=writes,selector_expiry_tick=expiry,first_music_inactive=inactive,final_selector=d.mem[0xD532],final_timer=d.mem[0xD44C]|d.mem[0xD44D]<<8,controlled=True,frame_wait_stubbed=True)
    # Execute UpdateMusic for every required zone/act and suppression value.
    table=[]
    for zone,act in [(z,0) for z in range(6)]+[(5,2),(7,0)]+[(z,0) for z in range(8,13)]:
        for gate in (0,1,255):
            d=T.Driver(rom);d.mem[0xD297]=zone;d.mem[0xD298]=act;d.mem[0xD4A3]=gate;d.call(0x189B)
            table.append(dict(zone=zone,act=act,gate=gate,direct=d.mem[0xDE04],deferred=d.mem[0xD4A4]))
    G.save(G.OUT/'writer-schedules.json',schedules)
    G.save(G.PUB/'writer-schedules.json',schedules)
    G.save(G.PUB/'writers.json',dict(power_cases=reports,level_writer=table,source_hashes={f'{a:04X}-{b:04X}':G.sha(rom[a:b]) for a,b in [(0x189B,0x18BA),(0x18E1,0x18ED),(0x4A74,0x4B33),(0x4787,0x4797),(0x2846,0x285D)]},natural_route=False))

def epochs(rom):
    from m5c71.research import key
    from backend import PSG
    from m5c71r83.pcm import DLL
    import numpy as np
    reports={}
    for rid in G.MUSIC:
        a=T.Driver(rom);a.request(rid);solo=T.Driver(rom);solo.request(rid)
        histories={};first_rejoin=None;last_bad=None;diffsamples=0;writes_bad=state_bad=ram_bad=iy_bad=0
        with PSG(DLL) as persistent,PSG(DLL) as fresh:
            for t in range(1,5251):
                if t==30:a.request(0xBA)
                if t==250:a.request(rid)
                start=len(a.writes);a.tick();ports=[v for _,v in a.writes[start:]]
                persistent.write(ports);audio=persistent.render()
                if t<250:
                    solo.tick()
                    if t>=30 and key(a)==key(solo) and first_rejoin is None:first_rejoin=t
                else:
                    if t==250:solo=T.Driver(rom);solo.request(rid)
                    st=len(solo.writes);solo.tick();sp=[v for _,v in solo.writes[st:]]
                    different=key(a)!=key(solo);state_bad+=different;writes_bad+=ports!=sp
                    if different:last_bad=t-249
                    ram_bad+=bytes(a.mem[0xDE00:0xDF90])!=bytes(solo.mem[0xDE00:0xDF90]);iy_bad+=a.cpu.iy!=solo.cpu.iy
                    fresh.write(sp);ref=fresh.render();diffsamples+=int(np.count_nonzero(audio!=ref))
                    if t in (250,500,1000,4450,5250):histories[str(t-249)]=G.sha(key(a))
        # A new original driver epoch is deterministic for5001 updates; physical
        # PSG phase remains independent and MUST NOT be reset by the host.
        reports[f'{rid:02X}']=dict(pre_reset_first_full_state_rejoin=first_rejoin,reset_at=250,post_reset_compared_ticks=5001,full400_IY_logical_PSG_mismatching_ticks=state_bad,last_full_state_mismatch_epoch_tick=last_bad,driver400_mismatching_ticks=ram_bad,IY_mismatching_ticks=iy_bad,ordered_write_mismatching_ticks=writes_bad,persistent_vs_fresh_chip_PCM_differing_samples=diffsamples,epoch_checkpoints=histories)
        assert not ram_bad and not iy_bad and not writes_bad,(rid,reports[f'{rid:02X}'])
    G.save(G.PUB/'epochs.json',dict(cases=reports,solo_certificate_reused=False,new_candidate_epoch_implemented=False))

if __name__=='__main__':
    rom=T.load_rom(sys.argv[1]);writers(rom);epochs(rom)

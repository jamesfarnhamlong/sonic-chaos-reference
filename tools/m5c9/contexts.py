"""Controlled original90 writer/lifecycle contexts; no natural-scene timing claim."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
import audio1_psg_trace as T
from m5c9.original import capture,OUT,PUB,load,save,sha,canonical
CASES={
 '90-opening-fade':(0x90,{745:[('fade',[12,1,2])],800:[('request',0x99)]},1100,(7,0)),
 '90-eez3-retrigger':(0x90,{2472:[('request',0x90)]},3000,(5,2)),
}

def original(path):
    rom=T.load_rom(path);cases=[]
    for label,z,a in (('opening',7,0),('EEZ3',5,2)):
        for gate in (0,1,255):
            d=T.Driver(rom);d.mem[0xD297]=z;d.mem[0xD298]=a;d.mem[0xD4A3]=gate
            d.mem[0xDE04]=0;d.mem[0xD4A4]=0;d.call(0x189B)
            expected=0x90 if gate==0 else 0
            assert d.mem[0xDE04]==expected and d.mem[0xD4A4]==expected
            cases.append(dict(context=label,zone=z,act=a,D4A3=gate,request_written=expected,writer=0x189B,table_address=0x18BA+3*z+a))
    save(PUB/'90-contexts.json',dict(writer_cases=cases,writer_instruction_sha256=sha(rom[0x189B:0x18BA]),prior_source_crosswalk='data/m5/catalogue.json:90; docs/m5-driver-integration-contract.md; tools/u5a_opening.py',opening='controlled zone7/act0 writer plus inherited745 fade fixture and99 replacement; not full cinematic execution',EEZ3='controlled zone5/act2 writer and same-ID retrigger; uninterrupted full composition independently certified',natural_scene_timing_qualified=False,short_M4_PCM_used=False))
    for name,(rid,events,end,writer) in CASES.items():capture(rom,rid,name,events,end,False,writer)

def candidate():
    from m5c9.verify import verify
    for name,(rid,events,end,writer) in CASES.items():verify(name,rid,'90.scsp',events)

if __name__=='__main__':
    original(sys.argv[2]) if sys.argv[1]=='original' else candidate()

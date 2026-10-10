"""Original zone5 scheduler fixtures from canonical mapped creation records.

Only initial placement records and boundary player/camera inputs are supplied.
Callbacks, movement, animation, child allocation and contact run original code.
"""
import argparse,json
import eez_foundation as F
import level_package as L
from sez_surfaces_rig import ZoneGame

def build(r):
    census=json.loads((F.OUT/'object-census.json').read_text());cases=[]
    for t,param,n in [(23,2,400),(54,None,300),(56,0,180),(56,1,300)]:
        key,rec=next((k,x) for k,a in census['acts'].items() for x in a['records'] if int(x['type_id'],16)==t and (param is None or int(x['parameter'],16)==param))
        act=int(key[-1])-1;g=ZoneGame(r,5,act,hooks={0x16D0:'after_player',0x16D3:'after_objects'})
        s,m=g.s,g.m;cpu=bytes(s.cpu.get_state_view());S=0xD540
        def restore():g.e.restore();s.cpu.get_state_view()[:]=cpu
        g.restore_snapshot=restore
        x,y=rec['world_x'],rec['world_y'];events=[];previous=[None];oldengine=g._engine_hook
        def engine(mm):
            oldengine(mm)
            if not g.recording or mm.cpu.ix!=0xD500:return
            # Keep fixture camera stable so generic wake/deletion stays visible.
            s.w16(0xD174,max(0,x-112));s.w16(0xD176,max(8,y-100))
            if t!=23:
                target=next((b for b in range(0xD540,0xDA00,64) if m[b]==56 and m[b+63]!=1),S)
                s.w16(0xD511,s.u16(target+17) if m[target] in (54,56) else x)
                s.w16(0xD514,(s.u16(target+20) if m[target] in (54,56) else y)-16)
                s.w16(0xD516,0);s.w16(0xD518,0);m[0xD501]=m[0xD502]=14;m[0xD503]=128;m[0xD3B0]=0;m[0xD522]=0
        g.hook(0x64FA,engine)
        def observe(mm):
            if not g.recording:return
            row=dict(player=[m[0xD501],m[0xD502],s.u16(0xD511),s.u16(0xD514),s.u16(0xD3A6)],
                     actors=g.objs((23,54,55,56,57,15)),score=list(m[0xD29D:0xD2A0]))
            signature=F.dumps(row)
            if signature!=previous[0]:events.append(dict(u=len(g.rows),**row));previous[0]=signature
        g.hook(0x16D3,observe)
        def setup(q):
            m[0xD540:0xDA00]=bytes(0x4C0);b=rec['original_creator'];m[S]=t;m[S+4]=b['flags'];m[S+8:S+10]=bytes(b['art_bases']);m[S+62]=b['token'];m[S+63]=b['parameter']
            s.w16(S+17,x);s.w16(S+20,y);s.w16(S+58,x)
            # Occupancy marks all canonical records allocated, avoiding fixture
            # duplicate actors; does not alter the actor's release token.
            m[0xD400:0xD440]=bytes([255])*64
            s.w16(0xD174,max(0,x-112));s.w16(0xD176,max(8,y-100))
        g.begin(x,y-16,cur=14,f3=2,floor=False,apply=setup,types=(23,54,55,56,57,15))
        rows=g.run(n,padf=lambda u,f:16 if t==23 and 40<=u<43 else 0)
        states=sorted({(a['type'],a['state']) for e in events for a in e['actors']})
        assert len(rows)>=n,(t,len(rows),n)
        if t==23:
            assert {22,23} <= {e['player'][0] for e in events}
            assert any(e['player'][4] for e in events) and any(e['u']>50 and not e['player'][4] for e in events)
        elif t==54:assert {(54,3),(55,1),(55,2)}<=set(states)
        elif param==0:assert any(e['score'][0] for e in events) and any(a['type']==57 for e in events for a in e['actors'])
        else:assert {(56,4),(56,5),(56,6)}<=set(states)
        cases.append(dict(type=t,parameter=rec['parameter'],placement=rec['rom_offset'],method=__doc__,updates=len(rows),states=states,events=events))
        print(t,rec['parameter'],states,sorted({e['player'][0] for e in events}),cases[-1]['events'][-1]['score'])
    return dict(rom_sha256=L.ROM_SHA256,assertions=9,cases=cases,
                player_fixture='Carrier uses one initial placement and button16 on updates40..42. Others hold immune Sonic at producer/child contact at every player boundary; objects untouched. No claim of input-only natural play.')

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();v=build(L.load_rom(a.rom));(F.OUT/'system-game-checks.json').write_text(F.dumps(v),encoding='utf-8')

if __name__=='__main__':main()

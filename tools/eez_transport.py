"""State21 transport route selectors, original-ROM boundary sweeps."""
import argparse,itertools
import eez_foundation as F
import level_package as L
from oracle import Oracle

def model(block,x,y,vx,vy,pad):
    xh=(vx>>8)&255;yh=(vy>>8)&255
    left=x%32<14;right=not left;up=y%32<14;down=((y-14)&31)>=20
    route=None
    if block in (0x74,0x81,0x82):route='snapY'
    elif block in (0x75,0x7F,0x80,0x83):route='snapX'
    elif block==0x7A:
        if xh:
            if (left if xh&128 else right):route='up' if pad&1 else 'left' if xh&128 else 'right'
        elif down:route='right' if pad&8 else 'left' if pad&4 else 'up'
    elif block==0x7B:
        if xh:
            if (left if xh&128 else right):route='down' if pad&2 else 'left' if xh&128 else 'right'
        elif up:route='right' if pad&8 else 'left' if pad&4 else 'down'
    elif block==0x7D:
        if not xh:
            if (up if yh&128 else down):route='left' if pad&4 else 'up' if yh&128 else 'down'
        elif right:route='up' if pad&1 else 'down' if pad&2 else 'left'
    elif block==0x7C:
        if not xh:
            if (up if yh&128 else down):route='right' if pad&8 else 'up' if yh&128 else 'down'
        elif left:route='up' if pad&1 else 'down' if pad&2 else 'right'
    elif block==0x79:
        if not xh and up:route='right'
        elif xh and left:route='down'
    elif block==0x78:
        if not xh and up:route='left'
        elif xh and right:route='down'
    elif block==0x77:
        if not xh and down:route='right'
        elif xh and left:route='up'
    elif block==0x76:
        if not xh and down:route='left'
        elif xh and right:route='up'
    latch=0
    if route:
        latch=255
        if route in ('snapX','down','up'):x=(x&0xFFE0)+14
        else:y=(((y-16)&65535)&0xFFE0)+44;y&=65535
        if route in ('left','right'):vx=-1536 if route=='left' else 1536;vy=0
        elif route in ('up','down'):vy=-1536 if route=='up' else 1536;vx=0
    return [x,y,vx&65535,vy&65535,latch]

def build(r):
    o=Oracle(r);o.bank(2,12);m=o.mem;o.cpu.ix=0xD500
    table=[int.from_bytes(r[0x311BC+2*i:0x311BE+2*i],'little') for i in range(16)]
    o.cpu.set_breakpoint(0x91DC);count=0;rows=[]
    for block,x,y,vel,pad in itertools.product(range(0x74,0x84),(0,13,14,15,31),(0,1,13,14,15,16,31),((-1536,0),(1536,0),(0,-1536),(0,1536),(64,0)),range(16)):
        vx,vy=vel;o.position(256+x,256+y);o.word(0xD516,vx);o.word(0xD518,vy);m[0xD137]=pad;m[0xD3C6]=0
        o.cpu.pc=table[block-0x74];o.cpu.sp=0xDFE0;o.word(o.cpu.sp,o.RETURN)
        for _ in range(20):
            o.cpu.ticks_to_stop=100000;o.cpu.run()
            if o.cpu.pc==0x91DC:break
        assert o.cpu.pc==0x91DC,(block,o.cpu.pc)
        actual=[o.word(0xD511),o.word(0xD514),o.word(0xD516),o.word(0xD518),m[0xD3C6]]
        expected=model(block,256+x,256+y,vx,vy,pad)
        assert actual==expected,(block,x,y,vx,vy,pad,actual,expected)
        count+=1
        if x==14 and y==14:rows.append([block,vx,vy,pad,actual])
    return dict(rom_sha256=L.ROM_SHA256,checks=count,table_cpu=0x91BC,table_file=0x311BC,table=table,
        evidence='original route handlers stopped at common move tail91DC; selector conditions independently modeled',
        region=F.A.source(r,12,0x916B,0x94C1),vectors=rows,
        semantics=dict(dispatch='state21 callback916B: hurt0416,clear hide4bit7,set D15Fbit1; reset D3C6 if floor block changes; current floor block74..83 then prior marker D36D; out of range exits.',
            latch='D3C6 prevents repeated route choice while same current floor block; fallback prior-block dispatch still evaluates.',
            exit='D373=0600; if Vy high bit7 then Vy=F980 (-6.5); soundBA; clear hurtrequestD3B0/contact21; JP03BF (ordinary state setter).',
            coordinates='all tube alignment and routing are WORLD; X snap (X&~31)+14, Y snap ((Y-16)&~31)+44; no viewport widening.',
            movement='route tail0338 moves before038C; callback skips ordinary terrain pass; initial surface handler and state21 execution occur on different updates.',
            inputs='pad bits0/1/2/3 Up/Down/Left/Right. Junction choices use signed high-byte velocity rather than exact zero; low positive fractions behave as high-byte0.',
            presentation='state21 records25..29 from table840F; frame duration3; state21 callback916B. Exact frame list retained in foundation player-state dependency, no added animation.'))

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();v=build(L.load_rom(a.rom))
    (F.OUT/'transport-state21.json').write_text(F.dumps(v),encoding='utf-8');print('route checks',v['checks'])

if __name__=='__main__':main()

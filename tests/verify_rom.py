"""Differential checks against original Z80 instructions, with explicit RAM fixtures."""
import argparse, csv, json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from rom import load, layout, SHA256, s16
from oracle import Oracle
from reference import lookup, project_floor, project_side, angle_velocity

def verify(path, output):
    rom = load(path); tiles = layout(rom); o = Oracle(rom)
    counts = dict(lookup=0, floor=0, side=0, angle_velocity=0, gravity=0, ramp_launch=0, layout_decoder=0)
    loader=Oracle(rom);loader.bank(2,18)
    loader.mem[0xc001:0xd000]=bytes(4095);loader.mem[0xd000]=0xa5
    loader.cpu.iy=0x8000;loader.cpu.de=0xc001;loader.cpu.pc=0x4dc4
    loader.cpu.set_breakpoint(0x4dfb)
    for _ in range(20):
        loader.cpu.ticks_to_stop=100000;loader.cpu.run()
        if loader.cpu.pc==0x4dfb:break
    assert loader.cpu.pc==0x4dfb and loader.cpu.de==0xd000
    assert bytes(loader.mem[0xc001:0xd000])==bytes(tiles)
    assert loader.mem[0xd000]==0xa5
    counts['layout_decoder']=1
    # Every tile and profile index; both collision planes. The fixture puts
    # each tile at (320,320), exercising the original header-selection logic.
    index = 10*128+10
    for tile in range(256):
        tiles[index] = tile; o.mem[0xc001+index] = tile
        for plane in (0,1):
            for phase in range(32):
                x,y = 320+phase,320+((phase*7)&31)-18
                actual = o.collision_sample(x,y,plane=plane)
                expected = lookup(rom,tiles,x,y,plane=plane)
                assert actual == expected, ('lookup',tile,plane,phase,actual,expected)
                counts['lookup'] += 1
    tiles = layout(rom); o.mem[0xc001:0xd000] = bytes(tiles)
    rng = random.Random(0x7666)
    # Real map probes, several previous surface classes, upward/downward speeds.
    for _ in range(2400):
        x=rng.randrange(32,4064); y=rng.randrange(32,970)
        previous=rng.choice((0,0x81,0x82,0x83,0x92,0x41,0x57,0x9c))
        vy=rng.choice((0,0x100,0x700,0x120,0xff00,0xf880))
        plane=rng.randrange(2)
        sample=o.collision_sample(x,y,plane=plane)
        o.word(0xd518,vy);o.mem[0xd36c]=previous
        o.mem[0xd524]=0;o.mem[0xd522]=0;o.mem[0xd369]=0
        expected=project_floor(rom,tiles,sample,y,vy,previous,plane=plane)
        o.call(0x6f61)
        actual=(o.word(0xd514),o.mem[0xd522],o.mem[0xd369],o.mem[0xd368])
        assert actual==expected, ('floor',x,y,previous,vy,sample,actual,expected)
        counts['floor']+=1
    for raw in range(256):
        for phase in range(32):
            for side,entry in (('right',0x71b2),('left',0x7257)):
                o.word(0xd511,500);o.word(0xd358,320+phase)
                o.mem[0xd364]=0x81;o.mem[0xd367]=raw;o.mem[0xd522]=0
                expected=project_side(500,320+phase,0x81,raw,side)
                o.call(entry)
                actual=(o.word(0xd511),o.mem[0xd522])
                assert actual==expected, ('side',raw,phase,side,actual,expected)
                counts['side']+=1
    for angle in range(256):
        for magnitude in (0,1,15,16,64,128,160,255):
            o.mem[0xd50a]=angle;o.mem[0xd50b]=magnitude
            o.call(0x6089)
            actual=(s16(o.word(0xd516)),s16(o.word(0xd518)))
            expected=angle_velocity(rom,angle,magnitude)
            assert actual==expected, ('angle',angle,magnitude,actual,expected)
            counts['angle_velocity']+=1
    for water in (0,1):
        for state,increment in ((10,0x30),(11,0x18),(27,0x24),(28,0x30)):
            o.position(200,200);o.word(0xd518,0xf880)
            o.mem[0xd501]=state;o.mem[0xd503]=1;o.mem[0xd522]=0
            o.mem[0xd443]=water
            o.call(0x4097)
            expected=(0xf880+(increment//2 if water else increment))&65535
            assert o.word(0xd518)==expected
            counts['gravity']+=1
    # Eligible rightward ramp launches: the arithmetic and requested state,
    # not a guessed height threshold. Preserve the original fixed-point units.
    for velocity in (1,127,256,511,768,952,1024,1536):
        o.word(0xd516,velocity);o.word(0xd518,0)
        o.mem[0xd501]=o.mem[0xd502]=5;o.mem[0xd36a]=14
        o.mem[0xd523]=2;o.mem[0xd522]=2;o.mem[0xd503]=0
        o.call(0x69b2)
        assert s16(o.word(0xd518)) == -(velocity+velocity//2)
        assert o.mem[0xd502]==27 and o.mem[0xd503]&3==3
        counts['ramp_launch']+=1
    # Standalone movement-core trace: applies the requested state next tick,
    # holds right, and follows the camera. No animation/state-script scheduler.
    o=Oracle(rom);o.position(320,654);o.word(0xd516,1024)
    o.mem[0xd522]=o.mem[0xd523]=2;o.mem[0xd137]=8
    trace=[]
    for frame in range(48):
        o.word(0xd174,o.word(0xd511)-100)
        o.mem[0xd501]=o.mem[0xd502]
        o.call(0x3fef)
        trace.append(dict(frame=frame,x=o.word(0xd511),y=o.word(0xd514),
                          vx_8_8=s16(o.word(0xd516)),vy_8_8=s16(o.word(0xd518)),
                          state=o.mem[0xd501],requested_state=o.mem[0xd502],
                          contact_flags=o.mem[0xd523],previous_surface=o.mem[0xd36c],
                          modifier=o.mem[0xd369]))
    launch=next(row for row in trace if row['requested_state']==0x1b)
    assert launch['x']==386 and launch['vy_8_8']==-1428,launch
    output.mkdir(parents=True,exist_ok=True)
    with (output/'first-ramp-trace.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=trace[0]);writer.writeheader();writer.writerows(trace)
    # Empty-map vertical-spring flight through its actual state wrapper.
    spring=Oracle(rom);spring.mem[0xc001:0xd000]=bytes(4095)
    spring.position(200,800);spring.word(0xd518,-1920)
    spring.mem[0xd501]=spring.mem[0xd502]=11
    spring.mem[0xd503]=1;spring.mem[0xd36c]=0
    flight=[]
    for tick in range(160):
        spring.mem[0xd501]=spring.mem[0xd502];spring.word(0xd174,100)
        spring.call(0x393b if spring.mem[0xd501]==11 else 0x3fef)
        flight.append(dict(tick=tick+1,y=spring.word(0xd514)+spring.mem[0xd513]/256,
                           vy=s16(spring.word(0xd518))/256,state=spring.mem[0xd501],
                           requested_state=spring.mem[0xd502]))
    apex=min(row['y'] for row in flight)
    assert apex==503.75 and flight[79]['requested_state']==14 and flight[79]['vy']==1
    with (output/'vertical-spring-trace.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=flight[0]);writer.writeheader();writer.writerows(flight)
    report=dict(rom_sha256=SHA256,counts=counts,total=sum(counts.values()),
                first_ramp_launch=launch,
                vertical_spring_fixture=dict(initial_y=800,rise_pixels=800-apex,
                    first_falling_request_tick=80,falling_initial_velocity=1),
                limitations=['Subroutine RAM fixtures, not a full SMS emulator.',
                  'No GameMaker compilation or gameplay validation.',
                  'Floor translation excludes IX+$24 special branches.',
                  'Side tests cover ordinary projection cores, not all special tile handlers.'])
    (output/'differential-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom');p.add_argument('--output',type=Path,default=Path('reports'))
    a=p.parse_args();print(json.dumps(verify(a.rom,a.output),indent=2))

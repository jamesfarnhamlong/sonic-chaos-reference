"""Differential checks against original Z80 instructions, with explicit RAM fixtures."""
import argparse, csv, json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from rom import load, layout, SHA256, s16
from oracle import Oracle
from reference import lookup, project_floor, project_side, angle_velocity
import thz1_object_27 as object27
import thz1_object_10 as object10

def verify(path, output):
    rom = load(path); tiles = layout(rom); o = Oracle(rom)
    counts = dict(lookup=0, floor=0, side=0, angle_velocity=0,
                  gravity=0, ramp_launch=0, layout_decoder=0,
                  object10_create=0, object10_init=0,
                  object10_state_entry=0, object10_non_contact=0,
                  object10_contact=0, object10_reward=0,
                  object10_airborne=0, object10_lifetime=0,
                  object21_init=0, object21_patrol=0, object21_contact=0,
                  object27_create=0, object27_init=0, object27_proximity=0,
                  object27_oscillation=0, object27_removal=0,
                  object27_contact=0, object27_lifetime=0)
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

    # Type $21 initialization and two real-placement patrols. These execute the
    # original bank-$0C callbacks plus the original THZ floor routines.
    object21_init=[]
    for parameter,expected_bound in ((2,968),(8,872)):
        obj=Oracle(rom);obj.bank(2,12);obj.mem[0xd12b]=12;obj.cpu.ix=0xd700
        obj.word(0xd711,1000);obj.mem[0xd73f]=parameter;obj.mem[0xd704]=0
        obj.call(0xb210)
        actual=(obj.mem[0xd702],s16(obj.word(0xd716)),
                s16(obj.word(0xd718)),obj.word(0xd737),obj.mem[0xd73f])
        assert actual==(3,-128,512,expected_bound,0),('object21_init',parameter,actual)
        object21_init.append(dict(parameter=parameter,left_bound=actual[3]))
        counts['object21_init']+=1

    object21_patrol=[]
    for x,y,parameter,expected_ticks in ((2400,254,2,(65,132)),
                                          (800,606,8,(257,516))):
        obj=Oracle(rom);obj.bank(2,12);obj.mem[0xd12b]=12;obj.cpu.ix=0xd700
        obj.mem[0xd700]=0x21;obj.word(0xd711,x);obj.word(0xd714,y)
        obj.word(0xd73a,x);obj.word(0xd73c,y);obj.mem[0xd73f]=parameter
        obj.call(0xb210);transitions=[]
        for tick in range(1,1025):
            before=obj.mem[0xd702]
            obj.call(0xb264 if before in (4,5) else 0xb268)
            after=obj.mem[0xd702]
            if after!=before:
                transitions.append(dict(tick=tick,from_state=before,to_state=after,
                                        x=obj.word(0xd711),x_fraction=obj.mem[0xd710],
                                        vx_8_8=s16(obj.word(0xd716))))
                if len(transitions)==2:break
        assert tuple(row['tick'] for row in transitions)==expected_ticks
        assert [(row['from_state'],row['to_state']) for row in transitions]==[(3,4),(4,3)]
        object21_patrol.append(dict(parameter=parameter,transitions=transitions))
        counts['object21_patrol']+=1

    def object21_contact_fixture(object_y,player_flags=0,power_up=0):
        obj=Oracle(rom);obj.bank(2,12);obj.mem[0xd12b]=12;obj.cpu.ix=0xd700
        obj.mem[0xd700]=0x21;obj.word(0xd711,500);obj.word(0xd714,object_y)
        obj.mem[0xd72c]=0x0b;obj.mem[0xd72d]=0x1a
        obj.word(0xd511,500);obj.word(0xd514,500)
        obj.mem[0xd52c]=9;obj.mem[0xd52d]=18
        obj.mem[0xd503]=player_flags;obj.mem[0xd532]=power_up
        obj.word(0xd518,0);obj.call(0xb2af)
        return obj

    top=object21_contact_fixture(504)
    assert (top.mem[0xd502],s16(top.word(0xd518)),top.mem[0xd448],
            top.mem[0xde04],top.mem[0xd700])==(11,-1728,255,0xa6,0x21)
    side=object21_contact_fixture(500)
    assert side.mem[0xd3b0]==0xff and side.mem[0xd700]==0x21
    attack=object21_contact_fixture(500,player_flags=2)
    assert attack.mem[0xd700]==0x0f and attack.mem[0xd73e]==0
    assert bytes(attack.mem[0xd29d:0xd2a0])==bytes.fromhex('10 00 00')
    invincible=object21_contact_fixture(500,power_up=6)
    assert invincible.mem[0xd700]==0x0f and invincible.mem[0xd3b0]==0
    counts['object21_contact']+=4

    # Type $27 source-level state scripts plus controlled original callbacks.
    # The dedicated tool also emits the committed ROM-cache report.
    object27_report=object27.build_report(rom)
    object27_fixtures=object27_report['controlled_original_routine_fixtures']

    created=object27_fixtures['placement_creation']
    assert (created['object_type'],created['current_x'],created['current_y'],
            created['saved_x'],created['saved_y'],created['object_flags_04'],
            created['parameter_3f'],created['art_base_08'],created['art_base_09'],
            created['placement_token_3e'],created['occupancy_value']) == (
                '0x27',3504,224,3504,224,'0x50','0x00','0xAA','0xAA',25,'0x27')
    counts['object27_create']+=1

    init_zero,init_nonzero=object27_fixtures['initialization']
    assert (init_zero['requested_state'],init_zero['x_velocity_8_8'],
            init_zero['y_velocity_8_8'],init_zero['object_flags_04']) == (1,-640,0,'0x10')
    assert (init_nonzero['requested_state'],init_nonzero['x_velocity_8_8'],
            init_nonzero['y_velocity_8_8'],init_nonzero['field_1e'],
            init_nonzero['field_1f']) == (2,0,0x5678,'0x80','0x01')
    counts['object27_init']+=2

    proximity=object27_fixtures['proximity']
    assert [row['distance_at_compare'] for row in proximity] == [65,64,63]
    assert [row['requested_state'] for row in proximity] == [1,1,2]
    assert proximity[2]['object_flags_04']=='0x12'
    assert proximity[2]['x_velocity_8_8']==0 and proximity[2]['counter_1e']=='0x80'
    counts['object27_proximity']+=3

    oscillation=object27_fixtures['oscillation']
    assert (oscillation['updates_to_counter_underflow'],oscillation['add_callbacks'],
            oscillation['subtract_callbacks']) == (129,65,64)
    assert oscillation['underflow_update']['requested_state']==3
    assert oscillation['underflow_update']['counter_1e']=='0xFF'
    assert oscillation['underflow_update']['y_displacement_8_8']==3
    assert oscillation['horizontal_resume_update']['current_state']==3
    assert oscillation['horizontal_resume_update']['callback_cpu']=='0x8A29'
    assert oscillation['horizontal_resume_update']['x_velocity_8_8']==-640
    assert oscillation['horizontal_resume_update']['y_velocity_8_8']==0
    assert object27_report['independent_translation']=={
        'updates':129,'add_callbacks':65,'subtract_callbacks':64,
        'displacement_8_8':3,'velocity_before_reset_8_8':3,'counter_after':255}
    counts['object27_oscillation']+=130

    removal=object27_fixtures['removal']
    assert [row['distance'] for row in removal] == [383,384,385]
    assert [row['object_type_after'] for row in removal] == ['0x27','0xFE','0xFE']
    assert all(row['placement_token_after']==25 for row in removal)
    counts['object27_removal']+=3

    contact=object27_fixtures['contact']
    assert contact['ordinary']['object_type_after']=='0x27'
    assert contact['ordinary']['damage_request_d3b0']=='0x00'
    assert contact['ordinary']['x_displacement_8_8']==0
    for name in ('rolling_attack','power_up_06'):
        assert contact[name]['object_type_after']=='0x0F'
        assert contact[name]['placement_token_after']==0
        assert contact[name]['score_bytes_after']=='10 00 00'
    counts['object27_contact']+=3

    lifetime=object27_fixtures['lifetime']
    assert lifetime['before_trigger']['object_type_after']=='0xFE'
    assert lifetime['after_trigger']['object_type_after']=='0x27'
    assert lifetime['after_trigger']['object_flags_04']=='0x52'
    assert lifetime['type_fe_cleanup']['occupancy_value_after']=='0x00'
    assert lifetime['type_fe_cleanup']['slot_is_zero']
    counts['object27_lifetime']+=3

    # Type $10 full placement, state, contact, numeric reward, replacement,
    # and occupancy chain. Each count is an original routine execution or a
    # controlled comparison, not a metadata-only assertion.
    object10_report=object10.build_report(rom)
    object10_fixtures=object10_report['controlled_original_routine_fixtures']

    created=object10_fixtures['placement_creation']
    assert len(created)==5
    assert [(row['current_x'],row['current_y']) for row in created]==[
        (656,846),(1712,494),(336,270),(1472,110),(2688,686)]
    assert [row['parameter_3f'] for row in created]==[
        '0x06','0x06','0x04','0x04','0x02']
    assert all(row['object_type']=='0x10' and row['object_flags_04']=='0x40'
               and row['art_base_08']=='0x00' and row['art_base_09']=='0x00'
               for row in created)
    counts['object10_create']+=5

    init=object10_fixtures['initialization']
    assert [row['parameter_after'] for row in init]==['0x02','0x04','0x06']
    assert all(row['requested_state']==1 and row['object_flags_03']=='0x81'
               for row in init)
    alternate=object10_fixtures['alternate_player_parameter_04']
    assert alternate['initialization']['parameter_after']=='0x01'
    assert alternate['reward_bits_d3a3']=='0x01'
    counts['object10_init']+=5  # three ordinary calls plus alternate init/contact

    entry=object10_fixtures['state_1_entry']
    assert [row['graphics_selector_d3b3'] for row in entry]==[
        '0x02','0x04','0x06']
    assert all(row['requested_state']==2 for row in entry)
    counts['object10_state_entry']+=3

    non_contact=object10_fixtures['ordinary_non_contact_update']
    assert non_contact['contact_bits_21']=='0x00'
    assert non_contact['object_type_after']=='0x10'
    assert non_contact['damage_request_d3b0']=='0x00'
    counts['object10_non_contact']+=1

    contact=object10_fixtures['contact']
    assert contact['ordinary_top_contact']['object_type_after']=='0x10'
    assert contact['power_up_06_without_attack']['object_type_after']=='0x10'
    assert contact['top_attack_downward']['object_type_after']=='0x0F'
    assert contact['side_attack_downward']['object_type_after']=='0x0F'
    assert contact['top_attack_zero_velocity']['object_type_after']=='0x10'
    assert contact['top_attack_upward']['object_type_after']=='0x10'
    bottom=contact['bottom_attack_upward']
    assert (bottom['object_type_after'],bottom['requested_object_state'],
            bottom['player_y_velocity_8_8'],bottom['object_y_velocity_8_8']) == (
                '0x10',3,512,-512)
    assert all(row['object_type_after']=='0x10'
               for row in contact['top_blocked_player_states'].values())
    boundaries=contact['overlap_boundaries']
    assert [row['contact_bits_21'] for row in boundaries]==[
        '0x04','0x04','0x00','0x01','0x01','0x00','0x02','0x02','0x00']
    assert all(row['contact_bits_21']==row['translated_contact'] for row in boundaries)
    counts['object10_contact']+=20

    rewards=object10_fixtures['reward']
    assert [row['table_mask'] for row in rewards]==['0x02','0x08','0x20']
    assert all(row['after_contact']['object_type_after']=='0x0F'
               and row['after_contact']['placement_token_after']==0
               and row['after_contact']['occupancy_value_after']=='0x10'
               and row['after_contact']['score_bytes_after']=='10 00 00'
               for row in rewards)
    dispatched=[row['after_reward_dispatch'] for row in rewards]
    assert (dispatched[0]['counter_d299_bcd'],
            dispatched[0]['sound_request_de04'])==('0x10','0xA9')
    assert (dispatched[1]['power_up_d532'],dispatched[1]['timer_d44c'],
            dispatched[1]['player_requested_state_d502'],
            dispatched[1]['sound_request_de04'])==('0x04',300,'0x11','0x85')
    assert (dispatched[2]['power_up_d532'],dispatched[2]['timer_d44c'],
            dispatched[2]['player_flags_d503'],
            dispatched[2]['sound_request_de04'],
            dispatched[2]['child']['type'])==('0x06',600,'0x82','0x84','0x05')
    counts['object10_reward']+=6  # contact plus reward-dispatch call per parameter

    airborne=object10_fixtures['airborne']
    assert airborne['empty_map_first_update']['y_velocity_8_8_after']==-448
    assert airborne['empty_map_first_update']['requested_state']==3
    assert airborne['first_thz1_placement_landing']['updates']==17
    assert airborne['first_thz1_placement_landing']['requested_state']==2
    counts['object10_airborne']+=18

    object10_lifetime=object10_fixtures['lifetime']
    assert object10_lifetime['untouched_off_range_before_cleanup']['object_type']=='0xFE'
    assert object10_lifetime['untouched_after_cleanup']['occupancy_value']=='0x00'
    assert object10_lifetime['untouched_after_cleanup']['can_respawn']
    assert object10_lifetime['consumed_after_conversion']['object_type']=='0x0F'
    assert object10_lifetime['consumed_after_conversion']['placement_token']==0
    assert object10_lifetime['consumed_after_replacement_cleanup']['occupancy_value']=='0x10'
    assert not object10_lifetime['consumed_after_replacement_cleanup']['can_respawn_same_loaded_act']
    counts['object10_lifetime']+=7

    report=dict(rom_sha256=SHA256,counts=counts,total=sum(counts.values()),
                first_ramp_launch=launch,
                vertical_spring_fixture=dict(initial_y=800,rise_pixels=800-apex,
                    first_falling_request_tick=80,falling_initial_velocity=1),
                object21_fixture=dict(initialization=object21_init,
                    patrol=object21_patrol,
                    contact=dict(top_bounce_velocity_8_8=-1728,
                        ordinary_side_damage_request='0xFF',
                        defeated_replacement_type='0x0F',
                        score_bytes='10 00 00')),
                object27_fixture=dict(
                    proximity_boundary='distance < 64',
                    oscillation_updates=129,
                    oscillation_displacement_8_8=3,
                    removal_boundary='distance >= 384',
                    ordinary_contact_damage_request='0x00',
                    defeated_replacement_type='0x0F',
                    score_bytes='10 00 00',
                    type_fe_cleanup_releases_occupancy=True),
                object10_fixture=dict(
                    parameters=dict(value_02='D3A3 bit 1 -> D299 BCD +1, sound A9',
                        value_04='D3A3 bit 3 -> D532=04, timer 300, player state 11',
                        value_06='D3A3 bit 5 -> D532=06, timer 600, type-05 child'),
                    active_contact_extents=dict(horizontal=10,vertical=24),
                    successful_replacement_type='0x0F',
                    score_bytes='10 00 00',
                    untouched_can_respawn=True,
                    consumed_can_respawn_same_loaded_act=False),
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

"""M5-P0R PCM-independent latched PSG emission model.

PRIVATE dry per-channel intents supply intrinsic note/envelope timing. Combined
original traces are never inputs. This models emission/holding, not oscillators
or a second independent sound-stream decoder. No PCM or Z80 dependency.
"""
from m5p0_model import Model

class Registers:
    def __init__(self):
        self.tone=[0,0,0];self.noise=0;self.attenuation=[15]*4;self.latch=0
    def write(self,value):
        if value&128:self.latch=(value>>4)&7
        channel=self.latch>>1;attenuation=self.latch&1
        if attenuation:self.attenuation[channel]=value&15
        elif channel==3:self.noise=value&7
        elif value&128:self.tone[channel]=(self.tone[channel]&0x3F0)|(value&15)
        else:self.tone[channel]=(self.tone[channel]&15)|((value&63)<<4)
    def snapshot(self):return (tuple(self.tone),self.noise,tuple(self.attenuation))

class EmissionModel(Model):
    def __init__(self,bank):
        self.psg=Registers();self.writes=[];self.audit=[];self.saved_noise=0;self.volumes=[0]*7
        self.env_position=[0]*7;self.env_value=[0]*7
        super().__init__(bank)
    def emit(self,value,reason,index=None):
        self.writes.append(value);self.psg.write(value)
        self.audit.append(dict(reason=reason,channel=index,value=value,registers=self.psg.snapshot()))
    def reset(self):
        super().reset();self.saved_noise=0;self.volumes=[0]*7;self.env_position=[0]*7;self.env_value=[0]*7
        for latch in (0x80,0xA0,0xC0):self.emit(latch,'reset-frequency');self.emit(0,'reset-frequency')
        for latch in (0x9F,0xBF,0xDF,0xFF):self.emit(latch,'reset-off')
    def init(self,rid):
        p=self.bank['programs'][str(rid)]
        noise_off=rid>=0xA0 and any(s['latch']==0xC0 for s in p['streams']) and not self.channels[6].flags&64
        super().init(rid)
        if rid<0xA0:
            for i,v in enumerate(p['initial_volumes']):self.volumes[i]=v;self.env_position[i]=0
        else:
            for n,s in enumerate(p['streams']):
                slot={0xA0:4,0xC0:5,0xE0:6}[s['latch']];self.volumes[slot]=p['initial_volumes'][n];self.env_position[slot]=0
            if noise_off:self.emit(0xFF,'tone2-init-noise-off')
    def f2(self,index):
        latch=self.channels[index].latch
        super().f2(index)
        if latch not in (0xA0,0xC0):self.emit(self.saved_noise,'F2-saved-noise-restore',index)
        self.emit(latch|31,'F2-explicit-own-off',index)
    def f3(self,index,value):
        rejected=not self.last_sfx&128 and value&3==3 and self.channels[5].flags&128
        super().f3(index,value)
        if rejected:self.emit(0xFF,'F3-rejected-noise-off',index);return
        self.emit(value,'F3-noise-control',index)
        if value&3==3:self.emit(0xDF,'F3-tone2-off',index)
    def tick(self):
        self.tick_number+=1;self.events=[];self.writes=[];self.audit=[]
        if self.paused:return
        self.arbitration()
        if self.tempo[0]:self.tempo[0]-=1;self.tempo[0]=self.tempo[0] or self.tempo[1]
        if self.fade[0]:
            for i in range(4,7):
                c=self.channels[i]
                if not c.flags&128:continue
                if c.latch==0xA0:self.channels[1].flags&=~4
                else:
                    if c.latch==0xE0:self.channels[3].flags&=~4
                    self.channels[2].flags&=~4
                c.flags=0
            self.fade[1]-=1
            if not self.fade[1]:
                self.fade[1]=self.fade[2];self.fade[0]-=1
                if not self.fade[0]:self.reset()
                else:
                    for i in range(3):
                        if self.volumes[i]+1<12:self.volumes[i]+=1
        rid=self.selected
        if rid!=0x80:
            if rid>=0xD4 or not rid&128:self.reset()
            elif 0x81<=rid<=0xC4:self.init(rid)
            else:raise ValueError('unindexed control')
        for i,c in enumerate(self.channels):
            if not c.flags&128:continue
            c.age+=1;p=self.bank['programs'][str(c.rid)]
            if c.age>p['coverage_ticks']:raise ValueError('private dry-intent coverage exhausted')
            for kind,value in p['events'][c.stream].get(str(c.age),[]):
                if kind=='read':
                    if c.waiting:self.events.append(('recover',i,c.rid,c.age))
                    c.waiting=False
                elif kind=='f2':self.f2(i)
                elif kind=='f3':self.f3(i,value)
                elif kind=='tempo':self.tempo=[value,value]
                elif kind=='volume-absolute':self.volumes[i]=value
                elif kind=='volume-relative':
                    if not self.fade[0]:self.volumes[i]=(self.volumes[i]+value)&15
                elif kind=='inhibit':c.waiting=True
                elif kind=='envelope-epoch':self.env_position[i]=0
                elif kind=='envelope-step':
                    # Tone/SFX suppression returns before envelope advancement;
                    # music-noise non-read path calls envelope before its guard.
                    if c.flags&4 and i!=3:continue
                    steps=p['envelope_sequences'][c.stream][str(value)];position=self.env_position[i]
                    if position>=len(steps):raise ValueError('envelope program coverage exhausted')
                    step=steps[position];self.env_position[i]+=1;self.env_value[i]=step.get('value')
                    if step['inhibit']:c.waiting=True
                    if step.get('off') and not c.flags&4:self.emit(c.latch|31,'envelope-terminal-explicit-off',i)
                elif kind=='off':
                    c.waiting=True
                    if not c.flags&4:self.emit(c.latch|31,'terminal-or-rest-explicit-off',i)
                elif kind=='attenuation':
                    if not c.flags&4 and not c.waiting:
                        if self.env_value[i] is None:raise ValueError('terminal envelope cannot emit a level')
                        result=(self.env_value[i]+self.volumes[i])&255
                        if result&16:result=15
                        self.emit(((result|c.latch)+16)&255,'ordinary-attenuation-write',i)
                elif kind=='port':
                    byte,at_read=value
                    if not c.flags&4 and (not c.waiting or not at_read):self.emit(byte,'ordinary-frequency-write',i)
                elif kind=='music-noise-control':
                    if not c.flags&4:self.saved_noise=value;self.emit(value,'music-noise-control',i)
                else:raise ValueError(kind)
    def emission_snapshot(self):
        return dict(registers=self.psg.snapshot(),data_latch=self.psg.latch,
            channel_state=[(c.flags&0xC4)|(16 if c.waiting else 0) for c in self.channels],priority=self.priority)

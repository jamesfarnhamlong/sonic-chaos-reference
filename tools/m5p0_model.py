"""PCM-independent M5 ownership model. No Z80, ROM or PCM dependency.

Input bank: PRIVATE dry-channel event/timing metadata exported once from the
original driver. This is an ownership/dispatch reference, not a note decoder.
Combined scenarios are predicted without consulting their original-driver trace.
"""
from dataclasses import dataclass

@dataclass
class Channel:
    flags:int=0
    latch:int=0
    rid:int=0
    stream:int=0
    age:int=0
    waiting:bool=False  # write-inhibit bookkeeping, NOT proof of PSG silence
    generation:int=0

class Model:
    def __init__(self,bank):
        self.bank=bank;self.channels=[Channel() for _ in range(7)]
        self.priority=0;self.mail=[0,0,0];self.deferred=0;self.selected=0x80
        self.tempo=[0,0];self.fade=[0,0,0];self.paused=False;self.tick_number=0
        self.last_sfx=0;self.events=[]

    def direct(self,rid,slot=0):self.mail[slot]=rid
    def game(self,rid):self.deferred=rid
    def transfer(self):
        if self.deferred:self.mail[0]=self.deferred;self.deferred=0
    def stop(self):
        self.reset();self.mail=[0,0,0];self.deferred=0;self.paused=False
    def reset(self):
        # Original reset clears DE03 onward, not DE01/DE02 tempo bytes.
        self.channels=[Channel(generation=c.generation+1) for c in self.channels]
        self.priority=0;self.selected=0x80;self.mail=[0,0,0];self.fade=[0,0,0];self.last_sfx=0
    def arbitration(self):
        for i,rid in enumerate(self.mail):
            if rid&127:
                pr=self.bank['priority'][str(rid)]
                if pr>=self.priority:self.priority=pr&127;self.selected=rid
            self.mail[i]=0
    def f2(self,index):
        c=self.channels[index];latch=c.latch
        if latch==0xA0:target=1
        elif latch==0xC0:target=6 if self.channels[6].flags&128 else 2
        else:
            if not c.flags&64 and not self.channels[5].flags&128:
                self.channels[2].flags&=~(4|64);self.channels[2].waiting=True
                self.channels[5].flags=0
            target=3
        self.channels[target].flags&=~4;self.channels[target].waiting=True
        self.priority=0;c.flags=0
        self.events.append(('end',index,c.rid,c.age))
    def f3(self,index,value):
        c=self.channels[index]
        if not self.last_sfx&128 and value&3==3 and self.channels[5].flags&128:
            self.channels[3].flags&=~4;self.channels[3].waiting=True
            c.flags=0;self.last_sfx=255;return
        if value&3==3:
            c.flags&=~64;self.channels[2].flags|=4;self.channels[5].flags|=4
        else:
            c.flags|=64
            target=5 if self.channels[5].flags&128 else 2
            self.channels[target].flags&=~4
    def init(self,rid):
        p=self.bank['programs'][str(rid)]
        if rid<0xA0:
            self.reset();self.tempo=list(p['tempo'])
            for n in range(p['channel_count']):
                self.channels[n]=Channel(128,0x80+32*n,rid,n)
        else:
            self.last_sfx=rid
            for n,s in enumerate(p['streams']):
                latch=s['latch'];slot={0xA0:4,0xC0:5,0xE0:6}[latch]
                if latch==0xC0 and not self.channels[6].flags&64:self.channels[6].flags|=4
                self.channels[{4:1,5:2,6:3}[slot]].flags|=4
                gen=self.channels[slot].generation+1
                self.channels[slot]=Channel(s['flags'],latch,rid,n,generation=gen)
        self.selected=0x80
    def tick(self):
        self.tick_number+=1;self.events=[]
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
        rid=self.selected
        if rid!=0x80:
            if rid>=0xD4 or not rid&128:self.reset()
            elif 0x81<=rid<=0xC4:self.init(rid)
            else:raise ValueError('unindexed control')
        for i,c in enumerate(self.channels):
            if not c.flags&128:continue
            c.age+=1;p=self.bank['programs'][str(c.rid)]
            if c.age>p['coverage_ticks']:raise ValueError('dry program coverage exhausted; recapture explicitly')
            # Music programs advance in exact captured driver-tick time,
            # including the original tempo divider, not a presumed fixed BPM.
            for kind,value in p['events'][c.stream].get(str(c.age),[]):
                if kind=='read':
                    if c.waiting:self.events.append(('recover',i,c.rid,c.age))
                    c.waiting=False
                elif kind=='f3':self.f3(i,value)
                elif kind=='f2':self.f2(i)
                elif kind=='tempo':self.tempo=[value,value]
    def snapshot(self):return dict(flags=[c.flags&0xC4 for c in self.channels],priority=self.priority)

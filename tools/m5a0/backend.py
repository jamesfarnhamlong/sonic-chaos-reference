"""Persistent PSG integration binding; no dependency on Z80 or reference captures."""
import ctypes as C
from pathlib import Path
import numpy as np
class PSG:
 def __init__(self,dll):
  self.lib=C.CDLL(str(Path(dll).resolve()));L=self.lib
  L.a0_new.restype=C.c_void_p;L.a0_free.argtypes=[C.c_void_p]
  L.a0_write.argtypes=[C.c_void_p,C.c_void_p,C.c_int];L.a0_render.argtypes=[C.c_void_p,C.c_void_p,C.c_int]
  L.a0_state.argtypes=[C.c_void_p,C.c_void_p];L.a0_state_bytes.restype=C.c_size_t
  L.a0_buffer_bytes.argtypes=[C.c_void_p];L.a0_buffer_bytes.restype=C.c_size_t
  L.a0_bench.argtypes=[C.c_void_p,C.c_int];L.a0_bench.restype=C.c_uint64
  self.ptr=L.a0_new()
  if not self.ptr:raise MemoryError('PSG')
 def close(self):
  if self.ptr:self.lib.a0_free(self.ptr);self.ptr=None
 def write(self,values):
  b=(C.c_uint8*len(values))(*values)
  assert self.lib.a0_write(self.ptr,b,len(values))==0
 def render(self,n=735):
  out=np.empty(n,dtype='<i2');assert self.lib.a0_render(self.ptr,out.ctypes.data,n)==0;return out
 def state(self):
  a=(C.c_int64*26)();self.lib.a0_state(self.ptr,a);return list(a)
 def __enter__(self):return self
 def __exit__(self,*_):self.close()

def candidate(bank,case,dll,split=False,reference_chunks=False):
 # Critical boundary: only private intrinsic programs and external request schedule
 # enter this function. No combined oracle writes/states are accepted as inputs.
 from m5p0r_emission import EmissionModel
 m=EmissionModel(bank);m.direct(case['initial']);rows=[];blocks=[]
 with PSG(dll) as chip:
  for tick in range(1,case['ticks']+1):
   for kind,value in case['events'].get(tick,[]):
    if kind=='request':m.direct(value)
    elif kind=='fade':m.fade=list(value)
   m.tick();writes=list(m.writes);chip.write(writes);before=chip.state()
   if reference_chunks:
    # Diagnostic: reproduce vgm2wav's external 2048-frame callback boundaries.
    # Events still come only from the independently advanced model.
    cursor=(tick-1)*735;remaining=735;parts=[]
    while remaining:
     n=min(remaining,2048-cursor%2048);parts.append(chip.render(n));cursor+=n;remaining-=n
    block=np.concatenate(parts)
   else:block=np.concatenate([chip.render(100),chip.render(635)]) if split else chip.render()
   blocks.append(block);rows.append(dict(ports=writes,registers=m.psg.snapshot(),latch=m.psg.latch,saved_noise=m.saved_noise,channels=m.emission_snapshot()['channel_state'],priority=m.priority,psg_before=before,psg_after=chip.state()))
 return np.concatenate(blocks),rows

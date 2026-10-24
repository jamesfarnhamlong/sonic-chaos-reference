"""Small PE/COFF dependency reader, authored for this audit (MIT)."""
import struct
from pathlib import Path
def pe_imports(path):
 b=Path(path).read_bytes();pe=struct.unpack_from('<I',b,0x3c)[0];assert b[pe:pe+4]==b'PE\0\0'
 count=struct.unpack_from('<H',b,pe+6)[0];opt=pe+24;optsize=struct.unpack_from('<H',b,pe+20)[0];assert struct.unpack_from('<H',b,opt)[0]==0x20b
 sections=[]
 for i in range(count):
  p=opt+optsize+i*40;vsize,rva,size,offset=struct.unpack_from('<IIII',b,p+8);sections.append((rva,max(vsize,size),offset))
 def address(rva):
  for start,n,offset in sections:
   if start<=rva<start+n:return offset+rva-start
  raise ValueError('unmapped RVA')
 def text(rva):
  p=address(rva);return b[p:b.index(b'\0',p)].decode('ascii')
 rva,size=struct.unpack_from('<II',b,opt+112+8);imports={}
 if rva:
  p=address(rva)
  while any(b[p:p+20]):
   original,stamp,chain,name,iat=struct.unpack_from('<IIIII',b,p);thunk=address(original or iat);symbols=[]
   while True:
    v=struct.unpack_from('<Q',b,thunk)[0]
    if not v:break
    symbols.append('ordinal:'+str(v&65535) if v>>63 else text(v+2));thunk+=8
   imports[text(name)]=symbols;p+=20
 return imports
if __name__=='__main__':
 import json,sys
 print(json.dumps(pe_imports(sys.argv[1]),indent=2))

def coff_symbols(path):
 b=Path(path).read_bytes();offset,count=struct.unpack_from('<II',b,8);strings=b[offset+18*count:];out=[];i=0
 while i<count:
  p=offset+18*i;raw=b[p:p+8]
  name=strings[struct.unpack_from('<I',raw,4)[0]:].split(b'\0')[0] if raw[:4]==b'\0'*4 else raw.split(b'\0')[0]
  value,section,typ,storage,aux=struct.unpack_from('<IhHBB',b,p+8)
  if storage==2:out.append(dict(name=name.decode(),defined=section>0,section=section,value=value))
  i+=1+aux
 return out

def pdb_modules(path):
 # MSF7 and DBI layouts described by LLVM's public format documentation.
 b=Path(path).read_bytes();assert b.startswith(b'Microsoft C/C++ MSF 7.00')
 block,_,_,dirbytes,_,mapblock=struct.unpack_from('<6I',b,32)
 ids=struct.unpack_from('<'+str((dirbytes+block-1)//block)+'I',b,mapblock*block)
 directory=b''.join(b[i*block:(i+1)*block] for i in ids)[:dirbytes]
 n=struct.unpack_from('<I',directory)[0];sizes=struct.unpack_from('<'+str(n)+'I',directory,4);p=4+4*n;streams=[]
 for size in sizes:
  count=0 if size==0xffffffff else (size+block-1)//block;ids=struct.unpack_from('<'+str(count)+'I',directory,p);p+=4*count
  streams.append(b''.join(b[i*block:(i+1)*block] for i in ids)[:size])
 dbi=streams[3];modsize=struct.unpack_from('<I',dbi,24)[0];mods=dbi[64:64+modsize];p=0;out=[]
 while p<len(mods):
  q=p+64;end=mods.index(b'\0',q);name=mods[q:end].decode();q=end+1;end=mods.index(b'\0',q);obj=mods[q:end].decode()
  out.append(dict(module=name,object=obj));p=(end+4)//4*4
 return out

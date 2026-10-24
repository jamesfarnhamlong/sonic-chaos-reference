"""Mechanical integration-only extraction of the explicitly BSD PSG source.
New translation units use no libvgm helper/header and link no C runtime.
"""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--cc',type=Path,required=True);a=p.parse_args()
out=ROOT/'build/m5-a1l';out.mkdir(parents=True,exist_ok=True);core=a.source.resolve()/'emu/cores/sn76496.c';raw=core.read_bytes();assert hashlib.sha256(raw).hexdigest()=='91e6d92121bd94466c6971c6a3b52adb2016930cc29fa38caa2fdf9a49e98ab3'
s=raw.decode().replace('\r\n','\n');start=s.index('static DEVDEF_RWFUNC devFunc[]');end=s.index('#define MAX_OUTPUT');body=s[end:]
s=s[:start]+s[end:];s=re.sub(r'^#include[^\r\n]*\r?\n','',s,flags=re.M)
retained=out/'retained_psg.c';retained.write_text(s,encoding='utf-8');assert retained.read_text(encoding='utf-8')[s.index('#define MAX_OUTPUT'):]==body
cc=str(a.cc.resolve());sources=[ROOT/'tools/m5a1l/adapter.c',ROOT/'tools/m5a1l/support.c'];dll=out/'psg-a1l.dll'
env=dict(os.environ,ZIG_GLOBAL_CACHE_DIR=str(out/'zig-cache'),ZIG_LOCAL_CACHE_DIR=str(out/'zig-local'),TEMP=str(out),TMP=str(out));commands=[];objects=[]
for src in sources:
 obj=out/(src.stem+'.obj');objects.append(obj)
 cmd=[cc,'cc','-c','-O2','-ffreestanding','-fno-builtin','-fno-stack-protector','-I',str(out),'-I',str(ROOT/'tools/m5a1l'),'-MD','-MF',str(out/(src.stem+'.d')),str(src),'-o',str(obj)];commands.append(cmd);subprocess.run(cmd,env=env,check=True)
cmd=[cc,'cc','-shared','-nostdlib','-Wl,--entry,a1_dll_entry',*[str(x) for x in objects],'-lkernel32','-o',str(dll),'-v'];commands.append(cmd)
linked=subprocess.run(cmd,env=env,capture_output=True,text=True);(out/'link-trace.txt').write_text(linked.stdout+linked.stderr);linked.check_returncode()
h=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
manifest=dict(core_source_sha256=h(core),retained_body_sha256=hashlib.sha256(body.encode()).hexdigest(),retained_psg_sha256=h(retained),removed='includes and device-registration table only; retained body identical after LF normalization',inputs={str(x.relative_to(ROOT)):h(x) for x in sources+[ROOT/'tools/m5a1l/support.h']},commands=commands,objects={x.name:h(x) for x in objects},dependencies={x.stem:(out/(x.stem+'.d')).read_text() for x in sources},binary_sha256=h(dll),binary_bytes=dll.stat().st_size,link_trace_sha256=h(out/'link-trace.txt'),pdb_sha256=h(out/'psg-a1l.pdb'),compiler_version=subprocess.check_output([cc,'version'],text=True).strip())
(out/'build.json').write_text(json.dumps(manifest,indent=2)+'\n');print('built',dll)

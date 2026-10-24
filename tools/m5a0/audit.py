"""Audit the exact source files transitively included by the feasibility build."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];source=ROOT.parent/'sonic-chaos-reference-m4/build/m4/renderer/libvgm-src'
seen={};todo=[source/'emu/cores/sn76496.c',source/'emu/Resampler.c',source/'emu/logging.c']
while todo:
 p=todo.pop().resolve()
 if p in seen:continue
 text=p.read_text();rel=p.relative_to(source.resolve()).as_posix();spdx=re.search(r'license:([^\r\n]+)',text[:1500])
 seen[p]=dict(path=rel,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),declared_license=spdx.group(1).strip() if spdx else 'not declared in file header')
 for inc in re.findall(r'^\s*#\s*include\s*"([^"]+)"',text,re.M):
  q=(p.parent/inc).resolve()
  if q.exists():todo.append(q)
dirty=subprocess.check_output(['git','diff','--name-only'],cwd=source,text=True).splitlines()
assert not set(dirty)&{v['path'] for v in seen.values()}
report=dict(pinned_commit='a6eed945ecf4e5a25cf82004779c6f7e4fd5c319',files=sorted(seen.values(),key=lambda r:r['path']),needed_sources_clean=True,unrelated_existing_patch=dirty,
 scope='file-specific license declaration; no assumption that PSG license covers resampler, headers, whole libvgm or MAME',
 sources=['https://github.com/ValleyBell/libvgm/issues/129','https://github.com/ValleyBell/libvgm/issues/43','https://raw.githubusercontent.com/ValleyBell/libvgm/master/emu/cores/sn76496.c','https://opensource.org/license/bsd-3-clause'],
 redistribution='CONDITIONAL: BSD core notices/conditions/disclaimer required; clarify or independently replace unlicensed helpers before a distributable extension')
p=ROOT/'data/m5-a0/source-license-audit.json';p.write_text(json.dumps(report,indent=2)+'\n');print('audited',len(seen),'source/header files')

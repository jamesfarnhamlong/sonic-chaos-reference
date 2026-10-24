"""Auditable file-permission matrix and exact experimental dependency manifest (MIT)."""
import hashlib,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from pe import pe_imports,coff_symbols,pdb_modules
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT.parent/'sonic-chaos-reference-m4/build/m4/renderer/libvgm-src';OUT=ROOT/'build/m5-a1l';PUB=ROOT/'data/m5-a1l'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
old=json.loads((ROOT/'data/m5-a0/source-license-audit.json').read_text());entries=[]
replacements={'_stdbool.h':'not required; new component uses no bool compatibility layer','common_def.h':'own static-inline definition only','emu/EmuCores.h':'registration metadata removed; no core ID tables needed','emu/EmuHelper.h':'new local initialization assignments; no helper source included','emu/EmuStructs.h':'new component-private types; not the libvgm ABI/layout','emu/Resampler.c':'new rational area-integration implementation; original quantization not reproduced','emu/Resampler.h':'new adapter has no libvgm resampler API','emu/cores/sn76496.h':'unneeded registration extern removed','emu/cores/sn764intf.h':'new private configuration fields with changed layout; functional identifiers for retained core','emu/logging.c':'diagnostic logging disabled with newly authored no-op sink; no formatting implementation','emu/logging.h':'new local diagnostic placeholders; no external logging ABI','emu/snddef.h':'own native signed sample typedef','stdtype.h':'own width-checked C integer typedefs'}
for e in old['files']:
 p=SOURCE/e['path'];assert sha(p)==e['sha256']
 history=subprocess.check_output(['git','log','-1','--format=%H %s','--',e['path']],cwd=SOURCE,text=True).strip()
 core=e['path']=='emu/cores/sn76496.c'
 entries.append(dict(path=e['path'],sha256=e['sha256'],explicit_file_grant='BSD-3-Clause' if core else None,
  evidence_class='explicit file-specific declaration' if core else 'provenance known; no applicable grant established in examined sources',
  inferred_provenance=history,separate_license_search='pinned tree/history license/copying filenames; local file notices; public maintainer issues43/129 via read-only connector; no governing grant found for helpers',
  absence_is_not_proof_of_no_license=True,experimental_use='retained BSD computations; includes/registry removed' if core else 'excluded completely',
  replacement=None if core else replacements[e['path']],if_retained_without_replacement='apply BSD notice/conditions/disclaimer' if core else 'clarify applicable file-specific or separate license before distribution'))
references=[dict(url='https://github.com/ValleyBell/libvgm/issues/129#issuecomment-2781054175',meaning='maintainer planned module licensing; intended future licensing is not a current grant'),dict(url='https://github.com/ValleyBell/libvgm/issues/43#issuecomment-797782644',meaning='maintainer discussed possible future licensing, not a completed grant'),dict(url='https://www.mamedev.org/legal.html',meaning='file-specific licences permitted; whole-project licence not inherited by isolated BSD file'),dict(url='https://raw.githubusercontent.com/mamedev/mame/master/src/devices/sound/sn76496.cpp',meaning='upstream PSG BSD declaration corroborates provenance; pinned libvgm file remains actual input')]
save(PUB/'license-matrix.json',dict(parent='549de7543b6704cf9d219d5c87f5a03bf854ec9e',management='6b72e7cd85fe29d938ce4672a7903e60d262732b',core_commit=old['pinned_commit'],entries=entries,sources=references,
 analysis='file-specific evidence supports retaining core; unknown helper grants do not become permission by linking a GPL/BSD file',upstream_contact=False,formal_legal_clearance_claimed=False))
build=json.loads((OUT/'build.json').read_text());imports=pe_imports(OUT/'psg-a1l.dll');assert set(imports)=={'KERNEL32.dll'}
# The compiler-generated make dependencies provide a second independent inventory.
for stem,dep in build['dependencies'].items():
 assert 'libvgm-src' not in dep and 'sonic-chaos-reference-m4' not in dep
 assert 'support.h' in dep
code=[ROOT/'tools/m5a1l'/n for n in ['adapter.c','support.c','support.h']]
symbols={n:coff_symbols(OUT/n) for n in ['adapter.obj','support.obj']}
defined={s['name'] for rows in symbols.values() for s in rows if s['defined']}
unresolved={s['name'] for rows in symbols.values() for s in rows if not s['defined']}-defined
assert unresolved=={'__imp_GetProcessHeap','__imp_HeapAlloc','__imp_HeapFree'}
modules=pdb_modules(OUT/'psg-a1l.pdb')
assert len(modules)==5 and all(any(x in m['module'] for x in ['adapter.obj','support.obj','KERNEL32.dll','* Linker *']) for m in modules)
trace=(OUT/'link-trace.txt').read_text()
archives=[p for p in (OUT/'zig-cache').rglob('*.lib') if p.name in ['c.lib','compiler_rt.lib','kernel32.lib'] and str(p) in trace]
assert {p.name for p in archives}=={'c.lib','compiler_rt.lib','kernel32.lib'}
manifest=dict(build=build,compiled_translation_units=['adapter.obj','support.obj'],compiled_source_closure=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=sha(p),license='MIT') for p in code]+[dict(path='generated/retained_psg.c',sha256=sha(OUT/'retained_psg.c'),license='BSD-3-Clause',input=entries[7]['path'])],
 removed_A0_dependency_files=[e['path'] for e in entries if e['path']!='emu/cores/sn76496.c'],binary_imports=imports,linked_C_runtime=False,full_libvgm_linked=False,full_MAME_linked=False,
 import_library='kernel32 import thunks generated by Zig linker; only API imports, no bundled Windows DLL',object_external_symbols=symbols,unresolved_object_symbols=sorted(unresolved),pdb_contributing_modules=modules,
 linker_archive_inputs=[dict(name=p.name,sha256=sha(p),contribution='import descriptors/thunks only' if p.name=='kernel32.lib' else 'available to linker; no contributing member in PDB, no unresolved runtime symbol') for p in archives],
 compiler=dict(name='Zig',version=build['compiler_version'],role='build-only; no compiler executable redistributed',license='MIT',notice_sha256=sha(ROOT.parent/'sonic-chaos-reference-m4/build/m4/tooldeps/ziglang/LICENSE')),
 notices=['tools/m5a1l/LICENSE-MIT.txt','docs/m5-a1l-THIRD-PARTY-NOTICES.md','original retained PSG preamble/comments'],
 permission_basis='explicit BSD file declaration plus new MIT source; no unclear helper code compiled; not a universal legal warranty',release_fidelity_status='HOLD: Manager must resolve changed resampler PCM or obtain exact-helper permission')
save(PUB/'dependency-manifest.json',manifest);print('14 files audited; source closure4; unresolved A0 helpers13 excluded')

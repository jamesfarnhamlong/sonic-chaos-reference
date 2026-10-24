"""Read-only artifact checks; emit safe build-provenance metadata, never payloads.

No compiler or DLL is executed. No source/notice grant is made by this tool.
"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

from pe import coff_symbols, pdb_modules, pe_imports

ROOT = Path(__file__).resolve().parents[2]
CODE = 'ad6aa301a7cc37a75f36a3d15c4804bcaa37b02b'
AUDIT = '0bf89ade86bfa7a92f7d918fae5f05d77e79b948'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def lf(raw):
    return raw.replace(b'\r\n', b'\n')


def check(ok, label):
    if not ok:
        raise ValueError(label)


def identity(raw):
    return dict(sha256=sha(raw), bytes=len(raw), crlf_count=raw.count(b'\r\n'))


def sections(path, pe=False):
    raw = path.read_bytes()
    base = struct.unpack_from('<I', raw, 0x3c)[0] + 4 if pe else 0
    check(struct.unpack_from('<H', raw, base)[0] == 0x8664, 'AMD64 machine')
    count = struct.unpack_from('<H', raw, base + 2)[0]
    optional = struct.unpack_from('<H', raw, base + 16)[0]
    result = {}
    for i in range(count):
        off = base + 20 + optional + 40 * i
        name = raw[off:off + 8].split(b'\0')[0].decode()
        size, start = struct.unpack_from('<II', raw, off + 16)
        result[name] = sha(raw[start:start + size])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-root', type=Path, required=True)
    parser.add_argument('--audit-root', type=Path, required=True)
    parser.add_argument('--zig-dir', type=Path, required=True)
    parser.add_argument('--upstream-core', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true', help='Verify the frozen receipt without rewriting it')
    args = parser.parse_args()
    for name in ('original_root', 'audit_root', 'zig_dir', 'upstream_core'):
        setattr(args, name, getattr(args, name).resolve())
    historical = json.loads((ROOT / 'data/m5-a1l/dependency-manifest.json').read_text())
    receipt = dict(schema=1, code_commit=CODE, accepted_audit_commit=AUDIT,
                   status='PROPOSAL ONLY; PROV-1 PENDING HUMAN APPROVAL; STOP for Manager review',
                   policy='Approved maximum 5 signed16 LSB for accepted controls unchanged',
                   source_inputs=[], builds={}, import_generation_inputs=[],
                   source_distribution=[], binary_distribution=[])
    originals = args.original_root / 'build/m5-a1l'
    reviewed = args.audit_root / 'build/m5-a1l'
    source_paths = ['tools/m5a1l/' + n for n in ('adapter.c', 'support.c', 'support.h')]
    manifests = {label: json.loads((out / 'build.json').read_text())
                 for label, out in [('original', originals), ('audit_rebuild', reviewed)]}
    check(manifests['original'] == historical['build'], 'historical build receipt')

    def package_entry(destination, raw, origin, role):
        return dict(path=destination, sha256=sha(raw), bytes=len(raw), origin=origin, role=role)

    for path in source_paths:
        blob = subprocess.check_output(['git', 'show', CODE + ':' + path], cwd=ROOT)
        check(b'\r' not in blob, 'LF Git content: ' + path)
        row = dict(path=path, git_lf=identity(blob))
        for label, root in [('original', args.original_root), ('audit_rebuild', args.audit_root)]:
            raw = (root / path).read_bytes()
            expected = {k.replace('\\', '/'): v for k, v in manifests[label]['inputs'].items()}
            check(sha(raw) == expected[path], 'raw source receipt: ' + label + path)
            check(lf(raw) == blob, 'normalized source equals Git: ' + label + path)
            row[label] = identity(raw)
        check(lf((ROOT / path).read_bytes()) == blob, 'continuation source unchanged')
        receipt['source_inputs'].append(row)
        raw = (args.original_root / path).read_bytes()
        receipt['source_distribution'].append(package_entry(
            'src/' + Path(path).name, raw, 'original build raw ' + path, 'MIT proposal; PROV-1 pending'))

    upstream = args.upstream_core.read_bytes()
    check(sha(upstream) == historical['build']['core_source_sha256'], 'pinned upstream core')
    text = lf(upstream).decode()
    start, end = text.index('static DEVDEF_RWFUNC devFunc[]'), text.index('#define MAX_OUTPUT')
    extracted = re.sub(r'^#include[^\r\n]*\r?\n', '', text[:start] + text[end:], flags=re.M)
    core = (originals / 'retained_psg.c').read_bytes()
    check(lf(core).decode() == extracted, 'mechanical core extraction and complete preamble')
    check(b'#include' not in core, 'no upstream includes')
    body = lf(core)[lf(core).index(b'#define MAX_OUTPUT'):]
    check(sha(body) == historical['build']['retained_body_sha256'], 'unchanged PSG body')
    receipt['upstream'] = dict(commit='a6eed945ecf4e5a25cf82004779c6f7e4fd5c319',
        path='emu/cores/sn76496.c', sha256=sha(upstream), retained_body_lf_sha256=sha(body),
        generated_raw=identity(core), complete_preamble_and_extraction='PASS')
    receipt['source_distribution'].append(package_entry(
        'generated/retained_psg.c', core, 'original build generated core', 'BSD-3-Clause; full preamble retained'))

    mingw = args.zig_dir / 'lib/libc/mingw'
    for name, expected in [
        ('lib-common/kernel32.def.in', '2b956e88d266cf6c0371011764822faad003397b24a27caf04caa74a322c2d44'),
        ('def-include/func.def.in', '431d2f5dc67ddba5db340ea029b6380021e5c10115ddd2ccb8c626357a29f86a'),
        ('COPYING', '99a69660981156c21336fdb5661f89341b013c94e4bf9e1c7467b4745718397f')]:
        raw = (mingw / name).read_bytes()
        check(sha(raw) == expected, 'bundled mingw input ' + name)
        receipt['import_generation_inputs'].append(dict(path='lib/libc/mingw/' + name, **identity(raw)))
    copied = (ROOT / 'docs/notices/m5-a1l/mingw-w64-COPYING.txt').read_bytes()
    check(copied == (mingw / 'COPYING').read_bytes(), 'verbatim bundled notice')
    check(not list(args.zig_dir.rglob('AUTHORS*')), 'update absent AUTHORS assessment')
    receipt['mingw_notice_basis'] = dict(default='ZPL-2.1 with marked exceptions',
        attribution='Copyright (c) 2009 - 2013 by the mingw-w64 project',
        file_specific_override_found=False, referenced_AUTHORS='absent in examined Zig installation',
        treatment='Carry complete bundled COPYING; Manager review pending')
    receipt['compiler'] = dict(name='Zig', version='0.13.0', host_target='Windows x86_64',
        executable_sha256=sha((args.zig_dir / 'zig.exe').read_bytes()),
        license_sha256=sha((args.zig_dir / 'LICENSE').read_bytes()), redistributed=False)

    expected_imports = {'KERNEL32.dll': ['GetProcessHeap', 'HeapAlloc', 'HeapFree']}
    executable_hashes = {}
    for label, root, out in [('original', args.original_root, originals),
                             ('audit_rebuild', args.audit_root, reviewed)]:
        manifest = manifests[label]
        check(manifest['compiler_version'] == '0.13.0', 'compiler version')
        files = dict(manifest['objects'], **{'psg-a1l.dll': manifest['binary_sha256'],
            'psg-a1l.pdb': manifest['pdb_sha256'], 'retained_psg.c': manifest['retained_psg_sha256'],
            'link-trace.txt': manifest['link_trace_sha256']})
        checked_files = {}
        for name, expected in files.items():
            raw = (out / name).read_bytes()
            check(sha(raw) == expected, 'build artifact ' + label + name)
            checked_files[name] = identity(raw)
        check((out / 'retained_psg.c').read_bytes() == core, 'same generated source')
        dependencies = {}
        for stem, names in [('adapter', ['adapter.c', 'support.h', 'retained_psg.c']),
                            ('support', ['support.c', 'support.h'])]:
            dep_raw = (out / (stem + '.d')).read_bytes()
            dep = dep_raw.decode().replace('\r\n', '\n')
            check(dep == manifest['dependencies'][stem], 'dependency receipt')
            # The make format stores one dependency per continued line.
            actual = re.findall(r'(?:[A-Za-z]:/)[^\n]+',
                                dep.split(': ', 1)[1].replace('\\ ', ' ').replace(' \\\n', '\n'))
            wanted = [(root / 'tools/m5a1l' / n).as_posix() if n != 'retained_psg.c'
                      else (out / n).as_posix() for n in names]
            check(sorted(x.strip() for x in actual) == sorted(wanted), 'exact compiler closure')
            dependencies[stem + '.obj'] = dict(sha256=sha(dep_raw), inputs=names)
        symbols = {n: coff_symbols(out / n) for n in manifest['objects']}
        defined = {s['name'] for rows in symbols.values() for s in rows if s['defined']}
        unresolved = {s['name'] for rows in symbols.values() for s in rows if not s['defined']} - defined
        check(unresolved == {'__imp_' + x for x in expected_imports['KERNEL32.dll']}, 'object closure')
        check(pe_imports(out / 'psg-a1l.dll') == expected_imports, 'PE imports')
        modules = pdb_modules(out / 'psg-a1l.pdb')
        check(len(modules) == 5, 'five PDB modules')
        module_names = [m['module'].replace('\\', '/').rsplit('/', 1)[-1] for m in modules]
        check(sorted(module_names) == sorted(['adapter.obj', 'support.obj', 'KERNEL32.dll',
                                             'Import:KERNEL32.dll', '* Linker *']), 'PDB contributions')
        trace = (out / 'link-trace.txt').read_text()
        archives = {}
        for archive in historical['linker_archive_inputs']:
            matches = [x for x in (out / 'zig-cache').rglob(archive['name'])
                       if str(x) in trace or x.as_posix() in trace]
            check(len(matches) == 1, 'unique selected archive')
            archive_path = matches[0]
            archive_hash = sha(archive_path.read_bytes())
            if label == 'original' or archive['name'] == 'kernel32.lib':
                check(archive_hash == archive['sha256'], 'historical/import archive hash')
            archives[archive['name']] = dict(sha256=archive_hash, contribution=archive['contribution'])
            if archive['name'] == 'kernel32.lib':
                definition = archive_path.with_suffix('.def').read_bytes()
                check(all(x.encode() in definition.splitlines() for x in expected_imports['KERNEL32.dll']),
                      'cached API definitions')
                receipt.setdefault('generated_definition', {})[label] = identity(definition)
        cache = out / 'zig-cache/h/ece1e5e76db1d46e8001aca2f659ec99.txt'
        check('libc\\mingw\\lib-common\\kernel32.def.in' in cache.read_text(), 'cache top-level input')
        texts = {name: sections(out / name, name.endswith('.dll'))['.text']
                 for name in ['adapter.obj', 'support.obj', 'psg-a1l.dll']}
        executable_hashes[label] = texts
        # Replace only known build/toolchain roots; never publish raw local command paths.
        substitutions = [(str(root), '${BUILD_ROOT}'), (str(args.zig_dir), '${ZIG_DIR}')]
        commands = []
        for command in manifest['commands']:
            normalized = []
            for arg in command:
                for old, new in substitutions:
                    arg = arg.replace(old, new)
                check(not re.search(r'[A-Za-z]:[\\/]', arg), 'sanitized build command')
                normalized.append(arg)
            commands.append(normalized)
        receipt['builds'][label] = dict(artifacts=checked_files, dependencies=dependencies,
            commands=commands, imports=expected_imports, unresolved=sorted(unresolved),
            pdb_modules=module_names, archives=archives, text_sha256=texts,
            build_receipt_sha256=sha((out / 'build.json').read_bytes()),
            cache_receipt_sha256=sha(cache.read_bytes()))
    check(executable_hashes['original'] == executable_hashes['audit_rebuild'], 'paired executable sections')
    receipt['whole_binary_identical'] = manifests['original']['binary_sha256'] == manifests['audit_rebuild']['binary_sha256']
    receipt['paired_text_sections_identical'] = True
    receipt['binary_distribution'].append(package_entry('psg-a1l.dll',
        (originals / 'psg-a1l.dll').read_bytes(), 'original build; payload remains private', 'binary proposal only'))
    for path, destination, role in [
        ('docs/m5-a1l-THIRD-PARTY-NOTICES.md', 'notices/THIRD-PARTY-NOTICES.md', 'complete BSD and integration notices'),
        ('tools/m5a1l/LICENSE-MIT.txt', 'notices/LICENSE-MIT.txt', 'MIT proposal; PROV-1 pending'),
        ('docs/notices/m5-a1l/mingw-w64-COPYING.txt', 'notices/mingw-w64-COPYING.txt', 'complete bundled mingw-w64 notice'),
        ('docs/m5-a1l-component-build.md', 'README.md', 'build/provenance and pending-approval instructions')]:
        # Package documentation uses stable LF. COPYING is preserved byte-for-byte.
        raw = (ROOT / path).read_bytes()
        if not path.endswith('mingw-w64-COPYING.txt'):
            raw = lf(raw)
        for field in ['source_distribution', 'binary_distribution']:
            receipt[field].append(package_entry(destination, raw, path, role))
    receipt['inventory_rules'] = dict(source_inputs='Original build raw bytes; Git LF comparison recorded separately',
        documentation='LF except verbatim bundled COPYING', inventory='External receipt; no self hash',
        no_payload_copied=True, no_compiler_or_DLL_executed=True,
        excluded=['ROM', 'WAV', 'state/event/music data', 'private proof ZIP', 'PDB', 'objects',
                  'import libraries', 'toolchain', 'Python runtime/utilities', 'A0 source',
                  'libvgm helpers', 'GameMaker/POC wrapper'])
    encoded = (json.dumps(receipt, indent=2) + '\n').encode()
    if args.check:
        check(lf(args.output.read_bytes()) == encoded, 'frozen receipt changed')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded)
    print('PASS: source/build/notice mappings; 8 source and 5 binary proposed files; no payload copied')


if __name__ == '__main__':
    main()

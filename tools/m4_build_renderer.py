"""Private Windows build of the existing pinned AUDIO-1B libvgm renderer.

Prerequisites in build/m4/: tooldeps (pip cmake ninja ziglang==0.13.0),
renderer/libvgm-src at AUDIO-1B pin, renderer/zlib-src at zlib v1.3.1.
No third-party code or binaries are published by this script.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'build/m4'
PIN='a6eed945ecf4e5a25cf82004779c6f7e4fd5c319'
ZPIN='51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf'

def run(args, **kw):
    subprocess.run([str(x) for x in args],check=True,**kw)

def main():
    src=B/'renderer/libvgm-src'; zs=B/'renderer/zlib-src'
    for path,pin in ((src,PIN),(zs,ZPIN)):
        assert subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()==pin
    zig=B/'tooldeps/ziglang/zig.exe'
    cmake=B/'tooldeps/cmake/data/bin/cmake.exe'
    ninja=B/'tooldeps/bin/ninja.exe'
    tc=B/'renderer/toolchain';tc.mkdir(parents=True,exist_ok=True)
    for name,args in (('cc','cc'),('cxx','c++'),('ar','ar'),('ranlib','ranlib')):
        (tc/f'{name}.cmd').write_text(f'@echo off\n"{zig}" {args} %*\n')
    tool=tc/'zig.cmake'
    tool.write_text('\n'.join([
        'set(CMAKE_SYSTEM_NAME Windows)',
        f'set(CMAKE_C_COMPILER "{(tc/"cc.cmd").as_posix()}")',
        f'set(CMAKE_CXX_COMPILER "{(tc/"cxx.cmd").as_posix()}")',
        f'set(CMAKE_AR "{(tc/"ar.cmd").as_posix()}")',
        f'set(CMAKE_RANLIB "{(tc/"ranlib.cmd").as_posix()}")',
        'set(CMAKE_C_FLAGS_INIT "-target x86_64-windows-gnu")',
        'set(CMAKE_CXX_FLAGS_INIT "-target x86_64-windows-gnu")',
    ])+'\n')
    env=dict(os.environ,ZIG_GLOBAL_CACHE_DIR=str(B/'zig-cache'),ZIG_LOCAL_CACHE_DIR=str(B/'zig-local'),
             TEMP=str(B/'tmp'),TMP=str(B/'tmp'))
    (B/'tmp').mkdir(exist_ok=True)
    common=['-G','Ninja',f'-DCMAKE_MAKE_PROGRAM={ninja}',f'-DCMAKE_TOOLCHAIN_FILE={tool}',
            '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_POLICY_VERSION_MINIMUM=3.5']
    zb=B/'renderer/zlib-build'
    run([cmake,'-S',zs,'-B',zb,*common,'-DZLIB_BUILD_EXAMPLES=OFF'],env=env)
    run([cmake,'--build',zb,'--target','zlibstatic','-j','4'],env=env)
    # zlib CMake generates zconf.h in the binary directory.
    shutil.copyfile(zs/'zlib.h',zb/'zlib.h')
    p=src/'vgm2wav.cpp';s=p.read_text()
    marker='    // set_core(plrEngine,DEVID_YM2612,FCC_NUKE);'
    patch=marker+'\n    if (getenv("VGM_SN_CORE")) {\n        const char* c = getenv("VGM_SN_CORE");\n        set_core(plrEngine, DEVID_SN76496, !strcmp(c, "MAXM") ? FCC_MAXM : FCC_MAME);\n    }'
    if 'VGM_SN_CORE' not in s:
        assert marker in s;p.write_text(s.replace(marker,patch))
    vb=B/'renderer/libvgm-build'
    run([cmake,'-S',src,'-B',vb,*common,'-DBUILD_PLAYER=OFF','-DBUILD_LIBAUDIO=OFF',
        '-DBUILD_TESTS=OFF','-DUSE_SANITIZERS=OFF','-DBUILD_VGM2WAV=ON',
        '-DLINK_STATIC_LIBS=OFF','-DSNDEMU__ALL=OFF','-DSNDEMU_SN76496_MAME=ON',
        f'-DZLIB_LIBRARY={zb/"libzlibstatic.a"}',f'-DZLIB_INCLUDE_DIR={zb}'],env=env)
    run([cmake,'--build',vb,'--target','vgm2wav','-j','4'],env=env)
    exe=vb/'bin/vgm2wav.exe'
    manifest=dict(libvgm_commit=PIN,zlib_commit=ZPIN,compiler='Zig 0.13.0 cc/c++ x86_64-windows-gnu',
        core='MAME only; SNDEMU__ALL=OFF, SNDEMU_SN76496_MAME=ON; VGM_SN_CORE=MAME',
        build_patch='same AUDIO-1B environment-based set_core patch',
        vgm2wav_cpp_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        binary_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),executable=str(exe))
    (B/'renderer/build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()

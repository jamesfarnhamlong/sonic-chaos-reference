# M5-A1L required third-party notices and attribution

This is the notice inventory for the dependency-reduced experiment, not a notice that all of MAME/libvgm has been licensed to this project. The exact build closure is in `data/m5-a1l/dependency-manifest.json`.

## Retained PSG

Source: ValleyBell/libvgm, commit `a6eed945ecf4e5a25cf82004779c6f7e4fd5c319`, `emu/cores/sn76496.c`, SHA-256 `91e6d92121bd94466c6971c6a3b52adb2016930cc29fa38caa2fdf9a49e98ab3`.

Original file declarations, retained verbatim:

```text
// license:BSD-3-Clause
// copyright-holders:Nicola Salmoria
```

Retain the complete original preamble and historical contributor comments in any source distribution. Names recorded there include Nicola Salmoria, Sebastien Chevalier, Lord Nightmare, Michael Zapf, Enik, ValleyBell, Qbix, NewRisingSun and referenced testers/contributors. This inventory is not a replacement for the actual original notices and does not invent contribution years or transfer their ownership.

BSD 3-Clause conditions and disclaimer accompanying this component:

```text
Copyright: Nicola Salmoria, as identified by the retained source declaration,
with contributions by others as preserved in the source notices.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

Modification notice, 24 October 2026: the experiment removes external includes and libvgm device-registration metadata, supplies new private declarations and support implementations, and retains the PSG body starting at `MAX_OUTPUT` unchanged after LF normalization. It does not rewrite tone/noise/register calculations. The build verifies both original and retained-body hashes. Do not use MAME branding to imply endorsement.

## New component code

`tools/m5a1l/adapter.c`, `support.c`, `support.h` and the new audit/build/comparison utilities are offered under their scoped MIT licence in `tools/m5a1l/LICENSE-MIT.txt`. Include that licence in a later source/binary package. It does not apply to upstream code or original music/event data.

## Toolchain and platform

Zig 0.13.0 is build-only and has its own MIT licence; preserve its original notice if distributing the toolchain. This experiment uses `-nostdlib` and two fully inventoried objects. It includes no libvgm helper, C/compiler-runtime implementation or whole MAME library. Zig offers `c.lib` and `compiler_rt.lib` as archive inputs, but the exact object symbol closure and PDB contributing-module list establish that no members enter this binary. The archive hashes and the actual link trace are inventoried rather than treating `-nostdlib` alone as proof. The Windows binary imports only `GetProcessHeap`, `HeapAlloc` and `HeapFree` from the operating system's `KERNEL32.dll`. Do not bundle Windows system DLLs. Kernel32 import thunks are linker-generated API references, not a bundled CRT implementation.

The build manifests and PE-import inspection together establish this particular binary closure. A different compiler, target, build flag or extension wrapper needs a fresh audit; import inspection alone would not prove absence of a statically linked runtime. The generated `_tls_index` placeholder is local code for Zig's Windows DLL link, and no thread-local runtime is used.

Excluded: all 13 unclear libvgm helpers/headers from A0, other MAME cores, VGM parser/player, original ROM/Z80 code, original note/envelope data and audio. If any excluded source is later reintroduced, these notices and this audit do not supply its permission.

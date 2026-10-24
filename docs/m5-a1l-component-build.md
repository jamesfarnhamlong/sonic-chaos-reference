# M5-A1L component source/binary proposal

24 October 2026. **Proposal only — PROV-1 PENDING HUMAN APPROVAL; distribution requires Manager review.** This README is proposed alongside both source and binary materials. No release package has been produced by this continuation.

The paired source files are `src/adapter.c`, `src/support.c`, `src/support.h`, and `generated/retained_psg.c`. Their raw hashes map to the original 6,656-byte AMD64 DLL with SHA-256 `47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65`. The original source inputs are preserved byte-for-byte, including mixed line endings; their CRLF-to-LF contents equal the reviewed Git blobs. The external `provenance-closure.json` inventory records both representations. Hashes must be refreshed for any subsequently changed material.

Required accompanying materials: `notices/THIRD-PARTY-NOTICES.md` (complete BSD terms and integration/provenance notices), `notices/LICENSE-MIT.txt` (current proposed notice; pending rightsholder/scope approval), `notices/mingw-w64-COPYING.txt` (complete bundled ZPL-2.1/default notice), and this `README.md`. The generated PSG source retains the complete upstream historical preamble. The BSD core is from ValleyBell/libvgm commit `a6eed945ecf4e5a25cf82004779c6f7e4fd5c319`, `emu/cores/sn76496.c`. Modification notice, 24 October 2026: external includes and registration metadata removed, local support supplied; `MAX_OUTPUT`-through-EOF body unchanged after LF normalization. Do not imply MAME, libvgm or mingw-w64 endorsement.

Build environment: external Zig 0.13.0 for x86_64 Windows, its original bundled mingw-w64 definition inputs and a writable private cache. Compiler, Windows DLLs and Python runtime are not included. For the proposed relocated layout, run these PowerShell commands from the package root (with `zig` resolving to that compiler); make the `build` directory first:

```powershell
New-Item -ItemType Directory -Path build -Force | Out-Null
zig cc -c -O2 -ffreestanding -fno-builtin -fno-stack-protector -I generated -I src -MD -MF build/adapter.d src/adapter.c -o build/adapter.obj
zig cc -c -O2 -ffreestanding -fno-builtin -fno-stack-protector -I generated -I src -MD -MF build/support.d src/support.c -o build/support.obj
zig cc -shared -nostdlib -Wl,--entry,a1_dll_entry build/adapter.obj build/support.obj -lkernel32 -o build/psg-a1l.dll -v
```

These use the original compilation/link flags and new paths. The existing builds used the same options without an explicit target and were verified as AMD64. Use the specified Windows compiler environment; another host/target requires a fresh audit. This is an instruction transcription, not a new tested rebuild or promise of byte-identical DLL/PDB reproduction across paths/caches. Preserve dependencies and verbose link output and make a new receipt before pairing any rebuilt DLL with a distribution.

The exact audited DLL imports only `GetProcessHeap`, `HeapAlloc`, `HeapFree` from the operating system's `KERNEL32.dll`. Zig preprocesses bundled `kernel32.def.in` and `func.def.in` to make an import library; carry the supplied mingw-w64 notice conservatively. Its referenced AUTHORS file is absent from the examined Zig distribution; no historical author list has been invented. No CRT implementation was identified in the two audited builds; this conclusion needs rechecking after build changes.

The approved bounded numerical policy allows measured differences up to 5 signed16 LSB for the accepted controls; it is not MAME sample identity or an untested universal bound. This component contains no ROM/music/event data and conveys no rights to them. The current MIT attribution and reuse of the A0 project wrapper require the scoped human declaration specified in the closure report. Do not treat this unsigned proposal as resolving ownership or employer/client authority.

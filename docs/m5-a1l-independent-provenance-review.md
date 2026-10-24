# M5-A1L-PROV — independent dependency and provenance review

**Verdict: CONDITIONAL GO.** Documented source and verified object evidence support the narrow BSD/MIT component strategy. No substantial copied implementation from the thirteen unclear libvgm dependencies was identified. Before redistribution, complete the four bounded actions below: confirm the project-code licensing authority and inherited A0 provenance, make the source manifest portable, document the import-library definition inputs, and verify the actual distribution's notice set and scope. This is an engineering provenance assessment, not a determination of copyright ownership or universal legal clearance.

Assistant Manager-san, 24 October 2026. Reviewed Research `research/m5-a1l-licensing@ad6aa301a7cc37a75f36a3d15c4804bcaa37b02b`; management authority read through authenticated GitHub at `main@a0849c93bcfb6aef2482d6da1fe0392bd00f3598` (AGENTS, MEMORY and ROADMAP). Audit branch is a separate direct descendant of the reviewed Research commit; management documents were not installed or merged.

Manager has accepted the measured maximum 5 signed16 LSB difference for continued development. This review does not reopen that decision, assert MAME sample identity, or extend the bound to untested controls. Research's prior exposure to the old resampler is acknowledged: **this was not formal clean-room development**.

## 1. Required actions before redistribution

| ID | Required action | Evidence and closure criterion |
|---|---|---|
| PROV-1 | Record the responsible human/rightsholder's approval of the scoped MIT grant, including earlier A0 wrapper material reused in A1L. Amend the provenance wording accordingly. | `tools/m5a1l/LICENSE-MIT.txt:3,25` uses the collective name “Sonic Chaos reference contributors” and describes newly authored files only. `adapter.c:11–17,34–42` reuses/adapts project-authored initialization, writes, state reporting and benchmark scaffolding from `tools/m5a0/psg_adapter.c` at parent `549de7543b6704cf9d219d5c87f5a03bf854ec9e`. That predecessor already declares MIT, but code history alone cannot establish who can license every contribution. Record contributors/authority, any employer or third-party constraints, and confirmation that no unrecorded external implementation was incorporated into the replacement. Do not require an upstream permission request for excluded helpers. |
| PROV-2 | Add committed/LF-normalized source hashes alongside exact build-input hashes, state the newline policy, and freeze a source-to-binary receipt for the eventual package. | The current manifest accurately hashes the original local files, but its three MIT source hashes do not equal Git blob bytes or a fresh Windows checkout. See section 5. This is a line-ending reproducibility defect, not an unexplained code substitution. A documented checkout/package normalization plus exact packaged-input hashes closes it; no runtime algorithm change is required. |
| PROV-3 | Expand the build-input inventory for Kernel32 import-library generation. | The supplied manifest hashes `kernel32.lib` but describes only Zig-generated API thunks. Zig 0.13.0 also consumes bundled mingw-w64 definition inputs; paths/hashes are in section 4. Record those inputs and their notice basis. A conservative sufficient documentation route is to accompany the build/source handoff with the bundled mingw-w64 `COPYING` and relevant attribution, and include that notice with the eventual binary to avoid relying on an unreviewed exemption. This does not mean a mingw CRT implementation entered the DLL or that three API names establish protected-expression copying. |
| PROV-4 | Assemble and check the actual intended source/binary notice inventory; obtain Manager's distribution approval. | The existing BSD and MIT texts are substantively adequate for their stated components **when actually carried with the distribution**. The private review ZIP carries both, but is not a complete buildable source package. Use section 6's inventory, preserve the exact PSG preamble, and map packaged files to hashes. Do not distribute the private proof ZIP as a component release: it also contains diagnostic audio/state outside this review's rights scope. Any future host wrapper needs its own delta audit. |

These conditions permit continued isolated engineering under existing management authority. They do not authorize binary publication, accepted POC integration, a merge, or upstream contact. If the human provenance confirmation discloses substantial externally copied expression without a grant, change the verdict to HOLD until that specific material is resolved.

## 2. Retained PSG and attribution

Actual upstream input is ValleyBell/libvgm commit `a6eed945ecf4e5a25cf82004779c6f7e4fd5c319`, [emu/cores/sn76496.c](https://github.com/ValleyBell/libvgm/blob/a6eed945ecf4e5a25cf82004779c6f7e4fd5c319/emu/cores/sn76496.c), SHA-256 `91e6d92121bd94466c6971c6a3b52adb2016930cc29fa38caa2fdf9a49e98ab3`. Local pinned checkout is `sonic-chaos-reference-m4/build/m4/renderer/libvgm-src` beside this worktree. Its unrelated modified `vgm2wav.cpp` is not a component input; all fourteen audited input files independently match the recorded hashes.

The file explicitly declares BSD-3-Clause and Nicola Salmoria as copyright holder (lines 1–2). Its complete opening historical comment credits Salmoria and contributions/testing by Sebastien Chevalier, Lord Nightmare, Michael Zapf, Enik, ValleyBell, Qbix, NewRisingSun, PlgDavid and Nemesis, including dated changes. The acknowledgement is more detailed than the abbreviated notice inventory; preserve the original comment, rather than replacing it with a shortened author list or invented ownership years.

`tools/m5a1l/build.py:7–10` checks the original raw hash, removes external includes and the `devFunc`/`devDef_SN76496_MAME` registration block before `MAX_OUTPUT`, and writes `build/m5-a1l/retained_psg.c`. I verified the full initial preamble is preserved, no include directives survive, and **all text from `#define MAX_OUTPUT` to EOF is identical after LF normalization**. This includes the core structs, tone/noise/register logic, counters, initialization and volume calculations. Retained-body SHA-256 is `fe45270980c6389ed337b0cbacde4211cb3a4069751e42dbc095173853158b25`; generated file raw SHA-256 is `9d18a1f7aeecf5124ebd5da931668e75d595d3a448dc40384e2123ce941d9afc` on both local builds.

The surrounding integration has changed: initialization macros, configuration types, logging and memory/math services are supplied locally. Thus “unchanged PSG body” is accurate; “unchanged complete source/environment” would not be. The dated integration-change notice in `docs/m5-a1l-THIRD-PARTY-NOTICES.md:48` accurately describes the mechanical changes. Also place that notice prominently in any separately shipped generated source (recommended provenance hygiene; BSD-3-Clause itself does not impose an Apache-style change-log condition).

The file-specific declaration and [MAME's official licensing policy](https://www.mamedev.org/legal.html) support the isolated BSD file assessment, not licensing of the entire libvgm/MAME tree. Missing helper headers are not evidence of infringement; absence of a documented grant is not proof none exists.

## 3. Replacement comparison and all thirteen excluded dependencies

I read the three replacement C files and compared them with the exact pinned helpers and the earlier A0 adapter. `tools/m5a1l/adapter.c:18–32` integrates one piecewise-constant native sample at a time, retaining `phase/have/sample` across calls. In contrast, pinned `emu/Resampler.c:359` onward (`Resmpl_Exec_LinearDown`) pregenerates arrays and handles first/last fractional samples plus interior samples through 11-bit fixed-point coordinates, with callback-sized lookahead, overflow adjustment and second-based position rebasing. Both perform area averaging; the A1L loop, state representation and control flow differ materially. I found no copied coefficient bank, old macros/comments, multi-mode dispatcher, buffer manager or line-by-line translated resampler body. Numerical divergence alone would not establish independent authorship; the source comparison is the relevant evidence here.

`support.c:10–24` supplies a checked heap-allocation product, Windows heap calls, a byte-fill loop, a restricted exponential Taylor series and a trivial DLL entry function. No old logging formatter, resampler allocator or general libm implementation appears there. The ln(2) constant and Taylor recurrence express mathematics; the provenance assertion that the implementation was authored from that specification remains subject to PROV-1.

| Excluded pinned path | Compared replacement / retained overlap |
|---|---|
| `_stdbool.h` | No bool compatibility machinery needed or copied. |
| `common_def.h` | `support.h:13` supplies the ordinary `static inline` spelling; no compiler-selection implementation. |
| `stdtype.h` | `support.h:7–11,17` supplies primitive width-checked C typedefs. Familiar names and primitive type choices remain, without the old portability branches or comments. |
| `emu/snddef.h` | `support.h:8,20` supplies `DEV_SMPL` and the one-pointer `DEV_DATA` compatibility type. `chipInf` is a functional member expected by the licensed core; this small declaration is acknowledged overlap, not evidence of an independent ABI invention. |
| `emu/EmuCores.h` | Core-ID registry omitted entirely. |
| `emu/EmuStructs.h` | `support.h:18–27` uses a callback signature and minimal private types. `DEV_INFO` reverses the two needed fields and omits the registry/link machinery; generic config keeps only clock/rate. No complete original structure/API collection is included. |
| `emu/EmuHelper.h` | `support.h:28` assigns the two needed outputs in a small macro. No old helper body, pow2 utilities or compatibility math code. |
| `emu/Resampler.h` | No old API or `RESMPL_STATE` definition; the adapter owns its different state. |
| `emu/Resampler.c` | Replaced by the rational integration loop above. |
| `emu/cores/sn76496.h` | Unneeded external registration declaration omitted. |
| `emu/cores/sn764intf.h` | `support.h:22–27` retains functional configuration field names/types consumed by the core, groups fields differently and moves `t6w28_tone`; no variant configuration table or commentary copied. Write-selector numeric constants remain ordinary interface facts. |
| `emu/logging.h` | Names/signatures needed by the core survive; the old callback-storage struct and setter body do not. Local logger is an unused placeholder with no-op functions. |
| `emu/logging.c` | No formatter, varargs handling, scratch buffer or dispatch implementation survives. |

The claim should therefore be **“all thirteen original files excluded; minimal functional declarations retained/re-expressed”**, rather than an absolute claim of zero shared identifiers or source expression. I identified no substantial protected implementation from those files in the replacement. Whether any particular minimal interface element is legally protectable is not established by this engineering audit.

As a supplementary check, a comment-stripped, identifier-preserving token comparison across all 39 replacement/helper pairs found longest exact runs of 6 tokens for `adapter.c`, 11 for `support.h` (callback-declaration boundary), and 4 for `support.c`. Against `Resampler.c` specifically the maxima were 6/4/4, all generic syntax. This is a triage check, not a plagiarism detector or proof against renamed/structurally translated copying; the manual algorithm and type comparison above addresses that limitation.

Earlier project MIT code is a distinct provenance path. The A0 initialization/write/state/benchmark scaffolding is visibly reused in A1L. Both commits name the same repository author, and the A0 adapter declares MIT, but that does not independently establish the human rightsholder. PROV-1 should identify this lineage explicitly instead of describing every adapter line as newly originated at A1L.

All new `tools/m5a1l` Python files were inspected too: build/extraction, manifest audit, PE/COFF/PDB readers, comparison and private packaging. They are not compiled into the DLL. Comparison/package utilities import earlier project modules, NumPy and Python facilities; the scoped MIT file does not relicense those dependencies. A runtime-only component needs none of those Python packages. A separately redistributed tool bundle must inventory what it actually ships; do not infer its licence closure from the four C inputs.

## 4. Compiled and linked dependency closure

I independently rebuilt in this isolated worktree with the existing Zig 0.13.0 and exact `build.py` commands. Initial sandboxed compilation failed with Zig's `Unexpected` diagnostic; the approved unrestricted retry succeeded. No compiler/source flags were changed. The original experimental worktree and its build products were read only.

Compiler dependency lists on disk match the original manifest. Fresh lists show exactly:

```text
adapter.obj <- tools/m5a1l/adapter.c
               tools/m5a1l/support.h
               build/m5-a1l/retained_psg.c
support.obj <- tools/m5a1l/support.c
               tools/m5a1l/support.h
```

There are no standard headers, old helper paths or additional translation units in this closure. `build.py:15` uses `-O2 -ffreestanding -fno-builtin -fno-stack-protector`; `:16` links `-shared -nostdlib` with explicit `a1_dll_entry`, the two objects and `-lkernel32`. Actual link traces also show `-NODEFAULTLIB` **and explicit `c.lib` and `compiler_rt.lib` arguments**. `-nostdlib` alone is therefore insufficient evidence of exclusion.

Both original and rebuilt object symbol tables resolve internally except `__imp_GetProcessHeap`, `__imp_HeapAlloc`, `__imp_HeapFree`. Both linked PDBs list five modules: adapter object, support object, Kernel32 descriptor/import modules, and linker-generated material; no `c.lib` or `compiler_rt.lib` contributing member appears. This agrees with the explicit trace, lack of runtime external references, and fresh matching executable sections. No C/compiler-runtime implementation was identified in these exact binaries. Generated instructions and standard object/unwind metadata still exist; the claim is not that the linker contributes no bytes.

PE32+ import inspection independently matches `KERNEL32.dll` with exactly those three heap APIs. Delay-import and TLS directories are zero. `_tls_index` is the locally defined placeholder in `support.c:7`; no TLS runtime or CRT startup is used. No Windows system DLL should be bundled. This evidence says nothing about runtime host-process dependencies or a future GameMaker wrapper.

Original archive hashes were independently checked:

| Linker input | SHA-256 | Observed contribution |
|---|---|---|
| `c.lib` | `2e30ae3f2e25dc919122b8f1270573d19ecb01cfb7ab9948db7c894cf25723a2` | Available, no contributing member identified. |
| `compiler_rt.lib` | `a75e32a2491729a6fcf1164b1404e0ebcb6404152632826b2b23da2f68d2703d` | Available, no contributing member identified. |
| `kernel32.lib` | `aee6eb7cb63c6fc9a4e64f3ab63399f440eeb8cdb81e2df30b032f4f4ded9080` | Import descriptors/thunks. Relevant entries are standard AMD64 short-import objects naming the three APIs, not heap implementations. |

**Additional build provenance:** Zig's bundled `lib/libc/mingw/lib-common/kernel32.def.in` lists the APIs (lines 740,892,898), includes `def-include/func.def.in`, and is preprocessed into cached `kernel32.def`. Both original and rebuilt cache receipts `zig-cache/h/ece1e5e76db1d46e8001aca2f659ec99.txt` identify that definition input. [Zig 0.13.0's import-library selection code](https://github.com/ziglang/zig/blob/0.13.0/src/mingw.zig#L307-L354) corroborates the definition-file selection. These are build-generation inputs, distinct from the four compiler-dependency files. Relevant bundled files:

| File relative to Zig installation | SHA-256 |
|---|---|
| `lib/libc/mingw/lib-common/kernel32.def.in` | `2b956e88d266cf6c0371011764822faad003397b24a27caf04caa74a322c2d44` |
| `lib/libc/mingw/def-include/func.def.in` | `431d2f5dc67ddba5db340ea029b6380021e5c10115ddd2ccb8c626357a29f86a` |
| `lib/libc/mingw/COPYING` | `99a69660981156c21336fdb5661f89341b013c94e4bf9e1c7467b4745718397f` |

The bundled COPYING states a ZPL-2.1 default with explicitly marked exceptions, credits mingw-w64 2009–2013 and references AUTHORS. The examined definition inputs have no separate file-specific grant overriding that default. This is an overlooked documentation input, not demonstrated inclusion of a new runtime implementation. Preserve the bundled notice and applicable attribution as PROV-3's conservative route; do not label the whole toolchain solely MIT or infer all its bundled components share Zig's licence. No broad assertion about copyright in generated API-reference bytes is needed to close this condition.

## 5. Hash and reproducibility reconciliation

The original 6,656-byte DLL hashes to `47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65`; original object, PDB, link-trace and generated-core hashes all match the supplied manifest. Fresh DLL SHA-256 is `576f5a3854cdcd3de6dc74953aa24ac39188289a342eec904255807ac0760e23`. A byte-identical whole-DLL rebuild was **not** achieved or claimed. Object debug information differs with source path/newlines and linked read-only data differs; executable `.text` is identical for each object and the DLL:

| Executable section | Original and fresh `.text` SHA-256 |
|---|---|
| `adapter.obj` | `8f44fe5782b20f845e9c9a004c09bae0bf98374758c856774881c29df9cf1441` |
| `support.obj` | `80aad8b112bbded7b325a79273cf1194d3a0a29600e7ad585a0ac813090b9112` |
| DLL | `7500a2bc2b6ccc6610d2f28d7a12a60c508aa03d68040dca78c444e115d12779` |

The repository's `* text=auto` and local `core.autocrlf=true` yield different raw source bytes. For example, original `adapter.c` is 2,632 bytes with one CRLF, Git blob is 2,631 LF bytes, and fresh checkout is 2,673 bytes with 42 CRLFs. **All three normalize to identical text.** The same normalization check passes for `support.c/h`. Record both raw build hashes and these exact reviewed-commit Git blob SHA-256 values:

| Committed source | Git blob content SHA-256 (LF) |
|---|---|
| `tools/m5a1l/adapter.c` | `cf0c9e641bdde3d2298cfad924c11094ca0567301db44821f29e87acee01e26d` |
| `tools/m5a1l/support.c` | `d10b2b2eb35f2d4a8f1f22461d50f3512a441b0e523c567d6acada5ca0961c30` |
| `tools/m5a1l/support.h` | `eac3f3138233e34790e59a97ccd7f60e09ec20e3ab103df1d549efc070441fc3` |

This preserves the exact original evidence without pretending its local-byte hashes are portable checkout hashes. Do not silently overwrite the old manifest to match a different build or require whole-object hash equality across debug paths.

## 6. Required distribution notice inventory

The [BSD-3-Clause terms](https://opensource.org/license/bsd-3-clause) require copyright/conditions/disclaimer retention in source and reproduction in binary documentation/materials, with no unauthorized endorsement. The [MIT terms](https://opensource.org/license/mit) require their copyright and permission notice in copies or substantial portions. The existing component notice contains the full BSD conditions and disclaimer; the separate MIT file contains the full grant/disclaimer and appropriately excludes upstream/game material. A separate filename `LICENSE-BSD` is optional if the complete text travels in the existing notice document. Neither licence requires releasing proprietary host source or shipping all development dependencies.

| Material | Source handoff | Binary handoff |
|---|---|---|
| Exact PSG declaration and complete historical preamble | Preserve in `retained_psg.c`; include BSD terms alongside it. | Include original copyright declaration, BSD terms/disclaimer in accompanying notices; retain contributor acknowledgements as documented provenance. |
| `docs/m5-a1l-THIRD-PARTY-NOTICES.md` | Include, with upstream pin and dated integration changes. | Include as a readable notice file/material delivered with the DLL/application. |
| `tools/m5a1l/LICENSE-MIT.txt` | Include for adapter/support and any shipped scoped utilities; correct/confirm provenance under PROV-1. | Include with the component; SPDX tags alone are not the complete MIT notice. |
| Kernel32 definition-input provenance / bundled mingw-w64 notice | Add the documented build-input references and conservative notice set under PROV-3; retain attribution when packaging those inputs. | Carry that conservative notice set too, unless Manager records a supported narrower treatment. No Windows DLL or mingw CRT implementation is to be bundled. |
| Frozen component manifest | Identify actual files, upstream source, exact raw and normalized hashes, target/compiler/options, object/DLL hashes, imports and linked contribution result. | Keep source-to-binary mapping for that exact build; no ROM/music/event-data rights inferred. |
| Toolchain / Python tooling | Only if supplied: retain their own applicable notices and enumerate actual bundled dependencies. | Not needed merely because they were used during development; revisit if code from them or their runtimes is added. |

I opened the original private 87-member review ZIP locally and checked ZIP CRC. Its SHA-256 matches `426c884c7e6d9b16437e5186386b0930cb3034cc356b6ac6c3ee81e0172178e2`; it includes `retained_psg.c`, `metadata/m5-a1l-THIRD-PARTY-NOTICES.md` and `metadata/LICENSE-MIT.txt`. It does **not** contain the three new C source/header files. That is not a BSD/MIT source-disclosure violation for a private binary proof package, but it is not a complete source handoff. `tools/m5a1l/package.py` deliberately includes diagnostic WAV/state; component licensing does not settle rights to those payloads. No audio was played, regenerated or redistributed for this audit.

For an eventual buildable source component, package the three MIT C inputs, generated BSD core, minimal build instructions/script and the notice set. Do not solve missing source by bundling the entire unclear libvgm checkout. For a binary-only component, source inclusion is optional, but accompanying notices and the internal frozen receipt remain required by this review. Public source-only research must continue excluding private proof assets.

## 7. Verification scope and stop

Performed locally: exact fourteen upstream input rehashes; three replacement sources reconciled with committed blobs; generated-body/preamble checks; manual helper, resampler and predecessor comparisons; original artifact/archive hash checks; fresh native build; dependency/COFF/PDB/PE closure inspection; independent COFF/PE executable-section and import-archive inspection; original private ZIP CRC and notice-presence inspection. Research's small parsers in `pe.py` were reused for symbol/module/import extraction and cross-checked against build traces and direct binary structure inspection; they are not a second independently implemented PDB toolchain.

`python -m unittest discover -s tests -p test_m5a1l.py`: **10 PASS, 5 SKIPPED** (native NumPy-dependent suite not enabled; NumPy is absent from default Python). Separately, direct ctypes checks on the fresh DLL passed all sixteen volume entries and one synthetic `735` versus `1+98+636` partition comparison, with normal instance cleanup. These narrow native checks do not replace Research's twelve-control differential gate, new-control acceptance, native GameMaker host testing or human listening. Existing 1–5 LSB policy remains as accepted; no material new fidelity error was identified here.

Private audit scratch is retained under this worktree's ignored `build/`: `provenance_check.py` SHA-256 `4ec7f598e0697c859bf4be5145c066f22b911d6c083237589c913f430996abb4`, `provenance-results.json` SHA-256 `90a7c329ed991ef7bd9bc9cb228b17ba5dca462d7da6aba9bb9b3b3513eb63df`. The report records the decision-relevant safe evidence so Manager review does not require opening local binaries. No scratch script, object, DLL, private data, upstream source copy or generated core is included in this audit commit.

**STOP for Manager review.** Only this report is committed. The reviewed code, original proof package, accepted POC, management files and Research main remain unchanged. No upstream maintainer was contacted and no binary was distributed. Human rightsholder/provenance confirmation and Manager's eventual redistribution checklist approval remain outstanding; this review does not supply them.

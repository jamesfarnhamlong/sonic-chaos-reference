# M5-A1L licensing and dependency decision

**Recommendation: HOLD for Manager's fidelity/permission decision.** A small dependency-reduced component set is demonstrated, supported by explicit BSD-3-Clause and newly authored MIT source. It preserves the PSG state machine in all twelve accepted controls. Its rational resampler does not preserve A0's matched-callback byte identity: the worst new difference is 5 signed-16-bit levels. This report neither grants legal clearance nor silently accepts that new numerical policy.

Baseline: `research/m5-a0-stateful-psg@549de7543b6704cf9d219d5c87f5a03bf854ec9e`; management read at `6b72e7cd85fe29d938ce4672a7903e60d262732b`. No canonical file or private GameMaker file was changed.

## Audit conclusion

The exact fourteen A0 files were rehashed and their pinned history examined. The PSG file explicitly declares BSD-3-Clause. For the thirteen helpers/headers, no governing separate grant was established by the examined file notices, pinned tree/history or public maintainer statements. This is an unresolved evidence status, **not proof that no separate licence exists**. [The file-by-file matrix](../data/m5-a1l/license-matrix.json) records each hash, provenance, permission status and replacement/exclusion.

The maintainer's [2025 module-licensing statement](https://github.com/ValleyBell/libvgm/issues/129#issuecomment-2781054175) and [earlier discussion](https://github.com/ValleyBell/libvgm/issues/43#issuecomment-797782644) describe future intentions, not an established grant for these exact files. A third party's suggestion that a GPL core licenses an entire library is not accepted as permission from all rights holders. Missing headers alone do not settle the question. No upstream contact was made.

The pinned core's BSD declaration, preserved notices and MAME's [file-specific licensing policy](https://www.mamedev.org/legal.html) support retaining that file rather than rewriting the PSG. This does not license a whole MAME/libvgm binary. The experiment mechanically removes only external includes/registration metadata; its retained body from `MAX_OUTPUT` onward is identical after LF normalization. Original PSG calculations, control writes, counters, LFSR and initialization code are retained.

## Smallest demonstrated component graph

```text
explicitly BSD PSG source (pinned hash)
  + MIT component-private support declarations/implementation
  + MIT rational area-average adapter
  -> adapter.obj + support.obj -> 6,656-byte Windows DLL
  -> KERNEL32: GetProcessHeap / HeapAlloc / HeapFree
```

All thirteen unclear libvgm files are absent from compiler dependency lists. The build uses `-nostdlib` and no standard headers. Zig still offers `c.lib` and `compiler_rt.lib` to the linker: they are inventoried, not assumed absent. COFF symbol closure and the linked PDB show no contributing members from either archive; only our two objects and Kernel32 import modules contribute code/data. No C/compiler-runtime implementation enters this DLL. New support code provides width-checked integer types, local initialization/configuration types, no-op diagnostics, Windows heap allocation, a local byte-fill routine and a narrow mathematical power calculation used only for the core's volume table. All sixteen resulting volume entries match the accepted formula exactly. No libvgm structure layout or external ABI is exported; functional field names serve the retained core.

The native objects, compiler dependency lists, input/generated-source hashes, build commands and binary import table are recorded in [the manifest](../data/m5-a1l/dependency-manifest.json). The DLL imports only the three listed system APIs. This is stronger evidence than import inspection alone: source/object closure and `-nostdlib` also exclude a hidden static CRT. Do not bundle Windows DLLs or the Zig toolchain. New component state is 296 bytes with zero resampler scratch allocation; no GameMaker performance claim follows.

The new resampler integrates piecewise-constant native samples on a rational time grid. Each native cell has width 44,100 units; each output spans 221,680 units. It carries partially consumed cells through request/block boundaries, applies the accepted fixed gain and converts once to signed16. There is no unclear resampler code, lookup bank, invented tail or phase reset. The author had already inspected A0's source; this is **not a formal clean-room attestation**. The implementation was newly written from this mathematical specification, not copied or translated line-by-line from libvgm's fixed-point implementation. Its different numerical results are retained.

## Technical outcome

All twelve controls / 5,587 ticks retain exact original-driver emission and every accepted core register/counter/LFSR snapshot. The candidate is still driven by the independently scheduled emitter and private intrinsic bank; recorded original events are comparison inputs only. A3's 28 muted ticks advance state correctly; both A3 resumption and finite-fade held noise remain present. All 5,880 required finite-fade noise samples are present, without source padding. Fresh instances are deterministic in all twelve cases; pause-without-production preserves state; explicit off produces silence while counters continue; F8/reset-followed-by-new-output remains covered.

The new output is invariant under 735 versus 100+635 and 2048 callback partitioning. However, against A0 it has up to 4 LSB new sample differences, and against the original continuous MAME reference it has up to 5 LSB. **The matched-callback exactness of A0 is lost.** No error threshold was widened. Full per-case, per-voice, envelope, waveform, noise and pitch results are in [comparisons.json](../data/m5-a1l/comparisons.json). The mathematical area filter avoids A0's callback-local fixed-point quantization; this explains the changed arithmetic, not permission to accept it. No human listening or native GameMaker acceptance was invented.

## Alternatives and action

1. **Permission/clarification for the exact A0 helper set:** best route if A0 sample identity is mandatory. An [unsent draft](m5-a1l-upstream-request-DRAFT.md) identifies all thirteen files and asks first for any existing applicable licence. Chief must explicitly approve contact. Retain HOLD until a documented grant covers all retained sources/contributions.
2. **Adopt the new BSD/MIT component set:** lowest demonstrated dependency surface. Manager must explicitly decide whether the measured 1–5 LSB resampler policy is acceptable and whether further independent authorship review is required. This is a bounded engineering alternative, not a claim that this report supplies legal approval.
3. **A documented permissive third-party resampler:** see below. It may simplify licence evidence but adds code and changes latency/filter behavior; it does not restore A0 byte identity automatically. No alternative library was built or silently substituted.

After either licence clarification or an explicit numerical-policy decision, repeat this exact comparison gate on the frozen chosen build, then use the separately authorized native feasibility workflow. No POC integration or full sound production is authorized here.

## Documented resampler alternatives

| Option | Permission evidence | Minimal runtime dependencies to investigate | Fit for this task |
|---|---|---|---|
| libsamplerate | [COPYING](https://raw.githubusercontent.com/libsndfile/libsamplerate/master/COPYING) grants BSD-2-Clause terms | C runtime/math; own linear/ZOH/sinc implementations and optional coefficient tables. Disable examples/tests and inspect selected target rather than assuming their dependencies belong to the library. [Build sources](https://raw.githubusercontent.com/libsndfile/libsamplerate/master/src/CMakeLists.txt). | Clearer source licence; more integration surface. Its interpolation/filter kernels do not reproduce A0's quantized area integrator. A pinned minimal build and a new source/binary audit would be required. |
| miniaudio | Explicit choice of MIT-0 or public domain in [LICENSE](https://raw.githubusercontent.com/mackron/miniaudio/master/LICENSE); prefer MIT-0 as the documented route | Single-header implementation, C runtime/math; configure away device I/O, decoding/encoding, resource manager and node graph. Audit remaining platform paths and any enabled bundled decoders separately. [Declared component](https://raw.githubusercontent.com/mackron/miniaudio/master/extras/miniaudio_split/miniaudio.h). | Useful maintained resampling API, but substantially larger than the new helper. No sample-parity advantage established; not a drop-in exact replacement. |

These are source assessments, not audited distributable builds. Current branch/version URLs are discovery references, not approved binary pins. Neither library is included in the demonstrated DLL or public Research.

## Distribution procedure

Before a release, freeze the chosen source hashes and helper policy. Rebuild with the recorded compiler/options; verify the retained core body, compiler dependencies, two object hashes and PE imports. Include the complete original PSG preamble/contributor notices, BSD-3-Clause conditions/disclaimer, the scoped MIT licence and integration-change notice from [the notice inventory](m5-a1l-THIRD-PARTY-NOTICES.md). Include equivalent documentation with a binary distribution. Do not imply MAME/contributor endorsement. Keep a source-to-binary manifest and reproducible test receipt with that version.

Any platform/compiler change, wrapper, CRT, new core or dependency invalidates this narrow manifest and requires a delta audit. A licence statement on the PSG alone never grants rights to musical/event data. Runtime data, PCM and detailed traces stay private; neither ROM nor original Z80 binary is needed by the backend. Accepted M4 and all five earlier proof archives remain unchanged. Private experimental output is review evidence, not a release.

**Stopped for Manager review.** The next decision is permission for exact A0 helpers versus explicit acceptance/review of the measured replacement arithmetic. No maintainers were contacted and no GameMaker implementation was attempted.

## Focused numerical comparison inventory

| Control | New vs A0 735 max LSB | New vs MAME max LSB | New matched-callback vs MAME max LSB |
|---|---:|---:|---:|
| fixed-hold | 3 | 3 | 3 |
| coupled-steal-recover | 2 | 2 | 2 |
| clock-switch-with-live-tone2 | 3 | 3 | 3 |
| periodic-retrigger | 3 | 3 | 3 |
| music-context-B6 | 3 | 3 | 3 |
| music-context-BA | 4 | 5 | 5 |
| isolated-context-B6 | 3 | 3 | 3 |
| off-then-fresh | 3 | 3 | 3 |
| finite-fade | 4 | 4 | 4 |
| BF-A3 | 3 | 3 | 3 |
| A3-BF | 3 | 3 | 3 |
| near-loop | 4 | 4 | 4 |

## Reproduction and preservation receipt

With the existing local dependencies and private A0 fixtures available:

```text
python tools/m5a1l/build.py --source PINNED_LIBVGM_CHECKOUT --cc ZIG_EXE
python tools/m5a1l/audit.py
python tools/m5a1l/compare.py
$env:M5A1L_NATIVE="1"
python -m unittest discover -s tests -p test_m5a1l.py
python tools/m5a1l/package.py
```

Set NumPy/Python dependency paths as in A0. The proof scripts deliberately use the existing sibling private A0 folders; they fail on missing inputs instead of downloading private assets or synthesizing substitutes. The runtime candidate has no ROM/Z80 dependency. `compare.py` reuses the A0 intrinsic bank and original-driver captures only as specified, with independently emitted candidate writes.

Executed: 15 A1L tests (including native helper/import tests), 13 inherited A0 tests with its immutable native DLL, and 11 P1C preservation/regression tests, all PASS. These green tests assert that the new sample discrepancy remains reported; they are not a blanket PCM-parity PASS. All five previous private archive hashes and 47 accepted M4 payloads match. The accepted private POC is clean at `11bff34356d5f5d979218896dc95fdc4bb265eae`.

The private sidecar contains only bounded experimental audio/state, build objects/PDB/DLL, notices and a member-hash manifest. Its CRC and every payload SHA-256 are verified. Path/hash are provided separately in the task response; [the safe receipt](../data/m5-a1l/private-package.json) records integrity and preservation. It is not a production audio package. The public [verification receipt](../data/m5-a1l/verification.json) records the exact safe file inventory and executed tests.

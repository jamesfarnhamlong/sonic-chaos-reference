# M5-A0 Manager handover

**CONDITIONAL GO: the bounded stateful backend is demonstrated.** Recommend a small stateful PSG behind the existing audio owner for later new content, with a narrowly defined M4 PCM hybrid. This is permission requested for a later isolated native feasibility gate, not acceptance of a complete sound library or authorization to modify the POC.

Research parent: `ce0eb2df1a943386082c48e3b35ae00e0e622f76`. Management read: `01af5a87a8c06cd198db94cdf300867013b4c2d1`. Accepted private POC remains `11bff34356d5f5d979218896dc95fdc4bb265eae`. ROM SHA-256: `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. Reference MAME executable SHA-256: `36821f4cfb6a1b6e386f1b468504245c21c6e24a2cbb0cba4b268703c96334a0`.

## Established

* Twelve independently scheduled original-driver controls pass exact emission/register/latch/saved-context/ownership/priority checks over 5,587 ticks and 32,512 ordered bytes.
* Persistent counters/LFSR close the A3→BC hidden-history failure: resumed-noise correlation 0.999999999818, versus prior carrier 0.05547. The finite-fade case retains all eight post-cancellation noise ticks without padding.
* All twelve full-mix comparisons are byte-identical when callback boundaries match. The intended 735-frame block path differs by 1–3 LSB through documented resampler segmentation; it is explicitly not called bit-identical.
* Offline native synthesis is about 26µs per block / 640× realtime on this machine. This is not a GameMaker benchmark. State plus resampler scratch is about 1.78 MB; private event storage is far smaller than PCM on measured controls, but full-library size is unproved.
* All earlier four private archives, 47 accepted M4 asset hashes and the private POC source remain unchanged. No original reference render, full library, long $90/$91/$8C job, native GameMaker build or POC modification occurred.

## Conditions before further implementation

1. Resolve redistribution permission for the exact resampler/logging/header dependencies, or independently replace them with documented/verified alternatives. The PSG's BSD-3-Clause declaration does not license the entire dependency chain. Do not redistribute the proof DLL as a release.
2. Manager must authorize one isolated GameMaker VM/YYC queue/timing/lifetime benchmark before full integration. Native C speed alone is insufficient; no human/native listening is claimed.
3. A later complete private event/decoder contract is required. The bounded P0R model uses measured intrinsic intents, not an independently complete decoder for every song/phase. The solo $81 coverage extension is limited to the existing loop control.
4. Define and test hybrid handoff/reset policy while preserving accepted M4 PCM bytes, single owner, pause, queue retirement and shutdown. This proof covers continuously synthesized sequences, not a live PCM↔synth seam.

No fundamental stateful-architecture failure remains in the bounded controls. The licensing and native-host gates prevent an unconditional production GO. Do not resume finite-carrier/context banks as a universal solution.

## Deliverables and reproduction

* [Architecture and runtime contract](m5-a0-architecture.md)
* [Exact emission, PCM and retained diagnostics](m5-a0-comparisons.md)
* [Performance, storage and file-specific licensing](m5-a0-performance-licensing.md)
* [Numerical results](../data/m5-a0/results.json), [source/license audit](../data/m5-a0/source-license-audit.json), [private integrity receipt](../data/m5-a0/private-package.json), and verification receipt alongside them.

Build `tools/m5a0/build.py --source PINNED_LIBVGM_CHECKOUT --cc ZIG_EXE` with Python. It builds only the adapter, selected PSG, resampler and logging files into ignored storage. Run `tools/m5a0/proof.py --rom PRIVATE_ROM` with the existing NumPy/emulator dependencies. Candidate binding is in `tools/m5a0/backend.py`; it accepts private intrinsic programs and external requests, never combined oracle output. `audit.py` records exact file provenance; `package.py` verifies the bounded private package and does no rendering. Default paths target the existing local private proof folders; missing data fail rather than triggering download or synthesis substitutes.

Private package is temporary local review evidence containing binary adapter, audio and detailed state captures with member hashes; it contains no ROM or original Z80 binary and is not redistribution-cleared. Its path/hash are supplied separately in the task response. Public Research contains only safe source, numeric metadata, tests and reports. Prior failure files remain immutable.

**STOP for Manager review. No automatic native benchmark, full production, Sound Test or GameMaker implementation.**

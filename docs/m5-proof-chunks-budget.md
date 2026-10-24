# M5 chunk and measured production budget proof

24 October 2026. Byte/addressing proof PASS; native cache performance NOT TESTED.
No long90/91/8C was rendered. Overall production remains HOLD for the separate
output-state/composition failure in [the audio report](m5-proof-audio.md).

## 4096-tick format

Existing authenticated continuous M4 character-choice82 PCM supplied the test
material. Four synchronized experimental residual-grouped voices were split
**after rendering**, with no new PSG process or reset at chunk boundaries.
Each raw little-endian signed16 mono chunk holds at most4096×735 samples:
6,021,120 bytes (5.742MiB). There are four matching voice groups; final chunks
can be shorter. Raw PCM has no per-chunk WAV header.

The private manifest records format, absolute first sample, sample/byte count
and SHA-256 for each chunk, plus a complete-voice SHA-256. The manifest itself
is anchored by SHA-256 in the parent package. Reader initialization checks its
trusted digest, format, contiguous addressing, complete sample coverage and
safe unique basenames. Missing files, wrong length and bad chunk hashes fail
before bytes are returned. Unit tests also reject altered manifest hashes,
unsafe paths and noncontiguous addresses. Do not allow a changed chunk to
authenticate itself by supplying an untrusted replacement manifest.

For absolute source sampleS:

```text
chunk_index = floor(S / (4096*735))
local_byte = 2*(S - chunk.first_sample)
loop_phase(A) = A, if A<cut
                cut + ((A-cut) mod period), otherwise
```

The test uses accepted82 cut1,381,065 and period5,080,320 samples, retaining
the intro. It checks boundaries near4096/8192 ticks, loop endpoints, repeated
body seeks and the final source sample. Reassembled bytes match the continuous
source for all four voices. **4,064 sample-address assertions PASS**, plus
missing/corrupt-chunk negative controls and additional manifest-reader unit
tests. See [chunk-proof.json](../data/m5-proof/chunk-proof.json).

No noise/oscillator phase is changed by splitting. A byte-identical stored loop
seek does not establish phase-continuous music, an inaudible seam or native
GameMaker performance. This is an offline storage proof, not a cache-runtime PASS.

## Proposed Designer cache contract, pending authorization

Keep the accepted single persistent owner,735-sample queue blocks, eight queue
buffers, pause/cursor behavior, deferred callback retirement and shutdown.
Add a file/PCM cache behind sample lookup; do not create another output owner.
Use one absolute music clock for all voices and one validated intro/body map.
Effects have independent ages, ownership and per-slot generations.

At most current+next synchronized groups occupy45.94MiB for four voices,
plus active effects, queue buffers, metadata and any retained M4 banks. Prefetch
and authenticate the next group in ordinary control flow before its first
needed block. Never perform file I/O/hash work or delete in-flight buffers from
an audio callback. Loop seeks may require a nonadjacent next group; derive it
from loop_phase, not blindly chunk_index+1. Pin groups referenced by queued
samples until copying/retirement is safe. Missing/corrupt data must stop with
an explicit diagnostic, not silently emit an invented replacement sound.

The Python prototype's cache is illustrative and is not accepted GameMaker
code. Designer must benchmark warm/cold transitions, next-group prefetch,
nonadjacent loop seeks, pause/resume,30Hz menus/60Hz audio, disk contention,
buffer retirement and clean return/shutdown. Measure actual resident memory,
frame time, queue underruns and audible gaps on Chief's runtime. No such test
was authorized or performed here.

## Measured bounded workload

Preflight free space was about749GiB. Limits were2GiB scratch,512MiB archive,
30-minute render/run budget and a4GiB remaining-space floor. Estimated proof
scratch/archive were700/160MiB; the small selection stayed well below both.
See [budget preflight](../data/m5-proof/budget-preflight.json) and
[measured budget](../data/m5-proof/measured-budget.json).

Initial production/validation/package run:

- 94 actual fresh renderer processes,635.75 summed voice-timeline seconds;
  hash-keyed cache reused the identical BC/C0 target. No old M4 cache changed.
- Renderer process wall time3.801s total, about167.28 audio-timeline seconds
  per wall second in this mixed short/70-second workload. Whole Python proof
  run26.266s including captures, measurements, chunks and ZIP checks.
- Python peak working set664,145,920 bytes (~633.38MiB); sampled renderer
  process peaks4,075,520–5,664,768 bytes. Child peaks were sampled while live,
  so very short process peaks can be missed. This is not a combined system
  high-water measurement. The Python tool keeps multiple whole-array templates;
  it is not the proposed bounded native cache.
- Final payload, scratch, archive and metadata-only repack timing are recorded
  exactly in the final numeric receipt; payload is about186.8MiB, scratch
  about308MiB and ZIP about13.71MiB. The compression ratio is not a guaranteed
  ratio for all later music. Native runtime size is distinct from private ZIP.

The chunk proof82 payload accounts for82,054,148 bytes. The private package
also retains raw/experimental stems, full mixes, original references and
diagnostic timelines. These are proof/archive artifacts, not all intended
GameMaker included files. ROM and renderer/toolchain binaries are excluded.

## Cautious long-target extrapolation

Using each verified recurrence start+one complete period, five passes
(mix+four voices) at the measured aggregate throughput predicts roughly:

| Target | Prefix+body ticks | One mono voice bytes | Simple five-pass wall estimate |
|---|---:|---:|---:|
|90 |20,575 |30,245,250 |10.25s |
|91 |32,651 |47,996,970 |16.27s |
|8C |81,137 |119,271,390 |40.42s |

These are **not rendered measurements, deadlines or production permission**.
They exclude a second body/seam scan, new validation, file/hash/ZIP work and
potential memory/disk bottlenecks. Short-process overhead and long-array memory
make linear extrapolation uncertain. The current all-array Python workflow
should not be scaled blindly: process continuous renderer output files a voice
at a time and split/hash in bounded blocks after rendering, preserving PSG
continuity. Do not restart the renderer per4096-tick chunk.

Complete8C mono output exceeds100MiB; chunk storage avoids that individual-file
problem without lossy conversion or altered music. Future library size remains
the conservative R1 estimate until actual seam choices/manifests exist. Rendering
speed/storage feasibility does not overcome the current composition HOLD.

# M5 private production feasibility and batch plan

24 October 2026. **Planning only. No audio rendered by M5-R1.** Runtime assets
and private capture/read maps belong in private SonicChaos_POC; public Research
contains metadata, hashes, tools and safe numeric checks only. Existing local
M4 renderer, PCM and archives remain unchanged. No new toolchain is needed.

## Targets and durations

The70 request rows comprise31 music,37 SFX and2 controls. Five music entries
9B–9F contain only terminating streams. The remaining26 music IDs produce
nonempty original-driver output, including unknown8E. All37 SFX are finite.
Three pairs have identical **complete solo command output**: A8/C2, BB/C4,
BC/C0. Thus **60 distinct nonempty solo command-output targets** is the
current production estimate:26 music+34 SFX. This is not proof of60 perceptually
distinct sounds, nor license to merge request priorities. Five empty indexed
music IDs and2 controls require metadata, not seven silent WAVs.

Each finite entry's first all-inactive driver tick, per-SFX-slot release ticks,
and last non-off register ticks are in [catalogue.json](../data/m5/catalogue.json).
Add a small common post-end safety pad and verify renderer decay/bucket behavior;
do not derive ownership lifetime from padded WAV length or first silence.
For request at tickR, a solo slot ending at tickN ends at `R+N-1`.
BF has inactive tick21, hence20 active ticks; A6 inactive41, hence40.
Multi-slot examples AC end ticks49/54, B6 16/27, BA5/25 require separate streams.
Finite full ending8D lasts10,432 ticks (173.8667s), not a repeating level song.

Eleven music IDs have verified whole-driver/PSG-command recurrences. These
are sufficient loop intervals, **not a claim of the shortest musical phrase**.
All have a byte-identical subsequent command period. The table in the
[catalogue report](m5-audio-catalogue.md) gives starts and lengths.
New90 full loop is19,768 ticks (329.4667s), boss8C80,640 ticks (1,344s),
SEZ9132,256 ticks (537.6s). Three channel-state recurrence probes did not
produce a shorter independently validated interval. Do not silently trim these
to a presumed musical phrase or replay the pilot opening file in EEZ3.

Loop recurrence proves driver/command repetition, not PCM oscillator recurrence
or an inaudible native seam. Keep M4's selected cuts for81/82 unchanged.
New songs require a joint four-stem/mix tick-boundary seam scan, same cut for
all stems, retained intro, original full body, and a native seek-near-seam
check. Export at least a complete body plus required seam scan coverage;
reuse register-period evidence instead of repeating independent emulator work.
Music maps wrap with the exact selected sample interval; absolute music age
continues through effects. Finite tracks never acquire synthetic loops.

## Storage and working-set estimate

Pinned pipeline remains libvgm MAME PSG, PAL3,546,893Hz,60 driver ticks/s,
44,100Hz signed16 mono per voice,735 samples/tick. One stem costs88,200B/s;
four cost352,800B/s. Do not normalize separately, change synthesis, invent
crossfades, alter M4 PCM or adopt compression without a separate measured gate.

Using each finite duration or `recurrence_start+one_period` for26 nonempty
music IDs totals186,645 ticks /3,110.75s. Four music stems total
**1,046.63MiB**, before padding, actual selected seam cut, manifests and
filesystem overhead. This is a planning lower estimate, not a finished manifest.
Selected cuts can retain more intro; a conservative all-new-song bound retaining
up to one additional body is about1.94GiB for four runtime music voices.
Original37 SFX total1,561 ticks /26.0167s; even four voices per ID is under9MiB
before pad, and alias reuse reduces that. Existing accepted M4 opening tail
bank and11 PCM payloads (~68.8MB reported) remain separate and reusable;
count overlap when producing the final private manifest rather than adding
all preparation files to runtime.

Largest conservative mono prefix+body is boss8C:81,137 ticks,119,271,390B
(113.75MiB) **per stem**, exceeding GitHub's ordinary100MiB file limit.
Do not plan native Git storage of that single file. Split **already continuously
rendered** PCM at4096-tick boundaries: at most6,021,120B (5.74MiB) per mono
chunk,22.97MiB for four matching chunks. This changes storage boundaries only;
samples and queue blocks remain identical. No restart of PSG at chunk edges.
Loop mapping may cross a chunk boundary; seek by absolute sample offset.
Native Git is sufficient for these chunks; no automatic LFS dependency.

The existing M4 owner eagerly loads its whole bank. M5 should add a small
private PCM cache behind `chaos_audio_sample`: current+next synchronized chunks
are about45.94MiB, plus active SFX, queue pool and retained M4 assets. Two
chunks per track, one active song, not all songs resident. File reads/prefetch
must finish before their blocks are requested, never from the audio callback.
Measure native seek, pause/resume and room-transition behavior. Preserve the
eight-buffer735-sample queue, callback retirement, owner reactivation and safe
shutdown. A cache can fail explicitly on missing chunks; it must not delete
in-flight buffers or start another output owner.

Private production should budget roughly10–20GiB scratch for source captures,
full/stem reference WAVs, one or two bodies, temporary arrays and validation;
this is a capacity allowance, not measured output size. Runtime is roughly
1.1–2.1GiB plus accepted context assets under this conservative plan. Archival
VGM, original reference renders, full read/restore maps, renderer provenance,
diagnostic mixes and raw stems stay private and separate from the shipped
GameMaker included-file list. Raw ROM and renderer binaries are regeneration
inputs, never runtime dependencies and never public Research files.

## Avoiding redundant or unbounded jobs

M4's hash-keyed renderer cache, private manifest and restore checks already work.
Reuse its renderer and six produced targets; preserve their bytes/hashes.
Deduplicate the three equal-output pairs only at asset level. Render missing
targets once; aliases point to shared PCM while keeping ID metadata.
Do not pre-render every music×SFX×phase combination or create generic fade
tail banks for every song tick. Do not redo737 opening tails.

The nominal music timeline for first recurrence plus **two** bodies totals
5,789.42s (~96.49min), before multiple renderer passes. This is timeline
duration, not measured wall-clock cost. A naive full-mix+four-stem approach
processes ~8.04 renderer-hours of timeline; blindly multiplying by every
fade, effect and validation phase is inappropriate. Benchmark one new short
song with existing pinned renderer, record time/memory and establish a batch
budget before long8C/91. Reuse validated raw stems, derive grouped residual
metadata from those captures, and check determinism with one fresh process per
new target, not endless whole-library reruns. Cache completion by input/tool
hash and verify saved hashes on resumption. Keep independent diagnostic
comparisons scoped to newly affected ownership classes.

M4 raw four-stem sums differed from full mix by up to6LSB; its exact runtime
two-group reconstruction is already documented. M5 needs four separately
gateable voices. Reuse the same measured residual-reconciliation method,
with the residual assigned to unstealable tone0 for new four-voice groups;
validate a declared guard against the actual new renders. For81/82, preserve
accepted tone2 and other3 assets: new tone0 can be derived from accepted other3
minus the original raw tone1/noise stems. This keeps the all-voices sum equal
to accepted PCM; it is not permission to rewrite accepted M4 files. Raw
stems, differences and numeric results stay explicit. This grouping is a
**proposal pending production validation**, not an existing four-stem PASS.

## Ordered production batches and gates

| Batch | Scope | Required evidence before integration |
|---|---|---|
| P0 | Metadata/dispatcher oracle, no bulk PCM: three slots, F3 coupling, both recovery readers, shared priority, mailbox/fade order | Run a proposed PCM-independent owner model against original-driver111 recovery cases and1,369 pair timelines; add staggered slot replacement, fade/request and deferred/direct overwrite controls. Preserve M4 checks. |
| P1 | Finite cues84–8A,94,96–9A,8D, unknown8E; missing SFX, including no-site entries; reuse99/BF/A6 | Complete finite endpoint and per-slot release validation, register silence vs PCM, pitch/noise/clipping/determinism, per-voice grouping. Validate empty9B–9F separately with no playable files. |
| P2 | New short common-loop music83,8B,8F,92,93,95; extend81/82 ownership using existing renders | Full-body command recurrence, private tone/noise recovery maps, common cut, stem reconstruction, one-shot phase combinations and seek-near-seam native smoke. |
| P3 | Long90/91/8C, full90 context plus chunk cache | Benchmark first; continuous render/chunk hash parity, loop/intro mapping, bounded memory, no chunk or seek gaps. Preserve original opening bank and timing. |
| P4 | Full scene event coverage and Sound Test, one consolidated source candidate | Every request site disposition, all70 menu rows, exact numeric ownership/priority lifecycle, unsupported asset honesty, return/stop/pause/shutdown. One short human listening/UI session, no full campaign. |

Independent new validation is justified for F3 coupled-noise interaction and
generic fades, because M4 did not cover these. Render a small representative
set of **continuous original-driver** timelines and compare with composed
PCM: BF→A3 and reverse; AC→A0; B6→A0; BA with partial replacement; fixed-rate
noise+tone2; release near a loop boundary; fade while multiple slots are live;
late effect over finite music. Compare per-tick registers/ownership exactly;
for PCM record unchanged-channel equality, envelope/noise/pitch and residual
metrics with honest waveform-phase differences. No hardware equivalence is
claimed. Native audibility/queue performance remains a separate gate.

## Manager decisions and stop conditions

Finite and independently rendered nonempty assets can begin **after Manager
authorizes the next batch**. This assignment grants no production permission.
Do not authorize a full unreviewed all-catalogue render merely because60
targets are known. The next work should start with P0 plus a small P1 proof,
then apply a measured wall-time/storage limit to later batches.

The original **logic** is specified, but the existing hybrid cannot promise
exact arbitrary-phase PSG waveform recovery or exact generic fades. Manager
must explicitly retain M4's declared PC approximations or authorize a scoped
new exact-tail/attenuation investigation for the relevant transitions. New
bulk all-phase fade banks or a synthesis rewrite are not recommended/authorized.
If the continuous-versus-composed noise checks expose a material new failure,
stop that ownership class before bulk asset production. Do not label a partial
library “complete original audio” while a reachable class is unsupported.

Other unresolved matters: unknown friendly names and natural use of no-site
IDs; actual hardware analogue/DC behavior of empty entries; shortest possible
long loops; new PCM seam cuts and native audibility; measured production time,
disk and cache working set. These are specifically bounded gates, not reasons
to replay campaigns, alter graphics/physics or rebuild GameMaker now.

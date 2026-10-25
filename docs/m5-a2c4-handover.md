# M5-A2C4 single-F3 coupled-noise SFX — Manager handover

**AF, B1 and B9 PASS within the demonstrated scopes. GO for a separately
authorised small tone2-only preflight/proof. STOP for Manager review.**
No accepted interpreter, SCSP format, FD scope or A1L synthesis source changed.

25 October 2026. Branch `research/m5-a2c4-single-f3-sfx`; exact parent C3
`84998b692c784d10ebe0bf571519ca81b6cf707b`; management read at
`55afed112dab114561d505c05b5e484831a599d1` (AGENTS/MEMORY/ROADMAP).
The C2/C3 handovers, C2 FD analysis, original language specification and P1C
class evidence remain historical inputs. Original ROM freshly authenticated:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Accepted M4 `11bff34356d5f5d979218896dc95fdc4bb265eae` remains read-only.

## Original-only preflight before extraction

The unmodified original Z80 executed each complete solo, 128 post ticks and a
THZ context before candidate record extraction or PCM. P1C class labels were
hypotheses until these fresh runs. Native reference diagnostics consume only
original OUT bytes and discard rendered samples during preflight; they supply
no events to the decoder. [preflight.json](../data/m5-a2c4/preflight.json)
records headers, pointers, flag/priority metadata, source hashes, bounded syntax,
reached commands, envelope/pitch selectors, native F3 states and latch restores.
Original CPU data addresses map to ROM offset CPU+$4000 in this sound-bank
research mapping, as documented by the accepted language specification.

| ID / preserved name | Header ROM offset / stream CPU | Header flags / slot | Priority | F3 execution | Inactive tick |
|---|---|---|---:|---|---:|
| AF / Unknown $AF | $E10F / $A119 | $80 / noise E0 | 72 | tick1, E7 mode7 once | 68 |
| B1 / Unknown $B1 | $E150 / $A15A | $88 raw / noise E0 | 72 | tick1, E7 mode7 once | 22 |
| B9 / Unknown $B9 | $E267 / $A271 | $80 / noise E0 | 72 | tick1, E7 mode7 once | 31 |

All use envelope base CPU $49FD and multiplier1. All actually produce
tone2-clocked white noise from a single SFX noise reader. AF reaches E0/F0/F2/F3/F5;
B1 E0/F0/F2/F3; B9 E6/F2/F3/F5/F7/F8/F9. B9 executes five F7 commands and six
calls plus six returns in its solo. AF/B1 use the existing algorithmic pitch
path; B9 uses the existing table-volume, relative-volume, loop and call paths.
No table pitch, unsupported opcode, alternate envelope base or FD invocation
was reached. B1's raw header is not an FD instruction. The verified FD boundary
remains SFX tone2 slot5/latchC0 only. Reached control transfers are compared
against original targets, ticks and channel order, not merely final duration.

All three finish with four attenuation registers15, no reader reactivation,
no subsequent solo writes and no enabled physical output during the observed
128 original-only post ticks. Candidate solos retain32 post ticks. This is
measured physical output, not a policy forcing inactivity to digital silence.
The continuously running chip counters/LFSR are still compared after release.

## Exact independent execution and interactions

**118 scenarios /35,704 ticks /170,201 ordered PSG bytes: exact PASS.** All99 C3
cases (32,531 ticks/154,221 bytes) are retained with frozen candidate rows.
The19 new cases add3173 ticks/15,980 bytes. Every tick compares ordered writes,
physical registers/data latch, saved DE11/shared IY, all336 channel bytes and12
globals, priorities/mailboxes, pointers/durations/envelopes and slot suppression.
Control transfers and actual admissions are compared/recorded separately.
Candidate execution completes before each original oracle is instantiated.
There is no timing or state tolerance. No captured combined timeline becomes
runtime input. See [emission.json](../data/m5-a2c4/emission.json).

The16 new interactions select actual classes: three THZ contexts; four-phase
retriggers of each new effect; AF interrupted by accepted tone2 hurt A4; lower
priority ring rejection then admission after B1; attempts to replace AF with
A7 and B1 with B0; admitted B9→B7 noise replacement; BA→B9 concurrent-slot
replacement; later-phase B9 in THZ; fade/reset followed by new output; and B9
followed by accepted finite music98. This is neither a Cartesian matrix nor a
natural gameplay capture.

The AF→A7 and B1→B0 scenario names describe host request order, **not admission**:
A7 at50 and B0 at35 are rejected by original priority72. They do not replace the
noise slot. Ring at3 is rejected during B1, then admitted at30 after release.
A4 at40 is admitted over AF at30. B7 at45 is admitted over B9 at30; actual F3
execution is mode7 at30, then mode3 at45 and48 from B7. BA at30 and B9 at32 are
both admitted; BA tone1 continues while B9 owns the replaced noise slot, giving
two simultaneous SFX slots. No new target has a tone1 reader of its own.

Each four-request AF/B1/B9 retrigger schedule produces exactly four F3 commands:
AF30/32/57/140, B1 30/33/45/90, B9 30/32/47/100. Early retriggers pre-empt active
instances; later ones follow completion. No internal second F3 was invented.
Every actual control resets LFSR to32768, preserving its instantaneous noise
countdown. Before-state values vary by phase; e.g. AF at32 changes LFSR8320→32768
while countdown80→80. B9→B7's second periodic control at48 changes16384→32768
while countdown21→21. Full native traces remain private; numeric control/reset
and continuity summaries are in [facts.json](../data/m5-a2c4/facts.json).

The original-only native observer distinguishes stream F3 writes (CPU OUT at
$477F) from music-percussion noise-control writes. A second all-control observer
compares instantaneous before/after states for every noise-control write against
the independent candidate, including music. Per-tick noise control, tone2 period,
noise counter, LFSR, flags and core22-field register/counter/LFSR snapshots match
in all19 cases. Muted progression is preserved; no request recreates the chip.
This remains the pinned tick-boundary reference model, not cycle-timed hardware
measurement. Audible coupled effects suppress music tone2; later music98 clocks
retained muted noise state. No audible co-ownership with unsuppressed music is
claimed.

THZ AF suppresses music tone2/noise30..96; noise next-read103 and tone2 next-read109.
THZ B1 suppresses30..50; both eligible reads61. THZ B9 suppresses30..59; both reads61.
Later B9 suppresses73..102 and both reads109. Reader release does not force an
immediate music read. Solo DE11=0 passes through latch7 at each release. THZ AF
restores E4 at97 through latch3; B1 at51 and B9 at60 through latch0; late B9 at103
uses latch3. Data bytes are interpreted through the actual latch and ordered
writes; they are not relabelled as guaranteed noise-control latches.

## Continuous PCM and ROM-free playback

Unchanged A1L and pinned original-driver/MAME: PAL3,546,893Hz,44,100Hz signed16
mono,735 samples per60Hz tick. All19 new cases compare full mix, four independently
attenuated voices, block-RMS envelope differences and core registers/counters/LFSR.
[pcm.json](../data/m5-a2c4/pcm.json) retains every metric, sample count and hash.

| Case | Ticks | Mix max LSB | Mix RMS LSB | Voice0/1/2/3 max LSB |
|---|---:|---:|---:|---|
| solo-AF | 100 | 3 | 0.158178 | 0,0,0,3 |
| solo-B1 | 54 | 3 | 0.130796 | 0,0,0,3 |
| solo-B9 | 63 | 2 | 0.059148 | 0,0,0,2 |
| THZ-AF | 180 | 3 | 0.223961 | 3,2,2,3 |
| THZ-B1 | 180 | 5 | 0.223708 | 3,2,3,3 |
| THZ-B9 | 180 | 3 | 0.212906 | 3,2,3,3 |
| AF-retrigger | 250 | 4 | 0.246532 | 3,2,2,3 |
| B1-retrigger | 170 | 4 | 0.229009 | 2,2,2,3 |
| B9-retrigger | 180 | 3 | 0.194598 | 3,2,2,3 |
| AF-tone2-interrupt | 180 | 4 | 0.299357 | 3,2,3,3 |
| B1-block-ring | 100 | 3 | 0.166231 | 0,0,3,3 |
| AF-to-A7 | 150 | 3 | 0.225937 | 2,2,2,3 |
| B1-to-B0 | 140 | 5 | 0.229611 | 2,2,3,3 |
| B9-to-B7 | 150 | 3 | 0.215752 | 2,2,2,3 |
| BA-to-B9 | 180 | 3 | 0.221365 | 3,3,2,3 |
| THZ-late-B9 | 180 | 3 | 0.209163 | 3,2,2,2 |
| fade-fresh-AF | 200 | 3 | 0.167596 | 2,2,2,3 |
| reset-fresh-B1 | 160 | 3 | 0.150820 | 2,2,2,3 |
| B9-to-music98 | 376 | 3 | 0.150300 | 3,2,2,2 |

The two5LSB cases are THZ-B1 and the rejected B1→B0 attempt. New solo maxima are
3/3/2LSB. No new case exceeds the previously observed range; that observation
is not a universal tolerance. Arithmetic/resampler and numerical policy remain
unchanged. Driver envelope/attenuation states are exact; per-voice waveform and
block-RMS differences remain explicitly measured, not labelled sample-identical.
No human listening test or hardware sample-identity claim is made.

All118 candidate outputs are identical for735 versus100+635 partitions. All99
previous candidate PCM outputs remain byte-identical, including8A's authentic
constant+8192 post-completion DC. Each of the19 new solo/interaction schedules
also runs in its own fresh process from packed SCSP with oracle imports and
ROM/VGM access forbidden. All19 WAVs are byte-identical to independent candidate
playback: [isolation.json](../data/m5-a2c4/isolation.json). PC-style runtime uses
only private program records, host requests and A1L, no Z80 or recorded timeline.

## SCSP storage and Python prototype cost

SCSP **v1**, source authentication and **4200-tick** explicit horizon remain
unchanged. Expanded bank9352B vs8942B (+410);5735 original data bytes (+88),528
header bytes (+30),70 priorities; raw field total6333B. There are33 unique program
headers and59 validated data segments; canonical record JSON30157B. Compression
and integrity/address/provenance metadata account for the packed size rather
than promising a raw-payload compression ratio. Bank SHA-256:
`e8cd4d721ad33d72a0b9daf6784c8d37ad03a01ee5516cc9acd9552e2cb34b91`.
All previous30 headers and5647 data bytes compare identically. Six original
standalone A2/B1/B2/C1/C2/C3 banks and hashes are preserved.

Python benchmark10850 ticks:6050 active median2.4µs,4800 idle median0.7µs;
combined median2.1µs, p9913.4µs, max108.4µs in this run. Whole-proof peak work is20
stream operations/21 ordered writes in one tick. Traced current/peak allocation:
previous528316/670950B, expanded531543/676021B, increments3227/5071B. Scope is
sparse Python bank/decoder and bounded diagnostics; excludes interpreter base
and PCM buffers. This is **not native GameMaker performance**.

## Catalogue and remaining original classes

All70 rows updated: **33 verified within tested scope,7 empty/control,30
unverified**;18 verified SFX and15 music. No partial/HOLD new target. Request IDs,
unique headers and audible outputs remain distinct. Original68 indexed records
and61 bounded solo-emission fingerprints do not prove68 complete programs or61
universal audible identities. Unknown AF/B1/B9 names remain unchanged.
[coverage.json](../data/m5-a2c4/coverage.json) contains every row.

Historical authenticated P1C class metadata intersected with this matrix gives
**19 remaining SFX:16 tone2-only and3 single-F3 coupled-white-noise (BB/BE/C4)**,
plus11 unverified music IDs. Zero remaining entries in that historical37-SFX
inventory belong to fixed-white-noise, periodic-noise, repeated-F3 or multi-slot
classes: their representatives already passed earlier bounded work. This is not
proof that no remaining program has a new envelope/opcode or context behaviour.
No remaining ID was newly executed, extracted or rendered here. These coarse
classes establish no extra decoder coverage.

**Next proposal only:** original-only preflight a Manager-selected small group
from the16 tone2-only effects, prioritising modulation/volume-envelope/raw-mode
variation before candidate extraction. They are the largest remaining class and
may expose language gaps, whereas more single-F3 white noise repeats a demonstrated
mechanism. BB/BE/C4 remain an alternative separately authorised finishing group.
FD in other readers, table pitch, DE-relative envelopes, E2/E4/E5/E8/ED/F4/FA,
alternate envelope bases, DE08 and numericD0/D1/D2 remain unsupported boundaries,
not assumed requirements of any unexecuted ID. No next batch has begun.

## Regression, private preservation and stopping boundary

**95 public tests PASS:** all78 inherited plus17 C4 evidence contracts. Fresh
original/native/PCM gates above are distinct from public JSON/source-receipt
tests. Wrong omission of the sole F3 fails at1 for each new solo; missing terminal
writes fail at68/22/31. The C3 duplicate-control negative is rerun on the expanded
bank: both B0 and B7 still cause36 LFSR-mismatching ticks and16384LSB maximum error
when their second identical control is removed. The second valid F3 resets LFSR
without resetting countdown21. This remains an explicit regression, not a
register-value dedup optimisation opportunity. All prior malformed/truncated data,
pointer/loop/stack, unknown-opcode, FD scope and horizon negatives are retained.

```text
python tools/m5a2c4/preflight.py PRIVATE_ROM
python tools/m5a2c4/proof.py PRIVATE_ROM
python tools/m5a2c4/pcm.py
python tools/m5a2c4/evidence.py PRIVATE_ROM
python tools/m5a2c4/isolation.py
python -m unittest discover -s tests -p test_m5a2*.py
python tools/m5a2c4/package.py
```

Use the pinned local Python3.12/NumPy and accepted native reference tools.
Original comparisons require the authenticated private ROM; playback does not.
New source programs, detailed driver/native traces, WAV/VGM and negative audio
remain under private-research/m5-a2c4, outside this checkout. The separate proof
ZIP is private; no ROM or DLL is included. Packaging checks twelve earlier proof
archives, six prior banks,47 M4 payloads, accepted M4 HEAD/clean tree and A1P
source/native/compiled VM integrity read-only. Public additions are safe source,
semantics, aggregate numerical evidence, tests and hash receipts only.

**GO for the next separately authorised class investigation; STOP for Manager
review now.** No POC/GameMaker/Sound Test change, long music, full catalogue,
component redistribution, upstream contact or topic merge into main occurred.
The purpose remains personal learning, faithful experimentation and public
ROM-documentation knowledge sharing.

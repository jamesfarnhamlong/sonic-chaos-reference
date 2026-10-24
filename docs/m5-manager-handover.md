# M5-R1 Manager handover — complete indexed audio contract

24 October 2026. **Research completed for review; STOP before bulk rendering or
GameMaker implementation.** Topic `research/m5-full-audio-contract`, direct
child of accepted M4 production `8df6e7e65ea93f7e49f0f975137eb55c0c5e5bf5`.
Management AGENTS/MEMORY/ROADMAP were read at `main@600951fde25ab27b3acf4bc6c6881f3f13654100`;
they were not edited or merged. This user assignment authorizes research and
its commit/push, superseding the historical Windows-root “no next assignment”.

## Deliverables

| Brief | Authoritative output |
|---|---|
| A complete catalogue | [70-entry JSON](../data/m5/catalogue.json) and [human matrix](m5-audio-catalogue.md) |
| B driver integration | [Full contract](m5-driver-integration-contract.md), [pair/control traces](../data/m5/interactions.json), [recovery/fade/channel evidence](../data/m5/extensions.json) |
| C Sound Test | [Design contract](m5-sound-test-contract.md), [private-source preflight metadata](../data/m5/poc-preflight.json) |
| D feasibility/batches | [Production plan](m5-production-plan.md), [derived estimate](../data/m5/production-estimate.json) |
| E reproducible verification | [Metadata-only probe](../tools/m5_audio_contract.py), [16 focused tests](../tests/test_m5_audio_contract.py), [verification receipt](../data/m5/verification.json) |
| F handover | This document |

## Established facts and evidence strength

- Authenticated GitHub confirms POC is private and the specified accepted source
  is readable. Local accepted checkout HEAD is exactly11bff343. Read-only
  inventory identifies73 audio-call source lines across29 GML files and hashes
  Sound Test/input sources. This is a syntax inventory, not proof all original
  events are correctly wired. Source/asset payloads were not copied to Research.
- Local original ROM is available and matches the required SHA-256. All68
  indexed headers executed in the existing isolated Z80 harness. No renderer,
  hardware comparison, new SMS campaign or native GameMaker run was used.
- 31 music+37 SFX+2 controls are retained. Eleven music requests repeat;
  fifteen nonempty music cues and all37 SFX are finite. Five entries9B–9F
  immediately terminate every stream and are unsuitable as playable tracks.
  Their tone2 period-zero register residue is preserved; physical/DC audibility
  is unresolved, not falsely marked measured silence.
-60 distinct nonempty solo command-output targets:26 music+34 SFX. A8/C2,
  BB/C4 and BC/C0 have identical complete solo command output, distinct headers
  and different priorities. Request identity remains separate from PCM reuse.
- Title99 finite/choice82/opening-and-EEZ3 90/empty00 corrections are explicit.
  Original AUDIO-0 prose/data are preserved unchanged, with later provenance
  and corrected fields in the new matrix.28 friendly labels remain unknown;
  nine IDs lack verified gameplay sites. Do not invent acoustic names or
  equate a static script site with observed original gameplay use.
- Shared arbitration tested for37 SFX+F8 against128 stored priority values:
  **4,864 assertions**. Numeric F8's raw priority is57 and higher effects can
  block it. M4's unconditional F8 is an existing adapter difference requiring
  scoped review, not an authorized runtime change here.
-1,369 ordered SFX pair cases plus37 restarts,37 music replacements and37
  reset attempts give **1,480 bounded scenarios**, including rejected resets.
  All111 single-effect recovery cases at three THZ phases are recorded;
  **159 released music-channel recovery facts** match their next eligible
  tone/noise reader in these cases. No claim covers every phase/music pair.
- Three slots are insufficient without coupling logic: noise may own tone2;
  ending any SFX stream clears global priority despite other active effects;
  fades cancel active SFX immediately; music noise has a different reader.
  Fade's terminal reset can erase a same-tick newly selected music request.
  These cases have original-driver traces or focused execution tests.
- Whole-driver command recurrence includes very long valid periods (boss8C
  1,344s, SEZ91537.6s, full90 329.4667s). They are proven sufficient, not
  necessarily minimal phrase lengths or native seamless PCM loops.

## Readiness and explicit remaining decisions

The next assignment can specify P0 state-machine parity and a small P1 finite
asset proof without guessing catalogue IDs, headers, priority, endpoints,
channel update order or initial ownership. It should use the exact private
M4 baseline and existing pinned MAME pipeline, preserving PCM queue/single
owner/pause/shutdown fixes. **Bulk production is not authorized by this report.**

Recommend authorizing P0 plus limited P1 first, then measured P2/P3 production,
then one consolidated P4 Sound Test/event integration candidate and short native
listening session. Detailed batch acceptance criteria are in the production plan.
Do not repeat the18-act campaign or build a standalone executable.

Manager should decide these material integration policies before declaring
complete authentic runtime audio:

1. Review original F8 priority and nonzero deferred-mailbox semantics against
   accepted M4 unconditional reset/explicit-zero transfer; authorize any scoped
   behavior change separately. Administrative Stop remains reliable and distinct.
2. Explicitly retain the accepted hybrid's oscillator/pause/generic-fade
   approximations, or commission a bounded new exact-tail/attenuation inquiry.
   No evidence establishes exact arbitrary-phase coupled-noise PCM composition.
   Compare a small continuous-versus-composed reference set before bulk noise
   production. Do not hide a failed class behind “complete”.
3. Approve the practical storage/cache extension: conservative runtime music
   ~1.1–2.1GiB plus context assets; sample-identical4096-tick mono chunks avoid
   the113.75MiB boss-stem file and use native private Git. Benchmark production
   time before the long loops; do not multiply all phases into giant fade banks.

Unresolved names/use, hardware/DC output, shortest possible long loops,
new seam cuts/native audibility and measured cache/render resource costs remain
explicit. They do not justify speculative sounds, gameplay changes, public
audio, replacing the renderer or modifying the accepted M4 branch.

## Verification and exact public inventory

Focused final run: **16 M5 tests +9 inherited M4 tests =25 PASS**, no skips,
failures or errors with authenticated ROM supplied. Python compilation and
diff whitespace checks pass. No broad historic gameplay suite, rendering,
listening or native build was run. Existing M4 tests/evidence were reused.
The16 tests split into7 ROM-free fixture/contract tests and9 original-ROM tests;
without SONIC_CHAOS_ROM the latter explicitly skip.25 PASS does not imply
hardware or new PCM parity.

Reproduction from this topic (all outputs metadata only):

```powershell
$env:SONIC_CHAOS_ROM = 'PRIVATE_VERIFIED_ROM.sms'
python tools/m5_audio_contract.py $env:SONIC_CHAOS_ROM catalogue
python tools/m5_audio_contract.py $env:SONIC_CHAOS_ROM interactions
python tools/m5_audio_contract.py $env:SONIC_CHAOS_ROM extensions
python tools/m5_audio_contract.py $env:SONIC_CHAOS_ROM reports
# Optional exact accepted private source checkout; read only:
python tools/m5_audio_contract.py $env:SONIC_CHAOS_ROM poc --poc PRIVATE_M4_CHECKOUT
python -m unittest discover -s tests -p test_m5_audio_contract.py -v
python -m unittest discover -s tests -p test_m4_audio.py -v
git diff --check
```

Exactly13 new public text files; no modified/deleted inherited files:

```text
data/m5/catalogue.json
data/m5/extensions.json
data/m5/interactions.json
data/m5/poc-preflight.json
data/m5/production-estimate.json
data/m5/verification.json
docs/m5-audio-catalogue.md
docs/m5-driver-integration-contract.md
docs/m5-manager-handover.md
docs/m5-production-plan.md
docs/m5-sound-test-contract.md
tests/test_m5_audio_contract.py
tools/m5_audio_contract.py
```

Commit/remote identity and final clean worktree are verified after committing;
the final chat handoff supplies the exact SHA. No main merge or canonical
management edit. No original ROM, private source payload, audio/VGM/WAV/PCM,
full port/read map, toolchain or private binary is in this inventory.

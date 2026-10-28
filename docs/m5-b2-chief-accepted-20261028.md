# M5-B2 — Chief Windows acceptance (28 October 2026)

**DECISION: ACCEPT M5-B2 native F2 catalogue candidate for its proven contextual listening/gameplay-return scope. M5 FULL ORIGINAL AUDIO REMAINS OPEN.**

## Accepted source

- Private GameMaker branch `poc/m5-b2-f2-catalogue@335ef23cca1f0aecaf6d43375b392f3732e69130`, direct one-commit child of Chief-accepted B1 `d23557d3733bfda8d7977eecaa5fe48b546af323`. GitHub branch tip independently verified.
- Private candidate ZIP, user-provided path `E:/AI/Codex/Sonic Chaos/releases/SonicChaos_M5_B2_F2_20261027_CANDIDATE_PRIVATE.zip`; **reported** SHA256 `fb79fe6629a4b5b974e5dae7041ae56287d52f323ca1f7f3eb61b4f430be1c21`. The local ZIP itself was not independently inspected by Manager; repository code, manifest and receipts were inspected.
- GitHub implementation report: `experiments/m5-b2/README.md`; native manifest: `experiments/m5-b2/native-playable-ids.json`; F5 guide: `README_B2_NATIVE_F2.md` at the exact commit above.

## Chief human acceptance

Chief explicitly reported **1 PASS, 2 PASS, 3 PASS, 4 PASS, 5 PASS** for the five B2 acceptance checks, plus **naturally triggered death followed by early stage-card skip: PASS** and `Music sounds good! No problems noted, sounds natural to me`.

These cover:
1. F2 starts at $81; catalogue navigation/counts and N/V native-entry shortcuts; 68 rows/five empty headers and unavailable labels.
2. New finite music playback, switching/retrigger/finish.
3. Expanded SFX over explicitly active $81 and priority behaviour.
4. Stop/replay, context-required refusal and control operation.
5. Return from F2 to normal THZ1 gameplay, music/SFX and pause/resume.
6. Additional genuine gameplay death/stage-card early skip (not the timed fixture's automatic assertion).
No additional unidentified failure was reported.

**Interpretation:** B2 **human acceptance PASS** in the tested session. The actual native F2 programme count is **39 of 63** nonempty original requests: **15 music / 24 SFX**, including 33 new B2 requests (11 finite music,22 finite SFX). SFX currently require active $81 in F2. All 68 menu rows preserved (31 music +37 SFX), with empty $9B..$9F and two non-menu original controls $00/$F8 excluded from the 63-programme denominator. **24 requests remain unintegrated/unauthenticated in C6 (11 music,13 SFX).** This is not a claim of 39 programmes naturally reachable/correctly wired in every gameplay zone, or all F2 audition contexts.

## Automated evidence and retained gaps

B2 evidence reports **95 Windows GameMaker cases, 45,610 exact original-driver sound ticks, 33,523,350 exact continuous A1L PCM samples, 95 native opens/closes, zero callback errors**. Five GML source changes? **Four B2 runtime GML files changed** relative B1; GameMaker normal audio owner, clock, PSG renderer, queue policy and game event writers unchanged. Independent manifest count exactly39; all33 attempted new requests have passing bounded native contexts.

**Gameplay fixture remains PARTIAL** despite Chief human card-skip PASS. The timed B2 fixture did not satisfy its early pre-emption condition (its second card duration236/269 ticks); an unchanged B1 binary control also missed it (214 ticks), without proving identical cause. The final epoch's3781-tick loop checkpoint was not reached in the timed B2 fixture, though earlier separate verified long renewals exist. Two inherited raw harness errors were retained in the earlier B1 chain, with focused successor checks. Do **not** rewrite any raw failing gate as PASS; preserve raw captures, context and source/control comparisons. The human test exercises actual gameplay behaviour, not the exact timed fixture schedule or strict original frame-accuracy for arbitrary gameplay interruptions.

Technical acceptance is specific to proven original/PSG/PCM/context checks and observed human session. B2 accepted but no automatic broad regression or final M5 closure.

## Updated immediate project status and next boundaries

- **M5-B1:** Chief-accepted foundation 6/63 native F2.
- **M5-B2:** **Chief-accepted populated F2 39/63 native**; no more B2 code work unless an actual bug is reported. Preserve B2 exact SHA as a new read-only accepted checkpoint.
- **Research C7-1:** $83/$92 originally HOLD for full native in candidate at `7496725`.
- **Subsequent Research $83:** A new pushed `research/m5-c7-1r83-pitch-region@9961b05eb9962bdeb43983028aa4b9ca4b802cec` was independently read on28 Oct. Its report claims **GO within tested original/candidate research scope** for the exact two-byte pitch-data region, 38,200 exact ticks, 28,077,000 exact A1L samples, 154 tests and uninterrupted $83 solo renewal 13,000 ticks. **It does not authorize GameMaker integration and long playback after an SFX/retrigger/fade is still HOLD.** Treat it as a separate research gate for Manager assessment, not retroactive B2 membership.
- **Research $92:** F7 index4 context remains HOLD; no source-backed decoder generalization approved.
- **Remaining native F2 requests:** 24 historical C6 unverified/unsupported, requiring original-driver proof per request; opening/EEZ3 $90 use must not reuse incomplete historical PCM as verified native loop.
- **Future work:** keep F2 as the qualification and listening hub; Research focuses unsupported source operations/loop lifecycles; Designer subsequently ports newly fully qualified programmes via small data/policy/driver contracts, and only then extends zone/title/boss/ending routing and interaction coverage. No automatic permission to bypass guards, import executable-region data outside a narrowly authenticated contract, or claim the soundtrack complete.

## Preservation

M4 `11bff34356d5f5d979218896dc95fdc4bb265eae`, A4B `afdd6a1e62e5e61234159266a05bcddab825faf9`, B0-D `1c7fb623c32f16b1fda0c9e070b92bb07ad1fb1d`, B1 `d23557d3733bfda8d7977eecaa5fe48b546af323`, and newly accepted B2 `335ef23cca1f0aecaf6d43375b392f3732e69130` stay read-only checkpoints. Canonical main `AGENTS.md`,`MEMORY.md`,`ROADMAP.md` not changed by this record. M5 remains open. No public ROM/SCSP/DLL/audio assets.

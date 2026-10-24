# M5-P1C runtime representation proposal — not implementation authority

The proposed interface can sit behind the accepted single persistent audio owner and its735-sample / 60 Hz PCM queue. Keep M4 PAL clock 3,546,893,44,100 Hz signed 16-bit PCM, pause freeze, retirement and shutdown unchanged. Existing accepted grouped PCM bytes remain immutable. No new resampler, crossfade or synthesis is proposed.

An asset descriptor would contain request/header identity, source/tool hashes, voice, signed 16-bit PCM, absolute sample cursor, authenticated finite source lifetime, original clock/control initialization and reset history, and context predicate. The emission model owns request admission, slots, saved DE11, data latch, ordered register writes, levels, explicit-off and recovery. A stream flag alone never controls amplitude. Inhibition never restarts a carrier. Explicit-off gates output, while future legitimate writes may restore it only inside a valid source lifetime.

Selection needs actual physical periods/noise mode and the history of tone2 clock/reset events, including muted intervals. Repeated identical F3 bytes are events, not redundant state assignments. B6/BA additionally need saved DE11 and the current PSG data latch at restoration; use original emission to compute their effective output, not a guessed named context. A context asset is valid only for a demonstrated predicate. A current-register match cannot recover missing LFSR/counter state.

Validate compatible history before selecting the source. Missing context, overrun, wrong clock or cancelled-source output must fail the diagnostic/preflight and block that asset class. Do not quietly truncate a required sound or substitute silence and call it faithful. An eventual PC administrative Stop can stop audio unconditionally; numericF8 remains original priority gated. No runtime failure behavior is implemented here.

A finite source can share chunk-cache addressing with music: key asset/hash/absolute sample, synchronized voices, owner-controlled cursor and pause; no PSG reset at cache/chunk boundaries. Queue/cache compatibility does not prove native GameMaker memory or deadline performance. Designer must later benchmark queue refill, concurrent voices, seeks, buffer retirement and shutdown under native load, only after authorization.

## Asset growth and limits

The 37 SFX identities occupy 40 original SFX channel streams: 23 tone2-only, 11 noise-only, 3 tone1+noise. Forty finite per-stream carriers is a structural starting estimate before deduplication, tails and context variants, not40 authenticated production assets. Aliased request IDs still retain different priorities. The previous1561-tick aggregate solo-duration bound at1470 bytes per voice-tick would cost about 8.75MiB for all four voices, plus padding/metadata; sparse streams can be smaller. This is a planning bound, not newly rendered storage. No complete catalogue was produced.

Named DE11/latch contexts can sometimes be normalized by emission/gain, as P0R demonstrates. General tone2-clocked noise requires the incoming oscillator counter/LFSR and its clock history. Enumerating request pairs, stagger offsets, music phases and prior interruptions multiplies beyond a per-ID bank; no defensible fixed upper asset count follows from the70-ID ledger. Carrier extension beyond its authenticated valid lifetime is forbidden. The fade example exposes this limit even with exact registers.

## Architecture choices for Manager

1. Restrict finite carriers to demonstrated compatible clock histories and context predicates. This supports bounded fixed-rate and reset/retrigger cases, not a complete unrestricted sound system.
2. Explicitly accept a broader phase/history approximation, with affected classes and audible comparisons reviewed. Current proof cannot approve this choice, and no human listening result is claimed.
3. Research preservation of shared oscillator/noise state. That potentially addresses the missing state but entails an architecture decision outside this task. No engine replacement was implemented.

Pre-rendering every interaction or arbitrary-phase bank is rejected as an unbounded production policy. Keep full production HOLD until Manager chooses the fidelity target and a representative counterexample passes that target.

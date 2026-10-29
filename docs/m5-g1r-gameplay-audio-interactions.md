# M5-G1-R — authentic gameplay audio interaction capability matrix

29 October 2026. **Research GO for the bounded interactions below; HOLD for
unbounded gameplay continuation after an interrupt. STOP for Manager review.**

Direct parent: completed C9 `713f7660c4881ac58f15c444e8e4e5e410b4d2ba`.
Manager7's explicit G1-R assignment authorises this isolated research branch.
No catalogue requalification, GameMaker changes, native acceptance, main merge,
or management/root AGENTS amendment is included.

## Designer decision

The original driver continues music sequencing underneath SFX suppression.
SFX completion releases channel gates; it does not resume a saved recording or
restart the song. Accepted music requests do restart programmes, including the
same ID, and reset active SFX. Invincibility/Rocket expiry uses that replacement
path, not a saved-position return. These semantics now have independent
multi-zone driver/state/ordered-PSG/accepted-A1L comparisons in the tested slices.

**Do not promote the solo 63/63 catalogue result to arbitrary gameplay audio.**
Existing solo continuation capabilities remain valid in their original scopes
and banks. A subsequent host request or fade revokes their permission. Completion
of an SFX does not automatically restore it. This investigation supplies no
new continuation runtime or generic permission. G1 needs the exact contracts
below plus a separately verified epoch/continuation capability before indefinite
multi-zone audio can be marked supported.

## One consolidated capability matrix

GO means original semantics and exact bounded Research execution, not native
GameMaker approval. All times are driver updates. Programmes tested are
`81/83/91/92/93/95/90` (seven normal-zone table entries), `8F` (all SS music),
`8B` (first EEZ encounter) and `8C` (ordinary boss). Initial scenes and host
request phases are controlled, not newly achieved natural gameplay routes.

| Interaction class | Research outcome / evidence | Required GameMaker contract | Continuation decision |
|---|---|---|---|
| Zone/SS/boss music + representative SFX | **GO bounded**: each of ten programmes with BF, A6, A3, B8, BA, B4 independently at30 and211; 120 cases through550 | Keep four advancing music slots and three independently replaceable SFX slots. Apply original suppression/coupling and original reader recovery, in original update order. One persistent PSG, ordered writes including repeated noise writes | Existing solo certificate cannot remain eligible merely because an effect finished. Long post-SFX playback **HOLD** |
| Competing SFX / priority / partial completion | **GO bounded**: ten multi-request cases through550, plus mailbox/F8 controls; reuse accepted M5 all1369 ordered SFX pairs and C1–C6 interference evidence | Global DE0F, not per-voice priority; lower drops, equal admits; F2 can clear priority while another SFX remains active. Replace only selected streams. Never resurrect a displaced SFX. Preserve F3 coupled-noise branches and saved DE11/data latch | No all-phases/all-pairs PCM extrapolation. Bounded shared semantics GO; arbitrary interrupted recurrence **HOLD** |
| SFX completion and music recovery | **GO bounded**: original F2 hooks, suppression-clear and both eligible-reader hooks; per-case aggregate facts in original.json | Music updates before SFX: release cannot retroactively replay that tick's music. Tone reader4341 and noise reader4650 are distinct. Clearing suppression plus setting bit4 is not an immediate audible note. Preserve current counters/pointers/envelopes | Retain song age; do not restart to regain a solo certificate. Fresh interaction-specific continuation evidence required |
| Different zone music / repeated music | **GO bounded**: ten zone replacement sequences and ten same-ID cases; through750/550 | Accepted music resets seven channels, global driver state and current SFX; loads requested header. No crossfade, saved-position stack or same-ID early return. Restore the correct zone/act ID | A genuinely accepted initialization is a candidate **new programme epoch**, never a continuation of the old epoch; safe extended capability still **HOLD** |
| Death, title card, act clear | **GO bounded**: ten death96→card88→level sequences through700 and ten clear89→clear97→level controls through750 | Retain event writers and ordering; do not schedule all transitions at these fixture times. Death/clear/title replace active music/SFX. SS failure has its separate fade path | Same new-epoch requirement; arbitrary complete scene chains **HOLD** pending their own package/epoch proofs |
| Invincibility84, Rocket85 and restoration | **GO bounded**: ten controlled power slices through1400; five additional schedules independently derived from original reward/timer execution through1500 | 84 finite; repeat pickup can restart and reload600. Ordinary85 finite, timer300. Selector4/6 expiry calls189B, subject to D4A3; restart zone music from its header. No automatic finite-end fallback | New accepted level request starts a new epoch. Preserve finite end/silence if no restoration request arrives; long recertification **HOLD** |
| SS1 Rocket exception / Silent Sneakers | **GO bounded**: original-routine-derived SS1 and SS4 Rocket plus invincibility→Sneakers counterfactual | Zone8 skips85; retain8F. Other ordinary Rocket contexts use85 and restore8F. Sneakers selects3 without a new sound and can prevent84 restoration; original finite84 then ends in silence | No invented resume on selector3 or finite completion; do not borrow a Rocket/invincibility certificate |
| Fade and reset | **GO bounded**: ten mixed fade/reset cases; early-dispatch and terminal-fade cases; numericF8 rejection | Direct fade `(12,1,2)` immediately deactivates SFX, releases suppression and applies original additive/clamped attenuation; reset at its terminal step. Dispatch follows fade; terminal reset can erase a previously selected request. NumericF8 still arbitrates at priority57. Zero cancels pending direct data and does not silence | Fade/reset revoke old continuation. PC administrative stop remains separate. No gain-only fade or unconditional numericF8 |
| SS clock/countdown | **GO bounded**: resetF8, ten B5 requests, restarted8F, exact through1100 | Retain original game clock: eleven decrements, only ten nonzero B5 writes; zero calls189B. Recollection reloads11. Driver fixture uses controlled60-update spacing, not a newly proved pickup-to-first-tick offset | Restored8F is a new programme epoch. Arbitrary countdown phase/natural-route integration **HOLD** |
| SS success and failure | **GO bounded**:8F→8A→86 through1200; separate failure fade through650 | Emerald touch supplies no invented immediate unique sound; success uses8A then86. Timeout/death uses original failure/fade path, not ordinary96 or success86 automatically | New epochs where music is actually accepted; full naturally timed SS chain still **HOLD** |
| Mailbox, deferred delivery and suppression | **GO source/execution scoped**: ordered overwrite, zero-cancel and auxiliary-slot controls;39 original189B gate/table cases and five power writer schedules | DirectDE04 is one mailbox, not a FIFO. IRQ nonzeroD4A4 overwrites direct pending data and clears the deferred latch. GuardedC4 writes only into an empty direct mailbox. BF→A9 wrap retains the last write. Driver scansDE04..06 in order; only final admitted selection dispatches | Host diagnostics must distinguish write/admit/replace/drop. Auxiliary slots tested only as controlled driver capability, not ordinary game writers |
| Original state after accepted restart | **GO original-only causal finding**: ten interference→same-music resets,5001 epoch ticks each | Keep persistent physical PSG. Driver RAM/IY restart immediately, but untouched logical PSG values can differ until later original writes. Compare the full actual epoch checkpoint, not only pointer/song age | Original behaviour supports a fresh epoch design; **HOLD for new candidate epoch certificates**. Repacked banks cannot use old hash-pinned solo capabilities |
| Long gameplay, arbitrary interruption phase, native G1 | **HOLD** | Preserve fail-closed limits; request a scoped interrupted-state/epoch proof and native bank verification. Never reset the PSG or rewind music/channel state to force certificate matching | No continuation permission granted by this report |

## Programme distinctions that must survive integration

`83` retains its exact83 pitch-pair reader contract. `92` retains its exact
tone2 F7 index4/cursor48 alias contract, not a general extra-counter permission.
C9 `91/93/95/8B/90` retain distinct authenticated per-programme pitch readers
and exact pair hashes. `8C` has its long original recurrence; a short interaction
slice does not qualify its80640-update period under interruptions. `8F` has its
own bank/certificate and clock restoration rules. `90` opening and EEZ3 remain
separate host contexts of the same composition. The short opening PCM cannot
serve EEZ3. No reader policies or existing continuation code were changed.

The private interaction banks are compatible unions of already authenticated
records, with overlap equality checked and the original per-reader loaders
retained. Their new hashes are in banks.json. Each uses the ordinary unchanged
4200-update decoder; no diagnostic traversal, horizon reset, continuation
renewal or permission widening occurs. They have **no** continuation certificate.
This is research packaging, not a replacement for Designer's native bank proof.

## Epoch evidence and exact acceptance condition

Each original-only epoch experiment starts one programme, requestsBA at30,
then requests the same music at250. Before reset none of the ten complete
400-byte/IY/logical-PSG states rejoined the uninterrupted solo during the tested
30..249 slice. Thus even apparently recovered music is not established to be
the old solo state.

For5001 updates after initialization, all ten have identical driver RAM400,
IY and every ordered write compared with fresh original solo execution.
However, the complete logical state differs initially for83 (383 updates),92
(192),93 (119),90 (304),8F (77),8B (144),8C (446). Other tested programmes
match logical state immediately. All converge within these experiments, but
these are **not universal all-phase convergence bounds**. Physical PSG PCM
differs from a newly created chip for every programme: the chip is deliberately
persistent and its oscillator/LFSR counters are not programme RAM.

A new epoch design therefore must: observe actual admitted music initialization,
retain absolute sound/sample clocks and the existing chip, start the original
programme proof position without altering chip state, authenticate the exact
new bank, verify the actual full driver/IY/logical-PSG checkpoint at each
capability boundary, and revoke on subsequent unsupported host actions.
It must compare uninterrupted persistent-chip PCM across the actual prelude,
restart and extension. Original-only convergence plus solo certificates are
insufficient to declare that new candidate gate implemented or accepted.

## Evidence provenance and limits

Read AUDIO-0 [request audit](audio-request-audit.md), the corrected
[M5 integration contract](m5-driver-integration-contract.md), accepted C1–C9
decoder/PCM work, and B0-D CROSSWALK/RECONCILIATION at private POC commit
`1c7fb623c32f16b1fda0c9e070b92bb07ad1fb1d` (original source pin
`afdd6a1e62e5e61234159266a05bcddab825faf9`). B0-D is a historical source
inventory, not current native eligibility. Its unresolved writers remain
unresolved; notably a state11 exit choosing81 for ordinary zones must not be
silently treated as original zone-table restoration. G1 should reconcile the
actual current writer against189B, separately from driver playback support.

Fresh ROM execution hash-checks Europev1.2
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Original captures are frozen before candidate comparison. Every verified tick
compares seven complete channel structures, globals, IY, logical PSG/data latch,
priority, saved noise, transfer edges and ordered PSG writes. An independent
400-byte reconstruction additionally checks the entire original driver RAM,
including zero unused globals, on every captured tick. Candidate equality of
those components therefore covers the full400 bytes, not merely active headers.

Both continuous PCM streams use accepted A1L
`47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65`,
PAL3546893Hz,44100Hz,735 samples/update. Every tick also compares100+635 versus735
render partitioning and all26 native before/after state fields. A fresh isolated
process per schedule loads only private banks, host schedules and the decoder;
three tested guards deny ROM reads, original-capture reads and original-CPU
imports. No audio file supplies playback.

These are204 controlled schedules,130350 differential ticks and95807250 exact
PCM samples, with zero state/PSG/transfer/PCM/native/partition differences.
The separate ten original epoch probes compare50010 post-reset ticks and
deliberately demonstrate differences from freshly created physical chips.
Do not count those expected chip-phase differences as successful equality tests.
Detailed counts and hashes are in evidence.json, original.json, verified.json,
writers.json and epochs.json under data/m5-g1r.
All37 fresh negative controls are detected: repacked C9 certificate rejection,
post-request/fade4201 rejection, older83/92/8F post-SFX rejection and corrupted
full-state shadow checks. Seven new public evidence tests and all seven inherited
C9 public tests pass. Earlier catalogue tests are reused as earlier evidence;
their original driver/PCM proofs were not repeated here.

Five writer schedules execute original4A74/reward logic with original gameplay
bank mapping and IRQ nonzero deferred delivery. The inherited frame-wait stub
is explicit; pickup time30 and Sneakers time130 are seeded. Invincibility expiry
is630, ordinary Rocket expiry330, SS4 Rocket restores8F at330; SS1 writes no85.
Invincibility→Sneakers has no restoration and music becomes inactive1117.
These are controlled counterfactual/routine fixtures, not naturally collected
monitors or an assertion of every gameplay scheduler phase. Other transition
fixtures use independently supported IDs/order but deliberately controlled timing.
No new natural-route, hardware, Windows F5 or native G1 acceptance is claimed.

## Reproduction and review boundary

Use installed Python3.13 with existing z80/NumPy and the accepted A1L DLL.
Private prerequisites are the unchanged C6, R83, C7-batch and C9 banks.

```text
python tools/m5g1r_source.py PRIVATE_ROM
python tools/m5g1r.py original PRIVATE_ROM
python tools/m5g1r.py prepare
python tools/m5g1r.py verify
python tools/m5g1r_evidence.py
python -m unittest discover -s tests -p test_m5g1r.py
python -m unittest discover -s tests -p test_m5c9.py
```

Public material contains harness code, aggregate facts, small host action
schedules, state/source/bank/PCM hashes and contracts only. ROM, programme
records/SCSP, raw captures, waveform data and binaries stay outside Git in
`<PRIVATE_RESEARCH_ROOT>/m5-g1r`. Inspect staged material before publication.
Manager review is the next step; no integration or automatic milestone follows.

Publication inspection covered all12 added text files: seven aggregate/schedule
JSON files, three Python harnesses, one evidence test and this report. JSON
leaves/array roles were inspected: no payload/hex/source-record arrays or raw
per-tick state/write/PCM streams occur; the largest array is the39 small writer
gate cases. Code literals describe addresses, requests, state-field offsets and
the explicitly synthetic wait stub, not copied programme data. No original
ROM, SCSP, captures, audio, binary or absolute private workstation path is
published. The detailed file/hash inspection receipt stays private.

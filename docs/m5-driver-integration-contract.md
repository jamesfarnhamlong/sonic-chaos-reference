# M5 full original-driver integration contract

24 October 2026. Research only; Manager review required. Authority: management
`main@600951fde25ab27b3acf4bc6c6881f3f13654100`, accepted audio research
`8df6e7e65ea93f7e49f0f975137eb55c0c5e5bf5`, private POC
`poc/m4-authentic-six-id-audio@11bff34356d5f5d979218896dc95fdc4bb265eae`.
The public Research topic is a direct continuation of accepted M4, not a merge
into main. AGENTS, MEMORY and ROADMAP on management main were read; none changed.

The ROM was available locally and SHA-256 authenticated before execution:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
All new execution below is the existing isolated kosarev Z80 driver harness,
sound banks 2/3, entry CPU `$4000`, not hardware, a new campaign replay, PCM
rendering, listening or GameMaker execution. CPU addresses in this document
are sound-bank CPU addresses; add `$4000` for their ROM file offsets.

## Request and update order

The byte-checked entry `$4000..$4065` establishes this exact order:

1. Pause `$DE08`: zero continues; negative decrements once and jumps to PSG
   silence; subsequent positive values return without arbitration or progression.
2. Arbitration `$407F`, then tempo `$4066`, then fade `$40B0`, then selected
   request dispatch `$4119`. Earlier AUDIO-1/M4 shorthand placing tempo before
   arbitration is superseded by this entry-path inspection.
3. Active music tone0, tone1, tone2, music noise, then SFX tone1, tone2, noise.
   Channel update order matters: an SFX release occurs after that tick's music.

Use existing `chaos_audio_write`, `chaos_audio_gameplay`, and `chaos_audio_tick`
as extension points. Preserve write sites, diagnostic sequence, single persistent
owner, queue and shutdown machinery. `$D4A4` game-side nonzero delivery to `$DE04`
at IRQ can replace a direct request. The original IRQ forwards only a **nonzero**
deferred byte; M4's explicit written-zero transfer is an adapter difference,
not a ROM rule. Keep accepted M4 behavior until a scoped integration change and
differential test establish the intended M5 correction. Zero written directly to
`$DE04` can cancel a still-pending request. It does not silence running audio.

Driver pending slots `$DE04,$DE05,$DE06` are consumed in that order. Each byte
is cleared. Ignore a byte whose low seven bits are zero. Otherwise compare
`ROM[$906F+(id&$7F)-1]` with global `$DE0F`; strictly lower drops, equal wins.
On admission store `priority&$7F`, and replace selected `$DE03` with the ID.
Only the final admitted selection dispatches. This is neither a FIFO nor a
per-channel priority policy. Gameplay evidence uses `$DE04`; auxiliary mailboxes
have no established ordinary game writer. Do not expose unindexed driver
controls `$D0..$D3` as extra catalogue sounds.

M5 executes all 37 SFX plus F8 against all128 possible stored priority values
(4,864 assertions). Numeric F8 reads raw priority **$57** from ROM$90E6
(the lookup reaches the adjacent index table); it is dropped if current
priority exceeds$57. This is original executed behavior, not an invented
control exemption. Music raw priority `$80` admits against every stored priority;
initialization resets channels and priority, including on repeated IDs. Full
request priorities remain distinct even when two IDs have identical solo output.
Never replace `$DE0F` by the maximum priority of currently active effects.

## Channel ownership, stealing and recovery

| Voice | Music structure | SFX structure | Initialization latch |
|---|---|---|---|
| tone0 | `$DE40` | none | `$80` |
| tone1 | `$DE70` | `$DF00` | `$A0` |
| tone2 | `$DEA0` | `$DF30` | `$C0` |
| noise | `$DED0` | `$DF60` | `$E0` |

Each structure is `$30` bytes. Bit7 is active, bit2 suppresses PSG output,
bit4 inhibits output until eligible stream progression, bit6 selects fixed-noise
behavior on SFX noise. Header flags, latch, multiplier, pointers, transpose,
attenuation and each slot's solo release tick are in [catalogue.json](../data/m5/catalogue.json).
The word index is ROM `$90E1`; music header channel initialization is `$422B`,
SFX initialization `$41A7..$422A`. A new SFX replaces **only** its header-selected
slots; other SFX can continue. `$AC,$B6,$BA` have tone1 and noise streams; their
different header stream order must be retained. Tone0 has no SFX slot.

Do not infer physical ownership solely from the header latch. Noise effects
can use tone2 as their noise clock. Command F3 (`$4753..$47AB`) writes its
noise-control operand. With low two bits 3, it turns tone2 attenuation off,
clears bit6 on the noise stream and suppresses music tone2 and SFX tone2.
With a fixed noise rate it sets bit6 and releases suppression on music tone2
when SFX tone2 is inactive, otherwise on the active tone2 effect. The driver
also has the `$DE0D`/active-tone2 rejection branch at `$4753..$477B`; port this
branch from source, not a blanket “noise wins” policy. The condition tests the
stored SFX request byte's sign, the command operand's low bits and active DF30.

Starting a tone2 SFX (`$41CD`) checks bit6 on the noise SFX slot. If clear,
it sets noise-slot bit2 and emits noise-off, even if that slot is active.
Fixed-rate noise is allowed to coexist. Music noise can rewrite noise control
later in the same tick before SFX channel execution; a standalone WAV does not
encode every resulting oscillator/noise phase.

F2 (`$47C8..$481B`) clears the ending slot and global priority **even if another
slot remains active**. Tone1 releases its music channel. Tone2 releases music
tone2 unless noise is active, in which case it releases noise-slot suppression.
Noise completion restores saved music noise control `$DE11`, and, for coupled
noise with no active tone2 effect, releases music tone2 and clears DF30.
Affected music gets bit2 cleared and bit4 set, plus attenuation-off. Do not
resume an effect it replaced or restart the interrupted music.

Music continues to advance while suppressed. Tone music clears bit4 at stream
reader `$4341`; noise uses **a different reader**, `$4650`. A read may itself
execute a rest/end/envelope condition that keeps output inhibited. Recovery
metadata must therefore represent eligible reads plus original output flags,
not just “next audible note” or a fixed delay. M4's `$4341` map cannot cover
music noise. Publish no complete private read timeline to Research.

New controlled evidence: [interactions.json](../data/m5/interactions.json)
has all 1,369 ordered SFX pairs at requests30/35 over THZ, plus each ID's
restart, music replacement and reset (1,480 scenarios). These are bounded
phases, not every possible timeline. [extensions.json](../data/m5/extensions.json)
adds each SFX at three THZ phases (111 cases), with per-channel release and
next-reader recovery facts. The published facts omit full port/read streams.

Concrete controls to preserve:

- BF at30, A3 at35: tone2 and noise SFX remain active together; BF becomes
  suppressed. At50 BF ends and **priority becomes0 while A3 remains active**;
  A3 ends83. A later low-priority request can now be admitted.
- AC at30, A0 at35: tone1, tone2 and noise slots coexist. Noise ends78,
  tone2 ends80, tone1 ends83. Do not stop all three when the first ends.
- B6 at30, A0 at35: noise ends45 and clears priority while tone1/tone2 live;
  tone1 ends56, tone2 ends80.
- Reversing request order can drop a lower-priority sound even on a different
  channel. Admission precedes channel ownership.

## Music lifecycle and gameplay events

Every admitted music ID initializes from its own header after reset. There is
no saved-position stack. Death96, clear89/97, Continue94, full ending8D,
partial ending9A, TRY AGAIN98, success86 and title99 are finite original cues.
Invincibility84 and Rocket85 are also **finite**, not indefinite loops.
Do not auto-restart them. The game may replace them earlier with restored
level music. Level restoration `$189B` starts the zone song afresh, subject to
`$D4A3`. The inherited Silent Sneakers mechanism remains authentic evidence:
Sneakers can replace selector6 with3 without a new song or restoration,
allowing finite84 to end in silence. Do not “repair” that through an automatic
music fallback.

Zone table: THZ81, GPZ83, SEZ91, MGHZ92, AQZ93, EEZ1/2 95, EEZ3 **90**;
all five Special Stages8F. Ordinary boss8C; first EEZ encounter8B; ending
selectors as above. Opening90 is the same indexed composition as EEZ3;
M4's short opening-specific asset and skip-tail bank cannot supply its full
EEZ3 loop. Preserve accepted opening assets and extend scene90 resolution
to the new full composition only for gameplay/Sound Test.

Exact contexts and source offsets for each entry remain in the matrix, inherited
from AUDIO-0 with explicit later corrections. Important event ordering:
clock pickupF8, ten nonzero B5 countdown requests, then restarted8F; success
transition8A then result86; timeout/failure follows original failure/fade path,
not success86. SS1 Rocket reward skips85; other Rocket contexts use85.
Emerald touch has no unique immediate sound, nor does Sneakers pickup.
Ring wrapping can overwrite BF with A9; guarded destructionC4 only writes
when the direct mailbox is empty. Keep these game-side gates before arbitration.
Choice82, cursorB4 and confirmA0 are separate from title99 and title lead-inBE.

A request site is not proof of natural observation or audibility. The matrix
explicitly separates static source contexts, isolated-driver output, existing
M4 Windows scope and per-ID original gameplay observation, which is not
established for the whole catalogue. Unknown entries retain neutral labels.

## Fade, reset and pause

`$00` has no dispatch and no audio file. **Admitted** `$F8` reaches reset `$43E5` after
arbitration; clears all seven channel structures/global driver state and emits
PSG silence in the same driver call. Music initialization also resets everything.
Administrative queue flush is a PC lifecycle operation, separate from a numeric
ROM request. Keep both APIs distinct in diagnostics. M4 currently treats F8
as unconditional reset; retain its accepted behavior until Manager reviews
this newly measured extension/correction. The pair-reset fixtures deliberately
retain cases where the original F8 is dropped; do not assert all37 reset.

Direct fade uses `(DE09,DE0A,DE0B)=(12,1,2)`. New inspection corrects an overly
broad older description: `$40B0..$40E6` **deactivates active SFX immediately**
and removes the corresponding music suppression; it does not fade every SFX
to its natural end. It then advances counters, increases tone music volume
offsets and shared noise offset DE16 (cap logic at `$4112`), ending in reset.
The controlled BA case has SFX at34, none at35 when fade starts, reset at57.
Dispatch follows fade: a request on that tick can initialize after fade work.
On the final fade tick, reset clears the selected byte as well: a99 request
selected before terminal reset is erased, and must not start afterward. A
focused original-driver regression preserves this boundary.
Do not implement fade as simply continuing active one-shots under master gain.

The accepted opening phase bank remains exact within its documented rendering
tier. Generic M4 gain fade is a **declared approximation**: PSG envelope+offset
clamping differs from multiplying an already mixed PCM block. Preserve it
until Manager approves M5's policy. Exact arbitrary-phase PCM fades would need
additional phase-consistent attenuation variants or scene-specific tails;
do not silently introduce crossfades/synthesis or a huge all-phase bank.

Pause freezes driver arbitration, clocks and pointers after initial mute.
Pending mailbox writes can accumulate/overwrite while paused; resume dispatches
the final pending byte before normal channel updates. M4 freezes the native
queue/cursor rather than reproducing the original 1–3-update reassertion; keep
that accepted PC adaptation and single-owner reactivation/shutdown safeguards.

## M5 state and asset contract

Extend the existing audio state with three independently aged SFX slots and
four music voice gates/recovery positions, shared priority and noise control/
coupling state. Preserve absolute music age, use one sample phase per shared
tick and preserve each stream's own release time. A two-stream effect requires
separate assets/metadata for each slot, not a combined file that cannot be
partially stolen. Noise effects that drive tone2 require a matched noise+tone2
ownership group. Keep per-channel generation numbers so replacing one slot
cannot let a stale release event clear a newer occupant.

Private metadata schema must include: ID and context variant; source/tool/PCM
hashes; sample format/count; per-voice PCM chunks; common loop cut/body or
finite endpoint; per-slot init/flags/priority/end; suppression/recovery maps
from **both** readers and F3 transitions; noise control dependencies; any
unsupported/empty state; provenance and native acceptance. No script payload,
ROM bank or runtime emulator is required. Conditional control metadata belongs
in private POC, with safe aggregate verification here.

The original-driver state transition rules above are established; exact PCM
equivalence for arbitrary multi-SFX noise phase, dynamic release transients and
generic fades is **not established by isolated renders**. Preserve M4's known
oscillator-phase compromise explicitly. The production gate must compare
composed mixes to original-driver continuous rendered controls, including
coupled-noise interruptions, before claiming a complete faithful hybrid.
Failure is a focused stop for Manager, not permission to rewrite the accepted
queue or substitute synthesis. See [production plan](m5-production-plan.md).

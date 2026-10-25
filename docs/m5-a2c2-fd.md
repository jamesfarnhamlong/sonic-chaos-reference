# FD original handler and prerequisite verdict

**PASS for the authenticated SFX tone2 reader scope.** This gate ran before A2
was added to the expanded production-style private bank. It does not enable FD
for every music/noise reader or unrelated command.

25 October2026. Original ROM SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` was freshly
checked. Evidence is original Z80 code inspection plus independent candidate/
original execution, with source-region hashes in [fd-gate.json](../data/m5-a2c2/fd-gate.json).
No other game's sound language supplied semantics.

## Source rule, caller and operand length

The command dispatcher at CPU `$46D5..$46E8` subtracts E0, indexes the handler
table at `$46ED`, loads A from the operand at DE and jumps to the selected
handler. FD's table entry points at `$47BA`.

At `$47BA..$47C7`, compare the operand with1. Equality sets channel flag bit3
at `(IX)`; every other operand clears that bit. The handler returns without
advancing DE, changing other channel bytes or emitting a PSG byte. Return
through `$46E9` advances DE once, then `$46EA` resumes the ordinary stream
reader. **FD is two bytes including its one operand.** Values0,2 and255 are
legitimate clear operations, not unknown subcommands or invalid operands.

The original read path at `$434F..$435A` checks command bytes first. For a
non-command byte, flag bit3 selects `$43C7..$43E4` instead of ordinary note/
inline-volume interpretation. That raw path takes a big-endian16-bit frequency,
adds signed channel transpose if the word is nonzero, stores frequency at
channel+11/+12, takes a following duration, and uses the existing duration
multiplier via `$4391`. A zero raw word does not receive transpose. Stream
bytesE0..FF still dispatch as commands before that mode check. FD changes
parsing, not the underlying PSG packing rules or tempo policy.

FD itself does not clear/reset duration, transpose, modulation, envelope, fine
offset, stack or loop counters. Existing reader/note stages still make their
ordinary updates. Algorithmic pitch modulation continues to operate on the
resulting frequency, including the previously authenticated shared-IY reload
dependency. Ordinary note parsing resumes when a later FD operand is not1.

Original SFX slot initialization `$41F6..$422A` copies new header flags rather
than inheriting a prior raw-mode bit. Thus replacement by a normal-mode header
clears the mode. F2 later clears active flags including bit3; it does not imply
an extra physical PSG mute beyond the original release writes.

## Exact tests before catalogue promotion

[fd_gate.py](../tools/m5a2c2/fd_gate.py) uses the prototype extension, extracting
only actual A2 data into an isolated private fixture. It completes candidate
generation before creating the original oracle. All67 ticks (35 to inactivity
plus32 post) match ordered bytes, PSG/latch, DE11/IY,336 channel bytes and12
globals. Actual A2 executes FD once at update2, operand1: flag128→136 at that
command. Update1 has ordinary-mode inhibited output; raw reading begins in
the same update as FD. Eight raw-reader visits are authenticated. FD treated
as a no-op fails the actual A2 emission comparison at update2.

The gate hooks the original handler entry/return and next stream read to prove
operand consumption: only flag bit3 differs, DE is unchanged at handler return,
and the caller's next read is DE+1. These details are not inferred merely from
the tune ending at the expected tick.

Six additional **synthetic seeded streams** exercise ordinary note→FD1→raw
word→FD0→ordinary note, signed transposes−1/0/+1, duration multipliers1/2 and
algorithmic modulation. Each24-tick candidate is completed before running the
unmodified original driver against the seeded stream. All six match full
state and ordered emission, with two FD transitions each. These authored data
probes are explicitly distinct from naturally reached game programs; they are
never included in the expanded real runtime bank.

Sixteen direct original-handler edge calls cover flags80/88/A4/FF and operands
0/1/2/255. They preserve all other47 channel bytes, leave DE unchanged and emit
no byte. Synthetic candidate tests assert the same source-backed bit semantics.
Negative controls reject a truncated operand, a missing next data pointer and
an unverified reader transition. Command operand values other than1 are **not**
misused as negative controls because the original defines their clear behavior.

## Runtime boundary and release/replacement checks

The [minimal extension](../tools/m5a2c2/decoder.py) subclasses the accepted B1
decoder, handles FD only, increments the command count and returns operand
pointer+1. It permits FD in SFX tone2 slot5/latchC0, the reader authenticated
here. Dedicated music noise, other tones and other SFX reader combinations
raise an explicit unsupported-scope error. This is a prototype verification
boundary, not a claim that the original callee rejects those channels.

The full C2 matrix separately checks actual A2 retrigger and replacement with
spring. Its raw bit is set after FD, disappears at F2 release, and is reset
by the new spring header at the authentic replacement update. All old decoder
commands retain their behavior; E2/E4/E5/E8/ED/F4/FA and other unverified
operations remain fail-fast. A7's raw-frequency **header** already sets bit3
and does not need FD enabled in its noise slot.

SCSP remains version1 and its old records still load. New A2's FD instruction
requires the C2 decoder; an older decoder deliberately rejects it rather than
silently playing a plausible interpretation. Source data, detailed gate traces
and seeded test captures are private. Public source, aggregate verdicts and
source hashes provide the reproducible method without publishing game streams.

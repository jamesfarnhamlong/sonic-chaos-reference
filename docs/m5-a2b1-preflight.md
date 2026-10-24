# M5-A2B1 finite-music preflight

25 October 2026. Original ROM authenticated as
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Research parent `47758830da9bb83ebb19bbd02950757838202763`; management read
`caa149cd9d2031113639884058ab98b058112e70`. This inventory preceded parser
extension and PCM generation. The standalone inventory was rerun with additional
aggregate envelope details; it never decodes candidate audio or promotes a row.

[preflight.json](../data/m5-a2b1/preflight.json) contains all twelve original
headers, channel pointers/transposes/volumes, actual reached opcode counts,
potential syntax/control-flow sets, envelope/pitch variants and complexity.
Names below are unchanged from the accepted R1 catalogue.

| ID | Existing authenticated label | Original inactive tick | New required command versus A2 | Structural counted-loop sites | Implementation scope |
|---|---|---:|---|---:|---|
|84 | Invincibility music |1088 | E1 |11 | authorised |
|85 | Rocket Shoes music |432 | none |4 | authorised |
|86 | Special Stage success results music |300 | none |0 | authorised |
|87 | Game over music |408 | E1 |0 | authorised |
|89 | Ordinary act-clear music |242 | E1 |0 | authorised |
|8A | Special Stage entry / success transition music |179 | E1 |4 | authorised |
|8E | Unknown $8E |188 | E1 |0 | preflight only |
|94 | Continue-screen music |1081 | none |2 | preflight only |
|96 | Player death music |340 | none |0 | preflight only |
|97 | Act 3 clear music |274 | E1 |0 | preflight only |
|98 | TRY AGAIN ending-card music |305 | E1 |2 | preflight only |
|9A | Partial Sonic ending music |1153 | E1 |4 | preflight only |

All twelve have four music channels and envelope-base metadata `$49FD`. Their
duration multiplier/tempo pairs are respectively `2/4,2/4,1/5,1/3,1/5,1/26,
1/6,1/0,1/6,1/6,1/3,1/0`. Header interpretation uses original `$4168..$4262`;
tempo update is `$4066..$407E`. Zero divider is a supported original setting,
not an inferred BPM. No original observed termination exceeded the1500-tick
preflight budget, and all twelve match their inherited R1 inactive ticks.

The bounded structural scanner walks stream-token boundaries, both counted-loop
outcomes and call/return contexts. It handles known command operand lengths,
note-duration reuse, music noise and raw-frequency mode. Work bound20000 nodes;
call bound3 pairs. All twelve terminate structurally without a call site,
unclassified command or required table-pitch selector. Structural counted-loop
site counts are not dynamic iteration counts. The union of potential command
sets equals the dynamically reached sets in this scan; neither proves reachability
under corrupt data or every later interference context. Detailed streams are
never saved publicly.

An independent original Z80 run per ID starts from the authenticated idle
baseline and ends only when all original slots are inactive. Breakpoints record
command dispatch, volume/pitch selector use, ADSR state visits and modulation
reload paths. No PCM or full expected event timeline is exported for the six
deferred candidates. These observations classify original paths; they are not
candidate correctness evidence.

The first batch uses existing algorithmic vibrato, ADSR, table volume envelopes,
ties, counted loops, transpose and F2 termination. None requires table pitch.
Reached table-envelope selectors:84 uses29/30/39;85 uses4/27/29/30/39;86 and87
use29/30/39;89 uses6/7/23/29/30/39;8A uses algorithmic volume. The preflight of
each selected table reaches ordinary attenuation steps followed by82 terminal
off. All reached ADSR modes are retained in JSON. No unknown DE-relative envelope
control is guessed. Context-dependent envelope advancement remains a separate
interaction obligation, addressed only for the selected proof windows.

**One necessary extension:** E1 dispatches to original CPU `$487E..$4881`, a
write of the operand to channel `+$25` (decimal37), then returns. Existing
`$4504..$450D` applies that field as a signed frequency offset. The selected
original E1 operands are positive; negative/edge operands receive synthetic
arithmetic tests, not a claim of naturally reached negative game data. The
implementation extends only this command. E2/E4/E5/E8/ED/F4/FA/FD, positive
table pitch, alternate envelope bases, DE08 and numeric D0/D1/D2 remain unverified.

Complexity is low for85/86 using A2's reached language;84/87/89/8A require a
small source-backed E1 extension and full-state checks. Longer finite84, looped
envelopes in85, and large gate-divider26 in8A deserve complete runs rather than
short previews. The six deferred candidates appear to use the same preflighted
classes, but have no expanded private program records, candidate completion,
PCM validation or ROM-free playback in this milestone. Recommend a separately
authorised remaining-finite batch; do not count preflight as implementation.

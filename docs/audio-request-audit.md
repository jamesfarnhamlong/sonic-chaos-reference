# AUDIO-0: canonical audio request ledger

Target: Sonic Chaos SMS Europe v1.2, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Base: fetched Research main `6874337671d01891909a1b5d439e0baba3fbfb80`.
This branch changes Research only and stops for Manager review.

The reproducible [JSON ledger](../data/rom-cache/audio/request-ledger.json)
contains **70 unique IDs: 31 music, 37 SFX, 2 control**, with **193 site/context
rows**. The 68 pointer-index IDs are classified by the original driver's
request dispatch, replacing the earlier *reported* music/SFX split for this
ledger. This is a category classification, not a claim that every entry is
used in gameplay or has a distinct audible composition. **24 music entries,
13 SFX entries and both controls have independently supported context names**.
31 names remain unresolved; nine indexed IDs have no verified gameplay/script
request site. No playback recording, PSG rendering, transcription, instrument
reconstruction or cycle-perfect timing is claimed.

## Reproduction and evidence boundaries

With Python 3.8+ and `requirements.txt` installed:

```powershell
python tools/audio_requests.py "$env:SONIC_CHAOS_ROM"
python tools/audio_requests.py "$env:SONIC_CHAOS_ROM" --check
python -m unittest discover -s tests -p test_audio_requests.py -v
python -m unittest discover -s tests -p test_ss_powerups.py -v
python -m unittest discover -s tests -p test_decomp1c.py -v
git diff --check
```

The tool hash-checks the local-only ROM. It emits metadata, offsets and hashes;
it does not emit ROM payloads or sound streams. Human context annotations live
separately in [audio-request-contexts.json](../data/audio-request-contexts.json).
Names describe an independently established *requesting event*, not an inferred
acoustic resemblance. A named feedback can occur in other contexts too.

Each JSON request retains the numeric ID, driver category, name/status/source,
pointer metadata, arbitration byte, and individual verified sites with ROM
file offset, physical bank and CPU address. Direct sites require the exact
immediate load/store encoding. Conditional/table requests retain their source
operand and condition. `FF 06` sites retain type, state, type-table entry,
state-pointer operand, script start and operand offset. Script reachability
is explicitly static; it does not claim that all pointer-table aliases are
instantiated in gameplay. Types $33/$40..$50, for example, share scripts.

The accepted bounded object parser is used with the independently derived
command-06 handler semantics and scheduler bank selection. The player parser
walks all command branches. Three bounded object-script tails remain without
explicit terminators (type $16/$2D/$2E state3); this is recorded, not repaired.
The scan of `LD ($DE04),A` patterns is only a completeness cross-check, never
a way to infer code from arbitrary bytes. All matches in this ROM were reviewed;
shared dynamic sites are represented separately. Indirect writes or novel
script entry paths outside the accepted parsers are not exhaustively excluded.

Addresses use half-open ROM ranges. Resident gameplay code uses file offset =
CPU address below $8000. Gameplay bank $0C/$1E scripts use slot2 ($8000).
**Sound bank2 executes in slot1 ($4000)**, with bank3 in slot2; thus driver CPU
$4119 is ROM $08119, not gameplay file $04119. This distinction is essential.

## Request selection, replacement and silence

The IRQ at ROM $005C9..$005DF forwards a nonzero deferred `$D4A4` request into
`$DE04`, clears the latch, maps sound banks and calls driver CPU $4000. The
script command handler at ROM $067D5..$067EC writes the same operand to `$DE04`
twice, back-to-back. These are mailbox writes, not a queue of sound instances:
a later write before driver consumption replaces an earlier one.

Driver ROM $0807F..$080B0 examines three pending bytes ($DE04..$DE06), clearing
each. A zero low-seven-bit value is ignored. Other values use the priority byte
at ROM `$0906F + (ID & $7F) - 1`: a value **below** current `$DE0F` is dropped;
equal priority is accepted. This is proved with $BF at priorities 0, $38 and
$7F (accepted, accepted, rejected). It is a local arbitration result, not an
exhaustive priority/channel policy for every event.

Dispatch ROM $08119..$08138 routes $81..$9F to music initialization, $A0..$C4
to SFX initialization, $D0..$D3 to a control jump table, and $D4..$FF to reset.
The latter includes the game's **$F8 reset/silence** request. Acceptance still
passes through arbitration first. Music initialization at $08168..$081A7 calls
reset $083E5 before loading stream headers: it replaces music and active SFX,
with no saved song-position stack. A later level-music request starts from its
header; it is not a continuation from the interrupted note.

There is no same-ID early return in these initialization paths. Controlled
reissues of $81/$84/$85 and $BF/$C4 reproduce the initialized 11-byte headers
of their active channels after ten updates. This proves restart for these
accepted requests; it does not promise admission despite a higher priority.
SFX initialization $081A7..$0822B sets bit2 on the corresponding music channel
and installs a separate SFX stream. It does not load a different song header.
Detailed stealing, end-of-SFX restoration and PSG output are deferred.

**$00 is not silence.** Act-clear paths at $014E5/$0157A write zero to the
pending mailbox. A controlled already-playing $81 remains unchanged by a zero
request. Silence/fade at transitions comes from other paths: goal sign state4
requests $F8, while `$18E1` directly sets driver fade counters `$DE09=12`,
`$DE0A=1`, `$DE0B=2`. Fade processing begins at driver ROM $080B0 and eventually
reaches reset. The direct fade helper is recorded separately from request IDs.
The driver recognizes $D0..$D3, but this audit found no gameplay request for
those IDs and does not add them to the observed/indexed ledger.

The shared destruction callback ROM $061D6 requests $C4 **only when $DE04 is
empty**. This game-side suppression precedes driver priority. A ring counter
wrap requests $BF and then extra-life $A9, so the latter replaces the pending
ring effect. Rocket damage similarly calls level-music restoration before
writing $C3; deferred `$D4A4` delivery can overwrite the immediate effect at
IRQ. These are ordering facts, not claims that every request becomes audible.

## Music lifecycle and Silent Sneakers

`UpdateMusic` $189B returns without a request when `$D4A3 != 0`. Otherwise it
indexes ROM $18BA by `zone*3 + act`, writes both $DE04 and deferred $D4A4. The
normal-zone table is $81/$83/$91/$92/$93 for THZ/GPZ/SEZ/MGHZ/AQZ;
EEZ1/2 use $95 and EEZ3 uses $90. All five Special Stages use $8F.

Ordinary boss entry requests $8C through scripts and/or the shared intro.
Ordinary boss defeat ultimately invokes $4892: $97 when act index is2,
otherwise $89. This replaces the boss music with clear music. The EEZ chain
is distinct: type $5E state0 requests $8B; its handoffs to $60/$61/$62 are not
ordinary act-clear resumptions. Final flags take the ending selector, where
full Sonic/Tails request $8D, partial Sonic requests $9A, and TRY AGAIN requests
$98. See the accepted [endgame audit](eez-boss-endgame-audit.md).

Invincibility reward $4B1D requests $84 **before** checking whether selector
$D532 is already6. It reloads the timer to600 even for repeat pickups, so a
repeat can restart music. Ordinary Rocket Shoes requests $85, selects4 and
uses300 updates. Timer expiration restores the zone table through $189B for
selectors4/6 and clears the selector. There is no song-position resume.

Power Sneakers reward $4B0F selects3 and loads900, with **no audio request**.
At zero, $4A8F..$4AA3 restores music/clears the selector only for4/6. Selector3
therefore stays3; the next decrement underflows its timer to $FFFF. No music
restoration accompanies that event.

This produces a **ROM-backed Silent Sneakers mechanism**, demonstrated by a
controlled counterfactual using the original reward/timer routine and driver:

| Fixture | Requests after initial $84 | Timer / selector result | Driver music result |
|---|---|---|---|
| Invincibility alone | $81 at update600 | selector cleared | level music remains active |
| Sneakers picked at update100 | none through1200 | timer zero1000, underflow1001, selector remains3 | $84 channels inactive at1089; silence remains |

The standalone original-driver run ends $84 at call1088. The paired fixture
has one extra initial dispatch boundary, hence1089. These are controlled driver
update counts, not wall-clock song durations. The fixture supplies only bank
switches and the IRQ's deferred-mailbox delivery; it does not synthesize PSG
output or replay a natural input route. It proves this mechanism; matching a
particular community video/input sequence remains an observation task.

## Special Stage closure and scoped event coverage

| Event/path | Request facts and exact locations |
|---|---|
| SS1 Rocket Shoes | $4AEE/$4787 zone8 fork skips $85 and frame wait; $8F continues. Other stages use ordinary pickup $85 and restore $8F at expiry. |
| Clock monitor | $4B0B requests $F8; eleven frozen one-second ticks. Ten nonzero ticks request $B5 at $2858; the eleventh calls $189B and restarts $8F. A recollection reloads11. |
| SS entry/success | $8A at $17B2/$1844. Success card $D2CD=FF requests $86 at $33CB. |
| SS timeout/death | Timeout sets failure at $2846; death $4984 checks zone>=8 and branches to stage failure before ordinary $96. Failure $1815 uses death routine/fade, then shared results; it does not request $8A or success $86. |
| Chaos Emerald | Type $31 contact sets completion/success flags and continue reward; **no immediate sound request**. Next main-loop success transition supplies $8A, then results $86. |
| Large Ring | $BF at $7640; +10 rings can replace it with $A9 on wrap. It has no independently proved unique sound ID. |
| Spring Shoes | Pickup has no unique immediate request; floor relaunch $C2 at $3B8A. Ordinary spring setters use $A6. |
| Monitors | Breaking uses shared destruction $C4 when mailbox is empty; reward dispatch separately selects life $A9, invincibility $84, Rocket $85, clock $F8, or no unique music for rings/Sneakers. |
| Boosters / crumble / break | Booster $BD at $7662; type $13 state1 and type $07 state0 scripts request $A3 for crumble/shards. |
| Ordinary badnik defeat | Shared conversion to type $0F; callback vector $03EF reaches guarded $C4 at $61DD. Hurt with rings $A4 at $493F; Rocket-cancel hurt $C3 at $490F; ordinary death $96 at $49B6. |
| Boss hits/defeat | Shared/zone-specific attack contact $B6; GPZ attached-contact $AB, head reaction script $B3; MGHZ landing $B9 / projectile scripts $BE; clear $89/$97. Context alone does not identify their acoustic timbre. |
| Zone hazards | AQZ drowning numeral type $32 scripts use $B5, final branch $96 at $7957B; EEZ tube entry uses $A5 and exit $BA at $311FA; moving-spike type $1B state1 uses $A7. Exact script/callback sites stay numeric where names are unresolved. |
| Title / menus / continue | Title entry $04B4->$3065 requests $82 at $30BC. Character changes request $B4 at $3581/$3591; acceptance $A0 at $3566. Continue $94 at $141D, countdown $B4 at $1487, accept $A0 at $148E. No accepted continue: game-over $87 at $13A5. |

The clock count corrects loose earlier prose saying every one of11 ticks plays
$B5: ROM $2853 jumps to music restoration on zero, so there are **ten $B5 writes**.
No Special Stage gameplay or POC implementation was changed.

## Full numeric index

Locations below are ROM offsets, deduplicated across static aliases. The JSON
retains each type/state or zone/act condition separately. Unknown means the
friendly name is unresolved; driver category and numeric sites still stand.

<!-- AUDIO_TABLE_START -->
| ID | Driver category | Supported context name | Verified ROM request locations |
|---|---|---|---|
| $00 | control | empty pending request (not silence) | $014E5, $0157A |
| $81 | music | Turquoise Hill Zone music | $018B3 |
| $82 | music | Title / character-selection music | $030BC |
| $83 | music | Gigalopolis Zone music | $018B3 |
| $84 | music | Invincibility music | $04B28 |
| $85 | music | Rocket Shoes music | $04790 |
| $86 | music | Special Stage success results music | $033CB |
| $87 | music | Game over music | $013A5 |
| $88 | music | Act title-card music | $031AE |
| $89 | music | Ordinary act-clear music | $048A3 |
| $8A | music | Special Stage entry / success transition music | $017B2, $01844 |
| $8B | music | EEZ first encounter entry music | $7AF68 |
| $8C | music | Ordinary boss music | $795B1, $79AAD |
| $8D | music | Full Sonic / Tails ending music | $01944, $01B37 |
| $8E | music | unknown | none found |
| $8F | music | Special Stage music | $018B3 |
| $90 | music | EEZ act 3 / intro-index music | $018B3 |
| $91 | music | Sleeping Egg Zone music | $018B3 |
| $92 | music | Mecha Green Hill Zone music | $018B3 |
| $93 | music | Aqua Planet Zone music | $018B3 |
| $94 | music | Continue-screen music | $0141D |
| $95 | music | Electric Egg Zone acts 1 / 2 music | $018B3 |
| $96 | music | Player death music | $049B6, $7957B |
| $97 | music | Act 3 clear music | $048A3 |
| $98 | music | TRY AGAIN ending-card music | $034FC |
| $99 | music | unknown | $00756 |
| $9A | music | Partial Sonic ending music | $01AA0 |
| $9B | music | unknown | none found |
| $9C | music | unknown | none found |
| $9D | music | unknown | none found |
| $9E | music | unknown | none found |
| $9F | music | unknown | none found |
| $A0 | sfx | unknown | $0148E, $03566 |
| $A1 | sfx | unknown | $047BD, $047D0 |
| $A2 | sfx | unknown | $04638, $06A35, $06A55 |
| $A3 | sfx | Break / crumble feedback | $31B02, $322A0 |
| $A4 | sfx | Player hurt with ring loss | $0493F |
| $A5 | sfx | unknown | $047F7, $06D82, $06DB2, $06DE9, $06E30, $06E76, $06EF9 |
| $A6 | sfx | Spring / rebound feedback | $04829, $04864, $0488E, $06AC4, $07497, $074E1, $3242A, $3243A, $7A24E |
| $A7 | sfx | unknown | $32C5A |
| $A8 | sfx | unknown | none found |
| $A9 | sfx | Extra life feedback | $00CAD, $00CE5, $03106 |
| $AA | sfx | Goal-sign spinning feedback | $327EF, $327FA, $32805, $32810, $32831, $3283C, $32847, $32852 |
| $AB | sfx | unknown | $3200B, $32823, $7A122 |
| $AC | sfx | unknown | $039AA, $046DE, $04715 |
| $AD | sfx | unknown | $7A55E |
| $AE | sfx | unknown | $30363, $30C0B |
| $AF | sfx | unknown | $31F95 |
| $B0 | sfx | unknown | $30C78 |
| $B1 | sfx | unknown | $78EA4, $78EC5, $7AFD0, $7AFE9 |
| $B2 | sfx | unknown | none found |
| $B3 | sfx | unknown | $79C86, $79C95 |
| $B4 | sfx | Results tally / continue countdown feedback | $01487, $02F45, $03581, $03591 |
| $B5 | sfx | Countdown numeral / frozen-clock tick feedback | $02858, $794D0, $794D7, $794DE, $794E5, $794EC, $794F3 |
| $B6 | sfx | Boss attack-contact feedback (not always damage) | $799E7, $79E3D, $7A3FC, $7A66B, $7AAF1, $7AD0A, $7B331, $7B7AB |
| $B7 | sfx | unknown | $325B2 |
| $B8 | sfx | unknown | $3083C |
| $B9 | sfx | unknown | $7A5F5, $7B0AB, $7B0B6, $7B130, $7B1CE |
| $BA | sfx | unknown | $3081C, $30E31, $311FA, $32449 |
| $BB | sfx | unknown | $326D9 |
| $BC | sfx | unknown | $32A68 |
| $BD | sfx | Booster-pad feedback | $07662 |
| $BE | sfx | unknown | $00746, $046FD, $04738, $7A6FA, $7A719, $7BBCC |
| $BF | sfx | Ring / Large Ring collection feedback | $03004, $075D6, $07640, $302CE, $31AF3, $31C2E, $31C49 |
| $C0 | sfx | unknown | $30C7E |
| $C1 | sfx | unknown | none found |
| $C2 | sfx | Spring Shoes relaunch feedback | $03B8A |
| $C3 | sfx | Rocket Shoes damage-cancel feedback | $0490F |
| $C4 | sfx | Shared destruction / explosion feedback | $061DD |
| $F8 | control | reset / silence | $04B0B, $327E8 |
<!-- AUDIO_TABLE_END -->

## Review limits and follow-up

No verified request site was found for **$8E, $9B..$9F, $A8, $B2, $C1**. These
remain indexed driver entries, not proven unused sounds. $99 has a startup
scene request at $00756, but its friendly name remains unknown. Several other
SFX have precise numeric state/callback sites without sufficient independent
support for an event name. The table and JSON make that distinction explicit.

The audit does not resolve every indirect writer, original-game audible
priority outcome, fade race, or synthetic-state reachability. It does not
reopen Special Stage gameplay, modify POC, replace audio, or merge main.
Manager can review the branch's evidence and controlled results before adoption.

Validation: 8 AUDIO-0 tests, 4 accepted Special Stage power-up tests, and 21
DECOMP-1C parser/evidence tests pass (33 total). JSON and human index regenerate
identically; staged `git diff --check` passes. The Windows sandbox required a
workspace-owned TEMP/TMP directory for the existing DECOMP-1C temporary files.

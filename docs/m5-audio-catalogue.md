# M5 complete indexed audio catalogue

24 October 2026. Research-only contract; no M5 PCM was rendered.
Machine authority: [catalogue.json](../data/m5/catalogue.json).
Source: accepted M4 research8df6e7e; management main600951f; private POC11bff343.
All68 indexed headers were executed against the SHA-256-authenticated ROM.
Each row retains all inherited request contexts, addresses and evidence; later corrections are additive.
Static request sites, isolated playback and observed natural use are distinct fields.
No-site and unknown-name entries are not automatically silent or unused.

## Complete matrix

Priority is the raw hexadecimal lookup byte; stored value is masked to7 bits.
End is the first inactive tick from request-at1, not padded WAV duration.
Loop notation is first repeated driver state / period in ticks (60/s).
Slot addresses and every initialization field are in JSON. Sites below are deduplicated ROM offsets.
Unknown labels deliberately remain numeric.

| ID | Kind | Verified label / requesting event | Priority | Lifecycle | Equal solo output | Request sites |
|---|---|---|---|---|---|---|
| $00 | control | empty pending request (not silence) | — | control only | — | $014E5, $0157A |
| $81 | music | Turquoise Hill Zone music | $80 | loop 1093/2688 | — | $018B3 |
| $82 | music | Character-selection music | $80 | loop 130/6912 | — | $030BC |
| $83 | music | Gigalopolis Zone music | $80 | loop 522/3072 | — | $018B3 |
| $84 | music | Invincibility music | $80 | end 1088 | — | $04B28 |
| $85 | music | Rocket Shoes music | $80 | end 432 | — | $04790 |
| $86 | music | Special Stage success results music | $80 | end 300 | — | $033CB |
| $87 | music | Game over music | $80 | end 408 | — | $013A5 |
| $88 | music | Act title-card music | $80 | end 212 | — | $031AE |
| $89 | music | Ordinary act-clear music | $80 | end 242 | — | $048A3 |
| $8A | music | Special Stage entry / success transition music | $80 | end 179 | — | $017B2, $01844 |
| $8B | music | EEZ first encounter entry music | $80 | loop 805/3456 | — | $7AF68 |
| $8C | music | Ordinary boss music | $80 | loop 497/80640 | — | $795B1, $79AAD |
| $8D | music | Full Sonic / Tails ending music | $80 | end 10432 | — | $01944, $01B37 |
| $8E | music | Unknown $8E | $80 | end 188 | — | none verified |
| $8F | music | Special Stage music | $80 | loop 78/1248 | — | $018B3 |
| $90 | music | Opening / Electric Egg Zone act 3 music | $80 | loop 807/19768 | — | $018B3 |
| $91 | music | Sleeping Egg Zone music | $80 | loop 395/32256 | — | $018B3 |
| $92 | music | Mecha Green Hill Zone music | $80 | loop 511/3648 | — | $018B3 |
| $93 | music | Aqua Planet Zone music | $80 | loop 2040/3000 | — | $018B3 |
| $94 | music | Continue-screen music | $80 | end 1081 | — | $0141D |
| $95 | music | Electric Egg Zone acts 1 / 2 music | $80 | loop 1224/4032 | — | $018B3 |
| $96 | music | Player death music | $80 | end 340 | — | $049B6, $7957B |
| $97 | music | Act 3 clear music | $80 | end 274 | — | $048A3 |
| $98 | music | TRY AGAIN ending-card music | $80 | end 305 | — | $034FC |
| $99 | music | Finite title music | $80 | end 1189 | — | $00756 |
| $9A | music | Partial Sonic ending music | $80 | end 1153 | — | $01AA0 |
| $9B | music | Unknown $9B | $80 | empty; unavailable | $9C, $9D, $9E, $9F | none verified |
| $9C | music | Unknown $9C | $80 | empty; unavailable | $9B, $9D, $9E, $9F | none verified |
| $9D | music | Unknown $9D | $80 | empty; unavailable | $9B, $9C, $9E, $9F | none verified |
| $9E | music | Unknown $9E | $80 | empty; unavailable | $9B, $9C, $9D, $9F | none verified |
| $9F | music | Unknown $9F | $80 | empty; unavailable | $9B, $9C, $9D, $9E | none verified |
| $A0 | sfx | Character-choice / Continue confirmation feedback | $78 | end 46 | — | $0148E, $03566 |
| $A1 | sfx | Unknown $A1 | $38 | end 30 | — | $047BD, $047D0 |
| $A2 | sfx | Unknown $A2 | $38 | end 35 | — | $04638, $06A35, $06A55 |
| $A3 | sfx | Break / crumble feedback | $58 | end 49 | — | $31B02, $322A0 |
| $A4 | sfx | Player hurt with ring loss | $70 | end 82 | — | $0493F |
| $A5 | sfx | Unknown $A5 | $38 | end 128 | — | $047F7, $06D82, $06DB2, $06DE9, $06E30, $06E76, $06EF9 |
| $A6 | sfx | Spring / rebound feedback | $38 | end 41 | — | $04829, $04864, $0488E, $06AC4, $07497, $074E1, $3242A, $3243A, $7A24E |
| $A7 | sfx | Unknown $A7 | $30 | end 7 | — | $32C5A |
| $A8 | sfx | Unknown $A8 | $78 | end 46 | $C2 | none verified |
| $A9 | sfx | Extra life feedback | $78 | end 66 | — | $00CAD, $00CE5, $03106 |
| $AA | sfx | Goal-sign spinning feedback | $70 | end 5 | — | $327EF, $327FA, $32805, $32810, $32831, $3283C, $32847, $32852 |
| $AB | sfx | Unknown $AB | $70 | end 9 | — | $3200B, $32823, $7A122 |
| $AC | sfx | Unknown $AC | $50 | end 54 | — | $039AA, $046DE, $04715 |
| $AD | sfx | Unknown $AD | $38 | end 65 | — | $7A55E |
| $AE | sfx | Unknown $AE | $68 | end 15 | — | $30363, $30C0B |
| $AF | sfx | Unknown $AF | $48 | end 68 | — | $31F95 |
| $B0 | sfx | Unknown $B0 | $40 | end 7 | — | $30C78 |
| $B1 | sfx | Unknown $B1 | $48 | end 22 | — | $78EA4, $78EC5, $7AFD0, $7AFE9 |
| $B2 | sfx | Unknown $B2 | $60 | end 58 | — | none verified |
| $B3 | sfx | Unknown $B3 | $68 | end 77 | — | $79C86, $79C95 |
| $B4 | sfx | Results tally / continue countdown feedback | $78 | end 31 | — | $01487, $02F45, $03581, $03591 |
| $B5 | sfx | Countdown numeral / frozen-clock tick feedback | $68 | end 19 | — | $02858, $794D0, $794D7, $794DE, $794E5, $794EC, $794F3 |
| $B6 | sfx | Boss attack-contact feedback (not always damage) | $68 | end 27 | — | $799E7, $79E3D, $7A3FC, $7A66B, $7AAF1, $7AD0A, $7B331, $7B7AB |
| $B7 | sfx | Unknown $B7 | $48 | end 7 | — | $325B2 |
| $B8 | sfx | Unknown $B8 | $48 | end 139 | — | $3083C |
| $B9 | sfx | Unknown $B9 | $48 | end 31 | — | $7A5F5, $7B0AB, $7B0B6, $7B130, $7B1CE |
| $BA | sfx | Unknown $BA | $48 | end 25 | — | $3081C, $30E31, $311FA, $32449 |
| $BB | sfx | Unknown $BB | $70 | end 65 | $C4 | $326D9 |
| $BC | sfx | Unknown $BC | $60 | end 29 | $C0 | $32A68 |
| $BD | sfx | Booster-pad feedback | $58 | end 23 | — | $07662 |
| $BE | sfx | Title lead-in / MGHZ projectile script feedback | $50 | end 38 | — | $00746, $046FD, $04738, $7A6FA, $7A719, $7BBCC |
| $BF | sfx | Ring / Large Ring collection feedback | $38 | end 21 | — | $03004, $075D6, $07640, $302CE, $31AF3, $31C2E, $31C49 |
| $C0 | sfx | Unknown $C0 | $40 | end 29 | $BC | $30C7E |
| $C1 | sfx | Unknown $C1 | $30 | end 10 | — | none verified |
| $C2 | sfx | Spring Shoes relaunch feedback | $40 | end 46 | $A8 | $03B8A |
| $C3 | sfx | Rocket Shoes damage-cancel feedback | $70 | end 46 | — | $0490F |
| $C4 | sfx | Shared destruction / explosion feedback | $60 | end 65 | $BB | $061DD |
| $F8 | control | reset / silence | $57 | control only | — | $04B0B, $327E8 |

## Reconciliation and limits

AUDIO-0 is preserved unchanged as historical evidence. Its82 “Title / character-selection” label is narrowed to character selection;99 is the finite original title cue, verified at ROM0756. BE title lead-in at0746 is added alongside its existing projectile contexts.90 remains opening **and EEZ3**, not an opening-only composition.
00 is empty pending request, never silence. F8 is reset/silence only when admitted; its priority57 can be rejected. The accepted M4 unconditional F8 reset is a documented adapter difference pending review.
All37 effects terminate. Eleven music entries repeat; fifteen nonempty music entries are finite. Five more indexed music entries9B–9F immediately end; all four streams begin with F2. They leave a period-zero tone2 attenuation residue in the register model, so silence at a physical output is not asserted. Do not render them as five playable tracks.
No two IDs share the same header pointer. Three effect pairs have equal complete solo command hashes (A8/C2, BB/C4, BC/C0), despite distinct headers/priorities. This supports shared PCM targets, not merging requests or acoustic names.60 nonempty distinct command-output targets is the production estimate.
The JSON reports every driver header, initialized flags, category, priority, finite/loop facts, per-slot release ticks, output identity, source contexts and confidence. Natural original-game use is not individually established for the whole catalogue. M4 Chief Windows observation is stored separately for its six accepted IDs.
Companions: [driver integration](m5-driver-integration-contract.md), [Sound Test](m5-sound-test-contract.md), [production plan](m5-production-plan.md), [Manager handover](m5-manager-handover.md).

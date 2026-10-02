; object_2f_scripts: ROM $78B1A..$78B5A (end exclusive $78B5B).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Object type $2F state table/scripts. State 1 offers attachment, state 3 follows player state $12, and state 5 falls away.
SC_78B1A:
    .db $26, $8B, $2C, $8B, $36, $8B, $40, $8B, $49, $8B, $4F, $8B, $E0, $00, $5B, $8B
SC_78B2A:
    .db $FF, $00, $08, $01, $64, $8B, $08, $02, $64, $8B, $FF, $00, $FF, $04, $0F, $00
SC_78B3A:
    .db $00, $00, $00, $00, $FF, $00, $0C, $03, $C3, $8B, $FF, $03, $04, $FF, $00, $04
SC_78B4A:
    .db $04, $C3, $8B, $FF, $00, $01, $04, $CE, $8B, $08, $04, $D7, $8B, $FF, $07, $53
SC_78B5A:
    .db $8B

; object_0f_scripts: ROM $31FC9..$32056 (end exclusive $32057).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Replacement type $0F state table and scripts; type-$10 conversion reaches state 1 and frames $07/$08/$09.
SC_31FC9:
    .db $D3, $9F, $D9, $9F, $D9, $9F, $0B, $A0, $38, $A0, $01, $00, $60, $A0, $FF, $00
SC_31FD9:
    .db $01, $00, $EF, $03, $04, $07, $2F, $03, $04, $08, $2F, $03, $04, $09, $2F, $03
SC_31FE9:
    .db $04, $07, $2F, $03, $04, $08, $2F, $03, $08, $09, $2F, $03, $04, $08, $2F, $03
SC_31FF9:
    .db $04, $07, $2F, $03, $FF, $01, $E7, $A0, $01, $07, $2F, $03, $80, $00, $C6, $A0
SC_32009:
    .db $FF, $00, $FF, $06, $AB, $04, $07, $2F, $03, $04, $08, $2F, $03, $04, $09, $2F
SC_32019:
    .db $03, $04, $07, $2F, $03, $04, $08, $2F, $03, $08, $09, $2F, $03, $04, $08, $2F
SC_32029:
    .db $03, $04, $07, $2F, $03, $01, $07, $2F, $03, $80, $00, $C6, $A0, $FF, $00, $FF
SC_32039:
    .db $02, $00, $01, $00, $00, $FF, $0E, $10, $04, $09, $57, $A0, $04, $08, $57, $A0
SC_32049:
    .db $04, $07, $57, $A0, $FF, $0F, $41, $A0, $E0, $09, $5B, $A0, $FF, $00

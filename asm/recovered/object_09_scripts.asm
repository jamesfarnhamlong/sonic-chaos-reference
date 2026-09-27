; object_09_scripts: ROM $31BC8..$31C0F (end exclusive $31C10).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Object type $09 four-entry state table and scripts: visible rotation, sparkle removal, and the empty parameter-$01 state.
SC_31BC8:
    .db $D0, $9B, $D6, $9B, $E8, $9B, $0A, $9C, $E0, $00, $10, $9C, $FF, $00, $08, $01
SC_31BD8:
    .db $22, $9C, $08, $02, $22, $9C, $08, $04, $22, $9C, $08, $03, $22, $9C, $FF, $00
SC_31BE8:
    .db $04, $05, $2F, $03, $04, $06, $2F, $03, $04, $05, $2F, $03, $04, $06, $2F, $03
SC_31BF8:
    .db $04, $05, $2F, $03, $04, $06, $2F, $03, $04, $05, $2F, $03, $04, $06, $4A, $03
SC_31C08:
    .db $FF, $00, $E0, $00, $3D, $9C, $FF, $00

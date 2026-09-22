; spike_object_scripts: ROM $32C4A..$32C7C (end exclusive $32C7D).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Object type $1B has five state-script pointers; THZ1 places four parameter-zero instances.
SC_32C4A:
    .db $54, $AC, $5A, $AC, $65, $AC, $6E, $AC, $74, $AC, $E0, $0E, $7D, $AC, $FF, $00
SC_32C5A:
    .db $FF, $06, $A7, $E0, $0E, $8B, $AC, $FF, $07, $5D, $AC, $30, $0E, $C3, $AC, $FF
SC_32C6A:
    .db $03, $03, $FF, $00, $E0, $0E, $CC, $AC, $FF, $00, $30, $0E, $FC, $AC, $FF, $03
SC_32C7A:
    .db $01, $FF, $00

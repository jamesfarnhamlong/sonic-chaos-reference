; player_state_11_script: ROM $30334..$30345 (end exclusive $30346).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Player state $11 script: frames $38,$39,$3A,$39 with callback vector $03C2 -> fixed $3A7C.
SC_30334:
    .db $08, $38, $C2, $03, $04, $39, $C2, $03, $08, $3A, $C2, $03, $04, $39, $C2, $03
SC_30344:
    .db $FF, $00

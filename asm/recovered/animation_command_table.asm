; animation_command_table: ROM $06696..$066B5 (end exclusive $066B6).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Sixteen animation command-handler pointers, indexed by command byte.
SC_06696:
    .db $B9, $66, $C5, $66, $DB, $66, $0B, $67, $1F, $67, $A1, $67, $D5, $67, $EC, $67
SC_066A6:
    .db $FF, $67, $27, $68, $41, $68, $57, $68, $73, $68, $8F, $68, $BB, $68, $CF, $68

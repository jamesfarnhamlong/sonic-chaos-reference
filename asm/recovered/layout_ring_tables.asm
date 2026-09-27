; layout_ring_tables: ROM $075DC..$0760B (end exclusive $0760C).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Terrain-ring quadrant-presence and replacement-block tables for blocks $40-$43.
SC_075DC:
    .db $FF, $FF, $00, $00, $00, $00, $FF, $FF, $FF, $00, $00, $00, $00, $FF, $00, $00
SC_075EC:
    .db $00, $00, $FF, $00, $00, $00, $00, $FF, $43, $42, $46, $46, $46, $46, $45, $44
SC_075FC:
    .db $46, $46, $46, $46, $46, $46, $46, $46, $46, $46, $46, $46, $46, $46, $46, $46

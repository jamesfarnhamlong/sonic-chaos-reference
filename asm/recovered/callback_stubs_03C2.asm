; callback_stubs_03C2: ROM $003C2..$003D6 (end exclusive $003D7).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_003C2:
    JP $3A7C
SC_003C5:
    JP $38C5
SC_003C8:
    JP $38D1
SC_003CB:
    JP $3C1B
SC_003CE:
    JP $3CFC
SC_003D1:
    JP $3DAE
SC_003D4:
    JP $384D

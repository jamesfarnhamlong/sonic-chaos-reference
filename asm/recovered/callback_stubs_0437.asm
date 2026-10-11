; callback_stubs_0437: ROM $00437..$00439 (end exclusive $0043A).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_00437:
    JP $62F7

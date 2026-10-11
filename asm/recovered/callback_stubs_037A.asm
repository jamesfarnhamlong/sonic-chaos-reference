; callback_stubs_037A: ROM $0037A..$0037C (end exclusive $0037D).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_0037A:
    JP $614E

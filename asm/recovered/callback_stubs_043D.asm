; callback_stubs_043D: ROM $0043D..$00445 (end exclusive $00446).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_0043D:
    JP $396D
SC_00440:
    JP $39B6
SC_00443:
    JP $3BFB

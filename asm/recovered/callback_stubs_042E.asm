; callback_stubs_042E: ROM $0042E..$00433 (end exclusive $00434).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_0042E:
    JP $62D5
SC_00431:
    JP $631A

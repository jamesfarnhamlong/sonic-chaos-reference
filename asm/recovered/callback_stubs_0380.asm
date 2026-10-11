; callback_stubs_0380: ROM $00380..$00388 (end exclusive $00389).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_00380:
    JP $617E
SC_00383:
    JP $61A5
SC_00386:
    JP $61B1

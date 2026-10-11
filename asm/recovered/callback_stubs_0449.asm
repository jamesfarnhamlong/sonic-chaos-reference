; callback_stubs_0449: ROM $00449..$0044E (end exclusive $0044F).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_00449:
    JP $4C02
SC_0044C:
    JP $4C12

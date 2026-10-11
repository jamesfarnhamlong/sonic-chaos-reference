; callback_stubs_0338: ROM $00338..$00340 (end exclusive $00341).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_00338:
    JP $60FB
SC_0033B:
    JP $6328
SC_0033E:
    JP $5F54

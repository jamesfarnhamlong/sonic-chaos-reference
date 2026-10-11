; callback_stubs_036E: ROM $0036E..$00373 (end exclusive $00374).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_0036E:
    JP $6089
SC_00371:
    JP $5EB7

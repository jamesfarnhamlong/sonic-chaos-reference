; callback_stubs_032F: ROM $0032F..$00334 (end exclusive $00335).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_0032F:
    JP $6065
SC_00332:
    JP $606B

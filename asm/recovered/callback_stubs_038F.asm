; callback_stubs_038F: ROM $0038F..$00397 (end exclusive $00398).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_0038F:
    JP $3657
SC_00392:
    JP $3BC6
SC_00395:
    JP $36C6

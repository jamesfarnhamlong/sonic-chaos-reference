; callback_stubs_0320: ROM $00320..$00325 (end exclusive $00326).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_00320:
    JP $77CB
SC_00323:
    JP $5F3D

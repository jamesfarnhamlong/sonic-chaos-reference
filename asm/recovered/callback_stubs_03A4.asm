; callback_stubs_03A4: ROM $003A4..$003BE (end exclusive $003BF).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_003A4:
    JP $3A23
SC_003A7:
    JP $3BF0
SC_003AA:
    JP $3A71
SC_003AD:
    JP $3A37
SC_003B0:
    JP $3B4E
SC_003B3:
    JP $3901
SC_003B6:
    JP $3955
SC_003B9:
    JP $3759
SC_003BC:
    JP $3713

; callback_stubs_03DA: ROM $003DA..$003EE (end exclusive $003EF).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Run of three-byte JP stubs, each a supported entry: a player state script stores its address as a callback vector or has the engine execute it, or recovered/vector-reachable code calls it.
SC_003DA:
    JP $3A59
SC_003DD:
    JP $39E6
SC_003E0:
    JP $36F0
SC_003E3:
    JP $386F
SC_003E6:
    JP $389A
SC_003E9:
    JP $3783
SC_003EC:
    JP $3EFD

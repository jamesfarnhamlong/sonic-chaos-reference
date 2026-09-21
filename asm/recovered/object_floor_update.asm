; object_floor_update: ROM $077CB..$077EC (end exclusive $077ED).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Generic object floor update; useful for enemy grounding, not the player routine.
SC_077CB:
    RES 1,(IX+$22)
SC_077CF:
    LD BC,0
SC_077D2:
    LD DE,0
SC_077D5:
    CALL $7666
SC_077D8:
    CALL $70E7
SC_077DB:
    LD A,($D364)
SC_077DE:
    AND $1F
SC_077E0:
    ADD A,A
SC_077E1:
    LD L,A
SC_077E2:
    LD H,0
SC_077E4:
    LD DE,$77ED
SC_077E7:
    ADD HL,DE
SC_077E8:
    LD E,(HL)
SC_077E9:
    INC HL
SC_077EA:
    LD D,(HL)
SC_077EB:
    EX DE,HL
SC_077EC:
    JP (HL)

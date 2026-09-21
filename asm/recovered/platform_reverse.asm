; platform_reverse: ROM $780F1..$78104 (end exclusive $78105).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

SC_780F1:
    LD H,(IX+$19)
SC_780F4:
    LD L,(IX+$18)
SC_780F7:
    DEC HL
SC_780F8:
    LD A,H
SC_780F9:
    CPL
SC_780FA:
    LD H,A
SC_780FB:
    LD A,L
SC_780FC:
    CPL
SC_780FD:
    LD L,A
SC_780FE:
    LD (IX+$19),H
SC_78101:
    LD (IX+$18),L
SC_78104:
    RET

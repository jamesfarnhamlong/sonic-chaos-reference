; spring_setters: ROM $0480C..$04891 (end exclusive $04892).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

SC_0480C:
    BIT 7,(IX+$19)
SC_04810:
    RET nz
SC_04811:
    LD (IX+2),11
SC_04815:
    LD (IX+$18),L
SC_04818:
    LD (IX+$19),H
SC_0481B:
    SET 0,(IX+3)
SC_0481F:
    RES 1,(IX+3)
SC_04823:
    RES 1,(IX+$22)
SC_04827:
    LD A,$A6
SC_04829:
    LD ($DE04),A
SC_0482C:
    RET
SC_0482D:
    BIT 7,(IX+$19)
SC_04831:
    RET nz
SC_04832:
    LD (IX+2),$1C
SC_04836:
    LD (IX+$18),L
SC_04839:
    LD (IX+$19),H
SC_0483C:
    SET 0,(IX+3)
SC_04840:
    SET 1,(IX+3)
SC_04844:
    RES 1,(IX+$22)
SC_04848:
    RET
SC_04849:
    LD (IX+2),9
SC_0484D:
    LD (IX+$16),L
SC_04850:
    LD (IX+$17),H
SC_04853:
    LD ($D373),HL
SC_04856:
    RES 0,(IX+3)
SC_0485A:
    SET 1,(IX+3)
SC_0485E:
    RES 1,(IX+$22)
SC_04862:
    LD A,$A6
SC_04864:
    LD ($DE04),A
SC_04867:
    RET
SC_04868:
    LD (IX+2),9
SC_0486C:
    LD (IX+$16),L
SC_0486F:
    LD (IX+$17),H
SC_04872:
    BIT 7,H
SC_04874:
    JR z,SC_0487D
SC_04876:
    DEC HL
SC_04877:
    LD A,H
SC_04878:
    CPL
SC_04879:
    LD H,A
SC_0487A:
    LD A,L
SC_0487B:
    CPL
SC_0487C:
    LD L,A
SC_0487D:
    LD ($D373),HL
SC_04880:
    RES 0,(IX+3)
SC_04884:
    SET 1,(IX+3)
SC_04888:
    RES 1,(IX+$22)
SC_0488C:
    LD A,$A6
SC_0488E:
    LD ($DE04),A
SC_04891:
    RET

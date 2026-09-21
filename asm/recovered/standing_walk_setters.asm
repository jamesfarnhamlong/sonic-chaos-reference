; standing_walk_setters: ROM $045B3..$045EC (end exclusive $045ED).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Request standing state $01; clear airborne/rolling, zero X velocity, set max X=4.
SC_045B3:
    RES 0,(IX+3)
SC_045B7:
    RES 1,(IX+3)
SC_045BB:
    LD (IX+2),1
SC_045BF:
    LD HL,0
SC_045C2:
    LD ($D516),HL
SC_045C5:
    LD HL,$400
SC_045C8:
    LD ($D373),HL
SC_045CB:
    JP $4A33
SC_045CE:
    RES 0,(IX+3)
SC_045D2:
    RES 1,(IX+3)
SC_045D6:
    RES 6,(IX+3)
SC_045DA:
    LD (IX+2),5
SC_045DE:
    LD HL,$400
SC_045E1:
    LD ($D373),HL
SC_045E4:
    CALL $48A7
SC_045E7:
    LD A,$60
SC_045E9:
    LD ($D289),A
SC_045EC:
    RET

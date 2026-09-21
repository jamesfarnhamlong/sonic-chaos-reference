; Recovered original Z80 code, file $0480C..$04891.
; Numeric object fields are offsets from IX. No behavior changes intended.
; Branch labels preserve original addresses; build_check.py verifies every ROM byte.


CR_SpringUp_SetState:
; Input HL is signed 8.8 Y velocity. Refuse launch while Y velocity is negative; request state $0B.
CR_0480C:
    BIT 7,(IX+$19)
CR_04810:
    RET nz
CR_04811:
    LD (IX+2),11
CR_04815:
    LD (IX+$18),L
CR_04818:
    LD (IX+$19),H
CR_0481B:
    SET 0,(IX+3)
CR_0481F:
    RES 1,(IX+3)
CR_04823:
    RES 1,(IX+$22)
CR_04827:
    LD A,$A6
CR_04829:
    LD ($DE04),A
CR_0482C:
    RET

CR_SpringDiagonal_SetState:
; Input HL is signed 8.8 Y velocity. X velocity is set by tile handler; request state $1C.
CR_0482D:
    BIT 7,(IX+$19)
CR_04831:
    RET nz
CR_04832:
    LD (IX+2),$1C
CR_04836:
    LD (IX+$18),L
CR_04839:
    LD (IX+$19),H
CR_0483C:
    SET 0,(IX+3)
CR_04840:
    SET 1,(IX+3)
CR_04844:
    RES 1,(IX+$22)
CR_04848:
    RET

CR_SpringRight_SetState:
; Input HL is positive X velocity. Request rolling state $09 and update max-speed field $D373.
CR_04849:
    LD (IX+2),9
CR_0484D:
    LD (IX+$16),L
CR_04850:
    LD (IX+$17),H
CR_04853:
    LD ($D373),HL
CR_04856:
    RES 0,(IX+3)
CR_0485A:
    SET 1,(IX+3)
CR_0485E:
    RES 1,(IX+$22)
CR_04862:
    LD A,$A6
CR_04864:
    LD ($DE04),A
CR_04867:
    RET

CR_SpringLeft_SetState:
; Input HL is negative X velocity. Max-speed field receives its absolute value.
CR_04868:
    LD (IX+2),9
CR_0486C:
    LD (IX+$16),L
CR_0486F:
    LD (IX+$17),H
CR_04872:
    BIT 7,H
CR_04874:
    JR z,CR_0487D
CR_04876:
    DEC HL
CR_04877:
    LD A,H
CR_04878:
    CPL
CR_04879:
    LD H,A
CR_0487A:
    LD A,L
CR_0487B:
    CPL
CR_0487C:
    LD L,A
CR_0487D:
    LD ($D373),HL
CR_04880:
    RES 0,(IX+3)
CR_04884:
    SET 1,(IX+3)
CR_04888:
    RES 1,(IX+$22)
CR_0488C:
    LD A,$A6
CR_0488E:
    LD ($DE04),A
CR_04891:
    RET

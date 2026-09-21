; Recovered original Z80 code, file $780F1..$78104.
; Numeric object fields are offsets from IX. No behavior changes intended.
; Branch labels preserve original addresses; build_check.py verifies every ROM byte.


CR_Platform_ReverseVerticalSpeed:
CR_780F1:
    LD H,(IX+$19)
CR_780F4:
    LD L,(IX+$18)
CR_780F7:
    DEC HL
CR_780F8:
    LD A,H
CR_780F9:
    CPL
CR_780FA:
    LD H,A
CR_780FB:
    LD A,L
CR_780FC:
    CPL
CR_780FD:
    LD L,A
CR_780FE:
    LD (IX+$19),H
CR_78101:
    LD (IX+$18),L
CR_78104:
    RET

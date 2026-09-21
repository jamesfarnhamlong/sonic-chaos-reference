; Recovered original Z80 code, file $314C1..$314F4.
; Numeric object fields are offsets from IX. No behavior changes intended.
; Branch labels preserve original addresses; build_check.py verifies every ROM byte.


CR_Twist_Update:
; State $22 calls collision update then dispatches using +$38 & 3 and tile ID minus $58.
CR_314C1:
    CALL $0416
CR_314C4:
    CALL $0410
CR_314C7:
    LD A,($D364)
; Continue only while (collision flags & $3F) equals $17; otherwise request rolling state via $95E4.
CR_314CA:
    AND $3F
CR_314CC:
    CP $17
CR_314CE:
    JP nz,$95E4
CR_314D1:
    LD A,(IX+$38)
CR_314D4:
    AND 3
CR_314D6:
    ADD A,A
CR_314D7:
    LD E,A
CR_314D8:
    LD D,0
CR_314DA:
    LD HL,$94F5
CR_314DD:
    ADD HL,DE
CR_314DE:
    LD A,(HL)
CR_314DF:
    INC HL
CR_314E0:
    LD H,(HL)
CR_314E1:
    LD L,A
CR_314E2:
    LD A,($D353)
CR_314E5:
    SUB $58
CR_314E7:
    ADD A,A
CR_314E8:
    LD E,A
CR_314E9:
    LD D,0
CR_314EB:
    ADD HL,DE
CR_314EC:
    LD A,(HL)
CR_314ED:
    INC HL
CR_314EE:
    LD H,(HL)
CR_314EF:
    LD L,A
CR_314F0:
    LD DE,$95DD
CR_314F3:
    PUSH DE
CR_314F4:
    JP (HL)

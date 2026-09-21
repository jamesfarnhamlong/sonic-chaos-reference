; Recovered original Z80 code, file $07294..$072B5.
; Numeric object fields are offsets from IX. No behavior changes intended.
; Branch labels preserve original addresses; build_check.py verifies every ROM byte.

CR_07294:
    LD HL,($D511)
CR_07297:
    ADD HL,BC
CR_07298:
    LD ($D511),HL
CR_0729B:
    SET 3,(IX+$22)
CR_0729F:
    CALL $64CB
CR_072A2:
    LD A,($D364)
CR_072A5:
    AND $1F
CR_072A7:
    CP 10
CR_072A9:
    RET nz
CR_072AA:
    LD A,($D501)
CR_072AD:
    CP $11
CR_072AF:
    RET z
CR_072B0:
    LD HL,$600
CR_072B3:
    JP $4849

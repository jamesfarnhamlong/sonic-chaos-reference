; Recovered original Z80 code, file $06CBA..$06CE4.
; Numeric object fields are offsets from IX. No behavior changes intended.
; Branch labels preserve original addresses; build_check.py verifies every ROM byte.


CR_LoopLeft_CheckEntry:
CR_06CBA:
    LD A,(IX+$25)
CR_06CBD:
    OR A
CR_06CBE:
    RET z
CR_06CBF:
    BIT 1,(IX+$22)
CR_06CC3:
    RET z
CR_06CC4:
    LD A,($D497)
CR_06CC7:
    CP $52
CR_06CC9:
    JP z,$3EE1
CR_06CCC:
    RET

CR_LoopRight_CheckEntry:
CR_06CCD:
    LD A,(IX+$25)
CR_06CD0:
    OR A
CR_06CD1:
    RET nz
CR_06CD2:
    BIT 1,(IX+$22)
CR_06CD6:
    RET z
CR_06CD7:
    LD A,($D497)
CR_06CDA:
    CP $51
CR_06CDC:
    JP z,$3EAB
CR_06CDF:
    CP $57
CR_06CE1:
    JP z,$3EF7
CR_06CE4:
    RET

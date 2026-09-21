; Recovered original Z80 code, file $06A75..$06ACD.
; Numeric object fields are offsets from IX. No behavior changes intended.
; Branch labels preserve original addresses; build_check.py verifies every ROM byte.


CR_SpringUp_TileContact:
CR_06A75:
    LD A,($D501)
CR_06A78:
    CP $11
CR_06A7A:
    RET z
CR_06A7B:
    BIT 1,(IX+$22)
CR_06A7F:
    RET z
CR_06A80:
    LD A,(IX+$19)
CR_06A83:
    AND A
CR_06A84:
    RET m
CR_06A85:
    LD A,$FF
CR_06A87:
    LD ($D448),A
; Upright launch: $F880 = -7.5 original pixels/update (not GameMaker units).
CR_06A8A:
    LD HL,$F880
CR_06A8D:
    JP $480C

CR_SpringDiagonal_TileContact:
CR_06A90:
    LD A,($D501)
CR_06A93:
    CP $11
CR_06A95:
    RET z
CR_06A96:
    BIT 1,(IX+$22)
CR_06A9A:
    RET z
; Default diagonal X = +4.0; tile ID >= $38 selects -4.0.
CR_06A9B:
    LD HL,$400
CR_06A9E:
    RES 4,(IX+4)
CR_06AA2:
    LD A,($D36B)
CR_06AA5:
    CP $38
CR_06AA7:
    JR c,CR_06AB0
CR_06AA9:
    LD HL,$FC00
CR_06AAC:
    SET 4,(IX+4)
CR_06AB0:
    LD (IX+$16),L
CR_06AB3:
    LD (IX+$17),H
; Default diagonal Y = -5.5; level 0 (THZ) uses -7.0.
CR_06AB6:
    LD HL,$FA80
CR_06AB9:
    LD A,($D297)
CR_06ABC:
    OR A
CR_06ABD:
    JR nz,CR_06AC2
CR_06ABF:
    LD HL,$F900
CR_06AC2:
    LD A,$A6
CR_06AC4:
    LD ($DE04),A
CR_06AC7:
    XOR A
CR_06AC8:
    LD ($D448),A
CR_06ACB:
    JP $482D

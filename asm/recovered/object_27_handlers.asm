; object_27_handlers: ROM $7898E..$78A44 (end exclusive $78A45).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Initialize object $27: parameter zero requests state 1 and sets X velocity to -2.5.
SC_7898E:
    LD (IX+2),1
SC_78992:
    LD A,(IX+$3F)
SC_78995:
    OR A
SC_78996:
    JP nz,$89CB
SC_78999:
    LD HL,$FD00
SC_7899C:
    LD (IX+$17),$FD
SC_789A0:
    LD (IX+$16),$80
SC_789A4:
    XOR A
SC_789A5:
    LD (IX+$19),A
SC_789A8:
    LD (IX+$18),A
SC_789AB:
    RET
SC_789AC:
    BIT 6,(IX+4)
SC_789B0:
    RET nz
SC_789B1:
    CALL $033B
SC_789B4:
    LD A,(IX+$21)
SC_789B7:
    AND 15
SC_789B9:
    JP nz,$0323
SC_789BC:
    CALL $0338
SC_789BF:
    LD BC,$40
SC_789C2:
    CALL $0383
SC_789C5:
    OR A
SC_789C6:
    RET z
SC_789C7:
    SET 1,(IX+4)
SC_789CB:
    LD (IX+2),2
SC_789CF:
    XOR A
SC_789D0:
    LD (IX+$17),A
SC_789D3:
    LD (IX+$16),A
SC_789D6:
    LD (IX+$1F),1
SC_789DA:
    LD (IX+$1E),$80
SC_789DE:
    RET
SC_789DF:
    LD H,(IX+$19)
SC_789E2:
    LD L,(IX+$18)
SC_789E5:
    LD D,0
SC_789E7:
    LD E,3
SC_789E9:
    ADD HL,DE
SC_789EA:
    LD (IX+$19),H
SC_789ED:
    LD (IX+$18),L
SC_789F0:
    JP $8A06
SC_789F3:
    LD H,(IX+$19)
SC_789F6:
    LD L,(IX+$18)
SC_789F9:
    LD D,0
SC_789FB:
    LD E,3
SC_789FD:
    XOR A
SC_789FE:
    SBC HL,DE
SC_78A00:
    LD (IX+$19),H
SC_78A03:
    LD (IX+$18),L
SC_78A06:
    CALL $033B
SC_78A09:
    LD A,(IX+$21)
SC_78A0C:
    AND 15
SC_78A0E:
    JP nz,$0323
SC_78A11:
    CALL $0338
SC_78A14:
    LD A,(IX+$3F)
SC_78A17:
    OR A
SC_78A18:
    RET nz
SC_78A19:
    LD A,(IX+$1E)
SC_78A1C:
    SUB 1
SC_78A1E:
    LD (IX+$1E),A
SC_78A21:
    RET nc
SC_78A22:
    LD (IX+2),3
SC_78A26:
    JP $8999
SC_78A29:
    LD BC,$180
SC_78A2C:
    CALL $0383
SC_78A2F:
    OR A
SC_78A30:
    JR nz,SC_78A37
SC_78A32:
    LD (IX+0),$FE
SC_78A36:
    RET
SC_78A37:
    CALL $033B
SC_78A3A:
    LD A,(IX+$21)
SC_78A3D:
    AND 15
SC_78A3F:
    JP nz,$0323
SC_78A42:
    JP $0338

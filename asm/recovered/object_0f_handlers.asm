; object_0f_handlers: ROM $32057..$32100 (end exclusive $32101).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

SC_32057:
    CALL $0338
SC_3205A:
    RET
SC_3205B:
    LD (IX+0),$FF
SC_3205F:
    RET
; Type $0F initialization; parameter zero requests state 1, detaches art bases, and preserves a nonzero inherited position.
SC_32060:
    LD A,(IX+$3F)
SC_32063:
    INC A
SC_32064:
    JP z,$A0C1
SC_32067:
    LD (IX+2),1
SC_3206B:
    BIT 6,(IX+$3F)
SC_3206F:
    JP z,$A089
SC_32072:
    LD (IX+2),3
SC_32076:
    LD B,$11
SC_32078:
    LD C,0
SC_3207A:
    LD D,(IX+$12)
SC_3207D:
    LD E,(IX+$11)
SC_32080:
    LD H,(IX+$15)
SC_32083:
    LD L,(IX+$14)
SC_32086:
    CALL $0371
SC_32089:
    RES 4,(IX+4)
SC_3208D:
    LD (IX+8),0
SC_32091:
    LD (IX+9),0
SC_32095:
    SET 0,(IX+4)
SC_32099:
    LD A,(IX+$11)
SC_3209C:
    OR (IX+$12)
SC_3209F:
    RET nz
SC_320A0:
    LD HL,($D511)
SC_320A3:
    LD A,L
SC_320A4:
    AND $E0
SC_320A6:
    ADD A,$10
SC_320A8:
    LD L,A
SC_320A9:
    LD (IX+$11),L
SC_320AC:
    LD (IX+$12),H
SC_320AF:
    LD HL,($D514)
SC_320B2:
    LD DE,$20
SC_320B5:
    ADD HL,DE
SC_320B6:
    LD A,L
SC_320B7:
    AND $E0
SC_320B9:
    LD L,A
SC_320BA:
    LD (IX+$14),L
SC_320BD:
    LD (IX+$15),H
SC_320C0:
    RET
SC_320C1:
    LD (IX+2),4
SC_320C5:
    RET
; Type $0F terminal callback selects $FF/$FE removal from parameter high bits.
SC_320C6:
    BIT 6,(IX+$3F)
SC_320CA:
    JP nz,$A0D9
SC_320CD:
    BIT 7,(IX+$3F)
SC_320D1:
    JP nz,$A0E2
SC_320D4:
    LD (IX+0),$FF
SC_320D8:
    RET
SC_320D9:
    XOR A
SC_320DA:
    LD (IX+$3E),A
SC_320DD:
    LD (IX+0),$FF
SC_320E1:
    RET
SC_320E2:
    LD (IX+0),$FE
SC_320E6:
    RET
SC_320E7:
    LD A,(IX+$3F)
SC_320EA:
    LD B,A
SC_320EB:
    AND $3F
SC_320ED:
    RET z
SC_320EE:
    DEC A
SC_320EF:
    LD C,A
SC_320F0:
    LD A,B
SC_320F1:
    AND $C0
SC_320F3:
    OR C
SC_320F4:
    LD (IX+$3F),A
SC_320F7:
    LD A,(IX+1)
SC_320FA:
    AND 1
SC_320FC:
    INC A
SC_320FD:
    LD (IX+2),A
SC_32100:
    RET

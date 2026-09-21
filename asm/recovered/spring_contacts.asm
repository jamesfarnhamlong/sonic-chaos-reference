; spring_contacts: ROM $06A75..$06ACD (end exclusive $06ACE).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

SC_06A75:
    LD A,($D501)
SC_06A78:
    CP $11
SC_06A7A:
    RET z
SC_06A7B:
    BIT 1,(IX+$22)
SC_06A7F:
    RET z
SC_06A80:
    LD A,(IX+$19)
SC_06A83:
    AND A
SC_06A84:
    RET m
SC_06A85:
    LD A,$FF
SC_06A87:
    LD ($D448),A
SC_06A8A:
    LD HL,$F880
SC_06A8D:
    JP $480C
SC_06A90:
    LD A,($D501)
SC_06A93:
    CP $11
SC_06A95:
    RET z
SC_06A96:
    BIT 1,(IX+$22)
SC_06A9A:
    RET z
SC_06A9B:
    LD HL,$400
SC_06A9E:
    RES 4,(IX+4)
SC_06AA2:
    LD A,($D36B)
SC_06AA5:
    CP $38
SC_06AA7:
    JR c,SC_06AB0
SC_06AA9:
    LD HL,$FC00
SC_06AAC:
    SET 4,(IX+4)
SC_06AB0:
    LD (IX+$16),L
SC_06AB3:
    LD (IX+$17),H
SC_06AB6:
    LD HL,$FA80
SC_06AB9:
    LD A,($D297)
SC_06ABC:
    OR A
SC_06ABD:
    JR nz,SC_06AC2
SC_06ABF:
    LD HL,$F900
SC_06AC2:
    LD A,$A6
SC_06AC4:
    LD ($DE04),A
SC_06AC7:
    XOR A
SC_06AC8:
    LD ($D448),A
SC_06ACB:
    JP $482D

; spike_object_handlers: ROM $32C7D..$32D58 (end exclusive $32D59).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Initialize retracting spikes: request state 1 and clear the hit cooldown.
SC_32C7D:
    SET 7,(IX+3)
SC_32C81:
    LD A,1
SC_32C83:
    LD (IX+2),A
SC_32C86:
    LD (IX+$1F),0
SC_32C8A:
    RET
; Rising state: damage/contact helper, then move Y up six pixels to an 18-pixel limit.
SC_32C8B:
    BIT 6,(IX+4)
SC_32C8F:
    RET nz
SC_32C90:
    CALL $ACFD
SC_32C93:
    LD H,(IX+$15)
SC_32C96:
    LD L,(IX+$14)
SC_32C99:
    LD DE,6
SC_32C9C:
    XOR A
SC_32C9D:
    SBC HL,DE
SC_32C9F:
    LD (IX+$15),H
SC_32CA2:
    LD (IX+$14),L
SC_32CA5:
    EX DE,HL
SC_32CA6:
    LD H,(IX+$3D)
SC_32CA9:
    LD L,(IX+$3C)
SC_32CAC:
    XOR A
SC_32CAD:
    SBC HL,DE
SC_32CAF:
    LD DE,$12
SC_32CB2:
    XOR A
SC_32CB3:
    SBC HL,DE
SC_32CB5:
    JR z,SC_32CB8
SC_32CB7:
    RET
SC_32CB8:
    LD A,2
SC_32CBA:
    LD (IX+2),A
SC_32CBD:
    LD A,$10
SC_32CBF:
    LD (IX+$1E),A
SC_32CC2:
    RET
SC_32CC3:
    BIT 6,(IX+4)
SC_32CC7:
    RET nz
SC_32CC8:
    CALL $ACFD
SC_32CCB:
    RET
; Retracting state: move Y down six pixels to the saved base, then request hidden state 4.
SC_32CCC:
    BIT 6,(IX+4)
SC_32CD0:
    RET nz
SC_32CD1:
    LD H,(IX+$15)
SC_32CD4:
    LD L,(IX+$14)
SC_32CD7:
    LD DE,6
SC_32CDA:
    XOR A
SC_32CDB:
    ADD HL,DE
SC_32CDC:
    LD (IX+$15),H
SC_32CDF:
    LD (IX+$14),L
SC_32CE2:
    EX DE,HL
SC_32CE3:
    LD H,(IX+$3D)
SC_32CE6:
    LD L,(IX+$3C)
SC_32CE9:
    XOR A
SC_32CEA:
    SBC HL,DE
SC_32CEC:
    JR z,SC_32CF1
SC_32CEE:
    JR c,SC_32CF1
SC_32CF0:
    RET
SC_32CF1:
    LD A,4
SC_32CF3:
    LD (IX+2),A
SC_32CF6:
    LD A,$40
SC_32CF8:
    LD (IX+$1E),A
SC_32CFB:
    RET
SC_32CFC:
    RET
; Spike contact helper; hit cooldown is object+$1F.
SC_32CFD:
    LD A,(IX+$1F)
SC_32D00:
    OR A
SC_32D01:
    JR z,SC_32D08
SC_32D03:
    DEC A
SC_32D04:
    LD (IX+$1F),A
SC_32D07:
    RET
SC_32D08:
    LD A,($D519)
SC_32D0B:
    RLCA
SC_32D0C:
    RET c
SC_32D0D:
    CALL $033B
SC_32D10:
    LD A,(IX+$21)
SC_32D13:
    AND 15
SC_32D15:
    RET z
SC_32D16:
    BIT 0,A
SC_32D18:
    JR z,SC_32D2B
SC_32D1A:
    LD A,$FF
SC_32D1C:
    LD ($D3B0),A
SC_32D1F:
    LD HL,$FC00
SC_32D22:
    LD ($D518),HL
SC_32D25:
    LD A,$10
SC_32D27:
    LD (IX+$1F),A
SC_32D2A:
    RET
SC_32D2B:
    LD A,($D522)
SC_32D2E:
    BIT 1,A
SC_32D30:
    RET z
SC_32D31:
    LD A,($D503)
SC_32D34:
    BIT 1,A
SC_32D36:
    RET z
SC_32D37:
    LD A,1
SC_32D39:
    LD ($D502),A
SC_32D3C:
    LD HL,0
SC_32D3F:
    LD ($D516),HL
SC_32D42:
    LD H,(IX+$12)
SC_32D45:
    LD L,(IX+$11)
SC_32D48:
    LD DE,$17
SC_32D4B:
    BIT 2,(IX+$21)
SC_32D4F:
    JR nz,SC_32D54
SC_32D51:
    LD DE,$FFE9
SC_32D54:
    ADD HL,DE
SC_32D55:
    LD ($D511),HL
SC_32D58:
    RET

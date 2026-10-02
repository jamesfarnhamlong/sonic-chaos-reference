; player_state_12_handler: ROM $03B4E..$03BC0 (end exclusive $03BC1).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Player state $12 callback: shared movement/collision, owner positioning, manual-jump detach, side-hurt detach and automatic floor rebound.
SC_03B4E:
    CALL $3FEF
SC_03B51:
    CALL $48A7
SC_03B54:
    CALL $3BA8
SC_03B57:
    LD A,($D147)
SC_03B5A:
    AND $30
SC_03B5C:
    JR nz,SC_03B8E
SC_03B5E:
    LD A,(IX+$23)
SC_03B61:
    AND 12
SC_03B63:
    JP nz,$3B9D
SC_03B66:
    BIT 1,(IX+$23)
SC_03B6A:
    RET z
SC_03B6B:
    RES 1,(IX+$22)
SC_03B6F:
    SET 0,(IX+3)
SC_03B73:
    LD HL,$F880
SC_03B76:
    LD ($D518),HL
SC_03B79:
    LD HL,($D514)
SC_03B7C:
    DEC HL
SC_03B7D:
    LD ($D514),HL
SC_03B80:
    LD IY,($D3A4)
SC_03B84:
    LD (IY+2),3
SC_03B88:
    LD A,$C2
SC_03B8A:
    LD ($DE04),A
SC_03B8D:
    RET
SC_03B8E:
    LD IY,($D3A4)
SC_03B92:
    LD (IY+2),5
SC_03B96:
    RES 0,(IX+3)
SC_03B9A:
    JP $45ED
SC_03B9D:
    LD IY,($D3A4)
SC_03BA1:
    LD (IY+2),5
SC_03BA5:
    JP $494F
SC_03BA8:
    PUSH IX
SC_03BAA:
    LD IX,($D3A4)
SC_03BAE:
    LD HL,$10
SC_03BB1:
    LD A,(IX+6)
SC_03BB4:
    CP 3
SC_03BB6:
    JR z,SC_03BBB
SC_03BB8:
    LD HL,11
SC_03BBB:
    CALL $5F27
SC_03BBE:
    POP IX
SC_03BC0:
    RET

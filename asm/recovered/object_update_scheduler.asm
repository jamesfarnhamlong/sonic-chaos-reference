; object_update_scheduler: ROM $05DD1..$05E6F (end exclusive $05E70).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Update 19 object slots. Types below $26 use bank $0C for animation/callbacks.
SC_05DD1:
    XOR A
SC_05DD2:
    LD ($D521),A
SC_05DD5:
    LD IX,$D540
SC_05DD9:
    LD B,$13
SC_05DDB:
    PUSH BC
SC_05DDC:
    LD A,$FF
SC_05DDE:
    LD ($D44F),A
SC_05DE1:
    CALL $5DF1
SC_05DE4:
    XOR A
SC_05DE5:
    LD ($D44F),A
SC_05DE8:
    LD DE,$40
SC_05DEB:
    ADD IX,DE
SC_05DED:
    POP BC
SC_05DEE:
    DJNZ SC_05DDB
SC_05DF0:
    RET
SC_05DF1:
    LD A,(IX+0)
SC_05DF4:
    OR A
SC_05DF5:
    RET z
SC_05DF6:
    CP $F0
SC_05DF8:
    JR nc,SC_05E61
SC_05DFA:
    LD A,(IX+0)
SC_05DFD:
    CP $26
SC_05DFF:
    JR nc,SC_05E31
SC_05E01:
    LD A,$FF
SC_05E03:
    LD ($D44F),A
SC_05E06:
    LD A,12
SC_05E08:
    LD ($D12B),A
SC_05E0B:
    LD ($FFFF),A
SC_05E0E:
    CALL $64FA
SC_05E11:
    XOR A
SC_05E12:
    LD ($D44F),A
SC_05E15:
    LD A,$FF
SC_05E17:
    LD ($D44F),A
SC_05E1A:
    LD A,12
SC_05E1C:
    LD ($D12B),A
SC_05E1F:
    LD ($FFFF),A
SC_05E22:
    CALL $5E91
SC_05E25:
    XOR A
SC_05E26:
    LD ($D44F),A
SC_05E29:
    LD A,(IX+1)
SC_05E2C:
    OR A
SC_05E2D:
    RET z
SC_05E2E:
    JP $61E1
SC_05E31:
    LD A,$FF
SC_05E33:
    LD ($D44F),A
SC_05E36:
    LD A,$1E
SC_05E38:
    LD ($D12B),A
SC_05E3B:
    LD ($FFFF),A
SC_05E3E:
    CALL $64FA
SC_05E41:
    XOR A
SC_05E42:
    LD ($D44F),A
SC_05E45:
    LD A,$FF
SC_05E47:
    LD ($D44F),A
SC_05E4A:
    LD A,$1E
SC_05E4C:
    LD ($D12B),A
SC_05E4F:
    LD ($FFFF),A
SC_05E52:
    CALL $5E91
SC_05E55:
    XOR A
SC_05E56:
    LD ($D44F),A
SC_05E59:
    LD A,(IX+1)
SC_05E5C:
    OR A
SC_05E5D:
    RET z
SC_05E5E:
    JP $61E1
SC_05E61:
    AND 15
SC_05E63:
    ADD A,A
SC_05E64:
    LD L,A
SC_05E65:
    LD H,0
SC_05E67:
    LD DE,$5E70
SC_05E6A:
    ADD HL,DE
SC_05E6B:
    LD E,(HL)
SC_05E6C:
    INC HL
SC_05E6D:
    LD D,(HL)
SC_05E6E:
    EX DE,HL
SC_05E6F:
    JP (HL)

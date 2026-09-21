; Recovered original Z80 code, file $03C1B..$03EFC.
; Numeric object fields are offsets from IX. No behavior changes intended.
; Branch labels preserve original addresses; build_check.py verifies every ROM byte.


CR_LoopRight_Update:
; Bank 13 contains signed 16-bit X/Y path offsets. D39D..D39F is an 8-bit-fraction path cursor.
CR_03C1B:
    LD A,13
CR_03C1D:
    CALL $1C6F
CR_03C20:
    LD L,(IX+$16)
CR_03C23:
    LD H,(IX+$17)
CR_03C26:
    LD DE,($D39D)
CR_03C2A:
    LD A,($D39F)
CR_03C2D:
    ADD HL,DE
CR_03C2E:
    JR nc,CR_03C31
CR_03C30:
    INC A
CR_03C31:
    LD ($D39D),HL
CR_03C34:
    LD ($D39F),A
; Right loop: Y table CPU $8000 / file $34000; X table CPU $8398 / file $34398.
CR_03C37:
    LD HL,($D39E)
CR_03C3A:
    ADD HL,HL
CR_03C3B:
    LD DE,$8000
CR_03C3E:
    ADD HL,DE
CR_03C3F:
    LD E,(HL)
CR_03C40:
    INC HL
CR_03C41:
    LD D,(HL)
CR_03C42:
    LD L,(IX+$3C)
CR_03C45:
    LD H,(IX+$3D)
CR_03C48:
    ADD HL,DE
CR_03C49:
    LD (IX+$14),L
CR_03C4C:
    LD (IX+$15),H
CR_03C4F:
    LD HL,($D39E)
CR_03C52:
    ADD HL,HL
CR_03C53:
    LD DE,$8398
CR_03C56:
    ADD HL,DE
CR_03C57:
    LD E,(HL)
CR_03C58:
    INC HL
CR_03C59:
    LD D,(HL)
CR_03C5A:
    LD L,(IX+$3A)
CR_03C5D:
    LD H,(IX+$3B)
CR_03C60:
    ADD HL,DE
CR_03C61:
    LD (IX+$11),L
CR_03C64:
    LD (IX+$12),H
; Decelerate by $000A before path index $90; accelerate by $000C afterward.
CR_03C67:
    LD HL,($D39E)
CR_03C6A:
    XOR A
CR_03C6B:
    LD DE,$90
CR_03C6E:
    SBC HL,DE
CR_03C70:
    JR nc,CR_03C88
CR_03C72:
    LD L,(IX+$16)
CR_03C75:
    LD H,(IX+$17)
CR_03C78:
    LD DE,10
CR_03C7B:
    XOR A
CR_03C7C:
    SBC HL,DE
CR_03C7E:
    JR c,CR_03CC5
CR_03C80:
    LD (IX+$16),L
CR_03C83:
    LD (IX+$17),H
CR_03C86:
    JR CR_03C9C
CR_03C88:
    LD (IX+$25),1
CR_03C8C:
    LD L,(IX+$16)
CR_03C8F:
    LD H,(IX+$17)
CR_03C92:
    LD DE,12
CR_03C95:
    ADD HL,DE
CR_03C96:
    LD (IX+$16),L
CR_03C99:
    LD (IX+$17),H
CR_03C9C:
    CALL $48BC
; Leave right loop when index reaches $180; state 6 or 9 selected by player flags.
CR_03C9F:
    LD HL,($D39E)
CR_03CA2:
    LD DE,$180
CR_03CA5:
    XOR A
CR_03CA6:
    SBC HL,DE
CR_03CA8:
    RET c
CR_03CA9:
    LD A,6
CR_03CAB:
    BIT 1,(IX+3)
CR_03CAF:
    JR z,CR_03CB3
CR_03CB1:
    LD A,9
CR_03CB3:
    LD (IX+2),A
CR_03CB6:
    LD HL,($D373)
CR_03CB9:
    LD (IX+$16),L
CR_03CBC:
    LD (IX+$17),H
CR_03CBF:
    LD A,$10
CR_03CC1:
    LD ($D3A0),A
CR_03CC4:
    RET
CR_03CC5:
    LD L,(IX+$3A)
CR_03CC8:
    LD H,(IX+$3B)
CR_03CCB:
    LD E,(IX+$11)
CR_03CCE:
    LD D,(IX+$12)
CR_03CD1:
    XOR A
CR_03CD2:
    SBC HL,DE
CR_03CD4:
    JR c,CR_03CE9
CR_03CD6:
    LD L,(IX+$11)
CR_03CD9:
    LD H,(IX+$12)
CR_03CDC:
    LD DE,8
CR_03CDF:
    ADD HL,DE
CR_03CE0:
    LD (IX+$11),L
CR_03CE3:
    LD (IX+$12),H
CR_03CE6:
    JP $4680
CR_03CE9:
    LD L,(IX+$11)
CR_03CEC:
    LD H,(IX+$12)
CR_03CEF:
    LD DE,$FFFE
CR_03CF2:
    ADD HL,DE
CR_03CF3:
    LD (IX+$11),L
CR_03CF6:
    LD (IX+$12),H
CR_03CF9:
    JP $4680

CR_LoopAlternateExit_Update:
CR_03CFC:
    LD A,13
CR_03CFE:
    CALL $1C6F
CR_03D01:
    LD L,(IX+$16)
CR_03D04:
    LD H,(IX+$17)
CR_03D07:
    LD DE,($D39D)
CR_03D0B:
    LD A,($D39F)
CR_03D0E:
    ADD HL,DE
CR_03D0F:
    JR nc,CR_03D12
CR_03D11:
    INC A
CR_03D12:
    LD ($D39D),HL
CR_03D15:
    LD ($D39F),A
; Alternate exit path: Y table $8DDC; X table $9140. Level usage still to verify.
CR_03D18:
    LD HL,($D39E)
CR_03D1B:
    ADD HL,HL
CR_03D1C:
    LD DE,$8DDC
CR_03D1F:
    ADD HL,DE
CR_03D20:
    LD E,(HL)
CR_03D21:
    INC HL
CR_03D22:
    LD D,(HL)
CR_03D23:
    LD L,(IX+$3C)
CR_03D26:
    LD H,(IX+$3D)
CR_03D29:
    ADD HL,DE
CR_03D2A:
    LD (IX+$14),L
CR_03D2D:
    LD (IX+$15),H
CR_03D30:
    LD HL,($D39E)
CR_03D33:
    ADD HL,HL
CR_03D34:
    LD DE,$9140
CR_03D37:
    ADD HL,DE
CR_03D38:
    LD E,(HL)
CR_03D39:
    INC HL
CR_03D3A:
    LD D,(HL)
CR_03D3B:
    LD L,(IX+$3A)
CR_03D3E:
    LD H,(IX+$3B)
CR_03D41:
    ADD HL,DE
CR_03D42:
    LD (IX+$11),L
CR_03D45:
    LD (IX+$12),H
CR_03D48:
    LD HL,($D39E)
CR_03D4B:
    XOR A
CR_03D4C:
    LD DE,$90
CR_03D4F:
    SBC HL,DE
CR_03D51:
    JR nc,CR_03D6A
CR_03D53:
    LD L,(IX+$16)
CR_03D56:
    LD H,(IX+$17)
CR_03D59:
    LD DE,10
CR_03D5C:
    XOR A
CR_03D5D:
    SBC HL,DE
CR_03D5F:
    JP c,$3CC5
CR_03D62:
    LD (IX+$16),L
CR_03D65:
    LD (IX+$17),H
CR_03D68:
    JR CR_03D7E
CR_03D6A:
    LD (IX+$25),1
CR_03D6E:
    LD L,(IX+$16)
CR_03D71:
    LD H,(IX+$17)
CR_03D74:
    LD DE,12
CR_03D77:
    ADD HL,DE
CR_03D78:
    LD (IX+$16),L
CR_03D7B:
    LD (IX+$17),H
CR_03D7E:
    CALL $48BC
CR_03D81:
    LD HL,($D39E)
CR_03D84:
    LD DE,$1A0
CR_03D87:
    XOR A
CR_03D88:
    SBC HL,DE
CR_03D8A:
    RET c
CR_03D8B:
    LD A,10
CR_03D8D:
    LD (IX+2),A
CR_03D90:
    LD HL,($D373)
CR_03D93:
    LD (IX+$18),L
CR_03D96:
    LD (IX+$19),H
CR_03D99:
    LD (IX+$16),0
CR_03D9D:
    LD (IX+$17),0
CR_03DA1:
    SET 0,(IX+3)
CR_03DA5:
    SET 1,(IX+3)
CR_03DA9:
    RES 1,(IX+$22)
CR_03DAD:
    RET

CR_LoopLeft_Update:
CR_03DAE:
    LD A,13
CR_03DB0:
    CALL $1C6F
CR_03DB3:
    LD L,(IX+$16)
CR_03DB6:
    LD H,(IX+$17)
CR_03DB9:
    DEC HL
CR_03DBA:
    LD A,H
CR_03DBB:
    CPL
CR_03DBC:
    LD H,A
CR_03DBD:
    LD A,L
CR_03DBE:
    CPL
CR_03DBF:
    LD L,A
CR_03DC0:
    LD DE,($D39D)
CR_03DC4:
    LD A,($D39F)
CR_03DC7:
    ADD HL,DE
CR_03DC8:
    JR nc,CR_03DCB
CR_03DCA:
    INC A
CR_03DCB:
    LD ($D39D),HL
CR_03DCE:
    LD ($D39F),A
; Left loop: Y table $86AE; X table $8A46.
CR_03DD1:
    LD HL,($D39E)
CR_03DD4:
    ADD HL,HL
CR_03DD5:
    LD DE,$86AE
CR_03DD8:
    ADD HL,DE
CR_03DD9:
    LD E,(HL)
CR_03DDA:
    INC HL
CR_03DDB:
    LD D,(HL)
CR_03DDC:
    LD L,(IX+$3C)
CR_03DDF:
    LD H,(IX+$3D)
CR_03DE2:
    ADD HL,DE
CR_03DE3:
    LD (IX+$14),L
CR_03DE6:
    LD (IX+$15),H
CR_03DE9:
    LD HL,($D39E)
CR_03DEC:
    ADD HL,HL
CR_03DED:
    LD DE,$8A46
CR_03DF0:
    ADD HL,DE
CR_03DF1:
    LD E,(HL)
CR_03DF2:
    INC HL
CR_03DF3:
    LD D,(HL)
CR_03DF4:
    LD L,(IX+$3A)
CR_03DF7:
    LD H,(IX+$3B)
CR_03DFA:
    ADD HL,DE
CR_03DFB:
    LD (IX+$11),L
CR_03DFE:
    LD (IX+$12),H
CR_03E01:
    LD HL,($D39E)
CR_03E04:
    XOR A
CR_03E05:
    LD DE,$90
CR_03E08:
    SBC HL,DE
CR_03E0A:
    JR nc,CR_03E30
CR_03E0C:
    LD L,(IX+$16)
CR_03E0F:
    LD H,(IX+$17)
CR_03E12:
    DEC HL
CR_03E13:
    LD A,H
CR_03E14:
    CPL
CR_03E15:
    LD H,A
CR_03E16:
    LD A,L
CR_03E17:
    CPL
CR_03E18:
    LD L,A
CR_03E19:
    LD DE,10
CR_03E1C:
    XOR A
CR_03E1D:
    SBC HL,DE
CR_03E1F:
    JR c,CR_03E74
CR_03E21:
    DEC HL
CR_03E22:
    LD A,H
CR_03E23:
    CPL
CR_03E24:
    LD H,A
CR_03E25:
    LD A,L
CR_03E26:
    CPL
CR_03E27:
    LD L,A
CR_03E28:
    LD (IX+$16),L
CR_03E2B:
    LD (IX+$17),H
CR_03E2E:
    JR CR_03E44
CR_03E30:
    LD (IX+$25),0
CR_03E34:
    LD L,(IX+$16)
CR_03E37:
    LD H,(IX+$17)
CR_03E3A:
    LD DE,$FFF4
CR_03E3D:
    ADD HL,DE
CR_03E3E:
    LD (IX+$16),L
CR_03E41:
    LD (IX+$17),H
CR_03E44:
    CALL $48BC
CR_03E47:
    LD HL,($D39E)
CR_03E4A:
    LD DE,$180
CR_03E4D:
    XOR A
CR_03E4E:
    SBC HL,DE
CR_03E50:
    RET c
CR_03E51:
    LD A,6
CR_03E53:
    BIT 1,(IX+3)
CR_03E57:
    JR z,CR_03E5B
CR_03E59:
    LD A,9
CR_03E5B:
    LD (IX+2),A
CR_03E5E:
    LD HL,($D373)
CR_03E61:
    DEC HL
CR_03E62:
    LD A,H
CR_03E63:
    CPL
CR_03E64:
    LD H,A
CR_03E65:
    LD A,L
CR_03E66:
    CPL
CR_03E67:
    LD L,A
CR_03E68:
    LD (IX+$16),L
CR_03E6B:
    LD (IX+$17),H
CR_03E6E:
    LD A,$10
CR_03E70:
    LD ($D3A0),A
CR_03E73:
    RET
CR_03E74:
    LD L,(IX+$3A)
CR_03E77:
    LD H,(IX+$3B)
CR_03E7A:
    LD E,(IX+$11)
CR_03E7D:
    LD D,(IX+$12)
CR_03E80:
    XOR A
CR_03E81:
    SBC HL,DE
CR_03E83:
    JR c,CR_03E98
CR_03E85:
    LD L,(IX+$11)
CR_03E88:
    LD H,(IX+$12)
CR_03E8B:
    LD DE,8
CR_03E8E:
    ADD HL,DE
CR_03E8F:
    LD (IX+$11),L
CR_03E92:
    LD (IX+$12),H
CR_03E95:
    JP $4680
CR_03E98:
    LD L,(IX+$11)
CR_03E9B:
    LD H,(IX+$12)
CR_03E9E:
    LD DE,$FFFE
CR_03EA1:
    ADD HL,DE
CR_03EA2:
    LD (IX+$11),L
CR_03EA5:
    LD (IX+$12),H
CR_03EA8:
    JP $4680

CR_LoopRight_Enter:
; Entry snaps X to a 32-pixel boundary and Y to boundary +4, saves origin and clears cursor.
CR_03EAB:
    LD (IX+2),12
CR_03EAF:
    LD A,(IX+$11)
CR_03EB2:
    AND $E0
CR_03EB4:
    LD (IX+$11),A
CR_03EB7:
    LD L,A
CR_03EB8:
    LD H,(IX+$12)
CR_03EBB:
    LD (IX+$3A),L
CR_03EBE:
    LD (IX+$3B),H
CR_03EC1:
    LD A,(IX+$14)
CR_03EC4:
    AND $E0
CR_03EC6:
    ADD A,4
CR_03EC8:
    LD L,A
CR_03EC9:
    LD (IX+$14),A
CR_03ECC:
    LD H,(IX+$15)
CR_03ECF:
    LD (IX+$3C),L
CR_03ED2:
    LD (IX+$3D),H
CR_03ED5:
    XOR A
CR_03ED6:
    LD ($D39D),A
CR_03ED9:
    LD ($D39E),A
CR_03EDC:
    LD ($D39F),A
CR_03EDF:
    POP AF
CR_03EE0:
    RET

CR_LoopLeft_Enter:
CR_03EE1:
    LD (IX+2),13
CR_03EE5:
    LD L,(IX+$11)
CR_03EE8:
    LD H,(IX+$12)
CR_03EEB:
    LD BC,$20
CR_03EEE:
    ADD HL,BC
CR_03EEF:
    LD (IX+$11),L
CR_03EF2:
    LD (IX+$12),H
CR_03EF5:
    JR CR_03EAF

CR_LoopAlternateExit_Enter:
CR_03EF7:
    LD (IX+2),$13
CR_03EFB:
    JR CR_03EAF

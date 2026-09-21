; Recovered original Z80 code, file $06E56..$06F60.
; Numeric object fields are offsets from IX. No behavior changes intended.
; Branch labels preserve original addresses; build_check.py verifies every ROM byte.


CR_Twist_CheckEntry:
; Flag $17 tile handler. Right entry tiles $59/$5C; left entry tiles $73/$72/$6B.
CR_06E56:
    LD A,($D36B)
CR_06E59:
    LD ($D36D),A
CR_06E5C:
    CP $59
CR_06E5E:
    JR z,CR_06E74
CR_06E60:
    CP $5C
CR_06E62:
    JR z,CR_06E74
CR_06E64:
    CP $73
CR_06E66:
    JP z,$6EF7
CR_06E69:
    CP $72
CR_06E6B:
    JP z,$6EF7
CR_06E6E:
    CP $6B
CR_06E70:
    JP z,$6EF7
CR_06E73:
    RET
CR_06E74:
    LD A,$A5
CR_06E76:
    LD ($DE04),A
CR_06E79:
    BIT 7,(IX+$17)
CR_06E7D:
    JR nz,CR_06E73
CR_06E7F:
    LD A,($D297)
CR_06E82:
    CP 3
CR_06E84:
    JR nz,CR_06EA1
CR_06E86:
    LD L,(IX+$16)
CR_06E89:
    LD H,(IX+$17)
CR_06E8C:
    LD DE,$500
CR_06E8F:
    XOR A
CR_06E90:
    SBC HL,DE
CR_06E92:
    JP nc,$6EB0
CR_06E95:
    LD HL,$500
CR_06E98:
    LD (IX+$16),L
CR_06E9B:
    LD (IX+$17),H
CR_06E9E:
    JP $6EB0
CR_06EA1:
    LD L,(IX+$16)
CR_06EA4:
    LD H,(IX+$17)
; THZ right entry requires X velocity >= +3.0; left path requires velocity strictly below -3.0.
CR_06EA7:
    LD DE,$300
CR_06EAA:
    XOR A
CR_06EAB:
    SBC HL,DE
CR_06EAD:
    JP c,$6E73
CR_06EB0:
    LD A,(IX+1)
CR_06EB3:
    CP $22
CR_06EB5:
    JR z,CR_06E73
CR_06EB7:
    CP 5
CR_06EB9:
    JR z,CR_06ECE
CR_06EBB:
    CP 6
CR_06EBD:
    JR z,CR_06ECE
CR_06EBF:
    CP 9
CR_06EC1:
    JR z,CR_06ECE
CR_06EC3:
    CP $10
CR_06EC5:
    JR z,CR_06ECE
CR_06EC7:
    CP $1A
CR_06EC9:
    JR z,CR_06ECE
CR_06ECB:
    JP $6E73

CR_Twist_EnterRight:
; Request player state $22. Fields +$0A/+$0B control direction/speed; +$38 chooses dispatch variant.
CR_06ECE:
    LD (IX+2),$22
CR_06ED2:
    LD L,(IX+$16)
CR_06ED5:
    LD H,(IX+$17)
CR_06ED8:
    ADD HL,HL
CR_06ED9:
    ADD HL,HL
CR_06EDA:
    ADD HL,HL
CR_06EDB:
    ADD HL,HL
CR_06EDC:
    ADD HL,HL
CR_06EDD:
    LD (IX+11),H
CR_06EE0:
    LD (IX+10),$40
CR_06EE4:
    LD (IX+$38),0
CR_06EE8:
    LD A,($D297)
CR_06EEB:
    CP 3
CR_06EED:
    JP nz,$6E73
CR_06EF0:
    LD (IX+$38),2
CR_06EF4:
    JP $6E73
CR_06EF7:
    LD A,$A5
CR_06EF9:
    LD ($DE04),A
CR_06EFC:
    BIT 7,(IX+$17)
CR_06F00:
    JP z,$6E73
CR_06F03:
    LD L,(IX+$16)
CR_06F06:
    LD H,(IX+$17)
CR_06F09:
    LD DE,$FD00
CR_06F0C:
    XOR A
CR_06F0D:
    SBC HL,DE
CR_06F0F:
    JP nc,$6E73
CR_06F12:
    LD A,(IX+1)
CR_06F15:
    CP $22
CR_06F17:
    JP z,$6E73
CR_06F1A:
    CP 5
CR_06F1C:
    JR z,CR_06F31
CR_06F1E:
    CP 6
CR_06F20:
    JR z,CR_06F31
CR_06F22:
    CP 9
CR_06F24:
    JR z,CR_06F31
CR_06F26:
    CP $10
CR_06F28:
    JR z,CR_06F31
CR_06F2A:
    CP $1A
CR_06F2C:
    JR z,CR_06F31
CR_06F2E:
    JP $6E73

CR_Twist_EnterLeft:
CR_06F31:
    LD (IX+2),$22
CR_06F35:
    LD L,(IX+$16)
CR_06F38:
    LD H,(IX+$17)
CR_06F3B:
    DEC HL
CR_06F3C:
    LD A,H
CR_06F3D:
    CPL
CR_06F3E:
    LD H,A
CR_06F3F:
    LD A,L
CR_06F40:
    CPL
CR_06F41:
    LD L,A
CR_06F42:
    ADD HL,HL
CR_06F43:
    ADD HL,HL
CR_06F44:
    ADD HL,HL
CR_06F45:
    ADD HL,HL
CR_06F46:
    ADD HL,HL
CR_06F47:
    LD (IX+11),H
CR_06F4A:
    LD (IX+10),$C0
CR_06F4E:
    LD (IX+$38),1
CR_06F52:
    LD A,($D297)
CR_06F55:
    CP 3
CR_06F57:
    JP nz,$6E73
CR_06F5A:
    LD (IX+$38),3
CR_06F5E:
    JP $6E73

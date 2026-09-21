; floor_projection: ROM $06F61..$0715D (end exclusive $0715E).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Use PREVIOUS surface type D36C to select solid / one-way projection.
SC_06F61:
    LD A,($D36C)
SC_06F64:
    BIT 7,A
SC_06F66:
    JR nz,SC_06F6D
SC_06F68:
    BIT 6,A
SC_06F6A:
    JR nz,SC_06FBB
SC_06F6C:
    RET
SC_06F6D:
    BIT 7,(IX+$19)
SC_06F71:
    RET nz
; The profile magnitude uses AND $3F: values 33..63 are not invalid heights.
SC_06F72:
    LD A,($D368)
SC_06F75:
    AND $3F
SC_06F77:
    CP $20
SC_06F79:
    CALL z,$7056
SC_06F7C:
    LD A,($D35A)
SC_06F7F:
    AND $1F
SC_06F81:
    LD C,A
SC_06F82:
    LD A,($D368)
SC_06F85:
    BIT 6,A
SC_06F87:
    JR z,SC_06F99
SC_06F89:
    LD A,($D36C)
SC_06F8C:
    AND $1F
SC_06F8E:
    CP $1C
SC_06F90:
    JR z,SC_06F97
SC_06F92:
    LD A,($D368)
SC_06F95:
    JR SC_06F99
SC_06F97:
    LD A,$20
; Solid Y correction = (profile & 63) + (adjustedY & 31) - 32, when nonnegative.
SC_06F99:
    AND $3F
SC_06F9B:
    ADD A,C
SC_06F9C:
    CP $20
SC_06F9E:
    RET c
SC_06F9F:
    SUB $20
SC_06FA1:
    LD C,A
SC_06FA2:
    LD B,0
SC_06FA4:
    LD HL,($D514)
SC_06FA7:
    XOR A
SC_06FA8:
    SBC HL,BC
SC_06FAA:
    LD ($D514),HL
SC_06FAD:
    SET 1,(IX+$22)
SC_06FB1:
    CALL $64CB
SC_06FB4:
    LD A,($D100)
SC_06FB7:
    LD ($D369),A
SC_06FBA:
    RET
; One-way branch; IX+$24 bits 0/1 select special subpaths (not in Python subset).
SC_06FBB:
    BIT 0,(IX+$24)
SC_06FBF:
    JR z,SC_06FC7
SC_06FC1:
    LD A,(IX+2)
SC_06FC4:
    CP $14
SC_06FC6:
    RET z
SC_06FC7:
    BIT 1,(IX+$24)
SC_06FCB:
    JP nz,$7010
SC_06FCE:
    BIT 7,(IX+$19)
SC_06FD2:
    RET nz
SC_06FD3:
    LD A,($D368)
SC_06FD6:
    AND $3F
SC_06FD8:
    CALL z,$7056
SC_06FDB:
    RES 1,(IX+$22)
; One-way correction must be strictly less than unsigned high-byte(vy)+9.
SC_06FDF:
    LD A,(IX+$19)
SC_06FE2:
    ADD A,9
SC_06FE4:
    LD B,A
SC_06FE5:
    LD A,($D35A)
SC_06FE8:
    AND $1F
SC_06FEA:
    LD C,A
SC_06FEB:
    LD A,($D368)
SC_06FEE:
    ADD A,C
SC_06FEF:
    CP $20
SC_06FF1:
    RET c
SC_06FF2:
    SUB $20
SC_06FF4:
    CP B
SC_06FF5:
    RET nc
SC_06FF6:
    LD C,A
SC_06FF7:
    LD B,0
SC_06FF9:
    LD HL,($D514)
SC_06FFC:
    XOR A
SC_06FFD:
    SBC HL,BC
SC_06FFF:
    LD ($D514),HL
SC_07002:
    SET 1,(IX+$22)
SC_07006:
    CALL $64CB
SC_07009:
    LD A,($D100)
SC_0700C:
    LD ($D369),A
SC_0700F:
    RET
SC_07010:
    BIT 7,(IX+$19)
SC_07014:
    RET nz
SC_07015:
    RES 1,(IX+$22)
SC_07019:
    LD HL,($D35A)
SC_0701C:
    LD DE,4
SC_0701F:
    ADD HL,DE
SC_07020:
    LD ($D35A),HL
SC_07023:
    LD A,($D35A)
SC_07026:
    AND $1F
SC_07028:
    LD C,A
SC_07029:
    LD A,($D368)
SC_0702C:
    ADD A,C
SC_0702D:
    CP $20
SC_0702F:
    RET c
SC_07030:
    SUB $20
SC_07032:
    CP B
SC_07033:
    RET nc
SC_07034:
    LD C,A
SC_07035:
    LD B,0
SC_07037:
    LD HL,($D514)
SC_0703A:
    XOR A
SC_0703B:
    SBC HL,BC
SC_0703D:
    LD A,($D3BC)
SC_07040:
    LD C,A
SC_07041:
    LD B,0
SC_07043:
    XOR A
SC_07044:
    ADD HL,BC
SC_07045:
    LD ($D514),HL
SC_07048:
    SET 1,(IX+$22)
SC_0704C:
    CALL $64CB
SC_0704F:
    LD A,($D100)
SC_07052:
    LD ($D369),A
SC_07055:
    RET
; Look up the tile one map row above. May project Y or extend the profile.
SC_07056:
    PUSH BC
SC_07057:
    LD A,($D12B)
SC_0705A:
    PUSH AF
SC_0705B:
    LD A,14
SC_0705D:
    LD ($D12B),A
SC_07060:
    LD ($FFFF),A
SC_07063:
    LD HL,($D354)
SC_07066:
    LD DE,($D16A)
SC_0706A:
    ADD HL,DE
SC_0706B:
    LD A,(HL)
SC_0706C:
    LD L,A
SC_0706D:
    LD H,0
SC_0706F:
    ADD HL,HL
SC_07070:
    LD DE,($D2E0)
SC_07074:
    ADD HL,DE
SC_07075:
    LD E,(HL)
SC_07076:
    INC HL
SC_07077:
    LD D,(HL)
SC_07078:
    EX DE,HL
; Dual header: bit 5 plus nonzero object+$25 selects the header seven bytes later.
SC_07079:
    BIT 5,(HL)
SC_0707B:
    JR z,SC_07087
SC_0707D:
    LD A,(IX+$25)
SC_07080:
    OR A
SC_07081:
    JR z,SC_07087
SC_07083:
    LD DE,7
SC_07086:
    ADD HL,DE
SC_07087:
    LD A,(HL)
SC_07088:
    BIT 6,A
SC_0708A:
    JR nz,SC_070C3
SC_0708C:
    BIT 7,A
SC_0708E:
    JR z,SC_070BA
SC_07090:
    INC HL
SC_07091:
    LD A,(HL)
SC_07092:
    LD ($D100),A
SC_07095:
    INC HL
SC_07096:
    LD C,(HL)
SC_07097:
    INC HL
SC_07098:
    LD B,(HL)
SC_07099:
    EX DE,HL
SC_0709A:
    LD A,($D358)
SC_0709D:
    AND $1F
SC_0709F:
    LD L,A
SC_070A0:
    LD H,0
SC_070A2:
    ADD HL,BC
SC_070A3:
    LD A,(HL)
SC_070A4:
    AND $3F
SC_070A6:
    JR z,SC_070BA
SC_070A8:
    LD C,A
SC_070A9:
    LD B,0
SC_070AB:
    LD H,(IX+$15)
SC_070AE:
    LD L,(IX+$14)
SC_070B1:
    XOR A
SC_070B2:
    SBC HL,BC
SC_070B4:
    LD (IX+$15),H
SC_070B7:
    LD (IX+$14),L
SC_070BA:
    POP AF
SC_070BB:
    LD ($D12B),A
SC_070BE:
    LD ($FFFF),A
SC_070C1:
    POP BC
SC_070C2:
    RET
; Above-tile bit 6 branch: extend low-six-bit value by 32, except subtype 9.
SC_070C3:
    AND $1F
SC_070C5:
    CP 9
SC_070C7:
    JR z,SC_070BA
SC_070C9:
    INC HL
SC_070CA:
    INC HL
SC_070CB:
    LD C,(HL)
SC_070CC:
    INC HL
SC_070CD:
    LD B,(HL)
SC_070CE:
    EX DE,HL
SC_070CF:
    LD A,($D358)
SC_070D2:
    AND $1F
SC_070D4:
    LD L,A
SC_070D5:
    LD H,0
SC_070D7:
    ADD HL,BC
SC_070D8:
    LD A,(HL)
SC_070D9:
    AND $3F
SC_070DB:
    JR z,SC_070BA
SC_070DD:
    LD B,A
SC_070DE:
    ADD A,$20
SC_070E0:
    LD ($D368),A
SC_070E3:
    LD B,A
SC_070E4:
    JP $70BA
; Generic object floor projection; different one-way tolerance (+7).
SC_070E7:
    LD A,($D364)
SC_070EA:
    RLCA
SC_070EB:
    JR c,SC_070F1
SC_070ED:
    RLCA
SC_070EE:
    JR c,SC_07123
SC_070F0:
    RET
SC_070F1:
    LD A,($D368)
SC_070F4:
    AND $3F
SC_070F6:
    CP $20
SC_070F8:
    CALL z,$7056
SC_070FB:
    LD A,($D35A)
SC_070FE:
    AND $1F
SC_07100:
    LD C,A
SC_07101:
    LD A,($D368)
SC_07104:
    AND $3F
SC_07106:
    ADD A,C
SC_07107:
    CP $20
SC_07109:
    RET c
SC_0710A:
    SUB $20
SC_0710C:
    LD C,A
SC_0710D:
    LD B,0
SC_0710F:
    LD H,(IX+$15)
SC_07112:
    LD L,(IX+$14)
SC_07115:
    XOR A
SC_07116:
    SBC HL,BC
SC_07118:
    LD (IX+$15),H
SC_0711B:
    LD (IX+$14),L
SC_0711E:
    SET 1,(IX+$22)
SC_07122:
    RET
SC_07123:
    BIT 7,(IX+$19)
SC_07127:
    RET nz
SC_07128:
    LD A,($D368)
SC_0712B:
    AND $3F
SC_0712D:
    CALL z,$7056
SC_07130:
    LD A,(IX+$19)
SC_07133:
    ADD A,7
SC_07135:
    LD B,A
SC_07136:
    LD A,($D35A)
SC_07139:
    AND $1F
SC_0713B:
    LD C,A
SC_0713C:
    LD A,($D368)
SC_0713F:
    ADD A,C
SC_07140:
    CP $20
SC_07142:
    RET c
SC_07143:
    SUB $20
SC_07145:
    CP B
SC_07146:
    RET nc
SC_07147:
    LD C,A
SC_07148:
    LD B,0
SC_0714A:
    LD H,(IX+$15)
SC_0714D:
    LD L,(IX+$14)
SC_07150:
    XOR A
SC_07151:
    SBC HL,BC
SC_07153:
    LD (IX+$15),H
SC_07156:
    LD (IX+$14),L
SC_07159:
    SET 1,(IX+$22)
SC_0715D:
    RET

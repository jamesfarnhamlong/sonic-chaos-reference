; movement_core: ROM $0401A..$0429C (end exclusive $0429D).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

SC_0401A:
    LD HL,($D51C)
SC_0401D:
    BIT 7,H
SC_0401F:
    RET nz
SC_04020:
    LD BC,$D0
SC_04023:
    XOR A
SC_04024:
    SBC HL,BC
SC_04026:
    RET c
SC_04027:
    JP $4984
; Integrate signed 8.8 horizontal velocity, input delta and surface delta into 16.8 X.
SC_0402A:
    LD HL,($D516)
SC_0402D:
    LD DE,($D375)
SC_04031:
    ADD HL,DE
SC_04032:
    LD DE,($D377)
SC_04036:
    ADD HL,DE
SC_04037:
    BIT 7,H
SC_04039:
    JR nz,SC_04052
; Combined contact bit 2 blocks movement to the right.
SC_0403B:
    BIT 2,(IX+$23)
SC_0403F:
    JR nz,SC_0408D
SC_04041:
    LD (IX+10),$40
SC_04045:
    LD A,($D374)
SC_04048:
    LD B,A
SC_04049:
    LD A,H
SC_0404A:
    CP B
SC_0404B:
    JR c,SC_04070
SC_0404D:
    LD HL,($D373)
SC_04050:
    JR SC_04070
; Combined contact bit 3 blocks movement to the left.
SC_04052:
    BIT 3,(IX+$23)
SC_04056:
    JR nz,SC_0408D
SC_04058:
    LD (IX+10),$C0
SC_0405C:
    LD A,($D374)
SC_0405F:
    NEG
SC_04061:
    LD B,A
SC_04062:
    LD A,H
SC_04063:
    CP B
SC_04064:
    JR nc,SC_04070
SC_04066:
    LD HL,($D373)
SC_04069:
    DEC HL
SC_0406A:
    LD A,H
SC_0406B:
    CPL
SC_0406C:
    LD H,A
SC_0406D:
    LD A,L
SC_0406E:
    CPL
SC_0406F:
    LD L,A
SC_04070:
    LD ($D516),HL
SC_04073:
    LD C,0
SC_04075:
    BIT 7,H
SC_04077:
    JR z,SC_0407A
SC_04079:
    DEC C
SC_0407A:
    XOR A
SC_0407B:
    LD DE,($D510)
SC_0407F:
    ADD HL,DE
SC_04080:
    LD ($D510),HL
SC_04083:
    LD A,0
SC_04085:
    ADC A,C
SC_04086:
    ADD A,(IX+$12)
SC_04089:
    LD ($D512),A
SC_0408C:
    RET
; Blocked movement clears velocity and input delta.
SC_0408D:
    LD HL,0
SC_04090:
    LD ($D516),HL
SC_04093:
    LD ($D375),HL
SC_04096:
    RET
; Vertical integration. Airborne flag is IX+$03 bit 0.
SC_04097:
    LD HL,($D518)
SC_0409A:
    LD A,(IX+1)
SC_0409D:
    CP $11
SC_0409F:
    JP z,$410B
SC_040A2:
    BIT 0,(IX+3)
SC_040A6:
    JR nz,SC_040BE
SC_040A8:
    LD A,($D3C0)
SC_040AB:
    OR A
SC_040AC:
    RET nz
SC_040AD:
    LD HL,($D518)
SC_040B0:
    LD A,H
SC_040B1:
    AND A
SC_040B2:
    JP p,$410B
SC_040B5:
    DEC HL
SC_040B6:
    LD A,H
SC_040B7:
    CPL
SC_040B8:
    LD H,A
SC_040B9:
    LD A,L
SC_040BA:
    CPL
SC_040BB:
    LD L,A
SC_040BC:
    JR SC_0410B
SC_040BE:
    LD HL,($D518)
SC_040C1:
    LD A,($D443)
SC_040C4:
    OR A
SC_040C5:
    JR nz,SC_040EA
SC_040C7:
    LD A,(IX+1)
; Dry airborne gravity: state $0B +$18; $1B +$24; other states +$30.
SC_040CA:
    LD DE,$18
SC_040CD:
    CP 11
SC_040CF:
    JR z,SC_040DB
SC_040D1:
    LD DE,$24
SC_040D4:
    CP $1B
SC_040D6:
    JR z,SC_040DB
SC_040D8:
    LD DE,$30
SC_040DB:
    ADD HL,DE
SC_040DC:
    LD A,H
SC_040DD:
    AND A
SC_040DE:
    JP m,$410B
SC_040E1:
    CP 7
SC_040E3:
    JR c,SC_040E8
SC_040E5:
    LD HL,$700
SC_040E8:
    JR SC_0410B
; Water path halves those increments; downward terminal velocity is +4.
SC_040EA:
    LD A,(IX+1)
SC_040ED:
    LD DE,12
SC_040F0:
    CP 11
SC_040F2:
    JR z,SC_040FE
SC_040F4:
    LD DE,$12
SC_040F7:
    CP $1B
SC_040F9:
    JR z,SC_040FE
SC_040FB:
    LD DE,$18
SC_040FE:
    ADD HL,DE
SC_040FF:
    LD A,H
SC_04100:
    AND A
SC_04101:
    JP m,$410B
SC_04104:
    CP 4
SC_04106:
    JR c,SC_0410B
SC_04108:
    LD HL,$400
; Grounded/background floor bit forces +7 Y motion, or +9 for modifiers $0A/$0C.
SC_0410B:
    BIT 1,(IX+$22)
SC_0410F:
    JR z,SC_04124
SC_04111:
    LD HL,$700
SC_04114:
    LD A,($D369)
SC_04117:
    CP 10
SC_04119:
    JR z,SC_04121
SC_0411B:
    CP 12
SC_0411D:
    JR z,SC_04121
SC_0411F:
    JR SC_04124
SC_04121:
    LD HL,$900
SC_04124:
    LD ($D518),HL
SC_04127:
    LD C,0
SC_04129:
    BIT 7,H
SC_0412B:
    JR z,SC_0412E
SC_0412D:
    DEC C
SC_0412E:
    XOR A
SC_0412F:
    LD DE,($D513)
SC_04133:
    ADD HL,DE
SC_04134:
    LD ($D513),HL
SC_04137:
    LD A,0
SC_04139:
    ADC A,C
SC_0413A:
    ADD A,(IX+$15)
SC_0413D:
    LD ($D515),A
SC_04140:
    RET
; Input/state-dependent speed deltas and modifier-table lookup.
SC_04141:
    LD A,(IX+1)
SC_04144:
    CP $29
SC_04146:
    JR nc,SC_04169
SC_04148:
    LD HL,($D511)
SC_0414B:
    LD DE,($D174)
SC_0414F:
    XOR A
SC_04150:
    SBC HL,DE
SC_04152:
    LD A,L
SC_04153:
    LD BC,$10
SC_04156:
    CP $10
SC_04158:
    JP c,$4244
SC_0415B:
    LD BC,$F7
SC_0415E:
    CP $F8
SC_04160:
    JP nc,$4251
SC_04163:
    LD A,(IX+1)
SC_04166:
    CP $1E
SC_04168:
    RET nc
SC_04169:
    LD A,($D443)
SC_0416C:
    OR A
SC_0416D:
    JP nz,$41CA
SC_04170:
    LD A,(IX+1)
SC_04173:
    ADD A,A
SC_04174:
    ADD A,A
SC_04175:
    LD L,A
SC_04176:
    LD H,0
SC_04178:
    LD A,($D137)
SC_0417B:
    AND 12
SC_0417D:
    JP z,$4223
SC_04180:
    LD DE,$431D
SC_04183:
    BIT 7,(IX+$17)
SC_04187:
    JR nz,SC_0418C
SC_04189:
    LD DE,$429D
SC_0418C:
    LD BC,0
SC_0418F:
    BIT 2,A
SC_04191:
    JR nz,SC_04196
SC_04193:
    LD BC,2
SC_04196:
    ADD HL,BC
SC_04197:
    ADD HL,DE
SC_04198:
    LD E,(HL)
SC_04199:
    INC HL
SC_0419A:
    LD D,(HL)
SC_0419B:
    LD HL,($D516)
SC_0419E:
    BIT 7,H
SC_041A0:
    JR z,SC_041A9
SC_041A2:
    DEC HL
SC_041A3:
    LD A,H
SC_041A4:
    CPL
SC_041A5:
    LD H,A
SC_041A6:
    LD A,L
SC_041A7:
    CPL
SC_041A8:
    LD L,A
SC_041A9:
    LD BC,$80
SC_041AC:
    ADD HL,BC
SC_041AD:
    LD A,H
SC_041AE:
    OR A
SC_041AF:
    JR nz,SC_041B4
SC_041B1:
    EX DE,HL
SC_041B2:
    ADD HL,HL
SC_041B3:
    EX DE,HL
SC_041B4:
    LD ($D375),DE
; D369 is a BYTE OFFSET into signed 16-bit table at $459D.
SC_041B8:
    LD A,($D369)
SC_041BB:
    LD L,A
SC_041BC:
    LD H,0
SC_041BE:
    LD DE,$459D
SC_041C1:
    ADD HL,DE
SC_041C2:
    LD E,(HL)
SC_041C3:
    INC HL
SC_041C4:
    LD D,(HL)
SC_041C5:
    LD ($D377),DE
SC_041C9:
    RET
SC_041CA:
    LD A,(IX+1)
SC_041CD:
    ADD A,A
SC_041CE:
    ADD A,A
SC_041CF:
    LD L,A
SC_041D0:
    LD H,0
SC_041D2:
    LD A,($D137)
SC_041D5:
    AND 12
SC_041D7:
    JR z,SC_04223
SC_041D9:
    LD DE,$449D
SC_041DC:
    BIT 7,(IX+$17)
SC_041E0:
    JR nz,SC_041E5
SC_041E2:
    LD DE,$441D
SC_041E5:
    LD BC,0
SC_041E8:
    BIT 2,A
SC_041EA:
    JR nz,SC_041EF
SC_041EC:
    LD BC,2
SC_041EF:
    ADD HL,BC
SC_041F0:
    ADD HL,DE
SC_041F1:
    LD E,(HL)
SC_041F2:
    INC HL
SC_041F3:
    LD D,(HL)
SC_041F4:
    LD HL,($D516)
SC_041F7:
    BIT 7,H
SC_041F9:
    JR z,SC_04202
SC_041FB:
    DEC HL
SC_041FC:
    LD A,H
SC_041FD:
    CPL
SC_041FE:
    LD H,A
SC_041FF:
    LD A,L
SC_04200:
    CPL
SC_04201:
    LD L,A
SC_04202:
    LD BC,$80
SC_04205:
    ADD HL,BC
SC_04206:
    LD A,H
SC_04207:
    OR A
SC_04208:
    JR nz,SC_0420D
SC_0420A:
    EX DE,HL
SC_0420B:
    ADD HL,HL
SC_0420C:
    EX DE,HL
SC_0420D:
    LD ($D375),DE
SC_04211:
    LD A,($D369)
SC_04214:
    LD L,A
SC_04215:
    LD H,0
SC_04217:
    LD DE,$459D
SC_0421A:
    ADD HL,DE
SC_0421B:
    LD E,(HL)
SC_0421C:
    INC HL
SC_0421D:
    LD D,(HL)
SC_0421E:
    LD ($D377),DE
SC_04222:
    RET
; No-direction friction uses table $439D. $451D is not selected by this branch.
SC_04223:
    LD DE,0
SC_04226:
    LD ($D375),DE
SC_0422A:
    LD A,(IX+$16)
SC_0422D:
    OR (IX+$17)
SC_04230:
    RET z
SC_04231:
    LD DE,$439D
SC_04234:
    LD BC,0
SC_04237:
    BIT 7,(IX+$17)
SC_0423B:
    JP nz,$4196
SC_0423E:
    LD BC,2
SC_04241:
    JP $4196
SC_04244:
    LD HL,($D174)
SC_04247:
    ADD HL,BC
SC_04248:
    LD ($D511),HL
SC_0424B:
    XOR A
SC_0424C:
    LD ($D510),A
SC_0424F:
    JR SC_0425C
SC_04251:
    LD HL,($D174)
SC_04254:
    ADD HL,BC
SC_04255:
    LD ($D511),HL
SC_04258:
    XOR A
SC_04259:
    LD ($D510),A
SC_0425C:
    LD HL,($D510)
SC_0425F:
    LD DE,($D516)
SC_04263:
    LD C,0
SC_04265:
    BIT 7,D
SC_04267:
    JR z,SC_0426A
SC_04269:
    DEC C
SC_0426A:
    XOR A
SC_0426B:
    SBC HL,DE
SC_0426D:
    LD ($D510),HL
SC_04270:
    LD A,(IX+$12)
SC_04273:
    SBC A,C
SC_04274:
    LD (IX+$12),A
SC_04277:
    LD HL,0
SC_0427A:
    LD ($D375),HL
SC_0427D:
    LD ($D516),HL
SC_04280:
    RET
SC_04281:
    LD HL,($D511)
SC_04284:
    LD DE,($D174)
SC_04288:
    XOR A
SC_04289:
    SBC HL,DE
SC_0428B:
    LD A,L
SC_0428C:
    LD BC,$10
SC_0428F:
    CP $10
SC_04291:
    JP c,$4244
SC_04294:
    LD BC,$F7
SC_04297:
    CP $F8
SC_04299:
    JP nc,$4251
SC_0429C:
    RET

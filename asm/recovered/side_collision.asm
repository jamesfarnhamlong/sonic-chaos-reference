; side_collision: ROM $0715E..$073C8 (end exclusive $073C9).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Clear side contacts, test right (+9,+6 effective), then left (-9,+6 effective).
SC_0715E:
    LD HL,$D522
SC_07161:
    RES 2,(HL)
SC_07163:
    RES 3,(HL)
SC_07165:
    CALL $716B
SC_07168:
    JP $7210
SC_0716B:
    LD BC,($D49C)
SC_0716F:
    LD DE,($D49E)
SC_07173:
    CALL $7666
SC_07176:
    CALL $73A7
SC_07179:
    LD A,($D364)
SC_0717C:
    AND $1F
SC_0717E:
    CP 5
SC_07180:
    JP z,$7306
SC_07183:
    CP 13
SC_07185:
    JP z,$72B6
SC_07188:
    CP $13
SC_0718A:
    JP z,$7357
SC_0718D:
    CP $16
SC_0718F:
    JP z,$736B
SC_07192:
    CP $1E
SC_07194:
    JP nz,$71B2
SC_07197:
    LD A,($D137)
SC_0719A:
    AND 8
SC_0719C:
    JR z,SC_071B2
SC_0719E:
    LD B,$5E
SC_071A0:
    LD A,($D2C8)
SC_071A3:
    DEC A
SC_071A4:
    JR z,SC_071A8
SC_071A6:
    LD B,$55
SC_071A8:
    LD A,($D506)
SC_071AB:
    CP B
SC_071AC:
    JR nz,SC_071B2
SC_071AE:
    LD (IX+2),$34
; Right-side ordinary projection: require surface bit 7; use HORIZONTAL profile D367.
SC_071B2:
    LD A,($D364)
SC_071B5:
    BIT 7,A
SC_071B7:
    RET z
SC_071B8:
    LD A,($D367)
SC_071BB:
    BIT 6,A
SC_071BD:
    JR nz,SC_071CF
SC_071BF:
    AND $3F
SC_071C1:
    RET z
SC_071C2:
    LD B,A
SC_071C3:
    LD A,($D358)
SC_071C6:
    AND $1F
SC_071C8:
    CP B
SC_071C9:
    RET nc
SC_071CA:
    LD C,A
SC_071CB:
    LD B,0
SC_071CD:
    JR SC_071EC
; Horizontal profile bit 6 chooses boundary measured from the right edge.
SC_071CF:
    AND $3F
SC_071D1:
    RET z
SC_071D2:
    LD C,A
SC_071D3:
    LD HL,($D358)
SC_071D6:
    LD DE,$20
SC_071D9:
    ADD HL,DE
SC_071DA:
    LD A,L
SC_071DB:
    AND $E0
SC_071DD:
    LD L,A
SC_071DE:
    LD B,0
SC_071E0:
    XOR A
SC_071E1:
    SBC HL,BC
SC_071E3:
    EX DE,HL
SC_071E4:
    LD HL,($D358)
SC_071E7:
    SBC HL,DE
SC_071E9:
    RET c
SC_071EA:
    LD C,L
SC_071EB:
    LD B,H
SC_071EC:
    LD HL,($D511)
SC_071EF:
    XOR A
SC_071F0:
    SBC HL,BC
SC_071F2:
    LD ($D511),HL
SC_071F5:
    SET 2,(IX+$22)
SC_071F9:
    CALL $64CB
SC_071FC:
    LD A,($D364)
SC_071FF:
    AND $1F
SC_07201:
    CP 10
SC_07203:
    RET nz
SC_07204:
    LD A,($D501)
SC_07207:
    CP $11
SC_07209:
    RET z
SC_0720A:
    LD HL,$FA00
SC_0720D:
    JP $4868
; Left-side probe uses D498/D49A offsets initialized at $3686.
SC_07210:
    LD BC,($D498)
SC_07214:
    LD DE,($D49A)
SC_07218:
    CALL $7666
SC_0721B:
    CALL $73B8
SC_0721E:
    LD A,($D364)
SC_07221:
    AND $1F
SC_07223:
    CP 5
SC_07225:
    JP z,$7329
SC_07228:
    CP 13
SC_0722A:
    JP z,$72DD
SC_0722D:
    CP $13
SC_0722F:
    JP z,$7357
SC_07232:
    CP $16
SC_07234:
    JP z,$7389
SC_07237:
    CP $1E
SC_07239:
    JP nz,$7257
SC_0723C:
    LD A,($D137)
SC_0723F:
    AND 4
SC_07241:
    JR z,SC_07257
SC_07243:
    LD B,$5E
SC_07245:
    LD A,($D2C8)
SC_07248:
    DEC A
SC_07249:
    JR z,SC_0724D
SC_0724B:
    LD B,$55
SC_0724D:
    LD A,($D506)
SC_07250:
    CP B
SC_07251:
    JR nz,SC_07257
SC_07253:
    LD (IX+2),$34
; Left-side ordinary projection; low six bits are extent, bit 6 selects orientation.
SC_07257:
    LD A,($D364)
SC_0725A:
    BIT 7,A
SC_0725C:
    RET z
SC_0725D:
    LD A,($D367)
SC_07260:
    BIT 6,A
SC_07262:
    JR nz,SC_07277
SC_07264:
    AND $3F
SC_07266:
    RET z
SC_07267:
    LD B,A
SC_07268:
    LD A,($D358)
SC_0726B:
    AND $1F
SC_0726D:
    SUB B
SC_0726E:
    RET nc
SC_0726F:
    NEG
SC_07271:
    DEC A
SC_07272:
    LD C,A
SC_07273:
    LD B,0
SC_07275:
    JR SC_07294
SC_07277:
    AND $3F
SC_07279:
    RET z
SC_0727A:
    LD C,A
SC_0727B:
    LD HL,($D358)
SC_0727E:
    LD DE,$20
SC_07281:
    ADD HL,DE
SC_07282:
    LD A,L
SC_07283:
    AND $E0
SC_07285:
    LD L,A
SC_07286:
    DEC HL
SC_07287:
    LD DE,($D358)
SC_0728B:
    XOR A
SC_0728C:
    SBC HL,DE
SC_0728E:
    RET c
SC_0728F:
    LD A,L
SC_07290:
    CP C
SC_07291:
    RET nc
SC_07292:
    LD C,L
SC_07293:
    LD B,H
SC_07294:
    LD HL,($D511)
SC_07297:
    ADD HL,BC
SC_07298:
    LD ($D511),HL
SC_0729B:
    SET 3,(IX+$22)
SC_0729F:
    CALL $64CB
SC_072A2:
    LD A,($D364)
SC_072A5:
    AND $1F
SC_072A7:
    CP 10
SC_072A9:
    RET nz
SC_072AA:
    LD A,($D501)
SC_072AD:
    CP $11
SC_072AF:
    RET z
SC_072B0:
    LD HL,$600
SC_072B3:
    JP $4849
; Breakable side handler checks rolling and X-speed before changing map data.
SC_072B6:
    BIT 1,(IX+3)
SC_072BA:
    JP z,$71B8
SC_072BD:
    LD A,($D517)
SC_072C0:
    BIT 7,A
SC_072C2:
    JR z,SC_072C6
SC_072C4:
    NEG
SC_072C6:
    CP 3
SC_072C8:
    JP c,$71B8
SC_072CB:
    LD HL,($D516)
SC_072CE:
    LD A,H
SC_072CF:
    CP 7
SC_072D1:
    JR nc,SC_072DA
SC_072D3:
    LD BC,$40
SC_072D6:
    ADD HL,BC
SC_072D7:
    LD ($D516),HL
SC_072DA:
    JP $7898
SC_072DD:
    BIT 1,(IX+3)
SC_072E1:
    JP z,$725D
SC_072E4:
    LD A,($D517)
SC_072E7:
    BIT 7,A
SC_072E9:
    JR z,SC_072ED
SC_072EB:
    NEG
SC_072ED:
    CP 3
SC_072EF:
    JP c,$725D
SC_072F2:
    LD HL,($D516)
SC_072F5:
    LD A,H
SC_072F6:
    NEG
SC_072F8:
    CP 7
SC_072FA:
    JR nc,SC_07303
SC_072FC:
    LD BC,$FFC0
SC_072FF:
    ADD HL,BC
SC_07300:
    LD ($D516),HL
SC_07303:
    JP $7898
SC_07306:
    LD A,($D353)
SC_07309:
    AND $FE
SC_0730B:
    CP $F2
SC_0730D:
    JR z,SC_0731A
SC_0730F:
    LD A,($D502)
SC_07312:
    CP $17
SC_07314:
    JP z,$72B6
SC_07317:
    CP $1E
SC_07319:
    RET z
SC_0731A:
    CALL $71B8
SC_0731D:
    CALL $64CB
SC_07320:
    LD A,($D353)
SC_07323:
    CP $F4
SC_07325:
    RET nz
SC_07326:
    JP $7349
SC_07329:
    LD A,($D353)
SC_0732C:
    AND $FE
SC_0732E:
    CP $F2
SC_07330:
    JR z,SC_0733D
SC_07332:
    LD A,($D502)
SC_07335:
    CP $17
SC_07337:
    JP z,$72DD
SC_0733A:
    CP $1E
SC_0733C:
    RET z
SC_0733D:
    CALL $725D
SC_07340:
    CALL $64CB
SC_07343:
    LD A,($D353)
SC_07346:
    CP $F5
SC_07348:
    RET nz
SC_07349:
    BIT 7,(IX+3)
SC_0734D:
    RET nz
SC_0734E:
    LD HL,$100
SC_07351:
    LD ($D518),HL
SC_07354:
    JP $48F7
SC_07357:
    LD A,($D353)
SC_0735A:
    LD ($D36D),A
SC_0735D:
    LD A,($D353)
SC_07360:
    CP $81
SC_07362:
    JP z,$6D4F
SC_07365:
    CP $82
SC_07367:
    JP z,$6D4F
SC_0736A:
    RET
SC_0736B:
    LD A,($D501)
SC_0736E:
    CP 15
SC_07370:
    JP z,$71B8
SC_07373:
    CP $15
SC_07375:
    JP z,$71B8
SC_07378:
    BIT 1,(IX+3)
SC_0737C:
    JP z,$71B8
SC_0737F:
    LD A,($D519)
SC_07382:
    AND A
SC_07383:
    JP m,$71B8
SC_07386:
    JP $7857
SC_07389:
    LD A,($D501)
SC_0738C:
    CP 15
SC_0738E:
    JP z,$725D
SC_07391:
    CP $15
SC_07393:
    JP z,$725D
SC_07396:
    BIT 1,(IX+3)
SC_0739A:
    JP z,$725D
SC_0739D:
    LD A,($D519)
SC_073A0:
    AND A
SC_073A1:
    JP m,$725D
SC_073A4:
    JP $7857
; Tile $A1 can clear collision plane object+$25; early unwind of right-side check.
SC_073A7:
    LD A,($D353)
SC_073AA:
    CP $A1
SC_073AC:
    RET nz
SC_073AD:
    LD A,(IX+$25)
SC_073B0:
    OR A
SC_073B1:
    RET z
SC_073B2:
    LD (IX+$25),0
SC_073B6:
    POP AF
SC_073B7:
    RET
; Tile $A2 can set collision plane object+$25; early unwind of left-side check.
SC_073B8:
    LD A,($D353)
SC_073BB:
    CP $A2
SC_073BD:
    RET nz
SC_073BE:
    LD A,(IX+$25)
SC_073C1:
    OR A
SC_073C2:
    RET nz
SC_073C3:
    LD (IX+$25),1
SC_073C7:
    POP AF
SC_073C8:
    RET

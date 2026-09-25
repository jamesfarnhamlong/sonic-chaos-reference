; object_player_overlap: ROM $06328..$0640A (end exclusive $0640B).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Shared object/player overlap: fixed player/object anchor extents, minimum-penetration directional bits, and no physical projection.
SC_06328:
    XOR A
SC_06329:
    LD (IX+$20),A
SC_0632C:
    LD A,(IX+$21)
SC_0632F:
    AND $F0
SC_06331:
    LD (IX+$21),A
SC_06334:
    BIT 6,(IX+3)
SC_06338:
    RET nz
SC_06339:
    BIT 7,(IX+3)
SC_0633D:
    JR nz,SC_06345
SC_0633F:
    LD A,($D503)
SC_06342:
    BIT 6,A
SC_06344:
    RET nz
SC_06345:
    LD HL,($D511)
SC_06348:
    LD E,(IX+$11)
SC_0634B:
    LD D,(IX+$12)
SC_0634E:
    XOR A
SC_0634F:
    SBC HL,DE
SC_06351:
    JR c,SC_0636A
SC_06353:
    LD A,H
SC_06354:
    OR A
SC_06355:
    JP nz,$6402
SC_06358:
    LD A,($D52C)
SC_0635B:
    ADD A,(IX+$2C)
SC_0635E:
    SUB L
SC_0635F:
    JP c,$6402
SC_06362:
    LD C,A
SC_06363:
    SET 2,(IX+$21)
SC_06367:
    JP $6385
SC_0636A:
    LD A,H
SC_0636B:
    INC A
SC_0636C:
    JP nz,$6402
SC_0636F:
    LD A,L
SC_06370:
    NEG
SC_06372:
    JP z,$6402
SC_06375:
    LD L,A
SC_06376:
    LD A,($D52C)
SC_06379:
    ADD A,(IX+$2C)
SC_0637C:
    SUB L
SC_0637D:
    JP c,$6402
SC_06380:
    LD C,A
SC_06381:
    SET 3,(IX+$21)
SC_06385:
    LD HL,($D514)
SC_06388:
    LD E,(IX+$14)
SC_0638B:
    LD D,(IX+$15)
SC_0638E:
    XOR A
SC_0638F:
    SBC HL,DE
SC_06391:
    JR c,SC_063A5
SC_06393:
    LD A,H
SC_06394:
    OR A
SC_06395:
    JR nz,SC_06402
SC_06397:
    LD A,($D52D)
SC_0639A:
    SUB L
SC_0639B:
    JR c,SC_06402
SC_0639D:
    LD L,A
SC_0639E:
    SET 1,(IX+$21)
SC_063A2:
    JP $63BA
SC_063A5:
    LD A,H
SC_063A6:
    INC A
SC_063A7:
    JR nz,SC_06402
SC_063A9:
    LD A,L
SC_063AA:
    NEG
SC_063AC:
    JR z,SC_06402
SC_063AE:
    LD L,A
SC_063AF:
    LD A,(IX+$2D)
SC_063B2:
    SUB L
SC_063B3:
    JR c,SC_06402
SC_063B5:
    LD L,A
SC_063B6:
    SET 0,(IX+$21)
SC_063BA:
    LD A,C
SC_063BB:
    CP L
SC_063BC:
    LD B,12
SC_063BE:
    JR c,SC_063C2
SC_063C0:
    LD B,3
SC_063C2:
    LD A,(IX+$21)
SC_063C5:
    AND B
SC_063C6:
    LD (IX+$21),A
SC_063C9:
    LD A,($D503)
SC_063CC:
    BIT 7,A
SC_063CE:
    JR nz,SC_063D4
SC_063D0:
    LD (IX+$20),1
SC_063D4:
    BIT 7,(IX+3)
SC_063D8:
    JR nz,SC_063E3
SC_063DA:
    PUSH IX
SC_063DC:
    POP HL
SC_063DD:
    CALL $606B
SC_063E0:
    LD ($D520),A
SC_063E3:
    LD A,(IX+$21)
SC_063E6:
    AND 15
SC_063E8:
    LD B,A
SC_063E9:
    AND 3
SC_063EB:
    LD C,12
SC_063ED:
    JR z,SC_063F1
SC_063EF:
    LD C,3
SC_063F1:
    LD A,B
SC_063F2:
    XOR C
SC_063F3:
    RLCA
SC_063F4:
    RLCA
SC_063F5:
    RLCA
SC_063F6:
    RLCA
SC_063F7:
    LD B,A
SC_063F8:
    LD A,($D521)
SC_063FB:
    AND 15
SC_063FD:
    OR B
SC_063FE:
    LD ($D521),A
SC_06401:
    RET
SC_06402:
    LD A,(IX+$21)
SC_06405:
    AND $F0
SC_06407:
    LD (IX+$21),A
SC_0640A:
    RET

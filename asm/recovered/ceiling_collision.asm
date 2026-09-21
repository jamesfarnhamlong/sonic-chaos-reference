; ceiling_collision: ROM $073C9..$0753D (end exclusive $0753E).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Ceiling centre probe uses dy=-24, effective Y-6 after lookup anchor adjustment.
SC_073C9:
    RES 0,(IX+$22)
SC_073CD:
    LD A,($D3C0)
SC_073D0:
    OR A
SC_073D1:
    JR nz,SC_073DD
SC_073D3:
    BIT 1,(IX+$22)
SC_073D7:
    RET nz
SC_073D8:
    BIT 7,(IX+$19)
SC_073DC:
    RET z
SC_073DD:
    LD BC,0
SC_073E0:
    LD DE,$FFE8
SC_073E3:
    BIT 1,(IX+0)
SC_073E7:
    JR z,SC_073EF
SC_073E9:
    LD BC,0
SC_073EC:
    LD DE,$FFE8
SC_073EF:
    CALL $7666
SC_073F2:
    LD A,($D364)
SC_073F5:
    LD B,A
SC_073F6:
    AND $1F
SC_073F8:
    CP 13
SC_073FA:
    JP z,$7464
SC_073FD:
    CP $15
SC_073FF:
    JP z,$748F
SC_07402:
    CP $14
SC_07404:
    JP z,$749D
SC_07407:
    CP $13
SC_07409:
    JP z,$752F
SC_0740C:
    CP 5
SC_0740E:
    JP z,$74E7
SC_07411:
    CP $1C
SC_07413:
    JP z,$746E
SC_07416:
    BIT 7,B
SC_07418:
    RET z
SC_07419:
    LD HL,($D35A)
SC_0741C:
    LD A,L
SC_0741D:
    AND $E0
SC_0741F:
    LD L,A
SC_07420:
    LD DE,($D514)
SC_07424:
    LD A,E
SC_07425:
    AND $E0
SC_07427:
    LD E,A
SC_07428:
    XOR A
SC_07429:
    SBC HL,DE
SC_0742B:
    RET z
SC_0742C:
    LD A,($D35A)
SC_0742F:
    AND $1F
SC_07431:
    LD C,A
SC_07432:
    LD A,($D368)
SC_07435:
    LD B,A
SC_07436:
    AND $3F
SC_07438:
    RET z
SC_07439:
    BIT 6,B
SC_0743B:
    JR nz,SC_0743F
SC_0743D:
    LD A,$20
SC_0743F:
    CP C
SC_07440:
    RET c
SC_07441:
    SUB C
SC_07442:
    LD C,A
SC_07443:
    LD B,0
SC_07445:
    LD L,(IX+$14)
SC_07448:
    LD H,(IX+$15)
SC_0744B:
    ADD HL,BC
SC_0744C:
    LD (IX+$14),L
SC_0744F:
    LD (IX+$15),H
SC_07452:
    SET 0,(IX+$22)
SC_07456:
    CALL $64CB
SC_07459:
    LD HL,$100
SC_0745C:
    LD ($D518),HL
SC_0745F:
    RES 0,(IX+$22)
SC_07463:
    RET
; Ceiling breakable handler; routes to map modification at $7898.
SC_07464:
    LD A,($D3C0)
SC_07467:
    OR A
SC_07468:
    JP z,$7898
SC_0746B:
    JP $4984
SC_0746E:
    LD HL,($D35A)
SC_07471:
    LD A,L
SC_07472:
    AND $E0
SC_07474:
    LD L,A
SC_07475:
    LD A,($D368)
SC_07478:
    BIT 6,A
SC_0747A:
    JR nz,SC_0747E
SC_0747C:
    LD A,$20
SC_0747E:
    AND $3F
SC_07480:
    LD E,A
SC_07481:
    LD D,0
SC_07483:
    ADD HL,DE
SC_07484:
    LD DE,($D514)
SC_07488:
    XOR A
SC_07489:
    SBC HL,DE
SC_0748B:
    RET nc
SC_0748C:
    JP $742C
SC_0748F:
    LD HL,$780
SC_07492:
    LD ($D518),HL
SC_07495:
    LD A,$A6
SC_07497:
    LD ($DE04),A
SC_0749A:
    JP $47FB
SC_0749D:
    LD A,($D353)
SC_074A0:
    AND $FE
SC_074A2:
    CP $3A
SC_074A4:
    RET nz
SC_074A5:
    LD A,($D35A)
SC_074A8:
    AND $1F
SC_074AA:
    LD C,A
SC_074AB:
    LD A,($D368)
SC_074AE:
    LD B,A
SC_074AF:
    AND $3F
SC_074B1:
    RET z
SC_074B2:
    CP $20
SC_074B4:
    JR z,SC_074B9
SC_074B6:
    BIT 6,B
SC_074B8:
    RET z
SC_074B9:
    CP C
SC_074BA:
    RET c
SC_074BB:
    SUB C
SC_074BC:
    LD C,A
SC_074BD:
    LD B,0
SC_074BF:
    LD L,(IX+$14)
SC_074C2:
    LD H,(IX+$15)
SC_074C5:
    ADD HL,BC
SC_074C6:
    LD (IX+$14),L
SC_074C9:
    LD (IX+$15),H
SC_074CC:
    SET 0,(IX+$22)
SC_074D0:
    CALL $64CB
SC_074D3:
    LD HL,$580
SC_074D6:
    LD ($D518),HL
SC_074D9:
    LD HL,$400
SC_074DC:
    LD ($D516),HL
SC_074DF:
    LD A,$A6
SC_074E1:
    LD ($DE04),A
SC_074E4:
    JP $47FB
SC_074E7:
    LD A,($D35A)
SC_074EA:
    AND $1F
SC_074EC:
    LD C,A
SC_074ED:
    LD A,($D368)
SC_074F0:
    LD B,A
SC_074F1:
    AND $3F
SC_074F3:
    RET z
SC_074F4:
    CP $20
SC_074F6:
    JR z,SC_074FB
SC_074F8:
    BIT 6,B
SC_074FA:
    RET z
SC_074FB:
    CP C
SC_074FC:
    RET c
SC_074FD:
    SUB C
SC_074FE:
    LD C,A
SC_074FF:
    LD B,0
SC_07501:
    LD L,(IX+$14)
SC_07504:
    LD H,(IX+$15)
SC_07507:
    ADD HL,BC
SC_07508:
    LD (IX+$14),L
SC_0750B:
    LD (IX+$15),H
SC_0750E:
    SET 0,(IX+$22)
SC_07512:
    CALL $64CB
SC_07515:
    LD A,(IX+1)
SC_07518:
    CP $1E
SC_0751A:
    RET z
SC_0751B:
    LD A,($D353)
SC_0751E:
    AND $FE
SC_07520:
    CP $3E
SC_07522:
    JP nz,$7459
SC_07525:
    BIT 7,(IX+3)
SC_07529:
    JP nz,$7459
SC_0752C:
    JP $48F7
SC_0752F:
    LD A,($D353)
SC_07532:
    CP $80
SC_07534:
    RET nz
SC_07535:
    LD A,($D353)
SC_07538:
    LD ($D36D),A
SC_0753B:
    JP $6D4F

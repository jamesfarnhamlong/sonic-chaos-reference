; object_animation_engine: ROM $064FA..$065AE (end exclusive $065AF).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Generic object animation/state-script engine.
SC_064FA:
    LD A,(IX+14)
SC_064FD:
    OR (IX+15)
SC_06500:
    JR z,SC_0651D
SC_06502:
    BIT 3,(IX+3)
SC_06506:
    JR nz,SC_06510
SC_06508:
    LD A,(IX+2)
SC_0650B:
    CP (IX+1)
SC_0650E:
    JR nz,SC_06517
SC_06510:
    DEC (IX+7)
SC_06513:
    JP z,$653D
SC_06516:
    RET
SC_06517:
    LD A,(IX+2)
SC_0651A:
    LD (IX+1),A
SC_0651D:
    LD A,(IX+0)
SC_06520:
    DEC A
SC_06521:
    ADD A,A
SC_06522:
    LD L,A
SC_06523:
    LD H,0
SC_06525:
    LD DE,$65BA
SC_06528:
    ADD HL,DE
SC_06529:
    LD E,(HL)
SC_0652A:
    INC HL
SC_0652B:
    LD D,(HL)
SC_0652C:
    LD A,(IX+1)
SC_0652F:
    ADD A,A
SC_06530:
    LD L,A
SC_06531:
    LD H,0
SC_06533:
    ADD HL,DE
SC_06534:
    LD E,(HL)
SC_06535:
    INC HL
SC_06536:
    LD D,(HL)
SC_06537:
    LD (IX+14),E
SC_0653A:
    LD (IX+15),D
SC_0653D:
    LD L,(IX+14)
SC_06540:
    LD H,(IX+15)
SC_06543:
    LD A,(HL)
SC_06544:
    CP $FF
SC_06546:
    JP z,$6680
SC_06549:
    LD (IX+7),A
SC_0654C:
    INC HL
SC_0654D:
    LD A,(HL)
SC_0654E:
    LD (IX+6),A
SC_06551:
    INC HL
SC_06552:
    LD A,(HL)
SC_06553:
    LD (IX+12),A
SC_06556:
    INC HL
SC_06557:
    LD A,(HL)
SC_06558:
    LD (IX+13),A
SC_0655B:
    INC HL
SC_0655C:
    LD (IX+14),L
SC_0655F:
    LD (IX+15),H
SC_06562:
    LD A,15
SC_06564:
    CALL $1C6F
SC_06567:
    LD L,(IX+0)
SC_0656A:
    LD H,0
SC_0656C:
    ADD HL,HL
SC_0656D:
    LD DE,$8000
SC_06570:
    ADD HL,DE
SC_06571:
    LD E,(HL)
SC_06572:
    INC HL
SC_06573:
    LD D,(HL)
SC_06574:
    LD L,(IX+6)
SC_06577:
    LD H,0
SC_06579:
    ADD HL,HL
SC_0657A:
    ADD HL,DE
SC_0657B:
    LD E,(HL)
SC_0657C:
    INC HL
SC_0657D:
    LD D,(HL)
SC_0657E:
    EX DE,HL
SC_0657F:
    LD A,(HL)
SC_06580:
    BIT 3,(IX+4)
SC_06584:
    JR z,SC_06590
SC_06586:
    OR A
SC_06587:
    JR z,SC_06590
SC_06589:
    INC A
SC_0658A:
    JR z,SC_0658D
SC_0658C:
    DEC A
SC_0658D:
    OR $80
SC_0658F:
    XOR A
SC_06590:
    LD (IX+5),A
SC_06593:
    INC HL
SC_06594:
    LD A,(HL)
SC_06595:
    LD (IX+$2C),A
SC_06598:
    INC HL
SC_06599:
    LD A,(HL)
SC_0659A:
    LD (IX+$2D),A
SC_0659D:
    INC HL
SC_0659E:
    LD A,(HL)
SC_0659F:
    LD (IX+$28),A
SC_065A2:
    INC HL
SC_065A3:
    LD A,(HL)
SC_065A4:
    LD (IX+$29),A
SC_065A7:
    INC HL
SC_065A8:
    LD (IX+$2A),L
SC_065AB:
    LD (IX+$2B),H
SC_065AE:
    RET

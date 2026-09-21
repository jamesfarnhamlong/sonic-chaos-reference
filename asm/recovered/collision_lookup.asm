; collision_lookup: ROM $07666..$077CA (end exclusive $077CB).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Full collision lookup; temporarily maps bank 14 into $8000..$BFFF.
SC_07666:
    LD A,($D12B)
SC_07669:
    PUSH AF
SC_0766A:
    LD A,14
SC_0766C:
    LD ($D12B),A
SC_0766F:
    LD ($FFFF),A
SC_07672:
    LD H,(IX+$12)
SC_07675:
    LD L,(IX+$11)
SC_07678:
    ADD HL,BC
SC_07679:
    LD ($D358),HL
SC_0767C:
    SLA L
SC_0767E:
    RL H
SC_07680:
    SLA L
SC_07682:
    RL H
SC_07684:
    SLA L
SC_07686:
    RL H
SC_07688:
    LD B,H
SC_07689:
    LD H,(IX+$15)
SC_0768C:
    LD L,(IX+$14)
SC_0768F:
    ADD HL,DE
; Add 18 to the player anchor Y; clamp a negative signed result to zero.
SC_07690:
    LD DE,$12
SC_07693:
    ADD HL,DE
SC_07694:
    BIT 7,H
SC_07696:
    JR z,SC_0769B
SC_07698:
    LD HL,0
SC_0769B:
    LD ($D35A),HL
SC_0769E:
    SLA L
SC_076A0:
    RL H
SC_076A2:
    SLA L
SC_076A4:
    RL H
SC_076A6:
    SLA L
SC_076A8:
    RL H
SC_076AA:
    LD A,H
SC_076AB:
    ADD A,A
SC_076AC:
    LD L,A
SC_076AD:
    LD H,0
; Use row-stride pointer D168, then base C001; reject outside C000..CFFF.
SC_076AF:
    LD DE,($D168)
SC_076B3:
    ADD HL,DE
SC_076B4:
    LD E,(HL)
SC_076B5:
    INC HL
SC_076B6:
    LD D,(HL)
SC_076B7:
    LD L,B
SC_076B8:
    LD H,0
SC_076BA:
    ADD HL,DE
SC_076BB:
    LD DE,$C001
SC_076BE:
    ADD HL,DE
SC_076BF:
    LD A,H
SC_076C0:
    AND $F0
SC_076C2:
    CP $C0
SC_076C4:
    JP nz,$77B0
SC_076C7:
    LD ($D354),HL
SC_076CA:
    LD A,(HL)
SC_076CB:
    LD ($D353),A
SC_076CE:
    LD L,A
SC_076CF:
    LD H,0
SC_076D1:
    ADD HL,HL
; Collision header pointer table comes from D2E0 (THZ: CPU $8000 in bank 14).
SC_076D2:
    LD DE,($D2E0)
SC_076D6:
    ADD HL,DE
SC_076D7:
    LD E,(HL)
SC_076D8:
    INC HL
SC_076D9:
    LD D,(HL)
SC_076DA:
    EX DE,HL
SC_076DB:
    LD A,(HL)
SC_076DC:
    LD ($D364),A
; Surface bit 5 plus object plane +$25 chooses alternate seven-byte header.
SC_076DF:
    BIT 5,A
SC_076E1:
    JR z,SC_076F1
SC_076E3:
    LD A,(IX+$25)
SC_076E6:
    OR A
SC_076E7:
    JR z,SC_076F1
SC_076E9:
    LD DE,7
SC_076EC:
    ADD HL,DE
SC_076ED:
    LD A,(HL)
SC_076EE:
    LD ($D364),A
SC_076F1:
    INC HL
SC_076F2:
    LD A,(HL)
SC_076F3:
    LD ($D100),A
SC_076F6:
    INC HL
SC_076F7:
    LD C,(HL)
SC_076F8:
    INC HL
SC_076F9:
    LD B,(HL)
SC_076FA:
    EX DE,HL
; Index first profile by adjusted X & 31 -> D368 (vertical projection).
SC_076FB:
    LD A,($D358)
SC_076FE:
    AND $1F
SC_07700:
    LD L,A
SC_07701:
    LD H,0
SC_07703:
    ADD HL,BC
SC_07704:
    LD A,(HL)
SC_07705:
    LD ($D368),A
SC_07708:
    EX DE,HL
SC_07709:
    INC HL
SC_0770A:
    LD C,(HL)
SC_0770B:
    INC HL
SC_0770C:
    LD B,(HL)
SC_0770D:
    EX DE,HL
; Index second profile by adjusted Y & 31 -> D367 (horizontal projection).
SC_0770E:
    LD A,($D35A)
SC_07711:
    AND $1F
SC_07713:
    LD L,A
SC_07714:
    LD H,0
SC_07716:
    ADD HL,BC
SC_07717:
    LD A,(HL)
SC_07718:
    LD ($D367),A
SC_0771B:
    EX DE,HL
SC_0771C:
    INC HL
SC_0771D:
    POP AF
SC_0771E:
    LD ($D12B),A
SC_07721:
    LD ($FFFF),A
SC_07724:
    RET
; Lightweight lookup reads only base surface type; does not select the alternate header.
SC_07725:
    LD A,($D12B)
SC_07728:
    PUSH AF
SC_07729:
    LD A,14
SC_0772B:
    LD ($D12B),A
SC_0772E:
    LD ($FFFF),A
SC_07731:
    LD H,(IX+$12)
SC_07734:
    LD L,(IX+$11)
SC_07737:
    ADD HL,BC
SC_07738:
    LD ($D358),HL
SC_0773B:
    SRL H
SC_0773D:
    RR L
SC_0773F:
    SRL H
SC_07741:
    RR L
SC_07743:
    SRL H
SC_07745:
    RR L
SC_07747:
    SRL H
SC_07749:
    RR L
SC_0774B:
    SRL H
SC_0774D:
    RR L
SC_0774F:
    LD B,H
SC_07750:
    LD C,L
SC_07751:
    LD H,(IX+$15)
SC_07754:
    LD L,(IX+$14)
SC_07757:
    ADD HL,DE
SC_07758:
    LD DE,$12
SC_0775B:
    ADD HL,DE
SC_0775C:
    BIT 7,H
SC_0775E:
    JR z,SC_07763
SC_07760:
    LD HL,0
SC_07763:
    LD ($D35A),HL
SC_07766:
    SLA L
SC_07768:
    RL H
SC_0776A:
    SLA L
SC_0776C:
    RL H
SC_0776E:
    SLA L
SC_07770:
    RL H
SC_07772:
    LD A,H
SC_07773:
    ADD A,A
SC_07774:
    LD L,A
SC_07775:
    LD H,0
SC_07777:
    LD DE,($D168)
SC_0777B:
    ADD HL,DE
SC_0777C:
    LD E,(HL)
SC_0777D:
    INC HL
SC_0777E:
    LD D,(HL)
SC_0777F:
    LD L,C
SC_07780:
    LD H,B
SC_07781:
    ADD HL,DE
SC_07782:
    LD DE,$C001
SC_07785:
    ADD HL,DE
SC_07786:
    LD A,H
SC_07787:
    AND $F0
SC_07789:
    CP $C0
SC_0778B:
    JP nz,$77B0
SC_0778E:
    LD ($D354),HL
SC_07791:
    LD A,(HL)
SC_07792:
    LD ($D353),A
SC_07795:
    LD L,A
SC_07796:
    LD H,0
SC_07798:
    ADD HL,HL
SC_07799:
    LD DE,($D2E0)
SC_0779D:
    ADD HL,DE
SC_0779E:
    LD E,(HL)
SC_0779F:
    INC HL
SC_077A0:
    LD D,(HL)
SC_077A1:
    LD A,(DE)
SC_077A2:
    LD ($D364),A
SC_077A5:
    POP AF
SC_077A6:
    LD ($D12B),A
SC_077A9:
    LD ($FFFF),A
SC_077AC:
    LD A,($D364)
SC_077AF:
    RET
; Outside map: tile $FF, surface/profile values zero; D100 modifier is not cleared here.
SC_077B0:
    LD HL,$CFFF
SC_077B3:
    LD ($D354),HL
SC_077B6:
    LD A,$FF
SC_077B8:
    LD ($D353),A
SC_077BB:
    LD A,0
SC_077BD:
    LD ($D364),A
SC_077C0:
    LD A,0
SC_077C2:
    LD ($D367),A
SC_077C5:
    LD ($D368),A
SC_077C8:
    JP $77A5

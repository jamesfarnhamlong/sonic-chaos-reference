; twist_handlers: ROM $315DD..$31829 (end exclusive $3182A).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; After tile handler: angle-to-velocity conversion then position integration.
SC_315DD:
    CALL $036E
SC_315E0:
    CALL $0338
SC_315E3:
    RET
SC_315E4:
    LD (IX+10),0
SC_315E8:
    LD (IX+11),0
SC_315EC:
    LD (IX+2),9
SC_315F0:
    RET
; Original LD ($0000),A falls through. ROM write has no effect on an SMS.
SC_315F1:
    LD ($0000),A
SC_315F4:
    LD (IX+10),$40
SC_315F8:
    CALL $97B8
SC_315FB:
    RET
SC_315FC:
    CALL $9772
SC_315FF:
    LD (IX+10),$28
SC_31603:
    RET
SC_31604:
    CALL $9772
SC_31607:
    LD (IX+10),$28
SC_3160B:
    RET
SC_3160C:
    LD (IX+10),$40
SC_31610:
    RET
SC_31611:
    CALL $974D
SC_31614:
    LD (IX+10),$58
SC_31618:
    RET
SC_31619:
    CALL $974D
SC_3161C:
    LD (IX+10),$58
SC_31620:
    RET
SC_31621:
    LD (IX+10),$40
SC_31625:
    CALL $97B8
SC_31628:
    RET
SC_31629:
    LD (IX+10),$40
SC_3162D:
    CALL $97B8
SC_31630:
    RET
SC_31631:
    LD ($0000),A
SC_31634:
    LD (IX+10),$C0
SC_31638:
    CALL $979F
SC_3163B:
    RET
SC_3163C:
    LD (IX+10),$C0
SC_31640:
    CALL $97B8
SC_31643:
    RET
SC_31644:
    CALL $974D
SC_31647:
    LD (IX+10),$A8
SC_3164B:
    RET
SC_3164C:
    LD (IX+10),$C0
SC_31650:
    CALL $97B8
SC_31653:
    RET
SC_31654:
    CALL $974D
SC_31657:
    LD (IX+10),$A8
SC_3165B:
    RET
SC_3165C:
    RET
SC_3165D:
    LD (IX+10),$C0
SC_31661:
    RET
SC_31662:
    CALL $9772
SC_31665:
    LD (IX+10),$D8
SC_31669:
    RET
SC_3166A:
    CALL $9772
SC_3166D:
    LD (IX+10),$D8
SC_31671:
    RET
SC_31672:
    LD (IX+10),$C0
SC_31676:
    CALL $979F
SC_31679:
    RET
SC_3167A:
    LD (IX+10),$C0
SC_3167E:
    CALL $97B8
SC_31681:
    RET
SC_31682:
    LD (IX+10),$68
SC_31686:
    CALL $9763
SC_31689:
    RET
SC_3168A:
    LD (IX+10),$40
SC_3168E:
    CALL $97B8
SC_31691:
    CALL $9763
SC_31694:
    RET
SC_31695:
    LD (IX+10),$78
SC_31699:
    CALL $9763
SC_3169C:
    RET
SC_3169D:
    CALL $9812
SC_316A0:
    LD (IX+10),$80
SC_316A4:
    CALL $9763
SC_316A7:
    RET
SC_316A8:
    LD (IX+10),$A8
SC_316AC:
    CALL $9763
SC_316AF:
    RET
SC_316B0:
    CALL $97F0
SC_316B3:
    LD (IX+10),$80
SC_316B7:
    CALL $9763
SC_316BA:
    RET
SC_316BB:
    CALL $981D
SC_316BE:
    LD (IX+10),$80
SC_316C2:
    CALL $9763
SC_316C5:
    RET
SC_316C6:
    LD (IX+10),$70
SC_316CA:
    CALL $9763
SC_316CD:
    RET
SC_316CE:
    LD (IX+10),$50
SC_316D2:
    CALL $9763
SC_316D5:
    RET
SC_316D6:
    LD (IX+10),$60
SC_316DA:
    CALL $9763
SC_316DD:
    RET
SC_316DE:
    LD (IX+10),$C0
SC_316E2:
    CALL $97B8
SC_316E5:
    CALL $9755
SC_316E8:
    RET
SC_316E9:
    LD (IX+10),$DC
SC_316ED:
    CALL $9755
SC_316F0:
    RET
SC_316F1:
    LD (IX+10),$F0
SC_316F5:
    CALL $9755
SC_316F8:
    RET
SC_316F9:
    CALL $97F0
SC_316FC:
    CALL $981D
SC_316FF:
    LD (IX+10),0
SC_31703:
    CALL $9755
SC_31706:
    RET
SC_31707:
    LD (IX+10),$28
SC_3170B:
    CALL $9755
SC_3170E:
    RET
SC_3170F:
    LD (IX+10),4
SC_31713:
    CALL $9755
SC_31716:
    RET
SC_31717:
    LD (IX+10),0
SC_3171B:
    CALL $9755
SC_3171E:
    RET
SC_3171F:
    CALL $9812
SC_31722:
    LD (IX+10),0
SC_31726:
    CALL $9755
SC_31729:
    RET
SC_3172A:
    LD (IX+10),$E8
SC_3172E:
    CALL $9755
SC_31731:
    RET
SC_31732:
    LD (IX+10),$E0
SC_31736:
    CALL $9755
SC_31739:
    RET
SC_3173A:
    LD (IX+10),$D8
SC_3173E:
    CALL $9755
SC_31741:
    RET
SC_31742:
    LD (IX+10),$C0
SC_31746:
    CALL $97B8
SC_31749:
    CALL $9755
SC_3174C:
    RET
; RET at this address makes the following two INC instructions unreachable via this entry.
SC_3174D:
    RET
SC_3174E:
    INC (IX+11)
SC_31751:
    INC (IX+11)
SC_31754:
    RET
; Decrease magnitude by one; if below $10 select variant 2.
SC_31755:
    LD A,(IX+11)
SC_31758:
    SUB 1
SC_3175A:
    LD (IX+11),A
SC_3175D:
    CP $10
SC_3175F:
    RET nc
SC_31760:
    JP $979A
; Increase magnitude by two below $A0; preserve wrapping arithmetic.
SC_31763:
    LD A,(IX+11)
SC_31766:
    LD (IX+11),A
SC_31769:
    CP $A0
SC_3176B:
    RET nc
SC_3176C:
    ADD A,2
SC_3176E:
    LD (IX+11),A
SC_31771:
    RET
; RET at this entry: do not translate the following subtraction as active behavior.
SC_31772:
    RET
SC_31773:
    LD A,(IX+11)
SC_31776:
    SUB 2
SC_31778:
    LD (IX+11),A
SC_3177B:
    CP $50
SC_3177D:
    RET nc
SC_3177E:
    XOR A
SC_3177F:
    LD (IX+$18),A
SC_31782:
    LD (IX+$19),A
SC_31785:
    LD (IX+10),A
SC_31788:
    LD (IX+11),A
SC_3178B:
    RES 1,(IX+$22)
SC_3178F:
    SET 0,(IX+3)
SC_31793:
    LD (IX+2),10
SC_31797:
    POP HL
SC_31798:
    POP HL
SC_31799:
    RET
SC_3179A:
    LD (IX+$38),2
SC_3179E:
    RET
; Y alignment using (Y-16)&~31, then +46.
SC_3179F:
    LD L,(IX+$14)
SC_317A2:
    LD H,(IX+$15)
SC_317A5:
    LD DE,$FFF0
SC_317A8:
    ADD HL,DE
SC_317A9:
    LD A,L
SC_317AA:
    AND $E0
SC_317AC:
    LD L,A
SC_317AD:
    LD DE,$2E
SC_317B0:
    ADD HL,DE
SC_317B1:
    LD (IX+$14),L
SC_317B4:
    LD (IX+$15),H
SC_317B7:
    RET
; Sonic Y alignment: ((Y-32)&~31)+46; alternate character branch differs.
SC_317B8:
    LD A,(IX+0)
SC_317BB:
    DEC A
SC_317BC:
    JR nz,SC_317D7
SC_317BE:
    LD L,(IX+$14)
SC_317C1:
    LD H,(IX+$15)
SC_317C4:
    LD DE,$FFE0
SC_317C7:
    ADD HL,DE
SC_317C8:
    LD A,L
SC_317C9:
    AND $E0
SC_317CB:
    LD L,A
SC_317CC:
    LD DE,$2E
SC_317CF:
    ADD HL,DE
SC_317D0:
    LD (IX+$14),L
SC_317D3:
    LD (IX+$15),H
SC_317D6:
    RET
SC_317D7:
    LD L,(IX+$14)
SC_317DA:
    LD H,(IX+$15)
SC_317DD:
    LD DE,$FFD9
SC_317E0:
    ADD HL,DE
SC_317E1:
    LD A,L
SC_317E2:
    AND $E0
SC_317E4:
    LD L,A
SC_317E5:
    LD DE,$30
SC_317E8:
    ADD HL,DE
SC_317E9:
    LD (IX+$14),L
SC_317EC:
    LD (IX+$15),H
SC_317EF:
    RET
SC_317F0:
    LD L,(IX+$11)
SC_317F3:
    LD H,(IX+$12)
SC_317F6:
    LD DE,6
SC_317F9:
    ADD HL,DE
SC_317FA:
    LD A,L
SC_317FB:
    AND $E0
SC_317FD:
    LD L,A
SC_317FE:
    LD DE,10
SC_31801:
    LD A,(IX+0)
SC_31804:
    DEC A
SC_31805:
    JR z,SC_3180A
SC_31807:
    LD DE,14
SC_3180A:
    ADD HL,DE
SC_3180B:
    LD (IX+$11),L
SC_3180E:
    LD (IX+$12),H
SC_31811:
    RET
; X low-byte alignment to tile boundary +22; high byte is preserved.
SC_31812:
    LD A,(IX+$11)
SC_31815:
    AND $E0
SC_31817:
    ADD A,$16
SC_31819:
    LD (IX+$11),A
SC_3181C:
    RET
SC_3181D:
    LD A,(IX+$11)
SC_31820:
    ADD A,$10
SC_31822:
    AND $E0
SC_31824:
    ADD A,4
SC_31826:
    LD (IX+$11),A
SC_31829:
    RET

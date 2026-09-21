; Recovered original Z80 code, file $78577..$78946.
; Numeric object fields are offsets from IX. No behavior changes intended.
; Branch labels preserve original addresses; build_check.py verifies every ROM byte.


CR_Platform_ClearDeltas:
CR_78577:
    XOR A
CR_78578:
    LD (IX+$39),A
CR_7857B:
    LD (IX+$38),A
CR_7857E:
    LD (IX+$24),A
CR_78581:
    LD (IX+$23),A
CR_78584:
    RET

CR_Platform_Initialize:
; Subtype comes from record byte 6 at object+$3F. Initial state=(subtype & $3F)+1.
CR_78585:
    SET 7,(IX+3)
CR_78589:
    LD (IX+$25),0
CR_7858D:
    LD A,(IX+$3F)
CR_78590:
    BIT 7,A
CR_78592:
    JR z,CR_78598
CR_78594:
    LD (IX+$25),$FF
CR_78598:
    LD (IX+$26),0
CR_7859C:
    BIT 6,A
CR_7859E:
    JR z,CR_785A4
CR_785A0:
    LD (IX+$26),$FF
CR_785A4:
    AND $3F
CR_785A6:
    INC A
CR_785A7:
    LD (IX+2),A
CR_785AA:
    LD (IX+$36),A
CR_785AD:
    LD A,(IX+$3F)
CR_785B0:
    AND $7F
CR_785B2:
    CP 11
CR_785B4:
    JR z,CR_785BC
CR_785B6:
    CP 5
CR_785B8:
    JR z,CR_785BC
CR_785BA:
    JR CR_785C0
CR_785BC:
    LD (IX+2),13
CR_785C0:
    LD A,(IX+9)
CR_785C3:
    LD (IX+$34),A
CR_785C6:
    LD (IX+$37),A
CR_785C9:
    LD (IX+$30),$10
CR_785CD:
    XOR A
CR_785CE:
    LD (IX+$35),A
CR_785D1:
    LD (IX+$39),A
CR_785D4:
    LD (IX+$38),A
CR_785D7:
    LD (IX+$24),A
CR_785DA:
    LD (IX+$23),A
CR_785DD:
    LD (IX+$1F),A
CR_785E0:
    LD (IX+$27),A
CR_785E3:
    LD (IX+$1E),A
CR_785E6:
    LD (IX+$31),A
CR_785E9:
    LD (IX+$33),A
CR_785EC:
    LD (IX+10),$C0
CR_785F0:
    LD (IX+11),2
CR_785F4:
    PUSH IX
CR_785F6:
    POP HL
CR_785F7:
    CALL $0332
CR_785FA:
    LD (IX+$32),A
CR_785FD:
    RET

CR_Platform_WaitForRider:
CR_785FE:
    BIT 6,(IX+4)
CR_78602:
    RET nz
CR_78603:
    LD A,($D519)
CR_78606:
    RLCA
CR_78607:
    RET c
CR_78608:
    CALL $033B
CR_7860B:
    LD A,(IX+$21)
CR_7860E:
    BIT 0,A
CR_78610:
    RET z
CR_78611:
    LD A,(IX+$36)
CR_78614:
    LD (IX+2),A
CR_78617:
    LD A,($D297)
CR_7861A:
    CP 4
CR_7861C:
    RET nz
CR_7861D:
    LD A,($D298)
CR_78620:
    CP 1
CR_78622:
    RET nz
CR_78623:
    LD (IX+2),14
CR_78627:
    RET

CR_Platform_HorizontalUpdate:
CR_78628:
    BIT 6,(IX+4)
CR_7862C:
    JR z,CR_78631
CR_7862E:
    CALL $0338
CR_78631:
    LD A,($D519)
CR_78634:
    BIT 7,A
CR_78636:
    JR z,CR_78644
CR_78638:
    LD (IX+$21),0
CR_7863C:
    CALL $0338
CR_7863F:
    CALL $8843
CR_78642:
    JR CR_78661
CR_78644:
    LD D,(IX+$12)
CR_78647:
    LD E,(IX+$11)
CR_7864A:
    PUSH DE
CR_7864B:
    CALL $0338
CR_7864E:
    POP DE
CR_7864F:
    LD H,(IX+$12)
CR_78652:
    LD L,(IX+$11)
CR_78655:
    XOR A
CR_78656:
    SBC HL,DE
CR_78658:
    LD (IX+$24),H
CR_7865B:
    LD (IX+$23),L
CR_7865E:
    CALL $8814
CR_78661:
    RET

CR_Platform_HorizontalTimedUpdate:
CR_78662:
    CALL $8908
CR_78665:
    LD A,($D519)
CR_78668:
    BIT 7,A
CR_7866A:
    JR z,CR_78678
CR_7866C:
    LD (IX+$21),0
CR_78670:
    CALL $0338
CR_78673:
    CALL $8843
CR_78676:
    JR CR_78695
CR_78678:
    LD D,(IX+$12)
CR_7867B:
    LD E,(IX+$11)
CR_7867E:
    PUSH DE
CR_7867F:
    CALL $0338
CR_78682:
    POP DE
CR_78683:
    LD H,(IX+$12)
CR_78686:
    LD L,(IX+$11)
CR_78689:
    XOR A
CR_7868A:
    SBC HL,DE
CR_7868C:
    LD (IX+$24),H
CR_7868F:
    LD (IX+$23),L
CR_78692:
    CALL $8814
CR_78695:
    LD B,$10
CR_78697:
    CALL $8925
CR_7869A:
    CP 0
CR_7869C:
    RET z
CR_7869D:
    CALL $0437
CR_786A0:
    RET

CR_Platform_VerticalUpdate:
CR_786A1:
    BIT 6,(IX+4)
CR_786A5:
    JR z,CR_786AA
CR_786A7:
    CALL $0338
CR_786AA:
    CALL $8866
CR_786AD:
    OR A
CR_786AE:
    JR z,CR_786BC
CR_786B0:
    LD (IX+$21),0
CR_786B4:
    CALL $0338
CR_786B7:
    CALL $8843
CR_786BA:
    JR CR_786D9
CR_786BC:
    LD D,(IX+$15)
CR_786BF:
    LD E,(IX+$14)
CR_786C2:
    PUSH DE
CR_786C3:
    CALL $0338
CR_786C6:
    POP DE
CR_786C7:
    LD H,(IX+$15)
CR_786CA:
    LD L,(IX+$14)
CR_786CD:
    XOR A
CR_786CE:
    SBC HL,DE
CR_786D0:
    LD (IX+$39),H
CR_786D3:
    LD (IX+$38),L
CR_786D6:
    CALL $8814
CR_786D9:
    RET

CR_Platform_VerticalTimedUpdate:
; THZ lift subtype $0A selects this state. Integrate velocity; carry/detach player; reverse every 16*aux1 updates.
CR_786DA:
    CALL $8908
CR_786DD:
    CALL $8866
CR_786E0:
    OR A
CR_786E1:
    JR z,CR_786EF
CR_786E3:
    LD (IX+$21),0
CR_786E7:
    CALL $0338
CR_786EA:
    CALL $8843
CR_786ED:
    JR CR_7870C
CR_786EF:
    LD D,(IX+$15)
CR_786F2:
    LD E,(IX+$14)
CR_786F5:
    PUSH DE
CR_786F6:
    CALL $0338
CR_786F9:
    POP DE
CR_786FA:
    LD H,(IX+$15)
CR_786FD:
    LD L,(IX+$14)
CR_78700:
    XOR A
CR_78701:
    SBC HL,DE
CR_78703:
    LD (IX+$39),H
CR_78706:
    LD (IX+$38),L
CR_78709:
    CALL $8814
CR_7870C:
    LD B,$10
CR_7870E:
    CALL $8925
CR_78711:
    CP 0
CR_78713:
    RET z
CR_78714:
    CALL $80F1
CR_78717:
    RET
CR_78718:
    RET
CR_78719:
    BIT 6,(IX+4)
CR_7871D:
    JR nz,CR_78788
CR_7871F:
    LD A,(IX+$27)
CR_78722:
    CP $FF
CR_78724:
    JR z,CR_7873D
CR_78726:
    CP 0
CR_78728:
    JR z,CR_78767
CR_7872A:
    LD A,(IX+$1E)
CR_7872D:
    OR A
CR_7872E:
    JR z,CR_78737
CR_78730:
    SUB 1
CR_78732:
    LD (IX+$1E),A
CR_78735:
    JR CR_78767
CR_78737:
    LD (IX+$27),$FF
CR_7873B:
    JR CR_78767
CR_7873D:
    LD H,(IX+$19)
CR_78740:
    LD L,(IX+$18)
CR_78743:
    LD DE,$30
CR_78746:
    ADD HL,DE
CR_78747:
    LD (IX+$19),H
CR_7874A:
    LD (IX+$18),L
CR_7874D:
    LD D,(IX+$15)
CR_78750:
    LD E,(IX+$14)
CR_78753:
    PUSH DE
CR_78754:
    CALL $0338
CR_78757:
    POP DE
CR_78758:
    LD H,(IX+$15)
CR_7875B:
    LD L,(IX+$14)
CR_7875E:
    XOR A
CR_7875F:
    SBC HL,DE
CR_78761:
    LD (IX+$39),H
CR_78764:
    LD (IX+$38),L
CR_78767:
    LD A,($D519)
CR_7876A:
    BIT 7,A
CR_7876C:
    JR z,CR_78775
CR_7876E:
    LD (IX+$21),0
CR_78772:
    JP $8843
CR_78775:
    CALL $8814
CR_78778:
    LD A,(IX+$27)
CR_7877B:
    OR A
CR_7877C:
    RET nz
CR_7877D:
    LD A,(IX+$21)
CR_78780:
    BIT 0,A
CR_78782:
    RET z
CR_78783:
    LD (IX+$27),$80
CR_78787:
    RET
CR_78788:
    LD A,(IX+$27)
CR_7878B:
    OR A
CR_7878C:
    RET z
CR_7878D:
    LD (IX+$3F),$80
CR_78791:
    LD (IX+$3E),0
CR_78795:
    LD (IX+0),$FE
CR_78799:
    RET

CR_Platform_StationaryUpdate:
CR_7879A:
    BIT 6,(IX+4)
CR_7879E:
    RET nz
CR_7879F:
    CALL $8866
CR_787A2:
    OR A
CR_787A3:
    JR z,CR_787AE
CR_787A5:
    LD (IX+$21),0
CR_787A9:
    CALL $8843
CR_787AC:
    JR CR_787B1
CR_787AE:
    CALL $8814
CR_787B1:
    RET
CR_787B2:
    CALL $8908
CR_787B5:
    LD A,(IX+$31)
CR_787B8:
    CP 0
CR_787BA:
    JR nz,CR_787C9
CR_787BC:
    CALL $033B
CR_787BF:
    LD A,(IX+$21)
CR_787C2:
    AND 15
CR_787C4:
    RET z
CR_787C5:
    LD (IX+$31),1
CR_787C9:
    CALL $86DA
CR_787CC:
    BIT 7,(IX+$19)
CR_787D0:
    JR z,CR_787DD
CR_787D2:
    LD A,(IX+$31)
CR_787D5:
    CP 1
CR_787D7:
    RET z
CR_787D8:
    LD (IX+$31),0
CR_787DC:
    RET
CR_787DD:
    LD (IX+$31),2
CR_787E1:
    RET
CR_787E2:
    CALL $8908
CR_787E5:
    LD A,(IX+$31)
CR_787E8:
    CP 0
CR_787EA:
    JR nz,CR_787F9
CR_787EC:
    CALL $033B
CR_787EF:
    LD A,(IX+$21)
CR_787F2:
    AND 15
CR_787F4:
    RET z
CR_787F5:
    LD (IX+$31),1
CR_787F9:
    CALL $8662
CR_787FC:
    BIT 7,(IX+$17)
CR_78800:
    JR nz,CR_7880D
CR_78802:
    LD A,(IX+$31)
CR_78805:
    CP 1
CR_78807:
    RET z
CR_78808:
    LD (IX+$31),0
CR_7880C:
    RET
CR_7880D:
    LD (IX+$31),2
CR_78811:
    RET
CR_78812:
    RET
CR_78813:
    RET

CR_Platform_CheckRider:
CR_78814:
    LD A,($D3C0)
CR_78817:
    LD C,A
CR_78818:
    OR A
CR_78819:
    JR z,CR_78822
CR_7881B:
    LD B,(IX+$32)
CR_7881E:
    LD A,C
CR_7881F:
    CP B
CR_78820:
    JR nz,CR_78843
CR_78822:
    CALL $033B
CR_78825:
    LD A,(IX+$21)
CR_78828:
    BIT 0,A
CR_7882A:
    JP z,$8843
CR_7882D:
    LD B,(IX+$32)
CR_78830:
    LD A,($D3C0)
CR_78833:
    OR A
CR_78834:
    JR z,CR_78838
CR_78836:
    CP B
CR_78837:
    RET nz
CR_78838:
    LD A,B
CR_78839:
    LD ($D3C0),A
CR_7883C:
    CALL $88FB
CR_7883F:
    CALL $88A0
CR_78842:
    RET

CR_Platform_DetachRider:
CR_78843:
    LD (IX+$33),0
CR_78847:
    LD A,(IX+$21)
CR_7884A:
    AND 12
CR_7884C:
    JR z,CR_78856
CR_7884E:
    LD A,($D521)
CR_78851:
    AND $33
CR_78853:
    LD ($D521),A
CR_78856:
    CALL $88E1
CR_78859:
    LD A,($D3C0)
CR_7885C:
    LD B,(IX+$32)
CR_7885F:
    CP B
CR_78860:
    RET nz
CR_78861:
    XOR A
CR_78862:
    LD ($D3C0),A
CR_78865:
    RET

CR_Platform_CheckRelativeVerticalSpeed:
CR_78866:
    LD H,(IX+$19)
CR_78869:
    LD L,(IX+$18)
CR_7886C:
    LD DE,($D518)
CR_78870:
    LD A,H
CR_78871:
    AND D
CR_78872:
    BIT 7,A
CR_78874:
    JR z,CR_7888B
CR_78876:
    DEC HL
CR_78877:
    LD A,H
CR_78878:
    CPL
CR_78879:
    LD H,A
CR_7887A:
    LD A,L
CR_7887B:
    CPL
CR_7887C:
    LD L,A
CR_7887D:
    DEC DE
CR_7887E:
    LD A,D
CR_7887F:
    CPL
CR_78880:
    LD D,A
CR_78881:
    LD A,E
CR_78882:
    CPL
CR_78883:
    LD E,A
CR_78884:
    LD A,$FF
CR_78886:
    LD ($D4A5),A
CR_78889:
    JR CR_78891
CR_7888B:
    LD A,H
CR_7888C:
    XOR D
CR_7888D:
    BIT 7,A
CR_7888F:
    JR z,CR_78898
CR_78891:
    XOR A
CR_78892:
    SBC HL,DE
CR_78894:
    RET nc
CR_78895:
    LD A,$FF
CR_78897:
    RET
CR_78898:
    XOR A
CR_78899:
    SBC HL,DE
CR_7889B:
    RET z
CR_7889C:
    RET c
CR_7889D:
    LD A,$FF
CR_7889F:
    RET

CR_Platform_CarryRider:
; Place player on platform top; add platform horizontal delta to player X.
CR_788A0:
    LD H,(IX+$15)
CR_788A3:
    LD L,(IX+$14)
CR_788A6:
    LD D,0
CR_788A8:
    LD E,(IX+$2D)
CR_788AB:
    DEC E
CR_788AC:
    DEC E
CR_788AD:
    XOR A
CR_788AE:
    SBC HL,DE
CR_788B0:
    LD ($D514),HL
CR_788B3:
    LD HL,($D511)
CR_788B6:
    LD D,(IX+$24)
CR_788B9:
    LD E,(IX+$23)
CR_788BC:
    ADD HL,DE
CR_788BD:
    LD ($D511),HL
CR_788C0:
    RET
CR_788C1:
    LD A,(IX+$35)
CR_788C4:
    CP 8
CR_788C6:
    JR z,CR_788DC
CR_788C8:
    INC (IX+$35)
CR_788CB:
    LD H,(IX+$15)
CR_788CE:
    LD L,(IX+$14)
CR_788D1:
    LD DE,1
CR_788D4:
    ADD HL,DE
CR_788D5:
    LD (IX+$15),H
CR_788D8:
    LD (IX+$14),L
CR_788DB:
    RET
CR_788DC:
    LD (IX+$33),$FF
CR_788E0:
    RET
CR_788E1:
    LD A,(IX+$35)
CR_788E4:
    CP 0
CR_788E6:
    RET z
CR_788E7:
    DEC (IX+$35)
CR_788EA:
    LD H,(IX+$15)
CR_788ED:
    LD L,(IX+$14)
CR_788F0:
    LD DE,$FFFF
CR_788F3:
    ADD HL,DE
CR_788F4:
    LD (IX+$15),H
CR_788F7:
    LD (IX+$14),L
CR_788FA:
    RET

CR_Platform_SagIfEnabled:
CR_788FB:
    BIT 7,(IX+$25)
CR_788FF:
    RET z
CR_78900:
    LD A,(IX+$33)
CR_78903:
    OR A
CR_78904:
    JR z,CR_788C1
CR_78906:
    JR CR_788E1

CR_Platform_CheckVisibility:
CR_78908:
    BIT 1,(IX+4)
CR_7890C:
    RET z
CR_7890D:
    LD BC,$280
CR_78910:
    CALL $0383
CR_78913:
    OR A
CR_78914:
    JR z,CR_78920
CR_78916:
    LD BC,$2A0
CR_78919:
    CALL $0386
CR_7891C:
    OR A
CR_7891D:
    JR z,CR_78920
CR_7891F:
    RET
CR_78920:
    LD (IX+0),$FE
CR_78924:
    RET

CR_Platform_TickTravelCounter:
; Counter +$30 counts 16 updates; +$37 counts groups and reloads from +$34 (record byte 8).
CR_78925:
    LD A,(IX+$30)
CR_78928:
    DEC A
CR_78929:
    JR z,CR_78930
CR_7892B:
    LD (IX+$30),A
CR_7892E:
    XOR A
CR_7892F:
    RET
CR_78930:
    LD (IX+$30),B
CR_78933:
    LD A,(IX+$37)
CR_78936:
    DEC A
CR_78937:
    JR z,CR_7893E
CR_78939:
    LD (IX+$37),A
CR_7893C:
    XOR A
CR_7893D:
    RET
CR_7893E:
    LD A,(IX+$34)
CR_78941:
    LD (IX+$37),A
CR_78944:
    LD A,$FF
CR_78946:
    RET

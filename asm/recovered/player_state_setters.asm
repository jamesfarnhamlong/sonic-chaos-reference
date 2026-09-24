; player_state_setters: ROM $045ED..$047A8 (end exclusive $047A9).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Normal jump requests state $0A and Y=-4.25 (dry) or -3.25 (water).
SC_045ED:
    BIT 0,(IX+3)
SC_045F1:
    RET nz
SC_045F2:
    LD A,($D501)
SC_045F5:
    CP $11
SC_045F7:
    RET z
SC_045F8:
    LD A,($D36B)
SC_045FB:
    AND $FC
SC_045FD:
    CP $90
SC_045FF:
    RET z
SC_04600:
    XOR A
SC_04601:
    LD ($D3B2),A
SC_04604:
    LD ($D3BC),A
SC_04607:
    SET 0,(IX+3)
SC_0460B:
    SET 1,(IX+3)
SC_0460F:
    RES 0,(IX+$24)
SC_04613:
    LD (IX+2),10
SC_04617:
    LD HL,$FBC0
SC_0461A:
    LD A,($D443)
SC_0461D:
    OR A
SC_0461E:
    JR z,SC_04623
SC_04620:
    LD HL,$FCC0
SC_04623:
    LD ($D518),HL
SC_04626:
    LD HL,($D514)
SC_04629:
    DEC HL
SC_0462A:
    LD ($D514),HL
SC_0462D:
    LD A,$60
SC_0462F:
    LD ($D289),A
SC_04632:
    RES 1,(IX+$22)
SC_04636:
    LD A,$A2
SC_04638:
    LD ($DE04),A
SC_0463B:
    RET
; Falling setter requests state $0E and sets Y velocity to +1.0; normal-jump state is exempt.
SC_0463C:
    LD A,(IX+1)
SC_0463F:
    CP 10
SC_04641:
    RET z
SC_04642:
    LD (IX+2),14
SC_04646:
    LD (IX+$18),0
SC_0464A:
    LD (IX+$19),1
SC_0464E:
    SET 0,(IX+3)
SC_04652:
    RES 1,(IX+3)
SC_04656:
    RES 0,(IX+$24)
SC_0465A:
    XOR A
SC_0465B:
    LD ($D3BC),A
SC_0465E:
    RES 1,(IX+$22)
SC_04662:
    RET
SC_04663:
    LD (IX+2),$14
SC_04667:
    LD (IX+$18),0
SC_0466B:
    LD (IX+$19),1
SC_0466F:
    SET 0,(IX+3)
SC_04673:
    RES 1,(IX+3)
SC_04677:
    RES 1,(IX+$22)
SC_0467B:
    XOR A
SC_0467C:
    LD ($D3BC),A
SC_0467F:
    RET
SC_04680:
    LD (IX+2),$1D
SC_04684:
    LD (IX+$18),$80
SC_04688:
    LD (IX+$19),0
SC_0468C:
    SET 0,(IX+3)
SC_04690:
    RES 1,(IX+3)
SC_04694:
    RES 1,(IX+$22)
SC_04698:
    RET
SC_04699:
    SET 0,(IX+3)
SC_0469D:
    SET 1,(IX+3)
SC_046A1:
    LD (IX+2),10
SC_046A5:
    LD HL,0
SC_046A8:
    LD ($D518),HL
SC_046AB:
    RES 1,(IX+$22)
SC_046AF:
    RET
SC_046B0:
    LD HL,0
SC_046B3:
    LD ($D516),HL
SC_046B6:
    LD (IX+2),3
SC_046BA:
    RET
SC_046BB:
    LD HL,0
SC_046BE:
    LD ($D516),HL
SC_046C1:
    RES 1,(IX+3)
SC_046C5:
    RES 6,(IX+3)
SC_046C9:
    LD (IX+2),4
SC_046CD:
    RET
SC_046CE:
    LD HL,0
SC_046D1:
    LD ($D516),HL
SC_046D4:
    RES 6,(IX+3)
SC_046D8:
    LD (IX+2),$15
SC_046DC:
    LD A,$AC
SC_046DE:
    LD ($DE04),A
SC_046E1:
    RET
SC_046E2:
    LD HL,$700
SC_046E5:
    LD ($D373),HL
SC_046E8:
    BIT 4,(IX+4)
SC_046EC:
    JR z,SC_046F1
SC_046EE:
    LD HL,$F900
SC_046F1:
    LD (IX+$16),L
SC_046F4:
    LD (IX+$17),H
SC_046F7:
    LD (IX+2),$1A
SC_046FB:
    LD A,$BE
SC_046FD:
    LD ($DE04),A
SC_04700:
    RET
SC_04701:
    LD HL,0
SC_04704:
    LD ($D516),HL
SC_04707:
    SET 1,(IX+3)
SC_0470B:
    RES 6,(IX+3)
SC_0470F:
    LD (IX+2),15
SC_04713:
    LD A,$AC
SC_04715:
    LD ($DE04),A
SC_04718:
    RET
SC_04719:
    LD HL,$700
SC_0471C:
    LD ($D373),HL
SC_0471F:
    BIT 4,(IX+4)
SC_04723:
    JR z,SC_04728
SC_04725:
    LD HL,$F900
SC_04728:
    LD (IX+$16),L
SC_0472B:
    LD (IX+$17),H
SC_0472E:
    SET 1,(IX+3)
SC_04732:
    LD (IX+2),$10
SC_04736:
    LD A,$BE
SC_04738:
    LD ($DE04),A
SC_0473B:
    RET
SC_0473C:
    LD HL,0
SC_0473F:
    LD ($D516),HL
SC_04742:
    LD HL,$FF00
SC_04745:
    LD ($D518),HL
SC_04748:
    LD HL,($D514)
SC_0474B:
    DEC HL
SC_0474C:
    DEC HL
SC_0474D:
    DEC HL
SC_0474E:
    DEC HL
SC_0474F:
    LD ($D514),HL
SC_04752:
    LD HL,$12C
SC_04755:
    LD ($D3A1),HL
SC_04758:
    RES 1,(IX+3)
SC_0475C:
    RES 6,(IX+3)
SC_04760:
    RES 1,(IX+$22)
SC_04764:
    RES 1,(IX+$21)
SC_04768:
    RES 1,(IX+$23)
SC_0476C:
    XOR A
SC_0476D:
    LD ($D3C0),A
SC_04770:
    LD (IX+2),$18
SC_04774:
    RET
; Numeric reward bit 3 player setup: zero velocity, set max X to 7, request sound $85 and state $11.
SC_04775:
    LD HL,0
SC_04778:
    LD ($D516),HL
SC_0477B:
    LD ($D518),HL
SC_0477E:
    LD HL,$700
SC_04781:
    LD ($D373),HL
SC_04784:
    LD HL,$1770
SC_04787:
    LD A,($D297)
SC_0478A:
    CP 8
SC_0478C:
    JR z,SC_04799
SC_0478E:
    LD A,$85
SC_04790:
    LD ($DE04),A
SC_04793:
    CALL $062D
SC_04796:
    LD HL,$12C
SC_04799:
    LD ($D3A1),HL
SC_0479C:
    RES 1,(IX+3)
SC_047A0:
    RES 6,(IX+3)
SC_047A4:
    LD (IX+2),$11
SC_047A8:
    RET

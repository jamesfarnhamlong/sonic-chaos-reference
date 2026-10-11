; gameplay_frame_update: ROM $016B8..$01752 (end exclusive $01753).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Gameplay frame update, $D131 = 0 variant: camera update $4C90, player update $361D, object scheduler $5DD1, $7AC2, then once the counter $D2E2 reaches 4 it is cleared, bank $1C is mapped and $8000 is called. $D2E2 is incremented on every exit.
SC_016B8:
    LD A,($D131)
SC_016BB:
    OR A
SC_016BC:
    JP nz,$16EF
SC_016BF:
    LD IX,$D15E
SC_016C3:
    BIT 6,(IX+0)
SC_016C7:
    JP nz,$16EA
SC_016CA:
    CALL $4C90
SC_016CD:
    CALL $361D
SC_016D0:
    CALL $5DD1
SC_016D3:
    CALL $7AC2
SC_016D6:
    LD A,($D2E2)
SC_016D9:
    CP 4
SC_016DB:
    JP c,$16EA
SC_016DE:
    XOR A
SC_016DF:
    LD ($D2E2),A
SC_016E2:
    LD A,$1C
SC_016E4:
    CALL $1C6F
SC_016E7:
    CALL $8000
SC_016EA:
    LD HL,$D2E2
SC_016ED:
    INC (HL)
SC_016EE:
    RET
; Gameplay frame update, $D131 nonzero variant: the same sequence with $D44F set to $FF around the player update and around the extra calls $220E and $1027 (bank 15 mapped for them).
SC_016EF:
    LD IX,$D15E
SC_016F3:
    BIT 6,(IX+0)
SC_016F7:
    JP nz,$173A
SC_016FA:
    CALL $4C90
SC_016FD:
    LD A,$FF
SC_016FF:
    LD ($D44F),A
SC_01702:
    CALL $361D
SC_01705:
    XOR A
SC_01706:
    LD ($D44F),A
SC_01709:
    CALL $5DD1
SC_0170C:
    LD A,$FF
SC_0170E:
    LD ($D44F),A
SC_01711:
    LD A,15
SC_01713:
    LD ($D12B),A
SC_01716:
    LD ($FFFF),A
SC_01719:
    CALL $220E
SC_0171C:
    CALL $1027
SC_0171F:
    XOR A
SC_01720:
    LD ($D44F),A
SC_01723:
    CALL $7AC2
SC_01726:
    LD A,($D2E2)
SC_01729:
    CP 4
SC_0172B:
    JP c,$173A
SC_0172E:
    XOR A
SC_0172F:
    LD ($D2E2),A
SC_01732:
    LD A,$1C
SC_01734:
    CALL $1C6F
SC_01737:
    CALL $8000
SC_0173A:
    LD HL,$D2E2
SC_0173D:
    INC (HL)
SC_0173E:
    RET
; When $D12E is nonzero: clear it, store $80 in $DE08 and set $D293 bit 0.
SC_0173F:
    LD A,($D12E)
SC_01742:
    OR A
SC_01743:
    RET z
SC_01744:
    XOR A
SC_01745:
    LD ($D12E),A
SC_01748:
    LD A,$80
SC_0174A:
    LD ($DE08),A
SC_0174D:
    LD HL,$D293
SC_01750:
    SET 0,(HL)
SC_01752:
    RET

; player_state_11_handler: ROM $03A7C..$03B4D (end exclusive $03B4E).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Player state $11 callback: directional acceleration, vertical wrap/clamp, damage check, shared movement/collision, and timer-expiry exit.
SC_03A7C:
    RES 7,(IX+4)
SC_03A80:
    CALL $3AC1
SC_03A83:
    CALL $3B25
SC_03A86:
    CALL $48A7
SC_03A89:
    LD B,4
SC_03A8B:
    BIT 4,(IX+4)
SC_03A8F:
    JR nz,SC_03A93
SC_03A91:
    LD B,8
SC_03A93:
    LD A,($D137)
SC_03A96:
    OR B
SC_03A97:
    LD ($D137),A
SC_03A9A:
    CALL $3FEF
SC_03A9D:
    BIT 1,(IX+$23)
SC_03AA1:
    JR z,SC_03AB5
SC_03AA3:
    RES 1,(IX+$22)
SC_03AA7:
    LD HL,($D514)
SC_03AAA:
    DEC HL
SC_03AAB:
    DEC HL
SC_03AAC:
    LD ($D514),HL
SC_03AAF:
    LD HL,0
SC_03AB2:
    LD ($D518),HL
SC_03AB5:
    LD HL,($D44C)
SC_03AB8:
    LD A,H
SC_03AB9:
    OR L
SC_03ABA:
    RET nz
SC_03ABB:
    CALL $189B
SC_03ABE:
    JP $463C
SC_03AC1:
    LD A,($D137)
SC_03AC4:
    BIT 0,A
SC_03AC6:
    JR nz,SC_03AE5
SC_03AC8:
    BIT 1,A
SC_03ACA:
    JR nz,SC_03B05
SC_03ACC:
    LD L,(IX+$18)
SC_03ACF:
    LD H,(IX+$19)
SC_03AD2:
    LD DE,$FFE0
SC_03AD5:
    LD A,H
SC_03AD6:
    AND A
SC_03AD7:
    JP p,$3ADD
SC_03ADA:
    LD DE,$20
SC_03ADD:
    ADD HL,DE
SC_03ADE:
    LD (IX+$18),L
SC_03AE1:
    LD (IX+$19),H
SC_03AE4:
    RET
SC_03AE5:
    LD DE,$FFC0
SC_03AE8:
    LD L,(IX+$18)
SC_03AEB:
    LD H,(IX+$19)
SC_03AEE:
    ADD HL,DE
SC_03AEF:
    LD (IX+$18),L
SC_03AF2:
    LD (IX+$19),H
SC_03AF5:
    LD A,H
SC_03AF6:
    AND A
SC_03AF7:
    RET p
SC_03AF8:
    CP $FD
SC_03AFA:
    RET nc
SC_03AFB:
    LD HL,$FC00
SC_03AFE:
    LD (IX+$18),L
SC_03B01:
    LD (IX+$19),H
SC_03B04:
    RET
SC_03B05:
    LD DE,$40
SC_03B08:
    LD L,(IX+$18)
SC_03B0B:
    LD H,(IX+$19)
SC_03B0E:
    ADD HL,DE
SC_03B0F:
    LD (IX+$18),L
SC_03B12:
    LD (IX+$19),H
SC_03B15:
    LD A,H
SC_03B16:
    AND A
SC_03B17:
    RET m
SC_03B18:
    CP 3
SC_03B1A:
    RET c
SC_03B1B:
    LD HL,$400
SC_03B1E:
    LD (IX+$18),L
SC_03B21:
    LD (IX+$19),H
SC_03B24:
    RET
SC_03B25:
    LD HL,($D51C)
SC_03B28:
    LD BC,$18
SC_03B2B:
    LD DE,$19
SC_03B2E:
    XOR A
SC_03B2F:
    SBC HL,BC
SC_03B31:
    JR c,SC_03B40
SC_03B33:
    LD HL,($D51C)
SC_03B36:
    LD BC,$C0
SC_03B39:
    LD DE,$BF
SC_03B3C:
    XOR A
SC_03B3D:
    SBC HL,BC
SC_03B3F:
    RET c
SC_03B40:
    LD HL,($D176)
SC_03B43:
    ADD HL,DE
SC_03B44:
    LD ($D514),HL
SC_03B47:
    LD HL,0
SC_03B4A:
    LD ($D518),HL
SC_03B4D:
    RET

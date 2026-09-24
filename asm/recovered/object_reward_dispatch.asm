; object_reward_dispatch: ROM $04AA3..$04B45 (end exclusive $04B46).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Dispatch the lowest queued numeric reward bit in $D3A3.
SC_04AA3:
    LD HL,$D3A3
SC_04AA6:
    LD A,(HL)
SC_04AA7:
    BIT 0,A
SC_04AA9:
    JR nz,SC_04AC0
SC_04AAB:
    BIT 1,A
SC_04AAD:
    JR nz,SC_04ADA
SC_04AAF:
    BIT 2,A
SC_04AB1:
    JR nz,SC_04B0F
SC_04AB3:
    BIT 3,A
SC_04AB5:
    JR nz,SC_04ADF
SC_04AB7:
    BIT 4,A
SC_04AB9:
    JR nz,SC_04B02
SC_04ABB:
    BIT 5,A
SC_04ABD:
    JR nz,SC_04B1D
SC_04ABF:
    RET
SC_04AC0:
    RES 0,(HL)
SC_04AC2:
    LD A,($D29A)
SC_04AC5:
    ADD A,$10
SC_04AC7:
    DAA
SC_04AC8:
    LD ($D29A),A
SC_04ACB:
    CALL $314A
SC_04ACE:
    LD A,($D29A)
SC_04AD1:
    CP $10
SC_04AD3:
    RET nc
SC_04AD4:
    CALL $3104
SC_04AD7:
    JP $178F
; Reward bit 1: clear the bit and increment the BCD byte at $D299.
SC_04ADA:
    RES 1,(HL)
SC_04ADC:
    JP $3104
; Reward bit 3 for player type 1: set $D532=$04 and a timer before player state setup.
SC_04ADF:
    RES 3,(HL)
SC_04AE1:
    LD A,($D500)
SC_04AE4:
    DEC A
SC_04AE5:
    RET nz
SC_04AE6:
    LD A,4
SC_04AE8:
    LD ($D532),A
SC_04AEB:
    LD HL,$12C
SC_04AEE:
    LD A,($D297)
SC_04AF1:
    CP 8
SC_04AF3:
    JR nz,SC_04AF8
SC_04AF5:
    LD HL,$1770
SC_04AF8:
    LD ($D44C),HL
SC_04AFB:
    LD IX,$D500
SC_04AFF:
    JP $4775
SC_04B02:
    RES 4,(HL)
SC_04B04:
    LD A,11
SC_04B06:
    LD ($D3C4),A
SC_04B09:
    LD A,$F8
SC_04B0B:
    LD ($DE04),A
SC_04B0E:
    RET
SC_04B0F:
    RES 2,(HL)
SC_04B11:
    LD A,3
SC_04B13:
    LD ($D532),A
SC_04B16:
    LD HL,$384
SC_04B19:
    LD ($D44C),HL
SC_04B1C:
    RET
; Reward bit 5: set player flags, sound $84, timer $0258, selector $06, and allocate type $05 if newly selected.
SC_04B1D:
    RES 5,(HL)
SC_04B1F:
    LD HL,$D503
SC_04B22:
    SET 1,(HL)
SC_04B24:
    SET 7,(HL)
SC_04B26:
    LD A,$84
SC_04B28:
    LD ($DE04),A
SC_04B2B:
    CALL $062D
SC_04B2E:
    LD HL,$258
SC_04B31:
    LD ($D44C),HL
SC_04B34:
    LD A,($D532)
SC_04B37:
    CP 6
SC_04B39:
    RET z
SC_04B3A:
    LD A,6
SC_04B3C:
    LD ($D532),A
SC_04B3F:
    LD C,5
SC_04B41:
    LD H,0
SC_04B43:
    JP $5E9C

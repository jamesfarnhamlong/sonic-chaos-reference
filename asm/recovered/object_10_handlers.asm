; object_10_handlers: ROM $32149..$321EF (end exclusive $321F0).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Type $10 initialization: enable object contact, request state 1, and rewrite parameter $04 to $01 for non-type-$01 player.
SC_32149:
    SET 7,(IX+3)
SC_3214D:
    LD (IX+2),1
SC_32151:
    LD A,($D500)
SC_32154:
    DEC A
SC_32155:
    RET z
SC_32156:
    LD A,(IX+$3F)
SC_32159:
    CP 4
SC_3215B:
    RET nz
SC_3215C:
    LD (IX+$3F),1
SC_32160:
    RET
; Type $10 state-1 entry: visibility graphics latch, then request active state 2.
SC_32161:
    LD B,(IX+$3F)
SC_32164:
    CALL $A1F9
SC_32167:
    LD (IX+2),2
SC_3216B:
    RET
; Type $10 active callback: graphics latch, overlap resolution, attack/contact branches, reward selection and conversion.
SC_3216C:
    LD B,(IX+$3F)
SC_3216F:
    CALL $A1F9
SC_32172:
    BIT 6,(IX+4)
SC_32176:
    RET nz
SC_32177:
    CALL $034D
SC_3217A:
    LD A,($D503)
SC_3217D:
    BIT 1,A
SC_3217F:
    RET z
SC_32180:
    LD A,(IX+$21)
SC_32183:
    AND 15
SC_32185:
    RET z
SC_32186:
    CP 2
SC_32188:
    JR nz,SC_3219E
SC_3218A:
    LD HL,$200
SC_3218D:
    LD ($D518),HL
SC_32190:
    LD HL,$FE00
SC_32193:
    LD (IX+$19),H
SC_32196:
    LD (IX+$18),L
SC_32199:
    LD (IX+2),3
SC_3219D:
    RET
SC_3219E:
    CP 1
SC_321A0:
    JR nz,SC_321B1
SC_321A2:
    LD A,($D502)
SC_321A5:
    CP 15
SC_321A7:
    RET z
SC_321A8:
    CP $10
SC_321AA:
    RET z
SC_321AB:
    CP $15
SC_321AD:
    RET z
SC_321AE:
    CP $1A
SC_321B0:
    RET z
SC_321B1:
    LD HL,($D518)
SC_321B4:
    LD A,L
SC_321B5:
    OR H
SC_321B6:
    RET z
SC_321B7:
    LD A,H
SC_321B8:
    AND $80
SC_321BA:
    RET nz
SC_321BB:
    CALL $A1D3
SC_321BE:
    LD (IX+$3F),$40
SC_321C2:
    LD A,($D501)
SC_321C5:
    CP 9
SC_321C7:
    JP z,$033E
SC_321CA:
    LD HL,$FC00
SC_321CD:
    LD ($D518),HL
SC_321D0:
    JP $033E
; Parameter below $0A indexes one-bit reward table $A1F0 and queues it in $D3A3.
SC_321D3:
    LD A,(IX+$3F)
SC_321D6:
    CP 10
SC_321D8:
    RET nc
SC_321D9:
    LD E,A
SC_321DA:
    LD D,0
SC_321DC:
    LD HL,$A1F0
SC_321DF:
    ADD HL,DE
SC_321E0:
    LD A,($D3A3)
SC_321E3:
    OR (HL)
SC_321E4:
    LD ($D3A3),A
SC_321E7:
    LD (IX+$3F),0
SC_321EB:
    SET 6,(IX+$3F)
SC_321EF:
    RET

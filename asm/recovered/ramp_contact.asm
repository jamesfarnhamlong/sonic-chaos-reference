; ramp_contact: ROM $069B1..$06A5A (end exclusive $06A5B).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

SC_069B1:
    RET
; Surface type $12 ramp behavior; upward motion returns without applying it.
SC_069B2:
    BIT 7,(IX+$19)
SC_069B6:
    RET nz
; Previous modifier D36A controls launch versus initial-roll path.
SC_069B7:
    LD A,($D36A)
SC_069BA:
    OR A
SC_069BB:
    JR z,SC_069DF
SC_069BD:
    LD A,(IX+1)
SC_069C0:
    CP $1B
SC_069C2:
    RET z
SC_069C3:
    LD A,(IX+$16)
SC_069C6:
    OR (IX+$17)
SC_069C9:
    RET z
SC_069CA:
    LD A,(IX+$23)
SC_069CD:
    BIT 7,(IX+$17)
SC_069D1:
    JR nz,SC_069D9
SC_069D3:
    BIT 1,A
SC_069D5:
    RET z
SC_069D6:
    JP $6A18
SC_069D9:
    BIT 1,A
SC_069DB:
    RET nz
SC_069DC:
    JP $6A18
SC_069DF:
    CALL $64CB
SC_069E2:
    BIT 1,(IX+$23)
SC_069E6:
    RET z
SC_069E7:
    LD A,($D36B)
; Initial-roll path: tile $1F or tile >=$22 adds -4 X; other tile IDs add +4.
SC_069EA:
    CP $1F
SC_069EC:
    JR z,SC_06A05
SC_069EE:
    CP $22
SC_069F0:
    JR nc,SC_06A05
SC_069F2:
    LD L,(IX+$16)
SC_069F5:
    LD H,(IX+$17)
SC_069F8:
    LD DE,$400
SC_069FB:
    ADD HL,DE
SC_069FC:
    LD (IX+$16),L
SC_069FF:
    LD (IX+$17),H
SC_06A02:
    JP $47DC
SC_06A05:
    LD L,(IX+$16)
SC_06A08:
    LD H,(IX+$17)
SC_06A0B:
    LD DE,$FC00
SC_06A0E:
    ADD HL,DE
SC_06A0F:
    LD (IX+$16),L
SC_06A12:
    LD (IX+$17),H
SC_06A15:
    JP $47DC
; Rightward ramp launch sets Y velocity to -(X + floor(X/2)); request $1B.
SC_06A18:
    LD L,(IX+$16)
SC_06A1B:
    LD H,(IX+$17)
SC_06A1E:
    BIT 7,H
SC_06A20:
    JR nz,SC_06A3B
SC_06A22:
    LD D,H
SC_06A23:
    LD E,L
SC_06A24:
    SRL H
SC_06A26:
    RR L
SC_06A28:
    ADD HL,DE
SC_06A29:
    DEC HL
SC_06A2A:
    LD A,H
SC_06A2B:
    CPL
SC_06A2C:
    LD H,A
SC_06A2D:
    LD A,L
SC_06A2E:
    CPL
SC_06A2F:
    LD L,A
SC_06A30:
    LD ($D518),HL
SC_06A33:
    LD A,$A2
SC_06A35:
    LD ($DE04),A
SC_06A38:
    JP $47FB
; Leftward path takes magnitude first, then applies the same upward launch formula.
SC_06A3B:
    DEC HL
SC_06A3C:
    LD A,H
SC_06A3D:
    CPL
SC_06A3E:
    LD H,A
SC_06A3F:
    LD A,L
SC_06A40:
    CPL
SC_06A41:
    LD L,A
SC_06A42:
    LD D,H
SC_06A43:
    LD E,L
SC_06A44:
    SRL H
SC_06A46:
    RR L
SC_06A48:
    ADD HL,DE
SC_06A49:
    DEC HL
SC_06A4A:
    LD A,H
SC_06A4B:
    CPL
SC_06A4C:
    LD H,A
SC_06A4D:
    LD A,L
SC_06A4E:
    CPL
SC_06A4F:
    LD L,A
SC_06A50:
    LD ($D518),HL
SC_06A53:
    LD A,$A2
SC_06A55:
    LD ($DE04),A
SC_06A58:
    JP $47FB

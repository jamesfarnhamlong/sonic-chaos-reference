; block_47_surface_handler: ROM $06AE3..$06B13 (end exclusive $06B14).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Surface type $16 handler used by THZ block $47 base collision: apply the normal contact-state path when object+$03 bit 1 is set; it does not create an object.
SC_06AE3:
    BIT 1,(IX+3)
SC_06AE7:
    RET z
SC_06AE8:
    LD A,($D501)
SC_06AEB:
    CP 15
SC_06AED:
    RET z
SC_06AEE:
    CP $10
SC_06AF0:
    RET z
SC_06AF1:
    CP $15
SC_06AF3:
    RET z
SC_06AF4:
    CP $1A
SC_06AF6:
    RET z
SC_06AF7:
    LD A,($D522)
SC_06AFA:
    AND 12
SC_06AFC:
    JR nz,SC_06B03
SC_06AFE:
    LD A,($D519)
SC_06B01:
    AND A
SC_06B02:
    RET m
SC_06B03:
    LD HL,$FBC0
SC_06B06:
    LD ($D518),HL
SC_06B09:
    RES 1,(IX+$22)
SC_06B0D:
    SET 0,(IX+3)
SC_06B11:
    JP $7857

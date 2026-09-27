; object_09_handlers: ROM $31C10..$31C57 (end exclusive $31C58).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Object $09 initialization and collection callbacks. Parameter zero is visible; nonzero is hidden and checked every other global frame.
SC_31C10:
    LD (IX+2),1
SC_31C14:
    LD A,(IX+$3F)
SC_31C17:
    OR A
SC_31C18:
    RET z
SC_31C19:
    LD (IX+2),3
SC_31C1D:
    SET 7,(IX+4)
SC_31C21:
    RET
SC_31C22:
    BIT 6,(IX+4)
SC_31C26:
    RET nz
SC_31C27:
    CALL $0380
SC_31C2A:
    OR A
SC_31C2B:
    RET z
SC_31C2C:
    LD A,$BF
SC_31C2E:
    LD ($DE04),A
SC_31C31:
    CALL $0347
SC_31C34:
    LD (IX+2),2
SC_31C38:
    LD (IX+$3E),0
SC_31C3C:
    RET
SC_31C3D:
    LD A,($D12F)
SC_31C40:
    RRCA
SC_31C41:
    RET c
SC_31C42:
    CALL $0380
SC_31C45:
    OR A
SC_31C46:
    RET z
SC_31C47:
    LD A,$BF
SC_31C49:
    LD ($DE04),A
SC_31C4C:
    CALL $0347
SC_31C4F:
    LD (IX+$3E),0
SC_31C53:
    LD (IX+0),$FF
SC_31C57:
    RET

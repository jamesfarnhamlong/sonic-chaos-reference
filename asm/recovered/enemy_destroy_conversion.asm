; enemy_destroy_conversion: ROM $05F54..$05F83 (end exclusive $05F84).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Generic defeated-enemy conversion: add the score-table value, replace the slot with type $0F, and detach it from its placement.
SC_05F54:
    CALL $5F77
SC_05F57:
    LD (IX+0),15
SC_05F5B:
    XOR A
SC_05F5C:
    LD (IX+1),A
SC_05F5F:
    LD (IX+2),A
SC_05F62:
    LD (IX+4),A
SC_05F65:
    LD (IX+7),A
SC_05F68:
    LD (IX+14),A
SC_05F6B:
    LD (IX+15),A
SC_05F6E:
    LD (IX+$3E),0
SC_05F72:
    LD (IX+$3F),0
SC_05F76:
    RET
SC_05F77:
    LD A,(IX+0)
SC_05F7A:
    CP $50
SC_05F7C:
    RET nc
SC_05F7D:
    RET z
SC_05F7E:
    LD HL,$27EB
SC_05F81:
    JP $262F

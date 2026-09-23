; object_slot_cleanup: ROM $05EF8..$05F16 (end exclusive $05F17).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Type $FE cleanup releases the placement occupancy byte named by object+$3E, then clears the slot.
SC_05EF8:
    LD A,(IX+$3E)
SC_05EFB:
    OR A
SC_05EFC:
    JP z,$5F09
SC_05EFF:
    DEC A
SC_05F00:
    LD E,A
SC_05F01:
    LD D,0
SC_05F03:
    LD HL,$D400
SC_05F06:
    ADD HL,DE
SC_05F07:
    LD (HL),0
SC_05F09:
    PUSH IX
SC_05F0B:
    POP HL
SC_05F0C:
    LD (HL),0
SC_05F0E:
    LD E,L
SC_05F0F:
    LD D,H
SC_05F10:
    INC DE
SC_05F11:
    LD BC,$3F
SC_05F14:
    LDIR
SC_05F16:
    RET

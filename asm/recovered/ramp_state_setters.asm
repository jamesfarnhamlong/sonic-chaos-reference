; ramp_state_setters: ROM $047DC..$0480B (end exclusive $0480C).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

SC_047DC:
    LD A,(IX+$17)
SC_047DF:
    OR A
SC_047E0:
    JP z,$46BB
SC_047E3:
    LD (IX+2),9
SC_047E7:
    LD HL,$600
SC_047EA:
    LD ($D373),HL
SC_047ED:
    RES 0,(IX+3)
SC_047F1:
    SET 1,(IX+3)
SC_047F5:
    LD A,$A5
SC_047F7:
    LD ($DE04),A
SC_047FA:
    RET
; Request ramp-launch state $1B; set airborne and rolling; clear ground contact.
SC_047FB:
    LD (IX+2),$1B
SC_047FF:
    SET 0,(IX+3)
SC_04803:
    SET 1,(IX+3)
SC_04807:
    RES 1,(IX+$22)
SC_0480B:
    RET

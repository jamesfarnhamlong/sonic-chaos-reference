; numeric_reward_counter: ROM $03104..$03137 (end exclusive $03138).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Numeric reward bit 1 path: request sound $A9 and increment BCD byte $D299 up to $99.
SC_03104:
    LD A,$A9
SC_03106:
    LD ($DE04),A
SC_03109:
    LD A,($D299)
SC_0310C:
    CP $99
SC_0310E:
    JR z,SC_03116
SC_03110:
    ADD A,1
SC_03112:
    DAA
SC_03113:
    LD ($D299),A
SC_03116:
    LD A,($D292)
SC_03119:
    OR A
SC_0311A:
    RET nz
SC_0311B:
    LD A,($D299)
SC_0311E:
    AND 15
SC_03120:
    RLCA
SC_03121:
    AND $1E
SC_03123:
    ADD A,$2E
SC_03125:
    LD ($DBA9),A
SC_03128:
    LD A,($D299)
SC_0312B:
    AND $F0
SC_0312D:
    RRCA
SC_0312E:
    RRCA
SC_0312F:
    RRCA
SC_03130:
    AND $1E
SC_03132:
    ADD A,$2E
SC_03134:
    LD ($DBAB),A
SC_03137:
    RET

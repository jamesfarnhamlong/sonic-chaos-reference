; dispatch_target_3018F: ROM $3018F..$30193 (end exclusive $30194).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_3018F:
    LD A,($D448)
SC_30192:
    RRCA
SC_30193:
    RET

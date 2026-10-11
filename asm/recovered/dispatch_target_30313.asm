; dispatch_target_30313: ROM $30313..$3031C (end exclusive $3031D).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_30313:
    SET 7,(IX+3)
SC_30317:
    LD A,12
SC_30319:
    LD ($D3B1),A
SC_3031C:
    RET

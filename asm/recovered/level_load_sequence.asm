; level_load_sequence: ROM $02934..$0297D (end exclusive $0297E).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Level load sequence: clear the $D300 block ($297E), $78E1, $2993, clear the $D15E block ($4FCE), level header loader $4FDC, $4DAD, $2A4F, $2A2E, copy $D2C8 to $D500, then $79DF (when $D2C8 is not 1) and $79F2. Both exits wait a frame ($062D).
SC_02934:
    DI
SC_02935:
    CALL $297E
SC_02938:
    CALL $78E1
SC_0293B:
    CALL $2993
SC_0293E:
    LD IX,$D15E
SC_02942:
    CALL $4FCE
SC_02945:
    CALL $4FDC
SC_02948:
    CALL $4DAD
SC_0294B:
    CALL $2A4F
SC_0294E:
    CALL $2A2E
SC_02951:
    LD A,($D2C8)
SC_02954:
    LD ($D500),A
SC_02957:
    DEC A
SC_02958:
    CALL nz,$79DF
SC_0295B:
    CALL $79F2
SC_0295E:
    LD A,($D2BD)
SC_02961:
    OR A
SC_02962:
    JR nz,SC_0297A
SC_02964:
    XOR A
SC_02965:
    LD ($D2BF),A
SC_02968:
    LD ($D2C0),A
SC_0296B:
    LD A,($D292)
SC_0296E:
    OR A
SC_0296F:
    JR nz,SC_02976
SC_02971:
    LD A,$FF
SC_02973:
    LD ($D2BE),A
SC_02976:
    CALL $062D
SC_02979:
    RET
SC_0297A:
    CALL $062D
SC_0297D:
    RET

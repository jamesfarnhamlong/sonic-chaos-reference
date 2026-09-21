; spring_state_updates: ROM $0393B..$0396C (end exclusive $0396D).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Vertical spring update: shared movement, then landing/apex state decisions.
SC_0393B:
    CALL $3FEF
SC_0393E:
    LD A,($D502)
SC_03941:
    CP 11
SC_03943:
    RET nz
SC_03944:
    BIT 1,(IX+$23)
SC_03948:
    JP nz,$45CE
SC_0394B:
    BIT 7,(IX+$19)
SC_0394F:
    JP z,$463C
SC_03952:
    JP $48A7
; Diagonal spring update: shared movement; on apex requests falling.
SC_03955:
    CALL $3FEF
SC_03958:
    LD A,($D502)
SC_0395B:
    CP $1C
SC_0395D:
    RET nz
SC_0395E:
    BIT 1,(IX+$23)
SC_03962:
    JP nz,$45CE
SC_03965:
    BIT 7,(IX+$19)
SC_03969:
    JP z,$463C
SC_0396C:
    RET

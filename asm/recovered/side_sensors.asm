; side_sensors: ROM $03686..$036C5 (end exclusive $036C6).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Default side probes: (-9,-12) and (+9,-12); lookup adds +18 to Y.
SC_03686:
    LD A,(IX+0)
SC_03689:
    DEC A
SC_0368A:
    JR nz,SC_036A9
SC_0368C:
    LD BC,$FFF7
SC_0368F:
    LD DE,$FFF4
SC_03692:
    LD ($D498),BC
SC_03696:
    LD ($D49A),DE
SC_0369A:
    LD BC,9
SC_0369D:
    LD DE,$FFF4
SC_036A0:
    LD ($D49C),BC
SC_036A4:
    LD ($D49E),DE
SC_036A8:
    RET
SC_036A9:
    LD BC,$FFF7
SC_036AC:
    LD DE,$FFF4
SC_036AF:
    LD ($D498),BC
SC_036B3:
    LD ($D49A),DE
SC_036B7:
    LD BC,9
SC_036BA:
    LD DE,$FFF4
SC_036BD:
    LD ($D49C),BC
SC_036C1:
    LD ($D49E),DE
SC_036C5:
    RET

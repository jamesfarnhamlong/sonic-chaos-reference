; object_26_span_handlers: ROM $783BF..$78438 (end exclusive $78439).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Span state 8: check a saved X interval before requesting activation state 9.
SC_783BF:
    LD A,($D519)
SC_783C2:
    BIT 7,A
SC_783C4:
    RET nz
SC_783C5:
    LD A,($D502)
SC_783C8:
    CP $21
SC_783CA:
    RET z
SC_783CB:
    LD A,($D522)
SC_783CE:
    BIT 1,A
SC_783D0:
    RET z
SC_783D1:
    LD H,(IX+$3B)
SC_783D4:
    LD L,(IX+$3A)
SC_783D7:
    LD (IX+$12),H
SC_783DA:
    LD (IX+$11),L
SC_783DD:
    LD HL,($D511)
SC_783E0:
    LD D,(IX+$12)
SC_783E3:
    LD E,(IX+$11)
SC_783E6:
    XOR A
SC_783E7:
    SBC HL,DE
SC_783E9:
    RET c
SC_783EA:
    LD D,(IX+$35)
SC_783ED:
    LD E,(IX+$34)
SC_783F0:
    XOR A
SC_783F1:
    SBC HL,DE
SC_783F3:
    RET nc
SC_783F4:
    LD BC,$30
SC_783F7:
    CALL $0386
SC_783FA:
    OR A
SC_783FB:
    RET z
SC_783FC:
    LD (IX+2),9
SC_78400:
    RET
; Span activation aligns object X to the player on a 16-pixel boundary and launches.
SC_78401:
    LD A,($D512)
SC_78404:
    LD (IX+$12),A
SC_78407:
    LD A,($D511)
SC_7840A:
    AND $F0
SC_7840C:
    LD (IX+$11),A
SC_7840F:
    LD B,$FF
SC_78411:
    LD HL,$F8A0
SC_78414:
    LD A,(IX+$3F)
SC_78417:
    OR A
SC_78418:
    JR z,SC_7841F
SC_7841A:
    LD B,0
SC_7841C:
    LD HL,$FB00
SC_7841F:
    LD A,B
SC_78420:
    LD ($D448),A
SC_78423:
    CALL $035F
SC_78426:
    LD A,$1C
SC_78428:
    LD (IX+$1E),A
SC_7842B:
    LD (IX+2),3
SC_7842F:
    LD A,(IX+9)
SC_78432:
    OR A
SC_78433:
    RET nz
SC_78434:
    LD (IX+2),1
SC_78438:
    RET

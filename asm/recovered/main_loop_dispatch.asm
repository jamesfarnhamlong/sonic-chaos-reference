; main_loop_dispatch: ROM $01333..$01364 (end exclusive $01365).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Main loop: wait for the frame ($062D), then test $D294 bit 7 and the bits of the flag byte $D293 in turn: bit 7 -> $1365, bit 6 clear -> $138A, bit 5 -> $14AE, bit 4 -> $1543, bit 2 -> $15F2, bit 1 -> $1673, bit 0 -> $1696 (bit 3 is not tested). With none selected it runs the gameplay update ($16B8, $173F) and loops.
SC_01333:
    CALL $062D
SC_01336:
    LD A,($D294)
SC_01339:
    RLCA
SC_0133A:
    JP c,$1762
SC_0133D:
    LD A,($D293)
SC_01340:
    RLCA
SC_01341:
    JP c,$1365
SC_01344:
    RLCA
SC_01345:
    JP nc,$138A
SC_01348:
    RLCA
SC_01349:
    JP c,$14AE
SC_0134C:
    RLCA
SC_0134D:
    JP c,$1543
SC_01350:
    RLCA
SC_01351:
    RLCA
SC_01352:
    JP c,$15F2
SC_01355:
    RLCA
SC_01356:
    JP c,$1673
SC_01359:
    RLCA
SC_0135A:
    JP c,$1696
SC_0135D:
    CALL $16B8
SC_01360:
    CALL $173F
SC_01363:
    JR SC_01333

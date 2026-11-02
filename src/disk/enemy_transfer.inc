    MACRO compact_transfer fast
    DUP 3,column
    PUSH DE
    LD A,E
    OUT ($99),A
    LD A,D
    OR $40
    OUT ($99),A
    LD B,8
    IF fast
    DUP 8
    OUTD
    EDUP
    ELSE
1:
    OUTD
    JP NZ,1B
    ENDIF
    LD DE,(COMPACT_BOTTOM)
    IF column > 0
    LD A,E
    ADD A,column*8
    LD E,A
    LD A,D
    ADC A,0
    LD D,A
    ENDIF
    LD A,E
    OUT ($99),A
    LD A,D
    OR $40
    OUT ($99),A
    LD BC,$0798
    IF fast
    DUP 7
    OUTD
    EDUP
    ELSE
2:
    OUTD
    JP NZ,2B
    ENDIF
    ; Row15 is permanently zero: cold VRAM clear initializes every private
    ; enemy slot and no other producer owns these pattern bytes. Transferring
    ; that constant row again spends the end of the tight NTSC VBlank window.
    POP DE
    IF column < 2
    LD A,E
    ADD A,8
    LD E,A
    JR NC,3F
    INC D
3:
    LD BC,100
    ADD HL,BC
    LD C,$98
    ENDIF
    EDUP
    RET
    ENDM

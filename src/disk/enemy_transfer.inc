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
    XOR A
    IF fast == 0
    NOP
    ENDIF
    OUT ($98),A
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

CURRENT_TILE EQU $CEB0
CURRENT_N EQU $CEB1
CURRENT_CLASS EQU $CEB2
CURRENT_WRITER EQU $CEB4

palette_current_field:
    LD A,H
    CP $D0
    JP C,current_dynamic
    PUSH HL
    LD DE,F_BACKGROUND_NAMES
    OR A
    SBC HL,DE
    POP HL
    JR C,.lookup
    LD A,L
    CP LOW F_BACKGROUND_TOP
    LD HL,forecast_top
    JR Z,.program
    LD HL,forecast_bottom
    JR .program
.lookup:
    LD A,H
    SUB $D0
    LD H,A
    LD DE,forecast_lookup
    ADD HL,DE
    LD L,(HL)
    LD H,0
    ADD HL,HL
    LD DE,forecast_program_pointers
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
.program:
    LD B,(HL)
    INC HL
.span:
    PUSH BC
    LD A,(HL)
    LD (CURRENT_TILE),A
    INC HL
    LD A,(HL)
    LD (CURRENT_N),A
    INC HL
    LD A,(HL)
    LD (CURRENT_CLASS),A
    INC HL
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD (CURRENT_WRITER),DE
    PUSH HL
    CALL current_span
    POP HL
    POP BC
    DJNZ .span
    RET

current_dynamic:
    LD B,3
.digit:
    PUSH BC
    LD A,(HL)
    INC HL
    PUSH HL
    LD (CURRENT_TILE),A
    LD L,A
    LD H,0
    ADD HL,HL
    LD DE,forecast_dynamic_writers
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (CURRENT_WRITER),DE
    LD A,1
    LD (CURRENT_N),A
    LD A,F_SCORE1
    LD (CURRENT_CLASS),A
    CALL current_span
    POP HL
    POP BC
    DJNZ .digit
    RET

current_span:
    LD A,(CURRENT_CLASS)
    ADD A,$B0
    LD L,A
    LD H,$CF
    LD E,(HL)
    LD A,(CURRENT_TILE)
    LD L,A
    LD A,(CURRENT_N)
    LD H,$EC
    BIT 7,A
    JR Z,.page
    INC H
.page:
    AND 127
    LD B,A
    DEC A
    JR NZ,.many
    LD A,(HL)
    CP E
    RET Z
    LD (HL),E
    JR .append
.many:
    PUSH HL
.test:
    LD A,(HL)
    CP E
    JR NZ,.dirty
    INC L
    DJNZ .test
    POP HL
    RET
.dirty:
    POP HL
    LD A,(CURRENT_N)
    AND 127
    LD B,A
.mark:
    LD (HL),E
    INC L
    DJNZ .mark
.append:
    LD HL,($C6DA)
    LD DE,(CURRENT_WRITER)
    LD (HL),E
    INC HL
    LD (HL),D
    INC HL
    LD ($C6DA),HL
    LD HL,$C6DC
    INC (HL)
    RET

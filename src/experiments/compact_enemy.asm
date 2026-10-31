; Throwaway corrected experiment. Match the accepted display-off fast mode.
COMPACT_BOTTOM EQU $CE80
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
    LD A,1
    LD ($7000),A
    RET
    ENDM

upload_banked_lane:
    LD A,(lane_var)
    LD E,A
    LD D,0
    LD HL,$C0D9
    ADD HL,DE
    BIT 3,(HL)
    LD A,(phase_page)
    JR Z,.phase
    ADD A,16
.phase:
    ADD A,$80
    LD H,A
    LD A,(source_ptr)
    SUB $A4
    LD L,A
    PUSH HL
    LD A,(tile_bottom_base)
    LD D,0
    DUP 3
    ADD A,A
    RL D
    EDUP
    LD E,A
    LD A,(lane_var)
    OR A
    JR Z,.split
    CP 3
    LD A,D
    JR Z,.bottom_ready
    OR 8
    JR .bottom_ready
.split:
    LD A,D
    OR $10
.bottom_ready:
    LD D,A
    LD (COMPACT_BOTTOM),DE
    LD A,(tile_base)
    LD D,0
    DUP 3
    ADD A,A
    RL D
    EDUP
    LD E,A
    LD A,(lane_var)
    CP 3
    JR Z,.top_ready
    LD A,D
    OR 8
    LD D,A
.top_ready:
    POP HL
    LD A,2
    LD ($7000),A
    LD C,$98
    LD A,(PAL_DISPLAY_OFF)
    OR A
    JP NZ,.fast
    compact_transfer 0
.fast:
    compact_transfer 1

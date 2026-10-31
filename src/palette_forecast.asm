; Private bank7 preparation of the predictable next idle-palette display.
; Canonical state is read only. C280/282/284 and the native TIM64T C296 stay
; reserved. C100/C300 are shadow HUD colour IDs; C200 holds a bounded
; future ROP queue. Actual cache tags are invalidated
; during preparation so no deferred marker drain is required.
F_QUEUE EQU $C200
F_MEMO EQU $C2A0
F_PTRS EQU $C2C8
F_COPY EQU $C2DC
F_QPTR EQU $C2DE
F_COUNT EQU $C2E0
F_STAGE EQU $C2E1
F_NEXT EQU $C2E2
F_CURRENT EQU $C2E3
F_COUNTER EQU $C2E4
F_A3 EQU $C2E5
F_TILE EQU $C2E7
F_N EQU $C2E8
F_CLASS EQU $C2E9
F_WRITER EQU $C2EA
F_SNAPSHOT EQU $C286
F_REMAIN EQU $C2F2
F_PROGRAM EQU $C2F3
F_DYNAMIC EQU $C2F5

palette_forecast_tick:
    LD A,($C081)
    CP $D0
    RET C
    LD A,($C0A3)
    OR A
    RET Z
    LD A,($C0E9)
    OR A
    RET NZ
    LD A,($C6D2)                ; pending RGB/IDs must already be complete
    OR A
    RET Z
    LD A,($C6D0)
    LD HL,F_CURRENT
    CP (HL)
    JR NZ,.reset
    LD A,($C6D1)
    LD HL,F_NEXT
    CP (HL)
    JR NZ,.reset
    LD A,($C0A2)
    LD HL,F_COUNTER
    CP (HL)
    JR NZ,.reset
    CALL forecast_snapshot_equal
    JR Z,.copy
.reset:
    LD A,($C6D0)
    LD (F_CURRENT),A
    LD A,($C6D1)
    LD (F_NEXT),A
    LD A,($C0A2)
    LD (F_COUNTER),A
    XOR A
    LD (F_STAGE),A
    LD (F_REMAIN),A
    LD (F_COUNT),A
    LD H,A
    LD L,A
    LD (F_COPY),HL
    LD HL,F_QUEUE
    LD (F_QPTR),HL
    LD HL,forecast_state_addresses
    LD DE,F_SNAPSHOT
    LD B,9
.snapshot:
    LD C,(HL)
    INC HL
    LD A,(HL)
    INC HL
    PUSH HL
    LD H,A
    LD L,C
    LD A,(HL)
    LD (DE),A
    INC DE
    POP HL
    DJNZ .snapshot
.copy:
    LD HL,(F_COPY)
    LD A,H
    CP 2
    JR NC,.collect
    ADD A,$C1
    ADD A,H                     ; source ED maps to shadow C3, not C2devices
    LD D,A
    LD E,L
    LD BC,$EC00
    ADD HL,BC
    LD BC,32
    LDIR
    LD HL,(F_COPY)
    LD BC,32
    ADD HL,BC
    LD (F_COPY),HL
    RET
.collect:
    LD A,($C081)
    CP $E0
    RET C
    LD A,(F_STAGE)
    CP 10
    RET NC
    ; A3 decrements modulo255, skipping zero, before phase increments. Predict
    ; the source value at the next phase0, including the255->128 idle wrap.
    LD A,($C081)
    NEG
    LD B,A
    LD A,($C0A3)
.future_a3:
    DEC A
    JR NZ,.nonzero
    DEC A
.nonzero:
    DJNZ .future_a3
    LD C,A
    LD A,(F_STAGE)
    OR A
    JR Z,.prepare_fields
    LD A,(F_A3)
    CP C
    JP NZ,.reset
    JR .dispatch
.prepare_fields:
    LD A,C
    LD (F_A3),A
    LD HL,$CF00
    LD DE,F_PTRS
    LD BC,16
    LDIR
    LD A,(F_A3)
    DUP 3
    SRL A
    EDUP
    CP 20
    JR NC,.activision
    CP 12
    JR C,.seaquest
    SUB 11
    JR .logo
.activision:
    LD A,8
    JR .logo
.seaquest:
    XOR A
.logo:
    LD L,A
    LD H,0
    LD E,A
    LD D,H
    DUP 3
    ADD HL,HL
    EDUP
    ADD HL,DE
    LD DE,F_HUD_LOGO
    ADD HL,DE
    LD (F_PTRS+10),HL
.dispatch:
    LD A,(F_REMAIN)
    OR A
    JP NZ,.resume
    LD A,(F_STAGE)
    ADD A,A
    ADD A,A
    ADD A,LOW F_MEMO
    LD L,A
    LD H,HIGH F_MEMO
    PUSH HL
    POP IY
    LD A,(F_STAGE)
    CP 8
    JR NC,.background
    ADD A,A
    ADD A,LOW F_PTRS
    LD L,A
    LD H,HIGH F_PTRS
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
    LD A,(F_STAGE)
    CP 4
    JR NC,.bottom
    LD A,($C0B7)
    OR A
    LD A,($CFD0+F_SCORE0)
    JR Z,$+5
    LD A,($CFD0+F_SCORE1)
    CALL forecast_field
    JR .stage_done
.bottom:
    JR NZ,.logo_field
    LD A,($CFD0+F_DIVER)
    CALL forecast_field
    JR .stage_done
.logo_field:
    CP 5
    JR Z,.force_logo_start
    CALL forecast_global_field
    JR .stage_done
.force_logo_start:
    ; Logo is the only HUD field that can move between the shadow copy and
    ; activation. Force its target nine tiles, avoiding stale-cache false hits.
    PUSH HL
    LD B,9
.force_logo:
    LD E,(HL)
    LD D,$C3
    XOR A
    LD (DE),A
    INC HL
    DJNZ .force_logo
    LD A,($CFD0+F_LOGO)
    POP HL
    CALL forecast_field
    JR .stage_done
.background:
    CP 8
    LD HL,F_BACKGROUND_TOP
    JR Z,.background_field
    LD HL,F_BACKGROUND_BOTTOM
.background_field:
    CALL forecast_global_field
.stage_done:
    LD A,(F_REMAIN)
    OR A
    JR Z,.finished_field
.resume:
    CALL forecast_one_span
    LD A,(F_REMAIN)
    OR A
    CALL NZ,forecast_one_span
    LD A,(F_REMAIN)
    OR A
    RET NZ
.finished_field:
    LD A,(F_STAGE)
    CP 255
    RET Z
    INC A
    LD (F_STAGE),A
    RET

forecast_snapshot_equal:
    LD HL,forecast_state_addresses
    LD DE,F_SNAPSHOT
    LD B,9
.byte:
    LD C,(HL)
    INC HL
    LD A,(HL)
    INC HL
    PUSH HL
    LD H,A
    LD L,C
    LD C,(HL)
    LD A,(DE)
    INC DE
    POP HL
    CP C
    RET NZ
    DJNZ .byte
    RET

forecast_global_field:
    LD A,(F_NEXT)
forecast_field:
    LD (IY+0),L
    LD (IY+1),H
    LD (IY+2),A
    LD (IY+3),0
    LD BC,4
    ADD IY,BC
    LD A,H
    CP $D0
    JR C,.dynamic
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
    LD A,(HL)
    LD (F_REMAIN),A
    INC HL
    LD (F_PROGRAM),HL
    XOR A
    LD (F_DYNAMIC),A
    RET
.dynamic:
    LD (F_PROGRAM),HL
    LD A,3
    LD (F_REMAIN),A
    LD (F_DYNAMIC),A
    RET

forecast_one_span:
    LD HL,(F_PROGRAM)
    LD A,(F_DYNAMIC)
    OR A
    JR NZ,.digit
    LD A,(HL)
    LD (F_TILE),A
    INC HL
    LD A,(HL)
    LD (F_N),A
    INC HL
    LD A,(HL)
    LD (F_CLASS),A
    INC HL
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (F_WRITER),DE
    INC HL
    LD (F_PROGRAM),HL
    CALL forecast_span
    JR .done
.digit:
    LD A,(HL)
    INC HL
    LD (F_PROGRAM),HL
    LD (F_TILE),A
    LD L,A
    LD H,0
    ADD HL,HL
    LD DE,forecast_dynamic_writers
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (F_WRITER),DE
    LD A,1
    LD (F_N),A
    LD A,F_SCORE1
    LD (F_CLASS),A
    CALL forecast_span
.done:
    LD HL,F_REMAIN
    DEC (HL)
    RET

forecast_span:
    LD A,(F_CLASS)
    ADD A,$D0
    LD L,A
    LD H,$CF
    LD E,(HL)
    LD A,(F_TILE)
    LD L,A
    LD A,(F_N)
    LD H,$C1
    BIT 7,A
    JR Z,.page
    LD H,$C3
.page:
    AND 127
    LD B,A
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
    LD A,(F_N)
    AND 127
    LD B,A
.mark:
    LD (HL),E
    INC L
    DJNZ .mark
    LD A,(F_TILE)
    LD L,A
    LD A,(F_N)
    LD H,$EC
    BIT 7,A
    JR Z,.physical_page
    INC H
.physical_page:
    AND 127
    LD B,A
    XOR A
.invalidate:
    LD (HL),A
    INC L
    DJNZ .invalidate
    LD A,(F_COUNT)
    CP 63
    JR C,.append
    LD A,255
    LD (F_STAGE),A
    RET
.append:
    LD HL,(F_QPTR)
    LD DE,(F_WRITER)
    LD (HL),E
    INC HL
    LD (HL),D
    INC HL
    LD (F_QPTR),HL
    LD HL,F_COUNT
    INC (HL)
    RET

palette_forecast_apply:
    LD A,(F_STAGE)
    CP 10
    JP NZ,.reject
    LD A,($C6D0)
    LD HL,F_NEXT
    CP (HL)
    JP NZ,.reject
    LD A,(F_COUNTER)
    INC A
    JR NZ,.counter
    LD A,128
.counter:
    LD HL,$C0A2
    CP (HL)
    JR Z,.counter_valid
    LD A,(HL)
    OR A                        ; input can clearA2 after computing this palette
    JR NZ,.reject
.counter_valid:
    LD A,(F_A3)
    LD HL,$C0A3
    CP (HL)
    JR NZ,.reject
    CALL forecast_snapshot_equal
    JR NZ,.reject
    LD HL,F_PTRS
    LD DE,$CF00
    LD B,16
.pointer:
    LD A,(DE)
    CP (HL)
    JR NZ,.reject
    INC HL
    INC DE
    DJNZ .pointer
    LD A,(F_COUNT)
    OR A
    JR Z,.reject
    LD A,(F_COUNT)
    LD ($C6DC),A
    ADD A,A
    LD C,A
    LD B,0
    LD HL,F_QUEUE
    LD DE,$C510
    LDIR
    LD ($C6DA),DE
    LD HL,F_MEMO
    LD DE,$CF80
    LD BC,40
    LDIR
    LD HL,(F_PTRS+10)
    LD B,9
.logo_tag:
    LD E,(HL)
    LD D,$ED
    XOR A
    LD (DE),A
    INC HL
    DJNZ .logo_tag
    ; The shared blank tile is either currently visible (therefore queued) or
    ; independently prewarmed while hidden. Its next-player cache ID is ready.
    LD A,($CFB0+F_SCORE0)
    LD ($EC00+F_BLANK_TILE),A
    LD A,255
    LD (F_STAGE),A
    LD A,1
    RET
.reject:
    XOR A
    RET

forecast_state_addresses:
    DW $C0B7,$C0B8,$C0B9,$C0BA,$C0BB,$C0BE,$C0C2,$C0E6,$C0E9

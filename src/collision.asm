; Original raster occupancy, independent of SCREEN 2 pixels and TMS collisions.
; Called with DI before original F5B8. Clobbers ordinary/alternate registers.
col_proj EQU $C440
col_mirror EQU $C442
col_shape EQU $C444
col_dy EQU $C446
col_reflect EQU $C447
col_lane EQU $C448
col_bits EQU $C44A
col_x EQU $C44C
col_mask EQU $C44D
col_ball_x EQU $C44E
col_copy EQU $C44F
col_overlap EQU $C450
col_height EQU $C451
col_window EQU $C452

acquire_contacts:
    LD HL,$FFFF
    LD ($C0B0),HL
    LD ($C0B2),HL
    LD ($C0B4),HL
    LD A,$FF
    LD ($C0B6),A
    ; CXPPMM's unconnected low bits return the original operand bus value 7.
    LD A,7
    LD ($C0F8),A
    XOR A
    LD (col_proj+1),A
    LD A,($C0E9)
    OR A
    JR Z,.normal_height
    CP 15
    JR NC,.normal_height
    LD DE,collision_player_heights
    JR .height
.normal_height:
    LD A,($C0E0)
    LD DE,collision_normal_heights
.height:
    LD L,A
    LD H,0
    ADD HL,DE
    LD A,(HL)
    LD (col_height),A
    ADD A,14
    LD (col_window),A
    JP .patrol_setup
.ensure_projection:
    LD A,($C0E9)
    OR A
    JR Z,.normal
    CP 15
    JR NC,.normal
    CP 10
    JR NC,.death
    LD A,10
.death:
    SUB 7
    JR .frame
.normal:
    LD A,($C0E0)
.frame:
    ADD A,A
    LD C,A
    LD A,($C0D6)
    AND 8
    RRCA
    RRCA
    RRCA
    OR C
    LD C,A
    CALL .projection
    LD (col_proj),HL
    LD A,C
    XOR 1
    CALL .projection
    LD (col_mirror),HL
    RET
.patrol_setup:
    ; ADC at F1B5 preserves death's carry: counters1..9 select rows11..4,
    ; otherwise rows12..5. These eight writes occupy raw lines45..52.
    LD A,($C0E0)
    LD E,A
    LD D,0
    LD HL,original_rom+$CFB
    ADD HL,DE
    LD A,(HL)
    ADD A,12
    LD C,A
    LD A,($C0E9)
    OR A
    JR Z,.patrol_rows
    CP 10
    JR NC,.patrol_rows
    DEC C
.patrol_rows:
    LD A,C
    LD L,A
    LD H,HIGH (original_rom+$D00)
    LD (col_shape),HL
    LD A,12
    LD HL,$C0E1
    SUB (HL)
    LD (col_dy),A
    LD A,8
    LD (col_reflect),A
    LD A,($C0F6)
    CP 160
    JR C,.patrol_x
    XOR A
.patrol_x:
    LD C,8
    CALL collision_player
    JR Z,.no_patrol
    LD A,135
    LD ($C0F8),A
.no_patrol:
    LD IY,$C0A3
    LD A,3
.lane:
    LD (col_lane),A
    ; Lane top minus player top; the clear window includes every nonzero row.
    LD E,A
    LD D,0
    LD HL,collision_lane_tops
    ADD HL,DE
    LD A,(HL)
    LD HL,$C0E1
    SUB (HL)
    SUB 33
    LD (col_dy),A
    ADD A,14
    LD HL,col_window
    CP (HL)                    ; skip verified zero tails of each player frame
    LD A,0
    JR NC,.vertical_flag
    INC A
.vertical_flag:
    LD (col_overlap),A
    LD A,(IY+39)               ; C7+lane, >=160 is positioned at zero
    CP 160
    JR C,.ball_x
    XOR A
.ball_x:
    LD (col_ball_x),A
    LD A,(col_overlap)
    OR A
    JR Z,.no_pickup
    LD A,(IY+57)               ; D9+lane
    AND 15
    LD C,A
    LD L,A
    LD H,0
    LD E,L
    LD D,H
    DUP 4
    ADD HL,HL
    EDUP
    OR A
    SBC HL,DE                 ; kind*15
    LD DE,collision_balls+14
    ADD HL,DE
    LD (col_shape),HL
    XOR A
    LD (col_reflect),A
    LD A,(col_ball_x)
    LD C,15
    CALL collision_player
    JR Z,.no_pickup
    LD A,(col_lane)
    LD ($C0B6),A
.no_pickup:
    LD A,(IY+57)
    AND 15
    ADD A,A
    ADD A,A
    ADD A,A
    ADD A,A
    LD C,A
    LD A,(IY+57)
    AND 7
    CP 4
    LD A,0
    JR NC,.animation
    LD A,($C0DD)
.animation:
    LD B,A
    ADD A,A
    ADD A,C
    LD L,A
    LD H,0
    LD DE,collision_enemy_ball
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (col_bits),DE
    LD A,(col_overlap)
    OR A
    JR Z,.repeats
    LD A,(IY+57)
    AND 7
    LD E,A
    LD D,0
    LD HL,original_rom+$FA2
    ADD HL,DE
    LD A,(HL)
    ADD A,B
    ADD A,14
    LD L,A
    LD H,HIGH (original_rom+$D00)
    LD (col_shape),HL
    LD A,(IY+57)
    AND 8
    LD (col_reflect),A
.repeats:
    LD A,(IY-2)                ; 9E+lane
    LD (col_x),A
    LD L,A
.mask_index:
    LD H,HIGH collision_clip_masks
    LD A,(IY+4)                ; A4+lane
    AND (HL)
    LD (col_mask),A
    JR NZ,.group
    ; No enabled repeat mask still leaves the TIA's base P1 copy at X=0.
    LD (col_x),A
    LD A,4
    LD (col_mask),A
.group:
    CALL collision_enemy_ball_group
    ; All P0/M0 contact lies inside the source player's nonzero row bounds. Skip
    ; groups outside its vertical window, while retaining their ball latches.
    LD A,(col_overlap)
    OR A
    JR Z,.next_lane
.copies:
    LD A,4
    LD (col_copy),A
.copy:
    LD B,A
    LD A,(col_mask)
    AND B
    CALL NZ,collision_enemy
    LD A,(col_x)
    ADD A,16
    LD (col_x),A
    LD A,(col_copy)
    SRL A
    LD (col_copy),A
    JR NZ,.copy
.next_lane:
    DEC IY
    LD A,(col_lane)
    DEC A
    JP P,.lane
    IFDEF COLLISION_CORRUPT
    LD A,($C0B6)
    XOR 1
    LD ($C0B6),A
    ENDIF
    RET
.projection:
    LD L,A
    LD H,0
    LD E,L
    LD D,H
    ADD HL,HL
    ADD HL,DE                 ; index*3
    DUP 4
    ADD HL,HL                 ; index*48
    EDUP
    LD DE,collision_projections
    ADD HL,DE
    RET

collision_enemy_ball_group:
    LD A,(col_ball_x)
    LD HL,col_x
    SUB (HL)
    LD C,0
    RL C
    ADD A,7
    CP 48
    JR C,.group_delta
    LD B,A
    LD A,(col_x)
    CP 160
    LD A,B
    JR NC,.positive
    BIT 0,C
    JR Z,.positive
    ADD A,160
    JR .wrapped
.positive:
    SUB 160
.wrapped:
    CP 48
    RET NC
.group_delta:
    LD C,A
    RRCA
    RRCA
    RRCA
    RRCA
    AND 3
    LD E,A
    LD D,0
    LD HL,collision_copy_masks
    ADD HL,DE
    LD A,(col_mask)
    AND (HL)
    RET Z
    LD A,C
    AND 15
    LD C,A
    AND 7
    LD L,A
    LD H,0
    LD DE,collision_bit_masks
    ADD HL,DE
    LD B,(HL)
    LD HL,(col_bits)
    BIT 3,C
    JR Z,.low
    LD L,H
.low:
    LD A,L
    AND B
    RET Z
    LD A,(col_lane)
    LD E,A
    LD D,0
    LD HL,$C0B0
    ADD HL,DE
    LD (HL),A
    RET

collision_enemy:
    LD A,(col_x)
    LD C,15
    CALL collision_player
    JR Z,.no_player
    LD A,(col_lane)
    LD ($C0B5),A
.no_player:
    ; M0 has one enabled raster line at E1+40 and width8, including X=0.
    LD A,7
    LD HL,col_dy
    SUB (HL)
    CP 15
    RET NC
    LD E,A
    LD D,0
    LD HL,(col_shape)
    OR A
    SBC HL,DE
    LD B,(HL)
    PUSH BC
    LD A,(col_x)
    LD HL,$C0E7
    SUB (HL)
    CALL collision_dx
    POP BC
    RET NC
    LD C,A
    LD A,(col_reflect)
    OR A
    LD A,C
    JR Z,.missile_mask
    LD A,14
    SUB C
.missile_mask:
    LD L,A
    LD H,0
    LD DE,collision_missile_masks
    ADD HL,DE
    LD A,(HL)
    AND B
    RET Z
    LD A,(col_lane)
    LD ($C0B4),A
    RET

; A is signed object-X separation modulo256. Normalize the circular160px TIA.
; Carry means valid [-7..7], returned A indexes that interval.
collision_dx:
    JR NC,.positive
    ADD A,7
    CP 15
    RET C
    ADD A,160
    CP 15
    RET
.positive:
    ADD A,7
    CP 15
    RET C
    SUB 160
    CP 15
    RET

; A otherX; C height; col_shape points at its first row (descending ROM order).
; Projection includes doubled player pixels; reflect the projection for REFP1.
collision_player:
    LD B,A
    LD A,(col_dy)
    OR A
    JP M,.check_above
    LD HL,col_height
    CP (HL)
    JP NC,.miss
    JR .vertical_valid
.check_above:
    NEG
    CP C
    JP NC,.miss
.vertical_valid:
    LD A,B
    LD HL,$C0C6
    SUB (HL)
    ADD A,7
    CP 23
    JP NC,.miss
    LD E,A
    LD A,(col_proj+1)
    OR A
    JR NZ,.projection_ready
    PUSH BC
    PUSH DE
    CALL acquire_contacts.ensure_projection
    POP DE
    POP BC
.projection_ready:
    LD A,(col_reflect)
    OR A
    LD HL,(col_proj)
    JR Z,.project
    LD HL,(col_mirror)
    LD A,22
    SUB E
    LD E,A
.project:
    LD D,0
    ADD HL,DE
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD HL,(col_shape)
    LD A,(col_dy)
    OR A
    JP M,.above
    LD B,A
    ADD A,E
    LD E,A
    JR NC,.no_carry
    INC D
.no_carry:
    LD A,(col_height)
    SUB B
    JR .count
.above:
    NEG
    CP C
    JR NC,.miss
    LD B,A
    LD A,L
    SUB B
    LD L,A
    JR NC,.no_borrow
    DEC H
.no_borrow:
    LD A,C
    SUB B
    LD C,A
    LD A,(col_height)
.count:
    CP C
    JR C,.short
    LD A,C
.short:
    LD B,A
.rows:
    LD A,(DE)
    AND (HL)
    RET NZ
    INC DE
    DEC HL
    DJNZ .rows
.miss:
    XOR A
    RET

collision_lane_tops:
    DB 137,113,89,65
collision_copy_masks:
    DB 4,2,1
collision_bit_masks:
    DB 1,2,4,8,16,32,64,128
collision_missile_masks:
    DB 1,3,7,15,31,63,127,255,254,252,248,240,224,192,128

    INCLUDE "../outputs/collision/masks.inc"
    ALIGN 256
collision_clip_masks:
    INCBIN "../outputs/collision/clip-masks.bin"

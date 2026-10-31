; Original-derived ROM data are generated locally. Resident patterns never
; change. Edge variants upload into the bank NOT referenced by the current SAT.
original_sprite_id:
    CP SPRITE_RESIDENT
    JR C,.resident
    PUSH BC
    LD L,A
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    LD DE,original_sprite_catalog
    ADD HL,DE
    PUSH HL
    LD A,(cache_page)
    XOR 64
    RRCA
    RRCA
    RRCA
    ADD A,SPRITE_RESIDENT
    ADD A,C
    ADD A,A
    ADD A,A
    LD (IX+2),A
    ; A is physical pattern*4. Build 3800 + A*8 directly in DE,
    ; avoiding a second general 16-bit multiply and base addition.
    LD D,7
    DUP 3
    ADD A,A
    RL D
    EDUP
    LD E,A
    POP HL
    LD B,32
    CALL vram_copy_short
    POP BC
    RET
.resident:
    ADD A,A
    ADD A,A
    LD (IX+2),A
    RET

; A = canonical X. Return index0/1 for normal parity, 2..8 for edge X153..159.
original_edge_index:
    CP 153
    JR NC,.edge
    AND 1
    RET
.edge:
    SUB 151
    CP 9
    RET C
    XOR A
    RET

prepare_original_sprites:
    LD A,($C0E1)
    OR A
    JP Z,.hide_player
    LD A,($C0C6)
    CP 160
    JP NC,.hide_player
    LD A,($C0D6)
    AND 8
    RRCA
    RRCA
    RRCA
    LD C,A
    LD A,($C0E9)
    OR A
    JR Z,.normal_player
    CP 15
    JR NC,.normal_player
    CP 10
    JR NC,.explosion_frame
    LD A,10
.explosion_frame:
    SUB 10
    ADD A,A
    ADD A,C
    ADD A,6
    JR .player_index
.normal_player:
    LD A,($C0E0)
    CP 3
    JR C,.valid_frame
    XOR A
.valid_frame:
    LD B,A
    LD A,C
    ADD A,A
    ADD A,C
    ADD A,B
.player_index:
    LD B,A
    LD H,0
    LD L,A
    ADD HL,HL
    LD A,($C0E1)
    SUB 13
    CP 11
    JR C,.surface
    LD DE,player_images
    ADD HL,DE
    JR .player_ready
.surface:
    PUSH AF
    LD DE,surface_pointers
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
    POP AF
    ADD A,A
    LD E,A
    LD D,0
    ADD HL,DE
.player_ready:
    LD IX,SATBUF
    LD C,0
    LD A,(HL)
    PUSH HL
    CALL original_sprite_id
    POP HL
    INC HL
    LD IX,SATBUF+4
    INC C
    LD A,(HL)
    CALL original_sprite_id
    JR .player_color
.hide_player:
    LD A,216
    LD (SATBUF),A
    LD (SATBUF+4),A
    XOR A
    LD (SATBUF+2),A
    LD (SATBUF+6),A
.player_color:
    IFDEF WITH_PALETTE
    LD A,($C0E9)
    OR A
    JR NZ,.source_player_color
    LD A,($C0B7)
    ADD A,3
    ADD A,LOW HUD_ROLES
    LD L,A
    LD H,HIGH HUD_ROLES
    LD A,(HL)
    JR .ready_color
.source_player_color:
    ENDIF
    LD A,($C0B7)
    AND 1
    LD E,A
    LD D,0
    IFDEF WITH_PALETTE
    LD HL,sprite_player_colors
    ELSE
    LD HL,original_rom+$CF3
    ENDIF
    ADD HL,DE
    LD A,($C085)
    XOR (HL)
    LD B,A
    LD A,($C086)
    AND B
    LD B,A
    LD A,($C0E9)
    OR A
    JR Z,.normal_color
    CP 24
    JR C,.death_color
    LD A,23
.death_color:
    LD E,A
    IFDEF WITH_PALETTE
    LD HL,sprite_death_colors
    ELSE
    LD HL,original_rom+$F17
    ENDIF
    ADD HL,DE
    LD B,(HL)
.normal_color:
    LD E,B
    IFDEF WITH_PALETTE
    LD HL,original_tia_to_tms
    ELSE
    LD HL,tia_to_tms
    ENDIF
    ADD HL,DE
    LD A,(HL)
.ready_color:
    LD (SATBUF+3),A
    LD (SATBUF+7),A
    LD (SATBUF+11),A
    LD A,($C0E7)
    OR A
    JR Z,.hide_shot
    CP 160
    JR NC,.hide_shot
    LD A,($C0E1)
    CP 17
    JR C,.hide_shot
    LD A,($C0E7)
    CALL original_edge_index
    LD E,A
    LD D,0
    LD HL,torpedo_images
    ADD HL,DE
    LD A,(HL)
    LD IX,SATBUF+8
    LD C,2
    CALL original_sprite_id
    LD A,($C0E1)
    ADD A,23
    LD (SATBUF+8),A
    JR .balls
.hide_shot:
    LD A,216
    LD (SATBUF+8),A
    XOR A
    LD (SATBUF+10),A
.balls:
    IFDEF WITH_PALETTE
    LD A,(HUD_ROLES+10)
    ELSE
    LD A,($C085)
    IFDEF WITH_PALETTE
    LD HL,sprite_diver_color
    ELSE
    LD HL,original_rom+$CFA
    ENDIF
    XOR (HL)
    LD B,A
    LD A,($C086)
    AND B
    LD E,A
    LD D,0
    IFDEF WITH_PALETTE
    LD HL,original_tia_to_tms
    ELSE
    LD HL,tia_to_tms
    ENDIF
    ADD HL,DE
    LD A,(HL)
    ENDIF
    LD (SATBUF+15),A
    LD (SATBUF+19),A
    LD (SATBUF+23),A
    LD (SATBUF+27),A
    LD IX,SATBUF+12
    LD IY,$C0C7
    LD B,4
    LD C,3
.ball:
    LD A,(IY+0)
    OR A
    JR Z,.hide_ball
    CP 160
    JR NC,.hide_ball
    LD A,(IY+$12)
    AND 15
    DUP 4
    RLCA
    EDUP
    LD L,A
    LD H,HIGH ball_images
    LD A,(IY+0)
    CALL original_edge_index
    LD E,A
    LD D,0
    ADD HL,DE
    LD A,(HL)
    CALL original_sprite_id
    JR .next_ball
.hide_ball:
    LD (IX+0),216
    LD (IX+2),0
.next_ball:
    LD DE,4
    ADD IX,DE
    INC IY
    INC C
    DJNZ .ball
    ; Four four-byte advances already leave IX at the patrol SAT slot.
    LD (IX+3),14
    LD A,($C0F6)
    OR A
    JP Z,.hide_patrol
    CP 160
    JP NC,.hide_patrol
    LD A,($C0E0)
    CP 3
    JR C,.patrol_frame
    XOR A
.patrol_frame:
    LD L,A
    LD H,0
    DUP 4
    ADD HL,HL
    EDUP
    LD DE,patrol_images
    LD A,($C0E9)
    OR A
    JR NZ,.patrol_death
    LD A,($C0BB)
    CP 2
    JR NC,.patrol_table
    JR .patrol_early
.patrol_death:
    CP 10
    JR NC,.patrol_table
.patrol_early:
    LD DE,early_patrol_images
.patrol_table:
    ADD HL,DE
    LD A,($C0F6)
    CALL original_edge_index
    LD E,A
    LD D,0
    ADD HL,DE
    LD A,(HL)
    LD C,7
    CALL original_sprite_id
    RET
.hide_patrol:
    LD (IX+0),216
    LD (IX+2),0
    RET

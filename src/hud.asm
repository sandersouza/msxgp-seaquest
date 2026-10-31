; Source HUD projection. Read-only tables unpack at D000; caches end before F000.
; C510..C5EF class colors, C700..C7FC pair colors, CF00..CFFF presentation state.
HUD_PTRS EQU $CF00
HUD_KEY EQU $CF10
HUD_KEY_VALID EQU $CF12
HUD_PALETTE_DIRTY EQU $CF13
HUD_UNPACK_CURSOR EQU $CF14
HUD_NAME_PAGE EQU $CF16
HUD_COLOR_BANK EQU $CF18
HUD_SIGNIFICANT EQU $CF19
HUD_COLORS_NEEDED EQU $CF1A
HUD_ROLES EQU $CF30
HUD_CLASS_COLORS EQU $C510
HUD_PAIR_COLORS EQU $C700
HUD_FIELD_CACHE EQU $CF80
HUD_ENEMY_COLORS EQU $C480
HUD_ENEMY_SLOTS EQU $C488
HUD_ENEMY_TOP_IDS EQU $C490
HUD_ENEMY_BOTTOM_IDS EQU $C494
HUD_CLASS_SIGNATURES EQU $CFB0
HUD_OXYGEN_SIGNATURE EQU $CFF0
HUD_CLASS_TEMP EQU $CF1C
HUD_PLAYER EQU $CF1D
HUD_ALL_CURRENT EQU $CF1E
HUD_FIRST_FRAME EQU $CF1F
HUD_PAIRS_BASE EQU $CF20
HUD_SINGLE_BASE EQU $CF22
HUD_LIVES_BASE EQU $CF24
HUD_PREVIOUS_SCORE EQU $CF26
HUD_PREVIOUS_LIVES EQU $CF29
HUD_PREVIOUS_DIVERS EQU $CF2A
HUD_PREVIOUS_LOGO EQU $CF2B
HUD_PREVIOUS_OXYGEN EQU $CF2C
HUD_ATTR EQU $C490
HUD_ATTR_SP EQU $C4C0
HUD_WATER_CURRENT EQU $C4C2
HUD_WATER_DIRTY EQU $C4C3
HUD_WATER_ATTR EQU $C4D0
HUD_FONT_SOURCES EQU $C4D8
HUD_SCORE_NAMES0 EQU $C4E0
HUD_SCORE_NAMES1 EQU $C4E9
HUD_SCORE_SOURCE_PTRS EQU $C4F2
HUD_FONT_BANK EQU $C4F8
HUD_SCORE_CHANGED EQU $C4F9

    MACRO hud_store_pointer offset
    LD DE,(HUD_PTRS+offset)
    LD A,L
    XOR E
    JR NZ,1F
    LD A,H
    XOR D
    JR Z,2F
1:
    LD A,1
    LD (HUD_COLORS_NEEDED),A
2:
    LD (HUD_PTRS+offset),HL
    ENDM

hud_init:
    LD A,($F3E0)
    AND $BF
    LD ($F3E0),A
    OUT ($99),A
    LD A,$81
    OUT ($99),A
    LD HL,hud_packed
    LD DE,$D000
    CALL hud_unpack
    XOR A
    LD HL,hud_top_cache
    LD DE,hud_top_cache+1
    LD BC,1023
    LD (HL),A
    LDIR
    LD HL,HUD_PTRS
    LD DE,HUD_PTRS+1
    LD BC,255
    LD (HL),A
    LDIR
    XOR A                       ; name-table high-byte offset0/4
    LD (HUD_NAME_PAGE),A
    LD A,255
    LD (HUD_PLAYER),A
    LD HL,HUD_PREVIOUS_SCORE
    LD DE,HUD_PREVIOUS_SCORE+1
    LD BC,7
    LD (HL),A
    LDIR
    LD HL,$FF00
    LD (HUD_KEY),HL
    LD HL,hud_default_roles
    LD DE,HUD_ROLES
    LD BC,HUD_ROLE_COUNT
    LDIR
    CALL hud_build_colors
    CALL hud_enemy_init
    ; The banked renderer streams ROM patterns, so CC00's old staging page is
    ; free. Predecode each source hue's normal slot*8;255 selects the fallback.
    LD HL,tia_to_tms
    LD DE,$CC00
.enemy_slots:
    PUSH HL
    LD L,(HL)
    LD H,0
    LD BC,enemy_normal_slots
    ADD HL,BC
    LD A,(HL)
    CP 255
    JR Z,.enemy_slot_ready
    ADD A,A
    ADD A,A
    ADD A,A
.enemy_slot_ready:
    POP HL
    LD (DE),A
    INC HL
    INC E
    JR NZ,.enemy_slots
    LD HL,$1414                 ; normal black foreground / blue water
    DUP 4,enemy_pair
    LD (HUD_ENEMY_COLORS+enemy_pair*2),HL
    EDUP
    XOR A
    LD (HUD_FONT_BANK),A
    LD HL,0
    DUP 3,font_source_pair
    LD (HUD_FONT_SOURCES+font_source_pair*2),HL
    EDUP
    LD (HUD_WATER_CURRENT),A
    LD (HUD_WATER_DIRTY),A
    CALL hud_prepare_water
    CALL hud_commit_water
    LD A,1
    LD (HUD_ALL_CURRENT),A
    LD (HUD_FIRST_FRAME),A
    LD HL,hud_oxygen_label
    LD (HUD_PTRS+14),HL
    XOR A
    LD (HUD_COLOR_BANK),A
    LD HL,hud_top_records
    LD B,HUD_TOP_COUNT
    LD C,0
    CALL hud_load_patterns
    LD A,$10
    LD (HUD_COLOR_BANK),A
    LD HL,hud_bottom_records
    LD B,HUD_BOTTOM_COUNT
    LD C,$10
    CALL hud_load_patterns
    LD HL,hud_background_names
    LD DE,$1800
    LD BC,768
    CALL vram_copy
    LD HL,hud_background_names
    LD DE,$1C00
    LD BC,768
    CALL vram_copy
    LD HL,hud_border_pattern
    LD DE,$3FE0
    LD B,32
    CALL vram_copy_short
    LD A,208
    LD (SATBUF+36),A
    LD HL,SATBUF+36
    LD DE,$1B24
    LD B,1
    CALL vram_copy_short
    RET

hud_unpack:
    LD A,(HL)
    INC HL
    OR A
    RET Z
    BIT 7,A
    JR NZ,.match
    LD C,A
    LD B,0
    LDIR
    JR hud_unpack
.match:
    AND 127
    ADD A,3
    LD C,A
    LD B,0
    LD A,(HL)
    INC HL
    PUSH DE
    LD E,A
    LD D,(HL)
    INC HL
    LD (HUD_UNPACK_CURSOR),HL
    EX DE,HL
    POP DE
    LDIR
    LD HL,(HUD_UNPACK_CURSOR)
    JR hud_unpack

hud_load_patterns:
    PUSH BC
    LD A,(HL)
    INC HL
    PUSH HL
    LD E,A
    LD D,0
    DUP 3
    SLA E
    RL D
    EDUP
    LD A,D
    OR C
    LD D,A
    POP HL
    LD B,8
    CALL vram_copy_short
    PUSH HL
    POP IX
    POP BC
    PUSH BC
    LD A,(IX-9)                 ; record ID precedes eight pattern bytes
    LD C,A
    CALL hud_tile_colors
    PUSH IX
    POP HL
    INC HL                      ; skip the class ID after eight pattern bytes
    POP BC
    DJNZ hud_load_patterns
    RET

hud_prepare_palette:
    LD A,($C085)
    LD L,A
    LD A,($C086)
    LD H,A
    LD DE,(HUD_KEY)
    OR A
    SBC HL,DE
    LD A,(HUD_KEY_VALID)
    JR NZ,.new_palette
    LD A,H
    OR L
    RET Z
.new_palette:
    ADD HL,DE
    LD (HUD_KEY),HL
    XOR A
    LD (HUD_KEY_VALID),A
    INC A
    LD (HUD_PALETTE_DIRTY),A
    LD (HUD_COLORS_NEEDED),A
    XOR A
    LD (HUD_ALL_CURRENT),A
    LD A,($C085)
    LD C,A
    EXX
    LD H,HIGH tia_to_tms
    LD A,($C086)
    LD C,A
    EXX
    LD HL,hud_role_sources
    LD DE,HUD_ROLES
    LD B,HUD_ROLE_COUNT
.role:
    LD A,(HL)
    INC HL
    XOR C
    EXX
    AND C
    LD L,A
    LD A,(HL)
    EXX
    LD (DE),A
    INC DE
    DJNZ .role
    LD A,($C0B7)
    LD L,A
    LD H,0
    LD DE,original_rom+$CF0
    ADD HL,DE
    LD A,($C085)
    XOR (HL)
    LD B,A
    LD A,($C086)
    AND B
    LD L,A
    LD H,HIGH tia_to_tms
    LD A,(HL)
    LD (HUD_ROLES+12),A
    JP hud_build_colors

hud_prepare:
    XOR A
    LD (HUD_COLORS_NEEDED),A
    LD (HUD_SCORE_CHANGED),A
    CALL hud_prepare_palette
    CALL hud_prepare_water
    CALL hud_player_bases
    LD HL,HUD_PREVIOUS_SCORE
    DUP 3,score_byte
    LD A,($C0B8+score_byte)
    CP (HL)
    JP NZ,.score_changed
    INC HL
    EDUP
    JP .score_ready
.score_changed:
    LD A,1
    LD (HUD_SCORE_CHANGED),A
    LD HL,($C0B8)
    LD (HUD_PREVIOUS_SCORE),HL
    LD A,($C0BA)
    LD (HUD_PREVIOUS_SCORE+2),A
    XOR A
    LD (HUD_SIGNIFICANT),A
    DUP 3,digit_pair
    LD A,($C0B8+digit_pair)
    LD B,A
    OR A
    JR NZ,1F
    LD A,(HUD_SIGNIFICANT)
    OR A
    JR NZ,2F
    IF digit_pair < 2
    LD HL,hud_blank_pair
    JR 4F
    ELSE
    LD HL,(HUD_SINGLE_BASE)
    JR 4F
    ENDIF
1:
    LD A,(HUD_SIGNIFICANT)
    OR A
    JR NZ,2F
    LD A,1
    LD (HUD_SIGNIFICANT),A
    LD A,B
    AND $F0
    JR NZ,2F
    LD A,B
    AND 15
    LD DE,(HUD_SINGLE_BASE)
    JR 3F
2:
    LD A,B
    AND 15
    LD C,A
    LD A,B
    DUP 4
    RRCA
    EDUP
    AND 15
    LD B,A
    ADD A,A
    ADD A,A
    ADD A,B
    ADD A,A
    ADD A,C
    CP 100
    JR C,5F
    XOR A                       ; only valid BCD is a source HUD contract
5:
    LD DE,(HUD_PAIRS_BASE)
3:
    LD L,A
    LD H,0
    LD B,H
    LD C,L
    ADD HL,HL
    LD A,(HUD_PLAYER)
    OR A
    JR Z,7F
    ADD HL,HL
    JR 8F
7:
    ADD HL,BC
8:
    ADD HL,DE
4:
    LD (HUD_SCORE_SOURCE_PTRS+digit_pair*2),HL
    hud_store_pointer digit_pair*2
    EDUP
.score_ready:
    LD A,(HUD_PLAYER)
    OR A
    JR Z,.font_ready
    LD A,(HUD_SCORE_CHANGED)
    OR A
    CALL NZ,hud_prepare_player2_score
.font_ready:
    LD A,($C0BB)
    LD HL,HUD_PREVIOUS_LIVES
    CP (HL)
    JR Z,.lives_ready
    LD (HL),A
    CALL hud_count9
    LD DE,(HUD_LIVES_BASE)
    ADD HL,DE
    hud_store_pointer 6
.lives_ready:
    LD A,($C0BE)
    CP 6
    JR NZ,.diver_count
    LD A,($C0E1)
    CP 13
    LD A,6
    JR Z,.diver_count
    LD A,($C081)
    AND 8
    LD A,6
    JR NZ,.diver_count
    XOR A
.diver_count:
    LD HL,HUD_PREVIOUS_DIVERS
    CP (HL)
    JR Z,.divers_ready
    LD (HL),A
    CALL hud_count9
    ADD HL,HL
    LD DE,hud_divers
    ADD HL,DE
    hud_store_pointer 8
.divers_ready:
    LD A,($C0A3)
    DUP 3
    SRL A
    EDUP
    CP 20
    JR NC,.activision
    CP 12
    JR C,.seaquest
    SUB 11                      ; source8..15 -> table1..8
    JR .logo_index
.activision:
    LD A,8
    JR .logo_index
.seaquest:
    XOR A
.logo_index:
    LD HL,HUD_PREVIOUS_LOGO
    CP (HL)
    JR Z,.logo_ready
    LD (HL),A
    LD L,A
    LD H,0
    LD E,A
    LD D,H
    DUP 3
    ADD HL,HL
    EDUP
    ADD HL,DE
    LD DE,hud_logo
    ADD HL,DE
    hud_store_pointer 10
.logo_ready:
    LD A,($C0E6)
    CP 65
    JR C,.oxygen_count
    LD A,64
.oxygen_count:
    LD B,A
    LD A,($C0E1)
    CP 13
    JR Z,.oxygen_ready
    LD A,($C0E9)
    OR A
    JR NZ,.oxygen_ready
    LD A,($C0E6)
    DEC A
    CP 16
    JR NC,.oxygen_ready
    LD A,($C081)
    AND 16
    JR NZ,.oxygen_ready
    LD A,B
    ADD A,65
    LD B,A
.oxygen_ready:
    LD A,B
    LD HL,HUD_PREVIOUS_OXYGEN
    CP (HL)
    JR Z,.oxygen_pointer_ready
    LD (HL),A
    LD L,A
    LD H,0
    LD E,A
    LD D,H
    ADD HL,HL
    ADD HL,HL
    LD B,H
    LD C,L
    ADD HL,HL
    ADD HL,BC
    ADD HL,DE                   ; thirteen names per gauge; lettering is shared
    LD DE,hud_oxygen
    ADD HL,DE
    hud_store_pointer 12
.oxygen_pointer_ready:
    LD A,216
    LD (SATBUF+32),A
    LD A,($C0E6)
    DEC A
    CP 4
    JR NC,.border_ready
    LD A,151
    LD (SATBUF+32),A
.border_ready:
    LD A,80
    LD (SATBUF+33),A
    LD A,252
    LD (SATBUF+34),A
    LD A,(HUD_ROLES+8)
    LD (SATBUF+35),A
    LD A,(HUD_NAME_PAGE)
    XOR 4
    LD (HUD_NAME_PAGE),A
    RET

hud_player_bases:
    LD A,($C0B7)
    LD HL,HUD_PLAYER
    CP (HL)
    RET Z
    LD (HL),A
    LD HL,hud_pairs
    LD DE,hud_single
    LD BC,hud_lives
    OR A
    JR Z,.bases
    LD HL,hud_pairs1
    LD DE,hud_single1
    LD BC,hud_lives1
.bases:
    LD (HUD_PAIRS_BASE),HL
    LD (HUD_SINGLE_BASE),DE
    LD (HUD_LIVES_BASE),BC
    LD A,255
    LD HL,HUD_PREVIOUS_SCORE
    LD (HL),A
    INC HL
    LD (HL),A
    INC HL
    LD (HL),A
    INC HL
    LD (HL),A
    RET

; Two three-tile scratch sets hold only nonresident middle-pair bitmaps for
; player2. At most three8-byte patterns change, always outside the visible set.
hud_prepare_player2_score:
    LD A,(HUD_FONT_BANK)
    XOR 1
    LD (HUD_FONT_BANK),A
    DUP 3,font_pair
    LD HL,(HUD_SCORE_SOURCE_PTRS+font_pair*2)
    LD DE,HUD_SCORE_NAMES0+font_pair*3
    LD A,(HUD_FONT_BANK)
    OR A
    JR Z,1F
    LD DE,HUD_SCORE_NAMES1+font_pair*3
1:
    DUP 3
    LDI
    EDUP
    DEC DE
    DEC DE
    LD A,(DE)
    OR A
    JR NZ,3F
    LD A,(HL)                  ; source atlas ID stored after the three names
    LD C,A
    LD A,(HUD_FONT_BANK)
    LD B,A
    ADD A,A
    ADD A,B
    ADD A,font_pair
    LD B,A
    ADD A,HUD_FONT_SCRATCH_FIRST
    LD (DE),A
    LD A,B
    ADD A,LOW HUD_FONT_SOURCES
    LD L,A
    LD H,HIGH HUD_FONT_SOURCES
    LD A,C
    CP (HL)
    JR Z,3F
    LD (HL),A
    SUB HUD_FONT_SOURCE_FIRST
    LD L,A
    LD H,0
    ADD HL,HL
    LD B,H
    LD C,L
    ADD HL,HL
    ADD HL,HL
    ADD HL,BC
    LD DE,hud_top_records+1
    ADD HL,DE                  ; source8-byte pattern, no target VRAM readback
    PUSH HL
    LD A,(HUD_FONT_BANK)
    LD B,A
    ADD A,A
    ADD A,B
    ADD A,HUD_FONT_SCRATCH_FIRST+font_pair
    LD E,A
    LD D,0
    DUP 3
    SLA E
    RL D
    EDUP
    POP HL
    LD B,8
    CALL vram_copy_short
3:
    LD HL,HUD_SCORE_NAMES0+font_pair*3
    LD A,(HUD_FONT_BANK)
    OR A
    JR Z,4F
    LD HL,HUD_SCORE_NAMES1+font_pair*3
4:
    hud_store_pointer font_pair*2
    EDUP
    RET

hud_count9:
    CP 7
    JR C,.valid
    LD A,6
.valid:
    LD L,A
    LD H,0
    LD E,A
    LD D,H
    DUP 3
    ADD HL,HL
    EDUP
    ADD HL,DE
    RET

hud_show:
    LD A,(HUD_FIRST_FRAME)
    OR A
    RET Z
    XOR A
    LD (HUD_FIRST_FRAME),A
    LD A,($F3E0)
    OR $40
    LD ($F3E0),A
    OUT ($99),A
    LD A,$81
    OUT ($99),A
    RET

; Only the inactive name table changes during the active picture.
hud_upload_names:
    DUP 3,hud_segment_index
    LD HL,(HUD_PTRS+2*hud_segment_index)
    LD DE,$180C+3*hud_segment_index
    LD B,3
    CALL hud_name_copy
    EDUP
    LD HL,(HUD_PTRS+6)
    LD DE,$182C
    LD B,9
    CALL hud_name_copy
    LD HL,(HUD_PTRS+8)
    LD DE,$1A8C
    LD B,9
    CALL hud_name_copy
    LD HL,(HUD_PTRS+8)
    LD BC,9
    ADD HL,BC
    LD DE,$1AAC
    LD B,9
    CALL hud_name_copy
    LD HL,(HUD_PTRS+10)
    LD DE,$1ACC
    LD B,9
    CALL hud_name_copy
    LD HL,(HUD_PTRS+12)
    LD DE,$1A69
    LD B,13
    CALL hud_name_copy
    LD HL,(HUD_PTRS+14)
    LD DE,$1A63
    LD B,6
    JP hud_name_copy
hud_name_copy:
    LD A,(HUD_NAME_PAGE)
    ADD A,D
    LD D,A
    JP vram_copy_short

hud_commit:
    CALL hud_commit_fields
    JP hud_commit_ripple
hud_commit_fields:
    LD A,(HUD_NAME_PAGE)
    RRCA
    RRCA
    ADD A,6
    OUT ($99),A
    LD ($F3E1),A
    LD A,$82
    OUT ($99),A
    CALL hud_commit_water
    LD A,(HUD_ALL_CURRENT)
    OR A
    RET NZ
    LD A,(HUD_COLORS_NEEDED)
    OR A
    RET Z
    LD IY,HUD_FIELD_CACHE
    XOR A
    LD (HUD_COLOR_BANK),A
    DUP 4,field
    LD HL,(HUD_PTRS+field*2)
    IF field==3
    LD B,9
    ELSE
    LD B,3
    ENDIF
    LD DE,(HUD_CLASS_SIGNATURES+2*HUD_SCORE_CLASS0)
    LD A,($C0B7)
    OR A
    JR Z,1F
    LD DE,(HUD_CLASS_SIGNATURES+2*HUD_SCORE_CLASS1)
1:
    CALL hud_field_colors
    EDUP
    LD A,$10
    LD (HUD_COLOR_BANK),A
    LD HL,(HUD_PTRS+8)
    LD B,18
    LD DE,(HUD_CLASS_SIGNATURES+HUD_DIVER_CLASS*2)
    CALL hud_field_colors
    LD HL,(HUD_PTRS+10)
    LD B,9
    LD DE,(HUD_CLASS_SIGNATURES+HUD_LOGO_CLASS*2)
    CALL hud_field_colors
    LD HL,(HUD_PTRS+12)
    LD B,13
    LD DE,(HUD_OXYGEN_SIGNATURE)
    CALL hud_field_colors
    LD HL,(HUD_PTRS+14)
    LD B,6
    LD DE,(HUD_OXYGEN_SIGNATURE)
    CALL hud_field_colors
    XOR A
    LD (HUD_COLOR_BANK),A
    LD HL,hud_background_top
    LD B,HUD_BACKGROUND_TOP_COUNT
    LD DE,(HUD_KEY)
    CALL hud_field_colors
    LD A,$10
    LD (HUD_COLOR_BANK),A
    LD HL,hud_background_bottom
    LD B,HUD_BACKGROUND_BOTTOM_COUNT
    LD DE,(HUD_KEY)
    CALL hud_field_colors
    RET

; Original surface rows45..54 rotate source82 before testing bit1. SCREEN2
; rows29/30 both project raw45; opaque background tiles253/254 have zero bits,
; so only the low color nibble matters. Normal blue maps both hues identically.
hud_commit_ripple:
    LD A,(HUD_ROLES+2)
    LD E,A
    LD A,(HUD_ROLES+HUD_RIPPLE_ROLE)
    CP E
    RET Z
    LD D,A
    LD A,($C082)
    LD C,A
    LD HL,$C4A0
    RLC C
    CALL .color
    LD (HL),A
    INC HL
    LD (HL),A
    INC HL
    LD B,9
.row:
    RLC C
    CALL .color
    LD (HL),A
    INC HL
    DJNZ .row
    LD HL,$C4A0
    LD DE,$27ED                 ; tile253 row5, three projected water rows
    LD B,3
    CALL vram_copy_short
    LD HL,$C4A3
    LD DE,$27F0                 ; tile254, eight projected water rows
    LD B,8
    JP vram_copy_short
.color:
    LD A,E
    BIT 1,C
    RET Z
    LD A,D
    RET

hud_prepare_water:
    LD A,(HUD_ROLES+2)
    LD B,A
    DUP 4
    RLCA
    EDUP
    OR B
    LD HL,HUD_WATER_CURRENT
    CP (HL)
    RET Z
    LD (HL),A
    LD H,A
    LD L,A
    DUP 4,water_pair
    LD (HUD_WATER_ATTR+2*water_pair),HL
    EDUP
    LD A,1
    LD (HUD_WATER_DIRTY),A
    RET
hud_commit_water:
    LD A,(HUD_WATER_DIRTY)
    OR A
    RET Z
    XOR A
    LD (HUD_WATER_DIRTY),A
    DUP 3,water_bank
    LD HL,HUD_WATER_ATTR
    LD DE,$2000+$800*water_bank
    LD B,8
    CALL vram_copy_short
    EDUP
    RET

; Attributes are transferred only into the inactive enemy cache. AC already
; contains the source-ordered old-phase hue; do not recompute from new D9/BD.
hud_prepare_enemy_colors:
    DUP 4,enemy_lane
    LD A,($C0AC+enemy_lane)
    LD L,A
    LD H,$CC
    LD B,(HL)
    LD A,(HUD_ROLES+2)
    CP 4
    JR NZ,2F
    LD A,B
    OR A
    JR Z,2F
    CP 255
    JR NZ,3F
2:
    LD A,($C0AC+enemy_lane)
    LD L,A
    LD H,HIGH tia_to_tms
    LD A,(HL)
    LD B,A
    DUP 4
    RLCA
    EDUP
    LD C,A
    LD A,(HUD_ROLES+2)
    OR C
    LD C,A
    XOR A
3:
    LD (HUD_ENEMY_SLOTS+enemy_lane),A
    LD B,A
    LD A,(cache_page)
    RLCA
    RLCA
    ADD A,B
    ADD A,enemy_lane*2
    LD L,A
    LD H,0
    LD DE,enemy_top_ids
    ADD HL,DE
    LD A,(HL)
    LD (HUD_ENEMY_TOP_IDS+enemy_lane),A
    LD DE,48
    ADD HL,DE
    LD A,(HL)
    LD (HUD_ENEMY_BOTTOM_IDS+enemy_lane),A
    LD A,(HUD_ENEMY_SLOTS+enemy_lane)
    OR A
    JR NZ,1F
    LD A,(cache_page)
    DUP 4
    RRCA
    EDUP
    ADD A,LOW(HUD_ENEMY_COLORS+enemy_lane)
    LD L,A
    LD H,HIGH HUD_ENEMY_COLORS
    LD A,C
    CP (HL)
    JR Z,1F
    LD (HL),A
    LD A,(HUD_ENEMY_TOP_IDS+enemy_lane)
    LD E,A
    LD D,0
    DUP 3
    SLA E
    RL D
    EDUP
    LD A,D
    IF enemy_lane==3
    OR $20
    ELSE
    OR $28
    ENDIF
    LD D,A
    IF enemy_lane==0
    LD A,C
    CALL hud_fill24
    LD A,(HUD_ENEMY_BOTTOM_IDS+enemy_lane)
    LD E,A
    LD D,0
    DUP 3
    SLA E
    RL D
    EDUP
    LD A,D
    OR $30
    LD D,A
    LD A,C
    CALL hud_fill24
    ELSE
    LD A,C
    CALL hud_fill48
    ENDIF
1:
    EDUP
    RET

; Constant data has the same29-cycle spacing as OUTI/JP. INC HL is a register
; delay only:12-cycleOUT +7-cycleINC +two5-cycleNOPs on standard MSX Z80.
hud_fill48:
    CALL hud_fill_address
    DUP 24
    OUT ($98),A
    INC HL
    NOP
    NOP
    EDUP
    JR hud_fill_tail24
hud_fill24:
    CALL hud_fill_address
hud_fill_tail24:
    DUP 24
    OUT ($98),A
    INC HL
    NOP
    NOP
    EDUP
    RET
hud_fill_address:
    PUSH AF
    LD A,E
    OUT ($99),A
    LD A,D
    OR $40
    OUT ($99),A
    POP AF
    RET

; A field needs checking only after its vector or source palette changes.
hud_field_colors:
    LD A,(IY+0)
    CP L
    JR NZ,.changed
    LD A,(IY+1)
    CP H
    JR NZ,.changed
    LD A,(IY+2)
    CP E
    JR NZ,.changed
    LD A,(IY+3)
    CP D
    JR Z,.done
.changed:
    LD (IY+0),L
    LD (IY+1),H
    LD (IY+2),E
    LD (IY+3),D
.tile:
    PUSH BC
    PUSH HL
    LD A,(HL)
    LD C,A
    CALL hud_tile_colors
    POP HL
    INC HL
    POP BC
    DJNZ .tile
.done:
    LD DE,4
    ADD IY,DE
    RET

; C=tile ID; only actual mapped colors invalidate the resident color cache.
hud_tile_colors:
    LD L,C
    LD H,0
    LD DE,hud_top_class_ids
    LD A,(HUD_COLOR_BANK)
    OR A
    JR Z,.class_id
    LD DE,hud_bottom_class_ids
.class_id:
    ADD HL,DE
    LD A,(HL)
    LD (HUD_CLASS_TEMP),A
    ADD A,A
    LD L,A
    LD H,0
    LD DE,HUD_CLASS_SIGNATURES
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    PUSH DE
    LD L,C
    LD H,0
    ADD HL,HL
    LD DE,hud_top_cache
    LD A,(HUD_COLOR_BANK)
    OR A
    JR Z,.cache
    LD DE,hud_bottom_cache
.cache:
    ADD HL,DE
    POP DE
    LD A,(HL)
    CP E
    JR NZ,.update
    INC HL
    LD A,(HL)
    CP D
    RET Z
    DEC HL
.update:
    LD (HL),E
    INC HL
    LD (HL),D
    LD A,(HUD_CLASS_TEMP)
    ADD A,A
    ADD A,A
    ADD A,A
    ADD A,LOW HUD_CLASS_COLORS
    LD L,A
    LD H,HIGH HUD_CLASS_COLORS
    JR NC,1F
    INC H
1:
    PUSH HL
    LD L,C
    LD H,0
    DUP 3
    ADD HL,HL
    EDUP
    LD A,(HUD_COLOR_BANK)
    ADD A,$20
    OR H
    LD D,A
    LD E,L
    POP HL
    LD B,8
    JP vram_copy_short

hud_border_pattern:
    DB 0,$80,$80,$80,$80
    DS 27,0

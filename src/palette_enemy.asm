; Global exact RGBA-to-slot map. Only fully warmed, unreferenced slots enter
; CC00. Slot0 can fall back to independent per-lane/per-cache colour updates.
PAL_GLOBAL_COLORS EQU $C4A0
PAL_LANE_READY EQU $C4AC
PAL_FUTURE_COLORS EQU $C4B0
PAL_FUTURE_COUNTER EQU $C4B4
PAL_FUTURE_MASK EQU $C4B5
PAL_FUTURE_XOR EQU $C4B6
PAL_FUTURE_NEW_MASK EQU $C4B7
PAL_FUTURE_BACKGROUND EQU $C4B8
PAL_FUTURE_WAVE EQU $C4B9
PAL_WARM_SLOT EQU $C6E0
PAL_WARM_CHUNK EQU $C6E1
PAL_WARM_RGB EQU $C6E2
PAL_FONT_UID EQU $C4BA
PAL_FONT_PLAYER EQU $C4BB
PAL_FONT_CURSOR EQU $C4BC
PAL_FONT_LEFT EQU $C4BE
PAL_FONT_BLANK EQU $C4BF
PAL_FONT_WORK EQU $C6E3
PAL_FONT_SOURCE EQU $C6E5

palette_enemy_init:
    LD HL,0
    DUP 4,pair
    LD (HUD_WATER_ATTR+pair*2),HL
    EDUP
    DUP 3,bank
    LD HL,HUD_WATER_ATTR
    LD DE,$2000+bank*$800
    LD B,8
    CALL vram_copy_short
    EDUP
    LD A,255
    LD (PAL_WARM_SLOT),A
    LD ($C2E2),A
    LD ($C2E3),A
    LD (PAL_FONT_UID),A
    LD HL,$CC00
    LD DE,$CC01
    LD BC,255
    LD (HL),A
    LDIR
    XOR A
    LD (PAL_FUTURE_MASK),A
    LD BC,ENEMY_SLOT_COUNT
    LD HL,enemy_normal_rgba
    LD DE,PAL_GLOBAL_COLORS
    LDIR
    LD HL,enemy_normal_rgba
    LD B,ENEMY_SLOT_COUNT
    LD C,0
.slot:
    LD E,(HL)
    LD D,$CC
    LD A,C
    LD (DE),A
    ADD A,8
    LD C,A
    INC HL
    DJNZ .slot
    RET

; The opposite player's font is not displayed during this idle half-period.
; Prewarm its attributes (not its patterns) so phase0's player swap does not
; add work to the period containing the large preceding colour commit.
palette_player_prefetch:
    LD A,($C081)
    CP $C0
    RET C
    LD A,($C0A3)
    OR A
    RET Z
    LD A,($C0E9)
    OR A
    RET NZ
    LD A,($C6D2)
    OR A
    RET Z
    LD A,($C6D1)
    LD HL,PAL_FONT_UID
    CP (HL)
    JR NZ,.start
    LD A,(PAL_CUR_INDEX)
    LD HL,PAL_FONT_SOURCE
    CP (HL)
    JR NZ,.start
    LD A,($C0B7)
    LD HL,PAL_FONT_PLAYER
    CP (HL)
    JR Z,.work
.start:
    LD A,(HUD_ALL_CURRENT)
    OR A
    CALL NZ,palette_stamp_default_memos
    LD A,(PAL_CUR_INDEX)
    LD (PAL_FONT_SOURCE),A
    LD A,($C6D1)
    LD (PAL_FONT_UID),A
    LD A,($C0B7)
    LD (PAL_FONT_PLAYER),A
    OR A
    LD HL,hud_top_records
    LD A,HUD_FONT_P0_COUNT
    JR NZ,.cursor
    LD HL,hud_top_records+10*HUD_FONT_P0_COUNT
    LD A,HUD_FONT_P1_COUNT
.cursor:
    LD (PAL_FONT_CURSOR),HL
    LD (PAL_FONT_LEFT),A
    XOR A
    LD (PAL_FONT_BLANK),A
.work:
    LD A,2
    LD (PAL_FONT_WORK),A
    LD A,(PAL_FONT_BLANK)
    OR A
    JR NZ,.font
    INC A
    LD (PAL_FONT_BLANK),A
    CALL .blank_visible
    JR Z,.next
    LD A,HUD_BLANK_TILE
    LD C,0
    CALL .write
    JR .next
.font:
    LD A,(PAL_FONT_LEFT)
    OR A
    RET Z
    DEC A
    LD (PAL_FONT_LEFT),A
    LD HL,(PAL_FONT_CURSOR)
    LD A,(HL)
    LD DE,10
    ADD HL,DE
    LD (PAL_FONT_CURSOR),HL
    CP HUD_BLANK_TILE
    JR NZ,.ordinary
    CALL .blank_visible
    JR Z,.next
    LD A,HUD_BLANK_TILE
.ordinary:
    LD C,A
    LD A,(PAL_FONT_PLAYER)
    XOR 1
    LD B,A
    LD A,C
    LD C,B
    CALL .write
.next:
    LD HL,PAL_FONT_WORK
    DEC (HL)
    JR NZ,.font
    RET
.blank_visible:
    LD A,HUD_BLANK_TILE
    DUP 3,field
    LD HL,(HUD_PTRS+field*2)
    DUP 3
    CP (HL)
    RET Z
    INC HL
    EDUP
    EDUP
    OR 1
    RET
.write:
    ; C is the exact uniform score class0/1, A the hidden atlas tile.
    LD E,A
    XOR A
    LD (HUD_ALL_CURRENT),A
    LD D,HIGH hud_top_cache
    LD A,C
    ADD A,LOW PAL_NEXT_IDS
    LD L,A
    LD H,HIGH PAL_NEXT_IDS
    LD A,(HL)
    LD (DE),A
    LD A,E
    LD D,0
    DUP 3
    ADD A,A
    RL D
    EDUP
    LD E,A
    LD A,D
    OR $20
    LD D,A
    LD A,C
    ADD A,A
    ADD A,A
    ADD A,A
    LD L,A
    LD A,(PAL_NEXT_PAGE)
    LD H,A
    LD B,8
    JP vram_copy_short

; All opposite-player font tiles were coloured while hidden. When that player
; becomes active, accept its exact four top-field signatures without scanning
; those already-correct tile attributes again.
palette_player_memo:
    LD A,(PAL_FONT_LEFT)
    OR A
    JR NZ,.no
    LD A,(PAL_FONT_UID)
    LD HL,PAL_CUR_INDEX
    CP (HL)
    JR NZ,.no
    LD A,(PAL_FONT_PLAYER)
    LD HL,$C0B7
    CP (HL)
    JR Z,.no
    LD A,(HUD_CLASS_SIGNATURES+HUD_SCORE_CLASS0)
    LD HL,hud_top_cache+HUD_BLANK_TILE
    CP (HL)
    JR NZ,.no
    LD A,($C0B7)
    OR A
    LD A,(HUD_CLASS_SIGNATURES+HUD_SCORE_CLASS0)
    JR Z,.colour
    LD A,(HUD_CLASS_SIGNATURES+HUD_SCORE_CLASS1)
.colour:
    LD C,A
    DUP 4,field
    LD HL,(HUD_PTRS+field*2)
    LD (IY+0),L
    LD (IY+1),H
    LD (IY+2),C
    LD (IY+3),0
    LD DE,4
    ADD IY,DE
    EDUP
    LD A,1
    RET
.no:
    XOR A
    RET

; Attract exits/refill have a fixed lower HUD. Its precompiled default queue
; avoids interpreting those fields on the same tick as console/input changes.
; Arbitrary scores still use the original three selected glyph vectors.
palette_default_prepare:
    LD A,(PAL_PALETTE_CHANGED)
    OR A
    JP Z,.no
    LD A,($C0E6)
    LD HL,$C0BE
    OR (HL)
    JP NZ,.no
    LD A,($C0BB)
    OR A
    JR Z,.attract
    CP 3
    JP NZ,.no
    LD A,($C0B7)
    OR A
    JP NZ,.no
    LD A,(HUD_PREVIOUS_LOGO)
    ADD A,18
    JR .base
.attract:
    LD A,($C0B7)
    OR A
    LD A,(HUD_PREVIOUS_LOGO)
    JR Z,.base
    ADD A,9
.base:
    ADD A,A
    LD L,A
    LD H,0
    LD DE,palette_default_bases
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
    LD A,(HL)
    INC HL
    LD (PAL_QUEUE_COUNT),A
    ADD A,A
    LD C,A
    LD B,0
    LD DE,PAL_QUEUE
    LDIR
    LD (PAL_QUEUE_PTR),DE
    LD HL,palette_base_memo
    LD DE,HUD_FIELD_CACHE+12
    LD BC,28
    DUP 28
    LDI
    EDUP
    LD HL,(HUD_PTRS+6)
    LD (HUD_FIELD_CACHE+12),HL
    LD HL,(HUD_PTRS+10)
    LD (HUD_FIELD_CACHE+20),HL
    LD A,($C0B7)
    OR A
    LD A,(HUD_CLASS_SIGNATURES+HUD_SCORE_CLASS0)
    JR Z,$+5
    LD A,(HUD_CLASS_SIGNATURES+HUD_SCORE_CLASS1)
    LD (HUD_FIELD_CACHE+14),A
    LD A,(HUD_CLASS_SIGNATURES+HUD_DIVER_CLASS)
    LD (HUD_FIELD_CACHE+18),A
    LD A,(HUD_CLASS_SIGNATURES+HUD_LOGO_CLASS)
    LD (HUD_FIELD_CACHE+22),A
    LD A,(PAL_CUR_INDEX)
    LD (HUD_FIELD_CACHE+26),A
    LD (HUD_FIELD_CACHE+30),A
    LD (HUD_FIELD_CACHE+34),A
    LD (HUD_FIELD_CACHE+38),A
    LD A,(PAL_PALETTE_CHANGED)
    CP 2
    CALL NZ,palette_base_clear_cache
    LD A,(HUD_CLASS_SIGNATURES+HUD_SCORE_CLASS0)
    LD (hud_top_cache+HUD_BLANK_TILE),A
    LD A,1
    LD (PAL_BASE_RESET_PENDING),A
    LD A,($C0B8)
    LD HL,$C0B9
    OR (HL)
    INC HL
    OR (HL)
    JR NZ,.scores
    DUP 3,field
    LD HL,(HUD_PTRS+field*2)
    LD (HUD_FIELD_CACHE+field*4),HL
    EDUP
    LD A,($C0B7)
    OR A
    LD A,(HUD_CLASS_SIGNATURES+HUD_SCORE_CLASS0)
    JR Z,$+5
    LD A,(HUD_CLASS_SIGNATURES+HUD_SCORE_CLASS1)
    DUP 3,field
    LD (HUD_FIELD_CACHE+field*4+2),A
    EDUP
    XOR A
    DUP 3,field
    LD (HUD_FIELD_CACHE+field*4+3),A
    EDUP
    LD A,1
    RET
.scores:
    LD IY,HUD_FIELD_CACHE
    XOR A
    LD (HUD_COLOR_BANK),A
    LD A,($C0B7)
    OR A
    JR Z,.scores_p0
    DUP 3,field
    LD HL,(HUD_PTRS+field*2)
    LD B,3
    hud_class_signature HUD_SCORE_CLASS1
    CALL hud_field_colors
    EDUP
    LD A,1
    RET
.scores_p0:
    DUP 3,field
    LD HL,(HUD_PTRS+field*2)
    LD B,3
    hud_class_signature HUD_SCORE_CLASS0
    CALL hud_field_colors
    EDUP
    LD A,1
    RET
.no:
    XOR A
    RET

; A original AC byte. Return A slot*8|128 if ready,0 fallback; C exactRGBA.
palette_enemy_lookup:
    LD L,A
    LD H,HIGH palette_enemy_nibbles
    LD A,(HL)
    LD C,A
    LD L,A
    LD H,$CC
    LD A,(HL)
    CP 255
    JR Z,.fallback
    OR 128
    RET
.fallback:
    LD A,(PAL_GLOBAL_COLORS)
    LD L,A
    LD A,(HL)
    OR A
    JR NZ,.private
    LD (HL),255                 ; only invalidate the mapping actually owned0
.private:
    XOR A
    RET

palette_enemy_prefetch:
    LD A,($C0A2)
    LD HL,PAL_FUTURE_COUNTER
    CP (HL)
    JR NZ,.new_prediction
    LD A,($C086)
    LD HL,PAL_FUTURE_MASK
    CP (HL)
    JR Z,.prediction_ready
.new_prediction:
    LD A,255
    LD (PAL_WARM_SLOT),A
    LD A,($C0A2)
    LD (PAL_FUTURE_COUNTER),A
    INC A
    JR NZ,.next_counter
    LD A,128
.next_counter:
    ADD A,A
    LD (PAL_FUTURE_XOR),A
    LD A,($C086)
    LD (PAL_FUTURE_MASK),A
    CP 7
    JR Z,.grey_mask
    CP 15
    LD A,$F7
    JR NZ,.new_mask
.grey_mask:
    LD A,7
.new_mask:
    LD (PAL_FUTURE_NEW_MASK),A
    LD C,A
    LD E,0
    LD A,($C0BD)
    AND 7
    LD L,A
    LD H,0
    LD BC,original_rom+$F0F
    ADD HL,BC
    LD A,(HL)
    LD (PAL_FUTURE_WAVE),A
    LD L,A
    LD H,HIGH palette_enemy_nibbles
    LD A,(HL)
    LD (PAL_FUTURE_BACKGROUND),A ; keep default wave and grey slots resident
    LD A,($C085)
    LD B,A
    LD A,($C086)
    LD C,A
    LD A,(PAL_FUTURE_WAVE)
    CALL .pair
    LD (PAL_FUTURE_COLORS),A
    LD A,8
    CALL .pair
    LD (PAL_FUTURE_COLORS+1),A
    LD A,(PAL_FUTURE_XOR)
    LD B,A
    LD A,(PAL_FUTURE_NEW_MASK)
    LD C,A
    LD A,(PAL_FUTURE_WAVE)
    CALL .pair
    LD (PAL_FUTURE_COLORS+2),A
    LD A,8
    CALL .pair
    LD (PAL_FUTURE_COLORS+3),A
.prediction_ready:
    LD A,(PAL_WARM_SLOT)
    CP 255
    JP NZ,.chunk
    LD HL,PAL_FUTURE_COLORS
    LD B,4
.missing:
    LD E,(HL)
    LD D,$CC
    LD A,(DE)
    CP 255
    JR Z,.allocate
    INC HL
    DJNZ .missing
    RET
.allocate:
    LD A,E
    LD (PAL_WARM_RGB),A
    LD B,ENEMY_SLOT_COUNT-1
.candidate:
    LD A,B
    ADD A,A
    ADD A,A
    ADD A,A
    LD C,A
    LD HL,HUD_ENEMY_SLOTS
    DUP 4
    CP (HL)
    JR Z,.next_candidate
    INC HL
    EDUP
    LD A,B
    ADD A,LOW PAL_GLOBAL_COLORS
    LD L,A
    LD H,HIGH PAL_GLOBAL_COLORS
    LD A,(HL)
    LD E,A
    LD L,A
    LD H,$CC
    LD A,(HL)
    CP C
    JR NZ,.claim               ; canceled/stale metadata owns no mapping
    LD A,E
    CP $E0
    JR Z,.next_candidate
    LD A,(PAL_FUTURE_BACKGROUND)
    CP E
    JR Z,.next_candidate
    LD A,E
    LD HL,PAL_FUTURE_COLORS
    DUP 4
    CP (HL)
    JR Z,.next_candidate
    INC HL
    EDUP
    ; Invalidate the old global mapping before modifying any colour bytes.
    LD L,E
    LD H,$CC
    LD (HL),255
.claim:
    LD A,B
    LD (PAL_WARM_SLOT),A
    OR A
    JR NZ,.start_chunk
    LD HL,HUD_ENEMY_COLORS
    LD DE,HUD_ENEMY_COLORS+1
    LD BC,7
    LD (HL),255
    LDIR
.start_chunk:
    XOR A
    LD (PAL_WARM_CHUNK),A
    JR .chunk
.next_candidate:
    DEC B
    JP NZ,.candidate            ; slot0 remains private to synchronous fallback
    RET                         ; active/default slots stay intact if all busy
.pair:
    XOR B
    AND C
    LD L,A
    LD H,HIGH tia_to_tms
    LD A,(HL)
    DUP 4
    RLCA
    EDUP
    OR E
    RET
.chunk:
    LD A,(PAL_WARM_SLOT)
    ADD A,A
    ADD A,A
    ADD A,A
    ADD A,A
    LD B,A
    LD A,(PAL_WARM_CHUNK)
    ADD A,A
    ADD A,B
    LD L,A
    LD H,0
    LD DE,palette_warm_addresses
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,(PAL_WARM_RGB)
    CALL hud_fill48
    LD HL,PAL_WARM_CHUNK
    INC (HL)
    LD A,(HL)
    CP 8
    RET NZ
    LD A,(PAL_WARM_SLOT)
    LD B,A
    ADD A,LOW PAL_GLOBAL_COLORS
    LD L,A
    LD H,HIGH PAL_GLOBAL_COLORS
    LD A,(PAL_WARM_RGB)
    LD (HL),A
    LD L,A
    LD H,$CC
    LD A,B
    ADD A,A
    ADD A,A
    ADD A,A
    LD (HL),A
    LD A,255
    LD (PAL_WARM_SLOT),A
    RET

palette_warm_addresses:
    DUP ENEMY_SLOT_COUNT,slot
    DW $2008+slot*96,$2038+slot*96
    DW $2808+slot*240,$2838+slot*240,$2868+slot*240
    DW $2898+slot*240,$28C8+slot*240,$3008+slot*48
    EDUP
    ALIGN 256
palette_enemy_nibbles:
    INCBIN "../outputs/presentation/enemy-foreground-nibbles.bin"

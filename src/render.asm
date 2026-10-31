; SCREEN 2 backend. Background enemies use shared per-lane six-tile caches;
; player (2), torpedo (1), lane balls (4), bottom-aligned patrol (1).
NAMEBUF EQU $C800
PATBUF EQU $CC00
SATBUF EQU $CE00
HUD_TOP EQU $CF00
HUD_BOTTOM EQU $CF20
LANE_SHAPES EQU $C500
lane_var EQU $C402
tile_base EQU $C404
phase_page EQU $C406
source_ptr EQU $C408
saved_sp EQU $C40E
cache_page EQU $C410
copy_mask EQU $C411
copy_x EQU $C412
name_row_ptr EQU $C414
tile_bottom_base EQU $C416

    MACRO enemy_bottom delta
    IFDEF WITH_HUD
    LD A,(tile_bottom_base)
    ELSE
    IF delta==1
    INC A
    ELSE
    ADD A,delta
    ENDIF
    ENDIF
    ENDM

render_init:
    LD A,2
    CALL $005F
    LD A,($F3E0)
    OR 2
    IFDEF WITH_INPUT
    AND $DF                     ; BIOS input can EI; keep the VDP IRQ masked
    ENDIF
    LD B,A
    LD C,1
    CALL $0047
    XOR A
    LD HL,NAMEBUF
    LD DE,NAMEBUF+1
    LD BC,767
    LD (HL),A
    LDIR
    LD (cache_page),A
    LD HL,0
    LD BC,$1800
    CALL $0056
    LD HL,$1800
    LD BC,768
    CALL $0056
    LD A,$51
    LD HL,$2000
    LD BC,$1800
    CALL $0056
    LD A,216
    LD HL,SATBUF
    LD DE,SATBUF+1
    LD BC,127
    LD (HL),A
    LDIR
    LD A,208
    LD (SATBUF+32),A
    LD HL,SATBUF
    LD DE,$1B00
    LD BC,128
    CALL vram_copy
    RET

; OUTI (18 cycles including MSX M1 waits) + JP NZ (11) spaces data writes
; by 29 cycles. This requires the standard MSX Z80 M1 wait, not a turbo CPU.
; HL source, DE VRAM address, BC total count. Clobbers all ordinary registers.
vram_copy:
    PUSH BC
    LD A,E
    OUT ($99),A
    LD A,D
    OR $40
    OUT ($99),A
    POP DE
    LD C,$98
.block:
    LD A,D
    OR A
    JR Z,.last
    LD B,0
.full:
    OUTI
    JP NZ,.full
    DEC D
    JR .block
.last:
    LD B,E
    LD A,B
    OR A
    RET Z
.tail:
    OUTI
    JP NZ,.tail
    RET

; Fixed transfers below256 bytes: B count, HL source, DE destination.
; Same29-cycle data spacing; no general16-bit count/block setup is needed.
vram_copy_short:
    LD A,E
    OUT ($99),A
    LD A,D
    OR $40
    OUT ($99),A
    LD C,$98
.tail:
    OUTI
    JP NZ,.tail
    RET

render_begin:
    LD A,(cache_page)
    XOR 64
    LD (cache_page),A
    ; This backend requires interrupts disabled. Stack stores clear two complete
    ; tile rows with half as many memory operations as byte-wise LDIR.
    LD (saved_sp),SP
    LD DE,0
    DUP 4, lane
    LD SP,NAMEBUF+(6+lane*3)*32+64
    DUP 32
    PUSH DE
    EDUP
    EDUP
    LD SP,(saved_sp)
    RET

; Draw a six-tile enemy at canonical X in A. Copies share phase because 16
; original pixels become exactly 24 MSX pixels. Clip to the 240-pixel viewport.
draw_enemy_names:
    ; render_enemies intersects the repeat mask with the edge table first:
    ; every admitted copy has an unsigned canonical X below 160.
    LD L,A
    LD H,HIGH column_lut
    LD C,(HL)
    LD HL,(name_row_ptr)
    LD B,0
    ADD HL,BC
    LD A,C
    CP 29
    JR NC,.clipped
    LD A,(tile_base)
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    LD DE,30
    ADD HL,DE
    enemy_bottom 1
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    RET
.clipped:
    LD A,C
    CP 31
    RET NC
    CP 30
    LD A,(tile_base)
    JR Z,.one_column
    ; Column29 retains two tiles; column30 retains one. Admitted copies
    ; cannot start left of column1. Preserve the same six-tile cache indices.
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    LD DE,31
    ADD HL,DE
    enemy_bottom 2
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    RET
.one_column:
    LD (HL),A
    LD DE,32
    ADD HL,DE
    enemy_bottom 3
    LD (HL),A
    RET

; Generate 6 tiles from 15 original bitmap rows, reflected if requested.
; source_ptr points to last source row, pattern_base selects lane cache RAM.
make_lane_patterns:
    IFDEF WITH_STREAM
    RET                         ; upload directly from the same expanded rows
    ELSE
    IFDEF WITH_COLLISIONS
    LD A,(lane_var)
    LD E,A
    LD D,0
    LD HL,$C0D9
    ADD HL,DE
    BIT 3,(HL)
    LD A,(phase_page)
    JR Z,.cache_page
    ADD A,16
.cache_page:
    ADD A,HIGH expand_lut
    LD H,A
    LD A,(source_ptr)
    SUB $B2
    LD L,A
    LD (saved_sp),SP
    DUP 3,column
    LD SP,PATBUF+32+8*column
    LD D,0
    LD E,(HL)
    INC L
    PUSH DE                    ; zero row15 followed by original row14
    DUP 3
    LD D,(HL)
    INC L
    LD E,(HL)
    INC L
    PUSH DE
    EDUP
    LD SP,PATBUF+8+8*column
    DUP 4
    LD D,(HL)
    INC L
    LD E,(HL)
    INC L
    PUSH DE
    EDUP
    IF column < 2
    LD A,L
    ADD A,70                   ; next85-byte column, after consuming15 rows
    LD L,A
    ENDIF
    EDUP
    LD SP,(saved_sp)
    RET
    ELSE
    LD IY,(source_ptr)
    LD A,(lane_var)
    LD E,A
    LD D,0
    LD HL,$C0D9
    ADD HL,DE
    BIT 3,(HL)
    JP NZ,.reflected
    CALL expansion_pages
    DUP 15, row
    LD L,(IY-row)
    LD H,D
    LD A,(HL)
    LD (PATBUF+(row/8)*24+(row%8)),A
    LD H,E
    LD A,(HL)
    LD (PATBUF+(row/8)*24+(row%8)+8),A
    LD H,B
    LD A,(HL)
    LD (PATBUF+(row/8)*24+(row%8)+16),A
    EDUP
    JP .blank
.reflected:
    CALL expansion_pages
    DUP 15, row
    LD L,(IY-row)
    LD H,HIGH reverse_bits
    LD L,(HL)
    LD H,D
    LD A,(HL)
    LD (PATBUF+(row/8)*24+(row%8)),A
    LD H,E
    LD A,(HL)
    LD (PATBUF+(row/8)*24+(row%8)+8),A
    LD H,B
    LD A,(HL)
    LD (PATBUF+(row/8)*24+(row%8)+16),A
    EDUP
    ENDIF
.blank:
    XOR A
    LD (PATBUF+31),A
    LD (PATBUF+39),A
    LD (PATBUF+47),A
    RET
    ENDIF

    IFNDEF WITH_BANKED
expansion_pages:
    LD A,(phase_page)
    LD L,A
    LD H,0
    LD DE,expand_pages
    ADD HL,DE
    LD A,(HL)
    ADD A,HIGH expand_lut
    LD D,A
    INC HL
    LD A,(HL)
    ADD A,HIGH expand_lut
    LD E,A
    INC HL
    LD A,(HL)
    ADD A,HIGH expand_lut
    LD B,A
    RET
    ENDIF

; Render current canonical enemy groups. Shape pointer and colors are provided
; by the caller; benchmark uses original-data pointers but never changes logic.
render_enemies:
    IFDEF WITH_BANKED
    DUP 4,lane_index
    LD A,3-lane_index
    LD (lane_var),A
    LD A,($C09E+3-lane_index)
    LD C,A
    AND 1
    DUP 5
    RRCA
    EDUP
    LD B,A
    LD A,C
    SRL A
    ADD A,C
    ADD A,8
    AND 7
    OR B
    LD (phase_page),A
    LD HL,NAMEBUF+(6+lane_index*3)*32
    LD (name_row_ptr),HL
    IFDEF WITH_HUD
    LD A,(HUD_ENEMY_TOP_IDS+3-lane_index)
    LD (tile_base),A
    LD A,(HUD_ENEMY_BOTTOM_IDS+3-lane_index)
    LD (tile_bottom_base),A
    ELSE
    LD A,(cache_page)
    OR 32+(3-lane_index)*6
    LD (tile_base),A
    ENDIF
    LD HL,(LANE_SHAPES+(3-lane_index)*2)
    LD (source_ptr),HL
    CALL upload_banked_lane
    LD A,($C09E+3-lane_index)
    LD (copy_x),A
    LD L,A
    LD H,HIGH collision_clip_masks
    LD A,($C0A4+3-lane_index)
    AND (HL)
    LD (copy_mask),A
    CALL draw_enemy_group
    EDUP
    RET
    ELSE
    LD A,3
.lane:
    LD (lane_var),A
    LD E,A
    LD D,0
    LD HL,$C09E
    ADD HL,DE
    LD A,(HL)
    LD C,A
    AND 1
    RRCA
    RRCA
    RRCA
    RRCA
    RRCA
    LD B,A
    LD A,C
    SRL A
    ADD A,C
    ADD A,8
    AND 7
    OR B
    LD E,A
    IFNDEF WITH_COLLISIONS
    ADD A,A
    ADD A,E
    ENDIF
    LD (phase_page),A
    LD A,(lane_var)
    LD C,A
    ADD A,A
    LD E,A
    LD D,0
    LD HL,lane_name_rows
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD (name_row_ptr),DE
    LD A,C
    LD B,A
    ADD A,A
    ADD A,B
    ADD A,A
    ADD A,32
    LD B,A
    LD A,(cache_page)
    OR B
    LD (tile_base),A
    LD A,(lane_var)
    ADD A,A
    LD E,A
    LD D,0
    LD HL,LANE_SHAPES
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
    LD (source_ptr),HL
    CALL make_lane_patterns
    CALL upload_lane_patterns
    LD A,(lane_var)
    LD E,A
    LD D,0
    LD HL,$C09E
    ADD HL,DE
    LD A,(HL)
    LD (copy_x),A
    CP 128
    LD E,8
    JR C,.mask_index
    SUB 128
    RRCA
    RRCA
    RRCA
    RRCA
    AND 7
    LD E,A
.mask_index:
    LD D,0
    LD HL,repeat_masks
    ADD HL,DE
    LD A,(HL)
    LD C,A
    LD A,(lane_var)
    LD E,A
    LD HL,$C0A4
    ADD HL,DE
    LD A,(HL)
    AND C
    LD (copy_mask),A
    DUP 3, copy
    LD A,(copy_mask)
    AND 4>>copy
    IF copy > 0
    JR Z,$+10
    ELSE
    JR Z,$+8
    ENDIF
    LD A,(copy_x)
    IF copy > 0
    ADD A,16*copy
    ENDIF
    CALL draw_enemy_names
    EDUP
    LD A,(lane_var)
    DEC A
    JP P,.lane
    RET
    ENDIF

; Normal unsigned groups share a starting tile column. Reuse that cursor for
; all three copies; the edge/wrap path retains the original individual draws.
draw_enemy_group:
    LD A,(copy_mask)
    OR A
    RET Z
    LD A,(copy_x)
    CP 128
    JP NC,.edge
    LD L,A
    LD H,HIGH column_lut
    LD C,(HL)
    LD B,0
    LD HL,(name_row_ptr)
    ADD HL,BC
    DUP 2,group_copy
    LD A,(copy_mask)
    AND 4>>group_copy
    JR Z,1F
    LD A,(tile_base)
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    LD DE,30
    ADD HL,DE
    enemy_bottom 1
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    LD DE,-31
    ADD HL,DE
    JR 2F
1:
    INC HL
    INC HL
    INC HL
2:
    EDUP
    LD A,(copy_mask)
    AND 1
    RET Z
    LD A,C
    ADD A,6
    CP 29
    JR NC,.last_clip
    LD A,(tile_base)
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    LD DE,30
    ADD HL,DE
    enemy_bottom 1
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    RET
.last_clip:
    CP 31
    RET NC
    CP 30
    LD A,(tile_base)
    JR Z,.one
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    LD DE,31
    ADD HL,DE
    enemy_bottom 2
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    RET
.one:
    LD (HL),A
    LD DE,32
    ADD HL,DE
    enemy_bottom 3
    LD (HL),A
    RET
.edge:
    DUP 3,group_edge_copy
    LD A,(copy_mask)
    AND 4>>group_edge_copy
    JR Z,1F
    LD A,(copy_x)
    IF group_edge_copy>0
    ADD A,16*group_edge_copy
    ENDIF
    CALL draw_enemy_names
1:
    EDUP
    RET

; Reuse one 48-byte staging lane. Direct stores avoid indexed-store overhead;
; each upload still targets only the inactive VRAM cache.
upload_lane_patterns:
    IFDEF WITH_BANKED
    JP upload_banked_lane
    ELSE
    IFDEF WITH_STREAM
    LD A,(lane_var)
    LD E,A
    LD D,0
    LD HL,$C0D9
    ADD HL,DE
    BIT 3,(HL)
    LD A,(phase_page)
    JR Z,.stream_page
    ADD A,16
.stream_page:
    ADD A,HIGH expand_lut
    LD H,A
    LD A,(source_ptr)
    SUB $A4                     ; first displayed row, then source rows descend
    LD L,A
    PUSH HL
    LD A,(lane_var)
    ADD A,A
    LD E,A
    LD HL,lane_vram
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,(cache_page)
    DUP 5
    RRCA
    EDUP
    ADD A,D
    LD D,A
    POP HL
    LD C,$98
    DUP 3,column
    PUSH DE
    LD A,E
    OUT ($99),A
    LD A,D
    OR $40
    OUT ($99),A
    LD B,8
1:
    OUTD
    JP NZ,1B
    EX DE,HL
    LD BC,24
    LD A,(lane_var)
    OR A
    JR NZ,2F
    LD BC,$0818
2:
    ADD HL,BC
    EX DE,HL
    LD A,E
    OUT ($99),A
    LD A,D
    OR $40
    OUT ($99),A
    LD BC,$0798
3:
    OUTD
    JP NZ,3B
    XOR A
    NOP
    OUT ($98),A                 ; source row15 remains blank
    POP DE
    IF column < 2
    LD A,E
    ADD A,8
    LD E,A
    LD BC,100                   ; OUTD can cross below the cache page at FDA4
    ADD HL,BC                  ; next85-byte column after15 descending reads
    LD C,$98
    ENDIF
    EDUP
    RET
    ELSE
    LD A,(lane_var)
    ADD A,A
    LD E,A
    LD D,0
    LD HL,lane_vram
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    LD A,(cache_page)
    RRCA
    RRCA
    RRCA
    RRCA
    RRCA
    ADD A,D
    LD D,A
    LD HL,PATBUF
    LD A,(lane_var)
    OR A
    JR Z,.split
    LD B,48
    CALL vram_copy_short
    RET
.split:
    PUSH HL
    PUSH DE
    LD B,24
    CALL vram_copy_short
    POP DE
    POP HL
    LD BC,24
    ADD HL,BC
    EX DE,HL
    LD BC,$0818
    ADD HL,BC
    EX DE,HL
    LD B,24
    JP vram_copy_short
    ENDIF
    ENDIF
lane_vram:
    DW $0900,$0930,$0960,$0190
lane_name_rows:
    DW NAMEBUF+15*32,NAMEBUF+12*32,NAMEBUF+9*32,NAMEBUF+6*32

upload_name_strips:
    DUP 4, lane
    LD HL,NAMEBUF+(6+lane*3)*32
    LD DE,$1800+(6+lane*3)*32
    LD B,64
    IFDEF WITH_HUD
    CALL hud_name_copy
    ELSE
    CALL vram_copy_short
    ENDIF
    EDUP
    RET

render_frame:
    CALL render_prepare
    JP render_commit

; Write only the inactive pattern cache during the active display.
render_prepare:
    CALL render_begin
    IFDEF WITH_HUD
    CALL hud_prepare_enemy_colors
    CALL render_enemies
    CALL upload_name_strips
    JP hud_upload_names
    ELSE
    JP render_enemies
    ENDIF

; Call at VBlank. All visible name/SAT changes finish before the next picture.
render_commit:
    IFDEF WITH_HUD
    CALL hud_commit
    ELSE
    CALL upload_name_strips
    LD HL,HUD_TOP
    LD DE,$1800
    LD B,32
    CALL vram_copy_short
    LD HL,HUD_BOTTOM
    LD DE,$1AE0
    LD B,32
    CALL vram_copy_short
    ENDIF
    LD HL,SATBUF
    LD DE,$1B00
    IFDEF WITH_HUD
    LD B,36
    ELSE
    LD B,32
    ENDIF
    CALL vram_copy_short
    ; Allow the TMS9918's final queued byte to reach VRAM before returning.
    NOP
    NOP
    IFDEF WITH_HUD
    CALL hud_show
    ENDIF
    RET

wait_vblank:
    IN A,($99)
vblank_clear_sample:
.wait:
    IN A,($99)
vblank_sample:
    OR A
    JP P,vblank_clear_sample.wait
    RET

repeat_masks:
    INCBIN "../outputs/render/repeat-masks.bin"

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
    INC A
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    INC HL
    INC A
    LD (HL),A
    RET
.clipped:
    LD A,(tile_base)
    LD B,2
.rows:
    PUSH BC
    PUSH HL
    LD B,3
.cols:
    PUSH AF
    LD A,C
    CP 1
    JR C,.skip
    CP 31
    JR NC,.skip
    POP AF
    LD (HL),A
    PUSH AF
.skip:
    POP AF
    INC A
    INC HL
    INC C
    DJNZ .cols
    POP HL
    LD DE,32
    ADD HL,DE
    POP BC
    DJNZ .rows
    RET

; Generate 6 tiles from 15 original bitmap rows, reflected if requested.
; source_ptr points to last source row, pattern_base selects lane cache RAM.
make_lane_patterns:
    LD IY,(source_ptr)
    LD A,(lane_var)
    LD E,A
    LD D,0
    LD HL,$C0D9
    ADD HL,DE
    BIT 3,(HL)
    JP NZ,.reflected
    LD A,(phase_page)
    LD D,A
    DUP 15, row
    LD L,(IY-row)
    LD H,D
    LD A,(HL)
    LD (PATBUF+(row/8)*24+(row%8)),A
    INC H
    LD A,(HL)
    LD (PATBUF+(row/8)*24+(row%8)+8),A
    INC H
    LD A,(HL)
    LD (PATBUF+(row/8)*24+(row%8)+16),A
    EDUP
    JP .blank
.reflected:
    LD A,(phase_page)
    LD D,A
    DUP 15, row
    LD L,(IY-row)
    LD H,HIGH reverse_bits
    LD L,(HL)
    LD H,D
    LD A,(HL)
    LD (PATBUF+(row/8)*24+(row%8)),A
    INC H
    LD A,(HL)
    LD (PATBUF+(row/8)*24+(row%8)+8),A
    INC H
    LD A,(HL)
    LD (PATBUF+(row/8)*24+(row%8)+16),A
    EDUP
.blank:
    XOR A
    LD (PATBUF+31),A
    LD (PATBUF+39),A
    LD (PATBUF+47),A
    RET

; Render current canonical enemy groups. Shape pointer and colors are provided
; by the caller; benchmark uses original-data pointers but never changes logic.
render_enemies:
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
    ADD A,A
    ADD A,E
    ADD A,HIGH expand_lut
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

; Reuse one 48-byte staging lane. Direct stores avoid indexed-store overhead;
; each upload still targets only the inactive VRAM cache.
upload_lane_patterns:
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
    LD BC,48
    CALL vram_copy
    RET
.split:
    PUSH HL
    PUSH DE
    LD BC,24
    CALL vram_copy
    POP DE
    POP HL
    LD BC,24
    ADD HL,BC
    EX DE,HL
    LD BC,$0818
    ADD HL,BC
    EX DE,HL
    LD BC,24
    JP vram_copy
lane_vram:
    DW $0900,$0930,$0960,$0190
lane_name_rows:
    DW NAMEBUF+15*32,NAMEBUF+12*32,NAMEBUF+9*32,NAMEBUF+6*32

upload_name_strips:
    DUP 4, lane
    LD HL,NAMEBUF+(6+lane*3)*32
    LD DE,$1800+(6+lane*3)*32
    LD BC,64
    CALL vram_copy
    EDUP
    RET

render_frame:
    CALL render_prepare
    JP render_commit

; Write only the inactive pattern cache during the active display.
render_prepare:
    CALL render_begin
    JP render_enemies

; Call at VBlank. All visible name/SAT changes finish before the next picture.
render_commit:
    CALL upload_name_strips
    LD HL,HUD_TOP
    LD DE,$1800
    LD BC,32
    CALL vram_copy
    LD HL,HUD_BOTTOM
    LD DE,$1AE0
    LD BC,32
    CALL vram_copy
    LD HL,SATBUF
    LD DE,$1B00
    LD BC,32
    CALL vram_copy
    ; Allow the TMS9918's final queued byte to reach VRAM before returning.
    NOP
    NOP
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

; Renderer diagnostic; original core/art are optional local-only inputs.
    ORG $4000
    DB "AB"
    DW init
    DW 0,0,0
    DS 6,0
init:
    DI
    LD SP,$F380
    ; BIOS starts a cartridge in page1; explicitly expose its second ROM page.
    CALL $0138
    RRCA
    RRCA
    AND 3
    LD C,A
    LD B,0
    LD HL,$FCC1
    ADD HL,BC
    LD A,(HL)
    AND $80
    OR C
    LD C,A
    INC HL
    INC HL
    INC HL
    INC HL
    LD A,(HL)
    AND $0C
    OR C
    LD H,$80
    CALL $0024
    CALL render_init
    DI
    IFDEF WITH_GRAPHICS
    LD HL,original_sprite_catalog
    LD BC,SPRITE_RESIDENT*32
    ELSE
    LD HL,sprite_patterns
    LD BC,256
    ENDIF
    LD DE,$3800
    CALL vram_copy
    LD HL,sat_initial
    LD DE,SATBUF
    LD BC,32
    LDIR
    LD HL,HUD_TOP
    LD DE,HUD_TOP+1
    LD BC,63
    LD (HL),0
    LDIR
    LD A,$53
    LD ($C7FD),A
idle:
    JP idle
rpc_start:
    LD SP,$F380
frame_start:
    IFDEF WITH_NATIVE
    LD A,($C6F4)
    LD E,A
    LD BC,($C6F2)
    LD HL,($C6F0)
    PUSH HL
    POP AF
    LD HL,core_done
    PUSH HL
    LD HL,($C6FE)
    JP (HL)
core_done:
    ENDIF
    CALL prepare_shapes
    CALL prepare_sprites
    IFDEF WITH_GRAPHICS
    CALL prepare_original_sprites
    ENDIF
    CALL render_frame
rpc_done:
    JP idle
paced_start:
    CALL wait_vblank
paced_commit:
    CALL render_commit
paced_frame_start:
    IFDEF WITH_NATIVE
    XOR A
    LD E,A
    LD B,$82
    LD C,A
    CALL core_F5B8
    ENDIF
    CALL prepare_shapes
    CALL prepare_sprites
    IFDEF WITH_GRAPHICS
    CALL prepare_original_sprites
    ENDIF
    CALL render_prepare
paced_prepared:
    JP paced_start

prepare_shapes:
    LD IX,LANE_SHAPES
    LD IY,$C0D9
    LD B,4
.lane:
    PUSH BC
    IFDEF WITH_NATIVE
    LD A,(IY+0)
    AND 7
    LD E,A
    LD D,0
    LD HL,original_rom+$FA2
    ADD HL,DE
    LD A,(HL)
    LD C,A
    LD A,E
    CP 4
    LD A,C
    JR NC,.sub
    LD A,($C0DD)
    ADD A,C
.sub:
    ADD A,14
    LD L,A
    LD H,HIGH (original_rom+$D00)
    ELSE
    LD HL,benchmark_shape+14
    ENDIF
    LD (IX+0),L
    LD (IX+1),H
    INC IX
    INC IX
    INC IY
    POP BC
    DJNZ .lane
    RET

; Synthetic shape indices are preloaded; only positions change per frame.
prepare_sprites:
    LD HL,SATBUF
    LD A,($C0E1)
    ADD A,16
    LD (HL),A
    LD (SATBUF+4),A
    ADD A,5
    LD (SATBUF+8),A
    LD A,($C0C6)
    CALL scale_x
    LD (SATBUF+1),A
    ADD A,16
    LD (SATBUF+5),A
    LD A,($C0E7)
    CALL scale_x
    LD (SATBUF+9),A
    LD IX,SATBUF+12
    LD IY,$C0C7
    LD B,4
    LD C,120
.ball:
    LD (IX+0),C
    LD A,(IY+0)
    CALL scale_x
    LD (IX+1),A
    LD A,C
    SUB 24
    LD C,A
    LD DE,4
    ADD IX,DE
    INC IY
    DJNZ .ball
    ; Original patrol rectangle raw y45..52 -> MSX y30..37. Anchor its
    ; hardware box at y22, using pattern rows8..15 (nonzero source y31..37).
    LD A,21
    LD (SATBUF+28),A
    LD A,($C0F6)
    CALL scale_x
    LD (SATBUF+29),A
    RET

scale_x:
    LD E,A
    SRL A
    ADD A,E
    ADD A,8
    RET
    INCLUDE "render.asm"
benchmark_shape:
    DB $18,$3C,$7E,$FF,$DB,$FF,$7E,$3C,$7E,$DB,$FF,$7E,$3C,$18,$08
    ALIGN 256
expand_lut:
    INCBIN "../outputs/render/expand.bin"
reverse_bits:
    INCBIN "../outputs/render/reverse.bin"
    IFDEF WITH_GRAPHICS
    INCLUDE "original_sprites.asm"
    INCLUDE "../outputs/graphics/sprites.inc"
    ENDIF
    IFNDEF WITH_GRAPHICS
sprite_patterns:
    DUP 8, sprite
    DUP 32, pos
    IF sprite == 7
    IF pos%16 < 8
    DB 0
    ELSE
    DB $F0
    ENDIF
    ELSE
    IF sprite == 2
    IF pos == 0
    DB $E0
    ELSE
    DB 0
    ENDIF
    ELSE
    IF pos%16 >= 12+(sprite>=3)*3 || (sprite==1 && pos>=16)
    DB 0
    ELSE
    IF sprite==1 || (sprite>=3 && pos>=16)
    DB $F0
    ELSE
    DB $FF
    ENDIF
    ENDIF
    ENDIF
    ENDIF
    EDUP
    EDUP
    ENDIF
sat_initial:
    DUP 8, sprite
    DB 216,0,sprite*4,15-sprite
    EDUP
    IFDEF WITH_NATIVE
    INCLUDE "../outputs/native/core.inc"
    ALIGN 256
original_rom:
    INCBIN "../outputs/native/original.rom"
    ENDIF
    ASSERT $ <= $C000
    IF $ < $C000
    DS $C000-$,$FF
    ENDIF

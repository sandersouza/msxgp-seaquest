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
    IFDEF WITH_BANKED
    LD A,1
    LD ($7000),A                ; ASCII16 page2 data bank; page1 code stays fixed
    ENDIF
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
    IFDEF WITH_PALETTE
    LD A,5
    LD ($7000),A
    ENDIF
    CALL vram_copy
    IFDEF WITH_PALETTE
    LD A,1
    LD ($7000),A
    ENDIF
    IFNDEF WITH_GRAPHICS
    LD HL,sat_initial
    LD DE,SATBUF
    LD BC,32
    LDIR
    ENDIF
    LD HL,HUD_TOP
    LD DE,HUD_TOP+1
    LD BC,63
    LD (HL),0
    LDIR
    LD A,$53
    LD ($C7FD),A
    IFDEF WITH_INPUT
    CALL input_init
    ENDIF
    IFDEF WITH_AUDIO
    CALL audio_init
    ENDIF
    IFDEF WITH_HUD
    CALL hud_init
    ENDIF
    IFDEF WITH_PALETTE
    CALL video_init
    ENDIF
    IFDEF CONTROL_DEMO
    LD HL,$C000
    LD DE,$C001
    LD BC,1023
    LD (HL),0
    LDIR
    LD A,1
    LD ($C082),A
    CALL core_FB54
    ; The first paced hardware phase acquires the original raster contacts.
    CALL neutral_contacts
    IFDEF WITH_HUD
    JP paced_frame_start
    ELSE
    JP paced_start
    ENDIF
    ENDIF
idle:
    JP idle
    IFDEF WITH_AUDIO
audio_prime_start:
    DI
    LD SP,$F380
    IFDEF WITH_PALETTE
    XOR A
    LD (PAL_FAST_VBLANK),A
    ENDIF
    CALL audio_init
    CALL audio_sync
    JP frame_start
audio_prime_only_start:
    DI
    LD SP,$F380
    CALL audio_init
    CALL audio_sync
audio_prime_only_done:
    JP idle
    ENDIF
    IFDEF WITH_INPUT
    IFDEF WITH_NATIVE
input_rpc_start:
    LD SP,$F380
    CALL neutral_contacts
    XOR A
    LD E,A
    LD B,$82
    LD C,A
    CALL core_F5B8
input_rpc_done:
    JP idle
    ENDIF
    ENDIF
rpc_start:
    LD SP,$F380
    IFDEF WITH_PALETTE
    XOR A
    LD (PAL_FAST_VBLANK),A
    ENDIF
frame_start:
    IFDEF WITH_NATIVE
    IFDEF WITH_COLLISIONS
    CALL acquire_frame_state
    ELSE
    IFDEF WITH_INPUT
    CALL neutral_contacts
    ENDIF
    ENDIF
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
    IFDEF WITH_HUD
    CALL hud_prepare
    ENDIF
    CALL prepare_shapes
    CALL prepare_sprites
    IFDEF WITH_GRAPHICS
    IFDEF WITH_PALETTE
    LD A,5
    LD ($7000),A
    ENDIF
    CALL prepare_original_sprites
    IFDEF WITH_PALETTE
    LD A,1
    LD ($7000),A
    ENDIF
    ENDIF
    CALL render_frame
rpc_done:
    JP idle
paced_start:
    CALL wait_vblank
    JR paced_commit
paced_wait:
    CALL wait_vblank_next
paced_commit:
    IFDEF WITH_PALETTE
    LD A,1
    LD (PAL_FAST_VBLANK),A
    ENDIF
    CALL render_commit
video_after_commit:
    IFDEF WITH_PALETTE
    XOR A
    LD (PAL_FAST_VBLANK),A
    CALL video_extra_tick
    ENDIF
paced_frame_start:
    IFDEF WITH_NATIVE
    IFDEF WITH_COLLISIONS
    CALL acquire_frame_state
    ELSE
    IFDEF WITH_INPUT
    CALL neutral_contacts
    ENDIF
    ENDIF
    XOR A
    LD E,A
    LD B,$82
    LD C,A
paced_core_start:
    CALL core_F5B8
    ENDIF
paced_core_done:
    IFDEF WITH_HUD
    CALL hud_prepare
    ENDIF
    CALL prepare_shapes
    CALL prepare_sprites
    IFDEF WITH_GRAPHICS
    IFDEF WITH_PALETTE
    LD A,5
    LD ($7000),A
    ENDIF
    CALL prepare_original_sprites
    IFDEF WITH_PALETTE
    LD A,1
    LD ($7000),A
    ENDIF
    ENDIF
    CALL render_prepare
paced_prepared:
    IFDEF WITH_PALETTE
    CALL video_prepare_extra
    JP paced_wait
    ELSE
    JP paced_start
    ENDIF

    IFDEF WITH_INPUT
neutral_contacts:
    LD HL,$FFFF
    LD ($C0B0),HL
    LD ($C0B2),HL
    LD ($C0B4),HL
    LD A,$FF
    LD ($C0B6),A
    XOR A
    LD ($C0F8),A
    RET
    ENDIF

    IFDEF WITH_COLLISIONS
collision_rpc_start:
    LD SP,$F380
    CALL acquire_contacts
collision_rpc_done:
    JP idle
collision_tick_rpc_start:
    LD SP,$F380
    CALL acquire_frame_state
    XOR A
    LD E,A
    LD B,$82
    LD C,A
    CALL core_F5B8
    JP collision_rpc_done
oxygen_rpc_start:
    LD SP,$F380
    CALL prepare_oxygen
    JP collision_rpc_done
    INCLUDE "oxygen.asm"
    INCLUDE "collision.asm"
    ENDIF

prepare_shapes:
    IFDEF WITH_STREAM
    DUP 4,lane
    LD A,($C0D9+lane)
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
    JR NC,1F
    LD A,($C0DD)
    ADD A,C
1:
    ADD A,14
    LD L,A
    LD H,HIGH (original_rom+$D00)
    LD (LANE_SHAPES+2*lane),HL
    EDUP
    RET
    ELSE
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
    ENDIF

    ; Inlined conversion avoids seven per-frame CALL/RET pairs.
    MACRO scale_x
    LD E,A
    SRL A
    ADD A,E
    ADD A,8
    ENDM

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
    scale_x
    LD (SATBUF+1),A
    ADD A,16
    LD (SATBUF+5),A
    LD A,($C0E7)
    scale_x
    LD (SATBUF+9),A
    DUP 4, lane
    IFDEF WITH_GRAPHICS
    LD A,119-24*lane
    ELSE
    LD A,120-24*lane
    ENDIF
    LD (SATBUF+12+4*lane),A
    LD A,($C0C7+lane)
    scale_x
    LD (SATBUF+13+4*lane),A
    EDUP
    ; Original patrol rectangle raw y45..52 -> MSX y30..37. Anchor its
    ; hardware box at y22, using pattern rows8..15 (nonzero source y31..37).
    LD A,21
    LD (SATBUF+28),A
    LD A,($C0F6)
    scale_x
    LD (SATBUF+29),A
    RET

    IFDEF WITH_INPUT
    INCLUDE "input.asm"
    ENDIF
    INCLUDE "render.asm"
    IFDEF WITH_AUDIO
    INCLUDE "audio.asm"
    ENDIF
    IFDEF WITH_BANKED
    INCLUDE "enemy_banked.asm"
    ENDIF
    IFDEF WITH_HUD
    INCLUDE "hud.asm"
    ENDIF
    IFDEF WITH_PALETTE
    INCLUDE "palette_fast.asm"
    ENDIF
benchmark_shape:
    IFNDEF WITH_NATIVE
    DB $18,$3C,$7E,$FF,$DB,$FF,$7E,$3C,$7E,$DB,$FF,$7E,$3C,$18,$08
    ENDIF
    IFNDEF WITH_BANKED
    ALIGN 256
expand_lut:
    IFDEF WITH_COLLISIONS
    INCBIN "../outputs/collision/enemy-cache.bin"
    ELSE
    INCBIN "../outputs/render/expand-compact.bin"
    ENDIF
expand_pages:
    INCBIN "../outputs/render/expand-pages.bin"
    ENDIF
    ALIGN 256
    IFNDEF WITH_BANKED
reverse_bits:
    INCBIN "../outputs/render/reverse.bin"
    ENDIF
column_lut:
    IFDEF WITH_BANKED
    INCBIN "../outputs/render/columns.bin",0,160
    ELSE
    INCBIN "../outputs/render/columns.bin"
    ENDIF
    IFDEF WITH_GRAPHICS
    INCLUDE "original_sprites.asm"
    IFNDEF WITH_BANKED
    INCLUDE "../outputs/graphics/sprites.inc"
    ENDIF
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
    IFNDEF WITH_GRAPHICS
    DUP 8, sprite
    DB 216,0,sprite*4,15-sprite
    EDUP
    ENDIF
    IFDEF WITH_BANKED
    IFNDEF WITH_PALETTE
    INCLUDE "../outputs/native/core.inc"
    ELSE
    INCLUDE "../outputs/presentation/palette-tables.inc"
    ENDIF
    ALIGN 256
    IFNDEF WITH_PALETTE
enemy_windows:
    INCBIN "../outputs/presentation/enemy-windows.bin"
    ENDIF
enemy_pointers:
    INCBIN "../outputs/presentation/enemy-pointers.bin"
    IFDEF WITH_PALETTE
; ALL_CURRENT is only established by the default-colour boot atlas. Before
; hidden font warming drops that stronger invariant, retain exact visible
; field memos. A later moving logo need not rescan every already-correct field.
palette_stamp_default_memos:
    DUP 8,field
    LD HL,(HUD_PTRS+field*2)
    LD (HUD_FIELD_CACHE+field*4),HL
    EDUP
    LD HL,hud_background_top
    LD (HUD_FIELD_CACHE+32),HL
    LD HL,hud_background_bottom
    LD (HUD_FIELD_CACHE+36),HL
    LD DE,1
    DUP 6,field
    LD (HUD_FIELD_CACHE+field*4+2),DE
    EDUP
    LD DE,PALETTE_DEFAULT_INDEX
    DUP 4,field
    LD (HUD_FIELD_CACHE+(field+6)*4+2),DE
    EDUP
    RET
    ENDIF
    IFDEF WITH_PALETTE
    INCLUDE "video.asm"
    ENDIF
    IFDEF WITH_PALETTE
collision_missile_masks:
    DB 1,3,7,15,31,63,127,255,254,252,248,240,224,192,128
    ENDIF
fixed_bank_end:
    ASSERT $ <= $8000
    DS $8000-$,$FF
    ORG $8000
    INCLUDE "../outputs/graphics/sprites.inc"
    IFDEF WITH_HUD
    INCLUDE "../outputs/presentation/hud.inc"
    IFNDEF WITH_PALETTE
    INCLUDE "../outputs/presentation/hud-palette.inc"
    ENDIF
    INCLUDE "../outputs/presentation/enemy-colors.inc"
    ENDIF
    IFDEF WITH_PALETTE
    INCLUDE "../outputs/native/core.inc"
    ENDIF
    ALIGN 256
original_rom EQU $-$C00
    INCBIN "../outputs/native/original.rom",$C00,$400
    IFDEF WITH_AUDIO
    INCLUDE "../outputs/presentation/audio-tables.inc"
    ENDIF
    IFDEF WITH_PALETTE
    ALIGN 256
    INCLUDE "../outputs/presentation/enemy-window-pointers.inc"
    ENDIF
data_bank_end:
    ASSERT $ <= $C000
    IFDEF WITH_PALETTE
    ASSERT $ <= $9B00
    DS $9B00-$,$FF
    INCLUDE "../outputs/presentation/palette-writers.inc"
    INCLUDE "palette_enemy.asm"
    INCLUDE "../outputs/presentation/palette-generations.inc"
palette_default:
    INCBIN "../outputs/presentation/palette-default.bin"
    INCLUDE "../outputs/presentation/palette-default-bases.inc"
    ASSERT $ <= $C000
    DS $C000-$,$FF
    ELSE
    IF $ < $C000
    DS $C000-$,$FF
    ENDIF
    ENDIF
    ORG $8000
    INCBIN "../outputs/presentation/enemy-patterns.bin",0,$4000
    ORG $8000
    IFDEF WITH_PALETTE
    INCBIN "../outputs/presentation/palette-bank3.bin"
    ORG $8000
    INCBIN "../outputs/presentation/palette-bank4.bin"
    ORG $8000
    INCBIN "../outputs/presentation/palette-bank5.bin"
    ORG $8000
    INCBIN "../outputs/presentation/palette-bank6.bin"
    ORG $8000
    INCBIN "../outputs/presentation/palette-bank7.bin"
    ELSE
    INCBIN "../outputs/presentation/enemy-patterns.bin",$4000,$4000
    ENDIF
    ELSE
    IFDEF WITH_NATIVE
    IFDEF WITH_HUD
    INCLUDE "../outputs/presentation/hud.inc"
    ENDIF
    INCLUDE "../outputs/native/core.inc"
    ALIGN 256
    IFDEF WITH_PACKED_DATA
original_rom EQU $-$C00
    INCBIN "../outputs/native/original.rom",$C00,$400
    ELSE
original_rom:
    INCBIN "../outputs/native/original.rom"
    ENDIF
    ENDIF
    ASSERT $ <= $C000
    IF $ < $C000
    DS $C000-$,$FF
    ENDIF
    ENDIF

; All routines here remain in fixed bank0 while reading a palette/sprite bank.
; Exact byte IDs are local to each immutable tile class (never lossy hashes).
PAL_CUR_INDEX EQU $C6D0
PAL_NEXT_INDEX EQU $C6D1
PAL_READY EQU $C6D2
PAL_CURRENT_PAGE EQU $C6D3
PAL_NEXT_PAGE EQU $C6D4
PAL_COPY_POS EQU $C6D5
PAL_COPY_SOURCE EQU $C6D7
PAL_COPY_BANK EQU $C6D9
PAL_QUEUE_PTR EQU $C6DA
PAL_QUEUE_COUNT EQU $C6DC
PAL_INIT EQU $C6DD
PAL_CACHE_PAGE EQU $C6DE
PAL_CLASS_PAGE EQU $C6DF
PAL_SPAN_CLASS EQU $C6E3
PAL_COMMIT_FLAGS EQU $C6E5
PAL_SAVED_SP EQU $C6E6
PAL_FAST_VBLANK EQU $C6E4
PAL_CURRENT_STATIC EQU $C680
PAL_PENDING_STATIC EQU $C600
PAL_GEN_SERIAL EQU $C6EA
PAL_PALETTE_CHANGED EQU $C6E8
PAL_STATIC_DEFAULT EQU $C6E9
PAL_BASE_RESET_PENDING EQU $C4C7
PAL_OFF_JUMP EQU $C6EB
PAL_DISPLAY_OFF EQU $C6EE
PAL_BLACKOUT EQU $C6EF
PAL_UPLOAD_DISPATCH EQU $C4C4
PAL_NEXT_ROLES EQU $C6B0
PAL_NEXT_IDS EQU $CFD0
PAL_QUEUE EQU $C510

palette_forecast_tick:
    LD A,7
    LD ($7000),A
    CALL palette_forecast_tick_banked
    LD A,1
    LD ($7000),A
    RET
palette_forecast_apply:
    LD A,($C2E1)
    CP 10
    LD A,0
    RET NZ
    LD A,7
    LD ($7000),A
    CALL palette_forecast_apply_banked
    LD B,A
    LD A,1
    LD ($7000),A
    LD A,B
    RET

palette_init:
    LD A,$C3
    LD (PAL_OFF_JUMP),A
    LD (PAL_UPLOAD_DISPATCH),A
    LD A,HIGH palette_off_data
    LD (PAL_OFF_JUMP+2),A
    LD A,1
    LD (PAL_DISPLAY_OFF),A
    LD (PAL_STATIC_DEFAULT),A
    CALL palette_upload_fast
    XOR A
    LD (PAL_BASE_RESET_PENDING),A
    LD (PAL_BLACKOUT),A
    LD (PAL_FAST_VBLANK),A
    LD ($C2EF),A
    LD ($C2E1),A
    LD (PAL_READY),A
    LD (PAL_QUEUE_COUNT),A
    LD A,255
    LD ($C2E2),A
    LD ($C2E3),A
    LD (PAL_NEXT_INDEX),A
    LD A,1
    LD (PAL_INIT),A
    LD A,PALETTE_DEFAULT_INDEX
    LD (PAL_CUR_INDEX),A
    LD A,$C7
    LD (PAL_CURRENT_PAGE),A
    LD HL,palette_default
    LD DE,$C700
    LD BC,248
    LDIR
    LD DE,HUD_CLASS_SIGNATURES
    LD BC,31
    LDIR
    PUSH HL
    LD HL,HUD_CLASS_SIGNATURES
    LD DE,PAL_CURRENT_STATIC
    LD BC,31
    LDIR
    POP HL
    PUSH HL
    LD HL,HUD_CLASS_SIGNATURES
    LD DE,HUD_CLASS_SIGNATURES+1
    LD BC,30
    LD (HL),1
    LDIR
    LD A,1
    LD (PAL_GEN_SERIAL),A
    POP HL
    LD DE,HUD_ROLES
    LD BC,24
    LDIR
    RET

; Source key -> exact complete-palette ID. Supports all original masks and
; mask0 cold/display-only fixtures; bit0 of a TIA colour is irrelevant.
palette_source_index:
    LD A,($C086)
    LD L,A
    LD H,HIGH palette_mask_groups
    LD A,(HL)
    LD C,A
    AND 1
    RRCA
    LD B,A
    LD A,($C085)
    SRL A
    OR B
    LD L,A
    LD A,C
    SRL A
    LD H,A
    LD DE,palette_key_ids
    ADD HL,DE
    LD A,(HL)
    RET

palette_prepare:
    XOR A
    LD (PAL_BLACKOUT),A
    LD A,($C086)
    OR A
    JR NZ,.normal
    LD A,($C0E9)
    LD HL,$C0F6
    OR (HL)
    JR NZ,.normal
    LD HL,$C0AC
    DUP 4
    OR (HL)
    INC HL
    EDUP
    JP Z,palette_prepare_blackout
.normal:
    LD A,($C085)
    LD HL,HUD_KEY
    CP (HL)
    JR NZ,.different_key
    INC HL
    LD A,($C086)
    CP (HL)
    RET Z
.different_key:
    CALL palette_source_index
    LD B,A
    LD A,($C085)
    LD (HUD_KEY),A
    LD A,($C086)
    LD (HUD_KEY+1),A
    LD A,(PAL_CUR_INDEX)
    CP B
    RET Z
    LD A,B
    CP PALETTE_DEFAULT_INDEX
    JR NZ,.pending
    LD A,$C7
    LD (PAL_CURRENT_PAGE),A
    CALL palette_generations_default
    CALL palette_restore_default_roles
    LD A,PALETTE_DEFAULT_INDEX
    JR .activated
.pending:
    LD A,(PAL_NEXT_INDEX)
    CP B
    JR NZ,.synchronous
    LD A,(PAL_READY)
    OR A
    JR NZ,.activate_pending
    JR .load
.synchronous:
    LD A,B
    CALL palette_start_copy
.load:
    CALL palette_copy_chunk
    LD A,(PAL_READY)
    OR A
    JR Z,.load
.activate_pending:
    LD A,(PAL_NEXT_PAGE)
    LD (PAL_CURRENT_PAGE),A
    LD HL,PAL_NEXT_IDS
    LD DE,HUD_CLASS_SIGNATURES
    LD BC,31
    LDIR
    LD HL,PAL_NEXT_ROLES
    LD DE,HUD_ROLES
    LD BC,24
    LDIR
    LD A,(PAL_NEXT_INDEX)
.activated:
    LD B,A
    LD A,1
    LD (PAL_PALETTE_CHANGED),A
    LD A,B
    PUSH AF
    CP PALETTE_DEFAULT_INDEX
    LD A,1
    JR Z,.static_mode
    XOR A
    LD (PAL_STATIC_DEFAULT),A
    LD HL,PAL_PENDING_STATIC
    LD DE,PAL_CURRENT_STATIC
    LD BC,31
    LDIR
    XOR A
.static_mode:
    LD (PAL_STATIC_DEFAULT),A
    POP AF
    LD (PAL_CUR_INDEX),A
    LD B,A
    LD A,(PAL_FONT_UID)
    CP B
    JR Z,.font_stamp
    LD A,255
    LD (PAL_FONT_UID),A
.font_stamp:
    LD A,255
    LD (PAL_NEXT_INDEX),A
    XOR A
    LD (PAL_READY),A
    LD (HUD_ALL_CURRENT),A
    INC A
    LD (HUD_COLORS_NEEDED),A
    RET

palette_invalidate_caches:
    LD (saved_sp),SP
    LD DE,0
    LD B,32
    LD SP,hud_bottom_cache+256
.block:
    DUP 8
    PUSH DE
    EDUP
    DJNZ .block
    LD SP,(saved_sp)
    RET

palette_generations_default:
    LD (saved_sp),SP
    LD DE,$0101
    LD SP,HUD_CLASS_SIGNATURES+32
    DUP 16
    PUSH DE
    EDUP
    LD SP,(saved_sp)
    RET

palette_prepare_blackout:
    LD A,1
    LD (PAL_BLACKOUT),A
    XOR A
    LD (PAL_QUEUE_COUNT),A
    LD (PAL_READY),A
    LD (HUD_KEY+1),A
    LD A,($C085)
    LD (HUD_KEY),A
    LD A,255
    LD (PAL_FONT_UID),A
    LD (PAL_NEXT_INDEX),A
    LD A,(PAL_CUR_INDEX)
    CP PALETTE_BLACK_INDEX
    RET Z
    LD A,PALETTE_BLACK_INDEX
    LD (PAL_CUR_INDEX),A
    LD HL,HUD_ROLES
    LD DE,HUD_ROLES+1
    LD BC,23
    LD (HL),1
    LDIR
    RET

palette_upload_fast:
    LD HL,palette_copy_short_off
    LD (PAL_UPLOAD_DISPATCH+1),HL
    RET
palette_upload_slow:
    LD HL,vram_copy_short_slow
    LD (PAL_UPLOAD_DISPATCH+1),HL
    RET
palette_copy_short_off:
    LD A,E
    OUT ($99),A
    LD A,D
    OR $40
    OUT ($99),A
    LD C,$98
    LD A,B
    ADD A,A
    NEG
    ADD A,(LOW palette_off_data+128)&255
    LD (PAL_OFF_JUMP+1),A
    JP PAL_OFF_JUMP
    ALIGN 128
palette_off_data:
    DUP 64
    OUTI
    EDUP
    RET

; Runtime tokens never reuse an earlier colour generation, even when a
; prefetched palette is canceled. Static source IDs only decide equality.
; Rebase before byte tokens can wrap, invalidating every old physical tag.
palette_translate_ids:
    LD HL,PAL_NEXT_IDS
    LD DE,PAL_PENDING_STATIC
    LD BC,31
    LDIR
    JP palette_translate_ids_banked

palette_rebase_generations:
    PUSH BC
    PUSH HL
    CALL palette_invalidate_caches
    CALL palette_rebase_current_tokens
    LD A,2
    LD (PAL_GEN_SERIAL),A
    LD A,($C0B7)
    OR A
    LD A,(HUD_CLASS_SIGNATURES+HUD_SCORE_CLASS0)
    JR Z,$+5
    LD A,(HUD_CLASS_SIGNATURES+HUD_SCORE_CLASS1)
    DUP 4,field
    LD (HUD_FIELD_CACHE+field*4+2),A
    EDUP
    LD A,(HUD_CLASS_SIGNATURES+HUD_DIVER_CLASS)
    LD (HUD_FIELD_CACHE+18),A
    LD A,(HUD_CLASS_SIGNATURES+HUD_LOGO_CLASS)
    LD (HUD_FIELD_CACHE+22),A
    LD A,255
    LD (PAL_FONT_UID),A
    LD ($C2E2),A
    LD ($C2E3),A
    POP HL
    POP BC
    RET

; A exact-palette ID. Record never straddles16KiB; the mapper is restored1
; before returning. Only the inactive RGB buffer and pending IDs/roles change.
palette_start_copy:
    LD (PAL_NEXT_INDEX),A
    LD L,A
    LD H,0
    LD E,A
    LD D,H
    ADD HL,HL
    ADD HL,DE
    LD DE,palette_locations
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD A,(HL)
    LD (PAL_COPY_BANK),A
    LD (PAL_COPY_SOURCE),DE
    LD HL,0
    LD (PAL_COPY_POS),HL
    XOR A
    LD (PAL_READY),A
    LD A,(PAL_CURRENT_PAGE)
    CP HIGH hud_rgb0
    LD A,HIGH hud_rgb0
    JR NZ,.page
    LD A,HIGH hud_rgb1
.page:
    LD (PAL_NEXT_PAGE),A
    RET

palette_copy_chunk:
    LD HL,(PAL_COPY_POS)
    LD A,H
    OR A
    JR NZ,.late
    LD A,L
    CP 248
    JR NC,.ids
    LD E,L
    LD A,(PAL_NEXT_PAGE)
    LD D,A
    LD A,248
    SUB L
    CP 32
    JR C,.length
    LD A,32
    JR .length
.ids:
    LD DE,PAL_NEXT_IDS-248
    ADD HL,DE
    EX DE,HL
    LD A,31
    JR .length
.late:
    LD DE,-279
    ADD HL,DE
    JR NC,.ids_high
    LD A,L
    LD DE,PAL_NEXT_ROLES
    ADD HL,DE
    EX DE,HL
    LD B,A
    LD A,24
    SUB B
    JR .length
.ids_high:
    ; Positions256..278 are the remainder of the31-byte ID segment. The
    ; first ID chunk starts248 and copies31, so this branch is defensive.
    LD HL,(PAL_COPY_POS)
    LD DE,PAL_NEXT_IDS-248
    ADD HL,DE
    EX DE,HL
    LD A,23
.length:
    LD C,A
    LD B,0
    LD HL,(PAL_COPY_POS)
    LD A,H
    OR A
    JR NZ,.raw
    LD A,L
    CP 248
    JR NC,.raw
    ; The source record stores one byte per descriptor run. Select the fixed
    ; expander for this32-byte destination chunk (the last contains24bytes).
    PUSH DE
    DUP 4
    RRCA
    EDUP
    AND 14
    LD L,A
    LD H,0
    LD DE,palette_rgb_copies
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    PUSH DE
    POP IX
    POP DE
    LD HL,(PAL_COPY_POS)
    ADD HL,BC
    LD (PAL_COPY_POS),HL
    PUSH HL
    LD HL,(PAL_COPY_SOURCE)
    LD A,(PAL_COPY_BANK)
    LD ($7000),A
    CALL .expand
    JR .copied
.expand:
    JP (IX)
.raw:
    LD HL,(PAL_COPY_POS)
    ADD HL,BC
    LD (PAL_COPY_POS),HL
    PUSH HL
    LD HL,(PAL_COPY_SOURCE)
    LD A,(PAL_COPY_BANK)
    LD ($7000),A
    LDIR
.copied:
    LD (PAL_COPY_SOURCE),HL
    LD A,1
    LD ($7000),A
    POP HL
    LD DE,303
    OR A
    SBC HL,DE
    RET NZ
    CALL palette_translate_ids
    LD A,1
    LD (PAL_READY),A
    RET

; Prefetch uses only predictable colour state, never future gameplay. On any
; mismatch palette_prepare validates the actual post-core key before activation.
palette_prefetch:
    LD A,($C0A2)
    CP 127
    RET C
    LD B,A
    LD A,($C081)
    CP $C0
    RET C
    ; Rebase in the first idle prefetch slot, before the last copy chunk
    ; also translates31 class IDs. Keep the translate-side guard defensive.
    LD A,(PAL_READY)
    OR A
    JR NZ,.epoch_ready
    LD A,(PAL_GEN_SERIAL)
    CP 240
    CALL NC,palette_rebase_generations
.epoch_ready:
    LD A,B
    INC A
    JR NZ,.counter
    LD A,128
.counter:
    ADD A,A
    SRL A
    LD L,A
    LD A,($C086)
    CP 15
    JR Z,.grey
    CP 7
    JR Z,.grey
    LD H,1                       ; maskF7 group2 => keytable+256
    JR .lookup
.grey:
    LD A,L
    AND 7
    LD L,A
    LD H,0
.lookup:
    LD DE,palette_key_ids
    ADD HL,DE
    LD A,(HL)
    LD B,A
    LD A,(PAL_CUR_INDEX)
    CP B
    JP Z,palette_enemy_prefetch
    LD A,(PAL_NEXT_INDEX)
    CP B
    JR NZ,.start
    LD A,(PAL_READY)
    OR A
    JP NZ,palette_enemy_prefetch
    JP palette_copy_chunk
.start:
    LD A,B
    CALL palette_start_copy
    JP palette_copy_chunk

palette_begin_queue:
    LD HL,PAL_QUEUE
    LD (PAL_QUEUE_PTR),HL
    XOR A
    LD (PAL_QUEUE_COUNT),A
    RET

; Bank4 contains native routines for unique coalesced tile spans. Each tests
; exact class IDs and appends only dirty spans; no descriptor interpreter runs.
palette_compile_field:
    LD A,H
    CP $D0
    JP C,.dynamic_score
    PUSH HL
    LD DE,hud_background_names
    OR A
    SBC HL,DE
    POP HL
    JR C,.lookup
    LD A,L
    CP LOW hud_background_top
    LD HL,palette_top_background_program
    JR Z,.program
    LD HL,palette_bottom_background_program
    JR .program
.lookup:
    LD A,H
    SUB $D0
    LD H,A
    LD A,4
    LD ($7000),A
    LD DE,palette_program_lookup
    ADD HL,DE
    LD L,(HL)
    LD H,0
    ADD HL,HL
    LD DE,palette_program_pointers
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    EX DE,HL
.program:
    LD A,4
    LD ($7000),A
    LD DE,(PAL_QUEUE_PTR)
    CALL .execute
    LD (PAL_QUEUE_PTR),DE
    LD A,1
    LD ($7000),A
    RET
.execute:
    JP (HL)
.dynamic_score:
    LD A,4
    LD ($7000),A
    LD DE,(PAL_QUEUE_PTR)
    LD B,3
.digit:
    LD A,(HL)
    PUSH BC
    PUSH HL
    LD L,A
    LD H,0
    ADD HL,HL
    LD BC,palette_dynamic_programs
    ADD HL,BC
    LD C,(HL)
    INC HL
    LD B,(HL)
    LD H,B
    LD L,C
    CALL .execute
    POP HL
    POP BC
    INC HL
    DJNZ .digit
    LD (PAL_QUEUE_PTR),DE
    LD A,1
    LD ($7000),A
    RET

palette_set_pages:
    LD A,(HUD_COLOR_BANK)
    RRCA
    RRCA
    RRCA
    RRCA
    ADD A,HIGH hud_top_class_ids
    LD (PAL_CLASS_PAGE),A
    ADD A,HIGH hud_top_cache-HIGH hud_top_class_ids
    LD (PAL_CACHE_PAGE),A
    RET

palette_tile_color:
    CALL palette_set_pages
    LD L,C
    LD A,(PAL_CLASS_PAGE)
    LD H,A
    LD A,(HL)
    LD E,A
    ADD A,LOW HUD_CLASS_SIGNATURES
    LD L,A
    LD H,HIGH HUD_CLASS_SIGNATURES
    LD A,(HL)
    LD L,C
    LD D,A
    LD A,(PAL_CACHE_PAGE)
    LD H,A
    LD A,D
    CP (HL)
    RET Z
    LD (HL),A
    LD A,E
    ADD A,A
    ADD A,A
    ADD A,A
    LD E,A                       ; class row offset0..240
    LD A,C
    LD D,0
    DUP 3
    ADD A,A
    RL D
    EDUP
    LD L,A
    LD A,(HUD_COLOR_BANK)
    ADD A,$60                    ; VRAM write address high for2000/3000
    OR D
    LD H,A
    LD D,H
    LD A,L
    LD L,E
    LD E,A
    LD A,(PAL_CURRENT_PAGE)
    LD H,A
    LD B,8
    JP vram_copy_short

palette_commit:
    LD A,(PAL_QUEUE_COUNT)
    OR A
    RET Z
    LD HL,(PAL_QUEUE_PTR)
    LD DE,palette_commit_done
    LD (HL),E
    INC HL
    LD (HL),D
    LD (PAL_SAVED_SP),SP
    LD IX,palette_write_uniform_slow
    LD IY,palette_write_vector_slow
    LD A,(PAL_FAST_VBLANK)
    OR A
    JR Z,.stream
    LD IX,palette_write_uniform_fast
    LD IY,palette_write_vector_fast
.stream:
    LD SP,PAL_QUEUE
    LD A,(PAL_CURRENT_PAGE)
    LD H,A
    LD C,$98
    RET
palette_commit_done:
    LD SP,(PAL_SAVED_SP)
    LD A,(PAL_BASE_RESET_PENDING)
    OR A
    JR Z,.done
    LD A,(HUD_CLASS_SIGNATURES+HUD_SCORE_CLASS0)
    LD (hud_top_cache+HUD_BLANK_TILE),A
.done:
    XOR A
    LD (PAL_QUEUE_COUNT),A
    LD (PAL_BASE_RESET_PENDING),A
    RET

; H keeps the RGB page throughout the return-address stream. D/E are scratch
; and OUTI never crosses the248-byte source image's page boundary.
palette_write_vector_slow:
    DUP 7
    OUTI
    JP $+3
    EDUP
    OUTI
    LD L,E
    DEC D
    JP NZ,palette_write_vector_slow
    RET
palette_write_uniform_slow:
    DUP 8
    OUT ($98),A
    INC DE
    NOP
    NOP
    EDUP
    DJNZ palette_write_uniform_slow
    RET

; TI DataManual2.1.5: the4.3ms vertical-refresh window has no slot wait and
; permits2us accesses. MSX OUT12cycles=3.35us, OUTI18=5.03us. These paths are
; selected only by the paced VBlank commit, never by active-display uploads.
palette_write_vector_fast:
    DUP 8
    OUTI
    EDUP
    DEC D
    RET Z
    LD L,E
    JP palette_write_vector_fast
palette_write_uniform_fast:
    DUP 8
    OUT ($98),A
    EDUP
    DJNZ palette_write_uniform_fast
    RET

palette_commit_sat:
    LD A,(PAL_FAST_VBLANK)
    OR A
    JP Z,vram_copy_short
    LD A,E
    OUT ($99),A
    LD A,D
    OR $40
    OUT ($99),A
    LD C,$98
    DUP 36
    OUTI
    EDUP
    RET

; ASCII16: code in bank0, source/art in bank1, expanded rows in banks2/3.
; Only this direct transfer temporarily changes page2. DI remains in force and
; bank1 is restored before any source/art lookup or caller can observe page2.
upload_banked_lane:
    LD A,(lane_var)
    LD E,A
    LD D,0
    LD HL,$C0D9
    ADD HL,DE
    BIT 3,(HL)
    LD A,(phase_page)
    JR Z,.phase
    ADD A,16
.phase:
    LD E,A
    LD A,(source_ptr)
    LD L,A
    IFDEF WITH_PALETTE
    LD H,HIGH enemy_windows_low
    LD A,(HL)
    INC H
    LD H,(HL)
    LD L,A
    LD A,E
    ADD A,A
    ADD A,E
    LD E,A
    ADD HL,DE
    ELSE
    LD H,HIGH enemy_windows
    LD L,(HL)
    LD H,0
    DUP 5
    ADD HL,HL
    EDUP
    ADD HL,DE
    LD D,H
    LD E,L
    ADD HL,HL
    ADD HL,DE
    LD DE,enemy_pointers
    ADD HL,DE
    ENDIF
    LD E,(HL)
    INC HL
    LD D,(HL)
    INC HL
    LD A,(HL)
    LD ($7000),A
    EX DE,HL
    PUSH HL
    IFDEF WITH_HUD
    LD A,(tile_base)
    LD D,0
    DUP 3
    ADD A,A
    RL D
    EDUP
    LD E,A
    LD A,(lane_var)
    CP 3
    JR Z,1F
    LD A,D
    OR 8
    LD D,A
1:
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
    DUP 5
    RRCA
    EDUP
    ADD A,D
    LD D,A
    ENDIF
    POP HL
    LD A,(lane_var)
    OR A
    JR Z,.split
    LD B,48
    CALL vram_copy_short
    JR .restore
.split:
    IFNDEF WITH_HUD
    PUSH DE
    ENDIF
    LD B,24
    CALL vram_copy_short
    IFDEF WITH_HUD
    LD A,(tile_bottom_base)
    LD D,0
    DUP 3
    ADD A,A
    RL D
    EDUP
    LD E,A
    LD A,D
    OR $10
    LD D,A
    ELSE
    POP DE
    EX DE,HL
    LD BC,$0818
    ADD HL,BC
    EX DE,HL
    ENDIF
    LD B,24
    CALL vram_copy_short
.restore:
    LD A,1
    LD ($7000),A
    RET

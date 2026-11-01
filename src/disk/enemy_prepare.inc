    MACRO compact_prepare which
    LD A,($C09E+which)
    LD L,A
    LD H,HIGH collision_clip_masks
    LD A,($C0A4+which)
    AND (HL)
    LD ($CE80+8*which+6),A
    JR Z,1F
    LD A,($C0D9+which)
    AND 8
    JR Z,2F
    LD A,(phase_page)
    ADD A,16
    JR 3F
2:
    LD A,(phase_page)
3:
    ADD A,HIGH expand_lut
    LD H,A
    LD A,(source_ptr)
    SUB $A4
    LD L,A
    LD ($CE80+8*which),HL
    LD A,(tile_base)
    LD D,0
    DUP 3
    ADD A,A
    RL D
    EDUP
    LD E,A
    IF which != 3
    LD A,D
    OR 8
    LD D,A
    ENDIF
    LD ($CE80+8*which+2),DE
    LD A,(tile_bottom_base)
    LD D,0
    DUP 3
    ADD A,A
    RL D
    EDUP
    LD E,A
    IF which != 3
    LD A,D
    IF which == 0
    OR $10
    ELSE
    OR 8
    ENDIF
    LD D,A
    ENDIF
    LD ($CE80+8*which+4),DE
1:
    ENDM

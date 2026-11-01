PAL_TRANSLATE_POS EQU $CEB7
PAL_TRANSLATE_GEN EQU $CEB8
PAL_DEFAULT_STATIC EQU $C640

palette_translate_ids_banked:
    LD A,(PAL_GEN_SERIAL)
    CP 240
    CALL NC,palette_rebase_generations
    LD A,(PAL_GEN_SERIAL)
    INC A
    LD (PAL_GEN_SERIAL),A
    LD (PAL_TRANSLATE_GEN),A
    XOR A
    LD (PAL_TRANSLATE_POS),A
    RET

palette_translate_ids_chunk:
    LD A,(PAL_TRANSLATE_POS)
    LD L,A
    LD H,0
    PUSH HL
    POP IX
    PUSH HL
    POP IY
    LD BC,PAL_DEFAULT_STATIC
    ADD IX,BC
    LD BC,HUD_CLASS_SIGNATURES
    ADD IY,BC
    LD H,$C6
    LD E,L
    SET 7,E
    LD D,H
    LD A,31
    SUB L
    CP 8
    JR C,.length
    LD A,8
.length:
    LD B,A
    LD A,(PAL_TRANSLATE_GEN)
    LD C,A
    LD A,(PAL_STATIC_DEFAULT)
    OR A
    JR NZ,.from_default
.loop:
    LD A,(HL)
    CP (IX+0)
    LD A,1
    JR Z,.store
    LD A,(HL)
    EX DE,HL
    CP (HL)
    EX DE,HL
    LD A,C
    JR NZ,.store
    LD A,(IY+0)
.store:
    LD (IY+32),A
    INC L
    INC E
    INC IX
    INC IY
    DJNZ .loop
    JR .done
.from_default:
    LD A,(HL)
    CP (IX+0)
    LD A,1
    JR Z,.default_store
    LD A,C
.default_store:
    LD (IY+32),A
    INC L
    INC E
    INC IX
    INC IY
    DJNZ .from_default
.done:
    LD A,L
    LD (PAL_TRANSLATE_POS),A
    CP 31
    LD A,0
    RET NZ
    LD A,1
    RET

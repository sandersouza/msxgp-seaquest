forecast_lookup_program:
    LD A,L
    AND 63
    LD C,A
    LD A,L
    RLCA
    RLCA
    AND 3
    LD E,A
    LD A,H
    ADD A,A
    ADD A,A
    OR E
    LD B,A
    LD L,C
    LD H,0
    LD DE,forecast_hash_displacements
    ADD HL,DE
    LD A,(HL)
    ADD A,B
    LD L,A
    LD H,0
    LD DE,forecast_lookup
    ADD HL,DE
    LD L,(HL)
    LD H,0
    RET

forecast_dynamic_writer:
    OR A
    JR Z,.zero
    CP 185
    JR C,.invalid
    CP 251
    JR NC,.invalid
    SUB 185
    LD L,A
    LD H,0
    ADD HL,HL
    LD DE,forecast_dynamic_writers
    ADD HL,DE
    LD E,(HL)
    INC HL
    LD D,(HL)
    RET
.zero:
    LD DE,(forecast_dynamic_zero)
    RET
.invalid:
    LD DE,0
    RET

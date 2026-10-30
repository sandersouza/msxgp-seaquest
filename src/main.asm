; MSX1 hardware diagnostic scaffold. This is not a playable Seaquest build.
    ORG $4000
    DB "AB"
    DW init
    DW 0, 0, 0
    DS 6, 0

init:
    DI
    LD SP, $F380                 ; below the BIOS work area
    LD A, 2
    CALL $005F                   ; CHGMOD: SCREEN 2
    LD HL, 0
    LD BC, $1800
    LD A, $FF
    CALL $0056                   ; FILVRM: solid tile patterns in all three banks
    LD HL, $2000
    LD BC, $1800
    LD A, $21                    ; medium green on black
    CALL $0056
    LD HL, $1800
    LD BC, $300
    XOR A
    CALL $0056                   ; name table filled with tile 0
    LD HL, $C000
    LD (HL), $53
    INC HL
    LD (HL), $51
    INC HL
    LD (HL), 0                   ; incremented once per BIOS interrupt
    EI
loop:
    HALT
    LD HL, $C002
    INC (HL)
    JR loop

    ASSERT $ < $8000
    DS $C000-$, $FF              ; plain 32 KiB cartridge, $4000-$BFFF

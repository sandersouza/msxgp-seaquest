; Sample at original F6A7, after frame increment and before console/joystick use.
; Main BIOS must be visible in page 0. The polled renderer disables VDP IRQs:
; BIOS routines may execute EI internally. DI on return also protects SP clearing.
input_switches EQU $C420
input_previous EQU $C421
input_keys EQU $C422
input_row6 EQU $C423
input_psg15 EQU $C424

input_init:
    LD A,$3F                    ; both players B; color, Reset/Select released
    LD (input_switches),A
    XOR A
    LD (input_previous),A
    RET

sample_input:
    PUSH AF
    PUSH BC
    PUSH DE
    PUSH HL
    ; SNSMAT/RDPSG/WRTPSG preserve IX/IY, and this routine never uses them.
    LD A,6
    CALL $0141                  ; SNSMAT: F1/F2/F3 are bits 5/6/7
    DI
    LD (input_row6),A
    CPL
    AND $80
    RRCA                        ; F3 -> player 1 difficulty, SWCHB bit 6
    LD B,A
    LD A,7
    CALL $0141                  ; F4 is bit 0
    DI
    CPL
    AND 1
    RRCA                        ; F4 -> player 2 difficulty, SWCHB bit 7
    OR B
    LD B,A
    LD A,(input_previous)
    CPL
    AND B                       ; only newly held difficulty keys toggle
    LD C,A
    LD A,B
    LD (input_previous),A
    LD A,(input_switches)
    XOR C
    LD (input_switches),A
    LD B,A
    LD A,(input_row6)
    RRCA
    RRCA
    RRCA
    RRCA
    RRCA
    AND 3                       ; F1 Reset/F2 Select remain held levels
    OR $FC
    AND B
    LD ($C282),A

    LD A,8
    CALL $0141                  ; retain opposing keys, bypass GTSTCK's table
    DI
    LD (input_keys),A
    ; Read each raw joystick once through BIOS PSG access. GTSTCK normalizes
    ; opposing directions; raw samples preserve the original 16 combinations.
    LD A,15
    CALL $0096                  ; RDPSG, save all peripheral output bits
    LD (input_psg15),A
    AND $BF
    OR $0F                      ; release both ports' trigger output lines
    LD E,A
    LD A,15
    CALL $0093                  ; WRTPSG, select joystick 1
    DI
    LD A,14
    CALL $0096
    LD B,A
    RLCA
    RLCA
    RLCA
    AND $80                     ; primary fire is active low bit 4
    LD ($C00C),A
    LD A,B
    AND $0F
    RLCA
    RLCA
    RLCA
    RLCA
    LD C,A
    SET 6,E
    LD A,15
    CALL $0093                  ; select joystick 2
    DI
    LD A,14
    CALL $0096
    LD B,A
    RLCA
    RLCA
    RLCA
    AND $80
    IFDEF INPUT_CORRUPT_PORT2
    XOR $80                     ; deliberate negative control, never normal build
    ENDIF
    LD ($C00D),A
    LD A,B
    AND $0F
    OR C
    LD ($C280),A
    LD A,(input_psg15)
    LD E,A
    LD A,15
    CALL $0093                  ; restore selection, strobes and other outputs
    DI

    ; Keyboard joins the currently selected original port, not both players.
    LD A,(input_keys)            ; row8: space,home,ins,del,left,up,down,right
    LD B,$0F
    BIT 5,A
    JR NZ,.down
    RES 0,B
.down:
    BIT 6,A
    JR NZ,.left
    RES 1,B
.left:
    BIT 4,A
    JR NZ,.right
    RES 2,B
.right:
    BIT 7,A
    JR NZ,.keyboard
    RES 3,B
.keyboard:
    LD A,($C0B7)
    OR A
    LD A,B
    JR NZ,.second
    RLCA
    RLCA
    RLCA
    RLCA
    OR $0F
    JR .mask_ready
.second:
    OR $F0                      ; retain the other joystick nibble
.mask_ready:
    LD B,A
    LD A,($C280)
    AND B
    LD ($C280),A
    LD A,(input_keys)
    BIT 0,A
    JR NZ,.done
    LD A,($C0B7)
    LD E,A
    LD D,0
    LD HL,$C00C
    ADD HL,DE
    LD (HL),0
.done:
    POP HL
    POP DE
    POP BC
    POP AF
    RET

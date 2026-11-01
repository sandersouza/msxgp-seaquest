BOOT_VIDEO_ID EQU $F3F0
native_init:
    DI
    LD SP,$F380
    XOR A
    LD HL,$C000
    LD DE,$C001
    LD BC,$0FFF
    LD (HL),A
    LDIR
    LD HL,$EC00
    LD DE,$EC01
    LD BC,$03FF
    LD (HL),A
    LDIR
    CALL render_init
    CALL input_init
    CALL audio_init
    CALL hud_init
    CALL video_init
    LD HL,$C000
    LD DE,$C001
    LD BC,1023
    LD (HL),0
    LDIR
    LD A,1
    LD ($C082),A
    CALL core_FB54
    CALL neutral_contacts
    LD A,$53
    LD ($C7FD),A
native_boot_ready:
    JP paced_frame_start

native_chgmod:
    LD HL,native_vdp_registers
    LD B,8
    LD C,$80
.register:
    LD A,(HL)
    OUT ($99),A
    LD A,C
    OUT ($99),A
    INC HL
    INC C
    DJNZ .register
    LD A,$82
    LD ($F3E0),A
    LD A,6
    LD ($F3E1),A
    LD A,4
    LD ($F3E7),A
    RET
native_vdp_registers:
    DB 2,$82,6,$FF,3,$36,7,4

native_wrtvdp:
    LD A,C
    ADD A,$DF
    LD L,A
    LD H,$F3
    LD (HL),B
    LD A,B
    OUT ($99),A
    LD A,C
    OR $80
    OUT ($99),A
    RET

native_filvrm:
    PUSH AF
    LD A,L
    OUT ($99),A
    LD A,H
    OR $40
    OUT ($99),A
    POP AF
    LD D,A
.byte:
    LD A,D
    OUT ($98),A
    DEC BC
    LD A,B
    OR C
    JR NZ,.byte
    RET

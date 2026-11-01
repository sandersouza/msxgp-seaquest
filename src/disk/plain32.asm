; Plain 32 KiB cartridge, using the same RAM runtime as the DOS1 executable.
    ORG $4000
    DB "AB"
    DW rom_init,0,0,0
    DS 6,0
rom_init:
    DI
    LD SP,$F3E0
    ; BIOS slot API exposes both halves of this ordinary 32 KiB cartridge.
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
    LD DE,4
    ADD HL,DE
    LD A,(HL)
    AND $0C
    OR C
    LD H,$80
    CALL $0024
    DI
    LD A,($002B)
    LD ($F3F0),A
    ; Preserve the actual page3 RAM's primary and secondary slot identity.
    IN A,($A8)
    RLCA
    RLCA
    AND 3
    LD E,A
    LD L,A
    LD H,0
    LD BC,$FCC1
    ADD HL,BC
    LD A,(HL)
    AND $80
    LD ($F3F3),A
    LD A,E
    CALL replicate_slot
    LD ($F3F1),A
    LD A,($FFFF)
    CPL
    RLCA
    RLCA
    AND 3
    CALL replicate_slot
    LD ($F3F2),A
    LD A,$82
    OUT ($99),A
    LD A,$81
    OUT ($99),A
    IN A,($99)
    LD HL,resident_data
    LD DE,$3800
    LD BC,1504
    CALL write_vram
    LD HL,low_data
    LD DE,$3000
    LD BC,$300
    CALL write_vram
    LD HL,main_data
    LD DE,0
    LD BC,$3000
    CALL write_vram
    LD HL,main_data+$3000
    LD DE,$C000
    LD BC,main_end-main_data-$3000
    LDIR
    LD HL,high_data
    LD DE,$E300
    LD BC,high_end-high_data
    LDIR
    LD HL,reloc_data
    LD DE,$F300
    LD BC,reloc_end-$F300
    LDIR
    LD HL,map_data
    LD DE,$F400
    LD BC,map_end-$F400
    LDIR
    JP map_ram
replicate_slot:
    LD B,A
    RLCA
    RLCA
    OR B
    LD B,A
    RLCA
    RLCA
    RLCA
    RLCA
    OR B
    RET
write_vram:
    LD A,E
    OUT ($99),A
    LD A,D
    OR $40
    OUT ($99),A
.byte:
    LD A,(HL)
    OUT ($98),A
    INC HL
    DEC BC
    LD A,B
    OR C
    JR NZ,.byte
    RET
map_data:
    PHASE $F400
map_ram:
    LD A,($F3F3)
    OR A
    JR Z,.primary
    LD A,($F3F2)
    LD ($FFFF),A
.primary:
    LD A,($F3F1)
    OUT ($A8),A
    ; Reject absent/aliased lower RAM instead of executing corrupted data.
    LD A,$11
    LD ($0000),A
    ADD A,$11
    LD ($4000),A
    ADD A,$11
    LD ($8000),A
    ADD A,$11
    LD ($F000),A
    LD A,($0000)
    CP $11
    JR NZ,ram_error
    LD A,($4000)
    CP $22
    JR NZ,ram_error
    LD A,($8000)
    CP $33
    JR NZ,ram_error
    LD HL,$C000
    LD DE,$3000
    LD BC,main_end-main_data-$3000
    LDIR
    XOR A
    OUT ($99),A
    OUT ($99),A
    LD HL,0
    LD BC,$3000
.read:
    IN A,($98)
    LD (HL),A
    INC HL
    DEC BC
    LD A,B
    OR C
    JR NZ,.read
    JP takeover
ram_error:
    LD A,6
    OUT ($99),A
    LD A,$87
    OUT ($99),A
    HALT
    JR ram_error
map_end:
    DEPHASE
reloc_data:
    PHASE $F300
takeover:
    LD HL,$E300+high_end-high_data-1
    LD DE,$FFF3
    CALL dzx0_standard_back
    LD HL,main_end-main_data-1
    LD DE,$F2FF
    CALL dzx0_standard_back
    XOR A
    OUT ($99),A
    LD A,$30
    OUT ($99),A
    LD HL,$0100
    LD BC,$0300
.restore:
    IN A,($98)
    LD (HL),A
    INC HL
    DEC BC
    LD A,B
    OR C
    JR NZ,.restore
    JP $0100
    INCLUDE "../third_party/zx0/dzx0_standard_back.asm"
reloc_end:
    ASSERT reloc_end < $F3D0
    DEPHASE
resident_data:
    INCBIN "../../outputs/disk/resident.bin"
low_data:
    INCBIN "../../outputs/disk/low.bin"
high_data:
    INCBIN "../../outputs/disk/high.bin.zx0"
high_end:
main_data:
    INCBIN "../../outputs/disk/main.bin.zx0"
main_end:
    ASSERT main_end-main_data-$3000 < $2300
    ASSERT $ < $C000
    DS $C000-$,$FF

; DOS1 entry; all DOS services finish before RAM takeover.
    ORG $0100
dos_entry:
    LD HL,($0006)
    LD DE,com_end+128
    OR A
    SBC HL,DE
    LD DE,error_memory
    JR C,dos_error
    LD HL,payload
    LD BC,payload_end-payload
    LD DE,0
.sum:
    LD A,(HL)
    ADD A,E
    LD E,A
    JR NC,.next
    INC D
.next:
    INC HL
    DEC BC
    LD A,B
    OR C
    JR NZ,.sum
    LD HL,PAYLOAD_SUM
    OR A
    SBC HL,DE
    LD DE,error_data
    JR NZ,dos_error
    LD A,($FCC1)
    LD HL,$002B
    CALL $000C
    LD ($F3F0),A
    DI
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
    LD DE,0
    LD BC,$300
    CALL write_vram
    LD HL,reloc_data
    LD DE,$F300
    LD BC,reloc_end-$F300
    LDIR
    JP takeover
dos_error:
    LD C,9
    CALL 5
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
error_memory:
    DB "Seaquest needs an original 64 KB MSX1 and enough DOS TPA.",13,10,"$"
error_data:
    DB "Seaquest: damaged executable. Copy the file again.",13,10,"$"
reloc_data:
    PHASE $F300
takeover:
    LD SP,$F3E0
    LD HL,high_end-1
    LD DE,$FFF3
    CALL dzx0_standard_back
    LD HL,main_data
    LD DE,0
    LD BC,main_end-main_data
    LDIR
    LD HL,main_end-main_data-1
    LD DE,$F2FF
    CALL dzx0_standard_back
    XOR A
    OUT ($99),A
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
    ASSERT reloc_end <= $F3D0
    DEPHASE
payload:
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
payload_end:
com_end:
    ASSERT com_end+128 < $C000

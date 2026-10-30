    ORG $4000
    DB "AB"
    DW init
    DW 0,0,0
    DS 6,0
init:
    DI
    LD SP,$F380
    LD A,$53
    LD ($C7FD),A
idle:
    JP idle
rpc_start:
    DI
    LD SP,$F380
    LD A,($C6F4)
    LD E,A
    LD BC,($C6F2)
    LD HL,($C6F0)
    PUSH HL
    POP AF
    LD HL,rpc_done
    PUSH HL
    LD HL,($C6FE)
    JP (HL)
rpc_done:
    NOP
    JP idle
    INCLUDE "../outputs/native/core.inc"
original_rom:
    INCBIN "../outputs/native/original.rom"
    ASSERT $ < $C000
    DS $C000-$,$FF

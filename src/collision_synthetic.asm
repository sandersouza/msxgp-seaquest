; Assembly-only public CI fixture. Every source/data byte is synthetic zero.
    ORG $4000
    DB "AB"
    DW idle
    DS 12,0
idle:
    JP idle
    INCLUDE "oxygen.asm"
    INCLUDE "collision.asm"
    ALIGN 256
original_rom:
    DS 4096,0
    ASSERT $ <= $C000
    DS $C000-$,$FF

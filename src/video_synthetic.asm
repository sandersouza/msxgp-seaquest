; Original-free assembly probe; not a gameplay or timing acceptance cartridge.
    ORG $4000
    DB "AB"
    DW init
    DS 12,0
init:
    DI
    LD SP,$F380
    CALL video_init
loop:
    CALL video_extra_tick
    CALL video_prepare_extra
    JP loop
    INCLUDE "video.asm"
core_F5B8:
acquire_frame_state:
    RET
    ASSERT $ < $8000
    DS $8000-$,$FF

; Portable assembly check: mathematical PSG tables only, no original assets.
    ORG $4000
    DB "AB"
    DW start,0,0,0,0,0,0
start:
    DI
    LD SP,$F380
    CALL audio_init
.idle:
    JP .idle
    INCLUDE "audio.asm"
    INCLUDE "../outputs/presentation/audio-tables.inc"
    ASSERT $ <= $8000
    DS $8000-$,$FF

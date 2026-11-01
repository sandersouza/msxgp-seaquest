COMPACT_BOTTOM EQU $CEA0
COMPACT_META EQU $CE80
    INCLUDE "enemy_transfer.inc"

upload_banked_lane:
    RET

compact_dispatch:
    JP (IY)

compact_commit_enemies:
    LD IY,compact_slow
    LD A,(PAL_FAST_VBLANK)
    LD B,A
    LD A,(PAL_DISPLAY_OFF)
    OR B
    JR Z,.selected
    LD IY,compact_fast
.selected:
    DUP 4,lane
    LD A,(COMPACT_META+8*lane+6)
    OR A
    JR Z,1F
    LD HL,(COMPACT_META+8*lane+4)
    LD (COMPACT_BOTTOM),HL
    LD HL,(COMPACT_META+8*lane)
    LD DE,(COMPACT_META+8*lane+2)
    LD C,$98
    CALL compact_dispatch
1:
    EDUP
    RET

compact_slow:
    compact_transfer 0
compact_fast:
    compact_transfer 1

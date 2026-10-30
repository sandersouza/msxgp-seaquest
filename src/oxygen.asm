; F44F..F473 raster-derived logical alarm. Color/PSG presentation is separate.
; Called before F5B8 with the OLD frame's state, including after Reset/Select.
prepare_oxygen:
    LD B,0
    LD A,($C0E1)
    CP 13
    JR Z,.store
    LD A,($C0E9)
    OR A
    JR NZ,.store
    LD A,($C0E6)
    DEC A
    CP 16
    JR NC,.store
    LD B,15
.store:
    LD A,B
    IFDEF OXYGEN_CORRUPT
    XOR 15
    ENDIF
    LD ($C0F9),A
    RET

acquire_frame_state:
    CALL prepare_oxygen
    JP acquire_contacts

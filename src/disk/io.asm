native_snsmat:
    LD L,A
    IN A,($AA)
    AND $F0
    OR L
    OUT ($AA),A
    IN A,($A9)
    RET
native_rdpsg:
    OUT ($A0),A
    IN A,($A2)
    RET
native_wrtpsg:
    OUT ($A0),A
    PUSH AF
    LD A,E
    OUT ($A1),A
    POP AF
    RET

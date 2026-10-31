; NTSC4K source:262 scanlines/update. PAL TMS9929A:313 lines/display.
; The fractional51/262 accumulator retains exact mean source speed. An extra
; source update has its own raster contacts, input sample and ordered audio;
; only its presentation is omitted. Acquire its contacts after the preceding
; complete render preparation to spread the work across adjacent PAL frames.
VIDEO_PAL EQU $C428
VIDEO_ACCUM EQU $C429
VIDEO_PENDING EQU $C42B

video_init:
    LD A,($002B)               ; BIOS IDBYT1 default VDP frequency, MSX1 fixed
    AND $80
    OR 1                      ; first preparation clears stale boot status once
    LD (VIDEO_PAL),A
    LD HL,0
    LD (VIDEO_ACCUM),HL
    XOR A
    LD (VIDEO_PENDING),A
    RET

video_extra_tick:
    LD A,(VIDEO_PENDING)
    OR A
    RET Z
    XOR A
    LD (VIDEO_PENDING),A
    LD E,A
    LD BC,$8200
video_extra_core_start:
    JP core_F5B8

video_prepare_extra:
    LD A,(VIDEO_PAL)
    OR A
    RET Z
    RRCA
    JR NC,.clock
    LD A,(VIDEO_PAL)
    AND $80
    LD (VIDEO_PAL),A
    IN A,($99)
    RET
.clock:
    LD HL,(VIDEO_ACCUM)
    LD DE,51
    ADD HL,DE
    LD A,H
    OR A
    JR Z,video_store_accum
    LD A,L
    CP 6                      ;262 = $0106
    JR C,video_store_accum
    LD DE,-262
    ADD HL,DE
    LD (VIDEO_ACCUM),HL
    LD A,1
    LD (VIDEO_PENDING),A
video_extra_acquire:
    JP acquire_frame_state
video_store_accum:
    LD (VIDEO_ACCUM),HL
    RET

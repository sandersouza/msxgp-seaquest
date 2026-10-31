; Each original AUDC/AUDF/AUDV store reaches the PSG in source order. Alternate
; registers isolate all main6502 registers/flags, including carry in E. DI is
; required by the platform; no BIOS routine or PSG15 write occurs here.
AUDIO_CTL EQU $C460
AUDIO_FREQ EQU $C462
AUDIO_VOLUME EQU $C464
AUDIO_PERIOD EQU $C466
AUDIO_MIXER EQU $C46A
AUDIO_NOISE EQU $C46B
AUDIO_PORTS EQU $C46C
AUDIO_OWNER EQU $C46D
AUDIO_PARTS EQU $C46E

    MACRO audio_handler handler_name, source, previous, value_mask, channel, kind
handler_name:
    EX AF,AF'
    EXX
    LD A,(source)
    AND value_mask
    LD HL,previous
    IF kind==2
    LD D,(HL)
    ENDIF
    CP (HL)
    JP Z,audio_event_done
    LD (HL),A
    IF kind<2
    IF kind==0
    ADD A,LOW audio_mixer_parts
    LD L,A
    LD H,HIGH audio_mixer_parts
    LD A,(HL)
    LD (AUDIO_PARTS+channel),A
    ENDIF
    CALL audio_period_0+channel*(audio_period_1-audio_period_0)
    IF kind==0
    CALL audio_mixer
    CALL audio_owner
    ELSE
    LD A,(AUDIO_OWNER)
    CP channel
    CALL Z,audio_noise
    ENDIF
    ELSE
    LD B,8+channel
    CALL audio_write
    LD A,D
    OR A
    JR Z,1F
    LD A,(HL)
    OR A
    JP NZ,audio_event_done
1:
    CALL audio_owner
    ENDIF
    IF kind==2
    JR audio_event_done
    ELSE
    JP audio_event_done
    ENDIF
    ENDM

    audio_handler audio_event_15,$C015,AUDIO_CTL,15,0,0
    audio_handler audio_event_16,$C016,AUDIO_CTL+1,15,1,0
    audio_handler audio_event_17,$C017,AUDIO_FREQ,31,0,1
    audio_handler audio_event_18,$C018,AUDIO_FREQ+1,31,1,1
    audio_handler audio_event_19,$C019,AUDIO_VOLUME,15,0,2
    audio_handler audio_event_1A,$C01A,AUDIO_VOLUME+1,15,1,2
audio_event_done:
    EXX
    EX AF,AF'
audio_event_restored:
    RET

; Source stores have already passed a masked-value change test. For a tonal
; source change, project its period immediately; DC/noise keep the held period.
    MACRO audio_period_handler name, channel
name:
    LD A,(AUDIO_PARTS+channel)
    BIT 5,A
    RET NZ
    AND $C0
    LD D,A
    LD A,(AUDIO_FREQ+channel)
    ADD A,A
    ADD A,D
    LD L,A
    LD H,HIGH audio_periods
    LD E,(HL)
    INC L
    LD D,(HL)
    LD A,channel*2
    OUT ($A0),A
    LD A,E
    OUT ($A1),A
    LD A,channel*2+1
    OUT ($A0),A
    LD A,D
    OUT ($A1),A
    RET
    ENDM
    audio_period_handler audio_period_0,0
    audio_period_handler audio_period_1,1

audio_mixer:
    LD A,(AUDIO_PARTS)
    AND 9
    LD B,A
    LD A,(AUDIO_PARTS+1)
    AND 9
    RLCA
    OR B
    OR $24                     ; third PSG channel stays disabled
    LD B,A
    LD A,(AUDIO_PORTS)
    OR B
    LD HL,AUDIO_MIXER
    CP (HL)
    RET Z
    LD (HL),A
    LD B,7
    JP audio_write

audio_owner:
    LD A,(AUDIO_MIXER)
    AND $18
    CP $18
    JR NZ,.enabled
    LD A,255
    LD (AUDIO_OWNER),A
    RET
.enabled:
    LD A,(AUDIO_CTL)
    CP 8
    JR Z,.channel0_volume
    CP 15
    JR NZ,.channel1
.channel0_volume:
    LD A,(AUDIO_VOLUME)
    OR A
    JR Z,.channel1
    XOR A
    JR .selected
.channel1:
    LD A,(AUDIO_CTL+1)
    CP 8
    JR Z,.channel1_volume
    CP 15
    JR NZ,.inactive
.channel1_volume:
    LD A,(AUDIO_VOLUME+1)
    OR A
    JR Z,.inactive
    LD A,1
    JR .selected
.inactive:
    LD A,255
.selected:
    LD HL,AUDIO_OWNER
    CP (HL)
    RET Z
    LD (HL),A
    CP 255
    RET Z
audio_noise:
    ADD A,LOW AUDIO_FREQ
    LD L,A
    LD H,HIGH AUDIO_FREQ
    LD A,(HL)
    ADD A,LOW audio_noise_periods
    LD L,A
    LD H,HIGH audio_noise_periods
    LD A,(HL)
    LD HL,AUDIO_NOISE
    CP (HL)
    RET Z
    LD (HL),A
    LD B,6
    JP audio_write

; A=value,B=register. PSG7's peripheral directions come from startup, and no
; code selects registers14/15 for output.
audio_write:
    PUSH AF
    LD A,B
    OUT ($A0),A
    POP AF
    OUT ($A1),A
    RET

audio_init:
    LD A,7
    OUT ($A0),A
    IN A,($A2)
    AND $C0
    LD (AUDIO_PORTS),A
    LD HL,audio_defaults
    LD C,0
.register:
    LD A,C
    OUT ($A0),A
    LD A,(HL)
    INC HL
    LD D,A
    LD A,C
    CP 7
    LD A,D
    JR NZ,.value
    LD A,(AUDIO_PORTS)
    OR 63
.value:
    OUT ($A1),A
    INC C
    LD A,C
    CP 11
    JR NZ,.register
    XOR A
    LD HL,AUDIO_CTL
    LD DE,AUDIO_CTL+1
    LD BC,5
    LD (HL),A
    LDIR
    LD HL,7
    LD (AUDIO_PERIOD),HL
    LD (AUDIO_PERIOD+2),HL
    LD A,(AUDIO_PORTS)
    OR 63
    LD (AUDIO_MIXER),A
    LD A,1
    LD (AUDIO_NOISE),A
    DEC A
    DEC A
    LD (AUDIO_OWNER),A
    LD A,41
    LD (AUDIO_PARTS),A
    LD (AUDIO_PARTS+1),A
    RET

audio_sync:
    LD A,($C017)
    AND 31
    LD (AUDIO_FREQ),A
    LD A,($C018)
    AND 31
    LD (AUDIO_FREQ+1),A
    CALL audio_event_15
    CALL audio_event_16
    CALL audio_event_17
    CALL audio_event_18
    CALL audio_event_19
    JP audio_event_1A

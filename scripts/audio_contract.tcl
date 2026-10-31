# Every target hook is observed before/after; source expectations are host6502.
set renderer none
set throttle off
set speed 999
set power true
set cases [open outputs/presentation/audio-cases.bin rb]
set events [open outputs/presentation/audio-events.bin wb]
set states [open outputs/presentation/audio-states.bin wb]
set count 0
set recording 0
proc audio_fail {reason} {puts stderr $reason; exit 1}
proc audio_registers {} {
    return [list [reg AF] [reg BC] [reg DE] [reg HL] [reg IX] [reg IY] [reg SP] [reg IFF]]
}
proc audio_next {} {
    set record [read $::cases 1029]
    if {![string length $record]} {
        close $::events; close $::states; close $::cases
        set f [open outputs/presentation/audio-complete.txt w]; puts $f $::count; close $f
        exit
        return
    }
    binary scan [string index $record 0] cu chained
    binary scan [string range $record 1 4] cu* keys
    foreach row {6 7 8} mask [lrange $keys 0 2] {
        keymatrixup $row 255; keymatrixdown $row $mask
    }
    debug write memory 0xC420 [lindex $keys 3]
    debug write memory 0xC421 0
    set ram [string range $record 5 end]
    if {$chained} {
        foreach offset {12 13 176 177 178 179 180 181 182 248 249 640 642} {
            binary scan [string index $ram $offset] cu value
            debug write memory [expr {0xC000+$offset}] $value
        }
        audio_start_core
        debug cont
        return
    }
    debug write_block memory 0xC000 $ram
    set ::recording 0
    reg PC $::audio_prime_only_start
    debug cont
}
proc audio_start_core {} {
    set ::recording 1
    reg SP 0xF37E
    debug write memory 0xF37E [expr {$::audio_prime_only_done&255}]
    debug write memory 0xF37F [expr {$::audio_prime_only_done>>8}]
    reg AF 0; reg BC 0x8200; reg DE 0; reg HL 0; reg IX 0x4567; reg IY 0x89AB
    reg PC $::core_F5B8
}
after time 5 {
    if {[debug read memory 0xC7FD]!=83} {audio_fail not-booted}
    foreach address $::audio_handlers {
        debug set_bp $address {$::recording} {
            set ::saved_audio_registers [audio_registers]
            set ::saved_audio_ports [expr {[debug read "PSG regs" 7]&192}]
            set ::saved_audio_15 [debug read "PSG regs" 15]
            set ::audio_started [machine_info time]
            set sp [reg SP]
            set return_pc [expr {[debug read memory $sp]|([debug read memory [expr {$sp+1}]]<<8)}]
            puts -nonewline $::events [binary format is $::count $return_pc]
            puts -nonewline $::events [debug read_block memory 0xC015 6]
            puts -nonewline $::events [binary format c [debug read memory 0xC081]]
        }
    }
    debug set_bp $::audio_event_restored {$::recording} {
        if {$::saved_audio_registers ne [audio_registers]} {audio_fail audio-clobbered-registers}
        if {[reg IFF]&3} {audio_fail interrupts-enabled}
        if {$::saved_audio_ports!=([debug read "PSG regs" 7]&192)} {audio_fail peripheral-directions-changed}
        if {$::saved_audio_15!=[debug read "PSG regs" 15]} {audio_fail peripheral-output-changed}
        if {$::inject_audio && $::count==0} {debug write "PSG regs" 8 15}
        puts -nonewline $::events [debug read_block "PSG regs" 0 11]
        puts -nonewline $::events [binary format i [expr {round(([machine_info time]-$::audio_started)*3579545)}]]
    }
    debug set_bp $::audio_prime_only_done {} {
        if {$::recording} {
            puts -nonewline $::states [debug read_block memory 0xC000 251]
            incr ::count
            debug break; after break audio_next
        } else {
            audio_start_core
        }
    }
    audio_next
}
after time 45 {audio_fail "audio-timeout count=$::count PC=[reg PC]"}

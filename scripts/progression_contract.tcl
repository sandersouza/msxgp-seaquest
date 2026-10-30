set renderer none
set throttle off
set speed 999
set power true
set input [open outputs/progression/cases.bin rb]
set count 0
set cycles {0 0 0}
proc finish {passed detail} {
    if {[debug read_block memory 0xD000 8960] ne [string repeat [binary format c 165] 8960]} {
        set passed false
        set detail ram-guard-corrupt
    }
    binary scan [debug read_block memory 0xF300 128] cu* stack
    set stack_min 62336
    for {set i 0} {$i<128} {incr i} {
        if {[lindex $stack $i]!=165} {set stack_min [expr {62208+$i}]; break}
    }
    set f [open outputs/progression/result.json w]
    puts $f "\{\"passed\":$passed,\"cases\":$::count,\"max_cycles\":\[[join $::cycles ,]\],\"stack_min\":$stack_min,\"detail\":\"$detail\"\}"
    close $f
    exit
}
proc next_case {} {
    set header [read $::input 10]
    if {![string length $header]} {finish true complete; return}
    binary scan $header cu* h
    set ::case_mode [lindex $h 2]
    set ram [read $::input 1024]
    set ::expected [read $::input 251]
    set ::status [read $::input 5]
    set ::check_status [lindex $h 9]
    if {[string length $header]!=10 || [string length $ram]!=1024 || [string length $::expected]!=251 || [string length $::status]!=5} {finish false truncated; return}
    if {$::case_mode!=2} {debug write_block memory 0xC000 $ram}
    keymatrixup 6 255
    keymatrixup 8 255
    keymatrixdown 6 [lindex $h 6]
    keymatrixdown 8 [lindex $h 7]
    debug write memory 0xC420 [lindex $h 8]
    debug write memory 0xC421 0
    if {$::case_mode==0} {
        reg AF [expr {[lindex $h 3]<<8}]
        reg BC [expr {[lindex $h 4]<<8}]
        reg DE [lindex $h 5]
        reg SP 0xF37E
        debug write memory 0xF37E [expr {$::done&255}]
        debug write memory 0xF37F [expr {$::done>>8}]
        reg PC [expr {[lindex $h 0]|([lindex $h 1]<<8)}]
    } else {reg PC $::integrated}
    set ::saved_psg15 [debug read "PSG regs" 15]
    set ::started [machine_info time]
    set ::watchdog [after time 0.1 {finish false stuck}]
    debug cont
}
proc compare_case {} {
    after cancel $::watchdog
    if {[reg IFF]&3 || [vdpreg 1]&32} {finish false interrupts-left-enabled; return}
    if {$::saved_psg15 != [debug read "PSG regs" 15]} {finish false psg15-not-restored; return}
    if {[info exists ::env(SEAQUEST_PROGRESSION_CORRUPT)] && !$::count} {
        debug write memory 0xC0BA [expr {[debug read memory 0xC0BA]^1}]
    }
    set cost [expr {round(([machine_info time]-$::started)*3579545)}]
    if {$cost>[lindex $::cycles $::case_mode]} {lset ::cycles $::case_mode $cost}
    set actual [debug read_block memory 0xC000 251]
    if {$actual ne $::expected} {
        binary scan $actual cu* aa
        binary scan $::expected cu* ee
        for {set i 0} {$i<251} {incr i} {
            if {[lindex $aa $i]!=[lindex $ee $i]} {
                finish false "byte=$i expected=[lindex $ee $i] actual=[lindex $aa $i]"
                return
            }
        }
    }
    if {$::check_status} {
        set f [expr {[reg AF]&255}]
        set status [binary format ccccc [expr {[reg AF]>>8}] [expr {[reg BC]>>8}] [expr {[reg BC]&255}] [expr {[reg DE]&255}] [expr {($f&128)|(($f&64)>>5)}]]
        if {$status ne $::status} {finish false score-register-or-NMOS-flag-mismatch; return}
    }
    incr ::count
    next_case
}
after time 5 {
    if {[debug read memory 0xC7FD]!=83} {finish false cartridge-not-booted; return}
    debug write_block memory 0xD000 [string repeat [binary format c 165] 9088]
    debug set_bp $::done {} {debug break; after break {if {[catch {compare_case} detail]} {puts stderr $detail; exit 1}}}
    if {[catch {next_case} detail]} {puts stderr $detail; exit 1}
}
after time 1000 {puts stderr progression-contract-timeout; exit 1}

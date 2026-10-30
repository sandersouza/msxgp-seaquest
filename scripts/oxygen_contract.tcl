set renderer none
set throttle off
set speed 999
set power true
set input [open outputs/oxygen/cases.bin rb]
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
    set f [open outputs/oxygen/result.json w]
    puts $f "\{\"passed\":$passed,\"cases\":$::count,\"max_cycles\":\[[join $::cycles ,]\],\"stack_min\":$stack_min,\"detail\":\"$detail\"\}"
    close $f
    exit
}
proc next_case {} {
    set header [read $::input 2]
    if {![string length $header]} {finish true complete; return}
    binary scan $header cu* fields
    set ::case_mode [lindex $fields 0]
    set keys [lindex $fields 1]
    set ram [read $::input 1024]
    set ::expected [read $::input 251]
    if {[string length $::expected]!=251} {finish false truncated; return}
    if {$::case_mode!=2} {debug write_block memory 0xC000 $ram}
    keymatrixup 8 255
    keymatrixdown 8 $keys
    debug write memory 0xC420 63
    debug write memory 0xC421 0
    reg PC [lindex $::entries $::case_mode]
    set ::saved_psg15 [debug read "PSG regs" 15]
    set ::started [machine_info time]
    set ::watchdog [after time 0.1 {finish false stuck}]
    debug cont
}
proc compare_case {} {
    after cancel $::watchdog
    if {[reg IFF]&3 || [vdpreg 1]&32} {finish false interrupts-left-enabled; return}
    if {$::saved_psg15 != [debug read "PSG regs" 15]} {finish false psg-output-register-not-restored; return}
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
    incr ::count
    next_case
}
after time 5 {
    if {[debug read memory 0xC7FD]!=83} {finish false cartridge-not-booted; return}
    debug write_block memory 0xD000 [string repeat [binary format c 165] 9088]
    debug set_bp $::done {} {debug break; after break {if {[catch {compare_case} detail]} {puts stderr $detail; exit 1}}}
    if {[catch {next_case} detail]} {puts stderr $detail; exit 1}
}
after time 400 {puts stderr oxygen-contract-timeout; exit 1}

set renderer none
set throttle off
set speed 999
set power true
set input [open outputs/collision/cases.bin rb]
set count 0
set cycles {0 0}
set worst {0 0}
proc finish {passed detail} {
    set guard [debug read_block memory 0xD000 8960]
    if {$guard ne [string repeat [binary format c 165] 8960]} {
        set passed false
        set detail ram-guard-corrupt
    }
    binary scan [debug read_block memory 0xF300 128] cu* stack
    set stack_min 62336
    for {set i 0} {$i<128} {incr i} {
        if {[lindex $stack $i]!=165} {set stack_min [expr {62208+$i}]; break}
    }
    set f [open outputs/collision/contract-result.json w]
    puts $f "\{\"passed\":$passed,\"cases\":$::count,\"acquisition_cycles\":[lindex $::cycles 0],\"tick_cycles\":[lindex $::cycles 1],\"acquisition_worst\":[lindex $::worst 0],\"tick_worst\":[lindex $::worst 1],\"stack_min\":$stack_min,\"detail\":\"$detail\"\}"
    close $f
    exit
}
proc next_case {} {
    set mode [read $::input 1]
    if {![string length $mode]} {finish true complete; return}
    binary scan $mode cu ::case_mode
    set ram [read $::input 1024]
    set ::expected [read $::input 251]
    if {[string length $::expected] != 251} {finish false truncated; return}
    debug write_block memory 0xC000 $ram
    reg PC [lindex $::entries $::case_mode]
    set ::started [machine_info time]
    set ::watchdog [after time 0.1 {finish false stuck}]
    debug cont
}
proc compare_case {} {
    after cancel $::watchdog
    set cost [expr {round(([machine_info time]-$::started)*3579545)}]
    if {$cost>[lindex $::cycles $::case_mode]} {
        lset ::cycles $::case_mode $cost
        lset ::worst $::case_mode $::count
    }
    set actual [debug read_block memory 0xC000 251]
    if {$actual ne $::expected} {
        binary scan $actual cu* aa
        binary scan $::expected cu* ee
        for {set i 0} {$i<251} {incr i} {
            if {[lindex $aa $i] != [lindex $ee $i]} {
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
    debug set_bp $::done {} {debug break; after break compare_case}
    next_case
}

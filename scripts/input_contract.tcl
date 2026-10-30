set renderer none
set throttle off
set speed 999
set power true
reverse loadreplay -goto begin -viewonly outputs/input/cases.omr
set input [open outputs/input/cases.bin rb]
set count 0
set expected ""
set max_sample_cycles 0
set actual_file [open outputs/input/actual.bin wb]
proc finish_input {passed detail} {
    set f [open outputs/input/result.json w]
    puts $f "\{\"passed\":$passed,\"cases\":$::count,\"max_sample_cycles\":$::max_sample_cycles,\"detail\":\"$detail\"\}"
    close $f
    close $::actual_file
    exit
}
proc read_expected {} {
    set header [read $::input 1]
    if {[string length $header] == 0} {finish_input true complete; return}
    binary scan $header cu switches
    set ram [read $::input 1024]
    binary scan [string index $ram 129] cu previous_phase
    set ::expected_sample_phase [expr {($previous_phase+1)&255}]
    set ::expected [read $::input 251]
    if {[string length $::expected] != 251} {finish_input false truncated; return}
}
proc compare_input {} {
    read_expected
    if {$::sample_phase != $::expected_sample_phase} {finish_input false wrong-original-sample-phase; return}
    set actual [debug read_block memory 0xC000 251]
    puts -nonewline $::actual_file $actual
    if {$actual ne $::expected} {
        binary scan $actual cu* aa
        binary scan $::expected cu* ee
        for {set i 0} {$i < 251} {incr i} {
            if {[lindex $aa $i] != [lindex $ee $i]} {
                finish_input false "byte=$i actual=[lindex $aa $i] expected=[lindex $ee $i]"
                return
            }
        }
    }
    incr ::count
    if {$::count == $::total_cases} {finish_input true complete; return}
    # Idle without changing CPU state until the next genuine device event.
    debug cont
}
after time 5.5 {
    if {[debug read memory 0xC7FD] != 83} {finish_input false cartridge-not-booted; return}
    debug set_bp $::sample_input {} {
        set ::sample_start [machine_info time]
        set ::sample_phase [debug read memory 0xC081]
        set ::saved_registers [list [reg AF] [reg BC] [reg DE] [reg HL] [reg IX] [reg IY]]
        set ::saved_psg15 [debug read "PSG regs" 15]
    }
    # core_F6A7's CALL is immediately before its first translated instruction.
    debug set_bp [expr {$::sample_input_return}] {} {
        if {$::saved_registers ne [list [reg AF] [reg BC] [reg DE] [reg HL] [reg IX] [reg IY]]} {finish_input false input-clobbered-core-registers}
        if {[reg IFF] & 3 || [vdpreg 1] & 32} {finish_input false interrupts-left-enabled}
        if {$::saved_psg15 != [debug read "PSG regs" 15]} {finish_input false psg-output-register-not-restored}
        set cycles [expr {round(([machine_info time]-$::sample_start)*3579545)}]
        if {$cycles > $::max_sample_cycles} {set ::max_sample_cycles $cycles}
    }
    debug set_bp $::input_rpc_done {} {debug break; after break compare_input}
}
after time 6.1 {if {$::count == 0} {finish_input false first-case-stuck}}
after time 100 {finish_input false timeout}

set renderer none
set throttle off
set speed 999
set power true
set cases_file [open "outputs/native/cases.bin" rb]
set case_count 0
set case_expected ""
set max_cycles 0
proc finish_contract {passed detail} {
    set f [open "outputs/native/result.json" w]
    puts $f "\{\"passed\":$passed,\"cases\":$::case_count,\"max_z80_cycles\":$::max_cycles,\"detail\":\"$detail\"\}"
    close $f
    exit
}
proc next_case {} {
    set progress [open "outputs/native/progress.txt" w]
    puts $progress $::case_count
    close $progress
    set header [read $::cases_file 7]
    if {[string length $header] == 0} {finish_contract true complete; return}
    binary scan $header c* values
    set entry [expr {([lindex $values 0]&255) | (([lindex $values 1]&255)<<8)}]
    debug write_block memory 0xC000 [read $::cases_file 1024]
    set ::case_expected [read $::cases_file 251]
    debug write memory 0xC6F0 [expr {[lindex $values 2]&255}]
    debug write memory 0xC6F1 [expr {[lindex $values 3]&255}]
    debug write memory 0xC6F2 [expr {[lindex $values 4]&255}]
    debug write memory 0xC6F3 [expr {[lindex $values 5]&255}]
    debug write memory 0xC6F4 [expr {[lindex $values 6]&255}]
    debug write memory 0xC6FE [expr {$entry&255}]
    debug write memory 0xC6FF [expr {$entry>>8}]
    reg PC $::rpc_start
    set ::case_started [machine_info time]
    set ::case_timeout [after time 0.1 {finish_contract false "stuck-PC=[reg PC] BC=[reg BC] AF=[reg AF] SP=[reg SP] frame=[debug read memory 0xC081]"}]
    debug cont
}
proc compare_case {} {
    after cancel $::case_timeout
    set cycles [expr {round(([machine_info time]-$::case_started)*3579545)}]
    if {$cycles > $::max_cycles} {set ::max_cycles $cycles}
    set actual [debug read_block memory 0xC000 251]
    if {$actual ne $::case_expected} {
        binary scan $actual c* aa
        binary scan $::case_expected c* ee
        for {set i 0} {$i < 251} {incr i} {
            if {[lindex $aa $i] != [lindex $ee $i]} {
                finish_contract false "byte=$i expected=[expr {[lindex $ee $i]&255}] actual=[expr {[lindex $aa $i]&255}] BC=[reg BC] AF=[reg AF] entryLo=[debug read memory 0xC6FE]"
                return
            }
        }
    }
    incr ::case_count
    next_case
}
after time 5 {
    if {[debug read memory 0xC7FD] != 83 || [debug read memory 0x4000] != 65} {
        finish_contract false cartridge-not-booted
        return
    }
    debug set_bp $::rpc_done {} {debug break; after break compare_case}
    next_case
}

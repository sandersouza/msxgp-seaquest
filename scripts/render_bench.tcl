set renderer none
set throttle off
set speed 999
set power true
set input [open outputs/render/cases.bin rb]
set dumps [open outputs/render/vram.bin wb]
set timings [open outputs/render/cycles.txt w]
set states [open outputs/render/state.bin wb]
set prepared [open outputs/render/prepared.bin wb]
set min_spacing 999999
set last_data -1
set data_writes 0
set count 0
proc fail {detail} {
    puts stderr $detail
    exit 1
}
proc next_case {} {
    set header [read $::input 6]
    set ram [read $::input 1024]
    if {[string length $ram] == 0} {
        close $::dumps
        close $::timings
        close $::states
        close $::prepared
        set f [open outputs/render/io.json w]
        puts $f "\{\"min_data_spacing\":$::min_spacing,\"data_writes\":$::data_writes\}"
        close $f
        set f [open outputs/render/complete.txt w]
        puts $f $::count
        close $f
        exit
        return
    }
    debug write_block memory 0xC000 $ram
    binary scan $header c* vv
    debug write memory 0xC6F0 0
    foreach {address index} {0xC6FE 0 0xC6FF 1 0xC6F1 2 0xC6F3 3 0xC6F2 4 0xC6F4 5} {
        debug write memory $address [expr {[lindex $vv $index]&255}]
    }
    reg PC $::rpc_start
    set ::started [machine_info time]
    set ::watchdog [after time 0.1 {fail "renderer stuck PC=[reg PC] SP=[reg SP]"}]
    debug cont
}
proc compare_case {} {
    after cancel $::watchdog
    puts $::timings [expr {round(([machine_info time]-$::started)*3579545)}]
    if {$::count == $::inject_pixel} {debug write VRAM 0 128}
    puts -nonewline $::dumps [debug read_block VRAM 0 16384]
    puts -nonewline $::states [debug read_block memory 0xC000 1024]
    incr ::count
    next_case
}
after time 5 {
    puts stderr "Machine [machine_info config_name] R1=[vdpreg 1]"
    if {[debug read memory 0xC7FD] != 83} {fail cartridge-not-booted; return}
    debug set_watchpoint write_io 0x98 {} {
        set now [machine_info time]
        if {$::last_data >= 0} {
            set gap [expr {round(($now-$::last_data)*3579545)}]
            if {$gap < $::min_spacing} {set ::min_spacing $gap}
        }
        set ::last_data $now
        incr ::data_writes
    }
    debug set_bp $::commit_pc {} {
        puts -nonewline $::prepared [debug read_block VRAM 0 16384]
    }
    debug set_bp $::rpc_done {} {debug break; after break compare_case}
    next_case
}

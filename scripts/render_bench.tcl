set renderer none
set throttle off
set speed 999
set power true
if {![info exists bench_dir]} {set bench_dir outputs/render}
set input [open $bench_dir/cases.bin rb]
set dumps [open $::bench_dir/vram.bin wb]
set timings [open $::bench_dir/cycles.txt w]
set states [open $::bench_dir/state.bin wb]
set prepared [open $::bench_dir/prepared.bin wb]
set prime_remaining 0
if {$hud_mode} {
    set baseline [open $::bench_dir/baseline.bin wb]
    set pages [open $::bench_dir/name-pages.bin wb]
    set registers [open $::bench_dir/registers.bin wb]
}
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
    if {$::input_mode && [string length $header]} {
        binary scan [read $::input 4] cu* keys
        foreach row {6 7 8} mask [lrange $keys 0 2] {
            keymatrixup $row 255
            keymatrixdown $row $mask
        }
        debug write memory 0xC420 [lindex $keys 3]
        debug write memory 0xC421 0
    }
    set ram [read $::input 1024]
    if {[string length $ram] == 0} {
        close $::dumps
        close $::timings
        close $::states
        close $::prepared
        if {$::hud_mode} {close $::baseline; close $::pages; close $::registers}
        set f [open $::bench_dir/io.json w]
        puts $f "\{\"min_data_spacing\":$::min_spacing,\"data_writes\":$::data_writes\}"
        close $f
        set f [open $::bench_dir/complete.txt w]
        puts $f $::count
        close $f
        if {[info exists ::font_prepare]} {
            set f [open $::bench_dir/font-stats.json w]
            puts $f "\{\"max_glyph_bytes\":$::max_font_writes\}"
            close $f
        }
        exit
        return
    }
    set ::case_ram $ram
    set ::case_header $header
    set ::prime_remaining [expr {$::hud_mode?2:0}]
    dispatch_case
}
proc dispatch_case {} {
    debug write_block memory 0xC000 $::case_ram
    set header $::case_header
    binary scan $header c* vv
    debug write memory 0xC6F0 0
    foreach {address index} {0xC6FE 0 0xC6FF 1 0xC6F1 2 0xC6F3 3 0xC6F2 4 0xC6F4 5} {
        debug write memory $address [expr {[lindex $vv $index]&255}]
    }
    if {$::prime_remaining>0} {
        binary scan [string index $::case_ram 134] cu old_color_mask
        if {$old_color_mask==0} {
            # Synthetic cold/reset fixtures precede their first source sample;
            # no earlier source display exists. Use the platform boot palette
            # for presentation init, then restore exact RAM before timedcore.
            debug write memory 0xC085 0
            debug write memory 0xC086 255
        }
        # Draw the supplied PRE-core display state into both caches, without
        # executing a gameplay instruction. Restore the exact input RAM again
        # before the measured F5B8 update; no target result enters its oracle.
        debug write memory 0xC6FE [expr {$::prime_entry&255}]
        debug write memory 0xC6FF [expr {$::prime_entry>>8}]
        if {[info exists ::prime_font_stress] && $::prime_font_stress &&
            (([lindex $vv 0]&255)|(([lindex $vv 1]&255)<<8))==$::prime_entry} {
            foreach address {0xC0B8 0xC0B9 0xC0BA} {debug write memory $address 153}
        }
    }
    reg PC [expr {$::prime_remaining>0?$::prime_start:$::rpc_start}]
    set ::started [machine_info time]
    set ::watchdog [after time 0.1 {fail "renderer stuck PC=[reg PC] SP=[reg SP]"}]
    debug cont
}
proc compare_case {} {
    after cancel $::watchdog
    if {$::prime_remaining>0} {
        incr ::prime_remaining -1
        if {$::prime_remaining==0} {
            puts -nonewline $::baseline [debug read_block VRAM 0 16384]
            puts -nonewline $::pages [binary format c [vdpreg 2]]
        }
        dispatch_case
        return
    }
    puts $::timings [expr {round(([machine_info time]-$::started)*3579545)}]
    if {$::count == $::inject_pixel} {debug write VRAM 0 128}
    puts -nonewline $::dumps [debug read_block VRAM 0 16384]
    puts -nonewline $::states [debug read_block memory 0xC000 1024]
    if {$::hud_mode} {
        puts -nonewline $::pages [binary format c [vdpreg 2]]
        set regs {}
        for {set i 0} {$i<8} {incr i} {lappend regs [vdpreg $i]}
        puts -nonewline $::registers [binary format c* $regs]
    }
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
        if {!$::hud_mode || $::prime_remaining==0} {incr ::data_writes}
    }
    debug set_bp $::commit_pc {} {
        if {!$::hud_mode || $::prime_remaining==0} {
            puts -nonewline $::prepared [debug read_block VRAM 0 16384]
            if {$::hud_mode} {puts -nonewline $::pages [binary format c [vdpreg 2]]}
        }
    }
    debug set_bp $::rpc_done {} {debug break; after break compare_case}
    if {[info exists ::font_prepare]} {
        set ::max_font_writes 0
        debug set_bp $::font_prepare {$::prime_remaining==0} {set ::font_writes_start $::data_writes}
        debug set_bp $::font_done {$::prime_remaining==0} {
            set bytes [expr {$::data_writes-$::font_writes_start}]
            if {$bytes>$::max_font_writes} {set ::max_font_writes $bytes}
        }
    }
    next_case
}

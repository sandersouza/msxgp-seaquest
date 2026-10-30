set renderer none
set throttle off
set speed 999
set power true
set count 0
set starts {}
set commits {}
set start_lines {}
set end_lines {}
set frame_counts {}
set last_commit 0
set busy_start 0
set max_busy 0
set input [open outputs/render/worst-case.bin rb]
set worst [read $input]
close $input
proc finish_pace {} {
    set guard [debug read_block memory 0xD000 8960]
    if {$guard ne [string repeat [binary format c 165] 8960]} {puts stderr ram-guard-corrupt; exit 1}
    binary scan [debug read_block memory 0xF300 128] c* stack
    set stack_min 62336
    for {set i 0} {$i < 128} {incr i} {
        if {[lindex $stack $i] != -91} {set stack_min [expr {62208+$i}]; break}
    }
    set f [open outputs/render/pace.json w]
    puts $f "\{\"frames\":$::count,\"periods\":\[[join $::starts ,]\],\"commit_cycles\":\[[join $::commits ,]\],\"commit_start_y\":\[[join $::start_lines ,]\],\"commit_end_y\":\[[join $::end_lines ,]\],\"frame_counts\":\[[join $::frame_counts ,]\],\"max_busy_cycles\":$::max_busy,\"stack_min\":$stack_min\}"
    close $f
    exit
}
after time 5 {
    if {[debug read memory 0xC7FD] != 83} {error cartridge-not-booted}
    # Probe stack headroom only after BIOS initialization, with IRQs disabled.
    debug write_block memory 0xD000 [string repeat [binary format c 165] 9088]
    debug set_bp $::paced_commit {} {
        set now [machine_info time]
        set y [machine_info VDP_msx_y_pos]
        if {$::count > 0} {
            lappend ::starts [expr {round(($now-$::last_commit)*3579545)}]
        }
        set ::last_commit $now
        set ::busy_start $now
        lappend ::start_lines $y
        lappend ::frame_counts [machine_info VDP_frame_count]
        incr ::count
        if {$::count == 241} {finish_pace}
    }
    debug set_bp $::paced_frame_start {} {
        set now [machine_info time]
        if {$::count > 0} {
            lappend ::commits [expr {round(($now-$::last_commit)*3579545)}]
            lappend ::end_lines [machine_info VDP_msx_y_pos]
        }
        debug write_block memory 0xC000 $::worst
    }
    debug set_bp $::paced_prepared {} {
        if {$::count > 0} {
            set busy [expr {round(([machine_info time]-$::last_commit)*3579545)}]
            if {$busy > $::max_busy} {set ::max_busy $busy}
        }
    }
    foreach address [list $::vblank_sample $::vblank_clear_sample] {
        debug set_bp $address {} {
            if {[reg A] & 64} {puts stderr sprite-overflow; exit 1}
        }
    }
    debug write_block memory 0xC000 $::worst
    reg PC $::paced_frame_start
    set ::last_commit [machine_info time]
    debug cont
}
after time 12 {puts stderr "pace-timeout count=$::count PC=[reg PC] SP=[reg SP] A=[reg A] R1=[vdpreg 1]"; exit 1}

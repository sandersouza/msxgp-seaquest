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
set guard_start [expr {$hud_mode?0xF000:0xD000}]
set guard_size [expr {0xF300-$guard_start}]
set pace_priming 0
if {$hud_mode} {
    set f [open outputs/presentation/hud.bin rb]
    set hud_static [read $f]
    close $f
}
set input [open outputs/render/worst-case.bin rb]
set worst [read $input]
close $input
proc finish_pace {} {
    set guard [debug read_block memory $::guard_start $::guard_size]
    if {$guard ne [string repeat [binary format c 165] $::guard_size]} {puts stderr ram-guard-corrupt; exit 1}
    if {$::hud_mode && [debug read_block memory 0xD000 [string length $::hud_static]] ne $::hud_static} {
        puts stderr immutable-hud-data-corrupt; exit 1
    }
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
    eval $::input_setup
    # Probe stack headroom only after BIOS initialization, with IRQs disabled.
    debug write_block memory $::guard_start [string repeat [binary format c 165] [expr {$::guard_size+128}]]
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
    if {$::hud_mode} {
        if {[debug read_block memory 0xD000 [string length $::hud_static]] ne $::hud_static} {
            puts stderr startup-hud-data-mismatch; exit 1
        }
        set ::pace_priming 2
        debug write memory 0xC6FE [expr {$::prime_entry&255}]
        debug write memory 0xC6FF [expr {$::prime_entry>>8}]
        foreach address {0xC6F0 0xC6F1 0xC6F2 0xC6F3 0xC6F4} {debug write memory $address 0}
        debug set_bp $::rpc_done {$::pace_priming>0} {
            incr ::pace_priming -1
            debug write_block memory 0xC000 $::worst
            set ::last_commit [machine_info time]
            if {$::pace_priming>0} {reg PC $::prime_start} else {reg PC $::paced_frame_start}
            debug cont
        }
        debug write_block memory 0xC000 $::worst
        reg PC $::prime_start
    } else {
        debug write_block memory 0xC000 $::worst
        reg PC $::paced_frame_start
        set ::last_commit [machine_info time]
    }
    debug cont
}
after time 12 {puts stderr "pace-timeout count=$::count PC=[reg PC] SP=[reg SP] A=[reg A] R1=[vdpreg 1]"; exit 1}

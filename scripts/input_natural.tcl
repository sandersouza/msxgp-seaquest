set renderer none
set throttle off
set speed 999
set power true
reverse loadreplay -goto begin -viewonly outputs/input/natural.omr
set states [open outputs/input/natural.bin wb]
set timings [open outputs/input/natural-timing.jsonl w]
set count 0
set recording 0
debug set_bp $::paced_commit {} {set ::commit_started [machine_info time]}
debug set_bp $::paced_frame_start {} {
    set ::frame_started [machine_info time]
    set ::commit_cycles 0
    if {[info exists ::commit_started]} {set ::commit_cycles [expr {round(($::frame_started-$::commit_started)*3579545)}]}
    if {$::recording} {
        puts $::timings "\{\"kind\":\"commit\",\"time\":[machine_info time],\"x\":[debug read VRAM 0x1B01]\}"
    }
    if {[machine_info time] >= 5.5} {
        if {[info exists ::oxygen_natural] && [machine_info time]>=17} {oxygen_controller}
        set ::recording 1
        set ::raster_input [debug read_block memory 0xC000 1024]
    }
}
debug set_bp $::paced_prepared {} {
    if {$::recording} {
        set busy [expr {round(([machine_info time]-$::frame_started)*3579545)+$::commit_cycles}]
        puts $::timings "\{\"kind\":\"busy\",\"cycles\":$busy\}"
    }
}
debug set_bp $::paced_core_start {} {
    if {[machine_info time] >= 5.5} {
        set ::recording 1
        set ::before [debug read_block memory 0xC000 1024]
    }
}
debug set_bp $::sample_input_return {} {
    if {$::recording} {
        set ::hardware [binary format cccc [debug read memory 0xC280] [debug read memory 0xC282] [debug read memory 0xC00C] [debug read memory 0xC00D]]
    }
}
debug set_bp $::paced_core_done {} {
    if {$::recording} {
        puts -nonewline $::states $::raster_input$::before$::hardware[debug read_block memory 0xC000 251]
        puts $::timings "\{\"kind\":\"state\",\"time\":[machine_info time],\"vdp_frame\":[machine_info VDP_frame_count],\"x\":[debug read memory 0xC0C6],\"y\":[debug read memory 0xC0E1],\"shot\":[debug read memory 0xC0E7],\"switches\":[debug read memory 0xC282]\}"
        incr ::count
    }
}
after time 16.5 {
    close $::states
    close $::timings
    set f [open outputs/input/natural-complete.txt w]
    puts $f $::count
    close $f
    exit
}

# Small isolated startup/one-frame probe; full acceptance uses the timed harness.
set renderer none
set throttle off
set speed 999
set power true
set hud_count 0
set hud_cycles {}
set hud_profile [open outputs/presentation/hud-profile.txt w]
after time 5 {
    if {[debug read memory 0xC7FD] != 83} {puts stderr hud-not-booted; exit 1}
    set f [open outputs/presentation/unpacked.bin wb]
    puts -nonewline $f [debug read_block memory 0xD000 $::hud_bytes]
    close $f
    set f [open outputs/presentation/stream-only-worst.bin rb]
    debug write_block memory 0xC000 [read $f]
    close $f
    debug write memory 0xC6FE [expr {$::core_F5B8&255}]
    debug write memory 0xC6FF [expr {$::core_F5B8>>8}]
    foreach address {0xC6F0 0xC6F1 0xC6F2 0xC6F4} {debug write memory $address 0}
    debug write memory 0xC6F3 130
    keymatrixdown 8 65
    foreach {name address} $::hud_stages {
        debug set_bp $address {} [format {puts $::hud_profile "%s [expr {round(([machine_info time]-$::started)*3579545)}]"} $name]
    }
    debug set_bp $::rpc_done {} {
        lappend ::hud_cycles [expr {round(([machine_info time]-$::started)*3579545)}]
        incr ::hud_count
        puts $::hud_profile "frame $::hud_count done [lindex $::hud_cycles end]"
        if {$::hud_count<3} {
            set f [open outputs/presentation/stream-only-worst.bin rb]
            debug write_block memory 0xC000 [read $f]
            close $f
            reg PC $::rpc_start
            set ::started [machine_info time]
            debug cont
            return
        }
        set f [open outputs/presentation/hud-probe-vram.bin wb]
        puts -nonewline $f [debug read_block VRAM 0 16384]
        close $f
        set f [open outputs/presentation/hud-probe-state.bin wb]
        puts -nonewline $f [debug read_block memory 0xC000 4096]
        close $f
        set f [open outputs/presentation/hud-probe.json w]
        puts $f "\{\"cycles\":\[[join $::hud_cycles ,]\],\"name_base\":[expr {([vdpreg 2]&15)*1024}]\}"
        close $f
        close $::hud_profile
        exit
    }
    reg PC $::rpc_start
    set ::started [machine_info time]
    debug cont
}
after time 6 {puts stderr "hud-probe-timeout PC=[reg PC] SP=[reg SP]"; exit 1}

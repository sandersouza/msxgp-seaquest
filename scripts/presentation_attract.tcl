set renderer none
set throttle off
set speed 999
set power true
set chain -1
set tick 0
set priming 0
set recording 0
set starts [open $out/timings.jsonl w]
set native [open $out/native.bin wb]
set pixels [open $out/pixels.bin wb]
set pixel_states [open $out/pixel-states.bin wb]
set pixel_meta [open $out/pixel-pages.bin wb]
set seeds [open $out/seeds.bin rb]
set max_busy 0
set max_commit 0
set skipped 0
set visible_commit 0
set generation_rebases 0
set ready_epoch_exposures 0
proc attract_fail {detail} {puts stderr $detail; exit 1}
proc profile_stage {name} {
    set cycle [expr {round(([machine_info time]-$::frame_started)*3579545)+$::commit_cycles}]
    puts $::starts "\{\"chain\":$::chain,\"tick\":$::tick,\"stage\":\"$name\",\"cycles\":$cycle,\"queue\":[debug read memory 0xC6DC],\"forecast\":[debug read memory 0xC2E1],\"player\":[debug read memory 0xC0B7],\"font_left\":[debug read memory 0xC4BE],\"iy\":[reg IY]\}"
}
proc next_chain {} {
    set data [read $::seeds 1024]
    if {[string length $data]==0} {
        foreach f {starts native pixels pixel_states pixel_meta seeds} {close [set ::$f]}
        set f [open $::out/result-raw.json w]
        puts $f "\{\"chains\":[expr {$::chain+1}],\"max_busy\":$::max_busy,\"max_commit\":$::max_commit,\"skipped\":$::skipped,\"visible_commit\":$::visible_commit,\"generation_rebases\":$::generation_rebases,\"ready_epoch_exposures\":$::ready_epoch_exposures\}"
        close $f
        exit
    }
    incr ::chain
    set ::seed $data
    set ::tick 0
    set ::last_vdp -1
    set ::injected 0
    set ::priming 2
    set ::recording 0
    foreach row {6 7 8} {keymatrixup $row 255}
    debug write memory 0xC420 [lindex $::switches $::chain]
    debug write memory 0xC421 0
    debug write memory 0xC2EF 0
    debug write memory 0xC2E2 255
    debug write memory 0xC2E3 255
    prime_display
}
proc prime_display {} {
    debug write_block memory 0xC000 [string range $::seed 0 250]
    debug write_block memory 0xC280 [string range $::seed 640 645]
    foreach {address value} [list 0xC6FE [expr {$::core_F00E&255}] 0xC6FF [expr {$::core_F00E>>8}] 0xC6F1 0 0xC6F2 0 0xC6F3 130 0xC6F4 0] {
        debug write memory $address $value
    }
    reg PC $::audio_prime_start
    debug cont
}
after time 5 {
    if {[debug read memory 0xC7FD]!=83} {attract_fail cartridge-not-booted}
    debug set_bp $::palette_rebase_generations {$::recording} {incr ::generation_rebases}
    debug set_bp $::palette_prefetch {$::recording && $::force_wrap && [debug read memory 0xC6EA]>=240 && [debug read memory 0xC6D2]==1} {incr ::ready_epoch_exposures}
    foreach {name address} $::profile_stages {
        debug set_bp $address {$::recording && $::chain==$::profile_chain && $::tick>=$::profile_start && $::tick<$::profile_start+10} [list profile_stage $name]
    }
    debug set_bp $::rpc_done {$::priming>0} {
        incr ::priming -1
        if {$::priming>0} {prime_display; return}
        debug write_block memory 0xC000 [string range $::seed 0 250]
        if {$::force_wrap} {
            # Advance the serial only; rolling it backward could manufacture
            # an impossible alias with a token retained by a previous chain.
            set serial [debug read memory 0xC6EA]
            if {$serial<$::epoch_seed} {debug write memory 0xC6EA $::epoch_seed}
        }
        set ::recording 1
        reg PC $::paced_start
        debug cont
    }
    debug set_bp $::paced_commit {$::recording} {
        set ::commit_started [machine_info time]
        set ::commit_y [machine_info VDP_msx_y_pos]
        set frame [machine_info VDP_frame_count]
        if {$::last_vdp>=0 && $frame-$::last_vdp!=1} {incr ::skipped}
        set ::last_vdp $frame
    }
    debug set_bp $::paced_frame_start {$::recording} {
        set ::frame_started [machine_info time]
        set ::commit_cycles [expr {round(($::frame_started-$::commit_started)*3579545)}]
        set end_y [machine_info VDP_msx_y_pos]
        if {$::commit_cycles>$::max_commit} {set ::max_commit $::commit_cycles}
        if {($::commit_y>=0 && $::commit_y<192) || ($end_y>=0 && $end_y<192)} {incr ::visible_commit}
        set phase [debug read memory 0xC081]
        puts $::starts "\{\"chain\":$::chain,\"tick\":$::tick,\"phase\":$phase,\"commit\":$::commit_cycles,\"start_y\":$::commit_y,\"end_y\":$end_y\}"
        if {$phase>=252 || $phase<=10} {
            puts -nonewline $::pixels [debug read_block VRAM 0 16384]
            puts -nonewline $::pixel_states [debug read_block memory 0xC000 251]
            puts -nonewline $::pixel_meta [binary format ccc [vdpreg 2] [vdpreg 7] [vdpreg 1]]
        }
        foreach row {6 7 8} {keymatrixup $row 255}
        set action [lindex $::actions $::chain]
        set trigger [lindex $::phases $::chain]
        if {$action && $phase==$trigger && !$::injected} {
            set ::injected 1
            if {$action==1} {keymatrixdown 8 128}
            if {$action==2} {keymatrixdown 6 32}
            if {$action==3} {keymatrixdown 6 64}
        }
        set ::raster [debug read_block memory 0xC000 1024]
    }
    debug set_bp $::paced_core_start {$::recording} {set ::before [debug read_block memory 0xC000 1024]}
    debug set_bp $::sample_input_return {$::recording} {
        set ::hardware [binary format cccc [debug read memory 0xC280] [debug read memory 0xC282] [debug read memory 0xC00C] [debug read memory 0xC00D]]
    }
    debug set_bp $::paced_core_done {$::recording} {
        puts -nonewline $::native $::raster$::before$::hardware[debug read_block memory 0xC000 251]
    }
    debug set_bp $::paced_prepared {$::recording} {
        set busy [expr {round(([machine_info time]-$::frame_started)*3579545)+$::commit_cycles}]
        if {$busy>$::max_busy} {set ::max_busy $busy}
        puts $::starts "\{\"chain\":$::chain,\"tick\":$::tick,\"busy\":$busy\}"
        incr ::tick
        if {$::tick>=$::chain_ticks} {
            set ::recording 0
            next_chain
        }
    }
    next_chain
}
after time $::watchdog_seconds {attract_fail "attract-test-timeout PC=[reg PC] SP=[reg SP] chain=$::chain tick=$::tick priming=$::priming recording=$::recording"}

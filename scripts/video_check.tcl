set renderer none
set throttle off
set speed 999
set z80_freq_locked true
set power true
set recording 0
set chain -1
set count 0
set tick 0
set priming 0
set active_tick 0
set max_busy 0
set max_commit 0
set min_spacing 999999
set min_active_spacing 999999
set last_data -1
set last_frame -1
set generation_rebases 0
set ready_epoch_exposures 0
set events [open $out/timing.jsonl w]
set native [open $out/native.bin wb]
set pixels [open $out/pixels.bin wb]
set states [open $out/pixel-states.bin wb]
set meta [open $out/pixel-meta.bin wb]
set seeds [open $out/seeds.bin rb]
proc fail_video {message} {puts stderr $message; exit 1}
proc initialize_video_guard {} {
    set cpu_hz [machine_info z80_freq]
    set vdp [dict get [machine_info device VDP] version]
    set ram_bytes [debug size {Main RAM}]
    set vram_bytes [debug size {physical VRAM}]
    if {$cpu_hz!=3579545 || $ram_bytes!=65536 || $vram_bytes!=16384 || $vdp ne $::expected_vdp} {fail_video hardware-settings}
    set f [open $::out/machine.json w]
    set bios [dict get [machine_info device {C-BIOS Main ROM}] actualSHA1]
    puts $f "\{\"machine\":\"[machine_info config_name]\",\"cpu_hz\":$cpu_hz,\"vdp\":\"$vdp\",\"ram_bytes\":$ram_bytes,\"vram_bytes\":$vram_bytes,\"bios_sha1\":\"$bios\"\}"
    close $f
    if {$::inject_clock_error} {debug write memory 0xC428 0}
    if {$::cold} {
        # Replay rejects debugger writes. C-BIOS init_ram itself fills the
        # F300..F37F disk/stack reserve with C9 before cartridge entry.
        set ::stack_marker 201
        if {[debug read_block memory 0xF300 64] ne [string repeat [binary format c 201] 64]} {fail_video cold-stack-baseline}
        set ::guard_value [debug read_block memory 0xF000 768]
    } else {
        set ::stack_marker 165
        set ::guard_value [string repeat [binary format c 165] 768]
        debug write_block memory 0xF000 [string repeat [binary format c 165] 896]
    }
}
proc finish_video {} {
    foreach channel {events native pixels states meta seeds audio_events} {close [set ::$channel]}
    if {[debug read_block memory 0xF000 768] ne $::guard_value} {fail_video RAM-guard}
    binary scan [debug read_block memory 0xF300 128] cu* stack
    set stack_min 62336
    for {set i 0} {$i<128} {incr i} {
        if {[lindex $stack $i]!=$::stack_marker} {set stack_min [expr {62208+$i}]; break}
    }
    set f [open $::out/raw.json w]
    puts $f "\{\"frames\":$::count,\"ticks\":$::tick,\"max_busy\":$::max_busy,\"max_commit\":$::max_commit,\"min_spacing\":$::min_spacing,\"min_active_spacing\":$::min_active_spacing,\"stack_min\":$stack_min,\"generation_rebases\":$::generation_rebases,\"ready_epoch_exposures\":$::ready_epoch_exposures\}"
    close $f
    exit
}
proc prime_video {} {
    debug write_block memory 0xC000 [string range $::seed 0 250]
    debug write_block memory 0xC280 [string range $::seed 640 645]
    debug write memory 0xC6FE [expr {$::core_F00E&255}]
    debug write memory 0xC6FF [expr {$::core_F00E>>8}]
    foreach address {0xC6F0 0xC6F1 0xC6F2 0xC6F3 0xC6F4} {debug write memory $address 0}
    reg PC $::audio_prime_start
    debug cont
}
proc next_video {} {
    set data [read $::seeds 1024]
    if {[string length $data]==0} {finish_video; return}
    set ::recording 0
    incr ::chain
    set ::chain_frames 0
    set ::last_frame -1
    set ::seed $data
    set ::priming 2
    set ::injected 0
    debug write memory 0xC42B 0
    set accum [lindex $::accumulators $::chain]
    debug write memory 0xC429 [expr {$accum&255}]
    debug write memory 0xC42A [expr {$accum>>8}]
    foreach row {6 7 8} {keymatrixup $row 255}
    debug write memory 0xC420 [lindex $::switches $::chain]
    debug write memory 0xC421 0
    prime_video
}
after time [expr {$cold?0:5}] {
    if {!$::cold} {
        if {[debug read memory 0xC7FD]!=83} {fail_video boot}
        initialize_video_guard
    }
    debug set_bp $::rpc_done {$::priming>0} {
        incr ::priming -1
        if {$::priming} {prime_video; return}
        debug write_block memory 0xC000 [string range $::seed 0 250]
        if {$::generation_mode ne "normal"} {
            set epoch [expr {$::generation_mode eq "wrap"?240:239}]
            if {[debug read memory 0xC6EA]<$epoch} {debug write memory 0xC6EA $epoch}
        }
        set ::recording 1
        reg PC $::paced_start
        debug cont
    }
    debug set_bp $::acquire_frame_state {$::recording} {
        set ::raster [debug read_block memory 0xC000 1024]
    }
    debug set_bp $::core_F5B8 {$::recording} {
        if {!$::cold} {
            foreach row {6 7 8} {keymatrixup $row 255}
            set action [lindex $::actions $::chain]
            if {$action && !$::injected && [debug read memory 0xC081]==[lindex $::phases $::chain]} {
                set ::injected 1
                if {$action==1} {keymatrixdown 8 128}
                if {$action==2} {keymatrixdown 6 32}
                if {$action==3} {keymatrixdown 6 64}
            }
        }
        set ::before [debug read_block memory 0xC000 1024]
        set ::active_tick 1
    }
    debug set_bp $::sample_input_return {$::recording && $::active_tick} {
        set ::hardware [binary format cccc [debug read memory 0xC280] [debug read memory 0xC282] [debug read memory 0xC00C] [debug read memory 0xC00D]]
        puts $::events "\{\"kind\":\"sample\",\"chain\":$::chain,\"tick\":$::tick,\"time\":[machine_info time],\"ports\":[debug read memory 0xC280]\}"
    }
    debug set_bp $::core_F00E {$::recording && $::active_tick} {
        puts -nonewline $::native $::raster$::before$::hardware[debug read_block memory 0xC000 251]
        puts $::events "\{\"kind\":\"state\",\"chain\":$::chain,\"tick\":$::tick,\"time\":[machine_info time],\"x\":[debug read memory 0xC0C6]\}"
        set ::active_tick 0
        incr ::tick
    }
    debug set_bp $::paced_commit {$::recording} {
        set ::commit_started [machine_info time]
        set ::commit_y [machine_info VDP_msx_y_pos]
        set frame [machine_info VDP_frame_count]
        if {$::last_frame>=0 && $frame-$::last_frame!=1} {fail_video "missed-frame chain=$::chain frame=$frame previous=$::last_frame"}
        set ::last_frame $frame
    }
    debug set_bp $::video_after_commit {$::recording} {
        set end_y [machine_info VDP_msx_y_pos]
        set cycles [expr {round(([machine_info time]-$::commit_started)*3579545)}]
        set ::max_commit [expr {max($::max_commit,$cycles)}]
        if {($::commit_y>=0 && $::commit_y<192) || ($end_y>=0 && $end_y<192)} {fail_video visible-commit}
        incr ::count
        incr ::chain_frames
        puts $::events "\{\"kind\":\"commit\",\"chain\":$::chain,\"frame\":$::chain_frames,\"ticks\":$::tick,\"start_time\":$::commit_started,\"time\":[machine_info time],\"commit\":$cycles,\"x\":[debug read VRAM 0x1B01]\}"
        set phase [debug read memory 0xC081]
        if {$phase<=10 || $phase>=250 || $::chain_frames%16==0} {
            puts -nonewline $::pixels [debug read_block VRAM 0 16384]
            puts -nonewline $::states [debug read_block memory 0xC000 251]
            puts -nonewline $::meta [binary format ccc [vdpreg 2] [vdpreg 7] [vdpreg 1]]
        }
    }
    debug set_bp $::paced_wait {$::recording} {
        if {[info exists ::commit_started] && $::chain_frames>0} {
            set cycles [expr {round(([machine_info time]-$::commit_started)*3579545)}]
            set ::max_busy [expr {max($::max_busy,$cycles)}]
            if {$cycles>=$::budget} {fail_video "budget=$cycles chain=$::chain frame=$::chain_frames"}
        }
        if {$::chain_frames>=$::frames} {
            if {$::cold} {finish_video} else {next_video}
        }
    }
    debug set_watchpoint write_io 0x98 {$::recording} {
        set now [machine_info time]
        if {$::last_data>=0} {
            set gap [expr {round(($now-$::last_data)*3579545)}]
            set ::min_spacing [expr {min($::min_spacing,$gap)}]
            set y [machine_info VDP_msx_y_pos]
            if {$y>=0 && $y<192 && ([vdpreg 1]&64)} {
                set ::min_active_spacing [expr {min($::min_active_spacing,$gap)}]
                if {$gap<29} {fail_video "active-IO-spacing=$gap"}
            }
        }
        set ::last_data $now
    }
    debug set_bp $::palette_rebase_generations {$::recording} {incr ::generation_rebases}
    debug set_bp $::video_extra_core_start {$::recording && $::inject_canonical_error} {
        debug write memory 0xC0E6 [expr {[debug read memory 0xC0E6]^1}]
        set ::inject_canonical_error 0
    }
    debug set_bp $::palette_prefetch {$::recording && [debug read memory 0xC6D2]==1 && [debug read memory 0xC6EA]>=240} {incr ::ready_epoch_exposures}
    if {$::cold} {
        set ::chain 0
        set ::chain_frames 0
        debug set_bp $::paced_frame_start {!$::guard_ready && [debug read memory 0xC7FD]==83} {
            initialize_video_guard
            set ::guard_ready 1
            set ::recording 1
        }
    } else {
        next_video
    }
}
after time 2000 {fail_video watchdog}

# Device-only exhaustion: alternate partial dives/ascent to exercise the original
# zero-diver penalty, both players, game over, selection and console restart.
# No game RAM is changed. The native BIOS sampler reads every keyboard event.
set progression_started 0
set progression_tick 0
set progression_restarted 0
set progression_selected 0
proc oxygen_controller {} {
    if {!$::progression_started} {
        reverse truncatereplay
        set ::progression_started 1
        puts $::timings "\{\"kind\":\"progression-controller\",\"time\":[machine_info time]\}"
    }
    incr ::progression_tick
    keymatrixup 6 255
    keymatrixup 7 255
    keymatrixup 8 255
    if {$::progression_tick==1 && [debug read memory 0xC080]!=1} {
        keymatrixdown 6 64
        set ::progression_selected 1
        return
    }
    if {$::progression_selected && $::progression_tick==2} {keymatrixdown 6 32; return}
    # Independent A/B switches, press then release; preserve these across reset.
    if {$::progression_tick==20 || $::progression_tick==60} {keymatrixdown 6 128}
    if {$::progression_tick==40 || $::progression_tick==80} {keymatrixdown 7 1}
    if {[debug read memory 0xC0A3] && !$::progression_restarted} {
        keymatrixdown 6 32
        set ::progression_restarted 1
        return
    }
    set py [debug read memory 0xC0E1]
    set oxygen [debug read memory 0xC0E6]
    set ty [expr {$oxygen==64 ? 20 : 13}]
    if {$ty<$py} {keymatrixdown 8 32}
    if {$ty>$py} {keymatrixdown 8 64}
}
